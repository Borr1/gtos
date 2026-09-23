"""Session AN — the population rule, priced on every axis a reader could reasonably ask about.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/an_population_rule.py
    ... --stage probe      # population counts only, ~30 s
    ... --stage delta      # what the coverage repair moves, and what it does not
    ... --stage grid       # the decision grid: 4 cells x 5 populations x 4 bands x 2 options
    ... --stage widened    # AM's band-widened era table as the model of record

WHAT IS BEING DECIDED
---------------------
Session AL measured the estate's first ADMIT at the sealed alpha and then measured that it
exists on exactly ONE of four defensible era populations:

    mx_btcusd_d1_donchian_20_breakout @ target_5R, band mid, m 35, B_balanced
      ALL_ERAS      n 318   +0.547 R/day   p 0.0106   REJECT
      RECORDED      n 232   +0.982 R/day   p 0.0011   ADMIT     <- the standing rule
      DECIDABLE     n 240   +0.513 R/day   p 0.0581   REJECT    <- the model's OWN rule
      INTERSECTION  n 154   +0.892 R/day   p 0.0158   REJECT

p ranges 53x across that axis while the effect size ranges 1.9x. The rule was never chosen
deliberately — it was inherited from a driver — so Borhen is being asked to ratify a RULE, and
this file is the evidence he ratifies it against.

THREE CONTROLS, BECAUSE A RE-DERIVATION IS WORTH WHAT ITS PARITY PROVES
----------------------------------------------------------------------
C1  population parity: `era_population.filter_records` must reproduce AL's five published
    counts exactly (318/232/240/154/78 and 88/85/56/53). It does — see `--stage probe`.
C2  p_raw parity: every arm this file shares with `AL_POPULATION_INTERSECTION_V1.json` must
    reproduce AL's `p_raw`. `q` must NOT be compared: BH is a step-up over the submitted
    vector and this file co-judges a different `sub_mid_dn_revert` population, so its q is a
    different quantity by construction. That is R0 applied to a column (AL §3.4).
C3  seal separation: the four populations must produce four different `spec_sha256`. For all
    of wave 9 they produced one, because the restriction was applied before `run_gate`.

WHAT THIS FILE DOES NOT DO
--------------------------
Choose the rule, adopt the widened era table, or touch alpha, arming or the VPS. It prices.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import gzip
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

from src.costs.coverage import Coverage, weakest  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
DECL = P9 / "CANDIDATE_FAMILY_V2.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AM_SUBMID = P9 / "AM_SUBMID_TRADES.json.gz"
AL_INTERSECT = P9 / "AL_POPULATION_INTERSECTION_V1.json"
WIDENED = P9 / "SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json"
OUT = HERE / "POPULATION_RULE_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
SUBMID = "sub_mid_dn_revert"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"

#: `None` is the flat 37-day snapshot. It is carried as a CONTROL and not as a fourth band:
#: it is the basis every pre-AG number in the estate was published on, including AM's
#: `sub_mid_dn_revert` p 0.0198 and AA's own walk, so without it none of those figures can be
#: reconciled against this table. Session AG's rule stands — a cell winning only at flat has
#: not been shown to win.
BANDS = (None, "low", "mid", "high")
OPTS = ("B_balanced", "A_strict")
POPS = EP.CANDIDATE_RULES + ("RECORDED_UNDECIDABLE",)

#: Two exit configurations, because `mx_btcusd @ target_5R` and `@ target_4R` are two exits for
#: ONE sleeve and cannot both sit in the same family run. Everything else is held identical, so
#: the two configs' shared cells are a further internal control.
CONFIGS = {
    "X_btc5R": {BTC: "target_5R", XVOL: "target_4R", SUBMID: "reclocked"},
    "Y_btc4R": {BTC: "target_4R", XVOL: "target_4R", SUBMID: "reclocked"},
}
CELLS = (BTC, XVOL, SUBMID)


# =====================================================================================
# substrate
# =====================================================================================

def build_substrate() -> dict:
    """AA's 32 sleeves, with the three candidate cells' own trade populations substituted in.

    `sub_mid_dn_revert` is AM's **re-clocked** 533, not AA's 503: AM measured that AA's
    population was produced by a clock defect (`substrate._session_hour` read raw UTC) and the
    repair is merged at HEAD. Judging the sleeve on AA's rows would be judging the defect.
    """
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()

    exits = {
        "as_walked": AD.AS_WALKED,
        "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                target_r=4.0),
        "target_5R": AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                                target_r=5.0),
    }
    variants: dict[tuple[str, str], list[dict]] = {}
    for sleeve, want in ((BTC, ("target_4R", "target_5R")), (XVOL, ("target_4R",))):
        for nm in want:
            rows, _ = AD.resimulate(base[sleeve], exits[nm], series, index, costs, ACCOUNT,
                                    rule)
            variants[(sleeve, nm)] = rows
    subm = json.load(gzip.open(AM_SUBMID, "rt"))
    variants[(SUBMID, "reclocked")] = subm["trades"]["server_repaired"]
    variants[(SUBMID, "aa_authored")] = base[SUBMID]

    print(f"substrate in {time.time()-t0:.0f}s: {len(base)} sleeves, "
          f"{len(variants)} candidate cells", flush=True)
    return {"base": base, "variants": variants, "costs": costs, "allowlist": al,
            "am_n_by_clock": subm["n_by_clock"]}


def rows_for(sub: dict, config: str) -> dict[str, list[dict]]:
    out = {s: list(r) for s, r in sub["base"].items()}
    for sleeve, exit_name in CONFIGS[config].items():
        out[sleeve] = sub["variants"][(sleeve, exit_name)]
    return out


# =====================================================================================
# one gated arm
# =====================================================================================

def _row(sv, res, spec, *, pop: str, band: str | None, option: str, config: str,
         mix: dict, seconds: float) -> dict:
    """One arm, R0-stamped. Every stamp field travels; an unstamped arm is an R0 violation."""
    st = sv.gates.get("stability", {}) if sv is not None else {}
    fam = res.family["multiplicity"]
    base = {
        # --- R0: the five stamp fields plus the two this session adds -----------------
        "population": pop, "config": config, "exit": CONFIGS[config],
        "band": band if band is not None else "flat_37_day_snapshot",
        "band_is_control": band is None,
        "option": option, "alpha": spec.alpha, "multiplicity": spec.multiplicity,
        "coverage_policy": spec.coverage_policy,
        "declared_family_size": spec.declared_family_size,
        "declared_family_id": spec.declared_family_id,
        "effective_family_size": fam["effective_family_size"],
        "n_sleeves_judged": fam["n_sleeves_judged_this_run"],
        "spread_require_decidable": bool(spec.spread_require_decidable),
        "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
        "population_mix": mix, "seconds": round(seconds, 2),
    }
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    cov = sv.coverage or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "p_floor": (sv.telemetry or {}).get("p_floor", {}).get("p_floor"),
            # --- the coverage block, which is where B1250 and B1251 become visible ------
            "coverage_frac": cov.get("coverage_frac"),
            "weakest_coverage": cov.get("weakest_coverage"),
            "measured_frac": cov.get("measured_frac"),
            "n_unpriced": cov.get("n_unpriced"),
            "unpriced_reasons": cov.get("unpriced_reasons"),
            "decidability_refusals": EP.decidability_refusals(cov),
            "universe_restriction": sv.universe_restriction,
            "reasons": list(sv.reasons),
            }


def run_arm(sub: dict, config: str, pop: str, band: str | None, option: str, fam,
            ledger: TrialLedger | None, *, note: str) -> dict[str, dict]:
    """One family run; returns the three candidate cells' rows from it."""
    t0 = time.time()
    o = OPTIONS[option]
    spec = o.with_(spec_id=f"{o.spec_id}_an_{config}", sleeve_symbol_allowlist=sub["allowlist"],
                   spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    recs0 = {s: AD.to_records(r) for s, r in rows_for(sub, config).items()}
    recs, spec, mix = EP.apply(pop, recs0, spec, account=ACCOUNT)
    res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
    el = time.time() - t0
    out = {}
    for sleeve in CELLS:
        sv = res.verdicts.get(sleeve)
        out[sleeve] = _row(sv, res, spec, pop=pop, band=band, option=option, config=config,
                           mix=mix, seconds=el)
        # RECORD EVERY GATE RUN, including NOT_EVALUABLE. The first version gated on
        # `sv.p_raw is not None` and so dropped the 88 NOT_EVALUABLE arms of 240 -- 36.7 % of
        # the grid, silently, while this session's own placebo file commits to the opposite
        # standard in writing. A look taken cannot be un-taken (B1267).
        if ledger is not None and sv is not None:
            ledger.record(
                mechanism="population_rule_grid", sleeve=sleeve,
                variant={"population": pop, "band": out[sleeve]["band"], "option": option,
                         "exit": CONFIGS[config][sleeve], "config": config},
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
                metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                note=f"AN population rule, {note}")
    return out


# =====================================================================================
# stage: probe -- C1, the population parity control
# =====================================================================================

#: AL's published counts. The BTC row is read back from `AL_POPULATION_INTERSECTION_V1.json`
#: by `c2_parity`; the xvol row is NOT in that file (it is BTC-only, 15 arms) and lives in
#: `AL_CANDIDATE_DOSSIER_V1.json`, so these four are TYPED LITERALS verified by hand against it.
#: Saying so because a control that compares against a constant is a weaker control than one
#: that compares against an artifact, and the difference should not be invisible.
AL_PUBLISHED_COUNTS = {
    (BTC, "target_5R"): {"ALL_ERAS": 318, "RECORDED": 232, "DECIDABLE": 240,
                         "RECORDED_AND_DECIDABLE": 154, "RECORDED_UNDECIDABLE": 78},
    (XVOL, "target_4R"): {"ALL_ERAS": 88, "RECORDED": 85, "DECIDABLE": 56,
                          "RECORDED_AND_DECIDABLE": 53},
}


def stage_probe(sub: dict) -> dict:
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    counts: dict[str, dict] = {}
    for (sleeve, exit_name), rows in sorted(sub["variants"].items()):
        recs = AD.to_records(rows)
        key = f"{sleeve}@{exit_name}"
        counts[key] = {"n_total": len(recs)}
        for pop in POPS:
            kept, mix = EP.filter_records(pop, recs, ACCOUNT, model=sm)
            counts[key][pop] = {"n": len(kept), **mix}
        print(f"  {key:44s} " + "  ".join(
            f"{p.split('_')[0][:5]}={counts[key][p]['n']}" for p in POPS), flush=True)

    checks = []
    for (sleeve, exit_name), want in AL_PUBLISHED_COUNTS.items():
        got = counts.get(f"{sleeve}@{exit_name}", {})
        for pop, n in want.items():
            checks.append({"cell": f"{sleeve}@{exit_name}", "population": pop,
                           "al_published": n, "here": (got.get(pop) or {}).get("n"),
                           "identical": (got.get(pop) or {}).get("n") == n})
    ok = all(c["identical"] for c in checks)
    print(f"\nC1 population parity vs AL: {'IDENTICAL on all ' if ok else 'MISMATCH in '}"
          f"{len(checks)} published counts")
    return {"counts": counts, "c1_parity_vs_al": {"all_identical": ok, "checks": checks},
            "am_n_by_clock": sub["am_n_by_clock"]}


# =====================================================================================
# stage: delta -- what the B1250 coverage repair moves, and what it does not
# =====================================================================================

@contextlib.contextmanager
def pre_b1250_coverage():
    """Restore the pre-repair coverage rule in-process, for one A/B.

    Wraps `SpreadModel.estimate` and rewrites only `coverage`, recomputing it from the two
    fields the old branch read. No source is reverted and no file is touched, which is the
    lesson of AL §9's `git checkout` note. Restored on exception.
    """
    import dataclasses

    from src.costs import spread_model as SM

    original = SM.SpreadModel.estimate

    def patched(self, symbol, account, at_utc=None, **kw):
        est = original(self, symbol, account, at_utc, **kw)
        if at_utc is None:
            return est
        rec = self.record(symbol, account)
        cov = Coverage(rec["anchor_coverage"])
        fb = rec.get("era_fallback")
        if fb is not None and not est.decidable:
            cov = Coverage.MODELLED
        elif est.era_class not in ("RECORDED", "NO_BAR_HISTORY"):
            cov = weakest(cov, Coverage.MODELLED
                          if est.era_class in ("SCHEDULE", "FLOORED")
                          else Coverage.TRANSFERRED)
        if est.detail.get("era_gap_quarters"):
            cov = Coverage.MODELLED
        return dataclasses.replace(est, coverage=cov)

    SM.SpreadModel.estimate = patched
    try:
        yield
    finally:
        SM.SpreadModel.estimate = original
        assert SM.SpreadModel.estimate is original


#: The fields a verdict is BUILT from. If the coverage repair moves any of these, it moves a
#: verdict; if it moves only the coverage stamp, it does not — and that distinction is the
#: whole content of `--stage delta`.
VERDICT_FIELDS = ("verdict", "n_trades", "pooled_oos_mean_r", "p_raw", "q_value",
                  "failing_core_gates", "fold_means", "drop_best_retention",
                  "coverage_frac", "n_unpriced")
STAMP_FIELDS = ("weakest_coverage", "measured_frac")


def _same(a, b) -> bool:
    """Equality that treats NaN as equal to itself.

    The first version of this comparison used `a != b` and reported **2 verdict moves** that
    were `drop_best_retention: nan -> nan` — `sub_mid_dn_revert @ ALL_ERAS @ band_high`, whose
    retention is NaN on both sides because its drop-best pooled expectancy is 0/0. Publishing
    that as "the coverage repair moved a verdict" would have been a fabricated finding of
    exactly the kind AL §8.4 and AK §7.6 both recorded against themselves.
    """
    if isinstance(a, float) and isinstance(b, float):
        if a != a and b != b:          # both NaN
            return True
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def per_trade_coverage_census(sub: dict, config: str, pop: str, band: str) -> dict:
    """The repair's effect where it actually lives: one coverage class per TRADE.

    The gate cannot see this and that is the finding. `SleeveCoverage.weakest_coverage` is an
    aggregate over the sleeve and `measured_frac` is computed on `total_r`, so on these cells
    BOTH were already saturated before the repair — 16 of `mx_btcusd`'s 232 RECORDED trades sit
    in a gap-extrapolated era, which the pre-repair rule already forced to MODELLED, and
    BTCUSD's `slippage_r` is TRANSFERRED at every instant so `measured_frac` was already 0.0.
    A defect on 78 trades was therefore invisible in every field a verdict carries. Counted
    here directly off the model, before and after.
    """
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    out: dict[str, dict] = {}
    for sleeve in CELLS:
        recs = AD.to_records(rows_for(sub, config)[sleeve])
        kept, _ = EP.filter_records(pop, recs, ACCOUNT, model=sm)
        after: collections.Counter = collections.Counter()
        before: collections.Counter = collections.Counter()
        for rec in kept:
            try:
                est = sm.estimate(rec.symbol, ACCOUNT, rec.entry_utc, band=band)
            except Exception:                                       # noqa: BLE001
                after["unpriceable"] += 1
                before["unpriceable"] += 1
                continue
            after[est.coverage.value] += 1
            anchor = Coverage(sm.record(rec.symbol, ACCOUNT)["anchor_coverage"])
            cov = anchor
            if est.era_class not in ("RECORDED", "NO_BAR_HISTORY"):
                cov = weakest(cov, Coverage.MODELLED
                              if est.era_class in ("SCHEDULE", "FLOORED")
                              else Coverage.TRANSFERRED)
            if est.detail.get("era_gap_quarters"):
                cov = Coverage.MODELLED
            before[cov.value] += 1
        moved = sum((collections.Counter(after) - collections.Counter(before)).values())
        out[sleeve] = {"n": len(kept), "before": dict(before), "after": dict(after),
                       "n_trades_whose_class_changed": moved}
    return out


def stage_delta(sub: dict, fam) -> dict:
    """Every standing candidate, at every band, before and after B1250.

    The commission's item 5 says the wiring "can" move a standing verdict because "coverage
    degradation feeds `restrict_to_priced`". **Measured, it does not, and the mechanism is
    worth stating**: `coverage_frac` is `n_priced / n_evaluable`, and a trade is priced iff
    `cost_r` did not RAISE. A coverage CLASS never makes `cost_r` raise, and the only
    GateSpec field that reads the class is `require_measured_cost_frac`, which is 0.0 in all
    three options. So the repair makes the stamp truthful and moves no verdict by itself.
    The thing that moves verdicts is the FLAG, which is the rest of this file.
    """
    arms: dict[str, dict] = {}
    census: dict[str, dict] = {}
    for config in CONFIGS:
        for band in BANDS:
            for pop in ("ALL_ERAS", "RECORDED"):
                key = f"{config}|{pop}|{band or 'flat'}"
                after = run_arm(sub, config, pop, band, "B_balanced", fam, None,
                                note="delta after")
                with pre_b1250_coverage():
                    before = run_arm(sub, config, pop, band, "B_balanced", fam, None,
                                     note="delta before")
                for sleeve in CELLS:
                    a, b = after[sleeve], before[sleeve]
                    arms[f"{key}|{sleeve}"] = {
                        "verdict_fields_identical": all(_same(a.get(f), b.get(f))
                                                        for f in VERDICT_FIELDS),
                        "verdict_field_diffs": {f: [b.get(f), a.get(f)]
                                                for f in VERDICT_FIELDS
                                                if not _same(a.get(f), b.get(f))},
                        "stamp_field_diffs": {f: [b.get(f), a.get(f)] for f in STAMP_FIELDS
                                              if not _same(a.get(f), b.get(f))},
                        "after": {f: a.get(f) for f in VERDICT_FIELDS + STAMP_FIELDS},
                    }
                if band is not None:
                    census[key] = per_trade_coverage_census(sub, config, pop, band)
            print(f"  delta {config} band={band or 'flat':>4} done", flush=True)

    moved = {k: v for k, v in arms.items() if not v["verdict_fields_identical"]}
    stamped = {k: v["stamp_field_diffs"] for k, v in arms.items() if v["stamp_field_diffs"]}
    per_trade_moved = sum(c[s]["n_trades_whose_class_changed"]
                          for c in census.values() for s in c)
    print(f"\nB1250 delta: {len(arms)} arm-cells compared, {len(moved)} moved a VERDICT "
          f"field, {len(stamped)} moved a coverage STAMP field, and "
          f"{per_trade_moved} trade-level coverage classes changed across the census")
    return {
        "n_compared": len(arms),
        "n_verdict_fields_moved": len(moved),
        "n_stamp_fields_moved": len(stamped),
        "n_trade_level_classes_changed": per_trade_moved,
        "verdict_moves": moved,
        "stamp_moves": stamped,
        "per_trade_coverage_census": census,
        "arms": arms,
        "reading": (
            "The coverage repair (B1250) is a TRUTHFULNESS repair, not a verdict repair, and "
            "it moves NOTHING a gate currently reads -- not a verdict field and not even a "
            "coverage stamp field. Three separate reasons, all measured: (1) `coverage_frac` "
            "counts REFUSALS, not classes, so a class change cannot move it -- the "
            "commission's 'coverage degradation feeds restrict_to_priced' is not the "
            "mechanism; (2) NO code reads the coverage class into a verdict -- the field that "
            "looks as if it would, `require_measured_cost_frac`, is declared at spec.py:354 "
            "and read by nothing in src/ at all, which is stronger than this note first said "
            "('it is 0.0 in all three options', true and beside the point); (3) the "
            "sleeve-level stamps held -- but for THREE different reasons, and an earlier "
            "version of this note called all of them saturation, which is true of only 16 of "
            "the 48 arm-cells. Correctly: on the 12 FLAT cells the repair is INAPPLICABLE "
            "(model.py enters the era path only when spread_band is not None). On the 36 "
            "banded cells `weakest_coverage` is genuinely SATURATED at MODELLED. "
            "`measured_frac` is saturated at 0.0 on the 16 mx_btcusd cells only -- 16 of its "
            "232 RECORDED trades sit in a gap-extrapolated era the pre-repair rule already "
            "forced to MODELLED, and BTCUSD's slippage is TRANSFERRED at every instant. On the "
            "other 32 cells `measured_frac` is LIVE (0.051-0.173) and held by DATA rather than "
            "by construction: all 39 fully-MEASURED-cost trades across the two other sleeves "
            "happen to sit in decidable, non-gapped RECORDED eras, so no MEASURED trade was "
            "available to weaken. One undecidable era touching any of those 39 would have moved "
            "it. So 'moves nothing' is a STRUCTURAL guarantee for the verdict fields and only a "
            "MEASURED FACT for `measured_frac`. "
            "So a defect on 78 trades was invisible in EVERY field a verdict carries, which "
            "is a stronger argument for the repair than a moved verdict would have been: the "
            "only place it was ever visible is per trade, and that is what "
            "`per_trade_coverage_census` counts. The thing that moves verdicts is the FLAG "
            "(`spread_require_decidable`), measured in the grid."),
    }


# =====================================================================================
# stage: grid -- the decision package
# =====================================================================================

def redundancy_control_scope(arms: dict[str, dict]) -> dict:
    """Where the filter-vs-flag control is ARMED, and where it reports 0 by construction.

    This exists because the first version of this file published "`decidability_refusals` is 0
    on all 240 arms" as if that were a check passing 240 times. An adversarial pass over the
    claim measured that on **168 of 240** a nonzero value is structurally unreachable, and the
    correction matters because it lands on the headline:

      * 144 arms carry `spread_require_decidable: False` (every ALL_ERAS, RECORDED and
        RECORDED_UNDECIDABLE arm). `spread_model.py` raises only under
        `if require_decidable and not decidable`, so the flag being off means 0 by construction.
      * 24 more carry the flag True but sit on the flat 37-day snapshot, where
        `model.py` enters the era path only `if spread_band is not None` -- so the flag is inert
        there too. Measured, not reasoned: the undecidable BTCUSD probe prices as
        ['priced','priced'] on flat under BOTH flag values and ['unpriced','priced'] at
        low/mid/high.
      * That leaves **72 armed arms** -- the 36 DECIDABLE and 36 RECORDED_AND_DECIDABLE arms at
        low/mid/high -- and the control passes on all 72.
      * **On 0 of the 9 ADMIT arms**, because all nine are RECORDED and RECORDED does not set
        the flag. The admitting population's 78 undecidable trades (33.6 % of 232) are priced
        rather than refused, by design, and no redundancy control speaks to them.
    """
    armed = [k for k, v in arms.items()
             if v.get("spread_require_decidable") and not v.get("band_is_control")]
    inert_flag_off = [k for k, v in arms.items() if not v.get("spread_require_decidable")]
    inert_flat = [k for k, v in arms.items()
                  if v.get("spread_require_decidable") and v.get("band_is_control")]
    admits = [k for k, v in arms.items() if v.get("verdict") == "ADMIT"]
    return {
        "n_arms": len(arms),
        "n_armed": len(armed),
        "n_inert_flag_off": len(inert_flag_off),
        "n_inert_flat_band": len(inert_flat),
        "n_armed_with_a_refusal": sum(1 for k in armed
                                      if (arms[k].get("decidability_refusals") or 0) > 0),
        "control_passes_on_armed_arms": all(
            (arms[k].get("decidability_refusals") or 0) == 0 for k in armed),
        "n_admit_arms": len(admits),
        "n_admit_arms_with_the_control_armed": sum(
            1 for k in admits if arms[k].get("spread_require_decidable")),
        "note": ("`decidability_refusals == 0` is a PASS on the armed arms and a tautology on "
                 "the rest. Quote the armed denominator, never the total."),
    }


def stage_grid(sub: dict, fam, ledger: TrialLedger) -> dict:
    arms: dict[str, dict] = {}
    for config in CONFIGS:
        for option in OPTS:
            for pop in POPS:
                for band in BANDS:
                    key = f"{config}|{option}|{pop}|{band or 'flat'}"
                    got = run_arm(sub, config, pop, band, option, fam, ledger, note=key)
                    for sleeve in CELLS:
                        arms[f"{key}|{sleeve}"] = got[sleeve]
                    b = got[BTC]
                    print(f"  {key:52s} btc {b.get('verdict','?'):13s} "
                          f"n={b.get('n_trades','?'):>4} p={b.get('p_raw')} "
                          f"q={b.get('q_value')}", flush=True)
    return {"arms": arms, "redundancy_control_scope": redundancy_control_scope(arms)}


# =====================================================================================
# stage: widened -- AM's band-widened era table as the model of record
# =====================================================================================

@contextlib.contextmanager
def alternate_default_model(path: Path):
    """AM's own context manager, reused verbatim in behaviour (`am_era_anchor.py:658-678`).

    The gate charges through `cost_r` with no model parameter, so the only way to price a
    verdict against another era table is to move the module default. `_load_cached` is an
    `lru_cache` keyed on the path string, so the cache is cleared on BOTH sides.
    """
    from src.costs import spread_model as SM

    saved = SM.DEFAULT_MODEL
    SM._load_cached.cache_clear()
    try:
        SM.DEFAULT_MODEL = Path(path)
        yield
    finally:
        SM.DEFAULT_MODEL = saved
        SM._load_cached.cache_clear()
        assert SM.DEFAULT_MODEL is saved


def widened_diff() -> dict:
    """What the widened artifact actually changes, read off the two files.

    **The first version of this function read the wrong field and reported all zeros**, which
    would have published "AM's repair changes nothing" — a silent null of exactly the kind the
    wave-10 agreement §2 calls worse than a failed attack. The widening does NOT touch
    `band_halfwidth_log` (the unfloored measurement, which is a property of the data and must
    not move). It raises `band_halfwidth_log_floored`, rewrites `era_ratio_low`/`_high` from
    it, preserves the old floored value as `band_halfwidth_log_v1`, and stamps
    `era_min_consistency_basis`. `era_min_consistency_factor` is null on every widened era —
    that field belongs to the LEVEL-SHIFT variant, which is the sensitivity and not the repair.

    **AM's published "536 eras, mean increase 0.166 log, 0 become undecidable" is CORRECT, and
    the second version of this function published a wrong correction to it.** Found by an
    adversarial refuter over this session's own claim, verified here. The stamp
    (`band_halfwidth_log_v1` present) is on **585** eras; on **49** of them the delta is exactly
    0.000000 — stamped for provenance without being widened. Counting MOVEMENT rather than
    field presence gives **536** (FTMO 394 + redacted_account 142) at mean **0.166247**, AM's figures
    to the digit. The arithmetic proves the dilution: 536 x 0.166247 / 585 = **0.152322**, which
    was exactly the "corrected" mean this file published. Counting a stamp is not counting an
    effect, and the difference was 49 zeros.

    The same error moved the headroom figure, which is the load-bearing half of this block: the
    widest half-width among ACTUALLY-widened eras is **0.404800** (FTMO AUDUSD 2000Q2), not the
    0.430310 of FTMO CHFJPY 2000Q2 — which carries `band_halfwidth_log_v1 == floored == 0.43031`,
    i.e. stamped, unmoved. So headroom to the 0.5 threshold is **0.0952** log and the flip
    multiplier is **1.235x**, not 0.0697 and 1.16x — a 37 % understatement of the margin.
    """
    from src.costs.spread_model import DEFAULT_MODEL

    a = json.loads(Path(DEFAULT_MODEL).read_text())
    b = json.loads(WIDENED.read_text())
    moved, dec_flips = [], []
    by_class: collections.Counter = collections.Counter()
    by_account: collections.Counter = collections.Counter()
    per_account_hw = collections.defaultdict(list)
    mid_moves = unfloored_moves = n_stamped = n_stamped_but_unmoved = 0
    widest_after = 0.0
    widest_at = None
    for acct, syms in a["accounts"].items():
        for sym, rec in syms.items():
            other = ((b["accounts"].get(acct) or {}).get(sym) or {}).get("eras") or {}
            for q, e in (rec.get("eras") or {}).items():
                o = other.get(q)
                if not o:
                    continue
                if o.get("band_halfwidth_log_v1") is not None:
                    n_stamped += 1
                    dhw = float(o["band_halfwidth_log_floored"]) - \
                        float(o["band_halfwidth_log_v1"])
                    # MOVEMENT, not the stamp. 49 of the 585 stamped eras carry delta exactly
                    # 0 and counting them is what produced this file's own wrong correction to
                    # AM's 536 / 0.166 -- see the docstring.
                    if abs(dhw) <= 1e-12:
                        n_stamped_but_unmoved += 1
                        continue
                    moved.append(dhw)
                    by_class[e["class"]] += 1
                    by_account[acct] += 1
                    per_account_hw[acct].append(dhw)
                    if float(o["band_halfwidth_log_floored"]) > widest_after:
                        widest_after = float(o["band_halfwidth_log_floored"])
                        widest_at = f"{acct} {sym} {q}"
                if abs(float(o.get("band_halfwidth_log", 0))
                       - float(e.get("band_halfwidth_log", 0))) > 1e-12:
                    unfloored_moves += 1
                if bool(o.get("decidable", True)) != bool(e.get("decidable", True)):
                    dec_flips.append({"account": acct, "symbol": sym, "era": q,
                                      "class": e["class"],
                                      "was": bool(e.get("decidable", True)),
                                      "now": bool(o.get("decidable", True))})
                if abs(float(o["era_ratio_mid"]) - float(e["era_ratio_mid"])) > 1e-12:
                    mid_moves += 1
    thresh = float(str(b.get("decidability_rule", "")).split("<=")[-1].strip() or 0.5) \
        if "<=" in str(b.get("decidability_rule", "")) else 0.5
    mean_moved = statistics.fmean(moved) if moved else 0.0
    return {"artifact": str(WIDENED.relative_to(REPO)),
            "widened_via": ("band_halfwidth_log_floored + era_ratio_low/high; "
                            "band_halfwidth_log (unfloored) deliberately untouched"),
            "n_eras_band_widened": len(moved),
            "n_eras_stamped": n_stamped,
            "n_eras_stamped_but_delta_zero": n_stamped_but_unmoved,
            "counting_note": (
                "The count is on MOVEMENT. Counting the provenance stamp instead gives "
                f"{n_stamped}, of which {n_stamped_but_unmoved} carry delta exactly 0 -- and "
                f"{len(moved)} x {round(mean_moved, 6)} / {n_stamped} reproduces the diluted "
                "mean 0.152322 that this file wrongly published as a correction to AM."),
            "mean_halfwidth_increase_log": round(mean_moved, 6),
            "by_era_class": dict(by_class), "by_account": dict(by_account),
            "mean_increase_by_account": {k: round(statistics.fmean(v), 6)
                                         for k, v in per_account_hw.items()},
            "n_unfloored_halfwidths_moved": unfloored_moves,
            "n_decidability_flips": len(dec_flips), "decidability_flips": dec_flips[:20],
            "n_era_ratio_mid_moved": mid_moves,
            "decidability_threshold": thresh,
            "widest_halfwidth_after_widening": round(widest_after, 6),
            "widest_at": widest_at,
            "headroom_to_undecidable_log": round(thresh - widest_after, 6),
            "flip_multiplier": round(thresh / widest_after, 4) if widest_after else None,
            "headroom_note": (
                f"The widening lands {round(thresh - widest_after, 4)} log below the "
                f"decidability threshold, i.e. a hypothesis "
                f"{round(thresh / widest_after, 3) if widest_after else '?'}x larger would "
                "start flipping SCHEDULE eras to UNDECIDABLE -- and since B1250 a flip degrades "
                "Coverage to MODELLED, which it would not have done before this session. That "
                "is the coupling between the two items and the one thing a future re-sizing of "
                "AH §6 has to check. Note this is the widest ACTUALLY-widened era; FTMO CHFJPY "
                "2000Q2 sits higher at 0.43031 but was stamped with delta 0, and reading it as "
                "widened understates this margin by 37 %."),
            "already_undecidable_in_both_files": sum(
                1 for acct, syms in a["accounts"].items() for sym, rec in syms.items()
                for q, e in (rec.get("eras") or {}).items()
                if not e.get("decidable", True)),
            "am_claims": {"n_eras": 536, "mean_increase_log": 0.166,
                          "n_become_undecidable": 0},
            "am_claims_reproduce": {
                "n_eras": len(moved) == 536,
                "n_eras_here": len(moved),
                "mean_increase": abs(mean_moved - 0.166) < 5e-4,
                "mean_increase_here": round(mean_moved, 6),
                "n_become_undecidable": sum(1 for f in dec_flips if not f["now"]) == 0,
                "mid_band_unchanged": mid_moves == 0,
                "note": ("ALL FOUR of AM's claims reproduce exactly. An earlier version of this "
                         "function counted the provenance stamp instead of the movement and "
                         "published a wrong correction to AM's 536 / 0.166; that correction is "
                         "withdrawn. AM needed no correction.")}}


def stage_widened(sub: dict, fam) -> dict:
    """The same grid at low/mid/high under the widened table, against the model of record.

    Restricted to `B_balanced` and the two candidate rules a decision could plausibly land on
    (RECORDED, RECORDED_AND_DECIDABLE) plus ALL_ERAS as the control — 3 populations x 3 bands
    x 2 configs, both models. The flat control is excluded because it has no era term at all,
    so it cannot move.
    """
    diff = widened_diff()
    print(f"  widened artifact: {diff['n_eras_band_widened']} eras widened "
          f"{diff['by_account']}, mean +{diff['mean_halfwidth_increase_log']} log, "
          f"{diff['n_decidability_flips']} decidability flips, "
          f"{diff['n_era_ratio_mid_moved']} mid-band ratios moved, "
          f"headroom {diff['headroom_to_undecidable_log']} log", flush=True)
    pops = ("ALL_ERAS", "RECORDED", "RECORDED_AND_DECIDABLE")
    arms: dict[str, dict] = {}
    for config in CONFIGS:
        for pop in pops:
            for band in ("low", "mid", "high"):
                key = f"{config}|{pop}|{band}"
                base = run_arm(sub, config, pop, band, "B_balanced", fam, None,
                               note="widened base")
                with alternate_default_model(WIDENED):
                    wide = run_arm(sub, config, pop, band, "B_balanced", fam, None,
                                   note="widened arm")
                for sleeve in CELLS:
                    a, w = base[sleeve], wide[sleeve]
                    arms[f"{key}|{sleeve}"] = {
                        "verdict_of_record": a.get("verdict"),
                        "verdict_widened": w.get("verdict"),
                        "verdict_moved": a.get("verdict") != w.get("verdict"),
                        "p_of_record": a.get("p_raw"), "p_widened": w.get("p_raw"),
                        "r_per_day_of_record": a.get("pooled_oos_mean_r"),
                        "r_per_day_widened": w.get("pooled_oos_mean_r"),
                        "n_of_record": a.get("n_trades"), "n_widened": w.get("n_trades"),
                        "population_mix_of_record": a.get("population_mix"),
                        "population_mix_widened": w.get("population_mix"),
                        "band": a.get("band"), "population": pop, "option": "B_balanced",
                        "config": config, "spec_sha256": a.get("spec_sha256"),
                    }
                r = arms[f"{key}|{BTC}"]
                print(f"  {key:44s} btc {r['verdict_of_record']:13s} -> "
                      f"{r['verdict_widened']:13s} p {r['p_of_record']} -> "
                      f"{r['p_widened']}", flush=True)
    moved = {k: v for k, v in arms.items() if v["verdict_moved"]}
    return {"artifact_diff": diff, "arms": arms, "n_verdicts_moved": len(moved),
            "verdicts_moved": moved}


# =====================================================================================
# stage: folds -- WHERE the admission's evidence sits in time, which nothing else measures
# =====================================================================================

def stage_folds(sub: dict, fam) -> dict:
    """The admitting cell's fold structure: chronological decay, and where the disputed 78 sit.

    WHY THIS EXISTS, AND IT IS A GAP A COMPLETENESS CRITIC FOUND IN THIS SESSION'S OWN OUTPUT.
    Everything else here prices the admission POOLED — R/day, p, the disputed trades' gross.
    Pooled statistics cannot answer the two questions an owner asks about a candidate that
    might carry money: is the edge still there recently, and is it concentrated where the
    evidence is weakest? Both are measurable from the arm's own folds and neither was published.

    `fold_rule="equal_calendar_folds_over_sleeve_span"`, so the folds are equal calendar blocks
    in TIME ORDER and fold 0 is consumed as the initial train block. Two things fall out:

    * **the ADMIT decays chronologically** -- fold means 1.134, 1.512, 1.866, 0.284, 0.112, so
      the two most recent folds average 13.2 % of the first three, on 34.5 % of the trades. Every
      gate still passes, because `stability` counts only the SIGN of a fold mean;
    * **the disputed 78 are concentrated in the early folds** -- 53 of 78 in folds 1-2, fold 2 at
      90.5 % disputed and carrying the second-highest fold mean, while folds 3 and 4 contain
      none. So the RECORDED-vs-BOTH difference is a FOLD-STRUCTURE difference and not only a
      pooled-mean one: dropping the 78 takes fold positivity 5/5 -> 3/5, which is what moves
      p 0.0011 -> 0.0158.

    Neither fact changes which population admits. Both belong in front of Borhen.
    """
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    o = OPTIONS["B_balanced"]
    rows = AD.to_records(rows_for(sub, "X_btc5R")[BTC])
    rec_pop, _ = EP.filter_records("RECORDED", rows, ACCOUNT, model=sm)
    disputed = {(r.symbol, r.entry_utc) for r in
                EP.filter_records("RECORDED_UNDECIDABLE", rows, ACCOUNT, model=sm)[0]}
    spec = o.with_(spec_id=f"{o.spec_id}_an_folds", spread_band="mid",
                   sleeve_symbol_allowlist={BTC: sub["allowlist"][BTC]})
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    sv = run_gate({BTC: rec_pop}, spec, costs=sub["costs"], server=SERVER,
                  diagnose=True).verdicts[BTC]
    means = sv.gates["stability"]["fold_means"]
    scored = [f for f in ((sv.diagnostics or {}).get("by_fold") or []) if f.get("oos_start")]

    def _d(s):
        return dt.date.fromisoformat(str(s)[:10])

    out = []
    for i, f in enumerate(scored):
        inw = [r for r in rec_pop
               if _d(f["oos_start"]) <= r.entry_utc.date() <= _d(f["oos_end"])]
        nd = sum(1 for r in inw if (r.symbol, r.entry_utc) in disputed)
        out.append({
            "fold_id": f.get("fold_id"), "oos_start": str(f["oos_start"])[:10],
            "oos_end": str(f["oos_end"])[:10], "n_trades": len(inw),
            "n_disputed": nd, "disputed_share": round(nd / len(inw), 4) if inw else None,
            "gross_r_per_trade": round(statistics.fmean(r.r_gross for r in inw), 4)
            if inw else None,
            "fold_mean_r_per_day": means[i] if i < len(means) else None,
            "status": f.get("status"),
        })
    first3 = statistics.fmean(means[:3])
    last2 = statistics.fmean(means[3:])
    n_last2 = sum(r["n_trades"] for r in out[3:])
    return {
        "sleeve": BTC, "exit": "target_5R", "population": "RECORDED", "band": "mid",
        "option": "B_balanced", "verdict": sv.verdict.value, "p_raw": sv.p_raw,
        "spec_sha256": spec.seal(), "scope": "SOLO (p_raw is sibling-independent)",
        "fold_rule": spec.fold_rule, "n_folds": spec.n_folds,
        "folds": out,
        "chronological_decay": {
            "mean_fold_r_per_day_first_three": round(first3, 4),
            "mean_fold_r_per_day_last_two": round(last2, 4),
            "ratio": round(last2 / first3, 4),
            "recent_window": f"{out[3]['oos_start']} .. {out[4]['oos_end']}",
            "n_trades_in_last_two": n_last2,
            "share_of_trades": round(n_last2 / len(rec_pop), 4),
            "why_no_gate_sees_it": (
                "`stability` counts the SIGN of a fold mean, not its level, so a 7.6x decay "
                "across chronological folds passes every gate. `min_oos_positive_fold_frac` is "
                "5/5 here."),
        },
        "disputed_concentration": {
            "n_disputed_total": len(disputed),
            "n_in_first_two_folds": sum(r["n_disputed"] for r in out[:2]),
            "folds_with_zero_disputed": [r["fold_id"] for r in out if r["n_disputed"] == 0],
            "max_share_fold": max(out, key=lambda r: r["disputed_share"] or 0)["fold_id"],
            "max_share": max((r["disputed_share"] or 0) for r in out),
            "reading": (
                "The RECORDED-vs-RECORDED_AND_DECIDABLE difference is a FOLD-STRUCTURE "
                "difference, not only a pooled-mean one. Dropping the 78 removes most of two "
                "early folds and takes fold positivity 5/5 -> 3/5, which is what moves p "
                "0.0011 -> 0.0158. The pooled statement 'their gross is +1.0196 against the "
                "clean 154's +1.0263' is true and does not carry that."),
        },
    }


# =====================================================================================
# stage: clockband -- the comparator this session first published a conclusion WITHOUT
# =====================================================================================

def stage_clockband(sub: dict, fam, ledger: TrialLedger | None) -> dict:
    """`sub_mid_dn_revert` under BOTH clocks at all four bands.

    WHY THIS STAGE EXISTS, AND IT IS A CORRECTION TO THIS SESSION'S OWN CLAIM.
    The grid carries only the RE-CLOCKED arm, so it measures the sleeve's absolute p at each
    band and NOT the clock delta. On that evidence this session first wrote *"the re-clock
    improvement is a flat-snapshot artefact"* — a statement about a DELTA, supported only by
    LEVELS. An adversarial refuter measured the missing arm and the conclusion inverts:

      band   authored p -> reclocked p   x closer   d(R/day)   expectancy gate
      flat   0.197480 -> 0.019798          9.975    +0.0988    both pass
      low    0.642836 -> 0.242876          2.647    +0.1182    FAIL -> PASS
      mid    0.741026 -> 0.352365          2.103    +0.1223    FAIL -> PASS
      high   0.856114 -> 0.533447          1.605    +0.1298    both fail

    The improvement weakens in p and GROWS in R/day, and at low and mid it is a sign flip on
    the expectancy gate that does not exist at flat. So charging the measured era cost makes
    AM's B1200 clock repair matter MORE, not less. What IS flat-only is the sleeve's nearness to
    ADMISSION: 6.93x the BH rank-1 bar at flat becomes 123.33x at mid, a 17.80x proximity loss.
    Those are different sentences and only the second one is supportable.

    Gated SOLO for the same reason `an_econ_placebo` is: `p_raw` and every per-sleeve gate input
    are independent of siblings, and this stage compares `p_raw`. Control: the authored arm at
    flat must reproduce AM's own published `authored_utc` figures, which it does to full
    precision.
    """
    o = OPTIONS["B_balanced"]
    rows: dict[str, dict] = {}
    for band in BANDS:
        for clock in ("authored_utc", "server_repaired"):
            spec = o.with_(spec_id=f"{o.spec_id}_an_clockband_{clock}", spread_band=band,
                           sleeve_symbol_allowlist={SUBMID: sub["allowlist"][SUBMID]})
            spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
            recs = {SUBMID: AD.to_records(sub["variants"][
                (SUBMID, "aa_authored" if clock == "authored_utc" else "reclocked")])}
            res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=False)
            sv = res.verdicts[SUBMID]
            key = f"{band or 'flat'}|{clock}"
            rows[key] = {
                "band": band or "flat_37_day_snapshot", "clock": clock,
                "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                "pooled_oos_mean_r": sv.pooled_oos_mean_r, "p_raw": sv.p_raw,
                "q_value": sv.q_value,
                "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                   "robustness", "significance")
                                       if not sv.gates.get(g, {}).get("pass")],
                "option": "B_balanced", "population": "ALL_ERAS",
                "declared_family_size": spec.declared_family_size,
                "spec_sha256": spec.seal(), "scope": "SOLO",
            }
            if ledger is not None and sv.p_raw is not None:
                ledger.record(
                    mechanism="submid_clock_by_band", sleeve=SUBMID,
                    variant={"clock": clock, "band": band or "flat", "option": "B_balanced",
                             "population": "ALL_ERAS"},
                    window="full_archive", spec_sha256=spec.seal(),
                    outcome={"ADMIT": "admitted", "REJECT": "rejected",
                             "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value,
                                                                   "evaluated"),
                    metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                    note=f"AN clock x band, {key}")
            print(f"  {key:28s} {sv.verdict.value:8s} n {sv.n_trades:>4} "
                  f"R/day {sv.pooled_oos_mean_r:+.5f} p {sv.p_raw:.6f}", flush=True)

    bar = OPTIONS["B_balanced"].alpha / 35
    delta = {}
    for band in BANDS:
        b = band or "flat"
        a_, r_ = rows[f"{b}|authored_utc"], rows[f"{b}|server_repaired"]
        delta[b] = {
            "p_authored": a_["p_raw"], "p_reclocked": r_["p_raw"],
            "x_closer_in_p": round(a_["p_raw"] / r_["p_raw"], 4),
            "r_per_day_authored": a_["pooled_oos_mean_r"],
            "r_per_day_reclocked": r_["pooled_oos_mean_r"],
            "delta_r_per_day": round(r_["pooled_oos_mean_r"] - a_["pooled_oos_mean_r"], 6),
            "expectancy_gate_flip": ("expectancy" in a_["failing_core_gates"]
                                     and "expectancy" not in r_["failing_core_gates"]),
            "x_the_bh_rank1_bar_reclocked": round(r_["p_raw"] / bar, 3),
        }
    prox = round(rows["mid|server_repaired"]["p_raw"] / rows["flat|server_repaired"]["p_raw"], 3)
    am = json.loads((P9 / "SUBMID_RECLOCK_V1.json").read_text())
    pub = (am.get("solo_gate") or {}).get("runs") or am.get("runs") or {}
    ctl = {}
    for clock in ("authored_utc", "server_repaired"):
        p = (pub.get(clock) or {})
        ctl[clock] = {
            "am_published_p_raw": p.get("p_raw"), "here_p_raw": rows[f"flat|{clock}"]["p_raw"],
            "identical_1e12": (p.get("p_raw") is not None
                              and abs(p["p_raw"] - rows[f"flat|{clock}"]["p_raw"]) < 1e-12),
            "am_published_r_per_day": p.get("pooled_oos_mean_r"),
            "here_r_per_day": rows[f"flat|{clock}"]["pooled_oos_mean_r"]}
    print(f"\n  proximity loss flat->mid: {prox}x   "
          f"control vs AM at flat: {[c['identical_1e12'] for c in ctl.values()]}")
    return {
        "arms": rows, "clock_delta_by_band": delta,
        "proximity_loss_flat_to_mid": prox,
        "control_vs_am_at_flat": ctl,
        "reading": (
            "Two different claims, and only one is supportable. The sleeve's NEARNESS TO "
            f"ADMISSION is flat-only: {delta['flat']['x_the_bh_rank1_bar_reclocked']}x the BH "
            f"rank-1 bar at flat becomes {delta['mid']['x_the_bh_rank1_bar_reclocked']}x at mid, "
            f"a {prox}x proximity loss. The RE-CLOCK IMPROVEMENT is not flat-only at all: it "
            "weakens in p (9.975x -> 2.103x) and GROWS in R/day (+0.0988 -> +0.1223), and at "
            "low and mid it is a sign flip on the expectancy gate that does not exist at flat. "
            "This session's first draft said the improvement was the artefact; that was a claim "
            "about a delta supported only by levels, and it is withdrawn."),
    }


