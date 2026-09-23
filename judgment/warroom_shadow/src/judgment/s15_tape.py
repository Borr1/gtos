"""Challenge 0 historical tape for S15 COST_OF_ERROR prove.

Close Loop ticket identities + gold_state.v0 bucket fields only. No live
bars, no raw OHLCV, no invented NEWS_PROTOCOL. S14 rows are reused where
the ticket already lives on the S14 tape; remaining Close Loop tickets
are materialized with the same Challenge login / magic / ns.
"""

from __future__ import annotations

from typing import Any

from .challenge import CHALLENGE_LOGIN
from .conf_gate import (
    REVIEW_KEEP_TICKET,
    REVIEW_OFFHOURS_TICKET,
    TICKET_SUBCLASS,
)
from .s14_tape import _answers, gold_state, historical_tape_rows

FS_HALF_TICKETS = tuple(
    ticket for ticket, subclass in TICKET_SUBCLASS.items() if subclass == "fs_half_still_losing"
)
EVENT_TICKETS = tuple(
    ticket for ticket, subclass in TICKET_SUBCLASS.items() if subclass == "event_gap_shadow"
)
SESSION_TICKETS = tuple(
    ticket for ticket, subclass in TICKET_SUBCLASS.items() if subclass == "session_cut_loss"
)

SESSION_CUT_NAMED = ("london", "ny", "asia", "london")


def _stamp_identity(gold: dict[str, Any], *, ticket: str, subclass: str) -> dict[str, Any]:
    identity = dict(gold.get("identity") or {})
    identity["ticket"] = ticket
    identity["s15_subclass"] = subclass
    gold = dict(gold)
    gold["identity"] = identity
    return gold


def _p_for_fs_half(index: int) -> float:
    """Mix HIGH / MED / LOW so the vendor-0.85 baseline can move."""

    if index < 8:
        return 0.88
    if index < 14:
        return 0.62
    return 0.35


