from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from scripts import follow_live_candidate_paths as flcp
from scripts.follow_live_candidate_paths import build_follow_row, classify_path, path_changed


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


def test_classify_long_no_touch_stayed_above_entry():
    result = classify_path(
        side="LONG",
        entry=100.0,
        stop_loss=98.0,
        take_profit_1=103.0,
        bars=[{"high": 102.0, "low": 100.5, "close": 101.0}],
    )

    assert result["path_label"] == "no_touch_stayed_above_entry"
    assert result["touched_entry"] is False
    assert result["nearest_abs_distance_to_entry"] == 0.5
    assert result["nearest_distance_to_entry_r"] == 0.25
    assert result["entry_touch_distance_status"] == "NEAR_MISS_LE_0_25R"


def test_classify_long_through_entry_to_sl():
    result = classify_path(
        side="LONG",
        entry=100.0,
        stop_loss=98.0,
        take_profit_1=103.0,
        bars=[{"high": 100.5, "low": 97.5, "close": 98.2}],
    )

    assert result["path_label"] == "went_through_entry_and_continued_to_sl"
    assert result["touched_entry"] is True
    assert result["hit_sl"] is True
    assert result["entry_first_touch_utc"] is None
    assert result["tick_order_claim_status"] == "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY"


def test_classify_same_m15_tp_sl_ambiguity_preserves_no_tick_claim():
    result = classify_path(
        side="LONG",
        entry=100.0,
        stop_loss=98.0,
        take_profit_1=103.0,
        bars=[{"time_utc": "2026-05-04T07:15:00+00:00", "high": 104.0, "low": 97.0, "close": 101.0}],
    )

    assert result["path_label"] == "entry_touched_tp_and_sl_m15_ambiguous"
    assert result["entry_first_touch_utc"] == "2026-05-04T07:15:00+00:00"
    assert result["tp1_first_touch_utc"] == "2026-05-04T07:15:00+00:00"
    assert result["sl_first_touch_utc"] == "2026-05-04T07:15:00+00:00"
    assert result["path_ambiguity_status"] == "M15_TP1_SL_ORDER_AMBIGUOUS_NO_TICK_ORDER_CLAIM"
    assert result["tick_order_claim_status"] == "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY"


def test_classify_short_no_touch_stayed_below_entry():
    result = classify_path(
        side="SHORT",
        entry=100.0,
        stop_loss=102.0,
        take_profit_1=97.0,
        bars=[{"high": 99.5, "low": 98.0, "close": 98.5}],
    )

    assert result["path_label"] == "no_touch_stayed_below_entry"
    assert result["touched_entry"] is False
    assert result["nearest_abs_distance_to_entry"] == 0.5
    assert result["nearest_distance_to_entry_r"] == 0.25
    assert result["entry_touch_distance_status"] == "NEAR_MISS_LE_0_25R"


def test_classify_no_entry_touch_tp_area_is_not_fill():
    result = classify_path(
        side="LONG",
        entry=100.0,
        stop_loss=98.0,
        take_profit_1=103.0,
        bars=[{"time_utc": "2026-05-04T07:15:00+00:00", "high": 104.0, "low": 101.0, "close": 103.5}],
    )

    assert result["path_label"] == "continued_without_entry_touch_to_tp_area"
    assert result["touched_entry"] is False
    assert result["tp1_first_touch_utc"] == "2026-05-04T07:15:00+00:00"
    assert result["entry_first_touch_utc"] is None
    assert result["path_ambiguity_status"] == "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL"
    assert result["nearest_distance_to_entry_r"] == 0.5
    assert result["entry_touch_distance_status"] == "FAR_MISS_GT_0_25R"


def test_path_changed_detects_append_only_correction_fields():
    existing = {"path_label": "entry_touched_unresolved", "touched_entry": True}
    new = {"path_label": "entry_touched_then_reached_tp1", "touched_entry": True}

    assert path_changed(existing, new) is True
    assert path_changed(new, dict(new)) is False
    assert (
        path_changed(
            {"path_label": "same"},
            {"path_label": "same", "m15_spread_source_status": "SPREAD_CAPTURED"},
        )
        is True
    )