# =====================================================================================
# stage: econ -- is `decidable` the right INSTRUMENT? (a proposal, priced, not adopted)
# =====================================================================================
#
# `decidable` is `max(band_halfwidth_log, class_floor) <= 0.5` -- a threshold on the spread's
# own LOG width. An admission does not ask that. It asks whether the cost uncertainty is small
# **relative to R**, and those two orderings are not the same: a 204,058x band on a quantity
# that is 0.9 % of a crypto risk unit moves the charged cost by 0.0122 R, while a 1.20x band on
# an index sleeve with a tight stop can move it by more.
#
# So the scale-correct form of the same question is the CHARGED range: how much does `total_r`
# move between `band_low` and `band_high` for THIS trade? It is outcome-independent (it reads
# only cost, never a return), it is in the units a verdict is in, and it needs no new data.
#
# This is published as a PROPOSAL over a tau sweep and NOT as a ratified rule, deliberately:
# picking one tau after seeing which tau admits is the exact selection this whole apparatus
# exists to prevent. Borhen sees the curve.
TAUS = (0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.50)


def cost_range_r(rec, costs, band_lo: str = "low", band_hi: str = "high") -> float | None:
    """|total_r(band_high) - total_r(band_low)| for one trade, or None if unpriceable."""
    from src.costs import cost_r

    try:
        args = dict(sl_distance_price=rec.sl_distance_price, entry_price=rec.entry_price,
                    side=("LONG" if rec.direction > 0 else "SHORT"), entry_utc=rec.entry_utc,
                    costs=costs)
        lo = cost_r(rec.symbol, ACCOUNT, rec.features["hold_hours"], spread_band=band_lo,
                    **args).total_r.value
        hi = cost_r(rec.symbol, ACCOUNT, rec.features["hold_hours"], spread_band=band_hi,
                    **args).total_r.value
    except Exception:                                                   # noqa: BLE001
        return None
    return abs(hi - lo)


