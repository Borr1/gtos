from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "moonshot_frozen_universe_cp281_runtime_mapping_v1"
SURFACE = "src/research_infra/moonshot_frozen_universe_cp281_runtime_mapping.py"
BOUNDARY_SCHEMA = "main_side_cp281_ready_runtime_default_off_registry_v1"

DEFAULT_RULE_MAPPING_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_RULE_LEDGER_2026-05-18.jsonl"
)
DEFAULT_AGGREGATE_MAPPING_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_AGGREGATE_LEDGER_2026-05-18.jsonl"
)
DEFAULT_BRANCH_DECISION_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_BRANCH_DECISIONS_LEDGER_2026-05-18.jsonl"
)
DEFAULT_RULE_REPLAY_RESULT_TABLE_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_RESULT_TABLE_LEDGER_2026-05-18.jsonl"
)
RULE_REPLAY_SOURCE_EVIDENCE_ROLE = "CP281_NATIVE_RULE_REPLAY_EVENT_FROM_HISTORICAL_READY_SLICE"
LIVE_SHADOW_SECONDARY_ROLE = "SECONDARY_EVENT_FIELD_INTEGRATION_EVIDENCE_ONLY_NOT_STRATEGY_EVIDENCE"
DEFAULT_RULE_REPLAY_RESULT_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("overall", ()),
    ("action_class", ("matched_action_class",)),
    ("symbol_family", ("symbol_family",)),
    ("market", ("source_symbol",)),
    ("timeframe", ("market_timeframe",)),
    ("session", ("route_session",)),
    ("horizon", ("horizon_id",)),
    ("side", ("side",)),
    ("branch", ("keep_kill_redesign_implement_decision",)),
    ("main_system_surface", ("main_system_surface",)),
    ("symbol_family_market_timeframe", ("symbol_family", "market_timeframe")),
    ("symbol_family_session", ("symbol_family", "route_session")),
    (
        "symbol_family_market_timeframe_session_horizon_side",
        ("symbol_family", "source_symbol", "market_timeframe", "route_session", "horizon_id", "side"),
    ),
    (
        "follow_vs_avoid_scope",
        ("matched_action_class", "symbol_family", "source_symbol", "market_timeframe", "route_session", "horizon_id", "side"),
    ),
    ("rule", ("matched_cp281_rule_row_id",)),
)

MATCH_FIELD_ALIASES = {
    "market_timeframe": ("market_timeframe", "timeframe"),
    "route_session": ("route_session", "session", "kill_zone"),
    "side": ("side", "selected_side", "direction", "candidate_side"),
}
CP281_SCOPE_REQUIRED_FIELDS = (
    "symbol_family",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
)
CP281_SOURCE_HASH_REQUIRED_FIELDS = ("source_path_sha256", "source_file_sha256")


def stable_hash(payload: Any, length: int = 64) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def safe_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "main_side_default_off_cp281_ready_runtime_registry",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "paid_api_or_vendor_call": False,
        "broker_operation": False,
        "replay_r_reference_counted_as_new_main_result": False,
    }


def surface_for_action_class(action_class: str | None) -> dict[str, str]:
    text = normalized(action_class)
    if text == "follow_rule":
        return {
            "main_system_surface": "cp281_default_off_follow_scorer_registry",
            "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_FOLLOW_SCORER_RULE",
            "main_surface_status": "READY_DEFAULT_OFF_CP281_FOLLOW_SCORER_RULE",
            "strategy_surface": "strategy_follow_candidates_and_evaluations",
            "implementation_decision": "IMPLEMENT_DEFAULT_OFF_FOLLOW_SCORER_RULE",
        }
    if text == "avoid_filter":
        return {
            "main_system_surface": "cp281_default_off_avoid_filter_registry",
            "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
            "main_surface_status": "READY_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
            "strategy_surface": "gate_filter_selector_avoid_filter_evaluation",
            "implementation_decision": "IMPLEMENT_DEFAULT_OFF_AVOID_FILTER_RULE",
        }
    return {
        "main_system_surface": "cp281_unclassified_ready_runtime_registry",
        "main_surface_action": "PRESERVE_CP281_RUNTIME_RULE_FOR_CLASSIFICATION_REPAIR",
        "main_surface_status": "CP281_RUNTIME_RULE_CLASSIFICATION_REPAIR_REQUIRED",
        "strategy_surface": "classification_repair",
        "implementation_decision": "REPAIR_ACTION_CLASS_BEFORE_RUNTIME_MAPPING",
    }


