"""
Replay identify_structure using production lookbacks
(D1=30, H4=80, H1=168, M15=672) and min_bars=2.

Question: is `bearish` EVER produced on real data with production settings?
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import Counter
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "historical_2026"

# Production lookbacks
LOOKBACK = {"D1": 30, "H4": 80, "H1": 168, "M15": 672}


@dataclass
class Swing:
    index: int
    type: str
    price: float
    time: str


def detect_swings(candles, min_bars: int = 2):
    swings = []
    for i in range(min_bars, len(candles) - min_bars):
        is_high = all(
            candles[i]["high"] > candles[i - j]["high"]
            and candles[i]["high"] > candles[i + j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_high:
            swings.append(Swing(i, "high", candles[i]["high"], candles[i]["time"]))
        is_low = all(
            candles[i]["low"] < candles[i - j]["low"]
            and candles[i]["low"] < candles[i + j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_low:
            swings.append(Swing(i, "low", candles[i]["low"], candles[i]["time"]))
    return sorted(swings, key=lambda s: s.index)


def identify_structure(swings):
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient_data", None
    hh = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i-1].price)
    ll = sum(1 for i in range(1, len(lows)) if lows[i].price < lows[i-1].price)
    hl = sum(1 for i in range(1, len(lows)) if lows[i].price > lows[i-1].price)
    lh = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i-1].price)
    rp = min(3, len(highs)-1, len(lows)-1)
    if hh >= rp and hl >= rp:
        return "bullish", {"hh":hh,"hl":hl,"lh":lh,"ll":ll,"rp":rp}
    if ll >= rp and lh >= rp:
        return "bearish", {"hh":hh,"hl":hl,"lh":lh,"ll":ll,"rp":rp}
    return "transitional", {"hh":hh,"hl":hl,"lh":lh,"ll":ll,"rp":rp}


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


def main():
    for symbol in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        print(f"\n=== {symbol} ===")
        for tf in ("D1", "H4", "H1"):
            rows = _read_tf(symbol, tf)
            lb = LOOKBACK[tf]
            if len(rows) < lb:
                print(f"  {tf}: n_rows={len(rows)} < lookback={lb}, skipping")
                continue
            labels = Counter()
            first_bearish = None
            for i in range(lb - 1, len(rows)):
                window = rows[i - lb + 1: i + 1]
                swings = detect_swings(window, 2)
                label, stats = identify_structure(swings)
                labels[label] += 1
                if label == "bearish" and first_bearish is None:
                    first_bearish = (rows[i]["time"], stats)
            total = sum(labels.values())
            print(f"  {tf} (lb={lb}): n_closes={total}  "
                  f"bullish={labels['bullish']} ({100*labels['bullish']/max(total,1):.1f}%), "
                  f"bearish={labels['bearish']} ({100*labels['bearish']/max(total,1):.1f}%), "
                  f"transitional={labels['transitional']} ({100*labels['transitional']/max(total,1):.1f}%)")
            if first_bearish:
                print(f"    first bearish close: {first_bearish[0]} stats={first_bearish[1]}")


if __name__ == "__main__":
    main()
