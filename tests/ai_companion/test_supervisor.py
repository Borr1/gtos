import json
from datetime import datetime, timezone

import src.components.ai_companion.supervisor as supervisor_module
from src.components.ai_companion.supervisor import AICompanionSupervisor, _read_jsonl_tail
from src.components.ai_companion.control_state import write_control_state_atomic
from src.components.ultimate_book.runtime_learning_packet import build_runtime_learning_packet


NOW = datetime(2026, 6, 19, 10, 10, tzinfo=timezone.utc)


def _append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _supervisor(tmp_path):
    return AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
        },
        repo_root=tmp_path,
    )


def test_supervisor_parses_false_string_for_targetless_pause_config(tmp_path):
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [],
            "targetless_time_stop_pause_new_entries_enabled": "false",
        },
        repo_root=tmp_path,
    )

    assert supervisor.targetless_time_stop_pause_new_entries_enabled is False


def test_supervisor_parses_false_string_for_enabled(tmp_path):
    supervisor = AICompanionSupervisor(
        {
            "enabled": "false",
            "authority_level": "protective",
            "namespaces": [],
        },
        repo_root=tmp_path,
    )

    assert supervisor.enabled is False


def test_supervisor_honors_digest_path_config_alias(tmp_path):
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [],
            "digest_path": "pipeline_state/custom/digest.json",
        },
        repo_root=tmp_path,
    )

    assert supervisor.digest_path == "pipeline_state/custom/digest.json"


def test_jsonl_tail_reader_bounds_rows_from_eof(tmp_path):
    path = tmp_path / "shadow_logs" / "large.jsonl"
    for idx in range(25):
        _append_jsonl(path, {"idx": idx})

    rows, errors = _read_jsonl_tail(path, max_rows=5)

    assert errors == []
    assert [row["idx"] for row in rows] == [20, 21, 22, 23, 24]


def test_jsonl_tail_reader_drops_byte_cap_head_fragment(tmp_path, monkeypatch):
    path = tmp_path / "shadow_logs" / "large_rows.jsonl"
    for idx in range(8):
        _append_jsonl(path, {"idx": idx, "payload": "x" * 180})
    monkeypatch.setattr(supervisor_module, "DEFAULT_JSONL_TAIL_MAX_BYTES", 700)

    rows, errors = _read_jsonl_tail(path, max_rows=20)

    assert errors == []
    assert [row["idx"] for row in rows] == [5, 6, 7]


def test_jsonl_tail_reader_ignores_only_unterminated_final_fragment(tmp_path):
    path = tmp_path / "shadow_logs" / "partial.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"idx": 1}\n{"idx":', encoding="utf-8")

    rows, errors = _read_jsonl_tail(path, max_rows=5)

    assert errors == []
    assert [row["idx"] for row in rows] == [1]


def test_jsonl_tail_reader_reports_newline_terminated_malformed_final_row(tmp_path):
    path = tmp_path / "shadow_logs" / "corrupt.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"idx": 1}\nnot-json\n', encoding="utf-8")

    rows, errors = _read_jsonl_tail(path, max_rows=5)

    assert [row["idx"] for row in rows] == [1]
    assert len(errors) == 1


