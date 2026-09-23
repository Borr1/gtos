"""Tests for Component 3A — Primary Analyzer.

All tests mock the Anthropic API — no real API calls are made.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.components.knowledge_base import KnowledgeBase
from src.components import primary_analyzer as _primary_analyzer_mod
from src.components.primary_analyzer import (
    PrimaryAnalyzer,
    guard_candidate_degenerate_params,
    guard_candidate_inconsistent_pois,
    guard_candidate_wrong_side_sl,
)
from src.components.verification import _compute_effective_framework
from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.market_state_models import (
    DataQuality,
    LiquidityPool,
    LiquiditySweep,
    MarketStateObject,
    OrderBlock,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)


# ── Helpers ───────────────────────────────────────────────────────────

def _make_mso() -> MarketStateObject:
    bullish = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
    m15 = TimeframeState(
        structure=bullish,
        structure_events=[
            StructureEvent(
                type="BOS", direction="bullish",
                level_broken=3050.0, close_price=3055.0,
                candle_index=10, time="2026-03-28T07:30:00Z",
                displacement_present=True, displacement_ratio=2.4,
            ),
        ],
    )
    pool = LiquidityPool(type="asian_low", price=3038.50, side="low")
    return MarketStateObject(
        timestamp_utc="2026-03-28T07:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish),
            "H4": TimeframeState(structure=bullish),
            "H1": TimeframeState(structure=bullish),
            "M15": m15,
        },
        session_levels=SessionLevels(
            asian_high=3045.0, asian_low=3038.50, pdh=3052.0, pdl=3030.0,
        ),
        liquidity_pools=[pool],
        detected_sweeps=[
            LiquiditySweep(
                pool=pool, sweep_type="sweep",
                wick_extreme=3037.0, body_close=3039.0,
                candle_index=8, time="2026-03-28T07:15:00Z",
            ),
        ],
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-03-28T07:30:00Z",
        ),
    )


def test_build_prompt_framework_override_narrows_cached_system_prompt(monkeypatch):
    captured_frameworks = []
    config = {
        "market": {"symbol": "XAUUSD"},
        "model_a": {"enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"]},
        "prompt": {"price_format": ".2f"},
        "ai": {"primary_model": "claude-sonnet-4-6"},
    }
    kb = MagicMock()
    kb.assemble_full_context.return_value = {"layer1": {}, "layer2": {}, "layer3": []}
    analyzer = PrimaryAnalyzer(config, kb)

    monkeypatch.setattr(
        _primary_analyzer_mod.primary_analyzer_prompt,
        "set_price_format",
        lambda _fmt: None,
    )
    monkeypatch.setattr(
        _primary_analyzer_mod.primary_analyzer_prompt,
        "build_static_context",
        lambda _mso: "static",
    )

    def fake_build_system_prompt(prompt_config):
        captured_frameworks.append(tuple(prompt_config["model_a"]["enabled_frameworks"]))
        return "system"

    monkeypatch.setattr(
        _primary_analyzer_mod.primary_analyzer_prompt,
        "build_system_prompt",
        fake_build_system_prompt,
    )
    monkeypatch.setattr(
        _primary_analyzer_mod.primary_analyzer_prompt,
        "build_user_message",
        lambda *_args, **_kwargs: "user",
    )

    analyzer.build_prompt(_make_mso(), "2026-05-18T00:00:00+00:00", frameworks_override=["ob_retest"])
    analyzer.build_prompt(_make_mso(), "2026-05-18T00:15:00+00:00", frameworks_override=["fvg_fill"])

    assert captured_frameworks == [("ob_retest",), ("fvg_fill",)]
    assert config["model_a"]["enabled_frameworks"] == ["ob_retest", "fvg_fill", "breaker_re_entry"]


_VALID_CANDIDATE_JSON = json.dumps({
    "timestamp_utc": "2026-03-28T07:30:00Z",
    "model_used": "claude-sonnet-4-20250514",
    "decision": "CANDIDATE",
    "confidence_score": 78,
    "reasoning": {
        "daily_bias": {
            "direction": "bullish",
            "confidence": "high",
            "protected_swing_level": 3030.0,
            "explanation": "Daily HH/HL intact.",
        },
        "h4_alignment": {
            "aligned": True,
            "h4_pois_identified": ["OB at 3042"],
            "explanation": "H4 aligned.",
        },
        "h1_setup": {
            "poi_identified": True,
            "poi_type": "OB",
            "poi_price_level": 3042.0,
            "zone": "discount",
            "fib_retracement_pct": 68.0,
            "explanation": "H1 pulled back to OB in OTE.",
        },
        "liquidity_sweep": {
            "detected": True,
            "pool_type": "asian_low",
            "sweep_quality": "clean",
            "sweep_price": 3037.0,
            "explanation": "Clean Asian low sweep.",
        },
        "m15_confirmation": {
            "choch_detected": True,
            "displacement_quality": "strong",
            "displacement_candle_body_vs_avg_ratio": 2.4,
            "explanation": "M15 CHoCH with 2.4x displacement.",
        },
        "similar_historical_setups_considered": [],
        "setup_grade": "A+",
        "overall_reasoning": "Full Model A alignment.",
    },
    "trade_parameters": {
        "direction": "LONG",
        "entry_price": 3039.85,
        "stop_loss": 3033.50,
        "take_profit_1": 3048.10,
        "take_profit_2": 3055.0,
        "take_profit_3": 3068.0,
        "risk_reward_ratio": 3.48,
        "position_size_lots": 0.08,
    },
    "no_trade_reason": None,
    "wait_reason": None,
})


_VALID_NO_TRADE_JSON = json.dumps({
    "timestamp_utc": "2026-03-28T07:30:00Z",
    "model_used": "claude-sonnet-4-20250514",
    "decision": "NO_TRADE",
    "confidence_score": 0,
    "reasoning": {
        "daily_bias": {
            "direction": "ranging",
            "confidence": "low",
            "protected_swing_level": 0.0,
            "explanation": "Daily ranging — no clear bias.",
        },
        "h4_alignment": {"aligned": False, "explanation": "N/A"},
        "h1_setup": {"poi_identified": False, "explanation": "N/A"},
        "liquidity_sweep": {"detected": False, "explanation": "N/A"},
        "m15_confirmation": {"choch_detected": False, "explanation": "N/A"},
        "setup_grade": "C",
        "overall_reasoning": "No trade — daily structure unclear.",
    },
    "trade_parameters": None,
    "no_trade_reason": "Daily structure ranging — no directional bias",
    "wait_reason": None,
})


def _mock_anthropic_response(text: str):
    """Create a mock Anthropic response object."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


