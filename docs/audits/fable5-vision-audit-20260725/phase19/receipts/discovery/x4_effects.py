#!/usr/bin/env python3
"""x4 step 1 — effect sizes of every intra-bar feature against outcome, on EXACTLY the
cohorts lane l3 used (TAKEABLE full-target winners vs TAKEABLE full stops), so the numbers
are directly comparable to l3's ceiling of |Cohen's d| = 0.152 over 28 engine fields.

Also: the same fields re-measured by l3 (control), continuous Spearman vs realised R, and
the same battery restricted to the 55.65 % bar-1 (<=60 s) touch cohort."""
import json, os, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

rows = X.load_joined()
XC = X.xcols(rows)

# l3's engine-field control set (the 28 pre-decision numerics it ranked)
CTRL = ["risk_distance_pct_of_price", "candidate_ev_r", "candidate_probability", "commission_r",
        "fill_probability", "expected_net_r", "swap_cost_r", "setup_dup_rank", "entry_price",
        "source_bound_signal_r", "cost_r", "effective_admission_count", "spread_r", "utc_hour",
        "execution_fill_probability", "risk_finalizer_rank", "expectancy_r", "spread_r",
        "expected_cost_r", "expected_slippage_r", "broker_pretrade_diag_expected_cost_r",
        "limit_fillability_probability", "entry_quality_fill_probability", "matched_sleeve_count",
        "policy_target_r", "raw_target_r", "risk_per_trade_pct", "take_profit_1",
        "same_symbol_exposure_risk_pct", "same_side_pending_risk_pct"]

take = [r for r in rows if r["takeable"]]
win = [r for r in take if r["outcome_band"] == "ge_target"]
los = [r for r in take if r["outcome_band"] == "full_stop"]

# fill-honest cohorts (only credit excursion from the fill bar onward)
hwin = [r for r in take if r.get("fill_honest_which_came_first") == "target"]
hlos = [r for r in take if r.get("fill_honest_which_came_first") == "stop"]

# the bar-1 (<=60 s) touch cohort, on takeable
bar1 = [r for r in take if r.get("bars_to_entry_touch") == 1]
b1win = [r for r in bar1 if r.get("fill_honest_which_came_first") == "target"]
b1los = [r for r in bar1 if r.get("fill_honest_which_came_first") == "stop"]


def battery(name, pos, neg, cols, cont_rows=None, cont_y="gross_r"):
    res = []
    for c in cols:
        a = [r[c] for r in pos if X._num(r.get(c))]
        b = [r[c] for r in neg if X._num(r.get(c))]
        d = X.cohend(a, b)
        if d is None:
            continue
        au = X.auc(a, b)
        t = X.welch_t(a, b)
        rec = {"feature": c, "d": round(d, 4), "auc": round(au, 4) if au else None,
               "n_pos": len(a), "n_neg": len(b),
               "mean_pos": round(X.mean(a), 6), "mean_neg": round(X.mean(b), 6),
               "welch_t": round(t, 3) if t else None,
               "p_two_sided": X.two_sided_p_from_t(t),
               "known_axis": c.replace("x4_", "") in X.KNOWN_AXIS}
        if cont_rows is not None:
            vv = [(r[c], r[cont_y]) for r in cont_rows
                  if X._num(r.get(c)) and X._num(r.get(cont_y))]
            if len(vv) > 50:
                rec["spearman_vs_" + cont_y] = round(
                    X.spearman([v[0] for v in vv], [v[1] for v in vv]), 4)
                rec["n_cont"] = len(vv)
        res.append(rec)
    res.sort(key=lambda r: -abs(r["d"]))
    return {"cohorts": name, "n_pos": len(pos), "n_neg": len(neg), "ranking": res}


out = {}
out["population"] = {
    "pool": len(rows), "takeable": len(take),
    "takeable_ge_target": len(win), "takeable_full_stop": len(los),
    "takeable_fillhonest_target": len(hwin), "takeable_fillhonest_stop": len(hlos),
    "bar1_touch_takeable": len(bar1), "bar1_target": len(b1win), "bar1_stop": len(b1los),
    "n_intrabar_features": len(XC),
}
out["A_control_engine_fields_band_cohorts"] = battery(
    "TAKEABLE ge_target vs full_stop (l3 replication)", win, los, CTRL, take, "gross_r")
out["B_intrabar_band_cohorts"] = battery(
    "TAKEABLE ge_target vs full_stop", win, los, XC, take, "gross_r")
out["C_intrabar_fillhonest_cohorts"] = battery(
    "TAKEABLE fill-honest target vs stop", hwin, hlos, XC, take, "fill_honest_walk_r")
out["D_intrabar_bar1_cohort"] = battery(
    "BAR-1 (<=60s) touch: continues (target) vs reverts (stop)", b1win, b1los, XC, bar1,
    "fill_honest_walk_r")
out["E_control_engine_fields_bar1"] = battery(
    "BAR-1 control: engine fields", b1win, b1los, CTRL, bar1, "fill_honest_walk_r")

for k in ("A_control_engine_fields_band_cohorts", "B_intrabar_band_cohorts",
          "C_intrabar_fillhonest_cohorts", "D_intrabar_bar1_cohort",
          "E_control_engine_fields_bar1"):
    top = out[k]["ranking"][:12]
    print(f"\n=== {k}  pos={out[k]['n_pos']} neg={out[k]['n_neg']} ===")
    for r in top:
        print(f"  {r['feature']:34s} d={r['d']:+.4f} auc={r['auc']} "
              f"mp={r['mean_pos']:<12} mn={r['mean_neg']:<12} known={r['known_axis']}")

json.dump(out, open(os.path.join(D, "x4_EFFECTS_V1.json"), "w"), indent=1)
print("\nwrote x4_EFFECTS_V1.json")
