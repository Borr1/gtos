"""m4-B/C/D — is the cost model right NOW, at broker truth, on both accounts?

THE STRUCTURAL CLAIM UNDER TEST
--------------------------------
`src/costs/model.py:cost_r` sums four terms. Session AG built an **era-aware** model for
exactly ONE of them (`spread`), on the argument that a 37-day 2026 tick snapshot charged
to 2000-2026 history is a first-order look-ahead with no consistent sign. The other three
terms are still read from a single snapshot:

    commission  BROKER_TRUE_COSTS_V1.json, fitted from the 2026-06/07 deal export
    swap        `spec.swap_long` / `swap_short`, the 2026-07-25 `symbol_info` read
    slippage    a constant in R, `GATE_G1B_RECEIPT.md:767-768`, W7 (2026-06/07) only

This script measures the exposure of each, whole population, on the estate artifact.

THREE SEPARATE DEFECT CANDIDATES
---------------------------------
B  `usd_per_price_unit_per_lot = trade_tick_value / trade_tick_size` is an **FX-rate
   dependent** quantity for the 65 of 167 FTMO instruments whose profit currency is not
   USD, and it is a 2026-07-25 constant. `commission_r = usd_per_lot / (sl * upu)`, so a
   flat `per_lot` schedule carries the whole FX move as a multiplicative error. (For the
   `notional_bp` kind the fit and the use cancel; that is asserted here and CHECKED
   numerically rather than argued.)

C  `slippage.value_r` is charged as a constant R to every trade of a symbol, and the
   artifact says so in its own conventions block ("R at the live stop geometry; does not
   rescale with stop distance"). Slippage is physically a PRICE displacement. Charging it
   in R means the implied price slippage is proportional to the stop the strategy happens
   to have chosen. Two trades on the same symbol at different stop widths cannot both be
   right, and this script measures how wide that spread is.

D  `swap_long`/`swap_short` are a single 2026-07-25 read of an interest-differential
   quantity, charged to trades back to 2000. This script measures the EXPOSURE (swap's
   share of total cost, and the share of the estate that sits outside the snapshot era);
   the true historical swap curve is not in this repository, so the size is reported as an
   exposure and the direction as structural, never as a fabricated correction.
"""

from __future__ import annotations

import bisect
import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import CostTruthError, cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "M4_COST_TRUTH_V1.json"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80
BAND = "mid"

ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
         "mx_btcusd_d1_donchian_20_breakout")

#: profit currency -> (archive symbol carrying its USD rate, invert?)
#: `invert=False` means the series IS "profit-ccy per USD" (USDJPY, USDCAD, USDCHF);
#: `invert=True` means the series is "USD per profit-ccy" (EURUSD, GBPUSD, AUDUSD).
FX_SERIES = {
    "JPY": ("USDJPY", False),
    "CAD": ("USDCAD", False),
    "CHF": ("USDCHF", False),
    "EUR": ("EURUSD", True),
    "GBP": ("GBPUSD", True),
    "AUD": ("AUDUSD", True),
    "NZD": ("NZDUSD", True),
}


def _trail_policy(sleeve: str):
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "trailing_runner":
        return None, None
    return prof.get("trigger_r"), prof.get("trail_gap_r")


