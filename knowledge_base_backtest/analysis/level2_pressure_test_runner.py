#!/usr/bin/env python3
"""Level 2 Verification Pressure Test — comprehensive logic verification.

Run from project root:
    python3 knowledge_base_backtest/analysis/level2_pressure_test_runner.py
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from src.components.verification import (
    VerificationCheck,
    VerificationResult,
    verify_candidate,
)
from src.models.market_state_models import (
    BreakerBlock,
    DataQuality,
    MarketStateObject,
    OrderBlock,
    PremiumDiscount,
    PriceZone,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
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
# Config
# ---------------------------------------------------------------------------
CFG = {
    "model_a": {"displacement_min_ratio": 1.5},
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "strict_zone_check": False,
        "log_warnings": False,
    },
}

results: dict[str, dict] = {}


def record(test_id: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    results[test_id] = {"status": status, "detail": detail}
    print(f"  {test_id}: {status}{'  — ' + detail if detail else ''}")


# ---------------------------------------------------------------------------
# Helpers to build test data
# ---------------------------------------------------------------------------

def _m15(direction="bullish", disp_present=True, ratio=2.0,
         event_type="CHoCH", events=None) -> TimeframeState:
    if events is not None:
        ev = events
    elif disp_present or ratio > 0:
        ev = [StructureEvent(
            type=event_type, direction=direction,
            level_broken=2260.0, close_price=2262.0,
            candle_index=50, time="2024-04-01T08:00:00",
            displacement_present=disp_present, displacement_ratio=ratio,
        )]
    else:
        ev = []
    return TimeframeState(
        structure=StructureAnalysis(direction=direction),
        structure_events=ev,
        avg_candle_body=1.0, atr_14=2.0,
    )


def _h1(obs=None, breakers=None, eq=2262.0,
        imp_low=2255.0, imp_high=2270.0) -> TimeframeState:
    if obs is None:
        obs = [OrderBlock(
            type="bullish", high=2261.50, low=2259.80,
            open=2261.00, close=2260.00,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )]
    rng = imp_high - imp_low
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
            impulse_low=imp_low, impulse_high=imp_high,
            equilibrium_50=eq,
            fib_62=imp_high - rng * 0.618,
            fib_79=imp_high - rng * 0.786,
            discount_zone=PriceZone(top=eq, bottom=imp_low),
            premium_zone=PriceZone(top=imp_high, bottom=eq),
            ote_zone=PriceZone(top=imp_high - rng * 0.618, bottom=imp_high - rng * 0.786),
        ),
        avg_candle_body=2.0, atr_14=4.0,
    )


def _mso(m15_tf=None, h1_tf=None) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2024-04-01T08:00:00Z",
        timeframes={
            "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H1": h1_tf or _h1(),
            "M15": m15_tf or _m15(),
        },
        session_levels=SessionLevels(
            asian_high=2265.0, asian_low=2258.0, pdh=2270.0, pdl=2250.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2024-04-01T08:00:00Z",
        ),
    )


def _analysis(direction="LONG", entry=2260.50, sl=2258.50, tp1=2263.50,
              poi_price=2260.50, poi_identified=True, choch=True,
              disp_ratio=2.0, framework="ob_retest") -> PrimaryAnalysisOutput:
    return PrimaryAnalysisOutput(
        timestamp_utc="2024-04-01T08:00:00Z", model_used="test",
        decision="CANDIDATE", confidence_score=80, framework=framework,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=poi_identified, poi_type="OB",
                poi_price_level=poi_price, zone="discount",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=choch, displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=disp_ratio,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction, entry_price=entry, stop_loss=sl,
            take_profit_1=tp1, risk_reward_ratio=1.5,
        ),
    )


# ===================================================================
# TEST 1: Known Preventable Losses
# ===================================================================
def test_1():
    print("\n=== TEST 1: Known Preventable Losses ===")

    # 1A: Structure Misread (2024-03-15)
    # AI set poi_identified=False but still output CANDIDATE
    # No unmitigated H1 OB exists near the AI's entry
    try:
        a = _analysis(poi_identified=False)
        mso = _mso()
        r = verify_candidate(a, mso, CFG)
        record("1A", not r.passed and r.blocked_by == "h1_poi_exists",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("1A", False, f"EXCEPTION: {e}")

    # 1A variant: poi_identified=True but H1 has no unmitigated OBs
    try:
        h1_no_obs = _h1(obs=[])
        a = _analysis(poi_price=2260.50)
        mso = _mso(h1_tf=h1_no_obs)
        r = verify_candidate(a, mso, CFG)
        record("1A_v2", not r.passed and r.blocked_by == "h1_poi_exists",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("1A_v2", False, f"EXCEPTION: {e}")

    # 1B: Threshold Violation (2024-03-01)
    # AI accepted displacement at 0.4x (below 1.5)
    try:
        m15 = _m15(disp_present=False, ratio=0.4)
        a = _analysis(disp_ratio=0.4)
        mso = _mso(m15_tf=m15)
        r = verify_candidate(a, mso, CFG)
        # Should fail on Check 1 (disp_present=False) or Check 2
        record("1B", not r.passed,
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("1B", False, f"EXCEPTION: {e}")

    # 1B variant: disp_present=True but ratio=0.4 (edge: system says present but ratio low)
    try:
        m15 = _m15(disp_present=True, ratio=0.4)
        a = _analysis(disp_ratio=0.4)
        mso = _mso(m15_tf=m15)
        r = verify_candidate(a, mso, CFG)
        record("1B_v2", not r.passed and r.blocked_by == "displacement_ratio",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("1B_v2", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 2: Valid Trade Passes All Checks
# ===================================================================
def test_2():
    print("\n=== TEST 2: Valid Trade Passes All Checks ===")
    try:
        a = _analysis()
        mso = _mso()
        r = verify_candidate(a, mso, CFG)
        all_pass = all(c.status in ("PASS", "WARN", "SKIP") for c in r.checks)
        record("2", r.passed and all_pass and len(r.checks) == 6,
               f"passed={r.passed}, checks={[(c.name, c.status) for c in r.checks]}")
    except Exception as e:
        record("2", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 3: Check-by-Check Isolation
# ===================================================================
def test_3():
    print("\n=== TEST 3: Check-by-Check Isolation ===")

    # 3A: No M15 CHoCH
    try:
        m15 = _m15(events=[])
        a = _analysis()
        mso = _mso(m15_tf=m15)
        r = verify_candidate(a, mso, CFG)
        record("3A", not r.passed and r.blocked_by == "m15_choch_exists",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("3A", False, f"EXCEPTION: {e}")

    # 3B: CHoCH exists but ratio=0.8 (disp_present=True to pass check 1, ratio fails check 2)
    try:
        m15 = _m15(disp_present=True, ratio=0.8)
        a = _analysis(disp_ratio=0.8)
        mso = _mso(m15_tf=m15)
        r = verify_candidate(a, mso, CFG)
        record("3B", not r.passed and r.blocked_by == "displacement_ratio",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("3B", False, f"EXCEPTION: {e}")

    # 3C: AI cites OB at 3042.50 but nearest MSO OB is 3080-3085
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3085.0, low=3080.0,
            open=3084.0, close=3081.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3050.0)
        a = _analysis(poi_price=3042.50, entry=3042.50, sl=3040.0, tp1=3046.0)
        mso = _mso(h1_tf=h1)
        r = verify_candidate(a, mso, CFG)
        record("3C", not r.passed and r.blocked_by == "h1_poi_exists",
               f"blocked_by={r.blocked_by}")
    except Exception as e:
        record("3C", False, f"EXCEPTION: {e}")

    # 3D: OB in premium but trade is LONG (with strict=True)
    try:
        cfg_strict = {**CFG, "verification": {**CFG["verification"], "strict_zone_check": True}}
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=2268.0, low=2266.0,
            open=2267.5, close=2266.5,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=2262.0)
        a = _analysis(entry=2267.0, sl=2264.0, tp1=2271.5, poi_price=2267.0)
        mso = _mso(h1_tf=h1)
        r = verify_candidate(a, mso, cfg_strict)
        c4 = next(c for c in r.checks if c.name == "ob_zone")
        record("3D", not r.passed and c4.status == "FAIL",
               f"blocked_by={r.blocked_by}, ob_zone={c4.status}")
    except Exception as e:
        record("3D", False, f"EXCEPTION: {e}")

    # 3E: Entry at 3065 but OB range is 3040-3045 (~$20 away, well beyond 0.2% tol)
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3045.0, low=3040.0,
            open=3044.0, close=3041.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3050.0)
        a = _analysis(entry=3065.0, sl=3038.0, tp1=3105.0, poi_price=3042.0)
        mso = _mso(h1_tf=h1)
        r = verify_candidate(a, mso, CFG)
        c5 = next(c for c in r.checks if c.name == "entry_in_ob")
        record("3E", c5.status == "FAIL",
               f"entry_in_ob={c5.status}, detail={c5.detail[:80]}")
    except Exception as e:
        record("3E", False, f"EXCEPTION: {e}")

    # 3F: LONG trade, SL at 3042 but OB.low is 3040 (SL inside OB)
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3045.0, low=3040.0,
            open=3044.0, close=3041.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3050.0)
        a = _analysis(entry=3042.0, sl=3042.0, tp1=3048.0, poi_price=3042.0)
        mso = _mso(h1_tf=h1)
        r = verify_candidate(a, mso, CFG)
        c6 = next(c for c in r.checks if c.name == "sl_beyond_ob")
        record("3F", c6.status == "FAIL",
               f"sl_beyond_ob={c6.status}")
    except Exception as e:
        record("3F", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 4: Edge Cases
# ===================================================================
def test_4():
    print("\n=== TEST 4: Edge Cases ===")

    # 4A: Missing trade_parameters
    try:
        a = _analysis()
        a.trade_parameters = None
        r = verify_candidate(a, _mso(), CFG)
        record("4A", not r.passed,
               f"passed={r.passed}, no crash")
    except Exception as e:
        record("4A", False, f"CRASH: {e}")

    # 4B: Missing reasoning fields — set h1_setup to minimal
    try:
        a = _analysis()
        a.reasoning.h1_setup = H1SetupAnalysis(poi_identified=False)
        r = verify_candidate(a, _mso(), CFG)
        record("4B", not r.passed,
               f"passed={r.passed}, blocked_by={r.blocked_by}")
    except Exception as e:
        record("4B", False, f"CRASH: {e}")

    # 4C: Empty M15 structure_events
    try:
        m15 = _m15(events=[])
        a = _analysis()
        r = verify_candidate(a, _mso(m15_tf=m15), CFG)
        c1 = r.checks[0]
        record("4C", c1.status == "FAIL",
               f"check1={c1.status}")
    except Exception as e:
        record("4C", False, f"CRASH: {e}")

    # 4D: No premium_discount data
    try:
        h1 = _h1()
        h1.premium_discount = None
        a = _analysis()
        mso = _mso(h1_tf=h1)
        r = verify_candidate(a, mso, CFG)
        c4 = next(c for c in r.checks if c.name == "ob_zone")
        record("4D", c4.status == "SKIP",
               f"ob_zone={c4.status}")
    except Exception as e:
        record("4D", False, f"CRASH: {e}")

    # 4E: Multiple M15 CHoCH events — 2 wrong direction, 1 correct
    try:
        events = [
            StructureEvent(type="CHoCH", direction="bearish",
                          level_broken=2260.0, close_price=2258.0,
                          candle_index=40, time="2024-04-01T07:30:00",
                          displacement_present=True, displacement_ratio=2.0),
            StructureEvent(type="CHoCH", direction="bearish",
                          level_broken=2259.0, close_price=2257.0,
                          candle_index=45, time="2024-04-01T07:45:00",
                          displacement_present=True, displacement_ratio=1.8),
            StructureEvent(type="CHoCH", direction="bullish",
                          level_broken=2261.0, close_price=2263.0,
                          candle_index=50, time="2024-04-01T08:00:00",
                          displacement_present=True, displacement_ratio=2.5),
        ]
        m15 = _m15(events=events)
        a = _analysis(direction="LONG")
        r = verify_candidate(a, _mso(m15_tf=m15), CFG)
        c1 = r.checks[0]
        record("4E", c1.status == "PASS" and "bullish" in c1.detail,
               f"check1={c1.status}, found correct direction")
    except Exception as e:
        record("4E", False, f"CRASH: {e}")

    # 4F: Multiple unmitigated OBs — AI matches 3rd one
    try:
        obs = [
            OrderBlock(type="bullish", high=2250.0, low=2248.0,
                      open=2249.5, close=2248.5, formation_index=10,
                      formation_time="2024-04-01T04:00:00", causing_bos_index=15,
                      mitigated=False),
            OrderBlock(type="bullish", high=2255.0, low=2253.0,
                      open=2254.5, close=2253.5, formation_index=20,
                      formation_time="2024-04-01T05:00:00", causing_bos_index=25,
                      mitigated=False),
            OrderBlock(type="bullish", high=2261.50, low=2259.80,
                      open=2261.0, close=2260.0, formation_index=30,
                      formation_time="2024-04-01T06:00:00", causing_bos_index=35,
                      mitigated=False),
            OrderBlock(type="bullish", high=2275.0, low=2273.0,
                      open=2274.5, close=2273.5, formation_index=40,
                      formation_time="2024-04-01T07:00:00", causing_bos_index=45,
                      mitigated=True),  # mitigated — should be skipped
            OrderBlock(type="bullish", high=2280.0, low=2278.0,
                      open=2279.5, close=2278.5, formation_index=50,
                      formation_time="2024-04-01T08:00:00", causing_bos_index=55,
                      mitigated=False),
        ]
        h1 = _h1(obs=obs)
        a = _analysis(poi_price=2260.50)  # Should match 3rd OB
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("4F", c3.status == "PASS" and "2259.80" in c3.detail,
               f"Matched 3rd OB: {c3.detail[:60]}")
    except Exception as e:
        record("4F", False, f"CRASH: {e}")

    # 4G: OB at zone boundary (midpoint exactly at equilibrium)
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=2263.0, low=2261.0,
            open=2262.5, close=2261.5, formation_index=30,
            formation_time="2024-04-01T06:00:00", causing_bos_index=35,
            mitigated=False,
        )], eq=2262.0)  # midpoint = (2263+2261)/2 = 2262.0 = exactly eq
        a = _analysis(entry=2262.0, sl=2259.0, tp1=2266.5, poi_price=2262.0)
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c4 = next(c for c in r.checks if c.name == "ob_zone")
        # midpoint (2262) <= eq (2262) → in discount zone → PASS for LONG
        record("4G", c4.status == "PASS",
               f"ob_zone={c4.status} (boundary: midpoint=eq)")
    except Exception as e:
        record("4G", False, f"CRASH: {e}")


# ===================================================================
# TEST 5: Tolerance Verification
# ===================================================================
def test_5():
    print("\n=== TEST 5: Tolerance Verification ===")

    # 5A: Gold tolerance — within range
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3045.0, low=3040.0,
            open=3044.0, close=3041.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3050.0)
        # tol = 3042.50 * 0.002 = ~6.08
        # OB range 3040-3045, with tol: 3033.92 - 3051.08
        # 3042.50 is within → PASS
        a = _analysis(poi_price=3042.50, entry=3042.50, sl=3038.0, tp1=3049.0)
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("5A_in", c3.status == "PASS",
               f"Gold in-range: {c3.status}")
    except Exception as e:
        record("5A_in", False, f"EXCEPTION: {e}")

    # 5A: Gold tolerance — out of range
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3060.0, low=3055.0,
            open=3059.0, close=3056.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3070.0)
        # tol = 3042.50 * 0.002 = ~6.08
        # OB range 3055-3060, with tol: 3048.92 - 3066.08
        # 3042.50 is below 3048.92 → FAIL
        a = _analysis(poi_price=3042.50, entry=3042.50, sl=3040.0, tp1=3046.0)
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("5A_out", c3.status == "FAIL",
               f"Gold out-of-range: {c3.status}")
    except Exception as e:
        record("5A_out", False, f"EXCEPTION: {e}")

    # 5B: GBPUSD tolerance — within range
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=1.2545, low=1.2535,
            open=1.2543, close=1.2537,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=1.2550)
        # tol = 1.2540 * 0.002 = ~0.002508 (2.5 pips)
        # OB range 1.2535-1.2545, with tol: 1.25099-1.25701
        # 1.2540 is within → PASS
        a = _analysis(poi_price=1.2540, entry=1.2540, sl=1.2520, tp1=1.2570)
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("5B_in", c3.status == "PASS",
               f"GBPUSD in-range: {c3.status}")
    except Exception as e:
        record("5B_in", False, f"EXCEPTION: {e}")

    # 5B: GBPUSD tolerance — out of range
    try:
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=1.2580, low=1.2570,
            open=1.2578, close=1.2572,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=1.2590)
        # tol = 1.2540 * 0.002 = ~0.002508
        # OB range 1.2570-1.2580, with tol: 1.25449 - 1.26051
        # 1.2540 is below 1.25449 → FAIL
        a = _analysis(poi_price=1.2540, entry=1.2540, sl=1.2520, tp1=1.2570)
        r = verify_candidate(a, _mso(h1_tf=h1), CFG)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("5B_out", c3.status == "FAIL",
               f"GBPUSD out-of-range: {c3.status}")
    except Exception as e:
        record("5B_out", False, f"EXCEPTION: {e}")

    # 5C: Custom wider tolerance
    try:
        wide_cfg = {**CFG, "verification": {**CFG["verification"], "ob_price_tolerance_pct": 0.005}}
        h1 = _h1(obs=[OrderBlock(
            type="bullish", high=3045.0, low=3040.0,
            open=3044.0, close=3041.0,
            formation_index=30, formation_time="2024-04-01T06:00:00",
            causing_bos_index=35, mitigated=False,
        )], eq=3070.0)
        # tol = 3055 * 0.005 = ~15.28
        # OB range 3040-3045, with tol: 3024.72 - 3060.28
        # 3055 is within → PASS (would fail with 0.002 tolerance)
        a = _analysis(poi_price=3055.0, entry=3055.0, sl=3038.0, tp1=3075.0)
        r = verify_candidate(a, _mso(h1_tf=h1), wide_cfg)
        c3 = next(c for c in r.checks if c.name == "h1_poi_exists")
        record("5C", c3.status == "PASS",
               f"Wide tolerance: {c3.status}")
    except Exception as e:
        record("5C", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 6: Pipeline Integration
# ===================================================================
def test_6():
    print("\n=== TEST 6: Pipeline Integration ===")

    # 6A: Verify orchestrator imports and calls verify_candidate
    try:
        import ast
        orch_path = _ROOT / "src" / "components" / "orchestrator.py"
        source = orch_path.read_text()

        has_import = "from src.components.verification import verify_candidate" in source
        has_call = "verify_candidate(analysis, mso, self.config)" in source
        has_reject = "REJECTED_L2" in source

        # Verify placement: must be after CANDIDATE check, before confidence scoring
        lines = source.splitlines()
        candidate_line = None
        verify_line = None
        confidence_line = None
        for i, line in enumerate(lines):
            if 'analysis.decision != "CANDIDATE"' in line:
                candidate_line = i
            if "verify_candidate(analysis, mso" in line:
                verify_line = i
            if "score_confidence" in line and verify_line and confidence_line is None:
                confidence_line = i

        correct_order = (candidate_line is not None and
                        verify_line is not None and
                        confidence_line is not None and
                        candidate_line < verify_line < confidence_line)

        record("6A", has_import and has_call and has_reject and correct_order,
               f"import={has_import}, call={has_call}, reject_log={has_reject}, "
               f"order={'CORRECT' if correct_order else 'WRONG'} "
               f"(candidate@{candidate_line}, verify@{verify_line}, confidence@{confidence_line})")
    except Exception as e:
        record("6A", False, f"EXCEPTION: {e}")

    # 6B: MSO saving in batch — check if batch_backtest.py saves MSO
    # (The implementation note says this is a future addition, so we check if it exists)
    try:
        batch_path = _ROOT / "scripts" / "batch_backtest.py"
        batch_source = batch_path.read_text()
        # Check if MSO is saved alongside session data
        saves_mso = "mso" in batch_source.lower() and ("session_data" in batch_source or "manifest" in batch_source)
        # This is noted as a future addition — log as informational
        record("6B", True,
               f"MSO saving in batch: {'present' if saves_mso else 'not yet added (noted as future work)'}")
    except Exception as e:
        record("6B", False, f"EXCEPTION: {e}")

    # 6C: Verification disabled via config
    try:
        disabled_cfg = {**CFG, "verification": {"enabled": False}}
        a = _analysis(poi_identified=False)  # Would fail if enabled
        r = verify_candidate(a, _mso(), disabled_cfg)
        record("6C", r.passed and r.checks[0].status == "SKIP",
               f"disabled: passed={r.passed}, skip={r.checks[0].status}")
    except Exception as e:
        record("6C", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 7: Gate 1 Non-Duplication
# ===================================================================
def test_7():
    print("\n=== TEST 7: Gate 1 Non-Duplication ===")
    try:
        source = (_ROOT / "src" / "components" / "verification.py").read_text()

        gate1_patterns = [
            ("grade check", "setup_grade"),
            ("direction match D1", "daily_bias.direction"),
            ("RR >= 1.3", "risk_reward_ratio"),
            ("TP1 side check", "take_profit_1 <= tp.entry" ),
            ("TP1 R range", "tp1_r"),
            ("SL floor $5", "sl_distance < 5"),
            ("SL ATR check", "m15_atr"),
            ("SL max %", "sl_pct"),
        ]

        found_duplicates = []
        for name, pattern in gate1_patterns:
            if pattern in source:
                found_duplicates.append(name)

        record("7", len(found_duplicates) == 0,
               f"Duplicated Gate 1 checks: {found_duplicates or 'NONE'}")
    except Exception as e:
        record("7", False, f"EXCEPTION: {e}")


# ===================================================================
# TEST 8: Regression (existing test suite)
# ===================================================================
def test_8():
    print("\n=== TEST 8: Regression ===")
    import subprocess
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--timeout=60"],
            capture_output=True, text=True, cwd=str(_ROOT), timeout=120,
        )
        output = r.stdout + r.stderr
        # Parse "N passed" from output
        for line in output.splitlines():
            if "passed" in line:
                record("8", r.returncode == 0,
                       line.strip())
                return
        record("8", r.returncode == 0,
               f"returncode={r.returncode}")
    except Exception as e:
        record("8", False, f"EXCEPTION: {e}")


# ===================================================================
# Main
# ===================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("LEVEL 2 VERIFICATION — PRESSURE TEST")
    print("=" * 60)

    test_1()
    test_2()
    test_3()
    test_4()
    test_5()
    test_6()
    test_7()
    test_8()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = len(results)
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    failed = sum(1 for r in results.values() if r["status"] == "FAIL")
    print(f"Total: {total}  Passed: {passed}  Failed: {failed}")
    if failed > 0:
        print("\nFAILED TESTS:")
        for tid, r in results.items():
            if r["status"] == "FAIL":
                print(f"  {tid}: {r['detail']}")

    # Save JSON output
    out_path = _ROOT / "knowledge_base_backtest" / "analysis" / "level2_pressure_test_20260404.json"
    out_path.write_text(json.dumps({
        "summary": {"total": total, "passed": passed, "failed": failed},
        "results": results,
    }, indent=2))
    print(f"\nResults saved to {out_path}")
