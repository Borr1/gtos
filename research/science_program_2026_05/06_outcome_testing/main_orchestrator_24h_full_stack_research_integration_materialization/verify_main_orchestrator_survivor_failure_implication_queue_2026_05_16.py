from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
NO_TAG = "NO_SYSTEM_IMPLICATION_TAG"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


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
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def source_tags(row: dict[str, Any]) -> list[str]:
    tags = row.get("evidence", {}).get("system_implication_tags") or []
    normalized = [str(tag) for tag in tags if str(tag).strip()]
    return normalized or [NO_TAG]


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_survivor_failure_implication_queue_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    source_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl"
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, source_path, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    source_rows = read_jsonl(source_path)
    output_rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    source_output_rows = [row for row in output_rows if row.get("row_type") == "SOURCE_DECISION_ROW"]
    tag_rows = [row for row in output_rows if row.get("row_type") == "TAG_AGGREGATE_ROW"]
    source_decision_ids = [str(row.get("decision_id")) for row in source_rows]
    output_source_decision_ids = [str(row.get("source_decision_id")) for row in source_output_rows]
    tag_counts = Counter(tag for row in source_rows for tag in source_tags(row))
    expected_tags = set(tag_counts)
    actual_tags = {str(row.get("implication_tag")) for row in tag_rows}

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_preserved", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("source_row_count_preserved", len(source_rows) == len(source_output_rows) == 915, len(source_output_rows)))
    checks.append(check("output_ledger_row_count_matches_summary", summary.get("output_ledger_rows") == len(output_rows)))
    checks.append(check("source_decision_ids_preserved_once", Counter(source_decision_ids) == Counter(output_source_decision_ids)))
    checks.append(check("tag_aggregate_set_complete", expected_tags == actual_tags, {"expected": sorted(expected_tags), "actual": sorted(actual_tags)}))
    checks.append(
        check(
            "tag_assignment_count_matches_summary",
            summary.get("tag_assignments_including_no_tag_group") == sum(tag_counts.values()),
            {"summary": summary.get("tag_assignments_including_no_tag_group"), "actual": sum(tag_counts.values())},
        )
    )
    checks.append(
        check(
            "no_tag_group_matches_summary",
            summary.get("source_rows_without_system_implication_tags") == tag_counts.get(NO_TAG, 0) == 143,
            {"summary": summary.get("source_rows_without_system_implication_tags"), "actual": tag_counts.get(NO_TAG, 0)},
        )
    )
    checks.append(
        check(
            "unique_tag_count_matches_summary",
            summary.get("unique_system_implication_tags") == len([tag for tag in tag_counts if tag != NO_TAG]) == 30,
            summary.get("unique_system_implication_tags"),
        )
    )

    aggregate_errors: list[dict[str, Any]] = []
    for row in tag_rows:
        tag = str(row.get("implication_tag"))
        if row.get("source_decision_rows") != tag_counts.get(tag, 0):
            aggregate_errors.append(
                {"tag": tag, "summary_count": row.get("source_decision_rows"), "actual": tag_counts.get(tag, 0)}
            )
    checks.append(check("aggregate_tag_counts_match_source", not aggregate_errors, aggregate_errors))

    summary_bucket_counts = summary.get("bucket_counts", {})
    actual_bucket_counts = dict(
        sorted(Counter(str(row.get("bucket") if row.get("bucket") is not None else "MISSING") for row in source_rows).items())
    )
    checks.append(check("bucket_counts_match_source", summary_bucket_counts == actual_bucket_counts, actual_bucket_counts))

    manifest_errors: list[dict[str, Any]] = []
    for section in ("artifacts", "input_artifacts"):
        for artifact in manifest.get(section, []):
            path = REPO_ROOT / artifact["path"]
            if not artifact.get("exists"):
                if artifact.get("sha256") is not None:
                    manifest_errors.append({"path": artifact["path"], "error": "missing_with_hash"})
                continue
            if not path.exists():
                manifest_errors.append({"path": artifact["path"], "error": "missing"})
                continue
            if path.stat().st_size != artifact.get("size_bytes"):
                manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
            actual = sha256(path)
            if actual != artifact.get("sha256"):
                manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "source_decision_rows": len(source_rows),
            "source_row_output_rows": len(source_output_rows),
            "tag_aggregate_rows": len(tag_rows),
            "output_ledger_rows": len(output_rows),
            "unique_system_implication_tags": len([tag for tag in tag_counts if tag != NO_TAG]),
            "source_rows_without_system_implication_tags": tag_counts.get(NO_TAG, 0),
            "tag_assignments_including_no_tag_group": sum(tag_counts.values()),
        },
        "can_mark_survivor_failure_implication_queue_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
