"""The estate walk in DIAGNOSTIC mode: every verdict becomes a prescription.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_estate_walk.py

Reads `AA_ESTATE_TRADES.json.gz` (from `aa_estate_generate.py`) and produces four things
nothing in this programme has produced before:

  1. **`REPAIR_QUEUE_V1.json`** — one row per (sleeve, prescription, evidence). Per-gate
     margins, the failing folds / symbols / sessions, the four-term cost decomposition,
     MFE-MAE aggregates, realised holds, and what to DO. No gate is relaxed to get it: the
     seven gates and their sealed thresholds are the same objects W wrote, and there is a
     test that runs the gate both ways and compares verdicts field by field.

  2. **Cost-true per-sleeve daily splits** (`AA_SLEEVE_SPLITS_V1.json`) — the input
     `FOURTH_REVIEW.md` §4.2 names as missing for the learning actuator, whose backtest
     half currently reads legacy-cost CP4/CP5 splits. Train / OOS / sealed day-series at
     broker truth, per sleeve, with the fold calendar that produced them.

  3. **The cost-repair A/B** — the same walk at `BROKER_TRUE_COSTS_V1.json` and at
     `V1_1` (the energy classifier fix), so the effect of landing the fix on `energy_agri`
     is measured rather than carried as a sensitivity.

  4. **The orphan triage** — `leadlag_core` (n=3,115, +362.6 R cached) and `subh4_ll_fx`
     (n=357) have no generator module in `sleeves/`, so they cannot be re-walked at broker
     truth however much anyone wants to. What they DO have is a cached daily R series, and
     the statistical half of the gate runs on that: is there a persistent edge worth
     building the generator for? Stamped LEGACY_COST throughout, because it is.

MULTIPLICITY ACROSS SESSIONS IS CHARGED, NOT ASSUMED AWAY
----------------------------------------------------------
`declared_family_size` counts LOOK EVENTS: W's 12 mx sleeves, X's estate walk, and this
one. A second look at the same hypothesis is a second chance to be wrong about it. Every
gate invocation is also appended to the trial-budget ledger, so the next session's DSR can
deflate against a counted number instead of `gate.py:47-48`'s "number nobody measured".

THE COST LOOK-AHEAD IS INHERITED, NOT DROPPED
----------------------------------------------
`BROKER_TRUE_COSTS_V1.json` measures spread over 37 days in 2026 and charges it as a
constant to a panel running 2000-2026. Spreads compressed, so every net number here is
optimistic by an unmeasured amount. Session AG's banded spread model is the repair;
until it lands, `gate._cost_window_note()` stamps it on every result and so does this.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import os
import pickle
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.folds import assign_folds, build_fold_calendar  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import build_daily_panel, price_trades  # noqa: E402
from src.research_infra.walkforward.registry import build_symbol_allowlist  # noqa: E402
from src.research_infra.walkforward.spec import GateSpec  # noqa: E402
from src.research_infra.walkforward.stats import (  # noqa: E402
    block_length_auto,
    combined_null_p,
)

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
#: `AA_TRADES_IN` / `AA_OUT_SUFFIX` exist so the whole pipeline can be exercised end to end
#: against X's already-generated trades while AA's own generation is still running. The
#: default is the real thing; the override never silently renames the real outputs.
IN = Path(os.environ.get("AA_TRADES_IN") or (HERE / "AA_ESTATE_TRADES.json.gz")).resolve()
_SFX = os.environ.get("AA_OUT_SUFFIX", "")
Q_OUT = HERE / f"REPAIR_QUEUE_V1{_SFX}.json"
WALK_OUT = HERE / f"AA_ESTATE_WALK{_SFX}.json"
SPLITS_OUT = HERE / f"AA_SLEEVE_SPLITS_V1{_SFX}.json"
ORPHAN_OUT = HERE / f"AA_ORPHAN_TRIAGE_V1{_SFX}.json"

COSTS_V1 = REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
COSTS_V1_1 = (REPO
              / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json")
CACHE = (REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
         / "INTEG_W5_new_streams_cache.pkl")
SERVER = "FTMO-Server3"

#: Prior LOOK EVENTS at this family, charged into the multiplicity correction.
W_PILOT_LOOKS = 12          # W_MX_PILOT.json, the 12 live mx sleeves
X_ESTATE_LOOKS = 25         # X_ESTATE_WALK.json, sleeves that reached a verdict there


def _dt(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s)


def zero_carry_costs(path: Path):
    """The same cost artifact with every swap rate set to zero.

    THE COUNTERFACTUAL OD-3 TURNS ON, made measurable. `SURVIVOR_BOOK_V1.json` tiers the
    book UNCONDITIONAL / CARRY_CONDITIONAL by comparing each sleeve's break-even hold to
    an ASSUMED horizon, because no realised hold survived in any cache
    (`SESSION_N_W7_RECOST_RESULT.md` §8.1). The archive supplies the realised hold, so the
    tiering can be measured instead: run the identical walk with swap zeroed and read
    which verdicts move. A sleeve whose verdict is the same at zero carry and at measured
    carry is not carry-conditional whatever its break-even says; one that flips is, and
    the flip names the size of the exit repair it needs.

    This is a COUNTERFACTUAL, not a cost model — nobody trades at zero swap. It is
    labelled that way everywhere it appears.
    """
    from src.costs.model import BrokerTrueCosts

    doc = json.loads(path.read_text())
    for acct in doc.get("accounts", {}).values():
        for rec in (acct.get("instruments") or {}).values():
            sw = rec.get("swap") or {}
            sw["swap_long"] = 0.0
            sw["swap_short"] = 0.0
            spec = rec.get("spec") or {}
            spec["swap_long"] = 0.0
            spec["swap_short"] = 0.0
            rec["swap"] = sw
            rec["spec"] = spec
    doc["version"] = f"{doc.get('version')}+zero_carry_counterfactual"
    return BrokerTrueCosts(doc, source=path)


def load() -> dict:
    with gzip.open(IN, "rt") as fh:
        return json.load(fh)


def to_records(raw: dict) -> dict[str, list[TradeRecord]]:
    out: dict[str, list[TradeRecord]] = {}
    for sleeve, rows in raw["trades"].items():
        recs = []
        for r in rows:
            recs.append(TradeRecord(
                sleeve=r["sleeve"], symbol=r["symbol"],
                entry_utc=_dt(r["entry_utc"]), exit_utc=_dt(r["exit_utc"]),
                direction=int(r["direction"]),
                sl_distance_price=float(r["sl_distance_price"]),
                entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
                features={
                    "decision_day": r["decision_day"],
                    "timeframe": r["timeframe"],
                    "hold_hours": r["hold_hours"],
                    "symbol_canonical": r.get("symbol_canonical"),
                    "decision_bar_iso": r.get("decision_bar_iso"),
                    # the path, which is what makes the exit prescriptions possible
                    "mfe_r": r.get("mfe_r"),
                    "mae_r": r.get("mae_r"),
                    "bars_to_mfe": r.get("bars_to_mfe"),
                    "exit_reason": r.get("exit_reason"),
                    "exit_policy": r.get("exit_policy"),
                    "r_gross_plain": r.get("r_gross_plain"),
                },
            ))
        out[sleeve] = recs
    return out


#: THE SURFACE AA ACTUALLY RAN, for sleeves whose live surface has moved since.
#:
#: This driver is a DATED receipt and its allowlist rides into `GateSpec.sleeve_symbol_allowlist`,
#: which rides into `GateSpec.seal()`, which is the published `spec_sha256` of AA's gate runs. So
#: deriving the allowlist from the LIVE registry silently couples a sealed research artifact to the
#: live trading surface: arm one more symbol on one sleeve and AA's published seals stop
#: reproducing, with no code change anywhere near the gate. That happened on 2026-08-11, when
#: ETHUSD was added to `crypto` (owner-authorized, lane B7), and
#: `tests/research_infra/test_candidate_family.py::test_AA_published_spec_seals_reproduce_again`
#: caught it -- its own failure message already named this cause: *"or the sleeve registry moved"*.
#:
#: The fix is the doctrine `config/live_armed_set.json` -> `dated_artifact_basis` states for the
#: phase-20 receipts: a receipt is not rewritten to match today's config, because a receipt edited
#: to match today's config is no longer evidence. Pin what AA ran; a walk of a NEW surface is a NEW
#: run with a NEW seal, which is the correct semantics and not a thing to smuggle in through a
#: mutable default.
AA_DATED_SURFACE: dict[str, tuple[str, ...]] = {
    # crypto ran BTCUSD + DASHUSD; ETHUSD was added to the live surface 2026-08-11.
    "crypto": ("BTCUSD", "DASHUSD"),
}


def allowlist() -> dict:
    al = build_symbol_allowlist()
    from src.components.ultimate_book.admission import effective_registry
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    for name, spec in effective_registry(include_clean3=True).items():
        al.setdefault(name, tuple(sorted({resolve(s) for s in (spec.symbols or ())})))
    # OVERRIDE, not setdefault: `build_symbol_allowlist` already populated every live sleeve from
    # the live registry, so a setdefault here would never fire and the pin would be inert.
    for name, symbols in AA_DATED_SURFACE.items():
        if name in al:
            al[name] = tuple(sorted({resolve(s) for s in symbols}))
    return al


# =====================================================================================


def run_option(records, al, declared, option, costs, costs_label, ledger):
    base = OPTIONS[option]
    spec = base.with_(
        spec_id=f"{base.spec_id}_aa_estate_{costs_label}",
        sleeve_symbol_allowlist=al,
        declared_family_size=declared,
    )
    res = run_gate(records, spec, costs=costs, diagnose=True, server=SERVER)
    rows = []
    for s, v in sorted(res.verdicts.items()):
        diag = v.diagnostics or {}
        rows.append({
            "sleeve": s, "verdict": v.verdict.value, "n_trades": v.n_trades,
            "primary_prescription": diag.get("primary_prescription"),
            "primary_component": diag.get("primary_component"),
            "pooled_oos_mean_r": v.pooled_oos_mean_r,
            "oos_mean_r_per_trade": v.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "lifetime_mean_r": v.gates.get("lifetime", {}).get(
                "mean_r_net_per_trade_all_folds"),
            "mean_gross_r": (diag.get("cost_decomposition") or {}).get("mean_gross_r"),
            "cost_pct_of_abs_gross": (diag.get("cost_decomposition") or {}).get(
                "cost_pct_of_abs_gross"),
            "largest_cost_term": (diag.get("cost_decomposition") or {}).get("largest_term"),
            "median_hold_hours": (diag.get("holding") or {}).get("median_hours"),
            "mean_mfe_r": (diag.get("excursion") or {}).get("mean_mfe_r"),
            "capture_ratio": (diag.get("excursion") or {}).get("capture_ratio_pooled"),
            "p_raw": v.p_raw, "q_value": v.q_value,
            "oos_positive_fold_frac": v.gates.get("stability", {}).get(
                "oos_positive_fold_frac"),
            "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
            "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
            "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
            "fidelity_recall": v.fidelity.get("live_recall"),
            "repair_paths": diag.get("repair_paths"),
        })
        ledger.record(
            mechanism="walkforward_gate", sleeve=s,
            variant={"option": option, "costs": costs_label, "spec": spec.spec_id},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(v.verdict.value, "evaluated"),
            metric=v.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
            note=f"AA estate walk, prescription {diag.get('primary_prescription')}",
        )
    return spec, res, rows


def print_table(option, costs_label, rows, res):
    print(f"\n--- {option} @ {costs_label} ---")
    print(f"{'sleeve':42s} {'verdict':14s} {'n':>6s} {'R/day':>9s} {'gross/t':>8s} "
          f"{'cost%':>7s} {'hold_h':>8s} {'MFE':>6s} {'prescription':22s}")
    for r in rows:
        f = lambda x, p=5: ("     -" if x is None else f"{x:.{p}f}")  # noqa: E731
        pct = "    -" if r["cost_pct_of_abs_gross"] is None else f"{r['cost_pct_of_abs_gross']:.1f}"
        hh = "     -" if r["median_hold_hours"] is None else f"{r['median_hold_hours']:.2f}"
        mfe = "    -" if r["mean_mfe_r"] is None else f"{r['mean_mfe_r']:.2f}"
        print(f"{r['sleeve']:42s} {r['verdict']:14s} {r['n_trades']:6d} "
              f"{f(r['pooled_oos_mean_r']):>9s} {f(r['mean_gross_r'],4):>8s} {pct:>7s} "
              f"{hh:>8s} {mfe:>6s} {str(r['primary_prescription']):22s}")
    print(f"  ADMIT({len(res.admitted)}): {res.admitted}")


# =====================================================================================
# cost-true per-sleeve splits — the §4.2 input


def sleeve_splits(records, spec, costs) -> dict:
    out: dict = {}
    for sleeve, recs in sorted(records.items()):
        if not recs:
            out[sleeve] = {"available": False, "reason": "no generated trades"}
            continue
        priced, cov = price_trades(recs, spec, costs=costs)
        daily_map, counts = build_daily_panel(priced, spec)
        daily = daily_map.get(sleeve, {})
        if not daily:
            out[sleeve] = {"available": False,
                           "reason": "no priced trade produced a daily observation",
                           "coverage": cov[sleeve].as_dict() if sleeve in cov else {}}
            continue
        folds = build_fold_calendar(spec, min(daily), max(daily))
        slices = assign_folds(priced, daily, folds, spec)
        # cost components per day, so the actuator can see WHICH term moved
        comp: dict[str, dict[str, float]] = {}
        for p in priced:
            if p.status != "priced" or not p.components:
                continue
            k = p.trade.day(spec.day_key).isoformat()
            d = comp.setdefault(k, {"commission_r": 0.0, "swap_r": 0.0, "spread_r": 0.0,
                                    "slippage_r": 0.0, "n": 0.0})
            for t in ("commission_r", "swap_r", "spread_r", "slippage_r"):
                d[t] += float(p.components.get(t, 0.0))
            d["n"] += 1.0
        out[sleeve] = {
            "available": True,
            "cost_basis": "broker_true_v1_1",
            "n_trades": len(recs),
            "coverage": cov[sleeve].as_dict() if sleeve in cov else {},
            "daily_net_r": {d.isoformat(): round(v, 8) for d, v in sorted(daily.items())},
            "daily_trade_counts": {d.isoformat(): n
                                   for d, n in sorted(counts.get(sleeve, {}).items())},
            "daily_cost_components": {k: {t: round(v, 8) for t, v in sorted(v2.items())}
                                      for k, v2 in sorted(comp.items())},
            "folds": [
                {"fold_id": s.fold.fold_id, "status": s.status,
                 "oos_start": s.fold.oos_start.isoformat(),
                 "oos_end": s.fold.oos_end.isoformat(),
                 "is_initial_train": s.fold.is_initial_train,
                 "embargo_days": s.embargo_days,
                 "n_train_trades": s.n_train_trades, "n_test_trades": s.n_test_trades,
                 "train_days": [d.isoformat() for d in s.train_days],
                 "test_days": [d.isoformat() for d in s.test_days]}
                for s in slices
            ],
        }
    return out


# =====================================================================================
# orphan triage — the statistical half, on the cached stream, stamped legacy-cost


def orphan_triage(spec: GateSpec) -> dict:
    if not CACHE.is_file():
        return {"available": False, "reason": f"{CACHE} absent"}
    with CACHE.open("rb") as fh:
        cache = pickle.load(fh)
    out: dict = {
        "schema": "gtos.walkforward.orphan_triage.v1",
        "cost_basis": "LEGACY — these rows carry {sleeve, sym, date, year, R} and nothing "
                      "else. No stop distance and no exit index survive, so `cost_r` "
                      "cannot be charged and this is NOT broker truth. It answers one "
                      "question only: is there a persistent edge in the cached stream "
                      "worth building the missing generator for?",
        "why_they_cannot_be_re-walked": (
            "`leadlag_core`, `subh4_ll_fx` and `session_leadlag_genuine` have no generator "
            "module in src/components/ultimate_book/sleeves/ — verified by directory "
            "listing 2026-07-29. Regeneration at broker truth is blocked on WRITING one, "
            "not on data."
        ),
        "sleeves": {},
    }
    for sleeve in ("leadlag_core", "subh4_ll_fx", "vp_euidx_pocgrav", "xlayer_veto_gate"):
        rows = cache.get(sleeve)
        if not rows:
            out["sleeves"][sleeve] = {"available": False,
                                      "reason": "absent from the cache entirely"}
            continue
        by_day: dict[dt.date, list[float]] = {}
        by_sym: dict[str, list[float]] = {}
        for r in rows:
            by_day.setdefault(r["date"], []).append(float(r["R"]))
            by_sym.setdefault(r["sym"], []).append(float(r["R"]))
        daily = [statistics.fmean(v) for _d, v in sorted(by_day.items())]
        days = sorted(by_day)
        block = block_length_auto(daily, min_blocks=spec.min_blocks)
        null = combined_null_p(daily, block=block, mode="both_conservative",
                               n_boot=4000, n_perm=4000, seed=spec.seed)
        # calendar halves, so the split is mechanical and outcome-independent
        mid = days[len(days) // 2]
        first = [statistics.fmean(by_day[d]) for d in days if d < mid]
        second = [statistics.fmean(by_day[d]) for d in days if d >= mid]
        yr: dict[int, list[float]] = {}
        for r in rows:
            yr.setdefault(int(r["year"]), []).append(float(r["R"]))
        out["sleeves"][sleeve] = {
            "available": True,
            "n_trades": len(rows),
            "n_days": len(days),
            "span": [days[0].isoformat(), days[-1].isoformat()],
            "mean_r_per_trade": round(statistics.fmean([float(r["R"]) for r in rows]), 6),
            "sum_r": round(math.fsum(float(r["R"]) for r in rows), 3),
            "mean_r_per_day": round(statistics.fmean(daily), 6),
            "day_block_null": {**null, "block_days": block},
            "calendar_halves": {
                "split_at": mid.isoformat(),
                "first_half_mean_r_day": round(statistics.fmean(first), 6) if first else None,
                "second_half_mean_r_day": (round(statistics.fmean(second), 6)
                                           if second else None),
                "both_positive": bool(first and second
                                      and statistics.fmean(first) > 0
                                      and statistics.fmean(second) > 0),
            },
            "by_year_mean_r": {str(k): round(statistics.fmean(v), 5)
                               for k, v in sorted(yr.items())},
            "by_symbol": sorted(
                ({"symbol": s, "n": len(v), "mean_r": round(statistics.fmean(v), 5),
                  "sum_r": round(math.fsum(v), 3)} for s, v in by_sym.items()),
                key=lambda d: -d["sum_r"]),
            "prescription": (
                "BUILD_GENERATOR" if statistics.fmean(daily) > 0 and null["p_value"] < 0.20
                else "BUILD_GENERATOR_LOW_PRIORITY"
            ),
        }
    return out


# =====================================================================================


def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AA")
    raw = load()
    records = to_records(raw)
    n_tr = sum(len(v) for v in records.values())
    print(f"loaded {IN.name}: {n_tr} trades over "
          f"{sum(1 for v in records.values() if v)} non-empty sleeves "
          f"({len(records)} in the family)")
    al = allowlist()
    judged = sorted(records)
    declared = len(judged) + W_PILOT_LOOKS + X_ESTATE_LOOKS
    print(f"family: {len(judged)} judged here + {W_PILOT_LOOKS} W looks + "
          f"{X_ESTATE_LOOKS} X looks = declared_family_size {declared} LOOK EVENTS")

    costs_v1 = load_broker_true_costs(COSTS_V1)
    costs_v11 = load_broker_true_costs(COSTS_V1_1)
    costs_zero = zero_carry_costs(COSTS_V1_1)

    runs: dict = {}
    queues: dict = {}
    for costs_label, costs in (("v1_1", costs_v11), ("v1", costs_v1),
                               ("v1_1_zero_carry", costs_zero)):
        for option in (("B_balanced",) if costs_label == "v1_1_zero_carry"
                       else ("B_balanced", "A_strict", "C_exploratory")):
            spec, res, rows = run_option(records, al, declared, option, costs,
                                         costs_label, ledger)
            print_table(option, costs_label, rows, res)
            runs[f"{option}|{costs_label}"] = {
                "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
                "costs_artifact": str(COSTS_V1 if costs_label == "v1" else COSTS_V1_1),
                "costs_note": ("COUNTERFACTUAL: every swap rate forced to zero. Nobody "
                               "trades at zero swap; this exists only to separate a "
                               "carry problem from an edge problem."
                               if costs_label == "v1_1_zero_carry" else ""),
                "admitted": res.admitted, "rejected": res.rejected,
                "not_evaluable": res.not_evaluable,
                "family": {k: v for k, v in res.family.items() if k != "n_trials_basis"},
                "rows": rows,
            }
            if costs_label == "v1_1":
                queues[option] = res.repair_queue(
                    server=SERVER, run_label=f"AA estate walk {option} @ {costs_label}",
                    extra={"cost_artifact": str(COSTS_V1_1),
                           "fidelity_policy": raw.get("fidelity_policy", {}).get("mode")})
            if option == "B_balanced" and costs_label == "v1_1":
                b_spec, b_res = spec, res

    # ---- the cost repair, measured ------------------------------------------------------
    ab = {}
    for s in judged:
        a = next((r for r in runs["B_balanced|v1"]["rows"] if r["sleeve"] == s), None)
        b = next((r for r in runs["B_balanced|v1_1"]["rows"] if r["sleeve"] == s), None)
        if not a or not b:
            continue
        if a["verdict"] != b["verdict"] or (
            a["pooled_oos_mean_r"] is not None and b["pooled_oos_mean_r"] is not None
            and abs(a["pooled_oos_mean_r"] - b["pooled_oos_mean_r"]) > 1e-12
        ):
            ab[s] = {
                "verdict_v1": a["verdict"], "verdict_v1_1": b["verdict"],
                "pooled_v1": a["pooled_oos_mean_r"], "pooled_v1_1": b["pooled_oos_mean_r"],
                "delta_pooled": (None if a["pooled_oos_mean_r"] is None
                                 or b["pooled_oos_mean_r"] is None
                                 else round(b["pooled_oos_mean_r"] - a["pooled_oos_mean_r"], 8)),
                "gross_v1_1": b["mean_gross_r"],
                "cost_pct_v1": a["cost_pct_of_abs_gross"],
                "cost_pct_v1_1": b["cost_pct_of_abs_gross"],
            }
    # ---- THE CARRY TABLE: is it a carry problem or an edge problem? ---------------------
    # `SURVIVOR_BOOK_V1.json` tiers the book by comparing an assumed horizon to a
    # break-even hold, because no realised hold survived in any cache. The archive has the
    # realised hold, so the tier is measurable: same walk, swap forced to zero, read which
    # verdicts move.
    carry = {}
    for s in judged:
        m = next((r for r in runs["B_balanced|v1_1"]["rows"] if r["sleeve"] == s), None)
        z = next((r for r in runs["B_balanced|v1_1_zero_carry"]["rows"]
                  if r["sleeve"] == s), None)
        if not m or not z:
            continue
        dg = (b_res.verdicts[s].diagnostics or {})
        cd = dg.get("cost_decomposition") or {}
        hold = dg.get("holding") or {}
        nights = cd.get("swap_nights") or {}
        swap_term = ((cd.get("terms") or {}).get("swap_r") or {})
        moved = m["verdict"] != z["verdict"]
        carry[s] = {
            "verdict_measured_carry": m["verdict"],
            "verdict_zero_carry": z["verdict"],
            "carry_decides_the_verdict": moved,
            "pooled_measured": m["pooled_oos_mean_r"],
            "pooled_zero_carry": z["pooled_oos_mean_r"],
            "delta_from_carry": (None if m["pooled_oos_mean_r"] is None
                                 or z["pooled_oos_mean_r"] is None
                                 else round(z["pooled_oos_mean_r"] - m["pooled_oos_mean_r"], 8)),
            "median_hold_hours": hold.get("median_hours"),
            "p90_hold_hours": hold.get("p90_hours"),
            "frac_over_24h": hold.get("frac_over_24h"),
            "swap_nights_mean": nights.get("mean"),
            "swap_nights_median": nights.get("median"),
            "frac_trades_zero_nights": nights.get("frac_zero"),
            "swap_r_mean": swap_term.get("mean_r"),
            "swap_share_of_cost": swap_term.get("share_of_cost"),
            "measured_tier": (
                "CARRY_DECIDES" if moved else
                ("CARRY_IMMATERIAL" if (nights.get("mean") or 0) < 0.05 else
                 "CARRY_PRICED_BUT_NOT_DECISIVE")
            ),
        }
    n_moved = sum(1 for v in carry.values() if v["carry_decides_the_verdict"])
    print(f"\ncarry table: {n_moved} of {len(carry)} sleeves change verdict at zero carry")
    for s, v in sorted(carry.items(), key=lambda kv: -(kv[1]["swap_r_mean"] or 0)):
        if v["swap_r_mean"] is None:
            continue
        print(f"  {s:42s} hold_med={str(v['median_hold_hours']):>8s}h "
              f"nights_mean={str(v['swap_nights_mean']):>7s} "
              f"swap={v['swap_r_mean']:+.5f}R ({v['swap_share_of_cost']}) "
              f"{v['verdict_measured_carry']:>13s} -> {v['verdict_zero_carry']:<13s} "
              f"[{v['measured_tier']}]")

    print(f"\ncost-repair A/B (V1 -> V1_1): {len(ab)} sleeves move")
    for s, d in sorted(ab.items()):
        print(f"  {s:42s} {d['verdict_v1']:14s} -> {d['verdict_v1_1']:14s} "
              f"dR/day={d['delta_pooled']}")

    # ---- splits and orphans ---------------------------------------------------------------
    splits = sleeve_splits(records, b_spec, costs_v11)
    SPLITS_OUT.write_text(json.dumps({
        "schema": "gtos.walkforward.sleeve_splits.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "spec_sha256": b_spec.seal(),
        "cost_artifact": str(COSTS_V1_1.relative_to(REPO)),
        "consumer": ("FOURTH_REVIEW §4.2 item 1 — learning_actuator.py's backtest half "
                     "currently reads legacy-cost CP4/CP5 splits. These are cost-true."),
        "cost_look_ahead": {
            "measured_window": ["2026-06-18", "2026-07-24"],
            "applied_to": "every trade in the panel regardless of era",
            "direction": "spreads compressed; pre-2026 trades are UNDER-costed",
        },
        "sleeves": splits,
    }, indent=1, default=str))
    print(f"wrote {SPLITS_OUT.relative_to(REPO)} "
          f"({sum(1 for v in splits.values() if v.get('available'))} sleeves with a series)")

    orphans = orphan_triage(b_spec)
    ORPHAN_OUT.write_text(json.dumps(orphans, indent=1, default=str))
    for s, v in (orphans.get("sleeves") or {}).items():
        if v.get("available"):
            print(f"  ORPHAN {s:26s} n={v['n_trades']:5d} sum={v['sum_r']:+9.1f} R "
                  f"day-mean={v['mean_r_per_day']:+.5f} p={v['day_block_null']['p_value']:.4f} "
                  f"halves_both_positive={v['calendar_halves']['both_positive']} "
                  f"-> {v['prescription']}")
        else:
            print(f"  ORPHAN {s:26s} {v['reason']}")
        ledger.record(mechanism="orphan_triage", sleeve=s,
                      variant={"basis": "cached_daily_r_legacy_cost"},
                      window="cache_span", outcome="evaluated",
                      metric=v.get("mean_r_per_day"), metric_name="mean_r_per_day")

    # ---- the queue ------------------------------------------------------------------------
    queue = queues["B_balanced"]
    queue["also_at"] = {k: {"n_rows": len(v["rows"]),
                            "by_prescription": v["summary"]["by_prescription"]}
                        for k, v in queues.items() if k != "B_balanced"}
    Q_OUT.write_text(json.dumps(queue, indent=1, default=str))
    print(f"\nwrote {Q_OUT.relative_to(REPO)}: {queue['summary']['n_rows']} rows")
    print("  by prescription:", json.dumps(queue["summary"]["by_prescription"]))

    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    print(f"  trial ledger: {nt['n_prospective_look_events']} look events; "
          f"DSR n_trials would be {nt['n_trials']} (basis {nt['basis']})")

    out = {
        "schema": "gtos.walkforward.estate_walk.v2",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "source": str(IN.relative_to(REPO)),
        "source_generated_by": raw.get("generated_by"),
        "family": {
            "judged_here": judged,
            "declared_family_size_look_events": declared,
            "composition": {"judged_here": len(judged), "w_pilot_looks": W_PILOT_LOOKS,
                            "x_estate_looks": X_ESTATE_LOOKS},
        },
        "fidelity_policy": raw.get("fidelity_policy", {}).get("mode"),
        "fidelity_below_floor_generated_anyway": raw.get(
            "fidelity_below_floor_generated_anyway"),
        "trail_repair": raw.get("trail_repair"),
        "entry_convention_gap": raw.get("entry_convention_gap"),
        "runs": runs,
        "carry_table": {
            "question": ("Is this sleeve's failure a CARRY problem or an EDGE problem? "
                         "Measured, not inferred from an assumed horizon."),
            "method": ("identical B_balanced walk at BROKER_TRUE_COSTS_V1_1 with every "
                       "swap rate forced to zero. A COUNTERFACTUAL — nobody trades at "
                       "zero swap — whose only job is to separate the two failures."),
            "supersedes": ("SURVIVOR_BOOK_V1.json's UNCONDITIONAL / CARRY_CONDITIONAL "
                           "tiers, which compare a break-even hold to an ASSUMED horizon "
                           "because no realised hold survived any cache "
                           "(SESSION_N_W7_RECOST_RESULT.md §8.1). These tiers use the "
                           "realised hold off the simulated path."),
            "n_sleeves_carry_decides": sum(
                1 for v in carry.values() if v["carry_decides_the_verdict"]),
            "sleeves": carry,
        },
        "cost_repair_ab": ab,
        "trial_ledger": nt,
        "cost_look_ahead": {
            "measured_window": ["2026-06-18", "2026-07-24"],
            "applied_to": "every trade in a 2000-2026 panel",
            "direction": "spreads compressed; pre-2026 trades are UNDER-costed, so every "
                         "net number here is optimistic by an unmeasured amount",
            "repair": "FOURTH_REVIEW §4.6 banded spread model (Session AG)",
        },
    }
    WALK_OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {WALK_OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
