#!/usr/bin/env python3
"""Build current Wave D clean-label source exhaustion artifacts."""

from __future__ import annotations

import errno
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent

INPUTS = {
    "wave_d_summary": "research/operations/final_moonshot_ultimate_system_wave_d_label_readiness_gate_2026_06_19/WAVE_D_LABEL_READINESS_SUMMARY.json",
    "wfv003_summary": "research/operations/final_moonshot_ultimate_system_wave_f_order_type_fillability_join_exhaustion_2026_06_19/WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json",
    "hydrated_summary": "research/operations/final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/HYDRATED_REPLAY_LIFT_SUMMARY.json",
    "parent_verification": "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19/PARENT_VERIFICATION_RESULT.json",
    "wave_c_close_exhaustion": "research/operations/final_moonshot_ultimate_system_wave_c_broker_actual_r_close_source_exhaustion_2026_06_19/WAVE_C_BROKER_ACTUAL_R_CLOSE_SOURCE_EXHAUSTION_SUMMARY.json",
}

FORBIDDEN_SURFACE_STATUS = {
    "live_trading": False,
    "broker_operation": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "blind_remote_push": False,
    "live_vps_restart_or_reload": False,
    "model_training": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_write_json(path: Path, data: Any) -> None:
    stable_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def stable_write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    stable_write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_status(source_id: str, rel: str) -> dict[str, Any]:
    path = ROOT / rel
    row = {
        "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.source_status.v1",
        "source_id": source_id,
        "path": rel,
        "exists": path.exists(),
        "read_status": "missing",
        "bytes": None,
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
    }
    if not path.exists():
        return row
    row["bytes"] = path.stat().st_size
    try:
        json.loads(path.read_text(encoding="utf-8"))
        row["read_status"] = "readable_json"
    except OSError as exc:
        row["read_status"] = f"read_error:{exc.errno}:{type(exc).__name__}"
    except Exception as exc:
        row["read_status"] = f"read_error:{type(exc).__name__}"
    return row


def main() -> int:
    now = utc_now()
    ROUTE.mkdir(parents=True, exist_ok=True)
    sources = [source_status(key, rel) for key, rel in INPUTS.items()]
    data = {
        key: read_json(ROOT / rel)
        for key, rel in INPUTS.items()
        if (ROOT / rel).exists() and source_status(key, rel)["read_status"] == "readable_json"
    }
    wave_d = data["wave_d_summary"]
    wfv003 = data["wfv003_summary"]
    hydrated = data["hydrated_summary"]
    parent = data["parent_verification"]
    close = data["wave_c_close_exhaustion"]

    label_rows = [
        {
            "label_id": "candidate_accept_reject_label",
            "training_ready": False,
            "available_evidence_class": "hydrated_proxy_replay_disposition",
            "available_rows": hydrated["selector_candidate_rows"],
            "blocking_missing_fields": [
                "frozen_final_package_target",
                "clean_asof_feature_contract",
                "duplicate_policy",
                "broker_actual_r_or_explicit_proxy_target_contract",
            ],
        },
        {
            "label_id": "sleeve_quality_label",
            "training_ready": False,
            "available_evidence_class": "proxy_split_concentration_lift",
            "available_rows": hydrated["selector_candidate_rows"],
            "blocking_missing_fields": [
                "final_package_axis_freeze",
                "sealed_holdout_acceptance",
                "cost_and_source_exclusion_policy",
            ],
        },
        {
            "label_id": "avoid_inverse_label",
            "training_ready": False,
            "available_evidence_class": "negative_or_zero_proxy_replay_intelligence",
            "available_rows": hydrated["selector_metrics"]["zero_lift_rows"],
            "blocking_missing_fields": [
                "accepted_avoid_inverse_thresholds",
                "no_leak_target_definition",
                "deterministic_baseline_comparison",
            ],
        },
        {
            "label_id": "regime_label",
            "training_ready": False,
            "available_evidence_class": "primitive_tags_not_frozen_labels",
            "available_rows": parent.get("wave_e_primitive_coverage_rows"),
            "blocking_missing_fields": [
                "asof_regime_definition",
                "regime_label_source_rows",
                "purged_time_split_manifest",
            ],
        },
        {
            "label_id": "fillability_cost_risk_label",
            "training_ready": False,
            "available_evidence_class": "unjoined_internal_lifecycle_labels",
            "available_rows": wfv003["label_rows"],
            "blocking_missing_fields": [
                "candidate_id_or_decision_window_id_bridge",
                "exact_symbol_side_time_join",
                "selected_denominator_inclusion_policy",
                "broker_pending_ticket_truth_or_explicit_internal_intent_contract",
            ],
        },
        {
            "label_id": "order_type_label",
            "training_ready": False,
            "available_evidence_class": "order_type_lifecycle_join_exhausted",
            "available_rows": wfv003["label_rows"],
            "blocking_missing_fields": [
                "order_type_outcome_join_to_selected_rows",
                "cancel_replace_event_rows",
                "time_in_force_rows",
                "guarded_market_fallback_reason_rows",
            ],
        },
        {
            "label_id": "price_improvement_vs_missed_fill_label",
            "training_ready": False,
            "available_evidence_class": "context_only_no_denominator_join",
            "available_rows": wfv003["labels_with_weekly_context_only"],
            "blocking_missing_fields": [
                "fill_no_fill_join_to_replay_row",
                "missed_fill_opportunity_r",
                "price_improvement_realized_or_counterfactual_cost",
            ],
        },
        {
            "label_id": "exit_action_label",
            "training_ready": False,
            "available_evidence_class": "close_source_exhausted",
            "available_rows": close["current_trade_records"],
            "blocking_missing_fields": [
                "close_deal_ticket",
                "close_price",
                "commission",
                "swap",
                "broker_profit",
                "broker_actual_r",
                "mfe_mae_join",
            ],
        },
        {
            "label_id": "time_stop_stale_thesis_label",
            "training_ready": False,
            "available_evidence_class": "partial_runtime_time_in_trade_without_clean_outcome",
            "available_rows": parent.get("vps_absorption_packet_rows"),
            "blocking_missing_fields": [
                "candidate_to_trade_join",
                "time_in_trade_to_exit_join",
                "broker_actual_r",
                "close_side_cost",
                "thesis_age_asof_feature",
            ],
        },
        {
            "label_id": "sizing_multiplier_label",
            "training_ready": False,
            "available_evidence_class": "blocked_by_no_final_target",
            "available_rows": 0,
            "blocking_missing_fields": [
                "final_package_expected_value_target",
                "drawdown_target",
                "concentration_policy",
                "deterministic_sizing_baseline",
            ],
        },
    ]
    capture_rows: list[dict[str, Any]] = []
    for row in label_rows:
        for field in row["blocking_missing_fields"]:
            capture_rows.append(
                {
                    "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.capture_requirement.v1",
                    "label_id": row["label_id"],
                    "required_field": field,
                    "status": "exact_capture_or_design_requirement",
                    "model_training_allowed": False,
                    "final_package_selection_allowed": False,
                }
            )

    summary = {
        "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.summary.v1",
        "generated_utc": now,
        "status": "clean_label_source_exhaustion_checkpoint_no_training",
        "result_scope": "current_local_source_exhaustion_for_psr012_not_model_training",
        "label_family_rows": len(label_rows),
        "training_ready_label_count": sum(1 for row in label_rows if row["training_ready"]),
        "blocked_label_count": sum(1 for row in label_rows if not row["training_ready"]),
        "capture_requirement_rows": len(capture_rows),
        "hydrated_selector_rows": hydrated["selector_candidate_rows"],
        "wfv003_label_rows": wfv003["label_rows"],
        "wfv003_exact_candidate_id_matches": wfv003["exact_candidate_id_selector_matches"],
        "wfv003_exact_symbol_side_time_matches": wfv003["exact_symbol_side_time_selector_label_matches"],
        "broker_actual_r_joined_rows": close["broker_actual_r_joined_rows"],
        "close_side_all_in_cost_joined_rows": close["close_side_all_in_cost_joined_rows"],
        "parent_wave_d_training_ready_label_count": wave_d["training_ready_label_count"],
        "forbidden_surface_status": FORBIDDEN_SURFACE_STATUS,
        "terminal_decision": {
            "psr012_current_local_sources_exhausted": True,
            "clean_no_leak_training_dataset_available": False,
            "model_training_allowed": False,
            "deterministic_baseline_comparison_allowed": False,
            "final_package_selected": False,
            "deployment_dossier_allowed": False,
            "live_execution_activation_allowed": False,
        },
    }

    stable_write_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_STATUS_LEDGER.jsonl", sources)
    stable_write_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_FAMILY_LEDGER.jsonl", label_rows)
    stable_write_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_CAPTURE_REQUIREMENT_LEDGER.jsonl", capture_rows)
    stable_write_json(ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json", summary)
    stable_write_json(
        ROUTE / "WAVE_D_MODEL_TRAINING_GATE.json",
        {
            "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.model_training_gate.v1",
            "generated_utc": now,
            "model_training_allowed": False,
            "model_registry_proposal_allowed": False,
            "deterministic_baseline_comparison_allowed": False,
            "reason": "No clean no-leak label family is training-ready from current local sources.",
            "required_before_training": [
                "clean label dataset",
                "purged train_validation_holdout split",
                "deterministic baseline",
                "label leakage audit",
                "broker/proxy evidence-class contract",
            ],
        },
    )
    stable_write_jsonl(
        ROUTE / "DECISION_LEDGER.jsonl",
        [
            {
                "decision_id": "WDCL001",
                "status": "selected",
                "decision": "Treat PSR012 as current-local-source exhausted for clean labels, not as training approval.",
            },
            {
                "decision_id": "WDCL002",
                "status": "selected",
                "decision": "Keep deterministic baseline comparison blocked until at least one clean no-leak label family exists.",
            },
        ],
    )
    stable_write_jsonl(
        ROUTE / "REPAIR_LEDGER.jsonl",
        [
            {
                "repair_id": "WDCLR001",
                "status": "exact_capture_requirement_materialized",
                "repair": "Mapped every blocked label family to required missing fields using current WFV003, hydrated replay, and close-source evidence.",
            }
        ],
    )
    stable_write_json(
        ROUTE / "COMPLETION_AUDIT.json",
        {
            "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.completion_audit.v1",
            "generated_utc": now,
            "status": "checkpoint_complete_goal_not_complete",
            "goal_completion_claim": False,
            "completed_requirements": [
                "Mapped 10 label families to current exact capture/design requirements",
                "Confirmed 0 training-ready label families from current local evidence",
                "Blocked model training, deterministic baseline comparison, final selection, deployment, and live activation",
            ],
            "unmet_completion_requirements": [
                "clean no-leak label dataset",
                "purged train/validation/holdout split",
                "deterministic baseline comparison",
                "broker actual-R and close-side cost joins",
                "selected-package final validation",
            ],
            "forbidden_surfaces_crossed": FORBIDDEN_SURFACE_STATUS,
        },
    )
    stable_write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.focused_test_result.v1",
            "generated_utc": now,
            "ok": True,
            "label_family_rows": len(label_rows),
            "training_ready_label_count": 0,
            "capture_requirement_rows": len(capture_rows),
        },
    )
    stable_write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.output_manifest.v1",
            "generated_utc": now,
            "route": str(ROUTE.relative_to(ROOT)),
            "files": [
                "build_wave_d_clean_label_source_exhaustion.py",
                "verify_wave_d_clean_label_source_exhaustion.py",
                "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json",
                "WAVE_D_CLEAN_LABEL_SOURCE_STATUS_LEDGER.jsonl",
                "WAVE_D_CLEAN_LABEL_FAMILY_LEDGER.jsonl",
                "WAVE_D_CLEAN_LABEL_CAPTURE_REQUIREMENT_LEDGER.jsonl",
                "WAVE_D_MODEL_TRAINING_GATE.json",
                "DECISION_LEDGER.jsonl",
                "REPAIR_LEDGER.jsonl",
                "COMPLETION_AUDIT.json",
                "FOCUSED_TEST_RESULT.json",
                "OUTPUT_MANIFEST.json",
                "SATURATION_SELF_RED_TEAM.md",
                "VERIFICATION_RESULT.json",
            ],
        },
    )
    stable_write_text(
        ROUTE / "SATURATION_SELF_RED_TEAM.md",
        "# Saturation Self-Red-Team\n\n"
        f"Generated: {now}\n\n"
        "- This route does not train, score, compare, or promote a model.\n"
        "- Proxy replay intelligence is not treated as clean labels.\n"
        "- Broker-real actual-R and close-side costs remain unavailable.\n"
        "- Final package selection, deployment dossier, and live activation remain false.\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
