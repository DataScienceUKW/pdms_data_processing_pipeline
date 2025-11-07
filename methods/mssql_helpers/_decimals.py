# methods/mssql_helpers/_decimals
from sqlalchemy import select, func, literal_column
from sqlalchemy.orm import Session, aliased
from models.sql_datadecimal63 import CO6DataDecimal63

def _nearest_decimal_val_to_dt(*, varid: int, p, ref_dt):
    """
    Returns a correlated scalar subquery selecting the value for `varid`
    nearest to `ref_dt` for patient alias `p`.
    """
    d = aliased(CO6DataDecimal63)
    return (
        select(d.val)
        .where(
            d.Parent_ID == p.ID,
            d.VarID == varid,
            d.deleted == 0,
            d.FlagCurrent == 1,
        )
        .order_by(func.abs(func.datediff(literal_column("second"), d.DateTimeTo, ref_dt)))
        .limit(1)
        .scalar_subquery()
    )

def _latest_decimal_val(*, varid: int, p):
    """
    Returns a correlated scalar subquery selecting the latest value for `varid` for patient alias `p`.
    """
    d = aliased(CO6DataDecimal63)
    return (
        select(d.val)
        .where(
            d.Parent_ID == p.ID,
            d.VarID == varid,
            d.deleted == 0,
            d.FlagCurrent == 1,
        )
        .order_by(d.DateTimeTo.desc())
        .limit(1)
        .scalar_subquery()
    )