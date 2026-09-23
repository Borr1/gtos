from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.mt5.mt5_mock import MockMT5
from src.research_infra.wave4r_replay_microstructure import (
    DayPropDecision,
    hydrate_readonly_mt5_day,
    hydrate_readonly_mt5_day_session,
    infer_limit_fill_from_m1,
    infer_limit_fill_from_ticks,
    infer_ordered_path_from_local_files,
    infer_ordered_path_from_m1,
    infer_ordered_path_from_ticks,
    simulate_fresh_day_prop_curve,
    split_decision_and_outcome_rows,
)


def test_readonly_mt5_day_hydration_replaces_previous_day_without_order_calls(tmp_path: Path) -> None:
    mt5 = MockMT5()
    mt5.set_candles(
        1,
        [
            {
                "time": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1,
            }
        ],
    )
    mt5.set_ticks(
        "XAUUSD",
        [
            {
                "ts_utc": "2026-01-01T00:01:00+00:00",
                "bid": 10.0,
                "ask": 10.1,
                "flags": 0,
            }
        ],
    )
    old = tmp_path / "2025-12-31" / "m1"
    old.mkdir(parents=True)
    (old / "old.csv").write_text("old\n", encoding="utf-8")

    result = hydrate_readonly_mt5_day(
        provider=mt5,
        symbols={"XAUUSD": "XAUUSD"},
        day="2026-01-01",
        root=tmp_path,
        timeframe_m1=1,
    )

    assert result.m1_rows == 1
    assert result.tick_rows == 1
    assert result.replaced_previous_day is True
    assert not (tmp_path / "2025-12-31").exists()
    assert (tmp_path / "2026-01-01" / "full_day" / "m1" / "XAUUSD.csv").exists()
    assert (tmp_path / "2026-01-01" / "full_day" / "ticks" / "XAUUSD.jsonl").exists()
    assert result.manifest_path is not None
    assert result.manifest_path.exists()
    assert mt5._order_log == []


def test_readonly_mt5_day_session_hydration_writes_manifest_and_bounds(tmp_path: Path) -> None:
    mt5 = MockMT5()
    mt5.set_candles(
        1,
        [
            {
                "time": datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1,
            }
        ],
    )

    result = hydrate_readonly_mt5_day_session(
        provider=mt5,
        symbols={"XAUUSD": "XAUUSD"},
        day="2026-01-01",
        root=tmp_path,
        timeframe_m1=1,
        session_id="london",
        session_start_utc="08:00",
        session_end_utc="11:00",
        include_ticks=False,
    )

    manifest = result.manifest_path.read_text(encoding="utf-8") if result.manifest_path else ""

    assert result.root == tmp_path / "2026-01-01" / "london"
    assert '"request_start_utc": "2026-01-01T08:00:00+00:00"' in manifest
    assert '"request_end_utc": "2026-01-01T11:00:00+00:00"' in manifest
    assert '"broker_order_mutation": false' in manifest
    assert "scratch_day_session_root_prunes_previous_day" in manifest


def test_split_decision_and_outcome_rows_prevents_future_leakage() -> None:
    split = split_decision_and_outcome_rows(
        [
            {"time": "2026-01-01T00:00:00+00:00", "price": 1},
            {"time": "2026-01-01T00:01:00+00:00", "price": 2},
        ],
        asof_utc="2026-01-01T00:00:00+00:00",
        time_key="time",
    )

    assert len(split["decision_input_rows"]) == 1
    assert len(split["outcome_path_rows"]) == 1
    assert split["outcome_path_rows"][0]["price"] == 2


def test_limit_fill_infers_from_ordered_ticks_after_candidate_asof() -> None:
    fill = infer_limit_fill_from_ticks(
        ticks=[
            {"ts_utc": "2026-01-01T00:00:00+00:00", "bid": 10.0, "ask": 10.1},
            {"ts_utc": "2026-01-01T00:02:00+00:00", "bid": 9.8, "ask": 9.95},
        ],
        side="LONG",
        entry_price=10.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert fill.filled is True
    assert fill.source == "tick_ask"
    assert fill.fill_time_utc == "2026-01-01T00:02:00+00:00"


def test_limit_fill_falls_back_to_m1_path_when_ticks_are_absent() -> None:
    fill = infer_limit_fill_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 10.5,
                "low": 9.9,
            }
        ],
        side="LONG",
        entry_price=10.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert fill.filled is True
    assert fill.source == "m1_low"


