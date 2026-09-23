#!/usr/bin/env python3
"""l3_unused - which fields SHOULD predict outcome and do not, which do unexpectedly,
and the ORDERING defect: the pool's single strongest discriminator is encoded in a field
the engine computes only AFTER the gate that would have used it has already fired.
"""
import json, os
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
out = {}

# ---- 1. ORDERING: limit_marketable_at_decision vs born_state
lm = df["limit_marketable_at_decision"]
out["ordering_defect"] = {
    "field": "limit_marketable_at_decision",
    "writer": "src/components/poi_execution_lifecycle.py:224",
    "consumers": ["src/research/moonshot_scheduler_v4_best_trade_allocator.py:17462",
                  ":17530", ":17820", ":18386"],
    "n_nonnull": int(lm.notna().sum()), "n_null": int(lm.isna().sum()),
    "pct_null": round(100.0 * float(lm.isna().mean()), 3),
    "n_scheduler_materialized": int((df["scheduler_materialization_status"] == "scheduler_option_materialized").sum()),
    "nonnull_equals_materialized": bool(lm.notna().sum() == (df["scheduler_materialization_status"] == "scheduler_option_materialized").sum()),
}
for st in ("born_past_stop", "born_marketable", "born_at_limit", "born_resting"):
    s = df[df["born_state"] == st]
    out["ordering_defect"]["by_born_state_" + st] = {
        "n": int(len(s)),
        "limit_marketable_nonnull_n": int(s["limit_marketable_at_decision"].notna().sum()),
        "limit_marketable_nonnull_pct": round(100.0 * float(s["limit_marketable_at_decision"].notna().mean()), 3),
        "mean_gross_r": round(float(s["gross_r"].mean()), 5),
        "pct_refused_by_cost_gates": round(100.0 * float(((s["spread_r"] > 0.10) | (s["cost_r"] > 0.15)).mean()), 3),
    }

# ---- 2. discriminating power on TAKEABLE, PRE-decision only, ranked
t = df[df["takeable"]].copy()
t["hit"] = (t["outcome_band"] == "ge_target").astype(int)
t["hhit"] = (t["fill_honest_which_came_first"] == "target").astype(int)
CAND = ["candidate_probability", "candidate_ev_r", "expected_net_r", "fill_probability",
        "execution_fill_probability", "source_bound_signal_r", "matched_sleeve_count",
        "effective_admission_count", "risk_finalizer_rank", "cost_r", "spread_r",
        "commission_r", "swap_cost_r", "risk_distance_pct_of_price", "implied_target_r",
        "risk_per_trade_pct", "same_symbol_exposure_risk_pct", "same_side_pending_risk_pct",
        "opposite_pending_risk_pct", "setup_dup_rank", "utc_hour", "abs_entry_offset_r",
        "mkt_r_prev_close", "broker_pretrade_diag_expected_cost_r", "expected_slippage_r"]
rk = []
for c in CAND:
    if c not in t.columns:
        continue
    m = t[[c, "hit", "hhit", "gross_r", "fill_honest_walk_r"]].dropna()
    if len(m) < 200 or m[c].nunique() < 3:
        continue
    rk.append({
        "field": c, "n": int(len(m)), "n_distinct": int(m[c].nunique()),
        "rho_vs_hit_target": round(float(stats.spearmanr(m[c], m["hit"]).statistic), 5),
        "rho_vs_honest_hit": round(float(stats.spearmanr(m[c], m["hhit"]).statistic), 5),
        "rho_vs_gross_r": round(float(stats.spearmanr(m[c], m["gross_r"]).statistic), 5),
        "rho_vs_fill_honest_r": round(float(stats.spearmanr(m[c], m["fill_honest_walk_r"]).statistic), 5),
    })
rk.sort(key=lambda d: -abs(d["rho_vs_gross_r"]))
out["pre_decision_power_takeable"] = rk

