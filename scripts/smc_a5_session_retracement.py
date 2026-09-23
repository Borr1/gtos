#!/usr/bin/env python3
"""
SMC A5 — Session Range Retracement Analysis
============================================
For each D1-clear day, compute the London session range (07:00-11:00 UTC on H1),
derive 38.2%, 50%, 61.8% retracement levels, then check whether M15 candles during
the NY session (13:00-17:00 UTC) touch those levels. Measure continuation via 1.5R
target over 12 subsequent M15 bars.

Output: knowledge_base_backtest/analysis/smc_session_retracement_20260405.json
"""

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from scipy.stats import chi2_contingency
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ── paths ──────────────────────────────────────────────────────────────────
BASE = Path("/Users/borr/Documents/trading/gold-agent")
H1_CSV = BASE / "data/historical/XAUUSD_H1.csv"
M15_CSV = BASE / "data/historical/XAUUSD_M15.csv"
CLASS_JSON = BASE / "knowledge_base_backtest/analysis/edge_discovery_d1unclear_20260405.json"
OUT_JSON = BASE / "knowledge_base_backtest/analysis/smc_session_retracement_20260405.json"

SL_BUFFER = 3.0
TARGET_R = 1.5
WALK_BARS = 12  # M15 bars = 3 hours
DISCOVERY_CUTOFF = "2025-07-01"

# ── CSV parser ─────────────────────────────────────────────────────────────
def parse_csv(path):
    candles = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("time") or row.get("Time") or row.get("datetime")
            try:
                ts = int(float(t))
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                t_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, TypeError):
                # Handle "2024-04-01 01:00:00" style
                t_str = t.strip().replace(" ", "T") + "Z" if "T" not in t else t
            candles.append({
                "time": t_str,
                "open": float(row.get("open") or row.get("Open")),
                "high": float(row.get("high") or row.get("High")),
                "low": float(row.get("low") or row.get("Low")),
                "close": float(row.get("close") or row.get("Close")),
            })
    candles.sort(key=lambda c: c["time"])
    return candles


def candle_dt(c):
    t = c["time"]
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    return datetime.fromisoformat(t).replace(tzinfo=timezone.utc)


def date_str(dt_obj):
    return dt_obj.strftime("%Y-%m-%d")


def dow_name(dt_obj):
    return dt_obj.strftime("%A")


# ── index candles by date ──────────────────────────────────────────────────
def index_by_date(candles):
    by_date = defaultdict(list)
    for c in candles:
        d = candle_dt(c)
        by_date[date_str(d)].append(c)
    return by_date


