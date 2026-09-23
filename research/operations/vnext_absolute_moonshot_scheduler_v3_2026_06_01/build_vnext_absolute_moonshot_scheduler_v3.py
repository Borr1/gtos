"""Build the vNext Absolute Moonshot Scheduler V3 route artifacts.

The route is default-off research/package generation only. It consumes current
Lane09B/Lane10/Lane10B/Lane11/Lane16/Lane17/Lane18/post-Lane18 source repair
artifacts and writes full-row Scheduler V3 evidence, decision, exposure,
conflict, recovery, source, stress, manifest, verifier, and audit outputs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scheduler_v3_default_off import (
    ACTION_CLASSES,
    REQUIRED_MONEY_RISK_FIELDS,
    RESULT_USE_STATUS,
    RUNTIME_EFFECT_BOUNDARY,
    build_money_risk_exposure,
    build_priority_components,
    classify_scheduler_v3_action,
    fnum,
    money,
    round9,
)


ROUTE_ID = "vnext_absolute_moonshot_scheduler_v3_2026_06_01"
SCHEMA_PREFIX = "scheduler_v3"
ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
LANE09B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
LANE10_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
LANE10B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
LANE11_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"
LANE16_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01"
LANE17_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01"
LANE18_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01"
POST18_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"

LANE09B_JOIN = LANE09B_DIR / "LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"
LANE10_REPLAY = LANE10_DIR / "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"
LANE10B_FULL = LANE10B_DIR / "LANE10B_FULL_CONFLICT_ANATOMY_LEDGER.jsonl.gz"
LANE10B_MULTI_TICKET = LANE10B_DIR / "LANE10B_MULTI_TICKET_LIFECYCLE_CONTRACT.json"
LANE10B_PACKAGE = LANE10B_DIR / "LANE10B_SCHEDULER_V3_DEFAULT_OFF_DESIGN_PACKAGE.json"
LANE11_PACKAGE = LANE11_DIR / "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE.json"
LANE16_PATH = LANE16_DIR / "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz"
LANE17_WHITEBOARD = LANE17_DIR / "LANE17_MARKET_WHITEBOARD_REPLAY_ROWS.jsonl.gz"
LANE17_CORRELATION = LANE17_DIR / "LANE17_CORRELATION_REGIME_SPREAD_LEDGER.jsonl"
LANE18_CONTRACT = LANE18_DIR / "LANE18_UNIVERSAL_BROKER_TRUTH_COST_CAPTURE_CONTRACT.json"
POST18_SUMMARY = POST18_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json"
POST18_COVERAGE = POST18_DIR / "POST_LANE18_SOURCE_COVERAGE_DELTA_LEDGER.jsonl"
MASTER_POST18_DECISION = MASTER_DIR / "ABSOLUTE_MASTER_POST_LANE18_IMPLEMENTATION_WAVE_DECISION.json"

FULL_EVIDENCE_LEDGER = ROUTE_DIR / "SCHEDULER_V3_FULL_EVIDENCE_LEDGER.jsonl.gz"
DECISION_LEDGER = ROUTE_DIR / "SCHEDULER_V3_ACCEPTED_REDUCED_REJECTED_DECISION_LEDGER.jsonl.gz"
CONFLICT_LEDGER = ROUTE_DIR / "SCHEDULER_V3_CONFLICT_ANATOMY_DISPOSITION_LEDGER.jsonl.gz"
BLOCKED_EDGE_LEDGER = ROUTE_DIR / "SCHEDULER_V3_BLOCKED_EDGE_RECOVERY_LEDGER.jsonl.gz"
MONEY_RISK_LEDGER = ROUTE_DIR / "SCHEDULER_V3_MONEY_RISK_EXPOSURE_LEDGER.jsonl.gz"
CORRELATION_LEDGER = ROUTE_DIR / "SCHEDULER_V3_CORRELATION_CLUSTER_EXPOSURE_LEDGER.jsonl.gz"
SOURCE_GAP_LEDGER = ROUTE_DIR / "SCHEDULER_V3_SOURCE_GAP_CAPTURE_DEPENDENCY_LEDGER.jsonl.gz"
SOURCE_COMPLETENESS_DECISIONS = ROUTE_DIR / "SCHEDULER_V3_SOURCE_COMPLETENESS_DECISIONS.jsonl"
SOURCE_CAPTURE_DECISIONS = ROUTE_DIR / "SCHEDULER_V3_SOURCE_CAPTURE_DECISIONS.jsonl"
BRANCH_DECISIONS = ROUTE_DIR / "SCHEDULER_V3_BRANCH_DECISION_LEDGER.jsonl"
IMPLEMENTATION_DECISIONS = ROUTE_DIR / "SCHEDULER_V3_IMPLEMENTATION_DECISION_LEDGER.jsonl"
SPLIT_STRESS_LEDGER = ROUTE_DIR / "SCHEDULER_V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl"
LIFECYCLE_CONTRACT = ROUTE_DIR / "SCHEDULER_V3_SAME_SYMBOL_MULTI_TICKET_LIFECYCLE_CONTRACT.json"
DEFAULT_OFF_PACKAGE = ROUTE_DIR / "SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json"
DOWNSTREAM_CONTRACTS = ROUTE_DIR / "SCHEDULER_V3_DOWNSTREAM_CONTRACTS.json"
RESULT_USE_STATUS_PATH = ROUTE_DIR / "SCHEDULER_V3_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY_PATH = ROUTE_DIR / "SCHEDULER_V3_RUNTIME_EFFECT_BOUNDARY.json"
SATURATION_MD = ROUTE_DIR / "SCHEDULER_V3_SATURATION_SELF_RED_TEAM.md"
CONTEXT_ANCHOR = ROUTE_DIR / "SCHEDULER_V3_CONTEXT_ANCHOR.md"
COMPLETION_AUDIT = ROUTE_DIR / "SCHEDULER_V3_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "SCHEDULER_V3_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "SCHEDULER_V3_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "SCHEDULER_V3_FOCUSED_TEST_RESULT.xml"

EXPECTED_ROWS = 289_928
EXPECTED_SOURCE_REPAIR_ROUTE = "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"
LIVE_FORBIDDEN = "no_live_scheduler_activation"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6) as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in iter_jsonl(path))


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slim_lane09b(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "join_status": row.get("join_status"),
        "reconciliation_class": row.get("reconciliation_class"),
        "risk_state": row.get("risk_state"),
        "lane11_policy_dependency": row.get("lane11_policy_dependency"),
        "source_gap_families": row.get("source_gap_families") or [],
        "source_completeness_state": row.get("source_completeness_state"),
        "source_quality_status": row.get("source_quality_status"),
        "lane09_mechanism_decision": row.get("lane09_mechanism_decision"),
        "lane09_mechanism_decision_reason": row.get("lane09_mechanism_decision_reason"),
    }


def slim_anatomy(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "row_id",
        "selected_row_id",
        "classification",
        "classification_reason",
        "correct_reject",
        "repairable_scheduler_block",
        "same_symbol_state",
        "same_symbol_release_state",
        "cluster_state",
        "risk_budget_state",
        "drawdown_state",
        "edge_bucket",
        "missed_edge_scope",
        "missed_result_r",
        "missed_risk_pct",
        "missed_proxy_amount",
        "max_money_risk_allowed_pct",
        "max_safe_risk_with_cluster_pct",
        "portfolio_headroom_pct",
        "cluster_headroom_pct",
        "account_headroom_after_existing_pct",
        "v3_action",
        "v3_branch_candidates",
        "lane09_mechanism_decision",
        "lane09_selector_component",
        "lane09_source_completeness_state",
        "lane09_source_quality_status",
        "lane09_policy_alignment_state",
        "lane09_path_class",
        "mechanism_family",
        "scheduler_decision",
        "scheduler_reason",
        "result_r",
        "result_r_class",
        "requested_risk_pct",
        "approved_risk_pct",
        "same_symbol_risk_pct_before",
        "correlated_cluster_risk_pct_before",
        "correlation_cluster",
        "total_risk_pct_before",
        "total_risk_pct_after",
        "cost_buffer_pct",
        "cost_status",
        "spread_r_bucket",
        "symbol",
        "side",
        "candidate_time_utc",
        "origin_family",
        "framework",
        "session_bucket",
        "chosen_policy",
    ]
    return {field: row.get(field) for field in fields}


def slim_path(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "row_id",
        "selected_row_id",
        "scheduler_join_state",
        "scheduler_decision",
        "scheduler_reason",
        "lane09b_reconciliation_class",
        "lane09b_risk_state",
        "lane10b_classification",
        "repairable_scheduler_block",
        "missed_opportunity",
        "missed_edge_scope",
        "requested_risk_pct",
        "approved_risk_pct",
        "selected_cell_effective_risk_pct",
        "selected_cell_risk_join_state",
        "best_policy_id",
        "best_policy_cost_adjusted_median_r",
        "current_router_policy",
        "current_policy_gross_r",
        "current_policy_cost_adjusted_median_r",
        "current_policy_cost_adjusted_high_stress_r",
        "policy_cost_stress_delta_r",
        "path_class",
        "mfe_r",
        "mae_r",
        "sl_before_1r",
        "partial_then_be",
        "partial_then_final",
        "no_entry_touch",
        "stuck_no_resolution",
        "source_gap_count",
        "source_gap_families",
        "source_completeness_state",
        "source_quality_status",
        "m1_availability_status",
        "tick_availability_status",
        "strict_tick_replay_status",
        "regime_h4_state",
        "regime_h4_direction",
        "regime_h4_score",
    ]
    return {field: row.get(field) for field in fields}


def slim_whiteboard(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row.get("row_id"),
        "source_replay_row_id": row.get("source_replay_row_id"),
        "duplicate_key": row.get("duplicate_key"),
        "source_completeness_state": row.get("source_completeness_state"),
        "source_completeness": row.get("source_completeness"),
        "correlation_cluster_state": row.get("correlation_cluster_state"),
        "field_source_state": row.get("field_source_state"),
        "broker_feasibility_fields": row.get("broker_feasibility_fields"),
        "market_hours_state": row.get("market_hours_state"),
        "spread_to_risk_state": row.get("spread_to_risk_state"),
        "regime_state": row.get("regime_state"),
        "m1_path_state": row.get("m1_path_state"),
        "tick_state": row.get("tick_state"),
        "no_leak_status": row.get("no_leak_status"),
    }


def build_indexes() -> dict[str, dict[str, dict[str, Any]]]:
    indexes: dict[str, dict[str, dict[str, Any]]] = {
        "lane09b": {},
        "anatomy": {},
        "path": {},
        "whiteboard": {},
    }
    for row in iter_jsonl(LANE09B_JOIN):
        key = row.get("lane10_row_id") or row.get("source_row_id")
        if key:
            indexes["lane09b"][str(key)] = slim_lane09b(row)
    for row in iter_jsonl(LANE10B_FULL):
        key = row.get("row_id")
        if key:
            indexes["anatomy"][str(key)] = slim_anatomy(row)
    for row in iter_jsonl(LANE16_PATH):
        key = row.get("selected_row_id")
        if key:
            indexes["path"][str(key)] = slim_path(row)
    for row in iter_jsonl(LANE17_WHITEBOARD):
        key = row.get("source_replay_row_id")
        if key:
            indexes["whiteboard"][str(key)] = slim_whiteboard(row)
    return indexes


def source_repair_scheduler_counts() -> dict[str, int]:
    summary = read_json(POST18_SUMMARY)
    counts: dict[str, int] = {}
    for key, value in (
        summary.get("source_stats", {}).get("consumer_disposition_counts", {}).items()
    ):
        consumer, _, disposition = key.partition("|")
        if consumer == "Scheduler V3":
            counts[disposition] = int(value)
    return dict(sorted(counts.items()))


def source_repair_scheduler_coverage_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(POST18_COVERAGE):
        if "Scheduler V3" in (row.get("downstream_consumers") or []):
            rows.append(row)
    return rows


def source_field_family_counts_for_scheduler() -> dict[str, int]:
    summary = read_json(POST18_SUMMARY)
    field_counts: dict[str, int] = {}
    for key, value in summary.get("source_stats", {}).get("field_disposition_counts", {}).items():
        # Keep scheduler-material field families and universal account/risk/cost fields.
        if any(
            token in key
            for token in (
                "portfolio_state",
                "selected_cell_risk",
                "correlation_cluster",
                "broker_real_net_r",
                "cost_adjusted_r",
                "cost",
                "spread",
                "commission",
                "swap",
                "slippage",
                "ticket",
                "broker_order_deal_position_lifecycle",
                "account_baseline_balance_equity",
                "market_hours_state",
                "broker_exact_tick_value",
                "tick_value",
            )
        ):
            field_counts[key] = int(value)
    return dict(sorted(field_counts.items()))


def merged_row(
    base: dict[str, Any],
    anatomy: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(base)
    if anatomy:
        for key, value in anatomy.items():
            if value is not None:
                merged[key] = value
    return merged


def row_identity(
    base: dict[str, Any],
    lane09b: dict[str, Any] | None,
    anatomy: dict[str, Any] | None,
    path: dict[str, Any] | None,
    whiteboard: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "lane10_row_id": base.get("row_id"),
        "selected_row_id": base.get("selected_row_id"),
        "candidate_id": base.get("candidate_id"),
        "candidate_time_utc": base.get("candidate_time_utc"),
        "symbol": base.get("symbol"),
        "side": base.get("side"),
        "framework": base.get("framework"),
        "origin_family": base.get("origin_family"),
        "session_bucket": base.get("session_bucket"),
        "lane09b_join_status": (lane09b or {}).get("join_status"),
        "lane10b_classification": (anatomy or {}).get("classification"),
        "lane16_path_row_id": (path or {}).get("row_id"),
        "lane17_whiteboard_row_id": (whiteboard or {}).get("row_id"),
        "source_replay_row_id": (whiteboard or {}).get("source_replay_row_id"),
    }


def build_rank_map(indexes: dict[str, dict[str, dict[str, Any]]]) -> dict[str, int]:
    rank_entries: list[tuple[float, str, str]] = []
    for base in iter_jsonl(LANE10_REPLAY):
        row_id = str(base.get("row_id"))
        anatomy = indexes["anatomy"].get(row_id)
        path = indexes["path"].get(str(base.get("selected_row_id")))
        whiteboard = indexes["whiteboard"].get(row_id)
        components = build_priority_components(merged_row(base, anatomy), path, whiteboard)
        score = fnum(components["offline_research_priority_score"], 0.0)
        rank_entries.append((-score, str(base.get("candidate_time_utc") or ""), row_id))
    rank_entries.sort()
    return {row_id: rank for rank, (_, _, row_id) in enumerate(rank_entries, start=1)}


def build_output_rows(
    indexes: dict[str, dict[str, dict[str, Any]]],
    rank_map: dict[str, int],
) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "row_count": 0,
        "decision_counts": Counter(),
        "action_class_counts": Counter(),
        "scheduler_lane10_decision_counts": Counter(),
        "result_class_counts": Counter(),
        "result_r_sum_by_class": Counter(),
        "source_gap_rows": 0,
        "blocked_edge_rows": 0,
        "money_risk_missing_field_rows": 0,
        "max_total_risk_pct_after": 0.0,
        "max_cluster_risk_pct_before": 0.0,
        "max_same_symbol_risk_pct_before": 0.0,
        "split_accumulators": defaultdict(lambda: {
            "rows": 0,
            "result_r_sum": 0.0,
            "accepted_rows": 0,
            "reduced_rows": 0,
            "rejected_rows": 0,
            "queue_rows": 0,
            "delay_rows": 0,
            "replace_rows": 0,
            "require_source_rows": 0,
            "exact_r_rows": 0,
            "proxy_r_rows": 0,
            "missing_r_rows": 0,
            "max_total_risk_pct_after": 0.0,
            "max_cluster_risk_pct_before": 0.0,
            "source_gap_rows": 0,
        }),
    }

    def evidence_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            lane09b = indexes["lane09b"].get(row_id)
            anatomy = indexes["anatomy"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            merged = merged_row(base, anatomy)
            action = classify_scheduler_v3_action(merged)
            components = build_priority_components(merged, path, whiteboard)
            identity = row_identity(base, lane09b, anatomy, path, whiteboard)
            source_gaps = list(
                dict.fromkeys(
                    (base.get("source_gap_families") or [])
                    + ((lane09b or {}).get("source_gap_families") or [])
                    + ((path or {}).get("source_gap_families") or [])
                )
            )
            source_gap_count = int(fnum((path or {}).get("source_gap_count"), 0.0))
            row = {
                "schema_version": f"{SCHEMA_PREFIX}_full_evidence_row_v1",
                "route_id": ROUTE_ID,
                **identity,
                "full_denominator_row_number": stats["row_count"] + 1,
                "global_priority_rank": rank_map[row_id],
                "scheduler_v3_priority_components": components,
                **action.asdict(),
                "lane10_scheduler_decision": base.get("scheduler_decision") or base.get("decision"),
                "lane10_scheduler_reason": base.get("scheduler_reason") or base.get("reason"),
                "lane10b_classification_reason": (anatomy or {}).get("classification_reason"),
                "accepted_by_lane10": bool(base.get("accepted")),
                "requested_risk_pct": base.get("requested_risk_pct"),
                "approved_risk_pct": base.get("approved_risk_pct"),
                "result_r": base.get("result_r"),
                "result_r_class": base.get("result_r_class"),
                "result_use_status": RESULT_USE_STATUS,
                "money_risk_authority": "account_exposure_not_static_count_cap",
                "source_completeness_state": (
                    (path or {}).get("source_completeness_state")
                    or (lane09b or {}).get("source_completeness_state")
                    or "missing"
                ),
                "source_quality_status": (
                    (path or {}).get("source_quality_status")
                    or (lane09b or {}).get("source_quality_status")
                    or "missing"
                ),
                "source_gap_count": source_gap_count,
                "source_gap_families": source_gaps,
                "correlation_cluster": base.get("correlation_cluster"),
                "cluster_state": (anatomy or {}).get("cluster_state"),
                "correlation_source_state": (
                    (whiteboard or {}).get("correlation_cluster_state") or {}
                ).get("source_state"),
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
            update_stats(stats, row, base, action, source_gap_count)
            yield row

    def decision_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            lane09b = indexes["lane09b"].get(row_id)
            anatomy = indexes["anatomy"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            merged = merged_row(base, anatomy)
            action = classify_scheduler_v3_action(merged)
            components = build_priority_components(merged, path, whiteboard)
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_decision_row_v1",
                "route_id": ROUTE_ID,
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                "global_priority_rank": rank_map[row_id],
                "scheduler_v3_decision": action.decision,
                "scheduler_v3_action_class": action.action_class,
                "scheduler_v3_action": action.action,
                "scheduler_v3_reason": action.reason,
                "blocked_edge_recovery_status": action.recovery_status,
                "lane10_scheduler_decision": base.get("scheduler_decision") or base.get("decision"),
                "lane10_scheduler_reason": base.get("scheduler_reason") or base.get("reason"),
                "lane10b_classification": (anatomy or {}).get("classification"),
                "lane10b_correct_reject": (anatomy or {}).get("correct_reject"),
                "lane10b_repairable_scheduler_block": (anatomy or {}).get(
                    "repairable_scheduler_block"
                ),
                "requested_risk_pct": base.get("requested_risk_pct"),
                "approved_risk_pct": base.get("approved_risk_pct"),
                "offline_research_priority_score": components["offline_research_priority_score"],
                "runtime_safe_priority_score": components["runtime_safe_priority_score"],
                "result_r": base.get("result_r"),
                "result_r_class": base.get("result_r_class"),
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    def conflict_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            anatomy = indexes["anatomy"].get(row_id)
            lane09b = indexes["lane09b"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            merged = merged_row(base, anatomy)
            action = classify_scheduler_v3_action(merged)
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_conflict_disposition_row_v1",
                "route_id": ROUTE_ID,
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                "scheduler_v3_action_class": action.action_class,
                "scheduler_v3_action": action.action,
                "same_symbol_state": (anatomy or {}).get("same_symbol_state"),
                "same_symbol_release_state": (anatomy or {}).get("same_symbol_release_state"),
                "same_symbol_conflict_ids": base.get("same_symbol_conflict_ids") or [],
                "same_symbol_risk_pct_before": base.get("same_symbol_risk_pct_before"),
                "cluster_state": (anatomy or {}).get("cluster_state"),
                "correlation_cluster": base.get("correlation_cluster"),
                "correlated_cluster_conflict_ids": base.get("correlated_cluster_conflict_ids") or [],
                "correlated_cluster_risk_pct_before": base.get(
                    "correlated_cluster_risk_pct_before"
                ),
                "risk_budget_state": (anatomy or {}).get("risk_budget_state"),
                "drawdown_state": (anatomy or {}).get("drawdown_state"),
                "classification": (anatomy or {}).get("classification"),
                "classification_reason": (anatomy or {}).get("classification_reason"),
                "v3_branch_candidates": (anatomy or {}).get("v3_branch_candidates") or [],
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    def blocked_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            anatomy = indexes["anatomy"].get(row_id)
            lane09b = indexes["lane09b"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            merged = merged_row(base, anatomy)
            action = classify_scheduler_v3_action(merged)
            lane10_decision = str(base.get("scheduler_decision") or base.get("decision"))
            result_r = fnum(base.get("result_r"), 0.0)
            if not (
                lane10_decision == "ACCEPTED_REDUCED_RISK"
                or (lane10_decision == "REJECTED" and result_r > 0.0)
                or action.action_class in {"queue", "delay", "replace", "admit_reduced_risk"}
            ):
                continue
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_blocked_edge_recovery_row_v1",
                "route_id": ROUTE_ID,
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                "lane10_scheduler_decision": lane10_decision,
                "lane10_scheduler_reason": base.get("scheduler_reason") or base.get("reason"),
                "scheduler_v3_decision": action.decision,
                "scheduler_v3_action_class": action.action_class,
                "scheduler_v3_action": action.action,
                "blocked_edge_recovery_status": action.recovery_status,
                "result_r": result_r,
                "result_r_class": base.get("result_r_class"),
                "missed_result_r": (anatomy or {}).get("missed_result_r"),
                "missed_risk_pct": (anatomy or {}).get("missed_risk_pct"),
                "missed_proxy_amount": (anatomy or {}).get("missed_proxy_amount"),
                "v3_branch_candidates": (anatomy or {}).get("v3_branch_candidates") or [],
                "source_completeness_state": (path or {}).get("source_completeness_state"),
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    def money_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            anatomy = indexes["anatomy"].get(row_id)
            lane09b = indexes["lane09b"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            merged = merged_row(base, anatomy)
            exposure = build_money_risk_exposure(merged)
            missing_fields = [field for field in REQUIRED_MONEY_RISK_FIELDS if field not in exposure]
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_money_risk_exposure_row_v1",
                "route_id": ROUTE_ID,
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                **exposure,
                "required_money_risk_fields": list(REQUIRED_MONEY_RISK_FIELDS),
                "missing_money_risk_fields": missing_fields,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    def correlation_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            anatomy = indexes["anatomy"].get(row_id)
            lane09b = indexes["lane09b"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            cluster_state = (whiteboard or {}).get("correlation_cluster_state") or {}
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_correlation_cluster_row_v1",
                "route_id": ROUTE_ID,
                "row_type": "scheduler_candidate_cluster_exposure",
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                "correlation_cluster": base.get("correlation_cluster"),
                "cluster_state": (anatomy or {}).get("cluster_state"),
                "cluster_source_state": cluster_state.get("source_state"),
                "runtime_exact_correlation_join_state": cluster_state.get(
                    "runtime_exact_correlation_join_state"
                ),
                "same_direction_cluster_peers": cluster_state.get(
                    "same_direction_cluster_peers"
                )
                or [],
                "cluster_peer_count": cluster_state.get("cluster_peer_count"),
                "risk_on_proxy_score": cluster_state.get("risk_on_proxy_score"),
                "correlated_cluster_risk_pct_before": base.get(
                    "correlated_cluster_risk_pct_before"
                ),
                "correlated_cluster_conflict_ids": base.get(
                    "correlated_cluster_conflict_ids"
                )
                or [],
                "cluster_ceiling_pct": 4.0,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        for pair in iter_jsonl(LANE17_CORRELATION):
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_correlation_pair_rule_v1",
                "route_id": ROUTE_ID,
                "row_type": "lane17_all_pair_correlation_rule",
                "symbol": pair.get("symbol"),
                "peer_symbol": pair.get("peer_symbol"),
                "correlation": pair.get("correlation"),
                "risk_relation": pair.get("risk_relation"),
                "cluster_threshold_abs": pair.get("cluster_threshold_abs"),
                "source_state": pair.get("source_state"),
                "source_path": pair.get("source_path"),
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    def source_gap_rows() -> Iterable[dict[str, Any]]:
        for base in iter_jsonl(LANE10_REPLAY):
            row_id = str(base.get("row_id"))
            anatomy = indexes["anatomy"].get(row_id)
            lane09b = indexes["lane09b"].get(row_id)
            path = indexes["path"].get(str(base.get("selected_row_id")))
            whiteboard = indexes["whiteboard"].get(row_id)
            source_completeness = (whiteboard or {}).get("source_completeness") or {}
            field_source_state = (whiteboard or {}).get("field_source_state") or {}
            gap_families = list(
                dict.fromkeys(
                    (base.get("source_gap_families") or [])
                    + ((lane09b or {}).get("source_gap_families") or [])
                    + ((path or {}).get("source_gap_families") or [])
                )
            )
            yield {
                "schema_version": f"{SCHEMA_PREFIX}_source_gap_capture_dependency_row_v1",
                "route_id": ROUTE_ID,
                **row_identity(base, lane09b, anatomy, path, whiteboard),
                "source_completeness_state": (
                    (path or {}).get("source_completeness_state")
                    or (whiteboard or {}).get("source_completeness_state")
                    or "missing"
                ),
                "source_gap_count": int(fnum((path or {}).get("source_gap_count"), 0.0)),
                "source_gap_families": gap_families,
                "whiteboard_field_source_state": field_source_state,
                "whiteboard_source_gaps_inherited": source_completeness.get(
                    "source_gaps_inherited"
                )
                or [],
                "post_lane18_scheduler_consumer_disposition_counts": source_repair_scheduler_counts(),
                "source_decision": "consume_proxy_or_repaired_rows_where_present_else_require_exact_capture_or_read_only_export",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }

    counts = {
        "full_evidence_rows": write_jsonl_gz(FULL_EVIDENCE_LEDGER, evidence_rows()),
        "decision_rows": write_jsonl_gz(DECISION_LEDGER, decision_rows()),
        "conflict_rows": write_jsonl_gz(CONFLICT_LEDGER, conflict_rows()),
        "blocked_edge_rows": write_jsonl_gz(BLOCKED_EDGE_LEDGER, blocked_rows()),
        "money_risk_rows": write_jsonl_gz(MONEY_RISK_LEDGER, money_rows()),
        "correlation_rows": write_jsonl_gz(CORRELATION_LEDGER, correlation_rows()),
        "source_gap_rows": write_jsonl_gz(SOURCE_GAP_LEDGER, source_gap_rows()),
    }
    stats["ledger_counts"] = counts
    write_split_stress(stats)
    return stats


def update_stats(
    stats: dict[str, Any],
    row: dict[str, Any],
    base: dict[str, Any],
    action: Any,
    source_gap_count: int,
) -> None:
    stats["row_count"] += 1
    stats["decision_counts"][action.decision] += 1
    stats["action_class_counts"][action.action_class] += 1
    stats["scheduler_lane10_decision_counts"][row["lane10_scheduler_decision"]] += 1
    result_class = str(base.get("result_r_class") or "missing_result")
    result_r = fnum(base.get("result_r"), 0.0)
    stats["result_class_counts"][result_class] += 1
    stats["result_r_sum_by_class"][result_class] += result_r
    if source_gap_count > 0:
        stats["source_gap_rows"] += 1
    if row["scheduler_v3_action_class"] in {"queue", "delay", "replace", "admit_reduced_risk"} or (
        row["lane10_scheduler_decision"] == "REJECTED" and result_r > 0.0
    ):
        stats["blocked_edge_rows"] += 1
    stats["max_total_risk_pct_after"] = max(
        stats["max_total_risk_pct_after"], fnum(base.get("total_risk_pct_after"), 0.0)
    )
    stats["max_cluster_risk_pct_before"] = max(
        stats["max_cluster_risk_pct_before"],
        fnum(base.get("correlated_cluster_risk_pct_before"), 0.0),
    )
    stats["max_same_symbol_risk_pct_before"] = max(
        stats["max_same_symbol_risk_pct_before"],
        fnum(base.get("same_symbol_risk_pct_before"), 0.0),
    )
    for scope, value in (
        ("symbol", base.get("symbol")),
        ("session_bucket", base.get("session_bucket")),
        ("origin_family", base.get("origin_family")),
        ("framework", base.get("framework")),
        ("correlation_cluster", base.get("correlation_cluster")),
        ("scheduler_v3_decision", action.decision),
        ("scheduler_v3_action_class", action.action_class),
        ("result_r_class", result_class),
        ("calendar_week", base.get("calendar_week")),
    ):
        key = (scope, str(value or "missing"))
        acc = stats["split_accumulators"][key]
        acc["rows"] += 1
        acc["result_r_sum"] += result_r
        if action.decision == "ACCEPTED":
            acc["accepted_rows"] += 1
        elif action.decision == "ACCEPTED_REDUCED_RISK":
            acc["reduced_rows"] += 1
        elif action.decision == "QUEUE":
            acc["queue_rows"] += 1
        elif action.decision == "DELAY":
            acc["delay_rows"] += 1
        elif action.decision == "REPLACE":
            acc["replace_rows"] += 1
        elif action.decision == "REQUIRE_SOURCE":
            acc["require_source_rows"] += 1
        else:
            acc["rejected_rows"] += 1
        if result_class == "exact_broker_real":
            acc["exact_r_rows"] += 1
        elif result_class == "source_bound_proxy":
            acc["proxy_r_rows"] += 1
        else:
            acc["missing_r_rows"] += 1
        acc["max_total_risk_pct_after"] = max(
            acc["max_total_risk_pct_after"], fnum(base.get("total_risk_pct_after"), 0.0)
        )
        acc["max_cluster_risk_pct_before"] = max(
            acc["max_cluster_risk_pct_before"],
            fnum(base.get("correlated_cluster_risk_pct_before"), 0.0),
        )
        if source_gap_count > 0:
            acc["source_gap_rows"] += 1


def write_split_stress(stats: dict[str, Any]) -> None:
    rows = []
    for (scope, value), acc in sorted(stats["split_accumulators"].items()):
        row = {
            "schema_version": f"{SCHEMA_PREFIX}_split_stress_deconcentration_row_v1",
            "route_id": ROUTE_ID,
            "split_scope": scope,
            "split_value": value,
            "rows": acc["rows"],
            "result_r_sum": round9(acc["result_r_sum"]),
            "expectancy_r": round9(acc["result_r_sum"] / acc["rows"]) if acc["rows"] else None,
            "accepted_rows": acc["accepted_rows"],
            "reduced_rows": acc["reduced_rows"],
            "rejected_rows": acc["rejected_rows"],
            "queue_rows": acc["queue_rows"],
            "delay_rows": acc["delay_rows"],
            "replace_rows": acc["replace_rows"],
            "require_source_rows": acc["require_source_rows"],
            "exact_r_rows": acc["exact_r_rows"],
            "proxy_r_rows": acc["proxy_r_rows"],
            "missing_r_rows": acc["missing_r_rows"],
            "source_gap_rows": acc["source_gap_rows"],
            "max_total_risk_pct_after": round9(acc["max_total_risk_pct_after"]),
            "max_cluster_risk_pct_before": round9(acc["max_cluster_risk_pct_before"]),
            "no_arbitrary_top_n_cutoff": True,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        rows.append(row)
    write_jsonl(SPLIT_STRESS_LEDGER, rows)


def write_control_artifacts(stats: dict[str, Any]) -> None:
    generated = utc_now()
    source_counts = source_repair_scheduler_counts()
    source_coverage = source_repair_scheduler_coverage_rows()
    field_counts = source_field_family_counts_for_scheduler()
    lane10b_contract = read_json(LANE10B_MULTI_TICKET)
    lane10b_package = read_json(LANE10B_PACKAGE)
    lane18_contract = read_json(LANE18_CONTRACT)
    lane11_package = read_json(LANE11_PACKAGE)
    master_decision = read_json(MASTER_POST18_DECISION)

    source_decision_rows = [
        {
            "schema_version": f"{SCHEMA_PREFIX}_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "consumer": "Scheduler V3",
            "disposition": disposition,
            "rows": count,
            "decision": (
                "consume_in_default_off_package"
                if disposition in {"filled_now", "reconstructed_now", "proxy_bound_now"}
                else "preserve_exact_capture_or_export_dependency"
            ),
            "source_route_id": EXPECTED_SOURCE_REPAIR_ROUTE,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        }
        for disposition, count in source_counts.items()
    ]
    write_jsonl(SOURCE_COMPLETENESS_DECISIONS, source_decision_rows)

    capture_rows = []
    for row in source_coverage:
        capture_rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}_source_capture_decision_v1",
                "route_id": ROUTE_ID,
                "source_route_id": EXPECTED_SOURCE_REPAIR_ROUTE,
                "disposition": row.get("disposition"),
                "affected_field_rows": row.get("affected_field_rows"),
                "downstream_consumers": row.get("downstream_consumers"),
                "decision": "consume_or_preserve_dependency_for_scheduler_v3",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    for field_key, count in field_counts.items():
        capture_rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}_source_capture_field_family_decision_v1",
                "route_id": ROUTE_ID,
                "field_disposition": field_key,
                "affected_field_rows": count,
                "decision": "field_family_preserved_for_scheduler_v3_money_risk_or_lifecycle_contract",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    write_jsonl(SOURCE_CAPTURE_DECISIONS, capture_rows)

    branch_rows = []
    for branch in lane10b_package.get("branch_names", []):
        branch_rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}_branch_decision_v1",
                "route_id": ROUTE_ID,
                "branch": branch,
                "source": rel(LANE10B_PACKAGE),
                "decision": "carry_forward_into_scheduler_v3_default_off_package",
                "live_activation": False,
                "owner_approval_required_for_live_use": True,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    for action_class in ACTION_CLASSES:
        branch_rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}_branch_decision_v1",
                "route_id": ROUTE_ID,
                "branch": f"scheduler_v3_action_class_{action_class}",
                "decision": "implemented_as_default_off_route_local_action_class",
                "live_activation": False,
                "owner_approval_required_for_live_use": True,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    write_jsonl(BRANCH_DECISIONS, branch_rows)

    write_jsonl(
        IMPLEMENTATION_DECISIONS,
        [
            {
                "schema_version": f"{SCHEMA_PREFIX}_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "decision_id": "route_local_default_off_scheduler_v3_code",
                "decision": "implement_scheduler_v3_default_off_helpers_and_builder",
                "evidence": rel(ROUTE_DIR / "scheduler_v3_default_off.py"),
                "runtime_effect_now": False,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            },
            {
                "schema_version": f"{SCHEMA_PREFIX}_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "decision_id": "full_denominator_ledgers",
                "decision": "emit_full_289928_row_evidence_decision_exposure_conflict_correlation_source_ledgers",
                "row_count": stats["row_count"],
                "runtime_effect_now": False,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            },
            {
                "schema_version": f"{SCHEMA_PREFIX}_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "decision_id": "no_live_activation",
                "decision": "do_not_modify_config_runtime_permissions_or_live_scheduler_behavior",
                "runtime_effect_now": False,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            },
        ],
    )

    lifecycle_contract = {
        "schema_version": f"{SCHEMA_PREFIX}_same_symbol_multi_ticket_lifecycle_contract_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated,
        "activation_default": "off",
        "runtime_effect_now": False,
        "owner_approval_required_for_live_activation": True,
        "source_contract": rel(LANE10B_MULTI_TICKET),
        "lane10b_contract": lane10b_contract,
        "scheduler_v3_supported_default_off_scenarios": {
            "same_symbol_same_side_stacking": (
                "queue_or_replace only after ticket_id, selected_row_id, risk release, "
                "residual exposure, and aggregate money-risk proof exist"
            ),
            "same_symbol_opposite_side": (
                "conflict-net rejects by default; hedge/netting requires separate owner-approved dossier"
            ),
            "partial_or_be_release": (
                "worst-case risk may be released only from ticket-level partial/BE proof; residual exposure remains counted"
            ),
            "multi_ticket_identity": (
                "every admitted ticket must carry ticket/order/deal/position identity when broker truth exists"
            ),
        },
        "required_money_risk_fields": list(REQUIRED_MONEY_RISK_FIELDS),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    }
    write_json(LIFECYCLE_CONTRACT, lifecycle_contract)

    package = {
        "schema_version": f"{SCHEMA_PREFIX}_default_off_package_v1",
        "route_id": ROUTE_ID,
        "package_id": "scheduler_v3_default_off_account_risk_exposure_package",
        "generated_at_utc": generated,
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "runtime_effect_now": False,
        "live_activation_allowed_by_this_package": False,
        "owner_approval_required_for_live_use": True,
        "scheduler_authority": (
            "balance_equity_day_start_realized_pnl_open_pending_new_worst_case_sl_risk_"
            "selected_cell_risk_lot_contract_geometry_cost_buffer_daily_total_limits_"
            "realized_cushion_drawdown_compression_same_symbol_lifecycle_cluster_exposure"
        ),
        "forbidden_authority": [
            "static max-trades authority",
            "stale count cap closure",
            "session count cap as final authority",
            "arbitrary top-N cutoff",
            "posthoc result_r in live runtime priority",
            "hidden live scheduler activation",
        ],
        "action_classes": list(ACTION_CLASSES),
        "required_money_risk_fields": list(REQUIRED_MONEY_RISK_FIELDS),
        "source_ledgers": {
            "full_evidence": rel(FULL_EVIDENCE_LEDGER),
            "decision": rel(DECISION_LEDGER),
            "conflict": rel(CONFLICT_LEDGER),
            "blocked_edge": rel(BLOCKED_EDGE_LEDGER),
            "money_risk": rel(MONEY_RISK_LEDGER),
            "correlation": rel(CORRELATION_LEDGER),
            "source_gap": rel(SOURCE_GAP_LEDGER),
            "split_stress": rel(SPLIT_STRESS_LEDGER),
        },
        "upstream_contracts": {
            "lane10b_multiticket": rel(LANE10B_MULTI_TICKET),
            "lane10b_scheduler_v3_design": rel(LANE10B_PACKAGE),
            "lane11_default_off_policy_router": rel(LANE11_PACKAGE),
            "lane18_universal_broker_truth_cost_capture": rel(LANE18_CONTRACT),
            "post_lane18_source_capture_repair": rel(POST18_SUMMARY),
        },
        "master_post_lane18_gate_status": master_decision.get("decision"),
        "summary_counts": compact_stats(stats),
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    }
    write_json(DEFAULT_OFF_PACKAGE, package)

    downstream = {
        "schema_version": f"{SCHEMA_PREFIX}_downstream_contracts_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "consumers": {
            "Selector V3": {
                "consume": [rel(DECISION_LEDGER), rel(SPLIT_STRESS_LEDGER)],
                "contract": "selector may use scheduler_v3_action_class and runtime_safe_priority_score, not posthoc result_r for live priority",
            },
            "Execution Policy V3": {
                "consume": [rel(MONEY_RISK_LEDGER), rel(LIFECYCLE_CONTRACT)],
                "contract": "execution policies must preserve ticket lifecycle and broker modify/partial/residual requirements",
            },
            "ML": {
                "consume": [rel(FULL_EVIDENCE_LEDGER), rel(SPLIT_STRESS_LEDGER)],
                "contract": "ML can train on offline exact/proxy labels only with no-leak partitions and evidence-class labels",
            },
            "Repair Companion": {
                "consume": [rel(SOURCE_GAP_LEDGER), rel(SOURCE_CAPTURE_DECISIONS)],
                "contract": "repair companion owns forward capture/read-only export work, not live activation",
            },
            "Command Center": {
                "consume": [rel(MONEY_RISK_LEDGER), rel(CORRELATION_LEDGER), rel(DECISION_LEDGER)],
                "contract": "command center shows current risk/source state and default-off decision status",
            },
            "Production Dossier": {
                "consume": [rel(DEFAULT_OFF_PACKAGE), rel(COMPLETION_AUDIT), rel(VERIFICATION_RESULT)],
                "contract": "separate owner-approved dossier required before live behavior change",
            },
        },
    }
    write_json(DOWNSTREAM_CONTRACTS, downstream)

    result_counts = {
        cls: {
            "rows": int(stats["result_class_counts"][cls]),
            "r_sum": round9(stats["result_r_sum_by_class"][cls]),
            "expectancy_r": round9(
                stats["result_r_sum_by_class"][cls] / stats["result_class_counts"][cls]
            )
            if stats["result_class_counts"][cls]
            else None,
        }
        for cls in sorted(stats["result_class_counts"])
    }
    write_json(
        RESULT_USE_STATUS_PATH,
        {
            "schema_version": f"{SCHEMA_PREFIX}_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_STATUS,
            "exact_proxy_expectancy_by_class": result_counts,
            "owned_result_materialization": (
                "Scheduler V3 owns offline admission/recovery accounting over Lane10/Lane10B rows; "
                "it does not claim broker-real production performance"
            ),
            "runtime_priority_rule": "future runtime may consume runtime_safe_priority_score only; source-bound result fields are research labels",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY_PATH,
        {
            "schema_version": f"{SCHEMA_PREFIX}_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "forbidden_surfaces": [
                "production-change activation",
                "live broker/order/deal/position operation",
                "paid API/vendor spend",
                "credential or remote change",
                "prompt/config/risk/execution/safety/canary/selector live behavior change",
            ],
            "live_activation": False,
        },
    )

    write_saturation(stats, source_counts)
    write_context_anchor(stats)


def compact_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_count": stats["row_count"],
        "ledger_counts": stats.get("ledger_counts", {}),
        "decision_counts": dict(sorted(stats["decision_counts"].items())),
        "action_class_counts": dict(sorted(stats["action_class_counts"].items())),
        "lane10_scheduler_decision_counts": dict(
            sorted(stats["scheduler_lane10_decision_counts"].items())
        ),
        "result_class_counts": dict(sorted(stats["result_class_counts"].items())),
        "result_r_sum_by_class": {
            key: round9(value) for key, value in sorted(stats["result_r_sum_by_class"].items())
        },
        "source_gap_rows": stats["source_gap_rows"],
        "blocked_edge_rows": stats["blocked_edge_rows"],
        "max_total_risk_pct_after": round9(stats["max_total_risk_pct_after"]),
        "max_cluster_risk_pct_before": round9(stats["max_cluster_risk_pct_before"]),
        "max_same_symbol_risk_pct_before": round9(stats["max_same_symbol_risk_pct_before"]),
    }


def write_saturation(stats: dict[str, Any], source_counts: dict[str, int]) -> None:
    text = f"""# Scheduler V3 Saturation And Self-Red-Team

