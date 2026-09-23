"""Verify the action ledger after conservative kill-label repair."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_main_orchestrator_action_kill_label_scope_repair_2026_05_17 import (  # noqa: E402
    REPAIRED_BRANCH,
    SOURCE_BRANCH,
    TARGET_PRIMITIVE,
    kill_audit_present,
    sha256_file,
    write_json,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 1026,
    "KILL": 967,
    "PRESERVE_REQUIREMENT": 63,
    "REDESIGN": 852,
}
EXPECTED_SOURCE_COST_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 33,
    "KEEP": 39,
    "KILL": 3,
    "PRESERVE_REQUIREMENT": 63,
}


def read_json(path: Path) -> dict[str, Any]:
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


def append_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def verify_manifest(manifest: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    for section in ("input_artifacts", "output_artifacts"):
        for raw_path, expected in manifest.get(section, {}).items():
            path = REPO_ROOT / raw_path if section == "input_artifacts" else ROUTE_DIR / raw_path
            append_check(checks, f"{section}:{raw_path}:exists", path.exists())
            if not path.exists():
                continue
            append_check(checks, f"{section}:{raw_path}:sha256", sha256_file(path) == expected.get("sha256"))
            append_check(checks, f"{section}:{raw_path}:size", path.stat().st_size == expected.get("size_bytes"))


def has_repaired_audit(row: dict[str, Any]) -> bool:
    audit = row.get("missed_opportunity_audit")
    return (
        row.get("action_class") == "PRESERVE_REQUIREMENT"
        and row.get("branch_decision") == REPAIRED_BRANCH
        and row.get("before_kill_label_scope_repair_action_class") == "KILL"
        and row.get("before_kill_label_scope_repair_branch_decision") == SOURCE_BRANCH
        and row.get("kill_label_scope_repair_status") == "RELABELED_KILL_OR_AVOID_AS_PRESERVE_REQUIREMENT"
        and row.get("claim_decision_scope")
        == "NOT_KILLED_ACCEPTED_SOURCE_BRANCH_PRESERVED_FOR_REPAIR_OR_AVOID_REDESIGN"
        and row.get("underlying_intelligence_preserved") is True
        and isinstance(audit, dict)
        and audit.get("kill_scope") == "NOT_KILLED_RELABELED_PRESERVE_REQUIREMENT"
        and bool(audit.get("what_was_tried"))
        and bool(audit.get("what_could_make_it_work"))
        and bool(audit.get("preserve_as"))
        and bool(audit.get("next_route"))
    )


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    action_counts = dict(Counter(str(row.get("action_class") or "") for row in rows))
    source_rows = [row for row in rows if row.get("primitive_family") == TARGET_PRIMITIVE]
    source_action_counts = dict(Counter(str(row.get("action_class") or "") for row in source_rows))
    relabelled = [
        row
        for row in rows
        if row.get("kill_label_scope_repair_status") == "RELABELED_KILL_OR_AVOID_AS_PRESERVE_REQUIREMENT"
    ]
    kill_rows = [row for row in rows if row.get("action_class") == "KILL"]

    append_check(checks, "row_count", len(rows) == 3426, len(rows))
    append_check(checks, "summary_row_count", summary.get("rows") == len(rows), summary.get("rows"))
    append_check(checks, "action_counts", action_counts == EXPECTED_ACTION_COUNTS, action_counts)
    append_check(checks, "source_cost_action_counts", source_action_counts == EXPECTED_SOURCE_COST_ACTION_COUNTS, source_action_counts)
    append_check(checks, "relabelled_count", len(relabelled) == 47, len(relabelled))
    append_check(
        checks,
        "no_remaining_kill_or_avoid_kill_labels",
        all(not (row.get("action_class") == "KILL" and row.get("branch_decision") == SOURCE_BRANCH) for row in rows),
    )
    append_check(
        checks,
        "no_none_kill_or_avoid_current_action",
        all("NONE_KILL_OR_AVOID" not in str(row.get("current_action") or "") for row in rows),
    )
    append_check(checks, "relabelled_audits_present", all(has_repaired_audit(row) for row in relabelled))
    append_check(checks, "remaining_kill_count", len(kill_rows) == 967, len(kill_rows))
    append_check(checks, "remaining_kill_audits_present", all(kill_audit_present(row) for row in kill_rows))
    append_check(checks, "numeric_proxy_rows", summary.get("numeric_proxy_rows_after") == 1475)
    append_check(checks, "proxy_sum", summary.get("proxy_r_sum_after") == 408.47201587)
    append_check(checks, "proxy_delta_zero", summary.get("proxy_r_sum_delta") == 0.0)
    append_check(checks, "exact_r_zero", summary.get("exact_r_rows") == 0)
    append_check(
        checks,
        "summary_relabelled_count",
        summary.get("repair_stats", {}).get("kill_or_avoid_source_rows_relabelled_to_preserve_requirement") == 47,
    )
    append_check(
        checks,
        "safe_flags_closed",
        summary.get("safe_flags")
        == {
            "NO_PROMOTION_VERDICT": True,
            "live_effect": False,
            "outcome_review_opened": False,
            "validation_safe": False,
        },
    )
    verify_manifest(manifest, checks)

    verified = all(check["ok"] for check in checks)
    result = {
        "schema_version": "main_orch24_action_kill_label_scope_repair_verifier_v1",
        "verified": verified,
        "decision": (
            "ACTION_KILL_LABEL_SCOPE_REPAIR_VERIFIED"
            if verified
            else "ACTION_KILL_LABEL_SCOPE_REPAIR_REJECTED"
        ),
        "checks": checks,
        "summary": {
            "rows": len(rows),
            "relabelled_rows": len(relabelled),
            "numeric_proxy_rows": summary.get("numeric_proxy_rows_after"),
            "proxy_r_sum": summary.get("proxy_r_sum_after"),
            "remaining_kill_rows": len(kill_rows),
            "preserve_requirement_rows": action_counts.get("PRESERVE_REQUIREMENT"),
        },
    }
    write_json(VERIFY_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
