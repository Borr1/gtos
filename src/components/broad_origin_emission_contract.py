"""Emission-contract predicates for the broad-origin generator.

Two measured defects in `broader_origin_generators.py` share one root cause:
**a quantity compared in a unit the contract it governs does not use.**

1. **The POI admission radius.**  `_current_framework_proximity_tolerance`
   returns a FRACTION OF PRICE (default 0.01 = 1.0 % of price) and is the sole
   distance test admitting a POI zone (`broader_origin_generators.py:1200`,
   `:1390`, `:1445`).  The candidate it admits is denominated in R: entry at the
   zone midpoint, stop one buffer-ATR beyond the zone edge, target at
   ``entry +/- rr * risk``.  Measured median risk over the eight-window
   population is 7.41-8.91 bps, so the gate is **11.2-13.5 R wide on a 1.5 R
   trade** (phase20/receipts/R2_CENSUS_V1.json).  Consequence, measured on
   1,066,352 POI emissions: 26.19 % of ``current_breaker_re_entry`` and 0.13 %
   of ``current_ob_retest`` emissions are **born beyond their own stop** - the
   decision-instant price is already on the far side of the stop, so the limit
   is marketable by construction, fills 100 % of the time and books a
   mechanical -0.997 R gross / -1.304 R net.

2. **The selected-bar age.**  `_selected_closed_bar_open` walks back to the last
   closed bar with no maximum-age test, so across a session gap or a weekend the
   decision is priced off a bar that closed hours ago.  5.48 % of all emissions
   are decided that way; for at-market families the emitted entry IS that stale
   close, and the displacement to the next actual print is a median 1.08-2.77 R
   **already in the shortest stale bucket** (one missing bar).

This module holds the repaired predicates, denominated in the contract's own
units, as pure functions with no dependency on the generator.  Same bug class as
``time_stop_bars = 96`` (Session AQ, `phase11/SESSION_AQ_CONTRACT_TRUTH_RESULT.md`):
a conversion ratio sitting in a field that wanted the converted value.

Configuration.  Every key below is resolved from ``gtos_vnext_runtime`` and is
**absent from every committed config file**, so the code default is the shipped
behaviour and no config byte moves.  The past-stop and selected-bar-age defaults
are correctness repairs already established on main.  Session naming,
breaker-buffer routing, and completed-bar-only generation are separate forward
P1 research treatments: their defaults deliberately preserve current main and
they move behavior only when a caller declares the corresponding mode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from src.research_infra.wave21_full_flow_truth import (
    WAVE21_FULL_FLOW_TRUTH_MODE_KEY,
    wave21_full_flow_truth_mode_enabled,
)


RUNTIME_SECTION = "gtos_vnext_runtime"

#: Refuse to emit a POI limit whose stop the decision-instant price has already
#: breached.  Default ``True``.
REFUSE_PAST_STOP_KEY = "broad_origin_poi_refuse_past_stop"

#: Far-side R-denominated admission radius: refuse a POI limit whose
#: ``fill_gap_r`` is at or beyond this many risk units.  ``None`` disables the
#: far-side refusal (the candidate is still measured and marked).  Default
#: ``None``; setting it to the candidate's own ``target_rr`` implements
#: "the target must still be in front of the market".
MAX_ADMISSION_GAP_R_KEY = "broad_origin_poi_max_admission_gap_r"

#: Near-side R-denominated admission radius: refuse a POI limit whose
#: ``fill_gap_r`` is below this many risk units.  ``-1.0`` is the stop itself
#: and is enforced separately by ``refuse_past_stop`` because a breached stop is
#: a malformed order rather than a policy preference; ``0.0`` additionally
#: refuses already-marketable limits.  Default ``None``.
MIN_ADMISSION_GAP_R_KEY = "broad_origin_poi_min_admission_gap_r"

#: Maximum age of the selected closed bar at the decision instant, in units of
#: that timeframe's own period.  ``1.0`` means "no bar is missing between the
#: selected bar and now".  ``None`` disables the check (legacy).  Default ``1.0``.
MAX_SELECTED_BAR_AGE_PERIODS_KEY = "broad_origin_max_selected_bar_age_periods"

#: A 24-hour configured window is a continuous session, not the absence of a
#: session.  The legacy mode is retained only for exact evidence reproduction.
SESSION_NAMING_KEY = "broad_origin_session_naming"
SESSION_NAMING_CONTINUOUS = "continuous"
SESSION_NAMING_LEGACY_SENTINEL = "legacy_sentinel"
SESSION_NAMING_MODES = (SESSION_NAMING_CONTINUOUS, SESSION_NAMING_LEGACY_SENTINEL)

#: Which risk key owns current-breaker stop geometry.  ADR-006 created a
#: breaker-specific key; the legacy generator accidentally read the generic
#: ob-retest baseline instead.
BREAKER_STOP_BUFFER_SOURCE_KEY = "broad_origin_breaker_stop_buffer_source"
BREAKER_BUFFER_ADR006 = "adr006"
BREAKER_BUFFER_LEGACY_GENERIC = "legacy_generic"
BREAKER_BUFFER_SOURCES = (BREAKER_BUFFER_ADR006, BREAKER_BUFFER_LEGACY_GENERIC)

#: A named R-bound mode.  The numeric value is resolved per candidate so a
#: future family target does not silently inherit a hard-coded 1.5 R radius.
GAP_R_TARGET_RR = "target_rr"

#: Forming-bar generation is a research experiment.  ``True`` preserves the
#: historical generator contract; a raw comparator can explicitly set False to
#: run the completed-bar-only treatment without conflating it with other P1 arms.
ALLOW_FORMING_BAR_KEY = "broad_origin_forming_bar_enabled"

DEFAULT_REFUSE_PAST_STOP = True
DEFAULT_MAX_ADMISSION_GAP_R: float | str | None = None
DEFAULT_MIN_ADMISSION_GAP_R: float | str | None = None
DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS: float | None = 1.0
# Forward P1 treatments remain explicit research arms.  Their stored economic
# evidence is not a raw-generation proof for this revision, so absent keys must
# reproduce the current generator exactly.
DEFAULT_SESSION_NAMING = SESSION_NAMING_LEGACY_SENTINEL
DEFAULT_BREAKER_STOP_BUFFER_SOURCE = BREAKER_BUFFER_LEGACY_GENERIC
DEFAULT_ALLOW_FORMING_BAR = True
DEFAULT_WAVE21_FULL_FLOW_TRUTH_MODE = False

BIN_PAST_STOP = "past_stop"
BIN_MARKETABLE = "marketable"
BIN_RESTING = "resting"
BIN_TARGET_THROUGH = "target_through"
ADMISSION_BINS = (BIN_PAST_STOP, BIN_MARKETABLE, BIN_RESTING, BIN_TARGET_THROUGH)

REASON_OK = "poi_admission_within_own_risk_envelope"
REASON_DEGENERATE = "poi_admission_geometry_degenerate"
REASON_PAST_STOP = "poi_admission_refused_born_beyond_own_stop"
REASON_MAX_GAP_R = "poi_admission_refused_beyond_max_admission_gap_r"
REASON_MIN_GAP_R = "poi_admission_refused_inside_min_admission_gap_r"

STALE_BAR_REASON = "selected_closed_bar_older_than_max_age"
ADMISSION_PARTITION_SCHEMA = "gtos.broad_origin_poi_admission_partition.v1"


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


@dataclass(frozen=True)
class BroadOriginEmissionPolicy:
    """The resolved emission contract for one generation call."""

    refuse_past_stop: bool = DEFAULT_REFUSE_PAST_STOP
    max_admission_gap_r: float | str | None = DEFAULT_MAX_ADMISSION_GAP_R
    min_admission_gap_r: float | str | None = DEFAULT_MIN_ADMISSION_GAP_R
    max_selected_bar_age_periods: float | None = DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS
    session_naming: str = DEFAULT_SESSION_NAMING
    breaker_stop_buffer_source: str = DEFAULT_BREAKER_STOP_BUFFER_SOURCE
    allow_forming_bar: bool = DEFAULT_ALLOW_FORMING_BAR
    truth_mode_enabled: bool = DEFAULT_WAVE21_FULL_FLOW_TRUTH_MODE

    def to_dict(self) -> dict[str, Any]:
        return {
            REFUSE_PAST_STOP_KEY: self.refuse_past_stop,
            MAX_ADMISSION_GAP_R_KEY: self.max_admission_gap_r,
            MIN_ADMISSION_GAP_R_KEY: self.min_admission_gap_r,
            MAX_SELECTED_BAR_AGE_PERIODS_KEY: self.max_selected_bar_age_periods,
            SESSION_NAMING_KEY: self.session_naming,
            BREAKER_STOP_BUFFER_SOURCE_KEY: self.breaker_stop_buffer_source,
            ALLOW_FORMING_BAR_KEY: self.allow_forming_bar,
            WAVE21_FULL_FLOW_TRUTH_MODE_KEY: self.truth_mode_enabled,
        }

    def resolved_gap_bounds(self, target_rr: float) -> tuple[float | None, float | None]:
        return (
            _resolve_gap_bound(self.min_admission_gap_r, target_rr),
            _resolve_gap_bound(self.max_admission_gap_r, target_rr),
        )


#: The pre-repair contract, kept as a named object so evidence reproduction is a
#: policy choice a caller states rather than a set of magic literals.
LEGACY_EMISSION_POLICY = BroadOriginEmissionPolicy(
    refuse_past_stop=False,
    max_admission_gap_r=None,
    min_admission_gap_r=None,
    max_selected_bar_age_periods=None,
    session_naming=SESSION_NAMING_LEGACY_SENTINEL,
    breaker_stop_buffer_source=BREAKER_BUFFER_LEGACY_GENERIC,
    allow_forming_bar=True,
    truth_mode_enabled=False,
)


def _resolve_gap_bound(value: Any, target_rr: float) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.strip().lower() == GAP_R_TARGET_RR:
            rr = _finite(target_rr)
            return rr if rr is not None and rr > 0 else None
        return None
    return _finite(value)


def _resolve_choice(raw: Any, allowed: tuple[str, ...], default: str) -> str:
    if not isinstance(raw, str):
        return default
    text = raw.strip().lower()
    return text if text in allowed else default


def resolve_emission_policy(config: Any) -> BroadOriginEmissionPolicy:
    """Resolve the emission contract from ``gtos_vnext_runtime``.

    Unreadable values fall back to the code default rather than to the legacy
    behaviour: a typo must not silently restore a defect.
    """

    runtime = config.get(RUNTIME_SECTION) if isinstance(config, Mapping) else None
    runtime = runtime if isinstance(runtime, Mapping) else {}

    refuse = runtime.get(REFUSE_PAST_STOP_KEY, DEFAULT_REFUSE_PAST_STOP)
    refuse_past_stop = (
        bool(refuse) if isinstance(refuse, bool) else DEFAULT_REFUSE_PAST_STOP
    )

    max_gap_r: float | str | None = DEFAULT_MAX_ADMISSION_GAP_R
    if MAX_ADMISSION_GAP_R_KEY in runtime:
        raw = runtime.get(MAX_ADMISSION_GAP_R_KEY)
        if isinstance(raw, str):
            max_gap_r = (
                GAP_R_TARGET_RR
                if raw.strip().lower() == GAP_R_TARGET_RR
                else DEFAULT_MAX_ADMISSION_GAP_R
            )
        else:
            max_gap_r = None if raw is None else _finite(raw)
            if max_gap_r is not None and max_gap_r <= 0:
                max_gap_r = DEFAULT_MAX_ADMISSION_GAP_R

    min_gap_r: float | str | None = DEFAULT_MIN_ADMISSION_GAP_R
    if MIN_ADMISSION_GAP_R_KEY in runtime:
        raw = runtime.get(MIN_ADMISSION_GAP_R_KEY)
        if isinstance(raw, str):
            min_gap_r = (
                GAP_R_TARGET_RR
                if raw.strip().lower() == GAP_R_TARGET_RR
                else DEFAULT_MIN_ADMISSION_GAP_R
            )
        else:
            min_gap_r = None if raw is None else _finite(raw)

    max_age: float | None = DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS
    if MAX_SELECTED_BAR_AGE_PERIODS_KEY in runtime:
        raw = runtime.get(MAX_SELECTED_BAR_AGE_PERIODS_KEY)
        if raw is None:
            max_age = None
        else:
            parsed = _finite(raw)
            max_age = parsed if parsed is not None and parsed > 0 else (
                DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS
            )

    truth_mode_enabled = wave21_full_flow_truth_mode_enabled(config)
    allow_forming_bar = (
        runtime.get(ALLOW_FORMING_BAR_KEY)
        if isinstance(runtime.get(ALLOW_FORMING_BAR_KEY), bool)
        else DEFAULT_ALLOW_FORMING_BAR
    )

    return BroadOriginEmissionPolicy(
        refuse_past_stop=refuse_past_stop,
        max_admission_gap_r=max_gap_r,
        min_admission_gap_r=min_gap_r,
        max_selected_bar_age_periods=max_age,
        session_naming=_resolve_choice(
            runtime.get(SESSION_NAMING_KEY),
            SESSION_NAMING_MODES,
            DEFAULT_SESSION_NAMING,
        ),
        breaker_stop_buffer_source=_resolve_choice(
            runtime.get(BREAKER_STOP_BUFFER_SOURCE_KEY),
            BREAKER_BUFFER_SOURCES,
            DEFAULT_BREAKER_STOP_BUFFER_SOURCE,
        ),
        allow_forming_bar=False if truth_mode_enabled else allow_forming_bar,
        truth_mode_enabled=truth_mode_enabled,
    )


def fill_gap_r(
    *,
    side: str,
    entry_price: Any,
    stop_loss: Any,
    current_price: Any,
) -> float | None:
    """Signed distance from the limit to the market, in the trade's OWN risk unit.

    ``fill_gap_r = (current_price - entry) / risk`` for a LONG, negated for a
    SHORT.  It partitions the whole contract:

    ======================  ====================================================
    ``fill_gap_r < -1``     the market is already beyond the stop
    ``-1 <= gap < 0``       the limit is marketable: it fills NOW, at the market
                            rather than at the limit price
    ``0 <= gap < rr``       the intended resting limit
    ``gap >= rr``           the target is already behind the market
    ======================  ====================================================

    ``gap >= rr`` and "current price is at or past the take-profit" are the same
    statement algebraically, which is why the whole gate can be written in price
    terms as ``stop < current_price < target``.

    **Two limits on the marketable bin, corrected by the v1 verification lane, wave
    20** (`phase20/SESSION_V1_VERIFICATION.md` §5.4).  (1) That bin used to read
    "fills now, *worse* than limit"; it is the other way round -- a buyer filled
    below their own buy limit, or a seller filled above their sell limit, gets a
    price at least as good.  (2) The estate's walkers fill a marketable limit AT the
    limit price, so every economic number over that bin -- including the
    ``-1.30135 R/row`` this module's own refusal is priced at -- is a property of
    that convention, not of money.  Refusing a ``gap < -1`` order needs no economic
    argument (it is malformed), but do not read the saving as realised P&L.

    ``current_price`` is the SELECTED BAR'S CLOSE, and that close is the **bid**
    (`walkforward/quote_side.py`, settled on 87,060 M15 and 820,452 M1 bars).  A
    short's sell limit transacts on the bid, so this test is exact for shorts; a
    long's buy limit transacts on the ask, so the strictly-malformed boundary for a
    long is ``gap < -1 - spread/risk``.  Measured over the whole POI population that
    costs **92 over-refusals in 25,243 (0.36 %)**, and all 92 had their stop breached
    on the quote the stop is watched on anyway
    (`phase20/receipts/v1/V1_R1xR2_COMPOSE_V1.json`).
    """

    entry = _finite(entry_price)
    stop = _finite(stop_loss)
    price = _finite(current_price)
    if entry is None or stop is None or price is None:
        return None
    risk = abs(entry - stop)
    if not risk > 0:
        return None
    sign = 1.0 if str(side or "").upper() == "LONG" else -1.0
    return (price - entry) / risk * sign


def admission_bin(gap_r: float | None, target_rr: float) -> str | None:
    if gap_r is None:
        return None
    if gap_r < -1.0:
        return BIN_PAST_STOP
    if gap_r < 0.0:
        return BIN_MARKETABLE
    if gap_r < target_rr:
        return BIN_RESTING
    return BIN_TARGET_THROUGH


def evaluate_poi_admission(
    *,
    side: str,
    entry_price: Any,
    stop_loss: Any,
    current_price: Any,
    target_rr: float,
    policy: BroadOriginEmissionPolicy,
) -> dict[str, Any]:
    """Decide whether a POI limit may be emitted, in the trade's own risk unit."""

    gap = fill_gap_r(
        side=side,
        entry_price=entry_price,
        stop_loss=stop_loss,
        current_price=current_price,
    )
    if gap is None:
        return {
            "fill_gap_r": None,
            "admission_bin": None,
            "admit": False,
            "reason": REASON_DEGENERATE,
        }
    bucket = admission_bin(gap, target_rr)
    min_gap_r, max_gap_r = policy.resolved_gap_bounds(target_rr)
    if policy.refuse_past_stop and gap < -1.0:
        return {
            "fill_gap_r": gap,
            "admission_bin": bucket,
            "admit": False,
            "reason": REASON_PAST_STOP,
        }
    if min_gap_r is not None and gap < min_gap_r:
        return {
            "fill_gap_r": gap,
            "admission_bin": bucket,
            "admit": False,
            "reason": REASON_MIN_GAP_R,
        }
    if max_gap_r is not None and gap >= max_gap_r:
        return {
            "fill_gap_r": gap,
            "admission_bin": bucket,
            "admit": False,
            "reason": REASON_MAX_GAP_R,
        }
    return {
        "fill_gap_r": gap,
        "admission_bin": bucket,
        "admit": True,
        "reason": REASON_OK,
    }


