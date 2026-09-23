"""DRAFT ONLY — not imported by live writer. Session 16 pretrade Score COST.

Score 0 STAND | 1 TRIM | 2 COST_OK over COMPLETE_STATE cost.
Fail-closed STAND. APPLY=0. Never size-up. Never router.place / order_send.

Chair copies into src/judgment/pretrade_cost_score.py after hist-prove.
"""
from __future__ import annotations

from typing import Any, Mapping

QUESTION_ID = "pretrade_spread_cost"
LABELS = {0: "STAND", 1: "TRIM", 2: "COST_OK"}


def pretrade_cost_questions() -> dict[str, Any]:
    return {
        QUESTION_ID: {
            "type": "score",
            "instructions": (
                "Score whether this leg should STAND (keep the static spread refuse), "
                "TRIM (allow after a size haircut because cost eats R but edge remains), "
                "or COST_OK (allow at the already-admitted size). Read cost.spread_r, "
                "cost.max_spread_r, cost.stop_dist, cost.commission_r, phi, "
                "session_bucket, occupancy, and affinity. Static cell max is context, "
                "not the answer. Do not size up. Do not invent NEWS_PROTOCOL. "
                "Empty news_join is STATE_MISSING. Do not merge Module_ATR R into this "
                "score — this is live tick spread vs stop, not a blotter lens."
            ),
            "criteria": [
                "STAND: spread structurally too wide for this stop; skip the send",
                "TRIM: edge may survive if size is cut; do not raise size",
                "COST_OK: spread is acceptable in named session/occupancy/phi context; full admitted size",
            ],
        }
    }


def assemble_cost_complete_state(
    *,
    symbol: str,
    broker_symbol: str | None,
    sleeve: str,
    decision_bar_iso: str | None,
    session_bucket: str | None,
    cost_skip: str | None,
    spread_r: float | None,
    spread_price: float | None,
    stop_dist: float | None,
    max_spread_r: float | None,
    max_spread_r_by_sleeve: float | None = None,
    commission_r: float | None = None,
    total_cost_r: float | None = None,
    occupancy: Mapping[str, Any] | None = None,
    phi: float | None = None,
    phi_by_sleeve: Mapping[str, float] | None = None,
    regime_tag: str | None = None,
    conf_band: str | None = None,
    session_fit: str | None = None,
    account: Mapping[str, Any] | None = None,
    news_join: Any = None,
    affinity: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": "gtos.complete_state.pretrade_cost.v0",
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "selected_sleeve_candidate": sleeve,
        "decision_bar_iso": decision_bar_iso,
        "session_bucket": session_bucket or "STATE_MISSING",
        "regime_tag": regime_tag or "PENDING",
        "conf_band": conf_band or "PENDING",
        "session_fit": session_fit or "PENDING",
        "phi": phi,
        "phi_by_sleeve": dict(phi_by_sleeve or {}),
        "cost": {
            "spread_r": spread_r,
            "spread_price": spread_price,
            "stop_dist": stop_dist,
            "max_spread_r": max_spread_r,
            "max_spread_r_by_sleeve": max_spread_r_by_sleeve,
            "commission_r": commission_r,
            "total_cost_r": total_cost_r,
            "cost_screen_would_refuse": cost_skip is not None,
            "cost_skip_reason": cost_skip,
            "spread_r_source": "book_owner._spread_cost_screen_live_tick"
            if spread_r is not None
            else "STATE_MISSING",
        },
        "occupancy": dict(occupancy or {}),
        "account": dict(account or {}),
        "news_join": news_join if news_join is not None else "STATE_MISSING",
        "affinity": affinity,
        "place": False,
        "apply": False,
    }


def evaluate_pretrade_cost(state: dict[str, Any]) -> dict[str, Any]:
    from src.judgment.jev_client import evaluate
    from src.judgment.jev_questions import MODEL

    return evaluate(state, model=MODEL)


def compose_cost_score(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map Score 0-2 → STAND|TRIM|COST_OK. Never size_mult > 1. Dark → STAND."""
    raw = (answers or {}).get(QUESTION_ID) or (answers or {}).get("score")
    value = None
    if isinstance(raw, dict):
        value = raw.get("value")
        if value is None:
            value = raw.get("score")
    elif isinstance(raw, (int, float)):
        value = raw
    try:
        if value is None:
            raise ValueError("missing")
        level = int(round(float(value)))
    except (TypeError, ValueError):
        return {"label": "STAND", "size_mult": 0.0, "reason": "jev_dark_or_unscored"}
    if level <= 0:
        return {"label": "STAND", "size_mult": 0.0, "reason": "score_stand"}
    if level == 1:
        # TRIM: midpoint haircut. Chair hist may replace 0.70 with a calibrated table.
        # Never > 1.0. F5-JEV-004 live tilt floor is 0.70 after cost already cleared —
        # this TRIM is the refuse-path cousin, default-off.
        return {"label": "TRIM", "size_mult": 0.70, "reason": "score_trim"}
    return {"label": "COST_OK", "size_mult": 1.0, "reason": "score_cost_ok"}
