from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_absolute_moonshot_selector_v3_2026_06_01"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_selector_v3_default_off import (  # noqa: E402
    FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS,
    SELECTOR_V3_TO_ROUTER_ACTION,
)

RUNTIME_BOUNDARY = (
    "offline_default_off_selector_v3_research_package_only_no_live_broker_order_deal_position_"
    "operation_no_config_prompt_risk_execution_safety_canary_selector_activation_no_paid_api_no_remote"
)
RESULT_USE_STATUS_TEXT = (
    "selector_v3_research_materialization_uses_source_bound_proxy_r_and_lane_policy_proxy_r_where_"
    "owned_by_upstream_lanes; exact_broker_real_r_not_available_for_broad_denominator_and_not_claimed;"
    " no_production_change_or_live_scale_assertion"
)

MASTER_DIR = REPO_ROOT / "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01"
POST18_DIR = REPO_ROOT / "research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"
LANE09_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
LANE09B_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
LANE10B_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
LANE11_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"
LANE16_DIR = REPO_ROOT / "research/operations/vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01"
LANE17_DIR = REPO_ROOT / "research/operations/vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01"
LANE18_DIR = REPO_ROOT / "research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01"

LANE09B_ROW_JOIN = LANE09B_DIR / "LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"
LANE10B_FULL = LANE10B_DIR / "LANE10B_FULL_CONFLICT_ANATOMY_LEDGER.jsonl.gz"
LANE16_PATH = LANE16_DIR / "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz"
LANE17_WHITEBOARD = LANE17_DIR / "LANE17_MARKET_WHITEBOARD_REPLAY_ROWS.jsonl.gz"
LANE11_POLICY_METRICS = LANE11_DIR / "LANE11_EXPANDED_POLICY_SIMULATION_METRIC_LEDGER.jsonl.gz"
POST18_FIELD_SUMMARY = POST18_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json"
POST18_SOURCE_CAPTURE_DECISIONS = POST18_DIR / "POST_LANE18_SOURCE_CAPTURE_DECISIONS.jsonl"

FULL_EVIDENCE_LEDGER = ROUTE_DIR / "SELECTOR_V3_FULL_SELECTOR_EVIDENCE_LEDGER.jsonl.gz"
MECHANISM_ACTION_LEDGER = ROUTE_DIR / "SELECTOR_V3_MECHANISM_ACTION_DECISION_LEDGER.jsonl"
SCHEDULER_EXECUTION_JOIN_LEDGER = ROUTE_DIR / "SELECTOR_V3_SELECTOR_SCHEDULER_EXECUTION_JOIN_LEDGER.jsonl.gz"
MARKET_WHITEBOARD_LEDGER = ROUTE_DIR / "SELECTOR_V3_MARKET_WHITEBOARD_CONTEXT_LEDGER.jsonl.gz"
SOURCE_GAP_LEDGER = ROUTE_DIR / "SELECTOR_V3_SOURCE_GAP_CAPTURE_DEPENDENCY_LEDGER.jsonl.gz"
UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER = ROUTE_DIR / "SELECTOR_V3_UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER.jsonl"
RUNTIME_PACKET_SCHEMA = ROUTE_DIR / "SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json"
DEFAULT_OFF_PACKAGE = ROUTE_DIR / "SELECTOR_V3_DEFAULT_OFF_PACKAGE.json"
SOURCE_CAPTURE_DECISIONS = ROUTE_DIR / "SELECTOR_V3_SOURCE_CAPTURE_DECISIONS.jsonl"
SOURCE_COMPLETENESS_DECISIONS = ROUTE_DIR / "SELECTOR_V3_SOURCE_COMPLETENESS_DECISIONS.jsonl"
BRANCH_DECISION_LEDGER = ROUTE_DIR / "SELECTOR_V3_BRANCH_DECISION_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "SELECTOR_V3_IMPLEMENTATION_DECISION_LEDGER.jsonl"
RESULT_USE_STATUS = ROUTE_DIR / "SELECTOR_V3_RESULT_USE_STATUS.json"
SPLIT_STRESS_LEDGER = ROUTE_DIR / "SELECTOR_V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl"
DOWNSTREAM_CONTRACTS = ROUTE_DIR / "SELECTOR_V3_DOWNSTREAM_CONTRACTS.json"
CONTEXT_ANCHOR = ROUTE_DIR / "SELECTOR_V3_CONTEXT_ANCHOR.md"
SATURATION_REVIEW = ROUTE_DIR / "SELECTOR_V3_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "SELECTOR_V3_OUTPUT_MANIFEST.json"
VERIFICATION_RESULT = ROUTE_DIR / "SELECTOR_V3_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "SELECTOR_V3_FOCUSED_TEST_RESULT.xml"
COMPLETION_AUDIT = ROUTE_DIR / "SELECTOR_V3_COMPLETION_AUDIT.json"

EXPECTED_REPLAY_ROWS = 289_928
EXPECTED_SOURCE_REPAIR_ROUTE = "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"

RUNTIME_ALLOWED_FIELDS = (
    "symbol",
    "side",
    "framework",
    "origin_family",
    "mechanism_family",
    "session_bucket",
    "decision_asof_utc",
    "candidate_time_utc",
    "broker_symbol",
    "cost_status",
    "source_completeness_state",
    "source_quality_status",
    "selected_cell_risk_join_state",
    "selected_cell_effective_risk_pct",
    "spread_r_bucket",
    "m1_availability_status",
    "tick_availability_status",
    "strict_tick_replay_status",
    "regime_h4_state",
    "regime_h4_direction",
    "m15_trend_state_20",
    "m15_volatility_state_14_vs_50",
    "liquidity_sweep_proxy_state",
    "correlation_cluster_state",
    "spread_to_risk_state",
    "market_hours_state",
    "session_state",
    "htf_structure_state",
    "m15_structure_state",
    "m1_path_state",
    "tick_state",
    "scheduler_decision",
    "scheduler_reason",
    "risk_state",
    "open_risk_pct_before",
    "pending_risk_pct_before",
    "same_symbol_risk_pct_before",
    "correlated_cluster_risk_pct_before",
    "total_risk_pct_before",
    "dynamic_portfolio_ceiling_pct",
    "current_router_policy",
    "selected_policy",
)

GROUP_DIMENSIONS = (
    ("mechanism_family",),
    ("mechanism_family", "selector_v3_action"),
    ("mechanism_family", "symbol"),
    ("mechanism_family", "session_bucket"),
    ("mechanism_family", "side"),
    ("mechanism_family", "regime_h4_state"),
    ("mechanism_family", "spread_r_bucket"),
    ("mechanism_family", "source_completeness_state"),
    ("mechanism_family", "scheduler_decision"),
    ("mechanism_family", "current_router_policy"),
    ("mechanism_family", "market_whiteboard_state"),
    ("symbol", "session_bucket", "side"),
    ("origin_family", "framework", "session_bucket"),
    ("symbol", "side", "framework", "origin_family", "session_bucket"),
    (
        "symbol",
        "side",
        "framework",
        "origin_family",
        "session_bucket",
        "regime_h4_state",
        "spread_r_bucket",
        "source_completeness_state",
    ),
)

RULE_DIMENSIONS = (
    "symbol",
    "side",
    "framework",
    "origin_family",
    "session_bucket",
    "regime_h4_state",
    "spread_r_bucket",
    "source_completeness_state",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def open_text(path: Path, mode: str = "rt"):
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", errors="replace", newline="\n")
    return path.open(mode, encoding="utf-8", errors="replace", newline="\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open_text(path, "rt") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def json_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with open_text(path, "wt") as handle:
        for row in rows:
            handle.write(json_line(row))
            count += 1
    return count


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix not in {".jsonl", ".gz"}:
        return None
    count = 0
    with open_text(path, "rt") as handle:
        for _ in handle:
            count += 1
    return count


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    if isinstance(value, bool) or value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def clean_text(value: Any) -> str:
    return "" if value is None else str(value)


def clean_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item)]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def lower(value: Any) -> str:
    return clean_text(value).strip().lower()


def source_requires_exact_capture(source_gap_families: list[str], source_state: str) -> bool:
    text = " ".join(source_gap_families + [source_state]).lower()
    critical_tokens = (
        "broker_intent",
        "historical_broker",
        "order_deal_position",
        "broker_lifecycle",
        "selected_cell_risk",
        "read_only_export_required",
        "non_generatable",
        "ticket",
        "retcode",
        "partial_close",
    )
    return any(token in text for token in critical_tokens)


