from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.components.broader_origin_generators import (
    CANDIDATE_EMISSION_ORDINAL_FIELD,
    CANDIDATE_OCCURRENCE_KEY_FIELD,
    CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD,
    PRODUCTION_ORIGIN_FAMILIES,
    SESSION_WINDOWS,
    SOURCE_QUALITY_KEY,
    _materialize_candidate_occurrences,
    candidate_occurrence_key_from_fields,
    candidate_source_safe_fingerprint_from_fields,
    evaluate_m15_ohlc_source_quality,
    generate_live_broader_origin_candidates,
)
from src.components.current_breaker_re_entry_repair import (
    ENABLE_CONFIG_KEY,
    TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.components.market_state import identify_fvgs
from src.research.moonshot_default_off_policy_router import (
    route_moonshot_dynamic_execution,
)
from src.research_infra.completed_bar_witness import (
    COMPLETION_SEMANTICS,
    ROW_WITNESS_FIELD,
    WITNESS_TYPE,
)


def _dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _flat_bars(
    *,
    latest_open: str = "2026-05-26T13:00:00Z",
    count: int = 60,
    close: float = 100.0,
    width: float = 1.0,
) -> list[dict]:
    latest = _dt(latest_open)
    start = latest - timedelta(minutes=15 * (count - 1))
    bars = []
    for i in range(count):
        ts = start + timedelta(minutes=15 * i)
        bars.append(
            {
                "time": ts.isoformat().replace("+00:00", "Z"),
                "open": close,
                "high": close + width / 2,
                "low": close - width / 2,
                "close": close,
            }
        )
    return bars


def _raw(symbol: str, bars: list[dict]) -> dict:
    latest_open = _dt(bars[-1]["time"])
    return {
        "symbol": symbol,
        "candle_open_utc": latest_open.isoformat(),
        "candle_close_utc": (latest_open + timedelta(minutes=15)).isoformat(),
        "candles": {"M15": bars},
    }


def _truth_raw(symbol: str, bars: list[dict]) -> dict:
    raw = _raw(symbol, copy.deepcopy(bars))
    timeframes = ("D1", "H4", "H1", "M15")
    raw["candles"] = {
        timeframe: copy.deepcopy(bars) for timeframe in timeframes
    }
    for timeframe, witnessed in raw["candles"].items():
        for ordinal, row in enumerate(witnessed):
            predecessor = _dt(row["time"])
            successor = predecessor + timedelta(minutes=15)
            row[ROW_WITNESS_FIELD] = {
                "witness_type": WITNESS_TYPE,
                "completion_semantics": COMPLETION_SEMANTICS,
                "timeframe": timeframe,
                "predecessor_source_ordinal": ordinal,
                "successor_source_ordinal": ordinal + 1,
                "predecessor_open_utc": predecessor.isoformat(),
                "successor_open_utc": successor.isoformat(),
                "successor_market_values_consumed": False,
            }
    witnessed = raw["candles"]["M15"]
    latest = _dt(witnessed[-1]["time"])
    raw.update(
        {
            "source_truth_scope": "unit_source_bound_truth",
            "source_hashes_by_timeframe": {
                timeframe: (str(index + 1) * 64)[:64]
                for index, timeframe in enumerate(timeframes)
            },
            "decision_rows_used_by_timeframe": {
                timeframe: len(witnessed) for timeframe in timeframes
            },
            "decision_max_source_time_utc_by_timeframe": {
                timeframe: latest.isoformat() for timeframe in timeframes
            },
            "decision_completion_witness_by_timeframe": {
                timeframe: copy.deepcopy(
                    raw["candles"][timeframe][-1][ROW_WITNESS_FIELD]
                )
                for timeframe in timeframes
            },
            "decision_completed_bar_selection": (
                "observed_successor_open_utc_upper_bound"
            ),
        }
    )
    return raw


def _truth_config() -> dict:
    return {
        "risk": {"min_rr": 1.5},
        "gtos_vnext_runtime": {
            "wave21_full_flow_truth_mode_enabled": True,
        },
    }


def _generate(
    raw_data: dict,
    *,
    symbol: str = "XAUUSD",
    kill_zone: str = "ny",
    cross_asset_raw_data: dict | None = None,
    mso=None,
    config: dict | None = None,
) -> list[dict]:
    now = _dt(raw_data["candle_close_utc"])
    return generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=mso,
        config=config or {"risk": {"min_rr": 1.5}},
        symbol=symbol,
        kill_zone=kill_zone,
        cross_asset_raw_data=cross_asset_raw_data,
        now_utc=now,
    )


