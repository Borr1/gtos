"""Launcher flags are facts on the ask. The cycle wait is the score for one print.

An empty answer, a tie, or an error does not copy an argv number back and does
not invent a wait. A score is how many seconds before that print the cycle
starts, and it is not used for a later print. Until one has returned for the
print ahead, the cycle starts at that print.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime, timedelta, timezone

_RETURNED: dict[str, float] = {}
_RETURNED_KEY: dict[str, str] = {}
_ASK_KEY = ""
_LOCK = threading.Lock()
_CYCLE_CLOCK: datetime | None = None
_INFLIGHT = False
_PACK_KEY: str | None = None
_ATTEMPT: tuple[str, str | None] | None = None
_WATCHED: object = None
_CYCLE_WAIT: float | None = None
_CYCLE_WAIT_PRINT: str | None = None
_AIMED_PRINT: float | None = None
_SERVED_PRINT: float | None = None
_DISPATCHED_PRINT: float | None = None
_WAKE_BEFORE_PRINT = False
_LAST_CYCLE_SECONDS: float | None = None

_EMPTY = (
    "An empty score leaves it unset. "
    "A tie leaves it unset. "
    "An error leaves it unset. "
    "This question does not send."
)

_QUESTIONS: tuple[tuple[str, str], ...] = (
    (
        "cycle_wait",
        "The score you return is how many seconds before the next print of the fastest "
        "watched bar this cycle starts. The cycle calculates that bar's move and has to "
        "finish before the print. A cycle takes minutes. "
        "The seconds until each watched print, and the seconds the previous cycle took, "
        "are facts on this card. They are not the wait. "
        + _EMPTY,
    ),
    (
        "transient_retry_cap",
        "The score you return is how many same-class placement failures this bar may attempt. "
        "The argv retry flag on this card is a fact. It is not the cap. "
        + _EMPTY,
    ),
    (
        "friday_cutoff_minute",
        "The score you return is the minute of the UTC day for the Friday new-risk clock. "
        "0 is 00:00 UTC. The argv clock on this card is a fact. It is not this clock. "
        "An empty score leaves the clock unset. "
        "A tie leaves the clock unset. "
        "An error leaves the clock unset. "
        "This question does not flatten.",
    ),
    (
        "weekend_flat_minute",
        "The score you return is the minute of the UTC day for the weekend-flat clock. "
        "0 is 00:00 UTC. The argv clock on this card is a fact. It is not this clock. "
        "An empty score leaves the clock unset. "
        "A tie leaves the clock unset. "
        "An error leaves the clock unset. "
        "This question does not flatten.",
    ),
    (
        "dead_window_start_hour",
        "The score you return is the UTC hour at which the thin window starts. "
        "0 is 00:00 UTC. Hours after that start, through the end of the UTC day, are the window. "
        + _EMPTY,
    ),
    (
        "thin_hour_end_hour",
        "The score you return is the UTC hour at which the thin session ends. "
        + _EMPTY,
    ),
    (
        "high_pre_minutes",
        "The score you return is how many minutes before a named high the window opens. "
        + _EMPTY,
    ),
    (
        "high_post_minutes",
        "The score you return is how many minutes after a named high the window stays open. "
        + _EMPTY,
    ),
    (
        "calendar_prime_pre_minutes",
        "The score you return is how many minutes before a named high the prime window opens. "
        + _EMPTY,
    ),
    (
        "limit_expiry_seconds",
        "The score you return is how many seconds a resting limit lives past the broker tick. "
        + _EMPTY,
    ),
    (
        "limit_expiry_bars",
        "The score you return is how many closed bars a resting limit lives. "
        + _EMPTY,
    ),
    (
        "thin_hour_limit_expiry_bars",
        "The score you return is how many decision bars a thin-hour resting limit lives. "
        + _EMPTY,
    ),
    (
        "fill_deviation_r",
        "The score you return is the adverse fill deviation, in R of the intent stop, past which the birth is a different risk. "
        + _EMPTY,
    ),
    (
        "manage_ttl_min_s",
        "The score you return is the shortest manage-row age in seconds that is still actionable. "
        + _EMPTY,
    ),
    (
        "manage_ttl_max_s",
        "The score you return is the longest manage-row age in seconds that is still actionable. "
        + _EMPTY,
    ),
    (
        "manage_ttl_default_s",
        "The score you return is the manage-row lifetime in seconds when the row names none. "
        + _EMPTY,
    ),
    (
        "close_none_max_retries",
        "The score you return is how many broker-None closes this ticket may attempt before the writer stops retrying. "
        + _EMPTY,
    ),
    (
        "close_none_backoff_s",
        "The score you return is how many seconds the writer waits after a broker-None close before it tries again. "
        + _EMPTY,
    ),
    (
        "close_none_cache_max",
        "The score you return is how many broker-None tickets the writer remembers. "
        + _EMPTY,
    ),
    (
        "auto_be_min_lock_r",
        "The score you return is the minimum lock past entry, in R of the original stop, for an economic breakeven. "
        + _EMPTY,
    ),
    (
        "auto_be_max_lock_r",
        "The score you return is the maximum lock past entry, in R of the original stop, for an economic breakeven. "
        + _EMPTY,
    ),
    (
        "auto_be_extra_spreads",
        "The score you return is how many extra spreads of room sit on top of the round-trip cost of an economic breakeven. "
        + _EMPTY,
    ),
    (
        "fx_sl_cooldown_hours",
        "The score you return is how many hours an FX major waits after an SL-class close. "
        + _EMPTY,
    ),
    (
        "sibling_window_minutes",
        "The score you return is how many minutes a same-symbol re-entry waits after a close. "
        + _EMPTY,
    ),
    (
        "fx_min_stop_pips",
        "The score you return is the stop width in pips at which an FX DSP stop is the cliff. "
        + _EMPTY,
    ),
    (
        "min_stop_ticks",
        "The score you return is the stop width in ticks at which a stop is the cliff. "
        + _EMPTY,
    ),
    (
        "sibling_retain_seconds",
        "The score you return is how many seconds a recorded close stays on the sibling card. "
        + _EMPTY,
    ),
    (
        "calendar_lookback_days",
        "The score you return is how many days of past named highs stay on the spine. "
        + _EMPTY,
    ),
    (
        "calendar_horizon_days",
        "The score you return is how many days of future named highs stay on the spine. "
        + _EMPTY,
    ),
    (
        "sl_class_adverse_r",
        "The score you return is the adverse R at which a close counts as an SL-class close. "
        + _EMPTY,
    ),
)

_HOURS = frozenset({"dead_window_start_hour", "thin_hour_end_hour"})
_CLOCKS = frozenset({"friday_cutoff_minute", "weekend_flat_minute"})
_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_POSITION = (
    " The score is your position on the named levels."
    " It may sit between them."
)

# The unit of each score. Anchors are facts already on the card, in that unit.
_UNIT = {
    "cycle_wait": "seconds",
    "transient_retry_cap": "count",
    "friday_cutoff_minute": "minute_of_day",
    "weekend_flat_minute": "minute_of_day",
    "dead_window_start_hour": "hour_of_day",
    "thin_hour_end_hour": "hour_of_day",
    "high_pre_minutes": "minutes",
    "high_post_minutes": "minutes",
    "calendar_prime_pre_minutes": "minutes",
    "limit_expiry_seconds": "seconds",
    "limit_expiry_bars": "bars",
    "thin_hour_limit_expiry_bars": "bars",
    "fill_deviation_r": "r",
    "manage_ttl_min_s": "seconds",
    "manage_ttl_max_s": "seconds",
    "manage_ttl_default_s": "seconds",
    "close_none_max_retries": "count",
    "close_none_backoff_s": "seconds",
    "close_none_cache_max": "count",
    "auto_be_min_lock_r": "r",
    "auto_be_max_lock_r": "r",
    "auto_be_extra_spreads": "spreads",
    "fx_sl_cooldown_hours": "hours",
    "sibling_window_minutes": "minutes",
    "fx_min_stop_pips": "pips",
    "min_stop_ticks": "ticks",
    "sibling_retain_seconds": "seconds",
    "calendar_lookback_days": "days",
    "calendar_horizon_days": "days",
    "sl_class_adverse_r": "r",
}


def _flag(name: str) -> str | None:
    argv = [str(arg) for arg in sys.argv]
    if name in argv:
        index = argv.index(name)
        if index + 1 < len(argv):
            return argv[index + 1]
    prefix = name + "="
    for arg in argv:
        if arg.startswith(prefix):
            return arg[len(prefix):]
    return None


def launcher_facts() -> dict[str, str]:
    """The process flags, when the launcher passed them. Absent when it did not."""

    named = {
        "launcher_f5_minimal_size_usd": "--f5-minimal-size-usd",
        "launcher_notional_initial_usd": "--f5-notional-initial-usd",
        "launcher_transient_retry_cap": "--transient-retry-cap",
        "launcher_poll_seconds": "--poll-seconds",
        "launcher_friday_cutoff_utc": "--f5-friday-new-risk-cutoff-utc",
        "launcher_weekend_flat_utc": "--f5-weekend-flat-utc",
    }
    out: dict[str, str] = {}
    for key, flag in named.items():
        value = _flag(flag)
        if value not in (None, ""):
            out[key] = value
    return out


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    else:
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def clock_from_minutes(number: object) -> tuple[int, int] | None:
    """A returned minute-of-day as HH:MM. Anything else is unset."""

    value = _finite(number)
    if value is None or value < 0:
        return None
    whole = int(value)
    if whole != value:
        return None
    hour, minute = divmod(whole, 60)
    if hour > 23:
        return None
    return hour, minute


def period_seconds(timeframe: object) -> float | None:
    """Bar length of one MetaTrader timeframe code.

    Minutes are the code itself. Hour codes pack the hour count in the low bits
    under 0x4000 (H1 is one hour, H4 is four, D1 is twenty-four). Week codes pack
    under 0x8000. A month has no fixed length, so that code is not a print.
    """

    try:
        code = int(timeframe)
    except (TypeError, ValueError):
        return None
    if isinstance(timeframe, bool) or code <= 0:
        return None
    high = code & 0xF000
    low = code & 0x0FFF
    if high == 0:
        minutes = float(code)
    elif high == 0x4000 and low > 0:
        minutes = float(low) * 60.0
    elif high == 0x8000 and low > 0:
        minutes = float(low) * 7.0 * 24.0 * 60.0
    else:
        return None
    if minutes <= 0:
        return None
    return minutes * 60.0


def timeframe_code(name: object) -> int | None:
    """MetaTrader code for a timeframe name. The library is the source."""

    text = str(name or "").strip().upper()
    if not text:
        return None
    try:
        import MetaTrader5 as mt5

        named = getattr(mt5, "TIMEFRAME_" + text, None)
        if isinstance(named, int) and not isinstance(named, bool):
            return named
    except Exception:
        pass
    if len(text) < 2:
        return None
    prefix, rest = text[0], text[1:]
    try:
        count = int(rest)
    except ValueError:
        return None
    if count <= 0:
        return None
    if prefix == "M":
        return count
    if prefix == "H":
        return 0x4000 | count
    return None


def _one_span(name: str) -> float | None:
    period = period_seconds(timeframe_code(name))
    if period is None or period <= 0:
        return None
    return period


def _clock_parts(text: object) -> tuple[int, int, int] | None:
    if not isinstance(text, str):
        return None
    bits = text.strip().split(":")
    if len(bits) < 2 or len(bits) > 3:
        return None
    try:
        hour = int(bits[0])
        minute = int(bits[1])
        second = int(bits[2]) if len(bits) == 3 else 0
    except ValueError:
        return None
    if hour < 0 or minute < 0 or second < 0 or hour > 23 or minute > 59 or second > 59:
        return None
    return hour, minute, second


def _seconds_until_period(period: float, now: float) -> float:
    remainder = now % period
    if remainder == 0.0:
        return 0.0
    return period - remainder


def _seconds_until_weekday_clock(text: object, day_name: str, now: datetime) -> float | None:
    parts = _clock_parts(text)
    if parts is None:
        return None
    hour, minute, second = parts
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cursor = now
    for _day in _WEEKDAYS + _WEEKDAYS:
        candidate = cursor.replace(hour=hour, minute=minute, second=second, microsecond=0)
        if candidate.strftime("%A") == day_name and candidate >= now:
            return (candidate - now).total_seconds()
        cursor = cursor + timedelta(days=1)
    return None


def _minute_of_day(now: datetime) -> float | None:
    minute = _one_span("M1")
    if minute is None:
        return None
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    raw = (now - start).total_seconds() / minute
    return float(int(raw))


def _minute_of_clock(text: object, now: datetime) -> float | None:
    parts = _clock_parts(text)
    if parts is None:
        return None
    hour, minute, second = parts
    return _minute_of_day(now.replace(hour=hour, minute=minute, second=second, microsecond=0))


def _held_size_facts() -> dict[str, float]:
    try:
        from src.components.ultimate_book.minimal_size import held_anchor_facts
    except Exception:
        return {}
    try:
        raw = held_anchor_facts()
    except Exception:
        return {}
    out: dict[str, float] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        number = _finite(value)
        if number is not None:
            out[str(key)] = number
    return out


def _prefixed(payload: dict, prefixes: tuple[str, ...]) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    for key, value in payload.items():
        name = str(key)
        if not any(name.startswith(prefix) for prefix in prefixes):
            continue
        number = _finite(value)
        if number is not None:
            found.append((name, number))
    return found


def _named(payload: dict, keys: tuple[str, ...]) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    for key in keys:
        number = _finite(payload.get(key))
        if number is not None:
            found.append((key, number))
    return found


def _anchors_for_unit(unit: str, payload: dict) -> list[tuple[str, float]]:
    """Facts already on the card, in this hop's unit. The spine drops a short list."""

    if unit == "seconds":
        return _prefixed(
            payload,
            (
                "seconds_until_now",
                "seconds_until_print_",
                "seconds_last_cycle",
                "seconds_until_friday_",
                "seconds_until_weekend_",
            ),
        )
    if unit == "minutes":
        return _prefixed(payload, ("period_minutes_", "minutes_until_"))
    if unit == "hours":
        return _prefixed(payload, ("period_hours_", "hours_until_"))
    if unit == "days":
        return _prefixed(payload, ("period_days_", "days_until_"))
    if unit == "bars":
        return _prefixed(payload, ("bars_of_",))
    if unit == "minute_of_day":
        return _named(
            payload,
            ("now_minute_of_day", "friday_cutoff_minute_fact", "weekend_flat_minute_fact"),
        )
    if unit == "hour_of_day":
        return _named(
            payload,
            ("now_hour_of_day", "friday_cutoff_hour_fact", "weekend_flat_hour_fact"),
        )
    if unit == "usd":
        return _named(
            payload,
            (
                "launcher_f5_minimal_size_usd",
                "launcher_notional_initial_usd",
                "notional_equity",
                "notional_initial",
                "day_start_notional",
                "notional_high_water",
            ),
        )
    return []


