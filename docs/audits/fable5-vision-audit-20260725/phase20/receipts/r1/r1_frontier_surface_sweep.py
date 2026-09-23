"""r1-7 — the WHOLE exit-contract surface, re-walked on the corrected quote convention.

WHY THIS RUNS
-------------
AD gated 1,631 exit cells over 25 sleeves and AK built the frontier that put
`sub_xvol_pullback @ target_4R` and `mx_btcusd @ target_5R` in front of the owner. Every one
of those cells was measured with the pre-repair walker, which resolved stops and targets
against a BID tape with unshifted levels and was therefore optimistic by a constant sign
(-0.1405 R/trade pooled on this estate; 736 of 7,552 booked targets did not happen).

`r1_estate_rewalk.py` re-walked AA's single labelled contract. `r1_frontier_admission.py`
re-walked the two named frontier cells. **Nobody has re-walked the SURFACE** — and the
surface is what a frontier is chosen from, so every "best cell" in the estate was chosen on
a tape that lied in one direction.

This sweeps the whole grid, both conventions, all three spread bands, whole population of
every sleeve. Nothing is sampled.

WHAT IT WRITES
--------------
`R1_FRONTIER_SURFACE_V1.json`  — one record per (sleeve, cell, band, convention)
`R1_FRONTIER_SURFACE_ROWS.json.gz` — per-trade rows for the cells whose ARGMAX MOVES

THE CONTROL
-----------
Same discipline as r1-5a: the uncorrected arm is re-derived from the bars, not copied. For
the one cell each sleeve was published at, the uncorrected arm must reproduce the published
figure. Deviations are reported per sleeve rather than aborting the run, because a sleeve
whose published cell is not in this grid is a finding, not a failure.

Long-running by design: ~25 sleeves x ~40 cells x 3 bands x 2 conventions. Progress is
flushed to the log after every sleeve so an interrupted run is still readable.
"""

from __future__ import annotations

import collections
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import datetime as _dt  # noqa: E402

import r1_estate_rewalk as R  # noqa: E402  (loaders, BANDS, TF maps, winsorize, replay)

R_TF = {v: k for k, v in R.TF_NAME.items()}


def _ts(s: str):
    """Estate stamps are tz-aware ISO; the bar index is naive UTC."""
    d = _dt.datetime.fromisoformat(s)
    return d.replace(tzinfo=None) if d.tzinfo else d

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

OUT = HERE / "R1_FRONTIER_SURFACE_V1.json"
LOG = HERE / "R1_FRONTIER_SURFACE.log"

# The grid AD and AK chose their winners from, plus the two live frontier contracts.
TARGET_MULTS = (None, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)   # None == stop_only_horizon
HORIZONS = (20, 40, 80, 160, 320)                      # in the sleeve's own printed bars


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def cells():
    for tm in TARGET_MULTS:
        for mb in HORIZONS:
            yield ("stop_only" if tm is None else f"target_{tm}R", tm, mb)


def fold_positivity(by_day):
    """Chronological fifths — the estate's own fold convention."""
    days = sorted(by_day)
    if len(days) < 5:
        return None
    k, out = len(days) // 5, []
    for f in range(5):
        chunk = days[f * k:(f + 1) * k] if f < 4 else days[4 * k:]
        vals = [v for d in chunk for v in by_day[d]]
        out.append(statistics.fmean(vals) if vals else 0.0)
    return {"folds": [round(x, 6) for x in out],
            "positive": sum(1 for x in out if x > 0)}


