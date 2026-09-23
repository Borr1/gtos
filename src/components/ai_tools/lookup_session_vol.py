"""Tool B — ``lookup_session_volatility`` — DESIGN.md §2.1 RANK #2.

Reads a pre-computed cache of (symbol, session) -> 30d ATR distribution
and compares it to the *current* session ATR. Returns a regime label
(low_vol / normal / high_vol / extreme).

This file is a SKELETON. Implementation hooks::

  - ``_compute_current_session_atr`` is a placeholder; the real
    implementation must mirror ``market_state.py`` lines 1057-1191
    (currently XAUUSD-M15-only ``atr_session`` calculation) generalized
    to the Stage08 broker-native vNext symbol surface and configured
    production sessions.

  - ``DEFAULT_VOL_CACHE_PATH`` points to a JSON file written by a weekly
    cron job (NOT YET IMPLEMENTED — DESIGN.md §6.1 Phase 1 step 4).
    Schema: ``{"<symbol>|<session>": {"daily_atrs": [...], "median": ...,
    "p25": ..., "p75": ...}}``

Phase 1 implementation agent: replace the placeholders, add the cron
script, write tests against synthetic cache fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from src.components.ai_tools.base import LIVE_SYMBOLS, SYMBOL_PROPERTY, Tool

DEFAULT_VOL_CACHE_PATH = Path("knowledge_base/ai_tools_cache/session_vol_30d.json")
VALID_SESSIONS = ("london", "ny", "tokyo", "asia")


def _compute_current_session_atr(symbol: str, session: str) -> Optional[float]:
    """Placeholder — return current-session ATR-14.

    PHASE 1 IMPLEMENTATION agent: implement by reading recent M15
    candles for the active session window and computing ATR-14. See
    ``market_state.py:1057-1191`` for the XAUUSD reference pattern.
    """
    # Skeleton returns None until implemented.
    return None


def _load_vol_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _classify_regime(percentile: float) -> str:
    if percentile < 0.20:
        return "low_vol"
    if percentile < 0.80:
        return "normal"
    if percentile < 0.95:
        return "high_vol"
    return "extreme"


def lookup_session_volatility(
    symbol: str,
    session: str,
    lookback_days: int = 30,
    *,
    cache_path: Optional[Path] = None,
    atr_now_override: Optional[float] = None,
) -> dict:
    """Return the (symbol, session) volatility regime.

    *cache_path* and *atr_now_override* are test hooks — pass them in
    tests so we don't depend on live-MT5 connectivity or the production
    cache file.
    """
    if symbol not in LIVE_SYMBOLS:
        return {"error": "unknown_symbol", "symbol": symbol}
    if session not in VALID_SESSIONS:
        return {"error": "unknown_session", "session": session}
    if not 7 <= lookback_days <= 90:
        return {"error": "lookback_out_of_range", "lookback_days": lookback_days}

    cache = _load_vol_cache(cache_path or DEFAULT_VOL_CACHE_PATH)
    key = f"{symbol}|{session}"
    snapshot = cache.get(key, {})

    atr_now = atr_now_override
    if atr_now is None:
        atr_now = _compute_current_session_atr(symbol, session)

    samples = snapshot.get("daily_atrs", [])

    if not samples or atr_now is None:
        return {
            "symbol": symbol,
            "session": session,
            "atr_now": atr_now,
            "atr_30d_median": snapshot.get("median"),
            "atr_30d_p25": snapshot.get("p25"),
            "atr_30d_p75": snapshot.get("p75"),
            "percentile_today": None,
            "regime": "unknown",
            "n_session_samples": len(samples),
        }

    # Empirical percentile rank.
    rank = sum(1 for x in samples if x <= atr_now)
    pct = rank / len(samples)
    regime = _classify_regime(pct)

    return {
        "symbol": symbol,
        "session": session,
        "atr_now": round(atr_now, 4),
        "atr_30d_median": round(snapshot["median"], 4),
        "atr_30d_p25": round(snapshot["p25"], 4),
        "atr_30d_p75": round(snapshot["p75"], 4),
        "percentile_today": round(pct, 2),
        "regime": regime,
        "n_session_samples": len(samples),
    }


class LookupSessionVolatilityTool(Tool):
    """Tool wrapper — DESIGN.md §2.1 Tool B."""

    name = "lookup_session_volatility"
    description = (
        "Look up the current session's ATR-14 vs the rolling 30-day "
        "distribution for that (symbol, session) bucket. Use when the "
        "setup hinges on impulse strength — e.g., London-OB framework "
        "in low-vol conditions may produce shallow impulses that fail "
        "to reach TP1. Returns regime label (low_vol/normal/high_vol/"
        "extreme) and percentile."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "symbol": SYMBOL_PROPERTY,
            "session": {
                "type": "string",
                "enum": list(VALID_SESSIONS),
                "description": "Trading session.",
            },
            "lookback_days": {
                "type": "integer",
                "minimum": 7,
                "maximum": 90,
                "default": 30,
            },
        },
        "required": ["symbol", "session"],
    }

    def execute(self, **kwargs: Any) -> dict:
        return lookup_session_volatility(
            symbol=kwargs.get("symbol", ""),
            session=kwargs.get("session", ""),
            lookback_days=int(kwargs.get("lookback_days", 30)),
        )


__all__ = [
    "DEFAULT_VOL_CACHE_PATH",
    "LookupSessionVolatilityTool",
    "VALID_SESSIONS",
    "lookup_session_volatility",
]
