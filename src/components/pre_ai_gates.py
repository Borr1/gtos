"""Pre-AI gates — deterministic checks that run before the primary analyzer.

Each gate mirrors an existing Level-2 verification condition. A skip here is
guaranteed to correspond to an L2 rejection downstream, so these gates never
filter a trade that would otherwise have passed — they only save the API call.

Multi-framework support shipped 2026-04-25 (FTMO $100K paid challenge): the
gate now skips ONLY when every currently-enabled framework has zero POIs in
the MSO. As soon as at least one framework has at least one POI candidate the
AI is invoked normally — letting whichever framework matches drive the
CANDIDATE decision. Fail-safe behaviour: unknown framework names default to
"do not skip" (run AI) so a typo in `enabled_frameworks` cannot silently mask
the model.
"""
from __future__ import annotations

from typing import Iterable

from src.models.market_state_models import MarketStateObject


# ---------------------------------------------------------------------------
# Framework-local POI helpers
# ---------------------------------------------------------------------------

def _has_ob_retest_poi(mso: MarketStateObject, bias: str = "") -> bool:
    """Return True when an ob_retest POI candidate exists in the MSO.

    The ob_retest framework requires either:

      * An unmitigated H1 OrderBlock, or
      * An unretested H1 BreakerBlock.

    When *bias* is supplied as ``"bullish"``/``"bearish"`` the lookup is
    direction-aware (matches the long-running L2 ``h1_poi_exists`` semantics
    and the original direction-aware shipping in `a84abde`). Empty/``"no_bias"``
    bias falls back to direction-agnostic.

    Returns ``False`` when the H1 timeframe is missing — that case is owned by
    the caller's framework loop, which treats "no POI for this framework" as a
    framework-level miss but still allows other frameworks to fire.
    """
    h1_tf = mso.timeframes.get("H1") if mso and mso.timeframes else None
    if h1_tf is None:
        return False

    directional = bias in ("bullish", "bearish")

    if directional:
        if any((not ob.mitigated) and ob.type == bias for ob in h1_tf.order_blocks):
            return True
        if any(
            (not bb.is_retested) and bb.direction == bias
            for bb in h1_tf.breaker_blocks
        ):
            return True
        return False

    if any(not ob.mitigated for ob in h1_tf.order_blocks):
        return True
    if any(not bb.is_retested for bb in h1_tf.breaker_blocks):
        return True
    return False


def _has_fvg_fill_poi(mso: MarketStateObject, bias: str = "") -> bool:
    """Return True when an fvg_fill POI candidate exists in the MSO.

    The fvg_fill framework cites an unfilled M15 FairValueGap whose ``type``
    matches the trade direction. Since the AI derives trade direction from the
    deterministic H1 bias, alignment is enforced via *bias*:

      * ``bias == "bullish"`` → require at least one unfilled bullish M15 FVG.
      * ``bias == "bearish"`` → require at least one unfilled bearish M15 FVG.
      * empty/``"no_bias"`` → any unfilled M15 FVG (either direction) keeps the
        gate passive. This is conservative: when bias is unknown the framework
        is left to the AI to evaluate.

    See ``_check_entry_in_fvg`` (verification.py) for the matching L2 contract:
    LONG → bullish FVG, SHORT → bearish FVG.
    """
    m15_tf = mso.timeframes.get("M15") if mso and mso.timeframes else None
    if m15_tf is None:
        return False

    directional = bias in ("bullish", "bearish")

    if directional:
        return any(
            (not fvg.filled) and (not fvg.invalidated) and fvg.type == bias
            for fvg in m15_tf.fair_value_gaps
        )

    return any(
        (not fvg.filled) and (not fvg.invalidated)
        for fvg in m15_tf.fair_value_gaps
    )


