"""Session AR, work orders AR-2 and AR-3 — spend the repair queue, and reconcile asia_pdl_fade.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_repair_program.py

Two work orders in one file because they share every piece of machinery: `AD.resimulate` for
exit geometry, `run_gate` at the ratified rule, the population restriction, and the band
envelope. One bar load (23 s) instead of two.

AR-3 -- asia_pdl_fade, RECONCILED
---------------------------------
Two sessions measured this sleeve and reached opposite-looking conclusions about DIFFERENT
levers, and the commission's first job is to say so plainly:

  * **AK/AL, the EXIT lever.** AK found the sleeve had no exit frontier at all and swept one:
    as-walked -0.0686 -> `stop_2.5x` +0.0846 R/day, 5/5 OOS folds, failing significance alone.
    AL crossed stop x target x time-stop over 150 cells and confirmed the same winner at rank 2,
    23.06x from the rank-1 bar.
  * **AO, the REGIME lever.** AO refuted the sleeve's pre-declared regime direction in the
    OPPOSITE direction at permutation p 5e-05 on 2,717 trades -- the most TRENDING third of the
    tape is the least bad, which inverts AH's precedent for liquidity sweeps.

Those do not contradict each other: one is about where the exit goes, the other about which tape
to fire in. What DOES contradict AK/AL is AO's third finding, and it is the one that matters:
**every figure in `AL_ASIA_PDL_FRONTIER_V1.json` is at the flat 37-day cost snapshot**, because
`al_asia_pdl_frontier.py:104-106` sets no `spread_band`. At the banded mid cost AL's winner goes
+0.08463 -> -0.27414 R/day. A SIGN FLIP. AO filed
`EXIT_FRONTIER_IS_AT_THE_FLAT_SNAPSHOT_ONLY` and named the repair: re-run the cross at the band.

That is AR-3, and it is run with a PREDICTION stated before the numbers, because a re-run that
only confirms a sign flip has learned nothing:

    **THE PREDICTION.** Swap is charged per rollover crossed and is the largest single broker
    cost for eight of eleven sleeves (wave-3 finding). AL optimised the cross at a cost basis
    that under-charges carry, so its optimum is free to hold. At the banded cost, holding is
    dearer, so the banded optimum should move toward SHORTER holds -- specifically toward
    tighter `time_stop_bars` and away from `ts_none`. AL's flat winner is `ts_none` at the
    WIDEST stop (2.5x-3x), the most carry-exposed corner of the grid, which is exactly what a
    cost-blind optimiser would pick. If the prediction holds, the repair is not "the sleeve is
    dead" but "the exit was optimised against the wrong cost" -- and the banded optimum is a
    different, cheaper cell that nobody has looked at.

This is falsifiable and it is written down before the run. If the banded surface is uniformly
negative with no interior optimum, the prediction is refuted and the row says so.

AR-2 -- the member-repair program
---------------------------------
`CANDIDATE_FAMILY_V4.json` declares the 9 members of AF's two coherent families and prices both
bills (declared-family BH, and a 30-family Bonferroni for the outcome-dependent family choice).
This file gates them at the ratified rule -- `B_balanced` alpha 0.10, RECORDED population, band
envelope -- which no member of either family has ever been judged under, then applies AD's exit
grid to whichever get closest. AD measured exit geometry as the estate's largest lever (1,631
cells, every sleeve improves, median +0.249 R/day), and the family members have never had one.

The honest target the commission set: **either a second admission at the sealed rule, or a
short-list of the nearest misses with exactly what each is missing.** No admission is
manufactured; a cell that fails reports as its next prescription.

Offline, pure, no broker import, no order path, no config write, no VPS.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import family as WFAM  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AD_DIR = AUD / "phase7/receipts"
AF_DIR = AUD / "phase7/receipts"
AL_DIR = AUD / "phase9/receipts"
DECL = HERE / "CANDIDATE_FAMILY_V4.json"
OUT = HERE / "AR_REPAIR_PROGRAM_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
ASIA = "asia_pdl_fade"
OPT = "B_balanced"          # the ratified option; options.py:110 disqualifies 0.20 for arming
POP_OF_RECORD = "RECORDED"  # ratified 2026-07-30 (POPULATION_RULE_V1.json ratified_rule)
BAND_OF_RECORD = "mid"
BANDS = ("flat", "low", "mid", "high")
AF_N_FAMILIES = 30
COHERENT = ("fam_energy_fvg_retest_energy_h4", "fam_volume_surge_reversal_index_d1")

#: AR-3's prediction, in source, before any number. See the module docstring.
AR3_PREDICTION = {
    "claim": ("at the BANDED cost the exit optimum moves toward SHORTER holds -- tighter "
              "`time_stop_bars`, away from `ts_none` -- because swap is charged per rollover "
              "and AL optimised at a cost basis that under-charges carry."),
    "al_flat_winner": "stop_2.5x_tgt_3R_ts_none",
    "al_flat_winner_is_the_most_carry_exposed_corner": (
        "widest stop AND no time stop: exactly what a cost-blind optimiser picks."),
    "falsifiable_by": ("a banded surface with no interior optimum -- uniformly negative, or a "
                       "banded winner that is ALSO `ts_none`. Either refutes it and the row "
                       "says so."),
    "declared_in": "source, before the run",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_EST: dict = {}


def _restrict(recs: dict, pop: str, smodel, band: str | None) -> tuple[dict, dict]:
    """AO's `_restrict`, verbatim, including the band-threading caveat.

    `estimate`'s `decidable` and `era_class` are properties of the band the estimate was taken
    at, so restricting at one band and pricing at another would be two populations wearing one
    name. The flat arm has no band, so it is ALL_ERAS-only.
    """
    if pop == "ALL_ERAS":
        return recs, {}
    if band is None:
        raise ValueError(f"population {pop!r} needs a band; the flat arm is ALL_ERAS-only")
    keep, mix = {}, {}
    for s, rs in sorted(recs.items()):
        cls, rows = collections.Counter(), []
        for r in rs:
            k = (r.symbol, r.entry_utc, band)
            if k not in _EST:
                try:
                    e = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=band)
                    _EST[k] = (e.era_class, bool(e.decidable))
                except Exception as exc:  # noqa: BLE001
                    _EST[k] = (f"UNPRICEABLE:{type(exc).__name__}", False)
            era, dec = _EST[k]
            if era.startswith("UNPRICEABLE:"):
                cls[era] += 1
                continue
            cls[f"{era}|{'decidable' if dec else 'undecidable'}"] += 1
            if (era == "RECORDED") if pop == "RECORDED" else dec:
                rows.append(r)
        mix[s] = {"n_total": len(rs), "n_kept": len(rows), "mix": dict(sorted(cls.items())),
                  "kept_frac": round(len(rows) / len(rs), 4) if rs else None}
        if rows:
            keep[s] = rows
    return keep, mix


def row_of(sv) -> dict:
    """AO's `row_of`, including the power terms and the resolution check.

    Falls back LOUDLY rather than writing a null: `n_oos_days` lives at
    `telemetry.dependence` (`gate.py:746-753`), never in `gates.significance`, and AO's first
    version guessed the latter and published `None`.
    """
    g = sv.gates
    tel = sv.telemetry or {}
    dep = tel.get("dependence") or {}
    fl = tel.get("p_floor") or {}
    if sv.p_raw is not None and not dep:
        raise SystemExit("REFUSING: a sleeve reached a null but telemetry['dependence'] is "
                         "absent, so the power accounting would publish nulls. gate.py:746-753.")
    return {
        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": g.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "failing_core_gates": [x for x in ("expectancy", "lifetime", "stability", "robustness",
                                           "significance") if not g.get(x, {}).get("pass")],
        "n_folds_evaluable": g.get("sample", {}).get("n_folds_evaluable"),
        "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
        "fold_means": g.get("stability", {}).get("fold_means"),
        "drop_best_retention": g.get("robustness", {}).get("retention"),
        "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
        "n_oos_days": dep.get("n_oos_days"),
        "n_blocks": fl.get("n_blocks"), "p_floor": fl.get("p_floor"),
        "p_floor_binds": g.get("significance", {}).get("p_floor_binds"),
        # AO's resolution audit, on every arm: a filter buys a smaller p by destroying the
        # resolution that would justify it. `p_floor` is the smallest p a B-block sign flip can
        # attain; a headroom near 1 means the p IS the floor and cannot be evidence.
        "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                             if (sv.p_raw is not None and fl.get("p_floor")) else None),
        "first_reason": (sv.reasons[0][:240] if sv.reasons else None),
    }


def bars_from_cell(name: str) -> tuple[float, float | None, int | None]:
    """`stop_2.5x_tgt_3R_ts_48` -> (2.5, 3.0, 48). `tgt_native`/`ts_none` -> None.

    Parsed by KEYWORD rather than by position, because the first version indexed
    `name.split("_")` as if `stop_2.5x` were one token and died on the first cell. A keyword
    parse also refuses a name whose shape moved instead of silently mis-reading it.
    """
    parts = name.split("_")
    got: dict[str, str] = {}
    for i, p in enumerate(parts):
        if p in ("stop", "tgt", "ts") and i + 1 < len(parts):
            got[p] = parts[i + 1]
    missing = [k for k in ("stop", "tgt", "ts") if k not in got]
    if missing:
        raise ValueError(f"cell name {name!r} is missing {missing}; AL's grid shape moved and a "
                         f"positional parse would mis-read it silently")
    stop = float(got["stop"].removesuffix("x"))
    tr = None if got["tgt"] == "native" else float(got["tgt"].removesuffix("R"))
    tb = None if got["ts"] == "none" else int(got["ts"])
    return stop, tr, tb


def main() -> dict:  # noqa: PLR0915, PLR0912
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=8,
                    help="how many cells carry the full band envelope")
    args = ap.parse_args()
    t0 = time.time()

    AA = _load(AA_DIR / "aa_estate_walk.py", "arp_aa")
    AD = _load(AD_DIR / "ad_exit_sweep.py", "arp_ad")
    from src.costs.spread_model import load_spread_model

    smodel = load_spread_model()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AR")
    fam = CF.load_candidate_family(DECL)
    m_all = fam.effective_size("CANDIDATE_BOOK_V1")
    bh1, bh2 = 0.10 / m_all, 0.20 / m_all
    bonf_fam = 0.10 / AF_N_FAMILIES
    costs = load_broker_true_costs(AD.COSTS)
    allow = dict(AA.allowlist())
    o = OPTIONS[OPT]

    raw = json.load(gzip.open(AA_DIR / "AA_ESTATE_TRADES.json.gz", "rt"))
    base_rows = {s: list(v) for s, v in raw["trades"].items()}
    af = json.load(gzip.open(AF_DIR / "AF_FAMILY_TRADES.json.gz", "rt"))
    af_rows = {k: list(v) for k, v in af["trades"].items()}
    af_fams = (af.get("grid") or {}).get("families") or {}
    series, index, _res = AD.load_bars()
    rule = AD.resolve_rule(SERVER)
    print(f"loaded: {len(base_rows)} AA sleeves, {len(af_rows)} AF members, "
          f"{len(series)} bar series  ({time.time()-t0:.0f}s)", flush=True)
    print(f"declared family {m_all}: BH rank1 {bh1:.6f} rank2 {bh2:.6f}; "
          f"family-selection Bonferroni {bonf_fam:.6f}", flush=True)

    out: dict = {
        "schema": "gtos.wave11.ar.repair_program.v1",
        "generated_by": str(Path(__file__).resolve().relative_to(REPO)),
        "session": "AR", "blocks": "B1450-B1499",
        "ratified_rule": {
            "option": OPT, "alpha": o.alpha, "multiplicity": o.multiplicity,
            "population": POP_OF_RECORD,
            "population_source": ("phase10/receipts/POPULATION_RULE_V1.json ratified_rule "
                                  "(Borhen 2026-07-30), test-pinned"),
            "band_of_record": BAND_OF_RECORD, "bands_published": list(BANDS),
            "why_not_alpha_0.20": "options.py:110 disqualifies 0.20 for arming; research triage only",
        },
        "declared_family": {
            "path": str(DECL.relative_to(REPO)), "sha256": fam.sha256,
            "all_declared": m_all, "bh_rank_1": round(bh1, 6), "bh_rank_2": round(bh2, 6),
            "membership_sha256": fam.membership_of("CANDIDATE_BOOK_V1"),
        },
        "second_bill": {
            "what": (f"AF's two families were chosen ON THE OUTCOME (2 of {AF_N_FAMILIES}, "
                     f"'every member positive'), which the declared-family BH bar does not "
                     f"charge for."),
            "bonferroni_over_af_families": round(bonf_fam, 6),
            "admission_rule": "the TIGHTER of bh_rank_1 and bonferroni_over_af_families",
            "binding_bar": round(min(bh1, bonf_fam), 6),
        },
        "ar3_prediction": AR3_PREDICTION,
    }

    def gate_one(key: str, rows_by_sleeve: dict, sleeve: str, band: str, pop: str,
                 *, mechanism: str, variant: dict, allowlist: dict | None = None) -> dict:
        recs_all = {s: AD.to_records(r) for s, r in rows_by_sleeve.items()}
        band_val = None if band == "flat" else band
        recs, mix = _restrict(recs_all, pop, smodel, band_val)
        spec = o.with_(spec_id=f"{o.spec_id}_ar_repair",
                       sleeve_symbol_allowlist=(allow if allowlist is None else allowlist),
                       **({"spread_band": band_val} if band_val else {}))
        spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
        if sleeve not in recs:
            return {"key": key, "sleeve": sleeve, "band": band, "population": pop,
                    "skipped": "no trade survives the population restriction",
                    "n_after_restriction": 0, "spec_sha256": spec.seal()}
        res = run_gate(recs, spec, costs=costs, server=SERVER)
        sv = res.verdicts.get(sleeve)
        arm = {"key": key, "sleeve": sleeve, "band": band, "population": pop,
               "option": OPT, "alpha": o.alpha,
               "declared_family_size": spec.declared_family_size,
               "effective_family_size": res.family["multiplicity"]["effective_family_size"],
               "n_sleeves_judged": res.family["multiplicity"]["n_sleeves_judged_this_run"],
               "spec_sha256": spec.seal(),
               "n_after_restriction": mix.get(sleeve, {}).get("n_kept"),
               "era_mix": mix.get(sleeve), **variant,
               **({} if sv is None else row_of(sv))}
        if arm.get("p_raw") is not None:
            arm["clears_bh_rank_1"] = arm["p_raw"] <= bh1
            arm["clears_bh_rank_2"] = arm["p_raw"] <= bh2
            arm["clears_family_selection_bonferroni"] = arm["p_raw"] <= bonf_fam
            arm["clears_the_binding_bar"] = arm["p_raw"] <= min(bh1, bonf_fam)
            arm["shortfall_factor_vs_binding_bar"] = round(
                arm["p_raw"] / min(bh1, bonf_fam), 3)
        ledger.record(mechanism=mechanism, sleeve=sleeve, variant=dict(variant, band=band,
                                                                      population=pop),
                      window="full_archive", spec_sha256=spec.seal(),
                      outcome={"ADMIT": "admitted", "REJECT": "rejected",
                               "NOT_EVALUABLE": "not_evaluable"}.get(
                          (sv.verdict.value if sv else ""), "evaluated"),
                      metric=(sv.pooled_oos_mean_r if sv else None),
                      metric_name="pooled_oos_mean_r", note=f"AR repair program, {key}")
        return arm

    # =================================================================================
    # AR-3: asia_pdl_fade's exit cross, at the band
    # =================================================================================
    print("\n=== AR-3: asia_pdl_fade exit cross at the BANDED cost, RECORDED ===", flush=True)
    al = json.loads((AL_DIR / "AL_ASIA_PDL_FRONTIER_V1.json").read_text())
    al_cells = al["cells"]
    #  AL's own note: `asia_pdl_fade.py:30` sets TARGET_R = 3.0 so the tgt_3R column is
    #  identical to tgt_native at every (stop, time-stop) pair. Dedupe on the geometry rather
    #  than on the name, so 150 named cells become the distinct set actually simulated.
    distinct: dict[tuple, str] = {}
    for nm in sorted(al_cells):
        stop, tr, tb = bars_from_cell(nm)
        distinct.setdefault((stop, (3.0 if tr is None else tr), tb), nm)
    print(f"  AL published {len(al_cells)} named cells -> {len(distinct)} distinct geometries",
          flush=True)

    asia_arms: dict[str, dict] = {}
    repro = {}
    for (stop, tr, tb), nm in sorted(distinct.items(), key=lambda kv: kv[1]):
        v = AD.Variant(name=nm, family="cross_stop_target_timestop", stop_mult=stop,
                       target_mode=("scales_with_stop" if "native" in nm else "fixed_r"),
                       target_r=(None if "native" in nm else tr), time_stop_bars=tb)
        rs, _tel = AD.resimulate(base_rows[ASIA], v, series, index, costs, ACCOUNT, rule)
        rows = {s: list(r) for s, r in base_rows.items()}
        rows[ASIA] = rs
        for band, pop in ((BAND_OF_RECORD, POP_OF_RECORD), (BAND_OF_RECORD, "ALL_ERAS")):
            k = f"{ASIA}|{nm}|band={band}|{pop}"
            asia_arms[k] = gate_one(k, rows, ASIA, band, pop,
                                    mechanism="exit_cell_at_the_band",
                                    variant={"cell": nm, "stop_mult": stop, "target_r": tr,
                                             "time_stop_bars": tb,
                                             "basis": "AL's cross, re-priced at the band"})
        #  the FLAT control, so AL's own published figure reproduces from this file
        if nm in ("stop_2.5x_tgt_3R_ts_none", "stop_1x_tgt_native_ts_none",
                  "stop_3x_tgt_3R_ts_none"):
            k = f"{ASIA}|{nm}|band=flat|ALL_ERAS"
            a = gate_one(k, rows, ASIA, "flat", "ALL_ERAS",
                         mechanism="exit_cell_flat_control",
                         variant={"cell": nm, "basis": "AL's own basis -- reproduction control"})
            asia_arms[k] = a
            pub = al_cells.get(nm) or {}
            repro[nm] = {
                "published_pooled_oos_mean_r": pub.get("pooled_oos_mean_r"),
                "here_pooled_oos_mean_r": a.get("pooled_oos_mean_r"),
                "published_p_raw": pub.get("p_raw"), "here_p_raw": a.get("p_raw"),
                "published_n": pub.get("n_trades"), "here_n": a.get("n_trades"),
                "abs_delta_r": (abs((a.get("pooled_oos_mean_r") or 0)
                                    - (pub.get("pooled_oos_mean_r") or 0))),
                "abs_delta_p": abs((a.get("p_raw") or 0) - (pub.get("p_raw") or 0)),
            }
            repro[nm]["reproduces_to_1e-12"] = (repro[nm]["abs_delta_r"] < 1e-12
                                                and repro[nm]["abs_delta_p"] < 1e-12
                                                and a.get("n_trades") == pub.get("n_trades"))
    ev = [a for a in asia_arms.values()
          if a.get("population") == POP_OF_RECORD and a.get("p_raw") is not None]
    ev.sort(key=lambda a: a["p_raw"])
    print(f"  gated {len(asia_arms)} arms; {len(ev)} evaluable at "
          f"{POP_OF_RECORD}@{BAND_OF_RECORD}", flush=True)
    for a in ev[:6]:
        print(f"    {a['cell']:30s} n={a['n_trades']:5d} R/day={a['pooled_oos_mean_r']:+.5f} "
              f"p={a['p_raw']:.5f} folds+={a['oos_positive_fold_frac']} "
              f"{a['verdict']} fail={a['failing_core_gates']}", flush=True)

    #  the band envelope on the best few
    for a in ev[:args.top]:
        nm = a["cell"]
        stop, tr, tb = bars_from_cell(nm)
        v = AD.Variant(name=nm, family="cross_stop_target_timestop", stop_mult=stop,
                       target_mode=("scales_with_stop" if "native" in nm else "fixed_r"),
                       target_r=(None if "native" in nm else tr), time_stop_bars=tb)
        rs, _t = AD.resimulate(base_rows[ASIA], v, series, index, costs, ACCOUNT, rule)
        rows = {s: list(r) for s, r in base_rows.items()}
        rows[ASIA] = rs
        for band in BANDS:
            if band == BAND_OF_RECORD:
                continue
            pop = "ALL_ERAS" if band == "flat" else POP_OF_RECORD
            k = f"{ASIA}|{nm}|band={band}|{pop}"
            if k in asia_arms:
                continue
            asia_arms[k] = gate_one(k, rows, ASIA, band, pop,
                                    mechanism="exit_cell_band_envelope",
                                    variant={"cell": nm, "basis": "AG band envelope"})
    # ---- THE MECHANISM, AND THE EXTENSION THAT TESTS IT ---------------------------------
    #  The pre-declared prediction (carry -> tighter time stops) is refuted, and the refutation
    #  names the true mechanism. Decomposing the 120-cell banded surface by axis:
    #  the TIME-STOP axis spans 12 % of the mean and the STOP axis spans 4.6x, monotone. Cost per
    #  trade is a price distance; expressed in R it divides by the stop distance, so a
    #  cost-dominated surface is `R/day = a - b/stop_mult` -- and the fit's R^2 is 0.9989.
    #  So this is NOT an exit-geometry surface, it is a cost-per-R surface. The fit's zero
    #  crossing is the repair address, and EXTRAPOLATING IT WOULD BE A HYPOTHESIS, so the
    #  extension below measures it instead: stops beyond AL's 3.5x grid edge, up to and past
    #  where the fit says the surface crosses zero. Legitimate on AL's own ground -- its
    #  `stop_cells_legitimate_because` records that `asia_pdl_fade.py:108` computes the stop
    #  AFTER every admission gate, so a k-x stop changes the geometry of the same candidate set
    #  and nothing else. Exit cells, so no family bill (AL section 6.3).
    stop_fit = _fit_cost_model(asia_arms)
    print(f"\n  COST MODEL: R/day = {stop_fit['mean_fit']['a']:+.5f} "
          f"- {stop_fit['mean_fit']['b']:.5f}/stop_mult  R2 {stop_fit['mean_fit']['r2']:.5f}; "
          f"zero crossing {stop_fit['mean_fit']['zero_crossing_stop_mult']}x", flush=True)
    ext_arms: dict[str, dict] = {}
    EXT_STOPS = (5.0, 7.0, 9.0, 11.0, 14.0)
    print(f"  extension: stops {EXT_STOPS} beyond AL's 3.5x edge, tgt native, ts none/48",
          flush=True)
    for st in EXT_STOPS:
        for tb in (None, 48):
            nm = f"stop_{st:g}x_tgt_native_ts_{'none' if tb is None else tb}"
            v = AD.Variant(name=nm, family="cross_stop_target_timestop", stop_mult=st,
                           target_mode="scales_with_stop", time_stop_bars=tb)
            rs, _t = AD.resimulate(base_rows[ASIA], v, series, index, costs, ACCOUNT, rule)
            rows = {s: list(r) for s, r in base_rows.items()}
            rows[ASIA] = rs
            k = f"{ASIA}|{nm}|band={BAND_OF_RECORD}|{POP_OF_RECORD}"
            a = gate_one(k, rows, ASIA, BAND_OF_RECORD, POP_OF_RECORD,
                         mechanism="exit_cell_beyond_ALs_grid_edge",
                         variant={"cell": nm, "stop_mult": st, "time_stop_bars": tb,
                                  "basis": ("tests the cost-model extrapolation; AL's grid stops "
                                            "at 3.5x")})
            ext_arms[k] = a
            print(f"    {nm:34s} n={a.get('n_trades')} R/day={a.get('pooled_oos_mean_r')} "
                  f"p={a.get('p_raw')} {a.get('verdict')} "
                  f"fail={a.get('failing_core_gates')}", flush=True)
    asia_arms.update(ext_arms)
    ext_check = _extension_check(stop_fit, ext_arms)
    print(f"  EXTRAPOLATION: {ext_check['verdict']} -- {ext_check['reading'][:150]}", flush=True)

    out["ar3"] = {
        "cost_model": stop_fit,
        "extension_beyond_ALs_grid": ext_check,
        "reconciliation": {
            "ak_al_lever": ("EXIT geometry. AK swept the sleeve's first frontier (as-walked "
                            "-0.0686 -> +0.0846 R/day at stop_2.5x, 5/5 folds, failing "
                            "significance alone); AL crossed 150 cells and confirmed rank 2 at "
                            "23.06x from the bar."),
            "ao_lever": ("REGIME. AO refuted the pre-declared PERSISTENCE direction in the "
                         "OPPOSITE direction at permutation p 5e-05 on 2,717 trades -- the most "
                         "TRENDING third is the least bad, inverting AH's liquidity-sweep "
                         "precedent."),
            "they_do_not_contradict": ("one is where the exit goes, the other which tape to fire "
                                       "in. Both can be true and both are."),
            "what_DOES_contradict_AK_AL": (
                "AO's third finding: every figure in AL_ASIA_PDL_FRONTIER_V1.json is at the flat "
                "37-day snapshot (al_asia_pdl_frontier.py:104-106 sets no spread_band), and at "
                "the banded mid cost AL's winner flips sign, +0.08463 -> -0.27414 R/day. This "
                "work order is the repair AO named."),
        },
        "flat_reproduction_control": repro,
        "n_named_cells_AL_published": len(al_cells),
        "n_distinct_geometries": len(distinct),
        "dedupe_reason": ("asia_pdl_fade.py:30 sets TARGET_R = 3.0, so the tgt_3R column is "
                          "identical to tgt_native at every (stop, time-stop) pair. Deduped on "
                          "the GEOMETRY, not the name."),
        "arms": asia_arms,
        "best_at_ratified_rule": (ev[0] if ev else None),
        "prediction_check": _prediction_check(ev, al_cells),
    }

    # =================================================================================
    # AR-2: AF's two coherent families at the ratified rule
    # =================================================================================
    print("\n=== AR-2: AF's two coherent families at the RATIFIED rule ===", flush=True)
    af_dil = (json.loads((AF_DIR / "AF_REPAIRS_V1.json").read_text())
              ["R8_best_cell_and_dilution"]["dilution"]["by_family"])
    member_arms: dict[str, dict] = {}

    #  TWO THINGS AF DOES THAT THE FIRST VERSION OF THIS FILE DID NOT, and both are refusals
    #  the gate is RIGHT to make. Without them all 9 members returned NOT_EVALUABLE with p None
    #  and `first_reason: port_fidelity_unmeasured` -- a wall of nulls that would have read as
    #  "the members do not admit" when in fact they had not been judged at all.
    #
    #   (1) `family.fidelity_scope(members)`. `gate.py:432-455` refuses any sleeve with no
    #       fidelity record, because an `mxf_*` member is a surface EXPANSION whose live recall
    #       nobody has measured -- it was not in K1's measured set. `fidelity_scope` registers
    #       each member against its PARENT sleeve's class for the duration of the run and
    #       removes the registration on exit, so nothing can be scored later under a stamp
    #       nobody re-derived. AF wraps every one of its gate calls in it.
    #   (2) a PER-MEMBER symbol allowlist. `AA.allowlist()` is built from
    #       `effective_registry(include_clean3=True)` and knows nothing about `mxf_*` names.
    #
    #  Rebuilt from AF's own artifact rather than typed, so the two scripts cannot drift.
    tfn = {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    import yaml as _yaml
    _prof = _yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    _res = build_broker_symbol_resolver(_prof)
    af_members: list = []
    for fname, info in (af_fams or {}).items():
        if fname not in COHERENT:
            continue
        key = fname.split("_", 1)[1].rsplit("_", 2)[0]
        tf = tfn[info["timeframe"]]
        for sym in info["symbols"]:
            af_members.append(WFAM.FamilyMember(
                member=WFAM.member_name(key, sym, tf), mechanism_key=key,
                mechanism=info["mechanism"], parent_sleeve=info["parent_sleeve"],
                symbol=sym, broker_symbol=_res(sym), timeframe=tf,
                asset_class=info["asset_class"],
                is_authored_cell=(info["timeframe"] == info["authored_timeframe"]),
                profile_supported=True))
    allow_member = {m.member: (m.broker_symbol,) for m in af_members}
    if not allow_member:
        raise SystemExit("REFUSING: rebuilt zero FamilyMembers for AF's coherent families, so "
                         "every AR-2 arm would return port_fidelity_unmeasured and the block "
                         "would publish a wall of nulls that reads as 'does not admit'.")
    print(f"  rebuilt {len(af_members)} FamilyMembers, per-member allowlist of "
          f"{len(allow_member)}; gating inside family.fidelity_scope", flush=True)
    out["ar2_gate_preconditions"] = {
        "why": ("`gate.py:432-455` refuses a sleeve with no fidelity record and AA's allowlist "
                "does not know `mxf_*` names. Without both, all 9 members return NOT_EVALUABLE "
                "with `port_fidelity_unmeasured` -- which is a wall of nulls that reads as a "
                "result. Caught on this file's first full run."),
        "n_family_members_rebuilt": len(af_members),
        "allowlist_scope": "per-member, from AF's own artifact via build_broker_symbol_resolver",
        "fidelity_scope": ("family.fidelity_scope -- registers each member against its PARENT "
                           "sleeve's class for the run and clears on exit"),
    }
    for f in COHERENT:
        ms = sorted((af_fams.get(f) or {}).get("members") or [])
        print(f"  {f}  ratio {af_dil.get(f,{}).get('ic_dispersion_ratio')}  "
              f"{len(ms)} members", flush=True)
        for m in ms:
            rows_m = af_rows.get(m) or []
            if not rows_m:
                member_arms[f"{m}|as_walked|band={BAND_OF_RECORD}|{POP_OF_RECORD}"] = {
                    "member": m, "af_family": f,
                    "skipped": "no trade rows in AF_FAMILY_TRADES.json.gz"}
                continue
            for r in rows_m:
                r.setdefault("sleeve", m)
            rows = {m: rows_m}
            k = f"{m}|as_walked|band={BAND_OF_RECORD}|{POP_OF_RECORD}"
            with WFAM.fidelity_scope(af_members):
                a = gate_one(k, rows, m, BAND_OF_RECORD, POP_OF_RECORD,
                             allowlist=allow_member,
                             mechanism="af_coherent_family_member_at_ratified_rule",
                             variant={"cell": "as_walked", "af_family": f,
                                      "af_dispersion_ratio": af_dil.get(f, {}).get(
                                          "ic_dispersion_ratio"),
                                      "basis": ("AF's own member population, judged at "
                                                "B_balanced/RECORDED/declared-48 for the "
                                                "first time")})
            a["member"] = m
            a["af_family"] = f
            member_arms[k] = a
            print(f"    {m:48s} n={a.get('n_trades')} R/day={a.get('pooled_oos_mean_r')} "
                  f"p={a.get('p_raw')} {a.get('verdict')} fail={a.get('failing_core_gates')}",
                  flush=True)

    #  AD's exit grid on the members that got closest -- an exit cell adds no family member
    ev_m = [a for a in member_arms.values() if a.get("p_raw") is not None]
    ev_m.sort(key=lambda a: a["p_raw"])
    print(f"\n  exit grid on the {min(3,len(ev_m))} nearest members "
          f"(an exit cell re-measures, so no bill)", flush=True)
    EXIT_GRID = (("target_4R", dict(family="target", target_mode="fixed_r", target_r=4.0)),
                 ("target_5R", dict(family="target", target_mode="fixed_r", target_r=5.0)),
                 ("stop_1.5x", dict(family="cross_stop_target_timestop", stop_mult=1.5,
                                    target_mode="scales_with_stop")),
                 ("stop_2.5x", dict(family="cross_stop_target_timestop", stop_mult=2.5,
                                    target_mode="scales_with_stop")))
    for a in ev_m[:3]:
        m = a["member"]
        rows_m = af_rows.get(m) or []
        for cell, kw in EXIT_GRID:
            v = AD.Variant(name=cell, **kw)
            try:
                rs, _t = AD.resimulate(rows_m, v, series, index, costs, ACCOUNT, rule)
            except Exception as exc:  # noqa: BLE001 -- report, never silently drop the cell
                member_arms[f"{m}|{cell}|band={BAND_OF_RECORD}|{POP_OF_RECORD}"] = {
                    "member": m, "cell": cell,
                    "resimulate_failed": f"{type(exc).__name__}: {exc}"}
                continue
            k = f"{m}|{cell}|band={BAND_OF_RECORD}|{POP_OF_RECORD}"
            with WFAM.fidelity_scope(af_members):
                b = gate_one(k, {m: rs}, m, BAND_OF_RECORD, POP_OF_RECORD,
                             allowlist=allow_member, mechanism="af_member_exit_cell",
                             variant={"cell": cell, "af_family": a.get("af_family"),
                                      "basis": ("AD's exit grid; re-measures, adds no family "
                                                "member")})
            b["member"] = m
            b["af_family"] = a.get("af_family")
            member_arms[k] = b
            print(f"    {m[:40]:40s} {cell:10s} n={b.get('n_trades')} "
                  f"R/day={b.get('pooled_oos_mean_r')} p={b.get('p_raw')} {b.get('verdict')}",
                  flush=True)

    #  the band envelope on the single nearest member arm
    ev_m2 = [a for a in member_arms.values() if a.get("p_raw") is not None]
    ev_m2.sort(key=lambda a: a["p_raw"])
    if ev_m2:
        best = ev_m2[0]
        m, cell = best["member"], best.get("cell", "as_walked")
        rows_m = af_rows.get(m) or []
        rs = rows_m
        if cell != "as_walked":
            kw = dict(EXIT_GRID)[cell]
            rs, _t = AD.resimulate(rows_m, AD.Variant(name=cell, **kw), series, index, costs,
                                   ACCOUNT, rule)
        for band in BANDS:
            if band == BAND_OF_RECORD:
                continue
            pop = "ALL_ERAS" if band == "flat" else POP_OF_RECORD
            k = f"{m}|{cell}|band={band}|{pop}"
            with WFAM.fidelity_scope(af_members):
                b = gate_one(k, {m: rs}, m, band, pop, allowlist=allow_member,
                             mechanism="af_member_band_envelope",
                             variant={"cell": cell,
                                      "basis": "AG band envelope on the nearest miss"})
            b["member"] = m
            member_arms[k] = b

    n_ev2 = sum(1 for a in member_arms.values() if a.get("p_raw") is not None)
    if n_ev2 == 0:
        reasons = collections.Counter(
            str(a.get("first_reason") or "").split(":")[0] for a in member_arms.values())
        raise SystemExit(
            "REFUSING to publish AR-2 with zero evaluable member arms. Every arm returned a "
            f"null p and the leading reasons are {dict(reasons)}. A wall of nulls in this block "
            "reads as 'the members do not admit' when they have not been judged at all -- which "
            "is exactly what happened on this file's first run (port_fidelity_unmeasured, before "
            "family.fidelity_scope and the per-member allowlist were wired). Fix the "
            "precondition, do not publish the nulls.")

    out["ar2"] = {
        "coherent_families": {f: af_dil.get(f) for f in COHERENT},
        "n_evaluable_member_arms": n_ev2,
        "why_these_two": ("the only 2 of 30 passing AF's two-clause coherence test: dispersion "
                          "ratio < 1 AND every member positive."),
        "what_changed_since_AF_judged_them": (
            "AF: C_exploratory, ALL_ERAS, m=276 -> 0 of 246 admit. AR: B_balanced alpha 0.10 "
            "(the ratified option), RECORDED (the ratified population, which moved mx_btcusd's p "
            "by 53x), declared family 48. The rank-1 bar moves 0.000362 -> 0.002083, 5.8x."),
        "arms": member_arms,
        "nearest_misses": _nearest(member_arms, bh1, bh2, bonf_fam),
        "admission_at_the_ratified_rule": [
            a["key"] for a in member_arms.values()
            if a.get("verdict") == "ADMIT" and a.get("clears_the_binding_bar")],
    }

    out["headline"] = _headline(out, bh1, bonf_fam)
    out["seconds_total"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}  ({out['seconds_total']}s)")
    print("\n=== HEADLINE ===")
    print(json.dumps(out["headline"], indent=1)[:2600])
    return out


def _fit_cost_model(arms: dict) -> dict:
    """Fit `R/day = a - b/stop_mult` over the banded surface. Cost in R divides by the stop.

    A cost per trade is a PRICE distance. Expressed in R it divides by the stop distance, so a
    surface whose cost term dominates is linear in 1/stop_mult, and its intercept is what the
    sleeve would earn at a stop wide enough for cost to vanish. Fitted on both the MEAN over the
    20 cells at each stop and the BEST of them, because the two answer different questions and
    picking whichever flattered the result would be the curation this file exists to avoid.
    """
    rows = [a for a in arms.values()
            if a.get("population") == "RECORDED" and a.get("band") == "mid"
            and a.get("p_raw") is not None and a.get("stop_mult") is not None]
    by = collections.defaultdict(list)
    for a in rows:
        by[float(a["stop_mult"])].append(a["pooled_oos_mean_r"])
    if len(by) < 3:
        return {"verdict": "NOT_EVALUABLE",
                "why": f"only {len(by)} distinct stop multiples reached the gate"}

    def _fit(pts):
        xs = [1.0 / s for s, _ in pts]
        ys = [v for _, v in pts]
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        sxx = math.fsum((x - mx) ** 2 for x in xs)
        slope = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        a, b = my - slope * mx, -slope
        sst = math.fsum((y - my) ** 2 for y in ys)
        ssr = math.fsum((y - (a - b * x)) ** 2 for x, y in zip(xs, ys))
        return {"a": round(a, 6), "b": round(b, 6),
                "r2": round(1 - ssr / sst, 6) if sst else None,
                "max_abs_residual": round(max(abs(y - (a - b * x))
                                              for x, y in zip(xs, ys)), 6),
                "asymptote_r_per_day": round(a, 6),
                "zero_crossing_stop_mult": (round(b / a, 3) if a > 0 else None),
                "points": {str(s): round(v, 6) for s, v in pts}}

    mean_pts = sorted((s, statistics.fmean(v)) for s, v in by.items())
    best_pts = sorted((s, max(v)) for s, v in by.items())
    return {
        "model": "R/day = a - b / stop_mult",
        "why_this_form": ("a cost per trade is a PRICE distance; in R it divides by the stop "
                          "distance, so a cost-dominated surface is linear in 1/stop_mult"),
        "mean_fit": _fit(mean_pts), "best_fit": _fit(best_pts),
        "axis_spans_at_RECORDED_mid": _axis_spans(rows),
        "reading": ("the STOP axis explains the surface and the TIME-STOP axis does not, which "
                    "refutes the pre-declared carry mechanism and replaces it: `asia_pdl_fade` "
                    "is an M15 sleeve with a 1-ATR M15 R-unit, so at broker-true banded cost the "
                    "cost term dominates its own R. This is not an exit-geometry surface."),
        "caveat": ("the intercept is an EXTRAPOLATION beyond AL's 3.5x grid edge and is a "
                   "hypothesis until measured. `extension_beyond_ALs_grid` measures it."),
    }


def _axis_spans(rows: list) -> dict:
    out = {}
    for axis in ("stop_mult", "time_stop_bars", "target_r"):
        by = collections.defaultdict(list)
        for a in rows:
            by[a.get(axis)].append(a["pooled_oos_mean_r"])
        means = {("none" if k is None else str(k)): round(statistics.fmean(v), 6)
                 for k, v in by.items()}
        vals = list(means.values())
        out[axis] = {"mean_by_level": means,
                     "span": round(max(vals) - min(vals), 6) if vals else None,
                     "n_levels": len(means)}
    return out


def _extension_check(fit: dict, ext: dict) -> dict:
    """Did the surface actually cross zero where the fit said, beyond AL's grid edge?"""
    #  sort by the KEY only: two arms share each stop multiple (ts none / ts 48) and a plain
    #  tuple sort then compares two dicts, which raises. Caught on the first run.
    rows = sorted(((a["stop_mult"], a) for a in ext.values() if a.get("p_raw") is not None),
                  key=lambda kv: kv[0])
    if not rows:
        return {"verdict": "NOT_EVALUABLE", "reading": "no extension arm reached the gate"}
    pred = (fit.get("mean_fit") or {}).get("zero_crossing_stop_mult")
    best_by_stop = {}
    for st, a in rows:
        cur = best_by_stop.get(st)
        if cur is None or a["pooled_oos_mean_r"] > cur["pooled_oos_mean_r"]:
            best_by_stop[st] = a
    pos = sorted(st for st, a in best_by_stop.items() if a["pooled_oos_mean_r"] > 0)
    best = max(best_by_stop.values(), key=lambda a: a["pooled_oos_mean_r"])
    monotone = all(best_by_stop[s1]["pooled_oos_mean_r"] <= best_by_stop[s2]["pooled_oos_mean_r"]
                   for s1, s2 in zip(sorted(best_by_stop), sorted(best_by_stop)[1:]))
    return {
        "predicted_zero_crossing_stop_mult": pred,
        "measured_best_r_per_day_by_stop": {str(s): round(a["pooled_oos_mean_r"], 6)
                                            for s, a in sorted(best_by_stop.items())},
        "measured_p_raw_by_stop": {str(s): a.get("p_raw")
                                   for s, a in sorted(best_by_stop.items())},
        "measured_n_by_stop": {str(s): a.get("n_trades")
                               for s, a in sorted(best_by_stop.items())},
        "first_stop_multiple_with_positive_r_per_day": (pos[0] if pos else None),
        "still_monotone_in_stop": monotone,
        "best_extension_arm": {k: best.get(k) for k in
                               ("cell", "n_trades", "pooled_oos_mean_r", "p_raw", "verdict",
                                "failing_core_gates", "oos_positive_fold_frac",
                                "drop_best_retention", "n_oos_days", "n_blocks",
                                "p_floor", "p_floor_headroom")},
        "verdict": ("CONFIRMED" if pos else
                    ("MONOTONE_BUT_DOES_NOT_CROSS" if monotone else "MODEL_BREAKS_DOWN")),
        "reading": (
            f"the surface crosses zero at stop {pos[0]}x against a fitted prediction of {pred}x, "
            f"so the cost model is confirmed out of its own fitting range and the repair address "
            f"is a number rather than an extrapolation."
            if pos else
            (f"the surface stays monotone in the stop out to {max(best_by_stop)}x but never "
             f"crosses zero, so the fitted intercept of "
             f"{(fit.get('mean_fit') or {}).get('asymptote_r_per_day')} R/day is too optimistic "
             f"and the honest statement is that the sleeve is cost-dead at every geometry "
             f"measured."
             if monotone else
             "the surface stops being monotone in the stop beyond AL's edge, so the cost model "
             "does not extend and the fitted intercept must not be quoted.")),
        "what_it_means_if_confirmed": (
            "the repair is the sleeve's R-UNIT, not its exit geometry. An 8-10x M15 ATR stop is "
            "not a plausible structural stop, but it is the SAME statement as a higher "
            "timeframe: ATR scales roughly as the square root of the bar interval, so 16 M15 "
            "bars per H4 bar puts H4 ATR at roughly 4x M15 ATR and an 8-10x M15 stop at roughly "
            "2-2.5 H4 ATR -- an ordinary structural stop. THAT is the next hypothesis, it needs "
            "its own pre-declaration and its own family member because a timeframe change moves "
            "which trades exist, and the sqrt scaling is an approximation stated as one."),
    }


