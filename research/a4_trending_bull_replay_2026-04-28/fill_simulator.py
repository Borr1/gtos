"""A4 Stage 2.5 — fill simulator for LIMIT_PLACED cohort records.

For each LIMIT_PLACED trade in the A4 cohort, simulate forward fill against
the M15 historical CSV (data/historical_2026/XAUUSD_M15.csv) using the
limit_intent metadata stored in the trade_records JSON.

Convention (standard SMC/SMT backtest):
- LONG limit fills when M15 bar low <= limit_price (we use the FIRST bar where
  this is true at or after the candle_time).
- After fill: track each subsequent M15 bar.
  - If bar low <= SL → SL hit, R = -1.0 (LOSS)
  - Else if bar high >= TP1 → TP1 hit, R = (TP1-entry)/(entry-SL) (WIN)
  - If both touched in same bar → assume SL first (conservative for LONGs)
- Limit expires after `expiry_candles` (default 192 M15 = 48h) if not filled.
- Trade expires at expiry_candles after fill if neither SL nor TP hit; mark
  outcome based on close-at-expiry R.

This script is read-only and produces a JSON report next to itself.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M15_CSV = REPO / "data" / "historical_2026" / "XAUUSD_M15.csv"
TRADE_RECORDS = REPO / "knowledge_base" / "trade_records" / "XAUUSD"
COHORT_MANIFEST = REPO / ".claude" / "worktrees" / "agent-a3b7a108632e7293d" / "research" / "a4_trending_bull_replay_2026-04-28" / "a4_cohort_manifest.csv"
OUT_DIR = REPO / ".claude" / "worktrees" / "agent-ae5e6ce714eaff374" / "research" / "a4_trending_bull_replay_2026-04-28"


def load_m15():
    """Load M15 candles into a list of dicts (sorted by time)."""
    bars = []
    with open(M15_CSV, encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            t = datetime.fromisoformat(row["time"]).replace(tzinfo=timezone.utc)
            bars.append({
                "time": t,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    bars.sort(key=lambda b: b["time"])
    return bars


def find_first_bar_at_or_after(bars, t: datetime) -> int:
    """Return index of first bar with bar.time >= t. Returns -1 if none."""
    for i, b in enumerate(bars):
        if b["time"] >= t:
            return i
    return -1


def simulate_limit(bars, candle_time: datetime, direction: str, limit: float, sl: float, tp1: float, expiry_candles: int = 192):
    """Simulate forward fill + exit on M15 bars.

    Returns dict with keys: outcome (FILLED_WIN/FILLED_LOSS/FILLED_TIME_EXPIRY/NEVER_FILLED),
    realized_r (float or None), fill_time, fill_price, exit_time, exit_price, exit_reason.
    """
    # Locate the first bar AFTER the candle_time (the LIMIT_PLACED candle is the
    # candle that just closed; the limit becomes active on the next bar).
    start_idx = find_first_bar_at_or_after(bars, candle_time)
    if start_idx == -1:
        return {"outcome": "NO_DATA", "reason": "candle_time after available data"}

    # Use start_idx + 1 for "next bar" since we treat candle_time as the close
    # of the LIMIT_PLACED bar. But we want the bar the candle_time falls in,
    # so look for first bar with time > candle_time.
    next_bar_idx = -1
    for i in range(start_idx, len(bars)):
        if bars[i]["time"] > candle_time:
            next_bar_idx = i
            break
    if next_bar_idx == -1:
        return {"outcome": "NO_DATA", "reason": "no bars after candle_time"}

    # Fill scan: limit lives for `expiry_candles` bars from placement.
    fill_idx = -1
    fill_price = None
    end_scan = min(next_bar_idx + expiry_candles, len(bars))
    for i in range(next_bar_idx, end_scan):
        b = bars[i]
        if direction == "LONG":
            if b["low"] <= limit:
                fill_idx = i
                # Conservative fill: assume fill at limit price (no slippage in sim)
                fill_price = limit
                break
        else:  # SHORT
            if b["high"] >= limit:
                fill_idx = i
                fill_price = limit
                break

    if fill_idx == -1:
        return {
            "outcome": "NEVER_FILLED",
            "realized_r": None,
            "reason": f"limit not touched in {expiry_candles} M15 candles after placement",
            "expiry_time": bars[end_scan-1]["time"].isoformat() if end_scan > 0 else None,
        }

    # Track exit. Trade expires expiry_candles AFTER fill (using same expiry window).
    risk = abs(fill_price - sl)
    reward = abs(tp1 - fill_price)

    # The fill bar itself can also trigger SL or TP — this matters for high-volatility
    # bars (e.g. lim_2026-04-16_1316 where the 16:45 bar's low=4784.77 is below both
    # the limit 4796.28 AND the SL 4786.65). We start from fill_idx (inclusive) and
    # treat the fill bar's high/low as post-fill price action.
    exit_end = min(fill_idx + 1 + expiry_candles, len(bars))
    for i in range(fill_idx, exit_end):
        b = bars[i]
        sl_hit = (direction == "LONG" and b["low"] <= sl) or (direction == "SHORT" and b["high"] >= sl)
        tp_hit = (direction == "LONG" and b["high"] >= tp1) or (direction == "SHORT" and b["low"] <= tp1)
        if sl_hit and tp_hit:
            # Conservative: SL first
            return {
                "outcome": "FILLED_LOSS",
                "realized_r": -1.0,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": sl,
                "exit_reason": "sl_hit (ambiguous bar — SL assumed first)",
            }
        if sl_hit:
            return {
                "outcome": "FILLED_LOSS",
                "realized_r": -1.0,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": sl,
                "exit_reason": "sl_hit",
            }
        if tp_hit:
            r = reward / risk if risk > 0 else 0.0
            return {
                "outcome": "FILLED_WIN",
                "realized_r": r,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": tp1,
                "exit_reason": "tp1_hit",
            }

    # Time expiry
    last_bar = bars[exit_end - 1]
    final_close = last_bar["close"]
    if direction == "LONG":
        pnl = final_close - fill_price
    else:
        pnl = fill_price - final_close
    r = pnl / risk if risk > 0 else 0.0
    return {
        "outcome": "FILLED_TIME_EXPIRY",
        "realized_r": r,
        "fill_time": bars[fill_idx]["time"].isoformat(),
        "fill_price": fill_price,
        "exit_time": last_bar["time"].isoformat(),
        "exit_price": final_close,
        "exit_reason": f"expiry_at_{expiry_candles}_bars",
    }


def main():
    print(f"Loading M15 from {M15_CSV}")
    bars = load_m15()
    print(f"  loaded {len(bars)} bars, range {bars[0]['time']} -> {bars[-1]['time']}\n")

    # The 4 LIMIT_PLACED records (per cohort manifest grep).
    limit_placed_records = [
        "2026-04-15_ny_1415",
        "2026-04-16_london_0930",
        "2026-04-16_ny_1316",
        "2026-04-17_ny_1330",
    ]

    results = {}
    for tid in limit_placed_records:
        rec_path = TRADE_RECORDS / f"{tid}.json"
        with open(rec_path, encoding="utf-8") as fh:
            data = json.load(fh)
        li = data["limit_intent"]
        tp = data["trade_parameters"]
        candle_time = datetime.fromisoformat(data["metadata"]["candle_time"])
        direction = tp["direction"]
        result = simulate_limit(
            bars,
            candle_time,
            direction,
            li["limit_price"],
            li["stop_loss"],
            li["take_profit_1"],
            li.get("expiry_candles", 192),
        )
        result["trade_id"] = tid
        result["candle_time"] = candle_time.isoformat()
        result["limit_price"] = li["limit_price"]
        result["stop_loss"] = li["stop_loss"]
        result["take_profit_1"] = li["take_profit_1"]
        result["direction"] = direction
        results[tid] = result
        print(f"{tid}:")
        print(f"  candle_time={candle_time}")
        print(f"  limit={li['limit_price']}  SL={li['stop_loss']}  TP1={li['take_profit_1']}  dir={direction}")
        print(f"  -> outcome={result['outcome']}  realized_r={result.get('realized_r')}")
        if "fill_time" in result:
            print(f"  -> fill_time={result['fill_time']}@{result['fill_price']}  exit_time={result.get('exit_time')}@{result.get('exit_price')}  reason={result.get('exit_reason')}")
        print()

    out_path = OUT_DIR / "fill_simulation_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
