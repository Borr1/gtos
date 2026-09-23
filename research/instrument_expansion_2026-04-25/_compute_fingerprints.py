"""Comprehensive structural fingerprint computation for 24 instruments.

Tier 1 Agent #1 — Instrument Expansion Research, 2026-04-25.

Computes per-instrument metrics across 10 sections:
  1. Liquidity / activity
  2. Structural metrics (re-using market_state.py)
  3. Liquidity-pool topology
  4. Edge-fit estimates (mechanical, no AI)
  5. Cross-correlation
  6. Kill-zone fit
  7. Decay-relevant metrics
  8. Per-instrument scorecard
  9. Composite ranking
 10. Sample chart for top candidates

Pure Python compute on existing CSVs in data/historical_2026/. $0 API.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv
from src.components.market_state import (
    Swing,
    StructureAnalysis,
    StructureEvent,
    OrderBlock,
    FairValueGap,
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    identify_fvgs,
    avg_candle_body,
    calculate_atr,
)

OUT_DIR = PROJECT_ROOT / "research" / "instrument_expansion_2026-04-25"
DATA_DIR = PROJECT_ROOT / "data" / "historical_2026"
CHARTS_DIR = OUT_DIR / "charts"

INSTRUMENTS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD",
    "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD",
    "GER40", "JP225", "NAS100", "NZDUSD", "SPX500",
    "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]

LIVE_INSTRUMENTS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]


def classify_cluster(symbol: str) -> str:
    """Cluster type: FX_major, FX_cross, metal, index, crypto, commodity."""
    fx_majors = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"}
    fx_crosses = {"EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY"}
    metals = {"XAUUSD", "XAGUSD"}
    indices = {"US30_cash", "NAS100", "SPX500", "GER40", "UK100", "JP225"}
    cryptos = {"BTCUSD", "ETHUSD"}
    commodities = {"USOIL_cash", "UKOIL_cash"}

    if symbol in fx_majors:
        return "FX_major"
    if symbol in fx_crosses:
        return "FX_cross"
    if symbol in metals:
        return "metal"
    if symbol in indices:
        return "index"
    if symbol in cryptos:
        return "crypto"
    if symbol in commodities:
        return "commodity"
    return "unknown"


def get_pip_size(symbol: str) -> float:
    """Pip size for round-number gravity calculation.

    For FX pairs with USD: 0.0001 pip (4dp), JPY pairs: 0.01.
    For metals: 0.01 (XAU/XAG quoted to 2dp).
    For indices: 1 point (round numbers are 100/1000-pt levels).
    For crypto: 1 USD (round numbers are 100/1000 USD).
    For commodities (oil): 0.01.
    """
    if "JPY" in symbol:
        return 0.01
    if symbol in {"XAUUSD", "XAGUSD"}:
        return 0.01
    if symbol in {"GER40", "UK100", "JP225", "US30_cash", "NAS100", "SPX500"}:
        return 1.0
    if symbol in {"BTCUSD", "ETHUSD"}:
        return 1.0
    if symbol in {"USOIL_cash", "UKOIL_cash"}:
        return 0.01
    return 0.0001  # FX majors


def round_number_grid_step(symbol: str) -> float:
    """Round-number grid step for round-number gravity test.

    Per Osler 2003: FX clusters at 50/100 pip levels.
    Adjusted by instrument scale.
    """
    cluster = classify_cluster(symbol)
    if cluster == "FX_major":
        return 0.0050  # 50 pips
    if cluster == "FX_cross":
        if "JPY" in symbol:
            return 0.50  # 50 pips for JPY pairs (0.01 pip × 50)
        return 0.0050
    if cluster == "metal":
        if symbol == "XAUUSD":
            return 10.0  # $10 increments
        return 1.0  # XAGUSD ~$30-50, $1 increments
    if cluster == "index":
        if symbol in {"NAS100"}:
            return 100.0  # NAS100 ~20000, 100-pt grid
        if symbol in {"US30_cash"}:
            return 100.0  # US30 ~40000, 100-pt grid
        if symbol in {"SPX500"}:
            return 25.0  # SPX ~5000-6000, 25-pt grid
        if symbol in {"GER40", "UK100"}:
            return 50.0
        if symbol == "JP225":
            return 100.0
    if cluster == "crypto":
        if symbol == "BTCUSD":
            return 1000.0  # $1000 increments
        return 100.0  # ETH $100 increments
    if cluster == "commodity":
        return 1.0  # $1 oil increments
    return 0.0050


# ─────────────────────────────────────────────────────────────────────────
# Section 1: Liquidity / Activity
# ─────────────────────────────────────────────────────────────────────────

def compute_section_1(candles_m15: list[dict], candles_h1: list[dict],
                      candles_h4: list[dict], candles_d1: list[dict]) -> dict:
    """Liquidity and activity metrics."""

    # Average daily volume (sum tick volume per UTC date from M15)
    daily_vol: dict[str, float] = defaultdict(float)
    for c in candles_m15:
        date = c["time"][:10]
        daily_vol[date] += c.get("volume", 0)

    avg_daily_vol = statistics.mean(daily_vol.values()) if daily_vol else 0.0

    # Average daily range (D1 H-L)
    if candles_d1:
        daily_ranges = [c["high"] - c["low"] for c in candles_d1]
        avg_daily_range = statistics.mean(daily_ranges)
        sorted_ranges = sorted(daily_ranges)
        n = len(sorted_ranges)
        p10 = sorted_ranges[int(n * 0.10)] if n > 10 else sorted_ranges[0]
        p50 = sorted_ranges[int(n * 0.50)]
        p90 = sorted_ranges[int(n * 0.90)] if n > 10 else sorted_ranges[-1]
    else:
        avg_daily_range = p10 = p50 = p90 = 0.0

    # Average M15 candle range
    m15_ranges = [c["high"] - c["low"] for c in candles_m15]
    avg_m15_range = statistics.mean(m15_ranges) if m15_ranges else 0.0

    # ATRs
    atr_m15 = calculate_atr(candles_m15, 14)
    atr_h1 = calculate_atr(candles_h1, 14)
    atr_h4 = calculate_atr(candles_h4, 14)
    atr_d1 = calculate_atr(candles_d1, 14)

    # Weekend gap behavior — detect Sunday→Monday or Friday→Sunday gaps in D1
    gaps = []
    for i in range(1, len(candles_d1)):
        prev_close = candles_d1[i - 1]["close"]
        curr_open = candles_d1[i]["open"]
        gap = abs(curr_open - prev_close)
        # Time delta to identify weekend gaps
        try:
            t_prev = datetime.fromisoformat(candles_d1[i - 1]["time"].rstrip("Z"))
            t_curr = datetime.fromisoformat(candles_d1[i]["time"].rstrip("Z"))
            delta_days = (t_curr - t_prev).days
            if delta_days >= 2:  # weekend gap
                gaps.append(gap)
        except Exception:
            pass

    avg_weekend_gap = statistics.mean(gaps) if gaps else 0.0
    weekend_gap_freq = len(gaps) / max(1, len(candles_d1) // 7)  # approx frac of weeks

    return {
        "avg_daily_volume": round(avg_daily_vol, 2),
        "avg_daily_range": round(avg_daily_range, 5),
        "avg_m15_range": round(avg_m15_range, 5),
        "atr_m15_14": round(atr_m15, 5),
        "atr_h1_14": round(atr_h1, 5),
        "atr_h4_14": round(atr_h4, 5),
        "atr_d1_14": round(atr_d1, 5),
        "daily_range_p10": round(p10, 5),
        "daily_range_p50": round(p50, 5),
        "daily_range_p90": round(p90, 5),
        "avg_weekend_gap": round(avg_weekend_gap, 5),
        "weekend_gap_frequency": round(weekend_gap_freq, 3),
        "n_d1": len(candles_d1),
        "n_m15": len(candles_m15),
    }


# ─────────────────────────────────────────────────────────────────────────
# Section 2: Structural metrics
# ─────────────────────────────────────────────────────────────────────────

def compute_section_2(candles_m15: list[dict], candles_h1: list[dict],
                      candles_d1: list[dict], atr_m15: float, atr_h1: float) -> dict:
    """Structural metrics using market_state.py."""

    # H1 swings + structure events (full series)
    h1_swings = detect_swings(candles_h1, min_bars=2)
    h1_structure = identify_structure(h1_swings)
    h1_events = detect_structure_breaks(candles_h1, h1_swings, h1_structure)

    bos_count = sum(1 for e in h1_events if e.type == "BOS")
    choch_count = sum(1 for e in h1_events if e.type == "CHoCH")

    # Per H1, per day rates
    n_h1 = len(candles_h1)
    n_days = len(candles_d1) if candles_d1 else max(1, n_h1 // 24)
    bos_per_h1 = bos_count / max(1, n_h1)
    bos_per_day = bos_count / max(1, n_days)
    choch_per_h1 = choch_count / max(1, n_h1)
    choch_per_day = choch_count / max(1, n_days)

    # OB formation count per month (using H1 events)
    # Period in months
    if candles_h1:
        try:
            t_first = datetime.fromisoformat(candles_h1[0]["time"].rstrip("Z"))
            t_last = datetime.fromisoformat(candles_h1[-1]["time"].rstrip("Z"))
            n_months = max(1, (t_last - t_first).days / 30.4)
        except Exception:
            n_months = max(1, n_days / 30.4)
    else:
        n_months = 1.0

    obs = identify_order_blocks(candles_h1, h1_events)
    ob_count = len(obs)
    ob_per_month = ob_count / n_months

    # FVG density per M15 — count per 100 candles
    pip = get_pip_size("FAKE")  # default
    # use a small min_gap of 0.1× ATR_M15 for permissive detection
    min_gap_m15 = max(atr_m15 * 0.1, 1e-6)
    fvgs_m15 = identify_fvgs(candles_m15, min_gap_size=min_gap_m15)
    fvg_density_per_100 = (len(fvgs_m15) / max(1, len(candles_m15))) * 100

    # Displacement candle frequency: body > 1.5× M15-ATR
    disp_count = 0
    for c in candles_m15:
        body = abs(c["close"] - c["open"])
        if atr_m15 > 0 and body >= 1.5 * atr_m15:
            disp_count += 1
    disp_freq = disp_count / max(1, len(candles_m15))

    # Equal-H/L formation rate: M15 swings within 0.1 × atr_m15
    m15_swings = detect_swings(candles_m15, min_bars=2)
    highs = [s for s in m15_swings if s.type == "high"]
    lows = [s for s in m15_swings if s.type == "low"]

    eq_high_count = 0
    for i, h1_swing in enumerate(highs):
        # check next 8 swings for equal-high
        for j in range(i + 1, min(i + 9, len(highs))):
            if abs(highs[j].price - h1_swing.price) <= 0.1 * atr_m15:
                eq_high_count += 1
                break

    eq_low_count = 0
    for i, l_swing in enumerate(lows):
        for j in range(i + 1, min(i + 9, len(lows))):
            if abs(lows[j].price - l_swing.price) <= 0.1 * atr_m15:
                eq_low_count += 1
                break

    eq_rate = (eq_high_count + eq_low_count) / max(1, len(highs) + len(lows))

    # Average swings per H1 day
    swings_per_day = len(h1_swings) / max(1, n_days)

    # Trend strength: cumulative directional movement / total movement (ADX-like)
    # On H1 series: sum |close[i]-close[i-1]| signed, divide by sum |...| absolute
    if len(candles_h1) > 1:
        net = abs(candles_h1[-1]["close"] - candles_h1[0]["close"])
        gross = sum(
            abs(candles_h1[i]["close"] - candles_h1[i - 1]["close"])
            for i in range(1, len(candles_h1))
        )
        trend_strength = net / max(gross, 1e-9)
    else:
        trend_strength = 0.0

    return {
        "bos_count": bos_count,
        "bos_per_h1": round(bos_per_h1, 5),
        "bos_per_day": round(bos_per_day, 4),
        "choch_count": choch_count,
        "choch_per_h1": round(choch_per_h1, 5),
        "choch_per_day": round(choch_per_day, 4),
        "ob_count": ob_count,
        "ob_per_month": round(ob_per_month, 2),
        "fvg_count_m15": len(fvgs_m15),
        "fvg_density_per_100_m15": round(fvg_density_per_100, 3),
        "displacement_count_m15": disp_count,
        "displacement_freq_m15": round(disp_freq, 4),
        "equal_high_count_m15": eq_high_count,
        "equal_low_count_m15": eq_low_count,
        "equal_rate_m15": round(eq_rate, 4),
        "swings_per_h1_day": round(swings_per_day, 3),
        "trend_strength": round(trend_strength, 4),
        "n_h1_swings": len(h1_swings),
        "n_m15_swings": len(m15_swings),
        "n_days": n_days,
        "n_months": round(n_months, 2),
    }, h1_swings, h1_events, obs, fvgs_m15


# ─────────────────────────────────────────────────────────────────────────
# Section 3: Liquidity-pool topology
# ─────────────────────────────────────────────────────────────────────────

def compute_section_3(candles_m15: list[dict], candles_h1: list[dict],
                      candles_d1: list[dict], h1_swings: list[Swing],
                      symbol: str) -> dict:
    """Liquidity-pool topology metrics."""

    grid_step = round_number_grid_step(symbol)
    pip = get_pip_size(symbol)

    # Round-number gravity: % of significant H1 swings within 5% of grid_step
    # of the nearest round-number level. Per Osler 2003 the relevant clustering
    # is at the *round number* (50/100 pip increments for FX, $10 for XAUUSD,
    # 100-pt for indices), not at every pip mark — so we measure proximity as
    # a fraction of the grid step itself, not as an absolute pip distance.
    # This makes the metric instrument-comparable.
    threshold = grid_step * 0.05  # 5% of grid step
    near_round = 0
    for s in h1_swings:
        # Distance to nearest round
        nearest_round = round(s.price / grid_step) * grid_step
        if abs(s.price - nearest_round) <= threshold:
            near_round += 1
    round_number_gravity = near_round / max(1, len(h1_swings))

    # Session H/L formation (on M15 candles, group by date + session window)
    LONDON_START_UTC = 7
    LONDON_END_UTC = 11
    NY_START_UTC = 13
    NY_END_UTC = 17
    TOKYO_START_UTC = 0
    TOKYO_END_UTC = 4

    london_extremes = defaultdict(lambda: {"high": -math.inf, "low": math.inf})
    ny_extremes = defaultdict(lambda: {"high": -math.inf, "low": math.inf})
    tokyo_extremes = defaultdict(lambda: {"high": -math.inf, "low": math.inf})

    for c in candles_m15:
        try:
            t = datetime.fromisoformat(c["time"].rstrip("Z"))
            date_key = t.strftime("%Y-%m-%d")
            hour = t.hour
            if LONDON_START_UTC <= hour < LONDON_END_UTC:
                london_extremes[date_key]["high"] = max(london_extremes[date_key]["high"], c["high"])
                london_extremes[date_key]["low"] = min(london_extremes[date_key]["low"], c["low"])
            if NY_START_UTC <= hour < NY_END_UTC:
                ny_extremes[date_key]["high"] = max(ny_extremes[date_key]["high"], c["high"])
                ny_extremes[date_key]["low"] = min(ny_extremes[date_key]["low"], c["low"])
            if TOKYO_START_UTC <= hour < TOKYO_END_UTC:
                tokyo_extremes[date_key]["high"] = max(tokyo_extremes[date_key]["high"], c["high"])
                tokyo_extremes[date_key]["low"] = min(tokyo_extremes[date_key]["low"], c["low"])
        except Exception:
            pass

    n_london_sessions = sum(1 for v in london_extremes.values() if v["high"] > -math.inf)
    n_ny_sessions = sum(1 for v in ny_extremes.values() if v["high"] > -math.inf)
    n_tokyo_sessions = sum(1 for v in tokyo_extremes.values() if v["high"] > -math.inf)

    # Day H/L retest rate: how often does next day's price retest prior day's H or L
    daily_retest_count = 0
    for i in range(1, len(candles_d1)):
        prev_high = candles_d1[i - 1]["high"]
        prev_low = candles_d1[i - 1]["low"]
        curr_high = candles_d1[i]["high"]
        curr_low = candles_d1[i]["low"]
        # retest if curr extends beyond prev by less than 0.3× ATR
        if curr_high >= prev_high or curr_low <= prev_low:
            daily_retest_count += 1
    daily_retest_rate = daily_retest_count / max(1, len(candles_d1) - 1)

    # Weekly H/L retest rate (approximate from D1 grouped by ISO week)
    weekly_extremes = defaultdict(lambda: {"high": -math.inf, "low": math.inf})
    for c in candles_d1:
        try:
            t = datetime.fromisoformat(c["time"].rstrip("Z"))
            iso_week = t.strftime("%G-W%V")
            weekly_extremes[iso_week]["high"] = max(weekly_extremes[iso_week]["high"], c["high"])
            weekly_extremes[iso_week]["low"] = min(weekly_extremes[iso_week]["low"], c["low"])
        except Exception:
            pass

    n_weeks = len(weekly_extremes)
    weeks_sorted = sorted(weekly_extremes.keys())
    weekly_retest_count = 0
    for i in range(1, len(weeks_sorted)):
        # crude: if the week's extreme is within 0.5× weekly avg range of prior week's H/L
        prev = weekly_extremes[weeks_sorted[i - 1]]
        curr = weekly_extremes[weeks_sorted[i]]
        if curr["high"] >= prev["high"] or curr["low"] <= prev["low"]:
            weekly_retest_count += 1
    weekly_retest_rate = weekly_retest_count / max(1, n_weeks - 1)

    return {
        "round_number_gravity_pct": round(round_number_gravity * 100, 2),
        "round_number_grid_step": grid_step,
        "pip_size": pip,
        "n_h1_swings_evaluated": len(h1_swings),
        "n_london_sessions": n_london_sessions,
        "n_ny_sessions": n_ny_sessions,
        "n_tokyo_sessions": n_tokyo_sessions,
        "daily_retest_rate": round(daily_retest_rate, 3),
        "weekly_retest_rate": round(weekly_retest_rate, 3),
        "n_weeks": n_weeks,
    }


# ─────────────────────────────────────────────────────────────────────────
# Section 4: Edge-fit estimates (mechanical)
# ─────────────────────────────────────────────────────────────────────────

def _candle_overlaps_zone(candle: dict, low: float, high: float) -> bool:
    return candle["low"] <= high and candle["high"] >= low


def _simulate_outcome(entry_price: float, sl: float, tp: float, direction: str,
                      forward_candles: list[dict], max_bars: int = 16) -> str | None:
    """Simulate trade outcome. Return 'win', 'loss', or None (timeout)."""
    if direction == "long":
        for c in forward_candles[:max_bars]:
            # SL first if both hit (conservative)
            if c["low"] <= sl:
                return "loss"
            if c["high"] >= tp:
                return "win"
    elif direction == "short":
        for c in forward_candles[:max_bars]:
            if c["high"] >= sl:
                return "loss"
            if c["low"] <= tp:
                return "win"
    return None


def compute_section_4(candles_m15: list[dict], candles_h1: list[dict],
                      h1_swings: list[Swing], h1_events: list[StructureEvent],
                      obs: list[OrderBlock], fvgs_m15: list[FairValueGap],
                      atr_m15: float, atr_h1: float) -> dict:
    """Edge-fit estimates: count candidate setups + mechanical implied WR.

    For each of 4 edges (ob_retest, fvg_fill, breaker_re_entry, sweep+reversal),
    count candidate setups in 6-month history, and simulate outcomes.

    Trade geometry: TP=1.5R, SL=1×ATR-M15. Forward window=16 M15 bars.
    """
    # Map H1 candle indices to approximate M15 indices using time matching
    h1_time_to_m15_idx: dict[str, int] = {}
    for i, c in enumerate(candles_m15):
        h1_time_to_m15_idx.setdefault(c["time"][:13], i)  # YYYY-MM-DDTHH

    def m15_idx_at_time(iso_time: str) -> int | None:
        # Try exact match first
        if iso_time[:13] in h1_time_to_m15_idx:
            return h1_time_to_m15_idx[iso_time[:13]]
        return None

    # ────────────────────────────────────────────────────────────
    # Edge 1: ob_retest
    # ────────────────────────────────────────────────────────────
    ob_candidates = 0
    ob_wins = 0
    ob_losses = 0
    ob_timeouts = 0

    for ob in obs:
        if not ob.mitigated:
            continue
        if atr_m15 <= 0:
            continue
        # Find M15 retest candle: first candle after BOS with low<=ob.high and high>=ob.low
        bos_h1_idx = ob.causing_bos_index
        if bos_h1_idx >= len(candles_h1):
            continue
        bos_time = candles_h1[bos_h1_idx]["time"]
        m15_start = m15_idx_at_time(bos_time)
        if m15_start is None:
            continue

        # Walk M15 forward to find first retest
        retest_idx = None
        for j in range(m15_start + 1, min(m15_start + 80, len(candles_m15))):
            if _candle_overlaps_zone(candles_m15[j], ob.low, ob.high):
                retest_idx = j
                break

        if retest_idx is None:
            continue

        # Direction: bullish OB → long, bearish OB → short
        direction = "long" if ob.type == "bullish" else "short"
        if direction == "long":
            entry = ob.high  # touch top of OB
            sl = ob.low - 0.5 * atr_m15
            risk = entry - sl
            tp = entry + 1.5 * risk
        else:
            entry = ob.low
            sl = ob.high + 0.5 * atr_m15
            risk = sl - entry
            tp = entry - 1.5 * risk

        if risk <= 0:
            continue

        forward = candles_m15[retest_idx:retest_idx + 16]
        outcome = _simulate_outcome(entry, sl, tp, direction, forward, max_bars=16)
        ob_candidates += 1
        if outcome == "win":
            ob_wins += 1
        elif outcome == "loss":
            ob_losses += 1
        else:
            ob_timeouts += 1

    ob_wr = ob_wins / max(1, ob_wins + ob_losses)

    # ────────────────────────────────────────────────────────────
    # Edge 2: fvg_fill
    # ────────────────────────────────────────────────────────────
    fvg_candidates = 0
    fvg_wins = 0
    fvg_losses = 0
    fvg_timeouts = 0

    # On M15 FVGs that filled, simulate the retest entry
    for fvg in fvgs_m15:
        if not fvg.filled:
            continue
        if atr_m15 <= 0:
            continue
        formation_idx = max(fvg.candle_indices)
        # Find first fill candle (the one that closed back through)
        fill_idx = None
        for j in range(formation_idx + 1, min(formation_idx + 30, len(candles_m15))):
            if fvg.type == "bullish" and candles_m15[j]["low"] <= fvg.bottom:
                fill_idx = j
                break
            if fvg.type == "bearish" and candles_m15[j]["high"] >= fvg.top:
                fill_idx = j
                break
        if fill_idx is None:
            continue

        direction = "long" if fvg.type == "bullish" else "short"
        if direction == "long":
            entry = fvg.midpoint
            sl = fvg.bottom - 0.5 * atr_m15
            risk = entry - sl
            tp = entry + 1.5 * risk
        else:
            entry = fvg.midpoint
            sl = fvg.top + 0.5 * atr_m15
            risk = sl - entry
            tp = entry - 1.5 * risk

        if risk <= 0:
            continue

        forward = candles_m15[fill_idx:fill_idx + 16]
        outcome = _simulate_outcome(entry, sl, tp, direction, forward, max_bars=16)
        fvg_candidates += 1
        if outcome == "win":
            fvg_wins += 1
        elif outcome == "loss":
            fvg_losses += 1
        else:
            fvg_timeouts += 1

    fvg_wr = fvg_wins / max(1, fvg_wins + fvg_losses)

    # ────────────────────────────────────────────────────────────
    # Edge 3: breaker_re_entry
    # Mitigated OB → polarity flip → retest from opposite side
    # ────────────────────────────────────────────────────────────
    breaker_candidates = 0
    breaker_wins = 0
    breaker_losses = 0
    breaker_timeouts = 0

    for ob in obs:
        # Need ob mitigated AND further price action breaks through
        if not ob.mitigated:
            continue
        bos_h1_idx = ob.causing_bos_index
        m15_start = m15_idx_at_time(candles_h1[bos_h1_idx]["time"]) if bos_h1_idx < len(candles_h1) else None
        if m15_start is None:
            continue

        # For bullish OB: needs body close BELOW low (polarity flip to bearish)
        # then retest from below = SHORT entry
        # For bearish OB: body close ABOVE high → LONG retest
        flip_idx = None
        for j in range(m15_start + 1, min(m15_start + 200, len(candles_m15))):
            cb = candles_m15[j]
            cb_body_low = min(cb["open"], cb["close"])
            cb_body_high = max(cb["open"], cb["close"])
            if ob.type == "bullish" and cb_body_high < ob.low:
                flip_idx = j
                break
            if ob.type == "bearish" and cb_body_low > ob.high:
                flip_idx = j
                break

        if flip_idx is None:
            continue

        # Find retest after flip
        retest_idx = None
        for j in range(flip_idx + 1, min(flip_idx + 80, len(candles_m15))):
            if _candle_overlaps_zone(candles_m15[j], ob.low, ob.high):
                retest_idx = j
                break
        if retest_idx is None:
            continue

        direction = "short" if ob.type == "bullish" else "long"
        if direction == "long":
            entry = ob.high
            sl = ob.low - 0.5 * atr_m15
            risk = entry - sl
            tp = entry + 1.5 * risk
        else:
            entry = ob.low
            sl = ob.high + 0.5 * atr_m15
            risk = sl - entry
            tp = entry - 1.5 * risk

        if risk <= 0:
            continue
        forward = candles_m15[retest_idx:retest_idx + 16]
        outcome = _simulate_outcome(entry, sl, tp, direction, forward, max_bars=16)
        breaker_candidates += 1
        if outcome == "win":
            breaker_wins += 1
        elif outcome == "loss":
            breaker_losses += 1
        else:
            breaker_timeouts += 1

    breaker_wr = breaker_wins / max(1, breaker_wins + breaker_losses)

    # ────────────────────────────────────────────────────────────
    # Edge 4: sweep + reversal
    # Detect equal-H/L sweeps on M15 and check for reversal ≥0.5× ATR within 16 bars
    # ────────────────────────────────────────────────────────────
    sweep_candidates = 0
    sweep_wins = 0
    sweep_losses = 0
    sweep_timeouts = 0

    # Build equal-H/L pools from M15 swings
    m15_swings = detect_swings(candles_m15, min_bars=2)
    highs_m = [s for s in m15_swings if s.type == "high"]
    lows_m = [s for s in m15_swings if s.type == "low"]

    # Find equal-high pools (clusters within 0.3 × atr)
    eq_high_levels: list[tuple[int, float]] = []  # (last_swing_idx, price)
    for i, sw in enumerate(highs_m):
        for j in range(i + 1, min(i + 8, len(highs_m))):
            if abs(highs_m[j].price - sw.price) <= 0.3 * atr_m15:
                # Use the second swing's index as the formation
                eq_high_levels.append((highs_m[j].index, max(sw.price, highs_m[j].price)))
                break

    eq_low_levels: list[tuple[int, float]] = []
    for i, sw in enumerate(lows_m):
        for j in range(i + 1, min(i + 8, len(lows_m))):
            if abs(lows_m[j].price - sw.price) <= 0.3 * atr_m15:
                eq_low_levels.append((lows_m[j].index, min(sw.price, lows_m[j].price)))
                break

    # For each equal-high level, scan candles AFTER for sweep + reversal entry
    for level_idx, level_price in eq_high_levels:
        # Look in next 60 candles for a sweep (wick > level, body close < level)
        for j in range(level_idx + 1, min(level_idx + 60, len(candles_m15))):
            c = candles_m15[j]
            body_top = max(c["open"], c["close"])
            if c["high"] > level_price and body_top < level_price:
                # SWEEP detected → SHORT entry on close
                if atr_m15 <= 0:
                    break
                entry = c["close"]
                sl = c["high"] + 0.25 * atr_m15
                risk = sl - entry
                if risk <= 0:
                    break
                tp = entry - 1.5 * risk
                forward = candles_m15[j + 1:j + 17]
                outcome = _simulate_outcome(entry, sl, tp, "short", forward, max_bars=16)
                sweep_candidates += 1
                if outcome == "win":
                    sweep_wins += 1
                elif outcome == "loss":
                    sweep_losses += 1
                else:
                    sweep_timeouts += 1
                break  # only first sweep counted per level

    for level_idx, level_price in eq_low_levels:
        for j in range(level_idx + 1, min(level_idx + 60, len(candles_m15))):
            c = candles_m15[j]
            body_bot = min(c["open"], c["close"])
            if c["low"] < level_price and body_bot > level_price:
                if atr_m15 <= 0:
                    break
                entry = c["close"]
                sl = c["low"] - 0.25 * atr_m15
                risk = entry - sl
                if risk <= 0:
                    break
                tp = entry + 1.5 * risk
                forward = candles_m15[j + 1:j + 17]
                outcome = _simulate_outcome(entry, sl, tp, "long", forward, max_bars=16)
                sweep_candidates += 1
                if outcome == "win":
                    sweep_wins += 1
                elif outcome == "loss":
                    sweep_losses += 1
                else:
                    sweep_timeouts += 1
                break

    sweep_wr = sweep_wins / max(1, sweep_wins + sweep_losses)

    return {
        "ob_retest_candidates": ob_candidates,
        "ob_retest_wins": ob_wins,
        "ob_retest_losses": ob_losses,
        "ob_retest_timeouts": ob_timeouts,
        "ob_retest_wr": round(ob_wr, 4),
        "fvg_fill_candidates": fvg_candidates,
        "fvg_fill_wins": fvg_wins,
        "fvg_fill_losses": fvg_losses,
        "fvg_fill_timeouts": fvg_timeouts,
        "fvg_fill_wr": round(fvg_wr, 4),
        "breaker_re_entry_candidates": breaker_candidates,
        "breaker_re_entry_wins": breaker_wins,
        "breaker_re_entry_losses": breaker_losses,
        "breaker_re_entry_timeouts": breaker_timeouts,
        "breaker_re_entry_wr": round(breaker_wr, 4),
        "sweep_reversal_candidates": sweep_candidates,
        "sweep_reversal_wins": sweep_wins,
        "sweep_reversal_losses": sweep_losses,
        "sweep_reversal_timeouts": sweep_timeouts,
        "sweep_reversal_wr": round(sweep_wr, 4),
    }


# ─────────────────────────────────────────────────────────────────────────
# Section 6: Kill-zone fit
# ─────────────────────────────────────────────────────────────────────────

def compute_section_6(candles_m15: list[dict]) -> dict:
    """Per-session % of daily movement.

    For each UTC date in candles_m15, compute total movement during:
      Asian (00-06 UTC), London (07-12 UTC), NY (13-18 UTC), other.
    Then aggregate.
    """
    daily: dict[str, dict[str, float]] = defaultdict(
        lambda: {"asian": 0.0, "london": 0.0, "ny": 0.0, "other": 0.0, "total": 0.0}
    )

    for c in candles_m15:
        try:
            t = datetime.fromisoformat(c["time"].rstrip("Z"))
            date_key = t.strftime("%Y-%m-%d")
            hour = t.hour
            move = abs(c["close"] - c["open"])
            if 0 <= hour < 7:
                daily[date_key]["asian"] += move
            elif 7 <= hour < 13:
                daily[date_key]["london"] += move
            elif 13 <= hour < 18:
                daily[date_key]["ny"] += move
            else:
                daily[date_key]["other"] += move
            daily[date_key]["total"] += move
        except Exception:
            pass

    total_asian = sum(d["asian"] for d in daily.values())
    total_london = sum(d["london"] for d in daily.values())
    total_ny = sum(d["ny"] for d in daily.values())
    total_other = sum(d["other"] for d in daily.values())
    grand_total = total_asian + total_london + total_ny + total_other

    if grand_total <= 0:
        return {
            "asian_pct": 0.0, "london_pct": 0.0, "ny_pct": 0.0, "other_pct": 0.0,
            "high_activity_sessions": "none",
        }

    asian_pct = total_asian / grand_total * 100
    london_pct = total_london / grand_total * 100
    ny_pct = total_ny / grand_total * 100
    other_pct = total_other / grand_total * 100

    sessions = [
        ("asian", asian_pct),
        ("london", london_pct),
        ("ny", ny_pct),
    ]
    sessions.sort(key=lambda x: -x[1])
    cumulative = 0.0
    high_activity = []
    for name, pct in sessions:
        if cumulative >= 70.0:
            break
        high_activity.append(name)
        cumulative += pct

    return {
        "asian_pct": round(asian_pct, 2),
        "london_pct": round(london_pct, 2),
        "ny_pct": round(ny_pct, 2),
        "other_pct": round(other_pct, 2),
        "high_activity_sessions": ",".join(high_activity),
    }


# ─────────────────────────────────────────────────────────────────────────
# Section 7: Decay-relevant metrics
# ─────────────────────────────────────────────────────────────────────────

def compute_section_7(candles_m15: list[dict], candles_h1: list[dict]) -> dict:
    """Monthly volatility / BOS / displacement trends."""

    # Group candles by month
    monthly_m15: dict[str, list[dict]] = defaultdict(list)
    monthly_h1: dict[str, list[dict]] = defaultdict(list)

    for c in candles_m15:
        ym = c["time"][:7]
        monthly_m15[ym].append(c)
    for c in candles_h1:
        ym = c["time"][:7]
        monthly_h1[ym].append(c)

    months = sorted(monthly_m15.keys())[:4]  # Jan, Feb, Mar, Apr

    monthly_atr_m15: dict[str, float] = {}
    monthly_median_range: dict[str, float] = {}
    monthly_disp_freq: dict[str, float] = {}
    monthly_bos_per_day: dict[str, float] = {}

    for ym in months:
        m15c = monthly_m15.get(ym, [])
        h1c = monthly_h1.get(ym, [])
        atr_m = calculate_atr(m15c, 14)
        monthly_atr_m15[ym] = round(atr_m, 5)

        # Median candle range — robust to outlier shocks (Wilder ATR can be
        # inflated for many bars after one extreme TR; median is regime-stable).
        ranges = [c["high"] - c["low"] for c in m15c]
        if ranges:
            monthly_median_range[ym] = round(sorted(ranges)[len(ranges) // 2], 5)
        else:
            monthly_median_range[ym] = 0.0

        # Displacement freq — use median range × 4 as displacement threshold
        # (more stable than ATR; corresponds roughly to "candle body 4× typical range").
        median_r = monthly_median_range[ym]
        disp = 0
        for c in m15c:
            body = abs(c["close"] - c["open"])
            if median_r > 0 and body >= 4.0 * median_r:
                disp += 1
        monthly_disp_freq[ym] = round(disp / max(1, len(m15c)), 4)

        # BOS rate
        if len(h1c) >= 5:
            sw = detect_swings(h1c, min_bars=2)
            st = identify_structure(sw)
            ev = detect_structure_breaks(h1c, sw, st)
            bos = sum(1 for e in ev if e.type == "BOS")
            n_days = max(1, len(h1c) / 24)
            monthly_bos_per_day[ym] = round(bos / n_days, 3)
        else:
            monthly_bos_per_day[ym] = 0.0

    return {
        "monthly_atr_m15": monthly_atr_m15,
        "monthly_median_range_m15": monthly_median_range,
        "monthly_displacement_freq": monthly_disp_freq,
        "monthly_bos_per_day": monthly_bos_per_day,
    }


# ─────────────────────────────────────────────────────────────────────────
# Section 5: Cross-correlation
# ─────────────────────────────────────────────────────────────────────────

def compute_log_returns(candles_m15: list[dict]) -> dict[str, float]:
    """Compute M15 log returns indexed by ISO timestamp."""
    out = {}
    for i in range(1, len(candles_m15)):
        prev = candles_m15[i - 1]["close"]
        curr = candles_m15[i]["close"]
        if prev > 0 and curr > 0:
            out[candles_m15[i]["time"]] = math.log(curr / prev)
    return out


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return 0.0
    return num / (sx * sy)


def correlation_matrix(returns: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    instruments = list(returns.keys())
    matrix: dict[str, dict[str, float]] = {}
    for a in instruments:
        matrix[a] = {}
        for b in instruments:
            if a == b:
                matrix[a][b] = 1.0
                continue
            common = sorted(set(returns[a].keys()) & set(returns[b].keys()))
            if len(common) < 30:
                matrix[a][b] = 0.0
                continue
            x = [returns[a][t] for t in common]
            y = [returns[b][t] for t in common]
            matrix[a][b] = round(pearson(x, y), 4)
    return matrix


# ─────────────────────────────────────────────────────────────────────────
# Composite scoring
# ─────────────────────────────────────────────────────────────────────────

def compute_composite_score(scorecard: dict, max_values: dict) -> float:
    """Composite weighted score:
      liquidity (20%) + structural fit (30%) + edge-fit (30%) +
      correlation/diversification (10%) + KZ fit (10%).
    Each subcomponent normalized to its observed max across instruments.
    """
    # Liquidity: log avg daily volume (since values vary by 100×)
    vol = scorecard.get("avg_daily_volume", 0)
    log_vol = math.log10(vol + 1)
    log_vol_norm = log_vol / max(max_values.get("log_vol", 1), 1e-9)

    # Structural fit: BOS/day + OB/month + displacement freq
    bos_norm = scorecard.get("bos_per_day", 0) / max(max_values.get("bos_per_day", 1), 1e-9)
    ob_norm = scorecard.get("ob_per_month", 0) / max(max_values.get("ob_per_month", 1), 1e-9)
    disp_norm = scorecard.get("displacement_freq_m15", 0) / max(max_values.get("displacement_freq_m15", 1), 1e-9)
    structural = (bos_norm + ob_norm + disp_norm) / 3

    # Edge-fit: weighted blend of WR × min(candidates, 100)/100 across 4 edges
    edges_score = 0.0
    edges_count = 0
    for edge_key in ("ob_retest", "fvg_fill", "breaker_re_entry", "sweep_reversal"):
        wr = scorecard.get(f"{edge_key}_wr", 0)
        n = scorecard.get(f"{edge_key}_candidates", 0)
        # Implied trades / month — assume 6-month sample
        months = max(scorecard.get("n_months", 1), 1)
        n_per_month = n / months
        # Reward both freq + WR
        # Cap at 50/month for any edge
        capped = min(n_per_month, 50) / 50
        edges_score += wr * capped
        edges_count += 1
    edges = edges_score / max(edges_count, 1)

    # Correlation/diversification: lower correlation to live instruments = higher score
    # But not too low (we want "structurally similar")
    # Use abs-correlation in 0.4-0.7 sweet spot
    avg_corr = scorecard.get("avg_corr_to_live", 0)
    abs_corr = abs(avg_corr)
    if abs_corr < 0.2:
        corr_score = 0.5  # too independent (different mechanism)
    elif abs_corr < 0.5:
        corr_score = 1.0  # sweet spot
    elif abs_corr < 0.8:
        corr_score = 0.7  # similar to live, less diversification
    else:
        corr_score = 0.4  # redundant

    # KZ fit: % of activity during London + NY (our trading sessions)
    kz_pct = scorecard.get("london_pct", 0) + scorecard.get("ny_pct", 0)
    kz_norm = kz_pct / 100  # max 100%

    composite = (
        0.20 * log_vol_norm +
        0.30 * structural +
        0.30 * edges +
        0.10 * corr_score +
        0.10 * kz_norm
    )

    return round(composite * 100, 3)


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def process_instrument(symbol: str) -> dict | None:
    """Process one instrument; return scorecard dict."""
    print(f"[{symbol}] Loading...", flush=True)
    try:
        candles_m15 = parse_tradingview_csv(DATA_DIR / f"{symbol}_M15.csv")
        candles_h1 = parse_tradingview_csv(DATA_DIR / f"{symbol}_H1.csv")
        candles_h4 = parse_tradingview_csv(DATA_DIR / f"{symbol}_H4.csv")
        candles_d1 = parse_tradingview_csv(DATA_DIR / f"{symbol}_D1.csv")
    except FileNotFoundError as e:
        print(f"[{symbol}] CSV missing: {e}", flush=True)
        return None

    if not candles_m15 or not candles_h1:
        print(f"[{symbol}] Empty data", flush=True)
        return None

    s1 = compute_section_1(candles_m15, candles_h1, candles_h4, candles_d1)
    print(f"[{symbol}] S1 done. atr_m15={s1['atr_m15_14']}", flush=True)

    s2_pack = compute_section_2(candles_m15, candles_h1, candles_d1, s1["atr_m15_14"], s1["atr_h1_14"])
    s2 = s2_pack[0]
    h1_swings = s2_pack[1]
    h1_events = s2_pack[2]
    obs = s2_pack[3]
    fvgs_m15 = s2_pack[4]
    print(f"[{symbol}] S2 done. BOS={s2['bos_count']}, OB={s2['ob_count']}, FVG={s2['fvg_count_m15']}", flush=True)

    s3 = compute_section_3(candles_m15, candles_h1, candles_d1, h1_swings, symbol)
    print(f"[{symbol}] S3 done. round_grav={s3['round_number_gravity_pct']}%", flush=True)

    s4 = compute_section_4(candles_m15, candles_h1, h1_swings, h1_events, obs, fvgs_m15, s1["atr_m15_14"], s1["atr_h1_14"])
    print(f"[{symbol}] S4 done. ob_retest_n={s4['ob_retest_candidates']}/wr={s4['ob_retest_wr']:.3f}, sweep_n={s4['sweep_reversal_candidates']}/wr={s4['sweep_reversal_wr']:.3f}", flush=True)

    s6 = compute_section_6(candles_m15)
    print(f"[{symbol}] S6 done. London={s6['london_pct']}%, NY={s6['ny_pct']}%", flush=True)

    s7 = compute_section_7(candles_m15, candles_h1)
    print(f"[{symbol}] S7 done.", flush=True)

    cluster = classify_cluster(symbol)

    scorecard = {
        "symbol": symbol,
        "cluster": cluster,
        "is_live": symbol in LIVE_INSTRUMENTS,
        **s1,
        **s2,
        **s3,
        **s4,
        **s6,
        "monthly_atr_m15_jan": s7["monthly_atr_m15"].get("2026-01", 0),
        "monthly_atr_m15_feb": s7["monthly_atr_m15"].get("2026-02", 0),
        "monthly_atr_m15_mar": s7["monthly_atr_m15"].get("2026-03", 0),
        "monthly_atr_m15_apr": s7["monthly_atr_m15"].get("2026-04", 0),
        "monthly_median_range_jan": s7["monthly_median_range_m15"].get("2026-01", 0),
        "monthly_median_range_feb": s7["monthly_median_range_m15"].get("2026-02", 0),
        "monthly_median_range_mar": s7["monthly_median_range_m15"].get("2026-03", 0),
        "monthly_median_range_apr": s7["monthly_median_range_m15"].get("2026-04", 0),
        "monthly_disp_jan": s7["monthly_displacement_freq"].get("2026-01", 0),
        "monthly_disp_feb": s7["monthly_displacement_freq"].get("2026-02", 0),
        "monthly_disp_mar": s7["monthly_displacement_freq"].get("2026-03", 0),
        "monthly_disp_apr": s7["monthly_displacement_freq"].get("2026-04", 0),
        "monthly_bos_jan": s7["monthly_bos_per_day"].get("2026-01", 0),
        "monthly_bos_feb": s7["monthly_bos_per_day"].get("2026-02", 0),
        "monthly_bos_mar": s7["monthly_bos_per_day"].get("2026-03", 0),
        "monthly_bos_apr": s7["monthly_bos_per_day"].get("2026-04", 0),
    }

    print(f"[{symbol}] DONE", flush=True)
    return scorecard


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80, flush=True)
    print(f"COMPUTING FINGERPRINTS FOR {len(INSTRUMENTS)} INSTRUMENTS", flush=True)
    print("=" * 80, flush=True)

    results = {}
    returns_all: dict[str, dict[str, float]] = {}

    for sym in INSTRUMENTS:
        scorecard = process_instrument(sym)
        if scorecard is None:
            continue
        results[sym] = scorecard

        # Load M15 returns for correlation matrix
        try:
            candles_m15 = parse_tradingview_csv(DATA_DIR / f"{sym}_M15.csv")
            returns_all[sym] = compute_log_returns(candles_m15)
        except Exception as e:
            print(f"[{sym}] returns load fail: {e}", flush=True)

    print("\n[CORRELATION MATRIX] Computing...", flush=True)
    corr_matrix = correlation_matrix(returns_all)

    # Compute avg correlation to live instruments per symbol
    for sym in results:
        corrs = []
        for live in LIVE_INSTRUMENTS:
            if live in corr_matrix.get(sym, {}) and live != sym:
                corrs.append(corr_matrix[sym][live])
        results[sym]["avg_corr_to_live"] = round(statistics.mean(corrs) if corrs else 0.0, 4)
        # Highest correlation to any live instrument
        results[sym]["max_corr_to_live"] = round(max(corrs, key=abs) if corrs else 0.0, 4)

    # Compute composite scores
    print("\n[SCORING] Computing composite...", flush=True)
    max_values = {
        "log_vol": max(math.log10(results[s].get("avg_daily_volume", 0) + 1) for s in results),
        "bos_per_day": max(results[s].get("bos_per_day", 0) for s in results),
        "ob_per_month": max(results[s].get("ob_per_month", 0) for s in results),
        "displacement_freq_m15": max(results[s].get("displacement_freq_m15", 0) for s in results),
    }

    for sym in results:
        results[sym]["composite_score"] = compute_composite_score(results[sym], max_values)

    # Recommendation logic — TIER 1 = composite score quartiles; TIER 2 = downgrades.
    # Composite is well-distributed 50-70 across qualifiers; we want a "STRONG"
    # tier that is genuinely separable, not gating on a single noisy WR threshold.
    composite_scores = sorted([results[s]["composite_score"] for s in results], reverse=True)
    n_results = len(composite_scores)
    p75 = composite_scores[int(n_results * 0.25)]   # top quartile
    p50 = composite_scores[int(n_results * 0.50)]   # median
    p25 = composite_scores[int(n_results * 0.75)]   # bottom quartile

    for sym in results:
        sc = results[sym]
        score = sc["composite_score"]
        ob_n = sc.get("ob_retest_candidates", 0)
        ob_wr = sc.get("ob_retest_wr", 0)
        sweep_n = sc.get("sweep_reversal_candidates", 0)
        sweep_wr = sc.get("sweep_reversal_wr", 0)
        fvg_n = sc.get("fvg_fill_candidates", 0)
        fvg_wr = sc.get("fvg_fill_wr", 0)
        london_ny = sc.get("london_pct", 0) + sc.get("ny_pct", 0)
        bos_per_day = sc.get("bos_per_day", 0)

        reasons = []

        # Hard rejection conditions (insufficient evidence)
        if ob_n < 20 and sweep_n < 100:
            rec = "REJECT"
            reasons.append(f"composite={score:.1f}")
            reasons.append(f"too thin: OB n={ob_n}, sweep n={sweep_n}")
            if bos_per_day < 0.5:
                reasons.append(f"BOS {bos_per_day:.2f}/day = low structural activity")
        # Hard rejection: NO mechanical edge holds at >= breakeven across ANY of the 4
        elif (ob_wr < 0.45 and sweep_wr < 0.40 and fvg_wr < 0.32 and
              sc.get("breaker_re_entry_wr", 0) < 0.45):
            rec = "REJECT"
            reasons.append(f"composite={score:.1f}")
            reasons.append(f"all 4 edges below breakeven (best: OB {ob_wr:.2%}, sweep {sweep_wr:.2%}, FVG {fvg_wr:.2%})")
        # STRONG-CANDIDATE: top quartile composite + at least one edge >= 0.55 + KZ fit
        elif score >= p75 and london_ny >= 45 and (ob_wr >= 0.55 or sweep_wr >= 0.50):
            rec = "STRONG-CANDIDATE"
            reasons.append(f"composite={score:.1f} (top quartile, ≥{p75:.1f})")
            reasons.append(f"OB n={ob_n} WR={ob_wr:.2%}")
            if sweep_wr >= 0.50:
                reasons.append(f"sweep n={sweep_n} WR={sweep_wr:.2%}")
            reasons.append(f"L+NY={london_ny:.1f}%")
        # WORTH-VALIDATING: above median composite, edge fit reasonable
        elif score >= p50 and (ob_n >= 30 or sweep_n >= 200):
            rec = "WORTH-VALIDATING"
            reasons.append(f"composite={score:.1f} (above median {p50:.1f})")
            reasons.append(f"OB n={ob_n} WR={ob_wr:.2%}")
            reasons.append(f"sweep n={sweep_n} WR={sweep_wr:.2%}")
            if london_ny < 50:
                reasons.append(f"L+NY={london_ny:.1f}% — partly outside our windows")
            if ob_wr < 0.48:
                reasons.append(f"OB WR={ob_wr:.2%} sub-breakeven (gold has 62% live; keep eye)")
        # MARGINAL: bottom-half composite OR weak edge fit
        elif score >= p25:
            rec = "MARGINAL"
            reasons.append(f"composite={score:.1f} (below median, in [{p25:.1f}, {p50:.1f}])")
            if ob_wr < 0.48:
                reasons.append(f"OB WR={ob_wr:.2%} sub-breakeven mechanically")
            if london_ny < 45:
                reasons.append(f"L+NY={london_ny:.1f}% — outside our trading windows")
        else:
            rec = "REJECT"
            reasons.append(f"composite={score:.1f} (bottom quartile, <{p25:.1f})")
            if ob_wr < 0.45:
                reasons.append(f"OB WR={ob_wr:.2%}")
            if bos_per_day < 0.6:
                reasons.append(f"BOS {bos_per_day:.2f}/day = thin structure")

        sc["recommendation"] = rec
        sc["reasoning"] = "; ".join(reasons)

    # Write scorecard CSV
    print("\n[WRITE] Scorecard CSV...", flush=True)
    if results:
        # Get all keys from any result, ensure consistent ordering
        sample_keys = list(next(iter(results.values())).keys())
        # Move composite_score, recommendation, reasoning to the end for readability
        for key in ("composite_score", "recommendation", "reasoning"):
            if key in sample_keys:
                sample_keys.remove(key)
                sample_keys.append(key)

        with open(OUT_DIR / "01_per_instrument_scorecard.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sample_keys)
            writer.writeheader()
            for sym in INSTRUMENTS:
                if sym in results:
                    writer.writerow({k: results[sym].get(k, "") for k in sample_keys})

    # Write correlation CSV
    print("[WRITE] Correlation CSV...", flush=True)
    with open(OUT_DIR / "01_correlation_matrix.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        symbols = sorted(corr_matrix.keys())
        writer.writerow([""] + symbols)
        for a in symbols:
            row = [a] + [corr_matrix.get(a, {}).get(b, "") for b in symbols]
            writer.writerow(row)

    # Write ranked CSV
    print("[WRITE] Ranked CSV...", flush=True)
    ranked = sorted(results.values(), key=lambda r: -r["composite_score"])
    with open(OUT_DIR / "01_ranked_candidates.csv", "w", newline="", encoding="utf-8") as f:
        keys = ["symbol", "cluster", "is_live", "composite_score", "recommendation",
                "ob_retest_candidates", "ob_retest_wr", "fvg_fill_candidates", "fvg_fill_wr",
                "breaker_re_entry_candidates", "breaker_re_entry_wr",
                "sweep_reversal_candidates", "sweep_reversal_wr",
                "bos_per_day", "ob_per_month", "displacement_freq_m15",
                "round_number_gravity_pct", "london_pct", "ny_pct", "asian_pct",
                "avg_daily_range", "atr_m15_14", "avg_corr_to_live", "max_corr_to_live",
                "reasoning"]
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in ranked:
            writer.writerow({k: r.get(k, "") for k in keys})

    # Write edge-fit CSV (long format)
    print("[WRITE] Edge-fit CSV...", flush=True)
    with open(OUT_DIR / "01_edge_fit_estimates.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "edge", "candidates", "wins", "losses", "timeouts", "wr", "implied_n_per_month", "n_months"])
        for sym, sc in results.items():
            n_months = sc.get("n_months", 1)
            for edge_key in ("ob_retest", "fvg_fill", "breaker_re_entry", "sweep_reversal"):
                n = sc.get(f"{edge_key}_candidates", 0)
                w = sc.get(f"{edge_key}_wins", 0)
                losses = sc.get(f"{edge_key}_losses", 0)
                t = sc.get(f"{edge_key}_timeouts", 0)
                wr = sc.get(f"{edge_key}_wr", 0)
                writer.writerow([sym, edge_key, n, w, losses, t, wr, round(n / max(n_months, 1), 2), round(n_months, 2)])

    # Persist raw JSON for chart agent + narrative agent
    with open(OUT_DIR / "01_scorecards_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    with open(OUT_DIR / "01_correlation_raw.json", "w", encoding="utf-8") as f:
        json.dump(corr_matrix, f, indent=2)

    print("\n[DONE]", flush=True)
    print(f"Output dir: {OUT_DIR}", flush=True)
    print(f"Total instruments processed: {len(results)}", flush=True)
    print("\nTop 10 by composite score:", flush=True)
    for r in ranked[:10]:
        marker = " (LIVE)" if r["is_live"] else ""
        print(f"  {r['symbol']:<14}{marker:<8} score={r['composite_score']:.2f}  {r['recommendation']}", flush=True)


if __name__ == "__main__":
    main()
