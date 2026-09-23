#!/usr/bin/env python3
"""l3_profile - the descriptive answer to 'what does a trade we want look like'.

Population: TAKEABLE (24,125) -- born_past_stop dropped, because 23.40 % of the briefed
full-stop cohort is the W0-capture artifact and 0.10 % of the winner cohort is, so the
briefed 3,072-vs-15,057 comparison is contaminated on ONE side only.

Cohorts, both reported for every cut:
  BRIEFED  outcome_band == ge_target (n=3,069)   vs  full_stop (n=11,534)
  HONEST   fill_honest_which_came_first == target (n=3,709) vs stop (n=12,331)

Every categorical cut carries n, win/stop counts, win-share, lift vs the cut's base rate,
mean gross R, mean fill-honest R, and mean risk distance -- because risk distance is the
axis everything else rides on (see l3_COHORT_INTEGRITY_V1.json risk_distance_decile).
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["BW"] = t["outcome_band"] == "ge_target"
t["BS"] = t["outcome_band"] == "full_stop"
t["HW"] = t["fill_honest_which_came_first"] == "target"
t["HS"] = t["fill_honest_which_came_first"] == "stop"

CUTS = ["origin_family", "symbol", "side", "session_bucket", "utc_hour", "utc_dow",
        "born_state", "decision_timeframe", "fill_realism_class", "kill_zone",
        "risk_per_trade_pct", "dynamic_geometry_policy", "setup_family",
        "scheduler_materialization_status", "final_blocker_class", "effective_order_type",
        "selected_policy_for_expected_net_r", "route_session", "market_timeframe"]

base_b = t["BW"].sum() / (t["BW"].sum() + t["BS"].sum())
base_h = t["HW"].sum() / (t["HW"].sum() + t["HS"].sum())
out = {"population": "TAKEABLE", "n": int(len(t)),
       "briefed_base_win_share": round(float(base_b), 5),
       "honest_base_win_share": round(float(base_h), 5),
       "briefed_n_win": int(t["BW"].sum()), "briefed_n_stop": int(t["BS"].sum()),
       "honest_n_win": int(t["HW"].sum()), "honest_n_stop": int(t["HS"].sum()),
       "cuts": {}}

for c in CUTS:
    if c not in t.columns:
        continue
    rows = []
    for lvl, s in t.groupby(t[c].astype(str), dropna=False):
        if len(s) < 30:
            continue
        bw, bs = int(s["BW"].sum()), int(s["BS"].sum())
        hw, hs = int(s["HW"].sum()), int(s["HS"].sum())
        rows.append({
            "level": str(lvl), "n": int(len(s)),
            "briefed_win": bw, "briefed_stop": bs,
            "briefed_win_share": round(bw / max(1, bw + bs), 5),
            "briefed_lift": round((bw / max(1, bw + bs)) / base_b, 4),
            "hit_target_rate_of_cell": round(bw / len(s), 5),
            "honest_win": hw, "honest_stop": hs,
            "honest_win_share": round(hw / max(1, hw + hs), 5),
            "honest_lift": round((hw / max(1, hw + hs)) / base_h, 4),
            "gross_r": round(float(s["gross_r"].mean()), 5),
            "fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 5),
            "neither_rate": round(float((s["which_came_first"] == "neither").mean()), 5),
            "risk_dist_pct": round(float(s["risk_distance_pct_of_price"].mean()), 5),
            "median_risk_dist_pct": round(float(s["risk_distance_pct_of_price"].median()), 5),
            "cost_r": round(float(s["cost_r"].mean()), 5),
            "mfe_r": round(float(s["mfe_r"].mean()), 5),
            "cand_prob": round(float(s["candidate_probability"].mean()), 5),
        })
    out["cuts"][c] = sorted(rows, key=lambda d: -d["n"])

# ---- continuous winner-vs-stop profile: means in each cohort, both definitions
NUMS = ["risk_distance_pct_of_price", "cost_r", "spread_r", "commission_r", "swap_cost_r",
        "candidate_probability", "candidate_ev_r", "expected_net_r", "execution_fill_probability",
        "fill_probability", "source_bound_signal_r", "implied_target_r", "mkt_r_prev_close",
        "abs_entry_offset_r", "matched_sleeve_count", "effective_admission_count",
        "risk_finalizer_rank", "utc_hour", "setup_dup_rank", "same_symbol_exposure_risk_pct",
        "same_side_pending_risk_pct", "opposite_pending_risk_pct", "entry_price", "risk_distance",
        "policy_target_r", "raw_target_r", "expected_slippage_r", "broker_pretrade_diag_expected_cost_r"]
prof = {}
for c in NUMS:
    if c not in t.columns:
        continue
    a = pd.to_numeric(t.loc[t["BW"], c], errors="coerce")
    b = pd.to_numeric(t.loc[t["BS"], c], errors="coerce")
    ah = pd.to_numeric(t.loc[t["HW"], c], errors="coerce")
    bh = pd.to_numeric(t.loc[t["HS"], c], errors="coerce")
    if a.notna().sum() < 30 or b.notna().sum() < 30:
        continue
    sp = np.sqrt(((a.count() - 1) * a.std() ** 2 + (b.count() - 1) * b.std() ** 2) / max(1, a.count() + b.count() - 2))
    prof[c] = {
        "briefed_mean_win": round(float(a.mean()), 6), "briefed_mean_stop": round(float(b.mean()), 6),
        "briefed_median_win": round(float(a.median()), 6), "briefed_median_stop": round(float(b.median()), 6),
        "briefed_mean_diff": round(float(a.mean() - b.mean()), 6),
        "briefed_cohens_d": (round(float((a.mean() - b.mean()) / sp), 4) if sp and sp > 0 else None),
        "honest_mean_win": round(float(ah.mean()), 6), "honest_mean_stop": round(float(bh.mean()), 6),
        "honest_mean_diff": round(float(ah.mean() - bh.mean()), 6),
        "n_win": int(a.count()), "n_stop": int(b.count()),
    }
out["numeric_profile"] = prof

json.dump(out, open(os.path.join(HERE, "l3_PROFILE_V1.json"), "w"), indent=1, default=str)

print("TAKEABLE n=%d  briefed base=%.5f (%d/%d)  honest base=%.5f (%d/%d)" % (
    len(t), base_b, t["BW"].sum(), t["BS"].sum(), base_h, t["HW"].sum(), t["HS"].sum()))
for c in ("origin_family", "symbol"):
    print("--- %s" % c)
    print("  %-32s %6s %7s %6s %7s %6s %8s %8s %7s" % ("level", "n", "bWin%", "lift", "hWin%", "hlift", "gross", "riskD%", "neith%"))
    for r in out["cuts"][c][:14]:
        print("  %-32s %6d %7.2f %6.2f %7.2f %6.2f %+8.4f %8.4f %7.1f" % (
            r["level"][:32], r["n"], 100 * r["briefed_win_share"], r["briefed_lift"],
            100 * r["honest_win_share"], r["honest_lift"], r["gross_r"], r["risk_dist_pct"], 100 * r["neither_rate"]))
print("--- top |cohens_d| numeric fields (briefed win vs stop)")
rk = sorted([(abs(v["briefed_cohens_d"] or 0), k, v) for k, v in prof.items()], reverse=True)
print("  %-34s %8s %10s %10s %9s" % ("field", "d", "mean_win", "mean_stop", "hon_diff"))
for d_, k, v in rk[:16]:
    print("  %-34s %8.4f %10.5f %10.5f %+9.5f" % (k, v["briefed_cohens_d"], v["briefed_mean_win"], v["briefed_mean_stop"], v["honest_mean_diff"]))
