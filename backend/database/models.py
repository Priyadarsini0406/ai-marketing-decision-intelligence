from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .connection import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")
    active = Column(Boolean, nullable=False, default=True)

class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(Float, nullable=False)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    values = Column(JSON, nullable=False)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    columns = Column(JSON, nullable=False)
    rows = Column(JSON, nullable=False)
    created_at = Column(Float, nullable=False)

class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True)
    values = Column(JSON, nullable=False)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, unique=True, index=True)
    student_name = Column(String)
    course_interested = Column(String)
    program = Column(String)
    qualification = Column(String)
    academic_score = Column(Float)
    enquiry_source = Column(String)
    location = Column(String)
    admission_year = Column(Integer)
    enquiry_date = Column(String)
    lead_status = Column(String)
    engagement_level = Column(String)
    follow_up_status = Column(String)
    admission_status = Column(Boolean)
    ad_spend = Column(Float)

    predictions = relationship("MLPrediction", back_populates="lead", uselist=False)

    customer_id = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    income = Column(Float)
    campaign_channel = Column(String)
    campaign_type = Column(String)
    click_through_rate = Column(Float)
    conversion_rate = Column(Float)
    website_visits = Column(Integer)
    pages_per_visit = Column(Float)
    time_on_site = Column(Float)
    social_shares = Column(Integer)
    email_opens = Column(Integer)
    email_clicks = Column(Integer)
    previous_purchases = Column(Integer)
    loyalty_points = Column(Integer)
    conversion = Column(Boolean)

class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(String, primary_key=True, default=generate_uuid)
    lead_id = Column(String, ForeignKey("leads.id"))
    admission_probability = Column(Float)
    lead_score = Column(String)
    segment_cluster = Column(Integer)
    segment_name = Column(String)
    shap_explanation = Column(JSON) # Can store top positive/negative factors

    lead = relationship("Lead", back_populates="predictions")

    conversion_probability = Column(Float)

class ChannelMetric(Base):
    __tablename__ = "channel_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    channel_name = Column(String, unique=True, index=True)
    total_spend = Column(Float)
    total_admissions = Column(Integer)
    historical_cpa = Column(Float)
    historical_admission_rate = Column(Float)

    total_conversions = Column(Integer)
    historical_cac = Column(Float)
    historical_conversion_rate = Column(Float)

class BudgetSimulation(Base):
    __tablename__ = "budget_simulations"

    id = Column(String, primary_key=True, default=generate_uuid)
    scenario_name = Column(String)
    allocations = Column(JSON) # e.g., {"Google Ads": 5000, "Instagram": 2000}
    predicted_admissions = Column(Float)
    predicted_cpa = Column(Float)

    predicted_conversions = Column(Float)
