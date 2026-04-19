from pydantic import BaseModel
from datetime import datetime


class RecommendationCreate(BaseModel):
    crop_id: int
    message: str
    recommendation_type: str | None = None


class RecommendationResponse(BaseModel):
    id: int
    crop_id: int
    message: str
    recommendation_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True
