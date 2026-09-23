from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CROSS_CORR_DIAGNOSTICS_TOOLING_INTAKE"
SCHEMA_VERSION = "main_orch48_cross_corr_diagnostics_tooling_intake_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
JOIN_SOURCE = REPO / "src/research_infra/decision_layer_diagnostics_join.py"
VERIFY_SOURCE = REPO / "scripts/verify_shadow_log_integrity.py"
BACKFILL_SOURCE = REPO / "scripts/backfill_decision_layer_diagnostics_join.py"
FOLLOWUP_SOURCE = REPO / "scripts/audit_live_shadow_followup_coverage.py"
JOIN_TEST_SOURCE = REPO / "tests/test_decision_layer_diagnostics_join.py"
FOLLOWUP_TEST_SOURCE = REPO / "tests/test_live_shadow_followup_coverage_audit.py"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def source_contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build() -> dict[str, Any]:
    join_accepts_source = source_contains(JOIN_SOURCE, "cross_instrument_correlation_rows")
    join_emits_context = source_contains(JOIN_SOURCE, "cross_instrument_correlation_context")
    missing_is_optional = source_contains(
        JOIN_SOURCE,
        "CROSS_INSTRUMENT_CORRELATION_DIAGNOSTIC_OPTIONAL_MISSING_WITHIN_TIME_WINDOW",
    )
    verify_reads_source = source_contains(VERIFY_SOURCE, "cross_instrument_correlation_decisions.jsonl")
    backfill_reads_source = source_contains(BACKFILL_SOURCE, "--cross-instrument-correlation")
    followup_matrix_includes_source = source_contains(
        FOLLOWUP_SOURCE,
        "shadow_logs/cross_instrument_correlation_decisions.jsonl",
    )
    join_tests_cover_source = source_contains(
        JOIN_TEST_SOURCE,
        "test_missing_cross_instrument_correlation_context_is_optional",
    )
    followup_tests_cover_source = source_contains(
        FOLLOWUP_TEST_SOURCE,
        "shadow_logs/cross_instrument_correlation_decisions.jsonl",
    )
    runtime_halt_active = RUNTIME_HALT_FLAG.exists()

    rows = [
        {
            "intake_row_id": "MAIN-ORCH48-CROSS-CORR-DIAG-TOOLING-0001",
            "schema_version": SCHEMA_VERSION,
            "check": "DECISION_LAYER_JOIN_ACCEPTS_OPTIONAL_SOURCE",
            "source_path": display_path(JOIN_SOURCE),
            "source_sha256": sha256_path(JOIN_SOURCE),
            "join_accepts_source": join_accepts_source,
            "join_emits_context": join_emits_context,
            "missing_is_optional": missing_is_optional,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "intake_row_id": "MAIN-ORCH48-CROSS-CORR-DIAG-TOOLING-0002",
            "schema_version": SCHEMA_VERSION,
            "check": "COMMAND_LINE_AUDITS_CONSUME_SOURCE",
            "verify_source_path": display_path(VERIFY_SOURCE),
            "verify_source_sha256": sha256_path(VERIFY_SOURCE),
            "backfill_source_path": display_path(BACKFILL_SOURCE),
            "backfill_source_sha256": sha256_path(BACKFILL_SOURCE),
            "verify_reads_source": verify_reads_source,
            "backfill_reads_source": backfill_reads_source,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "intake_row_id": "MAIN-ORCH48-CROSS-CORR-DIAG-TOOLING-0003",
            "schema_version": SCHEMA_VERSION,
            "check": "FOLLOWUP_MATRIX_AND_TESTS_ADVERTISE_SOURCE",
            "followup_source_path": display_path(FOLLOWUP_SOURCE),
            "followup_source_sha256": sha256_path(FOLLOWUP_SOURCE),
            "join_test_source_path": display_path(JOIN_TEST_SOURCE),
            "join_test_source_sha256": sha256_path(JOIN_TEST_SOURCE),
            "followup_test_source_path": display_path(FOLLOWUP_TEST_SOURCE),
            "followup_test_source_sha256": sha256_path(FOLLOWUP_TEST_SOURCE),
            "followup_matrix_includes_source": followup_matrix_includes_source,
            "join_tests_cover_source": join_tests_cover_source,
            "followup_tests_cover_source": followup_tests_cover_source,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "intake_row_id": "MAIN-ORCH48-CROSS-CORR-DIAG-TOOLING-0004",
            "schema_version": SCHEMA_VERSION,
            "check": "SESSION_57_RUNTIME_HALT_BOUNDARY",
            "source_path": display_path(RUNTIME_HALT_FLAG),
            "runtime_halt_active": runtime_halt_active,
            "live_runtime_restart_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "intake_rows": len(rows),
        "join_accepts_source": join_accepts_source,
        "join_emits_context": join_emits_context,
        "missing_is_optional": missing_is_optional,
        "verify_reads_source": verify_reads_source,
        "backfill_reads_source": backfill_reads_source,
        "followup_matrix_includes_source": followup_matrix_includes_source,
        "join_tests_cover_source": join_tests_cover_source,
        "followup_tests_cover_source": followup_tests_cover_source,
        "runtime_halt_active": runtime_halt_active,
        "implementation_effect": {
            "diagnostics_tooling_only": True,
            "current_runtime_restart_now": False,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "intake_rows": len(rows),
        "runtime_halt_active": runtime_halt_active,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
