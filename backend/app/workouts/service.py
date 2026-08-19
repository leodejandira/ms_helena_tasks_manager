from typing import Optional
from fastapi import HTTPException

from app.database import db
from app.workouts.parser import parse_workout_text, WorkoutParseError


def parse_workout(text: str) -> dict:
    try:
        parsed = parse_workout_text(text)
    except WorkoutParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return parsed.model_dump()


def create_workout(payload: dict) -> dict:
    if not payload.get("exercises") or not any(ex.get("sets") for ex in payload["exercises"]):
        raise HTTPException(
            status_code=422,
            detail="Treino sem exercícios/séries não pode ser salvo.",
        )

    # Persistência transacional: workouts + workout_sets são gravados dentro
    # de uma única função Postgres (create_workout_with_sets, ver migration),
    # então um erro no meio do processo desfaz tudo — nunca fica um treino
    # parcialmente salvo (seção 17 dos requisitos).
    resp = db.rpc("create_workout_with_sets", {"payload": payload}).execute()
    result = resp.data
    workout_id = result.get("id") if isinstance(result, dict) else result
    if not workout_id:
        raise HTTPException(status_code=500, detail="Falha ao salvar o treino.")
    return get_workout(workout_id)


def list_workouts() -> list:
    resp = db.table("workouts").select("*").order("workout_date", desc=True).order("created_at", desc=True).execute()
    workouts = resp.data
    if not workouts:
        return []

    ids = [w["id"] for w in workouts]
    sets_resp = (
        db.table("workout_sets")
        .select("workout_id, exercise_order")
        .in_("workout_id", ids)
        .execute()
    )

    set_counts: dict = {}
    exercise_orders: dict = {}
    for row in sets_resp.data:
        wid = row["workout_id"]
        set_counts[wid] = set_counts.get(wid, 0) + 1
        exercise_orders.setdefault(wid, set()).add(row["exercise_order"])

    for w in workouts:
        w["set_count"] = set_counts.get(w["id"], 0)
        w["exercise_count"] = len(exercise_orders.get(w["id"], set()))

    return workouts


def get_workout(workout_id: int) -> dict:
    resp = db.table("workouts").select("*").eq("id", workout_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Treino não encontrado")
    workout = resp.data[0]

    sets_resp = (
        db.table("workout_sets")
        .select("*")
        .eq("workout_id", workout_id)
        .order("exercise_order")
        .order("set_number")
        .execute()
    )
    workout["sets"] = sets_resp.data
    return workout


def delete_workout(workout_id: int) -> None:
    get_workout(workout_id)
    db.table("workouts").delete().eq("id", workout_id).execute()
