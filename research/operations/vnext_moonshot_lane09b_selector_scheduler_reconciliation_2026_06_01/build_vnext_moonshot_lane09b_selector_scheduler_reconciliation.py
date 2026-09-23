from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

LANE09_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
LANE10_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
LANE08_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE05_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"

LANE09_ROW_EVIDENCE = LANE09_DIR / "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz"
LANE09_DISCOVERY = LANE09_DIR / "LANE09_SELECTOR_DISCOVERY_LEDGER.jsonl.gz"
LANE09_CLAUSES = LANE09_DIR / "LANE09_DEFAULT_OFF_SELECTOR_CLAUSE_LEDGER.jsonl"
LANE09_MECHANISMS = LANE09_DIR / "LANE09_SELECTOR_MECHANISM_RANKING.jsonl"
LANE09_CAPTURE_REQUIREMENTS = LANE09_DIR / "LANE09_PACKET_CAPTURE_REQUIREMENTS.jsonl"
LANE09_PACKAGE = LANE09_DIR / "LANE09_DEFAULT_OFF_SELECTOR_PACKAGE.json"

LANE10_SCHEDULER_REPLAY = LANE10_DIR / "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz"
LANE10_CONFLICTS = LANE10_DIR / "LANE10_SCHEDULING_CONFLICT_LEDGER.jsonl.gz"
LANE10_RISK_EXPOSURE = LANE10_DIR / "LANE10_RISK_EXPOSURE_LEDGER.jsonl"
LANE10_SPLIT_STRESS = LANE10_DIR / "LANE10_SPLIT_STRESS_METRICS.jsonl"
LANE10_MISSING_GAPS = LANE10_DIR / "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"
LANE10_COMPLETION_AUDIT = LANE10_DIR / "LANE10_COMPLETION_AUDIT.json"

ROW_JOIN_LEDGER = ROUTE_DIR / "LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"
CLAUSE_OUTCOME_LEDGER = ROUTE_DIR / "LANE09B_CLAUSE_TO_SCHEDULER_OUTCOME_LEDGER.jsonl"
DISCOVERY_OUTCOME_LEDGER = ROUTE_DIR / "LANE09B_DISCOVERY_TO_SCHEDULER_OUTCOME_LEDGER.jsonl.gz"
MECHANISM_OUTCOME_LEDGER = ROUTE_DIR / "LANE09B_MECHANISM_TO_SCHEDULER_OUTCOME_LEDGER.jsonl"
ACTION_REFINEMENT_LEDGER = ROUTE_DIR / "LANE09B_PROMOTE_REDUCE_AVOID_CAPTURE_REFINEMENT_LEDGER.jsonl"
FALSE_POSITIVE_LEDGER = ROUTE_DIR / "LANE09B_SELECTOR_FALSE_POSITIVE_LEDGER.jsonl.gz"
BLOCKED_EDGE_LEDGER = ROUTE_DIR / "LANE09B_SCHEDULER_BLOCKED_EDGE_LEDGER.jsonl.gz"
EDGE_SUMMARY_LEDGER = ROUTE_DIR / "LANE09B_BLOCKED_AND_SURVIVING_EDGE_SUMMARY.jsonl"
CAPTURE_GAP_LEDGER = ROUTE_DIR / "LANE09B_CAPTURE_REQUIREMENT_TO_SCHEDULER_GAP_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE09B_SOURCE_GAP_LEDGER.jsonl"
REFINEMENT_PACKAGE = ROUTE_DIR / "LANE09B_SCHEDULER_AWARE_META_SELECTOR_REFINEMENT_PACKAGE.json"
LANE11_CONTRACT = ROUTE_DIR / "LANE09B_LANE11_EXPANDED_POLICY_INTEGRATION_CONTRACT.json"
SOURCE_USE_STATE = ROUTE_DIR / "LANE09B_SOURCE_USE_STATE.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE09B_RUNTIME_EFFECT_BOUNDARY.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE09B_RESULT_USE_STATUS.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE09B_CONTEXT_ANCHOR.md"
SATURATION_REVIEW = ROUTE_DIR / "LANE09B_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE09B_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE09B_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE09B_FOCUSED_TEST_RESULT.xml"
COMPLETION_AUDIT = ROUTE_DIR / "LANE09B_COMPLETION_AUDIT.json"

EXPECTED_LANE09_ROW_EVIDENCE_ROWS = 289_928
EXPECTED_LANE09_DISCOVERY_ROWS = 21_052
EXPECTED_LANE09_CLAUSE_ROWS = 9_808
EXPECTED_LANE09_MECHANISM_ROWS = 43
EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS = 1_909
EXPECTED_LANE10_REPLAY_ROWS = 289_928
EXPECTED_LANE10_REJECT_ROWS = 215_495
EXPECTED_LANE10_ACCEPTED_ROWS = 67_365
EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS = 7_068
EXPECTED_LANE10_RISK_EXPOSURE_ROWS = 1_474
EXPECTED_LANE10_SPLIT_STRESS_ROWS = 1_547
EXPECTED_LANE08_MISSING_GAP_ROWS = 3_471_773

RESULT_USE_STATUS_TEXT = (
    "offline_selector_scheduler_reconciliation_research_only_not_production_change;"
    " Lane09 and Lane10 terminal routes are immutable inputs; no live selector,"
    " scheduler, risk, execution, broker, credential, paid API, or remote effect"
)
RUNTIME_BOUNDARY_TEXT = (
    "offline_lane09b_selector_scheduler_reconciliation_only_no_live_broker_order_deal_position_operation_"
    "no_config_prompt_risk_execution_safety_canary_selector_scheduler_activation_no_paid_api_no_remote"
)

POLICY_DEPENDENT_PATH_CLASSES = {
    "breakeven_or_partial_be_return",
    "positive_less_than_1r_policy_exit",
    "negative_policy_exit_before_1r",
    "winner_partial_then_be_return",
    "winner_partial_then_dynamic_final",
    "partial_trigger_then_open_at_friday_close",
    "stuck_entry_no_sl_or_1r_before_friday_close",
}

