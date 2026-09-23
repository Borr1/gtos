"""Host-tape occupancy + governor extras for live gold_state.

Shadow already fills occupancy from Challenge deals. Live haircut / A1
assembled geometry+cost only, so ``completeness.occupancy`` stayed false
and ``governor`` stayed empty.

Chair splice: call ``host_occupancy_governor`` once per intent (after
``cost_skip``, before haircut / A1) from account_state / open book /
closed[] / decision.governor. This module does not place, remint, flatten,
or send.

Each decision on that splice, including each parameter, is the System One
return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only a Noul, a Choice,
or a Score. Prior outcomes are attached on the ask, and the return is
stored for the next ask.

An empty answer, a tie, or an error leaves that return unset. It does not
restore a constant. A floor and a baseline are not a question. Named host
fields stay facts on the state. Does not invent DXY, yields, or a clock offset.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from .occupancy import occupancy_at, parse_utc, trades_from_dicts
from .two_stop import closed_rows, load_siblings_doc, occupancy_from_closed

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_REASON_ORDER = ("allow", "stand", "cap", "block")
_ADMISSION_ORDER = ("keep", "kill")
_REASON_CRITERIA = {
    "allow": "New entries are allowed on this host state.",
    "stand": "This host state stands aside.",
    "cap": "This host state caps size.",
    "block": "New entries are blocked on this host state.",
}
_ADMISSION_CRITERIA = {
    "keep": "This admission is keep.",
    "kill": "This admission is kill.",
}
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_SPEC = (
    ("allow_new", "noul", "host_allow_new", ("true", "false")),
    ("cap_mult", "score", "host_cap_mult", None),
    ("reason", "choice", "host_reason", _REASON_ORDER),
    ("realized_today_pct", "score", "host_realized_today_pct", None),
    ("open_risk_pct", "score", "host_open_risk_pct", None),
    ("never_place", "noul", "host_never_place", ("true", "false")),
    ("never_remint", "noul", "host_never_remint", ("true", "false")),
    ("never_flatten", "noul", "host_never_flatten", ("true", "false")),
    ("admission", "choice", "host_admission", _ADMISSION_ORDER),
    ("admission_parameter", "score", "host_admission_parameter", None),
    ("apply", "noul", "host_apply", ("true", "false")),
)

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

_OPEN_KEYS = ("opens", "open_positions", "positions", "open_book")
_CLOSED_KEYS = ("closed", "just_closed_siblings", "siblings_doc", "closed_doc")
_ALLOW_KEYS = ("allow_new", "allow_new_entries", "new_entries_allowed")
_CAP_KEYS = ("cap_mult", "size_cap_multiplier")
_OPEN_RISK_KEYS = ("open_risk_pct",)
_REALIZED_KEYS = ("realized_today_pct",)
_REASON_KEYS = ("reason",)
_ROW_ATTRS = (
    "ticket",
    "symbol",
    "sleeve",
    "comment",
    "tag",
    "open_time_utc",
    "open_time",
    "time_utc",
    "time",
    "close_time_utc",
    "close_time",
    "closed_utc",
    "still_open",
    "_kind",
)


def _as_utc(raw: Any) -> datetime | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        dt = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if isinstance(raw, (int, float)) and raw > 1_000_000_000:
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    return parse_utc(raw)


def host_stamp(row: Mapping[str, Any] | None) -> datetime | None:
    """Named UTC / datetime / unix-as-UTC only. None if the row has no clock."""
    if not isinstance(row, Mapping):
        return None
    for key in (
        "open_time_utc",
        "time_utc",
        "last_seen_utc",
        "first_seen_utc",
        "open_time",
        "time",
    ):
        stamped = _as_utc(row.get(key))
        if stamped is not None:
            return stamped
    return None


def _as_row(item: Any) -> dict[str, Any] | None:
    if item is None:
        return None
    if isinstance(item, Mapping):
        row = dict(item)
    else:
        row = {}
        for name in _ROW_ATTRS:
            if hasattr(item, name):
                row[name] = getattr(item, name)
    ticket = row.get("ticket") or row.get("candidate_id")
    symbol = row.get("symbol")
    if ticket in (None, "") or not symbol:
        return None
    if not row.get("sleeve"):
        comment = str(row.get("comment") or row.get("tag") or "")
        if comment.startswith(("F5:", "W7:")):
            comment = comment[3:]
        row["sleeve"] = comment
    return row


def _normalize_opens(opens: Any) -> list[dict[str, Any]] | None:
    if opens is None:
        return None
    if isinstance(opens, Mapping) and not any(k in opens for k in ("ticket", "symbol")):
        for key in _OPEN_KEYS:
            if opens.get(key) is not None:
                return _normalize_opens(opens.get(key))
        return None
    if not isinstance(opens, (list, tuple)):
        item = _as_row(opens)
        return [item] if item else []
    out: list[dict[str, Any]] = []
    for item in opens:
        row = _as_row(item)
        if row is None:
            continue
        if row.get("still_open") is None and not (
            row.get("close_time_utc") or row.get("close_time") or row.get("closed_utc")
        ):
            row["still_open"] = True
            row.setdefault("_kind", "open")
        out.append(row)
    return out


def _as_closed_doc(closed_doc: Any) -> dict[str, Any] | None:
    if closed_doc is None:
        return None
    if isinstance(closed_doc, list):
        return {"closed": [r for r in closed_doc if isinstance(r, dict)], "two_stop_source": "closed[]"}
    if not isinstance(closed_doc, Mapping):
        return None
    if isinstance(closed_doc.get("closed"), list):
        return dict(closed_doc)
    for key in _CLOSED_KEYS:
        nested = closed_doc.get(key)
        if nested is None or nested is closed_doc:
            continue
        got = _as_closed_doc(nested)
        if got is not None:
            return got
    return None


def _closed_trade_rows(closed_doc: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not closed_doc:
        return []
    out: list[dict[str, Any]] = []
    for row in closed_rows(closed_doc):
        rec = dict(row)
        close = rec.get("close_time_utc") or rec.get("close_time") or rec.get("closed_utc")
        rec["close_time_utc"] = close
        if not rec.get("open_time_utc") and not rec.get("open_time"):
            rec["open_time_utc"] = close
        rec["still_open"] = False
        rec["_kind"] = rec.get("_kind") or "close"
        out.append(rec)
    return out


def opens_from_account_state(account_state: Any) -> list[dict[str, Any]] | None:
    if account_state is None:
        return None
    return _normalize_opens(account_state)


def live_occupancy_for(
    symbol: Any,
    as_of: Any,
    ticket: Any,
    opens: Any,
    closed_doc: Any,
    *,
    sleeve: Any = None,
) -> dict[str, Any]:
    """Wrap occupancy_at + occupancy_from_closed over the host tape.

    ``opens`` is the live open book (or account_state bag). ``closed_doc``
    is ``just_closed_siblings.json`` / ``closed[]``. Missing tape stays
    visible (None fields). Does not invent a sibling stop.
    """
    as_of_utc = _as_utc(as_of) or datetime.now(timezone.utc)
    closed = _as_closed_doc(closed_doc)
    open_rows = _normalize_opens(opens)
    if open_rows is None and closed is None:
        occ = occupancy_at(
            None,
            symbol=str(symbol or "XAUUSD"),
            as_of_utc=as_of_utc,
            this_ticket=ticket,
        )
    else:
        rows: list[dict[str, Any]] = list(open_rows or []) + _closed_trade_rows(closed)
        trades = trades_from_dicts(rows, stamp=host_stamp)
        occ = occupancy_at(
            trades,
            symbol=str(symbol or "XAUUSD"),
            as_of_utc=as_of_utc,
            this_ticket=ticket,
        )
        occ["occupancy_source"] = "host_tape"
    occ.update(
        occupancy_from_closed(
            closed,
            sleeve=str(sleeve or ""),
            as_of_utc=as_of_utc,
            symbol=str(symbol) if symbol else None,
        )
    )
    return occ


def _as_mapping(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return dict(obj)
    out: dict[str, Any] = {}
    for name in (
        *_ALLOW_KEYS,
        *_CAP_KEYS,
        *_OPEN_RISK_KEYS,
        *_REALIZED_KEYS,
        *_REASON_KEYS,
        "governor",
    ):
        if hasattr(obj, name):
            out[name] = getattr(obj, name)
    return out


def _first(payload: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, item in raw.items():
        number = _finite(item)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _present_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among probabilities that were actually returned.

    A missing probability is not zero. A tie is not a decision.
    """

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A label alone is not a choice."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    local = _present_unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probabilities, order)
    except Exception:
        picked = local
    if local is None or picked is None or str(picked) != local:
        return None
    if str(picked) not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is None:
            return None
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    if block.get("score") is None:
        return None
    return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probabilities = _probabilities(block)
    menu = order or tuple(probabilities)
    if probabilities and _present_unique(probabilities, menu) is None and menu:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(value: Any, seen: set[int] | None = None) -> None:
        if seen is None:
            seen = set()
        if isinstance(value, Mapping):
            ident = id(value)
            if ident in seen:
                return
            seen.add(ident)
            for key, item in value.items():
                if _limit_key(str(key)):
                    continue
                walk(item, seen)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            ident = id(value)
            if ident in seen:
                return
            seen.add(ident)
            for item in value:
                walk(item, seen)
            return
        number = _finite(value)
        if number is not None:
            found.append(number)

    walk(dict(facts or {}))
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(item) for key, item in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, body["criteria"])
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = dict(body["criteria"])
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, text, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": yes, "false": no},
        }
    }


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "A floor and a baseline are not a question. "
        "Do not send an order."
    )


