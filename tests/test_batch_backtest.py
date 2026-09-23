"""Tests for batch backtesting — prompt building, processing, safety checks."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.components.primary_analyzer import PrimaryAnalyzer, _normalize_pa_fields
from src.models.analysis_models import PrimaryAnalysisOutput
from src.utils.validation import strip_json_fences


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def config():
    return {
        "ai": {
            "primary_model": "claude-sonnet-4-20250514",
            "api_timeout_seconds": 30,
            "max_api_retries": 1,
        },
        "data": {
            "lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672},
            "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
            "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0},
        },
        "model_a": {"equal_level_tolerance": 2.50},
    }


@pytest.fixture
def kb(tmp_path):
    from src.components.knowledge_base import KnowledgeBase
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    return KnowledgeBase(base_path=str(tmp_path))


# ═══════════════════════════════════════════════════════════════════════
# build_prompt()
# ═══════════════════════════════════════════════════════════════════════


class TestBuildPrompt:
    """Test build_prompt by patching the prompt module functions."""

    def test_returns_valid_structure(self, config, kb):
        with patch("src.llm_backend.Anthropic"):
            analyzer = PrimaryAnalyzer(config, kb)

        mso = MagicMock()

        with patch("src.components.primary_analyzer.primary_analyzer_prompt") as mock_pap:
            mock_pap.SYSTEM_PROMPT = "System prompt text"
            mock_pap.build_static_context.return_value = "static context"
            mock_pap.build_user_message.return_value = "user message"

            result = analyzer.build_prompt(mso, "2025-04-01T07:15:00Z")

        assert "system" in result
        assert "user_message" in result
        assert "model" in result
        assert "max_tokens" in result
        assert "temperature" in result
        assert isinstance(result["system"], list)
        assert isinstance(result["user_message"], str)
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["max_tokens"] == 2000
        assert result["temperature"] == 0

    def test_system_has_cache_control(self, config, kb):
        """Session 43 (commit 080f703, CEO-approved): static system block
        was extended to 1h cache TTL (was default 5m) to amortize 2× cache-
        write cost across the 7-instrument fleet at M15 cadence. Wire
        format matches ``cache_helper.build_cache_control(ttl="1h")``.
        """
        with patch("src.llm_backend.Anthropic"):
            analyzer = PrimaryAnalyzer(config, kb)

        mso = MagicMock()

        with patch("src.components.primary_analyzer.primary_analyzer_prompt") as mock_pap:
            mock_pap.SYSTEM_PROMPT = "System prompt"
            mock_pap.build_static_context.return_value = "ctx"
            mock_pap.build_user_message.return_value = "msg"

            result = analyzer.build_prompt(mso, "2025-04-01T07:15:00Z")

        system = result["system"]
        assert len(system) >= 1
        assert system[0].get("cache_control") == {"type": "ephemeral", "ttl": "1h"}

    def test_session_cache_reset(self, config, kb):
        with patch("src.llm_backend.Anthropic"):
            analyzer = PrimaryAnalyzer(config, kb)

        mso = MagicMock()

        with patch("src.components.primary_analyzer.primary_analyzer_prompt") as mock_pap:
            mock_pap.SYSTEM_PROMPT = "System prompt"
            mock_pap.build_static_context.return_value = "ctx"
            mock_pap.build_user_message.return_value = "msg"

            p1 = analyzer.build_prompt(mso, "2025-04-01T07:15:00Z")
            sys1 = id(p1["system"])

            p2 = analyzer.build_prompt(mso, "2025-04-01T07:30:00Z")
            assert id(p2["system"]) == sys1  # same cached object

            analyzer.reset_session_cache()
            p3 = analyzer.build_prompt(mso, "2025-04-01T07:45:00Z")
            assert id(p3["system"]) != sys1  # new object after reset


# ═══════════════════════════════════════════════════════════════════════
# strip_json_fences (enhanced)
# ═══════════════════════════════════════════════════════════════════════


class TestStripJsonFencesEnhanced:
    def test_preamble_before_fences(self):
        """CLI mode: preamble text before ```json block."""
        text = 'Looking at the data, here is my analysis:\n\n```json\n{"decision": "NO_TRADE"}\n```'
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed["decision"] == "NO_TRADE"

    def test_bare_json_in_text(self):
        """JSON embedded in prose without fences."""
        text = 'Here is my analysis:\n\n{"decision": "NO_TRADE", "reason": "test"}\n\nThank you.'
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed["decision"] == "NO_TRADE"

    def test_clean_json(self):
        """Clean JSON with no wrapping."""
        text = '{"decision": "CANDIDATE", "confidence_score": 85}'
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed["decision"] == "CANDIDATE"

    def test_standard_fences(self):
        """Standard ```json ... ``` fences."""
        text = '```json\n{"decision": "WAIT"}\n```'
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed["decision"] == "WAIT"

    def test_first_valid_json_before_extra_object(self):
        """Recover the first valid object when the model appends extra JSON."""
        text = '{"decision": "NO_TRADE"}\n\n{"note": "extra diagnostic object"}'
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed == {"decision": "NO_TRADE"}

    def test_first_valid_json_ignores_non_json_braces_and_string_braces(self):
        """Preamble braces and braces inside strings must not break extraction."""
        text = (
            'Analysis note {not json}\n'
            '{"decision": "NO_TRADE", "reason": "literal } brace in text"}\n'
            '{"note": "extra diagnostic object"}'
        )
        result = strip_json_fences(text)
        parsed = json.loads(result)
        assert parsed["decision"] == "NO_TRADE"
        assert parsed["reason"] == "literal } brace in text"


# ═══════════════════════════════════════════════════════════════════════
# One-trade-per-day processing logic
# ═══════════════════════════════════════════════════════════════════════


class TestOneTradePerWindow:
    def test_no_trade_all_candles(self, tmp_path):
        """When all candles are NO_TRADE, no trade is taken."""
        from scripts.batch_backtest import process_results

        # Build 3 prompts for the same day (London window)
        prompts = [
            {"custom_id": "2025-04-01_london_0715", "date": "2025-04-01",
             "candle_time": "2025-04-01T07:15:00+00:00", "kill_zone": "london"},
            {"custom_id": "2025-04-01_london_0730", "date": "2025-04-01",
             "candle_time": "2025-04-01T07:30:00+00:00", "kill_zone": "london"},
            {"custom_id": "2025-04-01_london_0745", "date": "2025-04-01",
             "candle_time": "2025-04-01T07:45:00+00:00", "kill_zone": "london"},
        ]

        # All NO_TRADE
        no_trade_json = json.dumps({
            "timestamp_utc": "2025-04-01T07:15:00Z",
            "model_used": "test",
            "decision": "NO_TRADE",
            "confidence_score": 0,
            "framework": "none",
            "kill_zone": "london",
            "reasoning": {
                "daily_bias": {"direction": "bullish", "confidence": "low"},
                "h4_alignment": {"aligned": False},
                "h1_setup": {"poi_identified": False},
                "liquidity_sweep": {"detected": False},
                "m15_confirmation": {"choch_detected": False},
                "setup_grade": "C",
            },
            "no_trade_reason": "test",
        })

        results = {
            "2025-04-01_london_0715": {"text": no_trade_json, "input_tokens": 100,
                                       "output_tokens": 50, "cache_read": 0, "cache_create": 0,
                                       "status": "succeeded"},
            "2025-04-01_london_0730": {"text": no_trade_json, "input_tokens": 100,
                                       "output_tokens": 50, "cache_read": 0, "cache_create": 0,
                                       "status": "succeeded"},
            "2025-04-01_london_0745": {"text": no_trade_json, "input_tokens": 100,
                                       "output_tokens": 50, "cache_read": 0, "cache_create": 0,
                                       "status": "succeeded"},
        }

        config = {"data": {}, "model_a": {"equal_level_tolerance": 2.50}}
        all_candles = {"M15": [], "H1": [], "H4": [], "D1": []}

        batch_results, batch_cost = process_results(prompts, results, config, all_candles, output_dir=tmp_path)

        assert len(batch_results) == 1
        assert batch_results[0]["trade_taken"] is False
        # All decisions should be NO_TRADE
        assert all(d == "NO_TRADE" for d in batch_results[0]["decisions"])


# ═══════════════════════════════════════════════════════════════════════
# Safety check (batch version mirrors sequential runner)
# ═══════════════════════════════════════════════════════════════════════


class TestBatchSafetyCheck:
    def test_rejects_low_grade(self):
        from scripts.batch_backtest import _safety_check

        pa = MagicMock()
        pa.reasoning.setup_grade = "B"
        pa.trade_parameters = MagicMock()
        mso = MagicMock()

        result = _safety_check(pa, mso)
        assert result is not None
        assert "below_grade" in result

    def test_accepts_grade_a(self):
        from scripts.batch_backtest import _safety_check

        pa = MagicMock()
        pa.reasoning.setup_grade = "A"
        pa.reasoning.daily_bias.direction = "bullish"
        pa.trade_parameters.direction = "LONG"
        pa.trade_parameters.risk_reward_ratio = 3.0
        pa.trade_parameters.entry_price = 3100
        pa.trade_parameters.stop_loss = 3090  # $10 SL

        mso = MagicMock()
        m15_tf = MagicMock()
        m15_tf.atr_14 = 5.0  # SL 10 > 1.5*5 = 7.5 ✓
        mso.timeframes = {"M15": m15_tf}

        result = _safety_check(pa, mso)
        assert result is None  # all checks pass


# ═══════════════════════════════════════════════════════════════════════
# Pre-screen filters
# ═══════════════════════════════════════════════════════════════════════


class TestPrescreen:
    """Test deterministic pre-screening of dates before API calls."""

    @staticmethod
    def _make_mso_mock(d1_dir: str, h4_dir: str):
        """Build a mock MSO with specified D1 and H4 directions."""
        mso = MagicMock()
        d1_tf = MagicMock()
        d1_tf.structure.direction = d1_dir
        h4_tf = MagicMock()
        h4_tf.structure.direction = h4_dir
        mso.timeframes = {"D1": d1_tf, "H4": h4_tf, "H1": MagicMock(), "M15": MagicMock()}
        return mso

    def test_d1_transitional_h4_clear_passes(self):
        """D1 transitional + H4 bullish → passes (AI uses H4+H1 consensus)."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("transitional", "bullish")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is True
            assert reason == ""

    def test_both_d1_h4_unclear_skips(self):
        """Both D1 and H4 unclear → skip (no directional consensus)."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("transitional", "ranging")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is False
            assert "no_direction" in reason

    def test_l1_d1_insufficient_h4_insufficient_skips(self):
        """Both D1 and H4 insufficient_data → skip."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("insufficient_data", "insufficient_data")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is False
            assert "no_direction" in reason

    def test_l2_h4_conflicts_d1_skips(self):
        """Layer 2: D1 bullish + H4 bearish → skip entire date."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("bullish", "bearish")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is False
            assert reason.startswith("L2_")
            assert "conflict" in reason

    def test_d1_clear_h4_transitional_passes(self):
        """D1 bullish + H4 transitional → passes (D1 provides direction)."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("bullish", "transitional")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is True
            assert reason == ""

    def test_d1_bullish_h4_bullish_passes(self):
        """D1 bullish + H4 bullish → passes both layers."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("bullish", "bullish")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is True
            assert reason == ""

    def test_d1_bearish_h4_bearish_passes(self):
        """D1 bearish + H4 bearish → passes both layers."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("bearish", "bearish")

            passed, reason = prescreen_date("2025-01-01", {}, {})
            assert passed is True
            assert reason == ""

    def test_no_prescreen_submits_everything(self):
        """--no-prescreen flag disables filtering — all dates pass."""
        from scripts.batch_backtest import collect_prompts

        with patch("scripts.batch_backtest.replay_kill_zone") as mock_kz, \
             patch("scripts.batch_backtest.replay_london_open") as mock_london, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso, \
             patch("scripts.batch_backtest.PrimaryAnalyzer") as mock_pa_cls, \
             patch("scripts.batch_backtest.KnowledgeBase"):

            # 2 weekdays: Jan 6 (Mon) and Jan 7 (Tue) 2025
            m15_candles = [
                {"time": "2025-01-06T07:15:00Z"},
                {"time": "2025-01-07T07:15:00Z"},
            ]
            all_candles = {"M15": m15_candles, "H1": [], "H4": [], "D1": []}

            # MSO with transitional D1 — would be filtered WITH prescreen
            mso_mock = self._make_mso_mock("transitional", "bullish")
            mock_mso.return_value = mso_mock

            # replay_london_open is used by prescreen_date to get the first candle
            mock_london.return_value = iter([{"timestamp_utc": "2025-01-06T07:15:00Z"}])
            # replay_kill_zone is called once per KZ per date — return fresh iterator each time
            mock_kz.side_effect = lambda *a, **kw: iter([{"timestamp_utc": "2025-01-06T07:15:00Z"}])

            pa_instance = MagicMock()
            pa_instance.build_prompt.return_value = {
                "system": [{"type": "text", "text": "sys"}],
                "user_message": "msg",
                "model": "test",
                "max_tokens": 2000,
                "temperature": 0,
            }
            mock_pa_cls.return_value = pa_instance

            # With prescreen=True, D1 transitional + H4 bullish now passes
            # (H4 provides direction, AI uses H4+H1 consensus via U1)
            test_config_screened = {
                "market": {
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "09:30"},
                        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                    }
                }
            }
            prompts_screened, stats_screened = collect_prompts(
                "2025-01-06", "2025-01-06", test_config_screened, all_candles, prescreen=True,
            )
            assert stats_screened["l1_skip"] == 0
            assert len(prompts_screened) > 0

            # Reset mocks for second call
            mock_kz.side_effect = lambda *a, **kw: iter([{"timestamp_utc": "2025-01-06T07:15:00Z"}])
            pa_instance.reset_session_cache.reset_mock()

            # With prescreen=False, everything should be submitted
            # Pass config with KZ definitions so the loop has something to iterate
            test_config = {
                "market": {
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "09:30"},
                        "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                    }
                }
            }
            prompts_all, stats_all = collect_prompts(
                "2025-01-06", "2025-01-06", test_config, all_candles, prescreen=False,
            )
            assert stats_all["l1_skip"] == 0
            assert stats_all["l2_skip"] == 0
            assert len(prompts_all) > 0

    def test_prescreen_uses_component2_not_api(self):
        """Pre-screen only uses compute_market_state (Component 2), no API calls."""
        from scripts.batch_backtest import prescreen_date

        with patch("scripts.batch_backtest.replay_london_open") as mock_replay, \
             patch("scripts.batch_backtest.compute_market_state") as mock_mso:
            mock_replay.return_value = iter([{"timestamp_utc": "2025-01-01T07:15:00Z"}])
            mock_mso.return_value = self._make_mso_mock("bullish", "bullish")

            passed, _ = prescreen_date("2025-01-01", {}, {})
            assert passed is True
            # compute_market_state called exactly once (for the first candle)
            assert mock_mso.call_count == 1
            # No Anthropic client, no API call — only MSO computation


# ── Kill zone parameterization ─────────────────────────────────────

class TestKillZoneParameterization:
    """Tests for configurable per-instrument KZ windows."""

    def test_replay_kill_zone_candle_count(self):
        """replay_kill_zone yields correct number of M15 candles for given window."""
        from scripts.historical_data_loader import replay_kill_zone
        from unittest.mock import patch

        # Standard London 07:00-09:30 → 10 candles (07:15..09:30)
        with patch("scripts.historical_data_loader.build_raw_data") as mock_build, \
             patch("scripts.historical_data_loader.compute_session_levels", return_value={}):
            mock_build.side_effect = lambda ac, td, ct, sl, tol, **kw: {"timestamp_utc": ct}
            candles = list(replay_kill_zone(
                "2025-01-06", {"M15": []},
                kz_start="07:00", kz_end="09:30",
            ))
            assert len(candles) == 10
            assert candles[0]["timestamp_utc"] == "2025-01-06T07:15:00Z"
            assert candles[-1]["timestamp_utc"] == "2025-01-06T09:30:00Z"

        # Extended London for GBPUSD 07:00-12:00 → 20 candles
        with patch("scripts.historical_data_loader.build_raw_data") as mock_build, \
             patch("scripts.historical_data_loader.compute_session_levels", return_value={}):
            mock_build.side_effect = lambda ac, td, ct, sl, tol, **kw: {"timestamp_utc": ct}
            candles = list(replay_kill_zone(
                "2025-01-06", {"M15": []},
                kz_start="07:00", kz_end="12:00",
            ))
            assert len(candles) == 20
            assert candles[0]["timestamp_utc"] == "2025-01-06T07:15:00Z"
            assert candles[-1]["timestamp_utc"] == "2025-01-06T12:00:00Z"

        # Extended NY 13:00-17:00 → 16 candles
        with patch("scripts.historical_data_loader.build_raw_data") as mock_build, \
             patch("scripts.historical_data_loader.compute_session_levels", return_value={}):
            mock_build.side_effect = lambda ac, td, ct, sl, tol, **kw: {"timestamp_utc": ct}
            candles = list(replay_kill_zone(
                "2025-01-06", {"M15": []},
                kz_start="13:00", kz_end="17:00",
            ))
            assert len(candles) == 16
            assert candles[0]["timestamp_utc"] == "2025-01-06T13:15:00Z"
            assert candles[-1]["timestamp_utc"] == "2025-01-06T17:00:00Z"

    def test_config_kz_overrides_per_instrument(self):
        """Per-instrument KZ overrides in config are applied correctly."""
        import yaml
        with open("config/agent_config.yaml") as f:
            full_config = yaml.safe_load(f)

        instruments = full_config.get("instruments", {})

        # GBPUSD: London extended to 12:00
        gbp = instruments["GBPUSD"]["market"]["kill_zones"]
        assert gbp["london"]["end_utc"] == "12:00"
        assert gbp["london"]["core_end_utc"] == "09:30"

        # XAUUSD: NY extended to 17:00
        xau = instruments["XAUUSD"]["market"]["kill_zones"]
        assert xau["ny"]["end_utc"] == "17:00"
        assert xau["ny"]["core_end_utc"] == "15:30"

        # NAS100: NY extended to 17:00
        nas = instruments["NAS100"]["market"]["kill_zones"]
        assert nas["ny"]["end_utc"] == "17:00"

        # XAGUSD: NY extended to 17:00
        xag = instruments["XAGUSD"]["market"]["kill_zones"]
        assert xag["ny"]["end_utc"] == "17:00"

        # EURUSD: London extended to 12:00
        eur = instruments["EURUSD"]["market"]["kill_zones"]
        assert eur["london"]["end_utc"] == "12:00"

        # Base config London is 10:30 for XAUUSD (expanded KZ)
        base_london = full_config["market"]["kill_zones"]["london"]
        assert base_london["end_utc"] == "10:30"


# ── MFE/MAE tracking ───────────────────────────────────────────────

class TestMFEMAETracking:
    """Tests for MFE/MAE fields in evaluate_hypothetical_outcome."""

    def test_mfe_mae_long_trade_sl(self):
        """LONG: entry=100, SL=95. Candle goes 97-105 then hits SL."""
        from scripts.backtest_runner import evaluate_hypothetical_outcome
        from src.models.analysis_models import TradeParameters

        tp = TradeParameters(
            direction="LONG", entry_price=100.0, stop_loss=95.0,
            take_profit_1=115.0, take_profit_2=120.0, take_profit_3=125.0,
            risk_reward_ratio=3.0,
        )
        candles = [
            {"time": "t0", "open": 100, "close": 103, "high": 105, "low": 97},
            {"time": "t1", "open": 103, "close": 94, "high": 104, "low": 93},  # SL hit
        ]
        result = evaluate_hypothetical_outcome(tp, candles)
        # MFE: (105-100)/5 = 1.0R (first candle high)
        assert result["mfe_r"] == pytest.approx(1.0, abs=0.01)
        # MAE: worst was (100-93)/5 = 1.4R (second candle low after SL triggered)
        assert result["mae_r"] >= 1.0
        assert "mfe_r" in result
        assert "mae_r" in result

    def test_mfe_mae_short_trade(self):
        """SHORT: entry=100, SL=105. Candle goes to 97 low."""
        from scripts.backtest_runner import evaluate_hypothetical_outcome
        from src.models.analysis_models import TradeParameters

        tp = TradeParameters(
            direction="SHORT", entry_price=100.0, stop_loss=105.0,
            take_profit_1=85.0, take_profit_2=80.0, take_profit_3=75.0,
            risk_reward_ratio=3.0,
        )
        candles = [
            {"time": "t0", "open": 100, "close": 98, "high": 101, "low": 97},
            {"time": "t1", "open": 98, "close": 106, "high": 107, "low": 97},  # SL hit
        ]
        result = evaluate_hypothetical_outcome(tp, candles)
        # MFE: (100-97)/5 = 0.6R
        assert result["mfe_r"] == pytest.approx(0.6, abs=0.01)
        assert result["mae_r"] >= 1.0  # SL was hit
        assert result["outcome"] == "LOSS"

    def test_mfe_mae_zero_risk(self):
        """Zero risk edge case."""
        from scripts.backtest_runner import evaluate_hypothetical_outcome
        from src.models.analysis_models import TradeParameters

        tp = TradeParameters(
            direction="LONG", entry_price=100.0, stop_loss=100.0,
            take_profit_1=110.0, risk_reward_ratio=1.0,
        )
        result = evaluate_hypothetical_outcome(tp, [])
        assert result["mfe_r"] == 0.0
        assert result["mae_r"] == 0.0

    def test_exit_substate_persisted(self):
        """Verify exit_substate is in the result dict."""
        from scripts.backtest_runner import evaluate_hypothetical_outcome
        from src.models.analysis_models import TradeParameters

        tp = TradeParameters(
            direction="LONG", entry_price=100.0, stop_loss=95.0,
            take_profit_1=115.0, take_profit_2=120.0, take_profit_3=125.0,
            risk_reward_ratio=3.0,
        )
        candles = [
            {"time": "t0", "open": 100, "close": 94, "high": 101, "low": 93},
        ]
        result = evaluate_hypothetical_outcome(tp, candles)
        assert "exit_substate" in result
        assert result["exit_substate"] == "CLOSED_SL"
