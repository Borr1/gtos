#!/usr/bin/env python3
"""
Phase 3: Counter-Trend Analysis
================================
Finds all direction_mismatch safety rejections across all instruments,
simulates what would have happened if the trade had been taken using
actual M15 candle data, and computes statistical significance.
"""

import json
import os
import glob
import csv
from datetime import datetime, timedelta
from collections import Counter
import math

# ─── Configuration ───────────────────────────────────────────────────────────

BASE = "/Users/borr/Documents/trading/gold-agent/knowledge_base_backtest"
DATA_DIR = "/Users/borr/Documents/trading/gold-agent/data"
OUTPUT_PATH = os.path.join(BASE, "analysis", "counter_trend_results_20260403.json")

# Default risk parameters when AI didn't specify exact levels
# Based on the system's standard approach per instrument
DEFAULT_PARAMS = {
    "XAUUSD": {
        "sl_pips_approx": 15.0,      # ~$15 SL typical for gold
        "tp1_rr": 1.5,               # Standard TP1 at 1.5R
        "session_timeout_candles": 28 # Standard timeout
    },
    "GBPUSD": {
        "sl_pips_approx": 0.0015,    # ~15 pips SL typical for GBPUSD
        "tp1_rr": 1.5,
        "session_timeout_candles": 28
    }
}


# ─── 3A: Find All Direction-Mismatch Rejections ──────────────────────────────

def load_m15_candles(instrument):
    """Load M15 candle data for an instrument."""
    fp = os.path.join(DATA_DIR, f"{instrument}_M15.csv")
    candles = []
    with open(fp, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(float(row["volume"]))
            })
    return candles


def build_candle_index(candles):
    """Build a time-based lookup index for candles."""
    idx = {}
    for i, c in enumerate(candles):
        idx[c["time"]] = i
    return idx


def find_direction_mismatch_rejections():
    """Scan all session files for direction_mismatch rejections."""
    rejections = []

    # Scan XAUUSD sessions
    xauusd_dir = os.path.join(BASE, "sessions", "XAUUSD")
    if os.path.isdir(xauusd_dir):
        for fn in sorted(os.listdir(xauusd_dir)):
            if not fn.endswith("_session.json"):
                continue
            fp = os.path.join(xauusd_dir, fn)
            _extract_rejections(fp, "XAUUSD", rejections)

    # Scan GBPUSD sessions
    gbpusd_dir = os.path.join(BASE, "sessions", "GBPUSD")
    if os.path.isdir(gbpusd_dir):
        for fn in sorted(os.listdir(gbpusd_dir)):
            if not fn.endswith("_session.json"):
                continue
            fp = os.path.join(gbpusd_dir, fn)
            _extract_rejections(fp, "GBPUSD", rejections)

    # De-duplicate: root sessions are copies of XAUUSD, skip them
    # (verified: root sessions have identical direction_mismatch entries)

    return rejections


def _extract_rejections(filepath, instrument, rejections):
    """Extract direction_mismatch rejections from a session file."""
    with open(filepath) as f:
        data = json.load(f)

    date = data.get("date", os.path.basename(filepath)[:10])

    for ce in data.get("candle_evaluations", []):
        reason = ce.get("reason") or ""
        if "direction_mismatch" not in reason:
            continue

        # Parse the direction from the reason string
        # Format: "direction_mismatch: SHORT against bullish daily bias"
        # or "direction_mismatch: LONG against bearish daily bias"
        ai_direction = None
        d1_bias = None
        if "SHORT against bullish" in reason:
            ai_direction = "SHORT"
            d1_bias = "bullish"
        elif "LONG against bearish" in reason:
            ai_direction = "LONG"
            d1_bias = "bearish"
        elif "SHORT against bearish" in reason:
            ai_direction = "SHORT"
            d1_bias = "bearish"
        elif "LONG against bullish" in reason:
            ai_direction = "LONG"
            d1_bias = "bullish"
        else:
            # Try generic parse
            parts = reason.split(":")
            if len(parts) > 1:
                detail = parts[1].strip()
                if "SHORT" in detail:
                    ai_direction = "SHORT"
                elif "LONG" in detail:
                    ai_direction = "LONG"
                if "bullish" in detail:
                    d1_bias = "bullish"
                elif "bearish" in detail:
                    d1_bias = "bearish"

        rejections.append({
            "date": date,
            "instrument": instrument,
            "candle_time": ce.get("candle_time"),
            "kill_zone": ce.get("kill_zone"),
            "ai_direction": ai_direction,
            "d1_bias": d1_bias,
            "confidence": ce.get("confidence"),
            "setup_grade": ce.get("setup_grade"),
            "framework": ce.get("framework"),
            "reason": reason,
            "source_file": filepath
        })