def _stamp_clock(payload: dict, launcher: object) -> None:
    """Durations from now to each watched print, and to the Friday clocks on the card."""

    now_ts = time.time()
    now = datetime.fromtimestamp(now_ts, timezone.utc)
    payload["seconds_until_now"] = now_ts - now_ts
    periods: list[tuple[int, float]] = []
    for code in _watched_codes(launcher):
        period = period_seconds(code)
        if period is None or period <= 0:
            continue
        periods.append((code, period))
        payload[f"seconds_until_print_{code}"] = _seconds_until_period(period, now_ts)
        payload[f"period_seconds_{code}"] = period
    if _LAST_CYCLE_SECONDS is not None:
        payload["seconds_last_cycle"] = _LAST_CYCLE_SECONDS
    if periods:
        fastest = min(period for _code, period in periods)
        for code, period in periods:
            payload[f"bars_of_{code}"] = period / fastest
    minute_of_day = _minute_of_day(now)
    if minute_of_day is not None:
        payload["now_minute_of_day"] = minute_of_day
    payload["now_hour_of_day"] = float(now.hour)
    one_minute = _one_span("M1")
    one_hour = _one_span("H1")
    one_day = _one_span("D1")
    for code, period in periods:
        if one_minute is not None:
            payload[f"period_minutes_{code}"] = period / one_minute
        if one_hour is not None:
            payload[f"period_hours_{code}"] = period / one_hour
        if one_day is not None:
            payload[f"period_days_{code}"] = period / one_day
    friday = payload.get("launcher_friday_cutoff_utc")
    weekend = payload.get("launcher_weekend_flat_utc")
    for key, text in (
        ("seconds_until_friday_cutoff", friday),
        ("seconds_until_weekend_flat", weekend),
    ):
        if not isinstance(text, str) or not text:
            continue
        seconds = _seconds_until_weekday_clock(text, "Friday", now)
        if seconds is not None:
            payload[key] = seconds
    for key, text in (
        ("friday_cutoff_minute_fact", friday),
        ("weekend_flat_minute_fact", weekend),
    ):
        if isinstance(text, str) and text:
            minute = _minute_of_clock(text, now)
            if minute is not None:
                payload[key] = minute
    for key, text in (
        ("friday_cutoff_hour_fact", friday),
        ("weekend_flat_hour_fact", weekend),
    ):
        parts = _clock_parts(text) if isinstance(text, str) else None
        if parts is not None:
            payload[key] = float(parts[0])
    stamped = [
        item for item in payload.items()
        if str(item[0]).startswith((
            "seconds_until_now",
            "seconds_until_print_",
            "seconds_until_friday_",
            "seconds_until_weekend_",
        ))
    ]
    for key, value in stamped:
        number = _finite(value)
        if number is None:
            continue
        suffix = str(key)[len("seconds_until_"):]
        if one_minute is not None:
            payload[f"minutes_until_{suffix}"] = number / one_minute
        if one_hour is not None:
            payload[f"hours_until_{suffix}"] = number / one_hour
        if one_day is not None:
            payload[f"days_until_{suffix}"] = number / one_day
    for key, value in _held_size_facts().items():
        payload.setdefault(key, value)


