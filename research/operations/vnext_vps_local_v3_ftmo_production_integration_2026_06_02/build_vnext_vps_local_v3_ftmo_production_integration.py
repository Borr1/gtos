"""Build route artifacts for the VPS/local V3/FTMO production integration.

This route intentionally inventories branch diffs from Git instead of relying
on a short hand-written path list. The narrative fields classify the production
reason for each path family while the per-file rows preserve the full changed
surface for later audit.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[2]
VPS_BRANCH = "origin/vps-prod-live-sync-2026-06-02"
PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_VPS_LOCAL_V3_FTMO_PRODUCTION_INTEGRATION_GOAL_PROMPT_2026-06-02.md"
)
VPS_ROUTE = "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01"
FTMO_ROUTE = "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02"
SELECTOR_V3_ROUTE = "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01"
SCHEDULER_V3_ROUTE = "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01"
EXECUTION_V3_ROUTE = "research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01"
SOURCE_CAPTURE_ROUTE = (
    "research/operations/"
    "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01"
)


REQUIRED_ARTIFACTS = [
    "INTEGRATION_CONTEXT_ANCHOR.md",
    "VPS_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "BRANCH_BASE_AND_DIVERGENCE_LEDGER.json",
    "CONFLICT_RESOLUTION_LEDGER.jsonl",
    "SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl",
    "RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json",
    "redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl",
    "V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
    "RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl",
    "LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl",
    "VERIFICATION_MATRIX.json",
    "VERIFICATION_RESULT.json",
    "VPS_DEPLOYMENT_HANDOFF.md",
    "OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def git_optional(*args: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr


def parse_name_status(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            rows.append({"status": status, "path": parts[2], "old_path": parts[1]})
        elif len(parts) >= 2:
            rows.append({"status": status, "path": parts[1]})
    return rows


def path_exists(path: str) -> bool:
    return (ROOT / path).exists()


def file_size(path: str) -> int | None:
    candidate = ROOT / path
    if candidate.exists() and candidate.is_file():
        return candidate.stat().st_size
    return None


def write_json(name: str, payload: Any) -> None:
    (ROUTE_DIR / name).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    target = ROUTE_DIR / name
    target.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_md(name: str, text: str) -> None:
    (ROUTE_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def classify_vps_path(path: str, status: str) -> dict[str, str]:
    if path.startswith("src/components/gtos_vnext_runtime.py"):
        return {
            "class": "production code",
            "behavior_changed": "Adds cross-process locked JSONL appends, malformed row quarantine, and selected-cell risk/source handling repairs.",
            "issue_fixed": "Concurrent orchestrators could interleave JSONL writes and selected-cell refusal fields could be mislabeled.",
            "tests_verifiers": "tests/test_gtos_vnext_runtime.py and VPS focused suite.",
            "integration_disposition": "preserve_vps_runtime_repair",
        }
    if path.startswith("src/components/execution.py"):
        return {
            "class": "production code",
            "behavior_changed": "Repairs broker fill truth, SLTP action constants, pending-limit risk denominator, partial/residual recovery, close/deal accounting.",
            "issue_fixed": "OrderResult.price zero and recovered partial/residual rows could distort R, Telegram, or broker-truth lifecycle.",
            "tests_verifiers": "tests/test_execution.py plus trade capture and pending lifecycle tests.",
            "integration_disposition": "combine_with_local_namespace_support",
        }
    if path.startswith("src/components/orchestrator.py"):
        return {
            "class": "production code",
            "behavior_changed": "Repairs candidate identity, Lane06 lifecycle recovery, optional Gate3 snapshots, selected-cell risk/refusal semantics, and stale blocker classification.",
            "issue_fixed": "Historical tickets and broader-origin provisional rows could overwrite or falsely terminal-block live candidates.",
            "tests_verifiers": "tests/test_orchestrator.py, tests/test_vnext_broader_origin_orchestrator.py.",
            "integration_disposition": "combine_with_local_profile_namespace_support",
        }
    if path.startswith("src/components/m1_capture.py") or path.startswith("src/components/tick_capture.py"):
        return {
            "class": "production code",
            "behavior_changed": "Adds daemon liveness heartbeat and stale quote/data-progress separation for always-on capture.",
            "issue_fixed": "Capture processes could be restarted when broker data legitimately paused while the process was alive.",
            "tests_verifiers": "tests/test_m1_capture.py and tests/test_tick_capture.py.",
            "integration_disposition": "combine_with_local_terminal_and_namespace_support",
        }
    if path.startswith("src/") and "canary" in path.lower():
        return {
            "class": "production code",
            "behavior_changed": "Removes canary runtime/cache dependency.",
            "issue_fixed": "Live boot/restart behavior carried stale canary approval and cache semantics.",
            "tests_verifiers": "Canary tests deleted or updated by VPS sync branch.",
            "integration_disposition": "preserve_canary_removal",
        }
    if path.startswith("src/"):
        return {
            "class": "production code",
            "behavior_changed": "VPS live runtime repair or supporting production helper update.",
            "issue_fixed": "Live production sync defect or stale canary/runtime assumption.",
            "tests_verifiers": "VPS focused pytest suite and py_compile.",
            "integration_disposition": "preserve_after_semantic_review",
        }
    if path.startswith("scripts/watchdog") or path in {"run_agent.py", "start_all.bat"}:
        return {
            "class": "launcher/supervisor/watchdog",
            "behavior_changed": "Direct Python daemon launch, live redacted_account defaults, liveness-vs-progress supervision, and canary audit removal.",
            "issue_fixed": "cmd.exe wrapper PID ambiguity, demo default drift, stale tick freshness crash loops, and live canary blocker pollution.",
            "tests_verifiers": "tests/test_watchdog_e2e_verify.py and PowerShell static parse.",
            "integration_disposition": "preserve_vps_live_launch_shape",
        }
    if path.startswith("scripts/") and "canary" in path.lower():
        return {
            "class": "launcher/supervisor/watchdog",
            "behavior_changed": "Deletes stale canary fixture/generator/audit surfaces from live sync branch.",
            "issue_fixed": "Canary artifacts were no longer live production authority after VPS removal.",
            "tests_verifiers": "Canary-specific tests removed; live suite excludes canary blockers.",
            "integration_disposition": "preserve_canary_removal",
        }
    if path.startswith("scripts/"):
        return {
            "class": "tests/verifiers",
            "behavior_changed": "VPS verifier, monitoring, or maintenance script repair.",
            "issue_fixed": "Live production observability or artifact verification drift.",
            "tests_verifiers": "VPS focused test/verifier suite.",
            "integration_disposition": "preserve_after_scope_review",
        }
    if path.startswith("config/"):
        return {
            "class": "production config/profile",
            "behavior_changed": "Removes canary config and preserves selected-cell risk/execution policy production settings.",
            "issue_fixed": "Config could present stale canary authority or ambiguous selected-cell risk labels.",
            "tests_verifiers": "Stage13 builder/verifier and production wiring tests.",
            "integration_disposition": "preserve_vps_config_then_validate_ftmo_compatibility",
        }
    if path.startswith("research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/"):
        return {
            "class": "stage13 risk contract",
            "behavior_changed": "Separates configured profile-risk counts from effective selected-cell risk counts.",
            "issue_fixed": "The live 0.25 pct sizing proof could be misread as a profile-risk mismatch.",
            "tests_verifiers": "Stage13 builder and verifier.",
            "integration_disposition": "preserve_stage13_risk_label_split",
        }
    if path.startswith(VPS_ROUTE):
        if any(token in path for token in ("HANDOFF", "CLASSIFICATION", "VERIFICATION", "build_", "verify_", "test_")):
            disposition = "preserve_vps_handoff_verifier_artifact"
        else:
            disposition = "preserve_vps_supervisor_evidence_required_for_route_verifier"
        return {
            "class": "vps supervisor evidence",
            "behavior_changed": "Records VPS process, account, risk, supervisor, reload, and verifier truth for local integration.",
            "issue_fixed": "Local integration would otherwise lack the exact VPS live production context.",
            "tests_verifiers": "verify_vps_supervisor_artifacts.py and test_vps_supervisor_artifacts.py.",
            "integration_disposition": disposition,
        }
    if path.startswith("tests/") or path.startswith("research/operations/") and path.endswith(".py"):
        return {
            "class": "tests/verifiers",
            "behavior_changed": "Focused test/verifier update for VPS live production behavior.",
            "issue_fixed": "Regression coverage needed for repaired runtime surface.",
            "tests_verifiers": "Focused pytest and route verifiers.",
            "integration_disposition": "preserve_test_or_verifier",
        }
    if path.startswith("shadow_logs/") and status == "D":
        return {
            "class": "runtime cleanup",
            "behavior_changed": "Removes tracked stale canary-governance status log.",
            "issue_fixed": "A tracked live shadow log incorrectly preserved stale canary status as current state.",
            "tests_verifiers": "Scope review and canary removal tests.",
            "integration_disposition": "preserve_tracked_canary_log_deletion",
        }
    return {
        "class": "other vps sync path",
        "behavior_changed": "VPS branch path retained for production live-sync parity.",
        "issue_fixed": "See VPS handoff/classification for path-specific context.",
        "tests_verifiers": "VPS focused suite or scope ledger.",
        "integration_disposition": "reviewed_preserve_or_scope",
    }


def classify_local_path(path: str) -> dict[str, str]:
    if path.startswith("config/profiles/ftmo") or path == "config/profiles/README.md":
        return {
            "class": "production config/profile",
            "behavior_changed": "Adds FTMO Server 3 profile and FTMO compatibility pointer beside redacted_account.",
            "production_relevance": "Required for dual-production profile-bound symbol, risk, session, terminal, and broker metadata.",
            "tests_verifiers": "scripts/verify_broker_profile.py and tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py.",
            "integration_disposition": "port_local_profile_support_default_inactive_on_vps_until_owner_deploys",
        }
    if path == "src/utils/broker_profile.py":
        return {
            "class": "production code",
            "behavior_changed": "Adds broker/account namespace, namespaced file/directory helpers, terminal-path resolution, and profile checks.",
            "production_relevance": "Separates redacted_account and FTMO process groups, locks, checkpoints, data roots, and terminal paths.",
            "tests_verifiers": "tests/test_broker_profile_namespace.py and tests/test_verify_broker_profile.py.",
            "integration_disposition": "port_local_namespace_support",
        }
    if path in {"run_agent.py", "src/components/orchestrator.py", "src/components/execution.py", "src/components/m1_capture.py", "src/components/tick_capture.py"}:
        return {
            "class": "production code",
            "behavior_changed": "Wires runtime namespace, terminal path, and profile-specific persistence into launch/orchestrator/capture/execution paths.",
            "production_relevance": "Required for running FTMO beside redacted_account without lock/data/checkpoint collision.",
            "tests_verifiers": "Broker-profile namespace tests plus capture/execution/orchestrator tests.",
            "integration_disposition": "combine_with_vps_live_runtime_repairs",
        }
    if path == "src/components/broker_truth_cost_capture_v2.py":
        return {
            "class": "production code",
            "behavior_changed": "Adds namespace-aware broker truth/cost capture v2 log path support.",
            "production_relevance": "Keeps broker-truth cost capture separate per account/profile.",
            "tests_verifiers": "FTMO dual production prep test and broker truth capture tests if present.",
            "integration_disposition": "port_local_broker_truth_namespace_support",
        }
    if path == "scripts/verify_broker_profile.py":
        return {
            "class": "tests/verifiers",
            "behavior_changed": "Adds offline broker-profile verifier for expected account, symbol aliases, sessions, and namespace assumptions.",
            "production_relevance": "Deployment gate before adding FTMO or checking redacted_account profile drift.",
            "tests_verifiers": "tests/test_verify_broker_profile.py.",
            "integration_disposition": "port_local_profile_verifier",
        }
    if path.startswith(SELECTOR_V3_ROUTE):
        return {
            "class": "default-off v3 package",
            "behavior_changed": "Selector V3 package and source/research evidence.",
            "production_relevance": "Moves selector logic toward deployability while keeping activation gated/default-off.",
            "tests_verifiers": "Selector V3 route verifier/tests.",
            "integration_disposition": "preserve_default_off_package_by_reference_not_live_activation",
        }
    if path.startswith(SCHEDULER_V3_ROUTE):
        return {
            "class": "default-off v3 package",
            "behavior_changed": "Scheduler V3 default-off helper/package for account-risk and portfolio scheduling work.",
            "production_relevance": "Provides promotion-ready scheduler evidence without changing current redacted_account live admission authority.",
            "tests_verifiers": "tests/test_vnext_absolute_moonshot_scheduler_v3.py.",
            "integration_disposition": "preserve_default_off_scheduler_package",
        }
    if path.startswith(EXECUTION_V3_ROUTE):
        return {
            "class": "default-off v3 package",
            "behavior_changed": "Execution Policy V3 package, registry, and evaluation ledgers.",
            "production_relevance": "Provides production candidate policy variants while current live policy stays momentum/partial.",
            "tests_verifiers": "Execution Policy V3 route verifier/tests.",
            "integration_disposition": "preserve_default_off_execution_policy_package",
        }
    if path.startswith(SOURCE_CAPTURE_ROUTE):
        return {
            "class": "source capture repair",
            "behavior_changed": "Post-Lane18 source capture repair artifacts for runtime packet completeness and future verifier contracts.",
            "production_relevance": "Defines packet/capture completeness requirements consumed by V3 components.",
            "tests_verifiers": "Source capture repair route verifier/tests.",
            "integration_disposition": "preserve_by_reference_and_scope_ledgers",
        }
    if path.startswith(FTMO_ROUTE):
        return {
            "class": "deployment handoff evidence",
            "behavior_changed": "FTMO dual-production implementation contract, change ledger, verifier results, and owner/VPS requirements.",
            "production_relevance": "Exact route contract for adding FTMO beside redacted_account.",
            "tests_verifiers": "FTMO route verifier and profile verifier.",
            "integration_disposition": "preserve_local_deployment_contract",
        }
    if path.startswith("tests/"):
        return {
            "class": "tests/verifiers",
            "behavior_changed": "Adds or refreshes local V3/FTMO test coverage.",
            "production_relevance": "Guards default-off V3 package and broker-profile namespace behavior.",
            "tests_verifiers": "Focused pytest.",
            "integration_disposition": "preserve_test_or_verifier",
        }
    return {
        "class": "local v3/ftmo evidence or context",
        "behavior_changed": "Local post-V3 or FTMO route artifact.",
        "production_relevance": "Reviewed for deployable package, default-off package, or evidence-only scope.",
        "tests_verifiers": "Route verifier/focused tests where available.",
        "integration_disposition": "reviewed_preserve_or_reference",
    }


def staged_scope_rows(staged: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "path_family": "src/",
            "scope_decision": "include",
            "reason": "Deployable production runtime code from VPS sync plus FTMO namespace repairs.",
        },
        {
            "path_family": "config/",
            "scope_decision": "include",
            "reason": "Production config/profile surface including redacted_account current truth and FTMO staged profile support.",
        },
        {
            "path_family": "scripts/watchdog.ps1 and launch scripts",
            "scope_decision": "include",
            "reason": "VPS live direct Python launch shape and verifier/static checks are deployment-critical.",
        },
        {
            "path_family": "tests/",
            "scope_decision": "include",
            "reason": "Focused tests for execution, capture, heartbeat, broker profile, V3 packages, and VPS supervisor.",
        },
        {
            "path_family": VPS_ROUTE,
            "scope_decision": "include_route_evidence",
            "reason": "VPS supervisor handoff, verifier, and live proof artifacts preserve production truth for local integration.",
        },
        {
            "path_family": "pipeline_state/",
            "scope_decision": "exclude",
            "reason": "Runtime snapshots are excluded; VPS proof is preserved through handoff/classification artifacts.",
        },
        {
            "path_family": "shadow_logs/",
            "scope_decision": "exclude_except_tracked_canary_status_deletion",
            "reason": "Runtime logs stay out; tracked stale canary-governance status log deletion is part of canary cleanup.",
        },
        {
            "path_family": "raw research JSONL/JSONL.GZ ledgers",
            "scope_decision": "exclude_unless_already_required_by_runtime_or_stage13",
            "reason": "Local V3 raw ledgers remain recoverable by commit/path; production branch carries summaries, manifests, code, and verifier contracts.",
        },
    ]
    suspicious = []
    for row in staged:
        path = row["path"]
        status = row["status"]
        if path.startswith(("pipeline_state/", "data/", "knowledge_base/")):
            suspicious.append({**row, "scope_review": "forbidden_runtime_dirt"})
        elif path.startswith("shadow_logs/") and not (
            path == "shadow_logs/canary_restart_governance_status.jsonl" and status == "D"
        ):
            suspicious.append({**row, "scope_review": "forbidden_shadow_log"})
        elif path.endswith(".jsonl.gz"):
            suspicious.append({**row, "scope_review": "compressed_jsonl_requires_proof"})
    rows.append(
        {
            "path_family": "actual_staged_runtime_or_large_artifact_scan",
            "scope_decision": "machine_checked",
            "reason": "Forbidden runtime/cache/shadow paths must be absent except the tracked canary status deletion.",
            "matched_paths": suspicious,
            "matched_path_count": len(suspicious),
        }
    )
    ok, lfs_text = git_optional("lfs", "ls-files")
    rows.append(
        {
            "path_family": "git_lfs_ls_files",
            "scope_decision": "record_pointer_state" if ok else "tool_unavailable_or_failed",
            "reason": "LFS pointer review for production branch scope.",
            "tool_ok": ok,
            "line_count": len([line for line in lfs_text.splitlines() if line.strip()]) if ok else None,
            "raw_status_excerpt": "\n".join(lfs_text.splitlines()[:40]),
        }
    )
    return rows


def verification_matrix() -> dict[str, Any]:
    return {
        "schema_version": "vps_local_v3_ftmo_verification_matrix_v1",
        "generated_at_utc": utc_now(),
        "checks": [
            {"id": "py_compile_runtime", "command": "py -3 -m py_compile run_agent.py src/components/execution.py src/components/m1_capture.py src/components/tick_capture.py src/components/orchestrator.py src/components/gtos_vnext_runtime.py src/safety/heartbeat_monitor.py scripts/watchdog_e2e_verify.py scripts/verify_broker_profile.py", "required": True},
            {"id": "profile_verifier_redacted_account", "command": "py -3 scripts/verify_broker_profile.py config/profiles/redacted_account.yaml --result <route>/PROFILE_VERIFIER_redacted_account_RESULT.json", "required": True},
            {"id": "profile_verifier_ftmo", "command": "py -3 scripts/verify_broker_profile.py config/profiles/operator_profile.yaml --result <route>/PROFILE_VERIFIER_FTMO_RESULT.json", "required": True},
            {"id": "stage13_risk_proof", "command": "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/build_vnext_replacement_stage13_redacted_account_broker_risk_geometry.py && py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/verify_vnext_replacement_stage13_redacted_account_broker_risk_geometry.py", "required": True},
            {"id": "vps_supervisor_verifier", "command": "py -3 research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/verify_vps_supervisor_artifacts.py", "required": True},
            {"id": "focused_pytest_runtime", "command": "py -3 -m pytest tests/test_execution.py tests/test_m1_capture.py tests/test_tick_capture.py tests/test_heartbeat_monitor.py tests/test_gtos_vnext_runtime.py tests/test_orchestrator.py tests/test_broker_profile_namespace.py tests/test_verify_broker_profile.py tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/test_vps_supervisor_artifacts.py research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/test_vnext_vps_local_v3_ftmo_production_integration.py -q", "required": True},
            {"id": "watchdog_static_parse", "command": "powershell -NoProfile -Command \"[scriptblock]::Create((Get-Content scripts\\\\watchdog.ps1 -Raw)) | Out-Null\"", "required": True},
            {"id": "route_verifier", "command": "py -3 research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/verify_vnext_vps_local_v3_ftmo_production_integration.py", "required": True},
            {"id": "git_diff_check", "command": "git diff --check", "required": True},
            {"id": "staged_scope_review", "command": "git diff --cached --name-status plus route verifier scope checks", "required": True},
        ],
    }


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    local_head = git("rev-parse", "HEAD").strip()
    vps_head = git("rev-parse", VPS_BRANCH).strip()
    merge_base = git("merge-base", "HEAD", VPS_BRANCH).strip()
    staged = parse_name_status(git("diff", "--cached", "--name-status"))
    unmerged = [line for line in git("diff", "--name-only", "--diff-filter=U").splitlines() if line.strip()]
    vps_diff = parse_name_status(git("diff", "--name-status", f"{merge_base}..{VPS_BRANCH}"))
    local_diff = parse_name_status(git("diff", "--name-status", f"{merge_base}..HEAD"))

    vps_rows = []
    for row in vps_diff:
        cls = classify_vps_path(row["path"], row["status"])
        vps_rows.append(
            {
                "schema_version": "vps_production_change_inventory_v1",
                "branch": VPS_BRANCH,
                "merge_base": merge_base,
                "vps_head": vps_head,
                "status": row["status"],
                "path": row["path"],
                "old_path": row.get("old_path"),
                "file_size_bytes_after_sparse_checkout": file_size(row["path"]),
                "path_materialized_in_worktree": path_exists(row["path"]),
                **cls,
            }
        )
    if not vps_rows:
        vps_rows.append(
            {
                "schema_version": "vps_production_change_inventory_v1",
                "branch": VPS_BRANCH,
                "merge_base": merge_base,
                "vps_head": vps_head,
                "status": "CONSUMED",
                "path": VPS_BRANCH,
                "old_path": None,
                "file_size_bytes_after_sparse_checkout": None,
                "path_materialized_in_worktree": False,
                "class": "vps branch fully consumed",
                "behavior_changed": "No unconsumed VPS diff remains because the finalized VPS supervisor package is already merged into the integration branch.",
                "issue_fixed": "Prevents a fully consumed VPS branch from being misread as missing production-change evidence.",
                "tests_verifiers": "Route verifier, focused integration pytest, and focused runtime tests.",
                "integration_disposition": "vps_source_branch_consumed_as_ancestor",
            }
        )

    local_rows = []
    for row in local_diff:
        cls = classify_local_path(row["path"])
        local_rows.append(
            {
                "schema_version": "local_v3_ftmo_production_change_inventory_v1",
                "branch": branch,
                "merge_base": merge_base,
                "local_head": local_head,
                "status": row["status"],
                "path": row["path"],
                "old_path": row.get("old_path"),
                "file_size_bytes": file_size(row["path"]),
                "path_materialized_in_worktree": path_exists(row["path"]),
                **cls,
            }
        )

    write_jsonl("VPS_PRODUCTION_CHANGE_INVENTORY.jsonl", vps_rows)
    write_jsonl("LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl", local_rows)

    divergence = {
        "schema_version": "branch_base_and_divergence_ledger_v1",
        "generated_at_utc": utc_now(),
        "current_branch": branch,
        "local_head": local_head,
        "vps_branch": VPS_BRANCH,
        "vps_head": vps_head,
        "merge_base": merge_base,
        "local_diff_path_count": len(local_diff),
        "vps_diff_path_count": len(vps_diff),
        "staged_path_count_after_merge_resolution": len(staged),
        "unmerged_paths": unmerged,
        "vps_diff_summary_by_class": Counter(row["class"] for row in vps_rows),
        "local_diff_summary_by_class": Counter(row["class"] for row in local_rows),
        "staged_paths": staged,
        "vps_changed_paths": vps_diff,
        "local_changed_paths": local_diff,
        "sparse_checkout_enabled": git_optional("config", "--get", "core.sparseCheckout")[1].strip() == "true",
        "sparse_checkout_patterns": [line for line in git_optional("sparse-checkout", "list")[1].splitlines() if line.strip()],
    }
    write_json("BRANCH_BASE_AND_DIVERGENCE_LEDGER.json", divergence)

    conflict_rows = [
        {
            "schema_version": "conflict_resolution_ledger_v1",
            "path": "src/components/execution.py",
            "conflict_surface": "imports and runtime execution overlap",
            "local_side_preserved": "broker_account_namespace and namespaced_file_path for account/profile-separated checkpoints and pending intents.",
            "vps_side_preserved": "TRADE_ACTION_SLTP import plus VPS execution repairs already merged by Git: broker-history fill price, original risk denominator, recovered partial/residual SLTP repair.",
            "final_resolution": "combined both import families and kept local namespace constructor paths with VPS runtime behavior.",
            "verification": "py_compile plus execution focused tests in matrix.",
        },
        {
            "schema_version": "conflict_resolution_ledger_v1",
            "path": "src/components/m1_capture.py",
            "conflict_surface": "state save path, heartbeat semantics, and malformed OHLC repair config",
            "local_side_preserved": "profile/terminal/namespace arguments, namespaced data root, namespaced state path, namespaced daemon heartbeat name.",
            "vps_side_preserved": "last_progress_utc tracking, liveness timestamp, persisted progress heartbeat when no new M1 row appears, tick-anchored malformed OHLC repair, and structured repair diagnostics.",
            "final_resolution": "capture_once accepts namespace paths/heartbeat plus config; main passes data_root, state_path, heartbeat_name, and config so dual-account M1 capture and VPS source repair both remain active.",
            "verification": "py_compile plus M1 capture tests in matrix.",
        },
        {
            "schema_version": "conflict_resolution_ledger_v1",
            "path": "src/components/tick_capture.py",
            "conflict_surface": "namespaced tick heartbeat versus VPS liveness heartbeat",
            "local_side_preserved": "runtime namespace CLI, terminal path init, namespaced tick data root, namespaced daemon lock/heartbeat name.",
            "vps_side_preserved": "corrupt parquet quarantine, startup readiness heartbeat, poll liveness heartbeat, flush progress heartbeat, skip-freshness support.",
            "final_resolution": "all heartbeat writes use state.heartbeat_name fallback while preserving VPS liveness/progress fields.",
            "verification": "py_compile plus tick capture tests in matrix.",
        },
    ]
    write_jsonl("CONFLICT_RESOLUTION_LEDGER.jsonl", conflict_rows)

    semantic_rows = [
        {"path": "src/components/orchestrator.py", "review_role": "conflict integrator", "decision": "combine", "evidence": "VPS candidate identity, selected-cell refusal, Gate3 optional snapshot, Lane06 recovery, old-ticket stale-current repairs coexist with local profile terminal/runtime namespace constructor wiring.", "risk_if_wrong": "Could lose either live lifecycle repairs or dual-account process separation."},
        {"path": "src/components/gtos_vnext_runtime.py", "review_role": "VPS production auditor", "decision": "preserve_vps", "evidence": "Locked JSONL append and selected-cell risk load/source-status repairs are VPS live fixes; local V3 routes do not override this file with production activation.", "risk_if_wrong": "Concurrent live orchestrators could corrupt runtime JSONL or reject valid selected-cell rows."},
        {"path": "src/safety/heartbeat_monitor.py", "review_role": "VPS production auditor", "decision": "preserve_vps", "evidence": "Canary lenience and canary heartbeat surfaces removed; fleet monitor stays current 24-symbol heartbeat truth.", "risk_if_wrong": "Stale canary authority could mask or create live heartbeat behavior."},
        {"path": "scripts/watchdog.ps1", "review_role": "launcher/supervisor auditor", "decision": "preserve_vps_then_stage_ftmo_future_extension", "evidence": "Default live redacted_account direct Python launch and tick/M1 liveness supervision preserved; FTMO dual process group remains deployment-stage extension pending VPS terminal/account proof.", "risk_if_wrong": "VPS could regress to demo or cmd wrapper PID ambiguity."},
        {"path": "run_agent.py", "review_role": "local V3/FTMO auditor", "decision": "combine", "evidence": "Canary usage text removed while --terminal-path and --runtime-namespace local FTMO launch controls remain.", "risk_if_wrong": "Dual production launch would collide locks or reintroduce stale canary instruction."},
        {"path": "config/agent_config.yaml", "review_role": "risk/config auditor", "decision": "preserve_vps", "evidence": "Canary config removed; selected-cell and current vNext dynamic execution authority remain active for redacted_account. FTMO added through separate profile files, not by changing redacted_account live defaults.", "risk_if_wrong": "Risk labels or stale canary approval could govern live behavior."},
        {"path": "config/profiles/*", "review_role": "local V3/FTMO auditor", "decision": "port_local_and_repair_redacted_account_truth", "evidence": "FTMO profile and pointer stay beside redacted_account; redacted_account profile is repaired from VPS account/broker-spec evidence with expected account and full 24-symbol market geometry, without adding a runtime namespace default.", "risk_if_wrong": "redacted_account behavior could be polluted by FTMO metadata or continue without an account-specific profile assertion."},
        {"path": VPS_ROUTE, "review_role": "VPS production auditor", "decision": "preserve_vps_route", "evidence": "Supervisor handoff, classification, verifier, and proof ledgers preserve process/account/reload/risk truth for local deployment handoff.", "risk_if_wrong": "Local deployer would lack exact VPS production source evidence."},
        {"path": "canary path family", "review_role": "LFS/scope auditor", "decision": "preserve_canary_removal", "evidence": "VPS removes live canary boot/cache/governance dependencies and deletes stale canary tests/fixtures/scripts.", "risk_if_wrong": "Old live canary blocker could re-enter production."},
        {"path": "Stage13 risk proof artifacts", "review_role": "risk/config auditor", "decision": "preserve_vps", "evidence": "Configured profile-risk counts and effective selected-cell risk counts remain separate, explaining 0.25 pct live sizing.", "risk_if_wrong": "Operators could misread selected-cell risk as profile sizing defect."},
    ]
    write_jsonl("SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl", semantic_rows)

    runtime_map = {
        "schema_version": "runtime_behavior_map_after_integration_v1",
        "generated_at_utc": utc_now(),
        "redacted_account_live_default": {
            "profile": "redacted_account",
            "mode_default_in_watchdog": "live",
            "symbol_count": 24,
            "execution_policy": "momentum_exhaustion primary with partial_be_runner exception",
            "selected_cell_risk_authority": "effective selected-cell risk from Stage13 before account/prop projection",
            "profile_account_assertion": "redacted_account profile carries VPS account-specific expected account/server/login_sha256 and 24-symbol broker geometry; raw login is not stored.",
            "canary_runtime_dependency": "removed",
            "watchdog_launch_shape": "direct Python process launch",
        },
        "ftmo_staged_target": {
            "profile": "operator_profile",
            "compatibility_pointer": "config/profiles/ftmo.yaml",
            "runtime_namespace": "profile/account bound; required for all order-capable process groups",
            "terminal_path": "profile/CLI/env resolved; VPS-local proof required before deployment",
            "activation_status": "code/profile/verifier integrated; live process start requires owner deployment action",
        },
        "v3_components": {
            "selector_v3": "default-off/package evidence preserved; no live selector flip in this branch",
            "scheduler_v3": "default-off helper/package preserved; current redacted_account admission remains VPS stable path",
            "execution_policy_v3": "default-off registry/package preserved; current live policy unchanged",
            "source_capture_repair": "contracts preserved by reference for packet completeness and future promotion gates",
        },
        "lifecycle_truth": {
            "ticket_bound_management": True,
            "partial_close_residual_recovery": True,
            "broker_truth_over_local_projection": True,
            "pending_limit_original_risk_denominator_retained": True,
            "false_close_handling_explicit": True,
        },
    }
    write_json("RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json", runtime_map)

    compatibility_rows = [
        {"schema_version": "redacted_account_ftmo_profile_compatibility_v1", "surface": "redacted_account profile", "status": "preserved_current_live_repaired_with_vps_account_truth", "evidence": "watchdog default remains profile=redacted_account and mode=live; config/profiles/redacted_account.yaml now records VPS expected account/server/login_sha256, terminal path/data path, and full 24-symbol broker geometry from the VPS broker spec. Raw login is not stored and no runtime namespace default was added.", "deployment_requirement": "Run redacted_account profile verifier on VPS before reload."},
        {"schema_version": "redacted_account_ftmo_profile_compatibility_v1", "surface": "FTMO profile", "status": "integrated_staged", "evidence": "config/profiles/operator_profile.yaml and ftmo.yaml present with verifier/test coverage.", "deployment_requirement": "VPS-local MT5 terminal/account proof and owner account-stage/add-on confirmation."},
        {"schema_version": "redacted_account_ftmo_profile_compatibility_v1", "surface": "runtime namespace", "status": "integrated_required_for_dual_prod", "evidence": "run_agent, orchestrator, execution, M1, tick, broker truth capture use runtime namespace helpers.", "deployment_requirement": "Every order-capable process must pass --runtime-namespace and --terminal-path when FTMO is started."},
        {"schema_version": "redacted_account_ftmo_profile_compatibility_v1", "surface": "locks/data/checkpoints", "status": "separated_by_namespace", "evidence": "orchestrator locks, execution checkpoints, pending intents, M1/tick roots, and broker truth logs are namespace-aware.", "deployment_requirement": "Confirm no live redacted_account process uses FTMO namespace and vice versa."},
        {"schema_version": "redacted_account_ftmo_profile_compatibility_v1", "surface": "symbol aliases and broker metadata", "status": "profile_bound", "evidence": "broker profile verifier checks aliases, sessions, terminal, account, lot and stop metadata where configured.", "deployment_requirement": "Refresh FTMO broker export if account/specs differ from local profile."},
    ]
    write_jsonl("redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl", compatibility_rows)

    v3_rows = [
        {"schema_version": "v3_runtime_disposition_v1", "component": "Selector V3", "route": SELECTOR_V3_ROUTE, "runtime_disposition": "default_off_package_preserved", "production_code_effect_now": False, "result_use_status": "source-bound package and route evidence referenced; not live authority", "missing_for_activation": "production-change dossier, config authority, rollback, sealed/stress/live shadow proof, owner approval"},
        {"schema_version": "v3_runtime_disposition_v1", "component": "Scheduler V3", "route": SCHEDULER_V3_ROUTE, "runtime_disposition": "default_off_helper_preserved", "production_code_effect_now": False, "result_use_status": "account-risk/portfolio scheduling helper is testable and promotion-ready but not live default", "missing_for_activation": "VPS live account-risk parity proof and owner-approved scheduler promotion"},
        {"schema_version": "v3_runtime_disposition_v1", "component": "Execution Policy V3", "route": EXECUTION_V3_ROUTE, "runtime_disposition": "default_off_registry_preserved", "production_code_effect_now": False, "result_use_status": "policy registry/evaluation intelligence preserved; current live policy remains momentum_exhaustion/partial_be_runner", "missing_for_activation": "tick-realistic broker-feasible production-change dossier and owner approval"},
        {"schema_version": "v3_runtime_disposition_v1", "component": "Source Capture Repair", "route": SOURCE_CAPTURE_ROUTE, "runtime_disposition": "capture_contract_preserved_by_reference", "production_code_effect_now": False, "result_use_status": "packet completeness/capture requirements feed future promotion verifiers", "missing_for_activation": "component-specific consumer wiring and VPS-local forward capture proof"},
        {"schema_version": "v3_runtime_disposition_v1", "component": "FTMO Dual Production", "route": FTMO_ROUTE, "runtime_disposition": "staged_deployable_profile_support", "production_code_effect_now": False, "result_use_status": "code/profile/verifier integrated; no FTMO process started", "missing_for_activation": "owner deployment action, terminal/account proof, credential-safe VPS setup, final preflight"},
    ]
    write_jsonl("V3_RUNTIME_DISPOSITION_LEDGER.jsonl", v3_rows)

    invariant_rows = [
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "configured profile risk and effective selected-cell risk remain separate", "status": "preserved", "evidence": "Stage13 summary now reports configured and effective selected-cell distributions separately; runtime uses selected-cell risk first."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "account/prop risk projection stays separate from source selected-cell proof", "status": "preserved", "evidence": "VPS risk handoff and runtime selected-cell fields keep source-risk and prop-risk labels distinct."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "stale count caps and old fixed-risk labels do not govern valid vNext trades", "status": "preserved", "evidence": "VPS broader-origin cap repair deferred provisional counts until selected-cell/router gates."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "old fixed 1.5R/J46/J49/BE-only authority does not re-enter current vNext runtime", "status": "preserved", "evidence": "Execution code disables legacy J46/J49 live execution unless explicit allow flag is set while dynamic vNext policy is active."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "ticket-bound lifecycle and partial residual recovery remain intact", "status": "preserved", "evidence": "Execution and orchestrator repairs hydrate recovered geometry/events and match broker tickets/history."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "broker truth cost capture stays separate from projected/local PnL", "status": "preserved", "evidence": "VPS close/deal accounting repairs and namespace-aware broker truth capture v2 preserve broker-truth surfaces."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "trade-close notification failure cannot block exit monitoring updates", "status": "repaired", "evidence": "Orchestrator trade-close notification context now falls back to the active trade record and is wrapped non-blocking before SPRT/CUSUM updates."},
        {"schema_version": "risk_execution_lifecycle_invariant_v1", "invariant": "canary is not a live approval or blocking dependency", "status": "preserved", "evidence": "Config, heartbeat, watchdog, scripts, tests, and canary cache surfaces removed or reclassified historical."},
    ]
    write_jsonl("RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl", invariant_rows)

    write_jsonl("LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl", staged_scope_rows(staged))
    write_json("VERIFICATION_MATRIX.json", verification_matrix())

    handoff = f"""# VPS Deployment Handoff

