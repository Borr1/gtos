"""Spend the signed transfer: re-judge `energy_agri`'s FVG mechanism on its WHOLE class.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ap_energy_family_gate.py

THE QUESTION
------------
AF measured `fam_energy_fvg_retest_energy_h4` at **+0.4571 R/day pooled at mid** -- the
strongest mean in its entire 30-family grid -- with dispersion ratio 0.117, 3 of 3 members
positive and band stability across all four cost configurations. It REJECTed, and the reason
was sample, not sign.

**Read the coverage arithmetic carefully, because AP's own first draft got it wrong.** The
family has 76 trades; **14** are held out by the sealed March-2026 blackout BEFORE pricing
(`panel.py:207-218`, `blackout_r_gross +38.49`), so 62 are looked at, 53 priced and **9**
unpriced -- all 9 of them `NATGAS.cash`. `coverage_frac` 0.854839 is 53/62, NOT a fraction of
76, and `76 x (1 - 0.8548) = 11` mixes the denominators. **NINE trades were restored by this
transfer, not eleven.** OD-AI-8 says the fix is a signed energy-class peer transfer. It is
signed (`ENERGY_CLASS_PEER_TRANSFER_V1.json`). This spends it.

TWO REFUSALS STOOD IN FRONT OF THIS FAMILY, NOT ONE
---------------------------------------------------
The queue and AF §3.3 both name the commission. Measured here, the commission is the SECOND
refusal. The first is that `config/profiles/operator_profile.yaml` has no `instruments`
entry for `NATGAS_cash`, so `symbol_map.build_broker_symbol_resolver` returns the canonical
name unchanged and `AF_FAMILY_TRADES.json.gz` stores `symbol = "NATGAS_cash"` where it stores
`"UKOIL.cash"` for the two oil legs. `cost_r` then refuses with *"no broker truth for
'NATGAS_cash'"* before it ever reads a commission block.

No prior session's PROSE named this refusal -- but AF's own artifact PUBLISHED it 96 times,
in the member-level `first_reason` rows, and nobody read it. That is a more useful finding than
"nobody knew": the machine recorded the cause and the prose overwrote it, which is exactly what
`gate.py`'s misattributing PARTIAL UNIVERSE stamp did.

This run resolves `NATGAS_cash -> NATGAS.cash` from the **broker's own name** -- the costs
artifact's `broker_path: "Commodities\\NATGAS.cash"`, itself read from
`ftmo_symbols_get.jsonl`. That is a declared research-side use of the broker's spelling, not
a config change: the profile is R2-bound (H1) and, more to the point, the missing instrument
contract is a LIVE TRADEABILITY gap that no research run can close. It is on AP's handoff
list with its price.

WHAT IS DECLARED BEFORE ANY GATE IS COMPUTED
--------------------------------------------
Per AL §6.3 and the wave-10 agreement, the looks are declared first. **This run adds no
member to any declared family**, and that is a claim with a reason rather than a convenience:

  * `mxf_energy_fvg_retest_natgas_cash_h4` is already a declared member of
    `MECHANISM_CROSS_V1` (276) and already carried 9 trades in AF's artifact. Its look was
    taken; it could not be *evaluated*. Restoring a price re-measures a declared hypothesis.
  * AL's own precedent in `CANDIDATE_FAMILY_V2.json.history` is explicit: a threshold change
    adds a member because it changes which trades exist; an exit cell does not, because it
    re-measures the same hypothesis. A cost-coverage repair changes neither the trades nor
    the hypothesis -- it changes what can be *scored*.
  * so ledger rows YES and family ratchet NO. **The claim rests on the first two bullets --
    the trades and the generating rule are unchanged -- and NOT on the ledger.** An earlier
    draft leaned on "the ledger counts re-measurements so the DSR compensates", and an
    adversarial pass took that half apart: the gate is passed `n_trials=n_trials_pre`, which
    deliberately EXCLUDES this run's own rows, so nothing here deflates this run's own verdict.
    The ledger rows are for the NEXT look, which is what a prospective ledger is for.
    No `freeze_rule` clause covers "a declared member whose trades could not be PRICED" -- the
    acquisition clause is about `n_trades == 0` -- so this is an extension by analogy, declared
    as one, and the +1 arms below show the verdict does not turn on it.

Because "no rise" is the permissive direction, the run publishes a **+1 sensitivity arm** at
every bill so a reader can see the verdict does not turn on the judgement.

THE THREE COST ARMS, DECLARED BEFORE THE RESULTS
------------------------------------------------
  `control_v1_1`   V1_1 + AF's own symbol strings. Must reproduce AF's published numbers
                   byte-for-byte, or nothing else in this file means anything.
  `signed`         V1_2 (the signed transfer) + the broker's own NATGAS spelling.
  `zero_commission`  V1_2 with NATGAS's transferred commission forced to 0.00 USD/lot. This
                   is the counter-argument arm, and it exists because the signature's own
                   `the_counter_argument_stated_rather_than_hidden` names a reading under
                   which FTMO charges nothing on energy. 5.00 vs 0.00 is the whole quantity,
                   the x0.95/x1.05 class band cannot express it, so it gets an arm.

POPULATIONS: BOTH, BECAUSE THE RULE IS UNDECIDED
------------------------------------------------
AN's population-rule package is unmerged and unratified, so the wave-10 agreement requires
anything population-sensitive on BOTH `era_class == RECORDED` and the model's own `decidable`.
`all` is carried too because it is AF's own population and the control has to be like-for-like.

Offline and pure: reads artifacts, writes `AP_ENERGY_FAMILY_V2.json` and appends to the
trial ledger. Places no order and touches no config.
"""