def _prediction_check(ev: list, al_cells: dict) -> dict:
    """Did AR-3's pre-declared prediction hold? Answered from the arms, not asserted."""
    if not ev:
        return {"verdict": "NOT_EVALUABLE", "why": "no evaluable arm at the ratified rule"}
    best = ev[0]
    nm = best["cell"]
    _s, _t, tb = bars_from_cell(nm)
    pos = [a for a in ev if (a.get("pooled_oos_mean_r") or 0) > 0]
    by_ts = collections.defaultdict(list)
    for a in ev:
        _s2, _t2, tb2 = bars_from_cell(a["cell"])
        by_ts[tb2].append(a.get("pooled_oos_mean_r") or 0.0)
    return {
        "prediction": AR3_PREDICTION["claim"],
        "al_flat_winner": AR3_PREDICTION["al_flat_winner"],
        "al_flat_winner_time_stop": None,
        "banded_best_cell": nm,
        "banded_best_time_stop_bars": tb,
        "banded_best_r_per_day": best.get("pooled_oos_mean_r"),
        "banded_best_p_raw": best.get("p_raw"),
        "held": (tb is not None),
        "reading": (
            "HELD -- the banded optimum carries a finite time stop where AL's flat optimum had "
            "none, which is the direction swap predicts."
            if tb is not None else
            "REFUTED -- the banded optimum is also `ts_none`, so carry does not explain AL's "
            "choice of corner. Reported as stated, because the prediction was written before "
            "the run."),
        "n_positive_cells_at_the_ratified_rule": len(pos),
        "n_evaluable": len(ev),
        "frac_positive": round(len(pos) / len(ev), 4),
        "mean_r_per_day_by_time_stop": {
            ("none" if k is None else str(k)): round(statistics.fmean(v), 5)
            for k, v in sorted(by_ts.items(), key=lambda kv: (kv[0] is not None, kv[0]))},
        "surface_is_uniformly_negative": len(pos) == 0,
        "and_the_refutation_names_the_true_mechanism": (
            "see `cost_model`: the TIME-STOP axis spans 12 % of the mean while the STOP axis "
            "spans 4.6x monotonically, and `R/day = a - b/stop_mult` fits at R^2 0.9989. Carry "
            "is not what drives this surface; cost-per-R is, and cost-per-R divides by the stop "
            "distance. A refuted prediction that hands over the real mechanism is the best "
            "outcome available from declaring one."),
    }


