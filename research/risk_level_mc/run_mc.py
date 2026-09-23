#!/usr/bin/env python3
"""Monte Carlo: FTMO $100K paid challenge — risk-per-trade level optimization.

CEO is shipping Monday 2026-04-27. Question: BUMP risk-per-trade for Monday
given the actual FTMO 10%/5% MaxDD/Daily headroom.

FTMO Specs (corrected by CEO):
  - Step 1 target: 10%
  - Step 2 target: 5%
  - Total MaxDD: 10%
  - Daily MaxDD: 5%
  - Internal MTM stop: 4% (1pp safety margin from FTMO 5%)
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Force UTF-8 stdout on Windows BEFORE any prints
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import numpy as np
from scipy.stats import norm

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Trade model
RR_TP = 1.5
RR_SL = 1.0
INTRA_DAY_CORR = 0.3
MTM_STOP_PCT = 4.0
N_INST = 4

N_SIMS = int(os.environ.get("MC_NSIMS", "10000"))
N_DAYS_ANNUAL = 252
N_DAYS_STEP_WINDOW = 60

RISK_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
WR_LEVELS = [0.62, 0.58, 0.55, 0.50, 0.45]
LAMBDAS = [0.7, 1.0, 1.5]

STEP1_TARGET = 10.0
STEP2_TARGET = 5.0
MAX_DD_LIMIT = 10.0
DAILY_LIMIT = 5.0


@dataclass
class ScenarioResult:
    risk_pct: float
    wr: float
    lambda_per_day: float
    mean_annual_pnl_pct: float
    median_annual_pnl_pct: float
    monthly_return_pct: float
    p_max_dd_gt_10pct: float
    mean_max_dd_pct: float
    p99_max_dd_pct: float
    p_daily_loss_gt_5pct: float
    p_daily_loss_gt_4pct: float
    median_days_to_step1: float
    p90_days_to_step1: float
    p_step1_within_60d: float
    median_days_to_step2: float
    p90_days_to_step2: float
    p_step2_within_60d: float
    expected_mtm_stop_days_per_year: float


def simulate_year(rng, risk_pct: float, wr: float, lambda_per_day: float,
                  n_days: int = N_DAYS_ANNUAL):
    """Return daily_pnl array (pct) + n_mtm_halts, n_daily_breach_5, n_daily_breach_4."""
    z_target = norm.ppf(wr) if 0 < wr < 1 else 0.0
    daily_pnl = np.zeros(n_days)
    n_mtm_halts = 0
    n_daily_breach_5 = 0
    n_daily_breach_4 = 0

    for d in range(n_days):
        n_trades_raw = rng.poisson(lambda_per_day)
        n_trades = min(n_trades_raw, 8)
        if n_trades == 0:
            continue
        if INTRA_DAY_CORR > 0:
            z_day = rng.standard_normal()
            adj_wr = norm.cdf(z_target - INTRA_DAY_CORR * z_day)
            wins = rng.random(n_trades) < adj_wr
        else:
            wins = rng.random(n_trades) < wr
        r_per_trade = np.where(wins, RR_TP, -RR_SL)
        cum_r = np.cumsum(r_per_trade)
        cum_pct = cum_r * risk_pct
        halt_idx = np.where(cum_pct <= -MTM_STOP_PCT)[0]
        if len(halt_idx) > 0:
            day_pct = float(cum_pct[halt_idx[0]])
            n_mtm_halts += 1
        else:
            day_pct = float(cum_pct[-1])
        daily_pnl[d] = day_pct
        if day_pct < -DAILY_LIMIT:
            n_daily_breach_5 += 1
        if day_pct < -MTM_STOP_PCT:
            n_daily_breach_4 += 1
    return daily_pnl, n_mtm_halts, n_daily_breach_5, n_daily_breach_4


def first_hit_day(cum, target):
    hits = np.where(cum >= target)[0]
    return int(hits[0]) + 1 if len(hits) > 0 else None


def run_scenario(risk_pct, wr, lambda_per_day, seed):
    rng = np.random.default_rng(seed)
    annual_pnls = []
    max_dds = []
    n_mtm_total = 0
    n_d5 = 0
    n_d4 = 0
    days_to_s1 = []
    days_to_s2 = []
    n_hit_s1 = 0
    n_hit_s2 = 0
    total_days = 0

    for _ in range(N_SIMS):
        daily_pnl, mtm, d5, d4 = simulate_year(rng, risk_pct, wr, lambda_per_day, N_DAYS_ANNUAL)
        cum = np.cumsum(daily_pnl)
        peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
        dd = cum - peak
        annual_pnls.append(float(cum[-1]))
        max_dds.append(float(dd.min()))
        n_mtm_total += mtm
        n_d5 += d5
        n_d4 += d4
        total_days += N_DAYS_ANNUAL
        cum60 = cum[:N_DAYS_STEP_WINDOW]
        s1 = first_hit_day(cum60, STEP1_TARGET)
        s2 = first_hit_day(cum60, STEP2_TARGET)
        if s1 is not None:
            days_to_s1.append(s1)
            n_hit_s1 += 1
        if s2 is not None:
            days_to_s2.append(s2)
            n_hit_s2 += 1

    annual = np.array(annual_pnls)
    dds = np.array(max_dds)

    med_s1 = float(np.median(days_to_s1)) if days_to_s1 else float("inf")
    p90_s1 = float(np.percentile(days_to_s1, 90)) if days_to_s1 else float("inf")
    med_s2 = float(np.median(days_to_s2)) if days_to_s2 else float("inf")
    p90_s2 = float(np.percentile(days_to_s2, 90)) if days_to_s2 else float("inf")

    return ScenarioResult(
        risk_pct=risk_pct,
        wr=wr,
        lambda_per_day=lambda_per_day,
        mean_annual_pnl_pct=float(annual.mean()),
        median_annual_pnl_pct=float(np.median(annual)),
        monthly_return_pct=float(annual.mean() / 12.0),
        p_max_dd_gt_10pct=float((dds < -MAX_DD_LIMIT).mean()),
        mean_max_dd_pct=float(dds.mean()),
        p99_max_dd_pct=float(np.percentile(dds, 1)),
        p_daily_loss_gt_5pct=n_d5 / total_days,
        p_daily_loss_gt_4pct=n_d4 / total_days,
        median_days_to_step1=med_s1,
        p90_days_to_step1=p90_s1,
        p_step1_within_60d=n_hit_s1 / N_SIMS,
        median_days_to_step2=med_s2,
        p90_days_to_step2=p90_s2,
        p_step2_within_60d=n_hit_s2 / N_SIMS,
        expected_mtm_stop_days_per_year=n_mtm_total / N_SIMS,
    )


def main():
    print("=" * 80, flush=True)
    print("FTMO RISK-LEVEL MC: 7 risk x 5 WR x 3 lam = 105 scenarios x 10k sims", flush=True)
    print(f"FTMO targets: Step 1={STEP1_TARGET}%, Step 2={STEP2_TARGET}%, MaxDD={MAX_DD_LIMIT}%, Daily={DAILY_LIMIT}%, MTM={MTM_STOP_PCT}%", flush=True)
    print("=" * 80, flush=True)

    results = []
    n_total = len(RISK_LEVELS) * len(WR_LEVELS) * len(LAMBDAS)
    i = 0
    for risk_pct in RISK_LEVELS:
        for wr in WR_LEVELS:
            for lam in LAMBDAS:
                i += 1
                seed = (int(risk_pct * 1000) * 1_000_000
                        + int(wr * 100) * 1_000
                        + int(lam * 10) + 42)
                r = run_scenario(risk_pct, wr, lam, seed)
                results.append(asdict(r))
                med_s1_str = ">60d " if r.median_days_to_step1 == float("inf") else f"{r.median_days_to_step1:5.1f}d"
                print(
                    f"  [{i:3d}/{n_total}] risk={risk_pct:.2f}% wr={wr:.2f} lam={lam:.1f} | "
                    f"E[mo]={r.monthly_return_pct:+6.2f}% | "
                    f"P(DD>10)={r.p_max_dd_gt_10pct:.4f} | "
                    f"P(daily>5)={r.p_daily_loss_gt_5pct:.5f} | "
                    f"med_S1={med_s1_str} | "
                    f"P(S1<60d)={r.p_step1_within_60d:.3f}",
                    flush=True
                )

    out_csv = OUT_DIR / "risk_mc_results.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\n[ok] wrote {out_csv} ({len(results)} rows)", flush=True)

    out_json = OUT_DIR / "risk_mc_results.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"[ok] wrote {out_json}", flush=True)


if __name__ == "__main__":
    main()
