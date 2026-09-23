"""Challenge bar and quote decisions are one Choice each.

Each question is the two sides of that condition. The decision is the
alternative with the unique highest probability. A tie is not a decision.
An empty answer is not a decision and does not restore the old boolean.
The ask waits until the bar on the card prints. A card with no candle
time has no timeout. The same facts return the choice already received.
This module never calls order_send and never labels an unanswered hop.
A row carries persist only when the hop returned a weight. An open ticket
is not closed from here.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.pipeline_choices.v1"

QUESTIONS: dict[str, dict[str, Any]] = {
    "last_bar": {
        "id": "pipe_last_bar",
        "instructions": (
            "Bar question: the last candle in this pull, and whether its "
            "interval has already elapsed. Pick one option. The last candle "
            "stays out of the decision series only when forming_bar_stays_out "
            "is the single highest probability. closed_bar_reaches keeps it. "
            "An empty answer or a tie does not drop it and does not read the "
            "elapsed flag as the decision. Do not close an open ticket."
        ),
        "criteria": {
            "closed_bar_reaches": "This last candle reaches the decision series.",
            "forming_bar_stays_out": "This last candle is still forming and stays out.",
        },
    },
    "unclosed_tail": {
        "id": "pipe_unclosed_tail",
        "instructions": (
            "Bar question: the tail of this pull whose close is after the "
            "clock. Pick one option. That tail stays out only when "
            "unclosed_stays_out is the single highest probability. "
            "unclosed_reaches keeps the tail in the series the decision sees. "
            "An empty answer or a tie does not drop the tail. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "unclosed_reaches": "The tail whose close is after the clock still reaches.",
            "unclosed_stays_out": "That tail stays out of the decision series.",
        },
    },
    "raw_series": {
        "id": "pipe_raw_series",
        "instructions": (
            "Bar question: this timeframe pull is shorter than the lookback "
            "the pipeline asked for. Pick one option. The pull is refused "
            "only when series_short is the single highest probability. "
            "series_reaches lets the pull through. An empty answer or a tie "
            "does not refuse it. Do not close an open ticket."
        ),
        "criteria": {
            "series_reaches": "This pull reaches the decision.",
            "series_short": "This pull is short of the lookback and does not reach.",
        },
    },
    "closed_series": {
        "id": "pipe_closed_series",
        "instructions": (
            "Bar question: the closed bars in this pull are shorter than the "
            "lookback. Pick one option. The pull is refused only when "
            "closed_series_short is the single highest probability. "
            "closed_series_reaches lets it through. An empty answer or a tie "
            "does not refuse it. Do not close an open ticket."
        ),
        "criteria": {
            "closed_series_reaches": "The closed bars reach the decision.",
            "closed_series_short": "The closed bars are short and do not reach.",
        },
    },
    "decision_m15": {
        "id": "pipe_decision_m15",
        "instructions": (
            "Bar question: the latest M15 whose close is not after the clock. "
            "Pick one option. That bar is the decision timestamp only when "
            "this_m15_is_the_close is the single highest probability. "
            "not_this_m15 leaves the timestamp unset. An empty answer or a "
            "tie does not stamp the bar. Do not close an open ticket."
        ),
        "criteria": {
            "this_m15_is_the_close": "This M15 is the decision timestamp.",
            "not_this_m15": "This M15 is not the decision timestamp.",
        },
    },
    "repair_lane": {
        "id": "pipe_repair_lane",
        "instructions": (
            "Quote question: whether this timeframe's bars are read from the "
            "tick quote instead of the candle print. Pick one option. The "
            "tick lane runs only when quote_repair_lane is the single highest "
            "probability. candle_lane keeps the candle print. An empty answer "
            "or a tie does not open the tick lane. Do not close an open ticket."
        ),
        "criteria": {
            "quote_repair_lane": "Read this timeframe from the tick quote.",
            "candle_lane": "Keep the candle print. Do not open the tick lane.",
        },
    },
    "tick_quote": {
        "id": "pipe_tick_quote",
        "instructions": (
            "Quote question: this candle failed the print check and a tick "
            "quote was reconstructed for the same bar. Pick one option. The "
            "tick quote replaces the print only when tick_quote_reaches is "
            "the single highest probability. candle_print_stands keeps the "
            "print. An empty answer or a tie does not replace it. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "tick_quote_reaches": "The tick quote reaches in place of this print.",
            "candle_print_stands": "The candle print stands. The tick quote stays out.",
        },
    },
    "m5_series": {
        "id": "pipe_m5_series",
        "instructions": (
            "Bar question: this M5 pull. The count held and the count requested "
            "are facts on the card. Pick one option. The pull stays out only "
            "when m5_short is the single highest probability. m5_reaches lets "
            "the pull through to refinement. An empty answer or a tie does "
            "not drop it. Do not close an open ticket."
        ),
        "criteria": {
            "m5_reaches": "This M5 pull reaches refinement.",
            "m5_short": "This M5 pull is short and stays out.",
        },
    },
    "prev_day_bars": {
        "id": "pipe_prev_day_bars",
        "instructions": (
            "Bar question: the previous weekday's bars, and whether their "
            "high and low reach the decision as PDH and PDL. Pick one option. "
            "They reach only when prev_day_bars_reach is the single highest "
            "probability. prev_day_bars_out leaves the level unset. An empty "
            "answer or a tie does not publish the level. Do not close an open ticket."
        ),
        "criteria": {
            "prev_day_bars_reach": "The previous weekday high and low reach the decision.",
            "prev_day_bars_out": "Those bars do not publish PDH and PDL.",
        },
    },
    "asian_bars": {
        "id": "pipe_asian_bars",
        "instructions": (
            "Bar question: the Asian-window bars, and whether their high and "
            "low reach the decision. Pick one option. They reach only when "
            "asian_bars_reach is the single highest probability. "
            "asian_bars_out leaves the level unset. An empty answer or a tie "
            "does not publish the level. Do not close an open ticket."
        ),
        "criteria": {
            "asian_bars_reach": "The Asian-window high and low reach the decision.",
            "asian_bars_out": "Those bars do not publish the Asian level.",
        },
    },
    "session_bars": {
        "id": "pipe_session_bars",
        "instructions": (
            "Bar question: the session-window bars named on this card, and whether "
            "their high and low reach the decision. Pick one option. They "
            "reach only when session_bars_reach is the single highest "
            "probability. session_bars_out leaves the level unset. An empty "
            "answer or a tie does not publish the level. Do not close an open ticket."
        ),
        "criteria": {
            "session_bars_reach": "The session-window high and low reach the decision.",
            "session_bars_out": "Those bars do not publish the session level.",
        },
    },
    "london_bars": {
        "id": "pipe_london_bars",
        "instructions": (
            "Bar question: the London-window bars, and whether their high and "
            "low reach the decision. Pick one option. They reach only when "
            "london_bars_reach is the single highest probability. "
            "london_bars_out leaves the level unset. An empty answer or a tie "
            "does not publish the level. Do not close an open ticket."
        ),
        "criteria": {
            "london_bars_reach": "The London-window high and low reach the decision.",
            "london_bars_out": "Those bars do not publish the London level.",
        },
    },
    "placement_brake": {
        "id": "pipe_placement_brake",
        "instructions": (
            "Launcher question: the kill flag and the halt flag are facts on "
            "this card. Pick one option. Placement stays observe-only only "
            "when brake_holds is the single highest probability. "
            "placement_reaches lets this cycle place. An empty answer or a "
            "tie does not hold the brake and does not send. "
            "Do not close an open ticket."
        ),
        "criteria": {
            "placement_reaches": "This cycle may place. The flags do not hold the brake.",
            "brake_holds": "The flags hold this cycle at observe-only.",
        },
    },
}

_ASK: Callable[..., dict[str, Any]] | None = None


def bind_ask(fn: Callable[..., dict[str, Any]] | None) -> None:
    """Test seam. Production leaves this unset and asks the live hop."""
    global _ASK
    _ASK = fn


# MT5 hour charts are an hour count above this base. PERIOD_H1 is 16385.
# The next band is the weekly chart. A code there has no duration here.
_HOUR_BAND = 16384
_WEEK_BAND = 32768
_MINUTE_SECONDS = 60

_CACHE: dict[str, str | None] = {}
_INFLIGHT: dict[str, "_Gate"] = {}
_LOCK = threading.Lock()
_deadline = threading.local()


class _Gate:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.value: str | None = None


def clear_cache() -> None:
    """Drop stored choices. The next call asks that state again."""

    with _LOCK:
        _CACHE.clear()


def bar_minutes(timeframe: object) -> float | None:
    """Minutes in one bar, read off the timeframe identifier.

    A minute chart's code is the minute count. An hour chart, including
    the daily chart, is the hour count above the hour band. A name such
    as M15 or H4 is that same count. Anything else has no duration.
    """

    if isinstance(timeframe, str):
        text = timeframe.strip()
        if not text:
            return None
        upper = text.upper()
        if len(upper) > 1 and upper[0] in ("M", "H") and upper[1:].isdigit():
            count = int(upper[1:])
            if count <= 0:
                return None
            if upper[0] == "M":
                return float(count)
            return float(count) * _MINUTE_SECONDS
        if text.isdigit():
            return bar_minutes(int(text))
        return None
    if isinstance(timeframe, bool) or timeframe is None:
        return None
    if isinstance(timeframe, int):
        code = timeframe
    elif isinstance(timeframe, float):
        if not timeframe.is_integer():
            return None
        code = int(timeframe)
    else:
        return None
    if code <= 0:
        return None
    if code < _HOUR_BAND:
        return float(code)
    if code < _WEEK_BAND:
        hours = code - _HOUR_BAND
        if hours <= 0:
            return None
        return float(hours) * _MINUTE_SECONDS
    return None


def _parse_clock(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _candle_open(facts: Mapping[str, Any]) -> datetime | None:
    for key in ("bar", "last_time", "candle_time", "time"):
        parsed = _parse_clock(facts.get(key))
        if parsed is not None:
            return parsed
    return None


def bar_deadline_s(
    facts: Mapping[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> float | None:
    """Seconds until the bar on the card next prints.

    The print is the candle open plus one bar. When that instant is ahead,
    it is the deadline. When it has passed, the deadline is the following
    print of the same timeframe. No open, or no timeframe, means the ask
    has no expiry and the caller does not invent a wait.
    """

    card = facts or {}
    opened = _candle_open(card)
    minutes = bar_minutes(card.get("timeframe"))
    if minutes is None:
        minutes = bar_minutes(card.get("tf"))
    if minutes is None:
        raw = _finite(card.get("interval_minutes"))
        if raw is not None and raw > 0:
            minutes = raw
    if opened is None or minutes is None or minutes <= 0:
        return None
    span = timedelta(seconds=minutes * _MINUTE_SECONDS)
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    else:
        clock = clock.astimezone(timezone.utc)
    opened = opened.astimezone(timezone.utc)
    elapsed = (clock - opened).total_seconds()
    span_s = span.total_seconds()
    if span_s <= 0:
        return None
    if elapsed < 0:
        seconds = -elapsed + span_s
    else:
        steps = int(elapsed // span_s) + 1
        seconds = (opened + timedelta(seconds=steps * span_s) - clock).total_seconds()
    if seconds <= 0 or seconds != seconds or seconds == float("inf"):
        return None
    return float(seconds)


def _state_key(question: str, spot_id: str, facts: Mapping[str, Any]) -> str:
    return json.dumps(
        {"facts": dict(facts), "question": question, "spot": spot_id},
        sort_keys=True,
        default=str,
    )


def _arm_deadline(deadline: float | None, fn: Callable[[], Any]) -> Any:
    """The post waits until this bar prints.

    The current client reads ``seconds_from_clock`` on the card. A client
    that still has a socket wait uses that same number for this thread
    only, and only while this ask is in flight. No deadline leaves the
    post with no timeout.
    """

    previous_on = getattr(_deadline, "on", False)
    previous_seconds = getattr(_deadline, "seconds", None)
    _deadline.on = True
    _deadline.seconds = deadline
    try:
        try:
            import src.judgment.jev_client as client

            current = getattr(client, "_socket_timeout", None)
            if callable(current) and not getattr(current, "_pipeline_deadline", False):
                with _LOCK:
                    current = getattr(client, "_socket_timeout", None)
                    if callable(current) and not getattr(current, "_pipeline_deadline", False):
                        previous = current

                        def _wait(passed: float | None) -> float | None:
                            if getattr(_deadline, "on", False):
                                seconds = getattr(_deadline, "seconds", None)
                                if seconds is None:
                                    return None
                                return float(seconds)
                            return previous(passed)

                        _wait._pipeline_deadline = True  # type: ignore[attr-defined]
                        client._socket_timeout = _wait
        except Exception:
            pass
        return fn()
    finally:
        _deadline.on = previous_on
        _deadline.seconds = previous_seconds


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _returned_persist(hop: Mapping[str, Any]) -> float | None:
    """The weight this hop returned. An empty answer does not become 0.00."""

    for key in ("persist_weight", "persist"):
        if key not in hop:
            continue
        number = _finite(hop.get(key))
        if number is not None:
            return number
    return None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def record_path() -> Path:
    override = (os.environ.get("GTOS_PIPELINE_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "pipeline_choices.jsonl"
    )


def _append(row: Mapping[str, Any]) -> None:
    """One complete line. The memo lock keeps concurrent slots from tearing it."""
    try:
        path = record_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(dict(row), sort_keys=True, default=str) + "\n"
    except OSError:
        return
    with _LOCK:
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            return


def spot(question: str, *, spot: str, facts: Mapping[str, Any] | None = None) -> str | None:
    """Return the unique highest alternative, or None when there is no decision.

    None does not restore a boolean and does not name an unanswered hop.
    One state asks once. A later call with the same facts returns that choice.
    Independent states do not wait on each other.
    """

    spec = QUESTIONS.get(question)
    if spec is None:
        return None
    card = dict(facts or {})
    card.pop("persist", None)
    card.pop("persist_weight", None)
    for stale in ("seconds_from_clock", "seconds_until_cycle", "cycle_wait"):
        card.pop(stale, None)
    key = _state_key(question, str(spot), card)
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
        gate = _INFLIGHT.get(key)
        if gate is None:
            gate = _Gate()
            _INFLIGHT[key] = gate
            owner = True
        else:
            owner = False
    if not owner:
        owned = getattr(_deadline, "owned", None)
        if owned is not None and key in owned:
            return None
        gate.event.wait()
        return gate.value
    owned = getattr(_deadline, "owned", None)
    if owned is None:
        owned = set()
        _deadline.owned = owned
    owned.add(key)
    winner: str | None = None
    cache_it = False
    try:
        winner, cache_it = _ask(question, str(spot), card, spec)
    finally:
        owned.discard(key)
        if cache_it:
            with _LOCK:
                _CACHE[key] = winner
        gate.value = winner
        gate.event.set()
        with _LOCK:
            if _INFLIGHT.get(key) is gate:
                _INFLIGHT.pop(key, None)
    return winner


def _ask(
    question: str,
    spot_id: str,
    card: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> tuple[str | None, bool]:
    options = tuple(spec["criteria"])
    deadline = bar_deadline_s(card)
    asked_facts = dict(card)
    if deadline is not None:
        asked_facts["seconds_from_clock"] = deadline
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "question_id": spec["id"],
        "spot": spot_id,
        "choice": None,
        "decision_emitted": False,
        "order_send": False,
        "model": MODEL,
        "error": None,
        "deadline_s": deadline,
    }
    payload = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "spot": spot_id,
        "facts": asked_facts,
    }
    winner: str | None = None
    try:
        if _ASK is not None:
            hop = _ASK(
                payload,
                question_id=spec["id"],
                instructions=spec["instructions"],
                criteria=spec["criteria"],
                timeout_s=deadline,
            ) or {}
        else:
            from src.judgment.jev_client import calls_enabled
            from src.judgment.rung_choice import ask_choice

            if not calls_enabled():
                row["error"] = "call_not_made"
                hop = {}
            else:
                hop = _arm_deadline(
                    deadline,
                    lambda: ask_choice(
                        payload,
                        question_id=spec["id"],
                        instructions=spec["instructions"],
                        criteria=spec["criteria"],
                        timeout_s=deadline,
                    ),
                ) or {}
        if isinstance(hop, dict):
            weight = _returned_persist(hop)
            if weight is not None:
                row["persist"] = weight
        choice = hop.get("choice") if isinstance(hop, dict) else None
        if isinstance(hop, dict) and hop.get("decision_emitted") and choice in options:
            winner = str(choice)
            row["choice"] = winner
            row["probability"] = hop.get("probability")
            row["probabilities"] = hop.get("probabilities") or {}
            row["decision_emitted"] = True
            row["model"] = hop.get("model") or MODEL
        else:
            row["error"] = (hop.get("error") if isinstance(hop, dict) else None) or row["error"] or "no_unique_highest"
            if isinstance(hop, dict):
                row["probabilities"] = hop.get("probabilities") or {}
    except Exception as exc:  # noqa: BLE001 — ingest must not raise into the writer
        row["error"] = type(exc).__name__
        winner = None
        _append(row)
        return winner, False
    _append(row)
    return winner, row.get("error") != "call_not_made"
