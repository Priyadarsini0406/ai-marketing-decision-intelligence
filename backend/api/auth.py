import hashlib
import hmac
import secrets
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.connection import get_db
from database.models import User, LoginSession

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer = HTTPBearer(auto_error=False)
Role = Literal["admin", "marketer", "data_scientist", "executive"]

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000).hex()
    return f"{salt}${digest}"

def verify_password(password, encoded):
    salt, expected = encoded.split("$")
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000).hex()
    return hmac.compare_digest(actual, expected)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def public_user(user):
    return {key: getattr(user, key) for key in ("id", "name", "email", "role", "active")}

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1] or any(c.isspace() for c in value):
            raise ValueError("Enter a valid email address")
        return value

class NewUser(Credentials):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    role: Role = "marketer"

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError("Name is required")
        return value.strip()

def create_user(data, db):
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    db.refresh(user)
    return user

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    session = db.get(LoginSession, token_hash(credentials.credentials)) if credentials else None
    user = db.get(User, session.user_id) if session and session.expires_at > time.time() else None
    if not user or not user.active:
        raise HTTPException(401, "Please sign in again")
    return user

def require_admin(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return user

@router.post("/register", status_code=201)
def register(data: NewUser, db: Session = Depends(get_db)):
    if data.role == "admin":
        raise HTTPException(403, "Only an administrator can create admin accounts")
    return public_user(create_user(data, db))

@router.post("/login")
def login(data: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    # Perform the same expensive hash operation for unknown accounts.
    encoded = user.password_hash if user else "0" * 32 + "$" + "0" * 64
    valid = verify_password(data.password, encoded)
    if not user or not valid or not user.active:
        raise HTTPException(401, "Invalid email or password")
    token = secrets.token_urlsafe(32)
    db.query(LoginSession).filter(LoginSession.expires_at <= time.time()).delete()
    db.add(LoginSession(token_hash=token_hash(token), user_id=user.id, expires_at=time.time() + 28800))
    db.commit()
    return {"token": token, "user": public_user(user)}

@router.get("/me")
def me(user: User = Depends(current_user)):
    return public_user(user)

@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if credentials:
        db.query(LoginSession).filter(LoginSession.token_hash == token_hash(credentials.credentials)).delete()
        db.commit()
    return {"message": "Signed out"}
