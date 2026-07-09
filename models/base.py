"""
Base model configuration and shared imports for E-Council database models.
"""

from typing import Any

from extensions import db


class BaseModel:
    """Base model with common functionality for all models."""

    @classmethod
    def get_by_id(cls, id: Any) -> Any:
        """Get a record by ID."""
        return db.session.get(cls, id)

    @classmethod
    def get_all(cls) -> list[Any]:
        """Get all records."""
        return db.session.query(cls).all()

    @classmethod
    def create(cls, **kwargs: Any) -> "BaseModel":
        """Create a new record."""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, **kwargs: Any) -> "BaseModel":
        """Update the current record."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()
        return self

    def delete(self) -> bool:
        """Delete the current record."""
        db.session.delete(self)
        db.session.commit()
        return True
