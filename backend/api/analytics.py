from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import ChannelMetric

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/channels")
def get_channel_metrics(db: Session = Depends(get_db)):
    metrics = db.query(ChannelMetric).all()
    return metrics
