from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class DailyTaskCreate(BaseModel):
    item_id: int
    task_date: Optional[date] = None  # se omitido, backend assume "hoje" em America/Sao_Paulo


class DailyTaskResponse(BaseModel):
    id: int
    item_id: int
    task_date: date
    order_index: int
    status_dia: str
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DailyTaskReorderItem(BaseModel):
    id: int
    order_index: int


class DailyTaskReorderRequest(BaseModel):
    task_date: date
    items: List[DailyTaskReorderItem]
