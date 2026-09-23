"""Session AL, items 1c-3 — the two admission closers, gated, and the pair composed at the
SEALED alpha.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_admission_closers.py

THE ARITHMETIC BEING CLOSED
---------------------------
AI §2.6 left the estate here, on the RECORDED-era population at the mid band, m = 29:

    BH rank 1 needs p <= 0.10/29 = 0.003448 ; rank 2 needs p <= 0.006897
    mx_btcusd          p 0.006399   -- already inside rank 2
    sub_xvol_pullback  p 0.011999   -- cannot hold rank 1, so the PAIR is blocked

so the binding constraint is `sub_xvol_pullback`'s p, and two banked prescriptions address it
without new data. This file runs both properly and states what admits.

WHAT IS MEASURED, AND ON WHICH AXES
-----------------------------------
Four axes, every combination published, because R0 forbids comparing two figures whose stamps
differ and R1 forbids averaging them:

  population   ALL_ERAS (AA's own, all-eras snapshot spread) and RECORDED@mid (AI's restriction)
  exit         each candidate's as-walked labelling AND its banked repair cell
  alpha        0.05 (A_strict), 0.10 (the sealed B_balanced), 0.20 (C_exploratory, for reference
               only -- `options.py:110-111` disqualifies it for arming in its own author_note)
  family       CANDIDATE_FAMILY_V2's ratcheted 35 / 32, and AA's historical 69 as the comparator

THE BILL RISES AND THAT IS PAID FOR HERE
----------------------------------------
Three threshold cells are run, so three hypotheses join the family (`al_family_v2.py`): 32 -> 35
declared, 29 -> 32 looks taken. At m = 35, alpha = 0.10, rank 1 needs p <= 0.002857 and rank 2
p <= 0.005714 -- STRICTER than the m = 29 bar AI measured against. The closers therefore have to
beat a bill they also raise, and every arm below is reported at the raised bill. `gate.py:797`
floors the effective family at `max(n_judged, declared)` and all three variants are submitted in
ONE run, so the bill cannot be dodged by batching: n_judged is 35 whatever is declared.

TWO CONTROLS, BOTH ON THIS SESSION'S OWN MACHINERY
--------------------------------------------------
  1. the production cell, recovered by the offline threshold filter, must reproduce AA's 88
     trades bar-for-bar (asserted in `al_xvol_regenerate.py`), AND relabelled through this
     file's own labelling path must reproduce AA's `r_gross` exactly. The second is what makes
     the variant rows comparable to AA's -- a labelling difference would masquerade as an edge.
  2. `mx_btcusd`'s RECORDED as-walked p must reproduce AI's 0.006399 at n = 232, which AI in
     turn reproduced against AF's independently published figure.

Nothing is armed, no config is read for a live decision, no broker module is imported.
"""

from __future__ import annotations

import collections
import datetime as dt
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

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import stats as S  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.fidelity import register_threshold_variant  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AD_DIR = AUD / "phase7/receipts"
STATE = HERE / "AL_XVOL_REACHABLE_STATE_V1.json.gz"
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
OUT = HERE / "ADMISSION_CLOSER_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BAND = "mid"
MAXBARS = 80
PARENT = "sub_xvol_pullback"
BTC = "mx_btcusd_d1_donchian_20_breakout"

