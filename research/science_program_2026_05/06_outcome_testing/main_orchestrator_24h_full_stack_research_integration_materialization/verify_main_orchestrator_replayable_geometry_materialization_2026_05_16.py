from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
TERMINAL_DECISION = "CURRENT_REPLAYABLE_GEOMETRY_RESULTS_MATERIALIZED_WITH_PROXY_R_ROWS_ONLY"
OUT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)

PATHS = {
    "input_snapshot": OUT_DIR / f"MAIN_ORCH24_INPUT_SNAPSHOT_{DATE}.json",
    "candidate_ledger": OUT_DIR / f"MAIN_ORCH24_UNIFIED_CANDIDATE_LEDGER_{DATE}.jsonl",
    "geometry_binding_ledger": OUT_DIR / f"MAIN_ORCH24_GEOMETRY_BINDING_LEDGER_{DATE}.jsonl",
    "r_result_ledger": OUT_DIR / f"MAIN_ORCH24_EXACT_PROXY_R_RESULT_LEDGER_{DATE}.jsonl",
    "noncomputable_proof_ledger": OUT_DIR / f"MAIN_ORCH24_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl",
    "dependency_ledger": OUT_DIR / f"MAIN_ORCH24_CURRENT_SNAPSHOT_DEPENDENCY_LEDGER_{DATE}.jsonl",
    "bucket_inventory": OUT_DIR / f"MAIN_ORCH24_EIGHT_BUCKET_INVENTORY_{DATE}.jsonl",
    "split_summary": OUT_DIR / f"MAIN_ORCH24_SPLIT_SUMMARY_{DATE}.jsonl",
    "expectancy_summary": OUT_DIR / f"MAIN_ORCH24_EXPECTANCY_COST_STRESS_SUMMARY_{DATE}.json",
    "ready8_comparison": OUT_DIR / f"MAIN_ORCH24_READY8_COMPARISON_{DATE}.json",
    "survivor_failure_decisions": OUT_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl",
    "completion_audit": OUT_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_{DATE}.json",
    "manifest": OUT_DIR / f"MAIN_ORCH24_OUTPUT_MANIFEST_{DATE}.json",
    "summary_md": OUT_DIR / f"MAIN_ORCH24_REPLAYABLE_GEOMETRY_MATERIALIZATION_SUMMARY_{DATE}.md",
}

VERIFY_OUT = OUT_DIR / f"MAIN_ORCH24_VERIFICATION_RESULT_{DATE}.json"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append({"path": str(path), "line_no": line_no, "error": str(exc)})
    return rows, errors


