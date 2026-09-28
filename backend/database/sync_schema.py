"""Sync SQLite tables to the current SQLAlchemy models.

create_all() only creates missing tables — it never adds columns to tables that
already exist. This script ALTERs existing tables so they match the models,
preserving the rows that are already stored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text
from database.connection import Base, engine
import database.models as models

PY_TO_SQLITE = {
    "String": "VARCHAR",
    "Integer": "INTEGER",
    "Float": "FLOAT",
    "Boolean": "BOOLEAN",
    "JSON": "JSON",
}


def main():
    schema = models.Base.metadata
    with engine.begin() as conn:
        for table in schema.sorted_tables:
            existing = {c["name"] for c in inspect(conn).get_columns(table.name)}
            added = []
            for column in table.columns:
                if column.name in existing or column.primary_key:
                    continue
                type_name = column.type.__class__.__name__
                sql_type = PY_TO_SQLITE.get(type_name, "VARCHAR")
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {sql_type}'
                conn.execute(text(ddl))
                added.append(f"{column.name} {sql_type}")
            if added:
                print(f"{table.name}: added {', '.join(added)}")
            else:
                print(f"{table.name}: ok (no changes)")

    print("All tables in sync with models.")


if __name__ == "__main__":
    main()