from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.daily_log import DailyLog
from models.crop import Crop
from schemas.daily_log import DailyLogCreate, DailyLogResponse
from typing import List

router = APIRouter(prefix="/logs", tags=["Daily Logs"])


@router.post("/", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
def submit_log(data: DailyLogCreate, db: Session = Depends(get_db)):

    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    new_log = DailyLog(
        crop_id=data.crop_id,
        water_quantity=data.water_quantity,
        fertilizer_qty=data.fertilizer_qty
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@router.get("/{crop_id}", response_model=List[DailyLogResponse])
def get_logs(crop_id: int, db: Session = Depends(get_db)):

    logs = db.query(DailyLog).filter(DailyLog.crop_id == crop_id).all()
    return logs
