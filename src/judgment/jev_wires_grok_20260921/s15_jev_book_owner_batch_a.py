"""DRAFT ONLY — session 15_residual_static_book_owner_batch_a.

COMPLETE_STATE builder + Jev evaluate/compose for:
  weekend_entry_embargo  -> Choice KEEP_EMBARGO|SCOPED_ENTRY_OK|DELAY
  no_tick_transient      -> Noul tape_fresh -> RETRY|CONSUME_BAR

Envelope reasons are NOT composed here:
  breach_flatten_block, kill_switch_or_halt_forced_observe_only,
  account_state_unavailable, profile_missing_instrument_config,
  weekend_policy_clock_unavailable.

Never broker place / order_send / remint / flatten.
Fail-closed if Jev dark: static skip / retry.
Do not invent NEWS_PROTOCOL or ATR/regime.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

PACK_ID = "gtos.judgment.book_owner_batch_a.v0"
SHADOW_ENV = "GTOS_JEV_BOOK_OWNER_BATCH_A_SHADOW"
WEEKEND_APPLY_ENV = "GTOS_JEV_WEEKEND_EMBARGO_APPLY"
NO_TICK_APPLY_ENV = "GTOS_JEV_NO_TICK_TAPE_FRESH_APPLY"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

FN_FUNDED_NO_HOLD = "redacted_account"
FTMO = "FTMO"


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def batch_a_shadow_enabled() -> bool:
    return _env_on(SHADOW_ENV) or weekend_embargo_apply_enabled() or no_tick_apply_enabled()


def weekend_embargo_apply_enabled() -> bool:
    return _env_on(WEEKEND_APPLY_ENV)


def no_tick_apply_enabled() -> bool:
    return _env_on(NO_TICK_APPLY_ENV)


def firm_allows_weekend_hold(state: Mapping[str, Any]) -> bool:
    """Integer firm rule. Not a Jev toy."""
    account = state.get("account") if isinstance(state.get("account"), Mapping) else {}
    firm = str(account.get("firm") or "").strip()
    phase = str(account.get("phase") or "").strip().lower()
    if firm == FTMO:
        return True
    if firm == FN_FUNDED_NO_HOLD and phase in {"challenge", "verification", ""}:
        return True
    return False


def in_flatten_window_same_tick(state: Mapping[str, Any]) -> bool:
    """Entry that would be flattened on the same tick is not a judgment."""
    weekend = state.get("weekend") if isinstance(state.get("weekend"), Mapping) else {}
    try:
        hours = float(weekend.get("hours_to_boundary"))
        flatten_before = float(weekend.get("flatten_before_hours") or 0.0)
    except (TypeError, ValueError):
        return False
    return hours <= flatten_before


def build_batch_a_complete_state(
    *,
    reason: str,
    symbol: str | None,
    broker_symbol: str | None,
    sleeve: str | None,
    decision_bar_iso: str | None,
    session_day: str | None = None,
    session_bucket: str | None = "PENDING",
    account: Mapping[str, Any] | None = None,
    weekend: Mapping[str, Any] | None = None,
    tick: Mapping[str, Any] | None = None,
    occupancy: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    phi: float | None = None,
    place_context: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Gap-inventory COMPLETE_STATE v0 plus weekend/tick blocks.

    regime_tag / conf_band / session_fit stay PENDING unless a caller already
    assembled them. news_join is STATE_MISSING unless provided. No ATR invent.
    """
    extra = dict(extra or {})
    news = extra.get("news_join", "STATE_MISSING")
    state: dict[str, Any] = {
        "schema": PACK_ID,
        "reason": reason,
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "session_day": session_day,
        "decision_bar_iso": decision_bar_iso,
        "session_bucket": session_bucket or "PENDING",
        "alive_sleeves": extra.get("alive_sleeves") or [],
        "alive_menu": extra.get("alive_menu") or [],
        "selected_sleeve_candidate": sleeve,
        "conflict_set": extra.get("conflict_set") or [],
        "regime_tag": extra.get("regime_tag") or "PENDING",
        "conf_band": extra.get("conf_band") or "PENDING",
        "session_fit": extra.get("session_fit") or "PENDING",
        "phi": phi,
        "phi_by_sleeve": extra.get("phi_by_sleeve") or {},
        "cost": dict(cost or {}),
        "occupancy": dict(occupancy or {}),
        "account": dict(account or {}),
        "hard_off_hit": extra.get("hard_off_hit"),
        "remint": extra.get("remint") or {},
        "news_join": news if news is not None else "STATE_MISSING",
        "full_state_dark": bool(extra.get("full_state_dark", False)),
        "n_incomplete": int(extra.get("n_incomplete") or 0),
        "place_context": dict(place_context or {"writer_ready": False, "authority": False}),
        "weekend": dict(weekend or {}),
        "tick": dict(tick or {"present": False}),
        "place": False,
        "never_broker_place": True,
        "module_atr_invented": False,
    }
    return state