def _questions(facts: Mapping[str, Any] | None) -> dict[str, Any]:
    """One ask. The menu names what an answer may return. It does not decide."""

    levels = _levels(facts)
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        "host_allow_new",
        "Are new entries allowed on this host state? "
        "The noul you return is that allowance. "
        "An empty noul leaves it unset. "
        "Do not send an order.",
        "New entries are allowed.",
        "New entries are not allowed.",
    ))
    pack.update(_score_question(
        "host_cap_mult",
        _score_text("size-cap parameter"),
        levels,
    ))
    pack.update(_choice_question(
        "host_reason",
        "Which governor reason is this host state? "
        "The option with the single highest probability is the reason. "
        "An empty answer or a tie leaves the reason unset. "
        "Do not send an order.",
        _REASON_CRITERIA,
    ))
    pack.update(_score_question(
        "host_realized_today_pct",
        _score_text("realized-today parameter"),
        levels,
    ))
    pack.update(_score_question(
        "host_open_risk_pct",
        _score_text("open-risk parameter"),
        levels,
    ))
    pack.update(_noul_question(
        "host_never_place",
        "Is never-place stamped for this host state? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "Do not send an order.",
        "Never-place is stamped.",
        "Never-place is not stamped.",
    ))
    pack.update(_noul_question(
        "host_never_remint",
        "Is never-remint stamped for this host state? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "Do not send an order.",
        "Never-remint is stamped.",
        "Never-remint is not stamped.",
    ))
    pack.update(_noul_question(
        "host_never_flatten",
        "Is never-flatten stamped for this host state? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "Do not send an order and do not flatten.",
        "Never-flatten is stamped.",
        "Never-flatten is not stamped.",
    ))
    pack.update(_choice_question(
        "host_admission",
        "Which admission is this host state, keep or kill? "
        "The option with the single highest probability is the admission. "
        "An empty answer or a tie leaves the admission unset. "
        "Do not send an order.",
        _ADMISSION_CRITERIA,
    ))
    pack.update(_score_question(
        "host_admission_parameter",
        _score_text("admission parameter"),
        levels,
    ))
    pack.update(_noul_question(
        "host_apply",
        "Is apply stamped for this host admission? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "Do not send an order.",
        "Apply is stamped.",
        "Apply is not stamped.",
    ))
    return pack


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = list(_LOCAL_OUTCOMES)
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        from .jev_client import evaluate

        questions = _anchor_questions(questions, payload)
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
    }


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({"spot": str(key), "value": value, "error": error})
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            _LOCAL_OUTCOMES.append({"spot": str(key), "value": value, "error": error})
            return


