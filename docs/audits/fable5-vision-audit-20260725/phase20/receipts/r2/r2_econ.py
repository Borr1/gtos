"""r2_econ — price every roster emission ONCE per window, then decompose.

The three repaired gates only ever SUBTRACT emissions, so every arm's economics
is a filter over the legacy roster.  This walks the legacy roster once per
window on the M1 tape with the estate's own walkers and the h1 broker-true
four-term cost basis, tags each row with the quantities the gates key on
(family, fill_gap_r, selected-bar age), and writes a per-row record.  Arm
economics, per-family tables and gap_r bands are then exact groupbys of one
measurement rather than five re-walks.

Contract, unchanged from f1/d4:
  * at-market families  -> market order at the decision instant (`pbg_econ.walk`)
  * POI limit families  -> honest resting limit (`f1_walk.walk_limit2`)
  * horizon 120 M1 bars, target 1.5 R, cost charged once on fill, in R.
"""
from __future__ import annotations

import bisect
import csv
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)

import pbg_lib as PL  # noqa: E402
import pbg_econ as E  # noqa: E402

sys.path.insert(0, "/tmp/f1")
from f1_walk import walk_limit2, NEXT, HOR  # noqa: E402

BARS = PL.M15_DIR
RR = 1.5
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}

ROSTERS = {
    "2025-10": "/tmp/f1/roster_202510",
    "2025-11": "/tmp/f1/roster_202511",
    "2025-12": "/tmp/f1/roster_202512",
    "2026-01": "/tmp/d4/rosters/202601",
    "2026-02": "/tmp/d4/rosters/202602",
    "2026-03": "/tmp/d4/rosters/202603",
    "2026-04": "/tmp/f1/roster_202604",
    "2026-05": "/tmp/f1/roster_202605",
}


class Series:
    __slots__ = ("t", "c")

    def __init__(self, rows):
        self.t = [r[0] for r in rows]
        self.c = [r[1] for r in rows]


def load_series():
    out = {}
    for p in sorted(glob.glob(os.path.join(str(BARS), "*_M15.csv"))):
        sym = os.path.basename(p)[: -len("_M15.csv")]
        rows = []
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((datetime.fromisoformat(r["time"]).replace(tzinfo=None),
                             float(r["close"])))
        rows.sort()
        out[sym] = Series(rows)
    return out


def main(window, out_path):
    S = load_series()
    mons = [window.replace("-", "")] + ([NEXT[window]] if NEXT.get(window) else [])
    tape = E.Tape(list(PL.SYMBOLS), mons)
    cm = E.CostModel()
    rd = ROSTERS[window]
    recs = []
    for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
            continue
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15:
                continue
            sym = r["s"]
            if sym not in tape.c:
                continue
            s = S.get(sym)
            if s is None:
                continue
            T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            j = bisect.bisect_right(s.t, T - timedelta(minutes=15)
                                    + timedelta(seconds=2)) - 1
            if j < 0:
                continue
            cp = s.c[j]
            age_min = int((T - (s.t[j] + timedelta(minutes=15))).total_seconds() // 60)
            i = tape.idx(r["t"])
            if not (0 < i < tape.n):
                continue
            e, sl = r["e"], r["sl"]
            d = abs(e - sl)
            if not d > 0:
                continue
            lng = r["d"] == "L"
            gap = (cp - e) / d * (1.0 if lng else -1.0)
            fam = r["f"]
            if fam in POI:
                o = walk_limit2(tape, sym, i, entry=e, stop=sl, long=lng,
                                target_r=RR, horizon=HOR)
            else:
                o = E.walk(tape, sym, i, entry=e, stop=sl, long=lng,
                           target_r=RR, horizon=HOR)
            if o is None:
                continue
            filled = o[1] != "no_fill"
            px, _ = cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)
            recs.append({
                "w": window, "day": r["t"][:10], "s": sym, "f": fam,
                "gap": gap, "age": age_min, "g": float(o[0]),
                "c": float(px / d) if filled else 0.0,
                "fill": bool(filled), "reason": o[1],
                "d_bps": d / e * 1e4,
            })
    with gzip.open(out_path, "wt") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    print(window, "rows", len(recs), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
