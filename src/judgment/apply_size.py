"""Apply named live tilts to already-admitted Challenge size. Never refuse.

Physical mutation is env + Challenge-account gated:

  GTOS_JEV_APPLY_LIVE=1 AND (login 0 / ns operator)

F5 units size from ``risk_pct_per_trade`` (``_UnitView`` → router →
``risk_pct_override``). Haircut MUST scale that field (and ``unit_risk_pct``).
Host ``MinimalSizeScaler`` then asks the size hop. An empty answer
stays empty. Flow, cost, ca, and cash are the System One return for
this state. A miss stays unset. ``honor_f5_scaler_risk`` is that hop.
Lot keys are scaled when present. W7 armed books must not be resized.
Absence of login and namespace is not Challenge. Other books are not resized.
Flow, cost, and ca are the returned scores. A missing score stays unset.
Never places.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .compose import COST_TILT_MAX, COST_TILT_MIN, TILT_MAX, TILT_MIN, compose_shadow
from .host_events import as_of_from_state, coerce_as_of_utc, news_inventory_extra
from .process_lock import (
    CA_TILT_MAX,
    CA_TILT_MIN,
    WIRE_CA_SIZE,
    WIRE_COST,
    WIRE_FLOW,
    leave_orig_ticket,
    stamp_lock,
    wire_apply_open,
)

CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
MODEL = "jev-1.13.0"
_FUNCTION_ORDER = ("returned_score", "last_outcome", "withhold")
_BRANCH_ORDER = ("take", "skip")

# F5 live shape (host verdict B): router reads risk_pct_per_trade, not lots.
_RISK_KEYS = ("risk_pct_per_trade", "unit_risk_pct")
_LOT_KEYS = ("volume", "lots", "units", "size", "qty")
_INTENDED_KEYS = ("f5_intended_risk_usd", "intended_risk_usd", "risk_usd", "cash_risk_usd")
_SCALE_KEYS = _RISK_KEYS + _LOT_KEYS + _INTENDED_KEYS
_JEV_PASSTHROUGH = (
    "jev_combined_live_tilt",
    "jev_risk_pct_before",
    "jev_risk_pct_after",
    "f5_intended_risk_usd",
    "intended_risk_usd",
)

_LOG = logging.getLogger("gtos.judgment.apply_size")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT = REPO_ROOT / "judgment" / "astra" / "lab" / "a1" / "apply_receipt.jsonl"
_SECRET_TOKENS = ("api_key", "apikey", "authorization", "secret", "password")


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probabilities(raw: Any) -> dict[str, float]:
    block = raw if isinstance(raw, dict) else {}
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    numeric: dict[str, float] = {}
    if isinstance(probs_in, dict):
        for key, val in probs_in.items():
            number = _number(val)
            if number is not None:
                numeric[str(key)] = number
    return numeric


def _unique_name(raw: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A label without probabilities is not a decision."""

    numeric = _probabilities(raw)
    if not numeric:
        return None
    try:
        from .jev_questions import unique_highest
    except Exception:
        return None
    try:
        choice = unique_highest(numeric, order)
    except Exception:
        return None
    if choice is None or str(choice) not in order:
        return None
    return str(choice)


def _score_block(raw: Any) -> float | None:
    """The numeric score. A tie or a missing score stays empty. Levels are not substituted."""

    numeric = _probabilities(raw)
    if numeric:
        try:
            from .jev_questions import unique_highest

            picked = unique_highest(numeric, tuple(numeric))
        except Exception:
            return None
        if picked is None:
            return None
    block = raw if isinstance(raw, dict) else {}
    return _number(block.get("score"))


def _ordinal_block(raw: Any) -> int | None:
    """Nearest word level. The index is not dollars."""

    try:
        from .jev_questions import ordinal_index

        return ordinal_index(raw, 6)
    except Exception:
        return None


def _noul_value(raw: Any) -> bool | float | None:
    """A noul stays a bool or a probability. It is not coerced to a threshold."""

    block = raw if isinstance(raw, dict) else {}
    value = block.get("noul")
    if value is True or value is False:
        return value
    return _number(value)


def _last_logged(key: str) -> float | None:
    try:
        from .jev_questions import last_logged_value
    except Exception:
        return None
    try:
        return _number(last_logged_value(key))
    except Exception:
        return None


def _strip_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        kept: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key).lower().replace("-", "_")
            if any(token in name for token in _SECRET_TOKENS):
                continue
            kept[str(key)] = _strip_secrets(item)
        return kept
    if isinstance(value, list):
        return [_strip_secrets(item) for item in value]
    return value