def watched_clock_anchors(unit: str) -> list[tuple[str, float]]:
    """Clock anchors for one unit, from the bars this process is watching."""

    return list(_anchors_for_unit(str(unit), _card(_WATCHED)))


def _with_position(instructions: str) -> str:
    text = str(instructions).strip()
    if "named levels" in text:
        return text
    return text + _POSITION


def _watched_codes(launcher: object) -> tuple[int, ...]:
    tags = getattr(launcher, "_tf_tags", None)
    if not isinstance(tags, dict):
        return ()
    codes: list[int] = []
    for timeframe in tags:
        try:
            code = int(timeframe)
        except (TypeError, ValueError):
            continue
        if isinstance(timeframe, bool) or code <= 0:
            continue
        codes.append(code)
    return tuple(sorted(set(codes)))


def _periods(launcher: object) -> list[float]:
    found: list[float] = []
    for code in _watched_codes(launcher):
        period = period_seconds(code)
        if period is not None and period > 0:
            found.append(period)
    return found


def _fastest_period(launcher: object) -> float | None:
    periods = _periods(launcher)
    if not periods:
        return None
    return min(periods)


def note_cycle_clock(now: datetime | None) -> None:
    """The clock of the cycle now running. None outside that cycle."""

    global _CYCLE_CLOCK
    if now is None:
        _CYCLE_CLOCK = None
        return
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    _CYCLE_CLOCK = now.astimezone(timezone.utc)


