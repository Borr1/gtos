from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE"
SCHEMA_VERSION = "main_orch48_ai_decision_trace_provenance_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.ai_decision_trace_logger import build_ai_decision_trace_row  # noqa: E402


CONFIG_SOURCE = REPO / "config/agent_config.yaml"
TRACE_LOGGER = REPO / "src/components/ai_decision_trace_logger.py"
PRIMARY_ANALYZER = REPO / "src/components/primary_analyzer.py"
TRACE_TEST = REPO / "tests/test_ai_decision_trace_logger.py"
PRIMARY_TEST = REPO / "tests/test_primary_analyzer.py"
AI_AUDIT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_SUMMARY_{DATE}.json"
MALFORMED_CAPTURE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_MALFORMED_MONITOR_CAPTURE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_build_trace_row_is_hash_only",
    "test_record_trace_respects_enabled_config",
    "test_analyze_writes_hash_only_ai_decision_trace",
]
EXPECTED_STATUSES = [
    "api_timeout",
    "api_server_error",
    "api_rate_limit",
    "unexpected_error",
    "parsed_first_attempt",
    "parsed_retry",
    "malformed_demoted",
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


def read_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


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


def boundary(*, runtime_observability_effect_if_runtime_reenabled: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": (REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "runtime_observability_effect_if_runtime_reenabled": runtime_observability_effect_if_runtime_reenabled,
        "trading_decision_behavior_changed": False,
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "stores_full_prompt_or_response_text": False,
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def config_activation_row(config: dict[str, Any]) -> dict[str, Any]:
    logger_cfg = ((config.get("shadow_loggers") or {}).get("ai_decision_trace_logger") or {})
    return {
        "ai_decision_trace_provenance_row_id": "MAIN-ORCH48-AI-DECISION-TRACE-PROVENANCE-00000001",
        "audit_surface": "ai_decision_trace_config_activation",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(CONFIG_SOURCE),
        "source_sha256": sha256_path(CONFIG_SOURCE),
        "config_enabled": bool(logger_cfg.get("enabled", False)),
        "configured_path": logger_cfg.get("path") or "shadow_logs/ai_decision_trace.jsonl",
        "implementation_decision": "ENABLE_HASH_ONLY_AI_DECISION_TRACE_OBSERVABILITY",
        "research_boundary": boundary(runtime_observability_effect_if_runtime_reenabled=True),
    }


def runtime_patch_row(logger_text: str, analyzer_text: str) -> dict[str, Any]:
    status_presence = {status: status in analyzer_text for status in EXPECTED_STATUSES}
    return {
        "ai_decision_trace_provenance_row_id": "MAIN-ORCH48-AI-DECISION-TRACE-PROVENANCE-00000002",
        "audit_surface": "ai_decision_trace_runtime_patch",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": f"{display_path(TRACE_LOGGER)}, {display_path(PRIMARY_ANALYZER)}",
        "source_sha256": {
            display_path(TRACE_LOGGER): sha256_path(TRACE_LOGGER),
            display_path(PRIMARY_ANALYZER): sha256_path(PRIMARY_ANALYZER),
        },
        "logger_module_present": "def record_ai_decision_trace" in logger_text,
        "hash_only_schema_present": "stores_full_prompt_or_response_text" in logger_text,
        "primary_analyzer_imports_logger": "record_ai_decision_trace" in analyzer_text,
        "primary_analyzer_records_trace": "_record_ai_decision_trace" in analyzer_text,
        "expected_response_status_presence": status_presence,
        "expected_response_status_present_rows": sum(status_presence.values()),
        "implementation_decision": "WIRE_PRIMARY_ANALYZER_TO_HASH_ONLY_TRACE_LOGGER",
        "research_boundary": boundary(runtime_observability_effect_if_runtime_reenabled=True),
    }


def hash_only_self_check_row() -> dict[str, Any]:
    row = build_ai_decision_trace_row(
        system_prompt=[{"type": "text", "text": "SECRET_SYSTEM_PROMPT_SHOULD_NOT_APPEAR"}],
        user_message="SECRET_USER_MESSAGE_SHOULD_NOT_APPEAR",
        raw_response='{"secret":"SECRET_RESPONSE_SHOULD_NOT_APPEAR"}',
        result=None,
        usage={"input_tokens": 1, "output_tokens": 2, "cache_read_tokens": 3, "cache_create_tokens": 4},
        symbol="XAUUSD",
        candle_time="2026-05-18T00:00:00+00:00",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="parsed_first_attempt",
        parse_attempts=1,
    )
    encoded = json.dumps(row, sort_keys=True)
    forbidden = [
        "SECRET_SYSTEM_PROMPT_SHOULD_NOT_APPEAR",
        "SECRET_USER_MESSAGE_SHOULD_NOT_APPEAR",
        "SECRET_RESPONSE_SHOULD_NOT_APPEAR",
    ]
    return {
        "ai_decision_trace_provenance_row_id": "MAIN-ORCH48-AI-DECISION-TRACE-PROVENANCE-00000003",
        "audit_surface": "ai_decision_trace_hash_only_self_check",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(TRACE_LOGGER),
        "source_sha256": sha256_path(TRACE_LOGGER),
        "hash_only_self_check_passed": not any(token in encoded for token in forbidden),
        "prompt_fingerprint_present": bool(row.get("prompt_fingerprint")),
        "raw_response_hash_present": bool(row.get("raw_response_sha256")),
        "stores_full_prompt_or_response_text": False,
        "implementation_decision": "STORE_PROMPT_AND_RESPONSE_FINGERPRINTS_NOT_TEXT",
        "research_boundary": boundary(),
    }


def test_coverage_row(test_texts: dict[str, str]) -> dict[str, Any]:
    combined = "\n".join(test_texts.values())
    covered = {name: name in combined for name in EXPECTED_TEST_NAMES}
    return {
        "ai_decision_trace_provenance_row_id": "MAIN-ORCH48-AI-DECISION-TRACE-PROVENANCE-00000004",
        "audit_surface": "ai_decision_trace_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": ", ".join(display_path(path) for path in (TRACE_TEST, PRIMARY_TEST)),
        "source_sha256": {
            display_path(TRACE_TEST): sha256_path(TRACE_TEST),
            display_path(PRIMARY_TEST): sha256_path(PRIMARY_TEST),
        },
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_HASH_ONLY_TRACE_AND_PRIMARY_ANALYZER_WIRING",
        "research_boundary": boundary(),
    }


def inheritance_row(ai_audit_summary: dict[str, Any], malformed_capture_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ai_decision_trace_provenance_row_id": "MAIN-ORCH48-AI-DECISION-TRACE-PROVENANCE-00000005",
        "audit_surface": "ai_decision_trace_ai_architecture_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": f"{display_path(AI_AUDIT_SUMMARY)}, {display_path(MALFORMED_CAPTURE_SUMMARY)}",
        "source_sha256": {
            display_path(AI_AUDIT_SUMMARY): sha256_path(AI_AUDIT_SUMMARY),
            display_path(MALFORMED_CAPTURE_SUMMARY): sha256_path(MALFORMED_CAPTURE_SUMMARY),
        },
        "inherited_malformed_response_rows": int(ai_audit_summary.get("malformed_response_rows") or 0),
        "inherited_flat_refusal_or_short_non_json_rows": int(
            malformed_capture_summary.get("flat_refusal_or_short_non_json_rows") or 0
        ),
        "inherited_ai_audit_paid_api_rows": int(ai_audit_summary.get("paid_api_or_vendor_call_rows") or 0),
        "implementation_decision": "ADD_PROMPT_RESPONSE_FINGERPRINTS_FOR_NO_API_REPLAY_AND_CACHE_AUDITS",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "config_enabled_rows": sum(bool(row.get("config_enabled")) for row in rows),
        "logger_module_present_rows": sum(bool(row.get("logger_module_present")) for row in rows),
        "primary_analyzer_records_trace_rows": sum(bool(row.get("primary_analyzer_records_trace")) for row in rows),
        "expected_response_status_present_rows": sum(int(row.get("expected_response_status_present_rows") or 0) for row in rows),
        "hash_only_self_check_passed_rows": sum(bool(row.get("hash_only_self_check_passed")) for row in rows),
        "stores_full_prompt_or_response_text_rows": sum(bool(row.get("stores_full_prompt_or_response_text")) for row in rows),
        "expected_test_names_covered_rows": sum(int(row.get("expected_test_names_covered_rows") or 0) for row in rows),
        "inherited_malformed_response_rows": sum(int(row.get("inherited_malformed_response_rows") or 0) for row in rows),
        "runtime_observability_effect_if_runtime_reenabled_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_observability_effect_if_runtime_reenabled"))
            for row in rows
        ),
        "trading_decision_behavior_changed_rows": sum(
            bool((row.get("research_boundary") or {}).get("trading_decision_behavior_changed")) for row in rows
        ),
        "paid_api_or_vendor_call_rows": sum(
            bool((row.get("research_boundary") or {}).get("paid_api_or_vendor_call")) for row in rows
        ),
        "broker_operation_rows": sum(bool((row.get("research_boundary") or {}).get("broker_operation")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
    }


def build() -> dict[str, Any]:
    config = read_config(CONFIG_SOURCE)
    logger_text = TRACE_LOGGER.read_text(encoding="utf-8")
    analyzer_text = PRIMARY_ANALYZER.read_text(encoding="utf-8")
    test_texts = {
        display_path(TRACE_TEST): TRACE_TEST.read_text(encoding="utf-8"),
        display_path(PRIMARY_TEST): PRIMARY_TEST.read_text(encoding="utf-8"),
    }
    rows = [
        config_activation_row(config),
        runtime_patch_row(logger_text, analyzer_text),
        hash_only_self_check_row(),
        test_coverage_row(test_texts),
        inheritance_row(read_json(AI_AUDIT_SUMMARY), read_json(MALFORMED_CAPTURE_SUMMARY)),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(CONFIG_SOURCE),
            code_surface(AI_AUDIT_SUMMARY),
            code_surface(MALFORMED_CAPTURE_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(TRACE_LOGGER),
            code_surface(PRIMARY_ANALYZER),
            code_surface(TRACE_TEST),
            code_surface(PRIMARY_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "ai_decision_trace_logger_enabled": True,
            "hash_only_prompt_response_provenance": True,
            "runtime_observability_effect_if_runtime_reenabled": True,
            "trading_decision_behavior_changed": False,
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
        "hash_only_self_check_passed_rows": summary["hash_only_self_check_passed_rows"],
        "trading_decision_behavior_changed_rows": summary["trading_decision_behavior_changed_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
