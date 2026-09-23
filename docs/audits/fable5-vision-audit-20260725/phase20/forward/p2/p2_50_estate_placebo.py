"""p2-50 — the side placebo, turned on the SLEEVE ESTATE's exit frontier.

WHY. On the broad families, a coin-flipped-direction placebo reproduces 71-180 % of the
"delete the take-profit" effect at every resolution down to one minute (`P2_RESOLUTION_V1.json`).
That says the effect is a property of a fixed-R cap on this price process and not of the
families' ideas.

The estate's exit-frontier work has never had that control. AD swept 1,631 gated exit cells over
25 sleeves and found EVERY sleeve improves (median +0.249 R/day); AK's `target_4R` and AU's
`target_5R` -- one on an ARMED sleeve, one the estate's single standing admission -- were both
selected by that machinery. If a coin flip buys the same improvement, the improvement is not
evidence about the sleeve.

METHOD. AD's own `resimulate`, unmodified, on AD's own rows and AD's own bar archive. The only
thing that changes between the REAL and PLACEBO arms is `row["direction"]`, coin-flipped with a
fixed seed. Everything else -- the stop distance in price, the decision bar, the variant, the
maxbars, the winsorisation -- is identical, so the difference between the two arms is the whole
of the directional content of the exit cell's value.

Two paired quantities per (sleeve, variant):
    delta_R      mean r_gross under the variant minus mean r_gross under `as_walked`
    the same on the flipped population

and their difference, which is the part of the exit cell's value that its sleeve actually earned.
"""

from __future__ import annotations

import collections
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(P7))

import ad_exit_sweep as AD  # noqa: E402

HERE = Path(__file__).resolve().parent
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
#: the two cells that reach a decision: AK's frontier winner on an ARMED sleeve, and the
#: estate's one standing admission.
HEADLINE = {
    "sub_xvol_pullback": ("target_4R", 4.0),
    "mx_btcusd_d1_donchian_20_breakout": ("target_5R", 5.0),
}

VARIANTS = [
    AD.AS_WALKED,
    AD.Variant(name="target_2R", family="target", target_mode="fixed_r", target_r=2.0),
    AD.Variant(name="target_3R", family="target", target_mode="fixed_r", target_r=3.0),
    AD.Variant(name="target_4R", family="target", target_mode="fixed_r", target_r=4.0),
    AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0),
    AD.Variant(name="no_target", family="target", target_mode="no_target"),
]


def flip(rows, seed=17):
    import random
    rng = random.Random(seed)
    out = []
    for r in rows:
        q = dict(r)
        if rng.random() < 0.5:
            q["direction"] = -int(r["direction"])
        out.append(q)
    return out


def mean_r(rows):
    if not rows:
        return None
    return statistics.fmean(float(r["r_gross"]) for r in rows)


def per_day(rows):
    if not rows:
        return None
    days = {r["entry_utc"][:10] for r in rows}
    return sum(float(r["r_gross"]) for r in rows) / max(1, len(days))


def main():
    t0 = time.time()
    aa = json.load(gzip.open(AA_IN, "rt"))
    by_sleeve_src = aa["trades"]
    n_all = sum(len(v) for v in by_sleeve_src.values())
    print(f"AA rows: {n_all} in {len(by_sleeve_src)} sleeves  ({time.time()-t0:.0f}s)",
          file=sys.stderr)
    series, index, _ = AD.load_bars()
    print(f"bar series: {len(series)}  ({time.time()-t0:.0f}s)", file=sys.stderr)

    by_sleeve = {k: list(v) for k, v in by_sleeve_src.items()}

    out = {"schema": "gtos.p2.estate_side_placebo.v1",
           "source": "phase6/receipts/AA_ESTATE_TRADES.json.gz via phase7 ad_exit_sweep.resimulate",
           "seed": 17, "sleeves": {}}

    for sleeve, rows in sorted(by_sleeve.items()):
        if len(rows) < 30:
            continue
        rows_p = flip(rows)
        base_real = base_plc = None
        cells = {}
        for v in VARIANTS:
            rr, _ = AD.resimulate(rows, v, series, index, None, "FTMO", None)
            pp, _ = AD.resimulate(rows_p, v, series, index, None, "FTMO", None)
            mr, mp = mean_r(rr), mean_r(pp)
            dr, dp = per_day(rr), per_day(pp)
            if v.name == "as_walked":
                base_real, base_plc = mr, mp
                base_dr, base_dp = dr, dp
                cells[v.name] = {"n": len(rr), "R_per_trade": mr, "R_per_day": dr,
                                 "placebo_R_per_trade": mp, "placebo_R_per_day": dp}
                continue
            cells[v.name] = {
                "n": len(rr),
                "R_per_trade": mr, "R_per_day": dr,
                "delta_R_per_trade": None if mr is None or base_real is None else mr - base_real,
                "delta_R_per_day": None if dr is None or base_dr is None else dr - base_dr,
                "placebo_delta_R_per_trade":
                    None if mp is None or base_plc is None else mp - base_plc,
                "placebo_delta_R_per_day":
                    None if dp is None or base_dp is None else dp - base_dp,
            }
            c = cells[v.name]
            if c["delta_R_per_day"] is not None and c["placebo_delta_R_per_day"] is not None:
                c["sleeve_earned_R_per_day"] = c["delta_R_per_day"] - c["placebo_delta_R_per_day"]
        out["sleeves"][sleeve] = {
            "n_rows": len(rows),
            "armed": sleeve in ARMED,
            "headline_cell": HEADLINE.get(sleeve, [None])[0],
            "cells": cells,
        }
        print(f"  {sleeve:42s} n={len(rows):6d}  "
              f"{time.time()-t0:.0f}s", file=sys.stderr)

    p = HERE / "P2_ESTATE_SIDE_PLACEBO_V1.json"
    p.write_text(json.dumps(out, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
