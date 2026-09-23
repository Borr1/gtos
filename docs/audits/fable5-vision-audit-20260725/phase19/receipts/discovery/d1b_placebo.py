"""d1 — random-instant placebo for the at-market cohort.

For every at-market roster emission, three control rows: the SAME symbol, the SAME
trading day, the SAME side, the SAME risk distance in bps -- at a RANDOM instant drawn
from the system's own 96-window M15 decision grid.  Everything the setup could be
credited with except WHEN it fired is held.  If the real arm does not beat this, the
family is not choosing moments.
"""
from __future__ import annotations
import sys, os, json, gzip, glob
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
DISC = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
sys.path.insert(0, PBG); sys.path.insert(0, REPO); os.chdir(REPO)
import pbg_lib as L
import pbg_econ as E
sys.path.insert(0, "/tmp/d1")
from d1_rows import walk_market, FastCost, ATMARKET, NEXT, SRC, HOR

NDRAW = 3


def run(w, out):
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    keep = set(json.load(open(DISC + "/f1_ARM_TRADING_DAYS_V1.json"))[w])
    rows = []
    for f in sorted(glob.glob(SRC[w] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15 or r["t"][:10] not in keep or r["f"] not in ATMARKET:
                    continue
                rows.append(r)
    tape = E.Tape(list(L.SYMBOLS), mons)
    fc = FastCost()
    rs = np.random.default_rng(20260806)
    rec = []
    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n):
            continue
        e = r["e"]; sl = r["sl"]; lng = r["d"] == "L"
        d = abs(e - sl)
        if not (d > 0):
            continue
        A = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, sl, lng)
        if A is None:
            continue
        dbps = d / e * 1e4
        row = {"f": r["f"], "s": sym, "day": r["t"][:10], "lng": lng, "d_bps": dbps,
               "real20": A[4], "real15": A[2],
               "toll": fc.px(sym, r["t"], e, lng) / d}
        # mirrored side at the same instant (the paired coin-flip arm)
        M = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e, 2 * e - sl, not lng)
        row["anti20"] = M[4] if M else 0.0
        row["anti15"] = M[2] if M else 0.0
        # random instants on the same symbol+day, same side, same risk distance in bps
        day0 = tape.idx(r["t"][:10] + "T00:00:00+00:00")
        p20, p15, ptoll, nres = [], [], [], 0
        for _ in range(NDRAW):
            k = int(rs.integers(0, 96))
            j = day0 + 15 * k
            if not (0 < j < tape.n):
                continue
            pe = tape.last_close_before(sym, j)
            if pe != pe or pe <= 0:
                continue
            pd = dbps / 1e4 * pe
            psl = pe - pd if lng else pe + pd
            V = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, j, pe, psl, lng)
            if V is None:
                continue
            p20.append(V[4]); p15.append(V[2]); ptoll.append(fc.px(sym, tape.t0.strftime("%Y-%m-%dT%H:%M:%S+00:00") if False else
                                                                  (tape.t0 + __import__("datetime").timedelta(minutes=j)).isoformat(), pe, lng) / pd)
            nres += 1
        row["plc20"] = float(np.mean(p20)) if p20 else None
        row["plc15"] = float(np.mean(p15)) if p15 else None
        row["plctoll"] = float(np.mean(ptoll)) if ptoll else None
        row["ndraw"] = nres
        rec.append(row)
    with gzip.open(out, "wt") as fh:
        json.dump(rec, fh, separators=(",", ":"))
    print(w, "rows", len(rec), "placebo resolved",
          sum(1 for x in rec if x["plc20"] is not None) / max(len(rec), 1), flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
