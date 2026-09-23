"""Tool A — ``query_recent_trade_outcomes`` — DESIGN.md §2.1 RANK #1.

Reads ``knowledge_base/trade_records/{SYMBOL}/*.json`` (A3 v1.1 schema),
filters to filled-and-exited trades within ``days_back``, computes
WR / Exp R / last 5 outcomes / Wilson 95% CI.

This file is the data-fetching helper. Wiring into the AI tool-use API
happens in DESIGN.md §6.1 Phase 1 step 5.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from src.components.ai_tools.base import (
    DAYS_BACK_PROPERTY,
    DIRECTION_PROPERTY,
    LIVE_SYMBOLS,
    SYMBOL_PROPERTY,
    Tool,
)

# Default location — overrideable via constructor for tests (memory:
# project_pytest_contamination_forensics.md — never write to live paths
# from tests without monkeypatching the module-level constant).
DEFAULT_TRADE_RECORDS_ROOT = Path("knowledge_base/trade_records")


def _wilson_ci(wins: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion (no scipy dependency).

    Returns (low, high) clipped to [0, 1].
    """
    if n == 0:
        return (0.0, 1.0)
    z = 1.959963984540054  # 95% two-sided
    p_hat = wins / n
    denom = 1.0 + (z * z) / n
    centre = p_hat + (z * z) / (2 * n)
    spread = z * math.sqrt((p_hat * (1 - p_hat) + (z * z) / (4 * n)) / n)
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (max(0.0, lo), min(1.0, hi))


def _parse_candle_time(meta: dict) -> Optional[datetime]:
    """Extract candle_time from record metadata — UTC-explicit."""
    iso = meta.get("candle_time", "")
    if not iso:
        return None
    try:
        # Handle both naive and Z-suffixed forms.
        norm = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _extract_realized_R(record: dict) -> Optional[float]:
    """Pull realized_R from the A3 v1.1 ``exit`` block.

    A3 v1.1 schema (handoff §"What's shipped and live") writes
    ``record["exit"]["realized_R"]`` for every filled-and-exited trade.
    Returns None for unfilled / open / pending records.
    """
    ex = record.get("exit")
    if not ex:
        return None
    rr = ex.get("realized_R")
    if rr is None:
        return None
    try:
        return float(rr)
    except (TypeError, ValueError):
        return None


def query_recent_trade_outcomes(
    symbol: str,
    days_back: int = 30,
    framework: Optional[str] = None,
    direction: Optional[str] = None,
    *,
    trade_records_root: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Aggregate filled trade outcomes for ``symbol`` over the rolling window.

    *trade_records_root* and *now* are test hooks — pass them in tests to
    avoid live-data contamination and to pin the clock.

    Returns a dict with keys::

        {"symbol": str, "window_days": int, "n_trades": int,
         "win_rate": float | None, "exp_R": float | None,
         "last_5_outcomes": list, "wilson_95ci": [float, float] | None}

    On error returns ``{"error": str, ...context...}``.
    """
    if symbol not in LIVE_SYMBOLS:
        return {"error": "unknown_symbol", "symbol": symbol}
    if not 7 <= days_back <= 90:
        return {"error": "days_back_out_of_range", "days_back": days_back}

    root = trade_records_root or DEFAULT_TRADE_RECORDS_ROOT
    sym_dir = root / symbol
    if not sym_dir.exists():
        return {
            "symbol": symbol,
            "window_days": days_back,
            "n_trades": 0,
            "win_rate": None,
            "exp_R": None,
            "last_5_outcomes": [],
        }

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days_back)
    rows: list[dict] = []
    for fp in sorted(sym_dir.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        meta = d.get("metadata") or {}
        realized_R = _extract_realized_R(d)
        if realized_R is None:
            continue
        candle_dt = _parse_candle_time(meta)
        if candle_dt is None or candle_dt < cutoff:
            continue
        tp = d.get("trade_parameters") or {}
        if direction and tp.get("direction") != direction:
            continue
        ai_resp = d.get("ai_response") or {}
        if framework and ai_resp.get("framework") != framework:
            continue
        rows.append({
            "date": candle_dt.date().isoformat(),
            "R": realized_R,
            "framework": ai_resp.get("framework", "?"),
            "direction": tp.get("direction", "?"),
        })

    n = len(rows)
    if n == 0:
        return {
            "symbol": symbol,
            "window_days": days_back,
            "n_trades": 0,
            "win_rate": None,
            "exp_R": None,
            "last_5_outcomes": [],
        }

    # Sort chronologically (filename sort approximates this; explicit is safer).
    rows.sort(key=lambda r: r["date"])

    wins = sum(1 for r in rows if r["R"] > 0)
    wr = wins / n
    # Per memory project_distributional_findings.md — clip to [-5R, +5R]
    # to prevent fat-tail outliers from dominating expectancy.
    clipped = [max(-5.0, min(5.0, r["R"])) for r in rows]
    exp_R = sum(clipped) / n
    last_5 = rows[-5:]
    lo, hi = _wilson_ci(wins, n)

    return {
        "symbol": symbol,
        "window_days": days_back,
        "n_trades": n,
        "win_rate": round(wr, 3),
        "exp_R": round(exp_R, 3),
        "last_5_outcomes": last_5,
        "wilson_95ci": [round(lo, 3), round(hi, 3)],
    }


class QueryRecentTradeOutcomesTool(Tool):
    """Tool wrapper — DESIGN.md §2.1 Tool A."""

    name = "query_recent_trade_outcomes"
    description = (
        "Query realized R outcomes over a recent rolling window for a "
        "symbol. Use when uncertain about current edge state — e.g., "
        "when a setup looks textbook but recent outcomes have been "
        "unfavorable, or vice versa. Returns n_trades, win_rate, "
        "exp_R, last 5 outcomes, and Wilson 95% CI. Returns "
        "n_trades=0 when no data — handle gracefully."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "symbol": SYMBOL_PROPERTY,
            "days_back": {**DAYS_BACK_PROPERTY, "default": 30},
            "framework": {
                "type": "string",
                "description": "Optional framework filter (e.g., 'ob_retest').",
            },
            "direction": {
                **DIRECTION_PROPERTY,
                "description": "Optional direction filter.",
            },
        },
        "required": ["symbol"],
    }

    def execute(self, **kwargs: Any) -> dict:
        return query_recent_trade_outcomes(
            symbol=kwargs.get("symbol", ""),
            days_back=int(kwargs.get("days_back", 30)),
            framework=kwargs.get("framework"),
            direction=kwargs.get("direction"),
        )


__all__ = [
    "DEFAULT_TRADE_RECORDS_ROOT",
    "QueryRecentTradeOutcomesTool",
    "query_recent_trade_outcomes",
]
