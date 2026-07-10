"""Core helpers for idempotent seed scripts."""

from __future__ import annotations

from typing import Any

from extensions import db


def get_session():
    """Return the active SQLAlchemy session."""
    return db.session


def get_or_create(model, defaults=None, factory=None, **kwargs):
    """Return an existing record matching ``kwargs`` or create one.

    When ``factory`` is provided, the factory is used to build the new instance
    so that seed scripts and tests share the same object construction logic.
    Otherwise the model is instantiated directly.
    """
    session = get_session()
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False

    data = (defaults or {}).copy()
    data.update(kwargs)

    if factory is not None:
        instance = factory.create(**data)
    else:
        instance = model(**data)
        session.add(instance)
        session.commit()

    return instance, True