# ─── Walk-Forward Simulation ─────────────────────────────────────────────────

def estimate_entry_sl_tp(rejection, candle_at_signal, instrument):
    """
    Estimate entry, SL, and TP for a rejected trade.

    Since the trade was rejected before price calculation, we use
    the signal candle's close as entry and the instrument's typical
    SL distance based on actual taken trades in the dataset.
    """
    params = DEFAULT_PARAMS[instrument]
    direction = rejection["ai_direction"]
    entry = candle_at_signal["close"]

    # For SHORT: SL above entry, TP below entry
    # For LONG: SL below entry, TP above entry
    sl_dist = params["sl_pips_approx"]

    # Use the signal candle's range to estimate a more realistic SL
    candle_range = candle_at_signal["high"] - candle_at_signal["low"]

    # Use ATR-like approach: SL = max(default, 1.5x candle range)
    sl_dist = max(sl_dist, candle_range * 1.5)

    if direction == "SHORT":
        sl = entry + sl_dist
        tp1 = entry - (sl_dist * params["tp1_rr"])
    else:  # LONG
        sl = entry - sl_dist
        tp1 = entry + (sl_dist * params["tp1_rr"])

    return entry, sl, tp1, sl_dist


def simulate_trade(rejection, candles, candle_idx, instrument):
    """
    Walk forward through M15 candles to determine trade outcome.
    Returns outcome dict with R-multiple, MFE, MAE, etc.
    """
    params = DEFAULT_PARAMS[instrument]

    # Find the signal candle
    ct = rejection["candle_time"]
    # Normalize time format: "2024-02-02T15:00:00Z" -> "2024-02-02 15:00:00"
    ct_normalized = ct.replace("T", " ").replace("Z", "")

    if ct_normalized not in candle_idx:
        # Try without seconds
        return None

    signal_idx = candle_idx[ct_normalized]
    signal_candle = candles[signal_idx]

    entry, sl, tp1, risk = estimate_entry_sl_tp(rejection, signal_candle, instrument)
    direction = rejection["ai_direction"]

    # Walk forward from the NEXT candle
    max_candles = params["session_timeout_candles"]
    mfe_r = 0.0
    mae_r = 0.0
    outcome = "TIMEOUT"
    exit_r = 0.0
    r_path = []
    hold_time = 0

    for i in range(1, max_candles + 1):
        idx = signal_idx + i
        if idx >= len(candles):
            break

        c = candles[idx]
        hold_time = i

        if direction == "SHORT":
            r_at_high = (entry - c["high"]) / risk  # High is adverse for SHORT
            r_at_low = (entry - c["low"]) / risk     # Low is favorable for SHORT
            r_at_close = (entry - c["close"]) / risk

            # Check SL hit (high >= SL)
            if c["high"] >= sl:
                outcome = "LOSS"
                exit_r = -1.0
                # Check if TP was hit first on same candle (open is between entry and TP)
                if c["low"] <= tp1:
                    # Both hit - use open to determine which first
                    # If open closer to TP direction, TP first
                    if c["open"] <= entry:  # Gap down = favorable
                        outcome = "WIN"
                        exit_r = 1.5
                    # else SL hit first
                r_path.append({
                    "candle_index": i,
                    "time": c["time"],
                    "r_at_close": round(r_at_close, 4),
                    "r_at_high": round(r_at_high, 4),
                    "r_at_low": round(r_at_low, 4)
                })
                mae_r = max(mae_r, abs(min(0, r_at_high)))
                mfe_r = max(mfe_r, max(0, r_at_low))
                break

            # Check TP hit (low <= TP1)
            if c["low"] <= tp1:
                outcome = "WIN"
                exit_r = 1.5
                r_path.append({
                    "candle_index": i,
                    "time": c["time"],
                    "r_at_close": round(r_at_close, 4),
                    "r_at_high": round(r_at_high, 4),
                    "r_at_low": round(r_at_low, 4)
                })
                mae_r = max(mae_r, abs(min(0, r_at_high)))
                mfe_r = max(mfe_r, max(0, r_at_low))
                break

            mae_r = max(mae_r, abs(min(0, r_at_high)))
            mfe_r = max(mfe_r, max(0, r_at_low))

        else:  # LONG
            r_at_high = (c["high"] - entry) / risk
            r_at_low = (c["low"] - entry) / risk
            r_at_close = (c["close"] - entry) / risk

            # Check SL hit (low <= SL)
            if c["low"] <= sl:
                outcome = "LOSS"
                exit_r = -1.0
                if c["high"] >= tp1:
                    if c["open"] >= entry:
                        outcome = "WIN"
                        exit_r = 1.5
                r_path.append({
                    "candle_index": i,
                    "time": c["time"],
                    "r_at_close": round(r_at_close, 4),
                    "r_at_high": round(r_at_high, 4),
                    "r_at_low": round(r_at_low, 4)
                })
                mae_r = max(mae_r, abs(min(0, r_at_low)))
                mfe_r = max(mfe_r, max(0, r_at_high))
                break

            # Check TP hit
            if c["high"] >= tp1:
                outcome = "WIN"
                exit_r = 1.5
                r_path.append({
                    "candle_index": i,
                    "time": c["time"],
                    "r_at_close": round(r_at_close, 4),
                    "r_at_high": round(r_at_high, 4),
                    "r_at_low": round(r_at_low, 4)
                })
                mae_r = max(mae_r, abs(min(0, r_at_low)))
                mfe_r = max(mfe_r, max(0, r_at_high))
                break

            mae_r = max(mae_r, abs(min(0, r_at_low)))
            mfe_r = max(mfe_r, max(0, r_at_high))

        r_path.append({
            "candle_index": i,
            "time": c["time"],
            "r_at_close": round(r_at_close, 4),
            "r_at_high": round(r_at_high, 4),
            "r_at_low": round(r_at_low, 4)
        })

    # Timeout exit: use last candle close R
    if outcome == "TIMEOUT" and r_path:
        exit_r = r_path[-1]["r_at_close"]

    return {
        "date": rejection["date"],
        "instrument": rejection["instrument"],
        "candle_time": rejection["candle_time"],
        "kill_zone": rejection["kill_zone"],
        "ai_direction": rejection["ai_direction"],
        "d1_bias": rejection["d1_bias"],
        "confidence": rejection["confidence"],
        "setup_grade": rejection["setup_grade"],
        "framework": rejection["framework"],
        "entry_price": round(entry, 5),
        "stop_loss": round(sl, 5),
        "take_profit_1": round(tp1, 5),
        "risk": round(risk, 5),
        "outcome": outcome,
        "r_multiple": round(exit_r, 4),
        "mfe_r": round(mfe_r, 4),
        "mae_r": round(mae_r, 4),
        "hold_time_candles": hold_time,
        "r_path_length": len(r_path),
        "r_path_sample": r_path[:5]  # First 5 candles only for JSON size
    }


