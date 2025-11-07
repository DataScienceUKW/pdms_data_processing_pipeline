# tests/test_get_db.py
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import exc as sa_exc

from connection.session import get_db
from tests.conftest import tx_active, select_1

def test_get_db_yields_a_working_session():
    gen = get_db()
    s: Session = next(gen)
    assert select_1(s) == 1
    assert tx_active(s) is True

    # Exhaust generator -> triggers cleanup (commit/rollback + release)
    with pytest.raises(StopIteration):
        next(gen)

    # After cleanup: no active transaction; Session usable again (lazy reconnect)
    assert tx_active(s) is False
    assert select_1(s) == 1
    assert tx_active(s) is True

def test_get_db_rollback_on_error():
    # If you expect get_db() to rollback on errors, simulate a failing transaction.
    gen = get_db()
    s: Session = next(gen)

    # Deliberately break something — for SQLite you can do a bad statement:
    with pytest.raises(sa_exc.DBAPIError):
        s.execute(text("SELECT * FROM definitely_not_a_table"))

    # Exhaust generator -> should handle rollback cleanly
    with pytest.raises(StopIteration):
        next(gen)

    assert tx_active(s) is False
    # Should be able to reuse it
    assert select_1(s) == 1