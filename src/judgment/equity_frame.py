"""Challenge 0 equity card for gold_state / Jev POSTs.

The card is this login's live broker equity and balance. A missing terminal
read is a fact (`terminal_read=missing`). Chair day-start files stay facts
when they exist. This module does not invent one when the terminal has none.

Each decision on the card, and each parameter, is the System One return for
that account snapshot. The card questions share the decision post when this
snapshot has no frame yet. ``attach_account`` copies a frame and does not
post. ``assemble_account_card`` posts once when a caller builds the card.
A later question in the cycle copies that return. The post runs again only
when the account facts change. Questions are only Noul, Choice, or Score.
Prior outcomes ride on that ask. An empty answer, a tie, or an error leaves
that field unset. Floor and baseline are not questions. This module does not send.
"""

from __future__ import annotations

import json
import sys
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
_DECISION_IDS = (
    "score_is",
    "never_enlarge_because_to_pass",
    "friends_copy_lots",
    "never_book_owner",
    "day_start_max",
    "day_net",
    "open_pnl",
    "cash_unit_usd",
)
_SNAPSHOT_FACTS = (
    "login",
    "ns",
    "equity",
    "balance",
    "open_pnl",
    "to_pass",
    "floor_room",
    "day_start_balance",
    "day_start_equity",
    "day_start_reset_utc",
    "terminal_read",
    "source",
)
# One return per account snapshot. Callers in the same cycle share it.
_FRAME: dict[str, dict[str, Any]] = {}
_FLIGHT: dict[str, threading.Event] = {}
_FRAME_LOCK = threading.Lock()

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


