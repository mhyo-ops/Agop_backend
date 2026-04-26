from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.crop import Crop
from schemas.crop import CropCreate, CropResponse
from crud.crops import (
    create_crop as crud_create_crop,
    get_all_crops as crud_get_all_crops,
    get_crop_by_id as crud_get_crop_by_id,
    update_crop as crud_update_crop,
    delete_crop as crud_delete_crop,
)
from auth import get_current_user
from models.user import User

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(data: CropCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud_create_crop(db, current_user.id, data)


@router.get("/", response_model=List[CropResponse])
def get_crops(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud_get_all_crops(db, current_user.id)


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = crud_get_crop_by_id(db, crop_id)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this crop"
        )
    return crop


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(crop_id: int, data: CropCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = crud_get_crop_by_id(db, crop_id)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this crop"
        )
    updated_crop = crud_update_crop(db, crop_id, data)
    if not updated_crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    return updated_crop


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(crop_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop = crud_get_crop_by_id(db, crop_id)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
    if crop.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this crop"
        )
    if not crud_delete_crop(db, crop_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found"
        )
