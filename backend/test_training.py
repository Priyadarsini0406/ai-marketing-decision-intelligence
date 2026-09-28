"""Tests for the XGBoost lead-conversion pipeline and its database import."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import ml_service as svc
import train_model as training
from database.models import Lead, MLPrediction

ROOT = Path(__file__).resolve().parents[1]
DATASET = svc.DATASET_PATH

CATEGORICAL_FIXTURE = {
    "Lead Origin": "Landing Page Submission",
    "Lead Source": "Google",
    "TotalVisits": 4.0,
    "Total Time Spent on Website": 120.0,
    "Page Views Per Visit": 3.0,
}


def frame_fixture(rows: int = 40) -> pd.DataFrame:
    """A small frame that satisfies the real model feature contract."""
    frame = pd.read_csv(DATASET, nrows=rows, low_memory=False)
    return frame.reset_index(drop=True)


class ServiceContractTests(unittest.TestCase):
    def test_read_dataset_validates_target_and_keys(self):
        frame = svc.read_dataset()
        self.assertEqual(len(frame), 9240)
        self.assertEqual(set(frame[svc.TARGET_COLUMN].unique()), {0, 1})
        self.assertFalse(frame[svc.KEY_COLUMN].duplicated().any())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            frame.head(20).to_csv(path, index=False)

            broken = frame.head(20).copy()
            broken.loc[broken.index[0], svc.TARGET_COLUMN] = 7
            broken.to_csv(path, index=False)
            with self.assertRaisesRegex(svc.PipelineError, "only 0 and 1"):
                svc.read_dataset(path)

            broken = frame.head(20).copy()
            broken.loc[broken.index[1], svc.KEY_COLUMN] = broken.loc[broken.index[0], svc.KEY_COLUMN]
            broken.to_csv(path, index=False)
            with self.assertRaisesRegex(svc.PipelineError, "unique"):
                svc.read_dataset(path)

    def test_feature_contract_excludes_identifiers_target_and_constants(self):
        frame = frame_fixture()
        numeric, categorical, constant = svc.resolve_features(frame)
        approved = [*numeric, *categorical]

        self.assertNotIn(svc.TARGET_COLUMN, approved)
        for identifier in svc.IDENTIFIER_COLUMNS:
            self.assertNotIn(identifier, approved)
        self.assertIn("Magazine", constant)  # single-valued, cannot inform a split
        self.assertEqual(len(approved) + len(constant), len(frame.columns) - len(svc.IDENTIFIER_COLUMNS) - 1)
        self.assertTrue(set(numeric).issubset(approved))

    def test_unseen_category_still_scores(self):
        frame = frame_fixture()
        numeric, categorical, _ = svc.resolve_features(frame)
        pipeline = svc.make_model(numeric, categorical, n_estimators=10)
        pipeline.fit(frame[[*numeric, *categorical]], frame[svc.TARGET_COLUMN])

        mutated = frame.head(1).copy()
        mutated["Lead Source"] = "A channel never seen in training"
        probability = pipeline.predict_proba(
            svc.feature_frame(mutated, numeric, categorical)
        )[:, 1]
        self.assertTrue(np.isfinite(probability).all())
        self.assertGreaterEqual(probability[0], 0.0)
        self.assertLessEqual(probability[0], 1.0)

    def test_missing_features_fall_back_to_the_imputer(self):
        frame = frame_fixture()
        numeric, categorical, _ = svc.resolve_features(frame)
        pipeline = svc.make_model(numeric, categorical, n_estimators=10)
        pipeline.fit(frame[[*numeric, *categorical]], frame[svc.TARGET_COLUMN])

        # A manually created lead only shares a few fields with the model.
        sparse = pd.DataFrame([{"TotalVisits": 7.0}])
        probability = pipeline.predict_proba(svc.feature_frame(sparse, numeric, categorical))[:, 1]
        self.assertTrue(np.isfinite(probability).all())

    def test_shap_is_additive_against_the_model_logit(self):
        frame = frame_fixture(60)
        numeric, categorical, _ = svc.resolve_features(frame)
        pipeline = svc.make_model(numeric, categorical, n_estimators=25)
        model_input = frame[[*numeric, *categorical]]
        pipeline.fit(model_input, frame[svc.TARGET_COLUMN])

        probability = pipeline.predict_proba(model_input.head(5))[:, 1]
        values, base = svc.shap_contributions(pipeline, model_input.head(5))
        logit = np.log(probability / (1 - probability))
        # TreeSHAP must reconstruct the model output, proving the explainer is
        # bound to this exact model rather than an approximation.
        np.testing.assert_allclose(base + values.sum(axis=1), logit, atol=1e-3)

    def test_explanations_reference_source_features(self):
        frame = frame_fixture(60)
        numeric, categorical, _ = svc.resolve_features(frame)
        pipeline = svc.make_model(numeric, categorical, n_estimators=25)
        model_input = frame[[*numeric, *categorical]]
        pipeline.fit(model_input, frame[svc.TARGET_COLUMN])

        factors = svc.explain_frame(pipeline, model_input.head(3), numeric, categorical, top_n=4)
        self.assertEqual(len(factors), 3)
        for factor in factors:
            self.assertEqual(factor["model"], "lead_conversion_xgboost")
            self.assertEqual(factor["method"], "shap.TreeExplainer")
            for entry in factor["top_positive"]:
                self.assertGreater(entry["shap_value"], 0)
                self.assertIn(entry["feature"], [*numeric, *categorical])
            for entry in factor["top_negative"]:
                self.assertLess(entry["shap_value"], 0)
                self.assertIn(entry["feature"], [*numeric, *categorical])

    def test_score_bands_match_the_reported_thresholds(self):
        self.assertEqual(svc.score_band(0.95), "High")
        self.assertEqual(svc.score_band(0.70), "High")
        self.assertEqual(svc.score_band(0.55), "Medium")
        self.assertEqual(svc.score_band(0.40), "Medium")
        self.assertEqual(svc.score_band(0.10), "Low")


class ImportTests(unittest.TestCase):
    def test_lead_payload_maps_only_real_fields(self):
        record = frame_fixture(1).iloc[0].to_dict()
        payload = training.build_lead_payload(record)

        self.assertEqual(payload["customer_id"], record[svc.KEY_COLUMN])
        self.assertEqual(payload["conversion"], bool(record["Converted"]))
        self.assertEqual(payload["website_visits"], int(record["TotalVisits"]))
        self.assertEqual(payload["enquiry_source"], record["Lead Source"])
        # Columns the dataset cannot supply are never written, so they stay NULL
        # in the database rather than being invented.
        for column in ("ad_spend", "income", "campaign_channel", "loyalty_points"):
            self.assertIsNone(payload.get(column))

    def test_engagement_level_is_normalised(self):
        self.assertEqual(training.normalise_engagement("01.High"), "High")
        self.assertEqual(training.normalise_engagement("02.Medium"), "Medium")
        self.assertEqual(training.normalise_engagement("03.Low"), "Low")
        self.assertIsNone(training.normalise_engagement(np.nan))
        self.assertIsNone(training.normalise_engagement(None))

    def test_persist_removes_seeded_rows_and_stores_real_scores(self):
        frame = frame_fixture(12)
        engine = create_engine("sqlite:///:memory:")
        sessions = sessionmaker(bind=engine)
        training.Base.metadata.create_all(engine)

        probability = np.linspace(0.05, 0.95, len(frame))
        explanations = [
            {
                "model": "lead_conversion_xgboost",
                "method": "shap.TreeExplainer",
                "base_value": -0.4,
                "top_positive": [{"feature": "Lead Source", "category": "Google", "shap_value": 0.5, "value": "Google"}],
                "top_negative": [],
            }
            for _ in range(len(frame))
        ]

        with sessions.begin() as db:
            seeded = Lead(student_id="STU-1000", student_name="Student 0")
            db.add(seeded)
            db.flush()
            db.add(MLPrediction(lead_id=seeded.id, admission_probability=0.9,
                                shap_explanation={"positive": ["Academic Score"]}))
            unrelated = Lead(customer_id="keep-me", student_id="MANUAL-1")
            db.add(unrelated)

        with patch.object(training, "engine", engine), patch.object(training, "SessionLocal", sessions):
            with sessions.begin() as db:
                first = training.persist(db, frame, probability, explanations)
            with sessions.begin() as db:
                second = training.persist(db, frame, probability * 0.5, explanations)

        self.assertEqual(first["seeded_leads_removed"], 1)
        self.assertEqual(first["leads_created"], len(frame))
        self.assertEqual(second["leads_created"], 0)
        self.assertEqual(second["leads_updated"], len(frame))

        with sessions() as db:
            self.assertEqual(db.query(Lead).count(), len(frame) + 1)
            self.assertEqual(db.query(MLPrediction).count(), len(frame))
            self.assertIsNone(db.query(Lead).filter(Lead.student_id == "STU-1000").first())
            # The unrelated manual lead must survive untouched.
            self.assertIsNotNone(db.query(Lead).filter(Lead.customer_id == "keep-me").first())

            stored = db.query(MLPrediction).first()
            self.assertIsNotNone(stored.conversion_probability)
            self.assertIn(stored.lead_score, {"High", "Medium", "Low"})
            # No fabricated explanation may survive the import.
            self.assertEqual(stored.shap_explanation["method"], "shap.TreeExplainer")
        engine.dispose()

    def test_out_of_fold_scoring_covers_every_row(self):
        frame = frame_fixture(40)
        numeric, categorical, _ = svc.resolve_features(frame)
        probability, explanations = training.out_of_fold_scores(frame, numeric, categorical, folds=2)

        self.assertEqual(len(probability), len(frame))
        self.assertEqual(len(explanations), len(frame))
        self.assertTrue(np.isfinite(probability).all())
        self.assertTrue(((probability >= 0) & (probability <= 1)).all())
        for item in explanations:
            self.assertEqual(item["method"], "shap.TreeExplainer")


if __name__ == "__main__":
    unittest.main()
