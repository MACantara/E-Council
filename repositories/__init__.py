"""Repository layer for E-Council."""

from repositories.base import BaseRepository

repo = BaseRepository()


def get_repository(model=None, session=None):
    """Return a repository bound to the given model.

    Args:
        model: Optional model class to bind the repository to.
        session: Optional SQLAlchemy session override.

    Returns:
        BaseRepository instance with the model and session bound.
    """
    return BaseRepository(model=model, session=session)
