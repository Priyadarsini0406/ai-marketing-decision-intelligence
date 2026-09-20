from fastapi import APIRouter, Depends, HTTPException, Query
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

@router.get("", include_in_schema=False)
@router.get("/")
def get_leads(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str = "", db: Session = Depends(get_db)):
    query = db.query(Lead)
    if search.strip():
        query = query.filter(Lead.customer_id.contains(search.strip(), autoescape=True))
    leads = query.order_by(Lead.customer_id).offset(skip).limit(limit).all()
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

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.exc import IntegrityError

class LeadInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid', str_strip_whitespace=True)
    customer_id: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=100)
    income: float = Field(ge=0)
    campaign_channel: str = Field(min_length=1, max_length=100)
    campaign_type: str = Field(min_length=1, max_length=100)
    ad_spend: float = Field(ge=0)
    click_through_rate: float = Field(ge=0, le=1)
    conversion_rate: float = Field(ge=0, le=1)
    website_visits: int = Field(ge=0)
    pages_per_visit: float = Field(ge=0)
    time_on_site: float = Field(ge=0)
    social_shares: int = Field(ge=0)
    email_opens: int = Field(ge=0)
    email_clicks: int = Field(ge=0)
    previous_purchases: int = Field(ge=0)
    loyalty_points: int = Field(ge=0)
    conversion: bool | None = None

def commit_lead(db, lead):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Customer ID already exists')
    db.refresh(lead)
    return lead

@router.post('', status_code=201)
def create_lead(data: LeadInput, db: Session = Depends(get_db)):
    lead = Lead(**data.model_dump())
    db.add(lead)
    return commit_lead(db, lead)

@router.put('/{lead_id}')
def update_lead(lead_id: str, data: LeadInput, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None: raise HTTPException(404, 'Lead not found')
    for key, value in data.model_dump().items(): setattr(lead, key, value)
    db.query(MLPrediction).filter_by(lead_id=lead_id).delete()
    return commit_lead(db, lead)
