"""Exec, governor, news, cluster, and F5 fire decisions for one state.

One ask: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The return is a Noul, a Choice, or a Score. Prior outcomes are attached on
the ask, and the return is stored for the next ask.

Every decision in this module, including each parameter, is that return.
A Choice is the unique highest probability. A Score is the returned number
and may sit between levels. A Noul is a bool or a probability. An empty
answer, a tie, or an error leaves that field unset.

A floor and a baseline are not a question. This module does not send an
order and does not flatten. ``mill_url`` stays None. A missing calendar is
``feed: "no feed"`` on the state. It does not select an alternative.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

MODEL = "jev-1.13.0"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.judgment.exec_gov_news.v1"
EXEC_GOV_NEWS_ENV = "GTOS_JEV_EXEC_GOV_NEWS"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
KIND_READ = "read"

CANCEL_T15 = "cancel_t15"
REEVAL_T60 = "reeval_t60"
HOLD = "hold"
ABSTAIN = "abstain"
NEWS_ALTERNATIVES = (CANCEL_T15, REEVAL_T60, HOLD, ABSTAIN)
NATIVE_ALTERNATIVES = ("native_limit", "market", "abstain")
CLOSE_ALTERNATIVES = ("retry", "skip", "unknown")
ACTION_ALTERNATIVES = ("hold_corr", "size_down", "allow", "abstain")

SEATS = ("exec", "governor", "cluster", "news", "f5_fire")
BRANCHES = ("place", "modify", "close", "observe", "derisk", "cycle")
NO_FEED = "no feed"
NEVER_FLATTEN_TICKETS = frozenset(
    {294092360, 294088097, 293332188, 294069721, 294215389}
)
_TRUTHY_OFF = frozenset({"0", "false", "no", "off"})
_TRUTHY_ON = frozenset({"1", "true", "yes", "on"})
_BANNED = ("floor", "baseline", "90k", "110k", "90000", "110000")
_CHUNKS = (
    "tick",
    "geometry",
    "pending",
    "harvest",
    "close_receipt",
    "equity",
    "dd_wall",
    "derisk",
    "stress",
    "occupancy",
    "corr",
    "peers",
    "spine",
    "high_window",
    "cycle",
    "clock",
    "limit",
    "freeze",
    "thin",
    "stop_distance",
)
_CHOICE_ORDER = {
    "news_cycle": NEWS_ALTERNATIVES,
    "native_limit_vs_market": NATIVE_ALTERNATIVES,
    "close_none_label": CLOSE_ALTERNATIVES,
    "action_scope": ACTION_ALTERNATIVES,
}
_SCORE_IDS = (
    "window_pre_min",
    "window_post_min",
    "cap_mult_overlay",
    "derisk_tilt",
    "wall_pressure",
    "fire_window",
    "limit_expiry",
    "frozen_reprice",
    "thin_asia",
    "minstop_fit",
    "pip8_fit",
    "sl_fresh_fitness",
    "pretrade_mgr_quality",
    "j46_tp_fit",
    "harvest_observe",
    "never_widen_pressure",
    "fill_deviation_observe",
    "pending_still_same_setup",
    "opposite_lock",
    "eurgbp_stack",
)
_NOUL_IDS = (
    "may_send",
    "leave_orig",
    "extra_cancel",
    "extra_hold",
    "exec_state_sufficient",
    "state_sufficient",
    "governor_ready",
    "stress_continue",
    "coloss_same_bet",
    "cluster_same_dir",
    "speak_hold",
    "event_proximity",
    "calendar_honest",
)
_BRANCH_CHOICE = {
    "cycle": "news_cycle",
    "place": "native_limit_vs_market",
    "close": "close_none_label",
    "observe": "action_scope",
}
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _banned(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in _BANNED)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _spine_candidates() -> tuple[Path, ...]:
    """Calendars already on this tree. No invented URL."""
    root = _repo_root()
    host = Path(r"host-local\redacted_host\repo")
    names = (
        Path("data") / "news" / "f5_high_calendar.json",
        Path("judgment") / "state" / "f5_high_calendar.json",
        Path("pipeline_state")
        / "ultimate_book"
        / "operator"
        / "judgment"
        / "state"
        / "f5_high_calendar.json",
        Path("data") / "news_calendar.json",
    )
    out: list[Path] = []
    for base in (root, host):
        for name in names:
            out.append(base / name)
    return tuple(out)


def _parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z") and "T" in text and "-" in text[:5]:
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_when(row: Mapping[str, Any]) -> datetime | None:
    for key in ("scheduled_utc", "datetime_utc", "time_utc"):
        parsed = _parse_utc(row.get(key))
        if parsed is not None and (parsed.year > 2000 or key != "time_utc"):
            if key == "time_utc" and parsed.year < 2000:
                continue
            return parsed
    date = row.get("date")
    clock = row.get("time_utc")
    if date and clock and len(str(clock)) <= 8:
        return _parse_utc(f"{date}T{clock}:00Z")
    return None


def _compact_event(row: Mapping[str, Any], when: datetime) -> dict[str, Any]:
    name = row.get("event") or row.get("name")
    return {
        "event": name,
        "scheduled_utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "impact": row.get("impact"),
        "currency": row.get("currency"),
    }


def _read_live_spine() -> dict[str, Any] | None:
    for path in _spine_candidates():
        try:
            if not path.is_file():
                continue
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(loaded, dict):
            continue
        events = loaded.get("events")
        if not isinstance(events, list) or not events:
            continue
        return {"path": path, "payload": loaded}
    return None


def attach_feed(news: Mapping[str, Any] | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    """On-disk calendar as context. A missing file is 'no feed', not an answer.

    The pre and post windows are scores on the ask. They are not stamped here.
    """
    incoming = dict(news or {})
    for key in ("window_pre_min", "window_post_min", "inside_window"):
        incoming.pop(key, None)
    as_of = now or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    base: dict[str, Any] = {
        "mill_url": None,
        "invented": False,
        "NEWS_PROTOCOL_APPLIED": bool(incoming.get("NEWS_PROTOCOL_APPLIED", False)),
        "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open_gold_left_open": sorted(NEVER_FLATTEN_TICKETS),
    }
    found = _read_live_spine()
    if found is None:
        base.update(
            {
                "feed": NO_FEED,
                "source": None,
                "updated_utc": None,
                "n_events": 0,
                "events": [],
                "nearest": None,
                "next_future": None,
                "spine_empty": True,
            }
        )
        return base
    payload = found["payload"]
    compact: list[dict[str, Any]] = []
    nearest: dict[str, Any] | None = None
    nearest_abs: float | None = None
    next_future: dict[str, Any] | None = None
    next_future_min: float | None = None
    for row in payload.get("events") or []:
        if not isinstance(row, Mapping):
            continue
        when = _event_when(row)
        if when is None:
            continue
        item = _compact_event(row, when)
        minutes = (when - as_of).total_seconds() / 60.0
        item["minutes_from_as_of"] = round(minutes, 3)
        compact.append(item)
        if nearest_abs is None or abs(minutes) < nearest_abs:
            nearest_abs = abs(minutes)
            nearest = dict(item)
        if minutes >= 0 and (next_future_min is None or minutes < next_future_min):
            next_future_min = minutes
            next_future = dict(item)
    compact.sort(key=lambda item: str(item.get("scheduled_utc") or ""))
    base.update(
        {
            "feed": str(payload.get("schema") or found["path"].name),
            "source": str(found["path"]),
            "updated_utc": payload.get("updated_utc"),
            "n_events": len(compact),
            "events": compact,
            "nearest": nearest,
            "next_future": next_future,
            "spine_empty": len(compact) == 0,
        }
    )
    if not compact:
        base["feed"] = NO_FEED
        base["spine_empty"] = True
    return base


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    raw = block.get("probabilities") if isinstance(block, Mapping) else None
    if not isinstance(raw, Mapping):
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label is unset."""
    if not probabilities:
        return None
    best = max(probabilities.values())
    winners = [
        name
        for name in order
        if name in probabilities and probabilities[name] == best
    ]
    if len(winners) != 1:
        return None
    winner = winners[0]
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(probabilities), order)
    except Exception:
        agreed = winner
    if agreed is None or str(agreed) != winner:
        return None
    return winner


