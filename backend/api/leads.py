from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import uuid
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Lead, MLPrediction

router = APIRouter(prefix="/leads", tags=["leads"])

class LeadCreate(BaseModel):
    student_name: str = Field(min_length=1, max_length=150)
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    qualification: str | None = None
    academic_score: float | None = None
    course_interested: str | None = None
    program: str | None = None
    enquiry_source: str = "Walk-in"
    remarks: str | None = None

@router.post("/", status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(id=str(uuid.uuid4()), student_id=f"MANUAL-{uuid.uuid4().hex[:8]}", student_name=data.student_name,
        course_interested=data.course_interested, program=data.program, qualification=data.qualification,
        academic_score=data.academic_score, enquiry_source=data.enquiry_source, location=data.location,
        admission_year=date.today().year, enquiry_date=date.today().isoformat(), lead_status="New", engagement_level="Unknown",
        follow_up_status="Pending", admission_status=False, ad_spend=0)
    db.add(lead); db.commit(); db.refresh(lead)
    return lead

@router.get("/")
def get_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads

@router.get("/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead: raise HTTPException(404, "Lead not found")
    return lead

@router.get("/{lead_id}/prediction")
def get_lead_prediction(lead_id: str, db: Session = Depends(get_db)):
    prediction = db.query(MLPrediction).filter(MLPrediction.lead_id == lead_id).first()
    return prediction
