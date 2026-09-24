"""Decision-Intel Lead Conversion prediction layer.

Reusable prediction function/API for the saved lead-conversion model:

    python ml/predict_lead.py --sample 5        # predict the 6th row of the dataset
    python ml/predict_lead.py --json "{...}"     # predict from an inline lead dict

The output is a JSON object with the conversion probability, the binary
prediction, the High/Medium/Low priority (using the thresholds stored in the
model metadata), SHAP-based positive/negative factors, and a recommendation
generated from the actual prediction and feature contributions.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ML_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ML_ROOT.parent
MODELS_DIR = ML_ROOT / "models"

PREPROCESSOR_PATH = MODELS_DIR / "lead_preprocessor.pkl"
MODEL_PATH = MODELS_DIR / "lead_conversion_model.pkl"
META_PATH = MODELS_DIR / "lead_conversion_metadata.json"
DATASET_PATH = PROJECT_ROOT / "data" / "Leads X Education.csv"


@lru_cache(maxsize=1)
def load_artifacts() -> tuple:
    if not (PREPROCESSOR_PATH.exists() and MODEL_PATH.exists() and META_PATH.exists()):
        raise FileNotFoundError(
            "Saved model artifacts not found. Train first with "
            "python ml/scripts/train_lead_conversion_model.py"
        )
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(MODEL_PATH)
    metadata = json.loads(META_PATH.read_text(encoding="utf-8"))
    return preprocessor, model, metadata


def strip_feature_name(name: str) -> str:
    return name.split("_")[0] if "_" in name else name


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the same placeholder / missing normalisation used during training."""
    _, _, metadata = load_artifacts()
    cleaned = df.copy()
    for col in metadata["features"]["categorical"]:
        if col not in cleaned.columns:
            continue
        cleaned[col] = cleaned[col].astype("object")
        cleaned[col] = (
            cleaned[col]
            .str.strip()
            .replace({"Select": "Not Selected"})
            .fillna("Missing")
        )
    return cleaned


def build_input_frame(lead: dict) -> pd.DataFrame:
    _, _, metadata = load_artifacts()
    feature_columns = metadata["features"]["numeric"] + metadata["features"]["categorical"]
    row = {}
    for col in feature_columns:
        value = lead.get(col)
        if value is None:
            value = np.nan
        row[col] = value
    return pd.DataFrame([row])[feature_columns]


def classify_priority(probability: float, metadata: dict) -> str:
    thresholds = metadata["thresholds"]
    if probability >= thresholds["priority_high"]:
        return "High"
    if probability >= thresholds["priority_medium"]:
        return "Medium"
    return "Low"


@lru_cache(maxsize=1)
def _explainer_for(model):
    import shap

    model_type = type(model).__name__
    try:
        if "XGBClassifier" in model_type or hasattr(model, "get_booster"):
            return shap.TreeExplainer(model)
        if model_type in ("RandomForestClassifier", "GradientBoostingClassifier",
                          "ExtraTreesClassifier", "HistGradientBoostingClassifier"):
            return shap.TreeExplainer(model)
    except Exception:
        pass
    return shap.Explainer(model)


def shap_factors(model, row_array: np.ndarray, feature_names: list[str], probability: float) -> dict:
    """SHAP contributions for the converted (class 1) outcome of one lead."""
    explainer = _explainer_for(model)
    values = np.asarray(explainer.shap_values(row_array, check_additivity=False), dtype=float)

    if values.ndim == 3:
        values = values.squeeze(axis=0)
    if values.ndim == 2 and values.shape[0] == 1:
        values = values[0]
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]

    expected = values.shape[0] if values.ndim == 1 else values.shape[1]
    if len(feature_names) != expected:
        feature_names = [f"feature_{i}" for i in range(expected)]

    base = float(explainer.expected_value)
    if isinstance(base, (list, np.ndarray)):
        base = float(np.asarray(base).ravel()[-1])

    contribs = list(zip(feature_names, [float(v) for v in (values if values.ndim == 1 else values[0])]))
    positive = sorted([c for c in contribs if c[1] > 0], key=lambda c: c[1], reverse=True)
    negative = sorted([c for c in contribs if c[1] < 0], key=lambda c: c[1])

    return {
        "probability": round(probability, 4),
        "base_value": round(base, 4),
        "positive_factors": [
            {"feature": name, "shap_value": round(value, 4)} for name, value in positive[:5]
        ],
        "negative_factors": [
            {"feature": name, "shap_value": round(value, 4)} for name, value in negative[:5]
        ],
        "feature_contribution": [
            {"feature": name, "shap_value": round(value, 4)}
            for name, value in sorted(contribs, key=lambda c: abs(c[1]), reverse=True)[:10]
        ],
    }


