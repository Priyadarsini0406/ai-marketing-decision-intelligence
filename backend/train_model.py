"""Import the real lead dataset and store XGBoost predictions with SHAP.

    python backend/train_model.py

The model itself is trained by ml/scripts/train_lead_conversion_xgboost.py; this
module owns the database side. Every stored probability comes from an
out-of-fold model, so no lead is ever scored by a model that trained on it.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete, func
from sqlalchemy import update as row_update
from sklearn.model_selection import StratifiedKFold

import ml_service as svc
from database.connection import Base, SessionLocal, engine
from database.models import MLPrediction, Lead, generate_uuid

ROOT = Path(__file__).resolve().parents[1]

# Rows written by the old seed_mock_data.py, which injected random probabilities
# and a hardcoded SHAP dict. They are removed so no fabricated score survives.
SEEDED_STUDENT_ID_PREFIX = "STU-"

# Every stored explanation must carry this marker. Anything else in
# ml_predictions is a seeded or hand-written value, not a model output.
SHAP_METHOD = "shap.TreeExplainer"

CV_FOLDS = 5
TOP_FACTORS = 5

# Supabase round-trips cost roughly 200 ms over the pooler, so a per-row flush
# would take hours for 9,240 leads. Writes are sent as chunked executemany
# batches, which keeps a full import to a few minutes.
WRITE_CHUNK = 500

# Only fields with an exact counterpart in the dataset are mapped. The database
# structure is unchanged, so columns with no real source (ad_spend, income,
# campaign_channel, email/loyalty counters) are deliberately left NULL rather
# than invented; the spend-driven analytics keep their existing 409 behaviour.
COLUMN_MAP = {
    "customer_id": svc.KEY_COLUMN,
    "conversion": svc.TARGET_COLUMN,
    "enquiry_source": "Lead Source",
    "location": "City",
    "lead_status": "Tags",
    "engagement_level": "Asymmetrique Activity Index",
    "website_visits": "TotalVisits",
    "pages_per_visit": "Page Views Per Visit",
    "time_on_site": "Total Time Spent on Website",
}

INTEGER_COLUMNS = {"website_visits"}
FLOAT_COLUMNS = {"pages_per_visit", "time_on_site"}


def _clean(value):
    """Normalise a pandas scalar into a value the database can store."""
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def _as_int(value):
    value = _clean(value)
    if value is None:
        return None
    return int(value)


def _as_float(value):
    value = _clean(value)
    if value is None:
        return None
    return float(value)


def normalise_engagement(value) -> str | None:
    """Turn Asymmetrique's '01.High' style index into a plain engagement level."""
    value = _clean(value)
    if value is None:
        return None
    text = str(value).strip()
    for prefix in ("01.", "02.", "03."):
        if text.startswith(prefix):
            return text[len(prefix):]
    return text or None


def build_lead_payload(record: dict) -> dict:
    """Map one dataset row onto the unchanged leads schema."""
    payload: dict = {}
    for column, source in COLUMN_MAP.items():
        if column == "customer_id":
            payload[column] = str(record[source])
        elif column == "conversion":
            payload[column] = bool(record[source])
        elif column == "engagement_level":
            payload[column] = normalise_engagement(record[source])
        elif column in INTEGER_COLUMNS:
            payload[column] = _as_int(record[source])
        elif column in FLOAT_COLUMNS:
            payload[column] = _as_float(record[source])
        else:
            value = _clean(record[source])
            payload[column] = str(value) if value is not None else None
    return payload