# ─── 3B: Statistical Assessment ──────────────────────────────────────────────

def binomial_test_one_sided(successes, trials, p0=0.5):
    """
    One-sided binomial test: is the observed success rate
    significantly above p0?

    Returns p-value using normal approximation for large n,
    exact calculation for small n.
    """
    if trials == 0:
        return 1.0

    observed_rate = successes / trials

    if trials >= 20:
        # Normal approximation
        se = math.sqrt(p0 * (1 - p0) / trials)
        if se == 0:
            return 0.0 if observed_rate > p0 else 1.0
        z = (observed_rate - p0) / se
        # One-sided p-value: P(Z > z)
        p_value = 0.5 * math.erfc(z / math.sqrt(2))
        return p_value
    else:
        # Exact binomial
        p_value = 0.0
        for k in range(successes, trials + 1):
            p_value += _binom_pmf(k, trials, p0)
        return p_value


def _binom_pmf(k, n, p):
    """Binomial probability mass function."""
    coeff = math.comb(n, k)
    return coeff * (p ** k) * ((1 - p) ** (n - k))


def compute_stats(outcomes):
    """Compute combined statistics for all simulated trades."""
    if not outcomes:
        return {}

    total = len(outcomes)
    wins = sum(1 for o in outcomes if o["outcome"] == "WIN")
    losses = sum(1 for o in outcomes if o["outcome"] == "LOSS")
    timeouts = sum(1 for o in outcomes if o["outcome"] == "TIMEOUT")

    # Only count definitive outcomes for win rate
    decisive = wins + losses
    win_rate = wins / decisive if decisive > 0 else 0.0

    # R statistics
    all_r = [o["r_multiple"] for o in outcomes]
    avg_r = sum(all_r) / len(all_r) if all_r else 0.0
    total_r = sum(all_r)

    # MFE/MAE
    mfes = [o["mfe_r"] for o in outcomes]
    maes = [o["mae_r"] for o in outcomes]
    avg_mfe = sum(mfes) / len(mfes) if mfes else 0.0
    avg_mae = sum(maes) / len(maes) if maes else 0.0

    # Binomial test
    p_value = binomial_test_one_sided(wins, decisive, 0.5)

    # Expectancy
    expectancy = avg_r

    # Per-instrument breakdown
    instruments = set(o["instrument"] for o in outcomes)
    per_instrument = {}
    for inst in instruments:
        inst_outcomes = [o for o in outcomes if o["instrument"] == inst]
        inst_wins = sum(1 for o in inst_outcomes if o["outcome"] == "WIN")
        inst_losses = sum(1 for o in inst_outcomes if o["outcome"] == "LOSS")
        inst_decisive = inst_wins + inst_losses
        per_instrument[inst] = {
            "total": len(inst_outcomes),
            "wins": inst_wins,
            "losses": inst_losses,
            "timeouts": sum(1 for o in inst_outcomes if o["outcome"] == "TIMEOUT"),
            "win_rate": inst_wins / inst_decisive if inst_decisive > 0 else 0.0,
            "avg_r": sum(o["r_multiple"] for o in inst_outcomes) / len(inst_outcomes),
            "total_r": sum(o["r_multiple"] for o in inst_outcomes)
        }

    return {
        "total_rejections": total,
        "simulated": total,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "decisive_trades": decisive,
        "win_rate": round(win_rate, 4),
        "avg_r": round(avg_r, 4),
        "total_r": round(total_r, 4),
        "expectancy_per_trade": round(expectancy, 4),
        "avg_mfe": round(avg_mfe, 4),
        "avg_mae": round(avg_mae, 4),
        "binomial_test": {
            "null_hypothesis": "win_rate <= 0.50",
            "observed_wins": wins,
            "observed_trials": decisive,
            "observed_win_rate": round(win_rate, 4),
            "p_value": round(p_value, 6),
            "significant_at_005": p_value < 0.05,
            "significant_at_010": p_value < 0.10
        },
        "per_instrument": per_instrument
    }