def apply_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Tilt and cash card. One ask. Choice, score, and noul only.

    Cash and the splice bound are amounts on this card's own facts. A tilt
    has no amount unit here, so it is an ordinal and is not a dollar figure.
    """

    from .jev_questions import amount_question, count_anchors, ordinal_question, spot_question

    pack: dict[str, Any] = {}
    pack.update(spot_question(
        "apply_function",
        "Which function returns the flow tilt, the cost tilt, the ca tilt, and the cash on this state? "
        "The name you return is the function that runs. "
        "Do not name a number. Never place.",
        {
            "returned_score": (
                "The function is the score hop. Its return is the flow tilt, "
                "the cost tilt, the ca tilt, and the cash."
            ),
            "last_outcome": "The function reads the previous returned tilts and cash and returns those.",
            "withhold": "The function returns no tilt and no cash.",
        },
    ))
    pack.update(spot_question(
        "apply_if",
        "Does this state take the size branch? The name you return is the branch. Never place.",
        {
            "take": "Take the branch. The named function returns the tilts and the cash.",
            "skip": "Do not take the branch. The tilts and the cash stay unset.",
        },
    ))
    tilt_levels = (
        "none",
        "trace",
        "small",
        "modest",
        "notable",
        "heavy",
    )
    pack.update(ordinal_question(
        "apply_flow",
        "What flow tilt does this state return? "
        "The score you return is that tilt's place in the order. "
        "It is not an amount. It may sit between the levels. Never place.",
        tilt_levels,
    ))
    pack.update(ordinal_question(
        "apply_cost",
        "What cost tilt does this state return? "
        "The score you return is that tilt's place in the order. "
        "It is not an amount. It may sit between the levels. Never place.",
        tilt_levels,
    ))
    pack.update(ordinal_question(
        "apply_ca",
        "What ca tilt does this state return? "
        "The score you return is that tilt's place in the order. "
        "It is not an amount. It may sit between the levels. Never place.",
        tilt_levels,
    ))
    pack.update(amount_question(
        "apply_splice",
        "How many posted answers may sit on this state before the catalog is leftover? "
        "The score you return is that bound. Never place.",
        count_anchors(state),
    ))
    pack["cost_hurtful"] = {
        "type": "noul",
        "instructions": (
            "Is the cost on this already-admitted unit hurtful? "
            "The noul you return is that answer. Never place."
        ),
        "criteria": {
            "true": "The cost on this unit is hurtful.",
            "false": "The cost on this unit is not hurtful.",
        },
    }
    return pack


def _returned_unit(payload: Mapping[str, Any]) -> float | None:
    """unit_usd already returned for this state. A posted empty score stays empty."""

    if "apply_cash" in payload:
        return _score_block(payload.get("apply_cash"))
    if "unit_usd" in payload:
        return _score_block(payload.get("unit_usd"))
    return _last_logged("unit_usd")


def _applied_tilts(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Run the function and the branch. A skip, a tie, or a missing score leaves the numbers unset."""

    payload = answers if isinstance(answers, Mapping) else {}
    function_name = _unique_name(payload.get("apply_function"), _FUNCTION_ORDER)
    branch = _unique_name(payload.get("apply_if"), _BRANCH_ORDER)
    flow = cost = ca = cash = None
    if function_name == "withhold" or branch == "skip":
        pass
    elif function_name == "last_outcome" and branch == "take":
        flow = _ordinal_block({"score": _last_logged("apply_flow")})
        cost = _ordinal_block({"score": _last_logged("apply_cost")})
        ca = _ordinal_block({"score": _last_logged("apply_ca")})
        cash = _returned_unit(payload)
    elif function_name == "returned_score" and branch == "take":
        flow = _ordinal_block(payload.get("apply_flow"))
        cost = _ordinal_block(payload.get("apply_cost"))
        ca = _ordinal_block(payload.get("apply_ca"))
        cash = _returned_unit(payload)
    else:
        # Empty function or branch. Tilts stay unset. The returned unit still stands.
        cash = _returned_unit(payload)
    splice = _score_block(payload.get("apply_splice"))
    blocked = splice is not None and len(payload) >= splice
    if blocked:
        flow = cost = ca = cash = None
    return {
        "apply_function": function_name,
        "apply_if": branch,
        "flow": flow,
        "cost": cost,
        "ca": ca,
        "size_cash": cash,
        "splice_bound": splice,
        "blocked": blocked,
        "cost_hurtful": _noul_value(payload.get("cost_hurtful")),
    }


