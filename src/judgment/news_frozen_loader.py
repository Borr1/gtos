"""Load the host frozen news archive as HIGH history. Never invent.

Every decision on this load, including every parameter, is the System One
return for that state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only Noul, Choice, or Score.
Prior outcomes are attached on the ask, and the return is stored for the
next ask. A score may sit between levels. An empty answer, a tie, a
missing score, or an error leaves that field unset.

The archive freeze, the host sha256, and the byte length are facts of
that file. Rows at or after the freeze are not this loader's history.
A floor and a baseline are not a question. This module does not send.

``news_calendar.json.frozen-20260821`` is kind ``full_history_plus_scheduled``.
It is not ``gtos.news_calendar.v1`` and it is not ``NEWS_PROTOCOL``. Map rows
through the archive's own ``loader_contract.required_fields``. HIGH only
(the contract's ``current_should_skip_uses``). Do not merge MEDIUM / LOW /
mechanical WMR into the live stub. Do not overwrite the June week of record.

The 5.9 MB host blob is not committed. Lab reads
``data/news/lab/frozen_high_extract_20260821.json`` (HIGH rows with
``scheduled_utc`` strictly before the freeze stamp) or a local copy of the
full archive when present. Forward of the freeze belongs to
``f5_high_calendar`` / ``official_high_spine``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_DIR = REPO_ROOT / "data" / "news" / "lab"
DEFAULT_EXTRACT = LAB_DIR / "frozen_high_extract_20260821.json"
DEFAULT_POINTER = LAB_DIR / "FROZEN_NEWS_CALENDAR_POINTER.json"
FROZEN_ARCHIVE_NAME = "news_calendar.json.frozen-20260821"
FREEZE_UTC = datetime(2026, 8, 21, 12, 25, tzinfo=timezone.utc)
FROZEN_SHA256 = "98088a7dbbe8487db2136c6cd3fee25973d962f856a48844bf18f31fb3036649"
FROZEN_BYTES = 5_907_220
# Unset until a return names it. This attribute is not a stored decision.
NEWS_PROTOCOL_APPLIED = None
REQUIRED_FIELDS = ("date", "time_utc", "event", "impact", "currency")
G_FULL_START = datetime(2024, 4, 1, tzinfo=timezone.utc)
G_FULL_END = datetime(2026, 3, 30, tzinfo=timezone.utc)

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_CURRENCY_ORDER = ("usd_xau_all", "currencies_on_rows", "withhold")
_NOUL_ORDER = ("true", "false")
_CHOICE_IDS = ("frozen_currency",)
_SCORE_IDS = ("apply_persist", "gfull_start", "gfull_end", "cutoff_unix")
_NOUL_IDS = ("news_protocol_applied", "invented", "june_week_untouched")
_DECISION_IDS = _CHOICE_IDS + _SCORE_IDS + _NOUL_IDS
_FILE_DECISION_KEYS = (
    "NEWS_PROTOCOL_APPLIED",
    "invented",
    "june_week_of_record_untouched",
    "apply_persist",
    "gfull_start",
    "gfull_end",
    "cutoff_unix",
    "cutoff_utc",
    "frozen_currency",
)
_LIMIT_PARTS = ("floor", "baseline")
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
_SECRET_PARTS = ("api_key", "apikey", "authorization", "secret", "password", "token")
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


class FrozenArchiveError(RuntimeError):
    """Raised when a write would invent rows or clobber June."""


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def event_dt(row: dict[str, Any]) -> datetime | None:
    parsed = _parse_iso(str(row.get("scheduled_utc") or row.get("datetime_utc") or ""))
    if parsed is not None:
        return parsed
    date = str(row.get("date") or "").strip()
    tod = str(row.get("time_utc") or row.get("time") or "").strip()
    if date and tod:
        return _parse_iso(f"{date}T{tod}:00Z" if len(tod) <= 5 else f"{date}T{tod}Z")
    return None


def _required_fields(payload: Mapping[str, Any]) -> tuple[str, ...] | None:
    """Fields the archive contract names. A missing list stays missing."""

    contract = payload.get("loader_contract") or {}
    if not isinstance(contract, Mapping):
        return None
    named = contract.get("required_fields")
    if not isinstance(named, (list, tuple)) or not named:
        return None
    fields = tuple(str(item).strip() for item in named if str(item).strip())
    return fields or None


def _complete(row: Mapping[str, Any], required: Iterable[str] | None) -> bool:
    if not required:
        return False
    return all(str(row.get(key) or "").strip() for key in required)


def _is_high(row: Mapping[str, Any]) -> bool:
    return str(row.get("impact") or row.get("Impact") or "").strip().upper() in {"HIGH", "RED"}


def refuse_invented_write(path: Path) -> None:
    try:
        from .news_calendar_sync import (
            JUNE_WEEK_OF_RECORD,
            JuneWeekOfRecordError,
            refuse_june_overwrite,
        )
    except Exception as exc:
        raise FrozenArchiveError("june week guard is unset") from exc
    refuse_june_overwrite(path)
    if path.resolve() == JUNE_WEEK_OF_RECORD.resolve():
        raise JuneWeekOfRecordError("refusing to overwrite June week-of-record")


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


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return any(part in token for part in _LIMIT_PARTS)


def _secret_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return any(part in token for part in _SECRET_PARTS)


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

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or _secret_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = _probs(block)
    picked: str | None = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs or None, order)
    except Exception:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


def _score(block: Any) -> float | None:
    """The number that came back. It is not snapped to a level."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    number: Any = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        if "score" in block:
            number = block.get("score")
    return _finite(number)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut at a line."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(_probs(block) or None, _NOUL_ORDER)
    except Exception:
        picked = _unique(_probs(block), _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _blank(error: str | None) -> dict[str, Any]:
    row: dict[str, Any] = {key: None for key in _DECISION_IDS}
    row["error"] = error
    return row


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    row = _blank(error if not answers else None)
    if not answers:
        row["error"] = error or "empty"
        return row
    row["frozen_currency"] = _choice(answers.get("frozen_currency"), _CURRENCY_ORDER)
    for key in _SCORE_IDS:
        row[key] = _score(answers.get(key))
    for key in _NOUL_IDS:
        row[key] = _noul(answers.get(key))
    return row


def _question_text_ok(value: str) -> bool:
    low = value.lower()
    if "floor" in low or "baseline" in low:
        return False
    compact = value.replace(",", "").replace("_", "").replace(" ", "").lower()
    return not any(token.lower() in compact for token in _BANNED_TEXT)


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items()}
    block: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = {key: val for key, val in raw.items() if not _limit_key(str(key))}
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = cleaned
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, instructions, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    text = _scrub_text(instructions)
    return {
        qid: {
            "type": "noul",
            "instructions": text,
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def frozen_questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score. Floor and baseline are not on it."""

    pack: dict[str, Any] = {}
    pack.update(
        _noul_question(
            "news_protocol_applied",
            "Is NEWS_PROTOCOL applied on this frozen load? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "NEWS_PROTOCOL is applied on this frozen load.",
            "NEWS_PROTOCOL is not applied on this frozen load.",
        )
    )
    pack.update(
        _noul_question(
            "invented",
            "Did this frozen load invent rows? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "This load invented rows.",
            "This load did not invent rows.",
        )
    )
    pack.update(
        _noul_question(
            "june_week_untouched",
            "Does the June week of record stay untouched on this frozen load? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "The June week of record stays untouched.",
            "The June week of record does not stay untouched.",
        )
    )
    pack.update(
        _score_question(
            "apply_persist",
            "What persist does this frozen load return? "
            "The score you return is that persist. "
            "It may sit between levels. "
            "An empty score leaves the persist unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "gfull_start",
            "What unix time starts the covering window on this frozen load? "
            "The named window on this state is a fact. "
            "The score you return is the start. "
            "It may sit between instants. "
            "An empty score leaves the window unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "gfull_end",
            "What unix time ends the covering window on this frozen load? "
            "The named window on this state is a fact. "
            "The score you return is the end. "
            "It may sit between instants. "
            "An empty score leaves the window unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "cutoff_unix",
            "What unix time is the cutoff on this frozen receipt? "
            "The archive freeze on this state is a fact. "
            "The score you return is the cutoff. "
            "It may sit between instants. "
            "An empty score leaves the cutoff unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _choice_question(
            "frozen_currency",
            "Which currency count does this frozen receipt return? "
            "The unique highest probability is that count. "
            "An empty answer or a tie leaves the count unset. "
            "This ask does not transmit an order.",
            {
                "usd_xau_all": "Count rows in the returned window whose currency is USD, XAU, or ALL.",
                "currencies_on_rows": "Count every row in the returned window.",
                "withhold": "Leave the currency count unset.",
            },
        )
    )
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        texts = [str(block.get("instructions") or "")]
        criteria = block.get("criteria")
        if isinstance(criteria, dict):
            texts.extend(str(key) for key in criteria)
            texts.extend(str(text) for text in criteria.values())
        elif isinstance(criteria, list):
            texts.extend(str(item) for item in criteria)
        if any(not _question_text_ok(text) for text in texts):
            continue
        clean[str(qid)] = block
    return clean


def _local_priors() -> list[dict[str, Any]]:
    """History for the next ask. A miss is not copied back into a decision."""

    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    cleaned = _scrub(loaded)
    state["prior_outcomes"] = cleaned if isinstance(cleaned, list) else []


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    error = row.get("error")
    try:
        from .jev_questions import append_outcome
    except Exception:
        for spot in _DECISION_IDS:
            value = row.get(spot)
            _LOCAL_OUTCOMES.append(
                {
                    "spot": spot,
                    "value": value,
                    "error": None if value is not None else (error or "empty"),
                }
            )
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for spot in _DECISION_IDS:
        value = row.get(spot)
        try:
            append_outcome(
                spot,
                value,
                logged,
                error=None if value is not None else (error or "empty"),
            )
        except Exception:
            return


def _decide(state: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. A miss stays unset."""

    questions = frozen_questions()
    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    payload["api_url"] = API_URL
    payload.setdefault("login", CHALLENGE_LOGIN)
    payload.setdefault("namespace", CHALLENGE_NS)
    payload.setdefault("ns", CHALLENGE_NS)
    _attach_priors(payload, questions)
    try:
        from .jev_client import evaluate

        questions = _anchor_questions(questions, payload)
        receipt = evaluate(
            payload,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
        row = _blank(type(exc).__name__)
        _remember(payload, row)
        return row
    if not isinstance(receipt, dict):
        row = _blank("evaluate_not_a_dict")
        _remember(payload, row)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    row = _read(answers, None if error is None else str(error))
    _remember(payload, row)
    return row


def _identity_state() -> dict[str, Any]:
    return {
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "ns": CHALLENGE_NS,
        "model": MODEL,
        "api_url": API_URL,
        "source_frozen": FROZEN_ARCHIVE_NAME,
        "source_sha256": FROZEN_SHA256,
        "source_bytes": FROZEN_BYTES,
        "archive_freeze_unix": FREEZE_UTC.timestamp(),
        "named_gfull_start_unix": G_FULL_START.timestamp(),
        "named_gfull_end_unix": G_FULL_END.timestamp(),
    }


def _stamp_text(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    stamp = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_dt(row: Mapping[str, Any]) -> datetime | None:
    raw = row.get("_dt")
    if isinstance(raw, datetime):
        stamp = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return stamp.astimezone(timezone.utc)
    if isinstance(row, dict):
        return event_dt(row)
    return None


def _unix_dt(number: float | None) -> datetime | None:
    if number is None:
        return None
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _receipt_state(rows: list[dict[str, Any]]) -> dict[str, Any]:
    body = _identity_state()
    times = [dt for dt in (_row_dt(row) for row in rows) if dt is not None]
    body["n_high"] = len(rows)
    body["currencies"] = sorted({str(row.get("currency") or "") for row in rows if row.get("currency")})
    body["first_utc"] = _stamp_text(times[0]) if times else None
    body["last_utc"] = _stamp_text(times[-1]) if times else None
    return body


def _pointer_state(file_payload: Mapping[str, Any], present: bool) -> dict[str, Any]:
    body = _identity_state()
    body["pointer_present"] = present
    for key, value in file_payload.items():
        name = str(key)
        if name in _FILE_DECISION_KEYS or name == "prior_outcomes":
            body[f"file_{name}"] = value
            continue
        body[name] = value
    return body


def _window_rows(
    rows: list[dict[str, Any]],
    start: float | None,
    end: float | None,
) -> list[dict[str, Any]] | None:
    """Rows inside the returned window. A missing bound selects nothing from a named window."""

    lo = _unix_dt(start)
    hi = _unix_dt(end)
    if lo is None or hi is None:
        return None
    selected: list[dict[str, Any]] = []
    for row in rows:
        dt = _row_dt(row)
        if dt is None:
            continue
        if lo <= dt <= hi:
            selected.append(row)
    return selected


def _currency_count(
    window: list[dict[str, Any]] | None,
    choice: str | None,
) -> int | None:
    if window is None or choice is None or choice == "withhold":
        return None
    if choice == "usd_xau_all":
        return len([row for row in window if str(row.get("currency") or "") in {"USD", "XAU", "ALL"}])
    if choice == "currencies_on_rows":
        return len(window)
    return None


def load_pointer(path: Path | None = None) -> dict[str, Any]:
    target = Path(path or DEFAULT_POINTER)
    present = target.is_file()
    file_payload: dict[str, Any] = {}
    if present:
        loaded = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise FrozenArchiveError("frozen pointer must be an object")
        file_payload = loaded
    decision = _decide(_pointer_state(file_payload, present))
    if present:
        out = dict(file_payload)
    else:
        out = {
            "present": False,
            "sha256": FROZEN_SHA256,
            "bytes": FROZEN_BYTES,
        }
    out["present"] = present
    for key in _FILE_DECISION_KEYS:
        if key in file_payload:
            out[f"file_{key}"] = file_payload.get(key)
    out["NEWS_PROTOCOL_APPLIED"] = decision["news_protocol_applied"]
    out["invented"] = decision["invented"]
    out["june_week_of_record_untouched"] = decision["june_week_untouched"]
    out["apply_persist"] = decision["apply_persist"]
    out["gfull_start"] = decision["gfull_start"]
    out["gfull_end"] = decision["gfull_end"]
    out["cutoff_unix"] = decision["cutoff_unix"]
    out["frozen_currency"] = decision["frozen_currency"]
    out["error"] = decision["error"]
    return out


def load_frozen_payload(path: Path | None = None) -> dict[str, Any]:
    """Prefer the HIGH extract; accept a local full archive if it matches the pointer sha."""
    if path is not None:
        target = Path(path)
        if not target.is_file():
            raise FrozenArchiveError(f"missing frozen payload: {target}")
        raw = target.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise FrozenArchiveError("frozen payload must be an object")
        payload["_source_path"] = str(target)
        payload["_source_sha256"] = hashlib.sha256(raw).hexdigest()
        payload["_source_bytes"] = len(raw)
        return payload
    extract = DEFAULT_EXTRACT
    if extract.is_file():
        raw = extract.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        payload["_source_path"] = str(extract.relative_to(REPO_ROOT)) if extract.is_relative_to(REPO_ROOT) else str(extract)
        payload["_source_sha256"] = hashlib.sha256(raw).hexdigest()
        payload["_source_bytes"] = len(raw)
        return payload
    raise FrozenArchiveError(
        "frozen HIGH extract missing; host archive is read-only at "
        r"host-local\redacted_host\repo\data\news_calendar.json.frozen-20260821"
    )


def high_events(
    payload: dict[str, Any] | None = None,
    *,
    before: datetime | None = FREEZE_UTC,
) -> list[dict[str, Any]]:
    """HIGH rows from the archive.

    The default bound is the archive freeze, which is that file's own stamp.
    A caller-supplied ``before`` is the bound they asked for. The receipt
    cutoff is a separate score.
    """

    packed = payload if payload is not None else load_frozen_payload()
    required = _required_fields(packed)
    cutoff = before
    rows: list[dict[str, Any]] = []
    for row in packed.get("events") or []:
        if not isinstance(row, dict):
            continue
        if not _is_high(row):
            continue
        if not _complete(row, required):
            continue
        dt = event_dt(row)
        if dt is None:
            continue
        if cutoff is not None and dt >= cutoff:
            continue
        rows.append(
            {
                "date": str(row["date"]),
                "time_utc": str(row["time_utc"]),
                "event": str(row["event"]),
                "impact": "HIGH",
                "currency": str(row["currency"]).strip().upper(),
                "event_type": row.get("event_type"),
                "family": row.get("family"),
                "scheduled_utc": row.get("scheduled_utc") or dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "role": row.get("role"),
                "datetime_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "_dt": dt,
            }
        )
    rows.sort(key=lambda event: event["_dt"])
    return rows


def covering_gfull(events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Rows inside the returned window. An unset bound contributes no rows."""

    rows = events if events is not None else high_events()
    decision = _decide(_receipt_state(rows))
    window = _window_rows(rows, decision.get("gfull_start"), decision.get("gfull_end"))
    if window is None:
        return []
    return window


def extract_receipt(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = events if events is not None else high_events()
    decision = _decide(_receipt_state(rows))
    window = _window_rows(rows, decision.get("gfull_start"), decision.get("gfull_end"))
    cutoff = _unix_dt(decision.get("cutoff_unix"))
    return {
        "schema": "gtos.news.frozen_high_extract.v1",
        "model": MODEL,
        "api_url": API_URL,
        "invented": decision.get("invented"),
        "NEWS_PROTOCOL_APPLIED": decision.get("news_protocol_applied"),
        "june_week_of_record_untouched": decision.get("june_week_untouched"),
        "apply_persist": decision.get("apply_persist"),
        "frozen_currency": decision.get("frozen_currency"),
        "n_high": len(rows),
        "n_high_gfull": None if window is None else len(window),
        "n_high_gfull_usd_xau_all": _currency_count(window, decision.get("frozen_currency")),
        "cutoff_unix": decision.get("cutoff_unix"),
        "cutoff_utc": _stamp_text(cutoff),
        "gfull_start": decision.get("gfull_start"),
        "gfull_end": decision.get("gfull_end"),
        "archive_freeze_utc": _stamp_text(FREEZE_UTC),
        "source_frozen": FROZEN_ARCHIVE_NAME,
        "source_sha256": FROZEN_SHA256,
        "source_bytes": FROZEN_BYTES,
        "broker_effect": False,
        "error": decision.get("error"),
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
