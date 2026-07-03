"""
security.py
============
Hashing password (bcrypt) + JWT (PyJWT) + dependency FastAPI untuk
mengambil user yang sedang login dari token Bearer.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .. import config
from . import db
from .models import UserPublic

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=ALGORITHM)


def _row_to_user(row) -> UserPublic:
    return UserPublic(id=row["id"], username=row["username"], is_admin=bool(row["is_admin"]))


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error

    row = db.get_user_by_username(username)
    if row is None:
        raise credentials_error
    return _row_to_user(row)


def get_current_admin_user(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Butuh akses admin")
    return user
