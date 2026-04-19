from pydantic import BaseModel
from datetime import datetime


class DailyLogCreate(BaseModel):
    crop_id: int
    water_quantity: float
    fertilizer_qty: float | None = None


class DailyLogResponse(BaseModel):
    id: int
    crop_id: int
    water_quantity: float
    fertilizer_qty: float | None
    logged_at: datetime

    class Config:
        from_attributes = True
