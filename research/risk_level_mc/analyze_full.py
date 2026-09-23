#!/usr/bin/env python3
"""Final analysis: combines annual MC + challenge-horizon MC into the
recommendation with weighted-WR scenario weighting."""

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

# CEO weighted-WR scenario reflecting genuine uncertainty
WR_WEIGHTS = {
    0.62: 0.30,  # validated backtest baseline (CLAUDE.md, n=129 XAUUSD)
    0.55: 0.30,  # mid-case (combined dedup ~50%, slight positive bias)
    0.50: 0.25,  # near-breakeven (A1+A2 dedup 49.5% n=93; A2 v2-active n=30 53%)
    0.45: 0.15,  # bear case: H2 2026 24% n=25; April 10% n=10
}


def fmt_days(x):
    return ">60d  " if x == float("inf") else f"{x:>5.1f}d"


def fmt_pct(x):
    return f"{x*100:>5.2f}%"


def fmt_pct3(x):
    return f"{x*100:>6.3f}%"


def fmt_signed(x):
    return f"{x:+6.2f}%"


def fmt_idle(x):
    return f"{x:>5.2f}d"


def build_matrix(rows, metric, wr_levels, risk_levels, lam_filter, fmt_fn,
                 missing="n/a"):
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
    annual = json.loads((OUT_DIR / "risk_mc_results.json").read_text(encoding="utf-8"))
    challenge = json.loads((OUT_DIR / "risk_mc_challenge.json").read_text(encoding="utf-8"))

    risks = sorted(set(r["risk_pct"] for r in annual))
    wrs_desc = sorted(set(r["wr"] for r in annual), reverse=True)
    wrs_asc = sorted(set(r["wr"] for r in annual))
    lams = sorted(set(r["lambda_per_day"] for r in annual))
    central_lam = 1.0

    # Build matrices
    matrices = {
        "median_days_to_step1_annual": build_matrix(annual, "median_days_to_step1", wrs_desc, risks, central_lam, fmt_days),
        "median_days_to_step2_annual": build_matrix(annual, "median_days_to_step2", wrs_desc, risks, central_lam, fmt_days),
        "p_max_dd_gt_10pct_annual": build_matrix(annual, "p_max_dd_gt_10pct", wrs_desc, risks, central_lam, fmt_pct),
        "p_daily_loss_gt_5pct": build_matrix(annual, "p_daily_loss_gt_5pct", wrs_desc, risks, central_lam, fmt_pct3),
        "p_daily_loss_gt_4pct": build_matrix(annual, "p_daily_loss_gt_4pct", wrs_desc, risks, central_lam, fmt_pct3),
        "expected_mtm_idle_days_annual": build_matrix(annual, "expected_mtm_stop_days_per_year", wrs_desc, risks, central_lam, fmt_idle),
        "p_pass_step1_60d": build_matrix(challenge, "p_pass_s1", wrs_desc, risks, central_lam, fmt_pct),
        "p_bust_dd_60d": build_matrix(challenge, "p_bust_dd", wrs_desc, risks, central_lam, fmt_pct),
        "median_days_to_pass_60d": build_matrix(challenge, "median_days_to_pass", wrs_desc, risks, central_lam, fmt_days),
        "monthly_return_3d": build_3d(annual, "monthly_return_pct", wrs_desc, risks, lams, fmt_signed),
        "p_pass_60d_3d": build_3d(challenge, "p_pass_s1", wrs_desc, risks, lams, fmt_pct),
        "p_bust_dd_60d_3d": build_3d(challenge, "p_bust_dd", wrs_desc, risks, lams, fmt_pct),
    }

    # Compute weighted scenario evaluation (challenge + annual joined)
    weighted = {}
    for risk in risks:
        for lam in lams:
            entry = {"risk_pct": risk, "lambda_per_day": lam}
            w_monthly = w_dd_ann = w_d5 = w_d4 = w_pass = w_bust = w_to = w_med_pass = 0.0
            cw = 0.0
            for wr, weight in WR_WEIGHTS.items():
                ann = next((x for x in annual if x["risk_pct"] == risk and x["wr"] == wr and x["lambda_per_day"] == lam), None)
                ch = next((x for x in challenge if x["risk_pct"] == risk and x["wr"] == wr and x["lambda_per_day"] == lam), None)
                if ann is None or ch is None:
                    continue
                w_monthly += weight * ann["monthly_return_pct"]
                w_dd_ann += weight * ann["p_max_dd_gt_10pct"]
                w_d5 += weight * ann["p_daily_loss_gt_5pct"]
                w_d4 += weight * ann["p_daily_loss_gt_4pct"]
                w_pass += weight * ch["p_pass_s1"]
                w_bust += weight * ch["p_bust_dd"]
                w_to += weight * ch["p_timeout"]
                mp = ch["median_days_to_pass"] if ch["median_days_to_pass"] != float("inf") else 75.0
                w_med_pass += weight * mp
                cw += weight
            entry["w_monthly_pct"] = w_monthly
            entry["w_p_dd10_annual"] = w_dd_ann
            entry["w_p_d5"] = w_d5
            entry["w_p_d4"] = w_d4
            entry["w_p_pass_60d"] = w_pass
            entry["w_p_bust_dd_60d"] = w_bust
            entry["w_p_timeout_60d"] = w_to
            entry["w_med_days_to_pass_cap75"] = w_med_pass / cw if cw else float("inf")
            weighted[(risk, lam)] = entry

    # Decision rule (challenge-horizon)
    # Constraint A: weighted P(bust by DD over 60d) <= 5%
    # Constraint B: weighted P(daily>5%) <= 1% (annual proxy; conservative)
    # Maximize: weighted P(pass S1 within 60d), tiebreak on lower median_days_to_pass

    print("=" * 90, flush=True)
    print("FINAL ANALYSIS — challenge-horizon (60d) + annual MC, weighted WR scenario", flush=True)
    print(f"WR weights: {WR_WEIGHTS}", flush=True)
    print("Constraints: P(60d bust by DD) <= 5%, P(any daily > 5%) <= 1%", flush=True)
    print("=" * 90, flush=True)
    print("Risk |  E[mo] | P(bust 60d) | P(daily>5)| P(d>4) | P(PASS 60d) | med(pass) | DD-pass | D5-pass", flush=True)
    candidates = []
    for risk in risks:
        e = weighted[(risk, central_lam)]
        passes_dd = e["w_p_bust_dd_60d"] <= 0.05
        passes_d5 = e["w_p_d5"] <= 0.01
        candidates.append({
            "risk_pct": risk, "passes_dd": passes_dd, "passes_d5": passes_d5,
            "passes_constraints": passes_dd and passes_d5,
            **e
        })
        print(
            f"{risk:.2f}%| {e['w_monthly_pct']:+6.2f}% |   {e['w_p_bust_dd_60d']*100:5.2f}%   | "
            f"{e['w_p_d5']*100:5.3f}% | {e['w_p_d4']*100:5.3f}% |  {e['w_p_pass_60d']*100:5.2f}%   | "
            f"{e['w_med_days_to_pass_cap75']:6.1f}d   |   {('Y' if passes_dd else 'N')}    |   {('Y' if passes_d5 else 'N')}",
            flush=True
        )

    qualified = [c for c in candidates if c["passes_constraints"]]
    if qualified:
        chosen = max(qualified, key=lambda c: (c["w_p_pass_60d"], -c["w_med_days_to_pass_cap75"]))
        method = "constraint-pass-max-pass60d"
    else:
        chosen = max(candidates, key=lambda c: c["w_p_pass_60d"] - 5.0 * c["w_p_bust_dd_60d"])
        method = "no-pass-fallback"

    rec_risk = chosen["risk_pct"]
    print(f"\n>> CHOSEN: risk={rec_risk}% (method: {method})", flush=True)

    print(f"\nPer-WR breakdown @ risk={rec_risk}%, lambda=1.0 (challenge MC):", flush=True)
    for wr in wrs_desc:
        ann = next((x for x in annual if x["risk_pct"] == rec_risk and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        ch = next((x for x in challenge if x["risk_pct"] == rec_risk and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        med_p_str = f"{ch['median_days_to_pass']:.1f}d" if ch["median_days_to_pass"] != float("inf") else ">60d"
        print(
            f"  WR={wr*100:.0f}% | E[mo]={ann['monthly_return_pct']:+6.2f}% | "
            f"P(60d PASS)={ch['p_pass_s1']*100:5.2f}% | "
            f"P(60d bust DD)={ch['p_bust_dd']*100:5.2f}% | "
            f"P(daily>5)={ann['p_daily_loss_gt_5pct']*100:5.3f}% | "
            f"med(pass)={med_p_str}",
            flush=True
        )

    # WR threshold below which constraint-set fails at chosen risk
    wr_threshold_breakeven = None
    for wr in wrs_asc:
        ch = next((x for x in challenge if x["risk_pct"] == rec_risk and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        ann = next((x for x in annual if x["risk_pct"] == rec_risk and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        if ch is None or ann is None:
            continue
        if ch["p_bust_dd"] <= 0.05 and ann["p_daily_loss_gt_5pct"] <= 0.01:
            wr_threshold_breakeven = wr
            break

    # Threshold for reverting to 1%: if WR drops to where chosen's bust > 10% OR
    # 1% would deliver more pass-prob safely
    revert_threshold = None
    for wr in wrs_asc:
        ch_chosen = next((x for x in challenge if x["risk_pct"] == rec_risk and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        ch_1pct = next((x for x in challenge if x["risk_pct"] == 1.0 and x["wr"] == wr and x["lambda_per_day"] == central_lam), None)
        if ch_chosen is None or ch_1pct is None:
            continue
        # Revert if chosen's bust prob > 10% and 1% has lower bust at similar pass
        if ch_chosen["p_bust_dd"] > 0.10:
            revert_threshold = wr
            break

    baseline_1pct = next(c for c in candidates if c["risk_pct"] == 1.0)

    rec = {
        "recommended_risk_pct": rec_risk,
        "method": method,
        "wr_weights_used": WR_WEIGHTS,
        "constraints": {
            "p_bust_dd_60d_max": 0.05,
            "p_daily_loss_gt_5pct_max": 0.01,
        },
        "chosen_metrics_lambda_1.0": {
            "weighted_monthly_return_pct": chosen["w_monthly_pct"],
            "weighted_p_max_dd_gt_10pct_annual": chosen["w_p_dd10_annual"],
            "weighted_p_bust_dd_within_60d": chosen["w_p_bust_dd_60d"],
            "weighted_p_pass_step1_within_60d": chosen["w_p_pass_60d"],
            "weighted_p_timeout_60d": chosen["w_p_timeout_60d"],
            "weighted_p_daily_loss_gt_5pct": chosen["w_p_d5"],
            "weighted_p_daily_loss_gt_4pct": chosen["w_p_d4"],
            "weighted_median_days_to_pass": chosen["w_med_days_to_pass_cap75"],
        },
        "baseline_1pct_metrics_lambda_1.0": {
            "weighted_monthly_return_pct": baseline_1pct["w_monthly_pct"],
            "weighted_p_max_dd_gt_10pct_annual": baseline_1pct["w_p_dd10_annual"],
            "weighted_p_bust_dd_within_60d": baseline_1pct["w_p_bust_dd_60d"],
            "weighted_p_pass_step1_within_60d": baseline_1pct["w_p_pass_60d"],
            "weighted_p_daily_loss_gt_5pct": baseline_1pct["w_p_d5"],
            "weighted_median_days_to_pass": baseline_1pct["w_med_days_to_pass_cap75"],
        },
        "wr_threshold_below_which_revert_to_1pct": revert_threshold,
        "wr_threshold_breakeven_at_chosen": wr_threshold_breakeven,
        "all_risk_candidates_lambda_1.0": candidates,
    }
    rec_path = OUT_DIR / "recommendation.json"
    rec_path.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    print(f"\n[ok] wrote {rec_path}", flush=True)

    # Tables
    matrices_md = "# MC Result Matrices\n\n"
    matrices_md += "All matrices use lambda=1.0 (central case) unless suffix indicates 3D.\n\n"
    matrices_md += "## Annual MC (252-day horizon)\n\n"
    matrices_md += "### Median Days to Step 1 (10% target) — within first 60 days, censored to '>60d' if not hit\n\n"
    matrices_md += matrices["median_days_to_step1_annual"] + "\n\n"
    matrices_md += "### Median Days to Step 2 (5% target) — within first 60 days, censored to '>60d' if not hit\n\n"
    matrices_md += matrices["median_days_to_step2_annual"] + "\n\n"
    matrices_md += "### P(MaxDD > 10% at any point in 252-day year)\n\n"
    matrices_md += matrices["p_max_dd_gt_10pct_annual"] + "\n\n"
    matrices_md += "### P(any single day loss > 5%) — fraction of all simulated days\n\n"
    matrices_md += matrices["p_daily_loss_gt_5pct"] + "\n\n"
    matrices_md += "### P(any single day loss > 4%) — internal MTM trigger\n\n"
    matrices_md += matrices["p_daily_loss_gt_4pct"] + "\n\n"
    matrices_md += "### Expected MTM idle days/year (auto-flatten triggered)\n\n"
    matrices_md += matrices["expected_mtm_idle_days_annual"] + "\n\n"
    matrices_md += "## Challenge MC (60-day Step 1 race)\n\n"
    matrices_md += "### P(PASS Step 1 within 60 days)\n\n"
    matrices_md += matrices["p_pass_step1_60d"] + "\n\n"
    matrices_md += "### P(BUST by hitting -10% MaxDD before passing)\n\n"
    matrices_md += matrices["p_bust_dd_60d"] + "\n\n"
    matrices_md += "### Median days to PASS (conditional on passing)\n\n"
    matrices_md += matrices["median_days_to_pass_60d"] + "\n\n"
    matrices_md += "## 3D matrices (risk x WR x lambda)\n\n"
    matrices_md += "### Monthly Return (annual / 12)\n"
    matrices_md += matrices["monthly_return_3d"] + "\n\n"
    matrices_md += "### P(60d PASS) by lambda\n"
    matrices_md += matrices["p_pass_60d_3d"] + "\n\n"
    matrices_md += "### P(60d BUST by DD) by lambda\n"
    matrices_md += matrices["p_bust_dd_60d_3d"] + "\n"
    (OUT_DIR / "matrices.md").write_text(matrices_md, encoding="utf-8")
    print(f"[ok] wrote matrices.md", flush=True)


if __name__ == "__main__":
    main()
