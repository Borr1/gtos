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
