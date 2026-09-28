"""Single source of truth for the Decision-Intel lead-conversion model.

The validated XGBoost pipeline, its feature contract, preprocessing and SHAP
explainer all live here, so the offline training script, the batch import and
the FastAPI serving layer can never drift apart.

No value in this module is fabricated. When a field is genuinely unavailable
for a lead it is left missing and the fitted imputer supplies the statistic
learned from the training data.
"""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "Leads X Education.csv"
ARTIFACT_DIR = ROOT / "ml" / "models"
MODEL_PATH = ARTIFACT_DIR / "lead_conversion_xgboost.joblib"
METADATA_PATH = ARTIFACT_DIR / "lead_conversion_metadata.json"
SEGMENT_PATH = ARTIFACT_DIR / "lead_segments.joblib"

# The X Education lead dataset ships its target already encoded as 0/1.
TARGET_COLUMN = "Converted"
KEY_COLUMN = "Prospect ID"

# Prospect ID identifies a lead; Lead Number is a strictly increasing sequence.
# Both are excluded so nothing can memorise row order instead of learning.
IDENTIFIER_COLUMNS = ["Prospect ID", "Lead Number"]

NUMERIC_FEATURES = [
    "TotalVisits",
    "Total Time Spent on Website",
    "Page Views Per Visit",
    "Asymmetrique Activity Score",
    "Asymmetrique Profile Score",
]

RANDOM_STATE = 42

# Lead score bands already surfaced by the manager UI and reports.
HIGH_SCORE_MIN = 0.7
MEDIUM_SCORE_MIN = 0.4

# Segmentation is descriptive, not predictive: K-Means over the fitted model's
# own engagement features, so a lead's segment and its score describe the same
# real evidence.
SEGMENT_COUNT = 4

# Labels are handed out after ranking the clusters on their measured engagement
# index, so "High Intent" is always the cluster the data says is most engaged.
SEGMENT_LADDER = ["Low Engagement", "Casual Browsers", "Engaged Prospects", "High Intent"]

MIN_CLASS_COUNT = 5


class PipelineError(RuntimeError):
    """Raised when the dataset or artifacts violate the model contract."""


def read_dataset(path: str | os.PathLike = DATASET_PATH) -> pd.DataFrame:
    """Load and validate the lead dataset, raising on any contract breach."""
    path = Path(path)
    if not path.exists():
        raise PipelineError(f"Dataset not found: {path}")

    frame = pd.read_csv(path, low_memory=False)

    required = {KEY_COLUMN, TARGET_COLUMN, *NUMERIC_FEATURES}
    missing = required - set(frame.columns)
    if missing:
        raise PipelineError(f"Dataset is missing required columns: {sorted(missing)}")
    if frame[KEY_COLUMN].isna().any() or frame[KEY_COLUMN].astype(str).str.strip().eq("").any():
        raise PipelineError(f"{KEY_COLUMN} must be present and nonempty on every row")
    if frame[KEY_COLUMN].duplicated().any():
        raise PipelineError(f"{KEY_COLUMN} must be unique")

    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    if target.isna().any():
        raise PipelineError(f"{TARGET_COLUMN} must be 0 or 1 on every row")
    frame[TARGET_COLUMN] = target.astype(int)
    if set(frame[TARGET_COLUMN].unique()) - {0, 1}:
        raise PipelineError(f"{TARGET_COLUMN} must contain only 0 and 1")
    if frame[TARGET_COLUMN].value_counts().min() < MIN_CLASS_COUNT:
        raise PipelineError(
            f"{TARGET_COLUMN} needs at least {MIN_CLASS_COUNT} rows per class to stratify"
        )

    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame[KEY_COLUMN] = frame[KEY_COLUMN].astype(str)
    return frame