def _read(answers: Mapping[str, Any] | None, error: Any) -> tuple[dict[str, Any], list[tuple[str, Any, str | None]]]:
    got = answers if isinstance(answers, Mapping) else {}
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in _SPEC:
        block = got.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    return out, rows


def _decide(state: Mapping[str, Any]) -> dict[str, Any]:
    """One post. A miss leaves each field unset."""

    questions = _questions(state)
    allowed = {"noul", "choice", "score"}
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed
        for block in questions.values()
    ):
        blank, _rows = _read({}, "question_pack_fail")
        return blank
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    out, rows = _read(answers, asked.get("error"))
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else {}
    _remember(posted, rows)
    return out


def _governor_slice(decided: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "allow_new": decided.get("allow_new"),
        "cap_mult": decided.get("cap_mult"),
        "reason": decided.get("reason"),
        "realized_today_pct": decided.get("realized_today_pct"),
        "open_risk_pct": decided.get("open_risk_pct"),
    }


def _admission_slice(decided: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "choice": decided.get("admission"),
        "parameter": decided.get("admission_parameter"),
        "apply": decided.get("apply"),
    }


def _named_governor(
    *,
    decision: Any = None,
    account_state: Any = None,
    governor: Any = None,
    governor_state: Any = None,
) -> dict[str, Any]:
    """Host fields as facts. They are not the decision."""

    merged: dict[str, Any] = {}
    merged.update(_as_mapping(account_state))
    merged.update(_as_mapping(governor_state))
    dec = _as_mapping(decision)
    if dec.get("governor") is not None:
        merged.update(_as_mapping(dec.get("governor")))
    else:
        merged.update({k: v for k, v in dec.items() if k != "governor"})
    merged.update(_as_mapping(governor))
    if not merged:
        return {}
    return {
        "named_allow_new": _first(merged, _ALLOW_KEYS),
        "named_cap_mult": _first(merged, _CAP_KEYS),
        "named_reason": _first(merged, _REASON_KEYS),
        "named_realized_today_pct": _first(merged, _REALIZED_KEYS),
        "named_open_risk_pct": _first(merged, _OPEN_RISK_KEYS),
    }


