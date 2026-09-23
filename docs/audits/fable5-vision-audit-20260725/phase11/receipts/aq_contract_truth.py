"""Session AQ — contract truth: the estate at the exit contract the live engine actually runs.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_contract_truth.py
    ... --stage audit       # the spec audit, no bars needed, ~1 s
    ... --stage walk        # 3 contracts x 4 bands, RECORDED + ALL_ERAS control
    ... --stage admission   # the standing admission cell under all three contracts
    ... --stage all         # default

WHAT THIS MEASURES, AND WHY IT IS NOT A REPEAT OF AD
-----------------------------------------------------
`time_stop_bars` in `SLEEVE_EXIT_PROFILES` is **M15 bars that PRINTED**, for every sleeve
(`src/components/execution.py:8953-8958` counts them, `:9010` compares them). AD resolved
that unit (B750) and measured the per-symbol printed-bar ratio. It did not do the thing
this file does: gate the estate under that contract at the RATIFIED population rule, and
ask what the repair is worth **per sleeve, with a sign**.

Three contracts, per sleeve, all in the sleeve's OWN bar units so `exits.replay` can run
them:

    PUBLISHED   stop / native target / maxbars 80, no time stop.
                This is `AA_ESTATE_TRADES` as walked and it is what every published
                economic number in this estate describes.
    LIVE_TRUE   the same, plus a time stop at `round(time_stop_bars_m15 / m15_per_own_bar)`
                own bars. This is what the live engine does today.
    REPAIRED    the same, plus a time stop at the sleeve's DECLARED NATIVE horizon in own
                bars — i.e. what the spec would mean if its M15 value were scaled right.

For the twelve `mx_*` D1 sleeves REPAIRED == PUBLISHED (native 80 own bars == `maxbars`),
so the repair RESTORES the published economics — and running it anyway is a control, not a
waste: it must come back R-identical to PUBLISHED or the conversion is wrong.
For the unit-correct sleeves REPAIRED == LIVE_TRUE, so there the prescription is the
opposite one: the research LABEL must move to the live contract, because the spec is right.

THE DEFECT, STATED WITHOUT DIVINING INTENT
--------------------------------------------
1. The field's unit is M15 printed bars.               [execution.py:8953-8958, :9010]
2. `vol_compression`, a D1 sleeve four lines above the defect in the same dict, carries
   7680 with the comment "D1 research horizon: 80 D1 bars ~= 7680 M15 bars".
                                                        [execution_packets.py:63-64]
3. The fourteen `mx_*` D1 sleeves carry **96**, which is ONE D1 bar — it is the
   conversion RATIO written into a field that wants the converted VALUE.
                                                        [execution_packets.py:91-94]
4. Therefore their live horizon is 1/80th of the horizon every published number for them
   was measured under. No claim about what anyone meant is needed to say that.

MULTIPLICITY
------------
No new looks are declared here. Every arm is an EXIT-CELL re-measurement of a sleeve
already in `CANDIDATE_BOOK_V1`, and AI §0's rule is that BH corrects for distinct
hypotheses, not re-measurements of one (>= 2,260 exit cells have been gated across the
programme and charged 0). The family is V3 at 39 declared, per the wave-11 agreement.
Every arm is ledgered anyway, including NOT_EVALUABLE (B1267).

BOUNDARY
--------
Offline and pure. Reads bars, cost artifacts and AA's stored intents; imports no broker
module, places nothing, and writes nothing outside `phase11/receipts/` and the two
append-only ledgers.
"""
from __future__ import annotations

import argparse
import gzip
import os
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
UNITS = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AD_TIMESTOP_UNITS_V1.json"
AM_SUBMID = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_SUBMID_TRADES.json.gz"
FAMILY_V3 = REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts/CANDIDATE_FAMILY_V3.json"
OUT = HERE / "AQ_CONTRACT_TRUTH_V1.json"
STAGES_CACHE = HERE / "AQ_STAGES.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
MAXBARS = AD.MAXBARS  # 80
BANDS = (None, "low", "mid", "high")
#: The estate-wide research horizon, in the sleeve's own bars. Every correctly-scaled
#: sleeve's M15 value is `n * m15_per_bar` for some n <= this.
NATIVE_MAXBARS = 80
#: Calendar M15 bars per bar of each decision grid. NOT the printed-bar ratio (which is
#: 92 on a session symbol, 84 on UKOIL) — this is the conversion a SPEC can use, because a
#: spec is per sleeve and the printed ratio is per symbol. The residual is bounded, one-
#: directional and quantified in `spec_audit.rounding_residual`.
M15_PER_BAR_CALENDAR = {"M15": 1, "H4": 16, "D1": 96}

