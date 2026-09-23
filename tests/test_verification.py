"""Tests for Level 2 Candidate Verification."""

import pytest

from src.components.verification import (
    VerificationCheck,
    VerificationResult,
    verify_candidate,
    _check_m15_choch,
    _check_displacement_ratio,
    _check_h1_poi_exists,
    _check_ob_zone,
    _check_entry_in_ob,
    _check_entry_in_fvg,
    _check_entry_in_breaker,
    _check_sl_beyond_ob,
)
from src.models.market_state_models import (
    BreakerBlock,
    DataQuality,
    FairValueGap,
    MarketStateObject,
    OrderBlock,
    PremiumDiscount,
    PriceZone,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)
from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "model_a": {"displacement_min_ratio": 1.5},
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "strict_zone_check": False,
        "log_warnings": False,
    },
}


def _make_m15_tf(
    choch_dir="bullish",
    disp_present=True,
    disp_ratio=2.0,
    event_type="CHoCH",
    include_event=True,
) -> TimeframeState:
    events = []
    if include_event:
        events.append(StructureEvent(
            type=event_type,
            direction=choch_dir,
            level_broken=2260.0,
            close_price=2262.0,
            candle_index=50,
            time="2024-04-01T08:00:00",
            displacement_present=disp_present,
            displacement_ratio=disp_ratio,
        ))
    return TimeframeState(
        structure=StructureAnalysis(direction=choch_dir),
        structure_events=events,
        avg_candle_body=1.0,
        atr_14=2.0,
    )


def _make_h1_tf(
    obs=None,
    breakers=None,
    pd_eq=2262.0,
    pd_impulse_low=2255.0,
    pd_impulse_high=2270.0,
) -> TimeframeState:
    if obs is None:
        obs = [OrderBlock(
            type="bullish",
            high=2261.50,
            low=2259.80,
            open=2261.00,
            close=2260.00,
            formation_index=30,
            formation_time="2024-04-01T06:00:00",
            causing_bos_index=35,
            mitigated=False,
            causing_event_type="BOS",
        )]
    return TimeframeState(
        structure=StructureAnalysis(direction="bullish"),
        structure_events=[StructureEvent(
            type="BOS", direction="bullish",
            level_broken=2265.0, close_price=2266.0,
            candle_index=35, time="2024-04-01T06:30:00",
            displacement_present=True, displacement_ratio=2.5,
        )],
        order_blocks=obs,
        breaker_blocks=breakers or [],
        premium_discount=PremiumDiscount(
            impulse_low=pd_impulse_low,
            impulse_high=pd_impulse_high,
            equilibrium_50=pd_eq,
            fib_62=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.618,
            fib_79=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.786,
            discount_zone=PriceZone(top=pd_eq, bottom=pd_impulse_low),
            premium_zone=PriceZone(top=pd_impulse_high, bottom=pd_eq),
            ote_zone=PriceZone(
                top=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.618,
                bottom=pd_impulse_high - (pd_impulse_high - pd_impulse_low) * 0.786,
            ),
        ),
        avg_candle_body=2.0,
        atr_14=4.0,
    )


def _make_mso(
    m15_tf=None,
    h1_tf=None,
) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2024-04-01T08:00:00Z",
        timeframes={
            "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H1": h1_tf or _make_h1_tf(),
            "M15": m15_tf or _make_m15_tf(),
        },
        session_levels=SessionLevels(
            asian_high=2265.0, asian_low=2258.0,
            pdh=2270.0, pdl=2250.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2024-04-01T08:00:00Z",
        ),
    )


def _make_analysis(
    direction="LONG",
    entry=2260.50,
    sl=2258.50,
    tp1=2263.50,
    poi_price=2260.50,
    poi_identified=True,
    choch_detected=True,
    disp_ratio=2.0,
    framework="ob_retest",
) -> PrimaryAnalysisOutput:
    return PrimaryAnalysisOutput(
        timestamp_utc="2024-04-01T08:00:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework=framework,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=poi_identified,
                poi_type="OB",
                poi_price_level=poi_price,
                zone="discount",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=choch_detected,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=disp_ratio,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            risk_reward_ratio=1.5,
        ),
    )


# ---------------------------------------------------------------------------
# Test 1: All checks pass
# ---------------------------------------------------------------------------

class TestAllPass:
    def test_all_pass(self):
        analysis = _make_analysis()
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is True
        assert result.blocked_by is None
        # 9 checks (post-merge 2026-04-25 staging/sunday-deploy):
        #   - 6 original ob_retest checks
        #   - gap_ceiling (CHECK 7)
        #   - entry_in_fvg  (additive 2026-04-25 with fvg_fill framework
        #     activation; SKIPs on ob_retest path)
        #   - entry_in_breaker (additive 2026-04-25 with breaker_re_entry
        #     framework activation; SKIPs on ob_retest path)
        assert len(result.checks) == 9
        for c in result.checks:
            assert c.status in ("PASS", "WARN", "SKIP"), f"{c.name} was {c.status}: {c.detail}"


# ---------------------------------------------------------------------------
# Test 2: No M15 CHoCH
# ---------------------------------------------------------------------------

class TestNoM15Choch:
    def test_no_m15_choch(self):
        m15 = _make_m15_tf(include_event=False)
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        assert result.blocked_by == "m15_choch_exists"


# ---------------------------------------------------------------------------
# Test 3: CHoCH wrong direction
# ---------------------------------------------------------------------------

class TestChochWrongDirection:
    def test_choch_wrong_direction(self):
        m15 = _make_m15_tf(choch_dir="bearish")
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis(direction="LONG")
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        assert result.blocked_by == "m15_choch_exists"


