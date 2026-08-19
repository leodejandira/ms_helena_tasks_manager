import json
from datetime import date as date_type
from typing import Optional, List
from fastapi import HTTPException

from app.database import db
from app.timezone_utils import now_utc_iso, today_local_str

DONE_STATUSES = ("concluida", "cancelada")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _now_iso() -> str:
    return now_utc_iso()


def _today_local_str() -> str:
    return today_local_str()


def _remove_from_today_board(task_id: int) -> None:
    """Remove a tarefa da prancheta do dia atual, se ela estiver lá.
    Usado ao concluir ou cancelar uma tarefa (seção 9 dos requisitos)."""
    db.table("daily_tasks").delete().eq("task_id", task_id).eq("date", _today_local_str()).execute()


def _dependencies_resolved(dependency_ids: List[int]) -> bool:
    if not dependency_ids:
        return True
    resp = db.table("tasks").select("id,status").in_("id", dependency_ids).execute()
    found = {row["id"]: row["status"] for row in resp.data}
    for dep_id in dependency_ids:
        status = found.get(dep_id)
        if status not in DONE_STATUSES:
            return False
    return True


def _promote_dependents(completed_task_id: int) -> None:
    """Depois de concluir/cancelar uma tarefa, promove de 'criada' para
    'preparada' qualquer tarefa que dependia dela e que já tenha todas
    as dependências resolvidas."""
    # OBS: não usar .contains("dependencies", [completed_task_id]) aqui.
    # O client postgrest-py trata list/iterable como array literal do Postgres
    # e faz ",".join(value) internamente — como completed_task_id é int, isso
    # gera "TypeError: sequence item 0: expected str instance, int found".
    # Além disso, mesmo com strings, ",".join geraria a sintaxe de array
    # Postgres ({1,2}), que não é o formato correto para containment em JSONB.
    # A forma correta é montar o filtro "cs" (contains) manualmente com um
    # literal JSON, que é o que o PostgREST espera para colunas JSONB.
    resp = (
        db.table("tasks")
        .select("id,dependencies")
        .eq("status", "criada")
        .filter("dependencies", "cs", json.dumps([completed_task_id]))
        .execute()
    )
    for row in resp.data:
        if _dependencies_resolved(row["dependencies"] or []):
            db.table("tasks").update({
                "status": "preparada",
                "updated_at": _now_iso(),
            }).eq("id", row["id"]).execute()


