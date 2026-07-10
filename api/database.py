"""FastAPI database session and table creation."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.settings import DATABASE_URL
from config import DatabaseConfig

engine = create_engine(DATABASE_URL, **DatabaseConfig.get_engine_options(DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """Return the currently configured SQLAlchemy engine."""
    return engine


def set_engine(database_url: str | None = None) -> None:
    """Replace the global engine and session factory for the given database URL.

    This is intended for tests that need to switch to a test database after the
    module has already been imported.
    """
    global engine, SessionLocal
    url = database_url or DATABASE_URL
    engine = create_engine(url, **DatabaseConfig.get_engine_options(url))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables using the shared Flask-SQLAlchemy metadata."""
    from models import db

    db.metadata.create_all(bind=engine)
