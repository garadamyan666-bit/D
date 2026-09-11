"""SQLAlchemy engine and session helpers."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import BASE_DIR, settings


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///./"):
        path = BASE_DIR / url.removeprefix("sqlite:///./")
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    # Render supplies a generic postgresql:// URL. Explicitly select the
    # installed psycopg v3 driver instead of SQLAlchemy's psycopg2 default.
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


engine = create_engine(_database_url(), connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