def _by_family(candidates: list[dict], family: str) -> dict:
    for candidate in candidates:
        if candidate["origin_family"] == family:
            return candidate
    raise AssertionError(f"missing candidate family {family}: {candidates}")


def test_production_origin_registry_is_exact_seven_families() -> None:
    assert set(PRODUCTION_ORIGIN_FAMILIES) == {
        "microstructure_absorption_reversal",  # mined 2026-06-13, default-off
        "microstructure_vdelta_divergence",    # mined 2026-06-13, default-off
        "range_extreme_reversion",  # mined 2026-06-12, default-off emission
        "liquidity_sweep_reclaim",
        "structural_distance_extreme",
        "cross_asset_lead_lag",
        "displacement_continuation",
        "session_open_range_break",
        "regime_transition_break",
        "volatility_compression_expansion",
    }


def test_session_schedule_registry_covers_stage08_broker_native_universe() -> None:
    assert {
        "AUDJPY",
        "AUDUSD",
        "BTCUSD",
        "CHFJPY",
        "ETHUSD",
        "EURGBP",
        "EURJPY",
        "EURUSD",
        "GBPJPY",
        "GBPUSD",
        "JP225",
        "NAS100",
        "NZDUSD",
        "SPX500",
        "UK100",
        "US30_CASH",
        "USDCAD",
        "USDCHF",
        "USDJPY",
        "XAGUSD",
        "XAUUSD",
    }.issubset(set(SESSION_WINDOWS))


def test_liquidity_sweep_reclaim_generates_short_reclaim_candidate() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4})

    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "liquidity_sweep_reclaim")

    assert candidate["candidate_origin_family"] == "origin_liquidity_sweep_reclaim"
    assert candidate["side"] == "SHORT"
    assert candidate["entry_price"] == pytest.approx(100.4)
    assert candidate["stop_loss"] > candidate["entry_price"]
    assert candidate["take_profit_1"] < candidate["entry_price"]
    assert candidate["risk_reward_ratio"] == pytest.approx(1.5)
    assert candidate["source_window_complete"] is True
    assert candidate["source_path_feature_status"] == "raw_data_m15_asof_complete"
    assert candidate["live_generation_status"] == "generated_live_asof"
    assert candidate["candle_close_utc"] == "2026-05-26T13:15:00Z"
    assert candidate["source_fields"]["sweep_direction"] == "swept_prior_20_high_reclaimed_below"


def test_displacement_continuation_generates_impulse_candidate() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})

    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "displacement_continuation")

    assert candidate["side"] == "LONG"
    assert candidate["entry_price"] == pytest.approx(101.8)
    assert candidate["source_fields"]["range_atr14"] >= 1.5
    assert candidate["source_fields"]["body_atr14"] >= 0.75
    assert candidate["trade_parameters"]["direction"] == "LONG"


def test_volatility_compression_expansion_generates_break_candidate() -> None:
    bars = _flat_bars(width=2.0)
    for bar in bars[-14:-1]:
        bar.update({"high": 100.2, "low": 99.8})
    bars[-1].update({"open": 100.0, "high": 102.2, "low": 99.7, "close": 102.0})

    candidate = _by_family(
        _generate(_raw("XAUUSD", bars)),
        "volatility_compression_expansion",
    )

    assert candidate["side"] == "LONG"
    assert candidate["source_fields"]["prior_atr14_atr50_ratio"] <= 0.75
    assert candidate["source_fields"]["break_direction"] == "up"


def test_session_open_range_break_generates_first_session_break_candidate() -> None:
    bars = _flat_bars(latest_open="2026-05-26T07:45:00Z")
    by_time = {bar["time"]: bar for bar in bars}
    by_time["2026-05-26T07:00:00Z"].update({"open": 100, "high": 100.5, "low": 99.5, "close": 100})
    by_time["2026-05-26T07:15:00Z"].update({"open": 100, "high": 100.4, "low": 99.6, "close": 100})
    by_time["2026-05-26T07:30:00Z"].update({"open": 100, "high": 100.3, "low": 99.7, "close": 100})
    bars[-1].update({"open": 100.1, "high": 101.3, "low": 99.9, "close": 101.0})

    candidate = _by_family(
        _generate(_raw("XAUUSD", bars), kill_zone="london"),
        "session_open_range_break",
    )

    assert candidate["side"] == "LONG"
    assert candidate["session"] == "london"
    assert candidate["kill_zone"] == "london"
    assert candidate["source_fields"]["open_range_high"] == pytest.approx(100.5)
    assert candidate["source_fields"]["open_range_low"] == pytest.approx(99.5)


