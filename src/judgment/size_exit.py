"""Challenge size + manage/exit decisions through Jev.

Owner 2026-09-21: every trading-decision ``if`` on Challenge **0**
goes through Jev (Choice / Score / Noul). This module is the size /
manage / exit slice:

  * size (named tilt vs original unit)
  * move SL (BE) / trail
  * time stop
  * scale-out
  * flatten-from-governor

Gold walk 2026-09-21 (JEV_EVERYWHERE size+close seats + JEV_HISTORICAL):

  * Size IDs: ``persistence``, ``geometry_vs_tape``, ``session_fitness``,
    ``cost_hurtful``, ``conviction_vs_tape``, ``event_proximity``.
  * Close: ``exit_class`` lists ``time_stop``. The Choice is the noun.

An empty answer, a tie, or an error stays unset. It does not become leave-orig.
The writer prints.
Plumbing (``if path``, ``if err``, config parse, operator FLATTEN.flag,
weekend-flat compliance) stays code.

Does not invent a second MT5 client. W7 namespaces are untouched.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .apply_size import CHALLENGE_LOGIN, CHALLENGE_NS, is_challenge_account
from .compose import _jev_noul, _jev_score
from .jev_questions import SIZE_SEAT_IDS, hierarchical_labels, question_subtree

SCHEMA = "gtos.judgment.size_exit.v1"
STEAL = "SIZE_EXIT"
LEAVE_ORIG = "leave_orig"
NAMED_TILT = "named_tilt"
MOVE_BE = "move_be"
TRAIL = "trail"
TIME_STOP = "time_stop"
SCALE_OUT = "scale_out"
FLATTEN = "flatten"
ORIG_STOP = "orig_stop"
BROKER_TP = "broker_tp"
BREACH_FLATTEN = "breach_flatten"
UNLISTED_EXIT = "unlisted_exit"

_LOG = logging.getLogger("gtos.judgment.size_exit")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRINT = REPO_ROOT / "judgment" / "astra" / "lab" / "a1" / "size_exit_print.jsonl"

# Gold-walk size seat (JEV_EVERYWHERE §3). ac60_size is the already-wired alias
# of persistence (FLUID-SIZ-007). Nested under QUESTION_TREE["size"].
SIZE_IDS: tuple[str, ...] = SIZE_SEAT_IDS

EXIT_CLASS_CRITERIA = {
    ORIG_STOP: "Original broker stop.",
    BROKER_TP: "Broker target fill.",
    TIME_STOP: "Horizon / time-stop close. The option is this noun.",
    BREACH_FLATTEN: "Governor flatten named.",
    UNLISTED_EXIT: "The close noun is outside the named exits. Do not prefer this for a paying time-stop.",
}

SIZE_ACTION_CRITERIA = {
    LEAVE_ORIG: (
        "Keep the cash the last returned score named. "
        "Writer prints leave-orig and does not resize."
    ),
    NAMED_TILT: (
        "Named size change on this login's live equity. "
        "The cash number is the returned score. "
        "A pass line and a floor do not limit it."
    ),
}

MOVE_SL_CRITERIA = {
    LEAVE_ORIG: "Do not move SL or TP. Original broker protection stays.",
    MOVE_BE: "Move SL to break-even. Writer prints the SL modify.",
    TRAIL: "Trail the stop. Writer prints the SL modify.",
}

TIME_STOP_CRITERIA = {
    LEAVE_ORIG: "Do not time-stop. Original horizon / broker SL stays.",
    TIME_STOP: (
        "Close now as a time stop. The option you return is the close."
    ),
}

SCALE_CRITERIA = {
    LEAVE_ORIG: "Do not scale out. Full original size stays.",
    SCALE_OUT: "Take the sleeve partial. Writer prints the partial close.",
}

FLATTEN_GOV_CRITERIA = {
    LEAVE_ORIG: (
        "Do not flatten from the governor signal. Original positions stay. "
        "Operator FLATTEN.flag stays plumbing and still flattens."
    ),
    FLATTEN: "Governor flatten named. Writer prints flatten of book positions.",
}

SIZE_NAMED_LEVELS = (
    "leave the last returned cash",
    "a smaller cash than that returned score",
    "a larger cash than that returned score",
)


def _from_gold(*ids: str) -> dict[str, dict[str, Any]]:
    """Subtree dump of named gold IDs. Not a linear keep/drop of the catalog."""
    return question_subtree(*ids)


SIZE_OVERLAY: dict[str, dict[str, Any]] = {
    "size_action": {
        "type": "choice",
        "instructions": (
            "On this login's live equity, keep the last returned cash or name "
            "a change? The cash number is the returned score on size_cash. "
            "A pass line and a floor do not limit this. Never place."
        ),
        "criteria": dict(SIZE_ACTION_CRITERIA),
    },
    "size_named": {
        "type": "score",
        "instructions": (
            "How strongly does this tape name a size change versus leaving "
            "the last returned cash? You do not send. The number you return "
            "is the strength."
        ),
        "criteria": list(SIZE_NAMED_LEVELS),
    },
}

# Consume live size dump (9 IDs). Overlays are this hop only. Do not re-Noul
# completeness. Never a 57-key catalog.
SIZE_QUESTION_PACK: dict[str, dict[str, Any]] = {
    **question_subtree("size"),
    **SIZE_OVERLAY,
}
CLOSE_QUESTION_PACK: dict[str, dict[str, Any]] = {
    "manage_life": {
        "type": "choice",
        "instructions": (
            "This open ticket, this tick. Giveback is on the state when the "
            "peak favourable excursion and the excursion now are both known. "
            "That giveback is the case. Move the stop, scale out, close, or "
            "let it run. The option you return is the manage. "
            "An empty answer or a tie does not send."
        ),
        "criteria": {
            "move_sl": "Move the stop.",
            "scale_out": "Scale out.",
            "close": "Close this ticket.",
            "let_it_run": "Let this ticket run. Do not send.",
        },
    },
    "exit_class": {
        "type": "choice",
        "instructions": (
            "What noun is this exit on this open ticket? "
            "The option you return is the noun. "
            "An empty answer or a tie is not an exit. Do not send."
        ),
        "criteria": dict(EXIT_CLASS_CRITERIA),
    },
    "move_sl": {
        "type": "choice",
        "instructions": (
            "Should the writer move the stop on this open Challenge ticket? "
            "The option you return is the move. "
            "An empty answer or a tie is not a move."
        ),
        "criteria": dict(MOVE_SL_CRITERIA),
    },
    "time_stop": {
        "type": "choice",
        "instructions": (
            "Should the writer close this open Challenge ticket as a time stop? "
            "The option you return is the close. "
            "An empty answer or a tie is not a close."
        ),
        "criteria": dict(TIME_STOP_CRITERIA),
    },
    "scale_out": {
        "type": "choice",
        "instructions": (
            "Should the writer scale out this open Challenge ticket? "
            "The option you return is the scale. "
            "An empty answer or a tie is not a scale."
        ),
        "criteria": dict(SCALE_CRITERIA),
    },
    "flatten_governor": {
        "type": "choice",
        "instructions": (
            "Governor signalled a breach flatten. Should the writer flatten "
            "open Challenge positions? The option you return is the flatten. "
            "Operator FLATTEN.flag is not this question. "
            "An empty answer or a tie is not a flatten."
        ),
        "criteria": dict(FLATTEN_GOV_CRITERIA),
    },
}

QUESTION_PACK: dict[str, dict[str, Any]] = {**SIZE_QUESTION_PACK, **CLOSE_QUESTION_PACK}
QUESTION_IDS: tuple[str, ...] = tuple(QUESTION_PACK.keys())

_SIZE_SCORE_KEYS = (
    "persistence",
    "geometry_vs_tape",
    "session_fitness",
    "conviction_vs_tape",
    "ac60_size",
    "geo_size",
    "session_size",
    "flow_alignment",
    "level_size",
    "event_size",
    "combined_size",
    "size_named",
    "size_label",
)
_SIZE_NOUL_KEYS = ("cost_hurtful", "event_proximity")


def challenge_writer(*, login: Any = None, ns: Any = None) -> bool:
    """True on Challenge 0 / operator. W7 is false."""
    return is_challenge_account(login=login, ns=ns)


def _choice(answers: Mapping[str, Any] | None, key: str) -> str | None:
    """Unique highest probability on this question. A bare label is not a decision."""
    if not answers:
        return None
    block = answers.get(key)
    if not isinstance(block, dict):
        return None
    probs = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    from .jev_questions import unique_highest

    order = tuple(str(name) for name in probs) if isinstance(probs, dict) and probs else None
    return unique_highest(probs, order)


def _has_named_size_signal(answers: Mapping[str, Any] | None) -> bool:
    """A size change is the size_action Choice. A score is not a second decision."""
    if not answers:
        return False
    return _choice(answers, "size_action") == NAMED_TILT


def exit_class_lists_time_stop(pack: Mapping[str, Any] | None = None) -> bool:
    """Gold-walk close seat: exit_class criteria must list time_stop."""
    block = (pack or QUESTION_PACK).get("exit_class") or {}
    criteria = block.get("criteria") or {}
    return TIME_STOP in criteria


# Cash and persistence are the returns of this hop.
# A missing return stays missing.


def highest_probability(probabilities: Mapping[str, Any], order: tuple[str, ...]) -> str | None:
    """Unique argmax. A missing probability is not zero. A tie is not a decision."""
    from .jev_questions import unique_highest

    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    return unique_highest(probabilities, order)


def _logged_parameter(spot: str) -> float | None:
    """Latest returned number for this spot. A miss on that row stays missing."""
    try:
        from .jev_questions import last_logged_value
    except Exception:
        return None
    try:
        return _num(last_logged_value(spot))
    except Exception:
        return None


def size_persist_questions(state: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Function, branch, loop bound, and the catalog splice. One card.

    Cash and persistence are the unit_usd and persist_weight already returned
    on parameter_outcomes. This card does not ask those scores again.
    The loop bound and the splice are counts on this card. Fewer than two
    counts leaves that Score off the post.
    """
    from .jev_questions import amount_question, count_anchors, spot_question

    counts = count_anchors(state)
    return {
        **spot_question(
            "size_function",
            "Which function returns the already-returned cash and persistence on this state? "
            "The name you return is the function that runs. "
            "Do not name an amount.",
            {
                "returned_score": "Use the returned unit_usd and persist_weight.",
                "last_outcome": "Use the previous returned unit_usd and persist_weight.",
                "withhold": "Do not use the returned cash or weight.",
            },
        ),
        **spot_question(
            "size_if",
            "Does this state take the cash branch? "
            "The name you return is the branch.",
            {
                "take": "Take the branch. The returned unit_usd and persist_weight are the size.",
                "skip": "Do not take the branch. Cash and persistence stay unset.",
            },
        ),
        **amount_question(
            "size_loop",
            "How far does the learning loop read prior returned cash and persistence on this state? "
            "The score you return is that bound.",
            counts,
        ),
        **amount_question(
            "size_splice",
            "How many posted answers may sit on this state before the catalog is leftover? "
            "The score you return is that bound. "
            "An empty score does not discard the card.",
            counts,
        ),
    }


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _prior_outcomes_for_card(card: Mapping[str, Any]) -> Any:
    from .jev_questions import prior_outcomes

    return prior_outcomes(state=card, questions=size_persist_questions(card))


