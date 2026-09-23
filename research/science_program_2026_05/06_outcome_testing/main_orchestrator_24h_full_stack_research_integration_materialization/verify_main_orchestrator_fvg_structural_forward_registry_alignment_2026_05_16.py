from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ARTIFACT_SAFE_FLAGS = {
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
    build_script = ROUTE_DIR / "build_main_orchestrator_fvg_structural_forward_registry_alignment_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_FORWARD_REGISTRY_ALIGNMENT_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    checks.append(
        check(
            "route_id_matches",
            summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID,
        )
    )
    checks.append(
        check(
            "safe_flags_closed",
            summary.get("safe_flags") == ARTIFACT_SAFE_FLAGS
            and manifest.get("safe_flags") == ARTIFACT_SAFE_FLAGS
            and all(row.get("safe_flags") == ARTIFACT_SAFE_FLAGS for row in rows),
        )
    )
    checks.append(check("registry_row_count", len(rows) == summary.get("registry_rows") == 8, len(rows)))
    checks.append(
        check(
            "source_rows_match",
            sum(row.get("source_rows", 0) for row in rows) == summary.get("source_rows") == 2192,
            summary.get("source_rows"),
        )
    )
    checks.append(
        check(
            "current_source_summary_preserved",
            summary.get("source_summary_rows") == 2740
            and summary.get("source_summary_after_numeric_proxy_rows") == 537
            and summary.get("source_summary_after_proxy_r_sum") == 133.0
            and summary.get("source_summary_numeric_proxy_row_delta") == 340
            and summary.get("source_summary_proxy_r_sum_delta") == 83.0,
            {
                "rows": summary.get("source_summary_rows"),
                "after_numeric": summary.get("source_summary_after_numeric_proxy_rows"),
                "after_sum": summary.get("source_summary_after_proxy_r_sum"),
            },
        )
    )
    checks.append(
        check(
            "aligned_strategy_proxy_delta_matches_source_delta",
            summary.get("aligned_strategy_after_numeric_proxy_rows") == 340
            and summary.get("aligned_strategy_after_proxy_r_sum") == 83.0
            and summary.get("aligned_strategy_proxy_r_sum_delta") == 83.0,
            {
                "aligned_numeric": summary.get("aligned_strategy_after_numeric_proxy_rows"),
                "aligned_sum": summary.get("aligned_strategy_after_proxy_r_sum"),
            },
        )
    )
    expected_alignment = {
        "ALIGN_REGISTRY_TO_ROW_LEVEL_DEFAULT_OFF_SCORER": 7,
        "REGISTRY_ALREADY_ALIGNED_OR_PRESERVED": 1,
    }
    checks.append(
        check(
            "registry_alignment_counts_expected",
            summary.get("registry_alignment_decision_counts") == expected_alignment,
            summary.get("registry_alignment_decision_counts"),
        )
    )
    checks.append(
        check(
            "no_stale_global_source_blocked_decisions_on_aligned_rows",
            all(
                row.get("current_registry_branch_decision") != "SOURCE_CAPTURE_REQUIRED_SCORER_BLOCKED"
                for row in rows
                if row.get("alignment_decision") == "ALIGN_REGISTRY_TO_ROW_LEVEL_DEFAULT_OFF_SCORER"
            ),
            Counter(row.get("current_registry_branch_decision") for row in rows),
        )
    )
    per_strategy = summary.get("per_strategy_proxy_delta", {})
    checks.append(
        check(
            "priority_strategy_proxy_rows_expected",
            per_strategy.get("V2_STRUCT_FVG_MID_EDGE", {}).get("after_numeric_proxy_rows") == 3
            and per_strategy.get("V3_FVG_ONLY_RESCUE_RISK_BANK", {}).get("after_numeric_proxy_rows") == 3
            and per_strategy.get("V2_STRUCT_SWING_PROTECTED", {}).get("after_numeric_proxy_rows") == 49
            and per_strategy.get("FVG_OB_CONFLUENCE_OB_AFTER_FVG", {}).get("after_numeric_proxy_rows") == 57,
            per_strategy,
        )
    )
    checks.append(
        check(
            "branch_and_implementation_counts_cover_rows",
            all(row.get("current_registry_branch_decision") for row in rows)
            and all(row.get("implementation_candidate") for row in rows)
            and sum(summary.get("current_registry_branch_decision_counts", {}).values()) == len(rows),
            summary.get("current_registry_branch_decision_counts"),
        )
    )
    checks.append(
        check(
            "no_live_or_shadow_append",
            all(row.get("no_live_behavior") is True and row.get("no_shadow_log_append") is True for row in rows),
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
            "registry_rows": len(rows),
            "source_rows": summary.get("source_rows"),
            "aligned_strategy_after_numeric_proxy_rows": summary.get(
                "aligned_strategy_after_numeric_proxy_rows"
            ),
            "aligned_strategy_after_proxy_r_sum": summary.get(
                "aligned_strategy_after_proxy_r_sum"
            ),
            "registry_alignment_decision_counts": summary.get(
                "registry_alignment_decision_counts"
            ),
        },
        "plate_decision": summary.get("plate_decision"),
        "can_mark_fvg_structural_forward_registry_alignment_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": ARTIFACT_SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
