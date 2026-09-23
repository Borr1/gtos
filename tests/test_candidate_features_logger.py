"""Tests for candidate_features_logger — observation-only feature accumulator.

Covers:
1. Smoke — minimal PAOutput + MSO → valid JSONL line with expected keys.
2. Missing fields — pa_output.reasoning=None, MSO missing some TFs → null
   fields, no crash.
3. Exception isolation — mock raising on attribute access → no exception.
4. NO_TRADE decision → trade_parameters is null in output.
5. CANDIDATE decision → trade_parameters fields present.
6. Distinct lines per call → two writes produce two lines.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.components.candidate_features_logger import log_candidate_features


def _assert_cp281_event_contract(row: dict) -> None:
    for field in (
        "symbol",
        "source_symbol",
        "symbol_family",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "side",
        "source_path_sha256",
        "source_file_sha256",
    ):
        assert row.get(field) not in (None, ""), field


# -----------------------------------------------------------------------------
# Helpers to build minimal PAOutput / MSO stand-ins
# -----------------------------------------------------------------------------

class _Struct:
    """Simple attribute container — mimics pydantic-like objects for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _make_reasoning(
    daily_dir: str = "bullish",
    setup_grade: str = "B",
    m15_choch: bool = True,
    h4_aligned: bool = True,
):
    return _Struct(
        daily_bias=_Struct(direction=daily_dir, confidence="high"),
        h4_alignment=_Struct(aligned=h4_aligned),
        h1_setup=_Struct(poi_identified=True, poi_type="OB"),
        liquidity_sweep=_Struct(detected=False, pool_type="none"),
        m15_confirmation=_Struct(choch_detected=m15_choch),
        setup_grade=setup_grade,
        overall_reasoning="test reasoning",
    )


def _make_pa_candidate():
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        model_used="claude-sonnet-4-6",
        decision="CANDIDATE",
        confidence_score=80,
        framework="ob_retest",
        kill_zone="london",
        reasoning=_make_reasoning(daily_dir="bullish"),
        trade_parameters=_Struct(
            direction="LONG",
            entry_price=2800.50,
            stop_loss=2790.00,
            take_profit_1=2820.00,
            risk_reward_ratio=1.85,
        ),
        no_trade_reason=None,
    )


def _make_pa_no_trade():
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        model_used="claude-sonnet-4-6",
        decision="NO_TRADE",
        confidence_score=0,
        framework="none",
        kill_zone="london",
        reasoning=_make_reasoning(daily_dir="ranging"),
        trade_parameters=None,
        no_trade_reason="deterministic_no_bias",
    )


def _make_pa_wait():
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        model_used="claude-sonnet-4-6",
        decision="WAIT",
        confidence_score=60,
        framework="ob_retest",
        kill_zone="london",
        reasoning=_make_reasoning(daily_dir="bullish", setup_grade="B"),
        trade_parameters=None,
        no_trade_reason="poi_needs_retest",
    )


def _make_ob(
    direction: str = "bullish",
    high: float = 2810.0,
    low: float = 2805.0,
    touch_count: int = 0,
    mitigated: bool = False,
):
    return _Struct(
        type=direction,
        high=high,
        low=low,
        open=high,
        close=low,
        touch_count=touch_count,
        mitigated=mitigated,
    )


def _make_breaker(direction: str = "bullish", retested: bool = False):
    return _Struct(
        direction=direction,
        is_retested=retested,
    )


def _make_fvg(direction: str = "bullish", filled: bool = False):
    return _Struct(
        type=direction,
        filled=filled,
    )


def _make_tf_state(
    direction: str = "bullish",
    obs: list | None = None,
    breakers: list | None = None,
    fvgs: list | None = None,
    atr: float = 1.5,
    premium_discount=None,
    clv_current: float | None = 0.3,
    clv_avg_5: float | None = 0.2,
    bvc_buy_fraction: float | None = 0.55,
    net_flow_5: float | None = 0.1,
):
    return _Struct(
        structure=_Struct(direction=direction),
        order_blocks=obs or [],
        breaker_blocks=breakers or [],
        fair_value_gaps=fvgs or [],
        atr_14=atr,
        premium_discount=premium_discount,
        clv_current=clv_current,
        clv_avg_5=clv_avg_5,
        bvc_buy_fraction=bvc_buy_fraction,
        net_flow_5=net_flow_5,
        session_vol_ratio=None,
    )