def r_sign(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "non_numeric"
    if number > 0:
        return "positive"
    if number < 0:
        return "negative"
    return "zero"


def _self_tests_by_rule_id(self_test_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalized(row.get("input_runtime_rule_row_id")): row for row in self_test_rows}


def build_rule_mapping_rows(
    rule_rows: Iterable[dict[str, Any]],
    self_test_rows: Iterable[dict[str, Any]],
    *,
    source_rule_artifact: str,
    source_rule_artifact_sha256: str,
    source_self_test_artifact: str,
    source_self_test_artifact_sha256: str,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> list[dict[str, Any]]:
    self_tests = _self_tests_by_rule_id(self_test_rows)
    rows: list[dict[str, Any]] = []
    for line_no, rule in enumerate(rule_rows, start=1):
        rule_id = normalized(rule.get("frozen_ready_action_runtime_rule_row_id"))
        action_class = normalized(rule.get("action_class"))
        surface = surface_for_action_class(action_class)
        match_fields = list(rule.get("match_fields") or [])
        match_scope = dict(rule.get("match_scope") or {})
        self_test = self_tests.get(rule_id, {})
        missing_match_fields = list(rule.get("missing_match_fields") or [])
        self_test_pass = normalized(self_test.get("self_test_status")) == "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS"
        contract_ready = not missing_match_fields and bool(match_fields) and self_test_pass
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_ready_runtime_rule_to_main_system_surface",
                "row_key": stable_hash(["cp281_rule_mapping", rule_id, action_class, match_scope]),
                "cp281_rule_row_id": rule_id,
                "input_implementation_ready_bundle_row_id": rule.get("input_implementation_ready_bundle_row_id"),
                "action_class": action_class,
                "main_system_surface": surface["main_system_surface"],
                "main_surface_action": surface["main_surface_action"],
                "main_surface_status": surface["main_surface_status"],
                "main_surface_module": SURFACE,
                "strategy_surface": surface["strategy_surface"],
                "implementation_decision": surface["implementation_decision"],
                "downstream_system_action": (
                    "EVALUATE_ONLY_THROUGH_DEFAULT_OFF_CP281_READY_RUNTIME_REGISTRY_UNTIL_PRODUCTION_REVIEW"
                ),
                "branch_local_runtime_role": rule.get("branch_local_runtime_role"),
                "keep_kill_redesign_implement_decision": rule.get("keep_kill_redesign_implement_decision"),
                "symbol_family": rule.get("symbol_family"),
                "symbol": rule.get("symbol"),
                "source_symbol": rule.get("source_symbol"),
                "market_timeframe": rule.get("market_timeframe"),
                "route_session": rule.get("route_session"),
                "horizon_id": rule.get("horizon_id"),
                "side": rule.get("side"),
                "match_fields": match_fields,
                "match_scope": match_scope,
                "missing_match_fields": missing_match_fields,
                "source_capture_contract_ready": contract_ready,
                "source_capture_contract_status": (
                    "READY_DEFAULT_OFF_CP281_RULE_EVENT_CONTRACT"
                    if contract_ready
                    else "CP281_RULE_EVENT_CONTRACT_REPAIR_REQUIRED"
                ),
                "cost_adjusted_simulated_r": rounded(safe_float(rule.get("cost_adjusted_simulated_r"))),
                "gross_simulated_r": rounded(safe_float(rule.get("gross_simulated_r"))),
                "stress_simulated_r": rounded(safe_float(rule.get("stress_simulated_r"))),
                "simulated_r_sign": r_sign(rule.get("cost_adjusted_simulated_r")),
                "effective_n": rounded(safe_float(rule.get("effective_n"))),
                "rule_expression_sha256": rule.get("rule_expression_sha256"),
                "self_test_row_id": self_test.get("frozen_ready_action_runtime_self_test_row_id"),
                "self_test_status": self_test.get("self_test_status"),
                "self_test_matched": bool(self_test.get("matched")),
                "self_test_has_cost_stress_evidence": bool(self_test.get("has_cost_stress_evidence")),
                "source_ownership": {
                    "source_rule_artifact": source_rule_artifact,
                    "source_rule_artifact_sha256": source_rule_artifact_sha256,
                    "source_rule_line_no": line_no,
                    "source_self_test_artifact": source_self_test_artifact,
                    "source_self_test_artifact_sha256": source_self_test_artifact_sha256,
                    "source_action_closure_artifact": rule.get("source_action_closure_artifact"),
                    "source_action_closure_row_count": rule.get("source_action_closure_row_count"),
                    "source_path": rule.get("source_path"),
                    "source_path_sha256": rule.get("source_path_sha256"),
                    "source_file_sha256": rule.get("source_file_sha256"),
                    "source_row_count": rule.get("source_row_count"),
                    "source_row_ids_sha256": rule.get("source_row_ids_sha256"),
                },
                "moonshot_snapshot": {
                    "worktree_head": moonshot_head,
                    "status_clean": moonshot_status_clean,
                },
                "tests_needed": list(rule.get("tests_needed") or []),
                "parked_state": {
                    "is_parked": not contract_ready,
                    "reason": None if contract_ready else "MISSING_MATCH_FIELDS_OR_FAILED_SELF_TEST",
                },
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_aggregate_mapping_rows(
    aggregate_rows: Iterable[dict[str, Any]],
    *,
    source_aggregate_artifact: str,
    source_aggregate_artifact_sha256: str,
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, aggregate in enumerate(aggregate_rows, start=1):
        action_class = normalized(aggregate.get("action_class"))
        surface = surface_for_action_class(action_class)
        aggregate_scope = {
            "action_class": action_class,
            "symbol_family": aggregate.get("symbol_family"),
            "market_timeframe": aggregate.get("market_timeframe"),
            "route_session": aggregate.get("route_session"),
            "horizon_id": aggregate.get("horizon_id"),
            "side": aggregate.get("side"),
        }
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_ready_runtime_aggregate_to_main_system_surface",
                "row_key": stable_hash(["cp281_aggregate_mapping", aggregate_scope]),
                "cp281_aggregate_row_id": aggregate.get("frozen_ready_action_runtime_aggregate_row_id"),
                "action_class": action_class,
                "main_system_surface": surface["main_system_surface"],
                "main_surface_action": surface["main_surface_action"],
                "main_surface_status": surface["main_surface_status"],
                "main_surface_module": SURFACE,
                "aggregate_scope": aggregate_scope,
                "rule_count": int(aggregate.get("rule_count") or 0),
                "source_row_count": int(aggregate.get("source_row_count") or 0),
                "average_cost_adjusted_simulated_r": rounded(
                    safe_float(aggregate.get("average_cost_adjusted_simulated_r"))
                ),
                "average_stress_simulated_r": rounded(safe_float(aggregate.get("average_stress_simulated_r"))),
                "effective_n_sum": rounded(safe_float(aggregate.get("effective_n_sum"))),
                "source_ownership": {
                    "source_aggregate_artifact": source_aggregate_artifact,
                    "source_aggregate_artifact_sha256": source_aggregate_artifact_sha256,
                    "source_aggregate_line_no": line_no,
                },
                "moonshot_snapshot": {
                    "worktree_head": moonshot_head,
                    "status_clean": moonshot_status_clean,
                },
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_source_capture_contract_rows(rule_mapping_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mapping in rule_mapping_rows:
        required_fields = list(mapping.get("match_fields") or [])
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_ready_runtime_rule_event_contract",
                "row_key": stable_hash(["cp281_event_contract", mapping.get("cp281_rule_row_id"), required_fields]),
                "cp281_rule_row_id": mapping.get("cp281_rule_row_id"),
                "action_class": mapping.get("action_class"),
                "main_system_surface": mapping.get("main_system_surface"),
                "event_required_fields": required_fields,
                "event_required_field_count": len(required_fields),
                "event_required_field_aliases": {
                    field: list(MATCH_FIELD_ALIASES.get(field, (field,))) for field in required_fields
                },
                "source_capture_contract_status": mapping.get("source_capture_contract_status"),
                "source_capture_contract_ready": bool(mapping.get("source_capture_contract_ready")),
                "match_scope": dict(mapping.get("match_scope") or {}),
                "missing_match_fields": list(mapping.get("missing_match_fields") or []),
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def _event_value(event: dict[str, Any], field: str) -> str:
    if field == "matched_action_class":
        for alias in ("matched_action_class", "action_class", "source_action_class"):
            value = normalized(event.get(alias))
            if value:
                return value
        return ""
    if field == "matched_cp281_rule_row_id":
        for alias in ("matched_cp281_rule_row_id", "cp281_rule_row_id", "source_cp281_rule_row_id"):
            value = normalized(event.get(alias))
            if value:
                return value
        return ""
    for alias in MATCH_FIELD_ALIASES.get(field, (field,)):
        value = normalized(event.get(alias))
        if value:
            return value
    return ""


def cp281_contract_required_fields(contract_rows: Iterable[dict[str, Any]]) -> list[str]:
    fields = sorted({field for row in contract_rows for field in row.get("event_required_fields") or []})
    return fields


def cp281_field_present(row: dict[str, Any], field: str) -> bool:
    return bool(_event_value(row, field))


def cp281_audit_event_source_rows(
    source_rows: Iterable[dict[str, Any]],
    *,
    required_fields: list[str],
) -> dict[str, Any]:
    row_count = 0
    field_presence_counts = Counter()
    rows_with_scope_required_fields = 0
    rows_with_source_hash_required_fields = 0
    rows_with_all_required_fields = 0
    scope_fields = [field for field in CP281_SCOPE_REQUIRED_FIELDS if field in required_fields]
    source_hash_fields = [field for field in CP281_SOURCE_HASH_REQUIRED_FIELDS if field in required_fields]
    for row in source_rows:
        row_count += 1
        present = {field for field in required_fields if cp281_field_present(row, field)}
        field_presence_counts.update(present)
        if all(field in present for field in scope_fields):
            rows_with_scope_required_fields += 1
        if all(field in present for field in source_hash_fields):
            rows_with_source_hash_required_fields += 1
        if all(field in present for field in required_fields):
            rows_with_all_required_fields += 1

    missing_required_fields = [field for field in required_fields if field_presence_counts.get(field, 0) == 0]
    if rows_with_all_required_fields:
        status = "CURRENT_SOURCE_CAN_FEED_CP281_READY_RUNTIME_REGISTRY"
        repair_action = "USE_FOR_DEFAULT_OFF_CP281_REGISTRY_EVENT_REPLAY"
    elif rows_with_scope_required_fields:
        status = "CURRENT_SOURCE_HAS_CP281_SCOPE_BUT_MISSING_SOURCE_HASH_CONTRACT"
        repair_action = "ADD_SOURCE_PATH_SHA256_AND_SOURCE_FILE_SHA256_TO_EVENT_OUTPUT"
    else:
        status = "CURRENT_SOURCE_MISSING_CP281_READY_RUNTIME_CONTRACT_FIELDS"
        repair_action = "ADD_CP281_SCOPE_AND_SOURCE_HASH_FIELDS_TO_EVENT_OUTPUT"

    return {
        "event_source_rows": row_count,
        "required_field_presence_counts": dict(sorted(field_presence_counts.items())),
        "missing_required_fields": missing_required_fields,
        "rows_with_scope_required_fields": rows_with_scope_required_fields,
        "rows_with_source_hash_required_fields": rows_with_source_hash_required_fields,
        "rows_with_all_required_fields": rows_with_all_required_fields,
        "field_availability_status": status,
        "source_capture_repair_action": repair_action,
    }


def event_matches_rule_mapping(event: dict[str, Any], mapping: dict[str, Any]) -> bool:
    scope = mapping.get("match_scope") or {}
    for field in mapping.get("match_fields") or []:
        if _event_value(event, field) != normalized(scope.get(field)):
            return False
    return True


def event_from_rule_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    scope = dict(mapping.get("match_scope") or {})
    event = dict(scope)
    if scope.get("side") is not None:
        event["selected_side"] = scope.get("side")
    if scope.get("market_timeframe") is not None:
        event["timeframe"] = scope.get("market_timeframe")
    if scope.get("route_session") is not None:
        event["session"] = scope.get("route_session")
    return event


class CP281ReadyRuntimeRegistry:
    """Default-off evaluator over CP281 executable ready-rule mappings."""

    def __init__(self, rule_mappings: list[dict[str, Any]]) -> None:
        self.rule_mappings = list(rule_mappings)

    @classmethod
    def from_jsonl(cls, path: Path | str = DEFAULT_RULE_MAPPING_LEDGER) -> "CP281ReadyRuntimeRegistry":
        return cls(read_jsonl(path))

    def evaluate_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for mapping in self.rule_mappings:
            if not event_matches_rule_mapping(event, mapping):
                continue
            matches.append(
                {
                    "cp281_rule_row_id": mapping.get("cp281_rule_row_id"),
                    "action_class": mapping.get("action_class"),
                    "main_system_surface": mapping.get("main_system_surface"),
                    "main_surface_action": mapping.get("main_surface_action"),
                    "main_surface_status": mapping.get("main_surface_status"),
                    "symbol_family": mapping.get("symbol_family"),
                    "symbol": mapping.get("symbol"),
                    "source_symbol": mapping.get("source_symbol"),
                    "market_timeframe": mapping.get("market_timeframe"),
                    "route_session": mapping.get("route_session"),
                    "horizon_id": mapping.get("horizon_id"),
                    "side": mapping.get("side"),
                    "cost_adjusted_simulated_r": mapping.get("cost_adjusted_simulated_r"),
                    "gross_simulated_r": mapping.get("gross_simulated_r"),
                    "stress_simulated_r": mapping.get("stress_simulated_r"),
                    "effective_n": mapping.get("effective_n"),
                    "strategy_surface": mapping.get("strategy_surface"),
                    "implementation_decision": mapping.get("implementation_decision"),
                    "branch_local_runtime_role": mapping.get("branch_local_runtime_role"),
                    "keep_kill_redesign_implement_decision": mapping.get("keep_kill_redesign_implement_decision"),
                    "source_ownership": mapping.get("source_ownership"),
                    "registry_evaluation_status": "DEFAULT_OFF_CP281_READY_RUNTIME_RULE_MATCH",
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "research_boundary": research_boundary(),
                }
            )
        return matches

    def summarize_registry(self) -> dict[str, Any]:
        return {
            "rule_mapping_rows": len(self.rule_mappings),
            "action_class_counts": dict(
                sorted(Counter(normalized(row.get("action_class")) for row in self.rule_mappings).items())
            ),
            "main_system_surface_counts": dict(
                sorted(Counter(normalized(row.get("main_system_surface")) for row in self.rule_mappings).items())
            ),
            "runtime_candidate_use_permitted_rows": sum(
                bool(row.get("runtime_candidate_use_permitted")) for row in self.rule_mappings
            ),
            "candidate_use_allowed_now_rows": sum(
                bool(row.get("candidate_use_allowed_now")) for row in self.rule_mappings
            ),
        }


def build_registry_self_check_rows(rule_mapping_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    registry = CP281ReadyRuntimeRegistry(rule_mapping_rows)
    rows: list[dict[str, Any]] = []
    for mapping in rule_mapping_rows:
        event = event_from_rule_mapping(mapping)
        matches = registry.evaluate_event(event)
        own_id = mapping.get("cp281_rule_row_id")
        matched_self = any(match.get("cp281_rule_row_id") == own_id for match in matches)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_ready_runtime_registry_self_check",
                "row_key": stable_hash(["cp281_registry_self_check", own_id]),
                "cp281_rule_row_id": own_id,
                "action_class": mapping.get("action_class"),
                "main_system_surface": mapping.get("main_system_surface"),
                "event_payload": event,
                "matched_self": matched_self,
                "matched_rule_count": len(matches),
                "matched_rule_ids_sha256": stable_hash([match.get("cp281_rule_row_id") for match in matches]),
                "self_check_status": (
                    "CP281_READY_RUNTIME_REGISTRY_SELF_CHECK_PASS"
                    if matched_self
                    else "CP281_READY_RUNTIME_REGISTRY_SELF_CHECK_REPAIR_REQUIRED"
                ),
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_rule_replay_event_rows(rule_mapping_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, mapping in enumerate(rule_mapping_rows, start=1):
        event_payload = event_from_rule_mapping(mapping)
        match_scope = dict(mapping.get("match_scope") or {})
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_rule_replay_event",
                "row_key": stable_hash(["cp281_rule_replay_event", mapping.get("cp281_rule_row_id")]),
                "cp281_rule_replay_event_id": f"CP281-RULE-REPLAY-EVENT-{index:04d}",
                "source_cp281_rule_row_id": mapping.get("cp281_rule_row_id"),
                "source_mapping_row_key": mapping.get("row_key"),
                "source_action_class": mapping.get("action_class"),
                "source_main_system_surface": mapping.get("main_system_surface"),
                "source_main_surface_action": mapping.get("main_surface_action"),
                "source_main_surface_status": mapping.get("main_surface_status"),
                "source_strategy_surface": mapping.get("strategy_surface"),
                "source_implementation_decision": mapping.get("implementation_decision"),
                "branch_local_runtime_role": mapping.get("branch_local_runtime_role"),
                "keep_kill_redesign_implement_decision": mapping.get("keep_kill_redesign_implement_decision"),
                "symbol_family": mapping.get("symbol_family"),
                "symbol": mapping.get("symbol"),
                "source_symbol": mapping.get("source_symbol"),
                "market_timeframe": mapping.get("market_timeframe"),
                "route_session": mapping.get("route_session"),
                "horizon_id": mapping.get("horizon_id"),
                "side": mapping.get("side"),
                "source_path_sha256": match_scope.get("source_path_sha256"),
                "source_file_sha256": match_scope.get("source_file_sha256"),
                "event_payload": event_payload,
                "event_required_fields": list(mapping.get("match_fields") or []),
                "event_required_field_count": len(mapping.get("match_fields") or []),
                "event_materialization_status": "CP281_RULE_REPLAY_EVENT_MATERIALIZED_FROM_READY_RUNTIME_MAPPING",
                "source_evidence_role": RULE_REPLAY_SOURCE_EVIDENCE_ROLE,
                "live_shadow_matching_role": LIVE_SHADOW_SECONDARY_ROLE,
                "source_operation": "SOURCE_ARTIFACT_RULE_REPLAY_EVENT_PRODUCTION",
                "cost_adjusted_simulated_r": mapping.get("cost_adjusted_simulated_r"),
                "gross_simulated_r": mapping.get("gross_simulated_r"),
                "stress_simulated_r": mapping.get("stress_simulated_r"),
                "effective_n": mapping.get("effective_n"),
                "simulated_r_sign": mapping.get("simulated_r_sign"),
                "source_ownership": mapping.get("source_ownership"),
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_rule_replay_match_rows(
    event_rows: list[dict[str, Any]],
    *,
    registry: CP281ReadyRuntimeRegistry,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event_row in event_rows:
        matches = registry.evaluate_event(event_row.get("event_payload") or event_row)
        duplicate_rule_match = len(matches) > 1
        for match_index, match in enumerate(matches, start=1):
            own_rule_match = match.get("cp281_rule_row_id") == event_row.get("source_cp281_rule_row_id")
            action_conflict = normalized(match.get("action_class")) != normalized(event_row.get("source_action_class"))
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "cp281_rule_replay_match",
                    "row_key": stable_hash(
                        [
                            "cp281_rule_replay_match",
                            event_row.get("cp281_rule_replay_event_id"),
                            match.get("cp281_rule_row_id"),
                            match_index,
                        ]
                    ),
                    "cp281_rule_replay_event_id": event_row.get("cp281_rule_replay_event_id"),
                    "source_cp281_rule_row_id": event_row.get("source_cp281_rule_row_id"),
                    "matched_cp281_rule_row_id": match.get("cp281_rule_row_id"),
                    "match_index_for_event": match_index,
                    "matched_rule_count_for_event": len(matches),
                    "own_rule_match": own_rule_match,
                    "duplicate_rule_match": duplicate_rule_match,
                    "action_conflict_with_source_event": action_conflict,
                    "source_action_class": event_row.get("source_action_class"),
                    "matched_action_class": match.get("action_class"),
                    "main_system_surface": match.get("main_system_surface"),
                    "main_surface_action": match.get("main_surface_action"),
                    "main_surface_status": match.get("main_surface_status"),
                    "strategy_surface": match.get("strategy_surface"),
                    "implementation_decision": match.get("implementation_decision"),
                    "branch_local_runtime_role": match.get("branch_local_runtime_role"),
                    "keep_kill_redesign_implement_decision": match.get("keep_kill_redesign_implement_decision"),
                    "symbol_family": match.get("symbol_family"),
                    "symbol": match.get("symbol"),
                    "source_symbol": match.get("source_symbol"),
                    "market_timeframe": match.get("market_timeframe"),
                    "route_session": match.get("route_session"),
                    "horizon_id": match.get("horizon_id"),
                    "side": match.get("side"),
                    "matched_cost_adjusted_simulated_r": match.get("cost_adjusted_simulated_r"),
                    "matched_gross_simulated_r": match.get("gross_simulated_r"),
                    "matched_stress_simulated_r": match.get("stress_simulated_r"),
                    "matched_effective_n": match.get("effective_n"),
                    "source_evidence_role": RULE_REPLAY_SOURCE_EVIDENCE_ROLE,
                    "live_shadow_matching_role": LIVE_SHADOW_SECONDARY_ROLE,
                    "source_ownership": match.get("source_ownership") or event_row.get("source_ownership"),
                    "registry_evaluation_status": match.get("registry_evaluation_status"),
                    "production_change_approved": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "research_boundary": research_boundary(),
                }
            )
    return rows


def _counter(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(normalized(row.get(field)) for row in rows).items()))


def _numeric_summary(values: Iterable[Any]) -> dict[str, Any]:
    numbers = [value for value in (safe_float(value) for value in values) if value is not None]
    if not numbers:
        return {"count": 0, "min": None, "max": None, "mean": None, "sum": None}
    return {
        "count": len(numbers),
        "min": rounded(min(numbers)),
        "max": rounded(max(numbers)),
        "mean": rounded(sum(numbers) / len(numbers)),
        "sum": rounded(sum(numbers)),
    }


def _follow_vs_avoid_role(action_counts: dict[str, int]) -> str:
    has_follow = action_counts.get("follow_rule", 0) > 0
    has_avoid = action_counts.get("avoid_filter", 0) > 0
    if has_follow and has_avoid:
        return "follow_and_avoid_mixed"
    if has_follow:
        return "follow_rule_only"
    if has_avoid:
        return "avoid_filter_only"
    return "unclassified"


def build_rule_replay_result_table_rows(
    match_rows: list[dict[str, Any]],
    *,
    group_specs: tuple[tuple[str, tuple[str, ...]], ...] = DEFAULT_RULE_REPLAY_RESULT_GROUPS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_name, fields in group_specs:
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        for match in match_rows:
            key = tuple(normalized(match.get(field)) for field in fields)
            groups.setdefault(key, []).append(match)

        for key, members in sorted(groups.items(), key=lambda item: item[0]):
            dimensions = {field: key[index] for index, field in enumerate(fields)}
            action_counts = _counter(members, "matched_action_class")
            matched_rule_ids = sorted({normalized(row.get("matched_cp281_rule_row_id")) for row in members})
            replay_event_ids = sorted({normalized(row.get("cp281_rule_replay_event_id")) for row in members})
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "cp281_rule_replay_result_table",
                    "row_key": stable_hash(["cp281_rule_replay_result_table", group_name, dimensions]),
                    "result_table_group": group_name,
                    "result_table_dimensions": dimensions,
                    "result_table_dimension_key": "|".join(key) if key else "ALL",
                    "rule_replay_match_rows": len(members),
                    "unique_replay_event_count": len(replay_event_ids),
                    "unique_matched_rule_count": len(matched_rule_ids),
                    "matched_rule_ids_sha256": stable_hash(matched_rule_ids),
                    "replay_event_ids_sha256": stable_hash(replay_event_ids),
                    "follow_vs_avoid_role": _follow_vs_avoid_role(action_counts),
                    "action_class_counts": action_counts,
                    "main_system_surface_counts": _counter(members, "main_system_surface"),
                    "symbol_family_counts": _counter(members, "symbol_family"),
                    "source_symbol_counts": _counter(members, "source_symbol"),
                    "market_timeframe_counts": _counter(members, "market_timeframe"),
                    "route_session_counts": _counter(members, "route_session"),
                    "horizon_counts": _counter(members, "horizon_id"),
                    "side_counts": _counter(members, "side"),
                    "cost_adjusted_simulated_r": _numeric_summary(
                        row.get("matched_cost_adjusted_simulated_r") for row in members
                    ),
                    "gross_simulated_r": _numeric_summary(row.get("matched_gross_simulated_r") for row in members),
                    "stress_simulated_r": _numeric_summary(row.get("matched_stress_simulated_r") for row in members),
                    "effective_n": _numeric_summary(row.get("matched_effective_n") for row in members),
                    "source_evidence_role": RULE_REPLAY_SOURCE_EVIDENCE_ROLE,
                    "live_shadow_matching_role": LIVE_SHADOW_SECONDARY_ROLE,
                    "production_change_approved": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "research_boundary": research_boundary(),
                }
            )
    return rows


def summarize_rule_replay_execution_materialization(
    *,
    event_rows: list[dict[str, Any]],
    match_rows: list[dict[str, Any]],
    result_table_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    event_ids = {normalized(row.get("cp281_rule_replay_event_id")) for row in event_rows}
    matched_event_ids = {normalized(row.get("cp281_rule_replay_event_id")) for row in match_rows}
    duplicate_event_ids = {
        normalized(row.get("cp281_rule_replay_event_id"))
        for row in match_rows
        if bool(row.get("duplicate_rule_match"))
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_replay_event_rows": len(event_rows),
        "rule_replay_match_rows": len(match_rows),
        "rule_replay_result_table_rows": len(result_table_rows),
        "matched_event_rows": len(matched_event_ids),
        "unmatched_event_rows": len(event_ids - matched_event_ids),
        "own_rule_match_rows": sum(bool(row.get("own_rule_match")) for row in match_rows),
        "duplicate_rule_event_rows": len(duplicate_event_ids),
        "duplicate_rule_match_rows": sum(bool(row.get("duplicate_rule_match")) for row in match_rows),
        "action_conflict_match_rows": sum(bool(row.get("action_conflict_with_source_event")) for row in match_rows),
        "event_action_class_counts": _counter(event_rows, "source_action_class"),
        "matched_action_class_counts": _counter(match_rows, "matched_action_class"),
        "result_table_group_counts": _counter(result_table_rows, "result_table_group"),
        "event_symbol_family_counts": _counter(event_rows, "symbol_family"),
        "event_source_symbol_counts": _counter(event_rows, "source_symbol"),
        "event_market_timeframe_counts": _counter(event_rows, "market_timeframe"),
        "event_route_session_counts": _counter(event_rows, "route_session"),
        "event_horizon_counts": _counter(event_rows, "horizon_id"),
        "event_side_counts": _counter(event_rows, "side"),
        "matched_cost_adjusted_simulated_r": _numeric_summary(
            row.get("matched_cost_adjusted_simulated_r") for row in match_rows
        ),
        "matched_gross_simulated_r": _numeric_summary(row.get("matched_gross_simulated_r") for row in match_rows),
        "matched_stress_simulated_r": _numeric_summary(row.get("matched_stress_simulated_r") for row in match_rows),
        "matched_effective_n": _numeric_summary(row.get("matched_effective_n") for row in match_rows),
        "source_evidence_role": RULE_REPLAY_SOURCE_EVIDENCE_ROLE,
        "live_shadow_matching_role": LIVE_SHADOW_SECONDARY_ROLE,
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in event_rows + match_rows + result_table_rows
        ),
        "candidate_use_allowed_now_rows": sum(
            bool(row.get("candidate_use_allowed_now")) for row in event_rows + match_rows + result_table_rows
        ),
        "production_change_approved_rows": sum(
            bool(row.get("production_change_approved")) for row in event_rows + match_rows + result_table_rows
        ),
        "implementation_effect": {
            "main_side_cp281_rule_replay_events_materialized": True,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Execute these 461 CP281 ready runtime rules against the CP280/CP281 historical replay universe and "
            "promote the strongest follow/avoid result-table rows into callable default-off scorer/filter/router code."
        ),
    }


def aggregate_scope_key(row: dict[str, Any]) -> tuple[str, ...]:
    scope = row.get("aggregate_scope") if isinstance(row.get("aggregate_scope"), dict) else row
    return (
        normalized(scope.get("action_class") or row.get("action_class")),
        normalized(scope.get("symbol_family") or row.get("symbol_family")),
        normalized(scope.get("market_timeframe") or row.get("market_timeframe")),
        normalized(scope.get("route_session") or row.get("route_session")),
        normalized(scope.get("horizon_id") or row.get("horizon_id")),
        normalized(scope.get("side") or row.get("side")),
    )


def branch_decision_action(action_class: str, cost_summary: dict[str, Any], stress_summary: dict[str, Any]) -> str:
    cost_min = safe_float(cost_summary.get("min"))
    cost_max = safe_float(cost_summary.get("max"))
    stress_min = safe_float(stress_summary.get("min"))
    stress_max = safe_float(stress_summary.get("max"))
    if action_class == "follow_rule" and cost_min is not None and stress_min is not None:
        if cost_min > 0 and stress_min > 0:
            return "DEFAULT_OFF_CP281_BRANCH_FOLLOW_SCORER_READY"
        return "CP281_BRANCH_FOLLOW_SCORER_STRESS_OR_COST_REPAIR_REQUIRED"
    if action_class == "avoid_filter" and cost_max is not None and stress_max is not None:
        if cost_max < 0 and stress_max < 0:
            return "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY"
        return "CP281_BRANCH_AVOID_FILTER_SIGN_REPAIR_REQUIRED"
    return "CP281_BRANCH_DECISION_CLASSIFICATION_REPAIR_REQUIRED"


def build_branch_decision_rows(
    *,
    rule_mapping_rows: list[dict[str, Any]],
    aggregate_mapping_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rules_by_scope: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for rule in rule_mapping_rows:
        rules_by_scope.setdefault(aggregate_scope_key(rule), []).append(rule)

    rows: list[dict[str, Any]] = []
    for aggregate in aggregate_mapping_rows:
        key = aggregate_scope_key(aggregate)
        members = rules_by_scope.get(key, [])
        action_class = normalized(aggregate.get("action_class"))
        cost_summary = _numeric_summary(member.get("cost_adjusted_simulated_r") for member in members)
        stress_summary = _numeric_summary(member.get("stress_simulated_r") for member in members)
        effective_n_summary = _numeric_summary(member.get("effective_n") for member in members)
        decision_action = branch_decision_action(action_class, cost_summary, stress_summary)
        member_ids = [member.get("cp281_rule_row_id") for member in members]
        aggregate_scope = dict(aggregate.get("aggregate_scope") or {})
        source_contract_ready = all(bool(member.get("source_capture_contract_ready")) for member in members)
        self_check_pass = all(
            normalized(member.get("self_test_status")) == "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS"
            for member in members
        )
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_ready_runtime_branch_decision",
                "row_key": stable_hash(["cp281_branch_decision", aggregate.get("cp281_aggregate_row_id"), key]),
                "cp281_aggregate_row_id": aggregate.get("cp281_aggregate_row_id"),
                "action_class": action_class,
                "aggregate_scope": aggregate_scope,
                "main_system_surface": aggregate.get("main_system_surface"),
                "main_surface_action": aggregate.get("main_surface_action"),
                "main_surface_status": aggregate.get("main_surface_status"),
                "branch_decision_action": decision_action,
                "branch_decision_status": (
                    "READY_DEFAULT_OFF_CP281_BRANCH_DECISION"
                    if decision_action.startswith("DEFAULT_OFF_CP281_BRANCH_")
                    else "CP281_BRANCH_DECISION_REPAIR_REQUIRED"
                ),
                "member_rule_count": len(members),
                "aggregate_rule_count": aggregate.get("rule_count"),
                "member_rule_ids_sha256": stable_hash(member_ids),
                "member_rule_ids": member_ids,
                "source_capture_contract_ready": source_contract_ready,
                "self_test_pass": self_check_pass,
                "all_member_rows_preserved": len(members) == int(aggregate.get("rule_count") or 0),
                "cost_adjusted_simulated_r": cost_summary,
                "stress_simulated_r": stress_summary,
                "effective_n": effective_n_summary,
                "aggregate_average_cost_adjusted_simulated_r": aggregate.get("average_cost_adjusted_simulated_r"),
                "aggregate_average_stress_simulated_r": aggregate.get("average_stress_simulated_r"),
                "aggregate_effective_n_sum": aggregate.get("effective_n_sum"),
                "production_review_candidate": decision_action.startswith("DEFAULT_OFF_CP281_BRANCH_"),
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def summarize_branch_decisions(branch_decision_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready_rows = [
        row
        for row in branch_decision_rows
        if row.get("branch_decision_status") == "READY_DEFAULT_OFF_CP281_BRANCH_DECISION"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "branch_decision_rows": len(branch_decision_rows),
        "ready_branch_decision_rows": len(ready_rows),
        "repair_required_branch_decision_rows": len(branch_decision_rows) - len(ready_rows),
        "action_class_counts": _counter(branch_decision_rows, "action_class"),
        "branch_decision_action_counts": _counter(branch_decision_rows, "branch_decision_action"),
        "main_system_surface_counts": _counter(branch_decision_rows, "main_system_surface"),
        "member_rule_count": _numeric_summary(row.get("member_rule_count") for row in branch_decision_rows),
        "ready_follow_scope_rows": sum(
            row.get("branch_decision_action") == "DEFAULT_OFF_CP281_BRANCH_FOLLOW_SCORER_READY"
            for row in branch_decision_rows
        ),
        "ready_avoid_scope_rows": sum(
            row.get("branch_decision_action") == "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY"
            for row in branch_decision_rows
        ),
        "all_member_rows_preserved_rows": sum(bool(row.get("all_member_rows_preserved")) for row in branch_decision_rows),
        "source_capture_contract_ready_rows": sum(
            bool(row.get("source_capture_contract_ready")) for row in branch_decision_rows
        ),
        "self_test_pass_rows": sum(bool(row.get("self_test_pass")) for row in branch_decision_rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in branch_decision_rows
        ),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in branch_decision_rows),
        "implementation_effect": {
            "main_side_cp281_branch_decision_rows_materialized": True,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Join CP281 branch decisions to current replay or shadow events and decide which ready "
            "follow scopes and avoid scopes should advance to production-change review."
        ),
    }


BRANCH_EVENT_REQUIRED_FIELDS = ("symbol_family", "market_timeframe", "route_session", "horizon_id", "side")
CP281_PORTABLE_HORIZON_IDS = ("h4", "h16", "h32")
SYMBOL_FAMILY_BY_SYMBOL = {
    "GBPUSD": "GBPUSD_6B_FAMILY",
    "NAS100": "NAS100_NQ_FAMILY",
    "NDX100": "NAS100_NQ_FAMILY",
    "SPX500": "SPX500_ES_FAMILY",
    "US30": "US30_YM_FAMILY",
    "US30_CASH": "US30_YM_FAMILY",
    "USDJPY": "USDJPY_6J_FAMILY",
    "XAGUSD": "XAGUSD_SILVER_FAMILY",
}


def branch_decision_event_from_row(row: dict[str, Any]) -> dict[str, Any]:
    scope = row.get("aggregate_scope") or {}
    event = {field: scope.get(field) for field in BRANCH_EVENT_REQUIRED_FIELDS}
    if scope.get("side") is not None:
        event["selected_side"] = scope.get("side")
    if scope.get("market_timeframe") is not None:
        event["timeframe"] = scope.get("market_timeframe")
    if scope.get("route_session") is not None:
        event["session"] = scope.get("route_session")
    return event


def cp281_symbol_family_from_row(row: dict[str, Any]) -> str:
    explicit = normalized(row.get("symbol_family"))
    if explicit:
        return explicit
    for key in ("source_symbol", "symbol", "broker_symbol"):
        value = normalized(row.get(key)).upper()
        if value in SYMBOL_FAMILY_BY_SYMBOL:
            return SYMBOL_FAMILY_BY_SYMBOL[value]
    return ""


def cp281_branch_scope_events_from_source_row(
    row: dict[str, Any],
    *,
    default_market_timeframe: str = "M15",
    horizon_ids: tuple[str, ...] = CP281_PORTABLE_HORIZON_IDS,
) -> list[dict[str, Any]]:
    symbol_family = cp281_symbol_family_from_row(row)
    market_timeframe = _event_value(row, "market_timeframe") or default_market_timeframe
    route_session = _event_value(row, "route_session")
    side = _event_value(row, "side")
    missing_fields = [
        field
        for field, value in (
            ("symbol_family", symbol_family),
            ("market_timeframe", market_timeframe),
            ("route_session", route_session),
            ("side", side),
        )
        if not value
    ]
    if missing_fields:
        return []
    events: list[dict[str, Any]] = []
    for horizon_id in horizon_ids:
        events.append(
            {
                "symbol_family": symbol_family,
                "market_timeframe": market_timeframe,
                "route_session": route_session,
                "horizon_id": horizon_id,
                "side": side,
                "cp281_branch_scope_event_status": "CP281_BRANCH_SCOPE_EVENT_DERIVED_FROM_SOURCE_ROW",
                "cp281_branch_scope_derivation": {
                    "symbol_family_source": "explicit" if row.get("symbol_family") else "symbol_mapping",
                    "market_timeframe_source": "explicit_or_alias" if _event_value(row, "market_timeframe") else "default",
                    "default_market_timeframe": default_market_timeframe,
                    "horizon_id_source": "fanout",
                    "source_hash_required": False,
                },
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return events


def summarize_branch_scope_source_rows(
    source_rows: Iterable[dict[str, Any]],
    *,
    registry: "CP281BranchDecisionRegistry",
    default_market_timeframe: str = "M15",
) -> dict[str, Any]:
    source_row_count = 0
    event_rows = 0
    source_rows_with_events = 0
    matched_event_rows = 0
    registry_match_rows = 0
    action_class_counts = Counter()
    branch_decision_action_counts = Counter()
    for row in source_rows:
        source_row_count += 1
        events = cp281_branch_scope_events_from_source_row(row, default_market_timeframe=default_market_timeframe)
        if events:
            source_rows_with_events += 1
        for event in events:
            event_rows += 1
            matches = registry.evaluate_event(event)
            if matches:
                matched_event_rows += 1
            registry_match_rows += len(matches)
            action_class_counts.update(match.get("action_class") for match in matches)
            branch_decision_action_counts.update(match.get("branch_decision_action") for match in matches)
    return {
        "source_rows": source_row_count,
        "source_rows_with_cp281_branch_scope_events": source_rows_with_events,
        "derived_cp281_branch_scope_event_rows": event_rows,
        "registry_matched_event_rows": matched_event_rows,
        "registry_unmatched_event_rows": event_rows - matched_event_rows,
        "registry_match_rows": registry_match_rows,
        "registry_match_action_class_counts": dict(sorted((normalized(k), v) for k, v in action_class_counts.items())),
        "registry_match_branch_decision_action_counts": dict(
            sorted((normalized(k), v) for k, v in branch_decision_action_counts.items())
        ),
    }


def event_matches_branch_decision(event: dict[str, Any], row: dict[str, Any]) -> bool:
    scope = row.get("aggregate_scope") or {}
    for field in BRANCH_EVENT_REQUIRED_FIELDS:
        if _event_value(event, field) != normalized(scope.get(field)):
            return False
    return True


class CP281BranchDecisionRegistry:
    """Default-off evaluator over CP281 portable aggregate-scope decisions."""

    def __init__(self, branch_decisions: list[dict[str, Any]]) -> None:
        self.branch_decisions = list(branch_decisions)

    @classmethod
    def from_jsonl(cls, path: Path | str = DEFAULT_BRANCH_DECISION_LEDGER) -> "CP281BranchDecisionRegistry":
        return cls(read_jsonl(path))

    def evaluate_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for row in self.branch_decisions:
            if not event_matches_branch_decision(event, row):
                continue
            scope = row.get("aggregate_scope") or {}
            matches.append(
                {
                    "cp281_aggregate_row_id": row.get("cp281_aggregate_row_id"),
                    "action_class": row.get("action_class"),
                    "branch_decision_action": row.get("branch_decision_action"),
                    "branch_decision_status": row.get("branch_decision_status"),
                    "main_system_surface": row.get("main_system_surface"),
                    "symbol_family": scope.get("symbol_family"),
                    "market_timeframe": scope.get("market_timeframe"),
                    "route_session": scope.get("route_session"),
                    "horizon_id": scope.get("horizon_id"),
                    "side": scope.get("side"),
                    "member_rule_count": row.get("member_rule_count"),
                    "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": row.get("stress_simulated_r"),
                    "registry_evaluation_status": "DEFAULT_OFF_CP281_BRANCH_DECISION_MATCH",
                    "production_change_approved": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "research_boundary": research_boundary(),
                }
            )
        return matches

    def summarize_registry(self) -> dict[str, Any]:
        portable_scope_keys = [
            tuple(normalized((row.get("aggregate_scope") or {}).get(field)) for field in BRANCH_EVENT_REQUIRED_FIELDS)
            for row in self.branch_decisions
        ]
        duplicate_scope_counts = [count for count in Counter(portable_scope_keys).values() if count > 1]
        return {
            "branch_decision_rows": len(self.branch_decisions),
            "portable_scope_count": len(set(portable_scope_keys)),
            "duplicate_portable_scope_count": len(duplicate_scope_counts),
            "max_duplicate_portable_scope_size": max(duplicate_scope_counts) if duplicate_scope_counts else 1,
            "action_class_counts": dict(
                sorted(Counter(normalized(row.get("action_class")) for row in self.branch_decisions).items())
            ),
            "runtime_candidate_use_permitted_rows": sum(
                bool(row.get("runtime_candidate_use_permitted")) for row in self.branch_decisions
            ),
            "candidate_use_allowed_now_rows": sum(
                bool(row.get("candidate_use_allowed_now")) for row in self.branch_decisions
            ),
        }


def build_branch_scope_contract_rows(branch_decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in branch_decision_rows:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_branch_scope_event_contract",
                "row_key": stable_hash(["cp281_branch_scope_contract", row.get("cp281_aggregate_row_id")]),
                "cp281_aggregate_row_id": row.get("cp281_aggregate_row_id"),
                "action_class": row.get("action_class"),
                "branch_decision_action": row.get("branch_decision_action"),
                "event_required_fields": list(BRANCH_EVENT_REQUIRED_FIELDS),
                "event_required_field_count": len(BRANCH_EVENT_REQUIRED_FIELDS),
                "event_required_field_aliases": {
                    field: list(MATCH_FIELD_ALIASES.get(field, (field,))) for field in BRANCH_EVENT_REQUIRED_FIELDS
                },
                "source_hash_required_for_portable_branch_scope": False,
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_branch_scope_registry_self_check_rows(branch_decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    registry = CP281BranchDecisionRegistry(branch_decision_rows)
    rows: list[dict[str, Any]] = []
    for row in branch_decision_rows:
        event = branch_decision_event_from_row(row)
        matches = registry.evaluate_event(event)
        own_id = row.get("cp281_aggregate_row_id")
        matched_self = any(match.get("cp281_aggregate_row_id") == own_id for match in matches)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_branch_scope_registry_self_check",
                "row_key": stable_hash(["cp281_branch_scope_self_check", own_id]),
                "cp281_aggregate_row_id": own_id,
                "action_class": row.get("action_class"),
                "event_payload": event,
                "matched_self": matched_self,
                "matched_branch_decision_count": len(matches),
                "matched_aggregate_ids_sha256": stable_hash([match.get("cp281_aggregate_row_id") for match in matches]),
                "self_check_status": (
                    "CP281_BRANCH_SCOPE_REGISTRY_SELF_CHECK_PASS"
                    if matched_self
                    else "CP281_BRANCH_SCOPE_REGISTRY_SELF_CHECK_REPAIR_REQUIRED"
                ),
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def summarize_branch_scope_registry(
    *,
    branch_decision_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    self_check_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    registry = CP281BranchDecisionRegistry(branch_decision_rows)
    registry_summary = registry.summarize_registry()
    return {
        "schema_version": SCHEMA_VERSION,
        **registry_summary,
        "branch_scope_contract_rows": len(contract_rows),
        "branch_scope_self_check_rows": len(self_check_rows),
        "branch_scope_self_check_pass_rows": sum(
            row.get("self_check_status") == "CP281_BRANCH_SCOPE_REGISTRY_SELF_CHECK_PASS"
            for row in self_check_rows
        ),
        "event_required_fields": list(BRANCH_EVENT_REQUIRED_FIELDS),
        "source_hash_required_for_portable_branch_scope": False,
        "implementation_effect": {
            "main_side_cp281_portable_branch_scope_registry_materialized": True,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Add CP281 portable branch-scope fields to replay/shadow event producers, then evaluate "
            "current events through CP281BranchDecisionRegistry."
        ),
    }


def build_branch_scope_replay_event_rows(branch_decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(branch_decision_rows, start=1):
        event_payload = branch_decision_event_from_row(row)
        scope = row.get("aggregate_scope") or {}
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "cp281_branch_scope_replay_event",
                "row_key": stable_hash(["cp281_branch_scope_replay_event", row.get("cp281_aggregate_row_id")]),
                "cp281_branch_scope_replay_event_id": f"CP281-BRANCH-SCOPE-REPLAY-EVENT-{index:04d}",
                "source_cp281_aggregate_row_id": row.get("cp281_aggregate_row_id"),
                "source_branch_decision_row_key": row.get("row_key"),
                "source_branch_decision_action": row.get("branch_decision_action"),
                "source_branch_decision_status": row.get("branch_decision_status"),
                "source_action_class": row.get("action_class"),
                "symbol_family": scope.get("symbol_family"),
                "market_timeframe": scope.get("market_timeframe"),
                "route_session": scope.get("route_session"),
                "horizon_id": scope.get("horizon_id"),
                "side": scope.get("side"),
                "event_payload": event_payload,
                "event_required_fields": list(BRANCH_EVENT_REQUIRED_FIELDS),
                "event_required_field_count": len(BRANCH_EVENT_REQUIRED_FIELDS),
                "event_materialization_status": "CP281_BRANCH_SCOPE_EVENT_MATERIALIZED_FROM_BRANCH_DECISION",
                "source_operation": "SOURCE_ARTIFACT_BRANCH_SCOPE_REPLAY_EVENT_PRODUCTION",
                "member_rule_count": row.get("member_rule_count"),
                "aggregate_effective_n_sum": row.get("aggregate_effective_n_sum"),
                "aggregate_average_cost_adjusted_simulated_r": row.get("aggregate_average_cost_adjusted_simulated_r"),
                "aggregate_average_stress_simulated_r": row.get("aggregate_average_stress_simulated_r"),
                "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                "stress_simulated_r": row.get("stress_simulated_r"),
                "effective_n": row.get("effective_n"),
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def build_branch_scope_replay_match_rows(
    event_rows: list[dict[str, Any]],
    *,
    registry: CP281BranchDecisionRegistry,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event_row in event_rows:
        matches = registry.evaluate_event(event_row.get("event_payload") or event_row)
        duplicate_scope_match = len(matches) > 1
        for match_index, match in enumerate(matches, start=1):
            own_branch_match = match.get("cp281_aggregate_row_id") == event_row.get("source_cp281_aggregate_row_id")
            action_conflict = normalized(match.get("action_class")) != normalized(event_row.get("source_action_class"))
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "cp281_branch_scope_replay_match",
                    "row_key": stable_hash(
                        [
                            "cp281_branch_scope_replay_match",
                            event_row.get("cp281_branch_scope_replay_event_id"),
                            match.get("cp281_aggregate_row_id"),
                            match_index,
                        ]
                    ),
                    "cp281_branch_scope_replay_event_id": event_row.get("cp281_branch_scope_replay_event_id"),
                    "source_cp281_aggregate_row_id": event_row.get("source_cp281_aggregate_row_id"),
                    "matched_cp281_aggregate_row_id": match.get("cp281_aggregate_row_id"),
                    "match_index_for_event": match_index,
                    "matched_branch_decision_count_for_event": len(matches),
                    "own_branch_match": own_branch_match,
                    "duplicate_scope_match": duplicate_scope_match,
                    "action_conflict_with_source_event": action_conflict,
                    "source_action_class": event_row.get("source_action_class"),
                    "matched_action_class": match.get("action_class"),
                    "source_branch_decision_action": event_row.get("source_branch_decision_action"),
                    "matched_branch_decision_action": match.get("branch_decision_action"),
                    "matched_branch_decision_status": match.get("branch_decision_status"),
                    "main_system_surface": match.get("main_system_surface"),
                    "symbol_family": match.get("symbol_family"),
                    "market_timeframe": match.get("market_timeframe"),
                    "route_session": match.get("route_session"),
                    "horizon_id": match.get("horizon_id"),
                    "side": match.get("side"),
                    "member_rule_count": match.get("member_rule_count"),
                    "cost_adjusted_simulated_r": match.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": match.get("stress_simulated_r"),
                    "registry_evaluation_status": match.get("registry_evaluation_status"),
                    "production_change_approved": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "research_boundary": research_boundary(),
                }
            )
    return rows


def summarize_branch_scope_replay_materialization(
    *,
    event_rows: list[dict[str, Any]],
    match_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    event_ids = {normalized(row.get("cp281_branch_scope_replay_event_id")) for row in event_rows}
    matched_event_ids = {normalized(row.get("cp281_branch_scope_replay_event_id")) for row in match_rows}
    duplicate_event_ids = {
        normalized(row.get("cp281_branch_scope_replay_event_id"))
        for row in match_rows
        if bool(row.get("duplicate_scope_match"))
    }
    portable_scope_keys = [
        tuple(normalized(row.get(field)) for field in BRANCH_EVENT_REQUIRED_FIELDS) for row in event_rows
    ]
    duplicate_scope_counts = [count for count in Counter(portable_scope_keys).values() if count > 1]
    return {
        "schema_version": SCHEMA_VERSION,
        "branch_scope_replay_event_rows": len(event_rows),
        "branch_scope_replay_match_rows": len(match_rows),
        "matched_event_rows": len(matched_event_ids),
        "unmatched_event_rows": len(event_ids - matched_event_ids),
        "own_branch_match_rows": sum(bool(row.get("own_branch_match")) for row in match_rows),
        "duplicate_scope_event_rows": len(duplicate_event_ids),
        "duplicate_scope_match_rows": sum(bool(row.get("duplicate_scope_match")) for row in match_rows),
        "duplicate_portable_scope_count": len(duplicate_scope_counts),
        "max_duplicate_portable_scope_size": max(duplicate_scope_counts) if duplicate_scope_counts else 1,
        "action_conflict_match_rows": sum(bool(row.get("action_conflict_with_source_event")) for row in match_rows),
        "event_action_class_counts": _counter(event_rows, "source_action_class"),
        "matched_action_class_counts": _counter(match_rows, "matched_action_class"),
        "event_branch_decision_action_counts": _counter(event_rows, "source_branch_decision_action"),
        "matched_branch_decision_action_counts": _counter(match_rows, "matched_branch_decision_action"),
        "event_symbol_family_counts": _counter(event_rows, "symbol_family"),
        "event_market_timeframe_counts": _counter(event_rows, "market_timeframe"),
        "event_route_session_counts": _counter(event_rows, "route_session"),
        "event_horizon_counts": _counter(event_rows, "horizon_id"),
        "event_side_counts": _counter(event_rows, "side"),
        "implementation_effect": {
            "main_side_cp281_branch_scope_replay_events_materialized": True,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Feed concrete replay or shadow rows with these exact branch-scope fields into the portable "
            "CP281 registry, preserving duplicate-scope follow/avoid conflicts as explicit selector decisions."
        ),
    }


def summarize_mapping(
    *,
    rule_mapping_rows: list[dict[str, Any]],
    aggregate_mapping_rows: list[dict[str, Any]],
    source_capture_contract_rows: list[dict[str, Any]],
    registry_self_check_rows: list[dict[str, Any]],
    cp281_result_counts: dict[str, Any],
    moonshot_head: str,
    moonshot_status_clean: bool,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "rule_mapping_rows": len(rule_mapping_rows),
        "aggregate_mapping_rows": len(aggregate_mapping_rows),
        "source_capture_contract_rows": len(source_capture_contract_rows),
        "registry_self_check_rows": len(registry_self_check_rows),
        "action_class_counts": _counter(rule_mapping_rows, "action_class"),
        "main_system_surface_counts": _counter(rule_mapping_rows, "main_system_surface"),
        "symbol_family_counts": _counter(rule_mapping_rows, "symbol_family"),
        "market_timeframe_counts": _counter(rule_mapping_rows, "market_timeframe"),
        "route_session_counts": _counter(rule_mapping_rows, "route_session"),
        "horizon_counts": _counter(rule_mapping_rows, "horizon_id"),
        "side_counts": _counter(rule_mapping_rows, "side"),
        "simulated_r_sign_counts": _counter(rule_mapping_rows, "simulated_r_sign"),
        "cost_adjusted_simulated_r": _numeric_summary(row.get("cost_adjusted_simulated_r") for row in rule_mapping_rows),
        "stress_simulated_r": _numeric_summary(row.get("stress_simulated_r") for row in rule_mapping_rows),
        "effective_n": _numeric_summary(row.get("effective_n") for row in rule_mapping_rows),
        "source_capture_contract_ready_rows": sum(
            bool(row.get("source_capture_contract_ready")) for row in source_capture_contract_rows
        ),
        "registry_self_check_pass_rows": sum(
            row.get("self_check_status") == "CP281_READY_RUNTIME_REGISTRY_SELF_CHECK_PASS"
            for row in registry_self_check_rows
        ),
        "parked_rows": sum(bool((row.get("parked_state") or {}).get("is_parked")) for row in rule_mapping_rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool(row.get("runtime_candidate_use_permitted")) for row in rule_mapping_rows
        ),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rule_mapping_rows),
        "cp281_result_counts": cp281_result_counts,
        "represented_source_rows": cp281_result_counts.get("source_rows_represented"),
        "moonshot_snapshot": {
            "worktree_head": moonshot_head,
            "status_clean": moonshot_status_clean,
        },
        "implementation_effect": {
            "main_side_cp281_default_off_registry_materialized": True,
            "all_cp281_ready_runtime_rows_preserved": len(rule_mapping_rows) == cp281_result_counts.get("rule_rows"),
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "next_required_action": (
            "Use CP281 registry/contract rows to evaluate replay or shadow events, then decide which "
            "follow-rule and avoid-filter surfaces deserve production-change review."
        ),
    }
