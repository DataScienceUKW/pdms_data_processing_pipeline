# tests/test_session_helpers.py
import pytest
from datetime import date, datetime

from schemas.demographics import DemographicsOut

@pytest.fixture
def demo():
    return DemographicsOut(
        case_number="007",
        patient_sex="M",
        patient_date_of_birth=date(1992, 12, 13),
        case_admission_time=datetime(2025, 10, 1, 8, 0),
    )

def test_dump_clean_default_excludes_dob(demo):
    data = demo.dump_clean()
    assert "patient_date_of_birth" not in data
    assert data["case_number"] == "007"

@pytest.mark.parametrize(
    "include, expect_dob",
    [
        (set(), False),
        ({"patient_date_of_birth"}, True),
    ],
)

def test_dump_clean_include_toggle_dob(demo, include, expect_dob):
    data = demo.dump_clean(include=include)
    assert ("patient_date_of_birth" in data) is expect_dob

def test_dump_hashed_hashes_case_number_and_excludes_dob(demo):
    data = demo.dump_hashed(salt="secret")
    # just check that we got a 12-char hex string; avoid hardcoding the exact hash
    assert isinstance(data["case_number"], str) and len(data["case_number"]) == 12
    assert "patient_date_of_birth" not in data
    # if your schema computes age-at-admission, assert it deterministically:
    assert data["patient_age_at_admission"] >= 0

def test_dump_hashed_can_include_dob(demo):
    data = demo.dump_hashed(salt="secret", include={"patient_date_of_birth"})
    assert isinstance(data["case_number"], str) and len(data["case_number"]) == 12
    assert "patient_date_of_birth" in data