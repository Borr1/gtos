"""Remint / flatten / deal_close LABEL consume (Dig B APPLY_CANDIDATE KEEP).

Dig B closed the 60-seat deal_close board. This module lands the consume
drafts marked APPLY_CANDIDATE KEEP: LABEL / envelope consume only.

PLACE_APPLY + PLACE_ENSEMBLE stay the live place wires. Remint/flatten
Choice refuses incomplete SHA-256 and honors ``place_seat_trust`` KEEP
tickets only.

Hard walls:
  * Challenge ns ``operator`` / login 0 only
  * no redacted_account
  * no NEWS invent
  * ``pack1b_beaten`` stays false
  * never broker-send (no order_send / close_position / remint / flatten)

APPLY here is a LABEL draft. KILL is a refused seat. book_owner may
observe the stamp; H8 still means authority-false observes flatten
without mutating.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .challenge import (
    CHALLENGE_LOGIN,
    CHALLENGE_NS,
    account_surface,
    assert_challenge_payout_writer,
)
from .conf_gate import REVIEW_KEEP_TICKET, REVIEW_OFFHOURS_TICKET
from .family import family_class_for, hard_off_family, keep_family
from .p0_hist_prove import FIRE_1201_KEEP_WIN_TICKETS
from .place_seat_trust_remint import (
    PLACE_APPLY,
    PLACE_ENSEMBLE,
    PLACE_WIRES_LIVE,
    IncompleteHashError,
    canonical_sha256,
    is_complete_sha256,
    is_redacted_account,
    keep_ticket,
    pack1b_beaten,
    refuse_incomplete_hash,
    trust_seat,
)
from .process_lock import FORBIDDEN_AUTO_EFFECTS, PREAUTH_EFFECTS, leave_orig_ticket
from .veto import JevPlacePathVeto, refuse_broker_action, refuse_invented_news_protocol

SCHEMA = "gtos.judgment.remint_flatten_consume.v1"
DRAFT_ID = "BOOK_OWNER_REMINT_FLATTEN_CONSUME_DRAFT"
NAMESPACE = "gtos.astra.jev_trial.remint_flatten_consume.v1"
BOARD_SIZE = 60

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TAPE = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "shadow.jsonl"
)
DEFAULT_RECEIPT = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "REMINT_FLATTEN_CONSUME_RECEIPT.json"
)

CONSUME_KINDS = frozenset({"remint", "flatten", "deal_close"})
APPLY_EFFECT = "label"
KILL = "KILL"
APPLY = "APPLY"

# Tape deal_close tickets (46). Frozen so a missing jsonl still has a board.
DEAL_CLOSE_TAPE_TICKETS = (
    "291072108",
    "291076386",
    "291087142",
    "291096187",
    "291113462",
    "291120917",
    "291124471",
    "291139109",
    "291167802",
    "291186653",
    "291210052",
    "291234829",
    "291377397",
    "291383082",
    "291392252",
    "291402598",
    "291417478",
    "291420292",
    "291426696",
    "291439454",
    "291455851",
    "291466548",
    "291480724",
    "291486315",
    "291549869",
    "291549870",
    "291589055",
    "291589065",
    "291713652",
    "291758207",
    "291778371",
    "291789105",
    "291794419",
    "291816474",
    "291821945",
    "291827091",
    "292427064",
    "292513484",
    "292524534",
    "292667008",
    "292876275",
    "292885676",
    "293024386",
    "293128383",
    "293207416",
    "293362731",
)

# Dig B remint/flatten APPLY_CANDIDATE KEEP drafts + measured KILL seats.
# 14 drafts + 46 deal_close = 60.
DIG_B_REMINT_FLATTEN_DRAFTS: tuple[dict[str, Any], ...] = (
    {
        "seat_id": "remint:291794419",
        "kind": "remint",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "remint:291816474",
        "kind": "remint",
        "ticket": "291816474",
        "sleeve": "vss_fxcross_l",
        "symbol": "EURGBP",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "remint:293540988",
        "kind": "remint",
        "ticket": "293540988",
        "sleeve": "vss_fxcross_l",
        "symbol": "EURUSD",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "flatten:291794419",
        "kind": "flatten",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "flatten:291816474",
        "kind": "flatten",
        "ticket": "291816474",
        "sleeve": "vss_fxcross_l",
        "symbol": "EURGBP",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "flatten:293540988",
        "kind": "flatten",
        "ticket": "293540988",
        "sleeve": "vss_fxcross_l",
        "symbol": "EURUSD",
        "draft": "APPLY_CANDIDATE",
    },
    {
        "seat_id": "remint:293332188",
        "kind": "remint",
        "ticket": "293332188",
        "sleeve": "dsp_two_bar_t",
        "symbol": "XAUUSD",
        "draft": "LEAVE_ORIG",
        "expect_kill": "leave_orig_no_remint",
    },
    {
        "seat_id": "remint:incomplete_hash",
        "kind": "remint",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "draft": "INCOMPLETE_HASH",
        "sha256": "deadbeef",
        "expect_kill": "incomplete_sha256",
    },
    {
        "seat_id": "remint:redacted_account",
        "kind": "remint",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "ns": "redacted_account",
        "login": CHALLENGE_LOGIN,
        "draft": "redacted_account",
        "expect_kill": "redacted_account_forbidden",
    },
    {
        "seat_id": "flatten:verification",
        "kind": "flatten",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "login": "0",
        "ns": CHALLENGE_NS,
        "draft": "VERIFICATION",
        "expect_kill": "verification_quarantined",
    },
    {
        "seat_id": "remint:291076386",
        "kind": "remint",
        "ticket": "291076386",
        "sleeve": "xa_huge_20_ex",
        "symbol": "EURUSD",
        "draft": "HARD_OFF",
        "expect_kill": "hard_off:xa_huge",
    },
    {
        "seat_id": "flatten:291113462",
        "kind": "flatten",
        "ticket": "291113462",
        "sleeve": "dsp_first_cra",
        "symbol": "US30.cash",
        "draft": "HARD_OFF",
        "expect_kill": "hard_off:mx_us30",
    },
    {
        "seat_id": "remint:news_invent",
        "kind": "remint",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "draft": "NEWS_INVENT",
        "invented_files": ("NEWS_PROTOCOL",),
        "expect_kill": "news_protocol_invent_veto",
    },
    {
        "seat_id": "flatten:pack1b_beaten",
        "kind": "flatten",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "draft": "PACK1B",
        "pack1b_beaten": True,
        "expect_kill": "pack1b_beaten_must_stay_false",
    },
)


@dataclass(frozen=True)
class ConsumeDecision:
    """LABEL consume outcome. ``broker_effect`` is always False."""

    seat_id: str
    kind: str
    ticket: str | None
    verdict: str
    reason: str
    apply: bool
    keep_ticket: bool
    hash_complete: bool
    chair_verb: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "seat_id": self.seat_id,
            "kind": self.kind,
            "ticket": self.ticket,
            "verdict": self.verdict,
            "reason": self.reason,
            "apply": self.apply,
            "keep_ticket": self.keep_ticket,
            "hash_complete": self.hash_complete,
            "chair_verb": self.chair_verb,
            "broker_effect": False,
            "never_broker_send": True,
            "pack1b_beaten": pack1b_beaten(),
            "notes": list(self.notes),
        }


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seat_id(kind: str, ticket: Any, *, extra: str | None = None) -> str:
    if extra:
        return f"{kind}:{extra}"
    return f"{kind}:{ticket}"


def complete_draft_hash(seat: Mapping[str, Any]) -> str:
    """Canonical digest for an APPLY_CANDIDATE KEEP draft. Always 64 hex."""

    payload = {
        "draft_id": DRAFT_ID,
        "kind": seat.get("kind"),
        "ticket": str(seat.get("ticket") or ""),
        "sleeve": seat.get("sleeve"),
        "symbol": seat.get("symbol"),
        "login": str(seat.get("login") or CHALLENGE_LOGIN),
        "ns": str(seat.get("ns") or CHALLENGE_NS),
        "place_apply": PLACE_APPLY,
        "place_ensemble": PLACE_ENSEMBLE,
    }
    digest = canonical_sha256(payload)
    refuse_incomplete_hash(digest)
    return digest


def load_deal_close_tape(path: Path | str | None = None) -> list[dict[str, Any]]:
    """Read committed Challenge deal_close rows. Empty if the tape is absent."""

    target = Path(path) if path is not None else DEFAULT_TAPE
    if not target.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("kind") != "deal_close":
            continue
        house = rec.get("house") or {}
        ident = ((rec.get("state") or {}).get("identity") or {})
        rows.append(
            {
                "ticket": str(rec.get("ticket") or ident.get("candidate_id") or ""),
                "sleeve": ident.get("sleeve") or rec.get("sleeve"),
                "symbol": ident.get("symbol"),
                "family_class": house.get("family_class"),
                "hard_off_family": house.get("hard_off_family"),
                "keep_family": bool(house.get("keep_family")),
                "leave_orig": bool(house.get("leave_orig")),
                "kind": "deal_close",
            }
        )
    return rows


def deal_close_board_seats(*, tape: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    """46 tape seats, identity-stable even if jsonl is missing."""

    by_ticket = {str(row.get("ticket")): dict(row) for row in (tape or [])}
    seats: list[dict[str, Any]] = []
    for ticket in DEAL_CLOSE_TAPE_TICKETS:
        row = by_ticket.get(ticket) or {"ticket": ticket, "kind": "deal_close"}
        seat = {
            "seat_id": _seat_id("deal_close", ticket),
            "kind": "deal_close",
            "ticket": ticket,
            "sleeve": row.get("sleeve"),
            "symbol": row.get("symbol"),
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "draft": "DIG_B_CLOSED_BOARD",
            "family_class": row.get("family_class")
            or family_class_for(str(row.get("sleeve") or ""), symbol=str(row.get("symbol") or "")),
            "keep_family": bool(row.get("keep_family")) or keep_family(str(row.get("sleeve") or "")),
            "hard_off_family": row.get("hard_off_family")
            or hard_off_family(str(row.get("sleeve") or ""), str(row.get("symbol") or "")),
            "leave_orig": bool(row.get("leave_orig")) or leave_orig_ticket(ticket),
        }
        seat["sha256"] = complete_draft_hash(seat)
        seats.append(seat)
    return seats


def remint_flatten_draft_seats() -> list[dict[str, Any]]:
    """14 Dig B remint/flatten drafts. Complete hash unless the seat is the incomplete probe."""

    seats: list[dict[str, Any]] = []
    for raw in DIG_B_REMINT_FLATTEN_DRAFTS:
        seat = {
            "login": raw.get("login", CHALLENGE_LOGIN),
            "ns": raw.get("ns", CHALLENGE_NS),
            **raw,
        }
        if seat.get("sha256") is None and seat.get("draft") != "INCOMPLETE_HASH":
            seat["sha256"] = complete_draft_hash(seat)
        seats.append(seat)
    return seats


def consume_board(*, tape: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The 60-seat board: 46 deal_close + 14 remint/flatten drafts."""

    tape_rows = list(tape) if tape is not None else load_deal_close_tape()
    seats = deal_close_board_seats(tape=tape_rows) + remint_flatten_draft_seats()
    if len(seats) != BOARD_SIZE:
        raise RuntimeError(f"consume board must be {BOARD_SIZE}, got {len(seats)}")
    return seats


