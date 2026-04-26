from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class CropType(str, Enum):
    Corn = "Corn"
    Wheat = "Wheat"
    Potato = "Potato"
    Rice = "Rice"
    Tomato = "Tomato"


class SoilType(str, Enum):
    Clay = "Clay"
    Sandy = "Sandy"
    Loam = "Loam"
    Silty = "Silty"
    Peaty = "Peaty"


class CropCreate(BaseModel):
    crop_name: CropType
    field_name: str | None = None
    soil_type: SoilType | None = None
    area: float | None = None
    growth_stage: str | None = None
    planting_date: datetime | None = None
    last_watered_date: datetime | None = None
    last_fertilized_date: datetime | None = None


class CropResponse(BaseModel):
    id: int
    farmer_id: int
    crop_name: CropType
    field_name: str | None
    soil_type: SoilType | None
    area: float | None
    growth_stage: str | None
    planting_date: datetime | None
    last_watered_date: datetime | None
    last_fertilized_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
