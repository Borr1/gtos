"""UltimateBookLiveEngine — generation -> admission, default-off, exception-isolated.

Per book evaluation (driven on H4 closes by the orchestrator seam or the book-owner driver):
  1. run the ACTIVE sleeve generators across their on-surface symbols on the latest CLOSED bars
     -> list[TradeIntent] (the validated edge; sleeve-tagged), capturing each symbol's live price ctx;
  2. build the GovernorState from live equity + persisted high-water/day-anchor;
  3. call bridge.evaluate_vnext_ultimate_book_admission(config, intents, governor_state) -> decision
     (the triple-gate inside the bridge means: gates OFF -> shadow-only would_units, ZERO realized
     risk; gates ON + broad-selector clear -> realized_units carry the sized risk_pct_per_trade).
The order_router (separate, the FULL V4 route) consumes realized_units + the intents and places the
per-symbol orders. This engine NEVER places an order and NEVER raises into the caller (any failure ->
a safe no-op decision) so the live decision path is unaffected when the book errors or is off.
"""
from __future__ import annotations

import os
import threading
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

# MT5 timeframe constant -> bar interval in minutes (book uses M1/M15/H1/H4/D1).
_TF_MINUTES = {1: 1, 5: 5, 15: 15, 30: 30, 16385: 60, 16388: 240, 16408: 1440}

from .bar_provider import get_closed_bars, candles_to_bars, decision_day_of, enough, TF_M15
from .governor_state import GovernorStateBuilder
from .running_conviction_state import RunningConvictionLedger
from .bridge import (
    DEFAULT_CONFIG as _BRIDGE_DEFAULTS,
    config_bool_value,
    config_safety_flag,
    evaluate_vnext_ultimate_book_admission,
)
from .sleeves.registry import DISPLACEMENT_BUILT, active_specs
from .sleeve_geometry import apply_class_geometry
from .symbol_map import build_broker_symbol_resolver
from .admission import StressDeriskState, compute_stress_derisk_state, resolve_market_expansion_sleeves
from .edge_reconciler import closed_book_deals
from .event_clock_shadow import H4EventClockShadowLatch, TF_H4
from .lane_weights import neutral_snapshot

# Operator-facing terminal_status vocab. Admission still says
# decision_status == "no_candidates_this_bar"; the cycle/launcher reason
# must name WHY the generator produced nothing.
_OPERATOR_TERMINAL_STATUS_ORDER = (
    "stale_decision_bar",
    "profile_unsupported",
    "bars_unavailable",
    "insufficient_warmup",
    "future_decision_bar",
    "unit_unset",
    "no_candidate",
    "generator_exception",
    "spread_floor_refused",
    "entry_hour_deferred",
    "candidate_emitted",
)


def rewrite_no_candidates_operator_reason(
    decision_status: object,
    *,
    generation: Mapping[str, Any] | None = None,
    generation_terminals: list | None = None,
) -> object:
    """Rewrite bare no_candidates_this_bar into a terminal mix for operators.

    Bridge admission keeps ``decision_status == "no_candidates_this_bar"``.
    The cycle/launcher ``reason`` is what humans read; a gcc book whose
    terminals are stale_decision_bar / profile_unsupported must not look
    like a quiet market.
    """
    reason = decision_status
    if reason != "no_candidates_this_bar":
        return reason
    terminals = list(generation_terminals or [])
    if not terminals:
        return reason
    counts: dict[str, int] = {}
    for row in terminals:
        if not isinstance(row, Mapping):
            continue
        status = row.get("terminal_status")
        if not status:
            continue
        key = str(status)
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return reason
    parts: list[str] = []
    for status in _OPERATOR_TERMINAL_STATUS_ORDER:
        n = counts.pop(status, 0)
        if n:
            parts.append(f"{status}={n}")
    for status in sorted(counts):
        n = counts[status]
        if n:
            parts.append(f"{status}={n}")
    if not parts:
        return reason
    mix = ",".join(parts)
    evaluated = 0
    if isinstance(generation, Mapping):
        raw = generation.get("generator_evaluated_symbol_slot_count")
        try:
            evaluated = int(raw or 0)
        except (TypeError, ValueError):
            evaluated = 0
    if evaluated == 0:
        return f"terminals:{mix}"
    return f"no_candidates_this_bar+terminals:{mix}"


def _candidate_book_sleeves(config: dict) -> tuple[str, ...]:
    raw = config.get(
        "ultimate_book_candidate_book_sleeves",
        _BRIDGE_DEFAULTS.get("ultimate_book_candidate_book_sleeves", []),
    )
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,) if raw else ()
    if isinstance(raw, (list, tuple, set)):
        return tuple(str(item) for item in raw if str(item))
    return ()


def _market_expansion_sleeves(config: dict) -> tuple[str, ...]:
    raw = config.get(
        "ultimate_book_market_expansion_sleeves",
        _BRIDGE_DEFAULTS.get("ultimate_book_market_expansion_sleeves", []),
    )
    if raw is None:
        explicit = ()
    elif isinstance(raw, str):
        explicit = (raw,) if raw else ()
    elif isinstance(raw, (list, tuple, set)):
        explicit = tuple(str(item) for item in raw if str(item))
    else:
        explicit = ()
    policy = str(config.get(
        "ultimate_book_market_expansion_policy",
        _BRIDGE_DEFAULTS.get("ultimate_book_market_expansion_policy", "explicit_allowlist"),
    ) or "explicit_allowlist")
    resolved, error = resolve_market_expansion_sleeves(policy=policy, explicit_sleeves=explicit)
    return () if error else resolved


_CHALLENGE_NS = "operator"
_EXPANSION_WHOLE_MARKET = "all14_swap_adjusted"


def _include_unless_out(question: str, out_side: str, configured) -> bool:
    """Challenge include flag. The out side removes the surface only when it is unique highest.

    Other namespaces do not call this. An empty answer does not read ``configured``.
    """
    try:
        from src.judgment.book_engine_choices import spot
        winner = spot(question, spot=question, facts={"configured": configured, "namespace": _CHALLENGE_NS})
    except Exception:
        winner = None
    return winner != out_side


def _generation_policy_inputs(
    config: dict, namespace: str | None = None,
) -> tuple[bool, bool, bool, bool, tuple[str, ...], tuple[str, ...]]:
    """Resolve the shared include flags/allowlists once for generation and validation.

    On Challenge each include flag is a Choice. The surface stays in generation
    unless its out side is the unique highest. The config boolean is not read
    back as the decision. Other namespaces keep the config boolean.
    """
    cfg = config or {}
    if str(namespace or "") == _CHALLENGE_NS:
        inc3 = _include_unless_out(
            "include_clean3", "clean3_out",
            cfg.get("ultimate_book_include_clean3", _BRIDGE_DEFAULTS.get("ultimate_book_include_clean3", True)),
        )
        inc4 = _include_unless_out(
            "include_clean4", "clean4_out",
            cfg.get("ultimate_book_include_clean4", _BRIDGE_DEFAULTS.get("ultimate_book_include_clean4", False)),
        )
        inc_candidates = _include_unless_out(
            "include_candidate_book", "candidate_book_out",
            cfg.get(
                "ultimate_book_include_candidate_book",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False),
            ),
        )
        inc_expansion = _include_unless_out(
            "include_market_expansion", "market_expansion_out",
            cfg.get(
                "ultimate_book_include_market_expansion_book",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False),
            ),
        )
        expansion: tuple[str, ...] = ()
        if inc_expansion:
            resolved, error = resolve_market_expansion_sleeves(
                policy=_EXPANSION_WHOLE_MARKET, explicit_sleeves=(),
            )
            expansion = () if error else resolved
        return inc3, inc4, inc_candidates, inc_expansion, (), expansion
    inc3 = config_bool_value(
        cfg.get("ultimate_book_include_clean3",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_clean3", True)),
        _BRIDGE_DEFAULTS.get("ultimate_book_include_clean3", True),
    )
    inc4 = config_bool_value(
        cfg.get("ultimate_book_include_clean4",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_clean4", False)),
        _BRIDGE_DEFAULTS.get("ultimate_book_include_clean4", False),
    )
    inc_candidates = config_bool_value(
        cfg.get("ultimate_book_include_candidate_book",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False)),
        _BRIDGE_DEFAULTS.get("ultimate_book_include_candidate_book", False),
    )
    inc_expansion = config_bool_value(
        cfg.get("ultimate_book_include_market_expansion_book",
                _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False)),
        _BRIDGE_DEFAULTS.get("ultimate_book_include_market_expansion_book", False),
    )
    return (
        inc3, inc4, inc_candidates, inc_expansion,
        _candidate_book_sleeves(cfg), _market_expansion_sleeves(cfg),
    )


def effective_admission_sleeve_names(config: dict, namespace: str | None = None) -> set[str]:
    """Return the active admission/sizing registry with historical semantics intact."""
    from .admission import effective_registry
    inc3, inc4, inc_candidates, inc_expansion, candidates, expansion = (
        _generation_policy_inputs(config, namespace)
    )
    return set(effective_registry(
        include_clean3=inc3, include_clean4=inc4,
        include_candidate_book=inc_candidates,
        candidate_book_sleeves=candidates or None,
        include_market_expansion_book=inc_expansion,
        market_expansion_sleeves=expansion or None,
    ))


def effective_generation_specs(config: dict, tags=None, namespace: str | None = None) -> list:
    """Return the intersection of the generator and active admission surfaces.

    On Challenge a sleeve the intersection would drop stays unless
    ``off_generation_surface`` is the unique highest. Other namespaces keep
    the intersection boolean.
    """
    _inc3, _inc4, inc_candidates, inc_expansion, candidates, expansion = (
        _generation_policy_inputs(config, namespace)
    )
    admitted = effective_admission_sleeve_names(config, namespace)
    raw = active_specs(
        tags,
        include_candidate_book=inc_candidates,
        candidate_book_sleeves=candidates or None,
        include_market_expansion_book=inc_expansion,
        market_expansion_sleeves=expansion or None,
    )
    challenge = str(namespace or "") == _CHALLENGE_NS
    spot = None
    if challenge:
        try:
            from src.judgment.book_engine_choices import spot as _spot
            spot = _spot
        except Exception:
            spot = None
    kept = []
    for spec in raw:
        on_surface = spec.tag in admitted or spec.tag in DISPLACEMENT_BUILT
        if not challenge or on_surface:
            if on_surface:
                kept.append(spec)
            continue
        winner = None
        if spot is not None:
            winner = spot(
                "generation_surface",
                spot=spec.tag,
                facts={
                    "sleeve": spec.tag,
                    "in_admission": False,
                    "displacement": spec.tag in DISPLACEMENT_BUILT,
                },
            )
        if winner != "off_generation_surface":
            kept.append(spec)
    return kept


def effective_generation_sleeve_names(config: dict, tags=None, broker_symbol=None) -> set[str]:
    """Return effective specs with at least one profile-supported symbol."""
    supports = getattr(broker_symbol, "supports", None)
    return {
        spec.tag for spec in effective_generation_specs(config, tags)
        if not callable(supports) or any(supports(symbol) for symbol in spec.on_surface)
    }


#: Cap on every bounded skip SAMPLE in the generation telemetry. The COUNT beside each sample is
#: exact and unbounded; only the per-row detail is capped, so a weekend (when every slot is stale)
#: costs a fixed number of rows and still reports the true total. Same value the pre-existing
#: `broker_unsupported_skips` site inlines, named once here.
_SKIP_SAMPLE_CAP = 64


class _SlotFlight:
    """One in-flight fetch or score. Waiters share it. Other keys do not."""

    def __init__(self) -> None:
        self.event = threading.Event()
        self.value = None
        self.error: BaseException | None = None


_SLOT_LAST_BAR = threading.local()
_ENGINE_LOCK = threading.Lock()


def _sample_skip(bucket, row: dict) -> None:
    """Append `row` to a bounded telemetry sample. Never raises; never gates a decision."""
    try:
        if isinstance(bucket, list) and len(bucket) < _SKIP_SAMPLE_CAP:
            bucket.append(dict(row))
    except Exception:      # noqa: BLE001 — telemetry never gates
        pass


def _parse_bar_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return None


def _limit_level(anchor: Any, move: Any, direction: Any) -> float | None:
    """The open shifted by the returned distance once the side exists.

    A long limit is the open minus that distance. A short limit is the open
    plus that distance. A missing anchor, a missing move, a non-positive move,
    or any other direction leaves the limit unset.
    """

    if isinstance(anchor, bool) or isinstance(move, bool) or isinstance(direction, bool):
        return None
    if direction not in (1, -1):
        return None
    if anchor is None or move is None:
        return None
    try:
        distance = float(move)
        base = float(anchor)
        side = float(direction)
    except (TypeError, ValueError):
        return None
    if distance != distance or distance in (float("inf"), float("-inf")) or not (distance > 0):
        return None
    level = base - side * distance
    if level != level or level in (float("inf"), float("-inf")):
        return None
    return level


def _named_bar_count(value: Any) -> int | None:
    """A warmup count a score actually returned.

    A fraction, an empty score, or a non-positive number is not a count.
    Nothing here substitutes a printed minimum.
    """

    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")) or not (number > 0):
        return None
    nearest = round(number)
    if nearest != number:
        return None
    return int(nearest)


# Fact names copied onto the move ask. Labels below are the Score levels.
_ANCHOR_FACT_KEYS = (
    "high",
    "low",
    "close",
    "forming_high",
    "forming_low",
    "prev_high",
    "prev_low",
    "prev_extreme_high",
    "prev_extreme_low",
    "session_high",
    "session_low",
    "day_high",
    "day_low",
)

# (fact keys, level label). The value is the price distance from the entry.
_ANCHOR_SOURCES = (
    (("high", "forming_high"), "this bar high from the entry"),
    (("low", "forming_low"), "this bar low from the entry"),
    (("close",), "this bar close from the entry"),
    (("prev_high",), "previous bar high from the entry"),
    (("prev_low",), "previous bar low from the entry"),
    (("prev_extreme_high",), "previous bars high from the entry"),
    (("prev_extreme_low",), "previous bars low from the entry"),
    (("session_high",), "session high from the entry"),
    (("session_low",), "session low from the entry"),
    (("day_high",), "day high from the entry"),
    (("day_low",), "day low from the entry"),
)


def _aware_time(value: Any) -> datetime | None:
    return _parse_bar_time(value)


def _ordered_anchors(pairs: list[tuple[str, float]]) -> tuple[tuple[str, float], ...]:
    """Nearest distance first. The same distance keeps the earlier label."""

    ordered: list[tuple[str, float]] = []
    seen: list[float] = []
    for label, number in sorted(pairs, key=lambda item: item[1]):
        if any(number == prior for prior in seen):
            continue
        seen.append(number)
        ordered.append((label, number))
    return tuple(ordered)


def _atr_distance(facts: Mapping[str, Any] | None) -> float | None:
    """ATR already stored on the card, in price units. Absent stays absent."""

    if not isinstance(facts, Mapping):
        return None
    for key, value in facts.items():
        if str(key).lower() != "atr":
            continue
        number = UltimateBookLiveEngine._unit_number(value)
        if number is not None and number > 0:
            return number
    return None


