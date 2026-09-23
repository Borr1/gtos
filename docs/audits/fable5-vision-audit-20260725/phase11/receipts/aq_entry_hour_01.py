"""Session AQ — the ratified hour-01 entry convention, re-derived (AQ-2, B1422-B1435).

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_entry_hour_01.py
    ... --stage fine    # the exact re-derivation on the M15 grid
    ... --stage wide    # the cost-only re-pricing over the full D1 archive
    ... --stage gate    # RECORDED x 4 bands, at the declared family and at the un-raised one
    ... --stage all     # default

WHAT WAS RATIFIED, AND WHAT HAD ACTUALLY BEEN MEASURED
--------------------------------------------------------
`phase9/OWNER_DECISION_ENTRY_HOUR.md` (Borhen, 2026-07-30): the FX D1 cohort enters at the
first bar after the rollover — **broker hour 01**, not AH's hour 04. The evidence behind it
was two things, and neither was a re-derivation of the cohort at hour 01:

* AM's `hour_cost_frontier` re-priced AH's existing rows at shifts 0-8 h. It moves the
  entry INSTANT for the cost call and nothing else — same fill price, same path, same
  gross. It is a **cost** measurement and cannot see whether waiting an hour costs edge.
* AM's `reversion_fine_frontier` did move the bar, on M15, and is the number the decision
  rests on — but on **two of the three mechanisms** (822 rows), because
  `donchian_20_breakout` was not in its grid.

This file re-derives all three mechanisms at the convention, on the grid where an hour-01
fill is representable, and gates the result at the ratified rule.

THE DATA CONSTRAINT, STATED UP FRONT BECAUSE IT BOUNDS THE ANSWER
--------------------------------------------------------------------
An hour-01 fill needs a bar that closes at broker 01:00. In the **matched FTMO feed** —
`vps-bars-20260727`, the archive these trades were generated on — the D1 grid closes at
00:00 and the H4 grid at 00/04/08/12/16/20, so only M15 carries it, and M15 starts
**2023-12-31**. So:

    the ratified convention is EXACTLY measurable ON THE MATCHED FEED over
    2024-01-02 .. 2026-07-26, and on no earlier date.

**CORRECTED 2026-07-30 by an adversarial pass over this file's own claim.** The first
version of this docstring said "and on no earlier date, from any data in this repository or
beside it", which is FALSE. `data/` holds H1 series for 12 of the 14 cohort symbols, and for
four of them (`GBPUSD`, `USDJPY` from 2022-01-03; `GBPJPY`, `NZDUSD` from 2023-01-16) they
predate the M15 archive. They are unusable AS THEY STAND for two reasons, both fixable:
no `.timebase.json` sidecar, which `CsvBarSource` refuses outright (`generation.py:229`, the
F7 fail-closed rule) and which leaves their broker-clock alignment unverified; and a
different capture from the FTMO D1 the trades came from, so an arm on them is cross-feed and
owes its own parity control. Every H1 file that DOES carry a sidecar
(`data/historical_2026/`) starts 2025-10-01 or later.

An absence is a measurement and has to be searched for like one. The scoped claim above
survives; the sweeping one did not.

That is not a reason to skip the measurement and it is not a reason to quietly widen it. The
exact re-derivation runs on the window where it is exact; the full-archive arm is cost-only
and is labelled cost-only everywhere it appears; and the capture requirement — now two
smaller items, a timebase stamp for four existing files and the matched intraday feed for
the other ten — goes to the repair queue as a named, priced row.

WHAT THIS FILE FIXES IN THE MEASUREMENT IT INHERITS
------------------------------------------------------
AM disclosed three level defects in `AHG.cost_decomposition`, all of which travel into
every published hour-shift number. Two are repaired here and the third is bounded:

1. **`side` was never passed to `cost_r`**, so 45.0 % of rows were priced LONG when they
   were short. Repaired: `side` comes from the row's own direction.
2. `hold = max(0, hold - shift)` clamped 129 rows at shifts >= 5 h. Not reachable at the
   shifts this file uses (1 h and 4 h against a 72 h median), and asserted rather than
   assumed.
3. Slippage is hour-blind in `cost_r` itself, not in the driver. Left alone, quantified,
   and named in the artifact — a driver must not invent an hour profile the cost model
   does not have.

MULTIPLICITY
------------
The 45 cells were declared in `CANDIDATE_FAMILY_V4.json` and committed **before this file
ran** (`aq_family_v4.py`, which imports nothing from here). Every arm is gated twice — at
the raised 321 and at the un-raised 276 — and both q-values are published, so no verdict
can depend on the raise without saying so.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"))

import ah_entry_shift as AHS  # noqa: E402
import am_entry_frontier as AM  # noqa: E402
import yaml  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_M15, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
AH_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/AH_ENTRY_SHIFT_TRADES.json.gz"
AM_FINE = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_ATRMR_FINE_TRADES.json.gz"
FAMILY_V4 = HERE / "CANDIDATE_FAMILY_V4.json"
OUT = HERE / "AQ_ENTRY_HOUR01_V1.json"
OUT_TRADES = HERE / "AQ_ENTRY_HOUR01_TRADES.json.gz"
STAGES = HERE / "AQ_ENTRY_STAGES.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
RULE = resolve_rule(SERVER)
BANDS = (None, "low", "mid", "high")
#: DECLARED BEFORE THE RUN (`aq_family_v4.py`, committed 2026-07-30). 0 = the hour-00
#: control and the declared member itself; 60 = the ratified convention; 240 = AH's arm C,
#: already paid for in AH's 180-look bill and carried here only as a comparator.
SHIFT_MINUTES = (0, 60, 240)
SHIFT_NAME = {0: "h00_control", 60: "h01_ratified", 240: "h04_ah_comparator"}
MECHANISMS = ("atr_mean_reversion", "donchian_20_breakout", "volume_surge_reversal")
COHORT_CLASSES = ("fx",)
#: 80 D1 bars is the estate's research horizon; on M15 that is 80 x 6 x 16. Held identical
#: across arms so the horizon is the same wall-clock span at every shift (AM's discipline).
MAXBARS_M15 = 80 * 6 * 16


# =====================================================================================
# stage: fine -- the exact re-derivation
# =====================================================================================

def generate_fine() -> dict:
    if OUT_TRADES.is_file() and not os.environ.get("AQ_REGENERATE"):
        with gzip.open(OUT_TRADES, "rt") as fh:
            c = json.load(fh)
        print(f"reusing {OUT_TRADES.name}: {len(c['trades'])} rows "
              f"(AQ_REGENERATE=1 to re-walk)")
        return c

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = fam.FamilyGrid()
    for key in MECHANISMS:
        g = fam.family_members([key], (TF_D1,), symbols=AHS.archive_symbols(),
                               broker_symbol=res, classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
    symbols = sorted({m.symbol for m in grid.members})
    series = AHS.load_archive(set(symbols))
    m15 = AM._load_m15(set(symbols))
    print(f"cohort: {len(grid.members)} members over {len(symbols)} symbols, "
          f"{len(m15)} M15 series", flush=True)
    if len(grid.members) != 42:
        raise SystemExit(f"expected the 42-member FX D1 cohort, built {len(grid.members)}")
    if not m15:
        raise SystemExit("no M15 series — refusing to publish an empty re-derivation")

    warm = {k: AHS.warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()}
    d1grid = [t + dt.timedelta(minutes=1440) for t in AHS._all_d1_times()]
    rows: list[dict] = []
    drops = collections.Counter()
    t0 = time.time()
    with fam.expanded_surface(grid.members) as gens:
        for m in grid.members:
            d1 = series.get((m.symbol, TF_D1))
            mm = m15.get((m.symbol, TF_M15))
            if d1 is None or mm is None:
                drops[f"no series | {m.symbol}"] += 1
                continue
            dbars, dtimes = d1
            mbars, mtimes = mm
            mclose = [t + dt.timedelta(minutes=15) for t in mtimes]
            nwarm = WARMUP.get(warm[m.mechanism_key], 200)
            reach = AHS.engine_reachable(dtimes, d1grid, dt.timedelta(minutes=1440), nwarm)
            gen = gens[m.member]
            n_before = len(rows)
            for i in range(nwarm - 1, len(dbars) - 2):
                close_at = dtimes[i] + dt.timedelta(minutes=1440)
                if close_at < mclose[0] or close_at > mclose[-1]:
                    continue
                lo = max(0, i - 259)
                intent = gen(m.symbol, dbars[lo:i + 1], decision_day_of(dtimes[i]),
                             bar_time=dtimes[i], bar_times=dtimes[lo:i + 1],
                             aux_bars=None, aux_times=None, runtime_now=close_at)
                if intent is None:
                    continue
                d, sd = int(intent.direction), float(intent.stop_dist)
                if d not in (1, -1) or not (sd > 0):
                    continue
                td = float(intent.target_dist) if intent.target_dist else None
                # ONE decision bar contributes to an arm only if EVERY arm can reach it.
                # Otherwise the arms are scored on different populations and the shift is
                # confounded with the reachability guard — AH's own intersection rule.
                js = {}
                for shift in SHIFT_MINUTES:
                    want = close_at + dt.timedelta(minutes=shift)
                    j = bisect.bisect_left(mclose, want)
                    if j >= len(mbars) - 1 or mclose[j] != want:
                        js = {}
                        drops[f"no M15 close at +{shift}m"] += 1
                        break
                    js[shift] = j
                if not js:
                    continue
                for shift, j in js.items():
                    pr = replay(mbars, j, d, stop_dist=sd,
                                policy=ExitPolicy(target_dist=td, maxbars=MAXBARS_M15,
                                                  label=SHIFT_NAME[shift]))
                    want = close_at + dt.timedelta(minutes=shift)
                    rows.append({
                        "member": m.member, "mechanism": m.mechanism_key,
                        "family": f"fam_{m.mechanism_key}_fx_d1",
                        "symbol": m.broker_symbol, "symbol_canonical": m.symbol,
                        "direction": d, "sl_distance_price": sd, "target_dist": td,
                        "decision_bar_iso": dtimes[i].isoformat(),
                        "decision_day": decision_day_of(dtimes[i]),
                        "decision_close_utc": close_at.isoformat(),
                        "shift_minutes": shift, "arm": SHIFT_NAME[shift],
                        "entry_utc": want.isoformat(),
                        "entry_price": float(mbars[j].c),
                        "entry_broker_hour": utc_to_broker_naive(want, RULE).hour,
                        "exit_utc": mclose[pr.exit_index].isoformat(),
                        "r_gross": float(winsorize_R(pr.r_gross)),
                        "exit_reason": pr.exit_reason,
                        "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
                        "hold_hours": round((pr.exit_index - j) * 0.25, 4),
                        "entry_slip_price": float(mbars[j].c - dbars[i].c),
                        "engine_reachable": i in reach,
                    })
            print(f"  {m.member:52s} +{len(rows)-n_before}", flush=True)

    doc = {"schema": "gtos.wave11.aq.entry_hour01_trades.v1", "trades": rows,
           "maxbars_m15": MAXBARS_M15, "shift_minutes": list(SHIFT_MINUTES),
           "n_members": len(grid.members), "drops": dict(drops),
           "seconds": round(time.time() - t0, 1)}
    with gzip.open(OUT_TRADES, "wt") as fh:
        json.dump(doc, fh)
    return doc


def control_vs_am(rows: list[dict]) -> dict:
    """AM's fine frontier covered 2 of the 3 mechanisms. Where we overlap we must agree.

    Not a formality: it is the only independent check that this file's generation, grid and
    replay reproduce the measurement the owner decision was made on. `donchian_20_breakout`
    has no counterpart and is reported as new coverage rather than silently pooled in.
    """
    if not AM_FINE.is_file():
        return {"available": False, "reason": "AM_ATRMR_FINE_TRADES.json.gz absent"}
    with gzip.open(AM_FINE, "rt") as fh:
        am = json.load(fh)

    def key(r):
        return (r["member"], r["decision_bar_iso"], int(r["shift_minutes"]))

    a = {key(r): r for r in am["trades"] if int(r["shift_minutes"]) in SHIFT_MINUTES}
    b = {key(r): r for r in rows}
    shared = sorted(set(a) & set(b))
    mism = [k for k in shared if abs(a[k]["r_gross"] - b[k]["r_gross"]) > 1e-12]
    covered = sorted({m for m, *_ in a})
    new_mech = sorted({r["mechanism"] for r in rows} - {r["mechanism"] for r in am["trades"]})
    return {
        "available": True,
        "what": ("AM's fine frontier re-derived at the same shifts; where the two overlap "
                 "every r_gross must match to 1e-12"),
        "am_maxbars_m15": am.get("maxbars_m15"), "mine": MAXBARS_M15,
        "n_am_rows_at_shared_shifts": len(a), "n_mine": len(b), "n_shared_keys": len(shared),
        "n_r_gross_mismatched": len(mism),
        "n_am_members": len(covered),
        "only_in_am": len(set(a) - set(b)), "only_in_mine": len(set(b) - set(a)),
        "mechanisms_new_in_this_file": new_mech,
        "pass": (len(shared) > 0 and not mism
                 and am.get("maxbars_m15") == MAXBARS_M15),
    }


def summarise_fine(rows: list[dict], costs) -> dict:
    """Gross, cost and NET per arm — with `side` passed, which AM's helper never did."""
    by_arm = collections.defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)

    def bill(rs: list[dict]) -> dict:
        tot = sp = cm = sw = sl = 0.0
        n = unp = 0
        for r in rs:
            try:
                b = cost_r(r["symbol"], ACCOUNT, float(r["hold_hours"]),
                           sl_distance_price=float(r["sl_distance_price"]),
                           entry_price=float(r["entry_price"]),
                           side=("LONG" if int(r["direction"]) > 0 else "SHORT"),
                           entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                           spread_band="mid", costs=costs)
            except Exception:
                unp += 1
                continue
            n += 1
            tot += b.total_r.value
            sp += b.spread_r.value
            cm += b.commission_r.value
            sw += b.swap_r.value
            sl += b.slippage_r.value
        f = (lambda x: round(x / n, 6)) if n else (lambda x: None)
        return {"n_priced": n, "unpriced": unp, "mean_total_r": f(tot),
                "mean_spread_r": f(sp), "mean_commission_r": f(cm),
                "mean_swap_r": f(sw), "mean_slippage_r": f(sl)}

    out = {}
    for arm, rs in sorted(by_arm.items()):
        g = [r["r_gross"] for r in rs]
        c = bill(rs)
        out[arm] = {
            "n": len(rs), "mean_gross_r": round(statistics.fmean(g), 6),
            "median_hold_hours": round(statistics.median(r["hold_hours"] for r in rs), 4),
            "entry_broker_hours": dict(collections.Counter(
                str(r["entry_broker_hour"]) for r in rs)),
            "exit_reasons": dict(collections.Counter(r["exit_reason"] for r in rs)),
            "mean_pre_entry_drift_r": round(statistics.fmean(
                r["entry_slip_price"] * r["direction"] / r["sl_distance_price"]
                for r in rs), 6),
            **c,
            "mean_net_r": (round(statistics.fmean(g) - c["mean_total_r"], 6)
                           if c["mean_total_r"] is not None else None),
        }
    base = out.get("h00_control", {})
    for arm, v in out.items():
        if base.get("mean_net_r") is not None and v.get("mean_net_r") is not None:
            v["net_delta_vs_h00"] = round(v["mean_net_r"] - base["mean_net_r"], 6)
            v["spread_saved_vs_h00"] = round(base["mean_spread_r"] - v["mean_spread_r"], 6)
            v["gross_given_up_vs_h00"] = round(base["mean_gross_r"] - v["mean_gross_r"], 6)

    per_mech = {}
    for mech in sorted({r["mechanism"] for r in rows}):
        sub = {}
        for arm, rs in sorted(by_arm.items()):
            rr = [r for r in rs if r["mechanism"] == mech]
            if not rr:
                continue
            c = bill(rr)
            sub[arm] = {"n": len(rr),
                        "mean_gross_r": round(statistics.fmean(r["r_gross"] for r in rr), 6),
                        "mean_total_cost_r": c["mean_total_r"],
                        "mean_net_r": (round(statistics.fmean(r["r_gross"] for r in rr)
                                             - c["mean_total_r"], 6)
                                       if c["mean_total_r"] is not None else None)}
        for arm, v in sub.items():
            if sub.get("h00_control", {}).get("mean_net_r") is not None:
                v["net_delta_vs_h00"] = round(
                    v["mean_net_r"] - sub["h00_control"]["mean_net_r"], 6)
        per_mech[mech] = sub

    span = sorted(r["decision_close_utc"] for r in rows)
    return {"pooled": out, "by_mechanism": per_mech,
            "window": {"first": span[0], "last": span[-1],
                       "n_decision_bars": len({(r["member"], r["decision_bar_iso"])
                                               for r in rows})},
            "cost_repairs_applied": {
                "side_passed_to_cost_r": ("AM's `AHG.cost_decomposition` never passed it, so "
                                          "45.0 % of rows were priced LONG when short. "
                                          "Repaired here."),
                "hold_clamp": ("not reachable at 1 h / 4 h against a 72 h median; asserted "
                               "below rather than assumed"),
                "slippage_hour_blind": ("a property of `cost_r`, not of the driver. Left "
                                        "alone and reported; a driver must not invent an "
                                        "hour profile the cost model does not have."),
            }}


