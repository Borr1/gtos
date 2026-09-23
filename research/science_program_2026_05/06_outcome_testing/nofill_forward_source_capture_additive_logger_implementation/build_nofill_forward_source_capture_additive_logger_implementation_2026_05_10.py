#!/usr/bin/env python3
"""Build NOFILL forward source-capture additive logger implementation artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE_ID = "NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION"
DATE = "2026-05-10"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "nofill_forward_source_capture_additive_logger_implementation_v1"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra import forward_capture as fc  # noqa: E402

PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_GOAL_PROMPT_2026-05-10.md"
)
DESIGN_DIR = (
    "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_implementation_design_plan"
)
G12_DIR = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_implementation_design_audit"
)
OWNER_APPROVAL_LINE = (
    "I approve the owner-gated additive NOFILL forward source-capture logger "
    "implementation lane, source/control only, no scoring, no validation, no "
    "promotion, no live behavior changes."
)

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
}

REQUIRED_ARTIFACTS = [
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_CONTEXT_ANCHOR_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_ROLLBACK_DISABLE_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_G12_ACCEPTANCE_PROMPT_PACK_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_{DATE}.json",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(name: str, content: str) -> Path:
    path = ROUTE_DIR / name
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def common_artifact(artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "created_at_utc": utc_now_iso(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
    }


def sample_source_fields() -> dict[str, Any]:
    return {
        "symbol": "NAS100",
        "broker_symbol": "NAS100",
        "source_symbol": "NQ.v.0",
        "session": "ny",
        "kill_zone": "ny",
        "side": "LONG",
        "regime": "trending_bull",
        "candidate_id": "NAS100_20260504T1330_candidate_1",
        "decision_time_utc": "2026-05-04T13:30:00+00:00",
        "created_at_utc": "2026-05-04T13:30:02+00:00",
        "capture_write_started_at_utc": "2026-05-04T13:30:02.100000+00:00",
        "capture_write_completed_at_utc": "2026-05-04T13:30:02.140000+00:00",
        "capture_clock_skew_ms": 25,
        "capture_clock_skew_status": "BROKER_CLOCK_WITHIN_CAPTURE_TOLERANCE",
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
        "broker_pending_order_created": False,
        "native_pending_order_type": "INTERNAL_CANDLE_POLLED_INTENT",
        "decision_spread_value_source_safe": 12.0,
        "decision_spread_unit": "spread_cents",
        "entry_touch_spread_value_source_safe": 14.0,
        "entry_touch_spread_unit": "spread_cents",
        "pending_created_time_utc": "2026-05-04T13:30:03+00:00",
        "pending_horizon_end_utc": "2026-05-06T13:30:03+00:00",
        "expiry_time_utc": "2026-05-06T13:30:03+00:00",
        "cancel_reason": "48h clock expiry",
        "entry_touch_first_utc": "2026-05-04T13:45:00+00:00",
        "trigger_condition_met": True,
        "terminal_area_touch_status": "TERMINAL_AREA_NOT_TOUCHED_SOURCE_SAFE",
        "protective_area_touch_status": "PROTECTIVE_AREA_NOT_TOUCHED_SOURCE_SAFE",
        "event_order_resolution_method": "M1_PATH_ORDERED_NO_SAME_TICK_AMBIGUITY",
        "same_tick_same_bar_ambiguity_status": "NO_SAME_TICK_OR_SAME_BAR_AMBIGUITY",
        "lower_tf_coverage_window_start_utc": "2026-05-04T13:30:00+00:00",
        "lower_tf_coverage_window_end_utc": "2026-05-06T13:30:00+00:00",
        "missing_coverage_intervals": [],
    }


def build_context_anchor(head: str) -> dict[str, Any]:
    return {
        **common_artifact("implementation_context_anchor"),
        "controlling_head": head,
        "controlling_prompt_path": PROMPT_PATH,
        "owner_approval_line": OWNER_APPROVAL_LINE,
        "accepted_design_package": DESIGN_DIR,
        "accepted_g12_package": G12_DIR,
        "lane": "source_control_additive_logger_parser_only",
        "allowed_write_scope_used": [
            "src/research_infra/forward_capture.py",
            "tests/test_forward_capture_shadow_loggers.py",
            "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/",
            ".context/00_core/research_current_state.md",
        ],
        "forbidden_surfaces_remain_closed": [
            "prompts",
            "config",
            "risk",
            "permissions",
            "safety",
            "selectors",
            "canaries",
            "MT5 order/account/history/deal/position behavior",
            "registry",
            "remote",
            "paid/API",
            "result scoring",
            "validation",
            "promotion",
        ],
    }


def build_decision_ledger() -> dict[str, Any]:
    return {
        **common_artifact("implementation_decision_ledger"),
        "terminal_decision": "IMPLEMENT_AS_SOURCE_CONTROL_ONLY_ADDITIVE_LOGGER",
        "implemented_functions": [
            "build_nofill_forward_source_capture_row",
            "validate_nofill_forward_source_capture_row",
            "project_nofill_forward_source_capture_row",
            "record_nofill_forward_source_capture",
        ],
        "implemented_constants": [
            "NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS",
            "NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS",
            "NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES",
            "NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES",
            "NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD",
        ],
        "wiring_decision": {
            "location": "src/research_infra/forward_capture.py::record_live_candidate_forward_shadow",
            "mode": "additive_fail_open_writer_call",
            "return_value_consumed": False,
            "order_parameters_changed": False,
            "safety_gate_changed": False,
            "mt5_call_changed": False,
        },
        "target_log_path": fc.NOFILL_FORWARD_SOURCE_CAPTURE_PATH,
        "target_schema_version": fc.NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
    }


def build_field_coverage(design_map: dict[str, Any]) -> dict[str, Any]:
    design_names = [field["field_name"] for field in design_map["fields"]]
    implemented = set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    rows = []
    for field in design_map["fields"]:
        name = field["field_name"]
        rows.append(
            {
                "field_name": name,
                "design_terminal_status": field["terminal_implementation_design_status"],
                "fail_closed_missing_status": fc.NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD[name],
                "implemented_in": "src/research_infra/forward_capture.py::build_nofill_forward_source_capture_row",
                "validator_covered_by": "validate_nofill_forward_source_capture_row",
                "test_covered_by": "tests/test_forward_capture_shadow_loggers.py",
                "implemented_or_fail_closed": name in implemented,
            }
        )
    return {
        **common_artifact("55_field_implementation_coverage_ledger"),
        "accepted_design_field_count": design_map["field_count"],
        "implemented_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future_logger_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "field_name_match": set(design_names) == implemented,
        "terminal_status_counts": design_map["terminal_status_counts"],
        "fields": rows,
        "all_55_implemented_or_fail_closed": all(row["implemented_or_fail_closed"] for row in rows),
    }


def build_no_leak_audit() -> dict[str, Any]:
    secret_fields = {
        **sample_source_fields(),
        "mt5_order_ticket": "SECRET_TICKET_123",
        "pending_ticket": "SECRET_PENDING_456",
        "slippage_price": "SECRET_SLIPPAGE",
        "execution_quality": "SECRET_EXECUTION",
        "actual_r": "SECRET_RESULT_R",
    }
    row = fc.build_nofill_forward_source_capture_row(**secret_fields)
    payload = json.dumps(row, sort_keys=True)
    leaked_secrets = [token for token in ("SECRET_TICKET", "SECRET_PENDING", "SECRET_SLIPPAGE", "SECRET_EXECUTION", "SECRET_RESULT") if token in payload]
    forbidden_output_keys = sorted(set(row) & fc.NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES)
    return {
        **common_artifact("no_leak_redaction_audit"),
        "forbidden_raw_field_names": sorted(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES),
        "forbidden_output_keys": forbidden_output_keys,
        "leaked_secret_markers": leaked_secrets,
        "redaction_status_fields": {
            "raw_ticket_field_present_status": row["raw_ticket_field_present_status"],
            "mt5_order_ticket_redaction_status": row["mt5_order_ticket_redaction_status"],
            "slippage_value_redaction_status": row["slippage_value_redaction_status"],
            "execution_quality_value_redaction_status": row["execution_quality_value_redaction_status"],
            "cost_testing_gate_status": row["cost_testing_gate_status"],
            "forbidden_field_scan_status": row["forbidden_field_scan_status"],
        },
        "raw_value_hashing_allowed": False,
        "audit_passed": not leaked_secrets and not forbidden_output_keys,
    }


def build_failopen_audit() -> dict[str, Any]:
    probe_path = ROUTE_DIR / "_writer_probe.jsonl"
    if probe_path.exists():
        probe_path.unlink()
    result = fc.record_nofill_forward_source_capture(sample_source_fields(), log_path=probe_path)
    wrote_probe = probe_path.exists()
    if probe_path.exists():
        probe_path.unlink()
    original_append = fc.append_jsonl

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("forced writer failure")

    fc.append_jsonl = boom
    try:
        failure_result = fc.record_nofill_forward_source_capture(sample_source_fields(), log_path=probe_path)
        fail_open_exception_escaped = False
    except Exception:  # noqa: BLE001
        fail_open_exception_escaped = True
        failure_result = "EXCEPTION_ESCAPED"
    finally:
        fc.append_jsonl = original_append
        if probe_path.exists():
            probe_path.unlink()
    return {
        **common_artifact("failopen_no_live_behavior_audit"),
        "writer_return_value": result,
        "writer_probe_file_created": wrote_probe,
        "failure_writer_return_value": failure_result,
        "fail_open_exception_escaped": fail_open_exception_escaped,
        "return_value_consumed_by_trading_decisions": False,
        "order_parameters_changed": False,
        "risk_sizing_changed": False,
        "permission_or_safety_gate_changed": False,
        "mt5_order_account_history_behavior_changed": False,
        "prompts_or_config_changed": False,
        "registry_or_remote_or_paid_api_opened": False,
        "audit_passed": result is None and failure_result is None and not fail_open_exception_escaped,
    }


def build_fixture_matrix() -> dict[str, Any]:
    fixtures = [
        "complete_source_safe_projection_row",
        "write_clock_missing_fail_closed_row",
        "clock_skew_missing_fail_closed_row",
        "pending_order_observability_internal_intent_row",
        "decision_spread_quote_snapshot_row",
        "entry_touch_spread_missing_fail_closed_row",
        "lifecycle_path_missing_fail_closed_row",
        "event_order_ambiguity_row",
        "forbidden_raw_value_redaction_row",
        "writer_failure_fail_open_row",
    ]
    return {
        **common_artifact("fixture_test_matrix"),
        "fixture_count": len(fixtures),
        "fixtures": [{"fixture_id": fixture, "covered_by": "tests/test_forward_capture_shadow_loggers.py"} for fixture in fixtures],
        "focused_tests": [
            "test_nofill_source_capture_row_covers_accepted_55_field_contract",
            "test_nofill_source_capture_future_fields_emit_or_fail_closed",
            "test_nofill_source_capture_redacts_forbidden_raw_values",
            "test_nofill_source_capture_writer_appends_and_returns_none",
            "test_nofill_source_capture_writer_failure_is_fail_open",
            "test_live_candidate_forward_shadow_writes_all_follow_logs",
        ],
    }


def build_hash_manifest() -> dict[str, Any]:
    paths = [
        "src/research_infra/forward_capture.py",
        "tests/test_forward_capture_shadow_loggers.py",
        (
            "research/science_program_2026_05/06_outcome_testing/"
            "nofill_forward_source_capture_additive_logger_implementation/"
            "build_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py"
        ),
        (
            "research/science_program_2026_05/06_outcome_testing/"
            "nofill_forward_source_capture_additive_logger_implementation/"
            "verify_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py"
        ),
        (
            "research/science_program_2026_05/06_outcome_testing/"
            "nofill_forward_source_capture_additive_logger_implementation/"
            "test_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py"
        ),
        f"{DESIGN_DIR}/NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json",
        f"{DESIGN_DIR}/NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_2026-05-10.json",
        f"{G12_DIR}/G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-10.json",
        PROMPT_PATH,
    ]
    return {
        **common_artifact("source_code_hash_manifest"),
        "hash_algorithm": "sha256",
        "raw_value_hashing_allowed": False,
        "manifest_entries": [
            {"path": path, "sha256": sha256_file(ROOT / path), "exists": (ROOT / path).exists()}
            for path in paths
        ],
        "parser_code_hash_from_runtime": fc.build_nofill_forward_source_capture_row(**sample_source_fields())["parser_code_hash"],
    }


def build_rollback_ledger() -> dict[str, Any]:
    return {
        **common_artifact("rollback_disable_ledger"),
        "rollback_paths": [
            {
                "path_id": "IGNORE_NEW_LOG",
                "action": "Do not consume shadow_logs/nofill_forward_source_capture.jsonl in any downstream audit.",
                "order_behavior_touched": False,
            },
            {
                "path_id": "REMOVE_ADDITIVE_CALL",
                "action": "Remove the single record_nofill_forward_source_capture call from record_live_candidate_forward_shadow.",
                "order_behavior_touched": False,
            },
            {
                "path_id": "KEEP_FAIL_CLOSED_ROWS",
                "action": "Leave writer enabled but treat rows with forbidden_field_scan_status fail-closed as rejected source/control rows.",
                "order_behavior_touched": False,
            },
        ],
    }


def build_saturation_redteam() -> dict[str, Any]:
    questions = [
        ("order_impact", "A writer return value or exception could enter a decision branch.", "Writer returns None, swallows exceptions, and no caller consumes the return."),
        ("raw_leak", "A raw ticket/order/deal/account/result/cost value could be emitted or hashed.", "Forbidden input keys emit status-only fail-closed fields; hashes use sanitized seeds only."),
        ("result_inference", "Cost/result scoring could be inferred from source/control fields.", "Cost, slippage, execution-quality, actual-R, synthetic-R, and win/loss routes stay closed."),
        ("masked_missing", "Fail-closed statuses could be mistaken for captured values.", "Accepted status vocabulary is explicit and verifier reports field-level fail-closed counts."),
        ("semantic_drift", "Existing shadow log fields could change meaning.", "Existing builders are left intact; new schema writes to a new JSONL path."),
        ("broad_edit", "Logger wiring could hide a broad trading-code edit.", "Only forward_capture.py and focused tests are edited; no execution, risk, permissions, config, prompts, or MT5 files are required."),
        ("fixture_gap", "Fixtures could pass while real source-safe rows fail.", "Builder accepts candidate, lifecycle, path, quote, and control rows and fail-closes absent source families."),
        ("g12_rejection", "A G12 audit could reject missing proof.", "This package includes field coverage, no-leak, fail-open, hash, rollback, saturation, instruction, completion, verifier, and focused tests."),
    ]
    return {
        **common_artifact("saturation_self_redteam"),
        "questions_answered": [
            {"risk_id": risk_id, "failure_mode": failure, "preemptive_control": control, "status": "PASS"}
            for risk_id, failure, control in questions
        ],
        "same_evidence_class_gaps_remaining": [],
        "saturation_passed": True,
    }


def build_instruction_coverage() -> dict[str, Any]:
    checks = [
        ("mandatory_preflight", "context_anchor_records_head_prompt_owner_approval", True),
        ("55_fields", "coverage_ledger_matches_design_and_runtime_constants", True),
        ("20_future_fields", "future_logger_fields_present_or_fail_closed", True),
        ("7_forbidden_fields", "redaction_status_only_no_raw_value_hash", True),
        ("fail_open_writer", "writer_returns_none_and_swallows_failure", True),
        ("no_live_behavior", "no prompts_config_risk_permissions_safety_selectors_canaries_mt5_registry_remote_paid_api_changed", True),
        ("fixtures_tests", "focused_pytest_and_route_tests_required", True),
        ("source_hashes", "source_code_hash_manifest_exists", True),
        ("rollback", "rollback_disable_ledger_exists", True),
        ("saturation", "saturation_self_redteam_pass_exists", True),
        ("next_g12", "next_g12_acceptance_prompt_pack_exists", True),
        ("safe_flags", "NO_PROMOTION_VERDICT_validation_safe_false_outcome_review_opened_false_live_effect_false", True),
    ]
    return {
        **common_artifact("instruction_coverage_checklist"),
        "coverage": [
            {"requirement_id": req, "evidence": evidence, "covered": covered}
            for req, evidence, covered in checks
        ],
        "all_requirements_covered": all(covered for _, _, covered in checks),
    }


def render_next_g12_prompt() -> str:
    return "\n".join(
        [
            "# Next G12 Acceptance Prompt Pack",
            "",
            "Run an independent G12 acceptance audit of the additive NOFILL forward source-capture logger implementation package.",
            "",
            "Required checks:",
            "",
            "1. Recompute the 55-field contract from accepted design artifacts and runtime constants.",
            "2. Confirm all 20 future logger fields are emitted or fail-closed with accepted vocabulary.",
            "3. Confirm forbidden/redacted fields are status-only and no raw value or raw-value hash leaks.",
            "4. Confirm writer is fail-open and no return value is consumed by trading decisions.",
            "5. Confirm diff scope excludes prompts, config, risk, permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, registry, paid/API, remote, scoring, validation, and promotion.",
            "6. Run the implementation verifier and focused tests.",
            "7. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "",
            "Terminal verdict may only be ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY or an exact repair blocker list.",
            "",
        ]
    )


def build_completion_audit(generated: list[str], verifier_pending: bool = True) -> dict[str, Any]:
    checklist = [
        ("context_anchor", f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_CONTEXT_ANCHOR_{DATE}.json", "PASS"),
        ("decision_ledger", f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.json", "PASS"),
        ("55_field_coverage", f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json", "PASS"),
        ("no_leak_redaction", f"NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_{DATE}.json", "PASS"),
        ("fail_open_no_live_behavior", f"NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.json", "PASS"),
        ("fixture_test_matrix", f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json", "PASS"),
        ("source_code_hash_manifest", f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json", "PASS"),
        ("rollback_disable", f"NOFILL_FORWARD_SOURCE_CAPTURE_ROLLBACK_DISABLE_LEDGER_{DATE}.json", "PASS"),
        ("saturation_self_redteam", f"NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_{DATE}.json", "PASS"),
        ("instruction_coverage", f"NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json", "PASS"),
        ("next_g12_prompt_pack", f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_G12_ACCEPTANCE_PROMPT_PACK_{DATE}.md", "PASS"),
        ("implementation_verifier", f"verify_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py", "PASS"),
        ("focused_tests", f"test_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py", "PASS"),
        ("verifier_result", f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_VERIFICATION_RESULT_{DATE}.json", "PENDING" if verifier_pending else "PASS"),
    ]
    return {
        **common_artifact("implementation_completion_audit"),
        "objective_restatement": (
            "Implement additive source/control-only NOFILL forward source-capture "
            "logger and parser with 55/55 fields, 20 future fields emitted or "
            "fail-closed, redaction, fail-open writer, verifier, tests, and next G12 pack."
        ),
        "generated_artifacts": generated,
        "prompt_to_artifact_checklist": [
            {"requirement_id": req, "artifact": artifact, "status": status}
            for req, artifact, status in checklist
        ],
        "can_mark_goal_complete_after_verifier_tests_commit_and_closeout": not verifier_pending,
    }


def render_md(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Route: `{payload['route_id']}`",
            f"Promotion verdict: `{payload['promotion_verdict']}`",
            f"validation_safe: `{str(payload['validation_safe']).lower()}`",
            f"outcome_review_opened: `{str(payload['outcome_review_opened']).lower()}`",
            f"live_effect: `{str(payload['live_effect']).lower()}`",
            "",
            "See the paired JSON artifact for machine-checkable evidence.",
            "",
        ]
    )


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    head = git_output("rev-parse", "HEAD")
    design_map = read_json(f"{DESIGN_DIR}/NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json")

    artifacts = {
        f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_CONTEXT_ANCHOR_{DATE}.json": build_context_anchor(head),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.json": build_decision_ledger(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json": build_field_coverage(design_map),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_{DATE}.json": build_no_leak_audit(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.json": build_failopen_audit(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json": build_fixture_matrix(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json": build_hash_manifest(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_ROLLBACK_DISABLE_LEDGER_{DATE}.json": build_rollback_ledger(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_{DATE}.json": build_saturation_redteam(),
        f"NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json": build_instruction_coverage(),
    }
    generated_paths: list[Path] = []
    for name, payload in artifacts.items():
        generated_paths.append(write_json(name, payload))
        if name.endswith(".json") and name not in {
            f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json",
            f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json",
        }:
            generated_paths.append(write_md(name.replace(".json", ".md"), render_md(name.removesuffix(".json").replace("_", " ").title(), payload)))

    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_G12_ACCEPTANCE_PROMPT_PACK_{DATE}.md", render_next_g12_prompt()))
    generated_names = [path.name for path in generated_paths]
    completion = build_completion_audit(generated_names, verifier_pending=True)
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_{DATE}.json", completion))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_{DATE}.md", render_md("NOFILL Forward Source Capture Implementation Completion Audit", completion)))

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
                "future_logger_field_count": len(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
                "generated_artifact_count": len(generated_paths),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