def test_session_windows_are_derived_from_production_config_before_static_registry() -> None:
    bars = _flat_bars(latest_open="2026-05-26T06:45:00Z")
    by_time = {bar["time"]: bar for bar in bars}
    by_time["2026-05-26T06:00:00Z"].update({"open": 100, "high": 100.5, "low": 99.5, "close": 100})
    by_time["2026-05-26T06:15:00Z"].update({"open": 100, "high": 100.4, "low": 99.6, "close": 100})
    by_time["2026-05-26T06:30:00Z"].update({"open": 100, "high": 100.3, "low": 99.7, "close": 100})
    bars[-1].update({"open": 100.1, "high": 101.3, "low": 99.9, "close": 101.0})
    raw_data = _raw("XAUUSD", bars)
    config = {
        "risk": {"min_rr": 1.5},
        "market": {
            "symbol": "XAUUSD",
            "kill_zones": {
                "london": {
                    "start_utc": "06:00",
                    "end_utc": "07:00",
                    "core_end_utc": "07:00",
                },
            },
        },
    }

    candidates = generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=None,
        config=config,
        symbol="XAUUSD",
        kill_zone="london",
        now_utc=_dt(raw_data["candle_close_utc"]),
    )
    candidate = _by_family(candidates, "session_open_range_break")

    assert candidate["session"] == "london"
    assert candidate["source_fields"]["open_range_high"] == pytest.approx(100.5)


def test_moonshot_extended_hour_windows_are_configured_sessions_not_pseudo_sessions() -> None:
    bars = _flat_bars(latest_open="2026-05-26T03:00:00Z")
    bars[-1].update({"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4})
    raw_data = _raw("XAUUSD", bars)
    config = {
        "risk": {"min_rr": 1.5},
        "gtos_vnext_runtime": {"moonshot_broader_origin_extended_session_enabled": True},
        "market": {
            "symbol": "XAUUSD",
            "kill_zones": {
                "london": {
                    "start_utc": "07:00",
                    "end_utc": "10:30",
                    "core_end_utc": "09:30",
                },
            },
        },
    }

    candidates = _generate(
        raw_data,
        kill_zone="moonshot_h03_04",
        config=config,
    )
    candidate = _by_family(candidates, "liquidity_sweep_reclaim")

    assert candidate["session"] == "moonshot_h03_04"
    assert candidate["route_session"] == "moonshot_h03_04"
    assert candidate["utc_hour_bucket"] == "h03_04"
    assert candidate["source_fields"]["utc_hour_bucket"] == "h03_04"
    assert "session_open_range_break" not in {item["origin_family"] for item in candidates}


def test_candidates_record_closed_bar_source_contract_and_mso_context() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4})
    mso = SimpleNamespace(
        timestamp_utc="2026-05-26T13:15:00Z",
        timeframes={"M15": object(), "H1": object()},
    )

    candidate = _by_family(
        _generate(_raw("XAUUSD", bars), mso=mso),
        "liquidity_sweep_reclaim",
    )

    assert candidate["market_state_contract"] == (
        "closed_m15_source_bars_drive_origin_features_mso_context_recorded_only"
    )
    assert candidate["source_fields"]["origin_family_source_contract"] == (
        "liquidity_sweep_reclaim_closed_m15_source_fields"
    )
    assert candidate["source_fields"]["mso_context_available"] is True
    assert candidate["source_fields"]["mso_timestamp_utc"] == "2026-05-26T13:15:00Z"
    assert candidate["source_fields"]["mso_timeframes_available"] == ["H1", "M15"]


def test_regime_transition_break_generates_strong_trend_transition_candidate() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 103.3, "low": 99.8, "close": 103.0})

    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "regime_transition_break")

    assert candidate["side"] == "LONG"
    assert candidate["source_fields"]["trend_state_20"] == "strong_up"
    assert candidate["source_fields"]["previous_trend_state_20"] == "flat"
    assert candidate["source_fields"]["transition"] == "to_strong_up_break"


