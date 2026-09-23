#!/usr/bin/env python3
"""Pressure Test — Trade Data Capture Pipeline.

Tests 1-10 as specified in the pressure test prompt.
Run: python3 knowledge_base_backtest/analysis/trade_capture_pressure_test_runner.py
"""

import json
import os
import sys
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.components.trade_capture import (
    CAPTURE_VERSION,
    create_trade_record,
    update_verification,
    update_gate_results,
    update_execution,
    update_exit,
    save_trade_record,
    load_trade_record,
    build_gate3_result,
    build_gate1_result,
    _extract_system_prompt_text,
    _record_path,
)
from src.components.verification import (
    VerificationCheck,
    VerificationResult,
    verify_candidate,
)
from src.components.permissions import ExecutionDenial
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
from src.prompts.primary_analyzer_prompt import (
    build_system_prompt,
    build_user_message,
    build_static_context,
    format_cross_instrument_context,
)

import yaml

# ---------------------------------------------------------------------------
# Realistic fixture builders
# ---------------------------------------------------------------------------

def _load_config():
    with open(ROOT / "config" / "agent_config.yaml") as f:
        return yaml.safe_load(f)


def _build_realistic_mso() -> MarketStateObject:
    """Build a realistic MSO with all fields populated."""
    return MarketStateObject(
        timestamp_utc="2026-04-07T07:45:00+00:00",
        timeframes={
            "D1": TimeframeState(
                swings=[
                    Swing(index=5, type="high", price=3100.00, time="2026-04-04T00:00:00"),
                    Swing(index=8, type="low", price=3020.00, time="2026-04-02T00:00:00"),
                    Swing(index=12, type="high", price=3080.00, time="2026-03-31T00:00:00"),
                ],
                structure=StructureAnalysis(
                    direction="bullish",
                    protected_swing=Swing(index=8, type="low", price=3020.00,
                                          time="2026-04-02T00:00:00"),
                    swing_sequence=["HH", "HL", "HH"],
                    hh_count=2, hl_count=1,
                ),
                structure_events=[
                    StructureEvent(type="BOS", direction="bullish",
                                   level_broken=3080.00, close_price=3095.00,
                                   candle_index=5, time="2026-04-04T00:00:00",
                                   displacement_present=True, displacement_ratio=2.1),
                ],
                order_blocks=[
                    OrderBlock(type="bullish", high=3060.00, low=3050.00,
                               open=3058.00, close=3052.00, formation_index=4,
                               formation_time="2026-04-03T00:00:00",
                               causing_bos_index=5, mitigated=False),
                ],
                avg_candle_body=8.50,
                atr_14=22.0,
            ),
            "H4": TimeframeState(
                swings=[
                    Swing(index=10, type="high", price=3095.00, time="2026-04-07T04:00:00"),
                    Swing(index=14, type="low", price=3035.00, time="2026-04-06T16:00:00"),
                ],
                structure=StructureAnalysis(
                    direction="bullish",
                    protected_swing=Swing(index=14, type="low", price=3035.00,
                                          time="2026-04-06T16:00:00"),
                    swing_sequence=["HH", "HL"],
                    hh_count=1, hl_count=1,
                ),
                structure_events=[
                    StructureEvent(type="BOS", direction="bullish",
                                   level_broken=3075.00, close_price=3090.00,
                                   candle_index=10, time="2026-04-07T04:00:00",
                                   displacement_present=True, displacement_ratio=1.8),
                ],
                order_blocks=[
                    OrderBlock(type="bullish", high=3048.00, low=3040.00,
                               open=3046.00, close=3042.00, formation_index=12,
                               formation_time="2026-04-06T20:00:00",
                               causing_bos_index=10, mitigated=False),
                ],
                avg_candle_body=5.20,
                atr_14=14.0,
            ),
            "H1": TimeframeState(
                swings=[
                    Swing(index=20, type="high", price=3085.00, time="2026-04-07T06:00:00"),
                    Swing(index=24, type="low", price=3040.00, time="2026-04-07T04:00:00"),
                ],
                structure=StructureAnalysis(
                    direction="bullish",
                    protected_swing=Swing(index=24, type="low", price=3040.00,
                                          time="2026-04-07T04:00:00"),
                    swing_sequence=["HH", "HL"],
                    hh_count=1, hl_count=1,
                ),
                structure_events=[
                    StructureEvent(type="CHoCH", direction="bullish",
                                   level_broken=3065.00, close_price=3070.00,
                                   candle_index=20, time="2026-04-07T06:00:00",
                                   displacement_present=True, displacement_ratio=2.0),
                ],
                order_blocks=[
                    OrderBlock(type="bullish", high=3045.00, low=3040.00,
                               open=3044.00, close=3041.00, formation_index=19,
                               formation_time="2026-04-07T05:00:00",
                               causing_bos_index=20, mitigated=False,
                               causing_event_type="CHoCH"),
                ],
                breaker_blocks=[],
                fair_value_gaps=[],
                premium_discount=PremiumDiscount(
                    impulse_low=3040.00, impulse_high=3085.00,
                    equilibrium_50=3062.50,
                    fib_62=3057.10, fib_79=3049.45,
                    discount_zone=PriceZone(top=3062.50, bottom=3040.00),
                    premium_zone=PriceZone(top=3085.00, bottom=3062.50),
                    ote_zone=PriceZone(top=3057.10, bottom=3049.45),
                ),
                avg_candle_body=3.20,
                atr_14=8.50,
            ),
            "M15": TimeframeState(
                swings=[
                    Swing(index=50, type="high", price=3055.00, time="2026-04-07T07:30:00"),
                    Swing(index=48, type="low", price=3040.50, time="2026-04-07T07:15:00"),
                ],
                structure=StructureAnalysis(
                    direction="bullish",
                    swing_sequence=["HH", "HL"],
                    hh_count=1, hl_count=1,
                ),
                structure_events=[
                    StructureEvent(type="CHoCH", direction="bullish",
                                   level_broken=3048.00, close_price=3052.00,
                                   candle_index=50, time="2026-04-07T07:30:00",
                                   displacement_present=True, displacement_ratio=2.3),
                ],
                order_blocks=[
                    OrderBlock(type="bullish", high=3044.00, low=3041.00,
                               open=3043.50, close=3041.50, formation_index=49,
                               formation_time="2026-04-07T07:15:00",
                               causing_bos_index=50, mitigated=False),
                ],
                avg_candle_body=1.80,
                atr_14=5.00,
            ),
        },
        session_levels=SessionLevels(
            asian_high=3055.00, asian_low=3035.00,
            pdh=3090.00, pdl=3025.00,
            session_high=3058.00, session_low=3038.00,
            london_high=3058.00, london_low=3040.00,
        ),
        liquidity_pools=[],
        detected_sweeps=[],
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-04-07T07:45:00+00:00",
        ),
    )


