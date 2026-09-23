"""Tests for pre-AI gates (src/components/pre_ai_gates.py).

These gates short-circuit the AI call to save API cost. Each skip must mirror
an existing L2 rejection condition — the tests encode that equivalence so a
future drift between pre-AI gates and L2 gets caught.

Multi-framework support shipped 2026-04-25: the gate now skips ONLY when every
enabled framework has zero POIs. The original ``["ob_retest"]`` regression
suite is preserved verbatim below; new tests cover ``fvg_fill``,
``breaker_re_entry``, mixed configurations, and the unknown-framework
fail-safe.
"""
from __future__ import annotations

from src.components.pre_ai_gates import (
    _has_breaker_reentry_poi,
    _has_fvg_fill_poi,
    _has_ob_retest_poi,
    framework_poi_availability,
    h1_poi_availability,
    has_poi_for_framework,
    poi_proximity_availability,
)
from src.models.market_state_models import (
    BreakerBlock,
    DataQuality,
    FairValueGap,
    MarketStateObject,
    OrderBlock,
    SessionLevels,
    StructureAnalysis,
    TimeframeState,
)


OB_RETEST_CFG = {"model_a": {"enabled_frameworks": ["ob_retest"]}}
FVG_FILL_CFG = {"model_a": {"enabled_frameworks": ["fvg_fill"]}}
BREAKER_RE_ENTRY_CFG = {"model_a": {"enabled_frameworks": ["breaker_re_entry"]}}
ALL_FRAMEWORKS_CFG = {
    "model_a": {
        "enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
    },
}


def _structure(direction: str = "bullish"):
    return StructureAnalysis(direction=direction)  # type: ignore[arg-type]


def _make_ob(
    mitigated: bool,
    direction: str = "bullish",
    *,
    low: float = 214.3,
    high: float = 214.5,
) -> OrderBlock:
    return OrderBlock(
        type=direction,  # type: ignore[arg-type]
        high=high, low=low, open=(low + high) / 2, close=(low + high) / 2,
        formation_index=0,
        formation_time="2026-04-20T00:00",
        causing_bos_index=1,
        mitigated=mitigated,
    )


def _make_breaker(
    retested: bool,
    direction: str = "bullish",
    *,
    low: float = 214.8,
    high: float = 215.0,
) -> BreakerBlock:
    return BreakerBlock(
        zone_high=high, zone_low=low,
        direction=direction,
        original_ob_direction="bearish" if direction == "bullish" else "bullish",
        formation_time="2026-04-20T00:00",
        mitigation_time="2026-04-20T01:00",
        causing_event="BOS",
        is_retested=retested,
        timeframe="H1",
    )


def _make_fvg(
    filled: bool,
    direction: str = "bullish",
    *,
    bottom: float = 214.2,
    top: float = 214.6,
) -> FairValueGap:
    if direction == "bullish":
        return FairValueGap(
            type="bullish",
            top=top, bottom=bottom, midpoint=(top + bottom) / 2,
            candle_indices=[10, 11, 12],
            formation_time="2026-04-20T00:00",
            filled=filled,
        )
    return FairValueGap(
        type="bearish",
        top=top, bottom=bottom, midpoint=(top + bottom) / 2,
        candle_indices=[10, 11, 12],
        formation_time="2026-04-20T00:00",
        filled=filled,
    )


def _make_mso(
    h1_obs=None,
    h1_breakers=None,
    m15_fvgs=None,
    include_h1: bool = True,
    include_m15: bool = False,
    h1_direction: str = "bullish",
) -> MarketStateObject:
    timeframes = {}
    if include_h1:
        timeframes["H1"] = TimeframeState(
            structure=_structure(h1_direction),
            order_blocks=list(h1_obs or []),
            breaker_blocks=list(h1_breakers or []),
        )
    if include_m15:
        timeframes["M15"] = TimeframeState(
            structure=_structure(h1_direction),
            fair_value_gaps=list(m15_fvgs or []),
        )
    return MarketStateObject(
        timestamp_utc="2026-04-20T00:00:00",
        timeframes=timeframes,
        session_levels=SessionLevels(asian_high=0, asian_low=0, pdh=0, pdl=0),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2026-04-20T00:00:00",
        ),
    )