def _remember_apply(
    state: Mapping[str, Any],
    card: Mapping[str, Any],
    error: Any = None,
) -> None:
    """The returns just run are the next ask's history. A miss is stored as empty."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = _strip_secrets(dict(state))
    logged.pop("prior_outcomes", None)
    rows = (
        ("apply_flow", card.get("flow")),
        ("apply_cost", card.get("cost")),
        ("apply_ca", card.get("ca")),
    )
    for key, value in rows:
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else error,
            )
        except Exception:
            continue


def _apply_state(
    row: Mapping[str, Any] | None,
    *,
    ticket: Any = None,
    state: Mapping[str, Any] | None = None,
    symbol: Any = None,
    sleeve: Any = None,
    login: Any = None,
    ns: Any = None,
    unit: Any = None,
) -> dict[str, Any]:
    base = dict(state or {})
    facts = dict(row or {})
    for key in (
        "live_size_tilt",
        "live_cost_tilt",
        "live_ca_size_tilt",
        "jev_combined_live_tilt",
        "f5_intended_risk_usd",
        "intended_risk_usd",
    ):
        facts.pop(key, None)
    base["gate"] = "apply_size"
    base["model"] = MODEL
    if login is not None:
        base["login"] = login
    if ns is not None:
        base["namespace"] = ns
    if ticket is not None:
        base["ticket"] = ticket
    if symbol is not None:
        base["symbol"] = symbol
    if sleeve is not None:
        base["sleeve"] = sleeve
    identity = dict(base.get("identity") or {}) if isinstance(base.get("identity"), dict) else {}
    identity.setdefault("login", login)
    identity.setdefault("namespace", ns)
    identity.setdefault("ticket", ticket)
    identity.setdefault("symbol", symbol if symbol is not None else base.get("symbol"))
    identity.setdefault("sleeve", sleeve if sleeve is not None else base.get("sleeve"))
    base["identity"] = identity
    base["compose_facts"] = facts
    if unit is not None:
        snap = unit_size_snapshot(unit)
        snap.pop("f5_intended_risk_usd", None)
        snap.pop("intended_risk_usd", None)
        base["unit_before"] = snap
    base.setdefault(
        "clock",
        {"as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    )
    return base


def _ask_apply(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """One existing evaluate() call. Priors go in on this ask. No second client."""

    packed = _strip_secrets(dict(state or {}))
    packed.pop("prior_outcomes", None)
    packed["model"] = MODEL
    packed["gate"] = "apply_size"
    try:
        questions = apply_questions(packed)
    except Exception as exc:
        return {
            "ok": False,
            "source": "question_pack_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    try:
        from .equity_frame import attach_account

        attached = attach_account(packed)
        if isinstance(attached, dict):
            packed = attached
    except Exception:
        pass
    packed["model"] = MODEL
    packed["gate"] = "apply_size"
    try:
        from .jev_questions import hierarchical_labels

        packed["labels"] = hierarchical_labels(packed, extra={"subgoal": "apply_size"})
    except Exception:
        pass
    try:
        from .jev_questions import prior_outcomes

        packed["prior_outcomes"] = prior_outcomes(state=packed, questions=questions)
    except Exception:
        packed.setdefault("prior_outcomes", [])
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "jev_client_import_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    try:
        receipt = evaluate(
            packed,
            questions=questions,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "evaluate_raise",
            "error": type(exc).__name__,
            "answers": {},
            "state": packed,
        }
    if not isinstance(receipt, dict):
        receipt = {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "ok": bool(answers),
        "source": "apply_hop",
        "error": error,
        "answers": answers,
        "state": packed,
        "model": receipt.get("model") or MODEL,
    }


def apply_live_env() -> bool:
    return os.environ.get("GTOS_JEV_APPLY_LIVE", "").strip().lower() in {"1", "true", "yes"}


def is_challenge_account(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN
        except (TypeError, ValueError):
            login_ok = False
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def physical_apply_allowed(*, login: Any = None, ns: Any = None, ticket: Any = None) -> bool:
    if leave_orig_ticket(ticket):
        return False
    if not apply_live_env():
        return False
    return is_challenge_account(login=login, ns=ns)


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scaler_target_usd(
    scaler: Any,
    trade_params: dict[str, Any] | None,
    target_risk_usd: Any = None,
) -> float | None:
    got = _float_or_none(target_risk_usd)
    if got is not None:
        return got
    params = trade_params or {}
    details = params.get("gtos_vnext_source_event_details")
    symbol = params.get("symbol")
    sleeve = params.get("sleeve")
    if sleeve in (None, "") and isinstance(details, dict):
        sleeve = details.get("sleeve")
    if scaler is not None:
        fn = getattr(scaler, "risk_usd_for", None)
        if callable(fn):
            try:
                got = _float_or_none(fn(symbol, sleeve))
                if got is not None:
                    return got
            except Exception:
                pass
        got = _float_or_none(getattr(scaler, "target_risk_usd", None))
        if got is not None:
            return got
    return None


def f5_scaler_should_honor(
    *,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
    scaler: Any = None,
) -> bool:
    """Challenge APPLY only. Host scaler object is itself the F5 seam."""
    if leave_orig_ticket(ticket):
        return False
    if not apply_live_env():
        return False
    if ns is not None and str(ns).strip() != "" and not is_challenge_account(login=login, ns=ns):
        return False
    if login is not None and str(login).strip() != "" and not is_challenge_account(login=login, ns=ns):
        return False
    if physical_apply_allowed(login=login, ns=ns, ticket=ticket):
        return True
    return scaler is not None


def _positive_usd(value: Any) -> float | None:
    number = _float_or_none(value)
    if number is None or number <= 0 or number != number:
        return None
    if number in (float("inf"), float("-inf")):
        return None
    return number


def _percent_fraction(value: Any) -> float | None:
    """A ``*_pct`` fact is a percent: 5.0 is five percent, 0.5 is half a percent."""

    number = _positive_usd(value)
    if number is None:
        return None
    fraction = number / 100.0
    if fraction <= 0 or fraction >= 1.0:
        return None
    return fraction


def floor_room_usd(params: Mapping[str, Any] | None, equity: Any = None) -> float | None:
    """USD between this account's equity and its floor."""

    facts = params if isinstance(params, Mapping) else {}
    equity_n = _positive_usd(equity if equity is not None else facts.get("equity"))
    named = _positive_usd(facts.get("floor_room_usd"))
    if named is None:
        named = _positive_usd(facts.get("floor_room"))
    if named is not None and (equity_n is None or named < equity_n):
        return named
    floor = _positive_usd(facts.get("floor"))
    if floor is not None and equity_n is not None and equity_n > floor:
        return equity_n - floor
    initial = _positive_usd(facts.get("initial_balance"))
    overall = _positive_usd(facts.get("overall_loss_pct"))
    if initial is None or overall is None or equity_n is None:
        return None
    fraction = _percent_fraction(overall)
    if fraction is None:
        return None
    computed = initial * (1.0 - fraction)
    if equity_n <= computed:
        return None
    return equity_n - computed


def _day_baseline(facts: Mapping[str, Any]) -> float | None:
    named = _positive_usd(facts.get("day_start_equity_or_balance_baseline"))
    if named is not None:
        return named
    equity = _positive_usd(facts.get("day_start_equity"))
    balance = _positive_usd(facts.get("day_start_balance"))
    if equity is None or balance is None:
        return None
    return max(equity, balance)


def _remaining_loss_room(baseline: Any, equity: Any, percent: Any, initial: Any) -> float | None:
    """Room to the firm's daily floor: the day's start less the percent of the initial balance."""

    base = _positive_usd(baseline)
    equity_n = _positive_usd(equity)
    initial_n = _positive_usd(initial)
    fraction = _percent_fraction(percent)
    if base is None or equity_n is None or initial_n is None or fraction is None:
        return None
    room = equity_n - (base - initial_n * fraction)
    if room <= 0:
        return None
    return room


def daily_room_read(
    params: Mapping[str, Any] | None,
    equity: Any = None,
) -> tuple[float | None, str]:
    """Remaining USD under the firm's daily loss rule.

    A named USD room is that room. Otherwise the firm's daily percent of the
    initial balance is measured down from the higher of the day's starting
    equity and balance. One of those two, without the other, is not the
    higher, so the room stays unset. An internal overlay is not a rule of
    the account.
    """

    facts = params if isinstance(params, Mapping) else {}
    named = facts.get("daily_room_usd")
    if named not in (None, ""):
        number = _positive_usd(named)
        if number is None:
            return None, "unset"
        return number, "named"
    equity_n = equity if equity is not None else facts.get("equity")
    baseline = _day_baseline(facts)
    percent = facts.get("daily_percent_external")
    if percent in (None, "") or baseline is None:
        return None, "unset"
    room = _remaining_loss_room(baseline, equity_n, percent, facts.get("initial_balance"))
    if room is None:
        return None, "unset"
    return room, "firm_rule"