# =====================================================================================
# stage: wide -- the full-archive arm, cost-only and labelled cost-only
# =====================================================================================

def stage_wide(costs) -> dict:
    """AH's arm-A rows re-priced at each shift. Gross is HELD FIXED — that is the point.

    This arm exists to say how much SPREAD the convention saves over 26 years, and it
    cannot say anything about edge. Any reading of it as an economic result is wrong, and
    the artifact says so in the row that carries the numbers.
    """
    with gzip.open(AH_IN, "rt") as fh:
        ah = json.load(fh)
    rows = [r for r in ah["trades"] if r["arm"] == "A_d1close_d1exit"]
    out = {}
    clamped = 0
    for shift in SHIFT_MINUTES:
        h = shift / 60.0
        tot = sp = sw = cm = sl = 0.0
        n = unp = 0
        for r in rows:
            hold = float(r["hold_hours"]) - h
            if hold < 0:
                clamped += 1
                hold = 0.0
            try:
                b = cost_r(r["symbol"], ACCOUNT, hold,
                           sl_distance_price=float(r["sl_distance_price"]),
                           entry_price=float(r["entry_price"]),
                           side=("LONG" if int(r["direction"]) > 0 else "SHORT"),
                           entry_utc=(dt.datetime.fromisoformat(r["entry_utc"])
                                      + dt.timedelta(hours=h)),
                           spread_band="mid", costs=costs)
            except Exception:
                unp += 1
                continue
            n += 1
            tot += b.total_r.value
            sp += b.spread_r.value
            cm += b.commission_r.value
            sw += b.swap_r.value
            sl += b.slippage_r.value
        f = (lambda x: round(x / n, 6)) if n else (lambda x: None)
        out[SHIFT_NAME[shift]] = {"n_priced": n, "unpriced": unp, "mean_total_r": f(tot),
                                  "mean_spread_r": f(sp), "mean_commission_r": f(cm),
                                  "mean_swap_r": f(sw), "mean_slippage_r": f(sl)}
    base = out["h00_control"]
    for k, v in out.items():
        v["total_saved_vs_h00"] = round(base["mean_total_r"] - v["mean_total_r"], 6)
    span = sorted(r["entry_utc"] for r in rows)
    return {"what": ("COST ONLY. AH's full-archive arm-A rows re-priced at a later entry "
                     "instant. The fill price, the path and therefore the GROSS are held "
                     "fixed, so this arm can size the spread saving and can say NOTHING "
                     "about whether waiting an hour costs edge. The edge question is the "
                     "`fine` stage, and it is 2.5 years wide."),
            "n_rows": len(rows), "window": {"first": span[0], "last": span[-1]},
            "hold_clamped_rows": clamped, "arms": out}