PRODUCTION_PARAMS = {"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10}

CELLS = {
    "thr_sub_xvol_pullback_vr14_s125_ac015": {"vr_xhi": 1.4, "slope_up": 1.25, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s150_ac015": {"vr_xhi": 1.4, "slope_up": 1.5, "ac_band": 0.15},
    "thr_sub_xvol_pullback_vr14_s100_ac010": {"vr_xhi": 1.4, "slope_up": 1.0, "ac_band": 0.10},
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# =====================================================================================
# the threshold filter and the labelling, offline over the recorded reachable state


def cell_fires(rows: dict, p: dict) -> list[str]:
    """Keys of the reachable bars this cell fires on. The four production gates, offline.

    Byte-faithful to `regime_spine.conditions.SUB_XVOL_PULLBACK`'s gate chain, which is itself
    faithful to `substrate_engine.cell_coords` + `cell_matches` for this cell: `vol=xhi` is a
    single lower bound on `vr`, `trend=up` is `slope50 > slope_up`, `mtf=conflict` is
    `mtf_align == -1`, `persist=rand` is strictly inside +/- `ac_band`.
    """
    vr_xhi = p["vr_xhi"]
    slope_up = p["slope_up"]
    ac_band = p["ac_band"]
    thr = p.get("mtf_sgn_thr", 0.5)
    out = []
    for k, r in rows.items():
        if r["vr"] < vr_xhi:
            continue
        s50 = r["slope50"]
        if s50 is None or not s50 > slope_up:
            continue
        if abs(thr - 0.5) < 1e-12:
            align = r["mtf_align"]
        else:
            s20, s100 = r["slope20"], r["slope100"]
            if s20 is None or s100 is None:
                align = 0
            else:
                def _sgn(v):
                    return 1 if v > thr else (-1 if v < -thr else 0)
                a, b = _sgn(s20), _sgn(s100)
                align = 1 if (a != 0 and a == b) else (
                    -1 if (a != 0 and b != 0 and a == -b) else 0)
        if align != -1:
            continue
        ac = r["ac60"]
        if ac is None or not (-ac_band < ac < ac_band):
            continue
        out.append(k)
    return sorted(out)


def label(rows: dict, keys: list[str], sleeve: str, series: dict, index: dict) -> list[dict]:
    """AA's labelling (`aa_estate_generate.py:260-307`) applied to a set of reachable bars.

    Plain stop/target/maxbars, no trail (`sub_xvol_pullback` is `policy: time_stop`, not
    `trailing_runner`), `winsorize_R` on the result, `entry_utc = bar_open + interval`. The exit
    contract's `time_stop_bars` is NOT applied, exactly as AA declined to apply it.
    """
    ivl = dt.timedelta(minutes=240)
    out, skips = [], collections.Counter()
    for k in keys:
        r = rows[k]
        key = (r["symbol"], TF_H4)
        if key not in index:
            skips["no_series"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            skips["bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            skips["no_room"] += 1
            continue
        pol = ExitPolicy(target_dist=r["target_dist"], maxbars=MAXBARS, label="plain")
        pr = replay(bars, i, int(r["direction"]), stop_dist=float(r["stop_dist"]), policy=pol)
        xi = pr.exit_index
        out.append({
            "sleeve": sleeve, "symbol": r["symbol"], "symbol_canonical": r["symbol_canonical"],
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "direction": int(r["direction"]),
            "sl_distance_price": float(r["stop_dist"]),
            "entry_price": float(bars[i].c),
            "r_gross": float(winsorize_R(pr.r_gross)),
            "r_gross_plain": float(winsorize_R(pr.r_gross)),
            "exit_policy": "plain", "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "timeframe": int(TF_H4), "decision_bar_iso": r["decision_bar_iso"],
            "decision_day": r["decision_day"], "bar_decision_day": r["decision_day"],
            "target_dist": r["target_dist"], "intra_size": 1.0,
            "ll_impulse": None, "decision_hour": None, "vp_loc": None,
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * 240 / 60.0, 4),
            "features": {"bar_decision_day": r["decision_day"]},
        })
    return out, dict(skips)


# =====================================================================================


def restrict_recorded(records: dict, smodel) -> tuple[dict, dict]:
    """AI's outcome-independent restriction (`ai_recorded_era_gate.py:112-133`), verbatim."""
    kept, mix = {}, {}
    for sleeve, recs in sorted(records.items()):
        cls, rows = collections.Counter(), []
        for r in recs:
            try:
                est = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=BAND)
            except Exception:  # noqa: BLE001
                cls["unpriceable"] += 1
                continue
            cls[est.era_class] += 1
            if est.era_class == "RECORDED":
                rows.append(r)
        mix[sleeve] = {"n_total": len(recs), "era_class_mix": dict(cls),
                       "n_recorded": len(rows),
                       "recorded_frac": round(len(rows) / len(recs), 4) if recs else None}
        if rows:
            kept[sleeve] = rows
    return kept, mix


def row(sv) -> dict:
    g = sv.gates
    return {
        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": g.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "failing_core_gates": [x for x in ("expectancy", "lifetime", "stability", "robustness",
                                           "significance") if not g.get(x, {}).get("pass")],
        "n_folds_evaluable": g.get("sample", {}).get("n_folds_evaluable"),
        "min_trades_per_fold": g.get("sample", {}).get("min_trades_per_fold"),
        "per_fold_test_n": g.get("sample", {}).get("per_fold_test_n"),
        "thin_fold_frac": g.get("sample", {}).get("thin_fold_frac"),
        "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
        "n_oos_folds": g.get("stability", {}).get("n_oos_folds"),
        "drop_best_retention": g.get("robustness", {}).get("retention"),
        "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
        "p_floor": (sv.telemetry or {}).get("p_floor", {}).get("p_floor"),
        "n_oos_days": g.get("significance", {}).get("n_days"),
        "first_reason": (sv.reasons[0][:280] if sv.reasons else None),
    }


def bh_table(pvec: dict, m: int, alpha: float) -> dict:
    """BH at an explicit family size, padded with 1.0 exactly as `gate.py:806-809` does."""
    names = sorted(pvec)
    ps = [pvec[n] for n in names]
    padded = ps + [1.0] * max(0, m - len(ps))
    c = S.benjamini_hochberg(padded, alpha)
    return {
        "m": c["m"], "alpha": alpha, "bh_threshold_at_k": c["threshold"], "k_rejected": c["k"],
        "rows": {n: {"p_raw": ps[i], "q": c["qvalues"][i], "rejected": bool(c["rejected"][i]),
                     "rank": sorted(ps).index(ps[i]) + 1,
                     "rank_threshold": alpha * (sorted(ps).index(ps[i]) + 1) / c["m"]}
                 for i, n in enumerate(names)},
        "admitted": sorted(n for i, n in enumerate(names) if c["rejected"][i]),
    }


def main() -> dict:
    t_start = time.time()
    AA = _load(AA_DIR / "aa_estate_walk.py", "al_aa_walk")
    AD = _load(AD_DIR / "ad_exit_sweep.py", "al_ad_sweep")
    from src.costs.spread_model import load_spread_model

    smodel = load_spread_model()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AL")
    fam = CF.load_candidate_family(DECL)
    m_all = fam.effective_size("CANDIDATE_BOOK_V1")
    m_looks = fam.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN)
    print(f"declared family: all_declared {m_all}, looks_taken {m_looks}")

    raw = json.load(gzip.open(AA_DIR / "AA_ESTATE_TRADES.json.gz", "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AA.load_broker_true_costs(AA.COSTS_V1_1)
    series, index, _res = AD.load_bars()
    rule = AD.resolve_rule(SERVER)
    print(f"loaded {len(series)} bar series in {time.time()-t_start:.0f}s")

    state = json.load(gzip.open(STATE, "rt"))
    srows = state["rows"]
    print(f"reachable state: {len(srows)} bars; parity control identical="
          f"{state['parity_control']['identical']}")

    out = {
        "schema": "gtos.wave9.al.admission_closer.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "blocks": "B1150-B1199",
        "question": ("does the candidate pair admit at the SEALED B_balanced alpha of 0.10 once "
                     "the two banked prescriptions are run -- and at the RAISED bill running "
                     "them costs?"),
        "declared_family": {
            "path": str(DECL.relative_to(REPO)),
            "sha256": fam.sha256, "membership_sha256": fam.membership_of("CANDIDATE_BOOK_V1"),
            "all_declared": m_all, "looks_taken": m_looks,
            "raised_from": {"all_declared": 32, "looks_taken": 29,
                            "by": "3 threshold variants of sub_xvol_pullback, all RUN"},
            "bh_thresholds_at_alpha_0.10": {
                "rank_1": round(0.10 / m_all, 6), "rank_2": round(0.20 / m_all, 6),
                "ai_measured_against": {"m": 29, "rank_1": 0.003448, "rank_2": 0.006897}},
        },
        "reachability": state["reachability"],
        "xvol_parity_control": state["parity_control"],
        "controls": {}, "candidates": {}, "arms": {}, "composition": {},
    }

    # ---- control 2: relabel AA's own 88 through THIS file's labelling path -----------------
    prod_keys = cell_fires(srows, PRODUCTION_PARAMS)
    relab, relab_skips = label(srows, prod_keys, PARENT, series, index)
    aa88 = {(r["symbol"], r["decision_bar_iso"]): r for r in base_rows[PARENT]}
    same_r = sum(1 for r in relab
                 if (r["symbol"], r["decision_bar_iso"]) in aa88
                 and abs(aa88[(r["symbol"], r["decision_bar_iso"])]["r_gross"]
                         - r["r_gross"]) < 1e-12)
    out["controls"]["labelling_reproduces_AA"] = {
        "question": ("does this file's labelling path reproduce AA's own r_gross on AA's own 88 "
                     "trades, bit for bit? A labelling difference would show up as an edge."),
        "n_relabelled": len(relab), "n_aa": len(aa88),
        "n_r_gross_identical_to_1e-12": same_r,
        "identical": len(relab) == len(aa88) == same_r,
        "skips": relab_skips,
    }
    print(f"CONTROL labelling: {same_r}/{len(aa88)} r_gross identical to 1e-12 "
          f"({'PASS' if same_r == len(aa88) == len(relab) else 'FAIL'})")

    # ---- the three threshold cells --------------------------------------------------------
    variant_rows: dict[str, list[dict]] = {}
    for member, params in CELLS.items():
        register_threshold_variant(member, parent=PARENT, params=params,
                                   production_params=PRODUCTION_PARAMS,
                                   note="Session AL, gated at CANDIDATE_FAMILY_V2's raised bill.")
        keys = cell_fires(srows, params)
        rows, skips = label(srows, keys, member, series, index)
        variant_rows[member] = rows
        # AB measured these cells' n on `regime_spine`, which includes the pre-gap bars the
        # port cannot reach. Publishing both makes the gap visible instead of a discrepancy.
        out["candidates"][member] = {
            "kind": "threshold_variant", "parent": PARENT, "params": params,
            "n_fires_reachable": len(keys), "n_labelled": len(rows), "label_skips": skips,
            "n_prod_cell_reachable": len(prod_keys),
            "superset_of_production": set(prod_keys) <= set(keys),
            "ab_published_n_on_regime_spine": {
                "thr_sub_xvol_pullback_vr14_s125_ac015": 420,
                "thr_sub_xvol_pullback_vr14_s150_ac015": 368,
                "thr_sub_xvol_pullback_vr14_s100_ac010": 309}[member],
            "why_n_differs_from_AB": (
                "AB's neighborhood ran on `regime_spine`, which walks every bar in the frame "
                "including the pre-gap bars `candles_to_bars` drops. This n is the subset the "
                "production GenerationPort can REACH, which is what the live book could trade "
                "(`--recover-pre-gap-bar` defaults False, book_engine.py:107)."),
        }
        print(f"  {member}: {len(keys)} reachable fires (AB published "
              f"{out['candidates'][member]['ab_published_n_on_regime_spine']} on regime_spine), "
              f"superset of production: {set(prod_keys) <= set(keys)}")

    # ---- mx_btcusd @ target_5R, and its as-walked control ---------------------------------
    btc_variants = {
        "as_walked": AD.AS_WALKED,
        "target_5R": AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                                target_r=5.0),
        "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                target_r=4.0),
    }
    btc_rows = {}
    for nm, v in btc_variants.items():
        rows, tel = AD.resimulate(base_rows[BTC], v, series, index, costs, ACCOUNT, rule)
        btc_rows[nm] = rows
        print(f"  {BTC} @ {nm}: {len(rows)} rows re-simulated")
    out["candidates"][BTC] = {
        "kind": "exit_cell_on_a_declared_member",
        "adds_to_family": False,
        "why": ("an exit change re-measures the same hypothesis; AI §0's rule is that BH corrects "
                "for distinct hypotheses, not for the number of times each was measured, and AD "
                "and AK both gated exit cells inside AA's family without adding a member"),
        "n_by_exit": {k: len(v) for k, v in btc_rows.items()},
        "ad_published": {"target_5R_all_eras_pooled_oos_r_per_day": 0.5535,
                         "target_5R_all_eras_p_raw": 0.0101,
                         "as_walked_all_eras_p_raw": 0.0120},
    }

    # ---- the xvol exit cells --------------------------------------------------------------
    #  AK's best cell for this sleeve is `target_4R` (+1.1565 R/day at raw p 0.0078 on n=88).
    #  Both exits are run for every threshold cell, because AK measured that on this sleeve the
    #  mean rises and the p WORSENS at target_4R -- so the two must not be quoted from
    #  different cells, and which exit is better for ADMISSION is an open question this answers.
    xvol_exit = {
        "as_walked": AD.AS_WALKED,
        "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                target_r=4.0),
    }

    # ---- the allowlist, extended by the variants ------------------------------------------
    al = dict(AA.allowlist())
    for member in CELLS:
        al[member] = al[PARENT]

    # ---- the grid -------------------------------------------------------------------------
    def build_population(exit_xvol: str, exit_btc: str) -> dict:
        """The full family with every candidate at its chosen exit."""
        pop = {s: list(r) for s, r in base_rows.items()}
        pop[BTC] = btc_rows[exit_btc]
        for member, rows in variant_rows.items():
            if exit_xvol == "as_walked":
                pop[member] = rows
            else:
                rs, _ = AD.resimulate(rows, xvol_exit[exit_xvol], series, index, costs,
                                      ACCOUNT, rule)
                pop[member] = rs
        return pop

    focus = [PARENT, BTC, *CELLS]
    base_opt = OPTIONS["B_balanced"]

    for exit_xvol, exit_btc in (("as_walked", "as_walked"), ("as_walked", "target_5R"),
                                ("target_4R", "target_5R"), ("target_4R", "as_walked")):
        pop_rows = build_population(exit_xvol, exit_btc)
        recs_all = {s: AD.to_records(r) for s, r in pop_rows.items()}
        recs_rec, mix = restrict_recorded(recs_all, smodel)
        for pop_label, recs in (("ALL_ERAS", recs_all), ("RECORDED@mid", recs_rec)):
            for opt_name in ("A_strict", "B_balanced", "C_exploratory"):
                o = OPTIONS[opt_name]
                # THE BAND IS PART OF THE STAMP AND IT WAS MISSING FROM THE RECEIPT.
                # `spread_band` is set only on the RECORDED arm, so the ALL_ERAS arms price at
                # `flat_37_day_snapshot` (spec.py:82) -- which is correct for an "AA's own
                # population" comparator and was NOT recorded on the arm, so a reader could not
                # tell. Found by an adversarial pass over this session's own doc, which had
                # quoted the flat-snapshot figures under a "mid band" heading: an R0 violation in
                # the file whose whole subject is R0. The band now travels on every arm.
                band = BAND if pop_label == "RECORDED@mid" else None
                spec = o.with_(spec_id=f"{o.spec_id}_al_closers",
                              sleeve_symbol_allowlist=al,
                              **({"spread_band": band} if band else {}))
                spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
                res = run_gate(recs, spec, costs=costs, server=SERVER)
                mult = res.family["multiplicity"]
                arm = (f"xvol={exit_xvol}|btc={exit_btc}|pop={pop_label}|opt={opt_name}")
                out["arms"][arm] = {
                    "exit_xvol": exit_xvol, "exit_btc": exit_btc, "population": pop_label,
                    "option": opt_name, "alpha": o.alpha, "multiplicity": o.multiplicity,
                    "spread_band": band or "flat_37_day_snapshot",
                    "spread_band_note": (
                        "None/unset means spec.py:82's flat_37_day_snapshot -- the 37-day cost "
                        "measurement charged as a constant to every era. The ALL_ERAS arms are "
                        "deliberately at the flat snapshot because they are the comparator "
                        "against AA's own published figures, which were produced that way; the "
                        "RECORDED arms are banded at mid. Two different cost bases, so an "
                        "ALL_ERAS row and a RECORDED row must not be differenced without saying "
                        "so. The mid-band ALL_ERAS restatement is in "
                        "AL_DECIDABLE_POPULATION_V1.json and AL_CANDIDATE_DOSSIER_V1.json."),
                    "spec_sha256": spec.seal(),
                    "declared_family_size": spec.declared_family_size,
                    "declared_family_id": spec.declared_family_id,
                    "effective_family_size": mult["effective_family_size"],
                    "n_sleeves_judged": mult["n_sleeves_judged_this_run"],
                    "admitted": sorted(res.admitted), "n_admitted": len(res.admitted),
                    "focus": {s: (row(res.verdicts[s]) if s in res.verdicts else None)
                              for s in focus},
                    "era_mix_focus": ({s: mix.get(s) for s in focus}
                                      if pop_label == "RECORDED@mid" else None),
                }
                for s in focus:
                    if s not in res.verdicts:
                        continue
                    v = res.verdicts[s]
                    ledger.record(
                        mechanism=("threshold_variant_gate" if s in CELLS
                                   else "admission_closer_gate"),
                        sleeve=s,
                        variant={"exit_xvol": exit_xvol, "exit_btc": exit_btc,
                                 "population": pop_label, "option": opt_name,
                                 "declared_family_size": spec.declared_family_size,
                                 **({"params": CELLS[s]} if s in CELLS else {})},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(v.verdict.value,
                                                                       "evaluated"),
                        metric=v.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                        note=f"AL admission closers, arm {arm}")
                print(f"  {arm:64s} m={mult['effective_family_size']:3d} "
                      f"ADMIT {sorted(res.admitted) or '-'}", flush=True)

    # ---- control 2b: AI's RECORDED as-walked figures must reproduce ------------------------
    ai_arm = out["arms"]["xvol=as_walked|btc=as_walked|pop=RECORDED@mid|opt=B_balanced"]
    ai_btc = ai_arm["focus"][BTC]
    ai_par = ai_arm["focus"][PARENT]
    out["controls"]["reproduces_AI_recorded_era_gate"] = {
        "question": ("AI measured mx_btcusd RECORDED n=232 p_raw 0.006399 and sub_xvol_pullback "
                     "n=85 p_raw 0.011999 at the mid band. Do they reproduce here, with three "
                     "extra sleeves in the run and a family of 35?"),
        "mx_btcusd": {"ai_n": 232, "here_n": ai_btc["n_trades"],
                      "ai_p_raw": 0.006399, "here_p_raw": ai_btc["p_raw"],
                      "n_matches": ai_btc["n_trades"] == 232,
                      "p_matches_to_1e-6": (ai_btc["p_raw"] is not None
                                            and abs(ai_btc["p_raw"] - 0.006399) < 1e-6)},
        "sub_xvol_pullback": {"ai_n": 85, "here_n": ai_par["n_trades"],
                             "ai_p_raw": 0.011999, "here_p_raw": ai_par["p_raw"],
                             "n_matches": ai_par["n_trades"] == 85,
                             "p_matches_to_1e-6": (ai_par["p_raw"] is not None
                                                   and abs(ai_par["p_raw"] - 0.011999) < 1e-6)},
        "note": ("q MUST differ from AI's -- the family is 35 here against 29 there, and that "
                 "is the price this session paid. p_raw must not."),
    }
    print("\nCONTROL vs AI: mx_btcusd n "
          f"{ai_btc['n_trades']} p {ai_btc['p_raw']} | {PARENT} n {ai_par['n_trades']} "
          f"p {ai_par['p_raw']}")

    # ---- the composition, one population per vector (R0) ----------------------------------
    #  The vector is the best-p threshold cell plus mx_btcusd, per (population, exit) pair --
    #  and the BEST-CELL PICK is stamped as a pick. The gate's own BH over all 35 is the
    #  primary verdict; this table exists so the shortfall is legible as a distance.
    for arm_name, arm in sorted(out["arms"].items()):
        if arm["option"] != "B_balanced":
            continue
        pv = {}
        for s in focus:
            f = arm["focus"].get(s)
            if f and f["p_raw"] is not None and math.isfinite(f["p_raw"]):
                pv[s] = f["p_raw"]
        if not pv:
            continue
        best_cell = min(CELLS, key=lambda c: pv.get(c, 1.0))
        pair = {k: v for k, v in pv.items() if k in (BTC, best_cell)}
        out["composition"][arm_name] = {
            "vector_all_focus": pv,
            "best_threshold_cell": best_cell,
            "pair": pair,
            "at_alpha": {
                f"{a}": {
                    "declared_35": bh_table(pv, m_all, a),
                    "looks_taken_32": bh_table(pv, m_looks, a),
                    "ai_comparator_29": bh_table(pv, 29, a),
                    "pair_only_declared_35": bh_table(pair, m_all, a),
                } for a in (0.05, 0.10, 0.20)},
        }

    # ---- the answer, in the artifact ------------------------------------------------------
    sealed = {}
    for arm_name, arm in sorted(out["arms"].items()):
        if arm["option"] == "B_balanced":
            sealed[arm_name] = arm["admitted"]
    any_sealed = sorted({s for v in sealed.values() for s in v})
    best = None
    for arm_name, arm in sorted(out["arms"].items()):
        if arm["option"] != "B_balanced":
            continue
        for s in focus:
            f = arm["focus"].get(s)
            if not f or f["p_raw"] is None:
                continue
            cand = (f["p_raw"], s, arm_name)
            if best is None or cand < best:
                best = cand
    out["answer"] = {
        "admits_at_the_sealed_alpha_0.10": any_sealed,
        "by_arm_at_B_balanced": sealed,
        "lowest_p_raw_reached": ({"p_raw": best[0], "sleeve": best[1], "arm": best[2]}
                                 if best else None),
        "rank_1_threshold_at_declared_35_alpha_0.10": round(0.10 / m_all, 6),
        "rank_2_threshold_at_declared_35_alpha_0.10": round(0.20 / m_all, 6),
        "shortfall_factor_rank_1": (round(best[0] / (0.10 / m_all), 3) if best else None),
    }
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    out["trial_ledger"] = nt
    out["seconds_total"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"ADMITS at the sealed alpha 0.10: {any_sealed or '(none)'}")
    if best:
        print(f"lowest p_raw reached: {best[0]:.6f} ({best[1]}) against a rank-1 bar of "
              f"{0.10/m_all:.6f} -- short by {best[0]/(0.10/m_all):.2f}x")
    print(f"trial ledger: {nt['n_prospective_look_events']} look events")
    return out


if __name__ == "__main__":
    main()
