"""d2_entry — the entry-timing oracle AT THE SHIPPED EXIT CONTRACT.

f2's entry oracle is defined on the oracle exit menu, so it cannot be used as the
"replace only this layer" term in a leave-one-oracle-in table.  This computes, for every
row, max over the 15 M1 instants covering the following M15 bar of the SHIPPED 2R/-1R
walk, with the risk distance held at the generator's own d.  Appends to the row npz.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "pbg"))

import f2_ladder as F  # noqa: E402
import f2_run as R2  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--npz", required=True)
    args = ap.parse_args()
    rows = F.load_close_rows(args.indir, set(F.AT_MARKET))
    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()
    fr = R2.build_frame(rows, tape, cm, horizon=F.HORIZON)
    n = fr["n"]
    best = np.full(n, -np.inf)
    bestj = np.zeros(n, dtype=int)
    for j in range(F.ENTRY_WINDOW):
        ej = fr["W_c"][:, j]
        okj = np.isfinite(ej) & fr["ok"]
        rcj, rhj, rlj = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], ej, fr["d"],
                                   fr["long"], j, F.HORIZON)
        vj, _ = F.walk_fixed(rcj, rhj, rlj, F.SHIPPED_TARGET_R)
        vj = np.where(okj, vj, -np.inf)
        upd = vj > best
        bestj = np.where(upd, j, bestj)
        best = np.maximum(best, vj)
    best = np.where(np.isfinite(best), best, np.nan)
    d = dict(np.load(args.npz, allow_pickle=True))
    assert len(d["ok"]) == n, (len(d["ok"]), n)
    d["entry_oracle_shipped_exit"] = best
    d["entry_oracle_shipped_j"] = bestj
    np.savez_compressed(args.npz, **d)
    ok = fr["ok"]
    print(args.month, "entry-oracle@shipped-exit gross %+.5f (vs shipped %+.5f)"
          % (float(np.nanmean(best[ok])),
             float(np.nanmean(d["gross"][ok]))), flush=True)


if __name__ == "__main__":
    main()
