"""d1 — is the at-market cohort's positive gross an ENTRY-PRICE CONVENTION artifact?

The estate's shipped contract books a market order sent at decision instant i at the
CLOSE OF STAMP i-1 (the last print strictly before i) and then starts the forward path
at stamp i+1.  Stamp i itself -- the minute between the price you are credited with and
the first bar you are walked over -- is skipped.

This lane measured that 0.96 % of at-market rows are rows a resting limit at the same
price never fills, that they book +1.714 R/trade under that convention, and that they
carry 68 % of the whole at-market headline.  Those are exactly the rows where price left
the credited price during the skipped minute.

Three entry conventions, same rows, same stops, same toll, same walker:
  A  SHIPPED     entry = close[i-1]            (what f1/f2/PB/d1-pass-1 all price)
  B  ACHIEVABLE  entry = open[i]               (the first print at or after the decision)
  C  ONE-BAR-LATE entry = close[i]             (a fill at the end of the decision minute)
For B and C the STOP PRICE is held at the generator's own level, so the risk distance
moves with the entry -- which is what happens live.  A second pass holds the risk
distance instead, to separate "worse price" from "different R unit".
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


def blockboot(v, b, nboot=4000, seed=11):
    v = np.asarray(v, float)
    o = np.argsort(b, kind="stable"); v = v[o]; b = np.asarray(b)[o]
    ub = np.unique(b)
    st = np.searchsorted(b, ub, "left"); en = np.searchsorted(b, ub, "right")
    s = np.add.reduceat(v, st); c = (en - st).astype(float)
    rs = np.random.default_rng(seed)
    idx = rs.integers(0, s.size, size=(nboot, s.size))
    ms = s[idx].sum(1) / c[idx].sum(1)
    lo, hi = np.percentile(ms, [2.5, 97.5])
    return float(lo), float(hi), float((ms <= 0).mean())


def run(w, out):
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    keep = set(json.load(open(DISC + "/f1_ARM_TRADING_DAYS_V1.json"))[w])
    rows = []
    for f in sorted(glob.glob(SRC[w] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15 or r["t"][:10] not in keep:
                    continue
                if r["f"] not in ATMARKET:
                    continue
                rows.append(r)
    tape = E.Tape(list(L.SYMBOLS), mons)
    fc = FastCost()
    rec = []
    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n):
            continue
        e0 = r["e"]; sl = r["sl"]; lng = r["d"] == "L"
        d0 = abs(e0 - sl)
        if not (d0 > 0):
            continue
        oi = tape.o[sym][i]; ci = tape.c[sym][i]
        if oi != oi or ci != ci:
            continue
        A = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, e0, sl, lng)
        if A is None:
            continue
        row = {"f": r["f"], "s": sym, "day": r["t"][:10], "lng": lng,
               "A_r20": A[4], "A_r15": A[2], "d0_bps": d0 / e0 * 1e4,
               "gap_bps": (oi - e0) / e0 * 1e4 * (1 if lng else -1),
               "gapc_bps": (ci - e0) / e0 * 1e4 * (1 if lng else -1)}
        row["A_cost"] = fc.px(sym, r["t"], e0, lng) / d0
        for tag, ent in (("B", float(oi)), ("C", float(ci))):
            # stop held at the generator's own price level -> risk distance moves
            dv = abs(ent - sl)
            born = (ent <= sl) if lng else (ent >= sl)
            if born or not (dv > 0):
                row[tag + "_r20"] = -1.0; row[tag + "_r15"] = -1.0
                row[tag + "_born"] = 1; row[tag + "_cost"] = row["A_cost"] * (d0 / max(dv, 1e-12)) if dv > 0 else 0.0
                row[tag + "_d_bps"] = dv / ent * 1e4 if ent else 0.0
            else:
                V = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, ent, sl, lng)
                row[tag + "_r20"] = V[4] if V else 0.0
                row[tag + "_r15"] = V[2] if V else 0.0
                row[tag + "_born"] = 0
                row[tag + "_cost"] = fc.px(sym, r["t"], ent, lng) / dv
                row[tag + "_d_bps"] = dv / ent * 1e4
            # risk-distance-held variant: stop mirrored to keep |d| = d0
            sl2 = ent - d0 if lng else ent + d0
            V2 = walk_market(tape.h[sym], tape.l[sym], tape.c[sym], tape.n, i, ent, sl2, lng)
            row[tag + "H_r20"] = V2[4] if V2 else 0.0
            row[tag + "H_r15"] = V2[2] if V2 else 0.0
        rec.append(row)
    json.dump(rec, gzip_open(out), separators=(",", ":"))
    print(w, "at-market rows", len(rec), flush=True)


def gzip_open(p):
    import gzip as g
    return g.open(p, "wt")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
