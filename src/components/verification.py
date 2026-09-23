"""Level 2 Candidate Verification.

Deterministic checks that verify the AI's CANDIDATE output against
the Market State Object source data. Catches:
- Hallucinated order blocks (AI cites OB that doesn't exist in MSO)
- Threshold violations (displacement below minimum)
- Zone misclassification (OB not in correct premium/discount zone)
- Parameter errors (entry outside OB, SL inside OB)

This is NOT a replacement for Gate 1 safety checks. Gate 1 checks
trade parameters (RR, SL floor, direction). Level 2 checks that the
AI's structural claims are grounded in actual MSO data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from src.components import sl_beyond_ob_shadow_logger as _sl_shadow
from src.components.precision import _decimals_from_format, _snap_to_precision
from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.market_state_models import (
    BreakerBlock,
    FairValueGap,
    MarketStateObject,
    OrderBlock,
)

logger = logging.getLogger(__name__)


def _resolve_display_decimals(config: dict, default: int = 2) -> int:
    """Return the per-instrument display decimal-count for AI prices.

    Mirrors the lookup in ``_check_sl_beyond_ob`` (verification.py:862)
    and ``primary_analyzer.PrimaryAnalyzer.analyze`` (HALLUC-1 fix). Used
    by the SISTER-1/2/4/5 fixes to snap MSO underlying floats
    (``BreakerBlock.zone_low/high``, ``FairValueGap.bottom/top``) to the
    same precision plane the AI was shown before performing strict ``<=``
    / ``>=`` comparisons on AI-emitted SL.

    Falls back to *default* (2) when the config block is missing or the
    format is unrecognized — preserves XAUUSD-style legacy behavior so
    older test fixtures without a ``prompt.price_format`` keep passing.
    """
    fmt = config.get("prompt", {}).get("price_format") if isinstance(config, dict) else None
    decimals = _decimals_from_format(fmt)
    return decimals if decimals is not None else default


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class VerificationCheck:
    name: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    detail: str
    mso_value: Any = None
    ai_value: Any = None


@dataclass
class VerificationResult:
    passed: bool  # True only if ALL checks are PASS, WARN, or SKIP
    checks: list[VerificationCheck] = field(default_factory=list)
    blocked_by: Optional[str] = None  # name of first failed check
    # Target POI that the verifier matched — exposed so downstream callers
    # (trade_capture instrumentation) can snapshot target_ob_touch_count and
    # target_ob_zone at CAND time. None when no H1 POI matched.
    matched_ob: Optional[OrderBlock] = None
    matched_breaker: Optional[BreakerBlock] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _direction_for_trade(direction: str) -> str:
    """Map LONG/SHORT → bullish/bearish."""
    return "bullish" if direction == "LONG" else "bearish"


def _find_matching_ob(
    order_blocks: list[OrderBlock],
    poi_price: float,
    tolerance: float,
) -> Optional[OrderBlock]:
    """Find an unmitigated OB whose zone contains *poi_price* within tolerance."""
    for ob in order_blocks:
        if ob.mitigated:
            continue
        if ob.low - tolerance <= poi_price <= ob.high + tolerance:
            return ob
    return None


def _find_matching_breaker(
    breakers: list[BreakerBlock],
    poi_price: float,
    tolerance: float,
    required_direction: str,
) -> Optional[BreakerBlock]:
    """Find an unretested breaker whose zone contains *poi_price*."""
    for bb in breakers:
        if bb.is_retested:
            continue
        if bb.direction != required_direction:
            continue
        if bb.zone_low - tolerance <= poi_price <= bb.zone_high + tolerance:
            return bb
    return None


def _find_matching_fvg(
    fvgs: list[FairValueGap],
    poi_price: float,
    tolerance: float,
    required_type: str,
) -> Optional[FairValueGap]:
    """Find an unfilled FVG (bullish/bearish) whose range contains *poi_price*.

    *required_type* is "bullish" (for LONG fvg_fill) or "bearish" (for SHORT).
    The AI cites the FVG midpoint; we accept any unfilled FVG whose range
    [bottom, top] envelopes the cited midpoint within tolerance. This handles
    minor float-rounding without admitting mismatches across distinct FVGs.
    """
    for fvg in fvgs:
        if fvg.filled:
            continue
        if fvg.type != required_type:
            continue
        if fvg.bottom - tolerance <= poi_price <= fvg.top + tolerance:
            return fvg
    return None


def _ob_tolerance(price: float, config: dict) -> float:
    """Compute price tolerance for OB matching from config."""
    pct = config.get("verification", {}).get("ob_price_tolerance_pct", 0.002)
    return price * pct


def _sl_beyond_floor(price: float, config: dict) -> float:
    """Compute the minimum geometric distance SL must clear OB boundary.

    Returns ``max(broker_stops_level_proxy, configured tick floor)``. Default
    floor is ``1`` instrument tick. Per-instrument override via
    ``verification.sl_beyond_ob_tick_floor`` in agent_config or profile.

    *price* is reserved for a future broker-stops-level proxy (currently
    unused — we only return the tick-floor product). Quantization-aware:
    falls back to ``prompt.tick_size_fallback`` (default 1e-5) only when
    ``market.tick_size`` is missing or non-positive.
    """
    tick = float(config.get("market", {}).get("tick_size") or 0.0)
    if tick <= 0:
        tick = float(config.get("prompt", {}).get("tick_size_fallback", 1e-5))
    floor_ticks = int(config.get("verification", {}).get(
        "sl_beyond_ob_tick_floor", 1
    ))
    return tick * floor_ticks


# ---------------------------------------------------------------------------
# Multi-framework dispatch routing (HALLUC-1 / GBPJPY 2026-04-28 fix)
# ---------------------------------------------------------------------------

# Map h1_setup.poi_type values to canonical framework names. Used as a
# tiebreaker when multiple frameworks_evaluated entries are qualified=true.
_POI_TYPE_TO_FRAMEWORK = {
    "OB": "ob_retest",
    "FVG": "fvg_fill",
    "breaker_block": "breaker_re_entry",
}


def _compute_effective_framework(
    analysis: PrimaryAnalysisOutput,
) -> tuple[str, bool, dict]:
    """Defense-in-depth multi-framework dispatch routing.

    Routes the L2 verification on the AI's per-framework ``qualified``
    flags rather than the wrapper-level ``analysis.framework`` field. The
    wrapper field is biased by the user-message phrasing (pre-2026-04-28:
    "for the OB Retest setup") and observed to disagree with the AI's
    actual qualification reasoning under multi-framework dispatch — see
    ``research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md`` for the
    GBPJPY 2026-04-28 01:30 smoking gun.

    Algorithm:
      1. Start from ``analysis.framework`` (the wrapper-emitted label).
      2. If ``frameworks_evaluated[wrapper].qualified == False`` AND any
         OTHER framework has ``qualified == True``, override
         ``effective_framework`` to that qualified framework.
      3. If multiple frameworks are qualified (multi-qualified case),
         prefer the one matching ``h1_setup.poi_type``
         (FVG → fvg_fill, OB → ob_retest, breaker_block →
         breaker_re_entry). Falls back to the wrapper if poi_type does
         not disambiguate.

    Returns
    -------
    effective_framework : str
        The framework the L2 routing should use. Equal to
        ``analysis.framework`` whenever the wrapper agrees with the
        qualification flags, the qualification flags are absent, or the
        analysis lacks a wrapper framework.
    was_overridden : bool
        ``True`` iff ``effective_framework != analysis.framework`` AND
        the override was driven by the qualification flags. ``False``
        when the wrapper-and-qualification flags agree, or when the
        qualification flags are missing/empty (no override possible).
    routing_decision : dict
        Audit-trail payload with keys ``wrapper_framework``,
        ``effective_framework``, ``was_overridden``,
        ``frameworks_qualified`` (list[str]), and ``reason`` (str).
        Stored in the resulting ``VerificationCheck.details`` so the
        decision is preserved in the trade record.
    """
    wrapper = getattr(analysis, "framework", None) or "none"
    frameworks_eval = getattr(analysis, "frameworks_evaluated", None) or {}

    # Build the set of qualified frameworks. Tolerant of dicts and Pydantic
    # FrameworkEvaluation models — we duck-type the ``qualified`` attribute.
    qualified_set: list[str] = []
    for fw_name, fw_eval in frameworks_eval.items():
        if fw_eval is None:
            continue
        flag = getattr(fw_eval, "qualified", None)
        if flag is None and isinstance(fw_eval, dict):
            flag = fw_eval.get("qualified")
        if flag:
            qualified_set.append(fw_name)

    routing_decision: dict = {
        "wrapper_framework": wrapper,
        "effective_framework": wrapper,
        "was_overridden": False,
        "frameworks_qualified": list(qualified_set),
        "reason": "wrapper_used",
    }

    # No qualifications surfaced — fall back to wrapper. This preserves
    # bit-identical behavior on every analysis emitted before
    # frameworks_evaluated existed.
    if not qualified_set:
        routing_decision["reason"] = "no_qualified_flags"
        return wrapper, False, routing_decision

    # Helper: read h1_setup.poi_type → canonical framework name.
    def _poi_type_framework() -> str | None:
        reasoning = getattr(analysis, "reasoning", None)
        if reasoning is None:
            return None
        h1 = getattr(reasoning, "h1_setup", None)
        if h1 is None:
            return None
        poi_type = getattr(h1, "poi_type", None)
        return _POI_TYPE_TO_FRAMEWORK.get(poi_type or "")

    # Multi-qualified — apply the poi_type tiebreaker FIRST (per brief).
    # The AI's h1_setup.poi_type is the most reliable signal of which
    # framework the AI's reasoning actually fired on, even when the
    # wrapper-level field disagrees and even when multiple flags read
    # qualified=true (the GBPJPY 2026-04-28 01:30 smoking-gun signature:
    # both flags qualified=true, wrapper=ob_retest, but poi_type=FVG and
    # overall_reasoning explicitly names fvg_fill).
    if len(qualified_set) >= 2:
        poi_framework = _poi_type_framework()
        if poi_framework and poi_framework in qualified_set:
            if poi_framework == wrapper:
                routing_decision["reason"] = "multi_qualified_wrapper_matches_poi_type"
                return wrapper, False, routing_decision
            routing_decision["effective_framework"] = poi_framework
            routing_decision["was_overridden"] = True
            routing_decision["reason"] = "multi_qualified_poi_type_match"
            return poi_framework, True, routing_decision

        # poi_type does not disambiguate. If wrapper is in the qualified
        # set, defer to wrapper (preserves legacy behavior); otherwise
        # pick deterministically by sorted name.
        if wrapper in qualified_set:
            routing_decision["reason"] = "multi_qualified_wrapper_kept"
            return wrapper, False, routing_decision

        effective = sorted(qualified_set)[0]
        routing_decision["effective_framework"] = effective
        routing_decision["was_overridden"] = True
        routing_decision["reason"] = "multi_qualified_alphabetical_fallback"
        return effective, True, routing_decision

    # Single qualified path.
    only_qualified = qualified_set[0]
    if only_qualified == wrapper:
        # Wrapper agrees with the sole qualified framework — keep.
        routing_decision["reason"] = "wrapper_qualified"
        return wrapper, False, routing_decision

    # Wrapper disagrees: NOT in the qualified set. Override.
    routing_decision["effective_framework"] = only_qualified
    routing_decision["was_overridden"] = True
    routing_decision["reason"] = "wrapper_disagrees_single_qualified"
    return only_qualified, True, routing_decision


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_m15_choch(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
) -> VerificationCheck:
    """CHECK 1: M15 CHoCH with displacement exists in MSO."""
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck(
            "m15_choch_exists", "FAIL",
            "No trade_parameters — cannot determine direction",
        )

    required_dir = _direction_for_trade(tp.direction)
    m15_tf = mso.timeframes.get("M15")
    if m15_tf is None:
        return VerificationCheck(
            "m15_choch_exists", "FAIL",
            "No M15 timeframe data in MSO",
        )

    # Iterate newest-first so the reported event is the triggering one, not
    # a stale week-old match buried at the start of the list.  PASS/FAIL is
    # unchanged (any qualifying event produces PASS), but mso_value/time/ratio
    # now reflect the decision-relevant event.  See Thursday 2026-04-23 US30
    # audit (research/thursday_2026-04-23_analysis/US30_analysis.md §8 #6).
    for event in reversed(m15_tf.structure_events):
        if event.type == "CHoCH" and event.direction == required_dir and event.displacement_present:
            return VerificationCheck(
                "m15_choch_exists", "PASS",
                f"M15 CHoCH {required_dir} with displacement found at {event.time}",
                mso_value={"time": event.time, "ratio": event.displacement_ratio},
                ai_value=analysis.reasoning.m15_confirmation.choch_detected,
            )

    # Also accept BOS with displacement — some valid setups have BOS not CHoCH
    for event in reversed(m15_tf.structure_events):
        if event.type == "BOS" and event.direction == required_dir and event.displacement_present:
            return VerificationCheck(
                "m15_choch_exists", "PASS",
                f"M15 BOS {required_dir} with displacement found at {event.time} (BOS accepted)",
                mso_value={"time": event.time, "ratio": event.displacement_ratio, "type": "BOS"},
                ai_value=analysis.reasoning.m15_confirmation.choch_detected,
            )

    available = [
        f"{e.type} {e.direction} disp={e.displacement_present} ratio={e.displacement_ratio}"
        for e in m15_tf.structure_events
    ]
    return VerificationCheck(
        "m15_choch_exists", "FAIL",
        f"No M15 CHoCH/BOS with displacement for {required_dir}. "
        f"Available events: {available or 'none'}",
        mso_value=available,
        ai_value=analysis.reasoning.m15_confirmation.choch_detected,
    )


def _check_displacement_ratio(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
) -> VerificationCheck:
    """CHECK 2: M15 displacement ratio >= threshold."""
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck(
            "displacement_ratio", "SKIP",
            "No trade_parameters",
        )

    required_dir = _direction_for_trade(tp.direction)
    threshold = config.get("model_a", {}).get("displacement_min_ratio", 1.5)
    m15_tf = mso.timeframes.get("M15")
    if m15_tf is None:
        return VerificationCheck("displacement_ratio", "SKIP", "No M15 data")

    # Find the best qualifying event (CHoCH preferred, then BOS) -- iterate
    # newest-first so the reported ratio/time is the triggering event, not a
    # stale week-old match.  Under the shipping config
    # (model_a.displacement_min_ratio == market_state's displacement_present
    # threshold of 1.5), PASS/FAIL is unchanged because every qualifying
    # event satisfies the threshold by construction.  If the config threshold
    # is ever raised above 1.5, picking the most-recent event is the correct
    # validation target (the event that actually triggered this decision).
    # See research/thursday_2026-04-23_analysis/US30_analysis.md §8 #6.
    best_event = None
    for event in reversed(m15_tf.structure_events):
        if event.direction == required_dir and event.displacement_present:
            if event.type == "CHoCH":
                best_event = event
                break
            if best_event is None and event.type == "BOS":
                best_event = event

    if best_event is None:
        return VerificationCheck(
            "displacement_ratio", "SKIP",
            "No qualifying M15 event found (depends on Check 1)",
        )

    mso_ratio = best_event.displacement_ratio
    ai_ratio = analysis.reasoning.m15_confirmation.displacement_candle_body_vs_avg_ratio

    if mso_ratio < threshold:
        return VerificationCheck(
            "displacement_ratio", "FAIL",
            f"M15 displacement ratio {mso_ratio:.2f} below {threshold} threshold",
            mso_value=mso_ratio,
            ai_value=ai_ratio,
        )

    # Warn if AI misreported the ratio by a wide margin
    detail = f"M15 displacement ratio {mso_ratio:.2f} >= {threshold} threshold"
    if ai_ratio > 0 and abs(mso_ratio - ai_ratio) > 0.5:
        detail += f" (WARNING: AI reported {ai_ratio:.2f}, MSO has {mso_ratio:.2f})"
        logger.warning(
            "Displacement ratio mismatch: AI=%.2f MSO=%.2f", ai_ratio, mso_ratio,
        )

    return VerificationCheck(
        "displacement_ratio", "PASS", detail,
        mso_value=mso_ratio, ai_value=ai_ratio,
    )


def _check_h1_poi_exists(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
) -> tuple[VerificationCheck, Optional[OrderBlock], Optional[BreakerBlock]]:
    """CHECK 3: H1 unmitigated OB (or breaker) exists at AI's cited price level.

    Returns the check result AND the matched OB/breaker for downstream checks.

    Defense-in-depth (HALLUC-1, GBPJPY 2026-04-28): routes on the AI's
    actual ``frameworks_evaluated.<X>.qualified`` flags rather than the
    wrapper-level ``analysis.framework`` field. The wrapper field is
    biased by user-message phrasing (pre-2026-04-28 hard-coded "for the
    OB Retest setup") and observed to disagree with the AI's per-framework
    qualification reasoning under multi-framework dispatch. When the
    wrapper disagrees with the qualified framework, this check routes the
    verification to the qualified framework and returns ``WARN`` (not
    ``FAIL``) on the wrapper-vs-qualifications inconsistency. See
    ``research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md``.
    """
    h1_setup = analysis.reasoning.h1_setup

    # Compute effective framework by routing on AI's actual qualification
    # flags (defense-in-depth against the prompt-line-1426 dispatch bias).
    effective_framework, was_overridden, routing_decision = _compute_effective_framework(analysis)
    framework = effective_framework

    # WARN-on-routing-inconsistency: when wrapper and effective disagree,
    # the validation still proceeds against the AI's qualified framework
    # but the check status is downgraded to WARN to surface the
    # wrapper-qualifications mismatch in the audit trail.
    base_status_pass = "WARN" if was_overridden else "PASS"

    def _wrap_details(extra: dict | None = None) -> dict:
        payload = {"routing_decision": routing_decision}
        if extra:
            payload.update(extra)
        return payload

    if not h1_setup.poi_identified:
        return (
            VerificationCheck(
                "h1_poi_exists", "FAIL",
                "AI reports poi_identified=False — no H1 POI to validate",
                mso_value=_wrap_details(),
            ),
            None, None,
        )

    poi_price = h1_setup.poi_price_level
    if poi_price is None or poi_price == 0:
        return (
            VerificationCheck(
                "h1_poi_exists", "FAIL",
                "AI claims POI identified but poi_price_level is 0 or None",
                mso_value=_wrap_details(),
                ai_value=poi_price,
            ),
            None, None,
        )

    h1_tf = mso.timeframes.get("H1")
    if h1_tf is None:
        return (
            VerificationCheck(
                "h1_poi_exists", "FAIL", "No H1 timeframe data in MSO",
                mso_value=_wrap_details(),
            ),
            None, None,
        )

    tol = _ob_tolerance(poi_price, config)

    # fvg_fill effective framework — wrapper said ob_retest (or other) but
    # the AI's qualifications routed us to fvg_fill. Validate against the
    # M15 FVG array, mirroring the contract of _check_entry_in_fvg's
    # poi-match-step. Keep matched_ob/matched_bb as None — downstream
    # OB/breaker checks must SKIP in this branch.
    if framework == "fvg_fill":
        m15_tf = mso.timeframes.get("M15")
        if m15_tf is None:
            return (
                VerificationCheck(
                    "h1_poi_exists", "FAIL",
                    "fvg_fill effective framework but no M15 timeframe data in MSO",
                    mso_value=_wrap_details(),
                    ai_value=poi_price,
                ),
                None, None,
            )

        tp = analysis.trade_parameters
        required_fvg_type = (
            "bullish" if tp and tp.direction == "LONG" else "bearish"
        )
        matched_fvg = _find_matching_fvg(
            m15_tf.fair_value_gaps, poi_price, tol, required_fvg_type,
        )
        if matched_fvg:
            return (
                VerificationCheck(
                    "h1_poi_exists", base_status_pass,
                    f"M15 FVG found at {matched_fvg.bottom:.5f}-{matched_fvg.top:.5f} "
                    f"near AI's POI at {poi_price:.5f} (effective framework="
                    f"fvg_fill, wrapper={routing_decision['wrapper_framework']})",
                    mso_value=_wrap_details({
                        "fvg_top": matched_fvg.top,
                        "fvg_bottom": matched_fvg.bottom,
                        "fvg_type": matched_fvg.type,
                    }),
                    ai_value=poi_price,
                ),
                None, None,
            )

        available_fvgs = [
            f"{f.type} {f.bottom:.5f}-{f.top:.5f} filled={f.filled}"
            for f in m15_tf.fair_value_gaps
        ]
        return (
            VerificationCheck(
                "h1_poi_exists", "FAIL",
                f"AI cites POI at {poi_price:.5f} but no unfilled "
                f"{required_fvg_type} M15 FVG envelopes that price "
                f"(effective framework=fvg_fill, "
                f"wrapper={routing_decision['wrapper_framework']}). "
                f"Available M15 FVGs: {available_fvgs or 'none'}",
                mso_value=_wrap_details({"available_m15_fvgs": available_fvgs}),
                ai_value=poi_price,
            ),
            None, None,
        )

    # For breaker_retest / breaker_re_entry, check breaker blocks. Both
    # framework names route to the same H1 breaker validation — the explicit
    # ``breaker_re_entry`` is the production-facing label activated 2026-04-25
    # by ``model_a.enabled_frameworks``; ``breaker_retest`` remains the
    # legacy alias preserved for historical fixtures + AI string aliases
    # registered in primary_analyzer's ``_FW_MAP``.
    if framework in ("breaker_retest", "breaker_re_entry"):
        tp = analysis.trade_parameters
        required_dir = _direction_for_trade(tp.direction) if tp else "bullish"
        matched_bb = _find_matching_breaker(
            h1_tf.breaker_blocks, poi_price, tol, required_dir,
        )
        if matched_bb:
            return (
                VerificationCheck(
                    "h1_poi_exists", base_status_pass,
                    f"H1 breaker block found at {matched_bb.zone_low:.2f}-{matched_bb.zone_high:.2f} "
                    f"near AI's POI at {poi_price:.2f} (framework={framework})",
                    mso_value=_wrap_details({
                        "zone": f"{matched_bb.zone_low}-{matched_bb.zone_high}",
                    }),
                    ai_value=poi_price,
                ),
                None, matched_bb,
            )

        available_breakers = [
            f"{bb.direction} {bb.zone_low:.2f}-{bb.zone_high:.2f} retested={bb.is_retested}"
            for bb in h1_tf.breaker_blocks
        ]
        return (
            VerificationCheck(
                "h1_poi_exists", "FAIL",
                f"AI cites H1 breaker POI at {poi_price:.2f} but no unretested "
                f"H1 breaker found near that level (framework={framework}). "
                f"Available: {available_breakers or 'none'}",
                mso_value=_wrap_details({"available_breakers": available_breakers}),
                ai_value=poi_price,
            ),
            None, None,
        )

    # Default: ob_retest — check order blocks
    matched_ob = _find_matching_ob(h1_tf.order_blocks, poi_price, tol)
    if matched_ob:
        return (
            VerificationCheck(
                "h1_poi_exists", base_status_pass,
                f"H1 OB found at {matched_ob.low:.2f}-{matched_ob.high:.2f} "
                f"near AI's POI at {poi_price:.2f}",
                mso_value=_wrap_details({
                    "zone": f"{matched_ob.low}-{matched_ob.high}",
                }),
                ai_value=poi_price,
            ),
            matched_ob, None,
        )

    # No OB match — also check breakers as fallback (AI may have picked a breaker
    # under ob_retest framework if the prompt evaluates both)
    tp = analysis.trade_parameters
    required_dir = _direction_for_trade(tp.direction) if tp else "bullish"
    matched_bb = _find_matching_breaker(
        h1_tf.breaker_blocks, poi_price, tol, required_dir,
    )
    if matched_bb:
        return (
            VerificationCheck(
                "h1_poi_exists", base_status_pass,
                f"H1 breaker block found at {matched_bb.zone_low:.2f}-{matched_bb.zone_high:.2f} "
                f"near AI's POI at {poi_price:.2f} (breaker under ob_retest framework)",
                mso_value=_wrap_details({
                    "zone": f"{matched_bb.zone_low}-{matched_bb.zone_high}",
                }),
                ai_value=poi_price,
            ),
            None, matched_bb,
        )

    available_obs = [
        f"{ob.type} {ob.low:.2f}-{ob.high:.2f} mitigated={ob.mitigated}"
        for ob in h1_tf.order_blocks
    ]
    return (
        VerificationCheck(
            "h1_poi_exists", "FAIL",
            f"AI cites H1 POI at {poi_price:.2f} but no unmitigated H1 OB found "
            f"near that level. Available OBs: {available_obs or 'none'}",
            mso_value=_wrap_details({"available_obs": available_obs}),
            ai_value=poi_price,
        ),
        None, None,
    )


def _check_ob_zone(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    matched_ob: Optional[OrderBlock],
    matched_bb: Optional[BreakerBlock],
    config: dict,
) -> VerificationCheck:
    """CHECK 4: H1 OB/breaker in correct premium/discount zone."""
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("ob_zone", "SKIP", "No trade_parameters")

    if matched_ob is None and matched_bb is None:
        return VerificationCheck(
            "ob_zone", "SKIP",
            "No matched OB/breaker from Check 3",
        )

    h1_tf = mso.timeframes.get("H1")
    if h1_tf is None or h1_tf.premium_discount is None:
        return VerificationCheck(
            "ob_zone", "SKIP",
            "No H1 premium/discount data in MSO",
        )

    pd = h1_tf.premium_discount
    eq = pd.equilibrium_50

    if matched_ob:
        midpoint = (matched_ob.high + matched_ob.low) / 2
    else:
        midpoint = (matched_bb.zone_high + matched_bb.zone_low) / 2

    direction = tp.direction
    strict = config.get("verification", {}).get("strict_zone_check", False)

    if direction == "LONG":
        required_zone = "discount"
        in_correct_zone = midpoint <= eq
        actual_zone = "discount" if midpoint <= eq else "premium"
    else:
        required_zone = "premium"
        in_correct_zone = midpoint >= eq
        actual_zone = "premium" if midpoint >= eq else "discount"

    if in_correct_zone:
        return VerificationCheck(
            "ob_zone", "PASS",
            f"OB midpoint {midpoint:.2f} is in {actual_zone} zone "
            f"(eq={eq:.2f}), correct for {direction}",
            mso_value={"midpoint": midpoint, "equilibrium": eq, "zone": actual_zone},
            ai_value=analysis.reasoning.h1_setup.zone,
        )

    status = "FAIL" if strict else "WARN"
    return VerificationCheck(
        "ob_zone", status,
        f"OB midpoint {midpoint:.2f} is in {actual_zone} but {direction} requires "
        f"{required_zone}. Equilibrium at {eq:.2f}",
        mso_value={"midpoint": midpoint, "equilibrium": eq, "zone": actual_zone},
        ai_value=analysis.reasoning.h1_setup.zone,
    )


def _check_entry_in_ob(
    analysis: PrimaryAnalysisOutput,
    matched_ob: Optional[OrderBlock],
    matched_bb: Optional[BreakerBlock],
    config: dict,
) -> VerificationCheck:
    """CHECK 5: Entry price within OB/breaker zone."""
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("entry_in_ob", "SKIP", "No trade_parameters")

    if matched_ob is None and matched_bb is None:
        return VerificationCheck(
            "entry_in_ob", "SKIP",
            "No matched OB/breaker from Check 3",
        )

    entry = tp.entry_price
    tol = _ob_tolerance(entry, config)

    if matched_ob:
        zone_low, zone_high = matched_ob.low, matched_ob.high
        zone_label = "OB"
    else:
        zone_low, zone_high = matched_bb.zone_low, matched_bb.zone_high
        zone_label = "breaker"

    if zone_low - tol <= entry <= zone_high + tol:
        return VerificationCheck(
            "entry_in_ob", "PASS",
            f"Entry {entry:.2f} is within {zone_label} zone "
            f"{zone_low:.2f}-{zone_high:.2f}",
            mso_value=f"{zone_low}-{zone_high}",
            ai_value=entry,
        )

    return VerificationCheck(
        "entry_in_ob", "FAIL",
        f"Entry {entry:.2f} is outside {zone_label} zone "
        f"{zone_low:.2f}-{zone_high:.2f}",
        mso_value=f"{zone_low}-{zone_high}",
        ai_value=entry,
    )


def _check_entry_in_fvg(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
    effective_framework: Optional[str] = None,
) -> VerificationCheck:
    """CHECK 7: Entry within an unfilled M15 FVG (fvg_fill framework only).

    Activated 2026-04-25 alongside the `fvg_fill` framework. Mirrors the
    role `_check_entry_in_ob` plays for ob_retest, but on the M15 FVG
    array instead of the H1 OB array.

    Fires only when ``analysis.framework == "fvg_fill"``. For every other
    framework (including ``ob_retest``) the check returns SKIP and does
    not affect the verification verdict — the ob_retest path is governed
    by the existing OB checks (h1_poi_exists, ob_zone, entry_in_ob,
    sl_beyond_ob), which remain unchanged.

    Validates three conditions on the AI's CANDIDATE output:

      (a) the AI's cited POI midpoint (``h1_setup.poi_price_level``)
          falls inside an unfilled M15 FVG whose ``type`` matches the
          trade direction (bullish for LONG, bearish for SHORT);
      (b) ``trade_parameters.entry_price`` is within
          ``[fvg.bottom, fvg.top]`` of that same FVG (within OB-style
          tolerance);
      (c) ``trade_parameters.stop_loss`` is geometrically beyond the
          displacement candle that created the FVG. Since the M15
          candle list is not exposed on the MSO at L2 time, the
          structurally-aligned proxy used here is:
            - LONG  : ``stop_loss < fvg.bottom`` (strict)
            - SHORT : ``stop_loss > fvg.top``    (strict)
          The displacement candle's actual extreme is at or beyond the
          FVG's far edge by construction (see
          ``identify_fvgs`` in market_state.py:772). A SL placed beyond
          the FVG's far edge is therefore at-or-beyond the displacement
          candle's extreme — strictly correct in the conservative
          direction (the alternative — SL inside the FVG — defeats the
          structural premise that the gap-creating impulse must be
          violated to invalidate the setup).

    Returns PASS / FAIL / SKIP. Same VerificationCheck shape as
    ``_check_entry_in_ob``: ``mso_value`` / ``ai_value`` are populated
    with the FVG geometry and the AI's emitted prices for downstream
    diagnostics.
    """
    # Use effective_framework when provided (multi-framework dispatch
    # routing per HALLUC-1 fix); fall back to wrapper-level analysis.framework
    # for backwards compatibility with direct callers.
    if effective_framework is None:
        effective_framework = getattr(analysis, "framework", None)
    if effective_framework != "fvg_fill":
        return VerificationCheck(
            "entry_in_fvg", "SKIP",
            f"Framework is '{effective_framework}', not 'fvg_fill' — check is fvg_fill-only",
        )

    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("entry_in_fvg", "SKIP", "No trade_parameters")

    h1_setup = analysis.reasoning.h1_setup
    poi_price = getattr(h1_setup, "poi_price_level", 0) or 0
    if poi_price == 0:
        return VerificationCheck(
            "entry_in_fvg", "FAIL",
            "fvg_fill CANDIDATE but poi_price_level is 0 — cannot match an FVG",
            ai_value=poi_price,
        )

    m15_tf = mso.timeframes.get("M15")
    if m15_tf is None:
        return VerificationCheck(
            "entry_in_fvg", "FAIL",
            "fvg_fill CANDIDATE but no M15 timeframe data in MSO",
        )

    required_fvg_type = "bullish" if tp.direction == "LONG" else "bearish"
    tol = _ob_tolerance(poi_price, config)

    matched_fvg = _find_matching_fvg(
        m15_tf.fair_value_gaps, poi_price, tol, required_fvg_type,
    )
    if matched_fvg is None:
        available = [
            f"{f.type} {f.bottom:.5f}-{f.top:.5f} filled={f.filled}"
            for f in m15_tf.fair_value_gaps
        ]
        return VerificationCheck(
            "entry_in_fvg", "FAIL",
            f"AI cites fvg_fill POI at {poi_price} but no unfilled "
            f"{required_fvg_type} M15 FVG envelopes that price. "
            f"Available M15 FVGs: {available or 'none'}",
            mso_value=available,
            ai_value=poi_price,
        )

    # (b) entry inside FVG range
    entry = tp.entry_price
    entry_tol = _ob_tolerance(entry, config)
    if not (matched_fvg.bottom - entry_tol <= entry <= matched_fvg.top + entry_tol):
        return VerificationCheck(
            "entry_in_fvg", "FAIL",
            f"Entry {entry} is outside matched M15 FVG range "
            f"{matched_fvg.bottom}-{matched_fvg.top}",
            mso_value={
                "fvg_top": matched_fvg.top,
                "fvg_bottom": matched_fvg.bottom,
                "fvg_type": matched_fvg.type,
            },
            ai_value=entry,
        )

    # (c) SL beyond displacement extreme — proxied via FVG's far edge.
    #
    # SISTER-4/5 fix (research/sister_bug_audit_2026-04-27 #4-#5): the FVG
    # bottom/top are MSO underlying floats; the AI saw the rendered values
    # at ``prompt.price_format`` precision (e.g. ``.1f`` for NAS100). Snap
    # the MSO floats to the AI's display plane before strict comparison —
    # otherwise a sub-tick rendering delta forces a deterministic FAIL on
    # every NAS100 ``fvg_fill`` CANDIDATE whose AI-emitted SL lands at the
    # rendered FVG extreme. Same compound bug class as HALLUC-1
    # (commit 2c75f98).
    sl = tp.stop_loss
    _decimals = _resolve_display_decimals(config, default=2)
    _fvg_bottom = _snap_to_precision(matched_fvg.bottom, _decimals)
    _fvg_top = _snap_to_precision(matched_fvg.top, _decimals)
    if tp.direction == "LONG":
        if sl >= _fvg_bottom:
            return VerificationCheck(
                "entry_in_fvg", "FAIL",
                f"LONG fvg_fill SL {sl} is NOT strictly below FVG bottom "
                f"{_fvg_bottom} (rendered from underlying {matched_fvg.bottom}) "
                "— SL must sit beyond the displacement candle's far extreme "
                "(FVG bottom is a conservative proxy)",
                mso_value={
                    "fvg_bottom": matched_fvg.bottom,
                    "fvg_bottom_rendered": _fvg_bottom,
                    "fvg_top": matched_fvg.top,
                },
                ai_value=sl,
            )
    else:  # SHORT
        if sl <= _fvg_top:
            return VerificationCheck(
                "entry_in_fvg", "FAIL",
                f"SHORT fvg_fill SL {sl} is NOT strictly above FVG top "
                f"{_fvg_top} (rendered from underlying {matched_fvg.top}) "
                "— SL must sit beyond the displacement candle's far extreme "
                "(FVG top is a conservative proxy)",
                mso_value={
                    "fvg_top": matched_fvg.top,
                    "fvg_top_rendered": _fvg_top,
                    "fvg_bottom": matched_fvg.bottom,
                },
                ai_value=sl,
            )

    return VerificationCheck(
        "entry_in_fvg", "PASS",
        f"Entry {entry} within unfilled {matched_fvg.type} M15 FVG "
        f"{matched_fvg.bottom}-{matched_fvg.top} and SL {sl} is "
        f"beyond the {'low' if tp.direction == 'LONG' else 'high'} edge",
        mso_value={
            "fvg_bottom": matched_fvg.bottom,
            "fvg_top": matched_fvg.top,
            "fvg_midpoint": matched_fvg.midpoint,
            "fvg_type": matched_fvg.type,
            "formation_time": matched_fvg.formation_time,
        },
        ai_value={"entry": entry, "sl": sl, "poi": poi_price},
    )


def _check_entry_in_breaker(
    analysis: PrimaryAnalysisOutput,
    matched_bb: Optional[BreakerBlock],
    config: dict,
    effective_framework: Optional[str] = None,
) -> VerificationCheck:
    """CHECK 8 (breaker_re_entry only): Entry in breaker zone + SL beyond
    breaker far extreme.

    Mirrors :func:`_check_entry_in_ob` but is namespaced to the
    ``breaker_re_entry`` framework. Returns ``SKIP`` for any other framework
    (including the legacy ``breaker_retest`` alias, which already routes
    through the existing ``entry_in_ob`` + ``sl_beyond_ob`` pair via the
    matched-breaker fallback).

    Validates three conditions when ``framework == "breaker_re_entry"``:
      1. The cited POI resolved to an unretested H1 breaker in the AI's
         trade direction (delegated to ``_check_h1_poi_exists`` upstream;
         this check SKIPs cleanly if no breaker was matched).
      2. ``entry_price`` falls inside the breaker zone within configured
         tolerance.
      3. ``stop_loss`` sits BEYOND the breaker's far extreme on the correct
         side for the trade direction (LONG → SL strictly below
         ``zone_low``; SHORT → SL strictly above ``zone_high``).

    Cite Wave-1 source artifact: research/vision_program_2026-04-25/
    03_EDGE_TAXONOMY.md §E5 ("breaker re-entry, cheapest top-5 deploy").
    """
    # Use effective_framework when provided (multi-framework dispatch
    # routing per HALLUC-1 fix); fall back to wrapper-level analysis.framework
    # for backwards compatibility with direct callers.
    framework = effective_framework if effective_framework is not None else analysis.framework
    if framework != "breaker_re_entry":
        return VerificationCheck(
            "entry_in_breaker", "SKIP",
            f"Framework is {framework!r}, not 'breaker_re_entry' — check not applicable",
        )

    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck(
            "entry_in_breaker", "SKIP",
            "No trade_parameters",
        )

    if matched_bb is None:
        return VerificationCheck(
            "entry_in_breaker", "SKIP",
            "No matched breaker from h1_poi_exists (cannot validate entry/SL)",
        )

    entry = tp.entry_price
    sl = tp.stop_loss
    direction = tp.direction
    zone_low, zone_high = matched_bb.zone_low, matched_bb.zone_high
    tol = _ob_tolerance(entry, config)

    # (a) Entry inside breaker zone within tolerance.
    if not (zone_low - tol <= entry <= zone_high + tol):
        return VerificationCheck(
            "entry_in_breaker", "FAIL",
            f"Entry {entry:.5f} is outside breaker zone "
            f"{zone_low:.5f}-{zone_high:.5f} (tolerance {tol:.5f})",
            mso_value=f"{zone_low}-{zone_high}",
            ai_value=entry,
        )

    # (b) Direction-aware SL placement BEYOND breaker far extreme.
    #
    # SISTER-1/2 fix (research/sister_bug_audit_2026-04-27 #1-#2): the
    # breaker zone_low/zone_high are MSO underlying floats; the AI saw the
    # rendered values at ``prompt.price_format`` precision. Snap the MSO
    # floats to the AI's display plane before strict comparison — same
    # compound bug class as HALLUC-1 (commit 2c75f98). Without this snap,
    # NAS100 ``breaker_re_entry`` CANDIDATEs deterministically FAIL when
    # the AI emits an SL at the rendered breaker extreme but the
    # underlying float carries an extra decimal (e.g. zone_low underlying
    # 27200.16, AI saw "27200.2", emits SL=27200.1 thinking it's "below"
    # but pre-fix check ``27200.1 >= 27200.16`` is False -> demote when
    # the geometry is correct on the AI's plane).
    _decimals = _resolve_display_decimals(config, default=2)
    _zone_low = _snap_to_precision(zone_low, _decimals)
    _zone_high = _snap_to_precision(zone_high, _decimals)
    if direction == "LONG":
        if sl >= _zone_low:
            return VerificationCheck(
                "entry_in_breaker", "FAIL",
                f"SL {sl:.5f} is NOT strictly below breaker zone_low "
                f"{_zone_low:.5f} (rendered from underlying {zone_low:.5f}) "
                "for LONG breaker_re_entry",
                mso_value=zone_low,
                ai_value=sl,
            )
    else:
        if sl <= _zone_high:
            return VerificationCheck(
                "entry_in_breaker", "FAIL",
                f"SL {sl:.5f} is NOT strictly above breaker zone_high "
                f"{_zone_high:.5f} (rendered from underlying {zone_high:.5f}) "
                "for SHORT breaker_re_entry",
                mso_value=zone_high,
                ai_value=sl,
            )

    # (c) Direction matches breaker polarity (defensive — h1_poi_exists
    # already enforces this, but a passing path here without the polarity
    # check would mean a future refactor could introduce a regression).
    expected_dir = "bullish" if direction == "LONG" else "bearish"
    if matched_bb.direction != expected_dir:
        return VerificationCheck(
            "entry_in_breaker", "FAIL",
            f"Breaker direction {matched_bb.direction!r} does not match "
            f"trade direction {direction!r} (expected breaker direction "
            f"{expected_dir!r})",
            mso_value=matched_bb.direction,
            ai_value=direction,
        )

    return VerificationCheck(
        "entry_in_breaker", "PASS",
        f"Entry {entry:.5f} inside {matched_bb.direction} breaker zone "
        f"{zone_low:.5f}-{zone_high:.5f}; SL {sl:.5f} beyond far extreme "
        f"for {direction}",
        mso_value=f"{zone_low}-{zone_high}",
        ai_value=entry,
    )


def _check_gap_ceiling(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
) -> VerificationCheck:
    """CHECK 7: Current price is within max_gap_pct% of zone entry.

    Prevents limit orders on stale zones where price has run far away.
    Evidence: gap >1.5% band produced 12.3% WR on 57 trades (Jan–Apr 2026).
    Only meaningful after Change 1 (prompt fix) sets entry_price = ob_high.
    """
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("gap_ceiling", "SKIP", "No trade_parameters")

    m15_tf = mso.timeframes.get("M15")
    if not m15_tf or not getattr(m15_tf, "candles", None):
        return VerificationCheck("gap_ceiling", "SKIP", "No M15 candles in MSO")

    current_price = m15_tf.candles[-1].close
    entry_price = tp.entry_price
    direction = tp.direction

    if direction == "LONG":
        gap_pct = (current_price - entry_price) / entry_price * 100
    else:
        gap_pct = (entry_price - current_price) / entry_price * 100

    # `or 1.5` coerced the *strictest* configured value (0) into the *loosest*
    # default, silently disabling the gate for anyone who set `max_gap_pct: 0`.
    # Only a genuinely absent/None key falls back. Note `config.get("filters")`
    # rather than `config.get("filters", {})`: an explicit `filters:` with no
    # body yields None, not a missing key.
    configured_max_gap_pct = (config.get("filters") or {}).get("max_gap_pct")
    if configured_max_gap_pct is None or isinstance(configured_max_gap_pct, bool):
        # bool is a subclass of int; `max_gap_pct: no` must not become 0.0.
        max_gap_pct = 1.5
    else:
        try:
            max_gap_pct = float(configured_max_gap_pct)
        except (TypeError, ValueError):
            max_gap_pct = 1.5

    if gap_pct <= max_gap_pct:
        return VerificationCheck(
            "gap_ceiling", "PASS",
            f"Gap {gap_pct:.2f}% <= {max_gap_pct:.1f}% ceiling "
            f"(current={current_price:.2f}, zone_entry={entry_price:.2f})",
            mso_value=round(current_price, 2),
            ai_value=round(entry_price, 2),
        )

    return VerificationCheck(
        "gap_ceiling", "FAIL",
        f"Gap {gap_pct:.2f}% > {max_gap_pct:.1f}% ceiling — zone too far "
        f"(current={current_price:.2f}, zone_entry={entry_price:.2f})",
        mso_value=round(current_price, 2),
        ai_value=round(entry_price, 2),
    )


def _check_sl_beyond_ob(
    analysis: PrimaryAnalysisOutput,
    matched_ob: Optional[OrderBlock],
    matched_bb: Optional[BreakerBlock],
    config: dict,
) -> VerificationCheck:
    """CHECK 6: SL placed beyond OB/breaker extreme by at least the tick floor.

    Tolerance model (ADR-006, replaces strict-< binary check):
      LONG  : sl <= ob_low  - floor   (must clear by floor)
      SHORT : sl >= ob_high + floor   (must clear by floor)

    Floor is read from ``verification.sl_beyond_ob_tick_floor`` (default 1
    tick); set to 0 in config to revert to strict-< (rollback). Tight-FX
    profiles override the floor to 5-8 ticks per ADR-006 to absorb 5dp
    quantization rounding.

    Precision-snap (SISTER-consistency, 2026-04-28): the OB/breaker zone
    floats are MSO underlying values; the AI saw the rendered values at
    ``prompt.price_format`` precision. We snap the MSO floats to the AI's
    display plane before applying the floor-tolerance comparison — same
    contract as ``_check_entry_in_breaker`` (SISTER-1/2) and
    ``_check_entry_in_fvg`` (SISTER-4/5). Without this snap, a sub-tick
    rendering delta can survive the tick floor when the floor is 1 (the
    default) and the underlying carries an extra decimal beyond what the
    AI was shown. The original sister-bug audit incorrectly listed this
    site as "safe by audit"; the 2026-04-28 trending_bull-replay audit
    (``research/a4_trending_bull_replay_2026-04-28/``) re-tested and
    confirmed the snap is required for full SISTER consistency.
    """
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("sl_beyond_ob", "SKIP", "No trade_parameters")

    if matched_ob is None and matched_bb is None:
        return VerificationCheck(
            "sl_beyond_ob", "SKIP",
            "No matched OB/breaker from Check 3",
        )

    sl = tp.stop_loss
    direction = tp.direction
    floor = _sl_beyond_floor(sl, config)

    if matched_ob:
        zone_low, zone_high = matched_ob.low, matched_ob.high
        zone_label = "OB"
    else:
        zone_low, zone_high = matched_bb.zone_low, matched_bb.zone_high
        zone_label = "breaker"

    # SISTER-consistency snap (2026-04-28): align MSO floats to the AI's
    # display precision before strict comparison. Mirrors
    # _check_entry_in_breaker (SISTER-1/2) + _check_entry_in_fvg (SISTER-4/5).
    _decimals = _resolve_display_decimals(config, default=2)
    zone_low = _snap_to_precision(zone_low, _decimals)
    zone_high = _snap_to_precision(zone_high, _decimals)

    fmt = config.get("prompt", {}).get("price_format", ".2f")

    if direction == "LONG":
        if sl <= zone_low - floor:
            return VerificationCheck(
                "sl_beyond_ob", "PASS",
                f"SL {sl:{fmt}} clears {zone_label} low {zone_low:{fmt}} "
                f"by >= floor {floor:{fmt}}",
                mso_value=zone_low, ai_value=sl,
            )
        return VerificationCheck(
            "sl_beyond_ob", "FAIL",
            f"SL {sl:{fmt}} does not clear {zone_label} low "
            f"{zone_low:{fmt}} by floor {floor:{fmt}} for LONG",
            mso_value=zone_low, ai_value=sl,
        )

    # SHORT
    if sl >= zone_high + floor:
        return VerificationCheck(
            "sl_beyond_ob", "PASS",
            f"SL {sl:{fmt}} clears {zone_label} high {zone_high:{fmt}} "
            f"by >= floor {floor:{fmt}}",
            mso_value=zone_high, ai_value=sl,
        )
    return VerificationCheck(
        "sl_beyond_ob", "FAIL",
        f"SL {sl:{fmt}} does not clear {zone_label} high "
        f"{zone_high:{fmt}} by floor {floor:{fmt}} for SHORT",
        mso_value=zone_high, ai_value=sl,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def verify_candidate(
    analysis: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    config: dict,
) -> VerificationResult:
    """Verify AI CANDIDATE output against MSO source data.

    Branches on ``analysis.framework``:

      * ``ob_retest`` (and any non-fvg_fill value): runs the original 7
        OB-retest checks unchanged. The new ``entry_in_fvg`` check is
        appended and returns SKIP for these framewors so it never
        affects the verdict.

      * ``fvg_fill``: runs M15 CHoCH + displacement-ratio (still
        applicable — fvg_fill REQUIRES an aligned M15 displacement that
        created the gap), then the new ``entry_in_fvg`` check, plus the
        framework-agnostic ``gap_ceiling`` check. The OB-specific checks
        (``h1_poi_exists``, ``ob_zone``, ``entry_in_ob``,
        ``sl_beyond_ob``) are recorded as SKIP — they target H1 OB
        geometry which fvg_fill does not cite. This branch fully
        validates the fvg_fill path on the M15 FVG array.

    Returns ``VerificationResult`` with per-check details and overall
    pass/fail status. ``blocked_by`` names the first FAIL'd check or
    ``None`` on PASS.
    """
    v_cfg = config.get("verification", {})
    if not v_cfg.get("enabled", True):
        return VerificationResult(passed=True, checks=[
            VerificationCheck("verification_disabled", "SKIP", "Verification disabled in config"),
        ])

    # Multi-framework dispatch routing (HALLUC-1 fix, GBPJPY 2026-04-28):
    # route on the AI's per-framework qualified flags rather than the
    # wrapper-level framework field. The wrapper field is biased by
    # user-message phrasing and observed to disagree with qualifications
    # under multi-framework dispatch. _compute_effective_framework returns
    # the wrapper unchanged when the wrapper agrees with qualifications,
    # so happy-path behavior is bit-identical.
    effective_framework, _was_overridden, _routing_decision = _compute_effective_framework(analysis)
    is_fvg_fill = effective_framework == "fvg_fill"

    checks: list[VerificationCheck] = []
    # Default these to None so the post-branch CHECK 8 (breaker_re_entry)
    # dispatch can reference them safely on the fvg_fill branch where the
    # OB/breaker resolution does not run.
    matched_ob = None
    matched_bb = None

    # CHECK 1: M15 CHoCH with displacement (framework-agnostic — both
    # ob_retest and fvg_fill require an aligned M15 displacement event).
    c1 = _check_m15_choch(analysis, mso)
    checks.append(c1)

    # CHECK 2: Displacement ratio >= threshold (framework-agnostic).
    c2 = _check_displacement_ratio(analysis, mso, config)
    checks.append(c2)

    if is_fvg_fill:
        # ── fvg_fill branch ────────────────────────────────────────────
        # The cited POI is an M15 FVG midpoint, NOT an H1 OB. Skip the
        # OB-specific checks and run the dedicated FVG check instead.
        skip_msg = "Skipped — fvg_fill framework cites an M15 FVG, not an H1 OB"
        checks.append(VerificationCheck("h1_poi_exists", "SKIP", skip_msg))
        checks.append(VerificationCheck("ob_zone", "SKIP", skip_msg))
        checks.append(VerificationCheck("entry_in_ob", "SKIP", skip_msg))
        checks.append(VerificationCheck("sl_beyond_ob", "SKIP", skip_msg))

        # New check: entry within an unfilled M15 FVG, SL beyond
        # displacement-extreme proxy. Only this check enforces the
        # fvg_fill geometric contract at L2.
        c_fvg = _check_entry_in_fvg(analysis, mso, config, effective_framework=effective_framework)
        checks.append(c_fvg)

        # CHECK 7: Gap ceiling — framework-agnostic, runs unchanged.
        c7 = _check_gap_ceiling(analysis, mso, config)
        checks.append(c7)

    else:
        # ── ob_retest (default) branch — UNCHANGED behavior ────────────
        # CHECK 3: H1 POI exists at cited level
        c3, matched_ob, matched_bb = _check_h1_poi_exists(analysis, mso, config)
        checks.append(c3)

        # CHECK 4: OB in correct P/D zone
        c4 = _check_ob_zone(analysis, mso, matched_ob, matched_bb, config)
        checks.append(c4)

        # CHECK 5: Entry within OB zone
        c5 = _check_entry_in_ob(analysis, matched_ob, matched_bb, config)
        checks.append(c5)

        # CHECK 6: SL beyond OB extreme
        c6 = _check_sl_beyond_ob(analysis, matched_ob, matched_bb, config)
        checks.append(c6)

        # A.1 deferred-changes shadow logger — observation-only.
        # Capture every PASS / FAIL of the sl_beyond_ob L2 gate so a
        # post-30-day data accumulation can compute hypothetical realized
        # R via H1 forward-resolution. Wrapped in try/except as belt-and-
        # suspenders — the logger already self-isolates. SKIP results
        # (no matched OB/breaker) are dropped inside the logger.
        # See ``src/components/sl_beyond_ob_shadow_logger.py`` and
        # ``.context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md``
        # item A.1 for the full rationale.
        try:
            _sl_shadow.log_sl_beyond_ob_decision(
                analysis=analysis,
                mso=mso,
                config=config,
                matched_ob=matched_ob,
                matched_bb=matched_bb,
                check_result=c6,
            )
        except Exception as _e:  # noqa: BLE001 — must never break L2
            logger.warning(
                "sl_beyond_ob_shadow_logger outer guard: %s", _e,
            )

        # New entry_in_fvg check is appended in SKIP form so the result
        # shape stays uniform across frameworks for downstream logging.
        c_fvg = _check_entry_in_fvg(analysis, mso, config, effective_framework=effective_framework)
        checks.append(c_fvg)

        # CHECK 7: Gap ceiling — current price within configured % of zone entry
        c7 = _check_gap_ceiling(analysis, mso, config)
        checks.append(c7)

    # CHECK 8: Breaker-specific entry + SL anchor (additive 2026-04-25, FTMO
    # challenge breaker_re_entry activation). SKIPs silently for non-breaker
    # frameworks so OB-retest behavior is bit-identical; FAILs only when
    # framework=='breaker_re_entry' AND the entry geometry against the
    # matched breaker is invalid.
    c8 = _check_entry_in_breaker(
        analysis, matched_bb, config, effective_framework=effective_framework,
    )
    checks.append(c8)

    # Log warnings even on pass
    log_warnings = v_cfg.get("log_warnings", True)
    for c in checks:
        if c.status == "WARN" and log_warnings:
            logger.warning("L2 verification warning: %s — %s", c.name, c.detail)

    # Determine overall result
    first_fail = next((c for c in checks if c.status == "FAIL"), None)
    passed = first_fail is None

    if not passed:
        logger.info(
            "L2 verification FAILED: %s — %s", first_fail.name, first_fail.detail,
        )

    return VerificationResult(
        passed=passed,
        checks=checks,
        blocked_by=first_fail.name if first_fail else None,
        matched_ob=matched_ob,
        matched_breaker=matched_bb,
    )
