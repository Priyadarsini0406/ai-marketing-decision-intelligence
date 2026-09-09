from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Lead, MLPrediction

router = APIRouter(prefix="/leads", tags=["leads"])

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
