"""r1-5a — re-walk the LIVE SLEEVE ESTATE on both quote conventions.

Population: every one of the 22,354 trades in `AQ_ESTATE_TRADES_V2.json.gz`, the estate
artifact of record (32 sleeves, 2017-2026, `vps-bars-20260727`). Nothing sampled.

THE CONTROL THAT MAKES THIS ABOUT THE ESTATE
---------------------------------------------
The uncorrected arm is re-derived here from the bars, NOT copied from the artifact, and it
must reproduce the published `r_gross` to the bit on every row. If it does not, the delta
is about some other program and the run refuses to write.

Recipe copied from `phase6/receipts/aa_estate_generate.py:260-274`:

    plain = ExitPolicy(target_dist=c.target_dist, maxbars=80)
    trailing_runner sleeves add trail_arm = trigger_r * stop_dist,
                               trail_gap  = trail_gap_r * stop_dist
    r = winsorize_R(replay(...).r_gross)

THE CORRECTED ARM
-----------------
One substitution — `entry_price = bars[i].c + direction * spread` — which is the whole of
the quote-side correction for a fill-anchored contract (`walkforward.quote_side`). The
spread is AG's measured, era-aware, hour-aware model at the trade's own entry instant, on
all three bands, fail-closed.
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
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "R1_ESTATE_DELTA_V1.json"
ROWS = HERE / "R1_ESTATE_ROWS_V1.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80
BANDS = ("low", "mid", "high")

#: CORRECTED 2026-08-07 (wave-20 lane p4). This tuple was WRONG AT BOTH ENDS: it omitted
#: `sub_mid_dn_revert`, which is armed on both accounts and is the single largest
#: proportional casualty of this very lane's repair (+0.47842 -> +0.19325 R/trade, -59.6 %,
#: 38 exit-reason changes in 533 trades), and it included `mx_btcusd_d1_donchian_20_breakout`,
#: which the owner disarmed on 2026-08-05 (D-2 CLOSED, host commit 2fa77722d). Because of the
#: omission the armed sleeve that moved most never entered this lane's fold or p-value
#: receipts; `R1_ESTATE_DELTA_V2.json` and `R1_ADMISSION_STAT_V2.json` are the re-run.
#:
#: Do not write this list down again. `src/safety/armed_set.armed_sleeves()` is the single
#: source of truth and `tests/safety/test_armed_set_single_source.py` enforces it against
#: both the launcher and the owner-decision declaration.
try:  # pragma: no cover - the receipt script runs standalone as well as under pytest
    from src.safety.armed_set import armed_sleeves as _armed_sleeves

    ARMED = tuple(sorted(_armed_sleeves()))
except Exception:  # pragma: no cover - explicit fallback, kept identical to the manifest
    ARMED = ("crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback")
#: Armed at some point and pulled. `mx_btcusd...` ran FTMO-only on the `target_5R` frontier
#: contract, which is NOT what AA labelled; its per-sleeve delta is still carried because any
#: future frontier number has to carry it. Its measured estate delta is exactly 0.00000 on 318
#: trades, so its removal from ARMED costs this receipt nothing.
FORMERLY_ARMED = ("metals_core", "fx_jpy", "mx_btcusd_d1_donchian_20_breakout")


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
    series, index = load_series()
    print(f"loaded {len(series)} bar series", flush=True)

    per_sleeve = collections.defaultdict(lambda: {
        "old": [], "new": {b: [] for b in BANDS}, "delta": {b: [] for b in BANDS},
        "sd": [], "reason_old": collections.Counter(), "reason_new": collections.Counter(),
        "reason_changed": 0, "spread_over_risk": [], "symbols": collections.Counter(),
        "spread_coverage": collections.Counter(),
    })
    control = {"checked": 0, "mismatch": 0, "max_abs_err": 0.0, "examples": []}
    skips = collections.Counter()
    out_rows = []
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
            pol = ExitPolicy(target_dist=(float(td) if td else None), maxbars=MAXBARS,
                             label="plain")
            if trig_r is not None and gap_r is not None:
                pol = ExitPolicy(
                    target_dist=(float(td) if td else None),
                    trail_arm=float(trig_r) * sd, trail_gap=float(gap_r) * sd,
                    maxbars=MAXBARS, label="trailing_runner")

            old = replay(bars, i, d, stop_dist=sd, policy=pol)
            r_old = winsorize_R(old.r_gross)
            err = abs(r_old - float(r["r_gross"]))
            control["checked"] += 1
            control["max_abs_err"] = max(control["max_abs_err"], err)
            if err > 1e-9:
                control["mismatch"] += 1
                if len(control["examples"]) < 8:
                    control["examples"].append(
                        {"sleeve": sleeve, "symbol": r["symbol"],
                         "decision_bar_iso": r["decision_bar_iso"],
                         "published": r["r_gross"], "rederived": r_old})

            at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            row = {"sleeve": sleeve, "symbol": r["symbol"], "tf": TF_NAME[tf],
                   "entry_utc": at.isoformat(), "direction": d,
                   "r_old": r_old, "reason_old": old.exit_reason,
                   "sl_distance_price": sd}
            ok = True
            for band in BANDS:
                try:
                    s = spread_for(r["symbol"], at, account="FTMO", band=band)
                except SpreadUnavailable as exc:
                    skips[f"{sleeve}:no_spread[{band}]"] += 1
                    if band == "mid":
                        ok = False
                    row[f"r_new_{band}"] = None
                    continue
                anchor = replay_anchor(bars[i].c, d, s, BarQuote.BID)
                new = replay(bars, i, d, stop_dist=sd, policy=pol, entry_price=anchor)
                r_new = winsorize_R(new.r_gross)
                row[f"spread_{band}"] = s
                row[f"r_new_{band}"] = r_new
                if band == "mid":
                    row["reason_new"] = new.exit_reason
                per_sleeve[sleeve]["new"][band].append(r_new)
                per_sleeve[sleeve]["delta"][band].append(r_new - r_old)
                if band == "mid":
                    per_sleeve[sleeve]["reason_new"][new.exit_reason] += 1
                    if new.exit_reason != old.exit_reason:
                        per_sleeve[sleeve]["reason_changed"] += 1
                    per_sleeve[sleeve]["spread_over_risk"].append(s / sd if sd > 0 else None)
            if not ok:
                continue
            per_sleeve[sleeve]["old"].append(r_old)
            per_sleeve[sleeve]["reason_old"][old.exit_reason] += 1
            per_sleeve[sleeve]["symbols"][r["symbol"]] += 1
            out_rows.append(row)
        print(f"  {sleeve:36s} n={len(rows):6d}  {time.time()-t0:6.0f}s", flush=True)

    if control["mismatch"]:
        print("CONTROL FAILED — the re-derivation is not the estate's own labelling")
        print(json.dumps(control, indent=1))
        (HERE / "R1_ESTATE_CONTROL_FAILURE.json").write_text(json.dumps(control, indent=1))
        return 2

    sleeves = {}
    for s, a in sorted(per_sleeve.items()):
        sor = [x for x in a["spread_over_risk"] if x is not None]
        sleeves[s] = {
            "n": len(a["old"]),
            "old": summarise(a["old"]),
            **{f"new_{b}": summarise(a["new"][b]) for b in BANDS},
            **{f"delta_{b}": summarise(a["delta"][b]) for b in BANDS},
            "frac_delta_positive": (
                round(sum(1 for x in a["delta"]["mid"] if x > 1e-12) / len(a["delta"]["mid"]), 5)
                if a["delta"]["mid"] else None),
            "exit_reason_changed": a["reason_changed"],
            "exit_reason_changed_frac": (
                round(a["reason_changed"] / len(a["old"]), 5) if a["old"] else None),
            "exit_reasons_old": dict(sorted(a["reason_old"].items())),
            "exit_reasons_new_mid": dict(sorted(a["reason_new"].items())),
            "spread_over_risk_median": (
                round(statistics.median(sor), 6) if sor else None),
            "spread_over_risk_mean": (round(statistics.fmean(sor), 6) if sor else None),
            "n_symbols": len(a["symbols"]),
            "exit_policy": ("trailing_runner"
                            if _trail_policy(s)[0] is not None else "plain"),
            "armed": s in ARMED,
            "formerly_armed": s in FORMERLY_ARMED,
        }

    pool_old = [x for a in per_sleeve.values() for x in a["old"]]
    pool = {b: [x for a in per_sleeve.values() for x in a["delta"][b]] for b in BANDS}
    armed_delta = [x for s in ARMED for x in per_sleeve[s]["delta"]["mid"]]
    armed_old = [x for s in ARMED for x in per_sleeve[s]["old"]]

    agg = {
        "what": ("the quote-side correction, measured on the whole live sleeve estate, "
                 "both conventions, same walker, same bars"),
        "population": str(TRADES),
        "bars": BARS,
        "bar_quote": "BID (measured: phase20/receipts/r1/R1_QUOTESIDE_M15_V1.json)",
        "spread_source": ("src.costs.spread_model (Session AG) — tick anchor x bar-measured "
                          "era ratio x intraweek multiplier, at the trade's own entry "
                          "instant, FTMO, all three bands, fail-closed"),
        "anchoring": ("FILL — the live W7 book crosses the spread and hangs SL/TP off the "
                      "crossed price (ultimate_book/order_router.py:66-73)"),
        "control_rederives_published_r_gross": {
            "rows_checked": control["checked"],
            "mismatches": control["mismatch"],
            "max_abs_error": control["max_abs_err"],
        },
        "n_trades_scored": len(pool_old),
        "skips": dict(skips),
        "pooled": {
            "old": summarise(pool_old),
            **{f"delta_{b}": summarise(pool[b]) for b in BANDS},
            "frac_delta_positive_mid": (
                round(sum(1 for x in pool["mid"] if x > 1e-12) / len(pool["mid"]), 5)
                if pool["mid"] else None),
        },
        "armed_four": {
            "sleeves": list(ARMED),
            "old": summarise(armed_old),
            "delta_mid": summarise(armed_delta),
        },
        "per_sleeve": sleeves,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(agg, indent=1, sort_keys=True))
    with gzip.open(ROWS, "wt") as fh:
        json.dump(out_rows, fh)
    print("WROTE", OUT, "and", ROWS)
    print(json.dumps(agg["pooled"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
