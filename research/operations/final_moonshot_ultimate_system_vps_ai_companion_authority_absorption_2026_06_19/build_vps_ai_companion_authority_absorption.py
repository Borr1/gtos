#!/usr/bin/env python3
"""Build local absorption artifacts for the latest VPS AI companion authority commits."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
BASE_HEAD = "435d7d083611d11d986a02ee3bc688e952eb360a"
VPS_REMOTE_REF = "refs/heads/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
VPS_TRACKING_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
REQUIRED_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"
AUTHORITY_ROUTE = "research/operations/vps_runtime_ai_companion_authority_deployment_2026_06_19"
MICRO_ROUTE = "research/operations/vps_runtime_ai_companion_micro_observation_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def split_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def git_text_at(ref: str, path: str) -> str:
    return run(["git", "show", f"{ref}:{path}"]).stdout


def git_json_at(ref: str, path: str) -> Any:
    return json.loads(git_text_at(ref, path))


def git_path_exists(ref: str, path: str) -> bool:
    return run(["git", "cat-file", "-e", f"{ref}:{path}"], check=False).returncode == 0


def classify_path(path: str) -> str:
    if path.startswith("src/components/ai_companion/") or path == "scripts/run_ai_companion_supervisor.py":
        return "new_ai_companion_runtime_code"
    if path.startswith("src/components/ultimate_book/"):
        return "ultimate_book_runtime_integration"
    if path in {
        "src/components/execution.py",
        "src/components/execution_manager_v4.py",
        "src/components/broker_order_lifecycle_capture_v4.py",
        "src/components/slippage_shadow_logger.py",
    }:
        return "execution_lifecycle_runtime_code"
    if path in {
        "src/components/data_ingestion.py",
        "src/components/mt5_daemon_runtime.py",
        "src/components/tick_capture.py",
        "src/mt5/mt5_interface.py",
        "src/mt5/mt5_real.py",
        "src/utils/broker_profile.py",
    }:
        return "broker_profile_or_market_data_runtime"
    if path.startswith("scripts/") or path in {
        ".tools/monitor_books.py",
        "run_book.py",
        "src/notifications.py",
        "src/research_infra/account_pnl_truth_reconciler.py",
        "src/safety/heartbeat_monitor.py",
    }:
        return "runtime_supervision_or_reconciliation"
    if path.startswith("research/operations/vps_runtime_shadow_intelligence_only_handoff_"):
        return "shadow_intelligence_boundary_artifact"
    if path.startswith("config/"):
        return "runtime_config"
    if path.startswith("tests/"):
        return "focused_tests"
    if path.startswith(AUTHORITY_ROUTE):
        return "vps_authority_deployment_artifact"
    if path.startswith(MICRO_ROUTE):
        return "vps_micro_observation_artifact"
    if path.startswith(".context/"):
        return "vps_context_refresh"
    return "other"


def main() -> int:
    now = utc_now()
    remote_probe = run(["git", "ls-remote", "origin", VPS_REMOTE_REF]).stdout.strip().split()[0]
    local_origin_head_before_fetch = run(["git", "rev-parse", VPS_TRACKING_REF]).stdout.strip()
    if local_origin_head_before_fetch == remote_probe:
        fetch_attempt = subprocess.CompletedProcess([], 0, "", "")
        fetch_status = "not_required_current"
    else:
        fetch_attempt = run(
            [
                "git",
                "-c",
                "gc.auto=0",
                "fetch",
                "origin",
                f"{VPS_REMOTE_REF}:refs/remotes/{VPS_TRACKING_REF}",
            ],
            ROOT,
            check=False,
        )
        fetch_status = "passed" if fetch_attempt.returncode == 0 else "failed"
    local_origin_head_after_fetch = run(["git", "rev-parse", VPS_TRACKING_REF]).stdout.strip()
    local_floor_ok = run(
        ["git", "merge-base", "--is-ancestor", REQUIRED_FLOOR, local_origin_head_after_fetch],
        ROOT,
        check=False,
    ).returncode == 0
    source_snapshot_head = local_origin_head_after_fetch
    source_snapshot_verified = source_snapshot_head == remote_probe and local_floor_ok
    if not source_snapshot_verified:
        raise RuntimeError(
            "current VPS snapshot unavailable: "
            f"remote={remote_probe} local={source_snapshot_head} floor_ok={local_floor_ok}"
        )

    commit_rows: list[dict[str, Any]] = []
    log_lines = split_lines(
        run(
            ["git", "log", "--reverse", "--format=%H%x09%s", f"{BASE_HEAD}..{source_snapshot_head}"],
            ROOT,
        ).stdout
    )
    for line in log_lines:
        commit, subject = line.split("\t", 1)
        commit_rows.append(
            {
                "commit": commit,
                "short": commit[:9],
                "subject": subject,
                "source": f"git_snapshot:{source_snapshot_head}",
                "relative_to_local_origin_head": BASE_HEAD,
            }
        )

    changed_paths = split_lines(
        run(["git", "diff", "--name-only", f"{BASE_HEAD}..{source_snapshot_head}"], ROOT).stdout
    )
    code_rows = [
        {
            "path": path,
            "classification": classify_path(path),
            "package_relevance": classify_path(path)
            in {
                "new_ai_companion_runtime_code",
                "ultimate_book_runtime_integration",
                "execution_lifecycle_runtime_code",
                "broker_profile_or_market_data_runtime",
                "runtime_supervision_or_reconciliation",
                "shadow_intelligence_boundary_artifact",
                "runtime_config",
                "focused_tests",
                "vps_authority_deployment_artifact",
                "vps_micro_observation_artifact",
            },
        }
        for path in changed_paths
    ]
    path_classification_counts = Counter(row["classification"] for row in code_rows)
    package_relevant_changed_path_rows = sum(bool(row["package_relevance"]) for row in code_rows)

    authority_verification = git_json_at(source_snapshot_head, f"{AUTHORITY_ROUTE}/VERIFICATION_RESULT.json")
    authority_completion = git_json_at(source_snapshot_head, f"{AUTHORITY_ROUTE}/COMPLETION_AUDIT.json")
    authority_decision = git_json_at(source_snapshot_head, f"{AUTHORITY_ROUTE}/DECISION_LEDGER.json")
    micro_verification = git_json_at(source_snapshot_head, f"{MICRO_ROUTE}/VERIFICATION_RESULT.json")
    micro_synthesis = git_json_at(source_snapshot_head, f"{MICRO_ROUTE}/MICRO_OBSERVATION_SYNTHESIS.json")

    boundary = authority_verification.get("runtime_effect_boundary")
    boundary_rows = [
        {"control": value, "status": "allowed_reduce_or_protect_only", "source": "authority_completion"}
        for value in authority_completion.get("allowed_controls", [])
    ]
    boundary_rows.extend(
        {"control": value, "status": "forbidden", "source": "authority_completion"}
        for value in authority_completion.get("forbidden_controls", [])
    )
    source_status = "latest_remote_observed" if source_snapshot_head == remote_probe else "floor_or_newer_but_not_latest_remote"
    decision_rows = [
        {
            "decision_id": "VACD001",
            "status": "selected",
            "decision": "Absorb the latest fetched immutable VPS snapshot as a package guard.",
            "reason": "The remote branch advanced beyond the prior local VPS guard and contains package-relevant protective authority code, tests, and deployment artifacts.",
        },
        {
            "decision_id": "VACD002",
            "status": "selected",
            "decision": "Do not import local runtime code or claim deployment readiness from this absorption route.",
            "reason": "The local goal still requires final package selection gates, and runtime code import needs a separate scoped integration/merge lane after source access is clean.",
        },
    ]
    repair_rows = [
        {
            "repair_id": "VACR001_main_worktree_fetch",
            "status": fetch_status,
            "repair": "Compared the remote head probe with the local tracking ref and fetched only when stale.",
            "returncode": fetch_attempt.returncode,
        },
        {
            "repair_id": "VACR002_immutable_remote_snapshot_access",
            "status": "repaired_by_current_remote_tracking_snapshot",
            "repair": "Read package-guard artifacts directly from the fetched immutable Git snapshot instead of an ephemeral side clone.",
            "source_snapshot_head": source_snapshot_head,
        },
    ]

    summary = {
        "schema": "gtos.final_moonshot.vps_ai_companion_authority_absorption.summary.v1",
        "generated_utc": now,
        "status": "latest_vps_package_guard_absorbed_current_remote_snapshot",
        "base_local_vps_head": BASE_HEAD,
        "local_origin_head_before_fetch": local_origin_head_before_fetch,
        "local_origin_head_after_fetch": local_origin_head_after_fetch,
        "remote_probe_head": remote_probe,
        "source_snapshot_head": source_snapshot_head,
        "source_snapshot_ref": VPS_TRACKING_REF,
        "source_snapshot_verified": source_snapshot_verified,
        "required_floor": REQUIRED_FLOOR,
        "local_origin_floor_or_newer": local_floor_ok,
        "remote_probe_matches_source_snapshot": remote_probe == source_snapshot_head,
        "main_worktree_fetch_status": fetch_status,
        "main_worktree_fetch_returncode": fetch_attempt.returncode,
        "main_worktree_fetch_stderr_tail": split_lines(fetch_attempt.stderr)[-5:],
        "commit_rows": len(commit_rows),
        "changed_path_rows": len(code_rows),
        "package_relevant_changed_path_rows": package_relevant_changed_path_rows,
        "path_classification_counts": dict(sorted(path_classification_counts.items())),
        "authority_verification_ok": authority_verification.get("ok"),
        "micro_observation_verification_ok": micro_verification.get("ok"),
        "authority_level": authority_verification.get("config", {}).get("authority_level"),
        "ai_companion_enabled": authority_verification.get("config", {}).get("enabled"),
        "active_control_count": authority_verification.get("active_control_summary", {}).get("active_control_count"),
        "proposal_count": authority_verification.get("active_control_summary", {}).get("proposal_count"),
        "micro_sample_count": micro_verification.get("sample_count"),
        "micro_latest_packet_window_rows": micro_verification.get("latest_packet_window_rows"),
        "micro_latest_launcher_window_rows": micro_verification.get("latest_launcher_window_rows"),
        "micro_latest_opportunity_count": micro_verification.get("latest_opportunity_count"),
        "micro_recommendation_count": len(micro_synthesis.get("recommendations", [])),
        "runtime_effect_boundary": boundary,
        "local_runtime_code_imported": False,
        "final_package_selected": False,
        "model_training_allowed": False,
        "deployment_readiness_claim": False,
        "broker_runtime_change_status": False,
        "direct_broker_mutation_by_this_route": False,
        "forbidden_surface_status": {
            "live_trading": False,
            "broker_operation": False,
            "broker_account_order_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "blind_remote_push": False,
            "live_vps_restart_or_reload_by_this_route": False,
        },
        "package_implication": "The current VPS snapshot contains protective AI companion authority plus newer execution, lifecycle, broker-profile, supervision, shadow-intelligence, and ultimate-book changes. They are inventory-bound package inputs only: this absorption does not import or activate local runtime code.",
    }

    source_rows = [
        {
            "source_id": "main_worktree_fetch",
            "status": summary["main_worktree_fetch_status"],
            "returncode": fetch_attempt.returncode,
            "stderr_tail": summary["main_worktree_fetch_stderr_tail"],
        },
        {
            "source_id": "remote_head_probe",
            "status": "readable",
            "head": remote_probe,
            "ref": VPS_REMOTE_REF,
        },
        {
            "source_id": "immutable_remote_tracking_snapshot",
            "status": "readable_immutable_remote_tracking_snapshot",
            "ref": VPS_TRACKING_REF,
            "head": source_snapshot_head,
        },
        {
            "source_id": "local_remote_tracking_ref",
            "status": source_status,
            "head": local_origin_head_after_fetch,
            "floor_or_newer": local_floor_ok,
        },
    ]

    route_pointer_rows = [
        {
            "route": AUTHORITY_ROUTE,
            "artifact": name,
            "source_snapshot_path": f"{source_snapshot_head}:{AUTHORITY_ROUTE}/{name}",
            "exists_in_source_snapshot": git_path_exists(source_snapshot_head, f"{AUTHORITY_ROUTE}/{name}"),
        }
        for name in [
            "AI_COMPANION_AUTHORITY_DEPLOYMENT.md",
            "VERIFICATION_RESULT.json",
            "COMPLETION_AUDIT.json",
            "DECISION_LEDGER.json",
            "OUTPUT_MANIFEST.json",
            "verify_ai_companion_authority_deployment.py",
        ]
    ]
    route_pointer_rows.extend(
        {
            "route": MICRO_ROUTE,
            "artifact": name,
            "source_snapshot_path": f"{source_snapshot_head}:{MICRO_ROUTE}/{name}",
            "exists_in_source_snapshot": git_path_exists(source_snapshot_head, f"{MICRO_ROUTE}/{name}"),
        }
        for name in [
            "VERIFICATION_RESULT.json",
            "MICRO_OBSERVATION_SYNTHESIS.json",
            "MICRO_OBSERVATION_SAMPLE_LEDGER.jsonl",
            "OUTPUT_MANIFEST.json",
            "verify_runtime_ai_companion_micro_observation.py",
        ]
    )

    completion = {
        "schema": "gtos.final_moonshot.vps_ai_companion_authority_absorption.completion_audit.v1",
        "generated_utc": now,
        "goal_completion_claim": False,
        "status": "not_complete_continue",
        "completed_requirements": [
            "Probed latest VPS branch head without relying on stale local fetch state.",
            "Materialized AI companion authority deployment evidence from the current immutable remote-tracking snapshot.",
            "Preserved runtime authority boundaries and forbidden controls as local package-planning guards.",
        ],
        "instruction_coverage": {
            "live_state_regenerated": True,
            "starter_and_controlling_prompt_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "vps_source_of_truth_update_read": True,
            "same_evidence_class_repair_pursued": True,
            "no_arbitrary_top_n": True,
            "full_changed_path_ledger_preserved": True,
            "full_commit_ledger_preserved": True,
        },
        "same_evidence_class_next_step": "Use the current snapshot as a package guard, reconcile its package-relevant changes against the Fable integration surface, and continue the B7 proof ladder without importing or activating VPS runtime code by implication.",
        "forbidden_surface_status": summary["forbidden_surface_status"],
    }

    manifest_files = [
        "build_vps_ai_companion_authority_absorption.py",
        "verify_vps_ai_companion_authority_absorption.py",
        "VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json",
        "VPS_AI_COMPANION_REMOTE_COMMIT_LEDGER.jsonl",
        "VPS_AI_COMPANION_CODE_IMPACT_LEDGER.jsonl",
        "VPS_AI_COMPANION_ROUTE_ARTIFACT_POINTER_LEDGER.jsonl",
        "VPS_AI_COMPANION_RUNTIME_BOUNDARY_LEDGER.jsonl",
        "VPS_AI_COMPANION_SOURCE_ACCESS_LEDGER.jsonl",
        "DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "SATURATION_SELF_RED_TEAM.md",
        "NEXT_PROMPT.md",
        "OUTPUT_MANIFEST.json",
        "VERIFICATION_RESULT.json",
    ]

    write_json(ROUTE / "VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json", summary)
    write_jsonl(ROUTE / "VPS_AI_COMPANION_REMOTE_COMMIT_LEDGER.jsonl", commit_rows)
    write_jsonl(ROUTE / "VPS_AI_COMPANION_CODE_IMPACT_LEDGER.jsonl", code_rows)
    write_jsonl(ROUTE / "VPS_AI_COMPANION_ROUTE_ARTIFACT_POINTER_LEDGER.jsonl", route_pointer_rows)
    write_jsonl(ROUTE / "VPS_AI_COMPANION_RUNTIME_BOUNDARY_LEDGER.jsonl", boundary_rows)
    write_jsonl(ROUTE / "VPS_AI_COMPANION_SOURCE_ACCESS_LEDGER.jsonl", source_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE / "REPAIR_LEDGER.jsonl", repair_rows)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": "gtos.final_moonshot.vps_ai_companion_authority_absorption.focused_test_result.v1",
            "generated_utc": now,
            "status": "pending_verifier",
            "remote_probe_head": remote_probe,
            "source_snapshot_head": source_snapshot_head,
            "source_snapshot_verified": source_snapshot_verified,
            "authority_verification_ok": authority_verification.get("ok"),
            "micro_observation_verification_ok": micro_verification.get("ok"),
        },
    )
    write_text(
        ROUTE / "SATURATION_SELF_RED_TEAM.md",
        f"""# VPS AI Companion Authority Absorption Self Red Team

Generated: {now}

- `git ls-remote` and the fetched remote-tracking ref agree on head `{remote_probe}`.
- Package-guard artifacts and changed-path impact were read from that immutable Git snapshot.
- The full `BASE_HEAD..current` commit and path inventory is preserved; package-relevant runtime changes are not dismissed as context-only drift.
- This route does not import local runtime code, does not authorize live broker action, and does not claim final package readiness.
- AI companion authority remains typed and protective: pause new entries, symbol/sleeve cooldown, and reduce-only risk controls.
""",
    )
    write_text(
        ROUTE / "NEXT_PROMPT.md",
        f"""# Next Prompt

Continue from current disk state. Treat VPS snapshot `{remote_probe}` as a current package guard, not implicit local runtime authority. Reconcile package-relevant execution, lifecycle, broker-profile, shadow-intelligence, and ultimate-book changes against the active Fable batch before any scoped import. Keep broker/live/final false and continue the B7 proof ladder from current replay evidence.
""",
    )
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": "gtos.final_moonshot.vps_ai_companion_authority_absorption.output_manifest.v1",
            "generated_utc": now,
            "files": [{"path": name, "exists": (ROUTE / name).exists()} for name in manifest_files],
        },
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
