"""Session AL — the cell that settles the population question: RECORDED **and** DECIDABLE.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_population_intersection.py

WHY THIS RUN EXISTS
-------------------
`AL_DECIDABLE_POPULATION_V1.json` measured that the two era-quality fields the spread model
publishes disagree by a factor of **53 in p** on the same sleeve at the same exit:

    mx_btcusd @ target_5R, band mid, family 35
      ALL_ERAS    n 318   +0.547 R/day   p 0.0106   REJECT
      RECORDED    n 232   +0.982 R/day   p 0.0011   ADMIT     <- the wave-8 agreement's population
      DECIDABLE   n 240   +0.513 R/day   p 0.0581   REJECT    <- the spread model's OWN rule

and that the two populations are nearly the same SIZE (232 vs 240) with quite different
composition. That is not a tie-break anyone should decide by preference, so this file runs the two
cells that can settle it:

  **INTERSECTION** -- `era_class == RECORDED` AND `decidable`. The strictest defensible population:
  the era_ratio came from an observed series AND the band is narrow enough for the model's own rule
  to call it a result rather than a capture requirement. An admission that survives here does not
  depend on which field a reader prefers. One that does not survive here depends on the choice, and
  the choice then belongs to whoever owns the agreement's §4 rule.

  **RECORDED_UNDECIDABLE** -- the 78 BTCUSD trades the agreement KEEPS and the model's own rule
  says are undecidable. Their economics answer the mechanical question the p-difference raises:
  is DECIDABLE's worse p because those 78 trades were CARRYING the result, or because dropping
  them broke the fold structure? Those are different findings and only one of them is a problem
  with the claim.

Also published: the fold structure under each population, because a p that moves 53x while the
effect size barely moves is a variance or fold story, not an effect story, and the artifact should
say which.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

import gzip  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
OUT = HERE / "AL_POPULATION_INTERSECTION_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

BTC = "mx_btcusd_d1_donchian_20_breakout"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
POPS = ("ALL_ERAS", "RECORDED", "DECIDABLE", "INTERSECTION", "RECORDED_UNDECIDABLE")


def main() -> dict:
    t0 = time.time()
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AL")
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()
    o = OPTIONS["B_balanced"]

    exits = {
        "as_walked": AD.AS_WALKED,
        "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                target_r=4.0),
        "target_5R": AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                                target_r=5.0),
    }
    btc_rows = {}
    for nm, v in exits.items():
        btc_rows[nm], _ = AD.resimulate(base_rows[BTC], v, series, index, costs, ACCOUNT, rule)
    print(f"substrate in {time.time()-t0:.0f}s")

    def keeps(r, pop, band):
        try:
            est = sm.estimate(r.symbol, ACCOUNT, r.entry_utc, band=band)
        except Exception:  # noqa: BLE001
            return None
        rec, dec = est.era_class == "RECORDED", bool(est.decidable)
        return {"ALL_ERAS": True, "RECORDED": rec, "DECIDABLE": dec,
                "INTERSECTION": rec and dec, "RECORDED_UNDECIDABLE": rec and not dec}[pop]

    def restrict(recs, pop, band):
        if pop == "ALL_ERAS":
            return recs, {"kept": sum(len(v) for v in recs.values()), "dropped": 0}
        out, mix = {}, collections.Counter()
        for s, rs in recs.items():
            keep = []
            for r in rs:
                k = keeps(r, pop, band)
                mix["unpriceable" if k is None else ("kept" if k else "dropped")] += 1
                if k:
                    keep.append(r)
            if keep:
                out[s] = keep
        return out, dict(mix)

    rows_out: dict[str, dict] = {}
    for exit_name, rws in btc_rows.items():
        pop_rows = {s: list(r) for s, r in base_rows.items()}
        pop_rows[BTC] = rws
        recs0 = {s: AD.to_records(r) for s, r in pop_rows.items()}
        for pop in POPS:
            recs, mix = restrict(recs0, pop, "mid")
            sp = o.with_(spec_id=f"{o.spec_id}_al_intersect", sleeve_symbol_allowlist=al,
                         spread_band="mid")
            sp = CF.with_declared_family(sp, "CANDIDATE_BOOK_V1", loaded=fam)
            res = run_gate(recs, sp, costs=costs, server=SERVER, diagnose=True)
            v = res.verdicts.get(BTC)
            key = f"{exit_name}|{pop}"
            if v is None:
                rows_out[key] = {"verdict": "ABSENT", "restriction_mix": mix}
                print(f"  {key:34s} ABSENT")
                continue
            st = v.gates.get("stability", {})
            rows_out[key] = {
                "verdict": v.verdict.value, "n_trades": v.n_trades,
                "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                "q_value": v.q_value,
                "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                   "robustness", "significance")
                                       if not v.gates.get(g, {}).get("pass")],
                "fold_means": st.get("fold_means"),
                "n_oos_folds": st.get("denominator"),
                "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
                "n_thin_folds": v.gates.get("sample", {}).get("n_thin_folds"),
                "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
                "oos_mean_r_per_trade": v.gates.get("expectancy", {}).get(
                    "oos_mean_r_per_trade"),
                "p_floor": (v.telemetry or {}).get("p_floor", {}).get("p_floor"),
                "restriction_mix": mix, "spec_sha256": sp.seal(),
                # R0's five stamp fields, on every arm. Their absence here was found by an
                # adversarial pass over this session's own §8.8, which claimed the band stamp had
                # been fixed -- it had been fixed in ADMISSION_CLOSER_V1.json and not here, in the
                # file the result doc calls "the cell that settles §3.4".
                "population": pop, "exit": exit_name, "band": "mid", "option": "B_balanced",
                "alpha": o.alpha, "multiplicity": o.multiplicity,
                "declared_family_size": sp.declared_family_size,
                "declared_family_id": sp.declared_family_id,
                "effective_family_size": res.family["multiplicity"]["effective_family_size"],
                "n_sleeves_judged": res.family["multiplicity"]["n_sleeves_judged_this_run"],
                "q_is_only_comparable_within_this_artifact": (
                    "BH is a step-up over the whole submitted vector, so the same p_raw gets a "
                    "different q depending on which sleeves were co-judged. This file submits AA's "
                    "32; AL_DECIDABLE_POPULATION_V1.json submits those plus three threshold "
                    "variants, and the same DECIDABLE cell reads q 1.0 here and 0.662 there on an "
                    "identical p_raw. Compare p_raw across artifacts; never q."),
            }
            ledger.record(
                mechanism="population_intersection_gate", sleeve=BTC,
                variant={"exit": exit_name, "population": pop, "band": "mid"},
                window="full_archive", spec_sha256=sp.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(v.verdict.value, "evaluated"),
                metric=v.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                note=f"AL population intersection, {key}")
            r = rows_out[key]
            print(f"  {key:34s} {r['verdict']:13s} n={r['n_trades']:4d} "
                  f"R/day {r['pooled_oos_mean_r']:8.5f} p {r['p_raw']:9.6f} "
                  f"folds {r['n_folds_evaluable']} {r['fold_means']}", flush=True)

    # ---- the reading -----------------------------------------------------------------------
    def g(k, f):
        return (rows_out.get(k) or {}).get(f)

    inter5 = rows_out.get("target_5R|INTERSECTION") or {}
    ru5 = rows_out.get("target_5R|RECORDED_UNDECIDABLE") or {}
    out = {
        "schema": "gtos.wave9.al.population_intersection.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "sleeve": BTC,
        "why": ("the two era-quality fields the spread model publishes disagree by 53x in p on "
                "this sleeve at this exit, on populations of nearly identical size (232 vs 240). "
                "The intersection is the strictest defensible population and settles whether the "
                "admission depends on the field choice."),
        "arms": rows_out,
        "the_answer": {
            "intersection_verdict_at_target_5R": inter5.get("verdict"),
            "intersection_n": inter5.get("n_trades"),
            "intersection_p_raw": inter5.get("p_raw"),
            "intersection_q": inter5.get("q_value"),
            "recorded_undecidable_n": ru5.get("n_trades"),
            "recorded_undecidable_r_per_day": ru5.get("pooled_oos_mean_r"),
            "recorded_undecidable_verdict": ru5.get("verdict"),
            "reading": (
                "ADMIT at the INTERSECTION means the admission does not depend on which "
                "era-quality field a reader prefers, and the wave-8 §4 rule can stay as it is. "
                "REJECT at the INTERSECTION means the admission exists only under the LOOSER of "
                "the two fields, and the population choice -- not the exit and not the "
                "multiplicity bill -- is what decides it."),
        },
        "fold_structure_by_population_at_target_5R": {
            p: {"n": g(f"target_5R|{p}", "n_trades"),
                "fold_means": g(f"target_5R|{p}", "fold_means"),
                "n_folds_evaluable": g(f"target_5R|{p}", "n_folds_evaluable"),
                "n_thin_folds": g(f"target_5R|{p}", "n_thin_folds"),
                "oos_mean_r_per_trade": g(f"target_5R|{p}", "oos_mean_r_per_trade"),
                "p_raw": g(f"target_5R|{p}", "p_raw")}
            for p in POPS},
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nINTERSECTION @ target_5R: {inter5.get('verdict')} n={inter5.get('n_trades')} "
          f"p={inter5.get('p_raw')} q={inter5.get('q_value')}")
    print(f"RECORDED_UNDECIDABLE @ target_5R: n={ru5.get('n_trades')} "
          f"R/day {ru5.get('pooled_oos_mean_r')} -> {ru5.get('verdict')}")
    print(f"wrote {OUT.relative_to(REPO)} ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
