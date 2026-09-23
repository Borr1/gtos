import json, collections, math
import l9_lib as L

rows = L.load()
NUM = []
r0 = rows[0]
skip = {"risk_finalizer_rank"}
for k, v in r0.items():
    if k in skip: continue
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        NUM.append(k)
# add fields that are None on row0 but numeric elsewhere
extra = ["limit_marketable_at_decision","same_symbol_exposure_risk_pct","same_side_pending_risk_pct",
         "opposite_pending_risk_pct","effective_admission_count","matched_sleeve_count",
         "mkt_r_prev_close"]
for k in extra:
    if k not in NUM: NUM.append(k)
NUM = [k for k in NUM if any(isinstance(r.get(k), (int, float)) and not isinstance(r.get(k), bool) for r in rows[:2000])]

g = L.groups(rows)

def within_group_pairs(field, target):
    """pairs of (within-group rank of `field` ascending, target value demeaned by group)"""
    pairs = []
    for t, v in g.items():
        vv = [r for r in v if r.get(field) is not None and r.get(target) is not None]
        if len(vv) < 3: continue
        mu = sum(r[target] for r in vv)/len(vv)
        order = sorted(vv, key=lambda r: r[field])
        for i, r in enumerate(order):
            pairs.append((i+1, r[target]-mu))
    return pairs

OUT = {"fields_tested": len(NUM)}
# A) what does rank correlate with (within group)?
rankmap = {}
for f in NUM:
    pairs = []
    for t, v in g.items():
        vv = [r for r in v if r.get(f) is not None]
        if len(vv) < 3: continue
        order = sorted(vv, key=lambda r: r["risk_finalizer_rank"])
        for i, r in enumerate(order):
            pairs.append((i+1, r[f]))
    sp, n = L.spearman(pairs)
    if sp: rankmap[f] = {"rho_rank_vs_field": sp["rho"], "n": n}
OUT["rank_explained_by"] = dict(sorted(rankmap.items(), key=lambda kv: -abs(kv[1]["rho_rank_vs_field"])))

# B) what predicts outcome within group (fill_honest_walk_r), takeable only
gt = L.groups([r for r in rows if r["takeable"]])
pred = {}
for f in NUM:
    for target in ["fill_honest_walk_r", "gross_r"]:
        pairs = []
        for t, v in gt.items():
            vv = [r for r in v if r.get(f) is not None and r.get(target) is not None]
            if len(vv) < 3: continue
            mu = sum(r[target] for r in vv)/len(vv)
            order = sorted(vv, key=lambda r: r[f])
            for i, r in enumerate(order):
                pairs.append((i+1, r[target]-mu))
        sp, n = L.spearman(pairs)
        if sp: pred.setdefault(target, {})[f] = {"rho": sp["rho"], "n": n, "z": sp["z_approx"]}
for target in pred:
    pred[target] = dict(sorted(pred[target].items(), key=lambda kv: -abs(kv[1]["rho"])))
OUT["within_group_predictors_TAKEABLE"] = pred

json.dump(OUT, open("L9_RANKERMAP_V1.json","w"), indent=1, default=str)
print("== rank is explained by (|rho| top 14, within-group) ==")
for f, d in list(OUT["rank_explained_by"].items())[:14]:
    print(f"  {f:>42} rho={d['rho_rank_vs_field']:+.4f} n={d['n']}")
print("== predicts fill_honest_walk_r within group (TAKEABLE, top 16) ==")
for f, d in list(pred["fill_honest_walk_r"].items())[:16]:
    print(f"  {f:>42} rho={d['rho']:+.4f} z={d['z']:+.1f} n={d['n']}")