def resolve_features(frame: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Split the usable columns into numeric and categorical feature lists.

    Identifier columns, the target and any column with a single distinct value
    are dropped: a constant column cannot inform a split, and keeping it only
    adds encoding noise.
    """
    candidates = [
        column
        for column in frame.columns
        if column not in IDENTIFIER_COLUMNS and column != TARGET_COLUMN
    ]
    constant = [column for column in candidates if frame[column].nunique(dropna=False) <= 1]
    usable = [column for column in candidates if column not in constant]

    missing_numeric = [column for column in NUMERIC_FEATURES if column not in usable]
    if missing_numeric:
        raise PipelineError(f"Numeric features are unusable or constant: {missing_numeric}")

    numeric = [column for column in NUMERIC_FEATURES]
    categorical = [column for column in usable if column not in numeric]
    return numeric, categorical, constant


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    """Impute and one-hot encode. Trees need no scaling, so none is applied."""
    return ColumnTransformer(
        transformers=[
            (
                "num",
                SimpleImputer(strategy="median"),
                numeric,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def make_model(numeric: list[str] | None = None, categorical: list[str] | None = None, **overrides):
    """Build the validated XGBoost pipeline.

    Numeric and categorical lists may be omitted only when the saved metadata
    supplies the fitted contract.
    """
    from xgboost import XGBClassifier

    if numeric is None or categorical is None:
        contract = load_metadata()
        numeric, categorical = contract["numeric_features"], contract["categorical_features"]

    params = {
        "n_estimators": 400,
        "max_depth": 4,
        "learning_rate": 0.08,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "min_child_weight": 3,
        "reg_lambda": 1.0,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "tree_method": "hist",
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
    }
    params.update(overrides)

    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric, categorical)),
            ("classifier", XGBClassifier(**params)),
        ]
    )


def score_band(probability: float) -> str:
    if probability >= HIGH_SCORE_MIN:
        return "High"
    if probability >= MEDIUM_SCORE_MIN:
        return "Medium"
    return "Low"


def feature_frame(
    records: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> pd.DataFrame:
    """Project raw lead records onto the model feature contract.

    Columns absent from a record become NaN/None so the fitted imputer handles
    them, which keeps unknown or partially specified leads scoreable.
    """
    missing = [column for column in [*numeric, *categorical] if column not in records.columns]
    if missing:
        for column in missing:
            records[column] = np.nan
    return records[[*numeric, *categorical]]


def encoded_feature_names(pipeline: Pipeline, categorical: list[str]) -> list[tuple[str, str | None]]:
    """Map every encoded column back to its source feature.

    Returns (source feature, one-hot category or None) so explanations can say
    "Lead Source = Google" instead of leaking encoding internals.
    """
    numeric = pipeline.named_steps["preprocess"].named_transformers_["num"].feature_names_in_
    numeric_names = [str(column) for column in numeric]
    encoder = pipeline.named_steps["preprocess"].named_transformers_["cat"].named_steps["onehot"]

    mapping: list[tuple[str, str | None]] = [(name, None) for name in numeric_names]
    for column, categories in zip(categorical, encoder.categories_):
        for category in categories:
            mapping.append((column, str(category)))
    return mapping


def encoded_matrix(pipeline: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    """Apply the fitted preprocessing and return the dense model input."""
    return np.asarray(pipeline.named_steps["preprocess"].transform(frame), dtype=float)


def shap_contributions(pipeline: Pipeline, frame: pd.DataFrame) -> tuple[np.ndarray, float]:
    """Return SHAP values for the positive class and the model's base value.

    The explainer wraps the XGBoost classifier inside the fitted pipeline, so
    explanations always describe the model that produced the probability.
    """
    import shap

    classifier = pipeline.named_steps["classifier"]
    encoded = encoded_matrix(pipeline, frame)

    explainer = shap.TreeExplainer(classifier)
    values = np.asarray(explainer.shap_values(encoded))
    if values.ndim == 3:
        # Older SHAP returns one array per class; we explain the positive class.
        values = values[..., -1]
    if values.ndim != 2:
        raise PipelineError(f"Unexpected SHAP value shape: {values.shape}")

    base = np.ravel(np.asarray(explainer.expected_value))
    base_value = float(base[-1] if base.size > 1 else base[0])
    return values, base_value


def explain_frame(
    pipeline: Pipeline,
    frame: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    top_n: int = 5,
) -> list[dict]:
    """Build per-row positive/negative SHAP factor lists for a batch."""
    values, base_value = shap_contributions(pipeline, frame)
    mapping = encoded_feature_names(pipeline, categorical)
    if len(mapping) != values.shape[1]:
        raise PipelineError(
            f"SHAP produced {values.shape[1]} columns but {len(mapping)} feature names"
        )

    raw = frame.reset_index(drop=True)
    results: list[dict] = []
    for row_index in range(values.shape[0]):
        row = values[row_index]
        order = np.argsort(np.abs(row))[::-1]
        positive: list[dict] = []
        negative: list[dict] = []
        for encoded_index in order:
            contribution = float(row[encoded_index])
            if contribution == 0.0:
                continue
            feature, category = mapping[encoded_index]
            entry = {
                "feature": feature,
                "category": category,
                "shap_value": round(contribution, 6),
                "value": _raw_value(raw.iloc[row_index], feature),
            }
            (positive if contribution > 0 else negative).append(entry)
            if len(positive) >= top_n and len(negative) >= top_n:
                break
        results.append(
            {
                "model": "lead_conversion_xgboost",
                "method": "shap.TreeExplainer",
                "base_value": round(base_value, 6),
                "top_positive": positive[:top_n],
                "top_negative": negative[:top_n],
            }
        )
    return results


def _raw_value(row: pd.Series, feature: str):
    value = row[feature]
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return str(value)


def segment_features(pipeline: Pipeline, frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Return the imputed numeric engagement features the model was fitted on.

    The imputer is the fitted one inside the saved pipeline, so a lead is always
    segmented on exactly the values its prediction used.
    """
    numeric_step = pipeline.named_steps["preprocess"].named_transformers_["num"]
    columns = [str(column) for column in numeric_step.feature_names_in_]
    values = np.asarray(numeric_step.transform(frame[columns]), dtype=float)
    return values, columns


def _ladder_for(count: int) -> list[str]:
    """Stretch the label ladder so any cluster count still gets ordered names."""
    if count <= 0:
        return []
    step = len(SEGMENT_LADDER) / count
    return [
        SEGMENT_LADDER[min(len(SEGMENT_LADDER) - 1, int(position * step))]
        for position in range(count)
    ]


def fit_segments(pipeline: Pipeline, frame: pd.DataFrame, k: int = SEGMENT_COUNT) -> dict:
    """Cluster the real engagement features and name each cluster from the data.

    The clusters themselves are unsupervised: K-Means on the standardised
    engagement features the model was fitted on. Only the *labels* come from the
    model, because "High Intent" is a claim about conversion and the validated
    pipeline is the honest thing to rank on. Ranking on a hand-picked feature
    spread is unreliable here: three clusters can sit within 0.02 of each other
    on a mean-of-z-scores index while differing completely in behaviour.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    values, columns = segment_features(pipeline, frame)
    if len(values) < k:
        raise PipelineError(f"Need at least {k} rows to build {k} segments, got {len(values)}")

    scaler = StandardScaler().fit(values)
    scaled = scaler.transform(values)
    # n_init with a fixed random_state keeps the segmentation reproducible.
    kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(scaled)
    labels = kmeans.labels_

    engagement = scaled.mean(axis=1)
    priority = np.asarray(pipeline.predict_proba(frame)[:, 1], dtype=float)
    ranking = sorted(range(k), key=lambda cluster: float(priority[labels == cluster].mean()))
    ladder = _ladder_for(len(ranking))
    names = {cluster: ladder[position] for position, cluster in enumerate(ranking)}

    dominant: dict[int, str] = {}
    if "Lead Source" in frame.columns:
        sources = frame["Lead Source"].astype(str).to_numpy()
        for cluster in range(k):
            counts = pd.Series(sources[labels == cluster]).value_counts()
            if not counts.empty:
                dominant[cluster] = str(counts.index[0])

    return {
        "model": "lead_engagement_kmeans",
        "k": k,
        "columns": columns,
        "scaler": scaler,
        "kmeans": kmeans,
        "names": names,
        "dominant_source": dominant,
        "profile": {
            cluster: {
                "leads": int((labels == cluster).sum()),
                "engagement_index": round(float(engagement[labels == cluster].mean()), 4),
                "mean_probability": round(float(priority[labels == cluster].mean()), 4),
                "feature_means": {
                    column: round(float(values[labels == cluster, position].mean()), 4)
                    for position, column in enumerate(columns)
                },
            }
            for cluster in range(k)
        },
        "random_state": RANDOM_STATE,
        "rows_fitted": int(len(values)),
    }


def segment_label(artifact: dict, cluster: int) -> str:
    """Human-readable segment name, qualified by its dominant lead source."""
    name = artifact.get("names", {}).get(int(cluster)) or f"Segment {int(cluster) + 1}"
    source = artifact.get("dominant_source", {}).get(int(cluster))
    return f"{name} · {source}" if source else str(name)


def assign_segments(artifact: dict, pipeline: Pipeline, frame: pd.DataFrame) -> tuple[list[int], list[str]]:
    """Assign every row its real cluster index and segment name."""
    values, _ = segment_features(pipeline, frame)
    labels = artifact["kmeans"].predict(artifact["scaler"].transform(values))
    clusters = [int(label) for label in labels]
    return clusters, [segment_label(artifact, cluster) for cluster in clusters]


def save_segments(artifact: dict):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, SEGMENT_PATH)
    return SEGMENT_PATH


def load_segments() -> dict:
    if not SEGMENT_PATH.exists():
        raise PipelineError("Lead segments are missing. Run backend/train_model.py first.")
    return joblib.load(SEGMENT_PATH)


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise PipelineError(
            "Model metadata is missing. Run ml/scripts/train_lead_conversion_xgboost.py first."
        )
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def load_pipeline():
    """Load the trained pipeline and its feature contract."""
    if not MODEL_PATH.exists():
        raise PipelineError(
            "Trained model is missing. Run ml/scripts/train_lead_conversion_xgboost.py first."
        )
    contract = load_metadata()
    return joblib.load(MODEL_PATH), contract


def dataset_fingerprint(path: str | os.PathLike = DATASET_PATH) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_rows(path: str | os.PathLike = DATASET_PATH) -> dict[str, dict]:
    """Index the real dataset by Prospect ID for exact feature lookup."""
    frame = read_dataset(path)
    return {
        str(record[KEY_COLUMN]): record
        for record in frame.to_dict(orient="records")
    }


@lru_cache(maxsize=2)
def _cached_source_rows(stamp: int) -> dict[str, dict]:
    return source_rows()


def source_rows_cached() -> dict[str, dict]:
    """Dataset rows indexed by Prospect ID, reloaded when the file changes."""
    return _cached_source_rows(DATASET_PATH.stat().st_mtime_ns)


# Fields the leads table and the model feature space genuinely share. A lead
# imported from the dataset resolves by customer_id; a manually created lead is
# still scoreable for these fields, and the imputer supplies the rest.
LEAD_FEATURE_SOURCES = {
    "website_visits": "TotalVisits",
    "pages_per_visit": "Page Views Per Visit",
    "time_on_site": "Total Time Spent on Website",
}


def frame_for_lead(lead, contract: dict | None = None) -> tuple[pd.DataFrame, str]:
    """Build the model input for a lead, preferring its real dataset record.

    Returns the frame and a label describing where the features came from.
    """
    contract = contract or load_metadata()
    numeric = contract["numeric_features"]
    categorical = contract["categorical_features"]

    customer_id = getattr(lead, "customer_id", None)
    if customer_id:
        record = source_rows_cached().get(str(customer_id))
        if record is not None:
            return feature_frame(pd.DataFrame([record]), numeric, categorical), "dataset"

    record: dict = {column: np.nan for column in [*numeric, *categorical]}
    for column, source in LEAD_FEATURE_SOURCES.items():
        record[source] = getattr(lead, column, None)
    return feature_frame(pd.DataFrame([record]), numeric, categorical), "lead_fields"

