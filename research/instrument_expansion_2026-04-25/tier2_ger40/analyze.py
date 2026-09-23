"""GER40 Tier-2 Instrument Expansion — analysis & verdict.

Aggregates 12 parallel slices into fleet stats, applies pre-registered
acceptance criteria, and emits REPORT.md + aggregate.json + all_results.json.

Pre-registered criteria (frozen before analysis ran):

  PROMOTE-LIVE         — WR >= 55% AND Exp R >= +0.10R AND n >= 30 AND MaxDD <= 8R
  3-DAY-LIVE-OBSERVE   — Exp R > 0 AND n >= 30 AND MaxDD <= 8R but WR borderline (45-55%)
  OBSERVER-14D         — Exp R > 0 but n < 30 OR mixed signals
  REJECT               — Exp R <= 0 OR n < 10 OR MaxDD > 8R

Usage::

  python research/instrument_expansion_2026-04-25/tier2_ger40/analyze.py \
      --slice-dir research/instrument_expansion_2026-04-25/tier2_ger40/slices \
      --out-md  research/instrument_expansion_2026-04-25/tier2_ger40/REPORT.md \
      --out-json research/instrument_expansion_2026-04-25/tier2_ger40/aggregate.json \
      --out-results research/instrument_expansion_2026-04-25/tier2_ger40/all_results.json
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
    """Aggregate fleet stats from all slices."""
    out = {
        "per_slice": {},
        "fleet": {"all_rows": [], "cands": [], "filled_cands": [], "cost": 0.0},
    }
    for slice_name, s in slices.items():
        if s.get("skipped"):
            out["per_slice"][slice_name] = {"skipped": True}
            continue
        cands = []
        filled = []
        evaluations = 0
        for r in s["results"]:
            if r.get("decision") == "CANDIDATE":
                cands.append(r)
                if r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    filled.append(r)
            if r.get("cost", 0) > 0:
                evaluations += 1
        out["per_slice"][slice_name] = {
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
            "kz_breakdown": dict(Counter(r.get("kill_zone", "?") for r in cands)),
        }
        out["fleet"]["all_rows"].extend(s["results"])
        out["fleet"]["cands"].extend(cands)
        out["fleet"]["filled_cands"].extend(filled)
        out["fleet"]["cost"] += s["total_cost"]
    return out


def slice_stats(cands: list, filled: list) -> dict:
    """Compute summary stats from a list of CAND + filled rows."""
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
    # Chronological MaxDD (red-team C1 fix)
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
        "long_wins": long_wins,
        "short_wins": short_wins,
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


def monthly_breakdown(filled: list) -> dict:
    """Per-month outcome breakdown."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in filled:
        d = r.get("date") or r.get("candle_time", "")[:10]
        if d:
            by_month[d[:7]].append(r)
    out = {}
    for m, rows in sorted(by_month.items()):
        wins = sum(1 for r in rows if r.get("outcome") == "WIN")
        rs = [r.get("r_multiple", 0.0) for r in rows]
        out[m] = {
            "n": len(rows),
            "wins": wins,
            "losses": len(rows) - wins,
            "wr": wins / len(rows) if rows else 0.0,
            "exp": sum(rs) / len(rs) if rs else 0.0,
            "total_r": sum(rs),
        }
    return out


def kz_breakdown(filled: list) -> dict:
    """Per-kill-zone outcome breakdown."""
    by_kz: dict[str, list[dict]] = defaultdict(list)
    for r in filled:
        by_kz[r.get("kill_zone", "?")].append(r)
    out = {}
    for k, rows in by_kz.items():
        wins = sum(1 for r in rows if r.get("outcome") == "WIN")
        rs = [r.get("r_multiple", 0.0) for r in rows]
        out[k] = {
            "n": len(rows),
            "wins": wins,
            "losses": len(rows) - wins,
            "wr": wins / len(rows) if rows else 0.0,
            "exp": sum(rs) / len(rs) if rs else 0.0,
            "total_r": sum(rs),
        }
    return out


