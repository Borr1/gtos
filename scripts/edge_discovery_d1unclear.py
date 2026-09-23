#!/usr/bin/env python3
"""Edge Discovery on D1-Unclear Days — Data Mining Investigation.

Searches for tradeable edges on D1-unclear days that the current system ignores.
Tests 6 edge hypotheses with discovery/validation split, Bonferroni correction,
and rigorous statistical methodology.

Usage:
    python scripts/edge_discovery_d1unclear.py
"""
from __future__ import annotations

import json
import logging
import math
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats as sp_stats

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.historical_data_loader import (
    parse_tradingview_csv,
    compute_session_levels,
    LOOKBACK,
    ASIAN_START,
    ASIAN_END,
    LONDON_OPEN_START,
    LONDON_SESSION_END,
    NY_OPEN_START,
    NY_OPEN_END,
)
from src.components.market_state import (
    detect_swings,
    identify_structure,
    avg_candle_body,
    calculate_atr,
    detect_structure_breaks,
    identify_order_blocks,
    identify_fvgs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "analysis"

# Date splits
DISCOVERY_END = date(2025, 6, 30)
VALIDATION_START = date(2025, 7, 1)

# Bonferroni threshold
BONFERRONI_ALPHA = 0.05 / 6  # = 0.00833

# Kill zone time windows
LONDON_KZ_START = time(7, 0)
LONDON_KZ_END = time(9, 30)
NY_KZ_START = time(13, 0)
NY_KZ_END = time(15, 30)


# ═══════════════════════════════════════════════════════════════════════
# Utility functions
# ═══════════════════════════════════════════════════════════════════════

def _previous_weekday(d: date) -> date:
    prev = d - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


def _get_trading_dates(m15_candles: list[dict]) -> list[date]:
    """Extract unique trading dates from M15 candles (weekdays only)."""
    dates = set()
    for c in m15_candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        d = dt.date()
        if d.weekday() < 5:
            dates.add(d)
    return sorted(dates)


def _candles_for_date_range(candles: list[dict], start_dt: datetime, end_dt: datetime) -> list[dict]:
    """Filter candles within a datetime range."""
    result = []
    for c in candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if start_dt <= dt < end_dt:
            result.append(c)
    return result


def _candles_on_date(candles: list[dict], target: date) -> list[dict]:
    """Get all candles on a specific date."""
    result = []
    for c in candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt.date() == target:
            result.append(c)
    return result


def _candles_before_datetime(candles: list[dict], before_dt: datetime, count: int) -> list[dict]:
    """Get last `count` candles before a datetime."""
    filtered = []
    for c in candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt < before_dt:
            filtered.append(c)
    return filtered[-count:] if len(filtered) >= count else filtered


def _candles_after_datetime(candles: list[dict], after_dt: datetime, count: int) -> list[dict]:
    """Get first `count` candles after (inclusive) a datetime."""
    filtered = []
    for c in candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt >= after_dt:
            filtered.append(c)
            if len(filtered) >= count:
                break
    return filtered


def _compute_mfe_mae(candles_forward: list[dict], direction: str, entry_price: float):
    """Compute MFE and MAE from entry price over forward candles."""
    mfe = 0.0
    mae = 0.0
    for c in candles_forward:
        if direction == "bullish":
            fav = c["high"] - entry_price
            adv = entry_price - c["low"]
        else:
            fav = entry_price - c["low"]
            adv = c["high"] - entry_price
        mfe = max(mfe, fav)
        mae = max(mae, adv)
    return mfe, mae


def _check_continuation(candles_forward: list[dict], direction: str,
                         entry_price: float, sl_distance: float,
                         target_multiple: float = 1.5) -> bool:
    """Check if price reached target_multiple * sl_distance in expected direction."""
    target_dist = sl_distance * target_multiple
    for c in candles_forward:
        if direction == "bullish":
            if c["high"] - entry_price >= target_dist:
                return True
        else:
            if entry_price - c["low"] >= target_dist:
                return True
    return False


def _binomial_test(hits: int, n: int, p0: float = 0.5):
    """One-sided binomial test: H_a: p > p0. Returns p-value."""
    if n == 0:
        return 1.0
    result = sp_stats.binomtest(hits, n, p0, alternative='greater')
    return result.pvalue


def _confidence_interval(hits: int, n: int, confidence: float = 0.95):
    """Wilson score confidence interval for proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = sp_stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = hits / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0, center - spread), min(1, center + spread))


def _is_displacement(candle: dict, avg_body: float, threshold: float = 1.5) -> bool:
    """Check if candle body is >= threshold * avg_body."""
    body = abs(candle["close"] - candle["open"])
    return body >= threshold * avg_body if avg_body > 0 else False


def _candle_direction(candle: dict) -> str:
    """Return 'bullish' or 'bearish' based on candle close vs open."""
    return "bullish" if candle["close"] > candle["open"] else "bearish"


def _get_kz_name(dt: datetime) -> Optional[str]:
    """Return kill zone name or None."""
    t = dt.time()
    if LONDON_KZ_START <= t < LONDON_KZ_END:
        return "london"
    elif NY_KZ_START <= t < NY_KZ_END:
        return "ny"
    return None


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0: Day Classification
# ═══════════════════════════════════════════════════════════════════════

def classify_trading_days(symbol: str, all_candles: dict[str, list[dict]]) -> list[dict]:
    """Classify every trading day by D1/H4/H1 structure."""
    logger.info(f"Classifying trading days for {symbol}...")

    d1_candles = all_candles["D1"]
    h4_candles = all_candles["H4"]
    h1_candles = all_candles["H1"]
    m15_candles = all_candles["M15"]

    trading_dates = _get_trading_dates(m15_candles)
    classifications = []

    for td in trading_dates:
        td_dt = datetime.combine(td, time(7, 0), tzinfo=timezone.utc)

        # D1: get last 30 D1 candles before this date
        d1_before = [c for c in d1_candles
                     if datetime.fromisoformat(c["time"].replace("Z", "+00:00")).date() < td]
        d1_slice = d1_before[-30:] if len(d1_before) >= 30 else d1_before

        # H4: get last 80 H4 candles before London open
        h4_slice = _candles_before_datetime(h4_candles, td_dt, 80)

        # H1: get last 168 H1 candles before London open
        h1_slice = _candles_before_datetime(h1_candles, td_dt, 168)

        if len(d1_slice) < 5 or len(h4_slice) < 10 or len(h1_slice) < 10:
            continue

        # Compute structures
        d1_swings = detect_swings(d1_slice, min_bars=2)
        d1_structure = identify_structure(d1_swings)

        h4_swings = detect_swings(h4_slice, min_bars=2)
        h4_structure = identify_structure(h4_swings)

        h1_swings = detect_swings(h1_slice, min_bars=2)
        h1_structure = identify_structure(h1_swings)

        # D1 classification
        d1_dir = d1_structure.direction
        h4_dir = h4_structure.direction
        h1_dir = h1_structure.direction

        d1_clear = d1_dir in ("bullish", "bearish")
        h4_clear = h4_dir in ("bullish", "bearish")
        h1_clear = h1_dir in ("bullish", "bearish")

        # Category assignment
        if d1_clear and h4_clear and h4_dir == d1_dir:
            category = "PASS"
        elif not d1_clear and h4_clear and h1_clear and h4_dir == h1_dir:
            category = "CAT1"
        elif not d1_clear and not h4_clear:
            category = "CAT2"
        elif h4_clear and h1_clear and h4_dir != h1_dir:
            category = "CAT3"
        elif d1_clear and h4_clear and h4_dir != d1_dir:
            category = "CAT3"
        else:
            category = "CAT4"

        classifications.append({
            "date": td.isoformat(),
            "symbol": symbol,
            "d1_direction": d1_dir,
            "h4_direction": h4_dir,
            "h1_direction": h1_dir,
            "d1_clear": d1_clear,
            "category": category,
        })

    logger.info(f"  Classified {len(classifications)} days for {symbol}")
    cats = Counter(c["category"] for c in classifications)
    logger.info(f"  Categories: {dict(cats)}")
    d1s = Counter(c["d1_direction"] for c in classifications)
    logger.info(f"  D1 directions: {dict(d1s)}")

    return classifications


# ═══════════════════════════════════════════════════════════════════════
# PHASE 0.2: Baseline Displacement Quality Comparison
# ═══════════════════════════════════════════════════════════════════════

def baseline_displacement_comparison(disp_db: list[dict]) -> dict:
    """Compare displacement quality on D1-clear vs D1-unclear days."""
    logger.info("Computing baseline displacement comparison...")

    d1_clear_disps = [d for d in disp_db if d["d1_dir"] in ("bullish", "bearish")]
    d1_unclear_disps = [d for d in disp_db if d["d1_dir"] not in ("bullish", "bearish")]

    def _metrics(disps: list[dict]) -> dict:
        if not disps:
            return {"n": 0}
        dates = set(d["date"] for d in disps)
        cont_3h = sum(1 for d in disps if d.get("cont_3h", False))
        mfes = [d["mfe_3h"] for d in disps if d.get("mfe_3h") is not None]
        maes = [d["mae_3h"] for d in disps if d.get("mae_3h") is not None]
        body_ratios = [d["body_ratio"] for d in disps]
        return {
            "n": len(disps),
            "unique_dates": len(dates),
            "disps_per_date": round(len(disps) / len(dates), 2) if dates else 0,
            "avg_body_ratio": round(np.mean(body_ratios), 3),
            "median_body_ratio": round(np.median(body_ratios), 3),
            "continuation_rate_3h": round(cont_3h / len(disps), 4) if disps else 0,
            "cont_3h_hits": cont_3h,
            "avg_mfe_3h": round(np.mean(mfes), 2) if mfes else 0,
            "avg_mae_3h": round(np.mean(maes), 2) if maes else 0,
            "mfe_mae_ratio": round(np.mean(mfes) / np.mean(maes), 3) if maes and np.mean(maes) > 0 else 0,
        }

    clear_metrics = _metrics(d1_clear_disps)
    unclear_metrics = _metrics(d1_unclear_disps)

    # Mann-Whitney U test for continuation rates (binary outcomes)
    if clear_metrics["n"] > 20 and unclear_metrics["n"] > 20:
        clear_cont = [1 if d.get("cont_3h", False) else 0 for d in d1_clear_disps]
        unclear_cont = [1 if d.get("cont_3h", False) else 0 for d in d1_unclear_disps]
        u_stat, p_val = sp_stats.mannwhitneyu(clear_cont, unclear_cont, alternative='two-sided')
        quality_diff_p = round(p_val, 6)
    else:
        quality_diff_p = None

    return {
        "d1_clear": clear_metrics,
        "d1_unclear": unclear_metrics,
        "quality_difference_p_value": quality_diff_p,
    }


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS TESTING FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════

class HypothesisResult:
    """Container for hypothesis test results."""
    def __init__(self, hypothesis_id: int, name: str):
        self.id = hypothesis_id
        self.name = name
        self.signals: list[dict] = []

    def add_signal(self, signal: dict):
        self.signals.append(signal)

    def compute_stats(self, period: str = "all") -> dict:
        """Compute stats for signals in a given period."""
        if period == "discovery":
            sigs = [s for s in self.signals if date.fromisoformat(s["date"]) <= DISCOVERY_END]
        elif period == "validation":
            sigs = [s for s in self.signals if date.fromisoformat(s["date"]) >= VALIDATION_START]
        else:
            sigs = self.signals

        n = len(sigs)
        if n == 0:
            return {"n": 0, "insufficient": True}

        hits = sum(1 for s in sigs if s["continuation"])
        cont_rate = hits / n
        p_value = _binomial_test(hits, n, 0.5)
        ci_low, ci_high = _confidence_interval(hits, n)

        mfes = [s["mfe"] for s in sigs if s["mfe"] is not None]
        maes = [s["mae"] for s in sigs if s["mae"] is not None]
        r_multiples = [s.get("r_multiple", 0) for s in sigs if s.get("r_multiple") is not None]

        return {
            "n": n,
            "insufficient": n < 20,
            "hits": hits,
            "continuation_rate": round(cont_rate, 4),
            "p_value": round(p_value, 6),
            "significant_bonferroni": p_value < BONFERRONI_ALPHA,
            "ci_95": (round(ci_low, 4), round(ci_high, 4)),
            "avg_mfe": round(np.mean(mfes), 2) if mfes else 0,
            "avg_mae": round(np.mean(maes), 2) if maes else 0,
            "mfe_mae_ratio": round(np.mean(mfes) / np.mean(maes), 3) if maes and np.mean(maes) > 0 else 0,
            "avg_r_multiple": round(np.mean(r_multiples), 3) if r_multiples else 0,
            "edge_score": round((cont_rate - 0.5) * math.sqrt(n), 3) if n > 0 else 0,
        }

    def get_verdict(self) -> str:
        disc = self.compute_stats("discovery")
        val = self.compute_stats("validation")

        if disc.get("insufficient") or val.get("insufficient"):
            return "INSUFFICIENT_DATA"

        if (disc["continuation_rate"] > 0.5 and val["continuation_rate"] > 0.5
                and disc["p_value"] < BONFERRONI_ALPHA):
            return "GREEN"
        elif (disc["continuation_rate"] > 0.5 and val["continuation_rate"] > 0.5
              and disc["p_value"] < 0.05):
            return "YELLOW"
        else:
            return "RED"


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 1: Session Sweep Reversal
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_1(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H1: Session Sweep Reversal on D1-Unclear Days."""
    logger.info(f"Testing H1: Session Sweep Reversal for {symbol}...")
    result = HypothesisResult(1, "Session Sweep Reversal")

    m15_candles = all_candles["M15"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        # Compute session levels
        session_levels = compute_session_levels(m15_candles, td)
        if session_levels["asian_high"] == 0 or session_levels["pdh"] == 0:
            continue

        levels = {
            "asian_high": session_levels["asian_high"],
            "asian_low": session_levels["asian_low"],
            "pdh": session_levels["pdh"],
            "pdl": session_levels["pdl"],
        }

        # Scan London and NY kill zones
        for kz_name, kz_start, kz_end in [
            ("london", time(7, 0), time(9, 30)),
            ("ny", time(13, 0), time(15, 30)),
        ]:
            kz_start_dt = datetime.combine(td, kz_start, tzinfo=timezone.utc)
            kz_end_dt = datetime.combine(td, kz_end, tzinfo=timezone.utc)

            kz_candles = _candles_for_date_range(m15_candles, kz_start_dt, kz_end_dt)
            if len(kz_candles) < 3:
                continue

            # Get avg body for displacement check
            pre_kz_candles = _candles_before_datetime(m15_candles, kz_start_dt, 20)
            avg_body_val = avg_candle_body(pre_kz_candles) if pre_kz_candles else 1.0

            for i, candle in enumerate(kz_candles):
                c_dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))

                for level_name, level_price in levels.items():
                    if level_price <= 0:
                        continue

                    # Check sweep: wick extends beyond level, body closes back
                    is_high_level = level_name in ("asian_high", "pdh")

                    if is_high_level:
                        sweep_occurred = (candle["high"] > level_price and
                                         candle["close"] < level_price)
                    else:
                        sweep_occurred = (candle["low"] < level_price and
                                         candle["close"] > level_price)

                    if not sweep_occurred:
                        continue

                    # Check displacement on sweep candle or next candle
                    disp_candle = None
                    if _is_displacement(candle, avg_body_val):
                        disp_candle = candle
                    elif i + 1 < len(kz_candles) and _is_displacement(kz_candles[i + 1], avg_body_val):
                        disp_candle = kz_candles[i + 1]

                    if disp_candle is None:
                        continue

                    # Determine direction: sweep of high level = bearish reversal
                    if is_high_level:
                        expected_dir = "bearish"
                        disp_dir = _candle_direction(disp_candle)
                        if disp_dir != "bearish":
                            continue
                    else:
                        expected_dir = "bullish"
                        disp_dir = _candle_direction(disp_candle)
                        if disp_dir != "bullish":
                            continue

                    # Signal is the close of the displacement candle
                    entry_price = disp_candle["close"]
                    sl_price = candle["high"] if is_high_level else candle["low"]
                    sl_distance = abs(entry_price - sl_price)

                    if sl_distance <= 0:
                        continue

                    # Walk forward 3 hours (12 M15 candles)
                    disp_dt = datetime.fromisoformat(disp_candle["time"].replace("Z", "+00:00"))
                    fwd_start = disp_dt + timedelta(minutes=15)
                    fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

                    if len(fwd_candles) < 3:
                        continue

                    mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
                    continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

                    r_multiple = (mfe - mae) / sl_distance if sl_distance > 0 else 0

                    result.add_signal({
                        "date": td_str,
                        "time": disp_candle["time"],
                        "symbol": symbol,
                        "level_swept": level_name,
                        "kill_zone": kz_name,
                        "direction": expected_dir,
                        "entry_price": entry_price,
                        "sl_price": sl_price,
                        "sl_distance": round(sl_distance, 2),
                        "displacement_ratio": round(abs(disp_candle["close"] - disp_candle["open"]) / avg_body_val, 2),
                        "mfe": round(mfe, 2),
                        "mae": round(mae, 2),
                        "continuation": continuation,
                        "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                        "d1_clear": day_info["d1_clear"],
                        "category": day_info["category"],
                    })

    logger.info(f"  H1: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 2: FVG Fill Entry
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_2(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H2: FVG Fill Entry on D1-Unclear Days."""
    logger.info(f"Testing H2: FVG Fill Entry for {symbol}...")
    result = HypothesisResult(2, "FVG Fill Entry")

    m15_candles = all_candles["M15"]
    h1_candles = all_candles["H1"]
    h4_candles = all_candles["H4"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    # Minimum FVG size based on instrument
    min_fvg = 1.0 if symbol == "XAUUSD" else 0.0005

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        for kz_name, kz_start_t, kz_end_t in [
            ("london", time(7, 0), time(9, 30)),
            ("ny", time(13, 0), time(15, 30)),
        ]:
            kz_start_dt = datetime.combine(td, kz_start_t, tzinfo=timezone.utc)
            kz_end_dt = datetime.combine(td, kz_end_t, tzinfo=timezone.utc)

            # Get H1 candles up to KZ start for FVG detection
            h1_before = _candles_before_datetime(h1_candles, kz_start_dt, 50)
            if len(h1_before) < 5:
                continue

            # Get H4 structure for premium/discount context
            h4_before = _candles_before_datetime(h4_candles, kz_start_dt, 80)
            if len(h4_before) < 10:
                continue

            h4_swings = detect_swings(h4_before, min_bars=2)
            h4_structure = identify_structure(h4_swings)

            # Detect H1 FVGs
            fvgs = identify_fvgs(h1_before, min_fvg)
            unfilled_fvgs = [f for f in fvgs if not f.filled]

            if not unfilled_fvgs:
                continue

            # Get M15 candles during KZ
            kz_candles = _candles_for_date_range(m15_candles, kz_start_dt, kz_end_dt)
            if len(kz_candles) < 3:
                continue

            pre_kz = _candles_before_datetime(m15_candles, kz_start_dt, 20)
            avg_body_val = avg_candle_body(pre_kz) if pre_kz else 1.0

            for fvg in unfilled_fvgs:
                for i, candle in enumerate(kz_candles):
                    # Check if price enters FVG zone
                    price_in_fvg = (candle["low"] <= fvg.top and candle["high"] >= fvg.bottom)
                    if not price_in_fvg:
                        continue

                    # Check for displacement out of FVG
                    if not _is_displacement(candle, avg_body_val):
                        continue

                    c_dir = _candle_direction(candle)

                    # FVG type alignment check
                    if fvg.type == "bullish" and c_dir != "bullish":
                        continue
                    if fvg.type == "bearish" and c_dir != "bearish":
                        continue

                    # H4 alignment check (not D1)
                    h4_aligned = False
                    if fvg.type == "bullish" and h4_structure.direction == "bullish":
                        h4_aligned = True
                    elif fvg.type == "bearish" and h4_structure.direction == "bearish":
                        h4_aligned = True

                    entry_price = candle["close"]
                    if fvg.type == "bullish":
                        sl_price = fvg.bottom
                        expected_dir = "bullish"
                    else:
                        sl_price = fvg.top
                        expected_dir = "bearish"

                    sl_distance = abs(entry_price - sl_price)
                    if sl_distance <= 0:
                        continue

                    c_dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
                    fwd_start = c_dt + timedelta(minutes=15)
                    fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

                    if len(fwd_candles) < 3:
                        continue

                    mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
                    continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

                    result.add_signal({
                        "date": td_str,
                        "time": candle["time"],
                        "symbol": symbol,
                        "fvg_type": fvg.type,
                        "kill_zone": kz_name,
                        "direction": expected_dir,
                        "entry_price": entry_price,
                        "sl_price": sl_price,
                        "sl_distance": round(sl_distance, 2),
                        "displacement_ratio": round(abs(candle["close"] - candle["open"]) / avg_body_val, 2),
                        "h4_aligned": h4_aligned,
                        "mfe": round(mfe, 2),
                        "mae": round(mae, 2),
                        "continuation": continuation,
                        "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                        "d1_clear": day_info["d1_clear"],
                        "category": day_info["category"],
                    })
                    break  # One signal per FVG per KZ

    logger.info(f"  H2: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 3: Asian Range Sweep → London Continuation
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_3(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H3: Asian Range Sweep → London Continuation."""
    logger.info(f"Testing H3: Asian Sweep London Continuation for {symbol}...")
    result = HypothesisResult(3, "Asian Sweep London Continuation")

    m15_candles = all_candles["M15"]
    d1_candles = all_candles["D1"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        # Compute session levels
        session_levels = compute_session_levels(m15_candles, td)
        asian_high = session_levels["asian_high"]
        asian_low = session_levels["asian_low"]

        if asian_high == 0 or asian_low == 0 or asian_high <= asian_low:
            continue

        asian_range = asian_high - asian_low

        # Filter: Asian range >= 28% of 14-period ADR
        d1_before = [c for c in d1_candles
                     if datetime.fromisoformat(c["time"].replace("Z", "+00:00")).date() < td]
        d1_slice = d1_before[-14:] if len(d1_before) >= 14 else d1_before
        if len(d1_slice) < 5:
            continue

        adr = calculate_atr(d1_slice, period=14)
        if adr > 0 and asian_range < 0.28 * adr:
            continue  # Narrow range, skip per fp_001

        # Scan first 90 min of London (07:00 - 08:30)
        london_start = datetime.combine(td, time(7, 0), tzinfo=timezone.utc)
        london_90 = datetime.combine(td, time(8, 30), tzinfo=timezone.utc)

        london_candles = _candles_for_date_range(m15_candles, london_start, london_90)
        if len(london_candles) < 2:
            continue

        pre_london = _candles_before_datetime(m15_candles, london_start, 20)
        avg_body_val = avg_candle_body(pre_london) if pre_london else 1.0

        for i, candle in enumerate(london_candles):
            swept_high = candle["high"] > asian_high
            swept_low = candle["low"] < asian_low

            if not swept_high and not swept_low:
                continue

            if not _is_displacement(candle, avg_body_val):
                continue

            c_dir = _candle_direction(candle)

            # Determine sub-type and direction
            if swept_high and c_dir == "bearish":
                sub_type = "reversal"
                expected_dir = "bearish"
            elif swept_low and c_dir == "bullish":
                sub_type = "reversal"
                expected_dir = "bullish"
            elif swept_high and c_dir == "bullish":
                sub_type = "continuation"
                expected_dir = "bullish"
            elif swept_low and c_dir == "bearish":
                sub_type = "continuation"
                expected_dir = "bearish"
            else:
                continue

            entry_price = candle["close"]
            # SL = Asian range extreme opposite to trade direction
            if expected_dir == "bullish":
                sl_price = asian_low
            else:
                sl_price = asian_high

            sl_distance = abs(entry_price - sl_price)
            if sl_distance <= 0:
                continue

            c_dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
            fwd_start = c_dt + timedelta(minutes=15)
            fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

            if len(fwd_candles) < 3:
                continue

            mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
            continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

            # Also check: which level swept
            level_swept = "asian_high" if swept_high else "asian_low"

            result.add_signal({
                "date": td_str,
                "time": candle["time"],
                "symbol": symbol,
                "level_swept": level_swept,
                "sub_type": sub_type,
                "direction": expected_dir,
                "entry_price": entry_price,
                "sl_price": sl_price,
                "sl_distance": round(sl_distance, 2),
                "asian_range": round(asian_range, 2),
                "asian_range_pct_adr": round(asian_range / adr * 100, 1) if adr > 0 else 0,
                "displacement_ratio": round(abs(candle["close"] - candle["open"]) / avg_body_val, 2),
                "mfe": round(mfe, 2),
                "mae": round(mae, 2),
                "continuation": continuation,
                "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                "d1_clear": day_info["d1_clear"],
                "category": day_info["category"],
            })
            break  # One signal per day for this hypothesis

    logger.info(f"  H3: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 4: H4-Anchored OB Retest (D1 Removed)
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_4(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H4: H4-Anchored OB Retest with D1 requirement removed. CAT1 dates only."""
    logger.info(f"Testing H4: H4-Anchored OB Retest for {symbol}...")
    result = HypothesisResult(4, "H4-Anchored OB Retest (D1 Removed)")

    m15_candles = all_candles["M15"]
    h1_candles = all_candles["H1"]
    h4_candles = all_candles["H4"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        # Only CAT1 dates (D1 unclear, H4+H1 aligned)
        if day_info["category"] != "CAT1":
            continue

        h4_dir = day_info["h4_direction"]
        if h4_dir not in ("bullish", "bearish"):
            continue

        for kz_name, kz_start_t, kz_end_t in [
            ("london", time(7, 0), time(9, 30)),
            ("ny", time(13, 0), time(15, 30)),
        ]:
            kz_start_dt = datetime.combine(td, kz_start_t, tzinfo=timezone.utc)
            kz_end_dt = datetime.combine(td, kz_end_t, tzinfo=timezone.utc)

            # H1 OB detection
            h1_before = _candles_before_datetime(h1_candles, kz_start_dt, 168)
            if len(h1_before) < 20:
                continue

            h1_swings = detect_swings(h1_before, min_bars=2)
            h1_structure = identify_structure(h1_swings)

            # H1 must be aligned with H4
            if h1_structure.direction != h4_dir:
                continue

            h1_events = detect_structure_breaks(h1_before, h1_swings, h1_structure)
            h1_obs = identify_order_blocks(h1_before, h1_events)

            # Find unmitigated H1 OBs in correct direction
            target_obs = [ob for ob in h1_obs if ob.type == h4_dir and not ob.mitigated]
            if not target_obs:
                continue

            # Get M15 candles during KZ
            kz_candles = _candles_for_date_range(m15_candles, kz_start_dt, kz_end_dt)
            if len(kz_candles) < 3:
                continue

            pre_kz = _candles_before_datetime(m15_candles, kz_start_dt, 20)
            avg_body_val = avg_candle_body(pre_kz) if pre_kz else 1.0

            for ob in target_obs:
                for i, candle in enumerate(kz_candles):
                    # Check price pullback to OB zone
                    if h4_dir == "bullish":
                        at_ob = candle["low"] <= ob.high and candle["low"] >= ob.low
                    else:
                        at_ob = candle["high"] >= ob.low and candle["high"] <= ob.high

                    if not at_ob:
                        continue

                    # Check displacement from OB
                    if not _is_displacement(candle, avg_body_val):
                        continue

                    c_dir = _candle_direction(candle)
                    if c_dir != h4_dir:
                        continue

                    entry_price = candle["close"]
                    if h4_dir == "bullish":
                        sl_price = ob.low
                        expected_dir = "bullish"
                    else:
                        sl_price = ob.high
                        expected_dir = "bearish"

                    sl_distance = abs(entry_price - sl_price)
                    if sl_distance <= 0:
                        continue

                    c_dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
                    fwd_start = c_dt + timedelta(minutes=15)
                    fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

                    if len(fwd_candles) < 3:
                        continue

                    mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
                    continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

                    # H4 trend strength: count BOS events in last 20 H4 candles
                    h4_before = _candles_before_datetime(h4_candles, kz_start_dt, 20)
                    h4_sw = detect_swings(h4_before, min_bars=2)
                    h4_st = identify_structure(h4_sw)
                    h4_events = detect_structure_breaks(h4_before, h4_sw, h4_st)
                    h4_bos_count = sum(1 for e in h4_events if e.type == "BOS")

                    result.add_signal({
                        "date": td_str,
                        "time": candle["time"],
                        "symbol": symbol,
                        "kill_zone": kz_name,
                        "direction": expected_dir,
                        "entry_price": entry_price,
                        "sl_price": sl_price,
                        "sl_distance": round(sl_distance, 2),
                        "displacement_ratio": round(abs(candle["close"] - candle["open"]) / avg_body_val, 2),
                        "h4_bos_count": h4_bos_count,
                        "mfe": round(mfe, 2),
                        "mae": round(mae, 2),
                        "continuation": continuation,
                        "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                        "d1_clear": False,  # Always CAT1
                        "category": "CAT1",
                    })
                    break  # One signal per OB per KZ

    logger.info(f"  H4: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 5: Multi-Sweep Confluence
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_5(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H5: Multi-Sweep Confluence."""
    logger.info(f"Testing H5: Multi-Sweep Confluence for {symbol}...")
    result = HypothesisResult(5, "Multi-Sweep Confluence")

    m15_candles = all_candles["M15"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        session_levels = compute_session_levels(m15_candles, td)
        if session_levels["asian_high"] == 0 or session_levels["pdh"] == 0:
            continue

        levels = {
            "asian_high": session_levels["asian_high"],
            "asian_low": session_levels["asian_low"],
            "pdh": session_levels["pdh"],
            "pdl": session_levels["pdl"],
        }

        for kz_name, kz_start_t, kz_end_t in [
            ("london", time(7, 0), time(9, 30)),
            ("ny", time(13, 0), time(15, 30)),
        ]:
            kz_start_dt = datetime.combine(td, kz_start_t, tzinfo=timezone.utc)
            kz_end_dt = datetime.combine(td, kz_end_t, tzinfo=timezone.utc)

            kz_candles = _candles_for_date_range(m15_candles, kz_start_dt, kz_end_dt)
            if len(kz_candles) < 3:
                continue

            pre_kz = _candles_before_datetime(m15_candles, kz_start_dt, 20)
            avg_body_val = avg_candle_body(pre_kz) if pre_kz else 1.0

            # Track sweeps during this KZ window
            swept_levels: dict[str, dict] = {}  # level_name -> {candle, extreme}

            for i, candle in enumerate(kz_candles):
                for level_name, level_price in levels.items():
                    if level_price <= 0:
                        continue

                    is_high = level_name in ("asian_high", "pdh")

                    if is_high:
                        if candle["high"] > level_price:
                            if level_name not in swept_levels:
                                swept_levels[level_name] = {
                                    "candle": candle,
                                    "extreme": candle["high"],
                                    "index": i,
                                }
                    else:
                        if candle["low"] < level_price:
                            if level_name not in swept_levels:
                                swept_levels[level_name] = {
                                    "candle": candle,
                                    "extreme": candle["low"],
                                    "index": i,
                                }

                # Check if we have multi-sweep (2+)
                if len(swept_levels) >= 2:
                    # Check displacement on current or next candle
                    disp_candle = None
                    if _is_displacement(candle, avg_body_val):
                        disp_candle = candle
                    elif i + 1 < len(kz_candles) and _is_displacement(kz_candles[i + 1], avg_body_val):
                        disp_candle = kz_candles[i + 1]

                    if disp_candle is None:
                        continue

                    c_dir = _candle_direction(disp_candle)

                    # Determine expected direction based on which levels were swept
                    high_levels_swept = [k for k in swept_levels if k in ("asian_high", "pdh")]
                    low_levels_swept = [k for k in swept_levels if k in ("asian_low", "pdl")]

                    if high_levels_swept and c_dir == "bearish":
                        expected_dir = "bearish"
                    elif low_levels_swept and c_dir == "bullish":
                        expected_dir = "bullish"
                    else:
                        continue

                    entry_price = disp_candle["close"]
                    # SL = furthest sweep extreme
                    if expected_dir == "bearish":
                        sl_price = max(s["extreme"] for s in swept_levels.values())
                    else:
                        sl_price = min(s["extreme"] for s in swept_levels.values())

                    sl_distance = abs(entry_price - sl_price)
                    if sl_distance <= 0:
                        continue

                    d_dt = datetime.fromisoformat(disp_candle["time"].replace("Z", "+00:00"))
                    fwd_start = d_dt + timedelta(minutes=15)
                    fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

                    if len(fwd_candles) < 3:
                        continue

                    mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
                    continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

                    result.add_signal({
                        "date": td_str,
                        "time": disp_candle["time"],
                        "symbol": symbol,
                        "levels_swept": list(swept_levels.keys()),
                        "num_levels_swept": len(swept_levels),
                        "kill_zone": kz_name,
                        "direction": expected_dir,
                        "entry_price": entry_price,
                        "sl_price": sl_price,
                        "sl_distance": round(sl_distance, 2),
                        "displacement_ratio": round(abs(disp_candle["close"] - disp_candle["open"]) / avg_body_val, 2),
                        "mfe": round(mfe, 2),
                        "mae": round(mae, 2),
                        "continuation": continuation,
                        "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                        "d1_clear": day_info["d1_clear"],
                        "category": day_info["category"],
                    })
                    break  # One signal per KZ for multi-sweep

    logger.info(f"  H5: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# HYPOTHESIS 6: Previous Day Range Extremes on Ranging Days
# ═══════════════════════════════════════════════════════════════════════

def test_hypothesis_6(symbol: str, all_candles: dict[str, list[dict]],
                       day_class: list[dict]) -> HypothesisResult:
    """H6: Previous Day Range Extreme Sweep → Mean Reversion on D1-Unclear Days."""
    logger.info(f"Testing H6: PD Range Extreme Reversion for {symbol}...")
    result = HypothesisResult(6, "PD Range Extreme Reversion")

    m15_candles = all_candles["M15"]
    trading_dates = _get_trading_dates(m15_candles)
    day_map = {d["date"]: d for d in day_class if d["symbol"] == symbol}

    for td in trading_dates:
        td_str = td.isoformat()
        day_info = day_map.get(td_str)
        if not day_info:
            continue

        # D1-UNCLEAR only
        if day_info["d1_clear"]:
            continue

        session_levels = compute_session_levels(m15_candles, td)
        pdh = session_levels["pdh"]
        pdl = session_levels["pdl"]

        if pdh <= 0 or pdl <= 0 or pdh <= pdl:
            continue

        pd_mid = (pdh + pdl) / 2
        pd_range = pdh - pdl

        for kz_name, kz_start_t, kz_end_t in [
            ("london", time(7, 0), time(9, 30)),
            ("ny", time(13, 0), time(15, 30)),
        ]:
            kz_start_dt = datetime.combine(td, kz_start_t, tzinfo=timezone.utc)
            kz_end_dt = datetime.combine(td, kz_end_t, tzinfo=timezone.utc)

            kz_candles = _candles_for_date_range(m15_candles, kz_start_dt, kz_end_dt)
            if len(kz_candles) < 3:
                continue

            pre_kz = _candles_before_datetime(m15_candles, kz_start_dt, 20)
            avg_body_val = avg_candle_body(pre_kz) if pre_kz else 1.0

            for i, candle in enumerate(kz_candles):
                # Check sweep of PDH or PDL
                swept_pdh = candle["high"] > pdh
                swept_pdl = candle["low"] < pdl

                if not swept_pdh and not swept_pdl:
                    continue

                # Check displacement back inside range (reversal)
                if not _is_displacement(candle, avg_body_val):
                    continue

                c_dir = _candle_direction(candle)

                if swept_pdh and c_dir == "bearish":
                    expected_dir = "bearish"
                    level_swept = "pdh"
                    sl_price = candle["high"]
                elif swept_pdl and c_dir == "bullish":
                    expected_dir = "bullish"
                    level_swept = "pdl"
                    sl_price = candle["low"]
                else:
                    continue

                entry_price = candle["close"]
                sl_distance = abs(entry_price - sl_price)
                if sl_distance <= 0:
                    continue

                c_dt = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
                fwd_start = c_dt + timedelta(minutes=15)
                fwd_candles = _candles_after_datetime(m15_candles, fwd_start, 12)

                if len(fwd_candles) < 3:
                    continue

                mfe, mae = _compute_mfe_mae(fwd_candles, expected_dir, entry_price)
                continuation = _check_continuation(fwd_candles, expected_dir, entry_price, sl_distance)

                # Also check if price returned to mid-range
                reached_mid = False
                for fc in fwd_candles:
                    if expected_dir == "bearish" and fc["low"] <= pd_mid:
                        reached_mid = True
                        break
                    elif expected_dir == "bullish" and fc["high"] >= pd_mid:
                        reached_mid = True
                        break

                result.add_signal({
                    "date": td_str,
                    "time": candle["time"],
                    "symbol": symbol,
                    "level_swept": level_swept,
                    "kill_zone": kz_name,
                    "direction": expected_dir,
                    "entry_price": entry_price,
                    "sl_price": sl_price,
                    "sl_distance": round(sl_distance, 2),
                    "pd_mid": round(pd_mid, 2),
                    "pd_range": round(pd_range, 2),
                    "reached_mid_range": reached_mid,
                    "displacement_ratio": round(abs(candle["close"] - candle["open"]) / avg_body_val, 2),
                    "mfe": round(mfe, 2),
                    "mae": round(mae, 2),
                    "continuation": continuation,
                    "r_multiple": round(mfe / sl_distance if sl_distance > 0 else 0, 3),
                    "d1_clear": False,
                    "category": day_info["category"],
                })
                break  # One signal per KZ

    logger.info(f"  H6: {len(result.signals)} signals found")
    return result


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: Cross-Hypothesis Analysis
# ═══════════════════════════════════════════════════════════════════════

def cross_hypothesis_analysis(hypotheses: list[HypothesisResult]) -> dict:
    """Analyze overlap, frequency, and ranking across hypotheses."""
    logger.info("Running cross-hypothesis analysis...")

    # 1. Rank by edge quality
    rankings = []
    for h in hypotheses:
        val_stats = h.compute_stats("validation")
        disc_stats = h.compute_stats("discovery")
        rankings.append({
            "id": h.id,
            "name": h.name,
            "discovery_n": disc_stats["n"],
            "discovery_rate": disc_stats.get("continuation_rate", 0),
            "validation_n": val_stats["n"],
            "validation_rate": val_stats.get("continuation_rate", 0),
            "edge_score": val_stats.get("edge_score", 0),
            "verdict": h.get_verdict(),
        })
    rankings.sort(key=lambda x: x["edge_score"], reverse=True)

    # 2. Overlap analysis
    date_sets = {}
    for h in hypotheses:
        dates = set(s["date"] for s in h.signals)
        date_sets[h.id] = dates

    overlap_matrix = {}
    for h1 in hypotheses:
        for h2 in hypotheses:
            if h1.id >= h2.id:
                continue
            common = date_sets[h1.id] & date_sets[h2.id]
            overlap_matrix[f"H{h1.id}_H{h2.id}"] = {
                "common_dates": len(common),
                "h1_total": len(date_sets[h1.id]),
                "h2_total": len(date_sets[h2.id]),
                "overlap_pct": round(len(common) / max(1, min(len(date_sets[h1.id]), len(date_sets[h2.id]))) * 100, 1),
            }

    # 3. Combined frequency estimate
    # Count unique dates with valid signals for hypotheses with positive validation
    valid_hypotheses = [h for h in hypotheses if h.compute_stats("validation").get("continuation_rate", 0) > 0.55]

    all_valid_dates = set()
    for h in valid_hypotheses:
        val_sigs = [s for s in h.signals if date.fromisoformat(s["date"]) >= VALIDATION_START]
        for s in val_sigs:
            all_valid_dates.add(s["date"])

    val_months = 9  # Jul 2025 - Mar 2026
    additional_per_month = len(all_valid_dates) / val_months if val_months > 0 else 0

    # Combined expectancy
    combined_r = []
    for h in valid_hypotheses:
        val_sigs = [s for s in h.signals if date.fromisoformat(s["date"]) >= VALIDATION_START]
        for s in val_sigs:
            combined_r.append(s.get("r_multiple", 0))

    return {
        "rankings": rankings,
        "overlap_matrix": overlap_matrix,
        "valid_hypotheses_count": len(valid_hypotheses),
        "unique_valid_dates": len(all_valid_dates),
        "additional_trades_per_month": round(additional_per_month, 1),
        "combined_avg_r": round(np.mean(combined_r), 3) if combined_r else 0,
        "combined_median_r": round(np.median(combined_r), 3) if combined_r else 0,
    }


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Detailed Analysis for Top Hypotheses
# ═══════════════════════════════════════════════════════════════════════

def detailed_analysis(hypothesis: HypothesisResult) -> dict:
    """Detailed analysis for a top hypothesis."""
    logger.info(f"Detailed analysis for H{hypothesis.id}: {hypothesis.name}...")

    signals = sorted(hypothesis.signals, key=lambda s: s["date"])

    # Monthly distribution
    monthly = defaultdict(int)
    for s in signals:
        month = s["date"][:7]
        monthly[month] += 1

    # Consecutive losses
    max_consec_loss = 0
    current_streak = 0
    for s in signals:
        if not s["continuation"]:
            current_streak += 1
            max_consec_loss = max(max_consec_loss, current_streak)
        else:
            current_streak = 0

    # Profit factor
    wins = [s for s in signals if s["continuation"]]
    losses = [s for s in signals if not s["continuation"]]

    gross_profit = sum(s.get("mfe", 0) for s in wins)
    gross_loss = sum(s.get("mae", 0) for s in losses)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # R-multiple based profit factor
    r_wins = sum(s.get("r_multiple", 0) for s in wins)
    r_losses = sum(1.0 for s in losses)  # Each loss = 1R
    r_profit_factor = r_wins / r_losses if r_losses > 0 else float("inf")

    # Monte Carlo simulation (50-trade sequences)
    r_multiples = []
    for s in signals:
        if s["continuation"]:
            r_multiples.append(s.get("r_multiple", 1.5))
        else:
            r_multiples.append(-1.0)

    if len(r_multiples) >= 20:
        mc_results = []
        rng = np.random.default_rng(42)
        for _ in range(10000):
            seq = rng.choice(r_multiples, size=min(50, len(r_multiples)), replace=True)
            mc_results.append(float(np.sum(seq)))
        p5 = float(np.percentile(mc_results, 5))
        p25 = float(np.percentile(mc_results, 25))
        p50 = float(np.percentile(mc_results, 50))
        p75 = float(np.percentile(mc_results, 75))
    else:
        p5 = p25 = p50 = p75 = 0

    return {
        "hypothesis_id": hypothesis.id,
        "hypothesis_name": hypothesis.name,
        "total_signals": len(signals),
        "monthly_distribution": dict(monthly),
        "max_consecutive_losses": max_consec_loss,
        "profit_factor": round(profit_factor, 2),
        "r_profit_factor": round(r_profit_factor, 2),
        "monte_carlo_50_trade": {
            "p5": round(p5, 2),
            "p25": round(p25, 2),
            "p50_median": round(p50, 2),
            "p75": round(p75, 2),
        },
        "trade_list": signals,
    }


# ═══════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_report(
    day_classifications: list[dict],
    baseline: dict,
    hypotheses: list[HypothesisResult],
    cross_analysis: dict,
    detailed_analyses: list[dict],
) -> str:
    """Generate the full markdown report."""
    lines = []
    lines.append("# Edge Discovery on D1-Unclear Days")
    lines.append(f"\n**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Data Range:** 2024-04-01 to 2026-03-30")
    lines.append(f"**Discovery Period:** 2024-04-01 to 2025-06-30")
    lines.append(f"**Validation Period:** 2025-07-01 to 2026-03-30")
    lines.append(f"**Bonferroni α:** {BONFERRONI_ALPHA:.4f} (0.05/6)")

    # Section 1: Day Classification Summary
    lines.append("\n## 1. Day Classification Summary\n")

    for symbol in ["XAUUSD", "GBPUSD"]:
        sym_days = [d for d in day_classifications if d["symbol"] == symbol]
        if not sym_days:
            continue
        lines.append(f"### {symbol} ({len(sym_days)} trading days)\n")

        d1_counts = Counter(d["d1_direction"] for d in sym_days)
        cat_counts = Counter(d["category"] for d in sym_days)

        lines.append("| D1 Direction | Count | % |")
        lines.append("|---|---|---|")
        for d, c in sorted(d1_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {d} | {c} | {c/len(sym_days)*100:.1f}% |")

        d1_clear = sum(1 for d in sym_days if d["d1_clear"])
        d1_unclear = len(sym_days) - d1_clear
        lines.append(f"\n**D1-Clear:** {d1_clear} ({d1_clear/len(sym_days)*100:.1f}%)")
        lines.append(f"**D1-Unclear:** {d1_unclear} ({d1_unclear/len(sym_days)*100:.1f}%)")

        lines.append("\n| Category | Count | % | Description |")
        lines.append("|---|---|---|---|")
        cat_desc = {
            "PASS": "D1 clear + H4 aligned",
            "CAT1": "D1 unclear + H4/H1 aligned",
            "CAT2": "All unclear",
            "CAT3": "H4 mismatch",
            "CAT4": "H1 conflict",
        }
        for cat in ["PASS", "CAT1", "CAT2", "CAT3", "CAT4"]:
            c = cat_counts.get(cat, 0)
            lines.append(f"| {cat} | {c} | {c/len(sym_days)*100:.1f}% | {cat_desc.get(cat, '')} |")
        lines.append("")

    # Section 2: Baseline Comparison
    lines.append("\n## 2. Baseline Displacement Quality: D1-Clear vs D1-Unclear\n")

    for label, key in [("D1-Clear", "d1_clear"), ("D1-Unclear", "d1_unclear")]:
        m = baseline[key]
        if m["n"] == 0:
            continue
        lines.append(f"### {label}")
        lines.append(f"- Displacements: {m['n']} across {m.get('unique_dates', '?')} dates")
        lines.append(f"- Per-date average: {m.get('disps_per_date', '?')}")
        lines.append(f"- 3h Continuation rate: {m.get('continuation_rate_3h', 0)*100:.1f}%")
        lines.append(f"- Avg MFE (3h): {m.get('avg_mfe_3h', 0):.2f}")
        lines.append(f"- Avg MAE (3h): {m.get('avg_mae_3h', 0):.2f}")
        lines.append(f"- MFE/MAE ratio: {m.get('mfe_mae_ratio', 0):.3f}")
        lines.append("")

    p_val = baseline.get("quality_difference_p_value")
    if p_val is not None:
        sig = "SIGNIFICANT" if p_val < 0.05 else "NOT significant"
        lines.append(f"**Statistical test (Mann-Whitney U):** p = {p_val:.6f} — {sig}")
        lines.append("")

    # Section 3: Per-Hypothesis Results
    lines.append("\n## 3. Per-Hypothesis Results\n")

    lines.append("### Summary Table\n")
    lines.append("| H# | Hypothesis | Disc N | Disc Rate | Disc p | Val N | Val Rate | Val p | Verdict |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for h in hypotheses:
        disc = h.compute_stats("discovery")
        val = h.compute_stats("validation")
        verdict = h.get_verdict()

        emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "INSUFFICIENT_DATA": "⚪"}.get(verdict, "")

        lines.append(
            f"| H{h.id} | {h.name} | "
            f"{disc['n']} | {disc.get('continuation_rate', 0)*100:.1f}% | {disc.get('p_value', 1):.4f} | "
            f"{val['n']} | {val.get('continuation_rate', 0)*100:.1f}% | {val.get('p_value', 1):.4f} | "
            f"{emoji} {verdict} |"
        )

    # Detailed per-hypothesis
    for h in hypotheses:
        lines.append(f"\n### H{h.id}: {h.name}\n")

        for period_name in ["Discovery", "Validation"]:
            period_key = period_name.lower()
            stats = h.compute_stats(period_key)
            lines.append(f"**{period_name} Period:**")
            if stats.get("insufficient"):
                lines.append(f"- n = {stats['n']} (INSUFFICIENT, need ≥ 20)")
            else:
                lines.append(f"- n = {stats['n']}, hits = {stats['hits']}")
                lines.append(f"- Continuation rate: {stats['continuation_rate']*100:.1f}% [{stats['ci_95'][0]*100:.1f}% - {stats['ci_95'][1]*100:.1f}%]")
                lines.append(f"- p-value: {stats['p_value']:.6f} {'✓ Bonferroni significant' if stats.get('significant_bonferroni') else ''}")
                lines.append(f"- Avg MFE: {stats.get('avg_mfe', 0):.2f}, Avg MAE: {stats.get('avg_mae', 0):.2f}")
                lines.append(f"- MFE/MAE ratio: {stats.get('mfe_mae_ratio', 0):.3f}")
                lines.append(f"- Avg R-multiple: {stats.get('avg_r_multiple', 0):.3f}")
                lines.append(f"- Edge score: {stats.get('edge_score', 0):.3f}")
            lines.append("")

        # Sub-splits for D1-clear vs unclear
        d1_clear_sigs = [s for s in h.signals if s.get("d1_clear")]
        d1_unclear_sigs = [s for s in h.signals if not s.get("d1_clear")]

        if d1_clear_sigs and d1_unclear_sigs:
            clear_hits = sum(1 for s in d1_clear_sigs if s["continuation"])
            unclear_hits = sum(1 for s in d1_unclear_sigs if s["continuation"])
            lines.append(f"**D1-Clear:** {len(d1_clear_sigs)} signals, {clear_hits}/{len(d1_clear_sigs)} cont ({clear_hits/len(d1_clear_sigs)*100:.1f}%)")
            lines.append(f"**D1-Unclear:** {len(d1_unclear_sigs)} signals, {unclear_hits}/{len(d1_unclear_sigs)} cont ({unclear_hits/len(d1_unclear_sigs)*100:.1f}%)")
            lines.append("")

    # Section 4: Cross-Hypothesis Analysis
    lines.append("\n## 4. Cross-Hypothesis Analysis\n")

    lines.append("### Edge Quality Ranking\n")
    lines.append("| Rank | Hypothesis | Val Rate | Val N | Edge Score | Verdict |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(cross_analysis["rankings"], 1):
        lines.append(f"| {i} | H{r['id']}: {r['name']} | {r['validation_rate']*100:.1f}% | {r['validation_n']} | {r['edge_score']:.3f} | {r['verdict']} |")

    lines.append(f"\n### Frequency Estimate")
    lines.append(f"- Valid hypotheses (>55% val rate): {cross_analysis['valid_hypotheses_count']}")
    lines.append(f"- Unique dates with signals: {cross_analysis['unique_valid_dates']}")
    lines.append(f"- Additional trades per month: {cross_analysis['additional_trades_per_month']:.1f}")
    lines.append(f"- Combined avg R-multiple: {cross_analysis['combined_avg_r']:.3f}")

    # Section 5: Detailed Analysis of Top Hypotheses
    lines.append("\n## 5. Top Hypothesis Detailed Analysis\n")

    for da in detailed_analyses:
        lines.append(f"### H{da['hypothesis_id']}: {da['hypothesis_name']}\n")
        lines.append(f"- Total signals: {da['total_signals']}")
        lines.append(f"- Max consecutive losses: {da['max_consecutive_losses']}")
        lines.append(f"- Profit factor (raw): {da['profit_factor']:.2f}")
        lines.append(f"- R-based profit factor: {da['r_profit_factor']:.2f}")

        mc = da["monte_carlo_50_trade"]
        lines.append(f"\n**Monte Carlo (50-trade sequences):**")
        lines.append(f"- P5 (worst 5%): {mc['p5']:.2f}R")
        lines.append(f"- P25: {mc['p25']:.2f}R")
        lines.append(f"- P50 (median): {mc['p50_median']:.2f}R")
        lines.append(f"- P75: {mc['p75']:.2f}R")

        lines.append(f"\n**Monthly Distribution:**")
        lines.append("| Month | Signals |")
        lines.append("|---|---|")
        for month, count in sorted(da["monthly_distribution"].items()):
            lines.append(f"| {month} | {count} |")
        lines.append("")

    # Section 6: Statistical Rigor
    lines.append("\n## 6. Statistical Rigor\n")
    lines.append(f"- **Bonferroni correction:** 6 hypotheses tested, adjusted α = {BONFERRONI_ALPHA:.4f}")
    lines.append("- **Minimum sample:** n ≥ 20 per hypothesis per period")
    lines.append("- **Continuation metric:** Price reaches 1.5× SL distance in expected direction within 3 hours")
    lines.append("- **Null hypothesis:** Each signal has 50% chance of continuation (coin flip)")
    lines.append("- **Test:** One-sided binomial test (H_a: p > 0.5)")
    lines.append("- **Confidence intervals:** Wilson score intervals at 95%")
    lines.append("- **Discovery/Validation split:** Chronological (no leakage)")

    # Section 7: Overall Conclusion
    lines.append("\n## 7. Overall Conclusion\n")

    green = [h for h in hypotheses if h.get_verdict() == "GREEN"]
    yellow = [h for h in hypotheses if h.get_verdict() == "YELLOW"]
    red = [h for h in hypotheses if h.get_verdict() == "RED"]
    insuff = [h for h in hypotheses if h.get_verdict() == "INSUFFICIENT_DATA"]

    lines.append(f"- **GREEN (validated):** {len(green)} hypotheses")
    for h in green:
        lines.append(f"  - H{h.id}: {h.name}")
    lines.append(f"- **YELLOW (promising):** {len(yellow)} hypotheses")
    for h in yellow:
        lines.append(f"  - H{h.id}: {h.name}")
    lines.append(f"- **RED (not significant):** {len(red)} hypotheses")
    lines.append(f"- **Insufficient data:** {len(insuff)} hypotheses")

    lines.append(f"\n**Additional trades per month:** ~{cross_analysis['additional_trades_per_month']:.1f}")
    lines.append(f"**Combined expectancy:** {cross_analysis['combined_avg_r']:.3f}R per trade")

    d1_unclear_days = sum(1 for d in day_classifications if not d["d1_clear"])
    total_days = len(day_classifications)
    lines.append(f"\n**D1-Unclear days represent {d1_unclear_days}/{total_days} ({d1_unclear_days/total_days*100:.1f}%) of all trading days.**")

    if green:
        lines.append("\nD1-unclear days contain genuine, statistically validated trading edges that the current system leaves on the table.")
    elif yellow:
        lines.append("\nSome promising patterns exist on D1-unclear days, but more data is needed for high-confidence validation.")
    else:
        lines.append("\nThe investigation did not find statistically robust edges on D1-unclear days at the Bonferroni-corrected significance level.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 70)
    logger.info("EDGE DISCOVERY ON D1-UNCLEAR DAYS")
    logger.info("=" * 70)

    # Load data
    logger.info("Loading historical data...")

    symbols_data = {}

    for symbol in ["XAUUSD", "GBPUSD"]:
        logger.info(f"  Loading {symbol}...")
        try:
            candles = {}
            for tf in ["D1", "H4", "H1", "M15"]:
                fpath = HISTORICAL_DIR / f"{symbol}_{tf}.csv"
                candles[tf] = parse_tradingview_csv(fpath)
            symbols_data[symbol] = candles
        except Exception as e:
            logger.warning(f"  Failed to load {symbol}: {e}")

    if not symbols_data:
        logger.error("No data loaded!")
        return

    # Load displacement database
    disp_db_path = OUTPUT_DIR / "displacement_database_20260403_0030.json"
    if disp_db_path.exists():
        with open(disp_db_path) as f:
            disp_db = json.load(f)
        logger.info(f"Loaded displacement database: {len(disp_db)} entries")
    else:
        disp_db = []
        logger.warning("Displacement database not found")

    # ─────────────────────────────────────────────────────────────────
    # PHASE 0: Day Classification
    # ─────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 0: Day Classification")
    logger.info("=" * 50)

    all_classifications = []
    for symbol, candles in symbols_data.items():
        classifications = classify_trading_days(symbol, candles)
        all_classifications.extend(classifications)

    # Baseline displacement comparison (XAUUSD displacement DB only)
    baseline = baseline_displacement_comparison(disp_db) if disp_db else {
        "d1_clear": {"n": 0}, "d1_unclear": {"n": 0}, "quality_difference_p_value": None
    }
    logger.info(f"Baseline: D1-clear cont={baseline['d1_clear'].get('continuation_rate_3h', 0)*100:.1f}%, "
                f"D1-unclear cont={baseline['d1_unclear'].get('continuation_rate_3h', 0)*100:.1f}%")

    # ─────────────────────────────────────────────────────────────────
    # PHASE 1: Test Hypotheses
    # ─────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 1: Testing 6 Edge Hypotheses")
    logger.info("=" * 50)

    all_hypotheses = []

    for symbol, candles in symbols_data.items():
        # H1: Session Sweep Reversal
        h1 = test_hypothesis_1(symbol, candles, all_classifications)

        # H2: FVG Fill Entry
        h2 = test_hypothesis_2(symbol, candles, all_classifications)

        # H3: Asian Sweep London (XAUUSD only per spec)
        if symbol == "XAUUSD":
            h3 = test_hypothesis_3(symbol, candles, all_classifications)

        # H4: H4-Anchored OB Retest
        h4 = test_hypothesis_4(symbol, candles, all_classifications)

        # H5: Multi-Sweep Confluence
        h5 = test_hypothesis_5(symbol, candles, all_classifications)

        # H6: PD Range Extreme Reversion
        h6 = test_hypothesis_6(symbol, candles, all_classifications)

        if symbol == "XAUUSD":
            all_hypotheses = [h1, h2, h3, h4, h5, h6]
        else:
            # Merge GBPUSD signals into existing hypotheses
            for src, tgt_id in [(h1, 1), (h2, 2), (h4, 4), (h5, 5), (h6, 6)]:
                target = next(h for h in all_hypotheses if h.id == tgt_id)
                target.signals.extend(src.signals)

    # Log summary
    for h in all_hypotheses:
        disc = h.compute_stats("discovery")
        val = h.compute_stats("validation")
        logger.info(
            f"  H{h.id} ({h.name}): "
            f"disc={disc['n']}@{disc.get('continuation_rate', 0)*100:.1f}%, "
            f"val={val['n']}@{val.get('continuation_rate', 0)*100:.1f}%, "
            f"verdict={h.get_verdict()}"
        )

    # ─────────────────────────────────────────────────────────────────
    # PHASE 2: Cross-Hypothesis Analysis
    # ─────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 2: Cross-Hypothesis Analysis")
    logger.info("=" * 50)

    cross = cross_hypothesis_analysis(all_hypotheses)
    logger.info(f"  Additional trades/month: {cross['additional_trades_per_month']:.1f}")
    logger.info(f"  Combined avg R: {cross['combined_avg_r']:.3f}")

    # ─────────────────────────────────────────────────────────────────
    # PHASE 3: Detailed Analysis for Top 2
    # ─────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 3: Detailed Analysis of Top 2 Hypotheses")
    logger.info("=" * 50)

    # Get top 2 by validation edge score
    ranked = sorted(all_hypotheses,
                    key=lambda h: h.compute_stats("validation").get("edge_score", 0),
                    reverse=True)
    top2 = ranked[:2]

    detailed_analyses = []
    for h in top2:
        da = detailed_analysis(h)
        detailed_analyses.append(da)
        logger.info(f"  H{h.id}: PF={da['profit_factor']:.2f}, MaxConsecLoss={da['max_consecutive_losses']}, "
                    f"MC P50={da['monte_carlo_50_trade']['p50_median']:.2f}R")

    # ─────────────────────────────────────────────────────────────────
    # Generate outputs
    # ─────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 50)
    logger.info("Generating outputs...")
    logger.info("=" * 50)

    # Markdown report
    report = generate_report(
        all_classifications, baseline, all_hypotheses, cross, detailed_analyses
    )

    md_path = OUTPUT_DIR / "edge_discovery_d1unclear_20260405.md"
    with open(md_path, "w") as f:
        f.write(report)
    logger.info(f"  Report: {md_path}")

    # JSON output
    json_output = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_range": "2024-04-01 to 2026-03-30",
        "discovery_period": "2024-04-01 to 2025-06-30",
        "validation_period": "2025-07-01 to 2026-03-30",
        "bonferroni_alpha": BONFERRONI_ALPHA,
        "day_classifications": all_classifications,
        "baseline_comparison": baseline,
        "hypotheses": [],
        "cross_analysis": cross,
        "top_hypothesis_trades": [],
        "frequency_estimate": {
            "additional_trades_per_month": cross["additional_trades_per_month"],
            "combined_expectancy": cross["combined_avg_r"],
        },
    }

    for h in all_hypotheses:
        disc = h.compute_stats("discovery")
        val = h.compute_stats("validation")
        json_output["hypotheses"].append({
            "id": h.id,
            "name": h.name,
            "discovery": disc,
            "validation": val,
            "verdict": h.get_verdict(),
            "total_signals": len(h.signals),
        })

    # Top hypothesis trades
    for da in detailed_analyses:
        for trade in da["trade_list"]:
            json_output["top_hypothesis_trades"].append({
                "hypothesis": da["hypothesis_id"],
                "hypothesis_name": da["hypothesis_name"],
                **trade,
            })

    json_path = OUTPUT_DIR / "edge_discovery_d1unclear_20260405.json"
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    logger.info(f"  JSON: {json_path}")

    logger.info("\n" + "=" * 70)
    logger.info("EDGE DISCOVERY COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
