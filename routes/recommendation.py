from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.recommendation import Recommendation
from models.crop import Crop
from schemas.recommendation import RecommendationCreate, RecommendationResponse
from typing import List

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(data: RecommendationCreate, db: Session = Depends(get_db)):

    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    new_rec = Recommendation(
        crop_id=data.crop_id,
        message=data.message,
        recommendation_type=data.recommendation_type
    )

    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)

    return new_rec


@router.get("/{crop_id}", response_model=List[RecommendationResponse])
def get_recommendations(crop_id: int, db: Session = Depends(get_db)):

    recs = db.query(Recommendation).filter(Recommendation.crop_id == crop_id).all()
    return recs
