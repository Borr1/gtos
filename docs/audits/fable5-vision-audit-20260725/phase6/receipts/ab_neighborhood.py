"""Session AB, deliverable 3: parameter neighborhoods — plateau or spike.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_neighborhood.py

THREE NEIGHBORHOODS, ONE DECISION RULE
---------------------------------------
`FOURTH_REVIEW.md` section 5.1: *"sweep the neighborhood over the archive and publish the
surface, not the best cell. Plateaus are real, spikes are artifacts; a repair that only
works at one cell is not a repair."*

  1. **`sub_xvol_pullback`** — the session brief's item 3. The strongest earner in the
     estate (+1.19 R net per trade measured here) and the one whose whole doubt is
     selection artefact: it is a cell chosen from a substrate scan, and the scan's own
     window is the window that selected it. If the edge sits on a plateau of adjacent
     cells the doubt dissolves; if it sits on a spike, the book's expectation is honestly
     resized. Both outcomes are wins for a live book.

  2. **`metals_core`** — commissioned by this session's own restatement rather than by the
     brief. Measured here: gross **+0.174 R/trade** over 385 trades and 21 years, cost
     **0.259 R**, net **-0.085**. `FOURTH_REVIEW.md` section 2.2 maps that shape —
     expectancy fails with gross > 0 — straight onto a **cost-geometry repair**, and the
     cost is spread-dominated (0.126 R of 0.259), which names the lever: the stop. Cost in
     R is a price drag divided by the stop, so widening the stop divides it; whether the
     path pays for the wider stop is what the sweep measures.

  3. **`crypto`** — the persistence cut and the 2xATR stop, for completeness on the book's
     largest single edge.

PLATEAU MEASUREMENT, NOT PLATEAU ASSERTION
-------------------------------------------
For each neighborhood the artifact publishes:

  * `frac_positive`  — the share of cells with positive net expectancy. A plateau is
    mostly-positive; a spike is one cell in a field of zeros.
  * `selected_rank`  — where production's own cell sits in the sorted neighborhood. A cell
    at rank 1 of N is the signature of a cell that was CHOSEN by looking; a cell in the
    middle of a positive field is a cell that could have been chosen any number of ways
    and still worked.
  * `median_over_selected` — the neighborhood median divided by the selected cell. Near 1
    means the selection bought nothing, which is the strongest possible evidence that the
    edge is not a selection artefact.

Every cell is a trial and every cell is logged, including the ones that fail. The whole
point of `WAVE_6_WORKING_AGREEMENT.md` section 3 is that "we tried 400 things and the
ledger says the survivor still clears" is a different claim from "we tried 400 things and
reported the best one".
"""

from __future__ import annotations

import json
import os
import pickle
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.regime_spine import conditions as C  # noqa: E402
from src.research_infra.regime_spine.archive import ARCHIVE, frames_for  # noqa: E402
from src.research_infra.regime_spine.sweep import Variant, evaluate, grid  # noqa: E402
from src.research_infra.regime_spine.trials import TrialLedger  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "AB_NEIGHBORHOOD_V1.json"
LEDGER = HERE / "AB_TRIAL_LEDGER.jsonl"
FRAME_CACHE = os.environ.get("AB_FRAME_CACHE", "")
FIT_LAST_YEAR = 2023          # fit <= 2023, validate 2024+


def build_frames(sleeves) -> dict:
    want = sorted({s for n in sleeves for s in C.SLEEVES[n].surface})
    cache: dict = {}
    if FRAME_CACHE and Path(FRAME_CACHE).is_file():
        cache = pickle.load(open(FRAME_CACHE, "rb"))
    fr = frames_for(want, 16388, cache=cache)
    if FRAME_CACHE:
        with open(FRAME_CACHE, "wb") as fh:
            pickle.dump(cache, fh)
    return fr


