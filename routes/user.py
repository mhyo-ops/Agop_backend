from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.verification import VerificationCode
from schemas.user import UserRegister, UserLogin, UserResponse
from crud.users import (
    create_user as crud_create_user,
    authenticate_user as crud_authenticate_user,
    get_user_by_email,
    verify_user,
)
from auth import create_token, get_current_user
from email_service import send_verification_email, generate_code
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    # Check if email exists
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    # Check if username exists
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create user (unverified)
    user = crud_create_user(db, data)

    # Generate verification code
    code = generate_code()
    verification = VerificationCode(
        user_id=user.id,
        code=code,
        created_at=datetime.utcnow()
    )
    db.add(verification)
    db.commit()

    # Send email (async)
    import asyncio
    asyncio.create_task(send_verification_email(user.email, code))

    return user


@router.post("/verify")
def verify_email(email: str, code: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    verification = db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.code == code
    ).first()

    if not verification:
        raise HTTPException(status_code=400, detail="Invalid code")

    # Check if code is expired (10 minutes)
    if datetime.utcnow() - verification.created_at > timedelta(minutes=10):
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail="Code expired")

    # Verify user and delete code
    verify_user(db, user)
    db.delete(verification)
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = crud_authenticate_user(db, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )

    token = create_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
