"""SQLAlchemy engine and session helpers."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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
    # Additive migration: old forecasts remain readable, never fabricate outcomes.
    columns = {c['name']: c for c in inspect(engine).get_columns('forecast_checks')}
    with engine.begin() as connection:
        if 'evaluation' not in columns:
            connection.execute(text('ALTER TABLE forecast_checks ADD COLUMN evaluation TEXT'))
        if engine.dialect.name == 'postgresql' and str(columns['target_ms']['type']) != 'BIGINT':
            connection.execute(text('ALTER TABLE forecast_checks ALTER COLUMN target_ms TYPE BIGINT'))


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
