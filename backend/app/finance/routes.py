from typing import Optional
from fastapi import APIRouter, Query
from datetime import date as date_type

from app.finance import service
from app.finance.schemas import ExpenseCreate, ExpenseUpdate

router = APIRouter(tags=["finance"])


@router.get("/expenses")
def list_expenses(year: Optional[int] = None, month: Optional[int] = None):
    return service.list_expenses(year=year, month=month)


@router.post("/expenses", status_code=201)
def create_expense(payload: ExpenseCreate):
    return service.create_expense(payload.model_dump())


@router.get("/expenses/summary")
def summary(year: int = Query(...), month: int = Query(...)):
    return service.summary(year=year, month=month)


@router.get("/expenses/{expense_id}")
def get_expense(expense_id: int):
    return service.get_expense(expense_id)


@router.put("/expenses/{expense_id}")
def update_expense(expense_id: int, payload: ExpenseUpdate):
    return service.update_expense(expense_id, payload.model_dump(exclude_unset=True))


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    service.delete_expense(expense_id)
    return None
