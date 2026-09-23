"""DRAFT ONLY — not on the live fire path. Occupancy/place Choice wrapper.

Fail-closed: any missing key / dark Jev / APPLY=0 / authority false → static skip.
Never calls router.place / order_send / flatten.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Intended imports after land (do not execute from this OUT dir):
# from .jev_client import evaluate
# from .jev_questions import symbol_fanout_questions
# from .place_choice questions merged into symbol_fanout

_TRUTHY = frozenset({"1", "true", "yes", "on"})
SCOPED_DEFAULT = ("XAUUSD", "GBPJPY")
CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def shadow_enabled() -> bool:
    return _env_on("GTOS_JEV_PLACE_CHOICE_SHADOW") or _env_on("GTOS_JEV_OCCUPANCY_CHOICE_SHADOW")


def apply_enabled() -> bool:
    # Place APPLY is a dedicated flag. Size APPLY and fluid LABEL APPLY are not place authority.
    return _env_on("GTOS_JEV_PLACE_CHOICE_APPLY") or _env_on("GTOS_JEV_OCCUPANCY_CHOICE_APPLY")


def cost_apply_enabled() -> bool:
    return _env_on("GTOS_JEV_COST_SCORE_APPLY")


def scoped_symbols() -> set[str]:
    raw = os.environ.get("GTOS_JEV_PLACE_CHOICE_SCOPED_SYMBOLS", "").strip()
    if not raw:
        return set(SCOPED_DEFAULT)
    return {s.strip().upper() for s in raw.split(",") if s.strip()}


@dataclass
class PlaceDecision:
    place_action: str | None
    occupancy_action: str | None
    freshness_action: str | None
    cost_action: str | None  # COST_DOMINATED / TRIM / COST_OK
    apply: bool
    fail_closed: bool
    reason: str
    jev_ok: bool
    static_reason: str | None


ENVELOPE_STATIC = frozenset(
    {
        "already_placed_this_bar",
        "same_broker_symbol_already_placed_this_cycle",
        "same_broker_symbol_transient_attempt_this_cycle",
        "same_broker_symbol_position_source_unavailable_for_lifecycle_guard",
        "live_broker_authority_false_observe_only",
        "stale_tick_market_closed",
        "no_tick_transient",
        "breach_flatten_block",
        "kill_switch_or_halt_forced_observe_only",
        "account_state_unavailable",
        "profile_missing_instrument_config",
        "weekend_entry_embargo",
        "weekend_policy_clock_unavailable",
    }
)


def interpret_place_receipt(
    receipt: dict[str, Any],
    *,
    static_reason: str | None,
    authority: bool,
    symbol: str,
    ns: str | None,
    login: Any,
    occupancy: dict[str, Any] | None,
    apply_flag: bool,
) -> PlaceDecision:
    """Map Jev answers to a fire-path decision. Code owns legality."""
    occ = occupancy or {}
    answers = (receipt or {}).get("answers") or {}
    jev_ok = bool((receipt or {}).get("ok"))
    dark = (not jev_ok) or (receipt or {}).get("skipped") or (receipt or {}).get("error")

    if static_reason and any(
        static_reason == k or static_reason.startswith(k) for k in ENVELOPE_STATIC
    ):
        return PlaceDecision(
            None, None, None, None,
            apply=False, fail_closed=True,
            reason=f"envelope_keep:{static_reason}",
            jev_ok=jev_ok, static_reason=static_reason,
        )
    if not authority:
        return PlaceDecision(
            None, None, None, None,
            apply=False, fail_closed=True,
            reason="live_broker_authority_false",
            jev_ok=jev_ok, static_reason=static_reason,
        )
    if dark:
        return PlaceDecision(
            None, None, None, None,
            apply=False, fail_closed=True,
            reason="jev_dark_fail_closed",
            jev_ok=False, static_reason=static_reason,
        )
    if occ.get("two_stop_exhausted") is True:
        return PlaceDecision(
            "STAND", "HOLD", None, None,
            apply=False, fail_closed=True,
            reason="two_stop_count_integer",
            jev_ok=jev_ok, static_reason=static_reason,
        )

    def _choice(qid: str) -> str | None:
        block = answers.get(qid) or {}
        if isinstance(block, dict):
            return block.get("choice") or block.get("value") or block.get("answer")
        return None

    def _score_label(qid: str) -> str | None:
        block = answers.get(qid) or {}
        if not isinstance(block, dict):
            return None
        # Score may arrive as weighted levels; land code should map 0/1/2.
        raw = block.get("score")
        if raw is None:
            return block.get("choice")
        try:
            v = float(raw)
        except (TypeError, ValueError):
            return None
        if v < 0.67:
            return "COST_DOMINATED"
        if v < 1.33:
            return "TRIM"
        return "COST_OK"

    place_action = _choice("place_action")
    occupancy_action = _choice("occupancy_action")
    freshness_action = _choice("freshness_action")
    cost_action = _score_label("cost_action")

    scoped = str(symbol or "").upper() in scoped_symbols()
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    try:
        login_ok = int(login) == CHALLENGE_LOGIN if login not in (None, "") else False
    except (TypeError, ValueError):
        login_ok = False
    apply = bool(apply_flag and scoped and (ns_ok or login_ok) and not dark)

    # v0: never honor FLATTEN_ADD / REMINT send even if APPLY.
    if occupancy_action in {"FLATTEN_ADD", "REMINT"}:
        occupancy_action = "HOLD"
        apply = False
        reason = "occupancy_label_hold_until_flatten_remint_prove"
    elif occupancy_action == "PLACE_ISOLATED" and not occ.get("isolated_reentry_legal"):
        occupancy_action = "HOLD"
        apply = False
        reason = "place_isolated_illegal_not_flat"
    else:
        reason = "shadow" if not apply else "apply_candidate"

    if not apply:
        return PlaceDecision(
            place_action, occupancy_action, freshness_action, cost_action,
            apply=False, fail_closed=True,
            reason=reason, jev_ok=jev_ok, static_reason=static_reason,
        )
    return PlaceDecision(
        place_action, occupancy_action, freshness_action, cost_action,
        apply=True, fail_closed=False,
        reason=reason, jev_ok=jev_ok, static_reason=static_reason,
    )


def assemble_place_occupancy_state(
    *,
    symbol: str,
    broker_symbol: str,
    sleeve: str,
    side: str,
    session_day: str,
    decision_bar_iso: str | None,
    occupancy: dict[str, Any] | None,
    cost: dict[str, Any] | None,
    freshness: dict[str, Any] | None,
    place_context: dict[str, Any] | None,
    account: dict[str, Any] | None,
    news_join: Any = "STATE_MISSING",
    affinity: dict[str, Any] | None = None,
    module_atr: dict[str, Any] | None = None,
) -> dict[str, Any]:
    occ = dict(occupancy or {})
    n_incomplete = sum(1 for v in occ.values() if v is None)
    news = news_join if news_join not in (None, "") else "STATE_MISSING"
    return {
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "sleeve": sleeve,
        "side": side,
        "session_day": session_day,
        "decision_bar_iso": decision_bar_iso,
        "occupancy": occ,
        "cost": dict(cost or {}),
        "freshness": dict(freshness or {}),
        "place_context": dict(place_context or {}),
        "account": dict(account or {}),
        "news_join": news,
        "affinity": dict(affinity or {"instrument": symbol, "sleeve": sleeve, "held": True}),
        "module_atr": dict(module_atr or {"lens": "Module_ATR", "R_available": False, "never_merge_dig3r_or_edge_atr": True}),
        "hard_off_hit": None,
        "full_state_dark": n_incomplete > 0 or news == "STATE_MISSING",
        "n_incomplete": n_incomplete,
    }
