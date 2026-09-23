"""r1-CM — price the CM cell (`stop_1p5x_target_scale`) on the corrected quote convention.

WHY THIS RUNS
-------------
CM — FTMO `crypto` @ `stop_1p5x_target_scale`, armed 2026-08-06 — was ROLLED BACK on the
owner's word on 2026-08-10 (host `4d28676f8`, B3413): FTMO crypto is back on the shipped 4R
contract, and re-arming is gated on pricing that exact cell on the CORRECTED quote-convention
walker (CLAUDE.md plan position 2026-08-10). The wave-20 surface
(`R1_FRONTIER_SURFACE_V1.json`) walked 35 target/stop_only x maxbars cells x 3 bands x
2 conventions over crypto's 181-trade population — but its grid holds the stop width at
1.0x, so the CM geometry is in none of its 210 crypto cells. Every number CM was armed on
came from the pre-repair convention or from CM's own separate TRAIN/VAL lane; nobody had
priced the cell on THIS walker over THIS population.

THE CELL, FROM THE WIRING (all cites at the base of this branch, `2edefd48a`)
-----------------------------------------------------------------------------
  override        `execution_packets.py:213-217`  "crypto": stop_distance_multiplier=1.5,
                  frontier_cell="stop_1p5x_target_scale"
  committed prof  `execution_packets.py:80`       policy="time_stop", final_target_r=4.0,
                  time_stop_bars=1280  (= 80 H4 bars; crypto's 181 rows are all H4)
  merge           `execution_packets.py:413-419`  resolve_exit_profile = committed + override
  application     `execution_packets.py:530-535`  risk_distance = base_risk_distance * 1.5
                  `execution_packets.py:564-568`  broker SL rebuilt at entry -/+ risk_distance
                  `execution_packets.py:569`      broker TP = entry +/- 4.0 * risk_distance
So the walked contract is: stop at 1.5x the native sl_distance_price (that IS -1R, because
live sizes off the scaled risk distance), target at 4.0R of the scaled unit = 6.0x the
native distance, horizon 80 own H4 bars (1280 M15 bars and maxbars=80 fire on the same bar
at the same close — `execution_packets.py:184-186`), no trail, no partial. Identical to
AD's `stop_1.5x_tgtscale` research cell (`phase7/receipts/ad_exit_sweep.py:318,324,338,357`,
declared at `:501-507`), whose scaling-mode equivalence to the live fixed-4R construction
requires target_dist == 4 x sl on every row — asserted below rather than assumed.

WHAT THIS IS NOT
----------------
Not a new grid and not an admission. The CM cell was declared by AD's stop_width family and
selected by Session CM; the three comparison cells are re-reads of committed surface cells.
Output is evidence characterisation for an owner decision (re-arm CM / keep shipped 4R /
move to the surface best); the decision is Borhen's.

CONTROLS (each refuses the write on failure)
--------------------------------------------
C1  population invariants: exactly the estate's crypto rows, all H4, and
    target_dist == 4.0 x sl_distance_price bit-for-bit on every row.
C2  the three stop_mult=1.0 cells reproduce `R1_FRONTIER_SURFACE_V1.json`'s crypto record
    EXACTLY (n, r_per_trade, r_per_day, se, folds, exit_reasons) — same population, same
    folds, same bands, same walker, or this receipt is about a different program.
C3  construction identity, behavioural: the CM cell walked with the walker's
    `tm * (stop_mult * sd)` target must produce the SAME winsorized R on every trade as a
    direct replay under AD's `target_dist * stop_mult` target — both conventions, mid band.

R UNITS, SO THE COMPARISON IS READ RIGHT
----------------------------------------
Each contract's R is its own risk unit — the CM cell's R denominates on the 1.5x stop.
Live, the book sizes every trade to the same cash per R off the contract's own stop
distance (`risk_distance` above feeds sizing), so 1R is the same cash under either
contract and R/day is directly comparable across contracts. That is also how AD's sweep
and Session CM compared them.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import r1_estate_rewalk as R  # noqa: E402  (loaders, BANDS, TF maps, TRADES path)
import r1_frontier_surface_sweep as S  # noqa: E402  (walk + fold convention)

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

SLEEVE = "crypto"
SURFACE = HERE / "R1_FRONTIER_SURFACE_V1.json"
OUT = HERE / "R1_CM_CELL_PRICING_V1.json"

#: (key, stop_mult, tm, maxbars, role). Keys mirror the surface's cell-key grammar so the
#: two receipts read side by side; the CM key is new vocabulary because the surface's grid
#: cannot express a stop width.
CELLS = (
    ("stop_1p5x_target_scale|maxbars_80", 1.5, 4.0, 80,
     "THE CM CELL — live: stop x1.5 (= -1R of the scaled unit), broker TP 4R of the "
     "scaled unit = 6.0x native sd, horizon 1280 M15 = 80 H4 bars"),
    ("target_4.0R|maxbars_80", 1.0, 4.0, 80,
     "the SHIPPED contract crypto runs today (rolled back to it 2026-08-10)"),
    ("target_4.0R|maxbars_160", 1.0, 4.0, 160,
     "surface best cell under CORRECTED, mid and high bands"),
    ("target_5.0R|maxbars_160", 1.0, 5.0, 160,
     "surface best cell under CORRECTED, low band (and the PUBLISHED argmax at all three)"),
)

CM_KEY = CELLS[0][0]
SHIPPED_KEY = CELLS[1][0]


def cell_stats(vals, by_day, reasons, unpriceable, skips):
    ndays = max(1, len(by_day))
    n = len(vals)
    return {
        "n": n,
        "n_days": len(by_day),
        "r_per_trade": round(statistics.fmean(vals), 6),
        "r_per_day": round(math.fsum(vals) / ndays, 6),
        "se": round(statistics.pstdev(vals) / math.sqrt(n), 6) if n > 1 else None,
        "exit_reasons": dict(reasons),
        "maxbars_share": round(reasons.get("maxbars", 0) / n, 6) if n else None,
        "unpriceable": unpriceable,
        "skips": dict(skips),
        "folds": S.fold_positivity(by_day),
    }


def c1_population(trades):
    """Exactly the estate's crypto rows, all H4, target == 4 x stop bit-for-bit."""
    bad_tf = [r for r in trades if int(r["timeframe"]) != 16388]
    bad_tgt = []
    for r in trades:
        sd = float(r["sl_distance_price"])
        td = r.get("target_dist")
        if td is None or float(td) != 4.0 * sd:
            bad_tgt.append({"symbol": r["symbol"], "decision_bar_iso": r["decision_bar_iso"],
                            "target_dist": td, "sl_distance_price": sd})
    return {
        "n": len(trades),
        "all_h4": not bad_tf,
        "target_is_4x_stop_bitwise_all_rows": not bad_tgt,
        "violations": bad_tgt[:8],
        "ok": (not bad_tf) and (not bad_tgt),
    }