def test_m1_ordered_path_oracle_resolves_target_before_stop_across_bars() -> None:
    result = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:00:00+00:00",
                "high": 110.0,
                "low": 90.0,
            },
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 100.5,
                "low": 99.5,
            },
            {
                "time_utc": "2026-01-01T00:02:00+00:00",
                "high": 105.25,
                "low": 100.5,
            },
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert result.status == "resolved"
    assert result.fill_time_utc == "2026-01-01T00:01:00+00:00"
    assert result.terminal_outcome == "target_reached_before_stop"
    assert result.target_first_touch_utc == "2026-01-01T00:02:00+00:00"
    assert result.stop_first_touch_utc is None
    assert result.mfe_r == 1.05
    assert result.mae_r == -0.1
    assert result.adverse_before_profit_flag is True
    assert result.milestones["1r"]["reached"] is True
    assert result.milestones["1r"]["minutes_to_first_touch"] == 1.0
    assert result.decision_input_boundary.startswith("asof_safe")


def test_m1_passive_first_touch_without_queue_evidence_is_diagnostic() -> None:
    result = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 100.1,
                "low": 100.0,
                "close": 100.2,
            },
            {
                "time_utc": "2026-01-01T00:02:00+00:00",
                "high": 100.6,
                "low": 100.1,
                "close": 100.4,
            },
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.02,
        passive_limit_queue_min_touch_count=2,
    )

    assert result.fill_status == "not_filled_passive_limit_queue_realism_not_confirmed"
    assert result.terminal_outcome == "first_touch_optimistic_queue_realism_failed"
    assert result.fill_realism_class == "first_touch_optimistic"
    assert result.fill_realism_executable is False
    assert result.entry_first_touch_utc == "2026-01-01T00:01:00+00:00"
    assert result.passive_limit_queue_touch_count == 1
    assert result.passive_limit_queue_realism_passed is False
    assert result.fill_realism_diagnostic_fill_time_utc == "2026-01-01T00:01:00+00:00"


def test_m1_passive_penetration_or_second_touch_passes_queue_realism() -> None:
    penetrated = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 100.1,
                "low": 99.97,
                "close": 100.2,
            },
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.02,
        passive_limit_queue_min_touch_count=2,
    )
    second_touch = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 100.4,
                "low": 100.0,
                "close": 100.2,
            },
            {
                "time_utc": "2026-01-01T00:02:00+00:00",
                "high": 100.2,
                "low": 100.0,
                "close": 100.4,
            },
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.02,
        passive_limit_queue_min_touch_count=2,
    )

    assert penetrated.fill_status == "filled_from_ordered_m1_path"
    assert penetrated.fill_realism_class == "passive_queue_confirmed"
    assert penetrated.fill_realism_executable is True
    assert penetrated.passive_limit_queue_max_penetration_r == 0.03
    assert second_touch.fill_time_utc == "2026-01-01T00:02:00+00:00"
    assert second_touch.passive_limit_queue_touch_count == 2
    assert second_touch.fill_realism_class == "passive_queue_confirmed"


def test_m1_ordered_path_oracle_flags_same_bar_target_stop_ambiguity() -> None:
    result = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 106.0,
                "low": 94.0,
            }
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert result.status == "ambiguous_requires_tick"
    assert result.same_bar_ambiguity is True
    assert result.target_first_touch_utc == "2026-01-01T00:01:00+00:00"
    assert result.stop_first_touch_utc == "2026-01-01T00:01:00+00:00"
    assert "ordered_tick_required_for_same_bar_target_stop_sequence" in result.source_gaps