def test_build_follow_row_includes_external_confluence(monkeypatch):
    monkeypatch.setattr(
        "scripts.follow_live_candidate_paths.pull_m15_bars",
        lambda symbol, start, end: (
            [
                {
                    "time_utc": "2026-05-04T03:15:00+00:00",
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "spread": 12,
                    "tick_volume": 80,
                    "real_volume": 2,
                }
            ],
            None,
        ),
    )
    row, skip = build_follow_row(
        {
            "candidate_id": "c1",
            "symbol": "GBPJPY",
            "broker_symbol": "GBPJPY",
            "kill_zone": "tokyo",
            "side": "LONG",
            "decision_time_utc": "2026-05-04T03:00:00+00:00",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 100,
                "stop_loss": 98,
                "take_profit_1": 103,
            },
        },
        now=datetime(2026, 5, 4, 3, 20, tzinfo=timezone.utc),
        max_hours=8,
    )

    assert skip is None
    assert row["schema_version"] == "candidate_path_follow_v1"
    assert row["route_session"] == "tokyo"
    assert row["external_confluence"]["sierra"]["status"] == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    assert row["m15_spread_source_status"] == "SPREAD_CAPTURED"
    assert row["m15_spread_count"] == 1
    assert row["m15_spread_mean"] == 12
    assert row["m15_tick_volume_source_status"] == "TICK_VOLUME_CAPTURED"
    assert row["m15_tick_volume_mean"] == 80
    assert row["m15_real_volume_source_status"] == "REAL_VOLUME_CAPTURED"
    assert row["m15_real_volume_mean"] == 2
    _assert_cp281_event_contract(row)


def test_build_follow_row_skips_incomplete_path_sources(monkeypatch):
    monkeypatch.setattr(
        "scripts.follow_live_candidate_paths.pull_m15_bars",
        lambda symbol, start, end: ([], "mt5_initialize_failed"),
    )

    row, skip = build_follow_row(
        {
            "candidate_id": "c1",
            "symbol": "GBPJPY",
            "broker_symbol": "GBPJPY",
            "side": "LONG",
            "decision_time_utc": "2026-05-04T03:00:00+00:00",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 100,
                "stop_loss": 98,
                "take_profit_1": 103,
            },
        },
        now=datetime(2026, 5, 4, 3, 20, tzinfo=timezone.utc),
        max_hours=8,
    )

    assert row == {}
    assert skip == "path_source_incomplete:mt5_initialize_failed"


def test_build_follow_row_skips_missing_trade_prices(monkeypatch):
    monkeypatch.setattr(
        "scripts.follow_live_candidate_paths.pull_m15_bars",
        lambda symbol, start, end: (
            [{"time_utc": "2026-05-04T03:15:00+00:00", "high": 101, "low": 99, "close": 100}],
            None,
        ),
    )

    row, skip = build_follow_row(
        {
            "candidate_id": "c1",
            "symbol": "GBPJPY",
            "broker_symbol": "GBPJPY",
            "side": "LONG",
            "decision_time_utc": "2026-05-04T03:00:00+00:00",
            "trade_parameters": {"direction": "LONG"},
        },
        now=datetime(2026, 5, 4, 3, 20, tzinfo=timezone.utc),
        max_hours=8,
    )

    assert row == {}
    assert skip == "path_source_incomplete:missing_trade_parameters_or_prices"


def test_pull_m15_bars_shifts_raw_mt5_query_to_broker_time(monkeypatch):
    captured = {}
    broker_offset = 10_800
    broker_bar_time = int(datetime(2026, 5, 6, 5, 30, tzinfo=timezone.utc).timestamp())

    fake_mt5 = SimpleNamespace(
        TIMEFRAME_M15=15,
        initialize=lambda: True,
        shutdown=lambda: None,
    )

    def fake_copy_rates_range(symbol, timeframe, start, end):
        captured["symbol"] = symbol
        captured["timeframe"] = timeframe
        captured["start"] = start
        captured["end"] = end
        return [
            {
                "time": broker_bar_time,
                "open": 214.10,
                "high": 214.20,
                "low": 214.07,
                "close": 214.15,
                "spread": 9,
                "tick_volume": 123,
                "real_volume": 4,
            }
        ]

    fake_mt5.copy_rates_range = fake_copy_rates_range
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake_mt5)
    monkeypatch.setattr(flcp, "detect_broker_offset_seconds", lambda mt5, symbols=None: broker_offset)

    start = datetime(2026, 5, 6, 2, 30, tzinfo=timezone.utc)
    end = datetime(2026, 5, 6, 3, 30, tzinfo=timezone.utc)
    bars, error = flcp.pull_m15_bars("GBPJPY", start, end)

    assert error is None
    assert captured["start"] == start + timedelta(seconds=broker_offset)
    assert captured["end"] == end + timedelta(seconds=broker_offset)
    assert bars[0]["time_utc"] == "2026-05-06T02:30:00+00:00"
    assert bars[0]["spread"] == 9
    assert bars[0]["tick_volume"] == 123
    assert bars[0]["real_volume"] == 4