def cycle_clock() -> datetime | None:
    return _CYCLE_CLOCK


def seconds_until_fastest_print(launcher: object = None, now: float | None = None) -> float | None:
    """Seconds from the clock until the next print of the fastest watched bar.

    The print is the timeframe boundary on the clock. No watched bar leaves this unset.
    """

    watched = launcher if launcher is not None else _WATCHED
    fastest = _fastest_period(watched)
    if fastest is None:
        return None
    clock = time.time() if now is None else float(now)
    remainder = clock % fastest
    if remainder == 0.0:
        return 0.0
    return fastest - remainder


def ask_deadline_seconds() -> float | None:
    """Seconds from this call until the bar this process is waiting on prints.

    During a cycle the print is taken from that cycle's clock, and these
    seconds are that instant minus the wall clock now. A question asked
    later in the same cycle still ends on that print. Outside a cycle the
    clock is the wall. None when it has no bar.
    """

    stamped = cycle_clock()
    if stamped is not None:
        until = seconds_until_fastest_print(_WATCHED, now=stamped.timestamp())
        if until is None:
            return None
        return stamped.timestamp() + float(until) - time.time()
    return seconds_until_fastest_print(_WATCHED)


def _print_at_or_after(now: float, period: float) -> float:
    remainder = now % period
    if remainder == 0.0:
        return now
    return now + (period - remainder)