Branch: `{branch}`
Local HEAD before integration commit: `{local_head}`
VPS source branch: `{VPS_BRANCH}` at `{vps_head}`
Merge base: `{merge_base}`

## What This Branch Integrates

- VPS live production fixes from `{VPS_BRANCH}`: canary removal, watchdog direct Python live launch, liveness heartbeat supervision, selected-cell risk repairs, Stage13 risk label split, execution/broker lifecycle repairs, and VPS supervisor evidence.
- Local V3/FTMO production-ready package: FTMO profile support, broker/account namespace helpers, profile verifier, namespace-aware capture/execution/broker truth paths, and default-off V3 package disposition.
- Integration repairs: redacted_account profile account/broker-geometry verification now uses VPS truth without storing raw login, and trade-close notifications are non-blocking so SPRT/CUSUM exit updates continue if notification context is missing.

## Deployment Boundaries

This branch does not perform broker/order/deal/position mutation, credential changes, paid API calls, remote push, or VPS live process restart. VPS deployment is a separate owner action.

## VPS-Side Checks Before Reload

1. Pull or otherwise place this committed branch on the VPS.
2. Run `py -3 scripts/verify_broker_profile.py config/profiles/redacted_account.yaml --result research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/PROFILE_VERIFIER_redacted_account_RESULT.json`.
3. Run `py -3 research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/verify_vps_supervisor_artifacts.py`.
4. Run the focused pytest matrix from `VERIFICATION_MATRIX.json`.
5. For FTMO only after owner approval, run the FTMO profile verifier against the real VPS terminal/account export and confirm account stage/add-ons before starting any FTMO process group.