def unique_news_alternative(block: Any) -> dict[str, Any]:
    """The news choice is the unique highest probability. A tie is unset."""
    probs = _probabilities(block, NEWS_ALTERNATIVES)
    choice = _unique(probs, NEWS_ALTERNATIVES)
    confidence = None
    if isinstance(block, Mapping) and block.get("confidence") is not None:
        confidence = _number(block.get("confidence"))
    return {
        "choice": choice,
        "probabilities": probs,
        "confidence": confidence,
        "unique": choice is not None,
        "tie": bool(probs) and choice is None,
    }


def _score_of(block: Any) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped."""
    if isinstance(block, Mapping) and block.get("error"):
        return None
    if isinstance(block, Mapping):
        for key in ("score", "value"):
            if key in block and block.get(key) is not None:
                return _number(block.get(key))
        if isinstance(block.get("probabilities"), Mapping) and block.get("probabilities"):
            probs = {
                str(key): value
                for key, value in block["probabilities"].items()
                if _number(value) is not None
            }
            numeric = {key: float(value) for key, value in probs.items()}
            if numeric and _unique(numeric, tuple(numeric)) is None:
                return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    if isinstance(block, Mapping):
        return None
    return _number(block)


def _noul_of(block: Any) -> bool | float | None:
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
    return _number(value)


def include_depth_name(score: float | None) -> float | None:
    """Ordinal place of hide / short / long / full. Not an amount."""

    number = _number(score)
    if number is None or number != int(number):
        return None
    whole = int(number)
    depth = ("hide", "short", "long", "full")
    if whole < 0 or whole >= len(depth):
        return None
    return float(whole)


def completeness_noul(answers: Mapping[str, Any] | None) -> bool | float | None:
    """One completeness Noul. A missing noul stays missing."""
    if not isinstance(answers, Mapping):
        return None
    for key in ("state_sufficient", "exec_state_sufficient"):
        value = _noul_of(answers.get(key))
        if value is not None:
            return value
    return None


def _block(answers: Mapping[str, Any] | None, key: str) -> dict[str, Any] | None:
    if not isinstance(answers, Mapping):
        return None
    block = answers.get(key)
    return block if isinstance(block, dict) else None


def _choice_of(answers: Mapping[str, Any] | None, key: str) -> str | None:
    order = _CHOICE_ORDER.get(key)
    if order is None:
        return None
    return _unique(_probabilities(_block(answers, key), order), order)


def _read_answers(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    choices = {key: _choice_of(payload, key) for key in _CHOICE_ORDER}
    scores = {}
    for key in _SCORE_IDS:
        block = payload.get(key)
        if key in _ORDINAL_IDS:
            try:
                from .jev_questions import ordinal_index

                scores[key] = ordinal_index(block, len(_FIT_LEVELS))
            except Exception:
                scores[key] = None
        else:
            scores[key] = _score_of(block)
    nouls = {key: _noul_of(payload.get(key)) for key in _NOUL_IDS}
    include: dict[str, float] = {}
    for key, block in payload.items():
        name = str(key)
        if not name.startswith("include_") or _banned(name):
            continue
        try:
            from .jev_questions import ordinal_index

            number = ordinal_index(block, 4)
        except Exception:
            number = None
        if number is None:
            continue
        chunk = name[len("include_") :]
        if chunk and not _banned(chunk):
            include[chunk] = float(number)
    news = unique_news_alternative(payload.get("news_cycle"))
    return {
        "choices": choices,
        "scores": scores,
        "nouls": nouls,
        "include_depth": include,
        "news": news,
        "sufficient": completeness_noul(payload),
    }


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
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
    body["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return body


_FIT_LEVELS = (
    "poor fitness on this state",
    "ordinary fitness on this state",
    "clean fitness on this state",
)
_MINUTE_IDS = frozenset({"window_pre_min", "window_post_min"})
_MULT_IDS = frozenset({"cap_mult_overlay"})
_TILT_IDS = frozenset({"derisk_tilt"})
_ORDINAL_IDS = frozenset(
    {
        "wall_pressure",
        "fire_window",
        "limit_expiry",
        "frozen_reprice",
        "thin_asia",
        "minstop_fit",
        "pip8_fit",
        "sl_fresh_fitness",
        "pretrade_mgr_quality",
        "j46_tp_fit",
        "harvest_observe",
        "never_widen_pressure",
        "fill_deviation_observe",
        "pending_still_same_setup",
        "opposite_lock",
        "eurgbp_stack",
    }
)


def _score_question(qid: str, instructions: str, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Amount Scores use the card. Fitness and include-depth stay an order."""

    try:
        from .jev_questions import amount_question, minute_anchors, mult_anchors, ordinal_question
    except Exception:
        return {}
    name = str(qid)
    if name in _MINUTE_IDS:
        built = amount_question(name, instructions, minute_anchors(state))
    elif name in _MULT_IDS:
        built = amount_question(name, instructions, mult_anchors(state))
    elif name in _TILT_IDS:
        built = amount_question(name, instructions, [])
    elif name.startswith("include_"):
        built = ordinal_question(name, instructions, ("hide", "short", "long", "full"))
    else:
        built = ordinal_question(name, instructions, _FIT_LEVELS)
    row = built.get(name) if isinstance(built, dict) else None
    return dict(row) if isinstance(row, dict) else {}


