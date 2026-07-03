"""Endpoint auth: register, login, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from . import db
from .models import Token, UserCreate, UserPublic
from .security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate):
    if db.get_user_by_username(payload.username) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username sudah dipakai")
    row = db.create_user(payload.username, hash_password(payload.password))
    return UserPublic(id=row["id"], username=row["username"], is_admin=bool(row["is_admin"]))


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Username atau password salah")
    row = db.get_user_by_username(form_data.username)
    if row is None or not verify_password(form_data.password, row["hashed_password"]):
        raise invalid
    return Token(access_token=create_access_token(row["username"]))


@router.get("/me", response_model=UserPublic)
def me(user: UserPublic = Depends(get_current_user)):
    return user
