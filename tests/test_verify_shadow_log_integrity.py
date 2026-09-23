from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts import backfill_ai_narrowing_policy_shadow_evaluations as ai_narrowing_shadow
from scripts.verify_shadow_log_integrity import JSONL_SPECS, build_report, validate_schema_row
from src.research_infra.candidate_registry_audit import build_candidate_registry_audit_row
from src.research_infra.candidate_path_contract import build_candidate_path_contract_row
from src.research_infra.live_opportunity_dedupe import build_opportunity_index
from src.research_infra.opportunity_lifecycle_audit import build_opportunity_lifecycle_audit_rows
from src.research_infra.pending_limit_lifecycle_audit import build_pending_limit_lifecycle_audit_rows
from src.research_infra.trade_record_candidate_backfill import iter_trade_record_candidates
from src.research_infra.v2b_forward_pair_resolution_audit import build_v2b_forward_pair_audit_rows
from src.research_infra.prefill_delivery_path_audit import build_prefill_delivery_path_audit_rows
from src.research_infra.fvg_ob_confluence_audit import build_fvg_ob_confluence_audit_rows
from src.research_infra.context_control_audit import build_context_control_audit_rows
from src.research_infra.broker_actual_r_audit import build_broker_actual_r_audit_rows
from src.research_infra.j46_j49_exit_comparator_audit import build_candidate_context_row
from src.research_infra.account_pnl_truth_reconciler import build_account_pnl_truth_rows
from src.research_infra.trade_index_lifecycle_audit import (
    build_inventory_index,
    build_trade_index_lifecycle_rows,
)
from src.research_infra.session_volatility_sweep_status import (
    append_missing_no_event_rows,
    build_status_rows as build_session_vol_sweep_status_rows,
)
from src.research_infra.notification_queue_dead_zone_status import build_status_row as build_notification_queue_status_row
from src.research_infra.storage_retention_policy import build_status_row as build_storage_retention_status_row
from src.research_infra.v2_structural_selector_readiness import build_status_row as build_v2_selector_readiness_row
from src.research_infra.xauusd_same_market_extension import build_status_row as build_xauusd_same_market_status_row
from src.research_infra.es_mes_preregistration import (
    build_status_row as build_es_mes_prereg_status_row,
    default_registry_payload as default_es_mes_registry_payload,
)
from src.research_infra.shadow_observer_hardening import (
    build_status_row as build_shadow_observer_hardening_status_row,
)
from src.components.ai_decision_trace_logger import build_ai_decision_trace_row


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "market:",
                "  kill_zones:",
                "    london:",
                "      start_utc: '07:00'",
                "      end_utc: '12:00'",
                "    ny:",
                "      start_utc: '13:00'",
                "      end_utc: '17:00'",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _strategy_follow_evaluation_row(created_at: str) -> dict:
    return {
        "schema_version": "strategy_follow_evaluation_v1",
        "created_at_utc": created_at,
        "symbol": "EURUSD",
        "broker_symbol": "EURUSD",
        "candidate_id": "EURUSD_2026-05-04T12:00:00+00:00_pre_ai",
        "decision_time_utc": "2026-05-04T12:00:00+00:00",
        "evidence_class": "FORWARD_SHADOW",
        "no_leak_status": "NO_AI_OR_POST_OUTCOME_FIELDS_IN_ROW",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "evaluation_stage": "MSO_COMPUTED_PRE_AI",
        "ai_dependency": "NO_AI_REQUIRED_FOR_ROW",
        "ai_status": "NOT_CALLED_AT_ROW_TIME",
        "strategy_snapshots": [],
    }


