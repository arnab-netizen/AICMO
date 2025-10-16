from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("BACKEND_DATABASE_URL", "postgresql+psycopg2://appuser:appsecret@localhost:5432/appdb")
ENGINE = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, future=True)

@contextmanager
def get_session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
