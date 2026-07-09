"""Generic repository layer for E-Council.

The repository layer is the only place in the application that imports the
SQLAlchemy session internals. Routes and services use the exported ``repo``
instance or call ``get_repository`` instead of touching ``db.session`` directly.
"""

from __future__ import annotations

from typing import Any

from werkzeug.exceptions import NotFound

from extensions import db


class BaseRepository:
    """Generic SQLAlchemy-backed repository.

    The repository can be used with a bound model (``get_repository(Model)``)
    or as a generic session manager (``repo``) when the model is supplied at
    call time.
    """

    def __init__(self, model: type | None = None, session: Any | None = None) -> None:
        """Initialize the repository.

        Args:
            model: Optional model class to bind to this repository.
            session: Optional SQLAlchemy session. Defaults to the Flask-SQLAlchemy
                scoped session from ``extensions``.
        """
        self.model = model
        self.session = session or db.session

    def query(self, *entities: Any) -> Any:
        """Return a SQLAlchemy query for the given entities.

        When no entities are provided, the bound model is used. If no model is
        bound, the call is invalid.
        """
        if not entities:
            if self.model is None:
                raise ValueError("Repository has no model; pass a model to query()")
            return self.session.query(self.model)
        return self.session.query(*entities)

    def add(self, obj: Any) -> None:
        """Stage an instance for insertion."""
        self.session.add(obj)

    def add_all(self, objects: list[Any]) -> None:
        """Stage a list of instances for insertion."""
        self.session.add_all(objects)

    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def flush(self) -> None:
        """Flush the current session."""
        self.session.flush()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.session.rollback()

    def delete(self, obj: Any) -> None:
        """Delete an instance and commit."""
        self.session.delete(obj)

    def get(self, model: Any | None = None, id: Any | None = None) -> Any | None:
        """Get a record by primary key.

        May be called as ``repo.get(Model, id)`` or ``repo.get(id)`` when the
        repository is bound to a model.
        """
        if model is not None and id is not None:
            return self.session.get(model, id)
        if self.model is None or model is None:
            raise ValueError("Repository has no model; pass a model to get()")
        return self.session.get(self.model, model)

    def get_or_404(self, id: Any) -> Any:
        """Get a bound-model record by primary key or raise 404."""
        if self.model is None:
            raise ValueError("Repository has no model")
        obj = self.session.get(self.model, id)
        if obj is None:
            raise NotFound()
        return obj

    def refresh(self, obj: Any) -> None:
        """Refresh an instance from the database."""
        self.session.refresh(obj)

    def create(self, **kwargs: Any) -> Any:
        """Create, commit, and return a new bound-model instance."""
        if self.model is None:
            raise ValueError("Repository has no model")
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        return instance

    def update(self, obj: Any, **kwargs: Any) -> Any:
        """Update an instance and commit."""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.session.commit()
        return obj
