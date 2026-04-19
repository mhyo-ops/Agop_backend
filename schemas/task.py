from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    crop_id: int
    description: str
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    is_done: bool


class TaskResponse(BaseModel):
    id: int
    crop_id: int
    description: str
    due_date: datetime | None
    is_done: bool
    created_at: datetime

    class Config:
        from_attributes = True
