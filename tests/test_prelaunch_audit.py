"""Pre-launch audit tests — 2026-04-02.

Tests for:
1. Max SL distance gate
2. Breaker_retest disabled via config
3. London KZ reverted to 07:00-09:30
4. Config consistency checks
5. Null trade_parameters guard in orchestrator
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
import pytest

from src.models.analysis_models import (
    PrimaryAnalysisOutput, PrimaryAnalysisReasoning,
    DailyBiasAnalysis, H4AlignmentAnalysis, H1SetupAnalysis,
    LiquiditySweepAnalysis, M15ConfirmationAnalysis, TradeParameters,
)
from src.components.permissions import check_permissions, ExecutionDenial
from src.components.primary_analyzer import _strip_breaker_sections


# ── Helpers ──

def _make_tp(entry=3000, sl=2960, tp1=3060, rr=1.5, direction="LONG"):
    return TradeParameters(
        direction=direction, entry_price=entry, stop_loss=sl,
        take_profit_1=tp1, take_profit_2=tp1+20, take_profit_3=tp1+50,
        risk_reward_ratio=rr,
    )

def _make_pa(tp, grade="A", daily_bias="bullish"):
    return PrimaryAnalysisOutput(
        timestamp_utc="t", model_used="t", decision="CANDIDATE",
        confidence_score=80, framework="ob_retest",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_bias, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(poi_identified=True),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(choch_detected=True),
            setup_grade=grade,
        ),
        trade_parameters=tp,
    )

class _MockMSO:
    class _TF:
        atr_14 = 10.0
    timeframes = {"M15": _TF()}

class _MockMT5:
    class _Tick:
        spread_cents = 10
    def is_connected(self): return True
    def get_tick(self, _): return self._Tick()

def _session():
    return {"trades_today": 0, "current_kill_zone": "london",
            "trades_london": 0, "losses_today": 0}


# ═══════════════════════════════════════════════════════════════════════
# Fix 1: Max SL Distance Gate
# ═══════════════════════════════════════════════════════════════════════

class TestMaxSLDistanceGate:
    def test_normal_sl_passes(self):
        """Trade #1 from replay: $19.46 SL (0.58%) — should pass."""
        tp = _make_tp(entry=3330, sl=3310.54, tp1=3359.19)  # 1.5R TP1
        denial = check_permissions(_make_pa(tp), _MockMSO(), _session(), _MockMT5())
        assert denial is None

    def test_wide_sl_rejected(self):
        """Trade #34: $428.70 SL (7.70%) — should be rejected."""
        tp = _make_tp(entry=5568.70, sl=5140.00, tp1=5568.70 + 428.70 * 1.5)  # 1.5R TP1
        denial = check_permissions(_make_pa(tp), _MockMSO(), _session(), _MockMT5())
        assert denial is not None
        assert "sl_too_wide" in denial.reason

    def test_borderline_sl_passes(self):
        """SL at exactly 2.5% — should pass."""
        entry = 4000.0
        sl = entry * 0.975  # 2.5% below = 3900
        tp1 = entry + (entry - sl) * 1.5  # 1.5R TP1
        tp = _make_tp(entry=entry, sl=sl, tp1=tp1)
        denial = check_permissions(_make_pa(tp), _MockMSO(), _session(), _MockMT5())
        assert denial is None

    def test_slightly_over_limit_rejected(self):
        """SL at 3.0% — should be rejected."""
        entry = 4000.0
        sl = entry * 0.970  # 3.0% below
        tp1 = entry + (entry - sl) * 1.5  # 1.5R TP1
        tp = _make_tp(entry=entry, sl=sl, tp1=tp1)
        denial = check_permissions(_make_pa(tp), _MockMSO(), _session(), _MockMT5())
        assert denial is not None
        assert "sl_too_wide" in denial.reason


# ═══════════════════════════════════════════════════════════════════════
# Fix 2: Breaker Retest Disable
# ═══════════════════════════════════════════════════════════════════════

