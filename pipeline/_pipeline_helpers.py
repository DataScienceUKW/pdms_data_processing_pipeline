# _pipeline_helpers.py
from __future__ import annotations
import logging
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Optional, Callable, Dict, NamedTuple
import pandas as pd

log = logging.getLogger(__name__)

def _ensure_parent_dir(path: str) -> None:
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

def _validate_with_model(
    rows: Iterable[Mapping],
    model_cls,
    *,
    hash_salt: Optional[str] = None,
    include: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> list[dict]:
    cleaned: list[dict] = []
    errors: list[str] = []

    for i, row in enumerate(rows):
        try:
            obj = model_cls.model_validate(row)
            data = (
                obj.dump_hashed(salt=hash_salt, include=include, exclude=exclude, log=True)
                if hash_salt else
                obj.dump_clean(include=include, exclude=exclude, log=True)
            )
            cleaned.append(data)
        except Exception as exc:
            errors.append(f"row {i}: {exc}")

    if errors:
        for e in errors[:10]:
            log.warning("validation issue: %s", e)
        if len(errors) > 10:
            log.warning("... plus %d more validation issues", len(errors) - 10)

    return cleaned

def _write_df(df: pd.DataFrame, out: Optional[str], out_format: Optional[str]) -> None:
    if not out:
        return
    _ensure_parent_dir(out)
    fmt = (out_format or (Path(out).suffix.lower().lstrip(".")) or "csv")
    if fmt == "csv":
        df.to_csv(out, index=False)
    elif fmt in {"parquet", "pq"}:
        df.to_parquet(out, index=False)
    elif fmt == "jsonl":
        df.to_json(out, orient="records", lines=True, force_ascii=False)
    else:
        raise ValueError(f"Unsupported out format: {fmt}")
    log.info("Wrote %s (%d rows)", out, len(df))

def _enforce_order(df: pd.DataFrame, requested: Optional[Sequence[str]]) -> pd.DataFrame:
    """Slice/reshape df to exactly the requested columns in order."""
    if requested is None:
        return df
    cols = [c for c in requested if c in df.columns]
    if cols:
        return df.loc[:, cols]
    # If nothing survived validation, still return the requested schema (empty rows)
    return pd.DataFrame(columns=list(requested))

class ResourceSpec(NamedTuple):
    schema_cls: type
    derived_deps: Mapping[str, set[str]]
    requires_cases: set[str]
    fetchers: Mapping[str, Callable[..., Iterable[Mapping]]]
    # fetchers keys may include "cases" and/or "patients"