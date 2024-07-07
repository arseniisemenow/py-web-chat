from sqlalchemy.orm import Session
from .models import Message
from .schemas import MessageCreate


def create_message(db: Session, message: MessageCreate):
    db_message = Message(content=message.content, session_id=message.session_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Message).offset(skip).limit(limit).all()