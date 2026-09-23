"""F5 Challenge account identity for study/decide paths.

Chair retargeted VPS ``f5_study`` LIVE and ``nightly_study.ps1`` to Challenge
login ``0``. This module is the GitHub pin so a pull cannot drift
back to verification ``0``.

Challenge-only. redacted_account is out of scope. No broker-send.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

CHALLENGE_LOGIN = 0
VERIFICATION_LOGIN_QUARANTINED = 0
LIVE = CHALLENGE_LOGIN
MAGIC = 0
NAMESPACE = "operator"
PASS_TARGET = "$110k"
BROKER = "FTMO"
ACCOUNT_KIND = "challenge"

_LOGIN_KEYS = (
    "login",
    "LIVE",
    "live",
    "account_login",
    "account_id",
)


class VerificationLoginQuarantined(ValueError):
    """Study/decide was pointed at verification 0."""


class ChallengeLoginRequired(ValueError):
    """Study/decide login is missing or is not Challenge 0."""


def coerce_login(raw: Any) -> int | None:
    if raw is None or raw is False:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def resolve_live(raw: Any = None, *, default: int = LIVE) -> int:
    """Resolve LIVE/login. Empty → Challenge. Verification always raises."""
    login = coerce_login(raw)
    if login is None:
        login = int(default)
    return assert_challenge_login(login)


def assert_challenge_login(login: Any) -> int:
    resolved = coerce_login(login)
    if resolved is None:
        raise ChallengeLoginRequired("study/decide login is missing; Challenge LIVE is 0")
    if resolved == VERIFICATION_LOGIN_QUARANTINED:
        raise VerificationLoginQuarantined(
            "verification login 0 is quarantined; Challenge LIVE is 0"
        )
    if resolved != CHALLENGE_LOGIN:
        raise ChallengeLoginRequired(
            f"study/decide login {resolved} is not Challenge {CHALLENGE_LOGIN}"
        )
    return resolved


def extract_payload_login(obj: Mapping[str, Any] | None) -> int | None:
    if not isinstance(obj, Mapping):
        return None
    for key in _LOGIN_KEYS:
        login = coerce_login(obj.get(key))
        if login is not None:
            return login
    account = obj.get("account")
    if isinstance(account, Mapping):
        for key in ("login", "LIVE", "live"):
            login = coerce_login(account.get(key))
            if login is not None:
                return login
    identity = obj.get("identity")
    if isinstance(identity, Mapping):
        login = coerce_login(identity.get("login") or identity.get("LIVE") or identity.get("live"))
        if login is not None:
            return login
    return None


def row_login(row: Mapping[str, Any] | None) -> int | None:
    if not isinstance(row, Mapping):
        return None
    for key in _LOGIN_KEYS:
        login = coerce_login(row.get(key))
        if login is not None:
            return login
    return None


def filter_challenge_rows(rows: Iterable[Any]) -> tuple[list[Any], int, int]:
    """Keep Challenge (or unstamped) rows. Drop verification and other logins."""
    kept: list[Any] = []
    dropped_verification = 0
    dropped_other = 0
    for row in rows:
        if not isinstance(row, Mapping):
            kept.append(row)
            continue
        login = row_login(row)
        if login is None or login == CHALLENGE_LOGIN:
            kept.append(row)
            continue
        if login == VERIFICATION_LOGIN_QUARANTINED:
            dropped_verification += 1
            continue
        dropped_other += 1
    return kept, dropped_verification, dropped_other


def refuse_verification_payload(obj: Mapping[str, Any] | None) -> None:
    """Fail closed if the study/decide body is stamped verification."""
    login = extract_payload_login(obj)
    if login is None:
        return
    assert_challenge_login(login)


def identity_stamp() -> dict[str, Any]:
    return {
        "login": CHALLENGE_LOGIN,
        "LIVE": LIVE,
        "magic": MAGIC,
        "namespace": NAMESPACE,
        "pass_target": PASS_TARGET,
        "broker": BROKER,
        "account_kind": ACCOUNT_KIND,
        "verification_login_quarantined": VERIFICATION_LOGIN_QUARANTINED,
        "broker_send": False,
        "redacted_account_in_scope": False,
    }
