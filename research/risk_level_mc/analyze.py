#!/usr/bin/env python3
"""Build pivot tables + recommendation from risk_mc_results.json."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from collections import defaultdict

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

OUT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = OUT_DIR / "risk_mc_results.json"

# CEO weighted-WR scenario reflecting genuine uncertainty
WR_WEIGHTS = {
    0.62: 0.30,  # validated backtest baseline (CLAUDE.md, n=129 XAUUSD)
    0.55: 0.30,  # mid-case (combined dedup ~50%, plus mild positive bias toward backtest)
    0.50: 0.25,  # near-breakeven (A1+A2 dedup 49.5% n=93; A2 v2-active n=30 53%)
    0.45: 0.15,  # bear case: H2 2026 24% n=25 weighted; April 10% n=10
}


def build_matrix(rows, metric, wr_levels, risk_levels, lam_filter,
                 fmt_fn, missing="n/a"):
    grid = defaultdict(dict)
    for r in rows:
        if lam_filter is not None and r["lambda_per_day"] != lam_filter:
            continue
        grid[r["risk_pct"]][r["wr"]] = r
    header = "| risk \\ WR |" + "".join(f" {wr*100:.0f}% |" for wr in wr_levels)
    sep = "|---|" + "---|" * len(wr_levels)
    lines = [header, sep]
    for risk in risk_levels:
        row = [f"| **{risk:.2f}%** |"]
        for wr in wr_levels:
            r = grid[risk].get(wr)
            row.append((missing if r is None else fmt_fn(r[metric])) + " |")
        lines.append("".join(row))
    return "\n".join(lines)


def build_3d(rows, metric, wr_levels, risk_levels, lam_levels, fmt_fn):
    blocks = []
    for lam in lam_levels:
        blocks.append(f"\n### lambda = {lam} fleet trades/day\n")
        blocks.append(build_matrix(rows, metric, wr_levels, risk_levels, lam, fmt_fn))
    return "\n".join(blocks)


def main():
    rows = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    risks = sorted(set(r["risk_pct"] for r in rows))
    wrs_desc = sorted(set(r["wr"] for r in rows), reverse=True)
    wrs_asc = sorted(set(r["wr"] for r in rows))
    lams = sorted(set(r["lambda_per_day"] for r in rows))
    central_lam = 1.0

    fmt_days = lambda x: ">60d  " if x == float("inf") else f"{x:>5.1f}d"
    fmt_pct = lambda x: f"{x*100:>5.2f}%"
    fmt_pct3 = lambda x: f"{x*100:>6.3f}%"
    fmt_signed = lambda x: f"{x:+6.2f}%"
    fmt_idle = lambda x: f"{x:>5.2f}d"

    table_s1 = build_matrix(rows, "median_days_to_step1", wrs_desc, risks, central_lam, fmt_days)
    table_s2 = build_matrix(rows, "median_days_to_step2", wrs_desc, risks, central_lam, fmt_days)
    table_s1_p90 = build_matrix(rows, "p90_days_to_step1", wrs_desc, risks, central_lam, fmt_days)
    table_dd = build_matrix(rows, "p_max_dd_gt_10pct", wrs_desc, risks, central_lam, fmt_pct)
    table_daily5 = build_matrix(rows, "p_daily_loss_gt_5pct", wrs_desc, risks, central_lam, fmt_pct3)
    table_daily4 = build_matrix(rows, "p_daily_loss_gt_4pct", wrs_desc, risks, central_lam, fmt_pct3)
    table_mtm_idle = build_matrix(rows, "expected_mtm_stop_days_per_year", wrs_desc, risks, central_lam, fmt_idle)
    table_p_s1_60d = build_matrix(rows, "p_step1_within_60d", wrs_desc, risks, central_lam, fmt_pct)
    table_p_s2_60d = build_matrix(rows, "p_step2_within_60d", wrs_desc, risks, central_lam, fmt_pct)
    table_monthly_3d = build_3d(rows, "monthly_return_pct", wrs_desc, risks, lams, fmt_signed)

    # Weighted scenario eval
    weighted = {}
    for risk in risks:
        for lam in lams:
            entry = {"risk_pct": risk, "lambda_per_day": lam}
            w_monthly = w_dd10 = w_d5 = w_d4 = w_s1 = w_s2 = w_med_s1 = w_med_s2 = 0.0
            cw = 0.0
            for wr, weight in WR_WEIGHTS.items():
                r = next((x for x in rows if x["risk_pct"] == risk
                         and x["wr"] == wr and x["lambda_per_day"] == lam), None)
                if r is None:
                    continue
                w_monthly += weight * r["monthly_return_pct"]
                w_dd10 += weight * r["p_max_dd_gt_10pct"]
                w_d5 += weight * r["p_daily_loss_gt_5pct"]
                w_d4 += weight * r["p_daily_loss_gt_4pct"]
                w_s1 += weight * r["p_step1_within_60d"]
                w_s2 += weight * r["p_step2_within_60d"]
                ms1 = r["median_days_to_step1"] if r["median_days_to_step1"] != float("inf") else 90.0
                ms2 = r["median_days_to_step2"] if r["median_days_to_step2"] != float("inf") else 90.0
                w_med_s1 += weight * ms1
                w_med_s2 += weight * ms2
                cw += weight
            entry["w_monthly_pct"] = w_monthly
            entry["w_p_dd10"] = w_dd10
            entry["w_p_d5"] = w_d5
            entry["w_p_d4"] = w_d4
            entry["w_p_s1_60d"] = w_s1
            entry["w_p_s2_60d"] = w_s2
            entry["w_med_s1_cap90"] = w_med_s1 / cw if cw else float("inf")
            entry["w_med_s2_cap90"] = w_med_s2 / cw if cw else float("inf")
            weighted[(risk, lam)] = entry

    # Recommendation: constraints
    print("=" * 80, flush=True)
    print("WEIGHTED SCENARIO ANALYSIS (CEO WR weights: 62=30, 55=30, 50=25, 45=15)", flush=True)
    print(f"Constraints: P(DD>10%) <= 0.05, P(daily>5%) <= 0.01", flush=True)
    print("=" * 80, flush=True)
    print("Risk |  E[mo] | P(DD>10) | P(d>5)  | P(d>4)  | P(S1<60d) | med(S1)d | E[S2<60d] | DD-pass | D5-pass", flush=True)
    candidates = []
    for risk in risks:
        e = weighted[(risk, central_lam)]
        passes_dd = e["w_p_dd10"] <= 0.05
        passes_daily = e["w_p_d5"] <= 0.01
        candidates.append({
            "risk_pct": risk, "passes_dd": passes_dd, "passes_d5": passes_daily,
            "passes_constraints": passes_dd and passes_daily,
            **e
        })
        print(
            f"{risk:.2f}%| {e['w_monthly_pct']:+6.2f}% |  {e['w_p_dd10']*100:6.2f}% | "
            f"{e['w_p_d5']*100:5.3f}% | {e['w_p_d4']*100:5.3f}% |  {e['w_p_s1_60d']*100:5.2f}%  | "
            f"{e['w_med_s1_cap90']:6.1f}  |   {e['w_p_s2_60d']*100:5.2f}%   |   {('Y' if passes_dd else 'N')}    |   {('Y' if passes_daily else 'N')}",
            flush=True
        )

    qualified = [c for c in candidates if c["passes_constraints"]]
    if qualified:
        chosen = max(qualified, key=lambda c: (c["w_p_s1_60d"], -c["w_med_s1_cap90"]))
        method = "constraint-pass-max-s1"
    else:
        chosen = max(candidates, key=lambda c: c["w_p_s1_60d"] - 5.0 * c["w_p_dd10"])
        method = "no-pass-fallback"

    rec_risk = chosen["risk_pct"]
    print(f"\nCHOSEN: risk={rec_risk}% (method: {method})", flush=True)

    # Per-WR breakdown at chosen
    print(f"\nPer-WR breakdown @ risk={rec_risk}%, lambda=1.0:", flush=True)
    for wr in wrs_desc:
        r = next((x for x in rows if x["risk_pct"] == rec_risk
                 and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        ms1 = r["median_days_to_step1"]
        ms1_str = ">60d" if ms1 == float("inf") else f"{ms1:.1f}d"
        print(
            f"  WR={wr*100:.0f}% | E[mo]={r['monthly_return_pct']:+6.2f}% | "
            f"P(DD>10)={r['p_max_dd_gt_10pct']*100:5.2f}% | "
            f"P(daily>5)={r['p_daily_loss_gt_5pct']*100:5.3f}% | "
            f"P(S1<60d)={r['p_step1_within_60d']*100:5.2f}% | "
            f"med(S1)={ms1_str}",
            flush=True
        )

    # WR threshold below which to revert to 1.0%
    # Smallest WR where chosen still passes both constraints
    wr_threshold = None
    for wr in wrs_asc:
        r = next((x for x in rows if x["risk_pct"] == rec_risk
                 and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        if r is None:
            continue
        if r["p_max_dd_gt_10pct"] <= 0.05 and r["p_daily_loss_gt_5pct"] <= 0.01:
            wr_threshold = wr
            break

    baseline = next(c for c in candidates if c["risk_pct"] == 1.0)

    rec = {
        "recommended_risk_pct": rec_risk,
        "method": method,
        "wr_weights_used": WR_WEIGHTS,
        "constraints": {"p_max_dd_gt_10pct_max": 0.05, "p_daily_loss_gt_5pct_max": 0.01},
        "chosen_metrics": {
            "weighted_monthly_return_pct": chosen["w_monthly_pct"],
            "weighted_p_max_dd_gt_10pct": chosen["w_p_dd10"],
            "weighted_p_daily_loss_gt_5pct": chosen["w_p_d5"],
            "weighted_p_daily_loss_gt_4pct": chosen["w_p_d4"],
            "weighted_p_step1_within_60d": chosen["w_p_s1_60d"],
            "weighted_p_step2_within_60d": chosen["w_p_s2_60d"],
            "weighted_median_days_to_step1_capped90": chosen["w_med_s1_cap90"],
            "weighted_median_days_to_step2_capped90": chosen["w_med_s2_cap90"],
        },
        "baseline_1pct_metrics": {
            "weighted_monthly_return_pct": baseline["w_monthly_pct"],
            "weighted_p_max_dd_gt_10pct": baseline["w_p_dd10"],
            "weighted_p_daily_loss_gt_5pct": baseline["w_p_d5"],
            "weighted_p_step1_within_60d": baseline["w_p_s1_60d"],
            "weighted_median_days_to_step1_capped90": baseline["w_med_s1_cap90"],
        },
        "wr_threshold_below_which_revert_to_1pct": wr_threshold,
        "all_risk_candidates_lam_1.0": candidates,
    }
    rec_path = OUT_DIR / "recommendation.json"
    rec_path.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    print(f"\n[ok] wrote {rec_path}", flush=True)

    tables_path = OUT_DIR / "matrices.md"
    tables_path.write_text(
        "# MC Result Matrices (lambda=1.0 central case)\n\n"
        "## Median Days to Step 1 (10% target)\n\n"
        + table_s1 + "\n\n"
        "## Median Days to Step 2 (5% target)\n\n"
        + table_s2 + "\n\n"
        "## p90 Days to Step 1 (10% target)\n\n"
        + table_s1_p90 + "\n\n"
        "## P(MaxDD > 10% in single year)\n\n"
        + table_dd + "\n\n"
        "## P(any single day loss > 5%)\n\n"
        + table_daily5 + "\n\n"
        "## P(any single day loss > 4% triggers MTM)\n\n"
        + table_daily4 + "\n\n"
        "## Expected MTM-stop days/year (idle days)\n\n"
        + table_mtm_idle + "\n\n"
        "## P(Step 1 hit within 60 days)\n\n"
        + table_p_s1_60d + "\n\n"
        "## P(Step 2 hit within 60 days)\n\n"
        + table_p_s2_60d + "\n\n"
        "## Monthly Return — risk x WR x lambda (3 lambdas)\n"
        + table_monthly_3d + "\n",
        encoding="utf-8"
    )
    print(f"[ok] wrote {tables_path}", flush=True)


if __name__ == "__main__":
    main()
