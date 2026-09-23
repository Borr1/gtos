"""Tests for Trade Data Capture."""

import json
from pathlib import Path

import pytest

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
from src.components.verification import VerificationCheck, VerificationResult
from src.components.permissions import ExecutionDenial


# Isolation fixture — _make_config() at line 65-77 defaults base_path to
# "knowledge_base/trade_records" and _record_path() at line 396 is called with
# that literal string. None of the current tests actually call save_trade_record
# with that default (they all override to tmp_path), but chdir(tmp_path) is a
# belt-and-braces guard so any future regression cannot write to live
# knowledge_base/trade_records.
@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mso_dict() -> dict:
    """Minimal MSO-like dict for testing."""
    return {
        "timestamp_utc": "2026-04-07T07:45:00+00:00",
        "timeframes": {
            "D1": {"structure": {"direction": "bullish"}},
            "H4": {"structure": {"direction": "bullish"}},
            "H1": {"order_blocks": []},
            "M15": {"atr_14": 5.0},
        },
        "session_levels": {"asian_high": 3050.0, "asian_low": 3030.0},
    }


def _make_ai_response() -> dict:
    """Minimal AI response dict for a CANDIDATE."""
    return {
        "decision": "CANDIDATE",
        "confidence_score": 80,
        "framework": "ob_retest",
        "reasoning": {
            "setup_grade": "A+",
            "daily_bias": {"direction": "bullish"},
            "overall_reasoning": "Strong setup.",
        },
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 3042.50,
            "stop_loss": 3035.00,
            "take_profit_1": 3053.75,
            "risk_reward_ratio": 1.5,
        },
    }


def _make_config(**overrides) -> dict:
    """Minimal config dict for trade capture."""
    cfg = {
        "trade_capture": {
            "enabled": True,
            "base_path": "knowledge_base/trade_records",
            "save_mso": True,
            "save_prompt": True,
            "save_rejected": True,
        },
    }
    cfg.update(overrides)
    return cfg


def _make_record(tmp_path=None) -> dict:
    """Create a standard trade record for testing."""
    return create_trade_record(
        symbol="XAUUSD",
        kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso=_make_mso_dict(),
        prompt_system="You are an institutional gold trader...",
        prompt_user="## Dynamic Market Data\n...",
        ai_response=_make_ai_response(),
        cross_instrument_context="XAUUSD D1: bullish",
        session_memory="- 07:15 UTC: NO_TRADE — waiting",
        config=_make_config(),
    )


def _make_verification_pass() -> VerificationResult:
    return VerificationResult(
        passed=True,
        checks=[
            VerificationCheck("m15_choch_exists", "PASS", "CHoCH found"),
            VerificationCheck("displacement_ratio", "PASS", "ratio=2.3 >= 1.5"),
            VerificationCheck("h1_poi_exists", "PASS", "OB at 3040-3045"),
            VerificationCheck("ob_zone", "PASS", "discount zone"),
            VerificationCheck("entry_in_ob", "PASS", "entry within OB"),
            VerificationCheck("sl_beyond_ob", "PASS", "SL below OB low"),
        ],
        blocked_by=None,
    )


def _make_verification_fail() -> VerificationResult:
    return VerificationResult(
        passed=False,
        checks=[
            VerificationCheck("m15_choch_exists", "PASS", "CHoCH found"),
            VerificationCheck("displacement_ratio", "FAIL", "ratio=1.2 < 1.5",
                              mso_value=1.2, ai_value=2.0),
        ],
        blocked_by="displacement_ratio",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateTradeRecord:
    def test_required_fields_present(self):
        record = _make_record()
        assert "metadata" in record
        assert "decision_pipeline" in record
        assert "context_at_decision" in record
        assert "mso" in record
        assert "prompt" in record
        assert "ai_response" in record
        assert "trade_parameters" in record
        assert "execution" in record
        assert "exit" in record

    def test_metadata_values(self):
        record = _make_record()
        meta = record["metadata"]
        assert meta["symbol"] == "XAUUSD"
        assert meta["kill_zone"] == "london"
        assert meta["date"] == "2026-04-07"
        assert "XAUUSD_2026-04-07_london_0745" == meta["trade_id"]
        assert meta["capture_version"] == CAPTURE_VERSION

    def test_pipeline_values(self):
        record = _make_record()
        pipe = record["decision_pipeline"]
        assert pipe["ai_decision"] == "CANDIDATE"
        assert pipe["ai_grade"] == "A+"
        assert pipe["ai_confidence"] == 80
        assert pipe["ai_direction"] == "LONG"
        assert pipe["ai_framework"] == "ob_retest"
        assert pipe["final_outcome"] == "PENDING"

    def test_context_captured(self):
        record = _make_record()
        ctx = record["context_at_decision"]
        assert "XAUUSD D1: bullish" in ctx["cross_instrument_context"]
        assert "07:15 UTC" in ctx["session_memory"]

    def test_mso_captured(self):
        record = _make_record()
        assert record["mso"]["timestamp_utc"] == "2026-04-07T07:45:00+00:00"

    def test_prompt_captured(self):
        record = _make_record()
        assert "institutional gold trader" in record["prompt"]["system_prompt"]
        assert "Dynamic Market Data" in record["prompt"]["user_message"]

    def test_execution_and_exit_null(self):
        record = _make_record()
        assert record["execution"] is None
        assert record["exit"] is None


class TestMSOSerialization:
    """Test MSO serialization with Pydantic models."""

    def test_dict_mso(self):
        record = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00Z",
            mso={"timeframes": {"D1": {}}},
            prompt_system="sys", prompt_user="usr",
            ai_response=_make_ai_response(),
            cross_instrument_context=None,
            session_memory="",
            config=_make_config(),
        )
        assert record["mso"] == {"timeframes": {"D1": {}}}

    def test_mso_omitted_when_disabled(self):
        cfg = _make_config()
        cfg["trade_capture"]["save_mso"] = False
        record = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00Z",
            mso=_make_mso_dict(),
            prompt_system="sys", prompt_user="usr",
            ai_response=_make_ai_response(),
            cross_instrument_context=None,
            session_memory="",
            config=cfg,
        )
        assert record["mso"] == "[omitted]"


