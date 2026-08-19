from fastapi import APIRouter

from app.workouts import service
from app.workouts.schemas import WorkoutParseRequest, ParsedWorkout

router = APIRouter(tags=["workouts"])


@router.post("/workouts/parse")
def parse_workout(payload: WorkoutParseRequest):
    """Interpreta o texto colado (Hevy) sem persistir — usado para mostrar
    a prévia antes de o usuário confirmar o salvamento."""
    return service.parse_workout(payload.text)


@router.post("/workouts", status_code=201)
def create_workout(payload: ParsedWorkout):
    return service.create_workout(payload.model_dump())


@router.get("/workouts")
def list_workouts():
    return service.list_workouts()


@router.get("/workouts/{workout_id}")
def get_workout(workout_id: int):
    return service.get_workout(workout_id)


@router.delete("/workouts/{workout_id}", status_code=204)
def delete_workout(workout_id: int):
    service.delete_workout(workout_id)
    return None