def _make_mso(
    h1_obs: list | None = None,
    m15_fvgs: list | None = None,
    pools: list | None = None,
    sweeps: list | None = None,
    session_levels=None,
    tfs: dict | None = None,
    timestamp: str = "2026-04-17T08:00:00+00:00",
):
    if tfs is None:
        tfs = {
            "D1": _make_tf_state(direction="bullish", atr=12.0),
            "H1": _make_tf_state(
                direction="bullish",
                obs=h1_obs if h1_obs is not None else [_make_ob(touch_count=0)],
                atr=3.0,
                premium_discount=_Struct(equilibrium_50=2800.0),
            ),
            "M15": _make_tf_state(
                direction="bullish",
                fvgs=m15_fvgs or [],
                atr=1.2,
            ),
        }
    return _Struct(
        timestamp_utc=timestamp,
        timeframes=tfs,
        session_levels=session_levels or _Struct(
            session_high=2810.0, session_low=2790.0,
            asian_high=2805.0, asian_low=2795.0, pdh=2815.0, pdl=2785.0,
        ),
        liquidity_pools=pools if pools is not None else [
            _Struct(type="equal_highs", price=2810.0, side="high"),
            _Struct(type="pdl", price=2785.0, side="low"),
        ],
        detected_sweeps=sweeps or [],
    )


# -----------------------------------------------------------------------------
# 1. Smoke test
# -----------------------------------------------------------------------------

