#!/usr/bin/env python3
"""B1 — the two adversarial tests the positive result has to survive.

TEST 1 (mix vs order type).  The pooled LIMIT stop conditional is 1.157x MARKET's, but the two arms
trade different instruments. Reweight MARKET's per-symbol conditional onto the LIMIT arm's own symbol
mix: if the gap closes, the 1.157x is composition; if it survives, it is the order type.

TEST 2 (LIMIT fill feasibility, intrabar).  b1_slip.py compares the booked LIMIT level against the
true quote at the BOOKED FILL INSTANT. For a MARKET order that instant IS the fill (successor bar
open) and the comparison is exact. For a resting LIMIT the engine books "the approved limit price on
an intrabar correct-side touch" (quote_side.py:1340, :1471) -- the touch is INTRABAR, so comparing
against the bar-open quote systematically overstates LIMIT entry optimism. This test asks the tape
the right question: within the fill minute, did the true entry-side quote ever reach the level?

Writes B1_ADVERSARIAL.json.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

TICK = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP = {"NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
       "JP225": "JP225_cash", "UK100": "UK100_cash"}
OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
R = {"schema": "b1_adversarial_v1"}


def to_utc(sec):
    bn = pd.to_datetime(sec, unit="s")
    return (bn - pd.Timedelta(hours=7)).dt.tz_localize(
        "America/New_York", ambiguous=False, nonexistent="shift_forward").dt.tz_convert("UTC")


# ================= TEST 1 : mix vs order type =================
M = pd.read_pickle(f"{OUT}/legs_ctrlB_lg_market.pkl")
L = pd.read_pickle(f"{OUT}/legs_limit.pkl")
ms = M[(M.state == "STOP") & (M.found_cross == 1)]
ls = L[(L.state == "STOP") & (L.found_cross == 1)]
mu_m = ms.groupby("symbol").exit_opt_at_cross_r.mean()
mu_l = ls.groupby("symbol").exit_opt_at_cross_r.mean()
w_m = ms.groupby("symbol").size().astype(float)
w_l = ls.groupby("symbol").size().astype(float)
common = mu_m.index.intersection(mu_l.index)

def wavg(mu, w, idx):
    return float((mu.reindex(idx) * w.reindex(idx)).sum() / w.reindex(idx).sum())

R["test1_mix_vs_order_type"] = {
    "LIMIT_own_mix": wavg(mu_l, w_l, common),
    "MARKET_own_mix": wavg(mu_m, w_m, common),
    "MARKET_reweighted_to_LIMIT_mix": wavg(mu_m, w_l, common),
    "LIMIT_reweighted_to_MARKET_mix": wavg(mu_l, w_m, common),
    "n_symbols": int(len(common)),
}
t1 = R["test1_mix_vs_order_type"]
gap_raw = t1["LIMIT_own_mix"] - t1["MARKET_own_mix"]
gap_mix_matched = t1["LIMIT_own_mix"] - t1["MARKET_reweighted_to_LIMIT_mix"]
t1["gap_raw"] = gap_raw
t1["gap_at_matched_mix"] = gap_mix_matched
t1["share_of_gap_that_is_composition"] = 1.0 - (gap_mix_matched / gap_raw) if gap_raw else None
# per-symbol, n-weighted by the LIMIT arm's own exposure
per = []
for s in common:
    per.append(dict(symbol=s, n_lim=int(w_l[s]), n_mkt=int(w_m[s]),
                    lim=float(mu_l[s]), mkt=float(mu_m[s]),
                    ratio=float(mu_l[s] / mu_m[s]) if mu_m[s] else None))
per.sort(key=lambda x: -x["n_lim"])
R["test1_per_symbol_by_limit_exposure"] = per
top = [p for p in per[:10]]
R["test1_top10_limit_symbols"] = {
    "share_of_limit_stops": float(sum(p["n_lim"] for p in top) / w_l.reindex(common).sum()),
    "n_worse_for_limit": int(sum(1 for p in top if p["ratio"] and p["ratio"] > 1)),
    "median_ratio": float(np.median([p["ratio"] for p in top if p["ratio"]])),
}

# ================= TEST 2 : intrabar LIMIT fill feasibility =================
src = L[L.entry_opt_r.notna()].copy()
# recover the booked fill instant and level from the export
raw = []
import gzip
import pickle
for mth in ["jun", "jul"]:
    for r in pickle.load(gzip.open(f"{OUT}/b1_limit_{mth}.pkl.gz", "rb")):
        o = r.get("orig") or {}
        if not o.get("fill_time") or o.get("gross") is None:
            continue
        raw.append(dict(key=r["key"], symbol=r["symbol"], side=r["side"], risk=r["risk_price"],
                        fill_price=o["fill_price"], fill_time=o["fill_time"]))
RW = pd.DataFrame(raw).set_index("key")
src = src.join(RW[["fill_price", "fill_time"]], on="key", how="inner")
src["ft"] = pd.to_datetime(src.fill_time, utc=True)
src["d"] = np.where(src.side == "LONG", 1.0, -1.0)

out = []
for sym, g in src.groupby("symbol"):
    bs = MAP.get(sym, sym)
    f = f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.exists(f):
        continue
    t = pd.read_csv(f, usecols=["time_msc", "bid", "ask"])
    t["tu"] = to_utc(t.time_msc / 1000.0)
    t = t.sort_values("tu")
    t = t[(t.ask >= t.bid) & (t.bid > 0)]
    tv = t.tu.values.astype("datetime64[ns]")
    bid = t.bid.values.astype("float64")
    ask = t.ask.values.astype("float64")
    n_t = len(tv)
    for r in g.itertuples():
        ftn = np.datetime64(r.ft.tz_localize(None))
        a = int(np.searchsorted(tv, ftn))
        z = int(np.searchsorted(tv, ftn + np.timedelta64(60, "s")))
        if a >= n_t or z <= a:
            continue
        d = r.d
        # best achievable entry-side price inside the fill minute
        best = ask[a:z].min() if d > 0 else bid[a:z].max()
        feasible = (best <= r.fill_price + 1e-12) if d > 0 else (best >= r.fill_price - 1e-12)
        out.append(dict(key=r.key, symbol=sym, feasible=bool(feasible),
                        intrabar_opt_r=float(max(0.0, d * (best - r.fill_price)) / r.risk),
                        baropen_opt_r=float(r.entry_opt_r), n_ticks=int(z - a)))
F = pd.DataFrame(out)
F.to_pickle(f"{OUT}/limit_feasibility.pkl")
R["test2_limit_fill_feasibility_intrabar"] = {
    "n": int(len(F)),
    "frac_feasible_intrabar": float(F.feasible.mean()),
    "frac_infeasible_intrabar": float(1 - F.feasible.mean()),
    "baropen_measure_frac_adverse": float((F.baropen_opt_r > 1e-9).mean()),
    "entry_opt_at_baropen_mean": float(F.baropen_opt_r.mean()),
    "entry_opt_intrabar_mean": float(F.intrabar_opt_r.mean()),
    "overstatement_factor_of_baropen_measure": (
        float(F.baropen_opt_r.mean() / F.intrabar_opt_r.mean()) if F.intrabar_opt_r.mean() else None),
    "mean_when_infeasible": float(F[~F.feasible].intrabar_opt_r.mean()) if (~F.feasible).any() else 0.0,
    "p95_when_infeasible": float(F[~F.feasible].intrabar_opt_r.quantile(.95)) if (~F.feasible).any() else 0.0,
}
json.dump(R, open(f"{OUT}/B1_ADVERSARIAL.json", "w"), indent=1)
print(json.dumps({k: v for k, v in R.items() if k != "test1_per_symbol_by_limit_exposure"}, indent=1))
