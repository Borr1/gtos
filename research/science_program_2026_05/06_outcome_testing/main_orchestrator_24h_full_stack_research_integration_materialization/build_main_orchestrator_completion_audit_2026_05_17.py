from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-17"

OUTPUT_PATH = ROUTE_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_OUTPUT_MANIFEST_{DATE}.json"

EXACT_MATERIALIZATION_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_SUMMARY_{DATE}.json"
EXACT_MATERIALIZATION_VERIFY = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_MATERIALIZATION_VERIFICATION_RESULT_{DATE}.json"
RESIDUAL_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_SUMMARY_{DATE}.json"
RESIDUAL_VERIFY = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_VERIFY_RESULT_{DATE}.json"
SPLIT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_SUMMARY_{DATE}.json"
SPLIT_VERIFY = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_VERIFY_RESULT_{DATE}.json"
BRIDGE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_SUMMARY_{DATE}.json"
BRIDGE_VERIFY = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_VERIFICATION_RESULT_{DATE}.json"
ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_{DATE}.jsonl"
RESIDUAL_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_{DATE}.jsonl"
SPLIT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_PROXY_SPLIT_COMPARISON_LEDGER_{DATE}.jsonl"

ACTIVE_TEXT_SOURCES = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION_GOAL_PROMPT_2026-05-16.md",
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION_STARTER_2026-05-16.txt",
    REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    REPO_ROOT / "src/research_infra/science_goal_program.py",
    REPO_ROOT / "scripts/audit_goal_route_artifacts.py",
    REPO_ROOT / "scripts/build_science_goal_program.py",
    REPO_ROOT / "tests/test_science_goal_program.py",
    REPO_ROOT / "tests/scripts/test_audit_goal_route_artifacts.py",
    ROUTE_DIR / "build_main_orchestrator_action_after_exact_r_materialization_2026_05_17.py",
    ROUTE_DIR / "verify_main_orchestrator_action_after_exact_r_materialization_2026_05_17.py",
    ROUTE_DIR / "build_main_orchestrator_residual_numeric_r_field_resolution_2026_05_17.py",
    ROUTE_DIR / "verify_main_orchestrator_residual_numeric_r_field_resolution_2026_05_17.py",
    ROUTE_DIR / "build_main_orchestrator_exact_proxy_split_comparison_2026_05_17.py",
    ROUTE_DIR / "verify_main_orchestrator_exact_proxy_split_comparison_2026_05_17.py",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    rows = 0
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                json.loads(line)
                rows += 1
    return rows


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def scan_retired_markers(paths: tuple[Path, ...]) -> dict[str, Any]:
    markers = {
        "legacy_result_label": "_".join(("NO", "PROMOTION", "VERDICT")),
        "legacy_source_flag": "_".join(("validation", "safe")),
        "legacy_outcome_flag": "_".join(("outcome", "review", "opened")),
        "legacy_runtime_flag": "_".join(("live", "effect")),
        "legacy_safe_phrase": " ".join(("safe", "flags")),
        "legacy_claim_phrase": " ".join(("promotion", "claims")),
        "legacy_hold_phrase": " ".join(("no", "promotion")),
        "legacy_strict_phrase": " ".join(("strict", "promotion")),
    }
    hits: list[dict[str, str]] = []
    checked: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
        checked.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
        for marker_name, marker in markers.items():
            if marker in text:
                hits.append({"path": rel, "marker": marker_name})
    return {"checked": checked, "hits": hits, "ok": not hits}