#: The three sleeves live on both accounts. Nothing in this file may move them, and the
#: audit asserts it rather than assuming it.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")

#: THE DECLARATION AS IT STOOD BEFORE THIS SESSION'S REPAIR, frozen so this file stays
#: reproducible after it. Read off `git show 436dbb5c7:...execution_packets.py`.
#:
#: Without this the driver is a one-shot: it reads the live `SLEEVE_EXIT_PROFILES`, so the
#: moment the repair lands its own `--stage audit` reports "0 sleeves mis-scaled" and
#: overwrites the artifact that documents the defect. That happened once during this
#: session and cost a restore from the index. A measurement of a defect must survive the
#: defect being fixed, or it is not a measurement.
#:
#: `AS_OF` selects which declaration the audit describes. `pre_repair` reproduces the
#: artifact of record; `live` reads the source and is the REGRESSION CHECK — it must report
#: zero mis-scaled sleeves forever after B1404, and if it ever does not, the repair has been
#: reverted.
PRE_REPAIR_TIME_STOP_BARS: dict[str, int] = {
    **{s: 96 for s in (
        "mx_aus200_cash_d1_volume_surge_reversal", "mx_avausd_d1_donchian_20_breakout",
        "mx_btcusd_d1_donchian_20_breakout", "mx_cadjpy_d1_volume_surge_reversal",
        "mx_ethusd_d1_donchian_20_breakout", "mx_eu50_cash_d1_volume_surge_reversal",
        "mx_fra40_cash_d1_volume_surge_reversal", "mx_ger40_cash_d1_volume_surge_reversal",
        "mx_jp225_cash_d1_volume_surge_reversal", "mx_nzdjpy_d1_donchian_20_breakout",
        "mx_spn35_cash_d1_volume_surge_reversal", "mx_us100_cash_d1_atr_mean_reversion",
        "mx_us30_cash_d1_volume_surge_reversal", "mx_us500_cash_d1_atr_mean_reversion")},
}
AS_OF = os.environ.get("AQ_AS_OF", "pre_repair")   # "pre_repair" | "live"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
SUBMID = "sub_mid_dn_revert"


# =====================================================================================
# stage: audit -- the spec truth, read from source, no bars
# =====================================================================================

def profile_for(sleeve: str) -> dict:
    """The sleeve's exit profile at `AS_OF` — the frozen pre-repair declaration by default."""
    prof = dict(SLEEVE_EXIT_PROFILES.get(sleeve) or DEFAULT_EXIT_PROFILE)
    if AS_OF == "pre_repair" and sleeve in PRE_REPAIR_TIME_STOP_BARS:
        prof["time_stop_bars"] = PRE_REPAIR_TIME_STOP_BARS[sleeve]
    elif AS_OF not in ("pre_repair", "live"):
        raise SystemExit(f"AQ_AS_OF must be 'pre_repair' or 'live', got {AS_OF!r}")
    return prof


