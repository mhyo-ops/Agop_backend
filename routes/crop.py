from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.crop import Crop
from schemas.crop import CropCreate, CropResponse
from typing import List

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(farmer_id: int, data: CropCreate, db: Session = Depends(get_db)):

    new_crop = Crop(
        farmer_id=farmer_id,
        crop_name=data.crop_name,
        field_name=data.field_name,
        soil_type=data.soil_type,
        area=data.area,
        growth_stage=data.growth_stage,
        planting_date=data.planting_date,
        lastwatred_date=data.lastwatred_date,
        lastfertilized_date=data.lastfertilized_date
    )

    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)

    return new_crop


@router.get("/", response_model=List[CropResponse])
def get_crops(farmer_id: int, db: Session = Depends(get_db)):

    crops = db.query(Crop).filter(Crop.farmer_id == farmer_id).all()
    return crops


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, db: Session = Depends(get_db)):

    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    return crop


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(crop_id: int, db: Session = Depends(get_db)):

    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )

    db.delete(crop)
    db.commit()
