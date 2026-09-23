"""HALLUC-1 multi-framework dispatch routing tests (GBPJPY 2026-04-28 fix).

Defense-in-depth fix: when the wrapper-level ``analysis.framework`` field
disagrees with the AI's ``frameworks_evaluated.<X>.qualified`` flags, the
L2 ``_check_h1_poi_exists`` routing must follow the qualification flags
(the AI's actual finding) rather than the biased wrapper field.

See ``research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md`` and the
GBPJPY 2026-04-28 01:30 trade record (smoking gun: wrapper said
``ob_retest`` while ``frameworks_evaluated.fvg_fill.qualified=True``).
"""

from __future__ import annotations

import pytest

from src.components.verification import (
    VerificationCheck,
    VerificationResult,
    _check_h1_poi_exists,
    _compute_effective_framework,
    verify_candidate,
)
from src.models.analysis_models import (
    DailyBiasAnalysis,
    FrameworkEvaluation,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)
from src.models.market_state_models import (
    DataQuality,
    FairValueGap,
    MarketStateObject,
    OrderBlock,
    PremiumDiscount,
    PriceZone,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)


DEFAULT_CONFIG = {
    "model_a": {"displacement_min_ratio": 1.5},
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "strict_zone_check": False,
        "log_warnings": False,
    },
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _make_m15_tf(
    fvgs: list[FairValueGap] | None = None,
    structure_dir: str = "bullish",
) -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction=structure_dir),
        structure_events=[StructureEvent(
            type="BOS", direction=structure_dir,
            level_broken=215.500, close_price=215.520,
            candle_index=10, time="2026-04-27T15:00",
            displacement_present=True, displacement_ratio=2.5,
        )],
        fair_value_gaps=fvgs or [],
        avg_candle_body=0.05,
        atr_14=0.10,
    )


def _make_h1_tf(
    obs: list[OrderBlock] | None = None,
    pd_eq: float = 215.500,
) -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction="bullish"),
        structure_events=[StructureEvent(
            type="BOS", direction="bullish",
            level_broken=215.300, close_price=215.350,
            candle_index=20, time="2026-04-27T08:00",
            displacement_present=True, displacement_ratio=2.0,
        )],
        order_blocks=obs or [],
        breaker_blocks=[],
        premium_discount=PremiumDiscount(
            impulse_low=215.300, impulse_high=215.700,
            equilibrium_50=pd_eq,
            fib_62=215.500, fib_79=215.380,
            discount_zone=PriceZone(top=pd_eq, bottom=215.300),
            premium_zone=PriceZone(top=215.700, bottom=pd_eq),
            ote_zone=PriceZone(top=215.500, bottom=215.380),
        ),
        avg_candle_body=0.05,
        atr_14=0.15,
    )


def _make_mso(
    h1_tf: TimeframeState | None = None,
    m15_tf: TimeframeState | None = None,
) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2026-04-28T01:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H1": h1_tf or _make_h1_tf(),
            "M15": m15_tf or _make_m15_tf(),
        },
        session_levels=SessionLevels(
            asian_high=215.827, asian_low=215.662,
            pdh=216.050, pdl=215.421,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2026-04-28T01:30:00Z",
        ),
    )


def _make_analysis(
    framework: str = "ob_retest",
    poi_type: str = "OB",
    poi_price: float = 215.475,
    direction: str = "LONG",
    entry: float = 215.475,
    sl: float = 215.350,
    tp1: float = 215.661,
    frameworks_evaluated: dict | None = None,
) -> PrimaryAnalysisOutput:
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-28T01:30:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework=framework,
        frameworks_evaluated=frameworks_evaluated,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type=poi_type,
                poi_price_level=poi_price,
                zone="discount",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.5,
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
# _compute_effective_framework — unit tests for the helper
# ---------------------------------------------------------------------------

