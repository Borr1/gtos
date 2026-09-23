#!/usr/bin/env python3
"""l3_rules - an INTERPRETABLE profile, honestly split-half.

Enumerate every 1- and 2-condition rule over a fixed menu of PRE-DECISION predicates on the
TAKEABLE population, fit on January 1-15, score on January 16-31, and rank twice:
  (A) by full-target rate  -- the thing the mission asked for
  (B) by gross R/trade     -- the thing that pays
Report both, because l3 measured they point in OPPOSITE directions (the tighter the stop
the more often the 2R target is reached AND the more often the -1R stop is, and the pool's
gross is negative, so resolution costs money).
No rule is reported that was not measured on both halves.
"""
import json, os, itertools
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["hit"] = (t["outcome_band"] == "ge_target").astype(int)
t["honest_hit"] = (t["fill_honest_which_came_first"] == "target").astype(int)
H1 = (t["utc_dom"] <= 15).to_numpy()

# ---- the predicate menu: interpretable, pre-decision, no path/outcome fields
P = {}
rd = t["risk_distance_pct_of_price"]
for q in (0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
    P["riskdist<%.2f%%" % q] = (rd < q).to_numpy()
    P["riskdist>=%.2f%%" % q] = (rd >= q).to_numpy()
for c in (0.10, 0.15, 0.25, 0.40, 0.80):
    P["cost_r<=%.2f" % c] = (t["cost_r"] <= c).to_numpy()
    P["cost_r>%.2f" % c] = (t["cost_r"] > c).to_numpy()
for s in (0.05, 0.10, 0.20, 0.50):
    P["spread_r<=%.2f" % s] = (t["spread_r"] <= s).to_numpy()
    P["spread_r>%.2f" % s] = (t["spread_r"] > s).to_numpy()
for p in (0.70, 0.75, 0.80, 0.85):
    P["cand_prob>=%.2f" % p] = (t["candidate_probability"] >= p).to_numpy()
    P["cand_prob<%.2f" % p] = (t["candidate_probability"] < p).to_numpy()
for fam in t["origin_family"].value_counts().head(10).index:
    P["fam=%s" % fam] = (t["origin_family"] == fam).to_numpy()
    P["fam!=%s" % fam] = (t["origin_family"] != fam).to_numpy()
for sym in t["symbol"].value_counts().head(12).index:
    P["sym=%s" % sym] = (t["symbol"] == sym).to_numpy()
P["side=LONG"] = (t["side"].astype(str).str.upper().str.contains("LONG|BUY")).to_numpy()
P["side=SHORT"] = ~P["side=LONG"]
for b in t["session_bucket"].astype(str).value_counts().head(6).index:
    P["sess=%s" % b] = (t["session_bucket"].astype(str) == b).to_numpy()
for lo, hi in ((0, 6), (6, 10), (10, 14), (14, 18), (18, 24), (7, 12), (12, 17)):
    P["hour%02d-%02d" % (lo, hi)] = ((t["utc_hour"] >= lo) & (t["utc_hour"] < hi)).to_numpy()
P["born=at_limit"] = (t["born_state"] == "born_at_limit").to_numpy()
P["born=resting"] = (t["born_state"] == "born_resting").to_numpy()
P["born=marketable"] = (t["born_state"] == "born_marketable").to_numpy()
P["first_emission"] = t["is_first_emission_b"].to_numpy()
P["sched_materialized"] = (t["scheduler_materialization_status"] == "scheduler_option_materialized").to_numpy()
P["execfill>=0.90"] = (t["execution_fill_probability"] >= 0.90).fillna(False).to_numpy()
P["execfill<0.90"] = (t["execution_fill_probability"] < 0.90).fillna(False).to_numpy()
P["swap_r>0.0088"] = (t["swap_cost_r"] > 0.0088).to_numpy()
P["dup_rank=1"] = (t["setup_dup_rank"] == 1).to_numpy()

names = list(P.keys())
hit = t["hit"].to_numpy(); hhit = t["honest_hit"].to_numpy()
gr = t["gross_r"].to_numpy(); fh = t["fill_honest_walk_r"].to_numpy()
MIN_N = 300

def score(mask):
    m1 = mask & H1; m2 = mask & ~H1
    if m1.sum() < MIN_N or m2.sum() < MIN_N:
        return None
    return {"n": int(mask.sum()), "n_h1": int(m1.sum()), "n_h2": int(m2.sum()),
            "hit_h1": round(float(hit[m1].mean()), 5), "hit_h2": round(float(hit[m2].mean()), 5),
            "honest_hit_h1": round(float(hhit[m1].mean()), 5), "honest_hit_h2": round(float(hhit[m2].mean()), 5),
            "gross_h1": round(float(gr[m1].mean()), 5), "gross_h2": round(float(gr[m2].mean()), 5),
            "fh_h1": round(float(fh[m1].mean()), 5), "fh_h2": round(float(fh[m2].mean()), 5),
            "hit_all": round(float(hit[mask].mean()), 5), "gross_all": round(float(gr[mask].mean()), 5),
            "fh_all": round(float(fh[mask].mean()), 5)}

base = score(np.ones(len(t), dtype=bool))
res = []
for nm in names:
    s = score(P[nm])
    if s: s["rule"] = nm; s["k"] = 1; res.append(s)
for a, b in itertools.combinations(names, 2):
    m = P[a] & P[b]
    if m.sum() < 2 * MIN_N: continue
    s = score(m)
    if s: s["rule"] = a + " AND " + b; s["k"] = 2; res.append(s)

out = {"population": "TAKEABLE", "n": int(len(t)), "min_n_per_half": MIN_N,
       "n_predicates": len(names), "n_rules_scored": len(res), "base": base,
       "split": "H1 = January 1-15 (n=%d), H2 = January 16-31 (n=%d)" % (int(H1.sum()), int((~H1).sum()))}
byhit = sorted(res, key=lambda d: -min(d["hit_h1"], d["hit_h2"]))[:40]
bygr = sorted(res, key=lambda d: -min(d["gross_h1"], d["gross_h2"]))[:40]
out["top_by_full_target_rate"] = byhit
out["top_by_gross_r"] = bygr
out["all_rules"] = res
json.dump(out, open(os.path.join(HERE, "l3_RULES_V1.json"), "w"), indent=1, default=str)

print("base: n=%d hit_h1=%.4f hit_h2=%.4f gross_h1=%+.4f gross_h2=%+.4f" % (
    base["n"], base["hit_h1"], base["hit_h2"], base["gross_h1"], base["gross_h2"]))
print("rules scored=%d (predicates=%d)" % (len(res), len(names)))
print("--- TOP 14 by worst-half FULL-TARGET RATE")
print("%-56s %6s %7s %7s %8s %8s" % ("rule", "n", "hit_h1", "hit_h2", "gr_h1", "gr_h2"))
for r in byhit[:14]:
    print("%-56s %6d %7.4f %7.4f %+8.4f %+8.4f" % (r["rule"][:56], r["n"], r["hit_h1"], r["hit_h2"], r["gross_h1"], r["gross_h2"]))
print("--- TOP 14 by worst-half GROSS R")
print("%-56s %6s %7s %7s %8s %8s" % ("rule", "n", "gr_h1", "gr_h2", "hit_h1", "hit_h2"))
for r in bygr[:14]:
    print("%-56s %6d %+7.4f %+7.4f %8.4f %8.4f" % (r["rule"][:56], r["n"], r["gross_h1"], r["gross_h2"], r["hit_h1"], r["hit_h2"]))