def spec_audit(units: dict, tf_by_sleeve: dict, n_by_sleeve: dict) -> dict:
    """Per sleeve: declared M15 time stop -> own bars -> is it the native horizon?

    A sleeve is MISSCALED when its declared value resolves to fewer own bars than the
    sleeve's realised median hold, by a factor large enough that no exit policy would be
    written that way on purpose. That threshold is not a judgement call here: the mx_*
    cohort resolves to **1.0** own bars against a **3-4** own-bar median and a 9-14
    own-bar p90, and the value 96 is exactly `M15_PER_BAR_CALENDAR["D1"]`.
    """
    rows = {}
    for sleeve, tf in sorted(tf_by_sleeve.items()):
        prof = profile_for(sleeve)
        ts_m15 = prof.get("time_stop_bars")
        u = units.get(sleeve) or {}
        ratio_measured = u.get("m15_per_own_bar_trade_weighted")
        ratio_cal = M15_PER_BAR_CALENDAR[tf]
        ratio = ratio_measured or ratio_cal
        own_exact = (ts_m15 / ratio) if ts_m15 else None
        own = max(1, int(round(own_exact))) if own_exact else None
        rows[sleeve] = {
            "timeframe": tf,
            "policy": prof.get("policy"),
            "n_trades_walked": n_by_sleeve.get(sleeve, 0),
            "declared_time_stop_bars_m15": ts_m15,
            "m15_per_own_bar_measured": ratio_measured,
            "m15_per_own_bar_calendar": ratio_cal,
            "live_time_stop_own_bars_exact": (round(own_exact, 4) if own_exact else None),
            "live_time_stop_own_bars_rounded": own,
            "native_horizon_own_bars_if_correct": NATIVE_MAXBARS,
            "declared_equals_ratio_itself": (ts_m15 == ratio_cal),
            "realised_median_hold_hours": u.get("realised_median_hold_hours"),
            "realised_median_exit_bar_offset": u.get("realised_median_exit_bar_offset"),
            "frac_trades_the_time_stop_would_truncate":
                u.get("frac_trades_the_time_stop_would_truncate"),
            "binds_before_maxbars": u.get("time_stop_binds_before_maxbars"),
        }
        # classification
        if ts_m15 is None:
            cls = "NO_TIME_STOP"
        elif ts_m15 == ratio_cal and tf != "M15":
            cls = "MISSCALED_RATIO_AS_VALUE"
        elif own is not None and own > NATIVE_MAXBARS:
            cls = "UNIT_CORRECT_NEVER_BINDS"
        elif u.get("time_stop_binds_before_maxbars"):
            cls = "UNIT_CORRECT_BINDS_RESEARCH_NEVER_APPLIED_IT"
        else:
            cls = "UNIT_CORRECT_DOES_NOT_BIND"
        rows[sleeve]["classification"] = cls
        rows[sleeve]["repaired_time_stop_bars_m15"] = (
            NATIVE_MAXBARS * ratio_cal if cls == "MISSCALED_RATIO_AS_VALUE" else ts_m15)

    misscaled = sorted(s for s, r in rows.items()
                       if r["classification"] == "MISSCALED_RATIO_AS_VALUE")
    binds = sorted(s for s, r in rows.items()
                   if r["classification"] == "UNIT_CORRECT_BINDS_RESEARCH_NEVER_APPLIED_IT")

    # --- the armed-three assertion. Not a comment: a check that raises. ---------------
    armed = {}
    for s in ARMED:
        r = rows.get(s)
        if r is None:
            raise SystemExit(f"armed sleeve {s} absent from the audit — refusing to publish")
        armed[s] = {"timeframe": r["timeframe"],
                    "declared_time_stop_bars_m15": r["declared_time_stop_bars_m15"],
                    "repaired_time_stop_bars_m15": r["repaired_time_stop_bars_m15"],
                    "own_bars": r["live_time_stop_own_bars_rounded"],
                    "classification": r["classification"],
                    "unchanged_by_this_repair":
                        r["declared_time_stop_bars_m15"] == r["repaired_time_stop_bars_m15"]}
        if r["timeframe"] != "H4":
            raise SystemExit(f"armed sleeve {s} is {r['timeframe']}, expected H4 — refusing")
        if not armed[s]["unchanged_by_this_repair"]:
            raise SystemExit(f"the repair would move armed sleeve {s} — refusing to publish")

    # --- the rounding residual on session symbols ------------------------------------
    resid = []
    for s in misscaled:
        r = rows[s]
        rm, rc = r["m15_per_own_bar_measured"], r["m15_per_own_bar_calendar"]
        if not rm:
            continue
        # the repaired M15 value, converted back through the PRINTED ratio
        eff_own = (NATIVE_MAXBARS * rc) / rm
        resid.append({"sleeve": s, "m15_per_own_bar_measured": rm,
                      "effective_own_bars_of_repaired_value": round(eff_own, 3),
                      "overshoot_vs_maxbars_frac": round(eff_own / NATIVE_MAXBARS - 1.0, 5)})

    return {
        "what": ("the declared live time stop of every sleeve, resolved into the sleeve's "
                 "own bar grid, against the research horizon its published economics use"),
        "as_of": AS_OF,
        "as_of_note": (
            "`pre_repair` (the default, and what the artifact of record is built from) reads "
            "the frozen declaration as it stood at commit 436dbb5c7, so this measurement "
            "survives its own subject being fixed. `AQ_AS_OF=live` reads the source instead "
            "and is the REGRESSION CHECK: after B1404 it must report zero mis-scaled sleeves "
            "forever, and if it ever does not, the repair has been reverted."),
        "unit_authority": {
            "file_line": "src/components/execution.py:8953-8958",
            "symbol": "ExecutionEngine._trading_m15_bars_since",
            "consumer": "src/components/execution.py:9010 check_time_stop_and_close",
            "unit": "M15 bars that PRINTED (trading bars), for every sleeve",
        },
        "the_defect": {
            "sleeves": misscaled,
            "n": len(misscaled),
            "n_generating": sum(1 for s in misscaled if rows[s]["n_trades_walked"] > 0),
            "declared": 96,
            "correct": NATIVE_MAXBARS * M15_PER_BAR_CALENDAR["D1"],
            "factor": NATIVE_MAXBARS,
            "why_it_is_a_unit_error_and_not_a_policy": (
                "96 is exactly M15_PER_BAR_CALENDAR['D1'] — the conversion ratio written "
                "into a field that wants the converted value. `vol_compression`, a D1 "
                "sleeve declared four lines earlier in the same dict "
                "(execution_packets.py:63-64), carries 7680 with the comment 'D1 research "
                "horizon: 80 D1 bars ~= 7680 M15 bars'. Both cannot be right."),
            "site": "src/components/ultimate_book/execution_packets.py:91-94",
        },
        "unit_correct_but_research_never_applied_it": {
            "sleeves": binds,
            "n": len(binds),
            "prescription": ("the SPEC is right and the LABEL is wrong: re-stamp these "
                             "sleeves' published economics at their own live contract"),
        },
        "armed_three": armed,
        "rounding_residual": {
            "what": ("a spec is per SLEEVE and the printed-bar ratio is per SYMBOL, so a "
                     "spec-level conversion must use the calendar ratio. On session "
                     "symbols (92 printed M15 bars per D1 bar, not 96) the repaired value "
                     "therefore runs slightly PAST the 80-bar research horizon."),
            "direction": "LOOSER than the research contract, never tighter",
            "rows": resid,
            "max_overshoot_frac": (max((r["overshoot_vs_maxbars_frac"] for r in resid),
                                       default=0.0)),
        },
        "sleeves": rows,
    }