class TestComputeEffectiveFramework:

    def test_returns_wrapper_when_no_frameworks_evaluated(self):
        """When ``frameworks_evaluated`` is None or missing, the helper
        must return the wrapper unchanged so legacy analyses are
        bit-identical to pre-fix behavior."""
        analysis = _make_analysis(framework="ob_retest", frameworks_evaluated=None)
        eff, overridden, decision = _compute_effective_framework(analysis)
        assert eff == "ob_retest"
        assert overridden is False
        assert decision["reason"] == "no_qualified_flags"

    def test_returns_wrapper_when_wrapper_qualified(self):
        """Happy path: wrapper agrees with at least one qualified
        framework. Effective framework = wrapper, no override."""
        analysis = _make_analysis(
            framework="ob_retest",
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=True, reason="OB exists"),
                "fvg_fill": FrameworkEvaluation(qualified=False, reason="no FVG"),
            },
        )
        eff, overridden, decision = _compute_effective_framework(analysis)
        assert eff == "ob_retest"
        assert overridden is False
        assert decision["reason"] == "wrapper_qualified"

    def test_overrides_when_wrapper_disagrees_single_qualified(self):
        """Smoking-gun case: wrapper says ob_retest but
        frameworks_evaluated.ob_retest.qualified=False and
        frameworks_evaluated.fvg_fill.qualified=True. Override to
        fvg_fill."""
        analysis = _make_analysis(
            framework="ob_retest",
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=False, reason="no OB"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        eff, overridden, decision = _compute_effective_framework(analysis)
        assert eff == "fvg_fill"
        assert overridden is True
        assert decision["reason"] == "wrapper_disagrees_single_qualified"
        assert decision["wrapper_framework"] == "ob_retest"
        assert decision["effective_framework"] == "fvg_fill"

    def test_multi_qualified_prefers_poi_type_match(self):
        """When multiple frameworks qualify but wrapper isn't one of them,
        prefer the framework matching h1_setup.poi_type."""
        analysis = _make_analysis(
            framework="breaker_re_entry",  # wrapper that's NOT in qualified set
            poi_type="FVG",
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=True, reason="OB present"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        eff, overridden, decision = _compute_effective_framework(analysis)
        assert eff == "fvg_fill"  # poi_type=FVG -> fvg_fill wins
        assert overridden is True
        assert decision["reason"] == "multi_qualified_poi_type_match"


# ---------------------------------------------------------------------------
# _check_h1_poi_exists — routing-on-qualifications behavior
# ---------------------------------------------------------------------------

class TestCheckH1PoiRouting:

    def test_h1_poi_exists_routes_on_qualified_when_wrapper_disagrees(self):
        """Wrapper says ob_retest, qualified.fvg_fill=True, poi_type=FVG.
        The check must route to fvg_fill (M15 FVG lookup), NOT ob_retest
        (H1 OB lookup)."""
        # H1 has NO OBs (the GBPJPY trending-bull case).
        h1 = _make_h1_tf(obs=[])
        # M15 has a matching FVG at the AI's poi_price.
        fvg = FairValueGap(
            type="bullish", top=215.499, bottom=215.450,
            midpoint=215.475,
            candle_indices=[8, 9, 10],
            formation_time="2026-04-27T15:00",
            filled=False,
        )
        m15 = _make_m15_tf(fvgs=[fvg])
        mso = _make_mso(h1_tf=h1, m15_tf=m15)
        analysis = _make_analysis(
            framework="ob_retest",      # wrapper biased
            poi_type="FVG",              # AI's actual setup
            poi_price=215.475,           # midpoint of FVG
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=False, reason="no OB"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        check, matched_ob, matched_bb = _check_h1_poi_exists(
            analysis, mso, DEFAULT_CONFIG,
        )
        # Routed to fvg_fill: matched_ob and matched_bb are both None (the
        # FVG branch does not produce an OB/breaker handle).
        assert matched_ob is None
        assert matched_bb is None
        # The check status is WARN (validation passed but wrapper-vs-
        # qualifications inconsistency was surfaced).
        assert check.status == "WARN", f"expected WARN, got {check.status}: {check.detail}"
        # The detail mentions the M15 FVG (not an H1 OB).
        assert "M15 FVG" in check.detail
        # The routing decision is logged in details.
        assert isinstance(check.mso_value, dict)
        assert "routing_decision" in check.mso_value
        rd = check.mso_value["routing_decision"]
        assert rd["was_overridden"] is True
        assert rd["wrapper_framework"] == "ob_retest"
        assert rd["effective_framework"] == "fvg_fill"

    def test_h1_poi_exists_prefers_poi_type_when_multiple_qualified(self):
        """Wrapper not qualified, multiple qualified — poi_type=FVG must
        route to fvg_fill."""
        h1 = _make_h1_tf(obs=[])
        fvg = FairValueGap(
            type="bullish", top=215.499, bottom=215.450,
            midpoint=215.475,
            candle_indices=[8, 9, 10],
            formation_time="2026-04-27T15:00",
            filled=False,
        )
        m15 = _make_m15_tf(fvgs=[fvg])
        mso = _make_mso(h1_tf=h1, m15_tf=m15)
        analysis = _make_analysis(
            # wrapper is breaker_re_entry but neither OB list nor breaker list has it
            framework="breaker_re_entry",
            poi_type="FVG",
            poi_price=215.475,
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=True, reason="OB present"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        check, matched_ob, matched_bb = _check_h1_poi_exists(
            analysis, mso, DEFAULT_CONFIG,
        )
        # Routed to fvg_fill (FVG poi_type wins).
        assert check.status == "WARN"
        assert "M15 FVG" in check.detail
        rd = check.mso_value["routing_decision"]
        assert rd["effective_framework"] == "fvg_fill"

    def test_h1_poi_exists_unchanged_when_wrapper_matches_qualification(self):
        """Happy path: wrapper=ob_retest, qualified.ob_retest=True. The
        check must route to ob_retest (the legacy behavior is preserved
        bit-identically in this branch)."""
        # Build an H1 with a single unmitigated bullish OB at the AI's
        # poi_price.
        ob = OrderBlock(
            type="bullish", high=215.500, low=215.450,
            open=215.470, close=215.480,
            formation_index=20, formation_time="2026-04-27T08:00",
            causing_bos_index=22, mitigated=False,
            causing_event_type="BOS",
        )
        h1 = _make_h1_tf(obs=[ob])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            framework="ob_retest",
            poi_type="OB",
            poi_price=215.475,
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=True, reason="OB exists"),
                "fvg_fill": FrameworkEvaluation(qualified=False, reason="no FVG"),
            },
        )
        check, matched_ob, matched_bb = _check_h1_poi_exists(
            analysis, mso, DEFAULT_CONFIG,
        )
        # Status PASS (no override, no inconsistency).
        assert check.status == "PASS", f"expected PASS, got {check.status}: {check.detail}"
        # OB matched (ob_retest path).
        assert matched_ob is not None
        assert matched_ob.high == 215.500
        # Routing decision documents the no-override case.
        rd = check.mso_value["routing_decision"]
        assert rd["was_overridden"] is False
        assert rd["effective_framework"] == "ob_retest"

    def test_h1_poi_exists_logs_routing_decision_into_check_details(self):
        """Routing decision must always be logged in mso_value details
        (even on no-override paths) so the audit trail is complete."""
        # Trivial case: no frameworks_evaluated.
        ob = OrderBlock(
            type="bullish", high=215.500, low=215.450,
            open=215.470, close=215.480,
            formation_index=20, formation_time="2026-04-27T08:00",
            causing_bos_index=22, mitigated=False,
            causing_event_type="BOS",
        )
        h1 = _make_h1_tf(obs=[ob])
        mso = _make_mso(h1_tf=h1)
        analysis = _make_analysis(
            framework="ob_retest",
            poi_type="OB",
            poi_price=215.475,
            frameworks_evaluated=None,
        )
        check, matched_ob, _ = _check_h1_poi_exists(
            analysis, mso, DEFAULT_CONFIG,
        )
        assert check.status == "PASS"
        assert isinstance(check.mso_value, dict)
        assert "routing_decision" in check.mso_value
        rd = check.mso_value["routing_decision"]
        # When no qualifications surfaced, the decision documents the
        # fallback.
        assert rd["reason"] == "no_qualified_flags"
        assert rd["was_overridden"] is False

    def test_h1_poi_exists_warns_on_wrapper_qualification_mismatch(self):
        """When wrapper-qualifications disagree but validation passes,
        the check must be WARN (not FAIL) — the inconsistency is
        surfaced but not punished."""
        # Same as routes_on_qualified — already tested. Here we focus
        # on the WARN-vs-FAIL semantics specifically: the result is NOT
        # blocked when the override succeeds.
        h1 = _make_h1_tf(obs=[])
        fvg = FairValueGap(
            type="bullish", top=215.499, bottom=215.450,
            midpoint=215.475,
            candle_indices=[8, 9, 10],
            formation_time="2026-04-27T15:00",
            filled=False,
        )
        m15 = _make_m15_tf(fvgs=[fvg])
        mso = _make_mso(h1_tf=h1, m15_tf=m15)
        analysis = _make_analysis(
            framework="ob_retest",
            poi_type="FVG",
            poi_price=215.475,
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=False, reason="no OB"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        check, _, _ = _check_h1_poi_exists(analysis, mso, DEFAULT_CONFIG)
        assert check.status == "WARN"
        # The result should NOT be FAIL — WARN does not block downstream.
        assert check.status != "FAIL"


# ---------------------------------------------------------------------------
# verify_candidate end-to-end — override case must complete the FVG
# validation path (not be silently skipped).
# ---------------------------------------------------------------------------

class TestVerifyCandidateEndToEnd:

    def test_verify_candidate_routes_override_to_fvg_path(self):
        """End-to-end: wrapper=ob_retest, qualified=fvg_fill must run
        the fvg_fill verification branch (entry_in_fvg actually runs,
        not SKIPped)."""
        h1 = _make_h1_tf(obs=[])
        fvg = FairValueGap(
            type="bullish", top=215.499, bottom=215.450,
            midpoint=215.475,
            candle_indices=[8, 9, 10],
            formation_time="2026-04-27T15:00",
            filled=False,
        )
        m15 = _make_m15_tf(fvgs=[fvg])
        mso = _make_mso(h1_tf=h1, m15_tf=m15)
        analysis = _make_analysis(
            framework="ob_retest",
            poi_type="FVG",
            poi_price=215.475,
            entry=215.475,
            sl=215.420,    # below FVG.bottom (215.450) — passes SL check
            tp1=215.557,
            frameworks_evaluated={
                "ob_retest": FrameworkEvaluation(qualified=False, reason="no OB"),
                "fvg_fill": FrameworkEvaluation(qualified=True, reason="FVG present"),
            },
        )
        result = verify_candidate(analysis, mso, DEFAULT_CONFIG)
        # entry_in_fvg should NOT be SKIP — it should actually run.
        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status != "SKIP", (
            f"entry_in_fvg must run when effective framework is fvg_fill "
            f"(via wrapper-qualifications override); got SKIP: {c_fvg.detail}"
        )
        # The OB-specific checks should be SKIP (fvg_fill branch).
        for skip_name in ("h1_poi_exists", "ob_zone", "entry_in_ob", "sl_beyond_ob"):
            c = next(c for c in result.checks if c.name == skip_name)
            assert c.status == "SKIP", (
                f"{skip_name} should be SKIP on fvg_fill effective branch; "
                f"got {c.status}"
            )