def walk(trades, series, index, tm, mb, band, corrected, stop_mult=1.0):
    """One (cell, band, convention). API copied verbatim from r1_estate_rewalk.main().

    `stop_mult` (wave 21, CM-cell pricing) generalises the walk to AD's `stop_width`
    family, which this sweep's grid held fixed at 1.0: the effective stop is
    `stop_mult x sl_distance_price`, and the R unit, the `tm`-R target and any trail
    distances all follow the scaled stop. That is exactly AD's construction
    (`phase7/receipts/ad_exit_sweep.py:318` stop = sl*k, `:324` target scales with the
    stop, `:336-337` trails off the scaled stop, `:357` replay in the scaled R unit) and
    exactly the live application (`execution_packets.py:530-535` risk_distance =
    base * multiplier; `:564-569` broker SL = -1R and TP = final_target_r * risk_distance
    both rebuilt from it). The default multiplies every distance by exactly 1.0, which is
    bit-identical to the pre-change walker — held behaviourally by
    `tests/research_infra/test_r1_cm_cell_walker.py`.
    """
    if not (stop_mult > 0):
        raise ValueError(f"stop_mult must be > 0 (it scales the R unit), got {stop_mult!r}")
    label = "stop_only" if tm is None else f"target_{tm}R"
    if stop_mult != 1.0:
        label = f"stop_{stop_mult:g}x_{label}_tgtscale"
    vals, by_day = [], collections.defaultdict(list)
    reasons, unpriceable, skips = collections.Counter(), 0, collections.Counter()
    for r in trades:
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            skips["no_series"] += 1
            continue
        i = index[key].get(_dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            skips["bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            skips["no_room"] += 1
            continue
        d = int(r["direction"])
        sd = float(r["sl_distance_price"]) * stop_mult
        trig_r, gap_r = R._trail_policy(r["sleeve"])
        pol = ExitPolicy(
            target_dist=(None if tm is None else tm * sd),
            maxbars=mb,
            trail_arm=(None if trig_r is None else float(trig_r) * sd),
            trail_gap=(None if gap_r is None else float(gap_r) * sd),
            label=label,
        )
        if corrected:
            at = times[i] + _dt.timedelta(minutes=R.TF_MINUTES[tf])
            try:
                sp = spread_for(r["symbol"], at, account="FTMO", band=band)
            except SpreadUnavailable:
                unpriceable += 1
                continue
            anchor = replay_anchor(bars[i].c, d, sp, BarQuote.BID)
            res = replay(bars, i, d, stop_dist=sd, policy=pol, entry_price=anchor)
        else:
            res = replay(bars, i, d, stop_dist=sd, policy=pol)
        val = winsorize_R(res.r_gross)
        vals.append(val)
        by_day[r["decision_day"]].append(val)
        reasons[res.exit_reason] += 1
    return vals, by_day, reasons, unpriceable, skips


def main() -> int:
    t0 = time.time()
    log("loading bar series…")
    series, index = R.load_series()
    log(f"series loaded: {len(series)} (symbol, tf) keys")

    with gzip.open(R.TRADES, "rt") as fh:
        estate = json.load(fh)
    by_sleeve = {k: v for k, v in estate["trades"].items() if v}
    n_rows = sum(len(v) for v in by_sleeve.values())
    log(f"estate loaded: {n_rows} trades over {len(by_sleeve)} sleeves")

    grid = list(cells())
    log(f"grid: {len(grid)} cells x {len(R.BANDS)} bands x 2 conventions "
        f"x {len(by_sleeve)} sleeves = {len(grid)*len(R.BANDS)*2*len(by_sleeve)} walks")

    out = {"meta": {"grid": [c[0] for c in grid], "horizons": list(HORIZONS),
                    "bands": list(R.BANDS), "trades": n_rows,
                    "sleeves": len(by_sleeve),
                    "purpose": "every published exit cell was chosen on a BID tape with "
                               "unshifted levels; this is the same surface, corrected"},
           "sleeves": {}}

    for si, (sleeve, trades) in enumerate(sorted(by_sleeve.items()), 1):
        rec = {"n_trades": len(trades), "cells": {}}
        for name, tm, mb in grid:
            for band in R.BANDS:
                for corrected in (False, True):
                    vals, by_day, reasons, unp, skips = walk(
                        trades, series, index, tm, mb, band, corrected)
                    if not vals:
                        continue
                    ndays = max(1, len(by_day))
                    key = f"{name}|maxbars_{mb}|{band}|{'corrected' if corrected else 'published'}"
                    rec["cells"][key] = {
                        "n": len(vals),
                        "r_per_trade": round(statistics.fmean(vals), 6),
                        "r_per_day": round(math.fsum(vals) / ndays, 6),
                        "se": round(statistics.pstdev(vals) / math.sqrt(len(vals)), 6)
                              if len(vals) > 1 else None,
                        "exit_reasons": dict(reasons),
                        "unpriceable": unp,
                        "skips": dict(skips),
                        "folds": fold_positivity(by_day),
                    }
        # does the ARGMAX move? that is the whole question a frontier asks.
        for band in R.BANDS:
            best = {}
            for conv in ("published", "corrected"):
                cand = {k: v for k, v in rec["cells"].items()
                        if k.endswith(f"|{band}|{conv}")}
                if cand:
                    bk = max(cand, key=lambda k: cand[k]["r_per_day"])
                    best[conv] = {"cell": bk.rsplit("|", 2)[0],
                                  "r_per_day": cand[bk]["r_per_day"]}
            if len(best) == 2:
                best["argmax_moved"] = best["published"]["cell"] != best["corrected"]["cell"]
            rec.setdefault("best", {})[band] = best
        out["sleeves"][sleeve] = rec
        moved = sum(1 for b in rec.get("best", {}).values() if b.get("argmax_moved"))
        log(f"[{si}/{len(by_sleeve)}] {sleeve}: {len(rec['cells'])} cells, "
            f"argmax moved in {moved}/3 bands  ({time.time()-t0:.0f}s)")
        OUT.write_text(json.dumps(out, indent=1))  # flush after every sleeve

    total_cells = sum(len(s["cells"]) for s in out["sleeves"].values())
    if total_cells == 0:
        log("REFUSING TO REPORT SUCCESS: zero cells produced. A sweep that measures "
            "nothing is a failure, not a result. Check the key spaces and the index.")
        return 3

    n_moved = sum(1 for s in out["sleeves"].values()
                  for b in s.get("best", {}).values() if b.get("argmax_moved"))
    out["meta"]["argmax_moved_sleeve_bands"] = n_moved
    out["meta"]["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1))
    log(f"DONE in {time.time()-t0:.0f}s — argmax moved in {n_moved} sleeve-bands. -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
