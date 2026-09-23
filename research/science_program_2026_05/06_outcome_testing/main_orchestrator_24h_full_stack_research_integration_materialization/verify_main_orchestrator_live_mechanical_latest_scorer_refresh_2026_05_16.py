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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def grouped_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key) or "") for row in rows))


def group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    before = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "rows": len(rows),
        "before_numeric_proxy_rows": len(before),
        "after_numeric_proxy_rows": len(after),
        "numeric_proxy_row_delta": len(after) - len(before),
        "before_proxy_r_sum": sum(before),
        "after_proxy_r_sum": sum(after),
        "proxy_r_sum_delta": sum(after) - sum(before),
    }


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_live_mechanical_latest_scorer_refresh_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    dry_run_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DRY_RUN_LEDGER_{DATE}.jsonl"
    delta_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DELTA_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, dry_run_path, delta_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    dry_rows = read_jsonl(dry_run_path)
    delta_rows = read_jsonl(delta_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    before = [value for row in delta_rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after = [value for row in delta_rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_primitive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in delta_rows:
        by_strategy[str(row.get("strategy_id") or "")].append(row)
        by_primitive[str(row.get("primitive_family") or "")].append(row)

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("dry_run_rows_match_delta_rows", len(dry_rows) == len(delta_rows) == summary.get("rows")))
    checks.append(
        check(
            "latest_only_denominator_preserved",
            summary.get("backfill_run_summary", {}).get("latest_paths_only") is True
            and summary.get("backfill_run_summary", {}).get("dry_run") is True
            and summary.get("backfill_run_summary", {}).get("path_rows_evaluated") == summary.get("candidate_rows"),
            summary.get("backfill_run_summary"),
        )
    )
    checks.append(check("shadow_output_unchanged", summary.get("shadow_output_unchanged") is True))
    checks.append(check("no_shadow_append", summary.get("no_shadow_log_append") is True and all(row.get("no_shadow_log_append") is True for row in delta_rows)))
    checks.append(check("exact_r_not_opened", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in delta_rows)))
    checks.append(
        check(
            "numeric_proxy_counts_match",
            len(before) == summary.get("before_numeric_proxy_rows")
            and len(after) == summary.get("after_numeric_proxy_rows")
            and len(after) - len(before) == summary.get("numeric_proxy_row_delta"),
            {
                "before": len(before),
                "after": len(after),
                "summary_before": summary.get("before_numeric_proxy_rows"),
                "summary_after": summary.get("after_numeric_proxy_rows"),
            },
        )
    )
    checks.append(
        check(
            "proxy_sums_match",
            round(sum(before), 10) == round(float(summary.get("before_proxy_r_sum")), 10)
            and round(sum(after), 10) == round(float(summary.get("after_proxy_r_sum")), 10),
            {"before": sum(before), "after": sum(after)},
        )
    )
    checks.append(
        check(
            "append_status_counts_match",
            grouped_counts(delta_rows, "dry_run_append_status") == summary.get("dry_run_append_status_counts"),
        )
    )
    checks.append(
        check(
            "action_class_counts_match",
            grouped_counts(delta_rows, "action_class") == summary.get("action_class_counts"),
        )
    )
    checks.append(
        check(
            "strategy_summaries_match",
            all(
                summary.get("strategy_summary", {}).get(strategy, {}).get("rows") == group_summary(rows)["rows"]
                and summary.get("strategy_summary", {}).get(strategy, {}).get("after_numeric_proxy_rows")
                == group_summary(rows)["after_numeric_proxy_rows"]
                for strategy, rows in by_strategy.items()
            ),
        )
    )
    checks.append(
        check(
            "primitive_summaries_match",
            all(
                summary.get("primitive_family_summary", {}).get(family, {}).get("rows")
                == group_summary(rows)["rows"]
                for family, rows in by_primitive.items()
            ),
        )
    )
    checks.append(
        check(
            "material_rows_have_primitive_family",
            not [row["_line_no"] for row in delta_rows if not row.get("primitive_family")],
        )
    )
    checks.append(
        check(
            "all_rows_are_dry_run_append_candidates",
            set(grouped_counts(delta_rows, "dry_run_append_status")) <= {
                "WOULD_APPEND_CORRECTION",
                "WOULD_APPEND_NEW",
            },
        )
    )

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    manifest_outputs = manifest.get("outputs", {})
    for path in [dry_run_path, delta_path, summary_path]:
        recorded = manifest_outputs.get(path.name, {})
        checks.append(
            check(
                f"{path.name}_manifest_hash_matches",
                recorded.get("sha256") == sha256(path) and recorded.get("bytes") == path.stat().st_size,
                recorded,
            )
        )

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "rows": len(delta_rows),
        "dry_run_rows": len(dry_rows),
        "safe_flags": SAFE_FLAGS,
        "terminal_decision": "VERIFIED_LATEST_ONLY_SCORER_REFRESH_DRY_RUN_WITH_ROW_LEVEL_DELTAS"
        if ok
        else "LATEST_ONLY_SCORER_REFRESH_VERIFICATION_FAILED",
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