def _build_realistic_analysis() -> PrimaryAnalysisOutput:
    """Build a realistic CANDIDATE analysis output."""
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-07T07:45:00+00:00",
        model_used="claude-sonnet-4-20250514",
        decision="CANDIDATE",
        confidence_score=80,
        confidence_computation="Baseline 70 + strong displacement (+5) + OTE zone (+5) = 80",
        framework="ob_retest",
        kill_zone="london",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(
                direction="bullish", confidence="high",
                protected_swing_level=3020.00,
                explanation="D1 shows HH/HL sequence with strong impulse."),
            h4_alignment=H4AlignmentAnalysis(
                aligned=True,
                h4_pois_identified=["Bullish OB at 3040-3048"],
                explanation="H4 bullish, aligned with D1."),
            h1_setup=H1SetupAnalysis(
                poi_identified=True, poi_type="OB",
                poi_price_level=3042.50,
                zone="discount", fib_retracement_pct=67.0,
                causing_event_type="CHoCH",
                explanation="H1 bullish CHoCH, unmitigated OB at 3040-3045 in discount."),
            liquidity_sweep=LiquiditySweepAnalysis(
                detected=False, pool_type="none",
                sweep_quality="ambiguous",
                explanation="No clear sweep."),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.3,
                explanation="M15 CHoCH bullish with 2.3x displacement."),
            setup_grade="A+",
            overall_reasoning="Strong D1/H4/H1 aligned bullish. H1 OB in discount OTE zone. M15 CHoCH with strong displacement at OB.",
        ),
        trade_parameters=TradeParameters(
            direction="LONG",
            entry_price=3042.50,
            stop_loss=3035.00,
            sl_buffer_applied=1.50,
            take_profit_1=3053.75,
            take_profit_2=0.0,
            take_profit_3=0.0,
            risk_reward_ratio=1.5,
            position_size_lots=0.01,
        ),
    )


