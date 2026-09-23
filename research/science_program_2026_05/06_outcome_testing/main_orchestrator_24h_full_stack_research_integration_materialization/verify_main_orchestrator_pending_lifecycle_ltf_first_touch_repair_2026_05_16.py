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


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def resolve_manifest_path(path_text: str, section: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    if section == "input_artifacts":
        return REPO_ROOT / path
    return ROUTE_DIR / path


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_pending_lifecycle_ltf_first_touch_repair_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    first_touch_repair_rows = [
        row for row in rows if row.get("first_touch_source_repair_count", 0) > 0
    ]
    internal_rows = [
        row
        for row in rows
        if isinstance(row.get("after_source_capture_statuses"), dict)
        and row.get("after_source_capture_statuses")
    ]

    checks.append(
        check(
            "route_id_matches",
            summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID,
        )
    )
    checks.append(
        check(
            "safe_flags_closed",
            summary.get("safe_flags") == SAFE_FLAGS
            and manifest.get("safe_flags") == SAFE_FLAGS
            and all(row.get("safe_flags") == SAFE_FLAGS for row in rows),
        )
    )
    checks.append(check("row_count_matches_summary", len(rows) == summary.get("rows"), len(rows)))
    checks.append(
        check(
            "candidate_count_matches_summary",
            len({row.get("candidate_id") for row in rows}) == summary.get("candidate_rows"),
        )
    )
    checks.append(
        check(
            "internal_rows_match_summary",
            len(internal_rows) == summary.get("internal_pending_lifecycle_rows") == 39,
            len(internal_rows),
        )
    )
    checks.append(
        check(
            "exact_r_rows_zero",
            summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in rows),
        )
    )
    checks.append(
        check(
            "proxy_r_unchanged_from_previous_derivation_plate",
            len(before_values) == len(after_values) == summary.get("before_numeric_proxy_rows")
            == summary.get("after_numeric_proxy_rows")
            and summary.get("numeric_proxy_row_delta") == 0
            and round(sum(before_values), 10) == round(sum(after_values), 10)
            and round(float(summary.get("proxy_r_sum_delta")), 10) == 0.0,
            {
                "before_count": len(before_values),
                "after_count": len(after_values),
                "before_sum": sum(before_values),
                "after_sum": sum(after_values),
            },
        )
    )
    checks.append(
        check(
            "source_field_counts_not_degraded",
            summary.get("derived_source_field_cell_delta", 0) >= 0
            and summary.get("missing_source_field_cell_delta", 0) <= 0
            and summary.get("after_derived_source_field_cells") >= summary.get(
                "previous_derived_source_field_cells"
            )
            and summary.get("after_missing_source_field_cells") <= summary.get(
                "previous_missing_source_field_cells"
            ),
            {
                "derived_delta": summary.get("derived_source_field_cell_delta"),
                "missing_delta": summary.get("missing_source_field_cell_delta"),
            },
        )
    )
    checks.append(
        check(
            "current_ltf_first_touch_delta_classified",
            (
                summary.get("first_touch_source_repair_rows") == len(first_touch_repair_rows) > 0
                and summary.get("plate_decision")
                == "PENDING_LIFECYCLE_LTF_FIRST_TOUCH_SOURCE_REPAIR_IMPLEMENTED_PROXY_R_UNCHANGED"
            )
            or (
                summary.get("first_touch_source_repair_rows") == len(first_touch_repair_rows) == 0
                and summary.get("plate_decision")
                == "PENDING_LIFECYCLE_LTF_FIRST_TOUCH_SOURCE_REPAIR_NO_CURRENT_ROW_DELTA"
            ),
            {
                "first_touch_repair_rows": len(first_touch_repair_rows),
                "plate_decision": summary.get("plate_decision"),
            },
        )
    )
    checks.append(
        check(
            "branch_decisions_cover_all_rows",
            sum(summary.get("branch_decision_counts", {}).values()) == len(rows)
            and all(row.get("branch_decision") for row in rows),
            summary.get("branch_decision_counts"),
        )
    )
    checks.append(
        check(
            "no_live_or_shadow_append",
            all(row.get("no_live_behavior") is True and row.get("no_shadow_log_append") is True for row in rows),
        )
    )
    checks.append(
        check(
            "implementation_decisions_cover_all_rows",
            sum(summary.get("implementation_decision_counts", {}).values()) == len(rows)
            and all(row.get("implementation_decision") for row in rows),
            summary.get("implementation_decision_counts"),
        )
    )

    manifest_errors = []
    for section in ("input_artifacts", "output_artifacts"):
        for path_text, artifact in manifest.get(section, {}).items():
            path = resolve_manifest_path(path_text, section)
            if not path.exists():
                manifest_errors.append({"path": path_text, "error": "missing"})
                continue
            if artifact.get("sha256") != sha256(path):
                manifest_errors.append({"path": path_text, "error": "sha256_mismatch"})
            if artifact.get("size_bytes") != path.stat().st_size:
                manifest_errors.append({"path": path_text, "error": "size_mismatch"})
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
            "rows": len(rows),
            "candidate_rows": len({row.get("candidate_id") for row in rows}),
            "internal_pending_lifecycle_rows": len(internal_rows),
            "before_numeric_proxy_rows": len(before_values),
            "after_numeric_proxy_rows": len(after_values),
            "first_touch_source_repair_rows": len(first_touch_repair_rows),
            "branch_decision_counts": summary.get("branch_decision_counts"),
            "implementation_decision_counts": summary.get("implementation_decision_counts"),
        },
        "plate_decision": summary.get("plate_decision"),
        "can_mark_pending_lifecycle_ltf_first_touch_repair_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
