"""Red-Team independent verification of contested LIRA A/B claims (C1-C6).

Reads raw all_results.json files from main branch only:
  - LIRA: research/lira_ab_backtest/slices/*/all_results.json
  - A2 V3: research/a2_v2_active_backtest/slices/*/all_results.json
  - F3 reference: research/f3_backtest_2026-04-24/*/all_results.json

Trusts no prior agent. Each claim is reverified from scratch.
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import sys
from collections import defaultdict

# Force UTF-8 stdout on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path("C:/Users/MSI/Documents/ai-trading-agent")
LIRA_SLICE_DIR = REPO / "research/lira_ab_backtest/slices"
A2_SLICE_DIR = REPO / "research/a2_v2_active_backtest/slices"
F3_SLICE_DIR = REPO / "research/f3_backtest_2026-04-24"


def load_all_slices(slice_root: Path) -> dict[str, list[dict]]:
    """Return {slice_name: [results...]} for every all_results.json under slice_root."""
    out = {}
    for sub in sorted(os.listdir(slice_root)):
        p = slice_root / sub / "all_results.json"
        if not p.exists():
            continue
        with open(p) as f:
            data = json.load(f)
        out[sub] = data.get("results", [])
    return out


def parse_candle_time(s: str | None) -> datetime | None:
    if not s:
        return None
    # Try multiple formats. Most look like "2026-02-04T13:30:00Z" or "2026-02-04T13:30:00+00:00"
    fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s.replace("Z", "+0000") if fmt.endswith("%z") else s.replace("Z", ""), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # Fallback ISO
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def filled_in(slice_results: dict[str, list[dict]]) -> list[tuple[str, dict]]:
    """All filled CANDIDATEs across all slices, returned as (slice_name, result) tuples."""
    out = []
    for sname, results in slice_results.items():
        for r in results:
            if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                out.append((sname, r))
    return out


def cands_in(slice_results: dict[str, list[dict]]) -> list[tuple[str, dict]]:
    out = []
    for sname, results in slice_results.items():
        for r in results:
            if r.get("decision") == "CANDIDATE":
                out.append((sname, r))
    return out


def max_drawdown(r_series: list[float]) -> tuple[float, list[float]]:
    """Return MaxDD + cumulative equity."""
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    cum_series = []
    for r in r_series:
        cum += r
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)
        cum_series.append(cum)
    return max_dd, cum_series


# =====================================================================
# CLAIM C1 — analyze.py MaxDD bug (chronological vs alphabetical)
# =====================================================================
def verify_c1():
    print("=" * 78)
    print("C1: analyze.py MaxDD chronological order verification")
    print("=" * 78)

    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    a2_slices = load_all_slices(A2_SLICE_DIR)

    # Reproduce alpha/analyze.py order: alphabetical slice iteration
    def alphabetical_r_series(slices: dict) -> list[tuple[str, dict, float]]:
        out = []
        for sname in sorted(slices.keys()):  # os.listdir sorted == alphabetical
            for r in slices[sname]:
                if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    out.append((sname, r, r.get("r_multiple", 0.0)))
        return out

    # Beta's chronological re-sort
    def chronological_r_series(slices: dict) -> list[tuple[str, dict, float]]:
        all_filled = []
        for sname, results in slices.items():
            for r in results:
                if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    ct = parse_candle_time(r.get("candle_time", ""))
                    all_filled.append((sname, r, r.get("r_multiple", 0.0), ct))
        all_filled.sort(key=lambda x: (x[3] or datetime(1900, 1, 1, tzinfo=timezone.utc)))
        return [(s, r, rm) for (s, r, rm, _ct) in all_filled]

    for label, slices in [("LIRA", lira_slices), ("A2 V3", a2_slices)]:
        print(f"\n--- {label} ---")
        alpha_order = alphabetical_r_series(slices)
        chrono_order = chronological_r_series(slices)
        print(f"  n filled: {len(alpha_order)} (alpha) vs {len(chrono_order)} (chrono)")

        # Show first 6 entries each
        print("  First 6 alphabetical:")
        for (s, _, rm) in alpha_order[:6]:
            print(f"    {s} → R={rm:+.2f}")
        print("  First 6 chronological:")
        for (s, r, rm) in chrono_order[:6]:
            print(f"    {s} {r.get('candle_time')} → R={rm:+.2f}")

        alpha_r = [rm for (_, _, rm) in alpha_order]
        chrono_r = [rm for (_, _, rm) in chrono_order]
        alpha_dd, _ = max_drawdown(alpha_r)
        chrono_dd, chrono_cum = max_drawdown(chrono_r)
        print(f"  Total R: alpha sum={sum(alpha_r):+.2f}, chrono sum={sum(chrono_r):+.2f}")
        print(f"  MaxDD alphabetical: {alpha_dd:.2f}R")
        print(f"  MaxDD chronological: {chrono_dd:.2f}R")
        if chrono_cum:
            peak_idx = max(range(len(chrono_cum)), key=lambda i: chrono_cum[i])
            print(f"  Chronological peak +{chrono_cum[peak_idx]:.2f}R at trade idx {peak_idx} ({chrono_order[peak_idx][1].get('candle_time')})")
            print(f"  Chronological end +{chrono_cum[-1]:.2f}R")

        # The pre-reg gate is 8R
        gate_alpha = "PASS" if alpha_dd <= 8.0 else "FAIL"
        gate_chrono = "PASS" if chrono_dd <= 8.0 else "FAIL"
        print(f"  Pre-reg gate (MaxDD ≤ 8R): alpha={gate_alpha}, chrono={gate_chrono}")


# =====================================================================
# CLAIM C2 — Coverage gap on USDJPY (A2 cut off earlier?)
# =====================================================================
def verify_c2():
    print("\n" + "=" * 78)
    print("C2: USDJPY per-slice coverage analysis")
    print("=" * 78)

    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    a2_slices = load_all_slices(A2_SLICE_DIR)

    for slice_name in ["usdjpy_s1", "usdjpy_s2", "usdjpy_s3", "usdjpy_s4"]:
        if slice_name not in lira_slices or slice_name not in a2_slices:
            print(f"  {slice_name}: MISSING")
            continue

        # Collect candle_times where cost > 0 (i.e. an evaluation actually happened)
        def evaluated_candle_times(rows):
            return [r.get("candle_time") for r in rows if r.get("cost", 0) > 0]

        lira_eval = evaluated_candle_times(lira_slices[slice_name])
        a2_eval = evaluated_candle_times(a2_slices[slice_name])

        lira_eval_dt = sorted([t for t in lira_eval if t])
        a2_eval_dt = sorted([t for t in a2_eval if t])

        print(f"\n--- {slice_name} ---")
        print(f"  LIRA evaluations (cost>0): {len(lira_eval)}, first={lira_eval_dt[0] if lira_eval_dt else 'N/A'}, last={lira_eval_dt[-1] if lira_eval_dt else 'N/A'}")
        print(f"  A2   evaluations (cost>0): {len(a2_eval)},  first={a2_eval_dt[0] if a2_eval_dt else 'N/A'},  last={a2_eval_dt[-1] if a2_eval_dt else 'N/A'}")

        # Compute LIRA-only USDJPY LONG CANDs in/out of A2 coverage
        a2_eval_set = set(a2_eval)
        # All LIRA CANDs
        lira_cands_all = [r for r in lira_slices[slice_name] if r.get("decision") == "CANDIDATE"]
        # LIRA USDJPY LONG CANDs
        lira_long_cands = [r for r in lira_cands_all if r.get("direction") == "LONG"]
        # A2 USDJPY LONG CANDs (just for count)
        a2_long_cands = [r for r in a2_slices[slice_name] if r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"]

        # In coverage = A2 also evaluated this candle
        lira_long_in_cov = [r for r in lira_long_cands if r.get("candle_time") in a2_eval_set]
        lira_long_out_cov = [r for r in lira_long_cands if r.get("candle_time") not in a2_eval_set]

        print(f"  LIRA USDJPY LONG CANDs: total={len(lira_long_cands)}, in_A2_cov={len(lira_long_in_cov)}, out_A2_cov={len(lira_long_out_cov)}")
        print(f"  A2 USDJPY LONG CANDs: total={len(a2_long_cands)}")

    # Aggregate "+1 vs +14" check
    print("\n--- AGGREGATE: USDJPY LONG CANDs ---")
    lira_total_long = 0
    a2_total_long = 0
    lira_long_in_cov_total = 0
    for slice_name in ["usdjpy_s1", "usdjpy_s2", "usdjpy_s3", "usdjpy_s4"]:
        a2_eval_set = set(r.get("candle_time") for r in a2_slices.get(slice_name, []) if r.get("cost", 0) > 0)
        lira_long = [r for r in lira_slices.get(slice_name, []) if r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"]
        a2_long = [r for r in a2_slices.get(slice_name, []) if r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"]
        lira_total_long += len(lira_long)
        a2_total_long += len(a2_long)
        lira_long_in_cov_total += sum(1 for r in lira_long if r.get("candle_time") in a2_eval_set)
    print(f"  LIRA USDJPY LONG total: {lira_total_long}")
    print(f"  A2   USDJPY LONG total: {a2_total_long}")
    print(f"  LIRA USDJPY LONG within A2 coverage: {lira_long_in_cov_total}")
    print(f"  Naive delta (LIRA - A2): {lira_total_long - a2_total_long}")
    print(f"  Coverage-matched delta (LIRA_in_cov - A2_total): {lira_long_in_cov_total - a2_total_long}")


# =====================================================================
# CLAIM C3 — SL-tightness magnitude (50× inflation?)
# =====================================================================
def verify_c3():
    print("\n" + "=" * 78)
    print("C3: SL-tightness magnitude (28 same-candle/dir pairs)")
    print("=" * 78)

    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    a2_slices = load_all_slices(A2_SLICE_DIR)

    # Build (slice, candle_time, direction) → result for both
    def index(slices):
        out = {}
        for sname, results in slices.items():
            for r in results:
                if r.get("decision") == "CANDIDATE":
                    key = (sname, r.get("candle_time"), r.get("direction"))
                    out[key] = r
        return out

    lira_idx = index(lira_slices)
    a2_idx = index(a2_slices)
    common_keys = set(lira_idx.keys()) & set(a2_idx.keys())
    print(f"  Common (slice, candle_time, dir) pairs: {len(common_keys)}")

    deltas_pp = []  # signed: (LIRA - A2) % of entry, in percentage points (×100 of fraction)
    abs_deltas_pp = []
    lira_tighter_count = 0
    pair_details = []

    for key in sorted(common_keys, key=lambda x: (x[0], x[1])):
        lr = lira_idx[key]
        ar = a2_idx[key]
        lentry = lr.get("entry_price") or lr.get("entry")
        lsl = lr.get("stop_loss") or lr.get("sl")
        aentry = ar.get("entry_price") or ar.get("entry")
        asl = ar.get("stop_loss") or ar.get("sl")
        direction = lr.get("direction")

        if not all(isinstance(v, (int, float)) and v > 0 for v in (lentry, lsl, aentry, asl)):
            continue

        # SL distance from entry, as fraction of entry
        l_sl_frac = abs(lentry - lsl) / lentry  # fraction
        a_sl_frac = abs(aentry - asl) / aentry
        # Signed: LIRA_frac - A2_frac (in percentage points = fraction × 100)
        delta_pp = (l_sl_frac - a_sl_frac) * 100
        deltas_pp.append(delta_pp)
        abs_deltas_pp.append(abs(delta_pp))
        if l_sl_frac < a_sl_frac:
            lira_tighter_count += 1
        pair_details.append({
            "slice": key[0], "candle": key[1], "dir": direction,
            "lira_entry": lentry, "lira_sl": lsl,
            "a2_entry": aentry, "a2_sl": asl,
            "delta_pp": delta_pp,
            "lira_outcome": lr.get("outcome"),
            "a2_outcome": ar.get("outcome"),
        })

    n = len(deltas_pp)
    deltas_pp_sorted = sorted(deltas_pp)
    abs_deltas_pp.sort()
    median_signed = deltas_pp_sorted[n // 2] if n else 0
    mean_signed = sum(deltas_pp) / n if n else 0
    median_abs = abs_deltas_pp[n // 2] if n else 0
    mean_abs = sum(abs_deltas_pp) / n if n else 0
    print(f"  n usable pairs (positive entries+SL): {n}")
    if n == 0:
        print("  no usable pairs; skipping detail")
        return []
    print(f"  LIRA tighter share: {lira_tighter_count}/{n} = {100*lira_tighter_count/n:.1f}%")
    print(f"  Median signed delta (LIRA% - A2%): {median_signed:+.4f}pp")
    print(f"  Mean signed delta: {mean_signed:+.4f}pp")
    print(f"  Median |delta|: {median_abs:.4f}pp")
    print(f"  Mean |delta|: {mean_abs:.4f}pp")

    # Wilcoxon signed-rank approximation: sign-test for nonzero differences
    nonzero = [d for d in deltas_pp if abs(d) > 1e-12]
    n_lira_tighter_nonzero = sum(1 for d in nonzero if d < 0)  # LIRA frac smaller = LIRA tighter
    n_lira_wider_nonzero = sum(1 for d in nonzero if d > 0)
    print(f"  Nonzero diffs: {len(nonzero)}; LIRA tighter (signed<0): {n_lira_tighter_nonzero}, looser (signed>0): {n_lira_wider_nonzero}")

    # Compare per-instrument
    xau_deltas = [d["delta_pp"] for d in pair_details if d["slice"].startswith("xauusd")]
    jpy_deltas = [d["delta_pp"] for d in pair_details if d["slice"].startswith("usdjpy")]
    print(f"\n  XAUUSD pairs: n={len(xau_deltas)}, mean signed={sum(xau_deltas)/max(1,len(xau_deltas)):+.4f}pp, "
          f"LIRA tighter share: {sum(1 for d in xau_deltas if d<0)}/{len(xau_deltas)}")
    print(f"  USDJPY pairs: n={len(jpy_deltas)}, mean signed={sum(jpy_deltas)/max(1,len(jpy_deltas)):+.4f}pp, "
          f"LIRA tighter share: {sum(1 for d in jpy_deltas if d<0)}/{len(jpy_deltas)}")

    # Outcome flips
    flips_a2win_liraloss = sum(1 for p in pair_details if p["a2_outcome"] == "WIN" and p["lira_outcome"] == "LOSS")
    flips_a2loss_lirawin = sum(1 for p in pair_details if p["a2_outcome"] == "LOSS" and p["lira_outcome"] == "WIN")
    print(f"  WIN→LOSS (A2 WIN, LIRA LOSS): {flips_a2win_liraloss}")
    print(f"  LOSS→WIN (A2 LOSS, LIRA WIN): {flips_a2loss_lirawin}")

    return pair_details


# =====================================================================
# CLAIM C4 — XAUUSD-only edge for LIRA
# =====================================================================
def verify_c4():
    print("\n" + "=" * 78)
    print("C4: XAUUSD-only LIRA vs A2 V3 stats")
    print("=" * 78)

    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    a2_slices = load_all_slices(A2_SLICE_DIR)

    for label, slices in [("LIRA", lira_slices), ("A2 V3", a2_slices)]:
        # Aggregate XAUUSD only
        rs = []
        wins = 0
        for sname, results in slices.items():
            if not sname.startswith("xauusd"):
                continue
            for r in results:
                if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    rm = r.get("r_multiple", 0.0)
                    rs.append(rm)
                    if r.get("outcome") == "WIN":
                        wins += 1
        n = len(rs)
        wr = wins / n if n else 0
        exp = sum(rs) / n if n else 0
        z = 1.96
        if n > 0:
            denom = 1 + z * z / n
            centre = (wr + z * z / (2 * n)) / denom
            half = (z * math.sqrt(wr * (1 - wr) / n + z * z / (4 * n * n))) / denom
            ci = (max(0, centre - half), min(1, centre + half))
        else:
            ci = (0, 0)
        print(f"  {label} XAUUSD: n={n} WR={100*wr:.1f}% Wilson95=[{100*ci[0]:.1f}, {100*ci[1]:.1f}] Exp R={exp:+.3f}")

    # Bootstrap diff CI on Exp R (LIRA - A2)
    import random
    rng = random.Random(31)
    lira_rs = []
    a2_rs = []
    for sname, results in lira_slices.items():
        if sname.startswith("xauusd"):
            for r in results:
                if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    lira_rs.append(r.get("r_multiple", 0.0))
    for sname, results in a2_slices.items():
        if sname.startswith("xauusd"):
            for r in results:
                if r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    a2_rs.append(r.get("r_multiple", 0.0))
    diffs = []
    for _ in range(5000):
        l_sample = [lira_rs[rng.randint(0, len(lira_rs) - 1)] for _ in range(len(lira_rs))]
        a_sample = [a2_rs[rng.randint(0, len(a2_rs) - 1)] for _ in range(len(a2_rs))]
        diffs.append(sum(l_sample) / len(l_sample) - sum(a_sample) / len(a_sample))
    diffs.sort()
    lo = diffs[int(0.025 * 5000)]
    hi = diffs[int(0.975 * 5000) - 1]
    print(f"\n  Bootstrap diff (LIRA - A2 Exp R, 5000 iter): mean={sum(diffs)/5000:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]")
    print(f"  Includes zero? {'YES (NOT statistically significant)' if lo < 0 < hi else 'NO (significant)'}")

    # Per-direction breakdown
    print("\n  XAUUSD per-direction breakdown:")
    for dir in ["LONG", "SHORT"]:
        for label, slices in [("LIRA", lira_slices), ("A2 V3", a2_slices)]:
            rs = []
            wins = 0
            for sname, results in slices.items():
                if not sname.startswith("xauusd"):
                    continue
                for r in results:
                    if (r.get("decision") == "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN")
                            and r.get("direction") == dir):
                        rs.append(r.get("r_multiple", 0.0))
                        if r.get("outcome") == "WIN":
                            wins += 1
            n = len(rs)
            wr = wins / n if n else 0
            exp = sum(rs) / n if n else 0
            print(f"    {label} XAUUSD {dir}: n={n} WR={100*wr:.1f}% Exp={exp:+.3f}R")


# =====================================================================
# CLAIM C5 — Stale-OB anchoring on USDJPY (entry=154.88 etc)
# =====================================================================
def verify_c5():
    print("\n" + "=" * 78)
    print("C5: USDJPY LONG entry-price comparison (stale-OB anchoring)")
    print("=" * 78)

    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    a2_slices = load_all_slices(A2_SLICE_DIR)

    # All LIRA USDJPY LONG fills + entries
    print("\n  LIRA USDJPY LONG entries (filled, sample):")
    lira_jpy_long_entries = []
    for sname, results in lira_slices.items():
        if not sname.startswith("usdjpy"):
            continue
        for r in results:
            if (r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"
                    and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN")):
                lira_jpy_long_entries.append({
                    "slice": sname, "candle": r.get("candle_time"),
                    "entry": r.get("entry_price") or r.get("entry"), "sl": r.get("stop_loss") or r.get("sl"),
                    "outcome": r.get("outcome"), "r": r.get("r_multiple", 0.0),
                })
    # Group by entry value
    entry_groups = defaultdict(int)
    for e in lira_jpy_long_entries:
        ent = e["entry"]
        if ent is not None:
            # Bucket to nearest 0.05 USDJPY
            bucket = round(ent * 20) / 20
            entry_groups[bucket] += 1
    print(f"  LIRA USDJPY LONG fill entries (n={len(lira_jpy_long_entries)}): top entry-buckets:")
    for ent, cnt in sorted(entry_groups.items(), key=lambda x: -x[1])[:8]:
        print(f"    entry≈{ent:.2f}: {cnt} fills")

    # Same for A2
    print("\n  A2 USDJPY LONG entries (filled, sample):")
    a2_jpy_long_entries = []
    for sname, results in a2_slices.items():
        if not sname.startswith("usdjpy"):
            continue
        for r in results:
            if (r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"
                    and r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN")):
                a2_jpy_long_entries.append({
                    "slice": sname, "candle": r.get("candle_time"),
                    "entry": r.get("entry_price") or r.get("entry"), "sl": r.get("stop_loss") or r.get("sl"),
                    "outcome": r.get("outcome"), "r": r.get("r_multiple", 0.0),
                })
    entry_groups_a2 = defaultdict(int)
    for e in a2_jpy_long_entries:
        ent = e["entry"]
        if ent is not None:
            bucket = round(ent * 20) / 20
            entry_groups_a2[bucket] += 1
    print(f"  A2 USDJPY LONG fill entries (n={len(a2_jpy_long_entries)}): top entry-buckets:")
    for ent, cnt in sorted(entry_groups_a2.items(), key=lambda x: -x[1])[:8]:
        print(f"    entry≈{ent:.2f}: {cnt} fills")

    # Now look at usdjpy_s2 raw CANDs in detail (alpha says LIRA emits 154.88 on 65 candles)
    print("\n  USDJPY_s2 LIRA CAND/REJECT entry distribution:")
    s2 = lira_slices.get("usdjpy_s2", [])
    s2_cands = [r for r in s2 if r.get("decision") == "CANDIDATE"]
    s2_long_cands = [r for r in s2_cands if r.get("direction") == "LONG"]
    print(f"    s2 LIRA CANDs: {len(s2_cands)}, LONG: {len(s2_long_cands)}")
    s2_buckets = defaultdict(int)
    for r in s2_long_cands:
        ent = r.get("entry_price") or r.get("entry")
        if ent is not None:
            bucket = round(ent * 20) / 20
            s2_buckets[bucket] += 1
    print(f"    s2 LIRA LONG entry buckets:")
    for ent, cnt in sorted(s2_buckets.items(), key=lambda x: -x[1])[:8]:
        print(f"      entry≈{ent:.2f}: {cnt} fills")

    # Compare to A2 s2 LONG entries
    s2a = a2_slices.get("usdjpy_s2", [])
    s2a_long_cands = [r for r in s2a if r.get("decision") == "CANDIDATE" and r.get("direction") == "LONG"]
    print(f"    s2 A2 LONG CANDs: {len(s2a_long_cands)}")
    s2a_buckets = defaultdict(int)
    for r in s2a_long_cands:
        ent = r.get("entry_price") or r.get("entry")
        if ent is not None:
            bucket = round(ent * 20) / 20
            s2a_buckets[bucket] += 1
    for ent, cnt in sorted(s2a_buckets.items(), key=lambda x: -x[1])[:8]:
        print(f"      entry≈{ent:.2f}: {cnt} fills")


# =====================================================================
# CLAIM C6 — γ self-consistency + δ confidence_tier (verify by reading)
# =====================================================================
def verify_c6():
    print("\n" + "=" * 78)
    print("C6: γ replays + δ confidence_tier")
    print("=" * 78)

    # γ: Read the 4 replay files in the gamma directory
    GAMMA_DIR = Path("C:/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-a803587bd36113725/research/lira_ab_deep_forensic/gamma")
    if not GAMMA_DIR.exists():
        print("  gamma worktree not accessible, skipping")
    else:
        replay_files = sorted([f for f in os.listdir(GAMMA_DIR) if f.startswith("replays_") and f.endswith(".jsonl")])
        print(f"  γ replay files: {len(replay_files)}")
        for rf in replay_files:
            with open(GAMMA_DIR / rf) as f:
                lines = f.readlines()
            decisions = []
            directions = []
            for ln in lines:
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                # The replay file structure may have nested. Try multiple paths.
                pa = d.get("primary_analysis") or d.get("response") or {}
                # Could also be top-level
                decisions.append(d.get("decision") or pa.get("decision"))
                directions.append(d.get("direction") or pa.get("direction") or "")
            print(f"    {rf}: n={len(decisions)} decisions={set(decisions)} directions={set(directions)}")

    # δ: confidence_tier — recompute from raw_response on lira slices
    print("\n  δ confidence_tier verification:")
    lira_slices = load_all_slices(LIRA_SLICE_DIR)
    tier_stats = defaultdict(lambda: {"n": 0, "filled": 0, "wins": 0, "r_sum": 0.0})

    for sname, results in lira_slices.items():
        for r in results:
            if r.get("decision") != "CANDIDATE":
                continue
            # Try to read confidence_tier from multiple paths
            tier = None
            raw = r.get("raw_response", "")
            if isinstance(raw, str):
                # Regex search
                m = re.search(r'"confidence_tier"\s*:\s*"([^"]+)"', raw)
                if m:
                    tier = m.group(1)
            if tier is None:
                tier = r.get("confidence_tier")
            tier = tier or "unknown"
            tier_stats[tier]["n"] += 1
            if r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                tier_stats[tier]["filled"] += 1
                tier_stats[tier]["r_sum"] += r.get("r_multiple", 0.0)
                if r.get("outcome") == "WIN":
                    tier_stats[tier]["wins"] += 1

    for tier in sorted(tier_stats.keys()):
        s = tier_stats[tier]
        wr = s["wins"] / s["filled"] if s["filled"] else 0
        exp = s["r_sum"] / s["filled"] if s["filled"] else 0
        print(f"    tier={tier}: n_cand={s['n']}, n_filled={s['filled']}, wr={100*wr:.1f}%, ExpR={exp:+.3f}")

    # Two-prop z high vs moderate
    if "high_conviction" in tier_stats and "moderate" in tier_stats:
        h = tier_stats["high_conviction"]
        m = tier_stats["moderate"]
        if h["filled"] and m["filled"]:
            p_pool = (h["wins"] + m["wins"]) / (h["filled"] + m["filled"])
            se = math.sqrt(p_pool * (1 - p_pool) * (1 / h["filled"] + 1 / m["filled"])) if 0 < p_pool < 1 else 0
            if se > 0:
                z = (h["wins"] / h["filled"] - m["wins"] / m["filled"]) / se
                p = math.erfc(abs(z) / math.sqrt(2))
                print(f"    Two-prop z high_conviction vs moderate: z={z:.3f}, p={p:.4f}")


def main():
    verify_c1()
    verify_c2()
    pair_details = verify_c3()
    verify_c4()
    verify_c5()
    verify_c6()

    # Save pair-level SL detail for inspection
    out_path = Path("C:/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-redteam-1777079025/research/lira_ab_deep_forensic/red_team/sl_pair_details.json")
    with open(out_path, "w") as f:
        json.dump(pair_details, f, indent=2, default=str)
    print(f"\nWrote SL pair details: {out_path}")


if __name__ == "__main__":
    main()