def _outcome_identity(raw: Mapping[str, Any], ticket: Any) -> tuple[Any, Any, Any]:
    """Broker ticket, symbol, and sleeve. A stand-in string is not a ticket.

    Never raises. A ticket that is not on the chair is not returned, so a
    failed chair read cannot keep a stand-in and cannot skip the later append.
    """
    symbol = None
    sleeve = None
    try:
        if isinstance(raw, Mapping):
            if raw.get("symbol") not in (None, ""):
                symbol = raw.get("symbol")
            if raw.get("sleeve") not in (None, ""):
                sleeve = raw.get("sleeve")
        ident = "" if ticket is None else str(ticket)
        if ident.startswith("W7_BOOK::"):
            parts = ident.split("::")
            if len(parts) >= 6:
                if symbol is None and parts[2]:
                    symbol = parts[2]
                if sleeve is None and parts[5]:
                    sleeve = parts[5]
            ticket = None
        try:
            from .unique_loader import _open_broker_positions

            found = _open_broker_positions()
        except Exception:
            return None, symbol, sleeve
        if not isinstance(found, list):
            return None, symbol, sleeve
        positions = [pos for pos in found if isinstance(pos, dict)]
        open_ids = {
            str(pos.get("ticket"))
            for pos in positions
            if pos.get("ticket") is not None
        }
        if ticket is not None and str(ticket) not in open_ids:
            ticket = None
        if ticket is None and symbol is not None:
            matches = [
                pos
                for pos in positions
                if str(pos.get("symbol") or "") == str(symbol)
            ]
            if len(matches) == 1 and matches[0].get("ticket") is not None:
                ticket = matches[0].get("ticket")
                if sleeve is None and matches[0].get("sleeve") not in (None, ""):
                    sleeve = matches[0].get("sleeve")
        if ticket is None and symbol is None and len(positions) == 1:
            only = positions[0]
            if only.get("ticket") is not None:
                ticket = only.get("ticket")
                if only.get("symbol") not in (None, ""):
                    symbol = only.get("symbol")
                if sleeve is None and only.get("sleeve") not in (None, ""):
                    sleeve = only.get("sleeve")
        if ticket is not None and str(ticket) not in {
            str(pos.get("ticket"))
            for pos in positions
            if pos.get("ticket") is not None
        }:
            ticket = None
        return ticket, symbol, sleeve
    except Exception:
        return None, symbol, sleeve


