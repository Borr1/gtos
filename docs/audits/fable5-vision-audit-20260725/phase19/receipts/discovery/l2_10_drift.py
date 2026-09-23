"""l2 step 10 — if no stop rule moves the number, the excursion process itself must be driftless.
Test it directly.

Measures, on the honest population (ex-born_past_stop, entry actually touched), the mean
close-based R at bars 5/15/30/60/120 and the mean MFE/MAE at each of those bars.  A trade with a
real entry edge drifts favourably; a martingale does not.  Symmetry of the excursion envelope
(|MAE| vs MFE) is the second test: an edge shows up as MFE > |MAE| long before any exit rule.
Writes L2_DRIFT_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_DRIFT_V1.json")
BK = [5, 15, 30, 60, 120]


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


def med(v):
    v = sorted(x for x in v if x is not None)
    return round(v[len(v) // 2], 6) if v else None


rows = w0_ws.load()
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

pop = []
for r in rows:
    a = anch.get(w0_ws.key(r))
    if a is not None and a["mkt_r_prev_close"] is not None and a["mkt_r_prev_close"] <= -1.0:
        continue
    if not r.get("entry_touched"):
        continue
    pop.append(r)
IMM = [r for r in pop if r.get("bars_to_entry_touch") == 1]

res = {"n_honest_entry_touched": len(pop), "n_immediate_fill_bar1": len(IMM),
       "note": "r_at_bar_K is close-based, NO stop and NO target applied -- the raw excursion process"}


def blk(v):
    o = {"n": len(v)}
    for K in BK:
        o["bar%d" % K] = {"mean_r": mean([x.get("r_at_bar_%d" % K) for x in v]),
                          "median_r": med([x.get("r_at_bar_%d" % K) for x in v]),
                          "mean_mfe": mean([x.get("mfe_r_by_bar_%d" % K) for x in v]),
                          "mean_mae": mean([x.get("mae_r_by_bar_%d" % K) for x in v]),
                          "envelope_asymmetry": round((mean([x.get("mfe_r_by_bar_%d" % K) for x in v]) or 0)
                                                      + (mean([x.get("mae_r_by_bar_%d" % K) for x in v]) or 0), 6),
                          "share_positive_pct": round(100 * sum(1 for x in v if (x.get("r_at_bar_%d" % K) or 0) > 0)
                                                      / len(v), 3)}
    o["mean_r_at_path_end"] = mean([x.get("r_at_path_end") for x in v])
    o["mean_mfe_full"] = mean([x.get("mfe_r") for x in v])
    o["mean_mae_full"] = mean([x.get("mae_r") for x in v])
    o["envelope_asymmetry_full"] = round((mean([x.get("mfe_r") for x in v]) or 0)
                                         + (mean([x.get("mae_r") for x in v]) or 0), 6)
    return o


res["ALL_entry_touched"] = blk(pop)
res["IMMEDIATE_fill_bar1"] = blk(IMM)
res["per_family"] = {}
g = {}
for r in pop:
    g.setdefault(r.get("origin_family"), []).append(r)
for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(v) < 60:
        continue
    b = blk(v)
    res["per_family"][str(k)] = {"n": b["n"],
                                 "r_bar5": b["bar5"]["mean_r"], "r_bar15": b["bar15"]["mean_r"],
                                 "r_bar30": b["bar30"]["mean_r"], "r_bar60": b["bar60"]["mean_r"],
                                 "r_bar120": b["bar120"]["mean_r"],
                                 "r_end": b["mean_r_at_path_end"],
                                 "mfe_full": b["mean_mfe_full"], "mae_full": b["mean_mae_full"],
                                 "envelope_asym_full": b["envelope_asymmetry_full"]}
res["per_symbol"] = {}
g = {}
for r in pop:
    g.setdefault(r["symbol"], []).append(r)
for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(v) < 60:
        continue
    b = blk(v)
    res["per_symbol"][str(k)] = {"n": b["n"], "r_bar15": b["bar15"]["mean_r"], "r_bar60": b["bar60"]["mean_r"],
                                 "r_bar120": b["bar120"]["mean_r"], "r_end": b["mean_r_at_path_end"],
                                 "envelope_asym_full": b["envelope_asymmetry_full"]}
with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
for lab in ("ALL_entry_touched", "IMMEDIATE_fill_bar1"):
    b = res[lab]
    print(lab, "n=", b["n"])
    for K in BK:
        x = b["bar%d" % K]
        print("   bar%-4d mean_r=%+.5f med=%+.5f mfe=%+.5f mae=%+.5f asym=%+.5f pos%%=%.2f"
              % (K, x["mean_r"], x["median_r"], x["mean_mfe"], x["mean_mae"], x["envelope_asymmetry"],
                 x["share_positive_pct"]))
    print("   full mfe=%+.5f mae=%+.5f asym=%+.5f r_end=%+.5f"
          % (b["mean_mfe_full"], b["mean_mae_full"], b["envelope_asymmetry_full"], b["mean_r_at_path_end"]))
print("--- family: raw drift, no exit rule ---")
for k, v in res["per_family"].items():
    print("%-34s n=%5d b5=%+.4f b15=%+.4f b30=%+.4f b60=%+.4f b120=%+.4f end=%+.4f asym=%+.4f"
          % (k[:34], v["n"], v["r_bar5"], v["r_bar15"], v["r_bar30"], v["r_bar60"], v["r_bar120"],
             v["r_end"], v["envelope_asym_full"]))
