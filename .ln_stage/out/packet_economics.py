"""Economics blocks for the ultimate-book runtime learning packet.

Everything here is **additive and observation-only**. It builds optional sub-blocks that
`build_runtime_learning_packet` attaches to a packet; it holds no decision authority, opens
no order path, and imports nothing from the execution or admission layers.

Why this module exists
----------------------
Session N measured the dominant remaining uncertainty in the W7 book's economics and it is
**holding time**: at one night of average carry the book of record passes at ``P=0.951`` and
makes 1.97 %/month; if every trade ran to its structural horizon it passes at ``P=0.450`` and
makes 0.13 %/month. Nothing in the tree distinguishes those two worlds, because nothing records
how long a trade was actually open, in the clock that swap is charged on.

So the design rule for this module is narrow and it is the one that matters:

    **Emit what was observed, name where it came from, and never emit a derived number
    without also emitting the inputs it was derived from.**

That last clause is deliberate. Session N's carry layer shipped with a night count that scaled
every horizon by 5/7 on the reasoning that weekend midnights are not charged -- true in itself,
but the weekend is collected on the triple-swap weekday at weight 3.0, so a full week charges
seven nights, not five. Every ceiling was understated 1.40x. That error is invisible in a total
and obvious in a list of crossings, which is why :func:`rollover_nights_crossed` returns the
crossings and the packet carries them.

Provenance vocabulary
---------------------
The four labels below are deliberately the same words Session J's cost layer uses
(``src/costs/coverage.Coverage``: MEASURED / TRANSFERRED / MODELLED), plus ``unavailable`` for
the lifecycle stages where a value cannot exist yet. They are plain strings and **not** an import
of that module, because ``src/costs/`` does not exist on the live host and this module must
remain deployable there. Any consumer joining the two should treat the strings as the join key.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

# `src/utils/broker_clock.py` is NOT present on the live host as of the 2026-07-26 VPS export
# (`20_src/utils/` has no such file, and the VPS `governor_state.py` predates the clock work).
# A top-level import would therefore raise at module load, which propagates through book_owner and
# breaks the live book's import -- the single worst outcome this carry could have.
#
# So the dependency is optional by construction. Absent, the night count degrades to a labelled
# refusal (`rollover_nights: None` with `error: broker_clock_module_unavailable`) and every other
# field in this module still works. That also makes the carry order-independent: landing this file
# before broker_clock cannot break anything, it only postpones the night count.
try:
    from ...utils.broker_clock import (  # type: ignore[attr-defined]
        UnknownBrokerClockError,
        resolve_rule,
        utc_to_broker_naive,
    )

    BROKER_CLOCK_AVAILABLE = True
except Exception:  # noqa: BLE001 - pragma: no cover - exercised on hosts without the clock module
    # Deliberately broader than ImportError. `except ImportError` covers the module being ABSENT,
    # which is the VPS's steady state -- but not the module being PRESENT AND BROKEN, which is what
    # a half-finished file transfer produces. A truncated broker_clock.py raises SyntaxError here,
    # which `except ImportError` does not catch; it would propagate through book_owner and kill
    # run_book.py at startup on both namespaces. An absent optional dependency and a corrupt one
    # must degrade the same way, because the whole point of this guard is that nothing about this
    # file can stop a live book. Found by an adversarial pass, not by the original author.
    BROKER_CLOCK_AVAILABLE = False

    class UnknownBrokerClockError(LookupError):  # type: ignore[no-redef]
        pass

    def resolve_rule(server):  # type: ignore[misc]
        raise UnknownBrokerClockError("broker_clock module unavailable on this host")

    def utc_to_broker_naive(instant, rule):  # type: ignore[misc]
        raise UnknownBrokerClockError("broker_clock module unavailable on this host")

PACKET_ECONOMICS_CONTRACT_VERSION = "ultimate_book_packet_economics_v1"

# Provenance labels. Aligned with src/costs/coverage.Coverage by string value.
MEASURED = "measured"        # read from a broker deal, tick, or account fact
TRANSFERRED = "transferred"  # measured on a related instrument or window and carried across
MODELLED = "modelled"        # computed from config or a model; never observed
UNAVAILABLE = "unavailable"  # cannot exist at this point in the lifecycle

# Weakest-wins ordering, so a block's provenance is never stronger than its worst input.
_STRENGTH = {MEASURED: 0, TRANSFERRED: 1, MODELLED: 2, UNAVAILABLE: 3}


def weakest(*provenances: str | None) -> str:
    """The weakest provenance among the arguments; ``unavailable`` if there are none."""
    known = [p for p in provenances if p in _STRENGTH]
    if not known:
        return UNAVAILABLE
    return max(known, key=lambda p: _STRENGTH[p])


def _parse_utc(value: Any) -> datetime | None:
    """Parse an ISO-8601 instant to aware UTC. Returns None rather than raising.

    A naive string is *assumed* UTC, which is what every producer in this path emits --
    but see the module note in the carry doc: a field name ending in ``_utc`` is not
    evidence of a timebase, and this function cannot detect a mislabelled broker clock.
    The packet therefore records which field a value came from, so the assumption is
    auditable rather than buried.
    """
    # NOT `value in (None, "")`: that invokes __eq__ on the value, and a numpy array returns an
    # array (ValueError: truth value is ambiguous) while a hostile __eq__ can raise outright.
    # These helpers run inside a live book; an identity check cannot be tricked.
    if value is None or (isinstance(value, str) and not value):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mt5_dow(day: datetime) -> int:
    """MT5 ENUM_DAY_OF_WEEK: Sunday=0 .. Saturday=6. Python weekday(): Monday=0."""
    return (day.weekday() + 1) % 7


def rollover_nights_crossed(
    entry_utc: datetime,
    exit_utc: datetime,
    *,
    server: str | None,
    rollover3days_weekday: int | None = 3,
) -> tuple[float | None, dict[str, Any]]:
    """Swap-charged nights over a hold, counted on the **broker's** wall clock.

    A night is charged at each broker-wall midnight crossed. Saturday and Sunday midnights are
    not charged separately -- the weekend is collected on the triple-swap weekday
    (MT5 ``swap_rollover3days`` numbering, Wednesday=3 by default), which counts as three.
    Same rule as ``src/costs/model.rollover_nights``; the two must not be allowed to diverge.

    UTC midnight is the wrong boundary here and the error is not small: broker server wall clock
    is ``America/New_York + 7 h``, so the swap instant sits at 21:00 UTC in summer. A hold from
    22:00 to 23:00 UTC crosses no UTC midnight and one broker midnight.

    Fails closed **without raising**: an unregistered server yields ``(None, {...reason})``, never
    a guessed offset and never an exception into the caller.
    """
    detail: dict[str, Any] = {"basis": "broker_wall_midnight", "server": server}
    if not BROKER_CLOCK_AVAILABLE:
        detail["error"] = "broker_clock_module_unavailable"
        return None, detail
    try:
        rule = resolve_rule(server)
    except UnknownBrokerClockError as exc:
        detail["error"] = "unknown_broker_clock_rule"
        detail["error_detail"] = str(exc)
        return None, detail
    if exit_utc < entry_utc:
        detail["error"] = "exit_before_entry"
        return None, detail

    start = utc_to_broker_naive(entry_utc, rule)
    end = utc_to_broker_naive(exit_utc, rule)
    detail["rule"] = getattr(rule, "name", None)
    detail["entry_broker_wall"] = start.isoformat()
    detail["exit_broker_wall"] = end.isoformat()
    detail["rollover3days_weekday"] = rollover3days_weekday

    nights = 0.0
    crossings: list[str] = []
    day = (start + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= end:
        dow = _mt5_dow(day)
        if dow in (0, 6):  # Sunday / Saturday: market shut, no separate charge
            weight = 0.0
        elif rollover3days_weekday is not None and dow == int(rollover3days_weekday):
            weight = 3.0
        else:
            weight = 1.0
        if weight:
            crossings.append(f"{day.date().isoformat()}x{weight:g}")
        nights += weight
        day += timedelta(days=1)
    detail["crossings"] = crossings
    detail["nights_charged"] = nights
    return nights, detail


# Entry-instant candidates, strongest evidence first. Each is (packet key, provenance).
#
# Measured on the live export (99,112 packets, 2026-06-18..07-25): placement_observed_at_utc
# precedes broker_fill_time_utc by a median 1.23 s (90 of 93 closes, 126 of 132 placements) --
# it is the local send instant, not the fill. broker_fill_time_utc is the broker's own deal
# timestamp and is the only measured entry.
_ENTRY_SOURCES: tuple[tuple[str, str], ...] = (
    ("broker_fill_time_utc", MEASURED),
    ("placement_observed_at_utc", MODELLED),
)

# Exit-instant candidates, strongest first.
#
# Measured on the same export: closed_at_utc is the poll-loop's observation of the close, not a
# broker fact -- it is strictly later than the packet's own created_at_utc on 98 of 98 rows
# (median +0.046 s) and sits a median 26.8 s (p95 60.4 s, max 24.1 min) after
# broker_exit_time_utc. The poll cadence is 60 s, so that lag is one poll interval.
#
# `management_checked_at_utc` is DELIBERATELY NOT HERE, and this is the single most important
# line in the module.
#
# It means "the book looked at this position at time T", not "the position closed at time T".
# It is set unconditionally by book_owner immediately before the economics block is built, and it
# is present on 77,942 of 78,687 position_managed rows. Including it as an exit fallback made
# `exit_at` non-None for every management event, which -- verified by replay over the live corpus
# -- would have published 71,969 STILL-OPEN positions as completed holds, each with a
# holding_seconds of elapsed-so-far and rollover_nights counted to a fabricated exit. Mean
# holding time over the resulting block would read 20.85 h against a true 8.37 h: a **2.49x
# overstatement of the exact quantity this module exists to measure**, on a 476:1 ratio of
# fabricated to real samples, feeding the one number OD-3 turns on.
#
# The 88 position_managed rows that genuinely closed mid-management carry a real
# broker_exit_time_utc or closed_at_utc and are still honoured by the two entries below.
# An open position now reports `position_open_at_emit: true` and a CENSORED elapsed time under
# its own key -- which is honest evidence for a survival analysis, and is not a hold.
_EXIT_SOURCES: tuple[tuple[str, str], ...] = (
    ("broker_exit_time_utc", MEASURED),
    ("closed_at_utc", MODELLED),
)


def _resolve_instant(
    source: Mapping[str, Any], candidates: tuple[tuple[str, str], ...]
) -> tuple[datetime | None, str | None, str]:
    for key, provenance in candidates:
        parsed = _parse_utc(source.get(key))
        if parsed is not None:
            return parsed, key, provenance
    return None, None, UNAVAILABLE


def build_holding_block(
    outcome: Mapping[str, Any] | None,
    *,
    server: str | None = None,
    rollover3days_weekday: int | None = 3,
) -> dict[str, Any] | None:
    """Holding time as a first-class, provenance-labelled measurement.

    Returns ``None`` when no entry instant is resolvable at all, so the block never appears
    on the event types that cannot carry one (``unit_skipped``, ``cycle_no_candidates``,
    ``unit_shadow``, ``unit_admitted``) rather than appearing full of nulls.

    ``observation_lag_seconds`` is the honest part: when both a broker instant and a poll
    instant are present, it publishes the distance between them, so a consumer can see how
    much of a hold is real and how much is polling latency instead of assuming.
    """
    src = dict(outcome or {})
    entry, entry_key, entry_prov = _resolve_instant(src, _ENTRY_SOURCES)
    if entry is None:
        return None
    exit_at, exit_key, exit_prov = _resolve_instant(src, _EXIT_SOURCES)

    # `book_owner._iso_from_deal_time_near_reference` may have shifted the broker fill time by up
    # to +/-6 WHOLE HOURS to snap it to a local reference. That is not a measurement any more --
    # it is a measurement transferred onto our clock -- and it is exactly the class of silent
    # adjustment that makes a `_utc` suffix untrustworthy. When it fired, say so and weaken the
    # label; a reader must be able to tell a broker fact from one we moved.
    alignment_offset = _as_float(src.get("broker_fill_time_alignment_offset_seconds"))
    entry_aligned = bool(alignment_offset) and entry_key == "broker_fill_time_utc"
    if entry_aligned:
        entry_prov = TRANSFERRED

    block: dict[str, Any] = {
        "contract_version": PACKET_ECONOMICS_CONTRACT_VERSION,
        "entry_at_utc": entry.isoformat(),
        "entry_source_field": entry_key,
        "entry_provenance": entry_prov,
        "exit_at_utc": exit_at.isoformat() if exit_at else None,
        "exit_source_field": exit_key,
        "exit_provenance": exit_prov,
        "holding_seconds": None,
        "holding_provenance": UNAVAILABLE,
        "position_open_at_emit": exit_at is None,
        # None = the snap did not fire (or the field was never emitted); a number = the entry
        # instant was moved by that many seconds and is no longer a raw broker fact.
        "entry_alignment_offset_seconds": alignment_offset,
        "entry_alignment_applied": entry_aligned,
    }

    # Entry-side lag: how far the local send instant sat from the broker's fill.
    broker_entry = _parse_utc(src.get("broker_fill_time_utc"))
    local_entry = _parse_utc(src.get("placement_observed_at_utc"))
    if broker_entry is not None and local_entry is not None:
        block["entry_observation_lag_seconds"] = round(
            (local_entry - broker_entry).total_seconds(), 6
        )

    # Exit-side lag: how far the poll observation sat from the broker's exit deal.
    broker_exit = _parse_utc(src.get("broker_exit_time_utc"))
    polled_exit = _parse_utc(src.get("closed_at_utc")) or _parse_utc(
        src.get("management_checked_at_utc")
    )
    if broker_exit is not None and polled_exit is not None:
        block["exit_observation_lag_seconds"] = round(
            (polled_exit - broker_exit).total_seconds(), 6
        )

    if exit_at is None:
        # The position was open when this packet was written. That is not a missing measurement --
        # it is a right-censored one, and censored observations are real evidence provided they are
        # never mistaken for completed holds. Published under its own key so no consumer can
        # average it together with `holding_seconds` by accident.
        observed_at = (
            _parse_utc(src.get("management_checked_at_utc"))
            or _parse_utc(src.get("created_at_utc"))
        )
        if observed_at is not None and observed_at >= entry:
            block["elapsed_seconds_at_emit"] = round((observed_at - entry).total_seconds(), 6)
            block["elapsed_is_right_censored"] = True
            block["elapsed_observed_at_utc"] = observed_at.isoformat()
    else:
        seconds = (exit_at - entry).total_seconds()
        block["holding_seconds"] = round(seconds, 6)
        block["holding_hours"] = round(seconds / 3600.0, 8)
        block["holding_provenance"] = weakest(entry_prov, exit_prov)
        nights, night_detail = rollover_nights_crossed(
            entry,
            exit_at,
            server=server,
            rollover3days_weekday=rollover3days_weekday,
        )
        block["rollover_nights"] = nights
        block["rollover_detail"] = night_detail
        # The night count inherits the weaker of the two instants: a night boundary derived
        # from a polled exit is only as good as that poll.
        block["rollover_provenance"] = (
            UNAVAILABLE if nights is None else weakest(entry_prov, exit_prov)
        )
    return block


# Realized broker cost components already present on the packet, and the sign convention MT5
# uses for each: commission, swap and fee arrive NEGATIVE when charged.
_REALIZED_COST_FIELDS: tuple[str, ...] = (
    "broker_entry_commission",
    "broker_entry_swap",
    "broker_exit_commission",
    "broker_exit_swap",
    "broker_exit_fee",
)
_AGGREGATE_COST_FIELDS: tuple[str, ...] = (
    "broker_position_aggregate_commission",
    "broker_position_aggregate_swap",
    "broker_position_aggregate_fee",
)

# CN / OD-ALL-IN. The live broker-net model now charges commission as its fourth term.  Keep the
# legacy declaration beside it because every v2 packet already on disk has only the first three;
# historical rows must remain readable as the contract they actually carried, not be silently
# reinterpreted under today's model.
LEGACY_MODELLED_COST_COMPONENTS: tuple[str, ...] = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
)
MODELLED_COST_COMPONENTS: tuple[str, ...] = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
)
LEGACY_MODELLED_COST_EXCLUDES: tuple[str, ...] = ("commission",)
MODELLED_COST_EXCLUDES: tuple[str, ...] = ()


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or (isinstance(value, str) and not value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _modelled_cost_contract(src: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Resolve the component contract carried by one row, with v2-safe inference.

    New producers write both declarations explicitly.  Old producers wrote neither (or only the
    derived exclusion list), so absence must mean the historical three-component v2 contract.
    """
    raw_expected = src.get("modelled_cost_components_expected")
    if isinstance(raw_expected, (list, tuple)) and all(
        isinstance(value, str) and value for value in raw_expected
    ):
        expected = tuple(raw_expected)
    else:
        raw_components = src.get("modelled_cost_components")
        version = str(src.get("modelled_cost_model_version") or "")
        has_commission = (
            isinstance(raw_components, Mapping) and "commission_r" in raw_components
        )
        expected = (
            MODELLED_COST_COMPONENTS
            if has_commission or version.endswith("_v3")
            else LEGACY_MODELLED_COST_COMPONENTS
        )

    raw_excludes = src.get("modelled_cost_excludes")
    if isinstance(raw_excludes, (list, tuple)) and all(
        isinstance(value, str) and value for value in raw_excludes
    ):
        excludes = tuple(raw_excludes)
    else:
        excludes = (
            MODELLED_COST_EXCLUDES
            if "commission_r" in expected
            else LEGACY_MODELLED_COST_EXCLUDES
        )
    return expected, excludes


