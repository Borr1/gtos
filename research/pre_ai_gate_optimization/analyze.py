#!/usr/bin/env python3
"""Pre-AI gate optimization analysis.

Reads ``rich_per_candle.csv`` (9,069 KZ candles, Q1 2026, 5 instruments)
and the A1 ``merged_data.jsonl`` (1,142 AI-eval rows for XAUUSD+USDJPY
with realized outcomes), then evaluates a panel of gate-tightening
proposals against:

  * skip-rate impact (how many AI calls saved)
  * lost-CAND impact on the A1 sample where it intersects
  * realized-R cost projection per month under each tighter gate

Outputs:
  * ``analysis.json`` — full per-gate result table + Pareto data
  * Console summary + Pareto table (also written to stdout for the report)
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent

RICH_CSV = ROOT / "rich_per_candle.csv"
A1_JSONL = PROJECT / "research" / "phase1_full_extraction" / "merged_data.jsonl"
UNIFIED_TRADES = PROJECT / "research" / "phase1_xauusd_reverse_engineering" / "unified_trades.csv"
A2_DIR = PROJECT / "research" / "a2_v2_active_backtest" / "slices"

OUT = ROOT / "analysis.json"

# Cost per AI call (Sonnet 4.6, max effort). EXTRACTION.md uses ~$0.029/call;
# CLAUDE.md mentions ~$60/mo at ~17 trades. We treat $0.029/call as the
# average over evaluations (NOT just CANDs).
COST_PER_CALL = 0.029
Q1_DAYS = 89        # Jan 2 - Mar 31 weekday calendar coverage
TRADING_DAYS_PER_MONTH = 21


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def fmt_pct(x):
    return f"{100*x:.2f}%"


def fmt_r(x):
    return f"{x:+.3f}R"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_rich():
    with open(RICH_CSV) as f:
        rows = list(csv.DictReader(f))
    # Cast numeric fields
    for r in rows:
        for k in (
            "poi_ob_retest", "poi_fvg_fill", "poi_breaker_re_entry",
            "skip_baseline", "skip_multi",
            "h1_unmit_ob_count", "h1_unmit_ob_count_aligned",
            "h1_min_touch_aligned", "h1_max_touch_aligned",
            "h1_unret_breaker_aligned", "m15_unfilled_fvg",
            "m15_unfilled_fvg_aligned",
        ):
            r[k] = int(r[k])
        for k in (
            "h1_min_dist_atr_aligned", "h1_breaker_dist_atr_min",
            "m15_fvg_dist_atr_min", "h1_atr", "m15_close",
        ):
            r[k] = float(r[k])
    return rows


def load_a1():
    rows = []
    with open(A1_JSONL) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_unified():
    with open(UNIFIED_TRADES) as f:
        return list(csv.DictReader(f))


def load_a2_cand_rows():
    """A2 backtest CAND rows (v2-active). Used as a corroboration sample."""
    rows = []
    for slc in sorted(A2_DIR.glob("*/all_results.json")):
        with open(slc) as f:
            d = json.load(f)
        for r in d.get("results", []):
            if r.get("decision") == "CANDIDATE":
                rows.append(r)
    return rows


def section_2b_a2_crosscheck(rich, a2_cand_rows):
    """Cross-validate gate proposals against A2 (v2-active) CAND outcomes.

    A2 is the v2 backtest — the actual production-equivalent of what the live
    fleet will produce. If a gate skips A2 CANDs that filled with positive R,
    the proposal would have lost real expected R.
    """
    rich_by_key = {(r["symbol"], r["candle_time"]): r for r in rich}

    out = {}
    for gate_name, fn in GATES.items():
        skip_count = 0
        skipped_rs = []
        skipped_wins = 0
        skipped_losses = 0
        per_inst_lost = defaultdict(lambda: {"n": 0, "rs": [], "wins": 0})
        for r in a2_cand_rows:
            sym = r.get("symbol")
            ts = r.get("candle_time")
            rich_row = rich_by_key.get((sym, ts))
            if rich_row is None:
                continue
            if not fn(rich_row):
                continue
            skip_count += 1
            per_inst_lost[sym]["n"] += 1
            outcome = r.get("outcome")
            r_mul = r.get("r_multiple")
            if outcome in ("WIN", "LOSS", "BE") and r_mul is not None:
                skipped_rs.append(float(r_mul))
                per_inst_lost[sym]["rs"].append(float(r_mul))
                if outcome == "WIN":
                    skipped_wins += 1
                    per_inst_lost[sym]["wins"] += 1
                elif outcome == "LOSS":
                    skipped_losses += 1
        out[gate_name] = {
            "a2_cand_skipped": skip_count,
            "a2_filled_skipped": len(skipped_rs),
            "a2_wins_skipped": skipped_wins,
            "a2_losses_skipped": skipped_losses,
            "a2_total_r_skipped": sum(skipped_rs),
            "a2_lost_r_per_month_proj": (sum(skipped_rs) / Q1_DAYS) * TRADING_DAYS_PER_MONTH,
            "per_instrument": dict(per_inst_lost),
        }
    return out


# ---------------------------------------------------------------------------
# Section 1: per-instrument funnel + value-per-AI-call
# ---------------------------------------------------------------------------

def section_1_funnel(rich, a1, unified):
    """Build the current-state per-instrument funnel under multi-framework."""
    # Replay totals per instrument
    per_inst = defaultdict(lambda: {"n": 0, "skip_multi": 0, "skip_baseline": 0})
    for r in rich:
        per_inst[r["symbol"]]["n"] += 1
        per_inst[r["symbol"]]["skip_multi"] += r["skip_multi"]
        per_inst[r["symbol"]]["skip_baseline"] += r["skip_baseline"]

    # AI CAND rate from A1 (XAUUSD + USDJPY); from A2 also where overlapping
    a1_funnel = defaultdict(lambda: {"ai_eval": 0, "cand": 0, "filled": 0,
                                     "wins": 0, "losses": 0, "be": 0,
                                     "rs": []})
    for r in a1:
        sym = r["symbol"]
        a1_funnel[sym]["ai_eval"] += 1
        if r.get("out_decision") == "CANDIDATE":
            a1_funnel[sym]["cand"] += 1
            outcome = r.get("out_outcome")
            if outcome in ("WIN", "LOSS", "BE"):
                a1_funnel[sym]["filled"] += 1
                a1_funnel[sym]["rs"].append(float(r.get("out_r_multiple") or 0))
                if outcome == "WIN":
                    a1_funnel[sym]["wins"] += 1
                elif outcome == "LOSS":
                    a1_funnel[sym]["losses"] += 1
                elif outcome == "BE":
                    a1_funnel[sym]["be"] += 1

    # Unified (any source) — per-instrument Q1 realized stats.
    unified_q1 = defaultdict(lambda: {"n": 0, "wins": 0, "rs": []})
    for r in unified:
        if r["date"][:7] not in ("2026-01", "2026-02", "2026-03"):
            continue
        sym = r["symbol"]
        unified_q1[sym]["n"] += 1
        if r["outcome"] == "WIN":
            unified_q1[sym]["wins"] += 1
        try:
            unified_q1[sym]["rs"].append(float(r.get("r_multiple") or 0))
        except (ValueError, TypeError):
            pass

    out = []
    for sym in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        d = per_inst[sym]
        n = d["n"]
        sm = d["skip_multi"]
        ai_calls = n - sm  # multi-framework AI-eval count
        skip_rate = sm / n if n else 0

        # AI CAND data: A1 is direct (XAUUSD+USDJPY); for others use unified Q1 as proxy
        a1d = a1_funnel.get(sym, {})
        cand_rate = a1d.get("cand", 0) / max(a1d.get("ai_eval", 0), 1) if a1d.get("ai_eval") else None
        filled_rate_of_cand = a1d.get("filled", 0) / max(a1d.get("cand", 0), 1) if a1d.get("cand") else None
        wr = a1d.get("wins", 0) / max(a1d.get("filled", 0), 1) if a1d.get("filled") else None
        exp_r = (sum(a1d.get("rs", [])) / len(a1d["rs"])) if a1d.get("rs") else None

        un = unified_q1.get(sym, {})
        un_wr = un.get("wins", 0) / max(un.get("n", 0), 1) if un.get("n") else None
        un_exp = (sum(un.get("rs", [])) / len(un["rs"])) if un.get("rs") else None

        # Value per AI call = realized R per call
        # If A1 data exists, use it (XAUUSD/USDJPY).
        # Otherwise use unified Q1 trade R / projected eval count.
        # Eval count under multi-framework: ai_calls (which is Q1 total).
        if a1d.get("filled"):
            r_per_call_a1 = sum(a1d["rs"]) / max(a1d.get("ai_eval", 0), 1)
        else:
            r_per_call_a1 = None

        out.append({
            "symbol": sym,
            "kz_candles_q1": n,
            "skip_multi_q1": sm,
            "skip_rate_multi": skip_rate,
            "ai_calls_q1": ai_calls,
            "ai_calls_per_month": ai_calls / Q1_DAYS * TRADING_DAYS_PER_MONTH,
            "ai_dollars_per_month": ai_calls / Q1_DAYS * TRADING_DAYS_PER_MONTH * COST_PER_CALL,
            "a1_ai_eval": a1d.get("ai_eval"),
            "a1_cand": a1d.get("cand"),
            "a1_cand_rate": cand_rate,
            "a1_filled": a1d.get("filled"),
            "a1_filled_rate_of_cand": filled_rate_of_cand,
            "a1_wins": a1d.get("wins"),
            "a1_wr": wr,
            "a1_exp_r": exp_r,
            "a1_realized_r_per_ai_call": r_per_call_a1,
            "unified_q1_n": un.get("n"),
            "unified_q1_wr": un_wr,
            "unified_q1_exp_r": un_exp,
        })
    return out


# ---------------------------------------------------------------------------
# Section 2: gate-tightening proposals
# ---------------------------------------------------------------------------

GATES = {
    # Baseline — current production multi-framework gate.
    "G0_MULTI": lambda r: r["skip_multi"] == 1,
    # G2.1: require directional bias
    "G2_1_BIAS_REQ": lambda r: r["skip_multi"] == 1 or r["bias"] == "no_bias",
    # G2.2 variants — min-quality POI
    "G2_2_TOUCH_GE3_FAR_DIST_2ATR":
        lambda r: r["skip_multi"] == 1 or _g22(r, max_touch=3, max_dist_atr=2.0),
    "G2_2_TOUCH_GE3_FAR_DIST_3ATR":
        lambda r: r["skip_multi"] == 1 or _g22(r, max_touch=3, max_dist_atr=3.0),
    "G2_2_TOUCH_GE4_FAR_DIST_2ATR":
        lambda r: r["skip_multi"] == 1 or _g22(r, max_touch=4, max_dist_atr=2.0),
    # G2.3: distance-only (skip if everything is far away)
    "G2_3_DIST_GT_2ATR": lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=2.0),
    "G2_3_DIST_GT_3ATR": lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=3.0),
    "G2_3_DIST_GT_4ATR": lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=4.0),
    "G2_3_DIST_GT_5ATR": lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=5.0),
    "G2_3_DIST_GT_6ATR": lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=6.0),
    # Combined: bias-required + far OB (most aggressive realistic)
    "G2_BIAS_AND_DIST_3ATR":
        lambda r: r["skip_multi"] == 1 or r["bias"] == "no_bias" or _g23(r, max_dist_atr=3.0),
    # Less-aggressive combined: bias-required + touch≥4 stale
    "G2_BIAS_AND_TOUCH_GE4":
        lambda r: r["skip_multi"] == 1 or r["bias"] == "no_bias" or _g22(r, max_touch=4, max_dist_atr=99.0),
    # Conservative: only skip extreme far-distance + count >= 1 evidence
    "G2_CONSERVATIVE_DIST_5ATR":
        lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=5.0),
    "G2_CONSERVATIVE_DIST_6ATR":
        lambda r: r["skip_multi"] == 1 or _g23(r, max_dist_atr=6.0),
}


def _g22(r, max_touch, max_dist_atr):
    """Return True if multi-framework would currently NOT skip but *G2.2 conditions
    still classify it as low-quality and we should skip*.

    G2.2 fires when EVERY POI source is degenerate: aligned OB has touch>=max_touch
    AND distance>=max_dist_atr, AND no breaker, AND no aligned FVG (or aligned FVG
    is also far).
    """
    if r["skip_multi"] == 1:
        return False  # already skipped
    # If breaker is available within reach, don't skip
    if r["h1_unret_breaker_aligned"] >= 1 and 0 < r["h1_breaker_dist_atr_min"] <= max_dist_atr:
        return False
    # If there's an OB AT REASONABLE distance/touch, don't skip
    if r["poi_ob_retest"] == 1:
        ob_min_touch = r["h1_min_touch_aligned"]
        ob_dist = r["h1_min_dist_atr_aligned"]
        # Find an OB with EITHER fresh touch OR close distance
        # If ANY aligned OB has touch < max_touch AND dist <= max_dist_atr → don't skip
        # Approximate: if min_touch < max_touch AND min_dist <= max_dist_atr it could be the same OB; conservative pass.
        if ob_min_touch >= 0 and ob_min_touch < max_touch and 0 < ob_dist <= max_dist_atr:
            return False
        # If touch is OK but distance is bad, still allow if FVG aligned + close
        if ob_min_touch >= 0 and ob_min_touch < max_touch:
            if r["m15_unfilled_fvg_aligned"] >= 1 and 0 < r["m15_fvg_dist_atr_min"] <= max_dist_atr:
                return False
    # FVG-only path: if no usable OB but a close aligned FVG exists, don't skip
    if r["poi_fvg_fill"] == 1 and r["m15_unfilled_fvg_aligned"] >= 1:
        if 0 < r["m15_fvg_dist_atr_min"] <= max_dist_atr:
            return False
    # Otherwise — every POI is either far or stale → SKIP
    return True


def _g23(r, max_dist_atr):
    """Distance-only skip: if every available POI is > max_dist_atr away, skip."""
    if r["skip_multi"] == 1:
        return False
    # If ANY POI source is within reach, don't skip.
    if r["poi_ob_retest"] == 1 and 0 < r["h1_min_dist_atr_aligned"] <= max_dist_atr:
        return False
    if r["poi_breaker_re_entry"] == 1 and 0 < r["h1_breaker_dist_atr_min"] <= max_dist_atr:
        return False
    if r["poi_fvg_fill"] == 1 and 0 < r["m15_fvg_dist_atr_min"] <= max_dist_atr:
        return False
    return True


def section_2_gates(rich, a1):
    """Apply each gate to rich + measure (skip-rate, lost-CAND, lost-R).

    A1 (XAUUSD+USDJPY only, ~26% population coverage) gives DIRECT counterfactual
    on 4 lost CANDs at most. The DIRECT count is the most reliable evidence —
    it's what really happened to candles A1 evaluated.

    For extrapolation, we project R-loss for newly-skipped candles as if they
    were evaluated by the AI under the SAME funnel rates as A1's fleet average.
    But the candles being skipped are by construction LOWER QUALITY than the
    average A1 row (they have no aligned POI / weak distance / bad touch). So
    the fleet-average extrapolation is a CONSERVATIVE upper bound on R-loss.
    The TRUE expected R-loss is bounded by the stratum-specific Exp_R from A1.
    """
    a1_by_key = {(r["symbol"], r["timestamp_utc"]): r for r in a1}

    # Per-symbol AI CAND rate + Exp_R from A1 (XAUUSD / USDJPY direct);
    # for instruments with no A1 data, use unified Q1 average as a fallback.
    a1_per_inst = defaultdict(lambda: {"ai_eval": 0, "cand": 0, "filled": 0,
                                       "rs": []})
    for r in a1:
        sym = r["symbol"]
        a1_per_inst[sym]["ai_eval"] += 1
        if r.get("out_decision") == "CANDIDATE":
            a1_per_inst[sym]["cand"] += 1
            if r.get("out_outcome") in ("WIN", "LOSS", "BE"):
                a1_per_inst[sym]["filled"] += 1
                a1_per_inst[sym]["rs"].append(float(r.get("out_r_multiple") or 0))

    # Per-symbol fleet-average funnel parameters — used for the conservative
    # upper-bound extrapolation. CONDITIONAL parameters per stratum (e.g.,
    # `dist > 4 ATR` cells) are computed inline for each gate below.
    funnel_params = {}
    for sym, d in a1_per_inst.items():
        if d["ai_eval"]:
            funnel_params[sym] = {
                "cand_rate": d["cand"] / d["ai_eval"],
                "filled_rate_of_cand": d["filled"] / max(d["cand"], 1),
                "exp_r_filled": (sum(d["rs"]) / max(len(d["rs"]), 1)) if d["rs"] else 0.0,
            }
    if a1_per_inst:
        total_eval = sum(d["ai_eval"] for d in a1_per_inst.values())
        total_cand = sum(d["cand"] for d in a1_per_inst.values())
        total_filled = sum(d["filled"] for d in a1_per_inst.values())
        total_r = sum(sum(d["rs"]) for d in a1_per_inst.values())
        fleet_default = {
            "cand_rate": total_cand / total_eval if total_eval else 0,
            "filled_rate_of_cand": total_filled / total_cand if total_cand else 0,
            "exp_r_filled": (total_r / total_filled) if total_filled else 0.0,
        }
    else:
        fleet_default = {"cand_rate": 0.08, "filled_rate_of_cand": 0.81, "exp_r_filled": 0.27}

    # Conditional A1 funnel for stratum-aware extrapolation.
    # For each gate, compute CAND-rate + Exp_R among A1 rows that satisfy the
    # gate's skip predicate (i.e., among rows the gate would have caught).
    # Only meaningful for the XAUUSD+USDJPY subsample.
    n_total = len(rich)
    n_multi_skip = sum(1 for r in rich if r["skip_multi"] == 1)

    # We need to apply gate fn to A1 rows. But A1 lacks the rich columns
    # (h1_min_dist_atr_aligned, etc). We can join via candle_time → rich row.
    rich_by_key = {(r["symbol"], r["candle_time"]): r for r in rich}

    by_gate = {}
    for gate_name, fn in GATES.items():
        skipped = 0
        skipped_a1_eval = 0
        skipped_a1_cand = 0
        skipped_a1_filled_wins = 0
        skipped_a1_filled_losses = 0
        skipped_a1_filled_be = 0
        skipped_a1_filled_rs = []
        skipped_a1_unfilled_cand = 0
        per_inst = defaultdict(lambda: {
            "n": 0, "skipped": 0, "skipped_above_multi": 0,
            "skipped_a1_cand": 0, "skipped_a1_filled": 0,
            "skipped_a1_wins": 0, "skipped_a1_losses": 0,
            "skipped_a1_rs": [],
        })
        for r in rich:
            sym = r["symbol"]
            per_inst[sym]["n"] += 1
            do_skip = fn(r)
            if do_skip:
                skipped += 1
                per_inst[sym]["skipped"] += 1
                if r["skip_multi"] == 0:
                    per_inst[sym]["skipped_above_multi"] += 1
                key = (sym, r["candle_time"])
                a1_row = a1_by_key.get(key)
                if a1_row is not None:
                    skipped_a1_eval += 1
                    if a1_row.get("out_decision") == "CANDIDATE":
                        skipped_a1_cand += 1
                        per_inst[sym]["skipped_a1_cand"] += 1
                        out = a1_row.get("out_outcome")
                        if out in ("WIN", "LOSS", "BE"):
                            per_inst[sym]["skipped_a1_filled"] += 1
                            r_mul = float(a1_row.get("out_r_multiple") or 0)
                            skipped_a1_filled_rs.append(r_mul)
                            per_inst[sym]["skipped_a1_rs"].append(r_mul)
                            if out == "WIN":
                                skipped_a1_filled_wins += 1
                                per_inst[sym]["skipped_a1_wins"] += 1
                            elif out == "LOSS":
                                skipped_a1_filled_losses += 1
                                per_inst[sym]["skipped_a1_losses"] += 1
                            elif out == "BE":
                                skipped_a1_filled_be += 1
                        elif out == "UNFILLED":
                            skipped_a1_unfilled_cand += 1

        # === Extrapolation: full-population projected R loss ===
        # CONSERVATIVE (fleet-average) extrapolation: assume newly-skipped rows
        # would have AI-funnel = same as A1's fleet average.
        proj_lost_r_per_q1 = 0.0
        proj_lost_cand_per_q1 = 0.0
        proj_lost_filled_per_q1 = 0.0
        for sym, pd_ in per_inst.items():
            sk = pd_["skipped_above_multi"]
            params = funnel_params.get(sym, fleet_default)
            cand_n = sk * params["cand_rate"]
            filled_n = cand_n * params["filled_rate_of_cand"]
            r_loss = filled_n * params["exp_r_filled"]
            proj_lost_r_per_q1 += r_loss
            proj_lost_cand_per_q1 += cand_n
            proj_lost_filled_per_q1 += filled_n

        # STRATUM-CONDITIONAL extrapolation: for each gate, look at A1 rows
        # that the proposed TIGHTER gate would NEWLY skip (i.e., not already
        # caught by the multi-framework baseline). Use THAT stratum's CAND rate
        # + Exp_R as the funnel projection multiplier.
        a1_in_skip_stratum = 0
        a1_skip_cand = 0
        a1_skip_filled = 0
        a1_skip_rs = []
        a1_skip_winrate = 0
        for a1_row in a1:
            key = (a1_row["symbol"], a1_row["timestamp_utc"])
            rich_row = rich_by_key.get(key)
            if rich_row is None:
                continue
            if rich_row["skip_multi"] == 1:
                # Already skipped by multi — not part of the "above multi" stratum.
                continue
            if not fn(rich_row):
                continue
            # This A1 row would be NEWLY skipped under the proposed gate.
            a1_in_skip_stratum += 1
            if a1_row.get("out_decision") == "CANDIDATE":
                a1_skip_cand += 1
                out = a1_row.get("out_outcome")
                if out in ("WIN", "LOSS", "BE"):
                    a1_skip_filled += 1
                    a1_skip_rs.append(float(a1_row.get("out_r_multiple") or 0))
                    if out == "WIN":
                        a1_skip_winrate += 1

        # Stratum-conditional rates:
        if a1_in_skip_stratum > 0:
            stratum_cand_rate = a1_skip_cand / a1_in_skip_stratum
            stratum_filled_rate = a1_skip_filled / max(a1_skip_cand, 1)
            stratum_exp_r = (sum(a1_skip_rs) / len(a1_skip_rs)) if a1_skip_rs else 0.0
        else:
            stratum_cand_rate = stratum_filled_rate = stratum_exp_r = 0.0
        # Wilson 95% upper bound on stratum CAND rate (for honest sensitivity)
        if a1_in_skip_stratum > 0:
            _, stratum_cand_rate_ub = wilson_ci(a1_skip_cand, a1_in_skip_stratum)
        else:
            stratum_cand_rate_ub = 1.0  # max uncertainty
        # Project to full-population skipped count (excluding multi-skip portion)
        skipped_above_multi_count = sum(p["skipped_above_multi"] for p in per_inst.values())
        proj_strat_cand = skipped_above_multi_count * stratum_cand_rate
        proj_strat_filled = proj_strat_cand * stratum_filled_rate
        proj_strat_lost_r_q1 = proj_strat_filled * stratum_exp_r
        # 95% upper-bound R-loss: assume CAND rate at stratum's Wilson UB AND fleet
        # exp_r_filled (more pessimistic). Use this for the safety check.
        proj_strat_cand_ub = skipped_above_multi_count * stratum_cand_rate_ub
        # Pessimistic Exp_R: max of stratum and fleet
        pessimistic_exp_r = max(stratum_exp_r, fleet_default["exp_r_filled"]) if fleet_default["exp_r_filled"] > 0 else stratum_exp_r
        # Use fleet filled-rate as a defensible default
        fleet_filled_rate = fleet_default["filled_rate_of_cand"] if fleet_default["filled_rate_of_cand"] > 0 else 0.81
        proj_strat_filled_ub = proj_strat_cand_ub * fleet_filled_rate
        proj_strat_lost_r_q1_ub = proj_strat_filled_ub * pessimistic_exp_r

        skipped_above_multi = skipped - n_multi_skip
        ai_calls_multi = n_total - n_multi_skip
        ai_calls_tight = n_total - skipped
        delta_calls = ai_calls_multi - ai_calls_tight
        per_month_savings = (delta_calls / Q1_DAYS) * TRADING_DAYS_PER_MONTH * COST_PER_CALL

        # Direct (sample-based) projection vs extrapolated.
        # IMPORTANT: A1 covers only XAUUSD+USDJPY at ~26% of full population,
        # so the direct count is a LOWER bound; extrapolation is the FAIR estimate.
        lost_r_total_a1 = sum(skipped_a1_filled_rs)
        lost_r_per_month_proj_a1 = (lost_r_total_a1 / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        proj_lost_r_per_month_extrap = (proj_lost_r_per_q1 / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        proj_lost_cand_per_month_extrap = (proj_lost_cand_per_q1 / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        proj_lost_filled_per_month_extrap = (proj_lost_filled_per_q1 / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        # Stratum-conditional projection — best central estimate
        proj_strat_lost_r_per_month = (proj_strat_lost_r_q1 / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        proj_strat_lost_cand_per_month = ((proj_strat_cand) / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        proj_strat_lost_filled_per_month = ((proj_strat_filled) / Q1_DAYS) * TRADING_DAYS_PER_MONTH
        # Stratum-conditional 95% upper bound — for honest sensitivity check
        proj_strat_lost_r_per_month_ub = (proj_strat_lost_r_q1_ub / Q1_DAYS) * TRADING_DAYS_PER_MONTH

        by_gate[gate_name] = {
            "skipped_total": skipped,
            "skipped_above_multi": skipped_above_multi,
            "ai_calls_under_gate": ai_calls_tight,
            "delta_ai_calls_q1": delta_calls,
            "savings_per_month_usd": per_month_savings,
            # Direct A1 sample (lower bound; only XAUUSD+USDJPY coverage)
            "lost_a1_eval": skipped_a1_eval,
            "lost_a1_cand": skipped_a1_cand,
            "lost_a1_unfilled": skipped_a1_unfilled_cand,
            "lost_a1_filled": len(skipped_a1_filled_rs),
            "lost_a1_wins": skipped_a1_filled_wins,
            "lost_a1_losses": skipped_a1_filled_losses,
            "lost_a1_be": skipped_a1_filled_be,
            "lost_a1_total_r": lost_r_total_a1,
            "lost_r_per_month_proj_a1": lost_r_per_month_proj_a1,
            # Extrapolated projection — fleet-average funnel (CONSERVATIVE)
            "proj_lost_r_per_month_fleet": proj_lost_r_per_month_extrap,
            "proj_lost_cand_per_month_fleet": proj_lost_cand_per_month_extrap,
            "proj_lost_filled_per_month_fleet": proj_lost_filled_per_month_extrap,
            # Extrapolated projection — stratum-conditional (CENTRAL ESTIMATE)
            "proj_lost_r_per_month_stratum": proj_strat_lost_r_per_month,
            "proj_lost_r_per_month_stratum_ub": proj_strat_lost_r_per_month_ub,
            "proj_lost_cand_per_month_stratum": proj_strat_lost_cand_per_month,
            "proj_lost_filled_per_month_stratum": proj_strat_lost_filled_per_month,
            "stratum_cand_rate": stratum_cand_rate,
            "stratum_cand_rate_wilson_ub": stratum_cand_rate_ub,
            "stratum_exp_r": stratum_exp_r,
            "stratum_n_a1_rows": a1_in_skip_stratum,
            "per_instrument": {sym: {k: v if k != "skipped_a1_rs" else len(v) for k, v in d.items()}
                               for sym, d in per_inst.items()},
        }
    return by_gate


# ---------------------------------------------------------------------------
# Section 3: Pareto frontier
# ---------------------------------------------------------------------------

def section_3_pareto(gates_data):
    """Sort gates by savings; show savings vs lost R.

    Primary R-loss column: stratum-conditional (uses A1's CAND-rate AT the stratum
    being skipped). This is the most defensible estimate. The fleet-average column
    is a conservative upper bound. The A1-direct count is the literal observed loss
    on A1's 1,030/3,906 (XAUUSD+USDJPY) sample.
    """
    rows = []
    for name, d in gates_data.items():
        rows.append({
            "gate": name,
            "savings_per_month_usd": d["savings_per_month_usd"],
            "lost_r_per_month_stratum": d["proj_lost_r_per_month_stratum"],
            "lost_r_per_month_stratum_ub": d["proj_lost_r_per_month_stratum_ub"],
            "lost_cand_per_month_stratum": d["proj_lost_cand_per_month_stratum"],
            "lost_r_per_month_fleet_upper_bound": d["proj_lost_r_per_month_fleet"],
            "lost_r_per_month_a1_direct": d["lost_r_per_month_proj_a1"],
            "lost_a1_filled_cand": d["lost_a1_filled"],
            "lost_a1_wins": d["lost_a1_wins"],
            "delta_ai_calls_q1": d["delta_ai_calls_q1"],
            "stratum_n_a1_rows": d["stratum_n_a1_rows"],
            "stratum_cand_rate": d["stratum_cand_rate"],
            "stratum_cand_rate_wilson_ub": d["stratum_cand_rate_wilson_ub"],
            "stratum_exp_r": d["stratum_exp_r"],
        })
    rows.sort(key=lambda r: -r["savings_per_month_usd"])
    return rows


# ---------------------------------------------------------------------------
# Section 4: per-instrument differential gates
# ---------------------------------------------------------------------------

def section_4_per_instrument(rich, a1):
    """Apply gates per-instrument; surface where each gate is most/least costly."""
    a1_by_key = {(r["symbol"], r["timestamp_utc"]): r for r in a1}
    out = {}
    for sym in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        sym_rows = [r for r in rich if r["symbol"] == sym]
        n = len(sym_rows)
        sym_results = {}
        for gate_name, fn in GATES.items():
            skipped = sum(1 for r in sym_rows if fn(r))
            n_multi_skip = sum(1 for r in sym_rows if r["skip_multi"] == 1)
            delta = skipped - n_multi_skip
            cost_savings = (delta / Q1_DAYS) * TRADING_DAYS_PER_MONTH * COST_PER_CALL

            # Lost A1 CAND R (only meaningful for XAUUSD + USDJPY)
            lost_rs = []
            lost_cand = 0
            for r in sym_rows:
                if not fn(r):
                    continue
                key = (sym, r["candle_time"])
                a1_row = a1_by_key.get(key)
                if a1_row and a1_row.get("out_decision") == "CANDIDATE":
                    lost_cand += 1
                    if a1_row.get("out_outcome") in ("WIN", "LOSS", "BE"):
                        lost_rs.append(float(a1_row.get("out_r_multiple") or 0))
            sym_results[gate_name] = {
                "skipped": skipped,
                "skip_rate": skipped / n if n else 0,
                "delta_skip_above_multi": delta,
                "savings_per_month_usd": cost_savings,
                "lost_a1_cand": lost_cand,
                "lost_a1_filled": len(lost_rs),
                "lost_a1_total_r": sum(lost_rs),
                "lost_r_per_month_proj": (sum(lost_rs) / Q1_DAYS) * TRADING_DAYS_PER_MONTH,
            }
        out[sym] = {"n_q1": n, "by_gate": sym_results}
    return out


# ---------------------------------------------------------------------------
# Section 5: derive recommendation
# ---------------------------------------------------------------------------

def section_5_recommendation_v2(pareto_rows, a2_data):
    """V2 recommendation that ALSO requires the A2 (v2-active) cross-check
    R-loss to be ≤0.5R/mo. If A2 disqualifies a gate, the gate is rejected
    even if A1-stratum extrapolation passed.
    """
    qualifying = []
    for r in pareto_rows:
        a2_loss = a2_data.get(r["gate"], {}).get("a2_lost_r_per_month_proj", 0)
        if (r["lost_r_per_month_stratum"] <= 0.5
                and r["lost_r_per_month_stratum_ub"] <= 0.5
                and a2_loss <= 0.5
                and r["savings_per_month_usd"] > 0):
            r2 = dict(r)
            r2["a2_lost_r_per_month"] = a2_loss
            r2["a2_filled_skipped"] = a2_data[r["gate"]]["a2_filled_skipped"]
            r2["a2_wins_skipped"] = a2_data[r["gate"]]["a2_wins_skipped"]
            qualifying.append(r2)
    qualifying.sort(key=lambda x: -x["savings_per_month_usd"])
    return {
        "qualifying_gates": qualifying[:8],
        "best": qualifying[0] if qualifying else None,
        "ceiling_r_per_month": 0.5,
        "all_gates_with_a2": [{
            "gate": r["gate"],
            "savings_per_month_usd": r["savings_per_month_usd"],
            "lost_r_per_month_stratum": r["lost_r_per_month_stratum"],
            "lost_r_per_month_stratum_ub": r["lost_r_per_month_stratum_ub"],
            "lost_r_per_month_a1_direct": r["lost_r_per_month_a1_direct"],
            "a2_filled_skipped": a2_data.get(r["gate"], {}).get("a2_filled_skipped", 0),
            "a2_wins_skipped": a2_data.get(r["gate"], {}).get("a2_wins_skipped", 0),
            "a2_total_r_skipped": a2_data.get(r["gate"], {}).get("a2_total_r_skipped", 0),
            "a2_lost_r_per_month": a2_data.get(r["gate"], {}).get("a2_lost_r_per_month_proj", 0),
        } for r in pareto_rows],
    }


def section_5_recommendation(pareto_rows):
    """CEO ceiling: realized-R loss <= 0.5R/mo. Sign convention: lost_r_per_month_*
    is the EXPECTED REALIZED R FOREGONE, so positive=expensive, negative=we'd
    actually GAIN R. Use the stratum-conditional projection as the primary metric
    (it's the most defensible) but require it AND the conservative fleet-upper-bound
    to both be ≤0.5R/mo. This protects against funnel-rate optimism.
    """
    # Apply BOTH the stratum point estimate AND the stratum Wilson 95% UB
    qualifying = [r for r in pareto_rows
                  if r["lost_r_per_month_stratum"] <= 0.5
                  and r["lost_r_per_month_stratum_ub"] <= 0.5
                  and r["savings_per_month_usd"] > 0]
    qualifying.sort(key=lambda r: (-r["savings_per_month_usd"]))
    return {
        "qualifying_gates": qualifying[:8],
        "best": qualifying[0] if qualifying else None,
        "ceiling_r_per_month": 0.5,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...")
    rich = load_rich()
    a1 = load_a1()
    unified = load_unified()
    a2_cand = load_a2_cand_rows()
    print(f"  rich: {len(rich)} rows; a1: {len(a1)} rows; unified: {len(unified)}; a2_cand: {len(a2_cand)}")

    print("\nSection 1: per-instrument funnel...")
    s1 = section_1_funnel(rich, a1, unified)

    print("\nSection 2: gate evaluation...")
    s2 = section_2_gates(rich, a1)

    print("\nSection 2b: A2 (v2-active) cross-validation...")
    s2b = section_2b_a2_crosscheck(rich, a2_cand)

    print("\nSection 3: Pareto frontier...")
    s3 = section_3_pareto(s2)

    print("\nSection 4: per-instrument differential...")
    s4 = section_4_per_instrument(rich, a1)

    print("\nSection 5: recommendation...")
    s5 = section_5_recommendation_v2(s3, s2b)

    out = {
        "section_1_funnel": s1,
        "section_2_gates": s2,
        "section_2b_a2_crosscheck": s2b,
        "section_3_pareto": s3,
        "section_4_per_instrument": s4,
        "section_5_recommendation": s5,
        "meta": {
            "rich_csv": str(RICH_CSV),
            "a1_jsonl": str(A1_JSONL),
            "unified_csv": str(UNIFIED_TRADES),
            "cost_per_call_usd": COST_PER_CALL,
            "q1_calendar_days": Q1_DAYS,
            "trading_days_per_month": TRADING_DAYS_PER_MONTH,
            "n_rich_rows": len(rich),
            "n_a1_rows": len(a1),
            "n_unified": len(unified),
            "n_a2_cand": len(a2_cand),
        },
    }

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWrote {OUT}")

    # Console summary
    print("\n=== Section 1: funnel ===")
    print(f"{'sym':<12}{'kz':>6}{'skip%':>8}{'AI_calls/mo':>12}{'$/mo':>10}{'CAND_rate':>11}{'WR':>8}{'Exp_R':>9}")
    for row in s1:
        wr = fmt_pct(row["a1_wr"]) if row["a1_wr"] is not None else "—"
        cr = fmt_pct(row["a1_cand_rate"]) if row["a1_cand_rate"] is not None else "—"
        exp = fmt_r(row["a1_exp_r"]) if row["a1_exp_r"] is not None else "—"
        print(f"{row['symbol']:<12}{row['kz_candles_q1']:>6}"
              f"{100*row['skip_rate_multi']:>7.2f}%"
              f"{row['ai_calls_per_month']:>12.1f}"
              f"{row['ai_dollars_per_month']:>9.2f}$"
              f"{cr:>11}{wr:>8}{exp:>9}")

    print("\n=== Section 3: Pareto frontier ===")
    print(f"{'gate':<30}{'$/mo':>7}{'R_str':>9}{'R_str_UB':>10}{'R_a1':>8}{'A2_C':>6}{'A2_W':>6}{'A2_R':>9}")
    for row in s3:
        a2 = s2b.get(row['gate'], {})
        print(f"{row['gate']:<30}{row['savings_per_month_usd']:>6.2f}$"
              f"{row['lost_r_per_month_stratum']:>+8.3f}R"
              f"{row['lost_r_per_month_stratum_ub']:>+9.3f}R"
              f"{row['lost_r_per_month_a1_direct']:>+7.3f}R"
              f"{a2.get('a2_cand_skipped', 0):>6}"
              f"{a2.get('a2_wins_skipped', 0):>6}"
              f"{a2.get('a2_total_r_skipped', 0):>+8.2f}R")

    print("\n=== Section 5: recommendation ===")
    if s5["best"]:
        b = s5["best"]
        print(f"BEST: {b['gate']} -> savings ${b['savings_per_month_usd']:.2f}/mo, "
              f"R-loss(stratum) {b['lost_r_per_month_stratum']:+.3f}/mo, "
              f"R-loss(fleet UB) {b['lost_r_per_month_fleet_upper_bound']:+.3f}/mo, "
              f"R-loss(A1-direct) {b['lost_r_per_month_a1_direct']:+.3f}/mo")
        print(f"  qualifying gates: {len(s5['qualifying_gates'])}")
        for q in s5['qualifying_gates']:
            print(f"    - {q['gate']:<30} ${q['savings_per_month_usd']:>5.2f}/mo "
                  f"strat={q['lost_r_per_month_stratum']:+.3f}R "
                  f"fleet={q['lost_r_per_month_fleet_upper_bound']:+.3f}R")
    else:
        print("No gate qualifies (savings>0 AND stratum R-loss<=0.5R/mo)")


if __name__ == "__main__":
    main()
