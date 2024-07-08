import os

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext
from .database import SessionLocal
from .models import User
from .schemas import TokenData

SECRET_KEY = "secret_key"  # todo: change to some .env token
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))  # :D

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    token = serializer.dumps(to_encode)
    return token

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        serializer = URLSafeTimedSerializer(SECRET_KEY)
        payload = serializer.loads(token, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user
