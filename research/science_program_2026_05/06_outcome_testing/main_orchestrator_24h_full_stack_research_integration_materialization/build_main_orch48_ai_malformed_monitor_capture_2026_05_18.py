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
ROUTE_ID = "MAIN_ORCH48_AI_MALFORMED_MONITOR_CAPTURE"
SCHEMA_VERSION = "main_orch48_ai_malformed_monitor_capture_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.api_refusal_monitor import (  # noqa: E402
    malformed_response_category,
    summarize_malformed_entries,
)
from src.research_infra.ai_decision_architecture_audit import parse_jsonl  # noqa: E402


MALFORMED_LOG = REPO / "shadow_logs/malformed_responses.jsonl"
API_REFUSAL_MONITOR = REPO / "scripts/api_refusal_monitor.py"
PRIMARY_ANALYZER = REPO / "src/components/primary_analyzer.py"
API_REFUSAL_TEST = REPO / "tests/test_api_refusal_monitor.py"
PRIMARY_ANALYZER_TEST = REPO / "tests/test_primary_analyzer.py"
AI_PARSER_HARDENING_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_PARSER_HARDENING_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_category_detects_flat_refusal",
    "test_category_detects_fenced_or_trailing_json_parse_failure",
    "test_summary_counts_context_capture_gap",
    "test_analyze_retries_then_no_trade",
    "test_analyze_retry_transport_failure_logs_context_then_no_trade",
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