# =====================================================================================
# substrate
# =====================================================================================

def own_bar_stop(sleeve: str, audit: dict, which: str) -> int | None:
    """The time stop in the sleeve's own bars under contract `which`.

    `PUBLISHED` -> None. `LIVE_TRUE` -> the declared M15 value / the MEASURED printed
    ratio. `REPAIRED` -> the repaired M15 value / the same measured ratio, capped at
    `maxbars` because a policy cannot outlive the harness ceiling.
    """
    r = audit["sleeves"].get(sleeve)
    if r is None:
        return None
    if which == "PUBLISHED":
        return None
    key = "declared_time_stop_bars_m15" if which == "LIVE_TRUE" else \
        "repaired_time_stop_bars_m15"
    ts = r[key]
    if not ts:
        return None
    ratio = r["m15_per_own_bar_measured"] or r["m15_per_own_bar_calendar"]
    return max(1, min(MAXBARS, int(round(ts / ratio))))


def build_substrate(audit: dict) -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items()}
    # AQ-3's correction travels into every arm this file gates: AA's `sub_mid_dn_revert`
    # population was produced by a clock defect (`substrate._session_hour` read raw UTC,
    # 50.04 % of H4 bars mis-bucketed) and AM measured the repair. Judging AA's 503 would
    # be judging the defect. Same substitution AN made.
    subm = json.load(gzip.open(AM_SUBMID, "rt"))
    base[SUBMID] = subm["trades"]["server_repaired"]
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()
    fam = CF.load_candidate_family(FAMILY_V3)
    print(f"substrate in {time.time()-t0:.0f}s: {len(base)} sleeves, "
          f"submid {len(base[SUBMID])} (AA had {len(raw['trades'][SUBMID])})", flush=True)
    return {"base": base, "costs": costs, "rule": rule, "series": series, "index": index,
            "allowlist": al, "family": fam, "aa_submid_n": len(raw["trades"][SUBMID])}