@pytest.fixture(autouse=True)
def _isolate_malformed_log(tmp_path, monkeypatch):
    monkeypatch.setattr(
        _primary_analyzer_mod, "_MALFORMED_LOG", tmp_path / "malformed_responses.jsonl",
    )
    yield


@pytest.fixture
def config():
    return {
        "ai": {
            "primary_model": "claude-sonnet-4-20250514",
            "api_timeout_seconds": 30,
            "max_api_retries": 1,
        },
    }


@pytest.fixture
def kb(tmp_path, monkeypatch):
    """KnowledgeBase backed by tmp dir with pipeline_state ready."""
    import src.utils.file_io as fio
    monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    return KnowledgeBase(base_path=str(tmp_path))


def _make_analyzer(config, kb):
    """Build a PrimaryAnalyzer with a mocked Anthropic client."""
    with patch("src.llm_backend.Anthropic") as MockCls:
        mock_client = MagicMock()
        MockCls.return_value = mock_client
        analyzer = PrimaryAnalyzer(config, kb)
    # analyzer.client is mock_client (via backend.get_api_client())
    return analyzer


# ── Tests ─────────────────────────────────────────────────────────────

class TestPrimaryCandidateRateModelGuard:
    def test_agent_config_allows_validated_max_but_blocks_t2c_failed_high_effort(self, kb):
        with open("config/agent_config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert cfg["ai"]["primary_model"] == "claude-sonnet-4-6"
        assert cfg["ai"]["primary_effort"] == "max"
        analyzer = _make_analyzer(cfg, kb)
        assert analyzer.model == "claude-sonnet-4-6"
        assert analyzer.effort == "max"

        bad_cfg = dict(cfg)
        bad_cfg["ai"] = dict(cfg["ai"])
        bad_cfg["ai"]["primary_effort"] = "high"
        with pytest.raises(ValueError, match="t2c_sonnet46_medium_high_over_rejected_good_trades"):
            _make_analyzer(bad_cfg, kb)

        opus_cfg = dict(cfg)
        opus_cfg["ai"] = dict(cfg["ai"])
        opus_cfg["ai"]["primary_model"] = "claude-opus-4-7"
        opus_cfg["ai"]["primary_effort"] = "max"
        with pytest.raises(ValueError, match="p2c_opus4x_primary_analyzer_killed_by_cr_wr_and_cost"):
            _make_analyzer(opus_cfg, kb)

    def test_candidate_rate_guard_can_be_disabled_for_explicit_research_controls(self, kb):
        cfg = {
            "ai": {
                "primary_model": "claude-sonnet-4-6",
                "primary_effort": "medium",
                "candidate_rate_model_guard_enabled": False,
                "candidate_rate_blocked_model_efforts": [
                    {"model": "claude-sonnet-4-6", "efforts": ["medium"]},
                ],
            }
        }

        analyzer = _make_analyzer(cfg, kb)
        assert analyzer.effort == "medium"


class TestParseValidResponse:

    def test_parse_valid_candidate(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        result = analyzer._parse_and_validate(_VALID_CANDIDATE_JSON)
        assert isinstance(result, PrimaryAnalysisOutput)
        assert result.decision == "CANDIDATE"
        assert result.confidence_score == 78
        assert result.reasoning.setup_grade == "A+"
        assert result.trade_parameters is not None
        assert result.trade_parameters.direction == "LONG"

    def test_parse_valid_no_trade(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        result = analyzer._parse_and_validate(_VALID_NO_TRADE_JSON)
        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason is not None

    def test_parse_preserves_tokyo_kill_zone(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        payload = json.loads(_VALID_NO_TRADE_JSON)
        payload["kill_zone"] = "tokyo"
        tokyo_json = json.dumps(payload)
        result = analyzer._parse_and_validate(tokyo_json)
        assert result.kill_zone == "tokyo"

    def test_parse_normalizes_tokyo_session_aliases(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        payload = json.loads(_VALID_NO_TRADE_JSON)
        payload["kill_zone"] = "tokyo_kz"
        tokyo_json = json.dumps(payload)
        result = analyzer._parse_and_validate(tokyo_json)
        assert result.kill_zone == "tokyo"

    def test_parse_normalizes_breaker_alias_to_active_route(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        payload = json.loads(_VALID_CANDIDATE_JSON)
        payload["framework"] = "breaker_block"
        payload["reasoning"]["h1_setup"]["poi_type"] = "breaker"

        result = analyzer._parse_and_validate(json.dumps(payload))

        assert result.framework == "breaker_re_entry"
        assert result.reasoning.h1_setup.poi_type == "breaker_block"

    def test_parse_normalizes_frameworks_evaluated_breaker_alias_keys(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        payload = json.loads(_VALID_CANDIDATE_JSON)
        payload["framework"] = "breaker_block_retest"
        payload["reasoning"]["h1_setup"]["poi_type"] = "breaker"
        payload["frameworks_evaluated"] = {
            "breaker_block": {"qualified": True, "reason": "unretested breaker present"},
            "ob_retest": {"qualified": False, "reason": "no active OB"},
        }

        result = analyzer._parse_and_validate(json.dumps(payload))
        effective, overridden, decision = _compute_effective_framework(result)

        assert result.framework == "breaker_re_entry"
        assert result.frameworks_evaluated is not None
        assert "breaker_re_entry" in result.frameworks_evaluated
        assert "breaker_block" not in result.frameworks_evaluated
        assert effective == "breaker_re_entry"
        assert overridden is False
        assert decision["reason"] == "wrapper_qualified"

    def test_model_used_overrides_ai_hallucination(self, config, kb):
        """AI-reported model_used is overridden by config value."""
        # Raw response where AI writes a wrong model name (e.g. gpt-4.1)
        wrong_model_json = _VALID_NO_TRADE_JSON.replace(
            '"model_used": "claude-sonnet-4-20250514"',
            '"model_used": "gpt-4.1"',
        )
        analyzer = _make_analyzer(config, kb)
        result = analyzer._parse_and_validate(wrong_model_json)
        # Should be the config value, not the AI-hallucinated value
        assert result.model_used == config["ai"]["primary_model"]
        assert result.model_used != "gpt-4.1"


class TestParseMalformedResponse:

    def test_parse_malformed_raises(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        with pytest.raises(Exception):
            analyzer._parse_and_validate("This is not JSON at all")

    def test_parse_incomplete_json_raises(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        with pytest.raises(Exception):
            analyzer._parse_and_validate('{"decision": "CANDIDATE"}')

    async def test_analyze_retries_then_no_trade(self, config, kb):
        """Malformed on both attempts → NO_TRADE with ai_output_malformed."""
        config = {**config, "market": {"symbol": "XAUUSD"}}
        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.return_value = _mock_anthropic_response(
            "Sorry, I can't produce JSON right now."
        )

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason == "ai_output_malformed"
        # Should have been called twice (original + retry)
        assert analyzer.client.messages.create.call_count == 2
        rows = [
            json.loads(line)
            for line in _primary_analyzer_mod._MALFORMED_LOG.read_text(encoding="utf-8").splitlines()
        ]
        assert len(rows) == 2
        assert rows[0]["symbol"] == "XAUUSD"
        assert rows[0]["candle_time"] == mso.timestamp_utc
        assert rows[0]["kill_zone"] == "london"
        assert rows[0]["model"] == config["ai"]["primary_model"]
        assert rows[0]["schema_version"] == "ai_malformed_response_v2"
        assert rows[0]["raw_response_sha256"]
        fallback = rows[0]["ai_reliability_contract"]["fallback_behavior_contract"]
        assert fallback["fallback_active"] is True
        assert fallback["fallback_action"] == "NO_TRADE"

    async def test_analyze_ai_call_policy_blocks_historical_market_replay(self, config, kb, tmp_path):
        cfg = {
            **config,
            "market": {"symbol": "XAUUSD"},
            "ai_call_policy": {
                "enabled": True,
                "apply_to_ai_call": True,
                "decision_log_path": str(tmp_path / "ai_call_policy.jsonl"),
            },
        }
        analyzer = _make_analyzer(cfg, kb)

        result = await analyzer.analyze(
            _make_mso(),
            kill_zone="london",
            ai_call_context={
                "purpose": "market_edge_replay",
                "runtime_context": "historical_replay",
            },
        )

        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason == "ai_call_policy:ai_cost_control_no_api_market_replay"
        analyzer.client.messages.create.assert_not_called()
        rows = (tmp_path / "ai_call_policy.jsonl").read_text(encoding="utf-8").splitlines()
        assert json.loads(rows[0])["decision"]["action"] == "SKIP_AI_NO_API_REPLAY"

    async def test_analyze_retry_transport_failure_logs_context_then_no_trade(self, config, kb):
        """Malformed first attempt + retry call failure still returns NO_TRADE."""
        config = {**config, "market": {"symbol": "GBPJPY"}}
        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.side_effect = [
            _mock_anthropic_response("not json"),
            RuntimeError("retry transport failed"),
        ]

        mso = _make_mso()
        result = await analyzer.analyze(mso, kill_zone="ny")

        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason == "ai_output_malformed"
        rows = [
            json.loads(line)
            for line in _primary_analyzer_mod._MALFORMED_LOG.read_text(encoding="utf-8").splitlines()
        ]
        assert [row["attempt"] for row in rows] == [1, 2]
        assert rows[1]["symbol"] == "GBPJPY"
        assert rows[1]["candle_time"] == mso.timestamp_utc
        assert rows[1]["kill_zone"] == "ny"
        assert rows[1]["raw_response_length"] == 0

    async def test_analyze_succeeds_on_retry(self, config, kb):
        """Malformed first, valid on retry → CANDIDATE."""
        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.side_effect = [
            _mock_anthropic_response("not json"),
            _mock_anthropic_response(_VALID_CANDIDATE_JSON),
        ]

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "CANDIDATE"
        assert analyzer.client.messages.create.call_count == 2

    async def test_analyze_writes_hash_only_ai_decision_trace(self, config, kb, tmp_path):
        """Enabled trace logger records prompt/response hashes, not prompt text."""
        trace_path = tmp_path / "ai_decision_trace.jsonl"
        config = {
            **config,
            "market": {"symbol": "XAUUSD"},
            "shadow_loggers": {
                "ai_decision_trace_logger": {
                    "enabled": True,
                    "path": str(trace_path),
                },
            },
        }
        analyzer = _make_analyzer(config, kb)
        response = _mock_anthropic_response(_VALID_NO_TRADE_JSON)
        response.usage.input_tokens = 123
        response.usage.output_tokens = 45
        response.usage.cache_read_input_tokens = 67
        response.usage.cache_creation_input_tokens = 8
        analyzer.client.messages.create.return_value = response

        mso = _make_mso()
        result = await analyzer.analyze(mso, kill_zone="ny")

        assert result.decision == "NO_TRADE"
        rows = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        row = rows[0]
        assert row["symbol"] == "XAUUSD"
        assert row["candle_time"] == mso.timestamp_utc
        assert row["kill_zone"] == "ny"
        assert row["response_status"] == "parsed_first_attempt"
        assert row["parse_attempts"] == 1
        assert row["decision"] == "NO_TRADE"
        assert row["usage"]["input_tokens"] == 123
        assert row["usage"]["cache_read_tokens"] == 67
        assert row["prompt_fingerprint"]["system_prompt_sha256"]
        assert row["prompt_fingerprint"]["user_message_sha256"]
        assert row["raw_response_sha256"]
        encoded = json.dumps(row, sort_keys=True)
        assert "Dynamic Market Data" not in encoded
        assert _VALID_NO_TRADE_JSON not in encoded


class TestParseResponseWithFences:

    def test_json_in_markdown_fences(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        fenced = f"```json\n{_VALID_CANDIDATE_JSON}\n```"
        result = analyzer._parse_and_validate(fenced)
        assert result.decision == "CANDIDATE"

    def test_json_in_plain_fences(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        fenced = f"```\n{_VALID_NO_TRADE_JSON}\n```"
        result = analyzer._parse_and_validate(fenced)
        assert result.decision == "NO_TRADE"

    def test_json_with_trailing_second_object_uses_first_valid_object(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        raw = f"{_VALID_NO_TRADE_JSON}\n\n{{\"note\": \"extra diagnostic object\"}}"
        result = analyzer._parse_and_validate(raw)
        assert result.decision == "NO_TRADE"

    def test_fenced_json_with_trailing_object_inside_fence_uses_first_object(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        raw = f"```json\n{_VALID_CANDIDATE_JSON}\n{{\"note\": \"extra diagnostic object\"}}\n```"
        result = analyzer._parse_and_validate(raw)
        assert result.decision == "CANDIDATE"


class TestTimeoutHandling:

    async def test_no_trade_on_timeout(self, config, kb):
        from src.components.primary_analyzer import AnthropicTimeoutError

        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.side_effect = AnthropicTimeoutError(request=MagicMock())

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason == "api_timeout"

    async def test_no_trade_on_server_error(self, config, kb):
        from src.components.primary_analyzer import AnthropicServerError

        analyzer = _make_analyzer(config, kb)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        analyzer.client.messages.create.side_effect = AnthropicServerError(
            message="Server Error",
            response=mock_resp,
            body=None,
        )

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "NO_TRADE"
        assert "server_error" in result.no_trade_reason or "500" in str(result.no_trade_reason)


class TestCandidateOutputFormat:

    async def test_candidate_has_all_fields(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.return_value = _mock_anthropic_response(
            _VALID_CANDIDATE_JSON,
        )

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "CANDIDATE"
        assert result.confidence_score > 0
        assert result.reasoning is not None
        assert result.reasoning.daily_bias.direction == "bullish"
        assert result.reasoning.h4_alignment.aligned is True
        assert result.reasoning.h1_setup.poi_identified is True
        assert result.reasoning.liquidity_sweep.detected is True
        assert result.reasoning.m15_confirmation.choch_detected is True
        assert result.reasoning.setup_grade == "A+"
        assert result.trade_parameters is not None
        assert result.trade_parameters.entry_price > 0
        assert result.trade_parameters.stop_loss > 0
        assert result.trade_parameters.risk_reward_ratio >= 3.0

    async def test_pipeline_file_written(self, config, kb, tmp_path, monkeypatch):
        import src.utils.file_io as fio
        monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
        (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)

        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.return_value = _mock_anthropic_response(
            _VALID_CANDIDATE_JSON,
        )

        mso = _make_mso()
        await analyzer.analyze(mso)

        out = tmp_path / "pipeline_state" / "03a_primary_analysis.json"
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["decision"] == "CANDIDATE"


class TestNoTradeOutputFormat:

    async def test_no_trade_format(self, config, kb):
        analyzer = _make_analyzer(config, kb)
        analyzer.client.messages.create.return_value = _mock_anthropic_response(
            _VALID_NO_TRADE_JSON,
        )

        mso = _make_mso()
        result = await analyzer.analyze(mso)

        assert result.decision == "NO_TRADE"
        assert result.confidence_score == 0
        assert result.no_trade_reason is not None
        assert result.trade_parameters is None
        assert result.reasoning.daily_bias.direction == "ranging"


class TestGuardCandidateDegenerateParams:
    """FA-2 Change 2+3 validator — session 35 commit fa35cc0.

    Backstop for FX-precision-bug degeneracy (entry==SL or entry==TP1 bit-exactly
    due to 2-dp rounding on 4/5-dp FX instruments). β review quantified 59.67% of
    EURUSD CANDIDATE outputs as degenerate; the prompt fix (PRECISION block) cuts
    this to ~11% on EURUSD, and this validator demotes the residual to NO_TRADE
    before execution.
    """

    def _base_candidate(self) -> PrimaryAnalysisOutput:
        return PrimaryAnalysisOutput.model_validate(json.loads(_VALID_CANDIDATE_JSON))

    def test_entry_equals_sl_demotes_to_no_trade(self):
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.entry_price = 1.16000
        result.trade_parameters.stop_loss = 1.16000
        result.trade_parameters.take_profit_1 = 1.17000

        guarded = guard_candidate_degenerate_params(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "degenerate_trade_parameters"
        assert "entry_price==stop_loss" in guarded.reasoning.overall_reasoning

    def test_entry_equals_tp1_demotes_to_no_trade(self):
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.entry_price = 1.16000
        result.trade_parameters.stop_loss = 1.15000
        result.trade_parameters.take_profit_1 = 1.16000

        guarded = guard_candidate_degenerate_params(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "degenerate_trade_parameters"
        assert "entry_price==take_profit_1" in guarded.reasoning.overall_reasoning

    def test_non_degenerate_candidate_passes_through(self):
        result = self._base_candidate()
        # _VALID_CANDIDATE_JSON ships entry=3039.85, sl=3033.50, tp1=3048.10 —
        # all distinct; guard must NOT demote.
        guarded = guard_candidate_degenerate_params(result)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None
        assert guarded.trade_parameters is not None
        assert guarded.trade_parameters.entry_price == 3039.85

    def test_no_trade_passes_through_unchanged(self):
        result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_NO_TRADE_JSON))
        original_reason = result.no_trade_reason

        guarded = guard_candidate_degenerate_params(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == original_reason
        assert guarded.trade_parameters is None


# ── POI / entry / SL consistency guard (Thursday 2026-04-23 US30 NY 16:00) ────

def _mso_with_h1_obs(order_blocks: list[OrderBlock]) -> MarketStateObject:
    """Build a minimal MSO with an H1 timeframe carrying the supplied OBs.

    All other fields are default-ish so the guard only exercises the
    H1.order_blocks path.
    """
    bullish = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
    return MarketStateObject(
        timestamp_utc="2026-04-23T16:00:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish),
            "H4": TimeframeState(structure=bullish),
            "H1": TimeframeState(structure=bullish, order_blocks=order_blocks),
            "M15": TimeframeState(structure=bullish),
        },
        session_levels=SessionLevels(
            asian_high=48600.0, asian_low=48400.0,
            pdh=48700.0, pdl=48300.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-04-23T16:00:00Z",
        ),
    )


def _bullish_ob(low: float, high: float, touches: int = 1) -> OrderBlock:
    return OrderBlock(
        type="bullish", low=low, high=high,
        open=low, close=high,
        formation_index=1, formation_time="2026-04-23T14:00:00Z",
        causing_bos_index=2, touch_count=touches,
    )


def _bearish_ob(low: float, high: float, touches: int = 1) -> OrderBlock:
    return OrderBlock(
        type="bearish", low=low, high=high,
        open=high, close=low,
        formation_index=1, formation_time="2026-04-23T14:00:00Z",
        causing_bos_index=2, touch_count=touches,
    )


def _candidate_with(
    direction: str,
    poi_level: float,
    entry: float,
    sl: float,
    tp1: float,
) -> PrimaryAnalysisOutput:
    """Build a CANDIDATE output with the supplied trade params."""
    result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_CANDIDATE_JSON))
    result.reasoning.h1_setup.poi_price_level = poi_level
    assert result.trade_parameters is not None
    result.trade_parameters.direction = direction
    result.trade_parameters.entry_price = entry
    result.trade_parameters.stop_loss = sl
    result.trade_parameters.take_profit_1 = tp1
    return result


class TestGuardCandidateInconsistentPois:
    """Post-AI validator: poi_price_level, entry_price, stop_loss must all
    reference the SAME H1 OB. Thursday 2026-04-23 US30 NY 16:00 case.
    """

    def test_consistent_long_passes(self):
        # OB: [48500, 48600], LONG with entry inside, SL below, TP1 above.
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate_with(
            direction="LONG", poi_level=48550.0,
            entry=48590.0, sl=48480.0, tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_consistent_short_passes(self):
        # OB: [48500, 48600], SHORT with entry inside, SL above, TP1 below.
        ob = _bearish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate_with(
            direction="SHORT", poi_level=48550.0,
            entry=48510.0, sl=48620.0, tp1=48300.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_poi_and_entry_different_obs_demotes(self):
        """Thursday 2026-04-23 US30 NY 16:00 scenario.

        POI (48531.325) maps to the touches=4 OB [48472.35, 48590.30].
        Entry (48645.71) is on the HIGH of a different touches=2 OB
        [48590.30, 48645.71]. Different OBs → demote.
        """
        ob_touches_4 = _bullish_ob(low=48472.35, high=48590.30, touches=4)
        ob_touches_2 = _bullish_ob(low=48590.30, high=48645.71, touches=2)
        mso = _mso_with_h1_obs([ob_touches_4, ob_touches_2])
        result = _candidate_with(
            direction="LONG",
            poi_level=48531.325,   # midpoint of touches=4 OB
            entry=48645.71,        # high of touches=2 OB
            sl=48450.0,            # below touches=4 low (would pass if that OB matched)
            tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "ai_output_inconsistent_pois"
        assert "48531.325" in guarded.reasoning.overall_reasoning
        assert "48645.71" in guarded.reasoning.overall_reasoning
        # Matched OB annotated in detail.
        assert "48472.35" in guarded.reasoning.overall_reasoning
        assert "48590.3" in guarded.reasoning.overall_reasoning

    def test_sl_inside_ob_no_longer_demotes_here(self):
        """HALLUC-1 fix (2026-04-27): the SL-beyond-OB-far-edge check has been
        REMOVED from this guard.

        Rationale: the prompt instructs SL placement beyond the H1/M15 swing
        low (LONG) or swing high (SHORT) — NOT beyond the OB's far edge.
        Two-thirds of the NAS100 2026-04-27 demotion rate (Pattern B in
        ``research/halluc_1_nas100_dumps/report.json``) were this prompt-vs-
        guard contradiction. SL geometry vs. OB is now enforced solely by the
        tolerance-tier L2 ``sl_beyond_ob`` gate (verification.py:127-145),
        which is config-driven via ``verification.sl_beyond_ob_tick_floor``.

        This guard only enforces entry-vs-OB and TP1-vs-entry now.
        """
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        # LONG: SL=48505 is inside OB (above OB.low 48500). Pre-fix this
        # demoted; post-fix the guard ignores SL-vs-OB and L2 sl_beyond_ob
        # is the single source of truth.
        result = _candidate_with(
            direction="LONG", poi_level=48550.0,
            entry=48590.0, sl=48505.0, tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_tp1_wrong_side_demotes(self):
        """LONG with TP1 below entry → demote (overlaps with prompt check)."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate_with(
            direction="LONG", poi_level=48550.0,
            entry=48590.0, sl=48480.0, tp1=48400.0,  # TP1 < entry for LONG
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "ai_output_inconsistent_pois"
        assert "take_profit_1" in guarded.reasoning.overall_reasoning

    def test_poi_outside_all_obs_returns_unchanged(self):
        """POI level not inside any H1 OB — defer to L2 ``h1_poi_exists``."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate_with(
            direction="LONG",
            poi_level=49000.0,   # far outside the only OB
            entry=48590.0, sl=48480.0, tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)

        # Gate is passive here; later L2 will reject.
        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_ambiguous_overlapping_obs_picks_closest(self):
        """Two OBs overlap the POI level; the OB with the edge closest to
        ``entry_price`` wins the tiebreaker.

        Wider OB [48400, 48700] and tighter OB [48540, 48560] both contain
        POI 48550.

        Case A — entry 48545 inside the tight OB, SL 48535 below tight low
        (48540) but NOT below wide low (48400). If the guard picked the wide
        OB, the LONG SL check would fail (48535 not < 48400). The fact that
        this passes proves the tight OB was chosen.

        Case B — entry 48620 outside the tight OB but inside the wide OB.
        The nearest-edge distance is smaller for the tight OB (60) than the
        wide OB (80), so the guard still picks tight and the entry-inside-OB
        check fails → demote.
        """
        wide_ob = _bullish_ob(low=48400.0, high=48700.0, touches=5)
        tight_ob = _bullish_ob(low=48540.0, high=48560.0, touches=1)
        mso = _mso_with_h1_obs([wide_ob, tight_ob])

        # Case A — tight wins and the full setup is coherent against tight.
        result_pass = _candidate_with(
            direction="LONG",
            poi_level=48550.0,
            entry=48545.0,      # inside tight OB
            sl=48535.0,         # below tight low (48540), NOT below wide low (48400)
            tp1=48700.0,
        )
        guarded_pass = guard_candidate_inconsistent_pois(result_pass, mso)
        assert guarded_pass.decision == "CANDIDATE"
        assert guarded_pass.no_trade_reason is None

        # Case B — tight still wins on nearest-edge; entry outside tight → demote.
        result_fail = _candidate_with(
            direction="LONG",
            poi_level=48550.0,
            entry=48620.0,      # inside wide OB, OUTSIDE tight OB
            sl=48300.0,
            tp1=48800.0,
        )
        guarded_fail = guard_candidate_inconsistent_pois(result_fail, mso)
        assert guarded_fail.decision == "NO_TRADE"
        assert guarded_fail.no_trade_reason == "ai_output_inconsistent_pois"
        # Matched-OB label in the detail should be the tight OB.
        assert "48540" in guarded_fail.reasoning.overall_reasoning
        assert "48560" in guarded_fail.reasoning.overall_reasoning

    def test_not_candidate_returns_unchanged(self):
        """NO_TRADE input stays NO_TRADE without modification."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_NO_TRADE_JSON))
        original_reason = result.no_trade_reason

        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == original_reason
        assert guarded.trade_parameters is None

    def test_zero_poi_level_returns_unchanged(self):
        """AI omitted poi_price_level (Pydantic default 0.0) → defer."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate_with(
            direction="LONG",
            poi_level=0.0,       # not reported
            entry=48590.0, sl=48480.0, tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)
        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_missing_h1_timeframe_returns_unchanged(self):
        """MSO without H1 timeframe → conservative passthrough."""
        bullish = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
        mso = MarketStateObject(
            timestamp_utc="2026-04-23T16:00:00Z",
            timeframes={
                "D1": TimeframeState(structure=bullish),
                "H4": TimeframeState(structure=bullish),
                "M15": TimeframeState(structure=bullish),
            },
            session_levels=SessionLevels(
                asian_high=48600.0, asian_low=48400.0,
                pdh=48700.0, pdl=48300.0,
            ),
            data_quality=DataQuality(
                all_timeframes_complete=True, spread_normal=True,
                mt5_connected=True, timestamp_utc="2026-04-23T16:00:00Z",
            ),
        )
        result = _candidate_with(
            direction="LONG", poi_level=48550.0,
            entry=48590.0, sl=48480.0, tp1=48800.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso)
        assert guarded.decision == "CANDIDATE"
class TestGuardCandidateWrongSideSL:
    """PROMPT V2 validator — blocks geometrically impossible SL placement.

    Prompt V2 added a self-check instruction telling the AI to emit NO_TRADE
    with reason "self_check_failed" when SL is on the wrong side of entry.
    This validator is the programmatic backstop: if the AI still emits a
    wrong-side SL (e.g., LONG with SL > entry), demote to NO_TRADE with
    reason "wrong_side_sl" rather than let it reach execution.

    Motivating evidence: GBPUSD Thursday 2026-04-23 audit — 63.6% of 11
    CANDIDATEs had L2 reject on `sl_beyond_ob` because Sonnet-4-6 emitted
    SL > entry for LONG. Documented in fa3_t7_rerun_report.md §2 D1.
    """

    def _base_candidate(self) -> PrimaryAnalysisOutput:
        return PrimaryAnalysisOutput.model_validate(json.loads(_VALID_CANDIDATE_JSON))

    def test_fx_self_check_rejects_wrong_side_sl_long(self):
        """LONG with SL > entry — geometrically impossible protective stop."""
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.direction = "LONG"
        result.trade_parameters.entry_price = 1.26543
        result.trade_parameters.stop_loss = 1.26789  # ABOVE entry, invalid for LONG
        result.trade_parameters.take_profit_1 = 1.27033

        guarded = guard_candidate_wrong_side_sl(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "wrong_side_sl"
        assert "LONG" in guarded.reasoning.overall_reasoning
        assert "stop_loss=1.26789" in guarded.reasoning.overall_reasoning

    def test_fx_self_check_rejects_wrong_side_sl_short(self):
        """SHORT with SL < entry — geometrically impossible protective stop."""
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.direction = "SHORT"
        result.trade_parameters.entry_price = 1.26543
        result.trade_parameters.stop_loss = 1.26298  # BELOW entry, invalid for SHORT
        result.trade_parameters.take_profit_1 = 1.26053

        guarded = guard_candidate_wrong_side_sl(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "wrong_side_sl"
        assert "SHORT" in guarded.reasoning.overall_reasoning

    def test_correct_side_sl_long_passes_through(self):
        """LONG with SL < entry — valid geometry, no demotion."""
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.direction = "LONG"
        result.trade_parameters.entry_price = 1.26543
        result.trade_parameters.stop_loss = 1.26298  # BELOW entry, valid for LONG
        result.trade_parameters.take_profit_1 = 1.27033

        guarded = guard_candidate_wrong_side_sl(result)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None
        assert guarded.trade_parameters.stop_loss == 1.26298

    def test_correct_side_sl_short_passes_through(self):
        """SHORT with SL > entry — valid geometry, no demotion."""
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.direction = "SHORT"
        result.trade_parameters.entry_price = 1.26543
        result.trade_parameters.stop_loss = 1.26789  # ABOVE entry, valid for SHORT
        result.trade_parameters.take_profit_1 = 1.26053

        guarded = guard_candidate_wrong_side_sl(result)

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_equal_sl_defers_to_degenerate_guard(self):
        """SL == entry is degenerate (not wrong-side); this guard must not fire.

        guard_candidate_degenerate_params runs first in the pipeline and
        catches bit-exact equality; this guard targets STRICT wrong-side
        cases only. Asserting non-interaction keeps the two guards' roles
        separate and avoids double-counting.
        """
        result = self._base_candidate()
        assert result.trade_parameters is not None
        result.trade_parameters.direction = "LONG"
        result.trade_parameters.entry_price = 1.26543
        result.trade_parameters.stop_loss = 1.26543  # EQUAL, not wrong-side
        result.trade_parameters.take_profit_1 = 1.27033

        guarded = guard_candidate_wrong_side_sl(result)

        # Wrong-side guard alone should NOT demote on equality
        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_no_trade_passes_through_unchanged(self):
        """NO_TRADE inputs are not touched by the wrong-side guard."""
        result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_NO_TRADE_JSON))
        original_reason = result.no_trade_reason

        guarded = guard_candidate_wrong_side_sl(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == original_reason
        assert guarded.trade_parameters is None


class TestFxPrecisionPromptScaffolding:
    """PROMPT V2 — verify per-instrument FX precision scaffolding is in the prompt.

    These tests exercise the prompt-construction layer only (no API calls).
    They lock in:
      - Decimal-place directive for each instrument family.
      - Presence of valid + invalid example blocks.
      - Presence of the end-of-prompt self-check section.
      - Presence of the STRICT RULE — H1 POI SOURCE section.

    Prompt-only regressions (e.g., accidental removal of the self-check on
    a future edit) surface here without needing a live canary run.
    """

    def test_precision_block_fx_5dp(self):
        from src.prompts.primary_analyzer_prompt import build_system_prompt
        cfg = {
            "market": {"symbol": "GBPUSD"},
            "risk": {"sl_absolute_min": 0.0003},
            "prompt": {"price_format": ".5f"},
        }
        p = build_system_prompt(cfg)
        assert "EXACTLY 5 decimal places" in p
        # Valid LONG example present
        assert "1.26543" in p
        # Wrong-side-SL counter-examples for both directions present
        assert "INVALID (SL wrong side for LONG)" in p
        assert "INVALID (SL wrong side for SHORT)" in p
        # Precision counter-examples present
        assert "INVALID (too few decimals)" in p
        assert "INVALID (too many decimals)" in p
        # Zero-buffer counter-example present
        assert "INVALID (zero buffer)" in p

    def test_precision_block_jpy_3dp(self):
        from src.prompts.primary_analyzer_prompt import build_system_prompt
        cfg = {
            "market": {"symbol": "USDJPY"},
            "risk": {"sl_absolute_min": 0.03},
            "prompt": {"price_format": ".3f"},
        }
        p = build_system_prompt(cfg)
        assert "EXACTLY 3 decimal places" in p
        assert "156.821" in p  # anchor for 3dp family

    def test_precision_block_xauusd_2dp(self):
        from src.prompts.primary_analyzer_prompt import build_system_prompt
        cfg = {
            "market": {"symbol": "XAUUSD"},
            "risk": {"sl_absolute_min": 5.0},
            "prompt": {"price_format": ".2f"},
        }
        p = build_system_prompt(cfg)
        assert "EXACTLY 2 decimal places" in p
        assert "2346.55" in p  # anchor for 2dp family

    def test_self_check_block_present(self):
        from src.prompts.primary_analyzer_prompt import build_system_prompt
        p = build_system_prompt({
            "market": {"symbol": "GBPUSD"},
            "prompt": {"price_format": ".5f"},
        })
        # The self-check section and its three critical anchors
        assert "SELF-CHECK" in p
        assert "self_check_failed" in p
        assert "stop_loss < entry_price" in p
        assert "entry_price < take_profit_1" in p

    def test_h1_poi_source_strict_rule_present(self):
        """Prompt V2 Issue 2 — forbid M15/H4/D1 zone as h1_poi_zone."""
        from src.prompts.primary_analyzer_prompt import build_system_prompt
        p = build_system_prompt({"market": {"symbol": "XAUUSD"}})
        assert "STRICT RULE — H1 POI SOURCE" in p
        # Forbidden-substitutions clause mentions M15 explicitly
        assert "Any zone listed under `## M15" in p
        # NO_TRADE reason code for the case where no H1 zone exists
        assert "no_qualifying_h1_poi" in p
        # Self-check item 6 must also reference the forbidden TFs
        assert "not a price" in p.lower() or "NOT a price" in p

    def test_h1_poi_from_m15_ob_prompt_only_no_programmatic_check(self):
        """Document the safety boundary for the M15-as-H1 substitution issue.

        There is NO programmatic validator that checks the TIMEFRAME SOURCE of
        the AI's cited h1_poi_zone. The only safeguards are:
          1. The prompt rule added in Prompt V2 ("STRICT RULE — H1 POI SOURCE").
          2. The L2 `h1_poi_exists` check (`src/components/verification.py`)
             which cross-references poi_price_level against the MSO's H1
             OB / breaker arrays with instrument-specific tolerance.

        If the AI cites an M15 OB midpoint as poi_price_level, L2 will
        typically reject because the M15 midpoint usually falls outside any
        unmitigated H1 OB zone. In the US30 Thursday 2026-04-23 London case,
        L2 `h1_poi_exists` caught all 4 substitutions for a counterfactual
        ~4R save.

        This test asserts the current safety model: prompt + L2, no
        programmatic source-timeframe check at the primary_analyzer level.
        If future work adds such a check, update this test to exercise it.
        """
        import src.components.primary_analyzer as pa_mod
        pa_source = pa_mod.__file__
        # Sanity assertions about what exists today
        assert hasattr(pa_mod, "guard_candidate_degenerate_params")
        assert hasattr(pa_mod, "guard_candidate_wrong_side_sl")
        # There is intentionally no guard_candidate_h1_poi_source_timeframe
        # today — safety lives at the prompt + L2 layer.
        assert not hasattr(pa_mod, "guard_candidate_h1_poi_source_timeframe")
        # Doc anchor: L2 check name used by verification.py
        assert pa_source is not None  # file must exist


class TestFxPrecisionBelowRequiredDecimalsRejected:
    """Complement to FA-2's guard_candidate_degenerate_params.

    If Sonnet-4-6 renders FX prices at 3dp when 5dp is required, the
    rounding typically collapses entry/SL/TP1 to the same value, which
    `guard_candidate_degenerate_params` catches as degenerate. This class
    documents that the validator is the programmatic contract; the prompt
    scaffolding is the probabilistic primary line of defense.
    """

    def test_fx_precision_below_required_decimals_rejected(self):
        """3dp render on a 5dp pair that collapses entry==SL is demoted."""
        result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_CANDIDATE_JSON))
        assert result.trade_parameters is not None
        # AI renders at 3dp, collapsing 1.26543 and 1.26498 both to ~1.265
        result.trade_parameters.direction = "LONG"
        result.trade_parameters.entry_price = 1.265
        result.trade_parameters.stop_loss = 1.265  # collapsed by 3dp rounding
        result.trade_parameters.take_profit_1 = 1.270

        guarded = guard_candidate_degenerate_params(result)

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "degenerate_trade_parameters"
        assert "entry_price==stop_loss" in guarded.reasoning.overall_reasoning