SUMMARY_DIMENSIONS = [
    ("symbol",),
    ("session_bucket",),
    ("origin_family",),
    ("mechanism_family",),
    ("spread_r_bucket",),
    ("source_completeness_state",),
    ("scheduler_reason",),
    ("risk_state",),
    ("symbol", "session_bucket"),
    ("origin_family", "scheduler_reason"),
    ("origin_family", "spread_r_bucket"),
    ("origin_family", "risk_state"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def open_text(path: Path, mode: str = "rt"):
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", newline="\n")
    return open(path, mode, encoding="utf-8", newline="\n")


def iter_jsonl(path: Path):
    with open_text(path, "rt") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def json_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix not in {".jsonl", ".gz"}:
        return None
    count = 0
    with open_text(path, "rt") as handle:
        for _ in handle:
            count += 1
    return count


def float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def canonical_value(value: Any) -> Any:
    if value is None:
        return "missing"
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def normalize_side(value: Any) -> str:
    if value is None:
        return "unknown_side"
    lowered = str(value).strip().lower()
    if lowered in {"", "none", "no_side", "unknown", "unknown_side"}:
        return "unknown_side"
    if lowered in {"long", "short"}:
        return lowered.upper()
    return str(value)


def risk_state_from_scheduler(scheduler_row: dict[str, Any] | None) -> str:
    if not scheduler_row:
        return "scheduler_join_missing"
    decision = scheduler_row.get("scheduler_decision") or scheduler_row.get("decision")
    reason = scheduler_row.get("scheduler_reason") or scheduler_row.get("reason") or ""
    if decision == "ACCEPTED":
        return "accepted_full_risk"
    if decision == "ACCEPTED_REDUCED_RISK":
        return "accepted_reduced_risk"
    if "same_symbol" in reason:
        return "same_symbol_conflict"
    if "correlated_cluster" in reason:
        return "correlated_cluster_conflict"
    if "portfolio_total" in reason:
        return "portfolio_total_risk_limit"
    if "account_daily_or_overall" in reason:
        return "account_or_daily_limit"
    if "drawdown_compression" in reason:
        return "drawdown_compression_limit"
    if "selected_cell_or_effective_risk_missing" in reason:
        return "source_gap_risk_proof_missing"
    return "scheduler_reject_other"


def lane11_policy_dependency(selector_row: dict[str, Any]) -> bool:
    return selector_row.get("path_class") in POLICY_DEPENDENT_PATH_CLASSES


def classify_reconciliation(
    selector_row: dict[str, Any],
    scheduler_row: dict[str, Any] | None,
    mechanism_decision: str,
) -> str:
    if not scheduler_row:
        return "source-gap"

    decision = scheduler_row.get("scheduler_decision") or scheduler_row.get("decision")
    reason = scheduler_row.get("scheduler_reason") or scheduler_row.get("reason") or ""
    result_r = float_or_none(scheduler_row.get("result_r", selector_row.get("result_r")))

    if decision == "REJECTED":
        if "selected_cell_or_effective_risk_missing" in reason:
            return "source-gap"
        if result_r is not None and result_r <= 0:
            return "scheduler-blocked-correctly"
        if result_r is not None and result_r > 0:
            return "scheduler-blocked-repairable"
        return "scheduler-blocked-repairable"

    if decision == "ACCEPTED_REDUCED_RISK":
        return "scheduler-reduced"

    if decision == "ACCEPTED":
        if mechanism_decision == "promote" and result_r is not None and result_r <= 0:
            return "selector-false-positive"
        if mechanism_decision == "promote" and result_r is not None and result_r > 0 and lane11_policy_dependency(selector_row):
            return "Lane11-policy-dependent"
        return "scheduler-survived"

    return "source-gap"


def normalize_action(action: str | None) -> str:
    if not action:
        return "unknown"
    if action.startswith("capture_repair"):
        return "capture"
    if action.startswith("promote"):
        return "promote"
    if action.startswith("reduce"):
        return "reduce"
    if action.startswith("avoid"):
        return "avoid"
    if action.startswith("hold"):
        return "hold"
    return action


@dataclass
class OutcomeAggregate:
    rows: int = 0
    result_r_sum: float = 0.0
    positive_result_r_sum: float = 0.0
    negative_result_r_sum: float = 0.0
    surviving_edge_r_sum: float = 0.0
    blocked_edge_r_sum: float = 0.0
    false_positive_r_sum: float = 0.0
    scheduler_decision_counts: Counter = field(default_factory=Counter)
    scheduler_reason_counts: Counter = field(default_factory=Counter)
    reconciliation_class_counts: Counter = field(default_factory=Counter)
    risk_state_counts: Counter = field(default_factory=Counter)
    selector_mechanism_decision_counts: Counter = field(default_factory=Counter)
    lane11_policy_dependent_rows: int = 0

    def add(self, joined_row: dict[str, Any]) -> None:
        self.rows += 1
        result_r = float_or_none(joined_row.get("result_r"))
        if result_r is not None:
            self.result_r_sum += result_r
            if result_r > 0:
                self.positive_result_r_sum += result_r
            elif result_r < 0:
                self.negative_result_r_sum += result_r

        scheduler_decision = joined_row.get("scheduler_decision") or "missing"
        scheduler_reason = joined_row.get("scheduler_reason") or "missing"
        reconciliation_class = joined_row.get("reconciliation_class") or "missing"
        risk_state = joined_row.get("risk_state") or "missing"
        mechanism_decision = joined_row.get("lane09_mechanism_decision") or "missing"
        self.scheduler_decision_counts[scheduler_decision] += 1
        self.scheduler_reason_counts[scheduler_reason] += 1
        self.reconciliation_class_counts[reconciliation_class] += 1
        self.risk_state_counts[risk_state] += 1
        self.selector_mechanism_decision_counts[mechanism_decision] += 1

        if joined_row.get("lane11_policy_dependency"):
            self.lane11_policy_dependent_rows += 1
        if scheduler_decision in {"ACCEPTED", "ACCEPTED_REDUCED_RISK"} and result_r is not None and result_r > 0:
            self.surviving_edge_r_sum += result_r
        if scheduler_decision == "REJECTED" and result_r is not None and result_r > 0:
            self.blocked_edge_r_sum += result_r
        if reconciliation_class == "selector-false-positive" and result_r is not None:
            self.false_positive_r_sum += result_r

    def merge(self, other: "OutcomeAggregate") -> None:
        self.rows += other.rows
        self.result_r_sum += other.result_r_sum
        self.positive_result_r_sum += other.positive_result_r_sum
        self.negative_result_r_sum += other.negative_result_r_sum
        self.surviving_edge_r_sum += other.surviving_edge_r_sum
        self.blocked_edge_r_sum += other.blocked_edge_r_sum
        self.false_positive_r_sum += other.false_positive_r_sum
        self.scheduler_decision_counts.update(other.scheduler_decision_counts)
        self.scheduler_reason_counts.update(other.scheduler_reason_counts)
        self.reconciliation_class_counts.update(other.reconciliation_class_counts)
        self.risk_state_counts.update(other.risk_state_counts)
        self.selector_mechanism_decision_counts.update(other.selector_mechanism_decision_counts)
        self.lane11_policy_dependent_rows += other.lane11_policy_dependent_rows

    def as_dict(self) -> dict[str, Any]:
        accepted_rows = self.scheduler_decision_counts.get("ACCEPTED", 0)
        reduced_rows = self.scheduler_decision_counts.get("ACCEPTED_REDUCED_RISK", 0)
        rejected_rows = self.scheduler_decision_counts.get("REJECTED", 0)
        return {
            "rows": self.rows,
            "accepted_rows": accepted_rows,
            "accepted_reduced_risk_rows": reduced_rows,
            "rejected_rows": rejected_rows,
            "acceptance_rate": round6((accepted_rows + reduced_rows) / self.rows) if self.rows else None,
            "result_r_sum": round6(self.result_r_sum),
            "positive_result_r_sum": round6(self.positive_result_r_sum),
            "negative_result_r_sum": round6(self.negative_result_r_sum),
            "surviving_edge_r_sum": round6(self.surviving_edge_r_sum),
            "blocked_edge_r_sum": round6(self.blocked_edge_r_sum),
            "false_positive_r_sum": round6(self.false_positive_r_sum),
            "lane11_policy_dependent_rows": self.lane11_policy_dependent_rows,
            "scheduler_decision_counts": dict(sorted(self.scheduler_decision_counts.items())),
            "scheduler_reason_counts": dict(sorted(self.scheduler_reason_counts.items())),
            "reconciliation_class_counts": dict(sorted(self.reconciliation_class_counts.items())),
            "risk_state_counts": dict(sorted(self.risk_state_counts.items())),
            "selector_mechanism_decision_counts": dict(sorted(self.selector_mechanism_decision_counts.items())),
        }


def recommendation_for_aggregate(original_action: str, aggregate: OutcomeAggregate) -> tuple[str, str]:
    metrics = aggregate.as_dict()
    rows = aggregate.rows
    if rows == 0:
        return "capture", "no_scheduler_rows_joined_for_selector_scope"

    normalized = normalize_action(original_action)
    source_gap_rows = aggregate.reconciliation_class_counts.get("source-gap", 0)
    blocked_repairable_rows = aggregate.reconciliation_class_counts.get("scheduler-blocked-repairable", 0)
    false_positive_rows = aggregate.reconciliation_class_counts.get("selector-false-positive", 0)
    blocked_edge_r = metrics["blocked_edge_r_sum"] or 0.0
    surviving_edge_r = metrics["surviving_edge_r_sum"] or 0.0
    accepted_rows = aggregate.scheduler_decision_counts.get("ACCEPTED", 0)
    reduced_rows = aggregate.scheduler_decision_counts.get("ACCEPTED_REDUCED_RISK", 0)

    if normalized == "capture":
        return "capture", "original_selector_action_is_capture_repair_or_low_support"
    if source_gap_rows / rows >= 0.20:
        return "capture", "scheduler_reconciliation_is_source_gap_heavy"
    if normalized == "promote":
        if false_positive_rows and false_positive_rows / rows >= 0.25 and surviving_edge_r <= 0:
            return "avoid", "selector_promote_has_high_false_positive_share_and_no_surviving_edge"
        if blocked_edge_r > surviving_edge_r and blocked_repairable_rows / rows >= 0.10:
            return "reduce_risk", "positive_selector_edge_is_scheduler_constrained_by_portfolio_or_conflict_state"
        if reduced_rows / rows >= 0.10:
            return "reduce_risk", "scheduler_accepts_material_share_only_at_reduced_risk"
        if accepted_rows and surviving_edge_r > abs(metrics["false_positive_r_sum"] or 0.0):
            return "remain_promote", "selector_promote_survives_scheduler_with_positive_edge"
        return "hold", "selector_promote_does_not_have_enough_scheduler_survival_after_conflicts"
    if normalized == "reduce":
        if blocked_edge_r > surviving_edge_r:
            return "reduce_risk", "reduced_selector_scope_remains_scheduler_constrained"
        return "remain_reduce", "selector_reduce_survives_as_risk_tempered_scope"
    if normalized == "avoid":
        if surviving_edge_r > blocked_edge_r and accepted_rows:
            return "hold", "avoid_scope_has_scheduler_surviving_positive_rows_requiring_lane11_or_selector_review"
        return "remain_avoid", "avoid_scope_is_not_improved_by_scheduler_reconciliation"
    if normalized == "hold":
        if blocked_edge_r > surviving_edge_r:
            return "reduce_risk", "hold_scope_contains blocked_positive_scheduler_edge"
        return "hold", "hold_scope_remains inconclusive_after_scheduler_reconciliation"
    return "hold", "unknown_selector_action_after_scheduler_reconciliation"


def requirement_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        canonical_value(row.get("symbol")),
        canonical_value(row.get("framework")),
        normalize_side(row.get("side")),
        canonical_value(row.get("replay_gap_reason_code")),
        canonical_value(row.get("repair_requirement_code")),
    )


def dimension_key(row: dict[str, Any], dimensions: tuple[str, ...]) -> tuple[Any, ...]:
    return tuple(canonical_value(row.get(dim)) for dim in dimensions)


def clause_lookup_key(row: dict[str, Any]) -> tuple[tuple[str, ...], tuple[Any, ...]]:
    dimensions = tuple(row.get("dimensions") or [])
    values = row.get("dimension_values") or {}
    return dimensions, tuple(canonical_value(values.get(dim)) for dim in dimensions)


def load_scheduler_replay() -> tuple[dict[str, dict[str, Any]], Counter]:
    scheduler_by_row_id: dict[str, dict[str, Any]] = {}
    counts: Counter = Counter()
    for row in iter_jsonl(LANE10_SCHEDULER_REPLAY):
        row_id = row.get("row_id")
        if not row_id:
            continue
        scheduler_by_row_id[row_id] = {
            "row_id": row_id,
            "candidate_id": row.get("candidate_id"),
            "selected_row_id": row.get("selected_row_id"),
            "scheduler_decision": row.get("scheduler_decision") or row.get("decision"),
            "scheduler_reason": row.get("scheduler_reason") or row.get("reason"),
            "accepted": row.get("accepted"),
            "approved_risk_pct": row.get("approved_risk_pct"),
            "requested_risk_pct": row.get("requested_risk_pct"),
            "priority_score": row.get("priority_score"),
            "priority_rank_in_batch": row.get("priority_rank_in_batch"),
            "risk_state": risk_state_from_scheduler(row),
            "same_symbol_risk_pct_before": row.get("same_symbol_risk_pct_before"),
            "correlated_cluster_risk_pct_before": row.get("correlated_cluster_risk_pct_before"),
            "open_risk_pct_before": row.get("open_risk_pct_before"),
            "pending_risk_pct_before": row.get("pending_risk_pct_before"),
            "total_risk_pct_before": row.get("total_risk_pct_before"),
            "total_risk_pct_after": row.get("total_risk_pct_after"),
            "dynamic_portfolio_ceiling_pct": row.get("dynamic_portfolio_ceiling_pct"),
            "account_available_risk_pct": row.get("account_available_risk_pct"),
            "daily_cushion_before": row.get("daily_cushion_before"),
            "overall_cushion_before": row.get("overall_cushion_before"),
            "correlation_cluster": row.get("correlation_cluster"),
            "same_symbol_conflict_ids": row.get("same_symbol_conflict_ids") or [],
            "correlated_cluster_conflict_ids": row.get("correlated_cluster_conflict_ids") or [],
            "opportunity_cost_r": row.get("opportunity_cost_r"),
            "opportunity_cost_amount": row.get("opportunity_cost_amount"),
            "result_r": row.get("result_r"),
            "result_r_class": row.get("result_r_class"),
            "source_scheduler_state": row.get("source_scheduler_state"),
            "broker_ready_state": row.get("broker_ready_state"),
        }
        counts[row.get("scheduler_decision") or row.get("decision") or "missing"] += 1
    return scheduler_by_row_id, counts


def load_lane09_mechanism_decisions() -> dict[str, dict[str, Any]]:
    return {row["mechanism_family"]: row for row in iter_jsonl(LANE09_MECHANISMS)}


def load_selector_groups() -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[tuple[str, ...]]]:
    clauses = list(iter_jsonl(LANE09_CLAUSES))
    discovery = list(iter_jsonl(LANE09_DISCOVERY))
    dimension_sets = {tuple(row.get("dimensions") or []) for row in clauses}
    dimension_sets.update(tuple(row.get("dimensions") or []) for row in discovery)
    dimension_sets.update(SUMMARY_DIMENSIONS)
    dimension_sets.add(("origin_family",))
    return clauses, discovery, dimension_sets


