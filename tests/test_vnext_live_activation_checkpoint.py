from __future__ import annotations

import json
from datetime import datetime, timezone

from scripts import build_vnext_live_activation_checkpoint as checkpoint


def test_tick_stale_classifies_alive_outside_session_waiting_for_initial_tick() -> None:
    row = {
        "daemon_alive": True,
        "last_msc": None,
        "total_ticks_written": 0,
    }
    broker = {
        "info_exists": True,
        "broker_tick_time_msc": 1780095479838,
        "broker_tick_bid": 25051.67,
        "broker_tick_ask": 25053.67,
        "broker_tick_not_advanced_since_capture": False,
    }
    session = {"status": "outside_repo_configured_session"}

    assert checkpoint._tick_stale_classification(row, broker, session) == (
        "daemon_alive_outside_repo_session_waiting_for_first_broker_tick"
    )
    assert row["no_initial_capture_reason"] == (
        "daemon_alive_outside_repo_session_waiting_for_first_tick_after_restart"
    )


def test_tick_stale_does_not_mask_inside_session_initial_tick_absence() -> None:
    row = {
        "daemon_alive": True,
        "last_msc": None,
        "total_ticks_written": 0,
    }
    broker = {
        "info_exists": True,
        "broker_tick_time_msc": 1780095479838,
        "broker_tick_bid": 25051.67,
        "broker_tick_ask": 25053.67,
        "broker_tick_not_advanced_since_capture": False,
    }
    session = {"status": "inside_repo_configured_session"}

    assert checkpoint._tick_stale_classification(row, broker, session) is None


def test_tick_stale_classifies_inside_session_broker_quote_pre_restart() -> None:
    row = {
        "daemon_alive": True,
        "daemon_start_utc": "2026-05-30T23:05:07.099000+00:00",
        "last_msc": None,
        "total_ticks_written": 0,
    }
    broker = {
        "info_exists": True,
        "broker_tick_time_msc": 1780099199182,
        "broker_tick_bid": 73669.22,
        "broker_tick_ask": 73692.68,
        "broker_tick_not_advanced_since_capture": False,
    }
    session = {"status": "inside_repo_configured_session"}

    assert checkpoint._tick_stale_classification(row, broker, session) == (
        "daemon_alive_broker_quote_pre_restart_no_new_tick_after_restart"
    )
    assert row["no_initial_capture_reason"] == (
        "daemon_alive_broker_quote_pre_restart_waiting_for_next_broker_tick"
    )


def test_tick_stale_still_classifies_static_broker_tick() -> None:
    row = {
        "daemon_alive": True,
        "last_msc": 1780095479838,
        "total_ticks_written": 100,
    }
    broker = {
        "info_exists": True,
        "broker_tick_time_msc": 1780095479838,
        "broker_tick_bid": 25051.67,
        "broker_tick_ask": 25053.67,
        "broker_tick_not_advanced_since_capture": True,
    }
    session = {"status": "outside_repo_configured_session"}

    assert checkpoint._tick_stale_classification(row, broker, session) == (
        "daemon_alive_outside_repo_session_broker_tick_not_advanced"
    )