def evaluate_batch_a(state: dict[str, Any]) -> dict[str, Any]:
    """POST via jev_client.evaluate. Fail-closed skip receipt. Never raises."""
    receipt: dict[str, Any] = {
        "ok": False,
        "answers": {},
        "skipped": "not_called",
        "place": False,
        "pack_id": PACK_ID,
    }
    try:
        from src.judgment.jev_client import evaluate
        from .jev_questions_batch_a import batch_a_questions
    except Exception as exc:  # noqa: BLE001 — fire path must not raise
        receipt["skipped"] = f"import_failed:{type(exc).__name__}"
        return receipt
    # jev_client.evaluate uses symbol_fanout_questions(). For this draft we
    # still call evaluate(state) so the living client is the POST path; the
    # side-pack questions are attached on the state for a later payload splice.
    state = dict(state)
    state["_batch_a_questions"] = list(batch_a_questions())
    try:
        out = evaluate(state)
    except Exception as exc:  # noqa: BLE001
        receipt["skipped"] = f"evaluate_raised:{type(exc).__name__}"
        return receipt
    if not isinstance(out, dict):
        receipt["skipped"] = "evaluate_non_dict"
        return receipt
    receipt.update(out)
    receipt["place"] = False
    receipt["pack_id"] = PACK_ID
    return receipt


def compose_weekend_embargo(
    state: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
    *,
    apply: bool,
) -> str:
    """KEEP_EMBARGO | SCOPED_ENTRY_OK | DELAY. Fail-closed KEEP_EMBARGO."""
    if in_flatten_window_same_tick(state) or not firm_allows_weekend_hold(state):
        return "KEEP_EMBARGO"
    if not apply:
        return "KEEP_EMBARGO"
    if not receipt or not receipt.get("ok"):
        return "KEEP_EMBARGO"
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), Mapping) else {}
    block = answers.get("weekend_embargo_action") if isinstance(answers, Mapping) else None
    choice = None
    if isinstance(block, Mapping):
        choice = block.get("choice") or block.get("value") or block.get("label")
    if choice == "SCOPED_ENTRY_OK":
        return "SCOPED_ENTRY_OK"
    if choice == "DELAY":
        return "DELAY"
    return "KEEP_EMBARGO"


def compose_no_tick(
    state: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
    *,
    apply: bool,
) -> str:
    """RETRY | CONSUME_BAR. Fail-closed RETRY. Never PLACE."""
    tick = state.get("tick") if isinstance(state.get("tick"), Mapping) else {}
    if tick.get("present"):
        return "RETRY"
    if not apply:
        return "RETRY"
    if not receipt or not receipt.get("ok"):
        return "RETRY"
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), Mapping) else {}
    block = answers.get("tape_fresh") if isinstance(answers, Mapping) else None
    p_yes = None
    if isinstance(block, Mapping):
        p_yes = block.get("probability")
        if p_yes is None:
            p_yes = block.get("noul")
        if p_yes is None and isinstance(block.get("value"), bool):
            p_yes = 1.0 if block["value"] else 0.0
    try:
        p = float(p_yes) if p_yes is not None else None
    except (TypeError, ValueError):
        p = None
    if p is None:
        return "RETRY"
    # Near 0.5 = unknown (TypeSafe Noul). Consume only when clearly not-fresh.
    if p < 0.35:
        return "CONSUME_BAR"
    return "RETRY"