class TestPromptCapture:
    def test_string_system_prompt(self):
        text = _extract_system_prompt_text("Hello system")
        assert text == "Hello system"

    def test_list_system_prompt(self):
        blocks = [
            {"type": "text", "text": "Part 1", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "Part 2"},
        ]
        text = _extract_system_prompt_text(blocks)
        assert "Part 1" in text
        assert "Part 2" in text

    def test_prompt_omitted_when_disabled(self):
        cfg = _make_config()
        cfg["trade_capture"]["save_prompt"] = False
        record = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00Z",
            mso={}, prompt_system="secret", prompt_user="secret",
            ai_response=_make_ai_response(),
            cross_instrument_context=None, session_memory="",
            config=cfg,
        )
        assert record["prompt"]["system_prompt"] == "[omitted]"
        assert record["prompt"]["user_message"] == "[omitted]"


class TestUpdateVerification:
    def test_pass(self):
        record = _make_record()
        update_verification(record, _make_verification_pass())
        v = record["decision_pipeline"]["level2_verification"]
        assert v["passed"] is True
        assert len(v["checks"]) == 6
        assert v["blocked_by"] is None

    def test_fail(self):
        record = _make_record()
        update_verification(record, _make_verification_fail())
        v = record["decision_pipeline"]["level2_verification"]
        assert v["passed"] is False
        assert v["blocked_by"] == "displacement_ratio"
        fail_check = next(c for c in v["checks"] if c["status"] == "FAIL")
        assert fail_check["name"] == "displacement_ratio"
        assert fail_check["mso_value"] == 1.2


class TestUpdateGateResults:
    def test_pass(self):
        record = _make_record()
        g3 = {"passed": True, "checks_run": ["daily_loss"], "details": {}}
        g1 = {"passed": True, "checks_run": ["grade"], "details": {}}
        update_gate_results(record, g3, g1)
        assert record["decision_pipeline"]["gate3_result"]["passed"] is True
        assert record["decision_pipeline"]["gate1_result"]["passed"] is True

    def test_fail(self):
        record = _make_record()
        g3 = {"passed": True, "checks_run": ["daily_loss"], "details": {}}
        g1 = {"passed": False, "checks_run": ["grade"], "details": {"denial_reason": "below_grade"}}
        update_gate_results(record, g3, g1)
        assert record["decision_pipeline"]["gate1_result"]["passed"] is False


class TestUpdateExecution:
    def test_adds_execution_data(self):
        record = _make_record()
        update_execution(record, {
            "executed": True,
            "timestamp": "2026-04-07T07:45:12Z",
            "entry_price_actual": 3042.60,
            "entry_spread": 0.25,
            "slippage": 0.10,
            "mt5_ticket": 0,
            "lot_size": 0.10,
            "risk_pct": 1.0,
        })
        assert record["execution"]["executed"] is True
        assert record["execution"]["entry_price_actual"] == 3042.60
        assert record["execution"]["mt5_ticket"] == 0


