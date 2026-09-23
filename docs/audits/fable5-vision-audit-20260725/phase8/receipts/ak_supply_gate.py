"""Gate the four unreachable sleeves, and close AD's four-sleeve exit-frontier gap.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_supply_gate.py
    AK_STAGE=gate|sweep|gap python3 .../ak_supply_gate.py       # one stage at a time

TWO JOBS, ONE HARNESS
---------------------
1. **The four new sleeves** (`vol_squeeze`, `ny_index_momentum`, `structural_retest`,
   `session_leadlag_genuine`) go through `run_gate(..., diagnose=True)` inside AA's own
   32-sleeve family, at AA's `declared_family_size=69`, so every verdict and q-value is directly
   comparable to `AA_ESTATE_WALK.json` and `EXIT_FRONTIER_V1.json`. Then AD's exit families are
   swept over them wherever the diagnosis says the exit is the blocker.

2. **The four sleeves AD did not reach.** AD swept 25 of the 29 sleeves AA generated. Measured
   here by set difference against `AA_ESTATE_TRADES.json.gz`, the four with trades and no exit
   frontier anywhere are `asia_pdl_fade` (n=2,827 — the largest first-of-day sleeve, and AA
   measured it gross-positive at +0.196 R/trade), `orb_crypto_london` (858),
   `liq_asia_up_low_metal` (157) and **`sub_xvol_pullback` (88), which is ARMED and trading real
   money today**. AD's `WORK_LIST` is its own prompt's value order and simply did not name them;
   this is a scope gap, not an exclusion. They are swept here with AD's machinery, IMPORTED
   rather than reimplemented, so any difference between the two frontiers is a difference in the
   sleeve and not in the instrument.

WHY THE FAMILY SIZE IS REPORTED THREE WAYS AND NOT CHOSEN
----------------------------------------------------------
`GateSpec.declared_family_size` is on the caller's honour with no principled stopping rule, and
AF §11 routed the choice to Borhen as *"the only thing standing between the estate's best new-edge
candidate and a verdict"*. This session does not pick it. Every verdict is computed at AA's 69 —
which is what makes it an A/B against AA and AD — and each sleeve additionally carries `q` at
AF's 276 and at the trial ledger's measured count, so the owner decision can be read off the
artifact instead of re-run.

THE ONE THING THAT IS NOT AD's HARNESS
---------------------------------------
The four new sleeves have no `sleeve_symbol_allowlist` entry, because they are in no registry.
The gate then records `symbol_consistency` as *not checked* and takes the sleeve NAME on trust,
which is the exact hole `walkforward/registry.py`'s docstring says an adversarial refuter walked
through. The allowlist is therefore extended from each research spec's own surface, resolved
through `build_broker_symbol_resolver`, never by hand.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import yaml  # noqa: E402

import ad_exit_sweep as AD  # noqa: E402  — AD's sweep, imported so it is ONE implementation
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import supply as SUP  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.stats import benjamini_hochberg  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AK_IN = HERE / "AK_SUPPLY_TRADES.json.gz"
AD_FRONTIER = REPO / ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                      "EXIT_FRONTIER_V1.json")
AD_TRAIL = REPO / ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                   "EXIT_FRONTIER_V1_TRAIL.json")
OUT = HERE / "AK_SUPPLY_GATE_V1.json"
OUT_FRONTIER = HERE / "AK_EXIT_FRONTIER_V2.json"

SERVER = AD.SERVER
DECLARED_FAMILY = AD.DECLARED_FAMILY          # 69, AA's
FAMILY_SENSITIVITY = (69, 276)                # AA's, AF's; the ledger count is added at runtime

#: The gap, computed rather than transcribed — see `gap_sleeves()`.
GAP_EXPECTED = ("asia_pdl_fade", "liq_asia_up_low_metal", "orb_crypto_london",
                "sub_xvol_pullback")


def gap_sleeves(aa: dict) -> tuple[list[str], dict]:
    """Sleeves AA generated trades for that no exit frontier covers. Measured, not assumed."""
    swept = set()
    for p in (AD_FRONTIER, AD_TRAIL):
        if p.is_file():
            swept |= set(json.loads(p.read_text()).get("sleeves") or {})
    generated = {s for s, n in (aa.get("n_trades_by_sleeve") or {}).items() if n}
    gap = sorted(generated - swept)
    return gap, {
        "n_generated_with_trades": len(generated),
        "n_swept_by_AD": len(swept & generated),
        "gap": gap,
        "n_trades_in_gap": {s: aa["n_trades_by_sleeve"][s] for s in gap},
        "sources": [str(AD_FRONTIER.relative_to(REPO)), str(AD_TRAIL.relative_to(REPO))],
        "why": ("AD's WORK_LIST + MX_FAMILY is its own prompt's value order and does not name "
                "these; nothing about them was excluded on evidence. `sub_xvol_pullback` is one "
                "of the three ARMED sleeves and has the estate's best capture ratio (0.604, AA "
                "§2.2), so its exit surface was the largest unmeasured one in the estate."),
    }


def allowlist_with_supply() -> dict:
    al = dict(AD.allowlist())
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    for tag, spec in SUP.SUPPLY_SPECS.items():
        al[tag] = tuple(sorted({resolve(s) for s in spec.on_surface}))
    return al


def q_at(p_by_sleeve: dict[str, float], alpha: float, n_judged: int, n: int) -> dict[str, dict]:
    """BH q-values at one declared family size, padded EXACTLY as `gate.py:797-799` pads.

    Reproduced rather than approximated: the gate takes `max(n_judged, declared_family_size)`
    and carries the difference at `p = 1.0`, so a sleeve that never reached a null cannot shrink
    the family. A sensitivity computed any other way would not be the same statistic the verdict
    used at 69.
    """
    names = [s for s, p in p_by_sleeve.items() if p is not None]
    if not names:
        return {}
    effective = max(n_judged, n)
    padded = [p_by_sleeve[s] for s in names] + [1.0] * (effective - len(names))
    corr = benjamini_hochberg(padded, alpha)
    return {s: {"q": corr["qvalues"][i], "rejected": bool(corr["rejected"][i]),
                "family_size": corr["m"]}
            for i, s in enumerate(names)}


def verdict_row(sv, tag: str) -> dict:
    d = sv.diagnostics or {}
    cd = d.get("cost_decomposition") or {}
    hold = d.get("holds") or {}
    exc = d.get("excursion") or {}
    return {
        "verdict": sv.verdict.value,
        "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "gates": {g: bool(v.get("pass")) for g, v in sorted(sv.gates.items())},
        "failing_gates": [g for g in ("expectancy", "lifetime", "stability", "robustness",
                                      "significance")
                          if not sv.gates.get(g, {}).get("pass")],
        "gate_margins": (d.get("margins") or {}),
        "oos_positive_fold_frac": sv.gates.get("stability", {}).get("oos_positive_fold_frac"),
        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
        "coverage_frac": sv.gates.get("cost_coverage", {}).get("coverage_frac"),
        "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "lifetime_mean_r_per_trade": sv.gates.get("lifetime", {}).get(
            "mean_r_net_per_trade_all_folds"),
        "mean_gross_r": cd.get("mean_gross_r"),
        "mean_cost_r": cd.get("mean_cost_r"),
        "cost_pct_of_abs_gross": cd.get("cost_pct_of_abs_gross"),
        "largest_cost_term": cd.get("largest_term"),
        "cost_terms_mean_r": {k: (v or {}).get("mean_r")
                              for k, v in sorted((cd.get("terms") or {}).items())},
        "median_hold_hours": hold.get("median_hours"),
        "frac_hold_over_24h": hold.get("frac_over_24h"),
        "mean_mfe_r": exc.get("mean_mfe_r"),
        "mean_mae_r": exc.get("mean_mae_r"),
        "capture_ratio_pooled": exc.get("capture_ratio_pooled"),
        "by_fold": (d.get("by_fold") or {}),
        "by_symbol": (d.get("by_symbol") or {}),
        "by_side": (d.get("by_side") or {}),
        "primary_prescription": d.get("primary_prescription"),
        "prescriptions": d.get("prescriptions"),
        "fidelity": sv.fidelity,
        "reasons": list(sv.reasons),
    }


def main() -> dict:
    stage = os.environ.get("AK_STAGE") or "all"
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AK")

    aa = json.load(gzip.open(AA_IN, "rt"))
    ak = json.load(gzip.open(AK_IN, "rt"))
    gap, gap_meta = gap_sleeves(aa)
    print(f"AD's exit-frontier gap, measured: {gap}")
    if set(gap) != set(GAP_EXPECTED):
        print(f"  NOTE: gap differs from the expected {list(GAP_EXPECTED)} — reported as measured")

    costs = load_broker_true_costs(AD.COSTS)
    units = json.loads(AD.UNITS.read_text())
    tf_of = {s: {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[v]
             for s, v in aa["timeframe_by_sleeve"].items()}
    for tag, meta in ak["specs"].items():
        tf_of[tag] = {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[meta["timeframe"]]

    base_spec = OPTIONS["B_balanced"]
    spec = base_spec.with_(spec_id=f"{base_spec.spec_id}_ak_supply",
                           sleeve_symbol_allowlist=allowlist_with_supply(),
                           declared_family_size=DECLARED_FAMILY)

    # AA's 32 at their as-walked labelling + the four new sleeves at their AUTHORED contract.
    rows: dict[str, list[dict]] = {s: list(v) for s, v in aa["trades"].items()}
    for tag, v in ak["trades"].items():
        rows[tag] = list(v)
    print(f"family: {len(rows)} sleeves ({sum(1 for v in rows.values() if v)} with trades)")

    out: dict = {
        "schema": "gtos.walkforward.supply_gate.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_supply_gate.py"),
        "session": "AK", "blocks": "B950-B999",
        "gate": {"option": "B_balanced", "spec_id": spec.spec_id, "spec_sha256": spec.seal(),
                 "account": spec.account, "declared_family_size": DECLARED_FAMILY,
                 "note": ("AA's family and AA's declared_family_size, so every verdict is an A/B "
                          "against AA_ESTATE_WALK.json and EXIT_FRONTIER_V1.json")},
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "ad_frontier_gap": gap_meta,
        "sources": {"aa_trades": str(AA_IN.relative_to(REPO)),
                    "ak_trades": str(AK_IN.relative_to(REPO))},
    }

    # =================================================================================
    # 1. the gate, in diagnostic mode
    # =================================================================================
    if stage in ("all", "gate"):
        print("\n=== gating the whole family in diagnostic mode ===", flush=True)
        t0 = time.time()
        res = run_gate({s: AD.to_records(v) for s, v in rows.items()},
                       spec, costs=costs, diagnose=True, server=SERVER)
        print(f"  {time.time()-t0:.0f}s")

        # Parity against AA: the 32 must reproduce, or the four new sleeves changed the family's
        # BH ranks in a way that invalidates the A/B and the report has to say so.
        aa_walk = json.loads((REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
                              / "AA_ESTATE_WALK.json").read_text())
        aa_rows = {r["sleeve"]: r for r in aa_walk["runs"]["B_balanced|v1_1"]["rows"]}
        parity = {"n_compared": 0, "verdict_identical": 0, "pooled_identical": 0, "moved": {}}
        for s, sv in res.verdicts.items():
            a = aa_rows.get(s)
            if not a:
                continue
            parity["n_compared"] += 1
            vsame = a["verdict"] == sv.verdict.value
            psame = ((a["pooled_oos_mean_r"] is None) == (sv.pooled_oos_mean_r is None)
                     and (a["pooled_oos_mean_r"] is None
                          or abs(a["pooled_oos_mean_r"] - sv.pooled_oos_mean_r) < 1e-12))
            parity["verdict_identical"] += vsame
            parity["pooled_identical"] += psame
            if not (vsame and psame):
                parity["moved"][s] = {"aa_verdict": a["verdict"], "here": sv.verdict.value,
                                      "aa_pooled": a["pooled_oos_mean_r"],
                                      "here_pooled": sv.pooled_oos_mean_r,
                                      "aa_q": a.get("q_value"), "here_q": sv.q_value}
        parity["why"] = (
            "Adding four sleeves to the family changes the BH rank ORDER, so q-values may move "
            "even where the pooled mean is bit-identical. But that is NOT what moved here, and "
            "the first version of this string implied it was. All six sleeves below went "
            "NOT_EVALUABLE -> REJECT with aa_pooled null -> a number, i.e. AA could not score "
            "them at all and this run can. The cause is Session Y's fidelity merge (90224cfe6), "
            "which raised the first-of-day sleeves' live_recall to 1.0 — AD measured the same "
            "26-of-32 parity for the same six and recorded it at "
            "phase7/SESSION_AD_EXIT_REPAIR_RESULT.md §7.3. So this block reproducing AD exactly "
            "is a cross-check passing, not four new sleeves perturbing anything.")
        parity["cause"] = ("Session Y fidelity merge 90224cfe6 — live_recall 1.0 on the "
                           "first-of-day set; see AD §7.3 for the same six")
        out["aa_parity"] = parity
        print(f"  AA parity: verdict {parity['verdict_identical']}/{parity['n_compared']}, "
              f"pooled {parity['pooled_identical']}/{parity['n_compared']}; "
              f"moved {sorted(parity['moved'])}")

        p_by = {s: sv.p_raw for s, sv in res.verdicts.items()}
        n_measured = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
        n_ledger = int(n_measured["n_trials"])
        sens = {}
        for n in sorted({*FAMILY_SENSITIVITY, len(res.verdicts), n_ledger}):
            sens[str(n)] = q_at(p_by, spec.alpha, len(res.verdicts), n)
        # The 69-column must reproduce the verdicts' own q, or the sensitivity is not the same
        # statistic and every other column is uninterpretable.
        recomputed_ok = all(
            abs(sens[str(DECLARED_FAMILY)][s]["q"] - sv.q_value) < 1e-12
            for s, sv in res.verdicts.items()
            if sv.q_value is not None and s in sens[str(DECLARED_FAMILY)])
        out["family_size_sensitivity"] = {
            "alpha": spec.alpha,
            "family_sizes": {"sleeves_judged_in_this_run": len(res.verdicts), "AA": 69,
                             "AF": 276, "trial_ledger_measured": n_ledger},
            "reproduces_the_gates_own_q_at_69": recomputed_ok,
            "q_by_family_size": sens,
            "why": ("declared_family_size has no principled stopping rule (AF §11). Published as "
                    "a sensitivity so the owner decision can be read off this artifact rather "
                    "than re-run. Padded exactly as gate.py:797-799 pads."),
        }
        print(f"  family-size sensitivity reproduces the gate's own q at 69: {recomputed_ok}")

        out["new_sleeves"] = {tag: verdict_row(res.verdicts[tag], tag)
                             for tag in SUP.SUPPLY_SPECS if tag in res.verdicts}
        out["gap_sleeves_baseline"] = {s: verdict_row(res.verdicts[s], s)
                                       for s in gap if s in res.verdicts}
        for tag, r in out["new_sleeves"].items():
            print(f"  {tag:26s} {r['verdict']:14s} n={r['n_trades']:5d} "
                  f"pooled={r['pooled_oos_mean_r']} p={r['p_raw']} q={r['q_value']} "
                  f"failing={r['failing_gates']} -> {r['primary_prescription']}")
            ledger.record(
                mechanism="unregistered_sleeve_gate", sleeve=tag,
                variant={"exit": "authored_contract", "clock": "server_repaired",
                         "family": "AA_32_plus_AK_4"},
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(r["verdict"], "evaluated"),
                metric=r["pooled_oos_mean_r"], metric_name="pooled_oos_mean_r",
                note="AK first gate of a generator with no SleeveSpec")

    # =================================================================================
    # 2 + 3. the exit sweeps — AD's plan, AD's resimulation, AD's summary
    # =================================================================================
    if stage in ("all", "sweep", "gap"):
        print("\n=== loading bars for the sweeps ===", flush=True)
        t0 = time.time()
        series, index, _res = AD.load_bars()
        print(f"  {len(series)} series in {time.time()-t0:.0f}s", flush=True)
        rule = AD.resolve_rule(SERVER)

        targets: list[str] = []
        if stage in ("all", "sweep"):
            targets += sorted(SUP.SUPPLY_SPECS)
        if stage in ("all", "gap"):
            targets += gap
        frontier: dict[str, dict] = {}
        n_cells = 0
        for sleeve in targets:
            src = rows.get(sleeve) or []
            if not src:
                frontier[sleeve] = {"available": False, "reason": "no generated trades"}
                continue
            tf = tf_of[sleeve]
            plan = list(AD.plan_for(sleeve, tf, units))
            authored = SUP.SUPPLY_SPECS.get(sleeve)
            if authored is not None:
                ts = authored.authored_exit.get("time_stop_bars")
                plan.append(AD.Variant(
                    name="authored_contract", family="authored",
                    time_stop_bars=(int(ts) if ts else None), target_mode="native",
                    note=authored.authored_exit["cite"]))
            print(f"\n### {sleeve} [{AD.TF_NAME[tf]}] n={len(src)} — {len(plan)} cells",
                  flush=True)
            cells: dict[str, dict] = {}
            t1 = time.time()
            for v in plan:
                new_rows, tel = AD.resimulate(src, v, series, index, costs, spec.account, rule)
                if not new_rows:
                    cells[v.name] = {"variant": v.as_dict(), "available": False,
                                     "reason": "no trade survived re-simulation",
                                     "resim_skips": tel}
                    continue
                recs = {s: AD.to_records(r if s != sleeve else new_rows)
                        for s, r in rows.items()}
                gres = run_gate(recs, spec, costs=costs, diagnose=True, server=SERVER)
                cells[v.name] = {"variant": v.as_dict(),
                                 **AD.summarize(gres.verdicts[sleeve], tel, len(new_rows))}
                n_cells += 1
                ledger.record(
                    mechanism="exit_repair_sweep", sleeve=sleeve, variant=v.as_dict(),
                    window="full_archive", spec_sha256=spec.seal(),
                    outcome={"ADMIT": "admitted", "REJECT": "rejected",
                             "NOT_EVALUABLE": "not_evaluable"}.get(
                                 gres.verdicts[sleeve].verdict.value, "evaluated"),
                    metric=gres.verdicts[sleeve].pooled_oos_mean_r,
                    metric_name="pooled_oos_mean_r",
                    note=f"AK exit frontier, {v.family} cell {v.name}")
            ok = {k: c for k, c in cells.items() if c.get("pooled_oos_mean_r") is not None}
            best = max(ok, key=lambda k: ok[k]["pooled_oos_mean_r"]) if ok else None
            base = (cells.get("as_walked") or {}).get("pooled_oos_mean_r")
            frontier[sleeve] = {
                "available": True, "timeframe": AD.TF_NAME[tf], "n_trades": len(src),
                "n_cells": len(ok),
                "as_walked_pooled_oos_mean_r": base,
                "best_cell": best,
                "best_pooled_oos_mean_r": (ok[best]["pooled_oos_mean_r"] if best else None),
                "delta_vs_as_walked": (
                    round(ok[best]["pooled_oos_mean_r"] - base, 6)
                    if best is not None and base is not None else None),
                "best_failing_gates": (ok[best]["failing_gates"] if best else None),
                "best_verdict": (ok[best]["verdict"] if best else None),
                "cells": cells,
            }
            f = frontier[sleeve]
            print(f"  as_walked {f['as_walked_pooled_oos_mean_r']} -> best {f['best_cell']} "
                  f"{f['best_pooled_oos_mean_r']} (delta {f['delta_vs_as_walked']}) "
                  f"verdict {f['best_verdict']} failing {f['best_failing_gates']} "
                  f"[{time.time()-t1:.0f}s]", flush=True)

        fr_doc = {
            "schema": "gtos.walkforward.exit_frontier.v1",
            "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                             "ak_supply_gate.py"),
            "session": "AK", "blocks": "B950-B999",
            "extends": str(AD_FRONTIER.relative_to(REPO)),
            "why": ("the same schema as AD's frontier so the two concatenate. Two populations: "
                    "the four sleeves AD's WORK_LIST did not name (one of them ARMED) and the "
                    "four sleeves no registry can reach."),
            "gate": out["gate"], "cost_artifact": out["cost_artifact"],
            "maxbars": AD.MAXBARS,
            "harness": ("ad_exit_sweep.plan_for / resimulate / summarize, IMPORTED. Any "
                        "difference between this frontier and AD's is a difference in the "
                        "sleeve, not in the instrument."),
            "ad_frontier_gap": gap_meta,
            "n_cells_gated": n_cells,
            "sleeves": frontier,
        }
        OUT_FRONTIER.write_text(json.dumps(fr_doc, indent=2, default=str))
        print(f"\nwrote {OUT_FRONTIER.relative_to(REPO)} ({n_cells} cells gated)")
        out["frontier_artifact"] = str(OUT_FRONTIER.relative_to(REPO))

    out["seconds_total"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {OUT.relative_to(REPO)} in {time.time()-t_start:.0f}s")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
