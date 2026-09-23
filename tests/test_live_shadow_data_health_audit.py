from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_live_shadow_data_health import (
    _is_conditionally_allowed_null,
    audit_opportunity_counts,
    audit_trade_record_candidate_coverage,
    build_report,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _candidate() -> dict:
    return {
        "candidate_id": "XAGUSD_2026-05-04T10:00:00+00:00",
        "created_at_utc": "2026-05-04T10:00:25+00:00",
        "decision_time_utc": "2026-05-04T10:00:00+00:00",
        "symbol": "XAGUSD",
        "broker_symbol": "XAGUSD",
        "side": "SHORT",
        "framework": "ob_retest",
        "final_outcome_at_log": "REJECTED_L2",
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 75.471,
            "stop_loss": 75.924,
            "take_profit_1": 74.791,
        },
        "external_confluence": {
            "sierra": {"status": "FEATURES_EXTRACTED", "paid_fetch_attempted": False},
            "databento": {"status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE", "paid_fetch_attempted": False},
        },
        "strategy_snapshots": [
            {"strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR"},
            {"strategy_id": "PENDING_LIMIT_LIFECYCLE"},
        ],
    }


def _base_logs(tmp_path: Path) -> None:
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    cid = candidate["candidate_id"]
    asof = "2026-05-04T11:15:00+00:00"
    _write_jsonl(shadow / "strategy_follow_candidates.jsonl", [candidate])
    path = {
        "candidate_id": cid,
        "created_at_utc": "2026-05-04T11:15:01+00:00",
        "asof_latest_candle_utc": asof,
        "decision_time_utc": candidate["decision_time_utc"],
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "path_label": "entry_touched_then_reached_tp1",
        "trade_parameters": candidate["trade_parameters"],
    }
    _write_jsonl(shadow / "candidate_path_follow.jsonl", [path])
    _write_jsonl(
        shadow / "live_candidate_opportunity_clusters.jsonl",
        [
            {
                **path,
                "opportunity_id": "opp1",
                "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
                "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
                "opportunity_similarity": {"materially_same_setup": True},
            }
        ],
    )
    _write_jsonl(
        shadow / "live_candidate_strategy_rollups.jsonl",
        [
            {
                **path,
                "strategy_statuses": {
                    "LIVE_AI_J46_J49_BASELINE_COMPARATOR": {"score_status": "COMPUTED_FROM_CANDIDATE_PATH"},
                    "PENDING_LIMIT_LIFECYCLE": {"score_status": "COMPUTED_FROM_CANDIDATE_PATH"},
                },
                "unresolved_strategies": {},
            }
        ],
    )
    for name in (
        "v2b_forward_pairs.jsonl",
        "prefill_delivery_path.jsonl",
        "fvg_ob_confluence.jsonl",
        "context_control_ledger.jsonl",
        "live_structural_strategy_metadata.jsonl",
        "databento_live_trigger_decisions.jsonl",
        "sierra_confluence_source_status.jsonl",
        "account_truth_reconciliation_status.jsonl",
        "v2b_forward_pair_resolutions.jsonl",
        "prefill_delivery_path_resolutions.jsonl",
        "fvg_ob_confluence_resolutions.jsonl",
        "missed_opportunity_shadow.jsonl",
        "candidate_ltf_path_order.jsonl",
    ):
        row = {
            **path,
            "missing_exact_required_fields": {},
            "affected_strategy_ids": [],
        }
        _write_jsonl(shadow / name, [row])
    _write_jsonl(
        shadow / "sierra_depth_feature_snapshots.jsonl",
        [
            {
                **path,
                "row_key": f"sierra_depth_feature_snapshot_v1|{cid}|SIM26-COMEX|FEATURES_EXTRACTED|fixture",
                "source_system": "sierra_depth",
                "depth_path": "C:/SierraChart/Data/MarketDepthData/SIM26-COMEX.2026-05-04.depth",
                "feature_status": "FEATURES_EXTRACTED",
                "features_present": True,
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
                "no_leak_status": "PASS_PRE_DECISION_WINDOWS_ONLY",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )
    _write_jsonl(
        shadow / "live_mechanical_strategy_shadow_outcomes.jsonl",
        [
            {
                **path,
                "strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
            {
                **path,
                "strategy_id": "PENDING_LIMIT_LIFECYCLE",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
        ],
    )


def test_data_health_ok_when_candidate_dependent_rows_are_complete(tmp_path):
    _base_logs(tmp_path)

    report = build_report(tmp_path)

    assert report["status"] == "OK_WITH_DOCUMENTED_LIMITATIONS"
    assert report["issues"] == []
    assert report["counts"]["latest_candidates"] == 1
    assert report["opportunity_counting_health"]["status_counts"] == {
        "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY": 1
    }


def test_sierra_no_registered_proxy_nulls_are_documented_not_unexpected(tmp_path):
    _base_logs(tmp_path)
    cid = _candidate()["candidate_id"]
    _write_jsonl(
        tmp_path / "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        [
            {
                **_candidate(),
                "row_key": f"sierra_depth_feature_snapshot_v1|{cid}|NO_PROXY|NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "source_system": "sierra_depth",
                "sierra_futures_symbol": None,
                "sierra_source_symbol": None,
                "depth_path": None,
                "feature_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "features_present": False,
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
                "no_leak_status": "NO_SIERRA_SOURCE_REGISTERED",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )

    report = build_report(tmp_path)

    null_health = report["null_field_health"]
    assert report["status"] == "OK_WITH_DOCUMENTED_LIMITATIONS"
    assert null_health["critical_null_counts"] == {}
    assert "sierra_depth_feature_snapshots.jsonl.depth_path" not in null_health["unexpected_null_counts"]
    assert "sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol" not in null_health["unexpected_null_counts"]
    assert "sierra_depth_feature_snapshots.jsonl.sierra_source_symbol" not in null_health["unexpected_null_counts"]
    assert null_health["allowed_null_counts"][
        "sierra_depth_feature_snapshots.jsonl.depth_path"
    ] == 1
    assert null_health["allowed_null_counts"][
        "sierra_depth_feature_snapshots.jsonl.sierra_futures_symbol"
    ] == 1
    assert null_health["allowed_null_counts"][
        "sierra_depth_feature_snapshots.jsonl.sierra_source_symbol"
    ] == 1


def test_missing_dependent_log_is_action_required(tmp_path):
    _base_logs(tmp_path)
    (tmp_path / "shadow_logs/candidate_ltf_path_order.jsonl").unlink()

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert any(issue["code"] == "MISSING_CANDIDATE_COVERAGE" for issue in report["issues"])


def test_path_label_geometry_mismatch_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    row = {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T11:15:01+00:00",
        "asof_latest_candle_utc": "2026-05-04T11:15:00+00:00",
        "decision_time_utc": candidate["decision_time_utc"],
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "path_label": "entry_touched_then_reached_tp1",
        "touched_entry": False,
        "hit_tp1": False,
        "trade_parameters": candidate["trade_parameters"],
    }
    _write_jsonl(shadow / "candidate_path_follow.jsonl", [row])

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert any(issue["code"] == "PATH_LABEL_GEOMETRY_MISMATCH" for issue in report["issues"])


def test_limit_placed_candidate_requires_lifecycle_join(tmp_path):
    _base_logs(tmp_path)
    candidate = _candidate()
    candidate["final_outcome_at_log"] = "LIMIT_PLACED"
    candidate["trade_id"] = "lim_fixture"
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [candidate])

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert report["pending_lifecycle_health"]["missing_limit_placed_join_candidates"] == [
        candidate["candidate_id"]
    ]
    assert any(issue["code"] == "MISSING_LIMIT_PLACED_LIFECYCLE_JOIN" for issue in report["issues"])


def test_sierra_source_status_feature_interpretation_mismatch_is_action_required(tmp_path):
    _base_logs(tmp_path)
    candidate = _candidate()
    cid = candidate["candidate_id"]
    _write_jsonl(
        tmp_path / "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        [
            {
                **candidate,
                "row_key": f"sierra_depth_feature_snapshot_v1|{cid}|NO_PROXY|NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "source_system": "sierra_depth",
                "depth_path": "C:/SierraChart/Data/MarketDepthData/SHOULD_NOT_EXIST.depth",
                "feature_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
                "features_present": True,
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
                "no_leak_status": "NO_SIERRA_SOURCE_REGISTERED",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ],
    )

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert any(
        issue["code"] == "SOURCE_STATUS_FEATURE_INTERPRETATION_MISMATCH"
        for issue in report["issues"]
    )


def test_identity_conflict_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    _write_jsonl(
        shadow / "candidate_path_follow.jsonl",
        [
            {
                "candidate_id": candidate["candidate_id"],
                "created_at_utc": "2026-05-04T11:15:01+00:00",
                "asof_latest_candle_utc": "2026-05-04T11:15:00+00:00",
                "decision_time_utc": candidate["decision_time_utc"],
                "symbol": "NAS100",
                "broker_symbol": candidate["broker_symbol"],
                "side": candidate["side"],
                "framework": candidate["framework"],
                "path_label": "entry_touched_then_reached_tp1",
                "trade_parameters": candidate["trade_parameters"],
            }
        ],
    )

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert any(issue["code"] == "CANDIDATE_IDENTITY_CONFLICT" for issue in report["issues"])


def test_unknown_opportunity_counting_status_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    rows = [
        json.loads(line)
        for line in (shadow / "live_candidate_opportunity_clusters.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    rows[0]["opportunity_counting_status"] = "COUNT_ME_TWICE_MAYBE"
    _write_jsonl(shadow / "live_candidate_opportunity_clusters.jsonl", rows)

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert report["opportunity_counting_health"]["unknown_status_candidates"] == [
        _candidate()["candidate_id"]
    ]
    assert any(issue["code"] == "OPPORTUNITY_UNKNOWN_COUNTING_STATUS" for issue in report["issues"])


def test_multiple_countable_rows_for_one_opportunity_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    second = {
        **candidate,
        "candidate_id": "XAGUSD_2026-05-04T10:15:00+00:00",
        "decision_time_utc": "2026-05-04T10:15:00+00:00",
    }
    _write_jsonl(shadow / "strategy_follow_candidates.jsonl", [candidate, second])
    for name in (
        "candidate_path_follow.jsonl",
        "v2b_forward_pairs.jsonl",
        "prefill_delivery_path.jsonl",
        "fvg_ob_confluence.jsonl",
        "context_control_ledger.jsonl",
        "live_structural_strategy_metadata.jsonl",
        "databento_live_trigger_decisions.jsonl",
        "sierra_confluence_source_status.jsonl",
        "sierra_depth_feature_snapshots.jsonl",
        "account_truth_reconciliation_status.jsonl",
        "live_candidate_strategy_rollups.jsonl",
        "v2b_forward_pair_resolutions.jsonl",
        "prefill_delivery_path_resolutions.jsonl",
        "fvg_ob_confluence_resolutions.jsonl",
        "missed_opportunity_shadow.jsonl",
        "candidate_ltf_path_order.jsonl",
    ):
        rows = [json.loads(line) for line in (shadow / name).read_text(encoding="utf-8").splitlines()]
        clone = {**rows[0], "candidate_id": second["candidate_id"], "decision_time_utc": second["decision_time_utc"]}
        rows.append(clone)
        _write_jsonl(shadow / name, rows)
    mechanical_rows = [
        json.loads(line)
        for line in (shadow / "live_mechanical_strategy_shadow_outcomes.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    mechanical_rows.extend(
        [{**row, "candidate_id": second["candidate_id"], "decision_time_utc": second["decision_time_utc"]} for row in mechanical_rows]
    )
    _write_jsonl(shadow / "live_mechanical_strategy_shadow_outcomes.jsonl", mechanical_rows)
    cluster_rows = [
        {
            "candidate_id": candidate["candidate_id"],
            "created_at_utc": "2026-05-04T11:15:01+00:00",
            "asof_latest_candle_utc": "2026-05-04T11:15:00+00:00",
            "opportunity_id": "opp1",
            "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
            "opportunity_similarity": {"materially_same_setup": True},
        },
        {
            "candidate_id": second["candidate_id"],
            "created_at_utc": "2026-05-04T11:15:01+00:00",
            "asof_latest_candle_utc": "2026-05-04T11:15:00+00:00",
            "opportunity_id": "opp1",
            "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
            "opportunity_similarity": {"materially_same_setup": True},
        },
    ]
    _write_jsonl(shadow / "live_candidate_opportunity_clusters.jsonl", cluster_rows)

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert any(issue["code"] == "OPPORTUNITY_PRIMARY_COUNT_INVALID" for issue in report["issues"])


def test_overlap_suppressed_primary_is_not_counted_as_corrupt_data(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    rows = [
        {
            "candidate_id": _candidate()["candidate_id"],
            "created_at_utc": "2026-05-04T11:15:01+00:00",
            "asof_latest_candle_utc": "2026-05-04T11:15:00+00:00",
            "opportunity_id": "overlap_opp",
            "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
            "opportunity_counting_status": "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP",
            "opportunity_duplicate_status": "PRIMARY_UNIQUE_OPPORTUNITY",
            "opportunity_sequence_index": 0,
            "same_symbol_overlap_status": "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE",
            "overlapping_active_symbol_opportunity_ids": ["already_active"],
            "opportunity_similarity": {"materially_same_setup": True},
        }
    ]
    _write_jsonl(shadow / "live_candidate_opportunity_clusters.jsonl", rows)

    report = build_report(tmp_path)

    assert report["status"] == "OK_WITH_DOCUMENTED_LIMITATIONS"
    assert report["opportunity_counting_health"]["primary_suppressed_by_overlap_opportunity_ids"] == [
        "overlap_opp"
    ]
    assert not any(issue["code"] == "OPPORTUNITY_PRIMARY_COUNT_INVALID" for issue in report["issues"])


def test_overlap_suppressed_primary_with_duplicates_is_valid_opportunity_counting():
    issues: list[dict] = []
    rows = {
        "primary": {
            "candidate_id": "primary",
            "opportunity_id": "overlap_opp",
            "opportunity_counting_status": "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP",
            "opportunity_duplicate_status": "PRIMARY_UNIQUE_OPPORTUNITY",
            "opportunity_sequence_index": 0,
            "same_symbol_overlap_status": "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE",
            "overlapping_active_symbol_opportunity_ids": ["already_active"],
            "opportunity_similarity": {"materially_same_setup": True},
        },
        "duplicate": {
            "candidate_id": "duplicate",
            "opportunity_id": "overlap_opp",
            "opportunity_counting_status": "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
            "opportunity_duplicate_status": "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP",
            "opportunity_sequence_index": 1,
            "opportunity_first_candidate_id": "primary",
            "same_symbol_overlap_status": "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE",
            "overlapping_active_symbol_opportunity_ids": ["already_active"],
            "opportunity_similarity": {"materially_same_setup": True},
        },
    }

    health = audit_opportunity_counts(rows, issues)

    assert issues == []
    assert health["primary_suppressed_by_overlap_opportunity_ids"] == ["overlap_opp"]


def test_source_not_captured_is_reported_as_documented_limitation(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    structural_row = {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T10:01:00+00:00",
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "decision_time_utc": candidate["decision_time_utc"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "missing_exact_required_fields": {"fvg_lock_state": "SOURCE_NOT_CAPTURED"},
        "affected_strategy_ids": ["V3_FVG_ONLY_RESCUE_RISK_BANK"],
    }
    _write_jsonl(shadow / "live_structural_strategy_metadata.jsonl", [structural_row])

    report = build_report(tmp_path)

    assert report["status"] == "OK_WITH_DOCUMENTED_LIMITATIONS"
    assert report["issues"] == []
    assert report["documented_limitations"]["source_not_captured_fields"] == {"fvg_lock_state": 1}


def test_legacy_source_not_captured_is_split_from_current_forward_gap(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    structural_row = {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T10:01:00+00:00",
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "decision_time_utc": candidate["decision_time_utc"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "decision_time_structural_capture_status": "LEGACY_CANDIDATE_ROW_WITHOUT_STRUCTURAL_SOURCE_CAPTURE",
        "missing_exact_required_fields": {"fvg_lock_state": "SOURCE_NOT_CAPTURED"},
        "affected_strategy_ids": ["V3_FVG_ONLY_RESCUE_RISK_BANK"],
    }
    _write_jsonl(shadow / "live_structural_strategy_metadata.jsonl", [structural_row])

    report = build_report(tmp_path)

    assert report["documented_limitations"]["source_not_captured_fields"] == {}
    assert report["documented_limitations"]["legacy_source_not_captured_fields"] == {"fvg_lock_state": 1}


def test_lane_expectation_modes_are_reported(tmp_path):
    _base_logs(tmp_path)

    report = build_report(tmp_path)

    assert "candidate_driven_path_aligned" in report["lane_expectation_health"]["expectation_modes"]
    assert "source_driven_lifecycle_join" in report["lane_expectation_health"]["expectation_modes"]
    assert "source_driven_readiness_status" in report["lane_expectation_health"]["expectation_modes"]
    assert "source_driven_preregistration_status" in report["lane_expectation_health"]["expectation_modes"]
    assert "source_driven_observer_hardening_status" in report["lane_expectation_health"]["expectation_modes"]
    assert report["lane_expectation_health"]["row_counts_by_mode"]["candidate_registry"] == 1


def test_critical_null_field_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    candidate = _candidate()
    candidate["side"] = None
    _write_jsonl(shadow / "strategy_follow_candidates.jsonl", [candidate])

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert report["null_field_health"]["critical_null_counts"] == {
        "strategy_follow_candidates.jsonl.side": 1
    }
    assert any(issue["code"] == "CRITICAL_FIELD_NULL" for issue in report["issues"])


def test_waiting_path_asof_null_is_documented_not_action_required():
    row = {
        "candidate_id": "NAS100_2026-05-08T08:15:00+00:00",
        "candidate_path_status": "WAITING_FOR_PATH_ROW",
        "asof_latest_candle_utc": None,
    }

    assert _is_conditionally_allowed_null(
        "live_candidate_opportunity_clusters.jsonl",
        "asof_latest_candle_utc",
        row,
    )
    assert _is_conditionally_allowed_null(
        "live_candidate_strategy_rollups.jsonl",
        "asof_latest_candle_utc",
        row,
    )


def test_orphan_dependent_candidate_row_is_action_required(tmp_path):
    _base_logs(tmp_path)
    shadow = tmp_path / "shadow_logs"
    rows = [
        json.loads(line)
        for line in (shadow / "v2b_forward_pairs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    rows.append({**rows[0], "candidate_id": "MISSING_2026-05-04T10:00:00+00:00"})
    _write_jsonl(shadow / "v2b_forward_pairs.jsonl", rows)

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert report["all_row_identity_health"]["orphan_dependent_rows_by_log"] == {
        "v2b_forward_pairs.jsonl": ["MISSING_2026-05-04T10:00:00+00:00"]
    }
    assert any(issue["code"] == "ORPHAN_DEPENDENT_CANDIDATE_ROW" for issue in report["issues"])


def test_trade_record_candidate_collision_is_documented_not_compared_to_wrong_source(tmp_path):
    root = tmp_path
    records_root = root / "knowledge_base" / "trade_records" / "XAUUSD"
    records_root.mkdir(parents=True, exist_ok=True)
    candidate_id = "XAUUSD_2026-05-03T16:30:00+00:00"

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
                "final_outcome": "REJECTED_GATE3_CIRCUIT_BREAKER",
            },
            "ai_response": {
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_parameters": {
                    "direction": "SHORT",
                    "entry_price": entry,
                    "stop_loss": stop,
                    "take_profit_1": tp1,
                },
            },
        }

    first = records_root / "2026-05-03_ny_1630.json"
    second = records_root / "2026-05-03_ny_1645.json"
    first.write_text(json.dumps(_record(4668.45, 4681.54, 4649.82), sort_keys=True), encoding="utf-8")
    second.write_text(json.dumps(_record(4668.45, 4680.57, 4650.27), sort_keys=True), encoding="utf-8")
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": "2026-05-03T16:30:00+00:00",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "ob_retest",
        "final_outcome_at_log": "REJECTED_GATE3_CIRCUIT_BREAKER",
        "source_file": str(first),
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 4668.45,
            "stop_loss": 4681.54,
            "take_profit_1": 4649.82,
        },
    }
    issues: list[dict] = []

    coverage = audit_trade_record_candidate_coverage(
        root,
        {candidate_id: candidate},
        issues,
        candidate_rows_all=[candidate],
    )

    assert issues == []
    assert coverage["matched_candidate_shadow_rows"] == 1
    assert coverage["value_mismatches"] == []
    assert coverage["documented_candidate_id_collisions"] == [
        {
            "candidate_id": candidate_id,
            "source_files": [str(first), str(second)],
            "reason": "multiple trade-record files share one M15 candidate_id; exact source_file shadow row required for value comparison",
        }
    ]


def test_trade_record_candidate_coverage_uses_m5_refined_effective_geometry(tmp_path):
    root = tmp_path
    records_root = root / "knowledge_base" / "trade_records" / "NAS100"
    records_root.mkdir(parents=True, exist_ok=True)
    trade_record = records_root / "2026-05-08_london_0715.json"
    trade_record.write_text(
        json.dumps(
            {
                "metadata": {
                    "symbol": "NAS100",
                    "kill_zone": "london",
                    "candle_close_utc": "2026-05-08T07:15:00+00:00",
                },
                "decision_pipeline": {
                    "ai_decision": "CANDIDATE",
                    "ai_direction": "LONG",
                    "ai_framework": "ob_retest",
                    "final_outcome": "REJECTED_GATE1_SAFETY",
                },
                "ai_response": {
                    "decision": "CANDIDATE",
                    "framework": "ob_retest",
                    "trade_parameters": {
                        "direction": "LONG",
                        "entry_price": 28663.7,
                        "stop_loss": 28576.9,
                        "take_profit_1": 28781.7,
                    },
                },
                "instrumentation": {
                    "m5_refinement_details": {
                        "applied": True,
                        "overrides": {
                            "entry_price": 28663.7,
                            "stop_loss": 28582.4,
                            "take_profit_1": 28773.5,
                        },
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    candidate_id = "NAS100_2026-05-08T07:15:00+00:00"
    candidate = {
        "candidate_id": candidate_id,
        "decision_time_utc": "2026-05-08T07:15:00+00:00",
        "symbol": "NAS100",
        "side": "LONG",
        "framework": "ob_retest",
        "final_outcome_at_log": "REJECTED_GATE1_SAFETY",
        "source_file": str(trade_record),
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 28663.7,
            "stop_loss": 28582.4,
            "take_profit_1": 28773.5,
        },
    }
    issues: list[dict] = []

    coverage = audit_trade_record_candidate_coverage(
        root,
        {candidate_id: candidate},
        issues,
        candidate_rows_all=[candidate],
    )

    assert issues == []
    assert coverage["matched_candidate_shadow_rows"] == 1
    assert coverage["value_mismatches"] == []


def test_trade_record_candidate_missing_from_shadow_is_action_required(tmp_path):
    _base_logs(tmp_path)
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
                    "final_outcome": "REJECTED_GATE1_SAFETY",
                },
                "ai_response": {
                    "decision": "CANDIDATE",
                    "framework": "ob_retest",
                    "trade_parameters": {
                        "direction": "LONG",
                        "entry_price": 27446.2,
                        "stop_loss": 27389.2,
                        "take_profit_1": 27531.7,
                    },
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = build_report(tmp_path)

    assert report["status"] == "ACTION_REQUIRED"
    assert report["trade_record_candidate_coverage"]["missing_candidate_shadow_rows"] == [
        "NAS100_2026-05-04T13:15:00+00:00"
    ]
    assert any(issue["code"] == "MISSING_TRADE_RECORD_CANDIDATE_SHADOW" for issue in report["issues"])
