#!/usr/bin/env python3
"""Verify Wave F order-type/fillability join exhaustion artifacts."""

from __future__ import annotations

import errno
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "build_wave_f_order_type_fillability_join_exhaustion.py",
    "verify_wave_f_order_type_fillability_join_exhaustion.py",
    "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json",
    "WAVE_F_ORDER_TYPE_FILLABILITY_SOURCE_STATUS_LEDGER.jsonl",
    "WAVE_F_SELECTOR_MAY_KEYSPACE_LEDGER.jsonl",
    "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_LEDGER.jsonl",
    "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl",
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
        issue("required_files", "required files are missing", missing=missing)

    summary = read_json(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_SUMMARY.json")
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")
    source_rows = read_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_SOURCE_STATUS_LEDGER.jsonl")
    selector_may_rows = read_jsonl(ROUTE / "WAVE_F_SELECTOR_MAY_KEYSPACE_LEDGER.jsonl")
    join_rows = read_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_JOIN_EXHAUSTION_LEDGER.jsonl")
    requirement_rows = read_jsonl(ROUTE / "WAVE_F_ORDER_TYPE_FILLABILITY_CAPTURE_REQUIREMENT_LEDGER.jsonl")
    decision_rows = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repair_rows = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")

    expected_counts = {
        "label_rows": 877,
        "labels_with_decision_time": 428,
        "selector_rows": 289928,
        "selector_may_2026_context_rows": 622,
        "exact_candidate_id_selector_matches": 0,
        "exact_symbol_side_time_selector_label_matches": 0,
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            issue("summary_count", "summary count mismatch", key=key, value=summary.get(key), expected=expected)
        if focused.get(key) not in (expected, None):
            issue("focused_count", "focused count mismatch", key=key, value=focused.get(key), expected=expected)

    if len(join_rows) != summary.get("label_rows"):
        issue("join_ledger_count", "join ledger row count mismatch", rows=len(join_rows))
    if len(selector_may_rows) != summary.get("selector_may_2026_context_rows"):
        issue("selector_context_count", "selector May context row count mismatch", rows=len(selector_may_rows))
    if len(requirement_rows) < 4:
        issue("requirements", "capture requirement ledger is too small", rows=len(requirement_rows))
    if not decision_rows or not repair_rows:
        issue("decision_repair_ledgers", "decision or repair ledger is empty")

    if any(row.get("candidate_id_selector_exact_match") for row in join_rows):
        issue("candidate_join", "candidate exact matches unexpectedly present")
    if any(row.get("symbol_side_time_selector_exact_match_rows") for row in join_rows):
        issue("symbol_time_join", "exact symbol/side/time matches unexpectedly present")
    if any(row.get("current_denominator_inclusion_allowed") is not False for row in join_rows):
        issue("denominator_authority", "join row allows current denominator inclusion")
    if any(row.get("model_training_allowed") is not False for row in join_rows):
        issue("model_authority", "join row allows model training")
    if any(row.get("final_package_selection_allowed") is not False for row in join_rows):
        issue("final_selection_authority", "join row allows final package selection")
    if any(row.get("direct_execution_authority") is not False for row in join_rows):
        issue("execution_authority", "join row carries direct execution authority")

    source_status = {row.get("source_id"): row.get("read_status") for row in source_rows}
    if source_status.get("wave_f_row_bound_fillability_label_repair") != "readable":
        issue("source_status", "fillability label source is not readable", source_status=source_status)
    if source_status.get("hydrated_selector_candidate_replay_lift") != "readable":
        issue("source_status", "hydrated selector source is not readable", source_status=source_status)

    terminal = summary.get("terminal_decision") or {}
    for key in [
        "current_denominator_fillability_inclusion_allowed",
        "model_training_allowed",
        "broker_real_execution_claim_allowed",
        "final_package_selected",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "wave_f_complete",
    ]:
        if terminal.get(key) is not False:
            issue("terminal_decision", "terminal flag is not false", key=key, value=terminal.get(key))
    if terminal.get("wfv003_current_local_hydrated_selector_join_exhausted") is not True:
        issue("terminal_decision", "join exhaustion flag is not true")

    forbidden = summary.get("forbidden_surface_status") or {}
    forbidden_true = sorted(key for key, value in forbidden.items() if value is not False)
    if forbidden_true:
        issue("forbidden_surfaces", "forbidden surfaces crossed", keys=forbidden_true)
    if completion.get("goal_completion_claim") is not False:
        issue("completion_audit", "completion audit claims goal completion")

    manifest_files = set(manifest.get("files") or [])
    manifest_missing = sorted(name for name in REQUIRED_FILES + ["VERIFICATION_RESULT.json"] if name not in manifest_files)
    if manifest_missing:
        issue("manifest", "manifest missing required files", missing=manifest_missing)

    dispositions = summary.get("join_disposition_counts") or {}
    if dispositions.get("weekly_context_only_not_denominator_join") != 237:
        issue("dispositions", "weekly context disposition count drifted", dispositions=dispositions)
    if dispositions.get("missing_decision_time_exact_capture_required") != 449:
        issue("dispositions", "missing decision-time disposition count drifted", dispositions=dispositions)

    result = {
        "schema": "gtos.final_moonshot.wave_f.order_type_fillability_join_exhaustion.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "label_rows": len(join_rows),
        "selector_rows": summary.get("selector_rows"),
        "selector_may_2026_context_rows": len(selector_may_rows),
        "exact_candidate_id_selector_matches": summary.get("exact_candidate_id_selector_matches"),
        "exact_symbol_side_time_selector_label_matches": summary.get("exact_symbol_side_time_selector_label_matches"),
        "weekly_context_only_not_denominator_join": dispositions.get("weekly_context_only_not_denominator_join"),
        "missing_decision_time_exact_capture_required": dispositions.get("missing_decision_time_exact_capture_required"),
        "terminal_decision": terminal,
        "forbidden_surface_status": forbidden,
    }
    stable_write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
