import sys
import os
import pandas as pd

# Add parent directory to path so we can import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, Base, SessionLocal
from database.models import Lead

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

def ingest_data(csv_path: str):
    print(f"Reading dataset from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    # Clean up column names if needed, though they match our model based on analysis
    # Drop useless columns
    columns_to_drop = ["AdvertisingPlatform", "AdvertisingTool"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Rename columns to match the SQLAlchemy model (snake_case)
    df = df.rename(columns={
        "CustomerID": "customer_id",
        "Age": "age",
        "Gender": "gender",
        "Income": "income",
        "CampaignChannel": "campaign_channel",
        "CampaignType": "campaign_type",
        "AdSpend": "ad_spend",
        "ClickThroughRate": "click_through_rate",
        "ConversionRate": "conversion_rate",
        "WebsiteVisits": "website_visits",
        "PagesPerVisit": "pages_per_visit",
        "TimeOnSite": "time_on_site",
        "SocialShares": "social_shares",
        "EmailOpens": "email_opens",
        "EmailClicks": "email_clicks",
        "PreviousPurchases": "previous_purchases",
        "LoyaltyPoints": "loyalty_points",
        "Conversion": "conversion"
    })
    
    # Ensure boolean type for conversion
    df['conversion'] = df['conversion'].astype(bool)

    db = SessionLocal()
    
    # Check if data already exists to avoid duplicates
    existing_count = db.query(Lead).count()
    if existing_count > 0:
        print(f"Database already contains {existing_count} leads. Skipping ingestion to prevent duplicates.")
        db.close()
        return

    print("Inserting data into database...")
    # Convert dataframe to list of dictionaries for bulk insert
    records = df.to_dict(orient="records")
    
    leads_to_insert = [Lead(**record) for record in records]
    
    # Bulk save
    try:
        db.bulk_save_objects(leads_to_insert)
        db.commit()
        print(f"Successfully inserted {len(leads_to_insert)} records.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    from pathlib import Path
    csv_file_path = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parents[2] / "data" / "Digital_Marketing_Campaign_Dataset.csv"
    )
    ingest_data(csv_file_path)
