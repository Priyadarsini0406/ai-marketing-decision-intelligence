from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from pathlib import Path

# Load backend/.env (SUPABASE_URL, DATABASE_URL, ...) into the environment.
# load_dotenv never overrides variables already set in the shell, so explicit
# exports (used by tests) still win.
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Default to SQLite for local development. 
# To use Supabase PostgreSQL, set DATABASE_URL to the pooler connection string,
# e.g. "postgresql://postgres.user:pw@aws-0-region.pooler.supabase.com:6543/postgres"
database_url = os.environ.get("DATABASE_URL") or "sqlite:///" + str(Path(__file__).resolve().parents[1] / "marketing_ai.db")
SQLALCHEMY_DATABASE_URL = database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
    # check_same_thread=False is needed only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
