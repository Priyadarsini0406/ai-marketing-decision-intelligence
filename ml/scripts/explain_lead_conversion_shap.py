"""SHAP explainability for the saved lead-conversion model.

Run after training:
    python ml/scripts/explain_lead_conversion_shap.py

Generates global feature importance, individual explanations for representative
leads, and ml/reports/lead_conversion_shap_explainability.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"
MODELS_DIR = ML_ROOT / "models"
REPORTS_DIR = ML_ROOT / "reports"
DATA_PATH = PROJECT_ROOT / "data" / "Leads X Education.csv"

PREPROCESSOR_PATH = MODELS_DIR / "lead_preprocessor.pkl"
MODEL_PATH = MODELS_DIR / "lead_conversion_model.pkl"
META_PATH = MODELS_DIR / "lead_conversion_metadata.json"
RANDOM_STATE = 42


def load_artifacts():
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(MODEL_PATH)
    metadata = json_load(META_PATH)
    return preprocessor, model, metadata


def json_load(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def clean_features(df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    cleaned = df.copy()
    for col in metadata["features"]["categorical"]:
        cleaned[col] = cleaned[col].astype("object")
        cleaned[col] = (
            cleaned[col]
            .str.strip()
            .replace({"Select": "Not Selected"})
            .fillna("Missing")
        )
    return cleaned


def build_explainer(model):
    import shap

    model_type = type(model).__name__
    try:
        if "XGBClassifier" in model_type or hasattr(model, "get_booster"):
            return shap.TreeExplainer(model)
        if model_type in ("RandomForestClassifier", "GradientBoostingClassifier"):
            return shap.TreeExplainer(model)
    except Exception:
        pass
    return shap.Explainer(model)


def explain_sample(explainer, model, row_array: np.ndarray, feature_names: list[str]):
    values = np.asarray(explainer.shap_values(row_array, check_additivity=False), dtype=float)
    if values.ndim == 3:
        values = values.squeeze(axis=0)
    if values.ndim == 2 and values.shape[0] == 1:
        values = values[0]
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]

    prob = float(model.predict_proba(row_array)[0, 1])
    expected = explainer.expected_value
    if isinstance(expected, (list, np.ndarray)):
        expected = float(np.asarray(expected).ravel()[-1])
    else:
        expected = float(expected)

    contribs = list(zip(feature_names, [float(v) for v in values]))
    contribs.sort(key=lambda c: abs(c[1]), reverse=True)
    positive = [(c[0], c[1]) for c in contribs if c[1] > 0][:5]
    negative = [(c[0], c[1]) for c in contribs if c[1] < 0][:5]
    return prob, expected, positive, negative, contribs[:10]


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        sys.exit("Model not found. Run ml/scripts/train_lead_conversion_model.py first.")

    preprocessor, model, metadata = load_artifacts()

    df = pd.read_csv(DATA_PATH)
    cleaned = clean_features(df, metadata)
    feature_columns = metadata["features"]["numeric"] + metadata["features"]["categorical"]
    X = cleaned[feature_columns]
    y = cleaned[metadata["target_column"]].astype(int)

    X_train, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    feature_names = list(preprocessor.get_feature_names_out())
    X_train_t = np.asarray(preprocessor.transform(X_train), dtype=float)
    X_test_t = np.asarray(preprocessor.transform(X_test), dtype=float)

    import shap

    explainer = build_explainer(model)

    sample_rows = min(200, len(X_test_t))
    rng = np.random.RandomState(RANDOM_STATE)
    idx_sample = rng.choice(len(X_test_t), size=sample_rows, replace=False)
    global_values = np.asarray(
        explainer.shap_values(X_test_t[idx_sample], check_additivity=False), dtype=float
    )
    if global_values.ndim == 3:
        global_values = global_values.squeeze(axis=0)

    importance = np.abs(global_values).mean(axis=0)
    top_idx = np.argsort(importance)[::-1][:10]
    top_features = [(feature_names[i], float(importance[i])) for i in top_idx]

    # Bar plot of global importance.
    fig, ax = plt.subplots(figsize=(9, 7))
    ordered = sorted(top_features, key=lambda x: x[1])
    ax.barh([name for name, _ in ordered], [val for _, val in ordered], color="#4C72B0")
    ax.set_title("Lead Conversion SHAP Feature Importance (Top 10)")
    ax.set_xlabel("Mean |SHAP value|")
    plt.tight_layout()
    global_plot = REPORTS_DIR / "lead_conversion_shap_global_importance.png"
    fig.savefig(global_plot, dpi=200)
    plt.close(fig)
    print(f"saved_global_importance={global_plot.name}")

    # Individual explanations for representative probability bins.
    probs = model.predict_proba(X_test_t)[:, 1]
    bins = {"High": probs >= 0.7, "Medium": (probs >= 0.4) & (probs < 0.7), "Low": probs < 0.4}
    explanations = []
    for label, mask in bins.items():
        if not mask.any():
            continue
        pos_idx = int(np.where(mask)[0][0])
        row = X_test_t[[pos_idx]]
        prob, expected, positive, negative, contribs = explain_sample(
            explainer, model, row, feature_names
        )
        explanations.append(
            {
                "priority_tier": label,
                "dataset_row": int(pos_idx),
                "conversion_probability": round(prob, 4),
                "base_value": round(expected, 4),
                "positive_factors": [{"feature": f, "shap_value": round(v, 4)} for f, v in positive],
                "negative_factors": [{"feature": f, "shap_value": round(v, 4)} for f, v in negative],
                "feature_contribution": [{"feature": f, "shap_value": round(v, 4)} for f, v in contribs],
            }
        )

    lines = []
    add = lines.append
    add("# Explainable Lead Conversion Prediction (Decision-Intel)")
    add("")
    add("## Model used")
    add(f"- Model type: {type(model).__name__}")
    add(f"- Selected model during training: {metadata['selected_model']}")
    add(f"- Saved artifacts: `{MODEL_PATH.name}`, `{PREPROCESSOR_PATH.name}`")
    add("")
    add("## Preprocessing pipeline")
    add("- Numeric: median imputation + StandardScaler")
    add("- Categorical: 'Select' -> 'Not Selected', missing -> 'Missing', OneHotEncoder(handle_unknown='ignore')")
    add(f"- Input features: {len(metadata['features']['numeric'] + metadata['features']['categorical'])}")
    add(f"- Transformed features: {len(feature_names)}")
    add("- Train/test split (80/20 stratified, random_state=42) done before transformations; no leakage")
    add("")
    add("## SHAP method")
    add("- Explainer: SHAP TreeExplainer on the trained model over the preprocessed feature space")
    add("- Values are for the positive (converted) class.")
    add("")
    add("## Global feature importance (top 10)")
    for feature, value in top_features:
        add(f"- {feature}: {value:.6f}")
    add("")
    add("## Individual explanations")
    for item in explanations:
        add(f"### Representative lead - {item['priority_tier']} tier (dataset row {item['dataset_row']})")
        add(f"- Conversion probability: {item['conversion_probability']}")
        add(f"- Base value: {item['base_value']}")
        if item["positive_factors"]:
            add("- Important positive factors:")
            for entry in item["positive_factors"]:
                add(f"  - {entry['feature']}: {entry['shap_value']:.4f}")
        if item["negative_factors"]:
            add("- Important negative factors:")
            for entry in item["negative_factors"]:
                add(f"  - {entry['feature']}: {entry['shap_value']:.4f}")
        add("- Feature contributions:")
        for entry in item["feature_contribution"]:
            add(f"  - {entry['feature']}: {entry['shap_value']:.4f}")
        add("")
    add("## Limitations")
    add("- SHAP values explain model predictions, not causal effects.")
    add("- Excluded features (identifiers, constants, and post-hoc labels like Tags /")
    add("  Lead Quality / Lead Profile) would leak the outcome and are not modeled.")

    report_path = REPORTS_DIR / "lead_conversion_shap_explainability.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved_report={report_path.name}")
    print(f"GLOBAL_PLOT={global_plot.relative_to(PROJECT_ROOT)}")
    for item in explanations:
        print(f"REPRESENTATIVE {item['priority_tier']}: prob={item['conversion_probability']}")


if __name__ == "__main__":
    main()