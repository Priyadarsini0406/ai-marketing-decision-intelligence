import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import train_model as training
from database.models import Dataset, Lead, MLPrediction


class TrainingTests(unittest.TestCase):
    def frame(self):
        rows = []
        for i in range(10):
            row = {column: i + 1 for column in training.COLUMNS}
            row.update(CustomerID=str(i), Gender='Female', CampaignChannel='Email',
                       CampaignType='Awareness', Conversion=i % 2)
            rows.append(row)
        return pd.DataFrame(rows)

    def test_validation_rejects_duplicate_ids_and_invalid_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            frame = self.frame()
            frame.to_csv(path, index=False)
            self.assertEqual(len(training.read_dataset(path)), 10)
            frame.loc[1, 'CustomerID'] = '0'
            frame.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'unique'):
                training.read_dataset(path)
            frame = self.frame()
            frame.loc[1, 'Conversion'] = 2
            frame.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'Conversion'):
                training.read_dataset(path)

    def test_pipeline_handles_new_categories_and_excludes_outcome_columns(self):
        frame = self.frame()
        model = training.make_model().fit(frame[training.FEATURES], frame.Conversion)
        frame.loc[0, 'CampaignChannel'] = 'Unseen channel'
        probability = model.predict_proba(frame[training.FEATURES])[:, 1]
        self.assertTrue(np.isfinite(probability).all())
        for column in ['CustomerID', 'Conversion', 'ConversionRate']:
            self.assertNotIn(column, model.feature_names_in_)

    def test_reimport_updates_predictions_without_duplicating_or_clearing_other_leads(self):
        engine = create_engine('sqlite:///:memory:')
        sessions = sessionmaker(bind=engine)
        training.Base.metadata.create_all(engine)
        with sessions.begin() as db:
            db.add(Lead(customer_id='unrelated'))
        with patch.object(training, 'engine', engine), patch.object(training, 'SessionLocal', sessions):
            training.persist(self.frame(), np.full(10, .3), 'test.csv')
            training.persist(self.frame(), np.full(10, .8), 'test.csv')
        with sessions() as db:
            self.assertEqual(db.query(Lead).count(), 11)
            self.assertEqual(db.query(MLPrediction).count(), 10)
            self.assertEqual(db.query(Dataset).count(), 1)
            self.assertTrue(all(p.lead_score == 'High' for p in db.query(MLPrediction)))
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