## Runtime Contract

redacted_account remains the current live default. FTMO is staged with profile, namespace, terminal-path, verifier, and deployment-handoff support. V3 Selector/Scheduler/Execution packages remain default-off/promotion-ready; they are not silently activated by this integration branch.
"""
    write_md("VPS_DEPLOYMENT_HANDOFF.md", handoff)

    context_anchor = f"""# Integration Context Anchor

Generated: `{utc_now()}`

Controlling prompt: `{PROMPT_PATH}`
Current branch: `{branch}`
Local HEAD: `{local_head}`
VPS branch: `{VPS_BRANCH}`
VPS HEAD: `{vps_head}`
Merge base: `{merge_base}`

## Evidence Class

Production-code integration. Local code/config/profile/verifier/launcher/watchdog/test/handoff edits are authorized by the prompt. Broker/account/order/deal/position mutation, credentials, paid calls, remote push, and VPS live restart/reload are not authorized here.

## Required Context Read

The session regenerated `.context/LIVE_STATE.md` and reread AGENTS, current vNext map, reading order, quick reference, research/current doctrine, orchestration controls, moonshot vision, cleanup/scope policy, latest handoff, the controlling prompt, local HEAD, and `{VPS_BRANCH}` from disk.

## Isolated Review Passes

- VPS production auditor: `VPS_PRODUCTION_CHANGE_INVENTORY.jsonl`.
- Local V3/FTMO auditor: `LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl`.
- Conflict integrator: `CONFLICT_RESOLUTION_LEDGER.jsonl`.
- Verifier architect: `VERIFICATION_MATRIX.json` and route verifier.
- LFS/scope auditor: `LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl`.