# ===========================================================================
# Legacy ob_retest-only regression suite (preserved verbatim except for the
# reason-string format which now encodes the framework set).
# ===========================================================================

def test_all_obs_mitigated_no_breakers_skips():
    mso = _make_mso(
        h1_obs=[_make_ob(True), _make_ob(True, direction="bearish")],
        h1_breakers=[],
    )
    skipped, reason = h1_poi_availability(mso, OB_RETEST_CFG)
    assert skipped is True
    assert reason == "no_pois_for_ob_retest"


def test_empty_h1_lists_skip():
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    skipped, reason = h1_poi_availability(mso, OB_RETEST_CFG)
    assert skipped is True
    assert reason == "no_pois_for_ob_retest"


def test_all_obs_mitigated_all_breakers_retested_skips():
    mso = _make_mso(
        h1_obs=[_make_ob(True)],
        h1_breakers=[_make_breaker(retested=True)],
    )
    skipped, reason = h1_poi_availability(mso, OB_RETEST_CFG)
    assert skipped is True
    assert reason == "no_pois_for_ob_retest"


def test_single_unmitigated_ob_prevents_skip():
    mso = _make_mso(
        h1_obs=[_make_ob(True), _make_ob(False)],
        h1_breakers=[],
    )
    assert h1_poi_availability(mso, OB_RETEST_CFG) == (False, "")


def test_unmitigated_bearish_ob_prevents_skip():
    # Direction-agnostic: any unmitigated OB is enough to keep the gate passive,
    # because L2's _find_matching_ob also ignores OB direction.
    mso = _make_mso(
        h1_obs=[_make_ob(False, direction="bearish")],
        h1_breakers=[],
    )
    assert h1_poi_availability(mso, OB_RETEST_CFG) == (False, "")


def test_unretested_breaker_prevents_skip():
    mso = _make_mso(
        h1_obs=[_make_ob(True)],
        h1_breakers=[_make_breaker(retested=False)],
    )
    assert h1_poi_availability(mso, OB_RETEST_CFG) == (False, "")


def test_unretested_bearish_breaker_prevents_skip():
    mso = _make_mso(
        h1_obs=[],
        h1_breakers=[_make_breaker(retested=False, direction="bearish")],
    )
    assert h1_poi_availability(mso, OB_RETEST_CFG) == (False, "")


# ===========================================================================
# Scope / fail-safe behaviour
# ===========================================================================

def test_missing_model_a_config_bypasses_gate():
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    assert h1_poi_availability(mso, {}) == (False, "")


def test_empty_enabled_frameworks_bypasses_gate():
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    assert h1_poi_availability(mso, {"model_a": {"enabled_frameworks": []}}) == (False, "")


def test_missing_h1_timeframe_bypasses_gate():
    mso = _make_mso(include_h1=False)
    assert h1_poi_availability(mso, OB_RETEST_CFG) == (False, "")


def test_unknown_framework_name_does_not_skip():
    """Fail-safe: unknown framework → don't skip → run AI."""
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    cfg = {"model_a": {"enabled_frameworks": ["mystery_framework_v9000"]}}
    assert h1_poi_availability(mso, cfg) == (False, "")


def test_unknown_alongside_known_does_not_skip():
    """Fail-safe propagates: any unknown framework keeps the gate passive
    even when a known framework would otherwise skip."""
    mso = _make_mso(h1_obs=[], h1_breakers=[])  # ob_retest empty
    cfg = {"model_a": {"enabled_frameworks": ["ob_retest", "totally_new_framework"]}}
    assert h1_poi_availability(mso, cfg) == (False, "")


def test_framework_poi_availability_preserves_directional_empty_frameworks():
    mso = _make_mso(
        h1_obs=[_make_ob(mitigated=False, direction="bearish")],
        h1_breakers=[],
        m15_fvgs=[_make_fvg(filled=False, direction="bullish")],
        include_m15=True,
    )

    availability = framework_poi_availability(mso, ALL_FRAMEWORKS_CFG, bias="bullish")

    assert availability == {
        "ob_retest": False,
        "fvg_fill": True,
        "breaker_re_entry": False,
    }
    assert h1_poi_availability(mso, ALL_FRAMEWORKS_CFG, bias="bullish") == (False, "")


