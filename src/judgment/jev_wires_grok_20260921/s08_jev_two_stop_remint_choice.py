"""DRAFT ONLY — session 08_two_stop_remint_choice OUT dir.

Not imported by live writer. No order_send. No broker place.
Integer envelope stays fail-closed if Jev dark.

Intended land (Chair later):
  src/judgment/jev_two_stop_remint_choice.py
  called from book_owner isolated-yield AFTER 15m HOLD, BEFORE print.
"""
from __future__ import annotations

import os
from typing import Any, Iterable, Mapping, Optional

# When landed, import from two_stop_day_circuit / jev_client.
# This sketch inlines the WMB helpers so the OUT dir is self-contained.

REASON = "wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops"
TARGET_FAMILY_SUBSTR = ("two_bar", "rejection_wick", "isolated_spike")
CHOICE_ID = "remint_action"
SCORE_ID = "remint_continuation_quality"
LABELS = ("STAND", "REMINT_OK", "SWITCH_SLEEVE", "FLATTEN_SIBLING")
SHADOW_ENV = "GTOS_JEV_TWO_STOP_REMINT_SHADOW"
APPLY_ENV = "GTOS_JEV_TWO_STOP_REMINT_APPLY"
CONF_STAND = 0.45


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def sleeve_in_2stop_scope(sleeve: str) -> bool:
    sl = _norm(sleeve)
    return any(tok in sl for tok in TARGET_FAMILY_SUBSTR)


def count_orig_stops_today(
    rows: Iterable[dict],
    *,
    symbol: str,
    sleeve: str,
    session_day: str,
) -> int:
    sy, sl, day = _norm(symbol), _norm(sleeve), str(session_day or "")[:10]
    n = 0
    for r in rows or []:
        try:
            if _norm(r.get("symbol")) != sy:
                continue
            if _norm(r.get("sleeve")) != sl:
                continue
            d = str(r.get("decision_day") or r.get("session_day") or r.get("day") or "")[:10]
            if d != day:
                continue
            ex = _norm(r.get("exit_class") or r.get("close_action") or r.get("exit") or "")
            if ex == "orig_stop" or ex.endswith("orig_stop") or "orig_stop" in ex:
                n += 1
        except Exception:
            continue
    return n


def refuse_reason(
    *,
    symbol: str,
    sleeve: str,
    session_day: str,
    orig_stop_rows: Iterable[dict],
    threshold: int = 2,
) -> Optional[str]:
    """Integer WMB refuse. Fail-closed envelope. None = out of family or n < 2."""
    if not sleeve_in_2stop_scope(sleeve):
        return None
    n = count_orig_stops_today(
        orig_stop_rows, symbol=symbol, sleeve=sleeve, session_day=session_day
    )
    if n >= int(threshold):
        return (
            f"{REASON}:n={n}:threshold={threshold}:"
            f"symbol={_norm(symbol)}:sleeve={_norm(sleeve)}:day={str(session_day)[:10]}"
        )
    return None


def remint_complete_state(
    *,
    occupancy: Mapping[str, Any] | None,
    sleeve: str,
    last_exit_class: Any = None,
    parent_ticket: Any = None,
    spent_tickets: Iterable[str] | None = None,
    wmb_refuse: str | None = None,
    news_join: Any = "STATE_MISSING",
) -> dict[str, Any]:
    occ = dict(occupancy or {})
    source = occ.get("two_stop_source")
    return {
        "orig_stops_today": occ.get("same_sleeve_orig_stops_utc_day"),
        "last_exit_class": last_exit_class,
        "minutes_since_exit": occ.get("minutes_since_flat"),
        "two_stop_armed": occ.get("two_stop_exhausted"),
        "two_stop_source": source,
        "family_in_wmb_scope": sleeve_in_2stop_scope(sleeve),
        "threshold": 2,
        "closed_prune_risk": source == "closed[]" and occ.get("two_stop_updated_ict_stale") is True,
        "parent_ticket": None if parent_ticket in (None, "") else str(parent_ticket),
        "sibling_open": occ.get("symbol_open"),
        "spent_tickets": list(spent_tickets or []),
        "wmb_refuse_reason": wmb_refuse,
        "isolated_reentry_legal": occ.get("isolated_reentry_legal"),
        "news_join": news_join if news_join is not None else "STATE_MISSING",
    }