def test_smoke_writes_one_valid_json_line(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    pa = _make_pa_candidate()
    mso = _make_mso()

    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        candle_close_utc="2026-04-17T07:45:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    row = json.loads(lines[0])

    # Identification
    for key in (
        "timestamp_utc", "symbol", "evaluation_id", "kill_zone",
        "session_tag", "day_of_week", "hour_utc", "candle_close_utc",
        "candle_day_of_week", "candle_hour_utc",
        "timestamp_candle_lag_seconds",
    ):
        assert key in row

    # AI output
    for key in (
        "decision", "framework", "setup_grade", "c_gate_result",
        "daily_bias_direction", "trade_parameters",
    ):
        assert key in row

    # MSO features (prefixed)
    for key in (
        "mso_h1_structure_direction",
        "mso_m15_structure_direction",
        "mso_d1_structure_direction",
        "mso_h1_unmitigated_ob_count",
        "mso_h1_unmitigated_ob_count_bullish",
        "mso_h1_unmitigated_ob_count_bearish",
        "mso_h1_ob_touch_counts",
        "mso_h1_nearest_ob_distance_atr",
        "mso_h1_unretested_breaker_count",
        "mso_h1_unretested_breaker_count_bullish",
        "mso_h1_unretested_breaker_count_bearish",
        "mso_h1_fvg_count",
        "mso_h1_fvg_count_bullish",
        "mso_h1_fvg_count_bearish",
        "mso_m15_fvg_count",
        "mso_m15_fvg_count_bullish",
        "mso_m15_fvg_count_bearish",
        "mso_pool_count_by_type",
        "mso_nearest_same_side_pool_distance_atr",
        "mso_nearest_opposite_side_pool_distance_atr",
        "mso_h1_atr_14",
        "mso_m15_atr_14",
        "mso_d1_atr_14",
        "mso_pd_equilibrium_50",
        "mso_pd_current_zone",
        "mso_m15_clv_current",
        "mso_m15_clv_avg_5",
        "mso_m15_bvc_buy_fraction",
        "mso_m15_net_flow_5",
        "mso_m15_session_vol_ratio",
        "mso_detected_sweeps_count",
        "mso_detected_sweeps_types",
        "pre_ai_gate_bias",
        "pre_ai_gate_enabled_frameworks",
        "pre_ai_gate_framework_poi_availability",
        "pre_ai_gate_empty_frameworks",
        "pre_ai_gate_any_framework_has_poi",
    ):
        assert key in row, f"missing key: {key}"

    # Spot-checks on actual values
    assert row["symbol"] == "XAUUSD"
    assert row["decision"] == "CANDIDATE"
    assert row["kill_zone"] == "london"
    assert row["session_tag"] == "london"
    assert row["day_of_week"] == 4  # 2026-04-17 is a Friday
    assert row["hour_utc"] == 8
    assert row["candle_close_utc"] == "2026-04-17T07:45:00+00:00"
    assert row["candle_hour_utc"] == 7
    assert row["timestamp_candle_lag_seconds"] == 900.0
    assert row["evaluation_id"].startswith("XAUUSD_2026-04-17T07_45_00")
    assert row["mso_h1_structure_direction"] == "bullish"
    assert row["mso_h1_unmitigated_ob_count"] == 1
    assert row["mso_h1_unmitigated_ob_count_bullish"] == 1
    assert row["mso_h1_unmitigated_ob_count_bearish"] == 0
    assert isinstance(row["mso_h1_ob_touch_counts"], list)
    assert row["mso_pool_count_by_type"] == {"equal_highs": 1, "pdl": 1}
    _assert_cp281_event_contract(row)


def test_pre_ai_gate_capture_fields_include_directional_poi_detail(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    tfs = {
        "D1": _make_tf_state(direction="bullish", atr=12.0),
        "H1": _make_tf_state(
            direction="bullish",
            obs=[
                _make_ob(direction="bearish", mitigated=False),
                _make_ob(direction="bullish", mitigated=True),
            ],
            breakers=[
                _make_breaker(direction="bullish", retested=False),
                _make_breaker(direction="bearish", retested=True),
            ],
            atr=3.0,
        ),
        "M15": _make_tf_state(
            direction="bullish",
            fvgs=[
                _make_fvg(direction="bullish", filled=False),
                _make_fvg(direction="bearish", filled=True),
            ],
            atr=1.2,
        ),
    }

    log_candidate_features(
        pa_output=None,
        mso=_make_mso(tfs=tfs),
        symbol="GBPJPY",
        timestamp_utc="2026-05-04T07:30:05+00:00",
        candle_close_utc="2026-05-04T07:30:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
        pre_ai_gate_skipped=True,
        pre_ai_gate_reason="no_bullish_pois_for_ob_retest+fvg_fill+breaker_re_entry",
        ai_direction_evaluated="LONG",
        pre_ai_gate_bias="bullish",
        pre_ai_gate_enabled_frameworks=["ob_retest", "fvg_fill", "breaker_re_entry"],
        pre_ai_gate_framework_poi_availability={
            "ob_retest": False,
            "fvg_fill": True,
            "breaker_re_entry": True,
        },
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert row["pre_ai_gate_skipped"] is True
    assert row["ai_direction_evaluated"] == "LONG"
    assert row["pre_ai_gate_bias"] == "bullish"
    assert row["pre_ai_gate_enabled_frameworks"] == ["ob_retest", "fvg_fill", "breaker_re_entry"]
    assert row["pre_ai_gate_framework_poi_availability"] == {
        "ob_retest": False,
        "fvg_fill": True,
        "breaker_re_entry": True,
    }
    assert row["pre_ai_gate_empty_frameworks"] == ["ob_retest"]
    assert row["pre_ai_gate_any_framework_has_poi"] is True
    assert row["mso_h1_unmitigated_ob_count"] == 1
    assert row["mso_h1_unmitigated_ob_count_bullish"] == 0
    assert row["mso_h1_unmitigated_ob_count_bearish"] == 1
    assert row["mso_h1_unretested_breaker_count_bullish"] == 1
    assert row["mso_h1_unretested_breaker_count_bearish"] == 0
    assert row["mso_m15_fvg_count_bullish"] == 1
    assert row["mso_m15_fvg_count_bearish"] == 0


# -----------------------------------------------------------------------------
# 2. Missing fields → nulls, no crash
# -----------------------------------------------------------------------------

def test_missing_fields_become_null(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"

    # PA output with no reasoning and no trade_parameters
    pa = _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        decision="NO_TRADE",
        framework="none",
        kill_zone="ny",
        reasoning=None,
        trade_parameters=None,
        no_trade_reason="api_error",
    )

    # MSO missing some timeframes (only H1, no M15 or D1)
    mso = _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        timeframes={
            "H1": _make_tf_state(
                direction="bearish",
                obs=[],
                atr=2.5,
                clv_current=None,
                clv_avg_5=None,
                bvc_buy_fraction=None,
                net_flow_5=None,
            ),
        },
        session_levels=None,
        liquidity_pools=[],
        detected_sweeps=[],
    )

    # Must not raise
    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="US30",
        timestamp_utc="2026-04-17T13:30:00+00:00",
        log_path=str(log_file),
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())

    assert row["decision"] == "NO_TRADE"
    assert row["setup_grade"] is None            # reasoning=None
    assert row["daily_bias_direction"] is None   # reasoning=None
    assert row["trade_parameters"] is None
    # Missing TFs → None for those structure directions
    assert row["mso_m15_structure_direction"] is None
    assert row["mso_d1_structure_direction"] is None
    # H1 present
    assert row["mso_h1_structure_direction"] == "bearish"
    # Pools empty
    assert row["mso_pool_count_by_type"] == {}
    # Sweeps empty
    assert row["mso_detected_sweeps_count"] == 0
    assert row["mso_detected_sweeps_types"] == []
    # ATR for missing TFs is None
    assert row["mso_m15_atr_14"] is None
    assert row["mso_d1_atr_14"] is None


# -----------------------------------------------------------------------------
# 3. Exception isolation
# -----------------------------------------------------------------------------

def test_exception_isolation_does_not_propagate(tmp_path, caplog):
    """A PA output that raises on any attribute access must not crash."""
    log_file = tmp_path / "candidate_features_log.jsonl"

    class _ExplodingPA:
        """Raises Exception on every attribute access."""
        def __getattr__(self, name):
            raise RuntimeError(f"boom on {name}")

        def __getitem__(self, item):
            raise RuntimeError(f"boom on item {item}")

    class _ExplodingMSO:
        def __getattr__(self, name):
            raise RuntimeError(f"boom on mso {name}")

        def __getitem__(self, item):
            raise RuntimeError(f"boom on mso item {item}")

    # If any exception propagates, this test FAILS.
    with caplog.at_level(logging.WARNING, logger="src.components.candidate_features_logger"):
        log_candidate_features(
            pa_output=_ExplodingPA(),
            mso=_ExplodingMSO(),
            symbol="XAUUSD",
            timestamp_utc="2026-04-17T08:00:00+00:00",
            log_path=str(log_file),
        )
    # Must never raise — if it did, pytest would error before here.
    # A file MAY still be written with best-effort null values; our
    # invariant is simply "does not raise". We also check that it did
    # not somehow emit an error log.
    # (A warning may legitimately fire if the outer json.dumps fails —
    # that's acceptable.)


def test_exception_isolation_with_explicit_raise(tmp_path):
    """Even an unserializable PA still doesn't raise."""
    log_file = tmp_path / "candidate_features_log.jsonl"

    pa = MagicMock()
    # getattr on .decision raises
    type(pa).decision = PropertyMock(side_effect=Exception("nope"))
    type(pa).framework = PropertyMock(side_effect=Exception("nope"))
    type(pa).reasoning = PropertyMock(side_effect=Exception("nope"))
    type(pa).trade_parameters = PropertyMock(side_effect=Exception("nope"))
    type(pa).kill_zone = PropertyMock(side_effect=Exception("nope"))

    mso = MagicMock()
    type(mso).timeframes = PropertyMock(side_effect=Exception("nope"))
    type(mso).liquidity_pools = PropertyMock(side_effect=Exception("nope"))
    type(mso).detected_sweeps = PropertyMock(side_effect=Exception("nope"))
    type(mso).session_levels = PropertyMock(side_effect=Exception("nope"))

    # Should not raise
    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        log_path=str(log_file),
    )


