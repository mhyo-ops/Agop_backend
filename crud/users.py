from sqlalchemy.orm import Session
import hashlib
from models.user import User
from schemas.user import UserRegister, UserLogin


def create_user(db: Session, user_data: UserRegister) -> User:
    hashed = hashlib.sha256(user_data.password.encode()).hexdigest()
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, login_data: UserLogin) -> User | None:
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        return None
    hashed = hashlib.sha256(login_data.password.encode()).hexdigest()
    if hashed != user.password_hash:
        return None
    return user