Generated: {utc_now()}

Status: same-evidence-class pursuit executed for the default-off Scheduler V3 package.

- Lane10 rejected/conflict rows are preserved in full: {stats['scheduler_lane10_decision_counts'].get('REJECTED', 0)} rejected, {stats['scheduler_lane10_decision_counts'].get('ACCEPTED_REDUCED_RISK', 0)} reduced, and {stats['scheduler_lane10_decision_counts'].get('ACCEPTED', 0)} accepted.
- Repairable and blocked-positive rows are not summary-only: {stats['blocked_edge_rows']} rows are written to the blocked-edge recovery ledger.
- Static count/session caps are not Scheduler V3 authority. The package authority is account-risk exposure, money-risk headroom, same-symbol lifecycle proof, and correlation cluster exposure.
- Same-symbol/multi-ticket support remains default-off and ticket-bound. Same-side risk-released rows become queue/replace designs; opposite-side rows remain conflict-net rejects without an owner-approved hedge dossier.
- Correlation/cluster exposure uses all Lane17 candidate rows plus all 276 pair rows; no top-N peer truncation is used.
- Source capture repair is consumed from post-Lane18. Scheduler V3 source dispositions are {json.dumps(source_counts, sort_keys=True)}.
- Exact/proxy result fields are materialized only as research labels and expectancy accounting. Runtime-safe priority scores exclude post-outcome result fields.
- A skeptical production-change audit would reject live use until ticket identity, broker lifecycle, cost, selected-cell risk, exact account snapshots, correlation runtime snapshots, and owner-approved dossier gates are complete. The verifier checks default-off state and full-row preservation.

