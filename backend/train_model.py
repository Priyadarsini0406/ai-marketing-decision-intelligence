"""Train and import the local campaign dataset: python backend/train_model.py."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from database.connection import Base, SessionLocal, engine
from database.models import Dataset, Lead, MLPrediction

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / 'data' / 'Digital_Marketing_Campaign_Dataset.csv'
COLUMNS = dict(zip(
    ['CustomerID', 'Age', 'Gender', 'Income', 'CampaignChannel', 'CampaignType',
     'AdSpend', 'ClickThroughRate', 'ConversionRate', 'WebsiteVisits', 'PagesPerVisit',
     'TimeOnSite', 'SocialShares', 'EmailOpens', 'EmailClicks', 'PreviousPurchases',
     'LoyaltyPoints', 'Conversion'],
    ['customer_id', 'age', 'gender', 'income', 'campaign_channel', 'campaign_type',
     'ad_spend', 'click_through_rate', 'conversion_rate', 'website_visits', 'pages_per_visit',
     'time_on_site', 'social_shares', 'email_opens', 'email_clicks', 'previous_purchases',
     'loyalty_points', 'conversion']))
CATEGORICAL = ['Gender', 'CampaignChannel', 'CampaignType']
# ConversionRate describes observed conversions; omit it from prospective scoring.
FEATURES = [c for c in COLUMNS if c not in ('CustomerID', 'Conversion', 'ConversionRate')]


def read_dataset(path):
    frame = pd.read_csv(path, dtype={'CustomerID': str})
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame[list(COLUMNS)].isna().any().any():
        raise ValueError('Required dataset columns contain missing values')
    if frame.CustomerID.duplicated().any() or frame.CustomerID.str.strip().eq('').any():
        raise ValueError('CustomerID must be nonempty and unique')
    for column in set(COLUMNS) - set(CATEGORICAL) - {'CustomerID'}:
        frame[column] = pd.to_numeric(frame[column], errors='raise')
        if not np.isfinite(frame[column]).all():
            raise ValueError(f'{column} contains non-finite values')
    if set(frame.Conversion.unique()) != {0, 1} or frame.Conversion.value_counts().min() < 5:
        raise ValueError('Conversion must contain both 0 and 1, with at least five rows per class')
    return frame


def make_model():
    return Pipeline([
        ('encode', ColumnTransformer([
            ('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
            ('numeric', 'passthrough', [c for c in FEATURES if c not in CATEGORICAL])])),
        ('classifier', GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=42))])


def persist(frame, probabilities, name):
    """Upsert only the supplied customers; keep unrelated records and accounts."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal.begin() as db:
        leads = {lead.customer_id: lead for lead in db.query(Lead).all()}
        predictions = {p.lead_id: p for p in db.query(MLPrediction).all()}
        records = frame[list(COLUMNS)].rename(columns=COLUMNS).to_dict(orient='records')
        for record, probability in zip(records, probabilities):
            record['conversion'] = bool(record['conversion'])
            lead = leads.get(record['customer_id'])
            if lead is None:
                lead = Lead(**record)
                db.add(lead)
                db.flush()
            else:
                for key, value in record.items():
                    setattr(lead, key, value)
            prediction = predictions.get(lead.id)
            if prediction is None:
                prediction = MLPrediction(lead_id=lead.id)
                db.add(prediction)
            prediction.conversion_probability = float(probability)
            prediction.lead_score = 'High' if probability >= .7 else 'Medium' if probability >= .4 else 'Low'
            # Do not present explanations from a previous model as current ones.
            prediction.shap_explanation = None
        dataset = db.query(Dataset).filter(Dataset.name == name).first()
        if dataset is None:
            dataset = Dataset(name=name, created_at=time.time())
            db.add(dataset)
        dataset.columns = list(frame.columns)
        dataset.rows = json.loads(frame.to_json(orient='records'))


def train(csv_path=DEFAULT_CSV, output_dir=ROOT / 'backend' / 'artifacts', import_data=True):
    frame = read_dataset(csv_path)
    x, y = frame[FEATURES], frame.Conversion.astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, stratify=y, random_state=42)
    model = make_model()
    print(f'Training on {len(x_train)} rows; evaluating on {len(x_test)} held-out rows...', flush=True)
    model.fit(x_train, y_train)
    probability = model.predict_proba(x_test)[:, 1]
    predicted = (probability >= .5).astype(int)
    report = {
        'model': 'GradientBoostingClassifier', 'random_seed': 42,
        'dataset_sha256': hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
        'rows': len(frame), 'train_rows': len(x_train), 'test_rows': len(x_test),
        'features': FEATURES, 'excluded_columns': ['CustomerID', 'Conversion', 'ConversionRate', 'AdvertisingPlatform', 'AdvertisingTool'],
        'accuracy': accuracy_score(y_test, predicted),
        'balanced_accuracy': balanced_accuracy_score(y_test, predicted),
        'f1': f1_score(y_test, predicted), 'roc_auc': roc_auc_score(y_test, probability),
        'confusion_matrix': confusion_matrix(y_test, predicted, labels=[0, 1]).tolist(),
        'majority_baseline_accuracy': float(y_test.value_counts(normalize=True).max()),
        'stored_predictions': 'Five-fold out-of-fold probabilities; each row scored by a model that did not train on it.',
        'artifact': 'Pipeline refitted on all rows for future inference; metrics above come from the held-out evaluation.',
    }
    print('Generating out-of-fold lead predictions...', flush=True)
    probabilities = cross_val_predict(make_model(), x, y,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        method='predict_proba', n_jobs=1)[:, 1]
    model.fit(x, y)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / 'conversion_model.joblib')
    (output_dir / 'training_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if import_data:
        persist(frame, probabilities, Path(csv_path).name)
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=DEFAULT_CSV)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'backend' / 'artifacts')
    parser.add_argument('--no-import', action='store_true', help='Train without changing the database')
    args = parser.parse_args()
    train(args.csv, args.output_dir, not args.no_import)