def _first_price(facts: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        number = UltimateBookLiveEngine._unit_number(facts.get(key))
        if number is not None:
            return number
    return None


def _anchors_from_card(facts: Mapping[str, Any] | None) -> tuple[tuple[str, float], ...]:
    """(label, distance) pairs in price units, nearest first.

    This bar's high, low and close, the previous bars' extremes, the session
    and day extremes, and ATR when the card already has it. The side is not
    chosen here. Missing prices are dropped. Fewer than two distances is
    still returned; the spine does not post that ask.
    """

    if not isinstance(facts, Mapping):
        return ()
    entry = UltimateBookLiveEngine._unit_number(facts.get("entry"))
    if entry is None:
        entry = UltimateBookLiveEngine._unit_number(facts.get("forming_open"))
    if entry is None:
        entry = UltimateBookLiveEngine._unit_number(facts.get("open"))
    pairs: list[tuple[str, float]] = []
    if entry is not None:
        for keys, label in _ANCHOR_SOURCES:
            price = _first_price(facts, keys)
            if price is None:
                continue
            span = abs(price - entry)
            if span != span or span in (float("inf"), float("-inf")):
                continue
            pairs.append((label, span))
    atr = _atr_distance(facts)
    if atr is not None:
        pairs.append(("atr on this card", atr))
    return _ordered_anchors(pairs)


def _bind_entry(facts: dict) -> None:
    """The open the move is measured from. A missing open stays absent."""

    entry = UltimateBookLiveEngine._unit_number(facts.get("forming_open"))
    if entry is None:
        entry = UltimateBookLiveEngine._unit_number(facts.get("open"))
    if entry is None:
        facts.pop("entry", None)
    else:
        facts["entry"] = entry


def _session_extremes(rows: list[tuple[datetime | None, float | None, float | None]], ivl_minutes: int):
    """High and low of the contiguous run that ends on the current bar."""

    if not rows or not ivl_minutes:
        return None, None
    limit = timedelta(minutes=int(ivl_minutes))
    start = len(rows) - 1
    index = start
    while index > 0:
        later = rows[index][0]
        earlier = rows[index - 1][0]
        if later is None or earlier is None:
            return None, None
        if later - earlier > limit:
            break
        index -= 1
        start = index
    highs: list[float] = []
    lows: list[float] = []
    for _when, high, low in rows[start:]:
        if high is not None:
            highs.append(high)
        if low is not None:
            lows.append(low)
    return (max(highs) if highs else None, min(lows) if lows else None)


def _day_extremes(rows: list[tuple[datetime | None, float | None, float | None]], day: str):
    """High and low of bars on the current bar's UTC day."""

    highs: list[float] = []
    lows: list[float] = []
    for when, high, low in rows:
        if when is None:
            continue
        try:
            key = decision_day_of(when)
        except Exception:
            continue
        if key != day:
            continue
        if high is not None:
            highs.append(high)
        if low is not None:
            lows.append(low)
    return (max(highs) if highs else None, min(lows) if lows else None)


class UltimateBookLiveEngine:
    def __init__(self, config: dict, mt5, repo_root: str, namespace: str = "ftmo_primary",
                 account: str | None = None, bar_count: int = 260, broker_symbol=None,
                 recover_pre_gap_bar: bool = False, vol_level_tilt: bool = False,
                 spread_geometry_floor=None, entry_hour=None, broker_server=None,
                 event_clock_shadow: bool = False,
                 lane_weight_controller=None, f5_ledger=None,
                 risk_unit_floor_policy=None):
        self.config = config or {}
        self._mt5 = mt5
        self._namespace = namespace
        try:
            from .admission import bind_live_namespace
            bind_live_namespace(namespace)
        except Exception:
            pass
        # THE F5 NOTIONAL GOVERNOR SUBSTRATE (default None -> every seam below is a no-op).
        #
        # The minimal-size experiment places 1/200th-size lots while every DECISION must be
        # made at the production dial. Three of this class's broker reads feed the governor,
        # and left on the broker all three stop binding: equity never moves (no de-risk band,
        # no max-DD verdict), `realized_today_pct` stays ~0 (the soft daily stop never fires),
        # and -- the one that invalidates the experiment rather than merely weakening it --
        # `_open_risk_pct` reads ~0.0002 against a 0.04 cap, so the 4 % gross budget never
        # binds and the book runs 20+ concurrent units where production runs 2.
        #
        # So when a ledger is injected these three surfaces read the NOTIONAL book. Nothing
        # else changes: the same governor, the same thresholds, the same `breach_flatten_check`
        # acting on the same real positions.
        self._f5_ledger = f5_ledger
        # Session CO's learning-lane carrier.  The controller owns signature validation,
        # all-or-neutral scope, and the persisted decision-day latch.  This engine only
        # consumes its in-memory vector through the already-tested learning-rerate sizing
        # seam; no config/profile byte changes and the governor remains downstream/senior.
        self._lane_weight_controller = lane_weight_controller
        self._last_lane_weights_snapshot = neutral_snapshot(
            namespace, "unobserved", (), "lane_weights_not_observed", status="disabled"
        )
        # THE RATIFIED ENTRY-HOUR CONVENTION (Session CE, B2314), wired behind the same
        # launcher mechanism as the flags below. DEFAULT EMPTY -> byte-identical.
        #
        # `phase9/OWNER_DECISION_ENTRY_HOUR.md`: a sleeve whose decision bar closes at the
        # daily rollover enters at broker hour 01 instead. It is a DEFERRAL at generation
        # rather than a new decision timeframe because no bar closes at 01:00 on the matched
        # feed above M15 -- see `entry_hour.py`'s docstring, which also records why the
        # selection is per-sleeve (BTCUSD's hour-00 spread premium is x1.000 and the lever is
        # worth -0.019 R/trade there; `sub_mid_dn_revert`'s JPY crosses run x8-x20).
        #
        # `broker_server` is a CALLABLE resolved by the owner, not a string, so a terminal that
        # reconnects to a differently-named server cannot leave a stale name behind.
        self._entry_hour = dict(entry_hour or {})
        self._broker_server = broker_server
        # Q2 exact-H4 event observation. Its rows are telemetry only and are never
        # consumed by generation, admission, sizing, routing, or execution.
        if event_clock_shadow:
            resolver = broker_server if callable(broker_server) else (lambda: broker_server)
            self._event_clock_shadow = H4EventClockShadowLatch(resolver)
        else:
            self._event_clock_shadow = None
        # THE GENERATION-SIDE SPREAD-GEOMETRY FLOOR, wired behind the same launcher
        # mechanism as the three flags below and for the same reason (Session AY, B1810).
        #
        # A stop narrower than a few multiples of the round-trip spread should never be
        # PROPOSED. The live book already refuses to PLACE one -- twice, at the send layer
        # (`broker_net_cost_engine:718-727` and `book_owner._spread_cost_screen:4232-4270`,
        # both at `selected_cell_pretrade_max_spread_r`) -- but between generation and send
        # the doomed intent has already been counted by `_running_conviction_override`,
        # whose `precount_intent_filter` set does not include the cost screen and cannot:
        # the screen needs a tick and runs later. `admission.py:1188` takes
        # `na = max(na, override)`, monotone upward, so a sleeve that never places a leg can
        # still raise the day's Kelly-lite multiplier for every sleeve that does. Measured
        # on the 2026-07-25 export: 16 account-days counted a doomed sleeve, 3 of them moved
        # the multiplier, worst +25.2 % on every unit that day (AY_LIVE_SCREEN_EVIDENCE_V1).
        #
        # DEFAULT EMPTY -> not one tick of behaviour changes, and
        # `tests/ultimate_book/test_spread_geometry_floor.py` asserts the default path is
        # byte-identical to before this argument existed. Turning it ON for a sleeve is an
        # owner decision: it CHANGES WHICH TRADES AN ARMED BOOK PROPOSES.
        self._spread_geometry_floor = dict(spread_geometry_floor or {})
        # Q1 is a three-state policy, never a truthy mapping masquerading as activation.
        # OFF performs no extra reads and adds no telemetry. SHADOW/APPLY compute a proposal
        # only after pre-existing generation refusals AND admission have completed on the
        # original intents, so the running-conviction/candidate denominator stays exact.
        # The owner is the sole apply point, after its pre-send spread refusal and
        # immediately before order geometry is built.
        from .risk_unit_floor import OFF_POLICY
        self._risk_unit_floor_policy = risk_unit_floor_policy or OFF_POLICY
        # THE PRE-GAP BAR, wired behind a launcher flag (Session AI, 2026-07-30, B1075).
        #
        # `bar_provider.candles_to_bars` drops the last candle unconditionally on the
        # assumption that it is forming. At a session close it is not: the market shuts, no
        # new bar begins, and the last candle IS the freshly-closed decision bar. Session AB
        # measured the cost at H4 (29 of 29 fires immediately before a gap of >= 2 intervals,
        # 1.3 %-6.8 % of five sleeves' trades, 6.4 % on `sub_xvol_pullback`) and Session AF at
        # D1, where it is four times larger because every Friday is a pre-gap bar: 5,705 of
        # 134,027 trades, 4.26 %.
        #
        # AB wrote and tested the capability and DECLINED to wire it, for a reason that was
        # right: "Wiring it changes which bars an armed book trades on a funded account, and I
        # cannot gate it behind a config key because `config/agent_config.yaml` is bound to the
        # live activation token."
        #
        # The gate is therefore a CONSTRUCTOR ARGUMENT reached from `run_book.py
        # --recover-pre-gap-bar`, which is the same mechanism `--tags` already uses to bound
        # the armed book: settable at the supervisor, needs no source edit on a live host, and
        # -- the part that matters -- does not change one byte of `agent_config.yaml`, so the
        # activation token's config digest is untouched and the armed book keeps placing.
        #
        # DEFAULT FALSE, and `test_pre_gap_bar_wiring.py` asserts the default path is
        # byte-identical to before this argument existed. Turning it ON is an owner decision
        # with a measured price in BOTH directions: the unreachable population's mean is
        # -0.0771 R against +0.0117 R for reachable trades (AF section 1.1), so on the D1
        # family this defect is currently SAVING money, while at H4 the sleeve it costs most is
        # the one whose only gate failure is significance at n=88.
        self._recover_pre_gap_bar = bool(recover_pre_gap_bar)
        # THE WAVE-11 VOL-LEVEL SIZING TILT, wired behind the same launcher mechanism and for
        # the same reason (Session AR, B1452). `admission.vol_level_tilt_for` applies
        # clamp(vr/2.0, 0.80, 1.20) to `sub_xvol_pullback` intents -- a net ~7.5 % DE-RISK whose
        # size-up is reserved for the most expanded fifth of the sleeve's own firing range. See
        # the VOL_LEVEL_TILT block in `admission.py` for the measurement and
        # `phase11/receipts/VOL_LEVEL_TILT_DECLARATION_V1.json` for the prospective declaration.
        #
        # A SIZING flag is bridge-owned, not engine-owned, so unlike --recover-pre-gap-bar it
        # cannot be consumed here. It is instead INJECTED into the in-memory runtime dict handed
        # to `bridge.evaluate_vnext_ultimate_book_admission` (see `evaluate`), which reads it with
        # `_bool(cfg, "ultimate_book_vol_level_tilt")` exactly like every other flag. The point of
        # the injection is that `config/agent_config.yaml` -- and `config/profiles/redacted_account.yaml`
        # -- keep every byte, so neither live account's activation-token config digest moves and
        # neither armed book stops placing. `self.config` itself is NOT mutated: a copy is made at
        # the call site so any other reader of the config sees the file's own values.
        #
        # DEFAULT FALSE and `test_ar_vol_level_tilt.py` asserts the default path is byte-identical
        # to before this argument existed. Turning it ON is an owner decision on AR-1d's number.
        self._vol_level_tilt = bool(vol_level_tilt)
        # D10 (SLEEVE_BOOK_DEFECT_REGISTER): the allocation-profile SIDE is hard-wired to "A" and
        # book_owner.py never passes it, so BOTH live namespaces size from risk_per_unit_A. That is
        # harmless at every BALANCED dial (A == B, including the live clean3_w7_ceiling_nom2p00) and a
        # silent 2x risk error on one account under an ASYMMETRIC one such as staggered_1p00_0p50
        # (admission.py:679-682), which would run 1.00%/1.00% instead of 1.00%/0.50%.
        #
        # Deriving the side from the namespace is a RISK-ALLOCATION change and therefore the owner's
        # call, not a hygiene fix. What is landed here is the guard: remember whether the caller
        # actually chose a side, and refuse to size an asymmetric profile when nobody did
        # (_asymmetric_profile_guard). "A" stays the effective default, so balanced dials — i.e. every
        # dial live today — are byte-identical to before.
        self._account_explicit = account is not None
        self._account = "A" if account is None else account
        self._bar_count = bar_count
        # Governor anchoring (broker-correct, config-overridable; deploy defaults below):
        #  - static_initial_balance: the broker max-DD floor is STATIC from the initial balance
        #    (FTMO/FN 100k => fixed 90k floor); the wall is pinned to this reference (max_dd_reference_equity)
        #    and BYPASSES the trailing high-water entirely — high_water is kept only as a >=equity invariant.
        #  - daily_reset_offset_hours: the STATIC fallback only. The reset window is resolved per
        #    account at runtime; see reset_rule below and GovernorStateBuilder._effective_offset_h.
        #  - reset_rule: THE ACCOUNT'S OWN daily-loss reset calendar, corrected 2026-07-26 (B56).
        #    The two firms do not share a rule and the difference is not cosmetic:
        #      redacted_account resets at 00:00 SERVER time (GMT+2/+3) -> no rule, the detected offset is it.
        #      FTMO       resets at 00:00 CE(S)T, which is NOT its server clock. FTMO's MT5 server
        #                 runs the US DST calendar while CE(S)T runs the EU one, so server midnight
        #                 is 1 h early normally and 2 h early for ~4 weeks a year.
        #    Sourced from the profile the account already ships -- config/profiles/ftmo.yaml:85
        #    declares `prop_safe_selector_daily_reset_timezone: Europe/Prague` and :102 records the
        #    firm's rule verbatim. That file is decision-contract-bound (H1), so this reads the key
        #    rather than adding one; an account whose profile is silent keeps server midnight.
        _gov_init_bal = self.config.get("governor_static_initial_balance", 100000.0)
        _gov_reset_off = self.config.get("governor_daily_reset_offset_hours", 3.0)
        _gov_reset_rule = (self.config.get("governor_daily_reset_rule")
                           or self.config.get("prop_safe_selector_daily_reset_timezone")
                           or None)
        self._governor = GovernorStateBuilder(
            repo_root, namespace=namespace,
            static_initial_balance=_gov_init_bal, daily_reset_offset_hours=_gov_reset_off,
            offset_provider=self._live_broker_offset_hours,
            reset_rule=_gov_reset_rule)
        # leak-free RUNNING per-day conviction count store (recovers the validated full-day Kelly-lite
        # convention without lookahead; engine-gated by ultimate_book_kelly_running_count, default OFF).
        self._running_conviction = RunningConvictionLedger(repo_root, namespace=namespace)
        # canonical (registry on_surface) -> broker mt5_symbol for the bar fetch. The caller (owner)
        # passes a resolver built from the merged profile; default identity for configs without an
        # instruments map (metals/crypto are identity anyway).
        self._broker_symbol = broker_symbol or build_broker_symbol_resolver(self.config)
        self._last_generation_telemetry: dict[str, object] = {}
        self._last_generation_skips: list[dict] = []
        # One terminal observation per active spec x symbol slot. The owner writes the
        # complete list to observation ledgers; no trading branch reads it.
        self._last_generation_terminals: list[dict] = []
        self._stress_cache = None   # (server_date_key, StressDeriskState) — recomputed once per server-day
        # Decision-bar time-repair memo, persisted per namespace so a restart
        # inside a bar reuses the stamp it already placed against. That stamp is
        # the placement-ledger idempotency key.
        self._bar_offset_state_path = os.path.join(
            repo_root, "pipeline_state", "ultimate_book", namespace, "bar_time_repair.json"
        )
        self._bar_offset_latch = self._load_bar_offset_latch()
        self._hop_scores = {}
        self._hop_inflight = {}
        self._hop_flight_lock = threading.Lock()
        self._bar_series_lock = threading.Lock()
        self._bar_inflight = {}
        self._offset_lock = threading.Lock()
        self._offset_inflight = {}
        self._offset_asked = set()
        self._forming_reads = {}
        # CONTRACT leftover (Fable 5.1): assign the calendar the −45 amplifier reads.
        # getattr-only left _f5_calendar_events None forever (Grok sit 2026-09-02).
        # Loader already mtime-caches. Size-2 stays F5_CAL_PRIME_SIZE_MULT=1.0; not a gate.
        self._repo_root = repo_root
        self._f5_calendar_events = []
        if str(namespace) == "operator":
            try:
                from .minimal_size import f5_load_live_calendar_events
                self._f5_calendar_events = f5_load_live_calendar_events(repo_root)
            except Exception:
                self._f5_calendar_events = []

    def _stress_derisk_state(self, now):
        """Realized prior-day state for the reactive temporal de-risk overlay (consecutive-loss-day ladder
        + co-loss breaker), computed ONCE per server-day from the broker's closed BOOK deals and cached.
        Returns None when the overlay is OFF or no raw broker module is available (mocks). On real-broker
        read failure, fail safe to maximum reactive derisk instead of silently widening risk.
        Leak-free: compute_stress_derisk_state excludes today's in-progress server-day."""
        if not config_bool_value(
            self.config.get(
                "ultimate_book_stress_derisk",
                _BRIDGE_DEFAULTS.get("ultimate_book_stress_derisk", False),
            ),
            _BRIDGE_DEFAULTS.get("ultimate_book_stress_derisk", False),
        ):
            return None
        try:
            date_key = self.reset_window_date(now)
        except Exception:
            date_key = None
        cached = self._stress_cache
        if cached is not None and date_key is not None and cached[0] == date_key:
            return cached[1]
        state = None
        raw = None
        try:
            raw = getattr(self._mt5, "_mt5", None)   # the underlying MetaTrader5 module (None on mocks)
            if raw is not None:
                if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                    hours = self._hop_score(
                        "stress_lookback_hours",
                        "The score you return is how many hours of closed deals this state reads. "
                        "An empty score leaves the stress state unset. Do not send.",
                        {"reset_date": date_key},
                        cache_key=("stress_lookback_hours", str(date_key)),
                    )
                    off = self._live_broker_offset_hours()
                    if hours is not None and off is not None:
                        state = compute_stress_derisk_state(
                            closed_book_deals(raw, now, hours=hours),
                            now,
                            offset_hours=off,
                        )
                else:
                    deals = closed_book_deals(raw, now, hours=192)   # 8 days: 5 trailing + margin
                    try:
                        off = float(self._mt5.get_broker_offset_seconds()) / 3600.0
                    except Exception:
                        off = float(self.config.get("governor_daily_reset_offset_hours", 3.0) or 0.0)
                    state = compute_stress_derisk_state(deals, now, offset_hours=off)
        except Exception:
            if str(getattr(self, "_namespace", "") or "") == "operator":
                state = None
            elif raw is not None:
                state = StressDeriskState(consecutive_loss_days=2, trailing_neg_frac=1.0)
            else:
                state = None
        self._stress_cache = (date_key, state)
        return state

    def _live_broker_offset_hours(self):
        """The live broker server-time offset in HOURS for the governor's DST-correct reset window, or None
        when the mt5 does not expose it (mocks) / before first detection (returns 0 -> the governor's band
        guard falls back to the static config offset until a real offset is detected from a live tick)."""
        try:
            fn = getattr(self._mt5, "get_broker_offset_seconds", None)
            if not callable(fn):
                return None
            secs = fn()
            return (float(secs) / 3600.0) if secs is not None else None
        except Exception:
            return None

    def _broker_offset_score(
        self,
        *,
        latest_iso: str,
        interval_minutes: int,
        adapter_offset_seconds: int | None,
        seconds_from_clock: float,
    ) -> float | None:
        """Offset seconds for this bar. Empty leaves the stamp unshifted."""

        if str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS:
            return None
        try:
            from src.judgment.nineteen import score

            offset_card = {
                "latest_iso": latest_iso,
                "interval_minutes": interval_minutes,
                "adapter_offset_seconds": adapter_offset_seconds,
                "seconds_from_clock": seconds_from_clock,
            }
            return score(
                offset_card,
                question_id="broker_offset_seconds",
                instructions=(
                    "The score you return is the broker offset in seconds to subtract "
                    "so this bar stamp is the close. "
                    "seconds_from_clock is this bar's close minus the clock. "
                    "An empty score leaves the stamp unshifted and does not restore a fixed window. "
                    "Do not send."
                ),
                anchors=_anchors_from_card(offset_card),
            )
        except Exception:
            return None

    def _active_sleeve_names(self) -> set:
        """The sleeves in the ACTIVE book (effective registry), read with the SAME include flags
        convention the sizing path uses, so GENERATION, SIZING, and the Kelly conviction count share one
        source of truth. DF-1 fix: a sleeve dropped from the book (clean_3 when include_clean3=False) must
        not GENERATE — otherwise its phantom firing still inflates the Kelly-lite conviction count and
        over-sizes the real units even though it can never be sized or placed."""
        return effective_admission_sleeve_names(
            self.config, namespace=getattr(self, "_namespace", None),
        )

    def _spot_choice(self, question: str, *, spot: str, facts: dict | None = None) -> str | None:
        """Challenge spot Choice. None when this book is not Challenge or there is no unique winner."""
        if str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS:
            return None
        try:
            from src.judgment.book_engine_choices import spot as ask
            return ask(question, spot=spot, facts=facts)
        except Exception:
            return None

    # ---------------- intent generation ----------------
    def _resolve_repair_offset_seconds(
        self,
        times: list[datetime],
        *,
        now: datetime,
        interval_minutes: int,
        cache_key: tuple | None,
    ) -> int | None:
        """One repair for this raw bar. Other bars do not wait on it."""

        if not times:
            return self._resolve_repair_offset_body(
                times, now=now, interval_minutes=interval_minutes, cache_key=cache_key,
            )
        latest = times[-1]
        latest = (latest if latest.tzinfo else latest.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        memo_key = (cache_key, latest.isoformat())
        lock = self._offset_lock
        with lock:
            latch = getattr(self, "_bar_offset_latch", None) or {}
            asked = getattr(self, "_offset_asked", None)
            if isinstance(asked, set) and memo_key in asked and memo_key in latch:
                return latch[memo_key]
            if memo_key in latch and latch[memo_key] is not None:
                return latch[memo_key]
            gate = self._offset_inflight.get(memo_key)
            if gate is None:
                gate = _SlotFlight()
                self._offset_inflight[memo_key] = gate
                owner = True
            else:
                owner = False
        if not owner:
            gate.event.wait()
            if gate.error is not None:
                raise gate.error
            return gate.value
        try:
            value = self._resolve_repair_offset_body(
                times, now=now, interval_minutes=interval_minutes, cache_key=cache_key,
            )
            gate.value = value
            return value
        except Exception as exc:
            gate.error = exc
            raise
        finally:
            gate.event.set()
            with lock:
                if self._offset_inflight.get(memo_key) is gate:
                    self._offset_inflight.pop(memo_key, None)

    def _resolve_repair_offset_body(
        self,
        times: list[datetime],
        *,
        now: datetime,
        interval_minutes: int,
        cache_key: tuple | None,
    ) -> int | None:
        """Pick the broker offset to subtract, WITHOUT letting the wall clock choose it.

        Why this is not a free search any more. ``times[-1]`` becomes
        ``decision_bar_iso``, which is the placement-ledger idempotency key
        (``placement_ledger.py:1,88``). The original repair scanned 30-minute
        offsets and accepted the first one that made the bar look fresh
        *relative to now* — so as the wall clock advanced, the smallest
        satisfying offset shrank by one step every 30 minutes and the SAME bar
        acquired a NEW key every 30 minutes. Within a day the
        one-unit-per-(sleeve,symbol,day) cap (``book_owner.py:1601-1606``)
        absorbs that, but a shift of up to 5 h across a UTC date boundary
        changes the derived decision *day* too, and then nothing stops a second
        unit on the same real bar.

        So, in order:

        1. **Ask the adapter.** The broker offset is a property of the broker,
           and ``RealMT5`` already self-detects it and re-detects every 6 h
           (``mt5_real.py:74-119``). A value from there is the same on every
           cycle. This is the answer in every case except the one the repair
           exists for.
        2. **Clear a superseded repair.** If a positive adapter offset now yields
           a healthy closed bar, it outranks any fallback memo left by an earlier
           poisoned adapter state. The same raw ISO can otherwise collide with a
           later correctly-normalized bar and be shifted twice.
        3. **Latch.** If the adapter has nothing (the leaked zero-offset state),
           search once per (symbol, timeframe) and reuse that result for the
           rest of the process, so the stamp stops moving.
        4. **Persist.** The memo is written to the namespace's state directory,
           so a RESTART inside the same bar reuses the stamp it already placed
           against instead of re-deriving one from a new `now`.

        An earlier version of this fix refused any shift that changed the UTC
        day, on the reasoning that a changed decision *day* also changes the
        per-day placement cap's key. It worked, but it bought restart-stability
        by **dropping bars**: measured at 12.5 % of M15 and H1 bars per day in
        the leaked state (H4 was unaffected). Persisting the memo gives the same
        guarantee and costs nothing, so the refusal is gone.
        """

        latch = getattr(self, "_bar_offset_latch", None)
        if latch is None:
            latch = self._bar_offset_latch = {}

        ref_now = (now if now.tzinfo else now.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        latest = times[-1]
        latest = (latest if latest.tzinfo else latest.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        # Memoized on the RAW bar, not on the symbol: the same raw bar must
        # always produce the same repaired stamp however many cycles evaluate
        # it, because that stamp is the placement idempotency key. Keying on the
        # symbol alone was not enough -- a later cycle at which the leaked bar
        # no longer looks future would skip the repair and stamp the raw time.
        memo_key = (cache_key, latest.isoformat())

        def _remember(value: float | None) -> float | None:
            challenge = str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS
            cap = None
            if challenge:
                bound = self._hop_score(
                    "bar_offset_latch_bound",
                    "The score you return is how many repaired bar stamps this book remembers. "
                    "An empty score does not clear that memory. Do not send.",
                    {"remembered": len(latch)},
                    cache_key=("bar_offset_latch_bound",),
                )
                if bound is not None:
                    try:
                        cap = int(bound)
                    except (TypeError, ValueError):
                        cap = None
            with self._offset_lock:
                if challenge:
                    if cap is not None and cap > 0 and len(latch) > cap:
                        latch.clear()
                elif len(latch) > 4096:
                    latch.clear()
                asked_set = getattr(self, "_offset_asked", None)
                if not isinstance(asked_set, set):
                    asked_set = set()
                    self._offset_asked = asked_set
                asked_set.add(memo_key)
                latch[memo_key] = value
                self._persist_bar_offset_latch()
            return value

        detected = None
        try:
            probe = getattr(self._mt5, "get_broker_offset_seconds", None)
            if callable(probe):
                raw_offset = probe()
                if raw_offset is not None:
                    detected = int(raw_offset)
        except Exception:
            detected = None

        seconds_from_clock = (
            latest + timedelta(minutes=int(interval_minutes)) - ref_now
        ).total_seconds()
        asked_set = getattr(self, "_offset_asked", None)
        if not isinstance(asked_set, set):
            asked_set = set()
            self._offset_asked = asked_set
        # A stored integer, including zero, is the score for this bar.
        # A stored None has not been scored this process.
        if memo_key in asked_set and memo_key in latch:
            return latch[memo_key]
        if memo_key in latch and latch[memo_key] is not None:
            return latch[memo_key]

        def _offset() -> float | None:
            return self._broker_offset_score(
                latest_iso=latest.isoformat(),
                interval_minutes=int(interval_minutes),
                adapter_offset_seconds=detected,
                seconds_from_clock=seconds_from_clock,
            )

        challenge = str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS
        bound_key = ("bar_offset_latch_bound",)
        hop_cache = getattr(self, "_hop_scores", None)
        bound_ready = isinstance(hop_cache, dict) and bound_key in hop_cache
        if challenge and not bound_ready:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=2) as pool:
                offset_f = pool.submit(_offset)
                bound_f = pool.submit(self._seed_latch_bound, len(latch))
                asked = offset_f.result()
                bound_f.result()
        else:
            asked = _offset()
        if asked is None:
            return _remember(None)
        whole = self._unit_number(asked)
        if whole is None:
            return _remember(None)
        return _remember(whole)

    def _bar_offset_latch_path(self) -> "str | None":
        return getattr(self, "_bar_offset_state_path", None)

    def _load_bar_offset_latch(self) -> dict:
        """Restart-stability for the decision-bar stamp. Best-effort: an
        unreadable file means an empty memo, never a raise."""

        path = self._bar_offset_latch_path()
        if not path:
            return {}
        try:
            import json as _json
            with open(path, encoding="utf-8") as handle:
                raw = _json.load(handle)
            if not isinstance(raw, dict):
                return {}
            def _retuple(value):
                # JSON has no tuples, so the (symbol, timeframe, count) part of
                # the key round-trips as a LIST and would never match the live
                # key again. Rebuild it depth-first.
                return tuple(_retuple(x) for x in value) if isinstance(value, list) else value

            return {_retuple(_json.loads(k)): v for k, v in raw.items()}
        except Exception:  # noqa: BLE001
            return {}

    def _persist_bar_offset_latch(self) -> None:
        path = self._bar_offset_latch_path()
        if not path:
            return
        try:
            import json as _json
            import os as _os
            import uuid as _uuid
            latch = getattr(self, "_bar_offset_latch", {}) or {}
            payload = {_json.dumps(list(k)): v for k, v in latch.items()}
            _os.makedirs(_os.path.dirname(path), exist_ok=True)
            tmp = f"{path}.{_os.getpid()}.{_uuid.uuid4().hex}.tmp"
            with open(tmp, "w", encoding="utf-8") as handle:
                _json.dump(payload, handle)
            _os.replace(tmp, path)
        except Exception:  # noqa: BLE001
            pass

    def _normalize_future_bar_times(
        self,
        times: list[datetime],
        *,
        now: datetime,
        interval_minutes: int | None,
        cache_key: tuple | None = None,
    ) -> tuple[list[datetime], int | None]:
        """Repair broker-local bar timestamps that slipped through as UTC.

        The MT5 wrapper normally subtracts the broker offset (``mt5_real.py:246-262``
        does it for candles), so in the healthy case this returns immediately. If
        a live worker starts with a bad zero offset, the latest "closed" bar can
        appear hours in the future and trigger early placement; shifting the full
        aligned series back by a real broker offset repairs it. When no offset is
        both plausible and safe, the series is left unchanged so the future-bar
        fail-safe skips the bar.
        """
        if not times or not interval_minutes:
            return times, None
        try:
            ref_now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
            ref_now = ref_now.astimezone(timezone.utc)
            latest = times[-1]
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            latest = latest.astimezone(timezone.utc)
            # NOTE: the "is this bar in the future?" test lives inside the
            # resolver, not here, so that its answer is memoized with the bar.
            # Testing it here would let a later cycle -- at which the same
            # leaked bar no longer looks future -- bypass the memo and stamp the
            # raw broker-local time.
            offset = self._resolve_repair_offset_seconds(
                times,
                now=ref_now,
                interval_minutes=int(interval_minutes),
                cache_key=cache_key,
            )
            if not offset:
                return times, None
            shifted = [
                (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
                - timedelta(seconds=offset)
                for t in times
            ]
            return shifted, offset
        except Exception:
            return times, None

    def _warmup_required(self, spec):
        """Warmup count for this cluster. The map is not the count."""

        if str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS:
            return None
        cluster = getattr(spec, "cluster", None)
        return self._hop_score(
            "warmup_bars",
            "The score you return is the warmup bar count for this cluster. "
            "An empty score leaves the count unset. Do not send.",
            {"cluster": cluster, "sleeve": getattr(spec, "tag", None)},
            cache_key=("warmup_bars", str(cluster)),
        )

    def _unread_open_risk(self) -> float | None:
        """The score for an unreadable open-risk fraction. Empty stays unset."""

        number = self._spine_score(
            "gross_open_risk_pct",
            "The score you return is the open-risk fraction when the ledger cannot be read. "
            "An empty score leaves that fraction unset. Do not send.",
            {},
        )
        if number is None:
            return None
        return float(number)

    def _hop_score(self, question_id: str, instructions: str, facts: dict | None, *, cache_key):
        """One Score for this state. The same key shares one flight.

        Empty, tie, and error stay unset for that key. Waiters take that
        result and do not post again.
        """

        cache = getattr(self, "_hop_scores", None)
        if not isinstance(cache, dict):
            cache = {}
            self._hop_scores = cache
        anchors = _anchors_from_card(facts)
        stored = (cache_key, anchors)
        lock = getattr(self, "_hop_flight_lock", None)
        inflight = getattr(self, "_hop_inflight", None)
        if not isinstance(lock, threading.Lock) or not isinstance(inflight, dict):
            with _ENGINE_LOCK:
                lock = getattr(self, "_hop_flight_lock", None)
                inflight = getattr(self, "_hop_inflight", None)
                if not isinstance(lock, threading.Lock) or not isinstance(inflight, dict):
                    lock = threading.Lock()
                    inflight = {}
                    self._hop_flight_lock = lock
                    self._hop_inflight = inflight
        with lock:
            if stored in cache:
                return cache[stored]
            gate = inflight.get(stored)
            if gate is None:
                gate = _SlotFlight()
                inflight[stored] = gate
                owner = True
            else:
                owner = False
        if not owner:
            gate.event.wait()
            return gate.value
        cached = None
        try:
            from src.judgment.nineteen import score

            number = score(
                dict(facts or {}),
                question_id=str(question_id),
                instructions=str(instructions),
                anchors=anchors,
            )
            if isinstance(number, bool) or number is None:
                cached = None
            else:
                try:
                    cached = float(number)
                except (TypeError, ValueError):
                    cached = None
                else:
                    if cached != cached or cached in (float("inf"), float("-inf")):
                        cached = None
        except Exception:
            cached = None
        finally:
            with lock:
                cache[stored] = cached
                if inflight.get(stored) is gate:
                    inflight.pop(stored, None)
            gate.value = cached
            gate.event.set()
        return cached

    def _seed_latch_bound(self, remembered: int) -> None:
        self._hop_score(
            "bar_offset_latch_bound",
            "The score you return is how many repaired bar stamps this book remembers. "
            "An empty score does not clear that memory. Do not send.",
            {"remembered": remembered},
            cache_key=("bar_offset_latch_bound",),
        )

    def _spine_score(self, role: str, instructions: str, facts: dict | None = None):
        state = {
            "role": role,
            "namespace": getattr(self, "_namespace", None),
        }
        if isinstance(facts, dict):
            state.update(facts)
        key = (str(role), tuple(sorted((str(k), repr(v)) for k, v in state.items())))
        return self._hop_score(role, instructions, state, cache_key=key)

    def _f5_atr(self, bars, symbol: str | None = None) -> float | None:
        period = self._spine_score(
            "atr_period",
            "The score you return is the ATR period for these bars. "
            "An empty score leaves the average unset. Do not send.",
            {"symbol": symbol, "bar_count": len(bars) if bars else None},
        )
        if period is None:
            return None
        try:
            n = int(period)
        except (TypeError, ValueError):
            return None
        if n <= 0 or not bars or len(bars) <= n:
            return None
        trs = []
        for i in range(len(bars) - n, len(bars)):
            b, prev = bars[i], bars[i - 1]
            tr = max(float(b.h) - float(b.l), abs(float(b.h) - float(prev.c)), abs(float(b.l) - float(prev.c)))
            trs.append(tr)
        atr = sum(trs) / len(trs)
        return atr if atr > 0 else None

    def _f5_peer_panel(self, bar_cache: dict, symbol: str) -> dict | None:
        """Peer move in its own ATR. A missing span or period leaves the panel unset."""
        span = self._spine_score(
            "peer_move_bars",
            "The score you return is how many bars the peer move covers. "
            "An empty score leaves the panel unset. Do not send.",
            {"symbol": symbol},
        )
        if span is None:
            return None
        try:
            back = int(span)
        except (TypeError, ValueError):
            return None
        if back <= 0:
            return None
        moves: dict[str, float] = {}
        lock = getattr(self, "_bar_series_lock", None)
        if isinstance(lock, threading.Lock):
            with lock:
                series = list(bar_cache.items())
        else:
            series = list(bar_cache.items())
        for (sym, tf, _n), pair in series:
            if int(tf) != int(TF_M15):
                continue
            bars = pair[0] if pair else None
            if not bars or len(bars) <= back:
                continue
            atr = self._f5_atr(bars, str(sym))
            if not atr:
                continue
            try:
                moves[str(sym)] = (float(bars[-1].c) - float(bars[-1 - back].c)) / float(atr)
            except Exception:
                continue
        peers = {k: v for k, v in moves.items() if k != symbol}
        if not peers:
            return None
        aligned = sum(peers.values()) / len(peers)
        panel = {"aligned_move": aligned}
        panel.update(peers)
        return panel

    @staticmethod
    def _unit_number(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return number

    @staticmethod
    def _bar_number(bar: Any, *names: str) -> float | None:
        for name in names:
            raw = bar.get(name) if isinstance(bar, Mapping) else getattr(bar, name, None)
            number = UltimateBookLiveEngine._unit_number(raw)
            if number is not None:
                return number
        return None

    def _unit_quote(self, symbol: str) -> tuple[float | None, float | None]:
        """One bid and ask for this symbol during the cycle. A miss stays absent."""

        cache = getattr(self, "_unit_quotes", None)
        if not isinstance(cache, dict):
            cache = {}
            self._unit_quotes = cache
        if symbol in cache:
            return cache[symbol]
        bid = ask = None
        try:
            tick = self._mt5.get_tick(self._broker_symbol(symbol))
            if isinstance(tick, Mapping):
                bid = self._unit_number(tick.get("bid"))
                ask = self._unit_number(tick.get("ask"))
            elif tick is not None:
                bid = self._unit_number(getattr(tick, "bid", None))
                ask = self._unit_number(getattr(tick, "ask", None))
        except Exception:
            bid = ask = None
        cache[symbol] = (bid, ask)
        return bid, ask

    @staticmethod
    def _direction_if_any(spec: Any, bar: Any) -> Any:
        """A direction already on the slot. This does not invent a side."""

        for raw in (
            getattr(spec, "direction", None),
            bar.get("direction") if isinstance(bar, Mapping) else getattr(bar, "direction", None),
        ):
            if raw in (1, -1, "long", "short", "LONG", "SHORT"):
                return raw
        return None

    def _forming_from_candle(self, candle: Any, ivl: int, now: datetime) -> dict | None:
        if isinstance(candle, Mapping):
            open_px = self._unit_number(candle.get("open"))
            high = self._unit_number(candle.get("high"))
            low = self._unit_number(candle.get("low"))
            last = self._unit_number(candle.get("close"))
            raw_time = candle.get("time")
        else:
            open_px = self._unit_number(getattr(candle, "open", None))
            high = self._unit_number(getattr(candle, "high", None))
            low = self._unit_number(getattr(candle, "low", None))
            last = self._unit_number(getattr(candle, "close", None))
            raw_time = getattr(candle, "time", None)
        opened = _parse_bar_time(raw_time)
        if opened is None or open_px is None:
            return None
        ref = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        seconds = (
            opened.astimezone(timezone.utc)
            + timedelta(minutes=int(ivl))
            - ref.astimezone(timezone.utc)
        ).total_seconds()
        if seconds <= 0:
            return None
        return {
            "open": open_px,
            "high": high,
            "low": low,
            "last": last,
            "seconds_to_close": seconds,
        }

    def _read_forming_bar(self, symbol, timeframe, ivl, now) -> dict | None:
        """The candle that has not closed. A miss stays absent. This does not name the bar."""

        if symbol is None or timeframe is None or not ivl or now is None:
            return None
        cache = getattr(self, "_forming_reads", None)
        if not isinstance(cache, dict):
            cache = {}
            self._forming_reads = cache
        key = (str(symbol), str(timeframe), int(ivl))
        if key in cache:
            return cache[key]
        found = None
        probe = getattr(self._mt5, "get_candles", None)
        if callable(probe):
            try:
                resolver = getattr(self, "_broker_symbol", None)
                broker = resolver(symbol) if callable(resolver) else symbol
                candles = probe(broker, timeframe, 2)
                rows = [] if candles is None or isinstance(candles, (str, bytes)) else list(candles)
                if rows:
                    found = self._forming_from_candle(rows[-1], int(ivl), now)
            except Exception:
                found = None
        cache[key] = found
        return found

    def _projected_move(self, facts: Mapping[str, Any], timeframe) -> float | None:
        """Price distance from the open for this bar's price state. One ask per state."""

        anchor = self._unit_number(facts.get("forming_open"))
        if anchor is None:
            anchor = self._unit_number(facts.get("open"))
        high = self._unit_number(facts.get("forming_high"))
        if high is None:
            high = self._unit_number(facts.get("high"))
        low = self._unit_number(facts.get("forming_low"))
        if low is None:
            low = self._unit_number(facts.get("low"))
        bar_iso = facts.get("decision_bar_iso")
        entry = self._unit_number(facts.get("entry"))
        if entry is None:
            entry = anchor
        payload = {
            "symbol": facts.get("symbol"),
            "timeframe": timeframe,
            "bar_iso": bar_iso,
            "entry": entry,
            "open": anchor,
            "high": high,
            "low": low,
            "close": self._unit_number(facts.get("close")),
            "bid": self._unit_number(facts.get("bid")),
            "ask": self._unit_number(facts.get("ask")),
            "bid_from_open": self._unit_number(facts.get("bid_from_open")),
            "ask_from_open": self._unit_number(facts.get("ask_from_open")),
            "seconds_to_close": self._unit_number(facts.get("seconds_to_close")),
        }
        for key in _ANCHOR_FACT_KEYS:
            if key in facts and key not in payload:
                payload[key] = facts.get(key)
        atr = _atr_distance(facts)
        if atr is not None:
            payload["atr"] = atr
        # One ask per bar shape. A new high or low is a new state.
        # The live bid, ask, and seconds stay on the card for the unit ask.
        key = (
            "projected_move",
            str(facts.get("symbol") or ""),
            str(timeframe),
            str(bar_iso or ""),
            payload["open"],
            payload["high"],
            payload["low"],
        )
        return self._hop_score(
            "projected_move",
            "The score you return is the projected move of this forming bar, "
            "a price distance from the open, before the close prints. "
            "The side is chosen later. A long limit is the open minus that distance. "
            "A short limit is the open plus that distance. "
            "An empty score leaves the move unset. Do not name the side. Do not send.",
            payload,
            cache_key=key,
        )

    def _attach_forming_move(self, facts: dict, spec, symbol, ivl, now, bars=None, times=None) -> None:
        """Live forming facts, then the projected move for that price state."""

        seconds = facts.get("seconds_from_clock")
        fresh = (
            isinstance(seconds, (int, float))
            and not isinstance(seconds, bool)
            and seconds > 0
        )
        replaced = False
        if fresh:
            forming = {
                "open": facts.get("open"),
                "high": facts.get("high"),
                "low": facts.get("low"),
                "last": facts.get("close"),
                "seconds_to_close": seconds,
            }
        else:
            forming = self._read_forming_bar(
                symbol, getattr(spec, "timeframe", None), ivl, now,
            )
            if forming:
                replaced = True
                for name in ("open", "high", "low"):
                    if forming.get(name) is not None:
                        facts[name] = forming[name]
                if forming.get("last") is not None:
                    facts["close"] = forming["last"]
                high = self._unit_number(facts.get("high"))
                low = self._unit_number(facts.get("low"))
                close = self._unit_number(facts.get("close"))
                if close is not None and low is not None:
                    facts["range_to_low"] = close - low
                else:
                    facts.pop("range_to_low", None)
                if high is not None and close is not None:
                    facts["range_to_high"] = high - close
                else:
                    facts.pop("range_to_high", None)
                anchor = self._unit_number(forming.get("open"))
                bid = self._unit_number(facts.get("bid"))
                ask = self._unit_number(facts.get("ask"))
                if anchor is not None and bid is not None:
                    facts["bid_from_open"] = bid - anchor
                else:
                    facts.pop("bid_from_open", None)
                if anchor is not None and ask is not None:
                    facts["ask_from_open"] = ask - anchor
                else:
                    facts.pop("ask_from_open", None)
        if forming:
            facts["forming_open"] = forming.get("open")
            facts["forming_high"] = forming.get("high")
            facts["forming_low"] = forming.get("low")
            facts["seconds_to_close"] = forming.get("seconds_to_close")
        elif isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            facts["seconds_to_close"] = seconds
        self._stamp_price_structure(facts, bars, times, ivl, forming=replaced)
        _bind_entry(facts)
        if str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS:
            return
        move = self._projected_move(facts, getattr(spec, "timeframe", None))
        anchor = self._unit_number(facts.get("forming_open"))
        if anchor is None:
            anchor = self._unit_number(facts.get("open"))
        if move is None:
            facts.pop("projected_move", None)
            facts.pop("long_limit", None)
            facts.pop("short_limit", None)
            return
        facts["projected_move"] = move
        long_level = _limit_level(anchor, move, 1)
        short_level = _limit_level(anchor, move, -1)
        if long_level is None:
            facts.pop("long_limit", None)
        else:
            facts["long_limit"] = long_level
        if short_level is None:
            facts.pop("short_limit", None)
        else:
            facts["short_limit"] = short_level

    def _price_span(self, bars) -> tuple[float | None, float | None]:
        highs: list[float] = []
        lows: list[float] = []
        for bar in bars or ():
            high = self._bar_number(bar, "h", "high")
            low = self._bar_number(bar, "l", "low")
            if high is not None:
                highs.append(high)
            if low is not None:
                lows.append(low)
        return (max(highs) if highs else None, min(lows) if lows else None)

    def _stamp_price_structure(self, facts: dict, bars, times, ivl, *, forming: bool) -> None:
        """Previous, session, and day extremes already in this series.

        A missing bar or a missing clock stays absent. This does not name a side.
        """

        series = list(bars or ())
        stamps = list(times or ())
        aligned = bool(series) and len(series) == len(stamps)
        previous = series if forming else series[:-1]
        if previous:
            facts["prev_high"] = self._bar_number(previous[-1], "h", "high")
            facts["prev_low"] = self._bar_number(previous[-1], "l", "low")
            if facts.get("prev_high") is None:
                facts.pop("prev_high", None)
            if facts.get("prev_low") is None:
                facts.pop("prev_low", None)
            extreme_high, extreme_low = self._price_span(previous)
            if extreme_high is None:
                facts.pop("prev_extreme_high", None)
            else:
                facts["prev_extreme_high"] = extreme_high
            if extreme_low is None:
                facts.pop("prev_extreme_low", None)
            else:
                facts["prev_extreme_low"] = extreme_low
        else:
            for name in ("prev_high", "prev_low", "prev_extreme_high", "prev_extreme_low"):
                facts.pop(name, None)

        current_time = None
        rows: list[tuple[datetime | None, float | None, float | None]] = []
        if aligned:
            history = stamps if forming else stamps[:-1]
            older = series if forming else series[:-1]
            if len(history) == len(older):
                for when, bar in zip(history, older):
                    rows.append((
                        _aware_time(when),
                        self._bar_number(bar, "h", "high"),
                        self._bar_number(bar, "l", "low"),
                    ))
            if forming and stamps and ivl:
                opened = _aware_time(stamps[-1])
                if opened is not None:
                    current_time = opened + timedelta(minutes=int(ivl))
            elif stamps and not forming:
                current_time = _aware_time(stamps[-1])
        if current_time is None:
            for name in ("session_high", "session_low", "day_high", "day_low"):
                facts.pop(name, None)
            return
        rows.append((
            current_time,
            self._unit_number(facts.get("high")),
            self._unit_number(facts.get("low")),
        ))
        if ivl:
            session_high, session_low = _session_extremes(rows, int(ivl))
            if session_high is None:
                facts.pop("session_high", None)
            else:
                facts["session_high"] = session_high
            if session_low is None:
                facts.pop("session_low", None)
            else:
                facts["session_low"] = session_low
        else:
            facts.pop("session_high", None)
            facts.pop("session_low", None)
        try:
            day = decision_day_of(current_time)
        except Exception:
            day = None
        if day:
            day_high, day_low = _day_extremes(rows, day)
            if day_high is None:
                facts.pop("day_high", None)
            else:
                facts["day_high"] = day_high
            if day_low is None:
                facts.pop("day_low", None)
            else:
                facts["day_low"] = day_low
        else:
            facts.pop("day_high", None)
            facts.pop("day_low", None)

    @staticmethod
    def _bar_on_card(facts: Mapping[str, Any] | None, asked: Any) -> str | None:
        """The bar the last_bar ask returned.

        bid_from_open and ask_from_open stay on the card for that ask.
        An empty answer, a tie, and use_previous_close stay as returned.
        The quote having left the open does not rename them.
        """

        legal = (
            "closed_bar_reaches",
            "use_previous_close",
            "closed_bar_does_not_reach",
        )
        if not isinstance(facts, Mapping):
            return None
        return asked if asked in legal else None

    def _closed_bar_card(
        self, spec, symbol, bars, times, now, ivl, generator_error=None, *, bind_choice: bool = False,
        sleeve_fired: bool | None = None,
    ):
        """Prices on this close. A missing field stays absent. This does not pick a side.

        sleeve_fired is present only when the caller already knows whether the
        generator returned an intent. An unknown result stays off the card.
        """

        facts: dict[str, Any] = {
            "symbol": symbol,
            "sleeve": getattr(spec, "tag", None),
            "generator_error": generator_error,
            "decision_bar_iso": times[-1].isoformat() if times else None,
            "cluster": getattr(spec, "cluster", None),
        }
        if sleeve_fired is not None:
            facts["sleeve_fired"] = bool(sleeve_fired)
        try:
            if bars:
                bar = bars[-1]
                close = self._bar_number(bar, "c", "close")
                high = self._bar_number(bar, "h", "high")
                low = self._bar_number(bar, "l", "low")
                facts["open"] = self._bar_number(bar, "o", "open")
                facts["high"] = high
                facts["low"] = low
                facts["close"] = close
                if close is not None and low is not None:
                    facts["range_to_low"] = close - low
                if high is not None and close is not None:
                    facts["range_to_high"] = high - close
                facts["direction"] = self._direction_if_any(spec, bar)
        except Exception as exc:
            facts["price_error"] = type(exc).__name__
        bid, ask = self._unit_quote(symbol)
        facts["bid"] = bid
        facts["ask"] = ask
        # The live quote against the open is the move before this close prints.
        # A missing price stays absent. This difference does not pick a side
        # and does not fill a missing quote with 0.00.
        open_px = self._unit_number(facts.get("open"))
        if open_px is not None and bid is not None:
            facts["bid_from_open"] = bid - open_px
        if open_px is not None and ask is not None:
            facts["ask_from_open"] = ask - open_px
        if bind_choice:
            card_key = (
                str(getattr(spec, "tag", "") or ""),
                str(symbol),
                str(facts.get("decision_bar_iso") or ""),
            )
            overlay = getattr(_SLOT_LAST_BAR, "cards", None)
            remembered = None
            if isinstance(overlay, dict) and card_key in overlay:
                remembered = overlay[card_key]
            else:
                memo = getattr(self, "_last_bar_cards", None)
                if isinstance(memo, dict):
                    remembered = memo.get(card_key)
            named = self._bar_on_card(facts, remembered)
            if named:
                facts["last_bar_choice"] = named
        try:
            from .launcher_facts import launcher_facts

            facts.update(launcher_facts())
        except Exception:
            pass
        if ivl and times and now is not None:
            try:
                bar_close = times[-1] + timedelta(minutes=ivl)
                facts["seconds_from_clock"] = (bar_close - now).total_seconds()
            except Exception:
                facts["seconds_from_clock"] = None
        self._attach_forming_move(facts, spec, symbol, ivl, now, bars, times)
        return facts

    def _remember_last_bar(self, sleeve, symbol, bar_iso, choice) -> None:
        key = (str(sleeve or ""), str(symbol or ""), str(bar_iso or ""))
        overlay = getattr(_SLOT_LAST_BAR, "cards", None)
        if isinstance(overlay, dict):
            overlay[key] = choice
            return
        memo = getattr(self, "_last_bar_cards", None)
        if not isinstance(memo, dict):
            memo = {}
            self._last_bar_cards = memo
        memo[key] = choice

    def _limit_unit_from_closed_bar(
        self, spec, symbol, bars, times, day, generator_error, now=None, ivl=None,
    ):
        """Ask the unit question, then build a limit intent from the returned side.

        The card carries the projected move, a price distance from the open.
        The side is chosen later. A long limit is the open minus that distance.
        A short limit is the open plus that distance. Stop and target are
        scores between this card's anchors, measured from that limit. An empty
        move, an empty side, or an empty stop leaves the unit unset. This does
        not name the side and does not restore the close as the price.
        """

        from .admission import TradeIntent

        facts = self._closed_bar_card(
            spec, symbol, bars, times, now, ivl, generator_error, bind_choice=True,
            sleeve_fired=False,
        )
        winner = self._spot_choice(
            "unit",
            spot=f"{getattr(spec, 'tag', '')}|{symbol}|{facts.get('decision_bar_iso')}",
            facts=facts,
        )
        if winner == "unit_long":
            direction = 1
        elif winner == "unit_short":
            direction = -1
        else:
            return None
        anchor = self._unit_number(facts.get("forming_open"))
        if anchor is None:
            anchor = self._unit_number(facts.get("open"))
        move = self._unit_number(facts.get("projected_move"))
        level = _limit_level(anchor, move, direction)
        if level is None:
            return None
        card = dict(facts)
        card["entry"] = level
        spot = (
            str(getattr(spec, "tag", "") or ""),
            str(symbol),
            str(facts.get("decision_bar_iso") or ""),
            level,
        )
        stop_dist = self._hop_score(
            "unit_stop_dist",
            "The score you return is the stop distance from the entry, in price units. "
            "It may sit between the anchors. "
            "An empty score leaves the stop unset. Do not name the side. Do not send.",
            card,
            cache_key=("unit_stop_dist",) + spot,
        )
        target = self._hop_score(
            "unit_target_dist",
            "The score you return is the target distance from the entry, in price units. "
            "It may sit between the anchors. "
            "An empty score leaves the target unset. Do not name the side. Do not send.",
            card,
            cache_key=("unit_target_dist",) + spot,
        )
        if stop_dist is None or not (stop_dist > 0):
            return None
        target_dist = target if target is not None and target > 0 else None
        try:
            return TradeIntent(
                sleeve=spec.tag,
                symbol=symbol,
                direction=direction,
                decision_day=day,
                stop_dist=float(stop_dist),
                target_dist=None if target_dist is None else float(target_dist),
                entry_price=float(level),
                unit_choice=winner,
            )
        except Exception:
            return None

    def _slot_generation(self) -> dict:
        """Counters for one slot. The join adds them to the cycle."""

        generation = {
            "profile_supported_symbol_slot_count": 0,
            "broker_unsupported_symbol_slot_count": 0,
            "broker_unsupported_skips": [],
            "insufficient_bars_symbol_slot_count": 0,
            "insufficient_bars_skips": [],
            "stale_decision_bar_symbol_slot_count": 0,
            "stale_decision_bar_skips": [],
            "future_decision_bar_symbol_slot_count": 0,
            "generator_evaluated_symbol_slot_count": 0,
        }
        if self._event_clock_shadow is not None:
            generation["event_clock_shadow"] = []
        return generation

    def _merge_count_map(self, base: dict, incoming: dict) -> None:
        for key, value in incoming.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                base[key] = int(base.get(key) or 0) + value
            elif isinstance(value, list):
                dest = base.setdefault(key, [])
                for item in value:
                    if key == "sleeves":
                        if item not in dest:
                            dest.append(item)
                    elif key == "errors":
                        if item not in dest and len(dest) < 8:
                            dest.append(item)
                    else:
                        dest.append(item)
            elif isinstance(value, dict):
                nested = base.setdefault(key, {})
                if isinstance(nested, dict):
                    self._merge_count_map(nested, value)

    def _merge_slot_generation(self, generation: dict, part: dict) -> None:
        for key in (
            "profile_supported_symbol_slot_count",
            "broker_unsupported_symbol_slot_count",
            "insufficient_bars_symbol_slot_count",
            "stale_decision_bar_symbol_slot_count",
            "future_decision_bar_symbol_slot_count",
            "generator_evaluated_symbol_slot_count",
        ):
            generation[key] = int(generation.get(key) or 0) + int(part.get(key) or 0)
        for key in (
            "broker_unsupported_skips",
            "insufficient_bars_skips",
            "stale_decision_bar_skips",
        ):
            bucket = generation.get(key)
            if not isinstance(bucket, list):
                continue
            for row in part.get(key) or []:
                if len(bucket) >= _SKIP_SAMPLE_CAP:
                    break
                bucket.append(row)
        shadow = part.get("event_clock_shadow")
        if shadow and isinstance(generation.get("event_clock_shadow"), list):
            generation["event_clock_shadow"].extend(shadow)
        for key, value in part.items():
            if not isinstance(value, dict):
                continue
            dest = generation.setdefault(key, {})
            if isinstance(dest, dict):
                self._merge_count_map(dest, value)

    def _store_last_bar_cards(self, updates: dict) -> None:
        if not updates:
            return
        memo = getattr(self, "_last_bar_cards", None)
        if not isinstance(memo, dict):
            memo = {}
            self._last_bar_cards = memo
        memo.update(updates)

    def _raw_closed_bars(self, bar_cache, key, fetch):
        """One raw fetch for this key. The caller slices the lists it is given."""

        lock = self._bar_series_lock
        inflight = self._bar_inflight
        with lock:
            found = bar_cache.get(key)
            if found is not None:
                return list(found[0]), list(found[1])
            gate = inflight.get(key)
            if gate is None:
                gate = _SlotFlight()
                inflight[key] = gate
                owner = True
            else:
                owner = False
        if not owner:
            gate.event.wait()
            if gate.error is not None:
                raise gate.error
            found = gate.value or ([], [])
            return list(found[0]), list(found[1])
        stored = None
        error = None
        try:
            fetched = fetch()
            if not fetched:
                fetched = ([], [])
            stored = (list(fetched[0]), list(fetched[1]))
            with lock:
                bar_cache[key] = stored
        except Exception as exc:
            error = exc
        finally:
            gate.value = stored
            gate.error = error
            gate.event.set()
            with lock:
                if inflight.get(key) is gate:
                    inflight.pop(key, None)
        if error is not None:
            raise error
        return list(stored[0]), list(stored[1])

    def _generate_one_slot(
        self,
        spec,
        symbol: str,
        *,
        now,
        bar_cache,
        generation,
        generation_skips,
        generation_terminals,
        intents,
        meta,
        unsupported_seen,
    ) -> None:
        """One sleeve and symbol, in chain order. A raise leaves this slot only."""

        def terminal(spec, symbol: str, status: str, **observed) -> None:
            generation_terminals.append({
                "sleeve": spec.tag,
                "symbol": symbol,
                "timeframe": spec.timeframe,
                "terminal_status": status,
                **observed,
            })

        primary_count = max(int(self._bar_count), int(getattr(spec, "bar_count", 0) or 0))
        supports = getattr(self._broker_symbol, "supports", None)
        if callable(supports) and not supports(symbol):
            withhold_spec = str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS
            if not withhold_spec:
                withhold_spec = self._spot_choice(
                    "instrument_spec",
                    spot=f"{spec.tag}|{symbol}",
                    facts={
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "profile_supports_symbol": False,
                    },
                ) == "instrument_spec_missing"
            if withhold_spec:
                skip = {
                    "symbol": symbol,
                    "sleeve": spec.tag,
                    "cluster": spec.cluster,
                    "timeframe": spec.timeframe,
                    "reason": "profile_missing_instrument_config",
                }
                generation["broker_unsupported_symbol_slot_count"] += 1
                unsupported_seen.add(symbol)
                skips = generation["broker_unsupported_skips"]
                if isinstance(skips, list) and len(skips) < 64:
                    skips.append(dict(skip))
                generation_skips.append(skip)
                terminal(spec, symbol, "profile_unsupported")
                return
        generation["profile_supported_symbol_slot_count"] += 1
        broker_sym = self._broker_symbol(symbol)   # canonical -> broker for ALL fetches
        on_challenge = str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS
        named = _named_bar_count(self._warmup_required(spec)) if on_challenge else None
        fetch_count = primary_count
        if named is not None and named > fetch_count:
            fetch_count = named
        key = (symbol, spec.timeframe, fetch_count)
        # fetch under the BROKER name; meta + intent.symbol stay canonical for placement
        #
        # `now`/`interval_minutes` make `candles_to_bars` keep a last candle it
        # can PROVE is closed (`time + interval <= now`). H4 always passes both
        # so a session-close last candle (FRA40 Friday 17:00, no next forming
        # bar) is not discarded. Other TFs still pass them ONLY under the
        # pre-gap flag. Applied to the PRIMARY decision fetch only -- the aux
        # feed below is an M1 volume-profile window, not a decision bar.
        # H4 always keeps a last candle whose interval has elapsed
        # (FRA40 Friday 17:00: session close has no next forming bar).
        # D1 stays on the default drop unless --recover-pre-gap-bar
        # (D1 pre-gap EV is worse; do not flip that flag globally).
        # The cache keeps this raw series. The slot slices its own copy.
        interval_minutes = _TF_MINUTES.get(spec.timeframe)
        keep_last_closed = bool(self._recover_pre_gap_bar) or spec.timeframe in (
            16388, "H4", TF_H4,
        )
        if keep_last_closed:
            bars, times = self._raw_closed_bars(
                bar_cache,
                key,
                lambda mt5=self._mt5, broker=broker_sym, tf=spec.timeframe, count=fetch_count, clock=now, minutes=interval_minutes, ns=getattr(self, "_namespace", None): get_closed_bars(
                    mt5, broker, tf, count,
                    now=clock, interval_minutes=minutes, namespace=ns,
                ),
            )
        else:
            bars, times = self._raw_closed_bars(
                bar_cache,
                key,
                lambda mt5=self._mt5, broker=broker_sym, tf=spec.timeframe, count=fetch_count, ns=getattr(self, "_namespace", None): get_closed_bars(
                    mt5, broker, tf, count, namespace=ns,
                ),
            )
        if not bars:
            # No series to index. This keeps the cycle alive. On Challenge
            # the unit Choice is asked before this slot returns.
            try:
                generation["insufficient_bars_symbol_slot_count"] += 1
                _sample_skip(generation["insufficient_bars_skips"], {
                    "symbol": symbol,
                    "sleeve": spec.tag,
                    "cluster": spec.cluster,
                    "reason": "insufficient_bars",
                    "bars_returned": 0,
                    "bars_requested": primary_count,
                    "warmup_required": self._warmup_required(spec),
                })
            except Exception:      # noqa: BLE001 — telemetry never gates
                pass
            terminal(
                spec, symbol, "bars_unavailable",
                observed_bar_count=0,
                decision_bar_iso=times[-1].isoformat() if times else None,
            )
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                self._limit_unit_from_closed_bar(
                    spec, symbol, bars, times, None, None,
                    now=now, ivl=_TF_MINUTES.get(spec.timeframe),
                )
                terminal(
                    spec, symbol, "unit_unset",
                    observed_bar_count=0,
                    decision_bar_iso=times[-1].isoformat() if times else None,
                )
            return
        series_bar = times[-1].isoformat() if times else ""
        if not enough(
            bars,
            spec.cluster,
            symbol,
            spec.timeframe,
            series_bar,
            needed=named if on_challenge else None,
        ):
            # A friend book still uses its cluster map. On Challenge the
            # series is short only when a returned warmup count is unmet
            # and that ask's unique answer says so. An empty answer does
            # not withhold the slot.
            withhold_feed = not on_challenge
            if not withhold_feed:
                withhold_feed = self._spot_choice(
                    "feed_lookback",
                    spot=f"{spec.tag}|{symbol}|{len(bars)}|{fetch_count}",
                    facts={
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "bars_returned": len(bars),
                        "bars_requested": fetch_count,
                        "warmup_required": named,
                    },
                ) == "feed_short"
            if withhold_feed:
                try:
                    generation["insufficient_bars_symbol_slot_count"] += 1
                    _sample_skip(generation["insufficient_bars_skips"], {
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "cluster": spec.cluster,
                        "reason": "insufficient_bars",
                        "bars_returned": len(bars),
                        "bars_requested": fetch_count,
                        "warmup_required": named if on_challenge else self._warmup_required(spec),
                    })
                except Exception:      # noqa: BLE001 — telemetry never gates
                    pass
                terminal(
                    spec,
                    symbol,
                    "insufficient_warmup",
                    observed_bar_count=len(bars),
                    decision_bar_iso=times[-1].isoformat() if times else None,
                )
                return
        # DECISION-BAR RECENCY (chronological guard): the cycle is triggered by ONE reference
        # symbol's bar close, but each sleeve evaluates its OWN symbol's latest closed bar. If that
        # bar is grossly stale — the symbol's market is closed/holiday, its bar did not advance at
        # this trigger, or this is a cold post-restart read — acting on it is the ref-vs-sleeve
        # chronological hazard (e.g. trading a frozen index bar). Skip a bar whose close is older
        # than ~2 intervals. Fail-open if the interval is unknown.
        ivl = _TF_MINUTES.get(spec.timeframe)
        repaired_offset = None
        slot_observed = {
            "decision_bar_iso": times[-1].isoformat() if times else None,
        }
        if ivl and times:
            try:
                times, repaired_offset = self._normalize_future_bar_times(
                    times,
                    now=now,
                    interval_minutes=ivl,
                    cache_key=key,
                )
                bar_close = times[-1] + timedelta(minutes=ivl)
                slot_observed["decision_bar_iso"] = times[-1].isoformat()
                if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                    # The closed bar is named by the last_bar ask. The old
                    # 30-second and two-interval comparisons do not choose here.
                    _card = self._closed_bar_card(
                        spec, symbol, bars, times, now, ivl,
                    )
                    _lb = self._spot_choice(
                        "last_bar",
                        spot=f"{spec.tag}|{symbol}|{slot_observed['decision_bar_iso']}",
                        facts=_card,
                    )
                    # Empty stays empty and does not slice. use_previous_close
                    # slices when that ask returned it.
                    _named = self._bar_on_card(_card, _lb)
                    slot_observed["last_bar_choice"] = _named
                    self._remember_last_bar(
                        spec.tag, symbol, slot_observed["decision_bar_iso"], _named,
                    )
                    if _named == "use_previous_close":
                        _prior_times = times[:-1]
                        _prior_bars = bars[:-1]
                        if _prior_times and _prior_bars:
                            times = _prior_times
                            bars = _prior_bars
                            bar_close = times[-1] + timedelta(minutes=ivl)
                            slot_observed["decision_bar_iso"] = times[-1].isoformat()
                            self._remember_last_bar(
                                spec.tag, symbol, slot_observed["decision_bar_iso"], _named,
                            )
                    elif _named == "closed_bar_does_not_reach":
                        self._limit_unit_from_closed_bar(
                            spec,
                            symbol,
                            bars,
                            times,
                            decision_day_of(times[-1]) if times else None,
                            None,
                            now=now,
                            ivl=ivl,
                        )
                        terminal(spec, symbol, "last_bar_withholds", **slot_observed)
                        return
                else:
                    # Other books keep the clock gate. Challenge does not.
                    if (bar_close - now).total_seconds() > 30.0 and len(times) >= 2 and len(bars) >= 2:
                        _prev_close = times[-2] + timedelta(minutes=ivl)
                        if (_prev_close - now).total_seconds() <= 30.0:
                            times = times[:-1]
                            bars = bars[:-1]
                            bar_close = _prev_close
                            slot_observed["decision_bar_iso"] = times[-1].isoformat()
                    if (bar_close - now).total_seconds() > 30.0:
                        generation_skips.append({
                            "symbol": symbol,
                            "sleeve": spec.tag,
                            "reason": "future_decision_bar_time",
                            "decision_bar_iso": times[-1].isoformat(),
                            "bar_close_utc": bar_close.isoformat(),
                            "now_utc": now.isoformat(),
                        })
                        try:
                            generation["future_decision_bar_symbol_slot_count"] += 1
                        except Exception:  # noqa: BLE001 — telemetry never gates
                            pass
                        terminal(spec, symbol, "future_decision_bar", **slot_observed)
                        return
                    if (now - bar_close).total_seconds() > 2 * ivl * 60:
                        age_minutes = (now - bar_close).total_seconds() / 60.0
                        try:
                            generation["stale_decision_bar_symbol_slot_count"] += 1
                            _sample_skip(generation["stale_decision_bar_skips"], {
                                "symbol": symbol,
                                "sleeve": spec.tag,
                                "reason": "stale_decision_bar",
                                "decision_bar_iso": times[-1].isoformat(),
                                "bar_close_utc": bar_close.isoformat(),
                                "now_utc": now.isoformat(),
                                "age_minutes": round(age_minutes, 1),
                                "stale_limit_minutes": 2 * ivl,
                            })
                        except Exception:  # noqa: BLE001 — telemetry never gates
                            pass
                        terminal(spec, symbol, "stale_decision_bar", **slot_observed)
                        return
            except Exception:
                pass
        # Q2 SHADOW ONLY. times[-1] is the decision bar OPEN. The observer
        # derives the exact H4 close, resolves broker time, and latches retries.
        if self._event_clock_shadow is not None and spec.timeframe == TF_H4:
            try:
                event_row = self._event_clock_shadow.observe(
                    decision_bar_iso=times[-1],
                    timeframe=spec.timeframe,
                    observed_at_utc=now,
                )
            except Exception as exc:
                event_row = {
                    "schema": "gtos.q2_exact_h4_event_shadow.v1",
                    "classification_status": "observer_error_fail_closed",
                    "admission_effect": False,
                    "decision_bar_iso": times[-1].isoformat(),
                    "decision_bar_semantics": "bar_open_utc",
                    "timeframe": spec.timeframe,
                    "shadow_would_reject": None,
                    "reason": "event_clock_shadow_observer_error",
                    "error": repr(exc),
                    "observed_at_utc": now.isoformat(),
                }
            event_row = dict(event_row)
            event_row.update({"symbol": symbol, "sleeve": spec.tag})
            generation["event_clock_shadow"].append(event_row)
        # optional SECONDARY feed (e.g. M1 for the vp volume profile); cached per (symbol, aux_tf)
        aux_bars, aux_times = None, None
        if spec.aux_timeframe and spec.aux_count > 0:
            akey = (symbol, spec.aux_timeframe, spec.aux_count)
            aux_bars, aux_times = self._raw_closed_bars(
                bar_cache,
                akey,
                lambda mt5=self._mt5, broker=broker_sym, tf=spec.aux_timeframe, count=spec.aux_count: get_closed_bars(
                    mt5, broker, tf, count,
                ),
            )
            if aux_times and repaired_offset:
                aux_times = [
                    (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
                    - timedelta(seconds=repaired_offset)
                    for t in aux_times
                ]
        day = decision_day_of(times[-1])
        try:
            generation["generator_evaluated_symbol_slot_count"] += 1
        except Exception:      # noqa: BLE001 — telemetry never gates
            pass
        generator_error = None
        from_closed_bar = False
        peer_panel = None
        try:
            # bar_time = the decision bar's UTC datetime; bar_times = the full aligned series
            # (JPY session logic); aux_bars/aux_times = the secondary feed (vp M1). Each
            # generator reads only what it needs (the rest tolerate the extra kwargs via **_).
            # CONTRACT leftover A2 (Fable 5.1): pass peer_panel so dsp/xa direction_resolver
            # can return None on 0. skip_on_resolver_disagree stays unarmed.
            peer_panel = None
            if spec.tag in DISPLACEMENT_BUILT or str(spec.tag).startswith(("dsp_", "xa_")):
                try:
                    peer_panel = self._f5_peer_panel(bar_cache, symbol)
                except Exception:
                    peer_panel = None
            intent = spec.generator(symbol, bars, day, bar_time=times[-1], bar_times=times,
                                    aux_bars=aux_bars, aux_times=aux_times,
                                    runtime_now=now, peer_panel=peer_panel)
        except Exception as exc:
            generator_error = type(exc).__name__
            intent = None
        if intent is None and str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
            # The sleeve's None or exception is a fact. Ask before this slot returns.
            intent = self._limit_unit_from_closed_bar(
                spec, symbol, bars, times, day, generator_error,
                now=now, ivl=ivl,
            )
            from_closed_bar = intent is not None
        if intent is None:
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                status = "unit_unset"
            else:
                status = "generator_exception" if generator_error else "no_candidate"
            terminal(
                spec,
                symbol,
                status,
                generator_error=generator_error,
                **slot_observed,
            )
            return
        # B3: scale stop/target from the per-class table. Filled tickets keep broker SL/TP.
        # A unit built from the closed bar keeps that bar's range.
        try:
            if (
                not from_closed_bar
                and (
                    spec.tag in DISPLACEMENT_BUILT
                    or str(spec.tag).startswith(("dsp_", "xa_"))
                )
            ):
                intent = apply_class_geometry(intent)
        except Exception:
            pass
        # THE SPREAD-GEOMETRY FLOOR (default-OFF; see __init__). Applied here, after
        # the generator has proposed a stop and before the intent exists as far as
        # anything downstream is concerned -- which is the whole point: an intent
        # refused here never reaches `_running_conviction_override`, so it cannot
        # raise the day's Kelly-lite multiplier for the sleeves that do place.
        refusal = self._spread_geometry_refusal(intent, spec, symbol, generation)
        if refusal is not None:
            generation_skips.append(refusal)
            terminal(
                spec,
                symbol,
                "spread_floor_refused",
                direction=getattr(intent, "direction", None),
                **slot_observed,
            )
            return
        # THE RATIFIED ENTRY-HOUR CONVENTION (default-OFF; see __init__). Applied
        # after the floor and immediately before the intent exists downstream, so a
        # deferred intent does not enter the day's conviction count AT HOUR 00 -- it
        # enters when it actually fires, which is the honest count. `now` is the
        # CYCLE's instant, passed in, never a fresh wall-clock read inside the loop.
        deferral = self._entry_hour_deferral(intent, spec, symbol, times[-1], now,
                                             generation)
        if deferral is not None:
            generation_skips.append(deferral)
            terminal(
                spec,
                symbol,
                "entry_hour_deferred",
                direction=getattr(intent, "direction", None),
                **slot_observed,
            )
            return
        intents.append(intent)
        meta_row = {"symbol": symbol, "timeframe": spec.timeframe, "tag": spec.tag,
                    "last_close": bars[-1].c, "decision_day": day,
                    # the decision bar's UTC timestamp — the idempotency key granularity so a
                    # continuously-ticking launcher places each (sleeve, symbol, bar) ONCE.
                    "decision_bar_iso": times[-1].isoformat()}
        try:
            if peer_panel is not None:
                from .xasset_direction import direction_resolver
                meta_row["xasset_d"] = direction_resolver(
                    spec.tag, {"symbol": symbol}, peer_panel)
                meta_row["peer_panel_aligned_move"] = peer_panel.get("aligned_move")
        except Exception:
            pass
        try:
            from .minimal_size import (
                f5_calendar_prime_window_reason,
                f5_load_live_calendar_events,
            )
            if str(self._namespace) == "operator":
                self._f5_calendar_events = f5_load_live_calendar_events(
                    getattr(self, "_repo_root", None)
                )
            events = getattr(self, "_f5_calendar_events", None)
            prime = f5_calendar_prime_window_reason(symbol, now, events)
            if prime:
                meta_row["calendar_amplifier"] = prime
        except Exception:
            pass
        meta.append(meta_row)
        terminal(
            spec,
            symbol,
            "candidate_emitted",
            direction=getattr(intent, "direction", None),
            **slot_observed,
        )

    def _generate_intents(self, tags=None, now: Optional[datetime] = None) -> tuple[list, list[dict]]:
        now = now or datetime.now(timezone.utc)
        intents: list = []
        meta: list[dict] = []
        generation_skips: list[dict] = []
        generation_terminals: list[dict] = []
        self._last_generation_telemetry = {}
        self._last_generation_skips = generation_skips
        self._last_generation_terminals = generation_terminals
        specs = effective_generation_specs(
            self.config, tags, namespace=getattr(self, "_namespace", None),
        )
        # cache bars per (symbol, timeframe, count) so long-warmup candidates cannot be starved by a
        # shorter prior fetch on the same symbol/timeframe.
        bar_cache: dict[tuple[str, int, int], tuple[list, list]] = {}
        self._unit_quotes = {}
        self._forming_reads = {}
        generation = {
            "active_spec_count": len(specs),
            "active_symbol_slot_count": sum(len(spec.on_surface) for spec in specs),
            "profile_supported_symbol_slot_count": 0,
            "broker_unsupported_symbol_slot_count": 0,
            "broker_unsupported_unique_symbols": [],
            "broker_unsupported_skips": [],
            # THE TWO SILENT DROPS, made countable 2026-08-12 (F5 funnel trace).
            #
            # Between `profile_supported_symbol_slot_count` and the intent count there were two
            # bare `continue`s -- insufficient bars (:601) and a stale decision bar (:633) -- that
            # left NO counter and NO skip row. Both are FEED conditions, and they were
            # indistinguishable in every log from "the generator looked and there was no setup",
            # which is a different thing and the overwhelmingly common one. A sleeve starved of
            # bars, or one whose symbol stopped printing, therefore read exactly like a quiet
            # market for as long as it lasted.
            #
            # Counted here rather than pushed into `generation_skips` because that list is
            # unbounded and per-slot: on a weekend EVERY slot is stale, which would write ~13k rows
            # a day to say "the market is shut". A count plus a bounded sample is the same shape
            # `broker_unsupported_*` above already uses, and it lands in the same record an
            # operator already reads (`bridge.broker_profile_generation` in the launcher jsonl).
            #
            # With `generator_evaluated_symbol_slot_count` the funnel now closes arithmetically:
            #   active_symbol_slot_count
            #     - broker_unsupported - insufficient_bars - stale_decision_bar - future_decision_bar
            #     = generator_evaluated
            # and `n_intents` is already recorded alongside. NOTHING here changes a decision: every
            # `continue` is unchanged and every counter update is exception-guarded so that a bug in
            # this telemetry can never let a slot through a gate it should have been stopped by.
            "insufficient_bars_symbol_slot_count": 0,
            "insufficient_bars_skips": [],
            "stale_decision_bar_symbol_slot_count": 0,
            "stale_decision_bar_skips": [],
            "future_decision_bar_symbol_slot_count": 0,
            "generator_evaluated_symbol_slot_count": 0,
        }
        # Bind this cycle's mutable objects immediately so an outer safe-noop cannot
        # accidentally report the previous cycle's denominator.
        self._last_generation_telemetry = generation

        if self._event_clock_shadow is not None:
            generation["event_clock_shadow"] = []
        unsupported_seen: set[str] = set()
        self._bar_inflight = {}
        slots = [(spec, symbol) for spec in specs for symbol in spec.on_surface]
        task_count = int(generation["active_symbol_slot_count"])
        if slots and task_count != len(slots):
            task_count = len(slots)

        def _run_slot(spec, symbol):
            slot_generation = self._slot_generation()
            slot_skips: list[dict] = []
            slot_terminals: list[dict] = []
            slot_intents: list = []
            slot_meta: list[dict] = []
            slot_unsupported: set[str] = set()
            _SLOT_LAST_BAR.cards = {}
            try:
                try:
                    self._generate_one_slot(
                        spec,
                        symbol,
                        now=now,
                        bar_cache=bar_cache,
                        generation=slot_generation,
                        generation_skips=slot_skips,
                        generation_terminals=slot_terminals,
                        intents=slot_intents,
                        meta=slot_meta,
                        unsupported_seen=slot_unsupported,
                    )
                except Exception as exc:
                    slot_intents = []
                    slot_meta = []
                    slot_generation = self._slot_generation()
                    slot_skips = []
                    slot_unsupported = set()
                    slot_terminals = [{
                        "sleeve": getattr(spec, "tag", None),
                        "symbol": symbol,
                        "timeframe": getattr(spec, "timeframe", None),
                        "terminal_status": "slot_exception",
                        "error": type(exc).__name__,
                    }]
            finally:
                remembered = getattr(_SLOT_LAST_BAR, "cards", None)
                last_bar = dict(remembered) if isinstance(remembered, dict) else {}
                _SLOT_LAST_BAR.cards = None
            return {
                "intents": slot_intents,
                "meta": slot_meta,
                "skips": slot_skips,
                "terminals": slot_terminals,
                "generation": slot_generation,
                "unsupported": slot_unsupported,
                "last_bar": last_bar,
            }

        results = []
        if slots and task_count:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=task_count) as pool:
                futures = [
                    pool.submit(_run_slot, spec, symbol) for spec, symbol in slots
                ]
                for future, (spec, symbol) in zip(futures, slots):
                    try:
                        results.append(future.result())
                    except Exception as exc:
                        results.append({
                            "intents": [],
                            "meta": [],
                            "skips": [],
                            "terminals": [{
                                "sleeve": getattr(spec, "tag", None),
                                "symbol": symbol,
                                "timeframe": getattr(spec, "timeframe", None),
                                "terminal_status": "slot_exception",
                                "error": type(exc).__name__,
                            }],
                            "generation": self._slot_generation(),
                            "unsupported": set(),
                            "last_bar": {},
                        })
        for result in results:
            intents.extend(result["intents"])
            meta.extend(result["meta"])
            generation_skips.extend(result["skips"])
            generation_terminals.extend(result["terminals"])
            unsupported_seen.update(result["unsupported"])
            self._merge_slot_generation(generation, result["generation"])
            self._store_last_bar_cards(result["last_bar"])

        generation["broker_unsupported_unique_symbols"] = sorted(unsupported_seen)
        self._last_generation_telemetry = generation
        self._last_generation_skips = generation_skips
        self._last_generation_terminals = generation_terminals
        return intents, meta

    def _risk_unit_floor_after_admission(self, intents, meta, decision, now):
        """Attach Q1 observations only for units admitted on the original intents.

        Admission, selection, the running-conviction denominator, and every pre-existing
        generation refusal have already completed when this runs.  The method mutates only
        Q1 telemetry rows; it never replaces an intent.  The owner later performs shadow
        projection or the explicit apply-mode replacement after its pre-send refusal.
        """
        policy = self._risk_unit_floor_policy
        if not policy.enabled:
            return
        admitted: set[str] = set()
        for unit in getattr(decision, "would_units", []) or []:
            try:
                sized = bool(unit.get("sized"))
                risk = float(unit.get("risk_pct_per_trade", 0.0) or 0.0)
                members = unit.get("sleeve_members", []) or []
            except AttributeError:
                sized = bool(getattr(unit, "sized", False))
                risk = float(getattr(unit, "risk_pct_per_trade", 0.0) or 0.0)
                members = getattr(unit, "sleeve_members", ()) or ()
            if sized and risk > 0.0:
                admitted.update(str(member) for member in members)
        if not admitted:
            return
        intent_of = {
            (getattr(intent, "sleeve", None), getattr(intent, "symbol", None)): intent
            for intent in intents
        }
        generation = self._last_generation_telemetry
        bar_cache: dict[tuple, tuple[list, list]] = {}
        for row in meta:
            sleeve = row.get("tag")
            symbol = row.get("symbol")
            if sleeve not in admitted or policy.params_for(sleeve) is None:
                continue
            intent = intent_of.get((sleeve, symbol))
            if intent is None:
                continue
            try:
                decision_bar = datetime.fromisoformat(str(row.get("decision_bar_iso")))
            except (TypeError, ValueError):
                decision_bar = row.get("decision_bar_iso")
            observation = self._risk_unit_floor_proposal(
                intent,
                sleeve,
                row.get("timeframe"),
                symbol,
                self._broker_symbol(symbol),
                bar_cache,
                generation,
                decision_bar=decision_bar,
                now=now,
            )
            if observation is not None:
                row["risk_unit_floor"] = observation

    def _risk_unit_floor_proposal(self, intent, sleeve, timeframe, symbol, broker_sym,
                                  bar_cache, generation, *, decision_bar, now):
        """Compute one post-admission Q1 proposal at the DECISION cutoff.

        The returned object is telemetry, not a replacement intent. Any failure leaves the
        existing path untouched and is counted. In particular, the M15 instrument is cut at
        ``decision_bar + decision timeframe``; bars that arrived between that cutoff and a
        delayed evaluation/retry cannot move the proposed stop.
        """
        policy = self._risk_unit_floor_policy
        params = policy.params_for(sleeve)
        if params is None:
            return None
        counts = generation.setdefault("risk_unit_floor", {
            "mode": policy.mode,
            "evaluated": 0,
            "touched": 0,
            "fail_open": 0,
            "sleeves": [],
        })
        counts["evaluated"] += 1
        try:
            from .risk_unit_floor import (
                LOOKBACK_BARS,
                apply_floor,
                bar_range_median_at_cutoff,
                round_trip_cost_price,
            )

            interval = _TF_MINUTES.get(int(timeframe))
            if not interval:
                raise ValueError(f"unknown_decision_timeframe:{timeframe}")
            stamp = decision_bar
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            cutoff = stamp.astimezone(timezone.utc) + timedelta(minutes=interval)
            age_minutes = max(0.0, (now - cutoff).total_seconds() / 60.0)
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                requested_score = self._hop_score(
                    "m15_retry_bars",
                    "The score you return is how many M15 bars this retry reads "
                    "back to the decision cutoff. "
                    "An empty score leaves the window unset. Do not send.",
                    {
                        "symbol": symbol,
                        "sleeve": sleeve,
                        "age_minutes": age_minutes,
                        "decision_bar_iso": stamp.isoformat(),
                    },
                    cache_key=(
                        "m15_retry_bars",
                        str(symbol),
                        stamp.isoformat(),
                        age_minutes,
                    ),
                )
                requested = None
                if requested_score is not None and not isinstance(requested_score, bool):
                    try:
                        requested = int(requested_score)
                    except (TypeError, ValueError):
                        requested = None
                if requested is None or requested <= 0:
                    # An empty or non-positive score leaves this window unset.
                    # It does not raise and it does not plant a bar count.
                    counts["fail_open"] += 1
                    observation = {
                        "mode": policy.mode,
                        "sleeve": sleeve,
                        "symbol": symbol,
                        "applied": False,
                        "reason": "retry_bars_unset",
                    }
                    observations = generation.setdefault("risk_unit_floor_observations", [])
                    if len(observations) < 64:
                        observations.append(dict(observation))
                    return observation
            else:
                # Other books keep the window they already had.
                requested = LOOKBACK_BARS + int(age_minutes // 15) + 8
                if requested > 512:
                    raise ValueError(f"decision_cutoff_too_old_for_m15_window:{requested}")
                requested = max(LOOKBACK_BARS + 8, requested)
            key = ("risk_unit_floor", symbol, 15, requested)
            if key not in bar_cache:
                bar_cache[key] = get_closed_bars(
                    self._mt5,
                    broker_sym,
                    15,
                    requested,
                    now=now,
                    interval_minutes=15,
                    namespace=getattr(self, "_namespace", None),
                )
            m15_bars, m15_times = bar_cache[key]
            bar24, bar_detail = bar_range_median_at_cutoff(
                m15_bars,
                m15_times,
                decision_cutoff=cutoff,
            )
            try:
                tick = self._mt5.get_tick(broker_sym)
            except Exception:
                tick = None
            server = (
                self._broker_server()
                if callable(self._broker_server)
                else self._broker_server
            )
            round_trip, cost_detail = round_trip_cost_price(
                symbol,
                tick,
                server=server,
                namespace=self._namespace,
                broker_true_symbol=broker_sym,
            )
            _proposed, observation = apply_floor(
                intent,
                bar24=bar24,
                rt_cost_price=round_trip,
                params=params,
            )
            observation.update({
                "mode": policy.mode,
                "sleeve": sleeve,
                "symbol": symbol,
                "decision_bar_iso": stamp.isoformat(),
                "decision_cutoff_utc": cutoff.isoformat(),
                "bar_window": bar_detail,
                "round_trip_cost": {
                    key: value for key, value in cost_detail.items()
                    if key in (
                        "spread_price", "commission_price", "commission_kind", "reason"
                    )
                },
            })
            if not observation.get("applied"):
                counts["fail_open"] += 1
            elif observation.get("touched"):
                counts["touched"] += 1
                if sleeve not in counts["sleeves"]:
                    counts["sleeves"].append(sleeve)
            observations = generation.setdefault("risk_unit_floor_observations", [])
            if len(observations) < 64:
                observations.append(dict(observation))
            return observation
        except Exception as exc:  # noqa: BLE001 - Q1 cannot break the live cycle
            counts["fail_open"] += 1
            observation = {
                "mode": policy.mode,
                "sleeve": sleeve,
                "symbol": symbol,
                "applied": False,
                "reason": f"risk_unit_floor_error:{type(exc).__name__}:{exc}",
            }
            observations = generation.setdefault("risk_unit_floor_observations", [])
            if len(observations) < 64:
                observations.append(dict(observation))
            return observation

    def _spread_geometry_refusal(self, intent, spec, symbol, generation) -> Optional[dict]:
        """The generation-side spread-geometry floor for ONE intent. None => keep it.

        Returns a `generation_skips` row on refusal, so the decision is visible in the same
        place every other generation skip is rather than in a log line nobody greps.

        FAIL-CLOSED, INCLUDING ON THIS METHOD'S OWN BUGS. An exception here would otherwise
        propagate to `evaluate`'s catch-all and stand the whole book down for the tick, so
        it is caught -- and caught as a REFUSAL of this one intent, not as a pass. That
        matches the authoritative gate (`missing_current_quote_spread_or_sl_distance` is a
        refusal reason, not a warning), and it fails in the direction that costs one trade
        rather than the direction that takes the pathological one. The skip row names the
        exception so a persistent internal fault reads as a fault, not as a quiet sleeve.
        """
        if not self._spread_geometry_floor:
            return None
        try:
            from .spread_geometry import evaluate_intent, resolve_floor_limit
            limit = resolve_floor_limit(self.config, spec.tag, self._spread_geometry_floor)
            if limit is None:
                return None
            tick = None
            try:
                tick = self._mt5.get_tick(self._broker_symbol(symbol))
            except Exception:   # noqa: BLE001 -- an unreadable quote is a REFUSAL, below
                tick = None
            reason, obs = evaluate_intent(intent, tick, limit)
            counts = generation.setdefault("spread_geometry_floor", {
                "evaluated": 0, "refused": 0, "sleeves": []})
            counts["evaluated"] += 1
            spread_r_fact = obs.get("spread_r") if isinstance(obs, dict) else None
            floor_limit = obs.get("limit") if isinstance(obs, dict) else None
            if spread_r_fact is not None and floor_limit is not None:
                try:
                    above_floor = float(spread_r_fact) > float(floor_limit)
                except (TypeError, ValueError):
                    above_floor = False
                try:
                    from src.judgment.cost_choices import withholds
                    comparison_withholds = withholds(
                        "geometry_spread",
                        {
                            "symbol": symbol,
                            "sleeve": getattr(spec, "tag", None),
                            "spread_r": spread_r_fact,
                            "limit": floor_limit,
                            "spread_above_the_floor": above_floor,
                            "bid": obs.get("bid"),
                            "ask": obs.get("ask"),
                            "stop_dist": obs.get("stop_dist"),
                        },
                    )
                except Exception:
                    comparison_withholds = False
                if comparison_withholds:
                    if not (isinstance(reason, str) and reason.startswith("spread_geometry_floor:")):
                        reason = (
                            f"spread_geometry_floor:{float(spread_r_fact):.4f}>{float(floor_limit):.4f}"
                        )
                elif isinstance(reason, str) and reason.startswith("spread_geometry_floor:"):
                    reason = None
            if reason is None:
                return None
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                if self._spot_choice(
                    "spread_floor",
                    spot=f"{spec.tag}|{symbol}|{reason}",
                    facts={
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "floor_reason": str(reason),
                        "spread_r": spread_r_fact,
                        "limit": floor_limit,
                    },
                ) != "floor_refuses":
                    return None
            counts["refused"] += 1
            if spec.tag not in counts["sleeves"]:
                counts["sleeves"].append(spec.tag)
            return {"symbol": symbol, "sleeve": spec.tag, "cluster": spec.cluster,
                    "timeframe": spec.timeframe, "reason": reason,
                    "spread_geometry": {k: v for k, v in obs.items() if v is not None}}
        except Exception as exc:   # noqa: BLE001 -- never break the cycle; never fail open
            if str(getattr(self, "_namespace", "")) == "operator":
                return None
            return {"symbol": symbol, "sleeve": getattr(spec, "tag", None),
                    "reason": f"spread_geometry_floor_error:{type(exc).__name__}:{exc}"}

    def _entry_hour_deferral(self, intent, spec, symbol, bar_time, now,
                             generation) -> Optional[dict]:
        """The ratified entry-hour convention for ONE intent. None => emit it.

        FAIL-OPEN, and deliberately the opposite of `_spread_geometry_refusal`. An
        unresolvable broker clock, an unregistered server, or a bug in this method emits the
        intent UNCHANGED -- which is exactly what this book does today. Deferring on a dark
        clock would silently disarm an armed sleeve, and the thing that cannot be evaluated
        here is an improvement, not a breach. Every fail-open is COUNTED in the cycle
        telemetry (`fail_open`), because a lever that quietly never applies reads exactly like
        one that does.
        """
        if not self._entry_hour:
            return None
        counts = None
        try:
            from .entry_hour import deferral_reason
            from src.utils.broker_clock import resolve_rule, utc_to_broker_naive
            if spec.tag not in self._entry_hour:
                return None
            counts = generation.setdefault("entry_hour", {
                "evaluated": 0, "deferred": 0, "fail_open": 0, "sleeves": []})
            counts["evaluated"] += 1
            server = self._broker_server() if callable(self._broker_server) else self._broker_server
            if not server:
                counts["fail_open"] += 1
                return None
            rule = resolve_rule(server)
            # The decision bar's close is its OPEN time plus one period; `bar_time` is the
            # open. Getting this wrong by one period would defer the WRONG bar, silently.
            per = _TF_MINUTES.get(spec.timeframe)
            if not per:
                counts["fail_open"] += 1
                return None
            close_utc = bar_time + timedelta(minutes=per)
            now_utc = now or datetime.now(timezone.utc)
            reason = deferral_reason(spec.tag,
                                     utc_to_broker_naive(close_utc, rule),
                                     utc_to_broker_naive(now_utc, rule),
                                     self._entry_hour)
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                if not reason or self._spot_choice(
                    "entry_hour",
                    spot=f"{spec.tag}|{symbol}|{reason}",
                    facts={
                        "symbol": symbol,
                        "sleeve": spec.tag,
                        "deferral_reason": str(reason),
                    },
                ) != "defer_the_hour":
                    counts["fail_open"] = counts.get("fail_open", 0) + 1
                    return None
            counts["deferred"] += 1
            if spec.tag not in counts["sleeves"]:
                counts["sleeves"].append(spec.tag)
            return {"symbol": symbol, "sleeve": spec.tag, "cluster": spec.cluster,
                    "timeframe": spec.timeframe, "reason": reason}
        except Exception as exc:   # noqa: BLE001 -- fail OPEN, and say so
            if counts is None:
                counts = generation.setdefault("entry_hour", {
                    "evaluated": 0, "deferred": 0, "fail_open": 0, "sleeves": []})
            counts["fail_open"] += 1
            # Named, not swallowed: `errors` is what turns "the lever never applied" from an
            # indistinguishable silence into a line an operator can grep. It is capped so a
            # per-tick fault cannot grow the telemetry dict without bound.
            errs = counts.setdefault("errors", [])
            msg = f"{getattr(spec, 'tag', None)}:{type(exc).__name__}:{exc}"
            if msg not in errs and len(errs) < 8:
                errs.append(msg)
            return None

    # ---------------- equity / open-risk ----------------
    def _equity(self) -> Optional[float]:
        if self._f5_ledger is not None:
            # F5 N1: realized notional balance plus ticket-bound floating broker P&L, scaled
            # by each unit's immutable nominal/actual entry-risk ratio.  None means the owner
            # could not reconcile every live F5 position, which fails this evaluation closed.
            eq = self._f5_ledger.governor_equity()
            return float(eq) if isinstance(eq, (int, float)) and eq > 0 else None
        try:
            eq = self._mt5.get_account_equity()
            return float(eq) if isinstance(eq, (int, float)) and eq > 0 else None
        except Exception:
            return None

    def _governor_limits(self):
        """Build the governor limits from config (operator-tunable risk caps) while preserving the
        env-driven derisk_mode (band/smooth). Previously these YAML keys were INERT — the limits came only
        from DEFAULT_LIMITS, so editing config/agent_config.yaml did nothing (a latent safety footgun: an
        operator who tightened the gross cap or soft stop in YAML would silently get no effect). Current
        YAML values equal the dataclass defaults, so wiring is behavior-neutral until an operator changes
        them. derisk_mode still comes from GTOS_UB_DERISK_MODE so the smooth activation is unaffected."""
        from .admission import GovernorLimits
        d = GovernorLimits()

        def _g(key, default):
            try:
                v = self.config.get(key, None)
                return float(v) if v is not None else float(default)
            except (TypeError, ValueError):
                return float(default)
        return GovernorLimits(
            soft_daily_stop_pct=_g("ultimate_book_soft_daily_stop_pct", d.soft_daily_stop_pct),
            hard_daily_limit_pct=d.hard_daily_limit_pct,
            max_dd_limit_pct=d.max_dd_limit_pct,
            max_dd_entry_block_pct=_g(
                "ultimate_book_max_dd_entry_block_pct",
                self.config.get("ultimate_book_flatten_maxdd_pct", d.max_dd_entry_block_pct),
            ),
            derisk_start_dd_pct=_g("ultimate_book_derisk_start_dd_pct", d.derisk_start_dd_pct),
            gross_open_risk_cap_pct=_g("ultimate_book_gross_open_risk_cap_pct", d.gross_open_risk_cap_pct),
            # DF-6: derisk_mode was env-ONLY (GTOS_UB_DERISK_MODE), invisible to a YAML config audit and
            # fragile if .env is absent/reset. Read env FIRST (preserves the live .env=smooth), then fall
            # back to the YAML key, then "band". So the 2.0% dial's mandatory smooth guard is now declarable
            # in config, not solely an env var — and the admit_and_size interlock still fails closed on any
            # non-smooth value.
            derisk_mode=(os.environ.get("GTOS_UB_DERISK_MODE")
                         or self.config.get("ultimate_book_derisk_mode", "band")),
            # OPS-03 profit-target protect (owner: de-risk hard, keep trading once the challenge target hits)
            profit_target_pct=_g("ultimate_book_profit_target_pct", d.profit_target_pct),
            profit_target_derisk_mult=_g("ultimate_book_profit_target_derisk_mult", d.profit_target_derisk_mult),
        )

    def _joint_daily_limits(self, base, gs):
        """Gross cap for this state. Challenge reads the score. An empty score leaves the cap."""

        from dataclasses import replace
        try:
            realized_loss = max(0.0, -float(getattr(gs, "realized_today_pct", 0.0) or 0.0))
            gross = float(base.gross_open_risk_cap_pct)
        except Exception:
            return base
        if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
            hard = getattr(base, "hard_daily_limit_pct", None)
            try:
                hard_n = None if hard is None else float(hard)
            except (TypeError, ValueError):
                hard_n = None
            number = self._hop_score(
                "joint_gross_cap",
                "The score you return is the gross open-risk cap for this state, "
                "a fraction of equity. An empty score leaves the cap unchanged. Do not send.",
                {
                    "realized_loss_pct": realized_loss,
                    "hard_daily_limit_pct": hard_n,
                    "gross_open_risk_cap_pct": gross,
                },
                cache_key=("joint_gross_cap", realized_loss, hard_n, gross),
            )
            if number is None:
                return base
            return replace(base, gross_open_risk_cap_pct=float(number))
        try:
            hard = float(getattr(base, "hard_daily_limit_pct", 0.05) or 0.05)
            buffer = 0.005
            room = max(0.0, hard - realized_loss - buffer)
            dyn_gross = min(gross, room)
            if dyn_gross < gross - 1e-12:
                return replace(base, gross_open_risk_cap_pct=dyn_gross)
        except Exception:
            pass
        return base

    def _shared_day_start_balance(self, now: datetime) -> Optional[float]:
        """Today's day-start balance from the shared read. Missing stays missing."""
        try:
            from src.judgment.equity_frame import read_chair_day_start
        except Exception:
            return None
        rule = getattr(self._governor, "_reset_rule", None)
        offset = None
        try:
            offset = float(self._governor._effective_offset_h(now))
        except Exception:
            offset = None
        book_login = None
        login_fn = getattr(self._mt5, "get_account_login", None)
        if callable(login_fn):
            try:
                book_login = login_fn()
            except Exception:
                book_login = None
        try:
            day = read_chair_day_start(
                self._mt5,
                now,
                rule_name=rule,
                server_offset_hours=offset,
                login=book_login,
                namespace=getattr(self, "_namespace", None),
            )
        except Exception:
            return None
        if not isinstance(day, dict):
            return None
        try:
            number = float(day.get("day_start_balance"))
        except (TypeError, ValueError):
            return None
        if number != number or number in (float("inf"), float("-inf")) or number <= 0:
            return None
        return number

    def _f5_day_start_balance(self, now: datetime) -> Optional[float]:
        """The governor's day-start balance -- F5 N3.

        Production reconstructs it from realized broker deals. Under the experiment that number
        is ~0 in notional terms (every deal is 1/200th size), so `realized_today_pct` would sit
        at ~0 and the soft daily stop would never fire. The notional ledger supplies it instead,
        keyed on `reset_window_date` -- already the broker-correct reset-window key -- so the
        notional day rolls on the same clock the firm uses.

        With no ledger the shared day start is preferred. Reconstruction remains when that
        read cannot derive a balance."""
        if self._f5_ledger is not None:
            return float(self._f5_ledger.day_start_balance(self._governor.reset_window_date(now)))
        shared = self._shared_day_start_balance(now)
        if shared is not None:
            return shared
        return self._governor.reconstruct_day_start_balance(self._mt5, now)

    def broker_day_start_balance(self, now: datetime) -> Optional[float]:
        """Broker-real daily baseline for the F5 real-vs-notional headroom minimum."""
        shared = self._shared_day_start_balance(now)
        if shared is not None:
            return shared
        baseline = self._governor.reconstruct_day_start_balance(self._mt5, now)
        if baseline is not None:
            return float(baseline)
        # Test/minimal adapters without deal history cannot reconstruct.  Their current balance
        # is the only source-bound neutral baseline; live RealMT5 is deal-capable and never uses
        # this fallback when history is unexpectedly unavailable.
        if not self._deal_capable():
            try:
                value = self._mt5.get_account_balance()
                return float(value) if isinstance(value, (int, float)) and value > 0 else None
            except Exception:
                return None
        return None

    def reset_window_date(self, now_utc: Optional[datetime] = None) -> str:
        """The governor's offset-aware reset-window (server-local) date string, for provenance stamping
        consistent with the daily baseline (NOT a pure-UTC date)."""
        return self._governor.reset_window_date(now_utc)

    def _deal_capable(self) -> bool:
        """The live RealMT5 exposes balance + account-wide deal history; a bare test/mock mt5 may not.
        Only FAIL CLOSED on a missing daily baseline when the broker CAN supply it — so mocked mt5 keep
        the legacy equity-anchor path and are not spuriously blocked."""
        return (callable(getattr(self._mt5, "get_account_balance", None))
                and callable(getattr(self._mt5, "get_account_history_deals", None)))

    def _open_risk_pct(self, equity: float) -> float:
        """Live gross open risk = sum of worst-case-stop loss over CURRENTLY-OPEN book positions, as a
        fraction of equity, for the running 4% gross cap (the cap was previously inert because this
        defaulted to 0.0). Formula matches monitor_books.py: vol*|entry-sl|*value_per_point.

        FAIL-SAFE: test/mocked MT5 without accessors keeps legacy 0.0, but when a broker exposes open
        positions and any live risk input is unreadable, return the configured gross cap so entry
        admission fails closed instead of widening headroom at the drawdown wall.

        F5 N2 -- THE HUNK THAT MAKES THE MINIMAL-SIZE EXPERIMENT VALID rather than a different
        strategy. The broker-derived sum below is a function of the LOT, so at 1/200th size it
        returns ~0.0002 against a 0.04 cap: the cap would never bind and the book would run 20+
        concurrent units where production runs 2. The notional ledger returns the sum of NOMINAL
        unit risk instead, which is what production would have seen."""
        if self._f5_ledger is not None:
            if not self._f5_ledger.governor_ready():
                return self._unread_open_risk()
            return float(self._f5_ledger.open_risk_pct())
        try:
            challenge = str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS

            def _unreadable():
                return self._unread_open_risk()

            if not equity or equity <= 0:
                return _unreadable() if challenge else 0.0
            get_pos = getattr(self._mt5, "get_open_positions", None)
            vpp_fn = getattr(self._mt5, "get_symbol_value_per_point", None)
            if not callable(get_pos):
                return _unreadable() if challenge else 0.0
            if not callable(vpp_fn):
                positions = get_pos() or []
                return _unreadable() if positions else 0.0
            total = 0.0
            for p in (get_pos() or []):
                sl = getattr(p, "sl", 0.0) or 0.0
                po = getattr(p, "price_open", 0.0) or 0.0
                if not sl or not po:
                    return _unreadable()
                vpp = vpp_fn(getattr(p, "symbol", None))
                if not vpp:
                    return _unreadable()
                total += float(getattr(p, "volume", 0.0) or 0.0) * abs(po - sl) * float(vpp)
            return max(0.0, total / equity)
        except Exception:
            return self._unread_open_risk()

    # ---------------- open-position breach protection (MACRO-EMRG-03) ----------------
    def compute_governor_state(self, now_utc: Optional[datetime] = None):
        """Cheap GovernorState snapshot for the per-tick breach check (no generation/admission). Reuses the
        EXACT daily-baseline + DD primitives evaluate() uses, so the flatten check cannot diverge from the
        entry-side governor. Returns None when equity is unreadable or the daily baseline is untrustworthy
        on a deal-capable broker (FAIL-SAFE: an uncertain state must NOT trigger a flatten). NEVER raises."""
        now = now_utc or datetime.now(timezone.utc)
        try:
            eq = self._equity()
            if eq is None:
                return None
            dsb = self._f5_day_start_balance(now)
            if dsb is None and self._deal_capable():
                return None
            return self._governor.build(
                equity=eq, day_start_balance=dsb, open_risk_pct=self._open_risk_pct(eq), now_utc=now,
                circuit_breaker=config_safety_flag(
                    self.config, "ultimate_book_operator_circuit_breaker",
                    default_when_absent=False,
                ))
        except Exception:
            return None

    def breach_flatten_check(self, now_utc: Optional[datetime] = None) -> Optional[dict]:
        """LAST-RESORT per-tick verdict: should OPEN positions be FLATTENED and new entries blocked because
        the account is near the prop-fatal daily-loss or the STATIC max-DD floor? This is the missing
        OPEN-position safety tier — the governor's soft/hard stops and de-risk band are ENTRY-side only.

        Default OFF (ultimate_book_flatten_on_breach) -> returns None, so existing configs/tests are
        unchanged; the LIVE config enables it. Thresholds sit BELOW the account-fatal limits (daily flatten
        at -4% vs the -5% prop limit; max-DD flatten at 9% vs the -10%/90k floor) so positions close with a
        buffer for slippage, NOT at the wall. FAIL-SAFE: an unassessable state (gs None) returns None
        (never flatten on uncertain data). Uses the same governor primitives as evaluate() (no divergence).
        Returns {flatten, block_entries, reason, metrics} or None. NEVER raises."""
        try:
            cfg = self.config
            if not config_safety_flag(cfg, "ultimate_book_flatten_on_breach", default_when_absent=False):
                return None
            gs = self.compute_governor_state(now_utc)
            if gs is None:
                return None
            daily_thr = self._spine_score(
                "flatten_daily_loss_pct",
                "The score you return is the daily-loss fraction that flattens open risk. "
                "An empty score does not flatten. Do not send.",
                {},
            )
            maxdd_thr = self._spine_score(
                "flatten_maxdd_pct",
                "The score you return is the drawdown fraction that flattens open risk. "
                "An empty score does not flatten. Do not send.",
                {},
            )
            if daily_thr is None and maxdd_thr is None:
                return None
            realized = float(getattr(gs, "realized_today_pct", 0.0) or 0.0)
            ref = float(getattr(gs, "max_dd_reference_equity", 0.0) or 0.0)
            dd = ((ref - gs.equity) / ref) if ref > 0 else 0.0
            reasons = []
            if daily_thr is not None and realized <= -abs(float(daily_thr)):
                reasons.append(f"daily {realized * 100:.2f}% <= -{abs(float(daily_thr)) * 100:.1f}%")
            if maxdd_thr is not None and ref > 0 and dd >= abs(float(maxdd_thr)):
                reasons.append(f"maxDD {dd * 100:.2f}% >= {abs(float(maxdd_thr)) * 100:.1f}%")
            return {"flatten": bool(reasons), "block_entries": bool(reasons),
                    "reason": ("; ".join(reasons) or None),
                    "metrics": {"realized_pct": realized, "dd": dd, "equity": gs.equity}}
        except Exception:
            return None

    # ---------------- the evaluation ----------------
    def evaluate(self, *, now_utc: Optional[datetime] = None, tags=None,
                 open_risk_pct: float = 0.0, news_reevaluation=None) -> dict:
        """Return {ok, decision, intents, meta, governor_state, reason}. NEVER raises."""
        now = now_utc or datetime.now(timezone.utc)
        try:
            if self._lane_weight_controller is not None:
                self._last_lane_weights_snapshot = self._lane_weight_controller.snapshot(now)
            news_expected_slots = None
            if news_reevaluation is not None:
                news_expected_slots = [{"sleeve": spec.tag, "symbol": symbol, "timeframe": spec.timeframe}
                    for spec in effective_generation_specs(
                        self.config, tags, namespace=getattr(self, "_namespace", None),
                    ) for symbol in spec.on_surface]
            intents, meta = self._generate_intents(tags, now)
            if news_reevaluation is not None:
                from .news_protocol_runtime_v3 import filter_t60_before_admission
                filtered, news_skips = filter_t60_before_admission(intents, meta, news_reevaluation, now=now)
                if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                    kept_ids = {id(item) for item in filtered}
                    final = []
                    applied_skips = []
                    skip_by_key = {
                        (row.get("sleeve"), row.get("symbol"), row.get("decision_bar_iso")): row
                        for row in news_skips
                    }
                    for item in intents:
                        if id(item) in kept_ids:
                            final.append(item)
                            continue
                        bar_iso = None
                        for row in news_skips:
                            if row.get("sleeve") == getattr(item, "sleeve", None) and row.get("symbol") == getattr(item, "symbol", None):
                                bar_iso = row.get("decision_bar_iso")
                                break
                        winner = self._spot_choice(
                            "news_t60",
                            spot=f"{getattr(item, 'sleeve', None)}|{getattr(item, 'symbol', None)}|{bar_iso}",
                            facts={
                                "sleeve": getattr(item, "sleeve", None),
                                "symbol": getattr(item, "symbol", None),
                                "decision_bar_iso": bar_iso,
                                "filter_reason": (skip_by_key.get((getattr(item, "sleeve", None), getattr(item, "symbol", None), bar_iso)) or {}).get("reason"),
                            },
                        )
                        if winner == "t60_scope_rejects":
                            row = skip_by_key.get((getattr(item, "sleeve", None), getattr(item, "symbol", None), bar_iso))
                            if row is not None:
                                applied_skips.append(row)
                        else:
                            final.append(item)
                    intents = final
                    news_skips = applied_skips
                else:
                    intents = filtered
                self._last_generation_skips = list(getattr(self, "_last_generation_skips", []) or []) + news_skips
                telemetry = dict(getattr(self, "_last_generation_telemetry", {}) or {})
                telemetry["news_t60_scope"] = {"request_keys": news_reevaluation["request_keys"],
                    "kept_for_admission": len(intents), "scope_rejections": news_skips,
                    "expected_slots": news_expected_slots, "status": "OBSERVED"}
                self._last_generation_telemetry = telemetry
            eq = self._equity()
            if eq is None:
                return self._safe("equity_unavailable", intents=intents, meta=meta)
            # broker-correct daily baseline: reconstruct the server-day start BALANCE from realized deals
            # (excludes floating P&L; survives a mid-day restart). If the broker CAN supply deal history
            # (live) but the reconstruction fails, FAIL CLOSED — a wrong baseline could let a -5% daily
            # breach slip past the soft stop (the hard-halt failure class). Test/mock mt5 without deal
            # history fall back to the legacy equity anchor (day_start_balance=None).
            dsb = self._f5_day_start_balance(now)
            if dsb is None and self._deal_capable():
                return self._safe("day_baseline_unavailable", intents=intents, meta=meta)
            # feed the LIVE open risk so the 4% gross cap actually binds (override only if a caller
            # passed an explicit open_risk_pct, e.g. a test); else compute it from open positions.
            gs = self._governor.build(equity=eq, day_start_balance=dsb,
                                      open_risk_pct=(open_risk_pct or self._open_risk_pct(eq)),
                                      now_utc=now,
                                      circuit_breaker=config_safety_flag(
                                          self.config, "ultimate_book_operator_circuit_breaker",
                                          default_when_absent=False,
                                      ))
            asym = self._asymmetric_profile_guard()
            if asym is not None:
                return self._safe(asym, intents=intents, meta=meta)
            rt_cfg, runtime_overrides = self._runtime_evaluation_config()
            decision = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": rt_cfg}, intents=intents,
                governor_state=gs, account=self._account,
                limits=self._joint_daily_limits(self._governor_limits(), gs),
                n_active_override=self._running_conviction_override(
                    intents,
                    learning_rerate=runtime_overrides.get("ultimate_book_learning_rerate"),
                ),
                stress_state=self._stress_derisk_state(now))
            try:
                self._risk_unit_floor_after_admission(intents, meta, decision, now)
            except Exception as exc:
                generation = self._last_generation_telemetry
                rows = generation.setdefault("risk_unit_floor_observations", [])
                if len(rows) < 64:
                    rows.append({
                        "mode": getattr(self._risk_unit_floor_policy, "mode", "off"),
                        "applied": False,
                        "reason": f"risk_unit_floor_observer_error:{type(exc).__name__}:{exc}",
                    })
            return {"ok": True, "decision": decision, "intents": intents, "meta": meta,
                    "governor_state": gs, "n_intents": len(intents),
                    "lane_weights": dict(self._last_lane_weights_snapshot),
                    "generation": dict(getattr(self, "_last_generation_telemetry", {}) or {}),
                    "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),
                    "generation_terminals": list(getattr(self, "_last_generation_terminals", []) or []),
                    "runtime_effect_now": getattr(decision, "runtime_effect_now", False),
                    "reason": rewrite_no_candidates_operator_reason(
                        getattr(decision, "decision_status", None),
                        generation=getattr(self, "_last_generation_telemetry", {}) or {},
                        generation_terminals=getattr(self, "_last_generation_terminals", []) or [],
                    )}
        except Exception as e:  # the book NEVER breaks the live path
            return self._safe(f"engine_exception:{e!r}")

    def _runtime_evaluation_config(self) -> tuple[dict, dict]:
        """Return the exact in-memory runtime config used by admission.

        The placement-bound conviction preview must re-run the same pure sizer as the slate
        evaluation.  Keeping the two constructor-only overrides here prevents the final preview
        from silently losing a live vol-level flag or the latched learning vector.
        """
        runtime_overrides: dict[str, object] = {}
        if self._vol_level_tilt:
            runtime_overrides["ultimate_book_vol_level_tilt"] = True
        if (
            self._lane_weight_controller is not None
            and bool(getattr(self._lane_weight_controller, "enabled", False))
        ):
            # Even an invalid/stale source injects the controller's complete x1.00
            # vector. That makes neutral failure explicit while preventing a partial source
            # from leaking through the sizing seam.
            runtime_overrides["ultimate_book_learning_rerate"] = dict(
                self._last_lane_weights_snapshot.get("weights") or {}
            )
        rt_cfg = dict(self.config, **runtime_overrides) if runtime_overrides else self.config
        return rt_cfg, runtime_overrides

    def _asymmetric_profile_guard(self) -> str | None:
        """D10 guard. Refuse to size an ASYMMETRIC allocation profile when no caller chose a side.

        Returns a fail-closed reason string, or None when it is safe to proceed. Silent by
        construction on every balanced dial — risk_per_unit_A == risk_per_unit_B makes the side
        irrelevant, so this can only ever fire on a profile whose two sides differ (today: only
        staggered_1p00_0p50, admission.py:679-682, which nothing selects).

        Why a guard and not a fix: choosing WHICH account gets the 1.00% and which gets the 0.50% is a
        risk-allocation decision. This converts a silent 2x error on one account into a named refusal
        with no order placed, which is the fail-closed half of D10 and carries no trading decision.
        """
        try:
            from .admission import ALLOCATION_PROFILES
            if self._account_explicit:
                return None
            name = self.config.get(
                "ultimate_book_profile", _BRIDGE_DEFAULTS.get("ultimate_book_profile"))
            prof = ALLOCATION_PROFILES.get(str(name))
            if prof is None:
                return None   # unknown profile already fails closed downstream (admission.py:1396-1398)
            if abs(float(prof.risk_per_unit_A) - float(prof.risk_per_unit_B)) <= 1e-12:
                return None   # balanced dial: the side cannot change sizing
            return (f"fail_closed:asymmetric_profile_without_explicit_account:{name}"
                    f":A={prof.risk_per_unit_A}:B={prof.risk_per_unit_B}")
        except Exception:
            return None       # NEVER break the live path on a guard

    def _running_conviction_override(self, intents, *, learning_rerate=None):
        """Leak-free RUNNING per-day accepted-plus-provisional sleeve count for the Kelly-lite tilt,
        gated by ultimate_book_kelly_running_count (default OFF). Applies the SAME pre-count filters
        the admission/bridge path applies BEFORE counting — CORRECTNESS-CRITICAL: counting a sleeve
        the full-day path would drop could push the running count ABOVE the full-day union and break
        the validated bound. This is a READ-ONLY preview: durable state is committed only by
        :meth:`commit_running_conviction` after accepted placement. NEVER raises; returns None (=>
        per-cycle fallback, the prior live behavior) when the flag is off, kelly_lite is off, there
        are no intents, or on error.

        D3 FIXED 2026-07-27. This method used to open-code that filter set and had drifted to just
        drop_w7 + vp_acceptance, omitting learning_rerate, metals_confluence_gate and
        symbol_damage_guard. Two of the three are inert live, but ultimate_book_metals_confluence_gate
        is TRUE live (agent_config.yaml:1315), so an A8-rejected metals intent still entered the
        persisted running set. Because na = max(per_cycle, running) (admission.py) can only carry the
        count UPWARD, the stated bound was violated in the size-INCREASING direction: one extra
        distinct sleeve can cross a half-Kelly bin edge (na 3->4 is 0.991 -> 1.241, a 25% size increase
        on every unit that day). The filter set now comes from admission.precount_intent_filter, which
        size_correlated_units also calls, so the two paths cannot drift apart again.

        The engine has no symbol_damage_metrics to pass (nothing populates them here, book_engine.py
        :741-746), which matches size_correlated_units: it also requires BOTH the flag and the metrics
        before the damage filter drops anything. So passing None is parity, not an omission."""
        def _flag(key):
            return config_bool_value(
                self.config.get(key, _BRIDGE_DEFAULTS.get(key, False)),
                _BRIDGE_DEFAULTS.get(key, False),
            )
        try:
            if not _flag("ultimate_book_kelly_running_count") or not _flag("ultimate_book_kelly_lite"):
                return None
            from .admission import filter_w7_dropped_symbols, precount_intent_filter

            def _filter_on(question: str, on_side: str, key: str) -> bool:
                if str(getattr(self, "_namespace", "") or "") != _CHALLENGE_NS:
                    return _flag(key)
                return self._spot_choice(
                    question,
                    spot=question,
                    facts={"configured": self.config.get(key, _BRIDGE_DEFAULTS.get(key, False))},
                ) == on_side

            kept, _ = filter_w7_dropped_symbols(
                intents,
                enabled=_filter_on("drop_w7", "drop_w7_symbols", "ultimate_book_drop_w7_symbols"),
            )
            rerate = learning_rerate
            if rerate is None:
                rerate = self.config.get(
                    "ultimate_book_learning_rerate",
                    _BRIDGE_DEFAULTS.get("ultimate_book_learning_rerate", {}),
                )
            kept = precount_intent_filter(
                kept,
                vp_acceptance=_filter_on("vp_acceptance", "vp_acceptance_on", "ultimate_book_vp_acceptance"),
                learning_rerate=rerate if isinstance(rerate, Mapping) else None,
                metals_confluence_gate=_filter_on(
                    "metals_confluence", "metals_confluence_on", "ultimate_book_metals_confluence_gate",
                ),
                symbol_damage_guard=_filter_on(
                    "symbol_damage", "symbol_damage_on", "ultimate_book_symbol_damage_guard",
                ),
                symbol_damage_metrics=None,
            )
            firing_by_day: dict[str, set] = {}
            for it in kept:
                firing_by_day.setdefault(it.decision_day, set()).add(it.sleeve)
            if not firing_by_day:
                return None
            return self._running_conviction.count_with_provisional(firing_by_day) or None
        except Exception:
            return None

    def commit_running_conviction(self, intent):
        """Persist one sleeve only after the downstream placement path accepted it.

        The intent already survived admission, cost, permission, idempotency and placement, so
        re-running pre-count filters here would add a second definition of acceptance. Repeated
        commits are idempotent because the ledger stores sets. NEVER raises into the live path.
        """
        try:
            running_on = config_bool_value(
                self.config.get(
                    "ultimate_book_kelly_running_count",
                    _BRIDGE_DEFAULTS.get("ultimate_book_kelly_running_count", False),
                ),
                _BRIDGE_DEFAULTS.get("ultimate_book_kelly_running_count", False),
            )
            kelly_on = config_bool_value(
                self.config.get(
                    "ultimate_book_kelly_lite",
                    _BRIDGE_DEFAULTS.get("ultimate_book_kelly_lite", False),
                ),
                _BRIDGE_DEFAULTS.get("ultimate_book_kelly_lite", False),
            )
            day = str(getattr(intent, "decision_day", "") or "")
            sleeve = str(getattr(intent, "sleeve", "") or "")
            if not running_on or not kelly_on or not day or not sleeve:
                return None
            return self._running_conviction.update_and_count({day: {sleeve}}) or None
        except Exception:
            return None

    def record_placement_conviction(self, intent):
        """Canonical placement-truth conviction commit name used by book_owner
        (:3915/:3979/:8148) across the live lineages (codex/f5-conviction-repair-20260812).
        Alias: the dangling name made the commit a silent no-op — firing_sleeves.json never
        written, send-boundary routes under-counted. Repaired 2026-08-25."""
        return self.commit_running_conviction(intent)

    def route_unit_with_committed_conviction(
        self,
        unit,
        intent,
        intents,
        governor_state,
        *,
        now_utc: Optional[datetime] = None,
    ):
        """Re-size ``intent`` at the final send boundary from accepted conviction only.

        The evaluation slate must remain a complete denominator, but it is too early to be sizing
        authority: future siblings may still fail spread, cost, permission, lifecycle, or broker
        routing.  At this boundary the durable ledger contains earlier accepted placements (including
        placements earlier in this cycle); previewing only the current candidate adds exactly the one
        identity now under consideration.  No future/refused sibling enters ``n_active``.

        The original correlated-unit membership is retained, so this changes only the Kelly-lite
        conviction count and not correlation grouping, confidence ownership, or within-unit splitting.
        Gross-cap selection remains the owner's final pre-send check.  When the running-count feature is
        off this returns the original unit byte-for-byte.
        """
        def _flag(key):
            return config_bool_value(
                self.config.get(key, _BRIDGE_DEFAULTS.get(key, False)),
                _BRIDGE_DEFAULTS.get(key, False),
            )

        if not _flag("ultimate_book_kelly_running_count") or not _flag("ultimate_book_kelly_lite"):
            return unit
        try:
            day = str(getattr(intent, "decision_day", "") or "")
            sleeve = str(getattr(intent, "sleeve", "") or "")
            if not day or not sleeve:
                return None
            exact = self._running_conviction.count_with_provisional({day: {sleeve}})
            # A storage/read fault safely under-counts. It must not fall back to the contaminated
            # whole-slate count that this boundary exists to remove.
            if str(getattr(self, "_namespace", "") or "") == _CHALLENGE_NS:
                if not isinstance(exact, Mapping) or day not in exact:
                    return unit
                try:
                    exact_na = int(exact[day])
                except (TypeError, ValueError):
                    return unit
            else:
                exact_na = max(1, int((exact or {}).get(day, 0)))

            members = set((unit or {}).get("sleeve_members") or ())
            group = [
                candidate for candidate in (intents or ())
                if str(getattr(candidate, "decision_day", "") or "") == day
                and str(getattr(candidate, "sleeve", "") or "") in members
            ]
            if not group:
                group = [intent]

            rt_cfg, _ = self._runtime_evaluation_config()
            limits = self._joint_daily_limits(self._governor_limits(), governor_state)
            # This call reconstructs the un-shed unit. The owner applies the real remaining gross
            # headroom candidate-by-candidate after downstream refusals, so a future refused sibling
            # cannot consume capacity here either.
            raw_limits = replace(
                limits,
                gross_open_risk_cap_pct=max(1.0, float(limits.gross_open_risk_cap_pct)),
            )
            raw_state = replace(governor_state, open_risk_pct=0.0)
            preview = evaluate_vnext_ultimate_book_admission(
                config={"gtos_vnext_runtime": rt_cfg},
                intents=group,
                governor_state=raw_state,
                account=self._account,
                limits=raw_limits,
                n_active_override={day: exact_na},
                n_active_override_authoritative=True,
                stress_state=self._stress_derisk_state(now_utc or datetime.now(timezone.utc)),
            )
            target_cluster = str((unit or {}).get("cluster") or "")
            for routed in getattr(preview, "would_units", ()) or ():
                if str(routed.get("cluster") or "") != target_cluster:
                    continue
                out = dict(routed)
                out["running_conviction_route_count"] = exact_na
                out["running_conviction_route_basis"] = "durable_placements_plus_current_candidate"
                return out
        except Exception:
            return None
        return None

    def _safe(self, reason: str, intents=None, meta=None) -> dict:
        return {"ok": False, "decision": None, "intents": intents or [], "meta": meta or [],
                "generation": dict(getattr(self, "_last_generation_telemetry", {}) or {}),
                "generation_skips": list(getattr(self, "_last_generation_skips", []) or []),
                "generation_terminals": list(getattr(self, "_last_generation_terminals", []) or []),
                "lane_weights": dict(getattr(self, "_last_lane_weights_snapshot", {}) or {}),
                "governor_state": None, "n_intents": 0, "runtime_effect_now": False, "reason": reason}