def open_risk_read(params: Mapping[str, Any] | None) -> tuple[float | None, str]:
    """Stop-risk already open, in USD. A flat book is zero. An unread book stays unset."""

    facts = params if isinstance(params, Mapping) else {}
    pending = facts.get("pending_orders_total")
    if pending not in (None, ""):
        try:
            pending_n = int(pending)
        except (TypeError, ValueError):
            return None, "unset"
        if pending_n > 0 and facts.get("open_risk_usd") in (None, ""):
            return None, "unset"
    if "open_risk_usd" in facts and facts.get("open_risk_usd") not in (None, ""):
        number = _float_or_none(facts.get("open_risk_usd"))
        if (
            number is None
            or number < 0
            or number != number
            or number in (float("inf"), float("-inf"))
        ):
            return None, "unset"
        return number, "named"
    positions = facts.get("positions_total")
    if positions in (None, ""):
        return None, "unset"
    try:
        count = int(positions)
    except (TypeError, ValueError):
        return None, "unset"
    if count == 0:
        return 0.0, "flat"
    return None, "unset"


def _nonnegative_usd_fact(facts: Mapping[str, Any], key: str) -> tuple[float | None, str]:
    """A named USD amount that may be zero.

    Absent means none. A present value that is not a finite amount leaves
    the room unset.
    """

    if key not in facts or facts.get(key) in (None, ""):
        return 0.0, "absent"
    number = _float_or_none(facts.get(key))
    if (
        number is None
        or number < 0
        or number != number
        or number in (float("inf"), float("-inf"))
    ):
        return None, "unset"
    return number, "named"


def _cycle_risk_usd(facts: Mapping[str, Any]) -> tuple[float | None, str]:
    """Cash already sized for other candidates this cycle."""

    return _nonnegative_usd_fact(facts, "cycle_risk_usd")


def binding_room_usd(
    params: Mapping[str, Any] | None,
    equity: Any = None,
) -> tuple[float | None, str]:
    """Smaller of the floor room and the daily room, net of open risk.

    An account whose owner declares no firm rules (``account_rules: none``)
    has no daily rule and its floor is zero, so its room is its own equity
    less the stop risk already open. An account that declares nothing still
    needs its rules read; missing rules leave the room unset.

    ``cycle_risk_usd``, when named, is cash this cycle has already sized.
    Open risk is the figure ``_size_room_facts`` already computed: every
    open position and every pending order. Pending stop risk is inside
    that figure, so this function does not read the book again and does
    not take it off a second time.
    Admission and the execution size hop both call this function.
    """

    facts = params if isinstance(params, Mapping) else {}
    equity_n = equity if equity is not None else facts.get("equity")
    open_risk, _risk_read = open_risk_read(facts)
    cycle, cycle_read = _cycle_risk_usd(facts)
    if cycle_read == "unset" or cycle is None:
        return None, "unset"
    taken = open_risk
    if taken is None:
        return None, "unset"
    taken = taken + cycle
    if no_firm_rules(facts):
        own = _positive_usd(equity_n)
        if own is None:
            return None, "unset"
        room = own - taken
        if room <= 0:
            return None, "empty"
        return room, "own_equity"
    floor_room = floor_room_usd(facts, equity_n)
    daily_room, _daily_read = daily_room_read(facts, equity_n)
    if floor_room is None or daily_room is None:
        return None, "unset"
    room = min(floor_room, daily_room) - taken
    if room <= 0:
        return None, "empty"
    return room, "bound"


CASH_CARRY: list[dict[str, Any]] = []


def currency_digits(facts: Mapping[str, Any] | None) -> int | None:
    """Digits of the account currency. A missing or non-integer fact stays missing."""

    if not isinstance(facts, Mapping):
        return None
    value = facts.get("currency_digits")
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    number = _number(value)
    if number is None or number < 0 or number != int(number):
        return None
    return int(number)


def money_exceeds(amount: Any, ceiling: Any, facts: Mapping[str, Any] | None = None) -> bool:
    """True when amount is above ceiling in the account currency.

    Both sides round to ``currency_digits`` when the account states that fact.
    A missing digit fact compares the two amounts exactly. A missing amount
    does not exceed.
    """

    left = _number(amount)
    right = _number(ceiling)
    if left is None or right is None:
        return False
    digits = currency_digits(facts)
    if digits is None:
        return left > right
    return round(left, digits) > round(right, digits)


ROOM_FACT_KEYS = (
    "equity",
    "balance",
    "positions_total",
    "open_risk_usd",
    "initial_balance",
    "overall_loss_pct",
    "daily_percent_external",
    "day_start_balance",
    "day_start_equity",
    "day_start_equity_or_balance_baseline",
    "account_rules",
    "floor_room_usd",
    "floor",
    "daily_room_usd",
    "pending_orders_total",
    "pending_stop_risk_usd",
    "currency_digits",
)


def read_binding_room_facts(mt5: Any, config: Mapping[str, Any] | None = None, namespace: str | None = None) -> dict[str, Any]:
    """Facts for ``binding_room_usd``, from ``ExecutionEngine._size_room_facts``.

    That read already counts pending orders inside open risk. This function
    does not read positions or orders again.
    """

    from src.components.execution import ExecutionEngine

    engine = object.__new__(ExecutionEngine)
    engine.mt5 = mt5
    engine.config = dict(config) if isinstance(config, Mapping) else {}
    engine._runtime_namespace = namespace
    try:
        facts = engine._size_room_facts(0.0)
    except Exception:
        return {}
    if not isinstance(facts, Mapping):
        return {}
    return dict(facts)


def no_firm_rules(facts: Mapping[str, Any] | None) -> bool:
    """True only when the account's owner declared that no firm's rules apply."""

    if not isinstance(facts, Mapping):
        return False
    value = facts.get("account_rules")
    return isinstance(value, str) and value.strip().lower() in {"none", "no_firm", "own"}