def summarise(cells: list[dict], selected_id: str, key: str = "mean_r_net") -> dict:
    """Plateau statistics over one neighborhood, on one metric."""
    vals = [(c["variant_id"], c["result"]["all"][key], c["result"]["all"]["n"])
            for c in cells if c["result"]["all"][key] is not None]
    if not vals:
        return {"n_cells": len(cells), "n_scored": 0}
    ordered = sorted(vals, key=lambda t: -t[1])
    sel = next((v for v in vals if v[0] == selected_id), None)
    med = statistics.median([v[1] for v in vals])
    return {
        "metric": key,
        "n_cells": len(cells),
        "n_scored": len(vals),
        "frac_positive": round(sum(1 for _, v, _ in vals if v > 0) / len(vals), 4),
        "median": round(med, 5),
        "best": {"variant_id": ordered[0][0], "value": round(ordered[0][1], 5),
                 "n": ordered[0][2]},
        "worst": {"variant_id": ordered[-1][0], "value": round(ordered[-1][1], 5),
                  "n": ordered[-1][2]},
        "selected": ({"variant_id": sel[0], "value": round(sel[1], 5), "n": sel[2]}
                     if sel else None),
        "selected_rank": (1 + [v[0] for v in ordered].index(selected_id)
                          if sel else None),
        "median_over_selected": (round(med / sel[1], 4)
                                 if sel and sel[1] not in (0, None) else None),
        "verdict": _verdict(vals, sel, med),
    }


def _verdict(vals, sel, med) -> str:
    if sel is None:
        return "selected cell not scored"
    frac = sum(1 for _, v, _ in vals if v > 0) / len(vals)
    rank = 1 + sorted([v[1] for v in vals], reverse=True).index(sel[1])
    if frac >= 0.80 and rank > max(2, 0.1 * len(vals)):
        return ("PLATEAU — the neighborhood is broadly positive and the production cell is "
                "not its peak, so the edge does not depend on the cell that was chosen.")
    if frac >= 0.60:
        return ("BROAD — most of the neighborhood is positive; the production cell is near "
                "the top, so some of its level is selection but its sign is not.")
    if rank <= max(1, 0.05 * len(vals)):
        return ("SPIKE — the production cell is at or near the neighborhood maximum in a "
                "field that is mostly not positive. Treat the level as selected and size "
                "on the neighborhood median, not on the cell.")
    return ("MIXED — neither a clean plateau nor a spike; publish the surface and let the "
            "sizing conversation use the median.")


def run_axis(led, frames, cond, family, cells, *, base_over=None, note="") -> list[dict]:
    truth = load_broker_true_costs()
    out = []
    t0 = time.time()
    for k, v in enumerate(cells):
        params = {kk: vv for kk, vv in v.items()
                  if kk not in ("stop_scale", "atr_floor", "target_r_scale")}
        over = dict(base_over or {})
        for kk in ("stop_scale", "atr_floor", "target_r_scale"):
            if kk in v:
                over[kk] = v[kk]
        res = evaluate(frames, cond, params=params or None, costs=truth,
                       fit_last_year=FIT_LAST_YEAR, **over)
        vid = Variant(v).vid()
        out.append({"variant_id": vid, "params": dict(v), "result": res})
        led.log(family, cond.sleeve, vid, dict(v),
                {"n": res["all"]["n"],
                 "mean_r_net": res["all"]["mean_r_net"],
                 "fit_mean_r_net": res["fit"]["mean_r_net"],
                 "validate_mean_r_net": res["validate"]["mean_r_net"]},
                note=note)
        if (k + 1) % 25 == 0:
            print(f"    {k+1}/{len(cells)}  {time.time()-t0:.0f}s", flush=True)
    print(f"  {family}: {len(cells)} cells in {time.time()-t0:.0f}s", flush=True)
    return out