def test_candidate_driven_source_log_does_not_warn_when_no_new_candidate(tmp_path):
    old_ts = "2026-05-04T10:30:00+00:00"
    now = datetime(2026, 5, 4, 12, 30, tzinfo=timezone.utc)
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [
            {
                "schema_version": "strategy_follow_candidate_v1",
                "created_at_utc": old_ts,
                "symbol": "XAGUSD",
                "broker_symbol": "XAGUSD",
                "candidate_id": "XAGUSD_2026-05-04T10:30:00+00:00",
                "decision_time_utc": old_ts,
                "side": "SHORT",
                "framework": "ob_retest",
                "analysis_decision": "CANDIDATE",
                "final_outcome_at_log": "REJECTED_L2",
                "trade_parameters": {"direction": "SHORT"},
                "external_confluence": {},
                "strategy_snapshots": [],
                "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )

    report = build_report(tmp_path, now)

    assert not [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("strategy_follow_candidates.jsonl")
    ]


def test_opportunity_cluster_asof_can_be_null_for_waiting_path_rows():
    spec = JSONL_SPECS["live_candidate_opportunity_clusters.jsonl"]

    assert "asof_latest_candle_utc" in spec.required_fields
    assert "asof_latest_candle_utc" in spec.nullable_required_fields


def test_source_driven_pending_limit_join_does_not_warn_when_no_new_lifecycle_event(tmp_path):
    old_ts = "2026-05-04T17:15:00+00:00"
    now = datetime(2026, 5, 4, 19, 0, tzinfo=timezone.utc)
    _write_jsonl(
        tmp_path / "shadow_logs" / "pending_limit_lifecycle_join_backfill.jsonl",
        [
            {
                "schema_version": "pending_limit_lifecycle_join_backfill_v1",
                "row_key": "GBPJPY:GBPJPY_2026-05-04T17:15:00+00:00:20260504T171500",
                "created_at_utc": old_ts,
                "backfilled_at_utc": old_ts,
                "symbol": "GBPJPY",
                "trade_id": "20260504T171500",
                "join_status": "JOINED_TO_PENDING_LIMIT_LIFECYCLE",
                "source_lifecycle_trade_id": "20260504T171500",
                "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS",
                "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "no_ai_calls": True,
                "no_canary_required": True,
                "no_execution": True,
                "ai_calls": 0,
                "canary_calls": 0,
                "order_calls": 0,
                "paid_data_calls": 0,
                "paid_fetch_attempted": False,
            }
        ],
    )

    report = build_report(tmp_path, now)

    assert not [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("pending_limit_lifecycle_join_backfill.jsonl")
    ]


def test_per_follow_path_log_still_warns_when_not_refreshed(tmp_path):
    old_ts = "2026-05-04T10:30:00+00:00"
    now = datetime(2026, 5, 4, 12, 30, tzinfo=timezone.utc)
    _write_jsonl(
        tmp_path / "shadow_logs" / "candidate_path_follow.jsonl",
        [
            {
                "schema_version": "candidate_path_follow_v1",
                "created_at_utc": old_ts,
                "symbol": "XAGUSD",
                "broker_symbol": "XAGUSD",
                "candidate_id": "XAGUSD_2026-05-04T10:30:00+00:00",
                "decision_time_utc": old_ts,
                "asof_latest_candle_utc": old_ts,
                "side": "SHORT",
                "trade_parameters": {"direction": "SHORT"},
                "path_label": "entry_touched_then_reached_tp1",
                "touched_entry": True,
                "hit_tp1": True,
                "hit_sl": False,
                "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )

    report = build_report(tmp_path, now)

    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("candidate_path_follow.jsonl")
    ]


def test_strategy_follow_evaluations_freshness_is_suppressed_outside_kill_zone(tmp_path):
    old_ts = "2026-05-04T12:00:00+00:00"
    now = datetime(2026, 5, 4, 12, 45, tzinfo=timezone.utc)
    _write_config(tmp_path / "config" / "agent_config.yaml")
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl",
        [_strategy_follow_evaluation_row(old_ts)],
    )

    report = build_report(tmp_path, now)

    assert not [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("strategy_follow_evaluations.jsonl")
    ]


def test_strategy_follow_evaluations_freshness_warns_inside_kill_zone(tmp_path):
    old_ts = "2026-05-04T12:00:00+00:00"
    now = datetime(2026, 5, 4, 13, 45, tzinfo=timezone.utc)
    _write_config(tmp_path / "config" / "agent_config.yaml")
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl",
        [_strategy_follow_evaluation_row(old_ts)],
    )

    report = build_report(tmp_path, now)

    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("strategy_follow_evaluations.jsonl")
    ]


def test_kill_zone_freshness_uses_launched_symbols_from_start_all(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent_config.yaml").write_text(
        "\n".join(
            [
                "instruments:",
                "  XAUUSD:",
                "    market:",
                "      kill_zones:",
                "        ny:",
                "          start_utc: '13:00'",
                "          end_utc: '17:00'",
                "  NZDUSD:",
                "    market:",
                "      kill_zones:",
                "        tokyo:",
                "          start_utc: '22:00'",
                "          end_utc: '02:00'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "start_all.bat").write_text(
        "python.exe run_agent.py --symbol XAUUSD --mode demo\n",
        encoding="utf-8",
    )
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl",
        [_strategy_follow_evaluation_row("2026-05-04T19:00:00+00:00")],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 22, 30, tzinfo=timezone.utc))

    assert not [
        issue
        for issue in report["issues"]
        if issue["code"] == "FRESHNESS_THRESHOLD_EXCEEDED"
        and issue["path"].endswith("strategy_follow_evaluations.jsonl")
    ]


def test_j46_candidate_context_rows_cannot_claim_actual_r(tmp_path):
    row = build_candidate_context_row(
        {
            "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
            "created_at_utc": "2026-05-04T17:00:24+00:00",
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "side": "LONG",
            "framework": "ob_retest",
            "decision_time_utc": "2026-05-04T17:00:00+00:00",
            "final_outcome_at_log": "REJECTED_GATE1_SAFETY",
        },
        path_row={
            "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
            "created_at_utc": "2026-05-05T02:44:30+00:00",
            "asof_latest_candle_utc": "2026-05-05T02:30:00+00:00",
            "path_label": "continued_without_entry_touch_to_tp_area",
            "touched_entry": False,
            "hit_tp1": True,
            "hit_sl": False,
        },
        generated_at_utc="2026-05-05T02:45:00+00:00",
    )
    row["actual_r_claim_allowed"] = True
    row["broker_actual_r"] = 1.0
    _write_jsonl(tmp_path / "shadow_logs" / "j46_j49_exit_comparator_audit.jsonl", [row])

    report = build_report(tmp_path, datetime(2026, 5, 5, 2, 50, tzinfo=timezone.utc))

    assert {
        "J46_COMPARATOR_CANDIDATE_CONTEXT_ACTUAL_R_FORBIDDEN",
        "J46_COMPARATOR_CANDIDATE_CONTEXT_BROKER_R_FORBIDDEN",
    }.issubset({issue["code"] for issue in report["issues"]})


def _gbpjpy_proxy_gap_row(**overrides) -> dict:
    row = {
        "schema_version": "gbpjpy_orderflow_proxy_gap_status_v1",
        "row_key": "gbpjpy-proxy-gap-row",
        "source_dependency_signature": "sig",
        "created_at_utc": "2026-05-04T14:00:00+00:00",
        "backfilled_at_utc": "2026-05-04T14:00:00+00:00",
        "lto_id": "LTO-014",
        "follow_id": "LIVE-FOLLOW-022",
        "status": "BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN",
        "symbol": "GBPJPY",
        "broker_symbol": "GBPJPY",
        "candidate_id": "GBPJPY_2026-05-04T03:00:00+00:00",
        "decision_time_utc": "2026-05-04T03:00:00+00:00",
        "registry_proxy_class": "NO_REGISTERED_PROXY",
        "registry_source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        "registry_parity_status": "SOURCE_BLOCKED",
        "current_proxy_status": "NO_REGISTERED_DIRECT_PROXY",
        "direct_proxy_registered": False,
        "direct_confluence_allowed": False,
        "existing_confluence_inferred": False,
        "blocker_policy": "KEEP_BLOCKER_ROWS_NO_BACKFILL_CONFLUENCE",
        "proxy_design_version": "gbpjpy_two_leg_proxy_design_v1",
        "proxy_design_status": "PRE_REGISTERED_NOT_ACTIVE",
        "registered_proxy_designs": ["NO_DIRECT_PROXY_CURRENT", "TWO_BOOK_SYNTHETIC_6B_6J"],
        "pre_registered_tests": ["GBPJPY-PROXY-T1-CORRELATION-STABILITY"],
        "validation_summary": {"no_outcomes_opened": True},
        "outcome_transfer_caveat_status": "NOT_OPENED_EXISTING_CANDIDATE_ROWS_REMAIN_BLOCKED",
        "no_leak_status": "PRE_REGISTERED_SOURCE_TESTS_ONLY_NO_OUTCOME_FIELDS",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_gbpjpy_proxy_gap_status_schema_and_safety_counters_are_checked(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "gbpjpy_proxy_gap_status.jsonl",
        [_gbpjpy_proxy_gap_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 14, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("gbpjpy_proxy_gap_status.jsonl")
        and issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
    ]


def _sierra_6b_si_policy_row(**overrides) -> dict:
    row = {
        "schema_version": "sierra_6b_si_depth_policy_status_v1",
        "row_key": "sierra-6b-si-policy-row",
        "source_dependency_signature": "sig",
        "created_at_utc": "2026-05-04T14:00:00+00:00",
        "backfilled_at_utc": "2026-05-04T14:00:00+00:00",
        "lto_id": "LTO-030",
        "follow_id": "LIVE-FOLLOW-028",
        "status": "COMMON_SECOND_ALIGNMENT_POLICY_REGISTERED",
        "symbol": "GBPUSD",
        "broker_symbol": "GBPUSD",
        "source_symbol": "6BM26-CME",
        "futures_symbol": "6B.v.0",
        "policy_type": "COMMON_SECOND_ALIGNMENT",
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "COMMON_SECOND_ALIGNMENT_REGISTERED_6B",
        "interpretation_status": "REQUIRES_COMMON_SECOND_ALIGNED_FEATURE_ROW_BEFORE_USE",
        "current_rows_policy": "KEEP_CURRENT_ROWS_BLOCKED_UNTIL_ALIGNED_FEATURE_ROW",
        "depth_interpretation_allowed_current": False,
        "depth_interpretation_allowed_after_policy": True,
        "sample_alignment_policy": {"policy_version": "6b_common_second_alignment_v1"},
        "validation_summary": {"event15": {"common_count": 632}},
        "requirements_before_interpretation": ["feature row must declare sample alignment policy"],
        "no_leak_status": "SOURCE_POLICY_FROM_PREDECLARED_SAMPLING_AUDITS_NO_OUTCOME_FIELDS",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_sierra_6b_si_depth_policy_status_schema_and_safety_counters_are_checked(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "sierra_6b_si_depth_policy_status.jsonl",
        [_sierra_6b_si_policy_row(order_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 14, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("sierra_6b_si_depth_policy_status.jsonl")
        and issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
    ]


def _orderflow_primitives_status_row(**overrides) -> dict:
    row = {
        "schema_version": "orderflow_primitives_status_v1",
        "row_key": "orderflow-primitives-row",
        "source_dependency_signature": "sig",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "lto_id": "LTO-033",
        "follow_id": "LIVE-FOLLOW-031",
        "status": "OK_PRIMITIVES_REGISTERED_WITH_SOURCE_BLOCKERS",
        "registry_version": "orderflow_primitive_registry_v1",
        "primitive_count": 6,
        "primitive_ids": ["X1_FOOTPRINT_DELTA_ABSORPTION_V1"],
        "feature_families": ["footprint_delta_absorption"],
        "roles_evaluated_separately": {"entry_timing": ["X1_FOOTPRINT_DELTA_ABSORPTION_V1"]},
        "candidate_trigger_policy": {"decision_cutoff": "decision_time_utc"},
        "cost_policy": {"this_audit_paid_data_calls": 0},
        "no_lookahead_check": {"status": "PASS"},
        "field_coverage": {},
        "cached_feature_stability": {"status": "DIAGNOSTIC_ONLY_LABEL_LIMITED"},
        "source_readiness": {"databento_live": {"license_blocker": True}},
        "blocker_codes": ["DATABENTO_LIVE_LICENSE_BLOCKED"],
        "claim_boundary": "registry only",
        "no_leak_status": "PRIMITIVE_REGISTRY_AND_CACHED_ASOF_FEATURES_ONLY",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_orderflow_primitives_status_schema_and_safety_counters_are_checked(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "orderflow_primitives_status.jsonl",
        [_orderflow_primitives_status_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("orderflow_primitives_status.jsonl")
        and issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
    ]


def _exit_management_status_row(**overrides) -> dict:
    row = {
        "schema_version": "exit_management_shadow_status_v1",
        "row_key": "exit-management-row",
        "source_dependency_signature": "sig",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "classifier_version": "exit_management_status_classifier_v3",
        "lto_id": "LTO-021",
        "follow_id": "LIVE-FOLLOW-018",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "trade_id": None,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "ob_retest",
        "session": "london",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "candidate_final_outcome_at_log": "LIMIT_PLACED",
        "exit_management_status": "EXIT_MANAGEMENT_NO_EVENT_DOCUMENTED",
        "fill_state": "NO_FILLED_TRADE",
        "pending_lifecycle_fill_status": "NO_PENDING_LIFECYCLE_JOIN_ROW",
        "account_truth_fill_status": "NO_ACCOUNT_TRUTH_ROW",
        "broker_actual_r_fill_status": "NO_BROKER_AUDIT_ROW",
        "be_shadow_status": "NO_FILLED_TRADE",
        "partial_close_shadow_status": "NO_FILLED_TRADE",
        "time_in_trade_shadow_status": "NO_FILLED_TRADE",
        "documented_no_event_codes": ["NO_FILLED_TRADE", "NO_BE_TRIGGER", "NO_PARTIAL_TRIGGER", "NO_CLOSE_EVENT"],
        "action_required_codes": [],
        "actual_event_row_counts": {"be_shadow_log": 0, "partial_close_shadow_log": 0, "time_in_trade": 0},
        "event_log_file_statuses": {
            "be": "EVENT_LOG_FILE_MISSING_NO_EVENT_STATUS_REQUIRED",
            "partial_close": "EVENT_LOG_FILE_MISSING_NO_EVENT_STATUS_REQUIRED",
            "time_in_trade": "EVENT_LOG_FILE_MISSING_NO_EVENT_STATUS_REQUIRED",
        },
        "event_rows_separate_from_status_rows": True,
        "claim_boundary": "status row only",
        "evidence_class": "EXIT_MANAGEMENT_NO_EVENT_STATUS",
        "no_leak_status": "POST_DECISION_STATUS_ROW_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }
    row.update(overrides)
    return row


def test_exit_management_status_schema_and_safety_counters_are_checked(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "exit_management_shadow_status.jsonl",
        [_exit_management_status_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("exit_management_shadow_status.jsonl")
        and issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
    ]


def test_exit_management_status_required_when_candidate_rows_exist(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [
            {
                "schema_version": "strategy_follow_candidate_v1",
                "created_at_utc": "2026-05-04T07:15:25+00:00",
                "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
                "symbol": "XAUUSD",
                "broker_symbol": "XAUUSD",
                "side": "SHORT",
                "framework": "ob_retest",
                "session": "london",
                "decision_time_utc": "2026-05-04T07:15:00+00:00",
                "final_outcome_at_log": "LIMIT_PLACED",
                "analysis_decision": "CANDIDATE",
                "trade_parameters": {"direction": "SHORT"},
                "external_confluence": {},
                "strategy_snapshots": [],
                "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert report["exit_management_status_health"]["status"] == "ACTION_REQUIRED"
    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "EXIT_MANAGEMENT_STATUS_MISSING"
    ]


def test_session_vol_sweep_status_schema_and_safety_counters_are_checked(tmp_path):
    target = datetime(2026, 5, 4, tzinfo=timezone.utc).date()
    append_missing_no_event_rows(tmp_path, target)
    rows = build_session_vol_sweep_status_rows(
        root=tmp_path,
        target_date=target,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    rows[0]["paid_data_calls"] = 1
    _write_jsonl(tmp_path / "shadow_logs" / "session_volatility_sweep_status.jsonl", rows)

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("session_volatility_sweep_status.jsonl")
        and issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
    ]


def test_session_vol_sweep_status_required_when_csv_rows_exist(tmp_path):
    append_missing_no_event_rows(tmp_path, datetime(2026, 5, 4, tzinfo=timezone.utc).date())

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert report["session_vol_sweep_status_health"]["status"] == "ACTION_REQUIRED"
    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("session_volatility_sweep_status.jsonl")
        and issue["code"] == "SESSION_VOL_SWEEP_STATUS_MISSING"
    ]


def test_session_vol_sweep_status_accepts_current_status_rows(tmp_path):
    target = datetime(2026, 5, 4, tzinfo=timezone.utc).date()
    append_missing_no_event_rows(tmp_path, target)
    rows = build_session_vol_sweep_status_rows(
        root=tmp_path,
        target_date=target,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "session_volatility_sweep_status.jsonl", rows)

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert report["session_vol_sweep_status_health"]["status"] == "OK_WITH_DOCUMENTED_SESSION_VOL_SWEEP_STATUS"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("session_volatility_sweep_status.jsonl")
    ]


def test_notification_queue_dead_zone_required_when_queue_source_exists(tmp_path):
    queue_path = tmp_path / "pipeline_state" / "notification_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text("", encoding="utf-8")

    report = build_report(tmp_path, datetime(2026, 5, 5, 2, 30, tzinfo=timezone.utc))

    assert report["notification_queue_dead_zone_health"]["status"] == "ACTION_REQUIRED"
    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_MISSING"
    ]


def test_notification_queue_dead_zone_accepts_current_status_row(tmp_path):
    queue_path = tmp_path / "pipeline_state" / "notification_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text("", encoding="utf-8")
    lock_path = tmp_path / "knowledge_base" / "meta" / ".notification_queue_worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    now = datetime(2026, 5, 5, 2, 30, tzinfo=timezone.utc)
    row = build_notification_queue_status_row(
        root=tmp_path,
        now_utc=now,
        target_date=now.date(),
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "notification_queue_dead_zone_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["notification_queue_dead_zone_health"]["status"] == "OK_WITH_DOCUMENTED_NOTIFICATION_QUEUE_DEAD_ZONE"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("notification_queue_dead_zone_status.jsonl")
    ]


def test_storage_retention_status_rejects_non_dry_run_deletion(tmp_path):
    now = datetime(2026, 5, 5, 3, 0, tzinfo=timezone.utc)
    row = build_storage_retention_status_row(
        root=tmp_path,
        now_utc=now,
        max_files=1000,
        top_n=5,
        generated_at_utc=now.isoformat(),
    )
    row["deletion_performed"] = True
    _write_jsonl(tmp_path / "shadow_logs" / "storage_retention_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("storage_retention_status.jsonl")
        and issue["code"] == "STORAGE_RETENTION_NOT_DRY_RUN"
    ]


def _mechanical_row(**overrides) -> dict:
    row = {
        "schema_version": "live_mechanical_strategy_shadow_outcome_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T07:45:00+00:00",
        "strategy_id": "PENDING_LIMIT_LIFECYCLE",
        "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
        "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
        "outcome_status": "ENTRY_TOUCHED_THEN_SL",
        "path_label": "went_through_entry_and_continued_to_sl",
        "path_metrics": {},
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS",
        "no_ai_calls": True,
        "no_canary_required": True,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_mechanical_correction_duplicate_key_is_allowed(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "live_mechanical_strategy_shadow_outcomes.jsonl",
        [
            _mechanical_row(),
            _mechanical_row(
                created_at_utc="2026-05-04T08:01:00+00:00",
                strategy_status="SCORED_PENDING_LIFECYCLE_INTERNAL_TRUTH",
                score_status="COMPUTED_FROM_PENDING_LIFECYCLE",
                outcome_status="NO_FILL_CANCELLED_WRONG_SIDE",
                correction_of_created_at_utc="2026-05-04T08:00:00+00:00",
                correction_reason="latest_computed_shadow_outcome_changed_after_source_reconciliation",
                manual_backfill_status="CORRECTED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS",
            ),
        ],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 2, tzinfo=timezone.utc))

    assert not [issue for issue in report["issues"] if issue["code"] == "DUPLICATE_UNIQUE_KEY"]


def test_unmarked_mechanical_duplicate_key_is_rejected(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "live_mechanical_strategy_shadow_outcomes.jsonl",
        [
            _mechanical_row(),
            _mechanical_row(created_at_utc="2026-05-04T08:01:00+00:00"),
        ],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 2, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "DUPLICATE_UNIQUE_KEY"]


def _candidate_mso_row(**overrides) -> dict:
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-04T07:15:15+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "framework": "ob_retest",
        "analysis_decision": "CANDIDATE",
        "final_outcome_at_log": "REJECTED_L2",
        "trade_parameters": {
            "entry_price": 2300.0,
            "stop_loss": 2290.0,
            "take_profit_1": 2315.0,
        },
        "external_confluence": {"sierra": {"status": "SOURCE_BLOCKED"}, "databento": {"status": "SOURCE_BLOCKED"}},
        "strategy_snapshots": [{"strategy_id": "V2_STRUCT_OB_BOUNDARY"}],
        "mso_summary": {
            "timeframes": {
                "D1": {"structure_direction": "bullish", "order_block_count": 1},
                "H4": {"structure_direction": "bullish", "order_block_count": 2},
                "H1": {"structure_direction": "bullish", "order_block_count": 3},
                "M15": {"structure_direction": "bullish", "order_block_count": 4},
            }
        },
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _mso_eval_row(**overrides) -> dict:
    row = {
        "schema_version": "strategy_follow_evaluation_v1",
        "created_at_utc": "2026-05-04T07:15:05+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00_pre_ai",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "evidence_class": "FORWARD_SHADOW",
        "no_leak_status": "NO_AI_OR_POST_OUTCOME_FIELDS_IN_ROW",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "evaluation_stage": "MSO_COMPUTED_PRE_AI",
        "ai_dependency": "NO_AI_REQUIRED_FOR_ROW",
        "ai_status": "NOT_CALLED_AT_ROW_TIME",
        "source_file": "live_orchestrator_mso_pre_ai",
        "strategy_snapshots": [{"strategy_id": "V2_STRUCT_OB_BOUNDARY"}],
        "mso_summary": {
            "timeframes": {
                "D1": {"structure_direction": "bullish", "order_block_count": 1},
                "H4": {"structure_direction": "bullish", "order_block_count": 2},
                "H1": {"structure_direction": "bullish", "order_block_count": 3},
                "M15": {"structure_direction": "bullish", "order_block_count": 4},
            }
        },
    }
    row.update(overrides)
    return row


def _mso_join_row(**overrides) -> dict:
    row = {
        "schema_version": "candidate_mso_snapshot_join_v1",
        "row_key": "XAUUSD_2026-05-04T07:15:00+00:00|2026-05-04T07:15:00+00:00|mso_decision_snapshot_v1",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "join_status": "MSO_JOIN_MISSING",
        "join_method": "none_exact_symbol_decision_time",
        "context_comparison_status": "MSO_JOIN_MISSING",
        "manual_backfill_status": "DOCUMENTED_SOURCE_NOT_CAPTURED_MSO_JOIN_MISSING",
        "no_leak_status": "DECISION_TIME_MSO_CONTEXT_ONLY_NO_POST_OUTCOME_FIELDS",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }
    row.update(overrides)
    return row


def test_candidate_mso_coverage_reports_exact_join_cleanly(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [_candidate_mso_row()])
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl", [_mso_eval_row()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert report["mso_candidate_join_health"]["status"] == "OK"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("MSO_")]


def test_candidate_mso_coverage_flags_undocumented_missing_join(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [_candidate_mso_row(decision_time_utc="2026-05-04T07:30:00+00:00")],
    )
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl", [_mso_eval_row()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 35, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "MSO_JOIN_MISSING"]


def test_candidate_mso_coverage_accepts_documented_missing_join(tmp_path):
    candidate = _candidate_mso_row(decision_time_utc="2026-05-04T07:30:00+00:00")
    row_key = f"{candidate['candidate_id']}|{candidate['decision_time_utc']}|mso_decision_snapshot_v1"
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl", [_mso_eval_row()])
    _write_jsonl(
        tmp_path / "shadow_logs" / "candidate_mso_snapshot_joins.jsonl",
        [_mso_join_row(row_key=row_key, decision_time_utc=candidate["decision_time_utc"])],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 35, tzinfo=timezone.utc))

    assert report["mso_candidate_join_health"]["status"] == "OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"] == "MSO_JOIN_MISSING"]


def test_candidate_mso_coverage_flags_context_mismatch(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [_candidate_mso_row(mso_summary={"timeframes": {"D1": {"structure_direction": "bearish"}}})],
    )
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl", [_mso_eval_row()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "MSO_CONTEXT_MISMATCH"]


def _ai_narrowing_candidate(**overrides) -> dict:
    row = _candidate_mso_row(
        source_symbol="XAUUSD",
        market_timeframe="M15",
        route_session="ny",
        horizon_id="live_candidate_decision",
        source_component="primary_analyzer_live_candidate",
        selected_side="LONG",
    )
    row.update(overrides)
    return row


def _ai_narrowing_policy(**overrides) -> dict:
    row = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": "LONG",
        "ai_narrowing_policy_row_id": "POLICY-1",
        "ai_narrowing_policy_status": "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY",
        "ai_role_after_owner_approval": "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW",
    }
    row.update(overrides)
    return row


def _ai_narrowing_eval_row(candidate_path: Path, candidate: dict, *, forbidden_flag: bool = False) -> dict:
    candidate_sha = ai_narrowing_shadow.sha256_path(candidate_path)
    row = ai_narrowing_shadow.build_shadow_evaluations(
        candidate_rows=[(1, candidate)],
        policy_rows=[_ai_narrowing_policy()],
        candidate_source_path=candidate_path,
        candidate_source_sha256=candidate_sha,
        policy_ledger_path=Path("policy.jsonl"),
        policy_ledger_sha256="policy-sha",
        generated_at_utc="2026-05-04T07:16:00+00:00",
    )[0]
    if forbidden_flag:
        row["ai_call_skip_allowed_now"] = True
    return row


def test_ai_narrowing_shadow_eval_schema_registered():
    spec = JSONL_SPECS["ai_narrowing_policy_shadow_evaluations.jsonl"]

    assert spec.expected_schema == "ai_narrowing_policy_shadow_evaluation_v1"
    assert "ai_call_skip_allowed_now" in spec.required_fields
    assert "runtime_candidate_use_permitted" in spec.required_fields
    assert spec.unique_key == ("row_key",)


def test_ai_narrowing_shadow_eval_health_accepts_current_source_rows(tmp_path):
    candidate = _ai_narrowing_candidate()
    candidate_path = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    _write_jsonl(candidate_path, [candidate])
    _write_jsonl(
        tmp_path / "shadow_logs" / "ai_narrowing_policy_shadow_evaluations.jsonl",
        [_ai_narrowing_eval_row(candidate_path, candidate)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))
    health = report["ai_narrowing_policy_shadow_evaluations_health"]

    assert health["status"] == "OK_WITH_DEFAULT_OFF_AI_NARROWING_SHADOW_EVALUATIONS"
    assert health["candidate_ids"] == 1
    assert health["covered_current_candidate_ids"] == 1
    assert health["forbidden_flag_rows"] == 0
    assert not [issue for issue in report["issues"] if issue["code"].startswith("AI_NARROWING")]


def test_ai_narrowing_shadow_eval_health_flags_missing_current_candidate(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [_ai_narrowing_candidate()],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert report["ai_narrowing_policy_shadow_evaluations_health"]["status"] == "ACTION_REQUIRED"
    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "AI_NARROWING_SHADOW_EVAL_MISSING_CURRENT_CANDIDATES"
    ]


def test_ai_narrowing_shadow_eval_health_flags_forbidden_runtime_flag(tmp_path):
    candidate = _ai_narrowing_candidate()
    candidate_path = tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl"
    _write_jsonl(candidate_path, [candidate])
    _write_jsonl(
        tmp_path / "shadow_logs" / "ai_narrowing_policy_shadow_evaluations.jsonl",
        [_ai_narrowing_eval_row(candidate_path, candidate, forbidden_flag=True)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert report["ai_narrowing_policy_shadow_evaluations_health"]["status"] == "ACTION_REQUIRED"
    assert [issue for issue in report["issues"] if issue["code"] == "AI_NARROWING_FORBIDDEN_RUNTIME_FLAG"]
    assert [issue for issue in report["issues"] if issue["code"] == "AI_NARROWING_SHADOW_EVAL_FORBIDDEN_FLAGS"]


def _ai_decision_trace_row(**overrides) -> dict:
    row = build_ai_decision_trace_row(
        system_prompt=[{"type": "text", "text": "system prompt text"}],
        user_message="user message text",
        raw_response='{"decision":"NO_TRADE"}',
        result=None,
        usage={"input_tokens": 1, "output_tokens": 2, "cache_read_tokens": 3, "cache_create_tokens": 4},
        symbol="XAUUSD",
        candle_time="2026-05-18T00:00:00+00:00",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="parsed_first_attempt",
        parse_attempts=1,
    )
    row.update(overrides)
    return row


def test_ai_decision_trace_schema_registered():
    spec = JSONL_SPECS["ai_decision_trace.jsonl"]

    assert spec.expected_schema == "ai_decision_trace_v1"
    assert "prompt_fingerprint" in spec.required_fields
    assert "research_boundary" in spec.required_fields
    assert spec.unique_key == ("row_key",)


def test_ai_decision_trace_integrity_accepts_hash_only_rows(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "ai_decision_trace.jsonl",
        [_ai_decision_trace_row()],
    )

    report = build_report(tmp_path, datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc))

    assert not [issue for issue in report["issues"] if issue["code"].startswith("AI_DECISION_TRACE")]
    assert "ai_decision_trace.jsonl" not in report["waiting_files"]
    trace_file = [
        item for item in report["jsonl_files"] if item["path"].endswith("ai_decision_trace.jsonl")
    ][0]
    assert trace_file["known_spec"] is True
    assert trace_file["rows"] == 1


def test_ai_decision_trace_integrity_flags_full_text_or_runtime_flags(tmp_path):
    row = _ai_decision_trace_row(raw_response="full text should not be here")
    row["research_boundary"]["stores_full_prompt_or_response_text"] = True
    _write_jsonl(tmp_path / "shadow_logs" / "ai_decision_trace.jsonl", [row])

    report = build_report(tmp_path, datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "AI_DECISION_TRACE_FULL_TEXT_FIELD_PRESENT"]
    assert [issue for issue in report["issues"] if issue["code"] == "AI_DECISION_TRACE_FORBIDDEN_BOUNDARY_FLAG"]


def test_ai_decision_trace_missing_file_is_documented_waiting_lane(tmp_path):
    report = build_report(tmp_path, datetime(2026, 5, 18, 0, 5, tzinfo=timezone.utc))

    assert "ai_decision_trace.jsonl" in report["waiting_files"]


def test_candidate_registry_contract_accepts_audit_row(tmp_path):
    candidate = {
        **_candidate_mso_row(source_file="live_orchestrator_candidate_path", source_hash=None),
        "verification": {"passed": False, "blocked_by": "m15_choch_exists"},
        "structural_selector_metadata": {
            "capture_status": "DECISION_TIME_AVAILABLE_FIELDS_PRESERVED",
            "h1_setup_present": True,
            "m15_confirmation_present": True,
            "frameworks_evaluated_present": True,
            "mso_summary_present": True,
            "standalone_fvg_geometry_present": False,
            "structural_lock_event_present": False,
            "reentry_state_present": False,
            "cost_aware_min_r_present": False,
        },
    }
    audit = build_candidate_registry_audit_row(
        1,
        candidate,
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_registry_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert report["candidate_registry_audit_health"]["status"] == "OK_WITH_DOCUMENTED_REGISTRY_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("CANDIDATE_REGISTRY")]


def test_candidate_registry_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl",
        [_candidate_mso_row(source_file="live_orchestrator_candidate_path")],
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "CANDIDATE_REGISTRY_AUDIT_MISSING"]


def test_candidate_registry_contract_flags_action_required_audit_row(tmp_path):
    candidate = _candidate_mso_row(source_file="live_orchestrator_candidate_path", external_confluence={})
    audit = build_candidate_registry_audit_row(
        1,
        {**candidate, "verification": {"passed": False}},
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_registry_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 7, 20, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "CANDIDATE_REGISTRY_AUDIT_ACTION_REQUIRED"]


def _path_contract_source(**overrides) -> dict:
    row = {
        "schema_version": "candidate_path_follow_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "trade_parameters": {"direction": "LONG", "entry_price": 100, "stop_loss": 98, "take_profit_1": 103},
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_candidate_path_contract_accepts_audit_row(tmp_path):
    path_row = _path_contract_source()
    audit = build_candidate_path_contract_row(
        1,
        path_row,
        generated_at_utc="2026-05-05T00:00:00+00:00",
        ltf_row={"candidate_id": path_row["candidate_id"], "tp1_first_touch_utc": "2026-05-04T07:30:00+00:00"},
    )
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [path_row])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_contract_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["candidate_path_contract_health"]["status"] == "OK_WITH_DOCUMENTED_PATH_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("CANDIDATE_PATH_CONTRACT")]


def test_candidate_path_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [_path_contract_source()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "CANDIDATE_PATH_CONTRACT_AUDIT_MISSING"]


def _opportunity_cluster_source(candidate: dict, path_row: dict, computed: dict) -> dict:
    return {
        "schema_version": "live_candidate_opportunity_cluster_v1",
        "row_key": "cluster_fixture",
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T08:01:00+00:00",
        "backfilled_at_utc": "2026-05-04T08:01:00+00:00",
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "decision_time_utc": candidate["decision_time_utc"],
        "asof_latest_candle_utc": path_row["asof_latest_candle_utc"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "opportunity_id": computed["opportunity_id"],
        "opportunity_setup_signature": computed["opportunity_setup_signature"],
        "candidate_level_key": computed["candidate_level_key"],
        "opportunity_first_candidate_id": computed["opportunity_first_candidate_id"],
        "opportunity_sequence_index": computed["opportunity_sequence_index"],
        "opportunity_candidate_count": computed["opportunity_candidate_count"],
        "opportunity_duplicate_status": computed["opportunity_duplicate_status"],
        "opportunity_reset_reason": computed["opportunity_reset_reason"],
        "opportunity_counting_status": computed["opportunity_counting_status"],
        "same_symbol_overlap_status": computed["same_symbol_overlap_status"],
        "overlapping_active_symbol_opportunity_ids": computed["overlapping_active_symbol_opportunity_ids"],
        "opportunity_similarity": computed["opportunity_similarity"],
        "instrument_concurrency_guidance": computed["instrument_concurrency_guidance"],
        "opportunity_counting_guidance": "count only primary rows",
        "candidate_terminal_event": {},
        "same_setup_duplicate_rule": "fixture",
        "manual_backfill_status": "RECOVERED_DERIVED",
        "no_leak_status": "POST_DECISION_RECOVERY_ROW_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def test_opportunity_lifecycle_contract_accepts_audit_row(tmp_path):
    candidate = {
        **_candidate_mso_row(source_file="live_orchestrator_candidate_path"),
        "session": "london",
        "kill_zone": "london",
        "h1_setup": {"poi_type": "OB"},
    }
    path_row = _path_contract_source(candidate_id=candidate["candidate_id"], symbol="XAUUSD", broker_symbol="XAUUSD")
    computed = build_opportunity_index([candidate], latest_paths={candidate["candidate_id"]: path_row})[
        candidate["candidate_id"]
    ]
    cluster = _opportunity_cluster_source(candidate, path_row, computed)
    audit = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path_row)],
        cluster_rows=[(1, cluster)],
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [path_row])
    _write_jsonl(tmp_path / "shadow_logs" / "live_candidate_opportunity_clusters.jsonl", [cluster])
    _write_jsonl(tmp_path / "shadow_logs" / "opportunity_lifecycle_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["opportunity_lifecycle_audit_health"]["status"] == "OK_WITH_DOCUMENTED_LIFECYCLE_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("OPPORTUNITY_LIFECYCLE")]


def test_opportunity_lifecycle_contract_flags_missing_audit_row(tmp_path):
    candidate = {
        **_candidate_mso_row(source_file="live_orchestrator_candidate_path"),
        "session": "london",
        "kill_zone": "london",
        "h1_setup": {"poi_type": "OB"},
    }
    path_row = _path_contract_source(candidate_id=candidate["candidate_id"], symbol="XAUUSD", broker_symbol="XAUUSD")
    computed = build_opportunity_index([candidate], latest_paths={candidate["candidate_id"]: path_row})[
        candidate["candidate_id"]
    ]
    cluster = _opportunity_cluster_source(candidate, path_row, computed)
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [path_row])
    _write_jsonl(tmp_path / "shadow_logs" / "live_candidate_opportunity_clusters.jsonl", [cluster])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "OPPORTUNITY_LIFECYCLE_AUDIT_MISSING"]


def _pending_lifecycle_source(**overrides) -> dict:
    row = {
        "schema_version": "pending_limit_lifecycle_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "timestamp_utc": "2026-05-04T08:00:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "trade_id": "lim_2026-05-04_0715",
        "side": "SHORT",
        "entry_price": 100.0,
        "stop_loss": 110.0,
        "take_profit_1": 85.0,
        "pending_created_time_utc": "2026-05-04T07:15:00+00:00",
        "checked_candle_time_utc": "2026-05-04T08:00:00+00:00",
        "intent_after_check": "manual_or_system_cancelled",
        "fill_no_fill_label": "no_fill_cancelled",
        "broker_fill_state": "not_filled",
        "order_send_attempted": False,
        "order_send_success": False,
        "check_context": "cancel",
        "reason": "new_day",
    }
    row.update(overrides)
    return row


def _write_limit_trade_record(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "symbol": "XAUUSD",
                    "kill_zone": "london",
                    "candle_close_utc": "2026-05-04T07:15:00+00:00",
                },
                "decision_pipeline": {
                    "ai_decision": "CANDIDATE",
                    "ai_direction": "SHORT",
                    "ai_framework": "ob_retest",
                    "final_outcome": "LIMIT_PLACED",
                },
                "ai_response": {
                    "decision": "CANDIDATE",
                    "framework": "ob_retest",
                    "trade_parameters": {
                        "direction": "SHORT",
                        "entry_price": 100.0,
                        "stop_loss": 110.0,
                        "take_profit_1": 85.0,
                    },
                },
                "limit_intent": {
                    "trade_id": "lim_2026-05-04_0715",
                    "limit_price": 100.0,
                    "stop_loss": 110.0,
                    "take_profit_1": 85.0,
                },
                "execution": None,
                "pending_lifecycle": None,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_pending_limit_lifecycle_contract_accepts_audit_row(tmp_path):
    lifecycle = _pending_lifecycle_source()
    trade_record = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "2026-05-04_london_0715.json"
    _write_limit_trade_record(trade_record)
    trade_records, _skipped = iter_trade_record_candidates(tmp_path / "knowledge_base" / "trade_records")
    audit = build_pending_limit_lifecycle_audit_rows(
        [],
        [(1, lifecycle)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        trade_record_candidates=trade_records,
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "pending_limit_lifecycle.jsonl", [lifecycle])
    _write_jsonl(tmp_path / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["pending_limit_lifecycle_audit_health"]["status"] == "OK_WITH_DOCUMENTED_PENDING_LIFECYCLE_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("PENDING_LIMIT_LIFECYCLE")]


def test_pending_limit_lifecycle_contract_flags_missing_audit_row(tmp_path):
    lifecycle = _pending_lifecycle_source()
    trade_record = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "2026-05-04_london_0715.json"
    _write_limit_trade_record(trade_record)
    _write_jsonl(tmp_path / "shadow_logs" / "pending_limit_lifecycle.jsonl", [lifecycle])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "PENDING_LIMIT_LIFECYCLE_AUDIT_MISSING"]


def _v2b_pair(**overrides) -> dict:
    row = {
        "schema_version": "v2b_forward_pair_v1",
        "created_at_utc": "2026-05-04T07:15:05+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "ob_boundary_outcome": {"label_status": "unresolved_live_forward"},
        "j46_baseline_outcome": {"label_status": "unresolved_live_forward"},
        "fixed_r_comparator": {"label_status": "unresolved_live_forward"},
        "fvg_comparator": {"label_status": "unresolved_live_forward"},
        "path_label_status": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
        "actual_synthetic_label_lane": "no_outcome_at_decision_time",
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _v2b_resolution(**overrides) -> dict:
    row = {
        "schema_version": "v2b_forward_pair_resolution_v1",
        "row_key": "resolution_fixture",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "framework": "ob_retest",
        "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW",
        "path_metrics": {"base_r_price": 2.0},
        "path_label": "entry_touched_then_reached_tp1",
        "path_outcome_status": "ENTRY_TOUCHED_THEN_TP1",
        "strategy_outcomes": {
            "V2B_OB_BOUNDARY_PROSPECTIVE": {
                "strategy_status": "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
            "LIVE_AI_J46_J49_BASELINE_COMPARATOR": {
                "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_v2b_forward_pair_resolution_contract_accepts_audit_row(tmp_path):
    pair = _v2b_pair()
    resolution = _v2b_resolution()
    audit = build_v2b_forward_pair_audit_rows(
        [(1, pair)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pairs.jsonl", [pair])
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pair_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pair_resolution_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["v2b_forward_pair_resolution_audit_health"]["status"] == "OK_WITH_DOCUMENTED_V2B_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("V2B_FORWARD_PAIR_RESOLUTION")]


def test_v2b_forward_pair_resolution_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pairs.jsonl", [_v2b_pair()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "V2B_FORWARD_PAIR_RESOLUTION_AUDIT_MISSING"]


def test_v2b_forward_pair_resolution_contract_flags_action_required_audit_row(tmp_path):
    pair = _v2b_pair(
        actual_synthetic_label_lane="synthetic_path_r",
        ob_boundary_outcome={"label_status": "ENTRY_TOUCHED_THEN_TP1"},
    )
    resolution = _v2b_resolution()
    audit = build_v2b_forward_pair_audit_rows(
        [(1, pair)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pairs.jsonl", [pair])
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pair_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pair_resolution_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "V2B_FORWARD_PAIR_RESOLUTION_AUDIT_ACTION_REQUIRED"]


def _prefill_source(**overrides) -> dict:
    row = {
        "schema_version": "prefill_delivery_path_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "structural_setup_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "entry_arming_time_utc": "2026-05-04T07:15:00+00:00",
        "original_poi_bounds": {"poi_type": "OB", "poi_price_level": 100.0, "zone": "discount"},
        "pre_fill_candles": [],
        "pre_fill_ticks_summary": None,
        "delivery_leg_direction": "unresolved_live_forward",
        "reversal_leg_timing": None,
        "fill_happened": None,
        "fill_delay_seconds": None,
        "cancel_expiry_abort_reason": "REJECTED_L2",
        "lower_timeframe_path_ordering": "unresolved",
        "fvg_ob_swing_state_at_arm": {"framework": "ob_retest", "h1_poi_type": "OB"},
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _prefill_resolution(**overrides) -> dict:
    row = {
        "schema_version": "prefill_delivery_path_resolution_v1",
        "row_key": "prefill_resolution_fixture",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "framework": "ob_retest",
        "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW",
        "path_metrics": {"base_r_price": 2.0},
        "path_label": "continued_without_entry_touch_to_tp_area",
        "path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "strategy_outcomes": {
            "PREFILL_DELIVERY_REVERSAL_PATH": {
                "strategy_status": "REGISTERED_NO_SCORER_IMPLEMENTED",
                "score_status": "NOT_COMPUTABLE",
                "outcome_status": "NOT_SCORED",
            },
            "PENDING_LIMIT_LIFECYCLE": {
                "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_prefill_delivery_path_contract_accepts_audit_row(tmp_path):
    prefill = _prefill_source()
    resolution = _prefill_resolution()
    audit = build_prefill_delivery_path_audit_rows(
        [(1, prefill)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path.jsonl", [prefill])
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["prefill_delivery_path_audit_health"]["status"] == "OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("PREFILL_DELIVERY_PATH")]


def test_prefill_delivery_path_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path.jsonl", [_prefill_source()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "PREFILL_DELIVERY_PATH_AUDIT_MISSING"]


def test_prefill_delivery_path_contract_flags_action_required_audit_row(tmp_path):
    prefill = _prefill_source(fill_happened=False)
    resolution = _prefill_resolution()
    audit = build_prefill_delivery_path_audit_rows(
        [(1, prefill)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path.jsonl", [prefill])
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "prefill_delivery_path_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "PREFILL_DELIVERY_PATH_AUDIT_ACTION_REQUIRED"]


def _fvg_ob_source(**overrides) -> dict:
    row = {
        "schema_version": "fvg_ob_confluence_forward_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "bucket": "ob_only",
        "candidate_outcome_lane": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
        "decision_time_fields": {
            "framework": "ob_retest",
            "h1_poi_type": "OB",
            "h1_poi_price_level": 100.0,
        },
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _fvg_ob_resolution(**overrides) -> dict:
    row = {
        "schema_version": "fvg_ob_confluence_resolution_v1",
        "row_key": "fvg_ob_resolution_fixture",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "framework": "ob_retest",
        "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW",
        "path_metrics": {"base_r_price": 2.0},
        "path_label": "continued_without_entry_touch_to_tp_area",
        "path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "strategy_outcomes": {
            "FVG_OB_CONFLUENCE_OB_AFTER_FVG": {
                "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
                "score_status": "MISSING_REQUIRED_LIVE_METADATA",
                "outcome_status": "NOT_SCORED",
            },
            "V2_STRUCT_FVG_MID_EDGE": {
                "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
                "score_status": "MISSING_REQUIRED_LIVE_METADATA",
                "outcome_status": "NOT_SCORED",
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_fvg_ob_confluence_contract_accepts_audit_row(tmp_path):
    confluence = _fvg_ob_source()
    resolution = _fvg_ob_resolution()
    audit = build_fvg_ob_confluence_audit_rows(
        [(1, confluence)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl", [confluence])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["fvg_ob_confluence_audit_health"]["status"] == "OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("FVG_OB_CONFLUENCE")]


def test_fvg_ob_confluence_allows_append_only_geometry_supersession(tmp_path):
    original = _fvg_ob_source()
    enriched = _fvg_ob_source(
        created_at_utc="2026-05-04T08:01:00+00:00",
        fvg_bounds={"low": 99.5, "high": 100.5},
        manual_backfill_status="FVG_OB_EXACT_GEOMETRY_RECOVERED_FROM_STRATEGY_FOLLOW_DECISION_MSO",
        geometry_recovery_no_leak_status="DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS",
    )
    resolution = _fvg_ob_resolution()
    audit = build_fvg_ob_confluence_audit_rows(
        [(1, original), (2, enriched)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl", [original, enriched])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert not [
        issue
        for issue in report["issues"]
        if issue["code"] == "DUPLICATE_UNIQUE_KEY"
        and issue["path"].endswith("fvg_ob_confluence.jsonl")
    ]


def test_fvg_ob_confluence_audit_legacy_schema_rows_are_archive_allowed():
    confluence = _fvg_ob_source()
    resolution = _fvg_ob_resolution()
    audit = build_fvg_ob_confluence_audit_rows(
        [(1, confluence)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    audit["schema_version"] = "fvg_ob_confluence_audit_v1"
    issues: list[dict] = []

    validate_schema_row(
        "fvg_ob_confluence_audit.jsonl",
        JSONL_SPECS["fvg_ob_confluence_audit.jsonl"],
        1,
        audit,
        issues,
    )

    assert not [issue for issue in issues if issue["code"] == "SCHEMA_VERSION_MISMATCH"]


def test_fvg_ob_confluence_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl", [_fvg_ob_source()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "FVG_OB_CONFLUENCE_AUDIT_MISSING"]


def test_fvg_ob_confluence_contract_flags_action_required_audit_row(tmp_path):
    confluence = _fvg_ob_source(candidate_outcome_lane="synthetic_path_r")
    resolution = _fvg_ob_resolution()
    audit = build_fvg_ob_confluence_audit_rows(
        [(1, confluence)],
        [(1, resolution)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl", [confluence])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_resolutions.jsonl", [resolution])
    _write_jsonl(tmp_path / "shadow_logs" / "fvg_ob_confluence_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "FVG_OB_CONFLUENCE_AUDIT_ACTION_REQUIRED"]


def _context_control_source(**overrides) -> dict:
    row = {
        "schema_version": "context_control_forward_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "LONG",
        "context_question_id": "LIVE_CANDIDATE_CONTEXT_CONTROLS_V1",
        "context_family": "CL_ZN_VIX_CONTROL_CONTEXT",
        "context_values": {"status": "CONTROL_CONTEXT_NOT_JOINED_AT_DECISION_TIME"},
        "control_only": True,
        "evidence_class": "CONTROL_ONLY",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
    }
    row.update(overrides)
    return row


def _context_path_source(**overrides) -> dict:
    row = {
        "schema_version": "candidate_path_follow_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "NAS100_2026-05-04T07:15:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "trade_parameters": {"direction": "LONG"},
        "path_label": "continued_without_entry_touch_to_tp_area",
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_context_control_contract_accepts_audit_row(tmp_path):
    context = _context_control_source()
    path = _context_path_source()
    audit = build_context_control_audit_rows(
        [(1, context)],
        [(1, path)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "context_control_ledger.jsonl", [context])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [path])
    _write_jsonl(tmp_path / "shadow_logs" / "context_control_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["context_control_audit_health"]["status"] == "OK_WITH_DOCUMENTED_CONTEXT_CONTROL_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("CONTEXT_CONTROL")]


def test_context_control_contract_flags_missing_audit_row(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "context_control_ledger.jsonl", [_context_control_source()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "CONTEXT_CONTROL_AUDIT_MISSING"]


def test_context_control_contract_flags_direct_validation_row(tmp_path):
    context = _context_control_source(context_values={"strategy_validation_status": "VALIDATED", "actual_r": 1.0})
    path = _context_path_source()
    audit = build_context_control_audit_rows(
        [(1, context)],
        [(1, path)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    _write_jsonl(tmp_path / "shadow_logs" / "context_control_ledger.jsonl", [context])
    _write_jsonl(tmp_path / "shadow_logs" / "candidate_path_follow.jsonl", [path])
    _write_jsonl(tmp_path / "shadow_logs" / "context_control_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "CONTEXT_CONTROL_DIRECT_STRATEGY_VALIDATION_FORBIDDEN"]
    assert [issue for issue in report["issues"] if issue["code"] == "CONTEXT_CONTROL_AUDIT_ACTION_REQUIRED"]


def _account_truth_source(**overrides) -> dict:
    row = {
        "schema_version": "account_truth_reconciliation_status_v1",
        "row_key": "acct1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "account_truth_status": "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE_OR_NOT_QUERIED_IN_CLOSURE",
        "truth_lane": "ACCOUNT_HISTORY_REQUIRED_FOR_DOLLAR_OR_ACTUAL_R_CLAIMS",
        "actual_r_claim_allowed": False,
        "manual_backfill_status": "SOURCE_BLOCKED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _j46_source(**overrides) -> dict:
    row = {
        "fill_id": "NAS100_2026-04-29_ny_1500",
        "instrument": "NAS100",
        "direction": "LONG",
        "entry_time": "2026-04-29T15:15:05+00:00",
        "entry_price": 27100.36,
        "actual_close": {
            "exit_time": "2026-04-29T20:15:06+00:00",
            "exit_reason": "sl_hit",
            "realized_R": -1.0167,
            "broker_deal_reconciled": True,
        },
    }
    row.update(overrides)
    return row


def test_broker_actual_r_contract_accepts_audit_rows(tmp_path):
    account = _account_truth_source()
    j46 = _j46_source()
    slippage = {"symbol": "NAS100", "ts": "2026-04-29T15:15:05+00:00", "ticket": 234, "fill_price": 27100.36}
    audit_rows = build_broker_actual_r_audit_rows(
        [(1, account)],
        [(1, slippage)],
        [(1, j46)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "account_truth_reconciliation_status.jsonl", [account])
    _write_jsonl(tmp_path / "shadow_logs" / "slippage.jsonl", [slippage])
    _write_jsonl(tmp_path / "shadow_logs" / "j46_j49_shadow_outcomes.jsonl", [j46])
    _write_jsonl(tmp_path / "shadow_logs" / "broker_actual_r_audit.jsonl", audit_rows)

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["broker_actual_r_audit_health"]["status"] == "OK_WITH_DOCUMENTED_ACCOUNTING_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("BROKER_ACTUAL_R")]


def test_broker_actual_r_contract_flags_missing_audit(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "account_truth_reconciliation_status.jsonl", [_account_truth_source()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "BROKER_ACTUAL_R_AUDIT_MISSING"]


def test_broker_actual_r_contract_flags_non_account_history_actual_r_value(tmp_path):
    audit = build_broker_actual_r_audit_rows(
        [(1, _account_truth_source())],
        [],
        [],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )[0]
    audit["broker_actual_r"] = 1.0
    _write_jsonl(tmp_path / "shadow_logs" / "account_truth_reconciliation_status.jsonl", [_account_truth_source()])
    _write_jsonl(tmp_path / "shadow_logs" / "broker_actual_r_audit.jsonl", [audit])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "BROKER_ACTUAL_R_VALUE_ON_NON_ACCOUNT_HISTORY_ROW"]


def _daily_pnl_history_row(**overrides) -> dict:
    row = {
        "ts_utc": "2026-05-01T14:01:05+00:00",
        "symbol": "XAUUSD",
        "trade_id": "XAUUSD_2026-05-01_london_0815",
        "result_r": -0.7395,
        "realized_usd": -739.49,
        "risk_dollars": 1000.0,
        "r_evidence_class": "LOCAL_NOTIFICATION_R_INPUT",
        "dollar_evidence_class": "LOCAL_RISK_DOLLAR_PROJECTION",
        "actual_r_claim_allowed": False,
        "actual_dollar_claim_allowed": False,
        "account_truth_status": "NOT_ACCOUNT_HISTORY_RECONCILED_AT_NOTIFICATION_TIME",
    }
    row.update(overrides)
    return row


def _mt5_close_deal(**overrides) -> dict:
    row = {
        "schema_version": "mt5_account_history_deal_v1",
        "source": "MetaTrader5.history_deals_get",
        "read_only_export": True,
        "ticket": 219581847,
        "order": 235113710,
        "position_id": 235113710,
        "entry": 1,
        "time_utc": "2026-05-01T14:01:05+00:00",
        "symbol": "XAUUSD",
        "profit": -9.85,
        "commission": 0.0,
        "swap": 0.0,
    }
    row.update(overrides)
    return row


def _account_pnl_broker_row(**overrides) -> dict:
    row = {
        "schema_version": "broker_actual_r_audit_v1",
        "row_key": "broker_actual_r_fixture",
        "source_scope": "daily_pnl_history",
        "trade_id": "XAUUSD_2026-05-01_london_0815",
        "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
        "broker_actual_r": -0.7395,
        "actual_r_claim_allowed": True,
        "broker_actual_r_audit_status": "BROKER_ACTUAL_R_AUDIT_COMPLETE",
        "source_links": {"mt5_export_deal_id": 219581847},
    }
    row.update(overrides)
    return row


def test_account_pnl_truth_contract_accepts_reconciliation_rows(tmp_path):
    daily_history = _daily_pnl_history_row()
    broker = _account_pnl_broker_row()
    deal = _mt5_close_deal()
    reconciliation = build_account_pnl_truth_rows(
        daily_pnl_state=None,
        daily_pnl_history_rows=[(1, daily_history)],
        broker_actual_r_rows=[(1, broker)],
        mt5_deal_rows=[(1, deal)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "daily_pnl_history.jsonl", [daily_history])
    _write_jsonl(tmp_path / "shadow_logs" / "broker_actual_r_audit.jsonl", [broker])
    _write_jsonl(tmp_path / "data" / "account_history" / "mt5_deals_2026-04-27_2026-05-05.jsonl", [deal])
    _write_jsonl(tmp_path / "shadow_logs" / "account_pnl_truth_reconciliation.jsonl", reconciliation)

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["account_pnl_truth_health"]["status"] == "OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("ACCOUNT_PNL_TRUTH")]


def test_account_pnl_truth_contract_reads_newer_mt5_deal_exports(tmp_path):
    daily_history = _daily_pnl_history_row()
    broker = _account_pnl_broker_row()
    deal = _mt5_close_deal()
    reconciliation = build_account_pnl_truth_rows(
        daily_pnl_state=None,
        daily_pnl_history_rows=[(1, daily_history)],
        broker_actual_r_rows=[(1, broker)],
        mt5_deal_rows=[(1, deal)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "daily_pnl_history.jsonl", [daily_history])
    _write_jsonl(tmp_path / "shadow_logs" / "broker_actual_r_audit.jsonl", [broker])
    _write_jsonl(tmp_path / "data" / "account_history" / "mt5_deals_2026-04-27_2026-05-11.jsonl", [deal])
    _write_jsonl(tmp_path / "shadow_logs" / "account_pnl_truth_reconciliation.jsonl", reconciliation)

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert not [issue for issue in report["issues"] if issue["code"] == "ACCOUNT_PNL_TRUTH_RECONCILIATION_MISSING"]


def test_account_pnl_truth_contract_flags_missing_reconciliation(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs" / "daily_pnl_history.jsonl", [_daily_pnl_history_row()])

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "ACCOUNT_PNL_TRUTH_RECONCILIATION_MISSING"]


def test_account_pnl_truth_contract_flags_missing_evidence_class(tmp_path):
    daily_history = _daily_pnl_history_row()
    reconciliation = build_account_pnl_truth_rows(
        daily_pnl_state=None,
        daily_pnl_history_rows=[(1, daily_history)],
        broker_actual_r_rows=[],
        mt5_deal_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    reconciliation[0]["r_evidence_class"] = None
    _write_jsonl(tmp_path / "shadow_logs" / "daily_pnl_history.jsonl", [daily_history])
    _write_jsonl(tmp_path / "shadow_logs" / "account_pnl_truth_reconciliation.jsonl", reconciliation)

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "R_CLAIM_MISSING_EVIDENCE_CLASS"]


def _trade_index_record(**overrides) -> dict:
    row = {
        "metadata": {
            "trade_id": "XAUUSD_2026-05-04_london_0715",
            "date": "2026-05-04",
            "symbol": "XAUUSD",
            "kill_zone": "london",
            "candle_close_utc": "2026-05-04T07:15:00+00:00",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_direction": "SHORT",
            "ai_framework": "ob_retest",
            "final_outcome": "LIMIT_PLACED",
            "level2_verification": {"passed": True},
        },
        "trade_parameters": {"direction": "SHORT", "entry_price": 100.0, "stop_loss": 101.0, "take_profit_1": 98.5},
        "limit_intent": {"trade_id": "lim_2026-05-04_0715", "limit_price": 100.0, "stop_loss": 101.0, "take_profit_1": 98.5},
        "execution": None,
        "exit": None,
    }
    row.update(overrides)
    return row


def _trade_index_pending_audit(**overrides) -> dict:
    row = {
        "row_key": "pending1",
        "trade_record_path": "XAUUSD/2026-05-04_london_0715.json",
        "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "final_state": "NO_FILL_CANCELLED_WRONG_SIDE",
        "final_state_status": "FINAL_TERMINAL_NO_FILL",
        "missed_move_classification": "ENTRY_THEN_SL",
        "trade_id_global_uniqueness_status": "UNIQUE_IN_LIFECYCLE_LOG",
    }
    row.update(overrides)
    return row


def test_trade_index_lifecycle_contract_accepts_inventory_and_audit_rows(tmp_path):
    trade_record = _trade_index_record()
    pending = _trade_index_pending_audit()
    trade_path = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "2026-05-04_london_0715.json"
    trade_path.parent.mkdir(parents=True, exist_ok=True)
    trade_path.write_text(json.dumps(trade_record), encoding="utf-8")
    rows = build_trade_index_lifecycle_rows(
        trade_records=[(trade_path, trade_record)],
        trade_records_root=tmp_path / "knowledge_base" / "trade_records",
        pending_lifecycle_audit_rows=[(1, pending)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    inventory = build_inventory_index(rows, generated_at_utc="2026-05-05T00:00:00+00:00")
    _write_jsonl(tmp_path / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl", [pending])
    _write_jsonl(tmp_path / "shadow_logs" / "trade_index_lifecycle_audit.jsonl", rows)
    (tmp_path / "knowledge_base" / "index").mkdir(parents=True, exist_ok=True)
    (tmp_path / "knowledge_base" / "index" / "trade_record_inventory_index_2026-05-05.json").write_text(
        json.dumps(inventory, sort_keys=True),
        encoding="utf-8",
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert report["trade_index_lifecycle_health"]["status"] == "OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS"
    assert not [issue for issue in report["issues"] if issue["code"].startswith("TRADE_INDEX_LIFECYCLE")]


def test_trade_index_lifecycle_contract_flags_missing_audit(tmp_path):
    trade_record = _trade_index_record()
    trade_path = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "2026-05-04_london_0715.json"
    trade_path.parent.mkdir(parents=True, exist_ok=True)
    trade_path.write_text(json.dumps(trade_record), encoding="utf-8")

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "TRADE_INDEX_LIFECYCLE_AUDIT_MISSING"]


def test_trade_index_lifecycle_contract_flags_stale_inventory(tmp_path):
    trade_record = _trade_index_record()
    pending = _trade_index_pending_audit()
    trade_path = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "2026-05-04_london_0715.json"
    trade_path.parent.mkdir(parents=True, exist_ok=True)
    trade_path.write_text(json.dumps(trade_record), encoding="utf-8")
    rows = build_trade_index_lifecycle_rows(
        trade_records=[(trade_path, trade_record)],
        trade_records_root=tmp_path / "knowledge_base" / "trade_records",
        pending_lifecycle_audit_rows=[(1, pending)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    inventory = build_inventory_index(rows, generated_at_utc="2026-05-05T00:00:00+00:00")
    inventory["index_count"] = 0
    _write_jsonl(tmp_path / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl", [pending])
    _write_jsonl(tmp_path / "shadow_logs" / "trade_index_lifecycle_audit.jsonl", rows)
    (tmp_path / "knowledge_base" / "index").mkdir(parents=True, exist_ok=True)
    (tmp_path / "knowledge_base" / "index" / "trade_record_inventory_index_2026-05-05.json").write_text(
        json.dumps(inventory, sort_keys=True),
        encoding="utf-8",
    )

    report = build_report(tmp_path, datetime(2026, 5, 4, 8, 5, tzinfo=timezone.utc))

    assert [issue for issue in report["issues"] if issue["code"] == "TRADE_RECORD_INVENTORY_INDEX_STALE"]


def _nas100_orderflow_status_row(**overrides) -> dict:
    row = {
        "schema_version": "nas100_orderflow_adverse_selection_status_v1",
        "row_key": "lto011_fixture",
        "source_dependency_signature": "abc",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "lto_id": "LTO-011",
        "follow_id": "LIVE-FOLLOW-011",
        "status": "WAITING_FOR_DATABENTO_LIVE_LICENSE",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "databento_raw_symbol": "NQ.FUT",
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "trigger_criteria": {"policy_id": "lto010_databento_live_confluence_policy_v1"},
        "feature_family_forward_plan": [{"family": "depth_availability_thinness"}],
        "databento_live_status": {"latest_status": "LIVE_SESSION_FAILED_NO_LICENSE"},
        "floors": {"broker_actual_r_rows": 20, "mbp10_candidate_rows": 30},
        "current_counts": {"broker_actual_r_rows_nas100_unique": 1, "cached_mbp10_candidate_rows": 12},
        "readiness_gates": {"promotion_claim_allowed": False, "adverse_selection_filter_allowed": False},
        "diagnostic_only": True,
        "no_leak_status": "STATUS_ROW_NOT_A_DECISION_FEATURE",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_nas100_orderflow_status_contract_accepts_diagnostic_rows(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "nas100_orderflow_adverse_selection_status.jsonl",
        [_nas100_orderflow_status_row()],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("nas100_orderflow_adverse_selection_status.jsonl")
    ]


def test_nas100_orderflow_status_contract_rejects_paid_data_counter(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "nas100_orderflow_adverse_selection_status.jsonl",
        [_nas100_orderflow_status_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
        and issue["path"].endswith("nas100_orderflow_adverse_selection_status.jsonl")
    ]


def _sierra_depth_enrichment_status_row(**overrides) -> dict:
    row = {
        "schema_version": "sierra_depth_enrichment_status_v1",
        "row_key": "lto012_fixture",
        "source_dependency_signature": "abc",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "lto_id": "LTO-012",
        "follow_id": "LIVE-FOLLOW-010",
        "status": "OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE",
        "depth_feature_version": "sierra_depth_predecision_eob_top10_v2",
        "feature_status_counts": {"FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD": 1},
        "source_status_counts": {"LOCAL_SIERRA_DEPTH_CAPTURED": 1},
        "interpretation_status_counts": {"USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT": 1},
        "current_counts": {"latest_candidate_rows": 1, "latest_feature_rows": 1},
        "background_queue_policy": {"file_size_guard": "supported_by_max_file_size_mb"},
        "boundary": "shadow confluence only",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_sierra_depth_enrichment_status_contract_accepts_guarded_rows(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "sierra_depth_enrichment_status.jsonl",
        [_sierra_depth_enrichment_status_row()],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("sierra_depth_enrichment_status.jsonl")
    ]


def test_sierra_depth_enrichment_status_contract_rejects_paid_data_counter(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "sierra_depth_enrichment_status.jsonl",
        [_sierra_depth_enrichment_status_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
        and issue["path"].endswith("sierra_depth_enrichment_status.jsonl")
    ]


def _sierra_proxy_registry_status_row(**overrides) -> dict:
    row = {
        "schema_version": "sierra_proxy_registry_status_v1",
        "row_key": "lto013_fixture",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "lto_id": "LTO-013",
        "follow_ids": ["LIVE-FOLLOW-002", "LIVE-FOLLOW-010", "LIVE-FOLLOW-028"],
        "candidate_id": "NAS100_2026-05-04T16:30:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "decision_time_utc": "2026-05-04T16:30:00+00:00",
        "source_dependency_signature": "abc",
        "source_system": "sierra_registry",
        "sierra_source_symbol": "NQM26-CME",
        "sierra_futures_symbol": "NQ.v.0",
        "sierra_tick_size": 0.25,
        "proxy_class": "VALIDATED_PROXY",
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "DATABENTO_MBP10_PARITY_EXACT_ON_REGISTERED_NQ_PILOT",
        "interpretation_status": "USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT",
        "allowed_use": "predecision_nq_mbp10_depth_context_shadow_only",
        "claim_boundary": "shadow context only",
        "depth_interpretation_allowed": True,
        "scid_interpretation_allowed": True,
        "control_only": False,
        "registry_status": "REGISTERED",
        "backfill_policy": "candidate_registry_status_only_no_file_scan",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_sierra_proxy_registry_status_contract_accepts_registered_rows(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "sierra_proxy_registry_status.jsonl",
        [_sierra_proxy_registry_status_row()],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("sierra_proxy_registry_status.jsonl")
    ]


def test_sierra_proxy_registry_status_contract_rejects_paid_data_counter(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs" / "sierra_proxy_registry_status.jsonl",
        [_sierra_proxy_registry_status_row(paid_data_calls=1)],
    )

    report = build_report(tmp_path, datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc))

    assert [
        issue
        for issue in report["issues"]
        if issue["code"] == "GAP_CLOSURE_CALL_COUNTER_NONZERO"
        and issue["path"].endswith("sierra_proxy_registry_status.jsonl")
    ]


def _v2_selector_audit_source_row(**overrides) -> dict:
    row = {
        "schema_version": "v2b_forward_pair_resolution_audit_v1",
        "row_key": "v2-selector-audit-source",
        "candidate_id": "NAS100_2026-05-04T13:15:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "backfilled_at_utc": "2026-05-05T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T13:15:00+00:00",
        "symbol": "NAS100",
        "duplicate_aware_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
        "pending_limit_lifecycle_audit_status": "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "broker_actual_r_pair_counted": False,
        "synthetic_path_r_pair_counted": True,
        "documented_limitation_codes": [
            "OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA"
        ],
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def test_v2_structural_selector_readiness_contract_accepts_not_ready_status(tmp_path):
    now = datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc)
    source = _v2_selector_audit_source_row()
    _write_jsonl(tmp_path / "shadow_logs" / "v2b_forward_pair_resolution_audit.jsonl", [source])
    row = build_v2_selector_readiness_row(
        root=tmp_path,
        v2b_audit_rows=[(1, source)],
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "v2_structural_selector_readiness.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["v2_structural_selector_readiness_health"]["status"] == "OK_WITH_DOCUMENTED_V2_SELECTOR_NOT_READY"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("v2_structural_selector_readiness.jsonl")
    ]


def _xauusd_registry_fixture() -> dict:
    return {
        "schema_version": "xauusd_source_transfer_frozen_slice_registry_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "live_trading_behavior_changed": False,
        "families": ["XAUUSD.scid same-market", "GC/MGC futures proxy"],
        "evidence_classes": ["SAME_MARKET_SOURCE_TRANSFER", "FUTURES_PROXY_TRANSFER"],
        "frozen_question": "fixture",
        "target_resolved_rows_before_validation_discussion": 30,
        "holdout_policy": "no outcomes",
    }


def _xauusd_source_map_fixture() -> dict:
    return {
        "schema_version": "forward_capture_source_map_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "live_trading_behavior_changed": False,
        "opened_outcome_slices": [],
    }


def _xauusd_sierra_inventory_fixture() -> dict:
    return {
        "schema_version": "sierra_forward_capture_inventory_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "symbols": [
            {"symbol_root": "XAUUSD", "status": "CAUTION_SCID_PRESENT_DEPTH_MISSING", "scid_file_count": 1, "depth_file_count": 0},
            {"symbol_root": "GC", "status": "READY_SCID_AND_DEPTH_PRESENT", "scid_file_count": 1, "depth_file_count": 2},
            {"symbol_root": "MGC", "status": "READY_SCID_AND_DEPTH_PRESENT", "scid_file_count": 1, "depth_file_count": 2},
        ],
    }


def test_xauusd_same_market_extension_contract_accepts_preregistration(tmp_path):
    now = datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc)
    registry = _xauusd_registry_fixture()
    source_map = _xauusd_source_map_fixture()
    inventory = _xauusd_sierra_inventory_fixture()
    candidate = {"candidate_id": "XAUUSD_2026-05-04T13:15:00+00:00", "symbol": "XAUUSD", "decision_time_utc": "2026-05-04T13:15:00+00:00"}
    (tmp_path / "research" / "program_control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "research" / "program_control" / "XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04.json").write_text(json.dumps(registry), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json").write_text(json.dumps(source_map), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json").write_text(json.dumps(inventory), encoding="utf-8")
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    row = build_xauusd_same_market_status_row(
        registry=registry,
        source_map=source_map,
        sierra_inventory=inventory,
        candidate_rows=[(1, candidate)],
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "xauusd_same_market_extension_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["xauusd_same_market_extension_health"]["status"] == "OK_WITH_DOCUMENTED_XAUUSD_SAME_MARKET_PREREGISTRATION"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("xauusd_same_market_extension_status.jsonl")
    ]


def test_xauusd_same_market_extension_contract_ignores_forward_snapshot_churn(tmp_path):
    now = datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc)
    registry = _xauusd_registry_fixture()
    source_map = _xauusd_source_map_fixture()
    inventory = _xauusd_sierra_inventory_fixture()
    candidate = {"candidate_id": "XAUUSD_2026-05-04T13:15:00+00:00", "symbol": "XAUUSD", "decision_time_utc": "2026-05-04T13:15:00+00:00"}
    old_eval = {"symbol": "XAUUSD", "decision_time_utc": "2026-05-04T13:15:00+00:00"}
    fresh_eval = {"symbol": "XAUUSD", "decision_time_utc": "2026-05-04T13:30:00+00:00"}
    (tmp_path / "research" / "program_control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "research" / "program_control" / "XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04.json").write_text(json.dumps(registry), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json").write_text(json.dumps(source_map), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json").write_text(json.dumps(inventory), encoding="utf-8")
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl", [candidate])
    _write_jsonl(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl", [old_eval, fresh_eval])
    row = build_xauusd_same_market_status_row(
        registry=registry,
        source_map=source_map,
        sierra_inventory=inventory,
        candidate_rows=[(1, candidate)],
        evaluation_rows=[(1, old_eval)],
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "xauusd_same_market_extension_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["xauusd_same_market_extension_health"]["status"] == "OK_WITH_DOCUMENTED_XAUUSD_SAME_MARKET_PREREGISTRATION"
    assert report["xauusd_same_market_extension_health"]["stale_fields"] == []
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("xauusd_same_market_extension_status.jsonl")
    ]


def _es_mes_conversion_fixture() -> dict:
    return {
        "schema_version": "expanded_oos_first_wave_bounded_conversion_status_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "m15_inventory": [
            {"file_symbol": "SPX_ES", "source_symbol": "ESM26-CME", "rows": 268},
            {"file_symbol": "SPX_MES", "source_symbol": "MESM26-CME", "rows": 268},
        ],
    }


def _es_mes_label_status_fixture() -> dict:
    return {
        "schema_version": "expanded_oos_first_wave_label_status_audit_v1",
        "status": "RESEARCH_ARTIFACT_DONE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "families": [
            {
                "family": "S&P with ES/MES",
                "label_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
            }
        ],
    }


def _es_mes_sierra_inventory_fixture() -> dict:
    return {
        "schema_version": "sierra_forward_capture_inventory_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "symbols": [
            {"symbol_root": "ES", "status": "READY_SCID_AND_DEPTH_PRESENT", "scid_file_count": 1, "depth_file_count": 2},
            {"symbol_root": "MES", "status": "READY_SCID_AND_DEPTH_PRESENT", "scid_file_count": 2, "depth_file_count": 2},
        ],
    }


def test_es_mes_preregistration_contract_accepts_closed_outcomes(tmp_path):
    now = datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc)
    registry = default_es_mes_registry_payload(now.isoformat())
    prior = {"schema_version": "es_mes_pre_registration_v1", "promotion_verdict": "NO_PROMOTION_VERDICT"}
    conversion = _es_mes_conversion_fixture()
    label_status = _es_mes_label_status_fixture()
    inventory = _es_mes_sierra_inventory_fixture()
    (tmp_path / "research" / "program_control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "research" / "program_control" / "ES_MES_STRATEGY_COHORT_REGISTRY_2026-05-05.json").write_text(json.dumps(registry), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "ES_MES_PRE_REGISTRATION_2026-05-04.json").write_text(json.dumps(prior), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_2026-05-04.json").write_text(json.dumps(conversion), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_2026-05-04.json").write_text(json.dumps(label_status), encoding="utf-8")
    (tmp_path / "research" / "program_control" / "SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json").write_text(json.dumps(inventory), encoding="utf-8")
    row = build_es_mes_prereg_status_row(
        root=tmp_path,
        registry=registry,
        prior_preregistration=prior,
        conversion_status=conversion,
        label_status=label_status,
        sierra_inventory=inventory,
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "es_mes_preregistration_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["es_mes_preregistration_health"]["status"] == "OK_WITH_DOCUMENTED_ES_MES_PREREGISTRATION"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("es_mes_preregistration_status.jsonl")
    ]


def _shadow_observer_registry_fixture() -> dict:
    forbidden = [
        "ai_api_call",
        "canary_call",
        "order_send",
        "execution_engine",
        "permission_gate",
        "outcome_opening",
    ]
    active = [
        {
            "observer_id": "eurusd_6e_mso_shadow_v1",
            "enabled": True,
            "activation_state": "ACTIVE_MSO_SHADOW",
            "symbol": "EURUSD",
            "broker_symbol": "EURUSD",
            "config_symbol": "EURUSD",
            "family": "EURUSD/6E",
            "evidence_class": "FORWARD_SHADOW",
            "source_status": "LABEL_STATUS_ONLY_NO_REGISTERED_OUTCOME_COHORT",
            "pre_registered_question_id": "SHADOW-EURUSD",
            "allowed_rows": ["strategy_follow_evaluation_v1"],
            "forbidden": forbidden,
        },
        {
            "observer_id": "ger40_tier2_mso_shadow_v1",
            "enabled": True,
            "activation_state": "ACTIVE_MSO_SHADOW",
            "symbol": "GER40",
            "broker_symbol": "GER30",
            "config_symbol": "GER40",
            "family": "GER40 tier-2",
            "evidence_class": "FORWARD_SHADOW",
            "source_status": "TIER2_BACKTEST_ONLY_NO_PROMOTION",
            "pre_registered_question_id": "SHADOW-GER40",
            "allowed_rows": ["strategy_follow_evaluation_v1"],
            "forbidden": forbidden,
        },
    ]
    inactive = [
        ("uko_usd_cl_context_only_v1", "CONTEXT_CONTROL_ONLY", "UKOUSD"),
        ("zn_rates_context_only_v1", "CONTEXT_CONTROL_ONLY", "ZN_CONTROL"),
        ("vix_vxm_context_only_v1", "CONTEXT_CONTROL_ONLY", "VIX_VXM"),
        ("spx500_es_prereg_required_v1", "PRE_REGISTRATION_REQUIRED", "SPX500"),
        ("nzdusd_historical_excluded_v1", "EXCLUDED_KILLED_HISTORICAL", "NZDUSD"),
        ("xagusd_depth_future_v1", "PRE_REGISTRATION_REQUIRED", "XAGUSD"),
    ]
    return {
        "schema_version": "shadow_observer_registry_v1",
        "instruments": [
            *active,
            *[
                {
                    "observer_id": observer_id,
                    "enabled": False,
                    "activation_state": state,
                    "symbol": symbol,
                    "broker_symbol": symbol,
                    "config_symbol": None,
                    "family": "fixture inactive",
                    "evidence_class": "CONTROL_ONLY",
                    "source_status": "LABEL_STATUS_ONLY",
                }
                for observer_id, state, symbol in inactive
            ],
        ],
    }


def _shadow_observer_agent_config_fixture() -> dict:
    return {
        "instruments": {
            "EURUSD": {"market": {"kill_zones": {"ny": {"start_utc": "13:00", "end_utc": "15:30"}}}},
            "GER40": {"market": {"kill_zones": {"ny": {"start_utc": "14:00", "end_utc": "19:00"}}}},
        }
    }


def test_shadow_observer_hardening_contract_accepts_source_status(tmp_path):
    now = datetime(2026, 5, 5, 0, 5, tzinfo=timezone.utc)
    registry = _shadow_observer_registry_fixture()
    config = _shadow_observer_agent_config_fixture()
    state = {
        "eurusd_6e_mso_shadow_v1": {"last_candle_close_utc": "2026-05-04T15:15:00+00:00"},
        "ger40_tier2_mso_shadow_v1": {"last_candle_close_utc": "2026-05-04T19:00:00+00:00"},
    }
    status_rows = [
        {
            "schema_version": "shadow_observer_status_v1",
            "created_at_utc": "2026-05-05T00:02:00+00:00",
            "symbol": "EURUSD",
            "observer_id": "eurusd_6e_mso_shadow_v1",
            "activation_state": "ACTIVE_MSO_SHADOW",
            "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        {
            "schema_version": "shadow_observer_status_v1",
            "created_at_utc": "2026-05-05T00:03:00+00:00",
            "symbol": "GER40",
            "observer_id": "ger40_tier2_mso_shadow_v1",
            "activation_state": "ACTIVE_MSO_SHADOW",
            "lifecycle_status": "SKIPPED_OUTSIDE_KILL_ZONE",
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
    ]
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "shadow_observer_registry.yaml").write_text(
        yaml.safe_dump(registry),
        encoding="utf-8",
    )
    (tmp_path / "config" / "agent_config.yaml").write_text(
        yaml.safe_dump(config),
        encoding="utf-8",
    )
    (tmp_path / "pipeline_state" / "shadow_observer_state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )
    _write_jsonl(tmp_path / "shadow_logs" / "shadow_observer_status.jsonl", status_rows)
    row = build_shadow_observer_hardening_status_row(
        observer_registry=registry,
        agent_config=config,
        observer_state=state,
        status_rows=[(index, row) for index, row in enumerate(status_rows, start=1)],
        generated_at_utc=now.isoformat(),
    )
    _write_jsonl(tmp_path / "shadow_logs" / "shadow_observer_hardening_status.jsonl", [row])

    report = build_report(tmp_path, now)

    assert report["shadow_observer_hardening_health"]["status"] == "OK_WITH_DOCUMENTED_SHADOW_OBSERVER_HARDENING"
    assert not [
        issue
        for issue in report["issues"]
        if issue["path"].endswith("shadow_observer_hardening_status.jsonl")
    ]
