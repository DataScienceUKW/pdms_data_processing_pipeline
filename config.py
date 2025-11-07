# config.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

_LAST_CFG: Optional[dict] = None

# ---------------- helpers

def _bool(v: Optional[str], *, default: bool = False) -> bool:
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}

def _int(v: Optional[str], *, default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default

def _require_file(path: str | Path, *, description: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise RuntimeError(f"{description} not found at: {p}")
    return p

def _require_env(name: str) -> str:
    val = os.getenv(name)
    if val is None or val == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

# ---------------- .env loading (REQUIRED)

def load_env_or_fail(*, env_path: Optional[str] = None) -> Path:
    """
    Load a .env file with a sensible search order and fail if none found.

    Search order:
      1) explicit env_path argument
      2) $ENV_PATH environment variable
      3) ./.env in current working directory
      4) ./.env next to this config.py file

    Raises:
        RuntimeError if no .env could be located in any of the above places.
    """
    tried: list[Path] = []

    # 1) explicit
    if env_path:
        env_file = _require_file(env_path, description="Explicit .env")
        load_dotenv(env_file, override=False)
        return env_file

    # 2) ENV_PATH
    env_path_env = os.getenv("ENV_PATH")
    if env_path_env:
        env_file = _require_file(env_path_env, description="$ENV_PATH .env")
        load_dotenv(env_file, override=False)
        return env_file

    # 3) CWD/.env
    cwd_env = Path.cwd() / ".env"
    tried.append(cwd_env)
    if cwd_env.exists() and cwd_env.is_file():
        load_dotenv(cwd_env, override=False)
        return cwd_env

    # 4) config.py sibling .env
    here_env = Path(__file__).resolve().parent / ".env"
    tried.append(here_env)
    if here_env.exists() and here_env.is_file():
        load_dotenv(here_env, override=False)
        return here_env

    # Fail with helpful message
    tried_str = "\n  - ".join(str(p) for p in tried)
    raise RuntimeError(
        "No .env file found.\n"
        "Provide a path via init_runtime(env_path=...) or set ENV_PATH, or place a .env in one of:\n"
        f"  - {tried_str}"
    )

# ---------------- config assembly

def read_config() -> Dict[str, Any]:
    """
    Read configuration strictly from process env (after load_env_or_fail).
    No logging/side effects. Returns a plain dict with 'db' and 'audit' sections.
    """
    cfg: Dict[str, Any] = {}

    # ---- Database (use your existing discrete variables, NO DSN)
    db: Dict[str, Any] = {
        "server": _require_env("DB_SERVER"),
        "name": _require_env("DB_NAME"),
        "user": _require_env("DB_USER"),
        "password": _require_env("DB_PASSWORD"),
        "driver": os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
        # keep as strings to pass straight to pyodbc/sqlalchemy query args
        "encrypt": os.getenv("DB_ENCRYPT", "true"),
        "trust_server_certificate": os.getenv("DB_TRUSTSERVERCERTIFICATE", "false"),
    }
    cfg["db"] = db

    # ---- Audit (configure AuditLogger from .env)
    audit: Dict[str, Any] = {
        "path": os.getenv("AUDIT_PATH", "logs/audit.jsonl"),
        "include_id_samples": _bool(os.getenv("AUDIT_INCLUDE_ID_SAMPLES"), default=True),
        "id_sample_size": _int(os.getenv("AUDIT_ID_SAMPLE_SIZE"), default=3),
        # None/empty -> no hashing in the logger; non-empty -> hashing enabled in logger
        "id_hash_salt": (os.getenv("AUDIT_HASH_SALT") or None),
    }
    cfg["audit"] = audit

    return cfg

# ---------------- convenience wiring

def init_runtime(*, env_path: Optional[str] = None) -> Tuple[Dict[str, Any], Path]:
    """
    One call:
      - require & load the .env
      - return (cfg, env_file_path)
    """
    env_file = load_env_or_fail(env_path=env_path)
    cfg = read_config()
    # retain for later access (optional)
    global _LAST_CFG
    _LAST_CFG = {**cfg, "__env_loaded_from": str(env_file)}
    return _LAST_CFG, env_file

def get_last_config() -> Optional[dict]:
    """
    Return the last config produced by init_runtime(), or None if not called.
    """
    return _LAST_CFG

# ---------------- optional helpers

def make_audit_logger(cfg: Dict[str, Any]):
    """
    Build pipeline.audit_logger.AuditLogger from cfg['audit'].
    Imported lazily to avoid import side effects for users not using auditing.
    """
    from pipeline.audit_logger import AuditLogger
    a = cfg.get("audit", {})
    return AuditLogger(
        path=a.get("path"),
        include_id_samples=bool(a.get("include_id_samples", True)),
        id_sample_size=int(a.get("id_sample_size", 3)),
        id_hash_salt=a.get("id_hash_salt"),
    )

def build_sqlalchemy_url(cfg: Dict[str, Any]) -> str:
    """
    Optional convenience: build a SQLAlchemy URL from discrete DB_* vars WITHOUT requiring a DSN var.
    You can ignore this if you already assemble the engine elsewhere.
    """
    db = cfg["db"]
    user = db["user"]
    pwd = db["password"]
    server = db["server"]
    name = db["name"]
    driver = db["driver"].replace(" ", "+")  # URL param format
    encrypt = db["encrypt"]
    tsc = db["trust_server_certificate"]
    # Example for mssql+pyodbc:
    return (
        f"mssql+pyodbc://{user}:{pwd}@{server}/{name}"
        f"?driver={driver}&Encrypt={encrypt}&TrustServerCertificate={tsc}"
    )