"""
Algorithmic audit of market_state.py functions on raw 2026 data, across 7 instruments.

For each instrument/TF we compute:
  - swings
  - structure direction
  - BOS/CHoCH events
  - order blocks (counts, mitigated rate, touch distribution)
  - FVGs (fill rate)

Then we spot-check:
  1. Do the counts look reasonable vs bar count? (OB per 100 bars ratio)
  2. Is the structure label consistent with 20-bar close trajectory?
  3. For an OB near current price — does the human-readable chart confirm it?

OUTPUT: CSV summary + sample detailed dumps.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(ROOT))

from src.components.market_state import (
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    identify_breaker_blocks,
    identify_fvgs,
    calculate_atr,
)


def load_tf(symbol: str, tf: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{symbol}_{tf}.csv"
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["time"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            })
    return rows


def summarize(symbol: str, tf: str, candles: list[dict], min_bars: int, fvg_min_gap: float) -> dict:
    swings = detect_swings(candles, min_bars=min_bars)
    structure = identify_structure(swings)
    events = detect_structure_breaks(candles, swings, structure)
    obs = identify_order_blocks(candles, events)
    breakers = identify_breaker_blocks(candles, obs)
    fvgs = identify_fvgs(candles, min_gap_size=fvg_min_gap)
    atr = calculate_atr(candles, period=14)
    last_close = candles[-1]["close"] if candles else 0.0

    unmit_obs = [o for o in obs if not o.mitigated]
    # distance from last_close to nearest unmit OB
    gaps = []
    for o in unmit_obs:
        dist = min(abs(last_close - o.high), abs(last_close - o.low))
        gaps.append(dist)
    nearest_gap = min(gaps) if gaps else None

    filled_fvgs = sum(1 for f in fvgs if f.filled)
    return {
        "symbol": symbol,
        "tf": tf,
        "n_bars": len(candles),
        "n_swings": len(swings),
        "structure": structure.direction,
        "n_events": len(events),
        "n_bos": sum(1 for e in events if e.type == "BOS"),
        "n_choch": sum(1 for e in events if e.type == "CHoCH"),
        "n_obs_total": len(obs),
        "n_obs_unmit": len(unmit_obs),
        "n_breakers": len(breakers),
        "n_fvgs": len(fvgs),
        "pct_fvgs_filled": round(100 * filled_fvgs / len(fvgs), 2) if fvgs else 0.0,
        "atr_14": atr,
        "last_close": last_close,
        "nearest_unmit_ob_gap": nearest_gap,
        "bars_per_ob": round(len(candles) / max(1, len(obs)), 1),
        "bars_per_swing": round(len(candles) / max(1, len(swings)), 1),
    }


def main():
    # per CLAUDE.md: swing_detection_min_bars per TF is in config; use reasonable defaults
    tf_cfg = {
        "D1": {"min_bars": 2, "fvg_min_gap_xau": 2.0, "fvg_min_gap_eur": 0.0005, "fvg_min_gap_nas": 5.0},
        "H4": {"min_bars": 2, "fvg_min_gap_xau": 1.5, "fvg_min_gap_eur": 0.0003, "fvg_min_gap_nas": 3.0},
        "H1": {"min_bars": 2, "fvg_min_gap_xau": 1.0, "fvg_min_gap_eur": 0.0002, "fvg_min_gap_nas": 2.0},
        "M15": {"min_bars": 2, "fvg_min_gap_xau": 0.5, "fvg_min_gap_eur": 0.0001, "fvg_min_gap_nas": 1.0},
    }
    # Simpler: use fvg_min_gap=0.1×ATR heuristically; check with default 1.0
    symbols = ["XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD", "NAS100", "EURUSD"]
    tfs = ["D1", "H4", "H1", "M15"]

    results = []
    for sym in symbols:
        for tf in tfs:
            try:
                candles = load_tf(sym, tf)
            except FileNotFoundError:
                continue
            # Rough fvg_min_gap scale per symbol (ATR-ish)
            atr = calculate_atr(candles, period=14)
            gap = atr * 0.15  # 15% of ATR — rough
            s = summarize(sym, tf, candles, min_bars=2, fvg_min_gap=gap)
            results.append(s)

    # Emit CSV
    out_csv = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "07_market_state_summary.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"Saved: {out_csv}")

    # Print table
    print(f"{'symbol':<8}{'tf':<5}{'bars':>6}{'sw':>5}{'struct':>15}{'evts':>5}{'BOS':>5}{'CH':>4}"
          f"{'OB':>5}{'un':>4}{'Brk':>5}{'FVG':>6}{'%fil':>6}{'atr':>10}{'gap':>10}{'bar/OB':>8}")
    for r in results:
        print(f"{r['symbol']:<8}{r['tf']:<5}{r['n_bars']:>6}{r['n_swings']:>5}{r['structure']:>15}"
              f"{r['n_events']:>5}{r['n_bos']:>5}{r['n_choch']:>4}{r['n_obs_total']:>5}{r['n_obs_unmit']:>4}"
              f"{r['n_breakers']:>5}{r['n_fvgs']:>6}{r['pct_fvgs_filled']:>6.1f}"
              f"{r['atr_14']:>10.4f}{str(r['nearest_unmit_ob_gap'] or '-')[:9]:>10}{r['bars_per_ob']:>8}")


if __name__ == "__main__":
    main()
