import hashlib
import hmac
import secrets
import time
import os
import re
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.connection import get_db
from database.models import User, LoginSession


router = APIRouter(prefix="/auth", tags=["authentication"])
bearer = HTTPBearer(auto_error=False)
Role = Literal["admin", "student", "admission_manager", "marketing_manager"]

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
    payload = {key: getattr(user, key) for key in ("id", "name", "email", "role", "active")}
    payload["profile"] = getattr(user, "profile", None) or {}
    return payload

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
    role: Role = "student"
    institution: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError("Name is required")
        return value.strip()

Gender = Literal["female", "male", "other", "prefer_not_to_say"]
PROFILE_TEXT = {
    "door_no": "Door / house number",
    "street": "Street",
    "area": "Area or locality",
    "city": "City",
    "district": "District",
    "state": "State",
}

class StudentRegistration(NewUser):
    """Public sign-up contract. Every field is mandatory and the account is
    always created with the student role: manager and administrator accounts
    can only be issued by an administrator."""

    date_of_birth: date
    gender: Gender
    mobile: str = Field(min_length=10, max_length=15)
    door_no: str = Field(min_length=1, max_length=40)
    street: str = Field(min_length=1, max_length=160)
    area: str = Field(min_length=1, max_length=160)
    city: str = Field(min_length=1, max_length=80)
    district: str = Field(min_length=1, max_length=80)
    state: str = Field(min_length=1, max_length=80)
    pincode: str = Field(min_length=6, max_length=6)
    qualification: str = Field(min_length=1, max_length=120)
    institution: str = Field(min_length=1, max_length=160)
    completion_year: int = Field(ge=1950, le=date.today().year + 1)
    course_interested: str = Field(min_length=1, max_length=120)

    @field_validator("gender", mode="before")
    @classmethod
    def normalise_gender(cls, value):
        return str(value).strip().lower()

    @field_validator("mobile")
    @classmethod
    def valid_mobile(cls, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) != 10:
            raise ValueError("Enter a 10 digit mobile number")
        return digits

    @field_validator("pincode")
    @classmethod
    def valid_pincode(cls, value):
        if not re.fullmatch(r"\d{6}", value.strip()):
            raise ValueError("Enter a valid 6 digit PIN code")
        return value.strip()

    @model_validator(mode="after")
    def validate_details(self):
        blanks = [label for field, label in PROFILE_TEXT.items() if not str(getattr(self, field)).strip()]
        if blanks:
            raise ValueError(f"{blanks[0]} is required")
        if not str(self.qualification).strip() or not str(self.institution).strip():
            raise ValueError("Qualification and institution are required")
        if not str(self.course_interested).strip():
            raise ValueError("Course interested is required")
        if self.date_of_birth >= date.today():
            raise ValueError("Date of birth must be in the past")
        if (date.today() - self.date_of_birth).days < 3650:
            raise ValueError("You must be at least 10 years old to register")
        return self

    @property
    def profile(self) -> dict:
        return {
            "date_of_birth": self.date_of_birth.isoformat(),
            "gender": self.gender,
            "mobile": self.mobile,
            "door_no": self.door_no.strip(),
            "street": self.street.strip(),
            "area": self.area.strip(),
            "city": self.city.strip(),
            "district": self.district.strip(),
            "state": self.state.strip(),
            "pincode": self.pincode,
            "qualification": self.qualification.strip(),
            "institution": self.institution.strip(),
            "completion_year": self.completion_year,
            "course_interested": self.course_interested.strip(),
        }

def create_user(data, db):
    profile = dict(getattr(data, "profile", None) or {})
    institution = getattr(data, "institution", None)
    if institution and not profile.get("institution"):
        profile["institution"] = institution
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        profile=profile or None,
    )
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

def require_manager(user: User = Depends(current_user)):
    if user.role not in ("admission_manager", "marketing_manager"):
        raise HTTPException(403, "Admission or marketing manager access required")
    return user

@router.post("/register", status_code=201)
def register(data: StudentRegistration, db: Session = Depends(get_db)):
    # Public registration only ever produces a student account. Manager and
    # administrator accounts are issued by an administrator.
    data.role = "student"
    return public_user(create_user(data, db))

@router.post("/login")
def login(data: Credentials, db: Session = Depends(get_db)):
    # Local demo users go through normal authentication and never exist when
    # APP_ENV is production. The backend remains the source of the user role.
    demo_enabled = os.getenv("APP_ENV", "development").lower() in ("development", "demo")
    demo_accounts = {
        os.getenv("DEMO_STUDENT_EMAIL", "student@test.com").lower(): ("student", os.getenv("DEMO_STUDENT_PASSWORD", "Student@123")),
        os.getenv("DEMO_MANAGER_EMAIL", "manager@test.com").lower(): ("admission_manager", os.getenv("DEMO_MANAGER_PASSWORD", "Manager@123")),
        os.getenv("DEMO_ADMIN_EMAIL", "admin@test.com").lower(): ("admin", os.getenv("DEMO_ADMIN_PASSWORD", "Admin@123")),
    }
    is_demo = demo_enabled and data.email in demo_accounts

    user = db.query(User).filter(User.email == data.email).first()

    if is_demo and not user:
        role, demo_password = demo_accounts[data.email]
        user = User(
            name=data.email.split("@")[0].title().replace("_", " "),
            email=data.email,
            password_hash=hash_password(demo_password),
            role=role,
            active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not is_demo:
        # Perform the same expensive hash operation for unknown accounts.
        encoded = user.password_hash if user else "0" * 32 + "$" + "0" * 64
        valid = verify_password(data.password, encoded)
        if not user or not valid or not user.active:
            raise HTTPException(401, "Invalid email or password")
    elif not user.active:
        raise HTTPException(401, "Account disabled")
    elif not verify_password(data.password, user.password_hash):
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