from __future__ import annotations

import copy
import datetime as dt
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
TRADES = AUD / "phase7/receipts/AF_FAMILY_TRADES.json.gz"
DECL = AUD / "phase9/receipts/CANDIDATE_FAMILY_V2.json"
COSTS_V1_1 = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
COSTS_V1_2 = REPO / "research/operations/broker_truth_layer_2026_07_30/BROKER_TRUE_COSTS_V1_2.json"
OUT = HERE / "AP_ENERGY_FAMILY_V2.json"

FAMILY = "fam_energy_fvg_retest_energy_h4"
ACCOUNT = "FTMO"
SERVER = "FTMO-Server3"
BANDS = (None, "low", "mid", "high")
VERDICT_BAND = "mid"
#: The broker's own name for the instrument, from BROKER_TRUE_COSTS `broker_path`
#: ("Commodities\NATGAS.cash") -> ftmo_symbols_get.jsonl. NOT a config override.
BROKER_NAME_FIX = {"NATGAS_cash": "NATGAS.cash"}

#: AF's published figures for this family at `family|B_balanced|mid`. The control must
#: reproduce these exactly or the rest of the file is unreadable.
AF_PUBLISHED = {
    "n_trades": 76,
    "coverage_frac": 0.854839,
    "pooled_oos_mean_r": 0.4571223153521059,
    "p_raw": 0.17398260173982602,
    "verdict": "REJECT",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _zero_commission_costs(base_path: Path, symbol: str):
    """V1_2 with one instrument's transferred commission forced to 0.00 USD/lot.

    Written through the *signed* block rather than by swapping the kind, so the arm is still
    a `peer_transfer` and still refuses to call itself MEASURED. The point is to price the
    counter-argument, not to smuggle a zero past the coverage system.
    """
    doc = json.loads(base_path.read_text())
    rec = doc["accounts"][ACCOUNT]["instruments"][symbol]
    blk = copy.deepcopy(rec["commission"])
    blk["value"] = 0.0
    blk["transfer"] = {**blk["transfer"], "value": 0.0,
                       "rationale": (blk["transfer"]["rationale"]
                                     + " || SENSITIVITY ARM: value forced to 0.00 to price the "
                                       "counter-argument that FTMO charges nothing on energy "
                                       "(its Cash II CFD folder classification). Not the "
                                       "signed value.")}
    blk["provenance"] = "SENSITIVITY ARM, not the signed transfer: " + blk["provenance"]
    rec["commission"] = blk
    out = HERE / "_ap_zero_commission_arm.json"
    out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return load_broker_true_costs(out), out


def load_family(art: dict, resolve, *, fix: bool):
    """The one family's members, with the broker symbol resolved AF's way or the broker's."""
    info = art["grid"]["families"][FAMILY]
    members = []
    for sym in info["symbols"]:
        broker = resolve(sym)
        if fix:
            broker = BROKER_NAME_FIX.get(sym, broker)
        members.append(fam.FamilyMember(
            member=fam.member_name(info["mechanism"].split("_", 1)[0] and
                                   "energy_fvg_retest", sym, 16388),
            mechanism_key="energy_fvg_retest", mechanism=info["mechanism"],
            parent_sleeve=info["parent_sleeve"], symbol=sym, broker_symbol=broker,
            timeframe=16388, asset_class=info["asset_class"],
            is_authored_cell=True,
            profile_supported=bool(getattr(resolve, "supports", lambda _s: True)(sym))))
    assert {m.member for m in members} == set(info["members"]), (
        sorted(m.member for m in members), sorted(info["members"]))
    return members


def to_records(rows: list[dict], sleeve: str, *, fix: bool) -> list[TradeRecord]:
    out = []
    for r in rows:
        if not r["engine_reachable"]:
            continue
        sym = r["symbol"]
        if fix:
            sym = BROKER_NAME_FIX.get(sym, sym)
        out.append(TradeRecord(
            sleeve=sleeve, symbol=sym,
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"entry_hour_utc": r["entry_hour_utc"], "mfe_r": r["mfe_r"],
                      "mae_r": r["mae_r"], "hold_hours": r["hold_hours"],
                      "exit_reason": r["exit_reason"],
                      "symbol_canonical": r["symbol_canonical"]}))
    return out


