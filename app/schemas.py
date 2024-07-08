from pydantic import BaseModel, EmailStr, constr


class MessageCreate(BaseModel):
    content: str
    session_id: str


class Message(BaseModel):
    id: int
    content: str
    session_id: str

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
