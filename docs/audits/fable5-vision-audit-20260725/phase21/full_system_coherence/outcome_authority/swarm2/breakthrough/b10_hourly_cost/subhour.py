"""B10 -- the sub-hour refinement, and the adversarial finding that forced it.

`adversarial_level_vs_shape.py` compared B10's hour-SHAPE ratio against Lane 7's direct
LEVEL ratio on 436 (symbol, hour) cells / 19,403 walked candidates.  The tick-weighted
geometric-mean residual is **1.008** -- the per-symbol anchor is right and the hour shape
is the whole model error, which licenses B10's shape-only restatement.

One cell refused: **UK100 at 15:00 UTC, residual 1.949.**  It is not noise, it is
resolution.  16:30 London is the LSE closing auction; UK100's quoted spread steps up
mid-hour, so the hour's median (0.871) describes the first half and the walked candidates
land in the second.  An hourly grid cannot express a step that happens at :30.

This module builds the 15-minute grid from the M15 aggregates the tape reducer already
emits.

**The first version of this file was wrong and its own validation caught it.**  It shipped
a multiplicative refinement, ``median_mult(h) x mean(h,q)/mean(h)``.  That mixes bases in
exactly the case it was built for: when an hour is bimodal, its MEDIAN sits inside the
cheap mode, and scaling that by a ratio of MEANS lifts it by the right *factor* from the
wrong *base*.  On UK100 h15:30 it produced 1.50 against a tape truth of 2.24 -- 33 % light,
in the one cell the refinement exists to price.

The correct construction is a direct level, on a median basis on both sides:

    mult(sym, h, q) = median over M15 bars of (bar mean spread)  /  reference median spread

A 15-minute slice of a deterministic session event is close to unimodal, so the median of
its bar means is a sound central estimate; the denominator is the same reference p50 the
hour term uses, so hour and quarter cells are directly comparable.  ``validate()`` checks
the construction where both resolutions exist: median-of-bar-means at hour resolution
against the tick-histogram median.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

BROKER_TO_UTC_S = 3 * 3600
M15 = 900


def build(tape_dir: str, out_json: str, tape_model_json: str | None = None) -> dict:
    # the reference p50 per (broker, symbol) -- the same denominator the hour term uses
    ref_all: dict[str, dict[str, float]] = {}
    if tape_model_json:
        tm = json.load(open(tape_model_json))
        for acct, syms in tm["accounts"].items():
            ref_all[acct] = {s: b["reference"]["median_px"] for s, b in syms.items()
                             if b["reference"].get("median_px")}
    out: dict[str, dict] = {}
    for p in sorted(glob.glob(os.path.join(tape_dir, "*.npz"))):
        z = np.load(p, allow_pickle=True)
        broker = str(z["broker"])
        sym = str(z["symbol"])
        ref_median = ref_all.get(broker, {})
        bk = z["m15_bucket"]
        st = z["m15_stats"]
        if len(bk) == 0:
            continue
        # bucket -> utc seconds -> (weekday, hour, quarter)
        secs = bk * M15
        hour = (secs % 86400) // 3600
        quarter = (secs % 3600) // M15
        weekday = ((secs // 86400) + 4) % 7
        n = st[:, 0]
        sp_sum = st[:, 2]
        sp_min = st[:, 1]
        dwell = st[:, 3]
        sp_dwell = st[:, 4]

        ref_med = float(ref_median[sym]) if sym in ref_median else None
        with np.errstate(divide="ignore", invalid="ignore"):
            bar_mean_all = np.where(n > 0, sp_sum / np.maximum(n, 1), np.nan)

        cells: dict[str, dict] = {}
        # (hour, quarter) pooled over weekdays, plus the hour marginal
        for h in range(24):
            mh = (hour == h) & (n > 0)
            if not mh.any():
                continue
            mean_h = float(sp_sum[mh].sum() / n[mh].sum())
            med_h = float(np.median(bar_mean_all[mh]))
            for q in range(4):
                m = mh & (quarter == q)
                if not m.any() or n[m].sum() < 100:
                    continue
                mean_q = float(sp_sum[m].sum() / n[m].sum())
                med_q = float(np.median(bar_mean_all[m]))
                d = dwell[m].sum()
                cells[f"{h}|{q}"] = {
                    "n_ticks": int(n[m].sum()),
                    "n_bars": int(m.sum()),
                    "mean_px": mean_q,
                    "median_bar_mean_px": med_q,
                    "mean_px_tw": float(sp_dwell[m].sum() / d) if d > 0 else None,
                    # the term a consumer should use: a direct level on a median basis
                    "median_mult": (med_q / ref_med) if ref_med else None,
                    # kept only so the superseded construction stays auditable
                    "superseded_subhour_factor": mean_q / mean_h if mean_h > 0 else None,
                    "hour_mean_px": mean_h,
                    "hour_median_bar_mean_px": med_h,
                }
        # the within-bar minimum defect, measured on the same bars
        tot_n = n.sum()
        ok = n > 0
        bar_mean = sp_sum[ok] / n[ok]
        bar_min = sp_min[ok]
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(bar_min > 0, bar_mean / bar_min, np.nan)
        rr = ratio[np.isfinite(ratio)]
        out.setdefault(broker, {})[sym] = {
            "by_hour_quarter_utc": cells,
            "within_bar_min_defect_m15": {
                "n_bars": int(ok.sum()),
                "mean_over_min_mean": float(np.mean(rr)) if len(rr) else None,
                "mean_over_min_median": float(np.median(rr)) if len(rr) else None,
                "mean_over_min_p90": float(np.percentile(rr, 90)) if len(rr) else None,
                "mean_over_min_p99": float(np.percentile(rr, 99)) if len(rr) else None,
                "vw_bar_mean_px": float(sp_sum.sum() / tot_n) if tot_n else None,
                "vw_bar_min_px": float((sp_min[ok] * n[ok]).sum() / tot_n) if tot_n else None,
                "bias_pct_if_min_used": (
                    float(100 * (sp_sum.sum() / tot_n) / ((sp_min[ok] * n[ok]).sum() / tot_n) - 100)
                    if tot_n and (sp_min[ok] * n[ok]).sum() > 0 else None),
            },
        }
    doc = {
        "schema": "b10_subhour_and_bar_min_v1",
        "grid": "15 minutes of the hour, pooled over weekdays; >=100 ticks per cell",
        "refinement": "median_mult(sym,h,q) = median over M15 bars of the bar mean spread, "
                      "divided by the symbol's reference p50 -- a direct level on a median "
                      "basis, NOT a factor on the hour term (see the module docstring for "
                      "the superseded construction and the cell that refuted it)",
        "motivation": "adversarial_level_vs_shape.py -- UK100 h15 residual 1.949, the LSE "
                      "16:30 close inside the hour. Every other cell of 436 is within "
                      "0.88-1.08 and the tick-weighted geomean residual is 1.008.",
        "accounts": out,
    }
    json.dump(doc, open(out_json, "w"), indent=1)
    return doc


def validate(tape_dir: str, doc: dict, tape_model_json: str) -> dict:
    """Construction check: median-of-bar-means at HOUR resolution vs the tick-histogram
    median, on every (symbol, hour) cell where both exist."""
    tm = json.load(open(tape_model_json))
    errs = []
    for acct, syms in doc["accounts"].items():
        for sym, blk in syms.items():
            ref = ((tm["accounts"].get(acct) or {}).get(sym) or {}).get("by_hour_utc") or {}
            seen = {}
            for key, c in blk["by_hour_quarter_utc"].items():
                h = key.split("|")[0]
                seen.setdefault(h, c["hour_median_bar_mean_px"])
            for h, med_bar in seen.items():
                cell = ref.get(h)
                if cell and cell["q_tick"]["p50"]:
                    errs.append(med_bar / cell["q_tick"]["p50"])
    a = np.array(errs)
    return {"n_cells": int(len(a)), "median_ratio": float(np.median(a)),
            "p05": float(np.percentile(a, 5)), "p95": float(np.percentile(a, 95)),
            "frac_within_10pct": float(np.mean(np.abs(a - 1) < 0.10))}


if __name__ == "__main__":
    d = build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    if len(sys.argv) > 3:
        v = validate(sys.argv[1], d, sys.argv[3])
        d["construction_validation"] = v
        json.dump(d, open(sys.argv[2], "w"), indent=1)
        print("construction validation (median-of-bar-means vs tick p50, hour cells):", v)
    uk = d["accounts"]["FTMO"]["UK100_cash"]
    print("UK100 h15 quarters:")
    for q in range(4):
        c = uk["by_hour_quarter_utc"].get(f"15|{q}")
        if c:
            print(f"  :{q*15:02d}  n={c['n_ticks']:7d}  mean={c['mean_px']:.3f}  "
                  f"med_bar={c['median_bar_mean_px']:.3f}  mult={c['median_mult']:.3f}  "
                  f"(superseded factor {c['superseded_subhour_factor']:.3f})")
    print("\nwithin-bar-min defect, worst 12 by bias:")
    rows = [(s, v["within_bar_min_defect_m15"]) for s, v in d["accounts"]["FTMO"].items()]
    rows.sort(key=lambda kv: -(kv[1]["bias_pct_if_min_used"] or 0))
    for s, v in rows[:12]:
        print(f"  {s:14s} mean/min mean {v['mean_over_min_mean']:.3f}  "
              f"median {v['mean_over_min_median']:.3f}  p90 {v['mean_over_min_p90']:.3f}  "
              f"vw bias {v['bias_pct_if_min_used']:.1f}%")