def _noul_question(instructions: str, true_line: str, false_line: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true_line, "false": false_line},
    }


def _between(what: str) -> str:
    return (
        f"The score you return is the {what} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "This question does not send an order and does not flatten."
    )


def exec_gov_news_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seat: str = "exec",
    branch: str = "place",
    seats: Iterable[str] | None = None,
) -> dict[str, Any]:
    """The menu for one ask. The menu does not decide."""
    del seat, branch, seats
    unset = "An empty answer leaves it unset. This question does not send an order and does not flatten."
    pack: dict[str, Any] = {
        "exec_state_sufficient": _noul_question(
            "Is this exec, governor, news, cluster, or fire state complete enough to judge "
            "as of its clock? One completeness noul for this object. "
            "A missing calendar is context. It does not answer this noul. " + unset,
            "The named state is complete enough to judge.",
            "A named piece of this state is missing.",
        ),
        "state_sufficient": _noul_question(
            "Is this state sufficient for this hop? One completeness noul. " + unset,
            "This state is sufficient for this hop.",
            "This state is not sufficient for this hop.",
        ),
        "news_cycle": _choice_question(
            "news_cycle",
            "What is the news action for this state? "
            "The choice is the single highest probability. "
            "A tie or an empty answer leaves the choice unset. "
            "A missing calendar does not select an option. "
            "Do not invent a mill URL. Do not flatten an open ticket. "
            "This question does not send an order.",
            {
                CANCEL_T15: "Cancel the pending for this print.",
                REEVAL_T60: "Reevaluate this print. Do not cancel from this option.",
                HOLD: "The calendar does not call for cancel or reevaluate.",
                ABSTAIN: "Stand aside on this news state.",
            },
        ),
        "native_limit_vs_market": _choice_question(
            "native_limit_vs_market",
            "How does this order rest? The choice is the single highest probability. "
            "A tie or an empty answer leaves the route unset. " + unset,
            {
                "native_limit": "Rest a native limit.",
                "market": "Take the market.",
                "abstain": "Do not steer the route.",
            },
        ),
        "close_none_label": _choice_question(
            "close_none_label",
            "Name a close that did not send. The choice is the single highest probability. "
            "A tie or an empty answer leaves the label unset. Do not flatten. " + unset,
            {
                "retry": "The close looks transient.",
                "skip": "The close looks spent for this cycle.",
                "unknown": "The close is unassembled.",
            },
        ),
        "action_scope": _choice_question(
            "action_scope",
            "What is the correlation action for this state? "
            "The choice is the single highest probability. "
            "A tie or an empty answer leaves it unset. "
            "This is not an occupancy hold. Do not flatten. " + unset,
            {
                "hold_corr": "Hold for correlation.",
                "size_down": "Size down versus the named cluster.",
                "allow": "Correlation does not hold this fire.",
                "abstain": "Do not steer.",
            },
        ),
        "may_send": _noul_question(
            "Does this state authorize a send? The noul you return is that authorization. "
            + unset,
            "This state authorizes a send.",
            "This state does not authorize a send.",
        ),
        "leave_orig": _noul_question(
            "Does this state leave the original stop and target? " + unset,
            "Leave the original stop and target.",
            "Do not leave the original stop and target.",
        ),
        "extra_cancel": _noul_question(
            "Does this state cancel a pending for the print? " + unset,
            "Cancel that pending.",
            "Do not cancel that pending.",
        ),
        "extra_hold": _noul_question(
            "Does this state hold for correlation? " + unset,
            "Hold for correlation.",
            "Do not hold for correlation.",
        ),
        "governor_ready": _noul_question(
            "Is the governor snapshot readable for this state? " + unset,
            "The governor snapshot is readable.",
            "The governor snapshot is missing or contradictory.",
        ),
        "stress_continue": _noul_question(
            "Does named stress keep shrinking new risk? " + unset,
            "Named stress still shrinks new risk.",
            "Named stress does not shrink new risk.",
        ),
        "coloss_same_bet": _noul_question(
            "Is this fire the same bet as a named cluster already on the book? " + unset,
            "This fire is that same bet.",
            "This fire is not that same bet.",
        ),
        "cluster_same_dir": _noul_question(
            "Are named open units the same-direction cluster as this fire? " + unset,
            "The named cluster is the same direction.",
            "The named cluster is not the same direction.",
        ),
        "speak_hold": _noul_question(
            "Is a correlation hold speakable for this state? " + unset,
            "That correlation hold is speakable.",
            "That correlation hold is not speakable.",
        ),
        "event_proximity": _noul_question(
            "Is a named high-impact print near this fire on the calendar in state? "
            "A missing feed does not answer this noul. " + unset,
            "A named high-impact print is near this fire.",
            "No named high-impact print is near this fire.",
        ),
        "calendar_honest": _noul_question(
            "Did the events on this state come from the on-disk calendar, with mill_url empty? "
            + unset,
            "The events came from that file.",
            "There is no on-disk feed, or the events did not come from it.",
        ),
    }
    score_lines = {
        "window_pre_min": "minutes before a named print",
        "window_post_min": "minutes after a named print",
        "cap_mult_overlay": "size-cap overlay",
        "derisk_tilt": "derisk tilt",
        "wall_pressure": "pressure at the prop wall",
        "fire_window": "fire-window fitness",
        "limit_expiry": "resting-limit fitness",
        "frozen_reprice": "frozen-price fitness",
        "thin_asia": "thin-session fitness",
        "minstop_fit": "stop-distance fitness",
        "pip8_fit": "cash-fx stop fitness",
        "sl_fresh_fitness": "stop-geometry fitness from decision tick to send tick",
        "pretrade_mgr_quality": "pretrade fitness",
        "j46_tp_fit": "target-distance fitness",
        "harvest_observe": "harvest observation",
        "never_widen_pressure": "widen pressure of a stop modify",
        "fill_deviation_observe": "fill-deviation observation",
        "pending_still_same_setup": "pending-thesis fitness",
        "opposite_lock": "opposite-position lock",
        "eurgbp_stack": "same-currency stack",
    }
    for qid, what in score_lines.items():
        block = _score_question(qid, _between(what), state)
        if block:
            pack[qid] = block
    for chunk in _CHUNKS:
        block = _score_question(
            f"include_{chunk}",
            _between(f"include-depth of the named {chunk} chunk"),
            state,
        )
        if block:
            pack[f"include_{chunk}"] = block
    return _clean_questions(pack)