def _has_breaker_reentry_poi(mso: MarketStateObject, bias: str = "") -> bool:
    """Return True when a breaker_re_entry POI candidate exists in the MSO.

    The breaker_re_entry framework cites an unretested H1 BreakerBlock whose
    ``direction`` (the post-flip polarity) matches the trade direction. Since
    the AI derives trade direction from H1 bias, alignment is enforced via
    *bias*:

      * ``bias == "bullish"`` → require at least one unretested bullish
        breaker (former bearish OB now flipped to support).
      * ``bias == "bearish"`` → require at least one unretested bearish
        breaker (former bullish OB now flipped to resistance).
      * empty/``"no_bias"`` → any unretested breaker keeps the gate passive.

    See ``_check_entry_in_breaker`` (verification.py:465) for the matching L2
    contract: it requires breaker direction == trade direction with SL beyond
    the far breaker extreme.
    """
    h1_tf = mso.timeframes.get("H1") if mso and mso.timeframes else None
    if h1_tf is None:
        return False

    directional = bias in ("bullish", "bearish")

    if directional:
        return any(
            (not bb.is_retested) and bb.direction == bias
            for bb in h1_tf.breaker_blocks
        )

    return any(not bb.is_retested for bb in h1_tf.breaker_blocks)


def _within_price_tolerance(
    current_price: float,
    low: float,
    high: float,
    tolerance_pct: float,
) -> bool:
    tol = abs(current_price) * tolerance_pct
    return low - tol <= current_price <= high + tol


def _gap_pct_to_zone(current_price: float, low: float, high: float) -> float:
    if not current_price:
        return 0.0
    if low <= current_price <= high:
        return 0.0
    return min(abs(current_price - low), abs(current_price - high)) / abs(current_price) * 100.0


def _ob_retest_proximity(
    mso: MarketStateObject,
    current_price: float,
    tolerance_pct: float,
    bias: str = "",
) -> tuple[bool, float | None]:
    """Return whether an ob_retest POI is close enough to justify an AI call."""
    h1_tf = mso.timeframes.get("H1") if mso and mso.timeframes else None
    if h1_tf is None:
        return False, None

    directional = bias in ("bullish", "bearish")
    gaps: list[float] = []

    for ob in h1_tf.order_blocks:
        if ob.mitigated:
            continue
        if directional and ob.type != bias:
            continue
        gaps.append(_gap_pct_to_zone(current_price, ob.low, ob.high))
        if _within_price_tolerance(current_price, ob.low, ob.high, tolerance_pct):
            return True, min(gaps)

    for bb in h1_tf.breaker_blocks:
        if bb.is_retested:
            continue
        if directional and bb.direction != bias:
            continue
        gaps.append(_gap_pct_to_zone(current_price, bb.zone_low, bb.zone_high))
        if _within_price_tolerance(current_price, bb.zone_low, bb.zone_high, tolerance_pct):
            return True, min(gaps)

    return False, min(gaps) if gaps else None


def _breaker_reentry_proximity(
    mso: MarketStateObject,
    current_price: float,
    tolerance_pct: float,
    bias: str = "",
) -> tuple[bool, float | None]:
    """Return whether a breaker_re_entry POI is close enough for the AI call."""
    h1_tf = mso.timeframes.get("H1") if mso and mso.timeframes else None
    if h1_tf is None:
        return False, None

    directional = bias in ("bullish", "bearish")
    gaps: list[float] = []
    for bb in h1_tf.breaker_blocks:
        if bb.is_retested:
            continue
        if directional and bb.direction != bias:
            continue
        gaps.append(_gap_pct_to_zone(current_price, bb.zone_low, bb.zone_high))
        if _within_price_tolerance(current_price, bb.zone_low, bb.zone_high, tolerance_pct):
            return True, min(gaps)
    return False, min(gaps) if gaps else None