def c2_reproduction(rec, surface_crypto):
    """The stop_mult=1.0 cells must reproduce the committed surface record exactly."""
    checks = []
    for key, stop_mult, _tm, _mb, _role in CELLS:
        if stop_mult != 1.0:
            continue
        for band in R.BANDS:
            for conv in ("published", "corrected"):
                got = rec[key][band][conv]
                want = surface_crypto["cells"][f"{key}|{band}|{conv}"]
                same = (
                    got["n"] == want["n"]
                    and got["r_per_trade"] == want["r_per_trade"]
                    and got["r_per_day"] == want["r_per_day"]
                    and got["se"] == want["se"]
                    and got["folds"] == want["folds"]
                    and got["exit_reasons"] == want["exit_reasons"]
                )
                checks.append({"cell": f"{key}|{band}|{conv}", "reproduces": same})
    return {"checked": len(checks), "all_reproduce": all(c["reproduces"] for c in checks),
            "failures": [c["cell"] for c in checks if not c["reproduces"]]}


def c3_construction_identity(trades, series, index, stop_mult, tm):
    """CM walked via `tm * (stop_mult * sd)` == direct replay via AD's `td * stop_mult`.

    Behavioural, not arithmetic: both routes are replayed and every winsorized R must
    match bit-for-bit, both conventions, mid band. This is the check that the live
    fixed-4R-of-the-scaled-unit construction and AD's scales_with_stop construction are
    the SAME cell on this population.
    """
    mismatches, checked = [], 0
    for conv in (False, True):
        vals_a, _, _, _, _ = S.walk(trades, series, index, tm, 80, "mid", conv,
                                    stop_mult=stop_mult)
        vals_b = []
        for r in trades:
            key = (r["symbol"], int(r["timeframe"]))
            if key not in index:            # mirror S.walk's skips exactly, or the two
                continue                    # vectors de-align and C3 lies about a shift
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                continue
            bars, times = series[key]
            if i + 2 >= len(bars):
                continue
            d = int(r["direction"])
            sd = float(r["sl_distance_price"]) * stop_mult          # AD :318
            td = float(r["target_dist"]) * stop_mult                # AD :324 scales_with_stop
            pol = ExitPolicy(target_dist=td, maxbars=80, label="ad_route")
            if conv:
                at = times[i] + dt.timedelta(minutes=R.TF_MINUTES[int(r["timeframe"])])
                try:
                    sp = spread_for(r["symbol"], at, account="FTMO", band="mid")
                except SpreadUnavailable:
                    continue
                anchor = replay_anchor(bars[i].c, d, sp, BarQuote.BID)
                res = replay(bars, i, d, stop_dist=sd, policy=pol, entry_price=anchor)
            else:
                res = replay(bars, i, d, stop_dist=sd, policy=pol)
            vals_b.append(winsorize_R(res.r_gross))
        checked += len(vals_a)
        if len(vals_a) != len(vals_b):
            mismatches.append({"conv": conv, "len_a": len(vals_a), "len_b": len(vals_b)})
            continue
        for k, (a, b) in enumerate(zip(vals_a, vals_b)):
            if a != b:
                mismatches.append({"conv": conv, "row": k, "walker": a, "ad_route": b})
    return {"rows_checked": checked, "identical": not mismatches,
            "mismatches": mismatches[:8]}