def _build_verification_pass() -> VerificationResult:
    return VerificationResult(
        passed=True,
        checks=[
            VerificationCheck("m15_choch_exists", "PASS",
                              "M15 CHoCH bullish with displacement found at 2026-04-07T07:30:00",
                              mso_value={"time": "2026-04-07T07:30:00", "ratio": 2.3},
                              ai_value=True),
            VerificationCheck("displacement_ratio", "PASS",
                              "M15 displacement ratio 2.30 >= 1.5 threshold",
                              mso_value=2.3, ai_value=2.3),
            VerificationCheck("h1_poi_exists", "PASS",
                              "H1 OB found at 3040.00-3045.00 near AI's POI at 3042.50",
                              mso_value="3040.0-3045.0", ai_value=3042.50),
            VerificationCheck("ob_zone", "PASS",
                              "OB midpoint 3042.50 is in discount zone (eq=3062.50), correct for LONG",
                              mso_value={"midpoint": 3042.50, "equilibrium": 3062.50, "zone": "discount"},
                              ai_value="discount"),
            VerificationCheck("entry_in_ob", "PASS",
                              "Entry 3042.50 is within OB zone 3040.00-3045.00",
                              mso_value="3040.0-3045.0", ai_value=3042.50),
            VerificationCheck("sl_beyond_ob", "PASS",
                              "SL 3035.00 is below OB low 3040.00",
                              mso_value=3040.00, ai_value=3035.00),
        ],
        blocked_by=None,
    )


# ---------------------------------------------------------------------------
# Test runners
# ---------------------------------------------------------------------------

results = {}
details = {}


def run_test(name, fn):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    try:
        passed, detail = fn()
        status = "PASS" if passed else "FAIL"
    except Exception as e:
        import traceback
        passed = False
        status = "FAIL"
        detail = f"EXCEPTION: {e}\n{traceback.format_exc()}"
    results[name] = status
    details[name] = detail
    print(f"  Result: {status}")
    if detail:
        for line in detail.split("\n")[:10]:
            print(f"  {line}")
    return passed


# ---------------------------------------------------------------------------
# TEST 1: Complete Record — Executed Trade
# ---------------------------------------------------------------------------

