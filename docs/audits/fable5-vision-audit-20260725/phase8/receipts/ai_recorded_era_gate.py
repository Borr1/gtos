"""Session AI — close the gap the adversarial pass opened: run the RECORDED-era population
through the real gate.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_recorded_era_gate.py

WHY THIS EXISTS — AND IT EXISTS BECAUSE A REFUTER WAS RIGHT
----------------------------------------------------------
`ai_gate_at_declared_family.py` ran the gate on AA's population, where `mx_btcusd`'s p_raw is
0.011999. `AI_FAMILY_SENSITIVITY_V1.json` published the correction ARITHMETIC on AF's
RECORDED-era measurement, where it is 0.0064. An adversarial pass over this session's own claims
established that merging the two was the load-bearing error:

  * on AA's population, alpha = 0.10 admits `mx_btcusd` at NO family size. Measured: the largest
    admitting family at 0.10 is 16, and `gate.py:797` floors the effective family at
    `max(n_judged = 32, declared)`. The largest admitting family at alpha = 0.20 is **33**, not
    32 as first published -- `mx_btcusd` sits at BH rank 2, so the step-up boundary is one wider.
  * alpha = 0.20 is `options.C_exploratory`'s alpha, and its own sealed `author_note` reads
    "RESEARCH TRIAGE ONLY. A pass here means 'worth spending more data on', never 'worth arming'.
    Do not let a C-pass reach a book." So the ADMIT this session first reported is a
    research-triage pass, and saying "no threshold was loosened" was wrong: alpha is a threshold
    and it was doubled.

So the honest question is not "which family" but "does the admission survive at the SEALED
B_balanced alpha of 0.10 on a population whose costs are not an unvalidated extrapolation" -- and
that is answerable today, because the restriction AF used is outcome-independent and the machinery
is already in `GateSpec`.

WHAT IS RESTRICTED, AND WHY IT IS NOT SELECTION
----------------------------------------------
`era_class == RECORDED` is a property of the BROKER'S OWN BAR DATA — which eras
`spread_model_v1` measured rather than extrapolated. It is fixed before any return is seen, which
is the identical argument `GateSpec.coverage_policy="restrict_to_priced"` rests on and which its
own comment spells out: "which symbols are priceable is determined by what is in the tick archive,
NOT by what those symbols earned."

It matters because AF measured the model's composition defect: `anchor x era_ratio x hour_of_week`
reaches **198x** the modern base on 2000s NZDUSD, charging 178 % of the risk unit as spread, and
each factor was validated ALONE while the product never was. The wave-8 agreement's §4 therefore
restricts banded pricing to RECORDED until AG repairs it. This file follows that rule rather than
arguing with it.

THE RESTRICTION CUTS BOTH WAYS AND BOTH ARE PUBLISHED
-----------------------------------------------------
It is not a free improvement. Restricting drops trades, and `GateSpec.min_trades_total`,
`min_trades_per_fold` and `min_folds_evaluable` all bite harder on a smaller sample —
`sub_xvol_pullback` already has ZERO integer slack on the sample gate (3 evaluable folds against
a floor of 3) and on stability (3 of 4 positive against a `ceil(0.60 * 4) = 3` requirement), so
losing one fold makes it NOT_EVALUABLE before the core gates are ever read. Every sleeve's
retained fraction and every verdict is published, in both directions.
"""

from __future__ import annotations

import collections
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
DECL = HERE / "CANDIDATE_FAMILY_V1.json"
OUT = HERE / "AI_RECORDED_ERA_GATE_V1.json"

BAND = "mid"          # AF's verdict band; low/high are the robustness envelope
SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"