def _unserved_print(now: float, period: float) -> float:
    """The next print this process has not already run a cycle for."""

    candidate = _print_at_or_after(now, period)
    served = _SERVED_PRINT
    if served is None:
        return candidate
    while candidate <= served:
        candidate += period
    return candidate


def _print_token(aimed: float) -> str:
    return format(aimed, ".6f")


def _cycle_wait_question() -> str:
    for qid, text in _QUESTIONS:
        if qid == "cycle_wait":
            return text
    return ""


def _cycle_wait_for_print(launcher: object, aimed: float) -> float | None:
    """The lead for this print. A score stored for another print is not returned."""

    global _CYCLE_WAIT, _CYCLE_WAIT_PRINT
    token = _print_token(aimed)
    if _CYCLE_WAIT_PRINT == token:
        return _CYCLE_WAIT
    _CYCLE_WAIT = None
    _CYCLE_WAIT_PRINT = None
    try:
        from src.judgment.nineteen import score
    except Exception:
        return None
    card = _card(launcher)
    anchors = _anchors_for_unit("seconds", card)
    try:
        number = score(
            card,
            question_id="cycle_wait",
            instructions=_with_position(_cycle_wait_question()),
            anchors=anchors,
        )
    except Exception:
        return None
    value = _finite(number)
    if value is None or value < 0:
        return None
    _CYCLE_WAIT = float(value)
    _CYCLE_WAIT_PRINT = token
    return _CYCLE_WAIT


