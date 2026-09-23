"""
LIRA A/B 12-Slice Backtest analysis.

Computes fleet + per-instrument WR, expectancy, direction split, MaxDD from
12-slice LIRA backtest and applies the pre-registered LIRA-GO/STAY/HALT
criteria from PREREGISTRATION.md.

Pre-registered criteria (also in PREREGISTRATION.md):
  LIRA-GO (promote post-Monday challenge):
    - LIRA fleet Exp R >= +0.40R
    - LIRA parse error rate <= 5%
    - LIRA XAUUSD SHORT WR >= 40% if n >= 3 (auto-pass if n < 3)
    - LIRA fleet MaxDD <= 8R
  LIRA-STAY:
    - LIRA fleet Exp R <= A2 V3 baseline (+0.333R)
    - LIRA parse error rate > 5%
  LIRA-HALT:
    - LIRA fleet Exp R in (+0.333R, +0.40R) ambiguous window

Side-by-side comparison vs:
  - A2 V3-on-v2 (research/a2_v2_active_backtest/)
  - F3 V3-on-v2-detector (research/f3_backtest_2026-04-24/)

Usage:
  python research/lira_ab_backtest/analyze.py \
    --slice-dir research/lira_ab_backtest/slices \
    --out-md research/lira_ab_backtest/ANALYSIS.md \
    --out-json research/lira_ab_backtest/analysis_output.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def script_sha256(path: str) -> str:
    """Compute LF-normalized SHA256 of the script file.

    Line endings are normalized to LF before hashing so the value is stable
    across Windows (CRLF) and Unix (LF) checkouts. The pre-registered hash
    in PREREGISTRATION.md uses the same normalization.
    """
    with open(path, "rb") as f:
        content = f.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_ci(values: list[float], n_iter: int = 5000, rng_seed: int = 17) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(rng_seed)
    n = len(values)
    means = []
    for _ in range(n_iter):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int(0.025 * n_iter)
    hi_idx = int(0.975 * n_iter) - 1
    return (means[lo_idx], means[hi_idx])


def max_drawdown_from_peak(r_series: list[float]) -> float:
    if not r_series:
        return 0.0
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in r_series:
        cum += r
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)
    return max_dd


def two_prop_pvalue(k1: int, n1: int, k2: int, n2: int) -> float:
    """Pooled two-proportion z-test, two-sided."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    if p_pool in (0.0, 1.0):
        return 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return math.erfc(abs(z) / math.sqrt(2))


def load_slices(slice_dir: str) -> dict:
    slices = {}
    for p in sorted(os.listdir(slice_dir)):
        sdir = os.path.join(slice_dir, p)
        if not os.path.isdir(sdir):
            continue
        ar = os.path.join(sdir, "all_results.json")
        if not os.path.exists(ar):
            slices[p] = {"skipped": True, "reason": "no all_results.json"}
            continue
        with open(ar) as f:
            data = json.load(f)
        slices[p] = {
            "start": data.get("start"),
            "end": data.get("end"),
            "total_cost": data.get("total_cost", 0.0),
            "results": data.get("results", []),
        }
    return slices


