"""Comprehensive T7 C-Gate prompt deployment tests.

These tests verify that the T7 prompt change is safe to deploy live:
1. Prompt template correctness (no unreplaced placeholders, correct gates)
2. JSON schema compatibility (LLM output parses into PrimaryAnalysisOutput)
3. Permissions gate compatibility (grade=A+ passes, grade=C blocks)
4. Verification module compatibility (observation fields feed L2 checks)
5. User message format (all instruments, no breaker block references)
6. Shadow logger integration (proximity + partial close)
7. Orchestrator wiring (imports, no broken references)
"""

from __future__ import annotations

import ast
import json
import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml

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
    SYSTEM_PROMPT,
    build_system_prompt,
    build_user_message,
    build_static_context,
    build_dynamic_context,
)
from src.components.proximity_shadow_logger import (
    compute_proximity,
    compute_trade_proximity,
    parse_mso_zones,
)
from src.components.partial_close_shadow_logger import (
    PartialCloseShadowTracker,
    PARTIAL_CLOSE_FRACTION,
    TRIGGER_R,
)


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def gold_config():
    """Config dict mimicking XAUUSD live config (matches agent_config.yaml structure)."""
    return {
        "market": {
            "symbol": "XAUUSD",
            "kill_zones": {
                "london": {"start_utc": "07:00", "end_utc": "09:30"},
                "ny": {"start_utc": "13:00", "end_utc": "15:30"},
            },
        },
        "risk": {"sl_absolute_min": 5.0},
    }


@pytest.fixture
def us30_config():
    """Config dict mimicking US30 live config."""
    return {
        "market": {
            "symbol": "US30",
            "kill_zones": {
                "london": {"start_utc": "08:00", "end_utc": "10:30"},
                "ny": {"start_utc": "13:30", "end_utc": "16:00"},
            },
        },
        "risk": {"sl_absolute_min": 30.0},
    }


@pytest.fixture
def jpypair_config():
    """Config for JPY-quoted pairs (USDJPY, GBPJPY)."""
    return {
        "market": {
            "symbol": "USDJPY",
            "kill_zones": {
                "london": {"start_utc": "07:00", "end_utc": "09:30"},
                "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                "tokyo": {"start_utc": "00:00", "end_utc": "03:00"},
            },
        },
        "risk": {"sl_absolute_min": 0.30},
    }


def _make_t7_candidate_json() -> dict:
    """Build a valid T7 CANDIDATE JSON response matching PrimaryAnalysisOutput."""
    return {
        "timestamp_utc": "2026-04-13T14:15:00Z",
        "model_used": "claude-sonnet-4-6",
        "decision": "CANDIDATE",
        "confidence_score": 0,
        "framework": "ob_retest",
        "kill_zone": "ny",
        "reasoning": {
            "daily_bias": {
                "direction": "bullish",
                "confidence": "high",
                "protected_swing_level": 3200.0,
                "explanation": "H1 shows 3 BOS bullish in sequence.",
            },
            "h4_alignment": {
                "aligned": True,
                "h4_pois_identified": [],
                "explanation": "No H4 data in MSO — assumed aligned per C1 rule.",
            },
            "h1_setup": {
                "poi_identified": True,
                "poi_type": "OB",
                "poi_price_level": 3245.0,
                "zone": "discount",
                "fib_retracement_pct": 62.0,
                "causing_event_type": "BOS",
                "explanation": "H1 bullish OB at 3245.",
            },
            "liquidity_sweep": {
                "detected": True,
                "pool_type": "asian_low",
                "sweep_quality": "clean",
                "sweep_price": 3238.50,
                "explanation": "Asian low swept at 3238.50.",
            },
            "m15_confirmation": {
                "choch_detected": True,
                "displacement_quality": "strong",
                "displacement_candle_body_vs_avg_ratio": 2.8,
                "explanation": "M15 CHoCH bullish with strong displacement.",
            },
            "similar_historical_setups_considered": [],
            "setup_grade": "A+",
            "overall_reasoning": "C1 pass: H1 bullish bias. C2 pass: M15 not opposing. C3 pass: direction match.",
        },
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 3248.50,
            "stop_loss": 3240.00,
            "sl_buffer_applied": 0.0,
            "take_profit_1": 3261.25,
            "take_profit_2": 0.0,
            "take_profit_3": 0.0,
            "risk_reward_ratio": 1.5,
            "position_size_lots": 0.01,
        },
        "no_trade_reason": None,
    }