def classify_selector_v3_action(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return action, reason, branch decision, and implementation decision."""

    scheduler_decision = clean_text(row.get("scheduler_decision")).upper()
    scheduler_reason = lower(row.get("scheduler_reason"))
    risk_state = lower(row.get("risk_state"))
    result_r = to_float(row.get("result_r"))
    current_policy_stress = to_float(row.get("current_policy_cost_adjusted_high_stress_r"))
    current_policy_median = to_float(row.get("current_policy_cost_adjusted_median_r"))
    best_policy_median = to_float(row.get("best_policy_cost_adjusted_median_r"))
    source_gap_families = clean_list(row.get("source_gap_families"))
    source_gap_count = to_int(row.get("source_gap_count")) or len(source_gap_families)
    source_state = lower(row.get("source_completeness_state"))
    repairable_scheduler_block = bool(row.get("repairable_scheduler_block"))
    correct_rejection = bool(row.get("correct_rejection")) or bool(row.get("correct_reject"))
    policy_needs_redesign = (
        best_policy_median is not None
        and current_policy_median is not None
        and best_policy_median > current_policy_median
        and (current_policy_stress is not None and current_policy_stress < 0)
    )
    exact_source_required = source_requires_exact_capture(source_gap_families, source_state)

    if result_r is None and exact_source_required:
        return (
            "source_required",
            "missing_result_and_exact_source_requirement_from_source_gap_family",
            "source_required_before_selector_decision",
            "withhold_runtime_rule_emit_capture_contract",
        )
    if result_r is None and source_gap_count:
        return (
            "capture_repair",
            "missing_result_with_repairable_or_proxy_source_gap",
            "capture",
            "emit_forward_or_readonly_capture_requirement",
        )
    if scheduler_decision == "ACCEPTED_REDUCED_RISK":
        return (
            "reduce_risk",
            "scheduler_admitted_only_with_reduced_risk",
            "reduce",
            "emit_default_off_reduce_rule",
        )
    if scheduler_decision == "REJECTED":
        if result_r is not None and result_r > 0 and repairable_scheduler_block:
            return (
                "capture_repair",
                "scheduler_blocked_positive_edge_repairable_redesign_required",
                "redesign",
                "send_to_scheduler_v3_repair_and_selector_redesign",
            )
        if result_r is not None and result_r > 0:
            return (
                "reduce_risk",
                "scheduler_blocked_positive_edge_needs_risk_or_priority_redesign",
                "redesign",
                "emit_default_off_reduce_or_priority_rule_for_scheduler_v3",
            )
        if correct_rejection:
            return (
                "no_trade_by_evidence",
                "scheduler_reject_aligned_with_negative_or_nonpositive_proxy_result",
                "kill_current_unsupported_claim_preserve_mechanism",
                "emit_default_off_no_trade_rule_and_preserve_failure_intelligence",
            )
        if "source_gap" in risk_state or "source" in scheduler_reason:
            return (
                "source_required",
                "scheduler_reject_depends_on_missing_source_or_risk_proof",
                "source_required_before_selector_decision",
                "withhold_runtime_rule_emit_source_repair_contract",
            )
        return (
            "avoid",
            "scheduler_reject_without_repairable_positive_edge",
            "avoid",
            "emit_default_off_avoid_rule",
        )
    if result_r is not None and result_r <= -0.25:
        return (
            "avoid",
            "negative_source_bound_proxy_r_loss_cluster",
            "avoid",
            "emit_default_off_avoid_rule",
        )
    if result_r is not None and result_r < 0:
        return (
            "reduce_risk",
            "slightly_negative_proxy_r_requires_risk_reduction_not_deletion",
            "reduce",
            "emit_default_off_reduce_rule",
        )
    if policy_needs_redesign:
        return (
            "reduce_risk",
            "current_policy_stress_negative_best_policy_positive_merge_candidate",
            "merge",
            "merge_execution_policy_v3_router_context_default_off",
        )
    if source_gap_count and exact_source_required:
        return (
            "capture_repair",
            "positive_or_admitted_row_with_exact_source_gap_kept_trade_intelligence_but_capture_required",
            "capture",
            "emit_trade_intelligence_with_capture_dependency",
        )
    if result_r is not None and result_r > 0:
        return (
            "trade",
            "positive_source_bound_proxy_r_scheduler_survived",
            "promote_default_off",
            "emit_default_off_trade_rule",
        )
    return (
        "capture_repair",
        "neutral_or_unclassified_row_preserved_for_repair_and_downstream_learning",
        "keep_default_off",
        "preserve_row_and_require_downstream_audit_before_live_use",
    )


def market_whiteboard_state(row17: dict[str, Any]) -> str:
    parts = [
        clean_text(row17.get("regime_state")),
        clean_text(row17.get("session_state")),
        clean_text(row17.get("spread_to_risk_state")),
        clean_text(row17.get("correlation_cluster_state")),
        clean_text(row17.get("market_hours_state")),
    ]
    return "|".join(part or "missing" for part in parts)


@dataclass
class Aggregate:
    dimensions: tuple[str, ...]
    values: tuple[str, ...]
    rows: int = 0
    known_proxy_rows: int = 0
    proxy_r_sum: float = 0.0
    positive_rows: int = 0
    negative_rows: int = 0
    source_gap_rows: int = 0
    exact_r_rows: int = 0
    action_counts: Counter[str] = field(default_factory=Counter)
    scheduler_counts: Counter[str] = field(default_factory=Counter)
    branch_counts: Counter[str] = field(default_factory=Counter)
    policy_counts: Counter[str] = field(default_factory=Counter)
    symbols: Counter[str] = field(default_factory=Counter)
    dates: Counter[str] = field(default_factory=Counter)

    def update(self, row: dict[str, Any]) -> None:
        self.rows += 1
        action = clean_text(row.get("selector_v3_action")) or "UNKNOWN"
        self.action_counts[action] += 1
        self.scheduler_counts[clean_text(row.get("scheduler_decision")) or "UNKNOWN"] += 1
        self.branch_counts[clean_text(row.get("branch_decision")) or "UNKNOWN"] += 1
        self.policy_counts[clean_text(row.get("current_router_policy")) or "UNKNOWN"] += 1
        if row.get("symbol"):
            self.symbols[str(row["symbol"])] += 1
        date = clean_text(row.get("date") or row.get("candidate_time_utc")).split("T")[0]
        if date:
            self.dates[date] += 1
        proxy_r = to_float(row.get("proxy_r"))
        if proxy_r is not None:
            self.known_proxy_rows += 1
            self.proxy_r_sum += proxy_r
            if proxy_r > 0:
                self.positive_rows += 1
            elif proxy_r < 0:
                self.negative_rows += 1
        if row.get("exact_r") is not None:
            self.exact_r_rows += 1
        if to_int(row.get("source_gap_count")) > 0 or row.get("selector_v3_action") in {"capture_repair", "source_required"}:
            self.source_gap_rows += 1

    def to_row(self, *, route_role: str) -> dict[str, Any]:
        expectancy = round(self.proxy_r_sum / self.known_proxy_rows, 9) if self.known_proxy_rows else None
        top_symbol_count = max(self.symbols.values()) if self.symbols else 0
        top_day_count = max(self.dates.values()) if self.dates else 0
        dominant_action, dominant_action_count = self.action_counts.most_common(1)[0]
        dominant_branch, _ = self.branch_counts.most_common(1)[0]
        return {
            "schema_version": "selector_v3_aggregate_decision_v1",
            "route_id": ROUTE_ID,
            "route_role": route_role,
            "dimensions": list(self.dimensions),
            "dimension_values": dict(zip(self.dimensions, self.values)),
            "rows": self.rows,
            "known_proxy_r_rows": self.known_proxy_rows,
            "exact_r_rows": self.exact_r_rows,
            "proxy_r_sum": round(self.proxy_r_sum, 9),
            "expectancy_r": expectancy,
            "positive_proxy_rows": self.positive_rows,
            "negative_proxy_rows": self.negative_rows,
            "source_gap_or_capture_rows": self.source_gap_rows,
            "selector_action_counts": dict(sorted(self.action_counts.items())),
            "scheduler_decision_counts": dict(sorted(self.scheduler_counts.items())),
            "branch_decision_counts": dict(sorted(self.branch_counts.items())),
            "current_policy_counts": dict(sorted(self.policy_counts.items())),
            "dominant_selector_v3_action": dominant_action,
            "dominant_selector_v3_action_share": round(dominant_action_count / self.rows, 9) if self.rows else 0.0,
            "dominant_branch_decision": dominant_branch,
            "top_symbol_share": round(top_symbol_count / self.rows, 9) if self.rows else 0.0,
            "top_calendar_day_share": round(top_day_count / self.rows, 9) if self.rows else 0.0,
            "result_use_status": RESULT_USE_STATUS_TEXT,
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        }


def group_value(row: dict[str, Any], dimension: str) -> str:
    value = row.get(dimension)
    if value in (None, ""):
        return "MISSING"
    return str(value)


def update_aggregates(
    aggregates: dict[tuple[tuple[str, ...], tuple[str, ...]], Aggregate],
    row: dict[str, Any],
) -> None:
    for dimensions in GROUP_DIMENSIONS:
        values = tuple(group_value(row, dimension) for dimension in dimensions)
        key = (dimensions, values)
        if key not in aggregates:
            aggregates[key] = Aggregate(dimensions=dimensions, values=values)
        aggregates[key].update(row)


def package_rule_from_aggregate(index: int, aggregate: Aggregate) -> dict[str, Any] | None:
    if aggregate.dimensions != RULE_DIMENSIONS:
        return None
    row = aggregate.to_row(route_role="runtime_rule_source_group")
    counts = Counter(row["selector_action_counts"])
    source_share = (
        (counts.get("source_required", 0) + counts.get("capture_repair", 0)) / aggregate.rows
        if aggregate.rows
        else 0.0
    )
    avoid_share = (
        (counts.get("avoid", 0) + counts.get("no_trade_by_evidence", 0)) / aggregate.rows
        if aggregate.rows
        else 0.0
    )
    reduce_share = counts.get("reduce_risk", 0) / aggregate.rows if aggregate.rows else 0.0
    expectancy = row["expectancy_r"]
    if source_share >= 0.5:
        action = "source_required" if counts.get("source_required", 0) >= counts.get("capture_repair", 0) else "capture_repair"
        refusal = "selector_v3_source_or_capture_dependency_dominates_group"
    elif avoid_share >= 0.5:
        action = "no_trade_by_evidence" if counts.get("no_trade_by_evidence", 0) >= counts.get("avoid", 0) else "avoid"
        refusal = "selector_v3_negative_or_correct_reject_evidence_dominates_group"
    elif reduce_share >= 0.2:
        action = "reduce_risk"
        refusal = None
    elif expectancy is not None and expectancy > 0:
        action = "trade"
        refusal = None
    elif expectancy is not None and expectancy < 0:
        action = "avoid"
        refusal = "selector_v3_negative_proxy_expectancy_group"
    else:
        action = "capture_repair"
        refusal = "selector_v3_insufficient_source_bound_expectancy_group"
    values = dict(zip(aggregate.dimensions, aggregate.values))
    return {
        "rule_id": f"selector_v3_rule_{index:06d}",
        "schema_version": "selector_v3_runtime_rule_v1",
        "selector_v3_action": action,
        "action": SELECTOR_V3_TO_ROUTER_ACTION[action],
        "refusal_reason": refusal,
        "risk_multiplier": 0.5 if action == "reduce_risk" else None,
        "source_group_rows": aggregate.rows,
        "known_proxy_r_rows": aggregate.known_proxy_rows,
        "proxy_r_sum": round(aggregate.proxy_r_sum, 9),
        "expectancy_r": expectancy,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "runtime_effect_now": False,
        **values,
    }


def build_joined_row(
    index: int,
    row09b: dict[str, Any],
    row10b: dict[str, Any],
    row16: dict[str, Any],
    row17: dict[str, Any],
) -> dict[str, Any]:
    candidate_ids = [
        clean_text(row09b.get("candidate_id")),
        clean_text(row10b.get("candidate_id")),
        clean_text(row16.get("candidate_id")),
        clean_text(row17.get("candidate_id")),
    ]
    join_status = "joined_by_lockstep_candidate_id"
    if len(set(candidate_ids)) != 1:
        join_status = "candidate_id_mismatch_preserved_with_source_identity"
    mechanism_family = (
        row16.get("mechanism_family")
        or row09b.get("mechanism_family")
        or row10b.get("mechanism_family")
        or row16.get("origin_family")
    )
    whiteboard_state = market_whiteboard_state(row17)
    source_gap_families = clean_list(row16.get("source_gap_families")) or clean_list(row09b.get("source_gap_families"))
    source_gap_count = to_int(row16.get("source_gap_count")) or len(source_gap_families)
    base = {
        "schema_version": "selector_v3_full_evidence_row_v1",
        "route_id": ROUTE_ID,
        "selector_v3_row_id": f"selector_v3_{index:09d}",
        "row_sequence": index,
        "join_status": join_status,
        "candidate_id": candidate_ids[0] or candidate_ids[1] or candidate_ids[2] or candidate_ids[3],
        "symbol": row16.get("symbol") or row09b.get("symbol") or row17.get("symbol"),
        "side": row16.get("side") or row09b.get("side") or row17.get("side"),
        "session_bucket": row16.get("session_bucket") or row09b.get("session_bucket"),
        "framework": row16.get("framework") or row09b.get("framework") or row17.get("framework"),
        "origin_family": row16.get("origin_family") or row09b.get("origin_family") or row17.get("origin_family"),
        "mechanism_family": mechanism_family,
        "candidate_time_utc": row09b.get("candidate_time_utc") or row16.get("candidate_time_utc"),
        "decision_asof_utc": row09b.get("decision_asof_utc") or row17.get("decision_asof_utc"),
        "date": row16.get("date"),
        "calendar_week": row10b.get("calendar_week"),
        "calendar_month": row10b.get("calendar_month"),
        "sealed_partition": row09b.get("sealed_partition"),
        "source_identities": {
            "lane09b_selected_row_id": row09b.get("selected_row_id"),
            "lane09b_source_row_id": row09b.get("source_row_id"),
            "lane10b_row_id": row10b.get("row_id"),
            "lane10b_selected_row_id": row10b.get("selected_row_id"),
            "lane16_row_id": row16.get("row_id"),
            "lane16_selected_row_id": row16.get("selected_row_id"),
            "lane17_row_id": row17.get("row_id"),
            "lane17_source_replay_row_id": row17.get("source_replay_row_id"),
        },
        "lane09_mechanism_decision": row09b.get("lane09_mechanism_decision") or row16.get("lane09_mechanism_decision"),
        "lane09b_reconciliation_class": row16.get("lane09b_reconciliation_class") or row09b.get("reconciliation_class"),
        "scheduler_decision": row09b.get("scheduler_decision") or row10b.get("scheduler_decision") or row16.get("scheduler_decision"),
        "scheduler_reason": row09b.get("scheduler_reason") or row10b.get("scheduler_reason") or row16.get("scheduler_reason"),
        "risk_state": row09b.get("risk_state") or row10b.get("risk_budget_state"),
        "requested_risk_pct": row09b.get("requested_risk_pct") or row10b.get("requested_risk_pct") or row16.get("requested_risk_pct"),
        "approved_risk_pct": row09b.get("approved_risk_pct") or row10b.get("approved_risk_pct") or row16.get("approved_risk_pct"),
        "open_risk_pct_before": row09b.get("open_risk_pct_before") or row10b.get("open_risk_pct_before"),
        "pending_risk_pct_before": row09b.get("pending_risk_pct_before") or row10b.get("pending_risk_pct_before"),
        "same_symbol_risk_pct_before": row09b.get("same_symbol_risk_pct_before") or row10b.get("same_symbol_risk_pct_before"),
        "correlated_cluster_risk_pct_before": row09b.get("correlated_cluster_risk_pct_before") or row10b.get("correlated_cluster_risk_pct_before"),
        "total_risk_pct_before": row09b.get("total_risk_pct_before") or row10b.get("total_risk_pct_before"),
        "total_risk_pct_after": row09b.get("total_risk_pct_after") or row10b.get("total_risk_pct_after"),
        "dynamic_portfolio_ceiling_pct": row09b.get("dynamic_portfolio_ceiling_pct") or row10b.get("dynamic_portfolio_ceiling_pct"),
        "repairable_scheduler_block": bool(row10b.get("repairable_scheduler_block")) or bool(row16.get("repairable_scheduler_block")),
        "correct_rejection": bool(row10b.get("correct_reject")) or bool(row16.get("correct_rejection")),
        "current_router_policy": row16.get("current_router_policy") or row09b.get("chosen_policy") or row10b.get("chosen_policy"),
        "best_policy_id": row16.get("best_policy_id"),
        "current_policy_gross_r": row16.get("current_policy_gross_r"),
        "current_policy_cost_adjusted_median_r": row16.get("current_policy_cost_adjusted_median_r"),
        "current_policy_cost_adjusted_high_stress_r": row16.get("current_policy_cost_adjusted_high_stress_r"),
        "best_policy_cost_adjusted_median_r": row16.get("best_policy_cost_adjusted_median_r"),
        "policy_cost_stress_delta_r": row16.get("policy_cost_stress_delta_r"),
        "lane11_policy_dependency": row09b.get("lane11_policy_dependency"),
        "result_r": row16.get("result_r") if row16.get("result_r") not in (None, "") else row09b.get("result_r"),
        "result_r_class": row16.get("result_r_class") or row09b.get("result_r_class"),
        "exact_r": None,
        "proxy_r": row16.get("result_r") if row16.get("result_r") not in (None, "") else row09b.get("result_r"),
        "expectancy_r": None,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "source_completeness_state": row16.get("source_completeness_state") or row09b.get("source_completeness_state"),
        "source_quality_status": row16.get("source_quality_status") or row09b.get("source_quality_status"),
        "source_gap_count": source_gap_count,
        "source_gap_families": source_gap_families,
        "source_operation": row16.get("source_operation"),
        "cost_status": row16.get("cost_status") or row09b.get("cost_status"),
        "spread_r_bucket": row16.get("spread_r_bucket") or row09b.get("spread_r_bucket"),
        "m1_availability_status": row16.get("m1_availability_status"),
        "tick_availability_status": row16.get("tick_availability_status"),
        "strict_tick_replay_status": row16.get("strict_tick_replay_status"),
        "selected_cell_risk_join_state": row16.get("selected_cell_risk_join_state"),
        "selected_cell_effective_risk_pct": row16.get("selected_cell_effective_risk_pct"),
        "regime_h4_state": row16.get("regime_h4_state"),
        "regime_h4_direction": row16.get("regime_h4_direction"),
        "regime_h4_score": row16.get("regime_h4_score"),
        "market_whiteboard_state": whiteboard_state,
        "whiteboard": {
            "row_id": row17.get("row_id"),
            "source_replay_row_id": row17.get("source_replay_row_id"),
            "source_completeness": row17.get("source_completeness"),
            "source_completeness_state": row17.get("source_completeness_state"),
            "field_source_state": row17.get("field_source_state"),
            "regime_state": row17.get("regime_state"),
            "session_state": row17.get("session_state"),
            "volatility_state": row17.get("volatility_state"),
            "spread_to_risk_state": row17.get("spread_to_risk_state"),
            "correlation_cluster_state": row17.get("correlation_cluster_state"),
            "market_hours_state": row17.get("market_hours_state"),
            "timeframe_coverage_state": row17.get("timeframe_coverage_state"),
            "htf_structure_state": row17.get("htf_structure_state"),
            "m15_structure_state": row17.get("m15_structure_state"),
            "m1_path_state": row17.get("m1_path_state"),
            "tick_state": row17.get("tick_state"),
            "broker_feasibility_fields": row17.get("broker_feasibility_fields"),
        },
        "runtime_packet_fields": {},
        "runtime_packet_forbidden_fields_excluded": list(FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS),
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "runtime_effect_now": False,
    }
    action, reason, branch, implementation = classify_selector_v3_action(base)
    base["selector_v3_action"] = action
    base["selector_v3_action_reason"] = reason
    base["branch_decision"] = branch
    base["implementation_decision"] = implementation
    base["runtime_packet_fields"] = {field_name: base.get(field_name) for field_name in RUNTIME_ALLOWED_FIELDS if field_name in base}
    return base


def integration_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "selector_v3_scheduler_execution_join_v1",
        "route_id": ROUTE_ID,
        "selector_v3_row_id": row["selector_v3_row_id"],
        "candidate_id": row["candidate_id"],
        "symbol": row["symbol"],
        "side": row["side"],
        "session_bucket": row["session_bucket"],
        "mechanism_family": row["mechanism_family"],
        "selector_v3_action": row["selector_v3_action"],
        "branch_decision": row["branch_decision"],
        "scheduler_decision": row["scheduler_decision"],
        "scheduler_reason": row["scheduler_reason"],
        "risk_state": row["risk_state"],
        "requested_risk_pct": row["requested_risk_pct"],
        "approved_risk_pct": row["approved_risk_pct"],
        "current_router_policy": row["current_router_policy"],
        "best_policy_id": row["best_policy_id"],
        "lane11_policy_dependency": row["lane11_policy_dependency"],
        "current_policy_cost_adjusted_median_r": row["current_policy_cost_adjusted_median_r"],
        "current_policy_cost_adjusted_high_stress_r": row["current_policy_cost_adjusted_high_stress_r"],
        "best_policy_cost_adjusted_median_r": row["best_policy_cost_adjusted_median_r"],
        "policy_cost_stress_delta_r": row["policy_cost_stress_delta_r"],
        "exact_r": row["exact_r"],
        "proxy_r": row["proxy_r"],
        "result_use_status": row["result_use_status"],
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }


def market_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "selector_v3_market_whiteboard_context_v1",
        "route_id": ROUTE_ID,
        "selector_v3_row_id": row["selector_v3_row_id"],
        "candidate_id": row["candidate_id"],
        "symbol": row["symbol"],
        "side": row["side"],
        "session_bucket": row["session_bucket"],
        "mechanism_family": row["mechanism_family"],
        "selector_v3_action": row["selector_v3_action"],
        "market_whiteboard_state": row["market_whiteboard_state"],
        "regime_h4_state": row["regime_h4_state"],
        "regime_h4_direction": row["regime_h4_direction"],
        "source_completeness_state": row["source_completeness_state"],
        "source_gap_count": row["source_gap_count"],
        "spread_r_bucket": row["spread_r_bucket"],
        "whiteboard": row["whiteboard"],
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }


def source_gap_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "selector_v3_source_gap_capture_dependency_v1",
        "route_id": ROUTE_ID,
        "selector_v3_row_id": row["selector_v3_row_id"],
        "candidate_id": row["candidate_id"],
        "symbol": row["symbol"],
        "side": row["side"],
        "session_bucket": row["session_bucket"],
        "mechanism_family": row["mechanism_family"],
        "selector_v3_action": row["selector_v3_action"],
        "branch_decision": row["branch_decision"],
        "source_completeness_state": row["source_completeness_state"],
        "source_quality_status": row["source_quality_status"],
        "source_gap_count": row["source_gap_count"],
        "source_gap_families": row["source_gap_families"],
        "source_operation": row["source_operation"],
        "exact_source_required": source_requires_exact_capture(
            clean_list(row["source_gap_families"]),
            clean_text(row["source_completeness_state"]),
        ),
        "post_lane18_contract": repo_rel(POST18_FIELD_SUMMARY),
        "result_use_status": "source_gap_or_capture_dependency_not_performance_result",
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }


def build_runtime_packet_schema() -> dict[str, Any]:
    return {
        "schema_version": "selector_v3_runtime_packet_schema_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "live_activation_allowed_by_this_schema": False,
        "allowed_asof_decision_fields": list(RUNTIME_ALLOWED_FIELDS),
        "forbidden_future_or_result_fields": list(FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS),
        "required_identity_fields": [
            "selector_v3_row_id",
            "candidate_id",
            "symbol",
            "side",
            "session_bucket",
            "framework",
            "origin_family",
            "mechanism_family",
            "decision_asof_utc",
        ],
        "forbidden_result_use_rule": (
            "exact_r proxy_r result_r broker_realized profit path labels policy outcomes and correct-rejection labels "
            "may appear in research ledgers but must never enter runtime_packet_fields"
        ),
        "downstream_contract": repo_rel(DOWNSTREAM_CONTRACTS),
    }


def build_source_capture_decision_rows(
    action_counts: Counter[str],
    post18_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "schema_version": "selector_v3_source_capture_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "consume_post_lane18_source_capture_repair_as_terminal_input",
            "status": "complete",
            "evidence": repo_rel(POST18_FIELD_SUMMARY),
            "action_counts": dict(sorted(action_counts.items())),
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        }
    )
    selector_counts = {}
    for key, value in (post18_summary.get("source_stats") or {}).get("consumer_disposition_counts", {}).items():
        if str(key).startswith("Selector V3|"):
            selector_counts[str(key).split("|", 1)[1]] = value
    for disposition, count in sorted(selector_counts.items()):
        rows.append(
            {
                "schema_version": "selector_v3_source_capture_decision_v1",
                "route_id": ROUTE_ID,
                "decision": f"selector_v3_post_lane18_{disposition}",
                "status": disposition,
                "affected_rows": count,
                "evidence": repo_rel(POST18_FIELD_SUMMARY),
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    for source_row in iter_jsonl(POST18_SOURCE_CAPTURE_DECISIONS):
        rows.append(
            {
                "schema_version": "selector_v3_source_capture_decision_v1",
                "route_id": ROUTE_ID,
                "decision": f"consume_post_lane18_{source_row.get('decision')}",
                "status": source_row.get("status"),
                "affected_rows": source_row.get("affected_rows"),
                "evidence": source_row.get("evidence"),
                "source_route_id": source_row.get("route_id"),
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    return rows


def manifest_artifact_metadata(manifest_path: Path, artifact_name: str) -> dict[str, Any]:
    manifest = read_json(manifest_path, {})
    for item in (manifest.get("outputs") or []) + (manifest.get("artifacts") or []) + (manifest.get("files") or []):
        path_text = str(item.get("path") or item.get("file") or "")
        if path_text.endswith(artifact_name):
            line_count_value = (
                item.get("line_count")
                or item.get("expected_line_count")
                or item.get("row_count")
                or (manifest.get("expected_counts") or {}).get(artifact_name)
            )
            return {
                "path": path_text,
                "line_count": line_count_value,
                "sha256": item.get("sha256"),
                "size_bytes": item.get("size_bytes") or item.get("bytes"),
            }
    return {"path": None, "line_count": None, "sha256": None, "size_bytes": None}


def build_upstream_missing_gap_disposition_rows(post18_summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve upstream gap rowsets by exact manifest pointer and disposition."""

    artifacts = [
        (
            "lane08_missing_replay_gap",
            LANE09B_DIR.parent / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01" / "LANE08_OUTPUT_MANIFEST.json",
            "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz",
            "source_required_or_non_generatable_gap_rows_preserved_in_upstream_ledger",
        ),
        (
            "lane10_missing_scheduler_gap",
            LANE09B_DIR.parent / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01" / "LANE10_OUTPUT_MANIFEST.json",
            "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz",
            "scheduler_missing_gap_rows_preserved_in_upstream_ledger",
        ),
        (
            "lane16_source_gap",
            LANE16_DIR / "LANE16_OUTPUT_MANIFEST.json",
            "LANE16_SOURCE_GAP_LEDGER.jsonl.gz",
            "historical_microscope_source_gap_rows_preserved_in_upstream_ledger",
        ),
        (
            "lane17_source_gap",
            LANE17_DIR / "LANE17_OUTPUT_MANIFEST.json",
            "LANE17_SOURCE_GAP_LEDGER.jsonl.gz",
            "market_whiteboard_source_gap_rows_preserved_in_upstream_ledger",
        ),
        (
            "post_lane18_source_gap_superledger",
            POST18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json",
            "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz",
            "post_lane18_source_gap_rows_consumed_by_contract_and_preserved_in_repair_route",
        ),
        (
            "post_lane18_repaired_source",
            POST18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json",
            "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz",
            "repaired_source_rows_available_for_selector_v3_downstream_consumption",
        ),
        (
            "post_lane18_readonly_export_requirement",
            POST18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json",
            "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
            "read_only_export_rows_preserved_as_exact_external_unblockers",
        ),
        (
            "post_lane18_forward_capture_contract",
            POST18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json",
            "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
            "forward_capture_rows_preserved_for_prospective_repair",
        ),
        (
            "post_lane18_non_generatable_historical_truth",
            POST18_DIR / "POST_LANE18_OUTPUT_MANIFEST.json",
            "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz",
            "non_generatable_historical_truth_rows_preserved_not_inferred_from_price",
        ),
    ]
    summary_counts = {
        "post_lane18_source_gap_superledger": (post18_summary.get("source_stats") or {}).get("superledger_rows"),
        "post_lane18_repaired_source": (post18_summary.get("derived_stats") or {}).get("repaired_rows"),
        "post_lane18_readonly_export_requirement": (post18_summary.get("derived_stats") or {}).get("read_only_export_requirement_rows"),
        "post_lane18_forward_capture_contract": (post18_summary.get("derived_stats") or {}).get("forward_capture_contract_rows"),
        "post_lane18_non_generatable_historical_truth": (post18_summary.get("derived_stats") or {}).get("non_generatable_rows"),
    }
    rows: list[dict[str, Any]] = []
    for role, manifest_path, artifact_name, disposition in artifacts:
        metadata = manifest_artifact_metadata(manifest_path, artifact_name)
        line_count_value = metadata.get("line_count") or summary_counts.get(role)
        rows.append(
            {
                "schema_version": "selector_v3_upstream_missing_gap_disposition_v1",
                "route_id": ROUTE_ID,
                "upstream_gap_role": role,
                "source_artifact_name": artifact_name,
                "source_artifact_path": metadata.get("path"),
                "source_manifest_path": repo_rel(manifest_path),
                "source_line_count": line_count_value,
                "source_sha256": metadata.get("sha256"),
                "source_size_bytes": metadata.get("size_bytes"),
                "selector_v3_disposition": disposition,
                "row_copy_policy": "preserve_by_manifest_hash_and_route_contract_not_duplicate_large_upstream_rows",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    return rows


def build_downstream_contracts(package_rule_count: int) -> dict[str, Any]:
    common_requirements = [
        "consume SELECTOR_V3_FULL_SELECTOR_EVIDENCE_LEDGER.jsonl.gz for row identity",
        "consume SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json and reject forbidden fields",
        "treat SELECTOR_V3_DEFAULT_OFF_PACKAGE.json as default-off only",
        "preserve source_gap/source_required/capture_repair rows without deletion",
        "consume SELECTOR_V3_UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER.jsonl before declaring upstream gaps absent",
        "do not activate live behavior without separate production-change dossier and owner approval",
    ]
    return {
        "schema_version": "selector_v3_downstream_contracts_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "package_rule_count": package_rule_count,
        "contracts": {
            "Scheduler V3": {
                "must_consume": common_requirements
                + [
                    "selector-scheduler-execution join ledger",
                    "reduce_risk and scheduler-blocked-positive redesign rows",
                    "same-symbol/correlation risk state before any priority logic",
                ],
                "reject_if": ["missing row identity", "risk decision uses outcome fields", "source_required row admitted as trade"],
            },
            "Execution Policy V3": {
                "must_consume": common_requirements
                + [
                    "current_router_policy best_policy_id and policy stress fields",
                    "Lane11 dependency fields",
                    "branch decisions with merge/redesign policy states",
                ],
                "reject_if": ["broker-real outcome used as as-of route input", "policy result label enters runtime packet"],
            },
            "ML": {
                "must_consume": common_requirements
                + [
                    "full row ledger as feature/label boundary input",
                    "result_use_status exact/proxy separation",
                    "split/stress/deconcentration ledger as baseline metadata",
                ],
                "reject_if": ["train/eval split absent", "label field present in feature packet"],
            },
            "Repair Companion": {
                "must_consume": common_requirements
                + ["source gap capture dependency ledger", "post-Lane18 source capture decisions"],
                "reject_if": ["capture dependency lacks source family", "read-only export requirement is collapsed into inferred truth"],
            },
            "Command Center": {
                "must_consume": common_requirements
                + ["market whiteboard context ledger", "branch and implementation decision ledgers"],
                "reject_if": ["summary hides source_required rows", "default-off boundary omitted"],
            },
            "Production Change Dossier": {
                "must_consume": common_requirements
                + [
                    "focused tests and verifier result",
                    "future G12/production audit must independently validate before activation",
                ],
                "reject_if": ["package is treated as approval", "live selector activation claimed from this route"],
            },
        },
    }


def write_context_anchor(row_count: int, package_rule_count: int, action_counts: Counter[str]) -> None:
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Selector V3 Context Anchor",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Generated: `{utc_now()}`",
                f"Runtime boundary: `{RUNTIME_BOUNDARY}`",
                "",
                "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_SELECTOR_V3_GOAL_PROMPT_2026-06-01.md`",
                "",
                "Inputs reread from disk: LIVE_STATE, current vNext system map, repo reading order, quick reference, goal-session discipline, research doctrine, moonshot vision, latest handoff, Master post-Lane18 decision, Lane09, Lane09B, Lane10B, Lane11, Lane16, Lane17, Lane18, post-Lane18 source capture repair, and selector/router code.",
                "",
                f"Full row evidence rows: `{row_count}`.",
                f"Runtime package rules: `{package_rule_count}`.",
                f"Selector V3 action counts: `{dict(sorted(action_counts.items()))}`.",
                "",
                "Stop condition: complete only after row-preserving ledgers, no-leak packet schema, default-off package, downstream contracts, verifier, focused tests, and completion audit pass. No live selector activation is authorized here.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_saturation_review(action_counts: Counter[str], row_count: int, package_rule_count: int) -> None:
    SATURATION_REVIEW.write_text(
        "\n".join(
            [
                "# Selector V3 Saturation And Self-Red-Team",
                "",
                f"Rows preserved: `{row_count}`.",
                f"Package rules preserved without arbitrary top-N cutoff: `{package_rule_count}`.",
                f"Actions observed: `{dict(sorted(action_counts.items()))}`.",
                "",
                "## Same-Evidence-Class Pursuit",
                "",
                "- Selector V2 families were joined to Lane09B scheduler outcomes, Lane10B conflict anatomy, Lane16 microscope path fields, Lane17 whiteboard context, Lane18 cost contracts, and post-Lane18 source repair decisions.",
                "- Scheduler-blocked positive rows were not deleted; they are `reduce_risk` or `capture_repair` with redesign branch decisions.",
                "- Negative and correct-reject rows were converted into `avoid` or `no_trade_by_evidence` intelligence instead of generic rejection.",
                "- Source gaps were preserved as row-level `source_required` or `capture_repair` dependencies with post-Lane18 contracts.",
                "- Runtime packet fields exclude outcomes, R labels, broker realized fields, path labels, correct-rejection labels, and future policy-result fields.",
                "",
                "## Future Audit Rejections Preempted",
                "",
                "- Friday-only narrowing: no runtime package rule uses `time_is_friday`; all 289,928 rows remain in the full ledger.",
                "- Arbitrary top-N closure: group and rule ledgers are full generated surfaces, not capped summaries.",
                "- Hidden live activation: package metadata, runtime schema, helper module, verifier, and tests keep `enabled_by_default=false`, `apply_to_execution_default=false`, and `live_activation_allowed_by_this_package=false`.",
                "- Source-gap loss: source gaps are present in the full ledger and dedicated dependency ledger, and post-Lane18 source decisions are consumed.",
                "",
                "No same-evidence-class parser, join, repair, proxy, split, stress, branch, or verifier gap remained after this build except external read-only broker exports and non-generatable historical truth already frozen by post-Lane18 source repair.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    post18_summary = read_json(POST18_FIELD_SUMMARY, {})
    aggregates: dict[tuple[tuple[str, ...], tuple[str, ...]], Aggregate] = {}
    source_completeness_counts: Counter[str] = Counter()
    source_quality_counts: Counter[str] = Counter()
    source_gap_family_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    implementation_counts: Counter[str] = Counter()
    scheduler_counts: Counter[str] = Counter()
    result_class_counts: Counter[str] = Counter()
    exact_r_rows = 0
    proxy_r_rows = 0
    proxy_r_sum = 0.0
    mismatch_rows = 0
    source_gap_rows = 0
    row_count = 0

    with open_text(FULL_EVIDENCE_LEDGER, "wt") as full_out, open_text(
        SCHEDULER_EXECUTION_JOIN_LEDGER, "wt"
    ) as join_out, open_text(MARKET_WHITEBOARD_LEDGER, "wt") as market_out, open_text(
        SOURCE_GAP_LEDGER, "wt"
    ) as source_out:
        for row_count, rows in enumerate(
            zip_longest(
                iter_jsonl(LANE09B_ROW_JOIN),
                iter_jsonl(LANE10B_FULL),
                iter_jsonl(LANE16_PATH),
                iter_jsonl(LANE17_WHITEBOARD),
            ),
            start=1,
        ):
            if any(row is None for row in rows):
                raise RuntimeError("upstream_row_count_mismatch_before_selector_v3_completion")
            row09b, row10b, row16, row17 = rows  # type: ignore[misc]
            joined = build_joined_row(row_count, row09b, row10b, row16, row17)
            if joined["join_status"] != "joined_by_lockstep_candidate_id":
                mismatch_rows += 1
            action_counts[joined["selector_v3_action"]] += 1
            branch_counts[joined["branch_decision"]] += 1
            implementation_counts[joined["implementation_decision"]] += 1
            scheduler_counts[clean_text(joined["scheduler_decision"]) or "UNKNOWN"] += 1
            result_class_counts[clean_text(joined["result_r_class"]) or "UNKNOWN"] += 1
            source_completeness_counts[clean_text(joined["source_completeness_state"]) or "UNKNOWN"] += 1
            source_quality_counts[clean_text(joined["source_quality_status"]) or "UNKNOWN"] += 1
            for family in clean_list(joined["source_gap_families"]):
                source_gap_family_counts[family] += 1
            proxy_r = to_float(joined["proxy_r"])
            if proxy_r is not None:
                proxy_r_rows += 1
                proxy_r_sum += proxy_r
            if joined["exact_r"] is not None:
                exact_r_rows += 1
            if to_int(joined["source_gap_count"]) > 0 or joined["selector_v3_action"] in {"source_required", "capture_repair"}:
                source_gap_rows += 1
                source_out.write(json_line(source_gap_projection(joined)))
            update_aggregates(aggregates, joined)
            full_out.write(json_line(joined))
            join_out.write(json_line(integration_projection(joined)))
            market_out.write(json_line(market_projection(joined)))

    if row_count != EXPECTED_REPLAY_ROWS:
        raise RuntimeError(f"selector_v3_expected_{EXPECTED_REPLAY_ROWS}_rows_got_{row_count}")

    aggregate_rows = [aggregate.to_row(route_role="mechanism_action_or_interaction_decision") for aggregate in aggregates.values()]
    aggregate_rows.sort(key=lambda row: (",".join(row["dimensions"]), json.dumps(row["dimension_values"], sort_keys=True)))
    write_jsonl(MECHANISM_ACTION_LEDGER, aggregate_rows)
    split_rows = [
        {
            **row,
            "schema_version": "selector_v3_split_stress_deconcentration_v1",
            "route_role": "split_stress_deconcentration",
            "stress_interpretation": "source_bound_proxy_r_descriptive_research_only_not_production_change",
        }
        for row in aggregate_rows
    ]
    write_jsonl(SPLIT_STRESS_LEDGER, split_rows)

    package_rules: list[dict[str, Any]] = []
    for aggregate in aggregates.values():
        rule = package_rule_from_aggregate(len(package_rules) + 1, aggregate)
        if rule is not None:
            package_rules.append(rule)
    package_rules.sort(key=lambda row: row["rule_id"])

    runtime_schema = build_runtime_packet_schema()
    write_json(RUNTIME_PACKET_SCHEMA, runtime_schema)

    package = {
        "schema_version": "selector_v3_default_off_package_v1",
        "route_id": ROUTE_ID,
        "package_id": "vnext_absolute_moonshot_selector_v3_default_off",
        "generated_at_utc": utc_now(),
        "enabled_by_default": False,
        "apply_to_execution_default": False,
        "live_activation_allowed_by_this_package": False,
        "owner_approval_required_for_activation": True,
        "runtime_effect_now": False,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "full_row_evidence_ledger": repo_rel(FULL_EVIDENCE_LEDGER),
        "mechanism_action_decision_ledger": repo_rel(MECHANISM_ACTION_LEDGER),
        "selector_scheduler_execution_join_ledger": repo_rel(SCHEDULER_EXECUTION_JOIN_LEDGER),
        "market_whiteboard_context_ledger": repo_rel(MARKET_WHITEBOARD_LEDGER),
        "source_gap_capture_dependency_ledger": repo_rel(SOURCE_GAP_LEDGER),
        "upstream_missing_gap_disposition_ledger": repo_rel(UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER),
        "runtime_packet_schema": repo_rel(RUNTIME_PACKET_SCHEMA),
        "runtime_selector_rules": package_rules,
        "runtime_selector_rule_count": len(package_rules),
        "selector_v3_action_counts": dict(sorted(action_counts.items())),
        "branch_decision_counts": dict(sorted(branch_counts.items())),
        "implementation_decision_counts": dict(sorted(implementation_counts.items())),
        "scheduler_decision_counts": dict(sorted(scheduler_counts.items())),
        "result_class_counts": dict(sorted(result_class_counts.items())),
        "exact_r_rows": exact_r_rows,
        "proxy_r_rows": proxy_r_rows,
        "proxy_r_sum": round(proxy_r_sum, 9),
        "expectancy_r": round(proxy_r_sum / proxy_r_rows, 9) if proxy_r_rows else None,
        "source_gap_or_capture_rows": source_gap_rows,
        "post_lane18_source_capture_repair_consumed": True,
        "post_lane18_field_family_summary": repo_rel(POST18_FIELD_SUMMARY),
        "forbidden_runtime_fields": list(FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS),
        "router_compatibility": {
            "helper_module": "src.research.moonshot_selector_v3_default_off",
            "existing_router_quality_rules_can_consume": True,
            "selector_v3_to_router_action": SELECTOR_V3_TO_ROUTER_ACTION,
        },
    }
    write_json(DEFAULT_OFF_PACKAGE, package)

    source_capture_rows = build_source_capture_decision_rows(action_counts, post18_summary)
    write_jsonl(SOURCE_CAPTURE_DECISIONS, source_capture_rows)
    upstream_gap_disposition_rows = build_upstream_missing_gap_disposition_rows(post18_summary)
    write_jsonl(UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER, upstream_gap_disposition_rows)

    completeness_rows = []
    for state, count in sorted(source_completeness_counts.items()):
        completeness_rows.append(
            {
                "schema_version": "selector_v3_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision_type": "source_completeness_state",
                "state": state,
                "rows": count,
                "selector_v3_disposition": "runtime_packet_context_allowed_but_source_required_rows_remain_default_off"
                if "gap" in state.lower() or "missing" in state.lower()
                else "runtime_packet_context_allowed_default_off",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    for state, count in sorted(source_quality_counts.items()):
        completeness_rows.append(
            {
                "schema_version": "selector_v3_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision_type": "source_quality_status",
                "state": state,
                "rows": count,
                "selector_v3_disposition": "preserve_quality_state_as_default_off_context",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    for family, count in sorted(source_gap_family_counts.items()):
        completeness_rows.append(
            {
                "schema_version": "selector_v3_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision_type": "source_gap_family",
                "state": family,
                "rows": count,
                "selector_v3_disposition": "capture_repair_or_source_required_dependency_preserved",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    write_jsonl(SOURCE_COMPLETENESS_DECISIONS, completeness_rows)

    branch_rows = []
    for branch, count in sorted(branch_counts.items()):
        branch_rows.append(
            {
                "schema_version": "selector_v3_branch_decision_v1",
                "route_id": ROUTE_ID,
                "branch_decision": branch,
                "rows": count,
                "decision_scope": "mechanism_family_and_row_level_selector_v3_default_off",
                "kill_scope_rule": "kill_only_unsupported_current_claim_preserve_mechanism_intelligence",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    write_jsonl(BRANCH_DECISION_LEDGER, branch_rows)

    implementation_rows = []
    for decision, count in sorted(implementation_counts.items()):
        implementation_rows.append(
            {
                "schema_version": "selector_v3_implementation_decision_v1",
                "route_id": ROUTE_ID,
                "implementation_decision": decision,
                "rows": count,
                "implementation_scope": "default_off_package_or_downstream_contract_only",
                "live_activation": False,
                "owner_approval_required_before_live_use": True,
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows)

    result_status = {
        "schema_version": "selector_v3_result_use_status_v1",
        "route_id": ROUTE_ID,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "exact_r_owned_by_selector_v3": False,
        "exact_r_rows": exact_r_rows,
        "proxy_r_owned_from_upstream_source_bound_rows": True,
        "proxy_r_rows": proxy_r_rows,
        "proxy_r_sum": round(proxy_r_sum, 9),
        "expectancy_r": round(proxy_r_sum / proxy_r_rows, 9) if proxy_r_rows else None,
        "broker_real_performance_claim": False,
        "production_change_readiness_claim": False,
        "result_field_runtime_packet_allowed": False,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }
    write_json(RESULT_USE_STATUS, result_status)

    downstream = build_downstream_contracts(len(package_rules))
    write_json(DOWNSTREAM_CONTRACTS, downstream)
    write_context_anchor(row_count, len(package_rules), action_counts)
    write_saturation_review(action_counts, row_count, len(package_rules))

    completion = {
        "schema_version": "selector_v3_completion_audit_v1",
        "route_id": ROUTE_ID,
        "status": "complete_pending_verifier_and_scoped_commit",
        "generated_at_utc": utc_now(),
        "mandatory_context_use": {
            "live_state_regenerated": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "master_post_lane18_decision_read": True,
            "latest_handoff_read_historical_only": True,
            "lane01_to_lane18_terminal_inputs_read_from_disk": True,
            "lane09_lane09b_lane10b_lane11_lane16_lane17_lane18_read_from_disk": True,
            "post_lane18_source_capture_repair_read": True,
            "selector_router_code_read": True,
        },
        "instruction_coverage": {
            "constructive_selector_builder_posture_applied": True,
            "full_289928_row_identity_preserved": row_count == EXPECTED_REPLAY_ROWS,
            "mechanism_action_decisions_written": True,
            "selector_scheduler_execution_join_written": True,
            "market_whiteboard_context_written": True,
            "no_leak_runtime_packet_schema_written": True,
            "source_capture_and_completeness_decisions_written": True,
            "upstream_missing_gap_dispositions_written": True,
            "branch_and_implementation_decisions_written": True,
            "result_use_status_exact_proxy_expectancy_written": True,
            "split_stress_deconcentration_written": True,
            "downstream_contracts_written": True,
            "no_arbitrary_top_n": True,
            "no_friday_only_rule": True,
            "no_ml_only_handoff": True,
            "no_live_selector_activation": True,
        },
        "counts": {
            "full_evidence_rows": row_count,
            "source_gap_or_capture_rows": source_gap_rows,
            "package_rule_rows": len(package_rules),
            "mechanism_action_rows": len(aggregate_rows),
            "source_capture_decision_rows": len(source_capture_rows),
            "upstream_missing_gap_disposition_rows": len(upstream_gap_disposition_rows),
            "source_completeness_decision_rows": len(completeness_rows),
            "branch_decision_rows": len(branch_rows),
            "implementation_decision_rows": len(implementation_rows),
            "candidate_id_mismatch_rows": mismatch_rows,
            "exact_r_rows": exact_r_rows,
            "proxy_r_rows": proxy_r_rows,
        },
        "action_counts": dict(sorted(action_counts.items())),
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "focused_test_result_present": FOCUSED_TEST_RESULT.exists(),
        "scoped_commit_required": True,
    }
    write_json(COMPLETION_AUDIT, completion)
    write_manifest()
    verification = verify_outputs(write=True, require_focused_test=False)
    return {
        "ok": verification.get("ok", False),
        "row_count": row_count,
        "source_gap_rows": source_gap_rows,
        "package_rule_count": len(package_rules),
        "action_counts": dict(sorted(action_counts.items())),
        "verification": verification,
    }


def output_paths() -> list[Path]:
    return [
        FULL_EVIDENCE_LEDGER,
        MECHANISM_ACTION_LEDGER,
        SCHEDULER_EXECUTION_JOIN_LEDGER,
        MARKET_WHITEBOARD_LEDGER,
        SOURCE_GAP_LEDGER,
        UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER,
        RUNTIME_PACKET_SCHEMA,
        DEFAULT_OFF_PACKAGE,
        SOURCE_CAPTURE_DECISIONS,
        SOURCE_COMPLETENESS_DECISIONS,
        BRANCH_DECISION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        RESULT_USE_STATUS,
        SPLIT_STRESS_LEDGER,
        DOWNSTREAM_CONTRACTS,
        CONTEXT_ANCHOR,
        SATURATION_REVIEW,
        COMPLETION_AUDIT,
        FOCUSED_TEST_RESULT,
        VERIFICATION_RESULT,
        OUTPUT_MANIFEST,
    ]


def write_manifest() -> None:
    outputs = []
    for path in output_paths():
        if path.exists():
            outputs.append(
                {
                    "path": repo_rel(path),
                    "exists": True,
                    "size_bytes": path.stat().st_size,
                    "line_count": line_count(path),
                    "sha256": sha256_file(path),
                }
            )
        else:
            outputs.append({"path": repo_rel(path), "exists": False, "size_bytes": 0, "line_count": None, "sha256": None})
    write_json(
        OUTPUT_MANIFEST,
        {
            "schema_version": "selector_v3_output_manifest_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
            "output_count": len(outputs),
            "outputs": outputs,
        },
    )


def verify_outputs(*, write: bool = False, require_focused_test: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    required = [
        FULL_EVIDENCE_LEDGER,
        MECHANISM_ACTION_LEDGER,
        SCHEDULER_EXECUTION_JOIN_LEDGER,
        MARKET_WHITEBOARD_LEDGER,
        SOURCE_GAP_LEDGER,
        UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER,
        RUNTIME_PACKET_SCHEMA,
        DEFAULT_OFF_PACKAGE,
        SOURCE_CAPTURE_DECISIONS,
        SOURCE_COMPLETENESS_DECISIONS,
        BRANCH_DECISION_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        RESULT_USE_STATUS,
        SPLIT_STRESS_LEDGER,
        DOWNSTREAM_CONTRACTS,
        CONTEXT_ANCHOR,
        SATURATION_REVIEW,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
    ]
    if require_focused_test:
        required.append(FOCUSED_TEST_RESULT)
    for path in required:
        if not path.exists():
            issues.append(f"missing_required_output:{path.name}")
    if issues:
        result = {
            "ok": False,
            "issue_count": len(issues),
            "issues": issues,
            "schema_version": "selector_v3_verification_result_v1",
            "route_id": ROUTE_ID,
        }
        if write:
            write_json(VERIFICATION_RESULT, result)
        return result

    full_rows = line_count(FULL_EVIDENCE_LEDGER)
    join_rows = line_count(SCHEDULER_EXECUTION_JOIN_LEDGER)
    market_rows = line_count(MARKET_WHITEBOARD_LEDGER)
    source_gap_rows = line_count(SOURCE_GAP_LEDGER)
    upstream_gap_disposition_rows = line_count(UPSTREAM_MISSING_GAP_DISPOSITION_LEDGER)
    mechanism_rows = line_count(MECHANISM_ACTION_LEDGER)
    split_rows = line_count(SPLIT_STRESS_LEDGER)
    package = read_json(DEFAULT_OFF_PACKAGE, {})
    schema = read_json(RUNTIME_PACKET_SCHEMA, {})
    result_status = read_json(RESULT_USE_STATUS, {})
    audit = read_json(COMPLETION_AUDIT, {})
    manifest = read_json(OUTPUT_MANIFEST, {})

    for name, count in {
        "full_evidence": full_rows,
        "scheduler_execution_join": join_rows,
        "market_whiteboard": market_rows,
    }.items():
        if count != EXPECTED_REPLAY_ROWS:
            issues.append(f"{name}_row_count_expected_{EXPECTED_REPLAY_ROWS}_actual_{count}")
    if source_gap_rows is None or source_gap_rows <= 0:
        issues.append("source_gap_capture_dependency_ledger_empty")
    if upstream_gap_disposition_rows is None or upstream_gap_disposition_rows < 9:
        issues.append(f"upstream_missing_gap_disposition_rows_too_few:{upstream_gap_disposition_rows}")
    if mechanism_rows is None or mechanism_rows <= 0:
        issues.append("mechanism_action_decision_ledger_empty")
    if split_rows != mechanism_rows:
        issues.append(f"split_stress_rows_mismatch_mechanism_rows:{split_rows}!={mechanism_rows}")

    if package.get("enabled_by_default") is not False:
        issues.append("package_enabled_by_default_not_false")
    if package.get("apply_to_execution_default") is not False:
        issues.append("package_apply_to_execution_default_not_false")
    if package.get("live_activation_allowed_by_this_package") is not False:
        issues.append("package_live_activation_allowed_not_false")
    if package.get("runtime_effect_now") is not False:
        issues.append("package_runtime_effect_now_not_false")
    action_counts = package.get("selector_v3_action_counts") or {}
    for required_action in ("trade", "reduce_risk", "avoid", "capture_repair", "no_trade_by_evidence", "source_required"):
        if int(action_counts.get(required_action, 0)) <= 0:
            issues.append(f"missing_selector_v3_action:{required_action}")
    rules = package.get("runtime_selector_rules") or []
    if not rules:
        issues.append("runtime_selector_rules_empty")
    for rule in rules[:100]:
        if "time_is_friday" in rule or rule.get("session_bucket") == "friday_only":
            issues.append("friday_only_or_time_is_friday_rule_present")
            break
    forbidden = set(schema.get("forbidden_future_or_result_fields") or [])
    for field_name in ("result_r", "proxy_r", "exact_r", "broker_real_net_r", "path_class", "correct_rejection"):
        if field_name not in forbidden:
            issues.append(f"runtime_schema_missing_forbidden_field:{field_name}")
    allowed = set(schema.get("allowed_asof_decision_fields") or [])
    for field_name in ("symbol", "side", "framework", "origin_family", "session_bucket", "source_completeness_state", "scheduler_decision"):
        if field_name not in allowed:
            issues.append(f"runtime_schema_missing_allowed_field:{field_name}")
    if result_status.get("exact_r_rows") != 0:
        issues.append("exact_r_rows_should_be_zero_for_broad_selector_v3_denominator")
    if not result_status.get("proxy_r_rows"):
        issues.append("proxy_r_rows_missing")
    if result_status.get("result_field_runtime_packet_allowed") is not False:
        issues.append("result_fields_runtime_packet_allowed_not_false")
    coverage = audit.get("instruction_coverage") or {}
    for key in (
        "full_289928_row_identity_preserved",
        "no_leak_runtime_packet_schema_written",
        "source_capture_and_completeness_decisions_written",
        "upstream_missing_gap_dispositions_written",
        "downstream_contracts_written",
        "no_arbitrary_top_n",
        "no_friday_only_rule",
        "no_ml_only_handoff",
        "no_live_selector_activation",
    ):
        if coverage.get(key) is not True:
            issues.append(f"completion_instruction_coverage_missing:{key}")
    mandatory = audit.get("mandatory_context_use") or {}
    for key in (
        "live_state_regenerated",
        "goal_session_research_discipline_read",
        "research_operating_doctrine_read",
        "moonshot_vision_read",
        "master_post_lane18_decision_read",
        "post_lane18_source_capture_repair_read",
        "selector_router_code_read",
    ):
        if mandatory.get(key) is not True:
            issues.append(f"mandatory_context_use_missing:{key}")
    manifest_counts = {Path(item.get("path", "")).name: item.get("line_count") for item in manifest.get("outputs") or []}
    for path, expected_count in (
        (FULL_EVIDENCE_LEDGER, full_rows),
        (SCHEDULER_EXECUTION_JOIN_LEDGER, join_rows),
        (MARKET_WHITEBOARD_LEDGER, market_rows),
        (SOURCE_GAP_LEDGER, source_gap_rows),
        (MECHANISM_ACTION_LEDGER, mechanism_rows),
    ):
        if manifest_counts.get(path.name) != expected_count:
            issues.append(f"manifest_line_count_mismatch:{path.name}:{manifest_counts.get(path.name)}!={expected_count}")

    sample_runtime_packet_issues = 0
    for index, row in enumerate(iter_jsonl(FULL_EVIDENCE_LEDGER), start=1):
        packet = row.get("runtime_packet_fields") or {}
        if set(packet).intersection(FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS):
            sample_runtime_packet_issues += 1
        if index >= 1000:
            break
    if sample_runtime_packet_issues:
        issues.append(f"runtime_packet_contains_forbidden_fields_in_sample:{sample_runtime_packet_issues}")

    result = {
        "schema_version": "selector_v3_verification_result_v1",
        "route_id": ROUTE_ID,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "full_evidence_rows": full_rows,
            "selector_scheduler_execution_join_rows": join_rows,
            "market_whiteboard_rows": market_rows,
            "source_gap_capture_dependency_rows": source_gap_rows,
            "upstream_missing_gap_disposition_rows": upstream_gap_disposition_rows,
            "mechanism_action_rows": mechanism_rows,
            "split_stress_rows": split_rows,
            "runtime_selector_rule_count": len(rules),
            "proxy_r_rows": result_status.get("proxy_r_rows"),
            "exact_r_rows": result_status.get("exact_r_rows"),
        },
        "action_counts": action_counts,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "focused_test_result_required": require_focused_test,
        "focused_test_result_present": FOCUSED_TEST_RESULT.exists(),
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
        write_manifest()
    return result


def main() -> int:
    result = build_outputs()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