def aggregate(slices: dict) -> dict:
    """Aggregate fleet + per-instrument stats."""
    out = {
        "per_slice": {},
        "fleet": {"cands": [], "filled_cands": [], "cost": 0.0, "parse_errors": 0, "evaluations": 0},
        "per_instrument": defaultdict(lambda: {"cands": [], "filled_cands": [], "parse_errors": 0, "evaluations": 0}),
    }
    for slice_name, s in slices.items():
        if s.get("skipped"):
            out["per_slice"][slice_name] = {"skipped": True}
            continue
        symbol = None
        cands = []
        filled = []
        evaluations = 0
        parse_errors = 0
        for r in s["results"]:
            if r.get("symbol"):
                symbol = r["symbol"]
            decision = r.get("decision", "")
            if decision == "PARSE_ERROR":
                parse_errors += 1
            if r.get("decision") == "CANDIDATE":
                cands.append(r)
                if r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    filled.append(r)
            if r.get("cost", 0) > 0:
                evaluations += 1
        out["per_slice"][slice_name] = {
            "symbol": symbol,
            "start": s["start"],
            "end": s["end"],
            "cost": s["total_cost"],
            "evaluations": evaluations,
            "parse_errors": parse_errors,
            "candidates": len(cands),
            "filled": len(filled),
            "unfilled": sum(1 for r in cands if r.get("outcome") == "UNFILLED"),
            "long_cands": sum(1 for r in cands if r.get("direction") == "LONG"),
            "short_cands": sum(1 for r in cands if r.get("direction") == "SHORT"),
            "long_filled": sum(1 for r in filled if r.get("direction") == "LONG"),
            "short_filled": sum(1 for r in filled if r.get("direction") == "SHORT"),
            "long_wins": sum(1 for r in filled if r.get("direction") == "LONG" and r.get("outcome") == "WIN"),
            "short_wins": sum(1 for r in filled if r.get("direction") == "SHORT" and r.get("outcome") == "WIN"),
            "r_sum_filled": sum(r.get("r_multiple", 0.0) for r in filled),
        }
        out["fleet"]["cands"].extend(cands)
        out["fleet"]["filled_cands"].extend(filled)
        out["fleet"]["cost"] += s["total_cost"]
        out["fleet"]["parse_errors"] += parse_errors
        out["fleet"]["evaluations"] += evaluations
        if symbol:
            out["per_instrument"][symbol]["cands"].extend(cands)
            out["per_instrument"][symbol]["filled_cands"].extend(filled)
            out["per_instrument"][symbol]["parse_errors"] += parse_errors
            out["per_instrument"][symbol]["evaluations"] += evaluations
    return out


def slice_stats(cands: list, filled: list) -> dict:
    if not cands:
        return {
            "raw_n": 0, "filled_n": 0, "long_share": 0.0, "short_share": 0.0,
            "long_filled_n": 0, "short_filled_n": 0,
            "wr_filled": 0.0, "wr_ci": (0.0, 0.0),
            "exp_filled": 0.0, "exp_ci": (0.0, 0.0),
            "long_wr": 0.0, "long_wr_ci": (0.0, 0.0),
            "short_wr": 0.0, "short_wr_ci": (0.0, 0.0),
            "total_r": 0.0, "maxdd": 0.0,
            "unfilled_n": 0,
        }
    long_cands = [r for r in cands if r.get("direction") == "LONG"]
    short_cands = [r for r in cands if r.get("direction") == "SHORT"]
    long_filled = [r for r in filled if r.get("direction") == "LONG"]
    short_filled = [r for r in filled if r.get("direction") == "SHORT"]
    long_wins = sum(1 for r in long_filled if r.get("outcome") == "WIN")
    short_wins = sum(1 for r in short_filled if r.get("outcome") == "WIN")
    all_wins = sum(1 for r in filled if r.get("outcome") == "WIN")
    # Bug fix (red-team C1): MaxDD must be computed in chronological order,
    # not slice-iteration order. candle_time is ISO 8601 so lexical == chronological.
    filled_chrono = sorted(filled, key=lambda r: r.get("candle_time", ""))
    r_series = [r.get("r_multiple", 0.0) for r in filled_chrono]
    return {
        "raw_n": len(cands),
        "filled_n": len(filled),
        "unfilled_n": sum(1 for r in cands if r.get("outcome") == "UNFILLED"),
        "long_share": len(long_cands) / len(cands) if cands else 0.0,
        "short_share": len(short_cands) / len(cands) if cands else 0.0,
        "long_filled_n": len(long_filled),
        "short_filled_n": len(short_filled),
        "wr_filled": all_wins / len(filled) if filled else 0.0,
        "wr_ci": wilson_ci(all_wins, len(filled)),
        "exp_filled": sum(r_series) / len(r_series) if r_series else 0.0,
        "exp_ci": bootstrap_ci(r_series) if r_series else (0.0, 0.0),
        "long_wr": long_wins / len(long_filled) if long_filled else 0.0,
        "long_wr_ci": wilson_ci(long_wins, len(long_filled)),
        "short_wr": short_wins / len(short_filled) if short_filled else 0.0,
        "short_wr_ci": wilson_ci(short_wins, len(short_filled)),
        "total_r": sum(r_series),
        "maxdd": max_drawdown_from_peak(r_series),
    }