def test_supervisor_writes_running_heartbeat_before_expensive_digest(tmp_path):
    supervisor = _supervisor(tmp_path)

    def fake_digest(ts):
        heartbeat = json.loads(
            (tmp_path / "pipeline_state" / "ai_companion" / "heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        assert heartbeat["cycle_status"] == "running"
        assert heartbeat["ok"] is None
        return {
            "schema": "gtos.ai_companion.cycle_digest.v1",
            "ts": ts.isoformat(),
            "ok": True,
            "issue_counts": {},
            "book_heartbeats": {},
            "book_link_issues": {},
        }

    supervisor.build_digest = fake_digest

    supervisor.run_once(NOW)

    heartbeat = json.loads(
        (tmp_path / "pipeline_state" / "ai_companion" / "heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert heartbeat["cycle_status"] == "completed"
    assert heartbeat["ok"] is True


def test_supervisor_surfaces_execution_manager_blocks_as_advisory(tmp_path):
    launcher = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    _append_jsonl(
        launcher,
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "redacted_account_live_bee34003",
            "action": "cycle",
            "skipped": [
                {
                    "symbol": "ETHUSD",
                    "sleeve": "orb_crypto_london",
                    "decision_bar_iso": "2026-06-19T09:45:00+00:00",
                    "reason": "pretrade_cost:total_cost_r_exceeds_limit:0.170712>0.150000;exec_mgr_v4:pretrade_cost_model_status_not_passed:REFUSED",
                }
            ],
        },
    )

    supervisor = _supervisor(tmp_path)
    digest = supervisor.build_digest(NOW)
    state, proposals = supervisor.build_controls(digest, NOW)

    events = digest["launcher"]["execution_manager_block_events"]
    assert events == [
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "redacted_account_live_bee34003",
            "symbol": "ETHUSD",
            "sleeve": "orb_crypto_london",
            "decision_bar_iso": "2026-06-19T09:45:00+00:00",
            "reason": "pretrade_cost:total_cost_r_exceeds_limit:0.170712>0.150000;exec_mgr_v4:pretrade_cost_model_status_not_passed:REFUSED",
        }
    ]
    assert digest["ok"] is True
    assert state["summary"]["active_control_count"] == 0
    assert {
        proposal["reason"]
        for proposal in proposals
        if proposal["proposal_type"] == "advisory"
    } == {"execution_manager_block_review_only_runtime_already_fail_closed"}


def test_supervisor_keeps_execution_manager_blocks_separate_from_cost_screens(tmp_path):
    launcher = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    _append_jsonl(
        launcher,
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "operator_profile",
            "action": "cycle",
            "skipped": [
                {
                    "symbol": "GBPUSD",
                    "sleeve": "asian_fade",
                    "decision_bar_iso": "2026-06-19T08:15:00+00:00",
                    "reason": "cost_screen_spread_r:0.105>0.100",
                },
                {
                    "symbol": "ETHUSD",
                    "sleeve": "orb_crypto_london",
                    "decision_bar_iso": "2026-06-19T09:45:00+00:00",
                    "reason": "pretrade_cost:total_cost_r_exceeds_limit:0.170712>0.150000;exec_mgr_v4:pretrade_cost_model_status_not_passed:REFUSED",
                },
            ],
        },
    )

    digest = _supervisor(tmp_path).build_digest(NOW)

    assert len(digest["launcher"]["cost_screen_events"]) == 1
    assert len(digest["launcher"]["execution_manager_block_events"]) == 1
    assert digest["launcher"]["cost_screen_events"][0]["symbol"] == "GBPUSD"
    assert digest["launcher"]["execution_manager_block_events"][0]["symbol"] == "ETHUSD"


def test_supervisor_flags_launcher_runtime_learning_write_errors_as_integrity_issue(tmp_path):
    launcher = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    _append_jsonl(
        launcher,
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "operator_profile",
            "action": "cycle",
            "runtime_learning": {
                "enabled": True,
                "log_enabled": True,
                "error": "ValueError('unit_placed_capture_contract_incomplete')",
                "packets": 0,
            },
            "placed": [
                {
                    "symbol": "AVAUSD",
                    "sleeve": "mx_avausd_d1_donchian_20_breakout",
                    "decision_bar_iso": "2026-06-18T23:00:00+00:00",
                    "candidate_id": (
                        "W7_BOOK::crypto_alt_or_major::AVAUSD::2026-06-19::SHORT::"
                        "mx_avausd_d1_donchian_20_breakout"
                    ),
                    "ticket_hash_sha256": "ticket-hash",
                    "placement_source_completeness_status": "missing_required_ticket_placement_context",
                    "placement_source_missing_fields": ["cluster"],
                }
            ],
        },
    )

    supervisor = _supervisor(tmp_path)
    digest = supervisor.build_digest(NOW)
    state, _ = supervisor.build_controls(digest, NOW)

    assert digest["ok"] is False
    assert digest["issue_counts"]["launcher_runtime_learning_write_errors"] == 1
    assert digest["launcher"]["runtime_learning_write_error_count"] == 1
    event = digest["launcher"]["runtime_learning_write_errors"][0]
    assert event["placed_examples"][0]["symbol"] == "AVAUSD"
    assert state["summary"]["active_control_count"] == 1
    assert state["controls"][0]["reason"] == "ai_companion_runtime_integrity_issue"


