#!/usr/bin/env python3
"""l7 pass 5 — the ENTRY-DELAY LADDER on raw M1 bars, exact wall clock.

The path sidecar's first bar is stamped T+1 (it covers [T+1,T+2)), so the minute [T,T+1)
immediately after the decision is ABSENT from every published path. This pass rebuilds the
walk from the raw M1 series so the first minute is included and the delay axis is exact.

For each ATLIMIT candidate (entry price == the decision-instant market) and each delay k:
    entry_k = close of the bar stamped T+k-1   (k=0 -> the published entry_price)
    walk the raw bars from the bar stamped T+k, stop at entry_k - d, target at entry_k + 2d
    (mirror for the inverse), horizon 120 minutes from T, conservative tie -> stop.
Risk distance d is held fixed, so the R unit never changes and the delays are comparable.

Writes L7_RAWLADDER_V1.json.
"""
import bisect, csv, collections, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import l7_lib as L

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
        "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601")
DELAYS = [0, 1, 2, 3, 5, 10, 15, 30, 60]
HORIZON = 120

_c = {}


def ser(s):
    if s in _c:
        return _c[s]
    p = os.path.join(BARS, f"{s}_M1.csv")
    if not os.path.isfile(p):
        _c[s] = None
        return None
    ts, hi, lo, cl = [], [], [], []
    with open(p) as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            ts.append(r[0])
            hi.append(float(r[2]))
            lo.append(float(r[3]))
            cl.append(float(r[4]))
    _c[s] = (ts, hi, lo, cl)
    return _c[s]


def walk(hi, lo, cl, j0, jend, e, d, sgn, tgt=2.0, stop=-1.0):
    """sgn=+1 original side (LONG->+1 means fav is up), sgn=-1 mirrored."""
    for j in range(j0, jend):
        f = sgn * (hi[j] - e) / d if sgn > 0 else sgn * (lo[j] - e) / d
        a = sgn * (lo[j] - e) / d if sgn > 0 else sgn * (hi[j] - e) / d
        ht = f >= tgt
        hs = a <= stop
        if ht and hs:
            return stop
        if ht:
            return tgt
        if hs:
            return stop
    return sgn * (cl[jend - 1] - e) / d


def t(v):
    n = len(v)
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / n)
    return n, round(m, 5), round(m / (sd / math.sqrt(n)), 3) if sd > 0 else None


def main():
    rows = [r for r in L.load() if r["born"] == "born_at_limit"]
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    used = 0
    for r in rows:
        s = ser(r["sym"])
        if s is None:
            continue
        ts, hi, lo, cl = s
        j = bisect.bisect_left(ts, r["dt"])
        if j >= len(ts) or ts[j] != r["dt"]:
            continue
        jend = min(len(ts), j + HORIZON)
        d = r["risk_distance"]
        sg = 1.0 if r["side"] == "LONG" else -1.0
        used += 1
        for k in DELAYS:
            if j + k >= jend:
                continue
            e = r["entry"] if k == 0 else cl[j + k - 1]
            o = walk(hi, lo, cl, j + k, jend, e, d, sg)
            i = walk(hi, lo, cl, j + k, jend, e, d, -sg)
            for g in ("ALL", "fam=" + str(r["fam"]), "side=" + r["side"], "sym=" + r["sym"],
                      "famside=" + str(r["fam"]) + "/" + r["side"], "day=" + r["dt"][:10],
                      "hour=h%02d" % r["hour"], "sess=" + str(r["sess"]),
                      "vol=" + ("vTIGHT" if (r["rd_pct"] or 0) <= 0.05 else
                                "vMID" if (r["rd_pct"] or 0) <= 0.15 else "vWIDE")):
                acc[(g, k)]["o"].append(o)
                acc[(g, k)]["i"].append(i)
                acc[(g, k)]["d"].append((i - o) / 2)
                acc[(g, k)]["c"].append((i + o) / 2)
    res = {"n_anchored": used, "n_pop": len(rows), "delays": DELAYS, "horizon_min": HORIZON, "groups": {}}
    for (g, k), v in acc.items():
        n, mo, to = t(v["o"])
        _, mi, ti = t(v["i"])
        _, md, td = t(v["d"])
        _, mc, tc = t(v["c"])
        res["groups"].setdefault(g, {})["d%d" % k] = {
            "n": n, "orig": mo, "orig_t": to, "inv": mi, "inv_t": ti,
            "dirsig": md, "dirsig_t": td, "coin": mc, "coin_t": tc}
    with open(os.path.join(D, "L7_RAWLADDER_V1.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("anchored", used, "of", len(rows))
    g = res["groups"]["ALL"]
    print("%-7s %6s %10s %10s %10s %8s %10s" % ("delay", "n", "ORIG", "INV", "DIRSIG", "t", "COIN"))
    for k in DELAYS:
        x = g["d%d" % k]
        print("%-7s %6d %+10.5f %+10.5f %+10.5f %8.2f %+10.5f"
              % ("T+%dm" % k, x["n"], x["orig"], x["inv"], x["dirsig"], x["dirsig_t"] or 0, x["coin"]))


if __name__ == "__main__":
    main()