def _host_state(
    named: Mapping[str, Any],
    *,
    symbol: Any = None,
    as_of: Any = None,
    ticket: Any = None,
    sleeve: Any = None,
    namespace: str | None = None,
    login: Any = None,
    overlays_applied: Any = None,
    occupancy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "model": MODEL,
        "login": login if login not in (None, "") else CHALLENGE_LOGIN,
        "namespace": namespace or CHALLENGE_NS,
        "symbol": None if symbol in (None, "") else str(symbol),
        "as_of": None if as_of in (None, "") else str(as_of),
        "ticket": None if ticket in (None, "") else str(ticket),
        "sleeve": None if sleeve in (None, "") else str(sleeve),
        "overlays_applied": overlays_applied,
    }
    state.update(dict(named))
    if isinstance(occupancy, Mapping):
        state["occupancy"] = dict(occupancy)
    return state


def governor_from_host(
    *,
    decision: Any = None,
    account_state: Any = None,
    governor: Any = None,
    governor_state: Any = None,
) -> dict[str, Any]:
    """Governor fields are the System One return. A miss stays unset."""

    named = _named_governor(
        decision=decision,
        account_state=account_state,
        governor=governor,
        governor_state=governor_state,
    )
    decided = _decide(_host_state(named))
    return _governor_slice(decided)


def host_occupancy_governor(
    *,
    symbol: Any,
    as_of: Any,
    ticket: Any = None,
    sleeve: Any = None,
    account_state: Any = None,
    opens: Any = None,
    closed_doc: Any = None,
    decision: Any = None,
    governor: Any = None,
    governor_state: Any = None,
    namespace: str | None = None,
    login: Any = None,
    overlays_applied: Any = None,
) -> dict[str, Any]:
    """One Chair call: occupancy + governor extras for haircut / A1.

    Loads live ``closed[]`` when ``closed_doc`` is omitted. Never mutates
    the book. Prefer this over wholesale-copying ``book_owner.py``.
    Governor, admission, and the never-place stamps are the return on one
    ask. A miss leaves that field unset. This call does not send.
    """
    opens_here = opens if opens is not None else opens_from_account_state(account_state)
    closed_here = closed_doc if closed_doc is not None else _as_closed_doc(account_state)
    if closed_here is None:
        closed_here = load_siblings_doc(namespace=namespace or CHALLENGE_NS)
    occupancy = live_occupancy_for(
        symbol,
        as_of,
        ticket,
        opens_here,
        closed_here,
        sleeve=sleeve,
    )
    named = _named_governor(
        decision=decision,
        account_state=account_state,
        governor=governor,
        governor_state=governor_state,
    )
    decided = _decide(
        _host_state(
            named,
            symbol=symbol,
            as_of=as_of,
            ticket=ticket,
            sleeve=sleeve,
            namespace=namespace,
            login=login,
            overlays_applied=overlays_applied,
            occupancy=occupancy if isinstance(occupancy, Mapping) else None,
        )
    )
    return {
        "occupancy": occupancy,
        "governor": _governor_slice(decided),
        "admission": _admission_slice(decided),
        "never_place": decided.get("never_place"),
        "never_remint": decided.get("never_remint"),
        "never_flatten": decided.get("never_flatten"),
    }


