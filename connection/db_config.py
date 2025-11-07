# connection/config.py
from __future__ import annotations
import os
from urllib.parse import quote_plus
from typing import Optional

from config import init_runtime, build_sqlalchemy_url, read_config

def _odbc_connect_str_from_cfg(cfg: dict) -> str:
    """Optional: derive a classic ODBC connect string from the already-parsed cfg['db']."""
    db = cfg["db"]
    server_value = db["server"]
    instance = os.getenv("DB_INSTANCE")
    port = os.getenv("DB_PORT")
    if instance:
        server_value = f"{server_value}\\{instance}"
    elif port:
        server_value = f"{server_value},{port}"
    parts = {
        "DRIVER": db["driver"],
        "SERVER": server_value,
        "DATABASE": db["name"],
        "Encrypt": db["encrypt"],
        "TrustServerCertificate": db["trust_server_certificate"],
        "MARS_Connection": os.getenv("DB_MARS", "yes"),
        "Connection Timeout": os.getenv("DB_CONNECT_TIMEOUT", "15"),
    }
    # use UID/PWD unless integrated security is requested
    use_integrated = os.getenv("DB_INTEGRATED_SECURITY", "").strip().lower() in {"1","true","yes","on"}
    if use_integrated:
        parts["Trusted_Connection"] = "yes"
    else:
        parts["UID"] = db["user"]
        parts["PWD"] = db["password"]

    return ";".join(f"{k}={v}" for k, v in parts.items())

def get_sqlalchemy_url(*, env_path: Optional[str] = None) -> str:
    """
    Preferred override: PDMS_SQLALCHEMY_URL (complete URL).
    Fallback: build mssql+pyodbc URL from the *outer* config's DB_* variables.
    """
    # If a full URL is provided in env, use it verbatim
    url = os.getenv("PDMS_SQLALCHEMY_URL")
    if url:
        return url

    # Ask the application config to load the .env (external path or auto-discovery)
    cfg, _ = init_runtime(env_path=env_path)

    odbc = _odbc_connect_str_from_cfg(cfg)
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"

# (Optional) Keep the original name around for any legacy callers in your codebase:
def _odbc_connect_str(*, env_path: Optional[str] = None) -> str:
    cfg, _ = init_runtime(env_path=env_path)
    return _odbc_connect_str_from_cfg(cfg)