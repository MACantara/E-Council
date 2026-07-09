"""FastAPI repository layer re-exporting shared repository code."""

from api.repositories.base import APIBaseRepository
from repositories import get_repository, repo
from repositories.base import BaseRepository
from repositories.users import UserRepository

__all__ = [
    "APIBaseRepository",
    "BaseRepository",
    "get_repository",
    "repo",
    "UserRepository",
]