def check(condition: bool, name: str, detail: Any, checks: list[dict[str, Any]]) -> None:
    checks.append({"name": name, "ok": bool(condition), "detail": detail})


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def update_manifest_with_verification(manifest_path: Path) -> None:
    manifest = read_json(manifest_path)
    artifacts = [a for a in (manifest.get("artifacts") or []) if a.get("label") != "verification_result"]
    artifacts.append(
        {
            "label": "verification_result",
            "path": str(VERIFY_OUT),
            "exists": VERIFY_OUT.exists(),
            "size_bytes": VERIFY_OUT.stat().st_size if VERIFY_OUT.exists() else None,
            "sha256": sha256_file(VERIFY_OUT),
            "git_status": None,
        }
    )
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    checks: list[dict[str, Any]] = []
    jsonl_rows: dict[str, list[dict[str, Any]]] = {}
    jsonl_errors: list[dict[str, Any]] = []

    for name, path in PATHS.items():
        check(path.exists(), f"{name}_exists", str(path), checks)

    snapshot = read_json(PATHS["input_snapshot"])
    summary = read_json(PATHS["expectancy_summary"])
    ready8 = read_json(PATHS["ready8_comparison"])
    audit = read_json(PATHS["completion_audit"])
    manifest = read_json(PATHS["manifest"])

    for name, path in PATHS.items():
        if path.suffix == ".jsonl":
            rows, errors = read_jsonl(path)
            jsonl_rows[name] = rows
            jsonl_errors.extend(errors)

    check(not jsonl_errors, "jsonl_parse_errors_zero", jsonl_errors[:5], checks)
    check(snapshot["route_id"] == ROUTE_ID, "snapshot_route_id", snapshot.get("route_id"), checks)
    check(
        (snapshot.get("moonshot", {}).get("git_safe_head") or {}).get("returncode") == 0,
        "moonshot_safe_git_head_ok",
        snapshot.get("moonshot", {}).get("git_safe_head"),
        checks,
    )
    plain_attempt = snapshot.get("moonshot", {}).get("git_plain_rev_parse_attempt") or {}
    check(
        plain_attempt.get("returncode") != 0 and "dubious ownership" in (plain_attempt.get("stderr") or "").lower(),
        "moonshot_plain_git_dubious_ownership_recorded",
        plain_attempt,
        checks,
    )
    check(summary["terminal_decision"] == TERMINAL_DECISION, "terminal_decision", summary["terminal_decision"], checks)
    check(summary["counts"]["exact_r_rows"] == 0, "exact_r_rows_zero", summary["counts"]["exact_r_rows"], checks)
    check(summary["counts"]["proxy_r_rows"] > 0, "proxy_r_rows_positive", summary["counts"]["proxy_r_rows"], checks)
    check(
        summary["counts"]["ready8_noncomputable_rows"] == 5502,
        "ready8_noncomputable_rows_5502",
        summary["counts"]["ready8_noncomputable_rows"],
        checks,
    )
    check(
        summary["counts"]["moonshot_branch_rstyle_noncomputable_rows"] == 2,
        "moonshot_branch_rstyle_noncomputable_rows_2",
        summary["counts"]["moonshot_branch_rstyle_noncomputable_rows"],
        checks,
    )
    check(
        summary["counts"]["noncomputable_rows"] == 5504,
        "total_noncomputable_rows_5504",
        summary["counts"]["noncomputable_rows"],
        checks,
    )
    check(
        len(jsonl_rows["noncomputable_proof_ledger"]) == summary["counts"]["noncomputable_rows"],
        "noncomputable_ledger_count_matches_summary",
        len(jsonl_rows["noncomputable_proof_ledger"]),
        checks,
    )
    check(
        len(jsonl_rows["r_result_ledger"]) == summary["counts"]["proxy_result_rows_total"],
        "r_result_ledger_count_matches_summary",
        len(jsonl_rows["r_result_ledger"]),
        checks,
    )
    rstyle_rows = [row for row in jsonl_rows["r_result_ledger"] if row.get("result_layer") == "moonshot_branch_rstyle_proxy"]
    rstyle_status = Counter(row.get("result_status") for row in rstyle_rows)
    check(
        len(rstyle_rows) == 384,
        "branch_rstyle_proxy_rows_384",
        {"rows": len(rstyle_rows), "summary": summary["counts"].get("branch_rstyle_proxy_rows")},
        checks,
    )
    check(
        rstyle_status == Counter(
            {
                "branch_proxy_positive_midpoint": 243,
                "branch_proxy_negative_midpoint": 83,
                "branch_proxy_interval_straddles_zero": 58,
            }
        ),
        "branch_rstyle_status_counts_match_source",
        dict(rstyle_status),
        checks,
    )
    rstyle_noncomputable = [
        row
        for row in jsonl_rows["noncomputable_proof_ledger"]
        if row.get("source_row_type") == "moonshot_branch_rstyle_proxy_outcome"
    ]
    check(
        len(rstyle_noncomputable) == 2,
        "branch_rstyle_targetstop_na_proofs_2",
        [row.get("row_id") for row in rstyle_noncomputable],
        checks,
    )
    check(
        len(jsonl_rows["candidate_ledger"]) == summary["counts"]["candidate_rows"],
        "candidate_ledger_count_matches_summary",
        len(jsonl_rows["candidate_ledger"]),
        checks,
    )
    buckets = Counter(row.get("bucket") for row in jsonl_rows["bucket_inventory"])
    check(
        "OWNED_BY_ACTIVE_MOONSHOT_BUILDER" in buckets,
        "bucket_7_present",
        dict(buckets),
        checks,
    )
    check(
        "OUT_OF_SCOPE_FOR_MAIN_BECAUSE_NO_CURRENT_COMPUTABLE_PATH" in buckets,
        "bucket_8_present",
        dict(buckets),
        checks,
    )
    check(
        ready8["ready8_terminal_decision"] == "MERGE_READY8_SCID_INTELLIGENCE_INTO_A_BROADER_SYSTEM_BUT_DO_NOT_CONTINUE_IT_AS_STANDALONE",
        "ready8_terminal_decision_preserved",
        ready8["ready8_terminal_decision"],
        checks,
    )
    check(
        ready8["ready8_proxy_r_rows_in_current_materialization"] == 0
        and ready8["moonshot_untagged_proxy_rows"] > 0,
        "ready8_vs_moonshot_comparison_separates_r_sources",
        {
            "ready8_proxy": ready8["ready8_proxy_r_rows_in_current_materialization"],
            "moonshot_proxy": ready8["moonshot_untagged_proxy_rows"],
        },
        checks,
    )
    audit_items = audit.get("prompt_to_artifact_checklist") or []
    check(
        audit_items and all(item.get("covered") for item in audit_items),
        "completion_audit_checklist_covered_for_first_plate",
        audit_items,
        checks,
    )
    check(
        audit.get("can_mark_active_24h_goal_complete") is False,
        "audit_does_not_close_24h_goal_early",
        audit.get("can_mark_active_24h_goal_complete"),
        checks,
    )
    check(
        manifest.get("artifact_count", 0) >= 12,
        "manifest_artifact_count",
        manifest.get("artifact_count"),
        checks,
    )
    ids = [row.get("result_id") for row in jsonl_rows["r_result_ledger"]]
    check(len(ids) == len(set(ids)), "result_ids_unique", {"rows": len(ids), "unique": len(set(ids))}, checks)

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "can_mark_first_materialization_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "terminal_decision": TERMINAL_DECISION,
        "checks": checks,
        "counts": {
            "candidate_rows": len(jsonl_rows.get("candidate_ledger", [])),
            "r_result_rows": len(jsonl_rows.get("r_result_ledger", [])),
            "noncomputable_rows": len(jsonl_rows.get("noncomputable_proof_ledger", [])),
            "bucket_rows": len(jsonl_rows.get("bucket_inventory", [])),
            "decision_rows": len(jsonl_rows.get("survivor_failure_decisions", [])),
        },
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    VERIFY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with VERIFY_OUT.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    update_manifest_with_verification(PATHS["manifest"])
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