def _clean_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, body in questions.items():
        qid = str(key)
        if _banned(qid) or not isinstance(body, dict):
            continue
        kind = str(body.get("type") or "").lower()
        if kind not in {"noul", "choice", "score"}:
            continue
        instructions = str(body.get("instructions") or "")
        if _banned(instructions):
            continue
        cleaned = dict(body)
        cleaned["type"] = kind
        criteria = body.get("criteria")
        if isinstance(criteria, dict):
            kept: dict[str, str] = {}
            for name, text in criteria.items():
                if _banned(str(name)) or _banned(str(text)):
                    continue
                kept[str(name)] = str(text)
            if kind == "choice" and not kept:
                continue
            cleaned["criteria"] = kept
        elif isinstance(criteria, list):
            cleaned["criteria"] = [item for item in criteria if not _banned(str(item))]
        out[qid] = cleaned
    return out


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    """Drop banned keys. A repeated container is a cycle and stops. No depth cap."""

    if seen is None:
        seen = set()
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value) if isinstance(value, float) else value
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _banned(name) or name in _CHOICE_ORDER or name in _SCORE_IDS or name in _NOUL_IDS:
                continue
            if name.startswith("include_"):
                continue
            out[name] = _scrub(item, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        return [_scrub(item, seen) for item in value]
    return None


def _local_priors() -> list[dict[str, Any]]:
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    state["prior_outcomes"] = loaded if loaded is not None else []


def _remember(
    state: Mapping[str, Any],
    pairs: list[tuple[str, Any]],
    error: str | None,
) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append(
                {
                    "spot": key,
                    "value": value,
                    "error": None if value is not None else (error or "unset"),
                }
            )
        return
    for key, value in pairs:
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else (error or "unset"),
            )
        except Exception:
            return


