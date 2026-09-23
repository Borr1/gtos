from __future__ import annotations

import json
import os
from pathlib import Path

import scripts.dual_broker_trade_record_projector as projector
from scripts.dual_broker_trade_record_projector import project_once


def _write_record(path: Path, trade_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "trade_id": f"{trade_id}_record",
                    "symbol": "XAUUSD",
                    "candidate_id": "cand-1",
                    "kill_zone": "ny",
                },
                "limit_intent": {
                    "trade_id": trade_id,
                    "direction": "LONG",
                    "limit_price": 2350.0,
                    "stop_loss": 2340.0,
                    "take_profit_1": 2370.0,
                    "risk_pct": 1.0,
                    "broker_symbol": "XAUUSD",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_filled_vnext_record(path: Path, trade_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "trade_id": f"{trade_id}_record",
                    "symbol": "XAUUSD",
                    "candidate_id": "cand-vnext",
                    "kill_zone": "ny",
                },
                "execution": {
                    "trade_id": trade_id,
                    "broker_fill_state": "filled",
                    "fill_time_utc": "2026-06-02T08:00:00+00:00",
                    "entry_order_ticket": 12345,
                    "direction": "LONG",
                    "entry_price": 2350.0,
                    "stop_loss": 2340.0,
                    "take_profit_1": 2370.0,
                    "risk_pct": 0.5,
                    "broker_symbol": "XAUUSD",
                },
                "decision_pipeline": {
                    "gtos_vnext_moonshot_dynamic_execution": {
                        "selected_policy": "partial_be_runner",
                        "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                        "applied": True,
                        "replaced_policy": "retired_static_baseline_comparator",
                        "source_event": {
                            "selected_cell_risk_allowed": True,
                            "selected_cell_risk_pct": 0.5,
                            "selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-UNIT",
                            "selected_cell_risk_unresolved_reasons": [],
                            "selected_cell_risk_execution_critical_unresolved_reasons": [],
                            "selected_cell_risk_selected_policy": "partial_be_runner",
                            "selected_cell_risk_source_policy": "be_after_trigger",
                            "selected_cell_risk_policy_identity_status": "policy_invariant_broker_geometry_for_selected_execution_policy",
                        },
                    },
                    "gtos_vnext_candidate_intelligence_packet": {
                        "dynamic_policy": {
                            "dynamic_trigger_final_pullback": {
                                "selected_policy": "partial_be_runner",
                                "partial_trigger_r": 1.0,
                                "partial_final_target_r": 3.0,
                                "partial_close_ratio": 0.5,
                            }
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_projector_state_write_retries_transient_permission_error(
    tmp_path: Path,
    monkeypatch,
):
    state = tmp_path / "state.json"
    calls = {"count": 0}
    real_replace = os.replace

    def flaky_replace(src: str, dst: str) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("simulated windows file lock")
        real_replace(src, dst)

    monkeypatch.setattr(projector.os, "replace", flaky_replace)

    projector._write_json(state, {"status": "ok"})

    assert calls["count"] == 2
    assert json.loads(state.read_text(encoding="utf-8")) == {"status": "ok"}


def test_projector_state_write_preserves_prior_state_on_repeated_file_lock(
    tmp_path: Path,
    monkeypatch,
):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"status": "previous"}), encoding="utf-8")

    def locked_replace(src: str, dst: str) -> None:
        raise PermissionError("simulated persistent file lock")

    monkeypatch.setattr(projector.os, "replace", locked_replace)

    projector._write_json(state, {"status": "new"})

    assert json.loads(state.read_text(encoding="utf-8")) == {"status": "previous"}


def test_projector_initializes_at_end_without_replaying_existing_records(tmp_path: Path):
    source_root = tmp_path / "records"
    _write_record(source_root / "XAUUSD" / "record.json", "lim_existing")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=False,
    )

    assert summary["status"] == "initialized_at_end"
    assert not intent_log.exists()
    saved_state = json.loads(state.read_text(encoding="utf-8"))
    assert saved_state["projection_outcomes"][str(source_root / "XAUUSD" / "record.json")][
        "status"
    ] == "start_at_end_baseline"


def test_projector_ignores_pending_record_indexes(tmp_path: Path):
    source_root = tmp_path / "records"
    _write_record(source_root / "XAUUSD" / "record.json", "lim_existing")
    index_path = source_root / "XAUUSD" / "_pending_records_index.json"
    index_path.write_text(json.dumps({"pending": []}), encoding="utf-8")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=False,
    )

    saved_state = json.loads(state.read_text(encoding="utf-8"))
    assert summary["records_seen"] == 1
    assert str(index_path) not in saved_state["seen"]
    assert str(index_path) not in saved_state["projection_outcomes"]


