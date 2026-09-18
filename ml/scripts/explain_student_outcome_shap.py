from __future__ import annotations

import json
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "decision_intel_student_outcome_model.pkl"
META_PATH = PROJECT_ROOT / "ml" / "models" / "feature_metadata.json"
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"
RANDOM_STATE = 42


def load_model_and_data():
    with MODEL_PATH.open("rb") as fp:
        pipeline = pickle.load(fp)
    with META_PATH.open("r", encoding="utf-8") as fp:
        metadata = json.load(fp)

    df = pd.read_csv(DATA_PATH, sep=";")
    approved_features = metadata["approved_features"]
    target_column = "Target"
    X = df[approved_features]
    y = df[target_column]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    return pipeline, metadata, X, y, X_test, y_test


def compute_explanations(pipeline, X_train, X_test, y_test, metadata):
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out().tolist()

    background = X_train.sample(n=min(100, len(X_train)), random_state=RANDOM_STATE)
    background_X = preprocessor.transform(background)
    test_X = preprocessor.transform(X_test)

    explainer = shap.Explainer(model, background_X, feature_names=feature_names)
    explanation = explainer(test_X, check_additivity=False)

    class_names = metadata["target_classes"]
    importance = np.abs(explanation.values).mean(axis=(0, 2))
    top_indices = np.argsort(importance)[::-1][:10]
    top_features = [(feature_names[i], float(importance[i])) for i in top_indices]

    return preprocessor, model, feature_names, class_names, explanation, top_features


def save_global_importance_plot(top_features, feature_names, explanation, class_names):
    fig, ax = plt.subplots(figsize=(10, 8))
    ordered = sorted(top_features, key=lambda x: x[1], reverse=True)
    names = [item[0] for item in ordered]
    values = [item[1] for item in ordered]
    ax.barh(names[::-1], values[::-1], color="#4C72B0")
    ax.set_title("Global SHAP Feature Importance (Top 10)")
    ax.set_xlabel("Mean |SHAP value| across samples and classes")
    plt.tight_layout()
    out = REPORTS_DIR / "shap_global_importance.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(10, 8))
    ax2.barh(names[::-1], values[::-1], color="#55A868")
    ax2.set_title("SHAP summary / bar plot")
    ax2.set_xlabel("Mean |SHAP value|")
    plt.tight_layout()
    fig2.savefig(REPORTS_DIR / "shap_summary.png", dpi=200)
    plt.close(fig2)

    return out


def select_representative_samples(y_test, predicted_probs, class_names):
    selected = []
    for cls in class_names:
        mask = y_test == cls
        if mask.any():
            idx = np.where(mask.to_numpy())[0][0]
            selected.append((idx, cls))
    return selected


def generate_individual_explanations(explanation, X_test, y_test, pipeline, class_names, feature_names):
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocess"]
    test_X = preprocessor.transform(X_test)

    representative = select_representative_samples(y_test, model.predict_proba(test_X), class_names)
    outputs = []

    for idx, actual_label in representative:
        row = X_test.iloc[[idx]]
        probs = model.predict_proba(preprocessor.transform(row))[0]
        pred_index = int(np.argmax(probs))
        predicted_label = class_names[pred_index]
        sample_contrib = explanation.values[idx, :, pred_index]
        feature_order = np.argsort(np.abs(sample_contrib))[::-1][:10]

        positive = []
        negative = []
        for f_idx in feature_order:
            value = float(sample_contrib[f_idx])
            name = feature_names[f_idx]
            if value > 0:
                positive.append({"feature": name, "value": value})
            elif value < 0:
                negative.append({"feature": name, "value": value})

        # Save waterfall plot when possible
        out_path = REPORTS_DIR / f"shap_individual_example_{idx + 1}.png"
        try:
            shap.plots.waterfall(explanation[idx, :, pred_index], show=False)
            plt.gcf().savefig(out_path, dpi=200)
            plt.close()
        except Exception:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh([feature_names[i] for i in feature_order[:10]][::-1], [float(sample_contrib[i]) for i in feature_order[:10]][::-1], color="#C44E52")
            ax.set_title(f"Sample {idx} SHAP contributions for class {predicted_label}")
            ax.set_xlabel("SHAP contribution")
            plt.tight_layout()
            fig.savefig(out_path, dpi=200)
            plt.close(fig)

        outputs.append({
            "sample_index": int(idx),
            "actual_outcome": actual_label,
            "predicted_outcome": predicted_label,
            "class_probabilities": {class_names[i]: float(probs[i]) for i in range(len(class_names))},
            "top_positive_factors": positive[:5],
            "top_negative_factors": negative[:5],
            "top_contributing_features": [
                {"feature": feature_names[i], "shap_value": float(sample_contrib[i])}
                for i in feature_order[:10]
            ],
            "plot_path": str(out_path.relative_to(PROJECT_ROOT)),
        })

    return outputs


