import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from src.research_infra.live_shadow_gap_closure import (
    build_ltf_row,
    build_opportunity_cluster_row,
    build_pending_join_rows,
    build_structural_metadata_rows,
    close_gaps,
    first_touch_times,
    latest_ltf_by_candidate,
    order_label,
)
import src.research_infra.live_shadow_gap_closure as gap_closure


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _candidate(symbol: str, side: str, entry: float, sl: float, tp: float) -> dict:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-04T07:15:00+00:00",
        "candidate_id": f"{symbol}_2026-05-04T07:15:00+00:00",
        "trade_id": f"{symbol}_candidate",
        "symbol": symbol,
        "broker_symbol": symbol,
        "session": "london",
        "side": side,
        "framework": "ob_retest",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "final_outcome_at_log": "LIMIT_PLACED",
        "trade_parameters": {
            "direction": side,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp,
        },
        "external_confluence": {
            "sierra": {"status": "FEATURES_EXTRACTED", "source_symbol": "NQM26-CME"},
            "databento": {"status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE"},
        },
        "strategy_snapshots": [],
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_pending_join_backfill_disambiguates_minute_trade_id_collision():
    xau = _candidate("XAUUSD", "SHORT", 100.0, 110.0, 85.0)
    nas = _candidate("NAS100", "LONG", 200.0, 190.0, 215.0)
    lifecycle = [
        {
            "trade_id": "lim_2026-05-04_0715",
            "timestamp_utc": "2026-05-04T07:30:00+00:00",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "entry_price": 100.0,
            "stop_loss": 110.0,
            "take_profit_1": 85.0,
            "intent_after_check": "still_pending_no_trigger",
        },
        {
            "trade_id": "lim_2026-05-04_0715",
            "timestamp_utc": "2026-05-04T07:30:00+00:00",
            "symbol": "NAS100",
            "side": "LONG",
            "entry_price": 200.0,
            "stop_loss": 190.0,
            "take_profit_1": 215.0,
            "intent_after_check": "still_pending_no_trigger",
        },
    ]

    rows = build_pending_join_rows([xau, nas], lifecycle)

    assert rows[0]["join_status"] == "MATCHED_BY_SYMBOL_SIDE_PRICE_GEOMETRY"
    assert rows[0]["candidate_id_backfilled"] == xau["candidate_id"]
    assert rows[1]["candidate_id_backfilled"] == nas["candidate_id"]
    assert rows[0]["row_key"] != rows[1]["row_key"]


def test_opportunity_cluster_row_key_changes_when_counting_contract_changes():
    candidate = _candidate("XAGUSD", "SHORT", 75.0, 76.0, 73.5)
    path_row = {
        "candidate_id": candidate["candidate_id"],
        "asof_latest_candle_utc": "2026-05-04T19:00:00+00:00",
        "path_label": "entry_touched_then_reached_tp1",
        "touched_entry": True,
        "hit_tp1": True,
        "hit_sl": False,
    }
    opportunity = {
        "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
        "opportunity_id": "opp1",
        "opportunity_duplicate_status": "PRIMARY_UNIQUE_OPPORTUNITY",
        "opportunity_lifecycle_state": "NEW_COUNTABLE",
        "opportunity_candidate_count": 10,
        "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
        "same_symbol_overlap_status": "NO_ACTIVE_SYMBOL_OVERLAP",
    }

    first = build_opportunity_cluster_row(candidate, path_row, None, opportunity)
    changed = build_opportunity_cluster_row(
        candidate,
        path_row,
        None,
        {**opportunity, "opportunity_candidate_count": 19},
    )

    assert first["row_key"] != changed["row_key"]


def test_latest_ltf_by_candidate_prefers_recovered_evidence_over_blocked_placeholder():
    recovered = {
        "candidate_id": "c1",
        "asof_latest_candle_utc": "2026-05-04T08:15:00+00:00",
        "created_at_utc": "2026-05-04T08:16:00+00:00",
        "ltf_status": "M1_PATH_RECOVERED",
        "manual_backfill_status": "RECOVERED_DERIVED",
        "path_order_label": "entry_then_tp1_before_sl",
        "terminal_event_utc": "2026-05-04T07:50:00+00:00",
    }
    blocked = {
        "candidate_id": "c1",
        "asof_latest_candle_utc": "2026-05-04T08:15:00+00:00",
        "created_at_utc": "2026-05-04T08:20:00+00:00",
        "ltf_status": "SOURCE_BLOCKED",
        "manual_backfill_status": "SOURCE_BLOCKED",
        "path_order_label": "ltf_source_blocked",
        "mt5_read_error": "outside_max_hours",
    }

    selected = latest_ltf_by_candidate([recovered, blocked])["c1"]
    assert selected["ltf_status"] == "M1_PATH_RECOVERED"
    assert selected["path_order_label"] == "entry_then_tp1_before_sl"


