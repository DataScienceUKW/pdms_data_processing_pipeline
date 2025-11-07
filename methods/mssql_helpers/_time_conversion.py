# methods/mssql_helpers/_decimals
from sqlalchemy import func, literal_column

def _to_berlin_time(*, value):
    """Convert UTC datetime to Berlin local time (DST-aware)."""
    return value.op('AT TIME ZONE')('UTC').op('AT TIME ZONE')('W. Europe Standard Time')

def _to_utc_time(*, value):
    """Convert Berlin local time to UTC datetimeoffset."""
    return value.op('AT TIME ZONE')('W. Europe Standard Time').op('AT TIME ZONE')('UTC')

def _to_berlin_time_iso(*, value):
    """Return ISO 8601 Berlin-local string (with DST offset)."""
    berlin_time = _to_berlin_time(value=value)
    return func.FORMAT(berlin_time, literal_column("'yyyy-MM-ddTHH:mm:sszzz'"))