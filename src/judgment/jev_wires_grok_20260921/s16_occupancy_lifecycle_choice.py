"""DRAFT ONLY — not imported by live writer. Session 16 occupancy Choice.

Choice HOLD | REMINT | FLATTEN_ADD over COMPLETE_STATE occupancy.
Fail-closed HOLD. APPLY=0. Never router.place / order_send.

Chair copies into src/judgment/occupancy_lifecycle_choice.py after hist-prove.
"""
from __future__ import annotations

from typing import Any, Mapping

LEGAL = ("HOLD", "REMINT", "FLATTEN_ADD")
QUESTION_ID = "occupancy_lifecycle"


def occupancy_lifecycle_questions() -> dict[str, Any]:
    return {
        QUESTION_ID: {
            "type": "choice",
            "instructions": (
                "Read occupancy.*, remint.*, phi_by_sleeve, conflict_set, and "
                "place_context.last_refusal_class. The writer already holds or just "
                "attempted this broker symbol. Pick one: HOLD keep the existing "
                "unit and skip a new send; REMINT authorize replacing/re-adopting "
                "the existing ticket (management, not a second market order); "
                "FLATTEN_ADD authorize a second unit on the same broker symbol. "
                "Missing occupancy_source or position_source_available false → HOLD. "
                "Same-cycle in-flight transient attempt → do not pick FLATTEN_ADD. "
                "Empty news_join is STATE_MISSING, not a reason to fire. "
                "Do not invent NEWS_PROTOCOL, DXY, or yields."
            ),
            "criteria": {
                "HOLD": (
                    "Keep-one / retry-first / do not send a second order this cycle"
                ),
                "REMINT": (
                    "Existing ticket is the wrong sleeve or dead/unadopted; "
                    "authorize repair/replace, not a stacked send"
                ),
                "FLATTEN_ADD": (
                    "Second sleeve or timeframe on the occupied symbol is the "
                    "better book action after named occupancy fields"
                ),
            },
        }
    }


def assemble_occupancy_complete_state(
    *,
    symbol: str,
    broker_symbol: str | None,
    sleeve: str,
    decision_bar_iso: str | None,
    session_day: str | None,
    session_bucket: str | None = None,
    reason: str,
    occupancy: Mapping[str, Any] | None = None,
    remint: Mapping[str, Any] | None = None,
    phi_by_sleeve: Mapping[str, float] | None = None,
    conflict_set: list | None = None,
    place_context: Mapping[str, Any] | None = None,
    account: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    news_join: Any = None,
    affinity: str | None = None,
    in_flight_transient: bool = False,
    position_source_available: bool | None = None,
) -> dict[str, Any]:
    occ = dict(occupancy or {})
    news = news_join if news_join is not None else "STATE_MISSING"
    pos_avail = position_source_available
    if pos_avail is None:
        src = occ.get("occupancy_source")
        pos_avail = None if src in {None, "STATE_MISSING", "deal_tape_absent"} else True
    return {
        "schema": "gtos.complete_state.occupancy_lifecycle.v0",
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "selected_sleeve_candidate": sleeve,
        "decision_bar_iso": decision_bar_iso,
        "session_day": session_day,
        "session_bucket": session_bucket or "STATE_MISSING",
        "static_reason": reason,
        "occupancy": {
            "sleeve_holds_symbol": occ.get("sleeve_holds_symbol"),
            "sleeve_holds_symbol_broker": occ.get("sleeve_holds_symbol_broker"),
            "same_cycle_placed": occ.get("same_cycle_placed"),
            "same_cycle_transient_attempt": occ.get("same_cycle_transient_attempt")
            or in_flight_transient,
            "position_source_available": pos_avail,
            "n_open_same_broker_symbol": occ.get("n_open_same_broker_symbol")
            or occ.get("existing_position_count"),
            "existing_broker_symbols": list(occ.get("existing_broker_symbols") or []),
            "existing_comments": list(occ.get("existing_comments") or []),
            "existing_position_count": occ.get("existing_position_count"),
            "minutes_since_flat": occ.get("minutes_since_flat"),
            "isolated_reentry_legal": occ.get("isolated_reentry_legal"),
            "already_placed_today": occ.get("already_placed_today"),
            "cluster_placed_today": occ.get("cluster_placed_today"),
            "occupancy_source": occ.get("occupancy_source") or "STATE_MISSING",
        },
        "remint": dict(remint or {}),
        "phi_by_sleeve": dict(phi_by_sleeve or {}),
        "conflict_set": list(conflict_set or []),
        "place_context": dict(place_context or {}),
        "account": dict(account or {}),
        "cost": dict(cost or {}),
        "news_join": news,
        "affinity": affinity,
        "full_state_dark": pos_avail is not True,
        "in_flight_transient": bool(in_flight_transient),
        "place": False,
        "apply": False,
    }


def evaluate_occupancy_lifecycle(state: dict[str, Any]) -> dict[str, Any]:
    """POST System One. Never raises. Caller fail-closes HOLD on skipped/error."""
    from src.judgment.jev_client import evaluate
    from src.judgment.jev_questions import MODEL

    payload_state = dict(state)
    # jev_client.evaluate wraps systemone_payload(symbol_fanout_questions).
    # Site-local questions: pass state; Chair land should POST occupancy
    # questions explicitly (see PATCH_SKETCH). This helper stays fail-closed.
    return evaluate(payload_state, model=MODEL)


def compose_occupancy_choice(
    answers: Mapping[str, Any] | None,
    *,
    in_flight_transient: bool = False,
    position_source_available: bool | None = True,
) -> dict[str, Any]:
    if position_source_available is False or position_source_available is None:
        return {"choice": "HOLD", "reason": "occupancy_source_unavailable_envelope"}
    raw = (answers or {}).get(QUESTION_ID) or (answers or {}).get("choice")
    if isinstance(raw, dict):
        label = str(raw.get("value") or raw.get("choice") or "").upper()
    else:
        label = str(raw or "").upper()
    if label not in LEGAL:
        return {"choice": "HOLD", "reason": "jev_dark_or_illegal_label"}
    if in_flight_transient and label == "FLATTEN_ADD":
        return {"choice": "HOLD", "reason": "flatten_add_forbidden_while_in_flight"}
    return {"choice": label, "reason": "jev_choice"}
