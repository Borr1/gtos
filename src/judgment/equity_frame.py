"""Challenge 0 equity card for gold_state / Jev POSTs.

The card is this login's live broker equity and balance. A missing terminal
read is a fact (`terminal_read=missing`). Chair day-start files stay facts
when they exist. This module does not invent one when the terminal has none.

Each decision on the card, and each parameter, is the System One return for
that state. One call: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False`` (POST https://api.typesafe.ai/v1/systemone). Questions
are only Noul, Choice, or Score. Prior outcomes ride on that ask. An empty
answer, a tie, or an error leaves that field unset. Floor and baseline are
not questions. This module does not send.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
SCHEMA = "gtos.judgment.equity_frame.v1"
MODEL = "jev-1.13.0"
MONEY_KEYS = ("equity", "to_pass", "floor_room")

# evaluate() stamps this card before it POSTs. The inner stamp stays facts.
_ASK = threading.local()
# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

_SCORE_IS: dict[str, str] = {
    "live_equity": "The score on this card is the live equity.",
    "balance": "The score on this card is the live balance.",
    "open_pnl": "The score on this card is the open profit.",
    "day_net": "The score on this card is the day net.",
}
_SCORE_IS_ORDER = tuple(_SCORE_IS)
_NOULS: dict[str, str] = {
    "never_enlarge_because_to_pass": (
        "Is enlarge refused on this card? "
        "The noul you return is that refusal. "
        "An empty noul leaves it unset. "
        "This question does not send."
    ),
    "friends_copy_lots": (
        "Do friends copy the lots on this card? "
        "The noul you return is that copy. "
        "An empty noul leaves it unset. "
        "This question does not send."
    ),
    "never_book_owner": (
        "Does this card stay off the book owner? "
        "The noul you return is that stay. "
        "An empty noul leaves it unset. "
        "This question does not send."
    ),
}
_SCORES: dict[str, str] = {
    "day_start_max": (
        "The score you return is the day mark on this card. "
        "It may sit between the levels. "
        "An empty score leaves the mark unset. "
        "This question does not send."
    ),
    "day_net": (
        "The score you return is the day net on this card. "
        "It may sit between the levels. "
        "An empty score leaves the day net unset. "
        "This question does not send."
    ),
    "open_pnl": (
        "The score you return is the open profit on this card when the terminal "
        "did not name one. It may sit between the levels. "
        "An empty score leaves the profit unset. "
        "This question does not send."
    ),
    "cash_unit_usd": (
        "The score you return is the cash unit on this card. "
        "It may sit between the levels. "
        "An empty score leaves the cash unit unset. "
        "This question does not send."
    ),
}
_LIMIT_WORDS = ("floor", "baseline")

REPO_ROOT = Path(__file__).resolve().parents[2]
_CHAIR_BASELINE = (
    REPO_ROOT
    / "pipeline_state"
    / "ultimate_book"
    / "operator"
    / "judgment"
    / "state"
    / "chair_day_baseline.json"
)
# Sits next to Chair's balance file. Chair's own writer replaces that file
# with balance + reset_utc only, so day-start equity lives in the sibling.
_CHAIR_EQUITY = _CHAIR_BASELINE.with_name("chair_day_equity.json")


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _login_ok(login: Any) -> bool:
    if login is None or str(login).strip() == "":
        return False
    try:
        return int(login) == CHALLENGE_LOGIN
    except (TypeError, ValueError):
        return str(login).strip() == str(CHALLENGE_LOGIN)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _card_shell(*, terminal_read: str = "missing") -> dict[str, Any]:
    """Money keys always exist. A missing number is a fact, not a skip."""
    return {
        "schema": SCHEMA,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "present": False,
        "source": "terminal",
        "reason": None,
        "terminal_read": terminal_read,
        "equity": None,
        "balance": None,
        "open_pnl": None,
        "to_pass": None,
        "to_pass_balance": None,
        "floor_room": None,
        "day_equity": None,
        "day_start_balance": None,
        "day_start_equity": None,
        "day_start_max": None,
        "day_start_reset_utc": None,
        "day_start_source": "unassembled",
        "day_start_equity_source": "unassembled",
        "day_net": None,
        "pass_line": None,
        "floor": None,
        "initial": None,
        "cash_unit_usd": None,
        "score_is": None,
        "binding_wall": None,
        "never_enlarge_because_to_pass": None,
        "friends_copy_lots": None,
        "never_book_owner": None,
        "invented": False,
    }


def _attr(obj: Any, *names: str) -> Any:
    for name in names:
        if obj is None:
            continue
        if isinstance(obj, Mapping) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            try:
                return getattr(obj, name)
            except Exception:
                continue
    return None


def read_chair_day_start() -> dict[str, Any]:
    """Chair day-start balance at FTMO 00:00 CE(S)T (22:00 UTC).

    Day-start equity sits in the sibling file when a live read recorded it.
    A missing sibling equity stays missing. This read does not create the
    balance file.
    """
    out: dict[str, Any] = {
        "day_start_balance": None,
        "day_start_equity": None,
        "day_start_reset_utc": None,
        "day_start_source": "unassembled",
        "day_start_equity_source": "unassembled",
    }
    raw = _read_json(_CHAIR_BASELINE)
    if raw is None:
        return out
    out["day_start_balance"] = _float_or_none(raw.get("balance"))
    out["day_start_reset_utc"] = raw.get("reset_utc")
    out["day_start_source"] = "chair_day_baseline"
    file_equity = _float_or_none(raw.get("equity"))
    if file_equity is not None:
        out["day_start_equity"] = file_equity
        out["day_start_equity_source"] = "chair_day_baseline"
        return out
    side = _read_json(_CHAIR_EQUITY)
    if side is None or _float_or_none(side.get("equity")) is None:
        return out
    if side.get("reset_utc") != raw.get("reset_utc"):
        return out
    out["day_start_equity"] = _float_or_none(side.get("equity"))
    out["day_start_equity_source"] = str(side.get("source") or "live_read")
    return out


def _sit_day_start_equity(live_equity: float, recorded_utc: str) -> dict[str, Any]:
    """Record this live equity beside the existing Chair balance baseline.

    No Chair file → do not create one. Equity already stored for this reset
    → keep it. No live number → do not invent one.
    """
    day = read_chair_day_start()
    if day.get("day_start_balance") is None or day.get("day_start_equity") is not None:
        return day
    if live_equity is None:
        return day
    raw = _read_json(_CHAIR_BASELINE)
    if raw is None or _float_or_none(raw.get("balance")) is None:
        return day
    payload = {
        "equity": float(live_equity),
        "reset_utc": raw.get("reset_utc"),
        "source": "live_read",
        "recorded_utc": recorded_utc,
        "invented": False,
    }
    try:
        _CHAIR_EQUITY.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CHAIR_EQUITY.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        tmp.replace(_CHAIR_EQUITY)
    except Exception:
        day = dict(day)
        day["day_start_equity"] = float(live_equity)
        day["day_start_equity_source"] = "live_read"
        return day
    return read_chair_day_start()


def _apply_day_start(row: dict[str, Any], day: Mapping[str, Any]) -> None:
    """Copy chair day-start facts onto the card.

    The day mark and the day net are parameters. They stay unset here.
    """
    row["day_start_balance"] = day.get("day_start_balance")
    row["day_start_equity"] = day.get("day_start_equity")
    row["day_start_reset_utc"] = day.get("day_start_reset_utc")
    row["day_start_source"] = day.get("day_start_source")
    row["day_start_equity_source"] = day.get("day_start_equity_source")


def _from_info(info: Any, *, source: str) -> dict[str, Any] | None:
    login = _attr(info, "login")
    if not _login_ok(login):
        return None
    equity = _float_or_none(_attr(info, "equity"))
    if equity is None:
        return None
    balance = _float_or_none(_attr(info, "balance"))
    profit = _float_or_none(_attr(info, "profit"))
    return {
        "login": CHALLENGE_LOGIN,
        "equity": equity,
        "balance": balance,
        "open_pnl": profit,
        "profit": profit,
        "source": source,
    }


def read_live_mt5(*, mt5: Any = None, owner: Any = None) -> dict[str, Any] | None:
    """Read Challenge account_info. Never initialize a terminal. Never raise."""
    probes: list[tuple[str, Any]] = []
    if mt5 is not None:
        probes.append(("injected_mt5", mt5))
    if owner is not None:
        probes.append(("owner._mt5", getattr(owner, "_mt5", None)))
        probes.append(("owner.mt5", getattr(owner, "mt5", None)))
    try:
        import MetaTrader5 as mt5_mod  # type: ignore

        probes.append(("MetaTrader5", mt5_mod))
    except Exception:
        pass

    for source, mod in probes:
        if mod is None:
            continue
        try:
            fn = getattr(mod, "account_info", None)
            info = fn() if callable(fn) else None
            got = _from_info(info, source=source)
            if got:
                return got
        except Exception:
            continue
        try:
            eq_fn = getattr(mod, "get_account_equity", None)
            login_fn = getattr(mod, "get_account_login", None)
            bal_fn = getattr(mod, "get_account_balance", None)
            login = login_fn() if callable(login_fn) else None
            equity = eq_fn() if callable(eq_fn) else None
            balance = bal_fn() if callable(bal_fn) else None
            packed = {
                "login": login,
                "equity": equity,
                "balance": balance,
                "profit": None,
            }
            got = _from_info(packed, source=source + ".get_account_equity")
            if got:
                return got
        except Exception:
            continue
    return None


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _mentions_limit(*parts: Any) -> bool:
    blob = json.dumps(parts, default=str).lower()
    return any(word in blob for word in _LIMIT_WORDS)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    return body


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    body: dict[str, Any] = {"type": "score", "instructions": instructions}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "score"
    body["instructions"] = instructions
    criteria = body.get("criteria")
    if isinstance(criteria, list):
        kept = [item for item in criteria if not _mentions_limit(item)]
        body["criteria"] = kept or ["none", "trace", "small", "modest", "notable", "heavy"]
    return body


def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "Yes.",
            "false": "No.",
        },
    }


def equity_questions() -> dict[str, dict[str, Any]]:
    """One card. The menu names what an answer may return. It does not decide."""

    pack: dict[str, dict[str, Any]] = {
        "score_is": _choice_question(
            "score_is",
            (
                "Which reading is the score on this card? "
                "The choice is the single highest probability. "
                "An empty answer or a tie leaves the choice unset. "
                "This question does not send."
            ),
            _SCORE_IS,
        ),
    }
    for qid, instructions in _NOULS.items():
        pack[qid] = _noul_question(instructions)
    for qid, instructions in _SCORES.items():
        pack[qid] = _score_question(qid, instructions)
    return {
        qid: body
        for qid, body in pack.items()
        if not _mentions_limit(qid, body)
    }


def _probabilities(block: Any) -> dict[str, float]:
    raw = block.get("probabilities") if isinstance(block, Mapping) else None
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _finite(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _local_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p = -1.0
    tied = False
    seen = False
    for name in order:
        if name not in probabilities:
            continue
        seen = True
        p = probabilities[name]
        if best is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label stays unset."""

    probabilities = _probabilities(block)
    if not probabilities:
        return None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = _local_unique(probabilities, order)
    if agreed is None or str(agreed) not in order:
        return None
    if _local_unique(probabilities, order) != str(agreed):
        return None
    return str(agreed)


