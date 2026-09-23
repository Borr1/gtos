"""Session AL — the population the restriction SHOULD have used, and what it does to the verdict.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_decidable_population.py

THE DEFECT, MEASURED
--------------------
The wave-8 agreement §4 restricts banded pricing to `era_class == RECORDED` "until AG repairs the
era x hour product", and AI §2.6 ran the gate on exactly that population. The intent is right: keep
the eras whose cost is known and drop the ones where it is an unvalidated extrapolation.

**`era_class` and the model's `decidable` measure DIFFERENT things, and the restriction selects on
the wrong one of the two.** `era_class` records HOW an `era_ratio` was derived -- and it drives the
era term's `Coverage` (`spread_model.py:439-441`) and is the lookup key for the class half-width
floor (`build_spread_model.py:1000`) that `decidable` is computed FROM, so the two are NOT
orthogonal. `decidable` records whether the resulting band is narrow enough to decide anything:
`hw = max(band_halfwidth_log, class_floor); decidable = hw <= 0.5`
(`build_spread_model.py:1000-1004`, pinned by `tests/test_spread_model.py:107-115`).

On `mx_btcusd`'s BTCUSD eras the two fields select DIFFERENT populations:

  * **9 of 25 RECORDED quarters FAIL the model's own decidability rule** -- 2018Q2 0.910, 2018Q3
    1.293, 2019Q3 1.382, 2019Q4 0.694, **2020Q1 6.113** (whose own `capture_requirement` field
    reads "band spans 204058.1x, wider than any verdict can survive"), 2020Q3 0.746, 2020Q4 0.855,
    2021Q1 0.901, 2025Q3 0.951. All KEPT by the RECORDED restriction: **78 trades.**
  * **all 11 quarters the restriction DROPS are decidable** -- 7 SCHEDULE and 4 QUANTIZED, 10 of
    them carrying trades (2017Q2 has none): **86 trades**, 25 of which sit in the three traded
    QUANTIZED quarters at half-width 0.044-0.081.

**Do NOT read the SCHEDULE quarters' raw half-width of 0.0 as precision.** All 263 raw-0.0 eras in
the model are SCHEDULE and none is RECORDED: a SCHEDULE quarter is one backfilled constant, so
every dispersion term is identically zero BY DEGENERACY. `_measure_class_hw_floor`
(`build_spread_model.py:745-753`) exists to repair exactly that -- "the band collapses to a point on
the era where the data is least trustworthy" -- and floors it to 0.18229 (ratio 0.833-1.200), which
is what the model publishes; `test_schedule_eras_are_never_certain` enforces it. BTCUSD 2021Q3 is a
SCHEDULE quarter estimated from THREE nonzero bars, carrying 12 of the 86 dropped trades.

**The genuine hole, and it is sharper than "a field nobody passes": an undecidable RECORDED era
degrades NOTHING.** `spread_model.py:440-441` degrades `Coverage` only when
`era_class not in ("RECORDED", "NO_BAR_HISTORY")`, so 2020Q1 returns `coverage=MEASURED` on a
204,058x band and every `coverage_policy="restrict_to_priced"` consumer accepts it. Measured by
calling the model: 2020Q1 RECORDED/False/MEASURED, 2018Q3 RECORDED/False/MEASURED, 2021Q3
SCHEDULE/True/MODELLED, 2022Q1 QUANTIZED/True/TRANSFERRED. The runtime switch that WOULD refuse it
works -- `estimate(..., require_decidable=True)` raises on 2020Q1 and prices 2021Q3 -- and no
production path passes it: `src/costs/model.py:388`, the only non-test consumer of `spread_price`,
omits it; the only call sites that pass it are `tests/test_spread_model.py:193` and `:374`.

WHAT THIS FILE DOES ABOUT IT
----------------------------
It does not argue. It runs the same gate on three populations and publishes all three, because R1
says where populations disagree you publish both and name the axis:

  ALL_ERAS    every trade -- no restriction
  RECORDED    `era_class == RECORDED` -- AI's, the wave-8 agreement's
  DECIDABLE   `estimate(...).decidable` -- the spread model's OWN published rule

x three spread bands x the three sealed options. `DECIDABLE` is the honest instrument for the
question the restriction was introduced to answer, and it is strictly more principled than either
of the others: it is outcome-independent in exactly the same way (a half-width is a property of the
bar data), it is the model's own rule rather than a proxy for it, and it is not a calendar block.

Whatever it says is the finding.
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
from src.research_infra.walkforward import run_gate, stats as S  # noqa: E402
from src.research_infra.walkforward.fidelity import register_threshold_variant  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
STATE = HERE / "AL_XVOL_REACHABLE_STATE_V1.json.gz"
OUT = HERE / "AL_DECIDABLE_POPULATION_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

BTC = "mx_btcusd_d1_donchian_20_breakout"
PARENT = "sub_xvol_pullback"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
PRODUCTION_PARAMS = {"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10}
CELLS = {
    "thr_sub_xvol_pullback_vr14_s125_ac015": {"vr_xhi": 1.4, "slope_up": 1.25, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s150_ac015": {"vr_xhi": 1.4, "slope_up": 1.5, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s100_ac010": {"vr_xhi": 1.4, "slope_up": 1.0, "ac_band": 0.10},
}
POPULATIONS = ("ALL_ERAS", "RECORDED", "DECIDABLE")


def main() -> dict:
    t0 = time.time()
    import al_admission_closers as ALC  # the labelling path and cell filter, reused not copied

    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    m = fam.effective_size("CANDIDATE_BOOK_V1")
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AL")
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = dict(AD.allowlist())
    state = json.load(gzip.open(STATE, "rt"))
    srows = state["rows"]

    # the three threshold cells, at the production exit
    for member, params in CELLS.items():
        register_threshold_variant(member, parent=PARENT, params=params,
                                   production_params=PRODUCTION_PARAMS)
        keys = ALC.cell_fires(srows, params)
        rows, _ = ALC.label(srows, keys, member, series, index)
        base_rows[member] = rows
        al[member] = al[PARENT]

    r5 = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    r4 = AD.Variant(name="target_4R", family="target", target_mode="fixed_r", target_r=4.0)
    btc5, _ = AD.resimulate(base_rows[BTC], r5, series, index, costs, ACCOUNT, rule)
    btc4, _ = AD.resimulate(base_rows[BTC], r4, series, index, costs, ACCOUNT, rule)
    print(f"substrate in {time.time()-t0:.0f}s")

    def restrict(recs, pop, band):
        if pop == "ALL_ERAS":
            return recs, {}
        keep, mix = {}, collections.Counter()
        for s, rs in recs.items():
            out = []
            for r in rs:
                try:
                    est = sm.estimate(r.symbol, ACCOUNT, r.entry_utc, band=band)
                except Exception:  # noqa: BLE001
                    mix["unpriceable"] += 1
                    continue
                ok = (est.era_class == "RECORDED") if pop == "RECORDED" else bool(est.decidable)
                mix["kept" if ok else "dropped"] += 1
                if ok:
                    out.append(r)
            if out:
                keep[s] = out
        return keep, dict(mix)

    focus = [PARENT, BTC, *CELLS]
    out = {
        "schema": "gtos.wave9.al.decidable_population.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL",
        "the_defect": {
            "what": ("the wave-8 agreement §4 and AI §2.6 restrict to `era_class == RECORDED` in "
                     "order to keep the eras whose cost is known. `era_class` and `decidable` "
                     "measure DIFFERENT things and the restriction selects on the wrong one: "
                     "`era_class` records HOW an era_ratio was derived (and drives Coverage at "
                     "spread_model.py:439-441, and is the lookup key for the class half-width "
                     "floor at build_spread_model.py:1000 that `decidable` is computed FROM, so "
                     "they are NOT orthogonal), while `decidable` records whether the band is "
                     "narrow enough to decide anything: hw = max(band_halfwidth_log, "
                     "class_floor); decidable = hw <= 0.5 (build_spread_model.py:1000-1004, "
                     "pinned by tests/test_spread_model.py:107-115). The runtime switch is "
                     "`estimate(require_decidable=)`, default False, passed by no production "
                     "path -- src/costs/model.py:388 omits it and the only call sites that pass "
                     "it are tests/test_spread_model.py:193 and :374."),
            "measured_on_BTCUSD": {
                "recorded_quarters_failing_the_models_own_decidability_rule": {
                    "2018Q2": 0.9103, "2018Q3": 1.2926, "2019Q3": 1.3815, "2019Q4": 0.6935,
                    "2020Q1": 6.1131, "2020Q3": 0.7462, "2020Q4": 0.8554, "2021Q1": 0.9005,
                    "2025Q3": 0.9511},
                "quarters_the_restriction_drops_and_their_halfwidth": {
                    k: v["band_halfwidth_log"]
                    for k, v in sorted((sm.doc["accounts"]["FTMO"]["BTCUSD"]["eras"]).items())
                    if v.get("class") != "RECORDED"},
                "n_dropped_quarters_in_the_model": 11,
                "n_dropped_quarters_carrying_trades": 10,
                "do_not_read_raw_0.0_as_precision": (
                    "ALL 263 raw-0.0 eras in the model are SCHEDULE and NONE is RECORDED. A "
                    "SCHEDULE quarter is one backfilled constant, so cross-instrument dispersion, "
                    "split-half noise and D1-vs-H4 disagreement are identically zero BY "
                    "DEGENERACY. `_measure_class_hw_floor` (build_spread_model.py:745-753) exists "
                    "to repair exactly that -- 'the band collapses to a point on the era where the "
                    "data is least trustworthy' -- and floors it to 0.18229 (ratio 0.833-1.200), "
                    "which is what the model publishes; test_schedule_eras_are_never_certain "
                    "enforces it. BTCUSD 2021Q3 is a SCHEDULE quarter estimated from THREE "
                    "nonzero bars, carrying 12 of the 86 dropped trades. The 4 QUANTIZED dropped "
                    "quarters are NOT 0.0 (0.044-0.081) and the 3 traded ones hold 25 of the 86. "
                    "This correction came from an adversarial pass over this session's own first "
                    "draft, which read the degeneracy as precision."),
                "the_genuine_hole_an_undecidable_RECORDED_era_degrades_nothing": (
                    "spread_model.py:440-441 degrades Coverage only when era_class not in "
                    "('RECORDED','NO_BAR_HISTORY'), so BTCUSD 2020Q1 -- whose own "
                    "capture_requirement reads 'band spans 204058.1x, wider than any verdict can "
                    "survive' -- returns coverage=MEASURED, and every "
                    "coverage_policy='restrict_to_priced' consumer accepts it. Measured by "
                    "calling the model: 2020Q1 RECORDED/decidable False/MEASURED; 2018Q3 "
                    "RECORDED/False/MEASURED; 2021Q3 SCHEDULE/True/MODELLED; 2022Q1 "
                    "QUANTIZED/True/TRANSFERRED. estimate(require_decidable=True) refuses 2020Q1 "
                    "correctly. This is the actual unwired hole and it is stronger than 'a field "
                    "nobody passes'."),
                "the_decidability_rule_verbatim": sm.doc["decidability_rule"],
            },
            "consequence": ("the restriction of record keeps 78 of 232 BTCUSD trades in quarters "
                            "the model itself calls undecidable, and drops 86 that are all "
                            "decidable -- including every 2026 trade, the only genuinely "
                            "out-of-sample year. Neither field is 'the right one' on this "
                            "evidence; what is established is that they select different "
                            "populations and that the choice moves a verdict."),
        },
        "arms": {}, "focus_matrix": {},
    }

    for exit_btc, btc_rows in (("as_walked", base_rows[BTC]), ("target_4R", btc4),
                               ("target_5R", btc5)):
        pop_rows = {s: list(r) for s, r in base_rows.items()}
        pop_rows[BTC] = btc_rows
        recs0 = {s: AD.to_records(r) for s, r in pop_rows.items()}
        for pop in POPULATIONS:
            for band in ("low", "mid", "high"):
                recs, mix = restrict(recs0, pop, band)
                for opt in ("A_strict", "B_balanced"):
                    o = OPTIONS[opt]
                    sp = o.with_(spec_id=f"{o.spec_id}_al_decidable",
                                 sleeve_symbol_allowlist=al, spread_band=band)
                    sp = CF.with_declared_family(sp, "CANDIDATE_BOOK_V1", loaded=fam)
                    res = run_gate(recs, sp, costs=costs, server=SERVER)
                    arm = f"btc={exit_btc}|pop={pop}|band={band}|opt={opt}"
                    rows = {}
                    for s in focus:
                        v = res.verdicts.get(s)
                        rows[s] = None if v is None else {
                            "verdict": v.verdict.value, "n_trades": v.n_trades,
                            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                            "q_value": v.q_value,
                            "failing_core_gates": [g for g in (
                                "expectancy", "lifetime", "stability", "robustness",
                                "significance") if not v.gates.get(g, {}).get("pass")],
                            "fold_means": v.gates.get("stability", {}).get("fold_means"),
                            "n_folds_evaluable": v.gates.get("sample", {}).get(
                                "n_folds_evaluable"),
                            "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
                        }
                    out["arms"][arm] = {
                        "exit_btc": exit_btc, "population": pop, "band": band, "option": opt,
                        "alpha": o.alpha, "multiplicity": o.multiplicity,
                        "spec_sha256": sp.seal(),
                        "effective_family_size": res.family["multiplicity"][
                            "effective_family_size"],
                        "n_sleeves_judged": res.family["multiplicity"][
                            "n_sleeves_judged_this_run"],
                        "restriction_mix": mix,
                        "admitted": sorted(res.admitted), "focus": rows,
                    }
                    for s in focus:
                        v = res.verdicts.get(s)
                        if v is None:
                            continue
                        ledger.record(
                            mechanism="population_restriction_gate", sleeve=s,
                            variant={"exit_btc": exit_btc, "population": pop, "band": band,
                                     "option": opt},
                            window="full_archive", spec_sha256=sp.seal(),
                            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                     "NOT_EVALUABLE": "not_evaluable"}.get(
                                         v.verdict.value, "evaluated"),
                            metric=v.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                            note=f"AL decidable-population comparison, arm {arm}")
                    print(f"  {arm:56s} ADMIT {sorted(res.admitted) or '-'}", flush=True)

    # ---- the matrix a reader needs, one line per (candidate, exit, population, band) --------
    for arm, a in out["arms"].items():
        if a["option"] != "B_balanced":
            continue
        for s, r in a["focus"].items():
            if r is None or r["p_raw"] is None:
                continue
            out["focus_matrix"].setdefault(s, {})[
                f"{a['exit_btc']}|{a['population']}|{a['band']}"] = {
                    "n": r["n_trades"], "r_per_day": r["pooled_oos_mean_r"],
                    "p_raw": r["p_raw"], "q": r["q_value"], "verdict": r["verdict"]}

    admits = {a: v["admitted"] for a, v in out["arms"].items() if v["admitted"]}
    by_pop = collections.Counter()
    for a, v in out["arms"].items():
        if v["option"] == "B_balanced" and v["admitted"]:
            by_pop[v["population"]] += 1
    n_b = sum(1 for v in out["arms"].values() if v["option"] == "B_balanced")
    out["answer"] = {
        "arms_with_an_admission": admits,
        "b_balanced_admitting_arms_by_population": dict(by_pop),
        "n_b_balanced_arms": n_b,
        "reading": ("the population axis is the decision. An admission that appears under only "
                    "ONE of the three populations is a statement about that population, and the "
                    "artifact names which."),
    }
    out["seconds_total"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nB_balanced admitting arms by population: {dict(by_pop)} of {n_b} arms")
    print(f"wrote {OUT.relative_to(REPO)} ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
