"""Frozen funnel feature/eligibility contract for the forward-shadow lane.

Everything in this module mirrors, field for field, the committed February r2
scorer (`docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/
outcome_authority/w21_score_feb_market_top_r2.py`, ``feature_row``) and the
frozen rule `MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json`.  The shadow builds
the same 43 model features from DECISION-TIME fields only — no label, no
outcome, no postdecision input.  The parity harness re-derives the same rows
through the committed research scorer bytes and diffs them; any edit here that
is not also proven equivalent there breaks the lane's acceptance test.

Deliberately dependency-light: stdlib + math only (host-local).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

SCHEMA = "gtos.wave21.forward_shadow.feature_contract.v1"

# Frozen rule constants (MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json).
RULE_PAYLOAD_SHA256 = (
    "2625d29f3dfb2c242a2b0a5b413754282c85776059f9eaa5d0422f1382e72720"
)
MAX_COST_R = 0.20
MIN_EXPECTED_NET_R = 0.10
PENDING_EXPIRY_MINUTES = 120

# The funnel's native order-type projection (candidate_funnel_analysis.py).
LIMIT_FAMILIES = frozenset(
    {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
)

# Bar-3 ratification (2026-08-11): the rule scoped to this family is the
# PRIMARY deployable object; the general rule is the research track.  The
# shadow computes BOTH selections each window (see BAR3_RATIFICATION_20260811
# in outcome_authority once landed on main).
LSR_FAMILY = "liquidity_sweep_reclaim"
LANE_GENERAL = "general"
LANE_SCOPED_LSR = "scoped_lsr"

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "symbol",
    "side",
    "origin_family",
    "utc_session",
    "proposed_order_type",
    "utc_hour",
    "weekday",
    "symbol_x_family",
    "family_x_session",
    "symbol_x_side",
    "poi_mitigation_status",
    "limit_marketable_at_decision",
    "trend_state_m15",
    "trend_transition_flag",
)

NUMERIC_FEATURES: tuple[str, ...] = (
    "cost_r",
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
    "distance_to_limit_atr",
    "distance_to_limit_risk",
    "risk_over_atr",
    "risk_fraction_of_entry",
    "poi_age_hours",
    "poi_distance_to_midpoint_atr",
    "poi_distance_to_zone_atr",
    "poi_touch_count",
    "poi_max_mitigation_fraction",
    "poi_touch_episode_count",
    "poi_overlap_bar_count",
    "atr14_over_atr50",
    "stop_distance_atr",
    "target_distance_atr",
    "close_position_in_lookback_range",
    "dist_to_prior_high20_atr",
    "dist_to_prior_low20_atr",
    "trigger_bar_range_atr",
    "trigger_bar_body_atr",
    "compression_ratio_prior_bar",
    "bars_since_session_open",
    "close_to_close_vol_8_over_48",
    "sweep_depth_atr",
    "session_open_range_width_atr",
)

# The generator's predecision-feature contract keys (broader_origin_generators
# .PREDECISION_FEATURE_KEYS).  Kept as a literal so the VPS runtime can verify a
# candidate's contract without importing anything heavy; a unit test pins this
# tuple against the production module.
PREDECISION_FEATURE_KEYS: tuple[str, ...] = (
    "atr14_over_atr50",
    "stop_distance_atr",
    "target_distance_atr",
    "close_position_in_lookback_range",
    "trend_state_m15",
    "trend_transition_flag",
    "dist_to_prior_high20_atr",
    "dist_to_prior_low20_atr",
    "trigger_bar_range_atr",
    "trigger_bar_body_atr",
    "compression_ratio_prior_bar",
    "bars_since_session_open",
    "close_to_close_vol_8_over_48",
    "sweep_depth_atr",
    "session_open_range_width_atr",
)

_PREDECISION_NUMERIC_KEYS = tuple(
    key
    for key in PREDECISION_FEATURE_KEYS
    if key not in {"trend_state_m15", "trend_transition_flag"}
)

# ---------------------------------------------------------------------------
# ATR basis (foundation repair, 2026-08-12)
# ---------------------------------------------------------------------------
# `risk_over_atr` above divides by `fillability["atr14"]`, and until this repair
# nothing said what an "ATR-14" was here.  Measured on the sealed 2026 corpus
# (ops/receipts/ATR_FOUNDATION_V1.json) the answer is TWO estimators on ONE
# timeframe:
#
#   basis A  "M15|high_low_mean_14"     the 7 single-symbol families
#   basis B  "M15|wilder_true_range_14" current_fvg_fill / current_ob_retest /
#                                       current_breaker_re_entry
#
# Every same-basis family pair agrees to the bit at a shared decision minute;
# no cross-basis pair ever does.  The two disagree by a median 1.7 % with 41.8 %
# of decision-cells outside +/-10 %, which flips 5.28 % of basis-B rows across a
# 0.75 threshold.  The timeframe is M15 for all ten -- the defect is the
# estimator, not the clock.
#
# THE FROZEN FEATURE IS NOT RE-POINTED.  `risk_over_atr` keeps its exact
# as-shipped meaning because it is a live input to the wave-21 ridge; silently
# changing it would change that model's inputs without a refit.  The repaired
# quantity ships BESIDE it as `risk_over_atr_v2`, is absent from
# NUMERIC_FEATURES, and is therefore invisible to the current model by
# construction.  PROMOTING IT TO A MODEL INPUT REQUIRES A FULL REFIT of the
# ridge (daily_refit.py) plus a new ridge artifact; it is not a drop-in swap.
ATR_BASIS_M15_WILDER_TRUE_RANGE_14 = "M15|wilder_true_range_14"
ATR_BASIS_M15_HIGH_LOW_MEAN_14 = "M15|high_low_mean_14"

#: The single declared denominator `risk_over_atr_v2` is expressed in.
DECLARED_COMMON_ATR_BASIS = ATR_BASIS_M15_HIGH_LOW_MEAN_14

#: Emitted when the basis cannot be established.  Fail-closed: `risk_over_atr_v2`
#: is NaN and the basis reads `unavailable` rather than being assumed.
ATR_BASIS_UNAVAILABLE = "unavailable"


class FeatureContractError(ValueError):
    """A shadow candidate row violates the frozen funnel feature contract."""


def at_utc(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FeatureContractError(f"naive timestamp in shadow row: {value!r}")
    return parsed.astimezone(timezone.utc)


def number(value: Any) -> float:
    """Mirror of the r2 scorer's ``number``: non-finite/unparseable -> NaN."""

    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def resolve_atr_common_basis(
    raw: Mapping[str, Any], fillability: Mapping[str, Any]
) -> tuple[float, str]:
    """Return ``(atr_on_declared_common_basis, basis_actually_used)``.

    Resolution order, fail-closed at every step:

    1. an explicit ``atr14_common_basis_value`` whose declared
       ``atr14_common_basis`` matches :data:`DECLARED_COMMON_ATR_BASIS`;
    2. the raw ``atr14`` **only when** its own ``atr14_basis`` already equals the
       declared common basis -- i.e. the candidate was natively on it;
    3. otherwise NaN with basis :data:`ATR_BASIS_UNAVAILABLE`.

    Step 2 is the whole point of the labelling work: an unlabelled ``atr14`` is
    NEVER accepted as if it were on the common basis, because for three of the
    ten families it is not, and accepting it is precisely the silent regression
    this repair exists to prevent.
    """

    sources: tuple[Mapping[str, Any], ...] = tuple(
        m
        for m in (
            fillability,
            raw,
            raw.get("source_fields") if isinstance(raw.get("source_fields"), Mapping) else None,
            raw.get("candidate_source_fields")
            if isinstance(raw.get("candidate_source_fields"), Mapping)
            else None,
        )
        if isinstance(m, Mapping)
    )

    def first(key: str) -> Any:
        for m in sources:
            if m.get(key) is not None:
                return m.get(key)
        return None

    declared = str(first("atr14_common_basis") or "").strip()
    value = number(first("atr14_common_basis_value"))
    if declared == DECLARED_COMMON_ATR_BASIS and math.isfinite(value) and value > 0:
        return value, DECLARED_COMMON_ATR_BASIS

    native_basis = str(first("atr14_basis") or "").strip()
    native = number(first("atr14"))
    if (
        native_basis == DECLARED_COMMON_ATR_BASIS
        and math.isfinite(native)
        and native > 0
    ):
        return native, DECLARED_COMMON_ATR_BASIS

    return math.nan, ATR_BASIS_UNAVAILABLE


