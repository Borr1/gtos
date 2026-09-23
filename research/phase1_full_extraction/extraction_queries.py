"""Phase 1 comprehensive extraction (E1-E12).

Reads A1 logger + A1 all_results + F3 all_results, produces a joined dataset
and answers all 12 extractions.

Usage: python extraction_queries.py

Writes:
  - merged_data.jsonl (joined logger x outcome rows from A1)
  - extraction_output.json (machine-readable summary)
  - EXTRACTION.md (human-readable synthesis, written from main at end)
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

random.seed(20260424)  # reproducibility

REPO_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
A1_BASE = REPO_ROOT / ".claude" / "worktrees" / "agent-afdadba7818cfadd8" / "research" / "a1_adr005_backtest" / "slices"
F3_BASE = REPO_ROOT / "research" / "f3_backtest_2026-04-24"
OUT_DIR = REPO_ROOT / "research" / "phase1_full_extraction"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SLICES = [
    "xauusd_s1", "xauusd_s2", "xauusd_s3", "xauusd_s4",
    "xauusd_s5", "xauusd_s6", "xauusd_s7", "xauusd_s8",
    "usdjpy_s1", "usdjpy_s2", "usdjpy_s3", "usdjpy_s4",
]


# --------------------------------------------------------------------------- #
# Stats helpers
# --------------------------------------------------------------------------- #

def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = wins / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def bootstrap_mean_ci(values: list[float], iters: int = 5000, z: float = 1.96) -> tuple[float, float, float]:
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[random.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((1 - 0.95) / 2 * iters)]
    hi = means[int((1 + 0.95) / 2 * iters)]
    return (sum(values) / n, lo, hi)


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #

def load_a1_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load all A1 logger rows + outcome rows, join by (symbol, timestamp_utc)."""
    joined: list[dict[str, Any]] = []
    outcomes_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    logger_rows_all: list[dict[str, Any]] = []
    slice_meta: dict[str, dict[str, Any]] = {}

    for slc in SLICES:
        sd = A1_BASE / slc
        ar = sd / "all_results.json"
        cl = sd / "candidate_features_log.jsonl"
        with open(ar) as f:
            raw = json.load(f)
        slice_meta[slc] = {
            "start": raw.get("start"),
            "end": raw.get("end"),
            "total_rows": len(raw.get("results", [])),
        }
        for r in raw.get("results", []):
            # symbol inside the row
            sym = r.get("symbol", "?")
            ts = r.get("candle_time")
            outcomes_by_key[(sym, ts)] = {**r, "slice": slc}

        if cl.exists():
            with open(cl) as f:
                for line in f:
                    lr = json.loads(line)
                    lr["slice"] = slc
                    logger_rows_all.append(lr)

    # now join: for each logger row, find outcome
    for lr in logger_rows_all:
        key = (lr.get("symbol"), lr.get("timestamp_utc"))
        oc = outcomes_by_key.get(key)
        if oc is None:
            # try to find by candle_time alone (slice-local)
            oc = None
        joined.append({"logger": lr, "outcome": oc})
    return joined, {"slice_meta": slice_meta, "logger_count": len(logger_rows_all), "outcome_count": len(outcomes_by_key)}


