"""FastAPI database session and table creation."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DatabaseConfig

from api.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, **DatabaseConfig.get_engine_options(DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables using the shared Flask-SQLAlchemy metadata."""
    from models import db

    db.metadata.create_all(bind=engine)
