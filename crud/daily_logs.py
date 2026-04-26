from sqlalchemy.orm import Session
from typing import List
from models.daily_log import DailyLog
from schemas.daily_log import DailyLogCreate


def create_daily_log(db: Session, log_data: DailyLogCreate) -> DailyLog:
    new_log = DailyLog(**log_data.model_dump())
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


def get_daily_logs_by_crop(db: Session, crop_id: int) -> List[DailyLog]:
    return db.query(DailyLog).filter(DailyLog.crop_id == crop_id).all()