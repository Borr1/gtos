"""Owner PLACE_APPLY unlock for Challenge place / remint / flatten.

Chair stamped ``never_place`` as an eternal const. That was conservatism,
not owner law. After Challenge hist-prove (FIRE 1201 KEEP wins preserved)
the owner unlock is ``PLACE_APPLY=1`` (alias ``GTOS_JEV_PLACE_APPLY=1``).

Default is fail-closed. The cage lifts only when every envelope clause
holds:

* Challenge identity (login ``0`` / ns ``operator``)
* no redacted_account / verification login
* no Jev kill env
* Jev not dark (``GTOS_JEV_DARK=1`` or jev_status dark/unavailable/error).
  ``GTOS_JEV_A1_CALL=0`` is test/budget isolation, not organism dark.
* hist-prove allowed
* no invented NEWS_PROTOCOL
* leave-orig ticket 293332188 stays locked

This module authorizes the cage lift. It does not ``order_send``.
Dig/S16, harvest surveys, and W7 books stay off this path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_NS, VERIFICATION_QUARANTINED

PLACE_APPLY_ENV = "PLACE_APPLY"
PLACE_APPLY_ENV_ALIASES = (PLACE_APPLY_ENV, "GTOS_JEV_PLACE_APPLY")

KILL_ENVS = ("GTOS_JEV_KILL", "GTOS_JEV_PLACE_KILL", "PLACE_KILL")
DARK_ENV = "GTOS_JEV_DARK"

redacted_account_MARKERS = ("redacted_account", "fn_server", "fn-server")
LEAVE_ORIG_TICKETS = frozenset({"293332188"})
INVENTED_NEWS = "NEWS_PROTOCOL"

UNLOCKABLE_ACTIONS = frozenset(
    {
        "place",
        "remint",
        "flatten",
        "order_send",
        "open_trade",
        "broker",
        "order",
    }
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env(environ: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return environ if environ is not None else os.environ


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in _TRUTHY


def place_apply_requested(*, environ: Mapping[str, str] | None = None) -> bool:
    env = _env(environ)
    return any(_truthy(env.get(name)) for name in PLACE_APPLY_ENV_ALIASES)


def identity_is_challenge(*, login: Any = None, ns: Any = None) -> bool:
    """Challenge-only. Omitted identity defaults to the Challenge writer."""

    if login is None and ns is None:
        return True
    login_raw = "" if login is None else str(login).strip()
    ns_raw = "" if ns is None else str(ns).strip()
    if login_raw == VERIFICATION_QUARANTINED:
        return False
    if ns_raw and any(marker in ns_raw.lower() for marker in redacted_account_MARKERS):
        return False
    if login_raw and login_raw != CHALLENGE_LOGIN:
        try:
            if int(login_raw) != int(CHALLENGE_LOGIN):
                return False
        except (TypeError, ValueError):
            return False
    if ns_raw and ns_raw != CHALLENGE_NS:
        return False
    return True


def redacted_account_forbidden(*, login: Any = None, ns: Any = None) -> bool:
    ns_raw = "" if ns is None else str(ns).strip().lower()
    login_raw = "" if login is None else str(login).strip().lower()
    if any(marker in ns_raw for marker in redacted_account_MARKERS):
        return True
    if any(marker in login_raw for marker in redacted_account_MARKERS):
        return True
    return False


def kill_flags_armed(
    *,
    environ: Mapping[str, str] | None = None,
    flags: Iterable[Any] | None = None,
) -> tuple[str, ...]:
    env = _env(environ)
    hits: list[str] = []
    for name in KILL_ENVS:
        if _truthy(env.get(name)):
            hits.append(name)
    for raw in flags or ():
        text = str(raw or "").strip()
        if not text:
            continue
        if text in {"ENV-KILL", "$KILL", "ENV-H8", "h8_flatten"} or text.upper() == "KILL":
            hits.append(text)
    return tuple(hits)


def jev_is_dark(
    *,
    environ: Mapping[str, str] | None = None,
    jev_status: str | None = None,
) -> bool:
    """Organism dark — not ``GTOS_JEV_A1_CALL=0`` (test/budget isolation)."""

    env = _env(environ)
    if _truthy(env.get(DARK_ENV)):
        return True
    if jev_status is None:
        return False
    return str(jev_status).strip().lower() in {"dark", "unavailable", "error"}


def news_invent_requested(invented_files: Iterable[str] | None = None) -> bool:
    return any(str(name).strip() == INVENTED_NEWS for name in (invented_files or ()))


def leave_orig_locked(ticket: Any = None) -> bool:
    if ticket is None:
        return False
    return str(ticket).strip() in LEAVE_ORIG_TICKETS


@dataclass(frozen=True)
class PlaceApplyDecision:
    """Cage lift. ``allowed`` does not mean a broker send happened."""

    allowed: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "place_apply": self.allowed,
            "place_apply_reason": self.reason,
            "never_place": not self.allowed,
            "never_remint": not self.allowed,
            "never_flatten": not self.allowed,
        }


def evaluate_place_apply(
    *,
    environ: Mapping[str, str] | None = None,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
    invented_files: Iterable[str] | None = None,
    flags: Iterable[Any] | None = None,
    jev_status: str | None = None,
    hist_prove: Mapping[str, Any] | None = None,
    skip_hist: bool = False,
) -> PlaceApplyDecision:
    if not place_apply_requested(environ=environ):
        return PlaceApplyDecision(False, "place_apply_off")
    if redacted_account_forbidden(login=login, ns=ns):
        return PlaceApplyDecision(False, "redacted_account_forbidden")
    if not identity_is_challenge(login=login, ns=ns):
        return PlaceApplyDecision(False, "identity_not_challenge")
    kills = kill_flags_armed(environ=environ, flags=flags)
    if kills:
        return PlaceApplyDecision(False, f"kill_flag:{kills[0]}")
    if jev_is_dark(environ=environ, jev_status=jev_status):
        return PlaceApplyDecision(False, "jev_dark")
    if news_invent_requested(invented_files):
        return PlaceApplyDecision(False, "news_invent")
    if leave_orig_locked(ticket):
        return PlaceApplyDecision(False, "leave_orig")
    if not skip_hist:
        packed = hist_prove
        if packed is None:
            from .p0_hist_prove import hist_prove_allows_label_apply

            packed = hist_prove_allows_label_apply()
        if not bool((packed or {}).get("allowed")):
            return PlaceApplyDecision(
                False, str((packed or {}).get("reason") or "hist_prove_blocked")
            )
    return PlaceApplyDecision(True, "place_apply_authorized")


def place_authorized(**kwargs: Any) -> bool:
    return evaluate_place_apply(**kwargs).allowed


def cage_stamp(**kwargs: Any) -> dict[str, Any]:
    return evaluate_place_apply(**kwargs).as_dict()


def research_never_stamp() -> dict[str, bool]:
    """Observe / research / Dig writers stay caged even when PLACE_APPLY=1."""

    return {
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
    }


def action_unlockable(action: str) -> bool:
    name = str(action or "").strip().lower()
    if name in UNLOCKABLE_ACTIONS:
        return True
    return any(token == name or name.endswith(f"_{token}") for token in ("place", "remint", "flatten"))