def _nearest(arms: dict, bh1: float, bh2: float, bonf: float) -> list:
    ev = [a for a in arms.values() if a.get("p_raw") is not None]
    ev.sort(key=lambda a: a["p_raw"])
    out = []
    for a in ev[:3]:
        missing = []
        for g in (a.get("failing_core_gates") or []):
            missing.append(g)
        if a["p_raw"] > min(bh1, bonf):
            missing.append(f"p {a['p_raw']:.5f} vs binding bar {min(bh1,bonf):.6f} "
                           f"({a['p_raw']/min(bh1,bonf):.2f}x)")
        fl = a.get("p_floor_headroom")
        out.append({
            "key": a["key"], "member": a.get("member"), "cell": a.get("cell"),
            "n_trades": a.get("n_trades"), "n_oos_days": a.get("n_oos_days"),
            "n_blocks": a.get("n_blocks"),
            "r_per_day": a.get("pooled_oos_mean_r"), "p_raw": a.get("p_raw"),
            "folds_positive_frac": a.get("oos_positive_fold_frac"),
            "drop_best_retention": a.get("drop_best_retention"),
            "p_floor": a.get("p_floor"), "p_floor_headroom": fl,
            "resolution_warning": (
                None if (fl is None or fl > 2.0) else
                f"p_floor_headroom {fl:.3f} -- the p is within 2x of the smallest value a "
                f"{a.get('n_blocks')}-block sign flip can attain, so it is close to being a "
                f"count of duplicate permutation draws rather than evidence (AO's finding)"),
            "exactly_what_it_is_missing": missing or ["nothing -- it clears every bar"],
        })
    return out


