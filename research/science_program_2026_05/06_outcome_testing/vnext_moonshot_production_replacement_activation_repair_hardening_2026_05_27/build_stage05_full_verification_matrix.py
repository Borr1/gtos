from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
STAGE_ID = "stage_05_full_verification_matrix"
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_FULL_VERIFICATION_MATRIX_{DATE}.json"
SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def run_command(command_id: str, args: list[str], timeout: int = 300) -> dict[str, Any]:
    started = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        exit_code = proc.returncode
        stdout_tail = proc.stdout[-4000:]
        stderr_tail = proc.stderr[-4000:]
        status = "passed" if proc.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout_tail = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        stderr_tail = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
        status = "timeout"
    ended = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "id": command_id,
        "command": " ".join(args),
        "started_at_utc": started.isoformat().replace("+00:00", "Z"),
        "ended_at_utc": ended.isoformat().replace("+00:00", "Z"),
        "duration_seconds": round((ended - started).total_seconds(), 3),
        "exit_code": exit_code,
        "status": status,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def collect_gtos_runtime_nodeids() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_gtos_vnext_runtime.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or proc.stdout[-2000:])
    return [
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip().startswith("tests/test_gtos_vnext_runtime.py::")
    ]


def update_spine(stage04: dict[str, Any], passed: bool, generated_at: str) -> None:
    spine = read_json(SPINE)
    spine["current_stage"] = "stage_06_commit_and_final_route_state" if passed else STAGE_ID
    spine["generated_at_utc"] = generated_at
    spine["next_exact_action"] = (
        "Run Stage06 final current-evidence closure and commit."
        if passed
        else "Repair failing Stage05 matrix checks and rerun."
    )
    spine.setdefault("stage_status", {})[STAGE_ID] = "completed" if passed else "failed"
    completed = set(spine.get("completed_gates") or [])
    if passed:
        completed.update(
            {
                "rollback_executable_proof",
                "non_mutating_check_mode",
                "stage05_full_verification_matrix",
                "runtime_leakage_no_old_fallback",
                "current_manifest_route_state_verification",
                "live_dynamic_execution_router_launch_readiness",
            }
        )
    spine["completed_gates"] = sorted(completed)
    open_gates = set(spine.get("open_gates") or [])
    if passed:
        open_gates.difference_update(
            {
                "rollback_executable_proof",
                "non_mutating_check_mode",
                "stage05_full_verification_matrix",
                "runtime_leakage_no_old_fallback",
                "current_manifest_route_state_verification",
                "live_dynamic_execution_router_launch_readiness",
            }
        )
    spine["open_gates"] = sorted(open_gates)
    spine["latest_numbers"] = {
        "old_three_selected_rows": stage04["selector_counts"]["old_three_selected_rows"],
        "broader_origin_selected_rows": stage04["selector_counts"]["broader_origin_selected_rows"],
        "combined_selected_rows": stage04["selector_counts"]["combined_selected_rows"],
        "total_r": stage04["selector_metrics"]["total_r"],
    }
    active = set(spine.get("active_files") or [])
    active.add(rel(OUTPUT))
    active.add(rel(ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE05_ROLLBACK_PROOF_{DATE}.json"))
    active.add(rel(ROUTE_DIR / f"verify_stage05_runtime_leakage.py"))
    active.add(rel(ROUTE_DIR / f"verify_stage05_rollback_proof.py"))
    active.add(rel(ROUTE_DIR / f"verify_stage04_canonical_frequency_trade_r_ledger.py"))
    active.add(rel(ROUTE_DIR / f"verify_vnext_activation_repair_output_manifest.py"))
    active.add(rel(ROUTE_DIR / f"verify_vnext_activation_repair_route_state_integrity.py"))
    active.add(rel(ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"))
    active.add(rel(ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py"))
    active.add(rel(ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"))
    active.add(rel(ROUTE_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"))
    active.add(rel(ROUTE_DIR / "build_execution_policy_momentum_promotion.py"))
    active.add(rel(ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"))
    active.add(rel(ROUTE_DIR / "ei15r" / "momentum_policy_promotion_summary.json"))
    active.add(rel(ROUTE_DIR / "ei15r" / "momentum_policy_promotion.manifest.jsonl"))
    active.add(rel(ROUTE_DIR / "ei15r" / "selected_policy_risk_proof_summary.json"))
    active.add(rel(ROUTE_DIR / "ei15r" / "momentum_policy_lifecycle_propagation_proof.json"))
    active.add(rel(ROUTE_DIR / "build_launch_execution_router_dossier.py"))
    active.add(rel(ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_ROUTER_LAUNCH_DOSSIER_{DATE}.json"))
    spine["active_files"] = sorted(active)
    write_json(SPINE, spine)


def main() -> int:
    stage04 = read_json(STAGE04_SUMMARY)
    commands: list[dict[str, Any]] = []
    py_files = [
        "src/components/gtos_vnext_runtime.py",
        "src/components/orchestrator.py",
        "src/components/execution.py",
        "src/components/broader_origin_generators.py",
        "src/notifications.py",
        "src/components/slippage_shadow_logger.py",
    ]
    commands.append(run_command("py_compile_runtime_surface", [sys.executable, "-m", "py_compile", *py_files]))
    commands.append(
        run_command(
            "stage03_alias_verifier_check_mode",
            [sys.executable, rel(ROUTE_DIR / "verify_stage03_mt5_aliases_readonly.py"), "--check"],
        )
    )
    commands.append(
        run_command(
            "stage03_production_extraction_check_mode",
            [sys.executable, rel(ROUTE_DIR / "verify_stage03_production_extraction_readonly.py"), "--check"],
        )
    )
    commands.append(
        run_command(
            "stage04_canonical_frequency_ledger_check",
            [sys.executable, rel(ROUTE_DIR / "verify_stage04_canonical_frequency_trade_r_ledger.py"), "--check"],
            timeout=420,
        )
    )
    commands.append(
        run_command(
            "execution_intelligence_final_dynamic_router_replay_build",
            [sys.executable, rel(ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py")],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_intelligence_final_dynamic_router_replay_check",
            [
                sys.executable,
                rel(ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"),
                "--check",
            ],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_policy_momentum_promotion_build",
            [sys.executable, rel(ROUTE_DIR / "build_execution_policy_momentum_promotion.py")],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_policy_momentum_promotion_verifier_result_write",
            [sys.executable, rel(ROUTE_DIR / "verify_execution_policy_momentum_promotion.py")],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_policy_momentum_promotion_check",
            [
                sys.executable,
                rel(ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"),
                "--check",
            ],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_intelligence_static_15r_check",
            [
                sys.executable,
                rel(ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"),
                "--check",
            ],
            timeout=900,
        )
    )
    commands.append(
        run_command(
            "execution_intelligence_route_unit_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                rel(ROUTE_DIR / "test_execution_intelligence_static_15r_ceiling_repair.py"),
                "-q",
                "--basetemp=.pytest-tmp-vnext-stage05-ei15r",
                "-o",
                "cache_dir=.pytest-tmp-vnext-stage05-ei15r-cache",
            ],
        )
    )
    commands.append(
        run_command(
            "launch_execution_router_dossier_build",
            [sys.executable, rel(ROUTE_DIR / "build_launch_execution_router_dossier.py")],
        )
    )
    commands.append(run_command("stage05_rollback_proof_build", [sys.executable, rel(ROUTE_DIR / "verify_stage05_rollback_proof.py")]))
    commands.append(
        run_command(
            "stage05_rollback_proof_check_mode",
            [sys.executable, rel(ROUTE_DIR / "verify_stage05_rollback_proof.py"), "--check"],
        )
    )
    commands.append(
        run_command(
            "stage05_runtime_leakage_check",
            [sys.executable, rel(ROUTE_DIR / "verify_stage05_runtime_leakage.py"), "--check"],
        )
    )
    commands.append(
        run_command(
            "focused_runtime_broader_origin_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_vnext_production_wiring.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
                "-q",
                "--basetemp=.pytest-tmp-vnext-stage05-runtime",
                "-o",
                "cache_dir=.pytest-tmp-vnext-stage05-runtime-cache",
            ],
            timeout=420,
        )
    )
    commands.append(
        run_command(
            "focused_execution_lifecycle_pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_limit_order_flow.py",
                "tests/test_moonshot_default_off_policy_router.py",
                "tests/test_j46_j49_policy.py",
                "tests/test_notifications.py",
                "tests/test_slippage_shadow_logger.py",
                "-q",
                "--basetemp=.pytest-tmp-vnext-stage05-execution",
                "-o",
                "cache_dir=.pytest-tmp-vnext-stage05-execution-cache",
            ],
            timeout=420,
        )
    )
    nodeids = collect_gtos_runtime_nodeids()
    shard_count = 4
    for shard_index in range(shard_count):
        shard = [node for idx, node in enumerate(nodeids) if idx % shard_count == shard_index]
        commands.append(
            run_command(
                f"gtos_vnext_runtime_pytest_shard_{shard_index + 1}_of_{shard_count}",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    *shard,
                    "-q",
                    f"--basetemp=.pytest-tmp-vnext-stage05-runtime-shard-{shard_index}",
                    "-o",
                    f"cache_dir=.pytest-tmp-vnext-stage05-runtime-shard-{shard_index}-cache",
                ],
                timeout=600,
            )
        )
    commands.append(
        run_command(
            "git_diff_check_non_ei15r_row_ledgers",
            [
                "git",
                "diff",
                "--check",
                "--",
                ".",
                ":(exclude)research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/ei15r/*.jsonl",
            ],
            timeout=300,
        )
    )

    preliminary_passed = all(row["status"] == "passed" for row in commands)
    generated_at = utc_now()
    preliminary_result = {
        "schema_version": "vnext_activation_repair_stage05_full_verification_matrix_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "status": "passed" if preliminary_passed else "failed",
        "selector_counts_verified": stage04["selector_counts"],
        "selector_metrics_verified": stage04["selector_metrics"],
        "gtos_vnext_runtime_shards": {
            "collected_nodeids": len(nodeids),
            "shard_count": shard_count,
        },
        "commands": commands,
        "route_state_check_phase": "preliminary_result_written_before_current_route_state_check",
    }
    write_json(OUTPUT, preliminary_result)
    update_spine(stage04, preliminary_passed, generated_at)
    commands.append(
        run_command(
            "current_route_output_manifest_sync_before_route_state",
            [sys.executable, rel(ROUTE_DIR / "verify_vnext_activation_repair_output_manifest.py"), "--sync"],
            timeout=1800,
        )
    )
    commands.append(
        run_command(
            "final_semantic_state_proof_build_before_route_state",
            [sys.executable, rel(ROUTE_DIR / "build_vnext_activation_repair_final_semantic_state_proof.py")],
        )
    )
    commands.append(
        run_command(
            "stage06_final_route_state_build_before_integrity_check",
            [sys.executable, rel(ROUTE_DIR / "build_stage06_final_route_state.py")],
        )
    )
    commands.append(
        run_command(
            "final_semantic_state_proof_build_after_stage06_route_state",
            [sys.executable, rel(ROUTE_DIR / "build_vnext_activation_repair_final_semantic_state_proof.py")],
        )
    )
    commands.append(
        run_command(
            "current_route_output_manifest_sync_after_final_proof",
            [sys.executable, rel(ROUTE_DIR / "verify_vnext_activation_repair_output_manifest.py"), "--sync"],
            timeout=1800,
        )
    )
    commands.append(
        run_command(
            "current_route_state_integrity_check",
            [sys.executable, rel(ROUTE_DIR / "verify_vnext_activation_repair_route_state_integrity.py"), "--check"],
            timeout=1800,
        )
    )
    passed = all(row["status"] == "passed" for row in commands)
    if passed != preliminary_passed:
        generated_at = utc_now()
        update_spine(stage04, passed, generated_at)

    result = {
        "schema_version": "vnext_activation_repair_stage05_full_verification_matrix_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "status": "passed" if passed else "failed",
        "selector_counts_verified": stage04["selector_counts"],
        "selector_metrics_verified": stage04["selector_metrics"],
        "gtos_vnext_runtime_shards": {
            "collected_nodeids": len(nodeids),
            "shard_count": shard_count,
        },
        "commands": commands,
        "manifest_sync_executed_after_matrix_write": True,
    }
    write_json(OUTPUT, result)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage05_full_verification_matrix_completed",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": result["status"],
            "command_count": len(commands),
            "failed_command_ids": [row["id"] for row in commands if row["status"] != "passed"],
        },
    )
    final_proof_sync = run_command(
        "final_semantic_state_proof_build_after_matrix_write",
        [sys.executable, rel(ROUTE_DIR / "build_vnext_activation_repair_final_semantic_state_proof.py")],
    )
    manifest_sync = run_command(
        "current_route_output_manifest_sync",
        [sys.executable, rel(ROUTE_DIR / "verify_vnext_activation_repair_output_manifest.py"), "--sync"],
        timeout=1800,
    )
    print(json.dumps({"stage05": result["status"], "final_proof_sync": final_proof_sync["status"], "manifest_sync": manifest_sync["status"], "output": rel(OUTPUT)}, sort_keys=True))
    return 0 if passed and final_proof_sync["status"] == "passed" and manifest_sync["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
