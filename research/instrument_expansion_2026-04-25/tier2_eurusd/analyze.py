"""Tier 2 EURUSD instrument expansion — backtest analysis.

Aggregates 12 slices' all_results.json under tier2_eurusd/ into:
  - REPORT.md      — human-readable verdict + month/slice tables
  - aggregate.json — fleet/per-month structured stats (script-readable)
  - all_results.json — concatenated slice records

Pre-registered acceptance gates (frozen by the orchestrator brief, NOT
post-hoc):
  - WR (filled) ≥ 55%
  - Exp R (filled) ≥ +0.10R
  - n (filled) ≥ 30
  - MaxDD ≤ 8R (chronological, peak-trough on cumulative R series)

Verdict ladder:
  - PROMOTE-LIVE      — all gates clear with margin
  - 3-DAY-LIVE-OBSERVE — all gates clear but n<50 OR Exp CI lower bound <0
  - OBSERVER-14D      — gate(s) borderline / sample-small
  - REJECT            — material gate fail (WR<50% OR Exp<0)
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
    """Max drawdown on cumulative R series. Inputs MUST be chronological."""
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


def load_slices(slice_root: Path) -> dict:
    slices = {}
    for child in sorted(slice_root.iterdir()):
        if not child.is_dir():
            continue
        if not child.name.startswith("s"):  # only slice dirs, skip _smoke etc.
            continue
        ar = child / "all_results.json"
        if not ar.exists():
            slices[child.name] = {"skipped": True, "reason": "no all_results.json"}
            continue
        with open(ar) as f:
            data = json.load(f)
        slices[child.name] = {
            "start": data.get("start"),
            "end": data.get("end"),
            "total_cost": data.get("total_cost", 0.0),
            "results": data.get("results", []),
        }
    return slices


def aggregate(slices: dict) -> dict:
    out = {
        "per_slice": {},
        "fleet": {"cands": [], "filled_cands": [], "cost": 0.0},
    }
    for slice_name, s in slices.items():
        if s.get("skipped"):
            out["per_slice"][slice_name] = {"skipped": True, "reason": s.get("reason")}
            continue
        cands = []
        filled = []
        evaluations = 0
        no_trades = 0
        l2_rej = 0
        prescreen_skips = 0
        framework_counter: Counter[str] = Counter()
        for r in s["results"]:
            if r.get("decision") == "CANDIDATE":
                cands.append(r)
                fw = r.get("framework", "unknown")
                framework_counter[fw] += 1
                if r.get("outcome") in ("WIN", "LOSS", "BREAKEVEN"):
                    filled.append(r)
            elif r.get("decision") == "NO_TRADE":
                no_trades += 1
                reason = r.get("no_trade_reason", "")
                if reason.startswith("L2_"):
                    l2_rej += 1
                if reason.startswith("prescreen") or "prescreen" in reason:
                    prescreen_skips += 1
            if r.get("cost", 0) > 0:
                evaluations += 1
        out["per_slice"][slice_name] = {
            "start": s["start"],
            "end": s["end"],
            "cost": s["total_cost"],
            "evaluations": evaluations,
            "candidates": len(cands),
            "filled": len(filled),
            "no_trades": no_trades,
            "l2_rej": l2_rej,
            "prescreen_skips": prescreen_skips,
            "long_cands": sum(1 for r in cands if r.get("direction") == "LONG"),
            "short_cands": sum(1 for r in cands if r.get("direction") == "SHORT"),
            "long_filled": sum(1 for r in filled if r.get("direction") == "LONG"),
            "short_filled": sum(1 for r in filled if r.get("direction") == "SHORT"),
            "long_wins": sum(1 for r in filled if r.get("direction") == "LONG" and r.get("outcome") == "WIN"),
            "short_wins": sum(1 for r in filled if r.get("direction") == "SHORT" and r.get("outcome") == "WIN"),
            "r_sum_filled": sum(r.get("r_multiple", 0.0) for r in filled),
            "frameworks": dict(framework_counter),
        }
        out["fleet"]["cands"].extend(cands)
        out["fleet"]["filled_cands"].extend(filled)
        out["fleet"]["cost"] += s["total_cost"]
    return out


def fleet_stats(cands: list, filled: list) -> dict:
    if not cands:
        return {
            "raw_n": 0, "filled_n": 0, "long_share": 0.0, "short_share": 0.0,
            "long_filled_n": 0, "short_filled_n": 0,
            "wr_filled": 0.0, "wr_ci": (0.0, 0.0),
            "exp_filled": 0.0, "exp_ci": (0.0, 0.0),
            "long_wr": 0.0, "long_wr_ci": (0.0, 0.0),
            "short_wr": 0.0, "short_wr_ci": (0.0, 0.0),
            "total_r": 0.0, "maxdd": 0.0, "framework_share": {},
        }
    long_cands = [r for r in cands if r.get("direction") == "LONG"]
    short_cands = [r for r in cands if r.get("direction") == "SHORT"]
    long_filled = [r for r in filled if r.get("direction") == "LONG"]
    short_filled = [r for r in filled if r.get("direction") == "SHORT"]
    long_wins = sum(1 for r in long_filled if r.get("outcome") == "WIN")
    short_wins = sum(1 for r in short_filled if r.get("outcome") == "WIN")
    all_wins = sum(1 for r in filled if r.get("outcome") == "WIN")
    # Chronological ordering for MaxDD (candle_time is ISO 8601 → lexical OK)
    filled_chrono = sorted(filled, key=lambda r: r.get("candle_time", ""))
    r_series = [r.get("r_multiple", 0.0) for r in filled_chrono]
    fw_count: Counter[str] = Counter(r.get("framework", "unknown") for r in cands)
    fw_share = {fw: c / len(cands) for fw, c in fw_count.items()}
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
        "framework_share": fw_share,
    }


def per_month_breakdown(filled: list) -> dict:
    """Group filled CANDs by year-month using candle_time."""
    by_month: dict[str, list] = defaultdict(list)
    for r in filled:
        ct = r.get("candle_time", "")
        if len(ct) < 7:
            continue
        ym = ct[:7]  # 'YYYY-MM'
        by_month[ym].append(r)
    out = {}
    for ym, rows in sorted(by_month.items()):
        wins = sum(1 for r in rows if r.get("outcome") == "WIN")
        r_series = [r.get("r_multiple", 0.0) for r in rows]
        out[ym] = {
            "n": len(rows),
            "wins": wins,
            "wr": wins / len(rows) if rows else 0.0,
            "wr_ci": wilson_ci(wins, len(rows)),
            "exp": sum(r_series) / len(r_series) if r_series else 0.0,
            "total_r": sum(r_series),
            "long_n": sum(1 for r in rows if r.get("direction") == "LONG"),
            "short_n": sum(1 for r in rows if r.get("direction") == "SHORT"),
        }
    return out


def apply_criteria(stats: dict) -> tuple[str, dict]:
    """Apply pre-registered EURUSD acceptance gates.

    Gates (per orchestrator brief):
      - WR ≥ 55%          (vs decay-baseline 60.7% — allow 5.7pp regression)
      - Exp R ≥ +0.10R    (live profitability floor at 1% risk)
      - n ≥ 30            (avoid sub-significant claims)
      - MaxDD ≤ 8R        (1% × 8R = 8% account DD; FTMO 10% ceiling)
    """
    wr_ok = stats["wr_filled"] >= 0.55
    exp_ok = stats["exp_filled"] >= 0.10
    n_ok = stats["filled_n"] >= 30
    dd_ok = stats["maxdd"] <= 8.0

    crit = {
        "wr_ge_55pct": wr_ok,
        "exp_ge_0.10R": exp_ok,
        "n_ge_30": n_ok,
        "maxdd_le_8R": dd_ok,
    }

    # REJECT triggers
    reject_hard = (stats["wr_filled"] < 0.50) or (stats["exp_filled"] < 0.0)

    # Verdict ladder
    if reject_hard:
        verdict = "REJECT"
        reason = "Material gate fail (WR<50% or Exp<0)"
    elif wr_ok and exp_ok and n_ok and dd_ok:
        # All gates pass → PROMOTE-LIVE unless small sample / borderline CI
        if stats["filled_n"] >= 50 and stats["exp_ci"][0] > 0:
            verdict = "PROMOTE-LIVE"
            reason = "All gates clear with sample-size and CI margin"
        else:
            verdict = "3-DAY-LIVE-OBSERVE"
            reason = f"Gates clear but n={stats['filled_n']} or Exp CI lower bound {stats['exp_ci'][0]:+.3f} non-strict"
    else:
        verdict = "OBSERVER-14D"
        fails = [k for k, v in crit.items() if not v]
        reason = f"Borderline gate fail(s): {', '.join(fails)}"

    return verdict, {"criteria": crit, "reason": reason, "reject_hard": reject_hard}


def fmt_pct(x: float) -> str:
    return f"{x*100:.1f}%"


def fmt_r(x: float) -> str:
    return f"{x:+.3f}R"


def render_md(agg: dict, fleet: dict, by_month: dict, verdict: str,
              verdict_detail: dict, script_hash: str) -> str:
    lines = [
        "# Tier 2 EURUSD Instrument Expansion — Backtest Report",
        "",
        f"**Analysis script SHA256:** `{script_hash}`",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Pre-registered criteria:** WR ≥ 55%, Exp R ≥ +0.10R, n ≥ 30, MaxDD ≤ 8R (frozen by orchestrator brief).",
        "",
        "## Inputs",
        "",
        f"- 12 weekly slices, Jan 2 → Apr 13 2026 (full available range).",
        f"- Detector: `v2` (production HEAD `d614c54`).",
        f"- KZ: London 07:00-12:00 UTC + NY 13:00-15:30 UTC.",
        f"- Cost: ${agg['fleet']['cost']:.2f}",
        f"- Raw CANDs: {len(agg['fleet']['cands'])}",
        f"- Filled: {len(agg['fleet']['filled_cands'])}",
        "",
        "## Fleet stats",
        "",
        "| Metric | Value | 95% CI / note |",
        "|---|---:|---|",
        f"| Raw CAND | {fleet['raw_n']} | LONG {fmt_pct(fleet['long_share'])} / SHORT {fmt_pct(fleet['short_share'])} |",
        f"| Filled | {fleet['filled_n']} | LONG {fleet['long_filled_n']} / SHORT {fleet['short_filled_n']} |",
        f"| WR (filled) | {fmt_pct(fleet['wr_filled'])} | Wilson CI [{fmt_pct(fleet['wr_ci'][0])}, {fmt_pct(fleet['wr_ci'][1])}] |",
        f"| Expectancy | {fmt_r(fleet['exp_filled'])} | Bootstrap CI [{fmt_r(fleet['exp_ci'][0])}, {fmt_r(fleet['exp_ci'][1])}] |",
        f"| Total R | {fleet['total_r']:+.2f}R | |",
        f"| MaxDD | {fleet['maxdd']:.2f}R | chronological |",
        f"| LONG WR | {fmt_pct(fleet['long_wr'])} | n={fleet['long_filled_n']}, CI [{fmt_pct(fleet['long_wr_ci'][0])}, {fmt_pct(fleet['long_wr_ci'][1])}] |",
        f"| SHORT WR | {fmt_pct(fleet['short_wr'])} | n={fleet['short_filled_n']}, CI [{fmt_pct(fleet['short_wr_ci'][0])}, {fmt_pct(fleet['short_wr_ci'][1])}] |",
        "",
        "## Framework attribution (raw CANDs)",
        "",
        "| Framework | Share |",
        "|---|---:|",
    ]
    for fw, share in sorted(fleet["framework_share"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {fw} | {fmt_pct(share)} |")
    lines.append("")

    # Per-month
    lines.extend([
        "## Per-month trajectory (filled trades)",
        "",
        "_Tests decay-agent's `IMPROVING` signal: should see WR / Exp R rise across Jan→Apr._",
        "",
        "| Month | n | wins | WR | WR CI | Exp R | Total R | L/S |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ])
    for ym, m in sorted(by_month.items()):
        lines.append(
            f"| {ym} | {m['n']} | {m['wins']} | {fmt_pct(m['wr'])} | "
            f"[{fmt_pct(m['wr_ci'][0])}, {fmt_pct(m['wr_ci'][1])}] | "
            f"{fmt_r(m['exp'])} | {m['total_r']:+.2f}R | {m['long_n']}/{m['short_n']} |"
        )
    lines.append("")

    # Per-slice
    lines.extend([
        "## Per-slice summary",
        "",
        "| Slice | Range | Raw | L/S | Filled | L/S | Wins | Total R | Cost |",
        "|---|---|---:|---|---:|---|---:|---:|---:|",
    ])
    for slice_name, s in sorted(agg["per_slice"].items()):
        if s.get("skipped"):
            lines.append(f"| {slice_name} | SKIPPED | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {slice_name} | {s['start']}→{s['end']} | {s['candidates']} | "
            f"{s['long_cands']}/{s['short_cands']} | "
            f"{s['filled']} | {s['long_filled']}/{s['short_filled']} | "
            f"{s['long_wins'] + s['short_wins']} | {s['r_sum_filled']:+.2f} | ${s['cost']:.2f} |"
        )
    lines.append("")

    # Pre-reg criteria
    crit = verdict_detail["criteria"]
    lines.extend([
        "## Pre-registered acceptance gates",
        "",
        "| Gate | Threshold | Observed | Status |",
        "|---|---:|---:|---|",
        f"| WR (filled) | ≥ 55% | {fmt_pct(fleet['wr_filled'])} | {'PASS' if crit['wr_ge_55pct'] else 'FAIL'} |",
        f"| Expectancy | ≥ +0.10R | {fmt_r(fleet['exp_filled'])} | {'PASS' if crit['exp_ge_0.10R'] else 'FAIL'} |",
        f"| Sample size | ≥ 30 filled | {fleet['filled_n']} | {'PASS' if crit['n_ge_30'] else 'FAIL'} |",
        f"| MaxDD | ≤ 8R | {fleet['maxdd']:.2f}R | {'PASS' if crit['maxdd_le_8R'] else 'FAIL'} |",
        "",
        f"## VERDICT: **{verdict}**",
        "",
        f"_{verdict_detail['reason']}_",
        "",
    ])

    # Cross-reference to decay agent
    lines.extend([
        "## Cross-reference: Tier 1 decay-agent finding",
        "",
        "Decay agent classified EURUSD as **STABLE+ / IMPROVING** "
        "(CV 0.047, mean WR 60.7%, Δ +5.5pp Jan→Apr trajectory) on the "
        "mechanical 168-bar H1 BOS-retest proxy. This backtest evaluates the "
        "same period under the **AI-filtered + framework-gated production "
        "pipeline** (v2 detector, 3-framework set, AI Sonnet 4.6 effort=max). "
        "Per-month WR trajectory above is the direct test of the IMPROVING "
        "claim under live-faithful conditions.",
        "",
    ])

    # Caveats
    lines.extend([
        "## Caveats",
        "",
        "- **No spread simulation:** Entry prices are AI-quoted; real EURUSD spreads add ~0.1-0.3 pip slippage per trade.",
        "- **SL-first on wide candles:** If both SL and TP hit in one M15 candle, SL wins (conservative bias).",
        "- **No tick data:** Outcome from M15 OHLC only.",
        "- **KB context absent:** Production passes last-10-trade memory; sim does not.",
        "- **No live correlation gate / concurrent-cap:** Sim evaluates each candle independently; "
        "live system would suppress some EURUSD trades when GBPUSD/US30 already filled.",
        "- **Pre-AI gates (h1_poi, multi_framework) ARE applied** — sim mirrors orchestrator prescreen.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slice-root", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-allresults", required=True)
    args = p.parse_args()

    script_hash = script_sha256(__file__)
    slice_root = Path(args.slice_root)
    slices = load_slices(slice_root)
    agg = aggregate(slices)

    fleet = fleet_stats(agg["fleet"]["cands"], agg["fleet"]["filled_cands"])
    by_month = per_month_breakdown(agg["fleet"]["filled_cands"])
    verdict, verdict_detail = apply_criteria(fleet)

    md = render_md(agg, fleet, by_month, verdict, verdict_detail, script_hash)
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(md)

    out_json = {
        "script_sha256": script_hash,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "fleet": {k: (list(v) if isinstance(v, tuple) else v) for k, v in fleet.items()},
        "per_month": by_month,
        "per_slice": agg["per_slice"],
        "total_cost": agg["fleet"]["cost"],
    }
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2, default=str)

    # Concatenated all_results across slices, with slice tag
    all_results: list[dict] = []
    for slice_name, s in slices.items():
        if s.get("skipped"):
            continue
        for r in s["results"]:
            rr = dict(r)
            rr["_slice"] = slice_name
            all_results.append(rr)
    with open(args.out_allresults, "w", encoding="utf-8") as f:
        json.dump({
            "symbol": "EURUSD",
            "slices": list(slices.keys()),
            "n_records": len(all_results),
            "results": all_results,
        }, f, indent=2)

    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_allresults}")
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