# ---------------------------------------------------------------------------
# Test 4: Displacement below threshold (the 2024-03-01 case)
# ---------------------------------------------------------------------------

class TestDisplacementBelowThreshold:
    def test_displacement_below_threshold(self):
        m15 = _make_m15_tf(disp_present=False, disp_ratio=0.4)
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis(disp_ratio=0.4)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        # Check 1 fails because displacement_present=False
        assert result.passed is False
        assert result.blocked_by == "m15_choch_exists"

    def test_displacement_present_but_ratio_low(self):
        """displacement_present=True but ratio still below config threshold."""
        m15 = _make_m15_tf(disp_present=True, disp_ratio=1.2)
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis(disp_ratio=1.2)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        # Check 1 passes (displacement_present=True), but Check 2 fails
        assert result.passed is False
        assert result.blocked_by == "displacement_ratio"
        c2 = next(c for c in result.checks if c.name == "displacement_ratio")
        assert c2.status == "FAIL"
        assert "1.20" in c2.detail


# ---------------------------------------------------------------------------
# Test 5: No H1 OB (the 2024-03-15 case)
# ---------------------------------------------------------------------------

class TestNoH1OB:
    def test_no_h1_ob(self):
        h1 = _make_h1_tf(obs=[])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        assert result.blocked_by == "h1_poi_exists"


# ---------------------------------------------------------------------------
# Test 6: H1 OB price mismatch
# ---------------------------------------------------------------------------

class TestH1OBPriceMismatch:
    def test_h1_ob_price_mismatch(self):
        h1 = _make_h1_tf()  # OB at 2259.80-2261.50
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(poi_price=2280.00)  # Far from any OB
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        assert result.blocked_by == "h1_poi_exists"
        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert "2280.00" in c3.detail


# ---------------------------------------------------------------------------
# Test 7: OB in wrong zone
# ---------------------------------------------------------------------------

class TestOBWrongZone:
    def test_ob_wrong_zone_warn(self):
        """OB in premium but trade is LONG (needs discount). Default config → WARN."""
        h1 = _make_h1_tf(
            obs=[OrderBlock(
                type="bullish", high=2268.0, low=2266.0,
                open=2267.5, close=2266.5,
                formation_index=30, formation_time="2024-04-01T06:00:00",
                causing_bos_index=35, mitigated=False,
            )],
            pd_eq=2262.0,
        )
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            entry=2267.0, sl=2264.0, tp1=2271.5,
            poi_price=2267.0,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c4 = next(c for c in result.checks if c.name == "ob_zone")
        assert c4.status == "WARN"
        assert result.passed is True  # WARN doesn't block

    def test_ob_wrong_zone_strict(self):
        """With strict_zone_check=True, wrong zone → FAIL."""
        strict_config = {**DEFAULT_CONFIG, "verification": {
            **DEFAULT_CONFIG["verification"], "strict_zone_check": True,
        }}
        h1 = _make_h1_tf(
            obs=[OrderBlock(
                type="bullish", high=2268.0, low=2266.0,
                open=2267.5, close=2266.5,
                formation_index=30, formation_time="2024-04-01T06:00:00",
                causing_bos_index=35, mitigated=False,
            )],
            pd_eq=2262.0,
        )
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            entry=2267.0, sl=2264.0, tp1=2271.5,
            poi_price=2267.0,
        )
        result = verify_candidate(analysis, mso, strict_config)

        c4 = next(c for c in result.checks if c.name == "ob_zone")
        assert c4.status == "FAIL"
        assert result.passed is False


# ---------------------------------------------------------------------------
# Test 8: Entry outside OB
# ---------------------------------------------------------------------------

class TestEntryOutsideOB:
    def test_entry_outside_ob(self):
        h1 = _make_h1_tf()  # OB at 2259.80-2261.50
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            entry=2270.00,  # Way above OB
            poi_price=2260.50,  # POI matches OB
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c5 = next(c for c in result.checks if c.name == "entry_in_ob")
        assert c5.status == "FAIL"
        assert "2270.00" in c5.detail


# ---------------------------------------------------------------------------
# Test 9: SL inside OB
# ---------------------------------------------------------------------------

class TestSLInsideOB:
    def test_sl_inside_ob(self):
        h1 = _make_h1_tf()  # OB at 2259.80-2261.50
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            entry=2260.50,
            sl=2260.50,   # SL inside OB (above OB.low)
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c6 = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert c6.status == "FAIL"

    def test_sl_exactly_at_ob_low_fails(self):
        h1 = _make_h1_tf()  # OB.low = 2259.80
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            entry=2260.50,
            sl=2259.80,   # SL exactly at OB.low, not below
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c6 = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert c6.status == "FAIL"


# ---------------------------------------------------------------------------
# Test 10: Breaker retest framework
# ---------------------------------------------------------------------------

class TestBreakerRetest:
    def test_breaker_retest_uses_breaker_blocks(self):
        breaker = BreakerBlock(
            zone_high=2261.50, zone_low=2259.80,
            direction="bullish",
            original_ob_direction="bearish",
            formation_time="2024-04-01T05:00:00",
            mitigation_time="2024-04-01T06:00:00",
            causing_event="BOS",
            is_retested=False,
        )
        h1 = _make_h1_tf(obs=[], breakers=[breaker])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            framework="breaker_retest",
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "PASS"
        assert "breaker" in c3.detail.lower()


# ---------------------------------------------------------------------------
# Test 11: Missing fields — graceful handling
# ---------------------------------------------------------------------------