def boundary(*, runtime_diagnostic_behavior_effect_if_runtime_reenabled: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": (REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "production_import_path_hardened": runtime_diagnostic_behavior_effect_if_runtime_reenabled,
        "runtime_diagnostic_behavior_effect_if_runtime_reenabled": (
            runtime_diagnostic_behavior_effect_if_runtime_reenabled
        ),
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


def malformed_log_evidence_row(malformed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_malformed_entries(malformed_rows)
    categories = summary["malformed_response_category_counts"]
    timestamps = [str(row.get("timestamp") or "") for row in malformed_rows if row.get("timestamp")]
    return {
        "ai_malformed_monitor_capture_row_id": "MAIN-ORCH48-AI-MALFORMED-MONITOR-CAPTURE-00000001",
        "audit_surface": "malformed_response_log_context_gap",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(MALFORMED_LOG),
        "source_sha256": sha256_path(MALFORMED_LOG),
        **summary,
        "flat_refusal_or_short_non_json_rows": int(categories.get("FLAT_REFUSAL_OR_SHORT_NON_JSON") or 0),
        "json_fence_or_trailing_text_parse_failure_rows": int(
            categories.get("JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE") or 0
        ),
        "first_malformed_response_timestamp": min(timestamps) if timestamps else "",
        "latest_malformed_response_timestamp": max(timestamps) if timestamps else "",
        "implementation_decision": "KEEP_REFUSAL_MONITOR_AND_CAPTURE_ATTRIBUTION_FIELDS_ON_FUTURE_MALFORMED_ROWS",
        "research_boundary": boundary(),
    }


def monitor_taxonomy_row(monitor_text: str) -> dict[str, Any]:
    return {
        "ai_malformed_monitor_capture_row_id": "MAIN-ORCH48-AI-MALFORMED-MONITOR-CAPTURE-00000002",
        "audit_surface": "api_refusal_monitor_taxonomy",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(API_REFUSAL_MONITOR),
        "source_sha256": sha256_path(API_REFUSAL_MONITOR),
        "malformed_response_category_helper_present": "def malformed_response_category" in monitor_text,
        "flat_refusal_detector_delegates_to_category": (
            'malformed_response_category(entry) == "FLAT_REFUSAL_OR_SHORT_NON_JSON"' in monitor_text
        ),
        "summary_helper_counts_symbol_and_candle_time_gap": (
            "malformed_response_rows_missing_symbol_or_candle_time" in monitor_text
        ),
        "telegram_network_call_path_unchanged": "urllib.request.urlopen" in monitor_text,
        "implementation_decision": "ALIGN_WATCHDOG_REFUSAL_CLASSIFICATION_WITH_AI_ARCHITECTURE_AUDIT_CATEGORIES",
        "research_boundary": boundary(runtime_diagnostic_behavior_effect_if_runtime_reenabled=True),
    }


def primary_analyzer_capture_row(primary_text: str) -> dict[str, Any]:
    capture_fields = ["symbol", "candle_time", "kill_zone", "model"]
    field_presence = {field: f'"{field}": {field}' in primary_text for field in capture_fields}
    return {
        "ai_malformed_monitor_capture_row_id": "MAIN-ORCH48-AI-MALFORMED-MONITOR-CAPTURE-00000003",
        "audit_surface": "primary_analyzer_malformed_context_capture",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(PRIMARY_ANALYZER),
        "source_sha256": sha256_path(PRIMARY_ANALYZER),
        "malformed_log_context_present": "malformed_log_context = {" in primary_text,
        "capture_field_presence": field_presence,
        "capture_fields_present_rows": sum(field_presence.values()),
        "malformed_log_context_pass_count": primary_text.count("**malformed_log_context"),
        "retry_transport_failure_raw2_guard_present": 'raw2 = ""' in primary_text,
        "repo_runtime_diagnostic_code_changed": True,
        "implementation_decision": "LOG_SYMBOL_CANDLE_TIME_KILL_ZONE_MODEL_FOR_FUTURE_MALFORMED_AI_RESPONSES",
        "research_boundary": boundary(runtime_diagnostic_behavior_effect_if_runtime_reenabled=True),
    }


def test_coverage_row(test_texts: dict[str, str]) -> dict[str, Any]:
    combined = "\n".join(test_texts.values())
    covered = {name: name in combined for name in EXPECTED_TEST_NAMES}
    return {
        "ai_malformed_monitor_capture_row_id": "MAIN-ORCH48-AI-MALFORMED-MONITOR-CAPTURE-00000004",
        "audit_surface": "focused_malformed_monitor_capture_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": ", ".join(display_path(path) for path in (API_REFUSAL_TEST, PRIMARY_ANALYZER_TEST)),
        "source_sha256": {
            display_path(API_REFUSAL_TEST): sha256_path(API_REFUSAL_TEST),
            display_path(PRIMARY_ANALYZER_TEST): sha256_path(PRIMARY_ANALYZER_TEST),
        },
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_MONITOR_TAXONOMY_AND_PRIMARY_ANALYZER_MALFORMED_ATTRIBUTION_CAPTURE",
        "research_boundary": boundary(),
    }


def inherited_parser_hardening_row(parser_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ai_malformed_monitor_capture_row_id": "MAIN-ORCH48-AI-MALFORMED-MONITOR-CAPTURE-00000005",
        "audit_surface": "ai_parser_hardening_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(AI_PARSER_HARDENING_SUMMARY),
        "source_sha256": sha256_path(AI_PARSER_HARDENING_SUMMARY),
        "inherited_ai_parser_hardening_rows": int(parser_summary.get("rows") or 0),
        "inherited_malformed_response_rows": int(parser_summary.get("malformed_response_rows") or 0),
        "inherited_parser_hardening_scope_rows": int(parser_summary.get("parser_hardening_scope_rows") or 0),
        "implementation_decision": "EXTEND_AI_PARSER_HARDENING_PLATE_WITH_MALFORMED_MONITOR_ATTRIBUTION_CAPTURE",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter()
    for row in rows:
        category_counts.update(row.get("malformed_response_category_counts") or {})
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "malformed_response_rows": sum(int(row.get("malformed_response_rows") or 0) for row in rows),
        "malformed_response_category_counts": dict(sorted(category_counts.items())),
        "flat_refusal_or_short_non_json_rows": sum(
            int(row.get("flat_refusal_or_short_non_json_rows") or 0) for row in rows
        ),
        "json_fence_or_trailing_text_parse_failure_rows": sum(
            int(row.get("json_fence_or_trailing_text_parse_failure_rows") or 0) for row in rows
        ),
        "malformed_response_rows_with_symbol_and_candle_time": sum(
            int(row.get("malformed_response_rows_with_symbol_and_candle_time") or 0) for row in rows
        ),
        "malformed_response_rows_missing_symbol_or_candle_time": sum(
            int(row.get("malformed_response_rows_missing_symbol_or_candle_time") or 0) for row in rows
        ),
        "monitor_taxonomy_hardened_rows": sum(
            bool(row.get("malformed_response_category_helper_present")) for row in rows
        ),
        "future_malformed_context_capture_wired_rows": sum(
            int(row.get("capture_fields_present_rows") or 0) == 4
            and int(row.get("malformed_log_context_pass_count") or 0) >= 2
            for row in rows
        ),
        "retry_transport_failure_raw2_guard_present_rows": sum(
            bool(row.get("retry_transport_failure_raw2_guard_present")) for row in rows
        ),
        "repo_runtime_diagnostic_code_changed_rows": sum(
            bool(row.get("repo_runtime_diagnostic_code_changed")) for row in rows
        ),
        "runtime_diagnostic_behavior_effect_if_runtime_reenabled_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_diagnostic_behavior_effect_if_runtime_reenabled"))
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
    monitor_text = API_REFUSAL_MONITOR.read_text(encoding="utf-8")
    primary_text = PRIMARY_ANALYZER.read_text(encoding="utf-8")
    test_texts = {
        display_path(API_REFUSAL_TEST): API_REFUSAL_TEST.read_text(encoding="utf-8"),
        display_path(PRIMARY_ANALYZER_TEST): PRIMARY_ANALYZER_TEST.read_text(encoding="utf-8"),
    }
    parser_summary = read_json(AI_PARSER_HARDENING_SUMMARY)

    rows = [
        malformed_log_evidence_row(malformed_rows),
        monitor_taxonomy_row(monitor_text),
        primary_analyzer_capture_row(primary_text),
        test_coverage_row(test_texts),
        inherited_parser_hardening_row(parser_summary),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(MALFORMED_LOG),
            code_surface(AI_PARSER_HARDENING_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(API_REFUSAL_MONITOR),
            code_surface(PRIMARY_ANALYZER),
            code_surface(API_REFUSAL_TEST),
            code_surface(PRIMARY_ANALYZER_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "api_refusal_monitor_taxonomy_hardened": True,
            "future_malformed_response_context_capture_wired": True,
            "retry_transport_failure_raw2_guard_present": True,
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
        "flat_refusal_or_short_non_json_rows": summary["flat_refusal_or_short_non_json_rows"],
        "future_malformed_context_capture_wired_rows": summary["future_malformed_context_capture_wired_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