def test_structural_distance_extreme_generates_lower_extreme_candidate() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 100.2, "low": 96.0, "close": 96.1})

    candidate = _by_family(
        _generate(_raw("XAUUSD", bars)),
        "structural_distance_extreme",
    )

    assert candidate["side"] == "LONG"
    assert candidate["source_fields"]["lookback50_position"] <= 0.03
    assert candidate["source_fields"]["extreme_side"] == "lower_range_extreme"


def test_malformed_m15_price_scale_fails_closed_before_candidate_generation() -> None:
    bars = _flat_bars(close=71590.0, width=200.0)
    bars[-2].update(
        {
            "open": 71565.95,
            "high": 71686.24,
            "low": 71516.71,
            "close": 71597.24,
        }
    )
    bars[-1].update(
        {
            "open": 71596.68,
            "high": 71666.51,
            "low": 593.32,
            "close": 593.39,
        }
    )
    raw = _raw("BTCUSD", bars)

    candidates = _generate(raw, symbol="BTCUSD")

    assert candidates == []
    quality = raw[SOURCE_QUALITY_KEY]
    assert quality["status"] == "MALFORMED_OHLC_PRICE_SCALE"
    assert quality["reason"] == "raw_data_m15_interbar_price_jump_exceeds_threshold"
    assert raw["source_path_feature_status"] == "raw_data_m15_malformed_ohlc_price_scale"
    assert raw["source_window_complete"] is False


def test_m15_source_quality_fails_when_repair_failed() -> None:
    bars = _flat_bars(close=1995.0)
    bars[-1]["ohlc_source_repair"] = {
        "status": "repair_failed_local_tick_parquet_unavailable_or_empty",
        "reason": "m15_anchor_price_jump_exceeds_threshold",
    }
    quality = evaluate_m15_ohlc_source_quality(_raw("ETHUSD", bars))

    assert quality["status"] == "MALFORMED_OHLC_PRICE_SCALE"
    assert quality["reason"] == "raw_data_m15_ohlc_source_repair_failed"


def test_cross_asset_lead_lag_generates_when_leader_impulses_first() -> None:
    lag_bars = _flat_bars(latest_open="2026-05-26T13:00:00Z")
    lag_bars[-1].update({"open": 100.0, "high": 100.4, "low": 99.6, "close": 100.2})
    leader_bars = _flat_bars(latest_open="2026-05-26T13:00:00Z", close=50.0)
    leader_bars[-3].update({"open": 50.0, "high": 50.5, "low": 49.5, "close": 50.0})
    leader_bars[-2].update({"open": 50.0, "high": 52.4, "low": 49.8, "close": 52.0})

    cross_asset = {"XAGUSD": _raw("XAGUSD", leader_bars)}
    candidate = _by_family(
        _generate(_raw("XAUUSD", lag_bars), cross_asset_raw_data=cross_asset),
        "cross_asset_lead_lag",
    )

    assert candidate["side"] == "LONG"
    assert candidate["source_path_feature_status"] == "cross_asset_raw_data_asof_complete"
    assert candidate["source_fields"]["leader_symbol"] == "XAGUSD"
    assert candidate["source_fields"]["lag_symbol"] == "XAUUSD"
    assert candidate["source_fields"]["atr14"] > 0
    assert candidate["source_fields"]["lag_atr14"] == candidate["source_fields"]["atr14"]
    assert candidate["source_fields"]["leader_atr14"] > 0
    assert candidate["source_fields"]["leader_move_atr14"] >= 1.0
    assert candidate["source_fields"]["lag_prior_response_atr14"] <= 0.5


def test_future_bars_are_excluded_from_live_asof_generation() -> None:
    bars = _flat_bars(latest_open="2026-05-26T10:00:00Z")
    future = {
        "time": "2026-05-26T10:15:00Z",
        "open": 100.2,
        "high": 102.0,
        "low": 99.8,
        "close": 100.4,
    }
    raw_data = _raw("XAUUSD", [*bars, future])
    raw_data["candle_open_utc"] = "2026-05-26T10:00:00+00:00"
    raw_data["candle_close_utc"] = "2026-05-26T10:15:00+00:00"

    candidates = generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=None,
        config={"risk": {"min_rr": 1.5}},
        symbol="XAUUSD",
        kill_zone="london",
        now_utc=_dt("2026-05-26T10:15:00Z"),
    )

    assert "liquidity_sweep_reclaim" not in {candidate["origin_family"] for candidate in candidates}
    assert all(candidate["candle_open_utc"] != "2026-05-26T10:15:00Z" for candidate in candidates)