def note_cycle_served() -> None:
    """The cycle that just ran belongs to the print ``next_cycle_wake`` aimed at."""

    global _SERVED_PRINT
    if _AIMED_PRINT is not None:
        _SERVED_PRINT = _AIMED_PRINT


def note_last_cycle_seconds(seconds: float) -> None:
    """How long the cycle that just ran took. A fact on the next wait's card."""

    global _LAST_CYCLE_SECONDS
    number = _finite(seconds)
    if number is None or number < 0:
        return
    _LAST_CYCLE_SECONDS = float(number)


def wake_is_before_print() -> bool:
    """True when the wait just returned ends before the print it was aimed at."""

    return bool(_WAKE_BEFORE_PRINT)


def next_cycle_wake(launcher: object = None) -> tuple[float | None, datetime | None]:
    """The wait, and the instant that wait ends.

    A returned cycle_wait is how many seconds before the next unserved print
    the cycle starts. The card it is scored from carries the seconds until
    each watched print. That score is kept for that print only. Until one
    returns, the instant is the print itself.
    """

    global _WATCHED, _AIMED_PRINT, _DISPATCHED_PRINT, _WAKE_BEFORE_PRINT
    _WAKE_BEFORE_PRINT = False
    if launcher is not None:
        _WATCHED = launcher
    watched = launcher if launcher is not None else _WATCHED
    ensure_ask(watched)
    fastest = _fastest_period(watched)
    if fastest is None:
        return None, None
    now = time.time()
    aimed = _unserved_print(now, fastest)
    _AIMED_PRINT = aimed
    print_at = datetime.fromtimestamp(aimed, tz=timezone.utc)
    dispatched = _DISPATCHED_PRINT
    served = _SERVED_PRINT
    if dispatched is not None and dispatched == aimed and (
        served is None or served < aimed
    ):
        remain = aimed - now
        if remain > 0:
            return remain, print_at
        nxt = aimed + fastest
        wait = nxt - now
        if wait > 0:
            return wait, datetime.fromtimestamp(nxt, tz=timezone.utc)
        return 0.0, datetime.fromtimestamp(nxt, tz=timezone.utc)
    number = _cycle_wait_for_print(watched, aimed)
    if number is not None and number >= 0:
        start = aimed - float(number)
        if start > now:
            _DISPATCHED_PRINT = aimed
            _WAKE_BEFORE_PRINT = True
            return start - now, datetime.fromtimestamp(start, tz=timezone.utc)
        if now < aimed:
            _DISPATCHED_PRINT = aimed
            _WAKE_BEFORE_PRINT = True
            return 0.0, datetime.fromtimestamp(now, tz=timezone.utc)
        _DISPATCHED_PRINT = aimed
        remain = aimed - now
        if remain > 0:
            return remain, print_at
        return 0.0, print_at
    remain = aimed - now
    if remain > 0:
        return remain, print_at
    return 0.0, print_at


def _score_block(block: object) -> float | None:
    if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
        return None
    probabilities = block.get("probabilities")
    if isinstance(probabilities, dict) and probabilities:
        try:
            from src.judgment.jev_questions import unique_highest

            if unique_highest(probabilities) is None:
                return None
        except Exception:
            return None
    if "score" in block:
        if block.get("score") is None:
            return None
        return _finite(block.get("score"))
    if "value" in block:
        if block.get("value") is None:
            return None
        return _finite(block.get("value"))
    return None