def cash_anchor_levels(
    params: Mapping[str, Any] | None,
    *,
    target: Any = None,
    equity: Any = None,
) -> list[tuple[str, float]]:
    """Cash levels in USD. Each level sits inside the binding room.

    Equity, balance, day-start, and margin are account scale. They are not
    levels of this cash.
    """

    facts = params if isinstance(params, Mapping) else {}
    room, _read = binding_room_usd(facts, equity if equity is not None else facts.get("equity"))
    if room is None or room <= 0:
        return []
    open_risk, _risk_read = open_risk_read(facts)
    floor = floor_room_usd(facts, equity if equity is not None else facts.get("equity"))
    daily, _daily_read = daily_room_read(facts, equity if equity is not None else facts.get("equity"))
    share: dict = {}
    try:
        from src.components.ultimate_book.admission import cycle_share_facts

        share = cycle_share_facts()
    except Exception:
        share = {}
    pairs: list[tuple[str, float]] = []
    min_lot = _positive_usd(facts.get("min_lot_risk_usd"))
    if min_lot is None:
        by_symbol = share.get("min_lot_usd") if isinstance(share, dict) else None
        symbol = facts.get("symbol")
        if isinstance(by_symbol, dict) and symbol not in (None, ""):
            min_lot = _positive_usd(by_symbol.get(str(symbol)))
    if min_lot is not None and min_lot <= room:
        pairs.append(("the minimum lot's risk at this stop, in USD", min_lot))
    launcher = _positive_usd(target)
    if launcher is None and isinstance(share, dict):
        launcher = _positive_usd(share.get("launcher_usd"))
    if launcher is not None and launcher <= room:
        pairs.append(("the launcher cash, in USD", launcher))
    trades = facts.get("cycle_candidate_trades")
    if not isinstance(trades, int) or isinstance(trades, bool):
        trades = share.get("n") if isinstance(share, dict) else None
    if isinstance(trades, int) and not isinstance(trades, bool) and trades > 0:
        per_candidate = room / float(trades)
        if per_candidate <= room:
            pairs.append(("the room per candidate this cycle, in USD", per_candidate))
    if open_risk is not None and daily is not None:
        daily_left = daily - open_risk
        if daily_left > 0 and daily_left <= room + 1e-6:
            pairs.append(("the daily room, in USD", daily_left if daily_left <= room else room))
    if open_risk is not None and floor is not None:
        floor_left = floor - open_risk
        if floor_left > 0 and floor_left <= room + 1e-6:
            pairs.append(("the room to the floor, in USD", floor_left if floor_left <= room else room))
    if not pairs or max(value for _label, value in pairs) < room - 1e-6:
        pairs.append(("the binding room, in USD", room))
    kept: list[tuple[str, float]] = []
    seen: list[float] = []
    for label, number in pairs:
        if number in seen:
            continue
        seen.append(number)
        kept.append((label, number))
    kept.sort(key=lambda pair: pair[1])
    return kept


def _cash_inside_room(cash: Any, room: Any) -> bool:
    number = _positive_usd(cash)
    ceiling = _positive_usd(room)
    if number is None or ceiling is None:
        return False
    return number <= ceiling


def _score_cash(state: Mapping[str, Any], anchors: list[tuple[str, float]]) -> float | None:
    """One cash score on these levels. Fewer than two levels does not post."""

    if len(anchors) < 2:
        return None
    ceiling = max(value for _label, value in anchors)
    try:
        from .nineteen import score
    except Exception:
        return None
    try:
        number = score(
            dict(state),
            question_id="unit_usd",
            instructions=(
                "The score you return is this unit's cash in USD. "
                "It may sit between the levels. "
                "An empty score leaves the cash unset. Do not send."
            ),
            anchors=anchors,
        )
    except Exception:
        return None
    if not _cash_inside_room(number, ceiling):
        return None
    return _positive_usd(number)


