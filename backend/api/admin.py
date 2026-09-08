import csv
import io
import time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User, LoginSession, Dataset, SystemConfig, Lead, MLPrediction, ChannelMetric, BudgetSimulation
from api.auth import require_admin, NewUser, Role, create_user, public_user, hash_password

router = APIRouter(prefix="/admin", tags=["administration"], dependencies=[Depends(require_admin)])

class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: Role
    active: bool
    password: str | None = Field(default=None, min_length=12, max_length=128)

@router.get("/users")
def users(db: Session = Depends(get_db)):
    return [public_user(u) for u in db.query(User).order_by(User.email).all()]

@router.post("/users", status_code=201)
def add_user(data: NewUser, db: Session = Depends(get_db)):
    return public_user(create_user(data, db))

@router.put("/users/{user_id}")
def update_user(user_id: str, data: UserUpdate, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if actor.id == user.id and (not data.active or data.role != "admin"):
        raise HTTPException(400, "You cannot disable or demote your own account")
    if not data.name.strip():
        raise HTTPException(400, "Name is required")
    user.name, user.role, user.active = data.name.strip(), data.role, data.active
    if data.password:
        user.password_hash = hash_password(data.password)
    db.query(LoginSession).filter(LoginSession.user_id == user.id).delete()
    db.commit()
    return public_user(user)

def dataset_summary(item):
    return {"id": item.id, "name": item.name, "columns": item.columns, "row_count": len(item.rows), "created_at": item.created_at}

@router.get("/datasets")
def datasets(db: Session = Depends(get_db)):
    return [dataset_summary(d) for d in db.query(Dataset).order_by(Dataset.created_at.desc()).all()]

@router.post("/datasets", status_code=201)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "CSV must be no larger than 5 MB")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        columns = reader.fieldnames
        if not columns or len(columns) > 100 or any(not c.strip() for c in columns) or len(set(columns)) != len(columns):
            raise ValueError("CSV needs unique, nonempty headers (maximum 100 columns)")
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Each row must have the same number of columns as the header")
            rows.append(row)
            if len(rows) > 10000:
                raise ValueError("Maximum 10,000 rows per dataset")
        if not rows:
            raise ValueError("CSV must contain at least one data row")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(400, str(exc))
    item = Dataset(name=(file.filename or "Marketing dataset")[:200], columns=columns, rows=rows, created_at=time.time())
    db.add(item)
    db.commit()
    db.refresh(item)
    return dataset_summary(item)

@router.get("/datasets/{dataset_id}")
def preview_dataset(dataset_id: str, db: Session = Depends(get_db)):
    item = db.get(Dataset, dataset_id)
    if not item:
        raise HTTPException(404, "Dataset not found")
    return {**dataset_summary(item), "rows": item.rows[:50]}

class DatasetUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

@router.put("/datasets/{dataset_id}")
def rename_dataset(dataset_id: str, data: DatasetUpdate, db: Session = Depends(get_db)):
    item = db.get(Dataset, dataset_id)
    if not item:
        raise HTTPException(404, "Dataset not found")
    if not data.name.strip():
        raise HTTPException(400, "Name is required")
    item.name = data.name.strip()
    db.commit()
    return dataset_summary(item)

@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    item = db.get(Dataset, dataset_id)
    if not item:
        raise HTTPException(404, "Dataset not found")
    db.delete(item)
    db.commit()
    return {"message": "Dataset deleted"}

class Configuration(BaseModel):
    organization_name: str = Field(default="DecisionIntel", min_length=1, max_length=100)
    currency: Literal["USD", "INR", "EUR", "GBP"] = "USD"
    model: Literal["xgboost", "random_forest", "logistic_regression"] = "xgboost"
    conversion_threshold: float = Field(default=0.5, ge=0, le=1)
    test_size: float = Field(default=0.2, ge=0.1, le=0.4)
    random_seed: int = Field(default=42, ge=0, le=2147483647)

def configuration(db):
    config = db.get(SystemConfig, 1)
    return config.values if config else Configuration().model_dump()

@router.get("/configuration")
def get_configuration(db: Session = Depends(get_db)):
    return configuration(db)

@router.put("/configuration")
def save_configuration(data: Configuration, db: Session = Depends(get_db)):
    config = db.get(SystemConfig, 1)
    if config:
        config.values = data.model_dump()
    else:
        db.add(SystemConfig(id=1, values=data.model_dump()))
    db.commit()
    return data

def serialize(item):
    return {column.name: getattr(item, column.name) for column in item.__table__.columns}

@router.get("/reports")
def reports(db: Session = Depends(get_db)):
    config = configuration(db)
    leads = db.query(Lead).all()
    predictions = db.query(MLPrediction).all()
    datasets = db.query(Dataset).all()
    return {
        "generated_at": time.time(), "configuration": config,
        "summary": {"users": db.query(User).count(), "datasets": len(datasets),
                    "dataset_rows": sum(len(d.rows) for d in datasets), "leads": len(leads),
                    "conversions": sum(bool(l.conversion) for l in leads),
                    "ad_spend": sum(l.ad_spend or 0 for l in leads),
                    "high_probability_leads": sum((p.conversion_probability or 0) >= config["conversion_threshold"] for p in predictions)},
        "channels": [serialize(c) for c in db.query(ChannelMetric).all()],
        "simulations": [serialize(s) for s in db.query(BudgetSimulation).all()],
        "predictions": [serialize(p) for p in predictions],
        "leads": [serialize(l) for l in leads],
        "datasets": [dataset_summary(d) for d in datasets],
    }