def order_type_for_family(origin_family: str) -> str:
    """Mirror of candidate_funnel_analysis._order_type (native intent)."""

    return "LIMIT" if origin_family in LIMIT_FAMILIES else "MARKET"


def expiry_for_decision(decision_time: datetime) -> datetime:
    return decision_time + timedelta(minutes=PENDING_EXPIRY_MINUTES)


def shadow_feature_row(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Build the frozen 43-feature model row from a decision-time raw row.

    ``raw`` is the shadow's candidate record: the generator/enrichment output
    plus the live-stamped cost fields.  This mirrors the committed r2 scorer's
    ``feature_row(raw, label)`` exactly, except that label-only fields
    (lifecycle status, terminal net R) do not exist yet at decision time and
    the identity fields are taken from the raw row itself.
    """

    when = at_utc(raw["decision_time_utc"])
    family = str(raw["origin_family"])
    symbol = str(raw["symbol"])
    side = str(raw["side"]).upper()
    session = str(raw.get("session_bucket") or raw.get("session") or "unknown")
    fillability = raw.get("predecision_limit_fillability")
    fillability = fillability if isinstance(fillability, dict) else {}
    poi = raw.get("poi_state")
    poi = poi if isinstance(poi, dict) else {}
    source_features = raw.get("predecision_features")
    if not isinstance(source_features, dict) or set(source_features) != set(
        PREDECISION_FEATURE_KEYS
    ):
        raise FeatureContractError(
            "predecision feature contract missing: "
            f"{raw.get('candidate_occurrence_key') or raw.get('canonical_replay_candidate_instance_key')}"
        )
    risk = abs(number(raw.get("entry_price")) - number(raw.get("stop_loss")))
    atr = number(fillability.get("atr14"))
    atr_common, atr_common_basis = resolve_atr_common_basis(raw, fillability)
    entry = abs(number(raw.get("entry_price")))
    expiry = at_utc(raw["limit_first_expiry_utc"])
    row = {
        "candidate_occurrence_key": str(
            raw.get("canonical_replay_candidate_instance_key")
            or raw.get("candidate_occurrence_key")
            or ""
        ),
        "candidate_id": str(raw.get("candidate_id") or ""),
        "decision_window_id": str(raw["decision_window_id"]),
        "trading_day": str(raw["trading_day"]),
        # At decision time the label span has not started resolving; the frozen
        # selector orders windows by label_span_start == submission time, which
        # is the decision time.  This is the same value the research labeler
        # stamps (candidate_funnel_analysis._lifecycle_row: label_span_start_utc
        # = submission.isoformat()).
        "label_span_start_utc": when.isoformat(),
        "label_span_end_utc": None,
        "expiry_utc": expiry.isoformat(),
        "predecision_geometry_valid": bool(when < expiry and risk > 0),
        "symbol": symbol,
        "side": side,
        "origin_family": family,
        "utc_session": session,
        "proposed_order_type": order_type_for_family(family),
        "utc_hour": f"{when.hour:02d}",
        "weekday": str(when.weekday()),
        "symbol_x_family": symbol + "|" + family,
        "family_x_session": family + "|" + session,
        "symbol_x_side": symbol + "|" + side,
        "poi_mitigation_status": str(
            raw.get("poi_mitigation_status")
            or poi.get("poi_mitigation_status")
            or "not_applicable"
        ),
        "limit_marketable_at_decision": str(
            bool(fillability.get("limit_marketable_at_decision"))
        ),
        "trend_state_m15": str(source_features.get("trend_state_m15") or "MISSING"),
        "trend_transition_flag": str(source_features.get("trend_transition_flag")),
        "cost_r": number(raw.get("cost_r")),
        "spread_r": number(raw.get("spread_r")),
        "expected_slippage_r": number(raw.get("expected_slippage_r")),
        "swap_cost_r": number(raw.get("swap_cost_r")),
        "commission_r": number(raw.get("commission_r")),
        "distance_to_limit_atr": number(fillability.get("distance_to_limit_atr")),
        "distance_to_limit_risk": number(fillability.get("distance_to_limit_risk")),
        # FROZEN. Whatever basis the generator happened to put in
        # fillability["atr14"] -- basis A for seven families, basis B for three.
        # Live ridge input; not re-pointed. See the ATR-basis note above.
        "risk_over_atr": risk / atr
        if math.isfinite(risk) and math.isfinite(atr) and atr > 0
        else math.nan,
        # The basis `risk_over_atr` above is actually denominated in, so the
        # frozen feature is no longer silently ambiguous even though its VALUE
        # is unchanged.
        "risk_over_atr_basis": str(
            fillability.get("atr14_basis")
            or (
                raw.get("atr14_basis")
                if isinstance(raw.get("atr14_basis"), str)
                else None
            )
            or ATR_BASIS_UNAVAILABLE
        ),
        # REPAIRED, versioned, and NOT a model input (absent from
        # NUMERIC_FEATURES).  One declared denominator for all ten families, so
        # a threshold on it means the same thing in each.  NaN when the basis
        # cannot be established -- never silently substituted.
        "risk_over_atr_v2": risk / atr_common
        if math.isfinite(risk) and math.isfinite(atr_common) and atr_common > 0
        else math.nan,
        "risk_over_atr_v2_basis": atr_common_basis,
        "risk_fraction_of_entry": risk / entry
        if math.isfinite(risk) and math.isfinite(entry) and entry > 0
        else math.nan,
        "poi_age_hours": number(raw.get("poi_age_hours", poi.get("poi_age_hours"))),
        "poi_distance_to_midpoint_atr": number(raw.get("poi_distance_to_midpoint_atr")),
        "poi_distance_to_zone_atr": number(raw.get("poi_distance_to_zone_atr")),
        "poi_touch_count": number(
            raw.get("poi_touch_count", poi.get("poi_touch_count"))
        ),
        "poi_max_mitigation_fraction": number(poi.get("poi_max_mitigation_fraction")),
        "poi_touch_episode_count": number(poi.get("poi_touch_episode_count")),
        "poi_overlap_bar_count": number(poi.get("poi_overlap_bar_count")),
        **{key: number(source_features.get(key)) for key in _PREDECISION_NUMERIC_KEYS},
    }
    return row


def eligible(row: Mapping[str, Any], *, cost_complete: bool) -> tuple[bool, str | None]:
    """Frozen eligibility: geometry-valid + FINITE COMPLETE cost <= 0.2R.

    ``cost_complete`` is the shadow's fail-closed cost verdict (the four
    components summed by the pretrade packet; a refused/incomplete packet is
    ineligible, never defaulted — rule clause
    ``missing_or_incomplete_cost_is_ineligible_not_zero``).
    """

    if not row["predecision_geometry_valid"]:
        return False, "geometry_invalid"
    if not cost_complete:
        return False, "cost_incomplete_fail_closed"
    cost = row["cost_r"]
    if not (isinstance(cost, float) and math.isfinite(cost)):
        return False, "cost_not_finite"
    if cost > MAX_COST_R:
        return False, "cost_above_0p20"
    return True, None
