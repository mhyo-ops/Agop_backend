from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True, nullable=False)
    water_quantity = Column(Float, nullable=False)
    fertilizer_qty = Column(Float)
    logged_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("Crop", back_populates="daily_logs")