def test_cross_asset_lead_lag_fails_closed_without_cross_asset_source() -> None:
    lag_bars = _flat_bars(latest_open="2026-05-26T13:00:00Z")
    lag_bars[-1].update({"open": 100.0, "high": 100.4, "low": 99.6, "close": 100.2})

    candidates = _generate(_raw("XAUUSD", lag_bars), cross_asset_raw_data=None)

    assert "cross_asset_lead_lag" not in {candidate["origin_family"] for candidate in candidates}


def test_current_breaker_repair_is_default_off_and_pure() -> None:
    candidate = {
        "candidate_id": "broadorigin_original",
        "origin_family": "current_breaker_re_entry",
        "side": "LONG",
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "take_profit_1": 103.0,
        "risk_reward_ratio": 1.5,
        "predecision_features": {
            "stop_distance_atr": 2.0,
            "target_distance_atr": 3.0,
        },
        "source_fields": {"uses_outcome_fields": False},
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
            "risk_reward_ratio": 1.5,
        },
    }

    disabled = apply_current_breaker_re_entry_repair(candidate)
    repaired = apply_current_breaker_re_entry_repair(candidate, enabled=True)

    assert disabled == candidate
    assert disabled is not candidate
    assert candidate["side"] == "LONG"  # neither call mutated the input
    assert repaired["side"] == repaired["direction"] == "SHORT"
    assert repaired["entry_price"] == 100.0
    assert repaired["stop_loss"] == pytest.approx(100.5)
    assert repaired["take_profit_1"] == pytest.approx(90.0)
    assert repaired["risk_reward_ratio"] == pytest.approx(20.0)
    assert repaired["candidate_id"] != candidate["candidate_id"]
    assert repaired["candidate_transform_id"] == TRANSFORM_ID
    assert repaired["candidate_transform_default"] == "off"
    assert repaired["predecision_features"]["stop_distance_atr"] == pytest.approx(0.5)
    assert repaired["predecision_features"]["target_distance_atr"] == pytest.approx(10.0)

    # Real broker-price geometry does not generally round-trip bit-for-bit when the
    # canonicalizer recomputes target = entry + 20 * repaired risk. The transform's
    # reconciliation is numerical, not an accidental exact-float requirement.
    realistic = apply_current_breaker_re_entry_repair(
        {
            "candidate_id": "broadorigin_realistic",
            "origin_family": "current_breaker_re_entry",
            "side": "LONG",
            "entry_price": 25468.510000000002,
            "stop_loss": 25450.497531235655,
            "take_profit_1": 25504.534937528697,
        },
        enabled=True,
    )
    assert realistic["take_profit_1"] == pytest.approx(25378.447656178265)


def test_current_breaker_repair_is_wired_behind_absent_false_config_key() -> None:
    bars = _flat_bars(close=100.0, width=1.0)
    raw_data = _raw("XAUUSD", bars)
    mso = SimpleNamespace(
        timestamp_utc=raw_data["candle_close_utc"],
        timeframes={
            "H1": SimpleNamespace(
                atr_14=1.0,
                breaker_blocks=[
                    SimpleNamespace(
                        is_retested=False,
                        zone_low=99.0,
                        zone_high=101.0,
                        direction="bullish",
                        original_ob_direction="bearish",
                        formation_time="2026-05-26T10:00:00Z",
                        mitigation_time="2026-05-26T11:00:00Z",
                        causing_event="displacement",
                    )
                ],
            )
        },
    )
    base = {
        "risk": {"min_rr": 1.5, "sl_buffer_atr_multiplier": 0.25},
        "model_a": {"enabled_frameworks": ["breaker_re_entry"]},
        "gate1": {"poi_proximity_tolerance_pct": 0.05},
    }

    control = _by_family(
        _generate(raw_data, mso=mso, config=base),
        "current_breaker_re_entry",
    )
    audit: dict = {}
    repaired_rows = generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=mso,
        config={
            **base,
            "gtos_vnext_runtime": {ENABLE_CONFIG_KEY: True},
        },
        symbol="XAUUSD",
        kill_zone="ny",
        now_utc=_dt(raw_data["candle_close_utc"]),
        generation_audit=audit,
    )
    repaired = _by_family(repaired_rows, "current_breaker_re_entry")

    assert control["side"] == "LONG"
    assert "candidate_transform_id" not in control
    assert repaired["side"] == "SHORT"
    assert repaired["risk_reward_ratio"] == pytest.approx(20.0)
    assert repaired["candidate_transform_id"] == TRANSFORM_ID
    assert audit["current_breaker_re_entry_repair"] == {
        "config_key": ENABLE_CONFIG_KEY,
        "default": False,
        "enabled": True,
        "transform_id": TRANSFORM_ID,
        "applied_candidates": 1,
    }