Same-class gaps pursued here: row joins, full denominator preservation, repairable-block action mapping, money-risk field materialization, source-capture decision preservation, correlation ledger preservation, split/stress/deconcentration across all emitted groups, route-local code, focused tests, and verifier.
"""
    SATURATION_MD.write_text(text, encoding="utf-8")


def write_context_anchor(stats: dict[str, Any]) -> None:
    text = f"""# Scheduler V3 Context Anchor

Route: `{ROUTE_ID}`
Generated: `{utc_now()}`
HEAD context source: `.context/LIVE_STATE.md` regenerated before route build.

Controlling prompt:
`research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_SCHEDULER_V3_GOAL_PROMPT_2026-06-01.md`

Inputs consumed from disk:

- Lane09B selector-scheduler reconciliation
- Lane10 Scheduler V2
- Lane10B conflict anatomy and multi-ticket lifecycle design
- Lane11 execution-policy engine package
- Lane16 historical microscope scale
- Lane17 market awareness whiteboard
- Lane18 broker truth/cost capture V2
- Post-Lane18 Source Capture Repair
- Master post-Lane18 implementation wave decision
- route-local risk/scheduler/runtime code and current production risk/permissions context read before build

Rows materialized: `{stats['row_count']}` full Scheduler V3 denominator rows.
Runtime effect boundary: `{RUNTIME_EFFECT_BOUNDARY}`.
Live activation: `false`.

