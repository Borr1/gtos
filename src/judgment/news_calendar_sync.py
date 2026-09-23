"""Repair = sync rows FROM the live spine. Never invent. Never overwrite June.

THIS repo ``data/news_calendar.json`` is the June 2026-05-31 week of record.
VPS ``data/news_calendar.json`` is a stale stub (2026-09-07). The live HIGH
spine is ``f5_high_calendar`` / ``official_high_spine``. Frozen
``news_calendar.json.frozen-20260821`` is history (different schema), not a
drop-in merge.

Tickets copy from a stub only on exact scheduled_utc + name match. That match
is the copy law. Spine rows, the source path, and the source hash are facts.

Every decision on this sync, including each parameter, is one System One
return. The call is ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only a Noul, a Choice, or a Score. Prior outcomes are attached
on the ask, and the return is stored for the next ask.

A Choice is the unique highest probability. A Score is the returned number
and may sit between levels. A Noul is a bool or a probability. An empty
answer, a tie, or an error leaves that field unset and does not restore a
constant. The loop bound does not drop a spine row. Floor and baseline are
not a question.

``invented`` stays false: this module does not invent rows. The June path
still raises. ``write`` is the caller's gate. This module does not send and
does not add ``order_send``. Judge code stays unable to send.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.news_calendar.v1"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

REPO_ROOT = Path(__file__).resolve().parents[2]
JUNE_WEEK_OF_RECORD = REPO_ROOT / "data" / "news_calendar.json"
DEFAULT_SPINE = REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260916.json"
DEFAULT_OUT = REPO_ROOT / "data" / "news" / "news_calendar_f5_synced_from_spine.json"
FROZEN_ARCHIVE_NAME = "news_calendar.json.frozen-20260821"

_STATUS_ORDER = ("synced_from_high_spine", "withheld")
_IMPACT_ORDER = ("HIGH", "MEDIUM", "LOW", "omit")
_CLOCK_ORDER = ("spine_updated", "withhold")
_ROLE_ORDER = ("history_not_drop_in", "drop_in")

_STATUS_CRITERIA = {
    "synced_from_high_spine": "This sync carries the spine rows forward.",
    "withheld": "This sync withholds the status.",
}
_IMPACT_CRITERIA = {
    "HIGH": "The impact on this sync is high.",
    "MEDIUM": "The impact on this sync is medium.",
    "LOW": "The impact on this sync is low.",
    "omit": "This sync leaves the impact unset.",
}
_CLOCK_CRITERIA = {
    "spine_updated": "Carry the spine's own updated clock.",
    "withhold": "Leave the sync clocks unset.",
}
_ROLE_CRITERIA = {
    "history_not_drop_in": "The frozen archive is history, not a drop-in merge.",
    "drop_in": "The frozen archive is a drop-in merge.",
}

_DECISIONS = (
    ("sync_status", "status", "choice", _STATUS_ORDER),
    ("sync_impact", "impact", "choice", _IMPACT_ORDER),
    ("sync_clock", "clock", "choice", _CLOCK_ORDER),
    ("frozen_archive_role", "frozen_archive_role", "choice", _ROLE_ORDER),
    ("sync_official_high", "official_high", "noul", ()),
    ("june_week_untouched", "june_week_of_record_untouched", "noul", ()),
    ("sync_state_sufficient", "state_sufficient", "noul", ()),
    ("sync_parameter", "parameter", "score", ()),
    ("sync_loop_bound", "loop_bound", "score", ()),
)

_SKIP_PARTS = ("floor", "baseline")
_SECRET_PARTS = ("api_key", "token", "secret", "authorization", "password")
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

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


class JuneWeekOfRecordError(RuntimeError):
    """Raised when a write would clobber the June operator calendar."""


def refuse_june_overwrite(path: Path) -> None:
    if path.resolve() == JUNE_WEEK_OF_RECORD.resolve():
        raise JuneWeekOfRecordError(
            "refusing to overwrite June week-of-record data/news_calendar.json"
        )


def _load_json(path: Path) -> dict[str, Any] | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_name(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("event") or row.get("title") or "").strip()


def _scheduled(row: dict[str, Any]) -> str:
    raw = str(row.get("scheduled_utc") or row.get("datetime_utc") or "").strip()
    if raw.endswith("Z") or "+" in raw[10:]:
        return raw.replace("+00:00", "Z") if raw.endswith("+00:00") else raw
    date = str(row.get("date") or "").strip()
    tod = str(row.get("time_utc") or "").strip()
    if date and tod:
        return f"{date}T{tod}:00Z" if len(tod) <= 5 else f"{date}T{tod}Z"
    return raw


def _tickets_from_stub(stub_events: list[dict[str, Any]], scheduled: str, name: str) -> list | None:
    for row in stub_events:
        if _scheduled(row) == scheduled and _event_name(row) == name:
            tickets = row.get("tickets")
            if isinstance(tickets, list):
                return tickets
            return None
    return None


def _skip_key(key: str) -> bool:
    low = str(key).lower()
    return any(part in low for part in _SKIP_PARTS) or any(part in low for part in _SECRET_PARTS)


def _blocked_text(text: str) -> bool:
    low = text.lower()
    if any(part in low for part in _SKIP_PARTS):
        return True
    return any(token.lower() in low for token in _BANNED_TEXT)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _plain(value: Any, seen: set[int] | None = None) -> Any:
    """Facts for the ask. Floor, baseline, and secrets stay off the post."""

    if seen is None:
        seen = set()
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if _blocked_text(value):
            return None
        return value
    if isinstance(value, (int, float)):
        number = _number(value) if isinstance(value, float) else value
        if number in (90000, 90000.0, 110000, 110000.0):
            return None
        return number
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _skip_key(name):
                continue
            out[name] = _plain(item, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        return [_plain(item, seen) for item in value]
    return None


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, item in raw.items():
        number = _number(item)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _present_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among probabilities that were actually returned."""

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

    if isinstance(block, dict) and block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    local = _present_unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = local
    if local is None or agreed is None or str(agreed) != local:
        return None
    return local


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict):
        return _number(block)
    if block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "score" in block and block.get("score") is not None:
        raw = block.get("score")
    elif "value" in block and block.get("value") is not None:
        raw = block.get("value")
    else:
        return None
    number = _number(raw)
    if number is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = number
    if parsed is None or parsed != number:
        return None
    return number


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _skip_key(str(key)) and not _blocked_text(str(text))
    }
    return {qid: body}


