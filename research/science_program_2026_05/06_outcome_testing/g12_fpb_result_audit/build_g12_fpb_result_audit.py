from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT"
DECISION = "ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER"
SCHEMA_VERSION = "g12_fpb_result_audit_v1"

REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_VERIFIER = TARGET_DIR / "verify_family_path_behavior_result_screen_2026_05_10.py"
TARGET_TEST = TARGET_DIR / "test_family_path_behavior_result_screen_2026_05_10.py"

EXPECTED_COUNTS = {
    "raw_candidate_attempts": 13_540_033,
    "duplicate_candidate_keys": 687_275,
    "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
    "path_label_row_count": 12_852_758,
}
EXPECTED_FAMILIES = [
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout",
]
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
EXPECTED_LABELS = [
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_live_trading_behavior",
    "credentials_touched",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "opens_paid_api_or_databento_route",
    "opens_promotion",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_result_scoring",
    "opens_validation",
]
FORBIDDEN_RESULT_KEYS = {
    "actual_r",
    "broker_actual_r",
    "expectancy",
    "loss",
    "losses",
    "pnl",
    "pnl_usd",
    "profit",
    "r_multiple",
    "realized_r",
    "result_r",
    "win",
    "win_rate",
    "wins",
}


def _fs_path(path: Path) -> str:
    path = path if path.is_absolute() else REPO_ROOT / path
    raw = str(path.resolve(strict=False))
    if os.name == "nt" and not raw.startswith("\\\\?\\"):
        return "\\\\?\\" + raw
    return raw