def test_1_complete_executed_record():
    config = _load_config()
    mso = _build_realistic_mso()
    analysis = _build_realistic_analysis()
    verification = _build_verification_pass()

    # Build real prompt
    system_prompt = build_system_prompt(config)
    static_ctx = build_static_context(mso)
    system_blocks = [{"type": "text", "text": system_prompt + "\n\n## Static Context\n" + static_ctx,
                      "cache_control": {"type": "ephemeral"}}]
    user_msg = build_user_message(
        mso, {"layer1": {}, "layer2": {}, "layer3": []},
        "2026-04-07T07:45:00+00:00", kill_zone="london",
        session_memory="- 07:15 UTC: NO_TRADE — H1 structure unclear",
    )

    # Create record
    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso, prompt_system=system_blocks, prompt_user=user_msg,
        ai_response=analysis.model_dump(mode="json"),
        cross_instrument_context="",
        session_memory="- 07:15 UTC: NO_TRADE — H1 structure unclear",
        config=config,
    )

    # Update verification
    update_verification(record, verification)

    # Update gates
    g3 = {"passed": True, "checks_run": ["daily_loss", "trades_today", "trades_kz", "mt5_connected", "spread"],
           "details": {"daily_pnl_pct": 0.0, "trades_today": 0, "mt5_connected": True, "spread_cents": 15}}
    g1 = {"passed": True, "checks_run": ["grade", "direction", "rr", "tp1_side", "tp1_range", "sl_floor", "sl_atr", "sl_max_pct"],
           "details": {"grade": "A+", "direction": "LONG", "rr": 1.5, "sl_distance": 7.5}}
    update_gate_results(record, g3, g1)

    # Update execution
    update_execution(record, {
        "executed": True,
        "timestamp": "2026-04-07T07:45:12+00:00",
        "entry_price_actual": 3042.60,
        "entry_spread": 0.25,
        "slippage": 0.10,
        "mt5_ticket": 0,
        "lot_size": 0.10,
        "risk_pct": 1.0,
    })
    record["decision_pipeline"]["final_outcome"] = "EXECUTED"

    # Update exit
    update_exit(record, {
        "exit_type": "CLOSED_TP1",
        "exit_price": 3053.80,
        "exit_time": "2026-04-07T08:30:00+00:00",
        "actual_r": round((3053.80 - 3042.60) / 7.5, 2),
        "hold_time_minutes": 45,
        "mfe_price": 3055.20,
        "mfe_r": round((3055.20 - 3042.60) / 7.5, 2),
        "mae_price": 3039.50,
        "mae_r": round((3039.50 - 3042.60) / 7.5, 2),
    })

    # Save and load
    with tempfile.TemporaryDirectory() as tmp:
        path = save_trade_record(record, os.path.join(tmp, "trade_records"))
        loaded = load_trade_record(path)
        file_size = os.path.getsize(path)

    # Verify all fields
    checks = []
    def check(cond, msg):
        checks.append((cond, msg))

    # metadata
    check(loaded["metadata"]["trade_id"] == "XAUUSD_2026-04-07_london_0745", "trade_id")
    check(loaded["metadata"]["date"] == "2026-04-07", "date")
    check(loaded["metadata"]["symbol"] == "XAUUSD", "symbol")
    check(loaded["metadata"]["kill_zone"] == "london", "kill_zone")
    check(loaded["metadata"]["candle_time"] is not None, "candle_time")
    check(loaded["metadata"]["capture_version"] == CAPTURE_VERSION, "capture_version")

    # decision_pipeline
    dp = loaded["decision_pipeline"]
    check(dp["ai_decision"] == "CANDIDATE", "ai_decision")
    check(dp["ai_grade"] == "A+", "ai_grade")
    check(dp["ai_confidence"] == 80, "ai_confidence")
    check(dp["ai_direction"] == "LONG", "ai_direction")
    check(dp["final_outcome"] == "EXECUTED", "final_outcome")

    # L2 verification
    l2 = dp["level2_verification"]
    check(l2["passed"] is True, "l2_passed")
    check(len(l2["checks"]) == 6, f"l2_check_count={len(l2['checks'])}")
    check(all(c["status"] == "PASS" for c in l2["checks"]), "all_l2_checks_pass")

    # gates
    check(dp["gate3_result"]["passed"] is True, "g3_passed")
    check(dp["gate1_result"]["passed"] is True, "g1_passed")

    # context
    check(loaded["context_at_decision"]["session_memory"] != "", "session_memory_present")

    # mso
    check(isinstance(loaded["mso"], dict), "mso_is_dict")
    check("timeframes" in loaded["mso"], "mso_has_timeframes")
    check("D1" in loaded["mso"]["timeframes"], "mso_has_D1")
    check("session_levels" in loaded["mso"], "mso_has_session_levels")

    # prompt
    check(len(loaded["prompt"]["system_prompt"]) > 5000, f"system_prompt_len={len(loaded['prompt']['system_prompt'])}")
    check(len(loaded["prompt"]["user_message"]) > 200, f"user_message_len={len(loaded['prompt']['user_message'])}")

    # ai_response
    check(loaded["ai_response"]["decision"] == "CANDIDATE", "ai_response_decision")
    check(loaded["ai_response"]["reasoning"]["setup_grade"] == "A+", "ai_response_grade")

    # trade_parameters
    tp = loaded["trade_parameters"]
    check(tp["direction"] == "LONG", "tp_direction")
    check(tp["entry_price"] == 3042.50, "tp_entry")
    check(tp["stop_loss"] == 3035.00, "tp_sl")
    check(tp["take_profit_1"] == 3053.75, "tp_tp1")

    # execution
    ex = loaded["execution"]
    check(ex["executed"] is True, "ex_executed")
    check(ex["entry_price_actual"] == 3042.60, "ex_actual_price")
    check(ex["entry_spread"] == 0.25, "ex_spread")
    check(ex["slippage"] == 0.10, "ex_slippage")
    check(ex["mt5_ticket"] == 0, "ex_ticket")

    # exit
    ext = loaded["exit"]
    check(ext["exit_type"] == "CLOSED_TP1", "exit_type")
    check(ext["exit_price"] == 3053.80, "exit_price")
    check(ext["actual_r"] > 0, "exit_actual_r_positive")
    check(ext["mfe_r"] > 0, "exit_mfe_r_positive")
    check(ext["mae_r"] < 0, "exit_mae_r_negative")
    check(ext["hold_time_minutes"] == 45, "exit_hold_time")

    # file size
    check(file_size > 10000, f"file_size={file_size} > 10KB")

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED checks: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed. File size: {file_size} bytes"


# ---------------------------------------------------------------------------
# TEST 2: Rejected by Level 2
# ---------------------------------------------------------------------------