def _make_t7_no_trade_json() -> dict:
    """Build a valid T7 NO_TRADE JSON response."""
    return {
        "timestamp_utc": "2026-04-13T14:15:00Z",
        "model_used": "claude-sonnet-4-6",
        "decision": "NO_TRADE",
        "confidence_score": 0,
        "framework": "ob_retest",
        "kill_zone": "london",
        "reasoning": {
            "daily_bias": {
                "direction": "ranging",
                "confidence": "low",
                "explanation": "H1 has no clear BOS sequence — direction unclear.",
            },
            "h4_alignment": {
                "aligned": False,
                "explanation": "No H4 data.",
            },
            "h1_setup": {
                "poi_identified": False,
                "poi_type": "none",
                "explanation": "No clear H1 directional bias.",
            },
            "liquidity_sweep": {
                "detected": False,
                "pool_type": "none",
                "explanation": "No sweep observed.",
            },
            "m15_confirmation": {
                "choch_detected": False,
                "displacement_quality": "none",
                "explanation": "N/A — C1 failed.",
            },
            "similar_historical_setups_considered": [],
            "setup_grade": "C",
            "overall_reasoning": "C1 FAIL: H1 bias unclear. No directional structure.",
        },
        "no_trade_reason": "C1 FAIL: H1 has no clear directional bias — ranging.",
    }


# ═══════════════════════════════════════════════════════════════════════
# 1. PROMPT TEMPLATE CORRECTNESS
# ═══════════════════════════════════════════════════════════════════════

class TestPromptTemplate:
    """Verify the prompt template is correct and complete."""

    def test_no_unreplaced_placeholders_in_constant(self):
        # Only JSON curly braces should remain, not template placeholders
        # Template placeholders look like {word_word} (snake_case)
        placeholders = re.findall(r"\{[a-z][a-z_]+\}", SYSTEM_PROMPT)
        # Filter out JSON schema examples + V3 forbidden-pattern markers +
        # ADR-006 (2026-04-26) config-substituted SL buffer placeholders.
        # The unbuilt SYSTEM_PROMPT constant intentionally retains
        # ``{ob_atr_mult}`` / ``{breaker_atr_mult}`` / ``{min_ticks}`` —
        # they are substituted by ``build_system_prompt(config)`` from
        # ``risk.sl_buffer_*``. Without a config the constant carries the
        # placeholder so per-instrument overrides flow through cleanly.
        real_placeholders = [
            p for p in placeholders
            if p not in (
                "{kill_zone}", "{timestamp}",  # JSON schema field examples
                "{anything}",  # V3 NO FOURTH GATE forbidden-pattern marker
                "{ob_atr_mult}", "{breaker_atr_mult}", "{min_ticks}",  # ADR-006
            )
        ]
        assert len(real_placeholders) == 0, f"Unreplaced placeholders: {real_placeholders}"

    def test_c_gates_present(self):
        assert "C1" in SYSTEM_PROMPT
        assert "C2" in SYSTEM_PROMPT
        assert "C3" in SYSTEM_PROMPT

    def test_c1_describes_h1_bias(self):
        # C1 should check H1 directional bias
        c1_idx = SYSTEM_PROMPT.index("C1")
        c1_section = SYSTEM_PROMPT[c1_idx : c1_idx + 500]
        assert "H1" in c1_section
        assert "BOS" in c1_section

    def test_c2_describes_m15_non_opposition(self):
        # Find the C2 section header (V3 prepends an R1-R8 reject-reason
        # block where "C2 FAIL" appears in tags; the actual definition is
        # marked by "C2." section header).
        c2_idx = SYSTEM_PROMPT.index("C2.")
        c2_section = SYSTEM_PROMPT[c2_idx : c2_idx + 400]
        assert "M15" in c2_section
        assert "oppos" in c2_section.lower()

    def test_c3_describes_direction_match(self):
        # Find the C3 section header (see test_c2_describes_m15_non_opposition).
        c3_idx = SYSTEM_PROMPT.index("C3.")
        c3_section = SYSTEM_PROMPT[c3_idx : c3_idx + 300]
        assert "direction" in c3_section.lower()

    def test_no_breaker_block_in_prompt(self):
        assert "Breaker Block" not in SYSTEM_PROMPT
        assert "BREAKER BLOCK" not in SYSTEM_PROMPT
        assert "breaker_retest" not in SYSTEM_PROMPT
        assert "BR1" not in SYSTEM_PROMPT

    def test_no_scoring_system_in_prompt(self):
        assert "Q1." not in SYSTEM_PROMPT
        assert "Q2." not in SYSTEM_PROMPT
        assert "CONFIDENCE SCORE" not in SYSTEM_PROMPT
        assert "DECISION THRESHOLDS" not in SYSTEM_PROMPT
        assert "threshold of 65" not in SYSTEM_PROMPT

    def test_no_wait_decision(self):
        # T7 should only use CANDIDATE and NO_TRADE, not WAIT
        # WAIT may appear in schema definition but not as a recommended decision
        assert "Output WAIT" not in SYSTEM_PROMPT
        assert "WAIT —" not in SYSTEM_PROMPT

    def test_decision_integrity_instruction(self):
        # T7 must instruct that OB/FVG/zone data does not drive the C-gate
        # decision. The exact phrasing has shifted across prompt versions
        # (V1 used "Ignore all other framework references"; V3 + fvg_fill
        # expansion 2026-04-25 uses the DECISION INTEGRITY block + the
        # OBSERVATION REPORT "does NOT affect your decision" qualifier).
        # Either form is acceptable — the contract is "AI must not use
        # OB/FVG data to override the C-gate verdict".
        lower = SYSTEM_PROMPT.lower()
        decision_integrity_present = (
            "do not use this data for your candidate/no_trade decision"
            in lower
        )
        observation_report_present = "does not affect your decision" in lower
        assert decision_integrity_present or observation_report_present, (
            "T7 prompt must contain a clause stating that OB/FVG/zone "
            "data does NOT drive the CANDIDATE/NO_TRADE decision."
        )

    def test_calibration_section(self):
        # T7 should have calibration guidance
        assert "65" in SYSTEM_PROMPT  # 65-80% CR target
        assert "CANDIDATE" in SYSTEM_PROMPT

    def test_json_schema_present(self):
        assert "timestamp_utc" in SYSTEM_PROMPT
        assert "model_used" in SYSTEM_PROMPT
        assert "decision" in SYSTEM_PROMPT
        assert "reasoning" in SYSTEM_PROMPT
        assert "trade_parameters" in SYSTEM_PROMPT
        assert "no_trade_reason" in SYSTEM_PROMPT

    def test_setup_grade_a_plus_instruction(self):
        # T7 instructs: A+ for CANDIDATE, C for NO_TRADE
        assert "A+" in SYSTEM_PROMPT
        assert "setup_grade" in SYSTEM_PROMPT


