#!/usr/bin/env python3
"""Reconcile the LIVE firing rate with the three-sleeve book's own expectation.

Measurement only.  No live path, no config, no broker, no VPS.

WHY.  Lane F measured the armed book at **1 trade in 12.85 days** against a `CLAUDE.md`
expectation of ~7 book-days/month, and W7 §1.6 read that as "discount the headline by 2.74x".
Both compared the live rate against the `AS_PUBLISHED` cache rate of 6.5 book-days/month --
the rate of a book trading every symbol the cache contains, including the 44.9 % of its
population on instruments neither account's sleeves can generate today
(`LIVE_BOOK_INTEGRITY_V1.md` §1.4).  This asks the question against each account's OWN
surface, which is the only rate either account could ever produce, and reports a Poisson
tail for each so "consistent" and "inconsistent" are decided by a number.

`p_pass` is invariant to frequency (W7 §1.6: `p_timeout` is 0.0000 -- the MC draws book-days
until a barrier is hit).  Frequency scales the MONTHLY RATE and the CALENDAR CLOCK and nothing
else, so this restates both at every rate that has a claim to being the right one.

Inputs: `THREE_SLEEVE_BOOK_V1.json` (this lane), `LANE_F_LIVE_BOOK_GROUND_TRUTH_V1.md` §1
(1 book trade / 12.85 days armed on FTMO; 0 / 12.17 on redacted_account, the latter blocked by the
token-digest defect rather than by absence of signal).

Usage: python3 live_rate_reconciliation.py [book.json] [out.json]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "THREE_SLEEVE_BOOK_V1.json"
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "LIVE_RATE_RECONCILIATION_V1.json"

# LANE_F_LIVE_BOOK_GROUND_TRUTH_V1.md §1 [MEASURED, broker deal history 2026-08-11T09:24:57Z]
LANE_F = {
    "FTMO": {"days_armed": 12.85, "book_trades": 1, "book_days_observed": 1,
             "realized_usd": 493.20, "realized_R": 0.382, "balance_at_arming": 107872.28},
    "redacted_account": {"days_armed": 12.17, "book_trades": 0, "book_days_observed": 0,
                   "realized_usd": 0.0, "realized_R": 0.0, "balance_at_arming": 96229.28},
}
DAYS_PER_MONTH = 30.4369          # mean Gregorian calendar month

D = json.loads(BOOK.read_text())
CELLS = D["cells"]

# the honest cell for each account: its own tradeable surface
HONEST = {"FTMO": "THREE_SLEEVE_ARMED|CURRENT_SURFACE|FTMO",
          "redacted_account": "THREE_SLEEVE_ARMED|FN_TRADEABLE|redacted_account"}
PRIOR = {"FTMO": "FOUR_SLEEVE_PRIOR|CURRENT_SURFACE|FTMO",
         "redacted_account": "FOUR_SLEEVE_PRIOR|FN_TRADEABLE|redacted_account"}


def pois_le(k, lam):
    """P(X <= k) for a Poisson(lam)."""
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))


out = {
    "schema": "gtos.wave21.live_rate_reconciliation.v1",
    "measurement_only": True,
    "lane_f_ground_truth": LANE_F,
    "note_on_the_observation_window": (
        "the whole live window ran the FOUR-sleeve book with the cluster cap OFF, so the "
        "PRIOR row is the correct expectation to test the observation against; the HONEST "
        "row is the expectation going forward"),
    "accounts": {},
}

for acct in ("FTMO", "redacted_account"):
    f = LANE_F[acct]
    months_observed = f["days_armed"] / DAYS_PER_MONTH
    row = {"days_armed": f["days_armed"], "months_observed": round(months_observed, 4),
           "book_days_observed": f["book_days_observed"], "rates": {}}
    rates = {
        "CLAUDE_md_stated_expectation": 7.0,
        "AS_PUBLISHED_cache_three_sleeve": CELLS[f"THREE_SLEEVE_ARMED|AS_PUBLISHED|{acct}"]
        ["book_days_per_month"],
        "PRIOR_four_sleeve_own_surface": CELLS[PRIOR[acct]]["book_days_per_month"],
        "HONEST_three_sleeve_own_surface": CELLS[HONEST[acct]]["book_days_per_month"],
    }
    for label, bdpm in rates.items():
        lam = bdpm * months_observed
        row["rates"][label] = {
            "book_days_per_calendar_month": round(bdpm, 3),
            "expected_book_days_in_window": round(lam, 3),
            "P_at_most_observed_given_this_rate": round(pois_le(f["book_days_observed"], lam), 4),
            "consistent_at_5pct": pois_le(f["book_days_observed"], lam) >= 0.05,
        }
    # calendar restatement of the honest cell at each rate
    h = CELLS[HONEST[acct]]
    mbd = h["uncorrected"]["median_book_days_to_pass"]
    ci = h["corrected_instrument"]
    row["honest_cell"] = {
        "key": HONEST[acct],
        "trades": h["trades"], "book_days": h["book_days"],
        "mean_r_per_book_day": h["mean_r_per_book_day"],
        "ci95_mean_r_per_book_day": h["ci95_mean_r_per_book_day"],
        "t_stat_mean": h["t_stat_mean"],
        "median_book_days_to_pass_two_phase": mbd,
        "p_pass_uncorrected": h["uncorrected"]["p_pass"],
        "p_pass_corrected_median": round(ci["p_pass"]["median"], 5),
        "p_pass_corrected_ci95": [round(ci["p_pass"]["p2_5"], 5), round(ci["p_pass"]["p97_5"], 5)],
        "p_pass_joint_median": round(h["joint_instrument_x_sampling"]["p_pass"]["median"], 5),
        "p_pass_joint_ci95": [round(h["joint_instrument_x_sampling"]["p_pass"]["p2_5"], 5),
                              round(h["joint_instrument_x_sampling"]["p_pass"]["p97_5"], 5)],
        "p_pass_joint_p10": round(h["joint_instrument_x_sampling"]["p_pass"]["p10"], 5),
    }
    row["calendar_restatement"] = {}
    for label, bdpm in rates.items():
        row["calendar_restatement"][label] = {
            "monthly_pct_uncorrected": round(100.0 * h["mean_r_per_book_day"]
                                             * h["eff_risk_pct"] / 100.0 * bdpm, 3),
            "monthly_pct_corrected_median": round(
                100.0 * ci["mean_r_per_book_day"]["median"] * h["eff_risk_pct"] / 100.0 * bdpm, 3),
            "monthly_pct_corrected_ci95": [
                round(100.0 * ci["mean_r_per_book_day"]["p2_5"] * h["eff_risk_pct"] / 100.0 * bdpm, 3),
                round(100.0 * ci["mean_r_per_book_day"]["p97_5"] * h["eff_risk_pct"] / 100.0 * bdpm, 3)],
            "median_calendar_months_to_pass": (round(mbd / bdpm, 2) if mbd and bdpm else None),
            "median_calendar_days_to_pass": (round(mbd / bdpm * DAYS_PER_MONTH)
                                             if mbd and bdpm else None),
        }
    out["accounts"][acct] = row

# ---- the live P&L, stated as an interval ---------------------------------------------
# One trade. The honest statement is a Wilson/one-observation bound, not a rate.
out["live_pnl_interval"] = {
    "combined_realized_usd": 493.20,
    "combined_capital_usd": 200000.0,
    "combined_pct_of_capital": round(100.0 * 493.20 / 200000.0, 4),
    "ftmo_pct_of_balance_at_arming": round(100.0 * 493.20 / 107872.28, 4),
    "n_book_trades": 1,
    "note": ("a single realized trade supports no interval on a rate. Lane F's own power "
             "statement is the honest one: the 95 % interval on the monthly rate implied by "
             "one trade is [-5.6, +7.8] pp/month, which contains +4.5, +0.1 and zero alike."),
}

DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
for acct, row in out["accounts"].items():
    print(f"\n=== {acct}  observed {row['book_days_observed']} book-day(s) in "
          f"{row['days_armed']} days ({row['months_observed']:.3f} months)")
    for label, r in row["rates"].items():
        print(f"  {label:38s} {r['book_days_per_calendar_month']:6.3f}/mo  "
              f"E[days]={r['expected_book_days_in_window']:5.2f}  "
              f"P(X<=obs)={r['P_at_most_observed_given_this_rate']:.4f}  "
              f"{'consistent' if r['consistent_at_5pct'] else 'INCONSISTENT'}")
    h = row["honest_cell"]
    print(f"  HONEST CELL {h['key']}: n={h['trades']} d={h['book_days']} "
          f"R/bd={h['mean_r_per_book_day']:+.5f} CI95{h['ci95_mean_r_per_book_day']} "
          f"t={h['t_stat_mean']}")
    print(f"    p_pass  unc {h['p_pass_uncorrected']:.4f} | corrected {h['p_pass_corrected_median']:.4f} "
          f"{h['p_pass_corrected_ci95']} | JOINT {h['p_pass_joint_median']:.4f} "
          f"{h['p_pass_joint_ci95']} p10 {h['p_pass_joint_p10']:.4f}")
    for label, c in row["calendar_restatement"].items():
        print(f"    at {label:38s} %/mo {c['monthly_pct_corrected_median']:+7.3f} "
              f"{c['monthly_pct_corrected_ci95']}  median pass {c['median_calendar_days_to_pass']} days")
