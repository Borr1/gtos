"""Broker/profile runtime identity helpers.

These helpers are deliberately default-off. Existing redacted_account launches that
do not set a runtime namespace or expected account contract keep their current
paths and MT5 initialization behavior.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any


TERMINAL_PATH_ENV_VAR = "GTOS_MT5_TERMINAL_PATH"
TERMINAL_PORTABLE_ENV_VAR = "GTOS_MT5_PORTABLE"
RUNTIME_NAMESPACE_ENV_VAR = "GTOS_RUNTIME_NAMESPACE"


def sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def sanitize_namespace(value: Any, *, fallback: str = "") -> str:
    raw = str(value or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return cleaned or fallback


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def broker_account_namespace(config: dict[str, Any] | None, explicit: str | None = None) -> str:
    """Return the broker/account runtime namespace for *config*.

    Precedence is explicit CLI value, env var, profile runtime block, legacy
    top-level fields, then empty string. Empty means "use legacy un-namespaced
    paths" for backward compatibility.
    """
    if explicit:
        return sanitize_namespace(explicit)

    env_namespace = os.environ.get(RUNTIME_NAMESPACE_ENV_VAR, "").strip()
    if env_namespace:
        return sanitize_namespace(env_namespace)

    cfg = config or {}
    runtime = cfg.get("runtime") if isinstance(cfg.get("runtime"), dict) else {}
    vnext_runtime = (
        cfg.get("gtos_vnext_runtime") if isinstance(cfg.get("gtos_vnext_runtime"), dict) else {}
    )
    broker_profile = (
        cfg.get("broker_profile") if isinstance(cfg.get("broker_profile"), dict) else {}
    )
    candidates = (
        runtime.get("broker_account_namespace"),
        runtime.get("profile_namespace"),
        runtime.get("runtime_namespace"),
        vnext_runtime.get("broker_account_namespace"),
        vnext_runtime.get("runtime_namespace"),
        vnext_runtime.get("profile_namespace"),
        broker_profile.get("broker_account_namespace"),
        cfg.get("broker_account_namespace"),
        cfg.get("profile_namespace"),
    )
    for candidate in candidates:
        if candidate:
            return sanitize_namespace(candidate)
    return ""


def namespaced_daemon_name(base_name: str, namespace: str | None) -> str:
    ns = sanitize_namespace(namespace)
    return f"{base_name}_{ns}" if ns else base_name


def namespaced_file_path(path: str | Path, namespace: str | None) -> Path:
    """Append *namespace* to a filename stem while preserving its directory."""
    p = Path(path)
    ns = sanitize_namespace(namespace)
    if not ns:
        return p
    return p.with_name(f"{p.stem}_{ns}{p.suffix}")


def namespaced_directory_path(path: str | Path, namespace: str | None) -> Path:
    """Place a namespace directory under *path* when namespace is set."""
    p = Path(path)
    ns = sanitize_namespace(namespace)
    return p / ns if ns else p


def resolve_mt5_terminal_path(
    config: dict[str, Any] | None = None,
    explicit: str | None = None,
) -> str | None:
    """Resolve the MT5 terminal executable path.

    Precedence: explicit CLI argument, ``GTOS_MT5_TERMINAL_PATH``, then profile
    config blocks. ``None`` preserves MT5 package default terminal discovery.
    """
    if explicit:
        return explicit

    env_path = os.environ.get(TERMINAL_PATH_ENV_VAR, "").strip()
    if env_path:
        return env_path

    cfg = config or {}
    mt5_cfg = cfg.get("mt5") if isinstance(cfg.get("mt5"), dict) else {}
    broker_profile = (
        cfg.get("broker_profile") if isinstance(cfg.get("broker_profile"), dict) else {}
    )
    for candidate in (
        mt5_cfg.get("terminal_path"),
        broker_profile.get("terminal_path"),
        cfg.get("terminal_path"),
    ):
        if candidate:
            return str(candidate)
    return None


def resolve_mt5_portable_mode(
    config: dict[str, Any] | None = None,
    explicit: bool | None = None,
) -> bool:
    """Resolve whether MT5 should initialize in portable mode."""
    if explicit is not None:
        return bool(explicit)

    env_value = os.environ.get(TERMINAL_PORTABLE_ENV_VAR)
    if env_value is not None:
        return truthy(env_value)

    cfg = config or {}
    mt5_cfg = cfg.get("mt5") if isinstance(cfg.get("mt5"), dict) else {}
    broker_profile = (
        cfg.get("broker_profile") if isinstance(cfg.get("broker_profile"), dict) else {}
    )
    for candidate in (
        mt5_cfg.get("portable"),
        broker_profile.get("portable_terminal"),
        cfg.get("mt5_portable"),
    ):
        if candidate is not None:
            return truthy(candidate)
    return False


def _snapshot(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "_asdict"):
        try:
            return dict(value._asdict())
        except Exception:  # noqa: BLE001 - best-effort snapshot for assertions
            return {}
    if hasattr(value, "_fields"):
        return {field: getattr(value, field, None) for field in value._fields}
    if isinstance(value, dict):
        return dict(value)
    return {
        key: item
        for key, item in vars(value).items()
        if not str(key).startswith("_")
    } if hasattr(value, "__dict__") else {}


def expected_account_contract(config: dict[str, Any] | None) -> dict[str, Any]:
    cfg = config or {}
    broker_profile = (
        cfg.get("broker_profile") if isinstance(cfg.get("broker_profile"), dict) else {}
    )
    expected = broker_profile.get("expected_account")
    return dict(expected) if isinstance(expected, dict) else {}


def assert_mt5_account_matches_profile(mt5_wrapper: Any, config: dict[str, Any] | None) -> dict[str, Any]:
    """Fail fast when the connected MT5 account contradicts profile identity.

    The check is read-only. It inspects ``terminal_info`` and ``account_info``
    from the already-initialized MT5 module stashed by ``RealMT5``. Profiles
    without ``broker_profile.expected_account`` return ``not_configured``.
    """
    expected = expected_account_contract(config)
    if not expected:
        return {"status": "not_configured", "checked": False}

    mt5_module = getattr(mt5_wrapper, "_mt5", None)
    if mt5_module is None:
        raise RuntimeError("MT5 account assertion configured but raw MT5 module is unavailable")

    terminal = _snapshot(mt5_module.terminal_info())
    account = _snapshot(mt5_module.account_info())
    if not account:
        raise RuntimeError("MT5 account assertion configured but account_info() returned no data")

    actual = {
        "server": account.get("server"),
        "company": account.get("company"),
        "currency": account.get("currency"),
        "login_sha256": sha256_text(account.get("login")) if account.get("login") else None,
        "terminal_path": terminal.get("path"),
        "terminal_data_path": terminal.get("data_path"),
    }
    comparisons = {
        "server": (expected.get("server"), actual["server"]),
        "company": (expected.get("company"), actual["company"]),
        "currency": (expected.get("currency"), actual["currency"]),
        "login_sha256": (expected.get("login_sha256"), actual["login_sha256"]),
        "terminal_path": (expected.get("terminal_path"), actual["terminal_path"]),
        "terminal_data_path": (expected.get("terminal_data_path"), actual["terminal_data_path"]),
    }
    mismatches: dict[str, dict[str, Any]] = {}
    for field, (want, got) in comparisons.items():
        if want in (None, ""):
            continue
        if str(want) != str(got):
            mismatches[field] = {"expected": want, "actual": got}

    if mismatches:
        raise RuntimeError(f"MT5 account/profile mismatch: {mismatches}")

    return {
        "status": "passed",
        "checked": True,
        "fields_checked": sorted(
            field for field, (want, _got) in comparisons.items() if want not in (None, "")
        ),
        "actual_redacted": actual,
    }
