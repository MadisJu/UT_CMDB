"""
Lightweight database utilities used during application startup.

At the moment the project only needs to guarantee that a SQLite database
file exists so the rest of the stack can operate without import errors.
When real database models are introduced this module can evolve to
contain the SQLAlchemy/SQLModel engine and metadata management.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.core.configs.config import settings

logger = logging.getLogger(__name__)


def _resolve_sqlite_path(raw_path: str) -> Path:
    
    cleaned = raw_path.lstrip("/")
    path = Path(cleaned)

    if path.is_absolute():
        return path

    project_root = settings.base_dir.parent.parent
    path = (project_root / path).resolve()

    return path


def create_db_and_tables() -> None:
    
    db_url = settings.database_url

    if db_url.startswith("sqlite:///"):
        relative_path = db_url.replace("sqlite:///", "", 1)
        db_path = _resolve_sqlite_path(relative_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if not db_path.exists():
            db_path.touch()
            logger.info("Created SQLite database at %s", db_path)
        else:
            logger.debug("SQLite database already present at %s", db_path)
        return

    logger.warning(
        "Database initialisation skipped; unsupported URL scheme in %s", db_url
    )


__all__ = ["create_db_and_tables"]
