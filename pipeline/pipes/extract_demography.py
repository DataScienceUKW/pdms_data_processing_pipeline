from pipeline._pipeline_helpers import ResourceSpec
from methods.fetch_demographics import (
    fetch_demography_for_cases,
    fetch_demography_for_patients,
)
from schemas.demographics import DemographicsOut

DEMOGRAPHICS_SPEC = ResourceSpec(
    schema_cls=DemographicsOut,
    derived_deps={
        "patient_age_today": {"patient_date_of_birth"},
        "patient_age_at_admission": {"patient_date_of_birth", "case_admission_time"},
    },
    requires_cases={"case_number", "case_admission_time", "case_discharge_time", "patient_age_at_admission"},
    fetchers={
        "cases": fetch_demography_for_cases,
        "patients": fetch_demography_for_patients,
    },
)