def honor_f5_scaler_risk(
    nominal: Any,
    *,
    scaler: Any = None,
    trade_params: dict[str, Any] | None = None,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
    target_risk_usd: Any = None,
) -> tuple[float | None, dict[str, Any]]:
    """Map the size hop onto the next unit. Never places.

    The cash is the returned parameter. An empty answer stays empty.
    A returned cash above the binding room is not the cash. The binding
    room is the smaller of the room to the floor and the daily room, net
    of open risk. Equity-scale anchors are not levels of this cash.
    """
    params = trade_params if isinstance(trade_params, dict) else {}
    nominal_f = _float_or_none(nominal)
    target = _scaler_target_usd(scaler, params, target_risk_usd)
    tilt = _float_or_none(params.get("jev_combined_live_tilt"))
    if ticket is None:
        ticket = params.get("ticket") or params.get("candidate_id")
    if ns is None:
        ns = params.get("namespace") or params.get("profile_namespace")
    honored = target
    used = "scaler_target" if target is not None else "size_not_decided"
    choice_row: dict[str, Any] | None = None
    floor_room = floor_room_usd(params, params.get("equity"))
    daily_room, daily_read = daily_room_read(params, params.get("equity"))
    open_risk, risk_read = open_risk_read(params)
    binding_room, binding_read = binding_room_usd(params, params.get("equity"))
    anchors = cash_anchor_levels(params, target=target, equity=params.get("equity"))
    carried = _positive_usd(params.get("allocation_cash_usd"))
    rounded = None
    if is_challenge_account(login=login, ns=ns) and carried is not None:
        # The cycle allocation already decided this cash. Do not ask again.
        # The lot rounds up to volume_min when the cash is below that risk,
        # and that rounded risk is what the room has to hold.
        rounded = carried
        lot_risk = _positive_usd(params.get("min_lot_risk_usd"))
        if lot_risk is not None and money_exceeds(lot_risk, carried, params):
            rounded = lot_risk
        if binding_room is None or money_exceeds(rounded, binding_room, params):
            honored = None
            used = "size_not_decided" if binding_room is None else "allocation_above_room"
        else:
            honored = carried
            used = "allocation_cash"
        choice_row = {
            "size_decided": honored is not None,
            "cash_usd": honored,
            "returned_unit_usd": honored,
        }
    elif is_challenge_account(login=login, ns=ns):
        # The next unit's cash is the returned parameter. A miss stays unset.
        # The payload keys are the ones this hop already posts.
        # No room means no cash, and the hop is not asked.
        # This ask is the path the cycle allocation did not cover.
        # A Challenge limit fill carries allocation_cash_usd on the pending
        # record and does not reach this ask.
        if binding_room is None:
            honored = None
            used = "size_not_decided"
        else:
            try:
                from .size_exit import choose_size_and_persist

                choice_row = choose_size_and_persist(
                    {
                        "login": login,
                        "namespace": ns,
                        "open_ticket": ticket,
                        "launcher_f5_minimal_size_usd": target,
                        "launcher_notional_initial_usd": getattr(
                            getattr(scaler, "_cfg", None), "notional_initial_usd", None
                        ),
                    }
                )
            except Exception as exc:  # noqa: BLE001 — a miss stays unset
                choice_row = {"size_decided": False, "error": type(exc).__name__}
            if not isinstance(choice_row, dict):
                choice_row = {"size_decided": False}
            cash = choice_row.get("cash_usd")
            if choice_row.get("size_decided") and _cash_inside_room(cash, binding_room):
                honored = float(cash)
                used = "size_choice"
            elif choice_row.get("size_decided"):
                scored = _score_cash(
                    {
                        "login": login,
                        "namespace": ns,
                        "equity": params.get("equity"),
                        "floor_room_usd": floor_room,
                        "daily_room_usd": daily_room,
                        "open_risk_usd": open_risk,
                        "binding_room_usd": binding_room,
                    },
                    anchors,
                )
                if scored is None:
                    honored = None
                    used = "size_not_decided"
                else:
                    honored = scored
                    used = "size_cash_anchors"
            else:
                honored = None
                used = "size_not_decided"
    elif f5_scaler_should_honor(login=login, ns=ns, ticket=ticket, scaler=scaler):
        if tilt is not None and target is not None:
            honored = target * tilt
            used = "target_times_tilt"
        elif tilt is None and nominal_f is not None and nominal_f > 0:
            honored = nominal_f
            used = "haircutted_nominal"
        else:
            honored = None
            used = "size_not_decided"
    stamp = {
        "f5_nominal_risk_usd": _float_or_none(nominal_f),
        "f5_intended_risk_usd": _float_or_none(honored),
        "intended_risk_usd": _float_or_none(honored),
        "jev_combined_live_tilt": tilt,
        "f5_scaler_honor": used,
        "floor_room_usd": floor_room,
        "daily_room_usd": daily_room,
        "daily_room_read": daily_read,
        "open_risk_usd": open_risk,
        "open_risk_read": risk_read,
        "binding_room_usd": binding_room,
        "binding_room_read": binding_read,
        "cash_anchors": [{"label": label, "usd": value} for label, value in anchors],
        "size_alternative": None if choice_row is None else choice_row.get("size_alternative"),
        "size_function": None if choice_row is None else choice_row.get("size_function"),
        "size_if": None if choice_row is None else choice_row.get("size_if"),
        "loop_bound": None if choice_row is None else choice_row.get("loop_bound"),
        "persist_weight": None if choice_row is None else choice_row.get("returned_weight"),
        "unit_usd": None if choice_row is None else choice_row.get("returned_unit_usd"),
        "printed_unit_usd": None if choice_row is None else choice_row.get("returned_unit_usd"),
        "printed_persist_weight": None if choice_row is None else choice_row.get("returned_weight"),
        "size_decided": False if choice_row is None else bool(choice_row.get("size_decided")),
        "persist_decided": False if choice_row is None else bool(choice_row.get("persist_decided")),
        "allocation_cash_usd": carried,
        "rounded_risk_usd": rounded,
        "pending_stop_risk_usd": params.get("pending_stop_risk_usd"),
        "symbol": params.get("symbol"),
    }
    if carried is not None:
        CASH_CARRY.append({
            "symbol": params.get("symbol"),
            "sleeve": params.get("sleeve") or params.get("tag"),
            "allocation_cash_usd": carried,
            "rounded_risk_usd": rounded,
            "binding_room_usd": binding_room,
            "open_risk_usd": open_risk,
            "pending_stop_risk_usd": params.get("pending_stop_risk_usd"),
            "f5_scaler_honor": used,
            "final_check": (
                "refused"
                if honored is None
                else "inside_room"
            ),
        })
    if scaler is not None:
        try:
            scaler.last = dict(stamp)
        except Exception:
            pass
    if honored is None:
        return None, stamp
    return float(honored), stamp


def apply_f5_scaler_to_risk_amount(
    risk_amount: Any,
    *,
    engine: Any = None,
    trade_params: dict[str, Any] | None = None,
    scaler: Any = None,
    login: Any = None,
    ns: Any = None,
    ticket: Any = None,
) -> float:
    """open_trade hook. No-op when the host F5 scaler is absent (W7)."""
    if scaler is None and engine is not None:
        scaler = getattr(engine, "_f5_scaler", None)
    if scaler is None:
        return float(risk_amount)
    params = trade_params if isinstance(trade_params, dict) else {}
    if login is None and engine is not None:
        mt5 = getattr(engine, "mt5", None)
        if mt5 is not None:
            fn = getattr(mt5, "get_account_login", None)
            if callable(fn):
                try:
                    login = fn()
                except Exception:
                    login = None
            if login is None:
                info = getattr(mt5, "account_info", None)
                if callable(info):
                    try:
                        login = getattr(info(), "login", None)
                    except Exception:
                        login = None
    if ns is None and engine is not None:
        ns = getattr(engine, "_runtime_namespace", None)
    honored, stamp = honor_f5_scaler_risk(
        risk_amount,
        scaler=scaler,
        trade_params=params,
        login=login,
        ns=ns,
        ticket=ticket,
    )
    if isinstance(trade_params, dict):
        trade_params.update(stamp)
    return honored


class MinimalSizeScaler:
    """Host-compatible F5 dollar scaler that honors a Challenge haircut.

    Chair: copy ``scaled_risk_amount`` into the dirty-host class. Do not
    wholesale-replace host ``execution.py`` / scaler if ``risk_usd_for``
    has CLI/cfg sleeves. Never places.
    """

    def __init__(
        self,
        target_risk_usd: float | None = None,
        *,
        login: Any = None,
        ns: Any = None,
    ) -> None:
        self.target_risk_usd = None if target_risk_usd is None else float(target_risk_usd)
        self.login = login
        self.ns = ns
        self.last: dict[str, Any] = {}

    def risk_usd_for(self, symbol: Any = None, sleeve: Any = None) -> float | None:
        if self.target_risk_usd is None:
            return None
        return float(self.target_risk_usd)

    def scaled_risk_amount(self, nominal: Any, trade_params: dict[str, Any] | None = None) -> float | None:
        honored, _stamp = honor_f5_scaler_risk(
            nominal,
            scaler=self,
            trade_params=trade_params,
            login=self.login,
            ns=self.ns,
        )
        return honored


