from __future__ import annotations

import hashlib
import json
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def main() -> None:
    input_snapshot_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_INPUT_SNAPSHOT_{DATE}.json"
    field_contract_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_FIELD_CONTRACT_{DATE}.json"
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_IMPLEMENTATION_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_IMPLEMENTATION_SUMMARY_{DATE}.md"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_CAPTURE_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [input_snapshot_path, field_contract_path, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    input_snapshot = read_json(input_snapshot_path)
    field_contract = read_json(field_contract_path)
    ledger_rows = read_jsonl(ledger_path)
    manifest = read_json(manifest_path)
    summary = summary_path.read_text(encoding="utf-8", errors="replace")

    checks.append(check("route_id_matches", input_snapshot.get("route_id") == ROUTE_ID and field_contract.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_preserved", input_snapshot.get("safe_flags") == SAFE_FLAGS and field_contract.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("all_new_fields_listed", field_contract.get("new_source_safe_fields") == NEW_SOURCE_SAFE_FIELDS))
    checks.append(check("ledger_row_count_4", len(ledger_rows) == 4, len(ledger_rows)))
    checks.append(check("focused_tests_recorded_pass", any(row.get("focused_test_result") == "31 passed in 5.07s" for row in ledger_rows)))
    checks.append(check("implementation_commit_recorded", input_snapshot.get("implementation_commit") == "f54a0e09"))
    checks.append(check("summary_says_no_live_effect", "No trade placement" in summary and "live-effect change" in summary))

    presence = field_contract.get("field_presence", {})
    missing_presence = [
        field for field in NEW_SOURCE_SAFE_FIELDS if field not in presence or not presence[field].get("logger_required_field")
    ]
    checks.append(check("logger_required_fields_present", not missing_presence, missing_presence))

    code_text = {
        "logger": (REPO_ROOT / "src/components/pending_limit_lifecycle_logger.py").read_text(encoding="utf-8", errors="replace"),
        "execution": (REPO_ROOT / "src/components/execution.py").read_text(encoding="utf-8", errors="replace"),
        "tests": (REPO_ROOT / "tests/test_pending_limit_lifecycle_logger.py").read_text(encoding="utf-8", errors="replace"),
    }
    execution_expected_fields = [
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "decision_spread_value_source_safe",
        "decision_spread_unit",
        "entry_touch_spread_value_source_safe",
        "entry_touch_spread_unit",
        "terminal_area_first_touch_utc",
        "protective_area_first_touch_utc",
    ]
    tests_expected_fields = [
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_reason_status",
        "entry_touch_spread_value_source_safe",
        "entry_touch_spread_unit",
        "terminal_area_touch_status",
        "protective_area_touch_status",
        "event_order_resolution_method",
    ]
    missing_in_execution = [field for field in execution_expected_fields if field not in code_text["execution"]]
    missing_in_tests = [field for field in tests_expected_fields if field not in code_text["tests"]]
    checks.append(check("execution_emits_source_observed_subset", not missing_in_execution, missing_in_execution))
    checks.append(check("tests_cover_schema_and_observed_subset", not missing_in_tests, missing_in_tests))

    manifest_errors = []
    for artifact in manifest.get("artifacts", []):
        path = REPO_ROOT / artifact["path"]
        if not path.exists():
            manifest_errors.append({"path": artifact["path"], "error": "missing"})
            continue
        if path.stat().st_size != artifact.get("size_bytes"):
            manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
        actual = sha256(path)
        if actual != artifact.get("sha256"):
            manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))
    checks.append(check("can_mark_active_24h_goal_complete_false", True, False))

    result = {
        "route_id": ROUTE_ID,
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "counts": {
            "new_source_safe_fields": len(NEW_SOURCE_SAFE_FIELDS),
            "ledger_rows": len(ledger_rows),
            "manifest_artifacts": len(manifest.get("artifacts", [])),
        },
        "can_mark_pending_lifecycle_source_capture_plate_complete": all(item["ok"] for item in checks),
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