def test_2_rejected_l2():
    config = _load_config()
    mso = _build_realistic_mso()
    analysis = _build_realistic_analysis()

    # Create record
    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso,
        prompt_system=build_system_prompt(config),
        prompt_user="## Dynamic Market Data\nTest user message with enough content.",
        ai_response=analysis.model_dump(mode="json"),
        cross_instrument_context="",
        session_memory="- 07:15: NO_TRADE",
        config=config,
    )

    # L2 fails on h1_poi_exists
    verification = VerificationResult(
        passed=False,
        checks=[
            VerificationCheck("m15_choch_exists", "PASS", "CHoCH found"),
            VerificationCheck("displacement_ratio", "PASS", "ratio=2.3 >= 1.5"),
            VerificationCheck("h1_poi_exists", "FAIL",
                              "AI cites H1 POI at 3070.00 but no unmitigated OB found",
                              mso_value=[], ai_value=3070.00),
        ],
        blocked_by="h1_poi_exists",
    )
    update_verification(record, verification)
    record["decision_pipeline"]["final_outcome"] = "REJECTED_L2"

    with tempfile.TemporaryDirectory() as tmp:
        path = save_trade_record(record, os.path.join(tmp, "trade_records"))
        loaded = load_trade_record(path)

    checks = []
    checks.append((loaded["decision_pipeline"]["final_outcome"] == "REJECTED_L2", "outcome"))
    checks.append((loaded["decision_pipeline"]["level2_verification"]["passed"] is False, "l2_failed"))
    checks.append((loaded["decision_pipeline"]["level2_verification"]["blocked_by"] == "h1_poi_exists", "blocked_by"))
    checks.append((loaded["execution"] is None, "execution_null"))
    checks.append((loaded["exit"] is None, "exit_null"))
    checks.append((isinstance(loaded["mso"], dict), "mso_present"))
    checks.append((len(loaded["prompt"]["system_prompt"]) > 1000, "prompt_present"))
    checks.append((loaded["ai_response"]["decision"] == "CANDIDATE", "ai_response_present"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed."


# ---------------------------------------------------------------------------
# TEST 3: Rejected by Gate 1
# ---------------------------------------------------------------------------

def test_3_rejected_gate():
    config = _load_config()
    mso = _build_realistic_mso()
    analysis = _build_realistic_analysis()

    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso,
        prompt_system=build_system_prompt(config),
        prompt_user="## Dynamic Market Data\nuser msg",
        ai_response=analysis.model_dump(mode="json"),
        cross_instrument_context="",
        session_memory="",
        config=config,
    )

    # L2 passes
    update_verification(record, _build_verification_pass())

    # Gate 1 fails
    g3 = {"passed": True, "checks_run": ["daily_loss"], "details": {}}
    g1 = {"passed": False, "checks_run": ["grade", "direction", "rr"],
           "details": {"denial_reason": "below_grade_threshold: B", "grade": "B"}}
    update_gate_results(record, g3, g1)
    record["decision_pipeline"]["final_outcome"] = "REJECTED_GATE1_SAFETY"

    with tempfile.TemporaryDirectory() as tmp:
        path = save_trade_record(record, os.path.join(tmp, "trade_records"))
        loaded = load_trade_record(path)

    checks = []
    checks.append((loaded["decision_pipeline"]["final_outcome"] == "REJECTED_GATE1_SAFETY", "outcome"))
    checks.append((loaded["decision_pipeline"]["level2_verification"]["passed"] is True, "l2_passed"))
    checks.append((loaded["decision_pipeline"]["gate1_result"]["passed"] is False, "g1_failed"))
    checks.append((loaded["execution"] is None, "execution_null"))
    checks.append((loaded["exit"] is None, "exit_null"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed."


# ---------------------------------------------------------------------------
# TEST 4: Prompt Capture Fidelity
# ---------------------------------------------------------------------------

def test_4_prompt_fidelity():
    config = _load_config()
    mso = _build_realistic_mso()
    analysis = _build_realistic_analysis()

    # Generate prompt directly
    system_text = build_system_prompt(config)
    static_ctx = build_static_context(mso)
    full_system = system_text + "\n\n## Static Context (D1/H4/Session)\n" + static_ctx

    kb_context = {"layer1": {}, "layer2": {}, "layer3": []}
    session_memory = "- 07:15 UTC: NO_TRADE — H1 structure unclear\n- 07:30 UTC: WAIT — pullback developing"
    ci_context = ""

    user_msg = build_user_message(
        mso, kb_context, "2026-04-07T07:45:00+00:00",
        kill_zone="london", session_memory=session_memory,
        cross_instrument_context=ci_context,
    )

    # Simulate what PrimaryAnalyzer does — system blocks format
    system_blocks = [{"type": "text", "text": full_system,
                      "cache_control": {"type": "ephemeral"}}]

    # Create record
    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso, prompt_system=system_blocks, prompt_user=user_msg,
        ai_response=analysis.model_dump(mode="json"),
        cross_instrument_context=ci_context,
        session_memory=session_memory,
        config=config,
    )

    captured_system = record["prompt"]["system_prompt"]
    captured_user = record["prompt"]["user_message"]

    checks = []

    # System prompt fidelity
    checks.append((captured_system == full_system, "system_prompt_exact_match"))
    checks.append(("Internal Consistency Rules" in captured_system, "contains_internal_consistency"))
    checks.append(("confidence" in captured_system.lower(), "contains_confidence"))
    checks.append(("EVALUATION SEQUENCE" in captured_system, "contains_eval_sequence"))
    checks.append(("Data Grounding Rules" in captured_system, "contains_anti_hallucination"))
    checks.append((len(captured_system) > 3000, f"system_len={len(captured_system)}"))

    # User message fidelity
    checks.append((captured_user == user_msg, "user_message_exact_match"))
    checks.append(("Dynamic Market Data" in captured_user, "contains_dynamic_data"))
    checks.append(("Prior Candle Assessments" in captured_user, "contains_session_memory"))
    checks.append((len(captured_user) > 200, f"user_len={len(captured_user)}"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        # Show diff for exact match failures
        detail_lines = [f"FAILED: {', '.join(failed)}"]
        if not checks[0][0]:  # system prompt mismatch
            detail_lines.append(f"System prompt len: expected={len(full_system)} captured={len(captured_system)}")
            # Find first difference
            for i, (a, b) in enumerate(zip(full_system, captured_system)):
                if a != b:
                    detail_lines.append(f"First diff at char {i}: expected='{a}' got='{b}'")
                    detail_lines.append(f"Context: ...{full_system[max(0,i-20):i+20]}...")
                    break
        return False, "\n".join(detail_lines)
    return True, f"All {len(checks)} checks passed. System={len(captured_system)} chars, User={len(captured_user)} chars"


# ---------------------------------------------------------------------------
# TEST 5: MSO Serialization
# ---------------------------------------------------------------------------

def test_5_mso_serialization():
    config = _load_config()
    mso = _build_realistic_mso()

    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso, prompt_system="sys", prompt_user="usr",
        ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
                      "trade_parameters": {"direction": "LONG"}, "framework": "ob_retest",
                      "confidence_score": 80},
        cross_instrument_context=None, session_memory="",
        config=config,
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = save_trade_record(record, os.path.join(tmp, "trade_records"))
        loaded = load_trade_record(path)
        file_size = os.path.getsize(path)

    m = loaded["mso"]
    checks = []

    # Top-level keys
    checks.append(("timestamp_utc" in m, "has_timestamp"))
    checks.append(("timeframes" in m, "has_timeframes"))
    checks.append(("session_levels" in m, "has_session_levels"))
    checks.append(("data_quality" in m, "has_data_quality"))

    # Nested structures
    h1 = m["timeframes"]["H1"]
    checks.append(("order_blocks" in h1, "h1_has_obs"))
    checks.append((len(h1["order_blocks"]) > 0, "h1_obs_populated"))
    ob = h1["order_blocks"][0]
    checks.append(("high" in ob, "ob_has_high"))
    checks.append(("low" in ob, "ob_has_low"))
    checks.append(("mitigated" in ob, "ob_has_mitigated"))

    # Float precision
    checks.append((isinstance(ob["high"], float), f"ob_high_is_float={type(ob['high']).__name__}"))
    checks.append((ob["high"] == 3045.0, f"ob_high_value={ob['high']}"))

    # Structure events
    se = h1["structure_events"]
    checks.append((len(se) > 0, "h1_has_structure_events"))
    checks.append((se[0]["displacement_ratio"] == 2.0, f"displacement_ratio={se[0]['displacement_ratio']}"))

    # Premium/discount
    pd = h1.get("premium_discount")
    checks.append((pd is not None, "h1_has_premium_discount"))
    if pd:
        checks.append((pd["equilibrium_50"] == 3062.5, f"equilibrium={pd['equilibrium_50']}"))

    # File size
    checks.append((file_size < 200_000, f"file_size={file_size} < 200KB"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed. MSO JSON size OK, file={file_size} bytes"


# ---------------------------------------------------------------------------
# TEST 6: Cross-Instrument Context Capture
# ---------------------------------------------------------------------------

def test_6_cross_instrument():
    config = _load_config()
    mso = _build_realistic_mso()
    ai_resp = {"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
               "trade_parameters": {"direction": "LONG"}, "framework": "ob_retest",
               "confidence_score": 80}

    # GBPUSD with cross-instrument context
    ci_text = format_cross_instrument_context("bullish", {"asian_range": 0.00045, "pct_of_adr": 54.2, "category": "wide"}, config)
    # For GBPUSD, CI is only enabled if config enables it — use GBPUSD override
    gbpusd_ci = "XAUUSD D1 structure: bullish (indicates dollar weakness)\nAsian session range: 0.00045 = 54% of ADR (wide)"

    record_gbp = create_trade_record(
        symbol="GBPUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso, prompt_system="sys", prompt_user="usr",
        ai_response=ai_resp,
        cross_instrument_context=gbpusd_ci,
        session_memory="",
        config=config,
    )

    # XAUUSD without cross-instrument
    record_xau = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=mso, prompt_system="sys", prompt_user="usr",
        ai_response=ai_resp,
        cross_instrument_context=None,
        session_memory="",
        config=config,
    )

    checks = []

    # GBPUSD
    ci_gbp = record_gbp["context_at_decision"]["cross_instrument_context"]
    checks.append((len(ci_gbp) > 0, "gbpusd_has_ci"))
    checks.append(("bullish" in ci_gbp, "gbpusd_ci_has_direction"))
    checks.append(("54" in ci_gbp, "gbpusd_ci_has_asian_range"))

    # XAUUSD
    ci_xau = record_xau["context_at_decision"]["cross_instrument_context"]
    checks.append((ci_xau == "", "xauusd_ci_empty"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed."


# ---------------------------------------------------------------------------
# TEST 7: Pipeline Non-Interference
# ---------------------------------------------------------------------------

def test_7_pipeline_non_interference():
    checks = []

    # 7A: save_trade_record failure doesn't raise
    record = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso={}, prompt_system="sys", prompt_user="usr",
        ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
                      "trade_parameters": {"direction": "LONG"}, "framework": "ob_retest",
                      "confidence_score": 80},
        cross_instrument_context=None, session_memory="",
        config=_load_config(),
    )

    # Force save to fail by using an invalid path
    result = save_trade_record(record, "/nonexistent/readonly/path/that/cannot/exist")
    checks.append((result is None, "save_failure_returns_none"))
    # If we got here, it didn't raise
    checks.append((True, "save_failure_no_exception"))

    # 7B: Latency
    config = _load_config()
    mso = _build_realistic_mso()
    ai_resp = _build_realistic_analysis().model_dump(mode="json")

    with tempfile.TemporaryDirectory() as tmp:
        # With capture
        t0 = time.perf_counter()
        for _ in range(10):
            r = create_trade_record(
                symbol="XAUUSD", kill_zone="london",
                candle_time="2026-04-07T07:45:00+00:00",
                mso=mso, prompt_system=build_system_prompt(config),
                prompt_user="user msg", ai_response=ai_resp,
                cross_instrument_context=None, session_memory="",
                config=config,
            )
            save_trade_record(r, os.path.join(tmp, "trade_records"))
        t1 = time.perf_counter()
        avg_ms = ((t1 - t0) / 10) * 1000

    checks.append((avg_ms < 100, f"avg_latency={avg_ms:.1f}ms < 100ms"))

    # 7C: Disabled capture — orchestrator gates saving, but create still works
    config_off = _load_config()
    config_off["trade_capture"] = {"enabled": False}
    record_off = create_trade_record(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso={}, prompt_system="sys", prompt_user="usr",
        ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
                      "trade_parameters": {"direction": "LONG"}, "framework": "ob_retest",
                      "confidence_score": 80},
        cross_instrument_context=None, session_memory="",
        config=config_off,
    )
    # Record created but orchestrator wouldn't save it
    checks.append((record_off["metadata"]["trade_id"] is not None, "disabled_still_creates_record"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed. Avg write: {avg_ms:.1f}ms"


# ---------------------------------------------------------------------------
# TEST 8: File Structure and Naming
# ---------------------------------------------------------------------------

def test_8_file_structure():
    config = _load_config()

    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "trade_records")

        # London trade
        r1 = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00+00:00",
            mso={}, prompt_system="sys", prompt_user="usr",
            ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
                          "trade_parameters": {"direction": "LONG"}, "framework": "ob_retest",
                          "confidence_score": 80},
            cross_instrument_context=None, session_memory="",
            config=config,
        )
        p1 = save_trade_record(r1, base)

        # NY trade — same day, different KZ
        r2 = create_trade_record(
            symbol="XAUUSD", kill_zone="ny",
            candle_time="2026-04-07T13:30:00+00:00",
            mso={}, prompt_system="sys", prompt_user="usr",
            ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A"},
                          "trade_parameters": {"direction": "SHORT"}, "framework": "ob_retest",
                          "confidence_score": 75},
            cross_instrument_context=None, session_memory="",
            config=config,
        )
        p2 = save_trade_record(r2, base)

        checks = []

        # Path structure
        checks.append((p1 is not None, "london_saved"))
        checks.append((p2 is not None, "ny_saved"))
        checks.append(("XAUUSD" in p1, "london_has_symbol_dir"))
        checks.append(("2026-04-07_london_0745.json" in p1, f"london_filename={Path(p1).name}"))
        checks.append(("2026-04-07_ny_1330.json" in p2, f"ny_filename={Path(p2).name}"))
        checks.append((p1 != p2, "different_files"))

        # No temp files
        tmp_files = list(Path(base).rglob("*.tmp"))
        checks.append((len(tmp_files) == 0, f"no_tmp_files={len(tmp_files)}"))

        # Both files exist
        checks.append((os.path.exists(p1), "london_exists"))
        checks.append((os.path.exists(p2), "ny_exists"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed."


# ---------------------------------------------------------------------------
# TEST 9: Exit Data Completeness
# ---------------------------------------------------------------------------

def test_9_exit_data():
    checks = []

    entry = 3042.50
    sl = 3035.00
    sl_dist = abs(entry - sl)  # 7.50

    # TP1 exit (LONG)
    tp1_exit = 3053.80
    tp1_r = round((tp1_exit - entry) / sl_dist, 2)
    checks.append((abs(tp1_r - 1.51) < 0.01, f"tp1_r={tp1_r}≈1.51"))
    checks.append((tp1_r > 0, "tp1_r_positive"))

    # SL exit (LONG)
    sl_exit = 3035.00
    sl_r = round((sl_exit - entry) / sl_dist, 2)
    checks.append((abs(sl_r - (-1.0)) < 0.01, f"sl_r={sl_r}≈-1.0"))
    checks.append((sl_r < 0, "sl_r_negative"))

    # BE exit (LONG)
    be_exit = 3042.50
    be_r = round((be_exit - entry) / sl_dist, 2)
    checks.append((be_r == 0.0, f"be_r={be_r}≈0.0"))

    # SHORT direction
    s_entry = 3080.00
    s_sl = 3090.00
    s_sl_dist = abs(s_entry - s_sl)  # 10.0
    s_tp1 = 3065.00
    s_r = round((s_entry - s_tp1) / s_sl_dist, 2)
    checks.append((abs(s_r - 1.5) < 0.01, f"short_tp1_r={s_r}≈1.5"))

    # Build full exit records
    for exit_type, exit_price, expected_r_sign in [
        ("CLOSED_TP1", 3053.80, "positive"),
        ("CLOSED_SL", 3035.00, "negative"),
        ("CLOSED_BE", 3042.50, "zero"),
        ("CLOSED_SESSION_TIMEOUT", 3045.00, "positive"),
    ]:
        r = (exit_price - entry) / sl_dist
        record = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00+00:00",
            mso={}, prompt_system="sys", prompt_user="usr",
            ai_response={"decision": "CANDIDATE", "reasoning": {"setup_grade": "A+"},
                          "trade_parameters": {"direction": "LONG", "entry_price": entry,
                                                "stop_loss": sl, "take_profit_1": 3053.75},
                          "framework": "ob_retest", "confidence_score": 80},
            cross_instrument_context=None, session_memory="",
            config=_load_config(),
        )
        update_exit(record, {
            "exit_type": exit_type,
            "exit_price": exit_price,
            "exit_time": "2026-04-07T08:30:00+00:00",
            "actual_r": round(r, 2),
            "hold_time_minutes": 45,
            "mfe_price": 3055.20,
            "mfe_r": round((3055.20 - entry) / sl_dist, 2),
            "mae_price": 3039.50,
            "mae_r": round((3039.50 - entry) / sl_dist, 2),
        })

        ext = record["exit"]
        checks.append((ext["exit_type"] == exit_type, f"{exit_type}_type"))
        checks.append((ext["actual_r"] is not None, f"{exit_type}_r_not_null"))
        checks.append((ext["mfe_r"] is not None, f"{exit_type}_mfe_not_null"))
        checks.append((ext["mae_r"] is not None, f"{exit_type}_mae_not_null"))
        checks.append((ext["hold_time_minutes"] > 0, f"{exit_type}_hold_positive"))

    failed = [msg for cond, msg in checks if not cond]
    if failed:
        return False, f"FAILED: {', '.join(failed)}"
    return True, f"All {len(checks)} checks passed."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  TRADE CAPTURE PIPELINE — PRESSURE TEST")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    run_test("Test 1  (Complete Executed Record)", test_1_complete_executed_record)
    run_test("Test 2  (L2 Rejected Record)", test_2_rejected_l2)
    run_test("Test 3  (Gate Rejected Record)", test_3_rejected_gate)
    run_test("Test 4  (Prompt Capture Fidelity)", test_4_prompt_fidelity)
    run_test("Test 5  (MSO Serialization)", test_5_mso_serialization)
    run_test("Test 6  (Cross-Instrument Context)", test_6_cross_instrument)
    run_test("Test 7  (Pipeline Non-Interference)", test_7_pipeline_non_interference)
    run_test("Test 8  (File Structure/Naming)", test_8_file_structure)
    run_test("Test 9  (Exit Data Completeness)", test_9_exit_data)

    # Test 10 is the regression suite — handled separately
    print(f"\n{'='*60}")
    print("Test 10 (Regression): Run separately with pytest")
    print(f"{'='*60}")

    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    total = len(results)
    passed = sum(1 for v in results.values() if v == "PASS")
    for name, status in results.items():
        print(f"  {name}: {status}")
    print(f"\n  {passed}/{total} passed")

    return results, details


if __name__ == "__main__":
    main()
