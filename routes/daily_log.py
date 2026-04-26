from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.daily_log import DailyLog
from models.crop import Crop
from schemas.daily_log import DailyLogCreate, DailyLogResponse
from typing import List
from crud.daily_logs import (
    create_daily_log as crud_create_daily_log,
    get_daily_logs_by_crop as crud_get_daily_logs_by_crop,
)

router = APIRouter(prefix="/logs", tags=["Daily Logs"])


@router.post("/", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
def submit_log(data: DailyLogCreate, db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    return crud_create_daily_log(db, data)


@router.get("/{crop_id}", response_model=List[DailyLogResponse])
def get_logs(crop_id: int, db: Session = Depends(get_db)):
    return crud_get_daily_logs_by_crop(db, crop_id)
