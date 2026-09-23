"""Honest Monte Carlo simulation for redacted_account Stellar 2-Step pass probability.

Uses per-instrument honest expectancies from the chairman synthesis (phase 4),
NOT the artefactual canonical 73.2% WR number.

Run from repo root:
    python research/b_deep_audit_2026-04-19/honest_mc_redacted_account.py

Outputs JSON summary next to this script for the markdown report.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

STARTING_EQUITY = 100_000.0
DAILY_LOSS_CAP_PCT = 0.04        # GTOS internal cap (broker allows 5%)
OVERALL_LOSS_CAP_PCT = 0.10      # redacted_account Stellar rule
STEP1_TARGET_PCT = 0.10          # +10% to pass step 1
TRADING_DAYS = 90                # ~one quarter
N_PATHS = 10_000
RNG_SEED = 20260420


@dataclass(frozen=True)
class Instrument:
    name: str
    risk_pct: float          # fraction of equity at risk per trade (e.g. 0.01 = 1%)
    win_rate: float          # probability of a winner
    target_R: float          # R multiple on a win
    trades_per_month: float  # expected arrivals per calendar month


# Base case — chairman-synthesis honest numbers
BASE_INSTRUMENTS = [
    Instrument("XAUUSD", risk_pct=0.005, win_rate=0.594, target_R=1.5, trades_per_month=4.0),
    Instrument("US30",   risk_pct=0.010, win_rate=0.585, target_R=1.5, trades_per_month=3.5),
    Instrument("USDJPY", risk_pct=0.010, win_rate=0.758, target_R=1.5, trades_per_month=3.0),
    Instrument("GBPJPY", risk_pct=0.010, win_rate=0.571, target_R=1.5, trades_per_month=3.0),
]
# Fleet-wide ~13.5 trades/month, matches "17 trades/mo with 5 instruments pro-rated to 4".


def expectancy_R(wr: float, target_R: float) -> float:
    return wr * target_R - (1.0 - wr) * 1.0


# ---------------------------------------------------------------------------
# Monte Carlo core
# ---------------------------------------------------------------------------

def simulate(instruments: list[Instrument],
             n_paths: int = N_PATHS,
             trading_days: int = TRADING_DAYS,
             seed: int = RNG_SEED) -> dict:
    """Vectorized account-path MC.

    Poisson arrivals per instrument per day (monthly rate / 21 trading days).
    Daily loss cap halts further trades that day. Overall drawdown from
    running peak halts the account (FAIL). Reaching +10% total PnL = PASS
    (step 1 target). We track first-hit day for PASS and FAIL separately.
    """
    rng = np.random.default_rng(seed)

    daily_rates = np.array([inst.trades_per_month / 21.0 for inst in instruments])
    win_rates   = np.array([inst.win_rate for inst in instruments])
    targets_R   = np.array([inst.target_R for inst in instruments])
    risk_pcts   = np.array([inst.risk_pct for inst in instruments])
    n_inst      = len(instruments)

    equity       = np.full(n_paths, STARTING_EQUITY)
    peak_equity  = np.full(n_paths, STARTING_EQUITY)
    passed       = np.zeros(n_paths, dtype=bool)
    failed_overall = np.zeros(n_paths, dtype=bool)
    failed_daily_any = np.zeros(n_paths, dtype=bool)  # did ANY day breach 4%?
    failed_overall_any = np.zeros(n_paths, dtype=bool)

    day_passed   = np.full(n_paths, -1, dtype=np.int32)
    day_failed   = np.full(n_paths, -1, dtype=np.int32)

    for day in range(trading_days):
        live_mask = (~passed) & (~failed_overall)
        if not live_mask.any():
            break
        start_of_day_equity = equity.copy()
        # simulate trades per instrument
        for i in range(n_inst):
            # Poisson draws — how many trades today on this instrument, per path
            n_trades = rng.poisson(daily_rates[i], size=n_paths)
            max_trades = int(n_trades.max()) if n_trades.size else 0
            if max_trades == 0:
                continue
            # expand each path into up-to max_trades slots; mask inactive slots
            slot_idx = np.arange(max_trades)[None, :]  # (1, max_trades)
            active_slot = slot_idx < n_trades[:, None]  # (n_paths, max_trades)
            wins = rng.random(size=(n_paths, max_trades)) < win_rates[i]

            # outcome R per slot (win = +target, lose = -1)
            r_per_slot = np.where(wins, targets_R[i], -1.0) * active_slot

            # apply trades one slot at a time so we can enforce daily stop
            for s in range(max_trades):
                slot_live = live_mask & active_slot[:, s]
                if not slot_live.any():
                    continue
                # equity at risk per trade (use START-of-day equity, standard prop-firm convention)
                risk_amount = start_of_day_equity * risk_pcts[i]
                pnl_slot = r_per_slot[:, s] * risk_amount
                # projected equity
                projected = equity + pnl_slot
                # daily drawdown check: has equity fallen to -4% of start-of-day?
                daily_floor = start_of_day_equity * (1.0 - DAILY_LOSS_CAP_PCT)
                would_breach_daily = projected < daily_floor
                # for paths that would breach, still take the loss up to floor and stop for day
                daily_breach_this_slot = slot_live & would_breach_daily
                if daily_breach_this_slot.any():
                    # book the trade (it caused the breach), then mark daily-stopped
                    equity = np.where(slot_live, projected, equity)
                    failed_daily_any |= daily_breach_this_slot
                    # mark those paths done-for-today by pulling them out of live_mask
                    live_mask = live_mask & ~daily_breach_this_slot
                else:
                    equity = np.where(slot_live, projected, equity)

                # update peak + check overall drawdown and pass
                peak_equity = np.maximum(peak_equity, equity)
                overall_dd_from_peak = (peak_equity - equity) / STARTING_EQUITY
                # redacted_account static rule uses drawdown from starting balance high-water —
                # use starting_equity baseline so the 10% is off the opening balance, as
                # is typical for Stellar static-drawdown variant. For conservatism we
                # also require NOT breaching peak-to-trough >10%.
                overall_dd_from_start = (STARTING_EQUITY - equity) / STARTING_EQUITY
                overall_breach = (overall_dd_from_start >= OVERALL_LOSS_CAP_PCT) | \
                                 (overall_dd_from_peak >= OVERALL_LOSS_CAP_PCT)
                new_fail = overall_breach & (~failed_overall) & (~passed)
                if new_fail.any():
                    failed_overall |= new_fail
                    failed_overall_any |= new_fail
                    day_failed = np.where(new_fail & (day_failed < 0), day, day_failed)
                    live_mask = live_mask & ~new_fail

                pass_mask = (equity >= STARTING_EQUITY * (1.0 + STEP1_TARGET_PCT)) & (~passed) & (~failed_overall)
                if pass_mask.any():
                    passed |= pass_mask
                    day_passed = np.where(pass_mask & (day_passed < 0), day, day_passed)
                    live_mask = live_mask & ~pass_mask

    # --- summary ----------------------------------------------------------
    p_pass = passed.mean()
    p_overall_breach = failed_overall_any.mean()
    p_daily_breach_any = failed_daily_any.mean()

    pass_days = day_passed[passed]
    if pass_days.size:
        median_days_to_pass = float(np.median(pass_days))
        p10 = float(np.percentile(pass_days, 10))
        p90 = float(np.percentile(pass_days, 90))
    else:
        median_days_to_pass = p10 = p90 = float("nan")

    final_equity = equity
    final_R = (final_equity - STARTING_EQUITY) / STARTING_EQUITY

    return {
        "n_paths": int(n_paths),
        "trading_days": int(trading_days),
        "p_pass_step1": float(p_pass),
        "p_overall_breach": float(p_overall_breach),
        "p_daily_breach_any": float(p_daily_breach_any),
        "median_days_to_pass": median_days_to_pass,
        "p10_days_to_pass": p10,
        "p90_days_to_pass": p90,
        "median_final_pct": float(np.median(final_R)),
        "p10_final_pct": float(np.percentile(final_R, 10)),
        "p90_final_pct": float(np.percentile(final_R, 90)),
        "instruments": [asdict(i) for i in instruments],
    }


# ---------------------------------------------------------------------------
# Sensitivity scenarios
# ---------------------------------------------------------------------------

def pessimistic() -> list[Instrument]:
    """XAUUSD WR drops to 50%; others unchanged."""
    return [
        Instrument("XAUUSD", 0.005, 0.50, 1.5, 4.0),
        Instrument("US30",   0.010, 0.585, 1.5, 3.5),
        Instrument("USDJPY", 0.010, 0.758, 1.5, 3.0),
        Instrument("GBPJPY", 0.010, 0.571, 1.5, 3.0),
    ]


def optimistic() -> list[Instrument]:
    """XAUUSD reverts to 2025 regime, 65% WR."""
    return [
        Instrument("XAUUSD", 0.005, 0.65, 1.5, 4.0),
        Instrument("US30",   0.010, 0.585, 1.5, 3.5),
        Instrument("USDJPY", 0.010, 0.758, 1.5, 3.0),
        Instrument("GBPJPY", 0.010, 0.571, 1.5, 3.0),
    ]


def canonical_fleet() -> list[Instrument]:
    """Artefactual canonical 73.2% WR applied uniformly to the fleet."""
    return [
        Instrument("XAUUSD", 0.005, 0.732, 1.5, 4.0),
        Instrument("US30",   0.010, 0.732, 1.5, 3.5),
        Instrument("USDJPY", 0.010, 0.732, 1.5, 3.0),
        Instrument("GBPJPY", 0.010, 0.732, 1.5, 3.0),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    scenarios = {
        "base_chairman_honest": BASE_INSTRUMENTS,
        "pessimistic_xauusd_50wr": pessimistic(),
        "optimistic_xauusd_65wr": optimistic(),
        "canonical_artefact_732wr": canonical_fleet(),
    }

    results = {}
    for name, insts in scenarios.items():
        print(f"--- scenario: {name} ---")
        res = simulate(insts, seed=RNG_SEED)  # same seed for comparability
        results[name] = res
        print(json.dumps({k: v for k, v in res.items() if k != "instruments"}, indent=2))

    # Per-instrument monthly R contribution (base case only)
    per_inst_contrib = []
    for inst in BASE_INSTRUMENTS:
        exp_R = expectancy_R(inst.win_rate, inst.target_R)
        monthly_R = exp_R * inst.trades_per_month
        per_inst_contrib.append({
            "name": inst.name,
            "win_rate": inst.win_rate,
            "target_R": inst.target_R,
            "expectancy_R_per_trade": exp_R,
            "trades_per_month": inst.trades_per_month,
            "monthly_R_contribution": monthly_R,
            "risk_pct": inst.risk_pct,
            "monthly_pct_contribution": monthly_R * inst.risk_pct,
        })

    out = {
        "config": {
            "starting_equity": STARTING_EQUITY,
            "daily_loss_cap_pct": DAILY_LOSS_CAP_PCT,
            "overall_loss_cap_pct": OVERALL_LOSS_CAP_PCT,
            "step1_target_pct": STEP1_TARGET_PCT,
            "trading_days": TRADING_DAYS,
            "n_paths": N_PATHS,
            "seed": RNG_SEED,
        },
        "scenarios": results,
        "per_instrument_contribution_base": per_inst_contrib,
    }

    out_path = Path(__file__).parent / "honest_mc_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