def write_merged(joined: list[dict[str, Any]], path: Path) -> None:
    with open(path, "w") as f:
        for j in joined:
            lg = j["logger"]
            oc = j.get("outcome") or {}
            row = {
                "symbol": lg.get("symbol"),
                "slice": lg.get("slice"),
                "timestamp_utc": lg.get("timestamp_utc"),
                "kill_zone": lg.get("kill_zone"),
                "hour_utc": lg.get("hour_utc"),
                "day_of_week": lg.get("day_of_week"),
                "logger_decision": lg.get("decision"),
                "logger_framework": lg.get("framework"),
                "logger_setup_grade": lg.get("setup_grade"),
                "ai_decision": lg.get("ai_decision"),
                "ai_direction_evaluated": lg.get("ai_direction_evaluated"),
                "ai_no_trade_reason": lg.get("ai_no_trade_reason"),
                "c_gate_result": lg.get("c_gate_result"),
                "h1_opp_ob_touch": lg.get("h1_opp_ob_touch"),
                "h1_opp_ob_touch_long": lg.get("h1_opp_ob_touch_long"),
                "h1_opp_ob_touch_short": lg.get("h1_opp_ob_touch_short"),
                "h1_fvg_unfilled_count": lg.get("h1_fvg_unfilled_count"),
                "m15_fvg_unfilled_count": lg.get("m15_fvg_unfilled_count"),
                "mso_h1_structure_direction": lg.get("mso_h1_structure_direction"),
                "mso_h1_unmitigated_ob_count": lg.get("mso_h1_unmitigated_ob_count"),
                "mso_h1_ob_touch_counts": lg.get("mso_h1_ob_touch_counts"),
                "mso_h1_nearest_ob_distance_atr": lg.get("mso_h1_nearest_ob_distance_atr"),
                "mso_detected_sweeps_count": lg.get("mso_detected_sweeps_count"),
                "mso_m15_clv_current": lg.get("mso_m15_clv_current"),
                "mso_m15_clv_avg_5": lg.get("mso_m15_clv_avg_5"),
                "mso_m15_bvc_buy_fraction": lg.get("mso_m15_bvc_buy_fraction"),
                "pre_ai_gate_skipped": lg.get("pre_ai_gate_skipped"),
                "pre_ai_gate_reason": lg.get("pre_ai_gate_reason"),
                "detector_version_at_eval": lg.get("detector_version_at_eval"),
                "out_decision": oc.get("decision"),
                "out_direction": oc.get("direction"),
                "out_outcome": oc.get("outcome"),
                "out_r_multiple": oc.get("r_multiple"),
                "out_l2_passed": oc.get("l2_passed"),
                "out_no_trade_reason": oc.get("no_trade_reason"),
                "out_setup_grade": oc.get("setup_grade"),
                "out_prescreen": oc.get("prescreen"),
                "out_bias": oc.get("bias"),
                "out_p2a_bias": oc.get("p2a_bias"),
                "out_p2a_decision": oc.get("p2a_decision"),
            }
            f.write(json.dumps(row) + "\n")


# --------------------------------------------------------------------------- #
# Extractions
# --------------------------------------------------------------------------- #

def _outcome_realized_r(row: dict[str, Any]) -> float | None:
    """Return realized R if the CAND was taken and filled; None if unfilled/blocked."""
    oc = row.get("outcome") or {}
    if oc.get("decision") != "CANDIDATE":
        return None
    if oc.get("outcome") in {"WIN", "LOSS", "BE"}:
        return oc.get("r_multiple")
    if oc.get("outcome") in {"UNFILLED"}:
        return 0.0  # counts as 0R in expectancy (did not lose, did not win)
    return None


def _is_filled_cand(row: dict[str, Any]) -> bool:
    oc = row.get("outcome") or {}
    return oc.get("decision") == "CANDIDATE" and oc.get("outcome") in {"WIN", "LOSS", "BE"}