def show(title: str, cells: list[dict], sel: str, n_show: int = 12) -> None:
    print(f"\n  --- {title}")
    rows = sorted(cells, key=lambda c: -(c["result"]["all"]["mean_r_net"] or -9e9))
    print(f"    {'variant':52s} {'n':>4s} {'gross':>8s} {'cost':>7s} {'net':>8s} "
          f"{'fit n':>6s} {'fit net':>8s} {'val n':>6s} {'val net':>8s}")
    show_rows = rows[:n_show // 2] + rows[-(n_show // 2):] if len(rows) > n_show else rows
    seen = set()
    for c in show_rows + [c for c in cells if c["variant_id"] == sel]:
        if c["variant_id"] in seen:
            continue
        seen.add(c["variant_id"])
        a, f, v = c["result"]["all"], c["result"]["fit"], c["result"]["validate"]
        mark = " <= PRODUCTION" if c["variant_id"] == sel else ""
        g = lambda x, p=5: ("     -" if x is None else f"{x:8.{p}f}")  # noqa: E731
        print(f"    {c['variant_id'][:52]:52s} {a['n']:4d} {g(a['mean_r_gross'])} "
              f"{g(a['mean_cost_r'])} {g(a['mean_r_net'])} {f['n']:6d} "
              f"{g(f['mean_r_net'])} {v['n']:6d} {g(v['mean_r_net'])}{mark}")


def main() -> dict:
    t0 = time.time()
    sleeves = ("sub_xvol_pullback", "metals_core", "crypto")
    frames = build_frames(sleeves)
    led = TrialLedger(LEDGER, session="AB", append=True)
    out: dict = {
        "schema": "gtos.wave6.regime_spine.neighborhood.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "bars_archive": ARCHIVE,
        "fit_last_year": FIT_LAST_YEAR,
        "protocol": ("Fit era <= 2023, validation era 2024+. The production cells were "
                     "selected on 2025+ (build_survivor_book.py:60 / "
                     "KB7_growth_kelly_sizing.py:130 share `d.year >= 2025`), so a "
                     "validation era that ENDS before 2025 would be free of that "
                     "contamination but also free of the regime the book is armed in. "
                     "2024+ is the compromise: it contains the selection window and is "
                     "scored separately from the fit, so contamination is visible rather "
                     "than hidden."),
        "neighborhoods": {},
    }

    # ---------------------------------------------------------------- sub_xvol_pullback
    cond = C.SLEEVES["sub_xvol_pullback"]
    d = cond.defaults
    print("\n=== sub_xvol_pullback", flush=True)
    thr_cells = [Variant(c) for c in grid(
        vr_xhi=[1.4, 1.5, 1.6, 1.7, 1.8],
        slope_up=[1.0, 1.25, 1.5, 1.75, 2.0],
        ac_band=[0.05, 0.075, 0.10, 0.125, 0.15],
    )]
    thr = run_axis(led, frames, cond, "xvol_thresholds", thr_cells,
                   note="substrate cell threshold neighborhood")
    sel_thr = Variant({"vr_xhi": d["vr_xhi"], "slope_up": d["slope_up"],
                       "ac_band": d["ac_band"]}).vid()

    mtf_cells = [Variant(c) for c in grid(mtf_sgn_thr=[0.3, 0.4, 0.5, 0.6, 0.7])]
    mtf = run_axis(led, frames, cond, "xvol_mtf", mtf_cells,
                   note="multi-timeframe sign threshold")
    sel_mtf = Variant({"mtf_sgn_thr": d["mtf_sgn_thr"]}).vid()

    geo_cells = [Variant(c) for c in grid(
        stop_scale=[0.75, 1.0, 1.25, 1.5, 2.0],
        target_r_scale=[0.667, 0.833, 1.0, 1.167, 1.333],
    )]
    geo = run_axis(led, frames, cond, "xvol_geometry", geo_cells,
                   note="stop width x target multiple, path re-simulated")
    sel_geo = Variant({"stop_scale": 1.0, "target_r_scale": 1.0}).vid()

    out["neighborhoods"]["sub_xvol_pullback"] = {
        "production_params": dict(d),
        "thresholds": {"selected": sel_thr, "cells": thr,
                       "plateau_net": summarise(thr, sel_thr, "mean_r_net"),
                       "plateau_day": summarise(thr, sel_thr, "mean_r_net_per_day")},
        "mtf": {"selected": sel_mtf, "cells": mtf,
                "plateau_net": summarise(mtf, sel_mtf, "mean_r_net")},
        "geometry": {"selected": sel_geo, "cells": geo,
                     "plateau_net": summarise(geo, sel_geo, "mean_r_net")},
    }
    show("thresholds (vr_xhi x slope_up x ac_band)", thr, sel_thr)
    show("mtf sign threshold", mtf, sel_mtf)
    show("geometry (stop scale x target scale)", geo, sel_geo)

    # ---------------------------------------------------------------------- metals_core
    cond = C.SLEEVES["metals_core"]
    d = cond.defaults
    print("\n=== metals_core (cost-geometry repair)", flush=True)
    stop_cells = [Variant(c) for c in grid(
        stop_scale=[1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0],
        atr_floor=[0.25, 0.5, 0.75, 1.0],
    )]
    stops = run_axis(led, frames, cond, "metals_stop_geometry", stop_cells,
                     note="cost in R = drag / stop; widen the stop, re-simulate the path")
    sel_stop = Variant({"stop_scale": 1.0, "atr_floor": 0.25}).vid()

    ac_cells = [Variant(c) for c in grid(
        ac_thr=[0.05, 0.075, 0.10, 0.125, 0.15, 0.20],
        gate_k=[1.0, 1.1, 1.2, 1.3, 1.4],
    )]
    acs = run_axis(led, frames, cond, "metals_thresholds", ac_cells,
                   note="persistence cut x vol-expansion cut")
    sel_ac = Variant({"ac_thr": d["ac_thr"], "gate_k": d["gate_k"]}).vid()

    out["neighborhoods"]["metals_core"] = {
        "production_params": dict(d),
        "stop_geometry": {"selected": sel_stop, "cells": stops,
                          "plateau_net": summarise(stops, sel_stop, "mean_r_net"),
                          "plateau_day": summarise(stops, sel_stop,
                                                   "mean_r_net_per_day")},
        "thresholds": {"selected": sel_ac, "cells": acs,
                       "plateau_net": summarise(acs, sel_ac, "mean_r_net")},
    }
    show("stop geometry (scale x ATR floor)", stops, sel_stop, n_show=14)
    show("thresholds (ac_thr x gate_k)", acs, sel_ac)

    # --------------------------------------------------------------------------- crypto
    cond = C.SLEEVES["crypto"]
    d = cond.defaults
    print("\n=== crypto", flush=True)
    cry_cells = [Variant(c) for c in grid(
        ac_thr=[0.05, 0.10, 0.15, 0.20, 0.25],
        stop_scale=[0.75, 1.0, 1.25, 1.5],
    )]
    cry = run_axis(led, frames, cond, "crypto_neighborhood", cry_cells,
                   note="persistence cut x stop width")
    sel_cry = Variant({"ac_thr": d["ac_thr"], "stop_scale": 1.0}).vid()
    out["neighborhoods"]["crypto"] = {
        "production_params": dict(d),
        "cells": cry, "selected": sel_cry,
        "plateau_net": summarise(cry, sel_cry, "mean_r_net"),
    }
    show("ac_thr x stop scale", cry, sel_cry)

    # ------------------------------------------------------------------------- verdicts
    print("\n=== plateau verdicts")
    for sleeve, node in out["neighborhoods"].items():
        for axis, sub in node.items():
            if not isinstance(sub, dict) or "plateau_net" not in sub:
                continue
            p = sub["plateau_net"]
            if not p.get("n_scored"):
                continue
            print(f"  {sleeve:20s} {axis:16s} cells={p['n_cells']:4d} "
                  f"pos={p['frac_positive']:.0%} median={p['median']:+.4f} "
                  f"selected={p['selected']['value'] if p['selected'] else None} "
                  f"rank={p['selected_rank']}/{p['n_scored']}")
            print(f"      {p['verdict']}")

    out["n_trials_logged"] = led.n_trials
    led.write_summary(HERE / "AB_TRIAL_BUDGET_RESULT.json")
    led.close()
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB); "
          f"{led.n_trials} trials logged; {time.time()-t0:.0f}s")
    return out


if __name__ == "__main__":
    main()
