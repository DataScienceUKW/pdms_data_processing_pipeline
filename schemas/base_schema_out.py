from __future__ import annotations
from typing import Any, ClassVar, Iterable, Optional, Mapping
import logging

from pydantic import BaseModel, ConfigDict, model_serializer, model_validator
from helpers.hashing import hash_value

class BaseSchema(BaseModel):
    """
    Project-wide base for all Pydantic models.

    Features
    --------
    - Ignores unknown fields from the DB layer
    - Allows validating by field name or legacy aliases
    - Uniform clean/hashed dump helpers
    - Optional per-model identifier hashing via `hashable_fields`

    Usage (per model):
        class DemographicsOut(BaseSchema):
            hashable_fields = {"case_number", "patient_id"}
            ...

        m.dump_hashed(salt="secret")  # will hash those fields if present
    """

    # Pydantic config
    model_config = ConfigDict(
        extra="ignore",
        validate_by_alias=True,
        validate_by_name=True,
    )

    # Names of fields that should be hashed when a salt is provided at dump time
    hashable_fields: ClassVar[set[str]] = set()

    # Names of fields a model wants excluded by default
    excluded_by_default: ClassVar[set[str]] = set()

    # Optional per-model normalization maps. Subclasses can define mappings like:
    # normalization_maps = {
    #     "patient_sex": {"m": "M", "male": "M", "weiblich": "F", "__default__": "U"}
    # }
    normalization_maps: ClassVar[dict[str, dict[str, Any]]] = {}

    @classmethod
    def _normalize_value(cls, field: str, value: Any) -> Any:
        """Normalize a single field using the subclass-provided mapping.
        - Uses case-insensitive, trimmed keys.
        - If value is None or empty string -> returns None.
        - If key not found -> returns mapping.get("__default__", original value).
        """
        mapping = cls.normalization_maps.get(field)
        if mapping is None:
            return value
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        # Build a casefolded lookup to handle i18n (e.g., "Männlich") robustly
        folded_map = {str(k).strip().casefold(): v for k, v in mapping.items() if k != "__default__"}
        key = str(value).strip().casefold()
        if key in folded_map:
            return folded_map[key]
        return mapping.get("__default__", value)

    @model_validator(mode="before")
    @classmethod
    def _apply_normalization_maps(cls, data: Any) -> Any:
        """Apply `normalization_maps` to incoming data before validation.
        Supports dict-style inputs and returns data unchanged for other types.
        """
        if not isinstance(data, dict) or not getattr(cls, "normalization_maps", None):
            return data
        new_data = dict(data)
        for field in cls.normalization_maps.keys():
            if field in new_data:
                new_data[field] = cls._normalize_value(field, new_data[field])
        return new_data

    def _effective_exclude(
        self,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
    ) -> set[str]:
        exclude_set = set(exclude) if exclude else set()
        include_set = set(include) if include else set()
        effective = (self.excluded_by_default | exclude_set) - include_set
        return effective

    # ---------------- convenience dumps ----------------
    def dump_clean(
        self,
        *,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        log: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Return a dict with None/unset removed. Extra kwargs go to model_dump()."""
        effective_exclude = self._effective_exclude(include=include, exclude=exclude)
        result = self.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude=effective_exclude,
            **kwargs,
        )
        if log:
            log = logger or logging.getLogger(__name__)
            log.info(
                f"{self.__class__.__name__} dump_clean called; "
                f"excluded_by_default={self.excluded_by_default}, "
                f"explicit_include={include}, explicit_exclude={exclude}, "
                f"hashing_active=False"
            )
        return result

    def dump_hashed(
        self,
        *,
        salt: str,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        log: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Like dump_clean(), but passes a salt via context so fields listed in
        `hashable_fields` are hashed by the serializer below.
        """
        effective_exclude = self._effective_exclude(include=include, exclude=exclude)
        context = (kwargs.pop("context", None) or {})
        context = {**context, "salt": salt}
        result = self.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude=effective_exclude,
            context=context,
            **kwargs,
        )
        if log:
            log = logger or logging.getLogger(__name__)
            log.info(
                f"{self.__class__.__name__} dump_hashed called; "
                f"excluded_by_default={self.excluded_by_default}, "
                f"explicit_include={include}, explicit_exclude={exclude}, "
                f"hashing_active=True"
            )
        return result

    def json_clean(
        self,
        *,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        log: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> str:
        """Return a JSON string with None/unset removed."""
        effective_exclude = self._effective_exclude(include=include, exclude=exclude)
        result = self.model_dump_json(
            exclude_none=True,
            exclude_unset=True,
            exclude=effective_exclude,
            **kwargs,
        )
        if log:
            log = logger or logging.getLogger(__name__)
            log.info(
                f"{self.__class__.__name__} json_clean called; "
                f"excluded_by_default={self.excluded_by_default}, "
                f"explicit_include={include}, explicit_exclude={exclude}, "
                f"hashing_active=False"
            )
        return result

    def json_hashed(
        self,
        *,
        salt: str,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        log: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ) -> str:
        """Return a JSON string like json_clean(), but with hashing context applied."""
        effective_exclude = self._effective_exclude(include=include, exclude=exclude)
        context = (kwargs.pop("context", None) or {})
        context = {**context, "salt": salt}
        result = self.model_dump_json(
            exclude_none=True,
            exclude_unset=True,
            exclude=effective_exclude,
            context=context,
            **kwargs,
        )
        if log:
            log = logger or logging.getLogger(__name__)
            log.info(
                f"{self.__class__.__name__} json_hashed called; "
                f"excluded_by_default={self.excluded_by_default}, "
                f"explicit_include={include}, explicit_exclude={exclude}, "
                f"hashing_active=True"
            )
        return result

    # ---------------- automatic hashing hook ----------------
    @model_serializer(mode="wrap")
    def _apply_hashing(self, handler, info):
        data = handler(self)
        salt = (info.context or {}).get("salt")
        if not salt or not self.hashable_fields:
            return data
        # Only hash present string fields listed in hashable_fields
        for field in self.hashable_fields:
            val = data.get(field)
            if isinstance(val, str):
                data[field] = hash_value(val, salt=salt)
        return data