def test_current_framework_generation_audit_is_deepcopy_safe_and_candidate_inert() -> None:
    bars = _flat_bars(close=100.0, width=1.0)
    raw_data = _raw("XAUUSD", bars)
    mso = SimpleNamespace(
        timestamp_utc=raw_data["candle_close_utc"],
        timeframes={
            "H1": SimpleNamespace(
                atr_14=1.0,
                breaker_blocks=[
                    SimpleNamespace(
                        is_retested=False,
                        zone_low=99.0,
                        zone_high=101.0,
                        direction="bullish",
                        original_ob_direction="bearish",
                        formation_time="2026-05-26T10:00:00Z",
                        mitigation_time="2026-05-26T11:00:00Z",
                        causing_event="displacement",
                    )
                ],
            )
        },
    )
    config = {
        "risk": {"min_rr": 1.5, "sl_buffer_atr_multiplier": 0.25},
        "model_a": {"enabled_frameworks": ["breaker_re_entry"]},
        "gate1": {"poi_proximity_tolerance_pct": 0.05},
    }

    control = generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=mso,
        config=config,
        symbol="XAUUSD",
        kill_zone="ny",
        now_utc=_dt(raw_data["candle_close_utc"]),
    )
    audit: dict = {}
    observed = generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=mso,
        config=config,
        symbol="XAUUSD",
        kill_zone="ny",
        now_utc=_dt(raw_data["candle_close_utc"]),
        generation_audit=audit,
    )

    assert observed == control
    assert type(audit["current_framework_admission"]["target_rr"]) is float
    assert copy.deepcopy(audit) == audit


def test_current_fvg_candidate_reuses_stable_poi_identity_and_reconciles_generation() -> None:
    formation = [
        {
            "time": "2026-05-14T00:00:00+00:00",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
        },
        {
            "time": "2026-05-14T00:15:00+00:00",
            "open": 100.0,
            "high": 104.0,
            "low": 100.0,
            "close": 103.5,
        },
        {
            "time": "2026-05-14T00:30:00+00:00",
            "open": 103.5,
            "high": 105.0,
            "low": 103.0,
            "close": 104.0,
        },
    ]
    first_touch = {
        "time": "2026-05-14T00:45:00+00:00",
        "open": 104.0,
        "high": 104.2,
        "low": 102.0,
        "close": 102.0,
    }
    second_touch = {
        "time": "2026-05-14T01:00:00+00:00",
        "open": 102.0,
        "high": 103.2,
        "low": 101.5,
        "close": 102.0,
    }
    first_fvg = identify_fvgs(
        [*formation, first_touch],
        min_gap_size=1.0,
        symbol="US30_CASH",
        timeframe="M15",
    )[0]
    second_fvg = identify_fvgs(
        [*formation, first_touch, second_touch],
        min_gap_size=1.0,
        symbol="US30_CASH",
        timeframe="M15",
    )[0]
    config = {
        "risk": {"min_rr": 1.5, "sl_buffer_atr_multiplier": 0.25},
        "model_a": {"enabled_frameworks": ["fvg_fill"]},
        "gate1": {"poi_proximity_tolerance_pct": 0.05},
    }

    def generated(fvg, latest_open: str):
        bars = _flat_bars(latest_open=latest_open, close=102.0, width=1.0)
        raw_data = _raw("US30_CASH", bars)
        audit: dict = {}
        candidates = generate_live_broader_origin_candidates(
            raw_data=raw_data,
            mso=SimpleNamespace(
                timestamp_utc=raw_data["candle_close_utc"],
                timeframes={
                    "M15": SimpleNamespace(
                        atr_14=1.0,
                        fair_value_gaps=[fvg],
                    )
                },
            ),
            config=config,
            symbol="US30_CASH",
            kill_zone="ny",
            now_utc=_dt(raw_data["candle_close_utc"]),
            generation_audit=audit,
        )
        current_fvg = _by_family(candidates, "current_fvg_fill")
        return current_fvg, audit["current_fvg_poi_generation"]

    first_candidate, first_partition = generated(
        first_fvg,
        "2026-05-14T00:45:00Z",
    )
    second_candidate, second_partition = generated(
        second_fvg,
        "2026-05-14T01:00:00Z",
    )

    assert first_candidate["poi_id"] == second_candidate["poi_id"]
    assert first_candidate["poi_state_required"] is True
    assert second_candidate["poi_state_required"] is True
    assert first_candidate["candidate_id"] == second_candidate["candidate_id"]
    assert (
        first_candidate["poi_state_hash_sha256"]
        != second_candidate["poi_state_hash_sha256"]
    )
    for partition in (first_partition, second_partition):
        assert partition["considered_poi_count"] == 1
        assert partition["emitted_poi_count"] == 1
        assert partition["denied_poi_count"] == 0
        assert partition["partition_reconciled"] is True
        assert len(partition["rows"]) == 1
        assert partition["rows"][0]["candidate_id"] == first_candidate["candidate_id"]


