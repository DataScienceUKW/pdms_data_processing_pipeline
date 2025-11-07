# _pipeline_helpers.py
from __future__ import annotations
import json
import hashlib
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from typing import IO, Any
from typing import Iterable, Mapping, Sequence, Optional, Callable, Dict, NamedTuple
from ._pipeline_helpers import _ensure_parent_dir
from helpers.hashing import hash_value

# --------- AUDIT LOGGER (PHI-safe JSONL) -------------------------------------
class AuditLogger:
    """
    Minimal JSONL audit sink for pipeline accesses.
    Writes one JSON object per line. Defaults to PHI-safe summaries.
    """

    def __init__(
        self,
        *,
        path: Optional[str] = None,
        stream: Optional[IO[str]] = None,
        include_id_samples: bool = False,
        id_sample_size: int = 3,
        id_hash_salt: Optional[str] = None,
    ) -> None:
        if not path and not stream:
            raise ValueError("Provide either 'path' or 'stream' for AuditLogger.")
        self._path = path
        self._stream = stream
        self.include_id_samples = include_id_samples
        self.id_sample_size = id_sample_size
        self.id_hash_salt = id_hash_salt or ""
        self.hash_ids = id_hash_salt is not None
        if path:
            _ensure_parent_dir(path)
            # newline + utf-8 ensures proper jsonl
            self._fh = open(path, "a", encoding="utf-8", newline="\n")
        else:
            self._fh = stream  # assumed text mode

    def close(self) -> None:
        try:
            if self._path and self._fh:
                self._fh.close()
        except Exception:
            pass

    def _hash_id(self, s: str) -> str:
        return hash_value(s, salt=self.id_hash_salt)

    def _summarize_ids(self, ids: Sequence[str]) -> dict[str, Any]:
        summary: dict[str, Any] = {"count": len(ids)}
        if self.include_id_samples and ids:
            sample = list(ids[: self.id_sample_size])
            if self.hash_ids:
                summary["hashed_ids"] = [self._hash_id(x) for x in sample]
            else:
                summary["ids"] = sample
        return summary

    def log_access(
        self,
        *,
        actor: Optional[str],
        action: str,                 # e.g. "fetch"
        resource: str,               # e.g. "demographics"
        by: str,                     # "cases" | "patients"
        ids: Sequence[str],
        fields: Optional[Sequence[str]],
        fetch_fields: Optional[Sequence[str]],
        include_fields: Optional[Sequence[str]],
        derived_added: Sequence[str],
        hashed: bool,
        out: Optional[str],
        out_format: Optional[str],
        rows: Optional[int],
        duration_ms: Optional[float] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        record = {
            "ts": datetime.now(ZoneInfo("Europe/Berlin")).isoformat(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "by": by,
            "ids": self._summarize_ids(ids),
            "fields_requested": list(fields) if fields is not None else None,
            "fetch_fields": list(fetch_fields) if fetch_fields is not None else None,
            "include_fields": list(include_fields) if include_fields is not None else None,
            "derived_added": list(derived_added),
            "hashed": hashed,
            "out": out,
            "out_format": out_format,
            "rows": rows,
            "duration_ms": duration_ms,
        }
        if extra:
            record["extra"] = extra
        self._fh.write(json.dumps(record, ensure_ascii=False))
        self._fh.write("\n")
        self._fh.flush()


def timeit() -> tuple[callable, callable]:
    """Tiny timing helper returning (start, stop)->elapsed_ms."""
    t0 = {"v": 0.0}
    def start() -> None:
        t0["v"] = time.perf_counter()
    def stop() -> float:
        return (time.perf_counter() - t0["v"]) * 1000.0
    return start, stop