# connection/fetcher.py
from __future__ import annotations

from functools import wraps
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
)

import logging
import pandas as pd
from sqlalchemy.orm import Session

from .session import get_session

# ---- Types -------------------------------------------------------------------

Row = Mapping[str, Any]
T = TypeVar("T")  # transformed row type


class QueryFunc(Protocol):
    """Callable that executes a query using a provided SQLAlchemy Session.
    It should **not** create or close sessions itself.
    """
    def __call__(self, *, session: Session, **params) -> Iterable[Row]: ...


# ---- Decorators --------------------------------------------------------------

def with_db_session(fn: QueryFunc) -> Callable[..., Iterable[Row]]:
    """
    Decorator that opens a DB session for a single call to `fn`, making sure
    the session is always cleaned up afterwards.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs) -> Iterable[Row]:
        with get_session() as db:
            return fn(*args, session=db, **kwargs)
    return wrapper


# ---- Fetcher -----------------------------------------------------------------

class Fetcher:
    """
    Thin, reusable wrapper around a query function.

    Features
    --------
    - Simple call returning a **list** of rows (mappings)
    - `.iter()` for streaming rows (generator) under a single session
    - `.to_df()` convenience (handles empty gracefully)
    - `.to_csv()` / `.to_parquet()` convenience writers
    - `.with_defaults()` for pre-binding params
    - `.batched_iter()` / `.batched_to_df()` to chunk a large list parameter
      while reusing a single DB session

    Optional
    --------
    - `transform`: callable applied to each row before returning (e.g., to cast
      columns, validate, or map to Pydantic models).
    - `logger`: basic progress logging for batched calls.
    """

    def __init__(
        self,
        func: QueryFunc,
        defaults: Mapping[str, Any] | None = None,
        *,
        transform: Optional[Callable[[Row], T]] = None,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = None,
    ) -> None:
        self.func = func
        self.defaults: dict[str, Any] = dict(defaults or {})
        self.transform = transform
        self.logger = logger or logging.getLogger(__name__)
        self.name = name or getattr(func, "__name__", "query")

        @with_db_session
        def _runner(*, session: Session, **params) -> Iterable[Row]:
            return self.func(session=session, **{**self.defaults, **params})

        self._runner = _runner

    # ----- core API -----------------------------------------------------------

    def __call__(self, **overrides) -> list[T] | list[Row]:
        """Eagerly execute and return a list of rows (optionally transformed)."""
        rows = list(self._runner(**overrides))
        return self._apply_transform(rows)

    def iter(self, **overrides) -> Iterator[T] | Iterator[Row]:
        """Stream rows under a single session (useful for large result sets)."""
        params = {**self.defaults, **overrides}
        def _gen() -> Iterator[T] | Iterator[Row]:
            with get_session() as db:
                for r in self.func(session=db, **params):
                    yield self.transform(r) if self.transform else r
        return _gen()

    def to_df(self, **overrides) -> pd.DataFrame:
        """Return a pandas DataFrame (empty frame if no rows)."""
        rows = list(self.iter(**overrides))  # keep logic unified
        if not rows:
            return pd.DataFrame()
        first = rows[0]
        if isinstance(first, Mapping):
            return pd.DataFrame.from_records(rows)
        return pd.DataFrame(rows)

    def to_csv(self, path: str, index: bool = False, **overrides) -> str:
        """Write results to CSV and return the file path."""
        df = self.to_df(**overrides)
        df.to_csv(path, index=index)
        return path

    def to_parquet(self, path: str, **overrides) -> str:
        """Write results to Parquet and return the file path.
        Requires `pyarrow` (recommended) or `fastparquet` installed.
        """
        df = self.to_df(**overrides)
        df.to_parquet(path)
        return path

    def with_defaults(self, **more) -> "Fetcher":
        """Clone with extra default parameters and the same transform/logger."""
        return Fetcher(
            self.func,
            {**self.defaults, **more},
            transform=self.transform,
            logger=self.logger,
            name=self.name,
        )

    # ---------------- batching ------------------------------------------------

    def _call_with_session(self, db: Session, **params) -> list[Row]:
        return list(self.func(session=db, **{**self.defaults, **params}))

    def batched_iter(
        self,
        *,
        list_param: str,
        max_items: int = 1000,
        **overrides,
    ) -> Iterator[T] | Iterator[Row]:
        """
        Like `iter()`, but will run the underlying query multiple times,
        chunking a large sequence in `list_param` across calls while reusing a
        single DB session. Yields rows as they arrive.
        """
        seq = (
            overrides.get(list_param)
            if list_param in overrides
            else self.defaults.get(list_param)
        )

        if not _is_batchable_sequence(seq):
            yield from self.iter(**overrides)
            return

        seq_list = list(seq)
        n = len(seq_list)
        if n == 0 or n <= max_items:
            yield from self.iter(**overrides)
            return

        with get_session() as db:
            for i in range(0, n, max_items):
                chunk = seq_list[i : i + max_items]
                params = {**overrides, list_param: chunk}
                rows = self._call_with_session(db, **params)
                if not rows:
                    continue
                for r in rows:
                    yield self.transform(r) if self.transform else r
                self.logger.debug(
                    "[%s] fetched %d/%d items (chunk %d..%d)",
                    self.name, i + len(chunk), n, i, i + len(chunk) - 1
                )

    def batched_to_df(
        self,
        *,
        list_param: str,
        max_items: int = 1000,
        **overrides,
    ) -> pd.DataFrame:
        """DataFrame wrapper over `batched_iter()`."""
        rows = list(self.batched_iter(list_param=list_param, max_items=max_items, **overrides))
        if not rows:
            return pd.DataFrame()
        first = rows[0]
        if isinstance(first, Mapping):
            return pd.DataFrame.from_records(rows)
        return pd.DataFrame(rows)

    # ----- helpers ------------------------------------------------------------

    def _apply_transform(self, rows: list[Row]) -> list[T] | list[Row]:
        if not rows or self.transform is None:
            return rows  # type: ignore[return-value]
        return [self.transform(r) for r in rows]


# ---- Standalone helpers ------------------------------------------------------

def _is_batchable_sequence(obj: Any) -> bool:
    if obj is None:
        return False
    if isinstance(obj, (str, bytes, dict)):
        return False
    return isinstance(obj, Sequence)

def make_fetcher(func: QueryFunc, **defaults) -> Fetcher:
    return Fetcher(func, defaults)

def fetch_data(func: QueryFunc, **kwargs) -> pd.DataFrame:
    return make_fetcher(func).to_df(**kwargs)

def fetch_data_batched(
    func: QueryFunc,
    *,
    list_param: str,
    max_items: int = 1000,
    **kwargs,
) -> pd.DataFrame:
    return make_fetcher(func).batched_to_df(list_param=list_param, max_items=max_items, **kwargs)