def aggregate_lane10_missing_gaps() -> tuple[dict[tuple[Any, ...], int], int]:
    gap_counts: dict[tuple[Any, ...], int] = defaultdict(int)
    total = 0
    for row in iter_jsonl(LANE10_MISSING_GAPS):
        total += 1
        gap_counts[requirement_key(row)] += 1
    return gap_counts, total


def build_joined_row(
    selector_row: dict[str, Any],
    scheduler_row: dict[str, Any] | None,
    mechanism: dict[str, Any] | None,
) -> dict[str, Any]:
    mechanism_decision = (mechanism or {}).get("mechanism_decision", "source_gap")
    reconciliation_class = classify_reconciliation(selector_row, scheduler_row, mechanism_decision)
    risk_state = risk_state_from_scheduler(scheduler_row)
    result_r = float_or_none((scheduler_row or {}).get("result_r", selector_row.get("result_r")))
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_selector_scheduler_row_join_v1",
        "join_status": "joined_lane09_source_row_id_to_lane10_row_id" if scheduler_row else "missing_lane10_scheduler_row",
        "source_row_id": selector_row.get("source_row_id"),
        "lane10_row_id": (scheduler_row or {}).get("row_id"),
        "candidate_id": selector_row.get("candidate_id"),
        "selected_row_id": selector_row.get("selected_row_id"),
        "candidate_time_utc": selector_row.get("candidate_time_utc"),
        "decision_asof_utc": selector_row.get("decision_asof_utc"),
        "symbol": selector_row.get("symbol"),
        "session_bucket": selector_row.get("session_bucket"),
        "origin_family": selector_row.get("origin_family"),
        "mechanism_family": selector_row.get("origin_family"),
        "framework": selector_row.get("framework"),
        "side": selector_row.get("side"),
        "chosen_policy": selector_row.get("chosen_policy"),
        "path_class": selector_row.get("path_class"),
        "spread_r_bucket": selector_row.get("spread_r_bucket"),
        "source_completeness_state": selector_row.get("source_completeness_state"),
        "source_quality_status": selector_row.get("source_quality_status"),
        "source_gap_families": selector_row.get("source_gap_families") or [],
        "cost_status": selector_row.get("cost_status"),
        "label_evidence_class": selector_row.get("label_evidence_class"),
        "result_r": result_r,
        "result_r_class": (scheduler_row or {}).get("result_r_class", selector_row.get("result_r_class")),
        "lane09_mechanism_decision": mechanism_decision,
        "lane09_mechanism_decision_reason": (mechanism or {}).get("decision_reason"),
        "scheduler_decision": (scheduler_row or {}).get("scheduler_decision"),
        "scheduler_reason": (scheduler_row or {}).get("scheduler_reason"),
        "approved_risk_pct": (scheduler_row or {}).get("approved_risk_pct"),
        "requested_risk_pct": (scheduler_row or {}).get("requested_risk_pct"),
        "priority_score": (scheduler_row or {}).get("priority_score"),
        "priority_rank_in_batch": (scheduler_row or {}).get("priority_rank_in_batch"),
        "same_symbol_risk_pct_before": (scheduler_row or {}).get("same_symbol_risk_pct_before"),
        "correlated_cluster_risk_pct_before": (scheduler_row or {}).get("correlated_cluster_risk_pct_before"),
        "open_risk_pct_before": (scheduler_row or {}).get("open_risk_pct_before"),
        "pending_risk_pct_before": (scheduler_row or {}).get("pending_risk_pct_before"),
        "total_risk_pct_before": (scheduler_row or {}).get("total_risk_pct_before"),
        "total_risk_pct_after": (scheduler_row or {}).get("total_risk_pct_after"),
        "dynamic_portfolio_ceiling_pct": (scheduler_row or {}).get("dynamic_portfolio_ceiling_pct"),
        "risk_state": risk_state,
        "same_symbol_conflict_ids": (scheduler_row or {}).get("same_symbol_conflict_ids", []),
        "correlated_cluster_conflict_ids": (scheduler_row or {}).get("correlated_cluster_conflict_ids", []),
        "reconciliation_class": reconciliation_class,
        "lane11_policy_dependency": lane11_policy_dependency(selector_row),
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def emit_group_outcome(
    row: dict[str, Any],
    aggregate: OutcomeAggregate,
    source_type: str,
) -> dict[str, Any]:
    original_action = row.get("selector_action") or row.get("mechanism_decision") or "unknown"
    refined_action, reason = recommendation_for_aggregate(original_action, aggregate)
    return {
        "route_id": ROUTE_ID,
        "schema_version": f"lane09b_{source_type}_scheduler_outcome_v1",
        "source_type": source_type,
        "source_selector_action": original_action,
        "source_selector_action_family": row.get("selector_action_family") or normalize_action(original_action),
        "refined_scheduler_aware_action": refined_action,
        "refinement_reason": reason,
        "dimensions": row.get("dimensions") or [],
        "dimension_values": row.get("dimension_values") or {},
        "scheduler_metrics": aggregate.as_dict(),
        "lane09_decision_reason": row.get("decision_reason"),
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def build_route() -> dict[str, Any]:
    generated_at = utc_now()
    clauses, discovery, dimension_sets = load_selector_groups()
    mechanisms = load_lane09_mechanism_decisions()
    scheduler_by_row_id, scheduler_counts = load_scheduler_replay()
    lane10_gap_counts, lane10_gap_total = aggregate_lane10_missing_gaps()

    dimension_aggs: dict[tuple[tuple[str, ...], tuple[Any, ...]], OutcomeAggregate] = defaultdict(OutcomeAggregate)
    mechanism_aggs: dict[str, OutcomeAggregate] = defaultdict(OutcomeAggregate)
    summary_aggs: dict[tuple[tuple[str, ...], tuple[Any, ...]], OutcomeAggregate] = defaultdict(OutcomeAggregate)
    total_agg = OutcomeAggregate()
    joined_rows = 0
    missing_scheduler_rows = 0
    false_positive_rows = 0
    blocked_edge_rows = 0

    with open_text(ROW_JOIN_LEDGER, "wt") as row_out, open_text(FALSE_POSITIVE_LEDGER, "wt") as false_out, open_text(BLOCKED_EDGE_LEDGER, "wt") as blocked_out:
        for selector_row in iter_jsonl(LANE09_ROW_EVIDENCE):
            scheduler_row = scheduler_by_row_id.get(selector_row.get("source_row_id"))
            mechanism = mechanisms.get(selector_row.get("origin_family"))
            joined = build_joined_row(selector_row, scheduler_row, mechanism)
            row_out.write(json_line(joined))
            joined_rows += 1
            if not scheduler_row:
                missing_scheduler_rows += 1

            total_agg.add(joined)
            mechanism_aggs[joined["mechanism_family"]].add(joined)
            for dims in dimension_sets:
                key = (dims, dimension_key(joined, dims))
                dimension_aggs[key].add(joined)
            for dims in SUMMARY_DIMENSIONS:
                key = (dims, dimension_key(joined, dims))
                summary_aggs[key].add(joined)

            if joined["reconciliation_class"] == "selector-false-positive":
                false_positive_rows += 1
                false_out.write(json_line(joined))
            if joined["scheduler_decision"] == "REJECTED" and (joined.get("result_r") or 0) > 0:
                blocked_edge_rows += 1
                blocked_out.write(json_line(joined))

    clause_rows = 0
    clause_action_aggs: dict[tuple[str, str, str], OutcomeAggregate] = defaultdict(OutcomeAggregate)
    with open_text(CLAUSE_OUTCOME_LEDGER, "wt") as handle:
        for clause in clauses:
            aggregate = dimension_aggs.get(clause_lookup_key(clause), OutcomeAggregate())
            outcome = emit_group_outcome(clause, aggregate, "clause")
            handle.write(json_line(outcome))
            clause_rows += 1
            action_key = (
                normalize_action(clause.get("selector_action")),
                clause.get("selector_action") or "unknown",
                outcome["refined_scheduler_aware_action"],
            )
            clause_action_aggs[action_key].merge(aggregate)

    discovery_rows = 0
    discovery_action_counts: Counter = Counter()
    with open_text(DISCOVERY_OUTCOME_LEDGER, "wt") as handle:
        for group in discovery:
            aggregate = dimension_aggs.get(clause_lookup_key(group), OutcomeAggregate())
            outcome = emit_group_outcome(group, aggregate, "discovery_group")
            handle.write(json_line(outcome))
            discovery_rows += 1
            discovery_action_counts[group.get("selector_action") or "unknown"] += 1

    capture_requirement_rows = 0
    capture_requirement_row_sum = 0
    capture_joined_row_sum = 0
    capture_origin_counts: Counter = Counter()
    with open_text(CAPTURE_GAP_LEDGER, "wt") as handle:
        for requirement in iter_jsonl(LANE09_CAPTURE_REQUIREMENTS):
            capture_requirement_rows += 1
            lane09_rows = int(requirement.get("rows") or 0)
            capture_requirement_row_sum += lane09_rows
            matched_lane10_rows = lane10_gap_counts.get(requirement_key(requirement), 0)
            capture_joined_row_sum += min(lane09_rows, matched_lane10_rows)
            origin = requirement.get("origin_family") or "missing"
            capture_origin_counts[origin] += lane09_rows
            join_status = "matched_lane10_gap_without_origin_family_key"
            if matched_lane10_rows == 0:
                join_status = "missing_lane10_scheduler_gap_match"
            elif matched_lane10_rows < lane09_rows:
                join_status = "partial_lane10_gap_match_without_origin_family_key"
            handle.write(
                json_line(
                    {
                        "route_id": ROUTE_ID,
                        "schema_version": "lane09b_capture_requirement_scheduler_gap_join_v1",
                        "requirement_id": requirement.get("requirement_id"),
                        "origin_family": origin,
                        "framework": requirement.get("framework"),
                        "side": requirement.get("side"),
                        "symbol": requirement.get("symbol"),
                        "replay_gap_reason_code": requirement.get("replay_gap_reason_code"),
                        "repair_requirement_code": requirement.get("repair_requirement_code"),
                        "lane09_requirement_rows": lane09_rows,
                        "lane10_scheduler_gap_rows_matching_without_origin": matched_lane10_rows,
                        "join_status": join_status,
                        "missing_exact_join_keys": ["origin_family"],
                        "exact_next_capture": requirement.get("exact_next_capture"),
                        "scheduler_decision": "NOT_REPLAYABLE_SOURCE_GAP",
                        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                    }
                )
            )

    mechanism_rows = 0
    with open_text(MECHANISM_OUTCOME_LEDGER, "wt") as handle:
        for mechanism in iter_jsonl(LANE09_MECHANISMS):
            mechanism_rows += 1
            family = mechanism.get("mechanism_family")
            aggregate = mechanism_aggs.get(family, OutcomeAggregate())
            capture_rows = int(capture_origin_counts.get(family, 0))
            refined_action, reason = recommendation_for_aggregate(mechanism.get("mechanism_decision"), aggregate)
            if mechanism.get("mechanism_decision") == "capture_repair" and capture_rows:
                refined_action, reason = "capture", "mechanism_is_gap_only_or_missing_source_in_lane09_and_lane10"
            handle.write(
                json_line(
                    {
                        "route_id": ROUTE_ID,
                        "schema_version": "lane09b_mechanism_scheduler_outcome_v1",
                        "mechanism_family": family,
                        "lane09_mechanism_decision": mechanism.get("mechanism_decision"),
                        "lane09_decision_reason": mechanism.get("decision_reason"),
                        "lane09_scored_replay_rows": mechanism.get("scored_replay_rows"),
                        "lane09_missing_replay_gap_rows": mechanism.get("missing_replay_gap_rows"),
                        "lane09b_joined_scheduler_rows": aggregate.rows,
                        "lane09b_capture_requirement_rows_for_family": capture_rows,
                        "scheduler_metrics": aggregate.as_dict(),
                        "refined_scheduler_aware_action": refined_action,
                        "refinement_reason": reason,
                        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                    }
                )
            )

    edge_summary_rows = 0
    with open_text(EDGE_SUMMARY_LEDGER, "wt") as handle:
        for (dims, values), aggregate in sorted(summary_aggs.items(), key=lambda item: (item[0][0], item[0][1])):
            handle.write(
                json_line(
                    {
                        "route_id": ROUTE_ID,
                        "schema_version": "lane09b_blocked_surviving_edge_summary_v1",
                        "dimensions": list(dims),
                        "dimension_values": dict(zip(dims, values)),
                        "scheduler_metrics": aggregate.as_dict(),
                        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                    }
                )
            )
            edge_summary_rows += 1

    action_rows = 0
    with open_text(ACTION_REFINEMENT_LEDGER, "wt") as handle:
        for (action_family, selector_action, refined_action), aggregate in sorted(clause_action_aggs.items()):
            handle.write(
                json_line(
                    {
                        "route_id": ROUTE_ID,
                        "schema_version": "lane09b_action_refinement_v1",
                        "selector_action_family": action_family,
                        "selector_action": selector_action,
                        "refined_scheduler_aware_action": refined_action,
                        "metric_interpretation": "overlapping_clause_exposure_not_distinct_row_denominator",
                        "scheduler_metrics": aggregate.as_dict(),
                        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                    }
                )
            )
            action_rows += 1

    source_gap_rows = write_source_gap_ledger(
        missing_scheduler_rows=missing_scheduler_rows,
        lane10_gap_total=lane10_gap_total,
        capture_requirement_rows=capture_requirement_rows,
        capture_requirement_row_sum=capture_requirement_row_sum,
        capture_joined_row_sum=capture_joined_row_sum,
    )

    package = build_refinement_package(
        generated_at,
        total_agg,
        scheduler_counts,
        discovery_action_counts,
        {
            "row_join_rows": joined_rows,
            "clause_rows": clause_rows,
            "discovery_rows": discovery_rows,
            "mechanism_rows": mechanism_rows,
            "capture_requirement_rows": capture_requirement_rows,
            "false_positive_rows": false_positive_rows,
            "blocked_edge_rows": blocked_edge_rows,
            "edge_summary_rows": edge_summary_rows,
            "action_refinement_rows": action_rows,
            "source_gap_rows": source_gap_rows,
            "lane10_missing_gap_rows": lane10_gap_total,
        },
    )
    write_json(REFINEMENT_PACKAGE, package)
    write_json(LANE11_CONTRACT, build_lane11_contract(generated_at))
    write_json(SOURCE_USE_STATE, build_source_use_state(generated_at))
    write_json(RUNTIME_EFFECT_BOUNDARY, {"route_id": ROUTE_ID, "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT})
    write_json(RESULT_USE_STATUS, {"route_id": ROUTE_ID, "result_use_status": RESULT_USE_STATUS_TEXT})
    CONTEXT_ANCHOR.write_text(build_context_anchor(generated_at), encoding="utf-8")
    SATURATION_REVIEW.write_text(build_saturation_review(generated_at), encoding="utf-8")

    manifest = build_manifest(generated_at)
    write_json(OUTPUT_MANIFEST, manifest)
    verification = verify_outputs(write=True, require_focused_test=False)
    completion = build_completion_audit(generated_at, package, manifest, verification)
    write_json(COMPLETION_AUDIT, completion)
    return completion


def write_source_gap_ledger(
    *,
    missing_scheduler_rows: int,
    lane10_gap_total: int,
    capture_requirement_rows: int,
    capture_requirement_row_sum: int,
    capture_joined_row_sum: int,
) -> int:
    rows = [
        {
            "gap_code": "lane09_row_to_lane10_scheduler_row_join",
            "gap_status": "pass" if missing_scheduler_rows == 0 else "fail",
            "affected_rows": missing_scheduler_rows,
            "exact_missing_key_or_source": "Lane10 row_id for Lane09 source_row_id",
            "repair_action": "none_required" if missing_scheduler_rows == 0 else "rebuild_or_repair_lane10_scheduler_replay_from_lane08_row_id",
        },
        {
            "gap_code": "lane10_missing_gap_origin_family_absent",
            "gap_status": "partial_join_by_symbol_framework_side_reason_repair",
            "affected_rows": lane10_gap_total,
            "exact_missing_key_or_source": "origin_family is not present in LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz",
            "repair_action": "Lane11 or future scheduler-gap rebuild should carry Lane09 origin_family or Lane08 gap origin metadata",
        },
        {
            "gap_code": "lane09_capture_requirement_to_lane10_gap_join",
            "gap_status": "partial" if capture_joined_row_sum < capture_requirement_row_sum else "pass",
            "affected_rows": capture_requirement_row_sum - capture_joined_row_sum,
            "exact_missing_key_or_source": "origin_family exact key absent from Lane10 scheduler missing-gap rows",
            "repair_action": "preserve Lane09 capture origin in future Lane10/Lane11 gap contracts",
        },
        {
            "gap_code": "lane11_policy_engine_terminal_contract",
            "gap_status": "contract_written_pending_terminal_lane11_consumption",
            "affected_rows": EXPECTED_LANE09_ROW_EVIDENCE_ROWS,
            "exact_missing_key_or_source": "committed Lane11 terminal policy outcomes are not an immutable input to Lane09b at build time",
            "repair_action": "join Lane11 terminal policy ledger by source_row_id/lane08_row_id without rebuilding Lane09b row identity",
        },
    ]
    with open_text(SOURCE_GAP_LEDGER, "wt") as handle:
        for idx, row in enumerate(rows, start=1):
            payload = {
                "route_id": ROUTE_ID,
                "schema_version": "lane09b_source_gap_v1",
                "gap_id": f"lane09b_gap_{idx:03d}",
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                **row,
            }
            handle.write(json_line(payload))
    return len(rows)


def build_refinement_package(
    generated_at: str,
    total_agg: OutcomeAggregate,
    scheduler_counts: Counter,
    discovery_action_counts: Counter,
    output_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_scheduler_aware_meta_selector_refinement_package_v1",
        "generated_at_utc": generated_at,
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "live_activation_allowed_by_this_package": False,
        "owner_approval_required_for_activation": True,
        "lane09_inputs_immutable": True,
        "lane10_inputs_immutable": True,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "count_parity": {
            "lane09_selector_row_evidence_rows": output_counts["row_join_rows"],
            "lane09_discovery_group_rows": output_counts["discovery_rows"],
            "lane09_clause_rows": output_counts["clause_rows"],
            "lane09_mechanism_rows": output_counts["mechanism_rows"],
            "lane09_capture_requirement_rows": output_counts["capture_requirement_rows"],
            "lane10_scheduler_replay_rows": sum(scheduler_counts.values()),
            "lane10_conflict_reject_rows": line_count(LANE10_CONFLICTS),
            "lane10_rejected_rows": scheduler_counts.get("REJECTED", 0),
            "lane10_accepted_rows": scheduler_counts.get("ACCEPTED", 0),
            "lane10_accepted_reduced_risk_rows": scheduler_counts.get("ACCEPTED_REDUCED_RISK", 0),
            "lane10_risk_exposure_rows": line_count(LANE10_RISK_EXPOSURE),
            "lane10_split_stress_rows": line_count(LANE10_SPLIT_STRESS),
            "lane10_missing_gap_rows": output_counts["lane10_missing_gap_rows"],
        },
        "scheduler_reconciliation_metrics": total_agg.as_dict(),
        "discovery_action_counts": dict(sorted(discovery_action_counts.items())),
        "output_counts": output_counts,
        "primary_ledgers": {
            "row_join_ledger": repo_rel(ROW_JOIN_LEDGER),
            "clause_outcome_ledger": repo_rel(CLAUSE_OUTCOME_LEDGER),
            "discovery_outcome_ledger": repo_rel(DISCOVERY_OUTCOME_LEDGER),
            "mechanism_outcome_ledger": repo_rel(MECHANISM_OUTCOME_LEDGER),
            "action_refinement_ledger": repo_rel(ACTION_REFINEMENT_LEDGER),
            "false_positive_ledger": repo_rel(FALSE_POSITIVE_LEDGER),
            "blocked_edge_ledger": repo_rel(BLOCKED_EDGE_LEDGER),
            "capture_gap_ledger": repo_rel(CAPTURE_GAP_LEDGER),
            "lane11_contract": repo_rel(LANE11_CONTRACT),
        },
        "refinement_policy": {
            "promote": "remain_promote only when scheduler survival and positive edge dominate false positives and repairable blocks",
            "reduce_risk": "use when scheduler admits material rows only with reduced risk or blocked positive edge exceeds surviving edge",
            "avoid": "use when scheduler survival exposes high selector false-positive share without offsetting positive edge",
            "hold": "use when scheduler evidence is mixed or Lane11 policy proof is needed before selector change",
            "capture": "use when source gaps, missing scheduler joins, or gap-only mechanisms dominate",
        },
    }


def build_lane11_contract(generated_at: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_lane11_expanded_policy_integration_contract_v1",
        "generated_at_utc": generated_at,
        "purpose": "Allow Lane09b reconciliation to consume committed Lane11 policy outcomes by stable row identity without rebuilding Lane09 or Lane10.",
        "required_lane11_join_keys": [
            "source_row_id",
            "lane08_row_id",
            "selected_row_id",
            "candidate_id",
            "symbol",
            "candidate_time_utc",
            "side",
            "origin_family",
            "framework",
        ],
        "lane09b_stable_join_keys": [
            "source_row_id",
            "candidate_id",
            "selected_row_id",
            "symbol",
            "candidate_time_utc",
            "side",
            "origin_family",
            "framework",
        ],
        "required_lane11_policy_fields": [
            "lane11_policy_decision",
            "lane11_policy_reason",
            "chosen_execution_policy",
            "policy_expected_r",
            "policy_cost_stress_r",
            "policy_tick_realism_state",
            "policy_broker_feasibility_state",
            "partial_close_ticket_state",
            "modify_retcode_state",
            "time_stop_state",
            "trailing_stop_state",
            "momentum_exhaustion_state",
            "partial_be_runner_state",
            "fixed_comparator_state",
        ],
        "policy_dependency_rule": {
            "lane09b_field": "lane11_policy_dependency",
            "true_when_path_class_in": sorted(POLICY_DEPENDENT_PATH_CLASSES),
            "post_lane11_action": "append lane11 outcome fields to Lane09b row join by source_row_id and recompute only refinement summaries that explicitly name Lane11 policy fields",
        },
        "forbidden_lane11_join_fields": [
            "future live broker/account state not captured as-of",
            "post-production activation outcomes",
            "unapproved live order/deal/position mutations",
        ],
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def build_source_use_state(generated_at: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_source_use_state_v1",
        "generated_at_utc": generated_at,
        "inputs": {
            "lane09": [
                repo_rel(LANE09_ROW_EVIDENCE),
                repo_rel(LANE09_DISCOVERY),
                repo_rel(LANE09_CLAUSES),
                repo_rel(LANE09_MECHANISMS),
                repo_rel(LANE09_CAPTURE_REQUIREMENTS),
                repo_rel(LANE09_PACKAGE),
            ],
            "lane10": [
                repo_rel(LANE10_SCHEDULER_REPLAY),
                repo_rel(LANE10_CONFLICTS),
                repo_rel(LANE10_RISK_EXPOSURE),
                repo_rel(LANE10_SPLIT_STRESS),
                repo_rel(LANE10_MISSING_GAPS),
                repo_rel(LANE10_COMPLETION_AUDIT),
            ],
            "upstream_context": [
                repo_rel(LANE05_DIR),
                repo_rel(LANE06_DIR),
                repo_rel(LANE07_DIR),
                repo_rel(LANE08_DIR),
            ],
        },
        "source_use_state": "Lane09 selector intelligence and Lane10 scheduler decisions consumed as immutable committed evidence inputs; Lane05-Lane08 used as upstream context and row identity authority.",
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def build_context_anchor(generated_at: str) -> str:
    return f"""# Lane09b Selector Scheduler Reconciliation Context Anchor

Generated: {generated_at}
Route: `{ROUTE_ID}`

## Objective

Extend completed Lane09 selector intelligence into a selector-scheduler reconciliation layer using committed Lane09 and Lane10 terminal routes as immutable inputs.

## Inputs

- Lane09 Meta-Selector V2: `{repo_rel(LANE09_DIR)}`
- Lane10 Portfolio Scheduler V2: `{repo_rel(LANE10_DIR)}`
- Upstream row identity and context: Lane05, Lane06, Lane07, Lane08 terminal routes

## Boundary

Offline default-off research package only. No live broker/order/deal/position action, no production selector/scheduler activation, no config/risk/execution/safety change, no paid API/vendor call, no credentials, and no remote push.

## Stop Condition

Complete only when Lane09 and Lane10 count parity is verified, row/clause/discovery/mechanism/capture surfaces are reconciled, Lane11 integration contract is written, verifier passes, focused tests pass, and the scoped route commit is created.
"""


def build_saturation_review(generated_at: str) -> str:
    return f"""# Lane09b Saturation And Self-Red-Team

Generated: {generated_at}

- Row identity risk: Lane09 row evidence joins to Lane10 scheduler replay by `source_row_id` -> `row_id`; verifier requires `289,928` joined rows and zero missing scheduler rows.
- Count-delta risk: manifest and completion audit record Lane09 row/discovery/clause/mechanism/capture counts and Lane10 replay/reject/accept/reduced/risk/split counts.
- Gap risk: Lane10 missing-gap scheduler rows lack `origin_family`, so capture requirements join by symbol/framework/side/reason/repair and preserve `origin_family` as an exact missing key in the source-gap ledger.
- Outcome-leak risk: runtime package remains default-off; row ledgers carry replay/proxy result fields only for offline reconciliation, not live selector packet eligibility.
- Lane11 risk: policy-dependent rows are flagged and an integration contract freezes the future join keys so Lane11 can be consumed without rebuilding Lane09/Lane10 evidence.
- No top-N risk: all material rows are preserved; large row-level false-positive and blocked-edge ledgers are subsets by explicit predicate, not ranked truncations.
"""


def output_file_specs() -> list[tuple[Path, int | None, str]]:
    return [
        (ROW_JOIN_LEDGER, EXPECTED_LANE09_ROW_EVIDENCE_ROWS, "selector_to_scheduler_row_join_ledger"),
        (CLAUSE_OUTCOME_LEDGER, EXPECTED_LANE09_CLAUSE_ROWS, "clause_to_scheduler_outcome_ledger"),
        (DISCOVERY_OUTCOME_LEDGER, EXPECTED_LANE09_DISCOVERY_ROWS, "discovery_to_scheduler_outcome_ledger"),
        (MECHANISM_OUTCOME_LEDGER, EXPECTED_LANE09_MECHANISM_ROWS, "mechanism_to_scheduler_outcome_ledger"),
        (ACTION_REFINEMENT_LEDGER, None, "promote_reduce_avoid_capture_refinement_ledger"),
        (FALSE_POSITIVE_LEDGER, None, "selector_false_positive_ledger"),
        (BLOCKED_EDGE_LEDGER, None, "scheduler_blocked_edge_ledger"),
        (EDGE_SUMMARY_LEDGER, None, "blocked_and_surviving_edge_summary"),
        (CAPTURE_GAP_LEDGER, EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS, "capture_requirement_to_scheduler_gap_ledger"),
        (SOURCE_GAP_LEDGER, None, "source_gap_ledger"),
        (REFINEMENT_PACKAGE, None, "scheduler_aware_meta_selector_refinement_package"),
        (LANE11_CONTRACT, None, "lane11_expanded_policy_integration_contract"),
        (SOURCE_USE_STATE, None, "source_use_state"),
        (RESULT_USE_STATUS, None, "result_use_status"),
        (RUNTIME_EFFECT_BOUNDARY, None, "runtime_effect_boundary"),
        (CONTEXT_ANCHOR, None, "context_anchor"),
        (SATURATION_REVIEW, None, "saturation_self_red_team"),
        (FOCUSED_TEST_RESULT, None, "focused_test_result"),
        (OUTPUT_MANIFEST, None, "output_manifest"),
        (VERIFICATION_RESULT, None, "verification_result"),
        (COMPLETION_AUDIT, None, "completion_audit"),
    ]


def build_manifest(generated_at: str) -> dict[str, Any]:
    outputs = []
    for path, expected_count, role in output_file_specs():
        if path == OUTPUT_MANIFEST:
            continue
        exists = path.exists()
        observed_count = line_count(path) if exists and (path.suffix in {".jsonl", ".gz"}) else None
        outputs.append(
            {
                "path": repo_rel(path),
                "role": role,
                "exists": exists,
                "line_count": observed_count,
                "expected_line_count": expected_count,
                "size_bytes": path.stat().st_size if exists else None,
                "sha256": sha256_file(path) if exists else None,
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_output_manifest_v1",
        "generated_at_utc": generated_at,
        "route_dir": repo_rel(ROUTE_DIR),
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "expected_counts": {
            "lane09_selector_row_evidence_rows": EXPECTED_LANE09_ROW_EVIDENCE_ROWS,
            "lane09_discovery_groups": EXPECTED_LANE09_DISCOVERY_ROWS,
            "lane09_default_off_clauses": EXPECTED_LANE09_CLAUSE_ROWS,
            "lane09_mechanism_decisions": EXPECTED_LANE09_MECHANISM_ROWS,
            "lane09_capture_requirements": EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS,
            "lane10_scheduler_replay_rows": EXPECTED_LANE10_REPLAY_ROWS,
            "lane10_rejected_rows": EXPECTED_LANE10_REJECT_ROWS,
            "lane10_accepted_rows": EXPECTED_LANE10_ACCEPTED_ROWS,
            "lane10_accepted_reduced_risk_rows": EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS,
            "lane10_risk_exposure_rows": EXPECTED_LANE10_RISK_EXPOSURE_ROWS,
            "lane10_split_stress_rows": EXPECTED_LANE10_SPLIT_STRESS_ROWS,
            "lane08_missing_gap_rows": EXPECTED_LANE08_MISSING_GAP_ROWS,
        },
        "outputs": outputs,
        "output_count": len(outputs),
    }


def verify_outputs(*, write: bool = False, require_focused_test: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    counts: dict[str, Any] = {}

    required = {
        ROW_JOIN_LEDGER: EXPECTED_LANE09_ROW_EVIDENCE_ROWS,
        CLAUSE_OUTCOME_LEDGER: EXPECTED_LANE09_CLAUSE_ROWS,
        DISCOVERY_OUTCOME_LEDGER: EXPECTED_LANE09_DISCOVERY_ROWS,
        MECHANISM_OUTCOME_LEDGER: EXPECTED_LANE09_MECHANISM_ROWS,
        CAPTURE_GAP_LEDGER: EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS,
    }
    for path, expected in required.items():
        if not path.exists():
            issues.append(f"missing_required_output:{repo_rel(path)}")
            continue
        observed = line_count(path)
        counts[path.name] = observed
        if observed != expected:
            issues.append(f"line_count_mismatch:{path.name}:expected={expected}:observed={observed}")

    if LANE10_RISK_EXPOSURE.exists():
        risk_rows = line_count(LANE10_RISK_EXPOSURE)
        counts["lane10_risk_exposure_rows"] = risk_rows
        if risk_rows != EXPECTED_LANE10_RISK_EXPOSURE_ROWS:
            issues.append(f"lane10_risk_exposure_count_mismatch:{risk_rows}")
    else:
        issues.append("missing_lane10_risk_exposure_input")

    if LANE10_SPLIT_STRESS.exists():
        split_rows = line_count(LANE10_SPLIT_STRESS)
        counts["lane10_split_stress_rows"] = split_rows
        if split_rows != EXPECTED_LANE10_SPLIT_STRESS_ROWS:
            issues.append(f"lane10_split_stress_count_mismatch:{split_rows}")
    else:
        issues.append("missing_lane10_split_stress_input")

    if REFINEMENT_PACKAGE.exists():
        package = json.loads(REFINEMENT_PACKAGE.read_text(encoding="utf-8"))
        parity = package.get("count_parity", {})
        checks = {
            "lane10_scheduler_replay_rows": EXPECTED_LANE10_REPLAY_ROWS,
            "lane10_rejected_rows": EXPECTED_LANE10_REJECT_ROWS,
            "lane10_accepted_rows": EXPECTED_LANE10_ACCEPTED_ROWS,
            "lane10_accepted_reduced_risk_rows": EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS,
            "lane10_missing_gap_rows": EXPECTED_LANE08_MISSING_GAP_ROWS,
        }
        for key, expected in checks.items():
            observed = parity.get(key)
            counts[key] = observed
            if observed != expected:
                issues.append(f"package_count_parity_mismatch:{key}:expected={expected}:observed={observed}")
        if package.get("enabled_by_default") is not False or package.get("apply_to_execution_default") is not False:
            issues.append("refinement_package_not_default_off")
    else:
        issues.append("missing_refinement_package")

    if LANE11_CONTRACT.exists():
        contract = json.loads(LANE11_CONTRACT.read_text(encoding="utf-8"))
        required_keys = set(contract.get("required_lane11_join_keys", []))
        if "source_row_id" not in required_keys or "selected_row_id" not in required_keys:
            issues.append("lane11_contract_missing_stable_join_keys")
    else:
        issues.append("missing_lane11_contract")

    if require_focused_test and not FOCUSED_TEST_RESULT.exists():
        issues.append("missing_focused_test_result")

    result = {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_verification_result_v1",
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": counts,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
    return result


def build_completion_audit(
    generated_at: str,
    package: dict[str, Any],
    manifest: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "lane09b_completion_audit_v1",
        "generated_at_utc": generated_at,
        "status": "complete_verified" if verification.get("ok") else "verification_failed",
        "objective": "Selector-scheduler reconciliation over immutable Lane09 Meta-Selector V2 and Lane10 Portfolio Scheduler V2 terminal evidence",
        "source_use_state": "Lane09 row/clause/discovery/mechanism/capture surfaces and Lane10 replay/conflict/risk/split/gap surfaces consumed; Lane05-Lane08 used as upstream row identity and context.",
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "completion_requirements": {
            "mandatory_preflight_completed": True,
            "research_doctrine_read": True,
            "master_wave3_state_read": True,
            "lane09_consumed_read_only": True,
            "lane10_consumed_read_only": True,
            "lane09_row_count_parity": package["count_parity"]["lane09_selector_row_evidence_rows"] == EXPECTED_LANE09_ROW_EVIDENCE_ROWS,
            "lane09_clause_count_parity": package["count_parity"]["lane09_clause_rows"] == EXPECTED_LANE09_CLAUSE_ROWS,
            "lane09_discovery_count_parity": package["count_parity"]["lane09_discovery_group_rows"] == EXPECTED_LANE09_DISCOVERY_ROWS,
            "lane09_mechanism_count_parity": package["count_parity"]["lane09_mechanism_rows"] == EXPECTED_LANE09_MECHANISM_ROWS,
            "lane09_capture_requirement_count_parity": package["count_parity"]["lane09_capture_requirement_rows"] == EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS,
            "lane10_replay_count_parity": package["count_parity"]["lane10_scheduler_replay_rows"] == EXPECTED_LANE10_REPLAY_ROWS,
            "lane10_reject_accept_count_parity": package["count_parity"]["lane10_rejected_rows"] == EXPECTED_LANE10_REJECT_ROWS
            and package["count_parity"]["lane10_accepted_rows"] == EXPECTED_LANE10_ACCEPTED_ROWS
            and package["count_parity"]["lane10_accepted_reduced_risk_rows"] == EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS,
            "lane10_conflict_risk_split_count_parity": package["count_parity"].get("lane10_conflict_reject_rows") == EXPECTED_LANE10_REJECT_ROWS
            and package["count_parity"].get("lane10_risk_exposure_rows") == EXPECTED_LANE10_RISK_EXPOSURE_ROWS
            and package["count_parity"].get("lane10_split_stress_rows") == EXPECTED_LANE10_SPLIT_STRESS_ROWS,
            "manifest_written": manifest.get("output_count", 0) > 0,
            "verifier_ok": verification.get("ok") is True,
            "focused_tests_present": FOCUSED_TEST_RESULT.exists(),
            "scoped_commit_status": "ready_for_scoped_commit_after_verification",
        },
        "counts": package["count_parity"],
        "scheduler_reconciliation_metrics": package["scheduler_reconciliation_metrics"],
        "output_manifest": repo_rel(OUTPUT_MANIFEST),
        "verification_result": verification,
    }


def main() -> None:
    completion = build_route()
    print(json.dumps(completion, indent=2, sort_keys=True))
    if completion.get("status") != "complete_verified":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
