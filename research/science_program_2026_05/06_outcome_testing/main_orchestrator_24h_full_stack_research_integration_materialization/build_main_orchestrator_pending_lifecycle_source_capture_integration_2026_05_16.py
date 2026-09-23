from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
IMPLEMENTATION_COMMIT = "f54a0e09"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

NEW_SOURCE_SAFE_FIELDS = [
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_reason_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_value_source_safe",
    "entry_touch_spread_unit",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
]

CODE_FILES = [
    "src/components/pending_limit_lifecycle_logger.py",
    "src/components/execution.py",
    "tests/test_pending_limit_lifecycle_logger.py",
]

INPUT_EVIDENCE_FILES = [
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_INPUT_SNAPSHOT_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_DUPLICATE_AWARE_SUMMARY_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_2026-05-16.jsonl",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_VERIFICATION_RESULT_2026-05-16.json",
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_QUERY_FAILED: {exc}"


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    head = git_output(["rev-parse", "--short=8", "HEAD"])
    implementation_subject = git_output(["show", "-s", "--format=%H %s", IMPLEMENTATION_COMMIT])

    evidence_records = [
        artifact_record(Path(path).stem.lower(), REPO_ROOT / path) for path in INPUT_EVIDENCE_FILES
    ]
    code_records = [artifact_record(Path(path).stem, REPO_ROOT / path) for path in CODE_FILES]

    source_text = {
        path: (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace") for path in CODE_FILES
    }
    field_presence = {
        field: {
            "logger_required_field": field in source_text["src/components/pending_limit_lifecycle_logger.py"],
            "execution_emits_field": field in source_text["src/components/execution.py"],
            "test_asserts_or_schema_covers_field": field in source_text["tests/test_pending_limit_lifecycle_logger.py"],
        }
        for field in NEW_SOURCE_SAFE_FIELDS
    }

    input_snapshot_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_INPUT_SNAPSHOT_{DATE}.json"
    field_contract_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_FIELD_CONTRACT_{DATE}.json"
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_IMPLEMENTATION_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_IMPLEMENTATION_SUMMARY_{DATE}.md"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_OUTPUT_MANIFEST_{DATE}.json"

    input_snapshot = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "head_at_build": head,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "implementation_subject": implementation_subject,
        "input_evidence_files": evidence_records,
        "code_files": code_records,
        "safe_flags": SAFE_FLAGS,
    }

    field_contract = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "purpose": "Add forward source-safe observability for pending-limit no-fill/fillability replay without changing live decision behavior.",
        "new_source_safe_fields": NEW_SOURCE_SAFE_FIELDS,
        "field_presence": field_presence,
        "source_safe_semantics": {
            "decision_spread_value_source_safe": "Decision-time spread if telemetry captured it; does not infer historical spread after the fact.",
            "entry_touch_spread_value_source_safe": "Tick spread only when an entry-touch check is source-observed by the lifecycle path.",
            "terminal_area_touch_status": "Source-safe status for target/terminal area touch versus no touch/not captured.",
            "protective_area_touch_status": "Source-safe status for wrong-side/protective area touch versus no touch/not captured.",
            "event_order_resolution_method": "Explicit method label for no-entry, entry-touch, target-before-entry, or retry ambiguity.",
            "same_tick_same_bar_ambiguity_status": "Explicit unscored ambiguity flag; default is not evaluated by this logger.",
        },
        "does_not_change": [
            "trade placement",
            "risk sizing",
            "AI prompt behavior",
            "selector/gate behavior",
            "broker/order operations",
            "promotion or validation posture",
        ],
        "safe_flags": SAFE_FLAGS,
    }

    ledger_rows = [
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-CAPTURE-001",
            "decision": "IMPLEMENT_SOURCE_SAFE_PENDING_LIMIT_CAPTURE_FIELDS",
            "evidence": "Second live/shadow legacy plate selected UPGRADE_CAPTURE_CONTRACT_NOT_SCORE_ROWS because no-fill and pending lifecycle rows were useful as source infrastructure but not score-ready.",
            "source_artifacts": [rel(REPO_ROOT / INPUT_EVIDENCE_FILES[2]), rel(REPO_ROOT / INPUT_EVIDENCE_FILES[3])],
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-CAPTURE-002",
            "decision": "PRESERVE_FORWARD_SCOREABILITY_WITHOUT_BACKFILLING_HISTORICAL_TRUTH",
            "evidence": "Historical no-fill rows cannot reconstruct true intent/order/path chronology where the logger did not record it.",
            "new_fields": NEW_SOURCE_SAFE_FIELDS,
            "non_claims": [
                "No broker actual-R label is created.",
                "No target/stop ordering is inferred when source fields are absent.",
                "No live behavior changes are made.",
            ],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-CAPTURE-003",
            "decision": "UPDATE_EXECUTION_LIFECYCLE_LOGGING_AND_SCHEMA_TESTS",
            "code_files": CODE_FILES,
            "field_presence": field_presence,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-CAPTURE-004",
            "decision": "FOCUSED_TESTS_PASSED_WITH_REPO_LOCAL_TEMP_AND_CACHE_DISABLED",
            "syntax_check": "ast_parse_ok",
            "focused_test_command": r"py -3 -m pytest tests\test_pending_limit_lifecycle_logger.py tests\test_forward_capture_shadow_loggers.py -q -p no:cacheprovider --basetemp .codex_tmp\pytest-main-orch",
            "focused_test_result": "31 passed in 5.07s",
            "environment_note": "Default TEMP and C:\\tmp pytest temp roots were permission-blocked before test bodies; repo-local basetemp with pytest cache disabled avoided environment friction.",
            "safe_flags": SAFE_FLAGS,
        },
    ]

    summary = "\n".join(
        [
            "# Pending Lifecycle Source Capture Integration",
            "",
            f"Generated: `{generated_utc}`",
            f"Implementation commit: `{implementation_subject}`",
            "",
            "This plate converts the live/shadow legacy decision `UPGRADE_CAPTURE_CONTRACT_NOT_SCORE_ROWS` into an additive pending-limit lifecycle source-capture improvement.",
            "",
            "It adds forward source-safe fields for pending horizon, cancel/expiry reason status, decision and entry-touch spread, terminal/protective area touch status, event-order resolution method, and same-tick/same-bar ambiguity status.",
            "",
            "No trade placement, AI prompt, risk, selector, safety gate, broker operation, promotion, validation-safe claim, or live-effect change is opened.",
            "",
            "Verification recorded: `ast_parse_ok`; focused pytest with repo-local temp and cache disabled: `31 passed in 5.07s`.",
            "",
        ]
    )

    write_json(input_snapshot_path, input_snapshot)
    write_json(field_contract_path, field_contract)
    write_jsonl(ledger_path, ledger_rows)
    summary_path.write_text(summary, encoding="utf-8")

    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 4,
        "artifacts": [
            artifact_record("input_snapshot", input_snapshot_path),
            artifact_record("field_contract", field_contract_path),
            artifact_record("implementation_ledger", ledger_path),
            artifact_record("summary_md", summary_path),
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)

    print(json.dumps({"ok": True, "manifest": rel(manifest_path), "artifacts": manifest["artifact_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