def _aa():
    spec = importlib.util.spec_from_file_location("aa_estate_walk_re",
                                                 AA_DIR / "aa_estate_walk.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["aa_estate_walk_re"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    AA = _aa()
    from src.costs.spread_model import load_spread_model

    try:
        smodel = load_spread_model()
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            f"the spread model will not load: {e}\n"
            f"`research/operations/spread_model_2026_07_29/` is outside the sparse-checkout "
            f"cone in a fresh worktree -- `git sparse-checkout add "
            f"research/operations/spread_model_2026_07_29` hydrates it. Without it every "
            f"`spread_band=` verdict silently becomes unavailable, which is the agreement's §4 "
            f"trap in its exact predicted shape.") from None

    records = AA.to_records(AA.load())
    al = AA.allowlist()
    costs = AA.load_broker_true_costs(AA.COSTS_V1_1)
    fam = CF.load_candidate_family(DECL)

    # --- the restriction, per trade ---------------------------------------------------
    # The spread model keys on the BROKER symbol. AA's TradeRecord.symbol is already the
    # broker name (its allowlist resolves canonical -> broker for the gate's own check), and
    # `features["symbol_canonical"]` carries the other one -- so an unpriceable symbol here is
    # a real gap in the model rather than a naming mistake, and it is counted as one.
    kept: dict[str, list[TradeRecord]] = {}
    mix: dict[str, dict] = {}
    for sleeve, recs in sorted(records.items()):
        cls = collections.Counter()
        rows = []
        for r in recs:
            try:
                est = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=BAND)
            except Exception:  # noqa: BLE001
                cls["unpriceable"] += 1
                continue
            cls[est.era_class] += 1
            if est.era_class == "RECORDED":
                rows.append(r)
        n = sum(cls.values())
        mix[sleeve] = {
            "n_total": len(recs), "n_classified": n, "era_class_mix": dict(cls),
            "n_recorded": len(rows),
            "recorded_frac": (round(len(rows) / len(recs), 4) if recs else None),
        }
        if rows:
            kept[sleeve] = rows

    n_before = sum(len(v) for v in records.values())
    n_after = sum(len(v) for v in kept.values())
    print(f"restricted to era_class == RECORDED at band={BAND}: "
          f"{n_before} -> {n_after} trades over {len(kept)} of {len(records)} sleeves "
          f"({100 * n_after / n_before:.1f} %)", flush=True)

    # --- the grid: the sealed alpha first, and the family sizes that matter -----------
    base = AA.OPTIONS["B_balanced"].with_(
        spec_id="wf_gate_option_B_balanced_ai_recorded_eras",
        sleeve_symbol_allowlist=al, spread_band=BAND)

    arms = {
        "CANDIDATE_BOOK_V1@all_declared": CF.with_declared_family(
            base, "CANDIDATE_BOOK_V1", loaded=fam),
        "CANDIDATE_BOOK_V1@looks_taken": CF.with_declared_family(
            base, "CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN, loaded=fam),
        "AA_69_comparator": base.with_(declared_family_size=69),
        "MECHANISM_CROSS_V1@all_declared": CF.with_declared_family(
            base, "MECHANISM_CROSS_V1", loaded=fam),
    }
    # The zero-trade sleeves cannot be withheld by name here -- the restriction has already
    # removed any sleeve with no RECORDED trade, and `n_judged` is whatever survives it. That
    # is itself the `looks_taken` basis arriving by a different route, and it is recorded.
    out = {
        "schema": "gtos.walkforward.recorded_era_gate.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ai_recorded_era_gate.py"),
        "question": ("Does the candidate admission survive at the SEALED B_balanced alpha of "
                     "0.10 on the population whose costs the spread model MEASURED, rather than "
                     "needing C_exploratory's 0.20 on a population whose deep-history FX costs "
                     "are an unvalidated product of two unvalidated multipliers?"),
        "why_this_file_exists": (
            "An adversarial pass over this session's own claims established that alpha = 0.10 "
            "admits at NO family size on AA's all-eras population, and that the alpha = 0.20 "
            "which does admit is options.C_exploratory's -- labelled 'RESEARCH TRIAGE ONLY ... "
            "never worth arming. Do not let a C-pass reach a book.' The sensitivity table's "
            "alpha = 0.10 result was arithmetic on AF's RECORDED-era p of 0.0064 while the gate "
            "run was on AA's 0.011999. This file stops the two being merged by running the gate "
            "on the restricted population end to end."),
        "restriction": {
            "predicate": "era_class == RECORDED",
            "band": BAND,
            "outcome_independent": True,
            "why": ("a property of the broker's own bar data -- which eras spread_model_v1 "
                    "measured rather than extrapolated -- fixed before any return is seen. The "
                    "identical argument GateSpec.coverage_policy='restrict_to_priced' rests on."),
            "why_it_is_needed": (
                "AF measured spread_model_v1's era_ratio x hour_of_week product at 198x the "
                "modern base on 2000s NZDUSD, charging 178 % of the risk unit as spread, with "
                "each factor validated alone and the product never validated. WAVE_8 agreement "
                "§4 restricts banded pricing to RECORDED until AG repairs it."),
            "it_cuts_both_ways": (
                "restricting drops trades, and min_trades_total / min_trades_per_fold / "
                "min_folds_evaluable all bite harder on a smaller sample. Every sleeve's "
                "retained fraction and every verdict is published, in both directions."),
            "n_trades_before": n_before, "n_trades_after": n_after,
            "n_sleeves_before": len(records), "n_sleeves_after": len(kept),
            "by_sleeve": mix,
        },
        "arms": {},
    }

    focus = ("mx_btcusd_d1_donchian_20_breakout", "sub_xvol_pullback")
    for label, spec0 in arms.items():
        out["arms"][label] = {}
        for alpha in (0.05, 0.10, 0.20):
            spec = spec0.with_(alpha=alpha)
            res = run_gate(kept, spec, costs=costs, server=SERVER)
            mult = res.family["multiplicity"]
            rows = {}
            for s, v in sorted(res.verdicts.items()):
                rows[s] = {
                    "verdict": v.verdict.value, "n_trades": v.n_trades,
                    "pooled_oos_mean_r": v.pooled_oos_mean_r,
                    "p_raw": v.p_raw, "q_value": v.q_value,
                    "failing_core_gates": [
                        g for g in ("expectancy", "lifetime", "stability", "robustness",
                                    "significance")
                        if not v.gates.get(g, {}).get("pass")],
                    "first_reason": (v.reasons[0][:300] if v.reasons else None),
                }
            out["arms"][label][f"alpha_{alpha}"] = {
                "spec_sha256": spec.seal(),
                "declared_family_size": spec.declared_family_size,
                "declared_family_id": spec.declared_family_id,
                "effective_family_size": mult["effective_family_size"],
                "n_sleeves_judged": mult["n_sleeves_judged_this_run"],
                "admitted": sorted(res.admitted),
                "n_admitted": len(res.admitted),
                "n_not_evaluable": len(res.not_evaluable),
                "focus": {s: rows.get(s) for s in focus},
                "rows": rows,
            }
            print(f"  {label:34s} alpha={alpha:.2f} m={mult['effective_family_size']:4d} "
                  f"-> ADMIT {sorted(res.admitted)}", flush=True)

    # --- the answer, stated in the artifact rather than left to a reader --------------
    sealed_alpha = {lab: out["arms"][lab]["alpha_0.1"]["admitted"] for lab in out["arms"]}
    any_at_sealed = sorted({s for v in sealed_alpha.values() for s in v})
    out["answer"] = {
        "admits_at_the_sealed_B_balanced_alpha_0.10": any_at_sealed,
        "by_family_at_alpha_0.10": sealed_alpha,
        "at_alpha_0.20_C_exploratory": {
            lab: out["arms"][lab]["alpha_0.2"]["admitted"] for lab in out["arms"]},
        "at_alpha_0.05": {lab: out["arms"][lab]["alpha_0.05"]["admitted"]
                          for lab in out["arms"]},
        "reading": (
            "If the alpha = 0.10 row is non-empty, the candidate admission survives at the "
            "alpha every published verdict in this estate already used, and the family "
            "declaration is SUFFICIENT rather than merely necessary. If it is empty, the "
            "family repair is necessary and not sufficient, the remaining gap is alpha rather "
            "than the bill, and the honest next step is stated in the routing below."
            ),
        "routing_if_empty": (
            "The blocker is then sample, not the bill: `mx_btcusd` needs its raw p below "
            "alpha/m at the declared family, i.e. more RECORDED-era trades on the same rule. "
            "Its exit repair is already banked (AD's target_5R, +0.309 R/day, p_raw 0.0101 on "
            "the as-walked eras) and has never been measured ON the RECORDED-era population -- "
            "carrying it there is the cheapest remaining move and needs no new data."),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"ADMITS at the sealed alpha 0.10: {any_at_sealed or '(none)'}")


if __name__ == "__main__":
    main()
