"""d6_cancel — the obvious repair, priced: enter on the forming bar, FLATTEN at the
bar close if the setup does not re-emit.

The +0.209 R/trade earliness lever lives on the paired subset, whose membership is
only knowable at the M15 close.  But the close is only 1-14 minutes away, and a
live engine CAN hold the position until then and flatten it if the generator does
not re-emit the setup.  That contract is implementable end to end and it harvests
the paired leg in full.  This module prices it, and prices the two variants that
bound it (flatten at the close vs. flatten one bar later).

Everything is charged: the phantom leg pays a full entry toll AND a full exit toll
(2 x cost_r), because it opens and closes a position for nothing.

    python3 d6_cancel.py --months 202601,202602,202603 --out /tmp/d6/D6_CANCEL_V1.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
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


def blk(rows, key="net"):
    if not rows:
        return {"n": 0}
    v = np.array([r[key] for r in rows], float)
    by_day = defaultdict(lambda: [0.0, 0])
    for r in rows:
        by_day[r["m"] + "|" + r["day"]][0] += r[key]
        by_day[r["m"] + "|" + r["day"]][1] += 1
    out = {"n": int(len(v)), "net_r": float(v.mean()),
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

    res = {"months": months, "generated_utc": datetime.now(timezone.utc).isoformat()}
    paired_rows, phantom_rows = [], []

    for m in months:
        rows = D.load(m, fams=E5)
        tape = E.Tape(L.SYMBOLS, [m])
        for r in rows:
            P = r.get("P")
            if not P:
                continue
            if r.get("C"):
                paired_rows.append({"m": m, "day": r["day_part"], "f": r["f"],
                                    "net": P["g2"] - P["cr"],
                                    "net15": P["g15"] - P["cr15"]})
                continue
            # phantom: exit at the close of the forming bar (stamp bar_open+14)
            i = tape.idx(r["t_part"])
            j = tape.idx(r["b"])
            d = P["d"]
            long = r["sd"] == "L"
            row = {"m": m, "day": r["day_part"], "f": r["f"], "cost": P["cr"]}
            for label, off in (("close", 14), ("close_plus_1bar", 29)):
                px = tape.c[r["s"]][j + off] if 0 <= j + off < tape.n else np.nan
                if px != px:
                    row[label] = None
                    continue
                g = (px - P["e"]) / d if long else (P["e"] - px) / d
                # a stop inside the window still stops out first: floor at -1R
                row[label] = max(g, -1.0)
            phantom_rows.append(row)

    # ---- the three books
    def book(kind, exit_key, double_toll=True):
        rows = []
        for r in paired_rows:
            rows.append({"m": r["m"], "day": r["day"], "net": r["net"]})
        for r in phantom_rows:
            g = r.get(exit_key)
            if g is None:
                continue
            toll = r["cost"] * (2.0 if double_toll else 1.0)
            rows.append({"m": r["m"], "day": r["day"], "net": g - toll})
        return blk(rows)

    res["paired_leg_full_hold"] = blk([{"m": r["m"], "day": r["day"], "net": r["net"]}
                                       for r in paired_rows])
    res["phantom_leg_gross_at_bar_close"] = blk(
        [{"m": r["m"], "day": r["day"], "net": r["close"]}
         for r in phantom_rows if r["close"] is not None])
    res["phantom_leg_net_at_bar_close_double_toll"] = blk(
        [{"m": r["m"], "day": r["day"], "net": r["close"] - 2 * r["cost"]}
         for r in phantom_rows if r["close"] is not None])
    res["phantom_leg_net_at_bar_close_single_toll"] = blk(
        [{"m": r["m"], "day": r["day"], "net": r["close"] - r["cost"]}
         for r in phantom_rows if r["close"] is not None])

    res["BOOK_cancel_at_close_double_toll"] = book("cancel", "close", True)
    res["BOOK_cancel_at_close_single_toll"] = book("cancel", "close", False)
    res["BOOK_cancel_one_bar_later_double_toll"] = book("cancel", "close_plus_1bar", True)
    res["BOOK_zero_toll_on_cancels_UPPER_BOUND"] = blk(
        [{"m": r["m"], "day": r["day"], "net": r["net"]} for r in paired_rows]
        + [{"m": r["m"], "day": r["day"], "net": r["close"]}
           for r in phantom_rows if r["close"] is not None])
    res["BOOK_free_cancel_ORACLE_paired_only"] = res["paired_leg_full_hold"]

    res["counts"] = {"paired": len(paired_rows), "phantom": len(phantom_rows),
                     "phantom_priced_at_close": sum(1 for r in phantom_rows
                                                    if r["close"] is not None)}

    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