# ── main logic ─────────────────────────────────────────────────────────────
def main():
    print("Loading data...")
    h1_candles = parse_csv(H1_CSV)
    m15_candles = parse_csv(M15_CSV)
    print(f"  H1 candles: {len(h1_candles)}")
    print(f"  M15 candles: {len(m15_candles)}")

    with open(CLASS_JSON) as f:
        class_data = json.load(f)
    day_class = {d["date"]: d for d in class_data["day_classifications"]}

    h1_by_date = index_by_date(h1_candles)
    m15_by_date = index_by_date(m15_candles)

    # Also build a flat sorted list of m15 with index for walk-forward
    m15_sorted = sorted(m15_candles, key=lambda c: c["time"])
    m15_time_idx = {c["time"]: i for i, c in enumerate(m15_sorted)}

    levels = ["38.2%", "50%", "61.8%"]
    all_events = []  # list of event dicts

    dates_processed = 0
    dates_skipped_no_london = 0
    dates_skipped_no_m15 = 0

    for date_key, info in sorted(day_class.items()):
        if not info.get("d1_clear"):
            continue
        direction = info["d1_direction"]
        if direction not in ("bullish", "bearish"):
            continue

        # ── 1. London range from H1 07:00-11:00 ──
        h1_today = h1_by_date.get(date_key, [])
        london_candles = []
        for c in h1_today:
            h = candle_dt(c).hour
            if 7 <= h <= 11:
                london_candles.append(c)
        if len(london_candles) < 3:
            dates_skipped_no_london += 1
            continue

        london_high = max(c["high"] for c in london_candles)
        london_low = min(c["low"] for c in london_candles)
        london_range = london_high - london_low
        if london_range < 0.5:
            continue  # negligible range

        # ── 2. Retracement levels ──
        fib_50 = (london_high + london_low) / 2.0
        if direction == "bullish":
            # Retrace from high downward
            fib_382 = london_high - 0.382 * london_range
            fib_618 = london_high - 0.618 * london_range
        else:
            # Retrace from low upward
            fib_382 = london_low + 0.382 * london_range
            fib_618 = london_low + 0.618 * london_range

        level_values = {"38.2%": fib_382, "50%": fib_50, "61.8%": fib_618}

        # ── 3. NY session M15 candles 13:00-17:00 ──
        m15_today = m15_by_date.get(date_key, [])
        ny_candles = []
        for c in m15_today:
            h = candle_dt(c).hour
            if 13 <= h <= 16:  # 13:00 through 16:45
                ny_candles.append(c)
        if not ny_candles:
            dates_skipped_no_m15 += 1
            continue

        dates_processed += 1

        # ── check each level ──
        for level_name, level_price in level_values.items():
            touch_candle = None
            touch_idx_global = None
            for c in ny_candles:
                if c["low"] <= level_price <= c["high"]:
                    touch_candle = c
                    touch_idx_global = m15_time_idx.get(c["time"])
                    break  # first touch

            if touch_candle is None or touch_idx_global is None:
                continue

            # ── 4. Entry & outcome ──
            entry_price = level_price
            if direction == "bullish":
                sl_price = london_low - SL_BUFFER
                risk = entry_price - sl_price
                target_price = entry_price + TARGET_R * risk
            else:
                sl_price = london_high + SL_BUFFER
                risk = sl_price - entry_price
                target_price = entry_price - TARGET_R * risk

            if risk <= 0:
                continue

            # Same-candle conflict check: if touch candle already hit SL
            tc = touch_candle
            if direction == "bullish" and tc["low"] <= sl_price:
                outcome = "sl"
                mfe = 0.0
                mae = (sl_price - entry_price) / risk  # negative
                hit_target = False
            elif direction == "bearish" and tc["high"] >= sl_price:
                outcome = "sl"
                mfe = 0.0
                mae = (sl_price - entry_price) / risk
                hit_target = False
            else:
                # Walk forward 12 M15 bars
                mfe_points = 0.0
                mae_points = 0.0
                outcome = "open"
                hit_target = False
                for j in range(1, WALK_BARS + 1):
                    idx = touch_idx_global + j
                    if idx >= len(m15_sorted):
                        break
                    bar = m15_sorted[idx]
                    if direction == "bullish":
                        favorable = bar["high"] - entry_price
                        adverse = entry_price - bar["low"]
                        if bar["low"] <= sl_price:
                            outcome = "sl"
                            break
                        if bar["high"] >= target_price:
                            outcome = "tp"
                            hit_target = True
                            mfe_points = max(mfe_points, favorable)
                            break
                    else:
                        favorable = entry_price - bar["low"]
                        adverse = bar["high"] - entry_price
                        if bar["high"] >= sl_price:
                            outcome = "sl"
                            break
                        if bar["low"] <= target_price:
                            outcome = "tp"
                            hit_target = True
                            mfe_points = max(mfe_points, favorable)
                            break
                    mfe_points = max(mfe_points, favorable)
                    mae_points = max(mae_points, adverse)

                mfe = mfe_points / risk
                mae = mae_points / risk

            dt_obj = candle_dt(touch_candle)
            period = "discovery" if date_key < DISCOVERY_CUTOFF else "validation"

            all_events.append({
                "date": date_key,
                "dow": dow_name(dt_obj),
                "d1_direction": direction,
                "level": level_name,
                "london_high": round(london_high, 2),
                "london_low": round(london_low, 2),
                "london_range": round(london_range, 2),
                "level_price": round(level_price, 2),
                "entry_price": round(entry_price, 2),
                "sl_price": round(sl_price, 2),
                "risk": round(risk, 2),
                "target_price": round(target_price, 2),
                "touch_time": touch_candle["time"],
                "outcome": outcome,
                "hit_target": hit_target,
                "mfe_r": round(mfe, 3),
                "mae_r": round(mae, 3),
                "period": period,
            })

    print(f"\nDates processed: {dates_processed}")
    print(f"Dates skipped (no London H1): {dates_skipped_no_london}")
    print(f"Dates skipped (no NY M15): {dates_skipped_no_m15}")
    print(f"Total trade events: {len(all_events)}")

    # ── analysis ───────────────────────────────────────────────────────────
    def calc_stats(events, label=""):
        n = len(events)
        if n == 0:
            return {"n": 0, "note": "no events"}
        wins = [e for e in events if e["hit_target"]]
        losses = [e for e in events if e["outcome"] == "sl"]
        cont_rate = len(wins) / n if n > 0 else 0
        mfe_vals = [e["mfe_r"] for e in events]
        mae_vals = [e["mae_r"] for e in events]
        result = {
            "n": n,
            "wins": len(wins),
            "losses": len(losses),
            "open_at_cutoff": n - len(wins) - len(losses),
            "continuation_rate": round(cont_rate, 4),
            "avg_mfe_r": round(statistics.mean(mfe_vals), 3) if mfe_vals else 0,
            "avg_mae_r": round(statistics.mean(mae_vals), 3) if mae_vals else 0,
            "median_mfe_r": round(statistics.median(mfe_vals), 3) if mfe_vals else 0,
            "median_mae_r": round(statistics.median(mae_vals), 3) if mae_vals else 0,
        }
        if n < 30:
            result["LOW_SAMPLE_WARNING"] = f"n={n} < 30"
        return result

    # ── 5. By level ──
    by_level = defaultdict(list)
    for e in all_events:
        by_level[e["level"]].append(e)

    total_events_by_level = {}
    continuation_rates_by_level = {}
    mfe_mae_by_level = {}
    for lev in levels:
        evts = by_level[lev]
        stats = calc_stats(evts, lev)
        total_events_by_level[lev] = stats["n"]
        continuation_rates_by_level[lev] = stats["continuation_rate"]
        mfe_mae_by_level[lev] = {
            "n": stats["n"],
            "avg_mfe_r": stats["avg_mfe_r"],
            "avg_mae_r": stats["avg_mae_r"],
            "median_mfe_r": stats["median_mfe_r"],
            "median_mae_r": stats["median_mae_r"],
        }
        if "LOW_SAMPLE_WARNING" in stats:
            mfe_mae_by_level[lev]["LOW_SAMPLE_WARNING"] = stats["LOW_SAMPLE_WARNING"]

    # ── chi-squared test across levels ──
    chi2_result = None
    if HAS_SCIPY:
        # Contingency table: rows = levels, cols = [wins, non-wins]
        table = []
        for lev in levels:
            evts = by_level[lev]
            wins = sum(1 for e in evts if e["hit_target"])
            non_wins = len(evts) - wins
            table.append([wins, non_wins])
        # Only run if all cells > 0
        if all(row[0] + row[1] > 0 for row in table):
            try:
                chi2, p_val, dof, expected = chi2_contingency(table)
                chi2_result = {
                    "chi2": round(float(chi2), 4),
                    "p_value": round(float(p_val), 6),
                    "dof": int(dof),
                    "contingency_table": {lev: {"wins": table[i][0], "non_wins": table[i][1]} for i, lev in enumerate(levels)},
                    "significant_at_005": bool(p_val < 0.05),
                }
            except Exception as ex:
                chi2_result = {"error": str(ex)}

    # ── 6. By D1 direction ──
    d1_direction_split = {}
    for direction in ["bullish", "bearish"]:
        dir_events = [e for e in all_events if e["d1_direction"] == direction]
        d1_direction_split[direction] = {"overall": calc_stats(dir_events)}
        for lev in levels:
            lev_events = [e for e in dir_events if e["level"] == lev]
            d1_direction_split[direction][lev] = calc_stats(lev_events)

    # ── By day of week ──
    dow_split = {}
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for d in dow_order:
        d_events = [e for e in all_events if e["dow"] == d]
        if d_events:
            dow_split[d] = {"overall": calc_stats(d_events)}
            for lev in levels:
                lev_events = [e for e in d_events if e["level"] == lev]
                if lev_events:
                    dow_split[d][lev] = calc_stats(lev_events)

    # ── 7. Discovery vs validation ──
    disc_events = [e for e in all_events if e["period"] == "discovery"]
    val_events = [e for e in all_events if e["period"] == "validation"]
    discovery_vs_validation = {
        "discovery": {"overall": calc_stats(disc_events)},
        "validation": {"overall": calc_stats(val_events)},
    }
    for lev in levels:
        discovery_vs_validation["discovery"][lev] = calc_stats([e for e in disc_events if e["level"] == lev])
        discovery_vs_validation["validation"][lev] = calc_stats([e for e in val_events if e["level"] == lev])

    # ── optimal level verdict ──
    best_level = None
    best_rate = -1
    for lev in levels:
        r = continuation_rates_by_level[lev]
        n = total_events_by_level[lev]
        if n >= 30 and r > best_rate:
            best_rate = r
            best_level = lev
    if best_level is None:
        # Fall back to highest n
        best_level = max(levels, key=lambda l: total_events_by_level[l])
        best_rate = continuation_rates_by_level[best_level]

    optimal_level_verdict = {
        "best_level": best_level,
        "continuation_rate": best_rate,
        "n": total_events_by_level[best_level],
        "rationale": (
            f"{best_level} retracement has the highest continuation rate "
            f"({best_rate:.1%}) among levels with n >= 30."
            if total_events_by_level[best_level] >= 30
            else f"{best_level} selected but LOW SAMPLE (n={total_events_by_level[best_level]}). All levels have n < 30."
        ),
    }

    # Check if validation holds
    val_best = discovery_vs_validation["validation"].get(best_level, {})
    disc_best = discovery_vs_validation["discovery"].get(best_level, {})
    if val_best.get("n", 0) > 0 and disc_best.get("n", 0) > 0:
        optimal_level_verdict["discovery_rate"] = disc_best.get("continuation_rate", 0)
        optimal_level_verdict["validation_rate"] = val_best.get("continuation_rate", 0)
        diff = abs(disc_best.get("continuation_rate", 0) - val_best.get("continuation_rate", 0))
        optimal_level_verdict["disc_val_gap"] = round(diff, 4)
        optimal_level_verdict["holds_in_validation"] = diff < 0.15

    # ── build output ───────────────────────────────────────────────────────
    output = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "description": "Session Range Retracement: London range fib levels tested during NY session",
        "parameters": {
            "london_hours_utc": "07:00-11:00",
            "ny_hours_utc": "13:00-17:00",
            "sl_buffer_usd": SL_BUFFER,
            "target_r": TARGET_R,
            "walk_forward_bars_m15": WALK_BARS,
            "discovery_cutoff": DISCOVERY_CUTOFF,
        },
        "summary": {
            "total_d1_clear_days_processed": dates_processed,
            "total_trade_events": len(all_events),
            "events_by_level": total_events_by_level,
        },
        "total_events_by_level": total_events_by_level,
        "continuation_rates_by_level": continuation_rates_by_level,
        "mfe_mae_by_level": mfe_mae_by_level,
        "chi_squared_test_across_levels": chi2_result,
        "d1_direction_split": d1_direction_split,
        "dow_split": dow_split,
        "discovery_vs_validation": discovery_vs_validation,
        "optimal_level_verdict": optimal_level_verdict,
        "sample_events": all_events[:10],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    # ── print summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SESSION RANGE RETRACEMENT ANALYSIS")
    print("=" * 70)
    print(f"\nTotal events: {len(all_events)}")
    print(f"\nEvents by level:")
    for lev in levels:
        n = total_events_by_level[lev]
        r = continuation_rates_by_level[lev]
        flag = " *** LOW SAMPLE ***" if n < 30 else ""
        print(f"  {lev:>6}: n={n:>4}, continuation={r:.1%}{flag}")

    print(f"\nMFE/MAE by level:")
    for lev in levels:
        m = mfe_mae_by_level[lev]
        print(f"  {lev:>6}: avg_MFE={m['avg_mfe_r']:.3f}R, avg_MAE={m['avg_mae_r']:.3f}R")

    if chi2_result and "p_value" in chi2_result:
        print(f"\nChi-squared test: chi2={chi2_result['chi2']:.4f}, p={chi2_result['p_value']:.6f}")
        print(f"  Significant difference between levels: {'YES' if chi2_result['significant_at_005'] else 'NO'}")

    print(f"\nD1 direction split:")
    for d in ["bullish", "bearish"]:
        s = d1_direction_split[d]["overall"]
        print(f"  {d:>8}: n={s['n']}, rate={s['continuation_rate']:.1%}")

    print(f"\nDay of week:")
    for d in dow_order:
        if d in dow_split:
            s = dow_split[d]["overall"]
            print(f"  {d:>10}: n={s['n']}, rate={s['continuation_rate']:.1%}")

    print(f"\nDiscovery vs Validation:")
    for p in ["discovery", "validation"]:
        s = discovery_vs_validation[p]["overall"]
        print(f"  {p:>12}: n={s['n']}, rate={s['continuation_rate']:.1%}")

    print(f"\nOptimal level: {optimal_level_verdict['best_level']}")
    print(f"  {optimal_level_verdict['rationale']}")
    if "holds_in_validation" in optimal_level_verdict:
        print(f"  Discovery rate: {optimal_level_verdict['discovery_rate']:.1%}")
        print(f"  Validation rate: {optimal_level_verdict['validation_rate']:.1%}")
        print(f"  Holds in validation: {optimal_level_verdict['holds_in_validation']}")

    print(f"\nOutput saved to: {OUT_JSON}")


if __name__ == "__main__":
    main()