def test_truth_generator_refuses_naive_source_before_emission() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})
    raw = _truth_raw("XAUUSD", bars)
    for timeframe_rows in raw["candles"].values():
        for row in timeframe_rows:
            row["time"] = row["time"].replace("+00:00", "").removesuffix("Z")
    audit: dict = {}

    candidates = generate_live_broader_origin_candidates(
        raw_data=raw,
        mso=None,
        config=_truth_config(),
        symbol="XAUUSD",
        kill_zone="ny",
        now_utc=_dt(raw["candle_close_utc"]),
        generation_audit=audit,
    )

    assert candidates == []
    assert audit["status"] == "NOT_EVALUABLE_SOURCE_TIMEBASE"
    assert audit["source_terminal"] is True


def test_legacy_default_keeps_aware_and_naive_generator_behavior_identical() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})
    aware_raw = _raw("XAUUSD", bars)
    naive_raw = copy.deepcopy(aware_raw)
    naive_raw["candle_open_utc"] = naive_raw["candle_open_utc"].replace(
        "+00:00", ""
    )
    naive_raw["candle_close_utc"] = naive_raw["candle_close_utc"].replace(
        "+00:00", ""
    )
    for row in naive_raw["candles"]["M15"]:
        row["time"] = row["time"].removesuffix("Z").replace("+00:00", "")

    assert _generate(aware_raw) == _generate(naive_raw)


def test_truth_generator_uses_successor_open_with_zero_future_tolerance() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})
    raw = _truth_raw("XAUUSD", bars)
    exact = _dt(raw["candle_close_utc"])
    audit: dict = {}

    exact_candidates = generate_live_broader_origin_candidates(
        raw_data=raw,
        mso=None,
        config=_truth_config(),
        symbol="XAUUSD",
        kill_zone="ny",
        now_utc=exact,
        generation_audit=audit,
    )

    assert _by_family(exact_candidates, "displacement_continuation")
    for delta in (timedelta(microseconds=1), timedelta(seconds=1)):
        refusal_audit: dict = {}
        assert generate_live_broader_origin_candidates(
            raw_data=raw,
            mso=None,
            config=_truth_config(),
            symbol="XAUUSD",
            kill_zone="ny",
            now_utc=exact - delta,
            generation_audit=refusal_audit,
        ) == []
        assert refusal_audit["status"] == "NOT_EVALUABLE_SOURCE_CHRONOLOGY"


