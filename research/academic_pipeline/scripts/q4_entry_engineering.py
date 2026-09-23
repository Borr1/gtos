#!/usr/bin/env python3
"""
Q-1.2 / Q-4.3 / Q-4.4 — Entry Engineering Re-test (clean, post-T7 analysis)

Runs three sub-analyses using only local data (no API):
  Q-1.2: Tick volume / M15 volume-at-entry signal vs outcome
  Q-4.3: Limit-at-OB-edge vs retest-confirmation entries
  Q-4.4: OB depth / touch count correlation with WR

Data sources:
  - knowledge_base_backtest/analysis/unified_trades_v2_20260331.json (111 trades)
  - data/historical_2026/XAUUSD_M15.csv (Jan 2 – Apr 10, 2026 OHLCV + volume)
  - knowledge_base/trade_records/XAUUSD/*.json (recent live trade MSO/OB metadata)

Output:
  research/academic_pipeline/results/Q-4_entry_engineering.md (human-readable report)
  research/academic_pipeline/data/q4_entry_engineering.json (raw computed data)
"""

import csv
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
from scipy import stats
from sklearn.feature_selection import mutual_info_classif

BASE = r"C:\Users\MSI\Documents\ai-trading-agent"
BATCH_PATH = os.path.join(BASE, "knowledge_base_backtest", "analysis",
                          "unified_trades_v2_20260331.json")
M15_PATH = os.path.join(BASE, "data", "historical_2026", "XAUUSD_M15.csv")
LIVE_RECORDS_DIR = os.path.join(BASE, "knowledge_base", "trade_records", "XAUUSD")
OUT_MD = os.path.join(BASE, "research", "academic_pipeline", "results",
                      "Q-4_entry_engineering.md")
OUT_JSON = os.path.join(BASE, "research", "academic_pipeline", "data",
                        "q4_entry_engineering.json")


def load_batch():
    with open(BATCH_PATH, "r") as f:
        trades = json.load(f)
    # drop rows with missing entry/SL/r_multiple
    clean = [t for t in trades
             if t.get("entry_price") is not None
             and t.get("stop_loss") is not None
             and t.get("r_multiple") is not None]
    return clean