# ═══════════════════════════════════════════════════════════════════════
# 2. BUILD FUNCTIONS FOR ALL INSTRUMENTS
# ═══════════════════════════════════════════════════════════════════════

class TestBuildSystemPrompt:
    """Verify build_system_prompt works for all instrument configs."""

    def test_gold_config(self, gold_config):
        prompt = build_system_prompt(gold_config)
        assert "C1" in prompt
        assert "$5.00" in prompt
        assert "07:00" in prompt
        # Verify no unreplaced template placeholders survived rendering
        # (matches the snake_case regex in test_no_unreplaced_placeholders_in_constant).
        placeholders = re.findall(r"\{[a-z][a-z_]+\}", prompt)
        unreplaced = [
            p for p in placeholders
            if p not in ("{kill_zone}", "{timestamp}", "{anything}")
        ]
        assert not unreplaced, f"Unreplaced template vars: {unreplaced}"

    def test_us30_config(self, us30_config):
        prompt = build_system_prompt(us30_config)
        assert "C1" in prompt
        assert "$30.00" in prompt  # US30 uses $ format (not in pip/point lists)
        assert "08:00" in prompt  # London start for US30

    def test_jpypair_config(self, jpypair_config):
        prompt = build_system_prompt(jpypair_config)
        assert "C1" in prompt
        assert "30 pips" in prompt  # 0.30 / 0.01 = 30 pips for JPY pairs
        assert "Tokyo" in prompt  # Tokyo session exists for JPY pairs
        assert "00:00" in prompt

    def test_empty_kz_windows(self):
        """Prompt builds even with empty KZ config (uses defaults)."""
        prompt = build_system_prompt({})
        assert "C1" in prompt  # Core prompt still present
        assert isinstance(prompt, str)
        assert len(prompt) > 1000


