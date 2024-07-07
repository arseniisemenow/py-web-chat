from sqlalchemy.orm import Session
from .models import Message
from .schemas import MessageCreate
from sqlalchemy import desc

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
