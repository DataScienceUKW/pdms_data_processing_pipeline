# schemas/demographics.py
from __future__ import annotations
from datetime import date, datetime
from pydantic import Field, model_validator
from .base_schema_out import BaseSchema
from helpers.datetime_helpers import _age

class DemographicsOut(BaseSchema):
    hashable_fields = {"case_number"}
    excluded_by_default = {"patient_date_of_birth"}
    normalization_maps = {
        "patient_sex": {
            # Male
            "m": "M", "male": "M", "männlich": "M",
            # Female
            "f": "F", "female": "F", "w": "F", "weiblich": "F",
            # Diverse
            "d": "D", "divers": "D",
            # Unknown
            "u": "U", "unknown": "U",
            # Fallback for anything not matched above
            "__default__": "U",
        }
    }

    case_number: str

    # patient fields
    patient_sex: str | None = None
    patient_date_of_birth: date | None = Field(default=None)
    patient_body_weight: float | None = None
    patient_body_height: float | None = None

    # encounter fields (also used for internal calculations)
    case_admission_time: datetime | None = Field(default=None) #exclude=True
    case_discharge_time: datetime | None = Field(default=None) #exclude=True

    # derived
    patient_age_today: int | None = None
    patient_age_at_admission: int | None = None

    @model_validator(mode="after")
    def _compute_ages(self) -> "DemographicsOut":
        dob = self.patient_date_of_birth
        if not dob:
            return self
        if self.patient_age_today is None:
            self.patient_age_today = _age(dob)
        if self.case_admission_time and self.patient_age_at_admission is None:
            self.patient_age_at_admission = _age(dob, self.case_admission_time.date())
        return self