def s15_historical_tape_rows() -> list[dict[str, Any]]:
    """Close Loop labeled Challenge rows plus hard-off / review identities."""

    rows: list[dict[str, Any]] = []

    def add(
        *,
        tape_id: str,
        ticket: str,
        subclass: str,
        sleeve: str,
        symbol: str,
        side: str,
        choice: str,
        conf: float,
        change: float,
        viable: float,
        session: str,
        g4_applies: bool,
        note: str,
        spine_empty: bool = True,
        events: list[Any] | None = None,
        occupancy: dict[str, Any] | None = None,
        ret1: float = 0.012,
        ret5: float = 0.03,
        vol: float = 1.05,
        slope: float = 0.8,
        mom: float = 0.6,
        sma: float = 0.02,
    ) -> None:
        cid = f"challenge:{CHALLENGE_LOGIN}:{ticket}:{sleeve}:{side}"
        gold = gold_state(
            sleeve=sleeve,
            symbol=symbol,
            side=side,
            candidate_id=cid,
            close_ret_1=ret1,
            close_ret_5bar=ret5,
            vol_ratio=vol,
            htf_slope_norm=slope,
            mom_20_atr=mom,
            sma_frac=sma,
            session=session,
            occupancy=occupancy,
            spine_empty=spine_empty,
            events=events,
        )
        gold = _stamp_identity(gold, ticket=ticket, subclass=subclass)
        rows.append(
            {
                "tape_id": tape_id,
                "login": CHALLENGE_LOGIN,
                "ns": "operator",
                "magic": 0,
                "ticket": ticket,
                "subclass": subclass,
                "g4_applies": g4_applies,
                "note": note,
                "gold_state": gold,
                "system_one_answers": _answers(choice, conf, change, viable),
            }
        )

    for i, ticket in enumerate(FS_HALF_TICKETS):
        add(
            tape_id=f"fs-half-{i+1:02d}",
            ticket=ticket,
            subclass="fs_half_still_losing",
            sleeve="metals_core",
            symbol="XAUUSD",
            side="short" if i % 2 else "long",
            choice="trend_down" if i % 2 else "trend_up",
            conf=_p_for_fs_half(i),
            change=0.22,
            viable=0.72,
            session="off_hours",
            g4_applies=True,
            note="false_admit_fs_half_still_losing",
            ret1=-0.013 if i % 2 else 0.012,
            ret5=-0.028 if i % 2 else 0.03,
            slope=-0.8 if i % 2 else 0.8,
            mom=-0.5 if i % 2 else 0.6,
        )

    for i, ticket in enumerate(SESSION_TICKETS):
        add(
            tape_id=f"session-{i+1:02d}",
            ticket=ticket,
            subclass="session_cut_loss",
            sleeve="metals_core",
            symbol="XAUUSD",
            side="long",
            choice="trend_up",
            conf=0.84 if i % 2 else 0.88,
            change=0.20,
            viable=0.70,
            session=SESSION_CUT_NAMED[i % len(SESSION_CUT_NAMED)],
            g4_applies=False,
            note="false_admit_session_cut_loss",
        )

    for i, ticket in enumerate(EVENT_TICKETS):
        add(
            tape_id=f"event-{i+1:02d}",
            ticket=ticket,
            subclass="event_gap_shadow",
            sleeve="metals_core",
            symbol="XAUUSD",
            side="long",
            choice="trend_up",
            conf=0.70,
            change=0.24,
            viable=0.68,
            session="off_hours",
            g4_applies=True,
            note="false_admit_event_gap_stamped_only",
            spine_empty=False,
            events=[{"source": "stamped", "stamped": True, "proximity": True, "ticket": ticket}],
        )

    add(
        tape_id="review-291087142",
        ticket=REVIEW_KEEP_TICKET,
        subclass="full_size_loss",
        sleeve="vss_fxcross_london_up_low",
        symbol="EURGBP",
        side="sell",
        choice="range",
        conf=0.90,
        change=0.20,
        viable=0.70,
        session="off_hours",
        g4_applies=False,
        note="review_keep_full_size_loss_291087142",
        ret1=0.001,
        ret5=-0.002,
        vol=0.85,
        slope=0.05,
        mom=-0.04,
        sma=0.0,
    )

    add(
        tape_id="review-293128383",
        ticket=REVIEW_OFFHOURS_TICKET,
        subclass="review_keep_offhours_false_structure",
        sleeve="sub_mid_dn_re",
        symbol="XAUUSD",
        side="short",
        choice="trend_down",
        conf=0.80,
        change=0.18,
        viable=0.65,
        session="off_hours",
        g4_applies=False,
        note="review_keep_offhours_not_hard_off",
        ret1=-0.009,
        ret5=-0.02,
        vol=1.0,
        slope=-0.6,
        mom=-0.4,
    )

    add(
        tape_id="reject-index",
        ticket="s15idx",
        subclass="cost_avoided_by_reject",
        sleeve="idxrev",
        symbol="UK100.cash",
        side="sell",
        choice="trend_down",
        conf=0.91,
        change=0.12,
        viable=0.88,
        session="london",
        g4_applies=False,
        note="cost_avoided_by_reject_index",
        ret1=-0.01,
        ret5=-0.025,
        vol=1.1,
        slope=-0.7,
        mom=-0.4,
    )
    add(
        tape_id="reject-crypto",
        ticket="s15orb",
        subclass="cost_avoided_by_reject",
        sleeve="orb_crypto_london",
        symbol="ETHUSD",
        side="buy",
        choice="trend_up",
        conf=0.89,
        change=0.15,
        viable=0.84,
        session="london",
        g4_applies=False,
        note="cost_avoided_by_reject_crypto",
        ret1=0.015,
        ret5=0.04,
        vol=1.4,
        slope=0.9,
        mom=0.7,
    )
    add(
        tape_id="reject-us30",
        ticket="291113462",
        subclass="cost_avoided_by_reject",
        sleeve="dsp_walked_hi",
        symbol="US30.cash",
        side="buy",
        choice="trend_up",
        conf=0.86,
        change=0.20,
        viable=0.70,
        session="ny",
        g4_applies=False,
        note="cost_avoided_by_reject_us30",
    )

    # Keep S14 Challenge identities reachable for same-sidecar compose checks.
    seen = {str(r["ticket"]) for r in rows}
    for inherited in historical_tape_rows():
        gold = inherited.get("gold_state") or {}
        ident = gold.get("identity") if isinstance(gold, dict) else {}
        cid = str((ident or {}).get("candidate_id") or "")
        parts = cid.split(":")
        ticket = parts[2] if len(parts) >= 3 else ""
        if ticket and ticket in seen:
            continue
        if ticket and ticket in TICKET_SUBCLASS:
            continue
        rows.append(
            {
                "tape_id": f"s14-inherit-{inherited.get('tape_id')}",
                "login": CHALLENGE_LOGIN,
                "ns": "operator",
                "magic": 0,
                "ticket": ticket or None,
                "subclass": None,
                "g4_applies": False,
                "note": inherited.get("note") or "s14_identity",
                "gold_state": gold,
                "system_one_answers": inherited.get("system_one_answers"),
            }
        )
    return rows
