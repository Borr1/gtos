"""Session AH item 1, second half -- judge the four entry arms on one common population.

    python3 .../ah_entry_gate.py

THE POPULATION IS INTERSECTED, AND THAT IS THE WHOLE COMPARISON
---------------------------------------------------------------
Arm C loses 4,284 decision bars structurally: a Friday D1 bar closes Saturday 00:00 and its
next H4 close is Monday 04:00, 52 hours later, which is a different trade rather than a later
fill (`MAX_SHIFT_HOURS`). Most of those bars are `engine_reachable == False` anyway -- every
Friday is a pre-gap bar (AF §1.1) -- but "most" is not "all", and comparing 17,888 trades
against 16,338 would let a population change masquerade as an entry effect.

So every arm is judged on the **intersection**: decision bars where all four arms produced a
trade AND the bar is engine-reachable. The counts are then identical by construction, and the
per-arm difference is the entry instant and nothing else.

COST IS CHARGED WITH THE REPAIRED COMPOSITION
----------------------------------------------
This is the point of doing item 2 first. Under `v1_multiplicative` the FX cohort's hour-00
fills are charged an era x hour product of up to 880x and the modelled saving from moving the
entry is 80-81 % of a cost that is itself an unvalidated extrapolation -- which is exactly why
AF refused to publish it as a gain. Both compositions are run so the reader can see how much
of the "repair" was the defect.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.bar_provider import TF_D1  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import ERA_HOUR_EXPONENT  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

TRADES = HERE / "AH_ENTRY_SHIFT_TRADES.json.gz"
OUT = HERE / "ENTRY_HOUR_FRONTIER_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
VERDICT_BAND = "mid"
ARMS = ("A_d1close_d1exit", "B_d1close_h4exit", "C_h4next_h4exit", "D_h4second_h4exit")

#: AF's own bill (246 member cells + 30 families) plus this session's grid (4 arms x
#: (42 members + 3 families)). The cumulative reading, because a repair evaluated on trades
#: AF already swept does not get to forget AF's looks.
AF_LOOKS = 276
AH_LOOKS = 4 * (42 + 3)


def load() -> dict:
    with gzip.open(TRADES, "rt") as fh:
        return json.load(fh)


def intersect(art: dict) -> tuple[dict[str, list[dict]], dict]:
    """Rows keyed by arm, restricted to decision bars present and reachable in ALL arms."""
    by_key: dict[tuple[str, str], dict[str, dict]] = collections.defaultdict(dict)
    for r in art["trades"]:
        by_key[(r["member"], r["decision_bar_iso"])][r["arm"]] = r
    keep = {k: v for k, v in by_key.items()
            if len(v) == len(ARMS)
            and all(not v[a].get("dropped") for a in ARMS)
            and v["A_d1close_d1exit"]["engine_reachable"]}
    out = {a: [v[a] for v in keep.values()] for a in ARMS}
    stats = {
        "n_decision_bars_all_arms": len(keep),
        "n_decision_bars_seen": len(by_key),
        "excluded_not_reachable": sum(
            1 for v in by_key.values()
            if len(v) == len(ARMS) and all(not v[a].get("dropped") for a in ARMS)
            and not v["A_d1close_d1exit"]["engine_reachable"]),
        "excluded_arm_missing_or_dropped": sum(
            1 for v in by_key.values()
            if len(v) != len(ARMS) or any(v[a].get("dropped") for a in ARMS)),
        "counts_are_equal_across_arms": len({len(v) for v in out.values()}) == 1,
    }
    return out, stats


def to_records(rows: list[dict], sleeve: str | None = None) -> list[TradeRecord]:
    return [
        TradeRecord(
            sleeve=(sleeve or r["member"]), symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"mfe_r": r["mfe_r"], "mae_r": r["mae_r"],
                      "hold_hours": r["hold_hours"], "exit_reason": r["exit_reason"],
                      "entry_shift_hours": r["entry_shift_hours"]})
        for r in rows]


def cost_decomposition(rows: list[dict], costs, composition: str,
                       sample: int = 1) -> dict:
    """Mean per-trade cost in R, split by component, on the same rows the gate scored.

    `run_gate` charges the same layer but publishes only the total; the split is what answers
    "does cost or gross dominate", which is the question item 1 exists to settle.
    """
    acc = collections.defaultdict(list)
    unpriced = collections.Counter()
    for i, r in enumerate(rows):
        if sample > 1 and i % sample:
            continue
        try:
            b = cost_r(r["symbol"], "FTMO", r["hold_hours"],
                       sl_distance_price=r["sl_distance_price"],
                       entry_price=r["entry_price"],
                       entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                       spread_band=VERDICT_BAND, spread_composition=composition,
                       costs=costs)
        except Exception as e:                                  # noqa: BLE001
            unpriced[type(e).__name__ + ": " + str(e)[:70]] += 1
            continue
        acc["total_r"].append(b.total_r.value)
        acc["spread_r"].append(b.spread_r.value)
        acc["commission_r"].append(b.commission_r.value)
        acc["swap_r"].append(b.swap_r.value)
        acc["slippage_r"].append(b.slippage_r.value)
    return {"n_priced": len(acc["total_r"]), "unpriced": dict(unpriced.most_common(4)),
            "mean_r": {k: statistics.mean(v) for k, v in acc.items() if v},
            "median_r": {k: statistics.median(v) for k, v in acc.items() if v}}


def row_of(sleeve: str, v) -> dict:
    g = v.gates
    return {"sleeve": sleeve, "verdict": v.verdict.value, "n_trades": v.n_trades,
            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
            "q_value": v.q_value,
            "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
            "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
            "lifetime_mean_r_per_trade": (v.telemetry.get("lifetime", {})
                                          .get("mean_r_net_per_trade_all_folds")),
            "first_reason": (v.reasons[0][:300] if v.reasons else None)}


def do_gate() -> dict:
    t0 = dt.datetime.now(dt.timezone.utc)
    art = load()
    arms, pop = intersect(art)
    print(f"intersected population: {pop['n_decision_bars_all_arms']} decision bars "
          f"(equal across arms: {pop['counts_are_equal_across_arms']}); "
          f"{pop['excluded_not_reachable']} unreachable, "
          f"{pop['excluded_arm_missing_or_dropped']} missing/dropped in some arm")

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    costs = load_broker_true_costs(COSTS)
    cost_sha = hashlib.sha256(COSTS.read_bytes()).hexdigest()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AH")
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    declared = AF_LOOKS + AH_LOOKS
    print(f"declared_family_size {declared} = AF {AF_LOOKS} + AH {AH_LOOKS}; "
          f"measured n_trials {nt['n_trials']}")

    members = sorted({r["member"] for r in arms["A_d1close_d1exit"]})
    # `mxf_<mech>_<sym>_<tf>` -> the mechanism, taken from the member name rather than
    # re-derived, so this cannot disagree with what was generated.
    fam_of = {}
    for m in members:
        body = m[len("mxf_"):]
        mech = body.rsplit("_", 2)[0]
        fam_of[m] = f"fam_{mech}_fx_d1"
    families = sorted(set(fam_of.values()))
    print(f"{len(members)} members, {len(families)} families: {families}")

    allow_member = {m: (next(r["symbol"] for r in arms["A_d1close_d1exit"]
                            if r["member"] == m),) for m in members}
    allow_family = {f: tuple(sorted({r["symbol"] for r in arms["A_d1close_d1exit"]
                                     if fam_of[r["member"]] == f})) for f in families}

    # The grid members, rebuilt so `fidelity_scope` can register them. The gate refuses any
    # sleeve with no fidelity record (`gate.py:432-455`) and every one of these 42 cells is a
    # surface expansion that deliberately sits in no registry -- without this every arm comes
    # back NOT_EVALUABLE on `port_fidelity_unmeasured`, which is what the first run of this
    # script did. `expanded_surface` is for generating; this is for scoring.
    from ah_entry_shift import cohort_members  # noqa: PLC0415

    supports = getattr(res, "supports", None)
    grid_members = [m for m in cohort_members(res, supports).members if m.member in fam_of]
    assert len(grid_members) == len(members), (len(grid_members), len(members))

    runs: dict[str, dict] = {}
    decomp: dict[str, dict] = {}
    for comp in ("v2_damped", "v1_multiplicative"):
        for arm in ARMS:
            rows = arms[arm]
            by_member = collections.defaultdict(list)
            for r in rows:
                by_member[r["member"]].append(r)
            recs_member = {m: to_records(v) for m, v in by_member.items()}
            pooled = {}
            for f in families:
                ms = [m for m in members if fam_of[m] == f]
                pooled[f] = [t for m in ms for t in to_records(by_member[m], sleeve=f)]
            for scope, trades, allow in (("member", recs_member, allow_member),
                                         ("family", pooled, allow_family)):
                spec = OPTIONS["C_exploratory"].with_(
                    spec_id=f"C_exploratory_ah_entry_{arm}_{scope}_{comp}",
                    spread_band=VERDICT_BAND, spread_composition=comp,
                    cost_artifact_sha256=cost_sha, declared_family_size=declared,
                    n_trials=int(nt["n_trials"]),
                    n_trials_basis=(f"MEASURED from {DEFAULT_TRIAL_LEDGER} -- "
                                    f"{nt.get('basis')}"),
                    sleeve_symbol_allowlist=allow)
                with fam.fidelity_scope(grid_members):
                    r = run_gate(trades, spec, costs=costs, server=SERVER)
                key = f"{comp}|{arm}|{scope}"
                runs[key] = {"composition": comp, "arm": arm, "scope": scope,
                             "spec_sha256": spec.seal(),
                             "admitted": r.admitted, "rejected_n": len(r.rejected),
                             "not_evaluable_n": len(r.not_evaluable),
                             "rows": {s: row_of(s, v) for s, v in sorted(r.verdicts.items())}}
                print(f"  {key:46s} ADMIT {len(r.admitted):2d} REJECT {len(r.rejected):3d} "
                      f"N/E {len(r.not_evaluable):2d}", flush=True)
            # The cost split, on a 1-in-5 sample: 16k trades x 8 arm/composition cells is
            # 130k `cost_r` calls and the mean of 3,200 is already tight to 3 decimals.
            decomp[f"{comp}|{arm}"] = cost_decomposition(rows, costs, comp, sample=5)

    # per-member before/after, the deliverable's core table
    per_member = {}
    for m in members:
        rec = {"member": m, "symbol": allow_member[m][0]}
        for arm in ARMS:
            rr = [r for r in arms[arm] if r["member"] == m]
            rec[arm] = {
                "n": len(rr),
                "mean_r_gross": statistics.mean(r["r_gross"] for r in rr) if rr else None,
                "median_hold_hours": statistics.median(r["hold_hours"] for r in rr) if rr else None,
                "mean_mfe_r": statistics.mean(r["mfe_r"] for r in rr) if rr else None,
            }
            for comp in ("v2_damped", "v1_multiplicative"):
                row = runs[f"{comp}|{arm}|member"]["rows"].get(m)
                rec[arm][f"pooled_oos_mean_r_{comp}"] = (row or {}).get("pooled_oos_mean_r")
                rec[arm][f"verdict_{comp}"] = (row or {}).get("verdict")
                rec[arm][f"p_raw_{comp}"] = (row or {}).get("p_raw")
        rr_b = [r for r in arms["B_d1close_h4exit"] if r["member"] == m]
        rr_c = [r for r in arms["C_h4next_h4exit"] if r["member"] == m]
        rec["entry_shift_delta_gross_r"] = (
            statistics.mean(r["r_gross"] for r in rr_c)
            - statistics.mean(r["r_gross"] for r in rr_b)) if rr_b and rr_c else None
        rec["mean_pre_entry_drift_r"] = statistics.mean(
            (r["entry_slip_price"] * r["direction"]) / r["sl_distance_price"]
            for r in rr_c) if rr_c else None
        per_member[m] = rec

    for m, rec in sorted(per_member.items()):
        for arm in ARMS:
            ledger.record(
                mechanism=m[len("mxf_"):].rsplit("_", 2)[0], sleeve=m,
                variant={"entry_arm": arm, "exit_resolution":
                         ("D1" if arm == "A_d1close_d1exit" else "H4"),
                         "spread_composition": "v2_damped",
                         "declared_family_size": declared, "verdict_band": VERDICT_BAND},
                window="2000-03..2026-07 (whole FX archive)",
                outcome=("negative" if (rec[arm]["mean_r_gross"] or 0) < 0 else "positive"),
                metric=rec[arm].get("pooled_oos_mean_r_v2_damped"),
                metric_name="pooled_oos_mean_r",
                spec_sha256=runs[f"v2_damped|{arm}|member"]["spec_sha256"],
                note="AH entry-hour frontier: D1-close vs first/second H4 close")

    out = {
        "schema": "gtos.ah.entry_hour_frontier.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": t0.isoformat(),
        "trades_artifact": str(TRADES.relative_to(REPO)),
        "trades_generated_utc": art.get("generated_utc"),
        "cost_artifact": {"path": str(COSTS.relative_to(REPO)), "sha256": cost_sha},
        "verdict_band": VERDICT_BAND,
        "era_hour_exponent": ERA_HOUR_EXPONENT,
        "arms": {
            "A_d1close_d1exit": "entry at the D1 close (broker 00:00); exit on D1 bars, maxbars 80. AF's arm exactly.",
            "B_d1close_h4exit": "same entry instant; exit on H4 bars, maxbars 480. The resolution CONTROL.",
            "C_h4next_h4exit": "entry at the first H4 close after the decision (broker 04:00); exit on H4 bars.",
            "D_h4second_h4exit": "entry at the second H4 close (broker 08:00). Sensitivity, not a candidate.",
        },
        "population": pop,
        "parity_vs_af": art["parity_vs_af"],
        "decision_broker_hour_histogram": art["decision_broker_hour_histogram"],
        "entry_broker_hour_histogram": art["entry_broker_hour_histogram"],
        "arm_drops": art["arm_drops"],
        "multiplicity": {"declared_family_size": declared, "af_looks": AF_LOOKS,
                         "ah_looks": AH_LOOKS, "n_trials": int(nt["n_trials"]),
                         "n_trials_basis": nt.get("basis")},
        "aggregate": {
            arm: {"n": len(arms[arm]),
                  "mean_r_gross": statistics.mean(r["r_gross"] for r in arms[arm]),
                  "sum_r_gross": sum(r["r_gross"] for r in arms[arm]),
                  "median_hold_hours": statistics.median(r["hold_hours"] for r in arms[arm]),
                  "mean_mfe_r": statistics.mean(r["mfe_r"] for r in arms[arm]),
                  "exit_reasons": dict(collections.Counter(r["exit_reason"]
                                                           for r in arms[arm])),
                  "mean_pre_entry_drift_r": (statistics.mean(
                      (r["entry_slip_price"] * r["direction"]) / r["sl_distance_price"]
                      for r in arms[arm]) if arm != "A_d1close_d1exit" else 0.0)}
            for arm in ARMS},
        "cost_decomposition": decomp,
        "per_member": per_member,
        "runs": runs,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    return out


if __name__ == "__main__":
    do_gate()