def stage_econ(sub: dict, fam, ledger: TrialLedger | None) -> dict:
    """The inversion, then the sweep.

    Part 1 measures whether `decidable` orders trades the same way economic determinacy does.
    Part 2 gates the candidates under `RECORDED AND cost_range <= tau` at every tau, so the
    proposal is priced rather than asserted.
    """
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    costs = sub["costs"]

    # ---- part 1: is the ordering the same? -------------------------------------------
    groups: dict[str, dict[str, list[float]]] = {}
    ranges: dict[str, dict[int, float]] = {}
    for config in ("X_btc5R",):
        for sleeve in CELLS:
            recs = AD.to_records(rows_for(sub, config)[sleeve])
            g: dict[str, list[float]] = collections.defaultdict(list)
            per: dict[int, float] = {}
            for i, rec in enumerate(recs):
                rng = cost_range_r(rec, costs)
                if rng is None:
                    continue
                try:
                    est = sm.estimate(rec.symbol, ACCOUNT, rec.entry_utc, band="mid")
                except Exception:                                       # noqa: BLE001
                    continue
                per[i] = rng
                g[f"{est.era_class}/{'dec' if est.decidable else 'UNDEC'}"].append(rng)
                g["ALL"].append(rng)
            groups[sleeve] = {k: sorted(v) for k, v in g.items()}
            ranges[sleeve] = per
    summary = {
        sleeve: {k: {"n": len(v), "median_cost_range_r": round(statistics.median(v), 6),
                     # Nearest-rank on a SORTED list, ceil-indexed. The first version used
                     # `int(0.95*len(v)) - 1`, which on small groups returns an index BELOW the
                     # median -- two published p95s sat under their own medians (B1267).
                     "p95_cost_range_r": round(v[min(len(v) - 1,
                                                     max(0, -(-95 * len(v) // 100) - 1))], 6),
                     "frac_within": {str(t): round(sum(1 for x in v if x <= t) / len(v), 4)
                                     for t in TAUS}}
                 for k, v in g.items() if v}
        for sleeve, g in groups.items()}

    btc_undec = summary[BTC].get("RECORDED/UNDEC", {}).get("median_cost_range_r")
    sub_sched = summary[SUBMID].get("SCHEDULE/dec", {}).get("median_cost_range_r")
    # Within-sleeve and pooled ordering, because the cross-sleeve comparison alone does NOT
    # support the conclusion an earlier version of this block drew from it.
    order = {}
    for sleeve, g in groups.items():
        dec = sorted(v for k, kk in g.items() if k != "ALL" and k.endswith("/dec")
                     for v in kk)
        und = sorted(v for k, kk in g.items() if k != "ALL" and k.endswith("/UNDEC")
                     for v in kk)
        if dec and und:
            order[sleeve] = {
                "decidable_median_r": round(statistics.median(dec), 6), "n_decidable": len(dec),
                "undecidable_median_r": round(statistics.median(und), 6),
                "n_undecidable": len(und),
                "undecidable_over_decidable": round(statistics.median(und)
                                                    / statistics.median(dec), 3),
                "ordering_correct": statistics.median(und) > statistics.median(dec)}
    pooled_d = sorted(v for s in order for k, kk in groups[s].items()
                      if k != "ALL" and k.endswith("/dec") for v in kk)
    pooled_u = sorted(v for s in order for k, kk in groups[s].items()
                      if k != "ALL" and k.endswith("/UNDEC") for v in kk)
    inversion = {
        "headline": "MISCALIBRATED ACROSS SLEEVES, NOT INVERTED WITHIN THEM",
        "withdrawn_claim": (
            "An earlier version of this block read the cross-sleeve ratio below as 'the "
            "orderings are close to INVERTED'. An adversarial pass refuted it and the numbers "
            "agree: `decidable` orders cost range in the CORRECT direction in EVERY sleeve "
            "(undecidable wider) and pooled. 6.383x is max(accepted median)/min(rejected "
            "median) -- rank 1 of the 50 accepted-vs-rejected group pairs, of which only 5 "
            "have accepted wider. 'Inverted' is withdrawn."),
        "btc_recorded_UNDECIDABLE_median_cost_range_r": btc_undec,
        "submid_SCHEDULE_DECIDABLE_median_cost_range_r": sub_sched,
        "cross_sleeve_extreme_ratio": round(sub_sched / btc_undec, 3)
        if (btc_undec and sub_sched) else None,
        "within_sleeve_ordering": order,
        "pooled": {"decidable_median_r": round(statistics.median(pooled_d), 6),
                   "undecidable_median_r": round(statistics.median(pooled_u), 6),
                   "undecidable_over_decidable": round(statistics.median(pooled_u)
                                                       / statistics.median(pooled_d), 3),
                   "n": len(pooled_d) + len(pooled_u)} if pooled_d and pooled_u else {},
        "reading": (
            "The defect is the THRESHOLD'S LEVEL, not its direction. Within every sleeve "
            "`decidable` correctly separates narrow from wide -- mx_btcusd 8.83x, "
            "sub_xvol_pullback 5.09x, sub_mid_dn_revert 1.55x, pooled 3.02x, Spearman(flag, "
            "cost_range) = -0.2249. What is wrong is that one fixed log threshold means "
            "different amounts of R on different sleeves: sub_mid_dn_revert's ACCEPTED trades "
            f"sit at {sub_sched} R median while mx_btcusd's REJECTED trades sit at {btc_undec} "
            "R, so the same flag tolerates 1.9x more cost uncertainty on one sleeve than it "
            "refuses on another. A threshold in log-spread cannot be calibrated once for a "
            "0.9 %-of-R spread and a 6 %-of-R spread; a threshold in R can."),
    }

    # ---- part 2: gate under RECORDED and cost_range <= tau ---------------------------
    arms: dict[str, dict] = {}
    o = OPTIONS["B_balanced"]
    for config in CONFIGS:
        for tau in TAUS:
            spec = o.with_(spec_id=f"{o.spec_id}_an_{config}|pop=RECORDED_AND_ECON_TAU{tau:g}",
                           sleeve_symbol_allowlist=sub["allowlist"], spread_band="mid")
            spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
            recs0 = {s: AD.to_records(r) for s, r in rows_for(sub, config).items()}
            kept: dict[str, list] = {}
            mix: collections.Counter = collections.Counter()
            for s, rs in recs0.items():
                keep = []
                for rec in rs:
                    try:
                        est = sm.estimate(rec.symbol, ACCOUNT, rec.entry_utc, band="mid")
                    except Exception:                                   # noqa: BLE001
                        keep.append(rec)
                        mix["unpriceable"] += 1
                        continue
                    if est.era_class != "RECORDED":
                        mix["dropped_not_recorded"] += 1
                        continue
                    rng = cost_range_r(rec, costs)
                    if rng is None or rng > tau:
                        mix["dropped_cost_range"] += 1
                        continue
                    keep.append(rec)
                    mix["kept"] += 1
                if keep:
                    kept[s] = keep
            res = run_gate(kept, spec, costs=costs, server=SERVER, diagnose=True)
            for sleeve in CELLS:
                sv = res.verdicts.get(sleeve)
                arms[f"{config}|tau_{tau:g}|{sleeve}"] = _row(
                    sv, res, spec, pop=f"RECORDED_AND_ECON_TAU{tau:g}", band="mid",
                    option="B_balanced", config=config, mix=dict(mix), seconds=0.0)
                if ledger is not None and sv is not None and sv.p_raw is not None:
                    ledger.record(
                        mechanism="population_rule_econ_tau_sweep", sleeve=sleeve,
                        variant={"population": f"RECORDED_AND_ECON_TAU{tau:g}", "band": "mid",
                                 "option": "B_balanced", "config": config,
                                 "exit": CONFIGS[config][sleeve]},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value,
                                                                       "evaluated"),
                        metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                        note=f"AN econ tau sweep, tau={tau:g}, {config}")
            b = arms[f"{config}|tau_{tau:g}|{BTC}"]
            print(f"  {config} tau {tau:<5g} btc {b.get('verdict','?'):13s} "
                  f"n={b.get('n_trades','?'):>4} p={b.get('p_raw')}", flush=True)

    admits = sorted(k for k, v in arms.items() if v.get("verdict") == "ADMIT")
    return {
        "status": "PROPOSAL -- priced over a tau sweep, NOT adopted and NOT a ratified rule",
        "taus": list(TAUS),
        "instrument": ("|total_r(band_high) - total_r(band_low)| per trade, in R. "
                       "Outcome-independent: it reads only cost."),
        "cost_range_by_era_quality": summary,
        "the_inversion": inversion,
        "arms": arms,
        "n_admit_arms": len(admits), "admit_arms": admits,
        "why_no_tau_is_recommended": (
            "Choosing tau after seeing which tau admits is the selection this apparatus "
            "exists to prevent. The curve is published; the point is Borhen's, and it should "
            "be fixed on a materiality argument in R rather than on a p-value."),
    }


# =====================================================================================
# the reading
# =====================================================================================

def c2_parity(grid: dict) -> dict:
    """C2: this file's `p_raw` against AL's, on every arm the two share.

    Shared arms are `X_btc5R | B_balanced | <pop> | mid`, which is exactly AL's
    `target_5R|<pop>` at band mid, family 35. `q` is deliberately NOT compared.
    """
    al = json.loads(AL_INTERSECT.read_text())["arms"]
    name = {"ALL_ERAS": "ALL_ERAS", "RECORDED": "RECORDED", "DECIDABLE": "DECIDABLE",
            "RECORDED_AND_DECIDABLE": "INTERSECTION",
            "RECORDED_UNDECIDABLE": "RECORDED_UNDECIDABLE"}
    checks = []
    for pop, al_pop in name.items():
        a = al.get(f"target_5R|{al_pop}") or {}
        h = grid["arms"].get(f"X_btc5R|B_balanced|{pop}|mid|{BTC}") or {}
        ap, hp = a.get("p_raw"), h.get("p_raw")
        checks.append({
            "population": pop, "al_arm": f"target_5R|{al_pop}",
            "al_p_raw": ap, "here_p_raw": hp,
            "al_n": a.get("n_trades"), "here_n": h.get("n_trades"),
            "al_r_per_day": a.get("pooled_oos_mean_r"),
            "here_r_per_day": h.get("pooled_oos_mean_r"),
            "p_identical_1e9": (ap is not None and hp is not None
                                and abs(ap - hp) < 1e-9),
            "n_identical": a.get("n_trades") == h.get("n_trades"),
            "al_q": a.get("q_value"), "here_q": h.get("q_value"),
            "q_identical": (a.get("q_value") is not None and h.get("q_value") is not None
                            and abs(a["q_value"] - h["q_value"]) < 1e-12),
            "q_note": (
                "R0 applied to a column: BH is a step-up over the whole submitted vector, so "
                "the same p_raw MAY get a different q depending on which sleeves were "
                "co-judged, and this file co-judges AM's re-clocked sub_mid_dn_revert (533) "
                "where AL co-judged AA's (503). MEASURED, and the first version of this note "
                "over-claimed: q here is IDENTICAL to AL's on all five arms to full precision, "
                "so the substitution did not in fact move any rank that matters. The rule is "
                "that q NEED NOT travel, not that it cannot -- 'different by construction' was "
                "falsified by this artifact's own five rows."),
            "q_identical_to_al": None,
        })
    return {"checks": checks,
            "all_p_identical": all(c["p_identical_1e9"] for c in checks),
            "all_n_identical": all(c["n_identical"] for c in checks)}


def c3_seals(grid: dict) -> dict:
    """C3: four populations, four seals. For all of wave 9 they were one."""
    by_pop = collections.defaultdict(set)
    for k, v in grid["arms"].items():
        if v.get("spec_sha256"):
            by_pop[(v["config"], v["option"], v["band"])].add(
                (v["population"], v["spec_sha256"]))
    collisions = []
    for ctx, pairs in by_pop.items():
        seals = collections.Counter(s for _, s in pairs)
        for seal, n in seals.items():
            if n > 1:
                collisions.append({"context": list(ctx), "seal": seal, "n_populations": n})
    return {"n_contexts": len(by_pop), "n_seal_collisions": len(collisions),
            "collisions": collisions,
            "why": ("AL's three implementations restricted the population BEFORE run_gate, so "
                    "two runs on two populations produced the same spec_sha256. "
                    "`era_population.spec_for` stamps the rule into `spec_id`, which "
                    "`canonical()` hashes.")}


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["all", "probe", "delta", "grid", "widened", "econ",
                             "clockband", "folds"])
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()
    t0 = time.time()

    fam = CF.load_candidate_family(DECL)
    ledger = None if args.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AN")
    sub = build_substrate()

    doc: dict = {
        "schema": "gtos.wave10.an.population_rule.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AN", "blocks": "B1250-B1299",
        "account": ACCOUNT, "server": SERVER,
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "declared_family": {"file": str(DECL.relative_to(REPO)), "sha256": fam.sha256,
                            "family_id": "CANDIDATE_BOOK_V1",
                            "all_declared": fam.family("CANDIDATE_BOOK_V1").size_for(
                                CF.ALL_DECLARED),
                            "looks_taken": fam.family("CANDIDATE_BOOK_V1").size_for(
                                CF.LOOKS_TAKEN)},
        "configs": CONFIGS, "bands": [b or "flat_37_day_snapshot" for b in BANDS],
        "options": list(OPTS), "populations": list(POPS),
        "population_rules": {n: {"why": r.why, "require_decidable": r.require_decidable}
                             for n, r in EP.RULES.items()},
        "r0_note": ("Every arm carries population, config, exit, band, option, alpha, "
                    "multiplicity, declared family and spec_sha256. `q_value` is comparable "
                    "ONLY within this artifact -- never against AL's, AI's or AA's."),
    }
    if args.stage in ("all", "probe"):
        print("\n=== stage probe (C1) ===")
        doc["probe"] = stage_probe(sub)
    if args.stage in ("all", "delta"):
        print("\n=== stage delta (B1250 A/B) ===")
        doc["delta_b1250"] = stage_delta(sub, fam)
    if args.stage in ("all", "grid"):
        print("\n=== stage grid (the decision package) ===")
        doc["grid"] = stage_grid(sub, fam, ledger)
        doc["c2_p_raw_parity_vs_al"] = c2_parity(doc["grid"])
        doc["c3_seal_separation"] = c3_seals(doc["grid"])
        print(f"\nC2 p_raw parity vs AL: "
              f"{'ALL IDENTICAL' if doc['c2_p_raw_parity_vs_al']['all_p_identical'] else 'MISMATCH'}")
        print(f"C3 seal collisions: {doc['c3_seal_separation']['n_seal_collisions']}")
    if args.stage in ("all", "widened"):
        print("\n=== stage widened (AM's band-widened era table) ===")
        doc["widened"] = stage_widened(sub, fam)
    if args.stage in ("all", "folds"):
        print("\n=== stage folds (where the admission's evidence sits in time) ===")
        doc["admission_fold_structure"] = stage_folds(sub, fam)
    if args.stage in ("all", "clockband"):
        print("\n=== stage clockband (the comparator the first draft lacked) ===")
        doc["submid_clock_by_band"] = stage_clockband(sub, fam, ledger)
    if args.stage in ("all", "econ"):
        print("\n=== stage econ (is `decidable` the right instrument? a PROPOSAL) ===")
        doc["econ_proposal"] = stage_econ(sub, fam, ledger)

    doc["seconds_total"] = round(time.time() - t0, 1)
    prev = json.loads(OUT.read_text()) if OUT.is_file() and args.stage != "all" else {}
    OUT.write_text(json.dumps({**prev, **doc}, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB) "
          f"in {doc['seconds_total']}s")
    return doc


if __name__ == "__main__":
    main()
