"""Train the validated XGBoost lead-conversion model on Leads X Education.csv.

    python ml/scripts/train_lead_conversion_xgboost.py

Feature definitions, preprocessing and scoring live in backend/ml_service.py so
the saved artifact and the serving layer can never disagree.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import ml_service as svc  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
import xgboost  # noqa: E402
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split  # noqa: E402

REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"
TEST_SIZE = 0.2


def baselines(numeric: list[str], categorical: list[str]) -> dict:
    """Reference models, to confirm XGBoost is the right choice for this data."""
    return {
        "Logistic Regression": LogisticRegression(max_iter=5000, random_state=svc.RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, random_state=svc.RANDOM_STATE, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=svc.RANDOM_STATE),
    }


def evaluate(name: str, pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    probability = pipeline.predict_proba(x_test)[:, 1]
    predicted = (probability >= 0.5).astype(int)
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_test, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predicted)),
        "precision": float(precision_score(y_test, predicted, zero_division=0)),
        "recall": float(recall_score(y_test, predicted, zero_division=0)),
        "f1": float(f1_score(y_test, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=[0, 1]).tolist(),
    }


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    svc.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    frame = svc.read_dataset()
    numeric, categorical, constant = svc.resolve_features(frame)
    features = [*numeric, *categorical]

    print(f"rows={len(frame)} features={len(features)} "
          f"(numeric={len(numeric)} categorical={len(categorical)})")
    print(f"dropped_constant_columns={constant}")
    print(f"conversion_rate={frame[svc.TARGET_COLUMN].mean():.4f}")

    x = frame[features]
    y = frame[svc.TARGET_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, stratify=y, random_state=svc.RANDOM_STATE
    )

    results: list[dict] = []
    xgboost_pipeline = svc.make_model(numeric, categorical)
    print(f"\nFitting XGBoost on {len(x_train)} rows...", flush=True)
    xgboost_pipeline.fit(x_train, y_train)
    results.append(evaluate("XGBoost", xgboost_pipeline, x_test, y_test))

    for name, estimator in baselines(numeric, categorical).items():
        print(f"Fitting {name}...", flush=True)
        pipeline = svc.Pipeline(
            steps=[
                ("preprocess", svc.build_preprocessor(numeric, categorical)),
                ("classifier", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        results.append(evaluate(name, pipeline, x_test, y_test))

    print("\nRESULT_TABLE")
    print("Model | Accuracy | Balanced | Precision | Recall | F1 | ROC-AUC")
    for row in results:
        print(
            f"{row['model']} | {row['accuracy']:.4f} | {row['balanced_accuracy']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['roc_auc']:.4f}"
        )

    selected = next(row for row in results if row["model"] == "XGBoost")

    # Refit on every row for future inference; the metrics above stay held-out.
    final_pipeline = svc.make_model(numeric, categorical)
    print("\nRefitting XGBoost on all rows for serving...", flush=True)
    final_pipeline.fit(x, y)

    joblib_dump(final_pipeline)

    metadata = {
        "model": "lead_conversion_xgboost",
        "estimator": "xgboost.XGBClassifier",
        "dataset": svc.DATASET_PATH.name,
        "dataset_sha256": svc.dataset_fingerprint(),
        "target_column": svc.TARGET_COLUMN,
        "key_column": svc.KEY_COLUMN,
        "identifier_columns": svc.IDENTIFIER_COLUMNS,
        "excluded_constant_columns": constant,
        "numeric_features": numeric,
        "categorical_features": categorical,
        "approved_features": features,
        "score_bands": {
            "high_min": svc.HIGH_SCORE_MIN,
            "medium_min": svc.MEDIUM_SCORE_MIN,
        },
        "random_state": svc.RANDOM_STATE,
        "train_test_split": {"test_size": TEST_SIZE, "stratified": True},
        "rows": int(len(frame)),
        "positive_rate": float(y.mean()),
        "majority_baseline_accuracy": float(y_test.value_counts(normalize=True).max()),
        "held_out_metrics": selected,
        "model_comparison": results,
        "environment": {
            "python": platform.python_version(),
            "xgboost": xgboost.__version__,
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
        },
        "notes": [
            "Metrics come from a stratified held-out split; the served artifact is refit on all rows.",
            "Batch scores written to ml_predictions must come from out-of-fold models, not this refit.",
            "SHAP values explain model output, not causal effect.",
        ],
    }
    svc.METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved_metadata={svc.METADATA_PATH}")

    write_report(metadata, results)
    print(f"\nSELECTED_MODEL=XGBoost")
    print(f"ROC_AUC={selected['roc_auc']:.4f} F1={selected['f1']:.4f}")


def joblib_dump(pipeline) -> None:
    import joblib

    joblib.dump(pipeline, svc.MODEL_PATH)
    print(f"saved_model={svc.MODEL_PATH}")


def write_report(metadata: dict, results: list[dict]) -> None:
    lines = [
        "# Decision-Intel Lead Conversion Model",
        "",
        f"Dataset: `{metadata['dataset']}` ({metadata['rows']} rows, "
        f"positive rate {metadata['positive_rate']:.4f})",
        f"Target: `{metadata['target_column']}`",
        f"Estimator: `{metadata['estimator']}`",
        "",
        "## Held-out performance (stratified 20% test split)",
        "",
        "Model | Accuracy | Balanced | Precision | Recall | F1 | ROC-AUC",
        "--- | --- | --- | --- | --- | --- | ---",
    ]
    for row in results:
        lines.append(
            f"{row['model']} | {row['accuracy']:.4f} | {row['balanced_accuracy']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['roc_auc']:.4f}"
        )
    lines += [
        "",
        f"Majority-class baseline accuracy: {metadata['majority_baseline_accuracy']:.4f}",
        "",
        f"## Confusion matrix ({metadata['held_out_metrics']['model']})",
        "",
        "```",
        str(metadata["held_out_metrics"]["confusion_matrix"]),
        "```",
        "",
        "## Features",
        "",
        f"Numeric ({len(metadata['numeric_features'])}): "
        + ", ".join(f"`{c}`" for c in metadata["numeric_features"]),
        "",
        f"Categorical ({len(metadata['categorical_features'])}): "
        + ", ".join(f"`{c}`" for c in metadata["categorical_features"]),
        "",
        "Excluded identifiers: "
        + ", ".join(f"`{c}`" for c in metadata["identifier_columns"]),
        "",
        "Excluded constant columns: "
        + (", ".join(f"`{c}`" for c in metadata["excluded_constant_columns"]) or "none"),
        "",
        "## Environment",
        "",
        f"- Python {metadata['environment']['python']}",
        f"- xgboost {metadata['environment']['xgboost']}",
        f"- scikit-learn {metadata['environment']['sklearn']}",
        f"- pandas {metadata['environment']['pandas']}",
    ]
    path = REPORTS_DIR / "lead_conversion_model_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved_report={path}")


if __name__ == "__main__":
    main()