def main() -> int:
    t0 = time.time()
    series, index = R.load_series()
    estate = json.load(gzip.open(R.TRADES))
    trades = estate["trades"][SLEEVE]
    surface_crypto = json.load(open(SURFACE))["sleeves"][SLEEVE]

    c1 = c1_population(trades)
    if not c1["ok"]:
        print("C1 FAILED — population is not the surface's crypto population; refusing")
        print(json.dumps(c1, indent=1))
        return 2

    rec = {}
    raw_vals = {}
    for key, stop_mult, tm, mb, role in CELLS:
        rec[key] = {"role": role, "stop_mult": stop_mult, "target_r_of_unit": tm,
                    "maxbars_own": mb}
        for band in R.BANDS:
            rec[key][band] = {}
            for conv_name, conv in (("published", False), ("corrected", True)):
                vals, by_day, reasons, unp, skips = S.walk(
                    trades, series, index, tm, mb, band, conv, stop_mult=stop_mult)
                rec[key][band][conv_name] = cell_stats(vals, by_day, reasons, unp, skips)
                raw_vals[(key, band, conv_name)] = vals
        print(f"walked {key}  ({time.time()-t0:.0f}s)", flush=True)

    c2 = c2_reproduction(rec, surface_crypto)
    if not c2["all_reproduce"]:
        print("C2 FAILED — committed surface cells do not reproduce; refusing")
        print(json.dumps(c2, indent=1))
        return 2

    c3 = c3_construction_identity(trades, series, index, 1.5, 4.0)
    if not c3["identical"]:
        print("C3 FAILED — walker route and AD route disagree on the CM cell; refusing")
        print(json.dumps(c3, indent=1))
        return 2

    # ---- the comparison the rollback gate asks for -------------------------------------
    surface_best_corrected = {
        band: surface_crypto["best"][band]["corrected"] for band in R.BANDS
    }

    def paired_trade_delta(band, conv_name):
        """Per-trade CM-minus-shipped, valid because the two walks share every skip rule
        (skips depend on series/room/spread only, never on the policy), so index k is the
        same trade in both vectors — asserted, not assumed."""
        a = raw_vals[(CM_KEY, band, conv_name)]
        b = raw_vals[(SHIPPED_KEY, band, conv_name)]
        if len(a) != len(b):
            raise AssertionError(f"paired vectors de-aligned: {len(a)} vs {len(b)}")
        deltas = [x - y for x, y in zip(a, b)]
        n = len(deltas)
        return {
            "n": n,
            "mean": round(statistics.fmean(deltas), 6),
            "se": round(statistics.pstdev(deltas) / math.sqrt(n), 6) if n > 1 else None,
            "frac_positive": round(sum(1 for x in deltas if x > 1e-12) / n, 6),
            "frac_negative": round(sum(1 for x in deltas if x < -1e-12) / n, 6),
        }

    comparison = {}
    comparison_published = {}
    for band in R.BANDS:
        cm = rec[CM_KEY][band]["corrected"]
        sh = rec[SHIPPED_KEY][band]["corrected"]
        best_cell = surface_best_corrected[band]["cell"]
        best = rec[f"{best_cell}"][band]["corrected"]
        paired = None
        if cm["folds"] and sh["folds"]:
            deltas = [round(a - b, 6) for a, b in
                      zip(cm["folds"]["folds"], sh["folds"]["folds"])]
            paired = {"cm_minus_shipped_fold_r_per_trade": deltas,
                      "improved": sum(1 for x in deltas if x > 0),
                      "latest_fold_delta": deltas[-1]}
        comparison[band] = {
            "cm_r_per_day": cm["r_per_day"], "cm_r_per_trade": cm["r_per_trade"],
            "cm_fold_positive": cm["folds"]["positive"] if cm["folds"] else None,
            "shipped_r_per_day": sh["r_per_day"],
            "cm_minus_shipped_r_per_day": round(cm["r_per_day"] - sh["r_per_day"], 6),
            "surface_best_cell": best_cell,
            "surface_best_r_per_day": best["r_per_day"],
            "cm_minus_surface_best_r_per_day": round(
                cm["r_per_day"] - best["r_per_day"], 6),
            "paired_folds_vs_shipped": paired,
            "paired_trade_delta_vs_shipped": paired_trade_delta(band, "corrected"),
        }
        cm_p = rec[CM_KEY][band]["published"]
        sh_p = rec[SHIPPED_KEY][band]["published"]
        best_p_cell = surface_crypto["best"][band]["published"]["cell"]
        comparison_published[band] = {
            "cm_r_per_day": cm_p["r_per_day"],
            "shipped_r_per_day": sh_p["r_per_day"],
            "cm_minus_shipped_r_per_day": round(
                cm_p["r_per_day"] - sh_p["r_per_day"], 6),
            "surface_best_cell": best_p_cell,
            "surface_best_r_per_day": rec[best_p_cell][band]["published"]["r_per_day"]
            if best_p_cell in rec else None,
            "paired_trade_delta_vs_shipped": paired_trade_delta(band, "published"),
        }

    out = {
        "schema": "gtos.r1.cm_cell_pricing.v1",
        "what": ("the exact CM contract (crypto @ stop_1p5x_target_scale), the shipped 4R "
                 "contract, and the corrected-surface best cells, walked over the SAME "
                 "population, SAME folds, SAME bands as R1_FRONTIER_SURFACE_V1.json, "
                 "both conventions"),
        "why": ("CM rolled back 2026-08-10 (host 4d28676f8, B3413); re-arm gated on "
                "pricing this cell on the corrected-quote walker"),
        "geometry_provenance": {
            "override": "src/components/ultimate_book/execution_packets.py:213-217",
            "committed_profile": "src/components/ultimate_book/execution_packets.py:80",
            "resolution": "src/components/ultimate_book/execution_packets.py:413-419",
            "application": "src/components/ultimate_book/execution_packets.py:530-535,564-569",
            "research_cell": "phase7/receipts/ad_exit_sweep.py:318,324,338,357,501-507",
            "horizon_equivalence": "src/components/ultimate_book/execution_packets.py:184-186",
        },
        "population": {"sleeve": SLEEVE, "trades": str(R.TRADES), "n": len(trades),
                       "surface": str(SURFACE)},
        "bands": list(R.BANDS),
        "fold_convention": "chronological fifths of decision days (r1_frontier_surface_sweep.fold_positivity)",
        "winsor": {"lo": -1.3, "hi": 5.0,
                   "note": "same winsorize_R as every r1 receipt; target_5R cells sit at the cap"},
        "r_unit_note": ("each contract's R is its own risk unit (the CM cell's R is the "
                        "1.5x stop); live sizing puts the same cash on 1R of either "
                        "contract, so r_per_day is directly comparable across contracts"),
        "controls": {"c1_population": c1, "c2_surface_reproduction": c2,
                     "c3_construction_identity": c3},
        "cells": rec,
        "comparison_corrected": comparison,
        "comparison_published_for_reference": comparison_published,
        "decision_note": ("evidence characterisation only — re-arm / keep shipped / move "
                          "cell is an owner decision (OD); nothing here is an admission "
                          "claim and no new grid was opened"),
        "elapsed_s": round(time.time() - t0, 1),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(f"WROTE {OUT} in {out['elapsed_s']}s")
    print(json.dumps(comparison, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
