from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True, nullable=False)
    description = Column(String(255), nullable=False)
    due_date = Column(DateTime)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("Crop", back_populates="tasks")
