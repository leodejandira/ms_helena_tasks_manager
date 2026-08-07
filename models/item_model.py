from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemCreate(BaseModel):
    item: str
    grupo: str
    categoria: str

    requisito: Optional[str] = None
    notas: Optional[str] = None

    status: str

    complexidade: Optional[str] = None
    custo: Optional[float] = 0.0
    tempo_ext_h: Optional[float] = 0.0

    criticidade: Optional[str] = None
    prioridade: Optional[int] = 3

    data_limite: Optional[str] = None

    tempo_gasto_h: Optional[float] = 0.0


class ItemUpdate(BaseModel):
    item: Optional[str] = None
    grupo: Optional[str] = None
    categoria: Optional[str] = None

    requisito: Optional[str] = None
    notas: Optional[str] = None

    status: Optional[str] = None

    complexidade: Optional[str] = None
    custo: Optional[float] = None
    tempo_ext_h: Optional[float] = None

    criticidade: Optional[str] = None
    prioridade: Optional[int] = None

    data_limite: Optional[str] = None

    tempo_gasto_h: Optional[float] = None


class ItemResponse(ItemCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None