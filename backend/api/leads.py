from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Lead, MLPrediction

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("", include_in_schema=False)
@router.get("/")
def get_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads

@router.get("/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    return lead

@router.get("/{lead_id}/prediction")
def get_lead_prediction(lead_id: str, db: Session = Depends(get_db)):
    prediction = db.query(MLPrediction).filter(MLPrediction.lead_id == lead_id).first()
    return prediction