def relabel(sub: dict, audit: dict, which: str) -> tuple[dict, dict]:
    """Every sleeve's rows re-labelled under contract `which`. PUBLISHED is a passthrough."""
    if which == "PUBLISHED":
        return {s: list(r) for s, r in sub["base"].items()}, {}
    out, tel = {}, {}
    for sleeve, rows in sub["base"].items():
        ts = own_bar_stop(sleeve, audit, which)
        if ts is None or not rows:
            out[sleeve] = list(rows)
            continue
        v = AD.Variant(name=f"{which.lower()}_ts{ts}", family="time_stop",
                       time_stop_bars=ts, target_mode="native")
        r2, t = AD.resimulate(rows, v, sub["series"], sub["index"], sub["costs"], ACCOUNT,
                              sub["rule"])
        out[sleeve] = r2
        tel[sleeve] = {"time_stop_own_bars": ts, **t}
    return out, tel


# =====================================================================================
# one gated arm
# =====================================================================================

def row_of(sv, res, spec, *, pop: str, band, contract: str, option: str,
           seconds: float, mix: dict) -> dict:
    fam = res.family["multiplicity"]
    base = {
        "contract": contract, "population": pop,
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
    st = sv.gates.get("stability", {})
    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
    dep = (sv.telemetry or {}).get("dependence", {}) or {}
    cov = sv.coverage or {}
    diag = sv.diagnostics or {}
    cd = diag.get("cost_decomposition") or {}
    hold = diag.get("holding") or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "coverage_frac": cov.get("coverage_frac"),
            "weakest_coverage": cov.get("weakest_coverage"),
            "decidability_refusals": EP.decidability_refusals(cov),
            "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
            "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                 if (sv.p_raw is not None and fl.get("p_floor")) else None),
            "n_oos_days": dep.get("n_oos_days"),
            "effective_n_oos_days": dep.get("effective_n_oos_days"),
            "mean_gross_r": cd.get("mean_gross_r"), "mean_cost_r": cd.get("mean_cost_r"),
            "median_hold_hours": hold.get("median_hours"),
            "frac_hold_over_24h": hold.get("frac_over_24h"),
            "folds": sv.folds,
            "reasons": list(sv.reasons),
            }


