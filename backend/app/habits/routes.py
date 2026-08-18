from datetime import date as date_type
from typing import Optional
from fastapi import APIRouter, Query

from app.habits import service
from app.habits.schemas import HabitRecordUpsert

router = APIRouter(tags=["habits"])


@router.get("/habits")
def list_habits():
    return service.list_habits()


@router.get("/habits/today")
def today_habits(date: date_type = Query(...)):
    return service.today_habits(date.isoformat())


@router.get("/habits/history")
def habits_history(habit_id: Optional[int] = None, start: Optional[str] = None, end: Optional[str] = None):
    return service.history(habit_id=habit_id, start=start, end=end)


@router.post("/habits/records")
def upsert_record(payload: HabitRecordUpsert):
    return service.upsert_record(
        habit_id=payload.habit_id,
        date_str=payload.date.isoformat(),
        step=payload.step or "",
        value=payload.value,
        completed=payload.completed,
    )
