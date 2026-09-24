from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "Leads X Education.csv"
ML_ROOT = PROJECT_ROOT / "ml"
MODELS_DIR = ML_ROOT / "models"
REPORTS_DIR = ML_ROOT / "reports"

TARGET_COLUMN = "Converted"
RANDOM_STATE = 42

IDENTIFIER_COLUMNS = ["Prospect ID", "Lead Number"]
CONSTANT_COLUMNS = [
    "Magazine",
    "Receive More Updates About Our Courses",
    "Update me on Supply Chain Content",
    "Get updates on DM Content",
    "I agree to pay the amount through cheque",
]
LEAKAGE_COLUMNS = ["Tags", "Lead Quality", "Lead Profile"]
NEAR_CONSTANT_COLUMNS = [
    "Do Not Call",
    "Search",
    "Newspaper Article",
    "X Education Forums",
    "Newspaper",
    "Digital Advertisement",
    "Through Recommendations",
    "What matters most to you in choosing a course",
]

NUMERIC_COLUMNS = [
    "TotalVisits",
    "Total Time Spent on Website",
    "Page Views Per Visit",
    "Asymmetrique Activity Score",
    "Asymmetrique Profile Score",
]

# High / Medium / Low conversion-probability thresholds (match backend/train_model.py).
PRIORITY_THRESHOLDS = {"High": 0.70, "Medium": 0.40}
DECISION_THRESHOLD = 0.5

# Business purpose: education leads that are likely to convert. Positive class = Converted = 1.
SELECTION_METRIC = "f1"


def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset.")

    print("DATASET_INFO")
    print(f"path={DATA_PATH}")
    print(f"rows={len(df)}")
    print(f"columns={len(df.columns)}")
    print(f"target={TARGET_COLUMN}")
    print(f"target_distribution={df[TARGET_COLUMN].value_counts().to_dict()}")
    print(f"duplicate_rows={int(df.duplicated().sum())}")
    print(f"missing_values={int(df.isna().sum().sum())}")
    print()
    return df


def build_feature_lists(df: pd.DataFrame) -> dict:
    excluded = (
        IDENTIFIER_COLUMNS
        + CONSTANT_COLUMNS
        + LEAKAGE_COLUMNS
        + NEAR_CONSTANT_COLUMNS
        + [TARGET_COLUMN]
    )
    missing_expected = [col for col in excluded if col not in df.columns]
    if missing_expected:
        raise ValueError(f"Expected columns missing from dataset: {missing_expected}")

    remaining = [col for col in df.columns if col not in excluded]
    # Safely partition remaining columns into numeric vs categorical.
    used_numeric = [col for col in NUMERIC_COLUMNS if col in remaining]
    used_categorical = [col for col in remaining if col not in NUMERIC_COLUMNS]

    print("FEATURE_LISTS")
    print(f"excluded_count={len(excluded) - 1}")
    print(f"numeric_features={used_numeric}")
    print(f"categorical_features={used_categorical}")
    print()
    return {
        "excluded": excluded,
        "numeric": used_numeric,
        "categorical": used_categorical,
        "features": remaining,
    }


def clean_features(df: pd.DataFrame, feature_lists: dict) -> pd.DataFrame:
    """Normalise placeholder / missing categorical values before the transformer.

    'Select' means the prospect did not choose an option while filling the form
    (see the data dictionary), so it is kept as an explicit 'Not Selected'
    category rather than being imputed with a wrong meaningful value.
    """
    cleaned = df.copy()
    for col in feature_lists["categorical"]:
        cleaned[col] = cleaned[col].astype("object")
        cleaned[col] = (
            cleaned[col]
            .str.strip()
            .replace({"Select": "Not Selected"})
            .fillna("Missing")
        )
    return cleaned


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor


def balanced_sample_weights(y: pd.Series) -> np.ndarray:
    classes, counts = np.unique(y.to_numpy(), return_counts=True)
    weight = counts.sum() / (len(classes) * counts)
    return np.array([weight[int(value)] for value in y.to_numpy()])


def evaluate_model(
    name: str,
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    majority_baseline = float(y_test.value_counts(normalize=True).max())

    metrics = {
        "model": name,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "majority_baseline_accuracy": majority_baseline,
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["Not Converted", "Converted"],
            zero_division=0,
        ),
    }
    return metrics


def save_confusion_matrix(model_name: str, cm: np.ndarray) -> None:
    labels = ["Not Converted", "Converted"]
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.title(f"{model_name} Confusion Matrix")
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, labels, rotation=45)
    plt.yticks(tick_marks, labels)
    thresh = cm.max() / 2.0
    for i in range(2):
        for j in range(2):
            plt.text(
                j,
                i,
                format(cm[i, j], "d"),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )
    plt.tight_layout()
    output_path = REPORTS_DIR / f"lead_conversion_{model_name.lower().replace(' ', '_')}_confusion_matrix.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_confusion_matrix={output_path.name}")