def test_supervisor_classifies_bare_pretrade_cost_separately_from_execution_manager(tmp_path):
    launcher = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    _append_jsonl(
        launcher,
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "operator_profile",
            "action": "cycle",
            "skipped": [
                {
                    "symbol": "GBPUSD",
                    "sleeve": "asian_fade",
                    "decision_bar_iso": "2026-06-19T08:15:00+00:00",
                    "reason": "pretrade_cost:total_cost_r_exceeds_limit:0.170712>0.150000",
                }
            ],
        },
    )

    supervisor = _supervisor(tmp_path)
    digest = supervisor.build_digest(NOW)
    _, proposals = supervisor.build_controls(digest, NOW)

    assert len(digest["launcher"]["pretrade_cost_block_events"]) == 1
    assert digest["launcher"]["execution_manager_block_events"] == []
    assert any(
        proposal["reason"] == "pretrade_cost_block_review_only_runtime_already_fail_closed"
        for proposal in proposals
    )


def test_supervisor_enriches_execution_manager_cost_refusals(tmp_path):
    execution_log = tmp_path / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
    _append_jsonl(
        execution_log,
        {
            "generated_at_utc": "2026-06-19T10:05:10+00:00",
            "action": "block",
            "should_block": True,
            "fatal_reasons": ["pretrade_cost_model_status_not_passed:REFUSED"],
            "identity": {
                "symbol": "ETHUSD",
                "broker_symbol": "ETHUSD",
                "candidate_id": "W7_BOOK::crypto::ETHUSD::2026-06-19::LONG::orb_crypto_london",
            },
            "cost_context": {
                "pretrade_cost_model_status": "REFUSED",
                "status": "cost_incomplete",
                "spread_r": 0.051,
                "max_spread_r": 0.1,
                "commission_model_status": "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK",
            },
            "broker_order_lifecycle_capture_v4": {
                "pretrade_cost_model": {
                    "refusal_reasons": ["total_cost_r_exceeds_limit:0.170712>0.150000"]
                }
            },
        },
    )

    supervisor = _supervisor(tmp_path)
    digest = supervisor.build_digest(NOW)
    _, proposals = supervisor.build_controls(digest, NOW)

    event = digest["execution_manager"]["blocked_events"][0]
    assert event["symbol"] == "ETHUSD"
    assert event["cost_status"] == "REFUSED"
    assert event["cost_refusal_reasons"] == ["total_cost_r_exceeds_limit:0.170712>0.150000"]
    assert digest["execution_manager"]["cost_refusal_reason_counts"] == {
        "total_cost_r_exceeds_limit:0.170712>0.150000": 1
    }
    detail = [
        proposal
        for proposal in proposals
        if proposal["reason"] == "execution_manager_block_detail_runtime_already_fail_closed"
    ]
    assert len(detail) == 1
    assert detail[0]["event"]["fatal_reasons"] == ["pretrade_cost_model_status_not_passed:REFUSED"]


