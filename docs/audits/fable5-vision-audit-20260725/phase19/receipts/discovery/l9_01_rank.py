import json, collections, sys
import l9_lib as L

rows = L.load()
OUT = {}
OUT["n_rows"] = len(rows)
OUT["born_census"] = dict(collections.Counter(r["born_state"] for r in rows))

MEAS = ["gross_r", "plain_walk_r", "fill_honest_walk_r"]
for m in MEAS:
    OUT.setdefault("measure_overall", {})[m] = L.stats([r.get(m) for r in rows])

def bucket(rk):
    if rk is None: return "null"
    for hi, lab in [(1,"01"),(2,"02"),(3,"03"),(4,"04"),(5,"05"),(10,"06-10"),
                    (20,"11-20"),(40,"21-40"),(1e9,"41+")]:
        if rk <= hi: return lab
    return "41+"

def table(subset, label):
    by = collections.defaultdict(list)
    for r in subset:
        by[bucket(r["risk_finalizer_rank"])].append(r)
    t = {}
    for k in sorted(by):
        v = by[k]
        t[k] = {
            "n": len(v),
            "gross_r": L.mean([x["gross_r"] for x in v]),
            "plain_walk_r": L.mean([x.get("plain_walk_r") for x in v]),
            "fill_honest_walk_r": L.mean([x.get("fill_honest_walk_r") for x in v]),
            "win_rate_gross": sum(1 for x in v if x["gross_r"] > 0) / len(v),
            "full_stop_rate": sum(1 for x in v if x["gross_r"] <= -1 + 1e-3) / len(v),
            "share_past_stop": sum(1 for x in v if x["born_state"] == "past_stop") / len(v),
            "mean_cost_r": L.mean([x["cost_r"] for x in v]),
            "mean_risk_dist_pct": L.mean([100.0*x["risk_distance"]/x["entry_price"] for x in v if x.get("entry_price")]),
        }
    OUT.setdefault("rank_tables", {})[label] = t
    return t

table(rows, "ALL")
table([r for r in rows if r["takeable"]], "TAKEABLE_ex_past_stop")
table([r for r in rows if r["born_state"] == "past_stop"], "PAST_STOP_only")
table([r for r in rows if r["born_state"] == "at_limit"], "AT_LIMIT_only")
table([r for r in rows if r["born_state"] == "resting"], "RESTING_only")

# Spearman rank vs outcome, global and within-group (rank vs outcome demeaned by group)
for label, sub in [("ALL", rows), ("TAKEABLE", [r for r in rows if r["takeable"]])]:
    for m in MEAS:
        sp, n = L.spearman([(r["risk_finalizer_rank"], r.get(m)) for r in sub])
        OUT.setdefault("spearman_global", {})[f"{label}:{m}"] = sp

# within-group demeaned correlation: does a better rank predict a better-than-group outcome?
g = L.groups(rows)
for label, filt in [("ALL", lambda r: True), ("TAKEABLE", lambda r: r["takeable"])]:
    for m in MEAS:
        pairs = []
        for t, v in g.items():
            v2 = [r for r in v if filt(r) and r.get(m) is not None]
            if len(v2) < 2: continue
            mu = sum(r[m] for r in v2)/len(v2)
            # rank within the surviving subset, 1 = best rank number
            order = sorted(v2, key=lambda r: r["risk_finalizer_rank"])
            for i, r in enumerate(order):
                pairs.append((i+1, r[m]-mu))
        sp, n = L.spearman(pairs)
        OUT.setdefault("spearman_within_group_demeaned", {})[f"{label}:{m}"] = sp

json.dump(OUT, open("L9_RANK_V1.json","w"), indent=1, default=str)
# compact print
for lab in ["ALL","TAKEABLE_ex_past_stop"]:
    print("==", lab)
    t = OUT["rank_tables"][lab]
    print(f"{'rk':>6} {'n':>6} {'gross':>8} {'plain':>8} {'honest':>8} {'win%':>6} {'stop%':>6} {'past%':>6} {'cost':>6}")
    for k in sorted(t):
        d=t[k]
        print(f"{k:>6} {d['n']:>6} {d['gross_r']:>8.4f} {(d['plain_walk_r'] or 0):>8.4f} {(d['fill_honest_walk_r'] or 0):>8.4f} {100*d['win_rate_gross']:>6.1f} {100*d['full_stop_rate']:>6.1f} {100*d['share_past_stop']:>6.1f} {d['mean_cost_r']:>6.3f}")
print("spearman_global:", {k:(round(v['rho'],4) if v else None) for k,v in OUT["spearman_global"].items()})
print("spearman_within:", {k:(round(v['rho'],4) if v else None) for k,v in OUT["spearman_within_group_demeaned"].items()})