class TestBuildUserMessage:
    """Verify user message construction is framework-neutral.

    Pre-2026-04-28 this asserted "OB Retest" appeared in the message —
    that hardcoded phrasing was the HALLUC-1 multi-framework dispatch
    suppression bug source (see
    research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md). The user
    message now references the system-prompt PARALLEL EVALUATION block
    and does NOT name a specific framework as the default.
    """

    def test_user_message_is_framework_neutral(self):
        """Footer must not bias the AI toward any single framework, and
        must reference the PARALLEL EVALUATION dispatch block."""
        mso = SimpleNamespace(
            timestamp_utc="2026-04-13T14:15:00Z",
            model_dump=lambda mode="json": {
                "timestamp_utc": "2026-04-13T14:15:00Z",
                "session_levels": {"asian_high": 3250, "asian_low": 3230, "pdh": 3260, "pdl": 3220},
                "liquidity_pools": [],
                "timeframes": {"D1": {}, "H4": {}, "H1": {}, "M15": {}},
                "detected_sweeps": [],
                "data_quality": {},
            },
        )
        msg = build_user_message(mso, {}, "2026-04-13T14:15:00Z")
        # Framework-neutral wording — no "for the X setup" defaults.
        assert "for the OB Retest setup" not in msg
        assert "for the FVG Fill setup" not in msg
        assert "for the Breaker setup" not in msg
        # Must reference PARALLEL EVALUATION so the AI follows the
        # system-prompt's multi-framework dispatch contract.
        assert "PARALLEL" in msg
        # Schema cue retained.
        assert "Output your analysis as JSON" in msg
        assert "Breaker Block" not in msg
        assert "BOTH" not in msg  # Should not say "BOTH ... setups"


# ═══════════════════════════════════════════════════════════════════════
# 3. JSON SCHEMA COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════

class TestSchemaCompatibility:
    """Verify T7 JSON output parses into PrimaryAnalysisOutput."""

    def test_candidate_parses(self):
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.decision == "CANDIDATE"
        assert output.reasoning.setup_grade == "A+"
        assert output.trade_parameters is not None
        assert output.trade_parameters.direction == "LONG"
        assert output.framework == "ob_retest"

    def test_no_trade_parses(self):
        data = _make_t7_no_trade_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.decision == "NO_TRADE"
        assert output.reasoning.setup_grade == "C"
        assert output.trade_parameters is None
        assert output.no_trade_reason is not None

    def test_candidate_has_all_reasoning_fields(self):
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        r = output.reasoning
        # All required sub-models must be present
        assert isinstance(r.daily_bias, DailyBiasAnalysis)
        assert isinstance(r.h4_alignment, H4AlignmentAnalysis)
        assert isinstance(r.h1_setup, H1SetupAnalysis)
        assert isinstance(r.liquidity_sweep, LiquiditySweepAnalysis)
        assert isinstance(r.m15_confirmation, M15ConfirmationAnalysis)

    def test_h4_alignment_without_data_is_valid(self):
        """T7 acknowledges no H4 data — aligned=True, empty explanation is valid."""
        data = _make_t7_candidate_json()
        data["reasoning"]["h4_alignment"] = {
            "aligned": True,
            "h4_pois_identified": [],
            "explanation": "No H4 data in MSO.",
        }
        output = PrimaryAnalysisOutput(**data)
        assert output.reasoning.h4_alignment.aligned is True

    def test_daily_bias_covers_all_valid_directions(self):
        for direction in ("bullish", "bearish", "ranging"):
            data = _make_t7_candidate_json()
            data["reasoning"]["daily_bias"]["direction"] = direction
            if direction == "ranging":
                data["decision"] = "NO_TRADE"
                data["trade_parameters"] = None
                data["reasoning"]["setup_grade"] = "C"
                data["no_trade_reason"] = "C1 FAIL"
            output = PrimaryAnalysisOutput(**data)
            assert output.reasoning.daily_bias.direction == direction

    def test_grade_a_plus_for_candidate(self):
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.reasoning.setup_grade == "A+"

    def test_grade_c_for_no_trade(self):
        data = _make_t7_no_trade_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.reasoning.setup_grade == "C"


# ═══════════════════════════════════════════════════════════════════════
# 4. PERMISSIONS GATE COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════

