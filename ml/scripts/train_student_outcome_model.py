from __future__ import annotations

import json
import pickle
from pathlib import Path

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
DATA_PATH = PROJECT_ROOT / "data.csv"
ML_ROOT = PROJECT_ROOT / "ml"
MODELS_DIR = ML_ROOT / "models"
REPORTS_DIR = ML_ROOT / "reports"

TARGET_COLUMN = "Target"
RANDOM_STATE = 42


def build_feature_lists(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    approved_features = [col for col in df.columns if col != TARGET_COLUMN]
    excluded_features = [TARGET_COLUMN]
    numeric_cols = [
        "Previous qualification (grade)",
        "Admission grade",
        "Curricular units 1st sem (credited)",
        "Curricular units 1st sem (enrolled)",
        "Curricular units 1st sem (evaluations)",
        "Curricular units 1st sem (approved)",
        "Curricular units 1st sem (grade)",
        "Curricular units 1st sem (without evaluations)",
        "Curricular units 2nd sem (credited)",
        "Curricular units 2nd sem (enrolled)",
        "Curricular units 2nd sem (evaluations)",
        "Curricular units 2nd sem (approved)",
        "Curricular units 2nd sem (grade)",
        "Curricular units 2nd sem (without evaluations)",
        "Age at enrollment",
        "Unemployment rate",
        "Inflation rate",
        "GDP",
    ]
    categorical_cols = [col for col in approved_features if col not in numeric_cols]
    return approved_features, excluded_features, numeric_cols, categorical_cols


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, sep=";")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset.")

    print("DATASET_INFO")
    print(f"rows={len(df)}")
    print(f"features={len(df.columns)}")
    print(f"target={TARGET_COLUMN}")
    print(f"target_classes={sorted(df[TARGET_COLUMN].unique().tolist())}")
    print(f"missing_values={int(df.isna().sum().sum())}")
    print()

    return df


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )
    return preprocessor


def evaluate_model(name: str, pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, class_labels: list[str]) -> dict:
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    recall_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    precision_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    roc_auc = roc_auc_score(
        pd.get_dummies(y_test, drop_first=False),
        y_proba,
        multi_class="ovr",
        average="macro",
    )

    cm = confusion_matrix(y_test, y_pred, labels=class_labels)

    metrics = {
        "model": name,
        "accuracy": float(accuracy),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "precision_weighted": float(precision_weighted),
        "recall_weighted": float(recall_weighted),
        "f1_weighted": float(f1_weighted),
        "roc_auc_macro": float(roc_auc),
        "confusion_matrix": cm,
        "classification_report": classification_report(
            y_test,
            y_pred,
            labels=class_labels,
            zero_division=0,
        ),
    }

    return metrics


def save_confusion_matrix(model_name: str, cm: np.ndarray, labels: list[str]) -> None:
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.title(f"{model_name} Confusion Matrix")
    plt.colorbar()
    tick_marks = np.arange(len(labels))
    plt.xticks(tick_marks, labels, rotation=45)
    plt.yticks(tick_marks, labels)
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], "d"), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    output_path = REPORTS_DIR / f"{model_name.lower().replace(' ', '_')}_confusion_matrix.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_confusion_matrix={output_path.name}")


def save_metric_comparison(results: list[dict]) -> None:
    metrics = ["accuracy", "f1_macro", "precision_macro", "recall_macro", "roc_auc_macro"]
    labels = [item["model"] for item in results]
    values = {metric: [item[metric] for item in results] for metric in metrics}

    x = np.arange(len(labels))
    width = 0.15
    fig, ax = plt.subplots(figsize=(10, 6))

    for idx, metric in enumerate(metrics):
        ax.bar(x + (idx - 2) * width, values[metric], width=width, label=metric)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Score")
    ax.set_title("Model Metric Comparison")
    ax.legend()
    ax.set_ylim(0, 1.1)
    plt.tight_layout()
    output_path = REPORTS_DIR / "model_metric_comparison.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_metric_chart={output_path.name}")


def save_target_distribution(df: pd.DataFrame) -> None:
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    plt.figure(figsize=(6, 5))
    counts.plot(kind="bar", color=["#4C72B0", "#55A868", "#C44E52"])
    plt.title("Target Class Distribution")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.tight_layout()
    output_path = REPORTS_DIR / "target_distribution.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"saved_target_distribution={output_path.name}")


