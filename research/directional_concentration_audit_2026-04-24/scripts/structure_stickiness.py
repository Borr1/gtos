"""
Test whether identify_structure's swing-count-based classification produces a
bearish label when a clearly bearish run happens, or whether historical HH/HL
from earlier in the window dominate.

This time with random-walk noise overlaid on a trend so swings actually form.
"""
from __future__ import annotations
import random
from dataclasses import dataclass


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
        return "insufficient_data", {"nhighs": len(highs), "nlows": len(lows)}
    hh_count = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price)
    ll_count = sum(1 for i in range(1, len(lows)) if lows[i].price < lows[i - 1].price)
    hl_count = sum(1 for i in range(1, len(lows)) if lows[i].price > lows[i - 1].price)
    lh_count = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price)
    recent_pairs = min(3, len(highs) - 1, len(lows) - 1)
    label = "transitional"
    if hh_count >= recent_pairs and hl_count >= recent_pairs:
        label = "bullish"
    elif ll_count >= recent_pairs and lh_count >= recent_pairs:
        label = "bearish"
    return label, {
        "hh": hh_count, "hl": hl_count, "lh": lh_count, "ll": ll_count,
        "recent_pairs": recent_pairs, "nhighs": len(highs), "nlows": len(lows)
    }


def _mk_candles(trend_slope: float, n: int, noise: float, start_price: float = 100.0,
                start_idx: int = 0, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    candles = []
    price = start_price
    for i in range(n):
        drift = trend_slope * i
        o = price
        # Random movement with drift
        move = trend_slope + rng.gauss(0, noise)
        c = o + move
        hi = max(o, c) + abs(rng.gauss(0, noise * 0.5))
        lo = min(o, c) - abs(rng.gauss(0, noise * 0.5))
        candles.append({"time": str(start_idx + i), "open": o, "high": hi, "low": lo, "close": c})
        price = c
    return candles


def scenario(name, candles, desc):
    swings = detect_swings(candles, 2)
    label, stats = identify_structure(swings)
    print(f"\n-- {name}: {desc} (n_candles={len(candles)} n_swings={len(swings)}) --")
    print(f"   label={label} stats={stats}")


def main():
    # S_up: pure uptrend with realistic noise
    s_up = _mk_candles(trend_slope=0.1, n=200, noise=0.5, seed=1)
    scenario("S_up", s_up, "pure 200-bar uptrend + noise")

    # S_down: pure downtrend with noise
    s_down = _mk_candles(trend_slope=-0.1, n=200, noise=0.5, seed=2)
    scenario("S_down", s_down, "pure 200-bar downtrend + noise")

    # S_flat: pure random walk
    s_flat = _mk_candles(trend_slope=0.0, n=200, noise=0.5, seed=3)
    scenario("S_flat", s_flat, "pure random walk")

    # S_stickiness_1: 150 uptrend + 50 reversal (~200 bar window)
    s_stick_1 = _mk_candles(trend_slope=0.1, n=150, noise=0.5, seed=4)
    last_price = s_stick_1[-1]["close"]
    s_stick_1 += _mk_candles(trend_slope=-0.1, n=50, noise=0.5, seed=5, start_price=last_price, start_idx=150)
    scenario("S_stick_1", s_stick_1, "150 up + 50 down — reversal 25% of window")

    # S_stickiness_2: 100 uptrend + 100 reversal (~200 bar window)
    s_stick_2 = _mk_candles(trend_slope=0.1, n=100, noise=0.5, seed=6)
    last_price = s_stick_2[-1]["close"]
    s_stick_2 += _mk_candles(trend_slope=-0.1, n=100, noise=0.5, seed=7, start_price=last_price, start_idx=100)
    scenario("S_stick_2", s_stick_2, "100 up + 100 down — 50/50 split")

    # S_stickiness_3: 50 uptrend + 150 reversal (~200 bar window)
    s_stick_3 = _mk_candles(trend_slope=0.1, n=50, noise=0.5, seed=8)
    last_price = s_stick_3[-1]["close"]
    s_stick_3 += _mk_candles(trend_slope=-0.1, n=150, noise=0.5, seed=9, start_price=last_price, start_idx=50)
    scenario("S_stick_3", s_stick_3, "50 up + 150 down — 25/75 split (reversal dominant)")

    # S_stickiness_4: 180 uptrend + 20 mild retrace
    s_stick_4 = _mk_candles(trend_slope=0.1, n=180, noise=0.5, seed=10)
    last_price = s_stick_4[-1]["close"]
    s_stick_4 += _mk_candles(trend_slope=-0.08, n=20, noise=0.5, seed=11, start_price=last_price, start_idx=180)
    scenario("S_stick_4", s_stick_4, "180 up + 20 mild retrace — 10% of window")


if __name__ == "__main__":
    main()