def test_non_list_enabled_frameworks_bypasses_gate():
    """Hostile config (string instead of list) → bypass, don't crash."""
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    cfg = {"model_a": {"enabled_frameworks": "ob_retest"}}
    assert h1_poi_availability(mso, cfg) == (False, "")


# ===========================================================================
# POI proximity gate (Apr 13 OB-proximity conversion)
# ===========================================================================

def test_poi_proximity_skips_when_all_framework_pois_are_far():
    mso = _make_mso(
        h1_obs=[_make_ob(False, low=100.0, high=101.0)],
        h1_breakers=[_make_breaker(False, low=102.0, high=103.0)],
        m15_fvgs=[_make_fvg(False, bottom=104.0, top=105.0)],
        include_m15=True,
    )
    skipped, reason = poi_proximity_availability(
        mso,
        {
            **ALL_FRAMEWORKS_CFG,
            "pre_ai_gates": {"poi_proximity_tolerance_pct": 0.01},
        },
        current_price=120.0,
        bias="bullish",
    )

    assert skipped is True
    assert reason == (
        "bullish_price_far_from_pois_12.5pct_for_"
        "ob_retest+fvg_fill+breaker_re_entry"
    )


def test_poi_proximity_keeps_ai_when_fvg_route_is_near_even_if_h1_pois_far():
    mso = _make_mso(
        h1_obs=[_make_ob(False, low=100.0, high=101.0)],
        h1_breakers=[_make_breaker(False, low=102.0, high=103.0)],
        m15_fvgs=[_make_fvg(False, bottom=119.4, top=119.8)],
        include_m15=True,
    )

    assert poi_proximity_availability(
        mso,
        {
            **ALL_FRAMEWORKS_CFG,
            "pre_ai_gates": {"poi_proximity_tolerance_pct": 0.01},
        },
        current_price=120.0,
        bias="bullish",
    ) == (False, "")


def test_poi_proximity_keeps_ai_when_ob_retest_poi_is_near():
    mso = _make_mso(
        h1_obs=[_make_ob(False, low=119.0, high=119.4)],
        h1_breakers=[],
    )

    assert poi_proximity_availability(
        mso,
        {
            **OB_RETEST_CFG,
            "pre_ai_gates": {"poi_proximity_tolerance_pct": 0.01},
        },
        current_price=120.0,
        bias="bullish",
    ) == (False, "")


def test_poi_proximity_unknown_framework_fails_open():
    mso = _make_mso(h1_obs=[], h1_breakers=[])
    cfg = {
        "model_a": {"enabled_frameworks": ["ob_retest", "new_framework"]},
        "pre_ai_gates": {"poi_proximity_tolerance_pct": 0.01},
    }

    assert poi_proximity_availability(
        mso, cfg, current_price=120.0, bias="bullish"
    ) == (False, "")


# ===========================================================================
# Multi-framework: skip ONLY when ALL enabled frameworks are empty
# ===========================================================================

def test_all_frameworks_enabled_all_pois_empty_skips():
    """Empty MSO + all 3 frameworks enabled → skip with combined reason."""
    mso = _make_mso(
        h1_obs=[_make_ob(True)],          # OB mitigated → empty for ob_retest
        h1_breakers=[_make_breaker(True)],  # retested → empty for breaker_re_entry
        m15_fvgs=[_make_fvg(filled=True)],  # filled → empty for fvg_fill
        include_m15=True,
    )
    skipped, reason = h1_poi_availability(mso, ALL_FRAMEWORKS_CFG)
    assert skipped is True
    # All three frameworks should appear in the reason (order = enabled order)
    assert "ob_retest" in reason
    assert "fvg_fill" in reason
    assert "breaker_re_entry" in reason