def era_decidable_crosstab(recs: list[TradeRecord], smodel) -> dict:
    """`era_class` x `decidable`, because AN's two candidate populations may not be nested.

    Measured here they are NOT: on this family 26 of 73 RECORDED trades are un-decidable and 3
    decidable trades are not RECORDED, so neither predicate is a restriction of the other and
    "publish on both" is not a formality.
    """
    tab: dict[str, int] = {}
    for r in recs:
        try:
            est = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=VERDICT_BAND)
        except Exception:  # noqa: BLE001
            tab["UNPRICEABLE|-"] = tab.get("UNPRICEABLE|-", 0) + 1
            continue
        k = f"{est.era_class}|decidable={est.decidable}"
        tab[k] = tab.get(k, 0) + 1
    rec_t = sum(v for k, v in tab.items() if k.startswith("RECORDED|"))
    dec_t = sum(v for k, v in tab.items() if k.endswith("True"))
    both = tab.get("RECORDED|decidable=True", 0)
    return {
        "cells": dict(sorted(tab.items())),
        "n_recorded": rec_t, "n_decidable": dec_t, "n_both": both,
        "recorded_not_decidable": rec_t - both, "decidable_not_recorded": dec_t - both,
        "nested": (both == rec_t) or (both == dec_t),
        "note": ("if `nested` is false the two candidate populations CROSS, and a rule that "
                 "picks one is choosing a different trade set rather than a stricter one. "
                 "Evidence for AN's population decision."),
    }