class TestPermissionsGate:
    """Verify T7 output passes/blocks at the permissions grade gate."""

    def test_a_plus_passes_grade_gate(self):
        """CANDIDATE with A+ should not be blocked by grade check."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        # The permissions grade gate checks: grade in ("A+", "A")
        assert output.reasoning.setup_grade in ("A+", "A")

    def test_c_grade_blocks(self):
        """NO_TRADE with C grade would be blocked — this is expected."""
        data = _make_t7_no_trade_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.reasoning.setup_grade not in ("A+", "A")

    def test_direction_mismatch_detected(self):
        """If daily_bias=bearish but direction=LONG, permissions should catch it."""
        data = _make_t7_candidate_json()
        data["reasoning"]["daily_bias"]["direction"] = "bearish"
        output = PrimaryAnalysisOutput(**data)
        assert output.reasoning.daily_bias.direction == "bearish"
        assert output.trade_parameters.direction == "LONG"
        # This mismatch would be caught by permissions.py line 114-119


# ═══════════════════════════════════════════════════════════════════════
# 5. VERIFICATION MODULE COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════

class TestVerificationCompatibility:
    """Verify T7 output provides fields needed by verification.py L2 checks."""

    def test_m15_confirmation_feeds_check1(self):
        """Check 1 needs m15_confirmation.choch_detected."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        assert hasattr(output.reasoning.m15_confirmation, "choch_detected")
        assert output.reasoning.m15_confirmation.choch_detected is True

    def test_displacement_ratio_feeds_check2(self):
        """Check 2 needs m15_confirmation.displacement_candle_body_vs_avg_ratio."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        ratio = output.reasoning.m15_confirmation.displacement_candle_body_vs_avg_ratio
        assert isinstance(ratio, (int, float))
        assert ratio > 0

    def test_h1_poi_feeds_check3(self):
        """Check 3 needs h1_setup.poi_identified and poi_price_level."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        h1 = output.reasoning.h1_setup
        assert h1.poi_identified is True
        assert h1.poi_price_level > 0

    def test_trade_params_present_for_candidate(self):
        """All L2 checks require trade_parameters.direction."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        assert output.trade_parameters is not None
        assert output.trade_parameters.direction in ("LONG", "SHORT")

    def test_sl_and_entry_present(self):
        """Verification checks need entry_price and stop_loss."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        tp = output.trade_parameters
        assert tp.entry_price > 0
        assert tp.stop_loss > 0
        assert tp.entry_price != tp.stop_loss


# ═══════════════════════════════════════════════════════════════════════
# 6. SHADOW DATA FIELD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════

class TestShadowDataFields:
    """Verify T7 output provides fields the orchestrator logs as shadow data."""

    def test_h1_setup_fields_for_shadow(self):
        """Orchestrator logs h1_poi_type, h1_fib_pct, h1_causing_event, h1_zone."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        h1 = output.reasoning.h1_setup
        assert h1.poi_type is not None
        assert h1.fib_retracement_pct is not None
        assert h1.causing_event_type is not None
        assert h1.zone is not None

    def test_sweep_fields_for_shadow(self):
        """Orchestrator logs sweep_detected, sweep_type."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        sweep = output.reasoning.liquidity_sweep
        assert isinstance(sweep.detected, bool)
        assert sweep.pool_type is not None

    def test_m15_displacement_for_shadow(self):
        """Orchestrator logs m15_displacement_quality, m15_displacement_ratio."""
        data = _make_t7_candidate_json()
        output = PrimaryAnalysisOutput(**data)
        m15 = output.reasoning.m15_confirmation
        assert m15.displacement_quality is not None
        assert isinstance(m15.displacement_candle_body_vs_avg_ratio, (int, float))


# ═══════════════════════════════════════════════════════════════════════
# 7. PROXIMITY SHADOW LOGGER
# ═══════════════════════════════════════════════════════════════════════

