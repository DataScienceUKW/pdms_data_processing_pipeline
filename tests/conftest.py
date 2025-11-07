# tests/conftest.py
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from connection.session import get_engine, get_session

# ---------- Engine / Session fixtures ----------

@pytest.fixture(scope="session")
def engine():
    """Process-wide engine (your code already enforces singleton; this just reuses it)."""
    return get_engine()

@pytest.fixture(scope="function")
def db_session() -> Session:
    """Fresh SQLAlchemy session per test (transactionless by default)."""
    with get_session() as session:
        yield session

# ---------- helpers / import in tests ----------

def select_1(executor) -> int:
    """
    Run SELECT 1 against either a Session or a Connection.
    """
    return executor.execute(text("SELECT 1")).scalar()

def tx_active(sess: Session) -> bool:
    """
    Robustly detect if a Session has an active transaction across SQLAlchemy versions.
    Prefers get_transaction() when available; falls back to in_transaction / in_transaction().
    """
    if hasattr(sess, "get_transaction"):
        tx = sess.get_transaction()
        return bool(tx and tx.is_active)
    if hasattr(sess, "in_transaction") and callable(getattr(sess, "in_transaction")):
        return bool(sess.in_transaction())
    if hasattr(sess, "in_transaction"):  # SQLA 2.x attr (property-like)
        return bool(sess.in_transaction)
    return False