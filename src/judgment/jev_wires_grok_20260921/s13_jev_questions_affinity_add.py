"""DRAFT SKETCH — add JEV_SLEEVE_SELECT Choice + sleeve_affinity_fit Score
to symbol_fanout_questions(). Not live. No place.

Merge into _pr41_land/.../jev_questions.py gold_fanout_questions() dict.
Criteria for JEV_SLEEVE_SELECT are filled at call-time from SleeveSelectMenu
(cap 255, escapes always present).
"""
from __future__ import annotations

from typing import Any, Sequence

JEV_SLEEVE_SELECT_QUESTION = {
    "type": "choice",
    "instructions": (
        "Given alive_menu[].affinity (instrument×sleeve KEEP/NARROW/KILL, phi, side) "
        "and conflict_set, pick at most one sleeve tag to STAND the rest, or KEEP_ALL "
        "when relation is KEEP_ALL_DUAL_POS, or HOLD when sides unresolved / UNPROVED / Jev dark. "
        "Escapes HOLD/ABSTAIN/ESCALATE_CHAIR/BLOCKED always legal. "
        "Do not use miss/year_le0/R/exit_class. Do not invent NEWS. "
        "Cost is measurement-only — never a kill. "
        "XAU TRUE_CONFLICT three_fresh×spring: hist prior prefer spring. "
        "GBPJPY TRUE_CONFLICT: opp-side prefer vss LONG; same SHORT prefer sub_mid. "
        "EURUSD KEEP_ALL_DUAL_POS: both. XAG/NZD: single KEEP unless UNPROVED → HOLD. "
        "Never alias Package B to live sub_mid_dn_revert. Never port AUDUSD or EURUSD tags."
    ),
    "criteria": {
        "HOLD": "Sides unresolved, UNPROVED conflict, or better sleeve unclear",
        "ABSTAIN": "Not a sleeve-select decision this bar",
        "ESCALATE_CHAIR": "Hard-off / identity / occupancy envelope needs Chair",
        "BLOCKED": "Hard-off family hit (bleed/orb_crypto/idxrev/xa_huge/mx_us30)",
        "KEEP_ALL": "EURUSD dual-pos identity; both φ>0; signs-disagree n=0",
        "PICK_SPRING": "XAU conflict: prefer spring, STAND three_fresh",
        "PICK_VSS_LONG": "GBPJPY opp-side: vss LONG vs sub_mid SHORT",
        "PICK_SUB_MID_SHORT": "GBPJPY same SHORT, or NZDUSD single KEEP",
        "STAND_THREE_FRESH": "XAU three_fresh 2026 capability haircut on conflict",
    },
}

SLEEVE_AFFINITY_FIT_QUESTION = {
    "type": "score",
    "instructions": (
        "Score 0-2 how well this candidate's alive_menu[].affinity.keep_status "
        "and phi fit the named instrument. 0 = KILL/NARROW-without-KEEP-rival or banned_for_aplus; "
        "1 = NARROW or STATE_MISSING phi; 2 = KEEP on named instrument×sleeve. "
        "Do not port KEEP across instruments. Do not use cost as a kill."
    ),
    "criteria": [
        "Wrong instrument, KILL, or banned_for_aplus",
        "NARROW / missing phi / research_only",
        "KEEP on this instrument×sleeve",
    ],
}


def fill_sleeve_select_criteria(option_ids: Sequence[str]) -> dict[str, Any]:
    """Call-time criteria from menu. Escapes first. Cap 255 is menu-side."""
    q = dict(JEV_SLEEVE_SELECT_QUESTION)
    crit = dict(q["criteria"])
    for oid in option_ids:
        if oid not in crit:
            crit[str(oid)] = f"Select alive+affinity option {oid}"
    q["criteria"] = crit
    return q


def questions_to_merge() -> dict[str, Any]:
    return {
        "JEV_SLEEVE_SELECT": JEV_SLEEVE_SELECT_QUESTION,
        "sleeve_affinity_fit": SLEEVE_AFFINITY_FIT_QUESTION,
    }
