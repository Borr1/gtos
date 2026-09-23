"""d8_run — extract price-space forward statistics at every emission instant and at
every one of the 96 M15 grid windows on the same symbol-day, for one month.

    python3 d8_run.py --month 202601 --out d8/

Writes D8_EMIT_<mm>.npz and D8_GRID_<mm>.npz.  No sampling anywhere.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d8_lib as D  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "d8"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mm = a.month

    rows = D.load_roster(mm)
    syms = sorted({r["s"] for r in rows})
    tape = D.Tape(mm, symbols=syms)
    print("month %s roster=%d symbols=%d tape_minutes=%d" % (mm, len(rows), len(syms), tape.n),
          flush=True)

    fams = sorted({r["f"] for r in rows})
    fam_ix = {f: i for i, f in enumerate(fams)}
    sym_ix = {s: i for i, s in enumerate(syms)}

    # ---- concurrency: how many DISTINCT families emit on the same symbol+instant,
    #      and what is the net side agreement among them
    by_si = defaultdict(list)
    for r in rows:
        by_si[(r["s"], r["t"])].append(r)
    conc_n, conc_net = {}, {}
    for k, v in by_si.items():
        f_long = defaultdict(int)
        for r in v:
            f_long[r["f"]] += (1 if r["d"] == "L" else -1)
        nf = len(f_long)
        net = sum(np.sign(x) for x in f_long.values())
        conc_n[k], conc_net[k] = nf, net

    stats = {s: D.forward_stats(tape, s) for s in syms}

    # ---------------------------------------------------------------- emissions
    n = len(rows)
    E = {
        "sym": np.zeros(n, np.int16), "fam": np.zeros(n, np.int16),
        "day": np.zeros(n, "U10"), "long": np.zeros(n, bool),
        "i": np.zeros(n, np.int32), "hour": np.zeros(n, np.int8),
        "d_bps": np.full(n, np.nan, np.float32),
        "anchor": np.full(n, np.nan, np.float64),
        "conc_nf": np.zeros(n, np.int8), "conc_net": np.zeros(n, np.int8),
    }
    for h in D.HORIZONS:
        E["ret_%d" % h] = np.full(n, np.nan, np.float32)
        E["hi_%d" % h] = np.full(n, np.nan, np.float32)
        E["lo_%d" % h] = np.full(n, np.nan, np.float32)
    for a_i, r in enumerate(rows):
        s = r["s"]
        i = tape.idx(r["t"])
        E["sym"][a_i] = sym_ix[s]; E["fam"][a_i] = fam_ix[r["f"]]
        E["day"][a_i] = r["t"][:10]; E["long"][a_i] = (r["d"] == "L")
        E["i"][a_i] = i; E["hour"][a_i] = int(r["t"][11:13])
        E["conc_nf"][a_i] = min(127, conc_n[(s, r["t"])])
        E["conc_net"][a_i] = int(np.clip(conc_net[(s, r["t"])], -127, 127))
        st = stats[s]
        if 0 <= i < tape.n:
            anc = st["anchor"][i]
            E["anchor"][a_i] = anc
            if np.isfinite(anc) and anc > 0:
                E["d_bps"][a_i] = abs(float(r["e"]) - float(r["sl"])) / anc * 1e4
            for h in D.HORIZONS:
                ret, hib, lob, valid = st[h]
                if valid[i]:
                    E["ret_%d" % h][a_i] = ret[i]
                    E["hi_%d" % h][a_i] = hib[i]
                    E["lo_%d" % h][a_i] = lob[i]
    np.savez_compressed(os.path.join(a.out, "D8_EMIT_%s.npz" % mm),
                        fams=np.array(fams), syms=np.array(syms), **E)

    # --------------------------------------------------------------- grid control
    gi = D.grid_instants(mm, tape)
    m = len(gi) * len(syms)
    G = {"sym": np.zeros(m, np.int16), "day": np.zeros(m, "U10"),
         "w": np.zeros(m, np.int8), "i": np.zeros(m, np.int32)}
    for h in D.HORIZONS:
        G["ret_%d" % h] = np.full(m, np.nan, np.float32)
        G["hi_%d" % h] = np.full(m, np.nan, np.float32)
        G["lo_%d" % h] = np.full(m, np.nan, np.float32)
    p = 0
    for si, s in enumerate(syms):
        st = stats[s]
        idxs = np.array([x[2] for x in gi], np.int64)
        ok = (idxs >= 0) & (idxs < tape.n)
        k = len(gi)
        G["sym"][p:p + k] = si
        G["day"][p:p + k] = [x[0] for x in gi]
        G["w"][p:p + k] = [x[1] for x in gi]
        G["i"][p:p + k] = idxs
        for h in D.HORIZONS:
            ret, hib, lob, valid = st[h]
            v = np.zeros(k, bool); v[ok] = valid[idxs[ok]]
            for nm, arr in (("ret", ret), ("hi", hib), ("lo", lob)):
                tgt = G["%s_%d" % (nm, h)]
                sel = np.zeros(k, np.float32); sel[:] = np.nan
                sel[v] = arr[idxs[v]]
                tgt[p:p + k] = sel
        p += k
    np.savez_compressed(os.path.join(a.out, "D8_GRID_%s.npz" % mm),
                        syms=np.array(syms), **G)

    summ = {"month": mm, "roster_rows": n, "symbols": len(syms),
            "families": fams, "grid_rows": m,
            "emit_valid": {str(h): int(np.isfinite(E["ret_%d" % h]).sum()) for h in D.HORIZONS},
            "grid_valid": {str(h): int(np.isfinite(G["ret_%d" % h]).sum()) for h in D.HORIZONS}}
    print(json.dumps(summ), flush=True)
    with open(os.path.join(a.out, "D8_BUILD_%s.json" % mm), "w") as fh:
        json.dump(summ, fh, indent=1)


if __name__ == "__main__":
    main()
