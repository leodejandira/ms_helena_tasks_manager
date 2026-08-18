from datetime import datetime, date as date_type
from typing import Optional
from fastapi import HTTPException

from app.database import db


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _get_expense_or_404(expense_id: int) -> dict:
    resp = db.table("expenses").select("*").eq("id", expense_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    return resp.data[0]


def _signed_amount(expense_type: str, amount: float) -> float:
    """Regra de sinal: o usuário nunca informa se é positivo/negativo.
    'Entrada' é sempre positivo; qualquer outro tipo é sempre negativo.
    A interpretação acontece aqui, na camada de persistência."""
    magnitude = abs(amount)
    return magnitude if expense_type == "Entrada" else -magnitude


def create_expense(payload: dict) -> dict:
    expense_date = payload.get("date") or date_type.today()
    row = {
        "name": payload["name"],
        "type": payload["type"],
        "amount": _signed_amount(payload["type"], payload["amount"]),
        "notes": payload.get("notes"),
        "date": expense_date.isoformat(),
    }
    resp = db.table("expenses").insert(row).execute()
    return resp.data[0]


def list_expenses(year: Optional[int] = None, month: Optional[int] = None) -> list:
    query = db.table("expenses").select("*")
    if year and month:
        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1:04d}-01-01"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"
        query = query.gte("date", start).lt("date", end)
    resp = query.order("date", desc=True).execute()
    return resp.data


def get_expense(expense_id: int) -> dict:
    return _get_expense_or_404(expense_id)


def update_expense(expense_id: int, payload: dict) -> dict:
    existing = _get_expense_or_404(expense_id)
    row = {k: v for k, v in payload.items() if v is not None}
    if "date" in row and hasattr(row["date"], "isoformat"):
        row["date"] = row["date"].isoformat()
    if "amount" in row or "type" in row:
        effective_type = row.get("type", existing["type"])
        effective_amount = row.get("amount", existing["amount"])
        row["amount"] = _signed_amount(effective_type, effective_amount)
    row["updated_at"] = _now_iso()
    resp = db.table("expenses").update(row).eq("id", expense_id).execute()
    return resp.data[0]


def delete_expense(expense_id: int) -> None:
    _get_expense_or_404(expense_id)
    db.table("expenses").delete().eq("id", expense_id).execute()


def summary(year: int, month: int) -> dict:
    expenses = list_expenses(year=year, month=month)
    # "Entrada" é armazenado positivo; os demais tipos são armazenados
    # negativos (ver _signed_amount). "saidas" no resumo é a magnitude
    # (positiva) do total gasto, então usamos abs() aqui.
    entradas = sum(float(e["amount"]) for e in expenses if e["type"] == "Entrada")
    saidas = sum(abs(float(e["amount"])) for e in expenses if e["type"] != "Entrada")
    return {
        "entradas": round(entradas, 2),
        "saidas": round(saidas, 2),
        "saldo": round(entradas - saidas, 2),
    }
