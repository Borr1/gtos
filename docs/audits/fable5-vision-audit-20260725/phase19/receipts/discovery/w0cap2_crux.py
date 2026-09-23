"""THE CRUX: was the 'untakeable' population born past its own stop, or did price collapse
through a legitimate resting limit in the 60s the path cannot see?"""
import sys, os, json, gzip, statistics as st
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

rows = w0_ws.load()
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

# recompute the fill classification from the R-paths (prior lane's rule, independently)
fillcls = {}
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    fav, adv = rp["fav"], rp["adv"]
    t = None
    for i in range(len(adv)):
        if adv[i] <= 0.0: t = i; break
    if t is None:
        fillcls[k] = ("never", None, None)
    else:
        f = fav[t]
        c = "untakeable" if f <= -1.0 else ("gap" if f < 0.0 else "clean")
        fillcls[k] = (c, f, t + 1)

def pct(a, b): return round(100.0 * a / b, 4) if b else None
def q(v, p):
    if not v: return None
    s = sorted(v); i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
    return round(s[i], 4)
def summ(v):
    if not v: return {"n": 0}
    return {"n": len(v), "mean": round(sum(v)/len(v), 4), "p05": q(v,.05), "p25": q(v,.25),
            "median": q(v,.5), "p75": q(v,.75), "p95": q(v,.95), "min": round(min(v),4), "max": round(max(v),4)}

# --- born-state classification at DECISION TIME -------------------------------------------
def born(a):
    m = a["mkt_r_close"]
    if m <= -1.0: return "born_past_stop"
    if m < 0.0:   return "born_marketable"
    if m == 0.0:  return "born_at_limit"
    return "born_resting"

res = {"n_rows": len(rows), "n_anchored": len(anch)}
cross = {}
bornbook = {}
mkt_by_fill = {}
for r in rows:
    k = w0_ws.key(r)
    a = anch.get(k)
    if a is None: continue
    fc = fillcls.get(k, ("?", None, None))[0]
    bs = born(a)
    cross.setdefault(bs, {}).setdefault(fc, []).append(r.get("gross_r"))
    bornbook.setdefault(bs, []).append(r.get("gross_r"))
    mkt_by_fill.setdefault(fc, []).append(a["mkt_r_close"])

res["born_state_book"] = {b: {"n": len(v), "share_pct": pct(len(v), len(anch)),
                              "engine_gross_r": round(sum(x for x in v if x is not None)/max(1,len([x for x in v if x is not None])), 5),
                              "win_pct": pct(len([x for x in v if x is not None and x > 0]), len([x for x in v if x is not None]))}
                          for b, v in sorted(bornbook.items())}
res["cross_born_x_fill"] = {b: {f: {"n": len(v),
                                    "engine_gross_r": round(sum(x for x in v if x is not None)/max(1,len([x for x in v if x is not None])), 5)}
                                for f, v in sorted(d.items())} for b, d in sorted(cross.items())}
res["mkt_r_at_decision_by_fill_class"] = {f: summ(v) for f, v in sorted(mkt_by_fill.items())}

# --- the decisive number: of the untakeable rows, what were they at decision? --------------
unt = [(r, anch[w0_ws.key(r)]) for r in rows if w0_ws.key(r) in anch and fillcls.get(w0_ws.key(r), ("?",))[0] == "untakeable"]
mk = [a["mkt_r_close"] for _, a in unt]
res["UNTAKEABLE_AT_DECISION"] = {
    "n": len(unt),
    "mkt_r_close": summ(mk),
    "already_past_stop_at_decision_n": sum(1 for m in mk if m <= -1.0),
    "already_past_stop_at_decision_pct": pct(sum(1 for m in mk if m <= -1.0), len(mk)),
    "already_through_limit_at_decision_n": sum(1 for m in mk if m < 0.0),
    "already_through_limit_at_decision_pct": pct(sum(1 for m in mk if m < 0.0), len(mk)),
    "resting_at_decision_n": sum(1 for m in mk if m > 0.0),
    "resting_at_decision_pct": pct(sum(1 for m in mk if m > 0.0), len(mk)),
    "bar_range_also_past_stop_n": sum(1 for _, a in unt if max(a["mkt_r_high"], a["mkt_r_low"]) <= -1.0),
    "prev_close_past_stop_n": sum(1 for _, a in unt if a["mkt_r_prev_close"] <= -1.0),
}
with open(os.path.join(D, "W0CAP2_CRUX_V1.json"), "w") as f: json.dump(res, f, indent=1)
print(json.dumps(res["born_state_book"], indent=1))
print("UNTAKEABLE:", json.dumps(res["UNTAKEABLE_AT_DECISION"], indent=1))
