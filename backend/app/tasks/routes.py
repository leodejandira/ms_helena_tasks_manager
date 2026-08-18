from datetime import date as date_type
from typing import Optional
from fastapi import APIRouter, Query

from app.tasks import service
from app.tasks.schemas import TaskCreate, TaskUpdate, TimeAdd, DailyTaskCreate, DailyTaskReorder

router = APIRouter(tags=["tasks"])


@router.get("/tasks")
def list_tasks(
    status: Optional[str] = None,
    group_name: Optional[str] = None,
    complexity: Optional[str] = None,
    criticality: Optional[str] = None,
    deadline: Optional[str] = None,
    estimated_minutes: Optional[int] = None,
    include_done: bool = False,
):
    return service.list_tasks(
        status=status,
        group_name=group_name,
        complexity=complexity,
        criticality=criticality,
        deadline=deadline,
        estimated_minutes=estimated_minutes,
        include_done=include_done,
    )


@router.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    return service.create_task(payload.model_dump())


@router.get("/tasks/{task_id}")
def get_task(task_id: int):
    return service.get_task(task_id)


@router.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    return service.update_task(task_id, payload.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    service.delete_task(task_id)
    return None


@router.post("/tasks/{task_id}/start")
def start_task(task_id: int):
    return service.start_task(task_id)


@router.post("/tasks/{task_id}/time")
def add_time(task_id: int, payload: TimeAdd):
    return service.add_time(task_id, payload.minutes)


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    return service.complete_task(task_id)


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: int):
    return service.cancel_task(task_id)


# ---------------------------------------------------------------------
# Daily tasks (Prancheta)
# ---------------------------------------------------------------------

@router.get("/daily-tasks")
def list_daily_tasks(date: date_type = Query(...)):
    return service.list_daily_tasks(date.isoformat())


@router.post("/daily-tasks", status_code=201)
def add_daily_task(payload: DailyTaskCreate):
    return service.add_daily_task(payload.task_id, payload.date.isoformat())


@router.delete("/daily-tasks/{task_id}", status_code=204)
def remove_daily_task(task_id: int, date: date_type = Query(...)):
    service.remove_daily_task(task_id, date.isoformat())
    return None


@router.put("/daily-tasks/reorder")
def reorder_daily_tasks(payload: DailyTaskReorder):
    service.reorder_daily_tasks([item.model_dump() for item in payload.items])
    return {"ok": True}
