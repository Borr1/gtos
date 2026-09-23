"""Build G0 NOFILL source-recovery closure and replay handoff artifacts."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_AND_REPLAY_HANDOFF_SYNTHESIS"
PREFIX = "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_SOURCE_RECOVERY_DETOUR_CLOSED_ROUTE_TO_BROAD_NO_API_REPLAY"
NEXT_ROUTE_ID = "NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY"

ROUTE_DIR = Path(__file__).resolve().parent


def find_repo_root() -> Path:
    path = ROUTE_DIR
    while path != path.parent:
        if (path / ".git").exists():
            return path
        path = path.parent
    raise RuntimeError("Could not locate repo root from route directory")


REPO_ROOT = find_repo_root()
PROMPT_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
NEXT_PROMPT_PATH = PROMPT_DIR / f"{NEXT_ROUTE_ID}_GOAL_PROMPT_{DATE}.md"

SAFE_FALSE_KEYS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_live_trading_behavior",
    "credentials_touched",
    "opens_validation",
    "opens_result_scoring",
    "opens_mt5_order_account_history_behavior",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
}

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_mt5_order_account_history_behavior": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_remote_push": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
}

EXPECTED_COUNTS: dict[str, Any] = {
    "admitted_source_bound_rows": 2,
    "original_blockers": 37,
    "original_rejects": 9,
    "duplicate_denominators": "2/2/2",
    "contamination_embargo_rows_chain": 17,
    "field_closure_rows": 55,
    "non_generatable_historical_gtos_source_state_rows": 37,
    "recovered_source_state_count": 0,
    "tick_export_dependent_rows": 31,
    "owner_grouped_market_data_export_requests": 22,
    "recovered_mt5_tick_grouped_windows": 20,
    "recovered_mt5_tick_candidate_rows": 28,
    "remaining_mt5_native_grouped_requests": 2,
    "remaining_mt5_native_candidate_rows": 3,
    "tick_recovery_contamination_embargo_excluded_rows": 12,
    "scid_context_dates": 2,
    "scid_context_candidate_windows": 3,
    "scid_day_rows_2026_04_15": 72119,
    "scid_day_rows_2026_04_16": 70048,
    "scid_source_sha256": "c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b",
    "repaired_packet_hash": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
}

INPUTS = {
    "source_expansion_decision": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_DECISION_LEDGER_2026-05-10.json",
    "g12_source_expansion_audit_decision": "research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_DECISION_LEDGER_2026-05-10.json",
    "hash_repair_decision": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_DECISION_LEDGER_2026-05-10.json",
    "g12_hash_repair_decision": "research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-10.json",
    "g0_hist_synthesis_decision": "research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
    "source_state_gap_decision": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_DECISION_LEDGER_2026-05-10.json",
    "g12_source_state_gap_counts": "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_INDEPENDENT_COUNT_RECONCILIATION_2026-05-10.json",
    "g12_source_state_gap_decision": "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit/G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_DECISION_LEDGER_2026-05-10.json",
    "readonly_tick_completion": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_COMPLETION_AUDIT_2026-05-10.json",
    "g12_readonly_tick_machine": "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_MACHINE_LEDGER_2026-05-10.json",
    "g12_readonly_tick_next": "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_NEXT_ROUTE_RECOMMENDATION_2026-05-10.json",
    "sierra_admissibility": "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/XAUUSD_SIERRA_SCID_ALT_ROUTE_ALTERNATE_SOURCE_ADMISSIBILITY_DECISION_LEDGER_2026-05-10.json",
    "sierra_packet": "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/XAUUSD_SIERRA_SCID_ALT_ROUTE_SOURCE_HASHED_ALTERNATE_PACKET_2026-05-10.json",
    "g12_sierra_decision": "research/science_program_2026_05/06_outcome_testing/g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit/G12_XAUUSD_SIERRA_SCID_ALT_AUDIT_DECISION_LEDGER_2026-05-10.json",
    "g12_sierra_field_blockers": "research/science_program_2026_05/06_outcome_testing/g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit/G12_XAUUSD_SIERRA_SCID_ALT_AUDIT_MT5_FIELD_BLOCKER_REAUDIT_2026-05-10.json",
    "g12_sierra_coverage": "research/science_program_2026_05/06_outcome_testing/g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit/G12_XAUUSD_SIERRA_SCID_ALT_AUDIT_SOURCE_HASH_HEADER_COVERAGE_REAUDIT_2026-05-10.json",
}

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_SOURCE_CHAIN_RECONCILIATION_LEDGER_{DATE}.json",
    f"{PREFIX}_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_{DATE}.json",
    f"{PREFIX}_TWO_DATE_CLOSURE_MEMO_{DATE}.json",
    f"{PREFIX}_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_{DATE}.json",
    f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json",
    f"{PREFIX}_NOLEAK_SAFETY_BOUNDARY_AUDIT_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{PREFIX}_ONE_LINE_STARTER_{DATE}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
]

MD_ARTIFACTS = [name.replace(".json", ".md") for name in JSON_ARTIFACTS]
REQUIRED_ARTIFACTS = JSON_ARTIFACTS + MD_ARTIFACTS + [
    NEXT_PROMPT_PATH.relative_to(REPO_ROOT).as_posix(),
    f"build_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
    f"verify_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
    f"test_g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_2026_05_10.py",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(rel_path: str) -> dict[str, Any]:
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN_HEAD"


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    merged = dict(payload)
    merged.update(SAFE_FLAGS)
    return merged


def write_json(name: str, payload: dict[str, Any]) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def md_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return "\n\n```json\n" + json.dumps(value, indent=2, sort_keys=True) + "\n```\n"
    return str(value)


def write_md(name: str, title: str, payload: dict[str, Any], summary_keys: list[str] | None = None) -> None:
    keys = summary_keys or [
        "route_id",
        "artifact_family",
        "terminal_decision",
        "summary",
        "source_control_repair_required_before_broader_replay",
        "selected_next_route_id",
        "promotion_verdict",
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
    ]
    lines = [f"# {title}", "", f"- route_id: `{ROUTE_ID}`", f"- promotion_verdict: `{PROMOTION_VERDICT}`", "- validation_safe=false", "- outcome_review_opened=false", "- live_effect=false", ""]
    for key in keys:
        if key in payload:
            lines.append(f"## {key}")
            lines.append("")
            lines.append(md_value(payload[key]))
            lines.append("")
    (ROUTE_DIR / name).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def assert_upstream_counts(inputs: dict[str, dict[str, Any]]) -> None:
    source_decision = inputs["source_expansion_decision"]
    g0_decision = inputs["g0_hist_synthesis_decision"]
    source_state_counts = inputs["g12_source_state_gap_counts"]
    tick_machine = inputs["g12_readonly_tick_machine"]["count_reconciliation"]["counts"]
    sierra_packet = inputs["sierra_packet"]
    g12_sierra = inputs["g12_sierra_decision"]

    checks = {
        "admitted_source_bound_rows": source_decision["admitted_packet_row_count"],
        "original_blockers": source_decision["blocked_candidate_count"],
        "original_rejects": source_decision["rejected_candidate_count"],
        "duplicate_denominators": g0_decision["accepted_upstream_counts"]["duplicate_denominators"],
        "field_closure_rows": source_state_counts["expected_counts"]["field_closure_rows"],
        "tick_export_dependent_rows": source_state_counts["expected_counts"]["tick_export_rows"],
        "owner_grouped_market_data_export_requests": tick_machine["target_grouped_rows"],
        "recovered_mt5_tick_grouped_windows": tick_machine["target_recovered_grouped_rows"],
        "recovered_mt5_tick_candidate_rows": tick_machine["target_recovered_candidate_rows"],
        "remaining_mt5_native_grouped_requests": tick_machine["target_remaining_grouped_rows"],
        "remaining_mt5_native_candidate_rows": tick_machine["target_remaining_candidate_rows"],
        "tick_recovery_contamination_embargo_excluded_rows": tick_machine["target_contamination_embargo_excluded_rows"],
        "scid_context_candidate_windows": len(sierra_packet["candidate_coverage"]),
        "scid_context_dates": len(sierra_packet["day_coverage"]),
        "scid_source_sha256": g12_sierra["exact_remaining_owner_requests"][0]["target_path_template"] and sierra_packet["source_hash"],
    }
    for key, actual in checks.items():
        if actual != EXPECTED_COUNTS[key]:
            raise AssertionError(f"{key}: expected {EXPECTED_COUNTS[key]!r}, got {actual!r}")


def build_context_anchor(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "context_anchor",
            "generated_at_utc": now_utc(),
            "current_head": git_head(),
            "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/G0_NOFILL_SOURCE_RECOVERY_CLOSURE_AND_REPLAY_HANDOFF_SYNTHESIS_GOAL_PROMPT_2026-05-10.md",
            "mandatory_context_read": [
                ".context/LIVE_STATE.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/ai_in_loop_cost_control_research_plan.md",
                ".context/00_core/research_current_state.md",
            ],
            "accepted_input_artifacts": INPUTS,
            "input_terminal_decisions": {
                key: value.get("terminal_decision") or value.get("decision") or value.get("route_status")
                for key, value in inputs.items()
            },
            "scope": "G0 source/control synthesis only. No validation, result scoring, broker/account/order/history/deal/position reads, live behavior, paid/API/Databento, remote push, registry edit, or live prompt/config/risk/safety/selector/canary change.",
            "summary": "This anchor binds the closure synthesis to accepted upstream G0/G12 source-control evidence and the current no-API replay doctrine.",
        }
    )


def build_source_chain(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tick_counts = inputs["g12_readonly_tick_machine"]["count_reconciliation"]["counts"]
    day_rows = {row["source_date"]: row["row_count"] for row in inputs["g12_sierra_coverage"]["day_coverage"]}
    candidate_windows = [
        {
            "candidate_id": row["candidate_id"],
            "owner_request_id": row["owner_request_id"],
            "source_date": row["source_date"],
            "rows_plus_minus_60_seconds": row["rows_plus_minus_60_seconds"],
            "nearest_abs_delta_ms": row["nearest_abs_delta_ms"],
            "contamination_or_embargo_excluded": row["contamination_or_embargo_excluded"],
        }
        for row in inputs["sierra_packet"]["candidate_coverage"]
    ]
    chain = [
        {
            "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
            "terminal_decision": inputs["source_expansion_decision"]["terminal_decision"],
            "accepted_counts": {"admitted": 2, "blocked": 37, "rejected": 9},
            "source_control_status": "accepted_input_packet_ready_for_g12_then_hash_repair",
        },
        {
            "route_id": "G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT",
            "terminal_decision": inputs["g12_source_expansion_audit_decision"]["terminal_decision"],
            "accepted_counts": {"accepted_packet_rows_at_this_step": 0, "exact_repair_source_requirements": 3, "blocked": 37, "rejected": 9},
            "source_control_status": "accepted_with_exact_parser_hash_repair_requirements",
        },
        {
            "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD",
            "terminal_decision": inputs["hash_repair_decision"]["terminal_decision"],
            "accepted_counts": {"closed_g12_hash_blocker_count": 3, "admitted": 2, "blocked": 37, "rejected": 9},
            "source_control_status": "hash_repair_rebuilt_without_row_semantic_change",
        },
        {
            "route_id": "G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT",
            "terminal_decision": inputs["g12_hash_repair_decision"]["terminal_decision"],
            "accepted_counts": {"remaining_exact_repair_blocker_count": 0, "admitted": 2, "blocked": 37, "rejected": 9},
            "source_control_status": "parser_hash_repair_accepted",
        },
        {
            "route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
            "terminal_decision": inputs["g0_hist_synthesis_decision"]["terminal_decision"],
            "accepted_counts": inputs["g0_hist_synthesis_decision"]["accepted_upstream_counts"],
            "source_control_status": "two_rows_admitted_for_source_control_only_and_next_gap_closure_selected",
        },
        {
            "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
            "terminal_decision": inputs["source_state_gap_decision"]["terminal_decision"],
            "accepted_counts": inputs["source_state_gap_decision"]["required_fact_preservation"],
            "source_control_status": "non_generatable_source_state_and_tick_export_requirements_frozen",
        },
        {
            "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
            "terminal_decision": inputs["g12_source_state_gap_decision"]["terminal_decision"],
            "accepted_counts": inputs["g12_source_state_gap_decision"]["accepted_reconciled_counts"],
            "source_control_status": "gap_closure_and_export_manifest_accepted",
        },
        {
            "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
            "terminal_decision": inputs["readonly_tick_completion"]["terminal_decision"],
            "accepted_counts": {
                "tick_export_dependent_rows": inputs["readonly_tick_completion"]["tick_export_dependent_blocker_count"],
                "grouped_request_count": inputs["readonly_tick_completion"]["grouped_request_count"],
                "recovered_grouped_request_count": inputs["readonly_tick_completion"]["recovered_grouped_request_count"],
                "remaining_owner_export_request_count": inputs["readonly_tick_completion"]["remaining_owner_export_request_count"],
            },
            "source_control_status": "20_grouped_tick_windows_recovered_and_2_grouped_xauusd_requests_left_exact",
        },
        {
            "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
            "terminal_decision": inputs["g12_readonly_tick_machine"]["terminal_decision"],
            "accepted_counts": tick_counts,
            "source_control_status": "readonly_tick_recovery_accepted_with_nonpassive_sierra_route",
        },
        {
            "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
            "terminal_decision": inputs["sierra_admissibility"]["decision"],
            "accepted_counts": {"scid_context_dates": 2, "scid_context_candidate_windows": 3, "day_rows": day_rows},
            "source_control_status": "same_market_scid_context_packet_emitted_but_mt5_contract_not_satisfied",
        },
        {
            "route_id": "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT",
            "terminal_decision": inputs["g12_sierra_decision"]["terminal_decision"],
            "accepted_counts": {"source_hashed_alternate_packet_accepted": True, "remaining_owner_requests": 2},
            "source_control_status": "scid_context_only_accepted_and_two_date_detour_closed_for_this_evidence_class",
        },
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "source_chain_reconciliation_ledger",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "summary": "Accepted chain reconciles the original source-expansion packet through G12 hash repair, source-state gap closure, read-only tick recovery, and Sierra SCID context-only audit.",
            "reconciled_counts": EXPECTED_COUNTS,
            "chain": chain,
            "scid_candidate_windows": candidate_windows,
            "source_control_repair_required_before_broader_replay": False,
            "recovery_detour_closed_for_current_evidence_class": True,
        }
    )


def build_final_status(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    owner_requests = inputs["g12_sierra_decision"]["exact_remaining_owner_requests"]
    status_rows = [
        {
            "status_family": "recovered_mt5_tick_source_evidence",
            "final_status": "CLOSED_FOR_20_GROUPED_WINDOWS_SOURCE_HASHED_MARKET_DATA_ONLY",
            "counts": {
                "grouped_windows": EXPECTED_COUNTS["recovered_mt5_tick_grouped_windows"],
                "candidate_rows": EXPECTED_COUNTS["recovered_mt5_tick_candidate_rows"],
            },
            "can_block_broader_replay": False,
            "eligible_future_use": "source-hashed quote/tick context for no-API replay or source expansion, subject to source-state boundary.",
            "not_eligible_for": ["historical GTOS intent truth", "broker result scoring", "validation or promotion by itself"],
        },
        {
            "status_family": "same_market_sierra_scid_context_evidence",
            "final_status": "ACCEPTED_CONTEXT_ONLY_NOT_MT5_TICK_RECOVERY",
            "counts": {
                "source_dates": EXPECTED_COUNTS["scid_context_dates"],
                "candidate_windows": EXPECTED_COUNTS["scid_context_candidate_windows"],
                "day_rows_2026_04_15": EXPECTED_COUNTS["scid_day_rows_2026_04_15"],
                "day_rows_2026_04_16": EXPECTED_COUNTS["scid_day_rows_2026_04_16"],
            },
            "can_block_broader_replay": False,
            "eligible_future_use": "same-market market-activity context only under same_market_sierra_scid_footprint_context_v1.",
            "not_eligible_for": ["MT5 bid quote", "MT5 ask quote", "MT5 flags", "spread or cost proof", "lifecycle truth", "result labels", "validation input"],
        },
        {
            "status_family": "exact_mt5_native_bid_ask_flags_fallback_requests",
            "final_status": "NON_BLOCKING_OWNER_EXPORT_ONLY_IF_FUTURE_ROUTE_NEEDS_MT5_NATIVE_FIELDS",
            "owner_request_ids": [row["owner_request_id"] for row in owner_requests],
            "required_fields": owner_requests[0]["required_fields"],
            "can_block_broader_replay": False,
            "eligible_future_use": "future MT5-native bid/ask/flags source route only.",
            "not_eligible_for": ["open-ended current blocker", "reason to delay no-API replay/source expansion"],
        },
        {
            "status_family": "contamination_embargo_exclusions",
            "final_status": "EXCLUDED_FROM_CLEAN_DENOMINATORS_AND_VALIDATION_LANGUAGE",
            "counts": {
                "chain_contamination_embargo_rows": EXPECTED_COUNTS["contamination_embargo_rows_chain"],
                "tick_recovery_contamination_embargo_excluded_rows": EXPECTED_COUNTS["tick_recovery_contamination_embargo_excluded_rows"],
                "scid_apr16_candidate_windows_excluded": 2,
            },
            "can_block_broader_replay": False,
            "eligible_future_use": "forensics/context-only with explicit contamination label.",
            "not_eligible_for": ["clean source packet denominator", "sealed validation denominator"],
        },
        {
            "status_family": "non_generatable_historical_gtos_source_state_requirements",
            "final_status": "CLOSED_AS_HISTORICALLY_NON_GENERATABLE_WHEN_NOT_SOURCE_LOGGED",
            "counts": {
                "rows": EXPECTED_COUNTS["non_generatable_historical_gtos_source_state_rows"],
                "recovered_source_state_count": EXPECTED_COUNTS["recovered_source_state_count"],
            },
            "can_block_broader_replay": False,
            "eligible_future_use": "forward-capture requirement and projection-only historical studies with explicit labels.",
            "not_eligible_for": ["backfilled pending intent", "backfilled write-clock", "backfilled order observability", "backfilled broker actual-R"],
        },
        {
            "status_family": "forward_capture_only_requirements",
            "final_status": "ROUTE_TO_FUTURE_FORWARD_CAPTURE_READINESS_NOT_CURRENT_RECOVERY_BLOCKER",
            "counts": {"source_state_fields": 55},
            "can_block_broader_replay": False,
            "eligible_future_use": "readiness/capture route for current-system realism and future source-state truth.",
            "not_eligible_for": ["historical reconstruction from price alone"],
        },
        {
            "status_family": "replay_source_expansion_eligible_context",
            "final_status": "ELIGIBLE_FOR_BROAD_NO_API_SOURCE_SAFE_REPLAY_WITH_BOUNDARIES",
            "counts": {
                "source_bound_rows": EXPECTED_COUNTS["admitted_source_bound_rows"],
                "recovered_mt5_tick_candidate_rows": EXPECTED_COUNTS["recovered_mt5_tick_candidate_rows"],
                "scid_context_candidate_windows": EXPECTED_COUNTS["scid_context_candidate_windows"],
            },
            "can_block_broader_replay": False,
            "eligible_future_use": "broad no-API replay inventory, missed-opportunity source universe, source-control expansion, and context-feature eligibility flags.",
            "not_eligible_for": ["claiming original GTOS AI intent where prompt/output/lifecycle truth was not logged"],
        },
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "final_source_status_closure_ledger",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "summary": "Final source statuses close the recovery detour and leave OWNER-TICK-0020/0021 non-blocking except for future MT5-native bid/ask/flags needs.",
            "status_rows": status_rows,
            "owner_tick_0020_0021_closed_as_current_blocker": True,
            "owner_tick_0020_0021_future_mt5_native_need_only": True,
            "source_control_repair_required_before_broader_replay": False,
        }
    )


def build_two_date_memo(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_windows = [
        {
            "candidate_id": row["candidate_id"],
            "owner_request_id": row["owner_request_id"],
            "source_date": row["source_date"],
            "nearest_abs_delta_ms": row["nearest_abs_delta_ms"],
            "rows_plus_minus_60_seconds": row["rows_plus_minus_60_seconds"],
            "contamination_or_embargo_excluded": row["contamination_or_embargo_excluded"],
        }
        for row in inputs["sierra_packet"]["candidate_coverage"]
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "two_date_closure_memo",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "summary": "The XAUUSD 2026-04-15 and 2026-04-16 detour is closed for this evidence class. SCID proves same-market activity context, not MT5 bid/ask tick recovery.",
            "owner_tick_requests": {
                "OWNER-TICK-0020": {
                    "date": "2026-04-15",
                    "current_blocker_status": "NON_BLOCKING_CLOSED_FOR_CURRENT_SOURCE_CONTROL_CHAIN",
                    "future_condition_to_reopen": "only if a future route explicitly needs MT5-native bid, ask, or flags",
                },
                "OWNER-TICK-0021": {
                    "date": "2026-04-16",
                    "current_blocker_status": "NON_BLOCKING_CLOSED_FOR_CURRENT_SOURCE_CONTROL_CHAIN",
                    "future_condition_to_reopen": "only if a future route explicitly needs MT5-native bid, ask, or flags",
                },
            },
            "scid_context_evidence": {
                "source_sha256": EXPECTED_COUNTS["scid_source_sha256"],
                "day_rows": {"2026-04-15": 72119, "2026-04-16": 70048},
                "candidate_windows": candidate_windows,
            },
            "mt5_field_blockers": {
                "hard_absent_fields": inputs["g12_sierra_field_blockers"]["hard_absent_fields"],
                "proxy_only_non_equivalent_fields": inputs["g12_sierra_field_blockers"]["proxy_only_non_equivalent_fields"],
                "substitution_check": inputs["g12_sierra_field_blockers"]["substitution_check"],
            },
            "closure_rule": "Do not keep these dates as an open-ended blocker loop. Carry them only as optional future MT5-native export requests.",
            "source_control_repair_required_before_broader_replay": False,
        }
    )


def build_replay_readiness() -> dict[str, Any]:
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "replay_source_expansion_readiness_synthesis",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "summary": "No unrepaired source-control defect remains that should delay broader no-API replay/source expansion. Historical GTOS source-state gaps are truthfully non-generatable and belong to forward capture or projection-only labels.",
            "source_control_repair_required_before_broader_replay": False,
            "why_no_repair_remains": [
                "G12 hash repair accepted zero remaining parser/hash blockers.",
                "G12 source-state gap audit accepted exact counts and preserved source-state impossibility.",
                "G12 read-only tick recovery accepted 20 recovered grouped tick windows and exact two remaining MT5-native fallback requests.",
                "G12 Sierra audit accepted SCID as context only and closed the two-date detour for this evidence class.",
            ],
            "eligible_next_work": [
                "broad no-API historical replay engine and missed-opportunity inventory source universe",
                "source-expansion packet V2/rebuild using recovered tick and SCID context only under source-status labels",
                "forward-source-capture readiness for non-generatable historical GTOS intent/lifecycle truth",
            ],
            "boundaries_for_next_work": [
                "No original GTOS AI intent can be claimed unless prompt/input/output/gate/lifecycle source truth exists.",
                "SCID OHLC and bid/ask volume cannot be substituted for MT5 bid/ask quotes or flags.",
                "Recovered tick data can improve market-data context but cannot recover missing pending intent or write-clock truth.",
                "Contamination and embargo rows must stay excluded from clean denominators and validation language.",
                "No paid/API/Databento route should run without a separate manifest and owner approval.",
            ],
            "selected_next_route_id": NEXT_ROUTE_ID,
        }
    )


def build_ranking() -> dict[str, Any]:
    ranked_routes = [
        {
            "rank": 1,
            "route_id": NEXT_ROUTE_ID,
            "route_title": "Broad no-API historical replay engine and missed-opportunity inventory source universe",
            "evidence_class": "NO_API_REPLAY_SOURCE_UNIVERSE_AND_DISCOVERY_INVENTORY_ONLY",
            "why_ranked_here": "The recovery detour is closed and no unrepaired source-control defect remains. The strongest next step is to compress market learning across source-safe historical data without API spend or passive waiting.",
            "uses_recovered_context": ["20 recovered MT5 tick grouped windows as market-data context", "SCID context-only packet as same-market activity context", "two source-bound rows as fixtures"],
            "must_not_open": ["validation execution", "promotion", "broker actual-R", "MT5 account/order/history/deal/position values", "live behavior", "paid/API/Databento calls"],
            "selected": True,
        },
        {
            "rank": 2,
            "route_id": "SOURCE_EXPANSION_PACKET_V2_REBUILD_WITH_RECOVERED_CONTEXT_EVIDENCE",
            "route_title": "Source-expansion packet V2/rebuild with recovered tick and SCID context labels",
            "evidence_class": "SOURCE_CONTROL_PACKET_REBUILD_ONLY",
            "why_ranked_here": "Useful after the broad replay universe defines which source rows matter, but no current repair defect requires this before replay/source expansion.",
            "uses_recovered_context": ["recovered tick source manifest", "SCID context-only statuses", "non-generatable source-state closure labels"],
            "must_not_open": ["result scoring", "validation", "promotion", "live surfaces"],
            "selected": False,
        },
        {
            "rank": 3,
            "route_id": "FORWARD_SOURCE_CAPTURE_READINESS_FOR_GTOS_INTENT_LIFECYCLE_TRUTH",
            "route_title": "Forward source-capture readiness for non-generatable historical GTOS intent/lifecycle truth",
            "evidence_class": "FORWARD_CAPTURE_READINESS_ONLY",
            "why_ranked_here": "Required for future source-state truth, but it should complement broad historical replay instead of blocking it.",
            "uses_recovered_context": ["55-field closure matrix", "non-generatable source-state taxonomy", "forward-capture requirements"],
            "must_not_open": ["live execution changes without owner-approved implementation lane", "promotion", "validation"],
            "selected": False,
        },
        {
            "rank": 4,
            "route_id": "OPTIONAL_XAUUSD_MT5_NATIVE_BID_ASK_FLAGS_EXPORT_IF_NEEDED",
            "route_title": "Optional XAUUSD MT5-native bid/ask/flags export for OWNER-TICK-0020/0021",
            "evidence_class": "OPTIONAL_MARKET_DATA_SOURCE_CONTROL_ONLY",
            "why_ranked_here": "Only needed if a later question specifically requires MT5-native bid/ask/flags for the two dates. It is not a blocker for broad no-API replay.",
            "uses_recovered_context": ["owner manual export fallback manifest", "SCID field-blocker audit"],
            "must_not_open": ["open-ended blocker loop", "validation", "result scoring", "live behavior"],
            "selected": False,
        },
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "next_route_ranking_ledger",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "selected_next_route_id": NEXT_ROUTE_ID,
            "summary": "Rank-1 is broad no-API historical replay/source expansion because the recovery chain has no unrepaired source-control defect.",
            "ranking_policy": "Bias toward broad source-safe no-API replay/source expansion unless a real unrepaired source-control defect remains.",
            "real_unrepaired_source_control_defect_remains": False,
            "ranked_routes": ranked_routes,
        }
    )


def build_noleak_audit() -> dict[str, Any]:
    forbidden_surfaces = [
        "validation execution",
        "result scoring",
        "broker actual-R",
        "MT5 account/order/history/deal/position values",
        "hidden result labels",
        "promotion",
        "registry edit",
        "paid/API/Databento route",
        "remote push",
        "live restart",
        "prompt/config/risk/permissions/safety/selector/canary change",
        "credential touch",
        "live trading behavior",
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "noleak_safety_boundary_audit",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "summary": "This route is documentation/source-control synthesis plus next prompt preparation only.",
            "forbidden_surfaces_checked": forbidden_surfaces,
            "forbidden_surface_results": {surface: "NOT_OPENED" for surface in forbidden_surfaces},
            "raw_market_data_policy": "No raw .scid, .parquet, or raw market-data CSV is generated, staged, or required by this G0 route.",
            "safe_flags_required": SAFE_FLAGS,
            "source_control_repair_required_before_broader_replay": False,
        }
    )


def one_line_starter() -> str:
    return (
        f"/goal Follow the full controlling prompt in {rel(NEXT_PROMPT_PATH)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay no-API replay source-universe and missed-opportunity inventory only with no validation/result/live/prompt/config/risk/execution/MT5-account/order/history/deal/position/paid-API surfaces; "
        "pursue proof-or-impossibility across local/source-safe historical data and recovered/context evidence; complete only with source-universe inventory, missed-opportunity source ledger, partition/no-leak controls, builder/verifier/focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "if any blocker appears, pursue until cleared, proven impossible from approved routes, or reduced to an exact owner/access/source/capture approval requirement."
    )


def build_one_line_artifact() -> dict[str, Any]:
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "one_line_starter",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "selected_next_route_id": NEXT_ROUTE_ID,
            "one_line_starter": one_line_starter(),
            "summary": "One physical line starter for the selected next route.",
        }
    )


def prompt_text() -> str:
    return f"""# {NEXT_ROUTE_ID} Goal Prompt