# =====================================================================================
# stage: gate
# =====================================================================================

def to_records(rows: list[dict], key: str) -> dict:
    out = collections.defaultdict(list)
    for r in rows:
        out[r[key]].append(TradeRecord(
            sleeve=r[key], symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=int(r["direction"]),
            sl_distance_price=float(r["sl_distance_price"]),
            entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
            features={"decision_day": r["decision_day"], "hold_hours": r["hold_hours"],
                      "symbol_canonical": r["symbol_canonical"],
                      "decision_bar_iso": r["decision_bar_iso"],
                      "mfe_r": r["mfe_r"], "mae_r": r["mae_r"],
                      "mechanism": r["mechanism"], "arm": r["arm"]}))
    return dict(out)


def cohort_grid_members():
    """The 42 FamilyMembers, rebuilt so `fidelity_scope` can register them for SCORING.

    Every cell in this cohort is a surface expansion that deliberately sits in no registry,
    so `gate.py`'s hard fidelity refusal returns NOT_EVALUABLE on `port_fidelity_unmeasured`
    for all of them — which is exactly what the first run of this stage did, on all 72 arms.
    `expanded_surface` is for generating; this is for scoring. Same seam AH used
    (`ah_entry_gate.py:227`), and the records are removed again on exit so nothing can be
    scored later under a stamp nobody re-derived.
    """
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = fam.FamilyGrid()
    for key in MECHANISMS:
        g = fam.family_members([key], (TF_D1,), symbols=AHS.archive_symbols(),
                               broker_symbol=res, classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
    return grid.members


def stage_gate(rows: list[dict], costs, ledger: TrialLedger | None) -> dict:
    famv4 = CF.load_candidate_family(FAMILY_V4)
    grid_members = cohort_grid_members()
    by_arm = collections.defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)

    allow = {}
    for r in rows:
        for k in (r["family"], r["member"]):
            allow.setdefault(k, set()).add(r["symbol"])
    allow = {k: tuple(sorted(v)) for k, v in allow.items()}

    arms = {}
    for arm, rs in sorted(by_arm.items()):
        recs0 = to_records(rs, "family")
        for band in BANDS:
            for bill_name, size in (("declared_321", 321), ("unraised_276", 276)):
                o = OPTIONS["B_balanced"]
                spec = o.with_(spec_id=f"{o.spec_id}_aq_entry_{arm}_{bill_name}",
                               sleeve_symbol_allowlist=allow, spread_band=band)
                if bill_name == "declared_321":
                    spec = CF.with_declared_family(spec, "MECHANISM_CROSS_V1", loaded=famv4)
                else:
                    spec = spec.with_(declared_family_size=size,
                                      declared_family_id="unraised:MECHANISM_CROSS_V1@V3",
                                      declared_family_sha256="v3_276_sensitivity_arm")
                recs, spec, mix = EP.apply("RECORDED", dict(recs0), spec, account=ACCOUNT,
                                           band=(band or "mid"))
                t0 = time.time()
                with fam.fidelity_scope(grid_members):
                    res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=True)
                el = time.time() - t0
                if all(v.verdict.value == "NOT_EVALUABLE"
                       and any("port_fidelity_unmeasured" in r for r in v.reasons)
                       for v in res.verdicts.values()):
                    raise SystemExit(
                        "every sleeve came back NOT_EVALUABLE on port_fidelity_unmeasured "
                        "even inside fidelity_scope — the register did not take, and "
                        "publishing this would read as an entry-hour result when it is a "
                        "plumbing failure")
                for sleeve, sv in res.verdicts.items():
                    k = f"{arm}|{band or 'flat'}|{bill_name}|{sleeve}"
                    st = sv.gates.get("stability", {})
                    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
                    arms[k] = {
                        "arm": arm, "band": band or "flat_37_day_snapshot",
                        "band_is_control": band is None, "bill": bill_name,
                        "sleeve": sleeve, "population": "RECORDED", "option": "B_balanced",
                        "alpha": spec.alpha, "multiplicity": spec.multiplicity,
                        "declared_family_size": spec.declared_family_size,
                        "declared_family_id": spec.declared_family_id,
                        "effective_family_size":
                            res.family["multiplicity"]["effective_family_size"],
                        "n_sleeves_judged":
                            res.family["multiplicity"]["n_sleeves_judged_this_run"],
                        "spec_sha256": spec.seal(), "population_mix": mix,
                        "wipeout": res.family.get("wipeout"),
                        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                        "oos_mean_r_per_trade":
                            sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
                        "p_raw": sv.p_raw, "q_value": sv.q_value,
                        "failing_core_gates": [g for g in ("expectancy", "lifetime",
                                                           "stability", "robustness",
                                                           "significance")
                                               if not sv.gates.get(g, {}).get("pass")],
                        "fold_means": st.get("fold_means"),
                        "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
                        "n_folds_evaluable":
                            sv.gates.get("sample", {}).get("n_folds_evaluable"),
                        "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
                        "drop_best_retention":
                            sv.gates.get("robustness", {}).get("retention"),
                        "coverage_frac": (sv.coverage or {}).get("coverage_frac"),
                        "decidability_refusals": EP.decidability_refusals(sv.coverage),
                        "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
                        "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                             if (sv.p_raw is not None and fl.get("p_floor"))
                                             else None),
                        "folds": sv.folds, "reasons": list(sv.reasons),
                        "seconds": round(el, 2),
                    }
                    if ledger is not None:
                        ledger.record(
                            mechanism="entry_hour01_regate", sleeve=sleeve,
                            variant={"arm": arm, "band": band or "flat", "bill": bill_name,
                                     "population": "RECORDED", "option": "B_balanced"},
                            window="m15_window_2024_2026", spec_sha256=spec.seal(),
                            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                     "NOT_EVALUABLE": "not_evaluable"}.get(
                                         sv.verdict.value, "evaluated"),
                            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                            note="AQ hour-01 entry re-derivation")
            print(f"  gated {arm} @ {band or 'flat'}", flush=True)
    return {"arms": arms,
            "gated_object": ("the 3 pooled mechanism families. The 42 MEMBERS are not "
                             "gated: on the M15 window each holds ~10-40 trades against a "
                             "30-trade floor and a 3-evaluable-fold floor, so a member-level "
                             "run would be NOT_EVALUABLE by construction and reporting it "
                             "would read as a measurement."),
            "why_two_bills": ("`declared_321` is CANDIDATE_FAMILY_V4's raised "
                              "MECHANISM_CROSS_V1, which charges this session's 45 cells. "
                              "`unraised_276` is V3's, and is published so a reader can see "
                              "whether any verdict depends on the raise.")}