def _iso_z(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _same_reset(stored: Any, reset: datetime | None) -> bool:
    if reset is None:
        return False
    parsed = _parse_utc(stored)
    return parsed is not None and parsed == reset.astimezone(timezone.utc)


def _unset_day(reset: datetime | None, source: str = "unset") -> dict[str, Any]:
    return {
        "day_start_balance": None,
        "day_start_equity": None,
        "day_start_reset_utc": None if reset is None else _iso_z(reset),
        "day_start_source": source,
        "day_start_equity_source": "unset",
    }


def _account_reset_rule(rule_name: str | None) -> str | None:
    """The running account's reset calendar. A missing rule is not a guessed hour."""

    if rule_name in (None, ""):
        return None
    text = str(rule_name).strip()
    return text or None


def _account_login(value: Any) -> int | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _terminal_login(mt5: Any) -> int | None:
    fn = getattr(mt5, "get_account_login", None)
    if callable(fn):
        try:
            return _account_login(fn())
        except Exception:
            return None
    return None


def _writer_may_record(login: Any, namespace: Any, terminal_login: Any) -> bool:
    """The running book records its own day start. A name on argv does not.

    The files live under one account directory. Only that namespace, with
    the terminal's own login, may write them.
    """

    book = _account_login(login)
    terminal = _account_login(terminal_login)
    ns = str(namespace or "").strip()
    if book is None or terminal is None or not ns or book != terminal:
        return False
    try:
        folder = _CHAIR_BASELINE.parents[2].name
    except IndexError:
        return False
    return ns == folder


def _cash_amount(value: Any) -> float | None:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _deal_time(deal: Any, offset_seconds: int | None) -> datetime | None:
    """Deal ``time`` is a broker-wall epoch, the same clock as a position time.

    A datetime is already UTC, which is what ``get_account_history_deals``
    returns after it has removed the offset. An int is the raw epoch.
    """

    raw = _attr(deal, "time")
    if isinstance(raw, datetime) or isinstance(raw, str):
        return _parse_utc(raw)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        if offset_seconds is None:
            return None
        return datetime.fromtimestamp(float(raw) - float(offset_seconds), tz=timezone.utc)
    return None


def _deal_balance_delta(deal: Any) -> float | None:
    """Profit, commission, swap and fee. Balance operations are included."""

    total = 0.0
    for name in ("profit", "commission", "swap", "fee"):
        number = _cash_amount(_attr(deal, name))
        if number is None:
            return None
        total += number
    return total


def _history_deals(mt5: Any, reset: datetime, now: datetime) -> list[Any] | None:
    """Deals in ``[reset, now]``, both instants true UTC.

    ``get_account_history_deals`` shifts that UTC window by the broker offset
    before ``history_deals_get``, because the terminal compares the bounds to
    broker-wall epochs. It then returns each deal time as UTC. This caller
    does not shift the window again.
    """

    fn = getattr(mt5, "get_account_history_deals", None)
    if not callable(fn):
        return None
    try:
        deals = fn(reset, now)
    except Exception:
        return None
    if deals is None:
        return None
    try:
        return list(deals)
    except TypeError:
        return None


def _raw_module(mt5: Any) -> Any:
    raw = getattr(mt5, "_mt5", None)
    return raw if raw is not None else mt5


def _live_position_rows(mt5: Any) -> list[Any] | None:
    raw = _raw_module(mt5)
    fn = getattr(raw, "positions_get", None)
    if not callable(fn):
        return None
    try:
        found = fn()
    except Exception:
        return None
    if found is None:
        return None
    try:
        return list(found)
    except TypeError:
        return None


def _offset_seconds(mt5: Any, server_offset_hours: float | None) -> int | None:
    fn = getattr(mt5, "get_broker_offset_seconds", None)
    if callable(fn):
        try:
            seconds = fn()
        except Exception:
            seconds = None
        if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            return int(seconds)
    if server_offset_hours is None:
        return None
    try:
        hours = float(server_offset_hours)
    except (TypeError, ValueError):
        return None
    if hours != hours or hours in (float("inf"), float("-inf")):
        return None
    return int(round(hours * 3600.0))


def _position_time_utc(pos: Any, offset_seconds: int | None) -> datetime | None:
    raw = _attr(pos, "time")
    if isinstance(raw, datetime):
        return _parse_utc(raw)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        if offset_seconds is None:
            return None
        return datetime.fromtimestamp(float(raw) - float(offset_seconds), tz=timezone.utc)
    return None


def _open_across_reset(
    deals: list[Any],
    positions: list[Any] | None,
    reset: datetime,
    offset_seconds: int | None,
) -> bool | None:
    """Whether a position was open at the reset. None when that cannot be read."""

    if positions is None:
        return None
    opened: set[str] = set()
    crossed = False
    for deal in deals:
        when = _deal_time(deal, offset_seconds)
        if when is None or when < reset:
            continue
        try:
            pid = int(_attr(deal, "position_id"))
        except (TypeError, ValueError):
            pid = 0
        if pid <= 0:
            continue
        try:
            entry = int(_attr(deal, "entry"))
        except (TypeError, ValueError):
            return None
        key = str(pid)
        if entry == 0:
            opened.add(key)
        elif entry in (1, 2, 3) and key not in opened:
            crossed = True
    if crossed:
        return True
    for pos in positions:
        when = _position_time_utc(pos, offset_seconds)
        if when is None:
            return None
        if when < reset:
            return True
    return False


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def _stored_today(reset: datetime | None, login: Any) -> dict[str, Any] | None:
    if reset is None:
        return None
    asked = _account_login(login)
    if asked is None:
        return None
    raw = _read_json(_CHAIR_BASELINE)
    if raw is None or not _same_reset(raw.get("reset_utc"), reset):
        return None
    if _account_login(raw.get("login")) != asked:
        return None
    balance = _float_or_none(raw.get("balance"))
    if balance is None:
        return None
    out = _unset_day(reset, "recorded")
    out["day_start_balance"] = balance
    out["day_start_source"] = "recorded"
    equity = _float_or_none(raw.get("equity"))
    equity_source = "recorded_at_reset"
    if equity is None:
        side = _read_json(_CHAIR_EQUITY)
        if (
            side is not None
            and _same_reset(side.get("reset_utc"), reset)
            and _account_login(side.get("login")) == asked
        ):
            equity = _float_or_none(side.get("equity"))
            equity_source = str(side.get("source") or "recorded_at_reset")
    if equity is None:
        out["day_start_equity_source"] = "unset"
        return out
    out["day_start_equity"] = equity
    out["day_start_equity_source"] = equity_source
    return out


def _derive_day_start(
    mt5: Any,
    now: datetime,
    reset: datetime,
    server_offset_hours: float | None,
) -> dict[str, Any]:
    bal_fn = getattr(mt5, "get_account_balance", None)
    if not callable(bal_fn):
        return _unset_day(reset)
    try:
        balance = _float_or_none(bal_fn())
    except Exception:
        return _unset_day(reset)
    if balance is None:
        return _unset_day(reset)
    deals = _history_deals(mt5, reset, now)
    if deals is None:
        return _unset_day(reset)
    offset = _offset_seconds(mt5, server_offset_hours)
    delta = 0.0
    kept: list[Any] = []
    for deal in deals:
        when = _deal_time(deal, offset)
        if when is None:
            return _unset_day(reset)
        if when < reset:
            continue
        cash = _deal_balance_delta(deal)
        if cash is None:
            return _unset_day(reset)
        delta += cash
        kept.append(deal)
    start_balance = balance - delta
    if start_balance <= 0 or start_balance != start_balance:
        return _unset_day(reset)
    positions = _live_position_rows(mt5)
    crossed = _open_across_reset(kept, positions, reset, offset)
    out = _unset_day(reset, "derived")
    out["day_start_balance"] = start_balance
    out["day_start_source"] = "derived"
    if crossed is False:
        out["day_start_equity"] = start_balance
        out["day_start_equity_source"] = "flat_across_reset"
    return out


def _record_day_start(day: Mapping[str, Any], reset: datetime, login: Any) -> None:
    balance = _float_or_none(day.get("day_start_balance"))
    account = _account_login(login)
    if balance is None or account is None:
        return
    existing = _read_json(_CHAIR_BASELINE)
    if existing is not None:
        stamped = _account_login(existing.get("login"))
        if stamped is not None and stamped != account:
            return
    _write_json(_CHAIR_BASELINE, {
        "login": account,
        "balance": balance,
        "reset_utc": _iso_z(reset),
        "source": day.get("day_start_source") or "derived",
    })
    equity = _float_or_none(day.get("day_start_equity"))
    if equity is None:
        return
    _write_json(_CHAIR_EQUITY, {
        "login": account,
        "equity": equity,
        "reset_utc": _iso_z(reset),
        "source": day.get("day_start_equity_source") or "flat_across_reset",
        "invented": False,
    })


def read_chair_day_start(
    mt5: Any = None,
    now: datetime | None = None,
    *,
    rule_name: str | None = None,
    server_offset_hours: float | None = None,
    login: Any = None,
    namespace: Any = None,
    record: bool | None = None,
) -> dict[str, Any]:
    """Today's day start. A reset that is not the current one is unset.

    The first read after the reset derives the balance from the terminal.
    The running book records it when its login is the terminal's login and
    it names its namespace. A file for another login is not this account.
    """

    now_dt = now or datetime.now(timezone.utc)
    parsed_now = _parse_utc(now_dt)
    if parsed_now is None:
        return _unset_day(None)
    from src.utils.broker_clock import daily_reset_instant_utc

    reset = daily_reset_instant_utc(parsed_now, _account_reset_rule(rule_name), server_offset_hours)
    stored = _stored_today(reset, login)
    if stored is not None:
        return stored
    if mt5 is None or reset is None:
        return _unset_day(reset)
    derived = _derive_day_start(mt5, parsed_now, reset, server_offset_hours)
    terminal_login = _terminal_login(mt5)
    if record is None:
        do_record = _writer_may_record(login, namespace, terminal_login)
    else:
        do_record = bool(record)
    recorded_login = _account_login(login) or terminal_login
    if do_record and derived.get("day_start_balance") is not None:
        try:
            _record_day_start(derived, reset, recorded_login)
        except Exception:
            pass
    return derived


def read_live_positions(raw: Any = None) -> tuple[list[dict[str, Any]] | None, bool]:
    """Broker positions from positions_get. A failed read is unset, not flat."""

    module = raw
    if module is None:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception:
            return None, False
        module = mt5
    fn = getattr(module, "positions_get", None)
    if not callable(fn):
        return None, False
    try:
        found = fn()
    except Exception:
        return None, False
    if found is None:
        return None, False
    try:
        listed = list(found)
    except TypeError:
        return None, False
    rows: list[dict[str, Any]] = []
    for pos in listed:
        ticket = _attr(pos, "ticket")
        symbol = _attr(pos, "symbol")
        if ticket is None or not symbol:
            continue
        side_raw = _attr(pos, "type")
        if side_raw in (0, "BUY", "LONG", "buy"):
            side = "buy"
        elif side_raw in (1, "SELL", "SHORT", "sell"):
            side = "sell"
        else:
            side = None
        rows.append({
            "ticket": ticket,
            "symbol": symbol,
            "side": side,
            "lots": _attr(pos, "volume"),
            "live_sl": _attr(pos, "sl"),
            "tp": _attr(pos, "tp"),
            "entry": _attr(pos, "price_open"),
            "price_open": _attr(pos, "price_open"),
            "comment": _attr(pos, "comment"),
            "sleeve": _attr(pos, "comment"),
            "magic": _attr(pos, "magic"),
            "time": _attr(pos, "time"),
        })
    return rows, True


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


def _score_question(qid: str, instructions: str, anchors: Any = None) -> dict[str, Any]:
    """Amount Score for this card. Fewer than two money facts does not post."""

    try:
        from .jev_questions import amount_question

        built = amount_question(qid, instructions, anchors)
    except Exception:
        return {}
    row = built.get(qid) if isinstance(built, dict) else None
    if isinstance(row, dict):
        criteria = row.get("criteria")
        if isinstance(criteria, list) and len(criteria) >= 2:
            return dict(row)
    return {}


def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "Yes.",
            "false": "No.",
        },
    }


