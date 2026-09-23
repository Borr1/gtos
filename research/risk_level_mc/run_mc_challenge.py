#!/usr/bin/env python3
"""Challenge-horizon MC: race between Step 1 target (+10%) and MaxDD limit (-10%).

Different from the annual MC — here we ask: in a 60-day Monday-to-pass-Step-1
window, what's the probability of:
  - Hitting +10% (PASS)
  - Hitting -10% MaxDD first (BUST)
  - Neither in 60 days (TIME-OUT, retry)

This is the actual decision-relevant metric for FTMO Step 1.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import numpy as np
from scipy.stats import norm

OUT_DIR = Path(__file__).resolve().parent
RR_TP = 1.5
RR_SL = 1.0
INTRA_DAY_CORR = 0.3
MTM_STOP_PCT = 4.0
DAILY_LIMIT = 5.0

N_SIMS = int(os.environ.get("MC_NSIMS", "10000"))
N_DAYS = 60  # Step 1 challenge window
RISK_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
WR_LEVELS = [0.62, 0.58, 0.55, 0.50, 0.45]
LAMBDAS = [0.7, 1.0, 1.5]

STEP1 = 10.0
MAXDD_LIMIT = 10.0


@dataclass
class ChallengeResult:
    risk_pct: float
    wr: float
    lambda_per_day: float
    p_pass_s1: float
    p_bust_dd: float
    p_bust_daily5: float
    p_timeout: float
    median_days_to_pass: float
    median_days_to_bust_dd: float
    expected_attempts: float  # 1 / (p_pass + p_timeout * decay) — see below


def simulate_challenge(rng, risk_pct, wr, lambda_per_day, n_days=N_DAYS):
    z_target = norm.ppf(wr) if 0 < wr < 1 else 0.0
    cum = 0.0
    peak = 0.0
    pass_day = None
    bust_dd_day = None
    bust_daily_day = None

    for d in range(n_days):
        n_trades_raw = rng.poisson(lambda_per_day)
        n_trades = min(n_trades_raw, 8)
        if n_trades > 0:
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
                day_pnl = float(cum_pct[halt_idx[0]])
            else:
                day_pnl = float(cum_pct[-1])
            # Track intra-day max forward; assume sequential trade fills
            # FTMO daily limit measured vs start-of-day equity
            if day_pnl < -DAILY_LIMIT:
                if bust_daily_day is None:
                    bust_daily_day = d + 1
            cum += day_pnl
        # Update peak/dd
        if cum > peak:
            peak = cum
        dd = cum - peak
        if cum >= STEP1 and pass_day is None:
            pass_day = d + 1
        if dd <= -MAXDD_LIMIT and bust_dd_day is None:
            bust_dd_day = d + 1
        # Stop at first PASS or BUST
        if pass_day is not None or bust_dd_day is not None or bust_daily_day is not None:
            break

    return pass_day, bust_dd_day, bust_daily_day


def run_scenario(risk, wr, lam, seed):
    rng = np.random.default_rng(seed)
    pass_days = []
    bust_dd_days = []
    bust_daily_days = []
    n_pass = n_bust_dd = n_bust_d = n_timeout = 0
    for _ in range(N_SIMS):
        p, bdd, bd = simulate_challenge(rng, risk, wr, lam)
        if p is not None:
            n_pass += 1
            pass_days.append(p)
        elif bdd is not None:
            n_bust_dd += 1
            bust_dd_days.append(bdd)
        elif bd is not None:
            n_bust_d += 1
            bust_daily_days.append(bd)
        else:
            n_timeout += 1

    p_pass = n_pass / N_SIMS
    p_bdd = n_bust_dd / N_SIMS
    p_bd = n_bust_d / N_SIMS
    p_to = n_timeout / N_SIMS
    expected_attempts = 1.0 / max(p_pass, 1e-9)
    return ChallengeResult(
        risk_pct=risk, wr=wr, lambda_per_day=lam,
        p_pass_s1=p_pass, p_bust_dd=p_bdd, p_bust_daily5=p_bd, p_timeout=p_to,
        median_days_to_pass=float(np.median(pass_days)) if pass_days else float("inf"),
        median_days_to_bust_dd=float(np.median(bust_dd_days)) if bust_dd_days else float("inf"),
        expected_attempts=expected_attempts,
    )


def main():
    print("=" * 80, flush=True)
    print("CHALLENGE-HORIZON MC: 60-day Step 1 race (10% target vs 10% MaxDD bust)", flush=True)
    print(f"N_SIMS={N_SIMS} per scenario", flush=True)
    print("=" * 80, flush=True)
    results = []
    n_total = len(RISK_LEVELS) * len(WR_LEVELS) * len(LAMBDAS)
    i = 0
    for risk in RISK_LEVELS:
        for wr in WR_LEVELS:
            for lam in LAMBDAS:
                i += 1
                seed = int(risk * 1000) * 1_000_000 + int(wr * 100) * 1_000 + int(lam * 10) + 42
                r = run_scenario(risk, wr, lam, seed)
                results.append(asdict(r))
                med_p_str = f"{r.median_days_to_pass:.1f}d" if r.median_days_to_pass != float("inf") else ">60d"
                print(
                    f"  [{i:3d}/{n_total}] risk={risk:.2f}% wr={wr:.2f} lam={lam:.1f} | "
                    f"P(PASS)={r.p_pass_s1*100:5.2f}% | P(bust DD)={r.p_bust_dd*100:5.2f}% | "
                    f"P(bust daily)={r.p_bust_daily5*100:5.2f}% | P(time-out)={r.p_timeout*100:5.2f}% | "
                    f"med_PASS={med_p_str} | E[attempts]={r.expected_attempts:.2f}",
                    flush=True
                )

    out_csv = OUT_DIR / "risk_mc_challenge.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\n[ok] wrote {out_csv}", flush=True)
    out_json = OUT_DIR / "risk_mc_challenge.json"
    out_json.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"[ok] wrote {out_json}", flush=True)


if __name__ == "__main__":
    main()