def test_structural_metadata_uses_forward_captured_source_fields():
    candidate = _candidate("XAUUSD", "LONG", 100.0, 95.0, 107.5)
    cid = candidate["candidate_id"]
    candidate["decision_time_structural_fields"] = {
        "schema_version": "decision_time_structural_fields_v1",
        "capture_status": "DECISION_TIME_STRUCTURAL_SOURCE_CAPTURED",
        "fields": {
            "standalone_fvg_entry_geometry": {
                "source_status": "DECISION_TIME_SOURCE_CAPTURED",
                "h1_fair_value_gaps": [{"top": 101.0, "bottom": 99.5}],
            },
            "fvg_lock_state": {
                "source_status": "DECISION_TIME_SOURCE_CAPTURED_PATH_DERIVATION_PENDING",
            },
            "swing_protected_lock_level": {
                "source_status": "DECISION_TIME_SOURCE_CAPTURED",
                "h1_protected_swing": {"type": "low", "price": 95.0},
            },
            "structural_lock_event_time_price": {
                "source_status": "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED",
            },
            "post_lock_reentry_state": {
                "source_status": "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED",
            },
            "cost_aware_min_r_fields": {
                "source_status": "DECISION_TIME_SOURCE_CAPTURED",
                "candidate_geometry": {"gross_tp1_r": 1.5},
            },
        },
    }
    path = {
        "candidate_id": cid,
        "asof_latest_candle_utc": "2026-05-04T07:30:00+00:00",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
    }
    ltf = {
        "candidate_id": cid,
        "asof_latest_candle_utc": "2026-05-04T07:30:00+00:00",
        "terminal_outcome_status": "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
        "terminal_event_utc": "2026-05-04T07:21:00+00:00",
        "tp1_first_touch_utc": "2026-05-04T07:21:00+00:00",
    }

    rows = build_structural_metadata_rows([candidate], {}, {}, {cid: path}, {cid: ltf})

    row = rows[0]
    assert row["missing_exact_required_fields"] == {}
    assert row["structural_source_field_statuses"]["standalone_fvg_entry_geometry"] == "DECISION_TIME_SOURCE_CAPTURED"
    assert row["structural_source_field_statuses"]["structural_lock_event_time_price"] == "FORWARD_PATH_EVENT_CAPTURED"
    assert row["captured_structural_source_fields"]["structural_lock_event_time_price"]["event_price"] == 107.5
    assert row["scoreability_status"] == "STRUCTURAL_SOURCE_FIELDS_CAPTURED_SCORERS_MAY_STILL_REQUIRE_IMPLEMENTATION"


def test_ltf_order_labels_tp_area_without_entry_for_limit_near_miss():
    touches = first_touch_times(
        side="LONG",
        entry=100.0,
        stop_loss=90.0,
        take_profit_1=110.0,
        bars=[
            {"time_utc": "2026-05-04T07:16:00+00:00", "open": 104.0, "high": 111.0, "low": 103.0, "close": 110.0}
        ],
    )

    assert touches["entry_first_touch_utc"] is None
    assert touches["tp1_first_touch_utc"] == "2026-05-04T07:16:00+00:00"
    assert touches["tp1_first_touch_bar_ohlc"]["high"] == 111.0
    assert touches["terminal_outcome_status"] == "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
    assert touches["terminal_event_r"] == 0.0
    assert touches["terminal_event_bar_ohlc"]["time_utc"] == "2026-05-04T07:16:00+00:00"
    assert order_label(touches) == "tp1_area_reached_without_entry_touch"


