from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.crop import Crop
from schemas.crop import CropCreate, CropResponse
from typing import List
from crud.crops import (
    create_crop as crud_create_crop,
    get_all_crops as crud_get_all_crops,
    get_crop_by_id as crud_get_crop_by_id,
    update_crop as crud_update_crop,
    delete_crop as crud_delete_crop,
)

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(farmer_id: int, data: CropCreate, db: Session = Depends(get_db)):
    return crud_create_crop(db, farmer_id, data)


@router.get("/", response_model=List[CropResponse])
def get_crops(farmer_id: int, db: Session = Depends(get_db)):
    return crud_get_all_crops(db, farmer_id)


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, db: Session = Depends(get_db)):
    crop = crud_get_crop_by_id(db, crop_id)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    return crop


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(crop_id: int, data: CropCreate, db: Session = Depends(get_db)):
    crop = crud_update_crop(db, crop_id, data)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    return crop


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(crop_id: int, db: Session = Depends(get_db)):
    if not crud_delete_crop(db, crop_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
