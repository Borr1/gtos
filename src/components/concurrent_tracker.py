"""Legacy cross-symbol filled-position counter and concurrent-cap helper.

Introduced in T2.8 — concurrent-cap + daily-loss-stop risk architecture
(session 33, redacted_account kickoff 2026-04-21). Replaces the ad-hoc
``max_kz_trades=1`` + ``max_daily_losses=2`` guards with a principled
legacy portfolio-risk formula for non-vNext surfaces:

    max_concurrent = floor(max_daily_loss_pct / risk_per_trade_pct)

This module is not the FTMO dual-broker follower authority. The follower uses
account-specific aggregate drawdown budget, open stop-loss exposure, pending
risk, and prop-firm drawdown rules. Minimum of 1 remains here so no legacy
profile config can accidentally block all trading.

Current vNext contract:
  - "Concurrent" counts FILLED positions only. Pending limits do not count.
    (Locked decision #3 — pending limits cancel cheaply on trigger.)
  - Same-symbol vNext exposure is governed by the explicit lifecycle conflict
    gate in permissions.py. This module is only a cross-symbol filled-position
    cap for legacy or non-vNext paths.

Cross-symbol query pattern mirrors ``src/safety/heartbeat_monitor.py``
(the only other place that iterates ``mt5.positions_get()`` with no symbol
filter). We never touch ``MT5Interface.get_positions(symbol)`` here — that
call path is per-symbol by design.

A 10-second TTL cache avoids a per-evaluation MT5 round-trip. Every
CANDIDATE evaluation pings this module; the live trading loop runs at
M15 cadence, so a 10s window is tight enough that a fresh fill from
another process is almost always visible before the next check.

The module is stateless from a process perspective — the cache lives as
a module-level mutable, deliberately. Tests clear it via ``reset_cache()``.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any

from src.mt5.mt5_interface import MAGIC_NUMBER

logger = logging.getLogger(__name__)


# Default TTL — picked small enough that stale values don't mask a fresh
# concurrent fill from another symbol's orchestrator, large enough that
# per-evaluation MT5 round-trips (one per CANDIDATE) don't accumulate.
DEFAULT_CACHE_TTL_SECONDS = 10.0


_cache: dict[str, Any] = {"value": None, "ts": 0.0}


def reset_cache() -> None:
    """Clear the TTL cache. Tests must call this in a fixture."""
    _cache["value"] = None
    _cache["ts"] = 0.0


def _resolve_mt5_module(mt5) -> Any | None:
    """Find the raw MetaTrader5 module on an MT5 wrapper (RealMT5 / MockMT5).

    - ``RealMT5`` stashes it as ``self._mt5`` after ``connect()`` — that's the
      object with ``positions_get()`` returning MT5-native tuples.
    - ``MockMT5`` has no raw module; callers should use the fallback path
      that reads ``MockMT5._positions`` directly so tests can still exercise
      the gate.
    - Any other object that exposes a top-level ``positions_get`` attribute
      (e.g. a test double) is treated as the module itself.

    Returns ``None`` when no cross-symbol positions query is available.
    """
    if mt5 is None:
        return None
    # RealMT5 — has a connected MetaTrader5 module stashed.
    inner = getattr(mt5, "_mt5", None)
    if inner is not None and hasattr(inner, "positions_get"):
        return inner
    # Test double / explicit module.
    if hasattr(mt5, "positions_get"):
        return mt5
    return None


def _count_via_raw_module(mt5_module: Any) -> int:
    """Count filled positions via ``positions_get()`` filtered by MAGIC_NUMBER.

    Mirrors ``src.safety.heartbeat_monitor.flatten_open_positions`` pattern.
    Returns 0 on any exception — a concurrent-cap gate must fail OPEN (let
    the trade through) rather than fail CLOSED on a transient MT5 glitch,
    because the gate is an additive cap, not a safety primitive. Daily
    loss stop + H29 DD reduction remain authoritative.
    """
    try:
        positions = mt5_module.positions_get() or []
    except Exception as e:  # noqa: BLE001 — fail-open on MT5 error
        logger.warning(
            "concurrent_tracker: positions_get failed, failing open (count=0): %s", e,
        )
        return 0
    count = 0
    for p in positions:
        magic = getattr(p, "magic", None)
        if magic == MAGIC_NUMBER:
            count += 1
    return count


def _count_via_mock(mt5) -> int:
    """Count via ``MockMT5._positions`` when the raw module isn't available.

    MockMT5's public ``get_positions(symbol)`` is per-symbol filtered,
    which would miss cross-symbol holdings in tests. Iterating the
    private ``_positions`` list preserves the cross-symbol semantics of
    the production path.
    """
    positions = getattr(mt5, "_positions", None)
    if positions is None:
        return 0
    count = 0
    for p in positions:
        if getattr(p, "magic", None) == MAGIC_NUMBER:
            count += 1
    return count


def get_filled_position_count(mt5, *, ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS,
                              now: float | None = None) -> int:
    """Return the total filled GTOS position count across all symbols.

    Cached for ``ttl_seconds`` so per-evaluation calls don't spam MT5.
    Tests can pass ``now`` to pin the clock.
    """
    current_ts = time.monotonic() if now is None else now
    if (_cache["value"] is not None
            and (current_ts - _cache["ts"]) < ttl_seconds):
        return int(_cache["value"])

    raw = _resolve_mt5_module(mt5)
    if raw is not None:
        count = _count_via_raw_module(raw)
    else:
        count = _count_via_mock(mt5)
    _cache["value"] = count
    _cache["ts"] = current_ts
    return count


def compute_max_concurrent(risk_per_trade_pct: float,
                           max_daily_loss_pct: float) -> int:
    """Concurrent-cap formula: floor(max_daily_loss_pct / risk_per_trade_pct).

    Bounded below at 1 so a misconfigured profile cannot accidentally
    halt all trading. Bounded above only by input hygiene.

    Returns 1 when ``risk_per_trade_pct`` is non-positive (fail-open to
    the safest meaningful cap).
    """
    try:
        risk = float(risk_per_trade_pct)
        loss = float(max_daily_loss_pct)
    except (TypeError, ValueError):
        return 1
    if risk <= 0 or loss <= 0:
        return 1
    raw = math.floor(loss / risk)
    if raw < 1:
        return 1
    return int(raw)


def resolve_max_concurrent(config: dict | None) -> int:
    """Return the effective concurrent cap from config.

    Precedence:
      1. ``risk.max_concurrent`` (explicit pin in profile overlay)
      2. ``floor(risk.max_daily_loss_pct / risk.risk_per_trade_pct)``
    """
    risk_cfg = (config or {}).get("risk", {}) or {}
    pinned = risk_cfg.get("max_concurrent")
    if isinstance(pinned, int) and not isinstance(pinned, bool) and pinned >= 1:
        return int(pinned)
    return compute_max_concurrent(
        risk_cfg.get("risk_per_trade_pct", 2.0),
        risk_cfg.get("max_daily_loss_pct", 4.0),
    )
