# tests/test_connectivity.py
import pytest
from connection.session import get_engine
from tests.conftest import select_1

@pytest.mark.smoke
def test_engine_singleton_and_connectivity():
    e1 = get_engine()
    e2 = get_engine()
    assert e1 is e2, "Engine should be a singleton in this app"
    with e1.connect() as conn:
        assert select_1(conn) == 1

@pytest.mark.smoke
@pytest.mark.parametrize("use", ["connection", "session"])
def test_select_1_works_for_session_and_connection(engine, db_session, use):
    if use == "connection":
        with engine.connect() as conn:
            assert select_1(conn) == 1
    else:
        assert select_1(db_session) == 1