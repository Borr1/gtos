#!/usr/bin/env python3
"""h5 step 0 — build the h5 substrate.

Joins the three at-market (LIVE-EXPRESSIBLE) month tables built by e-stack
(`e_build_atmkt.py`) into one 43,755-row table under the repaired contract
(market entry delayed k=5 minutes, TRAIL025 exit), and adds the axis columns the
ATMKT build did not carry:

  rv60_bps   ex-ante realised volatility: stdev of the 60 M1 log returns that
             CLOSE strictly at or before the decision instant, in bps.  Zero
             look-ahead by construction (the anchor bar is stamped decision-1min).
  rv_rel     rv60_bps / the symbol's JANUARY median rv60_bps  (cuts frozen on Jan
             so February and March are read out of month)
  rdp_rel    rdp / the symbol's JANUARY median rdp  (relative stop width)
  dow        day of week of the decision
  rdp_dec    global risk-distance decile, cuts frozen on January
  cost_dec   broker-true cost decile, cuts frozen on January

Everything else is carried verbatim from the ATMKT tables.

out: h5_SUBSTRATE_V1.jsonl.gz  +  h5_SUBSTRATE_V1_BUILD.json
"""
import bisect
import csv
import gzip
import json
import math
import os
import sys
import time
from datetime import datetime

D = os.path.dirname(os.path.abspath(__file__))
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
MONTHS = [("2026-01", "202601", "e_JAN_ATMKT_V1.jsonl.gz"),
          ("2026-02", "202602", "e_FEB_ATMKT_V1.jsonl.gz"),
          ("2026-03", "202603", "e_MAR_ATMKT_V1.jsonl.gz")]
RVWIN = 60


def prevmonth(m):
    y, mo = int(m[:4]), int(m[4:])
    return f"{y - (mo == 1)}{(12 if mo == 1 else mo - 1):02d}"


def load_closes(month, sym):
    """ts[], close[] for month and the month before (so the first day has a window)."""
    ts, c = [], []
    for mm in (prevmonth(month), month):
        p = os.path.join(BARS, f"bridge_ftmo_m1_{mm}", f"{sym}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            rd = csv.reader(f)
            next(rd)
            for r in rd:
                ts.append(r[0])
                c.append(float(r[4]))
    if not ts:
        return None
    order = sorted(range(len(ts)), key=lambda i: ts[i])
    return [ts[i] for i in order], [c[i] for i in order]


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def main():
    t0 = time.time()
    rows = []
    for label, mm, fn in MONTHS:
        for line in gzip.open(os.path.join(D, fn), "rt"):
            if line.strip():
                r = json.loads(line)
                r["month"] = label
                r["_mm"] = mm
                rows.append(r)
    print("joined rows", len(rows), flush=True)

    # --- ex-ante realised vol ------------------------------------------------
    need = {}
    for r in rows:
        need.setdefault((r["_mm"], r["symbol"]), []).append(r)
    nrv = nomiss = 0
    for (mm, sym), rs in sorted(need.items()):
        bc = load_closes(mm, sym)
        if bc is None:
            nomiss += len(rs)
            for r in rs:
                r["rv60_bps"] = None
            continue
        ts, c = bc
        for r in rs:
            dt = r["dt"]
            i = bisect.bisect_right(ts, dt) - 1          # last bar stamped <= dt
            if ts[i] == dt:
                i -= 1                                    # OPEN-stamped: that bar has not closed
            if i < RVWIN:
                r["rv60_bps"] = None
                continue
            rets = []
            for k in range(i - RVWIN + 1, i + 1):
                a, b = c[k - 1], c[k]
                if a > 0 and b > 0:
                    rets.append(math.log(b / a))
            if len(rets) < 30:
                r["rv60_bps"] = None
                continue
            m = sum(rets) / len(rets)
            sd = (sum((x - m) ** 2 for x in rets) / (len(rets) - 1)) ** 0.5
            r["rv60_bps"] = round(sd * 1e4, 6)
            nrv += 1
    print("rv computed", nrv, "no bars", nomiss, round(time.time() - t0, 1), flush=True)

    # --- January-frozen normalisers -----------------------------------------
    jan = [r for r in rows if r["month"] == "2026-01"]
    med_rv, med_rdp = {}, {}
    for sym in sorted({r["symbol"] for r in rows}):
        v = [r["rv60_bps"] for r in jan if r["symbol"] == sym and r["rv60_bps"]]
        med_rv[sym] = median(v) if v else None
        w = [r["rdp"] for r in jan if r["symbol"] == sym and r["rdp"]]
        med_rdp[sym] = median(w) if w else None

    def deciles(v):
        s = sorted(v)
        return [s[int(round(p * (len(s) - 1)))] for p in [i / 10 for i in range(1, 10)]]

    rdp_cuts = deciles([r["rdp"] for r in jan])
    cost_cuts = deciles([r["cost_true"] for r in jan if r["cost_true"] is not None])

    for r in rows:
        s = r["symbol"]
        r["rv_rel"] = (r["rv60_bps"] / med_rv[s]) if (r["rv60_bps"] and med_rv.get(s)) else None
        r["rdp_rel"] = (r["rdp"] / med_rdp[s]) if (r["rdp"] and med_rdp.get(s)) else None
        r["rdp_dec"] = bisect.bisect_left(rdp_cuts, r["rdp"])
        r["cost_dec"] = (bisect.bisect_left(cost_cuts, r["cost_true"])
                         if r["cost_true"] is not None else None)
        r["dow"] = datetime.fromisoformat(r["dt"]).strftime("%a")
        r.pop("_mm", None)

    out = os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz")
    with gzip.open(out, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    rec = {"rows": len(rows),
           "per_month": {m: sum(1 for r in rows if r["month"] == m) for m, _, _ in MONTHS},
           "rv_computed": nrv, "rv_null": sum(1 for r in rows if r["rv60_bps"] is None),
           "rdp_decile_cuts_jan": [round(x, 8) for x in rdp_cuts],
           "cost_decile_cuts_jan": [round(x, 8) for x in cost_cuts],
           "median_rv_bps_jan": {k: (round(v, 6) if v else None) for k, v in med_rv.items()},
           "median_rdp_jan": {k: (round(v, 8) if v else None) for k, v in med_rdp.items()},
           "seconds": round(time.time() - t0, 1)}
    json.dump(rec, open(os.path.join(D, "h5_SUBSTRATE_V1_BUILD.json"), "w"), indent=1)
    print(json.dumps({k: rec[k] for k in ("rows", "per_month", "rv_computed", "rv_null", "seconds")}))


if __name__ == "__main__":
    main()