def save_report(results: list[dict], selected_model_name: str, selected_pipeline: Pipeline, approved_features: list[str], excluded_features: list[str], numeric_cols: list[str], categorical_cols: list[str], df: pd.DataFrame) -> None:
    report_path = REPORTS_DIR / "model_evaluation.txt"
    lines = []
    lines.append("Decision-Intel Student Outcome Prediction Experiment")
    lines.append("=" * 80)
    lines.append("Project: Student Academic Outcome Classification")
    lines.append("Objective: Predict the final student academic outcome from the approved feature set.")
    lines.append(
        "Scope: This dataset does not contain direct marketing campaign or lead conversion data; this model represents the Student Outcome Prediction component of Decision-Intel."
    )
    lines.append("")
    lines.append("Dataset")
    lines.append(f"- Rows: {len(df)}")
    lines.append(f"- Original columns: {len(df.columns)}")
    lines.append(f"- Target: {TARGET_COLUMN}")
    lines.append(f"- Classes: {sorted(df[TARGET_COLUMN].unique().tolist())}")
    lines.append(f"- Missing values: {int(df.isna().sum().sum())}")
    lines.append("")
    lines.append("Approved feature list")
    for feature in approved_features:
        lines.append(f"- {feature}")
    lines.append("")
    lines.append("Excluded feature list")
    for feature in excluded_features:
        lines.append(f"- {feature}")
    lines.append("")
    lines.append("Preprocessing")
    lines.append("- Numeric features: StandardScaler after median imputation")
    lines.append("- Categorical features: Most-frequent imputation + OneHotEncoder(handle_unknown='ignore')")
    lines.append("- Split before fitting preprocessing transformations")
    lines.append(f"- Train/test split: 80/20, stratified, random_state={RANDOM_STATE}")
    lines.append(f"- Numeric columns used: {len(numeric_cols)}")
    lines.append(f"- Categorical columns used: {len(categorical_cols)}")
    lines.append("")
    lines.append("Model results")
    lines.append("Model | Accuracy | Precision | Recall | F1 | ROC-AUC")
    for item in results:
        lines.append(
            f"{item['model']} | {item['accuracy']:.4f} | {item['precision_macro']:.4f} | {item['recall_macro']:.4f} | {item['f1_macro']:.4f} | {item['roc_auc_macro']:.4f}"
        )
    lines.append("")
    lines.append(f"Selected model: {selected_model_name}")
    lines.append("Selection basis: highest macro F1, with ROC-AUC and accuracy used as tie-breakers if needed.")
    lines.append("")
    lines.append("Saved artifacts")
    lines.append(f"- Core model pipeline: {MODELS_DIR / 'decision_intel_student_outcome_model.pkl'}")
    lines.append(f"- Feature metadata: {MODELS_DIR / 'feature_metadata.json'}")
    lines.append(f"- Metrics metadata: {MODELS_DIR / 'model_metrics.json'}")
    lines.append("")
    pathways = [
        REPORTS_DIR / "target_distribution.png",
        REPORTS_DIR / "model_metric_comparison.png",
    ]
    lines.append("Visualizations")
    for path in pathways:
        lines.append(f"- {path.name}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved_report={report_path}")


def save_model_artifacts(selected_pipeline: Pipeline, selected_model_name: str, approved_features: list[str], excluded_features: list[str], metrics: dict, class_labels: list[str]) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    candidate_path = MODELS_DIR / "decision_intel_student_outcome_model.pkl"
    if candidate_path.exists():
        path = MODELS_DIR / "decision_intel_student_outcome_model_v2.pkl"
        print(f"existing_model_detected={candidate_path.name}; writing_new={path.name}")
    else:
        path = candidate_path

    with path.open("wb") as fp:
        pickle.dump(selected_pipeline, fp)
    print(f"saved_model={path}")

    metadata = {
        "selected_model": selected_model_name,
        "approved_features": approved_features,
        "excluded_features": excluded_features,
        "target_classes": class_labels,
        "random_state": RANDOM_STATE,
        "model_metrics": {
            "accuracy": metrics["accuracy"],
            "precision_macro": metrics["precision_macro"],
            "recall_macro": metrics["recall_macro"],
            "f1_macro": metrics["f1_macro"],
            "precision_weighted": metrics["precision_weighted"],
            "recall_weighted": metrics["recall_weighted"],
            "f1_weighted": metrics["f1_weighted"],
            "roc_auc_macro": metrics["roc_auc_macro"],
        },
    }

    feature_metadata_path = MODELS_DIR / "feature_metadata.json"
    feature_metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved_feature_metadata={feature_metadata_path}")

    metrics_path = MODELS_DIR / "model_metrics.json"
    metrics_path.write_text(json.dumps({
        "selected_model": selected_model_name,
        "metrics": metadata["model_metrics"],
    }, indent=2), encoding="utf-8")
    print(f"saved_model_metrics={metrics_path}")


def main() -> None:
    ML_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    approved_features, excluded_features, numeric_cols, categorical_cols = build_feature_lists(df)

    X = df[approved_features]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    class_labels = sorted(y.unique().tolist())

    models = {
        "Logistic Regression": LogisticRegression(max_iter=5000, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=RANDOM_STATE,
            class_weight="balanced",
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
    }

    results: list[dict] = []
    trained_model_map: dict[str, Pipeline] = {}

    for model_name, model in models.items():
        preprocessor = build_preprocessor(numeric_cols, categorical_cols)
        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )
        pipeline.fit(X_train, y_train)
        trained_model_map[model_name] = pipeline

        metrics = evaluate_model(model_name, pipeline, X_test, y_test, class_labels)
        results.append(metrics)

        save_confusion_matrix(model_name, metrics["confusion_matrix"], class_labels)

    save_metric_comparison(results)
    save_target_distribution(df)

    selected = max(results, key=lambda item: (item["f1_macro"], item["roc_auc_macro"], item["accuracy"]))
    selected_model_name = selected["model"]
    selected_pipeline = trained_model_map[selected_model_name]

    save_model_artifacts(
        selected_pipeline,
        selected_model_name,
        approved_features,
        excluded_features,
        selected,
        class_labels,
    )

    save_report(
        results,
        selected_model_name,
        selected_pipeline,
        approved_features,
        excluded_features,
        numeric_cols,
        categorical_cols,
        df,
    )

    print("\nRESULT_TABLE")
    print("Model | Accuracy | Precision | Recall | F1 | ROC-AUC")
    for item in results:
        print(
            f"{item['model']} | {item['accuracy']:.4f} | {item['precision_macro']:.4f} | {item['recall_macro']:.4f} | {item['f1_macro']:.4f} | {item['roc_auc_macro']:.4f}"
        )
    print(f"SELECTED_MODEL={selected_model_name}")
    print(f"SELECTED_MODEL_F1={selected['f1_macro']:.4f}")
    print(f"SELECTED_MODEL_ROC_AUC={selected['roc_auc_macro']:.4f}")


if __name__ == "__main__":
    main()
