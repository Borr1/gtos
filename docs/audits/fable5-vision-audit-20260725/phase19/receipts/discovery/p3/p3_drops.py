"""p3 — survivorship: are the rows every lane DROPS (no M1 bar at T-1m) different?

d5's open question 3: 4.34-11.80% of emissions per window are dropped for having no
M1 bar at T-1m, concentrated at session opens, and nobody measured whether they
differ economically.  They cannot be classified by order type (mkt_r0 needs that
bar) but they CAN be walked under the estate's own EST contract, which does not.
"""
from __future__ import annotations
import glob
import gzip
import json
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, "/tmp/p3")
from p3_walk import load_tape, outcome, fill_index, NEXT, ROSTER, HOR  # noqa: E402

WINS = ["202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605"]
OUT = {}
for win in WINS:
    months = [win] + ([NEXT[win]] if NEXT.get(win) else [])
    t0, n, O, H, L, C = load_tape(months)
    okc = {s: ~np.isnan(C[s]) for s in C}
    rows = []
    for f in sorted(glob.glob(ROSTER[win] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] == 15:
                    rows.append(r)
    keep, drop = [], []
    for r in rows:
        sym = r["s"]
        if sym not in C:
            continue
        i = int((datetime.fromisoformat(r["t"]) - t0).total_seconds() // 60)
        if not (0 < i < n - 2):
            continue
        e = float(r["e"]); sl = float(r["sl"]); d = abs(e - sl)
        if not (d > 0):
            continue
        lng = r["d"] == "L"
        s = 1.0 if lng else -1.0
        c = C[sym]; h = H[sym]; l = L[sym]; ok = okc[sym]
        b = min(i + HOR, n)
        if not ok[i:b].any():
            continue
        fi = fill_index(h, l, ok, i, b, e, from_below=not lng)
        if fi < 0:
            g, f_ = 0.0, 0
        else:
            o1 = outcome(h, l, c, ok, fi + 1, b, lng, e, sl, e + s * 2.0 * d, d, True)
            g, f_ = (0.0, 0) if o1 is None else (o1[0], 1)
        (drop if c[i - 1] != c[i - 1] else keep).append((g, f_))
    K = np.asarray(keep) if keep else np.zeros((0, 2))
    D = np.asarray(drop) if drop else np.zeros((0, 2))
    OUT[win] = {
        "n_keep": len(K), "n_drop": len(D),
        "drop_share": len(D) / max(len(K) + len(D), 1),
        "EST_gross_per_opp_keep": float(K[:, 0].mean()) if len(K) else None,
        "EST_gross_per_opp_drop": float(D[:, 0].mean()) if len(D) else None,
        "fill_keep": float(K[:, 1].mean()) if len(K) else None,
        "fill_drop": float(D[:, 1].mean()) if len(D) else None,
    }
    o = OUT[win]
    print("%s keep %7d drop %6d (%.4f)  EST/opp keep %+8.5f drop %+8.5f  fill %.4f/%.4f"
          % (win, o["n_keep"], o["n_drop"], o["drop_share"], o["EST_gross_per_opp_keep"],
             o["EST_gross_per_opp_drop"], o["fill_keep"], o["fill_drop"]))
nk = sum(OUT[w]["n_keep"] for w in WINS)
nd = sum(OUT[w]["n_drop"] for w in WINS)
gk = sum(OUT[w]["EST_gross_per_opp_keep"] * OUT[w]["n_keep"] for w in WINS) / nk
gd = sum(OUT[w]["EST_gross_per_opp_drop"] * OUT[w]["n_drop"] for w in WINS) / nd
OUT["POOLED"] = {"n_keep": nk, "n_drop": nd, "drop_share": nd / (nk + nd),
                 "EST_gross_per_opp_keep": gk, "EST_gross_per_opp_drop": gd,
                 "combined": (gk * nk + gd * nd) / (nk + nd)}
print("POOLED keep %d drop %d (%.4f)  EST/opp keep %+.5f drop %+.5f combined %+.5f"
      % (nk, nd, nd / (nk + nd), gk, gd, OUT["POOLED"]["combined"]))
json.dump(OUT, open("/tmp/p3/P3_DROPS.json", "w"), indent=1)
