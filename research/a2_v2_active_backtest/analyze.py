"""
A2 v2-active backtest analysis.

Computes fleet + per-instrument WR, expectancy, direction split, MaxDD from
12-slice backtest and applies the pre-registered GO/STAY/HALT criteria
defined in PREREGISTRATION.md.

Pre-registered criteria (also in PREREGISTRATION.md):
  GO to v2 ACTIVE for Monday challenge:
    - fleet Exp R >= +0.15R
    - v2 XAUUSD SHORT share >= 15% of raw CANDs
    - v2 LONG WR (fleet) >= 55%
    - fleet MaxDD <= 8R (= 8% at 1% risk)
  STAY on v2_shadow (v1 production) for Monday:
    - Any GO criterion fails
    - fleet Exp R <= 0
    - LONG WR < 45%
  HALT / council:
    - LONG WR in [45%, 55%] window — ambiguous

Usage:
  python research/a2_v2_active_backtest/analyze.py \
    --slice-dir research/a2_v2_active_backtest/slices \
    --out-md research/a2_v2_active_backtest/ANALYSIS.md \
    --out-json research/a2_v2_active_backtest/analysis_output.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def script_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


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
    # two-sided via erfc
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
    """Aggregate fleet + per-instrument stats from all slices."""
    out = {
        "per_slice": {},
        "fleet": {"cands": [], "filled_cands": [], "cost": 0.0},
        "per_instrument": defaultdict(lambda: {"cands": [], "filled_cands": []}),
    }
    for slice_name, s in slices.items():
        if s.get("skipped"):
            out["per_slice"][slice_name] = {"skipped": True}
            continue
        symbol = None
        cands = []
        filled = []
        evaluations = 0
        for r in s["results"]:
            if r.get("symbol"):
                symbol = r["symbol"]
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
        if symbol:
            out["per_instrument"][symbol]["cands"].extend(cands)
            out["per_instrument"][symbol]["filled_cands"].extend(filled)
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
        }
    long_cands = [r for r in cands if r.get("direction") == "LONG"]
    short_cands = [r for r in cands if r.get("direction") == "SHORT"]
    long_filled = [r for r in filled if r.get("direction") == "LONG"]
    short_filled = [r for r in filled if r.get("direction") == "SHORT"]
    long_wins = sum(1 for r in long_filled if r.get("outcome") == "WIN")
    short_wins = sum(1 for r in short_filled if r.get("outcome") == "WIN")
    all_wins = sum(1 for r in filled if r.get("outcome") == "WIN")
    # Bug fix (red-team C1 2026-04-25): MaxDD must be computed in chronological order,
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


def apply_criteria(fleet_stats: dict, xauusd_stats: dict) -> tuple[str, dict]:
    """Apply pre-registered GO / STAY / HALT criteria."""
    criteria = {
        "fleet_exp_ge_0.15": fleet_stats["exp_filled"] >= 0.15,
        "xauusd_short_share_ge_15pct": xauusd_stats["short_share"] >= 0.15,
        "fleet_long_wr_ge_55pct": fleet_stats["long_wr"] >= 0.55,
        "fleet_maxdd_le_8R": fleet_stats["maxdd"] <= 8.0,
    }
    stay_triggers = {
        "fleet_exp_neg": fleet_stats["exp_filled"] <= 0,
        "fleet_long_wr_lt_45pct": fleet_stats["long_wr"] < 0.45,
    }
    halt_window = 0.45 <= fleet_stats["long_wr"] < 0.55
    if all(criteria.values()):
        verdict = "GO"
    elif stay_triggers["fleet_exp_neg"] or stay_triggers["fleet_long_wr_lt_45pct"]:
        verdict = "STAY"
    elif halt_window:
        verdict = "HALT"
    else:
        # partial — single criterion fails but no STAY trigger
        verdict = "HALT"  # conservative — anything not fully GO defaults to halt
    return verdict, {"criteria": criteria, "stay_triggers": stay_triggers, "halt_window": halt_window}


def f3_comparison() -> dict:
    """F3 session-38 reference numbers for v2-active comparison.

    Sourced from WAVE2_F3_SYNTHESIS_REPORT.md (main HEAD).
    """
    return {
        "fleet": {
            "raw_cand": 588, "filled": 32, "wr_filled": 0.562, "exp_filled": 0.407,
            "total_r": 13.0, "cost": 37.50,
        },
        "xauusd": {
            "raw_cand": 162, "long_raw": 124, "short_raw": 37, "short_share": 0.228,
            "final_cand": 15, "filled": 13, "long_filled": 11, "short_filled": 2,
            "long_wr": 0.455, "short_wr": 1.000, "exp_filled": 0.347, "total_r": 4.5,
            "maxdd": 2.0,
        },
        "usdjpy": {
            "raw_cand": 426, "long_raw": 426, "short_raw": 0, "short_share": 0.0,
            "final_cand": 24, "filled": 19, "long_wr": 0.579, "short_filled": 0,
            "exp_filled": 0.447, "total_r": 8.5, "maxdd": 3.0,
        },
    }


def format_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def format_r(x: float, sig: int = 3) -> str:
    return f"{x:+.3f}R"


def render_md(agg: dict, fleet_stats: dict, per_instr_stats: dict,
              verdict: str, verdict_detail: dict, script_hash: str) -> str:
    f3 = f3_comparison()
    lines = [
        "# A2 v2-Active Backtest — Analysis",
        "",
        f"**Analysis script SHA256:** `{script_hash}`",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Pre-registered criteria:** see `PREREGISTRATION.md` — criteria frozen before analysis ran.",
        "",
        "## Data",
        "",
        "12 slices executed with `--detector-version v2` (NOT v2_shadow — true v2 active).",
        f"- Fleet total cost: ${agg['fleet']['cost']:.2f} (budget $40)",
        f"- Fleet CANDs: {len(agg['fleet']['cands'])} raw / {len(agg['fleet']['filled_cands'])} filled",
        "",
        "## Fleet-level stats",
        "",
        "| Metric | v2-active (A2) | v1-production (F3 baseline) | Delta |",
        "|---|---:|---:|---:|",
        f"| Raw CAND | {fleet_stats['raw_n']} | {f3['fleet']['raw_cand']} | {fleet_stats['raw_n'] - f3['fleet']['raw_cand']:+d} |",
        f"| Filled | {fleet_stats['filled_n']} | {f3['fleet']['filled']} | {fleet_stats['filled_n'] - f3['fleet']['filled']:+d} |",
        f"| WR (filled) | {format_pct(fleet_stats['wr_filled'])} [CI {format_pct(fleet_stats['wr_ci'][0])}, {format_pct(fleet_stats['wr_ci'][1])}] | {format_pct(f3['fleet']['wr_filled'])} | {(fleet_stats['wr_filled'] - f3['fleet']['wr_filled'])*100:+.1f}pp |",
        f"| Expectancy | {format_r(fleet_stats['exp_filled'])} [CI {format_r(fleet_stats['exp_ci'][0])}, {format_r(fleet_stats['exp_ci'][1])}] | {format_r(f3['fleet']['exp_filled'])} | {(fleet_stats['exp_filled'] - f3['fleet']['exp_filled']):+.3f}R |",
        f"| Total R | {fleet_stats['total_r']:+.2f}R | {f3['fleet']['total_r']:+.2f}R | {fleet_stats['total_r'] - f3['fleet']['total_r']:+.2f}R |",
        f"| MaxDD | {fleet_stats['maxdd']:.2f}R | n/a | — |",
        f"| LONG WR | {format_pct(fleet_stats['long_wr'])} [CI {format_pct(fleet_stats['long_wr_ci'][0])}, {format_pct(fleet_stats['long_wr_ci'][1])}] | — | — |",
        f"| SHORT WR | {format_pct(fleet_stats['short_wr'])} [CI {format_pct(fleet_stats['short_wr_ci'][0])}, {format_pct(fleet_stats['short_wr_ci'][1])}] | — | — |",
        "",
    ]
    # per-instrument
    for inst in ["XAUUSD", "USDJPY"]:
        s = per_instr_stats.get(inst)
        if not s:
            continue
        f3_inst = f3.get(inst.lower(), {})
        lines.extend([
            f"## {inst} detail",
            "",
            "| Metric | v2-active (A2) | F3 v2 reference |",
            "|---|---:|---:|",
            f"| Raw CAND | {s['raw_n']} | {f3_inst.get('raw_cand', '-')} |",
            f"| LONG raw share | {format_pct(s['long_share'])} | — |",
            f"| SHORT raw share | {format_pct(s['short_share'])} | {format_pct(f3_inst.get('short_share', 0))} |",
            f"| Filled | {s['filled_n']} (L {s['long_filled_n']} / S {s['short_filled_n']}) | {f3_inst.get('filled', '-')} (L {f3_inst.get('long_filled', '-')} / S {f3_inst.get('short_filled', '-')}) |",
            f"| WR filled | {format_pct(s['wr_filled'])} [CI {format_pct(s['wr_ci'][0])}, {format_pct(s['wr_ci'][1])}] | — |",
            f"| Expectancy | {format_r(s['exp_filled'])} [CI {format_r(s['exp_ci'][0])}, {format_r(s['exp_ci'][1])}] | {format_r(f3_inst.get('exp_filled', 0))} |",
            f"| Total R | {s['total_r']:+.2f}R | {f3_inst.get('total_r', '-'):+.2f}R |" if isinstance(f3_inst.get('total_r'), (int, float)) else f"| Total R | {s['total_r']:+.2f}R | — |",
            f"| LONG WR | {format_pct(s['long_wr'])} [CI {format_pct(s['long_wr_ci'][0])}, {format_pct(s['long_wr_ci'][1])}] | {format_pct(f3_inst.get('long_wr', 0))} |",
            f"| SHORT WR | {format_pct(s['short_wr'])} [CI {format_pct(s['short_wr_ci'][0])}, {format_pct(s['short_wr_ci'][1])}] | {format_pct(f3_inst.get('short_wr', 0))} |",
            f"| MaxDD | {s['maxdd']:.2f}R | {f3_inst.get('maxdd', '-')}R |",
            "",
        ])

    # per-slice table
    lines.extend([
        "## Per-slice summary",
        "",
        "| Slice | Raw | L/S | Filled | L/S | Wins | Total R | Cost |",
        "|---|---:|---|---:|---|---:|---:|---:|",
    ])
    for slice_name, s in agg["per_slice"].items():
        if s.get("skipped"):
            lines.append(f"| {slice_name} | SKIPPED | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {slice_name} | {s['candidates']} | {s['long_cands']}/{s['short_cands']} | "
            f"{s['filled']} | {s['long_filled']}/{s['short_filled']} | "
            f"{s['long_wins'] + s['short_wins']} | {s['r_sum_filled']:+.2f} | ${s['cost']:.2f} |"
        )
    lines.append("")

    # pre-reg verdict
    crit = verdict_detail["criteria"]
    stay = verdict_detail["stay_triggers"]
    lines.extend([
        "## Pre-registered criteria check",
        "",
        "| Criterion | Threshold | Observed | Status |",
        "|---|---:|---:|---|",
        f"| Fleet Exp R | ≥ +0.150R | {format_r(fleet_stats['exp_filled'])} | {'PASS' if crit['fleet_exp_ge_0.15'] else 'FAIL'} |",
        f"| XAUUSD SHORT share | ≥ 15% | {format_pct(per_instr_stats.get('XAUUSD', {}).get('short_share', 0))} | {'PASS' if crit['xauusd_short_share_ge_15pct'] else 'FAIL'} |",
        f"| Fleet LONG WR | ≥ 55% | {format_pct(fleet_stats['long_wr'])} | {'PASS' if crit['fleet_long_wr_ge_55pct'] else 'FAIL'} |",
        f"| Fleet MaxDD | ≤ 8R | {fleet_stats['maxdd']:.2f}R | {'PASS' if crit['fleet_maxdd_le_8R'] else 'FAIL'} |",
        "",
        "## STAY triggers check",
        "",
        f"- fleet_exp_neg: {'TRIGGERED' if stay['fleet_exp_neg'] else 'no'}",
        f"- fleet_long_wr_lt_45pct: {'TRIGGERED' if stay['fleet_long_wr_lt_45pct'] else 'no'}",
        f"- halt_window (LONG WR in [45%, 55%]): {'YES' if verdict_detail['halt_window'] else 'no'}",
        "",
        f"## VERDICT: **{verdict}**",
        "",
    ])

    if verdict == "GO":
        lines.append("All 4 pre-registered criteria PASS. Flip `detector_version: v2_shadow → v2` "
                     "for Monday 2026-04-27 paid-FTMO-challenge deploy.")
    elif verdict == "STAY":
        fails = [k for k, v in crit.items() if not v]
        lines.append(f"Hard STAY: {', '.join(fails)} + stay-trigger active. "
                     "Stay on `v2_shadow` (v1 production) for Monday challenge.")
    else:  # HALT
        fails = [k for k, v in crit.items() if not v]
        lines.append(f"HALT / council: {', '.join(fails) if fails else 'ambiguous LONG WR window'}. "
                     "CEO review required before Monday detector decision.")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slice-dir", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-json", default=None)
    args = p.parse_args()

    script_hash = script_sha256(__file__)

    slices = load_slices(args.slice_dir)
    agg = aggregate(slices)

    fleet_stats = slice_stats(agg["fleet"]["cands"], agg["fleet"]["filled_cands"])
    per_instr_stats = {
        inst: slice_stats(d["cands"], d["filled_cands"])
        for inst, d in agg["per_instrument"].items()
    }

    # XAUUSD is the critical one for SHORT-share gate
    xauusd_stats = per_instr_stats.get("XAUUSD", {
        "short_share": 0.0, "long_wr": 0.0, "exp_filled": 0.0,
    })
    verdict, verdict_detail = apply_criteria(fleet_stats, xauusd_stats)

    md = render_md(agg, fleet_stats, per_instr_stats, verdict, verdict_detail, script_hash)
    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)

    if args.out_json:
        out = {
            "script_sha256": script_hash,
            "verdict": verdict,
            "verdict_detail": verdict_detail,
            "fleet_stats": {k: (list(v) if isinstance(v, tuple) else v) for k, v in fleet_stats.items()},
            "per_instrument_stats": {
                inst: {k: (list(v) if isinstance(v, tuple) else v) for k, v in s.items()}
                for inst, s in per_instr_stats.items()
            },
            "per_slice": agg["per_slice"],
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
