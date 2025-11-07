# helpers/hashing.py
import hashlib
from typing import Optional

def hash_value(value: str, *, salt: Optional[str] = None, length: int = 12) -> str:
    """
    Return a SHA-256 hash of `value` salted with `salt`.
    If no salt is provided, returns the original value unchanged.
    """
    if not salt:
        return value
    h = hashlib.sha256((salt + value).encode("utf-8")).hexdigest()
    return h[:length]