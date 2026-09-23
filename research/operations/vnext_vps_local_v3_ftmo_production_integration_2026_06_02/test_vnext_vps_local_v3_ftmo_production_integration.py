"""Focused tests for the VPS/local V3/FTMO integration route artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def _jsonl_rows(name: str) -> list[dict]:
    rows: list[dict] = []
    for line in (ROUTE_DIR / name).read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_required_artifacts_are_present_and_parseable() -> None:
    manifest = json.loads((ROUTE_DIR / "OUTPUT_MANIFEST.json").read_text(encoding="utf-8"))
    required = [entry for entry in manifest["entries"] if entry.get("required")]
    missing = [entry["path"] for entry in required if not entry.get("exists")]
    assert not missing

    for name in [
        "BRANCH_BASE_AND_DIVERGENCE_LEDGER.json",
        "RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json",
        "VERIFICATION_MATRIX.json",
        "VERIFICATION_RESULT.json",
        "COMPLETION_AUDIT.json",
    ]:
        assert isinstance(json.loads((ROUTE_DIR / name).read_text(encoding="utf-8-sig")), dict)

    for name in [
        "VPS_PRODUCTION_CHANGE_INVENTORY.jsonl",
        "LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl",
        "CONFLICT_RESOLUTION_LEDGER.jsonl",
        "SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl",
        "redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl",
        "V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
        "RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl",
        "LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl",
    ]:
        assert _jsonl_rows(name)


def test_conflict_and_runtime_disposition_contracts_are_explicit() -> None:
    conflicts = {row["path"]: row for row in _jsonl_rows("CONFLICT_RESOLUTION_LEDGER.jsonl")}
    assert {
        "src/components/execution.py",
        "src/components/m1_capture.py",
        "src/components/tick_capture.py",
    }.issubset(conflicts)
    assert "combine" in conflicts["src/components/execution.py"]["final_resolution"]

    dispositions = {row["component"]: row for row in _jsonl_rows("V3_RUNTIME_DISPOSITION_LEDGER.jsonl")}
    assert dispositions["Selector V3"]["runtime_disposition"] == "default_off_package_preserved"
    assert dispositions["Scheduler V3"]["production_code_effect_now"] is False
    assert dispositions["Execution Policy V3"]["production_code_effect_now"] is False
    assert dispositions["FTMO Dual Production"]["runtime_disposition"] == "staged_deployable_profile_support"


def test_scope_ledger_excludes_runtime_dirt_and_records_lfs_review() -> None:
    scope_rows = _jsonl_rows("LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl")
    by_family = {row["path_family"]: row for row in scope_rows}
    assert by_family["pipeline_state/"]["scope_decision"] == "exclude"
    assert by_family["shadow_logs/"]["scope_decision"] == "exclude_except_tracked_canary_status_deletion"
    assert by_family["actual_staged_runtime_or_large_artifact_scan"]["matched_path_count"] == 0
    assert by_family["git_lfs_ls_files"]["scope_decision"] in {
        "record_pointer_state",
        "tool_unavailable_or_failed",
    }
