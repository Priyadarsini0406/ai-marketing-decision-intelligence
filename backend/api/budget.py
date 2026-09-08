from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import BudgetSimulation

router = APIRouter(prefix="/budget", tags=["budget"])

@router.get("/simulations")
def get_simulations(db: Session = Depends(get_db)):
    simulations = db.query(BudgetSimulation).all()
    return simulations