def _score_local(block: Any) -> float | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "score" in block and block.get("score") is not None:
        return _finite(block.get("score"))
    probabilities = _probabilities(block)
    name = _local_unique(probabilities, tuple(probabilities))
    if name is None:
        return None
    return _finite(probabilities.get(name))


def _score(block: Any) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped to a level."""

    if isinstance(block, Mapping) and block.get("error"):
        return None
    try:
        from .jev_questions import returned_number
    except Exception:
        return _score_local(block)
    return _finite(returned_number(block))


def _noul(block: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. Missing stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block:
        value = block.get("noul")
    elif "Noul" in block:
        value = block.get("Noul")
    else:
        return None
    if value is True or value is False:
        return value
    return _finite(value)


def _priors(state: Mapping[str, Any], questions: Mapping[str, Any]) -> list[Any]:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        return [dict(item) for item in _LOCAL_OUTCOMES]
    return loaded if isinstance(loaded, list) else []


def _remember(row: Mapping[str, Any], pairs: tuple[tuple[str, Any], ...], error: Any) -> None:
    """The returns just run are the next ask's history. A miss is stored as empty."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else error,
            })
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, row, error=None if value is not None else error)
        except Exception:
            return


def _pairs(values: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    keys = ("score_is", *tuple(_NOULS), *tuple(_SCORES))
    return tuple((key, values.get(key)) for key in keys)


def _decide(row: dict[str, Any], ask: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One System One ask. A miss leaves the decision fields unset."""

    if getattr(_ASK, "on", False):
        return row
    _ASK.on = True
    try:
        questions = equity_questions()
        posted: dict[str, Any] = {
            "schema": SCHEMA,
            "model": MODEL,
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "account": dict(row),
        }
        posted["prior_outcomes"] = _priors(posted, questions)
        call = ask
        if call is None:
            from .jev_client import evaluate

            call = evaluate
        receipt = call(
            posted,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the card
        _remember(row, _pairs({}), type(exc).__name__)
        return row
    finally:
        _ASK.on = False

    if not isinstance(receipt, dict):
        _remember(row, _pairs({}), "evaluate_not_a_dict")
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        _remember(row, _pairs({}), error)
        return row

    returned_open = _score(answers.get("open_pnl"))
    values: dict[str, Any] = {
        "score_is": _choice(answers.get("score_is"), _SCORE_IS_ORDER),
        "day_start_max": _score(answers.get("day_start_max")),
        "day_net": _score(answers.get("day_net")),
        "open_pnl": returned_open,
        "cash_unit_usd": _score(answers.get("cash_unit_usd")),
    }
    for qid in _NOULS:
        values[qid] = _noul(answers.get(qid))
    row["score_is"] = values["score_is"]
    row["day_start_max"] = values["day_start_max"]
    row["day_net"] = values["day_net"]
    row["cash_unit_usd"] = values["cash_unit_usd"]
    for qid in _NOULS:
        row[qid] = values[qid]
    if row.get("open_pnl") is None:
        row["open_pnl"] = returned_open
    _remember(row, _pairs(values), None if error in (None, "") else error)
    return row


def _assemble_facts(
    *,
    injected: Mapping[str, Any] | None = None,
    mt5: Any = None,
    owner: Any = None,
    as_of_utc: datetime | None = None,
) -> dict[str, Any]:
    """Terminal facts. Money keys are always on the card. Parameters stay unset."""
    as_of = as_of_utc or datetime.now(timezone.utc)
    as_of_s = as_of.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    live = None
    if isinstance(injected, Mapping) and _float_or_none(injected.get("equity")) is not None:
        live = _from_info(injected, source=str(injected.get("source") or "injected"))
        if live is None and _login_ok(injected.get("login")):
            terminal_profit = _float_or_none(injected.get("profit"))
            live = {
                "login": CHALLENGE_LOGIN,
                "equity": _float_or_none(injected.get("equity")),
                "balance": _float_or_none(injected.get("balance")),
                "open_pnl": terminal_profit,
                "profit": terminal_profit,
                "source": str(injected.get("source") or "injected"),
            }
            if live["equity"] is None:
                live = None
    if live is None:
        live = read_live_mt5(mt5=mt5, owner=owner)
    if live is None or live.get("equity") is None:
        row = _card_shell(terminal_read="missing")
        row["as_of_utc"] = as_of_s
        _apply_day_start(row, read_chair_day_start())
        return row

    equity = float(live["equity"])
    balance = _float_or_none(live.get("balance"))
    open_pnl = _float_or_none(live.get("open_pnl"))
    day = read_chair_day_start()
    if isinstance(injected, Mapping):
        injected_equity = _float_or_none(injected.get("day_start_equity"))
        injected_balance = _float_or_none(injected.get("day_start_balance"))
        if injected_equity is not None:
            day = dict(day)
            day["day_start_equity"] = injected_equity
            day["day_start_equity_source"] = "injected"
        if injected_balance is not None:
            day = dict(day)
            day["day_start_balance"] = injected_balance
            if day.get("day_start_source") == "unassembled":
                day["day_start_source"] = "injected"
    if day.get("day_start_equity") is None and day.get("day_start_balance") is not None:
        day = _sit_day_start_equity(equity, as_of_s)

    row = _card_shell(terminal_read="live")
    row.update(
        {
            "present": True,
            "source": live.get("source") or "mt5",
            "equity": equity,
            "balance": balance,
            "open_pnl": open_pnl,
            "profit": live.get("profit"),
            "to_pass": None,
            "to_pass_balance": None,
            "floor_room": None,
            "day_equity": equity,
            "as_of_utc": as_of_s,
        }
    )
    _apply_day_start(row, day)
    return row


def assemble_account_card(
    *,
    injected: Mapping[str, Any] | None = None,
    mt5: Any = None,
    owner: Any = None,
    as_of_utc: datetime | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Facts, then one System One ask for the decisions and the parameters."""

    return _decide(
        _assemble_facts(
            injected=injected,
            mt5=mt5,
            owner=owner,
            as_of_utc=as_of_utc,
        ),
        ask=ask,
    )


def equity_present(state: Mapping[str, Any] | None) -> bool:
    """True when the money card is on the state the judge will see.

    A null equity is still the card (`terminal_read=missing`). Callers post
    that state. They do not treat a missing number as an absent system.
    """
    if not isinstance(state, Mapping):
        return False
    account = state.get("account")
    if not isinstance(account, Mapping):
        return False
    if not _login_ok(account.get("login")):
        return False
    return all(key in account for key in MONEY_KEYS)


def attach_account(
    state: dict[str, Any] | None,
    *,
    injected: Mapping[str, Any] | None = None,
    mt5: Any = None,
    owner: Any = None,
) -> dict[str, Any]:
    """Stamp ``account`` onto a gold_state object. Never raise."""
    out: dict[str, Any] = dict(state or {})
    existing = out.get("account") if isinstance(out.get("account"), Mapping) else None
    try:
        card = _assemble_facts(injected=injected, mt5=mt5, owner=owner)
    except Exception:
        card = _card_shell(terminal_read="missing")
    if (
        card.get("terminal_read") == "missing"
        and injected is None
        and isinstance(existing, Mapping)
        and _login_ok(existing.get("login"))
        and _float_or_none(existing.get("equity")) is not None
    ):
        try:
            card = _assemble_facts(injected=existing, mt5=mt5, owner=owner)
        except Exception:
            card = _card_shell(terminal_read="missing")
    card = _decide(card)
    for key in MONEY_KEYS:
        card.setdefault(key, None)
    card["reason"] = None
    card["invented"] = False
    out["account"] = card
    completeness = dict(out.get("completeness") or {})
    completeness["account_equity"] = _float_or_none(card.get("equity")) is not None
    completeness["account_card"] = True
    out["completeness"] = completeness
    identity = dict(out.get("identity") or {})
    identity.setdefault("login", CHALLENGE_LOGIN)
    identity.setdefault("ns", CHALLENGE_NS)
    out["identity"] = identity
    try:
        from .jev_questions import hierarchical_labels

        out["labels"] = hierarchical_labels(out)
    except Exception:
        pass
    return out