def test_all_frameworks_enabled_only_obs_present_does_not_skip():
    mso = _make_mso(
        h1_obs=[_make_ob(False, direction="bullish")],
        h1_breakers=[_make_breaker(True)],
        m15_fvgs=[_make_fvg(filled=True)],
        include_m15=True,
    )
    assert h1_poi_availability(mso, ALL_FRAMEWORKS_CFG) == (False, "")


def test_all_frameworks_enabled_only_fvgs_present_does_not_skip():
    mso = _make_mso(
        h1_obs=[_make_ob(True)],
        h1_breakers=[_make_breaker(True)],
        m15_fvgs=[_make_fvg(filled=False, direction="bullish")],
        include_m15=True,
    )
    assert h1_poi_availability(mso, ALL_FRAMEWORKS_CFG) == (False, "")


def test_all_frameworks_enabled_only_breakers_present_does_not_skip():
    mso = _make_mso(
        h1_obs=[_make_ob(True)],
        h1_breakers=[_make_breaker(retested=False, direction="bullish")],
        m15_fvgs=[_make_fvg(filled=True)],
        include_m15=True,
    )
    assert h1_poi_availability(mso, ALL_FRAMEWORKS_CFG) == (False, "")


# ===========================================================================
# Per-framework regression: single-framework configs match the framework's
# own helper exactly.
# ===========================================================================

def test_fvg_fill_alone_skips_when_no_unfilled_fvgs():
    mso = _make_mso(
        h1_obs=[_make_ob(False)],   # would PASS ob_retest, but ob_retest disabled
        m15_fvgs=[_make_fvg(filled=True)],
        include_m15=True,
    )
    skipped, reason = h1_poi_availability(mso, FVG_FILL_CFG)
    assert skipped is True
    assert "fvg_fill" in reason


def test_fvg_fill_alone_passive_when_unfilled_fvg_present():
    mso = _make_mso(
        h1_obs=[],
        m15_fvgs=[_make_fvg(filled=False)],
        include_m15=True,
    )
    assert h1_poi_availability(mso, FVG_FILL_CFG) == (False, "")


def test_fvg_fill_missing_m15_skips_framework_not_passive():
    """No M15 → fvg_fill helper returns False; with fvg_fill alone the gate
    skips. This intentionally differs from H1-missing for ob_retest-only
    (which bypasses) — the asymmetry is the per-framework helper's own
    semantic, and the framework-loop simply aggregates."""
    mso = _make_mso(include_h1=True, include_m15=False)
    skipped, reason = h1_poi_availability(mso, FVG_FILL_CFG)
    assert skipped is True
    assert "fvg_fill" in reason


def test_breaker_re_entry_alone_skips_when_no_unretested_breakers():
    mso = _make_mso(
        h1_obs=[_make_ob(False)],  # would PASS ob_retest, disabled here
        h1_breakers=[_make_breaker(retested=True)],
    )
    skipped, reason = h1_poi_availability(mso, BREAKER_RE_ENTRY_CFG)
    assert skipped is True
    assert "breaker_re_entry" in reason


def test_breaker_re_entry_alone_passive_when_unretested_breaker_present():
    mso = _make_mso(
        h1_obs=[],
        h1_breakers=[_make_breaker(retested=False, direction="bullish")],
    )
    assert h1_poi_availability(mso, BREAKER_RE_ENTRY_CFG) == (False, "")


def test_breaker_retest_legacy_alias_routes_to_breaker_re_entry_helper():
    """Legacy ``breaker_retest`` framework name shares the same L2 path and
    therefore the same pre-AI helper."""
    mso = _make_mso(
        h1_obs=[],
        h1_breakers=[_make_breaker(retested=False, direction="bullish")],
    )
    cfg = {"model_a": {"enabled_frameworks": ["breaker_retest"]}}
    assert h1_poi_availability(mso, cfg) == (False, "")

    # Empty breakers → skip.
    mso2 = _make_mso(h1_obs=[], h1_breakers=[_make_breaker(retested=True)])
    skipped, reason = h1_poi_availability(mso2, cfg)
    assert skipped is True
    assert "breaker_retest" in reason


# ===========================================================================
# Direction-aware (bias) behaviour — covers fvg_fill + breaker_re_entry too
# ===========================================================================

