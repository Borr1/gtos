"""Autonomous friend copy — Challenge fill → friend_a / redacted_account / redacted_account.

Challenge ``0`` / ``operator`` is the only deciding writer.
Friend FTMO demos copy that fill inside the system: same lots and the same
broker SL/TP. Agents never ``order_send``. redacted_account stays idle.
Verification stays quarantined.

The lots, the stop, the target, the deviation, and the magic on a request
are the returns of one ask for that state. An empty answer, a tie, or an
error is not a send and does not restore a constant. This file never
imports ``book_owner``, ``mt5_real``, or ``order_send``.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

try:
    from .challenge import (
        CHALLENGE_LOGIN as _CHALLENGE_LOGIN_STR,
        CHALLENGE_MAGIC as _CHALLENGE_MAGIC_STR,
        CHALLENGE_NS,
        VERIFICATION_QUARANTINED,
    )
except ImportError:  # file-location import on the host copier
    _CHALLENGE_LOGIN_STR = "0"
    _CHALLENGE_MAGIC_STR = "0"
    CHALLENGE_NS = "operator"
    VERIFICATION_QUARANTINED = "0"

FRIEND_COPY_ENV = "GTOS_FRIEND_COPY"
SCHEMA = "gtos.judgment.friend_copy.v0"
FEEDBACK_SCHEMA = "gtos.fleet_feedback.v0"
ASK_SCHEMA = "gtos.judgment.friend_copy_ask.v1"
MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

CHALLENGE_LOGIN = int(_CHALLENGE_LOGIN_STR)
CHALLENGE_MAGIC = int(_CHALLENGE_MAGIC_STR)
VERIFICATION_LOGIN = int(VERIFICATION_QUARANTINED)
redacted_account_LOGIN = 0
redacted_account_NS = "redacted_account_live_bee34003"

# Identity the fleet binder compares. The request magic is the score.
FRIEND_MAGIC = 20260919

FRIEND_NS = frozenset(
    {
        "friend_a_f5_minimal",
        "ftmo_redacted_account_f5_minimal",
        "ftmo_redacted_account_f5_minimal",
    }
)
FRIEND_LOGINS: dict[str, int] = {
    "friend_a_f5_minimal": 0,
    "ftmo_redacted_account_f5_minimal": 0,
    "ftmo_redacted_account_f5_minimal": 1514684855,
}
FRIEND_LOGIN_SET = frozenset(FRIEND_LOGINS.values())
FRIEND_PATH_MARKERS = ("FTMO_Trial", "FTMO_redacted_account", "FTMO_redacted_account")

FORBIDDEN_TARGET_LOGINS = frozenset(
    {CHALLENGE_LOGIN, VERIFICATION_LOGIN, redacted_account_LOGIN}
)
FORBIDDEN_TARGET_NS = frozenset({CHALLENGE_NS, redacted_account_NS})

VOLUME_POISON_KEYS = frozenset(
    {
        "volume_min",
        "volume_step",
        "volume_max",
        "micro_lot",
        "DEFAULT_MICRO_LOT",
        "lot_min",
        "lot_step",
    }
)
_LOT_EVENT_KEYS = ("lots_placed", "volume", "lots", "result_volume")
_PROTECT_SL_KEYS = (
    "broker_position_sl",
    "broker_position_fill_adjusted_stop_loss",
    "broker_position_planned_stop_loss",
    "orig_sl",
    "sl",
    "stop_loss",
)
_PROTECT_TP_KEYS = (
    "broker_position_tp",
    "broker_position_fill_adjusted_take_profit",
    "broker_position_planned_take_profit",
    "tp",
    "take_profit",
    "orig_tp",
)

TRADE_ACTION_DEAL = 1
TRADE_ACTION_SLTP = 6
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TIME_GTC = 0
ORDER_FILLING_IOC = 1
POSITION_TYPE_BUY = 0
POSITION_TYPE_SELL = 1

_COPY = ("copy", "withhold", "close_friend")
_SCORE_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")

_CLOSED_KIND = frozenset({"close", "closed", "flatten", "sync_close"})
_CLOSED_STATUS = frozenset(
    {
        "closed",
        "broker_closed",
        "vnext_time_stop",
        "time_stop",
        "broker_closed_absent_on_reconcile",
        "flattened",
        "stopped_out",
        "target_hit",
        "stop_hit",
    }
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRADE_RECORD_REL = Path("pipeline_state") / "ultimate_book" / CHALLENGE_NS / "trade_records"
HOST_TRADE_RECORD_ROOTS = (
    REPO_ROOT / TRADE_RECORD_REL,
    Path(r"C:host-local/redacted_host/repo") / TRADE_RECORD_REL,
)
_ASK_LOG = (
    REPO_ROOT
    / "pipeline_state"
    / "ultimate_book"
    / CHALLENGE_NS
    / "judgment"
    / "friend_copy.jsonl"
)

_SIDE_ALIASES = {
    "buy": "buy",
    "long": "buy",
    "0": "buy",
    "sell": "sell",
    "short": "sell",
    "1": "sell",
}

_CACHE: dict[str, dict[str, Any]] = {}
_LEVELS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()
_LAST = threading.local()
_EVAL: dict[str, Any] = {"done": False, "fn": None}


class FriendCopyError(ValueError):
    """The copy did not become a request. Nothing here was sent."""

    def __init__(self, reason: str, **extra: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.extra = extra


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _whole(value: Any) -> int | float | None:
    number = _finite(value)
    if number is None:
        return None
    whole = int(number)
    if whole == number:
        return whole
    return number


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return int(text) if text.lstrip("-").isdigit() else None


def _side_token(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return _SIDE_ALIASES.get(str(value).strip().lower())


def _walk(obj: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(obj, Mapping):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _walk(item)


def _dig(obj: Any, *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, Mapping) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _challenge_terminal_path(path: str) -> bool:
    if not path:
        return False
    if any(marker in path for marker in FRIEND_PATH_MARKERS):
        return False
    lowered = path.replace("/", "\\").lower()
    return lowered.endswith(r"\mt5\ftmo\terminal64.exe")


def _env_fact(environ: Mapping[str, str] | None) -> dict[str, Any]:
    env = environ if environ is not None else os.environ
    present = FRIEND_COPY_ENV in env
    raw = env.get(FRIEND_COPY_ENV) if present else None
    return {
        "name": FRIEND_COPY_ENV,
        "present": present,
        "value": None if raw is None else str(raw),
    }


def _friends_copy_lots_fact(
    event: Mapping[str, Any] | None,
    trade_record: Mapping[str, Any] | None,
) -> Any:
    """Use a copy-lots return already on the card. Do not ask it again."""

    for blob in (event, trade_record):
        if isinstance(blob, Mapping) and "friends_copy_lots" in blob:
            return blob.get("friends_copy_lots")
    return None


def _post_wait(state: Mapping[str, Any] | None) -> float | None:
    """Seconds until this copy state expires, when that fact is already on it.

    No expiry means no timeout.
    """

    if not isinstance(state, Mapping):
        return None
    for key in ("seconds_until_print", "seconds_from_clock", "bar_deadline_s"):
        number = _finite(state.get(key))
        if number is not None and number > 0:
            return float(number)
    return None


def _questions() -> dict[str, Any]:
    copy = (
        "The facts on this card are this copy state. "
        "The option with the single highest probability is the decision. "
        "An empty answer or a tie leaves the decision unset. "
        "An unset decision is not a send. "
        "This question does not send."
    )
    lot = (
        "The score you return is the lot for this copy. "
        "The challenge lots are on the card. "
        "It may sit between the levels. "
        "An empty score leaves the lot unset. "
        "An unset lot is not a send. "
        "This question does not send."
    )
    stop = (
        "The score you return is the stop for this copy. "
        "The challenge stop is on the card. "
        "It may sit between the levels. "
        "An empty score leaves the stop unset. "
        "An unset stop is not a send. "
        "This question does not send."
    )
    target = (
        "The score you return is the target for this copy. "
        "The challenge target is on the card. "
        "It may sit between the levels. "
        "An empty score leaves the target unset. "
        "An unset target is not a send. "
        "This question does not send."
    )
    deviation = (
        "The score you return is the deviation for this request. "
        "It may sit between the levels. "
        "An empty score leaves the deviation unset. "
        "An unset deviation is not a planted number. "
        "This question does not send."
    )
    magic = (
        "The score you return is the magic for this request. "
        "It may sit between the levels. "
        "An empty score leaves the magic unset. "
        "This question does not send."
    )
    on = (
        "Is the friend copy on for this state? "
        "The env value is a fact on the card. "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send."
    )
    target_ok = (
        "Is this login and path a friend copy target for this state? "
        "The login and the path are facts on the card. "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send."
    )
    agent = (
        "May an agent place, close, or resize this friend ticket? "
        "The actor is a fact on the card. "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "An unset noul is not a send. "
        "This question does not send."
    )
    return {
        "friend_copy": {
            "type": "choice",
            "instructions": copy,
            "criteria": {
                "copy": "Build the friend copy from the returned lot, stop, and target.",
                "withhold": "Do not build a copy request for this state.",
                "close_friend": "The next hop reads challenge_source_closed and closes the friend copy only.",
            },
        },
        "friend_lots": {"type": "score", "instructions": lot, "criteria": list(_SCORE_LEVELS)},
        "friend_sl": {"type": "score", "instructions": stop, "criteria": list(_SCORE_LEVELS)},
        "friend_tp": {"type": "score", "instructions": target, "criteria": list(_SCORE_LEVELS)},
        "friend_deviation": {
            "type": "score",
            "instructions": deviation,
            "criteria": list(_SCORE_LEVELS),
        },
        "friend_magic": {"type": "score", "instructions": magic, "criteria": list(_SCORE_LEVELS)},
        "friend_copy_on": {
            "type": "noul",
            "instructions": on,
            "criteria": {"true": "Yes, for this state.", "false": "No, for this state."},
        },
        "friend_target": {
            "type": "noul",
            "instructions": target_ok,
            "criteria": {"true": "Yes, for this state.", "false": "No, for this state."},
        },
        "agent_may_mutate_friend": {
            "type": "noul",
            "instructions": agent,
            "criteria": {"true": "Yes, for this state.", "false": "No, for this state."},
        },
    }


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        raw = block.get("Probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _finite(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in probabilities:
            continue
        seen = True
        p = float(probabilities[name])
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    return _unique(probabilities, order)


def _score_of(block: Any) -> float | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    for key in ("score", "Score", "value"):
        if key in block and block.get(key) is not None:
            return _finite(block.get(key))
    return None


def _noul_of(block: Any) -> bool | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is True or raw is False:
            return bool(raw)
        return None
    picked = _choice_of(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _package_evaluate() -> Callable[..., Any] | None:
    if _EVAL["done"]:
        return _EVAL["fn"]
    _EVAL["done"] = True
    try:
        from .jev_client import evaluate
    except Exception:
        _EVAL["fn"] = None
        return None
    _EVAL["fn"] = evaluate
    return evaluate


def _read_key_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" not in line:
            return line
    return None


def _key_from_env_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'").strip('"')
        if name in {"TYPESAFE_API_KEY", "TYPESAFE_KEY"} and value:
            found[name] = value
    return found.get("TYPESAFE_API_KEY") or found.get("TYPESAFE_KEY")


def _resolve_key() -> tuple[str | None, str | None]:
    """Return the key and a source label. The key stays out of every row."""

    env_api = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if env_api:
        return env_api, "env:TYPESAFE_API_KEY"
    env_key = (os.environ.get("TYPESAFE_KEY") or "").strip()
    if env_key:
        return env_key, "env:TYPESAFE_KEY"
    override = (os.environ.get("TYPESAFE_KEY_FILE") or "").strip()
    if override:
        path = Path(override)
        got = _key_from_env_file(path) or _read_key_file(path)
        if got:
            return got, "file:TYPESAFE_KEY_FILE"
    home = Path.home() / ".config" / "typesafe" / "api_key"
    got = _read_key_file(home)
    if got:
        return got, "file:~/.config/typesafe/api_key"
    for path, label in (
        (Path("/run/secrets/TYPESAFE_API_KEY"), "file:/run/secrets/TYPESAFE_API_KEY"),
        (Path("/run/secrets/TYPESAFE_KEY"), "file:/run/secrets/TYPESAFE_KEY"),
        (REPO_ROOT / "secrets" / "TYPESAFE_API_KEY.txt", "file:secrets/TYPESAFE_API_KEY.txt"),
        (REPO_ROOT / "secrets" / "TYPESAFE_KEY.txt", "file:secrets/TYPESAFE_KEY.txt"),
    ):
        got = _read_key_file(path)
        if got:
            return got, label
    got = _key_from_env_file(REPO_ROOT / ".env.typesafe")
    if got:
        return got, "file:.env.typesafe"
    return None, None


def _standalone_post(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    key, source = _resolve_key()
    if not key:
        return {"error": "key_unreadable", "answers": {}, "key_source": source, "model": MODEL}
    payload = {"model": MODEL, "state": dict(state), "questions": dict(questions)}
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, default=str).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/0.1",
        },
    )
    try:
        wait = _post_wait(state)
        opened = urllib.request.urlopen(req, timeout=wait) if wait is not None else urllib.request.urlopen(req)
        with opened as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"error": f"http_{exc.code}", "answers": {}, "key_source": source, "model": MODEL}
    except Exception as exc:  # noqa: BLE001 — a missed ask is not a send
        return {"error": type(exc).__name__, "answers": {}, "key_source": source, "model": MODEL}
    if not isinstance(body, dict):
        return {"error": "body_not_a_dict", "answers": {}, "key_source": source, "model": MODEL}
    answers = body.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    return {
        "error": body.get("error"),
        "answers": answers,
        "key_source": source,
        "model": body.get("model") or MODEL,
    }


def _post(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    if ask is not None:
        try:
            receipt = ask(dict(state), questions=dict(questions), merge_sleeve=False, model=MODEL)
        except Exception as exc:  # noqa: BLE001
            return {"error": type(exc).__name__, "answers": {}, "model": MODEL}
        if not isinstance(receipt, dict):
            return {"error": "evaluate_not_a_dict", "answers": {}, "model": MODEL}
        answers = receipt.get("answers")
        if not isinstance(answers, dict):
            answers = {}
        return {
            "error": receipt.get("error") or receipt.get("skipped"),
            "answers": answers,
            "model": receipt.get("model") or MODEL,
        }
    evaluate = _package_evaluate()
    if evaluate is not None:
        try:
            receipt = evaluate(
                dict(state),
                questions=dict(questions),
                merge_sleeve=False,
                model=MODEL,
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": type(exc).__name__, "answers": {}, "model": MODEL}
        if not isinstance(receipt, dict):
            return {"error": "evaluate_not_a_dict", "answers": {}, "model": MODEL}
        answers = receipt.get("answers")
        if not isinstance(answers, dict):
            answers = {}
        return {
            "error": receipt.get("error") or receipt.get("skipped"),
            "answers": answers,
            "model": receipt.get("model") or MODEL,
        }
    return _standalone_post(state, questions)


def _blank_row(error: Any) -> dict[str, Any]:
    return {
        "choice": None,
        "lots": None,
        "sl": None,
        "tp": None,
        "deviation": None,
        "magic": None,
        "copy_on": None,
        "target": None,
        "agent": None,
        "error": error,
        "asked": True,
        "model": MODEL,
    }


def _row_from_answers(answers: Mapping[str, Any], error: Any) -> dict[str, Any]:
    row = _blank_row(None if answers else error)
    row["choice"] = _choice_of(answers.get("friend_copy"), _COPY)
    row["lots"] = _score_of(answers.get("friend_lots"))
    row["sl"] = _score_of(answers.get("friend_sl"))
    row["tp"] = _score_of(answers.get("friend_tp"))
    row["deviation"] = _score_of(answers.get("friend_deviation"))
    row["magic"] = _score_of(answers.get("friend_magic"))
    row["copy_on"] = _noul_of(answers.get("friend_copy_on"))
    row["target"] = _noul_of(answers.get("friend_target"))
    row["agent"] = _noul_of(answers.get("agent_may_mutate_friend"))
    if answers and error:
        row["error"] = error
    return row


def _existing_answers(facts: Mapping[str, Any]) -> dict[str, Any] | None:
    answers = facts.get("answers")
    if not isinstance(answers, Mapping):
        return None
    if not any(name in answers for name in _questions()):
        return None
    return _row_from_answers(answers, facts.get("error"))


def _log_ask(facts: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    payload = {
        "schema": ASK_SCHEMA,
        "model": row.get("model") or MODEL,
        "ticket": facts.get("ticket"),
        "symbol": facts.get("symbol"),
        "side": facts.get("side"),
        "login": facts.get("login"),
        "ns": facts.get("ns"),
        "actor": facts.get("actor"),
        "choice": row.get("choice"),
        "lots": row.get("lots"),
        "sl": row.get("sl"),
        "tp": row.get("tp"),
        "deviation": row.get("deviation"),
        "magic": row.get("magic"),
        "friend_copy_on": row.get("copy_on"),
        "friend_target": row.get("target"),
        "agent_may_mutate_friend": row.get("agent"),
        "error": row.get("error"),
        "order_send": False,
        "agent_order_send": False,
    }
    try:
        _ASK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _ASK_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
    except OSError:
        return


def _decide(facts: Mapping[str, Any], *, ask: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One ask for this state. The same facts reuse that return."""

    existing = _existing_answers(facts)
    if existing is not None:
        _LAST.row = existing
        _LAST.fresh = True
        return existing
    key = json.dumps(facts, sort_keys=True, default=str)
    if ask is None:
        with _LOCK:
            hit = _CACHE.get(key)
        if hit is not None:
            _LAST.row = hit
            _LAST.fresh = True
            return hit
    receipt = _post(facts, _questions(), ask)
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), Mapping) else {}
    error = receipt.get("error")
    if not answers and not error:
        error = "empty"
    row = _row_from_answers(answers, error)
    row["model"] = receipt.get("model") or MODEL
    _LAST.row = row
    _LAST.fresh = True
    if ask is None:
        with _LOCK:
            _CACHE[key] = row
        _log_ask(facts, row)
    return row


