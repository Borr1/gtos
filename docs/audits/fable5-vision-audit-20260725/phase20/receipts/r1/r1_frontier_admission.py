"""r1-6 — does the correction touch the estate's ONE standing admission?

`mx_btcusd_d1_donchian_20_breakout @ target_5R` is the only cell in this estate that
admits at the ratified rule, it is LIVE on FTMO since 2026-07-31, and it runs on the
frontier contract (`run_book.py --frontier-exits`), which is NOT the contract AA labelled.
`sub_xvol_pullback @ target_4R` is the same shape on an armed sleeve (AK's frontier
winner, which AU then measured REJECTS at all four bands).

So the estate-wide re-walk does not answer the question by itself: it walks AA's contract.
This walks the frontier contracts themselves, both conventions, whole population of each
sleeve, and reports R/trade, R/day, per-fold positivity and the exit-reason census.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
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
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote, SpreadUnavailable, replay_anchor, spread_for)

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "R1_FRONTIER_ADMISSION_V1.json"
TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80

CELLS = {
    "mx_btcusd_d1_donchian_20_breakout": [("as_walked", None), ("target_5R", 5.0),
                                          ("target_2R", 2.0)],
    "sub_xvol_pullback": [("as_walked", None), ("target_4R", 4.0)],
    "crypto": [("as_walked", None), ("target_4R", 4.0)],
    "energy_agri": [("as_walked", None)],
}
BANDS = ("low", "mid", "high")


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


def stats(rs, days):
    n = len(rs)
    if not n:
        return {"n": 0}
    tot = math.fsum(rs)
    nd = len(set(days)) or 1
    return {"n": n, "r_per_trade": round(tot / n, 6),
            "se": round(statistics.pstdev(rs) / math.sqrt(n), 6) if n > 1 else None,
            "r_total": round(tot, 4), "n_days": nd,
            "r_per_day": round(tot / nd, 6)}


def folds(rs, days, k=5):
    """Chronological k folds by day; returns per-fold R/trade and the positivity count."""
    order = sorted(range(len(rs)), key=lambda j: days[j])
    cut = [order[i::1] for i in range(1)][0]
    per = []
    m = len(cut)
    for f in range(k):
        seg = cut[f * m // k:(f + 1) * m // k]
        if seg:
            per.append(round(math.fsum(rs[j] for j in seg) / len(seg), 6))
    return {"per_fold_r_per_trade": per,
            "folds_positive": sum(1 for x in per if x > 0), "n_folds": len(per)}


def main() -> int:
    doc = json.load(gzip.open(TRADES))
    series, index = load_series()
    out = {"what": ("the frontier contracts that carry the estate's standing admission, "
                    "re-walked on both quote conventions"),
           "population": str(TRADES), "bars": BARS, "cells": {}}

    for sleeve, cells in CELLS.items():
        rows = doc["trades"].get(sleeve) or []
        for label, tr in cells:
            acc = {b: {"old": [], "new": [], "days": [], "ro": collections.Counter(),
                       "rn": collections.Counter(), "chg": 0} for b in BANDS}
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
                td = (float(r["target_dist"]) if r["target_dist"] else None) if tr is None \
                    else tr * sd
                pol = ExitPolicy(target_dist=td, maxbars=MAXBARS)
                old = winsorize_R(replay(bars, i, d, stop_dist=sd, policy=pol).r_gross)
                oldres = replay(bars, i, d, stop_dist=sd, policy=pol)
                at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
                for b in BANDS:
                    try:
                        s = spread_for(r["symbol"], at, account="FTMO", band=b)
                    except SpreadUnavailable:
                        continue
                    nw = replay(bars, i, d, stop_dist=sd, policy=pol,
                                entry_price=replay_anchor(bars[i].c, d, s, BarQuote.BID))
                    acc[b]["old"].append(old)
                    acc[b]["new"].append(winsorize_R(nw.r_gross))
                    acc[b]["days"].append(r["decision_day"])
                    acc[b]["ro"][oldres.exit_reason] += 1
                    acc[b]["rn"][nw.exit_reason] += 1
                    acc[b]["chg"] += int(nw.exit_reason != oldres.exit_reason)
            cell = {}
            for b in BANDS:
                a = acc[b]
                if not a["old"]:
                    continue
                delta = [x - y for x, y in zip(a["new"], a["old"])]
                cell[b] = {
                    "old": stats(a["old"], a["days"]),
                    "new": stats(a["new"], a["days"]),
                    "delta": stats(delta, a["days"]),
                    "exit_reason_changed": a["chg"],
                    "exit_reasons_old": dict(sorted(a["ro"].items())),
                    "exit_reasons_new": dict(sorted(a["rn"].items())),
                    "folds_old": folds(a["old"], a["days"]),
                    "folds_new": folds(a["new"], a["days"]),
                }
            out["cells"][f"{sleeve}@{label}"] = cell
            m = cell.get("mid", {})
            if m:
                print(f"{sleeve}@{label:11s} n={m['old']['n']:5d} "
                      f"old {m['old']['r_per_trade']:+.5f} -> new {m['new']['r_per_trade']:+.5f} "
                      f"(d {m['delta']['r_per_trade']:+.5f})  "
                      f"R/day {m['old']['r_per_day']:+.5f} -> {m['new']['r_per_day']:+.5f}  "
                      f"folds+ {m['folds_old']['folds_positive']}->{m['folds_new']['folds_positive']}",
                      flush=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
