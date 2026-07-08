"""
Base model configuration and shared imports for E-Council database models.
"""

from extensions import db


class BaseModel:
    """Base model with common functionality for all models."""
    
    @classmethod
    def get_by_id(cls, id):
        """Get a record by ID."""
        return db.session.get(cls, id)
    
    @classmethod
    def get_all(cls):
        """Get all records."""
        return db.session.query(cls).all()
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new record."""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance
    
    def update(self, **kwargs):
        """Update the current record."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the current record."""
        db.session.delete(self)
        db.session.commit()
        return True