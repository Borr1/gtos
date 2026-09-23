"""l2 step 12 — the UNCONDITIONAL timeline.  No fill conditioning, no exit rule, no cost.

l2_11 measured the deficit is fully present at the fill bar.  A resting limit only fills when
price comes to it, so that measurement is conditioned on a fill and adverse selection alone could
produce it.  This step removes the conditioning entirely: the mean signed R of EVERY honest
candidate at each clock offset from its own decision, whether or not it would ever have been
filled.

  t = 0        anchor mkt_r_open   -- open of the M1 bar stamped at the decision (bars are
                                     OPEN-stamped, so this is the decision instant itself)
  t = +1 min   anchor mkt_r_close  -- close of that same bar
  t = +2..+21  path cls[0..19]     -- the ordered path sidecar starts at decision+1min

A negative unconditional mean is a directional anti-edge in the signal, not adverse selection.
Writes L2_UNCONDITIONAL_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_UNCONDITIONAL_V1.json")
MAXB = 20


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


def med(v):
    v = sorted(x for x in v if x is not None)
    return round(v[len(v) // 2], 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

G = {}


def add(lab, o, c, cls, sp, filled):
    g = G.setdefault(lab, {"open": [], "close": [], "path": [[] for _ in range(MAXB)],
                           "sp": [], "n": 0, "nfill": 0})
    g["n"] += 1
    g["nfill"] += 1 if filled else 0
    g["sp"].append(sp)
    if o is not None:
        g["open"].append(o)
    if c is not None:
        g["close"].append(c)
    for j in range(min(MAXB, len(cls))):
        g["path"][j].append(cls[j])


for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k); a = anch.get(k)
    if r is None:
        continue
    m = a["mkt_r_prev_close"] if a else None
    if m is not None and m <= -1.0:
        continue                                   # untakeable, excluded everywhere
    adv, cls = rp["adv"], rp["cls"]
    filled = any(v <= 0.0 for v in adv)
    o = a.get("mkt_r_open") if a else None
    c = a.get("mkt_r_close") if a else None
    sp = r.get("spread_r") or 0.0
    born = ("born_marketable" if (m is not None and m < 0.0) else
            "born_at_limit" if m == 0.0 else "born_resting" if m is not None else "unknown")
    add("ALL_honest", o, c, cls, sp, filled)
    add(born, o, c, cls, sp, filled)
    fam = r.get("origin_family")
    if fam:
        add("fam:" + fam, o, c, cls, sp, filled)
    add("sym:" + r["symbol"], o, c, cls, sp, filled)

res = {"convention": "signed R from entry_price in the trade's own direction; UNCONDITIONAL on fill; "
                     "t=0 is the decision instant (open of the decision-stamped M1 bar)"}
for lab, g in sorted(G.items()):
    res[lab] = {"n": g["n"], "fill_rate_pct": round(100 * g["nfill"] / g["n"], 3),
                "mean_spread_r": round(sum(g["sp"]) / len(g["sp"]), 5),
                "t0_open": mean(g["open"]), "t0_open_median": med(g["open"]),
                "t1_close": mean(g["close"]), "t1_close_median": med(g["close"]),
                "path_close_by_minute": [mean(g["path"][j]) for j in range(MAXB)],
                "drift_t0_to_t1": round((mean(g["close"]) or 0) - (mean(g["open"]) or 0), 6),
                "drift_t1_to_path19": round((mean(g["path"][19]) or 0) - (mean(g["close"]) or 0), 6)}
with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
print("%-36s %6s %6s %8s %8s %8s %8s %8s %9s" % ("group", "n", "fill%", "t0", "t1", "p0", "p5", "p19", "t0->t1"))
for lab in ["ALL_honest", "born_at_limit", "born_resting", "born_marketable"] + sorted(k for k in res if k.startswith("fam:")):
    if lab not in res:
        continue
    v = res[lab]; p = v["path_close_by_minute"]
    print("%-36s %6d %6.2f %+8.4f %+8.4f %+8.4f %+8.4f %+8.4f %+9.5f"
          % (lab[:36], v["n"], v["fill_rate_pct"], v["t0_open"] or 0, v["t1_close"] or 0,
             p[0] or 0, p[5] or 0, p[19] or 0, v["drift_t0_to_t1"]))
print("--- symbols ---")
for lab in sorted((k for k in res if k.startswith("sym:")), key=lambda k: res[k]["drift_t0_to_t1"]):
    v = res[lab]
    print("%-16s n=%5d sprd_r=%6.3f t0=%+.4f t1=%+.4f drift=%+.5f p19=%+.4f"
          % (lab[4:], v["n"], v["mean_spread_r"], v["t0_open"] or 0, v["t1_close"] or 0,
             v["drift_t0_to_t1"], v["path_close_by_minute"][19] or 0))
