"""
Replay `identify_structure` over H1 historical data to check whether H1 direction
labeling behaves symmetrically and tracks market in April 2026.

This uses the same logic as src/components/market_state.py without importing,
to avoid side effects.
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import Counter
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "historical_2026"


@dataclass
class Swing:
    index: int
    type: str
    price: float
    time: str


def detect_swings(candles, min_bars: int = 2) -> list[Swing]:
    swings = []
    for i in range(min_bars, len(candles) - min_bars):
        is_swing_high = all(
            candles[i]["high"] > candles[i - j]["high"]
            and candles[i]["high"] > candles[i + j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_high:
            swings.append(Swing(i, "high", candles[i]["high"], candles[i]["time"]))
        is_swing_low = all(
            candles[i]["low"] < candles[i - j]["low"]
            and candles[i]["low"] < candles[i + j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_low:
            swings.append(Swing(i, "low", candles[i]["low"], candles[i]["time"]))
    return sorted(swings, key=lambda s: s.index)


def identify_structure(swings: list[Swing]) -> str:
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient_data"
    hh_count = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price)
    ll_count = sum(1 for i in range(1, len(lows)) if lows[i].price < lows[i - 1].price)
    hl_count = sum(1 for i in range(1, len(lows)) if lows[i].price > lows[i - 1].price)
    lh_count = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price)
    recent_pairs = min(3, len(highs) - 1, len(lows) - 1)
    if hh_count >= recent_pairs and hl_count >= recent_pairs:
        return "bullish"
    if ll_count >= recent_pairs and lh_count >= recent_pairs:
        return "bearish"
    return "transitional"


def _read_tf(symbol: str, tf: str) -> list[dict]:
    fp = DATA / f"{symbol}_{tf}.csv"
    rows = []
    if not fp.exists():
        return rows
    with open(fp, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "time": r["time"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
            })
    return rows


def main() -> None:
    SWING_WINDOW = 200  # bars, consistent with typical MSO lookback
    for symbol in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        for tf in ("D1", "H4", "H1"):
            rows = _read_tf(symbol, tf)
            if not rows:
                print(f"-- {symbol} {tf}: no CSV"); continue
            print(f"\n-- {symbol} {tf} — replay identify_structure at end-of-day for April 2026 --")
            april_indexes = [i for i, r in enumerate(rows) if r["time"].startswith("2026-04")]
            if not april_indexes:
                print("  (no April rows)")
                continue
            labels = Counter()
            for i in april_indexes:
                window = rows[max(0, i - SWING_WINDOW + 1): i + 1]
                swings = detect_swings(window, min_bars=2)
                label = identify_structure(swings)
                labels[label] += 1
            print(f"  Label distribution over {len(april_indexes)} candle closes: {dict(labels)}")
            print(f"  Bull pct: {100*labels['bullish']/len(april_indexes):.0f}%, "
                  f"Bear pct: {100*labels['bearish']/len(april_indexes):.0f}%, "
                  f"Trans pct: {100*labels['transitional']/len(april_indexes):.0f}%")


if __name__ == "__main__":
    main()
