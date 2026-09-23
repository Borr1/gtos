from __future__ import annotations

from pathlib import Path

from src.research_infra.trade_index_lifecycle_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_BLOCKERS,
    build_inventory_index,
    build_rolling_status,
    build_trade_index_lifecycle_rows,
)


def _record(
    *,
    symbol: str = "XAUUSD",
    trade_id: str = "lim_2026-05-04_0715",
    final_outcome: str = "LIMIT_PLACED",
    execution=None,
    exit_payload=None,
) -> dict:
    return {
        "metadata": {
            "trade_id": f"{symbol}_2026-05-04_london_0715",
            "date": "2026-05-04",
            "symbol": symbol,
            "kill_zone": "london",
            "candle_close_utc": "2026-05-04T07:15:00+00:00",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_direction": "SHORT",
            "ai_framework": "ob_retest",
            "final_outcome": final_outcome,
            "level2_verification": {"passed": final_outcome != "REJECTED_L2"},
        },
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 100.0,
            "stop_loss": 101.0,
            "take_profit_1": 98.5,
        },
        "limit_intent": {
            "trade_id": trade_id,
            "limit_price": 100.0,
            "stop_loss": 101.0,
            "take_profit_1": 98.5,
        },
        "execution": execution,
        "exit": exit_payload,
    }


def _pending_audit(path: str, **overrides) -> dict:
    row = {
        "row_key": "pending1",
        "trade_record_path": path,
        "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "final_state": "NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH",
        "final_state_status": "FINAL_TERMINAL_NO_FILL",
        "missed_move_classification": "NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH",
        "trade_id_global_uniqueness_status": "UNIQUE_IN_LIFECYCLE_LOG",
    }
    row.update(overrides)
    return row


