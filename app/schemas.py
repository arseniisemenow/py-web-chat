from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str
    session_id: str

class Message(BaseModel):
    id: int
    content: str
    session_id: str

    class Config:
        orm_mode = True