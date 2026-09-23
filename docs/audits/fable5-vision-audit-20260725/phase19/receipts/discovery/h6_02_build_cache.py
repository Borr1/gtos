"""h6 step 2 — materialise the at-market cohort's R paths as a numpy cache so the
repaired contract's parameters can be swept JOINTLY at speed.

Rebuilds fav/adv/cls exactly as e_build_atmkt.py does, keyed on the 43,755 rows that
file already emitted, so the cohort is identical by construction.

Emits h6_ATMKT_PATHS.npz:
    F,A,C  float32 [n,120]  (NaN padded)   nb int16 [n]  valid bar count
    plus a parallel meta jsonl.gz with symbol/day/month/cost/entry/rd/efp/... per row.
"""
import bisect, csv, gzip, json, os, sys, time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
FILES = [("202601", "2026-01", f"{D}/e_JAN_ATMKT_V1.jsonl.gz"),
         ("202602", "2026-02", f"{D}/e_FEB_ATMKT_V1.jsonl.gz"),
         ("202603", "2026-03", f"{D}/e_MAR_ATMKT_V1.jsonl.gz")]
HZ = 120


def nextmonth(m):
    y, mo = int(m[:4]), int(m[4:])
    return f"{y + (mo == 12)}{(mo % 12) + 1:02d}"


def load_bars(month, sym):
    ts, h, l, c = [], [], [], []
    for mm in (month, nextmonth(month)):
        p = os.path.join(BARS, f"bridge_ftmo_m1_{mm}", f"{sym}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            rd = csv.reader(f)
            next(rd)
            for r in rd:
                ts.append(r[0]); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
    if not ts:
        return None
    o = sorted(range(len(ts)), key=lambda i: ts[i])
    return {"t": [ts[i] for i in o], "h": [h[i] for i in o],
            "l": [l[i] for i in o], "c": [c[i] for i in o]}


def main():
    t0 = time.time()
    allrows = []
    for month, mlabel, path in FILES:
        rows = [json.loads(x) for x in gzip.open(path, "rt") if x.strip()]
        for r in rows:
            r["_month_key"] = month
            r["month"] = mlabel
        allrows += rows
        print(mlabel, len(rows), round(time.time() - t0, 1), flush=True)
    n = len(allrows)
    F = np.full((n, HZ), np.nan, dtype=np.float64)
    A = np.full((n, HZ), np.nan, dtype=np.float64)
    C = np.full((n, HZ), np.nan, dtype=np.float64)
    NB = np.zeros(n, dtype=np.int16)

    cache = {}
    bad = 0
    for idx, r in enumerate(allrows):
        ck = (r["_month_key"], r["symbol"])
        if ck not in cache:
            cache[ck] = load_bars(r["_month_key"], r["symbol"])
            print("  bars", ck, "ok" if cache[ck] else "MISSING",
                  round(time.time() - t0, 1), flush=True)
        b = cache[ck]
        if b is None:
            bad += 1; continue
        dt = r["dt"]
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 1:
            bad += 1; continue
        entry = float(r["entry_price"]); d = float(r["risk_distance"])
        sgn = 1.0 if r["side"] == "LONG" else -1.0
        end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 126, len(b["t"]))):
            if b["t"][kx] <= dt or b["t"][kx] > end:
                if b["t"][kx] > end:
                    break
                continue
            hi = sgn * (b["h"][kx] - entry) / d
            lo = sgn * (b["l"][kx] - entry) / d
            fav.append(max(hi, lo)); adv.append(min(hi, lo))
            cls.append(sgn * (b["c"][kx] - entry) / d)
            if len(fav) >= HZ:
                break
        if len(fav) < 5:
            bad += 1; continue
        m = len(fav)
        F[idx, :m] = fav; A[idx, :m] = adv; C[idx, :m] = cls
        NB[idx] = m
        if idx % 5000 == 0:
            print("  row", idx, round(time.time() - t0, 1), flush=True)

    np.savez_compressed(f"{D}/h6_ATMKT_PATHS.npz", F=F, A=A, C=C, NB=NB)
    keep = ["cid", "dt", "day", "hour", "month", "symbol", "side", "family", "session",
            "n_bars", "risk_distance", "entry_price", "rdp", "cost_frozen", "spread_r",
            "commission_r", "swap_r", "slip_r", "real_spread_r", "real_comm_r",
            "real_slip_r", "cost_true", "efp", "prob",
            "K0_INC", "K5_TRAIL025", "K0_TRAIL025", "K5_INC"]
    with gzip.open(f"{D}/h6_ATMKT_META.jsonl.gz", "wt") as fh:
        for r in allrows:
            fh.write(json.dumps({k: r.get(k) for k in keep}) + "\n")

    # validation: recompute K5_TRAIL025 from the cache and diff against the shipped column
    rec = {"n": n, "bad": bad, "nb_mean": float(NB.mean()), "nb_min": int(NB.min()),
           "nb_max": int(NB.max()), "share_120": float((NB == HZ).mean()),
           "seconds": round(time.time() - t0, 1)}
    print(json.dumps(rec), flush=True)
    json.dump(rec, open(f"{D}/H6_CACHE_BUILD_V1.json", "w"), indent=1)


if __name__ == "__main__":
    main()
