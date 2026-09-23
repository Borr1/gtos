"""Next-14d registry derived FROM the live HIGH spine. Never invent.

Host ``event_registry_v1.json`` as_of 2026-09-14 still lists 2026-09-16 FOMC
as upcoming — STALE. Do not feed that file as a live registry. Horizon rows
come from ``f5_high_calendar`` / ``official_high_spine`` clocks already on
disk. No mill URL. No ``NEWS_PROTOCOL``.

Every decision on this registry, including every parameter, is the System
One return for that state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only Noul, Choice, or Score.
Prior outcomes are attached on the ask, and the return is stored for the
next ask. A score may sit between levels. An empty answer, a tie, a
missing score, or an error leaves that field unset.

The spine clocks and which file is on disk are facts. A floor and a
baseline are not a question. This module does not send.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from .news_calendar_sync import _scheduled

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPINE = REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260920.json"
FALLBACK_SPINE = REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260916.json"
STALE_HOST_REGISTRY_AS_OF = "2026-09-14T06:18:09Z"
STALE_HOST_REGISTRY_PATH = r"host-local\redacted_host\repo\judgment\state\event_registry_v1.json"

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
SCHEMA = "gtos.event_registry.next14d.v1"

_SOURCE_ORDER = ("high_spine", "withhold")
_NOUL_ORDER = ("true", "false")
_CHOICE_IDS = ("registry_source",)
_SCORE_IDS = ("horizon_days", "apply_persist")
_NOUL_IDS = (
    "invented",
    "news_protocol_applied",
    "stale_host_registry_unused",
    "official_high_when_omitted",
)
_DECISION_IDS = _CHOICE_IDS + _SCORE_IDS + _NOUL_IDS
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


def _parse(value: str) -> datetime | None:
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


def _spine_path(path: Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    if DEFAULT_SPINE.is_file():
        return DEFAULT_SPINE
    return FALLBACK_SPINE


def _stamp(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    stamp = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
    except (OSError, ValueError):
        return str(path)


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


def _flag(row: Mapping[str, Any], key: str) -> bool | None:
    """A flag the spine already stored. A missing flag stays missing."""

    if key not in row or row.get(key) is None:
        return None
    return bool(row.get(key))


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
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
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
    row["registry_source"] = _choice(answers.get("registry_source"), _SOURCE_ORDER)
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
    text = _scrub_text(instructions)
    block: dict[str, Any] = {
        "type": "score",
        "instructions": text,
        "criteria": ["below this state", "this state", "above this state"],
    }
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, text)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = {key: val for key, val in raw.items() if not _limit_key(str(key))}
    except Exception:
        pass
    block["type"] = "score"
    block["instructions"] = text
    criteria = block.get("criteria")
    if isinstance(criteria, list):
        kept = [_scrub_text(str(item)) for item in criteria if _question_text_ok(str(item))]
        if kept:
            block["criteria"] = kept
        else:
            block.pop("criteria", None)
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    text = _scrub_text(instructions)
    return {
        qid: {
            "type": "noul",
            "instructions": text,
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def registry_questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score. Floor and baseline are not on it."""

    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "registry_source",
            "Which source publishes the forward window on this registry? "
            "The unique highest probability is that source. "
            "The spine rows on this state are a fact. "
            "An empty answer or a tie leaves the window unset. "
            "This ask does not transmit an order.",
            {
                "high_spine": "Publish the window from the high spine rows on this state, measured with the returned horizon.",
                "withhold": "Leave the inside and beyond lists unset.",
            },
        )
    )
    pack.update(
        _score_question(
            "horizon_days",
            "How many days is the forward horizon on this registry? "
            "A proposed day count on this state is a fact, not the horizon. "
            "The score you return is the horizon. "
            "It may sit between levels. "
            "An empty score leaves the horizon unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "apply_persist",
            "What persist does this registry return? "
            "The score you return is that persist. "
            "It may sit between levels. "
            "An empty score leaves the persist unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _noul_question(
            "invented",
            "Did this registry invent rows? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "This registry invented rows.",
            "This registry did not invent rows.",
        )
    )
    pack.update(
        _noul_question(
            "news_protocol_applied",
            "Is NEWS_PROTOCOL applied on this registry? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "NEWS_PROTOCOL is applied on this registry.",
            "NEWS_PROTOCOL is not applied on this registry.",
        )
    )
    pack.update(
        _noul_question(
            "stale_host_registry_unused",
            "Does this registry leave the stale host registry unused? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This ask does not transmit an order.",
            "The stale host registry stays unused.",
            "The stale host registry does not stay unused.",
        )
    )
    pack.update(
        _noul_question(
            "official_high_when_omitted",
            "When a spine row omits official high, what is that mark? "
            "A mark the row already stores is a fact. "
            "The noul you return is the mark for an omitted row. "
            "An empty noul leaves the omitted mark unset. "
            "This ask does not transmit an order.",
            "An omitted official-high mark is yes.",
            "An omitted official-high mark is no.",
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
    if loaded is None:
        state["prior_outcomes"] = []
        return
    cleaned = _scrub(loaded)
    state["prior_outcomes"] = [] if cleaned is None else cleaned


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

    questions = registry_questions()
    allowed = {"noul", "choice", "score"}
    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    payload["api_url"] = API_URL
    payload.setdefault("login", CHALLENGE_LOGIN)
    payload.setdefault("namespace", CHALLENGE_NS)
    payload.setdefault("ns", CHALLENGE_NS)
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        row = _blank("question_pack_fail")
        _remember(payload, row)
        return row
    _attach_priors(payload, questions)
    try:
        from .jev_client import evaluate

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


def _load_spine(path: Path) -> tuple[dict[str, Any] | None, str]:
    """The file on disk. A missing file is no feed and does not select another source."""

    if not path.is_file():
        return None, "no feed"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "no feed"
    if not isinstance(loaded, dict):
        return None, "no feed"
    return loaded, "spine"


def _row_fact(row: Mapping[str, Any], scheduled: str, dt: datetime) -> dict[str, Any]:
    fact: dict[str, Any] = {
        "name": str(row.get("name") or row.get("event") or "").strip(),
        "scheduled_utc": _stamp(dt),
        "currency": str(row.get("currency") or "").strip().upper(),
        "event_type": row.get("event_type"),
        "time_certainty": row.get("time_certainty"),
    }
    if "official_high" in row and row.get("official_high") is not None:
        fact["official_high"] = bool(row.get("official_high"))
    past = _flag(row, "past")
    if past is not None:
        fact["past"] = past
    beyond = _flag(row, "beyond_horizon_14d")
    if beyond is not None:
        fact["beyond_horizon_14d"] = beyond
    fact["scheduled_raw"] = scheduled
    return fact


def _parsed_rows(payload: Mapping[str, Any] | None) -> list[tuple[dict[str, Any], datetime]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("events")
    if not isinstance(rows, list):
        return []
    parsed: list[tuple[dict[str, Any], datetime]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        scheduled = _scheduled(row)
        dt = _parse(scheduled)
        if dt is None:
            continue
        parsed.append((_row_fact(row, scheduled, dt), dt))
    return parsed


def _horizon_at(as_of: datetime, days: float | None) -> datetime | None:
    if days is None:
        return None
    try:
        return as_of + timedelta(days=days)
    except (OverflowError, OSError, ValueError):
        return None


def _window(
    parsed: list[tuple[dict[str, Any], datetime]],
    as_of: datetime,
    days: float | None,
    source: str | None,
    omitted: bool | float | None,
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None, datetime | None]:
    """Inside and beyond the returned horizon. A missing source or horizon selects nothing."""

    horizon = _horizon_at(as_of, days)
    if source != "high_spine" or horizon is None:
        return None, None, horizon
    inside: list[dict[str, Any]] = []
    beyond: list[dict[str, Any]] = []
    for fact, dt in parsed:
        item = _item(fact, omitted)
        if dt < as_of:
            continue
        if dt <= horizon:
            inside.append(item)
        else:
            beyond.append(item)
    return inside, beyond, horizon


def _item(fact: Mapping[str, Any], omitted: bool | float | None) -> dict[str, Any]:
    official = fact.get("official_high") if "official_high" in fact else omitted
    item = {
        "name": fact.get("name"),
        "scheduled_utc": fact.get("scheduled_utc"),
        "currency": fact.get("currency"),
        "event_type": fact.get("event_type"),
        "official_high": official,
        "past": fact.get("past") if "past" in fact else None,
        "beyond_horizon_14d": fact.get("beyond_horizon_14d") if "beyond_horizon_14d" in fact else None,
        "time_certainty": fact.get("time_certainty"),
    }
    return item


def _state(
    as_of: datetime,
    spine: Path,
    payload: Mapping[str, Any] | None,
    feed: str,
    parsed: list[tuple[dict[str, Any], datetime]],
    proposed_horizon_days: float | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "ns": CHALLENGE_NS,
        "model": MODEL,
        "api_url": API_URL,
        "as_of_utc": _stamp(as_of),
        "feed": feed,
        "source_spine": _rel(spine),
        "source_spine_updated_utc": payload.get("updated_utc") if isinstance(payload, Mapping) else None,
        "stale_host_registry_as_of_utc": STALE_HOST_REGISTRY_AS_OF,
        "stale_host_registry_path": STALE_HOST_REGISTRY_PATH,
        "n_spine_rows": len(parsed),
        "n_past_clock": sum(1 for _, dt in parsed if dt < as_of),
        "rows": [fact for fact, _dt in parsed],
    }
    if proposed_horizon_days is not None:
        body["proposed_horizon_days"] = proposed_horizon_days
    return body


def next_14d(
    as_of_utc: datetime | str,
    *,
    spine_path: Path | None = None,
    horizon_days: float | None = None,
) -> dict[str, Any]:
    """One registry card. The horizon, persist, and marks are that ask.

    ``horizon_days`` on the call is a proposed fact. The horizon on the
    card is the returned score. A missing score does not publish a window.
    """

    if isinstance(as_of_utc, datetime):
        as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
        as_of = as_of.astimezone(timezone.utc)
    else:
        parsed_as_of = _parse(str(as_of_utc))
        if parsed_as_of is None:
            raise ValueError("as_of_utc")
        as_of = parsed_as_of
    spine = _spine_path(spine_path)
    payload, feed = _load_spine(spine)
    parsed = _parsed_rows(payload)
    proposed = _finite(horizon_days)
    decision = _decide(_state(as_of, spine, payload, feed, parsed, proposed))
    days = decision.get("horizon_days")
    if not isinstance(days, (int, float)) or isinstance(days, bool):
        days = None
    source = decision.get("registry_source")
    omitted = decision.get("official_high_when_omitted")
    inside, beyond, horizon = _window(parsed, as_of, days if isinstance(days, (int, float)) else None, source if isinstance(source, str) else None, omitted)
    n_past = sum(1 for _, dt in parsed if dt < as_of)
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "api_url": API_URL,
        "as_of_utc": _stamp(as_of),
        "horizon_days": days,
        "horizon_utc": _stamp(horizon) if source == "high_spine" else None,
        "source_spine": _rel(spine),
        "source_spine_updated_utc": payload.get("updated_utc") if isinstance(payload, Mapping) else None,
        "feed": feed,
        "invented": decision.get("invented"),
        "NEWS_PROTOCOL_APPLIED": decision.get("news_protocol_applied"),
        "stale_host_registry_as_of_utc": STALE_HOST_REGISTRY_AS_OF,
        "stale_host_registry_unused": decision.get("stale_host_registry_unused"),
        "official_high_when_omitted": omitted,
        "registry_source": source,
        "n_inside_14d": None if inside is None else len(inside),
        "n_beyond_14d": None if beyond is None else len(beyond),
        "n_past": n_past,
        "inside_14d": inside,
        "beyond_14d": beyond,
        "apply_persist": decision.get("apply_persist"),
        "broker_effect": False,
        "error": decision.get("error"),
    }