def test_run_invokes_observer_tick_enrichment_lane(tmp_path, monkeypatch):
    source = tmp_path / "strategy_follow_candidates.jsonl"
    output = tmp_path / "candidate_path_follow.jsonl"
    source.write_text(
        json.dumps(
            {
                "candidate_id": "c1",
                "symbol": "XAUUSD",
                "broker_symbol": "XAUUSD",
                "side": "SHORT",
                "decision_time_utc": "2026-05-04T10:00:00+00:00",
                "final_outcome_at_log": "LIMIT_PLACED",
                "external_confluence": {"sierra": {"status": "TEST"}},
                "trade_parameters": {
                    "direction": "SHORT",
                    "entry_price": 100,
                    "stop_loss": 102,
                    "take_profit_1": 97,
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        flcp,
        "pull_m15_bars",
        lambda symbol, start, end: (
            [{"time_utc": "2026-05-04T10:15:00+00:00", "high": 101, "low": 98, "close": 99}],
            None,
        ),
    )

    import src.research_infra.live_mechanical_shadow as mechanical_shadow
    import src.research_infra.live_shadow_gap_closure as gap_closure
    import src.research_infra.shadow_observer_tick_enrichment as tick_enrichment

    monkeypatch.setattr(mechanical_shadow, "run", lambda **kwargs: {"rows_written": 0})
    monkeypatch.setattr(gap_closure, "close_gaps", lambda **kwargs: {"rows_written": {}})
    monkeypatch.setattr(
        tick_enrichment,
        "run",
        lambda **kwargs: {
            "rows_written": 2,
            "symbols": sorted(kwargs["symbol_filter"]),
            "no_ai_calls": True,
            "paid_fetch_attempted": False,
        },
    )

    summary = flcp.run(
        source,
        output,
        max_hours=1_000_000,
        observer_tick_symbols={"EURUSD"},
    )

    assert summary["rows_written"] == 1
    assert summary["observer_tick_enrichment"]["rows_written"] == 2
    assert summary["observer_tick_enrichment"]["symbols"] == ["EURUSD"]


def test_run_backfills_missing_candidate_from_trade_record_before_follow(tmp_path, monkeypatch):
    source = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    output = tmp_path / "shadow_logs" / "candidate_path_follow.jsonl"
    trade_record = tmp_path / "knowledge_base" / "trade_records" / "NAS100" / "2026-05-04_ny_1315.json"
    trade_record.parent.mkdir(parents=True, exist_ok=True)
    trade_record.write_text(
        json.dumps(
            {
                "metadata": {
                    "symbol": "NAS100",
                    "kill_zone": "ny",
                    "candle_close_utc": "2026-05-04T13:15:00+00:00",
                },
                "decision_pipeline": {
                    "ai_decision": "CANDIDATE",
                    "ai_direction": "LONG",
                    "ai_framework": "ob_retest",
                    "level2_verification": {"passed": True, "checks": [], "blocked_by": None},
                    "final_outcome": "REJECTED_GATE1_SAFETY",
                },
                "ai_response": {
                    "decision": "CANDIDATE",
                    "framework": "ob_retest",
                    "kill_zone": "ny",
                    "frameworks_evaluated": {"ob_retest": {"qualified": True}},
                    "reasoning": {
                        "h1_setup": {"poi_type": "OB", "zone": "discount"},
                        "m15_confirmation": {"displacement_quality": "strong"},
                    },
                    "trade_parameters": {
                        "direction": "LONG",
                        "entry_price": 100,
                        "stop_loss": 98,
                        "take_profit_1": 103,
                    },
                },
                "mso": {"timestamp_utc": "2026-05-04T13:15:00+00:00", "timeframes": {}},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        flcp,
        "pull_m15_bars",
        lambda symbol, start, end: (
            [{"time_utc": "2026-05-04T13:30:00+00:00", "high": 104, "low": 99, "close": 103}],
            None,
        ),
    )

    import src.research_infra.live_mechanical_shadow as mechanical_shadow
    import src.research_infra.live_shadow_gap_closure as gap_closure
    import src.research_infra.shadow_observer_tick_enrichment as tick_enrichment

    monkeypatch.setattr(mechanical_shadow, "run", lambda **kwargs: {"rows_written": 0})
    monkeypatch.setattr(gap_closure, "close_gaps", lambda **kwargs: {"rows_written": {}})
    monkeypatch.setattr(tick_enrichment, "run", lambda **kwargs: {"rows_written": 0})
    summary = flcp.run(source, output, max_hours=1_000_000, observer_tick_symbols=set())

    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    assert summary["trade_record_candidate_backfill"]["rows_written"] == 1
    assert summary["rows_written"] == 1
    assert rows[0]["candidate_id"] == "NAS100_2026-05-04T13:15:00+00:00"
    assert rows[0]["broker_symbol"] == "NDX100"
    assert rows[0]["final_outcome_at_log"] == "REJECTED_GATE1_SAFETY"

    second = flcp.run(source, output, max_hours=1_000_000, observer_tick_symbols=set())
    assert second["trade_record_candidate_backfill"]["rows_written"] == 0


def test_trade_record_backfill_skips_ambiguous_same_candle_candidate_ids(tmp_path, monkeypatch):
    source = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    output = tmp_path / "shadow_logs" / "candidate_path_follow.jsonl"
    records_root = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD"
    records_root.mkdir(parents=True, exist_ok=True)

    def _record(entry: float, stop: float, tp1: float) -> dict:
        return {
            "metadata": {
                "symbol": "XAUUSD",
                "kill_zone": "ny",
                "candle_close_utc": "2026-05-03T16:30:00+00:00",
            },
            "decision_pipeline": {
                "ai_decision": "CANDIDATE",
                "ai_direction": "SHORT",
                "ai_framework": "ob_retest",
                "level2_verification": {"passed": True, "checks": [], "blocked_by": None},
                "final_outcome": "REJECTED_GATE3_CIRCUIT_BREAKER",
            },
            "ai_response": {
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "kill_zone": "ny",
                "reasoning": {
                    "h1_setup": {"poi_type": "OB", "zone": "premium"},
                    "m15_confirmation": {"displacement_quality": "strong"},
                },
                "trade_parameters": {
                    "direction": "SHORT",
                    "entry_price": entry,
                    "stop_loss": stop,
                    "take_profit_1": tp1,
                },
            },
            "mso": {"timestamp_utc": "2026-05-03T16:30:00+00:00", "timeframes": {}},
        }

    (records_root / "2026-05-03_ny_1630.json").write_text(
        json.dumps(_record(4668.45, 4681.54, 4649.82), sort_keys=True),
        encoding="utf-8",
    )
    (records_root / "2026-05-03_ny_1645.json").write_text(
        json.dumps(_record(4668.45, 4680.57, 4650.27), sort_keys=True),
        encoding="utf-8",
    )
    monkeypatch.setattr(flcp, "pull_m15_bars", lambda symbol, start, end: ([], None))

    import src.research_infra.live_mechanical_shadow as mechanical_shadow
    import src.research_infra.live_shadow_gap_closure as gap_closure
    import src.research_infra.shadow_observer_tick_enrichment as tick_enrichment

    monkeypatch.setattr(mechanical_shadow, "run", lambda **kwargs: {"rows_written": 0})
    monkeypatch.setattr(gap_closure, "close_gaps", lambda **kwargs: {"rows_written": {}})
    monkeypatch.setattr(tick_enrichment, "run", lambda **kwargs: {"rows_written": 0})

    summary = flcp.run(source, output, max_hours=1_000_000, observer_tick_symbols=set())

    backfill = summary["trade_record_candidate_backfill"]
    assert backfill["rows_written"] == 0
    assert backfill["skipped"]["ambiguous_candidate_id_collision"] == 2
    assert backfill["ambiguous_candidate_id_collisions"] == [
        {
            "candidate_id": "XAUUSD_2026-05-03T16:30:00+00:00",
            "source_files": [
                str(records_root / "2026-05-03_ny_1630.json"),
                str(records_root / "2026-05-03_ny_1645.json"),
            ],
        }
    ]