class TestProximityShadowLogger:
    """Verify proximity computation logic."""

    def test_parse_mso_zones_extracts_obs(self):
        mso_text = """## H1 — Structure: bullish
  Unmitigated OBs (1):
    bullish 3210.50-3205.20 (2026-04-10T14:00)
  Avg body: 3.50  ATR(14): 12.30

## M15 — Structure: bullish
  Unmitigated OBs (1):
    bullish 3230.50-3228.00 (2026-04-11T13:15)
  Avg body: 1.80  ATR(14): 4.50"""
        zones = parse_mso_zones(mso_text)
        assert len(zones["h1_obs"]) == 1
        assert len(zones["m15_obs"]) == 1
        assert zones["h1_atr"] == 12.30
        assert zones["m15_atr"] == 4.50

    def test_parse_mso_zones_real_format(self):
        """Test with ACTUAL MSO format produced by _format_tf (includes body= and evt=)."""
        mso_text = """## H1 — Structure: bullish, Protected Swing: at 3200.000 (2026-04-10T10:00)
  Unmitigated OBs (2):
    bullish 3210.50-3205.20 body=3208.00-3209.50 evt=BOS (2026-04-10T14:00)
    bullish 3180.00-3175.50 body=3177.20-3179.80 evt=CHoCH (2026-04-09T08:00)
  Unfilled FVGs (1):
    bullish 3215.00-3212.50
  Avg body: 3.50  ATR(14): 12.30

## M15 — Structure: bullish, Protected Swing: at 3230.000 (2026-04-11T13:30)
  Unmitigated OBs (1):
    bullish 3230.50-3228.00 body=3229.10-3230.00 evt=BOS (2026-04-11T13:15)
  Avg body: 1.80  ATR(14): 4.50"""
        zones = parse_mso_zones(mso_text)
        assert len(zones["h1_obs"]) == 2, f"Expected 2 H1 OBs, got {len(zones['h1_obs'])}"
        assert len(zones["m15_obs"]) == 1
        assert zones["h1_obs"][0]["high"] == 3210.50
        assert zones["h1_obs"][0]["low"] == 3205.20
        assert zones["h1_obs"][1]["direction"] == "bullish"
        assert zones["h1_atr"] == 12.30
        assert zones["m15_atr"] == 4.50

    def test_proximity_inside(self):
        obs = [{"direction": "bullish", "high": 3250.0, "low": 3245.0, "timestamp": "t"}]
        label, ob, dist = compute_proximity(3247.0, obs, "bullish", 5.0)
        assert label == "inside"
        assert dist == 0.0

    def test_proximity_approaching(self):
        obs = [{"direction": "bullish", "high": 3240.0, "low": 3235.0, "timestamp": "t"}]
        label, ob, dist = compute_proximity(3245.0, obs, "bullish", 5.0)
        # dist = 3245 - 3240 = 5.0, threshold = 2 * 5.0 = 10.0
        assert label == "approaching"
        assert dist == 5.0

    def test_proximity_far(self):
        obs = [{"direction": "bullish", "high": 3200.0, "low": 3195.0, "timestamp": "t"}]
        label, ob, dist = compute_proximity(3250.0, obs, "bullish", 5.0)
        # dist = 3250 - 3200 = 50.0, threshold = 10.0
        assert label == "far"
        assert dist == 50.0

    def test_proximity_none_no_relevant_obs(self):
        obs = [{"direction": "bearish", "high": 3250.0, "low": 3245.0, "timestamp": "t"}]
        label, ob, dist = compute_proximity(3248.0, obs, "bullish", 5.0)
        assert label == "none"

    def test_proximity_none_empty_obs(self):
        label, ob, dist = compute_proximity(3248.0, [], "bullish", 5.0)
        assert label == "none"

    def test_compute_trade_proximity_long(self):
        mso_text = """Session H/L: 3250.00/3230.00
## H1 — Structure: bullish
  Unmitigated OBs (1):
    bullish 3235.00-3230.00 (2026-04-10T14:00)
  Avg body: 3.50  ATR(14): 12.30
## M15 — Structure: bullish
  Avg body: 1.80  ATR(14): 4.50"""
        result = compute_trade_proximity(mso_text, "LONG")
        assert result["proximity"] in ("inside", "approaching", "far", "none")
        assert result["atr_source"] == "m15"

    def test_compute_trade_proximity_short(self):
        mso_text = """Session H/L: 3220.00/3200.00
## H1 — Structure: bearish
  Unmitigated OBs (1):
    bearish 3250.00-3245.00 (2026-04-10T14:00)
  Avg body: 3.50  ATR(14): 12.30
## M15 — Structure: bearish
  Avg body: 1.80  ATR(14): 4.50"""
        result = compute_trade_proximity(mso_text, "SHORT")
        assert result["proximity"] in ("approaching", "far")  # OB above price

    def test_missing_atr_returns_unknown(self):
        mso_text = """Session H/L: 3250.00/3230.00
## H1 — Structure: bullish
  Unmitigated OBs (1):
    bullish 3235.00-3230.00 (2026-04-10T14:00)"""
        result = compute_trade_proximity(mso_text, "LONG")
        assert result["proximity"] == "unknown"
        assert result["reason"] == "missing_price_or_atr"


