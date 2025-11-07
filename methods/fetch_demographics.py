# methods/fetch_demographics.py
from typing import Sequence
from sqlalchemy import select, join
from sqlalchemy.orm import Session, aliased

from models.sql_patient import Patient
from models.sql_fall import Fall
from constants.varid_registry import varids
from .mssql_helpers._decimals import _nearest_decimal_val_to_dt, _latest_decimal_val
from .mssql_helpers._time_conversion import _to_berlin_time_iso


def _metric_expr(*, varid: int, p, ref_dt=None):
    """If ref_dt is given, take the value nearest to that datetime; else take latest overall."""
    return (
        _nearest_decimal_val_to_dt(varid=varid, p=p, ref_dt=ref_dt)
        if ref_dt is not None
        else _latest_decimal_val(varid=varid, p=p)
    )


def _build_field_map(*, p, f=None, fields: Sequence[str], ref_dt_for_metrics=None):
    """
    Make a unified field map. If a Fall alias f is supplied, case_* fields are available.
    ref_dt_for_metrics controls BODY_* selection (nearest to admission vs latest).
    """
    field_map = {
        "patient_id": p.ID.label("patient_id"),
        "patient_date_of_birth": p.GEB.label("patient_date_of_birth"),
        "patient_sex": p.GESCHLECHT.label("patient_sex"),
    }

    # Case-related fields only when a Fall is present
    if f is not None:
        field_map.update(
            {
                "case_number": f.FALLNR.label("case_number"),
                "case_admission_time": _to_berlin_time_iso(value=f.AUFN).label("case_admission_time"),
                "case_discharge_time": _to_berlin_time_iso(value=f.ENTL).label("case_discharge_time"),
            }
        )

    # Dynamic metrics only if requested
    need_weight = "patient_body_weight" in fields
    need_height = "patient_body_height" in fields
    if need_weight or need_height:
        BODY_WEIGHT, BODY_HEIGHT = varids("BODY_WEIGHT", "BODY_HEIGHT")
        if need_weight:
            field_map["patient_body_weight"] = _metric_expr(
                varid=BODY_WEIGHT, p=p, ref_dt=ref_dt_for_metrics
            ).label("patient_body_weight")
        if need_height:
            field_map["patient_body_height"] = _metric_expr(
                varid=BODY_HEIGHT, p=p, ref_dt=ref_dt_for_metrics
            ).label("patient_body_height")

    # Validate requested fields
    unknown = [name for name in fields if name not in field_map]
    if unknown:
        raise ValueError(f"Unknown demographic fields requested: {unknown}")

    return field_map


def _execute_select(session: Session, selectable, fields, field_map, whereclause=None):
    stmt = (
        select(*(field_map[name] for name in fields))
        .select_from(selectable)
        .distinct()
    )
    if whereclause is not None:
        stmt = stmt.where(whereclause)
    return session.execute(stmt).mappings().fetchall()


def fetch_demography_for_cases(
    session: Session,
    case_numbers: Sequence[str],
    fields: Sequence[str] | None = None,
):
    p = aliased(Patient)
    f = aliased(Fall)

    # Defaults match current behavior
    if not fields:
        fields = [
            "patient_id",
            "case_number",
            "patient_date_of_birth",
            "patient_sex",
            "case_admission_time",
            "case_discharge_time",
        ]

    # For cases, prefer measurements nearest to admission time
    field_map = _build_field_map(
        p=p,
        f=f,
        fields=fields,
        ref_dt_for_metrics=f.AUFN,
    )

    selectable = join(p, f, p.ID == f.Patient_ID)
    whereclause = f.FALLNR.in_(case_numbers)

    return _execute_select(session, selectable, fields, field_map, whereclause)


def fetch_demography_for_patients(
    session: Session,
    patient_ids: Sequence[int],
    fields: Sequence[str] | None = None,
):
    p = aliased(Patient)

    # Defaults match current behavior
    if not fields:
        fields = ["patient_id", "patient_date_of_birth", "patient_sex"]

    # For patients, use latest measurements overall
    field_map = _build_field_map(
        p=p,
        f=None,
        fields=fields,
        ref_dt_for_metrics=None,
    )

    selectable = p
    whereclause = p.ID.in_(patient_ids)

    return _execute_select(session, selectable, fields, field_map, whereclause)