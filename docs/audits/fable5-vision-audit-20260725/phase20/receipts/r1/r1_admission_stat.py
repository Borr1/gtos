"""r1-6b — how far does the correction move the admission STATISTIC?

Not the ratified gate. Re-running `run_gate` at the ratified rule needs AN's sealed
population spec, AU's fold construction and `CANDIDATE_BOOK_V1`'s family, and that
belongs to whoever owns the admission, not to the lane that owns the walker.

What this does instead is the honest bounded version: the gate's binding statistic is a
**day-block** statement about daily R (`walkforward/__init__` construction note 3 — a
per-trade bootstrap overstated a stated error budget by 2.1x-7.7x, B279), so this computes
a day-block bootstrap p(mean <= 0) on the SAME daily series, old convention and corrected,
for the cells that carry live money. If the two p-values sit on the same side of the
sealed alpha = 0.10 with room, the correction cannot be what moves a verdict.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
import random
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote, SpreadUnavailable, replay_anchor, spread_for)

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "R1_ADMISSION_STAT_V1.json"
TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS, BAND, DRAWS = 80, "mid", 20000

CELLS = [("mx_btcusd_d1_donchian_20_breakout", "target_5R", 5.0),
         ("sub_xvol_pullback", "target_4R", 4.0),
         ("sub_xvol_pullback", "as_walked", None),
         ("crypto", "as_walked", None),
         ("energy_agri", "as_walked", None)]


def load_series():
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files, inv = {}, {v: k for k, v in TF_NAME.items()}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        if inv.get(tfs) is None:
            continue
        files[(res(sym), inv[tfs])] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series, index = {}, {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                        for r in rows],
                       [dt.datetime.fromisoformat(r["time"]) for r in rows])
        index[key] = {ts: i for i, ts in enumerate(series[key][1])}
    return series, index


def block_boot(daily: dict, rng, draws=DRAWS):
    """p(mean daily R <= 0) by resampling whole DAYS with replacement."""
    days = sorted(daily)
    v = [daily[d] for d in days]
    n = len(v)
    if n < 2:
        return None
    obs = statistics.fmean(v)
    le = 0
    for _ in range(draws):
        m = statistics.fmean(v[rng.randrange(n)] for _ in range(n))
        if m <= 0:
            le += 1
    return {"n_days": n, "mean_daily_r": round(obs, 6),
            "p_mean_le_zero": round(le / draws, 5),
            "ci95": [round(x, 5) for x in _ci(v, rng, draws)]}


def _ci(v, rng, draws):
    n = len(v)
    ms = sorted(statistics.fmean(v[rng.randrange(n)] for _ in range(n)) for _ in range(draws))
    return ms[int(0.025 * draws)], ms[int(0.975 * draws)]


def main() -> int:
    doc = json.load(gzip.open(TRADES))
    series, index = load_series()
    out = {"what": ("day-block bootstrap on the admission statistic, old convention vs "
                    "quote-side corrected — a proxy on the same statistic CLASS, not the "
                    "ratified gate"),
           "draws": DRAWS, "band": BAND, "cells": {}}
    rng = random.Random(20260807)

    for sleeve, label, tr in CELLS:
        rows = doc["trades"].get(sleeve) or []
        gd_old, gd_new, nd_old, nd_new = (collections.defaultdict(float) for _ in range(4))
        n = 0
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            i = index.get(key, {}).get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                continue
            bars, times = series[key]
            if i + 2 >= len(bars):
                continue
            d, sd = int(r["direction"]), float(r["sl_distance_price"])
            td = (float(r["target_dist"]) if r["target_dist"] else None) if tr is None else tr * sd
            pol = ExitPolicy(target_dist=td, maxbars=MAXBARS)
            at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            try:
                s = spread_for(r["symbol"], at, account="FTMO", band=BAND)
            except SpreadUnavailable:
                continue
            o = replay(bars, i, d, stop_dist=sd, policy=pol)
            w = replay(bars, i, d, stop_dist=sd, policy=pol,
                       entry_price=replay_anchor(bars[i].c, d, s, BarQuote.BID))
            ro, rn = winsorize_R(o.r_gross), winsorize_R(w.r_gross)
            side = "LONG" if d > 0 else "SHORT"
            try:
                co = cost_r(r["symbol"], "FTMO", o.bars_held * TF_MINUTES[tf] / 60.0,
                            sl_distance_price=sd, entry_price=bars[i].c, side=side,
                            entry_utc=at, spread_band=BAND)
                cn = cost_r(r["symbol"], "FTMO", w.bars_held * TF_MINUTES[tf] / 60.0,
                            sl_distance_price=sd, entry_price=bars[i].c, side=side,
                            entry_utc=at, spread_band=BAND)
            except Exception:
                continue
            day = r["decision_day"]
            gd_old[day] += ro
            gd_new[day] += rn
            nd_old[day] += ro - float(co.total_r.value)
            nd_new[day] += rn - (float(cn.total_r.value) - float(cn.spread_r.value))
            n += 1
        cell = {"n_trades": n,
                "gross_old": block_boot(gd_old, rng), "gross_new": block_boot(gd_new, rng),
                "net_old": block_boot(nd_old, rng), "net_new": block_boot(nd_new, rng)}
        out["cells"][f"{sleeve}@{label}"] = cell
        g0, g1, n0, n1 = cell["gross_old"], cell["gross_new"], cell["net_old"], cell["net_new"]
        print(f"{sleeve}@{label:11s} n={n:5d} days={g0['n_days']:4d} | "
              f"GROSS R/day {g0['mean_daily_r']:+.4f} p={g0['p_mean_le_zero']:.4f} -> "
              f"{g1['mean_daily_r']:+.4f} p={g1['p_mean_le_zero']:.4f} | "
              f"NET R/day {n0['mean_daily_r']:+.4f} p={n0['p_mean_le_zero']:.4f} -> "
              f"{n1['mean_daily_r']:+.4f} p={n1['p_mean_le_zero']:.4f}", flush=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