_BOUND_CARD = None

_SKIP_FACT_KEYS = frozenset({
    "login",
    "magic",
    "model",
    "prior_outcomes",
    "reason_ids",
    "scoped_xau_names",
    "windows",
    "order_send",
    "flatten",
    "namespace",
    "ns",
    "api_url",
    "schema",
    "questions",
    "answers",
    "criteria",
    "instructions",
})
_PRICE_KEYS = frozenset({
    "entry",
    "stop",
    "target",
    "entry_price",
    "stop_loss",
    "take_profit",
    "take_profit_1",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "deal_final",
    "event_stop_now",
    "inv_entry",
    "inv_stop",
})
_PRICE_QIDS = frozenset({
    "inv_entry",
    "inv_stop",
    "entry_stop_parameter",
    "entry_target_parameter",
    "host_named_sl",
})
_WEIGHT_QIDS = frozenset({
    "geometry_vs_tape",
    "session_fitness",
    "level_respect",
    "flow_alignment",
    "persistence",
})
_UNIX_QIDS = frozenset({"gfull_start", "gfull_end", "cutoff_unix"})
_COUNT_LISTS = frozenset({
    "events",
    "rows",
    "candidates",
    "peers",
    "sites",
    "stubs",
    "recipe_rows",
    "recipes",
})
_ORDINAL_EXACT = frozenset({
    "wall_pressure",
    "fill_realism",
    "paper_live_parity",
    "protection_still_earns",
    "session_liquidity",
})


def _bind_card(card):
    global _BOUND_CARD
    if isinstance(card, Mapping):
        _BOUND_CARD = card


def _finite_fact(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _ordinal_words(qid):
    name = str(qid)
    if name == "session_liquidity":
        return ("thin liquidity", "ordinary liquidity", "deep liquidity")
    if name == "include_depth" or name.startswith("include_"):
        return ("hide", "short", "long", "full")
    if name in _ORDINAL_EXACT or name.endswith("_quality"):
        return ("poor", "ordinary", "clean")
    return None


def _qid_unit(qid):
    name = str(qid).lower()
    if _ordinal_words(name):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_QIDS:
        return "price"
    if name.endswith("_s") or "second" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or "percent" in name:
        return "pct"
    if name.endswith("_r") or "spread_r" in name:
        return "r"
    if name in _WEIGHT_QIDS or "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or "_tilt" in name
        or name.endswith("_tilt")
    ):
        return "mult"
    if name in _UNIX_QIDS or name.endswith("_unix"):
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net"):
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or "nth" in name
        or "candidate" in name
        or "occupancy" in name
        or "corr_window" in name
        or name.endswith("_shadow")
        or "shadow" in name
    ):
        return "count"
    return ""


def _key_unit(key):
    name = str(key).lower()
    if name in _SKIP_FACT_KEYS or name.startswith("_"):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_KEYS:
        return "price"
    if name.endswith("_seconds") or name.endswith("_s") or "delta_s" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or name.endswith("_percent") or "percent" in name:
        return "pct"
    if name.endswith("_r") or name in {"spread_r", "locked_r"}:
        return "r"
    if "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or name.endswith("_tilt")
        or name in {"tilt", "shadow_tilt"}
    ):
        return "mult"
    if name.endswith("_unix") or name in {"gfull_start", "gfull_end", "cutoff_unix"}:
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net") or name in {"equity", "balance", "profit", "pnl", "open_pnl", "net"}:
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or name.endswith("_hits")
        or name.endswith("_anchors")
        or "candidate" in name
        or "nth" in name
        or name == "occupancy_world"
    ):
        return "count"
    return ""


