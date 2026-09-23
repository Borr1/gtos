"""Session AU — the two wired frontier exits ARE their research cells, and what they are worth now.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_exit_contract_wiring.py
    ... --stage identity     # the runnability proof: live contract == research cell, trade by trade
    ... --stage gate         # both cells at the RATIFIED rule, 4 bands, chronological folds
    ... --stage all          # default

WHAT THIS SETTLES

`SESSION_AU_CONTRACT_WIRING.md` AU-1 asks for `target_5R` and `target_4R` as *"first-class, testable
exit contracts the live engine can run"*. The wiring is in `execution_packets.FRONTIER_EXIT_OVERRIDES`
and pinned behaviourally by `tests/ultimate_book/test_frontier_exit_contracts.py`. What a unit test
cannot show is that the contract the live engine now resolves is THE SAME OBJECT the research cell
measured -- that is a claim about two independent code paths agreeing on an economic quantity, and it
has to be measured over the trades.

    stage `identity`  replay the LIVE-resolved profile (`resolve_exit_profile(sleeve,
                      frontier_exits=(sleeve,))`, translated by `au_live_contract`) against AD's own
                      `target_5R`/`target_4R` variant over AA's stored intents, and require
                      R-identity trade by trade. Also runs the COMMITTED profile against
                      `as_walked`, which is the same claim about the contract already running.

    stage `gate`      both cells at the ratified rule -- `RECORDED`, `B_balanced` α 0.10,
                      `CANDIDATE_BOOK_V1` at the V5 declaration (48, the current high water), the
                      band column published alongside a flat CONTROL, chronological folds, and the
                      `maxbars` share on every cell (wave-12 agreement §4).

WHY THE GATE STAGE IS NOT A FORMALITY, AND THIS IS THE FINDING THE COMMISSION DID NOT ASK FOR

`mx_btcusd @ target_5R` has been gated at the ratified rule -- it IS the estate's standing admission.
`sub_xvol_pullback @ target_4R` has not. Its only verdict comes from `AK_EXIT_FRONTIER_V2.json`, and
`ak_supply_gate.py` sets **no `spread_band` and no era population**: it is the flat 37-day cost
snapshot on ALL_ERAS, at AA's 69-look bill. Those are exactly the two qualifications AO found on AL's
`asia_pdl_fade` frontier and AR then found again — and this sleeve is ARMED and trading real money on
both accounts, which makes it the one place in the estate where an un-re-gated frontier cell could
reach a live risk decision. So the wiring lands either way; whether to ARM it is a question this
stage answers rather than assumes.

MULTIPLICITY. No new looks. Every arm here is an exit-cell re-measurement of a sleeve already declared
in `CANDIDATE_BOOK_V1` (AI §0: BH corrects for distinct hypotheses, not for re-measurements of one;
>= 2,260 exit cells have been gated across the programme at zero charge). The declared family is
raised by nobody in this file. Every arm is ledgered anyway, including NOT_EVALUABLE (B1267).

BOUNDARY. Offline and pure. Reads bars, cost artifacts and AA's stored intents; imports no broker
module, places nothing, and writes only into `phase12/receipts/` and the two append-only ledgers.
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
    FRONTIER_EXIT_OVERRIDES,
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
#: The CURRENT high-water declaration: the wave-11 train's union of the two parallel V4s.
#: `CANDIDATE_BOOK_V1` is 48 there against AQ's V3 39, and the ratchet refuses to shrink, so 48 is
#: the bill actually payable. It is the TIGHTER bar, which is the safe direction.
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
OUT = HERE / "AU_EXIT_WIRING_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")          # None == the flat 37-day snapshot, a CONTROL
POPULATION = "RECORDED"                        # ratified 2026-07-30
OPTION = "B_balanced"                          # options.py:110 disqualifies 0.20 for arming
SUBMID = "sub_mid_dn_revert"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"

#: The research cell each wired sleeve's live contract must reproduce. `target_mode="fixed_r"` with
#: `target_r=k` is AD's own construction (`ad_exit_sweep.py:534-539`).
CELLS = {
    BTC: ("target_5R", 5.0),
    XVOL: ("target_4R", 4.0),
}
#: ...and the committed contract's counterpart, which is the same claim about what runs TODAY.
#: `as_walked` is AA's labelling; for both sleeves that is stop + the generator's own target +
#: maxbars, and both live specs resolve to exactly that R multiple (measured: 2.0 on all 318
#: `mx_btcusd` trades, 3.0 on all 88 `sub_xvol_pullback` trades).
COMMITTED_CELL = "as_walked"


# =====================================================================================
# substrate
# =====================================================================================

def build_substrate() -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items()}
    #: AQ-3's correction travels into every arm: AA's `sub_mid_dn_revert` population was produced by
    #: a clock defect (`substrate._session_hour` read raw UTC; 50.04 % of H4 bars mis-bucketed) and
    #: AM measured the repair. Judging AA's 503 would be judging the defect. Same substitution AN,
    #: AQ and AR made.
    subm = json.load(gzip.open(AM_SUBMID, "rt"))
    base[SUBMID] = subm["trades"]["server_repaired"]
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    fam = CF.load_candidate_family(FAMILY_V5)
    units = json.loads(LC.UNITS.read_text(encoding="utf-8"))
    print(f"substrate in {time.time() - t0:.0f}s: {len(base)} sleeves, "
          f"family {fam.family_id if hasattr(fam, 'family_id') else 'V5'}", flush=True)
    return {"base": base, "aa_meta": {k: v for k, v in raw.items() if k != "trades"},
            "costs": costs, "rule": rule, "series": series, "index": index,
            "allowlist": AD.allowlist(), "family": fam, "units": units}


def _resim(sub: dict, sleeve: str, variant) -> tuple[list, dict]:
    return AD.resimulate(sub["base"][sleeve], variant, sub["series"], sub["index"],
                         sub["costs"], ACCOUNT, sub["rule"])


# =====================================================================================
# stage `identity` — the live contract IS the research cell
# =====================================================================================

#: The fields an economic claim is made of. `exit_reason` is deliberately NOT among them and the
#: reason is a measurement, not a convenience: a time stop at exactly the sleeve's own 80-bar horizon
#: fires on the same bar `maxbars` does, at the same close, and `exits.replay` labels that bar
#: `time_stop` because the policy takes precedence over the harness ceiling. So a live contract that
#: is economically identical to a research cell with no time stop MUST differ on the label for the
#: subset of trades that ran the full horizon. AQ's C1 control found the same thing over 2,086 trades
#: and 4,000 randomised replays -- *"0 mismatches on r_gross, exit_index, bars_held; only exit_reason
#: changes"*. The relabelling is therefore reported and CONSTRAINED (below) rather than ignored.
_ECONOMIC_FIELDS = ("r_gross", "exit_bar_offset", "target_dist", "sl_distance_price",
                    "mfe_r", "mae_r")
#: The only relabelling the horizon coincidence can produce. Anything else is a real difference.
_ALLOWED_RELABEL = {("maxbars", "time_stop")}


def _identity(rows_a: list, rows_b: list) -> dict:
    """Trade-by-trade identity on the quantities an economic claim is made of.

    `rows_a` is the research cell, `rows_b` the live-resolved contract.
    """
    def key(r):
        return (r["symbol"], r["decision_bar_iso"], int(r["direction"]))

    a = {key(r): r for r in rows_a}
    b = {key(r): r for r in rows_b}
    shared = sorted(set(a) & set(b))
    mism, relabel, bad_relabel = [], {}, []
    for k in shared:
        for f in _ECONOMIC_FIELDS:
            va, vb = a[k].get(f), b[k].get(f)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                same = abs(float(va) - float(vb)) <= 1e-9
            else:
                same = va == vb
            if not same:
                mism.append({"key": list(k), "field": f, "research": va, "live": vb})
                break
        ra, rb = a[k].get("exit_reason"), b[k].get("exit_reason")
        if ra != rb:
            relabel[f"{ra}->{rb}"] = relabel.get(f"{ra}->{rb}", 0) + 1
            if (ra, rb) not in _ALLOWED_RELABEL:
                bad_relabel.append({"key": list(k), "research": ra, "live": rb})
    return {"n_research": len(a), "n_live": len(b), "n_shared": len(shared),
            "n_mismatched": len(mism),
            "identical": (not mism) and (not bad_relabel)
                         and len(shared) == len(a) == len(b),
            "exit_reason_relabelled": relabel,
            "n_relabelled": sum(relabel.values()),
            "n_unexpected_relabels": len(bad_relabel),
            "unexpected_relabels": bad_relabel[:5],
            "examples": mism[:5]}


def stage_identity(sub: dict) -> dict:
    out = {}
    for sleeve, (cell, k) in CELLS.items():
        grid = LC.grid_of(sub["base"][sleeve])
        ratio = LC.printed_ratio_of(sleeve, sub["units"])
        applied = sub["aa_meta"]["exit_contracts"][sleeve]["applied_here"]

        # --- control 0: the translator reproduces AA's own labelling ------------------------
        pub_v = LC.variant_for_applied(sleeve, SLEEVE_EXIT_PROFILES[sleeve], applied, grid=grid)
        pub_rows, pub_tel = _resim(sub, sleeve, pub_v)
        ctl0 = LC.published_identity_control(pub_rows, sub["base"][sleeve])

        # --- the COMMITTED contract vs AD's as_walked --------------------------------------
        cm_v = LC.variant_for_profile(sleeve, LC.live_profile(sleeve), grid=grid,
                                      name=f"live_committed_{sleeve}", printed_ratio=ratio)
        cm_rows, cm_tel = _resim(sub, sleeve, cm_v)
        aw_rows, aw_tel = _resim(sub, sleeve, AD.AS_WALKED)
        committed = _identity(aw_rows, cm_rows)

        # --- the FRONTIER contract vs AD's target_kR ---------------------------------------
        fr_prof = LC.live_profile(sleeve, frontier_exits=(sleeve,))
        fr_v = LC.variant_for_profile(sleeve, fr_prof, grid=grid,
                                      name=f"live_frontier_{sleeve}", printed_ratio=ratio)
        fr_rows, fr_tel = _resim(sub, sleeve, fr_v)
        res_v = AD.Variant(name=cell, family="target", target_mode="fixed_r", target_r=k)
        res_rows, res_tel = _resim(sub, sleeve, res_v)
        frontier = _identity(res_rows, fr_rows)

        out[sleeve] = {
            "grid": grid, "m15_per_own_bar_measured": ratio,
            "aa_applied_here": applied,
            "committed_profile": {kk: vv for kk, vv in SLEEVE_EXIT_PROFILES[sleeve].items()},
            "frontier_override": dict(FRONTIER_EXIT_OVERRIDES[sleeve]),
            "time_stop_own_bars": cm_v.time_stop_bars,
            "control_translator_reproduces_AA": ctl0,
            "committed_is_as_walked": committed,
            "frontier_is_the_research_cell": {"cell": cell, "target_r": k, **frontier},
            "maxbars": {
                "as_walked": LC.maxbars_share(aw_tel),
                "live_committed": LC.maxbars_share(cm_tel),
                f"research_{cell}": LC.maxbars_share(res_tel),
                "live_frontier": LC.maxbars_share(fr_tel),
            },
        }
        ok = (ctl0["identical"] and committed["identical"] and frontier["identical"])
        print(f"  {sleeve:34s} {cell:10s} translator={ctl0['identical']} "
              f"committed={committed['identical']} frontier={frontier['identical']} -> "
              f"{'OK' if ok else 'MISMATCH'}", flush=True)
    return out


# =====================================================================================
# stage `gate` — both cells at the ratified rule
# =====================================================================================

def row_of(sv, res, spec, *, band, arm: str, seconds: float, mix: dict, tel: dict) -> dict:
    fam = (res.family or {}).get("multiplicity", {}) or {}
    base = {
        "arm": arm, "population": POPULATION,
        "band": band if band is not None else "flat_37_day_snapshot",
        "band_is_control": band is None,
        "option": OPTION, "alpha": spec.alpha, "multiplicity": spec.multiplicity,
        "declared_family_size": spec.declared_family_size,
        "declared_family_id": spec.declared_family_id,
        "effective_family_size": fam.get("effective_family_size"),
        "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
        "population_mix": mix, "seconds": round(seconds, 2),
        **{f"maxbars_{k}": v for k, v in tel.items()
           if k in ("maxbars_share", "time_stop_share", "horizon_share", "n_exited")},
        "exit_reasons": tel.get("exit_reasons"),
    }
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    st = sv.gates.get("stability", {})
    fl = (sv.telemetry or {}).get("p_floor", {}) or {}
    diag = sv.diagnostics or {}
    # AR handoff item 2: both live on `telemetry`, not on `diagnostics` — which is part of why no
    # receipt in the estate had published them. `gate.py:771` and `:782` set them on EVERY run.
    tel_sv = sv.telemetry or {}
    ri = tel_sv.get("regime_inflation") or {}
    ins = tel_sv.get("in_sample") or {}
    hold = diag.get("holding") or {}
    cd = diag.get("cost_decomposition") or {}
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
            "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
            "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                 if (sv.p_raw is not None and fl.get("p_floor")) else None),
            # AR handoff item 2: `regime_inflation` and `in_sample` are computed on EVERY gate run
            # and were published by no AR receipt. On AR-2's own near-miss they read CONTAMINATED /
            # x0.42653 and a train/test SIGN INVERSION. Published here beside the headline R/day.
            "regime_inflation_verdict": ri.get("verdict"),
            "regime_inflation_contaminated": ri.get("contamination_flag"),
            "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
            "haircut_binding_term": ri.get("haircut_binding_term"),
            "haircut_at_floor": ri.get("haircut_at_floor"),
            "selection_surface_penalty": ri.get("selection_surface_penalty"),
            "selection_surface_evaluable": ri.get("selection_surface_evaluable"),
            "regime_basis_haircut": ri.get("regime_basis_haircut"),
            "in_sample_sign_inversion": (
                None if (ins.get("mean_is_r") is None or ins.get("mean_oos_r") is None)
                else bool(float(ins["mean_is_r"]) < 0 <= float(ins["mean_oos_r"]))),
            "in_sample_mean_is_r": ins.get("mean_is_r"),
            "in_sample_mean_oos_r": ins.get("mean_oos_r"),
            "median_hold_hours": hold.get("median_hours"),
            "frac_hold_over_24h": hold.get("frac_over_24h"),
            "mean_gross_r": cd.get("mean_gross_r"), "mean_cost_r": cd.get("mean_cost_r"),
            "folds": sv.folds,
            "reasons": list(sv.reasons),
            "family_wipeout": (res.family or {}).get("wipeout"),
            }


def run_arm(sub: dict, sleeve: str, variant, *, band, arm: str, tel: dict,
            ledger: TrialLedger | None) -> dict:
    """Gate `sleeve` under `variant`, with every OTHER sleeve at its as-walked labelling.

    The full-family gate is AD's convention and it is load-bearing: gating one sleeve alone changes
    its BH rank and makes the q-value incomparable to the baseline it is being measured against.
    """
    t0 = time.time()
    rows, _ = _resim(sub, sleeve, variant)
    by_sleeve = {s: list(r) for s, r in sub["base"].items()}
    by_sleeve[sleeve] = rows
    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_au_wiring_{arm}",
                  sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
    recs0 = {s: AD.to_records(r) for s, r in by_sleeve.items()}
    recs, spec, mix = POP.apply(POPULATION, recs0, spec, account=ACCOUNT, band=(band or "mid"))
    res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
    el = time.time() - t0
    sv = res.verdicts.get(sleeve)
    row = row_of(sv, res, spec, band=band, arm=arm, seconds=el, mix=mix, tel=tel)
    # AQ's `family["wipeout"]` is always PRESENT and carries `wiped_out: False` on a healthy run, so
    # the guard has to read the field and not the dict's truthiness. (My first version read the dict
    # and refused every arm -- loudly, which is the good kind of wrong.)
    wo = row.get("family_wipeout") or {}
    if wo.get("wiped_out"):
        raise RuntimeError(f"gate wipeout on {arm}: {wo} — a whole run of nulls tabulates as a "
                           f"result (AQ §0 item 6). Refusing to publish.")
    if ledger is not None and sv is not None:
        ledger.record(
            mechanism="frontier_exit_wiring", sleeve=sleeve,
            variant={"arm": arm, "population": POPULATION, "band": row["band"],
                     "option": OPTION},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(row.get("verdict"), "evaluated"),
            metric=row.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
            note=f"AU exit contract wiring, {sleeve} @ {arm}, "
                 f"maxbars_share={row.get('maxbars_share')}")
    return row


def stage_gate(sub: dict, ledger: TrialLedger | None) -> dict:
    out = {}
    for sleeve, (cell, k) in CELLS.items():
        grid = LC.grid_of(sub["base"][sleeve])
        ratio = LC.printed_ratio_of(sleeve, sub["units"])
        arms = {
            COMMITTED_CELL: LC.variant_for_profile(
                sleeve, LC.live_profile(sleeve), grid=grid,
                name=f"live_committed_{sleeve}", printed_ratio=ratio),
            cell: LC.variant_for_profile(
                sleeve, LC.live_profile(sleeve, frontier_exits=(sleeve,)), grid=grid,
                name=f"live_frontier_{sleeve}", printed_ratio=ratio),
        }
        rows = []
        for arm, v in arms.items():
            _, tel = _resim(sub, sleeve, v)
            share = LC.maxbars_share(tel)
            for band in BANDS:
                r = run_arm(sub, sleeve, v, band=band, arm=arm, tel=share, ledger=ledger)
                rows.append(r)
                print(f"  {sleeve:34s} {arm:10s} band={r['band']:20s} {r['verdict']:14s} "
                      f"n={r.get('n_trades')} R/day={r.get('pooled_oos_mean_r')} "
                      f"p={r.get('p_raw')} mb={share['maxbars_share']}", flush=True)
        out[sleeve] = {"cell": cell, "target_r": k, "arms": rows}
    return out


# =====================================================================================
# assemble
# =====================================================================================

def _prior_artifact() -> dict:
    if OUT.is_file():
        try:
            return json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def assemble(stages: dict) -> dict:
    prior = _prior_artifact()
    return {
        "schema": "gtos.au.exit_contract_wiring.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                        "au_exit_contract_wiring.py",
        "session": "AU", "blocks": "B1550-B1599",
        "what": ("the two wired frontier exit contracts, proved identical to their research cells "
                 "trade by trade, and re-gated at the ratified rule with the maxbars share"),
        "gate": {"population": POPULATION, "option": OPTION, "alpha": OPTIONS[OPTION].alpha,
                 "declared_family": "CANDIDATE_BOOK_V1 @ CANDIDATE_FAMILY_V5.json",
                 "bands": ["flat_37_day_snapshot (CONTROL)", "low", "mid", "high"],
                 "multiplicity_note": ("no new looks: every arm is an exit-cell re-measurement of a "
                                       "sleeve already declared in CANDIDATE_BOOK_V1 (AI §0)")},
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "bars_archive": AD.BARS,
        "wiring": {
            "site": "src/components/ultimate_book/execution_packets.py FRONTIER_EXIT_OVERRIDES",
            "launcher": "run_book.py --frontier-exits <sleeve>[,<sleeve>]",
            "default": "empty selection; the committed profile object is returned by identity",
            "tests": "tests/ultimate_book/test_frontier_exit_contracts.py",
            "overrides": {s: dict(o) for s, o in FRONTIER_EXIT_OVERRIDES.items()},
        },
        "identity": stages.get("identity") or prior.get("identity"),
        "gate_rows": stages.get("gate") or prior.get("gate_rows"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=("identity", "gate", "all"))
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    sub = build_substrate()
    ledger = None if a.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AU")
    stages: dict = {}
    if a.stage in ("identity", "all"):
        print("stage identity:", flush=True)
        stages["identity"] = stage_identity(sub)
    if a.stage in ("gate", "all"):
        print("stage gate:", flush=True)
        stages["gate"] = stage_gate(sub, ledger)
    doc = assemble(stages)
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=False, default=str), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