def load_series():
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    inv = {v: k for k, v in TF_NAME.items()}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = inv.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series, index = {}, {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = (
            [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
             for r in rows],
            [dt.datetime.fromisoformat(r["time"]) for r in rows],
        )
        index[key] = {ts: i for i, ts in enumerate(series[key][1])}
    return series, index


def load_fx_daily(series, index):
    """{ccy: (sorted [date], [rate as profit-ccy per USD])} from the D1 archive."""
    out = {}
    for ccy, (sym, invert) in FX_SERIES.items():
        key = (sym, TF_D1)
        if key not in series:
            continue
        bars, times = series[key]
        days, rates = [], []
        for b, t in zip(bars, times):
            if b.c <= 0:
                continue
            days.append(t.date())
            rates.append((1.0 / b.c) if invert else b.c)
        out[ccy] = (days, rates)
    return out


def fx_at(fx, ccy, day):
    tbl = fx.get(ccy)
    if not tbl:
        return None
    days, rates = tbl
    k = bisect.bisect_right(days, day) - 1
    if k < 0:
        return None
    return rates[k]


def summarise(vals):
    n = len(vals)
    if not n:
        return {"n": 0}
    mu = statistics.fmean(vals)
    sd = statistics.pstdev(vals) if n > 1 else 0.0
    return {"n": n, "mean": round(mu, 6),
            "se": round(sd / math.sqrt(n), 6) if n > 1 else None,
            "sum": round(math.fsum(vals), 4)}


def main() -> int:
    doc = json.load(gzip.open(TRADES))
    truth = load_broker_true_costs()
    series, index = load_series()
    fx = load_fx_daily(series, index)
    print(f"loaded {len(series)} bar series; fx for {sorted(fx)}", flush=True)

    inst = truth.doc["accounts"]["FTMO"]["instruments"]

    per = collections.defaultdict(lambda: {
        "gross": [], "net": [], "comm": [], "spread": [], "swap": [], "slip": [],
        "net_fx": [], "d_comm_fx": [], "sl_bps": [], "hold_h": [],
        "years": collections.Counter(), "nights": [],
    })
    sym_stop = collections.defaultdict(list)
    skips = collections.Counter()
    fxdiag = collections.defaultdict(lambda: {"n": 0, "ratio": []})
    t0 = time.time()

    for sleeve, rows in sorted(doc["trades"].items()):
        trig_r, gap_r = _trail_policy(sleeve)
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            if key not in index:
                skips[f"{sleeve}:no_series"] += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                skips[f"{sleeve}:bar_not_found"] += 1
                continue
            bars, times = series[key]
            if i + 2 >= len(bars):
                skips[f"{sleeve}:no_room"] += 1
                continue
            d = int(r["direction"])
            sd = float(r["sl_distance_price"])
            td = r["target_dist"]
            pol = ExitPolicy(target_dist=(float(td) if td else None), maxbars=MAXBARS)
            if trig_r is not None and gap_r is not None:
                pol = ExitPolicy(target_dist=(float(td) if td else None),
                                 trail_arm=float(trig_r) * sd,
                                 trail_gap=float(gap_r) * sd, maxbars=MAXBARS)
            res = replay(bars, i, d, stop_dist=sd, policy=pol)
            r_gross = winsorize_R(res.r_gross)
            at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            hh = res.bars_held * TF_MINUTES[tf] / 60.0
            side = "LONG" if d > 0 else "SHORT"
            try:
                b = cost_r(r["symbol"], "FTMO", hh, sl_distance_price=sd,
                           entry_price=bars[i].c, side=side, entry_utc=at,
                           spread_band=BAND)
            except CostTruthError as exc:
                skips[f"{sleeve}:cost[{str(exc)[:40]}]"] += 1
                continue

            a = per[sleeve]
            a["gross"].append(r_gross)
            a["net"].append(r_gross - b.total_r.value)
            a["comm"].append(b.commission_r.value)
            a["spread"].append(b.spread_r.value)
            a["swap"].append(b.swap_r.value)
            a["slip"].append(b.slippage_r.value)
            a["sl_bps"].append(sd / bars[i].c * 1e4)
            a["hold_h"].append(hh)
            a["years"][at.year] += 1
            a["nights"].append(b.detail["swap"].get("nights_charged", 0.0))
            sym_stop[r["symbol"]].append(sd / bars[i].c * 1e4)

            # --- B: FX-true usd_per_price_unit_per_lot ------------------------------
            rec = inst[r["symbol"]]
            cp = (rec.get("spec") or {}).get("currency_profit")
            upu_snap = rec["usd_per_price_unit_per_lot"]
            cs = (rec.get("spec") or {}).get("trade_contract_size")
            comm_fx = b.commission_r.value
            if cp and cp != "USD" and cs and upu_snap:
                x_snap = cs / upu_snap                    # profit-ccy per USD, snapshot
                x_true = fx_at(fx, cp, at.date())
                if x_true:
                    upu_true = cs / x_true
                    kind = rec["commission"].get("kind")
                    if kind == "per_lot":
                        # usd_per_lot is a FIXED USD charge; only the R denominator moves.
                        comm_fx = b.detail["commission"]["usd_per_lot_round_turn"] / (sd * upu_true)
                    elif kind == "notional_bp":
                        # the bp fit absorbed 1/x_snap; re-express it at x_true.
                        bp = rec["commission"]["value"] * x_snap / x_true
                        comm_fx = (bp / 1e4 * cs * bars[i].c) / (sd * upu_true)
                    fxdiag[r["symbol"]]["n"] += 1
                    fxdiag[r["symbol"]]["ratio"].append(x_snap / x_true)
            a["net_fx"].append(r_gross - (b.total_r.value - b.commission_r.value + comm_fx))
            a["d_comm_fx"].append(comm_fx - b.commission_r.value)
        print(f"  {sleeve:38s} {time.time()-t0:6.0f}s", flush=True)

    sleeves = {}
    for s, a in sorted(per.items()):
        tot = [c + sp + sw + sl for c, sp, sw, sl in
               zip(a["comm"], a["spread"], a["swap"], a["slip"])]
        sleeves[s] = {
            "n": len(a["gross"]),
            "gross": summarise(a["gross"]),
            "net": summarise(a["net"]),
            "cost_total": summarise(tot),
            "commission_r": summarise(a["comm"]),
            "spread_r": summarise(a["spread"]),
            "swap_r": summarise(a["swap"]),
            "slippage_r": summarise(a["slip"]),
            "slippage_share_of_cost": (round(statistics.fmean(a["slip"]) / statistics.fmean(tot), 5)
                                       if tot and statistics.fmean(tot) else None),
            "swap_share_of_cost": (round(statistics.fmean(a["swap"]) / statistics.fmean(tot), 5)
                                   if tot and statistics.fmean(tot) else None),
            "commission_share_of_cost": (round(statistics.fmean(a["comm"]) / statistics.fmean(tot), 5)
                                         if tot and statistics.fmean(tot) else None),
            "stop_bps_median": round(statistics.median(a["sl_bps"]), 4),
            "stop_bps_p05": round(statistics.quantiles(a["sl_bps"], n=20)[0], 4) if len(a["sl_bps"]) > 20 else None,
            "stop_bps_p95": round(statistics.quantiles(a["sl_bps"], n=20)[18], 4) if len(a["sl_bps"]) > 20 else None,
            "hold_hours_median": round(statistics.median(a["hold_h"]), 3),
            "nights_charged_mean": round(statistics.fmean(a["nights"]), 4),
            "delta_commission_fx_true": summarise(a["d_comm_fx"]),
            "net_fx_true": summarise(a["net_fx"]),
            "trades_pre_2022": sum(v for k, v in a["years"].items() if k < 2022),
            "armed": s in ARMED,
        }

    def pool(field):
        return [x for a in per.values() for x in a[field]]

    tot_all = [c + sp + sw + sl for c, sp, sw, sl in
               zip(pool("comm"), pool("spread"), pool("swap"), pool("slip"))]

    # --- C: the slippage identifiability test, per symbol -----------------------------
    slip_ident = {}
    for sym, ds in sorted(sym_stop.items()):
        if len(ds) < 40:
            continue
        q = statistics.quantiles(ds, n=20)
        slip_ident[sym] = {
            "n": len(ds), "stop_bps_p05": round(q[0], 4), "stop_bps_median": round(statistics.median(ds), 4),
            "stop_bps_p95": round(q[18], 4),
            "p95_over_p05": round(q[18] / q[0], 3) if q[0] > 0 else None,
            "slippage_r_charged": inst[sym]["slippage"]["value_r"],
            "slippage_coverage": inst[sym]["slippage"]["coverage"],
        }

    years = collections.Counter()
    for a in per.values():
        years.update(a["years"])

    doc_out = {
        "schema": "gtos.m4.cost_truth.v1",
        "population": {
            "artifact": str(TRADES.relative_to(REPO)),
            "n_trades_priced": len(pool("gross")),
            "account": "FTMO", "spread_band": BAND,
            "cost_artifact_version": truth.version,
            "skips": dict(skips),
        },
        "pooled": {
            "gross": summarise(pool("gross")),
            "net": summarise(pool("net")),
            "cost_total": summarise(tot_all),
            "commission_r": summarise(pool("comm")),
            "spread_r": summarise(pool("spread")),
            "swap_r": summarise(pool("swap")),
            "slippage_r": summarise(pool("slip")),
            "share_of_cost": {
                "commission": round(statistics.fmean(pool("comm")) / statistics.fmean(tot_all), 5),
                "spread": round(statistics.fmean(pool("spread")) / statistics.fmean(tot_all), 5),
                "swap": round(statistics.fmean(pool("swap")) / statistics.fmean(tot_all), 5),
                "slippage": round(statistics.fmean(pool("slip")) / statistics.fmean(tot_all), 5),
            },
            "delta_commission_fx_true": summarise(pool("d_comm_fx")),
            "net_fx_true": summarise(pool("net_fx")),
        },
        "era_exposure": {
            "trades_by_year": dict(sorted(years.items())),
            "snapshot_era": "2026-06/07 deal export + 2026-07-25 symbol_info",
            "trades_outside_snapshot_year": sum(v for k, v in years.items() if k < 2026),
            "frac_outside_snapshot_year": round(
                sum(v for k, v in years.items() if k < 2026) / sum(years.values()), 5),
            "trades_before_2022": sum(v for k, v in years.items() if k < 2022),
            "frac_before_2022": round(
                sum(v for k, v in years.items() if k < 2022) / sum(years.values()), 5),
        },
        "fx_lookahead_by_symbol": {
            k: {"n": v["n"],
                "x_snap_over_x_true_median": round(statistics.median(v["ratio"]), 5),
                "x_snap_over_x_true_min": round(min(v["ratio"]), 5),
                "x_snap_over_x_true_max": round(max(v["ratio"]), 5)}
            for k, v in sorted(fxdiag.items()) if v["n"]
        },
        "slippage_identifiability": slip_ident,
        "sleeves": sleeves,
    }
    OUT.write_text(json.dumps(doc_out, indent=1))
    print(json.dumps(doc_out["pooled"], indent=1))
    print(json.dumps(doc_out["era_exposure"], indent=1))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