def population_filter(recs: list[TradeRecord], which: str, smodel) -> tuple[list, dict]:
    """`all` / `recorded` / `decidable`, with the era mix recorded either way."""
    if which == "all":
        return list(recs), {"predicate": "none (AF's own population)", "n_in": len(recs),
                            "n_out": len(recs)}
    mix: dict[str, int] = {}
    kept = []
    for r in recs:
        try:
            est = smodel.estimate(r.symbol, ACCOUNT, r.entry_utc, band=VERDICT_BAND)
        except Exception:  # noqa: BLE001 - an unpriceable symbol is a real gap, counted as one
            mix["unpriceable"] = mix.get("unpriceable", 0) + 1
            continue
        mix[est.era_class] = mix.get(est.era_class, 0) + 1
        if which == "recorded" and est.era_class == "RECORDED":
            kept.append(r)
        elif which == "decidable" and est.decidable:
            kept.append(r)
    return kept, {"predicate": ({"recorded": "era_class == RECORDED",
                                 "decidable": "spread_model decidable is True"}[which]),
                  "band": VERDICT_BAND, "era_class_mix": mix,
                  "n_in": len(recs), "n_out": len(kept),
                  "retained_frac": (round(len(kept) / len(recs), 5) if recs else None)}


def row_of(sleeve: str, v) -> dict:
    """Every number an adversarial reader asked for, not only the pooled headline.

    `pooled_oos_mean_r` is `equal_by_fold`, so it can rise while per-trade expectancy FALLS if
    added trades land in thin folds -- which is exactly what the 9 restored NATGAS trades do
    (+23.4 % pooled, -5.6 % per trade). Publishing only the pooled figure would have let this
    session claim an improvement the per-trade series does not support. `measured_frac` is here
    for the same reason: the whole family prices at 0.0 MEASURED (every term is TRANSFERRED or
    MODELLED), and a coverage of 1.00 that is 100 % un-measured is a different claim from a
    coverage of 1.00 that is measured. Both added after an adversarial pass.
    """
    g = v.gates
    exp = g.get("expectancy", {}) or {}
    life = g.get("lifetime", {}) or {}
    cov = v.coverage or {}
    return {
        "verdict": v.verdict.value, "n_trades": v.n_trades,
        "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw, "q_value": v.q_value,
        "pooling_weights": exp.get("pooling_weights"),
        "oos_mean_r_per_trade": exp.get("oos_mean_r_per_trade"),
        "n_scored_oos_trades": exp.get("n_scored_oos_trades"),
        "lifetime_mean_r_net_per_trade_all_folds": life.get("mean_r_net_per_trade_all_folds"),
        "robustness_retention": (g.get("robustness", {}) or {}).get("retention"),
        "robustness_retention_floor": (g.get("robustness", {}) or {}).get("retention_floor"),
        "n_priced": cov.get("n_priced"), "n_unpriced": cov.get("n_unpriced"),
        "n_blackout_dropped": cov.get("n_blackout_dropped"),
        "blackout_r_gross": cov.get("blackout_r_gross"),
        "measured_frac": cov.get("measured_frac"),
        "weakest_coverage": cov.get("weakest_coverage"),
        "unpriced_reasons": cov.get("unpriced_reasons"),
        "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
        "n_folds_evaluable": g.get("sample", {}).get("n_folds_evaluable"),
        "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
        "evaluated_symbols": (v.universe_restriction or {}).get("evaluated_symbols"),
        "dropped_symbols": (v.universe_restriction or {}).get("dropped_symbols"),
        "failing_gates": sorted(k for k, d in g.items()
                                if isinstance(d, dict) and d.get("pass") is False),
        "first_reason": (v.reasons[0][:500] if v.reasons else None),
    }


