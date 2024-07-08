from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    session_id = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="messages")