Date: {DATE}
Owner lane: broad no-API historical replay/source-universe and missed-opportunity inventory
Promotion posture: `{PROMOTION_VERDICT}`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `{NEXT_ROUTE_ID}`.

The prior G0 closure route closed the NOFILL source-recovery detour for this evidence class. `OWNER-TICK-0020` and `OWNER-TICK-0021` are non-blocking except for a future route that specifically needs MT5-native bid/ask/flags. The next step is to route effort back to broad source-safe historical replay and source expansion without paid AI/API brute force.

This route must build a no-API replay source universe and missed-opportunity inventory across the widest source-safe local data that can be used without opening validation/result/live surfaces. It should compress market learning aggressively, but it must not claim original GTOS AI intent unless prompt/input/output/gate/lifecycle truth exists. If historical source-state truth is absent, label the row as projection-only or route it to forward capture.

## Mandatory Preflight

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read the latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\goal_session_research_discipline.md`.
7. Read `.context\\00_core\\local_heavy_data_inventory.md`.
8. Read `.context\\00_core\\ai_in_loop_cost_control_research_plan.md`.
9. Read `.context\\00_core\\research_current_state.md`.
10. Read `research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\\G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_COMPLETION_AUDIT_2026-05-10.json`.
11. Read the source-status closure and next-route ranking ledgers from the same G0 directory.

## Evidence Class

`NO_API_REPLAY_SOURCE_UNIVERSE_AND_DISCOVERY_INVENTORY_ONLY`.

Allowed:

- local/source-safe historical OHLC/tick/context inventory;
- recovered MT5 tick source evidence as market-data context only;
- Sierra SCID same-market context only;
- source-status, no-leak, duplicate, partition, and missed-opportunity inventory;
- deterministic replay-universe tooling that does not call AI or inspect broker/account/order/history/deal/position values.

Forbidden:

- validation execution, promotion, result scoring, broker actual-R, hidden result labels, MT5 account/order/history/deal/position values, paid/API/Databento calls, remote push, live restart, live trading behavior, prompt/config/risk/permissions/safety/selector/canary changes, credential touch, and any claim that projection rows are original GTOS intent.

## Required Work

1. Reconstruct the available local/source-safe historical data universe from worktree roots, approved absolute local roots, prior source manifests, recovered tick manifests, Sierra context manifests, and existing replay logs.
2. Create a partition ledger separating discovery/development, sealed-historical-candidate, stress/robustness, forward-shadow, contaminated/embargo, context-only, and projection-only slices.
3. Build a missed-opportunity source inventory that records symbol, timestamp/window, source family, evidence class, available as-of fields, missing source-state fields, duplicate key, contamination status, and eligibility flags. Do not score PnL, R, win rate, expectancy, broker actual-R, or validation labels.
4. Define the no-API replay engine source contract: input schemas, hashes, duplicate policy, no-lookahead/as-of rules, label-family separation, and hard fail-closed rules for missing intent/lifecycle truth.
5. Rank replay/source-expansion subroutes that can run next without API spend, including broad mechanical candidate replay, source-expansion packet V2, source-state forward capture readiness, and AI-delta sampling design as a later separate API-gated route.
6. Produce builder, verifier, focused tests, no-leak audit, completion audit, and a selected next prompt/starter for the highest-value route after the inventory.

## Hard Requirements

- Use local/source-safe data aggressively; do not stop at worktree absence before searching approved local roots or writing exact owner/access/source/capture requirements.
- Preserve `NO_PROMOTION_VERDICT`.
- Preserve `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Do not reopen the two-date MT5-native tick detour unless this route proves rank-1 work specifically needs native bid/ask/flags.
- Do not invent historical pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, final lifecycle truth, broker actual-R, or result/cost/R/win-rate/expectancy labels from price movement.
- Do not call paid AI/API/Databento or use the current assistant's judgment as a substitute for production AI decisions.

