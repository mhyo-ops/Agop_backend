from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.crop import Crop
from schemas.recommendation import RecommendationCreate, RecommendationResponse
from typing import List
from crud.recommendations import (
    create_recommendation as crud_create_recommendation,
    get_recommendations_by_crop as crud_get_recommendations_by_crop,
)
from auth import get_current_user
from models.user import User

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(data: RecommendationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create recommendations for this crop"
        )
    return crud_create_recommendation(db, data)


@router.get("/{crop_id}", response_model=List[RecommendationResponse])
def get_recommendations(crop_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view recommendations for this crop"
        )
    return crud_get_recommendations_by_crop(db, crop_id)
