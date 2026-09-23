"""DRAFT ONLY — hook sketch for emit_sleeve_select_shadow_payload.

Does not call broker. Global APPLY stays 0.
Fail-closed if jev_client.evaluate skips.
"""
from __future__ import annotations

from typing import Any, Mapping


def observe_evaluate_and_maybe_filter(
    payload: dict[str, Any],
    complete_state: Mapping[str, Any],
    *,
    evaluate_fn,
    global_apply: bool = False,
) -> dict[str, Any]:
    """POST evaluate; mutate admit filter only when scoped APPLY on and Jev ok.

    evaluate_fn is jev_client.evaluate. Never raises into fire path
    (jev_client already swallows). This wrapper still guards.
    """
    if global_apply:
        payload.setdefault("notes", [])
        if isinstance(payload.get("notes"), list):
            payload["notes"].append("WARN_global_APPLY_true_ignored_this_pass")
        global_apply = False

    receipt: dict[str, Any]
    try:
        receipt = dict(evaluate_fn(dict(complete_state)) or {})
    except Exception as exc:  # noqa: BLE001 — fire path
        receipt = {"ok": False, "skipped": f"evaluate_raised:{type(exc).__name__}", "answers": {}}

    payload["jev_evaluate"] = {
        "ok": bool(receipt.get("ok")),
        "skipped": receipt.get("skipped"),
        "error": receipt.get("error"),
        "answers": receipt.get("answers") or {},
        "calls_used": receipt.get("calls_used"),
        "place": False,
    }

    scoped = payload.get("scoped_apply") or {}
    jev_dark = not bool(receipt.get("ok")) or bool(receipt.get("skipped"))
    answers = receipt.get("answers") or {}
    noul_ok = True
    ss = answers.get("state_sufficient")
    if isinstance(ss, dict):
        noul_ok = bool(ss.get("value", ss.get("answer", True)))
    elif ss is False:
        noul_ok = False

    if jev_dark or not noul_ok:
        payload["apply"] = False
        payload["place"] = False
        payload["never_place"] = True
        payload["disposition"] = "advisory_only"
        payload["fail_closed"] = True
        payload["jev_dark"] = jev_dark
        payload["state_sufficient"] = noul_ok
        return payload

    choice = answers.get("conflict_pick") or answers.get("dual_pos_keep")
    if isinstance(choice, dict):
        choice = choice.get("value") or choice.get("answer")
    payload["jev_choice"] = choice

    # Scoped APPLY may filter; global stays 0. Writer still prints. This session never places.
    if scoped.get("any") and choice in {"KEEP_A", "KEEP_B", "KEEP_BOTH", "STAND"}:
        payload["apply"] = True
        payload["disposition"] = "admit_filter"
        payload["place"] = False
        payload["never_place"] = True
        payload["owner_override_20260921_place_when_proved"] = True
        # Chair later: if place_when_apply and writer authority, set place true.
    else:
        payload["apply"] = False
        payload["disposition"] = "advisory_only"
        payload["place"] = False
        payload["never_place"] = True
    return payload
