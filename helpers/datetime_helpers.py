# helpers/datetime_helpers.py
from datetime import date, datetime

def _age(dob: date, reference: date = date.today()) -> int:
    return reference.year - dob.year - ((reference.month, reference.day) < (dob.month, dob.day))