def _fvg_fill_proximity(
    mso: MarketStateObject,
    current_price: float,
    tolerance_pct: float,
    bias: str = "",
) -> tuple[bool, float | None]:
    """Return whether an unfilled M15 FVG is close enough for fvg_fill."""
    m15_tf = mso.timeframes.get("M15") if mso and mso.timeframes else None
    if m15_tf is None:
        return False, None

    directional = bias in ("bullish", "bearish")
    gaps: list[float] = []
    for fvg in m15_tf.fair_value_gaps:
        if fvg.filled or fvg.invalidated:
            continue
        if directional and fvg.type != bias:
            continue
        low = min(fvg.bottom, fvg.top)
        high = max(fvg.bottom, fvg.top)
        gaps.append(_gap_pct_to_zone(current_price, low, high))
        if _within_price_tolerance(current_price, low, high, tolerance_pct):
            return True, min(gaps)
    return False, min(gaps) if gaps else None


# ---------------------------------------------------------------------------
# Framework dispatch
# ---------------------------------------------------------------------------

# Registry of recognised frameworks → (helper, slug for logging). Frameworks
# absent from this map fail SAFELY: ``has_poi_for_framework`` returns True so
# the gate never skips on uncertainty.
_FRAMEWORK_POI_CHECKS = {
    "ob_retest": (_has_ob_retest_poi, "ob_retest"),
    "fvg_fill": (_has_fvg_fill_poi, "fvg_fill"),
    "breaker_re_entry": (_has_breaker_reentry_poi, "breaker_re_entry"),
    # Legacy alias — `breaker_retest` is the parser-side alias used historically
    # before `breaker_re_entry` became the production-facing label (CLAUDE.md
    # session 38, agent_config.yaml comment block in A9). The L2 verifier
    # treats both identically, so the pre-AI gate must too.
    "breaker_retest": (_has_breaker_reentry_poi, "breaker_retest"),
}

_FRAMEWORK_PROXIMITY_CHECKS = {
    "ob_retest": (_ob_retest_proximity, "ob_retest"),
    "fvg_fill": (_fvg_fill_proximity, "fvg_fill"),
    "breaker_re_entry": (_breaker_reentry_proximity, "breaker_re_entry"),
    "breaker_retest": (_breaker_reentry_proximity, "breaker_retest"),
}


def has_poi_for_framework(
    framework: str,
    mso: MarketStateObject,
    bias: str = "",
) -> bool:
    """Return True when *framework* has at least one POI candidate in *mso*.

    Unknown framework names return ``True`` (fail-safe: never skip on
    uncertainty — let the AI evaluate). This mirrors the rest of the pipeline
    where a typo in ``enabled_frameworks`` would surface as a CANDIDATE pass-
    through, not silent suppression.
    """
    entry = _FRAMEWORK_POI_CHECKS.get(framework)
    if entry is None:
        # Fail-safe: unknown framework → behave as if a POI exists so the AI
        # gets to evaluate.
        return True
    helper, _slug = entry
    return helper(mso, bias=bias)


def framework_poi_availability(
    mso: MarketStateObject,
    config: dict,
    bias: str = "",
) -> dict[str, bool]:
    """Return framework -> POI-present for the configured framework set.

    Observation-only callers use this to log what the pre-AI gate saw at the
    decision point. Unknown frameworks still return True through
    ``has_poi_for_framework`` so they cannot support a silent skip.
    """
    frameworks = _normalize_frameworks(
        config.get("model_a", {}).get("enabled_frameworks")
    )
    if not frameworks:
        return {}
    if mso is None or not getattr(mso, "timeframes", None):
        return {}
    return {
        framework: has_poi_for_framework(framework, mso, bias=bias)
        for framework in frameworks
    }


