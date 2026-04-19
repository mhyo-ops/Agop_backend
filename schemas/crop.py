from pydantic import BaseModel
from datetime import datetime


class CropCreate(BaseModel):
    crop_name: str
    field_name: str | None = None
    soil_type: str | None = None
    area: float | None = None
    growth_stage: str | None = None
    planting_date: datetime | None = None
    lastwatred_date: datetime | None = None
    lastfertilized_date: datetime | None = None


class CropResponse(BaseModel):
    id: int
    farmer_id: int
    crop_name: str
    field_name: str | None
    soil_type: str | None
    area: float | None
    growth_stage: str | None
    planting_date: datetime | None
    lastwatred_date: datetime | None
    lastfertilized_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
