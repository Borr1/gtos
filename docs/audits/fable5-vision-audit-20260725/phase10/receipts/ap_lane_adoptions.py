"""AP-5: adopt AE's five and P's three, and MEASURE what each adoption moved.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ap_lane_adoptions.py

WHAT THIS IS
------------
`OD-AI-*` are not the whole queue: AE's five items live in
`phase7/receipts/AE_OWNER_DECISIONS.json` and Session P's three in
`phase3/PACKET_EMITTER_CARRY.md` §7. Borhen's blanket ratification covers each of their own
written recommendations. This script records every adoption with its provenance and, for the two
that are code changes, measures the verdict delta over every sleeve rather than asserting it.

THE BOUNDARY THE COMMISSION SETS, AND IT BINDS TWO OF THE EIGHT
---------------------------------------------------------------
*"Where adopting a recommendation would change armed-money behaviour TODAY (not default-off
machinery), stop and put it on the handoff list instead."* The learning lane is default-off and
recommendation-only, so AE's items are all inside the boundary. **Two of P's three are not**:
OD-P1 (emit-on-change) and OD-P3 (`modelled_cost_r`) touch `book_owner.py`, which the ARMED FTMO
book runs. They go on the handoff list with their price, not into a commit.

Offline and pure. Reads the two decision artifacts and the actuator; writes one JSON.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.learning_actuator import (  # noqa: E402
    MATERIALITY_BAND,
    MIN_N,
    SleeveEvidence,
    recommend,
)

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AE = AUD / "phase7/receipts/AE_OWNER_DECISIONS.json"
OUT = HERE / "AP_LANE_ADOPTIONS_V1.json"

#: The CP4/CP5 legacy fixtures `test_learning_actuator.py` carries, which are the only sleeve
#: evidence reachable without the cost-true splits artifact. Named here so the delta table says
#: which basis it is measured on -- AE's own point is that the two bases disagree.
LEGACY = [
    ("idxrev", -0.024, -0.089, -0.000, 994, 2441, 1423, "breadth_falsified"),
    ("metals_core", +0.146, -0.061, +0.853, 105, 24, 49, "train_validated"),
    ("sub_mid_dn_revert", +0.228, +0.674, +1.167, 82, 70, 58, "train_validated"),
    ("metals_softband", +0.478, +1.527, +0.215, 37, 15, 39, "train_validated"),
    ("crypto", None, +1.512, +0.806, 0, 7, 60, "train_validated"),
    ("fx_jpy", -0.041, +0.003, +0.123, 4144, 1556, 744, "breadth_falsified"),
    ("fx_jpy_ny", -0.013, -0.071, +0.153, 1615, 702, 274, "forward_only"),
]


def _ev(row) -> SleeveEvidence:
    name, tr, oos, sl, ntr, noos, nsl, status = row
    return SleeveEvidence(name, train_meanR=tr, oos_meanR=oos, sealed_meanR=sl,
                          train_n=ntr, oos_n=noos, sealed_n=nsl, status=status)


def _band_would_have_gated(ev: SleeveEvidence) -> bool:
    """Would the OLD bare-sign rule have gated this sleeve where the band does not?"""
    means = [m for _n, m, _e in ev.evaluable_splits(day_blocked=False)]
    if len(means) < 2:
        return False
    return all(m <= 0.0 for m in means) and max(means) > -MATERIALITY_BAND


def _min_n_would_bite(ev: SleeveEvidence) -> list:
    admitted = {n for n, _m, _e in ev.evaluable_splits(day_blocked=False)}
    return [(s, m, eff) for s, m, _nt, _nd, eff, _u in ev.split_records()
            if m is not None and s not in admitted and m <= 0.0]


def main() -> dict:
    ae = json.loads(AE.read_text())
    cur = ae["decision_6_false_alarm_budgets_and_raise_caps"]["current"]

    rows = []
    for r in LEGACY:
        ev = _ev(r)
        v = recommend(ev)
        rows.append({
            "sleeve": ev.sleeve,
            "verdict_now": v.verdict, "conf_mult_now": v.conf_mult, "gate": v.gate,
            "symmetric_band_changed_this_row": _band_would_have_gated(ev),
            "min_n_disagreement_splits": [
                {"split": s, "meanR": m, "n_eff": eff} for s, m, eff in _min_n_would_bite(ev)],
            "min_n_rule_bit": "MIN_N DISAGREEMENT RULE" in v.reason,
            "reason": v.reason[:600],
        })

    doc = {
        "schema": "gtos.owner_decision_adoptions.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                         "ap_lane_adoptions.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": "AP (wave 10), blocks B1350-B1399",
        "authorized_by": ("borhen (2026-07-30) — blanket ratification of each queue item's own "
                          "written recommendation"),
        "boundary": ("the learning lane is default-off and recommendation-only, so nothing here "
                     "changes armed-money behaviour today. The two items that WOULD are on the "
                     "handoff list rather than in a commit."),

        "AE_1_family_scope_for_the_false_alarm_budget": {
            "options": ["armed", "book", "account", "cell"],
            "adopted": "armed",
            "basis": "the shipped value. AE §3.1 lists the four and prices them; it ships `armed` "
                     "and does not recommend a change, so the ratified recommendation is the "
                     "status quo.",
            "action": "CONFIRMED, no code change",
            "the_honest_calibration_AE_insisted_on": (
                "'this brake is weak and the correction made it weaker.' At `armed` scope a "
                "genuinely dead metals_core has a 4.6 % chance of being gated within its first "
                "60 live fills and energy_agri 14.5 %. That is not a reason to leave the budget "
                "mislabelled — it is the reason the label had to be fixed before the number is "
                "set. The number remains open for the owner."),
            "measured_cost_table": ae["decision_6_false_alarm_budgets_and_raise_caps"][
                "family_scope_cost_on_the_armed_four_FTMO"],
        },
        "AE_2_the_two_false_alarm_budgets": {
            "familywise_down": cur["familywise_down"],
            "familywise_kill": cur["familywise_kill"],
            "over": "60 live fills",
            "adopted": "unchanged (0.20 down / 0.02 gate)",
            "basis": "R published these and AE re-scoped them correctly without changing them. No "
                     "recommendation to move them exists, so the ratified recommendation is the "
                     "shipped pair.",
            "action": "CONFIRMED, no code change",
            "still_the_owner's": "the two numbers themselves. AE: 'Regenerate with one command.'",
        },
        "AE_3_LIVE_UP_STEP_and_the_dial_cap": {
            "LIVE_UP_STEP": cur["LIVE_UP_STEP"],
            "cycles_from_1.00_to_MAX_UP": 5,
            "owner_dial_cap_default": cur["owner_dial_cap_default"],
            "MAX_UP": cur["MAX_UP"],
            "adopted": "unchanged (0.05, i.e. five owner-applied re-rate cycles to reach MAX_UP)",
            "basis": "shipped; the ladder (0.05 -> 5 cycles, 0.10 -> 3, 0.25 -> 1) is published "
                     "and AE recommends none of the alternatives.",
            "action": "CONFIRMED, no code change",
            "what_a_cycle_IS": "one owner-applied re-rating on a fresh reading of the record, not "
                               "one tick. The lane is recommendation-only, so every step is a "
                               "human decision.",
        },
        "AE_4_the_MIN_N_rule": {
            "adopted": True,
            "recommendation_verbatim": ("'if a split was dropped for n_eff < MIN_N and its mean "
                                        "disagrees in sign with the admitted splits, cap the "
                                        "recommendation at KEEP. One-sided: it can only remove a "
                                        "size-up.' AE §3.2 adds: 'it is free today and it "
                                        "forecloses the recurrence. That is the whole argument.'"),
            "action": "IMPLEMENTED in the lane",
            "site": "src/components/ultimate_book/learning_actuator._apply_min_n_disagreement",
            "was": ("a receipt-side probe at phase7/receipts/ae_owner_evidence."
                    "min_n_disagreement_rule — it could measure the rule but never bind it"),
            "one_sided_by_construction": ("it can only remove a size-up; it cannot gate, "
                                          "down-weight or rescue anything, so the worst it can do "
                                          "is leave a sleeve at the weight it already carries"),
            "AE_measured_cost": {"cost_true_29_sleeves": "moves NOTHING — all four current "
                                                          "size-ups have no disagreeing dropped "
                                                          "split",
                                 "legacy_CP4_CP5": "moves exactly metals_core, x1.146 -> KEEP "
                                                   "x1.00, the case R §4 item 15 named"},
            "AP_measured_on_the_legacy_fixtures": [
                {"sleeve": r["sleeve"], "bit": r["min_n_rule_bit"],
                 "disagreeing_dropped_splits": r["min_n_disagreement_splits"]}
                for r in rows],
        },
        "AE_5_the_idxrev_materiality_band": {
            "adopted": True,
            "recommendation_verbatim": ("'every_neg is a bare sign test with no n band, while "
                                        "every_pos requires worst >= +0.05. Proposed repair: a "
                                        "symmetric flat band, which is a change to the standing "
                                        "rule and therefore the owner's.'"),
            "action": "IMPLEMENTED in the lane",
            "site": "src/components/ultimate_book/learning_actuator.MATERIALITY_BAND "
                    "and _backtest_verdict",
            "band": MATERIALITY_BAND,
            "the_instance": ("idxrev's cost-true splits are -0.0243 / -0.0124 / +0.0079, and a "
                             "sealed mean of +0.0079 on n=1145 — four orders of magnitude inside "
                             "the band the raise side demands — broke the every-split SIGN test "
                             "and moved the sleeve GATE -> HOLD_FLAG. On the legacy fixtures the "
                             "sealed mean is -0.000, which is the same defect from the other "
                             "side."),
            "HOW_IT_WAS_MADE_NON_PERMISSIVE": (
                "the naive mirror (`every_neg and best <= -BAND -> GATE`, else nothing) would "
                "DELETE a brake whenever a sleeve is negative-but-weakly-so, and a symmetry "
                "argument does not earn a fail-open. So the band DEGRADES the brake instead: "
                "`every_neg` with a best above -BAND becomes DOWN_WEIGHT x0.5 rather than GATE "
                "x0.0. The sleeve is still braked, proportionately, and the reason string says "
                "the band did it. A materially-negative sleeve still gates — pinned by a test on "
                "a second fixture."),
            "AP_measured_on_the_legacy_fixtures": [
                {"sleeve": r["sleeve"], "verdict_now": r["verdict_now"],
                 "conf_mult_now": r["conf_mult_now"],
                 "band_changed_this_row": r["symmetric_band_changed_this_row"]}
                for r in rows],
            "AND_IT_EXPOSED_A_PRE_EXISTING_FAIL_OPEN_WHICH_IS_ALSO_FIXED": {
                "what": ("`_apply_live`'s raise guard read `not v.gate and v.verdict != \"GATE\"`, "
                         "so it protected exactly ONE of the two brake states. A sleeve the "
                         "backtest half DOWN_WEIGHTed for a large high-n negative split could be "
                         "lifted to SIZE_UP x1.05 by a flattering live run."),
                "pre_existing": True,
                "measured_at_the_parent_commit": ("5065ed24c, same probe (train +0.30 / oos -0.20 "
                                                  "/ sealed +0.30 at n=200 each; live +1.5 on 200 "
                                                  "fills over 200 days) returns "
                                                  "`backtest=DOWN_WEIGHT final=SIZE_UP x1.05`"),
                "why_it_matters": ("it is the exact failure `_apply_live`'s own docstring names: "
                                   "'a false raise adds size at the moment a sleeve's recent "
                                   "record is flattering it, on a prop account whose drawdown "
                                   "limit is absorbing, and no later re-rate reverses the loss it "
                                   "funds.'"),
                "fix": ("the guard is now the property — live may not raise a sleeve the BACKTEST "
                        "half is braking, whichever brake it is"),
                "test": ("tests/ultimate_book/test_learning_actuator_live.py::"
                         "test_live_cannot_lift_a_backtest_down_weight_and_that_was_a_PRE_EXISTING_hole"),
            },
        },

        "P_1_emit_on_change_for_position_managed": {
            "decision": "OD-P1",
            "recommendation_verbatim": "yes, with a 15-minute heartbeat",
            "adopted": "RECOMMENDATION ACCEPTED, IMPLEMENTATION HANDED OFF",
            "why_not_implemented_here": ("it changes `book_owner.py`'s emit path, which the ARMED "
                                         "FTMO book runs today. The commission's boundary is "
                                         "explicit: an adoption that changes armed-money "
                                         "behaviour goes on the handoff list."),
            "price": {"stream_reduction": "76.05 % (75,372 of 99,112 packets, ~630 MB per 37 days)",
                      "not_lossless": "collapses 848 state oscillations, which are themselves "
                                      "signal",
                      "needs": "a forced 15-minute heartbeat matched to the measured M15 idle "
                               "pattern, so 'unchanged' stays distinguishable from 'dead'",
                      "IRREVERSIBLE": "for the window in which it runs — packets not emitted are "
                                      "not recoverable"},
            "sequencing": "P says OD-P3 goes BEFORE this one.",
        },
        "P_2_repair_the_join_key_on_multi_member_units": {
            "decision": "OD-P2",
            "recommendation_verbatim": "yes, but as its own scoped change with its own A/B",
            "adopted": "RECOMMENDATION ACCEPTED, IMPLEMENTATION HANDED OFF",
            "why_not_implemented_here": ("P's own recommendation is that it must be its own scoped "
                                         "change with its own A/B, and it touches "
                                         "`book_owner.py:1324` on the armed path. Folding it into "
                                         "a decision-implementation session is exactly what the "
                                         "recommendation forbids."),
            "the_booby_trap_to_carry": ("the naive version starts mis-attributing multi-sleeve "
                                        "units to the alphabetically-first sleeve (P §3). It is "
                                        "currently INERT; a careless repair arms it."),
            "not_R2_bound": True,
        },
        "P_3_wire_modelled_cost_r": {
            "decision": "OD-P3",
            "recommendation_verbatim": "yes, and it should go before OD-P1",
            "adopted": "RECOMMENDATION ACCEPTED, IMPLEMENTATION HANDED OFF",
            "why_not_implemented_here": ("it touches `_runtime_learning_trade_context`'s allowlist "
                                         "in `book_owner.py` — small, but on the armed path."),
            "what_it_buys": "it is what makes modelled-vs-realized computable (P §6 item 1).",
            "not_R2_bound": ("confirmed by P: `broker_net_cost_engine.py` was flagged only as the "
                             "SOURCE of the value and does not need editing."),
        },

        "handoff": [
            "OD-P3 wire `modelled_cost_r` — smallest, and P says it goes first",
            "OD-P1 emit-on-change with a 15-minute heartbeat — irreversible for its window",
            "OD-P2 the join key, as its own scoped change with its own A/B",
            "AE's two budget NUMBERS and the family scope remain the owner's; the labels are now "
            "correct so the numbers can be set on evidence",
        ],
        "legacy_basis_rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    for r in rows:
        print(f"  {r['sleeve']:20s} {r['verdict_now']:20s} x{r['conf_mult_now']:<6} "
              f"band_moved={r['symmetric_band_changed_this_row']!s:5s} "
              f"min_n_bit={r['min_n_rule_bit']}")
    return doc


if __name__ == "__main__":
    main()
