"""Test database isolation. Import this module FIRST in every test module.

database/connection.py binds its SQLAlchemy engine to DATABASE_URL the first
time it is imported, and main.py keeps its own reference to that engine. If a
test only set DATABASE_URL in setUpClass, any earlier import (for example by
another test module in the same `unittest discover` run) had already bound the
engine to the real backend/marketing_ai.db, and integration tests wrote there.

Importing this module before any project code points DATABASE_URL at one
temporary SQLite file for the whole test process, overriding backend/.env, and
refuses to continue if the engine was already bound to anything else.
Integration tests call reset_database() to start from empty tables.
"""
from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

REAL_DATABASE = (Path(__file__).resolve().parent / "marketing_ai.db").resolve()
_TEMP_DIR = Path(tempfile.mkdtemp(prefix="decisionintel-tests-"))
TEST_DATABASE = (_TEMP_DIR / "test.db").resolve()


def _bound_path() -> Path | None:
    connection = sys.modules.get("database.connection")
    if connection is None or not connection.engine.url.database:
        return None
    return Path(connection.engine.url.database).resolve()


if "database.connection" in sys.modules:
    raise RuntimeError("test_support must be imported before any project module; "
                       f"the database engine is already bound to {_bound_path()}")

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"


def ensure_test_database():
    """Return the project engine after proving it points at the temporary database."""
    from database.connection import engine
    bound = _bound_path()
    if bound is None or bound != TEST_DATABASE or bound == REAL_DATABASE:
        raise RuntimeError(f"Refusing to run: tests are bound to {bound}, not the temporary test database")
    return engine


def reset_database() -> None:
    """Drop and recreate every table in the temporary test database."""
    from database.connection import Base
    from database import models  # noqa: F401  (registers all tables)
    engine = ensure_test_database()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@atexit.register
def _cleanup() -> None:
    connection = sys.modules.get("database.connection")
    if connection is not None:
        connection.engine.dispose()
    shutil.rmtree(_TEMP_DIR, ignore_errors=True)
