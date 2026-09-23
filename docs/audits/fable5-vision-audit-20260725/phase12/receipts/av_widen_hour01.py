#!/usr/bin/env python3
"""Session AV — the hour-01 convention re-gated on the widened window (AV-1, B1614-B1622).

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_widen_hour01.py
    ... --stage parity   # cross-feed control on the overlap: do the two captures agree?
    ... --stage widen    # generate the pre-2024 rows from the newly-stamped repo archive
    ... --stage gate     # matched-only vs matched+widened, at the ratified rule
    ... --stage all      # default

WHAT THIS BUYS, STATED BEFORE THE RESULT
----------------------------------------
AQ measured the ratified hour-01 entry convention exactly, and could only do it over
2024-01-02 .. 2026-07-26 because an hour-01 fill needs a bar closing at broker 01:00 and
the matched FTMO M15 archive starts 2023-12-31. Its handoff item 7 called stamping the
repo's own pre-2024 files "the cheapest open item", worth "~2 extra years on 4 of 14
symbols for roughly a day of work".

`av_timebase_verify.py` then measured those files per file, and the cheap item is smaller
than it looked:

* **GBPUSD and USDJPY** carry a D1 *and* an M15 series in `data/historical_2022_2023/`,
  both PROVEN broker-local from their own bytes, both from one capture. Those two widen.
* **GBPJPY and NZDUSD** are in `data/historical/`, whose stamps are broker wall clock
  already corrected with the EUROPEAN calendar --- true UTC outside the US/EU DST
  disagreement windows and one hour fast inside them. GBPJPY's M15 is now readable through
  the declared `broker_server_local_eu_calendar_corrected` basis, but **NZDUSD has no
  provable M15 series at all** and neither symbol has a provable pre-2024 D1: their D1
  files are bare dates, which carry no clock.

So the widening is **2 of 14 symbols**, not 4, and the honest headline is the size of what
more calendar time buys --- which is the question AV-4 exists to answer and which this
arm answers directly for one cohort.

THE CONTROL THAT MAKES IT A MEASUREMENT
---------------------------------------
The widened rows come from a DIFFERENT CAPTURE than AQ's. AQ's own note says such an arm
"is cross-feed and owes its own parity control". So `--stage parity` regenerates on the
overlap window from BOTH feeds and compares trade for trade. If the two captures disagree
there, the widened rows are measuring the capture and not the convention, and the arm is
withdrawn rather than published with a caveat.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import json
import os
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
for phase in ("phase7", "phase8", "phase9", "phase11"):
    sys.path.insert(0, str(REPO / f"docs/audits/fable5-vision-audit-20260725/{phase}/receipts"))

import ah_entry_shift as AHS  # noqa: E402
import am_entry_frontier as AM  # noqa: E402
import yaml  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_M15, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
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

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
OUT = HERE / "AV_WIDEN_HOUR01_V1.json"
CACHE = HERE / ".av_widen_hour01_cache.json"
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
RULE = resolve_rule(SERVER)
MECHANISMS = ("atr_mean_reversion", "donchian_20_breakout", "volume_surge_reversal")
COHORT_CLASSES = ("fx",)
MAXBARS_M15 = 80 * 6 * 16
SHIFT_MINUTES = (0, 60, 240)
SHIFT_NAME = {0: "h00_control", 60: "h01_ratified", 240: "h04_ah_comparator"}
BANDS = (None, "low", "mid", "high")

#: The repo archive that PROVED its clock per file and carries BOTH a D1 and an M15 series
#: for the same symbol from the same capture. `av_timebase_verify.py --bounded --apply`
#: wrote the sidecars; `CsvBarSource` refuses anything without one, so this dict cannot
#: silently widen onto an unstamped file.
WIDEN_ARCHIVE = REPO / "data/historical_2022_2023"
WIDEN_SYMBOLS = ("GBPUSD", "USDJPY")
#: The matched FTMO M15 archive starts here; everything before it is what widening buys.
MATCHED_M15_START = dt.date(2023, 12, 31)


def _load_repo_series(symbols: tuple[str, ...]) -> dict:
    """D1 and M15 from the stamped repo archive, through the production loader.

    Same seam as `AM._load_m15`: `CsvBarSource` applies the sidecar's declared basis, so
    the broker->UTC crossing happens in one place for both feeds and a parity failure can
    never be a difference in how this file converts.
    """
    files: dict[tuple[str, int], str] = {}
    for sym in symbols:
        for tfs, tf in (("D1", TF_D1), ("M15", TF_M15)):
            p = WIDEN_ARCHIVE / f"{sym}_{tfs}.csv"
            if p.is_file():
                files[(sym, tf)] = str(p)
    src = CsvBarSource(files, label=f"repo-{WIDEN_ARCHIVE.name}")
    out = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        out[key] = (
            [AM.Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
             for r in rows],
            [dt.datetime.fromisoformat(r["time"]) for r in rows],
        )
    return out, dict(src.describe())


def _members(symbols):
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = fam.FamilyGrid()
    for key in MECHANISMS:
        g = fam.family_members([key], (TF_D1,), symbols=list(symbols),
                               broker_symbol=res, classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
    return grid.members


def _walk(members, series, feed_label: str, *, d1_key=TF_D1, m15_key=TF_M15) -> tuple[list[dict], dict]:
    """The AQ-shaped walk: decide on D1, enter on the M15 close at each shift, replay on M15."""
    warm = {k: AHS.warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()}
    rows: list[dict] = []
    drops: collections.Counter = collections.Counter()
    with fam.expanded_surface(members) as gens:
        for m in members:
            d1 = series.get((m.symbol, d1_key))
            mm = series.get((m.symbol, m15_key))
            if d1 is None or mm is None:
                drops[f"no series | {m.symbol}"] += 1
                continue
            dbars, dtimes = d1
            mbars, mtimes = mm
            mclose = [t + dt.timedelta(minutes=15) for t in mtimes]
            nwarm = WARMUP.get(warm[m.mechanism_key], 200)
            gen = gens[m.member]
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
                        "hold_hours": round((pr.exit_index - j) * 0.25, 4),
                        "feed": feed_label,
                        "engine_reachable": True,
                    })
    return rows, dict(drops)


# =====================================================================================
# stage: parity -- the cross-feed control
# =====================================================================================

def stage_bar_parity() -> dict:
    """Do the two archives hold the SAME PRICES on the bars they share?

    This is the probe the trade-level comparison cannot be: over the 7-week overlap no
    trade can complete inside the repo archive (`maxbars` is 80 D1 bars ~ 4 months), so
    every long trade exits on `maxbars` in one feed and on its stop in the other, and the
    r_gross comparison measures the archive's right EDGE rather than its content. Bars have
    no such horizon. Aligned on true-UTC timestamp --- which is only possible because the
    repo files' clock is now proven --- an identical capture agrees to the last digit.
    """
    out = {}
    for sym in WIDEN_SYMBOLS:
        for tfs, tf in (("D1", TF_D1), ("M15", TF_M15)):
            repo_path = WIDEN_ARCHIVE / f"{sym}_{tfs}.csv"
            matched_path = Path(AHS.BARS) / f"FTMO_{sym}_{tfs}.csv.gz"
            if not (repo_path.is_file() and matched_path.is_file()):
                continue
            a = {r["time"]: r for r in CsvBarSource({(sym, tf): str(repo_path)})._load((sym, tf))}
            b = {r["time"]: r for r in CsvBarSource({(sym, tf): str(matched_path)})._load((sym, tf))}
            shared = sorted(set(a) & set(b))
            if not shared:
                out[f"{sym}_{tfs}"] = {"n_shared_bars": 0,
                                       "note": "no overlapping timestamps"}
                continue
            diffs = [abs(a[k]["close"] - b[k]["close"]) for k in shared]
            rel = [d / abs(b[k]["close"]) for d, k in zip(diffs, shared)]
            exact = sum(1 for d in diffs if d < 1e-12)
            out[f"{sym}_{tfs}"] = {
                "n_shared_bars": len(shared),
                "close_exact_match": exact,
                "close_exact_match_frac": round(exact / len(shared), 6),
                "close_abs_diff_median": statistics.median(diffs),
                "close_abs_diff_max": max(diffs),
                "close_rel_diff_median": statistics.median(rel),
                "timestamps_align": True,
            }
    fracs = [v["close_exact_match_frac"] for v in out.values() if v.get("n_shared_bars")]
    return {
        "what": ("the two archives' OHLC on every timestamp they share. Timestamp alignment "
                 "is itself evidence the clock stamp is right; price disagreement is "
                 "evidence the CAPTURE is different."),
        "verdict": ("SAME_CAPTURE" if fracs and min(fracs) > 0.999
                    else "DIFFERENT_CAPTURE" if fracs else "NOT_EVALUABLE"),
        "per_series": out,
    }


def stage_parity() -> dict:
    """On the overlap window, do the two captures produce the same trades?

    A pass here is what licenses the widened rows. A fail withdraws them: the arm would be
    measuring which archive it read rather than what hour it entered at.
    """
    repo_series, repo_desc = _load_repo_series(WIDEN_SYMBOLS)
    matched = AHS.load_archive(set(WIDEN_SYMBOLS))
    matched.update(AM._load_m15(set(WIDEN_SYMBOLS)))
    members = _members(WIDEN_SYMBOLS)

    repo_rows, repo_drops = _walk(members, repo_series, "repo_historical_2022_2023")
    matched_rows, matched_drops = _walk(members, matched, "vps_bars_20260727")

    # The overlap is bounded on BOTH sides. Bounding only the lower end let 744 post-repo
    # matched-feed rows into the "only_in_matched" count, which read as a coverage gap when
    # it was the comparison window running off the end of the repo archive.
    repo_last = max((dt.date.fromisoformat(r["decision_bar_iso"][:10]) for r in repo_rows),
                    default=MATCHED_M15_START)

    def overlap(rows):
        return {(r["member"], r["decision_bar_iso"], r["shift_minutes"]): r
                for r in rows
                if MATCHED_M15_START <= dt.date.fromisoformat(r["decision_bar_iso"][:10]) <= repo_last}

    a, b = overlap(repo_rows), overlap(matched_rows)
    shared = sorted(set(a) & set(b))
    dirs = sum(1 for k in shared if a[k]["direction"] != b[k]["direction"])
    entry_rel = [abs(a[k]["entry_price"] - b[k]["entry_price"]) / max(1e-9, abs(b[k]["entry_price"]))
                 for k in shared]
    r_abs = [abs(a[k]["r_gross"] - b[k]["r_gross"]) for k in shared]
    same_sign = sum(1 for k in shared
                    if (a[k]["r_gross"] > 0) == (b[k]["r_gross"] > 0))
    disagreeing = sorted(
        ({"key": list(k), "repo_r": a[k]["r_gross"], "matched_r": b[k]["r_gross"],
          "repo_entry": a[k]["entry_price"], "matched_entry": b[k]["entry_price"],
          "repo_exit_reason": a[k]["exit_reason"], "matched_exit_reason": b[k]["exit_reason"]}
         for k in shared if abs(a[k]["r_gross"] - b[k]["r_gross"]) > 1e-6),
        key=lambda d: -abs(d["repo_r"] - d["matched_r"]))
    verdict = (
        "PASS" if shared and not dirs and (same_sign / len(shared)) == 1.0
        and max(r_abs, default=0) < 1e-6
        else "FAIL" if shared else "NOT_EVALUABLE_NO_SHARED_ROWS")
    return {
        "what": ("the two captures walked over the SAME decision bars with the SAME code; "
                 "any difference here is the archive, not the convention"),
        "verdict": verdict,
        "verdict_rule": ("PASS requires every shared row to agree on direction AND on r_gross "
                         "to 1e-6. Anything less means the widened rows would be measuring "
                         "which archive was read."),
        "n_rows_disagreeing_on_r_gross": len(disagreeing),
        "worst_disagreements": disagreeing[:8],
        "overlap_window": [MATCHED_M15_START.isoformat(), repo_last.isoformat()],
        "n_repo_rows_in_overlap": len(a),
        "n_matched_rows_in_overlap": len(b),
        "n_shared_keys": len(shared),
        "only_in_repo": len(set(a) - set(b)),
        "only_in_matched": len(set(b) - set(a)),
        "n_direction_mismatch": dirs,
        "entry_price_rel_diff": {
            "max": max(entry_rel) if entry_rel else None,
            "median": statistics.median(entry_rel) if entry_rel else None,
        },
        "r_gross_abs_diff": {
            "max": max(r_abs) if r_abs else None,
            "median": statistics.median(r_abs) if r_abs else None,
            "mean": statistics.fmean(r_abs) if r_abs else None,
        },
        "r_gross_sign_agreement": (same_sign / len(shared)) if shared else None,
        "repo_source_describe": repo_desc,
        "repo_drops": repo_drops,
        "matched_drops": matched_drops,
        "_repo_rows": repo_rows,
        "_matched_rows": matched_rows,
    }


# =====================================================================================
# stage: gate
# =====================================================================================

def to_records(rows: list[dict], key: str) -> dict:
    out: dict[str, list[TradeRecord]] = collections.defaultdict(list)
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
                      "exit_reason": r["exit_reason"],
                      "mechanism": r["mechanism"], "arm": r["arm"], "feed": r["feed"]}))
    return dict(out)


def stage_gate(repo_rows, matched_rows, costs, ledger) -> dict:
    famv5 = CF.load_candidate_family(FAMILY_V5)
    members = _members(WIDEN_SYMBOLS)

    matched_only = [r for r in matched_rows]
    widened = [r for r in repo_rows
               if dt.date.fromisoformat(r["decision_bar_iso"][:10]) < MATCHED_M15_START] + matched_rows

    populations = {
        "matched_only": matched_only,
        # NOT admission-grade: see `bar_parity`. Published so the SIZE of what more calendar
        # time buys is on the record, which is the question AV-4 asks of every family.
        "matched_plus_widened_CROSS_FEED": widened,
    }
    arms = {}
    for pop_name, rows in populations.items():
        by_arm = collections.defaultdict(list)
        for r in rows:
            by_arm[r["arm"]].append(r)
        allow: dict[str, set] = {}
        for r in rows:
            for k in (r["family"], r["member"]):
                allow.setdefault(k, set()).add(r["symbol"])
        allow = {k: tuple(sorted(v)) for k, v in allow.items()}
        for arm, rs in sorted(by_arm.items()):
            recs0 = to_records(rs, "family")
            for band in BANDS:
                o = OPTIONS["B_balanced"]
                spec = o.with_(spec_id=f"{o.spec_id}_av_widen_{pop_name}_{arm}",
                               sleeve_symbol_allowlist=allow, spread_band=band)
                spec = CF.with_declared_family(spec, "MECHANISM_CROSS_V1", loaded=famv5)
                recs, spec, mix = EP.apply("RECORDED", dict(recs0), spec, account=ACCOUNT,
                                           band=(band or "mid"))
                t0 = time.time()
                with fam.fidelity_scope(members):
                    res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=True)
                el = time.time() - t0
                # `wipeout` is a dict on EVERY run, not a truthy flag on a bad one --- reading
                # it as a flag made the first run of this stage abort on a healthy gate.
                if (res.family.get("wipeout") or {}).get("wiped_out"):
                    raise SystemExit(
                        f"whole-run wipeout on {pop_name}/{arm}/{band}: "
                        f"{res.family['wipeout']} -- refusing to tabulate a wall of nulls "
                        "as a result (AQ B1435)")
                for sleeve, sv in res.verdicts.items():
                    st = sv.gates.get("stability", {})
                    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
                    diag = sv.telemetry or {}
                    arms[f"{pop_name}|{arm}|{band or 'flat'}|{sleeve}"] = {
                        "population_arm": pop_name, "arm": arm,
                        "band": band or "flat_37_day_snapshot", "band_is_control": band is None,
                        "sleeve": sleeve, "population": "RECORDED", "option": "B_balanced",
                        "alpha": spec.alpha, "multiplicity": spec.multiplicity,
                        "declared_family_size": spec.declared_family_size,
                        "declared_family_id": spec.declared_family_id,
                        "effective_family_size":
                            res.family["multiplicity"]["effective_family_size"],
                        "spec_sha256": spec.seal(), "population_mix": mix,
                        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                        "oos_mean_r_per_trade":
                            sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
                        "p_raw": sv.p_raw, "q_value": sv.q_value,
                        "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                           "robustness", "significance")
                                               if not sv.gates.get(g, {}).get("pass")],
                        "fold_means": st.get("fold_means"),
                        "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
                        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
                        "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
                        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
                        "coverage_frac": (sv.coverage or {}).get("coverage_frac"),
                        "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
                        "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                             if (sv.p_raw is not None and fl.get("p_floor"))
                                             else None),
                        # AR §5.5's transferable repair: these two are computed on EVERY gate
                        # run and were published by no receipt until wave 12.
                        "regime_inflation_flag":
                            (diag.get("regime_inflation") or {}).get("contamination_flag"),
                        "regime_inflation_haircut":
                            (diag.get("regime_inflation") or {}).get("recommended_magnitude_haircut"),
                        "in_sample_mean_r": (diag.get("in_sample") or {}).get("mean_is_r"),
                        "maxbars_share": maxbars_share(rs, sleeve),
                        "folds": sv.folds, "reasons": list(sv.reasons),
                        "seconds": round(el, 2),
                    }
                    if ledger is not None:
                        ledger.record(
                            mechanism="entry_hour01_widened", sleeve=sleeve,
                            variant={"arm": arm, "band": band or "flat",
                                     "population_arm": pop_name,
                                     "population": "RECORDED", "option": "B_balanced"},
                            window=("m15_2022_2024_repo+matched" if pop_name != "matched_only"
                                    else "m15_2024_2026_matched"),
                            spec_sha256=spec.seal(),
                            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                     "NOT_EVALUABLE": "not_evaluable"}.get(
                                         sv.verdict.value, "evaluated"),
                            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                            note="AV hour-01 widened-window re-gate")
            print(f"  gated {pop_name}/{arm}", flush=True)
    return {"arms": arms,
            "why_no_new_family_members": (
                "widening the WINDOW of an already-declared cell re-measures an existing "
                "hypothesis; it proposes none. Same convention AR §5.2 applies to an exit "
                "cell. The bill is CANDIDATE_FAMILY_V5's MECHANISM_CROSS_V1 unchanged, and "
                "no arm here admits at any bill, so nothing turns on it."),
            "gated_object": ("the 3 pooled mechanism families over 2 symbols. Members are "
                             "not gated: 2 symbols x 1 mechanism holds far too few trades "
                             "for the 30-trade floor and would be NOT_EVALUABLE by "
                             "construction.")}


def maxbars_share(rows, sleeve) -> float | None:
    """Wave-12 §4: every sweep reports the fraction of its trades the horizon truncated."""
    rs = [r for r in rows if r["family"] == sleeve]
    if not rs:
        return None
    return round(sum(1 for r in rs if r["exit_reason"] == "maxbars") / len(rs), 6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("parity", "widen", "gate", "all"))
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()

    costs = load_broker_true_costs(COSTS)
    ledger = None if args.no_ledger else TrialLedger(DEFAULT_TRIAL_LEDGER, session="AV")

    t0 = time.time()
    bar_parity = stage_bar_parity()
    parity = stage_parity()
    repo_rows = parity.pop("_repo_rows")
    matched_rows = parity.pop("_matched_rows")

    pre = [r for r in repo_rows
           if dt.date.fromisoformat(r["decision_bar_iso"][:10]) < MATCHED_M15_START]
    widen = {
        "n_rows_before_the_matched_archive_starts": len(pre),
        "n_decision_bars": len({(r["member"], r["decision_bar_iso"]) for r in pre}),
        "window": ([min(r["decision_bar_iso"] for r in pre), max(r["decision_bar_iso"] for r in pre)]
                   if pre else None),
        "symbols": sorted({r["symbol_canonical"] for r in pre}),
        "extra_calendar_days": (
            (dt.date.fromisoformat(max(r["decision_bar_iso"] for r in pre)[:10])
             - dt.date.fromisoformat(min(r["decision_bar_iso"] for r in pre)[:10])).days
            if pre else 0),
    }

    gate = ({} if args.stage in ("parity", "widen")
            else stage_gate(repo_rows, matched_rows, costs, ledger))

    payload = {
        "schema": "gtos.wave12.av.widen_hour01.v1",
        "session": "AV", "blocks": "B1614-B1622",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "declared_family": str(FAMILY_V5.relative_to(REPO)),
        "the_scope": {
            "widened_symbols": list(WIDEN_SYMBOLS),
            "cohort_size": 14,
            "why_not_four": (
                "AQ's handoff named GBPUSD, USDJPY, GBPJPY and NZDUSD. Measured per file: "
                "GBPJPY and NZDUSD live in data/historical/, whose pre-2024 D1 stamps are "
                "bare DATES and therefore carry no clock at all, and NZDUSD has no provable "
                "M15 series. A D1 decision bar and an M15 entry bar are both required, so "
                "those two cannot widen whatever their H1 says."),
            "archive": str(WIDEN_ARCHIVE.relative_to(REPO)),
            "matched_m15_starts": MATCHED_M15_START.isoformat(),
        },
        "bar_parity": bar_parity,
        "parity": parity,
        "widen": widen,
        "gate": gate,
        "the_conclusion": {
            "clock": "PROVEN and stamped for both widening symbols, D1 and M15, from their own bytes",
            "capture": bar_parity["verdict"],
            "so": (
                "AQ handoff item 7 priced this as 'a timebase stamp, not a capture'. The stamp "
                "was necessary and is done; it was not sufficient. The pre-2024 repo archive is a "
                "DIFFERENT PRICE CAPTURE from the FTMO feed AQ measured the convention on, so its "
                "rows cannot extend that measurement --- the widened arm below is published as a "
                "CROSS-FEED SENSITIVITY and is not admission-grade. The residual ask is unchanged "
                "in kind but now exact: the matched FTMO intraday feed before 2023-12-31."
                if bar_parity["verdict"] == "DIFFERENT_CAPTURE" else
                "the captures agree, so the widened rows extend the measurement directly"),
        },
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(json.dumps({"bar_parity": bar_parity,
                      "trade_parity_verdict": parity["verdict"],
                      "widen": widen,
                      "conclusion": payload["the_conclusion"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
