"""Declarative base for future module-owned SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy metadata registry.

    Modules may define models against this base but retain ownership of their
    persistence mapping and migration history.
    """