class TestDirectionAware:
    """Bias-aware pre-AI POI checks: only skip when no POI supports the
    deterministic bias direction. Mirrors L2 direction matching."""

    def test_no_bias_falls_back_to_agnostic(self):
        # One unmitigated bearish OB, no bullish → agnostic fallback keeps gate
        # passive because SOME POI exists.
        mso = _make_mso(
            h1_obs=[_make_ob(False, direction="bearish")],
            h1_breakers=[],
        )
        assert h1_poi_availability(mso, OB_RETEST_CFG, bias="") == (False, "")

    def test_bullish_bias_with_only_bearish_pois_skips(self):
        mso = _make_mso(
            h1_obs=[_make_ob(False, direction="bearish")],
            h1_breakers=[],
        )
        skipped, reason = h1_poi_availability(mso, OB_RETEST_CFG, bias="bullish")
        assert skipped is True
        assert "bullish" in reason
        assert "ob_retest" in reason

    def test_bullish_bias_with_bullish_ob_does_not_skip(self):
        mso = _make_mso(
            h1_obs=[_make_ob(False, direction="bullish")],
            h1_breakers=[],
        )
        assert h1_poi_availability(mso, OB_RETEST_CFG, bias="bullish") == (False, "")

    def test_fvg_fill_bullish_bias_with_only_bearish_fvgs_skips(self):
        mso = _make_mso(
            m15_fvgs=[_make_fvg(filled=False, direction="bearish")],
            include_m15=True,
        )
        skipped, reason = h1_poi_availability(mso, FVG_FILL_CFG, bias="bullish")
        assert skipped is True
        assert "bullish" in reason
        assert "fvg_fill" in reason

    def test_fvg_fill_bullish_bias_with_bullish_fvg_does_not_skip(self):
        mso = _make_mso(
            m15_fvgs=[_make_fvg(filled=False, direction="bullish")],
            include_m15=True,
        )
        assert h1_poi_availability(mso, FVG_FILL_CFG, bias="bullish") == (False, "")

    def test_breaker_re_entry_bullish_bias_with_only_bearish_breakers_skips(self):
        mso = _make_mso(
            h1_breakers=[_make_breaker(retested=False, direction="bearish")],
        )
        skipped, reason = h1_poi_availability(
            mso, BREAKER_RE_ENTRY_CFG, bias="bullish"
        )
        assert skipped is True
        assert "bullish" in reason
        assert "breaker_re_entry" in reason

    def test_breaker_re_entry_bullish_bias_with_bullish_breaker_does_not_skip(self):
        mso = _make_mso(
            h1_breakers=[_make_breaker(retested=False, direction="bullish")],
        )
        assert h1_poi_availability(
            mso, BREAKER_RE_ENTRY_CFG, bias="bullish"
        ) == (False, "")

    def test_multi_framework_bullish_bias_one_aligned_keeps_passive(self):
        """One bullish FVG present, OB+breaker stack only has bearish — gate
        must stay passive because fvg_fill has an aligned POI."""
        mso = _make_mso(
            h1_obs=[_make_ob(False, direction="bearish")],
            h1_breakers=[_make_breaker(retested=False, direction="bearish")],
            m15_fvgs=[_make_fvg(filled=False, direction="bullish")],
            include_m15=True,
        )
        assert h1_poi_availability(
            mso, ALL_FRAMEWORKS_CFG, bias="bullish"
        ) == (False, "")

    def test_multi_framework_bullish_bias_no_aligned_skips(self):
        """All POIs are bearish; bullish bias → all 3 frameworks empty → skip."""
        mso = _make_mso(
            h1_obs=[_make_ob(False, direction="bearish")],
            h1_breakers=[_make_breaker(retested=False, direction="bearish")],
            m15_fvgs=[_make_fvg(filled=False, direction="bearish")],
            include_m15=True,
        )
        skipped, reason = h1_poi_availability(
            mso, ALL_FRAMEWORKS_CFG, bias="bullish"
        )
        assert skipped is True
        assert "bullish" in reason

    def test_no_bias_string_treated_as_agnostic(self):
        # Mixed OBs: bullish present AND bearish present. Agnostic fallback: keep
        # gate passive because SOME unmitigated OB exists.
        mso = _make_mso(
            h1_obs=[
                _make_ob(False, direction="bullish"),
                _make_ob(False, direction="bearish"),
            ],
            h1_breakers=[],
        )
        assert h1_poi_availability(mso, OB_RETEST_CFG, bias="no_bias") == (False, "")

    def test_h1_missing_remains_passive_with_bias(self):
        mso = _make_mso(include_h1=False)
        assert h1_poi_availability(mso, OB_RETEST_CFG, bias="bullish") == (False, "")
        assert h1_poi_availability(mso, OB_RETEST_CFG, bias="bearish") == (False, "")