def main() -> None:
    exact_summary = load_json(EXACT_MATERIALIZATION_SUMMARY)
    exact_verify = load_json(EXACT_MATERIALIZATION_VERIFY)
    residual_summary = load_json(RESIDUAL_SUMMARY)
    residual_verify = load_json(RESIDUAL_VERIFY)
    split_summary = load_json(SPLIT_SUMMARY)
    split_verify = load_json(SPLIT_VERIFY)
    bridge_summary = load_json(BRIDGE_SUMMARY)
    bridge_verify = load_json(BRIDGE_VERIFY)

    active_scan = scan_retired_markers(ACTIVE_TEXT_SOURCES)
    ledger_rows = count_jsonl(ACTION_LEDGER)
    residual_rows = count_jsonl(RESIDUAL_LEDGER)
    split_rows = count_jsonl(SPLIT_LEDGER)

    issues: list[str] = []
    if not exact_verify.get("verified"):
        issues.append("exact_materialization_verify_not_green")
    if not residual_verify.get("verified"):
        issues.append("residual_numeric_verify_not_green")
    if not split_verify.get("verified"):
        issues.append("split_verify_not_green")
    if not bridge_verify.get("verified"):
        issues.append("bridge_verify_not_green")
    if not active_scan["ok"]:
        issues.append("active_retired_marker_scan_failed")
    if ledger_rows != 3426 or residual_rows != 3426 or split_rows != 135:
        issues.append("current_ledger_row_counts_mismatch")
    if exact_summary.get("exact_r_owner_rows") != 2 or exact_summary.get("exact_r_reference_rows") != 24:
        issues.append("exact_r_counts_mismatch")
    if split_summary.get("proxy_owner_rows") != 718:
        issues.append("proxy_owner_count_mismatch")
    if exact_summary.get("source_paths_scanned") != 1076:
        issues.append("source_path_scan_count_mismatch")
    if exact_summary.get("source_rows_scanned") != 1620573:
        issues.append("source_row_scan_count_mismatch")
    if exact_summary.get("xagusd_position_238316913_missing_close_rows") != 0:
        issues.append("xagusd_position_close_not_resolved")
    if residual_verify.get("field_rows") != 6238:
        issues.append("residual_numeric_field_count_mismatch")
    if split_summary.get("exact_broker_profit_rows") != 24:
        issues.append("broker_profit_reference_count_mismatch")
    if abs(float(split_summary.get("exact_broker_profit_sum_usd")) - 7685.64) > 1e-9:
        issues.append("broker_profit_sum_mismatch")

    checklist = [
        {
            "requirement": "exact_r_bridge_not_terminal",
            "covered": exact_summary.get("exact_r_owner_rows") == 2,
            "evidence": "Bridge rows were consumed into owner/reference policy and current action ledger.",
        },
        {
            "requirement": "identifier_and_alias_search_exhausted_from_current_sources",
            "covered": exact_verify.get("source_paths_scanned") == 1076
            and exact_verify.get("source_rows_scanned") == 1620573,
            "evidence": "Exact materialization verifier checks per-row search keys, alias references, source manifests, and unresolved disposition on all 3,402 missing exact-R rows.",
        },
        {
            "requirement": "xagusd_close_deal_bound",
            "covered": exact_summary.get("xagusd_position_238316913_missing_close_rows") == 0,
            "evidence": "MT5 account-history export bound close deal 222552477 for position 238316913 and materialized +0.0289R owner exact R.",
        },
        {
            "requirement": "current_exact_and_proxy_rows_materialized",
            "covered": split_summary.get("exact_owner_rows") == 2
            and split_summary.get("exact_reference_rows") == 24
            and split_summary.get("proxy_owner_rows") == 718,
            "evidence": "Current split comparison uses owner-only exact R, reference R, proxy owner R, and exact/proxy overlap rows.",
        },
        {
            "requirement": "residual_numeric_r_fields_resolved",
            "covered": residual_verify.get("field_rows") == 6238 and not residual_verify.get("issues"),
            "evidence": "Residual numeric fields were classified as current proxy, reference, duplicate, descriptor, distance, provenance, or redesign rows with zero unclassified fields.",
        },
        {
            "requirement": "active_generators_and_context_no_retired_wrapper_labels",
            "covered": active_scan["ok"],
            "evidence": "Active prompt, starter, doctrine, science scaffold, route auditor, tests, and current exact/proxy builders were scanned.",
        },
    ]
    for item in checklist:
        if not item["covered"]:
            issues.append(f"checklist_uncovered:{item['requirement']}")

    completion = {
        "schema_version": "main_orch24_completion_audit_v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
        "git_head_at_build": git_head(),
        "can_mark_active_24h_goal_complete": not issues,
        "terminal_decision": (
            "CURRENT_REPLAYABLE_GEOMETRY_RESULTS_MATERIALIZED_WITH_EXACT_AND_PROXY_R_ROWS"
            if not issues
            else "CURRENT_REPLAYABLE_GEOMETRY_RESULTS_MATERIALIZATION_INCOMPLETE"
        ),
        "checkpoint_effect": {
            "concrete_behavior_or_code_changed": [
                "pending lifecycle source-capture fields were implemented and tested earlier in the route",
                "exact-R identifier propagation and account-history binding are materialized into current action rows",
                "active prompt/doctrine/scaffold/auditor sources now generate result-boundary fields instead of retired wrapper labels",
            ],
            "result_ledgers_changed": [
                str(ACTION_LEDGER.relative_to(REPO_ROOT)),
                str(RESIDUAL_LEDGER.relative_to(REPO_ROOT)),
                str(SPLIT_LEDGER.relative_to(REPO_ROOT)),
            ],
        },
        "numeric_results": {
            "action_rows": exact_summary.get("output_rows"),
            "exact_owner_rows": exact_summary.get("exact_r_owner_rows"),
            "exact_owner_sum": exact_summary.get("exact_r_owner_sum"),
            "exact_reference_rows": exact_summary.get("exact_r_reference_rows"),
            "exact_reference_sum": exact_summary.get("exact_r_reference_sum"),
            "proxy_owner_rows": split_summary.get("proxy_owner_rows"),
            "proxy_owner_sum": split_summary.get("proxy_owner_sum"),
            "exact_proxy_overlap_rows": split_summary.get("exact_proxy_overlap_rows"),
            "exact_proxy_delta_sum": split_summary.get("exact_proxy_delta_sum"),
            "exact_broker_profit_rows": split_summary.get("exact_broker_profit_rows"),
            "exact_broker_profit_sum_usd": split_summary.get("exact_broker_profit_sum_usd"),
            "split_rows": split_summary.get("split_rows"),
            "split_kind_counts": split_summary.get("split_kind_counts"),
        },
        "row_disposition_counts": split_summary.get("all_rows_metrics", {}).get("exact_status_counts"),
        "implementation_decisions": {
            "action_class_counts": split_summary.get("all_rows_metrics", {}).get("action_class_counts"),
            "branch_decision_top_counts": split_summary.get("all_rows_metrics", {}).get(
                "branch_decision_top_counts"
            ),
        },
        "source_search_proof": {
            "bridge_source_paths": bridge_summary.get("source_paths_searched"),
            "bridge_source_row_counts": bridge_summary.get("source_row_counts"),
            "materialization_source_paths_scanned": exact_summary.get("source_paths_scanned"),
            "materialization_source_rows_scanned": exact_summary.get("source_rows_scanned"),
            "missing_exact_r_rows_with_row_level_disposition": exact_summary.get("missing_r_rows"),
            "xagusd_position_238316913_missing_close_rows": exact_summary.get(
                "xagusd_position_238316913_missing_close_rows"
            ),
            "source_hash_manifest_sha256": exact_summary.get("source_hash_manifest_sha256"),
        },
        "residual_numeric_r_resolution": {
            "field_rows": residual_verify.get("field_rows"),
            "status_counts": residual_verify.get("resolution_status_counts"),
            "residual_numeric_r_counted_proxy_added_rows": residual_verify.get(
                "residual_numeric_r_counted_proxy_added_rows"
            ),
        },
        "active_retired_label_scan": active_scan,
        "verifier_inputs": {
            str(path.relative_to(REPO_ROOT)): {"sha256": sha256_file(path)}
            for path in (
                EXACT_MATERIALIZATION_SUMMARY,
                EXACT_MATERIALIZATION_VERIFY,
                RESIDUAL_SUMMARY,
                RESIDUAL_VERIFY,
                SPLIT_SUMMARY,
                SPLIT_VERIFY,
                BRIDGE_SUMMARY,
                BRIDGE_VERIFY,
            )
        },
        "focused_verification_already_run_this_checkpoint": [
            "py -3 -m pytest tests\\test_science_goal_program.py tests\\scripts\\test_audit_goal_route_artifacts.py -q -p no:cacheprovider --basetemp .pytest-tmp-active-boundary-label-repair",
            "py -3 -m py_compile src\\research_infra\\science_goal_program.py scripts\\build_science_goal_program.py scripts\\audit_goal_route_artifacts.py",
        ],
        "completion_checklist": checklist,
        "issues": issues,
    }
    OUTPUT_PATH.write_text(json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "main_orch24_completion_audit_manifest_v1",
        "generated_utc": completion["generated_utc"],
        "inputs": completion["verifier_inputs"],
        "outputs": {
            str(OUTPUT_PATH.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(OUTPUT_PATH),
                "rows": 1,
            }
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"can_mark_active_24h_goal_complete": completion["can_mark_active_24h_goal_complete"], "issues": issues}, sort_keys=True))


if __name__ == "__main__":
    main()