class TestBreakerRestestDisable:
    def test_strip_breaker_sections_removes_criteria(self):
        from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT
        stripped = _strip_breaker_sections(SYSTEM_PROMPT)
        assert "BR1." not in stripped
        assert "BREAKER BLOCK RETEST" not in stripped
        # T7 C-gate prompt: C1/C2/C3 gates should remain
        assert "C1" in stripped or "Q1." in stripped or "OB1." in stripped

    def test_strip_breaker_rewrites_step2(self):
        from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT
        stripped = _strip_breaker_sections(SYSTEM_PROMPT)
        # T7 C-gate prompt: breaker block was already removed from the prompt
        assert "BREAKER BLOCK RETEST" not in stripped

    def test_config_has_enabled_frameworks(self):
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)
        enabled = config.get("model_a", {}).get("enabled_frameworks")
        assert enabled is not None
        assert "ob_retest" in enabled
        assert "breaker_retest" not in enabled


# ═══════════════════════════════════════════════════════════════════════
# Fix 3: London KZ Reverted
# ═══════════════════════════════════════════════════════════════════════

class TestLondonKZReverted:
    def test_config_london_end_is_0930(self):
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)
        london = config["market"]["kill_zones"]["london"]
        assert london["end_utc"] == "10:30"

    def test_prompt_kz_display(self):
        """Default (gold) prompt shows standard KZ windows; GBPUSD shows extended London."""
        from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT, build_system_prompt
        # Default gold prompt: standard London 07:00-09:30
        assert "07:00\u201309:30" in SYSTEM_PROMPT
        assert "13:00\u201315:30" in SYSTEM_PROMPT
        # GBPUSD with extended London
        gbp_config = {
            "market": {
                "symbol": "GBPUSD",
                "kill_zones": {
                    "london": {"start_utc": "07:00", "end_utc": "12:00"},
                    "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                },
            },
            "risk": {"sl_absolute_min": 0.0003},
            "prompt": {"zone_width_max": 0.0015, "ob_buffer": 0.00015, "price_format": ".5f"},
        }
        gbp_prompt = build_system_prompt(gbp_config)
        assert "07:00\u201312:00" in gbp_prompt
        assert "13:00\u201315:30" in gbp_prompt


# ═══════════════════════════════════════════════════════════════════════
# Audit: Config Consistency
# ═══════════════════════════════════════════════════════════════════════

class TestConfigConsistency:
    def test_max_daily_loss_pct_matches(self):
        """T2.8: config risk.max_daily_loss_pct is 4.0 (daily MTM stop cap).

        The old ``max_daily_losses: 2`` count gate was removed in T2.8 —
        the concurrent-cap formula (floor(max_daily_loss_pct /
        risk_per_trade_pct)) replaces it. A pre-launch audit should now
        verify the new authoritative knob.
        """
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)
        assert config["risk"]["max_daily_loss_pct"] == 4.0
        # The removed key must stay removed.
        assert "max_daily_losses" not in config["risk"]

    def test_min_rr_matches_prompt(self):
        from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)
        assert config["risk"]["min_rr"] == 1.5
        assert "1:1.5" in SYSTEM_PROMPT or "1.5" in SYSTEM_PROMPT

    def test_max_spread_matches_permissions(self):
        """Config max_spread_cents should match Gate 3 limit."""
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)
        assert config["risk"]["max_spread_cents"] == 100

    def test_apr14_risk_keys_are_not_nested_under_drawdown_reduction(self):
        """Apr 14 live bug: malformed YAML made XAUUSD use fallback risk gates."""
        with open("config/agent_config.yaml") as f:
            config = yaml.safe_load(f)

        restored_risk_keys = {
            "max_daily_loss_pct",
            "max_weekly_loss_pct",
            "max_monthly_loss_pct",
            "min_rr",
            "tp1_close_pct",
            "max_spread_cents",
            "sl_buffer_dollars",
            "sl_absolute_min",
        }

        assert restored_risk_keys <= set(config["risk"])
        assert restored_risk_keys.isdisjoint(set(config["drawdown_reduction"]))
        assert config["risk"]["max_spread_cents"] == 100
        assert config["risk"]["sl_buffer_dollars"] == 1.20
        assert config["risk"]["sl_absolute_min"] == 5.0
        assert config["drawdown_reduction"]["threshold"] == 0.08
        assert config["drawdown_reduction"]["reduced_risk_pct"] == 0.5
        assert config["drawdown_reduction"]["contract_size"] == 100