def selected_bar_age_admissible(
    *,
    age_seconds: float,
    timeframe_minutes: float,
    policy: BroadOriginEmissionPolicy,
) -> bool:
    """Is the selected closed bar recent enough to price a decision against?

    ``age_seconds`` is ``now - (bar_open + one timeframe period)``: zero when the
    bar that just closed is the selected one, one period per missing bar.  The
    default budget of one period means "no bar is missing", which is the only
    threshold the data supports - displacement is already a median 1.08-2.77 R
    at a single missing bar.
    """

    if policy.max_selected_bar_age_periods is None:
        return True
    period = float(timeframe_minutes) * 60.0
    if not period > 0:
        return True
    return float(age_seconds) < period * policy.max_selected_bar_age_periods


__all__ = [
    "ADMISSION_BINS",
    "ADMISSION_PARTITION_SCHEMA",
    "ALLOW_FORMING_BAR_KEY",
    "BIN_MARKETABLE",
    "BIN_PAST_STOP",
    "BIN_RESTING",
    "BIN_TARGET_THROUGH",
    "BREAKER_BUFFER_ADR006",
    "BREAKER_BUFFER_LEGACY_GENERIC",
    "BREAKER_BUFFER_SOURCES",
    "BREAKER_STOP_BUFFER_SOURCE_KEY",
    "BroadOriginEmissionPolicy",
    "DEFAULT_ALLOW_FORMING_BAR",
    "DEFAULT_BREAKER_STOP_BUFFER_SOURCE",
    "DEFAULT_MAX_ADMISSION_GAP_R",
    "DEFAULT_MAX_SELECTED_BAR_AGE_PERIODS",
    "DEFAULT_MIN_ADMISSION_GAP_R",
    "DEFAULT_REFUSE_PAST_STOP",
    "DEFAULT_SESSION_NAMING",
    "DEFAULT_WAVE21_FULL_FLOW_TRUTH_MODE",
    "GAP_R_TARGET_RR",
    "LEGACY_EMISSION_POLICY",
    "MAX_ADMISSION_GAP_R_KEY",
    "MAX_SELECTED_BAR_AGE_PERIODS_KEY",
    "MIN_ADMISSION_GAP_R_KEY",
    "REASON_DEGENERATE",
    "REASON_MAX_GAP_R",
    "REASON_MIN_GAP_R",
    "REASON_OK",
    "REASON_PAST_STOP",
    "REFUSE_PAST_STOP_KEY",
    "RUNTIME_SECTION",
    "SESSION_NAMING_CONTINUOUS",
    "SESSION_NAMING_KEY",
    "SESSION_NAMING_LEGACY_SENTINEL",
    "SESSION_NAMING_MODES",
    "STALE_BAR_REASON",
    "WAVE21_FULL_FLOW_TRUTH_MODE_KEY",
    "admission_bin",
    "evaluate_poi_admission",
    "fill_gap_r",
    "resolve_emission_policy",
    "selected_bar_age_admissible",
]