def test_supervisor_keeps_distinct_execution_manager_detail_proposals(tmp_path):
    execution_log = tmp_path / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
    for suffix, refusal in (
        ("ETHUSD", "total_cost_r_exceeds_limit:0.170712>0.150000"),
        ("ETHUSD", "swap_cost_model_required"),
    ):
        _append_jsonl(
            execution_log,
            {
                "generated_at_utc": f"2026-06-19T10:05:{10 if 'total' in refusal else 20}+00:00",
                "action": "block",
                "should_block": True,
                "fatal_reasons": ["pretrade_cost_model_status_not_passed:REFUSED"],
                "identity": {
                    "symbol": suffix,
                    "broker_symbol": suffix,
                    "candidate_id": f"W7_BOOK::crypto::{suffix}::2026-06-19::LONG::orb_crypto_london::{refusal}",
                },
                "cost_context": {
                    "pretrade_cost_model_status": "REFUSED",
                    "status": "cost_incomplete",
                },
                "broker_order_lifecycle_capture_v4": {
                    "pretrade_cost_model": {"refusal_reasons": [refusal]}
                },
            },
        )

    supervisor = _supervisor(tmp_path)
    result = supervisor.run_once(NOW)
    rows = [
        json.loads(line)
        for line in (tmp_path / "pipeline_state" / "ai_companion" / "proposals.jsonl").read_text().splitlines()
    ]
    detail = [
        row
        for row in rows
        if row["reason"] == "execution_manager_block_detail_runtime_already_fail_closed"
    ]

    assert result["proposal_appended_count"] == 2
    assert len(detail) == 2
    assert {
        tuple(row["event"]["cost_refusal_reasons"])
        for row in detail
    } == {
        ("total_cost_r_exceeds_limit:0.170712>0.150000",),
        ("swap_cost_model_required",),
    }


def test_supervisor_orders_recent_rows_by_event_time_not_append_order(tmp_path):
    execution_log = tmp_path / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
    _append_jsonl(
        execution_log,
        {
            "generated_at_utc": "2026-06-19T10:08:00+00:00",
            "action": "block",
            "should_block": True,
            "fatal_reasons": ["late_newer"],
            "identity": {"symbol": "ETHUSD"},
        },
    )
    _append_jsonl(
        execution_log,
        {
            "generated_at_utc": "2026-06-19T10:02:00+00:00",
            "action": "block",
            "should_block": True,
            "fatal_reasons": ["late_older"],
            "identity": {"symbol": "BTCUSD"},
        },
    )

    digest = _supervisor(tmp_path).build_digest(NOW)

    assert [
        event["fatal_reasons"][0]
        for event in digest["execution_manager"]["blocked_events"]
    ] == ["late_older", "late_newer"]


def test_supervisor_flags_targetless_time_stop_policy_clock_anomaly(tmp_path):
    packets = tmp_path / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
    packet = build_runtime_learning_packet(
        namespace="redacted_account_live_bee34003",
        event_type="position_managed",
        ts="2026-06-19T10:05:00+00:00",
        outcome={
            "symbol": "ETHUSD",
            "sleeve": "ny_crypto_momentum",
            "candidate_id": "W7_BOOK::crypto::ETHUSD::2026-06-19::SHORT::ny_crypto_momentum",
            "ticket_hash_sha256": "ticket-hash",
            "management_action": "monitoring",
            "gtos_vnext_dynamic_policy_selected": "time_stop",
            "gtos_vnext_dynamic_no_broker_take_profit": True,
            "gtos_vnext_dynamic_broker_take_profit_mode": "none",
            "gtos_vnext_dynamic_time_stop_bars": 20,
            "policy_clock_status": "not_due",
            "policy_clock_checked_at_utc": "2026-06-19T10:05:00+00:00",
            "policy_clock_entry_time_utc": "2026-06-19T03:30:00+00:00",
            "policy_clock_source": "trading",
            "policy_clock_time_stop_bars": 20,
            "policy_clock_elapsed_m15_bars": 25,
            "policy_clock_bars_until_due": -5,
            "policy_clock_overdue_bars": 5,
        },
    )
    _append_jsonl(packets, packet)

    supervisor = _supervisor(tmp_path)
    digest = supervisor.build_digest(NOW)
    state, proposals = supervisor.build_controls(digest, NOW)

    assert digest["ok"] is False
    assert digest["issue_counts"]["targetless_time_stop_policy_clock_anomalies"] == 1
    anomaly = digest["runtime_packets"]["targetless_time_stop_policy_clock_anomalies"][0]
    assert anomaly["reason"] == "targetless_time_stop_overdue"
    assert anomaly["symbol"] == "ETHUSD"
    assert state["summary"]["active_control_count"] == 1
    control = state["controls"][0]
    assert control["type"] == "pause_new_entries"
    assert control["namespace"] == "redacted_account_live_bee34003"
    assert control["reason"] == "ai_companion_targetless_time_stop_policy_clock_issue"
    assert any(
        proposal.get("reason") == "targetless_time_stop_policy_clock_issue"
        for proposal in proposals
    )


