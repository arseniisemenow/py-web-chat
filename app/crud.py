from sqlalchemy.orm import Session
from .models import Message
from .schemas import MessageCreate
from . import models, schemas
from sqlalchemy import desc
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_message(db: Session, message: MessageCreate):
    db_message = Message(content=message.content, session_id=message.session_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_last_messages(db: Session, limit: int = 5):
    messages = db.query(Message).all()
    last_messages = messages[-limit:]
    return last_messages


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
