"""Hard PLACE allowlist for Feedback Fleet demo/trial workers.

Chair / Jev / ``run_book.py`` still never place on observer books.
This module is the only fleet writer, and it may PLACE only on
Free Trial / demo terminals. Challenge copy is VETO.

Source events: Challenge login 0 only (enforced by the relay).
PLACE targets: never 0, never quarantine 0, never
``\\MT5\\FTMO\\`` without a demo/trial marker.
"""

from __future__ import annotations

from typing import Any

from judgment.fleet.common import QUARANTINE_LOGINS, SOURCE_LOGIN

FORBIDDEN_LOGINS = frozenset({SOURCE_LOGIN, *QUARANTINE_LOGINS})
# Windows Challenge writer terminal (portable FTMO book). Needle is the
# directory, not ``FTMO_Trial`` / ``FTMO_redacted_account`` / ``FTMO_redacted_account``.
CHALLENGE_PATH_NEEDLE = "\\MT5\\FTMO\\"
CHALLENGE_PATH_TAIL = "\\MT5\\FTMO"
DEMO_PATH_MARKERS_CASE = ("_Trial", "_redacted_account", "_redacted_account")
DEMO_PATH_MARKERS_CI = ("demo", "trial", "freetrial", "free_trial", "free trial", "redacted_account")

ALLOWED_ACCOUNT_KINDS = frozenset(
    {
        "demo",
        "trial",
        "free_trial",
        "free trial",
        "freetrial",
        "mt5_demo",
    }
)
FORBIDDEN_ACCOUNT_KINDS = frozenset(
    {
        "challenge",
        "ftmo_challenge",
        "ftmo",
        "verification",
        "live",
        "funded",
        "payout",
    }
)


class PlaceVeto(Exception):
    """Refuse a PLACE attempt. Never swallowed into an order_send."""

    def __init__(self, reason: str, **extra: Any) -> None:
        self.reason = reason
        self.extra = extra
        super().__init__(reason)


def _as_int_login(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return int(text) if text.isdigit() else None


def normalize_terminal_path(path: str | None) -> str:
    if not path:
        return ""
    return str(path).replace("/", "\\").strip()


def login_is_forbidden(login: Any) -> bool:
    parsed = _as_int_login(login)
    return parsed is None or parsed in FORBIDDEN_LOGINS


def path_has_demo_marker(path: str | None) -> bool:
    raw = str(path or "")
    if any(marker in raw for marker in DEMO_PATH_MARKERS_CASE):
        return True
    folded = raw.lower()
    return any(marker in folded for marker in DEMO_PATH_MARKERS_CI)


def looks_like_challenge_path(path: str | None) -> bool:
    """True when the path is the FTMO Challenge writer tree (no demo marker)."""
    norm = normalize_terminal_path(path)
    if not norm:
        return False
    folded = norm.upper()
    challenge_shaped = CHALLENGE_PATH_NEEDLE.upper() in folded or folded.rstrip("\\").endswith(
        CHALLENGE_PATH_TAIL
    )
    if not challenge_shaped:
        return False
    return not path_has_demo_marker(path)


def account_kind_allowed(account_kind: str | None) -> bool:
    kind = str(account_kind or "").strip().lower()
    if not kind:
        return False
    if kind in FORBIDDEN_ACCOUNT_KINDS:
        return False
    return kind in ALLOWED_ACCOUNT_KINDS


def place_veto_reason(
    *,
    login: Any,
    terminal_path: str | None,
    account_kind: str | None = None,
) -> str | None:
    """Return a VETO reason, or None if PLACE on this target is allowed."""
    parsed = _as_int_login(login)
    if parsed is None:
        return "missing_demo_login"
    if parsed == SOURCE_LOGIN:
        return "forbidden_challenge_login"
    if parsed in QUARANTINE_LOGINS:
        return "forbidden_quarantine_login"
    if parsed in FORBIDDEN_LOGINS:
        return "forbidden_login"
    path = normalize_terminal_path(terminal_path)
    if not path:
        return "missing_terminal_path"
    if looks_like_challenge_path(path):
        return "forbidden_challenge_path"
    if account_kind is not None and not account_kind_allowed(account_kind):
        if str(account_kind).strip().lower() in FORBIDDEN_ACCOUNT_KINDS:
            return "veto_challenge_copy"
        return "account_kind_not_demo"
    return None


def assert_demo_place_target(
    *,
    login: Any,
    terminal_path: str | None,
    account_kind: str | None = None,
) -> int:
    reason = place_veto_reason(login=login, terminal_path=terminal_path, account_kind=account_kind)
    if reason is not None:
        raise PlaceVeto(
            reason,
            login=_as_int_login(login),
            terminal_path=normalize_terminal_path(terminal_path),
            account_kind=account_kind,
            place_on_challenge=False,
        )
    parsed = _as_int_login(login)
    assert parsed is not None
    return parsed


def is_challenge_copy_pair(source_login: Any, target_login: Any) -> bool:
    """FTMO challenge↔challenge copy. Always VETO."""
    src = _as_int_login(source_login)
    dst = _as_int_login(target_login)
    if src is None or dst is None:
        return False
    if src in FORBIDDEN_LOGINS and dst in FORBIDDEN_LOGINS:
        return True
    if src == SOURCE_LOGIN and dst == SOURCE_LOGIN:
        return True
    return False
