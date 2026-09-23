"""Challenge place seat-trust from Prove Dig B EXPAND 20260921.

Chair ENFORCE: HIGH-trust blocked seats force conf_order_consume_block on place_choice.
Ticket ids are research anchors; live gate uses symbol×sleeve class.
"""
from __future__ import annotations

from typing import Any

# From EXPAND_RECEIPT + Scout place-relevant labels
BLOCKED_TICKETS = frozenset({
    "291816474",  # EURGBP KEEP thin
    "291076386",  # EURUSD FS
    "291113462",  # US30
    "291087142",  # EURGBP flip 0.333
    "292427064",  # keep_surface=false → KILL
    "292667008",  # keep_surface=false → KILL
    "292885676",  # keep_surface=false → KILL
    "293207416",  # keep_surface=false → KILL
})
ALLOWED_TICKETS = frozenset({
    "291794419",  # KEEP-clear deal_close
    "293540988",  # KEEP-clear deal_close
})

# Live class heuristics (instrument×sleeve) until more seats
# True = force HIGH-trust block for place
_CLASS_BLOCK = {
    ("EURGBP", ""): True,
    ("US30", ""): True,
    ("US30.cash", ""): True,
}


def _norm_sym(symbol: str) -> str:
    s = str(symbol or "").upper().replace(" ", "")
    for suf in (".CASH", "_CASH", ".C"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    return s


def place_high_trust_blocked(
    *,
    symbol: str = "",
    sleeve: str = "",
    ticket: str | None = None,
    evidence_sufficient: bool | None = None,
    flip_rate: float | None = None,
    max_swing_pts: float | None = None,
) -> bool:
    """Return True when place should treat conf as LOW / force DELAY path."""
    tid = str(ticket or "").strip()
    if tid in BLOCKED_TICKETS:
        return True
    if tid in ALLOWED_TICKETS and evidence_sufficient is True:
        return False

    sym = _norm_sym(symbol)
    sleeve_l = str(sleeve or "").lower()

    if sym in {"US30", "US30CASH"} or sym.startswith("US30"):
        return True
    if sym == "EURGBP":
        return True
    if sym == "EURUSD" and ("fs" in sleeve_l or "fresh" in sleeve_l or "three_fresh" in sleeve_l):
        return True
    # thin evidence + any material order sensitivity
    material = (flip_rate is not None and float(flip_rate) > 0) or (
        max_swing_pts is not None and float(max_swing_pts) >= 3
    )
    if evidence_sufficient is False and material:
        return True
    if evidence_sufficient is False and sym in {"EURGBP", "EURUSD", "US30"}:
        return True
    return False


def stamp_place_state(state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    st = dict(state or {})
    blocked = place_high_trust_blocked(
        symbol=str(st.get("symbol") or kwargs.get("symbol") or ""),
        sleeve=str(st.get("sleeve") or kwargs.get("sleeve") or ""),
        ticket=kwargs.get("ticket"),
        evidence_sufficient=kwargs.get("evidence_sufficient", st.get("state_evidence_sufficiency_pass")),
        flip_rate=kwargs.get("flip_rate", st.get("option_order_flip_rate")),
        max_swing_pts=kwargs.get("max_swing_pts", st.get("option_order_swing_pts")),
    )
    if blocked:
        st["conf_order_consume_block"] = True
        st["order_sensitivity_blocks_high"] = True
        st["high_trust_blocked_for_place"] = True
        st["place_seat_trust"] = "HIGH_TRUST_BLOCKED_EXPAND_20260921"
    else:
        st.setdefault("place_seat_trust", "ALLOW_OR_UNKNOWN")
    return st