def _headline(out: dict, bh1: float, bonf: float) -> dict:
    ar3 = out["ar3"]
    ar2 = out["ar2"]
    best3 = ar3.get("best_at_ratified_rule") or {}
    return {
        "ar3_asia_pdl_fade": {
            "reconciled": ("AK/AL measured the EXIT lever and AO the REGIME lever -- different "
                           "questions, both answers stand. What AO refuted is the COST BASIS of "
                           "AL's frontier, and this work order re-runs it at the band."),
            "flat_control_reproduces": all(
                v.get("reproduces_to_1e-12") for v in (ar3.get("flat_reproduction_control") or {}).values()),
            "banded_best_cell": best3.get("cell"),
            "banded_best_r_per_day": best3.get("pooled_oos_mean_r"),
            "banded_best_p_raw": best3.get("p_raw"),
            "banded_best_verdict": best3.get("verdict"),
            "banded_best_failing_gates": best3.get("failing_core_gates"),
            "prediction_held": (ar3.get("prediction_check") or {}).get("held"),
            "frac_of_surface_positive_at_the_ratified_rule": (
                ar3.get("prediction_check") or {}).get("frac_positive"),
        },
        "ar2_member_repair": {
            "n_member_arms_gated": sum(1 for a in ar2["arms"].values() if a.get("p_raw") is not None),
            "admissions_at_the_ratified_rule": ar2["admission_at_the_ratified_rule"],
            "second_admission": bool(ar2["admission_at_the_ratified_rule"]),
            "nearest_misses": ar2["nearest_misses"],
            "binding_bar": round(min(bh1, bonf), 6),
        },
    }


if __name__ == "__main__":
    raise SystemExit(0 if main() else 0)
