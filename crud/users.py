from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.user import User
from schemas.user import UserRegister, UserLogin

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_user(db: Session, user_data: UserRegister) -> User:
    hashed = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        #phone=user_data.phone,
        password_hash=hashed,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, login_data: UserLogin) -> User | None:
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        return None
    if not pwd_context.verify(login_data.password, user.password_hash):
        return None
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def verify_user(db: Session, user: User):
    user.is_verified = True
    db.commit()