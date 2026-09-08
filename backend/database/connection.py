from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Default to SQLite for local development. 
# To use Supabase PostgreSQL, change this to:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@aws-0-region.pooler.supabase.com:6543/postgres"
SQLALCHEMY_DATABASE_URL = "sqlite:///./marketing_ai.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} 
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
