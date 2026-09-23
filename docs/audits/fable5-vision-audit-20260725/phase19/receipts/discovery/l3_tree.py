#!/usr/bin/env python3
"""l3_tree - DISCOVERY ONLY. A depth-3 CART on PRE-DECISION fields, fitted to the full-target
indicator, read purely as a rule-suggestion device. Every leaf it proposes is re-measured by
hand afterwards. Split-half (Jan 1-15 / Jan 16-31) so nothing here is fitted on all of January."""
import json, os
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR","/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["hit"] = (t["outcome_band"]=="ge_target").astype(int)

NUM = ["risk_distance_pct_of_price","cost_r","spread_r","candidate_probability","expected_net_r",
       "execution_fill_probability","source_bound_signal_r","implied_target_r","mkt_r_prev_close",
       "matched_sleeve_count","utc_hour","risk_per_trade_pct","commission_r","swap_cost_r",
       "setup_dup_rank","effective_admission_count","risk_finalizer_rank"]
CAT = ["symbol","origin_family","side","session_bucket","fill_realism_class","born_state",
       "scheduler_materialization_status","final_blocker_class","effective_order_type"]
X = t[NUM].astype(float).copy()
for c in CAT:
    d = pd.get_dummies(t[c].astype(str), prefix=c)
    X = pd.concat([X, d], axis=1)
X = X.fillna(-999.0)
y = t["hit"].to_numpy()

h1 = t["utc_dom"] <= 15
out = {}
for name, tr, te in (("fit_H1_test_H2", h1.to_numpy(), (~h1).to_numpy()),
                     ("fit_H2_test_H1", (~h1).to_numpy(), h1.to_numpy())):
    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=250, random_state=0)
    clf.fit(X[tr], y[tr])
    txt = export_text(clf, feature_names=list(X.columns), decimals=4)
    leaf_tr = clf.apply(X[tr]); leaf_te = clf.apply(X[te])
    rows = []
    for lf in sorted(set(leaf_tr)):
        mtr = leaf_tr == lf; mte = leaf_te == lf
        str_ = t[tr]; ste = t[te]
        rows.append({"leaf": int(lf),
                     "train_n": int(mtr.sum()), "train_hit": round(float(str_.loc[mtr,"hit"].mean()),4),
                     "train_gross_r": round(float(str_.loc[mtr,"gross_r"].mean()),4),
                     "test_n": int(mte.sum()),
                     "test_hit": (round(float(ste.loc[mte,"hit"].mean()),4) if mte.sum() else None),
                     "test_gross_r": (round(float(ste.loc[mte,"gross_r"].mean()),4) if mte.sum() else None)})
    out[name] = {"tree": txt, "leaves": rows,
                 "train_base_hit": round(float(t.loc[tr,"hit"].mean()),4),
                 "test_base_hit": round(float(t.loc[te,"hit"].mean()),4)}
json.dump(out, open(os.path.join(HERE,"l3_TREE_V1.json"),"w"), indent=1, default=str)
for k, v in out.items():
    print("===", k, "train_base", v["train_base_hit"], "test_base", v["test_base_hit"])
    print(v["tree"][:1400])
    for r in v["leaves"]:
        print(f"  leaf {r['leaf']:3d} trN {r['train_n']:5d} trHit {r['train_hit']:.4f} trR {r['train_gross_r']:+.4f} | teN {r['test_n']:5d} teHit {r['test_hit']} teR {r['test_gross_r']}")