def _get_task_or_404(task_id: int) -> dict:
    resp = db.table("tasks").select("*").eq("id", task_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return resp.data[0]


# ---------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------

def create_task(payload: dict) -> dict:
    dependencies = payload.get("dependencies") or []
    # Regra: sem dependências -> preparada; com uma ou mais dependências -> criada
    # (mesmo que essas dependências já estejam resolvidas no momento da criação).
    status = "preparada" if not dependencies else "criada"

    row = {
        "name": payload["name"],
        "group_name": payload["group_name"],
        "complexity": payload["complexity"],
        "criticality": payload["criticality"],
        "estimated_minutes": payload["estimated_minutes"],
        "elapsed_minutes": 0,
        "deadline": payload.get("deadline").isoformat() if payload.get("deadline") else None,
        "dependencies": dependencies,
        "notes": payload.get("notes"),
        "status": status,
    }
    resp = db.table("tasks").insert(row).execute()
    return resp.data[0]


def list_tasks(
    status: Optional[str] = None,
    group_name: Optional[str] = None,
    complexity: Optional[str] = None,
    criticality: Optional[str] = None,
    deadline: Optional[str] = None,
    estimated_minutes: Optional[int] = None,
    include_done: bool = False,
) -> List[dict]:
    query = db.table("tasks").select("*")

    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        query = query.in_("status", statuses)
    elif not include_done:
        query = query.not_.in_("status", list(DONE_STATUSES))

    if group_name:
        query = query.eq("group_name", group_name)
    if complexity:
        query = query.eq("complexity", complexity)
    if criticality:
        query = query.eq("criticality", criticality)
    if deadline:
        query = query.eq("deadline", deadline)
    if estimated_minutes is not None:
        query = query.eq("estimated_minutes", estimated_minutes)

    resp = query.order("created_at", desc=True).execute()
    return resp.data


def get_task(task_id: int) -> dict:
    return _get_task_or_404(task_id)


def update_task(task_id: int, payload: dict) -> dict:
    _get_task_or_404(task_id)
    row = {k: v for k, v in payload.items() if v is not None}
    if "deadline" in row and isinstance(row["deadline"], (date_type,)):
        row["deadline"] = row["deadline"].isoformat()
    row["updated_at"] = _now_iso()
    resp = db.table("tasks").update(row).eq("id", task_id).execute()
    return resp.data[0]


def delete_task(task_id: int) -> None:
    _get_task_or_404(task_id)
    # daily_tasks tem ON DELETE CASCADE, então referências são removidas automaticamente.
    db.table("tasks").delete().eq("id", task_id).execute()


# ---------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------

def start_task(task_id: int) -> dict:
    task = _get_task_or_404(task_id)
    if task["status"] in DONE_STATUSES:
        raise HTTPException(status_code=409, detail="Tarefa já finalizada, não pode ser iniciada")
    update = {"status": "em_andamento", "updated_at": _now_iso()}
    if not task.get("started_at"):
        update["started_at"] = _now_iso()
    resp = db.table("tasks").update(update).eq("id", task_id).execute()
    return resp.data[0]


def add_time(task_id: int, minutes: int) -> dict:
    if minutes is None or minutes <= 0:
        raise HTTPException(status_code=400, detail="Tempo informado deve ser maior que zero")
    task = _get_task_or_404(task_id)
    if task["status"] in DONE_STATUSES:
        raise HTTPException(status_code=409, detail="Tarefa já finalizada, não é possível registrar tempo")

    new_elapsed = (task.get("elapsed_minutes") or 0) + minutes
    update = {
        "elapsed_minutes": new_elapsed,
        "status": "em_andamento",
        "updated_at": _now_iso(),
    }
    if not task.get("started_at"):
        update["started_at"] = _now_iso()
    resp = db.table("tasks").update(update).eq("id", task_id).execute()
    return resp.data[0]


def complete_task(task_id: int) -> dict:
    task = _get_task_or_404(task_id)
    if task["status"] == "concluida":
        return task
    if task["status"] == "cancelada":
        raise HTTPException(status_code=409, detail="Tarefa cancelada não pode ser concluída")

    if not _dependencies_resolved(task.get("dependencies") or []):
        raise HTTPException(
            status_code=409,
            detail="Existem dependências pendentes. Conclua ou cancele-as antes de concluir esta tarefa.",
        )

    resp = db.table("tasks").update({
        "status": "concluida",
        "completed_at": _now_iso(),
        "updated_at": _now_iso(),
    }).eq("id", task_id).execute()

    _remove_from_today_board(task_id)
    _promote_dependents(task_id)
    return resp.data[0]


def cancel_task(task_id: int) -> dict:
    task = _get_task_or_404(task_id)
    if task["status"] in DONE_STATUSES:
        return task

    resp = db.table("tasks").update({
        "status": "cancelada",
        "cancelled_at": _now_iso(),
        "updated_at": _now_iso(),
    }).eq("id", task_id).execute()

    _remove_from_today_board(task_id)
    _promote_dependents(task_id)
    return resp.data[0]


# ---------------------------------------------------------------------
# Prancheta (daily_tasks)
# ---------------------------------------------------------------------

def list_daily_tasks(date_str: str) -> List[dict]:
    resp = (
        db.table("daily_tasks")
        .select("*, tasks(*)")
        .eq("date", date_str)
        .order("position")
        .execute()
    )
    return resp.data


def add_daily_task(task_id: int, date_str: str) -> dict:
    _get_task_or_404(task_id)
    existing = db.table("daily_tasks").select("position").eq("date", date_str).order("position", desc=True).limit(1).execute()
    next_position = (existing.data[0]["position"] + 1) if existing.data else 0
    resp = db.table("daily_tasks").upsert({
        "task_id": task_id,
        "date": date_str,
        "position": next_position,
    }, on_conflict="task_id,date").execute()
    return resp.data[0]


def remove_daily_task(task_id: int, date_str: str) -> None:
    db.table("daily_tasks").delete().eq("task_id", task_id).eq("date", date_str).execute()


def reorder_daily_tasks(items: List[dict]) -> None:
    for item in items:
        db.table("daily_tasks").update({"position": item["position"]}).eq("id", item["id"]).execute()
