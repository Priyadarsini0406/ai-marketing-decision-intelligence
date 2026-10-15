"""Persistent student profile and enquiry endpoints."""
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from api.auth import current_user
from database.connection import get_db
from database.models import StudentEnquiry, User

router = APIRouter(prefix="/student", tags=["student portal"], dependencies=[Depends(current_user)])


def require_student(user):
    if user.role != "student":
        raise HTTPException(403, "Student access required")
    return user


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    profile: dict


class EnquiryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)
    course_interested: str = Field(min_length=1, max_length=160)
    preferred_intake: str | None = Field(default=None, max_length=80)
    preferred_mode: str | None = Field(default=None, max_length=80)
    qualification: str | None = Field(default=None, max_length=160)
    institution: str | None = Field(default=None, max_length=200)
    academic_score: float | None = Field(default=None, ge=0, le=100)
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    interest_area: str | None = Field(default=None, max_length=200)
    contact_method: str | None = Field(default=None, max_length=40)
    remarks: str | None = Field(default=None, max_length=2000)


def enquiry_record(item):
    return {column.name: getattr(item, column.name) for column in item.__table__.columns}


@router.put("/profile")
def update_profile(data: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_student(user)
    if not data.name.strip():
        raise HTTPException(400, "Name is required")
    user.name = data.name.strip()
    user.profile = data.profile
    db.commit()
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "active": user.active, "profile": user.profile or {}}


@router.get("/enquiries")
def list_enquiries(user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_student(user)
    rows = db.query(StudentEnquiry).filter_by(student_user_id=user.id).order_by(StudentEnquiry.created_at.desc()).all()
    return [enquiry_record(row) for row in rows]


@router.post("/enquiries", status_code=201)
def create_enquiry(data: EnquiryInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_student(user)
    now = time.time()
    enquiry = StudentEnquiry(id=str(uuid.uuid4()), student_user_id=user.id,
                             status="Submitted", created_at=now, updated_at=now,
                             **data.model_dump())
    db.add(enquiry)
    # Keep current admission-interest fields in the account profile so manager
    # and admin directories, which share this record, reflect the latest student submission.
    profile = dict(user.profile or {})
    for profile_key, enquiry_key in {
        "course_interested": "course_interested",
        "qualification": "qualification",
        "institution": "institution",
        "mobile": "phone",
        "city": "location",
    }.items():
        value = getattr(enquiry, enquiry_key)
        if value is not None:
            profile[profile_key] = value
    user.profile = profile
    db.commit()
    db.refresh(enquiry)
    return enquiry_record(enquiry)