def test_supervisor_carries_unexpired_controls_until_ttl(tmp_path):
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
            "clear_resolved_control_reasons": [],
        },
        repo_root=tmp_path,
    )
    bad_digest = {
        "ok": False,
        "issue_counts": {
            "launcher_parse_errors": 1,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 0,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {},
        "launcher": {},
        "execution_manager": {},
    }
    state, _ = supervisor.build_controls(bad_digest, NOW)
    assert state["summary"]["active_control_count"] == 1
    write_control_state_atomic(tmp_path, state, supervisor.control_state_path)

    clean_digest = {
        "ok": True,
        "issue_counts": {
            "launcher_parse_errors": 0,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 0,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {},
        "launcher": {},
        "execution_manager": {},
    }
    carried_state, proposals = supervisor.build_controls(clean_digest, NOW.replace(minute=11))

    assert carried_state["summary"]["active_control_count"] == 1
    control = carried_state["controls"][0]
    assert control["control_lifecycle_status"] == "carried_forward_until_expiry"
    assert control["latest_digest_condition_active"] is False
    assert any(p["status"] == "carried_forward_until_expiry" for p in proposals)


def test_supervisor_clears_resolved_runtime_integrity_pause_controls(tmp_path):
    supervisor = _supervisor(tmp_path)
    bad_digest = {
        "ok": False,
        "issue_counts": {
            "launcher_parse_errors": 0,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 5,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {},
        "launcher": {},
        "execution_manager": {},
    }
    state, _ = supervisor.build_controls(bad_digest, NOW)
    assert state["summary"]["active_control_count"] == 1
    assert state["controls"][0]["reason"] == "ai_companion_runtime_integrity_issue"
    write_control_state_atomic(tmp_path, state, supervisor.control_state_path)

    clean_digest = {
        "ok": True,
        "issue_counts": {
            "launcher_parse_errors": 0,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 0,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {},
        "launcher": {},
        "execution_manager": {},
    }
    cleared_state, proposals = supervisor.build_controls(clean_digest, NOW.replace(minute=11))

    assert cleared_state["summary"]["active_control_count"] == 0
    assert cleared_state["controls"] == []
    cleared = [p for p in proposals if p["status"] == "cleared_after_condition_resolved"]
    assert len(cleared) == 1
    assert cleared[0]["control"]["reason"] == "ai_companion_runtime_integrity_issue"
    assert cleared[0]["control"]["latest_digest_condition_active"] is False
    clear_evidence = cleared[0]["control"]["clear_evidence"][0]
    assert clear_evidence["digest_ok"] is True
    assert clear_evidence["clear_condition"] == "runtime_integrity_issue_counts_zero"
    assert clear_evidence["issue_counts"]["packet_validation_issues"] == 0


def test_supervisor_missing_book_heartbeat_creates_protective_pause(tmp_path):
    namespace = "operator_profile"
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [namespace],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
        },
        repo_root=tmp_path,
    )

    digest = supervisor.build_digest(NOW)
    state, _ = supervisor.build_controls(digest, NOW)

    assert digest["ok"] is False
    assert digest["issue_counts"]["missing_book_heartbeats"] == 1
    assert digest["issue_counts"]["link_unhealthy_namespaces"] == 1
    assert digest["book_link_issues"][namespace]["link_issue_reason"] == "missing_heartbeat"
    assert state["summary"]["active_control_count"] == 1
    assert state["controls"][0]["reason"] == "ai_companion_book_link_unhealthy"


def test_supervisor_stale_book_heartbeat_creates_protective_pause(tmp_path):
    namespace = "redacted_account_live_bee34003"
    heartbeat = tmp_path / "pipeline_state" / "ultimate_book" / namespace / "heartbeat.json"
    heartbeat.parent.mkdir(parents=True)
    heartbeat.write_text(
        json.dumps({
            "ts": "2026-06-19T10:00:00+00:00",
            "pid": 123,
            "namespace": namespace,
            "healthy": True,
        }),
        encoding="utf-8",
    )
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [namespace],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
            "book_heartbeat_stale_seconds": 180,
        },
        repo_root=tmp_path,
    )

    digest = supervisor.build_digest(NOW.replace(minute=5))
    state, _ = supervisor.build_controls(digest, NOW.replace(minute=5))

    assert digest["ok"] is False
    assert digest["issue_counts"]["stale_book_heartbeats"] == 1
    assert digest["issue_counts"]["link_unhealthy_namespaces"] == 1
    assert digest["book_link_issues"][namespace]["link_issue_reason"] == "stale_heartbeat"
    assert state["summary"]["active_control_count"] == 1
    assert state["controls"][0]["namespace"] == namespace


