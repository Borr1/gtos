"""Tests for shadow data collection: Devil's Advocate, EvaluationLogger, enriched records."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from src.components.devils_advocate import DevilsAdvocate, DA_SYSTEM_PROMPT
from src.components.evaluation_logger import EvaluationLogger


# ══════════════════���══════════════════════════��═════════════════════════════════
# Devil's Advocate
# ══════════════════════════════════════════════��════════════════════════════════

class TestDevilsAdvocate:
    """Tests for the DA shadow evaluator."""

    def test_disabled_returns_empty(self):
        da = DevilsAdvocate({"devils_advocate": {"shadow_enabled": False}})
        result = da.evaluate("mso", "reasoning", {"direction": "LONG"})
        assert result == {}

    def test_enabled_by_default(self):
        da = DevilsAdvocate({})
        assert da.enabled is True

    @patch.object(DevilsAdvocate, "_get_client")
    def test_returns_valid_json_with_risks(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "risks": [
                {
                    "description": "Resistance at 2765.50",
                    "confirming_level": 2765.50,
                    "probability_pct": 40,
                    "category": "STRUCTURAL_RESISTANCE",
                },
                {
                    "description": "Momentum exhaustion after 3 consecutive BOS",
                    "confirming_level": 2758.00,
                    "probability_pct": 30,
                    "category": "MOMENTUM_EXHAUSTION",
                },
                {
                    "description": "Late in London KZ",
                    "confirming_level": 0,
                    "probability_pct": 20,
                    "category": "TIMING_CONFLICT",
                },
            ],
            "max_risk_pct": 40,
            "overall_risk_assessment": "Moderate risk. Main concern is structural resistance.",
        }))]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        da = DevilsAdvocate({})
        result = da.evaluate("mso text", "bullish reasoning", {"direction": "LONG", "entry_price": 2760})

        assert "risks" in result
        assert len(result["risks"]) == 3
        assert result["max_risk_pct"] == 40
        assert "overall_risk_assessment" in result

    @patch.object(DevilsAdvocate, "_get_client")
    def test_api_failure_returns_error_dict(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API timeout")
        mock_get_client.return_value = mock_client

        da = DevilsAdvocate({})
        result = da.evaluate("mso", "reasoning", {})

        assert "error" in result
        assert "API timeout" in result["error"]

    @patch.object(DevilsAdvocate, "_get_client")
    def test_malformed_json_returns_error(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json at all")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        da = DevilsAdvocate({})
        result = da.evaluate("mso", "reasoning", {})

        assert "error" in result

    @patch.object(DevilsAdvocate, "_get_client")
    def test_computes_max_risk_from_risks(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "risks": [
                {"description": "a", "confirming_level": 0, "probability_pct": 10, "category": "TIMING_CONFLICT"},
                {"description": "b", "confirming_level": 0, "probability_pct": 70, "category": "DISPLACEMENT_DOUBT"},
            ],
            "overall_risk_assessment": "High risk."
        }))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        da = DevilsAdvocate({})
        result = da.evaluate("mso", "reasoning", {})
        assert result["max_risk_pct"] == 70

    def test_system_prompt_not_empty(self):
        assert len(DA_SYSTEM_PROMPT) > 100
        assert "risk" in DA_SYSTEM_PROMPT.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Evaluation Logger
# ══════════════════════════════════════��════════════════════════════════════════

class TestEvaluationLogger:
    """Tests for the per-evaluation structured logger."""

    def test_writes_jsonl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(base_dir=tmpdir)
            logger.log_evaluation(
                symbol="XAUUSD",
                candle_time="2025-04-07T07:15:00Z",
                kill_zone="london",
                analysis_dict={
                    "decision": "NO_TRADE",
                    "confidence_score": 0,
                    "framework": "none",
                    "reasoning": {
                        "daily_bias": {"direction": "bullish", "confidence": "high"},
                        "h4_alignment": {"aligned": True},
                        "h1_setup": {"poi_identified": False, "poi_type": "none"},
                        "liquidity_sweep": {"detected": False},
                        "m15_confirmation": {"choch_detected": False, "displacement_quality": "none"},
                        "overall_reasoning": "No setup identified at 2750.50 level",
                    },
                    "no_trade_reason": "no_h1_poi",
                },
                session_memory_count=2,
                align_score=3,
                spread=0.25,
            )

            fpath = os.path.join(tmpdir, "XAUUSD", "2025-04-07.jsonl")
            assert os.path.exists(fpath)

            with open(fpath) as f:
                line = f.readline()
                record = json.loads(line)

            assert record["decision"] == "NO_TRADE"
            assert record["daily_bias_direction"] == "bullish"
            assert record["h4_aligned"] is True
            assert record["align_score"] == 3
            assert record["spread"] == 0.25
            assert record["no_trade_reason"] == "no_h1_poi"
            assert record["reasoning_price_count"] == 1  # "2750.50"
            assert record["candle_index_in_kz"] == 0

    def test_multiple_evaluations_append(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(base_dir=tmpdir)
            for i in range(3):
                logger.log_evaluation(
                    symbol="XAUUSD",
                    candle_time="2025-04-07T07:15:00Z",
                    kill_zone="london",
                    analysis_dict={"decision": "NO_TRADE", "reasoning": {}},
                    session_memory_count=0,
                    align_score=None,
                    spread=None,
                )

            fpath = os.path.join(tmpdir, "XAUUSD", "2025-04-07.jsonl")
            with open(fpath) as f:
                lines = f.readlines()
            assert len(lines) == 3
            # Check candle indices increment
            records = [json.loads(l) for l in lines]
            assert records[0]["candle_index_in_kz"] == 0
            assert records[1]["candle_index_in_kz"] == 1
            assert records[2]["candle_index_in_kz"] == 2

    def test_kz_switch_resets_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(base_dir=tmpdir)
            logger.log_evaluation(
                symbol="XAUUSD", candle_time="2025-04-07T07:15:00Z",
                kill_zone="london",
                analysis_dict={"decision": "NO_TRADE", "reasoning": {}},
                session_memory_count=0, align_score=None, spread=None,
            )
            logger.log_evaluation(
                symbol="XAUUSD", candle_time="2025-04-07T13:15:00Z",
                kill_zone="ny",
                analysis_dict={"decision": "NO_TRADE", "reasoning": {}},
                session_memory_count=0, align_score=None, spread=None,
            )

            fpath_london = os.path.join(tmpdir, "XAUUSD", "2025-04-07.jsonl")
            with open(fpath_london) as f:
                records = [json.loads(l) for l in f.readlines()]
            # NY record should have candle_index 0 (new KZ)
            assert records[1]["kill_zone"] == "ny"
            assert records[1]["candle_index_in_kz"] == 0

    def test_full_reasoning_saved_for_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(base_dir=tmpdir)
            logger.log_evaluation(
                symbol="XAUUSD", candle_time="2025-04-07T08:00:00Z",
                kill_zone="london",
                analysis_dict={
                    "decision": "CANDIDATE",
                    "reasoning": {"overall_reasoning": "Strong bullish setup at 2760"},
                },
                session_memory_count=3, align_score=4, spread=0.20,
            )

            fpath = os.path.join(tmpdir, "XAUUSD", "2025-04-07.jsonl")
            with open(fpath) as f:
                record = json.loads(f.readline())
            assert "overall_reasoning" in record
            assert "Strong bullish" in record["overall_reasoning"]

    def test_no_trade_reasoning_sampled(self):
        """First NO_TRADE in KZ always saves reasoning; later ones are random."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(base_dir=tmpdir)
            # First NO_TRADE — should always save
            logger.log_evaluation(
                symbol="XAUUSD", candle_time="2025-04-07T07:15:00Z",
                kill_zone="london",
                analysis_dict={
                    "decision": "NO_TRADE",
                    "reasoning": {"overall_reasoning": "First eval reasoning"},
                },
                session_memory_count=0, align_score=2, spread=0.30,
            )

            fpath = os.path.join(tmpdir, "XAUUSD", "2025-04-07.jsonl")
            with open(fpath) as f:
                record = json.loads(f.readline())
            assert "overall_reasoning" in record


# ══════════════════════════════════════════════════���════════════════════════════
# Orchestrator Integration
# ══════════════════════════════════════════��══════════════════════════════════��═

class TestOrchestratorShadowHelpers:
    """Test the helper methods added to SessionOrchestrator."""

    def test_extract_align_score_parses_correctly(self):
        from src.components.orchestrator import SessionOrchestrator
        assert SessionOrchestrator._extract_align_score("Alignment score: 3/4 (bullish)") == 3
        assert SessionOrchestrator._extract_align_score("Alignment score: 0/4 (transitional)") == 0
        assert SessionOrchestrator._extract_align_score("Alignment score: 4/4 (bearish)") == 4

    def test_extract_align_score_no_match(self):
        from src.components.orchestrator import SessionOrchestrator
        assert SessionOrchestrator._extract_align_score("no score here") is None
        assert SessionOrchestrator._extract_align_score("") is None