def _choice_from_receipt(receipt: Mapping[str, Any] | None) -> tuple[str | None, float | None, str]:
    if not isinstance(receipt, dict):
        return None, None, "jev_receipt_absent"
    if receipt.get("ok") is not True:
        return None, None, str(receipt.get("skipped") or receipt.get("error") or "jev_not_ok")
    answers = receipt.get("answers") or {}
    row = answers.get(CHOICE_ID) or {}
    choice = row.get("choice")
    try:
        conf = float(row.get("confidence")) if row.get("confidence") is not None else None
    except (TypeError, ValueError):
        conf = None
    if choice not in LABELS:
        return None, conf, "jev_choice_unknown"
    return str(choice), conf, "jev_ok"


def compose_remint_decision(
    integer_reason: str | None,
    jev_receipt: Mapping[str, Any] | None,
    *,
    apply: bool | None = None,
    shadow: bool | None = None,
    two_stop_source: str | None = None,
) -> dict[str, Any]:
    """Map integer + Choice → writer action. Never places. Never flattens.

    APPLY=0 (default): integer decides; Choice is receipt-only.
    Jev dark: integer decides.
    LABEL-only COUNT source cannot APPLY.
    """
    shadow_on = _env_on(SHADOW_ENV) if shadow is None else bool(shadow)
    apply_on = _env_on(APPLY_ENV) if apply is None else bool(apply)
    choice, conf, jev_src = _choice_from_receipt(jev_receipt)
    fail_closed = {
        "action": "STAND" if integer_reason else "PASS_INTEGER",
        "reason": integer_reason,
        "source": "integer_fail_closed",
        "choice": choice,
        "confidence": conf,
        "jev_src": jev_src,
        "shadow": shadow_on,
        "apply": False,
        "place": False,
        "flatten": False,
        "preferred_sleeve": None,
    }
    if not integer_reason:
        fail_closed["action"] = "PASS_INTEGER"
        fail_closed["source"] = "out_of_wmb_or_under_cap"
        return fail_closed
    if two_stop_source in {"closed_absent", "challenge_deals_label_not_count"}:
        fail_closed["source"] = "count_not_live_closed"
        return fail_closed
    if not apply_on:
        fail_closed["source"] = "apply_off_integer_stands"
        fail_closed["shadow"] = shadow_on
        return fail_closed
    if choice is None or (conf is not None and conf < CONF_STAND):
        fail_closed["source"] = "jev_dark_or_low_conf"
        return fail_closed
    if choice == "STAND":
        fail_closed["source"] = "jev_choice_stand"
        fail_closed["apply"] = True
        return fail_closed
    if choice == "REMINT_OK":
        return {
            **fail_closed,
            "action": "REMINT_OK",
            "source": "jev_choice_apply",
            "apply": True,
            "place": False,
        }
    if choice == "SWITCH_SLEEVE":
        return {
            **fail_closed,
            "action": "SWITCH_SLEEVE",
            "source": "jev_choice_apply_label_only",
            "apply": True,
            "place": False,
        }
    # FLATTEN_SIBLING — LABEL only even if APPLY; flatten send is a later Chair bind
    return {
        **fail_closed,
        "action": "FLATTEN_SIBLING",
        "source": "jev_choice_flatten_label_only",
        "apply": True,
        "place": False,
        "flatten": False,
    }


def jev_remint_choice(state: dict[str, Any], *, evaluate_fn=None) -> dict[str, Any]:
    """POST evaluate() when shadow on. Never raises into a fire path."""
    if not _env_on(SHADOW_ENV) and not _env_on(APPLY_ENV):
        return {"ok": False, "skipped": "two_stop_remint_flags_off", "answers": {}}
    if evaluate_fn is None:
        return {"ok": False, "skipped": "evaluate_fn_not_bound_in_sketch", "answers": {}}
    try:
        return evaluate_fn(state)
    except Exception as exc:  # noqa: BLE001 — fire-path must never raise
        return {"ok": False, "error": type(exc).__name__, "answers": {}}
