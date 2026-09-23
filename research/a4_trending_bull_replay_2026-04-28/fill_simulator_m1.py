"""A4 Stage 2.5 — M1-based fill simulator (resolves intra-bar ambiguity).

Improvement over fill_simulator.py: walks M1 bars (1-minute resolution) to
resolve order of fill / SL / TP within volatile bars. This matters for cases
like lim_2026-04-16_1316 where the single M15 bar's L=4784.77 is below both
the limit AND the SL — the order in which they were touched determines outcome.

Convention:
- Limit fills the first M1 bar where bar.low <= limit_price (LONG).
- After fill (counted from the fill bar onward), check SL/TP each subsequent
  M1 bar. SL hit if bar.low <= SL; TP hit if bar.high >= TP. If both hit in
  the SAME M1 bar, conservative assumption: SL first (LONG).
- The fill bar itself can ALSO trigger SL/TP if the bar's range crosses both
  the limit and the SL/TP levels.

Caveat: Even M1 has intra-bar ambiguity but it's much smaller than M15.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M1_CSV = REPO / "data" / "historical_2026" / "XAUUSD_M1.csv"
TRADE_RECORDS = REPO / "knowledge_base" / "trade_records" / "XAUUSD"
OUT_DIR = REPO / ".claude" / "worktrees" / "agent-ae5e6ce714eaff374" / "research" / "a4_trending_bull_replay_2026-04-28"


def load_m1():
    """Load M1 candles into a list of dicts (sorted by time)."""
    bars = []
    with open(M1_CSV, encoding="utf-8") as fh:
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


def find_first_bar_after(bars, t: datetime) -> int:
    """First bar with bar.time > t. Returns -1 if none.

    Uses linear scan — fine for this n=4 cohort.
    """
    for i, b in enumerate(bars):
        if b["time"] > t:
            return i
    return -1


def simulate_limit(bars, candle_time: datetime, direction: str, limit: float, sl: float, tp1: float, expiry_minutes: int = 192 * 15):
    """Simulate forward fill + exit on M1 bars."""
    next_idx = find_first_bar_after(bars, candle_time)
    if next_idx == -1:
        return {"outcome": "NO_DATA", "reason": "candle_time after data range"}

    end_scan = min(next_idx + expiry_minutes, len(bars))

    # Fill scan
    fill_idx = -1
    fill_price = None
    for i in range(next_idx, end_scan):
        b = bars[i]
        if direction == "LONG":
            if b["low"] <= limit:
                fill_idx = i
                fill_price = limit
                break
        else:
            if b["high"] >= limit:
                fill_idx = i
                fill_price = limit
                break

    if fill_idx == -1:
        return {
            "outcome": "NEVER_FILLED",
            "realized_r": None,
            "reason": f"limit not touched in {expiry_minutes} M1 bars after placement",
            "expiry_time": bars[end_scan-1]["time"].isoformat() if end_scan > 0 else None,
        }

    risk = abs(fill_price - sl)

    # Exit scan: include fill bar (volatile bar may also hit SL/TP).
    exit_end = min(fill_idx + expiry_minutes, len(bars))
    for i in range(fill_idx, exit_end):
        b = bars[i]
        sl_hit = (direction == "LONG" and b["low"] <= sl) or (direction == "SHORT" and b["high"] >= sl)
        tp_hit = (direction == "LONG" and b["high"] >= tp1) or (direction == "SHORT" and b["low"] <= tp1)
        if sl_hit and tp_hit:
            # M1 ambiguity — much smaller than M15 but still non-zero
            return {
                "outcome": "FILLED_LOSS",
                "realized_r": -1.0,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": sl,
                "exit_reason": "sl_hit (M1 ambiguous bar — SL assumed first)",
                "intra_m1_ambiguity": True,
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
            r = abs(tp1 - fill_price) / risk if risk > 0 else 0.0
            return {
                "outcome": "FILLED_WIN",
                "realized_r": r,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": tp1,
                "exit_reason": "tp1_hit",
            }

    last_bar = bars[exit_end - 1]
    final_close = last_bar["close"]
    pnl = (final_close - fill_price) if direction == "LONG" else (fill_price - final_close)
    r = pnl / risk if risk > 0 else 0.0
    return {
        "outcome": "FILLED_TIME_EXPIRY",
        "realized_r": r,
        "fill_time": bars[fill_idx]["time"].isoformat(),
        "fill_price": fill_price,
        "exit_time": last_bar["time"].isoformat(),
        "exit_price": final_close,
        "exit_reason": f"expiry_at_{expiry_minutes}_minutes",
    }


def main():
    print(f"Loading M1 from {M1_CSV}")
    bars = load_m1()
    print(f"  loaded {len(bars)} bars, range {bars[0]['time']} -> {bars[-1]['time']}\n")

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
            li.get("expiry_candles", 192) * 15,  # 192 M15 candles -> 192*15 M1 candles
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

    out_path = OUT_DIR / "fill_simulation_m1_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
