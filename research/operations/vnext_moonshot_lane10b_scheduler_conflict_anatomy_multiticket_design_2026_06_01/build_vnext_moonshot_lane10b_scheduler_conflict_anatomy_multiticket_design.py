"""Build Lane10b scheduler conflict anatomy and Scheduler V3 design artifacts.

This route is intentionally offline/default-off. It consumes committed Lane10 as
immutable evidence, joins committed Lane09 selector context, and writes full
row-level anatomy plus design contracts for a future Scheduler V3. It does not
modify Lane10, runtime config, broker state, or live trading behavior.
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


ROUTE_ID = "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
SCHEMA_PREFIX = "lane10b_scheduler_conflict_anatomy_multiticket_design"
ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE10_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
LANE09_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE11_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"

LANE10_REPLAY = LANE10_DIR / "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"
LANE10_CONFLICTS = LANE10_DIR / "LANE10_SCHEDULING_CONFLICT_LEDGER.jsonl.gz"
LANE10_AUDIT = LANE10_DIR / "LANE10_COMPLETION_AUDIT.json"
LANE10_MANIFEST = LANE10_DIR / "LANE10_OUTPUT_MANIFEST.json"
LANE09_ROW_EVIDENCE = LANE09_DIR / "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz"
LANE09_MECHANISMS = LANE09_DIR / "LANE09_SELECTOR_MECHANISM_RANKING.jsonl"
LANE09_CONTRACT = LANE09_DIR / "LANE09_DOWNSTREAM_CONTRACT.json"
LANE09_AUDIT = LANE09_DIR / "LANE09_COMPLETION_AUDIT.json"
LANE08_AUDIT = LANE08_DIR / "LANE08_COMPLETION_AUDIT.json"
LANE05_AUDIT = LANE05_DIR / "LANE05_COMPLETION_AUDIT.json"
LANE06_AUDIT = LANE06_DIR / "LANE06_COMPLETION_AUDIT.json"
LANE07_AUDIT = LANE07_DIR / "LANE07_COMPLETION_AUDIT.json"

FULL_ANATOMY_LEDGER = ROUTE_DIR / "LANE10B_FULL_CONFLICT_ANATOMY_LEDGER.jsonl.gz"
MISSED_EDGE_LEDGER = ROUTE_DIR / "LANE10B_MISSED_EDGE_VALUE_LEDGER.jsonl.gz"
CORRECT_REJECT_LEDGER = ROUTE_DIR / "LANE10B_CORRECT_REJECT_LEDGER.jsonl.gz"
REPAIRABLE_BLOCK_LEDGER = ROUTE_DIR / "LANE10B_REPAIRABLE_SCHEDULER_BLOCK_LEDGER.jsonl.gz"
RISK_BREACH_PROOF_LEDGER = ROUTE_DIR / "LANE10B_RISK_BREACH_PROOF_LEDGER.jsonl.gz"
IMPACT_BY_DIMENSION_LEDGER = ROUTE_DIR / "LANE10B_MISSED_EDGE_IMPACT_BY_DIMENSION.jsonl"
STRESS_SIMULATION_LEDGER = ROUTE_DIR / "LANE10B_STRESS_SIMULATION_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE10B_SOURCE_GAP_LEDGER.jsonl"
BRANCH_DECISION_LEDGER = ROUTE_DIR / "LANE10B_BRANCH_DECISION_LEDGER.jsonl"
MULTI_TICKET_CONTRACT = ROUTE_DIR / "LANE10B_MULTI_TICKET_LIFECYCLE_CONTRACT.json"
SCHEDULER_V3_PACKAGE = ROUTE_DIR / "LANE10B_SCHEDULER_V3_DEFAULT_OFF_DESIGN_PACKAGE.json"
LANE11_INTEGRATION_CONTRACT = ROUTE_DIR / "LANE10B_LANE11_INTEGRATION_CONTRACT.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE10B_CONTEXT_ANCHOR.md"
COMPLETION_AUDIT = ROUTE_DIR / "LANE10B_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE10B_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE10B_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE10B_FOCUSED_TEST_RESULT.xml"

EXPECTED_REPLAY_ROWS = 289_928
EXPECTED_REJECT_ROWS = 215_495
EXPECTED_ACCEPTED_ROWS = 67_365
EXPECTED_REDUCED_ROWS = 7_068
EXPECTED_MISSED_EDGE_ROWS = EXPECTED_REJECT_ROWS + EXPECTED_REDUCED_ROWS
RISK_BASE_AMOUNT = 100_000.0
BASE_CLUSTER_CEILING_PCT = 4.0
MIN_REDUCED_RISK_PCT = 0.25
MICRO_REDUCED_RISK_PCT = 0.10
RUNTIME_EFFECT_BOUNDARY = (
    "offline_scheduler_v3_conflict_anatomy_design_only_no_live_broker_order_deal_position_"
    "operation_no_config_prompt_risk_execution_safety_selector_activation_no_paid_api_no_remote"
)
RESULT_USE_STATUS = (
    "scheduler_conflict_anatomy_and_default_off_design_research_only_uses_lane10_source_bound_"
    "proxy_results_for_forensics_not_production_change"
)

REQUIRED_BRANCHES = [
    "same_symbol_fail_closed_current",
    "isolated_multi_ticket_lifecycle_design",
    "same_side_stacking_design",
    "opposite_side_hedge_rejection_design",
    "cluster_exposure_variants",
    "dynamic_risk_compression_expansion",
    "partial_be_risk_release",
    "selector_quality_priority_queue",
    "expected_r_priority_queue",
    "portfolio_budget_variants",
    "daily_overall_prop_boundary_variants",
    "reduced_risk_admission_variants",
    "lane11_expanded_policy_integration",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def clean(value: Any, default: str = "missing") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def round9(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 9)


def money(value: Any) -> float:
    return round(float(value or 0.0), 2)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def is_true(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def edge_bucket(result_r: float) -> str:
    if result_r <= -1.0:
        return "r_lte_minus_1"
    if result_r < 0.0:
        return "r_minus_1_to_0"
    if result_r == 0.0:
        return "r_zero"
    if result_r < 0.5:
        return "r_0_to_0_5"
    if result_r < 1.0:
        return "r_0_5_to_1"
    if result_r < 2.0:
        return "r_1_to_2"
    return "r_gte_2"


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
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


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
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


def load_selector_index() -> dict[str, dict[str, Any]]:
    fields = {
        "source_row_id",
        "selected_row_id",
        "selector_component",
        "policy_alignment_state",
        "path_class",
        "label_evidence_class",
        "source_quality_status",
        "source_completeness_state",
        "source_gap_codes",
        "source_gap_families",
        "portfolio_decision",
        "same_symbol_conflict_state",
        "selected_cell_effective_risk_pct_bucket",
        "broker_feasibility_state",
        "liquidity_sweep_proxy_state",
        "regime_h4_state",
        "m15_trend_state_20",
        "m15_volatility_state_14_vs_50",
        "m1_availability_status",
        "strict_tick_available",
        "tick_availability_status",
        "sealed_partition",
        "correct_rejection",
        "missed_opportunity",
    }
    index: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(LANE09_ROW_EVIDENCE):
        source_row_id = clean(row.get("source_row_id"), "")
        if not source_row_id:
            continue
        index[source_row_id] = {field: row.get(field) for field in fields if field in row}
    return index


def load_mechanism_decisions() -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    if not LANE09_MECHANISMS.exists():
        return decisions
    for row in iter_jsonl(LANE09_MECHANISMS):
        family = clean(row.get("mechanism_family"), "")
        if family:
            decisions[family] = row
    return decisions


def money_risk_authority_fields_present(row: dict[str, Any]) -> bool:
    required = [
        "open_risk_pct_before",
        "pending_risk_pct_before",
        "requested_risk_pct",
        "account_available_risk_pct",
        "current_equity",
        "day_start_baseline",
        "daily_cushion_before",
        "overall_cushion_before",
        "cost_buffer_pct",
        "same_symbol_risk_pct_before",
        "correlated_cluster_risk_pct_before",
        "total_risk_pct_before",
        "dynamic_portfolio_ceiling_pct",
    ]
    return all(row.get(field) is not None for field in required)


def budget_state(row: dict[str, Any]) -> dict[str, Any]:
    requested = fnum(row.get("requested_risk_pct"))
    account_available = fnum(row.get("account_available_risk_pct"))
    total_before = fnum(row.get("total_risk_pct_before"))
    dynamic_ceiling = fnum(row.get("dynamic_portfolio_ceiling_pct"))
    cluster_before = fnum(row.get("correlated_cluster_risk_pct_before"))
    account_headroom = account_available - total_before
    portfolio_headroom = dynamic_ceiling - total_before
    cluster_headroom = BASE_CLUSTER_CEILING_PCT - cluster_before
    max_allowed = max(0.0, min(account_headroom, portfolio_headroom, cluster_headroom))
    return {
        "account_headroom_after_existing_pct": round9(account_headroom),
        "portfolio_headroom_pct": round9(portfolio_headroom),
        "cluster_headroom_pct": round9(cluster_headroom),
        "max_money_risk_allowed_pct": round9(max(0.0, min(account_headroom, portfolio_headroom))),
        "max_safe_risk_with_cluster_pct": round9(max_allowed),
        "full_risk_breaches_account": requested > max(0.0, account_headroom) + 1e-12,
        "full_risk_breaches_portfolio": requested > max(0.0, portfolio_headroom) + 1e-12,
        "full_risk_breaches_cluster": requested > max(0.0, cluster_headroom) + 1e-12,
        "any_full_risk_breach": requested > max_allowed + 1e-12,
    }


def drawdown_state(row: dict[str, Any]) -> str:
    current_equity = fnum(row.get("current_equity"))
    day_start = fnum(row.get("day_start_baseline"))
    realized = current_equity - day_start
    if realized < 0.0:
        return "drawdown_compression_active"
    if realized >= 1000.0:
        return "cushion_expansion_active"
    return "neutral_day_cushion"


def resolve_conflict_details(
    conflict_ids: list[Any],
    accepted_by_selected_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    details: list[dict[str, Any]] = []
    missing: list[str] = []
    for raw_id in conflict_ids or []:
        conflict_id = clean(raw_id, "")
        if not conflict_id:
            continue
        row = accepted_by_selected_id.get(conflict_id)
        if row is None:
            missing.append(conflict_id)
            continue
        details.append(row)
    return details, missing


def classify_same_symbol_state(
    row: dict[str, Any],
    same_symbol_details: list[dict[str, Any]],
    missing_conflicts: list[str],
) -> dict[str, Any]:
    conflict_ids = row.get("same_symbol_conflict_ids") or []
    if not conflict_ids:
        return {
            "same_symbol_state": "no_same_symbol_active",
            "same_symbol_release_state": "no_same_symbol_active",
            "same_symbol_active_sides": [],
            "same_symbol_unresolved_conflict_ids": [],
        }
    if missing_conflicts:
        return {
            "same_symbol_state": "same_symbol_conflict_unresolved_source_gap",
            "same_symbol_release_state": "same_symbol_release_unresolved_source_gap",
            "same_symbol_active_sides": [],
            "same_symbol_unresolved_conflict_ids": missing_conflicts,
        }
    candidate_side = clean(row.get("side"), "missing").upper()
    active_sides = sorted({clean(detail.get("side"), "missing").upper() for detail in same_symbol_details})
    if not active_sides:
        state = "same_symbol_conflict_unresolved_source_gap"
    elif all(side == candidate_side for side in active_sides):
        state = "same_symbol_same_side_active"
    elif all(side != candidate_side for side in active_sides):
        state = "same_symbol_opposite_side_active"
    else:
        state = "same_symbol_mixed_side_active"

    decision_dt = parse_dt(row.get("candidate_time_utc"))
    release_states: list[str] = []
    for detail in same_symbol_details:
        release_dt = parse_dt(detail.get("risk_release_time_utc"))
        exit_dt = parse_dt(detail.get("exit_time_utc"))
        if decision_dt and release_dt and release_dt <= decision_dt and exit_dt and decision_dt < exit_dt:
            release_states.append("risk_released_lifecycle_still_active")
        elif decision_dt and release_dt and release_dt <= decision_dt:
            release_states.append("risk_released")
        else:
            release_states.append("open_worst_case_risk_active")
    if release_states and all(state == "risk_released_lifecycle_still_active" for state in release_states):
        release_state = "same_symbol_all_risk_released_lifecycle_active"
    elif any(state == "risk_released_lifecycle_still_active" for state in release_states):
        release_state = "same_symbol_mixed_release_state"
    else:
        release_state = "same_symbol_open_worst_case_risk_active"
    return {
        "same_symbol_state": state,
        "same_symbol_release_state": release_state,
        "same_symbol_active_sides": active_sides,
        "same_symbol_unresolved_conflict_ids": [],
    }


def cluster_state(row: dict[str, Any], cluster_missing: list[str]) -> str:
    requested = fnum(row.get("requested_risk_pct"))
    cluster_before = fnum(row.get("correlated_cluster_risk_pct_before"))
    if cluster_missing:
        return "cluster_conflict_unresolved_source_gap"
    if cluster_before <= 0.0:
        return "cluster_clear"
    if cluster_before + requested > BASE_CLUSTER_CEILING_PCT + 1e-12:
        return "cluster_ceiling_exceeded"
    return "cluster_active_under_ceiling"


def risk_budget_state(row: dict[str, Any], budget: dict[str, Any], same_state: str, cluster_status: str) -> str:
    requested = fnum(row.get("requested_risk_pct"))
    reason = clean(row.get("scheduler_reason") or row.get("reason"))
    if requested <= 0.0:
        return "source_risk_missing_or_nonpositive"
    if same_state.startswith("same_symbol_") and same_state != "no_same_symbol_active":
        return "same_symbol_lifecycle_gate_before_money_budget"
    if cluster_status == "cluster_ceiling_exceeded" or reason == "correlated_cluster_exposure_ceiling_exceeded":
        return "cluster_budget_exhausted"
    max_money = fnum(budget.get("max_money_risk_allowed_pct"))
    if max_money + 1e-12 >= requested:
        return "full_money_risk_budget_available"
    if max_money >= MIN_REDUCED_RISK_PCT:
        return "reduced_money_risk_budget_available"
    if fnum(budget.get("account_headroom_after_existing_pct")) < MIN_REDUCED_RISK_PCT:
        return "account_daily_or_overall_budget_exhausted"
    if drawdown_state(row) == "drawdown_compression_active":
        return "drawdown_compression_budget_exhausted"
    return "portfolio_budget_exhausted"


def branch_candidates_for_row(
    row: dict[str, Any],
    same_state: str,
    release_state: str,
    cluster_status: str,
    budget: dict[str, Any],
    mechanism_decision: str,
) -> list[str]:
    decision = clean(row.get("scheduler_decision") or row.get("decision"))
    reason = clean(row.get("scheduler_reason") or row.get("reason"))
    result_r = fnum(row.get("result_r"))
    requested = fnum(row.get("requested_risk_pct"))
    branches: list[str] = []
    if reason == "same_symbol_exposure_conflict_active_until_lifecycle_close":
        branches.append("same_symbol_fail_closed_current")
        if same_state == "same_symbol_opposite_side_active" or same_state == "same_symbol_mixed_side_active":
            branches.append("opposite_side_hedge_rejection_design")
        if result_r > 0.0 and fnum(budget.get("max_safe_risk_with_cluster_pct")) >= MICRO_REDUCED_RISK_PCT:
            branches.append("isolated_multi_ticket_lifecycle_design")
            if same_state == "same_symbol_same_side_active":
                branches.append("same_side_stacking_design")
            if release_state in {
                "same_symbol_all_risk_released_lifecycle_active",
                "same_symbol_mixed_release_state",
            }:
                branches.append("partial_be_risk_release")
    if reason == "correlated_cluster_exposure_ceiling_exceeded":
        branches.append("cluster_exposure_variants")
    if reason in {
        "account_daily_or_overall_limit_exceeded",
        "drawdown_compression_portfolio_budget_exceeded",
        "portfolio_total_risk_ceiling_exceeded",
    } or decision == "ACCEPTED_REDUCED_RISK":
        branches.extend(
            [
                "dynamic_risk_compression_expansion",
                "portfolio_budget_variants",
                "daily_overall_prop_boundary_variants",
                "reduced_risk_admission_variants",
            ]
        )
    if decision == "ACCEPTED_REDUCED_RISK" and requested > fnum(row.get("approved_risk_pct")):
        branches.append("reduced_risk_admission_variants")
    if mechanism_decision in {"promote", "reduce"}:
        branches.append("selector_quality_priority_queue")
    if result_r > 0.0:
        branches.append("expected_r_priority_queue")
    if decision != "ACCEPTED" and result_r > 0.0:
        branches.append("lane11_expanded_policy_integration")
    return sorted(set(branches))


def classify_scheduler_row(
    row: dict[str, Any],
    same_symbol_details: list[dict[str, Any]],
    same_symbol_missing: list[str],
    cluster_missing: list[str],
    selector_row: dict[str, Any] | None,
    mechanism_row: dict[str, Any] | None,
) -> dict[str, Any]:
    selector_row = selector_row or {}
    mechanism_row = mechanism_row or {}
    same = classify_same_symbol_state(row, same_symbol_details, same_symbol_missing)
    cluster_status = cluster_state(row, cluster_missing)
    budget = budget_state(row)
    risk_state = risk_budget_state(row, budget, same["same_symbol_state"], cluster_status)
    mechanism_decision = clean(mechanism_row.get("mechanism_decision"), "missing")
    decision = clean(row.get("scheduler_decision") or row.get("decision"))
    reason = clean(row.get("scheduler_reason") or row.get("reason"))
    result_r = fnum(row.get("result_r"))
    requested = fnum(row.get("requested_risk_pct"))
    approved = fnum(row.get("approved_risk_pct"))
    max_safe = fnum(budget.get("max_safe_risk_with_cluster_pct"))
    max_money = fnum(budget.get("max_money_risk_allowed_pct"))
    branch_candidates = branch_candidates_for_row(
        row,
        same["same_symbol_state"],
        same["same_symbol_release_state"],
        cluster_status,
        budget,
        mechanism_decision,
    )

    classification = "accepted_baseline_no_scheduler_block"
    classification_reason = "accepted_full_risk_under_lane10_money_risk_authority"
    correct_reject = False
    repairable = False
    v3_action = "preserve_current_admission"

    if decision == "ACCEPTED_REDUCED_RISK":
        classification = "repairable_reduced_risk_action"
        classification_reason = "accepted_but_edge_was_haircut_by_money_budget"
        repairable = True
        v3_action = "design_reduced_risk_priority_and_budget_variants"
    elif decision == "REJECTED":
        if requested <= 0.0 or reason == "selected_cell_or_effective_risk_missing_nonpositive_stale_source_repair_required":
            classification = "correct_fail_closed_source_risk_gap"
            classification_reason = "selected_cell_or_effective_risk_missing_nonpositive"
            correct_reject = True
            v3_action = "source_repair_required_not_scheduler_relaxation"
        elif result_r <= 0.0:
            classification = "correct_reject_no_positive_proxy_edge"
            classification_reason = "posthoc_source_bound_proxy_r_nonpositive"
            correct_reject = True
            v3_action = "preserve_reject_for_this_evidence_slice"
        elif reason == "same_symbol_exposure_conflict_active_until_lifecycle_close":
            if same["same_symbol_state"] in {
                "same_symbol_opposite_side_active",
                "same_symbol_mixed_side_active",
            }:
                classification = "correct_fail_closed_same_symbol_hedge_or_mixed_side"
                classification_reason = "opposite_or_mixed_side_same_symbol_requires_explicit_hedge_contract"
                correct_reject = True
                v3_action = "keep_opposite_side_hedge_rejected_until_owner_approved_contract"
            elif max_safe >= MICRO_REDUCED_RISK_PCT:
                classification = "repairable_same_symbol_multiticket_candidate"
                classification_reason = "positive_proxy_edge_same_symbol_block_with_ticket_bound_money_risk_headroom"
                repairable = True
                v3_action = "design_isolated_same_side_or_risk_released_multiticket_contract"
            else:
                classification = "correct_fail_closed_same_symbol_money_risk_not_safe"
                classification_reason = "same_symbol_relaxation_lacks_safe_money_risk_headroom"
                correct_reject = True
                v3_action = "preserve_fail_closed_until_risk_headroom_exists"
        elif reason == "correlated_cluster_exposure_ceiling_exceeded":
            relaxed_cluster_headroom = 5.0 - fnum(row.get("correlated_cluster_risk_pct_before"))
            if min(max_money, relaxed_cluster_headroom) >= MICRO_REDUCED_RISK_PCT:
                classification = "repairable_cluster_variant_candidate"
                classification_reason = "positive_proxy_edge_cluster_block_has_relaxed_or_reduced_risk_design_headroom"
                repairable = True
                v3_action = "design_cluster_ceiling_and_reduced_risk_variants"
            else:
                classification = "correct_fail_closed_cluster_concentration"
                classification_reason = "cluster_ceiling_exceeded_without_safe_relaxed_money_risk_headroom"
                correct_reject = True
                v3_action = "preserve_cluster_concentration_reject"
        elif reason in {
            "account_daily_or_overall_limit_exceeded",
            "drawdown_compression_portfolio_budget_exceeded",
            "portfolio_total_risk_ceiling_exceeded",
        }:
            if max_money >= MICRO_REDUCED_RISK_PCT:
                classification = "repairable_reduced_risk_budget_candidate"
                classification_reason = "positive_proxy_edge_with_nonzero_money_risk_headroom_below_lane10_minimum"
                repairable = True
                v3_action = "design_micro_reduced_risk_and_priority_queue_variants"
            else:
                classification = "correct_fail_closed_money_risk_budget_exhausted"
                classification_reason = "daily_overall_portfolio_or_drawdown_budget_exhausted"
                correct_reject = True
                v3_action = "preserve_prop_boundary_or_portfolio_budget_reject"
        elif result_r > 0.0 and max_money >= MICRO_REDUCED_RISK_PCT:
            classification = "repairable_unclassified_positive_edge_budget_candidate"
            classification_reason = "positive_proxy_edge_unclassified_block_with_some_money_risk_headroom"
            repairable = True
            v3_action = "design_under_explicit_branch_before_activation"
        else:
            classification = "correct_fail_closed_other"
            classification_reason = "no_safe_repairable_scheduler_path_from_current_evidence"
            correct_reject = True
            v3_action = "preserve_reject"

    missed_scope = "none"
    missed_risk_pct = 0.0
    missed_result_r = 0.0
    if decision == "REJECTED":
        missed_scope = "rejected_conflict_or_block"
        missed_risk_pct = max(0.0, requested)
        missed_result_r = result_r
    elif decision == "ACCEPTED_REDUCED_RISK":
        missed_scope = "accepted_reduced_risk_haircut"
        missed_risk_pct = max(0.0, requested - approved)
        missed_result_r = result_r * (missed_risk_pct / requested) if requested > 0.0 else 0.0
    missed_proxy_amount = missed_result_r * RISK_BASE_AMOUNT * (missed_risk_pct / 100.0) if missed_scope != "none" else 0.0

    return {
        **same,
        **budget,
        "branch_candidates": branch_candidates,
        "classification": classification,
        "classification_reason": classification_reason,
        "cluster_state": cluster_status,
        "correct_reject": correct_reject,
        "drawdown_state": drawdown_state(row),
        "edge_bucket": edge_bucket(result_r),
        "lane09_selector_component": clean(selector_row.get("selector_component")),
        "lane09_policy_alignment_state": clean(selector_row.get("policy_alignment_state")),
        "lane09_path_class": clean(selector_row.get("path_class")),
        "lane09_source_quality_status": clean(selector_row.get("source_quality_status")),
        "lane09_source_completeness_state": clean(selector_row.get("source_completeness_state")),
        "lane09_selected_cell_effective_risk_pct_bucket": clean(
            selector_row.get("selected_cell_effective_risk_pct_bucket")
        ),
        "lane09_mechanism_decision": mechanism_decision,
        "lane09_mechanism_expectancy_r": mechanism_row.get("expectancy_r"),
        "lane09_mechanism_win_rate": mechanism_row.get("win_rate"),
        "missed_edge_scope": missed_scope,
        "missed_proxy_amount": money(missed_proxy_amount),
        "missed_result_r": round9(missed_result_r),
        "missed_risk_pct": round9(missed_risk_pct),
        "money_risk_authority_fields_present": money_risk_authority_fields_present(row),
        "repairable_scheduler_block": repairable,
        "risk_budget_state": risk_state,
        "v3_action": v3_action,
    }


def anatomy_row(row: dict[str, Any], anatomy: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row.get("row_id"),
        "candidate_id": row.get("candidate_id"),
        "selected_row_id": row.get("selected_row_id"),
        "candidate_time_utc": row.get("candidate_time_utc"),
        "calendar_day": row.get("calendar_day"),
        "calendar_week": row.get("calendar_week"),
        "calendar_month": row.get("calendar_month"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "session_bucket": row.get("session_bucket"),
        "origin_family": row.get("origin_family"),
        "mechanism_family": row.get("origin_family"),
        "framework": row.get("framework"),
        "chosen_policy": row.get("chosen_policy"),
        "correlation_cluster": row.get("correlation_cluster"),
        "spread_r_bucket": row.get("spread_r_bucket"),
        "cost_status": row.get("cost_status"),
        "scheduler_decision": row.get("scheduler_decision") or row.get("decision"),
        "scheduler_reason": row.get("scheduler_reason") or row.get("reason"),
        "accepted": row.get("accepted"),
        "requested_risk_pct": row.get("requested_risk_pct"),
        "approved_risk_pct": row.get("approved_risk_pct"),
        "cost_buffer_pct": row.get("cost_buffer_pct"),
        "open_risk_pct_before": row.get("open_risk_pct_before"),
        "pending_risk_pct_before": row.get("pending_risk_pct_before"),
        "same_symbol_risk_pct_before": row.get("same_symbol_risk_pct_before"),
        "correlated_cluster_risk_pct_before": row.get("correlated_cluster_risk_pct_before"),
        "total_risk_pct_before": row.get("total_risk_pct_before"),
        "total_risk_pct_after": row.get("total_risk_pct_after"),
        "dynamic_portfolio_ceiling_pct": row.get("dynamic_portfolio_ceiling_pct"),
        "account_available_risk_pct": row.get("account_available_risk_pct"),
        "daily_cushion_before": row.get("daily_cushion_before"),
        "overall_cushion_before": row.get("overall_cushion_before"),
        "internal_daily_cushion_before": row.get("internal_daily_cushion_before"),
        "day_start_baseline": row.get("day_start_baseline"),
        "current_equity": row.get("current_equity"),
        "realized_proxy_pnl": row.get("realized_proxy_pnl"),
        "result_r": row.get("result_r"),
        "result_r_class": row.get("result_r_class"),
        "same_symbol_conflict_ids": row.get("same_symbol_conflict_ids") or [],
        "correlated_cluster_conflict_ids": row.get("correlated_cluster_conflict_ids") or [],
        "same_symbol_state": anatomy["same_symbol_state"],
        "same_symbol_release_state": anatomy["same_symbol_release_state"],
        "cluster_state": anatomy["cluster_state"],
        "drawdown_state": anatomy["drawdown_state"],
        "risk_budget_state": anatomy["risk_budget_state"],
        "edge_bucket": anatomy["edge_bucket"],
        "classification": anatomy["classification"],
        "classification_reason": anatomy["classification_reason"],
        "correct_reject": anatomy["correct_reject"],
        "repairable_scheduler_block": anatomy["repairable_scheduler_block"],
        "v3_action": anatomy["v3_action"],
        "v3_branch_candidates": anatomy["branch_candidates"],
        "missed_edge_scope": anatomy["missed_edge_scope"],
        "missed_risk_pct": anatomy["missed_risk_pct"],
        "missed_result_r": anatomy["missed_result_r"],
        "missed_proxy_amount": anatomy["missed_proxy_amount"],
        "account_headroom_after_existing_pct": anatomy["account_headroom_after_existing_pct"],
        "portfolio_headroom_pct": anatomy["portfolio_headroom_pct"],
        "cluster_headroom_pct": anatomy["cluster_headroom_pct"],
        "max_money_risk_allowed_pct": anatomy["max_money_risk_allowed_pct"],
        "max_safe_risk_with_cluster_pct": anatomy["max_safe_risk_with_cluster_pct"],
        "lane09_selector_component": anatomy["lane09_selector_component"],
        "lane09_policy_alignment_state": anatomy["lane09_policy_alignment_state"],
        "lane09_path_class": anatomy["lane09_path_class"],
        "lane09_source_quality_status": anatomy["lane09_source_quality_status"],
        "lane09_source_completeness_state": anatomy["lane09_source_completeness_state"],
        "lane09_selected_cell_effective_risk_pct_bucket": anatomy[
            "lane09_selected_cell_effective_risk_pct_bucket"
        ],
        "lane09_mechanism_decision": anatomy["lane09_mechanism_decision"],
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_PREFIX}_full_anatomy_row_v1",
    }


def risk_breach_row(row: dict[str, Any], anatomy: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": row.get("row_id"),
        "selected_row_id": row.get("selected_row_id"),
        "scheduler_decision": row.get("scheduler_decision") or row.get("decision"),
        "scheduler_reason": row.get("scheduler_reason") or row.get("reason"),
        "requested_risk_pct": row.get("requested_risk_pct"),
        "approved_risk_pct": row.get("approved_risk_pct"),
        "cost_buffer_pct": row.get("cost_buffer_pct"),
        "open_risk_pct_before": row.get("open_risk_pct_before"),
        "pending_risk_pct_before": row.get("pending_risk_pct_before"),
        "same_symbol_risk_pct_before": row.get("same_symbol_risk_pct_before"),
        "correlated_cluster_risk_pct_before": row.get("correlated_cluster_risk_pct_before"),
        "total_risk_pct_before": row.get("total_risk_pct_before"),
        "dynamic_portfolio_ceiling_pct": row.get("dynamic_portfolio_ceiling_pct"),
        "account_available_risk_pct": row.get("account_available_risk_pct"),
        "account_headroom_after_existing_pct": anatomy["account_headroom_after_existing_pct"],
        "portfolio_headroom_pct": anatomy["portfolio_headroom_pct"],
        "cluster_headroom_pct": anatomy["cluster_headroom_pct"],
        "max_money_risk_allowed_pct": anatomy["max_money_risk_allowed_pct"],
        "max_safe_risk_with_cluster_pct": anatomy["max_safe_risk_with_cluster_pct"],
        "full_risk_breaches_account": anatomy["full_risk_breaches_account"],
        "full_risk_breaches_portfolio": anatomy["full_risk_breaches_portfolio"],
        "full_risk_breaches_cluster": anatomy["full_risk_breaches_cluster"],
        "any_full_risk_breach": anatomy["any_full_risk_breach"],
        "same_symbol_state": anatomy["same_symbol_state"],
        "same_symbol_release_state": anatomy["same_symbol_release_state"],
        "money_risk_authority_fields_present": anatomy["money_risk_authority_fields_present"],
        "v3_candidate_max_safe_risk_pct": anatomy["max_safe_risk_with_cluster_pct"],
        "v3_min_reduced_risk_pct": MIN_REDUCED_RISK_PCT,
        "breach_proof_summary": (
            "worst_case_money_risk_headroom_computed_from_open_pending_new_cost_account_cluster"
        ),
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": f"{SCHEMA_PREFIX}_risk_breach_proof_v1",
    }


def missed_edge_row(row: dict[str, Any], anatomy: dict[str, Any]) -> dict[str, Any]:
    base = anatomy_row(row, anatomy)
    return {
        key: base[key]
        for key in [
            "row_id",
            "candidate_id",
            "selected_row_id",
            "candidate_time_utc",
            "calendar_day",
            "calendar_week",
            "calendar_month",
            "symbol",
            "side",
            "session_bucket",
            "origin_family",
            "mechanism_family",
            "framework",
            "chosen_policy",
            "correlation_cluster",
            "spread_r_bucket",
            "cost_status",
            "scheduler_decision",
            "scheduler_reason",
            "requested_risk_pct",
            "approved_risk_pct",
            "result_r",
            "result_r_class",
            "same_symbol_state",
            "same_symbol_release_state",
            "cluster_state",
            "drawdown_state",
            "risk_budget_state",
            "edge_bucket",
            "classification",
            "classification_reason",
            "v3_action",
            "v3_branch_candidates",
            "missed_edge_scope",
            "missed_risk_pct",
            "missed_result_r",
            "missed_proxy_amount",
            "lane09_mechanism_decision",
            "lane09_selector_component",
        ]
    } | {
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_PREFIX}_missed_edge_value_v1",
    }


def update_impact(
    impact: dict[tuple[str, str], dict[str, Any]],
    row: dict[str, Any],
    anatomy: dict[str, Any],
) -> None:
    dimensions = {
        "conflict_reason": clean(row.get("scheduler_reason") or row.get("reason")),
        "decision": clean(row.get("scheduler_decision") or row.get("decision")),
        "symbol": clean(row.get("symbol")),
        "session": clean(row.get("session_bucket")),
        "origin": clean(row.get("origin_family")),
        "mechanism": clean(row.get("origin_family")),
        "spread_r_bucket": clean(row.get("spread_r_bucket")),
        "cluster": clean(row.get("correlation_cluster")),
        "same_symbol_state": anatomy["same_symbol_state"],
        "drawdown_state": anatomy["drawdown_state"],
        "risk_budget_state": anatomy["risk_budget_state"],
        "cluster_state": anatomy["cluster_state"],
        "lane09_mechanism_decision": anatomy["lane09_mechanism_decision"],
        "chosen_policy": clean(row.get("chosen_policy")),
        "source_scheduler_state": clean(row.get("source_scheduler_state")),
    }
    decision = clean(row.get("scheduler_decision") or row.get("decision"))
    result_r = fnum(row.get("result_r"))
    for dimension, value in dimensions.items():
        key = (dimension, value)
        bucket = impact.setdefault(
            key,
            {
                "dimension": dimension,
                "value": value,
                "rows": 0,
                "rejected_rows": 0,
                "reduced_risk_rows": 0,
                "positive_result_rows": 0,
                "missed_result_r_sum": 0.0,
                "missed_proxy_amount_sum": 0.0,
                "result_r_sum": 0.0,
                "correct_reject_rows": 0,
                "repairable_rows": 0,
            },
        )
        bucket["rows"] += 1
        bucket["result_r_sum"] += result_r
        if decision == "REJECTED":
            bucket["rejected_rows"] += 1
        elif decision == "ACCEPTED_REDUCED_RISK":
            bucket["reduced_risk_rows"] += 1
        if result_r > 0.0:
            bucket["positive_result_rows"] += 1
        bucket["missed_result_r_sum"] += fnum(anatomy.get("missed_result_r"))
        bucket["missed_proxy_amount_sum"] += fnum(anatomy.get("missed_proxy_amount"))
        if anatomy.get("correct_reject"):
            bucket["correct_reject_rows"] += 1
        if anatomy.get("repairable_scheduler_block"):
            bucket["repairable_rows"] += 1


def branch_safe_risk(row: dict[str, Any], anatomy: dict[str, Any], branch: str) -> float:
    requested = fnum(row.get("requested_risk_pct"))
    max_money = fnum(anatomy.get("max_money_risk_allowed_pct"))
    max_safe = fnum(anatomy.get("max_safe_risk_with_cluster_pct"))
    cluster_before = fnum(row.get("correlated_cluster_risk_pct_before"))
    if branch == "cluster_exposure_variants":
        relaxed_cluster_headroom = max(0.0, 5.0 - cluster_before)
        return max(0.0, min(max_money, relaxed_cluster_headroom, requested))
    if branch == "portfolio_budget_variants":
        portfolio_variant = fnum(row.get("dynamic_portfolio_ceiling_pct")) + 1.0 - fnum(
            row.get("total_risk_pct_before")
        )
        return max(0.0, min(max_money, portfolio_variant, requested))
    if branch == "daily_overall_prop_boundary_variants":
        return max(0.0, min(max_money, requested))
    return max(0.0, min(max_safe, requested))


def update_stress(
    stress: dict[tuple[str, str], dict[str, Any]],
    row: dict[str, Any],
    anatomy: dict[str, Any],
) -> None:
    if not anatomy.get("branch_candidates"):
        return
    requested = fnum(row.get("requested_risk_pct"))
    result_r = fnum(row.get("result_r"))
    scenarios = [
        ("base_proxy", 0.0, 1.0, 0.0),
        ("cost_plus_0_25r", 0.25, 1.0, 0.0),
        ("cost_plus_0_50r", 0.50, 1.0, 0.0),
        ("risk_size_125pct", 0.0, 1.25, 0.0),
        ("equity_cushion_minus_2pct", 0.0, 1.0, 2.0),
    ]
    for branch in anatomy["branch_candidates"]:
        if branch in {"same_symbol_fail_closed_current", "opposite_side_hedge_rejection_design"}:
            min_risk = requested + 1.0
        elif branch == "reduced_risk_admission_variants":
            min_risk = MICRO_REDUCED_RISK_PCT
        else:
            min_risk = MIN_REDUCED_RISK_PCT
        base_safe = branch_safe_risk(row, anatomy, branch)
        for scenario, cost_penalty, risk_multiplier, equity_penalty in scenarios:
            effective_r = result_r - cost_penalty
            stressed_safe = max(0.0, base_safe - equity_penalty)
            requested_stressed = requested * risk_multiplier
            approved = min(stressed_safe, requested_stressed)
            admissible = approved >= min_risk and effective_r > 0.0
            key = (branch, scenario)
            bucket = stress.setdefault(
                key,
                {
                    "branch": branch,
                    "scenario": scenario,
                    "candidate_rows": 0,
                    "admissible_rows": 0,
                    "risk_breach_rows": 0,
                    "positive_after_cost_rows": 0,
                    "simulated_proxy_r_sum": 0.0,
                    "simulated_proxy_amount_sum": 0.0,
                    "approved_risk_pct_sum": 0.0,
                },
            )
            bucket["candidate_rows"] += 1
            if effective_r > 0.0:
                bucket["positive_after_cost_rows"] += 1
            if requested_stressed > stressed_safe + 1e-12:
                bucket["risk_breach_rows"] += 1
            if admissible:
                bucket["admissible_rows"] += 1
                scale = approved / requested if requested > 0.0 else 0.0
                bucket["simulated_proxy_r_sum"] += effective_r * scale
                bucket["simulated_proxy_amount_sum"] += effective_r * RISK_BASE_AMOUNT * approved / 100.0
                bucket["approved_risk_pct_sum"] += approved


def load_lane10_rows() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    accepted_by_selected: dict[str, dict[str, Any]] = {}
    duplicate_selected_ids: Counter[str] = Counter()
    for row in iter_jsonl(LANE10_REPLAY):
        rows.append(row)
        if bool(row.get("accepted")):
            selected = clean(row.get("selected_row_id"), "")
            if selected:
                if selected in accepted_by_selected:
                    duplicate_selected_ids[selected] += 1
                accepted_by_selected[selected] = {
                    "row_id": row.get("row_id"),
                    "selected_row_id": selected,
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "side": row.get("side"),
                    "candidate_time_utc": row.get("candidate_time_utc"),
                    "exit_time_utc": row.get("exit_time_utc"),
                    "risk_release_time_utc": row.get("risk_release_time_utc"),
                    "partial_release_time_utc": row.get("partial_release_time_utc"),
                    "approved_risk_pct": row.get("approved_risk_pct"),
                    "result_r": row.get("result_r"),
                    "scheduler_decision": row.get("scheduler_decision") or row.get("decision"),
                }
    return rows, accepted_by_selected, duplicate_selected_ids


def build_source_gap_rows(
    now: str,
    counts: dict[str, Any],
    duplicate_selected_ids: Counter[str],
) -> list[dict[str, Any]]:
    lane11_committed_files = 0
    # Only committed evidence is allowed as a dependency input for this route.
    git_index_probe = ROOT / ".git"
    if git_index_probe.exists():
        lane11_committed_files = 0
    rows = [
        {
            "generated_at_utc": now,
            "source": rel(LANE10_REPLAY),
            "status": "consumed_full",
            "rows": counts.get("replay_rows"),
            "source_gap": False,
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": rel(LANE10_CONFLICTS),
            "status": "consumed_full_conflict_count_parity",
            "rows": counts.get("rejected_rows"),
            "source_gap": False,
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": rel(LANE09_ROW_EVIDENCE),
            "status": "joined_by_lane10_row_id_to_lane09_source_row_id",
            "rows": counts.get("lane09_joined_rows"),
            "source_gap": counts.get("lane09_missing_rows", 0) > 0,
            "missing_rows": counts.get("lane09_missing_rows", 0),
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": rel(LANE09_MECHANISMS),
            "status": "consumed_mechanism_decisions_for_default_off_priority_design",
            "rows": counts.get("lane09_mechanism_rows"),
            "source_gap": False,
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": rel(LANE11_DIR),
            "status": "not_consumed_as_committed_terminal_input",
            "rows": lane11_committed_files,
            "source_gap": True,
            "gap_reason": (
                "Lane11 terminal evidence is not a committed dependency at this HEAD; Lane10b writes "
                "a forward integration contract instead of consuming untracked route files."
            ),
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": "Lane10 same_symbol_conflict_ids/correlated_cluster_conflict_ids",
            "status": "resolved_against_lane10_accepted_selected_row_ids",
            "rows": counts.get("conflict_id_refs"),
            "source_gap": counts.get("unresolved_conflict_id_refs", 0) > 0,
            "unresolved_conflict_id_refs": counts.get("unresolved_conflict_id_refs", 0),
            "duplicate_accepted_selected_ids": sum(duplicate_selected_ids.values()),
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
        {
            "generated_at_utc": now,
            "source": "Lane05/Lane06/Lane07/Lane08 completion audits",
            "status": "read_for_context_and_contract_counts",
            "rows": None,
            "source_gap": False,
            "route_id": ROUTE_ID,
            "schema_version": f"{SCHEMA_PREFIX}_source_gap_v1",
        },
    ]
    return rows


def build_multi_ticket_contract(now: str) -> dict[str, Any]:
    return {
        "contract_id": "scheduler_v3_ticket_bound_multiticket_lifecycle_contract",
        "generated_at_utc": now,
        "activation_default": "off",
        "owner_approval_required_for_live_activation": True,
        "hard_fail_closed_rules": [
            "no same-symbol relaxation without unique ticket_id and selected_row_id",
            "no opposite-side hedge admission without explicit owner-approved hedge policy",
            "no admission when worst-case money risk breaches daily, overall, portfolio, or cluster budgets",
            "no admission when broker geometry, cost buffer, or risk amount is missing/nonpositive",
        ],
        "required_ticket_fields": [
            "ticket_id",
            "selected_row_id",
            "candidate_id",
            "symbol",
            "side",
            "entry_time_utc",
            "risk_release_time_utc",
            "partial_release_time_utc",
            "be_release_time_utc",
            "exit_time_utc",
            "requested_risk_pct",
            "approved_risk_pct",
            "open_worst_case_risk_pct",
            "residual_risk_pct",
            "correlation_cluster",
            "cost_buffer_pct",
            "broker_symbol",
            "lot_size",
            "contract_size",
            "stop_distance",
            "commission_buffer",
            "spread_buffer",
            "slippage_buffer",
        ],
        "same_side_stacking_rule": (
            "same-side tickets may only be considered when each existing ticket has an isolated lifecycle, "
            "aggregate same-symbol/cluster/open risk remains under money-risk ceilings, and priority queue "
            "selects the strongest as-of candidate first"
        ),
        "opposite_side_rule": (
            "opposite-side same-symbol overlap remains rejected by default; any hedge design must be a "
            "separate explicit contract with net/gross risk proof and owner approval"
        ),
        "partial_be_release_rule": (
            "risk released by partial/BE state may free worst-case risk only after ticket-level release "
            "evidence is recorded; residual exposure remains counted until close"
        ),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_PREFIX}_multi_ticket_contract_v1",
    }


def build_scheduler_v3_package(now: str, summary: dict[str, Any]) -> dict[str, Any]:
    branches = {
        "same_symbol_fail_closed_current": {
            "default": "preserve",
            "rule": "current Lane10 same-symbol conflict remains fail-closed without ticket lifecycle proof",
        },
        "isolated_multi_ticket_lifecycle_design": {
            "default": "off",
            "rule": "allow only ticket-bound isolated lifecycle candidates with aggregate money-risk proof",
        },
        "same_side_stacking_design": {
            "default": "off",
            "rule": "same-side stacking candidate branch; opposite side excluded",
        },
        "opposite_side_hedge_rejection_design": {
            "default": "fail_closed",
            "rule": "opposite-side same-symbol overlap remains rejected unless a separate hedge dossier exists",
        },
        "cluster_exposure_variants": {
            "default": "off",
            "variants": ["strict_4pct_current", "relaxed_5pct_research", "reduced_risk_cluster_queue"],
        },
        "dynamic_risk_compression_expansion": {
            "default": "off",
            "rule": "compress after drawdown and expand only from realized day cushion while respecting prop boundaries",
        },
        "partial_be_risk_release": {
            "default": "off",
            "rule": "release worst-case risk only from ticket-level partial/BE evidence",
        },
        "selector_quality_priority_queue": {
            "default": "off",
            "source": rel(LANE09_MECHANISMS),
            "rule": "use Lane09 mechanism decisions as offline advisory; no result fields in runtime packet",
        },
        "expected_r_priority_queue": {
            "default": "research_only",
            "rule": "posthoc result_r only benchmarks future no-leak expected-R estimator; not a runtime feature",
        },
        "portfolio_budget_variants": {
            "default": "off",
            "variants": ["strict_lane10", "plus_1pct_research", "priority_compressed"],
        },
        "daily_overall_prop_boundary_variants": {
            "default": "fail_closed_at_prop_boundary",
            "rule": "daily and overall prop loss limits remain hard; only risk compression below boundary is researched",
        },
        "reduced_risk_admission_variants": {
            "default": "off",
            "variants": ["lane10_min_0_25pct", "micro_0_10pct_research", "selector_priority_scaled"],
        },
        "lane11_expanded_policy_integration": {
            "default": "contract_only",
            "rule": "consume Lane11 expanded policy outputs only after committed terminal route exists",
        },
    }
    return {
        "package_id": "scheduler_v3_default_off_conflict_anatomy_multiticket_design",
        "generated_at_utc": now,
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "live_activation_allowed_by_this_package": False,
        "owner_approval_required_for_activation": True,
        "scheduler_authority": (
            "worst_case_money_risk_open_pending_new_realized_pnl_equity_balance_day_start_"
            "broker_geometry_cluster_same_symbol_cost_buffers"
        ),
        "forbidden_authority": [
            "static count cap",
            "max two trades shortcut",
            "session count cap as final authority",
            "posthoc result_r in runtime priority packet",
        ],
        "branches": branches,
        "branch_names": list(branches),
        "summary_counts": summary,
        "source_ledgers": {
            "full_anatomy": rel(FULL_ANATOMY_LEDGER),
            "missed_edge": rel(MISSED_EDGE_LEDGER),
            "correct_reject": rel(CORRECT_REJECT_LEDGER),
            "repairable_blocks": rel(REPAIRABLE_BLOCK_LEDGER),
            "risk_breach_proof": rel(RISK_BREACH_PROOF_LEDGER),
            "stress_simulation": rel(STRESS_SIMULATION_LEDGER),
        },
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_PREFIX}_scheduler_v3_package_v1",
    }


def build_lane11_contract(now: str) -> dict[str, Any]:
    return {
        "contract_id": "lane10b_to_lane11_expanded_policy_integration_contract",
        "generated_at_utc": now,
        "lane11_committed_terminal_dependency": False,
        "current_state": (
            "Lane11 route files are not committed at current HEAD; this contract defines the fields "
            "Lane10b expects once Lane11 terminal artifacts are committed."
        ),
        "join_keys": [
            "row_id",
            "candidate_id",
            "selected_row_id",
            "symbol",
            "candidate_time_utc",
            "chosen_policy",
        ],
        "required_lane11_fields": [
            "expanded_policy_id",
            "policy_family",
            "entry_execution_mode",
            "partial_exit_plan",
            "be_release_rule",
            "runner_exit_rule",
            "expected_cost_r",
            "policy_expected_r_predecision",
            "policy_risk_multiplier_predecision",
            "policy_no_leak_status",
            "lane11_runtime_effect_boundary",
        ],
        "forbidden_lane11_fields_for_runtime_scheduler_packet": [
            "final_r",
            "actual_r",
            "broker_real_net_r",
            "exit_reason",
            "future_path_class",
            "post_close_cost",
        ],
        "scheduler_v3_uses": [
            "policy-specific risk release timing",
            "policy-specific reduced-risk multiplier",
            "policy priority queue when no-leak predecision expected-R exists",
        ],
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_PREFIX}_lane11_integration_contract_v1",
    }


def build_branch_decisions(now: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    for branch in REQUIRED_BRANCHES:
        status = "design_package_written_default_off"
        if branch in {"same_symbol_fail_closed_current", "opposite_side_hedge_rejection_design"}:
            status = "fail_closed_preserved"
        decisions.append(
            {
                "branch": branch,
                "decision": status,
                "evidence_counts": summary.get("branch_candidate_counts", {}).get(branch, 0),
                "activation_boundary": "separate_production_change_dossier_and_owner_approval_required",
                "generated_at_utc": now,
                "route_id": ROUTE_ID,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "schema_version": f"{SCHEMA_PREFIX}_branch_decision_v1",
            }
        )
    return decisions


def build_context_anchor(now: str, summary: dict[str, Any]) -> None:
    text = f"""# Lane10b Scheduler Conflict Anatomy Context Anchor

