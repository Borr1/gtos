"""l2 step 9 — is the price-space invariance of stop distance real, and is it real EVERYWHERE?

The central claim from l2_02/l2_03 is that moving the stop over a 12x range changes the
price-space (original-R-unit) expectancy by essentially nothing, so stop distance carries no
information about outcome and can only rescale the bet.  This step tests it:
  (a) pool-level: bootstrap CI on gross_old(k) - gross_old(1) for every k
  (b) per family and per symbol: same delta with a bootstrap SE, flagged when |delta| > 2 SE
  (c) the same on de-duplicated setups (W0-F1: 24.4% of the pool is pseudo-replication)
Writes L2_INVARIANCE_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

KS = [0.25, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
I1 = KS.index(1.0)
B = 400
random.seed(20260806)
OUT = os.path.join(D, "L2_INVARIANCE_V1.json")


def mean(v):
    return sum(v) / len(v) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
pop = []
with gzip.open(os.path.join(D, "l2_SWEEP_ROWS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln)
        if e["A"] is None or (e["m"] is not None and e["m"] <= -1.0):
            continue
        r = byk[(e["cid"], e["dt"])]
        pop.append({"g": [e["A"][ix][0] * KS[ix] for ix in range(len(KS))],   # ORIGINAL-unit R at each k
                    "fam": e["fam"], "sym": e["sym"], "first": bool(r.get("is_first_emission"))})
N = len(pop)


def boot_delta(sub, ix):
    """bootstrap the mean delta gross_old(k=KS[ix]) - gross_old(k=1)."""
    d = [x["g"][ix] - x["g"][I1] for x in sub]
    m = mean(d)
    n = len(d)
    bs = []
    for _ in range(B):
        s = 0.0
        for _ in range(n):
            s += d[random.randrange(n)]
        bs.append(s / n)
    bs.sort()
    return {"n": n, "delta": round(m, 6),
            "ci95_lo": round(bs[int(0.025 * (B - 1))], 6), "ci95_hi": round(bs[int(0.975 * (B - 1))], 6),
            "se": round((sum((x - mean(bs)) ** 2 for x in bs) / (B - 1)) ** 0.5, 6)}


res = {"n": N, "bootstrap_resamples": B, "seed": 20260806,
       "definition": "delta = mean price-space R at stop multiple k  MINUS  the same at k=1; "
                     "a stop change that creates or destroys value must move THIS"}
res["pool_delta_by_k"] = {}
for ix, kk in enumerate(KS):
    res["pool_delta_by_k"]["k=%.2f" % kk] = boot_delta(pop, ix)
    res["pool_delta_by_k"]["k=%.2f" % kk]["gross_old"] = round(mean([x["g"][ix] for x in pop]), 6)

DEDUP = [x for x in pop if x["first"]]
res["dedup_delta_by_k"] = {}
for ix, kk in enumerate(KS):
    if kk in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        b = boot_delta(DEDUP, ix)
        b["gross_old"] = round(mean([x["g"][ix] for x in DEDUP]), 6)
        res["dedup_delta_by_k"]["k=%.2f" % kk] = b

for cut, kf in (("family", lambda x: x["fam"]), ("symbol", lambda x: x["sym"])):
    g = {}
    for x in pop:
        g.setdefault(kf(x), []).append(x)
    out = {}
    for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 60:
            continue
        e = {"n": len(v), "gross_old_k1": round(mean([x["g"][I1] for x in v]), 6)}
        for ix, kk in enumerate(KS):
            if kk in (0.5, 1.5, 2.0, 3.0):
                b = boot_delta(v, ix)
                e["k=%.2f" % kk] = {"delta": b["delta"], "ci95": [b["ci95_lo"], b["ci95_hi"]],
                                    "significant_2se": abs(b["delta"]) > 2 * b["se"] if b["se"] else False}
        out[str(k)] = e
    res[cut] = out

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", N)
print("--- pool: price-space delta vs k=1 (95% bootstrap CI) ---")
for kk, b in res["pool_delta_by_k"].items():
    print("%s gross_old=%+.5f delta=%+.5f ci=[%+.5f,%+.5f]" % (kk, b["gross_old"], b["delta"], b["ci95_lo"], b["ci95_hi"]))
print("--- families where a stop change moves price-space value (2 SE) ---")
for k, e in res["family"].items():
    flags = [kk for kk in ("k=0.50", "k=1.50", "k=2.00", "k=3.00") if e[kk]["significant_2se"]]
    print("%-34s n=%5d g1=%+.5f " % (k[:34], e["n"], e["gross_old_k1"]) +
          " ".join("%s %+.4f%s" % (kk, e[kk]["delta"], "*" if e[kk]["significant_2se"] else "")
                   for kk in ("k=0.50", "k=1.50", "k=2.00", "k=3.00")))
