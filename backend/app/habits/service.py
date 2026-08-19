from typing import Optional
from fastapi import HTTPException

from app.database import db
from app.timezone_utils import now_utc_iso


def _now_iso() -> str:
    return now_utc_iso()


def list_habits() -> list:
    resp = db.table("habits").select("*").order("id").execute()
    return resp.data


def _records_for_date(date_str: str) -> list:
    resp = db.table("habit_daily_records").select("*").eq("date", date_str).execute()
    return resp.data


def today_habits(date_str: str) -> list:
    habits = list_habits()
    records = _records_for_date(date_str)

    records_by_habit: dict = {}
    for r in records:
        records_by_habit.setdefault(r["habit_id"], []).append(r)

    result = []
    for habit in habits:
        result.append({
            **habit,
            "records": records_by_habit.get(habit["id"], []),
        })
    return result


def history(habit_id: Optional[int] = None, start: Optional[str] = None, end: Optional[str] = None) -> list:
    query = db.table("habit_daily_records").select("*")
    if habit_id:
        query = query.eq("habit_id", habit_id)
    if start:
        query = query.gte("date", start)
    if end:
        query = query.lte("date", end)
    resp = query.order("date", desc=True).execute()
    return resp.data


def _get_habit_or_404(habit_id: int) -> dict:
    resp = db.table("habits").select("*").eq("id", habit_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Hábito não encontrado")
    return resp.data[0]


def upsert_record(habit_id: int, date_str: str, step: str = "", value: Optional[int] = None, completed: Optional[bool] = None) -> dict:
    habit = _get_habit_or_404(habit_id)
    step = step or ""

    existing = (
        db.table("habit_daily_records")
        .select("*")
        .eq("habit_id", habit_id)
        .eq("date", date_str)
        .eq("step", step)
        .execute()
    )

    if habit["type"] == "counter":
        # value é o incremento; soma ao valor já existente do dia
        current = existing.data[0]["value"] if existing.data else 0
        new_value = current + (value or 1)
        payload = {"habit_id": habit_id, "date": date_str, "step": step, "value": new_value, "completed": True, "updated_at": _now_iso()}
    elif habit["type"] == "minutes":
        payload = {"habit_id": habit_id, "date": date_str, "step": step, "value": value or 0, "completed": True, "updated_at": _now_iso()}
    else:
        # boolean ou steps: marca como concluído
        payload = {"habit_id": habit_id, "date": date_str, "step": step, "value": 1, "completed": True if completed is None else completed, "updated_at": _now_iso()}

    resp = db.table("habit_daily_records").upsert(payload, on_conflict="habit_id,date,step").execute()
    return resp.data[0]
