"""Session AL, item 5 — the candidate dossier, refreshed for what this session moved.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_candidate_dossier.py

WHAT IT IS
----------
One row per candidate this session touched, each carrying what the next composition needs and
nothing it has to re-derive: the per-fold OOS series with its window dates, q at EVERY declared
family in the artifact, and the full `(population, source, exit_assumption, era, account,
aggregation)` stamp AI's rules R0-R11 require. `AK_CANDIDATE_DOSSIER_V1.json`'s shape, extended by
the one axis wave 9 added: **population**, because this session measured that the population choice
moves `mx_btcusd`'s p by 53x and therefore moves a verdict.

R0 IS ENFORCED, NOT ADVISED
---------------------------
Every figure is emitted inside a `(population, exit, band, option, family)` key. There is no
top-level "the candidate's p" field, because there is no such number -- that is R0, and the way to
enforce it in an artifact is to make the un-stamped version unrepresentable rather than to warn
about it in prose.
"""

from __future__ import annotations

import collections
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(AD_DIR))
sys.path.insert(0, str(HERE))

import ad_exit_sweep as AD  # noqa: E402
import al_admission_closers as ALC  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    measured_n_trials,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.fidelity import register_threshold_variant  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

DECL = HERE / "CANDIDATE_FAMILY_V2.json"
STATE = HERE / "AL_XVOL_REACHABLE_STATE_V1.json.gz"
OUT = HERE / "AL_CANDIDATE_DOSSIER_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

