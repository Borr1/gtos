#!/usr/bin/env python3
"""Verify current Wave D clean-label source exhaustion artifacts."""

from __future__ import annotations

import errno
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent

REQUIRED_FILES = [
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
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_write_json(path: Path, data: Any) -> None:
    stable_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    issues: list[dict[str, Any]] = []

    def issue(check: str, message: str, **details: Any) -> None:
        issues.append({"check": check, "message": message, **details})

    missing = [name for name in REQUIRED_FILES if not (ROUTE / name).exists()]
    if missing:
        issue("required_files", "required route files are missing", missing=missing)

    summary = read_json(ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_EXHAUSTION_SUMMARY.json")
    gate = read_json(ROUTE / "WAVE_D_MODEL_TRAINING_GATE.json")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")
    source_rows = read_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_SOURCE_STATUS_LEDGER.jsonl")
    label_rows = read_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_FAMILY_LEDGER.jsonl")
    capture_rows = read_jsonl(ROUTE / "WAVE_D_CLEAN_LABEL_CAPTURE_REQUIREMENT_LEDGER.jsonl")

    expected = {
        "label_family_rows": 10,
        "training_ready_label_count": 0,
        "blocked_label_count": 10,
        "hydrated_selector_rows": 289928,
        "wfv003_label_rows": 877,
        "wfv003_exact_candidate_id_matches": 0,
        "wfv003_exact_symbol_side_time_matches": 0,
        "broker_actual_r_joined_rows": 0,
        "close_side_all_in_cost_joined_rows": 0,
        "parent_wave_d_training_ready_label_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            issue("summary_count", "summary count mismatch", key=key, value=summary.get(key), expected=value)
    if len(label_rows) != 10:
        issue("label_rows", "label family ledger count mismatch", rows=len(label_rows))
    if any(row.get("training_ready") is not False for row in label_rows):
        issue("training_ready", "a label family is marked training-ready")
    if len(capture_rows) != summary.get("capture_requirement_rows"):
        issue("capture_rows", "capture requirement row count mismatch", rows=len(capture_rows))
    if len(capture_rows) < 35:
        issue("capture_rows", "capture requirement matrix is unexpectedly small", rows=len(capture_rows))

    source_status = {row.get("source_id"): row.get("read_status") for row in source_rows}
    not_readable = {key: value for key, value in source_status.items() if value != "readable_json"}
    if not_readable:
        issue("source_status", "input source was not readable JSON", not_readable=not_readable)

    terminal = summary.get("terminal_decision") or {}
    if terminal.get("psr012_current_local_sources_exhausted") is not True:
        issue("terminal", "PSR012 exhaustion flag is not true")
    for key in [
        "clean_no_leak_training_dataset_available",
        "model_training_allowed",
        "deterministic_baseline_comparison_allowed",
        "final_package_selected",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
    ]:
        if terminal.get(key) is not False:
            issue("terminal", "terminal flag is not false", key=key, value=terminal.get(key))

    if gate.get("model_training_allowed") is not False:
        issue("model_gate", "model training gate allows training")
    if gate.get("model_registry_proposal_allowed") is not False:
        issue("model_gate", "model gate allows registry proposal")
    if focused.get("ok") is not True:
        issue("focused", "focused result is not ok")
    if completion.get("goal_completion_claim") is not False:
        issue("completion", "completion audit claims goal completion")
    forbidden = summary.get("forbidden_surface_status") or {}
    crossed = sorted(key for key, value in forbidden.items() if value is not False)
    if crossed:
        issue("forbidden", "forbidden surface crossed", crossed=crossed)

    manifest_files = set(manifest.get("files") or [])
    manifest_missing = sorted(name for name in REQUIRED_FILES + ["VERIFICATION_RESULT.json"] if name not in manifest_files)
    if manifest_missing:
        issue("manifest", "manifest missing expected files", missing=manifest_missing)

    result = {
        "schema": "gtos.final_moonshot.wave_d.clean_label_source_exhaustion.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "label_family_rows": len(label_rows),
        "training_ready_label_count": summary.get("training_ready_label_count"),
        "capture_requirement_rows": len(capture_rows),
        "hydrated_selector_rows": summary.get("hydrated_selector_rows"),
        "wfv003_label_rows": summary.get("wfv003_label_rows"),
        "broker_actual_r_joined_rows": summary.get("broker_actual_r_joined_rows"),
        "close_side_all_in_cost_joined_rows": summary.get("close_side_all_in_cost_joined_rows"),
        "terminal_decision": terminal,
        "forbidden_surface_status": forbidden,
    }
    stable_write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
