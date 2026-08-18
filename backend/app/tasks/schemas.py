from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field

GROUPS = ["IBM", "BB", "Angelo", "Pessoal", "Casa", "Relacionamento", "Carreira", "Faculdade"]
LEVELS = ["Baixa", "Média", "Alta", "Altíssima"]
STATUSES = ["criada", "preparada", "em_andamento", "cancelada", "concluida"]


class TaskCreate(BaseModel):
    name: str
    group_name: str
    complexity: str
    criticality: str
    estimated_minutes: int  # obrigatório — não pode ficar NULL/implícito
    deadline: Optional[date] = None
    dependencies: List[int] = Field(default_factory=list)
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    group_name: Optional[str] = None
    complexity: Optional[str] = None
    criticality: Optional[str] = None
    estimated_minutes: Optional[int] = None
    deadline: Optional[date] = None
    dependencies: Optional[List[int]] = None
    notes: Optional[str] = None


class TimeAdd(BaseModel):
    minutes: int


class DailyTaskCreate(BaseModel):
    task_id: int
    date: date


class DailyTaskReorderItem(BaseModel):
    id: int
    position: int


class DailyTaskReorder(BaseModel):
    items: List[DailyTaskReorderItem]
