from typing import Optional
from datetime import date
from pydantic import BaseModel


class HabitRecordUpsert(BaseModel):
    habit_id: int
    date: date
    step: Optional[str] = ""       # usado em hábitos do tipo 'steps' (manha/tarde/noite, cafe/almoco/jantar)
    value: Optional[int] = None    # usado em 'counter' (incremento) e 'minutes' (valor informado)
    completed: Optional[bool] = None  # usado em 'boolean' e 'steps'
