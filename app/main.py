import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from uuid import uuid4  # For generating unique session IDs
from .database import SessionLocal, engine
from .models import Base, Message
from .schemas import MessageCreate
from .crud import create_message, get_messages
from fastapi.templating import Jinja2Templates

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    session_id = str(uuid4())  # Generate a unique session ID for this connection
    await manager.connect(websocket)
    try:
        # Send message history
        messages = get_messages(db)
        for message in messages:
            await websocket.send_text(f"{message.session_id}: {message.content}")

        while True:
            data = await websocket.receive_text()
            message_data = {"content": data, "session_id": session_id}
            create_message(db, MessageCreate(**message_data))
            await manager.broadcast(f"{session_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