def _endpoint() -> str:
    try:
        from .jev_client import API_URL

        return str(API_URL)
    except Exception:
        return ENDPOINT


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One System One post. A miss stays an empty answer map."""
    pack = _clean_questions(questions)
    posted = _scrub(dict(state or {}))
    if not isinstance(posted, dict):
        posted = {}
    posted["model"] = MODEL
    _attach_priors(posted, pack)
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {
            "ok": False,
            "skipped": type(exc).__name__,
            "error": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "questions": pack,
            "posted_state": posted,
            "n_calls": 0,
            "endpoint": _endpoint(),
        }
    try:
        receipt = evaluate(
            posted,
            questions=pack,
            merge_sleeve=False,
            model=MODEL,
            timeout_s=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise
        return {
            "ok": False,
            "skipped": type(exc).__name__,
            "error": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "questions": pack,
            "posted_state": posted,
            "n_calls": 1,
            "endpoint": _endpoint(),
        }
    out = dict(receipt) if isinstance(receipt, Mapping) else {"ok": False, "answers": {}}
    answers = out.get("answers")
    if not isinstance(answers, dict):
        answers = {}
        out["answers"] = answers
    if not answers and not out.get("error") and not out.get("skipped"):
        out["error"] = "empty"
    out.setdefault("kind", KIND_READ)
    out["questions"] = pack
    out["posted_state"] = posted
    out["n_calls"] = 1
    out["model"] = out.get("model") or MODEL
    out["endpoint"] = _endpoint()
    out["merge_sleeve"] = False
    return out


def _value_for(parsed: Mapping[str, Any], key: str) -> Any:
    choices = parsed.get("choices") if isinstance(parsed.get("choices"), Mapping) else {}
    scores = parsed.get("scores") if isinstance(parsed.get("scores"), Mapping) else {}
    nouls = parsed.get("nouls") if isinstance(parsed.get("nouls"), Mapping) else {}
    include = parsed.get("include_depth") if isinstance(parsed.get("include_depth"), Mapping) else {}
    if key in choices:
        return choices.get(key)
    if key in scores:
        return scores.get(key)
    if key in nouls:
        return nouls.get(key)
    if key.startswith("include_"):
        return include.get(key[len("include_") :])
    return None


def _pairs_for(
    parsed: Mapping[str, Any],
    keys: Iterable[str],
) -> list[tuple[str, Any]]:
    return [(str(key), _value_for(parsed, str(key))) for key in keys]


def fanout_exec_gov_news(
    state: dict[str, Any],
    *,
    seat: str = "news",
    branch: str = "cycle",
    evaluate_jev: bool = True,
    include_answers: Mapping[str, Any] | None = None,
    decision_answers: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One TypeSafe read for this state. Supplied answers are that return."""
    questions = exec_gov_news_questions(state, seat=seat, branch=branch)
    merged: dict[str, Any] = {}
    if isinstance(include_answers, Mapping):
        merged.update(dict(include_answers))
    if isinstance(decision_answers, Mapping):
        merged.update(dict(decision_answers))
    supplied = include_answers is not None or decision_answers is not None
    if supplied or not evaluate_jev:
        return {
            "ok": bool(merged),
            "skipped": None if evaluate_jev or supplied else "evaluate_jev_false",
            "answers": merged,
            "n_calls": 0,
            "kind": KIND_READ,
            "merge_sleeve": False,
            "questions": questions,
            "posted_state": _scrub(dict(state or {})),
            "endpoint": _endpoint(),
            "never_second_llm_hop": True,
        }
    receipt = evaluate_pack(dict(state), questions, timeout_s=timeout_s)
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    return {
        "ok": bool(answers) and receipt.get("ok") is True,
        "skipped": receipt.get("skipped"),
        "error": receipt.get("error"),
        "answers": answers,
        "n_calls": receipt.get("n_calls") or 0,
        "kind": KIND_READ,
        "merge_sleeve": False,
        "questions": questions,
        "posted_state": receipt.get("posted_state"),
        "model": receipt.get("model") or MODEL,
        "endpoint": receipt.get("endpoint") or _endpoint(),
        "never_second_llm_hop": True,
    }


