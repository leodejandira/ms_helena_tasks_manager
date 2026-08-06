from fastapi import APIRouter, HTTPException, Depends, Query
from models.item_model import ItemCreate, ItemUpdate, ItemResponse
from controllers.item_controller import ItemController
from config.database import db
from typing import Optional, List

router = APIRouter(prefix="/items", tags=["Items"])

def get_item_controller():
    return ItemController(db)

@router.post("/", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate, controller: ItemController = Depends(get_item_controller)):
    try:
        return controller.create_item(item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[ItemResponse])
def list_items(
    grupo: Optional[str] = Query(None, description="Filtrar por grupo específico"),
    status: Optional[str] = Query(None, description="Filtrar por status específico"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria específica"),
    controller: ItemController = Depends(get_item_controller)
):
    try:
        return controller.get_items(grupo=grupo, status=status, categoria=categoria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, controller: ItemController = Depends(get_item_controller)):
    try:
        return controller.update_item(item_id, item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, controller: ItemController = Depends(get_item_controller)):
    try:
        controller.delete_item(item_id)
        return
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))