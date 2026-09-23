"""FrozenPriceIntent V1 — quote-dependent cost skips keep a frozen price live.

Default-off. The owner arms this only for an F5 minimal-size worker with
``--frozen-intent-reprice``. Classification is by refusal *family* plus the
pretrade packet's immutable floor, not by a loose reason-prefix allowlist.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping, Optional

from src.components.broker_net_cost_engine import pretrade_cost_refusal_reasons


SCHEMA = "gtos.ultimate_book.frozen_price_intent.v1"

PACKET_CLASS_QUOTE_DEPENDENT = "QUOTE_DEPENDENT"
PACKET_CLASS_STRUCTURAL = "STRUCTURAL"
PACKET_CLASS_MODEL_INPUT = "MODEL_INPUT_INVALID"
PACKET_CLASS_NONE = "NONE"

STATE_REFUSED_COST = "REFUSED_COST"
STATE_OBSERVING = "OBSERVING"
STATE_FILLED = "FILLED"
STATE_PRICE_INVALIDATED = "PRICE_INVALIDATED"
STATE_EXPIRED = "EXPIRED"
STATE_AUTHORITY_INVALIDATED = "AUTHORITY_INVALIDATED"
STATE_POSITION_CONFLICT = "POSITION_CONFLICT"
STATE_COST_NEVER_VALID = "COST_NEVER_VALID"

OPEN_STATES = frozenset({STATE_REFUSED_COST, STATE_OBSERVING})
TERMINAL_STATES = frozenset({
    STATE_FILLED,
    STATE_PRICE_INVALIDATED,
    STATE_EXPIRED,
    STATE_AUTHORITY_INVALIDATED,
    STATE_POSITION_CONFLICT,
    STATE_COST_NEVER_VALID,
})

# Exact family tokens (the substring before the first ':'). A reason whose
# family is not in either set is STRUCTURAL — fail closed, not "looks like
# spread so retry".
_QUOTE_DEPENDENT_FAMILIES = frozenset({
    "cost_screen_spread_r",
    "spread_r_exceeds_selected_cell_limit",
    "missing_current_quote_spread_or_sl_distance",
})
_MODEL_INPUT_FAMILIES = frozenset({
    "model_input_invalid_stop",
})
_STRUCTURAL_FAMILIES = frozenset({
    "missing_or_unapproved_selected_cell_commission_model_status",
    "missing_broker_true_commission_cost_r_conversion",
    "missing_broker_account_profile_namespace",
    "missing_broker_symbol_spec_fields",
    "missing_side_aware_swap_schedule",
    "missing_side_aware_swap_cost_r_conversion",
    "missing_expected_slippage_r",
    "missing_broker_trade_mode_or_hours_state",
    "broker_trade_mode_not_deal_enabled",
    "missing_explicit_broker_trading_session_table",
})
_TOTAL_COST_FAMILY = "total_cost_r_exceeds_limit"

_SCORE_LOCK = threading.Lock()
_SCORE_CACHE: dict[str, float | None] = {}
_SCORE_WAIT: dict[str, threading.Event] = {}
_FAMILY_CACHE: dict[str, str | None] = {}

_CHASE_TEXT = (
    "The score you return is the chase fraction of the stop that ends this frozen intent. "
    "An empty score leaves the chase unset. Do not send."
)
_EXPIRY_TEXT = (
    "The score you return is the expiry in seconds for this frozen intent. "
    "An empty score leaves the expiry unset. Do not send."
)
_TOLERANCE_TEXT = (
    "The score you return is the cost tolerance in R above max_total_cost_r for this packet. "
    "An empty score leaves the tolerance unset. Do not send."
)
_STOP_TEXT = (
    "The score you return is the minimum protective distance in pips. "
    "An empty score leaves the distance unset. Do not send."
)


def _push_level(levels: list, seen: list, label: str, number: float | None) -> None:
    text = str(label or "").strip()
    if number is None or not text or number in seen:
        return
    if number != number or number in (float("inf"), float("-inf")):
        return
    seen.append(number)
    levels.append((text, number))


def _pip_anchors(stop_dist: Any, point: Any, digits: Any, symbol: Any) -> list:
    """Pip distances from the stop and the point already on this card."""
    pip = fx_pip_size(digits=digits, point=point, symbol=symbol)
    if pip is None or pip <= 0:
        return []
    levels: list = []
    seen: list = []
    distance = _as_float(stop_dist)
    if distance is not None and distance > 0:
        _push_level(levels, seen, "this stop, in pips", distance / pip)
    point_n = _as_float(point)
    if point_n is not None and point_n > 0:
        _push_level(levels, seen, "one point of this symbol, in pips", point_n / pip)
    return levels


def _tolerance_anchors(facts: Mapping[str, Any] | None) -> list:
    """Cost tolerance in R. Both costs are already on the card."""
    if not isinstance(facts, Mapping):
        return []
    levels: list = []
    seen: list = []
    _push_level(levels, seen, "the packet's max total cost, in R", _as_float(facts.get("max_total_cost_r")))
    _push_level(levels, seen, "the packet's immutable cost, in R", _as_float(facts.get("immutable_cost_r")))
    return levels


def _day_start_utc(decision_day: Any) -> datetime | None:
    text = str(decision_day or "").strip()
    if len(text) < 10:
        return None
    head = text[:10]
    try:
        year = int(head[0:4])
        month = int(head[5:7])
        day = int(head[8:10])
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _clock_seconds(card: Mapping[str, Any], now: datetime, quote_at: datetime | None) -> dict[str, float]:
    """Seconds fixed by this bar and this clock. Missing stays off the card."""
    close = parse_decision_close_utc(card.get("decision_bar_iso"), fallback=now)
    queued = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
    found: dict[str, float] = {"since_bar_close_s": (queued - close).total_seconds()}
    start = _day_start_utc(card.get("decision_day"))
    if start is not None:
        found["bar_close_into_day_s"] = (close - start).total_seconds()
    if quote_at is not None:
        stamp = quote_at if quote_at.tzinfo is not None else quote_at.replace(tzinfo=timezone.utc)
        found["since_quote_s"] = (queued - stamp).total_seconds()
    return found


def _second_anchors(seconds: Mapping[str, float]) -> list:
    labels = {
        "since_bar_close_s": "seconds since this bar closed",
        "bar_close_into_day_s": "seconds from this day's start to the bar close",
        "since_quote_s": "seconds since this quote",
    }
    levels: list = []
    seen: list = []
    for key, label in labels.items():
        _push_level(levels, seen, label, _as_float(seconds.get(key)))
    return levels


def _chase_anchors(card: Mapping[str, Any]) -> list:
    """Chase is a fraction of the stop. A time ratio is not that fraction."""
    levels: list = []
    seen: list = []
    source = card if isinstance(card, Mapping) else {}
    for key, label in (
        ("spread_r", "this quote's spread over the stop"),
        ("chase", "the chase fraction on this tick"),
        ("chase_at_first_clear", "the chase fraction when the spread first cleared"),
        ("min_spread_over_stop", "the series minimum spread over the stop"),
        ("max_spread_over_stop", "the series maximum spread over the stop"),
    ):
        _push_level(levels, seen, label, _as_float(source.get(key)))
    return levels


def _spine_score(role: str, instructions: str, facts: dict | None = None, anchors=None):
    """One score for this fact card. A repeated card reuses that return.

    Anchors are this hop's unit. Fewer than two does not post.
    Empty, tie, and error stay None. They are stored for the card so the
    next hop does not ask the same card again and does not fill in a number.
    """

    key = str(role) + "|" + json.dumps(
        {"facts": facts or {}, "anchors": anchors},
        sort_keys=True,
        default=str,
    )
    with _SCORE_LOCK:
        if key in _SCORE_CACHE:
            return _SCORE_CACHE[key]
        event = _SCORE_WAIT.get(key)
        if event is None:
            event = threading.Event()
            _SCORE_WAIT[key] = event
            owner = True
        else:
            owner = False
    if not owner:
        event.wait()
        with _SCORE_LOCK:
            return _SCORE_CACHE.get(key)
    value: float | None = None
    try:
        from src.judgment.nineteen import score

        raw = score(
            dict(facts or {}),
            question_id=role,
            instructions=instructions,
            anchors=anchors,
        )
        if raw is not None:
            number = float(raw)
            if number == number and number not in (float("inf"), float("-inf")):
                value = number
    except Exception:
        value = None
    finally:
        with _SCORE_LOCK:
            _SCORE_CACHE[key] = value
            _SCORE_WAIT.pop(key, None)
        event.set()
    return value


def _parallel(jobs: dict[str, Callable[[], Any]]) -> dict[str, Any]:
    """Run independent asks together. One ask runs on this thread."""

    if not jobs:
        return {}
    if len(jobs) == 1:
        key, fn = next(iter(jobs.items()))
        try:
            return {key: fn()}
        except Exception:
            return {key: None}
    out: dict[str, Any] = {}

    def _run(key: str, fn: Callable[[], Any]) -> None:
        try:
            out[key] = fn()
        except Exception:
            out[key] = None

    threads = [threading.Thread(target=_run, args=(key, fn)) for key, fn in jobs.items()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return out

_IMMUTABLE_COMPONENT_KEYS = (
    "commission_r",
    "swap_cost_r",
    "expected_slippage_r",
)


def refusal_family(reason: Any) -> str:
    """Return the exact family token of one refusal reason (before the first ':')."""
    text = str(reason or "").strip()
    if not text:
        return ""
    return text.split(":", 1)[0]


def refusal_families(reasons: Iterable[Any] | None) -> list[str]:
    return [refusal_family(reason) for reason in (reasons or ()) if str(reason or "").strip()]


def _as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def quote_time_utc(tick: Any, *, fallback: datetime) -> datetime:
    """Best-effort quote time from a tick; fall back to the caller clock."""
    raw = getattr(tick, "time", None) if tick is not None else None
    if raw is None and isinstance(tick, Mapping):
        raw = tick.get("quote_at_utc") or tick.get("time")
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=timezone.utc)
        return raw.astimezone(timezone.utc)
    text = str(raw or "").strip()
    if text:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    fb = fallback if fallback.tzinfo is not None else fallback.replace(tzinfo=timezone.utc)
    return fb.astimezone(timezone.utc)


def side_from_direction(direction: Any) -> Optional[str]:
    try:
        value = int(direction)
    except (TypeError, ValueError):
        return None
    if value > 0:
        return "LONG"
    if value < 0:
        return "SHORT"
    return None


def unrounded_lots(*sources: Any) -> Optional[float]:
    """First present unrounded size/lots on a packet, unit, or scalar."""
    keys = (
        "unrounded",
        "unrounded_lots",
        "raw_lots",
        "f5_lots_requested",
        "lots_requested",
        "frozen_max_lots",
    )
    for source in sources:
        if source is None:
            continue
        if isinstance(source, Mapping):
            for key in keys:
                value = _as_float(source.get(key))
                if value is not None:
                    return value
            continue
        value = _as_float(source)
        if value is not None:
            return value
    return None


def quote_snapshot_from_tick(
    tick: Any,
    *,
    stop_dist: Any = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Executable quote fields for as_row / durable F5 persist. Missing stays None."""
    if isinstance(tick, Mapping):
        bid = _as_float(tick.get("bid"))
        ask = _as_float(tick.get("ask"))
        given_spread = _as_float(tick.get("spread_price") if tick.get("spread_price") is not None else tick.get("spread"))
    else:
        bid = _as_float(getattr(tick, "bid", None) if tick is not None else None)
        ask = _as_float(getattr(tick, "ask", None) if tick is not None else None)
        given_spread = None
    spread_price = given_spread
    if spread_price is None and bid is not None and ask is not None:
        spread_price = ask - bid
    distance = _as_float(stop_dist)
    spread_r = None
    if spread_price is not None and distance is not None and distance > 0:
        spread_r = spread_price / distance
    fallback = now if now is not None else datetime.now(timezone.utc)
    return {
        "bid": bid,
        "ask": ask,
        "spread": spread_price,
        "spread_price": spread_price,
        "spread_r": spread_r,
        "quote_at_utc": quote_time_utc(tick, fallback=fallback),
    }


