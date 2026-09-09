import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database.connection import Base
from database.models import Lead, ChannelMetric, BudgetSimulation
from seed_analytics import populate


class AnalyticsTests(unittest.TestCase):
    def test_metrics_scenarios_and_repeat_runs(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([
                Lead(customer_id='1', campaign_channel='Email', ad_spend=100, conversion=True),
                Lead(customer_id='2', campaign_channel='Email', ad_spend=100, conversion=False),
                Lead(customer_id='3', campaign_channel='SEO', ad_spend=100, conversion=False),
                BudgetSimulation(scenario_name='Existing scenario', allocations={'Email': 50})])
            db.flush()
            populate(db)
            populate(db)
            self.assertEqual(db.query(ChannelMetric).count(), 2)
            email = db.query(ChannelMetric).filter_by(channel_name='Email').one()
            self.assertEqual((email.total_spend, email.total_conversions, email.historical_cac, email.historical_conversion_rate), (200, 1, 200, .5))
            self.assertIsNone(db.query(ChannelMetric).filter_by(channel_name='SEO').one().historical_cac)
            self.assertEqual(db.query(BudgetSimulation).count(), 51)
            for scenario in db.query(BudgetSimulation).filter(BudgetSimulation.scenario_name.like('Illustrative%')):
                budget = sum(scenario.allocations.values())
                self.assertGreaterEqual(budget, 25000)
                self.assertTrue(all(value >= 0 for value in scenario.allocations.values()))
                if 'scenario ' not in scenario.scenario_name:
                    self.assertAlmostEqual(budget, 100000)
                self.assertAlmostEqual(scenario.predicted_conversions, scenario.allocations['Email'] / 200, places=2)
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