def run_arm(sub: dict, rows_by_sleeve: dict, *, contract: str, pop: str, band,
            option: str, ledger: TrialLedger | None, note: str,
            wanted: tuple[str, ...] | None = None, spec_tag: str = "aq") -> dict:
    t0 = time.time()
    o = OPTIONS[option]
    spec = o.with_(spec_id=f"{o.spec_id}_{spec_tag}_{contract.lower()}",
                   sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
    recs0 = {s: AD.to_records(r) for s, r in rows_by_sleeve.items()}
    recs, spec, mix = EP.apply(pop, recs0, spec, account=ACCOUNT,
                               band=(band or "mid"))
    res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
    el = time.time() - t0
    keys = wanted if wanted is not None else tuple(sorted(rows_by_sleeve))
    out = {}
    for sleeve in keys:
        sv = res.verdicts.get(sleeve)
        out[sleeve] = row_of(sv, res, spec, pop=pop, band=band, contract=contract,
                             option=option, seconds=el, mix=mix)
        if ledger is not None and sv is not None:
            ledger.record(
                mechanism="contract_truth_grid", sleeve=sleeve,
                variant={"contract": contract, "population": pop,
                         "band": out[sleeve]["band"], "option": option},
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
                metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                note=f"AQ contract truth, {note}")
    return out


# =====================================================================================
# stage: walk -- the estate under all three contracts
# =====================================================================================

CONTRACTS = ("PUBLISHED", "LIVE_TRUE", "REPAIRED")


def stage_walk(sub: dict, audit: dict, ledger: TrialLedger | None) -> dict:
    labelled, tel = {}, {}
    for c in CONTRACTS:
        labelled[c], tel[c] = relabel(sub, audit, c)
        print(f"  relabelled {c}", flush=True)

    # --- CONTROL C1: REPAIRED must be R-identical to PUBLISHED on the mis-scaled cohort.
    # A repaired D1 time stop of 80 own bars fires on the same bar `maxbars` does, at the
    # same close, so R must match to the bit. If it does not, the conversion is wrong and
    # every number below is about the wrong contract.
    c1 = {"checked": 0, "identical": 0, "mismatched": []}
    for s in audit["the_defect"]["sleeves"]:
        a = {(r["decision_bar_iso"], r["direction"]): r["r_gross"]
             for r in labelled["PUBLISHED"].get(s, [])}
        b = {(r["decision_bar_iso"], r["direction"]): r["r_gross"]
             for r in labelled["REPAIRED"].get(s, [])}
        if not a:
            continue
        c1["checked"] += len(a)
        same = sum(1 for k, v in a.items() if k in b and b[k] == v)
        c1["identical"] += same
        if same != len(a):
            c1["mismatched"].append({"sleeve": s, "n": len(a), "identical": same})
    c1["pass"] = (c1["checked"] > 0 and not c1["mismatched"])
    if not c1["pass"]:
        raise SystemExit(f"C1 FAILED — REPAIRED is not PUBLISHED on the D1 cohort: {c1}")
    print(f"  C1 repaired==published on the D1 cohort: {c1['identical']}/{c1['checked']}",
          flush=True)

    arms: dict[str, dict] = {}
    for c in CONTRACTS:
        for band in BANDS:
            key = f"{c}|RECORDED|{band or 'flat'}"
            arms[key] = run_arm(sub, labelled[c], contract=c, pop="RECORDED", band=band,
                                option="B_balanced", ledger=ledger,
                                note=f"{c} @ RECORDED/{band or 'flat'}")
            print(f"  {key}", flush=True)
        # the population control, at the ratified rule's own comparison band
        key = f"{c}|ALL_ERAS|mid"
        arms[key] = run_arm(sub, labelled[c], contract=c, pop="ALL_ERAS", band="mid",
                            option="B_balanced", ledger=ledger, note=f"{c} @ ALL_ERAS/mid")
        print(f"  {key}", flush=True)

    # --- the per-sleeve delta table, at the ratified band -----------------------------
    def cell(c, band, s):
        return arms[f"{c}|RECORDED|{band}"].get(s) or {}

    deltas = {}
    for s in sorted(audit["sleeves"]):
        row = {"classification": audit["sleeves"][s]["classification"],
               "timeframe": audit["sleeves"][s]["timeframe"],
               "n_trades_walked": audit["sleeves"][s]["n_trades_walked"],
               "live_time_stop_own_bars": own_bar_stop(s, audit, "LIVE_TRUE"),
               "repaired_time_stop_own_bars": own_bar_stop(s, audit, "REPAIRED"),
               "by_band": {}}
        for band in ("flat", "low", "mid", "high"):
            pub, liv, rep = (cell("PUBLISHED", band, s), cell("LIVE_TRUE", band, s),
                             cell("REPAIRED", band, s))
            if not pub:
                continue
            pr, lr = pub.get("pooled_oos_mean_r"), liv.get("pooled_oos_mean_r")
            row["by_band"][band] = {
                "published_r_per_day": pr, "live_true_r_per_day": lr,
                "repaired_r_per_day": rep.get("pooled_oos_mean_r"),
                "repair_worth_r_per_day": ((rep.get("pooled_oos_mean_r") - lr)
                                           if (rep.get("pooled_oos_mean_r") is not None
                                               and lr is not None) else None),
                "published_verdict": pub.get("verdict"),
                "live_true_verdict": liv.get("verdict"),
                "repaired_verdict": rep.get("verdict"),
                "published_p": pub.get("p_raw"), "live_true_p": liv.get("p_raw"),
                "published_n": pub.get("n_trades"), "live_true_n": liv.get("n_trades"),
                "published_median_hold_h": pub.get("median_hold_hours"),
                "live_true_median_hold_h": liv.get("median_hold_hours"),
            }
        deltas[s] = row

    return {"arms": arms, "per_sleeve": deltas, "relabel_telemetry": tel,
            "c1_repaired_equals_published": c1,
            "contracts": {c: {"what": _contract_doc(c)} for c in CONTRACTS}}


def _contract_doc(c: str) -> str:
    return {
        "PUBLISHED": ("AA's labelling: stop / native target / maxbars 80, NO time stop. "
                      "Every published economic number in this estate describes this."),
        "LIVE_TRUE": ("the same, plus a time stop at the DECLARED M15 value converted "
                      "through the sleeve's own measured printed-bar ratio. This is the "
                      "contract `run_book.py` runs today."),
        "REPAIRED": ("the same, plus a time stop at the sleeve's declared M15 value AFTER "
                     "the unit repair (80 own bars for the mis-scaled D1 cohort, "
                     "unchanged everywhere else), capped at maxbars."),
    }[c]


# =====================================================================================
# stage: admission -- the standing admission cell, under all three contracts
# =====================================================================================

#: AN's config, reproduced so this session's q is comparable to the ratified decision's.
#: `sub_mid_dn_revert` is already the re-clocked population in `build_substrate`.
ADM_EXITS = {
    BTC: AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0),
    XVOL: AD.Variant(name="target_4R", family="target", target_mode="fixed_r", target_r=4.0),
}


