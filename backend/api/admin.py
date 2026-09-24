import csv
import io
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path
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
        raise HTTPException(413, "Upload must be no larger than 5 MB")
    if (file.filename or '').lower().endswith('.zip') or zipfile.is_zipfile(io.BytesIO(raw)):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = [member for member in archive.infolist()
                           if not member.is_dir() and member.filename.lower().endswith('.csv')
                           and not member.filename.startswith('__MACOSX/')]
                if len(members) != 1:
                    raise HTTPException(400, "ZIP must contain exactly one CSV file")
                if members[0].file_size > 5 * 1024 * 1024:
                    raise HTTPException(413, "CSV inside ZIP must be no larger than 5 MB")
                # Read only the selected member into memory; never extract paths to disk.
                with archive.open(members[0]) as stream:
                    raw = stream.read(5 * 1024 * 1024 + 1)
                if len(raw) > 5 * 1024 * 1024:
                    raise HTTPException(413, "CSV inside ZIP must be no larger than 5 MB")
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError) as exc:
            raise HTTPException(400, "Cannot read ZIP. Upload a valid, unencrypted ZIP containing one CSV.") from exc
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
    item = Dataset(name=(file.filename or "Student Admission dataset")[:200], columns=columns, rows=rows, created_at=time.time())
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
                    "admissions": sum(bool(l.admission_status) for l in leads),
                    "ad_spend": sum(l.ad_spend or 0 for l in leads),
                    "high_probability_leads": sum((p.admission_probability or 0) >= config["conversion_threshold"] for p in predictions)},
        "channels": [serialize(c) for c in db.query(ChannelMetric).all()],
        "simulations": [serialize(s) for s in db.query(BudgetSimulation).all()],
        "predictions": [serialize(p) for p in predictions],
        "leads": [serialize(l) for l in leads],
        "datasets": [dataset_summary(d) for d in datasets],
    }

ML_ROOT = Path(__file__).resolve().parents[2] / "ml"
EVALUATION_PATH = ML_ROOT / "reports" / "lead_conversion_evaluation.txt"
METADATA_PATH = ML_ROOT / "models" / "lead_conversion_metadata.json"

def _parse_evaluation_table(path: Path) -> list[dict]:
    """Parse the model comparison table produced by the training pipeline.

    The report is the single source of truth written by training; model metrics
    are read from it rather than being copied into this API.
    """
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = next(
        (i for i, line in enumerate(lines) if line.split("|")[0].strip().lower() == "model"),
        None,
    )
    if header_index is None:
        return []
    header = [part.strip().lower().replace(" ", "_").replace("-", "_") for part in lines[header_index].split("|")]

    def numeric(value: str | None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    models = []
    for line in lines[header_index + 1:]:
        if "|" not in line:
            break
        record = dict(zip(header, [part.strip() for part in line.split("|")]))
        model = {
            "name": record.get("model", "").strip(),
            "accuracy": numeric(record.get("accuracy")),
            "precision": numeric(record.get("precision")),
            "recall": numeric(record.get("recall")),
            "f1": numeric(record.get("f1")),
            "roc_auc": numeric(record.get("roc_auc")),
        }
        if model["name"] and all(v is not None for v in list(model.values())[1:]):
            models.append(model)
    return models


@router.get("/ml/model-performance")
def model_performance():
    """Dynamic model performance derived from the existing ML evaluation output.

    Reads ml/reports/lead_conversion_evaluation.txt (all models) and
    ml/models/lead_conversion_metadata.json (selected model, thresholds). No
    metrics are duplicated or hard-coded here; when training is re-run the
    report and metadata update and this endpoint reflects the new values.
    """
    metadata = None
    if METADATA_PATH.exists():
        try:
            metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            metadata = None

    models = _parse_evaluation_table(EVALUATION_PATH)

    # Fallback for a metadata-only install: expose the selected model's metrics.
    if not models and metadata and isinstance(metadata.get("metrics"), dict):
        metrics = metadata["metrics"]
        models = [{
            "name": metadata.get("selected_model") or "Selected model",
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1": metrics.get("f1"),
            "roc_auc": metrics.get("roc_auc"),
        }]

    selected_model = metadata.get("selected_model") if metadata else None
    if selected_model and not any(m["name"] == selected_model for m in models):
        selected_model = None

    evaluated_at = None
    for path in (EVALUATION_PATH, METADATA_PATH):
        if path.exists():
            evaluated_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
            break

    return {
        "available": bool(models),
        "selected_model": selected_model,
        "evaluated_at": evaluated_at,
        "target_column": metadata.get("target_column") if metadata else None,
        "random_state": metadata.get("random_state") if metadata else None,
        "thresholds": metadata.get("thresholds") if metadata else None,
        "models": models,
        "source": {
            "evaluation": EVALUATION_PATH.name if EVALUATION_PATH.exists() else None,
            "metadata": METADATA_PATH.name if METADATA_PATH.exists() else None,
        },
    }
