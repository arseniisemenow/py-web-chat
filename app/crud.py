from sqlalchemy.orm import Session
from .models import Message
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_message(db: Session, message: schemas.MessageCreate):
    db_message = models.Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_last_messages(db: Session, limit: int = 5):
    messages = db.query(Message).all()
    last_messages = messages[-limit:]
    return last_messages


# def get_last_messages(db: Session, limit: int = 10):
#     return db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(limit).all()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_users(db: Session):
    return db.query(models.User).all()