def test_ltf_terminal_ignores_tp_before_entry_and_scores_post_entry_sl():
    touches = first_touch_times(
        side="LONG",
        entry=100.0,
        stop_loss=90.0,
        take_profit_1=110.0,
        bars=[
            {"time_utc": "2026-05-04T07:16:00+00:00", "open": 104.0, "high": 111.0, "low": 103.0, "close": 110.0},
            {"time_utc": "2026-05-04T07:30:00+00:00", "open": 105.0, "high": 106.0, "low": 99.0, "close": 101.0},
            {"time_utc": "2026-05-04T07:35:00+00:00", "open": 99.0, "high": 100.0, "low": 89.0, "close": 92.0},
        ],
    )

    assert touches["tp1_first_touch_utc"] == "2026-05-04T07:16:00+00:00"
    assert touches["entry_first_touch_utc"] == "2026-05-04T07:30:00+00:00"
    assert touches["sl_first_touch_utc"] == "2026-05-04T07:35:00+00:00"
    assert touches["entry_first_touch_bar_ohlc"]["low"] == 99.0
    assert touches["sl_first_touch_bar_ohlc"]["low"] == 89.0
    assert touches["terminal_outcome_status"] == "ENTRY_THEN_SL"
    assert touches["terminal_event_utc"] == "2026-05-04T07:35:00+00:00"
    assert touches["terminal_event_bar_ohlc"]["close"] == 92.0
    assert touches["terminal_event_r"] == -1.0
    assert order_label(touches) == "entry_then_sl_before_tp1"


def test_ltf_terminal_same_m1_entry_sl_is_ambiguous_not_loss():
    touches = first_touch_times(
        side="LONG",
        entry=100.0,
        stop_loss=90.0,
        take_profit_1=110.0,
        bars=[
            {"time_utc": "2026-05-04T07:30:00+00:00", "open": 105.0, "high": 106.0, "low": 89.0, "close": 92.0},
        ],
    )

    assert touches["terminal_outcome_status"] == "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS"
    assert touches["terminal_event_r"] is None
    assert touches["terminal_order_ambiguity"] is True
    assert touches["terminal_event_bar_ohlc"]["low"] == 89.0
    assert order_label(touches) == "entry_sl_same_m1_ambiguous"


def test_build_ltf_row_records_m1_source_hash_and_terminal_bar(monkeypatch):
    candidate = _candidate("XAUUSD", "LONG", 100.0, 90.0, 110.0)
    path = {
        "candidate_id": candidate["candidate_id"],
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
    }
    bars = [
        {"time_utc": "2026-05-04T07:16:00+00:00", "open": 104.0, "high": 106.0, "low": 99.0, "close": 101.0, "spread": 12},
        {"time_utc": "2026-05-04T07:17:00+00:00", "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0, "spread": 18},
    ]

    monkeypatch.setattr(gap_closure, "pull_m1_bars", lambda symbol, decision, end: (bars, None))

    row = build_ltf_row(candidate, path, max_hours=999999.0, skip_mt5=False)

    assert row["route_session"] == "london"
    assert row["ltf_status"] == "M1_PATH_RECOVERED"
    assert row["m1_source_first_bar_utc"] == "2026-05-04T07:16:00+00:00"
    assert row["m1_source_last_bar_utc"] == "2026-05-04T07:17:00+00:00"
    assert row["m1_source_sha256"]
    assert row["m1_spread_source_status"] == "SPREAD_CAPTURED"
    assert row["m1_spread_count"] == 2
    assert row["m1_spread_min"] == 12.0
    assert row["m1_spread_max"] == 18.0
    assert row["m1_spread_mean"] == 15.0
    assert row["terminal_outcome_status"] == "ENTRY_THEN_TP1"
    assert row["terminal_event_bar_ohlc"]["high"] == 111.0
    assert row["terminal_event_bar_ohlc"]["spread"] == 18.0


def test_pull_m1_bars_shifts_raw_mt5_query_to_broker_time(monkeypatch):
    captured = {}
    broker_offset = 10_800
    broker_bar_time = int(datetime(2026, 5, 6, 5, 31, tzinfo=timezone.utc).timestamp())

    fake_mt5 = SimpleNamespace(
        TIMEFRAME_M1=1,
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
                "spread": 17,
                "tick_volume": 42,
            }
        ]

    fake_mt5.copy_rates_range = fake_copy_rates_range
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake_mt5)
    monkeypatch.setattr(gap_closure, "detect_broker_offset_seconds", lambda mt5, symbols=None: broker_offset)

    start = datetime(2026, 5, 6, 2, 30, tzinfo=timezone.utc)
    end = datetime(2026, 5, 6, 3, 30, tzinfo=timezone.utc)
    bars, error = gap_closure.pull_m1_bars("GBPJPY", start, end)

    assert error is None
    assert captured["start"] == start + timedelta(seconds=broker_offset)
    assert captured["end"] == end + timedelta(seconds=broker_offset)
    assert bars[0]["time_utc"] == "2026-05-06T02:31:00+00:00"
    assert bars[0]["spread"] == 17.0
    assert bars[0]["tick_volume"] == 42.0


