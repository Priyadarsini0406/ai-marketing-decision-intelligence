import os
import random
import uuid
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Lead, MLPrediction, ChannelMetric, BudgetSimulation

# Database Setup
engine = create_engine("sqlite:///marketing_ai.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Cleanup existing mock data
db.query(MLPrediction).delete()
db.query(Lead).delete()
db.query(ChannelMetric).delete()
db.query(BudgetSimulation).delete()
db.commit()

# Constants
programs = ["MCA", "MBA", "B.E. Computer Science", "B.Tech AI & Data Science", "B.Com", "M.Sc Computer Science"]
sources = ["Google Ads", "Instagram", "Facebook", "Website", "Education Portal", "Referral"]
qualifications = ["High School", "Bachelor's Degree", "Diploma"]
statuses = ["New", "Contacted", "Counselling", "Application Started", "Application Submitted", "Admission Confirmed", "Not Converted"]

print("Seeding Education Mock Data...")

# 1. Seed Leads & Predictions
leads = []
for i in range(100):
    lead_id = str(uuid.uuid4())
    student_id = f"STU-{1000+i}"
    program = random.choice(programs)
    source = random.choice(sources)
    score = random.uniform(60.0, 99.0)
    ad_prob = random.uniform(0.1, 0.95)
    
    lead = Lead(
        id=lead_id,
        student_id=student_id,
        student_name=f"Student {i}",
        course_interested=program,
        program=program,
        qualification=random.choice(qualifications),
        academic_score=round(score, 2),
        enquiry_source=source,
        location="India",
        admission_year=2026,
        enquiry_date="2026-09-15",
        lead_status=random.choice(statuses),
        engagement_level=random.choice(["High", "Medium", "Low"]),
        follow_up_status="Pending",
        admission_status=ad_prob > 0.7,
        ad_spend=random.uniform(10, 100)
    )
    
    prediction = MLPrediction(
        id=str(uuid.uuid4()),
        lead_id=lead_id,
        admission_probability=round(ad_prob, 2),
        lead_score="High" if ad_prob > 0.7 else "Medium" if ad_prob > 0.4 else "Low",
        segment_cluster=random.randint(0, 3),
        segment_name="Highly Engaged" if ad_prob > 0.6 else "Needs Nurturing",
        shap_explanation={"positive": ["Academic Score", "Enquiry Source"], "negative": ["Follow-up delay"]}
    )
    
    db.add(lead)
    db.add(prediction)

# 2. Seed Channel Metrics
for source in sources:
    metric = ChannelMetric(
        id=str(uuid.uuid4()),
        channel_name=source,
        total_spend=random.uniform(1000, 5000),
        total_admissions=random.randint(10, 50),
        historical_cpa=random.uniform(50, 150),
        historical_admission_rate=random.uniform(0.05, 0.25)
    )
    db.add(metric)

# 3. Seed Budget Simulations
sim = BudgetSimulation(
    id=str(uuid.uuid4()),
    scenario_name="Optimal AI Allocation",
    allocations={"Google Ads": 4000, "Instagram": 2000, "Education Portal": 1500},
    predicted_admissions=120,
    predicted_cpa=62.5
)
db.add(sim)

db.commit()
print("Seeding Complete!")