# ─── 3C: Counter-Trend Profile ───────────────────────────────────────────────

def build_profile(rejections, outcomes):
    """
    For profitable counter-trend trades, analyze the setup profile.
    """
    winning_outcomes = [o for o in outcomes if o["outcome"] == "WIN"]
    losing_outcomes = [o for o in outcomes if o["outcome"] == "LOSS"]

    if not winning_outcomes:
        return {"note": "No winning counter-trend trades found"}

    # Framework distribution
    win_frameworks = Counter(o["framework"] for o in winning_outcomes)
    loss_frameworks = Counter(o["framework"] for o in losing_outcomes)
    all_frameworks = Counter(o["framework"] for o in outcomes)

    # Grade distribution
    win_grades = Counter(o["setup_grade"] for o in winning_outcomes)
    loss_grades = Counter(o["setup_grade"] for o in losing_outcomes)

    # Kill zone distribution
    win_kz = Counter(o["kill_zone"] for o in winning_outcomes)
    loss_kz = Counter(o["kill_zone"] for o in losing_outcomes)

    # Direction distribution
    win_directions = Counter(o["ai_direction"] for o in winning_outcomes)
    all_directions = Counter(o["ai_direction"] for o in outcomes)

    # Confidence analysis
    win_confs = [o["confidence"] for o in winning_outcomes if o["confidence"]]
    loss_confs = [o["confidence"] for o in losing_outcomes if o["confidence"]]

    # MFE analysis for winners - how far did they go?
    win_mfes = [o["mfe_r"] for o in winning_outcomes]

    # D1 bias direction
    win_d1 = Counter(o["d1_bias"] for o in winning_outcomes)

    # Framework win rates
    fw_win_rates = {}
    for fw in all_frameworks:
        fw_wins = sum(1 for o in winning_outcomes if o["framework"] == fw)
        fw_losses = sum(1 for o in losing_outcomes if o["framework"] == fw)
        fw_total = fw_wins + fw_losses
        fw_win_rates[fw] = {
            "wins": fw_wins,
            "losses": fw_losses,
            "win_rate": round(fw_wins / fw_total, 4) if fw_total > 0 else 0.0,
            "total": all_frameworks[fw]
        }

    # Temporal analysis - are counter-trend trades concentrated in specific months?
    win_months = Counter()
    for o in winning_outcomes:
        try:
            dt = datetime.strptime(o["date"], "%Y-%m-%d")
            win_months[dt.strftime("%Y-%m")] += 1
        except:
            pass

    all_months = Counter()
    for o in outcomes:
        try:
            dt = datetime.strptime(o["date"], "%Y-%m-%d")
            all_months[dt.strftime("%Y-%m")] += 1
        except:
            pass

    # CHoCH vs BOS analysis from framework names
    # ob_retest typically implies CHoCH-based retest
    # breaker_retest implies BOS / breaker block
    # session_sweep implies liquidity sweep
    choch_frameworks = ["ob_retest"]
    bos_frameworks = ["breaker_retest"]
    sweep_frameworks = ["session_sweep"]

    setup_type_analysis = {
        "choch_based": {
            "frameworks": choch_frameworks,
            "total": sum(1 for o in outcomes if o["framework"] in choch_frameworks),
            "wins": sum(1 for o in winning_outcomes if o["framework"] in choch_frameworks),
            "losses": sum(1 for o in losing_outcomes if o["framework"] in choch_frameworks)
        },
        "bos_breaker_based": {
            "frameworks": bos_frameworks,
            "total": sum(1 for o in outcomes if o["framework"] in bos_frameworks),
            "wins": sum(1 for o in winning_outcomes if o["framework"] in bos_frameworks),
            "losses": sum(1 for o in losing_outcomes if o["framework"] in bos_frameworks)
        },
        "liquidity_sweep_based": {
            "frameworks": sweep_frameworks,
            "total": sum(1 for o in outcomes if o["framework"] in sweep_frameworks),
            "wins": sum(1 for o in winning_outcomes if o["framework"] in sweep_frameworks),
            "losses": sum(1 for o in losing_outcomes if o["framework"] in sweep_frameworks)
        }
    }

    # Add win rates to setup types
    for st in setup_type_analysis.values():
        decisive = st["wins"] + st["losses"]
        st["win_rate"] = round(st["wins"] / decisive, 4) if decisive > 0 else None

    # Hold time analysis
    win_hold_times = [o["hold_time_candles"] for o in winning_outcomes]
    loss_hold_times = [o["hold_time_candles"] for o in losing_outcomes]

    # Instrument breakdown for winners
    win_instruments = Counter(o["instrument"] for o in winning_outcomes)

    return {
        "total_winners": len(winning_outcomes),
        "total_losers": len(losing_outcomes),
        "framework_distribution": {
            "winners": dict(win_frameworks),
            "losers": dict(loss_frameworks),
            "framework_win_rates": fw_win_rates
        },
        "grade_distribution": {
            "winners": dict(win_grades),
            "losers": dict(loss_grades)
        },
        "kill_zone_distribution": {
            "winners": dict(win_kz),
            "losers": dict(loss_kz)
        },
        "direction_analysis": {
            "all_counter_trend_directions": dict(all_directions),
            "winning_directions": dict(win_directions),
            "note": "All rejections are counter-D1-bias trades"
        },
        "d1_bias_at_rejection": dict(win_d1),
        "confidence_analysis": {
            "winners_avg_confidence": round(sum(win_confs) / len(win_confs), 1) if win_confs else None,
            "losers_avg_confidence": round(sum(loss_confs) / len(loss_confs), 1) if loss_confs else None,
            "winners_confidence_range": [min(win_confs), max(win_confs)] if win_confs else None,
            "losers_confidence_range": [min(loss_confs), max(loss_confs)] if loss_confs else None
        },
        "mfe_analysis": {
            "winners_avg_mfe": round(sum(win_mfes) / len(win_mfes), 4) if win_mfes else None,
            "winners_median_mfe": round(sorted(win_mfes)[len(win_mfes) // 2], 4) if win_mfes else None
        },
        "setup_type_analysis": setup_type_analysis,
        "hold_time_analysis": {
            "winners_avg_hold": round(sum(win_hold_times) / len(win_hold_times), 1) if win_hold_times else None,
            "losers_avg_hold": round(sum(loss_hold_times) / len(loss_hold_times), 1) if loss_hold_times else None
        },
        "temporal_concentration": {
            "winning_months": dict(sorted(win_months.items())),
            "all_rejection_months": dict(sorted(all_months.items()))
        },
        "instrument_breakdown": dict(win_instruments),
        "key_findings": []  # Populated below
    }


# ─── Main Execution ──────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 3: Counter-Trend Direction-Mismatch Analysis")
    print("=" * 70)

    # Step 1: Find all rejections
    print("\n[3A] Scanning sessions for direction_mismatch rejections...")
    rejections = find_direction_mismatch_rejections()
    print(f"  Found {len(rejections)} direction_mismatch rejections")

    # Breakdown
    by_instrument = Counter(r["instrument"] for r in rejections)
    for inst, count in sorted(by_instrument.items()):
        print(f"    {inst}: {count}")

    by_direction = Counter(r["ai_direction"] for r in rejections)
    print(f"  By AI direction: {dict(by_direction)}")

    by_d1 = Counter(r["d1_bias"] for r in rejections)
    print(f"  By D1 bias: {dict(by_d1)}")

    # Step 2: Load candle data
    print("\n  Loading M15 candle data...")
    candle_data = {}
    candle_indices = {}
    for inst in by_instrument:
        candles = load_m15_candles(inst)
        candle_data[inst] = candles
        candle_indices[inst] = build_candle_index(candles)
        print(f"    {inst}: {len(candles)} candles loaded")

    # Step 3: Simulate each rejected trade
    print("\n  Simulating rejected trades...")
    outcomes = []
    failed_simulations = 0

    for rej in rejections:
        inst = rej["instrument"]
        result = simulate_trade(rej, candle_data[inst], candle_indices[inst], inst)
        if result:
            outcomes.append(result)
        else:
            failed_simulations += 1

    print(f"  Simulated: {len(outcomes)} trades")
    if failed_simulations:
        print(f"  Failed (no matching candle data): {failed_simulations}")

    # Quick results
    wins = sum(1 for o in outcomes if o["outcome"] == "WIN")
    losses = sum(1 for o in outcomes if o["outcome"] == "LOSS")
    timeouts = sum(1 for o in outcomes if o["outcome"] == "TIMEOUT")
    print(f"\n  Results: {wins}W / {losses}L / {timeouts}T")
    if wins + losses > 0:
        print(f"  Win rate (decisive): {wins/(wins+losses)*100:.1f}%")
        avg_r = sum(o["r_multiple"] for o in outcomes) / len(outcomes)
        print(f"  Avg R: {avg_r:.3f}")

    # Step 4: Statistical assessment
    print("\n[3B] Statistical Assessment...")
    stats = compute_stats(outcomes)

    print(f"  Total: {stats['total_rejections']}")
    print(f"  Win rate: {stats['win_rate']*100:.1f}%")
    print(f"  Avg R: {stats['avg_r']:.4f}")
    print(f"  Total R: {stats['total_r']:.2f}")
    bt = stats["binomial_test"]
    print(f"  Binomial test p-value: {bt['p_value']:.6f}")
    print(f"  Significant at 5%: {bt['significant_at_005']}")
    print(f"  Significant at 10%: {bt['significant_at_010']}")

    if stats.get("per_instrument"):
        print("\n  Per-instrument:")
        for inst, ist in stats["per_instrument"].items():
            print(f"    {inst}: {ist['wins']}W/{ist['losses']}L/{ist['timeouts']}T | WR={ist['win_rate']*100:.1f}% | AvgR={ist['avg_r']:.3f}")

    # Step 5: Profile analysis
    print("\n[3C] Counter-Trend Profile...")
    profile = build_profile(rejections, outcomes)

    # Generate key findings
    key_findings = []

    if stats["win_rate"] > 0.5:
        key_findings.append(f"Counter-trend trades show {stats['win_rate']*100:.0f}% win rate, above 50% baseline")
    else:
        key_findings.append(f"Counter-trend trades show only {stats['win_rate']*100:.0f}% win rate, AT OR BELOW 50%")

    if bt["significant_at_005"]:
        key_findings.append("Win rate is STATISTICALLY SIGNIFICANT at p<0.05")
    elif bt["significant_at_010"]:
        key_findings.append("Win rate shows marginal significance at p<0.10")
    else:
        key_findings.append("Win rate is NOT statistically significant (cannot reject null)")

    if stats["avg_r"] > 0:
        key_findings.append(f"Positive expectancy: avg {stats['avg_r']:.3f}R per trade")
    else:
        key_findings.append(f"NEGATIVE expectancy: avg {stats['avg_r']:.3f}R per trade")

    # Framework insights
    fw_wr = profile.get("framework_distribution", {}).get("framework_win_rates", {})
    for fw, fwd in fw_wr.items():
        if fwd["wins"] + fwd["losses"] >= 3:
            key_findings.append(f"Framework '{fw}': {fwd['win_rate']*100:.0f}% WR ({fwd['wins']}W/{fwd['losses']}L)")

    # Setup type insights
    sta = profile.get("setup_type_analysis", {})
    for st_name, st_data in sta.items():
        if st_data["total"] > 0 and st_data["win_rate"] is not None:
            key_findings.append(f"{st_name}: {st_data['win_rate']*100:.0f}% WR ({st_data['wins']}W/{st_data['losses']}L, {st_data['total']} total)")

    # Direction observation
    if all(r["ai_direction"] == "SHORT" for r in rejections):
        key_findings.append("ALL counter-trend rejections are SHORT against bullish D1 bias")

    profile["key_findings"] = key_findings

    for finding in key_findings:
        print(f"  - {finding}")

    # Step 6: Build output
    output = {
        "analysis_timestamp": datetime.now().isoformat(),
        "description": "Phase 3: Counter-trend direction-mismatch analysis",
        "methodology": {
            "rejection_source": "All session files across XAUUSD and GBPUSD",
            "simulation_method": "Walk-forward using actual M15 OHLC candle data",
            "entry_estimation": "Signal candle close price",
            "sl_estimation": "Max of instrument default SL or 1.5x signal candle range",
            "tp_target": "1.5R from entry",
            "session_timeout": "28 candles (7 hours)",
            "note": "Rejected trades had no AI-specified entry/SL/TP, so levels are estimated"
        },
        "all_rejections": [{
            "date": r["date"],
            "instrument": r["instrument"],
            "candle_time": r["candle_time"],
            "kill_zone": r["kill_zone"],
            "ai_direction": r["ai_direction"],
            "d1_bias": r["d1_bias"],
            "confidence": r["confidence"],
            "setup_grade": r["setup_grade"],
            "framework": r["framework"],
            "reason": r["reason"]
        } for r in rejections],
        "per_trade_outcomes": [{k: v for k, v in o.items() if k != "r_path_sample"}
                               for o in outcomes],
        "per_trade_outcomes_with_paths": outcomes[:10],  # Full path for first 10
        "combined_stats": stats,
        "profile": profile
    }

    # Save
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to: {OUTPUT_PATH}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Direction-mismatch rejections found: {len(rejections)}")
    print(f"  Successfully simulated: {len(outcomes)}")
    print(f"  Win rate: {stats['win_rate']*100:.1f}% ({wins}W / {losses}L / {timeouts}T)")
    print(f"  Average R: {stats['avg_r']:.4f}")
    print(f"  Total R: {stats['total_r']:.2f}R across {len(outcomes)} trades")
    print(f"  Binomial p-value: {bt['p_value']:.6f} ({'significant' if bt['significant_at_005'] else 'NOT significant'} at 5%)")

    if stats["avg_r"] > 0 and bt["significant_at_005"]:
        print("\n  VERDICT: Counter-trend filter may be COSTING the system profitable trades")
    elif stats["avg_r"] > 0:
        print("\n  VERDICT: Suggestive but NOT conclusive evidence of missed profits")
    else:
        print("\n  VERDICT: Direction filter is CORRECTLY protecting from bad trades")


if __name__ == "__main__":
    main()
