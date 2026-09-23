#!/usr/bin/env python3
"""
LIRA A/B Deep Forensic Analyzer (Agent Alpha)

Reads:
- research/lira_ab_backtest/slices/{slice}/all_results.json (LIRA)
- research/a2_v2_active_backtest/slices/{slice}/all_results.json (V3 baseline)
- research/f3_backtest_2026-04-24/{slice}/all_results.json (F3 reference; same prompt as V3 but pre-V3 production)

Produces ANALYSIS_DATA.json with answers to Q1-Q7.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
LIRA_DIR = ROOT / "research" / "lira_ab_backtest" / "slices"
A2_DIR = ROOT / "research" / "a2_v2_active_backtest" / "slices"
F3_DIR = ROOT / "research" / "f3_backtest_2026-04-24"
OUT_DIR = ROOT / "research" / "lira_ab_deep_forensic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SLICE_NAMES = [
    "xauusd_s1", "xauusd_s2", "xauusd_s3", "xauusd_s4",
    "xauusd_s5", "xauusd_s6", "xauusd_s7", "xauusd_s8",
    "usdjpy_s1", "usdjpy_s2", "usdjpy_s3", "usdjpy_s4",
]


def load_slice(base: Path, slice_name: str) -> Optional[dict]:
    p = base / slice_name / "all_results.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def candidates(results_doc: dict) -> list[dict]:
    if not results_doc:
        return []
    return [r for r in results_doc.get("results", []) if r.get("decision") == "CANDIDATE"]


def all_decisions(results_doc: dict) -> list[dict]:
    if not results_doc:
        return []
    return results_doc.get("results", [])


def extract_lira_confidence_tier(raw_response: str) -> Optional[str]:
    if not raw_response:
        return None
    m = re.search(r'"confidence_tier"\s*:\s*"([^"]+)"', raw_response)
    return m.group(1) if m else None


def extract_lira_no_trade_reason(raw_response: str) -> Optional[str]:
    if not raw_response:
        return None
    m = re.search(r'"no_trade_reason"\s*:\s*"([^"]+)"', raw_response)
    if m:
        return m.group(1)
    return None


def extract_v3_confidence_score(raw_response: str) -> Optional[int]:
    if not raw_response:
        return None
    m = re.search(r'"confidence_score"\s*:\s*(\d+)', raw_response)
    return int(m.group(1)) if m else None


def extract_lira_h1_setup(raw_response: str) -> dict:
    out = {"poi_type": None, "touches": None, "fvg_density": None}
    if not raw_response:
        return out
    m = re.search(r'"poi_type"\s*:\s*"([^"]+)"', raw_response)
    if m:
        out["poi_type"] = m.group(1)
    m = re.search(r'"touches"\s*:\s*(\d+)', raw_response)
    if m:
        out["touches"] = int(m.group(1))
    return out


def extract_daily_bias_confidence(raw_response: str) -> Optional[str]:
    if not raw_response:
        return None
    # find daily_bias block then confidence within
    m = re.search(r'"daily_bias"\s*:\s*\{[^{}]*"confidence"\s*:\s*"([^"]+)"', raw_response)
    return m.group(1) if m else None


def is_filled(c: dict) -> bool:
    """A CANDIDATE is 'filled' if outcome is WIN/LOSS (i.e., entered the market)."""
    out = c.get("outcome")
    return out in ("WIN", "LOSS")


def r_value(c: dict) -> float:
    if c.get("outcome") == "WIN":
        return float(c.get("r_multiple", 1.5) or 1.5)
    if c.get("outcome") == "LOSS":
        return float(c.get("r_multiple", -1.0) or -1.0)
    return 0.0


def is_unfilled(c: dict) -> bool:
    """CAND that produced an order but never filled (UNFILLED outcome)."""
    return c.get("outcome") == "UNFILLED"


def aggregate_stats(cands: list[dict]) -> dict:
    """Compute fleet/sub-stratum stats: WR, Exp, total R, MaxDD over filled-only."""
    filled = [c for c in cands if is_filled(c)]
    n = len(filled)
    if n == 0:
        return {
            "n_cand": len(cands),
            "n_filled": 0,
            "wins": 0,
            "losses": 0,
            "wr": None,
            "exp_r": None,
            "total_r": 0.0,
            "max_dd": 0.0,
        }
    wins = sum(1 for c in filled if c.get("outcome") == "WIN")
    losses = n - wins
    rs = [r_value(c) for c in filled]
    total_r = sum(rs)
    # MaxDD over equity curve in chronological order
    sorted_filled = sorted(filled, key=lambda c: c.get("candle_time", ""))
    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    for c in sorted_filled:
        eq += r_value(c)
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd
    return {
        "n_cand": len(cands),
        "n_filled": n,
        "wins": wins,
        "losses": losses,
        "wr": wins / n,
        "exp_r": total_r / n,
        "total_r": total_r,
        "max_dd": max_dd,
    }


def split_by_direction(cands: list[dict]) -> dict[str, list[dict]]:
    out = {"LONG": [], "SHORT": []}
    for c in cands:
        d = c.get("direction")
        if d in out:
            out[d].append(c)
    return out


def split_by_kz(cands: list[dict]) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for c in cands:
        kz = c.get("kill_zone", "unknown")
        out[kz].append(c)
    return dict(out)


def split_by_h1_dir(cands: list[dict]) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for c in cands:
        h1 = c.get("h1_direction", "unknown")
        out[h1].append(c)
    return dict(out)


# -----------------------------------------------------------------------------
# Load all data
# -----------------------------------------------------------------------------
print("Loading slices...")
data = {"lira": {}, "a2": {}, "f3": {}}
for s in SLICE_NAMES:
    data["lira"][s] = load_slice(LIRA_DIR, s)
    data["a2"][s] = load_slice(A2_DIR, s)
    data["f3"][s] = load_slice(F3_DIR, s)
    if data["lira"][s] is None:
        print(f"  WARN: missing LIRA {s}")
    if data["a2"][s] is None:
        print(f"  WARN: missing A2 {s}")

# -----------------------------------------------------------------------------
# Q1: Per-slice breakdown
# -----------------------------------------------------------------------------
print("\nQ1: Per-slice breakdown")
q1_per_slice = {}
for s in SLICE_NAMES:
    lira_c = candidates(data["lira"][s])
    a2_c = candidates(data["a2"][s])
    f3_c = candidates(data["f3"][s] or {})
    lira_dirs = split_by_direction(lira_c)
    a2_dirs = split_by_direction(a2_c)
    q1_per_slice[s] = {
        "symbol": (data["lira"][s] or {}).get("results", [{}])[0].get("symbol", "?") if data["lira"][s] else "?",
        "lira": {
            "stats": aggregate_stats(lira_c),
            "long_n": len(lira_dirs["LONG"]),
            "short_n": len(lira_dirs["SHORT"]),
            "unfilled_n": sum(1 for c in lira_c if is_unfilled(c)),
        },
        "a2": {
            "stats": aggregate_stats(a2_c),
            "long_n": len(a2_dirs["LONG"]),
            "short_n": len(a2_dirs["SHORT"]),
            "unfilled_n": sum(1 for c in a2_c if is_unfilled(c)),
        },
        "f3": {
            "stats": aggregate_stats(f3_c),
        },
    }

# -----------------------------------------------------------------------------
# Q2: Decision-divergence audit (overlap analysis)
# -----------------------------------------------------------------------------
print("\nQ2: Decision-divergence audit")

# Build (slice, candle_time, direction) keyed dicts
def cand_key(slice_name, c):
    return (slice_name, c.get("candle_time"), c.get("direction"))

def cand_candle_key(slice_name, c):
    return (slice_name, c.get("candle_time"))

lira_by_key = {}
a2_by_key = {}
lira_by_candle = defaultdict(list)
a2_by_candle = defaultdict(list)

for s in SLICE_NAMES:
    for c in candidates(data["lira"][s]):
        lira_by_key[cand_key(s, c)] = c
        lira_by_candle[cand_candle_key(s, c)].append(c)
    for c in candidates(data["a2"][s]):
        a2_by_key[cand_key(s, c)] = c
        a2_by_candle[cand_candle_key(s, c)].append(c)

# Overlap: same (slice, candle, direction)
both_keys = set(lira_by_key) & set(a2_by_key)
lira_only_keys = set(lira_by_key) - set(a2_by_key)
a2_only_keys = set(a2_by_key) - set(lira_by_key)

# Opposite-direction: same (slice, candle) but different directions
both_candles = set(lira_by_candle) & set(a2_by_candle)
opposite_dir_candles = []
for ck in both_candles:
    lira_dirs_at = {c.get("direction") for c in lira_by_candle[ck]}
    a2_dirs_at = {c.get("direction") for c in a2_by_candle[ck]}
    # if either set has SHORT and the other has LONG (or vice versa) on same candle
    if (lira_dirs_at - a2_dirs_at) and (a2_dirs_at - lira_dirs_at):
        opposite_dir_candles.append({
            "slice": ck[0],
            "candle_time": ck[1],
            "lira_dirs": sorted(lira_dirs_at),
            "a2_dirs": sorted(a2_dirs_at),
        })

# Outcome buckets
def outcome_buckets(cands):
    b = Counter()
    for c in cands:
        b[c.get("outcome", "UNKNOWN")] += 1
    return dict(b)

both_lira = [lira_by_key[k] for k in both_keys]
both_a2 = [a2_by_key[k] for k in both_keys]
lira_only = [lira_by_key[k] for k in lira_only_keys]
a2_only = [a2_by_key[k] for k in a2_only_keys]

q2_summary = {
    "n_cand_lira": len(lira_by_key),
    "n_cand_a2": len(a2_by_key),
    "overlap_n": len(both_keys),
    "lira_only_n": len(lira_only_keys),
    "a2_only_n": len(a2_only_keys),
    "overlap_outcomes_lira": outcome_buckets(both_lira),
    "overlap_outcomes_a2": outcome_buckets(both_a2),
    "lira_only_outcomes": outcome_buckets(lira_only),
    "a2_only_outcomes": outcome_buckets(a2_only),
    "opposite_direction_candles": opposite_dir_candles,
}

# Detail tables for divergent trades
def trade_detail(c, variant):
    return {
        "variant": variant,
        "slice": next((s for s in SLICE_NAMES if data[variant.lower()][s] and any(
            r.get("candle_time") == c.get("candle_time") and r.get("decision") == "CANDIDATE"
            for r in data[variant.lower()][s].get("results", [])
        )), "?"),
        "candle_time": c.get("candle_time"),
        "kill_zone": c.get("kill_zone"),
        "symbol": c.get("symbol"),
        "direction": c.get("direction"),
        "h1_direction": c.get("h1_direction"),
        "entry": c.get("entry_price"),
        "sl": c.get("stop_loss"),
        "tp1": c.get("take_profit_1"),
        "outcome": c.get("outcome"),
        "r": r_value(c) if is_filled(c) else 0.0,
        "confidence_tier": extract_lira_confidence_tier(c.get("raw_response", "")),
        "v3_conf_score": extract_v3_confidence_score(c.get("raw_response", "")),
        "daily_bias_conf": extract_daily_bias_confidence(c.get("raw_response", "")),
    }

q2_lira_only_detail = [trade_detail(c, "lira") for c in lira_only]
q2_a2_only_detail = [trade_detail(c, "a2") for c in a2_only]
q2_overlap_detail = []
for k in sorted(both_keys):
    lc = lira_by_key[k]
    ac = a2_by_key[k]
    q2_overlap_detail.append({
        "slice": k[0],
        "candle_time": k[1],
        "direction": k[2],
        "symbol": lc.get("symbol"),
        "kill_zone": lc.get("kill_zone"),
        "lira_outcome": lc.get("outcome"),
        "a2_outcome": ac.get("outcome"),
        "lira_r": r_value(lc) if is_filled(lc) else 0.0,
        "a2_r": r_value(ac) if is_filled(ac) else 0.0,
        "lira_entry": lc.get("entry_price"),
        "a2_entry": ac.get("entry_price"),
        "lira_sl": lc.get("stop_loss"),
        "a2_sl": ac.get("stop_loss"),
        "lira_tp1": lc.get("take_profit_1"),
        "a2_tp1": ac.get("take_profit_1"),
        "lira_conf_tier": extract_lira_confidence_tier(lc.get("raw_response", "")),
        "a2_conf_score": extract_v3_confidence_score(ac.get("raw_response", "")),
    })

# -----------------------------------------------------------------------------
# Q3: USDJPY LONG over-permissiveness
# -----------------------------------------------------------------------------
print("\nQ3: USDJPY LONG over-permissiveness root cause")

usdjpy_lira_long = [c for k, c in lira_by_key.items() if k[0].startswith("usdjpy") and c.get("direction") == "LONG"]
usdjpy_a2_long = [c for k, c in a2_by_key.items() if k[0].startswith("usdjpy") and c.get("direction") == "LONG"]

# Find LIRA-only USDJPY LONG (in lira but not in A2 same candle+dir)
usdjpy_lira_only_keys = [k for k in lira_only_keys if k[0].startswith("usdjpy") and k[2] == "LONG"]
usdjpy_lira_only = [lira_by_key[k] for k in usdjpy_lira_only_keys]

# Profile features of LIRA-only USDJPY LONGs
def profile_features(cands):
    prof = {
        "n": len(cands),
        "kill_zone_dist": Counter(c.get("kill_zone") for c in cands),
        "h1_dir_dist": Counter(c.get("h1_direction") for c in cands),
        "setup_grade_dist": Counter(c.get("setup_grade") for c in cands),
        "conf_tier_dist": Counter(extract_lira_confidence_tier(c.get("raw_response", "")) for c in cands),
        "daily_bias_conf_dist": Counter(extract_daily_bias_confidence(c.get("raw_response", "")) for c in cands),
        "outcomes": Counter(c.get("outcome") for c in cands),
    }
    return {k: dict(v) if isinstance(v, Counter) else v for k, v in prof.items()}

q3_data = {
    "lira_usdjpy_long_n": len(usdjpy_lira_long),
    "a2_usdjpy_long_n": len(usdjpy_a2_long),
    "lira_only_usdjpy_long_n": len(usdjpy_lira_only),
    "lira_only_usdjpy_long_profile": profile_features(usdjpy_lira_only),
    "lira_total_usdjpy_long_profile": profile_features(usdjpy_lira_long),
    "a2_total_usdjpy_long_profile": profile_features(usdjpy_a2_long),
    "lira_only_usdjpy_long_filled_outcomes": Counter(c.get("outcome") for c in usdjpy_lira_only if is_filled(c) or is_unfilled(c)),
    "lira_only_usdjpy_long_total_r": sum(r_value(c) for c in usdjpy_lira_only),
}
# Convert Counter to dict for JSON
q3_data["lira_only_usdjpy_long_filled_outcomes"] = dict(q3_data["lira_only_usdjpy_long_filled_outcomes"])

# detail rows for the LIRA-only USDJPY LONGs
q3_data["lira_only_usdjpy_long_detail"] = []
for c in sorted(usdjpy_lira_only, key=lambda x: (x.get("symbol",""), x.get("candle_time",""))):
    # find slice
    sl = None
    for s in SLICE_NAMES:
        if data["lira"][s]:
            for r in data["lira"][s].get("results", []):
                if r.get("candle_time") == c.get("candle_time") and r.get("decision") == "CANDIDATE":
                    sl = s
                    break
        if sl:
            break
    q3_data["lira_only_usdjpy_long_detail"].append({
        "slice": sl,
        "candle_time": c.get("candle_time"),
        "kill_zone": c.get("kill_zone"),
        "h1_direction": c.get("h1_direction"),
        "setup_grade": c.get("setup_grade"),
        "conf_tier": extract_lira_confidence_tier(c.get("raw_response", "")),
        "daily_bias_conf": extract_daily_bias_confidence(c.get("raw_response", "")),
        "outcome": c.get("outcome"),
        "r": r_value(c) if is_filled(c) else 0.0,
        "entry": c.get("entry_price"),
        "sl_price": c.get("stop_loss"),
        "poi_type_match": c.get("poi_price_level"),
    })

# -----------------------------------------------------------------------------
# Q4: SL-placement delta quantification
# -----------------------------------------------------------------------------
print("\nQ4: SL-placement delta")

q4_rows = []
for k in sorted(both_keys):
    lc = lira_by_key[k]
    ac = a2_by_key[k]
    if lc.get("entry_price") is None or ac.get("entry_price") is None:
        continue
    if lc.get("stop_loss") is None or ac.get("stop_loss") is None:
        continue
    entry = float(lc["entry_price"])
    lira_sl = float(lc["stop_loss"])
    a2_sl = float(ac["stop_loss"])
    direction = k[2]
    # SL distance from entry (always positive)
    lira_sl_dist = abs(entry - lira_sl)
    a2_sl_dist = abs(entry - a2_sl)
    # ratio: <1.0 means LIRA tighter, >1.0 means LIRA wider
    sl_ratio = lira_sl_dist / a2_sl_dist if a2_sl_dist > 0 else None
    sl_pct_lira = lira_sl_dist / entry * 100 if entry > 0 else None
    sl_pct_a2 = a2_sl_dist / entry * 100 if entry > 0 else None
    # If LIRA was tighter and LOST while A2 won: hypothetical "would A2's SL have saved LIRA?"
    # Compute price-distance hit on stop_loss; LIRA-tighter = A2's SL further from entry
    q4_rows.append({
        "slice": k[0],
        "candle_time": k[1],
        "direction": direction,
        "symbol": lc.get("symbol"),
        "entry": entry,
        "lira_sl": lira_sl,
        "a2_sl": a2_sl,
        "lira_sl_dist_pct": sl_pct_lira,
        "a2_sl_dist_pct": sl_pct_a2,
        "lira_tighter": (lira_sl_dist < a2_sl_dist),
        "sl_ratio_lira_over_a2": sl_ratio,
        "abs_delta_pct_pts": (sl_pct_lira - sl_pct_a2) if (sl_pct_lira and sl_pct_a2) else None,
        "lira_outcome": lc.get("outcome"),
        "a2_outcome": ac.get("outcome"),
        "lira_r": r_value(lc) if is_filled(lc) else 0.0,
        "a2_r": r_value(ac) if is_filled(ac) else 0.0,
    })

# Aggregate
n_lira_tighter = sum(1 for r in q4_rows if r["lira_tighter"])
n_lira_wider = sum(1 for r in q4_rows if not r["lira_tighter"])
# Cases where LIRA LOSS + A2 WIN (tighter SL caused worse outcome)
loss_to_win = [r for r in q4_rows if r["lira_outcome"] == "LOSS" and r["a2_outcome"] == "WIN"]
win_to_loss = [r for r in q4_rows if r["lira_outcome"] == "WIN" and r["a2_outcome"] == "LOSS"]

# Median tightening
deltas_pct = [abs(r["abs_delta_pct_pts"]) for r in q4_rows if r["abs_delta_pct_pts"] is not None]
deltas_pct.sort()
median_delta_pct = deltas_pct[len(deltas_pct)//2] if deltas_pct else None
# For tighter cases only
tighter_rows = [r for r in q4_rows if r["lira_tighter"] and r["abs_delta_pct_pts"] is not None]
median_tighter_pct = sorted([abs(r["abs_delta_pct_pts"]) for r in tighter_rows])[len(tighter_rows)//2] if tighter_rows else None

q4_summary = {
    "n_overlap_pairs_with_sl": len(q4_rows),
    "n_lira_tighter": n_lira_tighter,
    "n_lira_wider": n_lira_wider,
    "median_abs_delta_sl_pct": median_delta_pct,
    "median_tighter_only_abs_delta_pct": median_tighter_pct,
    "n_lira_loss_a2_win": len(loss_to_win),
    "n_lira_win_a2_loss": len(win_to_loss),
    "loss_to_win_detail": loss_to_win,
    "win_to_loss_detail": win_to_loss,
    "rows": q4_rows,
}

# Per-instrument SL delta stats
q4_per_inst = {}
for inst in ["XAUUSD", "USDJPY"]:
    rows_inst = [r for r in q4_rows if r["symbol"] == inst]
    if not rows_inst:
        q4_per_inst[inst] = {"n": 0}
        continue
    n_t = sum(1 for r in rows_inst if r["lira_tighter"])
    deltas = sorted([abs(r["abs_delta_pct_pts"]) for r in rows_inst if r["abs_delta_pct_pts"] is not None])
    q4_per_inst[inst] = {
        "n": len(rows_inst),
        "n_lira_tighter": n_t,
        "tighter_share": n_t / len(rows_inst),
        "median_abs_delta_pct": deltas[len(deltas)//2] if deltas else None,
        "max_abs_delta_pct": max(deltas) if deltas else None,
    }

# Per-direction
q4_per_dir = {}
for d in ["LONG", "SHORT"]:
    rows_d = [r for r in q4_rows if r["direction"] == d]
    if not rows_d:
        q4_per_dir[d] = {"n": 0}
        continue
    n_t = sum(1 for r in rows_d if r["lira_tighter"])
    deltas = sorted([abs(r["abs_delta_pct_pts"]) for r in rows_d if r["abs_delta_pct_pts"] is not None])
    q4_per_dir[d] = {
        "n": len(rows_d),
        "n_lira_tighter": n_t,
        "tighter_share": n_t / len(rows_d),
        "median_abs_delta_pct": deltas[len(deltas)//2] if deltas else None,
    }

q4_summary["per_instrument"] = q4_per_inst
q4_summary["per_direction"] = q4_per_dir

# Counterfactual: For each LIRA LOSS where SL was tighter, would A2's wider SL have survived?
# We need OHLC to know if price retraced beyond LIRA's SL but not A2's SL.
# We don't have OHLC in all_results.json. But we can estimate from candle_close and outcome.
# For now, report the loss_to_win detail and flag the gap.

# -----------------------------------------------------------------------------
# Q5: Stratum dominance analysis
# -----------------------------------------------------------------------------
print("\nQ5: Stratum dominance")

def stratum_stats(cands):
    s = aggregate_stats(cands)
    return s

q5_strata = {}

# Direction
for d in ["LONG", "SHORT"]:
    lira_d = [c for c in lira_by_key.values() if c.get("direction") == d]
    a2_d = [c for c in a2_by_key.values() if c.get("direction") == d]
    q5_strata[f"direction_{d}"] = {
        "lira": stratum_stats(lira_d),
        "a2": stratum_stats(a2_d),
    }

# Instrument
for inst in ["XAUUSD", "USDJPY"]:
    lira_i = [c for c in lira_by_key.values() if c.get("symbol") == inst]
    a2_i = [c for c in a2_by_key.values() if c.get("symbol") == inst]
    q5_strata[f"inst_{inst}"] = {
        "lira": stratum_stats(lira_i),
        "a2": stratum_stats(a2_i),
    }

# Kill zone
for kz in ["london", "ny", "tokyo"]:
    lira_kz = [c for c in lira_by_key.values() if c.get("kill_zone") == kz]
    a2_kz = [c for c in a2_by_key.values() if c.get("kill_zone") == kz]
    q5_strata[f"kz_{kz}"] = {
        "lira": stratum_stats(lira_kz),
        "a2": stratum_stats(a2_kz),
    }

# h1_direction
for h1 in ["bullish", "bearish", "neutral"]:
    lira_h = [c for c in lira_by_key.values() if c.get("h1_direction") == h1]
    a2_h = [c for c in a2_by_key.values() if c.get("h1_direction") == h1]
    q5_strata[f"h1_{h1}"] = {
        "lira": stratum_stats(lira_h),
        "a2": stratum_stats(a2_h),
    }

# Cross-strata: instrument x direction
for inst in ["XAUUSD", "USDJPY"]:
    for d in ["LONG", "SHORT"]:
        lira_id = [c for c in lira_by_key.values() if c.get("symbol") == inst and c.get("direction") == d]
        a2_id = [c for c in a2_by_key.values() if c.get("symbol") == inst and c.get("direction") == d]
        q5_strata[f"{inst}_{d}"] = {
            "lira": stratum_stats(lira_id),
            "a2": stratum_stats(a2_id),
        }

# Find strata where LIRA dominates (with n >= 5 in both)
q5_lira_dominant_strata = []
for label, s in q5_strata.items():
    li = s["lira"]
    a = s["a2"]
    if li["n_filled"] >= 5 and a["n_filled"] >= 5:
        if li["exp_r"] is not None and a["exp_r"] is not None and li["exp_r"] > a["exp_r"]:
            q5_lira_dominant_strata.append({
                "stratum": label,
                "lira_exp_r": li["exp_r"],
                "a2_exp_r": a["exp_r"],
                "delta": li["exp_r"] - a["exp_r"],
                "lira_n": li["n_filled"],
                "a2_n": a["n_filled"],
                "lira_wr": li["wr"],
                "a2_wr": a["wr"],
            })
q5_lira_dominant_strata.sort(key=lambda x: -x["delta"])

# -----------------------------------------------------------------------------
# Q6: Regime-sliced analysis (s1-s4 vs s5-s8)
# -----------------------------------------------------------------------------
print("\nQ6: Regime split")

def filter_slice_set(cands_dict, slice_filter):
    out = []
    for k, c in cands_dict.items():
        if k[0] in slice_filter:
            out.append(c)
    return out

xau_early = {"xauusd_s1", "xauusd_s2", "xauusd_s3", "xauusd_s4"}
xau_late = {"xauusd_s5", "xauusd_s6", "xauusd_s7", "xauusd_s8"}
usdjpy_early = {"usdjpy_s1", "usdjpy_s2"}  # Jan-Feb
usdjpy_late = {"usdjpy_s3", "usdjpy_s4"}  # Feb-Apr

q6_regime = {
    "xauusd_early_s1_s4": {
        "lira": stratum_stats(filter_slice_set(lira_by_key, xau_early)),
        "a2": stratum_stats(filter_slice_set(a2_by_key, xau_early)),
    },
    "xauusd_late_s5_s8": {
        "lira": stratum_stats(filter_slice_set(lira_by_key, xau_late)),
        "a2": stratum_stats(filter_slice_set(a2_by_key, xau_late)),
    },
    "usdjpy_early_s1_s2": {
        "lira": stratum_stats(filter_slice_set(lira_by_key, usdjpy_early)),
        "a2": stratum_stats(filter_slice_set(a2_by_key, usdjpy_early)),
    },
    "usdjpy_late_s3_s4": {
        "lira": stratum_stats(filter_slice_set(lira_by_key, usdjpy_late)),
        "a2": stratum_stats(filter_slice_set(a2_by_key, usdjpy_late)),
    },
}

# -----------------------------------------------------------------------------
# Q7: Confidence_tier discrimination test
# -----------------------------------------------------------------------------
print("\nQ7: Confidence_tier discrimination")

# For LIRA, group filled CANDs by confidence_tier and compute WR
lira_filled = [c for c in lira_by_key.values() if is_filled(c)]
tier_buckets = defaultdict(list)
for c in lira_filled:
    tier = extract_lira_confidence_tier(c.get("raw_response", ""))
    if tier:
        tier_buckets[tier].append(c)

q7_tier_perf = {}
for tier, cands in tier_buckets.items():
    n = len(cands)
    wins = sum(1 for c in cands if c.get("outcome") == "WIN")
    rs = [r_value(c) for c in cands]
    q7_tier_perf[tier] = {
        "n": n,
        "wins": wins,
        "wr": wins / n if n > 0 else None,
        "exp_r": sum(rs) / n if n > 0 else None,
        "total_r": sum(rs),
    }

# For comparison: V3's confidence_score (always near 72 in baseline) — verify it's rubber-stamp
v3_filled = [c for c in a2_by_key.values() if is_filled(c)]
v3_scores = []
for c in v3_filled:
    s = extract_v3_confidence_score(c.get("raw_response", ""))
    if s is not None:
        v3_scores.append((s, c.get("outcome")))

v3_score_dist = Counter(s for s, _ in v3_scores)

# Bin V3 scores into tiers similar to LIRA
def bin_v3_score(s):
    if s is None:
        return "unknown"
    if s >= 80:
        return "high_conviction"
    if s >= 70:
        return "moderate"
    return "marginal_pass"

v3_tier_perf = defaultdict(list)
for c in v3_filled:
    s = extract_v3_confidence_score(c.get("raw_response", ""))
    bin_label = bin_v3_score(s)
    v3_tier_perf[bin_label].append(c)

q7_v3_binned = {}
for tier, cands in v3_tier_perf.items():
    n = len(cands)
    wins = sum(1 for c in cands if c.get("outcome") == "WIN")
    rs = [r_value(c) for c in cands]
    q7_v3_binned[tier] = {
        "n": n,
        "wins": wins,
        "wr": wins / n if n > 0 else None,
        "exp_r": sum(rs) / n if n > 0 else None,
    }

q7_data = {
    "lira_tier_performance": q7_tier_perf,
    "v3_score_distribution": dict(v3_score_dist),
    "v3_binned_performance": q7_v3_binned,
    "lira_total_filled": len(lira_filled),
}

# -----------------------------------------------------------------------------
# Final dump
# -----------------------------------------------------------------------------
print("\nWriting analysis_data.json")
out = {
    "q1_per_slice": q1_per_slice,
    "q2_divergence": q2_summary,
    "q2_overlap_detail": q2_overlap_detail,
    "q2_lira_only_detail": q2_lira_only_detail,
    "q2_a2_only_detail": q2_a2_only_detail,
    "q3_usdjpy_root_cause": q3_data,
    "q4_sl_delta": q4_summary,
    "q5_strata": q5_strata,
    "q5_lira_dominant_strata": q5_lira_dominant_strata,
    "q6_regime": q6_regime,
    "q7_confidence_tier": q7_data,
}

with open(OUT_DIR / "analysis_data.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)

print("\n=== Top-level summary ===")
print(f"LIRA: {len(lira_by_key)} CAND, {sum(1 for c in lira_by_key.values() if is_filled(c))} filled")
print(f"A2: {len(a2_by_key)} CAND, {sum(1 for c in a2_by_key.values() if is_filled(c))} filled")
print(f"Overlap (same slice/candle/dir): {len(both_keys)}")
print(f"LIRA-only: {len(lira_only_keys)}")
print(f"A2-only: {len(a2_only_keys)}")
print(f"Opposite-direction same candle: {len(opposite_dir_candles)}")
print(f"\nQ4 SL delta: LIRA tighter in {n_lira_tighter}/{len(q4_rows)} pairs")
print(f"  LIRA-LOSS-A2-WIN: {len(loss_to_win)}")
print(f"  LIRA-WIN-A2-LOSS: {len(win_to_loss)}")
print(f"\nQ7 LIRA tier performance:")
for tier, perf in q7_tier_perf.items():
    print(f"  {tier}: n={perf['n']} WR={perf['wr']} ExpR={perf['exp_r']}")
print(f"\nQ5 strata where LIRA dominates (n>=5 each):")
for s in q5_lira_dominant_strata:
    print(f"  {s['stratum']}: LIRA Exp +{s['lira_exp_r']:.3f}R vs A2 +{s['a2_exp_r']:.3f}R (n={s['lira_n']} vs {s['a2_n']})")