def apply_lira_criteria(fleet_stats: dict, xauusd_stats: dict, parse_rate: float) -> tuple[str, dict]:
    """Apply pre-registered LIRA-GO / LIRA-STAY / LIRA-HALT criteria."""
    A2_BASELINE_EXP = 0.333  # research/a2_v2_active_backtest/analysis_output.json
    GO_EXP_BAR = 0.40        # F3 v2 anchor (+0.407)
    PARSE_BAR = 0.05         # 5% headroom over canary 0/60
    SHORT_WR_BAR = 0.40
    SHORT_N_FLOOR = 3
    MAXDD_BAR = 8.0

    n_short = xauusd_stats.get("short_filled_n", 0)
    short_wr = xauusd_stats.get("short_wr", 0.0)
    short_wr_pass = (n_short < SHORT_N_FLOOR) or (short_wr >= SHORT_WR_BAR)

    criteria = {
        "lira_fleet_exp_ge_0.40": fleet_stats["exp_filled"] >= GO_EXP_BAR,
        "lira_parse_rate_le_5pct": parse_rate <= PARSE_BAR,
        f"lira_xauusd_short_wr_ge_40pct_or_n_lt_{SHORT_N_FLOOR}": short_wr_pass,
        "lira_fleet_maxdd_le_8R": fleet_stats["maxdd"] <= MAXDD_BAR,
    }
    stay_triggers = {
        "lira_fleet_exp_le_a2_baseline": fleet_stats["exp_filled"] <= A2_BASELINE_EXP,
        "lira_parse_rate_gt_5pct": parse_rate > PARSE_BAR,
    }
    in_halt_window = (A2_BASELINE_EXP < fleet_stats["exp_filled"] < GO_EXP_BAR)

    if all(criteria.values()):
        verdict = "LIRA-GO"
    elif stay_triggers["lira_fleet_exp_le_a2_baseline"] or stay_triggers["lira_parse_rate_gt_5pct"]:
        verdict = "LIRA-STAY"
    elif in_halt_window:
        verdict = "LIRA-HALT"
    else:
        # Above ambiguous window but failed a non-Exp criterion (e.g. MaxDD or SHORT WR)
        # Conservative default: HALT for council review.
        verdict = "LIRA-HALT"
    return verdict, {
        "criteria": criteria,
        "stay_triggers": stay_triggers,
        "in_halt_window": in_halt_window,
        "n_short": n_short,
        "short_wr_value": short_wr,
        "parse_rate_value": parse_rate,
    }


def baselines() -> dict:
    """Reference numbers from F3 (v2) and A2 (V3-on-v2) on the SAME 12 slices."""
    return {
        # F3 = research/f3_backtest_2026-04-24/ — V2 detector, V3 prompt
        "f3": {
            "fleet": {"raw_cand": 588, "filled": 32, "wr_filled": 0.562, "exp_filled": 0.407,
                      "total_r": 13.0, "cost": 37.50},
            "xauusd": {"raw_cand": 162, "long_raw": 124, "short_raw": 37, "short_share": 0.228,
                       "filled": 13, "long_filled": 11, "short_filled": 2,
                       "long_wr": 0.455, "short_wr": 1.000, "exp_filled": 0.347, "total_r": 4.5,
                       "maxdd": 2.0},
            "usdjpy": {"raw_cand": 426, "long_raw": 426, "short_raw": 0, "short_share": 0.0,
                       "filled": 19, "long_wr": 0.579, "short_filled": 0,
                       "exp_filled": 0.447, "total_r": 8.5, "maxdd": 3.0},
        },
        # A2 = research/a2_v2_active_backtest/ — V2 detector, V3 prompt (re-run)
        # Numbers loaded dynamically below.
        "a2": "see-loader",
    }


def load_a2_baseline(a2_json_path: str) -> dict | None:
    if not os.path.exists(a2_json_path):
        return None
    with open(a2_json_path) as f:
        return json.load(f)


def format_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def format_r(x: float) -> str:
    return f"{x:+.3f}R"