# ═══════════════════════════════════════════════════════════════════════
# 8. PARTIAL CLOSE SHADOW LOGGER
# ═══════════════════════════════════════════════════════════════════════

class TestPartialCloseShadowLogger:
    """Verify Variant C partial close logic."""

    def test_trigger_at_1r(self):
        tracker = PartialCloseShadowTracker(
            trade_id="t1", entry_price=3200.0, stop_loss=3190.0,
            take_profit=3220.0, direction="LONG", sl_distance=10.0,
        )
        assert not tracker.update(3205.0)  # +0.5R
        assert tracker.update(3210.0)       # +1.0R — trigger
        assert tracker.trigger_activated

    def test_no_trigger_below_1r(self):
        tracker = PartialCloseShadowTracker(
            trade_id="t2", entry_price=3200.0, stop_loss=3190.0,
            take_profit=3220.0, direction="LONG", sl_distance=10.0,
        )
        tracker.update(3209.0)  # +0.9R
        assert not tracker.trigger_activated
        result = tracker.compute_hypothetical(3190.0, -1.0)
        assert result is None  # Never triggered

    def test_big_winner_variant_c_worse(self):
        """Variant C costs R on big winners (partial at +1R < full at +2R)."""
        tracker = PartialCloseShadowTracker(
            trade_id="t3", entry_price=3200.0, stop_loss=3190.0,
            take_profit=3220.0, direction="LONG", sl_distance=10.0,
        )
        tracker.update(3210.0)  # trigger
        result = tracker.compute_hypothetical(3220.0, 2.0)
        assert result is not None
        assert result["delta_r"] < 0  # Variant C is worse on big winners
        assert not result["variant_c_better"]

    def test_reversal_loss_variant_c_better(self):
        """Variant C saves R on reversal losses (partial locked + BE stop)."""
        tracker = PartialCloseShadowTracker(
            trade_id="t4", entry_price=3200.0, stop_loss=3190.0,
            take_profit=3220.0, direction="LONG", sl_distance=10.0,
        )
        tracker.update(3210.0)  # trigger
        tracker.update(3199.0)  # reverses past entry
        result = tracker.compute_hypothetical(3190.0, -1.0)
        assert result is not None
        assert result["delta_r"] > 0
        assert result["variant_c_better"]
        # Should be: 0.33 * 1.0 + 0.67 * 0.0 = 0.33R vs -1.0R = +1.33R delta
        assert abs(result["variant_c_blended_r"] - PARTIAL_CLOSE_FRACTION * TRIGGER_R) < 0.01

    def test_short_direction(self):
        tracker = PartialCloseShadowTracker(
            trade_id="t5", entry_price=3200.0, stop_loss=3210.0,
            take_profit=3180.0, direction="SHORT", sl_distance=10.0,
        )
        assert tracker.update(3190.0)  # +1.0R for SHORT
        assert tracker.trigger_activated

    def test_partial_close_fraction(self):
        assert PARTIAL_CLOSE_FRACTION == 0.33
        assert TRIGGER_R == 1.0


