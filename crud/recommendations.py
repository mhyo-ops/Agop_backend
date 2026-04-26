from sqlalchemy.orm import Session
from typing import List
from models.recommendation import Recommendation
from schemas.recommendation import RecommendationCreate


def create_recommendation(db: Session, rec_data: RecommendationCreate) -> Recommendation:
    new_rec = Recommendation(**rec_data.model_dump())
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    return new_rec


def get_recommendations_by_crop(db: Session, crop_id: int) -> List[Recommendation]:
    return db.query(Recommendation).filter(Recommendation.crop_id == crop_id).all()