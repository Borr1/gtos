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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_pending_lifecycle_source_derivation_recompute_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    internal_rows = [row for row in rows if isinstance(row.get("after_source_capture_statuses"), dict)]
    derived_cells = sum(row["after_status_counts"]["derived_field_count"] for row in internal_rows)

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_matches_summary", len(rows) == summary.get("rows"), len(rows)))
    checks.append(check("candidate_count_matches_summary", len({row.get("candidate_id") for row in rows}) == summary.get("candidate_rows")))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in rows)))
    checks.append(
        check(
            "proxy_r_unchanged",
            len(before_values) == len(after_values) == 197
            and round(sum(before_values), 10) == round(sum(after_values), 10) == 50.0
            and summary.get("numeric_proxy_row_delta") == 0
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
            "current_internal_pending_rows_derivations_materialized",
            len(internal_rows) == 39
            and derived_cells == 323
            and summary.get("after_derived_source_field_cells") == 323
            and summary.get("after_capture_complete_rows") == 0,
            {
                "internal_rows": len(internal_rows),
                "derived_cells": derived_cells,
                "summary": summary.get("after_derived_source_field_cells"),
            },
        )
    )
    required_derived = {
        "pending_horizon_start_utc": 39,
        "pending_horizon_end_utc": 39,
        "cancel_expiry_reason_status": 39,
        "terminal_area_touch_status": 39,
        "protective_area_touch_status": 39,
        "event_order_resolution_method": 39,
        "same_tick_same_bar_ambiguity_status": 39,
    }
    checks.append(
        check(
            "core_pending_derivation_fields_present",
            all(summary.get("derived_field_counts", {}).get(field) == count for field, count in required_derived.items()),
            summary.get("derived_field_counts"),
        )
    )
    checks.append(
        check(
            "decision_counts_expected",
            summary.get("implementation_decision_counts", {}).get(
                "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL"
            )
            == 39
            and summary.get("implementation_decision_counts", {}).get(
                "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER"
            )
            == 235,
            summary.get("implementation_decision_counts"),
        )
    )

    manifest_errors = []
    for section in ("input_artifacts", "output_artifacts"):
        artifacts = manifest.get(section, {})
        for path_text, artifact in artifacts.items():
            path = Path(path_text)
            if not path.is_absolute():
                path = REPO_ROOT / path if section == "input_artifacts" else ROUTE_DIR / path
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

    checks.append(
        check(
            "no_empty_implementation_decisions",
            all(row.get("implementation_decision") for row in rows),
            Counter(str(row.get("implementation_decision")) for row in rows),
        )
    )

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "rows": len(rows),
            "candidate_rows": len({row.get("candidate_id") for row in rows}),
            "internal_pending_lifecycle_rows": len(internal_rows),
            "derived_source_field_cells": derived_cells,
            "before_numeric_proxy_rows": len(before_values),
            "after_numeric_proxy_rows": len(after_values),
            "implementation_decision_counts": summary.get("implementation_decision_counts"),
        },
        "plate_decision": "PENDING_LIFECYCLE_SOURCE_DERIVATIONS_RECOMPUTED_WITH_PROXY_R_UNCHANGED",
        "can_mark_pending_lifecycle_source_derivation_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
