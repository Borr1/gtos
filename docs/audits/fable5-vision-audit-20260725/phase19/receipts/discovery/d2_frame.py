"""d2_frame — price EVERY roster emission under the shipped contract, keep the join key.

One month per invocation.  Writes an .npz of per-row arrays plus a .json index of the
string columns, so d2_layers.py can do the layer arithmetic pooled over eight months
without ever re-walking the tape.

Population: the WHOLE reproduced close-only roster (all ten origin families, k=15),
not the at-market subset and not the counterfactual pool.

Contracts, all of them Session PB's / f2's, unchanged:
  * at-market families  -> market fill at the generator's own emitted entry, forward
    path from stamp D+1 (column j+2 of the frame), 120 M1 bars, stop -1R, target +2.0R
    (the shipped downstream momentum_exhaustion geometry), tie inside a bar -> stop.
  * POI families        -> honest resting-limit fill: fills only when the tape TRADES
    THROUGH the level inside the same 120-bar horizon; never touched -> not a trade.
  * toll                -> the four-term broker-true model (h1 basis) at the fill.

Extra arrays that only d2 needs:
  * shipped R at each of the 15 M1 entry stamps covering the following M15 bar (real
    layer = j 0; null layer = a random j; oracle layer = best j) — at-market only.
  * the 13-contract exit menu and the path-oracle exit, for the exit layer.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, DISC)
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)

import f2_ladder as F  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

AT = set(F.AT_MARKET)
POI = set(F.POI)
HOR = 120
ENTRY_WINDOW = 15
TARGET_R = 2.0

NEXT = {"202510": "202511", "202511": "202512", "202512": "202601", "202601": "202602",
        "202602": "202603", "202603": "202604", "202604": "202605", "202605": None}

ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}


def load_rows(indir):
    """One row per (cid, decision instant) — the sealed arm's own candidate key."""
    seen = {}
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                k = (r["cid"], r["t"])
                if k not in seen:
                    seen[k] = r
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    mm = args.month
    months = [mm] + ([NEXT[mm]] if NEXT[mm] else [])

    rows = load_rows(ROSTER[mm])
    n = len(rows)
    print("rows", n, flush=True)

    tape = E.Tape(L.SYMBOLS, months)
    cm = E.CostModel()

    sym = np.array([r["s"] for r in rows])
    fam = np.array([r["f"] for r in rows])
    day = np.array([r["t"][:10] for r in rows])
    cid = [r["cid"] for r in rows]
    inst = [r["t"] for r in rows]
    long = np.array([r["d"] == "L" for r in rows])
    entry = np.array([float(r["e"]) for r in rows])
    stop = np.array([float(r["sl"]) for r in rows])
    d = np.abs(entry - stop)
    is_at = np.array([f in AT for f in fam])

    idx, W_c, W_h, W_l = F.build_paths(tape, rows, extra=ENTRY_WINDOW + HOR + 4)
    # column 0 IS the shipped fill (proven identical to the emitted entry wherever the
    # tape has that minute); patch it so the j=0 entry-oracle candidate is the shipped one
    W_c[:, 0] = np.where(np.isfinite(entry), entry, W_c[:, 0])

    ok_at = is_at & np.isfinite(entry) & (d > 0)

    # ---------------------------------------------------------------- at-market walks
    rc, rh, rl = F.r_frames(W_c, W_h, W_l, entry, d, long, 0, HOR)
    shipped, code = F.walk_fixed(rc, rh, rl, TARGET_R)
    menu = F.exit_menu(rc, rh, rl)
    menu_names = list(menu.keys())
    menu_arr = np.vstack([menu[k] for k in menu_names])          # (13, n)
    path_or = F.oracle_exit_close(rc)
    intrabar_or = F.oracle_exit_intrabar(rh)
    # born past its own stop: the very first forward bar already prints <= -1R
    with np.errstate(invalid="ignore"):
        born_past = np.nan_to_num(rl[:, 0], nan=0.0) <= -1.0

    # shipped contract at each of the 15 entry stamps
    stamp_r = np.full((ENTRY_WINDOW, n), np.nan)
    stamp_cost = np.full((ENTRY_WINDOW, n), np.nan)
    for j in range(ENTRY_WINDOW):
        ej = W_c[:, j]
        okj = np.isfinite(ej) & ok_at
        rcj, rhj, rlj = F.r_frames(W_c, W_h, W_l, ej, d, long, j, HOR)
        sj, _ = F.walk_fixed(rcj, rhj, rlj, TARGET_R)
        stamp_r[j] = np.where(okj, sj, np.nan)
    print("at-market walks done", flush=True)

    # ---------------------------------------------------------------- POI honest fill
    poi_r = np.full(n, np.nan)
    poi_filled = np.zeros(n, dtype=bool)
    poi_fillbar = np.full(n, -1, dtype=np.int32)
    poi_fillpx = np.full(n, np.nan)
    for a in range(n):
        if is_at[a] or not (d[a] > 0):
            continue
        i = int(idx[a])
        b = min(i + HOR, tape.n)
        if i >= b:
            continue
        hi = tape.h[sym[a]][i:b]
        lo = tape.l[sym[a]][i:b]
        okm = ~np.isnan(hi)
        if not okm.any():
            continue
        ii = np.nonzero(okm)[0]
        touched = (lo[ii] <= entry[a]) if long[a] else (hi[ii] >= entry[a])
        if not touched.any():
            poi_filled[a] = False
            poi_r[a] = 0.0
            continue
        j = int(ii[int(np.argmax(touched))])
        res = E.walk(tape, sym[a], i + j, entry=float(entry[a]), stop=float(stop[a]),
                     long=bool(long[a]), target_r=TARGET_R, horizon=HOR - j - 1)
        if res is None:
            poi_r[a] = 0.0
            continue
        poi_filled[a] = True
        poi_fillbar[a] = j
        poi_fillpx[a] = entry[a]
        poi_r[a] = res[0]
    print("poi walks done", flush=True)

    # ---------------------------------------------------------------- toll at the fill
    cost_r = np.full(n, np.nan)
    spread_r = np.full(n, np.nan)
    for a in range(n):
        if not (d[a] > 0):
            continue
        if is_at[a]:
            if not np.isfinite(entry[a]):
                continue
            iso = inst[a]
            px = float(entry[a])
        else:
            if not poi_filled[a]:
                cost_r[a] = 0.0
                spread_r[a] = 0.0
                continue
            iso = (datetime.fromisoformat(inst[a])
                   + timedelta(minutes=int(poi_fillbar[a]))).isoformat()
            px = float(poi_fillpx[a])
        tot, terms = cm.cost_px(sym[a], iso, px, bool(long[a]))
        cost_r[a] = tot / d[a]
        spread_r[a] = terms["spread"] / d[a]
    print("cost done", flush=True)

    real_r = np.where(is_at, shipped, poi_r)
    filled = np.where(is_at, np.isfinite(shipped), poi_filled)

    np.savez_compressed(
        args.out + ".npz",
        long=long, d=d, entry=entry, stop=stop, is_at=is_at, ok_at=ok_at,
        shipped=shipped, code=code, path_or=path_or, intrabar_or=intrabar_or,
        born_past=born_past, menu=menu_arr, stamp_r=stamp_r,
        poi_r=poi_r, poi_filled=poi_filled, poi_fillbar=poi_fillbar,
        real_r=real_r, filled=filled, cost_r=cost_r, spread_r=spread_r, idx=idx,
    )
    with gzip.open(args.out + ".keys.jsonl.gz", "wt") as fh:
        for a in range(n):
            fh.write(json.dumps([cid[a], inst[a], sym[a], fam[a], day[a]]) + "\n")
    Path(args.out + ".meta.json").write_text(json.dumps({
        "month": mm, "n": n, "menu_names": menu_names, "horizon": HOR,
        "target_r": TARGET_R, "entry_window": ENTRY_WINDOW,
        "roster_dir": ROSTER[mm], "generated_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=1))
    print("WROTE", args.out, flush=True)


if __name__ == "__main__":
    main()