def _fact_label(key, used):
    text = "the " + str(key) + " named on this card"
    if text not in used:
        used.add(text)
        return text
    index = 2
    while True:
        alt = "another " + str(key) + " named on this card (" + str(index) + ")"
        if alt not in used:
            used.add(alt)
            return alt
        index += 1


def _walk_facts(value, key, unit, pairs, labels, seen):
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        for child_key, child in value.items():
            if not isinstance(child_key, str) or child_key.lower() in _SKIP_FACT_KEYS:
                continue
            _walk_facts(child, child_key, unit, pairs, labels, seen)
        return
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        if unit == "count" and str(key).lower() in _COUNT_LISTS:
            pairs.append((_fact_label("count of " + str(key), labels), float(len(value))))
        for item in value:
            if isinstance(item, Mapping):
                _walk_facts(item, key, unit, pairs, labels, seen)
        return
    if _key_unit(key) != unit:
        return
    number = _finite_fact(value)
    if number is None:
        return
    pairs.append((_fact_label(key, labels), number))


def _distance_gap(card, pairs, labels):
    left = None
    right = None

    def walk(node, seen):
        nonlocal left, right
        if not isinstance(node, Mapping):
            return
        ident = id(node)
        if ident in seen:
            return
        seen.add(ident)
        if left is None:
            left = _finite_fact(node.get("left"))
        if right is None:
            right = _finite_fact(node.get("right"))
        for child in node.values():
            if isinstance(child, Mapping):
                walk(child, seen)

    if isinstance(card, Mapping):
        walk(card, set())
    if left is None or right is None:
        return
    pairs.append((_fact_label("stop gap", labels), abs(left - right)))


def _anchors_for(unit, card):
    if not unit or not isinstance(card, Mapping):
        return []
    pairs = []
    labels = set()
    if unit == "weight":
        try:
            from .jev_questions import weight_anchors

            for label, number in weight_anchors(card):
                pairs.append((str(label), number))
                labels.add(str(label))
        except Exception:
            pairs = []
            labels = set()
    _walk_facts(card, "", unit, pairs, labels, set())
    if unit == "distance":
        _distance_gap(card, pairs, labels)
    return pairs


def _pending_score(qid, instructions, words=None):
    text = "" if instructions is None else str(instructions)
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return None
        if cleaned is None:
            return None
        if isinstance(cleaned, str):
            text = cleaned
    text = text.strip()
    if not text:
        return None
    for guard_name in ("_limit_key", "_skip_key", "_blocked", "_blocked_text", "_bad_text"):
        guard = globals().get(guard_name)
        if not callable(guard):
            continue
        try:
            if guard(str(qid)) or guard(text):
                return None
        except Exception:
            return None
    row = {"type": "score", "instructions": text}
    if words:
        kept = [str(item).strip() for item in words if str(item).strip()]
        if len(kept) >= 2:
            row["_words"] = kept
    return row


def _anchor_questions(questions, card):
    """Rebuild each Score from this card. Fewer than two levels drops that Score."""

    if not isinstance(questions, Mapping):
        return questions
    _bind_card(card)
    out = {}
    for key, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "") != "score":
            out[key] = block
            continue
        name = str(key)
        words = block.get("_words")
        if not isinstance(words, (list, tuple)):
            words = _ordinal_words(name)
        try:
            if words:
                from .jev_questions import ordinal_question

                built = ordinal_question(name, str(block.get("instructions") or ""), words)
            else:
                from .jev_questions import amount_question

                built = amount_question(
                    name,
                    str(block.get("instructions") or ""),
                    _anchors_for(_qid_unit(name), card),
                )
        except Exception:
            continue
        row = built.get(name) if isinstance(built, dict) else None
        if not isinstance(row, dict) or not row.get("criteria"):
            continue
        if block.get("ignore_if"):
            row = dict(row)
            row["ignore_if"] = block.get("ignore_if")
        out[key] = row
    return out


def _snap_ordinal(block, n_levels):
    try:
        count = int(n_levels)
    except (TypeError, ValueError):
        return None
    if count < 2:
        return None
    try:
        from .jev_questions import ordinal_index

        return ordinal_index(block, count)
    except Exception:
        return None


def _snap_if_ordinal(qid, block, fallback):
    words = _ordinal_words(qid)
    if not words:
        return fallback
    return _snap_ordinal(block, len(words))
