# PDMS Extraction

## Overview

PDMS Extraction is a secure, minimal, and auditable data extraction pipeline designed for Patient Data Management Systems (PDMS). It enables reproducible, validated data pulls with a strong paper trail, ensuring data minimization and privacy compliance.

## Key Features

- **Data Minimization:** Extract only the fields you request.
- **Schema Validation:** Per-record validation using Pydantic-style schemas.
- **Configurable Hashing:** Project-specific, salted hashing for IDs to control de-identification.
- **Auditing & Logging:** JSON Lines audit trail with optional inclusion of ID samples.
- **Time-Zone Handling:** DST-aware conversion to Berlin/UTC time zones for MSSQL.

## Quick Start

```python
from pipeline.audit_logger import AuditLogger
from pipeline.extraction_pipeline import run_demographics

audit = AuditLogger(
    path="logs/audit.jsonl",
    include_id_samples=True,   # Show sample IDs in internal audit logs
    id_hash_salt=None           # Or set a salt to hash IDs in audit logs
)

df = run_demographics(
    by="cases",
    ids=["123", "234"],
    fields=[
        "case_number",
        "patient_sex",
        "patient_age_at_admission",
        "patient_body_height",
        "case_admission_time",
    ],
    hash_salt="custom_demographics_salt",  # Salt for hashing IDs in output
    out="out/demographics.csv",             # Output CSV path or None to disable export
    audit=audit,                           # AuditLogger instance or None to disable auditing
    actor="n.schrader",                    # Identifier for the actor triggering extraction
)

audit.close()
```

## Why PDMS Extraction?

Healthcare data pipelines often become complex and prone to data leaks. PDMS Extraction provides a tight interface to pull only necessary data, validate it, and record who accessed what, when, and why—without inadvertently exposing Protected Health Information (PHI). This ensures traceability, reproducibility, and compliance with data privacy regulations.

## Architecture / Project Structure

```
pdms_extraction/
  connection/            # Database session and configuration
  helpers/
    datetime_helpers.py  # Time zone conversion utilities for MSSQL
    hashing.py           # Salted hashing helpers
  methods/
    mssql_helpers/       # SQLAlchemy utilities (AT TIME ZONE, ISO formatting)
    fetch_demographics.py
  pipeline/
    audit_logger.py      # JSON Lines audit logger
    extraction_pipeline.py
  schemas/
    demographics.py      # Output data schema definitions
  tests/                 # Test suite
```

## Configuration (.env)

Create a `.env` file or set environment variables directly to configure database connection and audit behavior:

```bash
# --- Database (required) ---
DB_SERVER=your-sqlserver-host
DB_NAME=your-database
DB_USER=service-user
DB_PASSWORD=supersecret
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_ENCRYPT=true
DB_TRUSTSERVERCERTIFICATE=false

# --- Audit (optional; defaults shown) ---
AUDIT_PATH=logs/audit.jsonl
AUDIT_INCLUDE_ID_SAMPLES=true
AUDIT_ID_SAMPLE_SIZE=999
AUDIT_HASH_SALT=
```

These variables are automatically loaded during startup. If the `.env` file is missing or incomplete, extraction will fail to prevent unsafe operation.

## Usage Patterns

### 1. Minimal, Validated DataFrame

```python
df = run_demographics(
    by="cases",
    ids=["123"],
    fields=["case_number", "patient_sex", "patient_age_at_admission"],
    hash_salt="analytics-v1",  # Hashed IDs in output
    out=None,                  # No CSV export
    audit=None,                # No audit logging
    actor="data.eng",
)
```

### 2. Write to CSV

```python
df = run_demographics(
    by="cases",
    ids=["123", "234"],
    fields=["case_number", "patient_body_height", "case_admission_time"],
    hash_salt="analytics-v1",
    out="out/demographics.csv",
    audit=None,
    actor="data.eng",
)
```

### 3. Full Audit Trail

```python
from pipeline.audit_logger import AuditLogger

audit = AuditLogger(
    path="logs/audit.jsonl",
    include_id_samples=True,  # Include real IDs in internal audit logs
    id_hash_salt=None         # Optional salt for hashing IDs in audit logs
)

df = run_demographics(
    by="cases",
    ids=["123", "234"],
    fields=[...],
    hash_salt="project-salt-2025",  # Hashing salt for output IDs
    out=None,
    audit=audit,
    actor="n.schrader",
)

audit.close()
```

## Security & PHI Handling

- **Two Zones:**
  - **Internal Audit Zone:** Restricted, encrypted, and access-controlled.
    - `include_id_samples=True` logs real IDs for traceability.
    - Logs must be stored securely and not forwarded to third-party collectors.
    - Regular rotation and expiration of logs are recommended.
  - **Analytics / Output Zone:** Shareable with fewer restrictions.
    - Use `hash_salt` or enable ID hashing to anonymize identifiers.
    - Avoid including direct identifiers unless absolutely necessary.

- **Hashing Policies:**
  - `run_demographics(..., hash_salt="...")` hashes IDs in the output with the provided salt.
  - If `hash_salt=None`, IDs appear in clear text (only inside trusted PHI boundaries).
  - In `AuditLogger`, providing `id_hash_salt` enables hashing of IDs in audit logs; otherwise, raw IDs are logged.

- **Recommended Defaults:**
  - Outputs: Always use a non-empty `hash_salt` (e.g., `"project-2025-06"`).
  - Audit Logs: Set `include_id_samples=True` only if logs remain internal and secure.

## Time Zone Handling

For MSSQL, PDMS Extraction uses Windows time zone IDs (not IANA). Timestamps are converted to Berlin time (DST-aware) and formatted as ISO strings, e.g., `'yyyy-MM-ddTHH:mm:sszzz'`.

## Validation & Auditing

- Each row is validated against the schema defined in the `schemas/` directory.
- Invalid rows are dropped and counted.
- The audit log records validation summaries and errors.
- Audit logs are JSON Lines with entries like:

```json
{
  "ts": "2025-11-06T10:57:11Z",
  "actor": "n.schrader",
  "resource": "demographics",
  "params": {"by": "cases", "fields": ["..."], "count_ids": 2},
  "samples": {"ids": ["123", "234"]},   // Present only if include_id_samples=True
  "result": {"rows": 2, "validated": 2, "invalid": 0}
}
```

Close the logger with `audit.close()` when done.

## Testing

Run tests with:

```bash
pytest -q
```

Tests cover connection setup, schema validation, hashing, and pipeline behavior.

## Operational Checklist

- Always use `hash_salt` for outputs unless inside a trusted PHI boundary.
- Store audit logs on encrypted, access-controlled storage.
- Enable `include_id_samples=True` only for internal audit logs.
- Rotate and expire logs regularly; do not ship logs to third-party collectors.
- Set environment variables via `.env`.
- Verify time zone configuration uses Windows TZ ID: `'W. Europe Standard Time'`.

## Troubleshooting
- **Berlin time off by 1 hour**  
  Confirm usage of Windows TZ ID `'W. Europe Standard Time'` instead of IANA `'Europe/Berlin'`.

- **IDs not hashed in output**  
  Check if `hash_salt=None` was set. Provide a non-empty salt to enable hashing and safe joins.

## License

See [LICENSE](./LICENSE) — © 2025 Dr. Nikolas B. Schrader. All rights reserved.

## Build small, ship safe, audit everything.