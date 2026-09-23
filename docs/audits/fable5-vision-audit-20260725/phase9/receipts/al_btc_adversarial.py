"""Session AL — the adversarial pass over this session's own load-bearing claim.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_btc_adversarial.py

THE CLAIM UNDER ATTACK
----------------------
`mx_btcusd_d1_donchian_20_breakout` at `target_5R` on the RECORDED-era population ADMITS at the
sealed B_balanced alpha of 0.10 AND at A_strict's Bonferroni 0.05, at the RAISED family of 35:
n 232, pooled OOS +0.9817 R/day, p_raw 0.0011, q 0.0385, every core gate passing.

That is the first ADMIT any candidate has reached at the sealed alpha in this programme, so it gets
attacked before it gets published. Seven attacks, each of which could kill it:

  A1  **The 5R cell is a spike.** AD swept nine target cells and 5R won on ALL eras; if the ridge
      does not survive on RECORDED, the winning cell is a pick from nine and the p is a selection.
      Measured: the whole target grid on RECORDED, with plateau statistics.

  A2  **`RECORDED` is a period selection wearing an outcome-independence argument.** The class is
      a property of the broker's bar data, so the restriction is fixed before any return is seen --
      but for this symbol it drops 86 of 318 trades, and if those 86 are the old ones and the edge
      is recent then the restriction is doing the work. Measured: the COMPLEMENT's economics, and
      the year composition of both halves. The complement is the number nobody publishes and it is
      the one that decides whether this is a restriction or a selection.

  A3  **The interaction is superadditive and that is suspicious.** Each move alone is worth ~1.6x
      in p and the two together are worth ~9x. Measured: the full 2x2, so the interaction is a
      number rather than an impression.

  A4  **One spread band is not a result** (Session AG's own instruction). Measured: low / mid /
      high, and both spread compositions (AH's `v2_damped` default and v1's multiplicative), so
      the verdict is read across the model's own envelope.

  A5  **The multiplicity bill could be the wrong one.** Measured: q at every declared family in
      the artifact -- 35, 32, AA's 69, AF's 276, the estate union's 298 -- and the largest family
      that still admits. If the admission needs the SMALLEST available family it is fragile.

  A6  **Within-hypothesis selection is not priced by BH.** Nine target cells x 25 sleeves is a
      search, and BH across sleeves cannot see it. Measured: the DSR at the trial ledger's own
      measured count and across `n_trials_sweep`, which is the instrument built for exactly this.

  A7  **One fold could be carrying it.** Measured: per-fold OOS means, and the drop-worst as well
      as the drop-best retention -- the gate publishes drop-best, which answers "is one fold
      carrying the edge" and not "does the edge survive its worst fold".

Every attack's result is written to the artifact whether it supports the claim or not.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import importlib.util
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

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    measured_n_trials,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate, stats as S  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
OUT = HERE / "AL_BTC_ADVERSARIAL_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

BTC = "mx_btcusd_d1_donchian_20_breakout"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
TARGET_GRID = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)


def era_split(recs, smodel, band="mid", composition=None):
    """(RECORDED, complement) per sleeve, plus the era class of every trade."""
    keep, drop, cls_of = {}, {}, {}
    for sleeve, rs in recs.items():
        a, b = [], []
        for r in rs:
            try:
                kw = {} if composition is None else {"composition": composition}
                est = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=band, **kw)
                c = est.era_class
            except Exception:  # noqa: BLE001
                c = "unpriceable"
            cls_of[(sleeve, r.entry_utc.isoformat(), r.symbol)] = c
            (a if c == "RECORDED" else b).append(r)
        if a:
            keep[sleeve] = a
        if b:
            drop[sleeve] = b
    return keep, drop, cls_of


def summarise_pop(rows: list[dict]) -> dict:
    """Gross-R statistics on a raw row list. Gross, because the whole point of the complement
    is that its COST is the thing the restriction distrusts -- so a net comparison would beg
    the question. Both are published: net comes from the gate, gross from here."""
    if not rows:
        return {"n": 0}
    by_day = collections.defaultdict(list)
    for r in rows:
        by_day[r["decision_day"]].append(r["r_gross"])
    years = collections.Counter(r["entry_utc"][:4] for r in rows)
    return {
        "n": len(rows), "n_days": len(by_day),
        "mean_r_gross": round(statistics.fmean(r["r_gross"] for r in rows), 5),
        "mean_r_gross_per_day": round(statistics.fmean(
            statistics.fmean(v) for v in by_day.values()), 5),
        "pos_frac": round(sum(1 for r in rows if r["r_gross"] > 0) / len(rows), 4),
        "first": min(r["entry_utc"] for r in rows)[:10],
        "last": max(r["entry_utc"] for r in rows)[:10],
        "by_year": dict(sorted(years.items())),
    }


def main() -> dict:
    t0 = time.time()
    from src.costs.spread_model import load_spread_model

    smodel = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    m35 = fam.effective_size("CANDIDATE_BOOK_V1")
    m32 = fam.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN)
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()
    print(f"substrate in {time.time()-t0:.0f}s")

    o = OPTIONS["B_balanced"]

    def spec_for(band="mid", composition=None, declared=None):
        s = o.with_(spec_id=f"{o.spec_id}_al_adv", sleeve_symbol_allowlist=al,
                    spread_band=band)
        if composition is not None:
            s = s.with_(spread_composition=composition)
        if declared is None:
            s = CF.with_declared_family(s, "CANDIDATE_BOOK_V1", loaded=fam)
        else:
            s = s.with_(declared_family_size=declared)
        return s

    def gate(rows_for_btc, *, restrict, band="mid", composition=None, declared=None,
             diagnose=False):
        pop = {s: list(r) for s, r in base_rows.items()}
        pop[BTC] = rows_for_btc
        recs = {s: AD.to_records(r) for s, r in pop.items()}
        if restrict == "RECORDED":
            recs, _, _ = era_split(recs, smodel, band=band, composition=composition)
        elif restrict == "COMPLEMENT":
            _, recs, _ = era_split(recs, smodel, band=band, composition=composition)
        sp = spec_for(band, composition, declared)
        res = run_gate(recs, sp, costs=costs, server=SERVER, diagnose=diagnose)
        v = res.verdicts.get(BTC)
        if v is None:
            return {"verdict": "ABSENT", "n_trades": 0}, sp, None
        return {
            "verdict": v.verdict.value, "n_trades": v.n_trades,
            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw, "q_value": v.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not v.gates.get(g, {}).get("pass")],
            "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
            "oos_positive_fold_frac": v.gates.get("stability", {}).get(
                "oos_positive_fold_frac"),
            "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
            "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
            "effective_family_size": res.family["multiplicity"]["effective_family_size"],
        }, sp, (res, v)

    out = {
        "schema": "gtos.wave9.al.btc_adversarial.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "sleeve": BTC,
        "claim_under_attack": (
            "mx_btcusd @ target_5R on RECORDED@mid ADMITS at the sealed alpha 0.10 (BH) and at "
            "A_strict 0.05 (Bonferroni), at the raised family of 35: n 232, +0.9817 R/day, "
            "p_raw 0.0011, q 0.0385, no core gate failing."),
        "attacks": {},
    }

    # ---- A1: the target ridge on RECORDED --------------------------------------------------
    print("\nA1 the target ridge on RECORDED")
    ridge = {}
    for tr in TARGET_GRID:
        v = AD.Variant(name=f"target_{tr:g}R", family="target", target_mode="fixed_r",
                       target_r=tr)
        rows, _ = AD.resimulate(base_rows[BTC], v, series, index, costs, ACCOUNT, rule)
        r, _, _ = gate(rows, restrict="RECORDED")
        ridge[f"{tr:g}R"] = r
        print(f"  target_{tr:g}R  {r['verdict']:13s} R/day {r['pooled_oos_mean_r']:.5f} "
              f"p {r['p_raw']}", flush=True)
    aw_rows, _ = AD.resimulate(base_rows[BTC], AD.AS_WALKED, series, index, costs, ACCOUNT, rule)
    ridge["as_walked"], _, _ = gate(aw_rows, restrict="RECORDED")
    tn = AD.Variant(name="target_none", family="target", target_mode="no_target")
    tn_rows, _ = AD.resimulate(base_rows[BTC], tn, series, index, costs, ACCOUNT, rule)
    ridge["target_none"], _, _ = gate(tn_rows, restrict="RECORDED")
    vals = [(v["pooled_oos_mean_r"], k) for k, v in ridge.items()
            if v.get("pooled_oos_mean_r") is not None]
    grid_only = [(v["pooled_oos_mean_r"], k) for k, v in ridge.items()
                 if k.endswith("R") and v.get("pooled_oos_mean_r") is not None]
    admits = sorted(k for k, v in ridge.items() if v["verdict"] == "ADMIT")
    out["attacks"]["A1_target_ridge_on_RECORDED"] = {
        "question": "is target_5R a ridge on RECORDED, or a spike picked from nine cells?",
        "cells": ridge,
        "n_grid_cells": len(grid_only),
        "frac_grid_positive": round(sum(1 for v, _ in grid_only if v > 0) / len(grid_only), 4),
        "n_cells_admitting_at_alpha_0.10": len(admits),
        "cells_admitting": admits,
        "monotone_1R_to_5R": all(
            ridge[f"{a:g}R"]["pooled_oos_mean_r"] <= ridge[f"{b:g}R"]["pooled_oos_mean_r"]
            for a, b in zip(TARGET_GRID, TARGET_GRID[1:]) if b <= 5.0),
        "best_cell": max(vals)[1] if vals else None,
        "verdict": ("RIDGE -- more than one adjacent cell admits and the surface rises "
                    "monotonically into it"
                    if len(admits) > 1 else
                    "SPIKE RISK -- only one cell admits; read the level at the grid median"),
        "grid_median_r_per_day": (round(statistics.median([v for v, _ in grid_only]), 5)
                                  if grid_only else None),
    }

    # ---- A2: the complement, and the year composition --------------------------------------
    print("\nA2 the RECORDED complement")
    r5 = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    rows5, _ = AD.resimulate(base_rows[BTC], r5, series, index, costs, ACCOUNT, rule)
    recs5 = {BTC: AD.to_records(rows5)}
    kept, dropped, cls_of = era_split(recs5, smodel)
    kept_keys = {(r.entry_utc.isoformat(), r.symbol) for r in kept.get(BTC, [])}
    rec_rows = [r for r in rows5 if (r["entry_utc"], r["symbol"]) in kept_keys]
    comp_rows = [r for r in rows5 if (r["entry_utc"], r["symbol"]) not in kept_keys]
    comp_gate, _, _ = gate(rows5, restrict="COMPLEMENT")
    out["attacks"]["A2_is_RECORDED_a_period_selection"] = {
        "question": ("RECORDED drops 86 of 318 trades. Are the 86 the old ones, and is the edge "
                     "recent? If so the restriction is doing the work the exit is credited with."),
        "recorded_population": summarise_pop(rec_rows),
        "complement_population": summarise_pop(comp_rows),
        "complement_through_the_gate": comp_gate,
        "era_class_counts": dict(collections.Counter(cls_of.values())),
        "why_gross_is_published_for_both": (
            "the restriction exists because the COST model is an extrapolation off RECORDED, so "
            "comparing the two halves on NET begs the question. Gross R is the same arithmetic on "
            "both halves and is the honest axis for 'is this a period selection'."),
        "reading": (
            "if the complement's gross is similar and only its cost is untrustworthy, the "
            "restriction is what AI says it is. If the complement's GROSS is much worse, the "
            "restriction is selecting a favourable period and the improvement must be attributed "
            "to the period, not to the exit."),
    }
    print(f"  RECORDED   n={len(rec_rows):4d} gross/trade "
          f"{summarise_pop(rec_rows).get('mean_r_gross')} "
          f"{summarise_pop(rec_rows).get('first')}..{summarise_pop(rec_rows).get('last')}")
    print(f"  COMPLEMENT n={len(comp_rows):4d} gross/trade "
          f"{summarise_pop(comp_rows).get('mean_r_gross')} "
          f"{summarise_pop(comp_rows).get('first')}..{summarise_pop(comp_rows).get('last')}")
    print(f"  complement through the gate: {comp_gate['verdict']} "
          f"R/day {comp_gate.get('pooled_oos_mean_r')} p {comp_gate.get('p_raw')}")

    # ---- A3: the 2x2 -----------------------------------------------------------------------
    print("\nA3 the 2x2")
    cells22 = {}
    for exit_name, rws in (("as_walked", aw_rows), ("target_5R", rows5)):
        for pop in ("ALL_ERAS", "RECORDED"):
            r, _, _ = gate(rws, restrict=(None if pop == "ALL_ERAS" else "RECORDED"))
            cells22[f"{exit_name}|{pop}"] = r
            print(f"  {exit_name:10s} {pop:9s} n={r['n_trades']:4d} "
                  f"R/day {r['pooled_oos_mean_r']:.5f} p {r['p_raw']}")
    base_p = cells22["as_walked|ALL_ERAS"]["p_raw"]
    out["attacks"]["A3_the_2x2_interaction"] = {
        "question": "how much of the p improvement is the exit, how much the population, and is "
                    "the interaction real?",
        "cells": cells22,
        "p_ratios_vs_baseline": {
            k: (round(base_p / v["p_raw"], 3) if v.get("p_raw") else None)
            for k, v in cells22.items()},
        "superadditive": (
            None if not all(cells22[k].get("p_raw") for k in cells22) else
            (base_p / cells22["target_5R|RECORDED"]["p_raw"])
            > (base_p / cells22["target_5R|ALL_ERAS"]["p_raw"])
            * (base_p / cells22["as_walked|RECORDED"]["p_raw"])),
    }

    # ---- A4: the band and composition envelope ---------------------------------------------
    print("\nA4 the band and composition envelope")
    env = {}
    for band in ("low", "mid", "high"):
        for comp in (None, "v1_multiplicative"):
            key = f"band_{band}|comp_{comp or 'default_v2_damped'}"
            r, sp, _ = gate(rows5, restrict="RECORDED", band=band, composition=comp)
            env[key] = {**r, "spec_sha256": sp.seal()}
            print(f"  {key:44s} {r['verdict']:13s} n={r['n_trades']:4d} "
                  f"R/day {r['pooled_oos_mean_r']:.5f} p {r['p_raw']} cov {r['coverage_frac']}")
    n_admit = sum(1 for v in env.values() if v["verdict"] == "ADMIT")
    out["attacks"]["A4_band_and_composition_envelope"] = {
        "question": ("Session AG: a cell that only wins at the flat snapshot has not been shown "
                     "to win. Does it admit across the model's own envelope?"),
        "arms": env, "n_arms": len(env), "n_admitting": n_admit,
        "admits_everywhere": n_admit == len(env),
        "note": ("the RECORDED restriction is itself band-dependent -- `era_class` is read at the "
                 "band being priced -- so each arm restricts at its own band rather than "
                 "inheriting mid's population. That is the stricter reading."),
    }

    # ---- A5: q at every family --------------------------------------------------------------
    print("\nA5 q at every declared family")
    fams = {"CANDIDATE_BOOK_V2_all_declared": m35,
            "CANDIDATE_BOOK_V2_looks_taken": m32,
            "AA_historical_69": 69,
            "MECHANISM_CROSS_V1": fam.effective_size("MECHANISM_CROSS_V1"),
            "ESTATE_UNION_V1": fam.effective_size("ESTATE_UNION_V1")}
    p5 = cells22["target_5R|RECORDED"]["p_raw"]
    byfam = {}
    for name, m in fams.items():
        r, _, _ = gate(rows5, restrict="RECORDED", declared=m)
        byfam[name] = {"m": m, **r}
        print(f"  {name:34s} m={m:4d} {r['verdict']:13s} q {r['q_value']}")
    out["attacks"]["A5_q_at_every_declared_family"] = {
        "question": "does the admission need the smallest family available?",
        "by_family": byfam,
        "largest_family_that_admits_at_alpha_0.10": CF.max_size_that_admits(p5, 0.10),
        "largest_family_that_admits_at_alpha_0.05": CF.max_size_that_admits(p5, 0.05),
        "p_raw": p5,
        "reading": ("the largest admitting family is the honest headroom. If it is far above the "
                    "declared 35 the admission is not resting on the family choice."),
    }

    # ---- A6: the DSR at the measured trial count -------------------------------------------
    print("\nA6 the DSR")
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    pop = {s: list(r) for s, r in base_rows.items()}
    pop[BTC] = rows5
    recs = {s: AD.to_records(r) for s, r in pop.items()}
    recs, _, _ = era_split(recs, smodel)
    # `_dsr_sweep` evaluates ONLY `spec.n_trials_sweep` and then looks up `sweep[str(n_trials)]`,
    # so setting `n_trials` without adding it to the sweep yields `at_spec_n_trials` with the count
    # and NO dsr value -- which is what my first run published, and I read it as "verdict
    # unchanged" when it was "not computed". Found by an adversarial pass. The measured count now
    # joins the sweep, so the number the spec carries is the number the DSR is evaluated at.
    nt_n = int(nt["n_trials"])
    sp = spec_for().with_(
        n_trials=nt_n,
        n_trials_sweep=tuple(sorted(set(OPTIONS["B_balanced"].n_trials_sweep) | {nt_n})),
        n_trials_basis=f"measured_n_trials at AL: {nt['basis']}")
    res = run_gate(recs, sp, costs=costs, server=SERVER, diagnose=True)
    v = res.verdicts[BTC]
    dsr = (res.family or {}).get("dsr") or {}
    per_sleeve_dsr = (v.diagnostics or {}).get("dsr") or v.telemetry.get("dsr") or {}
    out["attacks"]["A6_dsr_at_measured_trials"] = {
        "question": ("BH across sleeves cannot see that nine target cells were searched. The DSR "
                     "is the instrument that can. What does it say at the ledger's own count?"),
        "measured_n_trials": nt,
        "verdict_with_dsr_fed": v.verdict.value,
        "family_dsr": dsr,
        "sleeve_dsr": per_sleeve_dsr,
        "spec_sha256": sp.seal(),
        "note": ("`n_trials` feeds the DSR only; it is not a second multiplicity correction, and "
                 "the gate's verdict does not read the DSR at all -- `gate.py:844-845` writes "
                 "`sv.telemetry['dsr']` and no `sv.gates[...]` key consumes it. So 'the verdict is "
                 "unchanged with n_trials fed' is true BY CONSTRUCTION and tests nothing; this "
                 "attack is INCONCLUSIVE rather than survived, and the DSR sweep below is the part "
                 "that carries information."),
        "attack_verdict": "INCONCLUSIVE -- the instrument does not reach the verdict",
        "what_the_sweep_actually_says": (
            "read `sleeve_dsr.sweep`, which IS computed: DSR falls from ~1.0 at 1 trial to the "
            "value at the measured count, `significant` at every level, on an sr_benchmark that "
            "rises with the trial count. That is a selection-deflation on the Sharpe and NOT a "
            "family-wise error rate, so it does not substitute for the multiplicity bill -- and it "
            "is the honest instrument for the >=2,260 exit cells the family-wise bill charges at "
            "zero (result doc §3.6)."),
    }
    print(f"  n_trials {nt['n_trials']} (basis {nt['basis']}), verdict {v.verdict.value}")

    # ---- A7: per-fold, and drop-WORST -------------------------------------------------------
    print("\nA7 per-fold and drop-worst")
    # The per-fold series lives at `gates.stability.fold_means`. My first version of this attack
    # guessed three other key names, found none, and published `per_fold_oos_mean_r: null` with
    # `all_folds_positive: null` -- i.e. it reported the attack as INCONCLUSIVE when the data was
    # right there. Named because a silent null in an adversarial pass is worse than a failure.
    folds = v.gates.get("stability", {}) or {}
    per_fold = folds.get("fold_means") or []
    fm = [x for x in per_fold if x is not None]
    out["attacks"]["A7_fold_structure"] = {
        "question": "is one fold carrying the edge? drop-best answers that; drop-WORST asks "
                    "whether the edge survives its own bad fold.",
        "per_fold_oos_mean_r": fm or None,
        "stability_gate": {k: vv for k, vv in v.gates.get("stability", {}).items()},
        "robustness_gate": {k: vv for k, vv in v.gates.get("robustness", {}).items()},
        "sample_gate": {k: vv for k, vv in v.gates.get("sample", {}).items()},
        "drop_worst_mean": (round((sum(fm) - min(fm)) / (len(fm) - 1), 5)
                            if len(fm) > 1 else None),
        "drop_best_mean": (round((sum(fm) - max(fm)) / (len(fm) - 1), 5)
                           if len(fm) > 1 else None),
        "all_folds_positive": (all(x > 0 for x in fm) if fm else None),
    }
    print(f"  folds {fm}")

    # ---- the verdict on the claim ------------------------------------------------------------
    survived = {
        "A1_ridge_not_spike": out["attacks"]["A1_target_ridge_on_RECORDED"][
            "n_cells_admitting_at_alpha_0.10"] > 1,
        "A2_not_a_period_selection": None,      # judgement, filled from the numbers below
        "A4_admits_across_the_envelope": out["attacks"][
            "A4_band_and_composition_envelope"]["admits_everywhere"],
        "A5_headroom_above_the_declared_family": (
            out["attacks"]["A5_q_at_every_declared_family"][
                "largest_family_that_admits_at_alpha_0.10"] > m35),
        "A7_all_folds_positive": out["attacks"]["A7_fold_structure"]["all_folds_positive"],
    }
    cg = out["attacks"]["A2_is_RECORDED_a_period_selection"]["complement_population"].get(
        "mean_r_gross")
    rg = out["attacks"]["A2_is_RECORDED_a_period_selection"]["recorded_population"].get(
        "mean_r_gross")
    survived["A2_not_a_period_selection"] = (
        None if cg is None or rg is None else bool(cg > 0 and cg >= 0.5 * rg))
    out["survived"] = survived
    out["complement_vs_recorded_gross"] = {"recorded": rg, "complement": cg,
                                           "ratio": (round(cg / rg, 4) if rg else None)}
    out["seconds_total"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nsurvived: {json.dumps(survived)}")
    print(f"wrote {OUT.relative_to(REPO)} ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
