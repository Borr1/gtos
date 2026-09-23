"""Verify the 0.50R entry-offset candidate decision artifacts."""

from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
BUILDER = ROUTE_DIR / "build_main_orchestrator_entry_offset_050r_candidate_decisions_2026_05_16.py"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "KEEP": 177,
    "SOURCE_REPAIR": 2,
    "IMPLEMENT_DEFAULT_OFF": 3,
    "REDESIGN": 10,
    "KILL": 82,
}
EXPECTED_BRANCH_COUNTS = {
    "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_ENTRY_REDESIGN_DENOMINATOR": 177,
    "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER": 2,
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER": 3,
    "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL": 10,
    "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL": 82,
}
EXPECTED_BUCKET_COUNTS = {
    "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW": 177,
    "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE": 94,
    "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE": 3,
}
EXPECTED_TICK_SOURCE_COUNTS = {
    "NOT_REQUIRED_FOR_NON_REDESIGN_ROW": 177,
    "TICK_REPLAY_SOURCE_COMPLETE": 95,
    "TICK_SOURCE_INCOMPLETE_BAD_PARQUET": 2,
}
EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def approx_equal(left: float | None, right: float | None, tol: float = 1e-9) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tol


def assert_ast_parse(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing python artifact: {path.name}")
        return
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        errors.append(f"syntax parse failed for {path.name}: {exc}")


def main() -> None:
    errors: list[str] = []

    for path in [BUILDER, LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    assert_ast_parse(BUILDER, errors)
    assert_ast_parse(Path(__file__), errors)

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != 274:
        errors.append(f"expected 274 decision rows, got {len(rows)}")
    if summary.get("rows") != len(rows):
        errors.append(f"summary row mismatch: {summary.get('rows')} vs {len(rows)}")
    if summary.get("candidate_rows") != 274:
        errors.append(f"expected 274 candidate rows, got {summary.get('candidate_rows')}")
    if len({row.get("candidate_id") for row in rows}) != 274:
        errors.append("candidate ids are not unique across the decision ledger")
    if summary.get("affected_entry_redesign_rows") != 97:
        errors.append(f"expected 97 affected entry redesign rows, got {summary.get('affected_entry_redesign_rows')}")
    if summary.get("exact_r_rows") != 0 or any(row.get("exact_r") is not None for row in rows):
        errors.append("exact_r must remain absent for this proxy-R decision plate")

    action_counts = Counter(str(row.get("action_class")) for row in rows)
    branch_counts = Counter(str(row.get("branch_decision")) for row in rows)
    bucket_counts = Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)
    tick_counts = Counter(str(row.get("tick_source_status")) for row in rows)
    if dict(action_counts) != EXPECTED_ACTION_COUNTS:
        errors.append(f"action counts mismatch: {dict(action_counts)}")
    if summary.get("action_class_counts") != EXPECTED_ACTION_COUNTS:
        errors.append(f"summary action counts mismatch: {summary.get('action_class_counts')}")
    if dict(branch_counts) != EXPECTED_BRANCH_COUNTS:
        errors.append(f"branch decision counts mismatch: {dict(branch_counts)}")
    if summary.get("branch_decision_counts") != EXPECTED_BRANCH_COUNTS:
        errors.append(f"summary branch decision counts mismatch: {summary.get('branch_decision_counts')}")
    if dict(bucket_counts) != EXPECTED_BUCKET_COUNTS:
        errors.append(f"bucket counts mismatch: {dict(bucket_counts)}")
    if dict(tick_counts) != EXPECTED_TICK_SOURCE_COUNTS:
        errors.append(f"tick source counts mismatch: {dict(tick_counts)}")
    if summary.get("tick_source_status_counts") != EXPECTED_TICK_SOURCE_COUNTS:
        errors.append(f"summary tick source counts mismatch: {summary.get('tick_source_status_counts')}")

    selected = [row for row in rows if safe_float(row.get("selected_shift_proxy_r")) is not None]
    selected_sum = sum(float(row["selected_shift_proxy_r"]) for row in selected)
    if len(selected) != 13:
        errors.append(f"expected 13 selected 0.50R proxy rows, got {len(selected)}")
    if not approx_equal(selected_sum, 8.66977687):
        errors.append(f"selected proxy-R sum mismatch: {selected_sum}")
    if summary.get("selected_shift_numeric_proxy_rows") != 13:
        errors.append("summary selected proxy row count mismatch")
    if not approx_equal(safe_float(summary.get("selected_shift_proxy_r_sum")), 8.66977687):
        errors.append(f"summary selected proxy-R sum mismatch: {summary.get('selected_shift_proxy_r_sum')}")

    implement_rows = [row for row in rows if row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"]
    redesign_rows = [row for row in rows if row.get("action_class") == "REDESIGN"]
    kill_rows = [row for row in rows if row.get("action_class") == "KILL"]
    source_repair_rows = [row for row in rows if row.get("action_class") == "SOURCE_REPAIR"]
    if any(row.get("entry_retest_redesign_bucket") != "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE" for row in implement_rows):
        errors.append("default-off implementation rows must be near-miss rows")
    if any(row.get("selected_shift_r") != 0.5 or row.get("selected_shift_status") != "TP1_AFTER_SHIFT_FILL" for row in implement_rows):
        errors.append("default-off implementation rows must select a 0.50R TP-after-fill shift")
    if any(row.get("entry_retest_redesign_bucket") != "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE" for row in redesign_rows):
        errors.append("redesign rows must be far-miss rows")
    if any(row.get("selected_shift_r") != 0.5 or row.get("selected_shift_status") != "TP1_AFTER_SHIFT_FILL" for row in redesign_rows):
        errors.append("redesign rows must select a 0.50R TP-after-fill shift")
    if any(row.get("shift_050_status") != "NO_FILL_AT_SHIFT" for row in kill_rows):
        errors.append("kill rows must be 0.50R no-fill rows")
    if any(row.get("tick_source_status") != "TICK_SOURCE_INCOMPLETE_BAD_PARQUET" for row in source_repair_rows):
        errors.append("source repair rows must be the bad-parquet tick-source rows")

    tick_complete_affected = [
        row
        for row in rows
        if row.get("entry_retest_redesign_bucket")
        in {"NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE", "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"}
        and row.get("tick_source_status") == "TICK_REPLAY_SOURCE_COMPLETE"
    ]
    if len(tick_complete_affected) != 95:
        errors.append(f"expected 95 tick-complete affected rows, got {len(tick_complete_affected)}")
    if any(row.get("shift_025_status") != "NO_FILL_AT_SHIFT" for row in tick_complete_affected):
        errors.append("0.25R shift must be killed as no-fill for all tick-complete affected rows")

    if any(row.get("safe_flags") != EXPECTED_SAFE_FLAGS for row in rows):
        errors.append("row safe flags mismatch")
    if summary.get("safe_flags") != EXPECTED_SAFE_FLAGS or manifest.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        errors.append("summary or manifest safe flags mismatch")
    if any(row.get("no_shadow_log_append") is not True for row in rows):
        errors.append("decision rows must not append to shadow logs")
    if any(row.get("no_live_behavior") is not True for row in rows):
        errors.append("decision rows must not open live behavior")

    for group_name in ("inputs", "outputs"):
        for name, artifact in (manifest.get(group_name) or {}).items():
            path = Path(str(artifact.get("path") or ""))
            if not path.exists():
                errors.append(f"manifest {group_name} path missing: {name}")
                continue
            if artifact.get("bytes") != path.stat().st_size:
                errors.append(f"manifest byte mismatch: {name}")
            if artifact.get("sha256") != sha256_file(path):
                errors.append(f"manifest hash mismatch: {name}")

    result = {
        "ok": not errors,
        "errors": errors,
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "action_class_counts": dict(action_counts),
        "branch_decision_counts": dict(branch_counts),
        "bucket_counts": dict(bucket_counts),
        "tick_source_status_counts": dict(tick_counts),
        "selected_shift_numeric_proxy_rows": len(selected),
        "selected_shift_proxy_r_sum": selected_sum,
        "terminal_decision": summary.get("terminal_decision"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