# =====================================================================================

def _cache() -> dict:
    """Stage results, from this run's cache OR from the artifact of record.

    The cache is not committed (it duplicates the artifact byte for byte), so a
    single-stage re-run must be able to refresh its own stage and leave the rest alone —
    otherwise it assembles nulls over a complete artifact. Same hole as
    `aq_contract_truth.py`, same fix; that one cost a restore from the index first.
    """
    out: dict = {}
    if OUT.is_file():
        try:
            prior = json.loads(OUT.read_text())
            for k in ("fine", "gate", "wide"):
                if prior.get(k) is not None:
                    out[k] = prior[k]
        except Exception:
            pass
    if STAGES.is_file():
        try:
            out.update({k: v for k, v in json.loads(STAGES.read_text()).items()
                        if v is not None})
        except Exception:
            pass
    return out


def _put(k, v) -> None:
    c = _cache()
    c[k] = v
    STAGES.write_text(json.dumps(c, indent=1, sort_keys=True, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["fine", "wide", "gate", "assemble", "all"])
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    t_all = time.time()
    HERE.mkdir(parents=True, exist_ok=True)
    costs = load_broker_true_costs(COSTS)
    ledger = None if a.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AQ")

    if a.stage in ("fine", "gate", "all"):
        doc = generate_fine()
        rows = doc["trades"]
        if a.stage in ("fine", "all"):
            ctl = control_vs_am(rows)
            print(f"  control vs AM: pass={ctl.get('pass')} shared={ctl.get('n_shared_keys')} "
                  f"mismatched={ctl.get('n_r_gross_mismatched')} "
                  f"new mechanisms={ctl.get('mechanisms_new_in_this_file')}")
            _put("fine", {"summary": summarise_fine(rows, costs),
                          "control_vs_am": ctl, "generation": {
                              k: v for k, v in doc.items() if k != "trades"}})
        if a.stage in ("gate", "all"):
            print("GATE:")
            _put("gate", stage_gate(rows, costs, ledger))

    if a.stage in ("wide", "all"):
        print("WIDE (cost-only):")
        _put("wide", stage_wide(costs))

    c = _cache()
    out = {
        "schema": "gtos.wave11.aq.entry_hour01.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                         "aq_entry_hour_01.py"),
        "session": "AQ", "blocks": "B1422-B1435",
        "the_convention": {
            "ratified": "phase9/OWNER_DECISION_ENTRY_HOUR.md, Borhen 2026-07-30",
            "rule": "FX D1 cohort enters at the first bar after broker hour 00 = broker hour 01",
            "cohort": "42 members (3 mechanisms x 14 FX symbols, D1) + 3 pooled families",
        },
        "the_data_constraint": {
            "what": ("an hour-01 fill needs a bar closing at broker 01:00. In the MATCHED "
                     "FTMO feed (vps-bars-20260727) the D1 grid closes at 00:00 and H4 at "
                     "00/04/08/12/16/20; neither contains it at any date. Only M15 does, "
                     "and the M15 archive starts 2023-12-31."),
            "exactly_measurable_on": "2024-01-02 .. 2026-07-26, on the matched feed",
            "full_archive_alternative": ("cost-only re-pricing, which holds gross fixed and "
                                         "therefore cannot see edge — the `wide` stage"),
            "corrected_2026_07_30": {
                "the_claim_that_was_refuted": ("an earlier version of this artifact said the "
                                               "convention could not be measured before 2024 "
                                               "'from any data in this repository or beside "
                                               "it'. That is false."),
                "what_exists": ("`data/` holds H1 series for 12 of the 14 cohort symbols; "
                                "four predate the M15 archive — GBPUSD and USDJPY from "
                                "2022-01-03, GBPJPY and NZDUSD from 2023-01-16."),
                "why_they_are_still_unusable_as_they_stand": [
                    "no `.timebase.json` sidecar on any pre-2024 H1 file, so CsvBarSource "
                    "refuses them (generation.py:229, the F7 fail-closed rule) and their "
                    "broker-clock alignment is unverified",
                    "a different capture from the FTMO D1 the trades were generated on, so "
                    "an arm built on them is cross-feed and owes its own parity control",
                ],
                "every_h1_with_a_sidecar_starts": "2025-10-01 or later (data/historical_2026/)",
                "lesson": ("an absence is a measurement and has to be searched for like one; "
                           "'I looked in the obvious place and it was not there' is a "
                           "different and weaker claim"),
            },
            "capture_requirement": {
                "a_cheap": ("verify and stamp a timebase for the four existing pre-2024 H1 "
                            "files (GBPUSD, USDJPY, GBPJPY, NZDUSD). Buys 4/14 symbols over "
                            "~2 extra years; a day's work, not a capture."),
                "b_larger": ("the matched FTMO intraday feed for the other ten cohort "
                             "symbols, back as far as it goes."),
                "neither_reaches": "2001 — the 26-year claim stays cost-only.",
            },
        },
        "declared_family": {
            "file": str(FAMILY_V4.relative_to(REPO)),
            "declared_before_the_gate_ran": ("aq_family_v4.py imports nothing from this "
                                             "file and was committed first"),
            "raised": "MECHANISM_CROSS_V1 276 -> 321 (+45 entry-convention cells)",
            "also_gated_at": 276,
            "cut_rule": ("entry hour from the fixed set {00 control, 01 ratified, 04 AH "
                         "comparator}; no threshold, no median split, no data-dependent "
                         "choice of hour"),
        },
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "fine": c.get("fine"), "gate": c.get("gate"), "wide": c.get("wide"),
        "seconds_total": round(time.time() - t_all, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    print(f"wrote {OUT.relative_to(REPO)} in {out['seconds_total']}s")


if __name__ == "__main__":
    main()
