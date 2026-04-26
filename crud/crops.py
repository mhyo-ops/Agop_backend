from sqlalchemy.orm import Session
from typing import List
from models.crop import Crop
from schemas.crop import CropCreate


def create_crop(db: Session, farmer_id: int, crop_data: CropCreate) -> Crop:
    new_crop = Crop(farmer_id=farmer_id, **crop_data.model_dump())
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return new_crop


def get_all_crops(db: Session, farmer_id: int) -> List[Crop]:
    return db.query(Crop).filter(Crop.farmer_id == farmer_id).all()


def get_crop_by_id(db: Session, crop_id: int) -> Crop | None:
    return db.query(Crop).filter(Crop.id == crop_id).first()


def update_crop(db: Session, crop_id: int, crop_data: CropCreate) -> Crop | None:
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        return None
    for key, value in crop_data.model_dump(exclude_unset=True).items():
        setattr(crop, key, value)
    db.commit()
    db.refresh(crop)
    return crop


def delete_crop(db: Session, crop_id: int) -> bool:
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        return False
    db.delete(crop)
    db.commit()
    return True