class TestUpdateExit:
    def test_adds_exit_data(self):
        record = _make_record()
        update_exit(record, {
            "exit_type": "CLOSED_TP1",
            "exit_price": 3053.80,
            "exit_time": "2026-04-07T08:30:00Z",
            "actual_r": 1.49,
            "hold_time_minutes": 45,
            "mfe_price": 3055.20,
            "mfe_r": 1.68,
            "mae_price": 3039.50,
            "mae_r": -0.40,
        })
        assert record["exit"]["exit_type"] == "CLOSED_TP1"
        assert record["exit"]["actual_r"] == 1.49


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        record = _make_record()
        path = save_trade_record(record, str(tmp_path / "trade_records"))
        assert path is not None
        assert Path(path).exists()

        loaded = load_trade_record(path)
        assert loaded["metadata"]["trade_id"] == record["metadata"]["trade_id"]
        assert loaded["decision_pipeline"] == record["decision_pipeline"]

    def test_directory_creation(self, tmp_path):
        record = _make_record()
        deep_path = tmp_path / "a" / "b" / "c" / "trade_records"
        path = save_trade_record(record, str(deep_path))
        assert path is not None
        assert Path(path).exists()

    def test_atomic_write_pattern(self, tmp_path):
        """Verify no .tmp files left behind after successful write."""
        record = _make_record()
        base = str(tmp_path / "trade_records")
        save_trade_record(record, base)
        tmp_files = list(Path(base).rglob("*.tmp"))
        assert len(tmp_files) == 0

    def test_file_path_structure(self, tmp_path):
        record = _make_record()
        base = str(tmp_path / "trade_records")
        path = save_trade_record(record, base)
        assert "XAUUSD" in path
        assert "2026-04-07_london_0745.json" in path


class TestRejectedRecords:
    def test_rejected_l2_saved(self, tmp_path):
        record = _make_record()
        update_verification(record, _make_verification_fail())
        record["decision_pipeline"]["final_outcome"] = "REJECTED_L2"
        base = str(tmp_path / "trade_records")
        path = save_trade_record(record, base)
        assert path is not None
        loaded = load_trade_record(path)
        assert loaded["decision_pipeline"]["final_outcome"] == "REJECTED_L2"
        assert loaded["decision_pipeline"]["level2_verification"]["passed"] is False

    def test_rejected_gate1_saved(self, tmp_path):
        record = _make_record()
        update_verification(record, _make_verification_pass())
        g3 = {"passed": True, "checks_run": [], "details": {}}
        g1 = {"passed": False, "checks_run": ["grade"],
               "details": {"denial_reason": "below_grade_threshold"}}
        update_gate_results(record, g3, g1)
        record["decision_pipeline"]["final_outcome"] = "REJECTED_GATE1_SAFETY"
        base = str(tmp_path / "trade_records")
        path = save_trade_record(record, base)
        loaded = load_trade_record(path)
        assert loaded["decision_pipeline"]["final_outcome"] == "REJECTED_GATE1_SAFETY"


class TestDisabledCapture:
    def test_disabled_config_no_save(self, tmp_path):
        """When enabled=false in config, record still created but save is
        gated by the orchestrator. Test that create_trade_record works
        regardless — it's the orchestrator that checks enabled."""
        cfg = _make_config()
        cfg["trade_capture"]["enabled"] = False
        record = create_trade_record(
            symbol="XAUUSD", kill_zone="london",
            candle_time="2026-04-07T07:45:00Z",
            mso={}, prompt_system="sys", prompt_user="usr",
            ai_response=_make_ai_response(),
            cross_instrument_context=None, session_memory="",
            config=cfg,
        )
        # Record is created even when disabled — orchestrator gates saving
        assert record["metadata"]["trade_id"] is not None


class TestRecordPath:
    def test_path_format(self):
        record = _make_record()
        path = _record_path(record, "knowledge_base/trade_records")
        assert path == Path("knowledge_base/trade_records/XAUUSD/2026-04-07_london_0745.json")

    def test_path_includes_candidate_id_when_present(self):
        record = _make_record()
        record["metadata"]["candidate_id"] = "broadorigin_abc123"
        path = _record_path(record, "knowledge_base/trade_records")
        assert path == Path(
            "knowledge_base/trade_records/XAUUSD/"
            "2026-04-07_london_0745_broadorigin_abc123.json"
        )


class TestBuildGateResults:
    def test_gate3_pass(self):
        class FakeMT5:
            def is_connected(self): return True
            def get_tick(self, sym):
                class T:
                    spread_cents = 15
                return T()

        session = {"daily_pnl_pct": 0.0, "trades_today": 0,
                    "current_kill_zone": "london", "trades_london": 0}
        result = build_gate3_result(None, session, FakeMT5())
        assert result["passed"] is True
        assert result["details"]["mt5_connected"] is True

    def test_gate3_fail(self):
        class FakeMT5:
            def is_connected(self): return True
            def get_tick(self, sym):
                class T:
                    spread_cents = 15
                return T()

        denial = ExecutionDenial("gate3_circuit_breaker", "daily_loss_limit",
                                  {"daily_pnl_pct": -2.5})
        session = {"daily_pnl_pct": -2.5, "trades_today": 0,
                    "current_kill_zone": "london", "trades_london": 0}
        result = build_gate3_result(denial, session, FakeMT5())
        assert result["passed"] is False
        assert result["details"]["denial_reason"] == "daily_loss_limit"

    def test_gate1_pass(self):
        result = build_gate1_result(None, None, None)
        assert result["passed"] is True

    def test_gate1_fail(self):
        denial = ExecutionDenial("gate1_safety", "below_grade_threshold: B+",
                                  {"grade": "B+"})
        result = build_gate1_result(denial, None, None)
        assert result["passed"] is False
        assert result["details"]["denial_reason"] == "below_grade_threshold: B+"
