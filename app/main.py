import logging
from uuid import uuid4
from datetime import timedelta, datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, Form, HTTPException, status, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import Base, Message, User
from .schemas import MessageCreate
from .crud import create_message, get_last_messages, get_user_by_email
from .database import SessionLocal, engine
from . import models, schemas, crud, auth
from .auth import get_password_hash, authenticate_user, get_db

from typing import List

SECRET_KEY = "your_secret_key"  # Replace with your secret key
ALGORITHM = "HS256"

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user_from_cookie)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/users", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    users = crud.get_all_users(db)
    return users

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def validate_token(token: str) -> bool:
    """
    Validate the provided JWT token.

    This function verifies the token's signature and checks if it is valid.
    """
    try:
        # Decode the token, verifying the signature and validating its claims
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except JWTError:
        return False


def get_user_data_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None



@app.get("/sign-up")
async def read_sign_up(request: Request):
    return auth.templates.TemplateResponse("sign_up.html", {"request": request})


@app.post("/sign-up")
async def sign_up(
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
    response.set_cookie(key="access_token", value=access_token)
    # return RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)


@app.get("/chat")
async def protected_route(request: Request, current_user: User = Depends(get_current_active_user)):
    return auth.templates.TemplateResponse("index.html", {"request": request})


# return {"message": f"Hello, {current_user.username}!"}


@app.get("/user-info")
async def get_user_info(current_user: User = Depends(get_current_active_user)):
    return {"email": current_user.email}


@app.get("/logout")
async def logout(response: Response, access_token: str = Cookie(None)):
    if access_token:
        response.set_cookie(key="access_token", value="", expires=0, httponly=False)
    # return RedirectResponse(url="/auth")


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
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    if not token:
        await websocket.close(code=4000, reason="Missing token")
        return

    is_valid = validate_token(token)

    if not is_valid:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_data = get_user_data_from_token(token)
    await manager.connect(websocket)
    try:
        last_messages = get_last_messages(db, limit=10)
        for message in last_messages:
            await websocket.send_text(f"{message.timestamp.isoformat()} - {message.email}: {message.content}")

        while True:
            data = await websocket.receive_text()
            message_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "email": user_data["sub"],
                "content": data,
                "session_id": str(uuid4())
            }
            create_message(db, MessageCreate(**message_data))
            await manager.broadcast(f"{message_data['timestamp']} - {message_data['email']}: {message_data['content']}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