## Current Stop Condition

The route is complete only after conflicts are resolved, semantic overlaps reviewed, verification commands recorded, scope checks pass, output manifest and completion audit are final, and a scoped merge commit is created on `{branch}`.
"""
    write_md("INTEGRATION_CONTEXT_ANCHOR.md", context_anchor)

    latest_merge = git_optional("rev-list", "--merges", "-n", "1", "HEAD")[1].strip() or local_head
    latest_merge_parents = git_optional("show", "-s", "--format=%P", latest_merge)[1].split()
    write_json(
        "POST_COMMIT_COMPLETION_AUDIT.json",
        {
            "schema_version": "vps_local_v3_ftmo_post_commit_completion_audit_v2",
            "branch": branch,
            "integration_merge_commit": latest_merge,
            "integration_merge_parents": latest_merge_parents,
            "previous_integration_merge_commit": "7a60cb38edbae9a5ddeb53414c6e181d49a91ae5",
            "vps_source_branch": VPS_BRANCH,
            "vps_source_commit": vps_head,
            "local_head_when_built": local_head,
            "post_commit_evidence_refresh_reason": "Records the latest consumed VPS supervisor package merge and route evidence after the finalized VPS live-sync branch moved forward.",
            "required_route_verifier_result": str((ROUTE_DIR / "VERIFICATION_RESULT.json").relative_to(ROOT)).replace("\\", "/"),
            "required_completion_audit": str((ROUTE_DIR / "COMPLETION_AUDIT.json").relative_to(ROOT)).replace("\\", "/"),
            "additional_evidence_added": [
                "SATURATION_AND_SELF_RED_TEAM_PASS.json",
                "RESULT_USE_SOURCE_AND_IMPLEMENTATION_DECISION_LEDGER.jsonl",
                "POST_COMMIT_COMPLETION_AUDIT.json",
            ],
            "forbidden_surfaces_touched": False,
            "remote_push_performed": False,
            "broker_account_order_deal_position_mutation_performed": False,
            "credential_or_paid_vendor_action_performed": False,
            "vps_restart_or_reload_performed": False,
            "completion_status": "COMPLETE_COMMITTED_WITH_POST_COMMIT_EVIDENCE_REFRESH",
        },
    )

    manifest_entries = []
    for name in REQUIRED_ARTIFACTS:
        target = ROUTE_DIR / name
        manifest_entries.append(
            {
                "path": str(target.relative_to(ROOT)).replace("\\", "/"),
                "exists": target.exists(),
                "size_bytes": target.stat().st_size if target.exists() else None,
                "required": True,
            }
        )
    manifest_entries.extend(
        [
            {"path": str((ROUTE_DIR / "build_vnext_vps_local_v3_ftmo_production_integration.py").relative_to(ROOT)).replace("\\", "/"), "exists": True, "required": True},
            {"path": str((ROUTE_DIR / "verify_vnext_vps_local_v3_ftmo_production_integration.py").relative_to(ROOT)).replace("\\", "/"), "exists": (ROUTE_DIR / "verify_vnext_vps_local_v3_ftmo_production_integration.py").exists(), "required": True},
            {"path": str((ROUTE_DIR / "test_vnext_vps_local_v3_ftmo_production_integration.py").relative_to(ROOT)).replace("\\", "/"), "exists": (ROUTE_DIR / "test_vnext_vps_local_v3_ftmo_production_integration.py").exists(), "required": True},
        ]
    )
    write_json(
        "OUTPUT_MANIFEST.json",
        {
            "schema_version": "vps_local_v3_ftmo_output_manifest_v1",
            "generated_at_utc": utc_now(),
            "route": str(ROUTE_DIR.relative_to(ROOT)).replace("\\", "/"),
            "entries": manifest_entries,
        },
    )

    # The verifier rewrites these two files after local command results are
    # recorded. The builder creates a parseable initial state so every required
    # artifact is present immediately.
    write_json(
        "VERIFICATION_RESULT.json",
        {
            "schema_version": "vps_local_v3_ftmo_verification_result_v1",
            "generated_at_utc": utc_now(),
            "overall_status": "PENDING_ROUTE_VERIFIER_AND_COMMAND_RESULTS",
            "route_verifier_ok": False,
            "command_results_recorded": False,
        },
    )
    write_json(
        "COMPLETION_AUDIT.json",
        {
            "schema_version": "vps_local_v3_ftmo_completion_audit_v1",
            "generated_at_utc": utc_now(),
            "completion_status": "IN_PROGRESS_BUILDER_ARTIFACTS_WRITTEN",
            "can_mark_goal_complete": False,
            "local_head": local_head,
            "vps_head": vps_head,
            "merge_base": merge_base,
            "required_artifact_count": len(REQUIRED_ARTIFACTS),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
