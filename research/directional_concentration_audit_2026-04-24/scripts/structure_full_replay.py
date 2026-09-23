"""
Full-range replay of identify_structure on all historical CSV data to see how
often it produces each label per symbol×TF. The question: is 'bearish' EVER
produced on real market data, or is it numerically near-impossible with the
current threshold?
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import Counter
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "historical_2026"
WINDOW = 200  # standard MSO lookback


@dataclass
class Swing:
    index: int
    type: str
    price: float
    time: str


def detect_swings(candles, min_bars: int = 2):
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


def identify_structure(swings):
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


def _read_tf(symbol: str, tf: str):
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
    for symbol in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        for tf in ("D1", "H4", "H1"):
            rows = _read_tf(symbol, tf)
            if not rows:
                continue
            labels = Counter()
            for i in range(WINDOW - 1, len(rows)):
                window = rows[i - WINDOW + 1: i + 1]
                swings = detect_swings(window, 2)
                labels[identify_structure(swings)] += 1
            total = sum(labels.values())
            print(f"{symbol} {tf}: n_closes={total}  "
                  f"bullish={labels['bullish']} ({100*labels['bullish']/max(total,1):.1f}%), "
                  f"bearish={labels['bearish']} ({100*labels['bearish']/max(total,1):.1f}%), "
                  f"transitional={labels['transitional']} ({100*labels['transitional']/max(total,1):.1f}%), "
                  f"insufficient={labels['insufficient_data']}")


if __name__ == "__main__":
    main()
