"""V2 predecision feature block tests for the live broader-origin generators.

Covers: hand-computed feature values from deterministic closed-bar fixtures,
None-safety on short series, candidate_id stability with/without the feature
block, and forbidden-token cleanliness of every feature name.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

import src.components.broader_origin_generators as bog
from src.components.broader_origin_generators import (
    Bar,
    BarSeries,
    PREDECISION_FEATURE_KEYS,
    SESSION_WINDOWS,
    _predecision_features,
    _stable_id,
    generate_live_broader_origin_candidates,
)
from src.research_infra.learned_edge_dataset_builder import (
    FORBIDDEN_FEATURE_TOKENS,
    feature_guard_violations,
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


def _generate(
    raw_data: dict,
    *,
    symbol: str = "XAUUSD",
    kill_zone: str = "ny",
    cross_asset_raw_data: dict | None = None,
) -> list[dict]:
    return generate_live_broader_origin_candidates(
        raw_data=raw_data,
        mso=None,
        config={"risk": {"min_rr": 1.5}},
        symbol=symbol,
        kill_zone=kill_zone,
        cross_asset_raw_data=cross_asset_raw_data,
        now_utc=_dt(raw_data["candle_close_utc"]),
    )


def _by_family(candidates: list[dict], family: str) -> dict:
    for candidate in candidates:
        if candidate["origin_family"] == family:
            return candidate
    raise AssertionError(f"missing candidate family {family}: {candidates}")


def _sweep_bars() -> list[dict]:
    bars = _flat_bars()
    bars[-1].update({"open": 100.2, "high": 101.8, "low": 99.9, "close": 100.4})
    return bars


def _mean_high_low_atr(bars: list[dict], lookback: int) -> float:
    window = bars[-lookback:]
    return sum(bar["high"] - bar["low"] for bar in window) / len(window)


def test_every_candidate_carries_exact_predecision_feature_key_set() -> None:
    lag_bars = _flat_bars()
    lag_bars[-1].update({"open": 100.0, "high": 100.4, "low": 99.6, "close": 100.2})
    leader_bars = _flat_bars(close=50.0)
    leader_bars[-3].update({"open": 50.0, "high": 50.5, "low": 49.5, "close": 50.0})
    leader_bars[-2].update({"open": 50.0, "high": 52.4, "low": 49.8, "close": 52.0})

    scenarios = [
        _generate(_raw("XAUUSD", _sweep_bars())),
        _generate(
            _raw("XAUUSD", lag_bars),
            cross_asset_raw_data={"XAGUSD": _raw("XAGUSD", leader_bars)},
        ),
    ]
    seen_families: set[str] = set()
    for candidates in scenarios:
        assert candidates
        for candidate in candidates:
            seen_families.add(candidate["origin_family"])
            block = candidate["predecision_features"]
            assert isinstance(block, dict)
            assert set(block) == set(PREDECISION_FEATURE_KEYS)
    assert "liquidity_sweep_reclaim" in seen_families
    assert "cross_asset_lead_lag" in seen_families


def test_liquidity_sweep_predecision_values_hand_computed() -> None:
    bars = _sweep_bars()
    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "liquidity_sweep_reclaim")
    features = candidate["predecision_features"]

    atr14 = _mean_high_low_atr(bars, 14)  # (13 * 1.0 + 1.9) / 14
    atr50 = _mean_high_low_atr(bars, 50)  # (49 * 1.0 + 1.9) / 50
    assert atr14 == pytest.approx(14.9 / 14)
    assert atr50 == pytest.approx(50.9 / 50)

    assert features["atr14_over_atr50"] == pytest.approx(atr14 / atr50)
    # entry=100.4, stop=101.8 + 0.25*atr14 -> |entry-stop| = 1.4 + 0.25*atr14
    expected_stop_distance = (1.4 + 0.25 * atr14) / atr14
    assert features["stop_distance_atr"] == pytest.approx(expected_stop_distance)
    assert features["target_distance_atr"] == pytest.approx(1.5 * expected_stop_distance)
    # 50-bar range: high 101.8, low 99.5; close 100.4 -> 0.9 / 2.3
    assert features["close_position_in_lookback_range"] == pytest.approx(0.9 / 2.3)
    assert features["trend_state_m15"] == "flat"
    assert features["trend_transition_flag"] is False
    # prior20 high 100.5 / low 99.5 versus close 100.4
    assert features["dist_to_prior_high20_atr"] == pytest.approx(0.1 / atr14)
    assert features["dist_to_prior_low20_atr"] == pytest.approx(0.9 / atr14)
    assert features["trigger_bar_range_atr"] == pytest.approx(1.9 / atr14)
    assert features["trigger_bar_body_atr"] == pytest.approx(0.2 / atr14)
    # prior bar is flat width-1.0 history: atr14_prev / atr50_prev = 1.0
    assert features["compression_ratio_prior_bar"] == pytest.approx(1.0)
    # 13:00 is the first XAUUSD ny-session bar (12:45 is off-session)
    assert features["bars_since_session_open"] == 0
    # single close move 0.4: (0.4/8) / (0.4/48) = 6.0
    assert features["close_to_close_vol_8_over_48"] == pytest.approx(6.0)
    # wick above prior20 high: (101.8 - 100.5) / atr14
    assert features["sweep_depth_atr"] == pytest.approx(1.3 / atr14)
    assert features["session_open_range_width_atr"] is None


def test_regime_transition_sets_trend_state_and_transition_flag() -> None:
    bars = _flat_bars()
    bars[-1].update({"open": 100.0, "high": 103.3, "low": 99.8, "close": 103.0})

    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "regime_transition_break")
    features = candidate["predecision_features"]

    assert features["trend_state_m15"] == "strong_up"
    assert features["trend_transition_flag"] is True
    assert features["sweep_depth_atr"] is None
    assert features["session_open_range_width_atr"] is None


def test_session_open_range_break_width_and_bars_since_session_open() -> None:
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
    features = candidate["predecision_features"]

    # window: 10 flat width-1.0 bars + widths 1.0, 0.8, 0.6 (session-open bars)
    # + 1.4 (trigger bar)
    atr14 = _mean_high_low_atr(bars, 14)
    assert atr14 == pytest.approx(13.8 / 14)
    # open range = 100.5 / 99.5 from the first session bar(s) -> width 1.0
    assert features["session_open_range_width_atr"] == pytest.approx(1.0 / atr14)
    # 07:45 is the 4th london bar of the day (07:00 open) -> 3 closed bars since open
    assert features["bars_since_session_open"] == 3
    assert features["sweep_depth_atr"] is None


def test_cross_asset_candidate_features_come_from_lag_series_only() -> None:
    lag_bars = _flat_bars()
    lag_bars[-1].update({"open": 100.0, "high": 100.4, "low": 99.6, "close": 100.2})
    leader_bars = _flat_bars(close=50.0)
    leader_bars[-3].update({"open": 50.0, "high": 50.5, "low": 49.5, "close": 50.0})
    leader_bars[-2].update({"open": 50.0, "high": 52.4, "low": 49.8, "close": 52.0})

    candidate = _by_family(
        _generate(
            _raw("XAUUSD", lag_bars),
            cross_asset_raw_data={"XAGUSD": _raw("XAGUSD", leader_bars)},
        ),
        "cross_asset_lead_lag",
    )
    features = candidate["predecision_features"]

    lag_atr14 = _mean_high_low_atr(lag_bars, 14)  # (13 * 1.0 + 0.8) / 14
    assert lag_atr14 == pytest.approx(13.8 / 14)
    assert features["trigger_bar_range_atr"] == pytest.approx(0.8 / lag_atr14)
    # LONG: stop = lag low - 0.25*lag_atr14; entry = 100.2
    assert features["stop_distance_atr"] == pytest.approx(0.6 / lag_atr14 + 0.25)
    assert features["sweep_depth_atr"] is None
    assert features["session_open_range_width_atr"] is None


def test_short_series_yields_none_for_insufficient_lookback_features() -> None:
    start = datetime(2026, 5, 26, 13, 0)
    bars = tuple(
        Bar(
            time=start + timedelta(minutes=15 * i),
            open=100.0,
            high=100.5,
            low=99.5,
            close=100.0,
        )
        for i in range(5)
    )
    series = BarSeries(
        symbol="XAUUSD",
        timeframe="M15",
        bars=bars,
        source_path_feature_status="raw_data_m15_asof_complete",
        session_windows=SESSION_WINDOWS["XAUUSD"],
    )

    features = _predecision_features(
        series,
        len(bars) - 1,
        entry=100.0,
        stop=99.0,
        target=101.5,
        origin_family="liquidity_sweep_reclaim",
        extra={},
    )

    assert set(features) == set(PREDECISION_FEATURE_KEYS)
    # All bars sit inside the XAUUSD ny window, so the session counter is
    # well-defined even on a short series.
    assert features["bars_since_session_open"] == 4
    for key in PREDECISION_FEATURE_KEYS:
        if key == "bars_since_session_open":
            continue
        assert features[key] is None, f"expected None for {key} on short series"


def test_out_of_range_index_yields_all_none_block() -> None:
    series = BarSeries(
        symbol="XAUUSD",
        timeframe="M15",
        bars=(),
        source_path_feature_status="raw_data_m15_asof_complete",
        session_windows=SESSION_WINDOWS["XAUUSD"],
    )
    features = _predecision_features(
        series,
        -1,
        entry=100.0,
        stop=99.0,
        target=101.5,
        origin_family="displacement_continuation",
        extra={},
    )
    assert set(features) == set(PREDECISION_FEATURE_KEYS)
    assert all(value is None for value in features.values())


def test_candidate_id_hashes_preexisting_payload_only() -> None:
    bars = _sweep_bars()
    candidate = _by_family(_generate(_raw("XAUUSD", bars)), "liquidity_sweep_reclaim")

    atr14 = _mean_high_low_atr(bars, 14)
    entry = bars[-1]["close"]
    stop = bars[-1]["high"] + 0.25 * atr14
    target = entry - 1.5 * abs(entry - stop)
    payload = {
        "origin_family": "liquidity_sweep_reclaim",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "candle_open_utc": "2026-05-26T13:00:00Z",
        "entry": round(entry, 10),
        "stop": round(stop, 10),
        "target": round(target, 10),
    }

    assert candidate["candidate_id"] == _stable_id("broadorigin", payload)
    assert "predecision_features" not in payload


def test_candidate_ids_identical_with_and_without_feature_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = _sweep_bars()

    with_block = _generate(_raw("XAUUSD", bars))
    monkeypatch.setattr(bog, "_predecision_features", lambda *args, **kwargs: {})
    without_block = _generate(_raw("XAUUSD", bars))

    assert [candidate["candidate_id"] for candidate in with_block] == [
        candidate["candidate_id"] for candidate in without_block
    ]
    assert all(candidate["predecision_features"] == {} for candidate in without_block)
    assert all(
        set(candidate["predecision_features"]) == set(PREDECISION_FEATURE_KEYS)
        for candidate in with_block
    )


def test_feature_names_carry_no_forbidden_outcome_tokens() -> None:
    for name in PREDECISION_FEATURE_KEYS:
        lowered = name.lower()
        for token in FORBIDDEN_FEATURE_TOKENS:
            assert token not in lowered, f"forbidden token {token} in {name}"

    violations = feature_guard_violations(
        {f"f_{name}": 0.0 for name in PREDECISION_FEATURE_KEYS}
    )
    forbidden_violations = [
        violation
        for violation in violations
        if violation.startswith("forbidden_token_in_feature_name")
    ]
    assert forbidden_violations == []


# ---------------------------------------------------------------------------
# Stop-width scale experiment knob (default-off geometry research).
# ---------------------------------------------------------------------------


def test_stop_width_scale_default_is_noop_and_scales_geometry():
    from src.components.broader_origin_generators import _apply_stop_width_scale

    base = {
        "candidate_id": "broadorigin_x",
        "side": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 101.5,
        "risk_reward_ratio": 1.5,
        "stop_or_invalidation": 99.0,
        "target_reference": 101.5,
        "trade_parameters": {"stop_loss": 99.0, "take_profit_1": 101.5},
        "predecision_features": {"stop_distance_atr": 0.8, "target_distance_atr": 1.2},
    }
    import copy

    untouched = _apply_stop_width_scale(copy.deepcopy(base), 1.0)
    assert untouched == base  # byte-identical at default scale

    scaled = _apply_stop_width_scale(copy.deepcopy(base), 3.0)
    assert scaled["stop_loss"] == 97.0  # entry - 3x risk
    assert scaled["take_profit_1"] == 104.5  # entry + 1.5 * 3x risk
    assert scaled["trade_parameters"]["stop_loss"] == 97.0
    assert abs(scaled["predecision_features"]["stop_distance_atr"] - 2.4) < 1e-9
    assert scaled["stop_width_scale_applied"] == 3.0
    assert scaled["candidate_id"] == base["candidate_id"]  # identity stable across scales

    short = _apply_stop_width_scale(
        {**copy.deepcopy(base), "side": "SHORT", "stop_loss": 101.0, "take_profit_1": 98.5,
         "trade_parameters": {"stop_loss": 101.0, "take_profit_1": 98.5}},
        2.0,
    )
    assert short["stop_loss"] == 102.0
    assert short["take_profit_1"] == 97.0


# ---------------------------------------------------------------------------
# Microstructure mined detectors (S4 absorption, S5 volume-delta divergence).
# ---------------------------------------------------------------------------


def _vol_series(symbol, bars):
    from src.components.broader_origin_generators import Bar, BarSeries
    from datetime import datetime, timedelta
    t0 = datetime(2025, 1, 1)
    return BarSeries(symbol=symbol, timeframe="M15",
                     bars=tuple(Bar(time=t0 + timedelta(hours=4 * i), open=o, high=h, low=l, close=c, volume=v)
                                for i, (o, h, l, c, v) in enumerate(bars)),
                     source_path_feature_status="ok", session_windows=())


def test_microstructure_absorption_reversal_fires_default_off_and_on():
    from src.components.broader_origin_generators import _generate_single_symbol_candidates
    # 60 quiet uptrending bars then a high-volume / small-range bar at range HIGH
    bars = []
    px = 100.0
    for i in range(60):
        px += 0.5
        bars.append((px, px + 0.6, px - 0.2, px + 0.4, 1000.0))
        px += 0.4
    # absorption bar: huge volume, tiny range, at the top of the 48-bar range
    top = max(b[1] for b in bars[-48:])
    bars.append((top + 0.05, top + 0.12, top - 0.02, top + 0.03, 9000.0))
    series = _vol_series("XAUUSD", bars)
    idx = len(series.bars) - 1
    off = _generate_single_symbol_candidates(series=series, index=idx, target_rr=1.5,
                                             kill_zone="ny", enable_microstructure=False)
    on = _generate_single_symbol_candidates(series=series, index=idx, target_rr=1.5,
                                            kill_zone="ny", enable_microstructure=True)
    fams_off = {c.origin_family for c in off}
    fams_on = {c.origin_family for c in on}
    assert "microstructure_absorption_reversal" not in fams_off  # default-off
    assert "microstructure_absorption_reversal" in fams_on       # fires when enabled
    cand = next(c for c in on if c.origin_family == "microstructure_absorption_reversal")
    assert cand.side == "SHORT"  # fade the wall at the high
    # stop ~ 2.5 ATR above entry
    assert cand.stop_loss > cand.entry_price