def test_projector_reprocesses_legacy_seen_record_without_projection_outcome(
    tmp_path: Path,
):
    source_root = tmp_path / "records"
    record_path = source_root / "XAUUSD" / "record.json"
    _write_record(record_path, "lim_legacy_seen")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"
    state.write_text(
        json.dumps(
            {
                "projection_not_before_utc": "2026-06-02T07:00:00+00:00",
                "seen": {
                    str(record_path): {
                        "mtime_ns": record_path.stat().st_mtime_ns,
                        "size": record_path.stat().st_size,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=False,
    )

    intent_rows = _read_rows(intent_log)
    action_rows = _read_rows(action_log)
    saved_state = json.loads(state.read_text(encoding="utf-8"))
    outcome = saved_state["projection_outcomes"][str(record_path)]

    assert summary["projected"] == 1
    assert intent_rows[0]["intent_type"] == "pending_limit"
    assert action_rows[0]["event"] == "trade_record_projected"
    assert action_rows[0]["state_repair_reason"] == (
        "seen_signature_without_projection_outcome"
    )
    assert outcome["status"] == "appended"
    assert outcome["state_repair_reason"] == "seen_signature_without_projection_outcome"


def test_projector_replay_existing_emits_pending_limit_intent(tmp_path: Path):
    source_root = tmp_path / "records"
    _write_record(source_root / "XAUUSD" / "record.json", "lim_replay")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=True,
    )
    rows = _read_rows(intent_log)

    assert summary["projected"] == 1
    assert rows[0]["intent_type"] == "pending_limit"
    assert rows[0]["source"]["runtime_namespace"] == "redacted_account_live_bee34003"


def test_projector_replay_existing_enriches_vnext_execution_context(tmp_path: Path):
    source_root = tmp_path / "records"
    _write_filled_vnext_record(source_root / "XAUUSD" / "record.json", "lim_vnext")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=True,
    )
    rows = _read_rows(intent_log)

    assert summary["projected"] == 1
    assert rows[0]["intent_type"] == "market_entry"
    assert rows[0]["dynamic_context"]["gtos_vnext_dynamic_policy_applied"] is True
    assert rows[0]["dynamic_context"]["gtos_vnext_selected_cell_risk_selected_policy"] == "partial_be_runner"
    assert rows[0]["dynamic_context"]["gtos_vnext_dynamic_partial_close_ratio"] == 0.5


def test_projector_treats_sl_rewrite_as_duplicate_not_new_intent(tmp_path: Path):
    source_root = tmp_path / "records"
    record_path = source_root / "XAUUSD" / "record.json"
    _write_record(record_path, "lim_lifecycle")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    first = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=True,
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["limit_intent"]["stop_loss"] = 2350.0
    record["limit_intent"]["take_profit_1"] = 2399.0
    record_path.write_text(json.dumps(record), encoding="utf-8")

    second = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=True,
    )

    rows = _read_rows(intent_log)
    assert first["projected"] == 1
    assert second["projected"] == 0
    assert second["duplicates"] == 1
    assert len(rows) == 1


def test_projector_skips_old_filled_record_repaired_after_activation(tmp_path: Path):
    source_root = tmp_path / "records"
    record_path = source_root / "XAUUSD" / "record.json"
    _write_filled_vnext_record(record_path, "lim_old_fill")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    state.write_text(
        json.dumps(
            {
                "projection_not_before_utc": "2026-06-02T09:00:00+00:00",
                "seen": {
                    str(record_path): {
                        "mtime_ns": record_path.stat().st_mtime_ns,
                        "size": record_path.stat().st_size,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record.setdefault("instrumentation", {})[
        "gtos_vnext_active_lifecycle_truth_status"
    ] = "full_position_open_lifecycle_aligned_from_broker_probe"
    record_path.write_text(json.dumps(record), encoding="utf-8")

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=False,
    )

    assert summary["projected"] == 0
    assert summary["freshness_skipped"] == 1
    assert not intent_log.exists()
    action_rows = _read_rows(action_log)
    assert action_rows[0]["event"] == "trade_record_projection_skipped"
    assert action_rows[0]["reason"] == "filled_record_event_time_before_projection_activation"


def test_projector_skips_stale_filled_record_after_live_projection_window(
    tmp_path: Path,
):
    source_root = tmp_path / "records"
    record_path = source_root / "XAUUSD" / "record.json"
    _write_filled_vnext_record(record_path, "lim_stale_fill")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"
    state.write_text(
        json.dumps(
            {
                "projection_not_before_utc": "2026-06-02T07:00:00+00:00",
                "seen": {},
            }
        ),
        encoding="utf-8",
    )

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=False,
        max_filled_record_age_seconds=1.0,
    )

    assert summary["projected"] == 0
    assert summary["freshness_skipped"] == 1
    assert not intent_log.exists()
    action_rows = _read_rows(action_log)
    assert action_rows[0]["event"] == "trade_record_projection_skipped"
    assert action_rows[0]["reason"] == "filled_record_event_time_too_old_for_live_projection"


def test_projector_skips_terminal_pending_rewrite(tmp_path: Path):
    source_root = tmp_path / "records"
    record_path = source_root / "XAUUSD" / "record.json"
    _write_record(record_path, "lim_cancelled")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["limit_intent"]["terminal_state"] = "cleared_without_fill"
    record["limit_intent"]["broker_fill_state"] = "not_filled"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    intent_log = tmp_path / "intents.jsonl"
    state = tmp_path / "state.json"
    action_log = tmp_path / "actions.jsonl"

    summary = project_once(
        source_root=source_root,
        intent_log=intent_log,
        state_path=state,
        action_log=action_log,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        recent_file_limit=10,
        replay_existing=True,
    )

    assert summary["projected"] == 0
    assert summary["skipped"] == 1
    assert not intent_log.exists()
    action_rows = _read_rows(action_log)
    assert action_rows[0]["event"] == "trade_record_projection_skipped"
    assert action_rows[0]["reason"] == "intent_builder_returned_none"
    assert action_rows[0]["projection_skip_reasons"] == [
        "no_filled_execution_or_open_pending_source"
    ]
