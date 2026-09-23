#!/usr/bin/env python3
"""Materialize V3, validation, AI, and dual-broker Wave2 dispositions."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

WAVE1B_DIR = REPO_ROOT / "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04"
WAVE1C_DIR = REPO_ROOT / "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04"

AI_LOG_PATHS = {
    "ai_call_policy_decisions": REPO_ROOT / "shadow_logs/ai_call_policy_decisions.jsonl",
    "ai_decision_trace": REPO_ROOT / "shadow_logs/ai_decision_trace.jsonl",
    "ai_supervisor_decisions": REPO_ROOT / "shadow_logs/ai_supervisor_decisions.jsonl",
    "ai_narrowing_policy_shadow_evaluations": REPO_ROOT / "shadow_logs/ai_narrowing_policy_shadow_evaluations.jsonl",
    "malformed_responses": REPO_ROOT / "shadow_logs/malformed_responses.jsonl",
}


def route_path(name: str) -> Path:
    return ROUTE_DIR / name


def route_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix != ".jsonl":
        return None
    return sum(1 for line in path.open(encoding="utf-8-sig", errors="replace") if line.strip())


def append_unique_by_key(rows: list[dict[str, Any]], new_rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen = {row.get(key) for row in new_rows}
    return [row for row in rows if row.get(key) not in seen] + new_rows


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.open(encoding="utf-8-sig", errors="replace") if line.strip())


def build_v3_disposition_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    wave1b_rows = read_jsonl(WAVE1B_DIR / "V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl")
    live_matrix_rows = read_jsonl(WAVE1B_DIR / "LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl")
    label_by_component = {
        "selector_v3": "staged_default_off",
        "scheduler_v3": "research_only",
        "execution_policy_v3": "staged_default_off",
        "same_symbol_lifecycle_logic": "research_only",
        "cost_swap_slippage_handling": "research_only",
        "exposure_and_correlation_controls": "research_only",
        "halt_semantics_runtime_control": "research_only",
        "live_decision_packet_completeness": "research_only",
        "market_whiteboard_state_inputs": "research_only",
        "broker_profile_spec_session_authority": "staged_default_off",
        "replay_and_capture_contracts": "staged_default_off",
    }
    v4_action_by_component = {
        "selector_v3": "mine selector package rules into Selector V4 but require broker-net admission and final-say packet authority",
        "scheduler_v3": "replace with Scheduler V4 best-trade allocator because halt-time money-risk authority was missing",
        "execution_policy_v3": "stage for ticket-bound replay only; current halt-time live policy was momentum/partial runner evidence",
        "same_symbol_lifecycle_logic": "move into Same-Symbol Lifecycle V4 with ticket-bound scale/reverse/close rules",
        "cost_swap_slippage_handling": "move into Cost/Swap/Slippage Engine V4 with broker-local pretrade packet fields",
        "exposure_and_correlation_controls": "move into Scheduler V4 portfolio/cluster exposure gates",
        "halt_semantics_runtime_control": "move into Runtime Control V4 atomic halt and process-stop contract",
        "live_decision_packet_completeness": "move into LiveDecisionPacketV4 capture schema and verifier",
        "market_whiteboard_state_inputs": "move into Market Whiteboard V2 source completeness and bad-market separator",
        "broker_profile_spec_session_authority": "stage broker profile/spec/session fields as broker-local inputs only",
        "replay_and_capture_contracts": "stage as replay/digital-twin source contracts; not production readiness",
    }
    rows: list[dict[str, Any]] = []
    for source in wave1b_rows:
        component_id = source.get("component_id")
        disposition = label_by_component.get(str(component_id), "research_only")
        rows.append(
            {
                "row_id": f"v3_to_v4:{component_id}",
                "component_id": component_id,
                "component_family": source.get("component_family"),
                "production_code_disposition": disposition,
                "runtime_disposition_from_wave1b": source.get("runtime_disposition"),
                "live_authority_classification": source.get("live_authority_classification"),
                "halt_time_authority_result": "not_full_live_authority" if component_id in {"selector_v3", "scheduler_v3", "execution_policy_v3"} else source.get("live_authority_classification"),
                "config_flag_state": {
                    "selector_v3_enabled": False,
                    "selector_v3_apply_to_execution": False,
                    "scheduler_v3_enabled": False,
                    "scheduler_v3_apply_to_execution": False,
                    "execution_policy_v3_enabled": False,
                    "execution_policy_v3_apply_to_execution": False,
                }
                if component_id in {"selector_v3", "scheduler_v3", "execution_policy_v3"}
                else {},
                "v4_action": v4_action_by_component.get(str(component_id), source.get("implementation_decision")),
                "source_paths": source.get("source_paths") or [],
                "source_capture_state": source.get("source_capture_state"),
                "source_completeness_state": source.get("source_completeness_state"),
                "evidence_class": source.get("evidence_class"),
                "result_use_status": "v3_disposition_for_v4_design_not_live_activation_authority",
                "same_evidence_class_repairs_attempted": [
                    "wave1b_v3_runtime_disposition_consumed",
                    "config_default_off_flags_checked",
                    "live_authority_matrix_counts_preserved",
                ],
                "status": "v3_component_disposition_labeled_for_v4",
            }
        )
    rows.append(
        {
            "row_id": "v3_to_v4:hard_halt_flags_autostart_disabled",
            "component_id": "hard_halt_flags_autostart_disabled",
            "component_family": "runtime_control",
            "production_code_disposition": "active",
            "runtime_disposition_from_wave1b": "halt_flags_present",
            "live_authority_classification": "halt_control_guard_active_after_hard_halt",
            "halt_time_authority_result": "active_hard_halt_guard_not_live_restart_permission",
            "config_flag_state": {},
            "v4_action": "preserve hard-halt/autostart-disabled guard and implement atomic Runtime Control V4 before any production return",
            "source_paths": [
                "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag",
                "pipeline_state/RESEARCH_RUNTIME_HALT.flag",
                "knowledge_base/meta/AUTOSTART_DISABLED.flag",
            ],
            "source_capture_state": "halt_flags_present",
            "source_completeness_state": "active_guard_files_present",
            "evidence_class": "production_runtime_halt_guard",
            "result_use_status": "active_halt_guard_not_live_deploy_authorization",
            "same_evidence_class_repairs_attempted": ["halt_flag_presence_preserved"],
            "status": "active_hard_halt_guard_preserved",
        }
    )
    rows.append(
        {
            "row_id": "v3_to_v4:full_v3_live_authority_claim",
            "component_id": "full_v3_live_authority_claim",
            "component_family": "authority_claim",
            "production_code_disposition": "rejected",
            "runtime_disposition_from_wave1b": "not_supported_by_live_authority_matrix",
            "live_authority_classification": "claim_rejected",
            "halt_time_authority_result": "rejected_full_v3_was_not_halt_time_live_authority",
            "config_flag_state": {
                "selector_v3_enabled": False,
                "scheduler_v3_enabled": False,
                "execution_policy_v3_enabled": False,
            },
            "v4_action": "do not blame or promote full V3 as live authority; mine useful packages and rebuild V4 with broker-real contracts",
            "source_paths": [
                "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl",
                "config/agent_config.yaml",
                "tests/test_moonshot_v3_runtime_packages.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
            ],
            "source_capture_state": "wave1b_live_authority_matrix_and_config_flags",
            "source_completeness_state": "sufficient_to_reject_full_v3_live_authority_claim",
            "evidence_class": "config_and_live_authority_matrix_disposition",
            "result_use_status": "rejection_of_authority_claim_not_component_deletion",
            "same_evidence_class_repairs_attempted": ["wave1b_matrix_consumed", "config_default_off_flags_checked"],
            "status": "rejected_claim_not_v3_component_failure",
        }
    )
    summary = {
        "generated_at_utc": GENERATED_AT,
        "v3_disposition_rows": len(rows),
        "production_code_disposition_counts": dict(Counter(row.get("production_code_disposition") for row in rows)),
        "live_authority_matrix_rows": len(live_matrix_rows),
        "live_authority_classification_counts": dict(Counter(row.get("live_authority_classification") for row in live_matrix_rows)),
        "v3_selector_status_counts": dict(Counter(row.get("v3_selector_status") for row in live_matrix_rows)),
        "v3_scheduler_status_counts": dict(Counter(row.get("v3_scheduler_status") for row in live_matrix_rows)),
        "v3_execution_status_counts": dict(Counter(row.get("v3_execution_status") for row in live_matrix_rows)),
    }
    return rows, summary


def build_dual_broker_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    source_rows = read_jsonl(WAVE1C_DIR / "redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl")
    for source in source_rows:
        namespace = source.get("broker_namespace")
        component = source.get("component")
        disposition = "staged_default_off"
        if source.get("authority") in {"broker_neutral_intent_bus", "target_lifecycle_state", "supervisor", "read_only_maintenance"}:
            disposition = "active"
        if source.get("authority") == "projector_bridge":
            disposition = "research_only"
        rows.append(
            {
                "row_id": f"dual_broker_disposition:{component}",
                "broker_namespace": namespace,
                "component": component,
                "authority": source.get("authority"),
                "runtime_disposition": source.get("runtime_disposition"),
                "production_code_disposition": disposition,
                "dual_broker_constraint": "redacted_account may be source-brain primary; FTMO is follower/projector broker-local truth only",
                "ftmo_no_copy_rule": True,
                "no_copy_forbidden_fields": [
                    "redacted_account_lot_size",
                    "redacted_account_fill_price",
                    "redacted_account_cash_pnl",
                    "redacted_account_commission_swap_fee",
                    "redacted_account_symbol_spec_session",
                    "redacted_account_order_deal_position_lifecycle_truth",
                ],
                "required_ftmo_local_truth": [
                    "FTMO_symbol_spec",
                    "FTMO_session_hours",
                    "FTMO_spread_commission_swap",
                    "FTMO_lot_margin_cash_risk",
                    "FTMO_order_deal_position_account_history",
                    "FTMO_profile_namespace",
                ],
                "v4_action": source.get("implementation_decision"),
                "source_paths": [
                    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl",
                    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/COST_SWAP_SLIPPAGE_SPEC_SESSION_LEDGER.jsonl",
                    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/FOLLOWER_PROJECTOR_LIFECYCLE_LEDGER.jsonl",
                ],
                "evidence_class": source.get("evidence_class"),
                "result_use_status": "dual_broker_architecture_contract_not_target_broker_account_truth",
                "status": "dual_broker_no_copy_constraint_labeled_for_v4",
            }
        )
    summary = {
        "generated_at_utc": GENERATED_AT,
        "dual_broker_rows": len(rows),
        "ftmo_no_copy_rows": sum(row.get("ftmo_no_copy_rule") is True for row in rows),
        "production_code_disposition_counts": dict(Counter(row.get("production_code_disposition") for row in rows)),
        "broker_namespace_counts": dict(Counter(row.get("broker_namespace") for row in rows)),
    }
    return rows, summary


def update_contracts(v3_summary: dict[str, Any], dual_summary: dict[str, Any]) -> dict[str, Any]:
    ai_counts = {name: line_count(path) for name, path in AI_LOG_PATHS.items()}
    ai_contract = read_json(route_path("WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json"))
    ai_contract.update(
        {
            "generated_at_utc": GENERATED_AT,
            "status": "contract_materialized_no_paid_replay_guard_required_for_v4",
            "role": "measured_validator_after_no_api_replay_not_unguarded_main_actor",
            "runtime_log_counts": ai_counts,
            "guard_source_paths": [
                "config/agent_config.yaml",
                "src/components/ai_call_policy.py",
                "src/components/ai_supervisor.py",
                "tests/test_ai_call_policy.py",
                "tests/test_ai_narrowing_policy_shadow_evaluations.py",
            ],
            "hard_rules": [
                "no paid broad historical replay through AI",
                "historical/mechanical market replay must be no-API first",
                "research AI requires manifest, budget, owner approval, and cache",
                "AI supervisor may guard schema/health and disable narrowing but must not create trade authority",
                "AI narrowing remains shadow/default-off until validated against deterministic baselines",
            ],
            "result_use_status": "ai_contract_for_v4_design_not_live_ai_activation",
        }
    )
    write_json(route_path("WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json"), ai_contract)

    validation = read_json(route_path("WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json"))
    validation.update(
        {
            "generated_at_utc": GENERATED_AT,
            "status": "contract_materialized_execution_pending",
            "materialized_evidence_class_map": {
                "tick_repaired_first_passage_rows": 55,
                "full_tick_window_rows": 49,
                "partial_or_missing_tick_rows": 6,
                "allocator_replay_rows": 96,
                "zero_trade_rank_rows": 416,
                "final_say_authority_rows": 12775,
                "market_system_classification_rows": 77,
                "cost_source_coverage_rows": 77,
                "pending_nofill_lifecycle_rows": 877,
            },
            "required_execution_lanes": [
                "sealed row-id partition ledger",
                "purged walk-forward splits",
                "symbol/session/side/regime holdouts",
                "cost/swap/slippage stress",
                "GER30 largest-winner sensitivity",
                "deterministic digital-twin replay before any AI audit",
            ],
            "result_use_status": "validation_contract_not_validation_result",
        }
    )
    write_json(route_path("WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json"), validation)

    replay = read_json(route_path("WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json"))
    replay.update(
        {
            "generated_at_utc": GENERATED_AT,
            "status": "plan_materialized_execution_pending_wave3",
            "materialized_source_counts": validation["materialized_evidence_class_map"],
            "result_use_status": "replay_plan_not_executed_validation_result",
        }
    )
    write_json(route_path("WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json"), replay)

    return {
        "ai_log_counts": ai_counts,
        "validation_status": validation["status"],
        "ai_status": ai_contract["status"],
        "v3_summary": v3_summary,
        "dual_broker_summary": dual_summary,
    }


def update_capture_replay_ai_ledger(contract_summary: dict[str, Any]) -> None:
    rows = [
        {
            "ledger_id": "live_decision_packet_v4_gap",
            "surface": "capture_contract",
            "status": "capture_schema_contract_materialized_implementation_pending",
            "finding": "LiveDecisionPacketV4 field groups are specified, but runtime packet implementation and prospective capture remain Wave3 work.",
            "source_paths": [
                "WAVE2_CAPTURE_FIELD_CONTRACT_LIVEDECISIONPACKETV4.json",
                "WAVE2_LIVE_DECISION_PACKET_V4_CAPTURE_CONTRACT.json",
            ],
            "non_generatable_historical_truth": [
                "unlogged original final-say intent",
                "missing SLTP modify lifecycle",
                "uncaptured AI prompt/input/output/gate state",
                "original runtime allocator packet truth",
            ],
            "v4_requirement": "LiveDecisionPacketV4_required_before_production_return",
            "result_use_status": "capture_contract_not_runtime_packet_implementation",
        },
        {
            "ledger_id": "replay_validation_contract_gap",
            "surface": "validation_replay",
            "status": "validation_contract_materialized_execution_pending",
            "finding": "No-API deterministic replay, sealed partitions, cost stress, and digital-twin execution are specified but not executed in this Wave2 checkpoint.",
            "source_paths": [
                "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
                "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json",
            ],
            "materialized_source_counts": contract_summary.get("validation_status"),
            "v4_requirement": "historical_replay_digital_twin_and_anti_overfit_contract",
            "result_use_status": "validation_contract_not_validation_result",
        },
        {
            "ledger_id": "ai_role_after_hard_halt",
            "surface": "ai_reliability",
            "status": "ai_reliability_contract_materialized_no_paid_replay_guard",
            "finding": "AI is constrained to measured validator/audit role after deterministic replay; current logs show zero AI call-policy decisions, zero AI decision traces, zero AI supervisor decisions, 5671 narrowing shadow rows, and 38 malformed responses.",
            "source_paths": [
                "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json",
                "config/agent_config.yaml",
                "tests/test_ai_call_policy.py",
            ],
            "runtime_log_counts": contract_summary.get("ai_log_counts"),
            "v4_requirement": "cached_budgeted_stratified_ai_audit_only_until_value_proven",
            "result_use_status": "ai_contract_not_live_ai_activation",
        },
        {
            "ledger_id": "production_return_not_ready",
            "surface": "production_disposition",
            "status": "blocked_until_wave2_completion_and_v4_package_proven",
            "finding": "Production return remains blocked by V4 implementation, capture, validation, dual-broker broker-local constraints, and production-return dossier.",
            "source_paths": [
                "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
                "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl",
                "WAVE2_FINAL_MASTER_STATE_TABLE.json",
            ],
            "v4_requirement": "production_return_dossier_required",
            "result_use_status": "production_return_blocker_not_deploy_authorization",
        },
    ]
    write_jsonl(route_path("WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl"), rows)


def update_production_component_ledger() -> None:
    rows = read_jsonl(route_path("WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl"))
    label_map = {
        "primary_analyzer_prompt_raw_geometry": "research_only",
        "moonshot_dynamic_execution_router": "staged_default_off",
        "execution_manager_dynamic_exit": "research_only",
        "orchestrator_candidate_packet_v1": "research_only",
        "selector_scheduler_v3_packages": "staged_default_off",
        "broker_profiles_and_dual_broker_follower": "staged_default_off",
    }
    for row in rows:
        row["production_code_disposition"] = label_map.get(str(row.get("component")), "research_only")
        row["result_use_status"] = "production_component_disposition_for_v4_design_not_live_activation"
    write_jsonl(route_path("WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl"), rows)


def update_question_ledgers(summary: dict[str, Any]) -> None:
    updates = {
        "W2Q_DUAL_BROKER_CONSTRAINTS": {
            "status": "answered_with_dual_broker_broker_local_no_copy_contract",
            "coverage_status": "saturated_for_current_source_class_dual_broker_contract_materialized",
            "remaining_work": "Wave3 must implement/verifier-check broker-local FTMO profile/spec/risk/account-history truth before target trading.",
            "artifacts": ["WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl"],
            "repairs": ["wave1c_authority_matrix_flattened", "ftmo_no_copy_rule_materialized"],
        },
        "W2Q_FTMO_NO_COPY_RULE": {
            "status": "answered_with_ftmo_no_copy_broker_local_truth_contract",
            "coverage_status": "saturated_for_current_source_class_ftmo_no_copy_contract_materialized",
            "remaining_work": "Wave3 must enforce no-copy tests and broker-local risk/cost/session/account-history fields.",
            "artifacts": ["WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl"],
            "repairs": ["ftmo_no_copy_rule_materialized"],
        },
        "W2Q_VALIDATION_REPLAY": {
            "status": "answered_with_validation_replay_contract_materialized_execution_pending",
            "coverage_status": "saturated_for_current_source_class_validation_contract_materialized_execution_pending",
            "remaining_work": "Wave3 digital twin must execute sealed partitions and replay; Wave2 contract is not a validation result.",
            "artifacts": ["WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json", "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json"],
            "repairs": ["validation_evidence_class_map_materialized", "no_api_digital_twin_plan_materialized"],
        },
        "W2Q_AI_RELIABILITY": {
            "status": "answered_with_ai_reliability_no_paid_replay_contract_materialized",
            "coverage_status": "saturated_for_current_source_class_ai_contract_materialized_execution_pending",
            "remaining_work": "Wave3 must implement/cache/calibrate AI audit only after deterministic replay baselines.",
            "artifacts": ["WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json"],
            "repairs": ["ai_runtime_log_counts_materialized", "ai_call_policy_guard_contract_materialized"],
        },
        "W2Q_V3_DEFAULT_OFF_LIVE_DIVERGENCE": {
            "status": "answered_with_v3_to_v4_disposition_labels_and_full_v3_live_authority_claim_rejected",
            "coverage_status": "saturated_for_current_source_class_v3_disposition_materialized",
            "remaining_work": "Wave3 must implement V4 packages; V3 full-live-authority claim stays rejected and useful V3 pieces remain staged/research-only.",
            "artifacts": ["WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl"],
            "repairs": ["v3_disposition_labels_materialized", "full_v3_live_authority_claim_rejected"],
        },
    }
    for name in [
        "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
        "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
        "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl",
    ]:
        rows = read_jsonl(route_path(name))
        for row in rows:
            update = updates.get(row.get("question_id"))
            if not update:
                continue
            row["status"] = update["status"]
            row["pursuit_actions"] = list(
                dict.fromkeys(list(row.get("pursuit_actions") or []) + ["wave2_v3_validation_ai_dual_broker_disposition_pass"])
            )
            row["same_evidence_class_repairs_attempted"] = list(
                dict.fromkeys(list(row.get("same_evidence_class_repairs_attempted") or []) + update["repairs"])
            )
            existing = [item for item in str(row.get("result_artifact") or "").split(";") if item]
            row["result_artifact"] = ";".join(list(dict.fromkeys(existing + update["artifacts"])))
            row["v3_disposition_rows"] = summary["v3_summary"].get("v3_disposition_rows")
            row["dual_broker_rows"] = summary["dual_broker_summary"].get("dual_broker_rows")
            if name == "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl":
                row["coverage_status"] = update["coverage_status"]
                row["remaining_work"] = update["remaining_work"]
            if name == "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl":
                row["proof_status"] = "same_evidence_class_disposition_contract_materialized"
        write_jsonl(route_path(name), rows)


def update_hypothesis_and_intel(summary: dict[str, Any]) -> None:
    hypothesis_rows = read_jsonl(route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl"))
    new_hypotheses = [
        {
            "question_id": "W2HYP-V3-DISPOSITION-001",
            "origin": "code_config",
            "parent_question_ids": ["W2Q_V3_DEFAULT_OFF_LIVE_DIVERGENCE"],
            "trigger_source_path": "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
            "trigger_row_ids": ["v3_to_v4:full_v3_live_authority_claim"],
            "trigger_field_values": summary["v3_summary"],
            "hypothesis": "V3 should be mined as staged/default-off or research-only input, while the full-live-authority claim is rejected.",
            "falsification_test": "Config flags and Wave1B live authority matrix would need to show V3 was enabled and applied to execution at halt time.",
            "pursuit_actions": ["wave2_v3_validation_ai_dual_broker_disposition_pass"],
            "same_evidence_class_repairs_attempted": ["v3_disposition_labels_materialized"],
            "result_artifact": "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
            "status": "accepted_as_v3_to_v4_disposition_boundary",
            "downstream_v4_requirement_id": "v3_to_v4_component_disposition",
            "derived_wave3_lane": "v3_to_v4_disposition",
        }
    ]
    write_jsonl(
        route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl"),
        append_unique_by_key(hypothesis_rows, new_hypotheses, "question_id"),
    )

    intel_rows = read_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"))
    new_intel = [
        {
            "intelligence_id": "W2INTEL-CONT-V3-VALIDATION-AI-DUAL-001",
            "origin": "wave2_v3_validation_ai_dual_broker_disposition",
            "finding": "V3 disposition labels, validation/replay contract, AI guard contract, and FTMO no-copy dual-broker rows are now materialized.",
            "source_paths": [
                "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
                "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl",
                "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
                "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json",
            ],
            "evidence_class": "disposition_contract_not_live_activation",
            "downstream_question_ids": [
                "W2Q_DUAL_BROKER_CONSTRAINTS",
                "W2Q_FTMO_NO_COPY_RULE",
                "W2Q_VALIDATION_REPLAY",
                "W2Q_AI_RELIABILITY",
                "W2Q_V3_DEFAULT_OFF_LIVE_DIVERGENCE",
            ],
            "status": "accepted_disposition_contract_materialized",
            "v4_requirement_id": "wave3_contract_pack_inputs",
            "summary": summary,
        }
    ]
    write_jsonl(
        route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"),
        append_unique_by_key(intel_rows, new_intel, "intelligence_id"),
    )


def update_blockers(summary: dict[str, Any]) -> None:
    remove_ids = {
        "wave2_v3_to_v4_disposition_execution_pending",
        "wave2_validation_replay_execution_pending",
        "wave2_ai_reliability_execution_pending",
        "wave2_dual_broker_ftmo_no_copy_contract",
    }
    rows = [row for row in read_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl")) if row.get("blocker_id") not in remove_ids]
    rows.extend(
        [
            {
                "blocker_id": "wave2_v3_to_v4_disposition_execution_pending",
                "source_path": "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
                "evidence_class": "v3_disposition_materialized_v4_implementation_pending",
                "missing_file_path_field_source": "Selector/Scheduler/Execution V4 implementation, tests, and promotion dossier",
                "searched_roots_or_repairs": [
                    "research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04",
                    "config/agent_config.yaml",
                    "tests/test_moonshot_v3_runtime_packages.py",
                ],
                "reason_repair_not_complete_in_initial_spine": "Disposition is now labeled; implementation remains Wave3.",
                "owner_access_source_capture_requirement": "Implement V4 code/tests in Wave3; no live deployment or broker mutation.",
                "downstream_lane": "v3_to_v4_disposition",
                "status": "disposition_materialized_v4_implementation_pending",
                "row_count": summary["v3_summary"].get("v3_disposition_rows"),
            },
            {
                "blocker_id": "wave2_validation_replay_execution_pending",
                "source_path": "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
                "evidence_class": "validation_contract_materialized_not_executed",
                "missing_file_path_field_source": "sealed partition execution, digital twin replay, and stress results",
                "searched_roots_or_repairs": ["WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json", "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json"],
                "reason_repair_not_complete_in_initial_spine": "Contract is materialized; validation execution crosses into Wave3 digital-twin implementation.",
                "owner_access_source_capture_requirement": "Run sealed replay/digital twin after implementation; no paid AI or vendor calls by default.",
                "downstream_lane": "historical_replay_digital_twin_v4",
                "status": "contract_materialized_execution_pending",
            },
            {
                "blocker_id": "wave2_ai_reliability_execution_pending",
                "source_path": "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json",
                "evidence_class": "ai_guard_contract_materialized_not_live_activation",
                "missing_file_path_field_source": "AI calibration, schema/version traces, cached/budgeted audit rows after deterministic replay",
                "searched_roots_or_repairs": ["config/agent_config.yaml", "src/components/ai_call_policy.py", "src/components/ai_supervisor.py", "shadow_logs"],
                "reason_repair_not_complete_in_initial_spine": "AI role/guard is materialized; measured value audit remains Wave3.",
                "owner_access_source_capture_requirement": "Use no-API replay first; paid AI requires manifest/budget/owner approval/cache.",
                "downstream_lane": "ai_reliability_cost_control",
                "status": "contract_materialized_execution_pending",
                "runtime_log_counts": summary.get("ai_log_counts"),
            },
            {
                "blocker_id": "wave2_dual_broker_ftmo_no_copy_contract",
                "source_path": "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl",
                "evidence_class": "dual_broker_contract_materialized_implementation_pending",
                "missing_file_path_field_source": "V4 broker-local FTMO risk/cost/session/account-history verifier and no-copy tests",
                "searched_roots_or_repairs": [
                    "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04",
                ],
                "reason_repair_not_complete_in_initial_spine": "No-copy contract is materialized; target broker implementation/verifier remains Wave3.",
                "owner_access_source_capture_requirement": "No redacted_account lot/fill/cash/spec/lifecycle copying into FTMO; explicit FTMO account-history export required for FTMO broker-real cash claims.",
                "downstream_lane": "dual_broker_runtime_contract",
                "status": "contract_materialized_implementation_pending",
                "row_count": summary["dual_broker_summary"].get("dual_broker_rows"),
            },
        ]
    )
    write_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"), rows)


def update_source_ledgers() -> None:
    searched_rows = read_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"))
    new_roots = []
    for root in [WAVE1B_DIR, WAVE1C_DIR, REPO_ROOT / "config", REPO_ROOT / "src/components", REPO_ROOT / "tests"]:
        new_roots.append(
            {
                "generated_at_utc": GENERATED_AT,
                "root": root.as_posix(),
                "exists": root.exists(),
                "file_count": sum(1 for item in root.rglob("*") if item.is_file()) if root.exists() and root.is_dir() else 0,
                "search_method": "wave2_v3_validation_ai_dual_broker_disposition_targeted_scan",
                "search_status": "searched_for_disposition_contract_materialization",
                "evidence_class": "read_only_disposition_source_search",
            }
        )
    write_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"), append_unique_by_key(searched_rows, new_roots, "root"))

    inv_rows = read_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"))
    source_files = [
        WAVE1B_DIR / "V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl",
        WAVE1B_DIR / "LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl",
        WAVE1B_DIR / "WAVE1B_REPAIR_REQUIREMENT_LEDGER.jsonl",
        WAVE1C_DIR / "redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl",
        WAVE1C_DIR / "COST_SWAP_SLIPPAGE_SPEC_SESSION_LEDGER.jsonl",
        WAVE1C_DIR / "FOLLOWER_PROJECTOR_LIFECYCLE_LEDGER.jsonl",
        REPO_ROOT / "config/agent_config.yaml",
        REPO_ROOT / "src/components/ai_call_policy.py",
        REPO_ROOT / "src/components/ai_supervisor.py",
        REPO_ROOT / "src/research/moonshot_v3_runtime_packages.py",
    ]
    new_inv: list[dict[str, Any]] = []
    for path in source_files:
        new_inv.append(
            {
                "path": route_rel(path),
                "kind": "file",
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
                "inventory_scope": "wave2_v3_validation_ai_dual_broker_disposition",
                "evidence_class": "disposition_contract_source",
                "source_capture_status": "consumed_read_only_disposition_repair",
                "consume_status": "consumed_for_disposition_contract_repair",
            }
        )
    write_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"), append_unique_by_key(inv_rows, new_inv, "path"))


def update_summary_artifacts(summary: dict[str, Any]) -> None:
    write_json(route_path("WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json"), summary)

    coverage = read_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"))
    materialization = dict(coverage.get("continuation_materialization") or {})
    materialization.update(
        {
            "generated_at_utc": GENERATED_AT,
            "v3_disposition_rows": summary["v3_summary"].get("v3_disposition_rows"),
            "dual_broker_disposition_rows": summary["dual_broker_summary"].get("dual_broker_rows"),
            "ai_log_counts": summary.get("ai_log_counts"),
            "status": "same_evidence_class_continuation_materialized_not_wave2_complete",
        }
    )
    coverage["continuation_materialization"] = materialization
    coverage["coverage_gap"] = (
        "Wave2 now includes row-level market/system, selector repair, allocator replay, zero-trade rank, "
        "final-say join, MT5 read-only source recovery, local proxy market-data repair, broker cost/shadow "
        "slippage source-coverage repair, enriched pending/no-fill lifecycle reconciliation, and V3/validation/AI/"
        "dual-broker disposition contracts; remaining completion still requires full Wave3 prompt pack and V4 "
        "implementation/validation execution."
    )
    write_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"), coverage)

    final_state = read_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"))
    counts = dict(final_state.get("continuation_materialization_counts") or {})
    counts["v3_disposition"] = summary["v3_summary"].get("v3_disposition_rows")
    counts["dual_broker_disposition"] = summary["dual_broker_summary"].get("dual_broker_rows")
    final_state["continuation_materialization_counts"] = counts
    final_state["generated_at_utc"] = GENERATED_AT
    truths = list(final_state.get("truths") or [])
    for truth in [
        "V3 full live authority claim is rejected; useful V3 components are labeled active, staged_default_off, research_only, or rejected for V4",
        "FTMO no-copy rule is materialized: redacted_account lots, fills, cash, costs, specs, and lifecycle truth cannot be copied to target broker truth",
        "validation/replay and AI reliability are materialized as contracts, not completed validation or live AI activation",
    ]:
        if truth not in truths:
            truths.append(truth)
    final_state["truths"] = truths
    gaps = list(final_state.get("blocking_gaps") or [])
    for gap in [
        "Wave3 prompt pack and prompt hardening remain to be generated after disposition closure",
        "V4 implementation and sealed validation execution remain pending",
    ]:
        if gap not in gaps:
            gaps.append(gap)
    final_state["blocking_gaps"] = gaps
    final_state["wave3_prompt_pack_allowed"] = False
    final_state["status"] = "not_final_incomplete_master_state_continuation_materialized"
    write_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"), final_state)


def update_markdown(summary: dict[str, Any]) -> None:
    completion_path = route_path("WAVE2_COMPLETION_AUDIT.md")
    completion = completion_path.read_text(encoding="utf-8")
    bullet = (
        f"- `WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl` now has {summary['v3_summary'].get('v3_disposition_rows')} "
        "labeled disposition rows, including rejection of the full-V3-live-authority claim; validation/AI and "
        "dual-broker no-copy contracts are materialized but not implemented/executed.\n"
    )
    if "rejection of the full-V3-live-authority claim" not in completion:
        completion = completion.replace("Still not complete:\n\n", bullet + "\nStill not complete:\n\n")
    completion_path.write_text(completion, encoding="utf-8")

    saturation_path = route_path("WAVE2_SATURATION_SELF_RED_TEAM.md")
    saturation = saturation_path.read_text(encoding="utf-8")
    bullet2 = (
        "- V3/validation/AI/dual-broker disposition was pushed past open-question status: each now has a materialized "
        "contract or labeled disposition, while implementation and validation execution stay in Wave3.\n"
    )
    if "V3/validation/AI/dual-broker disposition was pushed past open-question status" not in saturation:
        saturation = saturation.replace("Remaining skeptical rejection points:\n\n", bullet2 + "\nRemaining skeptical rejection points:\n\n")
    saturation_path.write_text(saturation, encoding="utf-8")


def regenerate_manifest() -> None:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        files.append(
            {
                "path": route_rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
            }
        )
    write_json(
        route_path("WAVE2_OUTPUT_MANIFEST.json"),
        {
            "generated_at_utc": GENERATED_AT,
            "completion_status": "continuation_materialized_not_complete",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> int:
    v3_rows, v3_summary = build_v3_disposition_rows()
    dual_rows, dual_summary = build_dual_broker_rows()
    v3_count = write_jsonl(route_path("WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl"), v3_rows)
    dual_count = write_jsonl(route_path("WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl"), dual_rows)
    if v3_count < 13 or dual_count != 7:
        raise ValueError(f"unexpected disposition row counts v3={v3_count} dual={dual_count}")
    contract_summary = update_contracts(v3_summary, dual_summary)
    update_capture_replay_ai_ledger(contract_summary)
    update_production_component_ledger()
    update_question_ledgers(contract_summary)
    update_hypothesis_and_intel(contract_summary)
    update_blockers(contract_summary)
    update_source_ledgers()
    update_summary_artifacts(contract_summary)
    update_markdown(contract_summary)
    regenerate_manifest()
    print(json.dumps({"ok": True, "v3_rows": v3_count, "dual_rows": dual_count, "summary": contract_summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
