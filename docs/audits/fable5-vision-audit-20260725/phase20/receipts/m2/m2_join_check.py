"""Validate the roster<->tick join at the decision instant, and characterise the anchor."""
from __future__ import annotations
import datetime as dt, glob, gzip, json, sys
import numpy as np
sys.path.insert(0, "/tmp/m2")
from m2_tickwalk import load_ticks, ROSTER, FAM, EPOCH

sym, month = sys.argv[1], sys.argv[2]
ts, bd, ak = load_ticks(sym, [month])
rows = []
for f in sorted(glob.glob(ROSTER[month] + "/*.jsonl.gz")):
    with gzip.open(f, "rt") as fh:
        for line in fh:
            if '"structural_distance_extreme"' not in line:
                continue
            r = json.loads(line)
            if r["f"] == FAM and r["k"] == 15 and r["s"] == sym:
                rows.append(r)

dprev, dnext, gap_prev, gap_next, spr = [], [], [], [], []
for r in rows:
    T = dt.datetime.fromisoformat(r["t"])
    tms = int((T - EPOCH).total_seconds()) * 1000
    j = int(np.searchsorted(ts, tms, "left"))
    if j >= len(ts) or j == 0:
        continue
    e = float(r["e"])
    dprev.append(float(bd[j - 1]) - e)
    dnext.append(float(bd[j]) - e)
    gap_prev.append((tms - int(ts[j - 1])) / 1000.0)
    gap_next.append((int(ts[j]) - tms) / 1000.0)
    spr.append(float(ak[j] - bd[j]))
dprev = np.array(dprev); dnext = np.array(dnext)
gp = np.array(gap_prev); gn = np.array(gap_next); sp = np.array(spr)
print(f"{sym} {month} n={len(dprev)}")
print(" |bid(last tick BEFORE T) - e| : median %.6g  p95 %.6g  exact0 %.4f"
      % (np.median(np.abs(dprev)), np.percentile(np.abs(dprev), 95), float((np.abs(dprev) < 1e-9).mean())))
print(" |bid(first tick AT/AFTER T) - e|: median %.6g  p95 %.6g  exact0 %.4f"
      % (np.median(np.abs(dnext)), np.percentile(np.abs(dnext), 95), float((np.abs(dnext) < 1e-9).mean())))
print(" seconds T - prev tick : median %.3f p95 %.1f max %.0f" % (np.median(gp), np.percentile(gp, 95), gp.max()))
print(" seconds next tick - T : median %.3f p95 %.1f max %.0f" % (np.median(gn), np.percentile(gn, 95), gn.max()))
print(" spread at T: median %.6g" % np.median(sp))
print(" signed (bid_next - e)/spread: median %.4f mean %.4f" % (np.median(dnext / sp), (dnext / sp).mean()))
