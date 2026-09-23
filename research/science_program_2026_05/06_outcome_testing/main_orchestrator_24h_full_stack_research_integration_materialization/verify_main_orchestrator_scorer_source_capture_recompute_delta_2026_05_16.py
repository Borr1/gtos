from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter, defaultdict
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


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def summarize_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_surface[str(row.get("source_capture_surface") or "")].append(row)
    surface_summary = {}
    for surface, surface_rows in sorted(by_surface.items()):
        before = [value for row in surface_rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
        after = [value for row in surface_rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
        surface_summary[surface] = {
            "rows": len(surface_rows),
            "before_numeric_proxy_rows": len(before),
            "after_numeric_proxy_rows": len(after),
            "numeric_proxy_row_delta": len(after) - len(before),
            "before_proxy_r_mean": mean(before),
            "after_proxy_r_mean": mean(after),
            "before_proxy_r_sum": sum(before),
            "after_proxy_r_sum": sum(after),
            "proxy_r_sum_delta": sum(after) - sum(before),
            "delta_class_counts": dict(Counter(str(row.get("proxy_r_delta_class")) for row in surface_rows)),
            "implementation_decision_counts": dict(
                Counter(str(row.get("implementation_decision")) for row in surface_rows)
            ),
        }
    return surface_summary


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_scorer_source_capture_recompute_delta_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    current_surface_summary = summarize_from_rows(rows)

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_matches_summary", len(rows) == summary.get("rows"), {"rows": len(rows), "summary": summary.get("rows")}))
    checks.append(check("candidate_count_matches_summary", len({row.get("candidate_id") for row in rows}) == summary.get("candidate_rows")))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in rows)))
    checks.append(
        check(
            "numeric_proxy_counts_match",
            len(before_values) == summary.get("before_numeric_proxy_rows")
            and len(after_values) == summary.get("after_numeric_proxy_rows")
            and len(after_values) - len(before_values) == summary.get("numeric_proxy_row_delta"),
            {
                "before": len(before_values),
                "after": len(after_values),
                "summary_before": summary.get("before_numeric_proxy_rows"),
                "summary_after": summary.get("after_numeric_proxy_rows"),
            },
        )
    )
    checks.append(
        check(
            "proxy_sums_match",
            round(sum(before_values), 10) == round(float(summary.get("before_proxy_r_sum")), 10)
            and round(sum(after_values), 10) == round(float(summary.get("after_proxy_r_sum")), 10),
            {
                "before_sum": sum(before_values),
                "after_sum": sum(after_values),
                "summary_before": summary.get("before_proxy_r_sum"),
                "summary_after": summary.get("after_proxy_r_sum"),
            },
        )
    )
    checks.append(check("surface_summary_matches_rows", summary.get("surface_summary") == current_surface_summary))
    checks.append(
        check(
            "captured_fvg_rows_are_scored_or_missing_source",
            not [
                row
                for row in rows
                if row.get("source_capture_surface") == "standalone_fvg_metadata_scorer"
                and row.get("after_score_status") == "SCORER_NOT_IMPLEMENTED"
            ],
        )
    )
    checks.append(
        check(
            "captured_structural_rows_are_scored_or_missing_source",
            not [
                row
                for row in rows
                if row.get("source_capture_surface") == "structural_lock_metadata_scorer"
                and row.get("after_score_status") == "SCORER_NOT_IMPLEMENTED"
            ],
        )
    )
    checks.append(
        check(
            "implementation_decisions_not_empty",
            all(row.get("implementation_decision") for row in rows),
            Counter(str(row.get("implementation_decision")) for row in rows),
        )
    )
    checks.append(
        check(
            "new_numeric_proxy_rows_exist_for_repaired_scorers",
            summary.get("numeric_proxy_row_delta", 0) > 0,
            summary.get("numeric_proxy_row_delta"),
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

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "rows": len(rows),
            "candidate_rows": len({row.get("candidate_id") for row in rows}),
            "before_numeric_proxy_rows": len(before_values),
            "after_numeric_proxy_rows": len(after_values),
            "numeric_proxy_row_delta": len(after_values) - len(before_values),
            "implementation_decision_counts": summary.get("implementation_decision_counts"),
            "surface_summary": summary.get("surface_summary"),
        },
        "plate_decision": "REPAIRED_SCORER_SOURCE_CAPTURE_SURFACES_RECOMPUTED_WITH_CURRENT_ROW_PROXY_R_DELTAS",
        "can_mark_scorer_source_capture_recompute_delta_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