def test_truth_occurrence_keys_bind_current_geometry_and_exact_consumed_rows() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})
    raw = _truth_raw("XAUUSD", bars)
    candidate = _by_family(
        _generate(raw, config=_truth_config()),
        "displacement_continuation",
    )

    assert candidate_occurrence_key_from_fields(candidate) == candidate[
        CANDIDATE_OCCURRENCE_KEY_FIELD
    ]
    assert candidate_source_safe_fingerprint_from_fields(candidate) == candidate[
        CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD
    ]
    geometry_tamper = {**candidate, "stop_loss": candidate["stop_loss"] - 0.25}
    nested_geometry_tamper = copy.deepcopy(candidate)
    nested_geometry_tamper["trade_parameters"]["stop_loss"] -= 7.0
    nested_open_schema_tamper = copy.deepcopy(candidate)
    nested_open_schema_tamper["trade_parameters"]["unknown"] = 1
    source_tamper = copy.deepcopy(candidate)
    source_tamper["candidate_source_row_association"]["M15"]["row_count"] += 1
    status_tamper = {**candidate, "live_generation_status": "stale_copy"}
    assert candidate_occurrence_key_from_fields(geometry_tamper) == ""
    assert candidate_occurrence_key_from_fields(nested_geometry_tamper) == ""
    assert candidate_occurrence_key_from_fields(nested_open_schema_tamper) == ""
    assert candidate_occurrence_key_from_fields(source_tamper) == ""
    assert candidate_occurrence_key_from_fields(status_tamper) == ""

    open_schema_tamper = copy.deepcopy(candidate)
    open_schema_tamper["candidate_source_row_association"]["unknown"] = True
    assert candidate_occurrence_key_from_fields(open_schema_tamper) == ""

    router_event = {
        **candidate,
        "branch_label": "FOLLOW",
        "activated_origin_families": [candidate["origin_family"]],
        "broader_origin_allowed": True,
        "source_mode": "LIVE_RAW_M15",
    }
    accepted = route_moonshot_dynamic_execution(
        router_event, enabled=True, apply_to_execution=True
    )
    refused = route_moonshot_dynamic_execution(
        {**router_event, "live_generation_status": "stale_copy"},
        enabled=True,
        apply_to_execution=True,
    )
    assert "broader_origin_not_live_generated_asof" not in accepted.refusal_reasons
    assert "broader_origin_not_live_generated_asof" in refused.refusal_reasons


def test_occurrence_ordinal_is_stable_under_unrelated_emissions_and_keeps_duplicates() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 102.1, "low": 99.8, "close": 101.8})
    raw = _truth_raw("XAUUSD", bars)
    legacy = _by_family(
        _generate(_raw("XAUUSD", bars)),
        "displacement_continuation",
    )
    duplicate = copy.deepcopy(legacy)
    unrelated = copy.deepcopy(legacy)
    unrelated.update(
        {
            "candidate_id": "same-legacy-id-is-not-authority",
            "origin_family": "synthetic_unrelated_family",
            "candidate_origin_family": "origin_synthetic_unrelated_family",
            "framework": "synthetic_unrelated_family",
        }
    )
    decision_time = _dt(raw["candle_close_utc"])

    pair = _materialize_candidate_occurrences(
        [legacy, duplicate],
        raw_data=raw,
        cross_asset_raw_data=None,
        decision_time=decision_time,
    )
    with_unrelated = _materialize_candidate_occurrences(
        [unrelated, legacy, duplicate],
        raw_data=raw,
        cross_asset_raw_data=None,
        decision_time=decision_time,
    )[1:]

    assert [row[CANDIDATE_EMISSION_ORDINAL_FIELD] for row in pair] == [0, 1]
    assert len({row[CANDIDATE_OCCURRENCE_KEY_FIELD] for row in pair}) == 2
    assert [row[CANDIDATE_OCCURRENCE_KEY_FIELD] for row in pair] == [
        row[CANDIDATE_OCCURRENCE_KEY_FIELD] for row in with_unrelated
    ]

    distinct_geometry = copy.deepcopy(legacy)
    distinct_geometry["stop_loss"] -= 0.5
    distinct_geometry["stop_or_invalidation"] -= 0.5
    distinct_geometry["take_profit_1"] += 0.75
    distinct_geometry["target_reference"] += 0.75
    distinct_geometry["trade_parameters"] = {
        **distinct_geometry["trade_parameters"],
        "stop_loss": distinct_geometry["stop_loss"],
        "take_profit_1": distinct_geometry["take_profit_1"],
    }
    distinct = _materialize_candidate_occurrences(
        [legacy, distinct_geometry],
        raw_data=raw,
        cross_asset_raw_data=None,
        decision_time=decision_time,
    )
    assert distinct[0]["candidate_id"] == distinct[1]["candidate_id"]
    assert distinct[0][CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD] != distinct[1][
        CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD
    ]
    assert distinct[0][CANDIDATE_OCCURRENCE_KEY_FIELD] != distinct[1][
        CANDIDATE_OCCURRENCE_KEY_FIELD
    ]