def save_metric_comparison(results: list[dict]) -> None:
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    labels = [item["model"] for item in results]
    values = {metric: [item[metric] for item in results] for metric in metrics}

    x = np.arange(len(labels))
    width = 0.15
    fig, ax = plt.subplots(figsize=(10, 6))
    for idx, metric in enumerate(metrics):
        ax.bar(x + (idx - 2) * width, values[metric], width=width, label=metric)
    ax.axhline(y=results[0]["majority_baseline_accuracy"], color="red", linestyle="--", label="Majority baseline")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Score")
    ax.set_title("Lead Conversion Model Metric Comparison")
    ax.legend()
    ax.set_ylim(0, 1.1)
    plt.tight_layout()
    output_path = REPORTS_DIR / "lead_conversion_model_metric_comparison.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_metric_chart={output_path.name}")


def save_target_distribution(df: pd.DataFrame) -> None:
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    plt.figure(figsize=(6, 5))
    counts.plot(kind="bar", color=["#C44E52", "#55A868"])
    plt.title("Converted Class Distribution")
    plt.xticks(ticks=range(2), labels=["Not Converted", "Converted"], rotation=0)
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.tight_layout()
    output_path = REPORTS_DIR / "lead_conversion_target_distribution.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_target_distribution={output_path.name}")


def build_models(scale_pos_weight: float) -> dict:
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=5000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
    }
    try:
        from xgboost import XGBClassifier

        models["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            verbosity=0,
        )
    except ImportError:
        print("XGBoost not available; skipping XGBoost evaluation.")
    return models


def priority_for(probability: float) -> str:
    if probability >= PRIORITY_THRESHOLDS["High"]:
        return "High"
    if probability >= PRIORITY_THRESHOLDS["Medium"]:
        return "Medium"
    return "Low"


def save_report(
    results: list[dict],
    selected_model_name: str,
    feature_lists: dict,
    df: pd.DataFrame,
) -> None:
    report_path = REPORTS_DIR / "lead_conversion_evaluation.txt"
    lines: list[str] = []
    add = lines.append
    add("Decision-Intel Lead Conversion Prediction Experiment")
    add("=" * 55)
    add("Project: Education Lead Conversion (X Education leads dataset)")
    add("Objective: Predict the probability that an education lead converts, then")
    add("rank leads as High / Medium / Low priority for follow-up.")
    add("")
    add("Dataset")
    add("-------")
    add(f"- Path: data/Leads X Education.csv")
    add(f"- Rows: {len(df)}")
    add(f"- Columns: {len(df.columns)}")
    add(f"- Target: Converted (0 = not converted, 1 = converted)")
    add(f"- Class distribution: {df[TARGET_COLUMN].value_counts().to_dict()}")
    add(f"- Duplicate rows: {int(df.duplicated().sum())}")
    add(f"- Missing values: {int(df.isna().sum().sum())}")
    add("")
    add(f"Features used ({len(feature_lists['features'])})")
    add("-" * 30)
    add(f"Numeric ({len(feature_lists['numeric'])}): {', '.join(feature_lists['numeric'])}")
    add(f"Categorical ({len(feature_lists['categorical'])}): {', '.join(feature_lists['categorical'])}")
    add("")
    add("Features excluded and why")
    add("-" * 26)
    add(f"- Identifiers ({len(IDENTIFIER_COLUMNS)}): {', '.join(IDENTIFIER_COLUMNS)}")
    add(f"- Constant columns ({len(CONSTANT_COLUMNS)}): {', '.join(CONSTANT_COLUMNS)}")
    add(f"- Post-hoc leakage labels ({len(LEAKAGE_COLUMNS)}): {', '.join(LEAKAGE_COLUMNS)} (assigned after contact; leak outcome)")
    add(f"- Near-constant columns ({len(NEAR_CONSTANT_COLUMNS)}): {', '.join(NEAR_CONSTANT_COLUMNS)} (minority < 0.2%; no signal)")
    add("")
    add("Preprocessing")
    add("-------------")
    add("- 'Select' placeholder mapped to 'Not Selected'; missing categoricals -> 'Missing'")
    add("- Numeric: median imputation + StandardScaler")
    add("- Categorical: constant imputation + OneHotEncoder(handle_unknown='ignore')")
    add("- Train/test split before fitting any transformation (no data leakage)")
    add(f"- Split: 80/20 stratified, random_state={RANDOM_STATE}")
    add("- Class imbalance (38.5% converted) handled with balanced class weights")
    add("")
    add("Model results (held-out test set)")
    add("---------------------------------")
    add("Model | Accuracy | Precision | Recall | F1 | ROC-AUC")
    for item in results:
        add(
            f"{item['model']} | {item['accuracy']:.4f} | {item['precision']:.4f} | "
            f"{item['recall']:.4f} | {item['f1']:.4f} | {item['roc_auc']:.4f}"
        )
    add("")
    add(f"Selected model: {selected_model_name}")
    add("Selection basis: highest F1 for the positive (converted) class, the business")
    add("metric used to find leads worth following up, with ROC-AUC as tie-breaker.")
    add("")
    add("Saved artifacts")
    add("---------------")
    add(f"- Preprocessor: {MODELS_DIR / 'lead_preprocessor.pkl'}")
    add(f"- Model: {MODELS_DIR / 'lead_conversion_model.pkl'}")
    add(f"- Metadata: {MODELS_DIR / 'lead_conversion_metadata.json'}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved_report={report_path}")