def out_of_fold_scores(
    frame: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    folds: int = CV_FOLDS,
) -> tuple[np.ndarray, list[dict]]:
    """Score every row with a model that never saw it, and explain each score.

    Returns out-of-fold probabilities plus one SHAP factor list per row.
    """
    features = [*numeric, *categorical]
    x = frame[features]
    y = frame[svc.TARGET_COLUMN]

    probabilities = np.zeros(len(frame), dtype=float)
    explanations: list[dict | None] = [None] * len(frame)

    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=svc.RANDOM_STATE)
    for fold, (train_index, test_index) in enumerate(splitter.split(x, y), start=1):
        print(f"  fold {fold}/{folds}: fitting on {len(train_index)} rows", flush=True)
        pipeline = svc.make_model(numeric, categorical)
        pipeline.fit(x.iloc[train_index], y.iloc[train_index])

        probabilities[test_index] = pipeline.predict_proba(x.iloc[test_index])[:, 1]
        fold_explanations = svc.explain_frame(
            pipeline, x.iloc[test_index], numeric, categorical, top_n=TOP_FACTORS
        )
        for position, row_index in enumerate(test_index):
            explanations[row_index] = fold_explanations[position]

    missing = [i for i, item in enumerate(explanations) if item is None]
    if missing:
        raise svc.PipelineError(f"{len(missing)} rows were never scored by a fold model")
    return probabilities, [item for item in explanations if item is not None]


def _chunks(rows: list, size: int = WRITE_CHUNK):
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def _execute_in_chunks(db, statement, rows: list) -> int:
    for chunk in _chunks(rows):
        db.execute(statement, chunk)
    return len(rows)


def purge_seeded(db) -> int:
    """Delete seeded leads and every prediction this pipeline did not produce.

    A prediction is treated as fabricated unless its stored explanation carries
    this model's SHAP marker, so no hand-written or randomly seeded score can
    survive an import. Predictions are removed first: leads.id is referenced.
    """
    # coalesce covers both a NULL column and a stored explanation with no
    # "method" key, which is exactly the shape the seeded rows had.
    fabricated = db.query(MLPrediction.id).filter(
        func.coalesce(MLPrediction.shap_explanation["method"].as_string(), "") != SHAP_METHOD
    )
    prediction_ids = [row[0] for row in fabricated.all()]
    for chunk in _chunks(prediction_ids):
        db.execute(delete(MLPrediction).where(MLPrediction.id.in_(chunk)))

    # Leads left with no prediction are the seeded stubs; a real lead always has one.
    orphaned = db.query(Lead.id).filter(
        Lead.student_id.like(f"{SEEDED_STUDENT_ID_PREFIX}%"),
        ~Lead.id.in_(db.query(MLPrediction.lead_id)),
    )
    lead_ids = [row[0] for row in orphaned.all()]
    for chunk in _chunks(lead_ids):
        db.execute(delete(Lead).where(Lead.id.in_(chunk)))
    return len(lead_ids)


def _prediction_row(lead_id: str, probability: float, explanation: dict,
                    cluster: int | None, name: str | None, prediction_id: str | None = None) -> dict:
    score = float(probability)
    row = {
        "lead_id": lead_id,
        "conversion_probability": score,
        # The admin report reads admission_probability; it is the same model
        # output, so it carries the real score rather than a stale random value.
        "admission_probability": score,
        "lead_score": svc.score_band(score),
        "segment_cluster": cluster,
        "segment_name": name,
        "shap_explanation": explanation,
    }
    if prediction_id is not None:
        row["id"] = prediction_id
    return row


def persist(
    db,
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    explanations: list[dict],
    segments: tuple[list[int], list[str]] | None = None,
) -> dict:
    """Upsert leads and their real predictions; keep unrelated rows."""
    removed = purge_seeded(db)

    records = frame.to_dict(orient="records")
    existing_leads = {lead.customer_id: lead for lead in db.query(Lead).all()}
    existing_predictions = {prediction.lead_id: prediction for prediction in db.query(MLPrediction).all()}

    clusters, names = segments if segments else ([None] * len(frame), [None] * len(frame))

    lead_inserts: list[dict] = []
    lead_updates: list[dict] = []
    prediction_inserts: list[dict] = []
    prediction_updates: list[dict] = []
    created = updated = 0

    for record, probability, explanation, cluster, name in zip(
        records, probabilities, explanations, clusters, names
    ):
        payload = build_lead_payload(record)
        lead = existing_leads.get(payload["customer_id"])
        if lead is None:
            # The key is generated up front so the prediction can reference it in
            # the same batch; the column default only runs once a row is sent.
            row = {"id": generate_uuid(), **payload}
            lead_inserts.append(row)
            lead_id = row["id"]
            created += 1
        else:
            lead_id = lead.id
            if any(getattr(lead, key) != value for key, value in payload.items()):
                lead_updates.append({"id": lead_id, **payload})
            updated += 1

        existing = existing_predictions.get(lead_id)
        if existing is None:
            prediction_inserts.append(
                {"id": generate_uuid(), **_prediction_row(lead_id, probability, explanation, cluster, name)}
            )
        elif _prediction_is_stale(existing, probability, explanation, cluster, name):
            prediction_updates.append(
                {"id": existing.id,
                 **_prediction_row(lead_id, probability, explanation, cluster, name, existing.id)}
            )

    _execute_in_chunks(db, Lead.__table__.insert(), lead_inserts)
    # ORM bulk update by primary key: the id key becomes the WHERE clause and is
    # never written back into the row.
    _execute_in_chunks(db, row_update(Lead), lead_updates)
    # Leads are written first so the prediction foreign keys resolve.
    _execute_in_chunks(db, MLPrediction.__table__.insert(), prediction_inserts)
    _execute_in_chunks(db, row_update(MLPrediction), prediction_updates)

    return {
        "leads_created": created,
        "leads_updated": updated,
        "leads_inserted": len(lead_inserts),
        "leads_written": len(lead_updates),
        "predictions_inserted": len(prediction_inserts),
        "predictions_updated": len(prediction_updates),
        "seeded_leads_removed": removed,
    }


