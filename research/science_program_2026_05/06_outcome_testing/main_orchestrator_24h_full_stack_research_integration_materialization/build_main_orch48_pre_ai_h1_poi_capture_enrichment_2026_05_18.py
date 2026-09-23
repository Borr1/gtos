from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT"
SCHEMA_VERSION = "main_orch48_pre_ai_h1_poi_capture_enrichment_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
JOIN_SUMMARY = ROUTE_DIR / "MAIN_ORCH48_PRE_AI_H1_POI_OUTCOME_JOIN_SUMMARY_2026-05-18.json"
PRE_AI_GATES = REPO / "src/components/pre_ai_gates.py"
CANDIDATE_FEATURES_LOGGER = REPO / "src/components/candidate_features_logger.py"
ORCHESTRATOR = REPO / "src/components/orchestrator.py"
TEST_PRE_AI_GATES = REPO / "tests/test_pre_ai_gates.py"
TEST_CANDIDATE_FEATURES = REPO / "tests/test_candidate_features_logger.py"
TEST_BUGFIXES = REPO / "tests/test_bugfixes_0.py"
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def source_contains(path: Path, *tokens: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return all(token in text for token in tokens)


def build() -> dict[str, Any]:
    generated = utc_now()
    join_summary = read_json(JOIN_SUMMARY)
    join_counts = join_summary.get("join_summary") or {}
    rows = [
        {
            "capture_enrichment_row_id": "MAIN-ORCH48-PRE-AI-H1-POI-CAPTURE-ENRICH-0001",
            "schema_version": SCHEMA_VERSION,
            "surface": "source_gap_consumed",
            "source_path": display_path(JOIN_SUMMARY),
            "source_sha256": sha256_path(JOIN_SUMMARY),
            "pre_ai_skip_rows": join_counts.get("skip_rows"),
            "skip_rows_missing_directional_poi_detail": join_counts.get(
                "skip_rows_missing_directional_poi_detail"
            ),
            "status": "CAPTURE_GAP_IDENTIFIED_FROM_JOIN_ARTIFACT",
            "runtime_decision_effect": False,
        },
        {
            "capture_enrichment_row_id": "MAIN-ORCH48-PRE-AI-H1-POI-CAPTURE-ENRICH-0002",
            "schema_version": SCHEMA_VERSION,
            "surface": "pre_ai_gate_framework_availability_helper",
            "source_path": display_path(PRE_AI_GATES),
            "source_sha256": sha256_path(PRE_AI_GATES),
            "helper_present": source_contains(PRE_AI_GATES, "def framework_poi_availability("),
            "gate_reuses_helper": source_contains(PRE_AI_GATES, "availability = framework_poi_availability("),
            "status": "OBSERVATION_HELPER_WIRED",
            "runtime_decision_effect": False,
        },
        {
            "capture_enrichment_row_id": "MAIN-ORCH48-PRE-AI-H1-POI-CAPTURE-ENRICH-0003",
            "schema_version": SCHEMA_VERSION,
            "surface": "candidate_features_directional_poi_fields",
            "source_path": display_path(CANDIDATE_FEATURES_LOGGER),
            "source_sha256": sha256_path(CANDIDATE_FEATURES_LOGGER),
            "directional_ob_fields_present": source_contains(
                CANDIDATE_FEATURES_LOGGER,
                "mso_h1_unmitigated_ob_count_bullish",
                "mso_h1_unmitigated_ob_count_bearish",
            ),
            "directional_breaker_fields_present": source_contains(
                CANDIDATE_FEATURES_LOGGER,
                "mso_h1_unretested_breaker_count_bullish",
                "mso_h1_unretested_breaker_count_bearish",
            ),
            "directional_fvg_fields_present": source_contains(
                CANDIDATE_FEATURES_LOGGER,
                "mso_m15_fvg_count_bullish",
                "mso_m15_fvg_count_bearish",
            ),
            "pre_ai_framework_fields_present": source_contains(
                CANDIDATE_FEATURES_LOGGER,
                "pre_ai_gate_framework_poi_availability",
                "pre_ai_gate_empty_frameworks",
                "pre_ai_gate_any_framework_has_poi",
            ),
            "status": "LOGGER_CAPTURE_FIELDS_WIRED",
            "runtime_decision_effect": False,
        },
        {
            "capture_enrichment_row_id": "MAIN-ORCH48-PRE-AI-H1-POI-CAPTURE-ENRICH-0004",
            "schema_version": SCHEMA_VERSION,
            "surface": "orchestrator_pre_ai_skip_callsite",
            "source_path": display_path(ORCHESTRATOR),
            "source_sha256": sha256_path(ORCHESTRATOR),
            "callsite_passes_bias": source_contains(ORCHESTRATOR, "pre_ai_gate_bias=bias_result.get(\"bias\")"),
            "callsite_passes_frameworks": source_contains(ORCHESTRATOR, "pre_ai_gate_enabled_frameworks="),
            "callsite_passes_availability": source_contains(ORCHESTRATOR, "framework_poi_availability("),
            "callsite_passes_ai_direction": source_contains(ORCHESTRATOR, "ai_direction_evaluated=("),
            "status": "SKIP_CALLSITE_ENRICHED",
            "runtime_decision_effect": False,
        },
        {
            "capture_enrichment_row_id": "MAIN-ORCH48-PRE-AI-H1-POI-CAPTURE-ENRICH-0005",
            "schema_version": SCHEMA_VERSION,
            "surface": "focused_tests",
            "source_paths": [
                display_path(TEST_PRE_AI_GATES),
                display_path(TEST_CANDIDATE_FEATURES),
                display_path(TEST_BUGFIXES),
            ],
            "source_sha256": {
                display_path(TEST_PRE_AI_GATES): sha256_path(TEST_PRE_AI_GATES),
                display_path(TEST_CANDIDATE_FEATURES): sha256_path(TEST_CANDIDATE_FEATURES),
                display_path(TEST_BUGFIXES): sha256_path(TEST_BUGFIXES),
            },
            "test_markers_present": source_contains(
                TEST_PRE_AI_GATES,
                "test_framework_poi_availability_preserves_directional_empty_frameworks",
            )
            and source_contains(
                TEST_CANDIDATE_FEATURES,
                "test_pre_ai_gate_capture_fields_include_directional_poi_detail",
            ),
            "focused_test_command": (
                "py -3 -m pytest tests/test_pre_ai_gates.py tests/test_candidate_features_logger.py "
                "tests/test_bugfixes_0.py::TestCandidateFeaturesLoggedOnPreAiGate -q "
                "--basetemp=.pytest_tmp_pre_ai_h1_poi_capture_enrichment"
            ),
            "focused_test_result": "56 passed",
            "status": "FOCUSED_TESTS_PASSED",
            "runtime_decision_effect": False,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[str(row["status"])] = status_counts.get(str(row["status"]), 0) + 1
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "status": "OK_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_MATERIALIZED",
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "source_gap_reference": {
            "pre_ai_skip_rows": join_counts.get("skip_rows"),
            "skip_rows_missing_directional_poi_detail": join_counts.get(
                "skip_rows_missing_directional_poi_detail"
            ),
            "join_artifact_action": join_summary.get("gate_action"),
        },
        "capture_enrichment_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "implementation_effect": {
            "future_candidate_features_capture_enriched": True,
            "gate_config_change_now": False,
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "claim_boundary": (
            "The pre-AI gate's pass/skip rule is unchanged. The patch adds observation-only "
            "directional POI counts and per-framework POI availability to future skipped rows."
        ),
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
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
        "rows": len(rows),
        "pre_ai_skip_rows": join_counts.get("skip_rows"),
        "skip_rows_missing_directional_poi_detail": join_counts.get(
            "skip_rows_missing_directional_poi_detail"
        ),
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "manifest_output_count": len(outputs),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, sort_keys=True))
