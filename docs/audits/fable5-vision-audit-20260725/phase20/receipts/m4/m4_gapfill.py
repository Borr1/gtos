"""m4-A — the walker fills a stop AT the stop even when the bar GAPPED through it.

DEFECT UNDER TEST
-----------------
`primitives.simulate_detail` (`src/components/ultimate_book/primitives.py:79-80`) and its
sanctioned copy `walkforward.exits.replay` (`:387-390`) resolve a stop exit as

    if b.l <= stop:  return (stop - entry) / stop_dist

i.e. the fill is the STOP LEVEL, unconditionally. A market that OPENS beyond the stop
(`b.o < stop` for a long) never traded at `stop` on that bar: MT5 fills a stop-loss at the
first available price, which is `b.o`. The same arithmetic applies to the target in the
opposite direction (a limit that gaps through fills no worse than its level).

The tell is structural: the estate's own winsoriser `primitives.wins` clamps at **-1.3**,
a floor the shipped walker can never reach, because a stop always books exactly -1.

WHAT THIS MEASURES, WHOLE POPULATION, NOTHING SAMPLED
------------------------------------------------------
Every one of the 22,354 trades in `AQ_ESTATE_TRADES_V2.json.gz`, re-walked with r1's
recipe (which reproduces the published `r_gross` bit-for-bit; the control refuses to write
if it does not), then re-priced at the exit bar under three fill conventions:

    LEVEL   what ships today: fill at the stop / target level                (control)
    SYM     stop fills at min(stop, b.o) ; target fills at max(tgt, b.o)     (symmetric)
    ASYM    stop fills at min(stop, b.o) ; target still fills at its level   (conservative)

ASYM is the honest one for a prop account: a broker fills your stop at the gap and is
under no obligation to give you price improvement on your limit.

TRAIL EXITS ARE EXCLUDED FROM THE GAP TEST WHEN THE LEVEL WAS SET INTRABAR
---------------------------------------------------------------------------
`simulate` arms and fills a trail on one bar at `bar.h - gap` (B613). On that bar `b.o` is
below the level BY CONSTRUCTION -- the high had not happened at the open -- so a naive
`b.o < level` test would report ~100 % "gaps" on a trailing sleeve and be measuring B613's
intrabar assumption a second time, not a gap. A trail exit is admitted to the gap test
only when the exit bar did NOT set the running extreme, i.e. the level was already
standing at that bar's open. The excluded population is reported, not hidden.

COMPOSITION WITH r1
--------------------
r1's quote-side correction moves the entry anchor by one spread, which moves the stop and
target levels in tape space; the gap test then asks whether the bar opened past the MOVED
level. The two are therefore not additive by assumption, so the composed arm is walked
directly (`--compose`), on r1's own era-aware mid-band spread.
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
OUT = HERE / "M4_GAPFILL_V1.json"
ROWS = HERE / "M4_GAPFILL_ROWS_V1.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80

# scripts/run_book_supervisor.ps1:86-87 -- the committed launcher's tag lists, both books.
ARMED = (
    "crypto",
    "energy_agri",
    "sub_xvol_pullback",
    "sub_mid_dn_revert",
    "mx_btcusd_d1_donchian_20_breakout",
)


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


def regap(bars, i, entry, d, sd, pol, res):
    """Return (r_sym, r_asym, kind, gap_r, excluded) for one walked trade.

    `kind` in {"", "stop", "target", "trail"} names the leg that gapped; `excluded` is
    True when the exit is a trail whose level was set on its own exit bar (B613 territory,
    not a gap).
    """
    j = res.exit_index
    b = bars[j]
    reason = res.exit_reason
    bank = res.detail.get("partial_banked_r", 0.0) or 0.0
    frac = res.detail.get("partial_frac_taken", 0.0) or 0.0

    def _r(px):
        raw = ((px - entry) if d > 0 else (entry - px)) / sd
        return winsorize_R(bank + (1.0 - frac) * raw)

    r_level = winsorize_R(res.r_gross)
    if reason == "stop":
        lvl = entry - d * sd
        if (d > 0 and b.o < lvl) or (d < 0 and b.o > lvl):
            r = _r(b.o)
            return r, r, "stop", (r - r_level), False
        return r_level, r_level, "", 0.0, False
    if reason == "target" and pol.target_dist:
        lvl = entry + d * pol.target_dist
        if (d > 0 and b.o > lvl) or (d < 0 and b.o < lvl):
            return _r(b.o), r_level, "target", (_r(b.o) - r_level), False
        return r_level, r_level, "", 0.0, False
    if reason == "trail":
        # Level implied by the realised R (no partial on a trailing_runner sleeve).
        lvl = entry + d * (res.r_gross * sd)
        # Did THIS bar set the running extreme the level hangs off? If so the level did
        # not exist at the bar's open and the gap question is unanswerable on bars.
        set_here = (b.h >= lvl + pol.trail_gap - 1e-12) if d > 0 else (b.l <= lvl - pol.trail_gap + 1e-12)
        if set_here:
            return r_level, r_level, "", 0.0, True
        if (d > 0 and b.o < lvl) or (d < 0 and b.o > lvl):
            r = _r(b.o)
            return r, r, "trail", (r - r_level), False
        return r_level, r_level, "", 0.0, False
    return r_level, r_level, "", 0.0, False


def main() -> int:
    compose = "--compose" in sys.argv
    doc = json.load(gzip.open(TRADES))
    series, index = load_series()
    print(f"loaded {len(series)} bar series  compose={compose}", flush=True)

    per = collections.defaultdict(lambda: {
        "level": [], "sym": [], "asym": [], "d_asym": [],
        "n_stop": 0, "n_tgt": 0, "n_trail": 0, "n_trail_excluded": 0,
        "gap_stop": 0, "gap_tgt": 0, "gap_trail": 0,
        "gap_stop_r": [], "gap_tgt_r": [], "gap_trail_r": [],
        "gap_stop_weekend": 0, "gap_stop_intrasession": 0,
        "censored": 0, "reasons": collections.Counter(),
        "q_level": [], "q_asym": [], "q_n": 0,
    })
    control = {"checked": 0, "mismatch": 0, "max_abs_err": 0.0, "examples": []}
    skips = collections.Counter()
    rows_out = []
    min_r = 9e9
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

            res = replay(bars, i, d, stop_dist=sd, policy=pol)
            r_level = winsorize_R(res.r_gross)
            err = abs(r_level - float(r["r_gross"]))
            control["checked"] += 1
            control["max_abs_err"] = max(control["max_abs_err"], err)
            if err > 1e-9:
                control["mismatch"] += 1
                if len(control["examples"]) < 8:
                    control["examples"].append(
                        {"sleeve": sleeve, "symbol": r["symbol"],
                         "decision_bar_iso": r["decision_bar_iso"],
                         "published": r["r_gross"], "rederived": r_level})
            min_r = min(min_r, res.r_gross)

            a = per[sleeve]
            a["reasons"][res.exit_reason] += 1
            if res.exit_reason == "stop":
                a["n_stop"] += 1
            elif res.exit_reason == "target":
                a["n_tgt"] += 1
            elif res.exit_reason == "trail":
                a["n_trail"] += 1
            if (len(bars) - 1) < i + pol.maxbars:
                a["censored"] += 1

            entry = bars[i].c
            r_sym, r_asym, kind, gr, excl = regap(bars, i, entry, d, sd, pol, res)
            if excl:
                a["n_trail_excluded"] += 1
            if kind == "stop":
                a["gap_stop"] += 1
                a["gap_stop_r"].append(gr)
                j = res.exit_index
                dtm = (times[j] - times[j - 1]).total_seconds() / 60.0
                if dtm > TF_MINUTES[tf] + 1:
                    a["gap_stop_weekend"] += 1
                else:
                    a["gap_stop_intrasession"] += 1
            elif kind == "target":
                a["gap_tgt"] += 1
                a["gap_tgt_r"].append(gr)
            elif kind == "trail":
                a["gap_trail"] += 1
                a["gap_trail_r"].append(gr)

            a["level"].append(r_level)
            a["sym"].append(r_sym)
            a["asym"].append(r_asym)
            a["d_asym"].append(r_asym - r_level)

            if compose:
                at = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
                try:
                    s = spread_for(r["symbol"], at, account="FTMO", band="mid")
                except SpreadUnavailable:
                    skips[f"{sleeve}:no_spread"] += 1
                else:
                    anchor = replay_anchor(bars[i].c, d, s, BarQuote.BID)
                    qres = replay(bars, i, d, stop_dist=sd, policy=pol, entry_price=anchor)
                    q_level = winsorize_R(qres.r_gross)
                    _qs, q_asym, _k, _g, _e = regap(bars, i, anchor, d, sd, pol, qres)
                    a["q_level"].append(q_level)
                    a["q_asym"].append(q_asym)
                    a["q_n"] += 1

            if kind or (len(bars) - 1) < i + pol.maxbars:
                rows_out.append({
                    "sleeve": sleeve, "symbol": r["symbol"], "tf": TF_NAME[tf],
                    "entry_utc": (times[i] + dt.timedelta(minutes=TF_MINUTES[tf])).isoformat(),
                    "direction": d, "reason": res.exit_reason, "gap_leg": kind,
                    "r_level": r_level, "r_sym": r_sym, "r_asym": r_asym,
                    "gap_r": round(gr, 6),
                    "censored": bool((len(bars) - 1) < i + pol.maxbars),
                    "bars_held": res.bars_held,
                })
        print(f"  {sleeve:38s} n={len(rows):6d}  {time.time()-t0:6.0f}s", flush=True)

    if control["mismatch"]:
        print("CONTROL FAILED — the re-derivation is not the estate's own labelling")
        (HERE / "M4_GAPFILL_CONTROL_FAILURE.json").write_text(json.dumps(control, indent=1))
        return 2

    sleeves = {}
    for s, a in sorted(per.items()):
        stops = a["n_stop"] + (a["n_trail"] - a["n_trail_excluded"])
        sleeves[s] = {
            "n": len(a["level"]),
            "level": summarise(a["level"]),
            "sym": summarise(a["sym"]),
            "asym": summarise(a["asym"]),
            "delta_asym": summarise(a["d_asym"]),
            "n_stop": a["n_stop"], "n_target": a["n_tgt"],
            "n_trail": a["n_trail"], "n_trail_level_set_intrabar": a["n_trail_excluded"],
            "gap_through_stop": a["gap_stop"], "gap_through_trail": a["gap_trail"],
            "gap_through_target": a["gap_tgt"],
            "gap_stop_frac_of_stop_exits": (round(a["gap_stop"] / a["n_stop"], 5)
                                            if a["n_stop"] else None),
            "gap_frac_of_all_stop_type_exits": (
                round((a["gap_stop"] + a["gap_trail"]) / stops, 5) if stops else None),
            "gap_target_frac_of_targets": (round(a["gap_tgt"] / a["n_tgt"], 5)
                                           if a["n_tgt"] else None),
            "gap_stop_mean_extra_loss_r": (round(statistics.fmean(a["gap_stop_r"]), 6)
                                           if a["gap_stop_r"] else None),
            "gap_stop_worst_extra_loss_r": (round(min(a["gap_stop_r"]), 6)
                                            if a["gap_stop_r"] else None),
            "gap_stop_session_break": a["gap_stop_weekend"],
            "gap_stop_within_grid": a["gap_stop_intrasession"],
            "gap_target_mean_extra_gain_r": (round(statistics.fmean(a["gap_tgt_r"]), 6)
                                             if a["gap_tgt_r"] else None),
            "right_censored_trades": a["censored"],
            "exit_reasons": dict(sorted(a["reasons"].items())),
            "armed": s in ARMED,
            **({"compose_quote_side_only": summarise(a["q_level"]),
                "compose_quote_side_plus_gap": summarise(a["q_asym"])} if compose else {}),
        }

    pool_level = [x for a in per.values() for x in a["level"]]
    pool_sym = [x for a in per.values() for x in a["sym"]]
    pool_asym = [x for a in per.values() for x in a["asym"]]
    armed_level = [x for s in ARMED if s in per for x in per[s]["level"]]
    armed_asym = [x for s in ARMED if s in per for x in per[s]["asym"]]
    q_level = [x for a in per.values() for x in a["q_level"]]
    q_asym = [x for a in per.values() for x in a["q_asym"]]

    doc_out = {
        "schema": "gtos.m4.gapfill.v2",
        "population": {
            "artifact": str(TRADES.relative_to(REPO)),
            "bars": BARS,
            "n_trades_walked": len(pool_level),
            "n_sleeves": len(sleeves),
            "skips": dict(skips),
        },
        "control": {**control, "min_r_gross_pre_winsorise": round(min_r, 9),
                    "winsorise_floor_in_primitives_wins": -1.3,
                    "floor_reachable_under_shipped_walker": min_r < -1.0 - 1e-9},
        "pooled": {
            "level": summarise(pool_level),
            "sym": summarise(pool_sym),
            "asym": summarise(pool_asym),
            "delta_sym_per_trade": round(statistics.fmean(pool_sym) - statistics.fmean(pool_level), 6),
            "delta_asym_per_trade": round(statistics.fmean(pool_asym) - statistics.fmean(pool_level), 6),
            "gap_through_stops": sum(a["gap_stop"] for a in per.values()),
            "gap_through_trails": sum(a["gap_trail"] for a in per.values()),
            "gap_through_targets": sum(a["gap_tgt"] for a in per.values()),
            "n_stop_exits": sum(a["n_stop"] for a in per.values()),
            "n_trail_exits": sum(a["n_trail"] for a in per.values()),
            "n_trail_level_set_intrabar": sum(a["n_trail_excluded"] for a in per.values()),
            "n_target_exits": sum(a["n_tgt"] for a in per.values()),
            "gap_stop_session_break": sum(a["gap_stop_weekend"] for a in per.values()),
            "gap_stop_within_grid": sum(a["gap_stop_intrasession"] for a in per.values()),
            "right_censored_trades": sum(a["censored"] for a in per.values()),
        },
        "armed_pool": {
            "sleeves": list(ARMED),
            "level": summarise(armed_level),
            "asym": summarise(armed_asym),
            "delta_asym_per_trade": (
                round(statistics.fmean(armed_asym) - statistics.fmean(armed_level), 6)
                if armed_level else None),
        },
        **({"composition": {
            "n": len(q_level),
            "quote_side_only": summarise(q_level),
            "quote_side_plus_gap": summarise(q_asym),
            "gap_delta_on_top_of_quote_side": (
                round(statistics.fmean(q_asym) - statistics.fmean(q_level), 6)
                if q_level else None),
        }} if compose else {}),
        "sleeves": sleeves,
    }
    OUT.write_text(json.dumps(doc_out, indent=1))
    with gzip.open(ROWS, "wt") as f:
        json.dump(rows_out, f)
    print(json.dumps(doc_out["pooled"], indent=1))
    print(json.dumps(doc_out["armed_pool"], indent=1))
    if compose:
        print(json.dumps(doc_out["composition"], indent=1))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
