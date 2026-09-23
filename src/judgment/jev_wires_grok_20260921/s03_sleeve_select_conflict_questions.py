"""DRAFT ONLY — not imported by live writer.

JEV_SLEEVE_SELECT conflict question bank (typed Choice / Score / Noul).
Host merge target: src/judgment/jev_questions.py

place=false · global APPLY=0 · never invent NEWS_PROTOCOL
"""
from __future__ import annotations

from typing import Any


QUESTION_ID = "JEV_SLEEVE_SELECT"


def sleeve_select_conflict_questions() -> dict[str, Any]:
    """One POST. Independent questions. Meaning lives in instructions, not IDs."""
    return {
        "state_sufficient": {
            "type": "noul",
            "instructions": (
                "Do the named COMPLETE_STATE blocks (symbol, alive_sleeves, conflict_set, "
                "sleeve_sides, phi_by_sleeve, regime_tag, conf_band, session_fit, occupancy, "
                "account) contain enough to judge this sleeve conflict as-of decision_bar_iso? "
                "Yes = named tape/identity/conflict present. No = a required block is missing "
                "or unknown. Empty news_join / STATE_MISSING is not a No. Do not invent news."
            ),
            "criteria": {
                "true": "Named blocks are present enough to judge the conflict",
                "false": "A required named block is missing or unknown",
            },
        },
        "conflict_pick": {
            "type": "choice",
            "instructions": (
                "This is a TRUE_CONFLICT on one symbol this bar. "
                "`conflict_set[0]` is sleeve A (tag, side, phi, haircut, session_fit). "
                "`conflict_set[1]` is sleeve B. "
                "Pick KEEP_A to leave A eligible and stand B; KEEP_B to leave B eligible "
                "and stand A; STAND to fire neither. "
                "Do not read miss, year_le0, R, or exit_class if those keys exist. "
                "Cost fields are measurement-only and never a kill. "
                "Hard-off families are not fire options. "
                "If sleeve_sides are missing, prefer STAND. "
                "If A is three_fresh with phi_haircut and B is spring on XAUUSD, "
                "hist prior prefers KEEP_B; still judge from named state. "
                "If A is vss LONG and B is sub_mid SHORT on GBPJPY, hist prior prefers KEEP_A. "
                "If both SHORT on GBPJPY, hist prior prefers KEEP_B. "
                "Priors are context, not an oracle."
            ),
            "criteria": {
                "KEEP_A": "Sleeve A remains eligible this bar; stand sleeve B",
                "KEEP_B": "Sleeve B remains eligible this bar; stand sleeve A",
                "STAND": "Neither sleeve fires this bar",
            },
        },
        "dual_pos_keep": {
            "type": "choice",
            "instructions": (
                "EURUSD complementary pair only (asian_fade × Package B SHORT). "
                "Both have positive standing φ and signs_disagree is false. "
                "This is NOT a pick-one conflict. "
                "KEEP_BOTH leaves both eligible. STAND fires neither. "
                "ABSTAIN if state is too thin. Never TRIM both as a Choice. "
                "Code may trim an incomplete sleeve only after KEEP_BOTH."
            ),
            "criteria": {
                "KEEP_BOTH": "Both complementary sleeves remain eligible (place-both identity)",
                "STAND": "Fire neither this bar",
                "ABSTAIN": "Not enough named state to keep both or stand",
            },
        },
        "sleeve_fit": {
            "type": "score",
            "instructions": (
                "Score the KEEP candidate's session/geometry fit using only named fields. "
                "0 = wrong hour, haircut-stand, or toxic family leaking into menu. "
                "1 = ordinary KEEP. 2 = φ-top in a clean session. "
                "This Score does not refuse and does not kill on cost."
            ),
            "criteria": [
                "Wrong session, haircut-stand, or toxic leak",
                "Ordinary KEEP",
                "φ-top in the sleeve's clean hour",
            ],
        },
    }


def sleeve_select_systemone_payload(state: dict[str, Any], *, model: str = "jev-1.13.0") -> dict[str, Any]:
    return {"state": state, "model": model, "questions": sleeve_select_conflict_questions()}
