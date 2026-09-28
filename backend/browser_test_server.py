"""Isolated API fixture used by the admin browser tests; never uses the app database."""
import os
from pathlib import Path
import tempfile

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='decisionintel-browser-') as directory:
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(directory) / 'test.db')
        from database.connection import Base, engine, SessionLocal
        from api.auth import NewUser, create_user
        from database.models import Lead, MLPrediction, ChannelMetric, BudgetSimulation
        import uvicorn

        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            create_user(NewUser(name='Test Administrator', email='admin@example.com', password='BrowserTestPassword123!', role='admin'), db)
            lead = Lead(customer_id='TEST-LEAD', campaign_channel='SEO', campaign_type='Awareness', conversion=True, age=30, gender='Female', income=10000, ad_spend=100, click_through_rate=.1, conversion_rate=.1, website_visits=2, pages_per_visit=2, time_on_site=3, social_shares=1, email_opens=2, email_clicks=1, previous_purchases=1, loyalty_points=10)
            db.add(lead)
            db.flush()
            # Score with the real pipeline rather than a hardcoded probability.
            import ml_service as svc
            try:
                pipeline, contract = svc.load_pipeline()
                frame, _ = svc.frame_for_lead(lead, contract)
                probability = float(pipeline.predict_proba(frame)[0, 1])
                explanation = svc.explain_frame(
                    pipeline, frame, contract['numeric_features'], contract['categorical_features'], top_n=5
                )[0]
            except svc.PipelineError:
                probability, explanation = None, None
            db.add(MLPrediction(lead_id=lead.id, conversion_probability=probability,
                                admission_probability=probability,
                                lead_score=svc.score_band(probability) if probability is not None else None,
                                shap_explanation=explanation))
            db.add(ChannelMetric(channel_name='SEO', total_spend=100, total_conversions=2))
            db.add(BudgetSimulation(scenario_name='Test budget', allocations={'SEO':100}))
            db.commit()
        try:
            uvicorn.run('main:app', host='127.0.0.1', port=8011, log_level='warning')
        finally:
            engine.dispose()
