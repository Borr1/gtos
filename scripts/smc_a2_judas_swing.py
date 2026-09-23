#!/usr/bin/env python3
"""
SMC A2 - Judas Swing / AMD Pattern Analysis
============================================
Identifies counter-D1 rejection sweeps in the first 60 min of a KZ (London/NY)
on D1-clear days, then measures 3-hour continuation in the D1 direction.
"""

import json
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from scipy.stats import chi2_contingency
import numpy as np

BASE = "/Users/borr/Documents/trading/gold-agent"
SWEEP_FILE = f"{BASE}/knowledge_base_backtest/analysis/microstructure_stream1_sweeps_20260405.json"
CLASS_FILE = f"{BASE}/knowledge_base_backtest/analysis/edge_discovery_d1unclear_20260405.json"
M15_FILE   = f"{BASE}/data/historical/XAUUSD_M15.csv"
OUT_FILE   = f"{BASE}/knowledge_base_backtest/analysis/smc_judas_swing_20260405.json"

VALIDATION_CUTOFF = "2025-07-01"
SL_BUFFER = 3.0
TARGET_R  = 1.5
WALK_CANDLES = 12  # 3 hours of M15


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_m15():
    """Return dict: datetime_str -> {o, h, l, c} and sorted list of timestamps."""
    candles = {}
    ts_list = []
    with open(M15_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row["time"].strip()
            candles[t] = {
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
            }
            ts_list.append(t)
    return candles, ts_list


def load_sweeps():
    with open(SWEEP_FILE) as f:
        data = json.load(f)
    return data["daily_data"]["XAUUSD"]


def load_day_classes():
    with open(CLASS_FILE) as f:
        data = json.load(f)
    lookup = {}
    for rec in data["day_classifications"]:
        if rec["symbol"] == "XAUUSD":
            lookup[rec["date"]] = rec
    return lookup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_entry_candle_idx(ts_list, sweep_time_str):
    """Find index of M15 candle at or just after sweep_time."""
    for i, t in enumerate(ts_list):
        if t >= sweep_time_str:
            return i
    return None


def is_opposing_sweep(d1_dir, level_swept):
    """D1 bullish + downward level (asian_l/pdl) => opposing. Vice versa."""
    down_levels = {"asian_l", "pdl"}
    up_levels   = {"asian_h", "pdh"}
    if d1_dir == "bullish" and level_swept in down_levels:
        return True
    if d1_dir == "bearish" and level_swept in up_levels:
        return True
    return False


def compute_trade(candles, ts_list, entry_idx, d1_dir, level_value, wick_distance):
    """
    Compute MFE_R, MAE_R, hit_target for a Judas Swing trade.
    Returns dict or None if insufficient candles.
    """
    if entry_idx >= len(ts_list):
        return None

    entry_candle = candles.get(ts_list[entry_idx])
    if entry_candle is None:
        return None

    entry_price = entry_candle["c"]

    # SL
    if d1_dir == "bullish":
        # Long trade: SL below the swept low
        sl_price = level_value - wick_distance - SL_BUFFER
        sl_dist = entry_price - sl_price
        if sl_dist <= 0:
            return None
        direction = 1  # long
    else:
        # Short trade: SL above the swept high
        sl_price = level_value + wick_distance + SL_BUFFER
        sl_dist = sl_price - entry_price
        if sl_dist <= 0:
            return None
        direction = -1  # short

    # Walk forward 12 candles
    end_idx = min(entry_idx + 1 + WALK_CANDLES, len(ts_list))
    if entry_idx + 1 >= len(ts_list):
        return None

    mfe = 0.0
    mae = 0.0
    hit_target = False
    hit_sl = False

    for j in range(entry_idx + 1, end_idx):
        c = candles.get(ts_list[j])
        if c is None:
            continue

        if direction == 1:  # long
            favorable = c["h"] - entry_price
            adverse   = entry_price - c["l"]
        else:  # short
            favorable = entry_price - c["l"]
            adverse   = entry_price - c["h"]  # this is negative when price goes up
            adverse   = c["h"] - entry_price   # positive when against us

        mfe = max(mfe, favorable)
        mae = max(mae, adverse)

        # Check target & SL on same candle -> conservative = SL
        candle_hit_target = (favorable >= TARGET_R * sl_dist)
        candle_hit_sl     = (adverse >= sl_dist)

        if candle_hit_target and candle_hit_sl:
            hit_sl = True
            break
        elif candle_hit_sl:
            hit_sl = True
            break
        elif candle_hit_target:
            hit_target = True
            break

    mfe_r = mfe / sl_dist if sl_dist > 0 else 0
    mae_r = mae / sl_dist if sl_dist > 0 else 0

    return {
        "entry_price": round(entry_price, 2),
        "sl_price": round(sl_price, 2),
        "sl_dist": round(sl_dist, 2),
        "direction": "long" if direction == 1 else "short",
        "mfe_r": round(mfe_r, 4),
        "mae_r": round(mae_r, 4),
        "hit_target": hit_target,
        "hit_sl": hit_sl,
    }


def group_stats(events, label="all"):
    """Compute summary stats for a list of trade results."""
    n = len(events)
    if n == 0:
        return {"n": 0, "flag_low_n": True}

    wins = sum(1 for e in events if e["hit_target"])
    rate = wins / n
    avg_mfe = sum(e["mfe_r"] for e in events) / n
    avg_mae = sum(e["mae_r"] for e in events) / n

    return {
        "n": n,
        "wins": wins,
        "continuation_rate": round(rate, 4),
        "avg_mfe_r": round(avg_mfe, 4),
        "avg_mae_r": round(avg_mae, 4),
        "flag_low_n": n < 30,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading data...")
    candles, ts_list = load_m15()
    daily_data = load_sweeps()
    day_classes = load_day_classes()
    print(f"  M15 candles: {len(candles)}")
    print(f"  Daily records: {len(daily_data)}")
    print(f"  Day classifications: {len(day_classes)}")

    judas_events = []
    control_events = []  # all rejection sweeps in first 60 min of KZ

    for day in daily_data:
        date_str = day["date"]
        dc = day_classes.get(date_str)
        if dc is None:
            continue

        d1_dir = dc["d1_direction"]
        d1_clear = dc["d1_clear"]

        for sweep in day.get("sweeps", []):
            # Control: any rejection in first 60 min of KZ
            if sweep["sweep_type"] != "rejection":
                continue
            if sweep["mins_into_kz"] > 60:
                continue

            # Find entry candle
            entry_idx = find_entry_candle_idx(ts_list, sweep["sweep_time"])
            if entry_idx is None:
                continue

            # For control, trade WITH the rejection direction:
            # rejection of high -> short; rejection of low -> long
            level = sweep["level_swept"]
            if level in ("asian_h", "pdh"):
                ctrl_dir = "bearish"
            else:
                ctrl_dir = "bullish"

            ctrl_trade = compute_trade(
                candles, ts_list, entry_idx, ctrl_dir,
                sweep["level_value"], sweep["wick_distance"]
            )
            if ctrl_trade is not None:
                ctrl_trade["date"] = date_str
                ctrl_trade["kz"] = sweep["kz"]
                ctrl_trade["level_swept"] = level
                ctrl_trade["dow"] = sweep["dow"]
                ctrl_trade["d1_clear"] = d1_clear
                ctrl_trade["is_judas"] = False  # will update below
                control_events.append(ctrl_trade)

            # Judas criteria: d1_clear + opposing direction
            if not d1_clear:
                continue
            if not is_opposing_sweep(d1_dir, level):
                continue

            # Judas trade: WITH D1 direction (reversing the false move)
            trade = compute_trade(
                candles, ts_list, entry_idx, d1_dir,
                sweep["level_value"], sweep["wick_distance"]
            )
            if trade is None:
                continue

            trade["date"] = date_str
            trade["kz"] = sweep["kz"]
            trade["level_swept"] = level
            trade["dow"] = sweep["dow"]
            trade["sweep_time"] = sweep["sweep_time"]
            trade["d1_direction"] = d1_dir
            judas_events.append(trade)

            # Mark in control
            ctrl_trade["is_judas"] = True

    print(f"\nJudas Swing events: {len(judas_events)}")
    print(f"Control events (all rejections first 60 min): {len(control_events)}")

    # -----------------------------------------------------------------------
    # Aggregate stats
    # -----------------------------------------------------------------------
    overall = group_stats(judas_events)

    # By level
    by_level = defaultdict(list)
    for e in judas_events:
        by_level[e["level_swept"]].append(e)
    splits_level = {k: group_stats(v) for k, v in sorted(by_level.items())}

    # By KZ
    by_kz = defaultdict(list)
    for e in judas_events:
        by_kz[e["kz"]].append(e)
    splits_kz = {k: group_stats(v) for k, v in sorted(by_kz.items())}

    # By DOW
    by_dow = defaultdict(list)
    for e in judas_events:
        by_dow[e["dow"]].append(e)
    splits_dow = {k: group_stats(v) for k, v in sorted(by_dow.items())}

    # Discovery vs Validation
    disc = [e for e in judas_events if e["date"] < VALIDATION_CUTOFF]
    val  = [e for e in judas_events if e["date"] >= VALIDATION_CUTOFF]
    disc_stats = group_stats(disc)
    val_stats  = group_stats(val)

    # -----------------------------------------------------------------------
    # Control comparison + chi-squared
    # -----------------------------------------------------------------------
    ctrl_stats = group_stats(control_events)
    judas_ctrl = [e for e in control_events if e["is_judas"]]
    non_judas_ctrl = [e for e in control_events if not e["is_judas"]]

    judas_wins = sum(1 for e in judas_events if e["hit_target"])
    judas_losses = len(judas_events) - judas_wins
    ctrl_nj_wins = sum(1 for e in non_judas_ctrl if e["hit_target"])
    ctrl_nj_losses = len(non_judas_ctrl) - ctrl_nj_wins

    chi2_result = {}
    if len(judas_events) > 0 and len(non_judas_ctrl) > 0:
        table = np.array([
            [judas_wins, judas_losses],
            [ctrl_nj_wins, ctrl_nj_losses]
        ])
        if table.min() >= 0 and table.sum() > 0:
            try:
                chi2, p, dof, expected = chi2_contingency(table)
                chi2_result = {
                    "chi2": round(chi2, 4),
                    "p_value": round(p, 6),
                    "dof": dof,
                    "significant_005": p < 0.05,
                    "contingency_table": {
                        "judas":     {"wins": judas_wins, "losses": judas_losses},
                        "non_judas": {"wins": ctrl_nj_wins, "losses": ctrl_nj_losses},
                    }
                }
            except Exception as ex:
                chi2_result = {"error": str(ex)}

    # -----------------------------------------------------------------------
    # Verdict
    # -----------------------------------------------------------------------
    n = len(judas_events)
    rate = overall.get("continuation_rate", 0)
    val_rate = val_stats.get("continuation_rate", 0)
    disc_rate = disc_stats.get("continuation_rate", 0)
    p_val = chi2_result.get("p_value", 1.0)

    verdict_parts = []
    if n < 30:
        verdict_parts.append(f"LOW SAMPLE: only {n} Judas Swing events (need 30+)")
    if rate >= 0.55:
        verdict_parts.append(f"Continuation rate {rate:.1%} suggests edge")
    elif rate >= 0.45:
        verdict_parts.append(f"Continuation rate {rate:.1%} is marginal")
    else:
        verdict_parts.append(f"Continuation rate {rate:.1%} shows no edge")

    if val_stats["n"] >= 15 and disc_stats["n"] >= 15:
        decay = disc_rate - val_rate
        if abs(decay) < 0.10:
            verdict_parts.append(f"Discovery ({disc_rate:.1%}) vs validation ({val_rate:.1%}): stable")
        else:
            verdict_parts.append(f"Discovery ({disc_rate:.1%}) vs validation ({val_rate:.1%}): {'decay' if decay > 0 else 'improvement'} of {abs(decay):.1%}")

    if p_val < 0.05:
        verdict_parts.append(f"Chi-squared p={p_val:.4f}: Judas vs non-Judas IS statistically different")
    else:
        verdict_parts.append(f"Chi-squared p={p_val:.4f}: no significant difference vs control")

    verdict = " | ".join(verdict_parts)

    # -----------------------------------------------------------------------
    # Build output
    # -----------------------------------------------------------------------
    output = {
        "metadata": {
            "generated": datetime.utcnow().isoformat(),
            "sweep_source": os.path.basename(SWEEP_FILE),
            "classification_source": os.path.basename(CLASS_FILE),
            "m15_source": os.path.basename(M15_FILE),
            "sl_buffer": SL_BUFFER,
            "target_r": TARGET_R,
            "walk_candles": WALK_CANDLES,
            "validation_cutoff": VALIDATION_CUTOFF,
        },
        "total_events": n,
        "continuation_rate": overall.get("continuation_rate", 0),
        "mfe_mae": {
            "avg_mfe_r": overall.get("avg_mfe_r", 0),
            "avg_mae_r": overall.get("avg_mae_r", 0),
        },
        "splits_by_level": splits_level,
        "splits_by_kz": splits_kz,
        "splits_by_dow": splits_dow,
        "control_comparison": {
            "all_rejections_first_60min": ctrl_stats,
            "judas_subset": group_stats(judas_events),
            "non_judas_subset": group_stats(non_judas_ctrl),
        },
        "chi_squared": chi2_result,
        "discovery_vs_validation": {
            "discovery": disc_stats,
            "validation": val_stats,
        },
        "verdict": verdict,
        "event_log": [
            {
                "date": e["date"],
                "sweep_time": e["sweep_time"],
                "kz": e["kz"],
                "level_swept": e["level_swept"],
                "d1_direction": e["d1_direction"],
                "direction": e["direction"],
                "entry_price": e["entry_price"],
                "sl_dist": e["sl_dist"],
                "mfe_r": e["mfe_r"],
                "mae_r": e["mae_r"],
                "hit_target": e["hit_target"],
                "hit_sl": e["hit_sl"],
            }
            for e in judas_events
        ],
    }

    # Print summary
    print(f"\n{'='*60}")
    print(f"JUDAS SWING ANALYSIS — XAUUSD")
    print(f"{'='*60}")
    print(f"Total events:        {n}")
    print(f"Continuation (1.5R): {overall.get('continuation_rate', 0):.1%}")
    print(f"Avg MFE_R:           {overall.get('avg_mfe_r', 0):.2f}")
    print(f"Avg MAE_R:           {overall.get('avg_mae_r', 0):.2f}")
    print()

    print("BY LEVEL:")
    for k, v in splits_level.items():
        flag = " [LOW N]" if v.get("flag_low_n") else ""
        print(f"  {k:10s}: n={v['n']:3d}, rate={v.get('continuation_rate',0):.1%}, "
              f"MFE={v.get('avg_mfe_r',0):.2f}, MAE={v.get('avg_mae_r',0):.2f}{flag}")

    print("\nBY KZ:")
    for k, v in splits_kz.items():
        flag = " [LOW N]" if v.get("flag_low_n") else ""
        print(f"  {k:10s}: n={v['n']:3d}, rate={v.get('continuation_rate',0):.1%}, "
              f"MFE={v.get('avg_mfe_r',0):.2f}, MAE={v.get('avg_mae_r',0):.2f}{flag}")

    print("\nBY DOW:")
    for k, v in splits_dow.items():
        flag = " [LOW N]" if v.get("flag_low_n") else ""
        print(f"  {k:5s}: n={v['n']:3d}, rate={v.get('continuation_rate',0):.1%}, "
              f"MFE={v.get('avg_mfe_r',0):.2f}, MAE={v.get('avg_mae_r',0):.2f}{flag}")

    print(f"\nDISCOVERY vs VALIDATION:")
    print(f"  Discovery  (<{VALIDATION_CUTOFF}): n={disc_stats['n']}, rate={disc_stats.get('continuation_rate',0):.1%}")
    print(f"  Validation (>={VALIDATION_CUTOFF}): n={val_stats['n']}, rate={val_stats.get('continuation_rate',0):.1%}")

    print(f"\nCONTROL COMPARISON:")
    print(f"  All rejections first 60min: n={ctrl_stats['n']}, rate={ctrl_stats.get('continuation_rate',0):.1%}")
    print(f"  Non-Judas subset:           n={group_stats(non_judas_ctrl)['n']}, rate={group_stats(non_judas_ctrl).get('continuation_rate',0):.1%}")
    if chi2_result:
        print(f"  Chi-squared: chi2={chi2_result.get('chi2','N/A')}, p={chi2_result.get('p_value','N/A')}")

    print(f"\nVERDICT: {verdict}")

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            return super().default(obj)

    with open(OUT_FILE, "w") as f:
        json.dump(output, f, indent=2, cls=NumpyEncoder)
    print(f"\nSaved to {OUT_FILE}")


if __name__ == "__main__":
    main()