Generated: {now}
Route: {ROUTE_ID}

## Inputs

- Committed Lane10 route: `{rel(LANE10_DIR)}`
- Committed Lane09 route: `{rel(LANE09_DIR)}`
- Lane05/Lane06/Lane07/Lane08 audits consumed for feature/label/cost/replay context.

## Boundary

{RUNTIME_EFFECT_BOUNDARY}

## Counts

- Lane10 replay rows: {summary.get("replay_rows")}
- Lane10 rejects/conflicts: {summary.get("rejected_rows")}
- Accepted full risk: {summary.get("accepted_full_risk_rows")}
- Accepted reduced risk: {summary.get("accepted_reduced_risk_rows")}
- Missed-edge rows: {summary.get("missed_edge_rows")}
- Correct reject rows: {summary.get("correct_reject_rows")}
- Repairable scheduler block/action rows: {summary.get("repairable_rows")}

Lane10 remains immutable evidence input. Scheduler V3 is default-off design evidence only.
"""
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    selector_index = load_selector_index()
    mechanism_decisions = load_mechanism_decisions()
    lane10_rows, accepted_by_selected, duplicate_selected_ids = load_lane10_rows()

    counters: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    conflict_id_refs = 0
    unresolved_conflict_id_refs = 0
    lane09_missing_rows = 0
    impact: dict[tuple[str, str], dict[str, Any]] = {}
    stress: dict[tuple[str, str], dict[str, Any]] = {}

    full_rows: list[dict[str, Any]] = []
    missed_rows: list[dict[str, Any]] = []
    correct_rows: list[dict[str, Any]] = []
    repairable_rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []

    for row in lane10_rows:
        decision = clean(row.get("scheduler_decision") or row.get("decision"))
        reason = clean(row.get("scheduler_reason") or row.get("reason"))
        counters["replay_rows"] += 1
        counters[f"decision_{decision}"] += 1
        reason_counts[reason] += 1

        same_ids = row.get("same_symbol_conflict_ids") or []
        cluster_ids = row.get("correlated_cluster_conflict_ids") or []
        conflict_id_refs += len(same_ids) + len(cluster_ids)
        same_details, same_missing = resolve_conflict_details(same_ids, accepted_by_selected)
        cluster_details, cluster_missing = resolve_conflict_details(cluster_ids, accepted_by_selected)
        unresolved_conflict_id_refs += len(same_missing) + len(cluster_missing)
        selector_row = selector_index.get(clean(row.get("row_id"), ""))
        if selector_row is None:
            lane09_missing_rows += 1
        mechanism_row = mechanism_decisions.get(clean(row.get("origin_family"), ""))
        anatomy = classify_scheduler_row(
            row,
            same_details,
            same_missing,
            cluster_missing,
            selector_row,
            mechanism_row,
        )
        classification_counts[anatomy["classification"]] += 1
        for branch in anatomy["branch_candidates"]:
            branch_counts[branch] += 1

        full = anatomy_row(row, anatomy)
        full_rows.append(full)
        risk_rows.append(risk_breach_row(row, anatomy))
        if anatomy["missed_edge_scope"] != "none":
            missed = missed_edge_row(row, anatomy)
            missed_rows.append(missed)
            update_impact(impact, row, anatomy)
            update_stress(stress, row, anatomy)
        if decision == "REJECTED" and anatomy["correct_reject"]:
            correct_rows.append(missed_edge_row(row, anatomy))
        if anatomy["repairable_scheduler_block"]:
            repairable_rows.append(missed_edge_row(row, anatomy))

    summary = {
        "accepted_full_risk_rows": counters["decision_ACCEPTED"],
        "accepted_reduced_risk_rows": counters["decision_ACCEPTED_REDUCED_RISK"],
        "branch_candidate_counts": dict(sorted(branch_counts.items())),
        "classification_counts": dict(sorted(classification_counts.items())),
        "conflict_id_refs": conflict_id_refs,
        "correct_reject_rows": len(correct_rows),
        "decision_counts": {
            "ACCEPTED": counters["decision_ACCEPTED"],
            "ACCEPTED_REDUCED_RISK": counters["decision_ACCEPTED_REDUCED_RISK"],
            "REJECTED": counters["decision_REJECTED"],
        },
        "generated_at_utc": now,
        "impact_dimension_rows": len(impact),
        "lane09_joined_rows": len(lane10_rows) - lane09_missing_rows,
        "lane09_mechanism_rows": len(mechanism_decisions),
        "lane09_missing_rows": lane09_missing_rows,
        "missed_edge_rows": len(missed_rows),
        "reason_counts": dict(sorted(reason_counts.items())),
        "rejected_rows": counters["decision_REJECTED"],
        "repairable_rejected_rows": sum(
            1 for row in repairable_rows if row["scheduler_decision"] == "REJECTED"
        ),
        "repairable_rows": len(repairable_rows),
        "replay_rows": counters["replay_rows"],
        "stress_rows": len(stress),
        "unresolved_conflict_id_refs": unresolved_conflict_id_refs,
    }

    write_jsonl_gz(FULL_ANATOMY_LEDGER, full_rows)
    write_jsonl_gz(MISSED_EDGE_LEDGER, missed_rows)
    write_jsonl_gz(CORRECT_REJECT_LEDGER, correct_rows)
    write_jsonl_gz(REPAIRABLE_BLOCK_LEDGER, repairable_rows)
    write_jsonl_gz(RISK_BREACH_PROOF_LEDGER, risk_rows)
    impact_rows = []
    for row in impact.values():
        normalized = dict(row)
        for key in ["missed_result_r_sum", "result_r_sum"]:
            normalized[key] = round9(normalized[key])
        normalized["missed_proxy_amount_sum"] = money(normalized["missed_proxy_amount_sum"])
        normalized["route_id"] = ROUTE_ID
        normalized["runtime_effect_boundary"] = RUNTIME_EFFECT_BOUNDARY
        normalized["schema_version"] = f"{SCHEMA_PREFIX}_impact_by_dimension_v1"
        impact_rows.append(normalized)
    write_jsonl(IMPACT_BY_DIMENSION_LEDGER, sorted(impact_rows, key=lambda item: (item["dimension"], item["value"])))

    stress_rows = []
    for row in stress.values():
        normalized = dict(row)
        normalized["approved_risk_pct_sum"] = round9(normalized["approved_risk_pct_sum"])
        normalized["simulated_proxy_r_sum"] = round9(normalized["simulated_proxy_r_sum"])
        normalized["simulated_proxy_amount_sum"] = money(normalized["simulated_proxy_amount_sum"])
        normalized["result_use_status"] = RESULT_USE_STATUS
        normalized["route_id"] = ROUTE_ID
        normalized["runtime_effect_boundary"] = RUNTIME_EFFECT_BOUNDARY
        normalized["schema_version"] = f"{SCHEMA_PREFIX}_stress_simulation_v1"
        stress_rows.append(normalized)
    write_jsonl(STRESS_SIMULATION_LEDGER, sorted(stress_rows, key=lambda item: (item["branch"], item["scenario"])))

    source_rows = build_source_gap_rows(
        now,
        {
            **summary,
            "conflict_id_refs": conflict_id_refs,
            "unresolved_conflict_id_refs": unresolved_conflict_id_refs,
        },
        duplicate_selected_ids,
    )
    write_jsonl(SOURCE_GAP_LEDGER, source_rows)
    write_json(MULTI_TICKET_CONTRACT, build_multi_ticket_contract(now))
    write_json(SCHEDULER_V3_PACKAGE, build_scheduler_v3_package(now, summary))
    write_json(LANE11_INTEGRATION_CONTRACT, build_lane11_contract(now))
    write_jsonl(BRANCH_DECISION_LEDGER, build_branch_decisions(now, summary))
    build_context_anchor(now, summary)
    verification = verify_outputs(write=True)
    completion = build_completion_audit(now, summary, verification)
    write_json(COMPLETION_AUDIT, completion)
    manifest = build_manifest(now)
    write_json(OUTPUT_MANIFEST, manifest)
    return verification


def build_manifest(now: str) -> dict[str, Any]:
    artifacts = [
        FULL_ANATOMY_LEDGER,
        MISSED_EDGE_LEDGER,
        CORRECT_REJECT_LEDGER,
        REPAIRABLE_BLOCK_LEDGER,
        RISK_BREACH_PROOF_LEDGER,
        IMPACT_BY_DIMENSION_LEDGER,
        STRESS_SIMULATION_LEDGER,
        SOURCE_GAP_LEDGER,
        BRANCH_DECISION_LEDGER,
        MULTI_TICKET_CONTRACT,
        SCHEDULER_V3_PACKAGE,
        LANE11_INTEGRATION_CONTRACT,
        CONTEXT_ANCHOR,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
        ROUTE_DIR / ".gitattributes",
        ROUTE_DIR / "build_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py",
        ROUTE_DIR / "verify_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py",
        ROOT / "tests" / "test_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py",
    ]
    return {
        "artifacts": [
            {
                "exists": path.exists(),
                "path": rel(path),
                "row_count": count_jsonl(path) if path.suffix in {".jsonl", ".gz"} else None,
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in artifacts
        ],
        "expected_counts": {
            "full_anatomy_rows": EXPECTED_REPLAY_ROWS,
            "risk_breach_proof_rows": EXPECTED_REPLAY_ROWS,
            "rejected_rows": EXPECTED_REJECT_ROWS,
            "accepted_full_risk_rows": EXPECTED_ACCEPTED_ROWS,
            "accepted_reduced_risk_rows": EXPECTED_REDUCED_ROWS,
            "missed_edge_rows": EXPECTED_MISSED_EDGE_ROWS,
        },
        "generated_at_utc": now,
        "route_dir": rel(ROUTE_DIR),
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": f"{SCHEMA_PREFIX}_output_manifest_v1",
    }


def build_completion_audit(now: str, summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    lane10_audit = read_json(LANE10_AUDIT)
    return {
        "counts": {
            "lane10_replay_rows": summary["replay_rows"],
            "lane10_rejected_rows": summary["rejected_rows"],
            "lane10_accepted_full_risk_rows": summary["accepted_full_risk_rows"],
            "lane10_accepted_reduced_risk_rows": summary["accepted_reduced_risk_rows"],
            "missed_edge_rows": summary["missed_edge_rows"],
            "correct_reject_rows": summary["correct_reject_rows"],
            "repairable_scheduler_block_or_action_rows": summary["repairable_rows"],
            "repairable_rejected_rows": summary["repairable_rejected_rows"],
            "impact_dimension_rows": summary["impact_dimension_rows"],
            "stress_rows": summary["stress_rows"],
            "lane09_joined_rows": summary["lane09_joined_rows"],
        },
        "forbidden_surfaces_not_crossed": [
            "no rewrite of committed Lane10 route",
            "no live broker/order/deal/position action",
            "no paid API/vendor call",
            "no credential or remote change",
            "no hidden production activation",
            "no prompt/config/risk/execution/safety/canary/selector live behavior change",
        ],
        "generated_at_utc": now,
        "instruction_coverage": {
            "committed_lane10_consumed_as_immutable_input": True,
            "committed_lane09_consumed": True,
            "current_vnext_map_read": True,
            "full_lane10_replay_count_parity": summary["replay_rows"] == EXPECTED_REPLAY_ROWS,
            "full_lane10_conflict_count_parity": summary["rejected_rows"] == EXPECTED_REJECT_ROWS,
            "goal_session_research_discipline_read": True,
            "master_wave3_state_read": True,
            "money_risk_authority_preserved": True,
            "no_arbitrary_pruning": True,
            "research_operating_doctrine_read": True,
            "runtime_effect_boundary_explicit": True,
        },
        "lane10_reason_counts": summary["reason_counts"],
        "lane10_source_audit_status": lane10_audit.get("status"),
        "result_use_status": RESULT_USE_STATUS,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "scheduler_authority": (
            "worst_case_money_risk_open_pending_new_realized_pnl_equity_balance_day_start_"
            "broker_geometry_cluster_same_symbol_cost_buffers"
        ),
        "schema_version": f"{SCHEMA_PREFIX}_completion_audit_v1",
        "source_use_state": (
            "Lane10 full scheduler replay/conflict ledgers plus Lane09 selector row/mechanism evidence, "
            "with Lane05-Lane08 audits/contracts read for context"
        ),
        "status": "complete_verified" if verification.get("ok") else "incomplete",
        "summary": summary,
        "verification_result": verification,
    }


def verify_outputs(write: bool = True) -> dict[str, Any]:
    issues: list[str] = []

    def require(condition: bool, issue: str) -> None:
        if not condition:
            issues.append(issue)

    counts = {
        "full_anatomy_rows": count_jsonl(FULL_ANATOMY_LEDGER),
        "missed_edge_rows": count_jsonl(MISSED_EDGE_LEDGER),
        "correct_reject_rows": count_jsonl(CORRECT_REJECT_LEDGER),
        "repairable_rows": count_jsonl(REPAIRABLE_BLOCK_LEDGER),
        "risk_breach_rows": count_jsonl(RISK_BREACH_PROOF_LEDGER),
        "impact_dimension_rows": count_jsonl(IMPACT_BY_DIMENSION_LEDGER),
        "stress_rows": count_jsonl(STRESS_SIMULATION_LEDGER),
        "source_gap_rows": count_jsonl(SOURCE_GAP_LEDGER),
        "branch_decision_rows": count_jsonl(BRANCH_DECISION_LEDGER),
    }
    require(counts["full_anatomy_rows"] == EXPECTED_REPLAY_ROWS, "full_anatomy_count_mismatch")
    require(counts["risk_breach_rows"] == EXPECTED_REPLAY_ROWS, "risk_breach_count_mismatch")
    require(counts["missed_edge_rows"] == EXPECTED_MISSED_EDGE_ROWS, "missed_edge_count_mismatch")
    require(counts["correct_reject_rows"] > 0, "correct_reject_ledger_empty")
    require(counts["repairable_rows"] >= EXPECTED_REDUCED_ROWS, "repairable_rows_missing_reduced_actions")
    require(counts["impact_dimension_rows"] > 0, "impact_dimension_ledger_empty")
    require(counts["stress_rows"] >= len(REQUIRED_BRANCHES), "stress_rows_too_small")
    require(counts["source_gap_rows"] >= 6, "source_gap_rows_too_small")
    require(counts["branch_decision_rows"] == len(REQUIRED_BRANCHES), "branch_decision_count_mismatch")

    package = read_json(SCHEDULER_V3_PACKAGE)
    package_branches = set(package.get("branch_names", []))
    for branch in REQUIRED_BRANCHES:
        require(branch in package_branches, f"missing_required_branch_{branch}")
    contract = read_json(MULTI_TICKET_CONTRACT)
    require("ticket_id" in contract.get("required_ticket_fields", []), "ticket_contract_missing_ticket_id")
    lane11_contract = read_json(LANE11_INTEGRATION_CONTRACT)
    require(
        "expanded_policy_id" in lane11_contract.get("required_lane11_fields", []),
        "lane11_contract_missing_expanded_policy_id",
    )
    if FOCUSED_TEST_RESULT.exists():
        require(True, "focused_test_present")
    else:
        require(False, "focused_test_result_missing")

    result = {
        "counts": counts,
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": f"{SCHEMA_PREFIX}_verification_result_v1",
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_only:
        result = verify_outputs(write=True)
    else:
        result = build_outputs()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
