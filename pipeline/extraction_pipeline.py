# pipeline.py
from __future__ import annotations
import logging
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Optional, Callable, Dict, NamedTuple

import pandas as pd

# Flat imports to match your project layout
from connection.fetcher import make_fetcher
from ._pipeline_helpers import _ensure_parent_dir, _validate_with_model, _write_df, _enforce_order, ResourceSpec
from .audit_logger import AuditLogger, timeit

# ---------- public API (registry-based) ----------
from .pipes.extract_demography import DEMOGRAPHICS_SPEC

REGISTRY: Dict[str, ResourceSpec] = {
    "demographics": DEMOGRAPHICS_SPEC,
}

def _plan_fetch_and_include_for(
    spec: ResourceSpec,
    by: str,
    requested: Optional[Sequence[str]],
) -> tuple[Optional[list[str]], Optional[list[str]]]:
    """
    Return (fetch_fields, include_fields) for a given resource spec.
    - If requested is None: let fetchers use their defaults (both None).
    - Otherwise:
      * fetch_fields = requested without derived names + required deps appended
      * include_fields = exactly 'requested' (preserve order)
    """
    if requested is None:
        return None, None

    requested = list(dict.fromkeys(requested))  # de-dupe but keep order
    req_set = set(requested)

    # some fields/derivations only make sense when by='cases'
    if by != "cases" and (spec.requires_cases & req_set):
        raise ValueError("Requested fields require by='cases' for this resource.")

    # start with non-derived
    fetch_fields = [f for f in requested if f not in spec.derived_deps]
    # append deps in stable order
    for name in requested:
        for dep in spec.derived_deps.get(name, ()):
            if dep not in fetch_fields:
                fetch_fields.append(dep)

    return fetch_fields, requested

def run_resource(
    resource: str,
    *,
    by: str,
    ids: Sequence[str],
    fields: Optional[Sequence[str]] = None,
    hash_salt: Optional[str] = None,
    out: Optional[str] = None,
    out_format: Optional[str] = None,
    audit: Optional[AuditLogger] = None,
    actor: Optional[str] = None,
) -> pd.DataFrame:
    if resource not in REGISTRY:
        raise ValueError(f"Unknown resource: {resource}")
    if by not in {"cases", "patients"}:
        raise ValueError("by must be 'cases' or 'patients'")

    spec = REGISTRY[resource]
    fetch_fields, include_fields = _plan_fetch_and_include_for(spec, by, fields)

    # choose fetcher + params shape
    if by == "cases":
        fetch_func = spec.fetchers.get("cases")
        if not fetch_func:
            raise ValueError(f"Resource '{resource}' does not support by='cases'.")
        params = {"case_numbers": ids, "fields": fetch_fields}
    else:
        fetch_func = spec.fetchers.get("patients")
        if not fetch_func:
            raise ValueError(f"Resource '{resource}' does not support by='patients'.")
        params = {"patient_ids": ids, "fields": fetch_fields}

    start, stop = timeit()
    start()

    # Fetch → validate
    fetcher = make_fetcher(fetch_func)
    rows = list(fetcher.iter(**params))

    cleaned = _validate_with_model(
        rows,
        spec.schema_cls,
        hash_salt=hash_salt,
        include=set(include_fields) if include_fields is not None else None,
        exclude=None,
    )

    df = pd.DataFrame(cleaned)
    df = _enforce_order(df, include_fields)
    _write_df(df, out, out_format)

    elapsed = stop()

    # ---- AUDIT (single JSONL line) ----
    if audit is not None:
        requested = list(fields) if fields is not None else []
        fetched = list(fetch_fields) if fetch_fields is not None else []
        derived_added = sorted(set(fetched) - set(requested))
        audit.log_access(
            actor=actor,
            action="fetch",
            resource=resource,
            by=by,
            ids=ids,
            fields=fields,
            fetch_fields=fetch_fields,
            include_fields=include_fields,
            derived_added=derived_added,
            hashed=bool(hash_salt),
            out=out,
            out_format=out_format,
            rows=len(df),
            duration_ms=elapsed,
        )

    return df

# ---------- endpoints ----------

def run_demographics(
    *,
    by: str = "cases",
    ids: Sequence[str],
    fields: Optional[Sequence[str]] = None,
    hash_salt: Optional[str] = None,
    out: Optional[str] = None,
    out_format: Optional[str] = None,
    audit: Optional[AuditLogger] = None,
    actor: Optional[str] = None,
) -> pd.DataFrame:
    return run_resource(
        "demographics",
        by=by,
        ids=ids,
        fields=fields,
        hash_salt=hash_salt,
        out=out,
        out_format=out_format,
        audit=audit,
        actor=actor,
    )