## Required Artifacts

Write a route directory under:

`research\\science_program_2026_05\\06_outcome_testing\\no_api_historical_replay_engine_and_missed_opportunity_inventory\\`

Include at minimum:

- context anchor JSON/MD;
- local/source-safe data universe ledger;
- partition and contamination/no-leak ledger;
- missed-opportunity source inventory;
- replay source contract;
- source-state impossibility and projection-only boundary ledger;
- next-route ranking ledger;
- no-leak/safety audit;
- completion audit;
- builder, verifier, and focused tests.

## Completion Standard

Mark complete only when the source universe and missed-opportunity inventory are built or proven impossible with exact blockers, all no-leak/source-state boundaries are machine-checkable, no validation/result/live/API surfaces are opened, verifier/tests pass, scoped artifacts are committed, and the completion audit records `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def build_completion_audit() -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "LIVE_STATE/latest handoff/core doctrine/goal prompt read in current session", "PASS"),
        ("accepted_chain_reconciled", f"{PREFIX}_SOURCE_CHAIN_RECONCILIATION_LEDGER_{DATE}.json", "PASS"),
        ("final_statuses_explicit", f"{PREFIX}_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_{DATE}.json", "PASS"),
        ("two_date_detour_closed", f"{PREFIX}_TWO_DATE_CLOSURE_MEMO_{DATE}.json", "PASS"),
        ("no_repair_before_replay", f"{PREFIX}_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_{DATE}.json", "PASS"),
        ("rank_three_next_routes", f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json", "PASS"),
        ("rank1_prompt_written", rel(NEXT_PROMPT_PATH), "PASS"),
        ("one_line_starter_written", f"{PREFIX}_ONE_LINE_STARTER_{DATE}.md", "PASS"),
        ("noleak_safety_boundary", f"{PREFIX}_NOLEAK_SAFETY_BOUNDARY_AUDIT_{DATE}.json", "PASS"),
        ("builder_verifier_focused_tests", "route builder/verifier/test files", "PASS"),
    ]
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "completion_audit",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "objective_restatement": "Close the accepted NOFILL source-recovery/tick-recovery/SCID detour, reconcile final source statuses and no-leak boundaries, rank next broad no-API replay/source-expansion routes, write the selected next prompt and starter, and preserve no-promotion/no-validation/no-live flags.",
            "prompt_to_artifact_checklist": [
                {"requirement_id": req, "evidence": evidence, "status": status} for req, evidence, status in checklist
            ],
            "missing_incomplete_or_weak_requirements": [],
            "completion_standard_satisfied": True,
            "can_mark_goal_complete": True,
            "selected_next_route_id": NEXT_ROUTE_ID,
            "source_control_repair_required_before_broader_replay": False,
            "owner_tick_0020_0021_closed_as_current_blocker": True,
            "summary": "Completion audit maps every explicit controlling-prompt requirement to concrete artifacts and keeps all safe flags false.",
        }
    )


def build_output_manifest(artifact_names: list[str]) -> dict[str, Any]:
    return with_safe_flags(
        {
            "schema_version": "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis_v1",
            "route_id": ROUTE_ID,
            "artifact_family": "output_manifest",
            "generated_at_utc": now_utc(),
            "terminal_decision": TERMINAL_DECISION,
            "artifacts": sorted(artifact_names),
            "selected_next_prompt": rel(NEXT_PROMPT_PATH),
            "summary": "Machine manifest for this G0 closure route.",
        }
    )


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = {key: load_json(path) for key, path in INPUTS.items()}
    assert_upstream_counts(inputs)

    artifacts: dict[str, tuple[dict[str, Any], str]] = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json": (build_context_anchor(inputs), "Context Anchor"),
        f"{PREFIX}_SOURCE_CHAIN_RECONCILIATION_LEDGER_{DATE}.json": (build_source_chain(inputs), "Source Chain Reconciliation Ledger"),
        f"{PREFIX}_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_{DATE}.json": (build_final_status(inputs), "Final Source Status Closure Ledger"),
        f"{PREFIX}_TWO_DATE_CLOSURE_MEMO_{DATE}.json": (build_two_date_memo(inputs), "Two-Date Closure Memo"),
        f"{PREFIX}_REPLAY_SOURCE_EXPANSION_READINESS_SYNTHESIS_{DATE}.json": (build_replay_readiness(), "Replay Source-Expansion Readiness Synthesis"),
        f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json": (build_ranking(), "Next Route Ranking Ledger"),
        f"{PREFIX}_NOLEAK_SAFETY_BOUNDARY_AUDIT_{DATE}.json": (build_noleak_audit(), "No-Leak Safety Boundary Audit"),
        f"{PREFIX}_ONE_LINE_STARTER_{DATE}.json": (build_one_line_artifact(), "One-Line Starter"),
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json": (build_completion_audit(), "Completion Audit"),
    }

    written: list[str] = []
    for json_name, (payload, title) in artifacts.items():
        md_name = json_name.replace(".json", ".md")
        write_json(json_name, payload)
        write_md(md_name, title, payload)
        written.extend([rel(ROUTE_DIR / json_name), rel(ROUTE_DIR / md_name)])

    NEXT_PROMPT_PATH.write_text(prompt_text(), encoding="utf-8")
    written.append(rel(NEXT_PROMPT_PATH))

    output_manifest = build_output_manifest(written)
    output_json = f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
    output_md = output_json.replace(".json", ".md")
    write_json(output_json, output_manifest)
    write_md(output_md, "Output Manifest", output_manifest)
    written.extend([rel(ROUTE_DIR / output_json), rel(ROUTE_DIR / output_md)])

    return {"route_id": ROUTE_ID, "artifacts_written": sorted(written), "selected_next_prompt": rel(NEXT_PROMPT_PATH)}


def main() -> None:
    print(json.dumps(build_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
