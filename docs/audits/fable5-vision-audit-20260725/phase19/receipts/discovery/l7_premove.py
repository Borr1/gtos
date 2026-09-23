#!/usr/bin/env python3
"""l7 pass 3 — PRE-DECISION context, strictly no look-ahead.

Bars are OPEN-STAMPED (w0-capture RESULT sec 0.1), so the last bar observable at decision
minute T is the bar stamped T-1 (it closes at T). Everything here is built from bars
stamped <= T-1 only.

Per candidate we emit, in the trade's OWN direction and in R units (risk_distance):
    pre_K   = (close[T-1] - close[T-1-K]) / d   signed for side, K in {5,15,30,60,120}
              > 0 means the market had ALREADY moved in the trade's favour before entry
    rng60   = (high-low over the prior 60 bars) / d
    pos60   = where close[T-1] sits in the prior-60 range, signed for side
              1.0 = at the extreme in the trade's favour, 0.0 = at the extreme against
    nb      = how many prior bars were actually available

Writes l7_PREMOVE_V1.jsonl.gz
"""
import csv, gzip, json, os, sys, bisect

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import l7_lib as L

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
        "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601")
OUT = os.path.join(D, "l7_PREMOVE_V1.jsonl.gz")
KS = [5, 15, 30, 60, 120]

_cache = {}


def series(sym):
    if sym in _cache:
        return _cache[sym]
    p = os.path.join(BARS, f"{sym}_M1.csv")
    if not os.path.isfile(p):
        _cache[sym] = None
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
    _cache[sym] = (ts, hi, lo, cl)
    return _cache[sym]


def main():
    rows = L.load()
    n = 0
    miss = 0
    with gzip.open(OUT, "wt") as out:
        for r in rows:
            s = series(r["sym"])
            if s is None:
                miss += 1
                continue
            ts, hi, lo, cl = s
            # index of the last bar stamped STRICTLY BEFORE the decision minute
            j = bisect.bisect_left(ts, r["dt"]) - 1
            if j < 0:
                miss += 1
                continue
            d = r["risk_distance"]
            sgn = 1.0 if r["side"] == "LONG" else -1.0
            e = {"cid": r["cid"], "dt": r["dt"], "anchor_bar": ts[j], "nb": j + 1}
            c0 = cl[j]
            for k in KS:
                jj = j - k
                e["pre_%d" % k] = round(sgn * (c0 - cl[jj]) / d, 6) if jj >= 0 else None
            a = max(0, j - 59)
            h = max(hi[a:j + 1])
            l_ = min(lo[a:j + 1])
            e["rng60"] = round((h - l_) / d, 6)
            e["pos60"] = round((sgn * (c0 - l_) / (h - l_) + (0.0 if sgn > 0 else 1.0)) if h > l_ else 0.5, 6)
            out.write(json.dumps(e, separators=(",", ":")) + "\n")
            n += 1
    print("wrote", n, "miss", miss, "->", OUT)


if __name__ == "__main__":
    main()
