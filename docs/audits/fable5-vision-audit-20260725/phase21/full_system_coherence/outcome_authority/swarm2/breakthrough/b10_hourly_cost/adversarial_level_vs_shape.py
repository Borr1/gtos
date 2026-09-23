"""B10 adversarial check -- is the hour SHAPE the whole error, or is the ANCHOR wrong too?

B10's restatement prices a hour-shape ratio (tape multiplier / model multiplier, each
relative to its own reference level).  Lane 7 priced a LEVEL ratio (true quoted spread /
modelled quoted spread) directly.  If the model's per-symbol anchor is also wrong, the
shape-only ratio understates the correction and B10's number is too small.

The test uses Lane 7's own surviving `walk.pkl`, unmodified: 21,684 MARKET candidates in
the tick window, each carrying the labeller's `model_spread_px` and the true ask-bid at
the first strictly-post-decision minute.  `walk.pkl`'s `hour` is the exact decision UTC
hour (`walk.py`: ``int(pd.Timestamp(r.decision_utc).hour)``), so no keying defect is
inherited.

  level_ratio(sym, h)  = median(true_spread_px / model_spread_px)     <- Lane 7
  shape_ratio(sym, h)  = tape_mult(sym, h) / model_class_mult(sym, h) <- B10
  anchor_error(sym)    = median over hours of level_ratio / shape_ratio

If anchor_error ~ 1 the shape is the whole story.  If it departs from 1, the difference is
a level error B10's restatement does not carry, and it must be reported as such.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tape_hourly import TapeHourly  # noqa: E402

SHIPPED = "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
CLASS_OF_CANON = {
    "AUDJPY": "jpy_fx", "CHFJPY": "jpy_fx", "EURJPY": "jpy_fx", "GBPJPY": "jpy_fx",
    "NZDJPY": "jpy_fx", "USDJPY": "jpy_fx", "CADJPY": "jpy_fx",
    "AUDUSD": "fx", "EURGBP": "fx", "EURUSD": "fx", "GBPUSD": "fx", "NZDUSD": "fx",
    "USDCAD": "fx", "USDCHF": "fx", "BTCUSD": "crypto", "ETHUSD": "crypto",
    "GER40": "index", "JP225": "index", "NAS100": "index", "SPX500": "index",
    "UK100": "index", "US30_cash": "index", "UKOIL_cash": "energy",
    "USOIL_cash": "energy", "XAGUSD": "metals", "XAUUSD": "metals",
}
BROKER_MINUS_UTC = 3
# a representative mid-window instant per weekday is enough: the class table is
# hour-of-week and the walk covers all five weekdays roughly evenly
REF_DAY = dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc)   # a Wednesday


def class_mult(ship, klass, hour_utc):
    vals = []
    for wd in range(5):
        at = REF_DAY + dt.timedelta(days=wd - REF_DAY.weekday(), hours=hour_utc - REF_DAY.hour)
        wall = at + dt.timedelta(hours=BROKER_MINUS_UTC)
        how = str(wall.weekday() * 24 + wall.hour)
        v = ((ship["intraweek"]["FTMO"].get("by_class_hour_of_week") or {})
             .get(klass) or {}).get(how)
        if v is not None:
            vals.append(float(v))
    return float(np.median(vals)) if vals else None


def tape_mult_hour(tape, sym, hour_utc):
    c = tape.hour_cell(sym, "FTMO", hour_utc)
    return c["median_mult"] if c else None


def main(walk_pkl, tape_json, out_json):
    w = pd.read_pickle(walk_pkl)
    ship = json.load(open(SHIPPED))
    tape = TapeHourly(path=tape_json)
    w = w[(w.model_spread_px > 0) & (w.true_spread_px > 0)].copy()
    w["lvl"] = w.true_spread_px / w.model_spread_px

    rows = []
    for (sym, h), g in w.groupby(["symbol", "hour"]):
        if len(g) < 20:
            continue
        klass = CLASS_OF_CANON.get(sym)
        cm = class_mult(ship, klass, int(h))
        tm = tape_mult_hour(tape, sym, int(h))
        if not cm or not tm:
            continue
        rows.append({"symbol": sym, "hour": int(h), "n": int(len(g)),
                     "level_ratio": float(g.lvl.median()),
                     "shape_ratio": float(tm / cm),
                     "anchor_residual": float(g.lvl.median() / (tm / cm))})
    df = pd.DataFrame(rows)
    per_sym = (df.groupby("symbol")
               .apply(lambda g: pd.Series({
                   "n_cells": len(g), "n_rows": int(g.n.sum()),
                   "level_ratio_med": float(np.median(g.level_ratio)),
                   "shape_ratio_med": float(np.median(g.shape_ratio)),
                   "anchor_residual_med": float(np.median(g.anchor_residual)),
                   "corr_level_shape": float(np.corrcoef(g.level_ratio, g.shape_ratio)[0, 1])
                   if len(g) > 2 else float("nan"),
               }), include_groups=False)
               .sort_values("n_rows", ascending=False))

    # weighted overall residual
    wgt = df.n.values
    overall = float(np.exp(np.average(np.log(df.anchor_residual.values), weights=wgt)))
    doc = {
        "schema": "b10_level_vs_shape_v1",
        "source": "Lane 7 walk.pkl, unmodified; 21,684 MARKET candidates in the tick window",
        "n_cells": int(len(df)), "n_rows": int(df.n.sum()),
        "overall_anchor_residual_geomean": overall,
        "interpretation": (
            "anchor_residual = level_ratio / shape_ratio. 1.0 means the per-symbol ANCHOR "
            "is right and the hour SHAPE is the whole error, which is what B10's "
            "restatement assumes. A value away from 1 is a level error B10 does not carry."),
        "per_symbol": json.loads(per_sym.reset_index().to_json(orient="records")),
        "cells": json.loads(df.to_json(orient="records")),
    }
    json.dump(doc, open(out_json, "w"), indent=1)
    print(per_sym.to_string())
    print("\noverall anchor residual (tick-weighted geomean):", round(overall, 4))
    print("cells:", len(df), "rows:", int(df.n.sum()))
    uk = df[df.symbol == "UK100"]
    if len(uk):
        print("\nUK100 cells:")
        print(uk.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