def _quote_as_utc(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def quote_series_rollup(
    quotes: Iterable[Any],
    *,
    need_spr: Any,
    stop_dist: Any,
    direction: Any,
    frozen_entry: Any,
    tuition_usd: float | None = None,
) -> dict[str, Any]:
    """Rollup a quote series so harvest can tell poll from tax.

    usd = tuition * spr / stop_dist. cap_inside_oscillation is true when
    need_spr sits inside [min_spr, max_spr]. first_clear is the first
    spr <= need_spr; otherwise first_clear_lag_s is ``never``.
    """
    need = _as_float(need_spr)
    distance = _as_float(stop_dist)
    entry = _as_float(frozen_entry)
    try:
        side = int(direction)
    except (TypeError, ValueError):
        side = 0
    snapshots: list[dict[str, Any]] = []
    sprs: list[float] = []
    usds: list[float] = []
    first_utc: Optional[datetime] = None
    first_clear_utc: Optional[datetime] = None
    first_clear_lag_s: Any = "never"
    chase_at_first_clear: Optional[float] = None
    for raw in quotes or ():
        snap = quote_snapshot_from_tick(raw, stop_dist=distance, now=first_utc)
        spr = _as_float(snap.get("spread_price"))
        if spr is None:
            continue
        snapshots.append(snap)
        sprs.append(spr)
        tuition = _as_float(tuition_usd)
        if distance is not None and distance > 0 and tuition is not None:
            usds.append(tuition * spr / distance)
        quote_at = snap.get("quote_at_utc")
        if isinstance(quote_at, datetime):
            if first_utc is None:
                first_utc = quote_at
            if (
                first_clear_utc is None
                and need is not None
                and spr <= need
            ):
                first_clear_utc = quote_at
                first_clear_lag_s = (quote_at - first_utc).total_seconds() if first_utc is not None else 0.0
                tick = raw
                if not hasattr(tick, "bid") or not hasattr(tick, "ask"):
                    tick = type("_Tick", (), {"bid": snap.get("bid"), "ask": snap.get("ask")})()
                if entry is not None and distance is not None:
                    chase_at_first_clear = chase_stop_fraction(
                        direction=side,
                        tick=tick,
                        frozen_entry=entry,
                        stop_dist=distance,
                    )
    min_spr = min(sprs) if sprs else None
    max_spr = max(sprs) if sprs else None
    unique_n = len({round(value, 10) for value in sprs})
    cap_inside = (
        min_spr is not None
        and max_spr is not None
        and need is not None
        and min_spr <= need <= max_spr
    )
    return {
        "min_spr": min_spr,
        "max_spr": max_spr,
        "unique_n": unique_n,
        "min_usd": min(usds) if usds else None,
        "max_usd": max(usds) if usds else None,
        "cap_inside_oscillation": bool(cap_inside),
        "first_clear_utc": first_clear_utc,
        "first_clear_lag_s": first_clear_lag_s,
        "chase_at_first_clear": chase_at_first_clear,
        "series_n": len(snapshots),
        "quotes": snapshots,
    }


# Sleeve import name. Not read as a distance. The minimum is the score.
MARKET_STOP_MIN_PIPS = 0

_METAL_PREFIXES = ("XAU", "XAG", "XPT", "XPD")
_SYMBOL_SUFFIXES = (".A", ".PRO", ".M", ".I")


def _canon_symbol(symbol: Any) -> str:
    name = str(symbol or "").strip().upper()
    for suffix in _SYMBOL_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def looks_like_fx(symbol: Any) -> bool:
    name = _canon_symbol(symbol)
    if len(name) != 6 or not name.isalpha():
        return False
    return not name.startswith(_METAL_PREFIXES)


def fx_pip_size(
    *,
    digits: Any = None,
    point: Any = None,
    symbol: Any = "",
) -> Optional[float]:
    """Conventional pip on 3/5-digit FX. None means this class does not apply."""
    point_n = _as_float(point)
    try:
        digits_n = int(digits) if digits not in (None, "") else None
    except (TypeError, ValueError):
        digits_n = None
    if point_n is not None and point_n > 0 and digits_n in (3, 5):
        return 10.0 * point_n
    if point_n is not None and point_n > 0 and digits_n in (2, 4) and looks_like_fx(symbol):
        return point_n
    return None



def quoted_book_pips(
    *,
    bid,
    ask,
    digits=None,
    point=None,
    symbol="",
) -> Optional[float]:
    """Pip width of the quoted book. The spread, not the stop.

    On 3/5-digit FX a pip is ten points, so one point of EURUSD is 0.1 pip.
    A missing pip size returns None. It does not substitute 0.0001, and it
    does not divide the stop into a 1.30 pip label.
    """
    pip = fx_pip_size(digits=digits, point=point, symbol=symbol)
    if pip is None or pip <= 0:
        return None
    try:
        spread = float(ask) - float(bid)
    except (TypeError, ValueError):
        return None
    if spread < 0:
        return None
    return spread / pip


def broker_stop_minimum(
    *,
    stops_level: Any = None,
    point: Any = None,
    tick_size: Any = None,
    spread: Any = None,
) -> float | None:
    """Fill-to-stop distance required by this symbol's broker facts.

    A market fill is the far side of the quote. The stop is checked from the
    near side, so the live spread is part of the distance. ``trade_stops_level``
    times ``point`` is the indentation. ``trade_tick_size`` raises that
    indentation when the tick is wider. A present zero level is that fact.
    A missing level, point, or spread leaves the minimum unset.
    """
    level = _as_float(stops_level)
    point_n = _as_float(point)
    spread_n = _as_float(spread)
    if (
        level is None
        or point_n is None
        or spread_n is None
        or level < 0
        or point_n <= 0
        or spread_n < 0
    ):
        return None
    indent = level * point_n
    tick = _as_float(tick_size)
    if tick is not None and tick > indent:
        indent = tick
    return indent + spread_n


def is_market_stop(
    stop_dist: Any,
    *,
    digits: Any = None,
    point: Any = None,
    symbol: Any = "",
    stops_level: Any = None,
    tick_size: Any = None,
    spread: Any = None,
) -> bool | None:
    """Whether this stop reaches the broker minimum.

    True means the distance is at least ``trade_stops_level * point``, raised
    to the tick when the tick is wider, plus the live spread. False means the
    distance is inside that minimum. None means those facts are not all
    present. A pip count is not a minimum. A missing distance does not invent
    one.
    """
    del digits, symbol
    distance = _as_float(stop_dist)
    if distance is None or distance <= 0:
        return None
    minimum = broker_stop_minimum(
        stops_level=stops_level,
        point=point,
        tick_size=tick_size,
        spread=spread,
    )
    if minimum is None:
        return None
    return distance >= minimum


def immutable_cost_r(packet: Mapping[str, Any] | None) -> Optional[float]:
    """Sum of cost components that a tighter quote cannot repair.

    Spread is excluded. Missing components are omitted rather than coerced to
    zero: a hole in the packet is not evidence the floor is clear.
    """
    if not isinstance(packet, Mapping):
        return None
    components = packet.get("total_cost_components")
    source = components if isinstance(components, Mapping) else packet
    parts: list[float] = []
    for key in _IMMUTABLE_COMPONENT_KEYS:
        value = _as_float(source.get(key))
        if value is None and key == "swap_cost_r":
            swap = packet.get("swap_cost") if isinstance(packet.get("swap_cost"), Mapping) else {}
            value = _as_float(swap.get("cost_r"))
        if value is None and key == "commission_r":
            commission = (
                packet.get("commission_cost")
                if isinstance(packet.get("commission_cost"), Mapping)
                else {}
            )
            value = _as_float(packet.get("commission_r"))
            if value is None:
                value = _as_float(commission.get("cost_r"))
        if value is not None:
            parts.append(value)
    if not parts:
        return None
    return float(sum(parts))


def _tolerance_facts(packet: Mapping[str, Any], max_total: float, immutable: float) -> dict[str, Any]:
    return {
        "max_total_cost_r": max_total,
        "immutable_cost_r": immutable,
        "symbol": packet.get("symbol"),
        "sleeve": packet.get("sleeve"),
    }


def immutable_floor_clear(
    packet: Mapping[str, Any] | None,
    *,
    tolerance: float | None = None,
    tolerance_asked: bool = False,
) -> bool:
    """True when non-spread costs do not prove a breach of the returned tolerance.

    A missing packet or missing immutable components cannot prove a breach.
    A tolerance already on the packet is that fact. A missing tolerance is
    one score. An empty score does not become zero and does not prove a breach.
    """
    if not isinstance(packet, Mapping):
        return True
    max_total = _as_float(packet.get("max_total_cost_r"))
    immutable = immutable_cost_r(packet)
    if max_total is None or immutable is None:
        return True
    if not tolerance_asked:
        given = _as_float(packet.get("cost_limit_tolerance_r"))
        if given is not None:
            tolerance = given
        else:
            tolerance_card = _tolerance_facts(packet, max_total, immutable)
            tolerance = _spine_score(
                "cost_limit_tolerance_r",
                _TOLERANCE_TEXT,
                tolerance_card,
                _tolerance_anchors(tolerance_card),
            )
    if tolerance is None:
        return True
    return immutable - max_total <= tolerance


def reasons_from_packet(packet: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(packet, Mapping):
        return []
    existing = packet.get("refusal_reasons")
    if isinstance(existing, list) and existing:
        return [str(reason) for reason in existing if str(reason or "").strip()]
    return list(pretrade_cost_refusal_reasons(dict(packet)))


def _family_choice(families: list[str], symbol: Any, stop_dist: Any) -> str | None:
    """Ask the class of refusal families the sets do not name.

    None is unanswered. It does not become a structural kill.
    """

    key = "cost_family|" + "|".join(sorted(families)) + "|" + str(symbol or "")
    with _SCORE_LOCK:
        if key in _FAMILY_CACHE:
            return _FAMILY_CACHE[key]
    alternative: str | None = None
    try:
        from src.judgment.no_fear import fear_withholds

        asked = fear_withholds(
            "cost_family",
            {
                "symbol": str(symbol or ""),
                "families": list(families),
                "stop_dist": stop_dist,
            },
            {
                "quote_dependent": "A tighter quote can still repair this reason.",
                "structural": "A tighter quote cannot repair this reason.",
                "model_input": "This reason says the stop is not a market.",
            },
            "structural",
            key,
            "These refusal families are on the state. "
            "quote_dependent keeps the frozen price. "
            "structural means a tighter quote cannot repair it. "
            "model_input means the stop is not a market. "
            "An empty answer or a tie does not restore a structural kill. "
            "Do not close an open ticket. Do not send.",
        )
        if isinstance(asked, dict):
            alt = asked.get("alternative")
            if (
                not asked.get("unanswered")
                and not asked.get("error")
                and alt in {"quote_dependent", "structural", "model_input"}
            ):
                alternative = str(alt)
    except Exception:
        alternative = None
    with _SCORE_LOCK:
        _FAMILY_CACHE.setdefault(key, alternative)
        return _FAMILY_CACHE[key]


def _tolerance_missing(packet: Mapping[str, Any] | None, families: list[str]) -> bool:
    if _TOTAL_COST_FAMILY not in families or not isinstance(packet, Mapping):
        return False
    if _as_float(packet.get("cost_limit_tolerance_r")) is not None:
        return False
    max_total = _as_float(packet.get("max_total_cost_r"))
    immutable = immutable_cost_r(packet)
    return max_total is not None and immutable is not None


def classify_cost_refusal(
    reasons: Iterable[Any] | None = None,
    packet: Mapping[str, Any] | None = None,
    *,
    screen_reason: Any = None,
    stop_dist: Any = None,
    digits: Any = None,
    point: Any = None,
    symbol: Any = "",
    stops_level: Any = None,
    tick_size: Any = None,
    spread: Any = None,
) -> str | None:
    """Return a packet class, or None when the ask that would name it is empty.

    ``screen_reason`` is the owner pre-send string from ``_spread_cost_screen``.
    A packet, when present, is the authority for mixed / total-cost cases.
    A stop inside the broker minimum is model input. Missing broker facts do
    not make that class. An unnamed family is asked. An empty family answer
    leaves the class unset. It does not kill and it does not send.
    """
    collected: list[str] = []
    if screen_reason not in (None, ""):
        collected.append(str(screen_reason))
    if reasons is not None:
        collected.extend(str(reason) for reason in reasons if str(reason or "").strip())
    if packet is not None:
        for reason in reasons_from_packet(packet):
            if reason not in collected:
                collected.append(reason)
    if not collected:
        return PACKET_CLASS_NONE

    families = refusal_families(collected)
    if any(family in _STRUCTURAL_FAMILIES for family in families):
        return PACKET_CLASS_STRUCTURAL
    if any(family in _MODEL_INPUT_FAMILIES for family in families):
        return PACKET_CLASS_MODEL_INPUT
    unknown = [
        family for family in families
        if family not in _QUOTE_DEPENDENT_FAMILIES
        and family not in _MODEL_INPUT_FAMILIES
        and family != _TOTAL_COST_FAMILY
    ]
    unknown_set = set(unknown)
    jobs: dict[str, Callable[[], Any]] = {
        "market": lambda: is_market_stop(
            stop_dist,
            digits=digits,
            point=point,
            symbol=symbol,
            stops_level=stops_level,
            tick_size=tick_size,
            spread=spread,
        ),
    }
    if unknown:
        named = list(unknown)
        jobs["family"] = lambda: _family_choice(named, symbol, stop_dist)
    if isinstance(packet, Mapping) and _tolerance_missing(packet, families):
        max_total = _as_float(packet.get("max_total_cost_r"))
        immutable = immutable_cost_r(packet)
        if max_total is not None and immutable is not None:
            facts = _tolerance_facts(packet, max_total, immutable)
            tol_anchors = _tolerance_anchors(facts)
            jobs["tol"] = lambda: _spine_score(
                "cost_limit_tolerance_r",
                _TOLERANCE_TEXT,
                facts,
                tol_anchors,
            )
    got = _parallel(jobs)
    market = got.get("market")
    if market is False:
        return PACKET_CLASS_MODEL_INPUT
    if unknown:
        alt = got.get("family")
        if alt == "structural":
            return PACKET_CLASS_STRUCTURAL
        if alt == "model_input":
            return PACKET_CLASS_MODEL_INPUT
        if alt != "quote_dependent":
            return None
        families = [
            family if family not in unknown_set else "cost_screen_spread_r"
            for family in families
        ]
    if _TOTAL_COST_FAMILY in families:
        if "tol" in got:
            clear = immutable_floor_clear(
                packet,
                tolerance=_as_float(got.get("tol")),
                tolerance_asked=True,
            )
        else:
            clear = immutable_floor_clear(packet)
        if not clear:
            return PACKET_CLASS_STRUCTURAL
    return PACKET_CLASS_QUOTE_DEPENDENT


def packet_from_place_result(result: Mapping[str, Any] | None) -> Optional[dict[str, Any]]:
    if not isinstance(result, Mapping):
        return None
    trade_params = result.get("trade_params")
    if not isinstance(trade_params, Mapping):
        return None
    packet = trade_params.get("gtos_vnext_pretrade_cost_model")
    return dict(packet) if isinstance(packet, Mapping) else None


def parse_decision_close_utc(value: Any, *, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def frozen_intent_key(sleeve: Any, symbol: Any, decision_bar_iso: Any) -> tuple[str, str, str]:
    return (str(sleeve or ""), str(symbol or ""), str(decision_bar_iso or ""))


def geometry_from_intent_tick(intent: Any, tick: Any) -> Optional[dict[str, float]]:
    """Freeze absolute entry / stop / target from the *current* quote. No wait."""
    try:
        direction = int(getattr(intent, "direction"))
        stop_dist = float(getattr(intent, "stop_dist") or 0.0)
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    if direction == 0 or stop_dist <= 0 or bid <= 0 or ask <= 0 or ask < bid:
        return None
    sign = 1.0 if direction > 0 else -1.0
    entry = float(ask if direction > 0 else bid)
    stop = entry - sign * stop_dist
    raw_target = getattr(intent, "target_dist", None)
    try:
        target_dist = float(raw_target) if raw_target not in (None, "") else None
    except (TypeError, ValueError):
        target_dist = None
    target = (entry + sign * target_dist) if target_dist is not None and target_dist > 0 else None
    geometry = {
        "entry_price": entry,
        "stop_loss": stop,
        "risk_distance": stop_dist,
        "stop_dist": stop_dist,
    }
    if target is not None and target_dist is not None:
        geometry["take_profit_1"] = target
        geometry["target_dist"] = target_dist
    return geometry


def is_blow_through(*, direction: int, tick: Any, stop_loss: float) -> bool:
    """Protective side already at or through the frozen stop."""
    try:
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        stop = float(stop_loss)
    except (TypeError, ValueError):
        return False
    if bid <= 0 or ask <= 0 or ask < bid:
        return False
    if int(direction) > 0:
        return bid <= stop
    if int(direction) < 0:
        return ask >= stop
    return False


def chase_stop_fraction(*, direction: int, tick: Any, frozen_entry: float, stop_dist: float) -> Optional[float]:
    """Adverse executable-side move from the frozen entry, in units of stop distance.

    Negative / zero means the quote is at or better than the frozen entry.
    """
    try:
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        entry = float(frozen_entry)
        distance = float(stop_dist)
        side = int(direction)
    except (TypeError, ValueError):
        return None
    if side > 0:
        sign = 1.0
    elif side < 0:
        sign = -1.0
    else:
        return None
    if distance <= 0 or bid <= 0 or ask <= 0 or ask < bid:
        return None
    current = ask if int(direction) > 0 else bid
    return (current - entry) * sign / distance


def decision_close_to_send_ms(decision_close_utc: datetime, send_at: datetime) -> float:
    close = decision_close_utc
    if close.tzinfo is None:
        close = close.replace(tzinfo=timezone.utc)
    sent = send_at
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=timezone.utc)
    return (sent - close).total_seconds() * 1000.0


@dataclass
class FrozenPriceIntent:
    """In-process price-level object. PlacementLedger remains the durable authority."""

    sleeve: str
    symbol: str
    direction: int
    decision_bar_iso: str
    decision_day: str
    decision_close_utc: datetime
    queued_at_utc: datetime
    expires_at_utc: datetime | None
    frozen_entry: float
    frozen_stop: float
    frozen_stop_dist: float
    frozen_target: float | None
    frozen_target_dist: float | None
    frozen_max_lots: float | None
    unit: dict[str, Any]
    refusal_reasons: list[str]
    packet_class: str = PACKET_CLASS_QUOTE_DEPENDENT
    state: str = STATE_REFUSED_COST
    last_reason: str = ""
    candidate_id: str | None = None
    max_chase_stop_fraction: float | None = None
    hard_expiry_seconds: float | None = None
    decision_close_to_send_ms: float | None = None
    quote_bid: float | None = None
    quote_ask: float | None = None
    quote_spread_price: float | None = None
    quote_spread_r: float | None = None
    quote_at_utc: datetime | None = None
    unrounded: float | None = None
    annotations: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return frozen_intent_key(self.sleeve, self.symbol, self.decision_bar_iso)

    @property
    def is_open(self) -> bool:
        return self.state in OPEN_STATES

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def geometry(self) -> dict[str, float]:
        geom = {
            "entry_price": float(self.frozen_entry),
            "stop_loss": float(self.frozen_stop),
            "risk_distance": float(self.frozen_stop_dist),
            "stop_dist": float(self.frozen_stop_dist),
        }
        if self.frozen_target is not None:
            geom["take_profit_1"] = float(self.frozen_target)
        if self.frozen_target_dist is not None:
            geom["target_dist"] = float(self.frozen_target_dist)
        return geom

    def expired_at(self, now: datetime) -> bool:
        if self.expires_at_utc is None:
            return False
        now_utc = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        return now_utc >= self.expires_at_utc

    def terminate(self, state: str, reason: str) -> None:
        self.state = state
        self.last_reason = str(reason)

    def as_row(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "sleeve": self.sleeve,
            "symbol": self.symbol,
            "direction": self.direction,
            "decision_bar_iso": self.decision_bar_iso,
            "decision_day": self.decision_day,
            "state": self.state,
            "packet_class": self.packet_class,
            "last_reason": self.last_reason,
            "frozen_entry": self.frozen_entry,
            "frozen_stop": self.frozen_stop,
            "frozen_target": self.frozen_target,
            "frozen_stop_dist": self.frozen_stop_dist,
            "frozen_max_lots": self.frozen_max_lots,
            "candidate_id": self.candidate_id,
            "decision_close_to_send_ms": self.decision_close_to_send_ms,
            "queued_at_utc": self.queued_at_utc.isoformat(),
            "expires_at_utc": (
                self.expires_at_utc.isoformat() if self.expires_at_utc is not None else None
            ),
            "bid": self.quote_bid,
            "ask": self.quote_ask,
            "spread": self.quote_spread_price,
            "spread_price": self.quote_spread_price,
            "spread_r": self.quote_spread_r,
            "stop": self.frozen_stop,
            "unrounded": self.unrounded,
            "quote_at_utc": self.quote_at_utc.isoformat() if self.quote_at_utc is not None else None,
            "side": side_from_direction(self.direction),
            "refusal_reasons": list(self.refusal_reasons),
        }


def build_frozen_price_intent(
    *,
    intent: Any,
    unit: Mapping[str, Any],
    tick: Any,
    decision_bar_iso: str,
    decision_day: str,
    now: datetime,
    reasons: Iterable[Any],
    candidate_id: str | None = None,
    frozen_max_lots: float | None = None,
    max_chase_stop_fraction: float | None = None,
    hard_expiry_seconds: float | None = None,
) -> FrozenPriceIntent | None:
    geometry = geometry_from_intent_tick(intent, tick)
    if geometry is None:
        return None
    queued = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
    quote = quote_snapshot_from_tick(
        tick,
        stop_dist=geometry.get("stop_dist") or geometry.get("risk_distance"),
        now=queued,
    )
    close = parse_decision_close_utc(decision_bar_iso, fallback=queued)
    sleeve = str(getattr(intent, "sleeve", "") or "")
    symbol = str(getattr(intent, "symbol", "") or "")
    card = {
        "symbol": symbol,
        "sleeve": sleeve,
        "decision_bar_iso": str(decision_bar_iso),
        "decision_day": str(decision_day),
    }
    card.update(_clock_seconds(card, queued, quote.get("quote_at_utc")))
    spread_r = _as_float(quote.get("spread_r"))
    if spread_r is not None:
        card["spread_r"] = spread_r
    chase_levels = _chase_anchors(card)
    expiry_levels = _second_anchors(card)
    jobs: dict[str, Callable[[], Any]] = {}
    if max_chase_stop_fraction is None:
        jobs["chase"] = lambda: _spine_score(
            "max_chase_stop_fraction", _CHASE_TEXT, card, chase_levels,
        )
    if hard_expiry_seconds is None:
        jobs["expiry"] = lambda: _spine_score(
            "hard_expiry_seconds", _EXPIRY_TEXT, card, expiry_levels,
        )
    got = _parallel(jobs)
    if "chase" in got:
        max_chase_stop_fraction = got.get("chase")
        if _as_float(max_chase_stop_fraction) is None:
            return None
    if "expiry" in got:
        hard_expiry_seconds = got.get("expiry")
        if _as_float(hard_expiry_seconds) is None:
            return None
    chase_limit = _as_float(max_chase_stop_fraction)
    expiry_s = _as_float(hard_expiry_seconds)
    return FrozenPriceIntent(
        sleeve=str(getattr(intent, "sleeve", "") or ""),
        symbol=str(getattr(intent, "symbol", "") or ""),
        direction=int(getattr(intent, "direction")),
        decision_bar_iso=str(decision_bar_iso),
        decision_day=str(decision_day),
        decision_close_utc=close,
        queued_at_utc=queued,
        expires_at_utc=None if expiry_s is None else queued + timedelta(seconds=expiry_s),
        frozen_entry=float(geometry["entry_price"]),
        frozen_stop=float(geometry["stop_loss"]),
        frozen_stop_dist=float(geometry["risk_distance"]),
        frozen_target=(
            float(geometry["take_profit_1"]) if "take_profit_1" in geometry else None
        ),
        frozen_target_dist=(
            float(geometry["target_dist"]) if "target_dist" in geometry else None
        ),
        frozen_max_lots=frozen_max_lots,
        unit=dict(unit),
        refusal_reasons=[str(reason) for reason in reasons if str(reason or "").strip()],
        packet_class=PACKET_CLASS_QUOTE_DEPENDENT,
        state=STATE_REFUSED_COST,
        last_reason=str(next(iter(reasons), "") or ""),
        candidate_id=candidate_id,
        max_chase_stop_fraction=chase_limit,
        hard_expiry_seconds=expiry_s,
        quote_bid=quote.get("bid"),
        quote_ask=quote.get("ask"),
        quote_spread_price=quote.get("spread_price"),
        quote_spread_r=quote.get("spread_r"),
        quote_at_utc=quote.get("quote_at_utc"),
        unrounded=unrounded_lots(unit, frozen_max_lots),
    )


def observe_frozen_price_intent(
    item: FrozenPriceIntent,
    *,
    now: datetime,
    tick: Any,
    place: bool,
    authority_reason: str | None = None,
    position_reason: str | None = None,
    cost_class: str | None = None,
    cost_reason: str | None = None,
) -> str:
    """Advance one open object. Returns the resulting state.

    ``place`` is the cycle flag. It is not a kill. ``authority_reason`` is
    set only when the withhold ask won. An empty reason does not invalidate.
    A null chase limit does not invalidate. A null expiry does not expire.
    """
    del place
    if item.is_terminal:
        return item.state
    if item.state == STATE_REFUSED_COST:
        item.state = STATE_OBSERVING

    if authority_reason:
        item.terminate(STATE_AUTHORITY_INVALIDATED, authority_reason)
        return item.state
    if position_reason:
        item.terminate(STATE_POSITION_CONFLICT, position_reason)
        return item.state
    if item.expired_at(now):
        seconds = _as_float(item.hard_expiry_seconds)
        item.terminate(
            STATE_EXPIRED,
            "hard_expiry_unset" if seconds is None else f"hard_expiry_seconds:{seconds:g}",
        )
        return item.state
    if is_blow_through(direction=item.direction, tick=tick, stop_loss=item.frozen_stop):
        item.terminate(STATE_PRICE_INVALIDATED, "blow_through_frozen_stop")
        return item.state
    chase = chase_stop_fraction(
        direction=item.direction,
        tick=tick,
        frozen_entry=item.frozen_entry,
        stop_dist=item.frozen_stop_dist,
    )
    limit = _as_float(item.max_chase_stop_fraction)
    if chase is not None and limit is not None and chase > limit:
        item.terminate(
            STATE_PRICE_INVALIDATED,
            f"chase_stop_fraction:{chase:.4f}>{limit:.4f}",
        )
        return item.state
    if cost_class in {PACKET_CLASS_STRUCTURAL, PACKET_CLASS_MODEL_INPUT}:
        item.terminate(
            STATE_COST_NEVER_VALID,
            cost_reason or "cost_reclassified_structural",
        )
        return item.state
    if cost_class in {PACKET_CLASS_QUOTE_DEPENDENT, None} and cost_class != PACKET_CLASS_NONE:
        if cost_reason:
            item.last_reason = str(cost_reason)
        item.state = STATE_OBSERVING
        return item.state
    item.state = STATE_OBSERVING
    return item.state
