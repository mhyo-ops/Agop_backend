from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task
from models.crop import Crop
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from typing import List
from datetime import datetime
from services.irrigation import get_irrigation_advice

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):

    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    new_task = Task(
        crop_id=data.crop_id,
        description=data.description,
        due_date=data.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@router.get("/{crop_id}", response_model=List[TaskResponse])
def get_tasks(crop_id: int, db: Session = Depends(get_db)):

    tasks = db.query(Task).filter(Task.crop_id == crop_id).all()
    return tasks


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task.is_done = data.is_done
    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()


@router.post("/generate/{crop_id}", response_model=List[TaskResponse])
def generate_tasks(
    crop_id: int,
    lat: float = Query(...),
    lon: float = Query(...),
    region: str = Query("North"),
    fertilizer: bool = Query(True),
    db: Session = Depends(get_db)
):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    # Calculate days to harvest
    if crop.planting_date:
        days_to_harvest = (datetime.utcnow() - crop.planting_date).days
    else:
        days_to_harvest = 90  # default

    try:
        advice = get_irrigation_advice(
            lat=lat,
            lon=lon,
            crop_type=crop.crop_name,
            soil_type=crop.soil_type or "Clay",
            region=region,
            fertilizer=fertilizer,
            days_to_harvest=days_to_harvest
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create tasks based on advice
    tasks = []
    if advice["should_irrigate"]:
        task_desc = f"Irrigate {crop.crop_name} - {advice['reason']}"
        new_task = Task(
            crop_id=crop_id,
            description=task_desc,
            due_date=datetime.utcnow()  # due today
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        tasks.append(new_task)
    else:
        # Maybe create a monitoring task
        task_desc = f"Monitor {crop.crop_name} - {advice['reason']}"
        new_task = Task(
            crop_id=crop_id,
            description=task_desc,
            due_date=None  # no due date
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        tasks.append(new_task)

    return tasks
