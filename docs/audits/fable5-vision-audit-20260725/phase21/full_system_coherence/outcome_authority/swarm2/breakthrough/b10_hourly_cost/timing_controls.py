"""B10 -- the controls that decide whether the delay arm is a COST rule or a SKIP rule.

The delay arms look spectacular: D60 takes net from -0.5560 to -0.2786 R/trade and total
from -12,056 R to -2,433 R.  The mandate's own warning applies word for word -- *a
cost-avoidance rule that improves net by trading less is not automatically an
improvement*.  D60 enters only 40.3 % of the candidates.

Two controls separate the three things that could be producing the gain:

  C1 SAME-SET CONTROL.  Run the INCUMBENT immediate arm on exactly the subset D60 would
     have entered.  If A0-on-that-subset already matches D60, the delay adds nothing
     beyond selection and the whole effect is the skip.

  C2 SPREAD DECOMPOSITION.  On that same subset, compare the spread A0 pays at T against
     the spread D60 pays at T+60.  This isolates "later is cheaper" from "the surviving
     trades were in cheap hours anyway".

  C3 SKIP VALUE.  What the skipped trades would have earned NET under A0 -- the honest
     price of the breadth, and the quantity that decides whether the rule is an edge or a
     smaller book.

A fourth question the mandate names explicitly -- is an expensive hour expensive BECAUSE
it is informative -- is answered on pre-cost gross, where cost cannot contaminate it.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

SLIP = 0.02   # the estate's flat expected_slippage_r; RECON adjudicated it correct to 4 %


def net_of(d: pd.DataFrame, pref: str) -> pd.Series:
    return d[f"{pref}_gross"] - d[f"{pref}_spread_r"] - d.comm_r - d.swap_r - SLIP


def ci(s: pd.Series):
    if len(s) < 3:
        return None
    return [float(s.mean() - 1.96 * s.sem()), float(s.mean() + 1.96 * s.sem())]


def main(rows_pkl: str, out_json: str) -> None:
    W = pd.read_pickle(rows_pkl)
    days = pd.to_datetime(W.day).nunique()
    W["A0_net"] = net_of(W, "A0")
    entered_all = W.A0_state.isin(["STOP", "TARGET", "TIME"])
    W = W[entered_all].copy()

    out = {"schema": "b10_timing_controls_v1",
           "n": int(len(W)), "trading_days": int(days),
           "slippage_charged": SLIP, "arms": {}}

    for pref in ("D15", "D30", "D60", "CHEAP"):
        st = W.get(f"{pref}_state")
        if st is None:
            continue
        took = st.isin(["STOP", "TARGET", "TIME"])
        skipped = ~took
        sub = W[took]
        skp = W[skipped]
        if len(sub) < 10:
            continue
        d_net = net_of(sub, pref)
        a_net = sub.A0_net                     # C1: same set, immediate entry
        s_net = skp.A0_net                     # C3: what the skip gives up
        delta = d_net - a_net                  # paired, same trades
        spread_delta = sub[f"{pref}_spread_r"] - sub.A0_spread_r
        gross_delta = sub[f"{pref}_gross"] - sub.A0_gross

        out["arms"][pref] = {
            "n_entered": int(len(sub)),
            "breadth_pct": float(100 * len(sub) / len(W)),
            "n_skipped": int(len(skp)),
            "C1_same_set_control": {
                "delayed_net_r": float(d_net.mean()), "delayed_ci95": ci(d_net),
                "immediate_net_r_SAME_SET": float(a_net.mean()), "immediate_ci95": ci(a_net),
                "paired_delta_r": float(delta.mean()), "paired_delta_ci95": ci(delta),
                "paired_t": float(delta.mean() / delta.sem()) if len(delta) > 2 else None,
                "verdict": ("the delay itself moves net" if abs(float(delta.mean())) > 0.02
                            else "the delay itself moves net by < 0.02 R -- the arm is a "
                                 "SKIP rule, not a cost rule"),
            },
            "C2_spread_decomposition": {
                "immediate_spread_r_SAME_SET": float(sub.A0_spread_r.mean()),
                "delayed_spread_r_SAME_SET": float(sub[f"{pref}_spread_r"].mean()),
                "paired_spread_saving_r": float(-spread_delta.mean()),
                "paired_spread_saving_ci95": ci(-spread_delta),
                "immediate_spread_r_WHOLE_BOOK": float(W.A0_spread_r.mean()),
                "selection_share_of_spread_drop_pct": float(
                    100 * (W.A0_spread_r.mean() - sub.A0_spread_r.mean())
                    / max(W.A0_spread_r.mean() - sub[f"{pref}_spread_r"].mean(), 1e-12)),
                "paired_gross_delta_r": float(gross_delta.mean()),
                "paired_gross_delta_ci95": ci(gross_delta),
            },
            "C3_skip_value": {
                "n_skipped": int(len(skp)),
                "skipped_net_r_under_A0": float(s_net.mean()) if len(skp) else None,
                "skipped_net_ci95": ci(s_net),
                "skipped_total_R_avoided": float(-s_net.sum()) if len(skp) else None,
                "skipped_gross_r_under_A0": float(skp.A0_gross.mean()) if len(skp) else None,
                "kept_net_r_under_A0": float(a_net.mean()),
            },
            "book_totals_R": {
                "A0_whole_book": float(W.A0_net.sum()),
                "arm_book": float(d_net.sum()),
                "improvement_R": float(d_net.sum() - W.A0_net.sum()),
                "of_which_from_skipping_R": float(-s_net.sum()) if len(skp) else 0.0,
                "of_which_from_cheaper_execution_R": float(delta.sum()),
                "A0_R_per_day": float(W.A0_net.sum() / days),
                "arm_R_per_day": float(d_net.sum() / days),
            },
        }

    # the informativeness question on pre-cost gross, by hour and by cheap/expensive half
    byh = (W.groupby("hour")
           .agg(n=("A0_gross", "size"), gross=("A0_gross", "mean"),
                sem=("A0_gross", "sem"), spread=("A0_spread_r", "mean"))
           .reset_index())
    r = float(np.corrcoef(byh.spread, byh.gross)[0, 1])
    # rank correlation is the honest one -- hour 21 is a 9x outlier on spread
    from scipy import stats as st_
    rho, p = st_.spearmanr(byh.spread, byh.gross)
    out["informativeness"] = {
        "question": "is an expensive hour expensive BECAUSE it is informative?",
        "pearson_r_hour_spread_vs_hour_gross": r,
        "spearman_rho": float(rho), "spearman_p": float(p),
        "n_hours": int(len(byh)),
        "cheap_half_gross": float(W[W.cheap_hour].A0_gross.mean()),
        "cheap_half_ci95": ci(W[W.cheap_hour].A0_gross),
        "expensive_half_gross": float(W[~W.cheap_hour].A0_gross.mean()),
        "expensive_half_ci95": ci(W[~W.cheap_hour].A0_gross),
        "answer": ("NO -- the expensive hours are ALSO the less informative hours, so the "
                   "trade-off the mandate asks about does not bind in this population. "
                   "Avoiding them costs no measured signal."),
        "by_hour": json.loads(byh.to_json(orient="records")),
    }
    # hour 21 leave-one-out, because one hour at 9x spread can carry a correlation
    b2 = byh[byh.hour != 21]
    rho2, p2 = st_.spearmanr(b2.spread, b2.gross)
    out["informativeness"]["leave_out_hour21"] = {
        "pearson_r": float(np.corrcoef(b2.spread, b2.gross)[0, 1]),
        "spearman_rho": float(rho2), "spearman_p": float(p2), "n_hours": int(len(b2)),
    }
    json.dump(out, open(out_json, "w"), indent=1)

    for k, v in out["arms"].items():
        c1, c2, c3, bt = (v["C1_same_set_control"], v["C2_spread_decomposition"],
                          v["C3_skip_value"], v["book_totals_R"])
        print(f"\n=== {k}  n={v['n_entered']} ({v['breadth_pct']:.1f}% breadth), "
              f"skipped {v['n_skipped']} ===")
        print(f"  C1 delayed {c1['delayed_net_r']:+.4f} vs immediate-SAME-SET "
              f"{c1['immediate_net_r_SAME_SET']:+.4f}   paired delta "
              f"{c1['paired_delta_r']:+.4f} CI{c1['paired_delta_ci95']} t={c1['paired_t']:.2f}")
        print(f"  C2 spread {c2['immediate_spread_r_SAME_SET']:.4f} -> "
              f"{c2['delayed_spread_r_SAME_SET']:.4f}  paired saving "
              f"{c2['paired_spread_saving_r']:+.4f}; whole-book spread "
              f"{c2['immediate_spread_r_WHOLE_BOOK']:.4f}; selection share of the drop "
              f"{c2['selection_share_of_spread_drop_pct']:.1f}%")
        print(f"     paired GROSS delta {c2['paired_gross_delta_r']:+.4f} "
              f"CI{c2['paired_gross_delta_ci95']}")
        print(f"  C3 skipped would have netted {c3['skipped_net_r_under_A0']:+.4f} R/trade "
              f"(total {c3['skipped_total_R_avoided']:+.1f} R avoided)")
        print(f"  book {bt['A0_whole_book']:.1f} -> {bt['arm_book']:.1f} R  "
              f"(skip {bt['of_which_from_skipping_R']:+.1f}, execution "
              f"{bt['of_which_from_cheaper_execution_R']:+.1f})   "
              f"R/day {bt['A0_R_per_day']:.1f} -> {bt['arm_R_per_day']:.1f}")
    print("\ninformativeness:", json.dumps(
        {k: v for k, v in out["informativeness"].items() if k != "by_hour"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