def stage_admission(sub: dict, audit: dict, ledger: TrialLedger | None) -> dict:
    """`mx_btcusd @ target_5R` with the live time stop switched on, off, and repaired.

    The published admission carries NO time stop: `target_5R`'s `Variant` leaves
    `time_stop_bars=None`, its median hold is 120 h and 82.6 % of its trades are held past
    24 h. The live engine would close all of those at ~24 h. So the admission and the
    contract are not the same object, and this stage measures the difference.
    """
    base = {s: list(r) for s, r in sub["base"].items()}
    out: dict[str, dict] = {}
    cells: dict[str, dict] = {}

    for contract in CONTRACTS:
        rows = {s: list(r) for s, r in base.items()}
        for sleeve, v in ADM_EXITS.items():
            ts = own_bar_stop(sleeve, audit, contract)
            var = AD.Variant(name=f"{v.name}__{contract.lower()}", family="target",
                             target_mode=v.target_mode, target_r=v.target_r,
                             time_stop_bars=ts)
            r2, tel = AD.resimulate(base[sleeve], var, sub["series"], sub["index"],
                                    sub["costs"], ACCOUNT, sub["rule"])
            rows[sleeve] = r2
            cells[f"{sleeve}|{contract}"] = {
                "variant": var.as_dict(), "n": len(r2),
                "time_stop_own_bars": ts, "exit_reasons":
                    {k[5:]: v2 for k, v2 in sorted(tel.items()) if k.startswith("exit_")}}
        for band in BANDS:
            for option in ("B_balanced", "A_strict"):
                key = f"{contract}|{option}|RECORDED|{band or 'flat'}"
                out[key] = run_arm(sub, rows, contract=contract, pop="RECORDED", band=band,
                                   option=option, ledger=ledger,
                                   note=f"admission cell {contract} @ {band or 'flat'}",
                                   wanted=(BTC, XVOL, SUBMID), spec_tag="aqadm")
                print(f"  {key}: btc {out[key][BTC]['verdict']} "
                      f"p={out[key][BTC]['p_raw']}", flush=True)
    return {"arms": out, "cells": cells,
            "config": {BTC: "target_5R", XVOL: "target_4R", SUBMID: "reclocked"},
            "why_this_config": ("AN's `X_btc5R`, reproduced so this session's q sits on the "
                                "same submitted vector as the ratified decision's")}


# =====================================================================================
# assembly
# =====================================================================================

