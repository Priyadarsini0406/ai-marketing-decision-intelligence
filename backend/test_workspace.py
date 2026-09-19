import unittest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database.connection import Base
from database.models import Lead
from api.workspace import SimulationInput, simulate, overview, segments


class WorkspaceTests(unittest.TestCase):
    def test_optimization_cap_and_custom_allocations(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([Lead(customer_id='1', campaign_channel='Email', ad_spend=100, conversion=True),
                        Lead(customer_id='2', campaign_channel='SEO', ad_spend=200, conversion=True)])
            db.flush()
            result = simulate(SimulationInput(budget=1000, mode='optimized', max_channel_share=.6), db)
            self.assertEqual(result['allocations'], {'Email': 600, 'SEO': 400})
            self.assertEqual(result['predicted_conversions'], 8)
            custom = simulate(SimulationInput(budget=1000, mode='custom', allocations={'Email': 600, 'SEO': 400}), db)
            self.assertEqual(custom['predicted_conversions'], result['predicted_conversions'])
            with self.assertRaises(HTTPException) as error:
                simulate(SimulationInput(budget=1000, mode='optimized', max_channel_share=.4), db)
            self.assertEqual(error.exception.status_code, 422)
            with self.assertRaises(HTTPException):
                simulate(SimulationInput(budget=1000, mode='custom', allocations={'Unknown':1000}), db)
        engine.dispose()

    def test_empty_analytics_and_segments(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            self.assertEqual(overview(db)['summary']['leads'], 0)
            self.assertEqual(segments(db), [])
            with self.assertRaises(HTTPException) as error:
                simulate(SimulationInput(budget=100, mode='equal'), db)
            self.assertEqual(error.exception.status_code, 409)
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