def _news_receipt_path() -> Path:
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / "operator"
        / "judgment"
        / "news_choice.json"
    )


def _write_news_receipt(row: Mapping[str, Any]) -> None:
    path = _news_receipt_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(row), default=str), encoding="utf-8")
    except Exception:
        return


def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default on. An explicit off skips the ask and leaves the return unset."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(EXEC_GOV_NEWS_ENV, "")).strip().lower()
    if raw in _TRUTHY_OFF:
        return False
    if raw in _TRUTHY_ON or raw == "":
        return True
    return True


def _is_challenge_account(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN
        except (TypeError, ValueError):
            login_ok = False
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def _not_challenge(state: Mapping[str, Any]) -> bool:
    identity = dict(state.get("identity") or {})
    login = identity.get("login")
    ns = identity.get("ns")
    if login is None and ns is None:
        return False
    return not _is_challenge_account(login=login, ns=ns)


def _inside_window(
    events: Any,
    pre: float | None,
    post: float | None,
) -> list[dict[str, Any]] | None:
    """Events inside the returned window. A missing score classifies nothing."""
    if pre is None or post is None or not isinstance(events, list):
        return None
    inside: list[dict[str, Any]] = []
    for item in events:
        if not isinstance(item, Mapping):
            continue
        minutes = _number(item.get("minutes_from_as_of"))
        if minutes is None:
            continue
        if -float(post) <= minutes <= float(pre):
            inside.append(dict(item))
    return inside


@dataclass(frozen=True)
class ExecGovNewsDecision:
    """The return for this state. This object does not send or flatten."""

    disposition: str | None = None
    reason: str | None = None
    extra_pass: bool = False
    may_send: bool | float | None = None
    leave_orig: bool | float | None = None
    extra_cancel: bool | float | None = None
    extra_hold: bool | float | None = None
    cap_mult_overlay: float | None = None
    include_depth: dict[str, float] = field(default_factory=dict)
    missing_jev: bool = True
    jev_no_decision: bool = True
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload,
            "disposition": self.disposition,
            "reason": self.reason,
            "kind": KIND_READ,
            "flatten": False,
            "place": False,
            "apply": False,
            "persist_weight": None,
            "extra_pass": False,
            "sends": False,
            "may_send": self.may_send,
            "leave_orig": self.leave_orig,
            "extra_cancel": self.extra_cancel,
            "extra_hold": self.extra_hold,
            "cap_mult_overlay": self.cap_mult_overlay,
            "include_depth": dict(self.include_depth),
            "missing_jev": self.missing_jev,
            "jev_no_decision": self.jev_no_decision,
        }


def _base(
    *,
    seat: str,
    branch: str,
    enabled: bool,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "endpoint": _endpoint(),
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "overlay": EXEC_GOV_NEWS_ENV,
        "overlay_enabled": enabled,
        "seat": seat,
        "branch": branch,
        "mill_url": None,
        "invented": False,
        "flatten": False,
        "place": False,
        "apply": False,
        "extra_pass": False,
        "sends": False,
        "never_second_llm_hop": True,
        "merge_sleeve": False,
        **dict(extra or {}),
    }