def test_close_gaps_writes_all_expected_shadow_lanes_idempotently(tmp_path):
    candidates = [
        _candidate("NAS100", "LONG", 200.0, 190.0, 215.0),
        _candidate("XAGUSD", "SHORT", 30.0, 31.0, 28.5),
    ]
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", candidates)
    _write_jsonl(
        tmp_path / "shadow_logs/candidate_path_follow.jsonl",
        [
            {
                "candidate_id": candidates[0]["candidate_id"],
                "trade_id": candidates[0]["trade_id"],
                "symbol": "NAS100",
                "broker_symbol": "NAS100",
                "side": "LONG",
                "framework": "ob_retest",
                "decision_time_utc": candidates[0]["decision_time_utc"],
                "asof_latest_candle_utc": "2026-05-04T07:30:00+00:00",
                "path_label": "continued_without_entry_touch_to_tp_area",
                "touched_entry": False,
                "hit_tp1": True,
                "hit_sl": False,
                "bars_elapsed": 2,
                "trade_parameters": candidates[0]["trade_parameters"],
                "min_low": 201.0,
                "max_high": 216.0,
                "last_close": 214.0,
            }
        ],
    )
    _write_jsonl(
        tmp_path / "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
        [
            {
                "candidate_id": candidates[0]["candidate_id"],
                "strategy_id": "V2B_OB_BOUNDARY_PROSPECTIVE",
                "asof_latest_candle_utc": "2026-05-04T07:30:00+00:00",
                "strategy_status": "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
            }
        ],
    )
    _write_jsonl(
        tmp_path / "shadow_logs/pending_limit_lifecycle.jsonl",
        [
            {
                "trade_id": "lim_2026-05-04_0715",
                "timestamp_utc": "2026-05-04T07:30:00+00:00",
                "symbol": "NAS100",
                "side": "LONG",
                "entry_price": 200.0,
                "stop_loss": 190.0,
                "take_profit_1": 215.0,
                "intent_after_check": "still_pending_no_trigger",
            }
        ],
    )

    first = close_gaps(root=tmp_path, skip_mt5=True)
    second = close_gaps(root=tmp_path, skip_mt5=True)

    assert first["rows_written"]["live_candidate_strategy_rollups.jsonl"] == 2
    assert first["rows_written"]["live_candidate_opportunity_clusters.jsonl"] == 2
    assert second["rows_written"]["live_candidate_strategy_rollups.jsonl"] == 0
    assert second["rows_written"]["live_candidate_opportunity_clusters.jsonl"] == 0
    missed = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs/missed_opportunity_shadow.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert missed[0]["near_miss_classification"] == "LIMIT_NO_FILL_TP1_AREA_REACHED"
    assert missed[0]["entry_touch_distance_status"] == "NEAR_MISS_LE_0_25R"
    assert missed[0]["nearest_distance_to_entry_r"] == 0.1
    assert missed[0]["entry_retest_redesign_bucket"] == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"
    trigger_rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs/databento_live_trigger_decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all(row["paid_fetch_attempted"] is False for row in trigger_rows)
    opportunity_rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs/live_candidate_opportunity_clusters.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert opportunity_rows[0]["opportunity_duplicate_status"] == "PRIMARY_UNIQUE_OPPORTUNITY"
    assert opportunity_rows[0]["opportunity_assignment_algorithm_version"] == "active_setup_lifecycle_tolerance_v1"
    assert opportunity_rows[0]["opportunity_counting_status"] == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    assert opportunity_rows[0]["opportunity_similarity"]["materially_same_setup"] is True
    assert opportunity_rows[0]["entry_touch_distance_status"] == "NEAR_MISS_LE_0_25R"
    assert opportunity_rows[0]["nearest_distance_to_entry_r"] == 0.1
    assert opportunity_rows[0]["entry_retest_redesign_bucket"] == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"
    assert "cannot assume multiple simultaneous same-instrument fills" in opportunity_rows[0]["instrument_concurrency_guidance"]
    assert "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY" in opportunity_rows[0]["opportunity_counting_guidance"]
    rollup_rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs/live_candidate_strategy_rollups.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rollup_rows[0]["entry_touch_distance_status"] == "NEAR_MISS_LE_0_25R"
    assert rollup_rows[0]["nearest_distance_to_entry_r"] == 0.1
    assert rollup_rows[0]["entry_retest_redesign_bucket"] == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"


