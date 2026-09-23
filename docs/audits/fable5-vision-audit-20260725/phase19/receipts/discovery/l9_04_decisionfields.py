import json, collections, math
import l9_lib as L

rows = L.load()
for r in rows:
    ep = r.get("entry_price")
    r["risk_distance_pct"] = (100.0*r["risk_distance"]/ep) if ep else None
    r["neg_cost_r"] = -r["cost_r"] if r.get("cost_r") is not None else None

DT = ["risk_finalizer_rank","candidate_probability","candidate_ev_r","expectancy_r","candidate_confidence",
      "cost_r","expected_cost_r","spread_r","commission_r","swap_cost_r","expected_slippage_r",
      "expected_net_r","execution_fill_probability","fill_probability","entry_quality_fill_probability",
      "limit_fillability_probability","risk_distance","risk_distance_pct","risk_per_trade_pct",
      "policy_target_r","raw_target_r","matched_sleeve_count","effective_admission_count",
      "same_symbol_exposure_risk_pct","same_side_pending_risk_pct","opposite_pending_risk_pct",
      "source_bound_signal_r","old_proxy_vs_broker_calibrated_delta_r",
      "broker_pretrade_diag_expected_cost_r","fallback_execution_surcharge_r",
      "guarded_market_fallback_extra_cost_r","mkt_r_prev_close","neg_cost_r"]

def wg(sub, field, target):
    g = L.groups(sub)
    pairs = []
    for t, v in g.items():
        vv = [r for r in v if r.get(field) is not None and r.get(target) is not None]
        if len(vv) < 3: continue
        mu = sum(r[target] for r in vv)/len(vv)
        order = sorted(vv, key=lambda r: r[field])
        for i, r in enumerate(order):
            pairs.append((i+1, r[target]-mu))
    return L.spearman(pairs)[0]

OUT = {}
tk = [r for r in rows if r["takeable"]]
for label, sub in [("ALL", rows), ("TAKEABLE", tk)]:
    for target in ["fill_honest_walk_r", "gross_r"]:
        d = {}
        for f in DT:
            sp = wg(sub, f, target)
            if sp: d[f] = {"rho": round(sp["rho"],4), "z": round(sp["z_approx"],1), "n": sp["n"]}
        OUT.setdefault(f"{label}:{target}", {}).update(dict(sorted(d.items(), key=lambda kv: -abs(kv[1]["rho"]))))

# within-group rank PERCENTILE table (controls for group size)
def pct_table(sub, label):
    g = L.groups(sub)
    by = collections.defaultdict(list)
    for t, v in g.items():
        if len(v) < 4: continue
        order = sorted(v, key=lambda r: r["risk_finalizer_rank"])
        n = len(order)
        for i, r in enumerate(order):
            q = min(4, int(5.0*i/n))
            by[q].append(r)
    t = {}
    for q in sorted(by):
        v = by[q]
        t[f"Q{q+1}"] = {"n": len(v),
                        "gross_r": L.mean([x["gross_r"] for x in v]),
                        "fill_honest_walk_r": L.mean([x.get("fill_honest_walk_r") for x in v]),
                        "plain_walk_r": L.mean([x.get("plain_walk_r") for x in v]),
                        "cost_r": L.mean([x["cost_r"] for x in v]),
                        "risk_distance_pct": L.mean([x["risk_distance_pct"] for x in v]),
                        "share_past_stop": sum(1 for x in v if x["born_state"]=="past_stop")/len(v),
                        "mean_abs_rank": L.mean([x["risk_finalizer_rank"] for x in v])}
    OUT.setdefault("within_group_quintile", {})[label] = t
    return t

pct_table(rows, "ALL"); pct_table(tk, "TAKEABLE")
json.dump(OUT, open("L9_DECISIONFIELDS_V1.json","w"), indent=1, default=str)

for k in ["TAKEABLE:fill_honest_walk_r","ALL:gross_r"]:
    print("==", k)
    for f, d in list(OUT[k].items())[:12]:
        print(f"   {f:>38} rho={d['rho']:+.4f} z={d['z']:+.1f}")
for lab in ["ALL","TAKEABLE"]:
    print("== within-group rank quintile:", lab)
    t = OUT["within_group_quintile"][lab]
    print(f"{'Q':>3} {'n':>6} {'gross':>8} {'honest':>8} {'plain':>8} {'cost':>6} {'rdpct':>7} {'past%':>6} {'absrk':>6}")
    for q in sorted(t):
        d=t[q]
        print(f"{q:>3} {d['n']:>6} {d['gross_r']:>8.4f} {d['fill_honest_walk_r']:>8.4f} {d['plain_walk_r']:>8.4f} {d['cost_r']:>6.3f} {d['risk_distance_pct']:>7.4f} {100*d['share_past_stop']:>6.1f} {d['mean_abs_rank']:>6.1f}")