def poi_proximity_availability(
    mso: MarketStateObject,
    config: dict,
    *,
    current_price: float,
    bias: str = "",
) -> tuple[bool, str]:
    """Skip the AI call when every active framework's POI is far from price.

    This is the production version of the Apr 13 OB-proximity prescreen. It is
    framework-aware so the ob_retest/breaker distance check cannot suppress a
    valid fvg_fill route, and it fails open for unknown framework names.
    """
    frameworks = _normalize_frameworks(
        config.get("model_a", {}).get("enabled_frameworks")
    )
    if not frameworks:
        return False, ""
    if mso is None or not getattr(mso, "timeframes", None):
        return False, ""
    try:
        price = float(current_price)
    except (TypeError, ValueError):
        return False, ""
    if price <= 0:
        return False, ""

    gate_cfg = config.get("pre_ai_gates", {}) if isinstance(config, dict) else {}
    try:
        tolerance_pct = float(gate_cfg.get("poi_proximity_tolerance_pct", 0.01))
    except (TypeError, ValueError):
        return False, ""
    if tolerance_pct <= 0:
        return False, ""

    far_frameworks: list[str] = []
    nearest_gaps: list[float] = []
    for framework in frameworks:
        entry = _FRAMEWORK_PROXIMITY_CHECKS.get(framework)
        if entry is None:
            return False, ""
        helper, _slug = entry
        near, gap_pct = helper(mso, price, tolerance_pct, bias=bias)
        if near:
            return False, ""
        far_frameworks.append(framework)
        if gap_pct is not None:
            nearest_gaps.append(gap_pct)

    if not far_frameworks:
        return False, ""

    if nearest_gaps:
        reason = (
            f"price_far_from_pois_{min(nearest_gaps):.1f}pct_for_"
            f"{'+'.join(far_frameworks)}"
        )
    else:
        reason = f"no_near_pois_for_{'+'.join(far_frameworks)}"
    if bias in ("bullish", "bearish"):
        reason = f"{bias}_{reason}"
    return True, reason


# ---------------------------------------------------------------------------
# Public gate
# ---------------------------------------------------------------------------

def _normalize_frameworks(raw: object) -> list[str]:
    """Coerce the config value into a list[str] of framework names.

    Accepts list/tuple of strings; ignores empty / non-string entries. Any
    other type falls through to an empty list which the caller treats as
    "skip the gate" (passive) since there's nothing to evaluate against.
    """
    if not isinstance(raw, (list, tuple)):
        return []
    return [fw for fw in raw if isinstance(fw, str) and fw]


def h1_poi_availability(
    mso: MarketStateObject,
    config: dict,
    bias: str = "",
) -> tuple[bool, str]:
    """Skip the AI call when EVERY enabled framework has zero POIs.

    Behaviour summary:

      * For each framework in ``config['model_a']['enabled_frameworks']``
        invoke its registered helper. The first helper that returns ``True``
        (POI present) terminates the loop and the gate stays passive
        (``returns (False, "")``).
      * If every helper returns ``False`` the gate skips with a reason that
        encodes both the bias direction (when applicable) and the set of
        frameworks that came up empty.
      * Fail-safes (return ``(False, "")``):
          - empty/missing enabled_frameworks
          - unknown framework name (treated as POI-present by
            ``has_poi_for_framework``)
          - ``mso`` is missing or has no timeframes

    Bias semantics are inherited per-framework — see the individual
    ``_has_*_poi`` helpers. When *bias* is ``""`` or ``"no_bias"`` each
    helper falls back to direction-agnostic.

    The function name is preserved for backwards-compatibility with the
    orchestrator call site (``orchestrator.py:662``) and the existing
    ``pre_ai_gates.h1_poi_availability_enabled`` config flag — the H1-only
    semantic is no longer accurate (fvg_fill is M15-driven), but the gate's
    contract remains identical: skip the AI call iff a downstream L2 reject
    is guaranteed.
    """
    frameworks = _normalize_frameworks(
        config.get("model_a", {}).get("enabled_frameworks")
    )
    if not frameworks:
        return False, ""

    if mso is None or not getattr(mso, "timeframes", None):
        return False, ""

    directional = bias in ("bullish", "bearish")

    availability = framework_poi_availability(mso, config, bias=bias)
    empty_frameworks = [
        framework for framework in frameworks if availability.get(framework) is False
    ]
    if len(empty_frameworks) != len(frameworks):
        return False, ""

    # Every enabled framework came up empty — skip the AI call.
    if directional:
        reason = f"no_{bias}_pois_for_{'+'.join(empty_frameworks)}"
    else:
        reason = f"no_pois_for_{'+'.join(empty_frameworks)}"
    return True, reason
