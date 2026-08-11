from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date

from models.daily_task_model import (
    DailyTaskCreate,
    DailyTaskResponse,
    DailyTaskReorderRequest,
)
from controllers.daily_task_controller import DailyTaskController
from config.database import db


router = APIRouter(
    prefix="/daily-tasks",
    tags=["Daily Tasks"]
)


def get_daily_task_controller():
    return DailyTaskController(db)


@router.get(
    "/",
    response_model=list[DailyTaskResponse]
)
def list_daily_tasks(
    task_date: Optional[date] = Query(None, alias="date"),
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        return controller.get_daily_tasks(task_date=task_date)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/",
    response_model=DailyTaskResponse,
    status_code=201
)
def create_daily_task(
    payload: DailyTaskCreate,
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        return controller.create_daily_task(payload)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete(
    "/{daily_task_id}",
    status_code=204
)
def delete_daily_task(
    daily_task_id: int,
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        controller.delete_daily_task(daily_task_id)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.put(
    "/reorder",
    response_model=list[DailyTaskResponse]
)
def reorder_daily_tasks(
    payload: DailyTaskReorderRequest,
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        return controller.reorder_daily_tasks(payload)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/{daily_task_id}/complete",
    response_model=DailyTaskResponse
)
def complete_daily_task(
    daily_task_id: int,
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        return controller.complete_daily_task(daily_task_id)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.patch(
    "/{daily_task_id}/cancel",
    response_model=DailyTaskResponse
)
def cancel_daily_task(
    daily_task_id: int,
    controller: DailyTaskController = Depends(get_daily_task_controller)
):
    try:
        return controller.cancel_daily_task(daily_task_id)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
