"""Config loading and multi-instrument merge utility."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

from src.components.gtos_vnext_runtime import (
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)

PROFILES_DIR = Path(__file__).resolve().parents[2] / "config" / "profiles"
PROFILE_ENV_VAR = "GTOS_PROFILE"

VNEXT_FAMILY_TO_INSTRUMENT_CONFIG_KEYS: dict[str, tuple[str, ...]] = {
    "AUDJPY_FAMILY": ("AUDJPY",),
    "AUDUSD_FAMILY": ("AUDUSD",),
    "BTCUSD_FAMILY": ("BTCUSD",),
    "CADJPY_FAMILY": ("CADJPY",),
    "CHFJPY_FAMILY": ("CHFJPY",),
    "ETHUSD_FAMILY": ("ETHUSD",),
    "EURGBP_FAMILY": ("EURGBP",),
    "EURJPY_FAMILY": ("EURJPY",),
    "EURUSD_6E_FAMILY": ("EURUSD",),
    "GBPUSD_6B_FAMILY": ("GBPUSD",),
    "GER40_FAMILY": ("GER40_cash", "GER40"),
    "JP225_FAMILY": ("JP225_cash", "JP225"),
    "NAS100_NQ_FAMILY": ("US100_cash", "NAS100"),
    "NZDJPY_FAMILY": ("NZDJPY",),
    "NZDUSD_FAMILY": ("NZDUSD",),
    "SPX500_ES_FAMILY": ("US500_cash", "SPX500", "US500"),
    "UK100_FAMILY": ("UK100",),
    "UKOIL_FAMILY": ("UKOIL_cash",),
    "US30_YM_FAMILY": ("US30_cash", "US30"),
    "USDCAD_FAMILY": ("USDCAD",),
    "USDCHF_FAMILY": ("USDCHF",),
    "USDJPY_6J_FAMILY": ("USDJPY",),
    "USOIL_FAMILY": ("USOIL_cash",),
    "XAGUSD_SILVER_FAMILY": ("XAGUSD",),
    "XAUUSD_GC_FAMILY": ("XAUUSD",),
}


def deep_merge(base: dict, override: dict) -> dict:
    """Deep-merge *override* into a copy of *base*.

    Nested dicts are recursively merged. All other values in *override*
    replace the corresponding value in *base*.  Keys present in *base*
    but absent in *override* are preserved unchanged.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def resolve_instrument_config_key(config: dict, symbol: str | None = None) -> str | None:
    """Return the instrument override key for a raw broker/source symbol."""
    if symbol is None:
        return None

    instruments = config.get("instruments", {}) if isinstance(config, dict) else {}
    if not isinstance(instruments, dict):
        return None

    raw = str(symbol).strip()
    if not raw:
        return None
    if raw in instruments:
        return raw

    normalized_key = normalize_vnext_symbol_key(raw)
    if normalized_key in instruments:
        return normalized_key

    family = resolve_vnext_symbol_family(raw)
    for candidate in VNEXT_FAMILY_TO_INSTRUMENT_CONFIG_KEYS.get(family, ()):
        if candidate in instruments:
            return candidate

    return None


def apply_instrument_overrides(config: dict, symbol: str | None = None) -> dict:
    """Return *config* with instrument-specific overrides applied.

    If *symbol* is ``None`` or matches the base config symbol, return
    the config unchanged.  Otherwise deep-merge the matching key from
    ``config['instruments']`` over the base values.

    The ``instruments`` section itself is removed from the returned
    config so downstream code only sees flat values.
    """
    base_symbol = config.get("market", {}).get("symbol", "XAUUSD")
    instruments = config.get("instruments", {})

    if symbol is None:
        result = copy.deepcopy(config)
        result.pop("instruments", None)
        return result

    resolved_symbol = resolve_instrument_config_key(config, symbol)
    overrides = instruments.get(resolved_symbol) if resolved_symbol else None
    if overrides is None:
        if symbol == base_symbol:
            # No overrides for base symbol — return as-is
            result = copy.deepcopy(config)
            result.pop("instruments", None)
            return result
        raise ValueError(
            f"No instrument config for '{symbol}'. "
            f"Available: {list(instruments.keys())}"
        )

    merged = deep_merge(config, overrides)
    override_market = overrides.get("market") if isinstance(overrides, dict) else None
    override_kill_zones = (
        override_market.get("kill_zones")
        if isinstance(override_market, dict)
        else None
    )
    if isinstance(override_kill_zones, dict):
        # Instrument schedules are complete contracts, not additive overlays.
        # Deep-merging here leaked base-only pseudo sessions such as
        # off_configured_session/missing_session into every live orchestrator.
        merged.setdefault("market", {})["kill_zones"] = copy.deepcopy(override_kill_zones)
    merged["market"]["symbol"] = resolved_symbol
    if symbol != resolved_symbol:
        merged["market"]["requested_symbol"] = symbol
        family = resolve_vnext_symbol_family(symbol)
        if family:
            merged["market"]["symbol_family"] = family
    merged.pop("instruments", None)
    return merged


def resolve_profile(explicit: str | None = None) -> str | None:
    """Return the active profile name.

    Precedence: explicit arg > GTOS_PROFILE env var > None.
    A ``None`` return means "no profile; use base config unchanged" —
    preserves exact backward compatibility for processes that don't opt in.
    """
    if explicit:
        return explicit.strip() or None
    env_val = os.environ.get(PROFILE_ENV_VAR, "").strip()
    return env_val or None


def apply_profile_overrides(config: dict, profile: str | None) -> dict:
    """Deep-merge the profile overlay on top of *config*.

    If *profile* is ``None``/empty, return *config* unchanged (no overlay).
    Profile files live in ``config/profiles/{profile}.yaml`` and should list
    only the keys that differ from the base — typically ``risk`` and
    ``drawdown_reduction`` for prop-firm risk budgets.
    """
    if not profile:
        return config

    profile_path = PROFILES_DIR / f"{profile}.yaml"
    if not profile_path.exists():
        available = sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))
        raise ValueError(
            f"Unknown profile '{profile}'. Profile file not found at "
            f"{profile_path}. Available: {available}"
        )

    with open(profile_path, encoding="utf-8") as f:
        overlay = yaml.safe_load(f) or {}

    return deep_merge(config, overlay)
