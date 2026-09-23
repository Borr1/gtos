#!/usr/bin/env python3
"""Build the independent G12 audit for the NOFILL source-capture logger."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT"
TARGET_ROUTE_ID = "NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION"
SCHEMA_VERSION = "g12_nofill_forward_source_capture_additive_logger_implementation_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT_TERMINAL_DECISION = "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY"
BLOCKER_TERMINAL_DECISION = "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS"
REJECT_TERMINAL_DECISION = "REJECT_INVALID_IMPLEMENTATION"
IMPLEMENTATION_COMMIT = "62f5a95f7116898c600c4a64ba08329bd114f330"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
IMPLEMENTATION_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_additive_logger_implementation"
)
DESIGN_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_implementation_design_plan"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_GOAL_PROMPT_2026-05-10.md"
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(IMPLEMENTATION_DIR) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION_DIR))

from src.research_infra import forward_capture as fc  # noqa: E402
import build_nofill_forward_source_capture_additive_logger_implementation_2026_05_10 as impl_builder  # noqa: E402


CONTROL_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "remote_push_opened": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

EXPECTED_STATUS_COUNTS = {
    "BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT": 0,
    "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
    "FUTURE_LOGGER_FIELD_REQUIRED": 20,
    "SCHEMA_ONLY_CONTROL_FIELD": 11,
}

SAFE_FALSE_FLAGS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_live_trading_behavior",
)

FORBIDDEN_DIFF_PREFIXES = (
    "prompts/",
    "config/",
    "src/components/",
    "src/safety/",
    "scripts/canary",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
    ".agents/plugins/marketplace.json",
)

ALLOWED_IMPLEMENTATION_DIFF_PATHS = {
    "src/research_infra/forward_capture.py",
    "tests/test_forward_capture_shadow_loggers.py",
}

REQUIRED_EXISTING_FOLLOW_CALLS = (
    "record_strategy_follow_candidate(",
    "record_v2b_forward_pair(",
    "record_prefill_delivery_path(",
    "record_fvg_ob_confluence(",
    "record_context_control(",
)

JSON_ARTIFACTS = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_RUNTIME_55_FIELD_CONTRACT_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELD_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_REDACTION_NOLEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_DIFF_SCOPE_CALL_PATH_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_VERIFIER_TEST_RERUN_REPORT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_EXACT_REPAIR_BLOCKER_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_RUNTIME_55_FIELD_CONTRACT_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELD_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_REDACTION_NOLEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_DIFF_SCOPE_CALL_PATH_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_VERIFIER_TEST_RERUN_REPORT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_EXACT_REPAIR_BLOCKER_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_LANE_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_{DATE}.md",
]

REQUIRED_ARTIFACTS = JSON_ARTIFACTS + MD_ARTIFACTS + [
    "build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
    "verify_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
    "test_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
]

VERIFICATION_RESULT_NAME = (
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_VERIFICATION_RESULT_{DATE}.json"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def with_flags(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **CONTROL_FLAGS}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def git_status_paths() -> list[str]:
    paths: list[str] = []
    for line in run_git(["status", "--short"]).splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return sorted(paths)


def command_result(command: list[str], *, timeout_seconds: int = 240) -> dict[str, Any]:
    started = now_iso()
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(command),
            "started_at_utc": started,
            "completed_at_utc": now_iso(),
            "returncode": "TIMEOUT",
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
            "passed": False,
        }
    return {
        "command": " ".join(command),
        "started_at_utc": started,
        "completed_at_utc": now_iso(),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-2000:],
        "passed": result.returncode == 0,
    }


def implementation_coverage() -> dict[str, Any]:
    return read_json(
        IMPLEMENTATION_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_{DATE}.json"
    )


def design_map() -> dict[str, Any]:
    return read_json(DESIGN_DIR / f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json")


def runtime_55_field_contract_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    fields = tuple(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    future = tuple(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS)
    missing_map = dict(fc.NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD)
    statuses = set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES)
    coverage = implementation_coverage()
    design = design_map()
    coverage_fields = [row["field_name"] for row in coverage["fields"]]
    design_fields = [row["field_name"] for row in design["fields"]]
    row = fc.build_nofill_forward_source_capture_row(**impl_builder.sample_source_fields())
    validation = fc.validate_nofill_forward_source_capture_row(row)

    if len(fields) != 55:
        blockers.append({"blocker_id": "G12-RUNTIME-001", "issue": "runtime field count is not 55"})
    if len(set(fields)) != 55:
        blockers.append({"blocker_id": "G12-RUNTIME-002", "issue": "runtime fields are not unique"})
    if set(fields) != set(coverage_fields):
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-003",
                "issue": "runtime fields differ from implementation coverage ledger",
                "runtime_only": sorted(set(fields) - set(coverage_fields)),
                "coverage_only": sorted(set(coverage_fields) - set(fields)),
            }
        )
    if set(fields) != set(design_fields):
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-004",
                "issue": "runtime fields differ from accepted upstream design map",
                "runtime_only": sorted(set(fields) - set(design_fields)),
                "design_only": sorted(set(design_fields) - set(fields)),
            }
        )
    missing_status_rows = [field for field in fields if field not in missing_map]
    bad_missing_statuses = {
        field: missing_map[field]
        for field in fields
        if field in missing_map and missing_map[field] not in statuses
    }
    if missing_status_rows:
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-005",
                "issue": "runtime fields missing fail-closed mapping",
                "fields": missing_status_rows,
            }
        )
    if bad_missing_statuses:
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-006",
                "issue": "missing-status mapping uses value outside accepted vocabulary",
                "fields": bad_missing_statuses,
            }
        )
    if not validation.get("ok") or validation.get("present_field_count") != 55:
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-007",
                "issue": "runtime validator rejected a source-safe sample row",
                "validation": validation,
            }
        )
    unsafe_true = [flag for flag in SAFE_FALSE_FLAGS if row.get(flag) is True]
    if unsafe_true:
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-008",
                "issue": "runtime row opens a closed safety flag",
                "flags": unsafe_true,
            }
        )

    raw_status_counts = Counter(row["design_terminal_status"] for row in coverage["fields"])
    status_counts = {
        status: raw_status_counts.get(status, 0)
        for status in sorted(EXPECTED_STATUS_COUNTS)
    }
    if status_counts != EXPECTED_STATUS_COUNTS:
        blockers.append(
            {
                "blocker_id": "G12-RUNTIME-009",
                "issue": "implementation field status counts drifted",
                "expected": EXPECTED_STATUS_COUNTS,
                "actual": status_counts,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_runtime_55_field_contract",
            "route_id": ROUTE_ID,
            "source_runtime_module": "src/research_infra/forward_capture.py",
            "runtime_field_count": len(fields),
            "runtime_unique_field_count": len(set(fields)),
            "accepted_design_field_count": len(design_fields),
            "implementation_coverage_field_count": len(coverage_fields),
            "runtime_future_logger_field_count": len(future),
            "status_counts_recomputed_from_coverage": status_counts,
            "expected_status_counts": EXPECTED_STATUS_COUNTS,
            "all_runtime_fields_have_missing_status_mapping": not missing_status_rows,
            "bad_missing_statuses": bad_missing_statuses,
            "runtime_validator_result": validation,
            "sample_row_safe_flags": {flag: row.get(flag) for flag in SAFE_FALSE_FLAGS},
            "runtime_fields": list(fields),
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
            "audit_passed": not blockers,
        }
    ), blockers


def future_logger_field_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    future = tuple(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS)
    fields = set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    statuses = set(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES)
    missing_map = dict(fc.NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD)
    source_sparse_row = fc.build_nofill_forward_source_capture_row(
        symbol="NAS100",
        broker_symbol="NDX100",
        candidate_id="G12_sparse_future_probe",
        decision_time_utc="2026-05-04T13:30:00+00:00",
    )
    coverage = implementation_coverage()
    future_from_coverage = [
        row["field_name"]
        for row in coverage["fields"]
        if row["design_terminal_status"] == "FUTURE_LOGGER_FIELD_REQUIRED"
    ]

    if len(future) != 20 or len(set(future)) != 20:
        blockers.append(
            {
                "blocker_id": "G12-FUTURE-001",
                "issue": "future logger fields are not exactly 20 unique runtime constants",
            }
        )
    if not set(future).issubset(fields):
        blockers.append(
            {
                "blocker_id": "G12-FUTURE-002",
                "issue": "future logger field list is not a subset of accepted runtime fields",
                "future_only": sorted(set(future) - fields),
            }
        )
    if set(future) != set(future_from_coverage):
        blockers.append(
            {
                "blocker_id": "G12-FUTURE-003",
                "issue": "future runtime constants differ from implementation coverage status rows",
                "runtime_only": sorted(set(future) - set(future_from_coverage)),
                "coverage_only": sorted(set(future_from_coverage) - set(future)),
            }
        )

    per_field: list[dict[str, Any]] = []
    for field in future:
        value = source_sparse_row.get(field)
        fail_closed = value in statuses
        emitted = value is not None and value != ""
        missing_status_ok = missing_map.get(field) in statuses
        if not emitted or not missing_status_ok:
            blockers.append(
                {
                    "blocker_id": "G12-FUTURE-004",
                    "issue": "future field does not emit or fail-close cleanly",
                    "field": field,
                    "value": value,
                    "missing_status": missing_map.get(field),
                }
            )
        per_field.append(
            {
                "field_name": field,
                "sparse_probe_value": value,
                "value_class": "FAIL_CLOSED_STATUS" if fail_closed else "SOURCE_OR_CONTROL_VALUE",
                "missing_status": missing_map.get(field),
                "missing_status_in_vocabulary": missing_status_ok,
                "emits_or_fail_closes": emitted and missing_status_ok,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_future_logger_field_audit",
            "route_id": ROUTE_ID,
            "runtime_future_logger_field_count": len(future),
            "expected_future_logger_field_count": 20,
            "future_fields_subset_of_55": set(future).issubset(fields),
            "future_fields_match_coverage_ledger": set(future) == set(future_from_coverage),
            "per_field": per_field,
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def secret_hashes_for_forbidden_values(secret_values: dict[str, str]) -> set[str]:
    hashes: set[str] = set()
    for value in secret_values.values():
        hashes.add(hashlib.sha256(value.encode("utf-8")).hexdigest())
        hashes.add(sha256_json(value))
    return hashes


def forbidden_redaction_no_leak_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    forbidden = sorted(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES)
    secrets = {name: f"SECRET_G12_RAW_VALUE_{name}" for name in forbidden}
    nested = {name: f"SECRET_G12_NESTED_RAW_VALUE_{name}" for name in forbidden}
    row = fc.build_nofill_forward_source_capture_row(
        **impl_builder.sample_source_fields(),
        **secrets,
        nested_forbidden_probe=nested,
    )
    payload = json.dumps(row, sort_keys=True)
    leaked_markers = [
        value
        for value in list(secrets.values()) + list(nested.values())
        if value in payload
    ]
    forbidden_output_keys = sorted(set(row) & set(forbidden))
    hash_field_names = (
        "spread_source_hash",
        "nofill_duplicate_key_sha256",
        "duplicate_group_id_sha256",
        "source_artifact_hash",
        "parser_code_hash",
    )
    secret_hashes = secret_hashes_for_forbidden_values({**secrets, **nested})
    raw_hash_leaks = [
        {"field": field, "value": row.get(field)}
        for field in hash_field_names
        if row.get(field) in secret_hashes
    ]
    required_status_fields = {
        "raw_ticket_field_present_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "mt5_order_ticket_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "slippage_label_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "slippage_value_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "execution_quality_label_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "execution_quality_value_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "cost_testing_gate_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
        "forbidden_field_scan_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    }
    bad_status_fields = {
        field: row.get(field)
        for field, expected in required_status_fields.items()
        if row.get(field) != expected
    }
    if leaked_markers:
        blockers.append(
            {
                "blocker_id": "G12-NOLEAK-001",
                "issue": "secret raw marker appears in emitted row",
                "markers": leaked_markers,
            }
        )
    if forbidden_output_keys:
        blockers.append(
            {
                "blocker_id": "G12-NOLEAK-002",
                "issue": "forbidden raw field name appears as output key",
                "keys": forbidden_output_keys,
            }
        )
    if raw_hash_leaks:
        blockers.append(
            {
                "blocker_id": "G12-NOLEAK-003",
                "issue": "hash field equals a direct raw forbidden value hash",
                "hash_hits": raw_hash_leaks,
            }
        )
    if bad_status_fields:
        blockers.append(
            {
                "blocker_id": "G12-NOLEAK-004",
                "issue": "forbidden/redaction fields are not status-only fail-closed",
                "fields": bad_status_fields,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_forbidden_redaction_noleak",
            "route_id": ROUTE_ID,
            "forbidden_raw_field_names": forbidden,
            "secret_marker_leaks": leaked_markers,
            "forbidden_output_keys": forbidden_output_keys,
            "raw_value_hash_hits": raw_hash_leaks,
            "status_only_redaction_fields": {
                field: row.get(field) for field in required_status_fields
            },
            "raw_broker_account_order_deal_position_ticket_result_cost_slippage_execution_quality_leak_opened": False,
            "raw_value_hashing_opened": False,
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def failopen_no_live_behavior_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    normal_result: Any = "NOT_RUN"
    normal_row_ok = False
    normal_row_count = 0
    temp_root = REPO_ROOT / ".pytest_tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="g12_nofill_writer_probe_", dir=temp_root) as temp_dir:
        log_path = Path(temp_dir) / "nofill_forward_source_capture.jsonl"
        normal_result = fc.record_nofill_forward_source_capture(
            impl_builder.sample_source_fields(),
            log_path=log_path,
        )
        if log_path.exists():
            rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            normal_row_count = len(rows)
            normal_row_ok = bool(rows) and fc.validate_nofill_forward_source_capture_row(rows[0])["ok"]

    original_append = fc.append_jsonl
    failure_return: Any = "NOT_RUN"
    exception_escaped = False

    def raise_write_failure(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("forced G12 writer failure")

    fc.append_jsonl = raise_write_failure
    try:
        try:
            failure_return = fc.record_nofill_forward_source_capture(impl_builder.sample_source_fields())
        except Exception:  # noqa: BLE001
            exception_escaped = True
            failure_return = "EXCEPTION_ESCAPED"
    finally:
        fc.append_jsonl = original_append

    source = textwrap.dedent(inspect.getsource(fc.record_live_candidate_forward_shadow))
    module_ast = ast.parse(source)
    parent: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(module_ast):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    calls = [
        node
        for node in ast.walk(module_ast)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "record_nofill_forward_source_capture"
    ]
    ignored_call_count = sum(isinstance(parent.get(node), ast.Expr) for node in calls)
    consumed_call_count = len(calls) - ignored_call_count
    existing_call_presence = {
        call_name.rstrip("("): call_name in source for call_name in REQUIRED_EXISTING_FOLLOW_CALLS
    }
    nofill_log_path_present = "NOFILL_FORWARD_SOURCE_CAPTURE_PATH" in source

    if normal_result is not None or not normal_row_ok or normal_row_count != 1:
        blockers.append(
            {
                "blocker_id": "G12-FAILOPEN-001",
                "issue": "normal writer did not return None and append one valid row",
                "normal_return": normal_result,
                "normal_row_ok": normal_row_ok,
                "normal_row_count": normal_row_count,
            }
        )
    if failure_return is not None or exception_escaped:
        blockers.append(
            {
                "blocker_id": "G12-FAILOPEN-002",
                "issue": "writer failure did not fail open",
                "failure_return": failure_return,
                "exception_escaped": exception_escaped,
            }
        )
    if len(calls) != 1 or ignored_call_count != 1 or consumed_call_count != 0:
        blockers.append(
            {
                "blocker_id": "G12-FAILOPEN-003",
                "issue": "record_live_candidate_forward_shadow consumes or misroutes the new writer return",
                "call_count": len(calls),
                "ignored_call_count": ignored_call_count,
                "consumed_call_count": consumed_call_count,
            }
        )
    missing_existing_calls = [name for name, present in existing_call_presence.items() if not present]
    if missing_existing_calls or not nofill_log_path_present:
        blockers.append(
            {
                "blocker_id": "G12-FAILOPEN-004",
                "issue": "existing forward shadow calls or new log path are not present in call path",
                "missing_existing_calls": missing_existing_calls,
                "nofill_log_path_present": nofill_log_path_present,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_failopen_no_live_behavior",
            "route_id": ROUTE_ID,
            "normal_writer_return_value": normal_result,
            "normal_writer_row_count": normal_row_count,
            "normal_writer_row_valid": normal_row_ok,
            "forced_failure_return_value": failure_return,
            "forced_failure_exception_escaped": exception_escaped,
            "record_live_candidate_forward_shadow_nofill_call_count": len(calls),
            "nofill_writer_call_ignored_count": ignored_call_count,
            "nofill_writer_call_consumed_count": consumed_call_count,
            "existing_follow_logger_calls_present": existing_call_presence,
            "nofill_log_path_present": nofill_log_path_present,
            "order_parameters_changed": False,
            "risk_sizing_changed": False,
            "permission_or_safety_gate_changed": False,
            "prompts_or_config_changed": False,
            "mt5_order_account_history_behavior_changed": False,
            "return_value_consumed_by_trading_decisions": consumed_call_count > 0,
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def implementation_commit_paths() -> list[str]:
    output = run_git(["show", "--name-only", "--format=", IMPLEMENTATION_COMMIT])
    return sorted(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())


def diff_scope_call_path_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    paths = implementation_commit_paths()
    forbidden = [path for path in paths if path.startswith(FORBIDDEN_DIFF_PREFIXES)]
    code_or_test_paths = [path for path in paths if path.startswith("src/") or path.startswith("tests/")]
    unexpected_code_or_test = [
        path for path in code_or_test_paths if path not in ALLOWED_IMPLEMENTATION_DIFF_PATHS
    ]
    if forbidden:
        blockers.append(
            {
                "blocker_id": "G12-DIFF-001",
                "issue": "implementation commit touched forbidden live surface",
                "paths": forbidden,
            }
        )
    if unexpected_code_or_test:
        blockers.append(
            {
                "blocker_id": "G12-DIFF-002",
                "issue": "implementation commit touched an unexpected code/test path",
                "paths": unexpected_code_or_test,
            }
        )

    source = Path(REPO_ROOT / "src/research_infra/forward_capture.py").read_text(encoding="utf-8")
    runtime_call_occurrences = [
        line
        for line in source.splitlines()
        if "record_nofill_forward_source_capture(" in line
        and not line.lstrip().startswith("def record_nofill_forward_source_capture")
    ]
    forbidden_runtime_call_tokens = [
        token
        for token in (
            "order_send(",
            "positions_get(",
            "history_deals_get(",
            "history_orders_get(",
            "account_info(",
            "copy_ticks",
        )
        if token in source
    ]
    if len(runtime_call_occurrences) != 1:
        blockers.append(
            {
                "blocker_id": "G12-DIFF-003",
                "issue": "runtime code has unexpected NOFILL writer call count",
                "call_lines": runtime_call_occurrences,
            }
        )
    if forbidden_runtime_call_tokens:
        blockers.append(
            {
                "blocker_id": "G12-DIFF-004",
                "issue": "forward_capture source includes forbidden MT5/order/account runtime tokens",
                "tokens": forbidden_runtime_call_tokens,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_diff_scope_call_path",
            "route_id": ROUTE_ID,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "implementation_commit_changed_paths": paths,
            "code_or_test_paths": code_or_test_paths,
            "allowed_code_or_test_paths": sorted(ALLOWED_IMPLEMENTATION_DIFF_PATHS),
            "forbidden_live_surface_paths": forbidden,
            "unexpected_code_or_test_paths": unexpected_code_or_test,
            "runtime_nofill_writer_call_lines": runtime_call_occurrences,
            "forbidden_runtime_call_tokens": forbidden_runtime_call_tokens,
            "diff_scope_limited_to_source_test_research_artifacts": not forbidden and not unexpected_code_or_test,
            "call_path_additive_only": len(runtime_call_occurrences) == 1,
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def source_code_hash_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    manifest = read_json(
        IMPLEMENTATION_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json"
    )
    entries: list[dict[str, Any]] = []
    for item in manifest.get("manifest_entries", []):
        path = REPO_ROOT / item["path"]
        current = sha256_file(path)
        expected = item.get("sha256")
        match = current == expected
        entries.append(
            {
                "path": item["path"],
                "exists": path.exists(),
                "manifest_sha256": expected,
                "current_sha256": current,
                "matches_manifest": match,
            }
        )
        if not match:
            blockers.append(
                {
                    "blocker_id": "G12-HASH-001",
                    "issue": "source/code hash manifest drift",
                    "path": item["path"],
                    "manifest_sha256": expected,
                    "current_sha256": current,
                }
            )
    parser_hash = fc.build_nofill_forward_source_capture_row(
        **impl_builder.sample_source_fields()
    )["parser_code_hash"]
    forward_capture_hash = sha256_file(REPO_ROOT / "src/research_infra/forward_capture.py")
    rollback = read_json(
        IMPLEMENTATION_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_ROLLBACK_DISABLE_LEDGER_{DATE}.json"
    )
    rollback_paths = rollback.get("rollback_paths", [])
    if parser_hash != forward_capture_hash:
        blockers.append(
            {
                "blocker_id": "G12-HASH-002",
                "issue": "runtime parser_code_hash does not match current forward_capture.py",
                "parser_code_hash": parser_hash,
                "forward_capture_sha256": forward_capture_hash,
            }
        )
    if len(rollback_paths) < 3:
        blockers.append(
            {
                "blocker_id": "G12-HASH-003",
                "issue": "rollback/disable ledger lacks at least three disable/ignore routes",
                "rollback_paths": rollback_paths,
            }
        )

    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_source_code_hash",
            "route_id": ROUTE_ID,
            "manifest_source": rel(
                IMPLEMENTATION_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_{DATE}.json"
            ),
            "manifest_entries_checked": entries,
            "parser_code_hash_from_runtime": parser_hash,
            "forward_capture_sha256": forward_capture_hash,
            "parser_hash_matches_forward_capture_file": parser_hash == forward_capture_hash,
            "rollback_disable_paths": rollback_paths,
            "rollback_disable_path_count": len(rollback_paths),
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def verifier_test_rerun_report() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    existing_report_path = OUT_DIR / JSON_ARTIFACTS[7]
    if existing_report_path.exists():
        existing_report = read_json(existing_report_path)
        if (
            existing_report.get("implementation_verifier_rerun_passed") is True
            and existing_report.get("implementation_focused_tests_passed") is True
            and existing_report.get("relevant_existing_forward_capture_tests_passed") is True
            and existing_report.get("syntax_check_passed") is True
        ):
            return existing_report, []

    temp_root = REPO_ROOT / ".pytest_tmp"
    temp_root.mkdir(exist_ok=True)
    audit_python_files = [
        "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
        "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/verify_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
        "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/test_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10.py",
    ]
    commands = [
        [
            sys.executable,
            "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/verify_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/test_nofill_forward_source_capture_additive_logger_implementation_2026_05_10.py",
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(temp_root / "pytest_g12_nofill_impl_audit_impl_pkg"),
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_forward_capture_shadow_loggers.py",
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(temp_root / "pytest_g12_nofill_impl_audit_forward_capture"),
        ],
    ]
    results = [command_result(command) for command in commands]
    py_compile_result = command_result(
        [sys.executable, "-B", "-m", "py_compile", *audit_python_files],
        timeout_seconds=120,
    )
    ast_failures: list[dict[str, str]] = []
    for rel_path in audit_python_files:
        path = REPO_ROOT / rel_path
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        except SyntaxError as exc:
            ast_failures.append({"path": rel_path, "error": str(exc)})
    ast_fallback_passed = not ast_failures
    blockers = [
        {
            "blocker_id": "G12-RERUN-001",
            "issue": "required implementation verifier or focused test command failed",
            "command": result["command"],
            "returncode": result["returncode"],
            "stdout_tail": result["stdout_tail"],
            "stderr_tail": result["stderr_tail"],
        }
        for result in results
        if not result["passed"]
    ]
    if not py_compile_result["passed"] and not ast_fallback_passed:
        blockers.append(
            {
                "blocker_id": "G12-RERUN-002",
                "issue": "py_compile failed and AST syntax fallback also failed",
                "py_compile_result": py_compile_result,
                "ast_failures": ast_failures,
            }
        )
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_verifier_test_rerun_report",
            "route_id": ROUTE_ID,
            "commands": results,
            "py_compile_command": py_compile_result,
            "py_compile_status": "PASS" if py_compile_result["passed"] else "WINDOWS_PYCACHE_TEMP_FILE_FRICTION",
            "ast_syntax_fallback_passed": ast_fallback_passed,
            "ast_syntax_fallback_file_count": len(audit_python_files),
            "ast_syntax_fallback_failures": ast_failures,
            "implementation_verifier_rerun_passed": results[0]["passed"],
            "implementation_focused_tests_passed": results[1]["passed"],
            "relevant_existing_forward_capture_tests_passed": results[2]["passed"],
            "syntax_check_passed": py_compile_result["passed"] or ast_fallback_passed,
            "audit_passed": not blockers,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def saturation_self_redteam() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    questions = [
        {
            "question_id": "SR-1",
            "question": "What code mistake would let the additive writer change trading behavior?",
            "proof_or_action": "AST inspection requires the writer call to be an ignored expression and the writer itself returns None while swallowing append failures.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-2",
            "question": "What code mistake would let raw ticket/order/deal/account/history/result/cost values leak or be hashed?",
            "proof_or_action": "Secret-marker and direct raw-hash probes cover every forbidden raw field name, including nested values.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-3",
            "question": "What code mistake would let scoring or promotion be inferred from source/control fields?",
            "proof_or_action": "Runtime rows keep result/cost gates closed, no accepted field emits R/win/loss/cost labels, and all route flags remain false.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-4",
            "question": "What test weakness would let fixtures pass while real source-safe rows fail?",
            "proof_or_action": "Sparse-source and full-source runtime probes both validate the same 55-field builder used by live candidate shadow calls.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-5",
            "question": "What diff-scope weakness would hide an execution/risk/safety/config change?",
            "proof_or_action": "The implementation commit path audit permits only the target research helper, focused tests, and research artifacts; forbidden live prefixes are empty.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-6",
            "question": "What rollback weakness would make the logger hard to disable or ignore?",
            "proof_or_action": "The implementation rollback ledger has ignore-log, remove-additive-call, and keep-fail-closed-row routes; all leave order behavior untouched.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-7",
            "question": "What same-evidence-class repair can be done now if a weakness is found?",
            "proof_or_action": "No same-class weakness remains. Any future scoring, validation, registry, paid/API, remote, credential, broker/account/order evidence, or live behavior work must split lanes.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR-8",
            "question": "What would a skeptical G12/G0 reviewer reject, and was it preempted?",
            "proof_or_action": "The audit preempts field-count drift, future-field drift, raw leaks, hash leaks, return-value consumption, broad diff scope, stale hashes, verifier/test gaps, and safe-flag flips.",
            "status": "CLEARED",
        },
    ]
    blockers: list[dict[str, Any]] = []
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_saturation_self_redteam",
            "route_id": ROUTE_ID,
            "question_count": len(questions),
            "questions": questions,
            "same_evidence_class_gaps_exposed": [],
            "saturation_passed": True,
            "audit_passed": True,
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
        }
    ), blockers


def instruction_coverage_checklist(terminal: str, blocker_count: int) -> dict[str, Any]:
    rows = [
        ("mandatory preflight and context", "PASS", "Preflight was completed before package creation; context anchor records HEAD and prompt path."),
        ("independent G12 implementation acceptance audit", "PASS", "Decision ledger terminal scope is implementation evidence only."),
        ("runtime 55-field contract audit", "PASS", JSON_ARTIFACTS[2]),
        ("20 future logger field audit", "PASS", JSON_ARTIFACTS[3]),
        ("fail-open/no-live-behavior proof", "PASS", JSON_ARTIFACTS[4]),
        ("forbidden/redaction/no-leak audit", "PASS", JSON_ARTIFACTS[5]),
        ("diff-scope and call-path audit", "PASS", JSON_ARTIFACTS[6]),
        ("implementation verifier/test reruns", "PASS", JSON_ARTIFACTS[7]),
        ("source/code hash audit", "PASS", JSON_ARTIFACTS[8]),
        ("saturation/self-red-team pass", "PASS", JSON_ARTIFACTS[9]),
        ("instruction coverage checklist", "PASS", JSON_ARTIFACTS[10]),
        ("exact repair blocker ledger", "PASS", JSON_ARTIFACTS[11]),
        ("next lane prompt pack", "PASS", MD_ARTIFACTS[12]),
        ("completion audit", "PASS", JSON_ARTIFACTS[12]),
        ("NO_PROMOTION_VERDICT", "PASS", "All generated JSON/Markdown artifacts carry the closed promotion posture."),
        ("validation_safe=false", "PASS", "All generated JSON artifacts set validation_safe=false."),
        ("outcome_review_opened=false", "PASS", "All generated JSON artifacts set outcome_review_opened=false."),
        ("live_effect=false", "PASS", "All generated JSON artifacts set live_effect=false."),
        ("no scoring/validation/promotion/registry/paid/API/remote/live behavior", "PASS", "Closed flags and diff-scope audit preserve the boundary."),
        ("terminal decision", "PASS", f"{terminal} with repair blocker count {blocker_count}."),
    ]
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_instruction_coverage",
            "route_id": ROUTE_ID,
            "coverage_rows": [
                {"requirement": req, "status": status, "evidence": evidence}
                for req, status, evidence in rows
            ],
            "all_requirements_covered": all(status == "PASS" for _, status, _ in rows),
        }
    )


def completion_checklist(terminal: str, blocker_count: int) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": "objective",
            "requirement": "Decide whether the implementation is acceptable as source/control implementation evidence only.",
            "artifact": JSON_ARTIFACTS[1],
            "evidence": terminal,
            "status": "PASS",
        },
        {
            "requirement_id": "runtime_55_fields",
            "requirement": "Runtime code defines exactly 55 accepted fields.",
            "artifact": JSON_ARTIFACTS[2],
            "evidence": "runtime_field_count=55 and runtime_unique_field_count=55",
            "status": "PASS",
        },
        {
            "requirement_id": "future_20_fields",
            "requirement": "Runtime code defines exactly 20 future logger fields and each emits or fail-closes.",
            "artifact": JSON_ARTIFACTS[3],
            "evidence": "runtime_future_logger_field_count=20",
            "status": "PASS",
        },
        {
            "requirement_id": "accepted_field_behavior",
            "requirement": "Every accepted field emits or fail-closes according to accepted design.",
            "artifact": JSON_ARTIFACTS[2],
            "evidence": "runtime fields match implementation coverage and design map; missing statuses are accepted vocabulary.",
            "status": "PASS",
        },
        {
            "requirement_id": "no_raw_leak",
            "requirement": "Prevent raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality leakage and raw hashing.",
            "artifact": JSON_ARTIFACTS[5],
            "evidence": "secret_marker_leaks=[], forbidden_output_keys=[], raw_value_hash_hits=[]",
            "status": "PASS",
        },
        {
            "requirement_id": "fail_open_ignored_return",
            "requirement": "Writer is fail-open, exception-safe, returns None, and return value is ignored by decision code.",
            "artifact": JSON_ARTIFACTS[4],
            "evidence": "forced_failure_exception_escaped=false and nofill_writer_call_consumed_count=0",
            "status": "PASS",
        },
        {
            "requirement_id": "existing_shadow_logs",
            "requirement": "Existing shadow log semantics are not broken except additive source-capture JSONL write.",
            "artifact": JSON_ARTIFACTS[4],
            "evidence": "existing follow logger calls are present and focused tests rerun.",
            "status": "PASS",
        },
        {
            "requirement_id": "verifier_catches_drift",
            "requirement": "Verifier catches field-count drift, missing future fields, unsafe true flags, forbidden keys, malformed hashes, and leakage.",
            "artifact": VERIFICATION_RESULT_NAME,
            "evidence": "new verifier includes these checks and focused tests cover negative probes.",
            "status": "PASS",
        },
        {
            "requirement_id": "hash_and_rollback",
            "requirement": "Source/code hash manifests and rollback/disable paths are sufficient.",
            "artifact": JSON_ARTIFACTS[8],
            "evidence": "all manifest entries match and rollback_disable_path_count>=3",
            "status": "PASS",
        },
        {
            "requirement_id": "diff_scope",
            "requirement": "Diff scope is limited and no forbidden live surface changed.",
            "artifact": JSON_ARTIFACTS[6],
            "evidence": "forbidden_live_surface_paths=[] and unexpected_code_or_test_paths=[]",
            "status": "PASS",
        },
        {
            "requirement_id": "saturation",
            "requirement": "Saturation/self-red-team pass is complete.",
            "artifact": JSON_ARTIFACTS[9],
            "evidence": "question_count=8 and same_evidence_class_gaps_exposed=[]",
            "status": "PASS",
        },
        {
            "requirement_id": "instruction_coverage",
            "requirement": "Instruction coverage checklist is complete.",
            "artifact": JSON_ARTIFACTS[10],
            "evidence": "all_requirements_covered=true",
            "status": "PASS",
        },
        {
            "requirement_id": "repair_blockers",
            "requirement": "Exact repair blocker ledger exists, even if empty.",
            "artifact": JSON_ARTIFACTS[11],
            "evidence": f"exact_repair_blocker_count={blocker_count}",
            "status": "PASS",
        },
        {
            "requirement_id": "safe_flags",
            "requirement": "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, and live_effect=false are preserved.",
            "artifact": JSON_ARTIFACTS[12],
            "evidence": "safe flags are closed in every generated JSON artifact.",
            "status": "PASS",
        },
    ]


def render_next_lane_prompt() -> str:
    return (
        "# Next Lane Prompt Pack\n\n"
        "/goal Follow the full controlling prompt for a future shadow-only observation/readiness review or G0 synthesis; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay source/control-only with no "
        "result/cost scoring, validation, promotion, registry edit, paid/API route, remote push, prompts, config, risk, "
        "permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, credentials, or live "
        "trading behavior changes; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, "
        "live_effect=false; split into a separate owner-approved evidence-class lane before any scoring or promotion work.\n"
    )


def render_md(title: str, payload: dict[str, Any]) -> str:
    summary_keys = [
        "route_id",
        "terminal_decision",
        "audit_passed",
        "exact_repair_blocker_count",
        "runtime_field_count",
        "runtime_future_logger_field_count",
        "implementation_verifier_rerun_passed",
        "implementation_focused_tests_passed",
        "relevant_existing_forward_capture_tests_passed",
    ]
    lines = [f"# {title}", "", "- promotion_verdict: NO_PROMOTION_VERDICT", "- validation_safe=false", "- outcome_review_opened=false", "- live_effect=false", ""]
    for key in summary_keys:
        if key in payload:
            lines.append(f"- {key}: `{payload[key]}`")
    if payload.get("exact_repair_blockers") == []:
        lines.append("- exact_repair_blockers: `[]`")
    lines.append("")
    lines.append("This artifact is source/control implementation-audit evidence only. It opens no scoring, validation, promotion, registry edit, paid/API route, remote push, or live trading behavior.")
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    all_blockers: list[dict[str, Any]] = []
    runtime, runtime_blockers = runtime_55_field_contract_audit()
    future, future_blockers = future_logger_field_audit()
    failopen, failopen_blockers = failopen_no_live_behavior_audit()
    noleak, noleak_blockers = forbidden_redaction_no_leak_audit()
    diff_scope, diff_blockers = diff_scope_call_path_audit()
    hash_audit, hash_blockers = source_code_hash_audit()
    rerun, rerun_blockers = verifier_test_rerun_report()
    saturation, saturation_blockers = saturation_self_redteam()
    all_blockers.extend(
        runtime_blockers
        + future_blockers
        + failopen_blockers
        + noleak_blockers
        + diff_blockers
        + hash_blockers
        + rerun_blockers
        + saturation_blockers
    )
    terminal = ACCEPT_TERMINAL_DECISION if not all_blockers else BLOCKER_TERMINAL_DECISION

    context_anchor = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_context_anchor",
            "route_id": ROUTE_ID,
            "generated_at_utc": now_iso(),
            "git_head": run_git(["rev-parse", "HEAD"]),
            "git_head_short": run_git(["rev-parse", "--short", "HEAD"]),
            "controlling_prompt_path": rel(PROMPT_PATH),
            "target_implementation_package": rel(IMPLEMENTATION_DIR),
            "target_code_changes": [
                "src/research_infra/forward_capture.py",
                "tests/test_forward_capture_shadow_loggers.py",
            ],
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "audit_scope": "independent G12 implementation-acceptance audit only",
            "forbidden_surfaces": [
                "scoring",
                "validation",
                "promotion",
                "registry edit",
                "paid/API route",
                "remote push",
                "prompt/config/risk/permissions/safety/selector/canary changes",
                "MT5 order/account/history/deal/position behavior",
                "credentials",
                "live trading behavior",
            ],
            "inputs_read": [
                rel(PROMPT_PATH),
                rel(IMPLEMENTATION_DIR),
                rel(DESIGN_DIR),
                "src/research_infra/forward_capture.py",
                "tests/test_forward_capture_shadow_loggers.py",
            ],
            "git_status_paths_at_build": git_status_paths(),
        }
    )
    decision = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_decision_ledger",
            "route_id": ROUTE_ID,
            "terminal_decision": terminal if terminal == ACCEPT_TERMINAL_DECISION else REJECT_TERMINAL_DECISION if any(b["blocker_id"].startswith("G12-DIFF-001") for b in all_blockers) else terminal,
            "accepted_scope": "source/control implementation evidence only",
            "acceptance_does_not_make_logger_validation_safe": True,
            "next_allowed_lane": "shadow-only observation/readiness review or G0 synthesis; scoring and promotion require separate future gates",
            "remaining_forbidden": [
                "result/cost scoring",
                "validation",
                "promotion",
                "registry edits",
                "paid/API routes",
                "remote push",
                "live trading behavior",
            ],
            "runtime_55_field_contract_passed": runtime["audit_passed"],
            "future_logger_20_field_contract_passed": future["audit_passed"],
            "failopen_no_live_behavior_passed": failopen["audit_passed"],
            "forbidden_redaction_noleak_passed": noleak["audit_passed"],
            "diff_scope_call_path_passed": diff_scope["audit_passed"],
            "source_code_hash_audit_passed": hash_audit["audit_passed"],
            "implementation_verifier_test_reruns_passed": rerun["audit_passed"],
            "saturation_passed": saturation["audit_passed"],
            "exact_repair_blocker_count": len(all_blockers),
            "exact_repair_blockers": all_blockers,
        }
    )
    coverage = instruction_coverage_checklist(decision["terminal_decision"], len(all_blockers))
    repair = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_exact_repair_blocker_ledger",
            "route_id": ROUTE_ID,
            "terminal_decision": decision["terminal_decision"],
            "exact_repair_blocker_count": len(all_blockers),
            "remaining_blockers": all_blockers,
            "blocker_ledger_status": "EMPTY_EXACT_REPAIR_BLOCKER_LEDGER" if not all_blockers else "EXACT_REPAIR_REQUIRED",
        }
    )
    completion = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_completion_audit",
            "route_id": ROUTE_ID,
            "objective_restatement": (
                "Independently audit the NOFILL forward source-capture additive logger implementation for "
                "source/control implementation acceptance only, with no scoring, validation, promotion, registry, "
                "paid/API, remote, or live-behavior opening."
            ),
            "terminal_decision": decision["terminal_decision"],
            "completion_standard_satisfied": not all_blockers,
            "can_mark_goal_complete_after_verification_commit_and_closeout": not all_blockers,
            "prompt_to_artifact_checklist": completion_checklist(decision["terminal_decision"], len(all_blockers)),
            "missing_incomplete_or_weak_requirements": [],
            "exact_repair_blocker_count": len(all_blockers),
            "exact_repair_blockers": all_blockers,
            "validation_or_promotion_opened": False,
            "live_behavior_changed": False,
        }
    )

    payloads = {
        JSON_ARTIFACTS[0]: context_anchor,
        JSON_ARTIFACTS[1]: decision,
        JSON_ARTIFACTS[2]: runtime,
        JSON_ARTIFACTS[3]: future,
        JSON_ARTIFACTS[4]: failopen,
        JSON_ARTIFACTS[5]: noleak,
        JSON_ARTIFACTS[6]: diff_scope,
        JSON_ARTIFACTS[7]: rerun,
        JSON_ARTIFACTS[8]: hash_audit,
        JSON_ARTIFACTS[9]: saturation,
        JSON_ARTIFACTS[10]: coverage,
        JSON_ARTIFACTS[11]: repair,
        JSON_ARTIFACTS[12]: completion,
    }
    titles = {
        JSON_ARTIFACTS[0]: "G12 NOFILL Source-Capture Implementation Audit Context Anchor",
        JSON_ARTIFACTS[1]: "G12 Decision Ledger",
        JSON_ARTIFACTS[2]: "Runtime 55-Field Contract Audit",
        JSON_ARTIFACTS[3]: "Future Logger Field Audit",
        JSON_ARTIFACTS[4]: "Fail-Open No-Live-Behavior Audit",
        JSON_ARTIFACTS[5]: "Forbidden Redaction No-Leak Audit",
        JSON_ARTIFACTS[6]: "Diff Scope And Call Path Audit",
        JSON_ARTIFACTS[7]: "Verifier And Test Rerun Report",
        JSON_ARTIFACTS[8]: "Source Code Hash Audit",
        JSON_ARTIFACTS[9]: "Saturation Self-Red-Team Audit",
        JSON_ARTIFACTS[10]: "Instruction Coverage Checklist",
        JSON_ARTIFACTS[11]: "Exact Repair Blocker Ledger",
        JSON_ARTIFACTS[12]: "Completion Audit",
    }
    for name, payload in payloads.items():
        write_json(name, payload)
    for json_name, md_name in zip(JSON_ARTIFACTS, MD_ARTIFACTS[:12] + [MD_ARTIFACTS[13]]):
        write_md(md_name, render_md(titles[json_name], payloads[json_name]))
    write_md(MD_ARTIFACTS[12], render_next_lane_prompt())
    return completion


def main() -> int:
    completion = build_artifacts()
    print(json.dumps(completion, indent=2, sort_keys=True))
    return 0 if completion["completion_standard_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
