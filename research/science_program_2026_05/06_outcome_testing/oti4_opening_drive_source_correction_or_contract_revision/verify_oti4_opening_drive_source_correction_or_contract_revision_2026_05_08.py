#!/usr/bin/env python3
"""Verify OTI4 opening-drive source-correction / contract-revision artifacts."""

from __future__ import annotations

import hashlib
import json
import py_compile
import tempfile
from pathlib import Path


DATE = "2026-05-08"
OUT = Path(__file__).resolve().parent


def read_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    build_script = OUT / "build_oti4_opening_drive_source_correction_or_contract_revision_2026_05_08.py"
    test_file = OUT / "test_oti4_opening_drive_source_correction_or_contract_revision_2026_05_08.py"
    with tempfile.TemporaryDirectory(prefix="oti4_pycompile_") as pyc_dir:
        py_compile.compile(str(build_script), cfile=str(Path(pyc_dir) / "build.pyc"), doraise=True)
        py_compile.compile(str(test_file), cfile=str(Path(pyc_dir) / "test.pyc"), doraise=True)

    completion = read_json(f"OTI4_OPENING_DRIVE_COMPLETION_AUDIT_{DATE}.json")
    packet = read_json(f"OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_{DATE}.json")
    source_audit = read_json(f"OTI4_OPENING_DRIVE_SOURCE_HASH_ASOF_DUPLICATE_AUDIT_{DATE}.json")
    search = read_json(f"OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_{DATE}.json")
    rows_path = OUT / f"OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_{DATE}.jsonl"
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    issues: list[str] = []
    if not completion.get("can_mark_goal_complete"):
        issues.append("completion audit does not allow completion")
    if completion.get("row_count") != 80 or packet.get("row_count") != 80 or len(rows) != 80:
        issues.append("80-row coverage failed")
    if completion.get("proof_status_counts") != {
        "EXACT_IMPOSSIBILITY_OR_SOURCE_BLOCKER": 11,
        "SOURCE_HASHED_RANGE_BREAKOUT_ASOF_PROOF": 69,
    }:
        issues.append("proof status counts changed")
    if completion.get("row_route_decision_counts") != {
        "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": 12,
        "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": 8,
        "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": 6,
        "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": 51,
        "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": 3,
    }:
        issues.append("route decision counts changed")
    if source_audit.get("source_hash_mismatch_count") != 0 or search.get("source_hash_mismatch_count") != 0:
        issues.append("source hash mismatch detected")
    if source_audit.get("asof_failure_count_for_source_corrected_rows") != 0:
        issues.append("as-of failure detected in source-corrected rows")
    if not source_audit.get("all_rows_have_proof_or_exact_blocker"):
        issues.append("some rows lack proof or exact blocker")

    for artifact in [completion, packet, source_audit, search]:
        if artifact.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append(f"{artifact.get('artifact_family')} promotion verdict changed")
        if artifact.get("validation_safe") is not False:
            issues.append(f"{artifact.get('artifact_family')} validation_safe changed")
        if artifact.get("outcome_review_opened") is not False:
            issues.append(f"{artifact.get('artifact_family')} outcome_review_opened changed")
        if artifact.get("live_effect") is not False:
            issues.append(f"{artifact.get('artifact_family')} live_effect changed")

    for record in search.get("source_hash_records", []):
        if not record.get("strict_recompute_required", True):
            continue
        path = Path(record["path"])
        if not path.exists():
            issues.append(f"missing source hash path: {path}")
            continue
        if sha256_file(path) != record.get("expected_sha256"):
            issues.append(f"source hash recompute mismatch: {path}")

    output_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in OUT.glob(f"OTI4_OPENING_DRIVE_*_{DATE}.json*"))
    forbidden_positive_fragments = [
        '"validation_safe": true',
        '"outcome_review_opened": true',
        '"live_effect": true',
        '"result_label_assigned": true',
        '"broker_actual_r_inspected": true',
        '"account_history_inspected": true',
        '"live_order_deal_position_labels_inspected": true',
        '"paid_network_api_databento_mt5_calls": true',
        '"outcome_scoring_run": true',
    ]
    for term in forbidden_positive_fragments:
        if term in output_text:
            issues.append(f"forbidden positive-use fragment present: {term}")

    result = {
        "verification_status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "can_mark_goal_complete": not issues,
        "row_count": len(rows),
        "completion_artifact": f"OTI4_OPENING_DRIVE_COMPLETION_AUDIT_{DATE}.json",
    }
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