def remint_flatten_choice(
    seat: Mapping[str, Any],
    *,
    invented_files: Iterable[str] = (),
) -> ConsumeDecision:
    """Choice path for remint / flatten / deal_close. LABEL or KILL. Never send."""

    kind = str(seat.get("kind") or seat.get("action") or "").strip().lower()
    ticket = None if seat.get("ticket") is None else str(seat.get("ticket")).strip()
    seat_id = str(seat.get("seat_id") or _seat_id(kind or "unknown", ticket or "none"))
    notes = [
        "apply_is_label_only",
        "place_apply_already_live",
        "place_ensemble_already_live",
        "pack1b_beaten_false",
        "challenge_only_operator",
    ]

    if kind in {"place", "order_send", "open_trade", "mint_token"}:
        raise JevPlacePathVeto(f"VETO PLACE_PATH: remint/flatten consume never {kind}")
    if kind in FORBIDDEN_AUTO_EFFECTS and kind not in CONSUME_KINDS:
        raise JevPlacePathVeto(f"VETO PLACE_PATH: remint/flatten consume never {kind}")

    try:
        refuse_invented_news_protocol(invented_files)
        refuse_invented_news_protocol(tuple(seat.get("invented_files") or ()))
    except Exception:
        return ConsumeDecision(
            seat_id=seat_id,
            kind=kind or "unknown",
            ticket=ticket,
            verdict=KILL,
            reason="news_protocol_invent_veto",
            apply=False,
            keep_ticket=keep_ticket(ticket, sleeve=seat.get("sleeve"), symbol=seat.get("symbol")),
            hash_complete=is_complete_sha256(seat.get("sha256")),
            chair_verb="VETO",
            notes=tuple(notes + ["news_invent_refused"]),
        )

    if kind not in CONSUME_KINDS:
        return ConsumeDecision(
            seat_id=seat_id,
            kind=kind or "unknown",
            ticket=ticket,
            verdict=KILL,
            reason="kind_not_remint_flatten_deal_close",
            apply=False,
            keep_ticket=False,
            hash_complete=is_complete_sha256(seat.get("sha256")),
            chair_verb="VETO",
            notes=tuple(notes),
        )

    # Choice hash wall is explicit â€” trust_seat also checks, but remint/flatten
    # must fail closed on the incomplete probe before any LABEL write.
    digest = seat.get("sha256") or seat.get("seat_sha256") or seat.get("draft_sha256")
    try:
        if kind in {"remint", "flatten"}:
            refuse_incomplete_hash(digest)
    except IncompleteHashError:
        return ConsumeDecision(
            seat_id=seat_id,
            kind=kind,
            ticket=ticket,
            verdict=KILL,
            reason="incomplete_sha256",
            apply=False,
            keep_ticket=keep_ticket(ticket, sleeve=seat.get("sleeve"), symbol=seat.get("symbol")),
            hash_complete=False,
            chair_verb="REFUSE",
            notes=tuple(notes + ["choice_refuses_incomplete_hash"]),
        )

    trust = trust_seat(seat, invented_files=invented_files)
    if not trust.get("trusted"):
        return ConsumeDecision(
            seat_id=seat_id,
            kind=kind,
            ticket=ticket,
            verdict=KILL,
            reason=str(trust.get("reason") or "not_trusted"),
            apply=False,
            keep_ticket=bool(trust.get("keep_ticket")),
            hash_complete=bool(trust.get("hash_complete")),
            chair_verb="KILL",
            notes=tuple(notes + ["place_seat_trust_kill"]),
        )

    if APPLY_EFFECT not in PREAUTH_EFFECTS:
        return ConsumeDecision(
            seat_id=seat_id,
            kind=kind,
            ticket=ticket,
            verdict=KILL,
            reason="label_not_preauthorized",
            apply=False,
            keep_ticket=True,
            hash_complete=True,
            chair_verb="KILL",
            notes=tuple(notes),
        )

    return ConsumeDecision(
        seat_id=seat_id,
        kind=kind,
        ticket=ticket,
        verdict=APPLY,
        reason="apply_candidate_keep_label",
        apply=True,
        keep_ticket=True,
        hash_complete=True,
        chair_verb="LABEL",
        notes=tuple(notes + ["apply_candidate_keep", "broker_mutation_false"]),
    )


