"""l2 step 11 — WHEN is the loss created?  Minute by minute from the fill.

l2_10 measured that for trades filled on path bar 1 the mean close-based R is already -0.246 at
bar 5 and is FLAT (-0.246 -> -0.198) for the next 115 minutes.  That is a martingale after minute
five and locates the entire deficit at, or immediately after, the fill.  This step resolves it to
the minute and splits it by born state, because the two states are different order types:
   born_at_limit  (entry_price == the market price at the decision instant) -> a market order
   born_resting   (entry_price away from the market)                        -> a true resting limit
   born_marketable(entry through the market, stop intact)                   -> immediately fillable
Writes L2_FIRST_MINUTES_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_FIRST_MINUTES_V1.json")
MAXB = 20


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

groups = {}          # label -> list of per-bar-offset lists
meta = {}


def add(lab, rel, sp):
    g = groups.setdefault(lab, [[] for _ in range(MAXB)])
    for j in range(min(MAXB, len(rel))):
        g[j].append(rel[j])
    meta.setdefault(lab, {"n": 0, "spread_r_sum": 0.0})
    meta[lab]["n"] += 1
    meta[lab]["spread_r_sum"] += sp


for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k)
    if r is None:
        continue
    a = anch.get(k)
    m = a["mkt_r_prev_close"] if a else None
    if m is not None and m <= -1.0:
        continue
    adv, cls = rp["adv"], rp["cls"]
    fb = next((i for i in range(len(adv)) if adv[i] <= 0.0), None)
    if fb is None:
        continue
    born = ("born_marketable" if (m is not None and m < 0.0) else
            "born_at_limit" if m == 0.0 else "born_resting" if m is not None else "unknown")
    sp = r.get("spread_r") or 0.0
    rel = cls[fb:fb + MAXB]                    # close-based R, indexed from the FILL bar
    add("ALL", rel, sp)
    add(born, rel, sp)
    if fb == 0:
        add("filled_on_bar1", rel, sp)
    else:
        add("filled_later", rel, sp)
    fam = r.get("origin_family")
    if fam:
        add("fam:" + fam, rel, sp)

res = {"convention": "index 0 = the CLOSE OF THE FILL BAR itself; index j = j minutes after it",
       "note": "no stop, no target, no cost -- the raw price process from the fill"}
for lab, g in sorted(groups.items()):
    n = meta[lab]["n"]
    res[lab] = {"n": n, "mean_spread_r": round(meta[lab]["spread_r_sum"] / n, 5),
                "mean_r_by_minute": [mean(g[j]) for j in range(MAXB)],
                "n_by_minute": [len(g[j]) for j in range(MAXB)]}
    s = res[lab]["mean_r_by_minute"]
    res[lab]["created_at_fill_bar_close"] = s[0]
    res[lab]["created_minutes_1_to_5"] = round((s[5] or 0) - (s[0] or 0), 6) if len(s) > 5 else None
    res[lab]["created_minutes_5_to_19"] = round((s[19] or 0) - (s[5] or 0), 6) if len(s) > 19 else None

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
hdr = "%-36s %6s %7s " % ("group", "n", "sprd_r") + " ".join("m%-2d" % j for j in (0, 1, 2, 3, 5, 10, 15, 19))
print(hdr)
for lab in ["ALL", "filled_on_bar1", "filled_later", "born_at_limit", "born_resting", "born_marketable"] + \
           sorted(k for k in res if k.startswith("fam:")):
    if lab not in res:
        continue
    v = res[lab]; s = v["mean_r_by_minute"]
    print("%-36s %6d %7.3f " % (lab[:36], v["n"], v["mean_spread_r"]) +
          " ".join("%+.4f" % (s[j] or 0) for j in (0, 1, 2, 3, 5, 10, 15, 19)))