def render_md(agg: dict, fleet_stats: dict, per_instr_stats: dict,
              verdict: str, verdict_detail: dict, script_hash: str,
              parse_rate: float, a2_baseline: dict | None) -> str:
    f3 = baselines()["f3"]
    a2_fleet = (a2_baseline or {}).get("fleet_stats") if a2_baseline else None
    a2_xauusd = ((a2_baseline or {}).get("per_instrument_stats") or {}).get("XAUUSD")
    a2_usdjpy = ((a2_baseline or {}).get("per_instrument_stats") or {}).get("USDJPY")

    lines = [
        "# LIRA A/B 12-Slice Backtest — Analysis",
        "",
        f"**Analysis script SHA256:** `{script_hash}`",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Pre-registered criteria:** see `PREREGISTRATION.md` — frozen before analysis ran.",
        "",
        "## Data",
        "",
        "12 slices executed with `--detector-version v2` + LIRA system prompt + DP4 schema_adapter.",
        f"- Fleet total cost: ${agg['fleet']['cost']:.2f} (budget $80 hard cap)",
        f"- Fleet evaluations (API calls): {agg['fleet']['evaluations']}",
        f"- Fleet CANDs: {len(agg['fleet']['cands'])} raw / {len(agg['fleet']['filled_cands'])} filled",
        f"- Fleet parse errors: {agg['fleet']['parse_errors']} of {agg['fleet']['evaluations']} = {format_pct(parse_rate)}",
        "",
        "## Fleet-level — 3-way comparison (LIRA vs A2-V3 vs F3-V3)",
        "",
        "All three runs use IDENTICAL 12 slices, IDENTICAL v2 detector, IDENTICAL fill logic.",
        "Only difference: LIRA uses decision-first prompt + schema adapter.",
        "",
        "| Metric | LIRA (this) | A2 V3 (v2 detector) | F3 V3 (v2 detector) |",
        "|---|---:|---:|---:|",
        f"| Raw CAND | {fleet_stats['raw_n']} | "
        f"{a2_fleet['raw_n'] if a2_fleet else 'n/a'} | "
        f"{f3['fleet']['raw_cand']} |",
        f"| Filled | {fleet_stats['filled_n']} | "
        f"{a2_fleet['filled_n'] if a2_fleet else 'n/a'} | "
        f"{f3['fleet']['filled']} |",
        f"| WR (filled) | {format_pct(fleet_stats['wr_filled'])} | "
        f"{format_pct(a2_fleet['wr_filled']) if a2_fleet else 'n/a'} | "
        f"{format_pct(f3['fleet']['wr_filled'])} |",
        f"| Expectancy | {format_r(fleet_stats['exp_filled'])} | "
        f"{format_r(a2_fleet['exp_filled']) if a2_fleet else 'n/a'} | "
        f"{format_r(f3['fleet']['exp_filled'])} |",
        f"| Total R | {fleet_stats['total_r']:+.2f}R | "
        f"{a2_fleet['total_r']:+.2f}R" if a2_fleet else "n/a"
        f" | {f3['fleet']['total_r']:+.2f}R |",
        f"| MaxDD | {fleet_stats['maxdd']:.2f}R | "
        f"{a2_fleet['maxdd']:.2f}R" if a2_fleet else "n/a"
        f" | n/a |",
        f"| Parse errors | {agg['fleet']['parse_errors']} ({format_pct(parse_rate)}) | "
        f"unknown | unknown |",
        "",
    ]

    # CIs separate row for clarity
    lines.extend([
        "### LIRA confidence intervals (Wilson WR, bootstrap Exp)",
        "",
        f"- Fleet WR: {format_pct(fleet_stats['wr_filled'])} CI [{format_pct(fleet_stats['wr_ci'][0])}, {format_pct(fleet_stats['wr_ci'][1])}]",
        f"- Fleet Exp R: {format_r(fleet_stats['exp_filled'])} CI [{format_r(fleet_stats['exp_ci'][0])}, {format_r(fleet_stats['exp_ci'][1])}]",
        f"- Fleet LONG WR: {format_pct(fleet_stats['long_wr'])} CI [{format_pct(fleet_stats['long_wr_ci'][0])}, {format_pct(fleet_stats['long_wr_ci'][1])}]",
        f"- Fleet SHORT WR: {format_pct(fleet_stats['short_wr'])} CI [{format_pct(fleet_stats['short_wr_ci'][0])}, {format_pct(fleet_stats['short_wr_ci'][1])}]",
        "",
    ])

    # per-instrument 3-way
    for inst in ["XAUUSD", "USDJPY"]:
        s = per_instr_stats.get(inst)
        if not s:
            continue
        f3_inst = f3.get(inst.lower(), {})
        a2_inst = a2_xauusd if inst == "XAUUSD" else a2_usdjpy
        lines.extend([
            f"## {inst} — 3-way comparison",
            "",
            "| Metric | LIRA (this) | A2 V3 | F3 V3 |",
            "|---|---:|---:|---:|",
            f"| Raw CAND | {s['raw_n']} | "
            f"{a2_inst['raw_n'] if a2_inst else 'n/a'} | "
            f"{f3_inst.get('raw_cand', 'n/a')} |",
            f"| LONG raw share | {format_pct(s['long_share'])} | "
            f"{format_pct(a2_inst['long_share']) if a2_inst else 'n/a'} | "
            f"— |",
            f"| SHORT raw share | {format_pct(s['short_share'])} | "
            f"{format_pct(a2_inst['short_share']) if a2_inst else 'n/a'} | "
            f"{format_pct(f3_inst.get('short_share', 0))} |",
            f"| Filled | {s['filled_n']} (L {s['long_filled_n']}/S {s['short_filled_n']}) | "
            f"{a2_inst['filled_n'] if a2_inst else 'n/a'} | "
            f"{f3_inst.get('filled', 'n/a')} |",
            f"| WR filled | {format_pct(s['wr_filled'])} | "
            f"{format_pct(a2_inst['wr_filled']) if a2_inst else 'n/a'} | "
            f"— |",
            f"| Expectancy | {format_r(s['exp_filled'])} | "
            f"{format_r(a2_inst['exp_filled']) if a2_inst else 'n/a'} | "
            f"{format_r(f3_inst.get('exp_filled', 0))} |",
            f"| Total R | {s['total_r']:+.2f}R | "
            f"{a2_inst['total_r']:+.2f}R" if a2_inst else "n/a"
            f" | {f3_inst.get('total_r', 'n/a')} |",
            f"| LONG WR | {format_pct(s['long_wr'])} | "
            f"{format_pct(a2_inst['long_wr']) if a2_inst else 'n/a'} | "
            f"{format_pct(f3_inst.get('long_wr', 0))} |",
            f"| SHORT WR | {format_pct(s['short_wr'])} | "
            f"{format_pct(a2_inst['short_wr']) if a2_inst else 'n/a'} | "
            f"{format_pct(f3_inst.get('short_wr', 0))} |",
            f"| MaxDD | {s['maxdd']:.2f}R | "
            f"{a2_inst['maxdd']:.2f}R" if a2_inst else "n/a"
            f" | {f3_inst.get('maxdd', 'n/a')} |",
            "",
        ])

    # per-slice table
    lines.extend([
        "## Per-slice summary",
        "",
        "| Slice | Raw | L/S | Filled | L/S | Wins | Total R | Parse | Cost |",
        "|---|---:|---|---:|---|---:|---:|---:|---:|",
    ])
    for slice_name, s in agg["per_slice"].items():
        if s.get("skipped"):
            lines.append(f"| {slice_name} | SKIPPED | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {slice_name} | {s['candidates']} | {s['long_cands']}/{s['short_cands']} | "
            f"{s['filled']} | {s['long_filled']}/{s['short_filled']} | "
            f"{s['long_wins'] + s['short_wins']} | {s['r_sum_filled']:+.2f} | "
            f"{s['parse_errors']} | ${s['cost']:.2f} |"
        )
    lines.append("")

    # pre-reg verdict
    crit = verdict_detail["criteria"]
    stay = verdict_detail["stay_triggers"]
    lines.extend([
        "## Pre-registered LIRA criteria check",
        "",
        "| Criterion | Threshold | Observed | Status |",
        "|---|---:|---:|---|",
        f"| LIRA fleet Exp R | >= +0.400R | {format_r(fleet_stats['exp_filled'])} | "
        f"{'PASS' if crit['lira_fleet_exp_ge_0.40'] else 'FAIL'} |",
        f"| LIRA parse rate | <= 5.0% | {format_pct(parse_rate)} | "
        f"{'PASS' if crit['lira_parse_rate_le_5pct'] else 'FAIL'} |",
        f"| LIRA XAUUSD SHORT WR | >= 40% if n>=3 | "
        f"{format_pct(verdict_detail['short_wr_value'])} (n={verdict_detail['n_short']}) | "
        f"{'PASS' if list(crit.values())[2] else 'FAIL'} |",
        f"| LIRA fleet MaxDD | <= 8R | {fleet_stats['maxdd']:.2f}R | "
        f"{'PASS' if crit['lira_fleet_maxdd_le_8R'] else 'FAIL'} |",
        "",
        "## STAY triggers check",
        "",
        f"- lira_fleet_exp_le_a2_baseline (+0.333R): {'TRIGGERED' if stay['lira_fleet_exp_le_a2_baseline'] else 'no'}",
        f"- lira_parse_rate_gt_5pct: {'TRIGGERED' if stay['lira_parse_rate_gt_5pct'] else 'no'}",
        f"- in_halt_window (Exp R in (+0.333, +0.40)): {'YES' if verdict_detail['in_halt_window'] else 'no'}",
        "",
        f"## VERDICT: **{verdict}**",
        "",
    ])

    if verdict == "LIRA-GO":
        lines.append("All 4 pre-registered LIRA-GO criteria PASS. Recommend cold-review pass on "
                     "LIRA prompt, then schedule cutover post-Monday challenge.")
    elif verdict == "LIRA-STAY":
        fails = [k for k, v in stay.items() if v]
        lines.append(f"LIRA-STAY: {', '.join(fails) or 'criteria fail without stay-trigger'}. "
                     "DP4 surprise was data-thin / cherry-picked. V3 stays as production prompt; "
                     "shelve LIRA or re-investigate the 3-slice DP4 result for missing context.")
    else:  # LIRA-HALT
        fails = [k for k, v in crit.items() if not v]
        lines.append(f"LIRA-HALT / council: {', '.join(fails) if fails else 'ambiguous Exp R window'}. "
                     "CEO review required — LIRA above A2 baseline but below F3 anchor.")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slice-dir", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-json", default=None)
    p.add_argument("--a2-baseline-json",
                   default="research/a2_v2_active_backtest/analysis_output.json",
                   help="Path to A2 analysis_output.json for side-by-side baseline.")
    args = p.parse_args()

    script_hash = script_sha256(__file__)

    slices = load_slices(args.slice_dir)
    agg = aggregate(slices)

    fleet_stats = slice_stats(agg["fleet"]["cands"], agg["fleet"]["filled_cands"])
    per_instr_stats = {
        inst: slice_stats(d["cands"], d["filled_cands"])
        for inst, d in agg["per_instrument"].items()
    }

    parse_rate = (agg["fleet"]["parse_errors"] / agg["fleet"]["evaluations"]
                  if agg["fleet"]["evaluations"] else 0.0)

    xauusd_stats = per_instr_stats.get("XAUUSD", {
        "short_share": 0.0, "long_wr": 0.0, "exp_filled": 0.0,
        "short_wr": 0.0, "short_filled_n": 0,
    })
    verdict, verdict_detail = apply_lira_criteria(fleet_stats, xauusd_stats, parse_rate)

    a2_baseline = load_a2_baseline(args.a2_baseline_json)

    md = render_md(agg, fleet_stats, per_instr_stats, verdict, verdict_detail,
                   script_hash, parse_rate, a2_baseline)
    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)

    if args.out_json:
        out = {
            "script_sha256": script_hash,
            "verdict": verdict,
            "verdict_detail": verdict_detail,
            "parse_rate": parse_rate,
            "fleet_stats": {k: (list(v) if isinstance(v, tuple) else v) for k, v in fleet_stats.items()},
            "per_instrument_stats": {
                inst: {k: (list(v) if isinstance(v, tuple) else v) for k, v in s.items()}
                for inst, s in per_instr_stats.items()
            },
            "per_slice": agg["per_slice"],
            "fleet_aggregate": {
                "total_cost": agg["fleet"]["cost"],
                "evaluations": agg["fleet"]["evaluations"],
                "parse_errors": agg["fleet"]["parse_errors"],
            },
        }
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)

    print(f"Wrote {args.out_md}")
    print(f"Script hash: {script_hash}")
    if args.out_json:
        print(f"Wrote {args.out_json}")
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