# ===========================================================================
# has_poi_for_framework dispatcher — direct unit tests
# ===========================================================================

class TestHasPOIForFramework:
    """Direct tests of the dispatcher used by the framework loop."""

    def test_unknown_framework_returns_true(self):
        mso = _make_mso(h1_obs=[], h1_breakers=[])
        assert has_poi_for_framework("nonsense_framework", mso) is True

    def test_ob_retest_dispatch_matches_helper(self):
        mso_with = _make_mso(h1_obs=[_make_ob(False)])
        mso_without = _make_mso(h1_obs=[_make_ob(True)])
        assert has_poi_for_framework("ob_retest", mso_with) is True
        assert has_poi_for_framework("ob_retest", mso_without) is False

    def test_fvg_fill_dispatch_matches_helper(self):
        mso_with = _make_mso(m15_fvgs=[_make_fvg(False)], include_m15=True)
        mso_without = _make_mso(m15_fvgs=[_make_fvg(True)], include_m15=True)
        assert has_poi_for_framework("fvg_fill", mso_with) is True
        assert has_poi_for_framework("fvg_fill", mso_without) is False

    def test_breaker_re_entry_dispatch_matches_helper(self):
        mso_with = _make_mso(h1_breakers=[_make_breaker(False)])
        mso_without = _make_mso(h1_breakers=[_make_breaker(True)])
        assert has_poi_for_framework("breaker_re_entry", mso_with) is True
        assert has_poi_for_framework("breaker_re_entry", mso_without) is False


# ===========================================================================
# Direct helper tests — guard against drift between framework-local helpers
# and the L2 verifier semantics.
# ===========================================================================

class TestFrameworkHelpers:
    def test_ob_retest_helper_no_h1(self):
        mso = _make_mso(include_h1=False)
        assert _has_ob_retest_poi(mso) is False

    def test_ob_retest_helper_only_breakers(self):
        mso = _make_mso(
            h1_obs=[_make_ob(True)],
            h1_breakers=[_make_breaker(retested=False)],
        )
        assert _has_ob_retest_poi(mso) is True

    def test_fvg_fill_helper_no_m15(self):
        mso = _make_mso(include_m15=False)
        assert _has_fvg_fill_poi(mso) is False

    def test_fvg_fill_helper_filled_only(self):
        mso = _make_mso(
            m15_fvgs=[_make_fvg(True), _make_fvg(True, direction="bearish")],
            include_m15=True,
        )
        assert _has_fvg_fill_poi(mso) is False

    def test_fvg_fill_helper_directional(self):
        mso = _make_mso(
            m15_fvgs=[_make_fvg(False, direction="bullish")],
            include_m15=True,
        )
        assert _has_fvg_fill_poi(mso, bias="bullish") is True
        assert _has_fvg_fill_poi(mso, bias="bearish") is False
        # Bidirectional fallback when bias is empty:
        assert _has_fvg_fill_poi(mso, bias="") is True

    def test_breaker_reentry_helper_no_h1(self):
        mso = _make_mso(include_h1=False)
        assert _has_breaker_reentry_poi(mso) is False

    def test_breaker_reentry_helper_directional(self):
        mso = _make_mso(
            h1_breakers=[_make_breaker(retested=False, direction="bullish")],
        )
        assert _has_breaker_reentry_poi(mso, bias="bullish") is True
        assert _has_breaker_reentry_poi(mso, bias="bearish") is False