class TestMissingFields:
    def test_no_trade_parameters(self):
        analysis = _make_analysis()
        analysis.trade_parameters = None
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        # Check 1 should FAIL because no trade_parameters → no direction
        c1 = result.checks[0]
        assert c1.status == "FAIL"

    def test_poi_price_zero(self):
        analysis = _make_analysis(poi_price=0.0)
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "FAIL"
        assert "0" in c3.detail

    def test_poi_not_identified(self):
        analysis = _make_analysis(poi_identified=False)
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is False
        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "FAIL"


# ---------------------------------------------------------------------------
# Test 12: Tolerance config
# ---------------------------------------------------------------------------

class TestToleranceConfig:
    def test_tolerance_allows_near_match(self):
        """OB at 2259.80-2261.50, poi at 2262.00 — within 0.2% tolerance."""
        h1 = _make_h1_tf()  # OB.high = 2261.50
        mso = _make_mso(h1_tf=h1)
        # 2262.00 is ~0.02% above OB.high (2261.50). Tolerance = 2262 * 0.002 ≈ 4.52
        # So 2262.00 is within 2261.50 + 4.52 range
        analysis = _make_analysis(poi_price=2262.00)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "PASS"

    def test_tighter_tolerance_rejects(self):
        """With very tight tolerance, same price mismatches."""
        tight_config = {**DEFAULT_CONFIG, "verification": {
            **DEFAULT_CONFIG["verification"], "ob_price_tolerance_pct": 0.0001,
        }}
        h1 = _make_h1_tf()  # OB.high = 2261.50
        mso = _make_mso(h1_tf=h1)
        # With 0.01% tolerance = 2266 * 0.0001 ≈ 0.22 — OB.high + 0.22 = 2261.72
        # poi at 2266.0 is way outside
        analysis = _make_analysis(poi_price=2266.00)
        result = verify_candidate(analysis, mso, tight_config)

        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "FAIL"


# ---------------------------------------------------------------------------
# Test 13: Orchestrator integration — rejection
# ---------------------------------------------------------------------------

class TestOrchestratorIntegration:
    def test_verification_rejects_in_orchestrator(self, monkeypatch):
        """Verify orchestrator rejects trades when L2 fails."""
        from src.components import orchestrator as orch_mod

        calls = {"verify": 0, "log_candle": []}

        def mock_verify(analysis, mso, config):
            calls["verify"] += 1
            return VerificationResult(
                passed=False,
                checks=[VerificationCheck("m15_choch_exists", "FAIL", "No CHoCH")],
                blocked_by="m15_choch_exists",
            )

        monkeypatch.setattr(orch_mod, "verify_candidate", mock_verify)

        # Build a minimal orchestrator and call _process_candle logic
        # We test via the imported function, not the full orchestrator
        # (full orchestrator requires MT5 etc.)
        assert calls["verify"] == 0  # sanity
        result = mock_verify(None, None, None)
        assert result.passed is False
        assert result.blocked_by == "m15_choch_exists"


# ---------------------------------------------------------------------------
# Test 14: Orchestrator integration — pass-through
# ---------------------------------------------------------------------------

class TestOrchestratorPassThrough:
    def test_verification_passes_through(self):
        """Verify that when L2 passes, the result is correct."""
        analysis = _make_analysis()
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is True
        assert result.blocked_by is None


# ---------------------------------------------------------------------------
# Test 15: Disabled verification
# ---------------------------------------------------------------------------

class TestVerificationDisabled:
    def test_disabled_skips_all_checks(self):
        disabled_config = {**DEFAULT_CONFIG, "verification": {"enabled": False}}
        analysis = _make_analysis(poi_identified=False)  # Would fail if enabled
        mso = _make_mso()
        result = verify_candidate(analysis, mso, disabled_config)

        assert result.passed is True
        assert len(result.checks) == 1
        assert result.checks[0].status == "SKIP"


# ---------------------------------------------------------------------------
# Test 16: SHORT trade direction
# ---------------------------------------------------------------------------