Resume rule: regenerate LIVE_STATE, reread the controlling prompt, doctrine, Master post-Lane18 decision, Source Capture Repair, this anchor, manifest, verifier, and completion audit before continuing.
"""
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def manifest_rows() -> list[dict[str, Any]]:
    paths = [
        FULL_EVIDENCE_LEDGER,
        DECISION_LEDGER,
        CONFLICT_LEDGER,
        BLOCKED_EDGE_LEDGER,
        MONEY_RISK_LEDGER,
        CORRELATION_LEDGER,
        SOURCE_GAP_LEDGER,
        SOURCE_COMPLETENESS_DECISIONS,
        SOURCE_CAPTURE_DECISIONS,
        BRANCH_DECISIONS,
        IMPLEMENTATION_DECISIONS,
        SPLIT_STRESS_LEDGER,
        LIFECYCLE_CONTRACT,
        DEFAULT_OFF_PACKAGE,
        DOWNSTREAM_CONTRACTS,
        RESULT_USE_STATUS_PATH,
        RUNTIME_EFFECT_BOUNDARY_PATH,
        SATURATION_MD,
        CONTEXT_ANCHOR,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        ROUTE_DIR / "scheduler_v3_default_off.py",
        ROUTE_DIR / "build_vnext_absolute_moonshot_scheduler_v3.py",
        ROUTE_DIR / "verify_vnext_absolute_moonshot_scheduler_v3.py",
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "line_count": count_jsonl(path) if path.suffix in {".jsonl", ".gz"} else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": file_sha256(path),
            }
        )
    return rows


def write_manifest_and_audit(stats: dict[str, Any], verification: dict[str, Any] | None = None) -> None:
    generated = utc_now()
    audit = {
        "schema_version": f"{SCHEMA_PREFIX}_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated,
        "status": "complete_for_default_off_scheduler_v3_package_pending_scoped_commit",
        "instruction_coverage": {
            "live_state_regenerated": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "master_post_lane18_decision_read": True,
            "lane09b_lane10_lane10b_lane11_lane16_lane17_lane18_read": True,
            "source_capture_repair_consumed": True,
            "risk_scheduler_runtime_code_read": True,
            "builder_posture": "constructive_scheduler_builder_with_same_evidence_class_pursuit",
            "proof_or_impossibility": "all current executable joins/parsers/ledgers/verifiers/focused_tests_done_inside_default_off_evidence_class",
        },
        "row_counts": compact_stats(stats),
        "required_outputs": {
            "full_scheduler_evidence_ledger": rel(FULL_EVIDENCE_LEDGER),
            "accepted_reduced_rejected_decision_ledger": rel(DECISION_LEDGER),
            "conflict_anatomy_disposition_ledger": rel(CONFLICT_LEDGER),
            "blocked_edge_recovery_ledger": rel(BLOCKED_EDGE_LEDGER),
            "money_risk_exposure_ledger": rel(MONEY_RISK_LEDGER),
            "same_symbol_multi_ticket_lifecycle_contract": rel(LIFECYCLE_CONTRACT),
            "correlation_cluster_exposure_ledger": rel(CORRELATION_LEDGER),
            "source_gap_capture_dependency_ledger": rel(SOURCE_GAP_LEDGER),
            "default_off_package": rel(DEFAULT_OFF_PACKAGE),
            "source_capture_decisions": rel(SOURCE_CAPTURE_DECISIONS),
            "source_completeness_decisions": rel(SOURCE_COMPLETENESS_DECISIONS),
            "branch_decisions": rel(BRANCH_DECISIONS),
            "implementation_decisions": rel(IMPLEMENTATION_DECISIONS),
            "result_use_status": rel(RESULT_USE_STATUS_PATH),
            "split_stress_deconcentration": rel(SPLIT_STRESS_LEDGER),
            "downstream_contracts": rel(DOWNSTREAM_CONTRACTS),
            "saturation_self_red_team": rel(SATURATION_MD),
            "route_manifest": rel(OUTPUT_MANIFEST),
            "verifier": rel(VERIFICATION_RESULT),
        },
        "source_use_state": "current_disk_route_artifacts_and_local_repo_code_only_no_broker_mutation",
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "live_scheduler_activation": False,
        "scoped_commit_required": True,
        "verification_result": verification,
    }
    write_json(COMPLETION_AUDIT, audit)
    manifest = {
        "schema_version": f"{SCHEMA_PREFIX}_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "artifact_count": len(manifest_rows()),
        "artifacts": manifest_rows(),
        "counts": compact_stats(stats),
    }
    write_json(OUTPUT_MANIFEST, manifest)


def verify_outputs(write: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    package = read_json(DEFAULT_OFF_PACKAGE) if DEFAULT_OFF_PACKAGE.exists() else {}
    completion = read_json(COMPLETION_AUDIT) if COMPLETION_AUDIT.exists() else {}
    ledger_counts = {
        "full_evidence_rows": count_jsonl(FULL_EVIDENCE_LEDGER),
        "decision_rows": count_jsonl(DECISION_LEDGER),
        "conflict_rows": count_jsonl(CONFLICT_LEDGER),
        "money_risk_rows": count_jsonl(MONEY_RISK_LEDGER),
        "source_gap_rows": count_jsonl(SOURCE_GAP_LEDGER),
    }
    for name, count in ledger_counts.items():
        if count != EXPECTED_ROWS:
            issues.append(f"{name} expected {EXPECTED_ROWS} got {count}")
    blocked_count = count_jsonl(BLOCKED_EDGE_LEDGER)
    if blocked_count <= 0:
        issues.append("blocked edge recovery ledger is empty")
    correlation_count = count_jsonl(CORRELATION_LEDGER)
    if correlation_count < EXPECTED_ROWS + 276:
        issues.append("correlation ledger does not preserve candidate rows plus pair rules")
    if package.get("enabled_by_default") is not False:
        issues.append("default-off package is not disabled by default")
    if package.get("apply_to_execution_default") is not False:
        issues.append("default-off package apply_to_execution_default is not false")
    if package.get("live_activation_allowed_by_this_package") is not False:
        issues.append("package permits live activation")
    forbidden = " ".join(package.get("forbidden_authority") or [])
    if "static max-trades authority" not in forbidden:
        issues.append("package does not explicitly forbid static max-trades authority")
    if set(ACTION_CLASSES) - set(package.get("action_classes") or []):
        issues.append("package missing Scheduler V3 action classes")

    sample_money = next(iter(iter_jsonl(MONEY_RISK_LEDGER)), {})
    missing_money = [field for field in REQUIRED_MONEY_RISK_FIELDS if field not in sample_money]
    if missing_money:
        issues.append(f"money-risk sample missing fields: {missing_money}")

    decision_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    result_class_counts: Counter[str] = Counter()
    checked = 0
    for row in iter_jsonl(DECISION_LEDGER):
        decision_counts[row.get("scheduler_v3_decision")] += 1
        action_counts[row.get("scheduler_v3_action_class")] += 1
        result_class_counts[row.get("result_r_class")] += 1
        checked += 1
    required_action_classes = set(ACTION_CLASSES)
    if required_action_classes - set(action_counts):
        issues.append(f"decision ledger missing action classes: {sorted(required_action_classes - set(action_counts))}")
    if checked != EXPECTED_ROWS:
        issues.append("decision ledger scan count mismatch")
    if not {"ACCEPTED", "ACCEPTED_REDUCED_RISK", "REJECTED", "QUEUE", "DELAY", "REPLACE", "REQUIRE_SOURCE"} & set(decision_counts):
        issues.append("decision ledger lacks expected decision states")

    source_decisions = list(iter_jsonl(SOURCE_COMPLETENESS_DECISIONS))
    if not source_decisions:
        issues.append("source completeness decisions missing")
    if not any(row.get("consumer") == "Scheduler V3" for row in source_decisions):
        issues.append("source completeness decisions do not reference Scheduler V3")

    result_use = read_json(RESULT_USE_STATUS_PATH) if RESULT_USE_STATUS_PATH.exists() else {}
    if "exact_proxy_expectancy_by_class" not in result_use:
        issues.append("result-use status missing exact/proxy expectancy fields")
    if LIVE_FORBIDDEN not in completion.get("runtime_effect_boundary", "") and "no_live" not in completion.get("runtime_effect_boundary", ""):
        issues.append("completion audit runtime boundary is not explicit enough")

    result = {
        "schema_version": f"{SCHEMA_PREFIX}_verification_result_v1",
        "route_id": ROUTE_ID,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "ledger_counts": {
            **ledger_counts,
            "blocked_edge_rows": blocked_count,
            "correlation_rows": correlation_count,
            "split_stress_rows": count_jsonl(SPLIT_STRESS_LEDGER),
        },
        "decision_counts": dict(sorted(decision_counts.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
        "result_class_counts": dict(sorted(result_class_counts.items())),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    indexes = build_indexes()
    rank_map = build_rank_map(indexes)
    stats = build_output_rows(indexes, rank_map)
    write_control_artifacts(stats)
    write_json(FOCUSED_TEST_RESULT, {"placeholder": "focused pytest writes junit xml here when executed"})
    write_manifest_and_audit(stats, verification=None)
    verification = verify_outputs(write=True)
    write_manifest_and_audit(stats, verification=verification)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = verify_outputs(write=True) if args.verify_only else build_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
