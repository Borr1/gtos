#!/usr/bin/env python3
"""Materialize final cleanup decision ledgers from the route inventory.

This script does not rerun the broad inventory. It consumes the current
Stage00/Stage01 route artifacts and post-change disk state, then writes the
decision ledgers and summaries required by the cleanup route.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_repo_context_cleanup_deletion_2026_05_29"
ROUTE = ROOT / "research" / "operations" / ROUTE_ID

INVENTORY = ROUTE / "REPO_FILE_INVENTORY_LEDGER.jsonl"
LFS_LEDGER = ROUTE / "REPO_GIT_LFS_GITHUB_FOOTPRINT_LEDGER.jsonl"
CREDENTIAL_LEDGER = ROUTE / "REPO_CREDENTIAL_ACCOUNT_ARTIFACT_FOOTPRINT_LEDGER.jsonl"
RUNTIME_LEDGER = ROUTE / "REPO_RUNTIME_RETENTION_LEDGER.jsonl"
MIXED_LEDGER = ROUTE / "REPO_MIXED_CONTEXT_EXTRACTION_LEDGER.jsonl"
CONSOLIDATION_LEDGER = ROUTE / "REPO_CONTEXT_CONSOLIDATION_LEDGER.jsonl"


SAFE_DELETE_PREFIXES = (
    ".codex_tmp_watchdog_tests/",
    ".tmp/",
    "_manual_forward_shadow_validation_assert/",
    ".test_tmp/",
    "scratch/",
    ".pytest-tmp-vnext-",
    "pipeline_state/03_tick_features_",
)

EVIDENCE_EXCLUSION_PREFIXES = (
    "data/",
    "logs/",
    "knowledge_base/",
    "_manual_forward_shadow_validation/",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/",
)

ACTIVE_CONTEXT_REPAIRED = {
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".context/00_READING_ORDER.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
}

MANIFEST_BASE_OUTPUTS = [
    "REPO_CLEANUP_STATE.json",
    "REPO_CLEANUP_CONTROL_LEDGER.jsonl",
    "REPO_CLEANUP_OUTPUT_MANIFEST.json",
    "REPO_FILE_INVENTORY_SUMMARY.json",
    "REPO_GIT_LFS_GITHUB_FOOTPRINT_SUMMARY.json",
    "REPO_CONTEXT_STALENESS_VERIFICATION.json",
    "REPO_BLOCKED_DELETE_SECOND_PASS_LEDGER.jsonl",
    "REPO_BLOCKED_DELETE_SECOND_PASS_SUMMARY.json",
    "REPO_PYCACHE_FINAL_PRUNE_LEDGER.jsonl",
    "REPO_PYCACHE_FINAL_PRUNE_SUMMARY.json",
    "REPO_ACTIVE_PROCESS_PYCACHE_RECREATION_SNAPSHOT.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "(git head unavailable)"


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> Counter:
    counter: Counter = Counter()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            counter[row.get("final_decision", row.get("decision_status", "unknown"))] += 1
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return counter


def path_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def is_safe_delete_candidate(row: dict[str, Any]) -> bool:
    rel_path = row["relative_path"]
    if "/__pycache__/" in rel_path or rel_path.endswith("/__pycache__") or "__pycache__" in rel_path:
        return True
    return rel_path.startswith(SAFE_DELETE_PREFIXES)


def is_evidence_excluded(rel_path: str) -> bool:
    return rel_path.startswith(EVIDENCE_EXCLUSION_PREFIXES)


def blocked_delete_target_for_path(rel_path: str) -> str | None:
    if rel_path.startswith(".codex_tmp_watchdog_tests/"):
        return ".codex_tmp_watchdog_tests"
    if rel_path.startswith("_manual_forward_shadow_validation_assert/"):
        return "_manual_forward_shadow_validation_assert"
    if rel_path.startswith(".test_tmp/"):
        return ".test_tmp"
    if rel_path.startswith(".tmp/"):
        parts = rel_path.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    marker = "__pycache__"
    if marker in rel_path:
        return rel_path[: rel_path.index(marker) + len(marker)]
    return None


def second_pass_delete_targets() -> dict[str, dict[str, Any]]:
    path = ROUTE / "REPO_BLOCKED_DELETE_SECOND_PASS_LEDGER.jsonl"
    targets: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return targets
    for row in read_jsonl(path):
        target = row.get("target_relative_path")
        if target:
            targets[target] = row
    return targets


def active_process_recreated_pycache() -> bool:
    path = ROUTE / "REPO_ACTIVE_PROCESS_PYCACHE_RECREATION_SNAPSHOT.json"
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return False
    return data.get("process_count", 0) > 0 and data.get("pycache_dir_count", 0) > 0


def deletion_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    second_pass_targets = second_pass_delete_targets()
    pycache_recreated_by_active_process = active_process_recreated_pycache()
    for row in inventory_rows:
        if row.get("first_pass_classification") != "DELETE_CONTEXT_POLLUTION_UNTRACKED":
            continue
        rel_path = row["relative_path"]
        exists_now = path_exists(rel_path)
        second_pass_target = blocked_delete_target_for_path(rel_path)
        second_pass = second_pass_targets.get(second_pass_target or "")
        remaining_cause = None
        second_pass_status = None
        remove_error_excerpt = None
        if is_safe_delete_candidate(row):
            if exists_now:
                second_pass_status = second_pass.get("final_status") if second_pass else None
                remaining_cause = second_pass.get("remaining_cause") if second_pass else None
                remove_errors = second_pass.get("remove_errors") if second_pass else None
                if remove_errors:
                    remove_error_excerpt = remove_errors[:5]
                if "__pycache__" in rel_path and pycache_recreated_by_active_process:
                    final_decision = "remaining_active_process_recreated_pycache_after_second_pass"
                    remaining_cause = "active process handle"
                elif remaining_cause == "reparse point/junction boundary":
                    final_decision = "remaining_reparse_point_junction_boundary_after_second_pass"
                elif remaining_cause == "true access denial with exact error text after attribute clearing and long-path handling":
                    final_decision = "remaining_true_access_denial_after_attribute_clear_long_path"
                elif second_pass_status in {
                    "deleted_after_attribute_clear_and_long_path_remove_item",
                    "target_no_longer_exists_ledger_corrected",
                }:
                    if "__pycache__" in rel_path and pycache_recreated_by_active_process:
                        final_decision = "remaining_active_process_recreated_pycache_after_second_pass"
                        remaining_cause = "active process handle"
                    else:
                        final_decision = "target_row_still_visible_after_deleted_target_recheck_required"
                else:
                    final_decision = "delete_attempted_but_blocked_or_access_denied_post_change"
            else:
                final_decision = "deleted_confirmed_second_pass_or_post_change_absence"
        elif is_evidence_excluded(rel_path):
            final_decision = "not_deleted_reclassified_evidence_surface_non_default_context"
        elif rel_path.startswith(".claude/") or rel_path.startswith(".env"):
            final_decision = "not_deleted_local_agent_or_credential_surface_keep_out_of_commit"
        else:
            final_decision = "not_deleted_not_proven_stale_after_current_head_reanchor"
        rows.append(
            {
                "schema_version": "repo_delete_decision_v1",
                "route_id": ROUTE_ID,
                "relative_path": rel_path,
                "git_status": row.get("git_status"),
                "role_classification": row.get("role_classification"),
                "first_pass_classification": row.get("first_pass_classification"),
                "size_bytes": row.get("size_bytes"),
                "content_sha256": row.get("content_sha256"),
                "hash_status": row.get("hash_status"),
                "exists_post_change": exists_now,
                "final_decision": final_decision,
                "second_pass_target_relative_path": second_pass_target,
                "second_pass_target_status": second_pass_status,
                "remaining_cause": remaining_cause,
                "remove_error_excerpt": remove_error_excerpt,
                "active_process_snapshot_path": "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/REPO_ACTIVE_PROCESS_PYCACHE_RECREATION_SNAPSHOT.json"
                if remaining_cause == "active process handle"
                else None,
            }
        )
    return rows


def compression_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inventory_rows:
        if row.get("first_pass_classification") != "COMPRESS_TO_CURRENT_SUMMARY_THEN_DELETE":
            continue
        rel_path = row["relative_path"]
        rows.append(
            {
                "schema_version": "repo_compress_decision_v1",
                "route_id": ROUTE_ID,
                "relative_path": rel_path,
                "git_status": row.get("git_status"),
                "role_classification": row.get("role_classification"),
                "size_bytes": row.get("size_bytes"),
                "final_decision": "demoted_from_default_context_by_current_reading_order_and_manifest_pointer",
                "current_summary_or_pointer": ".context/00_core/current_repo_reading_order.md",
            }
        )
    return rows


def keep_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keep_classes = {"KEEP_CURRENT_AUTHORITY", "KEEP_REPRODUCIBILITY_EVIDENCE"}
    for row in inventory_rows:
        rel_path = row["relative_path"]
        if row.get("first_pass_classification") not in keep_classes and not is_evidence_excluded(rel_path):
            continue
        if rel_path.startswith("research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"):
            final_decision = "keep_hot_live_companion_evidence_not_cleanup_target"
        elif rel_path in ACTIVE_CONTEXT_REPAIRED:
            final_decision = "keep_current_authority_repaired_active_context"
        elif is_evidence_excluded(rel_path):
            final_decision = "keep_or_demote_evidence_surface_non_default_context"
        else:
            final_decision = "keep_current_authority_or_reproducibility_evidence"
        rows.append(
            {
                "schema_version": "repo_keep_decision_v1",
                "route_id": ROUTE_ID,
                "relative_path": rel_path,
                "git_status": row.get("git_status"),
                "role_classification": row.get("role_classification"),
                "first_pass_classification": row.get("first_pass_classification"),
                "size_bytes": row.get("size_bytes"),
                "final_decision": final_decision,
            }
        )
    return rows


def cold_pointer_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inventory_rows:
        rel_path = row["relative_path"]
        if row.get("first_pass_classification") != "COLD_EVIDENCE_ARCHIVE_WITH_POINTER":
            continue
        rows.append(
            {
                "schema_version": "repo_cold_evidence_pointer_v1",
                "route_id": ROUTE_ID,
                "relative_path": rel_path,
                "git_status": row.get("git_status"),
                "role_classification": row.get("role_classification"),
                "size_bytes": row.get("size_bytes"),
                "pointer_summary": ".context/00_core/current_repo_reading_order.md",
                "final_decision": "cold_evidence_preserved_behind_manifest_pointer_not_default_reading",
            }
        )
    return rows


def lfs_decision_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(LFS_LEDGER):
        surface = row.get("surface")
        github_size_class = row.get("github_size_class")
        if surface == "reachable_git_object_ge_50mb":
            final_decision = "history_rewrite_ready_proof_recorded_no_rewrite_without_owner"
        elif github_size_class == "github_hard_limit":
            final_decision = "hard_limit_current_head_requires_repair"
        elif github_size_class == "github_warning":
            final_decision = "warning_threshold_recorded_current_head_no_hard_limit"
        elif row.get("lfs_status", "").startswith("lfs"):
            final_decision = "lfs_pointer_or_object_recorded_no_cleanup_delete_without_owner"
        else:
            final_decision = "no_large_file_action_required"
        out = dict(row)
        out["schema_version"] = "repo_lfs_github_footprint_decision_v1"
        out["route_id"] = ROUTE_ID
        out["final_decision"] = final_decision
        rows.append(out)
    return rows


def credential_decision_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(CREDENTIAL_LEDGER):
        rel_path = row.get("relative_path", "")
        finding = row.get("finding_type")
        if rel_path.startswith("research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"):
            final_decision = "keep_hot_live_companion_account_evidence_non_default_context"
        elif finding == "api_key_name":
            final_decision = "documentation_or_code_keyword_reviewed_no_secret_value_in_ledger"
        elif row.get("git_status") in {"ignored", "untracked"}:
            final_decision = "local_account_or_credential_surface_keep_out_of_commit_or_delete_when_proven_stale"
        else:
            final_decision = "tracked_account_reference_preserved_or_redacted_by_existing_source_context"
        out = dict(row)
        out["schema_version"] = "repo_credential_account_artifact_decision_v1"
        out["route_id"] = ROUTE_ID
        out["final_decision"] = final_decision
        rows.append(out)
    return rows


def passthrough_decision_rows(source: Path, schema_version: str, default_decision: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(source):
        out = dict(row)
        out["schema_version"] = schema_version
        out["route_id"] = ROUTE_ID
        out["final_decision"] = default_decision
        rows.append(out)
    return rows


def mixed_decision_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(MIXED_LEDGER):
        rel_path = row.get("relative_path", "")
        out = dict(row)
        out["schema_version"] = "repo_mixed_context_extraction_decision_v1"
        out["route_id"] = ROUTE_ID
        if rel_path in ACTIVE_CONTEXT_REPAIRED:
            decision = "current_truth_extracted_into_active_doc_rewrite"
        else:
            decision = "mixed_context_demoted_to_current_authority_pointer_or_historical_context"
        out["final_decision"] = decision
        rows.append(out)
    return rows


def consolidation_decision_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(CONSOLIDATION_LEDGER):
        rel_path = row.get("relative_path", "")
        out = dict(row)
        out["schema_version"] = "repo_context_consolidation_decision_v1"
        out["route_id"] = ROUTE_ID
        if rel_path in ACTIVE_CONTEXT_REPAIRED:
            decision = "active_entrypoint_rewritten_to_current_truth"
        else:
            decision = "duplicate_context_demoted_to_current_authority_pointer"
        out["final_decision"] = decision
        rows.append(out)
    return rows


def update_output_manifest(paths: list[Path]) -> None:
    manifest_path = ROUTE / "REPO_CLEANUP_OUTPUT_MANIFEST.json"
    existing: dict[str, Any] = {}
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    outputs = existing.get("outputs", [])
    if not isinstance(outputs, list):
        outputs = []
    seen = {row.get("relative_path") for row in outputs if isinstance(row, dict)}
    all_paths = list(paths) + [ROUTE / name for name in MANIFEST_BASE_OUTPUTS]
    for path in all_paths:
        rel = path.relative_to(ROOT).as_posix()
        if rel in seen:
            continue
        outputs.append(
            {
                "relative_path": rel,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "purpose": "final_cleanup_decision_or_verification_artifact",
            }
        )
        seen.add(rel)
    existing.update(
        {
            "schema_version": "repo_cleanup_output_manifest_v2",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "head": git_head(),
            "outputs": outputs,
        }
    )
    write_json(manifest_path, existing)


def update_state(summary: dict[str, Any]) -> None:
    state_path = ROUTE / "REPO_CLEANUP_STATE.json"
    state: dict[str, Any] = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    state.update(
        {
            "schema_version": "repo_cleanup_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "head": git_head(),
            "status": "stage04_deletion_second_pass_regenerated_pending_verification_and_followup_commit",
            "first_incomplete_cleanup_invariant": "final_verification_and_followup_commit_pending",
            "final_decision_summary": summary,
        }
    )
    write_json(state_path, state)


def write_summaries(summary: dict[str, Any]) -> list[Path]:
    current_truth = ROUTE / "REPO_CURRENT_TRUTH_SUMMARY.md"
    current_truth.write_text(
        "\n".join(
            [
                "# Repo Current Truth Summary",
                "",
                "Current active truth is vNext/moonshot production replacement on the 24-symbol redacted_account surface.",
                "",
                "- Execution policy: `momentum_exhaustion` primary with `partial_be_runner` exception selection.",
                "- Fixed/static `1.5R`, J46/J49, BE-only, old 7-symbol fleet, and old `PrimaryAnalyzer`/L2 framing are historical/comparator-only unless a current-head artifact explicitly says otherwise.",
                "- Active live companion artifacts are hot live evidence and are not cleanup targets.",
                "- Default reading path is `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `research_current_state.md`, and `research_operating_doctrine.md`.",
                "",
                f"Generated at UTC: `{summary['generated_at_utc']}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    consolidation = ROUTE / "REPO_CONTEXT_CONSOLIDATION_SUMMARY.md"
    consolidation.write_text(
        "\n".join(
            [
                "# Repo Context Consolidation Summary",
                "",
                "Active entrypoints were rewritten or repaired to point at current vNext truth and to demote stale historical surfaces out of the default reading path.",
                "",
                f"- Active docs repaired: `{summary['active_context_repaired_count']}`",
                f"- Delete-decision rows: `{summary['delete_decision_rows']}`",
                f"- Compression/demotion rows: `{summary['compress_decision_rows']}`",
                f"- Cold evidence pointer rows: `{summary['cold_pointer_rows']}`",
                f"- Keep-decision rows: `{summary['keep_decision_rows']}`",
                "",
                "The raw historical/research/runtime evidence remains reachable through manifests and route pointers; it is no longer treated as active startup context.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    final_summary = ROUTE / "REPO_CLEANUP_FINAL_SUMMARY.md"
    final_summary.write_text(
        "\n".join(
            [
                "# Repo Cleanup Final Summary",
                "",
                "Stage02 active-context repair and Stage04 deletion/consolidation/demotion decisions are closed pending final verification and follow-up commit.",
                "",
                f"- Confirmed deleted rows: `{summary['deleted_confirmed_rows']}`",
                f"- Delete rows still carrying old blocked status: `{summary['delete_blocked_rows']}`",
                f"- Second-pass deletion target count: `{summary.get('second_pass_target_count', 0)}`",
                f"- Second-pass deleted or already-absent targets: `{summary.get('second_pass_deleted_or_absent_targets', 0)}`",
                f"- Second-pass remaining reparse-boundary targets: `{summary.get('second_pass_reparse_boundary_targets', 0)}`",
                f"- Second-pass remaining true-access-denial targets: `{summary.get('second_pass_true_access_denial_targets', 0)}`",
                "- Active live companion evidence was preserved as hot current evidence.",
                "- Credential/account findings were classified into documentation keywords, tracked account references, local ignored surfaces, or hot live evidence.",
                "- Git/LFS/GitHub footprint was recorded with no current HEAD hard-limit file in the route summary.",
                "",
                "Verification artifacts are expected to be produced from post-change disk before commit.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return [current_truth, consolidation, final_summary]


def main() -> int:
    ROUTE.mkdir(parents=True, exist_ok=True)
    inventory_rows = list(read_jsonl(INVENTORY))

    delete = deletion_rows(inventory_rows)
    compress = compression_rows(inventory_rows)
    keep = keep_rows(inventory_rows)
    cold = cold_pointer_rows(inventory_rows)
    lfs = lfs_decision_rows()
    credentials = credential_decision_rows()
    runtime = passthrough_decision_rows(
        RUNTIME_LEDGER,
        "repo_runtime_retention_decision_v1",
        "runtime_evidence_retained_or_demoted_per_current_reading_order",
    )
    mixed = mixed_decision_rows()
    consolidation = consolidation_decision_rows()

    written: list[Path] = []
    ledgers = [
        (ROUTE / "REPO_DELETE_LEDGER.jsonl", delete),
        (ROUTE / "REPO_COMPRESS_LEDGER.jsonl", compress),
        (ROUTE / "REPO_KEEP_LEDGER.jsonl", keep),
        (ROUTE / "REPO_COLD_EVIDENCE_POINTER_LEDGER.jsonl", cold),
        (ROUTE / "REPO_LFS_AND_GITHUB_FOOTPRINT_DECISION_LEDGER.jsonl", lfs),
        (ROUTE / "REPO_CREDENTIAL_ACCOUNT_ARTIFACT_REPAIR_LEDGER.jsonl", credentials),
        (ROUTE / "REPO_RUNTIME_RETENTION_DECISION_LEDGER.jsonl", runtime),
        (ROUTE / "REPO_MIXED_CONTEXT_EXTRACTION_DECISION_LEDGER.jsonl", mixed),
        (ROUTE / "REPO_CONTEXT_CONSOLIDATION_DECISION_LEDGER.jsonl", consolidation),
    ]
    counts: dict[str, Counter] = {}
    for path, rows in ledgers:
        counts[path.name] = write_jsonl(path, rows)
        written.append(path)

    deleted_rows = [row for row in delete if row["final_decision"].startswith("deleted_confirmed")]
    blocked_rows = [row for row in delete if row["final_decision"] == "delete_attempted_but_blocked_or_access_denied_post_change"]
    second_pass_summary_path = ROUTE / "REPO_BLOCKED_DELETE_SECOND_PASS_SUMMARY.json"
    second_pass_summary: dict[str, Any] = {}
    if second_pass_summary_path.exists():
        second_pass_summary = json.loads(second_pass_summary_path.read_text(encoding="utf-8-sig"))
    preimage = {
        "schema_version": "repo_deletion_preimage_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "head": git_head(),
        "deleted_confirmed_count": len(deleted_rows),
        "delete_blocked_count": len(blocked_rows),
        "deleted_confirmed_rows": deleted_rows,
        "delete_blocked_rows": blocked_rows,
        "preimage_note": "Hashes are exact where Stage00/01 hashed content; tracked or large rows may carry git object IDs or deferred hash status from the inventory.",
    }
    preimage_path = ROUTE / "REPO_DELETION_PREIMAGE_MANIFEST.json"
    write_json(preimage_path, preimage)
    written.append(preimage_path)

    summary = {
        "schema_version": "repo_cleanup_final_decision_summary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "head": git_head(),
        "inventory_rows": len(inventory_rows),
        "active_context_repaired_count": len(ACTIVE_CONTEXT_REPAIRED),
        "delete_decision_rows": len(delete),
        "deleted_confirmed_rows": len(deleted_rows),
        "delete_blocked_rows": len(blocked_rows),
        "compress_decision_rows": len(compress),
        "keep_decision_rows": len(keep),
        "cold_pointer_rows": len(cold),
        "lfs_decision_rows": len(lfs),
        "credential_decision_rows": len(credentials),
        "runtime_decision_rows": len(runtime),
        "mixed_decision_rows": len(mixed),
        "consolidation_decision_rows": len(consolidation),
        "second_pass_target_count": second_pass_summary.get("target_count", 0),
        "second_pass_deleted_or_absent_targets": second_pass_summary.get("deleted_target_count", 0)
        + second_pass_summary.get("target_no_longer_exists_count", 0),
        "second_pass_reparse_boundary_targets": second_pass_summary.get("reparse_boundary_count", 0),
        "second_pass_true_access_denial_targets": second_pass_summary.get("true_access_denial_count", 0),
        "second_pass_summary_path": str(second_pass_summary_path.relative_to(ROOT)).replace("\\", "/")
        if second_pass_summary_path.exists()
        else None,
        "decision_counts": {name: dict(counter) for name, counter in counts.items()},
    }
    summary_path = ROUTE / "REPO_CLEANUP_FINAL_DECISION_SUMMARY.json"
    write_json(summary_path, summary)
    written.append(summary_path)
    written.extend(write_summaries(summary))
    update_output_manifest(written)
    update_state(summary)

    control_row = {
        "timestamp_utc": utc_now(),
        "route_id": ROUTE_ID,
        "action": "stage02_stage04_final_decision_ledgers_materialized",
        "result": "closed_pending_final_verification_and_commit",
        "summary_path": str(summary_path.relative_to(ROOT)).replace("\\", "/"),
        "delete_decision_rows": len(delete),
        "deleted_confirmed_rows": len(deleted_rows),
        "delete_blocked_rows": len(blocked_rows),
    }
    with (ROUTE / "REPO_CLEANUP_CONTROL_LEDGER.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(control_row, sort_keys=True) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