def build_cost_block(outcome: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Realized broker cost, separated from modelled cost, with the gap left computable.

    The named Phase-6 cost source records **intent only** -- what the book expected a trade to
    cost. It never records what the trade actually cost, so the modelling error has never been
    measurable, only assumed. Both sides are published here under distinct keys and the
    difference is deliberately *not* collapsed into one number: F38 (zero commission) and F39
    (tick erosion credited with the wrong sign) were both invisible precisely because a single
    net figure hid which component was wrong.

    ``components_present`` is derived by set-difference from the full expected field set rather
    than accumulated from what happened to be found, so a missing component reads as missing
    instead of as zero. Charging zero for an unknown cost is the F38 defect itself.
    """
    src = dict(outcome or {})
    realized: dict[str, float] = {}
    for key in _REALIZED_COST_FIELDS:
        val = _as_float(src.get(key))
        if val is not None:
            realized[key] = val
    aggregate: dict[str, float] = {}
    for key in _AGGREGATE_COST_FIELDS:
        val = _as_float(src.get(key))
        if val is not None:
            aggregate[key] = val
    modelled_cost_r = _as_float(src.get("modelled_cost_r"))
    spread_r = _as_float(src.get("spread_r"))
    if not realized and not aggregate and modelled_cost_r is None and spread_r is None:
        return None

    # The modelled side, by set-difference like the realized side above.
    expected_components, declared_excludes = _modelled_cost_contract(src)
    raw_components = src.get("modelled_cost_components")
    modelled_components: dict[str, float] = {}
    if isinstance(raw_components, Mapping):
        for key in expected_components:
            val = _as_float(raw_components.get(key))
            if val is not None:
                modelled_components[key] = val
    modelled_missing = sorted(set(expected_components) - set(modelled_components))
    # Comparability is a property of BOTH sides. Subtracting is safe only when the realized side
    # charges nothing the modelled side omits -- so an absent commission on the realized side is
    # not a licence to subtract, it is just a row where the question has not arisen yet.
    charged_commission = [
        k for k in ("broker_entry_commission", "broker_exit_commission")
        if realized.get(k) not in (None, 0.0)
    ]
    if modelled_cost_r is None:
        modelled_comparable = None
        modelled_incomparable_reason = "modelled_cost_absent"
    elif charged_commission and "commission" in declared_excludes:
        modelled_comparable = False
        modelled_incomparable_reason = (
            "realized_charges_commission_modelled_excludes_it:" + ",".join(sorted(charged_commission))
        )
    elif charged_commission and "commission_r" not in modelled_components:
        modelled_comparable = False
        modelled_incomparable_reason = "realized_charges_commission_modelled_commission_component_missing"
    elif not realized:
        modelled_comparable = None
        modelled_incomparable_reason = "realized_cost_absent"
    else:
        modelled_comparable = True
        modelled_incomparable_reason = None

    # Set-difference, not accumulation: name what is absent.
    missing = sorted(set(_REALIZED_COST_FIELDS) - set(realized))
    block: dict[str, Any] = {
        "contract_version": PACKET_ECONOMICS_CONTRACT_VERSION,
        "realized_components": realized,
        "realized_components_missing": missing,
        "realized_components_expected": list(_REALIZED_COST_FIELDS),
        "realized_provenance": MEASURED if realized else UNAVAILABLE,
        "realized_complete": not missing,
        "aggregate_components": aggregate or None,
        "modelled_cost_r": modelled_cost_r,
        "modelled_cost_provenance": MODELLED if modelled_cost_r is not None else UNAVAILABLE,
        "modelled_components": modelled_components or None,
        "modelled_components_expected": list(expected_components),
        "modelled_components_missing": modelled_missing,
        "modelled_cost_excludes": list(declared_excludes),
        # The one boolean a cost reader needs before subtracting. False whenever the realized side
        # charges a component the modelled side structurally cannot, which today is commission on
        # every row that has one.
        "modelled_vs_realized_comparable": modelled_comparable,
        "modelled_vs_realized_incomparable_reason": modelled_incomparable_reason,
        "spread_r": spread_r,
        "spread_r_provenance": src.get("spread_r_provenance")
        or (MEASURED if spread_r is not None else UNAVAILABLE),
    }
    # Only sum when the component set is complete. A partial sum is a wrong number wearing the
    # costume of a right one.
    if realized and not missing:
        block["realized_cost_currency_total"] = round(sum(realized.values()), 10)
    else:
        block["realized_cost_currency_total"] = None
    return block


def build_governor_block(
    governor: Any | None,
    *,
    limits: Any | None = None,
    decision: Any | None = None,
    day_anchor_equity: float | None = None,
    reset_window_date: str | None = None,
) -> dict[str, Any] | None:
    """The governor's **raw** inputs, not its derived verdict.

    This is the block that makes the gross-cap shed validatable. Today a packet carries no
    governor state at all, so any headroom analysis reconstructs equity and open risk from the
    same derived quantities it is trying to check -- the recovery is self-fulfilling and cannot
    fail. Session L measured the consequence from the other side: over 6,355 recorded units the
    gross cap **never bound**, zero units were shed, and peak utilization reached 0.4654. A shed
    that never fired cannot be validated on the data that failed to fire it, and it will stay
    unvalidatable until the raw inputs are on the record.

    The four that matter are ``equity``, ``open_risk_pct``, ``gross_open_risk_cap_pct`` and
    ``day_anchor_equity``. The first three are the shed's entire arithmetic
    (``available = cap - open_risk``); the fourth is the denominator of ``realized_today_pct``,
    which ``GovernorState`` consumes and then discards -- without it the daily-loss band is
    exactly the self-fulfilling case again.

    Every read is defensive: this runs inside a live book and a missing attribute must degrade
    the block, never the cycle.
    """
    if governor is None and limits is None and decision is None:
        return None

    def _get(obj: Any, name: str) -> Any:
        if obj is None:
            return None
        try:
            if isinstance(obj, Mapping):
                return obj.get(name)
            return getattr(obj, name, None)
        except Exception:  # noqa: BLE001 - observability must never raise into the book
            return None

    block: dict[str, Any] = {
        "contract_version": PACKET_ECONOMICS_CONTRACT_VERSION,
        # --- raw account facts (measured from the broker) ---
        "equity": _as_float(_get(governor, "equity")),
        "high_water": _as_float(_get(governor, "high_water")),
        "open_risk_pct": _as_float(_get(governor, "open_risk_pct")),
        "max_dd_reference_equity": _as_float(_get(governor, "max_dd_reference_equity")),
        "operator_circuit_breaker": bool(_get(governor, "operator_circuit_breaker")),
        # --- the discarded denominator, without which realized_today_pct cannot be checked ---
        "day_anchor_equity": _as_float(day_anchor_equity),
        "reset_window_date": reset_window_date,
        # --- derived, published alongside its inputs so it can be recomputed and disagreed with ---
        "realized_today_pct": _as_float(_get(governor, "realized_today_pct")),
        # --- the limits the shed compares against ---
        "gross_open_risk_cap_pct": _as_float(_get(limits, "gross_open_risk_cap_pct")),
        "soft_daily_stop_pct": _as_float(_get(limits, "soft_daily_stop_pct")),
        "max_dd_limit_pct": _as_float(_get(limits, "max_dd_limit_pct")),
        "max_dd_entry_block_pct": _as_float(_get(limits, "max_dd_entry_block_pct")),
        "derisk_start_dd_pct": _as_float(_get(limits, "derisk_start_dd_pct")),
        "derisk_mode": _get(limits, "derisk_mode"),
        "profit_target_pct": _as_float(_get(limits, "profit_target_pct")),
        # --- the verdict, so packet-only analysis can A/B its own recomputation ---
        "decision_allow_new_entries": _get(decision, "allow_new_entries"),
        "decision_size_cap_multiplier": _as_float(_get(decision, "size_cap_multiplier")),
        "decision_available_gross_risk_pct": _as_float(
            _get(decision, "available_gross_risk_pct")
        ),
        "decision_reason": _get(decision, "reason"),
        "provenance": MEASURED,
    }
    cap = block["gross_open_risk_cap_pct"]
    open_risk = block["open_risk_pct"]
    if cap not in (None, 0) and open_risk is not None:
        block["gross_cap_utilization"] = round(open_risk / cap, 8)
        block["gross_cap_bound"] = bool(open_risk >= cap)
    else:
        block["gross_cap_utilization"] = None
        block["gross_cap_bound"] = None
    return block


def build_economics_block(
    outcome: Mapping[str, Any] | None,
    *,
    server: str | None = None,
    rollover3days_weekday: int | None = 3,
    governor: Any | None = None,
    governor_limits: Any | None = None,
    governor_decision: Any | None = None,
    day_anchor_equity: float | None = None,
    reset_window_date: str | None = None,
    features: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Assemble the optional ``economics`` block. Returns ``None`` when nothing is available.

    Returning ``None`` rather than an empty shell matters: a block full of nulls is
    indistinguishable from a block that was never populated, and this programme has been burned
    four times by artifacts that could not tell absence from zero.
    """
    holding = build_holding_block(
        outcome, server=server, rollover3days_weekday=rollover3days_weekday
    )
    cost = build_cost_block(outcome)
    gov = build_governor_block(
        governor,
        limits=governor_limits,
        decision=governor_decision,
        day_anchor_equity=day_anchor_equity,
        reset_window_date=reset_window_date,
    )
    feats = dict(features) if features else None
    if holding is None and cost is None and gov is None and not feats:
        return None
    block: dict[str, Any] = {"contract_version": PACKET_ECONOMICS_CONTRACT_VERSION}
    if holding is not None:
        block["holding"] = holding
    if cost is not None:
        block["cost"] = cost
    if gov is not None:
        block["governor"] = gov
    if feats:
        block["features"] = feats
    return block


__all__ = [
    "PACKET_ECONOMICS_CONTRACT_VERSION",
    "MEASURED",
    "TRANSFERRED",
    "MODELLED",
    "UNAVAILABLE",
    "weakest",
    "rollover_nights_crossed",
    "build_holding_block",
    "build_cost_block",
    "build_governor_block",
    "build_economics_block",
]