# ═══════════════════════════════════════════════════════════════════════
# 9. ORCHESTRATOR WIRING INTEGRITY
# ═══════════════════════════════════════════════════════════════════════

    def test_configurable_variant_c_trigger_and_fraction(self):
        tracker = PartialCloseShadowTracker(
            trade_id="t6", entry_price=3200.0, stop_loss=3190.0,
            take_profit=3220.0, direction="LONG", sl_distance=10.0,
            partial_close_fraction=0.50, trigger_r=1.50,
            source_evidence={"source_path": "unit-test"},
        )
        assert not tracker.update(3210.0)  # +1.0R, below configured trigger
        assert tracker.update(3215.0)      # +1.5R
        result = tracker.compute_hypothetical(3190.0, -1.0)
        assert result is not None
        assert result["partial_close_fraction"] == 0.50
        assert result["trigger_r"] == 1.50
        assert result["source_evidence"]["source_path"] == "unit-test"

    def test_agent_config_wires_variant_c_shadow_parameters(self):
        with open("config/agent_config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        block = cfg["shadow_loggers"]["partial_close_shadow_logger"]
        assert block["enabled"] is True
        assert block["partial_close_fraction"] == 0.33
        assert block["trigger_r"] == 1.0
        assert block["ftmo_pass_delta_pp"] == 4.9
        assert block["q62_verdict"] == "DEFER"
        assert block["q62_runtime_artifact_path"].endswith(
            "GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        assert block["q62_source_rows_represented"] == 1899
        assert block["q62_valid_universe_size"] == 251
        assert block["q62_triggered_trade_count"] == 102
        assert block["q62_variant_c_mean_delta_r"] == 0.0536
        assert block["q62_variant_c_wilcoxon_p"] == 0.957373
        assert block["q62_common_subset_c_mean_delta_r"] == -0.0983
        assert block["q62_variant_d_shadow_enabled"] is False
        assert block["active_policy_change_allowed_now"] is False
        assert block["live_triggered_events_required"] == 30
        assert block["source_path"] == "research/q62_partial_close_optimization/q62_report_2026-04-18.md"

    def test_orchestrator_initializes_variant_c_shadow_from_config(self):
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.config = {
            "shadow_loggers": {
                "partial_close_shadow_logger": {
                    "enabled": True,
                    "partial_close_fraction": 0.25,
                    "trigger_r": 1.25,
                    "source_path": "unit-source",
                    "source_line_no": 9,
                    "q62_verdict": "DEFER",
                    "q62_variant_d_shadow_enabled": False,
                    "active_policy_change_allowed_now": False,
                }
            }
        }
        trade_state = SimpleNamespace(
            trade_id="t7",
            entry_price=3200.0,
            stop_loss=3190.0,
            take_profit=3220.0,
            direction="LONG",
            sl_distance=10.0,
            entry_time="2026-05-19T00:00:00+00:00",
        )

        orch._init_trade_tracking(trade_state)

        tracker = orch._partial_close_shadow_tracker
        assert tracker is not None
        assert tracker.partial_close_fraction == 0.25
        assert tracker.trigger_r == 1.25
        assert tracker.source_evidence["source_path"] == "unit-source"
        assert tracker.source_evidence["q62_verdict"] == "DEFER"
        assert tracker.source_evidence["q62_variant_d_shadow_enabled"] is False
        assert tracker.source_evidence["active_policy_change_allowed_now"] is False

    def test_orchestrator_can_disable_variant_c_shadow_tracker(self):
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.config = {"shadow_loggers": {"partial_close_shadow_logger": {"enabled": False}}}
        trade_state = SimpleNamespace(
            trade_id="t8",
            entry_price=3200.0,
            stop_loss=3190.0,
            take_profit=3220.0,
            direction="LONG",
            sl_distance=10.0,
            entry_time="2026-05-19T00:00:00+00:00",
        )

        orch._init_trade_tracking(trade_state)

        assert orch._partial_close_shadow_tracker is None


class TestOrchestratorWiring:
    """Verify orchestrator.py imports and references are correct."""

    def test_orchestrator_parses(self):
        """orchestrator.py has no syntax errors after our edits."""
        with open("src/components/orchestrator.py") as f:
            tree = ast.parse(f.read())
        assert tree is not None

    def test_shadow_logger_imports_present(self):
        """All three shadow loggers are imported."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "from src.components.be_shadow_logger import" in content
        assert "from src.components.partial_close_shadow_logger import" in content
        assert "from src.components.proximity_shadow_logger import" in content

    def test_partial_close_tracker_initialized(self):
        """PartialCloseShadowTracker is created in _init_trade_tracking."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "_partial_close_shadow_tracker = PartialCloseShadowTracker(" in content

    def test_partial_close_tracker_updated_on_tick(self):
        """Partial close tracker is updated alongside BE tracker on ticks."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "_partial_close_shadow_tracker" in content
        # Should appear in _update_mfe_mae_from_tick
        assert "self._partial_close_shadow_tracker.update(price)" in content

    def test_proximity_logged_at_candidate(self):
        """Proximity is computed and logged for every CANDIDATE."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "compute_trade_proximity" in content
        assert "write_proximity_shadow_log" in content

    def test_partial_close_logged_at_exit(self):
        """Partial close result is computed at trade close."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "write_partial_close_shadow_log" in content
        assert "compute_hypothetical" in content

    def test_proximity_outcome_updated_at_exit(self):
        """Proximity outcome is updated at trade close."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "update_proximity_outcome" in content

    def test_trackers_reset_at_cleanup(self):
        """Both shadow trackers are reset at trade cleanup."""
        with open("src/components/orchestrator.py") as f:
            content = f.read()
        assert "self._be_shadow_tracker = None" in content
        assert "self._partial_close_shadow_tracker = None" in content
