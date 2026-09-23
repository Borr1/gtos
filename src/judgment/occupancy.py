"""Challenge-true occupancy extras from the deal tape.

Not the 2-stop COUNT. That stays ``closed[]`` only (envelope integer).
The labels and the parameters are the System One return for this state.
The call is ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only a Noul, a Choice, or a Score. Prior outcomes are on
every ask. An empty answer, a tie, or an error leaves that return unset.
A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from .bars import normalize_symbol

MODEL = "jev-1.13.0"

# Cluster names are the choice menu. Membership for a symbol is corr_cluster.
# world_state still iterates this name at import. The name has to exist or
# run_book dies. An empty map does not restore a planted symbol list.
BOOK_CLUSTERS = ("metals", "fx_major", "index", "crypto")
CORR_CLUSTER: dict[str, str] = {}
_CLUSTER_ORDER = BOOK_CLUSTERS + ("none",)
_REFUSAL_ORDER = ("none", "cost", "other")
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
_CLUSTER_CRITERIA = {
    "metals": "This symbol is in the metals cluster.",
    "fx_major": "This symbol is in the fx major cluster.",
    "index": "This symbol is in the index cluster.",
    "crypto": "This symbol is in the crypto cluster.",
    "none": "This symbol is not in a named cluster.",
}
_REFUSAL_CRITERIA = {
    "none": "No named last refusal.",
    "cost": "The named last refusal is cost.",
    "other": "The named last refusal is something else.",
}


@dataclass(frozen=True)
class TapeTrade:
    ticket: str
    symbol: str
    sleeve: str
    open_utc: datetime
    close_utc: datetime | None
    still_open: bool


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


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
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return value
        if number == number and number in (90000.0, 110000.0):
            return None
        return value
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


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is not a decision."""

    if not isinstance(probs, Mapping) or not probs:
        return None
    names = tuple(order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if p != p or p in (float("inf"), float("-inf")):
            continue
        seen = True
        if best_p is None or p > best_p:
            best = str(name)
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    local = _unique(probs, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs, order)
    except Exception:
        agreed = local
    if agreed != local:
        return None
    if local not in order:
        return None
    return str(local)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    number = _finite(raw)
    if number is not None:
        return number
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The Score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
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
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = order or (tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ())
    if isinstance(probs, Mapping) and probs and _unique(probs, menu or None) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the facts. A score may sit between them."""

    found: list[float] = []
    for key, value in dict(facts or {}).items():
        if _limit_key(str(key)):
            continue
        number = _finite(value)
        if number is not None and number not in (90000.0, 110000.0):
            found.append(number)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
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
    instructions = _scrub_text(text)
    criteria = [str(item) for item in levels] if levels else list(_BETWEEN)
    body = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = list(criteria)
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


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


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=questions)
    except Exception:
        payload["prior_outcomes"] = []
    try:
        from .jev_client import evaluate

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
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _run(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    _remember(asked.get("state") or {}, rows)
    return out


def _clock(as_of_utc: datetime) -> datetime:
    if as_of_utc.tzinfo is None:
        return as_of_utc.replace(tzinfo=timezone.utc)
    return as_of_utc.astimezone(timezone.utc)


def _iso(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    return _clock(moment).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ticket(this_ticket: Any) -> str | None:
    if this_ticket in (None, ""):
        return None
    text = str(this_ticket).strip()
    return text or None


def _trade_rows(trades: Sequence[TapeTrade], this: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trade in trades:
        if this and trade.ticket == this:
            continue
        rows.append(
            {
                "ticket": trade.ticket,
                "symbol": trade.symbol,
                "sleeve": trade.sleeve,
                "open_utc": _iso(trade.open_utc),
                "close_utc": _iso(trade.close_utc),
                "still_open": bool(trade.still_open),
            }
        )
    return rows


def _measured_minutes(
    trades: Sequence[TapeTrade],
    *,
    symbol: str,
    as_of: datetime,
    this: str | None,
) -> float | None:
    """Elapsed minutes on the named tape. Evidence for the ask, not the return."""

    want = normalize_symbol(symbol)
    last: datetime | None = None
    for trade in trades:
        if trade.symbol != want:
            continue
        if this and trade.ticket == this:
            continue
        closed = trade.close_utc
        if closed is None or closed > as_of:
            continue
        if last is None or closed > last:
            last = closed
    if last is None:
        return None
    return (as_of - last).total_seconds() / 60.0


def _sym_qid(symbol: str, used: dict[str, str]) -> str:
    cleaned = "".join(ch for ch in symbol if ch.isalnum() or ch == "_") or "symbol"
    qid = f"occ_open_{cleaned}"
    if qid in used and used[qid] != symbol:
        qid = f"{qid}_{len(used)}"
    used[qid] = symbol
    return qid


def _jsonish(value: Any) -> Any:
    cleaned = _scrub(value)
    if cleaned is None or isinstance(cleaned, (str, int, float, bool)):
        return cleaned
    if isinstance(cleaned, datetime):
        return _iso(cleaned)
    if isinstance(cleaned, list):
        return [_jsonish(item) for item in cleaned]
    if isinstance(cleaned, dict):
        return {str(key): _jsonish(item) for key, item in cleaned.items()}
    return _scrub_text(str(cleaned))


def parse_utc(raw: Any) -> datetime | None:
    if raw is None or raw == "":
        return None
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def trades_from_dicts(rows: Iterable[dict[str, Any]], *, stamp) -> list[TapeTrade]:
    """``stamp`` is challenge_as_of-compatible: dict → datetime."""
    out: list[TapeTrade] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        open_utc = stamp(row)
        close_probe = {
            "open_time_utc": row.get("close_time_utc") or row.get("close_time"),
            "open_time_server": row.get("close_time_server"),
        }
        close_utc = stamp(close_probe) if close_probe["open_time_utc"] else None
        ticket = str(row.get("ticket") or row.get("candidate_id") or "")
        symbol = str(row.get("symbol") or "")
        if not ticket or not symbol or open_utc is None:
            continue
        out.append(
            TapeTrade(
                ticket=ticket,
                symbol=normalize_symbol(symbol),
                sleeve=str(row.get("sleeve") or row.get("comment") or row.get("tag") or ""),
                open_utc=open_utc,
                close_utc=close_utc,
                still_open=bool(row.get("still_open") or row.get("_kind") == "open"),
            )
        )
    return out


def _blank_occupancy(source: str) -> dict[str, Any]:
    return {
        "symbol_open": None,
        "already_placed_today": None,
        "cluster_placed_today": None,
        "isolated_reentry_legal": None,
        "minutes_since_flat": None,
        "corr_hold_named": None,
        "isolated_reentry_minutes": None,
        "loop_bound": None,
        "open_allowed": None,
        "occupancy_source": source,
    }


def occupancy_at(
    trades: Sequence[TapeTrade] | None,
    *,
    symbol: str,
    as_of_utc: datetime,
    this_ticket: Any = None,
    kind: str | None = None,
    still_open: bool = False,
) -> dict[str, Any]:
    """Occupancy at as_of. Each label is the return. A miss stays unset.

    A missing tape is a fact on the card. It does not decide crowded.
    ``open_allowed`` is how many tickets can be open. This module does not cap the tape.
    """

    absent = trades is None
    source = "deal_tape_absent" if absent else "challenge_deals"
    try:
        as_of = _clock(as_of_utc)
        this = _ticket(this_ticket)
        try:
            want = normalize_symbol(symbol) if str(symbol or "").strip() else ""
        except Exception:
            want = ""
        measured = None
        if not absent and want:
            measured = _measured_minutes(trades, symbol=want, as_of=as_of, this=this)
        state: dict[str, Any] = {
            "symbol": want or None,
            "symbol_absent": not bool(want),
            "as_of_utc": _iso(as_of),
            "this_ticket": this,
            "kind": kind,
            "still_open": bool(still_open),
            "holding": kind == "open" or bool(still_open),
            "tape_absent": absent,
            "trades": [] if absent else _trade_rows(trades, this),
            "tape_rows": 0 if absent else len(trades),
            "model": MODEL,
        }
        if measured is not None:
            state["measured_minutes_since_flat"] = measured
        levels = _levels(state)
        pack: dict[str, Any] = {}
        pack.update(_noul_question(
            "occ_symbol_open",
            "Is this symbol open on the named deal tape at as_of? "
            "Count another live ticket or this holding. "
            "An empty answer leaves it unset. Do not send an order.",
            "The symbol is open at as_of.",
            "The symbol is not open at as_of.",
        ))
        pack.update(_noul_question(
            "occ_already_placed_today",
            "Was this symbol already placed on this decision day on the named tape? "
            "An empty answer leaves it unset. Do not send an order.",
            "This symbol was already placed today.",
            "This symbol was not already placed today.",
        ))
        pack.update(_noul_question(
            "occ_cluster_placed_today",
            "Was this symbol's cluster already placed on this decision day on the named tape? "
            "An empty answer leaves it unset. Do not send an order.",
            "The cluster was already placed today.",
            "The cluster was not already placed today.",
        ))
        pack.update(_noul_question(
            "occ_isolated_reentry_legal",
            "Is an isolated re-entry legal for this symbol at as_of? "
            "The minutes parameter is the score on occ_isolated_reentry_minutes. "
            "An empty answer leaves it unset. Do not send an order.",
            "Isolated re-entry is legal.",
            "Isolated re-entry is not legal.",
        ))
        pack.update(_noul_question(
            "occ_corr_hold",
            "Is another same-cluster symbol open at as_of? "
            "An empty answer leaves it unset. Do not send an order.",
            "Another same-cluster symbol is open.",
            "No other same-cluster symbol is open.",
        ))
        pack.update(_score_question(
            "occ_minutes_since_flat",
            _score_text("minutes since this symbol was flat"),
            levels,
        ))
        pack.update(_score_question(
            "occ_isolated_reentry_minutes",
            _score_text("isolated-reentry minutes parameter"),
            levels,
        ))
        pack.update(_score_question(
            "occ_loop",
            _score_text("loop bound for how many named tape rows this label covers"),
            levels,
        ))
        pack.update(_score_question(
            "occ_open_allowed",
            _score_text("how many tickets can be open on this state"),
            levels,
        ))
        spec = (
            ("symbol_open", "noul", "occ_symbol_open", ("true", "false")),
            ("already_placed_today", "noul", "occ_already_placed_today", ("true", "false")),
            ("cluster_placed_today", "noul", "occ_cluster_placed_today", ("true", "false")),
            ("isolated_reentry_legal", "noul", "occ_isolated_reentry_legal", ("true", "false")),
            ("corr_hold_named", "noul", "occ_corr_hold", ("true", "false")),
            ("minutes_since_flat", "score", "occ_minutes_since_flat", None),
            ("isolated_reentry_minutes", "score", "occ_isolated_reentry_minutes", None),
            ("loop_bound", "score", "occ_loop", None),
            ("open_allowed", "score", "occ_open_allowed", None),
        )
        got = _run(state, pack, spec)
    except Exception:
        return _blank_occupancy(source)
    row = _blank_occupancy(source)
    row.update(got)
    row["occupancy_source"] = source
    return row


def corr_cluster(symbol: str | None) -> str | None:
    """The cluster is the unique highest choice. A miss stays unset."""

    want = ""
    if symbol is not None and str(symbol).strip():
        try:
            want = normalize_symbol(symbol)
        except Exception:
            want = ""
    state = {"symbol": want or None, "symbol_absent": not bool(want), "model": MODEL}
    pack = _choice_question(
        "occ_cluster",
        "Which named cluster is this symbol in? "
        "The option you return is that cluster. "
        "An empty answer or a tie is not a cluster. "
        "Do not send an order.",
        _CLUSTER_CRITERIA,
    )
    try:
        got = _run(state, pack, (("cluster", "choice", "occ_cluster", _CLUSTER_ORDER),))
    except Exception:
        return None
    cluster = got.get("cluster")
    if cluster not in _CLUSTER_ORDER:
        return None
    return str(cluster)


def corr_hold_at(
    trades: Sequence[TapeTrade] | None,
    *,
    symbol: str,
    as_of_utc: datetime,
    this_ticket: Any = None,
) -> bool | float | None:
    """Same-cluster hold is the Noul. A missing tape is a fact. A miss stays unset."""

    absent = trades is None
    try:
        as_of = _clock(as_of_utc)
        this = _ticket(this_ticket)
        try:
            want = normalize_symbol(symbol) if str(symbol or "").strip() else ""
        except Exception:
            want = ""
        state: dict[str, Any] = {
            "symbol": want or None,
            "symbol_absent": not bool(want),
            "as_of_utc": _iso(as_of),
            "this_ticket": this,
            "tape_absent": absent,
            "trades": [] if absent else _trade_rows(trades, this),
            "tape_rows": 0 if absent else len(trades),
            "model": MODEL,
        }
        levels = _levels(state)
        pack: dict[str, Any] = {}
        pack.update(_noul_question(
            "occ_corr_hold",
            "Is another same-cluster symbol open at as_of? "
            "An empty answer leaves it unset. Do not send an order.",
            "Another same-cluster symbol is open.",
            "No other same-cluster symbol is open.",
        ))
        pack.update(_choice_question(
            "occ_cluster",
            "Which named cluster is this symbol in? "
            "The option you return is that cluster. "
            "An empty answer or a tie is not a cluster. "
            "Do not send an order.",
            _CLUSTER_CRITERIA,
        ))
        pack.update(_score_question(
            "occ_corr_loop",
            _score_text("loop bound for how many named tape rows this hold covers"),
            levels,
        ))
        got = _run(
            state,
            pack,
            (
                ("hold", "noul", "occ_corr_hold", ("true", "false")),
                ("cluster", "choice", "occ_cluster", _CLUSTER_ORDER),
                ("loop_bound", "score", "occ_corr_loop", None),
            ),
        )
    except Exception:
        return None
    hold = got.get("hold")
    if hold is True or hold is False:
        return hold
    return _finite(hold)


def classify_refusal(raw: Any) -> str | None:
    """The refusal class is the choice. Empty text is a fact, not a class."""

    text = str(raw or "").strip()
    state = {"text": _scrub_text(text), "text_absent": not bool(text), "model": MODEL}
    pack = _choice_question(
        "occ_refusal_class",
        "Classify this named refusal text. Do not invent a refusal. "
        "The option you return is that class. "
        "An empty answer or a tie is not a class. "
        "Do not send an order.",
        _REFUSAL_CRITERIA,
    )
    try:
        got = _run(
            state,
            pack,
            (("cls", "choice", "occ_refusal_class", _REFUSAL_ORDER),),
        )
    except Exception:
        return None
    cls = got.get("cls")
    if cls not in _REFUSAL_ORDER:
        return None
    return str(cls)


def refusal_tape(slate: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Named last-refusal rows from a Challenge slate. Do not invent."""
    if not isinstance(slate, dict):
        return []
    rows: list[dict[str, Any]] = []
    for rec in slate.get("refusals") or []:
        if isinstance(rec, dict):
            rows.append(rec)
    skips = slate.get("skips")
    if isinstance(skips, dict):
        for rec in skips.get("recent") or []:
            if isinstance(rec, dict):
                rows.append(rec)
    for rec in slate.get("candidates") or []:
        if isinstance(rec, dict) and rec.get("last_refusal_class"):
            rows.append(rec)
    return rows


def last_refusal_class(
    refusals: Sequence[dict[str, Any]] | None,
    *,
    symbol: str | None,
    as_of_utc: datetime | None,
    named: Any = None,
) -> str | None:
    """The last refusal class is the choice. A miss stays unset."""

    named_text = str(named or "").strip()
    try:
        want = normalize_symbol(symbol) if symbol else None
        as_of = _clock(as_of_utc) if as_of_utc is not None else None
        rows = [_jsonish(rec) for rec in (refusals or []) if isinstance(rec, Mapping)]
        state: dict[str, Any] = {
            "symbol": want,
            "as_of_utc": _iso(as_of),
            "named": _scrub_text(named_text) if named_text else None,
            "named_absent": not bool(named_text),
            "refusals_absent": refusals is None,
            "refusals": rows,
            "tape_rows": len(rows),
            "model": MODEL,
        }
        levels = _levels(state)
        pack: dict[str, Any] = {}
        pack.update(_choice_question(
            "occ_last_refusal_class",
            "Classify the named last refusal on this tape. Do not invent a refusal. "
            "The option you return is that class. "
            "An empty answer or a tie is not a class. "
            "Do not send an order.",
            _REFUSAL_CRITERIA,
        ))
        pack.update(_score_question(
            "occ_refusal_window",
            _score_text("refusal-window minutes"),
            levels,
        ))
        pack.update(_score_question(
            "occ_refusal_loop",
            _score_text("loop bound for how many named refusal rows this class covers"),
            levels,
        ))
        got = _run(
            state,
            pack,
            (
                ("cls", "choice", "occ_last_refusal_class", _REFUSAL_ORDER),
                ("window", "score", "occ_refusal_window", None),
                ("loop_bound", "score", "occ_refusal_loop", None),
            ),
        )
    except Exception:
        return None
    cls = got.get("cls")
    if cls not in _REFUSAL_ORDER:
        return None
    return str(cls)


def _blank_book(source: str) -> dict[str, Any]:
    return {
        "clusters_open": None,
        "book_open_n": None,
        "n_clusters_open": None,
        "symbols_open": None,
        "loop_bound": None,
        "open_allowed": None,
        "occupancy_source": source,
    }


def occupancy_book_at(
    trades: Sequence[TapeTrade] | None,
    *,
    as_of_utc: datetime,
    this_ticket: Any = None,
) -> dict[str, Any]:
    """Book occupancy. Each count is the score. A miss stays unset.

    ``open_allowed`` is how many tickets can be open. It is not applied as a cap.
    The closed[] count stays the envelope integer in two_stop.
    """

    absent = trades is None
    source = "deal_tape_absent" if absent else "challenge_deals"
    try:
        as_of = _clock(as_of_utc)
        this = _ticket(this_ticket)
        symbols: list[str] = []
        if not absent:
            for trade in trades:
                if this and trade.ticket == this:
                    continue
                if trade.symbol and trade.symbol not in symbols:
                    symbols.append(trade.symbol)
        state: dict[str, Any] = {
            "as_of_utc": _iso(as_of),
            "this_ticket": this,
            "tape_absent": absent,
            "trades": [] if absent else _trade_rows(trades, this),
            "symbols": list(symbols),
            "tape_rows": 0 if absent else len(trades),
            "model": MODEL,
        }
        levels = _levels(state)
        pack: dict[str, Any] = {}
        spec: list[tuple[str, str, str, tuple[str, ...] | None]] = []
        for cluster in BOOK_CLUSTERS:
            qid = f"occ_book_{cluster}"
            pack.update(_score_question(
                qid,
                _score_text(f"open count for the {cluster} cluster"),
                levels,
            ))
            spec.append((cluster, "score", qid, None))
        pack.update(_score_question(
            "occ_book_open_n",
            _score_text("open count across the named clusters"),
            levels,
        ))
        pack.update(_score_question(
            "occ_n_clusters_open",
            _score_text("how many named clusters are open"),
            levels,
        ))
        pack.update(_score_question(
            "occ_book_loop",
            _score_text("loop bound for how many named tape rows this book label covers"),
            levels,
        ))
        pack.update(_score_question(
            "occ_book_open_allowed",
            _score_text("how many tickets can be open on this state"),
            levels,
        ))
        spec.append(("book_open_n", "score", "occ_book_open_n", None))
        spec.append(("n_clusters_open", "score", "occ_n_clusters_open", None))
        spec.append(("loop_bound", "score", "occ_book_loop", None))
        spec.append(("open_allowed", "score", "occ_book_open_allowed", None))
        used: dict[str, str] = {}
        symbol_qids: list[tuple[str, str]] = []
        for symbol in symbols:
            qid = _sym_qid(symbol, used)
            pack.update(_noul_question(
                qid,
                f"Is {symbol} open on this named tape at as_of? "
                "An empty answer leaves it unset. Do not send an order.",
                f"{symbol} is open at as_of.",
                f"{symbol} is not open at as_of.",
            ))
            symbol_qids.append((symbol, qid))
            spec.append((qid, "noul", qid, ("true", "false")))
        got = _run(state, pack, tuple(spec))
    except Exception:
        return _blank_book(source)
    counts: dict[str, float] = {}
    for cluster in BOOK_CLUSTERS:
        number = _finite(got.get(cluster))
        if number is not None:
            counts[cluster] = number
    open_names: list[str] = []
    symbols_open: list[str] | None = None
    if symbols:
        symbols_open = open_names
        for symbol, qid in symbol_qids:
            value = got.get(qid)
            if value is True:
                open_names.append(symbol)
            elif value is not False:
                symbols_open = None
                break
    return {
        "clusters_open": counts if counts else None,
        "book_open_n": _finite(got.get("book_open_n")),
        "n_clusters_open": _finite(got.get("n_clusters_open")),
        "symbols_open": symbols_open,
        "loop_bound": _finite(got.get("loop_bound")),
        "open_allowed": _finite(got.get("open_allowed")),
        "occupancy_source": source,
    }
