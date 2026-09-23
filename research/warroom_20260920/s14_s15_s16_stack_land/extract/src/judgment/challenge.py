"""Challenge payout identity for Jev fluid-gate shadow logs.

Challenge login ``0`` is the sole payout / calibration writer.
Verification ``0`` is quarantined. This module never talks to a broker.
"""

from __future__ import annotations

CHALLENGE_LOGIN = "0"
CHALLENGE_PASS_TARGET = "$110k"
CHALLENGE_MAGIC = "0"
CHALLENGE_NS = "operator"
VERIFICATION_QUARANTINED = "0"

#: F5 keep-family nouns (V2 / house law). Not a W7 armed-set reprint.
CHALLENGE_KEEP_FAMILIES = ("spring", "vss")
CHALLENGE_HARD_OFF_FAMILIES = (
    "bleed",
    "orb_crypto",
    "idxrev",
    "xa_huge",
    "mx_us30",
)

CHALLENGE_WORKER_ID = f"challenge:{CHALLENGE_LOGIN}"


class QuarantinedAccountError(ValueError):
    """Verification login used as a shadow / payout surface."""


class PayoutWriterError(ValueError):
    """A login other than Challenge 0 tried to own a payout row."""


def assert_challenge_payout_writer(login: str) -> None:
    """Refuse any login that is not Challenge 0.

    Verification 0 is named so a silent splice fails closed instead of
    looking like a second Challenge book.
    """

    raw = str(login or "").strip()
    if raw == VERIFICATION_QUARANTINED:
        raise QuarantinedAccountError(
            "verification login 0 is quarantined; do not shadow-batch "
            "or stamp payout rows on it"
        )
    if raw != CHALLENGE_LOGIN:
        raise PayoutWriterError(
            f"Challenge {CHALLENGE_LOGIN} is the sole payout writer; got {raw!r}"
        )


def account_surface() -> dict[str, str]:
    """The house-law identity block stamped on every fluid-gate log."""

    return {
        "login": CHALLENGE_LOGIN,
        "pass_target": CHALLENGE_PASS_TARGET,
        "magic": CHALLENGE_MAGIC,
        "ns": CHALLENGE_NS,
        "role": "challenge_calibration",
        "verification_login_quarantined": VERIFICATION_QUARANTINED,
    }
