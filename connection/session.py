# connection/session.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .db_config import get_sqlalchemy_url

_engine = None
_SessionLocal: sessionmaker[Session] | None = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_sqlalchemy_url(),
            echo=False,                 # flip to True for SQL echo
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,        # heals stale connections
            pool_recycle=1800,         # recycle every 30 min (SQL Server+NATs)
            connect_args={
                # big speedup for executemany/bulk inserts; harmless otherwise
                "fast_executemany": True
            },
        )
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _SessionLocal


def create_session() -> Session:
    """Explicit session (remember to close or use get_session())."""
    return get_sessionmaker()()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Contextmanager for manual use:
        with get_session() as db:
            ...
    """
    db = create_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# FastAPI-style dependency generator (kept for compatibility)
def get_db() -> Generator[Session, None, None]:
    """
    Usage in DI frameworks:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    with get_session() as db:
        yield db