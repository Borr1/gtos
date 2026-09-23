"""Tests for Component 3B — Bull/Bear Debate.

All tests mock the Anthropic API — no real API calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.components.debate import DebateEngine, _make_rejection_verdict
from src.components.knowledge_base import KnowledgeBase
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
from src.models.debate_models import DebateVerdict
from src.models.market_state_models import (
    DataQuality,
    LiquidityPool,
    LiquiditySweep,
    MarketStateObject,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)


# ── Realistic JSON payloads ───────────────────────────────────────────

_BULL_R1_JSON = json.dumps({
    "position": "TAKE_TRADE",
    "argument_strength_self_assessed": 82,
    "key_points": [
        {"point": "Clean Asian low sweep at 3037.0", "supporting_data": "Wick 3037.0, body close 3039.0"},
        {"point": "Strong 2.4x displacement CHoCH", "supporting_data": "Avg body 2.3, BOS candle 5.5"},
    ],
    "historical_parallels_cited": ["tr_2026-02-10_001"],
    "full_argument": "Bullish daily aligned with H4. Clean Asian low sweep followed by 2.4x displacement CHoCH on M15. RR 3.48 with SL below sweep wick. Similar setup on Feb 10 yielded 3.2R WIN.",
})

_BEAR_R1_JSON = json.dumps({
    "position": "DO_NOT_TRADE",
    "argument_strength_self_assessed": 55,
    "key_points": [
        {"point": "Friday session — liquidity thins after noon", "supporting_data": "Historical pattern: Friday setups underperform"},
    ],
    "risks_identified": [
        {"risk": "Friday afternoon liquidity", "severity": "medium", "evidence": "Condition insight shows Friday win rate 35%"},
    ],
    "alternative_interpretations": ["Sweep could be a run if NY pushes lower"],
    "full_argument": "Friday risk is material. Historical Monday Asian low sweeps have 35% win rate. Displacement is strong but Friday afternoon could cause early TP miss.",
})

_BULL_REBUTTAL_JSON = json.dumps({
    "points_addressed": ["Friday liquidity risk"],
    "rebuttal": "TP1 at 3048.10 closes 50% before noon UTC. Remaining runner has SL at breakeven.",
    "concessions": ["Friday afternoon liquidity does thin — but risk is mitigated by TP1 timing."],
})

_BEAR_REBUTTAL_JSON = json.dumps({
    "points_addressed": ["Clean sweep and displacement"],
    "rebuttal": "Sweep wick was only $1.50 below Asian low — borderline. Could be noise not institutional.",
    "concessions": ["2.4x displacement ratio is genuinely strong."],
})

_VERDICT_APPROVE_JSON = json.dumps({
    "timestamp_utc": "2026-03-28T07:17:30Z",
    "model_used": "claude-sonnet-4-20250514",
    "verdict": "APPROVE",
    "winning_perspective": "BULL",
    "confidence_score": 80,
    "bull_argument_strength": 82,
    "bear_argument_strength": 55,
    "key_factor": "2.4x displacement with clean sweep outweighs Friday risk given TP1 timing",
    "risk_concerns_acknowledged": ["Friday liquidity thinning after noon"],
    "summary": "Bull case is clearly stronger. Displacement quality and clean sweep form a high-conviction setup. Bear's Friday concern is valid but mitigated by TP1 before noon.",
})

_VERDICT_REJECT_JSON = json.dumps({
    "timestamp_utc": "2026-03-28T07:17:30Z",
    "model_used": "claude-sonnet-4-20250514",
    "verdict": "REJECT",
    "winning_perspective": "BEAR",
    "confidence_score": 45,
    "bull_argument_strength": 60,
    "bear_argument_strength": 65,
    "key_factor": "Insufficient conviction — ties go to the bear",
    "risk_concerns_acknowledged": ["Friday risk", "borderline sweep"],
    "summary": "Arguments roughly equal. Default to capital preservation.",
})

_VERDICT_MARGINAL_JSON = json.dumps({
    "timestamp_utc": "2026-03-28T07:17:30Z",
    "model_used": "claude-sonnet-4-20250514",
    "verdict": "APPROVE",
    "winning_perspective": "BULL",
    "confidence_score": 55,
    "bull_argument_strength": 70,
    "bear_argument_strength": 60,
    "key_factor": "Bull case slightly stronger but bear raised valid points",
    "risk_concerns_acknowledged": ["Marginal conviction"],
    "summary": "Marginal approval — flagged for review.",
})


# ── Fixtures ──────────────────────────────────────────────────────────

def _mock_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _make_mso():
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


def _make_primary():
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-03-28T07:30:00Z",
        model_used="claude-sonnet-4-20250514",
        decision="CANDIDATE",
        confidence_score=78,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(poi_identified=True, poi_type="OB"),
            liquidity_sweep=LiquiditySweepAnalysis(detected=True, pool_type="asian_low"),
            m15_confirmation=M15ConfirmationAnalysis(choch_detected=True, displacement_quality="strong"),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction="LONG", entry_price=3039.85,
            stop_loss=3033.50, take_profit_1=3048.10,
            risk_reward_ratio=3.48,
        ),
    )


def _kb_context():
    return {"layer1": {}, "layer2": {}, "layer3": []}


@pytest.fixture
def config():
    return {
        "ai": {
            "debate_model": "claude-sonnet-4-20250514",
            "api_timeout_seconds": 30,
            "max_api_retries": 1,
            "debate_round2_enabled": True,
        },
    }


@pytest.fixture
def config_no_round2():
    return {
        "ai": {
            "debate_model": "claude-sonnet-4-20250514",
            "api_timeout_seconds": 30,
            "max_api_retries": 1,
            "debate_round2_enabled": False,
        },
    }


@pytest.fixture
def kb(tmp_path, monkeypatch):
    import src.utils.file_io as fio
    monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    return KnowledgeBase(base_path=str(tmp_path))


def _make_engine(config, kb):
    with patch("src.llm_backend.Anthropic") as MockCls:
        mock_client = MagicMock()
        MockCls.return_value = mock_client
        engine = DebateEngine(config, kb)
    return engine


# ── evaluate_verdict (deterministic, no async) ────────────────────────

class TestEvaluateVerdict:

    def test_approve_high(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=80,
            bull_argument_strength=85, bear_argument_strength=50,
        )
        assert DebateEngine.evaluate_verdict(v) == "APPROVED"

    def test_approve_marginal(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=55,
            bull_argument_strength=70, bear_argument_strength=60,
        )
        assert DebateEngine.evaluate_verdict(v) == "APPROVED_MARGINAL"

    def test_approve_low_confidence_rejected(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=40,
            bull_argument_strength=60, bear_argument_strength=55,
        )
        assert DebateEngine.evaluate_verdict(v) == "REJECTED"

    def test_reject(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="REJECT",
            winning_perspective="BEAR", confidence_score=90,
            bull_argument_strength=30, bear_argument_strength=90,
        )
        assert DebateEngine.evaluate_verdict(v) == "REJECTED"

    def test_boundary_70(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=70,
            bull_argument_strength=75, bear_argument_strength=50,
        )
        assert DebateEngine.evaluate_verdict(v) == "APPROVED"

    def test_boundary_50(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=50,
            bull_argument_strength=65, bear_argument_strength=60,
        )
        assert DebateEngine.evaluate_verdict(v) == "APPROVED_MARGINAL"

    def test_boundary_49(self):
        v = DebateVerdict(
            timestamp_utc="t", model_used="m", verdict="APPROVE",
            winning_perspective="BULL", confidence_score=49,
            bull_argument_strength=60, bear_argument_strength=58,
        )
        assert DebateEngine.evaluate_verdict(v) == "REJECTED"


# ── Full debate flow (async) ──────────────────────────────────────────

class TestFullDebateFlow:

    async def test_full_debate_with_round2(self, config, kb):
        engine = _make_engine(config, kb)
        # 5 sequential calls: bull_r1, bear_r1, bull_rebuttal, bear_rebuttal, judge
        engine.client.messages.create.side_effect = [
            _mock_response(_BULL_R1_JSON),
            _mock_response(_BEAR_R1_JSON),
            _mock_response(_BULL_REBUTTAL_JSON),
            _mock_response(_BEAR_REBUTTAL_JSON),
            _mock_response(_VERDICT_APPROVE_JSON),
        ]

        mso = _make_mso()
        pa = _make_primary()
        verdict = await engine.run_debate(mso, pa, _kb_context())

        assert isinstance(verdict, DebateVerdict)
        assert verdict.verdict == "APPROVE"
        assert verdict.confidence_score == 80
        assert DebateEngine.evaluate_verdict(verdict) == "APPROVED"
        assert engine.client.messages.create.call_count == 5

    async def test_round2_disabled(self, config_no_round2, kb):
        engine = _make_engine(config_no_round2, kb)
        # 3 calls: bull_r1, bear_r1, judge
        engine.client.messages.create.side_effect = [
            _mock_response(_BULL_R1_JSON),
            _mock_response(_BEAR_R1_JSON),
            _mock_response(_VERDICT_APPROVE_JSON),
        ]

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "APPROVE"
        # Only 3 calls — no Round 2
        assert engine.client.messages.create.call_count == 3

    async def test_round1_output_written(self, config_no_round2, kb, tmp_path, monkeypatch):
        import src.utils.file_io as fio
        monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
        (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)

        engine = _make_engine(config_no_round2, kb)
        engine.client.messages.create.side_effect = [
            _mock_response(_BULL_R1_JSON),
            _mock_response(_BEAR_R1_JSON),
            _mock_response(_VERDICT_APPROVE_JSON),
        ]

        await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        r1_path = tmp_path / "pipeline_state" / "03b_debate_round1.json"
        verdict_path = tmp_path / "pipeline_state" / "03b_verdict.json"
        assert r1_path.exists()
        assert verdict_path.exists()

        r1_data = json.loads(r1_path.read_text())
        assert "bull_argument" in r1_data
        assert "bear_argument" in r1_data


# ── Failure handling ──────────────────────────────────────────────────

class TestFailureHandling:

    async def test_bull_failure_rejection(self, config_no_round2, kb):
        """When _run_bull raises, we get REJECTED with bull_agent_api_failure."""
        engine = _make_engine(config_no_round2, kb)

        async def _bull_raise(*a, **kw):
            raise Exception("timeout")

        engine._run_bull = _bull_raise
        # Bear still works — but it doesn't matter, bull failure → rejection
        engine.client.messages.create.return_value = _mock_response(_BEAR_R1_JSON)

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "REJECT"
        assert "bull_agent_api_failure" in verdict.key_factor

    async def test_bear_failure_rejection(self, config_no_round2, kb):
        """When _run_bear raises, we get REJECTED with bear_agent_api_failure."""
        engine = _make_engine(config_no_round2, kb)

        async def _bear_raise(*a, **kw):
            raise Exception("timeout")

        engine._run_bear = _bear_raise
        engine.client.messages.create.return_value = _mock_response(_BULL_R1_JSON)

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "REJECT"
        assert "bear_agent_api_failure" in verdict.key_factor

    async def test_judge_failure_rejection(self, config_no_round2, kb):
        """When judge fails, we get REJECTED with judge_api_failure."""
        engine = _make_engine(config_no_round2, kb)
        # R1 succeeds, judge fails
        engine.client.messages.create.side_effect = [
            _mock_response(_BULL_R1_JSON),
            _mock_response(_BEAR_R1_JSON),
        ]

        async def _judge_fail(*a, **kw):
            return None

        engine._run_judge = _judge_fail

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "REJECT"
        assert "judge_api_failure" in verdict.key_factor

    async def test_round2_failure_falls_back(self, config, kb):
        """Round 2 fails → Judge still runs with Round 1 only."""
        engine = _make_engine(config, kb)

        async def _round2_fail(*a, **kw):
            return None

        engine._run_round2 = _round2_fail
        # R1 + Judge
        engine.client.messages.create.side_effect = [
            _mock_response(_BULL_R1_JSON),
            _mock_response(_BEAR_R1_JSON),
            _mock_response(_VERDICT_APPROVE_JSON),
        ]

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "APPROVE"

    async def test_both_agents_fail(self, config_no_round2, kb):
        engine = _make_engine(config_no_round2, kb)

        async def _bull_raise(*a, **kw):
            raise Exception("fail")

        async def _bear_raise(*a, **kw):
            raise Exception("fail")

        engine._run_bull = _bull_raise
        engine._run_bear = _bear_raise

        verdict = await engine.run_debate(_make_mso(), _make_primary(), _kb_context())

        assert verdict.verdict == "REJECT"
        assert "both_agents_failed" in verdict.key_factor