def consume_seats(
    seats: Sequence[Mapping[str, Any]] | None = None,
    *,
    tape: Sequence[Mapping[str, Any]] | None = None,
) -> list[ConsumeDecision]:
    board = list(seats) if seats is not None else consume_board(tape=tape)
    return [remint_flatten_choice(seat) for seat in board]


def receipt_payload(
    decisions: Sequence[ConsumeDecision] | None = None,
    *,
    tape: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = list(decisions) if decisions is not None else consume_seats(tape=tape)
    apply_seats = [row.as_dict() for row in rows if row.verdict == APPLY]
    kill_seats = [row.as_dict() for row in rows if row.verdict != APPLY]
    return {
        "schema": SCHEMA,
        "draft_id": DRAFT_ID,
        "namespace": NAMESPACE,
        "logged_at_utc": _now_utc(),
        "account_surface": account_surface(),
        "board_size": len(rows),
        "board_size_required": BOARD_SIZE,
        "place_apply": PLACE_APPLY,
        "place_ensemble": PLACE_ENSEMBLE,
        "place_wires_live": list(PLACE_WIRES_LIVE),
        "pack1b_beaten": pack1b_beaten(),
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_broker_send": True,
        "broker_effect": False,
        "apply_is_label_only": True,
        "keep_trust_tickets": sorted(set(FIRE_1201_KEEP_WIN_TICKETS) | {REVIEW_KEEP_TICKET}),
        "review_offhours_ticket_not_remint_keep": REVIEW_OFFHOURS_TICKET,
        "n_apply": len(apply_seats),
        "n_kill": len(kill_seats),
        "apply_seats": apply_seats,
        "kill_seats": kill_seats,
        "apply_seat_ids": [row["seat_id"] for row in apply_seats],
        "kill_seat_ids": [row["seat_id"] for row in kill_seats],
        "deal_close_tape_n": len(DEAL_CLOSE_TAPE_TICKETS),
        "remint_flatten_draft_n": len(DIG_B_REMINT_FLATTEN_DRAFTS),
    }


def write_consume_receipt(
    path: Path | str | None = None,
    *,
    decisions: Sequence[ConsumeDecision] | None = None,
    tape: Sequence[Mapping[str, Any]] | None = None,
) -> Path:
    target = Path(path) if path is not None else DEFAULT_RECEIPT
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = receipt_payload(decisions, tape=tape)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def observe_book_owner_consume(
    *,
    namespace: Any,
    live_broker_authority: bool = False,
    now: Any = None,
    tape: Sequence[Mapping[str, Any]] | None = None,
    invented_files: Iterable[str] = (),
) -> dict[str, Any]:
    """book_owner observe hook. Challenge ns only. Never mutates.

    H8: ``live_broker_authority`` false still observes. This hook never
    calls close_position / order_send regardless of the flag.
    """

    refuse_invented_news_protocol(invented_files)
    ns = str(namespace or "").strip()
    absent = {
        "schema": SCHEMA,
        "draft_id": DRAFT_ID,
        "action": "PASS",
        "reason": "not_f5",
        "namespace": ns,
        "broker_effect": False,
        "never_broker_send": True,
        "pack1b_beaten": pack1b_beaten(),
        "live_broker_authority": bool(live_broker_authority),
        "h8_observe_only": not bool(live_broker_authority),
    }
    if ns != CHALLENGE_NS:
        return absent
    if is_redacted_account(ns=ns):
        return dict(absent, reason="redacted_account_forbidden")
    assert_challenge_payout_writer(CHALLENGE_LOGIN)
    if APPLY_EFFECT not in PREAUTH_EFFECTS:
        return dict(absent, reason="label_not_preauthorized")

    decisions = consume_seats(tape=tape)
    payload = receipt_payload(decisions, tape=tape)
    payload.update(
        {
            "action": "OBSERVE",
            "reason": "label_consume_observed",
            "namespace": ns,
            "live_broker_authority": bool(live_broker_authority),
            "h8_observe_only": not bool(live_broker_authority),
            "broker_mutation_allowed": False,
            "observed_at_utc": _now_utc()
            if now is None
            else (now.isoformat() if hasattr(now, "isoformat") else str(now)),
        }
    )
    try:
        from .unique_loader import observe_unique_apply

        payload["unique_apply"] = observe_unique_apply(namespace=ns)
    except Exception as exc:  # noqa: BLE001 — LABEL only; never take down consume
        payload["unique_apply_block"] = f"{type(exc).__name__}: {exc}"
    return payload