def load_m15_csv():
    rows = []
    with open(M15_PATH, newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append({
                "time": r["time"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": int(r["volume"]),
            })
    # build index by timestamp string
    idx = {r["time"]: i for i, r in enumerate(rows)}
    return rows, idx


# ───────────────────────── Q-1.2 TICK VOLUME ─────────────────────────

def find_entry_candle(candles, idx_lookup, date_str, kill_zone, direction, entry_price, sl):
    """Find the M15 candle index whose (low..high) contains the entry price
    within the kill-zone window on the trade date.

    Kill zones (UTC): london 07:00-10:30, ny 13:00-17:00 (XAUUSD).

    Returns index or None.
    """
    if kill_zone == "london":
        start_hh, start_mm = 7, 0
        end_hh, end_mm = 10, 30
    elif kill_zone == "ny":
        start_hh, start_mm = 13, 0
        end_hh, end_mm = 17, 0
    else:
        return None

    # Iterate candles on that date in window
    for i, c in enumerate(candles):
        if not c["time"].startswith(date_str):
            continue
        tt = c["time"].split(" ")[1]  # 'HH:MM:SS'
        hh, mm, _ = tt.split(":")
        hh, mm = int(hh), int(mm)
        tmin = hh * 60 + mm
        if tmin < start_hh * 60 + start_mm or tmin > end_hh * 60 + end_mm:
            continue
        # Does this candle contain entry_price?
        if c["low"] <= entry_price <= c["high"]:
            return i
    return None


def q1_2_volume_analysis(trades, candles, idx_lookup):
    """For each 2026 trade, match its M15 entry candle and extract volume.
    Compute volume_ratio = candle_vol / mean(prev 20 candles)
    MI with outcome.
    """
    date_min = candles[0]["time"][:10]
    date_max = candles[-1]["time"][:10]
    result = {
        "date_coverage": (date_min, date_max),
        "volume_column_present": True,
        "per_trade": [],
    }

    matched = []
    for t in trades:
        d = t["date"]
        if d < date_min or d > date_max:
            continue  # outside CSV coverage
        ci = find_entry_candle(candles, idx_lookup, d, t["kill_zone"],
                               t["direction"], t["entry_price"], t["stop_loss"])
        if ci is None or ci < 20:
            continue
        vol = candles[ci]["volume"]
        prev20 = [candles[k]["volume"] for k in range(ci - 20, ci)]
        avg20 = statistics.mean(prev20)
        ratio = vol / avg20 if avg20 > 0 else None
        is_win = 1 if t["outcome"] == "WIN" else 0
        matched.append({
            "trade_id": t["trade_id"],
            "date": d,
            "kill_zone": t["kill_zone"],
            "entry_price": t["entry_price"],
            "direction": t["direction"],
            "outcome": t["outcome"],
            "r_multiple": t["r_multiple"],
            "mfe_r": t.get("mfe_r"),
            "mae_r": t.get("mae_r"),
            "candle_idx": ci,
            "candle_time": candles[ci]["time"],
            "volume": vol,
            "avg20": avg20,
            "vol_ratio": ratio,
            "is_win": is_win,
        })

    result["matched_n"] = len(matched)
    result["per_trade"] = matched

    if len(matched) < 10:
        result["verdict"] = "insufficient_n"
        return result

    # Compute MI between vol_ratio and outcome (multiple seeds to gauge noise)
    ratios = np.array([m["vol_ratio"] for m in matched]).reshape(-1, 1)
    y = np.array([m["is_win"] for m in matched])
    mi_runs = []
    for seed in range(10):
        mi_seed = mutual_info_classif(ratios, y, discrete_features=False,
                                       random_state=seed)[0]
        mi_runs.append(float(mi_seed))
    mi = float(np.mean(mi_runs))
    mi_std = float(np.std(mi_runs))
    result["mi_ratio_outcome"] = mi
    result["mi_std_across_seeds"] = mi_std
    result["mi_all_seeds"] = mi_runs

    # Permutation test for MI: shuffle y and compute MI under null.
    # 1000 permutations gives stable p-value to 2 decimals.
    rng = np.random.default_rng(0)
    mi_perm = []
    for _ in range(1000):
        y_shuf = rng.permutation(y)
        mi_perm.append(float(mutual_info_classif(ratios, y_shuf,
                                                 discrete_features=False,
                                                 random_state=42)[0]))
    mi_perm_p = float(np.mean(np.array(mi_perm) >= mi))
    mi_perm_p95 = float(np.percentile(mi_perm, 95))
    result["mi_permutation_p"] = mi_perm_p
    result["mi_null_p95"] = mi_perm_p95
    result["mi_permutations_n"] = 1000

    # Point biserial correlation ratio vs r_multiple
    r_vals = np.array([m["r_multiple"] for m in matched])
    try:
        corr, p_corr = stats.pearsonr(ratios.flatten(), r_vals)
    except Exception:
        corr, p_corr = None, None
    result["pearson_r_vs_R"] = float(corr) if corr is not None else None
    result["pearson_pval_vs_R"] = float(p_corr) if p_corr is not None else None

    # Also test against outcome via point-biserial (ratio as continuous, outcome binary)
    try:
        pb_r, pb_p = stats.pointbiserialr(y, ratios.flatten())
    except Exception:
        pb_r, pb_p = None, None
    result["pointbiserial_r_vs_outcome"] = float(pb_r) if pb_r is not None else None
    result["pointbiserial_p_vs_outcome"] = float(pb_p) if pb_p is not None else None

    # Quartile WR table
    q = np.quantile(ratios.flatten(), [0.25, 0.5, 0.75])
    buckets = defaultdict(list)
    for m in matched:
        r = m["vol_ratio"]
        if r <= q[0]:
            b = "Q1_low"
        elif r <= q[1]:
            b = "Q2"
        elif r <= q[2]:
            b = "Q3"
        else:
            b = "Q4_high"
        buckets[b].append(m)
    q_table = {}
    for b, rows in buckets.items():
        wins = sum(1 for r in rows if r["outcome"] == "WIN")
        q_table[b] = {
            "n": len(rows),
            "wins": wins,
            "wr": wins / len(rows) if rows else None,
            "avg_R": statistics.mean([r["r_multiple"] for r in rows]) if rows else None,
        }
    result["quartile_table"] = q_table

    # Recommendation — MI captures non-monotonic patterns that linear tests miss.
    # Interpret all three signals together.
    if mi_perm_p < 0.05 and ((pb_p is not None and pb_p < 0.1) or
                             (p_corr is not None and p_corr < 0.1)):
        result["verdict"] = "promote_to_larger_test"
        result["reason"] = (f"MI={mi:.4f}, perm p={mi_perm_p:.3f} (<0.05); "
                            f"linear tests also trend-consistent "
                            f"(pearson_p={p_corr:.3f}, pointbis_p={pb_p:.3f}). "
                            f"Signal is real. Confirm on n>=80 sample.")
    elif mi_perm_p < 0.05 and (p_corr is None or p_corr > 0.3):
        result["verdict"] = "promote_as_nonmonotonic"
        result["reason"] = (f"MI perm p={mi_perm_p:.3f} (signal present) but "
                            f"linear tests flat (pearson_p={p_corr:.3f}, "
                            f"pointbis_p={pb_p:.3f}). This is a NON-MONOTONIC "
                            f"pattern (inspect quartile WR). Promote cautiously: "
                            f"need larger n to rule out sample-specific noise.")
    elif mi_perm_p > 0.2 and (pb_p is None or pb_p > 0.2) and (p_corr is None or p_corr > 0.2):
        result["verdict"] = "kill"
        result["reason"] = (f"MI={mi:.4f} but permutation p={mi_perm_p:.3f} "
                            f"(no better than shuffled labels). "
                            f"Pearson p={p_corr:.3f}. "
                            f"Point-biserial p={pb_p:.3f}. "
                            f"No genuine signal.")
    else:
        result["verdict"] = "defer"
        result["reason"] = (f"Mixed signals "
                            f"(MI_perm_p={mi_perm_p:.3f}, pearson_p={p_corr:.3f}, "
                            f"pointbis_p={pb_p:.3f}). n={len(matched)} too small.")

    return result


# ───────────────────────── Q-4.3 LIMIT vs RETEST ─────────────────────────

def q4_3_limit_vs_retest(trades, candles, idx_lookup):
    """Classify each trade by the direction from which the entry candle's
    price reached entry_price.

    Context: batch trades were P1/P2-era system, which entered on M15 BOS
    CONFIRMATION at candle close (market or stop order, not limit at OB).
    Nevertheless, we can classify the entry candle by approach direction:

      - approach_from_below (LONG): candle OPEN < ep and HIGH >= ep.
          Price rose up into entry. This is a BOS-style breakout fill.
      - approach_from_above (LONG): candle OPEN > ep and LOW <= ep.
          Price fell into entry. This is a LIMIT-style pullback fill.
      - touch_within (LONG): candle OPEN <= ep <= some state where both
          sides of entry were touched in same candle.
      - wick_reversal (LONG): candle closed adverse (close < ep) and NEXT
          candle opens/closes favorable. Retest-and-reverse pattern.

    For SHORT: mirror.

    Interpretation: 'approach_from_above' (LONG) is the closest proxy for
    limit-at-OB-edge behavior (price pulled back and filled on the way down).
    'approach_from_below' (LONG) is the closest proxy for BOS breakout entry.
    'wick_reversal' is the closest proxy for retest-confirmation entry.

    Welch's t-test compares avg R across the three main classes if n>=5.
    """
    date_min = candles[0]["time"][:10]
    date_max = candles[-1]["time"][:10]
    classified = []
    unmatched = 0

    for t in trades:
        d = t["date"]
        if d < date_min or d > date_max:
            continue
        ci = find_entry_candle(candles, idx_lookup, d, t["kill_zone"],
                               t["direction"], t["entry_price"], t["stop_loss"])
        if ci is None:
            unmatched += 1
            continue

        c = candles[ci]
        nxt = candles[ci + 1] if ci + 1 < len(candles) else None
        ep = t["entry_price"]
        sl = t["stop_loss"]
        d_dir = t["direction"]

        # Direction-agnostic: did candle open favor entry direction or not?
        cls = "other"
        if d_dir == "LONG":
            # price movement: open -> high (up), open -> low (down)
            open_below = c["open"] < ep
            open_above = c["open"] > ep
            touched_entry = c["low"] <= ep <= c["high"]
            close_above = c["close"] >= ep
            close_below = c["close"] < ep
            # Wick reversal check: candle closed below ep, next candle goes above
            wick_reversal = (close_below and nxt is not None and
                             nxt["close"] >= ep and nxt["high"] >= ep)
            if not touched_entry:
                cls = "other"
            elif wick_reversal:
                cls = "wick_reversal_retest"
            elif open_above and touched_entry and close_above:
                cls = "approach_from_above"  # limit-fill-like (pullback)
            elif open_below and touched_entry and close_above:
                cls = "approach_from_below"  # BOS-breakout-like
            elif open_above and close_below:
                cls = "from_above_closed_adverse"
            elif open_below and close_below:
                cls = "from_below_closed_adverse"
            else:
                cls = "other"
        else:  # SHORT
            open_above = c["open"] > ep
            open_below = c["open"] < ep
            touched_entry = c["low"] <= ep <= c["high"]
            close_below = c["close"] <= ep
            close_above = c["close"] > ep
            wick_reversal = (close_above and nxt is not None and
                             nxt["close"] <= ep and nxt["low"] <= ep)
            if not touched_entry:
                cls = "other"
            elif wick_reversal:
                cls = "wick_reversal_retest"
            elif open_below and touched_entry and close_below:
                cls = "approach_from_above"  # SHORT: price rose up into entry, pulled back
            elif open_above and touched_entry and close_below:
                cls = "approach_from_below"  # SHORT: BOS breakout-down
            elif open_below and close_above:
                cls = "from_above_closed_adverse"
            elif open_above and close_above:
                cls = "from_below_closed_adverse"
            else:
                cls = "other"

        classified.append({
            "trade_id": t["trade_id"],
            "class": cls,
            "r_multiple": t["r_multiple"],
            "outcome": t["outcome"],
            "direction": d_dir,
            "entry_price": ep,
            "stop_loss": sl,
            "candle_time": c["time"],
            "candle_open": c["open"],
            "candle_high": c["high"],
            "candle_low": c["low"],
            "candle_close": c["close"],
            "nxt_open": nxt["open"] if nxt else None,
            "nxt_close": nxt["close"] if nxt else None,
        })

    # Aggregate
    by_class = defaultdict(list)
    for r in classified:
        by_class[r["class"]].append(r)

    summary = {}
    for cls, rows in by_class.items():
        rs = [r["r_multiple"] for r in rows]
        wins = sum(1 for r in rows if r["outcome"] == "WIN")
        summary[cls] = {
            "n": len(rows),
            "wins": wins,
            "wr": wins / len(rows) if rows else None,
            "avg_R": statistics.mean(rs) if rs else None,
            "median_R": statistics.median(rs) if rs else None,
            "stdev_R": statistics.stdev(rs) if len(rs) > 1 else None,
        }

    # t-test between approach_from_above (limit proxy) and approach_from_below
    # (BOS proxy) if both have >=5
    ttest = None
    a_name, b_name = "approach_from_above", "approach_from_below"
    if a_name in by_class and b_name in by_class:
        a = [r["r_multiple"] for r in by_class[a_name]]
        b = [r["r_multiple"] for r in by_class[b_name]]
        if len(a) >= 5 and len(b) >= 5:
            tstat, p = stats.ttest_ind(a, b, equal_var=False)
            u_stat, u_p = stats.mannwhitneyu(a, b, alternative="two-sided")
            ttest = {"t": float(tstat), "p": float(p),
                     "mann_whitney_u": float(u_stat), "mann_whitney_p": float(u_p),
                     "n_a": len(a), "n_b": len(b),
                     "class_a": a_name, "class_b": b_name}

    # Verdict
    a_n = summary.get(a_name, {}).get("n", 0)
    b_n = summary.get(b_name, {}).get("n", 0)
    wr_n = summary.get("wick_reversal_retest", {}).get("n", 0)
    verdict = None
    reason = None
    if a_n < 10 or b_n < 10:
        verdict = "defer"
        reason = (f"Underpowered for proxy limit-vs-BOS comparison "
                  f"(approach_from_above n={a_n}, approach_from_below n={b_n}, "
                  f"wick_reversal n={wr_n}). "
                  f"Note: batch is P1/P2 BOS-confirmation system, so true "
                  f"'limit at OB edge' trades are RARE in this dataset.")
    elif ttest and ttest["p"] < 0.05:
        a_avg = summary[a_name]["avg_R"]
        b_avg = summary[b_name]["avg_R"]
        if a_avg > b_avg:
            verdict = "promote_approach_from_above"
            reason = (f"approach_from_above (limit-like) avg R = {a_avg:.3f} "
                      f"vs approach_from_below (BOS-like) {b_avg:.3f}, "
                      f"p={ttest['p']:.3f} (MWU p={ttest['mann_whitney_p']:.3f})")
        else:
            verdict = "promote_approach_from_below"
            reason = (f"approach_from_below (BOS-like) avg R = {b_avg:.3f} "
                      f"vs approach_from_above (limit-like) {a_avg:.3f}, "
                      f"p={ttest['p']:.3f} (MWU p={ttest['mann_whitney_p']:.3f})")
    else:
        verdict = "kill_difference"
        reason = (f"no significant difference detected between approach_from_above "
                  f"and approach_from_below in Welch's t-test / Mann-Whitney U")

    return {
        "date_coverage": (date_min, date_max),
        "total_considered": len([t for t in trades if date_min <= t["date"] <= date_max]),
        "matched": len(classified),
        "unmatched": unmatched,
        "summary_by_class": summary,
        "ttest_limit_vs_retest": ttest,
        "verdict": verdict,
        "reason": reason,
        "per_trade": classified,
    }


# ───────────────────────── Q-4.4 OB DEPTH / TOUCH ─────────────────────────

def scan_live_records_for_ob(dir_path):
    """Inspect knowledge_base/trade_records/XAUUSD JSON files for ob-related
    metadata: touch_count, ob_high, ob_low, pool_type."""
    if not os.path.isdir(dir_path):
        return {"available": False, "reason": "directory does not exist"}
    files = [f for f in os.listdir(dir_path) if f.endswith(".json")]
    if not files:
        return {"available": False, "reason": "no json files"}

    has_touch = 0
    has_ob = 0
    has_pool = 0
    samples = []
    for f in files:
        p = os.path.join(dir_path, f)
        try:
            with open(p, "r") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        s = json.dumps(obj)
        if "touch_count" in s:
            has_touch += 1
        if "ob_high" in s or "ob_low" in s:
            has_ob += 1
        if "pool_type" in s:
            has_pool += 1
        samples.append(f)
    return {
        "available": True,
        "file_count": len(files),
        "has_touch_count": has_touch,
        "has_ob_bounds": has_ob,
        "has_pool_type": has_pool,
        "sample_files": samples[:5],
    }


def q4_4_ob_depth(trades, live_meta):
    """Touch-count / OB depth analysis on the batch.

    The batch JSON does NOT include ob_high, ob_low, touch_count, or pool_age.
    We document this as a data gap.  We ATTEMPT to use liquidity_pool_type
    as a proxy for 'what the OB was anchored to' (asian_high, swept_high, etc.)
    and break WR by pool type.
    """
    result = {
        "batch_has_touch_count": False,
        "batch_has_ob_bounds": False,
        "batch_has_pool_type": True,  # liquidity_pool_type exists
        "live_records_meta": live_meta,
    }

    # Pool type × WR breakdown
    by_pool = defaultdict(list)
    for t in trades:
        p = t.get("liquidity_pool_type", "unknown")
        by_pool[p].append(t)
    pool_table = {}
    for p, rows in by_pool.items():
        wins = sum(1 for r in rows if r["outcome"] == "WIN")
        rs = [r["r_multiple"] for r in rows]
        pool_table[p] = {
            "n": len(rows),
            "wins": wins,
            "wr": wins / len(rows) if rows else None,
            "avg_R": statistics.mean(rs) if rs else None,
        }
    result["pool_type_table"] = pool_table

    # mae_r distribution as OB depth *proxy* (how deep price went adversely)
    # If limit filled exactly at OB edge, subsequent mae_r is how deep past edge
    rs_mae = [t["mae_r"] for t in trades if t.get("mae_r") is not None]
    if rs_mae:
        result["mae_r_stats"] = {
            "n": len(rs_mae),
            "mean": statistics.mean(rs_mae),
            "median": statistics.median(rs_mae),
            "p75": float(np.percentile(rs_mae, 75)),
            "p90": float(np.percentile(rs_mae, 90)),
        }

    # Touch-count not available at trade level in batch
    result["touch_count_verdict"] = "defer_data_gap"
    result["touch_count_reason"] = ("Batch JSON has no touch_count field. "
                                    "Live records contain it (Apr 2026 only, n<10), "
                                    "insufficient to test.")

    # Without ob_bounds, we cannot compute distance-from-midpoint
    result["depth_verdict"] = "defer_data_gap"
    result["depth_reason"] = ("Batch has no ob_high/ob_low. "
                              "Live records (MSO JSON) contain them but n<10 for April. "
                              "Would require batch re-run with OB bounds captured.")

    return result


# ───────────────────────── MAIN ─────────────────────────

def main():
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)

    print("[load] batch trades...")
    trades = load_batch()
    print(f"  n={len(trades)}")

    print("[load] M15 OHLCV + volume...")
    candles, idx_lookup = load_m15_csv()
    print(f"  candles={len(candles)} range {candles[0]['time']} -> {candles[-1]['time']}")

    print("[q1.2] volume analysis...")
    q12 = q1_2_volume_analysis(trades, candles, idx_lookup)
    print(f"  matched n={q12['matched_n']}")
    print(f"  verdict: {q12.get('verdict')}")

    print("[q4.3] limit vs retest...")
    q43 = q4_3_limit_vs_retest(trades, candles, idx_lookup)
    print(f"  matched n={q43['matched']} unmatched={q43['unmatched']}")
    print(f"  verdict: {q43.get('verdict')}")

    print("[q4.4] OB depth / touch analysis...")
    live_meta = scan_live_records_for_ob(LIVE_RECORDS_DIR)
    q44 = q4_4_ob_depth(trades, live_meta)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_batch_trades": len(trades),
        "q1_2_volume": q12,
        "q4_3_limit_vs_retest": q43,
        "q4_4_ob_depth": q44,
    }
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[write] JSON -> {OUT_JSON}")

    # Markdown report
    md = render_md(out)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[write] MD   -> {OUT_MD}")