BTC = "mx_btcusd_d1_donchian_20_breakout"
PARENT = "sub_xvol_pullback"
ASIA = "asia_pdl_fade"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
PRODUCTION_PARAMS = {"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10}

#: (candidate, headline cell) -- the cell each candidate's row is built at, and WHY that cell.
HEADLINES = {
    BTC: ("target_5R", "AD's target ridge peak; a RIDGE not a spike (target_4R also admits on "
                       "RECORDED, and the surface is monotone 1R->5R)"),
    PARENT: ("as_walked", "the production contract; AK's target_4R is the banked exit repair and "
                          "is carried as a second cell"),
    "thr_sub_xvol_pullback_vr14_s125_ac015": (
        "as_walked", "AB B658's headline threshold variant, the one banked as a prescription"),
    "thr_sub_xvol_pullback_vr14_s150_ac015": ("as_walked", "AB's second variant cell"),
    "thr_sub_xvol_pullback_vr14_s100_ac010": ("as_walked", "AB's third variant cell"),
    ASIA: ("stop_2.5x", "AK's winner, confirmed at rank 1-2 of AL's 150-cell cross"),
}

CELLS = {
    "thr_sub_xvol_pullback_vr14_s125_ac015": {"vr_xhi": 1.4, "slope_up": 1.25, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s150_ac015": {"vr_xhi": 1.4, "slope_up": 1.5, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s100_ac010": {"vr_xhi": 1.4, "slope_up": 1.0, "ac_band": 0.10},
}

POPS = ("ALL_ERAS", "RECORDED", "DECIDABLE", "INTERSECTION")


def _fold_series(folds) -> list:
    """AK §7.9's lesson: `diagnostics.by_fold` emits `test_mean_r`, and guessing the key name
    yields a list of Nones that silently empties the deliverable. Fall back loudly."""
    for k in ("test_mean_r", "oos_mean_r", "mean_r"):
        vals = [f.get(k) for f in (folds or [])]
        if vals and all(v is not None for v in vals):
            return vals
    return []


def main() -> dict:
    t0 = time.time()
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    families = {
        "CANDIDATE_BOOK_V2@all_declared": fam.effective_size("CANDIDATE_BOOK_V1"),
        "CANDIDATE_BOOK_V2@looks_taken": fam.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN),
        "AA_historical_69": 69,
        "MECHANISM_CROSS_V1": fam.effective_size("MECHANISM_CROSS_V1"),
        "ESTATE_UNION_V1": fam.effective_size("ESTATE_UNION_V1"),
    }
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = dict(AD.allowlist())
    state = json.load(gzip.open(STATE, "rt"))
    srows = state["rows"]

    for member, params in CELLS.items():
        register_threshold_variant(member, parent=PARENT, params=params,
                                   production_params=PRODUCTION_PARAMS)
        keys = ALC.cell_fires(srows, params)
        rows, _ = ALC.label(srows, keys, member, series, index)
        base_rows[member] = rows
        al[member] = al[PARENT]

    #: the per-candidate row set at its headline cell, and the second cell where one is banked
    cells_by_candidate = {
        BTC: {"as_walked": AD.AS_WALKED,
              "target_5R": AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                                      target_r=5.0),
              "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                      target_r=4.0)},
        PARENT: {"as_walked": AD.AS_WALKED,
                 "target_4R": AD.Variant(name="target_4R", family="target",
                                         target_mode="fixed_r", target_r=4.0)},
        ASIA: {"as_walked": AD.AS_WALKED,
               "stop_2.5x": AD.Variant(name="stop_2.5x", family="stop_width", stop_mult=2.5,
                                       target_mode="scales_with_stop")},
    }
    for member in CELLS:
        cells_by_candidate[member] = {
            "as_walked": AD.AS_WALKED,
            "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                    target_r=4.0)}
    print(f"substrate in {time.time()-t0:.0f}s")

    def restrict(recs, pop, band="mid"):
        if pop == "ALL_ERAS":
            return recs
        out = {}
        for s, rs in recs.items():
            keep = []
            for r in rs:
                try:
                    est = sm.estimate(r.symbol, ACCOUNT, r.entry_utc, band=band)
                except Exception:  # noqa: BLE001
                    continue
                rec, dec = est.era_class == "RECORDED", bool(est.decidable)
                if {"RECORDED": rec, "DECIDABLE": dec,
                    "INTERSECTION": rec and dec}[pop]:
                    keep.append(r)
            if keep:
                out[s] = keep
        return out

    o = OPTIONS["B_balanced"]
    dossier: dict[str, dict] = {}
    for cand, cells in cells_by_candidate.items():
        head_cell, head_why = HEADLINES[cand]
        row = {
            "headline_cell": head_cell, "why_this_cell": head_why,
            "kind": ("threshold_variant" if cand in CELLS else
                     ("declared_member_exit_cell")),
            "adds_to_declared_family": cand in CELLS,
            "by_stamp": {},
        }
        for cell_name, v in cells.items():
            rws, _ = AD.resimulate(base_rows[cand], v, series, index, costs, ACCOUNT, rule)
            if not rws:
                continue
            pop_rows = {s: list(r) for s, r in base_rows.items()}
            pop_rows[cand] = rws
            recs0 = {s: AD.to_records(r) for s, r in pop_rows.items()}
            for pop in POPS:
                recs = restrict(recs0, pop)
                for fname, m in families.items():
                    sp = o.with_(spec_id=f"{o.spec_id}_al_dossier",
                                 sleeve_symbol_allowlist=al, spread_band="mid",
                                 declared_family_size=m)
                    res = run_gate(recs, sp, costs=costs, server=SERVER,
                                   diagnose=(fname == "CANDIDATE_BOOK_V2@all_declared"))
                    sv = res.verdicts.get(cand)
                    if sv is None:
                        continue
                    stamp = (f"population={pop}|exit={cell_name}|band=mid|option=B_balanced"
                             f"|family={fname}")
                    d = sv.diagnostics or {}
                    folds = d.get("by_fold") or []
                    row["by_stamp"][stamp] = {
                        # --- R0's five stamp fields, on every row, never implied ---
                        "stamp": {"population": pop, "source": "AA archive walk, re-labelled",
                                  "exit_assumption": cell_name, "era": "full archive",
                                  "account": ACCOUNT, "aggregation": "per decision-day, pooled OOS",
                                  "band": "mid", "option": "B_balanced", "family": fname,
                                  "declared_family_size": m},
                        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                        "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get(
                            "oos_mean_r_per_trade"),
                        "p_raw": sv.p_raw, "q_value": sv.q_value,
                        "effective_family_size": res.family["multiplicity"][
                            "effective_family_size"],
                        "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                           "robustness", "significance")
                                               if not sv.gates.get(g, {}).get("pass")],
                        "gates": {g: bool(x.get("pass")) for g, x in sorted(sv.gates.items())},
                        "fold_means": sv.gates.get("stability", {}).get("fold_means"),
                        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
                        "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
                        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
                        "coverage_frac": sv.gates.get("cost_coverage", {}).get("coverage_frac"),
                        "by_fold": ([{k: f.get(k) for k in
                                      ("fold_id", "status", "oos_start", "oos_end",
                                       "n_test_trades", "test_mean_r", "train_mean_r")}
                                     for f in folds] or None),
                        "fold_oos_mean_r_series": _fold_series(folds) or None,
                        "primary_prescription": d.get("primary_prescription"),
                        "fidelity": {"class": sv.fidelity.get("class"),
                                     "basis": sv.fidelity.get("basis"),
                                     "live_recall": sv.fidelity.get("live_recall")},
                        "spec_sha256": sp.seal(),
                    }
            print(f"  {cand:40s} {cell_name:12s} "
                  f"{len([k for k in row['by_stamp'] if f'exit={cell_name}' in k])} stamps",
                  flush=True)
        dossier[cand] = row

    # ---- the fold series is FAMILY-INVARIANT, so a bare null on the non-diagnosed family arms
    #      would be exactly the silent null this session criticised in its own adversarial pass.
    #      `declared_family_size` enters only `significance` (gate.py:789-830); it cannot move a
    #      fold mean or a p_raw. That is ASSERTED here across every family arm of each group
    #      rather than asserted in prose, and then the series is carried to the siblings with a
    #      pointer at the row it came from.
    #  My first version of this control put `verdict` in the invariant set and it fired 5 times —
    #  correctly, and the control was the thing that was wrong. `declared_family_size` enters
    #  `significance`, so `q_value` and therefore `verdict` MUST be free to move with the family;
    #  only `p_raw`, `pooled_oos_mean_r` and `n_trades` are invariant. What the verdict owes instead
    #  is MONOTONICITY: a LARGER declared family can only ever be stricter, so a bigger m turning a
    #  REJECT into an ADMIT would be a real defect. That is the assertion worth having and it is
    #  the one this now makes.
    invariance = {"n_groups": 0, "n_checked": 0, "violations": [],
                  "invariant_fields": ["p_raw", "pooled_oos_mean_r", "n_trades"],
                  "fields_free_to_move_with_the_family": ["q_value", "verdict"],
                  "monotonicity_checked": "a larger declared family may never admit what a smaller "
                                          "one rejected",
                  "monotonicity_violations": []}
    for cand, row in dossier.items():
        groups: dict[tuple, list[str]] = collections.defaultdict(list)
        for stamp in row["by_stamp"]:
            parts = dict(p.split("=", 1) for p in stamp.split("|"))
            groups[(parts["population"], parts["exit"], parts["band"],
                    parts["option"])].append(stamp)
        for key, stamps in groups.items():
            invariance["n_groups"] += 1
            src = next((s for s in stamps
                        if dossier[cand]["by_stamp"][s].get("fold_oos_mean_r_series")), None)
            ref = dossier[cand]["by_stamp"][stamps[0]]
            for s in stamps:
                r = dossier[cand]["by_stamp"][s]
                invariance["n_checked"] += 1
                for f in invariance["invariant_fields"]:
                    a, b = ref.get(f), r.get(f)
                    same = (a == b) or (isinstance(a, float) and isinstance(b, float)
                                        and abs(a - b) < 1e-15)
                    if not same:
                        invariance["violations"].append(
                            {"candidate": cand, "group": list(key), "field": f,
                             "stamp_a": stamps[0], "a": a, "stamp_b": s, "b": b})
            # monotonicity: sort this group's arms by declared size and check no ADMIT appears
            # at a larger family than a REJECT of the same candidate.
            by_m = sorted(((dossier[cand]["by_stamp"][s]["stamp"]["declared_family_size"], s)
                           for s in stamps), key=lambda t: t[0])
            seen_reject_at = None
            for m_i, s in by_m:
                v = dossier[cand]["by_stamp"][s]["verdict"]
                if v == "REJECT" and seen_reject_at is None:
                    seen_reject_at = m_i
                if v == "ADMIT" and seen_reject_at is not None and m_i > seen_reject_at:
                    invariance["monotonicity_violations"].append(
                        {"candidate": cand, "group": list(key),
                         "rejected_at_m": seen_reject_at, "admitted_at_larger_m": m_i,
                         "stamp": s})
                if src and s != src and not r.get("fold_oos_mean_r_series"):
                    r["fold_oos_mean_r_series"] = dossier[cand]["by_stamp"][src][
                        "fold_oos_mean_r_series"]
                    r["by_fold"] = dossier[cand]["by_stamp"][src]["by_fold"]
                    r["fold_series_carried_from"] = src
                    r["why_carried"] = (
                        "declared_family_size enters only the `significance` gate "
                        "(gate.py:789-830) and cannot move a fold mean, a p_raw or an n. The "
                        "invariance is ASSERTED across every family arm of this group; see "
                        "`family_invariance_control`.")
                elif not src and not r.get("fold_oos_mean_r_series"):
                    r["fold_oos_mean_r_series"] = None
                    r["no_fold_series_because"] = (
                        f"no arm in this group produced one; the verdict here is "
                        f"{r.get('verdict')}, so the gate returned before scoring folds")
    print(f"family-invariance control: {invariance['n_checked']} rows over "
          f"{invariance['n_groups']} groups, {len(invariance['violations'])} invariance "
          f"violations, {len(invariance['monotonicity_violations'])} monotonicity violations")

    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    out = {
        "schema": "gtos.wave9.al.candidate_dossier.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "blocks": "B1150-B1199",
        "for": ("the next composition. Every figure is inside a (population, exit, band, option, "
                "family) key -- there is no un-stamped 'the candidate's p', which is R0 enforced "
                "rather than advised."),
        "family_sizes": families,
        "declared_family": {"path": str(DECL.relative_to(REPO)), "sha256": fam.sha256,
                            "membership_sha256": fam.membership_of("CANDIDATE_BOOK_V1")},
        "the_population_axis_is_new_in_wave_9": (
            "AK's dossier carried (population, source, exit_assumption, era, account, "
            "aggregation). Wave 9 measured that WHICH era-quality field defines the population "
            "moves mx_btcusd's p by 53x -- ALL_ERAS 0.0106, RECORDED 0.0011, DECIDABLE 0.0581 at "
            "target_5R -- so `population` is now an explicit key on every row rather than an "
            "assumed constant. See AL_DECIDABLE_POPULATION_V1.json and "
            "AL_POPULATION_INTERSECTION_V1.json."),
        "rules_applied": {
            "R0": "no un-stamped figure; every number lives under its five-field stamp",
            "R1": "populations that disagree are both published and the axis is named; never averaged",
            "R2": ("the ACCOUNT is part of the sleeve: every stamp carries account=FTMO, and no "
                   "redacted_account figure appears in this artifact at all rather than being implied"),
            "R6": "a gate ADMIT is not a survivor tier and not a lane KEEP",
            "R7": ("cost coverage is part of the number: `coverage_frac` is on every row, and the "
                   "population keys are themselves a coverage statement -- RECORDED / DECIDABLE / "
                   "INTERSECTION differ precisely in which eras the cost model is trusted on"),
            "R11": "when a control disagrees with prose, cite the JSON",
            "AI_§0": ("BH corrects for distinct HYPOTHESES: a threshold variant adds a family "
                      "member (`adds_to_declared_family: true`), an exit cell does not"),
            "rules_NOT_applicable_here_and_why": {
                "R3": "no UNCONDITIONAL/CARRY tier is asserted in this artifact",
                "R4": "no live corpus is used; every row is the archive walk",
                "R5": "no hold anchor is quoted; holds enter only through the exit re-simulation",
                "R8_R9_R10": ("outside this artifact's subject -- see phase8/receipts/"
                              "SLEEVE_DOSSIER_V1.json `reconciliation_rules` for the full twelve"),
            },
        },
        "strict_mode": {
            "what": ("R0's own check, emitted rather than asserted: a row is a violation if it "
                     "carries a metric without a complete five-field stamp."),
            "violations": [
                f"{cand}|{stamp}"
                for cand, row in dossier.items() for stamp, r in row["by_stamp"].items()
                if r.get("pooled_oos_mean_r") is not None
                and not all(r.get("stamp", {}).get(k) for k in
                            ("population", "exit_assumption", "band", "option", "account"))
            ],
        },
        "trial_ledger": nt,
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "family_invariance_control": {
            "claim": ("declared_family_size enters only the `significance` gate "
                      "(gate.py:789-830), so p_raw, pooled_oos_mean_r, n_trades and the fold "
                      "means must be IDENTICAL across the five family arms of every "
                      "(population, exit, band, option) group. q_value and verdict are NOT "
                      "invariant -- they are what the family moves -- so what they owe instead is "
                      "MONOTONICITY: a larger declared family may only ever be stricter, and an "
                      "ADMIT at a larger m than a REJECT of the same candidate would be a real "
                      "defect. Both are checked."),
            "why_it_is_asserted_and_not_stated": (
                "diagnostics are only computed on one family arm per group, so the other four "
                "would carry a bare null fold series. A bare null reads as 'not evaluable' when "
                "it means 'not requested', which is the silent-null failure this session's own "
                "adversarial pass caught in itself (result doc §8.2). Carrying the series is only "
                "legitimate if the invariance holds, so it is measured."),
            **invariance,
        },
        "candidates": dossier,
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    n_stamps = sum(len(v["by_stamp"]) for v in dossier.values())
    print(f"\nwrote {OUT.relative_to(REPO)}: {len(dossier)} candidates, {n_stamps} stamped rows "
          f"({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
