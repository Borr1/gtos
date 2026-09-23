"""Challenge host events.jsonl — trail + calendar honesty. Never invents HIGH.

Reads the landed ``events_since_*.jsonl`` writer tape. Does not add a
NEWS_PROTOCOL endpoint. The path search is the reader. A set-but-missing
env path stays missing, and a live read does not swap in the lab tape.

The trail column, the named stop, the differ noul, the trail epsilon,
the news status, the news event, the news source, the news row, the
count, the window, and the named-stamp preference are the System One
return for that state. One ask: ``jev_client.evaluate`` with model
``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only a Noul, a Choice, or a
Score. Prior outcomes are attached on that ask and the return is stored
for the next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset. A floor and a baseline are not a question. This module does not
send an order.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "events_since_20260915.jsonl"
)

# Challenge f5-live writer tape. Lab DEFAULT_EVENTS is not a live candidate.
LIVE_HOST_EVENT_CANDIDATES = (
    REPO_ROOT / "shadow_logs" / "f5_minimal" / "operator" / "events.jsonl",
    Path(r"C:host-local/redacted_host/repo/shadow_logs/f5_minimal/operator/events.jsonl"),
)
HOST_EVENTS_ENV = ("GTOS_JEV_HOST_EVENTS", "GTOS_CHALLENGE_EVENTS")

_EVENTS_CACHE: dict[str, tuple[int, int, list[dict[str, Any]]]] = {}

MODEL = "jev-1.13.0"
_NEWS_EVENTS = ("news_t15_pending_cancel", "news_t60_expiry_reeval")
_SOURCE_ORDER = ("challenge_host_news_writer", "unassembled")
_SOURCE_CRITERIA = {
    "challenge_host_news_writer": "This inventory is the challenge host news writer.",
    "unassembled": "This inventory is not assembled from that writer.",
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
_NOUL_ORDER = ("true", "false")


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_utc(raw: Any) -> datetime | None:
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


def iter_events(path: Path | None = None) -> Iterable[dict[str, Any]]:
    dest = path if path is not None else DEFAULT_EVENTS
    if not dest.is_file():
        return
    with dest.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def load_host_events(path: Path | None = None) -> list[dict[str, Any]]:
    dest = Path(path) if path is not None else DEFAULT_EVENTS
    if not dest.is_file():
        return []
    try:
        st = dest.stat()
        key = str(dest)
        hit = _EVENTS_CACHE.get(key)
        if hit is not None and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
            return hit[2]
        rows = list(iter_events(dest))
        _EVENTS_CACHE[key] = (st.st_mtime_ns, st.st_size, rows)
        return rows
    except OSError:
        return list(iter_events(dest))


def resolve_host_events_path(*, live: bool = False) -> Path | None:
    """Env, then known Challenge host writer, else lab tape for research.

    ``live=True`` never falls back to ``DEFAULT_EVENTS``. A set-but-missing
    env path stays missing so unread is not silently swapped for lab.
    The search is the reader. It is not the inventory decision.
    """
    for name in HOST_EVENTS_ENV:
        raw = (os.environ.get(name) or "").strip()
        if not raw:
            continue
        dest = Path(raw)
        return dest if dest.is_file() else None
    if live:
        for dest in LIVE_HOST_EVENT_CANDIDATES:
            if dest.is_file():
                return dest
        return None
    return DEFAULT_EVENTS


def coerce_as_of_utc(raw: Any) -> datetime | None:
    if isinstance(raw, datetime):
        return raw.astimezone(timezone.utc) if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    return _parse_utc(raw)


def as_of_from_state(state: dict[str, Any] | None, fallback: Any = None) -> datetime | None:
    clock = (state or {}).get("clock") or {}
    return coerce_as_of_utc(clock.get("as_of_utc")) or coerce_as_of_utc(fallback)


def last_stop_now(
    events: Iterable[dict[str, Any]] | None,
    ticket: Any,
) -> float | None:
    """Last f5_stop_move.stop_now for this ticket. The printed stop is the tape fact."""
    if events is None or ticket is None:
        return None
    want = str(ticket)
    last = None
    for row in events:
        if row.get("event") != "f5_stop_move":
            continue
        if str(row.get("ticket") or "") != want:
            continue
        value = _f(row.get("stop_now"))
        if value is not None:
            last = value
    return last


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    lowered = cleaned.lower()
    kept: list[str] = []
    index = 0
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        kept.append(cleaned[index])
        index += 1
    return "".join(kept)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
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


def _probs(block: Any, order: Sequence[str] | None = None) -> dict[str, float]:
    """Finite probabilities only. A missing probability is not zero."""

    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    names = tuple(order) if order else tuple(str(name) for name in raw)
    out: dict[str, float] = {}
    for name in names:
        if name not in raw:
            continue
        number = _finite(raw.get(name))
        if number is not None:
            out[str(name)] = number
    return out


def _unique(probs: Mapping[str, float] | None, order: Sequence[str] | None) -> str | None:
    """Unique highest probability. An empty map or a tie is not a decision."""

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
        number = _finite(probs.get(name))
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = str(name)
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: Sequence[str]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = _probs(block, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(block.get("probabilities"), tuple(order))
    except Exception:
        picked = None
    if picked not in order:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


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
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if "score" not in block:
        return None
    return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: Sequence[str] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: Sequence[str] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = _probs(block, order)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    cleaned = {str(key): _scrub_text(str(value)) for key, value in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": instructions, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str) -> dict[str, Any]:
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
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves it unset. "
        "This ask does not transmit an order."
    )


def _keep_questions(pack: Mapping[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key, block in pack.items():
        name = str(key)
        if _limit_key(name) or not isinstance(block, Mapping):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        kept[name] = dict(block)
    return kept


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    asked = _keep_questions(questions)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=asked)
    except Exception:
        loaded = []
    if loaded is None:
        loaded = []
    payload["prior_outcomes"] = loaded
    try:
        from .jev_client import evaluate

        asked = _anchor_questions(asked, payload)
        receipt = evaluate(
            payload,
            questions=asked,
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


def _iso(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    stamp = moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def named_final_sl(
    *,
    deal_final: Any = None,
    event_stop_now: Any = None,
) -> float | None:
    """The named stop is the returned score. A miss does not copy either column."""

    deal = _finite(deal_final)
    event = _finite(event_stop_now)
    if deal is None and event is None:
        return None
    criteria: dict[str, str] = {}
    order: list[str] = []
    state: dict[str, Any] = {"model": MODEL}
    if deal is not None:
        state["deal_final"] = deal
        order.append("deal")
        criteria["deal"] = "The named stop is the deal column on this state."
    if event is not None:
        state["event_stop_now"] = event
        order.append("event_stop")
        criteria["event_stop"] = "The named stop is the monitor stop on this state."
    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "host_trail_source",
            "Which column is the named final stop for this state? "
            "The prices on this state are facts. "
            "The option you return is the column. "
            "An empty answer or a tie leaves it unset. "
            "This ask does not transmit an order.",
            criteria,
        )
    )
    pack.update(_score_question("host_named_sl", _score_text("named final stop")))
    try:
        got = _run(
            state,
            pack,
            (
                ("source", "choice", "host_trail_source", tuple(order)),
                ("named_sl", "score", "host_named_sl", None),
            ),
        )
    except Exception:
        return None
    return _finite(got.get("named_sl"))


def sl_differs(left: Any, right: Any, *, eps: float | None = None) -> bool | float | None:
    """Whether the stops differ is the Noul. The epsilon is the Score on this ask."""

    a = _finite(left)
    b = _finite(right)
    if a is None or b is None:
        return None
    state: dict[str, Any] = {"left": a, "right": b, "model": MODEL}
    passed = _finite(eps)
    if passed is not None:
        state["passed_eps"] = passed
    pack: dict[str, Any] = {}
    pack.update(
        _noul_question(
            "host_trail_differs",
            "Do these two stops differ for this state? "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "The two stops differ.",
            "The two stops do not differ.",
        )
    )
    pack.update(_score_question("host_trail_eps", _score_text("trail epsilon")))
    try:
        got = _run(
            state,
            pack,
            (
                ("differs", "noul", "host_trail_differs", _NOUL_ORDER),
                ("eps", "score", "host_trail_eps", None),
            ),
        )
    except Exception:
        return None
    differs = got.get("differs")
    if differs is True or differs is False:
        return differs
    return _finite(differs)


def _news_blank() -> dict[str, Any]:
    return {
        "host_news_inventory_status": None,
        "host_news_n_in_window": None,
        "host_news_event": None,
        "host_news_ts_utc": None,
        "host_news_source": None,
        "host_news_window_s": None,
        "host_news_named_prefer_s": None,
    }


def _row_id(index: int, row: Mapping[str, Any], seen: dict[str, int]) -> str:
    event = str(row.get("event") or "event")
    stamp = str(row.get("ts_utc") or index)
    raw = f"{event}_{stamp}"
    token = "".join(ch if ch.isalnum() else "_" for ch in raw)
    count = seen.get(token, 0)
    seen[token] = count + 1
    if count:
        token = f"{token}_{count}"
    return token or f"row_{index}"


def _news_facts(
    events: Iterable[dict[str, Any]],
    as_of: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for raw in events:
        if not isinstance(raw, dict):
            continue
        event = str(raw.get("event") or "")
        if event not in _NEWS_EVENTS:
            continue
        moment = _parse_utc(raw.get("ts_utc") or raw.get("checked_at_utc") or raw.get("logged_at_utc"))
        if moment is None:
            continue
        status = raw.get("inventory_status")
        status_text = str(status).strip() if status not in (None, "") else None
        item = {
            "event": event,
            "inventory_status": status_text,
            "n_events_in_window": _finite(raw.get("n_events_in_window")),
            "ts_utc": _iso(moment),
            "delta_s": abs((moment - as_of).total_seconds()),
        }
        item["row_id"] = _row_id(len(rows), item, seen)
        rows.append(item)
    return rows


def _distinct(rows: Sequence[Mapping[str, Any]], key: str) -> tuple[str, ...]:
    found: list[str] = []
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value or value in found:
            continue
        if _limit_key(value):
            continue
        found.append(value)
    return tuple(found)


def news_inventory_at(
    events: Iterable[dict[str, Any]] | None,
    as_of_utc: datetime | None,
    *,
    path: Path | str | None = None,
) -> dict[str, Any]:
    """Host news inventory at as-of. Each field is the return. A miss stays unset.

    The stamp time is the clock on the row the choice names. Unread tape
    stays unset. This does not invent a status.
    """

    if events is None or as_of_utc is None:
        return _news_blank()
    as_of = as_of_utc.astimezone(timezone.utc) if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    rows = _news_facts(events, as_of)
    if not rows:
        return _news_blank()
    state: dict[str, Any] = {
        "model": MODEL,
        "as_of_utc": _iso(as_of),
        "rows": rows,
        "path": None if path is None else str(path),
    }
    pack: dict[str, Any] = {}
    spec: list[tuple[str, str, str, tuple[str, ...] | None]] = []
    statuses = _distinct(rows, "inventory_status")
    if statuses:
        pack.update(
            _choice_question(
                "host_news_inventory_status",
                "Which inventory status is named for this as-of on the host news rows? "
                "The rows are facts. "
                "The option you return is the status. "
                "An empty answer or a tie leaves it unset. "
                "This ask does not transmit an order.",
                {name: f"The inventory status on this tape is {name}." for name in statuses},
            )
        )
        spec.append(("host_news_inventory_status", "choice", "host_news_inventory_status", statuses))
    events_named = _distinct(rows, "event")
    if events_named:
        pack.update(
            _choice_question(
                "host_news_event",
                "Which host news event is the one for this as-of? "
                "The option you return is that event. "
                "An empty answer or a tie leaves it unset. "
                "This ask does not transmit an order.",
                {name: f"The host news event is {name}." for name in events_named},
            )
        )
        spec.append(("host_news_event", "choice", "host_news_event", events_named))
    pack.update(
        _choice_question(
            "host_news_source",
            "Where does this inventory come from for this state? "
            "The option you return is the source. "
            "An empty answer or a tie leaves it unset. "
            "This ask does not transmit an order.",
            _SOURCE_CRITERIA,
        )
    )
    spec.append(("host_news_source", "choice", "host_news_source", _SOURCE_ORDER))
    row_order = tuple(str(row.get("row_id") or "") for row in rows)
    row_criteria = {
        str(row.get("row_id")): (
            f"event {row.get('event')} status {row.get('inventory_status')} "
            f"at {row.get('ts_utc')} delta_s {row.get('delta_s')}"
        )
        for row in rows
        if row.get("row_id")
    }
    pack.update(
        _choice_question(
            "host_news_row",
            "Which host news row carries the stamp time for this as-of? "
            "The option you return names that row. "
            "An empty answer or a tie leaves the stamp time unset. "
            "This ask does not transmit an order.",
            row_criteria,
        )
    )
    spec.append(("host_news_row", "choice", "host_news_row", row_order))
    pack.update(_score_question("host_news_n_in_window", _score_text("count of host news events in the window")))
    pack.update(_score_question("host_news_window_s", _score_text("news window in seconds")))
    pack.update(
        _score_question(
            "host_news_named_prefer_s",
            _score_text("named-stamp preference in seconds"),
        )
    )
    spec.extend(
        (
            ("host_news_n_in_window", "score", "host_news_n_in_window", None),
            ("host_news_window_s", "score", "host_news_window_s", None),
            ("host_news_named_prefer_s", "score", "host_news_named_prefer_s", None),
        )
    )
    try:
        got = _run(state, pack, tuple(spec))
    except Exception:
        return _news_blank()
    out = _news_blank()
    for key in out:
        if key == "host_news_ts_utc":
            continue
        if key in got:
            out[key] = got.get(key)
    picked = got.get("host_news_row")
    named = next((row for row in rows if row.get("row_id") == picked), None)
    if named is not None:
        out["host_news_ts_utc"] = named.get("ts_utc")
    return out


def news_inventory_extra(
    as_of_utc: datetime | None,
    path: Path | str | None = None,
    *,
    live: bool = False,
) -> dict[str, Any]:
    """Host news inventory for this as-of. The fields are the return.

    Missing tape stays unset. Does not invent a status.
    """
    dest: Path | None
    if path is not None and str(path).strip():
        dest = Path(path)
    else:
        dest = resolve_host_events_path(live=live)
    if dest is None or not dest.is_file():
        return news_inventory_at(None, as_of_utc)
    return news_inventory_at(load_host_events(dest), as_of_utc, path=dest)


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