def _level_key(symbol: Any, volume: Any, sl: Any, tp: Any) -> str:
    return "|".join(
        [
            str(symbol or ""),
            "" if _finite(volume) is None else repr(_finite(volume)),
            "" if _finite(sl) is None else repr(_finite(sl)),
            "" if _finite(tp) is None else repr(_finite(tp)),
        ]
    )


def _remember_levels(symbol: Any, volume: Any, sl: Any, tp: Any, row: Mapping[str, Any]) -> None:
    if _finite(volume) is None or _finite(sl) is None or _finite(tp) is None:
        return
    _LEVELS[_level_key(symbol, volume, sl, tp)] = dict(row)


def _saved_row(symbol: Any, volume: Any, sl: Any, tp: Any) -> dict[str, Any] | None:
    found = _LEVELS.get(_level_key(symbol, volume, sl, tp))
    if isinstance(found, dict):
        return found
    if getattr(_LAST, "fresh", False) and isinstance(getattr(_LAST, "row", None), dict):
        _LAST.fresh = False
        return dict(_LAST.row)
    return None


def _volume_facts(
    event: Mapping[str, Any] | None,
    trade_record: Mapping[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    legal: list[dict[str, Any]] = []
    poison: list[dict[str, Any]] = []

    def add(bucket: list[dict[str, Any]], source: str, value: Any) -> None:
        got = _finite(value)
        if got is None:
            return
        bucket.append({"source": source, "value": got})

    paths = (
        ("instrumentation", "gtos_live_flow_execution", "lots_placed"),
        ("gtos_live_flow_execution", "lots_placed"),
        ("execution", "lots_placed"),
        ("lots_placed",),
    )
    if isinstance(trade_record, Mapping):
        for path in paths:
            add(legal, "trade_record." + ".".join(path), _dig(trade_record, *path))
        for path, source in (
            (("execution", "result", "volume"), "trade_record.execution.result.volume"),
            (("result", "volume"), "trade_record.result.volume"),
            (("execution", "request", "volume"), "trade_record.execution.request.volume"),
            (("request", "volume"), "trade_record.request.volume"),
            (("lots_normalized",), "trade_record.lots_normalized"),
        ):
            add(legal, source, _dig(trade_record, *path))
    if isinstance(event, Mapping):
        for path, source in (
            (("execution", "result", "volume"), "event.execution.result.volume"),
            (("result", "volume"), "event.result.volume"),
            (("execution", "request", "volume"), "event.execution.request.volume"),
            (("request", "volume"), "event.request.volume"),
            (("lots_normalized",), "event.lots_normalized"),
        ):
            add(legal, source, _dig(event, *path))
        for key in _LOT_EVENT_KEYS:
            add(legal, f"event.{key}", event.get(key))
    for blob, label in ((trade_record, "trade_record"), (event, "event")):
        if not isinstance(blob, Mapping):
            continue
        for row in _walk(blob):
            for key, value in row.items():
                if key in VOLUME_POISON_KEYS:
                    add(poison, f"{label}.{key}", value)
                elif key in _LOT_EVENT_KEYS or key == "lots_normalized":
                    add(legal, f"{label}.{key}", value)
    return {"legal": legal, "poison": poison}


def _protection_facts(
    event: Mapping[str, Any] | None,
    trade_record: Mapping[str, Any] | None,
    keys: Iterable[str],
    kind: str,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def add(source: str, value: Any) -> None:
        got = _finite(value)
        if got is None:
            return
        found.append({"source": source, "value": got})

    fill_key = (
        "broker_position_fill_adjusted_stop_loss"
        if kind == "sl"
        else "broker_position_fill_adjusted_take_profit"
    )
    planned_key = (
        "broker_position_planned_stop_loss"
        if kind == "sl"
        else "broker_position_planned_take_profit"
    )
    preferred = (
        ("execution", f"broker_position_{kind}"),
        ("execution", fill_key),
        ("execution", planned_key),
    )
    if isinstance(trade_record, Mapping):
        for path in preferred:
            add(".".join(path), _dig(trade_record, *path))
        for row in _walk(trade_record):
            for key in keys:
                add(f"trade_record.{key}", row.get(key))
    if isinstance(event, Mapping):
        for key in keys:
            add(f"event.{key}", event.get(key))
    return found


def _side_from_geometry(record: Mapping[str, Any] | None) -> str | None:
    """SHORT: SL above fill above TP. LONG: the inverse. A fact, not a default."""

    if not isinstance(record, Mapping):
        return None
    fill = _finite(
        _dig(record, "execution", "broker_position_fill_price")
        or _dig(record, "execution", "broker_position_price_open")
        or _dig(record, "execution", "broker_entry_price")
    )
    stops = _protection_facts(None, record, _PROTECT_SL_KEYS, "sl")
    targets = _protection_facts(None, record, _PROTECT_TP_KEYS, "tp")
    sl = next((item["value"] for item in stops if item["value"] != 0), None)
    tp = next((item["value"] for item in targets if item["value"] != 0), None)
    if fill is None or sl is None or tp is None:
        return None
    if sl > fill > tp:
        return "sell"
    if tp > fill > sl:
        return "buy"
    return None


def _status_closed(status: str) -> bool:
    token = str(status or "").strip().lower()
    if not token:
        return False
    if token in _CLOSED_STATUS:
        return True
    return token.startswith("closed") or token.endswith("_closed")


def _target_facts(
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
) -> dict[str, Any]:
    token = str(ns or "").strip()
    parsed = _as_int(login)
    path = str(terminal_path or "")
    return {
        "ns": token or None,
        "login": parsed,
        "terminal_path": path or None,
        "target_is_challenge_login": parsed == CHALLENGE_LOGIN if parsed is not None else None,
        "target_is_verification": parsed == VERIFICATION_LOGIN if parsed is not None else None,
        "target_is_redacted_account": parsed == redacted_account_LOGIN if parsed is not None else None,
        "target_is_friend_login": parsed in FRIEND_LOGIN_SET if parsed is not None else None,
        "target_is_friend_ns": token in FRIEND_NS if token else None,
        "target_is_forbidden_ns": token in FORBIDDEN_TARGET_NS if token else None,
        "target_is_challenge_terminal": _challenge_terminal_path(path) if path else False,
    }


def _card(
    event: Mapping[str, Any] | None,
    trade_record: Mapping[str, Any] | None,
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
    price: Any = None,
    environ: Mapping[str, str] | None = None,
    actor: str = "copier",
) -> dict[str, Any]:
    row = dict(event or {})
    record = trade_record if isinstance(trade_record, Mapping) else None
    ticket = row.get("ticket")
    if ticket in (None, "") and isinstance(record, Mapping):
        ticket = (
            record.get("ticket")
            or _dig(record, "execution", "ticket")
            or _dig(record, "execution", "broker_entry_deal_ticket")
        )
    symbol = str(row.get("symbol") or (record or {}).get("symbol") or "").strip()
    side = _side_token(
        row.get("side")
        or (record or {}).get("side")
        or (record or {}).get("direction")
        or _dig(record, "instrumentation", "direction")
        or _dig(record, "instrumentation", "gtos_vnext_pretrade_cost_model", "side")
        or _dig(record, "instrumentation", "gtos_vnext_source_event_details", "direction")
        or _dig(record, "execution", "side")
    )
    if side is None:
        side = _side_from_geometry(record)
    closed, closed_from = challenge_source_is_closed(row, record)
    source_login = _as_int(row.get("source_login") or row.get("login"))
    card: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "actor": actor,
        "ticket": None if ticket in (None, "") else ticket,
        "symbol": symbol or None,
        "side": side,
        "source_login": source_login,
        "source_is_challenge": source_login == CHALLENGE_LOGIN if source_login is not None else None,
        "source_is_verification": (
            source_login == VERIFICATION_LOGIN if source_login is not None else None
        ),
        "source_closed": closed,
        "source_closed_from": closed_from,
        "lots": _volume_facts(row, record),
        "stops": _protection_facts(row, record, _PROTECT_SL_KEYS, "sl"),
        "targets": _protection_facts(row, record, _PROTECT_TP_KEYS, "tp"),
        "friends_copy_lots": _friends_copy_lots_fact(row, record),
        "env": _env_fact(environ),
        "price": _finite(price),
    }
    card.update(_target_facts(ns=ns, login=login, terminal_path=terminal_path))
    carried = _existing_answers({"answers": row.get("answers"), "error": row.get("error")})
    if carried is not None:
        card["answers"] = row.get("answers")
        card["error"] = row.get("error")
    return card


def _naked(sl: Any, tp: Any) -> bool:
    stop = _finite(sl)
    target = _finite(tp)
    return stop is None or target is None or stop == 0 or target == 0


def _usable_lot(lots: Any) -> bool:
    number = _finite(lots)
    return number is not None and number > 0


@dataclass(frozen=True)
class CopyContract:
    """One Challenge fill, ready for the in-system copier. Never sends."""

    ok: bool
    reason: str | None
    ticket: Any = None
    symbol: str = ""
    side: str | None = None
    lots: float | None = None
    sl: float | None = None
    tp: float | None = None
    comment: str = ""
    lots_source: str | None = None
    sl_source: str | None = None
    tp_source: str | None = None
    place_on_challenge: bool = False
    agent_order_send: bool = False
    redacted_account_idle: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        extra = self.extra if isinstance(self.extra, dict) else {}
        agent = extra.get("agent_may_mutate_friend") if "agent_may_mutate_friend" in extra else None
        return {
            "schema": SCHEMA,
            "ok": self.ok,
            "reason": self.reason,
            "choice": extra.get("choice"),
            "ticket": self.ticket,
            "symbol": self.symbol,
            "side": self.side,
            "lots": self.lots,
            "sl": self.sl,
            "tp": self.tp,
            "deviation": extra.get("deviation"),
            "magic": extra.get("magic"),
            "comment": self.comment,
            "lots_source": self.lots_source,
            "sl_source": self.sl_source,
            "tp_source": self.tp_source,
            "place_on_challenge": False,
            "agent_order_send": False,
            "agent_may_mutate_friend": agent,
            "friend_copy_on": extra.get("friend_copy_on"),
            "friend_target": extra.get("friend_target"),
            "redacted_account_idle": True,
            "never_invent_micro_lot": True,
            "never_invent_zero_protection": True,
            "never_flatten_challenge": True,
            "source_closed": self.reason == "challenge_source_closed",
            "close_friend_only": self.reason == "challenge_source_closed",
            "error": extra.get("error"),
            "order_send": False,
        }


def agent_may_mutate_friend(
    *,
    ns: Any = None,
    login: Any = None,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
) -> bool | None:
    """The noul for this state. An empty noul is not a mutation."""

    card = _card(
        {"actor": "agent"},
        None,
        ns=ns,
        login=login,
        environ=environ,
        actor="agent",
    )
    return _decide(card, ask=ask)["agent"]


def friend_copy_env_on(
    *,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
) -> bool | None:
    """The copy-on noul. An empty noul does not restore the old default."""

    card = _card(None, None, environ=environ, actor="copier")
    return _decide(card, ask=ask)["copy_on"]


def friend_copy_on(
    *,
    ns: Any = None,
    login: Any = None,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
) -> bool | None:
    """The copy-on noul for this namespace and login."""

    card = _card(None, None, ns=ns, login=login, environ=environ, actor="copier")
    return _decide(card, ask=ask)["copy_on"]


def assert_copy_target(
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
    ask: Callable[..., Any] | None = None,
) -> None:
    """The target noul. An empty noul is not a send."""

    card = _card(None, None, ns=ns, login=login, terminal_path=terminal_path, actor="copier")
    decided = _decide(card, ask=ask)
    if decided["target"] is True:
        return
    if decided["target"] is False:
        raise FriendCopyError(
            "friend_target",
            login=_as_int(login),
            ns=str(ns or "").strip(),
            place_on_challenge=False,
            redacted_account_idle=True,
        )
    raise FriendCopyError(
        "no_decision",
        error=decided.get("error"),
        place_on_challenge=False,
        redacted_account_idle=True,
    )


def fleet_comment(ticket: Any) -> str:
    return f"fleet:{ticket}"


def order_side(side: Any) -> int:
    token = _side_token(side)
    if token is None:
        raise FriendCopyError("missing_side", side=side)
    return ORDER_TYPE_BUY if token == "buy" else ORDER_TYPE_SELL


def challenge_source_is_closed(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """Tape fact. The close decision is the ask, not this boolean."""

    if isinstance(event, Mapping):
        kind = str(event.get("kind") or "").strip().lower()
        if kind in _CLOSED_KIND:
            return True, "event.kind"
        if event.get("closed") is True:
            return True, "event.closed"
        if _status_closed(str(event.get("trade_lifecycle_status") or "")):
            return True, "event.trade_lifecycle_status"
        if event.get("closed_at_utc") not in (None, "", 0, "0"):
            return True, "event.closed_at_utc"
    if isinstance(trade_record, Mapping):
        if _status_closed(str(trade_record.get("trade_lifecycle_status") or "")):
            return True, "trade_lifecycle_status"
        closed_at = trade_record.get("closed_at_utc") or _dig(
            trade_record, "execution", "closed_at_utc"
        )
        if closed_at not in (None, "", 0, "0"):
            return True, "closed_at_utc"
        close_action = trade_record.get("close_action") or _dig(
            trade_record, "execution", "close_action"
        )
        if close_action not in (None, "", 0, "0"):
            return True, "close_action"
    return False, None


def protection_is_missing(position: Any) -> bool:
    if isinstance(position, Mapping):
        sl = _finite(position.get("sl"))
        tp = _finite(position.get("tp"))
    else:
        sl = _finite(getattr(position, "sl", None))
        tp = _finite(getattr(position, "tp", None))
    return _naked(sl, tp)


def load_challenge_trade_record(
    ticket: Any,
    *,
    roots: Iterable[Path] | None = None,
) -> dict[str, Any] | None:
    """``pipeline_state/ultimate_book/operator/trade_records/{ticket}.json``."""

    if ticket in (None, ""):
        return None
    name = f"{ticket}.json"
    for root in roots or HOST_TRADE_RECORD_ROOTS:
        path = Path(root) / name
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def resolve_copy_lots(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., Any] | None = None,
) -> tuple[float | None, str | None]:
    """The lot score. An empty score leaves the lot unset."""

    card = _card(event, trade_record, actor="copier")
    lots = _decide(card, ask=ask)["lots"]
    if lots is None:
        return None, None
    return lots, "friend_lots"


def resolve_copy_protection(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., Any] | None = None,
) -> tuple[float | None, float | None, str | None, str | None]:
    """The stop and target scores. An empty score leaves that price unset."""

    card = _card(event, trade_record, actor="copier")
    row = _decide(card, ask=ask)
    sl = row["sl"]
    tp = row["tp"]
    return sl, tp, ("friend_sl" if sl is not None else None), ("friend_tp" if tp is not None else None)


def _contract_from(
    decided: Mapping[str, Any],
    *,
    ticket: Any,
    symbol: str,
    side: str | None,
    comment: str,
    price: Any,
    closed_from: str | None,
) -> CopyContract:
    lots = decided.get("lots")
    sl = decided.get("sl")
    tp = decided.get("tp")
    choice = decided.get("choice")
    extra = {
        "choice": choice,
        "deviation": decided.get("deviation"),
        "magic": decided.get("magic"),
        "friend_copy_on": decided.get("copy_on"),
        "friend_target": decided.get("target"),
        "agent_may_mutate_friend": decided.get("agent"),
        "error": decided.get("error"),
        "source_closed_from": closed_from,
        "asked": True,
        "price": _finite(price),
    }
    if choice == "close_friend":
        extra["close_friend_only"] = True
        reason: str | None = "challenge_source_closed"
        ok = False
    elif choice == "withhold":
        reason = "withhold"
        ok = False
    elif (
        choice == "copy"
        and decided.get("copy_on") is True
        and decided.get("target") is True
        and ticket not in (None, "")
        and bool(symbol)
        and side is not None
        and _usable_lot(lots)
        and not _naked(sl, tp)
    ):
        reason = "copy_ready"
        ok = True
    else:
        reason = None
        ok = False
    contract = CopyContract(
        ok=ok,
        reason=reason,
        ticket=ticket,
        symbol=symbol,
        side=side,
        lots=_finite(lots),
        sl=_finite(sl),
        tp=_finite(tp),
        comment=comment,
        lots_source="friend_lots" if lots is not None else None,
        sl_source="friend_sl" if sl is not None else None,
        tp_source="friend_tp" if tp is not None else None,
        extra=extra,
    )
    _remember_levels(symbol, lots, sl, tp, decided)
    return contract


def resolve_copy_contract(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
    price: Any = None,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
) -> CopyContract:
    """One ask. The contract is that return. An empty return is not a send."""

    row = dict(event or {})
    record = trade_record if isinstance(trade_record, Mapping) else None
    if record is None and row.get("ticket") not in (None, ""):
        record = load_challenge_trade_record(row.get("ticket"))
    card = _card(
        row,
        record,
        ns=ns,
        login=login,
        terminal_path=terminal_path,
        price=price,
        environ=environ,
        actor="copier",
    )
    decided = _decide(card, ask=ask)
    comment = fleet_comment(card["ticket"]) if card.get("ticket") not in (None, "") else ""
    return _contract_from(
        decided,
        ticket=card.get("ticket"),
        symbol=str(card.get("symbol") or ""),
        side=card.get("side"),
        comment=comment,
        price=price,
        closed_from=card.get("source_closed_from"),
    )


def _attach_request_numbers(
    request: dict[str, Any],
    *,
    symbol: Any,
    volume: Any,
    sl: Any,
    tp: Any,
    deviation: Any,
    magic: Any,
    ask: Callable[..., Any] | None,
    facts: Mapping[str, Any],
) -> dict[str, Any]:
    dev = _finite(deviation)
    mag = _finite(magic)
    saved = _saved_row(symbol, volume, sl, tp) if dev is None or mag is None else None
    if saved is None and (dev is None or mag is None):
        saved = _decide(facts, ask=ask)
    if dev is None and isinstance(saved, Mapping):
        dev = _finite(saved.get("deviation"))
    if mag is None and isinstance(saved, Mapping):
        mag = _finite(saved.get("magic"))
    if dev is not None:
        request["deviation"] = _whole(dev)
    if mag is not None:
        request["magic"] = _whole(mag)
    return request


def copy_open_request(
    *,
    symbol: str,
    side: str,
    volume: float,
    sl: float,
    tp: float,
    comment: str,
    price: float,
    magic: Any = None,
    deviation: Any = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """DEAL request. Deviation and magic are the scores. This function does not send."""

    lot = _finite(volume)
    stop = _finite(sl)
    target = _finite(tp)
    px = _finite(price)
    if lot is None or not _usable_lot(lot):
        raise FriendCopyError("missing_source_volume", volume=volume)
    if _naked(stop, target):
        raise FriendCopyError("naked", sl=sl, tp=tp)
    if px is None:
        raise FriendCopyError("missing_price", price=price)
    request = {
        "action": TRADE_ACTION_DEAL,
        "symbol": str(symbol),
        "volume": float(lot),
        "type": order_side(side),
        "price": float(px),
        "sl": float(stop),
        "tp": float(target),
        "comment": str(comment),
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }
    return _attach_request_numbers(
        request,
        symbol=symbol,
        volume=lot,
        sl=stop,
        tp=target,
        deviation=deviation,
        magic=magic,
        ask=ask,
        facts={
            "schema": SCHEMA,
            "actor": "copier",
            "symbol": str(symbol),
            "side": _side_token(side),
            "lots": {"legal": [{"source": "request.volume", "value": lot}], "poison": []},
            "stops": [{"source": "request.sl", "value": stop}],
            "targets": [{"source": "request.tp", "value": target}],
            "price": px,
        },
    )


def copy_sltp_request(
    *,
    symbol: str,
    position: int,
    sl: float,
    tp: float,
    magic: Any = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """SLTP request for an already-open friend ticket. This function does not send."""

    stop = _finite(sl)
    target = _finite(tp)
    if _naked(stop, target):
        raise FriendCopyError("naked", sl=sl, tp=tp)
    ticket = _as_int(position)
    if ticket is None:
        raise FriendCopyError("missing_demo_ticket", position=position)
    request: dict[str, Any] = {
        "action": TRADE_ACTION_SLTP,
        "symbol": str(symbol),
        "position": int(ticket),
        "sl": float(stop),
        "tp": float(target),
    }
    mag = _finite(magic)
    if mag is None:
        saved = _saved_row(symbol, None, stop, target)
        if isinstance(saved, Mapping):
            mag = _finite(saved.get("magic"))
        elif ask is not None or getattr(_LAST, "row", None) is None:
            row = _decide(
                {
                    "schema": SCHEMA,
                    "actor": "copier",
                    "symbol": str(symbol),
                    "demo_ticket": ticket,
                    "stops": [{"source": "request.sl", "value": stop}],
                    "targets": [{"source": "request.tp", "value": target}],
                },
                ask=ask,
            )
            mag = _finite(row.get("magic"))
    if mag is not None:
        request["magic"] = _whole(mag)
    return request


def copy_close_request(
    *,
    symbol: str,
    side: str,
    volume: float,
    position: int,
    price: float,
    comment: str = "",
    magic: Any = None,
    deviation: Any = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """DEAL close of a friend copy. Deviation is the score. This function does not send."""

    lot = _finite(volume)
    ticket = _as_int(position)
    px = _finite(price)
    if lot is None or not _usable_lot(lot):
        raise FriendCopyError("missing_close_volume", volume=volume)
    if ticket is None:
        raise FriendCopyError("missing_demo_ticket", position=position)
    if px is None:
        raise FriendCopyError("missing_price", price=price)
    open_type = order_side(side)
    close_type = ORDER_TYPE_SELL if open_type == ORDER_TYPE_BUY else ORDER_TYPE_BUY
    text = str(comment or f"fleet-close:{ticket}")
    request = {
        "action": TRADE_ACTION_DEAL,
        "symbol": str(symbol),
        "volume": float(lot),
        "type": close_type,
        "position": int(ticket),
        "price": float(px),
        "comment": text,
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
        "place_on_challenge": False,
        "close_friend_only": True,
    }
    return _attach_request_numbers(
        request,
        symbol=symbol,
        volume=lot,
        sl=None,
        tp=None,
        deviation=deviation,
        magic=magic,
        ask=ask,
        facts={
            "schema": SCHEMA,
            "actor": "copier",
            "symbol": str(symbol),
            "side": _side_token(side),
            "demo_ticket": ticket,
            "lots": {"legal": [{"source": "request.volume", "value": lot}], "poison": []},
            "price": px,
            "close_friend_only": True,
        },
    )


def enrich_open_request(
    request: Mapping[str, Any],
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Stamp the returned lots and protection onto a fleet DEAL request."""

    contract = resolve_copy_contract(event, trade_record, ask=ask)
    if not contract.ok:
        raise FriendCopyError(contract.reason or "no_decision", ticket=contract.ticket, symbol=contract.symbol)
    out = dict(request)
    out["volume"] = contract.lots
    out["sl"] = contract.sl
    out["tp"] = contract.tp
    if contract.comment:
        out.setdefault("comment", contract.comment)
    extra = contract.extra if isinstance(contract.extra, dict) else {}
    if extra.get("deviation") is not None:
        out["deviation"] = _whole(extra.get("deviation"))
    if extra.get("magic") is not None:
        out["magic"] = _whole(extra.get("magic"))
    if _naked(out.get("sl"), out.get("tp")):
        raise FriendCopyError("naked", request=out)
    return out


def protection_sync_plan(
    *,
    challenge_ticket: Any,
    demo_ticket: Any,
    demo_symbol: str,
    demo_sl: Any,
    demo_tp: Any,
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Plan a copier SLTP from the ask. A missing side stays missing."""

    position = {"sl": demo_sl, "tp": demo_tp, "symbol": demo_symbol, "ticket": demo_ticket}
    seed = dict(event or {})
    if seed.get("ticket") in (None, "") and challenge_ticket not in (None, ""):
        seed["ticket"] = challenge_ticket
    if not seed.get("symbol") and demo_symbol:
        seed["symbol"] = demo_symbol
    contract = resolve_copy_contract(seed, trade_record, ask=ask)
    base = {
        "action": "sync_protection",
        "ticket": challenge_ticket,
        "demo_ticket": demo_ticket,
        "order_send": False,
        "agent_order_send": False,
        "place_on_challenge": False,
        "choice": (contract.extra or {}).get("choice"),
        "side": contract.side,
    }
    if not contract.ok:
        base.update({"ok": False, "reason": contract.reason, "error": (contract.extra or {}).get("error")})
        return base
    if not protection_is_missing(position):
        base.update(
            {
                "ok": True,
                "reason": "already_protected",
                "sl": contract.sl,
                "tp": contract.tp,
            }
        )
        return base
    request = copy_sltp_request(
        symbol=demo_symbol or contract.symbol,
        position=int(demo_ticket),
        sl=float(contract.sl),
        tp=float(contract.tp),
        magic=(contract.extra or {}).get("magic"),
        ask=ask,
    )
    base.update(
        {
            "ok": True,
            "reason": "protect_ready",
            "lots": contract.lots,
            "sl": contract.sl,
            "tp": contract.tp,
            "request": request,
            "copier_owned": True,
        }
    )
    return base


def feedback_label_row(
    *,
    ticket: Any,
    symbol: str,
    timing: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Close-loop LABEL only. ``place`` stays false."""

    return {
        "schema": FEEDBACK_SCHEMA,
        "verb": "LABEL",
        "place": False,
        "never_place": True,
        "timing": timing,
        "ticket": ticket,
        "symbol": symbol,
        "source_login": CHALLENGE_LOGIN,
        "note": note,
        "agent_order_send": False,
        "place_on_challenge": False,
    }


def print_plan(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ns: str = "friend_a_f5_minimal",
    login: int = 0,
    price: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Observer dry plan. The open request uses the same ask. This function does not send."""

    contract = resolve_copy_contract(
        event,
        trade_record,
        ns=ns,
        login=login,
        price=price,
        ask=ask,
    )
    payload: dict[str, Any] = contract.as_dict()
    payload["ns"] = ns
    payload["demo_login"] = login
    payload["agent_may_mutate_friend"] = (contract.extra or {}).get("agent_may_mutate_friend")
    payload["friend_copy_on"] = (contract.extra or {}).get("friend_copy_on")
    if contract.ok and price is not None and contract.lots is not None and contract.sl is not None and contract.tp is not None and contract.side:
        open_req = copy_open_request(
            symbol=contract.symbol,
            side=str(contract.side),
            volume=float(contract.lots),
            sl=float(contract.sl),
            tp=float(contract.tp),
            comment=contract.comment,
            price=float(price),
            deviation=(contract.extra or {}).get("deviation"),
            magic=(contract.extra or {}).get("magic"),
            ask=ask,
        )
        payload["open_request"] = open_req
        payload["open_request_has_sl_tp"] = "sl" in open_req and "tp" in open_req
        payload["feedback"] = feedback_label_row(
            ticket=contract.ticket,
            symbol=contract.symbol,
            note="copy_plan",
        )
    if contract.reason == "challenge_source_closed":
        payload["close_friend_only"] = True
        payload["never_flatten_challenge"] = True
        payload["source_closed_from"] = (contract.extra or {}).get("source_closed_from")
    payload["order_send"] = False
    return payload


# Measured 2026-09-21 Challenge fills. Used by CLI --print-plan when no files given.
MEASURED_CHALLENGE_FILLS: tuple[dict[str, Any], ...] = (
    {
        "event": {
            "kind": "fill",
            "ticket": 294088097,
            "symbol": "EURUSD",
            "side": "short",
            "source_login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
        },
        "trade_record": {
            "ticket": 294088097,
            "symbol": "EURUSD",
            "side": "SHORT",
            "execution": {
                "broker_position_sl": 1.14844,
                "broker_position_tp": 1.14697,
                "request": {"volume": 0.87},
                "result": {"volume": 0.87},
            },
            "instrumentation": {"gtos_live_flow_execution": {"lots_placed": 0.87}},
            "volume_min": 0.01,
            "volume_step": 0.01,
        },
        "ns": "friend_a_f5_minimal",
        "login": 0,
        "price": 1.14795,
        "demo_ticket": 546460735,
    },
    {
        "event": {
            "kind": "fill",
            "ticket": 294092360,
            "symbol": "NZDUSD",
            "side": "short",
            "source_login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
        },
        "trade_record": {
            "ticket": 294092360,
            "symbol": "NZDUSD",
            "side": "SHORT",
            "execution": {
                "broker_position_sl": 0.57318,
                "broker_position_tp": 0.57169,
                "request": {"volume": 1.75},
                "result": {"volume": 1.75},
            },
            "instrumentation": {"gtos_live_flow_execution": {"lots_placed": 1.75}},
            "volume_min": 0.01,
            "volume_step": 0.01,
        },
        "ns": "ftmo_redacted_account_f5_minimal",
        "login": 0,
        "price": 0.57267,
        "demo_ticket": 546460779,
    },
)