def _clamp_open(number: float | None, lo: float, hi: float, *, open_wire: bool) -> tuple[float | None, bool]:
    """The returned score. Bounds and a closed wire do not clip it or invent one."""

    del lo, hi, open_wire
    if number is None:
        return None, True
    return float(number), False


def apply_named_tilts(
    compose_row: dict[str, Any] | None,
    *,
    ticket: Any = None,
    leave_orig: bool | None = None,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    symbol: Any = None,
    sleeve: Any = None,
    login: Any = None,
    ns: Any = None,
    unit: Any = None,
) -> dict[str, Any]:
    """Judgment receipt. Does not mutate a broker unit.

    On Challenge the ask runs. Leave-orig, a shadow sleeve, and a closed wire
    are facts on that ask. The returned scores are the tilts. An empty answer
    does not become an identity.
    """

    row = dict(compose_row or {})
    ticket = ticket if ticket is not None else row.get("leave_orig_ticket")
    if leave_orig is None:
        leave_orig = bool(row.get("leave_orig")) or leave_orig_ticket(ticket)
    from .aplus_sleeve import is_aplus_shadow_only

    aplus_shadow = is_aplus_shadow_only(compose_row, compose_row=row, sleeve=row.get("sleeve"))
    named_apply_symbol = row.get("named_apply_symbol")
    apply_flow = wire_apply_open(WIRE_FLOW, ticket=ticket)
    apply_cost = wire_apply_open(WIRE_COST, ticket=ticket)
    apply_ca = wire_apply_open(WIRE_CA_SIZE, ticket=ticket)
    challenge = is_challenge_account(login=login, ns=ns)
    row["leave_orig"] = bool(leave_orig)
    row["aplus_shadow"] = bool(aplus_shadow)
    row["named_apply_symbol"] = named_apply_symbol
    row["wire_flow_open"] = bool(apply_flow)
    row["wire_cost_open"] = bool(apply_cost)
    row["wire_ca_open"] = bool(apply_ca)
    need = challenge or bool(apply_flow or apply_cost or apply_ca)
    if not challenge and (named_apply_symbol is False or aplus_shadow or leave_orig):
        need = False
    card: dict[str, Any] = {
        "apply_function": None,
        "apply_if": None,
        "flow": None,
        "cost": None,
        "ca": None,
        "size_cash": None,
        "splice_bound": None,
        "blocked": False,
        "cost_hurtful": None,
    }
    if need and answers is None and evaluate_jev:
        ask_state = _apply_state(
            row,
            ticket=ticket,
            state=state,
            symbol=symbol,
            sleeve=sleeve,
            login=login,
            ns=ns,
            unit=unit,
        )
        asked = _ask_apply(ask_state)
        answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
        card = _applied_tilts(answers)
        _remember_apply(asked.get("state") or ask_state, card, error=asked.get("error"))
    elif need:
        card = _applied_tilts(answers)
        if answers is not None:
            _remember_apply(
                dict(state or {}),
                card,
                error=None if card.get("apply_function") else "empty",
            )
    flow, flow_missing = _clamp_open(card.get("flow"), TILT_MIN, TILT_MAX, open_wire=apply_flow)
    cost, cost_missing = _clamp_open(
        card.get("cost"), COST_TILT_MIN, COST_TILT_MAX, open_wire=apply_cost,
    )
    ca, ca_missing = _clamp_open(card.get("ca"), CA_TILT_MIN, CA_TILT_MAX, open_wire=apply_ca)
    size_cash = card.get("size_cash")
    # The tilt is an ordinal place. It is not a size and not dollars.
    combined: float | None = None
    del flow_missing, cost_missing, ca_missing
    return {
        **stamp_lock(),
        "ticket": ticket,
        "leave_orig": bool(leave_orig),
        "flow": flow,
        "cost": cost,
        "ca": ca,
        "combined": combined,
        "size_cash": size_cash,
        "apply_function": card.get("apply_function"),
        "apply_if": card.get("apply_if"),
        "cost_hurtful": card.get("cost_hurtful"),
        "splice_bound": card.get("splice_bound"),
        "blocked": bool(card.get("blocked")),
        "model": MODEL,
        "ca_apply": bool(apply_ca),
        "ca_live": ca,
        "ca_ignored": not apply_ca,
        "apply_this_row": need,
        "cannot_refuse": True,
        "physical_size_stays_flow_x_cost": False,
        "physical_size_stays_flow_x_cost_x_ca": False,
        WIRE_CA_SIZE: {"apply": apply_ca, "live": ca},
    }


def unit_size_snapshot(unit: Any) -> dict[str, Any]:
    """Non-secret size fields only. Used for apply receipts."""
    snap: dict[str, Any] = {}
    for key in _SCALE_KEYS:
        if isinstance(unit, dict) and key in unit and unit[key] is not None:
            snap[key] = unit[key]
        elif not isinstance(unit, dict) and hasattr(unit, key):
            value = getattr(unit, key)
            if value is not None:
                snap[key] = value
    if isinstance(unit, (int, float)) and not isinstance(unit, bool):
        snap["scalar"] = unit
    return snap


def _scale_number(value: Any, mult: float) -> Any:
    try:
        number = float(value) * mult
    except (TypeError, ValueError):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) >= 1 and abs(number) >= 1:
            return int(round(number)) if abs(number - round(number)) < 1e-9 else number
        return number
    return number


def _scale_unit(unit: Any, mult: float) -> Any:
    if isinstance(unit, bool):
        return unit
    if isinstance(unit, int):
        scaled = unit * mult
        if isinstance(scaled, float) and abs(scaled - round(scaled)) < 1e-9:
            return int(round(scaled))
        return scaled
    if isinstance(unit, float):
        return unit * mult
    if isinstance(unit, dict):
        out = dict(unit)
        for key in _SCALE_KEYS:
            if key in out and out[key] is not None:
                out[key] = _scale_number(out[key], mult)
        return out
    for attr in _SCALE_KEYS:
        if hasattr(unit, attr):
            try:
                setattr(unit, attr, _scale_number(getattr(unit, attr), mult))
            except Exception:
                pass
    return unit