# ---- 3. constants: computed, emitted, and carrying zero information
const = {}
for c in df.columns:
    s = df[c]
    try:
        nd = s.nunique(dropna=True)
    except Exception:
        continue
    if nd == 1 and s.notna().sum() == len(df):
        const[c] = str(s.dropna().iloc[0])
out["zero_information_constants"] = const

# ---- 4. the belief field that cannot vary
out["candidate_confidence"] = {
    "n_distinct": int(df["candidate_confidence"].nunique()),
    "value": str(df["candidate_confidence"].dropna().iloc[0]) if df["candidate_confidence"].notna().any() else None,
    "confidence_default_applied_true_pct": round(100.0 * float(df["confidence_default_applied"].astype(str).eq("True").mean()), 3),
    "note": "constant -> cannot correlate with anything; it is not a belief, it is a placeholder",
}

# ---- 5. the one place belief WORKS
lsr = t[t["origin_family"] == "liquidity_sweep_reclaim"]
q = pd.qcut(lsr["candidate_probability"], 5, labels=False, duplicates="drop")
tab = []
for k, s in lsr.assign(_q=q).groupby("_q"):
    tab.append({"quintile": int(k) + 1, "n": int(len(s)),
                "cand_prob": round(float(s["candidate_probability"].mean()), 5),
                "hit": round(float((s["outcome_band"] == "ge_target").mean()), 5),
                "honest_hit": round(float((s["fill_honest_which_came_first"] == "target").mean()), 5),
                "gross_r": round(float(s["gross_r"].mean()), 5),
                "fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 5)})
out["belief_inside_liquidity_sweep_reclaim"] = {
    "n": int(len(lsr)),
    "rho_belief_vs_gross": round(float(stats.spearmanr(lsr["candidate_probability"], lsr["gross_r"]).statistic), 5),
    "rho_belief_vs_fill_honest": round(float(stats.spearmanr(lsr["candidate_probability"], lsr["fill_honest_walk_r"]).statistic), 5),
    "quintiles": tab}

json.dump(out, open(os.path.join(HERE, "l3_UNUSED_V1.json"), "w"), indent=1, default=str)

o = out["ordering_defect"]
print("limit_marketable_at_decision: %.2f%% null (n_nonnull=%d == scheduler_materialized=%d -> %s)" % (
    o["pct_null"], o["n_nonnull"], o["n_scheduler_materialized"], o["nonnull_equals_materialized"]))
for st in ("born_past_stop", "born_marketable", "born_at_limit", "born_resting"):
    b = o["by_born_state_" + st]
    print("  %-16s n=%5d  field populated on %6.2f%%  gross=%+.4f  cost-gate refuses %.1f%%" % (
        st, b["n"], b["limit_marketable_nonnull_pct"], b["mean_gross_r"], b["pct_refused_by_cost_gates"]))
print("--- PRE-decision power on TAKEABLE (spearman)")
print("%-36s %8s %10s %10s %10s" % ("field", "n", "rho_hit", "rho_gross", "rho_fhR"))
for r in rk[:18]:
    print("%-36s %8d %+10.4f %+10.4f %+10.4f" % (r["field"], r["n"], r["rho_vs_hit_target"], r["rho_vs_gross_r"], r["rho_vs_fill_honest_r"]))
print("ZERO-INFO CONSTANTS (%d):" % len(const), json.dumps(const))
print("BELIEF inside liquidity_sweep_reclaim: rho_gross=%+.4f rho_fh=%+.4f" % (
    out["belief_inside_liquidity_sweep_reclaim"]["rho_belief_vs_gross"],
    out["belief_inside_liquidity_sweep_reclaim"]["rho_belief_vs_fill_honest"]))
for r in tab:
    print("  q%d n=%4d p=%.4f hit=%.4f hon=%.4f gross=%+.4f fh=%+.4f" % (
        r["quintile"], r["n"], r["cand_prob"], r["hit"], r["honest_hit"], r["gross_r"], r["fill_honest_walk_r"]))
