"""Isolated API fixture used by the admin browser tests; never uses the app database."""
import os
from pathlib import Path
import tempfile

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='decisionintel-browser-') as directory:
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(directory) / 'test.db')
        from database.connection import Base, engine, SessionLocal
        from api.auth import NewUser, create_user
        import uvicorn

        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            create_user(NewUser(name='Test Administrator', email='admin@example.com', password='BrowserTestPassword123!', role='admin'), db)
        try:
            uvicorn.run('main:app', host='127.0.0.1', port=8011, log_level='warning')
        finally:
            engine.dispose()
