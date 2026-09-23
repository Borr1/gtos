"""s19 — compose fail-closed when Jev is dark.

Today `flow_alignment_size_tilt(None) → 1.0` (fail-open). Dark Jev still
fires full named size. Usage-ramp observe must not silently size-up.

When GTOS_JEV_FAIL_CLOSED_DARK=1 and receipt is dark:
- size_mult stays 1.0 (cannot size-up, cannot zero)
- stamp jev_dark
- cannot refuse envelope
- leave-orig tickets stay 1.0

Physical APPLY still Challenge login/ns only. This module does not place.
"""

from __future__ import annotations

from typing import Any, Mapping

from .jev_client_gate import dark, fail_closed_dark_enabled

LEAVE_ORIG_TICKET = 293332188


def cannot_size_up(receipt: Mapping[str, Any] | None) -> bool:
    return fail_closed_dark_enabled() and dark(receipt)


def compose_size_mult(
    answers: Mapping[str, Any] | None,
    *,
    jev_receipt: Mapping[str, Any] | None = None,
    ticket: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra = dict(extra or {})
    extra.setdefault("news_join", extra.get("news_join") or "STATE_MISSING")
    out: dict[str, Any] = {
        "size_mult": 1.0,
        "place": False,
        "named_apply": False,
        "news_invent": False,
        "leave_orig": ticket == LEAVE_ORIG_TICKET,
        "jev_dark": dark(jev_receipt),
    }
    if out["leave_orig"]:
        out["reason"] = "leave_orig_ticket"
        return out
    if cannot_size_up(jev_receipt):
        out["disposition"] = "stand_dark"
        out["cannot_size_up"] = True
        out["reason"] = "jev_dark_fail_closed"
        extra["jev_dark"] = True
        extra["disposition"] = "stand_dark"
        out["extra"] = extra
        return out
    # Live named tilts stay in apply_size / compose.py — this helper only
    # blocks size-up when dark. Haircut still Challenge-login gated.
    out["disposition"] = "observe"
    out["extra"] = extra
    out["answers_present"] = bool(answers)
    return out
