"""pbg_phantom — can the phantom leg be suppressed?

For every at-market setup-bar, split by the FIRST minute at which the partial-bar
generator emitted, and price the two legs separately:

  * paired   — the setup also exists at the M15 close (it "completed")
  * phantom  — it never did

If precision rises with the firing minute fast enough, and the confirmed leg stays
positive, a minute floor is the design.  If it does not, the phantom leg is a
property of the mechanism and no cadence choice removes it.

    python3 pbg_phantom.py --in /tmp/pbg_full_jan --month 202601 --out PBG_PHANTOM_JAN_V1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5]))

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402
from pbg_analyze import (  # noqa: E402
    AT_MARKET,
    EARLY5,
    load_rows,
    paired_bootstrap,
    setup_key,
    summarise,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", default="202601")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()

    def price(r, d0=None):
        i = tape.idx(r["t"])
        entry, stop = r["e"], r["sl"]
        d = abs(entry - stop) if d0 is None else d0
        if not (d > 0):
            return None
        stop_eff = entry - d if r["d"] == "L" else entry + d
        w = E.walk(tape, r["s"], i, entry=entry, stop=stop_eff,
                   long=(r["d"] == "L"), target_r=2.0)
        if w is None:
            return None
        g, ex, _bar, _n = w
        cpx, _ = cm.cost_px(r["s"], r["t"], entry, r["d"] == "L")
        return {"gross": g, "cost_r": cpx / d, "bps_gross": g * d / entry * 1e4,
                "bps_net": (g - cpx / d) * d / entry * 1e4, "day": r["t"][:10],
                "exit": ex, "risk": d}

    by_key = defaultdict(dict)
    for r in load_rows(args.indir):
        if r["f"] in AT_MARKET:
            by_key[setup_key(r)][r["k"]] = r

    out = {"month": args.month, "cohorts": {}}
    for cname, fams in (("AT_MARKET", set(AT_MARKET)), ("EARLY5", set(EARLY5))):
        per_k = {}
        cum = {}
        rows_by_k = defaultdict(lambda: {"paired": [], "phantom": [],
                                         "paired_d0": [], "delta": []})
        for k, per in by_key.items():
            if k[1] not in fams:
                continue
            pkm = min((x for x in per if x < 15), default=None)
            if pkm is None:
                continue
            tp = price(per[pkm])
            if tp is None:
                continue
            ck = per.get(15)
            if ck is None:
                rows_by_k[pkm]["phantom"].append(tp)
            else:
                tc = price(ck)
                if tc is None:
                    continue
                td = price(per[pkm], d0=tc["risk"])
                rows_by_k[pkm]["paired"].append(tp)
                if td:
                    rows_by_k[pkm]["paired_d0"].append(td)
                    rows_by_k[pkm]["delta"].append(
                        (tc["day"], (td["gross"] - td["cost_r"]) - (tc["gross"] - tc["cost_r"]))
                    )
        for kk in range(1, 15):
            b = rows_by_k[kk]
            npair, nph = len(b["paired"]), len(b["phantom"])
            per_k[str(kk)] = {
                "n_paired": npair,
                "n_phantom": nph,
                "precision": npair / (npair + nph) if (npair + nph) else None,
                "paired": summarise(b["paired"], f"paired_firstk{kk}"),
                "paired_d0": summarise(b["paired_d0"], f"paired_d0_firstk{kk}"),
                "phantom": summarise(b["phantom"], f"phantom_firstk{kk}"),
                "delta_net_d0": paired_bootstrap(b["delta"]) if b["delta"] else None,
            }
        # cumulative: a MINUTE FLOOR — take only setups whose first emission is at
        # or after minute f (i.e. refuse the very early firings).
        for f in range(1, 15):
            P = [x for kk in range(f, 15) for x in rows_by_k[kk]["paired"]]
            H = [x for kk in range(f, 15) for x in rows_by_k[kk]["phantom"]]
            cum[str(f)] = {
                "n_paired": len(P),
                "n_phantom": len(H),
                "precision": len(P) / (len(P) + len(H)) if (len(P) + len(H)) else None,
                "book": summarise(P + H, f"book_floor_min{f}"),
                "paired": summarise(P, f"paired_floor_min{f}"),
                "phantom": summarise(H, f"phantom_floor_min{f}"),
            }
        out["cohorts"][cname] = {"by_first_minute": per_k, "minute_floor": cum}

    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    for cname in out["cohorts"]:
        print("=" * 78)
        print(cname, " k | n_pair n_phan  prec | paired net | phantom net | floor book net")
        c = out["cohorts"][cname]
        for kk in range(1, 15):
            a = c["by_first_minute"][str(kk)]
            f = c["minute_floor"][str(kk)]
            print(
                " %2d | %6d %6d %.3f | %+9.5f | %+9.5f | %+9.5f (n=%d, days+ %d/%d)"
                % (
                    kk, a["n_paired"], a["n_phantom"], a["precision"] or 0,
                    a["paired"].get("net_r_per_trade", float("nan")),
                    a["phantom"].get("net_r_per_trade", float("nan")),
                    f["book"].get("net_r_per_trade", float("nan")),
                    f["book"].get("n", 0),
                    f["book"].get("days_net_positive", 0), f["book"].get("n_days", 0),
                )
            )


if __name__ == "__main__":
    main()
