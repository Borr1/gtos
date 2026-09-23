from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_PARSER_HARDENING"
SCHEMA_VERSION = "main_orch48_ai_parser_hardening_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.ai_decision_architecture_audit import (
    classify_malformed_ai_response,
    parse_jsonl,
)


PARSER_SOURCE = REPO / "src/utils/validation.py"
PRIMARY_ANALYZER_SOURCE = REPO / "src/components/primary_analyzer.py"
PRIMARY_ANALYZER_TEST = REPO / "tests/test_primary_analyzer.py"
BATCH_BACKTEST_TEST = REPO / "tests/test_batch_backtest.py"
MALFORMED_LOG = REPO / "shadow_logs/malformed_responses.jsonl"
AI_AUDIT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_LEDGER_{DATE}.jsonl"
AI_AUDIT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_first_valid_json_before_extra_object",
    "test_first_valid_json_ignores_non_json_braces_and_string_braces",
    "test_json_with_trailing_second_object_uses_first_valid_object",
    "test_fenced_json_with_trailing_object_inside_fence_uses_first_object",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def boundary(*, runtime_parser_behavior_effect_if_runtime_reenabled: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": (REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "production_import_path_hardened": runtime_parser_behavior_effect_if_runtime_reenabled,
        "runtime_parser_behavior_effect_if_runtime_reenabled": runtime_parser_behavior_effect_if_runtime_reenabled,
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def malformed_evidence_row(malformed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    classifications = Counter(classify_malformed_ai_response(row) for row in malformed_rows)
    return {
        "ai_parser_hardening_row_id": "MAIN-ORCH48-AI-PARSER-HARDENING-00000001",
        "audit_surface": "malformed_response_parser_hardening_trigger",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(MALFORMED_LOG),
        "source_sha256": sha256_path(MALFORMED_LOG),
        "malformed_response_rows": len(malformed_rows),
        "malformed_response_classification_counts": dict(sorted(classifications.items())),
        "parser_hardening_scope_rows": classifications.get("JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE", 0),
        "flat_refusal_or_short_non_json_rows": classifications.get("FLAT_REFUSAL_OR_SHORT_NON_JSON", 0),
        "source_operation": "consume_existing_malformed_log_no_api_call",
        "implementation_decision": "HARDEN_JSON_EXTRACTION_FOR_VALID_FIRST_OBJECT_AND_KEEP_REFUSAL_RETRY_PATH",
        "research_boundary": boundary(),
    }


def parser_patch_row(parser_text: str) -> dict[str, Any]:
    return {
        "ai_parser_hardening_row_id": "MAIN-ORCH48-AI-PARSER-HARDENING-00000002",
        "audit_surface": "shared_strip_json_fences_patch",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(PARSER_SOURCE),
        "source_sha256": sha256_path(PARSER_SOURCE),
        "balanced_json_object_helper_present": "def _balanced_json_object_at" in parser_text,
        "first_valid_json_object_helper_present": "def _first_valid_json_object" in parser_text,
        "json_decode_guard_present": "json.JSONDecodeError" in parser_text,
        "strip_json_fences_uses_first_valid_object_count": parser_text.count("_first_valid_json_object"),
        "repo_runtime_parser_code_changed": True,
        "implementation_decision": "EXTRACT_FIRST_SYNTACTICALLY_VALID_BALANCED_JSON_OBJECT_BEFORE_LEGACY_FALLBACK",
        "research_boundary": boundary(runtime_parser_behavior_effect_if_runtime_reenabled=True),
    }


def primary_analyzer_row(primary_text: str) -> dict[str, Any]:
    parse_block = primary_text[primary_text.find("def _parse_and_validate") : primary_text.find("# ------------------------------------------------------------------", primary_text.find("def _parse_and_validate") + 1)]
    return {
        "ai_parser_hardening_row_id": "MAIN-ORCH48-AI-PARSER-HARDENING-00000003",
        "audit_surface": "primary_analyzer_parser_path",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(PRIMARY_ANALYZER_SOURCE),
        "source_sha256": sha256_path(PRIMARY_ANALYZER_SOURCE),
        "parse_and_validate_uses_strip_json_fences": "strip_json_fences(raw_response)" in parse_block,
        "parse_and_validate_uses_json_loads_after_shared_cleaning": "json.loads(cleaned)" in parse_block,
        "malformed_retry_path_preserved": "_log_malformed_response" in primary_text and "ai_output_malformed" in primary_text,
        "repo_runtime_parser_code_changed": False,
        "implementation_decision": "KEEP_PRIMARY_ANALYZER_RETRY_FLOW_AND_HARDEN_SHARED_CLEANING_LAYER",
        "research_boundary": boundary(runtime_parser_behavior_effect_if_runtime_reenabled=True),
    }


def test_coverage_row(test_texts: dict[str, str]) -> dict[str, Any]:
    combined = "\n".join(test_texts.values())
    covered = {name: name in combined for name in EXPECTED_TEST_NAMES}
    return {
        "ai_parser_hardening_row_id": "MAIN-ORCH48-AI-PARSER-HARDENING-00000004",
        "audit_surface": "focused_parser_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": ", ".join(display_path(path) for path in (BATCH_BACKTEST_TEST, PRIMARY_ANALYZER_TEST)),
        "source_sha256": {
            display_path(BATCH_BACKTEST_TEST): sha256_path(BATCH_BACKTEST_TEST),
            display_path(PRIMARY_ANALYZER_TEST): sha256_path(PRIMARY_ANALYZER_TEST),
        },
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_FIRST_VALID_OBJECT_EXTRACTION_IN_UTILITY_AND_PRIMARY_ANALYZER_PATH",
        "research_boundary": boundary(),
    }


def inherited_ai_architecture_row(ai_audit_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ai_parser_hardening_row_id": "MAIN-ORCH48-AI-PARSER-HARDENING-00000005",
        "audit_surface": "ai_architecture_audit_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(AI_AUDIT_SUMMARY),
        "source_sha256": sha256_path(AI_AUDIT_SUMMARY),
        "inherited_ai_audit_rows": int(ai_audit_summary.get("rows") or 0),
        "inherited_malformed_response_rows": int(ai_audit_summary.get("malformed_response_rows") or 0),
        "inherited_manual_canary_fixture_rows": int(ai_audit_summary.get("manual_canary_fixture_rows") or 0),
        "inherited_selector_dossier_rows": int(ai_audit_summary.get("selector_dossier_rows") or 0),
        "implementation_decision": "CONSUME_AI_ARCHITECTURE_AUDIT_HARDEN_PARSER_SUBTASK_WITHOUT_PAID_API",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "malformed_response_rows": sum(int(row.get("malformed_response_rows") or 0) for row in rows),
        "parser_hardening_scope_rows": sum(int(row.get("parser_hardening_scope_rows") or 0) for row in rows),
        "flat_refusal_or_short_non_json_rows": sum(int(row.get("flat_refusal_or_short_non_json_rows") or 0) for row in rows),
        "repo_runtime_parser_code_changed_rows": sum(bool(row.get("repo_runtime_parser_code_changed")) for row in rows),
        "runtime_parser_behavior_effect_if_runtime_reenabled_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_parser_behavior_effect_if_runtime_reenabled"))
            for row in rows
        ),
        "paid_api_or_vendor_call_rows": sum(
            bool((row.get("research_boundary") or {}).get("paid_api_or_vendor_call")) for row in rows
        ),
        "broker_operation_rows": sum(bool((row.get("research_boundary") or {}).get("broker_operation")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
        "expected_test_names_covered_rows": sum(int(row.get("expected_test_names_covered_rows") or 0) for row in rows),
    }


def build() -> dict[str, Any]:
    malformed_rows = parse_jsonl(MALFORMED_LOG.read_text(encoding="utf-8")) if MALFORMED_LOG.exists() else []
    parser_text = PARSER_SOURCE.read_text(encoding="utf-8")
    primary_text = PRIMARY_ANALYZER_SOURCE.read_text(encoding="utf-8")
    test_texts = {
        display_path(BATCH_BACKTEST_TEST): BATCH_BACKTEST_TEST.read_text(encoding="utf-8"),
        display_path(PRIMARY_ANALYZER_TEST): PRIMARY_ANALYZER_TEST.read_text(encoding="utf-8"),
    }
    ai_audit_summary = read_json(AI_AUDIT_SUMMARY)

    rows = [
        malformed_evidence_row(malformed_rows),
        parser_patch_row(parser_text),
        primary_analyzer_row(primary_text),
        test_coverage_row(test_texts),
        inherited_ai_architecture_row(ai_audit_summary),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(MALFORMED_LOG),
            code_surface(AI_AUDIT_LEDGER),
            code_surface(AI_AUDIT_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(PARSER_SOURCE),
            code_surface(PRIMARY_ANALYZER_SOURCE),
            code_surface(BATCH_BACKTEST_TEST),
            code_surface(PRIMARY_ANALYZER_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "shared_parser_hardened": True,
            "primary_analyzer_uses_hardened_shared_parser": True,
            "runtime_parser_behavior_effect_if_runtime_reenabled": True,
            "research_runtime_halt_active": boundary()["research_runtime_halt_active"],
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "runtime_trading_or_live_broker_effect": False,
            "runtime_candidate_use_permitted": False,
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
        "rows": summary["rows"],
        "malformed_response_rows": summary["malformed_response_rows"],
        "parser_hardening_scope_rows": summary["parser_hardening_scope_rows"],
        "expected_test_names_covered_rows": summary["expected_test_names_covered_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
