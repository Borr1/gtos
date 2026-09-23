"""DRAFT SKETCH — evaluate() wrapper for sleeve-select.
Fail-closed if Jev dark. Never order_send. APPLY only when scoped env + hist rule.

Does not import live jev_client at sketch time (paths differ box vs VPS).
"""
from __future__ import annotations

from typing import Any, Mapping


def scoped_apply_allowed(symbol: str, conflict: Mapping[str, Any] | None, environ: Mapping[str, str]) -> bool:
    """Global APPLY must stay 0. Scoped bits are Chair-owned."""
    if str(environ.get("GTOS_JEV_SLEEVE_SELECT_APPLY", "0")).strip() in {"1", "true", "yes", "on"}:
        # still: this sketch REFUSES to honor a global flip from a session draft
        return False
    if not conflict or not conflict.get("place_when_apply"):
        return False
    sym = str(symbol).upper()
    key = str(conflict.get("scoped_apply_key") or "")
    def _on(name: str) -> bool:
        return str(environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}
    if "XAU" in key and sym in {"XAUUSD", "XAU"}:
        return _on("GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT")
    if "GBPJPY" in key and sym == "GBPJPY":
        return _on("GTOS_JEV_SLEEVE_SELECT_APPLY_GBPJPY_CONFLICT")
    if "EURUSD" in key and sym == "EURUSD":
        return _on("GTOS_JEV_SLEEVE_SELECT_APPLY_EURUSD_KEEP_ALL")
    return False


def evaluate_sleeve_select_shadow(
    state: dict[str, Any],
    *,
    evaluate_fn,
    conflict: Mapping[str, Any] | None,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    """POST evaluate. On skip/error: fail_closed, apply=false, place=false."""
    receipt = {
        "ok": False,
        "apply": False,
        "place": False,
        "fail_closed": True,
        "never_broker_place": True,
        "answers": {},
        "reason": None,
    }
    try:
        jev = evaluate_fn(state)
    except Exception as exc:  # noqa: BLE001 — fire path must not raise
        receipt["reason"] = f"evaluate_raised:{type(exc).__name__}"
        return receipt
    if not jev.get("ok"):
        receipt["reason"] = jev.get("skipped") or jev.get("error") or "jev_dark"
        receipt["jev"] = {k: jev.get(k) for k in ("ok", "skipped", "error", "http_status")}
        return receipt
    receipt["ok"] = True
    receipt["fail_closed"] = False
    receipt["answers"] = jev.get("answers") or {}
    receipt["jev"] = {k: jev.get(k) for k in ("ok", "model", "usage", "calls_used")}
    # SHADOW default. APPLY is Chair env + hist conflict only. Session never places.
    if scoped_apply_allowed(str(state.get("symbol") or ""), conflict, environ):
        receipt["apply"] = True
        receipt["place"] = False  # writer prints; Choice may later PLACE after hist — not here
        receipt["disposition"] = "admit_filter"
    else:
        receipt["disposition"] = "advisory_only"
    receipt["reason"] = "shadow_or_scoped_logged"
    return receipt
