"""Tests for A3 trade record instrumentation (CAPTURE_VERSION 1.1).

Covers the 10 CAND-time + 3 exit-time fields added for Phase 2 sniper
subset analysis. All tests are pure-unit (no MT5, no AI call, no disk).

See research/a3_trade_record_instrumentation/PHASE_A_RECON.md for the
field inventory and source mapping.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components.trade_capture import (
    CAPTURE_VERSION,
    EXIT_REASON_BE,
    EXIT_REASON_MANUAL,
    EXIT_REASON_SL,
    EXIT_REASON_TIMEOUT,
    EXIT_REASON_TP1,
    EXIT_REASON_TP2,
    EXIT_REASON_UNKNOWN,
    _canonical_exit_reason,
    _kill_zone_bucket_15min,
    _nearest_opposing_ob_touch,
    _count_unfilled_fvgs,
    _infer_sl_source,
    create_trade_record,
    load_trade_record,
    save_trade_record,
    update_exit,
    update_m5_refinement,
    update_verification,
)
from src.components.verification import (
    VerificationCheck,
    VerificationResult,
)
from src.models.market_state_models import (
    BreakerBlock,
    FairValueGap,
    OrderBlock,
)


# Isolation — conftest write guards would fire otherwise.
@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _config(detector_version: str = "v2_shadow") -> dict:
    return {
        "trade_capture": {
            "enabled": True,
            "base_path": "knowledge_base/trade_records",
            "save_mso": True,
            "save_prompt": True,
            "save_rejected": True,
        },
        "market_state": {
            "detector_version": detector_version,
        },
    }


def _mso_dict(
    h1_obs=None,
    h1_fvgs=None,
    m15_fvgs=None,
) -> dict:
    """Build a compact MSO-like dict for instrumentation tests."""
    return {
        "timestamp_utc": "2026-04-24T07:15:00+00:00",
        "timeframes": {
            "D1": {"structure": {"direction": "bullish"}},
            "H4": {"structure": {"direction": "bullish"}},
            "H1": {
                "order_blocks": h1_obs or [],
                "fair_value_gaps": h1_fvgs or [],
            },
            "M15": {
                "atr_14": 5.0,
                "fair_value_gaps": m15_fvgs or [],
            },
        },
        "session_levels": {"asian_high": 3050.0, "asian_low": 3030.0},
    }


def _ai_response(
    direction: str = "LONG",
    entry: float = 3042.50,
    sl: float = 3035.00,
    sl_buffer: float = 0.15,
    framework: str = "ob_retest",
) -> dict:
    return {
        "decision": "CANDIDATE",
        "confidence_score": 80,
        "framework": framework,
        "reasoning": {
            "setup_grade": "A+",
            "daily_bias": {"direction": "bullish"},
            "overall_reasoning": "Setup.",
        },
        "trade_parameters": {
            "direction": direction,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": entry + 11.25 if direction == "LONG" else entry - 11.25,
            "take_profit_2": 0.0,
            "take_profit_3": 0.0,
            "sl_buffer_applied": sl_buffer,
            "risk_reward_ratio": 1.5,
        },
    }


def _make_record(
    ai_response=None,
    mso=None,
    config=None,
    kill_zone: str = "london",
    candle_time: str = "2026-04-24T07:15:00+00:00",
) -> dict:
    return create_trade_record(
        symbol="XAUUSD",
        kill_zone=kill_zone,
        candle_time=candle_time,
        mso=mso or _mso_dict(),
        prompt_system="system",
        prompt_user="user",
        ai_response=ai_response or _ai_response(),
        cross_instrument_context=None,
        session_memory="",
        config=config or _config(),
    )


def _ob(
    zone_type: str, low: float, high: float,
    touch_count: int = 0, mitigated: bool = False,
) -> dict:
    """A dict-shaped OB matching market_state_models.OrderBlock (dict-MSO path)."""
    return {
        "type": zone_type, "low": low, "high": high,
        "open": (low + high) / 2, "close": (low + high) / 2,
        "formation_index": 0, "formation_time": "2026-04-20T10:00:00",
        "causing_bos_index": 0, "mitigated": mitigated,
        "causing_event_type": "BOS", "touch_count": touch_count,
    }


def _real_ob(
    zone_type: str, low: float, high: float,
    touch_count: int = 0, mitigated: bool = False,
) -> OrderBlock:
    """A real pydantic OrderBlock for the matched_ob injection test."""
    return OrderBlock(
        type=zone_type, low=low, high=high,
        open=(low + high) / 2, close=(low + high) / 2,
        formation_index=0, formation_time="2026-04-20T10:00:00",
        causing_bos_index=0, mitigated=mitigated,
        touch_count=touch_count,
    )


# ---------------------------------------------------------------------------
# Test 1 — target_ob_touch_count on CAND
# ---------------------------------------------------------------------------

class TestTouchCount:
    def test_target_ob_touch_count_populated_on_cand(self):
        """Synthetic CAND with touch=2 OB -> record has touch_count=2."""
        record = _make_record()
        vr = VerificationResult(
            passed=True,
            checks=[VerificationCheck("h1_poi_exists", "PASS", "OB matched")],
            blocked_by=None,
            matched_ob=_real_ob("bullish", low=3040.0, high=3045.0, touch_count=2),
        )
        update_verification(record, vr)
        inst = record["instrumentation"]
        assert inst["target_ob_touch_count"] == 2
        assert inst["target_ob_zone"]["low"] == 3040.0
        assert inst["target_ob_zone"]["high"] == 3045.0
        assert inst["target_ob_zone"]["type"] == "bullish"

    def test_target_ob_touch_count_null_when_no_match(self):
        """No matched OB -> touch_count stays None, no exception."""
        record = _make_record()
        vr = VerificationResult(
            passed=False,
            checks=[VerificationCheck("h1_poi_exists", "FAIL", "no match")],
            blocked_by="h1_poi_exists",
            matched_ob=None,
        )
        update_verification(record, vr)
        inst = record["instrumentation"]
        assert inst["target_ob_touch_count"] is None
        assert inst["target_ob_zone"] is None

    def test_target_ob_touch_count_breaker_fallback(self):
        """Breaker-matched setups report zone but no touch_count."""
        record = _make_record()
        bb = BreakerBlock(
            zone_high=3050.0, zone_low=3045.0,
            direction="bullish", original_ob_direction="bearish",
            formation_time="2026-04-18T10:00:00",
            mitigation_time="2026-04-19T10:00:00",
            causing_event="BOS",
        )
        vr = VerificationResult(
            passed=True, checks=[], blocked_by=None,
            matched_ob=None, matched_breaker=bb,
        )
        update_verification(record, vr)
        inst = record["instrumentation"]
        assert inst["target_ob_touch_count"] is None
        assert inst["target_ob_zone"]["low"] == 3045.0
        assert inst["target_ob_zone"]["high"] == 3050.0
        assert inst["target_ob_zone"]["type"].startswith("breaker_")


# ---------------------------------------------------------------------------
# Test 2 — m5_refined snapshot
# ---------------------------------------------------------------------------

class TestM5Refinement:
    def test_m5_refined_snapshot_when_applied(self):
        """With m5 refinement applied -> record has m5_refined=True + details."""
        record = _make_record()
        m5_out = {
            "applied": True,
            "m5_result": {"decision": "REFINE", "m5_quality": "strong"},
            "overrides": {
                "m5_quality": "strong",
                "m5_raw_sl_dist": 7.50,
                "sl_distance": 3.20,
                "take_profit_1": 3045.30,
            },
        }
        update_m5_refinement(record, m5_out)
        inst = record["instrumentation"]
        assert inst["m5_refined"] is True
        assert inst["m5_refinement_details"]["applied"] is True
        assert inst["m5_refinement_details"]["overrides"]["m5_quality"] == "strong"
        assert inst["m5_refinement_details"]["overrides"]["sl_distance"] == 3.20
        assert inst["m5_refinement_details"]["m5_result_decision"] == "REFINE"

    def test_m5_refined_snapshot_when_skipped(self):
        """M5 skipped -> record has m5_refined=False + result decision preserved."""
        record = _make_record()
        m5_out = {
            "applied": False,
            "m5_result": {"decision": "SKIP_NO_STRUCTURE"},
            "overrides": None,
        }
        update_m5_refinement(record, m5_out)
        inst = record["instrumentation"]
        assert inst["m5_refined"] is False
        assert inst["m5_refinement_details"]["applied"] is False
        assert inst["m5_refinement_details"]["m5_result_decision"] == "SKIP_NO_STRUCTURE"

    def test_m5_snapshot_tolerates_schema_drift(self):
        """Malformed m5_out -> no exception, instrumentation unchanged or safe."""
        record = _make_record()
        # Initial state
        assert record["instrumentation"]["m5_refined"] is False
        # Passing empty / None should not crash
        update_m5_refinement(record, {})
        update_m5_refinement(record, None)  # type: ignore[arg-type]
        # m5_refined stays False throughout
        assert record["instrumentation"]["m5_refined"] is False


# ---------------------------------------------------------------------------
# Test 3 — realized_R on TP1 exit
# ---------------------------------------------------------------------------

class TestRealizedR:
    def test_realized_R_populated_on_tp_exit(self):
        """Synthetic TP1 fill -> realized_R aliased from actual_r."""
        record = _make_record()
        update_exit(record, {
            "exit_type": "tp_hit",
            "exit_price": 3045.25,
            "exit_time": "2026-04-24T08:00:00+00:00",
            "actual_r": 1.5,
            "hold_time_minutes": 45,
            "mfe_price": 3045.25,
            "mae_price": 3041.00,
            "mfe_r": 1.5,
            "mae_r": -0.2,
            "partial_closes": [],
        })
        exit_data = record["exit"]
        assert exit_data["realized_R"] == 1.5
        assert exit_data["time_in_trade_minutes"] == 45
        assert exit_data["exit_reason"] == EXIT_REASON_TP1
        # Original keys preserved
        assert exit_data["actual_r"] == 1.5
        assert exit_data["hold_time_minutes"] == 45

    def test_realized_R_negative_on_SL(self):
        record = _make_record()
        update_exit(record, {
            "exit_type": "sl_hit",
            "exit_price": 3035.00,
            "exit_time": "2026-04-24T08:00:00+00:00",
            "actual_r": -1.0,
            "hold_time_minutes": 30,
        })
        exit_data = record["exit"]
        assert exit_data["realized_R"] == -1.0
        assert exit_data["exit_reason"] == EXIT_REASON_SL


# ---------------------------------------------------------------------------
# Test 4 — exit_reason enum normalization
# ---------------------------------------------------------------------------

class TestExitReason:
    @pytest.mark.parametrize("exit_type,expected", [
        ("tp_hit", EXIT_REASON_TP1),
        ("TP1", EXIT_REASON_TP1),
        ("TP2", EXIT_REASON_TP2),
        ("tp_hit_2", EXIT_REASON_TP2),
        ("sl_hit", EXIT_REASON_SL),
        ("SL_HIT", EXIT_REASON_SL),
        ("breakeven", EXIT_REASON_BE),
        ("BE", EXIT_REASON_BE),
        ("timeout_2h", EXIT_REASON_TIMEOUT),
        ("session_timeout", EXIT_REASON_TIMEOUT),
        ("manual_close", EXIT_REASON_MANUAL),
        ("broker_closed", EXIT_REASON_UNKNOWN),
        ("", EXIT_REASON_UNKNOWN),
        (None, EXIT_REASON_UNKNOWN),
        ("garbage", EXIT_REASON_UNKNOWN),
    ])
    def test_canonical_reason_mapping(self, exit_type, expected):
        assert _canonical_exit_reason(exit_type) == expected

    def test_update_exit_respects_preset_reason(self):
        record = _make_record()
        update_exit(record, {"exit_type": "tp_hit", "exit_reason": EXIT_REASON_MANUAL})
        # Valid preset is respected even though exit_type suggests TP1
        assert record["exit"]["exit_reason"] == EXIT_REASON_MANUAL

    def test_update_exit_ignores_invalid_preset(self):
        record = _make_record()
        update_exit(record, {"exit_type": "tp_hit", "exit_reason": "NOT_AN_ENUM"})
        # Invalid preset falls through to exit_type derivation
        assert record["exit"]["exit_reason"] == EXIT_REASON_TP1

    def test_update_exit_classifies_broker_sl_close_from_mt5_deal(self):
        record = _make_record()
        update_exit(record, {
            "exit_type": "broker_closed",
            "broker_deal_reconciled": True,
            "broker_close_reason": 4,
            "broker_close_comment": "[sl 97.506]",
        })
        assert record["exit"]["exit_reason"] == EXIT_REASON_SL

    def test_update_exit_broker_deal_overrides_stale_manual_reason(self):
        record = _make_record()
        update_exit(record, {
            "exit_type": "broker_closed",
            "exit_reason": EXIT_REASON_MANUAL,
            "broker_deal_reconciled": True,
            "broker_close_reason": 4,
            "broker_close_comment": "[sl 93.912]",
        })
        assert record["exit"]["exit_reason"] == EXIT_REASON_SL


# ---------------------------------------------------------------------------
# Test 5 — backward compatibility with pre-1.1 records
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    def test_pre_instrumentation_record_loads_without_exception(self, tmp_path):
        """A v1.0-shaped record on disk -> load_trade_record returns it without KeyError."""
        legacy_record = {
            "metadata": {
                "trade_id": "XAUUSD_2026-04-01_london_0715",
                "date": "2026-04-01",
                "symbol": "XAUUSD",
                "kill_zone": "london",
                "candle_time": "2026-04-01T07:15:00+00:00",
                "capture_version": "1.0",
                "system_version": "abcd123",
            },
            "decision_pipeline": {
                "ai_decision": "CANDIDATE",
                "ai_grade": "A",
                "ai_confidence": 75,
                "ai_direction": "LONG",
                "ai_framework": "ob_retest",
                "level2_verification": None,
                "gate3_result": None,
                "gate1_result": None,
                "final_outcome": "REJECTED_L2",
            },
            "context_at_decision": {"cross_instrument_context": "", "session_memory": ""},
            "mso": {"timeframes": {}, "timestamp_utc": "2026-04-01T07:15:00+00:00"},
            "prompt": {"system_prompt": "sys", "user_message": "usr"},
            "ai_response": {"decision": "CANDIDATE"},
            "trade_parameters": {"direction": "LONG", "entry_price": 3000.0},
            "execution": None,
            "exit": None,
            # NO instrumentation block — v1.0 record
        }
        path = tmp_path / "legacy.json"
        path.write_text(json.dumps(legacy_record), encoding="utf-8")
        loaded = load_trade_record(str(path))
        # Must not raise. Legacy records are loadable as-is.
        assert loaded["metadata"]["capture_version"] == "1.0"
        # Legacy records have no instrumentation block
        assert "instrumentation" not in loaded
        # Phase-2 queries that expect instrumentation MUST use .get(), not []:
        assert loaded.get("instrumentation") is None

    def test_pre_instrumentation_record_tolerates_update_helpers(self, tmp_path):
        """A v1.0 record fed into v1.1 update helpers -> instrumentation auto-added."""
        legacy_record = {
            "metadata": {"capture_version": "1.0", "trade_id": "t", "symbol": "XAUUSD",
                         "date": "2026-04-01", "kill_zone": "london",
                         "candle_time": "2026-04-01T07:15:00+00:00"},
            "decision_pipeline": {"final_outcome": "PENDING",
                                  "ai_decision": "CANDIDATE", "ai_framework": "ob_retest",
                                  "level2_verification": None,
                                  "gate3_result": None, "gate1_result": None,
                                  "ai_grade": "A", "ai_confidence": 80, "ai_direction": "LONG"},
        }
        vr = VerificationResult(
            passed=True, checks=[], blocked_by=None,
            matched_ob=_real_ob("bullish", 3040.0, 3045.0, touch_count=1),
        )
        update_verification(legacy_record, vr)
        # instrumentation block created on demand
        assert legacy_record["instrumentation"]["target_ob_touch_count"] == 1

    def test_load_trade_record_on_new_v11_record_roundtrip(self, tmp_path):
        """Write a v1.1 record + load it back -> instrumentation round-trips."""
        record = _make_record()
        # Add verification + m5 + exit so every v1.1 field lands
        update_verification(record, VerificationResult(
            passed=True, checks=[], blocked_by=None,
            matched_ob=_real_ob("bullish", 3040.0, 3045.0, touch_count=3),
        ))
        update_m5_refinement(record, {
            "applied": True,
            "m5_result": {"decision": "REFINE"},
            "overrides": {"sl_distance": 3.0},
        })
        update_exit(record, {
            "exit_type": "sl_hit", "actual_r": -1.0, "hold_time_minutes": 15,
        })
        saved = save_trade_record(record, str(tmp_path))
        assert saved is not None
        loaded = load_trade_record(saved)
        assert loaded["metadata"]["capture_version"] == "1.1"
        assert loaded["instrumentation"]["target_ob_touch_count"] == 3
        assert loaded["instrumentation"]["m5_refined"] is True
        assert loaded["exit"]["exit_reason"] == EXIT_REASON_SL
        assert loaded["exit"]["realized_R"] == -1.0


# ---------------------------------------------------------------------------
# Test 6 — kill_zone_bucket_15min derivation
# ---------------------------------------------------------------------------

class TestKillZoneBucket:
    @pytest.mark.parametrize("kz,candle_time,expected", [
        ("london", "2026-04-24T07:15:00+00:00", "london_0715"),
        ("london", "2026-04-24T07:00:00+00:00", "london_0700"),
        ("ny", "2026-04-24T13:30:00+00:00", "ny_1330"),
        ("tokyo", "2026-04-24T00:00:00+00:00", "tokyo_0000"),
        ("ny", "2026-04-24T15:45:00Z", "ny_1545"),
    ])
    def test_bucket_derivation(self, kz, candle_time, expected):
        assert _kill_zone_bucket_15min(kz, candle_time) == expected

    def test_bucket_unknown_on_bad_time(self):
        assert _kill_zone_bucket_15min("london", "not-an-iso-date") == "london_unknown"

    def test_bucket_in_record(self):
        record = _make_record(kill_zone="london",
                              candle_time="2026-04-24T07:15:00+00:00")
        assert record["instrumentation"]["kill_zone_bucket_15min"] == "london_0715"


# ---------------------------------------------------------------------------
# Test 7 — FVG counts + opposing OB touch
# ---------------------------------------------------------------------------

class TestMSODerivedFields:
    def test_fvg_counts_populated(self):
        h1_fvgs = [
            {"type": "bullish", "top": 3050.0, "bottom": 3045.0, "midpoint": 3047.5,
             "candle_indices": [1, 2, 3], "formation_time": "x", "filled": False},
            {"type": "bearish", "top": 3020.0, "bottom": 3015.0, "midpoint": 3017.5,
             "candle_indices": [5, 6, 7], "formation_time": "y", "filled": True},
            {"type": "bullish", "top": 3000.0, "bottom": 2995.0, "midpoint": 2997.5,
             "candle_indices": [8, 9, 10], "formation_time": "z", "filled": False},
        ]
        mso = _mso_dict(h1_fvgs=h1_fvgs, m15_fvgs=h1_fvgs[:1])
        record = _make_record(mso=mso)
        # 2 unfilled H1 FVGs (the bearish is filled)
        assert record["instrumentation"]["h1_fvg_unfilled_count"] == 2
        assert record["instrumentation"]["m15_fvg_unfilled_count"] == 1

    def test_fvg_count_handles_empty_mso(self):
        record = _make_record(mso={"timeframes": {}})
        assert record["instrumentation"]["h1_fvg_unfilled_count"] == 0
        assert record["instrumentation"]["m15_fvg_unfilled_count"] == 0

    def test_opposing_ob_touch_for_long(self):
        """LONG at 3000 -> nearest bearish (opposing) OB ABOVE entry."""
        h1_obs = [
            _ob("bullish", low=2990.0, high=2995.0, touch_count=0),  # same-side, below
            _ob("bearish", low=3005.0, high=3010.0, touch_count=1),  # opposing, closer
            _ob("bearish", low=3030.0, high=3035.0, touch_count=3),  # opposing, farther
        ]
        mso = _mso_dict(h1_obs=h1_obs)
        record = _make_record(
            mso=mso,
            ai_response=_ai_response(direction="LONG", entry=3000.0),
        )
        assert record["instrumentation"]["h1_opp_ob_touch"] == 1

    def test_opposing_ob_touch_for_short(self):
        """SHORT at 3020 -> nearest bullish (opposing) OB BELOW entry."""
        h1_obs = [
            _ob("bearish", low=3030.0, high=3035.0, touch_count=0),  # same-side, above
            _ob("bullish", low=3000.0, high=3005.0, touch_count=2),  # opposing, closer
            _ob("bullish", low=2990.0, high=2995.0, touch_count=0),  # opposing, farther
        ]
        mso = _mso_dict(h1_obs=h1_obs)
        record = _make_record(
            mso=mso,
            ai_response=_ai_response(direction="SHORT", entry=3020.0,
                                      sl=3028.0, sl_buffer=0.10, framework="ob_retest"),
        )
        assert record["instrumentation"]["h1_opp_ob_touch"] == 2

    def test_opposing_ob_touch_null_when_none(self):
        record = _make_record(mso=_mso_dict(h1_obs=[]))
        assert record["instrumentation"]["h1_opp_ob_touch"] is None

    def test_opposing_ob_touch_skips_mitigated(self):
        h1_obs = [
            _ob("bearish", low=3005.0, high=3010.0, touch_count=5, mitigated=True),
            _ob("bearish", low=3030.0, high=3035.0, touch_count=1, mitigated=False),
        ]
        mso = _mso_dict(h1_obs=h1_obs)
        record = _make_record(
            mso=mso,
            ai_response=_ai_response(direction="LONG", entry=3000.0),
        )
        # First (closer) is mitigated, so the far one at touch=1 wins
        assert record["instrumentation"]["h1_opp_ob_touch"] == 1


# ---------------------------------------------------------------------------
# Test 8 — sl_source inference
# ---------------------------------------------------------------------------

class TestSlSource:
    def test_ob_retest_with_buffer_is_ob(self):
        assert _infer_sl_source("ob_retest", 0.15) == "ob"

    def test_ob_retest_without_buffer_is_atr_fallback(self):
        assert _infer_sl_source("ob_retest", 0.0) == "atr_fallback"
        assert _infer_sl_source("ob_retest", None) == "atr_fallback"

    def test_other_framework_with_buffer_is_structural(self):
        assert _infer_sl_source("breaker_retest", 0.2) == "structural"

    def test_other_framework_without_buffer_is_atr_fallback(self):
        assert _infer_sl_source("session_sweep", 0.0) == "atr_fallback"

    def test_no_framework_is_unknown(self):
        assert _infer_sl_source("", 0.15) == "unknown"
        assert _infer_sl_source(None, 0.15) == "unknown"

    def test_record_sl_source_populated(self):
        record = _make_record(ai_response=_ai_response(sl_buffer=0.15, framework="ob_retest"))
        assert record["instrumentation"]["sl_source"] == "ob"
        assert record["instrumentation"]["sl_buffer_applied"] == 0.15


# ---------------------------------------------------------------------------
# Test 9 — detector_version snapshot
# ---------------------------------------------------------------------------

class TestDetectorVersion:
    def test_detector_v1(self):
        record = _make_record(config=_config(detector_version="v1"))
        assert record["instrumentation"]["detector_version_at_eval"] == "v1"

    def test_detector_v2_shadow(self):
        record = _make_record(config=_config(detector_version="v2_shadow"))
        assert record["instrumentation"]["detector_version_at_eval"] == "v2_shadow"

    def test_detector_missing(self):
        record = _make_record(config={"trade_capture": {"enabled": True,
                                                         "base_path": "p",
                                                         "save_mso": True,
                                                         "save_prompt": True}})
        assert record["instrumentation"]["detector_version_at_eval"] is None


# ---------------------------------------------------------------------------
# Test 10 — CAPTURE_VERSION bump
# ---------------------------------------------------------------------------

class TestCaptureVersion:
    def test_capture_version_is_1_1(self):
        assert CAPTURE_VERSION == "1.1"

    def test_new_records_stamp_1_1(self):
        record = _make_record()
        assert record["metadata"]["capture_version"] == "1.1"