def save_report(model, metadata, feature_names, class_names, explanation, top_features, example_outputs):
    report_path = REPORTS_DIR / "shap_explainability_report.md"
    lines = []
    lines.append("# Explainable Student Academic Outcome Prediction")
    lines.append("")
    lines.append("## Model used")
    lines.append(f"- Model type: {type(model).__name__}")
    lines.append(f"- Saved pipeline: {MODEL_PATH.name}")
    lines.append(f"- Selected model from training: {metadata['selected_model']}")
    lines.append("")
    lines.append("## Preprocessing pipeline used")
    lines.append("- Numeric: median imputation + StandardScaler")
    lines.append("- Categorical: most-frequent imputation + OneHotEncoder(handle_unknown='ignore')")
    lines.append(f"- Number of transformed features: {len(feature_names)}")
    lines.append(f"- Number of original approved features: {len(metadata['approved_features'])}")
    lines.append(f"- Target classes: {', '.join(class_names)}")
    lines.append("")
    lines.append("## SHAP method")
    lines.append("- Explainer: shap.Explainer with the trained Random Forest model and the transformed training background data")
    lines.append("- Reason: the model is a multiclass Random Forest classifier; SHAP values are computed per class using the actual trained model output")
    lines.append("")
    lines.append("## Global feature importance")
    for feature, value in top_features:
        lines.append(f"- {feature}: {value:.6f}")
    lines.append("")
    lines.append("## Individual explanations")
    for item in example_outputs:
        lines.append(f"### Sample index {item['sample_index']}")
        lines.append(f"- Actual outcome: {item['actual_outcome']}")
        lines.append(f"- Predicted outcome: {item['predicted_outcome']}")
        lines.append("- Class probabilities:")
        for key, value in item["class_probabilities"].items():
            lines.append(f"  - {key}: {value:.4f}")
        if item["top_positive_factors"]:
            lines.append("- Important positive factors:")
            for entry in item["top_positive_factors"]:
                lines.append(f"  - {entry['feature']}: {entry['value']:.4f}")
        if item["top_negative_factors"]:
            lines.append("- Important negative factors:")
            for entry in item["top_negative_factors"]:
                lines.append(f"  - {entry['feature']}: {entry['value']:.4f}")
        lines.append(f"- Plot: {item['plot_path']}")
        lines.append("")
    lines.append("## Important observations")
    lines.append("- SHAP explanations were generated from the actual saved model and preprocessing pipeline.")
    lines.append("- The model is a multiclass classifier, so contributions are reported per class rather than as a binary decision score.")
    lines.append("- This is Explainable Student Academic Outcome Prediction and does not represent direct marketing lead conversion prediction.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("- SHAP values explain model output, not causal effects.")
    lines.append("- Feature importance highlights association patterns in the training data and should be interpreted as model-based evidence rather than a causal statement.")
    lines.append("- The current dataset does not contain direct campaign/lead conversion data, so the explainability remains within the student academic outcome domain.")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pipeline, metadata, X, y, X_test, y_test = load_model_and_data()
    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    preprocessor, model, feature_names, class_names, explanation, top_features = compute_explanations(
        pipeline,
        X_train,
        X_test,
        y_test,
        metadata,
    )

    save_global_importance_plot(top_features, feature_names, explanation, class_names)
    example_outputs = generate_individual_explanations(explanation, X_test, y_test, pipeline, class_names, feature_names)
    report_path = save_report(model, metadata, feature_names, class_names, explanation, top_features, example_outputs)

    print("MODEL_TYPE", type(model).__name__)
    print("FEATURE_COUNT", len(feature_names))
    print("CLASS_NAMES", class_names)
    print("TOP_10_GLOBAL_FEATURES", top_features)
    print("REPORT_PATH", report_path)
    print("EXAMPLE_COUNT", len(example_outputs))


if __name__ == "__main__":
    main()