def test_supervisor_does_not_clear_book_link_pause_when_heartbeat_disappears(tmp_path):
    namespace = "operator_profile"
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [namespace],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
        },
        repo_root=tmp_path,
    )
    bad_digest = {
        "ok": False,
        "issue_counts": {"link_unhealthy_namespaces": 1},
        "runtime_packets": {},
        "book_heartbeats": {
            namespace: {
                "healthy": False,
                "path": "pipeline_state/ultimate_book/operator_profile/heartbeat.json",
            }
        },
        "launcher": {},
        "execution_manager": {},
    }
    state, _ = supervisor.build_controls(bad_digest, NOW)
    write_control_state_atomic(tmp_path, state, supervisor.control_state_path)

    missing_digest = supervisor.build_digest(NOW.replace(minute=11))
    next_state, proposals = supervisor.build_controls(missing_digest, NOW.replace(minute=11))

    assert missing_digest["book_link_issues"][namespace]["link_issue_reason"] == "missing_heartbeat"
    assert next_state["summary"]["active_control_count"] == 1
    assert next_state["controls"][0]["reason"] == "ai_companion_book_link_unhealthy"
    assert not [p for p in proposals if p["status"] == "cleared_after_condition_resolved"]


def test_supervisor_clears_resolved_book_link_pause_controls(tmp_path):
    supervisor = _supervisor(tmp_path)
    bad_digest = {
        "ok": False,
        "issue_counts": {
            "launcher_parse_errors": 0,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 0,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {
            "operator_profile": {
                "healthy": False,
                "path": "pipeline_state/ultimate_book/operator_profile/heartbeat.json",
            }
        },
        "launcher": {},
        "execution_manager": {},
    }
    state, _ = supervisor.build_controls(bad_digest, NOW)
    assert state["summary"]["active_control_count"] == 1
    assert state["controls"][0]["reason"] == "ai_companion_book_link_unhealthy"
    write_control_state_atomic(tmp_path, state, supervisor.control_state_path)

    clean_digest = {
        "ok": True,
        "issue_counts": {
            "launcher_parse_errors": 0,
            "launcher_error_rows": 0,
            "packet_parse_errors": 0,
            "packet_validation_issues": 0,
            "targetless_time_stop_policy_clock_anomalies": 0,
        },
        "runtime_packets": {},
        "book_heartbeats": {
            "operator_profile": {
                "healthy": True,
                "age_seconds": 0,
                "path": "pipeline_state/ultimate_book/operator_profile/heartbeat.json",
            }
        },
        "launcher": {},
        "execution_manager": {},
    }
    cleared_state, proposals = supervisor.build_controls(clean_digest, NOW.replace(minute=11))

    assert cleared_state["summary"]["active_control_count"] == 0
    assert cleared_state["controls"] == []
    cleared = [p for p in proposals if p["status"] == "cleared_after_condition_resolved"]
    assert len(cleared) == 1
    assert cleared[0]["control"]["control_lifecycle_status"] == "cleared_after_condition_resolved"
    assert cleared[0]["control"]["reason"] == "ai_companion_book_link_unhealthy"
    clear_evidence = cleared[0]["control"]["clear_evidence"][0]
    assert clear_evidence["digest_ok"] is True
    assert clear_evidence["clear_condition"] == "book_link_healthy_or_no_link_issue"
    assert clear_evidence["heartbeat"]["healthy"] is True


def test_supervisor_logs_new_book_link_incident_after_clear(tmp_path):
    namespace = "operator_profile"
    supervisor = AICompanionSupervisor(
        {
            "enabled": True,
            "authority_level": "protective",
            "namespaces": [namespace],
            "window_minutes": 20,
            "control_ttl_minutes": 30,
        },
        repo_root=tmp_path,
    )
    heartbeat = tmp_path / "pipeline_state" / "ultimate_book" / namespace / "heartbeat.json"

    def write_heartbeat(healthy: bool, ts: datetime) -> None:
        heartbeat.parent.mkdir(parents=True, exist_ok=True)
        heartbeat.write_text(
            json.dumps({"ts": ts.isoformat(), "pid": 123, "namespace": namespace, "healthy": healthy}),
            encoding="utf-8",
        )

    write_heartbeat(False, NOW)
    supervisor.run_once(NOW)
    write_heartbeat(True, NOW.replace(minute=11))
    supervisor.run_once(NOW.replace(minute=11))
    write_heartbeat(False, NOW.replace(minute=12))
    supervisor.run_once(NOW.replace(minute=12))

    proposal_rows = [
        json.loads(line)
        for line in (tmp_path / "pipeline_state" / "ai_companion" / "proposals.jsonl").read_text().splitlines()
    ]
    book_link_rows = [
        row
        for row in proposal_rows
        if row.get("control", {}).get("reason") == "ai_companion_book_link_unhealthy"
    ]

    assert [row["status"] for row in book_link_rows] == [
        "accepted",
        "cleared_after_condition_resolved",
        "accepted",
    ]


def test_supervisor_dedupes_repeated_proposal_log_rows(tmp_path):
    launcher = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    _append_jsonl(
        launcher,
        {
            "ts": "2026-06-19T10:05:00+00:00",
            "namespace": "redacted_account_live_bee34003",
            "action": "cycle",
            "skipped": [
                {
                    "symbol": "ETHUSD",
                    "sleeve": "orb_crypto_london",
                    "decision_bar_iso": "2026-06-19T09:45:00+00:00",
                    "reason": "pretrade_cost:total_cost_r_exceeds_limit:0.170712>0.150000;exec_mgr_v4:pretrade_cost_model_status_not_passed:REFUSED",
                }
            ],
        },
    )

    supervisor = _supervisor(tmp_path)
    first = supervisor.run_once(NOW)
    second = supervisor.run_once(NOW.replace(minute=11))
    rows = [
        json.loads(line)
        for line in (tmp_path / "pipeline_state" / "ai_companion" / "proposals.jsonl").read_text().splitlines()
    ]

    assert first["proposal_appended_count"] == 1
    assert second["proposal_suppressed_duplicate_count"] >= 1
    assert len(rows) == 1