def _answers_missing(answers: Mapping[str, Any] | None) -> bool:
    return answers is None or (isinstance(answers, Mapping) and not answers)


def compose_exec_gov_news(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    seat: str = "exec",
    branch: str = "place",
    seats: Iterable[str] | None = None,
    integer_cap_mult: float | None = None,
    integer_high_blackout: bool | None = None,
    environ: Mapping[str, str] | None = None,
    extra: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    timeout_s: float | None = None,
) -> ExecGovNewsDecision:
    """One hop. The fields are the return. A miss stays unset."""
    del seats
    state_map = dict(state or {})
    state_map["news"] = attach_feed(state_map.get("news") if isinstance(state_map.get("news"), Mapping) else None)
    enabled = overlay_enabled(environ=environ)
    seat_n = seat if seat in SEATS else "exec"
    branch_n = branch if branch in BRANCHES else branch
    base = _base(seat=seat_n, branch=branch_n, enabled=enabled, extra=extra)
    news = dict(state_map.get("news") or {})
    base["feed"] = news.get("feed")
    base["feed_source"] = news.get("source")
    base["n_events"] = news.get("n_events")
    base["spine_empty"] = news.get("spine_empty")
    base["nearest"] = news.get("nearest")
    base["next_future"] = news.get("next_future")
    base["open_gold_left_open"] = list(news.get("open_gold_left_open") or [])
    facts = dict(state_map.get("facts") or {})
    if integer_cap_mult is not None:
        facts["integer_cap_mult"] = integer_cap_mult
    if integer_high_blackout is not None:
        facts["integer_high_blackout"] = bool(integer_high_blackout)
    state_map["facts"] = facts
    state_map["seat"] = seat_n
    state_map["branch"] = branch_n
    state_map["model"] = MODEL

    asked = False
    error = None
    posted_state: Mapping[str, Any] | None = None
    question_ids: list[str] = []
    if _not_challenge(state_map):
        answers = {}
        base["skipped"] = "not_challenge"
        error = "not_challenge"
    elif not enabled:
        answers = {}
        base["skipped"] = "overlay_off"
        error = "overlay_off"
    elif _answers_missing(answers):
        if not evaluate_jev:
            answers = {}
            base["skipped"] = "evaluate_jev_false"
            error = "evaluate_jev_false"
        else:
            fanout = fanout_exec_gov_news(
                state_map,
                seat=seat_n,
                branch=branch_n,
                evaluate_jev=True,
                timeout_s=timeout_s,
            )
            answers = fanout.get("answers") if isinstance(fanout.get("answers"), Mapping) else {}
            asked = True
            error = fanout.get("error") or fanout.get("skipped")
            posted_state = fanout.get("posted_state") if isinstance(fanout.get("posted_state"), Mapping) else None
            question_ids = list(fanout.get("questions") or {})
            base["live_fanout_ok"] = fanout.get("ok")
            base["live_fanout_skipped"] = fanout.get("skipped")
            base["live_n_calls"] = fanout.get("n_calls")
            base["live_hop"] = f"{seat_n}:{branch_n}"
            base["endpoint"] = fanout.get("endpoint") or _endpoint()
    else:
        asked = True
        question_ids = list(exec_gov_news_questions(state_map, seat=seat_n, branch=branch_n))

    if not isinstance(answers, Mapping):
        answers = {}
    parsed = _read_answers(answers if answers else None)
    if asked:
        remember_state = dict(posted_state or _scrub(state_map) or {})
        if base.get("live_n_calls"):
            remembered = _pairs_for(parsed, question_ids)
            miss = None if answers else (str(error) if error else "empty")
        else:
            remembered = _pairs_for(parsed, answers.keys())
            miss = None
        _remember(remember_state, remembered, miss)
    choices = parsed["choices"]
    scores = parsed["scores"]
    nouls = parsed["nouls"]
    news_pick = parsed["news"]
    disposition = choices.get(_BRANCH_CHOICE.get(branch_n, ""))
    if branch_n == "derisk":
        decided = scores.get("cap_mult_overlay") is not None
    elif branch_n == "modify":
        decided = nouls.get("leave_orig") is not None
    else:
        decided = disposition is not None
    pre = scores.get("window_pre_min")
    post = scores.get("window_post_min")
    inside = _inside_window(news.get("events"), pre, post)
    sufficient = parsed["sufficient"]
    missing = not bool(answers)
    payload = {
        **base,
        "state_sufficient": sufficient,
        "native_limit_vs_market": choices.get("native_limit_vs_market"),
        "close_none_label": choices.get("close_none_label"),
        "news_cycle": news_pick.get("choice"),
        "action_scope": choices.get("action_scope"),
        "cluster_same_dir": nouls.get("cluster_same_dir"),
        "speak_hold": nouls.get("speak_hold"),
        "governor_ready": nouls.get("governor_ready"),
        "wall_pressure": scores.get("wall_pressure"),
        "derisk_tilt": scores.get("derisk_tilt"),
        "stress_continue": nouls.get("stress_continue"),
        "coloss_same_bet": nouls.get("coloss_same_bet"),
        "event_proximity": nouls.get("event_proximity"),
        "calendar_honest": nouls.get("calendar_honest"),
        "fire_window": scores.get("fire_window"),
        "limit_expiry": scores.get("limit_expiry"),
        "frozen_reprice": scores.get("frozen_reprice"),
        "thin_asia": scores.get("thin_asia"),
        "minstop_fit": scores.get("minstop_fit"),
        "pip8_fit": scores.get("pip8_fit"),
        "sl_fresh_fitness": scores.get("sl_fresh_fitness"),
        "pretrade_mgr_quality": scores.get("pretrade_mgr_quality"),
        "j46_tp_fit": scores.get("j46_tp_fit"),
        "harvest_observe": scores.get("harvest_observe"),
        "never_widen_pressure": scores.get("never_widen_pressure"),
        "fill_deviation_observe": scores.get("fill_deviation_observe"),
        "pending_still_same_setup": scores.get("pending_still_same_setup"),
        "opposite_lock": scores.get("opposite_lock"),
        "eurgbp_stack": scores.get("eurgbp_stack"),
        "window_pre_min": pre,
        "window_post_min": post,
        "inside_window": inside,
        "tie": bool(news_pick.get("tie")),
        "choice": news_pick.get("choice"),
        "probabilities": news_pick.get("probabilities") or {},
        "confidence": news_pick.get("confidence"),
        "question_ids": question_ids,
        "error": None if answers else error,
    }
    if integer_cap_mult is not None:
        payload["integer_cap_mult"] = integer_cap_mult
    if integer_high_blackout is not None:
        payload["integer_high_blackout"] = bool(integer_high_blackout)
    return ExecGovNewsDecision(
        disposition=disposition if isinstance(disposition, str) else None,
        reason=disposition if isinstance(disposition, str) else None,
        may_send=nouls.get("may_send"),
        leave_orig=nouls.get("leave_orig"),
        extra_cancel=nouls.get("extra_cancel"),
        extra_hold=nouls.get("extra_hold"),
        cap_mult_overlay=scores.get("cap_mult_overlay"),
        include_depth=dict(parsed["include_depth"]),
        missing_jev=missing,
        jev_no_decision=not decided,
        payload=payload,
    )


