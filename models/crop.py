from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    crop_name = Column(String(100), nullable=False)
    field_name = Column(String(100))
    soil_type = Column(String(50))
    area = Column(Float)
    growth_stage = Column(String(50))
    planting_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_watered_date = Column(DateTime)
    last_fertilized_date = Column(DateTime)
    farmer = relationship("User", back_populates="crops")
    daily_logs = relationship("DailyLog", back_populates="crop", cascade="all, delete")
    recommendations = relationship("Recommendation", back_populates="crop", cascade="all, delete")
    tasks = relationship("Task", back_populates="crop", cascade="all, delete")