def money_facts(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Equity, balance, and tape fields already on the state. No invented cash."""
    raw = dict(state or {})
    account = raw.get("account") if isinstance(raw.get("account"), Mapping) else {}
    equity = _num(raw.get("equity"))
    if equity is None:
        equity = _num(account.get("equity"))
    balance = _num(raw.get("balance"))
    if balance is None:
        balance = _num(account.get("balance"))
    realized = _num(raw.get("realized_closed_profit"))
    if realized is None:
        realized = _num(account.get("realized_closed_profit"))
    day_net = _num(raw.get("day_net"))
    if day_net is None:
        day_net = _num(account.get("day_net"))
    open_pnl = _num(raw.get("open_pnl"))
    if open_pnl is None:
        open_pnl = _num(account.get("open_pnl"))
    if open_pnl is None and equity is not None and balance is not None:
        open_pnl = equity - balance
    ticket = raw.get("open_ticket")
    if ticket is None and isinstance(raw.get("open_gold"), Mapping):
        ticket = raw["open_gold"].get("ticket")
    if ticket is None:
        ticket = raw.get("ticket")
    try:
        ticket, symbol, sleeve = _outcome_identity(raw, ticket)
    except Exception:
        ticket, symbol, sleeve = None, None, None
    card: dict[str, Any] = {
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "equity": equity,
        "balance": balance,
        "realized_closed_profit": realized,
        "day_net": day_net,
        "open_pnl": open_pnl,
        "open_ticket": ticket,
    }
    if ticket is not None:
        card["ticket"] = ticket
    if symbol not in (None, ""):
        card["symbol"] = symbol
    if sleeve not in (None, ""):
        card["sleeve"] = sleeve
    for key in ("symbol", "sleeve", "time", "open", "high", "low", "close", "volume"):
        if card.get(key) not in (None, ""):
            continue
        if key in raw and raw.get(key) not in (None, ""):
            card[key] = raw.get(key)
    try:
        card["prior_outcomes"] = _prior_outcomes_for_card(card)
    except Exception:
        card["prior_outcomes"] = []
    return card


def _attach_live_card(state: Mapping[str, Any] | None) -> dict[str, Any]:
    base = dict(state or {})
    if _num(base.get("equity")) is not None or (
        isinstance(base.get("account"), Mapping) and _num(base["account"].get("equity")) is not None
    ):
        return base
    try:
        from .equity_frame import attach_account

        return attach_account(base)
    except Exception:
        return base


def _probs(block: Any) -> dict[str, float] | None:
    if not isinstance(block, dict):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, dict) or not raw:
        return None
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out or None


def _score_on(payload: Mapping[str, Any], key: str) -> float | None:
    """The score on this ask. A present empty score stays empty."""
    from .jev_questions import returned_number

    if key not in payload:
        return None
    try:
        return _num(returned_number(payload.get(key)))
    except Exception:
        return None


def _parameter_on(payload: Mapping[str, Any], asked: str, logged: str) -> tuple[float | None, bool]:
    """This ask's score, or the logged return when this ask did not post the spot.

    A key that is present and empty does not fall back to an older number.
    """
    if asked in payload:
        return _score_on(payload, asked), True
    return _logged_parameter(logged), False


def _row_from_answers(facts: Mapping[str, Any], answers: Mapping[str, Any]) -> dict[str, Any]:
    from .jev_questions import returned_number, unique_highest

    payload = answers if isinstance(answers, Mapping) else {}
    fn_block = payload.get("size_function")
    if_block = payload.get("size_if")
    loop_block = payload.get("size_loop")
    fn_probs = _probs(fn_block)
    if_probs = _probs(if_block)
    function_name = unique_highest(fn_probs)
    branch = unique_highest(if_probs)
    loop_bound = None
    try:
        loop_bound = _num(returned_number(loop_block))
    except Exception:
        loop_bound = None
    if "unit_usd" in payload:
        unit, asked_unit = _parameter_on(payload, "unit_usd", "unit_usd")
    elif "size_cash" in payload:
        unit, asked_unit = _parameter_on(payload, "size_cash", "unit_usd")
    else:
        unit, asked_unit = _logged_parameter("unit_usd"), False
    weight, asked_weight = _parameter_on(payload, "persist_weight", "persist_weight")
    splice = _score_on(payload, "size_splice") if "size_splice" in payload else None
    blocked = splice is not None and len(payload) >= splice
    size_action = _choice(payload, "size_action")
    decline = (
        blocked
        or function_name == "withhold"
        or branch == "skip"
        or size_action == LEAVE_ORIG
    )
    cash = None if decline else unit
    used_weight = None if decline else weight
    return {
        "schema": "gtos.judgment.size_persist_choice.v1",
        "facts": dict(facts),
        "size_function": function_name,
        "size_if": branch,
        "size_action": size_action,
        "loop_bound": loop_bound,
        "size_alternative": function_name if cash is not None else None,
        "persist_alternative": function_name if used_weight is not None else None,
        "cash_usd": cash,
        "persist_weight": used_weight,
        "returned_unit_usd": unit,
        "returned_weight": weight,
        "size_decided": cash is not None,
        "persist_decided": used_weight is not None,
        "asked_unit": asked_unit,
        "asked_persist": asked_weight,
        "asked_loop": "size_loop" in payload,
        "splice_bound": splice,
        "blocked": blocked,
        "size_probabilities": {},
        "persist_probabilities": {},
        "size_confidence": None,
        "persist_confidence": None,
        "model": "jev-1.13.0",
    }


def _remember(facts: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    """Remember this ask's own spots. Do not write a miss over unit_usd or persist_weight."""
    from .jev_questions import append_outcome

    logged = dict(facts)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    if row.get("asked_loop"):
        loop_bound = row.get("loop_bound")
        append_outcome(
            "size_loop",
            loop_bound,
            logged,
            error=None if loop_bound is not None else error,
        )
    if row.get("asked_unit"):
        unit = row.get("returned_unit_usd")
        append_outcome(
            "unit_usd",
            unit,
            logged,
            error=None if unit is not None else error,
        )
    if row.get("asked_persist"):
        weight = row.get("returned_weight")
        append_outcome(
            "persist_weight",
            weight,
            logged,
            error=None if weight is not None else error,
        )


def _post_size_persist(facts: Mapping[str, Any]) -> dict[str, Any]:
    """One existing hop. Empty answers stay empty. The old cash menu is not restored."""
    from .jev_client import evaluate
    from .jev_questions import MODEL

    row = _row_from_answers(facts, {})
    row["unanswered"] = True
    try:
        receipt = evaluate(
            dict(facts),
            questions=size_persist_questions(facts),
            model=MODEL,
            merge_sleeve=False,
        )
    except Exception as exc:
        row["error"] = type(exc).__name__
        _remember(facts, row)
        return row
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        receipt = receipt if isinstance(receipt, dict) else {}
        row["error"] = receipt.get("error") or receipt.get("skipped") or "post_failed"
        row["key_source"] = receipt.get("key_source")
        _remember(facts, row)
        return row
    packed = _row_from_answers(facts, receipt.get("answers") or {})
    packed["model"] = receipt.get("model") or MODEL
    packed["key_source"] = receipt.get("key_source")
    packed["unanswered"] = packed.get("cash_usd") is None and packed.get("size_function") is None
    if packed["unanswered"] and not packed.get("size_decided"):
        packed["error"] = packed.get("error") or "score_missing"
    _remember(facts, packed)
    return packed


def choose_size_and_persist(
    state: Mapping[str, Any] | None = None,
    *,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Size and persist for this card. The returns are the values. A miss stays unset."""
    try:
        facts = money_facts(_attach_live_card(state))
    except Exception:
        facts = {
            "login": CHALLENGE_LOGIN,
            "namespace": CHALLENGE_NS,
            "prior_outcomes": [],
        }
    if answers is not None:
        row = _row_from_answers(facts, answers)
        row["source"] = "answers_injected"
        _note_persist(row.get("persist_weight") if row.get("persist_decided") else None)
        _remember(facts, row)
        return row
    row = _post_size_persist(facts)
    row["source"] = "post"
    _note_persist(row.get("persist_weight") if row.get("persist_decided") else None)
    _write_choice_receipt(row)
    return row


def _note_persist(weight: float | None) -> None:
    try:
        from .gold_priors import note_persist_choice

        note_persist_choice(weight)
    except Exception:
        return


def _write_choice_receipt(row: Mapping[str, Any]) -> None:
    try:
        path = (
            REPO_ROOT
            / "pipeline_state"
            / "ultimate_book"
            / CHALLENGE_NS
            / "judgment"
            / "size_persist_choice.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(row)
        payload["at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        return


@dataclass(frozen=True)
class SizeDecision:
    action: str | None = None
    named_change: bool = False
    source: str = "unanswered"
    jev_ok: bool | None = None
    skipped: str | None = None
    cash_usd: float | None = None
    persist_weight: float | None = None
    size_alternative: str | None = None
    persist_alternative: str | None = None
    size_decided: bool = False
    persist_decided: bool = False
    size_function: str | None = None
    size_if: str | None = None
    loop_bound: float | None = None
    returned_unit_usd: float | None = None
    returned_persist_weight: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "steal": STEAL,
            "site": "size",
            "action": self.action,
            "choice": self.size_alternative or self.action,
            "named_change": self.named_change,
            "source": self.source,
            "jev_ok": self.jev_ok,
            "skipped": self.skipped,
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "size_ids": list(SIZE_IDS),
            "cash_unit_usd": self.cash_usd,
            "cash_usd": self.cash_usd,
            "unit_usd": self.returned_unit_usd,
            "persist_weight": self.persist_weight,
            "size_alternative": self.size_alternative,
            "persist_alternative": self.persist_alternative,
            "size_decided": self.size_decided,
            "persist_decided": self.persist_decided,
            "printed_unit_usd": self.returned_unit_usd,
            "printed_persist_weight": self.returned_persist_weight,
            "open_ticket_not_resized": None,
            "size_function": self.size_function,
            "size_if": self.size_if,
            "loop_bound": self.loop_bound,
        }


@dataclass(frozen=True)
class ManageDecision:
    move_sl: str | None = None
    time_stop: str | None = None
    scale_out: str | None = None
    flatten_governor: str | None = None
    exit_class: str | None = None
    source: str = "unanswered"
    jev_ok: bool | None = None
    skipped: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def move_be(self) -> bool:
        return self.move_sl == MOVE_BE

    @property
    def trail(self) -> bool:
        return self.move_sl == TRAIL

    @property
    def allow_time_stop(self) -> bool:
        return self.time_stop == TIME_STOP

    @property
    def allow_scale_out(self) -> bool:
        return self.scale_out == SCALE_OUT

    @property
    def allow_flatten(self) -> bool:
        return self.flatten_governor == FLATTEN

    @property
    def named_any(self) -> bool:
        return bool(
            self.move_be
            or self.trail
            or self.allow_time_stop
            or self.allow_scale_out
            or self.allow_flatten
        )

    def as_allow(self) -> dict[str, bool]:
        """Mask for ``check_and_manage_trade``. W7 passes None instead."""
        return {
            "move_be": self.move_be,
            "trail": self.trail,
            "scale_out": self.allow_scale_out,
        }

    def as_dict(self) -> dict[str, Any]:
        row = {
            "schema": SCHEMA,
            "steal": STEAL,
            "site": "manage_exit",
            "move_sl": self.move_sl,
            "time_stop": self.time_stop,
            "scale_out": self.scale_out,
            "flatten_governor": self.flatten_governor,
            "exit_class": self.exit_class,
            "named_any": self.named_any,
            "source": self.source,
            "jev_ok": self.jev_ok,
            "skipped": self.skipped,
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "allow": self.as_allow(),
        }
        if self.extra:
            row["extra"] = dict(self.extra)
        return row


def decide_size(
    answers: Mapping[str, Any] | None = None,
    *,
    ticket: Any = None,
    jev_ok: bool | None = None,
    skipped: str | None = None,
) -> SizeDecision:
    """The size Choice on these answers. An empty answer stays unanswered."""
    del ticket  # receipt context; leave-orig default is not ticket-locked here
    answers = answers or {}
    action = _choice(answers, "size_action")
    if action == LEAVE_ORIG:
        return SizeDecision(
            action=LEAVE_ORIG,
            named_change=False,
            source="jev_size_action",
            jev_ok=jev_ok,
            skipped=skipped,
        )
    if action == NAMED_TILT or _has_named_size_signal(answers):
        return SizeDecision(
            action=NAMED_TILT,
            named_change=True,
            source="jev_named" if action == NAMED_TILT else "jev_size_scores",
            jev_ok=jev_ok,
            skipped=skipped,
        )
    return SizeDecision(
        action="unanswered",
        named_change=False,
        source="not_decided",
        jev_ok=jev_ok,
        skipped=skipped,
        size_decided=False,
        persist_decided=False,
    )


def _named_or_orig(answers: Mapping[str, Any] | None, key: str, named: str) -> str | None:
    got = _choice(answers, key)
    if got == named:
        return named
    if key == "move_sl" and got in {MOVE_BE, TRAIL, "move_sl"}:
        return got
    if got:
        return got
    return None


def decide_manage(
    answers: Mapping[str, Any] | None = None,
    *,
    jev_ok: bool | None = None,
    skipped: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> ManageDecision:
    """Each manage field is that question's Choice. Empty and tie stay unset.

    ``manage_life`` is the one lifetime Choice: move the stop, scale out,
    close, or let it run. Giveback on the state is that case.
    ``exit_class=time_stop`` names the time-stop close.
    ``exit_class=breach_flatten`` names governor flatten.
    """
    answers = answers or {}
    source = "jev_choices" if answers else "not_decided"
    life = _choice(answers, "manage_life")
    exit_cls = _choice(answers, "exit_class")
    time_stop = _named_or_orig(answers, "time_stop", TIME_STOP)
    move_sl = _named_or_orig(answers, "move_sl", MOVE_BE)
    scale_out = _named_or_orig(answers, "scale_out", SCALE_OUT)
    flatten = _named_or_orig(answers, "flatten_governor", FLATTEN)
    if life == "let_it_run":
        return ManageDecision(
            source="let_it_run",
            jev_ok=jev_ok,
            skipped=skipped,
            extra=dict(extra or {}),
        )
    if life == "close":
        time_stop = TIME_STOP
        source = "manage_life"
    elif life == "scale_out":
        scale_out = SCALE_OUT
        source = "manage_life"
    elif life == "move_sl":
        move_sl = move_sl or "move_sl"
        source = "manage_life"
    if exit_cls == TIME_STOP:
        time_stop = TIME_STOP
        source = "jev_exit_class"
    if exit_cls == BREACH_FLATTEN:
        flatten = FLATTEN
        source = "jev_exit_class"
    return ManageDecision(
        move_sl=move_sl,
        time_stop=time_stop,
        scale_out=scale_out,
        flatten_governor=flatten,
        exit_class=exit_cls,
        source=source,
        jev_ok=jev_ok,
        skipped=skipped,
        extra=dict(extra or {}),
    )


def manage_state(
    *,
    symbol: Any = None,
    sleeve: Any = None,
    ticket: Any = None,
    occupancy: Mapping[str, Any] | None = None,
    governor: Mapping[str, Any] | None = None,
    record: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Closed state object for a manage/exit Choice. No invented NEWS."""
    trade: dict[str, Any] = {}
    if isinstance(record, Mapping):
        for key in (
            "ticket",
            "symbol",
            "sleeve",
            "entry_price",
            "stop_loss",
            "take_profit",
            "orig_sl",
            "orig_tp",
            "fav_r",
            "mfe_r",
            "progress_r",
            "open_r",
            "bars_held",
        ):
            if record.get(key) is not None:
                trade[key] = record.get(key)
    peak = _num(trade.get("mfe_r"))
    if peak is None:
        peak = _num(trade.get("fav_r"))
    now = _num(trade.get("progress_r"))
    if now is None:
        now = _num(trade.get("open_r"))
    if peak is not None and now is not None:
        trade["giveback"] = peak - now
    state = {
        "schema": SCHEMA,
        "identity": {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "symbol": symbol,
            "sleeve": sleeve,
            "ticket": ticket,
        },
        "occupancy": dict(occupancy or {}),
        "governor": dict(governor or {}),
        "trade": trade,
        "giveback": trade.get("giveback"),
        "gold_walk": {
            "exit_class_lists_time_stop": TIME_STOP in EXIT_CLASS_CRITERIA,
            "size_ids": list(SIZE_IDS),
        },
    }
    state["labels"] = hierarchical_labels(
        state,
        extra={"ticket": ticket, "subgoal": "manage_exit"},
    )
    if extra:
        state["extra"] = dict(extra)
    return state


def evaluate_size_exit(
    state: Mapping[str, Any] | None,
    *,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    questions: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (answers, receipt). Never raises. Dark Jev → empty answers."""
    if answers is not None:
        return dict(answers), {"ok": True, "skipped": "answers_injected", "answers": dict(answers)}
    if not evaluate_jev or state is None:
        return {}, {"ok": False, "skipped": "evaluate_jev_false", "answers": {}}
    pack = dict(questions) if questions is not None else QUESTION_PACK
    try:
        from .jev_client import evaluate

        if questions is SIZE_QUESTION_PACK or (
            isinstance(questions, Mapping)
            and "size_action" in questions
            and "exit_class" not in questions
        ):
            receipt = evaluate(
                dict(state),
                questions=size_persist_questions(state),
                merge_sleeve=False,
            ) or {}
        else:
            receipt = evaluate(dict(state), questions=pack, merge_sleeve=False) or {}
    except Exception as exc:  # noqa: BLE001 — writer path must never raise
        receipt = {"ok": False, "skipped": None, "error": type(exc).__name__, "answers": {}}
    packed = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    return dict(packed or {}), dict(receipt)


def decide_size_from_state(
    state: Mapping[str, Any] | None = None,
    *,
    answers: Mapping[str, Any] | None = None,
    ticket: Any = None,
    evaluate_jev: bool = True,
) -> SizeDecision:
    packed, receipt = evaluate_size_exit(
        state,
        evaluate_jev=evaluate_jev,
        answers=answers,
        questions=SIZE_QUESTION_PACK,
    )
    return decide_size(
        packed,
        ticket=ticket,
        jev_ok=receipt.get("ok"),
        skipped=receipt.get("skipped") or receipt.get("error"),
    )


def decide_size_exit(
    state: Mapping[str, Any] | None = None,
    *,
    answers: Mapping[str, Any] | None = None,
    ticket: Any = None,
    evaluate_jev: bool = True,
) -> SizeDecision:
    """Cash and persist for this card. A miss stays unset."""
    del ticket
    if not evaluate_jev and answers is None:
        return SizeDecision(
            action="unanswered",
            source="not_asked",
            size_decided=False,
            persist_decided=False,
        )
    row = choose_size_and_persist(state, answers=answers)
    size_alt = row.get("size_alternative")
    cash = row.get("cash_usd") if row.get("size_decided") else None
    action = size_alt or row.get("size_function")
    if action is None and cash is not None:
        action = "returned_score"
    if action is None:
        action = "unanswered"
    return SizeDecision(
        action=action,
        named_change=bool(row.get("size_decided") and cash is not None),
        source=str(row.get("source") or "size_persist_choice"),
        jev_ok=bool(row.get("size_function") and row.get("size_if")) or cash is not None,
        skipped=row.get("error"),
        cash_usd=cash,
        persist_weight=row.get("persist_weight") if row.get("persist_decided") else None,
        size_alternative=size_alt,
        persist_alternative=row.get("persist_alternative"),
        size_decided=bool(row.get("size_decided")),
        persist_decided=bool(row.get("persist_decided")),
        size_function=row.get("size_function"),
        size_if=row.get("size_if"),
        loop_bound=row.get("loop_bound"),
        returned_unit_usd=row.get("returned_unit_usd"),
        returned_persist_weight=row.get("returned_weight"),
    )


def decide_manage_from_state(
    state: Mapping[str, Any] | None = None,
    *,
    answers: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
) -> ManageDecision:
    packed, receipt = evaluate_size_exit(
        state,
        evaluate_jev=evaluate_jev,
        answers=answers,
        questions=CLOSE_QUESTION_PACK,
    )
    return decide_manage(
        packed,
        jev_ok=receipt.get("ok"),
        skipped=receipt.get("skipped") or receipt.get("error"),
        extra={"evaluate": {k: receipt.get(k) for k in ("ok", "skipped", "error") if k in receipt}},
    )


def jev_manage_allows(jev_allow: Mapping[str, Any] | None, action: str) -> bool:
    """An empty mask is not an allow."""
    if not isinstance(jev_allow, Mapping):
        return False
    return bool(jev_allow.get(action))


def _print_path() -> Path:
    raw = (os.environ.get("GTOS_JEV_SIZE_EXIT_PRINT") or "").strip()
    return Path(raw) if raw else DEFAULT_PRINT


def write_size_exit_print(row: Mapping[str, Any]) -> None:
    """Writer print. Best-effort JSONL. Never raises."""
    payload = dict(row)
    payload.setdefault("schema", SCHEMA)
    payload.setdefault("logged_at_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    try:
        path = _print_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        _LOG.debug("size_exit print failed", exc_info=True)
    try:
        _LOG.info(
            "writer print size_exit site=%s action=%s named=%s ticket=%s",
            payload.get("site"),
            payload.get("action") or payload.get("time_stop") or payload.get("move_sl"),
            payload.get("named_change") if "named_change" in payload else payload.get("named_any"),
            payload.get("ticket"),
        )
    except Exception:
        pass


CONVERTED_SITES: tuple[dict[str, str], ...] = (
    {
        "id": "SE-SIZE-001",
        "site": "src/judgment/apply_size.py:haircut_challenge_unit",
        "was": "compose_shadow local H4/spread_r picked size when Jev was dark",
        "now": (
            "The returned unit_usd and persist_weight are the size. "
            "An empty answer stays unset. Writer prints"
        ),
        "slice": "size",
        "consume": "persistence,geometry_vs_tape,session_fitness,cost_hurtful,conviction_vs_tape,event_proximity",
    },
    {
        "id": "SE-SIZE-002",
        "site": "src/judgment/apply_size.py:physical_apply_allowed",
        "was": "leave_orig_ticket 293332188 hard-blocked size even if Jev named a tilt",
        "now": "leave-orig default; jev_named_size lets a named tilt print",
        "slice": "size",
    },
    {
        "id": "SE-BE-001",
        "site": "src/components/execution.py:check_and_manage_trade move_be/trail",
        "was": "static TP1/trailing runner moved SL on Challenge",
        "now": "Jev move_sl Choice; default leave-orig; writer prints named BE/trail",
        "slice": "manage/exit",
    },
    {
        "id": "SE-TS-001",
        "site": "src/components/ultimate_book/book_owner.py:_manage_engine time_stop",
        "was": "static check_time_stop_and_close every tick",
        "now": (
            "Jev manage_life and time_stop Choice. An empty answer stays unset. "
            "Writer prints a named close."
        ),
        "slice": "close",
        "consume": "exit_class",
    },
    {
        "id": "SE-SCALE-001",
        "site": "src/components/execution.py:check_and_manage_trade TP1/TP2",
        "was": "static partial scale-out on TP1/TP2",
        "now": "Jev scale_out Choice; default leave-orig; writer prints named partial",
        "slice": "manage/exit",
    },
    {
        "id": "SE-FLAT-001",
        "site": "src/components/ultimate_book/book_owner.py:_apply_breach_flatten governor",
        "was": "static governor flatten after N-tick hysteresis",
        "now": (
            "Jev flatten_governor / exit_class=breach_flatten; default "
            "leave-orig; operator flag stays plumbing"
        ),
        "slice": "manage/exit",
    },
)