def compose_place(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="exec", branch="place", **kwargs)


def compose_modify(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="exec", branch="modify", **kwargs)


def compose_close(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="exec", branch="close", **kwargs)


def compose_governor(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="governor", branch="derisk", **kwargs)


def compose_news(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="news", branch="cycle", **kwargs)


def compose_cluster(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="cluster", branch="observe", **kwargs)


def compose_f5_fire(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ExecGovNewsDecision:
    return compose_exec_gov_news(state, answers, seat="f5_fire", branch="place", **kwargs)


def compose_from_intent(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    branch: str = "place",
    seats: Iterable[str] | None = None,
    evaluate_jev: bool = True,
    timeout_s: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """One intent, one ask. The decision dict is the return."""
    questions = exec_gov_news_questions(state, branch=branch, seats=seats)
    decision = compose_exec_gov_news(
        state,
        answers,
        branch=branch,
        seats=seats,
        evaluate_jev=evaluate_jev,
        timeout_s=timeout_s,
        **kwargs,
    )
    row = decision.as_dict()
    return {
        "questions": list(questions),
        "decision": row,
        "ask_together": True,
        "never_second_llm_hop": True,
        "evaluate_jev": bool(evaluate_jev),
        "model": MODEL,
        "endpoint": row.get("endpoint") or _endpoint(),
        "n_calls": row.get("live_n_calls") or 0,
    }


def maybe_run_news_skip(
    state: Mapping[str, Any] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """News hop for the Challenge book. Does not flatten and does not send."""
    st = dict(state or {})
    identity = dict(st.get("identity") or {})
    identity.setdefault("login", CHALLENGE_LOGIN)
    identity.setdefault("ns", CHALLENGE_NS)
    st["identity"] = identity
    decision = compose_news(st, None, environ=environ, timeout_s=timeout_s)
    row = decision.as_dict()
    row["never_flatten_tickets"] = sorted(NEVER_FLATTEN_TICKETS)
    row["flatten"] = False
    row["place"] = False
    row["mill_url"] = None
    row["hop"] = "news"
    row["pid"] = os.getpid()
    if row.get("news_cycle"):
        row["kind"] = "choice"
    _write_news_receipt(row)
    return row


def for_send_choke(
    state: Mapping[str, Any] | None = None,
    *,
    intent: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """News-cycle return. This choke does not send."""
    del intent
    return maybe_run_news_skip(state, environ=environ, timeout_s=timeout_s)