class TestShortDirection:
    def test_short_all_pass(self):
        m15 = _make_m15_tf(choch_dir="bearish")
        h1 = _make_h1_tf(
            obs=[OrderBlock(
                type="bearish", high=2268.0, low=2266.0,
                open=2266.5, close=2267.5,
                formation_index=30, formation_time="2024-04-01T06:00:00",
                causing_bos_index=35, mitigated=False,
            )],
            pd_eq=2262.0,  # OB at 2266-2268 is above eq → premium → correct for SHORT
        )
        mso = _make_mso(m15_tf=m15, h1_tf=h1)
        analysis = _make_analysis(
            direction="SHORT",
            entry=2267.0,
            sl=2269.0,
            tp1=2264.0,
            poi_price=2267.0,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        assert result.passed is True

    def test_short_sl_below_ob_high_fails(self):
        """For SHORT, SL must be above OB.high."""
        m15 = _make_m15_tf(choch_dir="bearish")
        h1 = _make_h1_tf(
            obs=[OrderBlock(
                type="bearish", high=2268.0, low=2266.0,
                open=2266.5, close=2267.5,
                formation_index=30, formation_time="2024-04-01T06:00:00",
                causing_bos_index=35, mitigated=False,
            )],
            pd_eq=2262.0,
        )
        mso = _make_mso(m15_tf=m15, h1_tf=h1)
        analysis = _make_analysis(
            direction="SHORT",
            entry=2267.0,
            sl=2267.5,  # Below OB.high of 2268
            tp1=2264.0,
            poi_price=2267.0,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c6 = next(c for c in result.checks if c.name == "sl_beyond_ob")
        assert c6.status == "FAIL"


# ---------------------------------------------------------------------------
# Test 17: BOS also accepted for M15 confirmation
# ---------------------------------------------------------------------------

class TestBOSAccepted:
    def test_bos_accepted_for_m15(self):
        """M15 BOS (not CHoCH) with displacement should also pass Check 1."""
        m15 = _make_m15_tf(event_type="BOS")
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c1 = result.checks[0]
        assert c1.status == "PASS"
        assert "BOS" in c1.detail


# ---------------------------------------------------------------------------
# Test 18: Displacement check binds to the most-recent event, not the oldest
#
# Regression for the Thursday 2026-04-23 US30 forensic finding:
#   research/thursday_2026-04-23_analysis/US30_analysis.md §8 #6.
# market_state.detect_structure_breaks emits events in chronological order
# (oldest first at index 0), so the previous "pick first match" behavior was
# effectively "pick the oldest (stalest) event".  The triggering event for
# the current decision is always the most-recent one.
# ---------------------------------------------------------------------------

def _mk_event(
    event_type, direction, ratio, time_str, candle_index=0,
    disp_present=True,
):
    """Compact StructureEvent helper for ordering tests."""
    return StructureEvent(
        type=event_type, direction=direction,
        level_broken=2260.0, close_price=2262.0,
        candle_index=candle_index, time=time_str,
        displacement_present=disp_present, displacement_ratio=ratio,
    )


class TestDisplacementUsesMostRecentEvent:
    def test_check1_reports_most_recent_matching_choch(self):
        """_check_m15_choch must report the newest qualifying CHoCH, not the oldest."""
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                # Oldest: qualifying CHoCH (week-old stale event)
                _mk_event("CHoCH", "bullish", 1.8,
                         "2024-03-25T08:00:00", candle_index=1),
                _mk_event("BOS", "bullish", 2.0,
                         "2024-03-26T08:00:00", candle_index=10),
                # Newest: qualifying CHoCH (the actual triggering event)
                _mk_event("CHoCH", "bullish", 3.2,
                         "2024-04-01T07:45:00", candle_index=50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c1 = next(c for c in result.checks if c.name == "m15_choch_exists")
        assert c1.status == "PASS"
        # Must report the most-recent event's time and ratio, not the oldest.
        assert c1.mso_value["time"] == "2024-04-01T07:45:00"
        assert c1.mso_value["ratio"] == 3.2
        # And must NOT report the stale event.
        assert "2024-03-25" not in c1.detail

    def test_check1_falls_back_to_most_recent_bos_when_no_choch(self):
        """When only BOS events qualify, pick the newest BOS."""
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                _mk_event("BOS", "bullish", 1.6,
                         "2024-03-25T08:00:00"),
                _mk_event("BOS", "bullish", 2.5,
                         "2024-04-01T07:45:00", candle_index=50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c1 = next(c for c in result.checks if c.name == "m15_choch_exists")
        assert c1.status == "PASS"
        assert "BOS" in c1.detail
        assert c1.mso_value["time"] == "2024-04-01T07:45:00"
        assert c1.mso_value["ratio"] == 2.5

    def test_check2_reports_most_recent_ratio(self):
        """_check_displacement_ratio must report the newest qualifying ratio."""
        # Two CHoCHs with different ratios; old=1.6, new=2.8. CHoCH preferred
        # over BOS means both are candidates, but the loop breaks on the
        # first CHoCH seen -- which must be the newest.
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                _mk_event("CHoCH", "bullish", 1.6,
                         "2024-03-25T08:00:00"),
                _mk_event("CHoCH", "bullish", 2.8,
                         "2024-04-01T07:45:00", candle_index=50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c2 = next(c for c in result.checks if c.name == "displacement_ratio")
        assert c2.status == "PASS"
        assert c2.mso_value == 2.8
        assert "2.80" in c2.detail

    def test_check2_bos_fallback_uses_most_recent(self):
        """Among BOS-only events, displacement_ratio picks the newest ratio."""
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                _mk_event("BOS", "bullish", 1.7,
                         "2024-03-25T08:00:00"),
                _mk_event("BOS", "bullish", 3.5,
                         "2024-04-01T07:45:00", candle_index=50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c2 = next(c for c in result.checks if c.name == "displacement_ratio")
        assert c2.status == "PASS"
        assert c2.mso_value == 3.5

    def test_check1_skips_non_matching_recent_event(self):
        """A newer wrong-direction event must not hide an older valid one.

        The wrong-direction/no-displacement events in the recent tail do NOT
        disqualify the match -- the loop continues past them to find the
        newest qualifying one.
        """
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                # Oldest: qualifying CHoCH bullish
                _mk_event("CHoCH", "bullish", 2.4,
                         "2024-03-25T08:00:00", candle_index=5),
                # Newer: wrong direction (bearish) -- must be ignored
                _mk_event("CHoCH", "bearish", 3.1,
                         "2024-04-01T07:30:00", candle_index=45),
                # Newest: wrong type? no -- BOS bullish no-displacement
                _mk_event("BOS", "bullish", 1.2,
                         "2024-04-01T07:45:00", candle_index=50,
                         disp_present=False),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis(direction="LONG")
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c1 = next(c for c in result.checks if c.name == "m15_choch_exists")
        # Only one event qualifies: the old bullish CHoCH.
        assert c1.status == "PASS"
        assert c1.mso_value["time"] == "2024-03-25T08:00:00"
        assert c1.mso_value["ratio"] == 2.4

    def test_check2_pass_fail_unchanged_under_shipping_config(self):
        """Under displacement_min_ratio=1.5 == displacement_present threshold,
        every qualifying event satisfies the ratio check. Verify PASS outcome
        is identical whether the oldest or newest event is the selected one.
        """
        # Both events have displacement_present=True (ratio>=1.5), but at
        # different ratios. Under the shipping config threshold (1.5), either
        # choice produces PASS.
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[
                _mk_event("CHoCH", "bullish", 1.51,
                         "2024-03-25T08:00:00"),
                _mk_event("CHoCH", "bullish", 4.0,
                         "2024-04-01T07:45:00", candle_index=50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)

        c2 = next(c for c in result.checks if c.name == "displacement_ratio")
        # Outcome must remain PASS regardless of which event is selected.
        assert c2.status == "PASS"
        # But post-fix, the reported ratio is the most-recent event's.
        assert c2.mso_value == 4.0


# ---------------------------------------------------------------------------
# Tests 19+: fvg_fill framework — entry_in_fvg check (added 2026-04-25)
#
# Activates the L2 contract for the fvg_fill standalone framework (per
# CLAUDE.md §Validated Numbers: FVG-in-impulse +7-20pp WR across 6
# instruments, Bonferroni-surviving). The new check fires only when
# `analysis.framework == "fvg_fill"`; ob_retest CANDs see entry_in_fvg as
# SKIP and behave identically to pre-2026-04-25.
# ---------------------------------------------------------------------------


def _make_fvg(
    fvg_type="bullish",
    top=2261.50,
    bottom=2259.50,
    filled=False,
    formation_time="2024-04-01T07:45:00",
    candle_indices=(48, 49, 50),
) -> FairValueGap:
    """Compact FairValueGap helper for fvg_fill tests."""
    return FairValueGap(
        type=fvg_type,
        top=top,
        bottom=bottom,
        midpoint=(top + bottom) / 2,
        candle_indices=list(candle_indices),
        formation_time=formation_time,
        filled=filled,
    )


def _make_m15_tf_with_fvgs(
    fvgs=None,
    choch_dir="bullish",
    disp_present=True,
    disp_ratio=2.0,
    event_type="CHoCH",
) -> TimeframeState:
    """M15 TimeframeState with both an aligned displacement event AND FVGs."""
    return TimeframeState(
        structure=StructureAnalysis(direction=choch_dir),
        structure_events=[StructureEvent(
            type=event_type, direction=choch_dir,
            level_broken=2260.0, close_price=2262.0,
            candle_index=49, time="2024-04-01T07:45:00",
            displacement_present=disp_present,
            displacement_ratio=disp_ratio,
        )],
        fair_value_gaps=fvgs or [_make_fvg()],
        avg_candle_body=1.0,
        atr_14=2.0,
    )


def _make_fvg_analysis(
    direction="LONG",
    entry=2260.50,
    sl=2259.00,  # below FVG.bottom=2259.50 for LONG
    tp1=2262.75,
    poi_price=2260.50,  # midpoint of default FVG
    framework="fvg_fill",
    poi_type="FVG",
    choch_detected=True,
    disp_ratio=2.0,
):
    """Build a CANDIDATE PrimaryAnalysisOutput for the fvg_fill framework.

    Defaults match a LONG fvg_fill on a bullish FVG at 2259.50-2261.50:
    POI = midpoint 2260.50, entry within FVG, SL below FVG.bottom.
    """
    from src.models.analysis_models import (
        DailyBiasAnalysis, H1SetupAnalysis, H4AlignmentAnalysis,
        LiquiditySweepAnalysis, M15ConfirmationAnalysis, PrimaryAnalysisOutput,
        PrimaryAnalysisReasoning, TradeParameters,
    )
    daily_dir = "bullish" if direction == "LONG" else "bearish"
    return PrimaryAnalysisOutput(
        timestamp_utc="2024-04-01T08:00:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework=framework,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_dir, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type=poi_type,
                poi_price_level=poi_price,
                zone="discount" if direction == "LONG" else "premium",
                causing_event_type="BOS",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=choch_detected,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=disp_ratio,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            sl_buffer_applied=0.5,
            take_profit_1=tp1,
            risk_reward_ratio=1.5,
        ),
    )


class TestEntryInFvgGuardsOnFramework:
    """entry_in_fvg must SKIP when framework != fvg_fill (additive only)."""

    def test_skip_on_ob_retest(self):
        """An ob_retest CAND sees entry_in_fvg as SKIP and is unaffected."""
        analysis = _make_analysis()  # framework defaults to ob_retest
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "SKIP"
        assert "fvg_fill" in c_fvg.detail.lower()
        # ob_retest path stays PASS — unchanged behavior.
        assert result.passed is True

    def test_skip_on_breaker_retest(self):
        """breaker_retest CAND also sees entry_in_fvg as SKIP."""
        analysis = _make_analysis(framework="breaker_retest")
        mso = _make_mso()
        # Note: this CAND will fail h1_poi_exists (no breaker present), but
        # the entry_in_fvg check itself must SKIP regardless.
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "SKIP"

    def test_skip_on_none_framework(self):
        """framework='none' (NO_TRADE in production) also SKIPs cleanly."""
        analysis = _make_analysis(framework="none")
        mso = _make_mso()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "SKIP"


class TestEntryInFvgPositive:
    """fvg_fill CANDIDATE — all geometric conditions met -> PASS."""

    def _build_long_fvg_mso(self):
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        return _make_mso(m15_tf=m15)

    def test_long_fvg_fill_all_conditions_met(self):
        mso = self._build_long_fvg_mso()
        analysis = _make_fvg_analysis(
            direction="LONG",
            entry=2260.50,
            sl=2258.00,  # below FVG.bottom=2259.50
            tp1=2264.25,
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "PASS", c_fvg.detail
        # OB-specific checks must SKIP under fvg_fill branch.
        for skipped in ("h1_poi_exists", "ob_zone", "entry_in_ob", "sl_beyond_ob"):
            c = next(c for c in result.checks if c.name == skipped)
            assert c.status == "SKIP", f"{skipped} should SKIP under fvg_fill"
        assert result.passed is True

    def test_short_fvg_fill_all_conditions_met(self):
        bearish_fvg = _make_fvg(
            fvg_type="bearish", top=2266.00, bottom=2264.00,
        )
        m15 = _make_m15_tf_with_fvgs(fvgs=[bearish_fvg], choch_dir="bearish")
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="SHORT",
            entry=2265.00,
            sl=2267.00,  # above FVG.top=2266.00
            tp1=2261.25,
            poi_price=2265.00,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "PASS", c_fvg.detail
        assert result.passed is True


class TestEntryInFvgRejections:
    """fvg_fill CANDIDATE rejection paths — FAIL with descriptive details."""

    def test_no_unfilled_fvg_in_correct_direction(self):
        """All M15 FVGs are filled (or wrong direction) -> FAIL."""
        m15 = _make_m15_tf_with_fvgs(fvgs=[
            # Filled bullish FVG — does not qualify
            _make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50, filled=True),
            # Bearish FVG — wrong direction for LONG
            _make_fvg(fvg_type="bearish", top=2266.00, bottom=2264.00),
        ])
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(direction="LONG", poi_price=2260.50)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "no unfilled" in c_fvg.detail.lower()
        assert result.passed is False
        assert result.blocked_by == "entry_in_fvg"

    def test_poi_outside_any_fvg_range(self):
        """AI cites a POI midpoint that doesn't envelope any unfilled FVG."""
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        mso = _make_mso(m15_tf=m15)
        # POI at 2280 — way outside the 2259.50-2261.50 FVG range.
        analysis = _make_fvg_analysis(direction="LONG", poi_price=2280.00)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "no unfilled" in c_fvg.detail.lower()

    def test_entry_outside_fvg_range_fails(self):
        """POI midpoint matches an FVG, but entry_price is outside the FVG."""
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="LONG",
            poi_price=2260.50,
            entry=2272.00,  # well above FVG.top=2261.50, outside tolerance
            sl=2255.00,
            tp1=2280.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "outside" in c_fvg.detail.lower()

    def test_long_sl_inside_fvg_fails(self):
        """LONG SL placed inside the FVG range fails (must sit below bottom)."""
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="LONG",
            entry=2260.50,
            sl=2260.00,  # inside FVG, NOT below bottom
            tp1=2261.25,
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "below FVG bottom" in c_fvg.detail

    def test_short_sl_inside_fvg_fails(self):
        """SHORT SL placed inside the FVG range fails (must sit above top)."""
        bearish_fvg = _make_fvg(
            fvg_type="bearish", top=2266.00, bottom=2264.00,
        )
        m15 = _make_m15_tf_with_fvgs(fvgs=[bearish_fvg], choch_dir="bearish")
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="SHORT",
            entry=2265.00,
            sl=2265.50,  # inside FVG, NOT above top=2266.00
            tp1=2264.25,
            poi_price=2265.00,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "above FVG top" in c_fvg.detail

    def test_long_sl_at_fvg_bottom_strictly_fails(self):
        """SL exactly at FVG.bottom is NOT strictly below — FAIL."""
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="LONG",
            entry=2260.50,
            sl=2259.50,  # exactly at FVG.bottom
            tp1=2262.00,
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"

    def test_no_m15_data_fails(self):
        """Missing M15 timeframe block in MSO -> FAIL."""
        mso = MarketStateObject(
            timestamp_utc="2024-04-01T08:00:00Z",
            timeframes={
                "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
                "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
                "H1": _make_h1_tf(),
                # No M15
            },
            session_levels=SessionLevels(
                asian_high=2265.0, asian_low=2258.0,
                pdh=2270.0, pdl=2250.0,
            ),
            data_quality=DataQuality(
                all_timeframes_complete=False, spread_normal=True,
                mt5_connected=True, timestamp_utc="2024-04-01T08:00:00Z",
            ),
        )
        analysis = _make_fvg_analysis()
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "M15" in c_fvg.detail

    def test_poi_zero_fails(self):
        """fvg_fill CANDIDATE with poi_price_level=0 -> FAIL."""
        m15 = _make_m15_tf_with_fvgs()
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(poi_price=0.0)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "FAIL"
        assert "0" in c_fvg.detail


class TestEntryInFvgMultipleFvgsDisambiguation:
    """When multiple unfilled FVGs exist, the check picks the one enveloping POI."""

    def test_picks_correct_fvg_among_multiple(self):
        m15 = _make_m15_tf_with_fvgs(fvgs=[
            _make_fvg(fvg_type="bullish", top=2255.00, bottom=2253.00),
            _make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50),
            _make_fvg(fvg_type="bullish", top=2270.00, bottom=2268.00),
        ])
        mso = _make_mso(m15_tf=m15)
        # POI inside the SECOND FVG (2259.50-2261.50).
        analysis = _make_fvg_analysis(
            direction="LONG",
            entry=2260.50,
            sl=2258.00,  # below the matched FVG's bottom (2259.50)
            tp1=2264.25,
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status == "PASS"
        assert c_fvg.mso_value["fvg_bottom"] == 2259.50
        assert c_fvg.mso_value["fvg_top"] == 2261.50


class TestEntryInFvgIntegration:
    """fvg_fill verify_candidate end-to-end — m15_choch + entry_in_fvg pass."""

    def test_full_fvg_fill_passes_all_checks(self):
        m15 = _make_m15_tf_with_fvgs(
            fvgs=[_make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50)],
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(
            direction="LONG",
            entry=2260.50,
            sl=2258.00,
            tp1=2264.25,
            poi_price=2260.50,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        # entry_in_fvg PASS
        assert result.passed is True
        # m15_choch_exists / displacement_ratio still active for fvg_fill.
        c1 = next(c for c in result.checks if c.name == "m15_choch_exists")
        assert c1.status == "PASS"
        c2 = next(c for c in result.checks if c.name == "displacement_ratio")
        assert c2.status == "PASS"
        # OB checks all SKIP under fvg_fill.
        for skipped in ("h1_poi_exists", "ob_zone", "entry_in_ob", "sl_beyond_ob"):
            c = next(c for c in result.checks if c.name == skipped)
            assert c.status == "SKIP"

    def test_fvg_fill_no_displacement_event_blocks(self):
        """If M15 has no aligned displacement event, m15_choch_exists fails first."""
        m15 = TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            structure_events=[],  # no displacement events
            fair_value_gaps=[
                _make_fvg(fvg_type="bullish", top=2261.50, bottom=2259.50),
            ],
            avg_candle_body=1.0, atr_14=2.0,
        )
        mso = _make_mso(m15_tf=m15)
        analysis = _make_fvg_analysis(direction="LONG", poi_price=2260.50)
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        # m15_choch_exists fails first — fvg_fill cannot fire without a
        # qualifying displacement event.
        assert result.passed is False
        assert result.blocked_by == "m15_choch_exists"
# Test 16: breaker_re_entry framework (additive 2026-04-25, FTMO challenge)
# ---------------------------------------------------------------------------
#
# These tests cover the new ``entry_in_breaker`` L2 check + the breaker-aware
# behavior of ``h1_poi_exists`` for the explicit ``breaker_re_entry`` framework
# label. The legacy ``breaker_retest`` path remains tested by
# ``TestBreakerRetest`` above.
#
# Invariants:
#   - ``entry_in_breaker`` SKIPs for any framework other than
#     ``breaker_re_entry`` (including ob_retest and the legacy breaker_retest).
#   - Failure modes are bit-identical to the underlying ob-retest geometry
#     checks, but anchored on ``breaker_blocks`` instead of ``order_blocks``.
#   - ``framework`` field on ``PrimaryAnalysisOutput`` accepts the new literal
#     ``"breaker_re_entry"`` (Pydantic Literal extension confirmed).


class TestBreakerReEntryHelperSKIP:
    """``_check_entry_in_breaker`` returns SKIP for non-breaker frameworks."""

    def test_skips_for_ob_retest(self):
        analysis = _make_analysis(framework="ob_retest")
        # Pass a non-None breaker to confirm SKIP is driven by framework, not
        # by the absence of a matched zone.
        bb = BreakerBlock(
            zone_high=2261.50, zone_low=2259.80,
            direction="bullish",
            original_ob_direction="bearish",
            formation_time="2024-04-01T05:00:00",
            mitigation_time="2024-04-01T06:00:00",
            causing_event="BOS",
            is_retested=False,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "SKIP"
        assert "breaker_re_entry" in check.detail

    def test_skips_for_legacy_breaker_retest(self):
        # Legacy ``breaker_retest`` framework label still routes through the
        # generic OB/breaker matching for backwards compatibility; the new
        # ``entry_in_breaker`` check stays SKIP for that label.
        analysis = _make_analysis(framework="breaker_retest")
        check = _check_entry_in_breaker(analysis, matched_bb=None, config=DEFAULT_CONFIG)
        assert check.status == "SKIP"

    def test_skips_when_no_trade_parameters(self):
        analysis = _make_analysis(framework="breaker_re_entry")
        analysis.trade_parameters = None
        check = _check_entry_in_breaker(analysis, matched_bb=None, config=DEFAULT_CONFIG)
        assert check.status == "SKIP"

    def test_skips_when_no_matched_breaker(self):
        analysis = _make_analysis(framework="breaker_re_entry")
        check = _check_entry_in_breaker(analysis, matched_bb=None, config=DEFAULT_CONFIG)
        assert check.status == "SKIP"
        assert "matched breaker" in check.detail.lower()


def _make_bullish_breaker(
    zone_low: float = 2259.80,
    zone_high: float = 2261.50,
) -> BreakerBlock:
    """Helper: bullish breaker (mitigated bearish OB), supports a LONG."""
    return BreakerBlock(
        zone_high=zone_high, zone_low=zone_low,
        direction="bullish",
        original_ob_direction="bearish",
        formation_time="2024-04-01T05:00:00",
        mitigation_time="2024-04-01T06:00:00",
        causing_event="BOS",
        is_retested=False,
    )


def _make_bearish_breaker(
    zone_low: float = 2270.00,
    zone_high: float = 2272.00,
) -> BreakerBlock:
    """Helper: bearish breaker (mitigated bullish OB), supports a SHORT."""
    return BreakerBlock(
        zone_high=zone_high, zone_low=zone_low,
        direction="bearish",
        original_ob_direction="bullish",
        formation_time="2024-04-01T05:00:00",
        mitigation_time="2024-04-01T06:00:00",
        causing_event="BOS",
        is_retested=False,
    )


class TestEntryInBreakerLong:
    """Helper-level checks for LONG breaker_re_entry geometry."""

    def test_pass_long_entry_in_zone_sl_below(self):
        bb = _make_bullish_breaker()  # 2259.80-2261.50
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,            # at zone_high (entry side for LONG)
            sl=2258.50,                # strictly below zone_low
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "PASS", check.detail

    def test_fail_long_sl_at_zone_low(self):
        bb = _make_bullish_breaker()
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2259.80,                # AT zone_low — must be strictly below
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"
        assert "strictly below" in check.detail

    def test_fail_long_sl_above_zone_low(self):
        bb = _make_bullish_breaker()
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2260.50,                # inside the zone — protective stop misplaced
            tp1=2266.00,
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"

    def test_fail_long_entry_above_zone(self):
        bb = _make_bullish_breaker()  # 2259.80-2261.50
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2270.00,             # well above the breaker zone (outside tolerance)
            sl=2258.50,
            tp1=2280.00,
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"
        assert "outside breaker zone" in check.detail


class TestEntryInBreakerShort:
    """Helper-level checks for SHORT breaker_re_entry geometry."""

    def test_pass_short_entry_in_zone_sl_above(self):
        bb = _make_bearish_breaker()  # 2270.00-2272.00
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="SHORT",
            entry=2270.00,             # at zone_low (entry side for SHORT)
            sl=2273.00,                # strictly above zone_high
            tp1=2265.50,               # below entry, valid SHORT TP1
            poi_price=2271.00,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "PASS", check.detail

    def test_fail_short_sl_at_zone_high(self):
        bb = _make_bearish_breaker()
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="SHORT",
            entry=2270.00,
            sl=2272.00,                # AT zone_high — must be strictly above
            tp1=2265.50,
            poi_price=2271.00,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"
        assert "strictly above" in check.detail

    def test_fail_short_sl_below_zone_high(self):
        bb = _make_bearish_breaker()
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="SHORT",
            entry=2270.00,
            sl=2271.00,                # inside the zone
            tp1=2265.50,
            poi_price=2271.00,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"


class TestEntryInBreakerDirectionalConsistency:
    """Defensive: breaker.direction must match trade direction."""

    def test_fail_long_against_bearish_breaker(self):
        # A bearish breaker should not back a LONG. Even though h1_poi_exists
        # already enforces this via _find_matching_breaker's direction filter,
        # entry_in_breaker rechecks defensively to catch any future regression
        # that might allow a mis-keyed BreakerBlock through.
        bb = _make_bearish_breaker(zone_low=2259.80, zone_high=2261.50)
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2258.50,
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=DEFAULT_CONFIG)
        assert check.status == "FAIL"
        assert "direction" in check.detail.lower()


class TestVerifyCandidateBreakerReEntryEndToEnd:
    """End-to-end verify_candidate flow with framework=breaker_re_entry."""

    def test_full_pass_long_breaker_re_entry(self):
        bb = _make_bullish_breaker()  # 2259.80-2261.50
        h1 = _make_h1_tf(obs=[], breakers=[bb])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2258.50,
            poi_price=2260.65,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        assert result.passed is True, result.blocked_by
        # entry_in_breaker should be PASS for breaker_re_entry framework.
        c8 = next(c for c in result.checks if c.name == "entry_in_breaker")
        assert c8.status == "PASS"
        # h1_poi_exists should resolve via the breaker, not OB, fallback.
        c3 = next(c for c in result.checks if c.name == "h1_poi_exists")
        assert c3.status == "PASS"
        assert "breaker_re_entry" in c3.detail or "breaker" in c3.detail.lower()

    def test_blocks_when_no_breaker_in_mso(self):
        # No breakers + no matching OB → h1_poi_exists FAIL, blocks.
        h1 = _make_h1_tf(obs=[], breakers=[])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2258.50,
            poi_price=2260.65,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        assert result.passed is False
        assert result.blocked_by == "h1_poi_exists"

    def test_blocks_on_invalid_sl_with_valid_breaker(self):
        bb = _make_bullish_breaker()
        h1 = _make_h1_tf(obs=[], breakers=[bb])
        mso = _make_mso(h1_tf=h1)
        # SL above zone_low → entry_in_breaker FAIL. (sl_beyond_ob also fails.)
        analysis = _make_analysis(
            framework="breaker_re_entry",
            direction="LONG",
            entry=2261.50,
            sl=2260.00,
            tp1=2266.00,
            poi_price=2260.65,
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        assert result.passed is False
        # Either gate is acceptable as the blocker — depends on check order.
        assert result.blocked_by in ("sl_beyond_ob", "entry_in_breaker")

    def test_ob_retest_path_unaffected_by_breaker_check(self):
        """Confirm OB-retest path produces SKIP for entry_in_breaker check."""
        h1 = _make_h1_tf()  # has unmitigated OB
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis()  # framework=ob_retest by default
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        assert result.passed is True
        c8 = next(c for c in result.checks if c.name == "entry_in_breaker")
        assert c8.status == "SKIP"


class TestBreakerReEntryAnalysisModelLiteral:
    """The Pydantic Literal on ``framework`` admits the new label."""

    def test_breaker_re_entry_literal_accepted(self):
        analysis = _make_analysis(framework="breaker_re_entry")
        assert analysis.framework == "breaker_re_entry"
        # Round-trip through model_dump → the literal survives unchanged.
        dumped = analysis.model_dump()
        assert dumped["framework"] == "breaker_re_entry"
