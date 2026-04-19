from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True, nullable=False)
    message = Column(Text, nullable=False)
    recommendation_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("Crop", back_populates="recommendations")
