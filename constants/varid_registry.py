# constants/varid_registry
from typing import Final

VARIDS: Final[dict[str, int]] = {
    "BODY_WEIGHT": 6,
    "BODY_HEIGHT": 7,
}

# --- interaction methods ---

def varid(name: str) -> int:
    try:
        return VARIDS[name.upper()]
    except KeyError as e:
        raise ValueError(f"Unknown VARID: {name}") from e

def varids(*names: str) -> list[int]:
    return [varid(n) for n in names]