def _receipt_path() -> Path:
    override = (os.environ.get("GTOS_JEV_APPLY_RECEIPT_PATH") or "").strip()
    return Path(override) if override else DEFAULT_RECEIPT


def write_apply_receipt(row: dict[str, Any]) -> None:
    """One-line apply receipt. No secrets. Safe if disk is missing."""
    _LOG.info(
        "JEV_APPLY receipt symbol=%s sleeve=%s ticket=%s tilt=%s before=%s after=%s",
        row.get("symbol"),
        row.get("sleeve"),
        row.get("ticket"),
        row.get("combined_live_tilt"),
        row.get("unit_before"),
        row.get("unit_after"),
    )
    try:
        path = _receipt_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, default=str) + "\n")
    except Exception:
        return


def maybe_haircut_unit(
    unit: Any,
    compose_row: dict[str, Any] | None = None,
    *,
    ticket: Any = None,
    login: Any = None,
    ns: Any = None,
    already_admitted: bool = True,
    symbol: Any = None,
    sleeve: Any = None,
    answers: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    state: Mapping[str, Any] | None = None,
) -> Any:
    """Physical hook. Challenge asks. Other books are returned unchanged."""
    if not is_challenge_account(login=login, ns=ns):
        return unit
    if symbol is None and isinstance(unit, dict):
        symbol = unit.get("symbol")
    row = dict(compose_row or {})
    row["already_admitted"] = bool(already_admitted)
    named = apply_named_tilts(
        row,
        ticket=ticket,
        answers=answers,
        state=state,
        evaluate_jev=evaluate_jev,
        symbol=symbol,
        sleeve=sleeve,
        login=login,
        ns=ns,
        unit=unit,
    )
    if not named["apply_this_row"]:
        return unit
    cash = named.get("size_cash")
    combined = named.get("combined")
    if combined is None and cash is None:
        return unit
    if symbol is None and isinstance(unit, dict):
        symbol = unit.get("symbol")
    if sleeve is None and isinstance(unit, dict):
        sleeve = unit.get("sleeve") or unit.get("cluster")
        members = unit.get("sleeve_members")
        if sleeve in (None, "", "book") and isinstance(members, (list, tuple)) and members:
            sleeve = members[0]
    before = unit_size_snapshot(unit)
    if combined is None:
        if not isinstance(unit, dict):
            return unit
        scaled = dict(unit)
    else:
        scaled = _scale_unit(unit, combined)
    after = unit_size_snapshot(scaled)
    if isinstance(scaled, dict):
        if combined is not None:
            scaled["jev_combined_live_tilt"] = combined
            scaled["jev_risk_pct_before"] = before.get("risk_pct_per_trade")
            scaled["jev_risk_pct_after"] = after.get("risk_pct_per_trade")
        scaled["f5_intended_risk_usd"] = cash
        scaled["intended_risk_usd"] = cash
    write_apply_receipt(
        {
            "schema": "gtos.judgment.apply_receipt.v0",
            "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "symbol": symbol,
            "sleeve": sleeve,
            "ticket": ticket or named.get("ticket"),
            "combined_live_tilt": combined,
            "flow": named.get("flow"),
            "cost": named.get("cost"),
            "ca": named.get("ca"),
            "ca_apply": named.get("ca_apply", False),
            "cost_hurtful": named.get("cost_hurtful"),
            "model": named.get("model") or MODEL,
            "unit_before": before,
            "unit_after": after,
            "f5_intended_risk_usd": cash,
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
        }
    )
    return scaled


def haircut_challenge_unit(
    unit: Any,
    *,
    intent: Any = None,
    tick: Any = None,
    state: dict[str, Any] | None = None,
    answers: dict[str, Any] | None = None,
    ticket: Any = None,
    login: Any = None,
    ns: Any = None,
    already_admitted: bool = True,
    evaluate_jev: bool = True,
    books: dict[str, Any] | None = None,
    as_of_utc: Any = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> Any:
    """Compose (optional Jev answers) then haircut. Challenge-gated inside.

    Host splice: after cost_skip is None, call this instead of
    compose_shadow(state, None) + maybe_haircut_unit. Pass occupancy=
    and governor= from host_occupancy_governor (open book / closed[] /
    decision.governor). Do not wholesale-copy GitHub book_owner.py onto
    the dirty 10069-line host.

    Live compose gets host writer inventory via ``news_inventory_extra``
    (same fields ``challenge_shadow`` already stamps). Lab tape is not live.
    """
    if ticket is None:
        ticket = getattr(intent, "ticket", None) or getattr(intent, "candidate_id", None)
    if state is None and intent is not None:
        from .a1_log import intent_gold_state

        state = intent_gold_state(
            intent,
            tick,
            origin="f5_challenge",
            books=books,
            as_of_utc=as_of_utc,
            occupancy=occupancy,
            governor=governor,
        )
    packed = answers
    as_of = coerce_as_of_utc(as_of_utc) or as_of_from_state(state)
    extra = news_inventory_extra(as_of, live=True)
    composed = compose_shadow(state or {}, packed or {}, ticket=ticket, extra=extra)
    symbol = getattr(intent, "symbol", None) if intent is not None else None
    sleeve = getattr(intent, "sleeve", None) if intent is not None else None
    if symbol is None and isinstance(state, dict):
        symbol = ((state.get("identity") or {}).get("symbol"))
    if sleeve is None and isinstance(state, dict):
        sleeve = ((state.get("identity") or {}).get("sleeve"))
    return maybe_haircut_unit(
        unit,
        composed,
        ticket=ticket,
        login=login,
        ns=ns,
        already_admitted=already_admitted,
        symbol=symbol,
        sleeve=sleeve,
        answers=answers,
        evaluate_jev=evaluate_jev and answers is None,
        state=state,
    )
