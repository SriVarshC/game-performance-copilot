"""
POST /api/auth/register — create a new user, returns a JWT
POST /api/auth/login    — authenticate, returns a JWT
GET  /api/auth/me       — return the currently logged-in user's info
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.auth.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ─── Request / Response schemas ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email:    str
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    username:     str
    user_id:      int


class UserResponse(BaseModel):
    user_id:  int
    username: str
    email:    str


# ─── Register ─────────────────────────────────────────────────────────────────
@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter((User.username == request.username) | (User.email == request.email))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.user_id), "username": user.username})
    return TokenResponse(access_token=token, username=user.username, user_id=user.user_id)


# ─── Login ────────────────────────────────────────────────────────────────────
@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token({"sub": str(user.user_id), "username": user.username})
    return TokenResponse(access_token=token, username=user.username, user_id=user.user_id)


# ─── Current user ─────────────────────────────────────────────────────────────
@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get the currently logged-in user",
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
    )