def e1_touch_strata(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """E1: WR + expectancy per h1_opp_ob_touch stratum among CANDs taken.

    Reports stratified across direction-aware touch (Track A semantic fix):
    - LONG CAND uses h1_opp_ob_touch_long
    - SHORT CAND uses h1_opp_ob_touch_short
    Also computes legacy h1_opp_ob_touch (backwards-compat aggregate) and missing.
    """
    # Which field to use per direction
    def direction_touch(lg: dict[str, Any], direction: str | None) -> int | None:
        if direction == "LONG":
            t = lg.get("h1_opp_ob_touch_long")
        elif direction == "SHORT":
            t = lg.get("h1_opp_ob_touch_short")
        else:
            t = lg.get("h1_opp_ob_touch")
        return t

    buckets = {"1": [], "2": [], ">=3": [], "missing": []}
    filled_buckets = {"1": [], "2": [], ">=3": [], "missing": []}
    taken_only = []  # only CAND that got filled

    for j in joined:
        lg = j["logger"]
        oc = j.get("outcome") or {}
        if oc.get("decision") != "CANDIDATE":
            continue
        direction = oc.get("direction")
        touch = direction_touch(lg, direction)
        rmult = oc.get("r_multiple")
        outcome_str = oc.get("outcome")  # WIN/LOSS/BE/UNFILLED
        bucket = (
            "missing" if touch is None else
            "1" if touch <= 1 else
            "2" if touch == 2 else
            ">=3"
        )
        if outcome_str in {"WIN", "LOSS", "BE"}:
            filled_buckets[bucket].append(rmult)
        # unfilled still counted in "taken" universe for expectancy if desired, but bootstrapping only over filled
        if outcome_str in {"WIN", "LOSS", "BE", "UNFILLED"}:
            taken_only.append((bucket, outcome_str, rmult, direction))

    out = {"direction_aware_touch": {}, "all_taken_universe": {}}
    for b, vals in filled_buckets.items():
        n = len(vals)
        wins = sum(1 for v in vals if v is not None and v > 0)
        losses = sum(1 for v in vals if v is not None and v < 0)
        be = sum(1 for v in vals if v is not None and v == 0)
        wr_lo, wr_hi = wilson_ci(wins, n)
        exp_vals = [v for v in vals if v is not None]
        mean, elo, ehi = bootstrap_mean_ci(exp_vals, iters=5000) if exp_vals else (float("nan"), float("nan"), float("nan"))
        out["direction_aware_touch"][b] = {
            "n": n, "wins": wins, "losses": losses, "be": be,
            "wr": wins / n if n else float("nan"),
            "wr_ci95": [wr_lo, wr_hi],
            "expectancy_r": mean,
            "expectancy_ci95": [elo, ehi],
        }
    # All-taken universe (incl. UNFILLED as 0R)
    for bucket_name in ["1", "2", ">=3", "missing"]:
        rows = [r for r in taken_only if r[0] == bucket_name]
        vals = [r[2] if r[2] is not None else 0.0 for r in rows]  # UNFILLED -> 0
        n_total = len(rows)
        n_filled = sum(1 for r in rows if r[1] in {"WIN", "LOSS", "BE"})
        n_unfilled = sum(1 for r in rows if r[1] == "UNFILLED")
        wins = sum(1 for r in rows if r[1] == "WIN")
        wr_lo, wr_hi = wilson_ci(wins, n_filled) if n_filled else (float("nan"), float("nan"))
        mean, elo, ehi = bootstrap_mean_ci(vals, iters=5000) if vals else (float("nan"), float("nan"), float("nan"))
        out["all_taken_universe"][bucket_name] = {
            "n_total": n_total, "n_filled": n_filled, "n_unfilled": n_unfilled,
            "wins": wins,
            "wr_of_filled": wins / n_filled if n_filled else float("nan"),
            "wr_ci95_of_filled": [wr_lo, wr_hi],
            "expectancy_r_with_unfilled_as_0": mean,
            "expectancy_ci95": [elo, ehi],
        }
    return out


def e2_fvg_strata(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """E2: WR + expectancy per FVG count bucket."""
    buckets = defaultdict(list)  # bucket -> [r_values]
    for j in joined:
        lg = j["logger"]
        oc = j.get("outcome") or {}
        if oc.get("decision") != "CANDIDATE":
            continue
        if oc.get("outcome") not in {"WIN", "LOSS", "BE"}:
            continue
        h1f = lg.get("h1_fvg_unfilled_count") or 0
        m15f = lg.get("m15_fvg_unfilled_count") or 0
        total = h1f + m15f
        bucket = (
            "<5" if total < 5 else
            "5-10" if total < 11 else
            "11-20" if total < 21 else
            "21-30" if total < 31 else
            ">=31"
        )
        buckets[bucket].append(oc.get("r_multiple"))
    out = {}
    for b, vals in buckets.items():
        n = len(vals)
        wins = sum(1 for v in vals if v is not None and v > 0)
        wr_lo, wr_hi = wilson_ci(wins, n)
        exp = [v for v in vals if v is not None]
        mean, elo, ehi = bootstrap_mean_ci(exp, iters=5000) if exp else (float("nan"), float("nan"), float("nan"))
        out[b] = {
            "n": n, "wins": wins,
            "wr": wins / n if n else float("nan"),
            "wr_ci95": [wr_lo, wr_hi],
            "expectancy_r": mean,
            "expectancy_ci95": [elo, ehi],
        }
    return out


def e3_direction_breakdown(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """E3: WR + expectancy per direction (LONG/SHORT/UNCLEAR)."""
    direction_filled = defaultdict(list)
    direction_taken = defaultdict(list)
    direction_eval_total = Counter()  # all AI evals
    direction_cand_total = Counter()
    direction_cand_unfilled = Counter()
    for j in joined:
        lg = j["logger"]
        oc = j.get("outcome") or {}
        # logger eval direction
        eval_dir = lg.get("ai_direction_evaluated")
        if eval_dir:
            direction_eval_total[eval_dir] += 1
        if oc.get("decision") != "CANDIDATE":
            continue
        direction = oc.get("direction") or eval_dir
        direction_cand_total[direction] += 1
        if oc.get("outcome") in {"WIN", "LOSS", "BE"}:
            direction_filled[direction].append(oc.get("r_multiple"))
            direction_taken[direction].append(oc.get("r_multiple"))
        elif oc.get("outcome") == "UNFILLED":
            direction_cand_unfilled[direction] += 1
            direction_taken[direction].append(0.0)
    out = {}
    for d, vals in direction_filled.items():
        n = len(vals)
        wins = sum(1 for v in vals if v is not None and v > 0)
        wr_lo, wr_hi = wilson_ci(wins, n)
        mean, elo, ehi = bootstrap_mean_ci([v for v in vals if v is not None], iters=5000) if vals else (float("nan"),) * 3
        t_mean, t_elo, t_ehi = bootstrap_mean_ci(direction_taken[d], iters=5000) if direction_taken[d] else (float("nan"),) * 3
        out[d] = {
            "n_filled": n, "wins": wins,
            "wr_filled": wins / n if n else float("nan"),
            "wr_ci95": [wr_lo, wr_hi],
            "expectancy_filled_r": mean,
            "expectancy_filled_ci95": [elo, ehi],
            "expectancy_taken_r_unfilled_as_0": t_mean,
            "expectancy_taken_ci95": [t_elo, t_ehi],
            "n_cand_total": direction_cand_total[d],
            "n_cand_unfilled": direction_cand_unfilled[d],
            "n_ai_eval_total": direction_eval_total.get(d, 0),
        }
    return out


def e4_short_share_diff(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """E4: SHORT share A1 vs F3 per slice."""
    # F3: count CAND direction from raw_response? Use trade_parameters.direction.
    # Simpler: in F3 all_results, CAND has 'direction' field.
    def count_cands(all_results_path: Path) -> dict[str, int]:
        with open(all_results_path) as f:
            d = json.load(f)
        long_c, short_c, cand_total = 0, 0, 0
        long_l2, short_l2 = 0, 0
        for r in d.get("results", []):
            dec = r.get("decision")
            if dec == "CANDIDATE":
                cand_total += 1
                dr = r.get("direction", "?")
                if dr == "LONG": long_c += 1
                elif dr == "SHORT": short_c += 1
            elif dec == "REJECTED_L2":
                dr = r.get("direction", r.get("trade_parameters", {}).get("direction") if isinstance(r.get("trade_parameters"), dict) else None)
                if dr == "LONG": long_l2 += 1
                elif dr == "SHORT": short_l2 += 1
        return {"long_cand": long_c, "short_cand": short_c, "cand_total": cand_total, "long_rej_l2": long_l2, "short_rej_l2": short_l2}

    # A1 SHORT share also from logger AI-direction breakdown (pre-CAND)
    def count_logger_eval_direction(slc: str) -> dict[str, int]:
        cl = A1_BASE / slc / "candidate_features_log.jsonl"
        long_e, short_e = 0, 0
        if cl.exists():
            with open(cl) as f:
                for line in f:
                    r = json.loads(line)
                    d = r.get("ai_direction_evaluated")
                    if d == "LONG": long_e += 1
                    elif d == "SHORT": short_e += 1
        return {"ai_eval_long": long_e, "ai_eval_short": short_e}

    out = {"per_slice": {}, "totals": {}}
    total_a1_long = total_a1_short = 0
    total_f3_long = total_f3_short = 0
    total_a1_eval_long = total_a1_eval_short = 0
    for slc in SLICES:
        a1 = count_cands(A1_BASE / slc / "all_results.json")
        f3_path = F3_BASE / slc / "all_results.json"
        f3 = count_cands(f3_path) if f3_path.exists() else None
        eval_d = count_logger_eval_direction(slc)
        out["per_slice"][slc] = {"a1": a1, "f3": f3, "a1_logger_eval": eval_d}
        total_a1_long += a1["long_cand"]; total_a1_short += a1["short_cand"]
        if f3:
            total_f3_long += f3["long_cand"]; total_f3_short += f3["short_cand"]
        total_a1_eval_long += eval_d["ai_eval_long"]; total_a1_eval_short += eval_d["ai_eval_short"]
    a1_tot = total_a1_long + total_a1_short
    f3_tot = total_f3_long + total_f3_short
    out["totals"] = {
        "a1_long": total_a1_long, "a1_short": total_a1_short, "a1_short_share": total_a1_short / a1_tot if a1_tot else None,
        "f3_long": total_f3_long, "f3_short": total_f3_short, "f3_short_share": total_f3_short / f3_tot if f3_tot else None,
        "a1_logger_long_eval": total_a1_eval_long,
        "a1_logger_short_eval": total_a1_eval_short,
        "a1_logger_short_eval_share": total_a1_eval_short / (total_a1_eval_long + total_a1_eval_short) if (total_a1_eval_long + total_a1_eval_short) else None,
    }
    return out


def e5_pre_ai_gate_reasons(joined: list[dict[str, Any]]) -> dict[str, Any]:
    reasons_all = Counter()
    per_symbol = defaultdict(Counter)
    per_slice = defaultdict(Counter)
    total_skipped = 0
    total_rows = 0
    for j in joined:
        lg = j["logger"]
        total_rows += 1
        if lg.get("pre_ai_gate_skipped"):
            total_skipped += 1
            reason = lg.get("pre_ai_gate_reason") or "?"
            reasons_all[reason] += 1
            per_symbol[lg.get("symbol")][reason] += 1
            per_slice[lg.get("slice")][reason] += 1
    return {
        "total_logger_rows": total_rows,
        "total_pre_ai_gate_skipped": total_skipped,
        "skip_rate": total_skipped / total_rows if total_rows else None,
        "reasons_all": dict(reasons_all.most_common()),
        "per_symbol": {k: dict(v.most_common()) for k, v in per_symbol.items()},
        "per_slice": {k: dict(v.most_common()) for k, v in per_slice.items()},
    }


def e6_per_instrument(joined: list[dict[str, Any]]) -> dict[str, Any]:
    # same as e1-e3 but split by symbol
    by_sym = defaultdict(list)
    for j in joined:
        by_sym[j["logger"].get("symbol")].append(j)
    out = {}
    for sym, rows in by_sym.items():
        out[sym] = {
            "e1_touch": e1_touch_strata(rows),
            "e2_fvg": e2_fvg_strata(rows),
            "e3_direction": e3_direction_breakdown(rows),
        }
    return out


def e7_per_slice_regime(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """Dominant v2_shadow H1 structure direction per slice, then outcomes."""
    # Group by slice
    by_slice = defaultdict(list)
    for j in joined:
        by_slice[j["logger"].get("slice")].append(j)
    out = {}
    for slc, rows in by_slice.items():
        structs = Counter()
        for j in rows:
            d = j["logger"].get("mso_h1_structure_direction")
            structs[d] += 1
        total = sum(structs.values())
        dominant = structs.most_common(1)[0][0] if structs else None
        # Outcome stats among CANDs
        cand_rows = [j for j in rows if (j.get("outcome") or {}).get("decision") == "CANDIDATE"]
        filled = [r for r in cand_rows if (r.get("outcome") or {}).get("outcome") in {"WIN", "LOSS", "BE"}]
        wins = sum(1 for r in filled if (r.get("outcome") or {}).get("outcome") == "WIN")
        shorts = sum(1 for r in cand_rows if (r.get("outcome") or {}).get("direction") == "SHORT")
        out[slc] = {
            "structs_h1": dict(structs),
            "dominant": dominant,
            "dominant_share": structs.most_common(1)[0][1] / total if total else None,
            "n_cand": len(cand_rows),
            "n_cand_filled": len(filled),
            "wins": wins,
            "wr_filled": wins / len(filled) if filled else None,
            "n_short_cand": shorts,
        }
    return out


def e8_c_gate_vs_l2(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """Break down per decision path:
    From logger perspective: c_gate_result breakdown by decision.
    From outcome side: REJECTED_L2 reasons."""
    logger_c_by_decision = defaultdict(Counter)
    for j in joined:
        lg = j["logger"]
        dec = lg.get("decision")
        cg = lg.get("c_gate_result") or {}
        key = f"c1={cg.get('c1_h1_bias_present')}|c2={cg.get('c2_m15_choch_detected')}|c3={cg.get('c3_direction_matches')}"
        logger_c_by_decision[dec][key] += 1
    # L2 reject counts per slice
    l2_reject_reasons = Counter()
    l2_reject_symbol = Counter()
    blocked_limit_symbol = Counter()
    for slc in SLICES:
        with open(A1_BASE / slc / "all_results.json") as f:
            d = json.load(f)
        for r in d.get("results", []):
            if r.get("decision") == "REJECTED_L2":
                reason = r.get("no_trade_reason") or r.get("reason") or "?"
                l2_reject_reasons[reason] += 1
                l2_reject_symbol[r.get("symbol", "?")] += 1
            elif r.get("decision") == "BLOCKED_LIMIT":
                blocked_limit_symbol[r.get("symbol", "?")] += 1
    # per touch bucket x decision: does h1_opp_ob_touch correlate with L2 reject?
    touch_decision = defaultdict(Counter)
    for j in joined:
        lg = j["logger"]
        dec = lg.get("decision")
        t = lg.get("h1_opp_ob_touch")
        bucket = "missing" if t is None else ("1" if t <= 1 else ("2" if t == 2 else ">=3"))
        touch_decision[bucket][dec] += 1
    return {
        "logger_c_gate_breakdown_by_decision": {k: dict(v.most_common()) for k, v in logger_c_by_decision.items()},
        "l2_reject_reasons_all": dict(l2_reject_reasons.most_common(20)),
        "l2_reject_by_symbol": dict(l2_reject_symbol),
        "blocked_limit_by_symbol": dict(blocked_limit_symbol),
        "logger_touch_x_decision": {k: dict(v.most_common()) for k, v in touch_decision.items()},
    }


def e10_setup_grade_outcome(joined: list[dict[str, Any]]) -> dict[str, Any]:
    by_grade = defaultdict(list)
    for j in joined:
        oc = j.get("outcome") or {}
        if oc.get("decision") != "CANDIDATE":
            continue
        if oc.get("outcome") not in {"WIN", "LOSS", "BE"}:
            continue
        grade = oc.get("setup_grade") or j["logger"].get("setup_grade") or "?"
        by_grade[grade].append(oc.get("r_multiple"))
    out = {}
    for g, vals in by_grade.items():
        n = len(vals)
        wins = sum(1 for v in vals if v is not None and v > 0)
        wr_lo, wr_hi = wilson_ci(wins, n)
        mean, elo, ehi = bootstrap_mean_ci([v for v in vals if v is not None], iters=5000) if vals else (float("nan"),) * 3
        out[g] = {
            "n": n, "wins": wins,
            "wr": wins / n if n else float("nan"),
            "wr_ci95": [wr_lo, wr_hi],
            "expectancy_r": mean,
            "expectancy_ci95": [elo, ehi],
        }
    return out


def e11_kz_bucket_outcome(joined: list[dict[str, Any]]) -> dict[str, Any]:
    """KZ x 15-min bucket x outcome on A1 only. No external combine; call out n."""
    buckets = defaultdict(list)
    # key: (symbol, kill_zone, hour:quarter)
    for j in joined:
        oc = j.get("outcome") or {}
        if oc.get("decision") != "CANDIDATE":
            continue
        if oc.get("outcome") not in {"WIN", "LOSS", "BE"}:
            continue
        lg = j["logger"]
        # compute 15-min bucket from hour_utc + timestamp
        ts = lg.get("timestamp_utc") or ""
        # parse minute
        min_ = 0
        if "T" in ts:
            try:
                hh_mm = ts.split("T")[1][:5]
                h_, m_ = hh_mm.split(":")
                min_ = int(m_) // 15 * 15  # snap
            except Exception:
                pass
        bkey = (lg.get("symbol"), lg.get("kill_zone"), f"{lg.get('hour_utc')}:{min_:02d}")
        buckets[bkey].append(oc.get("r_multiple"))
    out = []
    for k, vals in sorted(buckets.items()):
        n = len(vals)
        wins = sum(1 for v in vals if v is not None and v > 0)
        out.append({
            "symbol": k[0], "kill_zone": k[1], "bucket_hhmm": k[2],
            "n": n, "wins": wins,
            "wr": wins / n if n else None,
        })
    # sort by n desc
    out.sort(key=lambda x: (-x["n"],))
    # n>=20 is the target but a1 won't have any; caveat in report
    return {
        "buckets": out,
        "max_n": max((b["n"] for b in out), default=0),
    }


# E12 runs separately (inspects code diffs)


def run_all():
    joined, meta = load_a1_rows()
    # Only use logger rows that have a matched outcome
    joined_matched = [j for j in joined if j["outcome"] is not None]
    print(f"logger_rows={meta['logger_count']}, outcome_rows={meta['outcome_count']}, matched={len(joined_matched)}")

    write_merged(joined_matched, OUT_DIR / "merged_data.jsonl")

    output = {
        "meta": meta,
        "joined_rows_matched": len(joined_matched),
        "E1_touch": e1_touch_strata(joined_matched),
        "E2_fvg": e2_fvg_strata(joined_matched),
        "E3_direction": e3_direction_breakdown(joined_matched),
        "E4_short_share_diff": e4_short_share_diff(joined_matched),
        "E5_pre_ai_gate_reasons": e5_pre_ai_gate_reasons(joined_matched),
        "E6_per_instrument": e6_per_instrument(joined_matched),
        "E7_per_slice_regime": e7_per_slice_regime(joined_matched),
        "E8_c_gate_vs_l2": e8_c_gate_vs_l2(joined_matched),
        "E10_setup_grade": e10_setup_grade_outcome(joined_matched),
        "E11_kz_buckets": e11_kz_bucket_outcome(joined_matched),
    }

    with open(OUT_DIR / "extraction_output.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("Written", OUT_DIR / "extraction_output.json")
    print("Written", OUT_DIR / "merged_data.jsonl")
    return output


if __name__ == "__main__":
    run_all()