def test_inventory_index_count_matches_trade_records(tmp_path):
    root = tmp_path / "trade_records"
    path1 = root / "XAUUSD" / "2026-05-04_london_0715.json"
    path2 = root / "GBPJPY" / "2026-05-04_london_0715.json"
    rows = build_trade_index_lifecycle_rows(
        trade_records=[(path1, _record(symbol="XAUUSD")), (path2, _record(symbol="GBPJPY", final_outcome="REJECTED_L2"))],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    index = build_inventory_index(rows, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert index["index_count"] == 2
    assert index["trade_record_count"] == 2
    assert index["index_count_equals_trade_record_count"] is True
    assert index["legacy_trade_index_status"] == "LEGACY_TRADE_INDEX_DEPRECATED_FOR_CURRENT_COUNTS"


def test_limit_placed_with_pending_audit_is_complete_and_preserves_missed_move():
    root = Path("knowledge_base/trade_records")
    path = root / "XAUUSD" / "2026-05-04_london_0715.json"
    rows = build_trade_index_lifecycle_rows(
        trade_records=[(path, _record(symbol="XAUUSD"))],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[(1, _pending_audit("XAUUSD/2026-05-04_london_0715.json"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]

    assert row["trade_index_lifecycle_status"] == COMPLETE_WITH_BLOCKERS
    assert row["lifecycle_completeness"] == "LIMIT_PLACED_COMPLETE_WITH_PENDING_LIFECYCLE_AUDIT"
    assert row["pending_lifecycle_missed_move_classification"] == "NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH"
    assert "PENDING_LIFECYCLE_PRESENT_IN_AUDIT_NOT_EMBEDDED_IN_TRADE_RECORD" in row["documented_limitation_codes"]


def test_source_only_missing_pending_group_does_not_change_trade_index_contract():
    root = Path("knowledge_base/trade_records")
    path = root / "XAUUSD" / "2026-05-04_london_0715.json"
    source_only_gap = _pending_audit(
        "knowledge_base\\trade_records\\XAUUSD\\2026-05-04_london_0715.json",
        pending_limit_lifecycle_audit_status="PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED",
        final_state="PENDING_LIFECYCLE_GROUP_MISSING",
        final_state_status="ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH",
        manual_backfill_status="SOURCE_ONLY_NO_LIFECYCLE_GROUP",
        missed_move_classification="NO_LIFECYCLE_GROUP",
    )

    rows = build_trade_index_lifecycle_rows(
        trade_records=[(path, _record(symbol="XAUUSD"))],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[(1, source_only_gap)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["has_pending_lifecycle_audit"] is False
    assert row["pending_lifecycle_audit_row_key"] is None
    assert row["trade_index_lifecycle_status"] == COMPLETE_WITH_BLOCKERS
    assert row["lifecycle_completeness"] == "LIMIT_PLACED_DOCUMENTED_LEGACY_LIFECYCLE_GAP"
    assert "MATCHED_PENDING_LIFECYCLE_AUDIT_ACTION_REQUIRED" not in row["action_required_codes"]


def test_cross_symbol_raw_trade_id_collision_is_documented():
    root = Path("knowledge_base/trade_records")
    rows = build_trade_index_lifecycle_rows(
        trade_records=[
            (root / "XAUUSD" / "2026-05-04_london_0715.json", _record(symbol="XAUUSD", trade_id="lim_same")),
            (root / "NAS100" / "2026-05-04_london_0715.json", _record(symbol="NAS100", trade_id="lim_same")),
        ],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    by_symbol = {row["symbol"]: row for row in rows}

    assert by_symbol["XAUUSD"]["raw_trade_id_collision_symbols"] == ["NAS100"]
    assert by_symbol["NAS100"]["raw_trade_id_collision_symbols"] == ["XAUUSD"]
    assert "LEGACY_RAW_TRADE_ID_NOT_GLOBALLY_UNIQUE" in by_symbol["XAUUSD"]["documented_limitation_codes"]


def test_wrong_side_cancel_and_pending_open_states_are_preserved():
    root = Path("knowledge_base/trade_records")
    wrong_side = _pending_audit(
        "XAUUSD/2026-05-04_london_0715.json",
        final_state="NO_FILL_CANCELLED_WRONG_SIDE",
        final_state_status="FINAL_TERMINAL_NO_FILL",
        missed_move_classification="ENTRY_THEN_SL",
    )
    still_open = _pending_audit(
        "GBPJPY/2026-05-04_tokyo_0300.json",
        row_key="pending2",
        final_state="NO_FILL_STILL_PENDING",
        final_state_status="STILL_ACTIVE_PENDING",
        missed_move_classification="NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH",
    )
    rows = build_trade_index_lifecycle_rows(
        trade_records=[
            (root / "XAUUSD" / "2026-05-04_london_0715.json", _record(symbol="XAUUSD")),
            (root / "GBPJPY" / "2026-05-04_tokyo_0300.json", _record(symbol="GBPJPY", trade_id="lim_other")),
        ],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[(1, wrong_side), (2, still_open)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    states = {row["symbol"]: row["pending_lifecycle_final_state"] for row in rows}

    assert states["XAUUSD"] == "NO_FILL_CANCELLED_WRONG_SIDE"
    assert states["GBPJPY"] == "NO_FILL_STILL_PENDING"


def test_exit_without_execution_is_documented_broker_position_mismatch():
    root = Path("knowledge_base/trade_records")
    rows = build_trade_index_lifecycle_rows(
        trade_records=[
            (
                root / "NAS100" / "2026-04-29_ny_1500.json",
                _record(
                    symbol="NAS100",
                    exit_payload={"exit_type": "broker_closed", "actual_r": -1.0, "realized_R": -1.0},
                ),
            )
        ],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]

    assert row["trade_index_lifecycle_status"] == COMPLETE_WITH_BLOCKERS
    assert row["lifecycle_completeness"] == "LIMIT_PLACED_COMPLETE_WITH_EXIT"
    assert row["broker_position_mismatch_status"] == "EXIT_PRESENT_EXECUTION_FIELD_NULL_ACCOUNT_HISTORY_REQUIRED"
    assert "TRADE_RECORD_EXIT_PRESENT_BUT_EXECUTION_FIELD_NULL" in row["documented_limitation_codes"]


def test_action_required_rows_are_counted():
    root = Path("knowledge_base/trade_records")
    rows = build_trade_index_lifecycle_rows(
        trade_records=[
            (
                root / "XAUUSD" / "2026-05-04_london_0715.json",
                _record(symbol="XAUUSD", final_outcome="FILLED", execution=None, exit_payload=None),
            )
        ],
        trade_records_root=root,
        pending_lifecycle_audit_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    status = build_rolling_status(rows, legacy_index={"trades": []})

    assert rows[0]["trade_index_lifecycle_status"] == ACTION_REQUIRED
    assert status["action_required_rows"] == 1
