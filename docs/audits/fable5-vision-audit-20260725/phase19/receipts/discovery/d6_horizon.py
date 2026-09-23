"""d6_horizon — the truncation question, answered rather than disclosed.

30.96 % of the winner's trades resolve at the path end rather than at a target or
a stop, so the published number is partly a statement about the 120-M1-bar
horizon.  This re-walks BOTH legs at 120 / 240 / 480 / 960 M1 bars and reports the
book at each, so the horizon dependence is a measured curve rather than a caveat.

    python3 d6_horizon.py --months 202601,202602,202603 --out /tmp/d6/D6_HORIZON_V1.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PBG))
sys.path.insert(0, str(HERE.parents[5]))

import d6_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

HORIZONS = (120, 240, 480, 960)


def blk(rows):
    if not rows:
        return {"n": 0}
    v = np.array([r["net"] for r in rows], float)
    by_day = defaultdict(lambda: [0.0, 0])
    for r in rows:
        by_day[r["k"]][0] += r["net"]
        by_day[r["k"]][1] += 1
    out = {"n": int(len(v)), "net_r": float(v.mean()),
           "gross_r": float(np.mean([r["g"] for r in rows])),
           "truncation_share": float(np.mean([r["x"] == "path_end" for r in rows])),
           "days_positive": sum(1 for d in by_day if by_day[d][0] > 0),
           "n_days": len(by_day)}
    out["boot"] = D.bootstrap_days(by_day)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()
    E5 = set(D.EARLY5)

    acc = {h: {"paired_partial": [], "paired_close": [], "phantom": []} for h in HORIZONS}
    for m in months:
        rows = D.load(m, fams=E5)
        tape = E.Tape(L.SYMBOLS, [m])
        for r in rows:
            for armk, leg in (("P", "paired_partial" if r.get("C") else "phantom"),
                              ("C", "paired_close")):
                a = r.get(armk)
                if not a:
                    continue
                if armk == "C" and not r.get("P"):
                    continue          # keep the close leg on the paired subset only
                iso = r["t_part"] if armk == "P" else r["t_close"]
                i = tape.idx(iso)
                d = a["d"]
                entry = a["e"]
                long = r["sd"] == "L"
                stop = entry - d if long else entry + d
                for h in HORIZONS:
                    w = E.walk(tape, r["s"], i, entry=entry, stop=stop, long=long,
                               target_r=2.0, horizon=h)
                    if w is None:
                        continue
                    g, x, _eb, _nb = w
                    acc[h][leg].append({"net": g - a["cr"], "g": g, "x": x,
                                        "k": m + "|" + (r["day_part"] if armk == "P"
                                                        else r["day_close"])})

    res = {"months": months, "horizons_m1_bars": list(HORIZONS),
           "generated_utc": datetime.now(timezone.utc).isoformat(), "by_horizon": {}}
    for h in HORIZONS:
        cell = {k: blk(v) for k, v in acc[h].items()}
        book = acc[h]["paired_partial"] + acc[h]["phantom"]
        cell["BOOK_partial_implementable"] = blk(book)
        res["by_horizon"][str(h)] = cell
    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
