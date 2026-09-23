"""DRAFT ONLY — not landed. CONF_GATE System One questions.

Choice YES|NO|UNSURE over COMPLETE_STATE. Vendor 0.50/0.85 is not truth.
Never place / remint / flatten / order_send. Never invent NEWS_PROTOCOL or ATR.
"""

from __future__ import annotations

from typing import Any

CONF_ADMIT_CRITERIA = {
    "YES": (
        "Named COMPLETE_STATE still supports LABEL-admitting this sleeve-fire. "
        "Not 'will it profit'. Not permission to place."
    ),
    "NO": (
        "Named tape / regime / cost / occupancy argue stand_down. "
        "House hard-off and 2-stop COUNT remain code."
    ),
    "UNSURE": (
        "State thin, mixed, or concentration too spread. REVIEW / SHADOW. Do not invent."
    ),
}

CONF_BAND_CRITERIA = {
    "STRICT": "fs_half / false_structure residual — second confirm; not a new hard-off.",
    "SESSION": "session_cut residual — low-conf admits in named London/NY/Asia; G6 already cut size.",
    "EVENT": "stamped event proximity only. Empty spine is not 'no HIGH'. Never invent NEWS.",
    "REVIEW": "KEEP-surface residual. Cap / review. NOT hard-off.",
    "KEEP": "STATE keep_signature present and no STRICT/SESSION/EVENT/REVIEW cut.",
    "ALLOW": "No S15 cut and named state is clean enough to LABEL-admit.",
    "PENDING": "Jev dark or buckets/state missing. Honest.",
}


def conf_gate_questions() -> dict[str, Any]:
    return {
        "conf_admit": {
            "type": "choice",
            "instructions": (
                "Given COMPLETE_STATE (regime_tag, buckets, session, occupancy, "
                "keep_signature, s15 subclass if named, news_join or STATE_MISSING), "
                "should this fire be LABEL-admitted? YES / NO / UNSURE. "
                "Vendor 0.50/0.85 is not Challenge truth. Hard-off families are already code. "
                "Empty news spine is not 'no HIGH'. Do not emit place/remint/flatten/order_send."
            ),
            "criteria": dict(CONF_ADMIT_CRITERIA),
        },
        "conf_band_label": {
            "type": "choice",
            "instructions": (
                "Pick the CONF_GATE band label from named S15 subclass, keep_signature, "
                "session, and stamped news only. PENDING if unknown. Never invent NEWS."
            ),
            "criteria": dict(CONF_BAND_CRITERIA),
        },
    }


def regime_and_conf_pack(sleeve: str | None = None) -> dict[str, Any]:
    """One System One request: S14 regime pack + conf_gate Choice. Independent questions."""
    # Land path: merge with regime_system_one.build_question_pack(sleeve)
    pack: dict[str, Any] = {}
    pack.update(conf_gate_questions())
    return pack