def main() -> dict:
    t0 = dt.datetime.now(dt.timezone.utc)
    from src.costs.spread_model import load_spread_model

    try:
        smodel = load_spread_model()
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            f"the spread model will not load: {e}\n`git sparse-checkout add "
            f"research/operations/spread_model_2026_07_29` hydrates it. Without it every "
            f"banded verdict silently becomes unavailable.") from None

    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    declared = CF.load_candidate_family(DECL)

    # --- DECLARE THE LOOKS FIRST -------------------------------------------------------
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AP")
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    n_trials_pre = int(nt["n_trials"])
    bills = {
        "MECHANISM_CROSS_V1@all_declared": declared.effective_size("MECHANISM_CROSS_V1"),
        "CANDIDATE_BOOK_V1@all_declared": declared.effective_size("CANDIDATE_BOOK_V1"),
        "CANDIDATE_BOOK_V1@looks_taken": declared.effective_size(
            "CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN),
    }
    bills["MECHANISM_CROSS_V1@all_declared_plus1_sensitivity"] = (
        bills["MECHANISM_CROSS_V1@all_declared"] + 1)
    bills["CANDIDATE_BOOK_V1@all_declared_plus1_sensitivity"] = (
        bills["CANDIDATE_BOOK_V1@all_declared"] + 1)
    print(f"declared bills: {bills}")
    print(f"trial ledger before this run: n_trials = {n_trials_pre} ({nt.get('basis')})")

    arms_cfg = [("control_v1_1", COSTS_V1_1, False), ("signed", COSTS_V1_2, True),
                ("zero_commission", None, True)]

    zero_costs, zero_path = _zero_commission_costs(COSTS_V1_2, "NATGAS.cash")
    results: dict = {}
    for arm, path, fix in arms_cfg:
        costs = zero_costs if path is None else load_broker_true_costs(path)
        cost_sha = _sha(zero_path if path is None else path)
        members = load_family(art, resolve, fix=fix)
        by_member = {m.member: to_records(art["trades"][m.member], m.member, fix=fix)
                     for m in members}
        with fam.fidelity_scope(members):
            pooled_all = fam.pool_family(FAMILY, by_member, members)
        allow = {FAMILY: tuple(sorted({m.broker_symbol for m in members}))}
        allow.update({m.member: (m.broker_symbol,) for m in members})

        results[arm] = {
            "cost_artifact": (str(path.relative_to(REPO)) if path is not None
                              else "V1_2 with NATGAS.cash commission forced to 0.00 (arm only)"),
            "cost_artifact_sha256": cost_sha,
            "broker_symbol_fix_applied": fix,
            "broker_symbols": {m.symbol: m.broker_symbol for m in members},
            "profile_supported": {m.symbol: m.profile_supported for m in members},
            "member_trade_counts": {m: len(v) for m, v in by_member.items()},
            "populations": {},
        }
        for pop in ("all", "recorded", "decidable"):
            pooled, pinfo = population_filter(pooled_all, pop, smodel)
            per_member_pop = {}
            for m in members:
                kept, _ = population_filter(by_member[m.member], pop, smodel)
                per_member_pop[m.member] = kept
            block = {"restriction": pinfo, "runs": {}, "members": {}}
            for m in members:
                rows = per_member_pop[m.member]
                block["members"][m.member] = {
                    "symbol": m.symbol, "broker_symbol": m.broker_symbol,
                    "n_trades": len(rows),
                    "mean_r_gross": (round(statistics.fmean(t.r_gross for t in rows), 5)
                                     if rows else None)}
            with fam.fidelity_scope(members):
                for opt, base in OPTIONS.items():
                    for band in BANDS:
                        bname = band or "snapshot"
                        for bill_label, bill in bills.items():
                            if (opt != "B_balanced" or band != VERDICT_BAND) and \
                                    "plus1" in bill_label:
                                continue    # the sensitivity is published once, not 36 times
                            spec = base.with_(
                                spec_id=f"{base.spec_id}_ap_energy_{arm}_{pop}_{bname}",
                                spread_band=band, cost_artifact_sha256=cost_sha,
                                declared_family_size=bill, n_trials=n_trials_pre,
                                n_trials_basis=(f"MEASURED from {DEFAULT_TRIAL_LEDGER} "
                                                f"BEFORE this run's own rows -- "
                                                f"{nt.get('basis')}"),
                                sleeve_symbol_allowlist=allow)
                            trades = {FAMILY: pooled, **per_member_pop}
                            r = run_gate(trades, spec, costs=costs, server=SERVER)
                            key = f"{opt}|{bname}|{bill_label}"
                            block["runs"][key] = {
                                "option": opt, "alpha": base.alpha, "band": bname,
                                "declared_family_size": bill, "bill": bill_label,
                                "spec_sha256": spec.seal(),
                                "rows": {s: row_of(s, v)
                                         for s, v in sorted(r.verdicts.items())},
                            }
            results[arm]["populations"][pop] = block
            fr = block["runs"][f"B_balanced|{VERDICT_BAND}|MECHANISM_CROSS_V1@all_declared"]
            fam_row = fr["rows"][FAMILY]
            print(f"  {arm:16s} {pop:10s} n={fam_row['n_trades']:3d} "
                  f"cov={fam_row['coverage_frac']} mean={fam_row['pooled_oos_mean_r']} "
                  f"p={fam_row['p_raw']} -> {fam_row['verdict']} "
                  f"(fails {fam_row['failing_gates']})", flush=True)

    # --- the control ------------------------------------------------------------------
    ctrl = (results["control_v1_1"]["populations"]["all"]["runs"]
            [f"B_balanced|{VERDICT_BAND}|MECHANISM_CROSS_V1@all_declared"]["rows"][FAMILY])
    control = {"af_published": AF_PUBLISHED, "reproduced": {k: ctrl.get(k) for k in AF_PUBLISHED},
               "holds": all(
                   (abs(ctrl[k] - v) < 1e-9) if isinstance(v, float) else ctrl[k] == v
                   for k, v in AF_PUBLISHED.items())}
    print(f"\ncontrol vs AF published: {'HOLDS' if control['holds'] else 'BROKEN'}")
    if not control["holds"]:
        print(f"  published {AF_PUBLISHED}\n  reproduced {control['reproduced']}")

    # --- ledger: one row per (arm, population) family look, AFTER the gates ------------
    # One row per MEASUREMENT CELL, not one per (arm, population). AP's first version recorded
    # 9 rows for 36 distinct (arm x band x population) cells -- a 4x under-record of its own
    # re-measurements, in a ledger whose whole job is to count looks. Caught by an adversarial
    # pass. The bill is held at the ratified CANDIDATE_BOOK_V1@all_declared so the rows are
    # comparable; the band and option are in `variant`, which is where the DSR reads them.
    for arm in results:
        for pop, block in results[arm]["populations"].items():
          for key, r in sorted(block["runs"].items()):
            if r["bill"] != "CANDIDATE_BOOK_V1@all_declared":
                continue
            row = r["rows"][FAMILY]
            ledger.record(
                mechanism="h4_fvg_retest_energy_gate", sleeve=FAMILY,
                variant={"scope": "pooled_family", "asset_class": "energy",
                         "timeframe": "H4", "n_members": 3, "cost_arm": arm,
                         "population": pop, "band": r["band"], "option": r["option"],
                         "alpha": r["alpha"],
                         "declared_family_size": r["declared_family_size"],
                         "bill": "CANDIDATE_BOOK_V1@all_declared",
                         "adds_no_family_member": True},
                window=results[arm]["populations"][pop]["restriction"]["predicate"],
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(row["verdict"], "evaluated"),
                metric=row["pooled_oos_mean_r"], metric_name="pooled_oos_mean_r",
                spec_sha256=r["spec_sha256"],
                note=("Session AP (B1350-B1399), OD-AI-8 signed energy-class peer transfer "
                      "spent. RE-MEASUREMENT of a declared look, not a new hypothesis: no "
                      "family member added (see the module docstring)."))

    out = {
        "schema": "gtos.walkforward.energy_family_v2.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                         "ap_energy_family_gate.py"),
        "generated_utc": t0.isoformat(),
        "session": "AP (wave 10), blocks B1350-B1399",
        "decision": "OD-AI-8",
        "family": FAMILY,
        "trades_artifact": {"path": str(TRADES.relative_to(REPO)), "sha256": _sha(TRADES)},
        "signature": {
            "path": "docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                    "ENERGY_CLASS_PEER_TRANSFER_V1.json",
            "sha256": _sha(HERE / "ENERGY_CLASS_PEER_TRANSFER_V1.json"),
        },
        "declaration": {"path": str(DECL.relative_to(REPO)), "sha256": _sha(DECL),
                        "bills": bills},
        "two_refusals_not_one": {
            "first": ("config/profiles/operator_profile.yaml has no `instruments` entry "
                      "for NATGAS_cash, so the resolver returns the canonical name and "
                      "cost_r refuses on \"no broker truth for 'NATGAS_cash'\" before it "
                      "reads any commission. NO PRIOR SESSION'S PROSE NAMED IT -- AF §3.3, "
                      "OD-AI-8 and FOURTH_REVIEW §4.6/§9 all named the commission or a tick "
                      "capture, and AF's own family-level PARTIAL UNIVERSE stamp mis-named it "
                      "as a missing spread. But the FACT was published: AF's member-level rows "
                      "in FAMILY_ADMISSION_V1.json print the exact string \"no broker truth "
                      "for 'NATGAS_cash' on FTMO\" 96 times, with the exact count 9, and it "
                      "went unread. Corrected by an adversarial pass over AP's own claim; the "
                      "first version said 'named by no prior session', which the artifact "
                      "refutes."),
            "second": ("commission.kind == 'unknown' -- the one OD-AI-8 and AF §3.3 name."),
            "handled_how": ("this run uses the broker's own spelling for the first and the "
                            "signed transfer for the second; the profile is R2-bound and the "
                            "missing instrument contract is a live-tradeability gap on AP's "
                            "handoff list."),
        },
        "multiplicity": {
            "adds_no_family_member": True,
            "why": ("mxf_energy_fvg_retest_natgas_cash_h4 is already a declared member of "
                    "MECHANISM_CROSS_V1 and already carried 9 trades. A cost-coverage repair "
                    "changes neither the trades nor the hypothesis; it changes what can be "
                    "scored. AL's CANDIDATE_FAMILY_V2 history draws the same line for exit "
                    "cells."),
            "and_it_is_the_permissive_direction_so_it_is_tested": (
                "every bill is also run at +1 (`*_plus1_sensitivity`) at the ratified option "
                "and band."),
            "ratchet_no_because_trades_and_rule_unchanged": (
                "the claim rests on the trades and the generating rule being unchanged, and on "
                "NOTHING ELSE. An earlier draft added 'and the ledger's DSR deflation compensates "
                "for the re-measurement'; an adversarial pass took that half apart, because the "
                "gate is passed `n_trials=n_trials_pre`, which deliberately EXCLUDES this run's "
                "own rows -- so nothing here deflates this run's own verdict. The ledger rows are "
                "for the NEXT look, which is what a prospective ledger is for. No `freeze_rule` "
                "clause covers 'a declared member whose trades could not be PRICED' (the "
                "acquisition clause is about n_trades == 0), so this is an extension by ANALOGY, "
                "declared as one, and the +1 arms are what show the verdict does not turn on it."),
            "n_trials_before_this_run": n_trials_pre,
            "n_trials_basis": nt.get("basis"),
        },
        "ratified_rule": json.loads(DECL.read_text()).get("ratified_rule"),
        "population_crosstab_for_AN": era_decidable_crosstab(
            fam.pool_family(FAMILY, {m.member: to_records(art["trades"][m.member], m.member,
                                                          fix=True)
                                     for m in load_family(art, resolve, fix=True)},
                            load_family(art, resolve, fix=True)),
            smodel),
        "verdict_band": VERDICT_BAND,
        "control": control,
        "arms": results,
        "ledger_rows_written": ledger.n_written,
        "ledger_write_errors": ledger.write_errors,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size / 1e3:.0f} KB); "
          f"ledger {ledger.n_written} rows, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