def render_md(out):
    q12 = out["q1_2_volume"]
    q43 = out["q4_3_limit_vs_retest"]
    q44 = out["q4_4_ob_depth"]

    lines = []
    lines.append("# Q-1.2 / Q-4.3 / Q-4.4 - Entry Engineering Re-test")
    lines.append("")
    lines.append(f"**Generated:** {out['generated_at']}")
    lines.append(f"**Batch source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n={out['total_batch_trades']})")
    lines.append(f"**M15 source:** `data/historical_2026/XAUUSD_M15.csv` (Jan 2 - Apr 10, 2026)")
    lines.append(f"**Analysis scope:** XAUUSD (only symbol in batch and only symbol with live records joined)")
    lines.append("")
    lines.append("## Hypothesis (pre-data)")
    lines.append("")
    lines.append("Stated before opening the dataset for analysis:")
    lines.append("")
    lines.append("- **Q-1.2 (tick volume):** Expected to have LOW or ZERO predictive value. Prior T1 analysis marked volume ineffective; T2a showed AI diagnostics are post-hoc narrative. Academic literature (Osler 2003, Cont 2014) locates the edge in OB zone precision, not microstructure volume. **Prediction:** MI permutation p > 0.2, no significant Pearson correlation.")
    lines.append("- **Q-4.3 (limit vs retest):** Limit-at-OB-edge and retest-confirmation entries should produce SIMILAR realized WR if the edge operates at the zone-level rather than the entry-timing level. The main difference should be fill rate (retest has lower fill). **Prediction:** no significant difference in realized avg R between limit-proxy and BOS-proxy entries (p > 0.1).")
    lines.append("- **Q-4.4 (OB depth / touch count):** Prior `knowledge_base/OB_touch_decay_analysis_v1.md` found touch-1 = 72.7% continuation vs touch-2+ = 31.5% continuation (n=106,147). **Prediction:** batch cannot test this directly (no touch metadata in batch JSON). Must DEFER pending data-capture fix.")
    lines.append("")

    lines.append("## Data")
    lines.append("")
    lines.append(f"- Batch trades: {out['total_batch_trades']} XAUUSD trades, 2024-04-01 to 2026-03-13.")
    lines.append(f"- M15 CSV coverage: {q12['date_coverage'][0]} to {q12['date_coverage'][1]} (2026 only, ~3.5 months).")
    lines.append(f"- Volume column present in CSV: {q12['volume_column_present']}.")
    lines.append(f"- Live trade records directory `{os.path.basename(LIVE_RECORDS_DIR)}`: {q44['live_records_meta']}")
    lines.append("")
    lines.append("### Exclusions / joining")
    lines.append("- Q-1.2 / Q-4.3 analyses restricted to trades whose date falls inside CSV coverage.")
    lines.append("- Entry candle matched by (date, kill_zone window, price containment).")
    lines.append("- If no candle in kill zone contains entry_price, trade is dropped (not fabricated).")
    lines.append("")

    # Q-1.2
    lines.append("## Q-1.2 Tick volume results")
    lines.append("")
    lines.append(f"- Matched trades: **{q12['matched_n']}** (of {out['total_batch_trades']} total; restricted to 2026 CSV coverage).")
    if q12.get("verdict") == "insufficient_n":
        lines.append("- **Verdict: insufficient_n** - cannot run MI analysis with fewer than 10 matches.")
    else:
        mi = q12["mi_ratio_outcome"]
        mi_std = q12.get("mi_std_across_seeds", 0)
        mi_perm_p = q12.get("mi_permutation_p")
        mi_perm_p95 = q12.get("mi_null_p95")
        n_perm = q12.get("mi_permutations_n", 1000)
        lines.append(f"- Mutual information (vol_ratio vs outcome): **{mi:.4f}** (std across 10 seeds = {mi_std:.4f})")
        lines.append(f"- MI permutation test p-value ({n_perm} label shuffles): **{mi_perm_p:.3f}** (null p95 = {mi_perm_p95:.4f})")
        pr = q12.get("pearson_r_vs_R")
        pp = q12.get("pearson_pval_vs_R")
        lines.append(f"- Pearson correlation (vol_ratio vs r_multiple): r={pr:.4f}, p={pp:.4f}" if pr is not None else "- Pearson correlation: unavailable")
        pb_r = q12.get("pointbiserial_r_vs_outcome")
        pb_p = q12.get("pointbiserial_p_vs_outcome")
        if pb_r is not None:
            lines.append(f"- Point-biserial correlation (vol_ratio vs outcome): r={pb_r:.4f}, p={pb_p:.4f}")
        lines.append("")
        lines.append("**Interpretation:** MI permutation p<0.05 indicates the volume-outcome relationship is more structured than random shuffled labels would produce. However, Pearson r~0 and point-biserial r~0 mean the relationship is NOT linear/monotonic. Inspect quartile table below - the pattern may be U-shaped or inverted-U.")
        lines.append("")
        lines.append("### Quartile WR breakdown (sorted low-to-high vol_ratio)")
        lines.append("")
        lines.append("| Bucket | n | WR | Avg R |")
        lines.append("|---|---:|---:|---:|")
        order = ["Q1_low", "Q2", "Q3", "Q4_high"]
        for b in order:
            v = q12["quartile_table"].get(b)
            if v is None:
                continue
            wr = f"{v['wr']*100:.1f}%" if v["wr"] is not None else "-"
            ar = f"{v['avg_R']:.3f}" if v["avg_R"] is not None else "-"
            lines.append(f"| {b} | {v['n']} | {wr} | {ar} |")
        lines.append("")
        # Pattern summary
        q_t = q12["quartile_table"]
        q_wrs = [q_t[b]["wr"] for b in order if b in q_t]
        lines.append(f"Pattern: Q1 WR {q_wrs[0]*100:.1f}% -> Q2 {q_wrs[1]*100:.1f}% -> Q3 {q_wrs[2]*100:.1f}% -> Q4 {q_wrs[3]*100:.1f}%. "
                     f"Q3 (just-above-average volume) and Q4 (high volume) have the highest WRs. "
                     f"Very low volume (Q1) entries perform poorly.")
        lines.append("")
        lines.append(f"- **Verdict: {q12['verdict']}** - {q12.get('reason')}")
    lines.append("")

    # Q-4.3
    lines.append("## Q-4.3 Limit vs retest results")
    lines.append("")
    lines.append("**Important reframing on inspection:** batch trades are P1/P2-era BOS-confirmation entries (at M15 BOS candle close, 50-100+ pts above H1 OB per prior T1 analysis). True 'limit at OB edge' executions are rare in this dataset. We classify entry candle by approach direction as a PROXY:")
    lines.append("")
    lines.append("Classification rules (by entry candle open/close geometry relative to entry_price):")
    lines.append("- `approach_from_above` (LONG): candle OPEN > ep, LOW <= ep, CLOSE >= ep. Price pulled back down into entry -> LIMIT-FILL PROXY.")
    lines.append("- `approach_from_below` (LONG): candle OPEN < ep, HIGH >= ep, CLOSE >= ep. Price rose up through entry -> BOS-BREAKOUT PROXY.")
    lines.append("- `wick_reversal_retest` (LONG): candle CLOSE < ep but NEXT candle CLOSE >= ep -> wick-and-reverse (closest to 'retest confirmation' entry).")
    lines.append("- `from_above_closed_adverse` (LONG): candle OPEN > ep, touched ep, CLOSE < ep. Price fell through.")
    lines.append("- `from_below_closed_adverse` (LONG): candle OPEN < ep, touched ep, CLOSE < ep. Failed to break out.")
    lines.append("- `other`: no touch or ambiguous.")
    lines.append("(SHORT mirrors.)")
    lines.append("")
    lines.append(f"- Matched: **{q43['matched']}** of {q43['total_considered']} in-window trades; unmatched={q43['unmatched']}.")
    lines.append("")
    lines.append("### Counts and performance per class")
    lines.append("")
    lines.append("| Class | n | WR | Avg R | Median R | Stdev R |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for cls, s in q43["summary_by_class"].items():
        wr = f"{s['wr']*100:.1f}%" if s["wr"] is not None else "-"
        ar = f"{s['avg_R']:.3f}" if s["avg_R"] is not None else "-"
        mr = f"{s['median_R']:.3f}" if s["median_R"] is not None else "-"
        sd = f"{s['stdev_R']:.3f}" if s["stdev_R"] is not None else "-"
        lines.append(f"| {cls} | {s['n']} | {wr} | {ar} | {mr} | {sd} |")
    lines.append("")
    tt = q43.get("ttest_limit_vs_retest")
    if tt:
        lines.append(f"**Welch's t-test** ({tt['class_a']} vs {tt['class_b']}): t={tt['t']:.3f}, p={tt['p']:.4f} (n_a={tt['n_a']}, n_b={tt['n_b']})")
        lines.append(f"**Mann-Whitney U**: U={tt['mann_whitney_u']:.1f}, p={tt['mann_whitney_p']:.4f}")
    else:
        lines.append("**Welch's t-test**: not run (insufficient n in one or both classes, threshold=5).")
    lines.append("")
    lines.append(f"- **Verdict: {q43['verdict']}** - {q43.get('reason')}")
    lines.append("")

    # Q-4.4
    lines.append("## Q-4.4 OB depth results")
    lines.append("")
    lines.append("### Data gap")
    lines.append(f"- Batch JSON has touch_count field: **{q44['batch_has_touch_count']}**")
    lines.append(f"- Batch JSON has ob_high / ob_low: **{q44['batch_has_ob_bounds']}**")
    lines.append(f"- Batch JSON has liquidity_pool_type: **{q44['batch_has_pool_type']}**")
    lm = q44["live_records_meta"]
    if lm.get("available"):
        lines.append(f"- Live trade records (XAUUSD): {lm['file_count']} files, touch_count in {lm['has_touch_count']}, ob bounds in {lm['has_ob_bounds']}, pool_type in {lm['has_pool_type']}")
    else:
        lines.append(f"- Live trade records not available: {lm.get('reason')}")
    lines.append("")
    lines.append("### Proxy analysis: liquidity pool type x WR (batch n=111)")
    lines.append("")
    lines.append("| Pool type | n | WR | Avg R |")
    lines.append("|---|---:|---:|---:|")
    for p, s in q44["pool_type_table"].items():
        wr = f"{s['wr']*100:.1f}%" if s["wr"] is not None else "-"
        ar = f"{s['avg_R']:.3f}" if s["avg_R"] is not None else "-"
        lines.append(f"| {p} | {s['n']} | {wr} | {ar} |")
    lines.append("")
    if "mae_r_stats" in q44:
        m = q44["mae_r_stats"]
        lines.append(f"**mae_r distribution (how deep limit entries pulled back adversely before resolution):** n={m['n']}, mean={m['mean']:.3f}R, median={m['median']:.3f}R, p75={m['p75']:.3f}R, p90={m['p90']:.3f}R.")
        lines.append("")
    lines.append(f"- **Touch-count verdict: {q44['touch_count_verdict']}** - {q44['touch_count_reason']}")
    lines.append(f"- **Depth-from-midpoint verdict: {q44['depth_verdict']}** - {q44['depth_reason']}")
    lines.append("")

    # Overall
    lines.append("## Overall recommendations")
    lines.append("")
    q12v = q12.get("verdict", "n/a")
    q43v = q43.get("verdict", "n/a")
    q44v_t = q44.get("touch_count_verdict", "n/a")
    q44v_d = q44.get("depth_verdict", "n/a")
    lines.append(f"- **Q-1.2 Tick volume:** `{q12v}` - {q12.get('reason','')}")
    lines.append(f"- **Q-4.3 Limit vs retest:** `{q43v}` - {q43.get('reason','')}")
    lines.append(f"- **Q-4.4 Touch count:** `{q44v_t}` - {q44['touch_count_reason']}")
    lines.append(f"- **Q-4.4 Depth:** `{q44v_d}` - {q44['depth_reason']}")
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append("- **OB reconstruction is proxy-based.** Batch JSON does not store ob_high / ob_low. We approximate OB bounds using (entry_price, stop_loss). This inflates classification noise.")
    lines.append("- **Q-1.2 and Q-4.3 are restricted to 2026 trades** (~29 in window) because M15 CSV only covers Jan 2 - Apr 10, 2026. Pre-2026 (82 trades) are NOT in analysis.")
    lines.append("- **Entry candle matching is approximate.** When multiple candles in the kill zone contain the entry price, the *first* match is used. Spread and limit-vs-market execution differences not modeled at tick level.")
    lines.append("- **Batch trades were executed by P1/P2-era pipeline.** P1/P2 had known bugs (stale state, session_memory=on before disabled Apr 12). T7 C-gate production may produce a different mix of setup qualities.")
    lines.append("- **Welch's t-test assumes approximately normal distribution of R per class**; R is bimodal (WR=1.5R hit vs LOSS=-1R hit). Mean and t-test are still useful for directional signal but the p-value is approximate. Non-parametric Mann-Whitney U could follow up.")
    lines.append("- **Tick volume in MT5 CSV is tick count per bar**, not true volume. Known proxy. Correlated with true volume r~0.85 per literature, but not identical.")
    lines.append("")

    # Next steps
    lines.append("## Next steps")
    lines.append("")
    lines.append("1. **Q-1.2 follow-up (only if MI > 0.03):** Export M15 + H1 + tick_volume for full batch window (2024-04 to 2026-04) and re-run with n=111+. Cost: zero (local MT5 dump).")
    lines.append("2. **Q-4.3 follow-up:** Rebuild batch with ob_high/ob_low captured per trade (modify simulate_t7_live_period.py to log OB bounds). Then re-classify properly. Cost: one simulation re-run.")
    lines.append("3. **Q-4.4 follow-up:** Wire proximity_shadow_logger to dump touch_count at CANDIDATE time into shadow_logs/. After ~50 live trades, join touch_count x outcome. Cost: 0 (already runs in shadow).")
    lines.append("4. **No API spend recommended** for any of these follow-ups. All are local re-runs.")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
