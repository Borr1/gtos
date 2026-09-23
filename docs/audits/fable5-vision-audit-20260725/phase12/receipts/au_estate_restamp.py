"""Session AU — the estate restamped at the exit contract the live engine actually runs.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_estate_restamp.py
    ... --stage targets    # the target axis: does the live broker TP equal the walked target? (~1 s)
    ... --stage walk       # 4 contracts x 4 bands over the whole estate, gated at the ratified rule
    ... --stage all        # default

WHAT AU-2 ASKS FOR, AND THE CORRECTION IT TURNS INTO

AQ built the three-contract machinery and ran it on the D1 cohort, filing 10
`RESTAMP_PUBLISHED_ECONOMICS_AT_THE_LIVE_CONTRACT` rows for the sleeves whose spec is RIGHT and whose
published economics never applied it. The commission asks for those 10 restamped. Running them turned
up something about the instrument rather than about the sleeves:

**AQ's `LIVE_TRUE` arm is a time stop bolted onto a PLAIN exit, and for three sleeves the live
contract is not plain.** `relabel()` builds `AD.Variant(family="time_stop", time_stop_bars=ts,
target_mode="native")`, and `Variant` defaults `trail_arm_r=None, trail_gap_r=None,
partial_at_r=None`. So for `asian_fade` and `metal_session_reversion` (live policy `trailing_runner`)
and `energy_agri` (live policy `partial_be_runner`) that arm silently DELETES the sleeve's own exit
contract. Two of the three are the largest rows in AQ's Side-B table:

    asian_fade                AQ error +0.8832 R/day, truncation 0.0 %
    metal_session_reversion   AQ error +0.3050 R/day, truncation 0.1 %

A truncation fraction of zero says the time stop never fired, so the error cannot be the horizon.
AQ named the mechanism and routed the measurement here. `AA_ESTATE_TRADES`'s own metadata settles what
the published contract was: `exit_contracts[sleeve]["applied_here"] == "trail+stop+target+maxbars"`
for both, and `time_stop_bars_applied: false` for every sleeve in the estate.

So this file runs FOUR contracts, and the third exists only to decompose the second against AQ's:

    PUBLISHED             AA's own applied contract, replayed. CONTROL: must be R-identical to AA's
                          stored rows, or the translator is not to be trusted about anything else.
    LIVE_TRUE             the WHOLE live profile -- trail AND scale-out AND target AND time stop --
                          at the production trail bound.
    LIVE_TRUE_TS_ONLY     AQ's construction: the time stop on a plain exit. Reproduces AQ's Side-B
                          column, so `AQ_error - true_error` is the artifact, measured not argued.
    LIVE_TRUE_HONEST      LIVE_TRUE with `trail_lag_extremes=True`. B613 makes both trail bounds
                          mandatory: 95.8 % of `asian_fade`'s apparent trail gain was intrabar
                          sequencing, so the production bound alone is not a publishable number for
                          a trailing sleeve. Identical to LIVE_TRUE for every non-trailing sleeve,
                          which the artifact asserts rather than assumes.

Every cell carries its `maxbars` share and its `time_stop` share (wave-12 agreement §4, from AR's
finding that AL's published winner carries 20.6 % unreported).

MULTIPLICITY. No new looks: every arm is an exit-cell re-measurement of a declared member (AI §0).
Gated on `RECORDED` at `B_balanced` α 0.10 against `CANDIDATE_BOOK_V1` at the V5 declaration, with the
flat 37-day snapshot as a CONTROL band. Ledgered including NOT_EVALUABLE (B1267).

BOUNDARY. Offline and pure. No broker module, no order, no VPS.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

import au_live_contract as LC  # noqa: E402

AD = LC.AD

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as POP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AM_SUBMID = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_SUBMID_TRADES.json.gz"
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
AQ_TRUTH = HERE.parent.parent / "phase11/receipts/AQ_CONTRACT_TRUTH_V1.json"
OUT = HERE / "AU_ESTATE_RESTAMP_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")
POPULATION = "RECORDED"
OPTION = "B_balanced"
SUBMID = "sub_mid_dn_revert"
CONTRACTS = ("PUBLISHED", "LIVE_TRUE", "LIVE_TRUE_TS_ONLY", "LIVE_TRUE_HONEST")
#: The three sleeves whose LIVE policy is not a plain exit, so the choice of construction moves them.
#: Read from the profiles rather than listed, so a future policy change cannot leave this stale.
POLICY_BEARING = tuple(sorted(
    s for s, p in SLEEVE_EXIT_PROFILES.items()
    if str(p.get("policy")) in ("trailing_runner", "partial_be_runner")))
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert")


# =====================================================================================
# substrate
# =====================================================================================

def build_substrate() -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items() if r}
    subm = json.load(gzip.open(AM_SUBMID, "rt"))
    base[SUBMID] = subm["trades"]["server_repaired"]     # AQ-3's re-clock, as every session since
    print(f"substrate: loading bars...", flush=True)
    series, index, _ = AD.load_bars()
    out = {"base": base, "aa_meta": {k: v for k, v in raw.items() if k != "trades"},
           "costs": AD.load_broker_true_costs(AD.COSTS), "rule": AD.resolve_rule(SERVER),
           "series": series, "index": index, "allowlist": AD.allowlist(),
           "family": CF.load_candidate_family(FAMILY_V5),
           "units": json.loads(LC.UNITS.read_text(encoding="utf-8")),
           "aq": (json.loads(AQ_TRUTH.read_text(encoding="utf-8")) if AQ_TRUTH.is_file() else {})}
    print(f"substrate in {time.time() - t0:.0f}s: {len(base)} sleeves, "
          f"{len(POLICY_BEARING)} policy-bearing", flush=True)
    return out


# =====================================================================================
# stage `targets` — the axis that turns out to be clean, stated as a measurement
# =====================================================================================

def stage_targets(sub: dict) -> dict:
    """Does the live broker TP equal the target AA walked? Cheap, and it bounds the restamp.

    A published economic number can diverge from the live contract on THREE axes: the target, the
    management policy (trail / scale-out), and the time stop. AQ measured the third. This measures
    the first, so the restamp's scope is a finding rather than an assumption.
    """
    rows = {}
    for sleeve, tr in sorted(sub["base"].items()):
        prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
        ratios = sorted({round(float(r["target_dist"]) / float(r["sl_distance_price"]), 6)
                         for r in tr if r.get("target_dist")})
        no_tp = str(prof.get("broker_take_profit_mode", "final_target")).lower() == "none"
        ftr = prof.get("final_target_r")
        ffi = bool(prof.get("final_from_intent"))
        if no_tp:
            agree = (not ratios)          # targetless live == targetless walk
            basis = "no_broker_tp"
        elif ffi:
            agree = bool(ratios)          # the broker TP tracks the intent, whatever it is
            basis = "final_from_intent_tracks_the_walked_target"
        else:
            agree = (len(ratios) == 1 and abs(ratios[0] - float(ftr)) < 1e-6)
            basis = "fixed_final_target_r"
        rows[sleeve] = {
            "grid": LC.grid_of(tr), "n_trades": len(tr),
            "walked_target_r": ratios if len(ratios) <= 4 else [ratios[0], ratios[-1]],
            "n_distinct_walked_target_r": len(ratios),
            "live_final_target_r": ftr, "final_from_intent": ffi, "no_broker_tp": no_tp,
            "basis": basis, "agrees": bool(agree),
            "live_policy": str(prof.get("policy")),
            "live_time_stop_m15": prof.get("time_stop_bars"),
        }
    dis = sorted(s for s, r in rows.items() if not r["agrees"])
    print(f"  target axis: {len(rows) - len(dis)}/{len(rows)} agree; disagree: {dis}", flush=True)
    return {"n_sleeves": len(rows), "n_agree": len(rows) - len(dis), "disagreeing": dis,
            "note": ("the TARGET axis of the restamp. A sleeve here that disagrees would have a "
                     "published economic number measured at a broker take-profit the live engine "
                     "does not set, which is a third defect class beside the time stop and the "
                     "management policy."),
            "sleeves": rows}


# =====================================================================================
# stage `walk` — the estate under four contracts
# =====================================================================================

def variant_for(sub: dict, sleeve: str, contract: str):
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    grid = LC.grid_of(sub["base"][sleeve])
    ratio = LC.printed_ratio_of(sleeve, sub["units"])
    if contract == "PUBLISHED":
        applied = ((sub["aa_meta"].get("exit_contracts") or {}).get(sleeve) or {}).get("applied_here")
        if not applied:
            raise KeyError(f"{sleeve}: AA records no `applied_here`; refusing to guess the "
                           f"published contract")
        return LC.variant_for_applied(sleeve, prof, applied, grid=grid, name=f"published_{sleeve}")
    if contract == "LIVE_TRUE":
        return LC.variant_for_profile(sleeve, prof, grid=grid, name=f"live_{sleeve}",
                                      printed_ratio=ratio)
    if contract == "LIVE_TRUE_HONEST":
        return LC.variant_for_profile(sleeve, prof, grid=grid, name=f"live_honest_{sleeve}",
                                      printed_ratio=ratio, trail_lag_extremes=True)
    if contract == "LIVE_TRUE_TS_ONLY":
        # AQ's construction, reproduced deliberately: a time stop on stop+native target+maxbars,
        # with the sleeve's trail and scale-out absent. Not the live contract for POLICY_BEARING.
        ts = LC.own_bars(sleeve, prof.get("time_stop_bars"), grid=grid, printed_ratio=ratio)
        return AD.Variant(name=f"ts_only_{sleeve}", family="time_stop", time_stop_bars=ts,
                          target_mode="native",
                          note="AQ's LIVE_TRUE construction; drops trail/partial by Variant default")
    raise ValueError(contract)


def relabel_estate(sub: dict, contract: str) -> tuple[dict, dict]:
    out, tel = {}, {}
    for sleeve in sorted(sub["base"]):
        v = variant_for(sub, sleeve, contract)
        rows, t = AD.resimulate(sub["base"][sleeve], v, sub["series"], sub["index"],
                                sub["costs"], ACCOUNT, sub["rule"])
        out[sleeve] = rows
        tel[sleeve] = {"variant": v.as_dict(), **LC.maxbars_share(t)}
    return out, tel


def row_of(sv, res, spec, *, band, contract, seconds, mix, tel) -> dict:
    fam = (res.family or {}).get("multiplicity", {}) or {}
    base = {
        "contract": contract, "population": POPULATION,
        "band": band if band is not None else "flat_37_day_snapshot",
        "band_is_control": band is None,
        "option": OPTION, "declared_family_size": spec.declared_family_size,
        "effective_family_size": fam.get("effective_family_size"),
        "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
        "population_mix": mix, "seconds": round(seconds, 2),
        "maxbars_share": tel.get("maxbars_share"),
        "time_stop_share": tel.get("time_stop_share"),
        "horizon_share": tel.get("horizon_share"),
        "exit_reasons": tel.get("exit_reasons"),
    }
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    st = sv.gates.get("stability", {})
    t = sv.telemetry or {}
    ri = t.get("regime_inflation") or {}
    ins = t.get("in_sample") or {}
    diag = sv.diagnostics or {}
    hold = diag.get("holding") or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            # AR handoff item 2, on every row
            "regime_inflation_contaminated": ri.get("contamination_flag"),
            "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
            "haircut_binding_term": ri.get("haircut_binding_term"),
            "haircut_at_floor": ri.get("haircut_at_floor"),
            "selection_surface_evaluable": ri.get("selection_surface_evaluable"),
            "in_sample_mean_is_r": ins.get("mean_is_r"),
            "in_sample_mean_oos_r": ins.get("mean_oos_r"),
            "in_sample_sign_inversion": (
                None if (ins.get("mean_is_r") is None or ins.get("mean_oos_r") is None)
                else bool(float(ins["mean_is_r"]) < 0 <= float(ins["mean_oos_r"]))),
            "median_hold_hours": hold.get("median_hours"),
            "reasons": list(sv.reasons),
            }


def gate_estate(sub: dict, labelled: dict, tel: dict, *, contract: str, band,
                ledger: TrialLedger | None) -> dict:
    t0 = time.time()
    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_au_restamp_{contract.lower()}",
                   sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
    recs0 = {s: AD.to_records(r) for s, r in labelled.items()}
    recs, spec, mix = POP.apply(POPULATION, recs0, spec, account=ACCOUNT, band=(band or "mid"))
    res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
    wo = (res.family or {}).get("wipeout") or {}
    if wo.get("wiped_out"):
        raise RuntimeError(f"gate wipeout on {contract}/{band}: {wo}. Refusing to publish.")
    el = time.time() - t0
    out = {}
    for sleeve in sorted(labelled):
        sv = res.verdicts.get(sleeve)
        out[sleeve] = row_of(sv, res, spec, band=band, contract=contract, seconds=el, mix=mix,
                             tel=tel.get(sleeve, {}))
        if ledger is not None and sv is not None:
            ledger.record(
                mechanism="estate_restamp", sleeve=sleeve,
                variant={"contract": contract, "population": POPULATION,
                         "band": out[sleeve]["band"], "option": OPTION},
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
                metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                note=f"AU estate restamp, {contract} @ {out[sleeve]['band']}")
    return out


def stage_walk(sub: dict, ledger: TrialLedger | None) -> dict:
    labelled, tel = {}, {}
    for c in CONTRACTS:
        t0 = time.time()
        labelled[c], tel[c] = relabel_estate(sub, c)
        print(f"  relabelled {c} in {time.time() - t0:.0f}s", flush=True)

    # --- CONTROL: PUBLISHED must reproduce AA's own stored labelling -----------------------
    ctl = {}
    for sleeve in sorted(sub["base"]):
        ctl[sleeve] = LC.published_identity_control(labelled["PUBLISHED"][sleeve],
                                                   sub["base"][sleeve])
    bad = sorted(s for s, c in ctl.items() if not c["identical"])
    print(f"  control PUBLISHED==AA: {len(ctl) - len(bad)}/{len(ctl)} identical; bad={bad}",
          flush=True)
    if bad:
        raise RuntimeError(f"the translator does not reproduce AA's own labelling for {bad}. "
                           f"Refusing to publish a restamp built on it.")

    # --- CONTROL: HONEST == LIVE_TRUE for every non-policy-bearing sleeve ------------------
    same = {}
    for sleeve in sorted(sub["base"]):
        same[sleeve] = LC.published_identity_control(labelled["LIVE_TRUE_HONEST"][sleeve],
                                                    labelled["LIVE_TRUE"][sleeve])["identical"]
    unexpected = sorted(s for s, ok in same.items()
                        if ok is False and s not in POLICY_BEARING)
    print(f"  control HONEST==LIVE for non-trail sleeves: unexpected={unexpected}", flush=True)

    rows = {}
    for c in CONTRACTS:
        for band in BANDS:
            r = gate_estate(sub, labelled[c], tel[c], contract=c, band=band, ledger=ledger)
            rows[f"{c}|{band or 'flat'}"] = r
            adm = sorted(s for s, x in r.items() if x.get("verdict") == "ADMIT")
            print(f"  gated {c:18s} band={str(band):5s} admit={adm}", flush=True)
    return {"control_published_reproduces_AA": ctl,
            "control_honest_equals_live_for_non_policy_sleeves":
                {"policy_bearing": list(POLICY_BEARING),
                 "unexpected_differences": unexpected,
                 "identical_by_sleeve": same},
            "telemetry": tel, "arms": rows}


# =====================================================================================
# the restamp table: what each published number overstates, and what AQ's arm attributed wrongly
# =====================================================================================

def restamp_table(sub: dict, walk: dict) -> dict:
    aq_rows = ((sub.get("aq") or {}).get("sleeves") or {})
    out = {}
    for sleeve in sorted(sub["base"]):
        rec = {"live_policy": str(SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
                                  .get("policy")),
               "policy_bearing": sleeve in POLICY_BEARING,
               "armed": sleeve in ARMED, "bands": {}}
        for band in BANDS:
            b = band or "flat"
            cells = {c: walk["arms"][f"{c}|{b}"].get(sleeve, {}) for c in CONTRACTS}
            pub = cells["PUBLISHED"].get("pooled_oos_mean_r")
            liv = cells["LIVE_TRUE"].get("pooled_oos_mean_r")
            tso = cells["LIVE_TRUE_TS_ONLY"].get("pooled_oos_mean_r")
            hon = cells["LIVE_TRUE_HONEST"].get("pooled_oos_mean_r")
            rec["bands"][b] = {
                "published_r_per_day": pub, "live_true_r_per_day": liv,
                "ts_only_r_per_day": tso, "honest_trail_r_per_day": hon,
                # the LABELLING ERROR: how much the published figure overstates the live contract
                "restamp_error": (None if (pub is None or liv is None) else pub - liv),
                # AQ's column, and the part of it that is the dropped trail/scale-out rather than
                # the horizon. Positive => AQ's arm overstated the error.
                "ts_only_error": (None if (pub is None or tso is None) else pub - tso),
                "construction_artifact": (None if (liv is None or tso is None) else liv - tso),
                # what the honest trail bound costs, for the sleeves it applies to
                "intrabar_trail_credit": (None if (liv is None or hon is None) else liv - hon),
                "verdicts": {c: cells[c].get("verdict") for c in CONTRACTS},
                "verdict_moved": (cells["PUBLISHED"].get("verdict")
                                  != cells["LIVE_TRUE"].get("verdict")),
                "maxbars_share": {c: cells[c].get("maxbars_share") for c in CONTRACTS},
                "horizon_share": {c: cells[c].get("horizon_share") for c in CONTRACTS},
            }
        aq = aq_rows.get(sleeve) or {}
        rec["aq_published_error_at_mid"] = (aq.get("bands", {}).get("mid", {}) or {}).get("error")
        out[sleeve] = rec
    return out


# =====================================================================================
# assemble
# =====================================================================================

def _prior() -> dict:
    if OUT.is_file():
        try:
            return json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def assemble(sub: dict, stages: dict) -> dict:
    prior = _prior()
    walk = stages.get("walk") or prior.get("walk")
    doc = {
        "schema": "gtos.au.estate_restamp.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                        "au_estate_restamp.py",
        "session": "AU", "blocks": "B1550-B1599",
        "what": ("every sleeve's published economics restamped at the WHOLE live exit contract "
                 "(target + management policy + time stop), gated at the ratified rule, with the "
                 "maxbars share on every cell"),
        "contracts": {
            "PUBLISHED": "AA's own `applied_here` contract, replayed. CONTROL: R-identical to AA.",
            "LIVE_TRUE": "the whole live profile: trail AND scale-out AND target AND time stop.",
            "LIVE_TRUE_TS_ONLY": ("AQ's construction -- a time stop on a PLAIN exit. Reproduced to "
                                  "decompose AQ's Side-B error column; not the live contract for "
                                  "the policy-bearing sleeves."),
            "LIVE_TRUE_HONEST": ("LIVE_TRUE at `trail_lag_extremes=True` (B613's honest bound). "
                                 "Identical to LIVE_TRUE for every non-trailing sleeve."),
        },
        "gate": {"population": POPULATION, "option": OPTION,
                 "declared_family": "CANDIDATE_BOOK_V1 @ CANDIDATE_FAMILY_V5.json",
                 "bands": ["flat_37_day_snapshot (CONTROL)", "low", "mid", "high"],
                 "multiplicity_note": "no new looks; exit-cell re-measurements of declared members"},
        "policy_bearing_sleeves": list(POLICY_BEARING),
        "armed_sleeves": list(ARMED),
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "targets": stages.get("targets") or prior.get("targets"),
        "walk": walk,
    }
    if walk:
        doc["restamp"] = restamp_table(sub, walk)
    else:
        doc["restamp"] = prior.get("restamp")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("targets", "walk", "all"))
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    sub = build_substrate()
    ledger = None if a.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AU")
    stages: dict = {}
    if a.stage in ("targets", "all"):
        print("stage targets:", flush=True)
        stages["targets"] = stage_targets(sub)
    if a.stage in ("walk", "all"):
        print("stage walk:", flush=True)
        stages["walk"] = stage_walk(sub, ledger)
    doc = assemble(sub, stages)
    OUT.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
