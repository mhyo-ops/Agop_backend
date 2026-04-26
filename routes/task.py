from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models.crop import Crop
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from services.irrigation import get_irrigation_advice
from crud.tasks import (
    create_task as crud_create_task,
    get_tasks_by_crop as crud_get_tasks_by_crop,
    update_task as crud_update_task,
    delete_task as crud_delete_task,
)
from auth import get_current_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tasks for this crop"
        )
    return crud_create_task(db, data)


@router.get("/{crop_id}", response_model=List[TaskResponse])
def get_tasks(crop_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view tasks for this crop"
        )
    return crud_get_tasks_by_crop(db, crop_id)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # First check if task exists and belongs to user's crop
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    crop = db.query(Crop).filter(Crop.id == task.crop_id).first()
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this task"
        )
    updated_task = crud_update_task(db, task_id, data)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # First check if task exists and belongs to user's crop
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    crop = db.query(Crop).filter(Crop.id == task.crop_id).first()
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
    if not crud_delete_task(db, task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.post("/generate/{crop_id}", response_model=List[TaskResponse])
def generate_tasks(
    crop_id: int,
    lat: float = Query(...),
    lon: float = Query(...),
    region: str = Query("North"),
    fertilizer: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate tasks for this crop"
        )

    if crop.planting_date:
        days_to_harvest = (datetime.utcnow() - crop.planting_date).days
    else:
        days_to_harvest = 90

    try:
        advice = get_irrigation_advice(
            lat=lat,
            lon=lon,
            crop_type=crop.crop_name,
            soil_type=crop.soil_type or "Clay",
            region=region,
            fertilizer=fertilizer,
            days_to_harvest=days_to_harvest,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tasks = []
    if advice["should_irrigate"]:
        task_desc = f"Irrigate {crop.crop_name} - {advice['reason']}"
        task_data = TaskCreate(crop_id=crop_id, description=task_desc, due_date=datetime.utcnow())
        new_task = crud_create_task(db, task_data)
        tasks.append(new_task)
    else:
        task_desc = f"Monitor {crop.crop_name} - {advice['reason']}"
        task_data = TaskCreate(crop_id=crop_id, description=task_desc, due_date=None)
        new_task = crud_create_task(db, task_data)
        tasks.append(new_task)

    return tasks