def _cache() -> dict:
    """Stage results, from this run's cache OR from the artifact of record.

    The cache is a convenience and is deliberately NOT committed — it is a byte-for-byte
    duplicate of the two heavy stages. So the fallback matters: without it a
    `--stage audit` re-run assembles `walk: null, admission: null` over a complete
    artifact, which is exactly the accident this session had to restore from the index.
    A single-stage run must be able to refresh its own stage and leave the rest alone.
    """
    out: dict = {}
    if OUT.is_file():
        try:
            prior = json.loads(OUT.read_text())
            for k in ("walk", "admission"):
                if prior.get(k) is not None:
                    out[k] = prior[k]
            if prior.get("spec_audit"):
                out["audit"] = prior["spec_audit"]
        except Exception:
            pass
    if STAGES_CACHE.is_file():
        try:
            # the cache WINS where it has a stage, because it is this run's own output;
            # the artifact only fills the stages this run did not touch.
            out.update({k: v for k, v in json.loads(STAGES_CACHE.read_text()).items()
                        if v is not None})
        except Exception:
            pass
    return out


def _cache_put(k: str, v) -> None:
    c = _cache()
    c[k] = v
    STAGES_CACHE.write_text(json.dumps(c, indent=1, sort_keys=True, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["audit", "walk", "admission", "assemble", "all"])
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    t_all = time.time()
    HERE.mkdir(parents=True, exist_ok=True)

    units = json.load(open(UNITS))["sleeve_contracts"]
    raw_meta = json.load(gzip.open(AA_IN, "rt"))
    tf_by = raw_meta["timeframe_by_sleeve"]
    n_by = raw_meta["n_trades_by_sleeve"]
    audit = spec_audit(units, tf_by, n_by)
    if a.stage in ("audit", "all"):
        _cache_put("audit", audit)
        d = audit["the_defect"]
        print(f"AUDIT: {d['n']} sleeves declared {d['declared']} where {d['correct']} "
              f"is correct ({d['factor']}x); {d['n_generating']} of them generate.")
        print(f"       {audit['unit_correct_but_research_never_applied_it']['n']} more are "
              f"unit-correct but their published economics ignore the time stop.")
        print(f"       armed three unaffected: "
              f"{all(v['unchanged_by_this_repair'] for v in audit['armed_three'].values())}")

    ledger = None if a.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AQ")

    if a.stage in ("walk", "admission", "all"):
        sub = build_substrate(audit)
        if a.stage in ("walk", "all"):
            print("WALK:")
            _cache_put("walk", stage_walk(sub, audit, ledger))
        if a.stage in ("admission", "all"):
            print("ADMISSION:")
            _cache_put("admission", stage_admission(sub, audit, ledger))

    c = _cache()
    doc = {
        "schema": "gtos.wave11.aq.contract_truth.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                         "aq_contract_truth.py"),
        "session": "AQ", "blocks": "B1400-B1415",
        "source_trades": str(AA_IN.relative_to(REPO)),
        "submid_population": ("AM's re-clocked `server_repaired` arm, substituted for AA's "
                              "defect-clock 503 — see `phase9/receipts/AM_SUBMID_TRADES.json.gz`"),
        "cost_artifact": str(Path(AD.COSTS).relative_to(REPO)),
        "declared_family": {
            "file": str(FAMILY_V3.relative_to(REPO)), "family_id": "CANDIDATE_BOOK_V1",
            "basis": "all_declared", "size": 39,
            "new_looks_declared_by_this_session": 0,
            "why_zero": ("every arm is an EXIT-CELL re-measurement of a sleeve already "
                         "declared in CANDIDATE_BOOK_V1. AI §0: BH corrects for distinct "
                         "hypotheses, not re-measurements of one."),
        },
        "population_rule": {"gated_on": "RECORDED", "control": "ALL_ERAS",
                            "ratified": "Borhen 2026-07-30, POPULATION_RULE_V1.ratified_rule",
                            "bands_published": ["flat(control)", "low", "mid", "high"]},
        "spec_audit": c.get("audit", audit),
        "walk": c.get("walk"),
        "admission": c.get("admission"),
        "seconds_total": round(time.time() - t_all, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))
    print(f"wrote {OUT.relative_to(REPO)} in {doc['seconds_total']}s")


if __name__ == "__main__":
    main()
