"""Inbox / shim gates: occupancy is SCRIPT; HARD_OFF sleeves are not approvable.

Fail-open PASS when ``verdict.json`` is missing stays (judgment_flow no-row is
PASS). These gates only rewrite rows that already exist. They never invent a
whole-book HOLD sidecar.

UK100 179172159 ``asia_pdl_fade`` APPROVE ``isolated_reentry_free_symbol``
was the week’s one intelligence approve (−$426.69). Vacancy is not EV.
"""
from __future__ import annotations

from typing import Any, Optional

try:
    from src.components.ultimate_book.minimal_size import (
        F5_HIGH_POST_MIN,
        F5_HIGH_PRE_MIN,
        f5_hard_off_sleeve_reason,
        f5_sleeve_name,
    )
except ImportError:  # pragma: no cover — desk fallback if book laws lag
    F5_HIGH_PRE_MIN = 15.0
    F5_HIGH_POST_MIN = 60.0

    def f5_sleeve_name(family: object) -> str:
        text = str(family or "").strip()
        if "::" in text:
            return text.split("::")[-1]
        return text

    def f5_hard_off_sleeve_reason(family: object) -> str | None:
        lower = str(family or "").lower()
        if "asia_pdl_fade" in lower:
            return "hard_off_sleeve"
        if "climax" in lower and "flush" in lower:
            return "hard_off_sleeve"
        if "isolated_flush" in lower:
            return "hard_off_sleeve"
        return None


#: Occupancy keep-one is a writer script. Inbox why_codes in this set are not
#: intelligence. Charter four mechanisms: microstructure | correlation |
#: event_proximity | weekend_carry.
OCCUPANCY_WHY_EXACT = frozenset({
    "occupied_no_second_ticket",
    "occupied_pending_no_second",
    "occupied_pending_no_second_ticket",
    "no_second_ticket_occupied",
    "owner_spent_gold_no_remint_tonight",
    "grok_sit_no_named_mechanism",
    "chair_sit_no_place_from_seat",
    "no_named_mechanism_chair_sit",
    "same_symbol_stack_keep_working_ticket",
    "same_currency_dsp_stack_one_bet",
    "same_currency_fade_stack_hold",
})
OCCUPANCY_WHY_PREFIXES = (
    "occupied_",
    "no_second_ticket",
    "owner_spent_",
    "same_symbol_stack",
    "same_currency_dsp_stack",
    "same_currency_fade_stack",
    "eurusd_already_occupied",
    "no_second_",
    "grok_sit_no_named",
    "chair_sit_no_place",
    "no_named_mechanism",
)
USDJPY_WHY_PREFIXES = ("usdjpy_", "named_usdjpy")
ISOLATED_REENTRY_PREFIXES = ("isolated_reentry", "unoccupied_isolated")
HARD_OFF_WHY = frozenset({"hard_off_sleeve", "sleeve_expectancy_hard_off"})


def is_usdjpy_why(why_code: object) -> bool:
    text = str(why_code or "").strip().lower()
    return any(text.startswith(p) for p in USDJPY_WHY_PREFIXES)


def is_occupancy_why(why_code: object) -> bool:
    """SCRIPT occupancy overlay. USDJPY named HOLD is not this."""
    text = str(why_code or "").strip().lower()
    if not text or is_usdjpy_why(text) or text in HARD_OFF_WHY:
        return False
    if text in OCCUPANCY_WHY_EXACT:
        return True
    return any(text.startswith(p) for p in OCCUPANCY_WHY_PREFIXES)


def is_isolated_reentry_why(why_code: object) -> bool:
    text = str(why_code or "").strip().lower()
    return any(text.startswith(p) for p in ISOLATED_REENTRY_PREFIXES)


def high_window_blocks_new_risk(cand: dict) -> bool:
    """T-15..T+60 by candidate symbol. Composer minutes_from_now: future is positive."""
    raw = cand.get("high_impact_minutes")
    if raw is None:
        raw = cand.get("minutes_to_nearest_high_impact_signed")
    try:
        minutes = float(raw)
    except (TypeError, ValueError):
        return False
    # future +PRE, past -POST
    return -float(F5_HIGH_POST_MIN) <= minutes <= float(F5_HIGH_PRE_MIN)


def gate_candidate_verdict(row: dict, cand: dict) -> tuple[dict, Optional[str]]:
    """Rewrite one inbox/judge row. Returns (row, demotion_tag or None).

    HARD_OFF (asia_pdl_fade, climax/flush): cannot APPROVE or abstain-pass.
    Isolated re-entry on those names is still off. Occupancy HOLDs demote to
    abstain (writer keep-one already binds). USDJPY named HOLD stays.
    """
    out = dict(row)
    sleeve = str(cand.get("sleeve") or "") or f5_sleeve_name(
        cand.get("candidate_id") or out.get("candidate_id")
    )
    family = sleeve or cand.get("candidate_id") or out.get("candidate_id")
    hard = f5_hard_off_sleeve_reason(family) or f5_hard_off_sleeve_reason(sleeve)
    verdict = str(out.get("verdict") or "").strip().lower()
    why = str(out.get("why_code") or "").strip().lower()
    status = str(cand.get("status") or "intent").strip().lower()

    if hard:
        if verdict != "hold" or is_occupancy_why(why) or is_isolated_reentry_why(why):
            out["verdict"] = "hold"
            out["mechanism"] = str(out.get("mechanism") or "").strip() or "microstructure"
            out["why_code"] = "hard_off_sleeve"
            return out, "hard_off_sleeve_not_approvable"
        out["why_code"] = "hard_off_sleeve"
        if not str(out.get("mechanism") or "").strip():
            out["mechanism"] = "microstructure"
        return out, None

    if is_usdjpy_why(why):
        if verdict != "hold":
            out["verdict"] = "hold"
            out["mechanism"] = str(out.get("mechanism") or "").strip() or "microstructure"
            return out, "usdjpy_named_hold_kept"
        return out, None

    if verdict == "hold" and is_occupancy_why(why):
        out["verdict"] = "abstain"
        out["mechanism"] = ""
        out["why_code"] = "occupancy_script_not_intelligence"
        return out, "occupancy_hold_demoted_script"

    if verdict == "approve" and is_isolated_reentry_why(why) and hard:
        out["verdict"] = "hold"
        out["mechanism"] = "microstructure"
        out["why_code"] = "hard_off_sleeve"
        return out, "isolated_reentry_hard_off"

    if verdict == "approve" and status in ("intent", "", "standing"):
        if high_window_blocks_new_risk(cand):
            out["verdict"] = "hold"
            out["mechanism"] = "event_proximity"
            out["why_code"] = "named_high_print_window_candidate_symbol"
            return out, "high_window_candidate_symbol"

    return out, None