def framework_attribution(rows: list) -> dict:
    """Best-effort framework attribution from CAND rows.

    The simulator does not currently emit a `framework` field — extract from
    the AI raw response or no_trade_reason where possible.
    """
    out: dict[str, int] = Counter()
    for r in rows:
        # Simulator normalizes raw_response into setup_grade etc. but framework
        # isn't currently captured. Use a coarse proxy: scan raw_response if present.
        rr = r.get("raw_response", "")
        framework = ""
        if isinstance(rr, str):
            for fw in ("ob_retest", "fvg_fill", "breaker_re_entry"):
                if f'"setup_pattern": "{fw}"' in rr or f'"framework": "{fw}"' in rr:
                    framework = fw
                    break
        if not framework:
            framework = "(unknown)"
        out[framework] += 1
    return dict(out)


def apply_criteria(fleet_stats: dict) -> tuple[str, dict]:
    """Apply pre-registered acceptance criteria."""
    n = fleet_stats["filled_n"]
    wr = fleet_stats["wr_filled"]
    expR = fleet_stats["exp_filled"]
    maxdd = fleet_stats["maxdd"]

    promote = (wr >= 0.55) and (expR >= 0.10) and (n >= 30) and (maxdd <= 8.0)
    reject = (expR <= 0) or (n < 10) or (maxdd > 8.0)
    three_day = (
        not promote and not reject
        and (expR > 0) and (n >= 30) and (maxdd <= 8.0)
        and 0.45 <= wr < 0.55
    )
    observer = not promote and not reject and not three_day and (expR > 0)

    if promote:
        verdict = "PROMOTE-LIVE"
    elif three_day:
        verdict = "3-DAY-LIVE-OBSERVE"
    elif observer:
        verdict = "OBSERVER-14D"
    else:
        verdict = "REJECT"
    return verdict, {
        "promote_live": {
            "criteria": {
                "wr_ge_55pct": wr >= 0.55,
                "exp_ge_0.10R": expR >= 0.10,
                "n_ge_30": n >= 30,
                "maxdd_le_8R": maxdd <= 8.0,
            },
            "all_pass": promote,
        },
        "three_day_observe": {
            "criteria": {
                "exp_gt_0": expR > 0,
                "n_ge_30": n >= 30,
                "maxdd_le_8R": maxdd <= 8.0,
                "wr_in_45_55_window": 0.45 <= wr < 0.55,
            },
        },
        "reject_triggers": {
            "exp_le_0": expR <= 0,
            "n_lt_10": n < 10,
            "maxdd_gt_8R": maxdd > 8.0,
        },
    }


def fmt_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def fmt_r(x: float) -> str:
    return f"{x:+.3f}R"