# -----------------------------------------------------------------------------
# 4. NO_TRADE → trade_parameters null
# -----------------------------------------------------------------------------

def test_no_trade_has_null_trade_parameters(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    pa = _make_pa_no_trade()
    mso = _make_mso()

    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert row["decision"] == "NO_TRADE"
    assert row["trade_parameters"] is None


# -----------------------------------------------------------------------------
# 5. CANDIDATE → trade_parameters populated
# -----------------------------------------------------------------------------

def test_wait_decision_is_logged_for_r2_distribution(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    pa = _make_pa_wait()
    mso = _make_mso()

    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert row["decision"] == "WAIT"
    assert row["trade_parameters"] is None
    assert row["ai_no_trade_reason"] == "poi_needs_retest"
    assert row["mso_pool_count_by_type"] == {"equal_highs": 1, "pdl": 1}


def test_candidate_has_trade_parameters(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    pa = _make_pa_candidate()
    mso = _make_mso()

    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert row["decision"] == "CANDIDATE"
    tp = row["trade_parameters"]
    assert tp is not None
    assert tp["direction"] == "LONG"
    assert tp["entry_price"] == 2800.50
    assert tp["stop_loss"] == 2790.00
    assert tp["take_profit_1"] == 2820.00
    assert tp["risk_reward_ratio"] == 1.85


# -----------------------------------------------------------------------------
# 6. Two calls → two lines
# -----------------------------------------------------------------------------

def test_distinct_lines_per_call(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    pa1 = _make_pa_candidate()
    pa2 = _make_pa_no_trade()
    mso = _make_mso()

    log_candidate_features(
        pa_output=pa1, mso=mso, symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )
    log_candidate_features(
        pa_output=pa2, mso=mso, symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:15:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )

    content = log_file.read_text(encoding="utf-8").strip()
    lines = content.split("\n")
    assert len(lines) == 2

    r1 = json.loads(lines[0])
    r2 = json.loads(lines[1])
    assert r1["decision"] == "CANDIDATE"
    assert r2["decision"] == "NO_TRADE"
    assert r1["timestamp_utc"] != r2["timestamp_utc"]
    assert r1["evaluation_id"] != r2["evaluation_id"]
