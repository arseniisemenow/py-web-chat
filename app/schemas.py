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


class UserBase(BaseModel):
    username: str
    email: EmailStr

class TokenData(BaseModel):
    email: str | None = None

class UserCreate(UserBase):
    password: constr(min_length=8)

class User(UserBase):
    id: int

    class Config:
        orm_mode = True