def test_open_position_with_lifecycle_row_reconciles_when_entry_deal_aged_out(tmp_path, monkeypatch):
    lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle_path.write_text(
        json.dumps(
            {
                "gtos_vnext_dynamic_policy_applied": True,
                "broker_fill_state": "filled",
                "mt5_position_ticket": 111,
                "mt5_entry_order_ticket": 111,
                "candidate_id": "broadorigin_test",
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(checkpoint, "PENDING_LIMIT_LIFECYCLE_PATH", lifecycle_path)

    mt5 = {
        "position_details": [{"ticket": 111, "magic": checkpoint.GTOS_MAGIC_NUMBER}],
        "order_details": [],
        "history_order_tail": [],
        "history_deal_tail": [],
    }

    summary = checkpoint._broker_lifecycle_summary(mt5)

    assert summary["reconciled_open_position_ids"] == [111]
    assert summary["unreconciled_open_position_ids"] == []
    assert summary["unreconciled_open_exposure_count"] == 0
    assert summary["open_position_entry_deal_aged_out_ids"] == [111]


def test_open_position_without_lifecycle_row_stays_unreconciled(tmp_path, monkeypatch):
    lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(checkpoint, "PENDING_LIMIT_LIFECYCLE_PATH", lifecycle_path)

    mt5 = {
        "position_details": [{"ticket": 222, "magic": checkpoint.GTOS_MAGIC_NUMBER}],
        "order_details": [],
        "history_order_tail": [],
        "history_deal_tail": [],
    }

    summary = checkpoint._broker_lifecycle_summary(mt5)

    assert summary["reconciled_open_position_ids"] == []
    assert summary["unreconciled_open_position_ids"] == [222]
    assert summary["unreconciled_open_exposure_count"] == 1


def test_broker_lifecycle_summary_preserves_all_matched_rows(tmp_path, monkeypatch):
    lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle_path.write_text(
        "".join(
            json.dumps(
                {
                    "gtos_vnext_dynamic_policy_applied": True,
                    "broker_fill_state": "filled",
                    "mt5_position_ticket": 111,
                    "mt5_entry_order_ticket": 111,
                    "candidate_id": f"broadorigin_{idx}",
                    "trade_id": f"lim_NAS100_row_{idx}",
                    "symbol": "NAS100",
                    "broker_symbol": "NDX100",
                }
            )
            + "\n"
            for idx in range(6)
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(checkpoint, "PENDING_LIMIT_LIFECYCLE_PATH", lifecycle_path)
    mt5 = {
        "position_details": [{"ticket": 111, "magic": checkpoint.GTOS_MAGIC_NUMBER}],
        "order_details": [],
        "history_order_tail": [],
        "history_deal_tail": [],
    }

    summary = checkpoint._broker_lifecycle_summary(mt5)

    matched = summary["matched_pending_lifecycle_rows"]
    assert len(matched) == 6
    assert matched[0]["trade_id"] == "lim_NAS100_row_0"
    assert matched[-1]["trade_id"] == "lim_NAS100_row_5"


def test_open_position_reconciles_from_lane06_lifecycle_fallback(tmp_path, monkeypatch):
    pending_path = tmp_path / "pending_limit_lifecycle.jsonl"
    pending_path.write_text("", encoding="utf-8")
    lane06_path = tmp_path / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
    lane06_path.write_text(
        json.dumps(
            {
                "schema_version": "lane06_broker_lifecycle_v1",
                "ticket": 111,
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "side": "LONG",
                "selected_policy": "partial_be_runner",
                "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                "broker_lifecycle_status": "PARTIAL_CLOSED_RESIDUAL_OPEN_BROKER",
                "entry_order_tickets": [111],
                "entry_deal_tickets": [999],
                "open_position_present": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(checkpoint, "PENDING_LIMIT_LIFECYCLE_PATH", pending_path)
    monkeypatch.setattr(checkpoint, "LANE06_BROKER_LIFECYCLE_PATH", lane06_path)
    mt5 = {
        "position_details": [{"ticket": 111, "magic": checkpoint.GTOS_MAGIC_NUMBER}],
        "order_details": [],
        "history_order_tail": [],
        "history_deal_tail": [],
    }

    summary = checkpoint._broker_lifecycle_summary(mt5)

    assert summary["reconciled_open_position_ids"] == [111]
    assert summary["unreconciled_open_position_ids"] == []
    assert summary["matched_pending_lifecycle_rows"][0][
        "_checkpoint_lifecycle_source"
    ] == "lane06_broker_lifecycle"


def test_candidate_summary_counts_old_system_absence_from_native_packet(monkeypatch) -> None:
    from scripts import build_vnext_post_reload_candidate_proof as proof_builder

    def fake_build_post_reload(*, reload_ts_text=None, snapshot_upper_bound_text=None):
        row = {
            "packet_capture_mode": "native_live_writer",
            "dynamic_policy_selected": "partial_be_runner",
            "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
            "final_outcome": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
            "record_mtime_utc": "2026-06-01T05:00:00+00:00",
            "packet": {
                "old_primary_analyzer_called": False,
                "old_l2_required": False,
                "old_system_absence_proof": {
                    "old_primary_analyzer_called": False,
                    "old_l2_required": False,
                    "absence_status": "explicit_absent",
                },
            },
        }
        summary = {
            "reload_timestamp_utc": reload_ts_text,
            "packet_capture_mode_counts": {"native_live_writer": 1},
            "repair_entry_counts": {"not_entered": 1},
            "rows_missing_required_packet_fields": 0,
            "rows_with_null_zero_without_reason": 0,
            "order_path_rows": 0,
        }
        return [row], summary

    monkeypatch.setattr(proof_builder, "build", fake_build_post_reload)

    summary = checkpoint._candidate_summary(
        datetime(2026, 6, 1, 5, 1, tzinfo=timezone.utc),
        reload_ts_text="2026-06-01T04:00:00+00:00",
    )

    assert summary["old_primary_analyzer_field_present_count"] == 1
    assert summary["old_l2_required_field_present_count"] == 1
    assert summary["old_primary_analyzer_field_missing_count"] == 0
    assert summary["old_l2_required_field_missing_count"] == 0
    assert summary["old_primary_analyzer_l2_absence_proof_status"] == (
        "explicit_false_on_all_rows"
    )
    assert summary["native_old_primary_analyzer_l2_absence_proof_status"] == (
        "explicit_false_on_native_live_writer_rows"
    )


def test_process_version_proof_requires_reload_after_current_runtime_commit(monkeypatch) -> None:
    monkeypatch.setattr(
        checkpoint,
        "_git_head",
        lambda: {"head": "abc123", "head_short": "abc123", "head_subject": "runtime change"},
    )
    monkeypatch.setattr(checkpoint, "_sha256_file", lambda path: "hash")
    monkeypatch.setattr(
        checkpoint,
        "_combined_hash",
        lambda paths: {"sha256": "combined", "files": []},
    )
    monkeypatch.setattr(
        checkpoint,
        "_latest_commit_for_paths",
        lambda paths: {
            "head": "runtime123",
            "committed_at_utc": "2026-05-31T07:00:00+00:00",
            "subject": "runtime selector change",
            "paths": paths,
        },
    )
    monkeypatch.setattr(checkpoint.subprocess, "call", lambda *args, **kwargs: 0)
    process = {
        "orchestrator_python": len(checkpoint.EXPECTED_SYMBOLS),
        "missing_orchestrator_symbols": [],
        "extra_orchestrator_symbols": [],
        "all_orchestrators_started_after_required_post_786_commit": True,
        "oldest_orchestrator_start_utc": "2026-05-31T06:59:00+00:00",
        "newest_orchestrator_start_utc": "2026-05-31T06:59:00+00:00",
        "orchestrators": [
            {
                "symbol": symbol,
                "pid": index,
                "creation_date_utc": "2026-05-31T06:59:00+00:00",
            }
            for index, symbol in enumerate(checkpoint.EXPECTED_SYMBOLS, start=1)
        ],
    }

    proof = checkpoint._process_version_proof(
        datetime(2026, 5, 31, 7, 5, tzinfo=timezone.utc),
        process,
    )

    assert proof["proof_status"] == "reload_required_or_process_proof_incomplete"
    assert proof["required_runtime_reload_after_utc"] == "2026-05-31T07:00:00+00:00"
    assert len(proof["stale_or_unproven_orchestrators"]) == len(checkpoint.EXPECTED_SYMBOLS)
    assert proof["stale_or_unproven_orchestrators"][0]["stale_reason"] == (
        "process_started_before_current_runtime_surface_commit"
    )


def test_process_version_proof_accepts_processes_after_current_runtime_commit(monkeypatch) -> None:
    monkeypatch.setattr(
        checkpoint,
        "_git_head",
        lambda: {"head": "abc123", "head_short": "abc123", "head_subject": "runtime change"},
    )
    monkeypatch.setattr(checkpoint, "_sha256_file", lambda path: "hash")
    monkeypatch.setattr(
        checkpoint,
        "_combined_hash",
        lambda paths: {"sha256": "combined", "files": []},
    )
    monkeypatch.setattr(
        checkpoint,
        "_latest_commit_for_paths",
        lambda paths: {
            "head": "runtime123",
            "committed_at_utc": "2026-05-31T07:00:00+00:00",
            "subject": "runtime selector change",
            "paths": paths,
        },
    )
    monkeypatch.setattr(checkpoint.subprocess, "call", lambda *args, **kwargs: 0)
    process = {
        "orchestrator_python": len(checkpoint.EXPECTED_SYMBOLS),
        "missing_orchestrator_symbols": [],
        "extra_orchestrator_symbols": [],
        "all_orchestrators_started_after_required_post_786_commit": True,
        "oldest_orchestrator_start_utc": "2026-05-31T07:01:00+00:00",
        "newest_orchestrator_start_utc": "2026-05-31T07:01:00+00:00",
        "orchestrators": [
            {
                "symbol": symbol,
                "pid": index,
                "creation_date_utc": "2026-05-31T07:01:00+00:00",
            }
            for index, symbol in enumerate(checkpoint.EXPECTED_SYMBOLS, start=1)
        ],
    }

    proof = checkpoint._process_version_proof(
        datetime(2026, 5, 31, 7, 5, tzinfo=timezone.utc),
        process,
    )

    assert proof["proof_status"] == "all_24_live_orchestrators_running_current_runtime_surface"
    assert proof["stale_or_unproven_orchestrators"] == []
