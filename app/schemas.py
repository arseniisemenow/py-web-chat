from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str
