"""DRAFT ONLY — 14_place_fluid_hist_prove_apply.

Not imported by live writer. Never order_send. place=False in this process.

When Chair lands, copy into src/judgment/place_fluid.py after hist PASS.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

# --- env (all default-off) ---
PLACE_SHADOW_ENV = "GTOS_JEV_PLACE_FLUID_SHADOW"
PLACE_APPLY_ENV = "GTOS_JEV_PLACE_FLUID_APPLY"  # global — stay 0 this pass
PLACE_APPLY_XAU_ENV = "GTOS_JEV_PLACE_FLUID_APPLY_XAU"
PLACE_APPLY_GBPJPY_ENV = "GTOS_JEV_PLACE_FLUID_APPLY_GBPJPY"
PLACE_PROVE_DIR_ENV = "GTOS_JEV_PLACE_FLUID_PROVE_DIR"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
CHALLENGE_LOGIN = "0"
LEAVE_ORIG = frozenset({"293332188"})
CHOICE_OK = frozenset({"PLACE", "STAND", "DELAY"})


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def place_shadow_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    return _env_on(PLACE_SHADOW_ENV, environ)


def place_apply_global(*, environ: Mapping[str, str] | None = None) -> bool:
    return _env_on(PLACE_APPLY_ENV, environ)


def place_apply_scoped(symbol: str, *, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    sym = str(symbol or "").upper()
    xau = _env_on(PLACE_APPLY_XAU_ENV, environ) and sym in {"XAUUSD", "XAU"}
    gbp = _env_on(PLACE_APPLY_GBPJPY_ENV, environ) and sym == "GBPJPY"
    return {
        "symbol": sym,
        "xau": xau,
        "gbpjpy": gbp,
        "global": place_apply_global(environ=environ),
        "any": bool(xau or gbp or place_apply_global(environ=environ)),
        "owner_override_20260921_place_when_proved": True,
        "never_place_default": True,
    }


def fail_closed_if_jev_dark(jev: Mapping[str, Any] | None) -> bool:
    if not jev:
        return True
    if jev.get("ok") is not True:
        return True
    if jev.get("skipped"):
        return True
    if jev.get("error"):
        return True
    return False


def selected_place_choice(answers: Mapping[str, Any] | None) -> str:
    packed = (answers or {}).get("place_now") or {}
    raw = str(packed.get("choice") or packed.get("selected") or "STAND").strip().upper()
    return raw if raw in CHOICE_OK else "STAND"


def place_apply_authorized(
    *,
    symbol: str,
    login: str,
    ticket: Any,
    jev: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None,
    envelope_clear: bool,
    prove_receipt: Mapping[str, Any] | None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Authorize writer print. This function never sends."""
    choice = selected_place_choice(answers)
    scoped = place_apply_scoped(symbol, environ=environ)
    dark = fail_closed_if_jev_dark(jev)
    leave = str(ticket or "").strip() in LEAVE_ORIG
    login_ok = str(login or "").strip() == CHALLENGE_LOGIN
    receipt_ok = bool(prove_receipt and prove_receipt.get("proven") and prove_receipt.get("wire_class") in {"A1", "A2", "A3", "W_named"})
    apply_bit = bool(scoped.get("any"))
    authorize = (
        (not dark)
        and choice == "PLACE"
        and apply_bit
        and receipt_ok
        and envelope_clear
        and login_ok
        and (not leave)
    )
    reason = "authorize_writer" if authorize else (
        "jev_dark_stand" if dark else
        "choice_not_place" if choice != "PLACE" else
        "apply_flag_off" if not apply_bit else
        "prove_receipt_missing_or_unproven" if not receipt_ok else
        "envelope_hit" if not envelope_clear else
        "login_or_leave_orig"
    )
    return {
        "schema": "jev_place_fluid_v0",
        "authorize_writer": authorize,
        "broker_effect": False,
        "choice": choice,
        "reason": reason,
        "scoped": scoped,
        "never_place": not authorize,
        "never_place_default": True,
        "owner_override_20260921_place_when_proved": True,
        "do_not_flip_GTOS_JEV_SLEEVE_SELECT_APPLY": True,
        "do_not_use_GTOS_JEV_FLUID_GATES_APPLY_for_place": True,
    }
