import logging
import os
from jose import jws
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from uuid import uuid4
from .models import Base, Message, User
from .schemas import MessageCreate
from .crud import create_message, get_last_messages

from .database import SessionLocal, engine
from passlib.context import CryptContext

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from . import models, schemas, crud, auth
from .database import engine
from .auth import (
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_active_user,
    get_db
)

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


@app.get("/sign-up")
async def read_sign_up(request: Request):
    return auth.templates.TemplateResponse("sign_up.html", {"request": request})


@app.post("/sign-up")
async def sign_up(
        response: Response,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    db_user = crud.get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)
    user = schemas.UserCreate(username=username, email=email, password=hashed_password)
    crud.create_user(db=db, user=user)

    return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)


@app.get("/auth")
async def read_auth(request: Request):
    return auth.templates.TemplateResponse("auth.html", {"request": request})


@app.post("/auth")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    # return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)


@app.get("/chat")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    # logging.debug(f"Current user: {current_user.username}")
    return {"message": f"Hello, {current_user.username}!"}



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
    session_id = str(uuid4())
    await manager.connect(websocket)
    try:
        # Send message history
        messages = get_last_messages(db)
        for message in messages:
            await websocket.send_text(f"{message.session_id}: {message.content}")

        while True:
            data = await websocket.receive_text()
            message_data = {"content": data, "session_id": session_id}
            create_message(db, MessageCreate(**message_data))
            await manager.broadcast(f"{session_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# @app.get("/")
# async def get(request: Request):
#     return auth.templates.TemplateResponse("index.html", {"request": request})
