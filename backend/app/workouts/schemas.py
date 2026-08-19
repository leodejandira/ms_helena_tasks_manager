from typing import Optional, List
from pydantic import BaseModel


class WorkoutParseRequest(BaseModel):
    text: str


class ParsedSet(BaseModel):
    set_number: int
    repetitions: Optional[int] = None
    weight: Optional[float] = None
    unit: Optional[str] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None


class ParsedExercise(BaseModel):
    exercise_name: str
    exercise_order: int
    set_type: Optional[str] = None
    sets: List[ParsedSet]


class ParsedWorkout(BaseModel):
    """Estrutura devolvida por POST /api/workouts/parse (prévia) e também
    aceita por POST /api/workouts (persistência) — o frontend reenvia a
    mesma estrutura que recebeu na prévia, permitindo revisão antes de
    salvar sem duplicar o parser no cliente."""

    name: str
    workout_date: str  # data ISO (YYYY-MM-DD), já no fuso America/Sao_Paulo
    source: Optional[str] = None
    source_url: Optional[str] = None
    exercises: List[ParsedExercise]
    exercise_count: int
    set_count: int
