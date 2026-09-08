"""Run from backend: python create_admin.py --email you@example.com"""
import argparse
import getpass
from api.auth import NewUser, create_user
from database.connection import Base, engine, SessionLocal
from database import models

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an administrator account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Administrator")
    args = parser.parse_args()
    password = getpass.getpass("Password (at least 12 characters): ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    data = NewUser(email=args.email, name=args.name, password=password, role="admin")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        create_user(data, db)
    print(f"Administrator {data.email} created. Sign in at /admin/login.")
