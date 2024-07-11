from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    email: str
    content: str
    timestamp: datetime
    session_id: str

class Message(MessageCreate):
    id: int

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    email: str | None = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True