def equity_questions(card: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """One card. Amount Scores use this card's own money. The menu does not decide."""

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
    try:
        from .jev_questions import usd_anchors

        anchors = usd_anchors(card)
    except Exception:
        anchors = []
    for qid, instructions in _SCORES.items():
        block = _score_question(qid, instructions, anchors)
        if isinstance(block.get("criteria"), list) and len(block.get("criteria") or []) >= 2:
            pack[qid] = block
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
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in probabilities:
            continue
        seen = True
        p = probabilities[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
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


def _snapshot_facts() -> tuple[str, ...]:
    try:
        from .jev_client import _ACCOUNT_FACTS
    except Exception:
        return _SNAPSHOT_FACTS
    if isinstance(_ACCOUNT_FACTS, tuple) and _ACCOUNT_FACTS:
        return tuple(str(name) for name in _ACCOUNT_FACTS)
    return _SNAPSHOT_FACTS


def _snapshot_key(row: Mapping[str, Any]) -> str:
    facts = {name: row.get(name) for name in _snapshot_facts()}
    return json.dumps(facts, sort_keys=True, default=str)


def _blank_values() -> dict[str, Any]:
    return {key: None for key in _DECISION_IDS}


def _copy_frame(row: dict[str, Any], saved: Mapping[str, Any]) -> dict[str, Any]:
    """Stamp the shared return. A terminal open profit stays the terminal fact."""

    for key in _DECISION_IDS:
        if key == "open_pnl":
            if row.get("open_pnl") is None:
                row["open_pnl"] = saved.get("open_pnl")
            continue
        row[key] = saved.get(key)
    return row


def _memo_receipt(row: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        from .jev_client import _ACCOUNT_LOCK, _ACCOUNT_MEMO, _account_key
    except Exception:
        return None
    key = _account_key(row)
    with _ACCOUNT_LOCK:
        hit = _ACCOUNT_MEMO.get(key)
    if not isinstance(hit, dict):
        return None
    answers = hit.get("answers")
    if not isinstance(answers, dict) or not answers:
        return None
    return dict(hit)


def _values_of(answers: Mapping[str, Any]) -> dict[str, Any]:
    values = _blank_values()
    values["score_is"] = _choice(answers.get("score_is"), _SCORE_IS_ORDER)
    values["day_start_max"] = _score(answers.get("day_start_max"))
    values["day_net"] = _score(answers.get("day_net"))
    values["open_pnl"] = _score(answers.get("open_pnl"))
    values["cash_unit_usd"] = _score(answers.get("cash_unit_usd"))
    for qid in _NOULS:
        values[qid] = _noul(answers.get(qid))
    return values


def _read_receipt(row: dict[str, Any], receipt: Any) -> dict[str, Any]:
    """Apply one receipt. Empty, tie, and error stay unset."""

    if not isinstance(receipt, dict):
        _remember(row, _pairs({}), "evaluate_not_a_dict")
        _copy_frame(row, _blank_values())
        return _blank_values()
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        _remember(row, _pairs({}), error)
        _copy_frame(row, _blank_values())
        return _blank_values()
    values = _values_of(answers)
    _copy_frame(row, values)
    _remember(row, _pairs(values), None if error in (None, "") else error)
    return values


def frame_ready(account: Mapping[str, Any] | None) -> bool:
    """True when this snapshot already has a frame. It does not post."""

    if not isinstance(account, Mapping):
        return False
    key = _snapshot_key(account)
    with _FRAME_LOCK:
        if key in _FRAME:
            return True
    return _memo_receipt(account) is not None


def note_receipt(account: dict[str, Any], receipt: Mapping[str, Any]) -> None:
    """Store account answers that arrived on a decision post. It does not post.

    An empty score on that post is the answer for this snapshot. A transport
    error does not reach here, so a miss is asked again with the next decision.
    """

    if not isinstance(account, dict) or not isinstance(receipt, Mapping):
        return
    if not receipt.get("ok"):
        return
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        return
    if not any(qid in answers for qid in _DECISION_IDS):
        return
    values = _read_receipt(account, receipt)
    key = _snapshot_key(account)
    with _FRAME_LOCK:
        _FRAME[key] = dict(values)
    try:
        from .jev_client import _ACCOUNT_LOCK, _ACCOUNT_MEMO, _account_key

        akey = _account_key(account)
        kept = {qid: answers.get(qid) for qid in _DECISION_IDS if qid in answers}
        with _ACCOUNT_LOCK:
            _ACCOUNT_MEMO[akey] = {"ok": True, "answers": kept}
    except Exception:
        return


def _cached(row: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    with _FRAME_LOCK:
        saved = _FRAME.get(key)
    if saved is not None:
        return dict(saved)
    receipt = _memo_receipt(row)
    if receipt is None:
        return None
    values = _values_of(receipt.get("answers") or {})
    with _FRAME_LOCK:
        _FRAME.setdefault(key, dict(values))
        return dict(_FRAME[key])


def _post_frame(row: Mapping[str, Any], ask: Callable[..., Any] | None) -> Any:
    questions = equity_questions(row)
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
    return call(
        posted,
        questions=questions,
        merge_sleeve=False,
        model=MODEL,
    )


def _decide(row: dict[str, Any], ask: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One frame for this account snapshot. A later call copies it.

    Inside an ask that already holds the thread, a miss stays the facts.
    It does not start another post.
    """

    key = _snapshot_key(row)
    saved = _cached(row, key)
    if saved is not None:
        return _copy_frame(row, saved)
    if getattr(_ASK, "on", False):
        return row
    with _FRAME_LOCK:
        saved = _FRAME.get(key)
        if saved is not None:
            event = None
            leader = False
        else:
            event = _FLIGHT.get(key)
            if event is None:
                event = threading.Event()
                _FLIGHT[key] = event
                leader = True
            else:
                leader = False
    if saved is not None:
        return _copy_frame(row, saved)
    if not leader:
        event.wait()
        with _FRAME_LOCK:
            saved = _FRAME.get(key)
        if saved is not None:
            return _copy_frame(row, saved)
        return row
    values = _blank_values()
    _ASK.on = True
    try:
        try:
            receipt = _post_frame(row, ask)
        except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the card
            _remember(row, _pairs({}), type(exc).__name__)
            _copy_frame(row, values)
        else:
            values = _read_receipt(row, receipt)
    finally:
        _ASK.on = False
        with _FRAME_LOCK:
            _FRAME[key] = dict(values)
            _FLIGHT.pop(key, None)
        event.set()
    return row


def _day_start_for_card(
    mt5: Any,
    as_of: datetime,
    *,
    login: Any,
    rule_name: str | None,
    server_offset_hours: float | None,
) -> dict[str, Any]:
    """This account's day start. The card reads. It does not record."""

    return read_chair_day_start(
        mt5=mt5,
        now=as_of,
        rule_name=rule_name,
        server_offset_hours=server_offset_hours,
        login=login,
        record=False,
    )


def _assemble_facts(
    *,
    injected: Mapping[str, Any] | None = None,
    mt5: Any = None,
    owner: Any = None,
    as_of_utc: datetime | None = None,
    login: Any = None,
    rule_name: str | None = None,
    server_offset_hours: float | None = None,
) -> dict[str, Any]:
    """Terminal facts. Money keys are always on the card. Parameters stay unset."""
    as_of = as_of_utc or datetime.now(timezone.utc)
    as_of_s = as_of.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    asked_login = login
    if asked_login is None and isinstance(injected, Mapping):
        asked_login = injected.get("login")

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
        _apply_day_start(row, _day_start_for_card(
            mt5 or owner,
            as_of,
            login=asked_login,
            rule_name=rule_name,
            server_offset_hours=server_offset_hours,
        ))
        return row

    equity = float(live["equity"])
    balance = _float_or_none(live.get("balance"))
    open_pnl = _float_or_none(live.get("open_pnl"))
    day = _day_start_for_card(
        mt5 or owner,
        as_of,
        login=asked_login,
        rule_name=rule_name,
        server_offset_hours=server_offset_hours,
    )
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
    login: Any = None,
    rule_name: str | None = None,
    server_offset_hours: float | None = None,
) -> dict[str, Any]:
    """Facts, then one System One ask for the decisions and the parameters."""

    return _decide(
        _assemble_facts(
            injected=injected,
            mt5=mt5,
            owner=owner,
            as_of_utc=as_of_utc,
            login=login,
            rule_name=rule_name,
            server_offset_hours=server_offset_hours,
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
    identity = out.get("identity") if isinstance(out.get("identity"), Mapping) else {}
    asked_login = identity.get("login")
    rule_name = identity.get("reset_rule") or identity.get("daily_reset_rule")
    server_offset_hours = identity.get("server_offset_hours")
    try:
        card = _assemble_facts(
            injected=injected,
            mt5=mt5,
            owner=owner,
            login=asked_login,
            rule_name=rule_name,
            server_offset_hours=server_offset_hours,
        )
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
            card = _assemble_facts(
                injected=existing,
                mt5=mt5,
                owner=owner,
                login=asked_login if asked_login is not None else existing.get("login"),
                rule_name=rule_name,
                server_offset_hours=server_offset_hours,
            )
        except Exception:
            card = _card_shell(terminal_read="missing")
    saved = _cached(card, _snapshot_key(card))
    if saved is not None:
        card = _copy_frame(card, saved)
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