def _stable_key(launcher: object) -> str:
    payload = {
        "facts": launcher_facts(),
        "namespace": _flag("--namespace") or "",
        "profile": _flag("--profile") or "",
        "timeframes": list(_watched_codes(launcher)),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def _bar_token(launcher: object) -> str | None:
    fastest = _fastest_period(launcher)
    if fastest is None:
        return None
    clock = time.time()
    opened = clock - (clock % fastest)
    return repr(opened)


def _card(launcher: object) -> dict[str, object]:
    facts = launcher_facts()
    payload: dict[str, object] = {"launcher_facts": dict(facts)}
    payload.update(facts)
    namespace = _flag("--namespace")
    if namespace:
        payload["namespace"] = namespace
    profile = _flag("--profile")
    if profile:
        payload["profile"] = profile
    codes = _watched_codes(launcher)
    if codes:
        payload["watched_timeframes"] = list(codes)
    fastest = _fastest_period(launcher)
    if fastest is not None:
        payload["fastest_bar_seconds"] = fastest
    until = seconds_until_fastest_print(launcher)
    if until is not None:
        payload["seconds_until_next_print"] = until
    current = _stable_key(launcher)
    for key, value in list(_RETURNED.items()):
        if _RETURNED_KEY.get(key) == current:
            payload["returned_" + key] = value
    _stamp_clock(payload, launcher)
    return payload


def _post(state: dict[str, object], questions: dict[str, object]) -> object:
    from src.judgment.jev_client import evaluate

    return evaluate(
        state,
        questions=dict(questions),
        merge_sleeve=False,
        include_depth="full",
    )


def _accept(qid: str, number: float) -> None:
    if number < 0:
        return
    if qid in _CLOCKS:
        if clock_from_minutes(number) is None:
            return
        stored = float(number)
    elif qid in _HOURS:
        whole = int(number)
        if whole != number or whole > 23:
            return
        stored = float(whole)
    else:
        stored = float(number)
    _RETURNED[qid] = stored
    _RETURNED_KEY[qid] = _ASK_KEY


def _ask_once(launcher: object) -> bool:
    global _ASK_KEY
    _ASK_KEY = _stable_key(launcher)
    card = _card(launcher)
    try:
        from src.judgment.nineteen import score
    except Exception:
        return False
    accepted = False
    for qid, text in _QUESTIONS:
        # cycle_wait is scored per print in ``_cycle_wait_for_print``. The pack
        # key does not change between prints, so a score left here would be
        # reused for a later print.
        if qid == "cycle_wait":
            continue
        anchors = _anchors_for_unit(_UNIT.get(qid, ""), card)
        try:
            number = score(
                card,
                question_id=qid,
                instructions=_with_position(text),
                anchors=anchors,
            )
        except TypeError:
            number = None
        except Exception:
            number = None
        if number is None:
            continue
        _accept(qid, number)
        accepted = True
    return accepted


def ensure_ask(launcher: object = None) -> None:
    """Post the pack once per launcher state. The post does not hold the caller."""

    global _INFLIGHT, _ATTEMPT
    watched = launcher if launcher is not None else _WATCHED
    key = _stable_key(watched)
    with _LOCK:
        if _PACK_KEY == key or _INFLIGHT:
            return
        bar = _bar_token(watched)
        if _ATTEMPT == (key, bar):
            return
        _INFLIGHT = True
        _ATTEMPT = (key, bar)

    def run() -> None:
        global _INFLIGHT, _PACK_KEY
        posted = False
        try:
            posted = _ask_once(watched)
        except Exception:
            posted = False
        with _LOCK:
            if posted:
                _PACK_KEY = key
            _INFLIGHT = False

    threading.Thread(target=run, name="launcher-scores", daemon=True).start()


def launcher_return(name: str) -> float | None:
    """The score accepted for the launcher state now watched. A previous state does not count."""

    qid = str(name)
    if _RETURNED_KEY.get(qid) != _stable_key(_WATCHED):
        return None
    number = _RETURNED.get(qid)
    if number is None:
        return None
    return float(number)


def next_cycle_wait(launcher: object = None) -> float | None:
    """Seconds before the next cycle.

    A returned ``cycle_wait`` for the print ahead is the lead before that
    print. Until one returns, the wait is the seconds until that print. An
    empty answer, a tie, or an error does not restore a poll flag or any
    other number.
    """

    seconds, _when = next_cycle_wake(launcher)
    return seconds
