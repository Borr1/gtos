"""vNext evidence-to-system translation helpers.

This module consumes the main-side moonshot/CP281/router integration ledgers and
normalizes them into default-off system-build rows. It does not enable runtime
behavior; it only creates traceable artifacts with source line, source hash, and
source-row hash anchors.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "gtos_vnext_evidence_system_v1"
SURFACE = "src/research_infra/gtos_vnext_evidence_system.py"
DATE = "2026-05-18"
MAIN_ORCH48_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DEFAULT_OUTPUT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)

FORBIDDEN_RUNTIME_TRUE_FIELDS = (
    "runtime_effect_now",
    "candidate_use_allowed_now",
    "runtime_candidate_use_permitted",
    "runtime_candidate_use_allowed",
    "runtime_score_allowed",
    "live_effect",
    "live_ai_runtime_change_now",
    "live_selector_change_now",
    "paid_api_or_vendor_call",
    "broker_operation",
)

ROW_ID_CANDIDATE_FIELDS = (
    "row_key",
    "candidate_row_id",
    "ai_narrowing_policy_row_id",
    "gate_surface_row_id",
    "scope_system_decision_row_id",
    "numeric_router_family_spec_id",
    "numeric_router_output_row_id",
    "cp281_aggregate_row_id",
    "source_repair_plan_row_id",
    "scorer_registry_surface_row_id",
    "avoid_comparator_score_row_id",
    "context_guard_input_row_id",
    "source_repair_proof_row_id",
    "source_row_id",
)


@dataclass(frozen=True)
class EvidenceSourceSpec:
    source_name: str
    evidence_family: str
    source_role: str
    path: Path
    system_surface: str
    implementation_action: str
    ledger_targets: tuple[str, ...]
    row_id_fields: tuple[str, ...] = ()


DEFAULT_SOURCE_SPECS: tuple[EvidenceSourceSpec, ...] = (
    EvidenceSourceSpec(
        source_name="cp281_rule_replay_result_table",
        evidence_family="cp281_native_rule_replay",
        source_role="historical_replay_result_table",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_RESULT_TABLE_LEDGER_2026-05-18.jsonl",
        system_surface="cp281_default_off_follow_avoid_registry_result_tables",
        implementation_action="PRESERVE_CP281_RULE_REPLAY_RESULT_TABLE_FOR_DEFAULT_OFF_SCORER_FILTER_TRANSLATION",
        ledger_targets=(
            "scorer_filter_router",
            "gate_filter_selector_risk_exit",
            "market_timeframe_expansion",
            "legacy_research_merger",
            "exact_proxy_r",
        ),
        row_id_fields=("row_key",),
    ),
    EvidenceSourceSpec(
        source_name="cp281_branch_decisions",
        evidence_family="cp281_ready_runtime_mapping",
        source_role="default_off_branch_decision",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_CP281_BRANCH_DECISIONS_LEDGER_2026-05-18.jsonl",
        system_surface="cp281_default_off_branch_scorer_filter_registry",
        implementation_action="REGISTER_DEFAULT_OFF_CP281_BRANCH_DECISION",
        ledger_targets=(
            "scorer_filter_router",
            "gate_filter_selector_risk_exit",
            "market_timeframe_expansion",
            "legacy_research_merger",
            "exact_proxy_r",
        ),
        row_id_fields=("row_key", "cp281_aggregate_row_id"),
    ),
    EvidenceSourceSpec(
        source_name="moonshot_reduced_surface_candidates",
        evidence_family="expanded_market_reduced_surface",
        source_role="branch_local_default_off_candidate",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_2026-05-18.jsonl",
        system_surface="default_off_expanded_market_side_filter_candidates",
        implementation_action="REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE",
        ledger_targets=(
            "scorer_filter_router",
            "market_timeframe_expansion",
            "legacy_research_merger",
            "exact_proxy_r",
        ),
        row_id_fields=("candidate_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="ai_narrowing_policy",
        evidence_family="ai_decision_architecture",
        source_role="mechanical_first_ai_narrowing_policy",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_AI_NARROWING_POLICY_LEDGER_2026-05-18.jsonl",
        system_surface="default_off_pre_ai_mechanical_selector_review",
        implementation_action="KEEP_AI_UNCHANGED_AND_STAGE_DEFAULT_OFF_MECHANICAL_SELECTOR_REVIEW",
        ledger_targets=("ai_decision_architecture", "scorer_filter_router", "legacy_research_merger"),
        row_id_fields=("ai_narrowing_policy_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="gate_evidence_surface_inventory",
        evidence_family="gate_filter_selector_evidence",
        source_role="gate_surface_capture_inventory",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_GATE_EVIDENCE_SURFACE_INVENTORY_LEDGER_2026-05-18.jsonl",
        system_surface="gate_filter_selector_risk_exit_evidence_inventory",
        implementation_action="PRESERVE_GATE_SURFACE_EVIDENCE_AND_CAPTURE_GAPS",
        ledger_targets=("gate_filter_selector_risk_exit", "runtime_architecture", "legacy_research_merger"),
        row_id_fields=("gate_surface_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_scope_decisions",
        evidence_family="numeric_router_system_recommendations",
        source_role="scope_system_decision",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SCOPE_DECISION_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_default_off_scope_decision_catalog",
        implementation_action="TRANSLATE_NUMERIC_ROUTER_SCOPE_DECISION_DEFAULT_OFF",
        ledger_targets=(
            "scorer_filter_router",
            "gate_filter_selector_risk_exit",
            "legacy_research_merger",
            "exact_proxy_r",
        ),
        row_id_fields=("scope_system_decision_row_id", "input_scope_router_decision_row_id"),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_family_action_specs",
        evidence_family="numeric_router_system_recommendations",
        source_role="family_action_spec",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_default_off_family_action_spec_catalog",
        implementation_action="TRANSLATE_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_DEFAULT_OFF",
        ledger_targets=(
            "scorer_filter_router",
            "gate_filter_selector_risk_exit",
            "legacy_research_merger",
            "exact_proxy_r",
        ),
        row_id_fields=("numeric_router_family_spec_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_scorer_surface",
        evidence_family="numeric_router_system_recommendations",
        source_role="scorer_registry_surface",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SCORER_SURFACE_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_default_off_scorer_registry_surface",
        implementation_action="REGISTER_DEFAULT_OFF_NUMERIC_ROUTER_SCORER_SURFACE",
        ledger_targets=("scorer_filter_router", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("numeric_router_output_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_avoid_score",
        evidence_family="numeric_router_system_recommendations",
        source_role="avoid_comparator_score",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_AVOID_SCORE_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_default_off_avoid_filter_score_surface",
        implementation_action="REGISTER_DEFAULT_OFF_NUMERIC_ROUTER_AVOID_FILTER_SCORE",
        ledger_targets=("scorer_filter_router", "gate_filter_selector_risk_exit", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("numeric_router_output_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_context_guard",
        evidence_family="numeric_router_system_recommendations",
        source_role="context_guard_input",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_default_off_context_stress_guard_input",
        implementation_action="MERGE_AS_DEFAULT_OFF_CONTEXT_STRESS_GUARD_INPUT",
        ledger_targets=("scorer_filter_router", "gate_filter_selector_risk_exit", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("numeric_router_output_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_source_repair_proof",
        evidence_family="numeric_router_source_repair",
        source_role="exact_r_source_repair_proof",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_exact_r_source_repair_proof_queue",
        implementation_action="PRESERVE_SOURCE_REPAIR_PROOF_FOR_EXACT_R_EXHAUSTION",
        ledger_targets=("runtime_architecture", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("numeric_router_output_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_source_repair_execution_plan",
        evidence_family="numeric_router_source_repair",
        source_role="source_repair_execution_plan",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_source_repair_execution_plan_queue",
        implementation_action="EXECUTE_OR_PRESERVE_SOURCE_REPAIR_PLAN_DEFAULT_OFF",
        ledger_targets=("runtime_architecture", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("source_repair_plan_row_id",),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_source_repair_selector_surface",
        evidence_family="numeric_router_source_repair",
        source_role="source_repair_selector_surface",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_source_repair_selector_surface",
        implementation_action="REGISTER_DEFAULT_OFF_SOURCE_REPAIR_SELECTOR_SURFACE",
        ledger_targets=("scorer_filter_router", "runtime_architecture", "legacy_research_merger", "exact_proxy_r"),
        row_id_fields=("source_repair_selector_surface_row_id", "numeric_router_output_row_id"),
    ),
    EvidenceSourceSpec(
        source_name="numeric_router_system_recommendation",
        evidence_family="numeric_router_system_recommendations",
        source_role="system_recommendation",
        path=MAIN_ORCH48_DIR / "MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_LEDGER_2026-05-18.jsonl",
        system_surface="numeric_router_system_recommendation_checkpoint",
        implementation_action="PRESERVE_NUMERIC_ROUTER_SYSTEM_RECOMMENDATION_AS_NON_TERMINAL_INPUT",
        ledger_targets=("runtime_architecture", "legacy_research_merger"),
        row_id_fields=("system_recommendation_row_id", "numeric_router_system_reco_row_id"),
    ),
)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(payload: Any, length: int = 64) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:length]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path, repo: Path | None = None) -> str:
    if repo is not None:
        try:
            return str(path.resolve().relative_to(repo.resolve())).replace("\\", "/")
        except ValueError:
            pass
    return str(path).replace("\\", "/")


def _payload_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("source_row")
    return payload if isinstance(payload, dict) else {}


def _dict_contexts(row: dict[str, Any]) -> list[dict[str, Any]]:
    payload = _payload_row(row)
    contexts: list[dict[str, Any]] = [row, payload]
    for key in ("result_table_dimensions", "aggregate_scope", "surface_scope", "safe_flags"):
        value = row.get(key)
        if isinstance(value, dict):
            contexts.append(value)
    for key in ("safe_flags", "surface_scope"):
        value = payload.get(key)
        if isinstance(value, dict):
            contexts.append(value)
    return contexts


def first_value(row: dict[str, Any], fields: Iterable[str]) -> Any:
    for field in fields:
        for context in _dict_contexts(row):
            if field in context and context.get(field) is not None:
                return context.get(field)
    return None


def first_text(row: dict[str, Any], fields: Iterable[str]) -> str:
    value = first_value(row, fields)
    return normalized(value)


def _row_id(spec: EvidenceSourceSpec, row: dict[str, Any], line_no: int) -> str:
    candidates = (*spec.row_id_fields, *ROW_ID_CANDIDATE_FIELDS)
    value = first_value(row, candidates)
    if value not in (None, ""):
        return normalized(value)
    return f"{spec.source_name}:line:{line_no}:{stable_hash(row, length=16)}"


def _truthy_flag(row: dict[str, Any], fields: Iterable[str]) -> bool:
    for field in fields:
        value = first_value(row, (field,))
        if value is True:
            return True
    boundary = row.get("research_boundary")
    if isinstance(boundary, dict):
        for field in fields:
            if boundary.get(field) is True:
                return True
    payload_boundary = _payload_row(row).get("research_boundary")
    if isinstance(payload_boundary, dict):
        for field in fields:
            if payload_boundary.get(field) is True:
                return True
    return False


def metric_stats(row: dict[str, Any], metric_name: str, scalar_fields: tuple[str, ...]) -> dict[str, Any]:
    raw = first_value(row, (metric_name,))
    if isinstance(raw, dict):
        return {
            "count": rounded(safe_float(raw.get("count"))),
            "sum": rounded(safe_float(raw.get("sum"))),
            "mean": rounded(safe_float(raw.get("mean"))),
            "min": rounded(safe_float(raw.get("min"))),
            "max": rounded(safe_float(raw.get("max"))),
            "source_field": metric_name,
            "source_shape": "summary_dict",
        }
    for field in scalar_fields:
        scalar = safe_float(first_value(row, (field,)))
        if scalar is not None:
            return {
                "count": 1,
                "sum": rounded(scalar),
                "mean": rounded(scalar),
                "min": rounded(scalar),
                "max": rounded(scalar),
                "source_field": field,
                "source_shape": "scalar",
            }
    return {
        "count": 0,
        "sum": None,
        "mean": None,
        "min": None,
        "max": None,
        "source_field": "",
        "source_shape": "missing",
    }


def extract_r_metrics(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "cost_adjusted_simulated_r": metric_stats(
            row,
            "cost_adjusted_simulated_r",
            (
                "target_selected_intrabar_cost_adjusted_simulated_r",
                "average_selected_intrabar_cost_adjusted_simulated_r",
                "aggregate_average_cost_adjusted_simulated_r",
                "selected_intrabar_cost_adjusted_simulated_r",
            ),
        ),
        "gross_simulated_r": metric_stats(
            row,
            "gross_simulated_r",
            ("aggregate_average_gross_simulated_r", "target_selected_intrabar_gross_simulated_r"),
        ),
        "stress_simulated_r": metric_stats(
            row,
            "stress_simulated_r",
            ("aggregate_average_stress_simulated_r", "target_selected_intrabar_stress_simulated_r"),
        ),
        "effective_n": metric_stats(row, "effective_n", ("target_effective_n", "aggregate_effective_n_sum")),
        "proxy_score": metric_stats(
            row,
            "proxy_score",
            ("registry_surface_score", "avoid_comparator_score", "score_mean"),
        ),
    }


def evidence_class(row: dict[str, Any], metrics: dict[str, dict[str, Any]]) -> str:
    if metrics["cost_adjusted_simulated_r"]["count"]:
        return "SIMULATED_REPLAY_R"
    if metrics["proxy_score"]["count"] or first_text(row, ("proxy_r_class",)):
        return "PROXY_R"
    if first_value(row, ("exact_missing_field_proof",)) or first_text(row, ("source_repair_system_decision",)):
        return "SOURCE_REPAIR_FOR_EXACT_R"
    if first_text(row, ("gate_surface", "decision_counts", "capture_status")):
        return "GATE_DECISION_EVIDENCE"
    return "SYSTEM_TRANSLATION_EVIDENCE"


def implementation_action(spec: EvidenceSourceSpec, row: dict[str, Any]) -> str:
    return first_text(
        row,
        (
            "main_surface_action",
            "main_compiler_action",
            "router_scope_decision",
            "numeric_router_action",
            "avoid_comparator_action",
            "context_guard_decision",
            "source_repair_system_decision",
            "source_repair_execution_status",
            "source_repair_selector_surface_status",
            "registry_surface_status",
            "ai_narrowing_policy_status",
            "recommended_next_action",
        ),
    ) or spec.implementation_action


def system_surface(spec: EvidenceSourceSpec, row: dict[str, Any]) -> str:
    value = first_text(
        row,
        (
            "main_system_surface",
            "implementation_target",
            "default_off_policy_surface",
            "output_family",
            "gate_surface",
            "expanded_market_reduced_surface_execution_surface",
        ),
    )
    return value or spec.system_surface


def build_matrix_row(
    *,
    spec: EvidenceSourceSpec,
    row: dict[str, Any],
    source_line_no: int,
    source_sha256: str,
    repo: Path | None = None,
) -> dict[str, Any]:
    metrics = extract_r_metrics(row)
    source_path = display_path(Path(spec.path), repo)
    row_id = _row_id(spec, row, source_line_no)
    boundary = row.get("research_boundary")
    if not isinstance(boundary, dict):
        boundary = _payload_row(row).get("research_boundary") if isinstance(_payload_row(row).get("research_boundary"), dict) else {}

    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_evidence_to_system_matrix_row",
        "vnext_matrix_row_id": f"GTOS-VNEXT-EVIDENCE-SYSTEM-{stable_hash([spec.source_name, source_line_no, row_id], length=24)}",
        "evidence_family": spec.evidence_family,
        "source_name": spec.source_name,
        "source_role": spec.source_role,
        "source_artifact": source_path,
        "source_artifact_sha256": source_sha256,
        "source_line_no": source_line_no,
        "source_row_id": row_id,
        "source_row_payload_sha256": stable_hash(row),
        "declared_origin_artifact": first_text(row, ("source_artifact", "execution_source_artifact", "surface_source_artifact")),
        "declared_origin_line_no": first_value(row, ("source_line_no", "execution_source_line_no", "surface_source_line_no")),
        "declared_origin_sha256": first_text(row, ("source_sha256", "execution_source_sha256", "surface_source_sha256")),
        "ledger_targets": list(spec.ledger_targets),
        "system_surface": system_surface(spec, row),
        "implementation_action": implementation_action(spec, row),
        "source_group": first_text(row, ("result_table_group", "output_family", "family_spec_type")),
        "source_dimension_key": first_text(row, ("result_table_dimension_key",)),
        "runtime_architecture_decision": "DEFAULT_OFF_RESEARCH_TO_RUNTIME_TRANSLATION_ONLY",
        "activation_state": first_text(row, ("activation_state",)) or "DEFAULT_OFF",
        "candidate_use_allowed_now": _truthy_flag(row, ("candidate_use_allowed_now",)),
        "runtime_candidate_use_permitted": _truthy_flag(row, ("runtime_candidate_use_permitted", "runtime_candidate_use_allowed")),
        "runtime_score_allowed": _truthy_flag(row, ("runtime_score_allowed",)),
        "runtime_effect_now": _truthy_flag(
            row,
            ("live_effect", "runtime_decision_effect", "live_ai_runtime_change_now", "live_selector_change_now"),
        ),
        "paid_api_or_vendor_call": _truthy_flag(row, ("paid_api_or_vendor_call",)),
        "broker_operation": _truthy_flag(row, ("broker_operation",)),
        "production_import_path": bool(boundary.get("production_import_path") is True),
        "mutates_order_risk_prompt_safety_or_mt5": bool(boundary.get("mutates_order_risk_prompt_safety_or_mt5") is True),
        "replay_r_reference_counted_as_new_main_result": _truthy_flag(row, ("replay_r_reference_counted_as_new_main_result",)),
        "r_evidence_class": evidence_class(row, metrics),
        "r_metrics": metrics,
        "symbol": first_text(row, ("symbol", "source_symbol")),
        "source_symbol": first_text(row, ("source_symbol", "symbol")),
        "symbol_family": first_text(row, ("symbol_family",)),
        "market_timeframe": first_text(row, ("market_timeframe", "timeframe")),
        "route_session": first_text(row, ("route_session", "session", "kill_zone")),
        "horizon_id": first_text(row, ("horizon_id",)),
        "side": first_text(row, ("side", "selected_side", "direction")),
        "source_component": first_text(row, ("source_component",)),
        "action_class": first_text(row, ("action_class", "matched_action_class", "main_compiler_action_class")),
        "proxy_r_class": first_text(row, ("proxy_r_class",)),
        "target_stop_order_class": first_text(row, ("target_stop_order_class",)),
        "source_boundary": boundary,
        "research_boundary_controls": {
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "runtime_effect_now": False,
        },
    }


def additive_metric_allowed(row: dict[str, Any]) -> bool:
    if row.get("source_name") == "cp281_rule_replay_result_table":
        return row.get("source_group") == "overall"
    return True


def source_inventory_row(repo: Path, spec: EvidenceSourceSpec, rows: list[dict[str, Any]], sha256: str) -> dict[str, Any]:
    path = repo / spec.path
    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_source_inventory_row",
        "source_name": spec.source_name,
        "evidence_family": spec.evidence_family,
        "source_role": spec.source_role,
        "source_artifact": display_path(path, repo),
        "source_artifact_sha256": sha256,
        "source_rows": len(rows),
        "source_lines": count_lines(path),
        "system_surface": spec.system_surface,
        "implementation_action": spec.implementation_action,
        "ledger_targets": list(spec.ledger_targets),
        "source_exists": path.exists(),
    }


def build_evidence_matrix(
    repo: Path,
    source_specs: Iterable[EvidenceSourceSpec] = DEFAULT_SOURCE_SPECS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matrix_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    for spec in source_specs:
        source_path = repo / spec.path
        rows = read_jsonl(source_path)
        source_sha = sha256_path(source_path)
        inventory_rows.append(source_inventory_row(repo, spec, rows, source_sha))
        for line_no, row in enumerate(rows, start=1):
            matrix_rows.append(
                build_matrix_row(
                    spec=spec,
                    row=row,
                    source_line_no=line_no,
                    source_sha256=source_sha,
                    repo=repo,
                )
            )
    return matrix_rows, inventory_rows


def build_runtime_architecture_ledger(
    matrix_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_source = {row["source_name"]: row for row in inventory_rows}
    output: list[dict[str, Any]] = []
    for source_name in sorted(rows_by_source):
        source_rows = [row for row in matrix_rows if row["source_name"] == source_name]
        surfaces = Counter(row["system_surface"] for row in source_rows)
        actions = Counter(row["implementation_action"] for row in source_rows)
        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "gtos_vnext_runtime_architecture_decision",
                "runtime_architecture_row_id": f"GTOS-VNEXT-RUNTIME-ARCH-{stable_hash(source_name, length=24)}",
                "source_name": source_name,
                "evidence_family": rows_by_source[source_name]["evidence_family"],
                "source_artifact": rows_by_source[source_name]["source_artifact"],
                "source_artifact_sha256": rows_by_source[source_name]["source_artifact_sha256"],
                "source_rows_preserved": len(source_rows),
                "source_rows_expected": rows_by_source[source_name]["source_rows"],
                "all_source_rows_preserved": len(source_rows) == rows_by_source[source_name]["source_rows"],
                "runtime_architecture_decision": "DEFAULT_OFF_LEDGERED_SYSTEM_SURFACE_NO_RUNTIME_ENABLEMENT",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "runtime_score_allowed": False,
                "runtime_effect_now": False,
                "paid_api_or_vendor_call": False,
                "broker_operation": False,
                "system_surface_counts": dict(sorted(surfaces.items())),
                "implementation_action_counts": dict(sorted(actions.items())),
            }
        )
    return output


def rows_for_target(matrix_rows: Iterable[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    return [row for row in matrix_rows if target in row.get("ledger_targets", [])]


def summarize_exact_proxy_expectancy(matrix_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = {}
    overall = {
        "source_rows": 0,
        "simulated_r_rows": 0,
        "proxy_r_rows": 0,
        "source_repair_rows": 0,
        "cost_adjusted_simulated_r_sum": 0.0,
        "stress_simulated_r_sum": 0.0,
        "proxy_score_sum": 0.0,
        "effective_n_sum": 0.0,
        "cost_adjusted_simulated_r_row_metric_sum": 0.0,
        "stress_simulated_r_row_metric_sum": 0.0,
        "effective_n_row_metric_sum": 0.0,
        "non_additive_metric_rows": 0,
    }

    def family_bucket(name: str) -> dict[str, Any]:
        if name not in families:
            families[name] = {
                "source_rows": 0,
                "r_evidence_class_counts": Counter(),
                "cost_adjusted_simulated_r_sum": 0.0,
                "stress_simulated_r_sum": 0.0,
                "proxy_score_sum": 0.0,
                "effective_n_sum": 0.0,
                "cost_adjusted_simulated_r_row_metric_sum": 0.0,
                "stress_simulated_r_row_metric_sum": 0.0,
                "effective_n_row_metric_sum": 0.0,
                "non_additive_metric_rows": 0,
            }
        return families[name]

    for row in matrix_rows:
        overall["source_rows"] += 1
        bucket = family_bucket(row["evidence_family"])
        bucket["source_rows"] += 1
        evidence = row.get("r_evidence_class") or "UNKNOWN"
        bucket["r_evidence_class_counts"][evidence] += 1
        if evidence == "SIMULATED_REPLAY_R":
            overall["simulated_r_rows"] += 1
        elif evidence == "PROXY_R":
            overall["proxy_r_rows"] += 1
        elif evidence == "SOURCE_REPAIR_FOR_EXACT_R":
            overall["source_repair_rows"] += 1

        metrics = row.get("r_metrics") or {}
        additive_allowed = additive_metric_allowed(row)
        if not additive_allowed:
            overall["non_additive_metric_rows"] += 1
            bucket["non_additive_metric_rows"] += 1

        for key, summary_key, row_trace_key in (
            ("cost_adjusted_simulated_r", "cost_adjusted_simulated_r_sum", "cost_adjusted_simulated_r_row_metric_sum"),
            ("stress_simulated_r", "stress_simulated_r_sum", "stress_simulated_r_row_metric_sum"),
            ("proxy_score", "proxy_score_sum", ""),
            ("effective_n", "effective_n_sum", "effective_n_row_metric_sum"),
        ):
            value = safe_float((metrics.get(key) or {}).get("sum"))
            if value is None:
                continue
            if row_trace_key:
                overall[row_trace_key] += value
                bucket[row_trace_key] += value
            if key == "proxy_score" or additive_allowed:
                overall[summary_key] += value
                bucket[summary_key] += value

    family_rows = []
    for name, payload in sorted(families.items()):
        row = dict(payload)
        row["evidence_family"] = name
        row["r_evidence_class_counts"] = dict(sorted(payload["r_evidence_class_counts"].items()))
        for field in (
            "cost_adjusted_simulated_r_sum",
            "stress_simulated_r_sum",
            "proxy_score_sum",
            "effective_n_sum",
            "cost_adjusted_simulated_r_row_metric_sum",
            "stress_simulated_r_row_metric_sum",
            "effective_n_row_metric_sum",
        ):
            row[field] = rounded(row[field])
        family_rows.append(row)

    for field in (
        "cost_adjusted_simulated_r_sum",
        "stress_simulated_r_sum",
        "proxy_score_sum",
        "effective_n_sum",
        "cost_adjusted_simulated_r_row_metric_sum",
        "stress_simulated_r_row_metric_sum",
        "effective_n_row_metric_sum",
    ):
        overall[field] = rounded(overall[field])

    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_exact_proxy_r_expectancy_summary",
        "overall": overall,
        "by_evidence_family": family_rows,
        "additivity_policy": (
            "cost/stress/effective-N sums use additive rows only where grouped result-table rows would otherwise "
            "double-count overlapping views; *_row_metric_sum fields preserve the raw row-level trace totals."
        ),
        "exact_r_policy": (
            "Exact broker/account R is not treated as a blocker; source-repair rows are preserved "
            "where exact fields are missing, while simulated replay R and proxy R remain primary."
        ),
    }


def build_instruction_coverage_rows(matrix_rows: list[dict[str, Any]], inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_source_rows = sum(row["source_rows"] for row in inventory_rows)
    matrix_count = len(matrix_rows)
    checks = [
        (
            "run_on_main_no_branch_worktree",
            "COVERED_BY_BUILDER_CONTEXT",
            "Builder is main-repo route; manifest records git head/status separately.",
        ),
        (
            "preserve_all_material_rows_no_top_n",
            "PASS" if matrix_count == total_source_rows else "FAIL",
            f"matrix_rows={matrix_count}; source_rows={total_source_rows}",
        ),
        (
            "default_off_no_runtime_enablement",
            "PASS" if not find_safety_issues(matrix_rows) else "FAIL",
            "All matrix rows must keep runtime/candidate/broker/API flags false.",
        ),
        (
            "primary_truth_replay_proxy_expectancy",
            "COVERED_BY_GTOS_VNEXT_EXACT_PROXY_R_EXPECTANCY_SUMMARY",
            "R/proxy/effective-N fields are materialized from source rows when present.",
        ),
        (
            "do_not_chase_broker_account_realized_r",
            "PASS",
            "Exact-R source-repair rows are preserved as source-completeness work, not blockers.",
        ),
        (
            "no_live_runtime_watchdog_restart_or_broker_operation",
            "PASS",
            "This module only writes research artifacts.",
        ),
        (
            "completion_not_final_before_72h",
            "INCOMPLETE_BY_DESIGN",
            "Checkpoint artifact; final completion audit remains open.",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for index, (instruction, status, evidence) in enumerate(checks, start=1):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_type": "gtos_vnext_instruction_coverage_row",
                "instruction_coverage_row_id": f"GTOS-VNEXT-INSTRUCTION-COVERAGE-{index:04d}",
                "instruction": instruction,
                "coverage_status": status,
                "evidence": evidence,
                "candidate_use_allowed_now": False,
                "runtime_effect_now": False,
                "paid_api_or_vendor_call": False,
                "broker_operation": False,
            }
        )
    return rows


def find_safety_issues(rows: Iterable[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        row_id = row.get("vnext_matrix_row_id") or row.get("runtime_architecture_row_id") or row.get("instruction_coverage_row_id")
        for field in FORBIDDEN_RUNTIME_TRUE_FIELDS:
            if row.get(field) is True:
                issues.append(f"forbidden_true_field:{row_id}:{field}")
    return issues


def summarize_matrix(matrix_rows: list[dict[str, Any]], inventory_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts = Counter(row["source_name"] for row in matrix_rows)
    target_counts: Counter[str] = Counter()
    for row in matrix_rows:
        target_counts.update(row.get("ledger_targets", []))
    return {
        "schema_version": SCHEMA_VERSION,
        "source_files": len(inventory_rows),
        "source_rows_expected": sum(row["source_rows"] for row in inventory_rows),
        "matrix_rows": len(matrix_rows),
        "all_source_rows_preserved": len(matrix_rows) == sum(row["source_rows"] for row in inventory_rows),
        "source_row_counts": dict(sorted(source_counts.items())),
        "ledger_target_counts": dict(sorted(target_counts.items())),
        "evidence_family_counts": dict(sorted(Counter(row["evidence_family"] for row in matrix_rows).items())),
        "r_evidence_class_counts": dict(sorted(Counter(row["r_evidence_class"] for row in matrix_rows).items())),
        "safety_issue_count": len(find_safety_issues(matrix_rows)),
    }