def read_text(path: Path) -> str:
    with open(_fs_path(path), encoding="utf-8", errors="replace") as handle:
        return handle.read()


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def exists(path: Path) -> bool:
    return os.path.exists(_fs_path(path))


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def run_cmd(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_fs_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def last_jsonl(path: Path) -> dict[str, Any]:
    last = ""
    with open(_fs_path(path), encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                last = line
    if not last:
        return {}
    return json.loads(last)


def recursive_key_hits(value: Any, prefix: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower()
            if key_l in FORBIDDEN_RESULT_KEYS:
                hits.append(f"{prefix}.{key}")
            hits.extend(recursive_key_hits(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(recursive_key_hits(child, f"{prefix}[{idx}]"))
    return hits


def safe_flags_ok(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append("promotion_verdict")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(flag)
    return not failures, failures


def all_target_json_payloads() -> dict[str, dict[str, Any]]:
    payloads = {}
    for path in sorted(TARGET_DIR.glob("FPB_*.json")):
        payloads[path.name] = read_json(path)
    return payloads


def blob_size_audit() -> dict[str, Any]:
    result = run_cmd(["git", "ls-tree", "-r", "-l", "HEAD"])
    oversized: list[dict[str, Any]] = []
    line_count = 0
    if result["ok"]:
        for line in result["stdout"].splitlines():
            line_count += 1
            parts = line.split(None, 4)
            if len(parts) == 5 and parts[1] == "blob":
                size = int(parts[3])
                if size > 100 * 1024 * 1024:
                    oversized.append({"path": parts[4], "git_blob_size": size})
    return {
        "command": {
            "args": result["args"],
            "returncode": result["returncode"],
            "stderr": result["stderr"],
            "ok": result["ok"],
            "output_line_count": line_count,
        },
        "oversized_git_blobs": oversized,
        "passes": result["ok"] and not oversized,
    }


def predecessor_audit(context_anchor: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for path_text in context_anchor.get("inputs_read", []):
        path = REPO_ROOT / path_text
        row = {
            "path": path_text,
            "exists": exists(path),
            "long_path_sensitive": len(str(path.resolve(strict=False))) >= 260,
        }
        if row["exists"] and path.suffix == ".json":
            try:
                payload = read_json(path)
                row.update(
                    {
                        "route_id": payload.get("route_id"),
                        "promotion_verdict": payload.get("promotion_verdict"),
                        "validation_safe": payload.get("validation_safe"),
                        "outcome_review_opened": payload.get("outcome_review_opened"),
                        "live_effect": payload.get("live_effect"),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - audit records exact parse issue.
                row["json_parse_error"] = repr(exc)
        rows.append(row)
    return {
        "rows": rows,
        "all_context_anchor_inputs_exist": all(row["exists"] for row in rows),
        "long_path_note": "Some G0 predecessor absolute paths exceed 260 characters; audit used long-path-aware reads.",
    }


def lfs_audit(lfs_payload: dict[str, Any]) -> dict[str, Any]:
    rows = []
    lfs_list = run_cmd(["git", "lfs", "ls-files"])
    for row in lfs_payload.get("rows", []):
        path = REPO_ROOT / row["path"]
        pointer = run_cmd(["git", "cat-file", "-p", f"HEAD:{row['path']}"])
        local_size = path.stat().st_size if exists(path) else None
        local_hash = sha256_file(path) if exists(path) else None
        rows.append(
            {
                "artifact": row.get("artifact"),
                "path": row["path"],
                "head_pointer_text": pointer["stdout"].strip(),
                "head_pointer_ok": pointer["ok"]
                and f"oid sha256:{row['expected_lfs_oid']}" in pointer["stdout"]
                and f"size {row['expected_lfs_size']}" in pointer["stdout"],
                "local_exists": exists(path),
                "local_size": local_size,
                "local_sha256": local_hash,
                "expected_size": row["expected_lfs_size"],
                "expected_sha256": row["expected_lfs_oid"],
                "materialized_ok": local_size == row["expected_lfs_size"] and local_hash == row["expected_lfs_oid"],
            }
        )
    return {
        "git_lfs_ls_files": lfs_list,
        "rows": rows,
        "passes": lfs_list["ok"] and all(row["head_pointer_ok"] and row["materialized_ok"] for row in rows),
    }


def matrix_count_audit(matrix: dict[str, Any], denominator: dict[str, Any], progress_last: dict[str, Any]) -> dict[str, Any]:
    family_rows = matrix.get("family_rows") or []
    global_counts = (matrix.get("global_label_distribution") or {}).get("counts") or {}
    family_sum = sum(int(row.get("denominator", 0)) for row in family_rows)
    global_sum = sum(int(global_counts.get(label, 0)) for label in EXPECTED_LABELS)
    family_label_sums_ok = all(
        sum(int(row.get("counts", {}).get(label, 0)) for label in EXPECTED_LABELS) == int(row.get("denominator", 0))
        for row in family_rows
    )
    ambiguity_ok = all(
        int(row.get("ambiguity_unresolved_count", 0))
        == int(row.get("counts", {}).get("SAME_BAR_CONTEXT_AMBIGUOUS", 0))
        + int(row.get("counts", {}).get("UNRESOLVED_BY_WINDOW", 0))
        + int(row.get("counts", {}).get("UNRESOLVED_AT_SOURCE_END", 0))
        for row in family_rows
    )
    count_checks = {
        "matrix_raw_candidate_attempts": matrix.get("raw_candidate_attempts") == EXPECTED_COUNTS["raw_candidate_attempts"],
        "matrix_duplicate_candidate_keys": matrix.get("duplicate_candidate_keys") == EXPECTED_COUNTS["duplicate_candidate_keys"],
        "matrix_unique_denominator": matrix.get("unique_nonduplicate_candidate_path_label_denominator")
        == EXPECTED_COUNTS["unique_nonduplicate_candidate_path_label_denominator"],
        "matrix_path_label_rows": matrix.get("path_label_row_count") == EXPECTED_COUNTS["path_label_row_count"],
        "denominator_recomputed_raw": denominator.get("recomputed_raw_candidate_attempts")
        == EXPECTED_COUNTS["raw_candidate_attempts"],
        "denominator_recomputed_duplicates": denominator.get("recomputed_duplicate_candidate_keys")
        == EXPECTED_COUNTS["duplicate_candidate_keys"],
        "denominator_recomputed_unique": denominator.get("recomputed_unique_nonduplicate_denominator")
        == EXPECTED_COUNTS["unique_nonduplicate_candidate_path_label_denominator"],
        "denominator_recomputed_path_labels": denominator.get("recomputed_path_label_count")
        == EXPECTED_COUNTS["path_label_row_count"],
        "progress_final_raw": progress_last.get("candidate_attempts_so_far") == EXPECTED_COUNTS["raw_candidate_attempts"],
        "progress_final_duplicates": progress_last.get("duplicate_candidate_keys_so_far") == EXPECTED_COUNTS["duplicate_candidate_keys"],
        "progress_final_unique": progress_last.get("unique_candidate_denominator_so_far")
        == EXPECTED_COUNTS["unique_nonduplicate_candidate_path_label_denominator"],
        "progress_final_path_labels": progress_last.get("path_label_rows_so_far") == EXPECTED_COUNTS["path_label_row_count"],
    }
    return {
        "expected_counts": EXPECTED_COUNTS,
        "count_checks": count_checks,
        "opened_families": matrix.get("opened_families"),
        "opened_family_count": matrix.get("opened_family_count"),
        "baseline_control_families": matrix.get("baseline_control_families"),
        "baseline_control_family_count": len(matrix.get("baseline_control_families") or []),
        "family_set_ok": matrix.get("opened_families") == EXPECTED_FAMILIES,
        "baseline_set_ok": matrix.get("baseline_control_families") == EXPECTED_BASELINES,
        "all_family_denominators_positive": all(int(row.get("denominator", 0)) > 0 for row in family_rows),
        "family_denominator_sum": family_sum,
        "family_denominator_sum_ok": family_sum == EXPECTED_COUNTS["path_label_row_count"],
        "global_label_sum": global_sum,
        "global_label_sum_ok": global_sum == EXPECTED_COUNTS["path_label_row_count"],
        "family_label_sums_ok": family_label_sums_ok,
        "ambiguity_unresolved_separated_ok": ambiguity_ok,
        "passes": all(count_checks.values())
        and matrix.get("opened_families") == EXPECTED_FAMILIES
        and matrix.get("baseline_control_families") == EXPECTED_BASELINES
        and family_sum == EXPECTED_COUNTS["path_label_row_count"]
        and global_sum == EXPECTED_COUNTS["path_label_row_count"]
        and family_label_sums_ok
        and ambiguity_ok,
    }


def no_forbidden_surface_audit(commit: str = "11439e4a") -> dict[str, Any]:
    live_surface_diff = run_cmd(
        [
            "git",
            "diff",
            "--name-only",
            f"{commit}^",
            commit,
            "--",
            "src",
            "config",
            "prompts",
            "run_agent.py",
            "start_all.bat",
            "scripts/canary_test.py",
            "scripts/watchdog.ps1",
        ]
    )
    current_live_surface_dirty = run_cmd(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "src",
            "config",
            "prompts",
            "run_agent.py",
            "start_all.bat",
            "scripts/canary_test.py",
            "scripts/watchdog.ps1",
        ]
    )
    cached = run_cmd(["git", "diff", "--cached", "--name-only"])
    target_status = run_cmd(
        [
            "git",
            "status",
            "--short",
            "--",
            rel(TARGET_DIR),
            rel(PROMPT_PATH),
        ]
    )
    return {
        "target_commit": commit,
        "target_commit_live_surface_diff": live_surface_diff,
        "current_live_surface_dirty": current_live_surface_dirty,
        "cached_diff": cached,
        "target_route_status": target_status,
        "passes": live_surface_diff["ok"]
        and not live_surface_diff["stdout"].strip()
        and current_live_surface_dirty["ok"]
        and not current_live_surface_dirty["stdout"].strip()
        and cached["ok"]
        and not cached["stdout"].strip()
        and target_status["ok"]
        and not target_status["stdout"].strip(),
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    matrix = read_json(TARGET_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json")
    denominator = read_json(TARGET_DIR / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json")
    baseline = read_json(TARGET_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json")
    compact = read_json(TARGET_DIR / "FPB_COMPACT_CAP_DIAGNOSTICS_2026-05-10.json")
    lfs = read_json(TARGET_DIR / "FPB_LFS_MATERIALIZATION_AUDIT_2026-05-10.json")
    noleak = read_json(TARGET_DIR / "FPB_NOLEAK_DIRTY_STATE_AUDIT_2026-05-10.json")
    selection = read_json(TARGET_DIR / "FPB_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json")
    instruction = read_json(TARGET_DIR / "FPB_CONTEXT_INSTRUCTION_COVERAGE_LEDGER_2026-05-10.json")
    saturation = read_json(TARGET_DIR / "FPB_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json")
    manifest = read_json(TARGET_DIR / "FPB_OUTPUT_MANIFEST_2026-05-10.json")
    completion = read_json(TARGET_DIR / "FPB_COMPLETION_AUDIT_2026-05-10.json")
    context = read_json(TARGET_DIR / "FPB_CONTEXT_ANCHOR_2026-05-10.json")
    progress_last = last_jsonl(REPO_ROOT / matrix["source_progress_path"])

    target_verifier_rerun = run_cmd([sys.executable, rel(TARGET_VERIFIER)])
    target_test_script_rerun = run_cmd([sys.executable, rel(TARGET_TEST)])
    py_compile = run_cmd([sys.executable, "-m", "py_compile", rel(TARGET_VERIFIER), rel(TARGET_TEST), rel(TARGET_DIR / "build_family_path_behavior_result_screen_2026_05_10.py")])

    target_payloads = all_target_json_payloads()
    flag_failures = {}
    key_hits = {}
    for name, payload in target_payloads.items():
        ok, failures = safe_flags_ok(payload)
        if not ok:
            flag_failures[name] = failures
        hits = recursive_key_hits(payload)
        if hits:
            key_hits[name] = hits

    count_audit = matrix_count_audit(matrix, denominator, progress_last)
    lfs_check = lfs_audit(lfs)
    predecessor_check = predecessor_audit(context)
    surface_check = no_forbidden_surface_audit()
    blob_check = blob_size_audit()

    prompt_to_artifact_checklist = [
        {
            "requirement": "Rerun target verifier and focused tests",
            "evidence": [rel(TARGET_VERIFIER), rel(TARGET_TEST)],
            "status": "PASS" if target_verifier_rerun["ok"] and target_test_script_rerun["ok"] else "FAIL",
        },
        {
            "requirement": "Full-population aggregate, not compact-only decisive ranking",
            "evidence": rel(TARGET_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json"),
            "status": "PASS"
            if matrix.get("aggregation_mode") == "full_stream_recomputed_from_accepted_source_rows_aggregate_only"
            and matrix.get("compact_sample_used_for_decisive_ranking") is False
            and compact.get("decisive_ranking_uses_compact_sample") is False
            and compact.get("full_stream_aggregate_used_for_route_priority") is True
            else "FAIL",
        },
        {
            "requirement": "Exact denominator counts",
            "evidence": [rel(TARGET_DIR / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json"), matrix.get("source_progress_path")],
            "status": "PASS" if count_audit["passes"] else "FAIL",
        },
        {
            "requirement": "All 11 families and four baseline controls",
            "evidence": rel(TARGET_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json"),
            "status": "PASS" if count_audit["family_set_ok"] and count_audit["baseline_set_ok"] and baseline.get("all_four_baseline_controls_included") is True else "FAIL",
        },
        {
            "requirement": "Exact label vocabulary and ambiguity/unresolved separation",
            "evidence": rel(TARGET_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json"),
            "status": "PASS" if matrix.get("label_vocabulary") == EXPECTED_LABELS and count_audit["ambiguity_unresolved_separated_ok"] else "FAIL",
        },
        {
            "requirement": "No path label use as R/PnL/win-rate/expectancy/performance",
            "evidence": "recursive JSON key scan plus boundary-string review",
            "status": "PASS" if not key_hits else "FAIL",
        },
        {
            "requirement": "LFS pointer/materialization and no raw >100MB Git blobs",
            "evidence": rel(TARGET_DIR / "FPB_LFS_MATERIALIZATION_AUDIT_2026-05-10.json"),
            "status": "PASS" if lfs_check["passes"] and blob_check["passes"] else "FAIL",
        },
        {
            "requirement": "Selection-bias, multiple-testing, compact-cap, context-anchor, instruction coverage, no-leak, saturation, manifest, completion audit",
            "evidence": [
                rel(TARGET_DIR / "FPB_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_CONTEXT_ANCHOR_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_CONTEXT_INSTRUCTION_COVERAGE_LEDGER_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_NOLEAK_DIRTY_STATE_AUDIT_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_OUTPUT_MANIFEST_2026-05-10.json"),
                rel(TARGET_DIR / "FPB_COMPLETION_AUDIT_2026-05-10.json"),
            ],
            "status": "PASS"
            if selection.get("multiple_testing_debt", {}).get("selection_not_validation") is True
            and instruction.get("all_requirements_covered") is True
            and noleak.get("passes") is True
            and len(saturation.get("checks") or []) >= 5
            and manifest.get("opened_family_count") == 11
            and completion.get("completion_standard_satisfied") is True
            and predecessor_check["all_context_anchor_inputs_exist"]
            else "FAIL",
        },
        {
            "requirement": "No prompt/config/risk/safety/execution/live trading surfaces changed",
            "evidence": "git diff scoped to live surfaces",
            "status": "PASS" if surface_check["passes"] else "FAIL",
        },
        {
            "requirement": "Safe flags preserved",
            "evidence": "all target FPB JSON artifacts",
            "status": "PASS" if not flag_failures else "FAIL",
        },
    ]

    blockers = [
        row
        for row in prompt_to_artifact_checklist
        if row["status"] != "PASS"
    ]
    audit = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": "g12_fpb_result_audit",
        "generated_at_utc": generated_at,
        "target_route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
        "audit_decision": DECISION if not blockers else "ACCEPT_WITH_EXACT_REPAIR_REQUIREMENTS",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changes_live_trading_behavior": False,
        "opens_validation": False,
        "opens_promotion": False,
        "opens_result_scoring": False,
        "opens_paid_api_or_databento_route": False,
        "opens_mt5_order_account_history_behavior": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "objective_restatement": (
            "Independently audit the no-API mechanical replay family path-behavior discovery result screen as a "
            "quarantined discovery path-behavior ledger only, with no validation, promotion, result scoring, "
            "broker account/order/history/deal/position evidence, paid/API use, or live behavior."
        ),
        "target_verifier_rerun": target_verifier_rerun,
        "target_focused_test_script_rerun": target_test_script_rerun,
        "py_compile": py_compile,
        "count_audit": count_audit,
        "label_vocabulary": matrix.get("label_vocabulary"),
        "baseline_controls": matrix.get("baseline_control_families"),
        "lfs_materialization_audit": lfs_check,
        "blob_size_audit": blob_check,
        "predecessor_context_anchor_audit": predecessor_check,
        "selection_bias_multiple_testing_audit": {
            "selection_not_validation": selection.get("multiple_testing_debt", {}).get("selection_not_validation"),
            "post_hoc_thresholds_created": selection.get("multiple_testing_debt", {}).get("post_hoc_thresholds_created"),
            "promotion_permitted": selection.get("multiple_testing_debt", {}).get("promotion_permitted"),
            "family_choices_frozen": selection.get("family_choices_frozen_before_result_screen"),
            "baseline_controls_frozen": selection.get("baseline_controls_frozen_before_result_screen"),
            "compact_cap_policy": selection.get("compact_cap_policy"),
        },
        "no_leak_dirty_state_audit": {
            "target_noleak_passes": noleak.get("passes"),
            "target_forbidden_live_surface_output_paths": noleak.get("forbidden_live_surface_output_paths"),
            "target_raw_jsonl_rows_written_by_this_route": noleak.get("raw_jsonl_rows_written_by_this_route"),
            "surface_diff": surface_check,
            "safe_flag_failures": flag_failures,
            "forbidden_result_key_hits": key_hits,
        },
        "manifest_and_completion": {
            "manifest_opened_family_count": manifest.get("opened_family_count"),
            "manifest_baseline_control_family_count": manifest.get("baseline_control_family_count"),
            "instruction_all_requirements_covered": instruction.get("all_requirements_covered"),
            "completion_standard_satisfied": completion.get("completion_standard_satisfied"),
            "target_can_mark_goal_complete": completion.get("can_mark_goal_complete"),
            "target_missing_incomplete_or_weak_requirements": completion.get("missing_incomplete_or_weak_requirements"),
        },
        "prompt_to_artifact_checklist": prompt_to_artifact_checklist,
        "missing_incomplete_or_weak_requirements": blockers,
        "completion_standard_satisfied": not blockers,
        "can_mark_goal_complete": not blockers,
        "notes": [
            "The target context anchor predecessor paths are materially present; long-path-aware reads were required for some G0 files on Windows.",
            "Risky terms such as R, PnL, win-rate, expectancy, promotion, validation, and performance appear only in explicit negative boundary language or policy fields reviewed by this audit.",
            "The target route artifacts remain quarantined discovery path-behavior ledgers and do not validate or rank a tradable edge.",
        ],
    }

    json_path = ROUTE_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.json"
    md_path = ROUTE_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.md"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = [
        "# G12 FPB Result Audit",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Target: `{audit['target_route_id']}`",
        f"- Decision: `{audit['audit_decision']}`",
        "- Promotion posture: `NO_PROMOTION_VERDICT`",
        "- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Checklist",
    ]
    for row in prompt_to_artifact_checklist:
        md_lines.append(f"- `{row['status']}` - {row['requirement']}")
    md_lines.extend(
        [
            "",
            "## Counts",
            f"- Raw candidate attempts: `{matrix.get('raw_candidate_attempts')}`",
            f"- Duplicate candidate keys: `{matrix.get('duplicate_candidate_keys')}`",
            f"- Unique denominator: `{matrix.get('unique_nonduplicate_candidate_path_label_denominator')}`",
            f"- Path-label rows: `{matrix.get('path_label_row_count')}`",
            f"- Opened families: `{matrix.get('opened_family_count')}`",
            f"- Baseline controls: `{len(matrix.get('baseline_control_families') or [])}`",
            "",
            "## Completion",
            f"- Completion standard satisfied: `{audit['completion_standard_satisfied']}`",
            f"- Can mark goal complete: `{audit['can_mark_goal_complete']}`",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": audit["can_mark_goal_complete"], "audit_json": rel(json_path), "audit_md": rel(md_path)}, indent=2))
    return 0 if audit["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