def build_recommendation(probability: float, priority: str, factors: dict) -> str:
    positives = ", ".join(f["feature"] for f in factors.get("positive_factors", [])) or "none dominant"
    negatives = ", ".join(f["feature"] for f in factors.get("negative_factors", [])) or "none dominant"

    if priority == "High":
        action = (
            "Prioritize this lead for immediate follow-up (call/email within 24 hours). "
            "It has a strong predicted chance of conversion."
        )
        closing = f"Reinforce {positives}. Actively address any friction indicated by {negatives}."
    elif priority == "Medium":
        action = (
            "Follow up with this lead and invest in additional engagement "
            "(personalized content, second touch)."
        )
        closing = f"Leverage {positives} and work to improve {negatives} to increase conversion likelihood."
    else:
        action = (
            "Treat as a low-priority, nurture lead. Maintain light-touch engagement "
            "and revisit periodically."
        )
        closing = f"Watch for positive movement in {positives}; track {negatives} as warning signs."

    return (
        f"[{priority} priority] {action} Predicted conversion probability "
        f"is {probability * 100:.1f}%. {closing} Recommendation generated from the "
        f"actual model probability and SHAP feature contributions."
    )


def predict_lead(lead: dict) -> dict:
    """Predict conversion for one lead and return probability, class, priority,
    SHAP factors, and a dynamic recommendation."""
    preprocessor, model, metadata = load_artifacts()
    frame = build_input_frame(lead)
    frame = clean_features(frame)

    feature_columns = metadata["features"]["numeric"] + metadata["features"]["categorical"]
    feature_names = list(preprocessor.get_feature_names_out())
    transformed = preprocessor.transform(frame[feature_columns])
    transformed_arr = np.asarray(transformed, dtype=float)

    probability = float(model.predict_proba(transformed_arr.reshape(1, -1))[0, 1])
    prediction = int(probability >= metadata["thresholds"]["decision"])
    priority = classify_priority(probability, metadata)

    try:
        factors = shap_factors(model, transformed_arr.reshape(1, -1), feature_names, probability)
    except Exception as exc:  # keep prediction usable even if SHAP fails
        factors = {"probability": round(probability, 4), "explanation_error": str(exc)}

    return {
        "conversion_probability": round(probability, 4),
        "prediction": prediction,
        "lead_priority": priority,
        "explanation": factors,
        "recommendation": build_recommendation(probability, priority, factors),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=0, help="Dataset row index to use as the lead (0-based).")
    parser.add_argument("--json", type=str, default=None, help="Inline JSON lead dict.")
    args = parser.parse_args(argv)

    if args.json:
        lead = json.loads(args.json)
        if not isinstance(lead, dict):
            raise SystemExit("--json must be a JSON object.")
        result = predict_lead(lead)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found for --sample: {DATASET_PATH}")
    frame = pd.read_csv(DATASET_PATH)
    if args.sample < 0 or args.sample >= len(frame):
        raise SystemExit(f"--sample must be between 0 and {len(frame) - 1}.")
    lead = frame.iloc[[args.sample]].to_dict(orient="records")[0]
    result = predict_lead(lead)
    print(f"Input lead (row {args.sample}):")
    for key in ("Lead Origin", "Lead Source", "Last Activity", "Total Time Spent on Website"):
        print(f"  {key}: {lead.get(key)}")
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())