def _score_question(qid: str, instructions: str, criteria: list[str]) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, instructions, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes, on this state.",
                "false": "No, on this state.",
            },
        }
    }


def _between(measured: list[float]) -> list[str]:
    levels = [
        "below the levels on this state",
        "between the levels on this state",
        "above the levels on this state",
    ]
    for number in sorted(set(measured)):
        if number in (90000.0, 110000.0):
            continue
        levels.append(format(number, ".10g"))
    return levels


def _measured_levels(measured: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []
    for value in dict(measured or {}).values():
        number = _number(value)
        if number is not None:
            found.append(number)
    return _between(found)


def sync_questions(measured: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One ask. The menu names what an answer may return. It does not decide."""

    levels = _measured_levels(measured)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "sync_status",
        "Which status is this spine sync? "
        "The option with the single highest probability is the status. "
        "An empty answer or a tie leaves the status unset. "
        "This question does not send.",
        _STATUS_CRITERIA,
    ))
    pack.update(_choice_question(
        "sync_impact",
        "Which impact is this spine sync? "
        "The option with the single highest probability is the impact. "
        "An empty answer or a tie leaves the impact unset. "
        "This question does not send.",
        _IMPACT_CRITERIA,
    ))
    pack.update(_choice_question(
        "sync_clock",
        "Which clock does this spine sync carry? "
        "The option with the single highest probability is the clock. "
        "An empty answer or a tie leaves the clocks unset. "
        "This question does not send.",
        _CLOCK_CRITERIA,
    ))
    pack.update(_choice_question(
        "frozen_archive_role",
        "Which role is the frozen archive on this sync? "
        "The option with the single highest probability is the role. "
        "An empty answer or a tie leaves the role unset. "
        "This question does not send.",
        _ROLE_CRITERIA,
    ))
    pack.update(_noul_question(
        "sync_official_high",
        "Is official high the mark on this sync? "
        "The noul you return is that mark. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "june_week_untouched",
        "Is the June week of record untouched by this sync? "
        "The noul you return is that mark. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "sync_state_sufficient",
        "Is this spine state sufficient to sync? "
        "The noul you return is that sufficiency. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        "sync_parameter",
        "The score you return is the parameter for this sync. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset. "
        "This question does not send.",
        levels,
    ))
    pack.update(_score_question(
        "sync_loop_bound",
        "The score you return is the loop bound for this sync. "
        "It may sit between the levels. "
        "An empty score leaves the bound unset. "
        "The bound does not drop a spine row. "
        "This question does not send.",
        levels,
    ))
    return pack


def _blank(error: str | None) -> dict[str, Any]:
    """Unset decisions. Invented stays the module law, not a restored answer."""

    row = {
        "status": None,
        "impact": None,
        "clock": None,
        "frozen_archive_role": None,
        "official_high": None,
        "june_week_of_record_untouched": None,
        "state_sufficient": None,
        "parameter": None,
        "loop_bound": None,
        "model": MODEL,
        "error": error,
    }
    return row


def _read_answers(answers: Mapping[str, Any]) -> dict[str, Any]:
    row = _blank(None)
    for qid, field, kind, order in _DECISIONS:
        block = answers.get(qid)
        if kind == "choice":
            row[field] = _choice(block, order)
        elif kind == "noul":
            row[field] = _noul(block)
        else:
            row[field] = _score(block)
    return row


def _local_priors(questions: Mapping[str, Any]) -> list[dict[str, Any]]:
    del questions
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors(questions)
        return
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else loaded


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    pairs = [(qid, row.get(field)) for qid, field, _kind, _order in _DECISIONS]
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
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else (None if error is None else str(error)),
            )
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    questions = _anchor_questions(questions, state)
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _spine_clock(payload: Mapping[str, Any]) -> str | None:
    raw = payload.get("updated_utc")
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text or _blocked_text(text):
        return None
    return text


def _as_of_text(raw: str) -> str:
    """Format a spine clock that already parses. An unparsed fact stays that fact."""

    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _selected_clocks(choice: str | None, spine_updated: str | None) -> tuple[str | None, str | None]:
    """Clocks come from the spine fact only when that Choice is returned."""

    if choice != "spine_updated" or not spine_updated:
        return None, None
    return spine_updated, _as_of_text(spine_updated)


def _row_flag(row: Mapping[str, Any], key: str) -> Any:
    if key not in row:
        return None
    return row.get(key)


def _fact_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for row in rows:
        scheduled = _scheduled(row)
        name = _event_name(row)
        if not scheduled or not name:
            continue
        facts.append({
            "scheduled_utc": scheduled,
            "name": name,
            "currency": str(row.get("currency") or "").strip().upper(),
            "event_type": row.get("event_type"),
            "source": row.get("source"),
            "past": row.get("past"),
            "time_certainty": row.get("time_certainty"),
            "beyond_horizon_14d": row.get("beyond_horizon_14d"),
            "row_impact": _row_flag(row, "impact"),
            "row_official_high": _row_flag(row, "official_high"),
        })
    return facts


def _event_from_row(row: dict[str, Any], tickets: list | None) -> dict[str, Any] | None:
    scheduled = _scheduled(row)
    name = _event_name(row)
    if not scheduled or not name:
        return None
    parsed = datetime.fromisoformat(scheduled.replace("Z", "+00:00")).astimezone(timezone.utc)
    return {
        "date": parsed.date().isoformat(),
        "time_utc": parsed.strftime("%H:%M"),
        "datetime_utc": parsed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scheduled_utc": parsed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": name,
        "name": name,
        "currency": str(row.get("currency") or "").strip().upper(),
        "event_type": row.get("event_type"),
        "source": row.get("source"),
        "past": row.get("past"),
        "time_certainty": row.get("time_certainty"),
        "beyond_horizon_14d": row.get("beyond_horizon_14d"),
        "tickets": tickets,
        "note": row.get("note"),
    }


def _ask_state(
    *,
    spine: Path,
    spine_updated: str | None,
    rows: list[dict[str, Any]],
    named: list[dict[str, Any]],
    stub_present: bool,
    n_stub_events: int,
    stub_tickets_used: int,
    write: bool,
) -> dict[str, Any]:
    relative = str(spine.relative_to(REPO_ROOT)) if spine.is_relative_to(REPO_ROOT) else str(spine)
    state = {
        "schema": SCHEMA,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "source_spine": relative,
        "spine_updated_utc": spine_updated,
        "n_spine_rows": len(rows),
        "n_named_rows": len(named),
        "stub_present": stub_present,
        "n_stub_events": n_stub_events,
        "stub_tickets_mapped": stub_tickets_used,
        "frozen_archive": FROZEN_ARCHIVE_NAME,
        "caller_write": bool(write),
        "rows": named,
    }
    plain = _plain(state)
    return plain if isinstance(plain, dict) else {}


def _stamp_events(events: list[dict[str, Any]], decided: Mapping[str, Any]) -> None:
    impact = decided.get("impact")
    official = decided.get("official_high")
    for event in events:
        event["impact"] = impact
        event["official_high"] = official


def sync_from_spine(
    *,
    spine_path: Path | None = None,
    stub_path: Path | None = None,
    out_path: Path | None = None,
    write: bool = True,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Sync spine rows into a snapshot.

    Row identity, tickets on an exact scheduled and name match, the source
    path, and the source hash are facts. Status, impact, clocks, archive
    role, official high, the June mark, sufficiency, the parameter, and the
    loop bound are the System One return. A miss leaves that field unset.
    The loop bound does not drop a spine row. This function does not send.
    """

    spine = Path(spine_path or DEFAULT_SPINE)
    dest = Path(out_path or DEFAULT_OUT)
    refuse_june_overwrite(dest)
    payload = _load_json(spine)
    if not isinstance(payload, dict):
        raise ValueError("spine must be an object")
    rows = [r for r in (payload.get("events") or []) if isinstance(r, dict)]
    stub_events: list[dict[str, Any]] = []
    stub_tickets_used = 0
    stub_present = False
    if stub_path is not None and Path(stub_path).is_file():
        refuse_june_overwrite(Path(stub_path))
        stub_payload = _load_json(Path(stub_path))
        if isinstance(stub_payload, dict):
            stub_present = True
            stub_events = [r for r in (stub_payload.get("events") or []) if isinstance(r, dict)]
    events: list[dict[str, Any]] = []
    for row in rows:
        scheduled = _scheduled(row)
        name = _event_name(row)
        if not scheduled or not name:
            continue
        tickets = _tickets_from_stub(stub_events, scheduled, name)
        if tickets:
            stub_tickets_used += 1
        event = _event_from_row(row, tickets)
        if event is not None:
            events.append(event)
    named = _fact_rows(rows)
    spine_updated = _spine_clock(payload)
    questions = sync_questions({
        "n_spine_rows": len(rows),
        "n_named_rows": len(named),
        "n_stub_events": len(stub_events),
        "stub_tickets_mapped": stub_tickets_used,
    })
    state = _ask_state(
        spine=spine,
        spine_updated=spine_updated,
        rows=rows,
        named=named,
        stub_present=stub_present,
        n_stub_events=len(stub_events),
        stub_tickets_used=stub_tickets_used,
        write=write,
    )
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a failed ask must not restore a constant
        decided = _blank(type(exc).__name__)
        _remember(state, decided)
        receipt = {}
    else:
        answers = receipt.get("answers")
        if not isinstance(answers, dict):
            answers = {}
        error = receipt.get("error") or receipt.get("skipped")
        if not answers and not error:
            error = "empty"
        if not answers:
            decided = _blank(None if error in (None, "") else str(error))
        else:
            decided = _read_answers(answers)
            if error not in (None, ""):
                decided["error"] = str(error)
        if receipt.get("model"):
            decided["model"] = receipt.get("model")
        _remember(state, decided)
    updated_utc, as_of_utc = _selected_clocks(decided.get("clock"), spine_updated)
    _stamp_events(events, decided)
    relative = str(spine.relative_to(REPO_ROOT)) if spine.is_relative_to(REPO_ROOT) else str(spine)
    snapshot = {
        "schema": SCHEMA,
        "status": decided.get("status"),
        "updated_utc": updated_utc,
        "as_of_utc": as_of_utc,
        "source_spine": relative,
        "source_spine_sha256": hashlib.sha256(spine.read_bytes()).hexdigest(),
        "n_events": len(events),
        "stub_tickets_mapped": stub_tickets_used,
        "invented": False,
        "june_week_of_record_untouched": decided.get("june_week_of_record_untouched"),
        "frozen_archive": FROZEN_ARCHIVE_NAME,
        "frozen_archive_role": decided.get("frozen_archive_role"),
        "clock": decided.get("clock"),
        "impact": decided.get("impact"),
        "official_high": decided.get("official_high"),
        "state_sufficient": decided.get("state_sufficient"),
        "parameter": decided.get("parameter"),
        "loop_bound": decided.get("loop_bound"),
        "model": decided.get("model") or MODEL,
        "error": decided.get("error"),
        "note": (
            "Rows are the spine facts. Tickets copy only on an exact scheduled "
            "and name match. Status, impact, clocks, archive role, official high, "
            "the June mark, sufficiency, the parameter, and the loop bound are "
            "the System One return. A miss leaves that field unset. "
            "Does not overwrite data/news_calendar.json."
        ),
        "events": events,
    }
    if write:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        snapshot["wrote"] = str(dest.relative_to(REPO_ROOT)) if dest.is_relative_to(REPO_ROOT) else str(dest)
    return snapshot


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
