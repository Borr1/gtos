"""l2 step 8 — dynamic stop placement: break-even moves, trailing stops, and time stops.

Stop DISTANCE was measured k-invariant in price space (l2_02/l2_03), so it can only rescale the
bet.  A break-even move or a trail is different in kind: it changes WHICH bar the trade leaves on,
so it can move the price-space numerator.  This is the only stop lever that can.

All walks: honest fill required (resting limit at entry_price), conservative same-bar tie -> stop,
2h/120-bar horizon, structural price target held at policy_target_r.
Reported in the ORIGINAL R unit (price space, stop distance unchanged) and net of the frozen and
corrected cost.  Writes L2_DYNAMIC_STOP_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_DYNAMIC_STOP_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

CONFIGS = [("baseline", dict()),
           ("be_at_0.25", dict(be_at=0.25)), ("be_at_0.5", dict(be_at=0.5)),
           ("be_at_0.75", dict(be_at=0.75)), ("be_at_1.0", dict(be_at=1.0)),
           ("be_at_1.5", dict(be_at=1.5)),
           ("trail_0.25", dict(trail=0.25)), ("trail_0.5", dict(trail=0.5)),
           ("trail_0.75", dict(trail=0.75)), ("trail_1.0", dict(trail=1.0)),
           ("trail_1.5", dict(trail=1.5)),
           ("partial_1.0", dict(partial_at=1.0)), ("partial_0.5", dict(partial_at=0.5)),
           ("be1.0_trail1.0", dict(be_at=1.0, trail=1.0)),
           ("time_15", dict(max_bars=15)), ("time_30", dict(max_bars=30)),
           ("time_60", dict(max_bars=60)), ("time_90", dict(max_bars=90)),
           ("be0.5_time60", dict(be_at=0.5, max_bars=60)),
           ("no_stop", dict(stop_r=-1e9))]

acc = {name: {"r": [], "ex": [], "fam": [], "cost": [], "cost73": []} for name, _ in CONFIGS}
n = 0
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k)
    if r is None:
        continue
    a = anch.get(k)
    if a is not None and a["mkt_r_prev_close"] is not None and a["mkt_r_prev_close"] <= -1.0:
        continue                                  # born_past_stop: never takeable
    tgt = rp.get("policy_target_r") or 2.0
    sp = r.get("spread_r") or 0.0; cm = r.get("commission_r") or 0.0
    swp = r.get("swap_cost_r") or 0.0; sl = r.get("expected_slippage_r") or 0.0
    c1 = sp + cm + swp + sl
    c73 = sp / 7.3 + cm + swp + sl
    fam = r.get("origin_family")
    n += 1
    for name, kw in CONFIGS:
        w = w0_ws.walk(rp, target_r=tgt, require_fill=True, **kw)
        acc[name]["r"].append(w["r"]); acc[name]["ex"].append(w["exit_reason"])
        acc[name]["fam"].append(fam); acc[name]["cost"].append(c1); acc[name]["cost73"].append(c73)

res = {"n": n, "population": "filled OR not; born_past_stop excluded; require_fill=True inside walk",
       "unit": "ORIGINAL R (stop distance unchanged) -- these levers do not rescale the bet"}
base = acc["baseline"]["r"]
tab = []
for name, _ in CONFIGS:
    v = acc[name]["r"]; ex = acc[name]["ex"]
    c1 = acc[name]["cost"]; c73 = acc[name]["cost73"]
    nw = sum(1 for x in v if x > 0)
    tab.append({"config": name, "n": len(v), "gross_r": mean(v),
                "delta_vs_baseline": round((mean(v) or 0) - (mean(base) or 0), 6),
                "win_pct": round(100 * nw / len(v), 3),
                "net_frozen": round((mean(v) or 0) - (mean(c1) or 0), 6),
                "net_sp73": round((mean(v) or 0) - (mean(c73) or 0), 6),
                "exit_mix": {e: round(100 * ex.count(e) / len(ex), 2) for e in sorted(set(ex))},
                "converted_L_to_W": sum(1 for j in range(len(v)) if base[j] <= 0 < v[j]),
                "converted_W_to_L": sum(1 for j in range(len(v)) if v[j] <= 0 < base[j])})
res["configs"] = tab

# per family for the best few
fams = sorted({f for f in acc["baseline"]["fam"] if f})
pf = {}
for name in ("baseline", "be_at_0.5", "be_at_1.0", "trail_0.5", "trail_1.0", "partial_1.0",
             "time_30", "time_60", "no_stop"):
    v = acc[name]["r"]; fm = acc[name]["fam"]
    for f in fams:
        idx = [j for j in range(len(v)) if fm[j] == f]
        pf.setdefault(f, {})[name] = {"n": len(idx), "gross_r": mean([v[j] for j in idx])}
for f in pf:
    b = pf[f]["baseline"]["gross_r"]
    for name in pf[f]:
        pf[f][name]["delta"] = round((pf[f][name]["gross_r"] or 0) - (b or 0), 6)
res["per_family"] = pf

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", n)
print("%-16s %8s %9s %8s %10s %9s %7s %7s" % ("config", "gross", "delta", "win%", "netFROZEN", "net/7.3", "L>W", "W>L"))
for t in tab:
    print("%-16s %+8.5f %+9.5f %8.3f %+10.5f %+9.5f %7d %7d"
          % (t["config"], t["gross_r"], t["delta_vs_baseline"], t["win_pct"], t["net_frozen"],
             t["net_sp73"], t["converted_L_to_W"], t["converted_W_to_L"]))