def test_tick_ordered_path_oracle_excludes_asof_rows_and_resolves_stop_first() -> None:
    result = infer_ordered_path_from_ticks(
        ticks=[
            {
                "ts_utc": "2026-01-01T00:00:00+00:00",
                "bid": 110.0,
                "ask": 110.1,
            },
            {
                "ts_utc": "2026-01-01T00:00:05+00:00",
                "bid": 99.8,
                "ask": 99.95,
            },
            {
                "ts_utc": "2026-01-01T00:00:10+00:00",
                "bid": 95.0,
                "ask": 95.1,
            },
            {
                "ts_utc": "2026-01-01T00:00:20+00:00",
                "bid": 106.0,
                "ask": 106.1,
            },
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert result.status == "resolved"
    assert result.source == "tick"
    assert result.fill_time_utc == "2026-01-01T00:00:05+00:00"
    assert result.terminal_outcome == "stop_reached_before_target"
    assert result.stop_first_touch_utc == "2026-01-01T00:00:10+00:00"
    assert result.target_first_touch_utc is None
    assert result.same_bar_ambiguity is False
    assert result.adverse_before_profit_flag is True


def test_ordered_path_oracle_keeps_missing_fill_as_source_gap() -> None:
    result = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 105.0,
                "low": 101.0,
            }
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert result.status == "source_gap"
    assert result.fill_status == "not_filled_in_post_asof_m1_path"
    assert result.terminal_outcome == "not_filled"
    assert "entry_not_touched_in_post_asof_m1_path" in result.source_gaps


def test_local_file_ordered_path_adapter_prefers_ticks_over_m1_ambiguity(tmp_path: Path) -> None:
    m1_path = tmp_path / "XAUUSD.csv"
    tick_path = tmp_path / "XAUUSD.jsonl"
    m1_path.write_text(
        "time_utc,symbol,open,high,low,close\n"
        "2026-01-01T00:01:00+00:00,XAUUSD,100,106,94,100\n",
        encoding="utf-8",
    )
    tick_path.write_text(
        '{"ts_utc":"2026-01-01T00:00:05+00:00","bid":99.8,"ask":99.95}\n'
        '{"ts_utc":"2026-01-01T00:00:10+00:00","bid":105.2,"ask":105.3}\n'
        '{"ts_utc":"2026-01-01T00:00:20+00:00","bid":94.8,"ask":94.9}\n',
        encoding="utf-8",
    )

    result = infer_ordered_path_from_local_files(
        m1_path=m1_path,
        tick_path=tick_path,
        side="LONG",
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
        asof_utc="2026-01-01T00:00:00+00:00",
    )

    assert result.source == "tick"
    assert result.terminal_outcome == "target_reached_before_stop"
    assert result.same_bar_ambiguity is False


def test_passive_queue_zero_penetration_floor_still_requires_repeated_touch() -> None:
    result = infer_ordered_path_from_m1(
        bars=[
            {
                "time_utc": "2026-01-01T00:01:00+00:00",
                "high": 100.2,
                "low": 100.0,
            }
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.0,
        passive_limit_queue_min_touch_count=2,
    )

    assert result.fill_status == "not_filled_passive_limit_queue_realism_not_confirmed"
    assert result.passive_limit_queue_touch_count == 1
    assert result.passive_limit_queue_max_penetration_price == 100.0
    assert result.passive_limit_queue_max_penetration_r == 0.0
    assert result.passive_limit_queue_realism_passed is False
    assert result.diagnostic_fill_only is True
    assert result.package_execution_result_scope == "diagnostic_counterfactual_only"


def test_local_file_adapter_propagates_passive_queue_contract(tmp_path: Path) -> None:
    m1_path = tmp_path / "XAUUSD.csv"
    m1_path.write_text(
        "time_utc,symbol,open,high,low,close\n"
        "2026-01-01T00:01:00+00:00,XAUUSD,100.1,100.2,100.0,100.1\n",
        encoding="utf-8",
    )

    result = infer_ordered_path_from_local_files(
        m1_path=m1_path,
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.0,
        passive_limit_queue_min_touch_count=2,
    )

    assert result.source == "m1"
    assert result.fill_realism_class == "first_touch_optimistic"
    assert result.fill_realism_executable is False
    assert result.passive_limit_queue_realism_passed is False


def test_tick_queue_records_market_penetration_price_and_r() -> None:
    result = infer_ordered_path_from_ticks(
        ticks=[
            {
                "ts_utc": "2026-01-01T00:01:00+00:00",
                "bid": 99.95,
                "ask": 99.97,
            }
        ],
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        asof_utc="2026-01-01T00:00:00+00:00",
        passive_limit_queue_realism_enabled=True,
        passive_limit_queue_min_penetration_r=0.02,
        passive_limit_queue_min_touch_count=2,
    )

    assert result.fill_status == "filled_from_ordered_tick_path"
    assert result.passive_limit_queue_max_penetration_price == 99.97
    assert result.passive_limit_queue_max_penetration_r == 0.03


def test_fresh_day_prop_curve_blocks_after_daily_headroom_is_consumed() -> None:
    rows = simulate_fresh_day_prop_curve(
        [
            DayPropDecision("win", "2026-01-01T00:00:00+00:00", 1.0, 2.0),
            DayPropDecision("loss", "2026-01-01T01:00:00+00:00", 1.0, -4.5),
            DayPropDecision("blocked", "2026-01-01T02:00:00+00:00", 1.0, 2.0),
        ],
        daily_drawdown_limit_r=3.0,
    )

    assert rows[0]["allowed"] is True
    assert rows[0]["day_realized_r_after"] == 2.0
    assert rows[1]["allowed"] is True
    assert rows[1]["day_realized_r_after"] == -2.5
    assert rows[2]["daily_drawdown_blocked"] is True
    assert rows[2]["allowed"] is False
