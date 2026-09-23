"""place_seat_trust ΓÇö KEEP tickets only for remint/flatten Choice.

PLACE_APPLY and PLACE_ENSEMBLE are already live on Challenge 0.
This module does not re-implement place. It is the trust table those
wires already honor, reused by remint/flatten/deal_close LABEL consume.

Choice refuses incomplete SHA-256. redacted_account is out. Verification
0 is quarantined. ``pack1b_beaten`` stays false. Never broker-send.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .challenge import (
    CHALLENGE_HARD_OFF_FAMILIES,
    CHALLENGE_KEEP_FAMILIES,
    CHALLENGE_LOGIN,
    CHALLENGE_NS,
    VERIFICATION_QUARANTINED,
    assert_challenge_payout_writer,
)
from .chair_enforce import is_hard_off_sleeve, is_keep_family
from .conf_gate import REVIEW_KEEP_TICKET
from .family import hard_off_family, keep_family
from .p0_hist_prove import FIRE_1201_KEEP_WIN_TICKETS
from .process_lock import LEAVE_ORIG_TICKETS, leave_orig_ticket
from .veto import InventedNewsProtocolVeto, refuse_invented_news_protocol

#: Already-live place wires. Remint/flatten consume must not re-open place.
PLACE_APPLY = "PLACE_APPLY"
PLACE_ENSEMBLE = "PLACE_ENSEMBLE"
PLACE_WIRES_LIVE = (PLACE_APPLY, PLACE_ENSEMBLE)

CHALLENGE_LOGIN_INT = 0
redacted_account_NS_MARKERS = (
    "redacted_account",
    "fn_",
    "fn-",
    "funded_next",
)

# FIRE 1201 KEEP wins + Chair KEEP-family residual that is not hard-off.
# REVIEW_OFFHOURS 293128383 stays deal_close-labelable, not remint KEEP.
KEEP_TRUST_TICKETS = frozenset(FIRE_1201_KEEP_WIN_TICKETS) | frozenset({REVIEW_KEEP_TICKET})

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# Dig B leftover: pack1b is not beaten. Consume must never flip this.
PACK1B_BEATEN = False

SCHEMA = "gtos.judgment.place_seat_trust.v1"


def pack1b_beaten() -> bool:
    """Standing false. A true value is a consume defect, not a gate."""

    return PACK1B_BEATEN


def is_complete_sha256(value: Any) -> bool:
    """True only for a 64-char lowercase/mixed hex digest. LFS pointers fail."""

    if value is None:
        return False
    raw = str(value).strip()
    if not raw:
        return False
    if raw.startswith("version https://git-lfs"):
        return False
    if "incomplete" in raw.lower():
        return False
    return bool(SHA256_HEX_RE.fullmatch(raw.lower()))


def refuse_incomplete_hash(value: Any, *, field: str = "sha256") -> str:
    """Return the digest or raise. Choice path uses this before APPLY."""

    if not is_complete_sha256(value):
        raise IncompleteHashError(f"{field} is not a complete SHA-256 digest")
    return str(value).strip().lower()


class IncompleteHashError(ValueError):
    """Remint/flatten Choice saw a missing, short, or LFS-pointer hash."""


class SeatTrustError(ValueError):
    """Seat failed Challenge / KEEP / hash / NEWS / pack1b walls."""


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def is_redacted_account(*, ns: Any = None, login: Any = None) -> bool:
    raw_ns = str(ns or "").strip().lower()
    if any(marker in raw_ns for marker in redacted_account_NS_MARKERS):
        return True
    if login is not None and str(login).strip() not in {"", CHALLENGE_LOGIN, str(CHALLENGE_LOGIN_INT)}:
        # Non-Challenge login is not automatically FN, but FN ns is enough.
        return False
    return False


def is_challenge_surface(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN_INT
        except (TypeError, ValueError):
            login_ok = str(login).strip() == CHALLENGE_LOGIN
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def keep_ticket(
    ticket: Any,
    *,
    sleeve: Any = None,
    symbol: Any = None,
) -> bool:
    """True only for place_seat_trust KEEP tickets.

    FIRE 1201 KEEP wins always. Chair KEEP families (spring / vss) when the
    sleeve is present. Leave-orig is never KEEP for remint. Hard-off is never
    KEEP. A KEEP-family sleeve without a trusted ticket still fails ΓÇö tickets
    only.
    """

    raw = str(ticket or "").strip()
    if not raw:
        return False
    if leave_orig_ticket(raw):
        return False
    if is_hard_off_sleeve(str(sleeve or "")):
        return False
    if hard_off_family(str(sleeve or ""), str(symbol or "")):
        return False
    if raw in KEEP_TRUST_TICKETS:
        return True
    if sleeve and (keep_family(str(sleeve)) or is_keep_family(str(sleeve))):
        # Sleeve KEEP is not enough ΓÇö remint/flatten Choice is ticket-keyed.
        return raw in KEEP_TRUST_TICKETS
    return False


def assert_place_wires_already_live() -> dict[str, Any]:
    """PLACE_APPLY + PLACE_ENSEMBLE are named live. Do not re-implement."""

    return {
        "schema": SCHEMA,
        "place_apply": PLACE_APPLY,
        "place_ensemble": PLACE_ENSEMBLE,
        "already_live": True,
        "reimplement_place_forbidden": True,
        "never_place": True,
        "never_broker_send": True,
        "pack1b_beaten": pack1b_beaten(),
    }


def trust_seat(
    seat: Mapping[str, Any] | None,
    *,
    invented_files: Iterable[str] = (),
) -> dict[str, Any]:
    """Judge one remint/flatten/deal_close seat. LABEL trust only.

    Returns a stamp. Does not write. Does not call a broker. Raises only
    for NEWS invent (same veto as the rest of judgment).
    """

    refuse_invented_news_protocol(invented_files)
    extra_invented = ()
    if isinstance(seat, Mapping):
        extra_invented = tuple(seat.get("invented_files") or ())
    if extra_invented:
        refuse_invented_news_protocol(extra_invented)

    row = dict(seat or {})
    ticket = row.get("ticket")
    sleeve = row.get("sleeve")
    symbol = row.get("symbol")
    login = row.get("login") if row.get("login") is not None else CHALLENGE_LOGIN
    ns = row.get("ns") if row.get("ns") is not None else CHALLENGE_NS
    kind = str(row.get("kind") or row.get("action") or "").strip().lower()
    digest = row.get("sha256") or row.get("seat_sha256") or row.get("draft_sha256")

    stamp = {
        "schema": SCHEMA,
        "ticket": None if ticket is None else str(ticket).strip(),
        "kind": kind or None,
        "login": str(login or ""),
        "ns": str(ns or ""),
        "sleeve": sleeve,
        "symbol": symbol,
        "place_apply_live": True,
        "place_ensemble_live": True,
        "pack1b_beaten": pack1b_beaten(),
        "never_place": True,
        "never_remint_broker": True,
        "never_flatten_broker": True,
        "never_broker_send": True,
        "broker_effect": False,
        "keep_ticket": False,
        "hash_complete": False,
        "trusted": False,
        "reason": "unchecked",
    }

    if row.get("pack1b_beaten") is True or pack1b_beaten():
        stamp["reason"] = "pack1b_beaten_must_stay_false"
        return stamp

    if str(login or "").strip() == VERIFICATION_QUARANTINED:
        stamp["reason"] = "verification_quarantined"
        return stamp

    if is_redacted_account(ns=ns, login=login):
        stamp["reason"] = "redacted_account_forbidden"
        return stamp

    if not is_challenge_surface(login=login, ns=ns):
        stamp["reason"] = "not_challenge_surface"
        return stamp

    try:
        assert_challenge_payout_writer(str(login))
    except Exception:
        stamp["reason"] = "not_challenge_payout_writer"
        return stamp

    if leave_orig_ticket(ticket) and kind in {"remint", "flatten"}:
        stamp["reason"] = "leave_orig_no_remint"
        return stamp

    if kind in {"place", "order_send", "open_trade"}:
        stamp["reason"] = "place_path_veto_already_live_wires_only"
        return stamp

    off = hard_off_family(str(sleeve or ""), str(symbol or ""))
    if off or is_hard_off_sleeve(str(sleeve or "")):
        stamp["reason"] = f"hard_off:{off or 'family'}"
        return stamp

    stamp["keep_ticket"] = keep_ticket(ticket, sleeve=sleeve, symbol=symbol)
    stamp["hash_complete"] = is_complete_sha256(digest)
    if not stamp["hash_complete"]:
        stamp["reason"] = "incomplete_sha256"
        return stamp
    if not stamp["keep_ticket"]:
        stamp["reason"] = "not_keep_ticket"
        return stamp

    stamp["trusted"] = True
    stamp["reason"] = "place_seat_trust_keep"
    stamp["sha256"] = str(digest).strip().lower()
    stamp["keep_families"] = list(CHALLENGE_KEEP_FAMILIES)
    stamp["hard_off_families"] = list(CHALLENGE_HARD_OFF_FAMILIES)
    stamp["leave_orig_tickets"] = sorted(LEAVE_ORIG_TICKETS)
    return stamp