def test_close_gaps_can_refresh_single_candidate(tmp_path):
    first = _candidate("XAGUSD", "SHORT", 30.0, 31.0, 28.5)
    target = _candidate("XAGUSD", "SHORT", 30.0, 31.0, 28.5)
    target["candidate_id"] = "XAGUSD_2026-05-04T07:30:00+00:00"
    target["decision_time_utc"] = "2026-05-04T07:30:00+00:00"
    candidates = [first, target]
    target_id = candidates[1]["candidate_id"]
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", candidates)
    _write_jsonl(
        tmp_path / "shadow_logs/candidate_path_follow.jsonl",
        [
            {
                "candidate_id": target_id,
                "trade_id": candidates[1]["trade_id"],
                "symbol": "XAGUSD",
                "broker_symbol": "XAGUSD",
                "side": "SHORT",
                "framework": "ob_retest",
                "decision_time_utc": candidates[1]["decision_time_utc"],
                "asof_latest_candle_utc": "2026-05-04T07:30:00+00:00",
                "path_label": "continued_without_entry_touch_to_tp_area",
                "touched_entry": False,
                "hit_tp1": True,
                "hit_sl": False,
                "bars_elapsed": 2,
                "trade_parameters": candidates[1]["trade_parameters"],
            }
        ],
    )

    summary = close_gaps(root=tmp_path, skip_mt5=True, candidate_ids={target_id})

    assert summary["candidate_filter"] == [target_id]
    assert summary["candidates_seen"] == 1
    assert summary["context_candidates_seen"] == 2
    opportunity_rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs/live_candidate_opportunity_clusters.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["candidate_id"] for row in opportunity_rows] == [target_id]
    assert opportunity_rows[0]["opportunity_duplicate_status"] in {
        "DUPLICATE_ACTIVE_SETUP",
        "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP",
    }


def test_static_blocker_status_rows_refresh_by_time_bucket(monkeypatch):
    candidate = _candidate("NAS100", "SHORT", 200.0, 210.0, 185.0)

    monkeypatch.setattr(gap_closure, "utc_now_iso", lambda: "2026-05-04T10:38:51+00:00")
    first = gap_closure.static_blocker_rows([candidate])
    same_bucket = gap_closure.static_blocker_rows([candidate])

    assert first["proxy"][0]["row_key"] == same_bucket["proxy"][0]["row_key"]
    assert first["ml"][0]["row_key"] == same_bucket["ml"][0]["row_key"]
    assert first["external"][0]["row_key"] == same_bucket["external"][0]["row_key"]
    assert first["proxy"][0]["status_bucket_utc"] == "2026-05-04T10:30:00+00:00"
    assert first["proxy"][0]["status_cadence_minutes"] == 15

    monkeypatch.setattr(gap_closure, "utc_now_iso", lambda: "2026-05-04T10:45:00+00:00")
    next_bucket = gap_closure.static_blocker_rows([candidate])

    assert first["proxy"][0]["row_key"] != next_bucket["proxy"][0]["row_key"]
    assert first["ml"][0]["row_key"] != next_bucket["ml"][0]["row_key"]
    assert first["external"][0]["row_key"] != next_bucket["external"][0]["row_key"]
    assert next_bucket["proxy"][0]["status_bucket_utc"] == "2026-05-04T10:45:00+00:00"