def _prediction_is_stale(prediction, probability: float, explanation: dict,
                         cluster: int | None, name: str | None) -> bool:
    """Only rewrite a stored prediction when something the UI reads has changed."""
    score = float(probability)
    return (
        prediction.conversion_probability != score
        or prediction.admission_probability != score
        or prediction.lead_score != svc.score_band(score)
        or prediction.segment_cluster != cluster
        or prediction.segment_name != name
        or (prediction.shap_explanation or {}) != explanation
    )


def run(csv_path: Path = svc.DATASET_PATH, import_data: bool = True, folds: int = CV_FOLDS) -> dict:
    served_pipeline, _ = svc.load_pipeline()  # fail fast if training has not run

    frame = svc.read_dataset(csv_path)
    numeric, categorical, _ = svc.resolve_features(frame)
    features = [*numeric, *categorical]
    print(
        f"Loaded {len(frame)} leads; {len(numeric)} numeric and "
        f"{len(categorical)} categorical features",
        flush=True,
    )

    # Segmentation uses the served pipeline's imputer, so a lead's segment is
    # derived from exactly the values its prediction used. K-Means is
    # unsupervised, so fitting it on every row leaks no target information.
    print(f"Fitting the {svc.SEGMENT_COUNT}-segment lead segmentation...", flush=True)
    segment_artifact = svc.fit_segments(served_pipeline, frame[features])
    svc.save_segments(segment_artifact)
    clusters, names = svc.assign_segments(segment_artifact, served_pipeline, frame[features])

    print(f"Generating out-of-fold predictions and SHAP explanations...", flush=True)
    probabilities, explanations = out_of_fold_scores(frame, numeric, categorical, folds)

    summary = {
        "leads": int(len(frame)),
        "folds": folds,
        "mean_probability": round(float(probabilities.mean()), 4),
        "high_score_leads": int((probabilities >= svc.HIGH_SCORE_MIN).sum()),
        "actual_conversions": int(frame[svc.TARGET_COLUMN].sum()),
        "segments": {
            str(cluster): {
                "name": segment_artifact["names"][cluster],
                "leads": profile["leads"],
                "engagement_index": profile["engagement_index"],
                "mean_probability": profile["mean_probability"],
            }
            for cluster, profile in sorted(segment_artifact["profile"].items())
        },
    }

    if not import_data:
        print(json.dumps(summary, indent=2))
        return summary

    Base.metadata.create_all(bind=engine)
    with SessionLocal.begin() as db:
        summary.update(persist(db, frame, probabilities, explanations, (clusters, names)))
    summary["ml_predictions"] = int(len(frame))

    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=svc.DATASET_PATH)
    parser.add_argument("--folds", type=int, default=CV_FOLDS)
    parser.add_argument(
        "--no-import", action="store_true", help="Score the dataset without writing to the database"
    )
    args = parser.parse_args()
    run(args.csv, not args.no_import, args.folds)


if __name__ == "__main__":
    main()