def render_md(agg: dict, fleet_stats: dict, monthly: dict, kz: dict,
              fw: dict, verdict: str, verdict_detail: dict, script_hash: str,
              total_cost: float) -> str:
    lines = [
        "# GER40 Tier-2 Instrument Expansion — F3-Style 12-Slice Backtest",
        "",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Analysis script SHA256:** `{script_hash}`",
        "**Pre-registered acceptance criteria:** WR >= 55%, Exp R >= +0.10R, n >= 30, MaxDD <= 8R",
        "",
        "## Configuration",
        "",
        "- **Symbol:** GER40 (DAX index, FTMO-tradable)",
        "- **Window:** 2026-01-02 -> 2026-04-13",
        "- **Slices:** 12 parallel (6-trading-day chunks; s12 = 4 trading days)",
        "- **Detector:** v2_shadow (production v1, v2 shadow-logged)",
        "- **Frameworks:** ob_retest + fvg_fill + breaker_re_entry (multi-framework, Wave 1 default)",
        "- **Kill zones:** London-late 10:00-12:00 UTC + NY 14:00-19:00 UTC "
        "(per `03_MICROSTRUCTURE.md` 3.2 — 13.4% / 1.74x London + 30.7% / 1.70x NY natural-density windows)",
        "- **Fill epsilon:** 2.0 pts (2 x 1.0 tick, mirroring NAS100/US30)",
        "- **Microstructure context:** 3.10% R-cost typ (best-tier per `03_MICROSTRUCTURE.md` 1.2)",
        "",
        "## Fleet stats (filled trades only)",
        "",
        "| Metric | Value | Pre-reg threshold | Status |",
        "|---|---:|---:|---|",
        f"| Raw CAND | {fleet_stats['raw_n']} | -- | -- |",
        f"| Unfilled | {fleet_stats['unfilled_n']} | -- | -- |",
        f"| Filled n | {fleet_stats['filled_n']} | >= 30 | "
        f"{'PASS' if fleet_stats['filled_n'] >= 30 else 'FAIL'} |",
        f"| WR | {fmt_pct(fleet_stats['wr_filled'])} "
        f"[CI {fmt_pct(fleet_stats['wr_ci'][0])}, {fmt_pct(fleet_stats['wr_ci'][1])}] | >= 55% | "
        f"{'PASS' if fleet_stats['wr_filled'] >= 0.55 else 'FAIL'} |",
        f"| Expectancy | {fmt_r(fleet_stats['exp_filled'])} "
        f"[CI {fmt_r(fleet_stats['exp_ci'][0])}, {fmt_r(fleet_stats['exp_ci'][1])}] | >= +0.10R | "
        f"{'PASS' if fleet_stats['exp_filled'] >= 0.10 else 'FAIL'} |",
        f"| Total R | {fleet_stats['total_r']:+.2f}R | -- | -- |",
        f"| MaxDD (chronological) | {fleet_stats['maxdd']:.2f}R | <= 8R | "
        f"{'PASS' if fleet_stats['maxdd'] <= 8.0 else 'FAIL'} |",
        f"| LONG share (raw CANDs) | {fmt_pct(fleet_stats['long_share'])} | -- | -- |",
        f"| SHORT share (raw CANDs) | {fmt_pct(fleet_stats['short_share'])} | -- | -- |",
        f"| LONG WR | {fmt_pct(fleet_stats['long_wr'])} "
        f"[CI {fmt_pct(fleet_stats['long_wr_ci'][0])}, {fmt_pct(fleet_stats['long_wr_ci'][1])}] "
        f"(n={fleet_stats['long_filled_n']}) | -- | -- |",
        f"| SHORT WR | {fmt_pct(fleet_stats['short_wr'])} "
        f"[CI {fmt_pct(fleet_stats['short_wr_ci'][0])}, {fmt_pct(fleet_stats['short_wr_ci'][1])}] "
        f"(n={fleet_stats['short_filled_n']}) | -- | -- |",
        f"| Total cost | ${total_cost:.2f} | <= $30 | "
        f"{'PASS' if total_cost <= 30 else 'FAIL'} |",
        "",
    ]

    # Per-slice
    lines.extend([
        "## Per-slice summary",
        "",
        "| Slice | Window | Raw | L/S | Filled | L/S | Wins | Total R | Cost |",
        "|---|---|---:|---|---:|---|---:|---:|---:|",
    ])
    for slice_name, s in agg["per_slice"].items():
        if s.get("skipped"):
            lines.append(f"| {slice_name} | SKIPPED | -- | -- | -- | -- | -- | -- | -- |")
            continue
        win_n = s["long_wins"] + s["short_wins"]
        lines.append(
            f"| {slice_name} | {s['start']} -> {s['end']} | {s['candidates']} | "
            f"{s['long_cands']}/{s['short_cands']} | {s['filled']} | "
            f"{s['long_filled']}/{s['short_filled']} | {win_n} | "
            f"{s['r_sum_filled']:+.2f} | ${s['cost']:.2f} |"
        )
    lines.append("")

    # Monthly trend
    lines.extend([
        "## Monthly trend (filled trades)",
        "",
        "| Month | n | Wins | Losses | WR | Exp R | Total R |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for m, d in monthly.items():
        lines.append(
            f"| {m} | {d['n']} | {d['wins']} | {d['losses']} | "
            f"{fmt_pct(d['wr'])} | {fmt_r(d['exp'])} | {d['total_r']:+.2f}R |"
        )
    lines.append("")

    # KZ breakdown
    lines.extend([
        "## Kill-zone breakdown (filled trades)",
        "",
        "| KZ | n | Wins | Losses | WR | Exp R | Total R |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for k, d in sorted(kz.items()):
        lines.append(
            f"| {k} | {d['n']} | {d['wins']} | {d['losses']} | "
            f"{fmt_pct(d['wr'])} | {fmt_r(d['exp'])} | {d['total_r']:+.2f}R |"
        )
    lines.append("")

    # Framework attribution
    if fw:
        lines.extend([
            "## Framework attribution (raw CANDs, best-effort grep of raw_response)",
            "",
            "| Framework | n |",
            "|---|---:|",
        ])
        for f, n in sorted(fw.items(), key=lambda kv: -kv[1]):
            lines.append(f"| {f} | {n} |")
        lines.append("")
        lines.append("> Note: simulator does not currently emit a `framework` field; counts from "
                     "string-grep over `raw_response`. Use as approximate ratios only.")
        lines.append("")

    # Pre-reg verdict
    crit = verdict_detail["promote_live"]["criteria"]
    rej = verdict_detail["reject_triggers"]
    lines.extend([
        "## Pre-registered criteria check",
        "",
        "### PROMOTE-LIVE",
        "",
        "| Criterion | Threshold | Observed | Status |",
        "|---|---:|---:|---|",
        f"| WR >= 55% | 0.55 | {fmt_pct(fleet_stats['wr_filled'])} | "
        f"{'PASS' if crit['wr_ge_55pct'] else 'FAIL'} |",
        f"| Exp R >= +0.10R | +0.100R | {fmt_r(fleet_stats['exp_filled'])} | "
        f"{'PASS' if crit['exp_ge_0.10R'] else 'FAIL'} |",
        f"| n >= 30 | 30 | {fleet_stats['filled_n']} | "
        f"{'PASS' if crit['n_ge_30'] else 'FAIL'} |",
        f"| MaxDD <= 8R | 8.0R | {fleet_stats['maxdd']:.2f}R | "
        f"{'PASS' if crit['maxdd_le_8R'] else 'FAIL'} |",
        "",
        "### REJECT triggers",
        "",
        f"- exp_le_0: {'TRIGGERED' if rej['exp_le_0'] else 'no'}",
        f"- n_lt_10: {'TRIGGERED' if rej['n_lt_10'] else 'no'}",
        f"- maxdd_gt_8R: {'TRIGGERED' if rej['maxdd_gt_8R'] else 'no'}",
        "",
        f"## VERDICT: **{verdict}**",
        "",
    ])

    if verdict == "PROMOTE-LIVE":
        lines.append("All 4 PROMOTE-LIVE criteria PASS. Recommend GER40 added to live fleet "
                     "with full 1% risk per trade after CEO sign-off and Monday config wiring.")
    elif verdict == "3-DAY-LIVE-OBSERVE":
        lines.append("3-day live observation window: place 1-2 small (0.25-0.50% risk) live trades "
                     "to confirm execution path + spread reality, then re-evaluate.")
    elif verdict == "OBSERVER-14D":
        lines.append("Insufficient sample for live promotion. Run as observer-only for 14+ days, "
                     "accumulate live CANDs into shadow log, then re-run this analysis.")
    else:
        fail_reasons = []
        if rej["exp_le_0"]:
            fail_reasons.append(f"Exp R={fmt_r(fleet_stats['exp_filled'])}<=0")
        if rej["n_lt_10"]:
            fail_reasons.append(f"n={fleet_stats['filled_n']}<10")
        if rej["maxdd_gt_8R"]:
            fail_reasons.append(f"MaxDD={fleet_stats['maxdd']:.2f}R>8R")
        lines.append(
            "REJECT: " + (", ".join(fail_reasons) if fail_reasons else "criteria not met") +
            ". Do NOT add GER40 to live fleet on this evidence."
        )

    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- **No live evaluation comparison:** GER40 has never been live-traded; "
                 "no `knowledge_base/live_evaluations/GER40/` exists. P2A-comparison columns "
                 "in per-slice JSON are all `N/A`.")
    lines.append("- **KZ choice:** Configured DAX-specific bimodal (London-late 10-12 + NY 14-19) "
                 "per microstructure 3.2 natural-density. An ALL-DAY KZ comparison was not run; "
                 "if PROMOTE-LIVE the KZ gets etched into config; if REJECT a future re-run with "
                 "ALL-DAY KZ may surface trades this filter masks.")
    lines.append("- **Provisional risk parameters:** equal_level_tolerance, fvg_min_gap, "
                 "sl_floor scaled proportionally from NAS100 (also index, similar microstructure). "
                 "Real broker tick size, contract size, max_spread should be MT5-verified before "
                 "any live trading.")
    lines.append("- **Spread not simulated:** Entry prices are AI-quoted, no spread added. "
                 "Microstructure 1.2 lists GER40 R-cost typ 3.10% (best-tier) so real-world drag "
                 "is small but not zero.")
    lines.append("- **2026 H2 decay risk:** XAUUSD shows monthly WR decay (Jan 45.5% -> Apr 10.0% per "
                 "CLAUDE.md 9). GER40 monthly trend should be cross-checked for the same pattern.")
    lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slice-dir", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-json", default=None)
    p.add_argument("--out-results", default=None,
                   help="If set, also write a combined all_results.json with every CAND row.")
    args = p.parse_args()

    script_hash = script_sha256(__file__)
    slices = load_slices(args.slice_dir)
    agg = aggregate(slices)
    fleet_stats = slice_stats(agg["fleet"]["cands"], agg["fleet"]["filled_cands"])
    monthly = monthly_breakdown(agg["fleet"]["filled_cands"])
    kz = kz_breakdown(agg["fleet"]["filled_cands"])
    fw = framework_attribution(agg["fleet"]["cands"])
    verdict, verdict_detail = apply_criteria(fleet_stats)

    md = render_md(
        agg, fleet_stats, monthly, kz, fw, verdict, verdict_detail,
        script_hash, agg["fleet"]["cost"],
    )
    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {args.out_md}")

    if args.out_json:
        out = {
            "script_sha256": script_hash,
            "verdict": verdict,
            "verdict_detail": verdict_detail,
            "total_cost": agg["fleet"]["cost"],
            "fleet_stats": {k: (list(v) if isinstance(v, tuple) else v)
                            for k, v in fleet_stats.items()},
            "monthly": monthly,
            "kz_breakdown": kz,
            "framework_attribution": fw,
            "per_slice": agg["per_slice"],
        }
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"Wrote {args.out_json}")

    if args.out_results:
        out = {
            "verdict": verdict,
            "total_cost": agg["fleet"]["cost"],
            "n_cands": len(agg["fleet"]["cands"]),
            "n_filled": len(agg["fleet"]["filled_cands"]),
            "rows": agg["fleet"]["all_rows"],
        }
        with open(args.out_results, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"Wrote {args.out_results}")

    print(f"VERDICT: {verdict}")
    print(f"Fleet: n={fleet_stats['filled_n']} WR={fmt_pct(fleet_stats['wr_filled'])} "
          f"Exp={fmt_r(fleet_stats['exp_filled'])} Total={fleet_stats['total_r']:+.2f}R "
          f"MaxDD={fleet_stats['maxdd']:.2f}R Cost=${agg['fleet']['cost']:.2f}")


if __name__ == "__main__":
    main()
