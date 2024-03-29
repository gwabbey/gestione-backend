import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib import pwd
from passlib.context import CryptContext

import app.models as models
import app.schemas as schemas
from app.database import SessionLocal, get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == token_data.username).join(models.Client,
                                                                                          models.User.client_id == models.Client.id).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    return current_user


async def is_admin(current_user: models.User = Depends(get_current_user)):
    if not current_user.role_id == 1:
        raise HTTPException(status_code=403, detail="Non sei autorizzato a fare questa operazione.")
    return current_user


def get_user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto.")


async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido o scaduto.")
    return user_id


def reset_password(db: SessionLocal, user_id: int):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    tmp_password = pwd.genword()
    tmp_password_hashed = get_password_hash(tmp_password)
    user.temp_password = tmp_password
    user.hashed_password = tmp_password_hashed
    db.add(user)
    db.commit()
    db.refresh(user)