def save_artifacts(
    selected_model_name: str,
    selected_model,
    preprocessor: ColumnTransformer,
    selected_metrics: dict,
    feature_lists: dict,
) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    pre_path = MODELS_DIR / "lead_preprocessor.pkl"
    model_path = MODELS_DIR / "lead_conversion_model.pkl"
    joblib.dump(preprocessor, pre_path)
    joblib.dump(selected_model, model_path)
    print(f"saved_preprocessor={pre_path}")
    print(f"saved_model={model_path}")

    metadata = {
        "project": "Decision-Intel Lead Conversion",
        "target_column": TARGET_COLUMN,
        "positive_class": 1,
        "selected_model": selected_model_name,
        "random_state": RANDOM_STATE,
        "features": {
            "numeric": feature_lists["numeric"],
            "categorical": feature_lists["categorical"],
        },
        "excluded_features": {
            "identifiers": IDENTIFIER_COLUMNS,
            "constant": CONSTANT_COLUMNS,
            "leakage": LEAKAGE_COLUMNS,
            "near_constant": NEAR_CONSTANT_COLUMNS,
        },
        "placeholder_values": {"Select": "Not Selected", "(missing)": "Missing"},
        "thresholds": {
            "decision": DECISION_THRESHOLD,
            "priority_high": PRIORITY_THRESHOLDS["High"],
            "priority_medium": PRIORITY_THRESHOLDS["Medium"],
        },
        "metrics": {
            k: selected_metrics[k]
            for k in ("accuracy", "precision", "recall", "f1", "roc_auc")
        },
    }

    meta_path = MODELS_DIR / "lead_conversion_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved_metadata={meta_path}")


def main() -> None:
    ML_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    feature_lists = build_feature_lists(df)
    cleaned = clean_features(df, feature_lists)

    X = cleaned[feature_lists["features"]]
    y = cleaned[TARGET_COLUMN].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    preprocessor = build_preprocessor(feature_lists["numeric"], feature_lists["categorical"])
    preprocessor.fit(X_train)
    X_train_t = preprocessor.transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    class_counts = y_train.value_counts()
    scale_pos_weight = class_counts[0] / class_counts[1]

    models = build_models(float(scale_pos_weight))
    results: list[dict] = []
    trained_models: dict[str, object] = {}

    for model_name, model in models.items():
        if model_name == "Gradient Boosting":
            model.fit(X_train_t, y_train, sample_weight=balanced_sample_weights(y_train))
        else:
            model.fit(X_train_t, y_train)
        trained_models[model_name] = model

        metrics = evaluate_model(model_name, model, X_test_t, y_test)
        results.append(metrics)
        save_confusion_matrix(model_name, np.array(metrics["confusion_matrix"]))

    save_metric_comparison(results)
    save_target_distribution(df)

    selected = max(
        results,
        key=lambda item: (item[SELECTION_METRIC], item["roc_auc"], item["accuracy"]),
    )
    selected_model_name = selected["model"]
    selected_model = trained_models[selected_model_name]

    save_artifacts(
        selected_model_name,
        selected_model,
        preprocessor,
        selected,
        feature_lists,
    )
    save_report(results, selected_model_name, feature_lists, df)

    probability = selected_model.predict_proba(X_test_t)[:, 1]
    priority = priority_for(probability[0])

    print("\nRESULT_TABLE")
    print("Model | Accuracy | Precision | Recall | F1 | ROC-AUC")
    for item in results:
        print(
            f"{item['model']} | {item['accuracy']:.4f} | {item['precision']:.4f} | {item['recall']:.4f} | {item['f1']:.4f} | {item['roc_auc']:.4f}"
        )
    print(f"SELECTED_MODEL={selected_model_name}")
    print(f"SELECTED_MODEL_F1={selected['f1']:.4f}")
    print(f"SELECTED_MODEL_ROC_AUC={selected['roc_auc']:.4f}")
    print(
        f"SAMPLE_PREDICTION={{'conversion_probability': {probability[0]:.4f}, 'prediction': {int(probability[0] >= DECISION_THRESHOLD)}, 'lead_priority': '{priority}'}}"
    )


if __name__ == "__main__":
    main()