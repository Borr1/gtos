#!/usr/bin/env python3
"""Session AE — the evidence the two owner decisions need, and every variant that produced it.

Run: ``PYTHONPATH=. python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ae_owner_evidence.py``

Emits four receipts beside this file and appends every evaluated variant to the shared trial
ledger (WAVE_7_WORKING_AGREEMENT section 3):

* ``AE_LEGACY_VS_COST_TRUE.json``   — what swapping the evidence basis did, sleeve by sleeve.
* ``AE_ADMISSION_FLOOR.json``       — day-blocked vs raw-trade n, over all 29 cost-true sleeves.
* ``AE_ARMED_FOUR.json``            — the one-minute table: what the lane would recommend today.
* ``AE_OWNER_DECISIONS.json``       — FOURTH_REVIEW section 8 items 6 and 8, with numbers attached.

Nothing here actuates, mutates a config, or contacts a broker. Every number is recomputed from
committed artifacts on each run.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.components.ultimate_book.cost_true_splits import build_cost_true_evidence, load_splits
from src.components.ultimate_book.learning_actuator import (
    LIVE_MIN_DAY_BLOCKS_SUPPORT,
    LIVE_MIN_N_SUPPORT,
    LIVE_UP_MAX_EXCESS,
    LIVE_UP_STEP,
    MAX_UP,
    MIN_N,
    SleeveEvidence,
    recommend,
)
from src.components.ultimate_book.live_evidence import CALIBRATION_V1, CALIBRATION_V2
from src.research_infra.validation_integrity.trial_budget_ledger import (
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
SURVIVOR = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"

# The seven CP4/CP5 triples that WERE `rerate_book_from_live.BACKTEST` until 2026-07-30, priced by
# the legacy cost map (F38: zero commission; F39: wrong sign on tick erosion). Retained here, and
# only here, as the comparator for what retiring them changed. Not evidence for anything.
LEGACY = {
    "idxrev": (-0.024, -0.089, -0.000, 994, 2441, 1423, "breadth_falsified"),
    "metals_core": (+0.146, -0.061, +0.853, 105, 24, 49, "train_validated"),
    "sub_mid_dn_revert": (+0.228, +0.674, +1.167, 82, 70, 58, "train_validated"),
    "metals_softband": (+0.478, +1.527, +0.215, 37, 15, 39, "train_validated"),
    "crypto": (None, +1.512, +0.806, 0, 7, 60, "train_validated"),
    "fx_jpy": (-0.041, +0.003, +0.123, 4144, 1556, 744, "breadth_falsified"),
    "fx_jpy_ny": (-0.013, -0.071, +0.153, 1615, 702, 274, "forward_only"),
}


def legacy_evidence() -> dict:
    return {name: SleeveEvidence(name, train_meanR=t[0], oos_meanR=t[1], sealed_meanR=t[2],
                                 train_n=t[3], oos_n=t[4], sealed_n=t[5], status=t[6],
                                 evidence_basis="legacy_cp4_cp5")
            for name, t in LEGACY.items()}


def trade_count_variant(ev: SleeveEvidence) -> SleeveEvidence:
    """The same cost-true evidence admitted on RAW TRADE counts — the pre-AE floor."""
    return SleeveEvidence(
        ev.sleeve, train_meanR=ev.train_meanR, oos_meanR=ev.oos_meanR, sealed_meanR=ev.sealed_meanR,
        train_n=ev.train_n, oos_n=ev.oos_n, sealed_n=ev.sealed_n, status=ev.status,
        evidence_basis=ev.evidence_basis + "|floor=trades")


def min_n_disagreement_rule(ev: SleeveEvidence):
    """PROPOSED (owner's call): a discarded split that DISAGREES IN SIGN blocks the size-up.

    R section 4 item 15: `metals_core` FTMO's SIZE_UP x1.15 survived only because its one negative
    split (oos -0.061 on n=24) fell under MIN_N and was dropped, so "positive on every split" was
    met by discarding the split that disagreed. Cost-true evidence resolves that INSTANCE -- the
    negative is now the 232-trade/118-day oos, which no floor can discard -- but not the RULE.

    The rule as proposed: run `recommend()` unchanged, then, if any split was dropped for being
    under the floor and its mean has the opposite sign to the admitted ones, cap at KEEP. It can
    only ever remove a size-up; it cannot gate, down-weight, or rescue anything.

    Returns (recommendation, applied, note).
    """
    r = recommend(ev)
    if r.conf_mult <= 1.0:
        return r, False, ""
    dropped = [(s, m, eff) for s, m, eff in ev.splits() if m is not None and eff < MIN_N]
    disagree = [(s, m, eff) for s, m, eff in dropped if m <= 0.0]
    if not disagree:
        return r, False, ""
    r.conf_mult = 1.0
    r.verdict = "KEEP"
    r.reason += (" MIN_N DISAGREEMENT RULE: size-up refused because "
                 + ", ".join(f"{s} {m:+.3f} (n_eff {eff} < {MIN_N})" for s, m, eff in disagree)
                 + " was dropped for sample size and disagrees in sign with the admitted splits.")
    return r, True, "; ".join(f"{s} {m:+.3f}@{eff}" for s, m, eff in disagree)


def _row(ev: SleeveEvidence, r) -> dict:
    return {
        "verdict": r.verdict, "conf_mult": r.conf_mult, "gate": r.gate,
        "splits": {n: {"meanR": m, "n_trades": nt, "n_days": nd, "n_effective": eff, "unit": u}
                   for n, m, nt, nd, eff, u in ev.split_records()},
        "evidence_basis": ev.evidence_basis,
    }


def main() -> int:
    led = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AE")
    doc_splits = load_splits()
    cost_true = build_cost_true_evidence(doc_splits)
    legacy = legacy_evidence()
    survivor = json.loads(SURVIVOR.read_text()) if SURVIVOR.is_file() else {"accounts": {}}
    tiers = {a: {s: r.get("survivor_tier") for s, r in b["sleeves"].items()}
             for a, b in survivor["accounts"].items()}
    armed = {a: list(b.get("survivors") or []) for a, b in survivor["accounts"].items()}
    window = "1992-2026 archive, broker-true (BROKER_TRUE_COSTS_V1_1)"

    # ---------------------------------------------------------------- 1. legacy vs cost-true
    lvc: dict = {}
    for name in sorted(LEGACY):
        lr = recommend(legacy[name])
        led.record(mechanism="learning_actuator.recommend", sleeve=name,
                   variant={"evidence_basis": "legacy_cp4_cp5", "floor": "trades"},
                   window="CP4/CP5 replay, legacy cost map", outcome="rejected",
                   metric=lr.conf_mult, metric_name="conf_mult",
                   note="the retired backtest half; logged as the comparator, not as evidence")
        ct = cost_true.get(name)
        cr = recommend(ct) if ct is not None else None
        if cr is not None:
            led.record(mechanism="learning_actuator.recommend", sleeve=name,
                       variant={"evidence_basis": "cost_true", "floor": "day_blocks"},
                       window=window, outcome="evaluated",
                       metric=cr.conf_mult, metric_name="conf_mult", note=cr.verdict)
        lvc[name] = {
            "legacy": _row(legacy[name], lr),
            "cost_true": _row(ct, cr) if cr is not None else {"verdict": "NOT_IN_ARTIFACT"},
            "verdict_moved": (cr.verdict != lr.verdict) if cr is not None else None,
            "conf_mult_delta": (round(cr.conf_mult - lr.conf_mult, 4)) if cr is not None else None,
            "tiers": {a: t.get(name) for a, t in tiers.items()},
        }

    # ---------------------------------------------------------------- 2. the admission floor
    floor: dict = {}
    for name, ev in sorted(cost_true.items()):
        day = recommend(ev)
        tr = recommend(trade_count_variant(ev))
        led.record(mechanism="learning_actuator.evaluable_splits", sleeve=name,
                   variant={"admission_floor": "raw_trades", "MIN_N": MIN_N},
                   window=window, outcome="rejected", metric=tr.conf_mult,
                   metric_name="conf_mult",
                   note=f"{tr.verdict}; superseded by the day-blocked floor")
        led.record(mechanism="learning_actuator.evaluable_splits", sleeve=name,
                   variant={"admission_floor": "day_blocks", "MIN_N": MIN_N},
                   window=window, outcome="admitted", metric=day.conf_mult,
                   metric_name="conf_mult", note=day.verdict)
        floor[name] = {
            "day_blocked": {"verdict": day.verdict, "conf_mult": day.conf_mult},
            "raw_trades": {"verdict": tr.verdict, "conf_mult": tr.conf_mult},
            "moved": day.verdict != tr.verdict or day.conf_mult != tr.conf_mult,
            "splits": {n: {"n_trades": nt, "n_days": nd} for n, _m, nt, nd, _e, _u
                       in ev.split_records()},
        }
    floor_moved = sorted(k for k, v in floor.items() if v["moved"])

    # ---------------------------------------------------------------- 3. the MIN_N rule proposal
    minn: dict = {}
    for label, book in (("cost_true", cost_true), ("legacy_cp4_cp5", legacy)):
        rows = {}
        for name, ev in sorted(book.items()):
            base = recommend(ev)
            proposed, applied, note = min_n_disagreement_rule(
                SleeveEvidence(**{k: v for k, v in ev.__dict__.items()}))
            if applied:
                led.record(mechanism="learning_actuator.min_n_disagreement_rule", sleeve=name,
                           variant={"rule": "drop_disagreeing_under_floor_blocks_size_up"},
                           window=window if label == "cost_true" else "CP4/CP5 replay",
                           outcome="evaluated", metric=proposed.conf_mult,
                           metric_name="conf_mult", note=f"{base.verdict}->{proposed.verdict}: {note}")
            if applied or base.conf_mult > 1.0:
                rows[name] = {"current": {"verdict": base.verdict, "conf_mult": base.conf_mult},
                              "with_rule": {"verdict": proposed.verdict,
                                            "conf_mult": proposed.conf_mult},
                              "rule_applied": applied, "disagreeing_splits": note}
        minn[label] = rows

    # ---------------------------------------------------------------- 4. the raise-side caps
    ladder: dict = {}
    for step in (0.05, 0.10, 0.25):
        cur, cycles = 1.0, 0
        while cur < MAX_UP and cycles < 50:
            cur = min(MAX_UP, cur + step)
            cycles += 1
        ladder[str(step)] = {"cycles_from_1.00_to_MAX_UP": cycles,
                             "shipped": step == LIVE_UP_STEP}
        led.record(mechanism="learning_actuator.LIVE_UP_STEP", sleeve="",
                   variant={"LIVE_UP_STEP": step}, window="n/a (rule parameter)",
                   outcome="admitted" if step == LIVE_UP_STEP else "evaluated",
                   metric=float(cycles), metric_name="owner_cycles_to_MAX_UP",
                   note="one cycle is one owner-applied re-rating, not one tick")

    # ---------------------------------------------------------------- 5. family-wise scopes
    cal2 = json.loads(CALIBRATION_V2.read_text()) if CALIBRATION_V2.is_file() else None
    cal1 = json.loads(CALIBRATION_V1.read_text()) if CALIBRATION_V1.is_file() else None
    fam: dict = {}
    if cal2:
        for account, sleeves in cal2["accounts"].items():
            for sleeve, row in sleeves.items():
                if not row.get("calibrated"):
                    continue
                for scope, s in row["familywise_sensitivity"].items():
                    led.record(mechanism="live_evidence_calibration.family_scope", sleeve=sleeve,
                               variant={"family_scope": scope, "account": account,
                                        "budget_down": s["budget_down"],
                                        "budget_kill": s["budget_kill"]},
                               window="first passage over n_max=60 live fills, day-block null",
                               outcome="admitted" if scope == cal2["familywise_scope"] else "evaluated",
                               metric=s["power_if_edge_gone"]["p_gate_within_n_max"],
                               metric_name="p_gate_if_edge_gone",
                               note=f"{s['stop_outs_to_down_weight_measured']} stop-outs to "
                                    f"down-weight, {s['stop_outs_to_gate_measured']} to gate")
                if account == "FTMO" and sleeve in armed.get("FTMO", []):
                    fam[sleeve] = {
                        scope: {
                            "budget_per_cell_down": s["budget_down"],
                            "stop_outs_to_down_weight": s["stop_outs_to_down_weight_measured"],
                            "stop_outs_to_gate": s["stop_outs_to_gate_measured"],
                            "p_gate_if_edge_gone": s["power_if_edge_gone"]["p_gate_within_n_max"],
                        } for scope, s in row["familywise_sensitivity"].items()
                    }

    # ---------------------------------------------------------------- 6. the armed-four table
    armed_rows: dict = {}
    for account, names in armed.items():
        rows = {}
        for name in names:
            ev = cost_true.get(name)
            if ev is None:
                rows[name] = {"verdict": "INSUFFICIENT_EVIDENCE", "conf_mult": 1.0,
                              "why": "no generated trades in the estate walk — unmeasured, "
                                     "not dead"}
                continue
            r = recommend(ev)
            cal_row = ((cal2 or {}).get("accounts", {}).get(account, {}) or {}).get(name) or {}
            rows[name] = {
                "verdict": r.verdict,
                "conf_mult": r.conf_mult,
                "tier": tiers.get(account, {}).get(name),
                "splits": {n: {"meanR": (round(m, 4) if m is not None else None),
                               "n_trades": nt, "n_days": nd, "clears_floor": eff >= MIN_N}
                           for n, m, nt, nd, eff, _u in ev.split_records()},
                "live_n": 0,
                "brake_stop_outs_to_down_weight": cal_row.get("stop_outs_to_down_weight_measured"),
                "brake_stop_outs_to_gate": cal_row.get("stop_outs_to_gate_measured"),
                "raise_bar": {"fills": LIVE_MIN_N_SUPPORT, "day_blocks": LIVE_MIN_DAY_BLOCKS_SUPPORT,
                              "step_per_cycle": LIVE_UP_STEP},
                "reason": r.reason,
            }
        armed_rows[account] = rows

    out = {
        "AE_LEGACY_VS_COST_TRUE.json": {
            "schema": "gtos.learning_lane.ae_legacy_vs_cost_true.v1",
            "what": "the actuator's backtest half before and after AE, on the 7 sleeves the legacy "
                    "constant covered. The cost-true side additionally covers 22 more.",
            "legacy_basis": "CP4/CP5 replay at the legacy cost map (F38 zero commission, F39 wrong "
                            "sign on tick erosion)",
            "cost_true_basis": doc_splits.get("cost_artifact"),
            "cost_look_ahead": doc_splits.get("cost_look_ahead"),
            "rows": lvc,
            "verdicts_moved": sorted(k for k, v in lvc.items() if v["verdict_moved"]),
        },
        "AE_ADMISSION_FLOOR.json": {
            "schema": "gtos.learning_lane.ae_admission_floor.v1",
            "what": f"MIN_N={MIN_N} counted in day-blocks (shipped) vs raw trades (pre-AE), over "
                    "all cost-true sleeves",
            "why": "trades cluster on days; R measured lag-1 rho 0.511 on sub_xvol_pullback and "
                   "0.441 on crypto, and corrected the live null only",
            "sleeves_whose_verdict_moved": floor_moved,
            "rows": floor,
        },
        "AE_ARMED_FOUR.json": {
            "schema": "gtos.learning_lane.ae_armed_four.v1",
            "what": "what the lane would recommend TODAY for each account's survivor set, "
                    "default-off, on cost-true evidence plus the live record",
            "live_record": "no armed sleeve has a closed live position; live_n = 0 on all of them, "
                           "so every verdict below is the backtest half alone",
            "accounts": armed_rows,
        },
        "AE_OWNER_DECISIONS.json": {
            "schema": "gtos.learning_lane.ae_owner_decisions.v1",
            "decision_6_false_alarm_budgets_and_raise_caps": {
                "what_is_being_set": "the two false-alarm budgets, the family they apply to, and "
                                     "the raise-side caps",
                "current": {
                    "familywise_down": (cal2 or {}).get("familywise_down"),
                    "familywise_kill": (cal2 or {}).get("familywise_kill"),
                    "family_scope_shipped": (cal2 or {}).get("familywise_scope"),
                    "LIVE_UP_STEP": LIVE_UP_STEP,
                    "LIVE_UP_MAX_EXCESS": LIVE_UP_MAX_EXCESS,
                    "LIVE_MIN_N_SUPPORT": LIVE_MIN_N_SUPPORT,
                    "LIVE_MIN_DAY_BLOCKS_SUPPORT": LIVE_MIN_DAY_BLOCKS_SUPPORT,
                    "MAX_UP": MAX_UP,
                    "owner_dial_cap_default": MAX_UP,
                },
                "family_scope_cost_on_the_armed_four_FTMO": fam,
                "v1_comparison": {
                    "note": "V1 solved every cell at the full budget; its columns are the `cell` "
                            "scope above, modulo the seed defect that made V1 unreproducible",
                    "v1_book_level_down_bound": (
                        round(min(1.0, 22 * (cal1 or {}).get("familywise_down", 0.20)), 3)
                        if cal1 else None),
                },
                "raise_ladder": ladder,
                "what_the_owner_actually_chooses": [
                    "the family the budget applies to (armed / book / account / cell)",
                    "the two budget numbers themselves",
                    "LIVE_UP_STEP, i.e. how many of his own re-rate cycles a sleeve needs to reach "
                    "MAX_UP on live evidence alone",
                    "owner_dial_cap, which no recommendation may exceed whatever the evidence says",
                ],
            },
            "decision_8_min_n_rule": {
                "what_is_being_set": "whether a split dropped for sample size may be silently "
                                     "discarded when it disagrees in sign with the admitted ones",
                "origin": "R section 4 item 15 — metals_core FTMO's SIZE_UP x1.15 survived only by "
                          "dropping its one negative split (oos -0.061 at n=24 < MIN_N)",
                "status_of_that_instance": "resolved by evidence, not by rule: on cost-true splits "
                                           "metals_core's negative is the 232-trade / 118-day oos, "
                                           "which no sample floor can discard, and the sleeve is "
                                           "DOWN_WEIGHT x0.50",
                "proposed_rule": "if a split was dropped for n_eff < MIN_N and its mean disagrees "
                                 "in sign with the admitted splits, cap the recommendation at KEEP. "
                                 "One-sided: it can only remove a size-up.",
                "what_it_would_change": minn,
            },
        },
    }
    for name, payload in out.items():
        (HERE / name).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
        print(f"wrote {HERE / name}")
    s = led.summary()
    print(f"trial ledger: +{s['written_this_process']} rows this run "
          f"({s['n_trials']} total, {s['by_session']}), "
          f"{s['write_errors_this_process']} write errors -> {led.path}")
    print(f"verdicts moved by the evidence swap: "
          f"{out['AE_LEGACY_VS_COST_TRUE.json']['verdicts_moved']}")
    print(f"verdicts moved by the day-blocked floor: {floor_moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
