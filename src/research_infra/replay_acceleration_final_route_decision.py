"""Final measured route decision for the bounded replay acceleration program.

The decision aggregates only accepted structural evidence.  It does not inspect
legacy progress rows or economic outputs and cannot grant successor-arm, broker,
live, deployment, or full accelerated S0R0 authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.final_route_decision.v1"
AMENDMENT_SCHEMA = "gtos.replay_acceleration.prospective_contract_amendment.v1"
OUTPUT_DIR = Path(
    "research/operations/replay_acceleration_final_route_decision_2026_07_19"
)
RESULT_NAME = "FINAL_ACCELERATION_ROUTE_DECISION.json"
AMENDMENT_NAME = "PROSPECTIVE_CONTRACT_AMENDMENT_V1.json"
PROTECTED_LEGACY_PID = 34389
LEGACY_OUTPUT_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_"
    "S0R0_SOURCE_REPAIRED_R3_CAP_R2"
)
LEGACY_ROUTE = Path(
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
WARNING_BYTES = 34 * 1024**3
HARD_FLOOR_BYTES = 28 * 1024**3

STAGE_PATHS: dict[str, tuple[Path, str]] = {
    "authoritative_source": (
        Path(
            "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
            "BOUNDED_EQUIVALENCE_RESULT.json"
        ),
        "BOUNDED_EQUIVALENCE_ACCEPTED_FOR_REPLAY_SLICE",
    ),
    "normalization": (
        Path(
            "research/operations/replay_acceleration_normalized_slice_2026_07_19/"
            "NORMALIZATION_EQUIVALENCE_RESULT.json"
        ),
        "NORMALIZATION_EQUIVALENCE_ACCEPTED",
    ),
    "candidate_boundary": (
        Path(
            "research/operations/replay_acceleration_candidate_boundary_2026_07_19/"
            "CANDIDATE_BOUNDARY_RESULT.json"
        ),
        "CANDIDATE_BASE_BOUNDARY_ACCEPTED",
    ),
    "isolated_reducers": (
        Path(
            "research/operations/replay_acceleration_isolated_reducers_2026_07_19/"
            "ISOLATED_REDUCER_RESULT.json"
        ),
        "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED",
    ),
    "typed_proofs": (
        Path(
            "research/operations/replay_acceleration_typed_proofs_2026_07_19/"
            "TYPED_PROOF_RESULT.json"
        ),
        "TYPED_STREAMING_PROOF_PLANE_ACCEPTED",
    ),
    "resume": (
        Path(
            "research/operations/replay_acceleration_resume_2026_07_19/"
            "RESUME_RESULT.json"
        ),
        "COMPLETE_RESUME_SEMANTICS_ACCEPTED",
    ),
    "resource_architecture": (
        Path(
            "research/operations/replay_acceleration_resource_architecture_2026_07_19/"
            "RESOURCE_ARCHITECTURE_RESULT.json"
        ),
        "RESOURCE_STORAGE_ARCHITECTURE_ACCEPTED",
    ),
    "progressive_two_day": (
        Path(
            "research/operations/replay_acceleration_progressive_benchmark_2026_07_19/"
            "PROGRESSIVE_EQUIVALENCE_RESULT.json"
        ),
        "PROGRESSIVE_TWO_DAY_EQUIVALENCE_ACCEPTED",
    ),
}

ACCEPTED_COMMIT_CHAIN = (
    "0d4faafc35f5d93ee8a54bc16d4e37b1c137394c",
    "11c007e0f",
    "c6f9751a5",
    "cee459a5b",
    "1210df806",
    "b4c8e7c9f",
    "668038992",
    "3570c4b0b",
    "01a076e5f",
    "30b2ed114",
    "6c740781b",
    "0668be9d9",
    "683bc0bc6",
    "cdca644d9",
    "7df73173a",
)


class FinalRouteError(RuntimeError):
    """Stable fail-closed final-route rejection."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FinalRouteError(code)


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _full_commit(commit: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _available_bytes() -> int:
    stat = os.statvfs(Path.cwd())
    return stat.f_bavail * stat.f_frsize


def _tree_allocated_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            stat = item.stat()
            total += stat.st_blocks * 512 if stat.st_blocks else stat.st_size
    return total


def load_accepted_layers() -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for stage, (path, expected_gate) in STAGE_PATHS.items():
        try:
            raw = path.read_bytes()
            payload = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FinalRouteError(f"accepted_layer_missing:{stage}") from exc
        _require(payload.get("status") == "ACCEPTED", f"accepted_layer_status_invalid:{stage}")
        _require(payload.get("gate") == expected_gate, f"accepted_layer_gate_invalid:{stage}")
        root = payload.get("result_root_sha256")
        _require(isinstance(root, str) and len(root) == 64, f"accepted_layer_root_invalid:{stage}")
        layers.append(
            {
                "stage": stage,
                "path": path.as_posix(),
                "file_sha256": hashlib.sha256(raw).hexdigest(),
                "file_bytes": len(raw),
                "schema": payload.get("schema"),
                "gate": payload.get("gate"),
                "status": payload.get("status"),
                "result_root_sha256": root,
            }
        )
    return layers


def _ps_observation() -> dict[str, Any]:
    completed = subprocess.run(
        ["ps", "-p", str(PROTECTED_LEGACY_PID), "-o", "pid=,state=,etime=,command="],
        check=False,
        capture_output=True,
        text=True,
    )
    line = completed.stdout.strip()
    if completed.returncode != 0 or not line:
        return {
            "pid": PROTECTED_LEGACY_PID,
            "running": False,
            "state": None,
            "elapsed": None,
            "command_sha256": None,
            "expected_output_prefix_present_in_process": False,
        }
    parts = line.split(None, 3)
    _require(len(parts) == 4, "legacy_process_observation_invalid")
    command = parts[3]
    return {
        "pid": int(parts[0]),
        "running": True,
        "state": parts[1],
        "elapsed": parts[2],
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "expected_output_prefix_present_in_process": LEGACY_OUTPUT_PREFIX in command,
    }


def observe_legacy_golden_availability() -> dict[str, Any]:
    process = _ps_observation()
    matches: list[str] = []
    if LEGACY_ROUTE.exists():
        for path in LEGACY_ROUTE.rglob("*"):
            relative = path.as_posix()
            upper = path.name.upper()
            if (
                LEGACY_OUTPUT_PREFIX in relative
                and any(marker in upper for marker in ("SEALED", "MANIFEST", "COMPLETION"))
            ):
                matches.append(relative)
    matches.sort()
    return {
        **process,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sealed_golden_artifact_count_in_worktree": len(matches),
        "sealed_golden_artifact_path_root_sha256": stable_sha256(matches),
        "sealed_full_month_golden_available": bool(matches) and not process["running"],
        "discovery_allowlist": ["SEALED", "MANIFEST", "COMPLETION"],
        "progress_rows_read": False,
        "forbidden_output_fields_read": [],
        "process_namespace_inspected": False,
        "modified_or_signaled": False,
    }


def measured_route_decision() -> dict[str, Any]:
    progressive_path = STAGE_PATHS["progressive_two_day"][0]
    progressive = json.loads(progressive_path.read_bytes())
    runs = progressive.get("measurements", {}).get("runs") or []
    _require(len(runs) == 4, "progressive_measurement_run_count_invalid")
    fastest = min(runs, key=lambda row: float(row["end_to_end_wall_seconds"]))
    stages = fastest.get("stage_wall_seconds") or {}
    dominant_stage = max(stages, key=lambda key: float(stages[key]))
    cold = [float(row["end_to_end_wall_seconds"]) for row in runs if row["cache_state_label"] == "cold"]
    warm = [float(row["end_to_end_wall_seconds"]) for row in runs if row["cache_state_label"] == "warm"]
    wall = float(fastest["end_to_end_wall_seconds"])
    stage_shares = {
        name: float(seconds) / wall
        for name, seconds in stages.items()
    }
    return {
        "classification": "fastest_tested_bounded_candidate_origin_route_not_whole_replay",
        "fastest_tested_run_label": fastest["run_label"],
        "fastest_tested_wall_seconds": wall,
        "immutable_prebarrier_worker_count": fastest["immutable_prebarrier_worker_count"],
        "candidate_generation_worker_count": fastest["candidate_generation_worker_count"],
        "peak_rss_bytes": fastest["resources"]["peak_rss_bytes"],
        "cpu_user_seconds": fastest["resources"]["cpu_user_seconds"],
        "cpu_system_seconds": fastest["resources"]["cpu_system_seconds"],
        "minor_page_faults": fastest["resources"]["minor_page_faults"],
        "major_page_faults": fastest["resources"]["major_page_faults"],
        "explicit_bytes_read": fastest["resources"]["explicit_bytes_read"],
        "explicit_run_receipt_bytes_written": fastest["resources"]["explicit_run_receipt_bytes_written"],
        "swap_delta_bytes": fastest["swap"]["delta_bytes"],
        "stage_wall_seconds": stages,
        "stage_wall_share": stage_shares,
        "dominant_stage": dominant_stage,
        "cold_wall_seconds": cold,
        "warm_wall_seconds": warm,
        "cold_mean_seconds": sum(cold) / len(cold),
        "warm_mean_seconds": sum(warm) / len(warm),
        "cold_to_warm_mean_ratio": (sum(cold) / len(cold)) / (sum(warm) / len(warm)),
        "whole_replay_speedup_claim": False,
        "warm_speedup_claim": False,
        "two_worker_speedup_claim": False,
        "tested_scope": progressive["scope"],
        "campaign_candidate_identity_root_sha256": progressive["determinism"][
            "campaign_candidate_identity_root_sha256"
        ],
        "progressive_result_root_sha256": progressive["result_root_sha256"],
    }


def _identity_projection() -> dict[str, Any]:
    source = json.loads(STAGE_PATHS["authoritative_source"][0].read_bytes())
    normalized = json.loads(STAGE_PATHS["normalization"][0].read_bytes())
    candidate = json.loads(STAGE_PATHS["candidate_boundary"][0].read_bytes())
    reducer = json.loads(STAGE_PATHS["isolated_reducers"][0].read_bytes())
    typed = json.loads(STAGE_PATHS["typed_proofs"][0].read_bytes())
    resume = json.loads(STAGE_PATHS["resume"][0].read_bytes())
    resource_result = json.loads(STAGE_PATHS["resource_architecture"][0].read_bytes())
    progressive = json.loads(STAGE_PATHS["progressive_two_day"][0].read_bytes())
    return {
        "accepted_ancestor_commit": source["accepted_base_commit"],
        "current_code_commit": _git_head(),
        "accepted_commit_chain": [_full_commit(commit) for commit in ACCEPTED_COMMIT_CHAIN],
        "source": {
            "result_root_sha256": source["result_root_sha256"],
            "bundle_root_sha256": source["bundle_root_sha256"],
            "selection_root_sha256": source["selection_root_sha256"],
            "source_plan_digest_sha256": source["source_plan_digest_sha256"],
        },
        "normalization": {
            "result_root_sha256": normalized["result_root_sha256"],
            "normalized_bundle_root_sha256": normalized["normalized_bundle_root_sha256"],
            "code_identity": normalized["code_identity"],
        },
        "candidate_boundary": {
            "result_root_sha256": candidate["result_root_sha256"],
            "candidate_probe_root_sha256": stable_sha256(candidate["candidate_probe"]),
        },
        "isolated_reducers": {
            "result_root_sha256": reducer["result_root_sha256"],
            "structural_state_root_sha256": stable_sha256(
                {
                    "arms": reducer["arms"],
                    "cross_symbol_barrier": reducer["cross_symbol_barrier"],
                }
            ),
        },
        "typed_proofs": {
            "result_root_sha256": typed["result_root_sha256"],
            "campaign_root_sha256": typed.get("campaign_root_sha256"),
        },
        "resume": {
            "result_root_sha256": resume["result_root_sha256"],
            "resume_route_root_sha256": resume["resume_route_root_sha256"],
        },
        "resource_architecture": {
            "result_root_sha256": resource_result["result_root_sha256"],
            "code_identity": resource_result["code_identity"],
        },
        "progressive_two_day": {
            "result_root_sha256": progressive["result_root_sha256"],
            "campaign_candidate_identity_root_sha256": progressive["determinism"][
                "campaign_candidate_identity_root_sha256"
            ],
            "code_identity": progressive["code_identity"],
        },
    }


def build_prospective_amendment() -> dict[str, Any]:
    amendment: dict[str, Any] = {
        "schema": AMENDMENT_SCHEMA,
        "status": "DRAFT_NOT_AUTHORITY_DO_NOT_EXECUTE",
        "purpose": "prospective_identity_binding_for_fastest_tested_safe_bounded_route",
        "identity_projection": _identity_projection(),
        "bounded_preprocessing_authority": True,
        "full_accelerated_s0r0_authority": False,
        "successor_arm_authority": False,
        "broker_or_live_authority": False,
        "deployment_authority": False,
        "activation_prerequisites": [
            "sealed_full_month_legacy_s0r0_golden_available",
            "full_accelerated_s0r0_structural_comparison_independently_accepted",
            "prospective_contract_amendment_human_sealed",
        ],
        "permitted_route": {
            "immutable_source_cache": True,
            "normalized_partition_cache": True,
            "candidate_base_sharing_only_through_proven_factor_free_boundary": True,
            "cross_symbol_barrier_required": True,
            "policy_days_chronological": True,
            "candidate_generation_worker_count": 1,
            "immutable_prebarrier_worker_count": 1,
            "actual_policy_or_successor_execution": False,
        },
        "outcome_blind": True,
        "forbidden_output_fields_read": [],
    }
    amendment["amendment_root_sha256"] = stable_sha256(amendment)
    return amendment


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    os.replace(temporary, path)


def build_final_route_decision(*, amendment_path: Path) -> dict[str, Any]:
    layers = load_accepted_layers()
    golden = observe_legacy_golden_availability()
    measured = measured_route_decision()
    amendment_raw = amendment_path.read_bytes()
    amendment = json.loads(amendment_raw)
    _require(golden["sealed_full_month_golden_available"] is False, "golden_availability_changed")
    available = _available_bytes()
    _require(available >= WARNING_BYTES, "disk_below_warning")
    writer_path = Path(__file__)
    verifier_path = writer_path.with_name(
        "replay_acceleration_final_route_decision_verifier.py"
    )
    test_path = Path("tests/test_replay_acceleration_final_route_decision.py")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "BLOCKED_EXTERNAL_GOLDEN_INCOMPLETE",
        "gate": "HUMAN_OR_EXTERNAL_BLOCKER",
        "accepted_bounded_layers": layers,
        "accepted_bounded_layer_count": len(layers),
        "measured_route_decision": measured,
        "fastest_safe_successor": {
            "classification": "bounded_candidate_origin_route_only",
            "immutable_prebarrier_worker_count": 1,
            "candidate_generation_worker_count": 1,
            "cross_symbol_barrier": "required",
            "chronology": "required",
            "content_addressed_source_and_normalization": "accepted",
            "typed_proof_and_resume": "accepted_structural_only",
            "actual_policy_execution": False,
            "whole_replay_claim": False,
        },
        "residual_bottlenecks": [
            {
                "stage": "all_symbol_snapshot",
                "wall_seconds": measured["stage_wall_seconds"]["all_symbol_snapshot"],
                "wall_share": measured["stage_wall_share"]["all_symbol_snapshot"],
            },
            {
                "stage": "candidate_origin_generation_single_worker",
                "wall_seconds": measured["stage_wall_seconds"][
                    "candidate_origin_generation_single_worker"
                ],
                "wall_share": measured["stage_wall_share"][
                    "candidate_origin_generation_single_worker"
                ],
            },
            {
                "stage": "full_month_golden_comparison",
                "measurement_available": False,
                "blocker": "sealed_full_month_legacy_s0r0_golden_unavailable",
            },
        ],
        "external_blocker": {
            "code": "sealed_full_month_legacy_s0r0_golden_unavailable",
            "protected_pid": PROTECTED_LEGACY_PID,
            "protected_process_running": golden["running"],
            "sealed_golden_artifact_count_in_worktree": golden[
                "sealed_golden_artifact_count_in_worktree"
            ],
            "bounded_implementation_prerequisite": False,
            "final_accelerated_route_prerequisite": True,
            "resolution": (
                "external legacy process completes and publishes its sealed structural golden; "
                "then run full accelerated S0R0 structural comparison under separately sealed authority"
            ),
        },
        "legacy_golden_observation": golden,
        "execution_authority": {
            "bounded_immutable_preprocessing": True,
            "bounded_candidate_origin_projection": True,
            "full_accelerated_s0r0": False,
            "successor_arms": False,
            "broker_live_vps_canary_deployment": False,
            "production_trading": False,
        },
        "prospective_amendment": {
            "path": amendment_path.as_posix(),
            "file_sha256": hashlib.sha256(amendment_raw).hexdigest(),
            "file_bytes": len(amendment_raw),
            "amendment_root_sha256": amendment["amendment_root_sha256"],
            "status": amendment["status"],
        },
        "resource_and_storage": {
            "available_bytes": available,
            "warning_bytes": WARNING_BYTES,
            "hard_floor_bytes": HARD_FLOOR_BYTES,
            "final_route_allocated_bytes_before_result": _tree_allocated_bytes(OUTPUT_DIR),
            "files_deleted": 0,
            "bytes_reclaimed": 0,
            "broad_lfs_hydration_performed": False,
            "lfs_prune_performed": False,
            "unique_proof_evidence_preserved": True,
        },
        "code_identity": {
            "execution_commit": _git_head(),
            "writer_path": writer_path.as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
            "test_path": test_path.as_posix(),
            "test_sha256": file_sha256(test_path),
        },
        "exact_command_receipts": {
            "materialization": [
                "python3",
                "-m",
                "src.research_infra.replay_acceleration_final_route_decision",
                "--output-dir",
                OUTPUT_DIR.as_posix(),
            ],
            "structural_process_observation": [
                "ps", "-p", str(PROTECTED_LEGACY_PID),
                "-o", "pid=,state=,etime=,command=",
            ],
        },
        "outcome_blind_structural_only": True,
        "progress_rows_read": False,
        "forbidden_output_fields_read": [],
        "policy_execution_entered": False,
        "successor_arm_execution_launched": False,
        "whole_replay_speedup_claim": False,
        "warm_speedup_claim": False,
    }
    result["result_root_sha256"] = stable_sha256(result)
    return result


def write_final_route_decision(output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    amendment_path = output_dir / AMENDMENT_NAME
    _atomic_write(amendment_path, build_prospective_amendment())
    result_path = output_dir / RESULT_NAME
    _atomic_write(
        result_path,
        build_final_route_decision(amendment_path=amendment_path),
    )
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    path = write_final_route_decision(args.output_dir)
    result = json.loads(path.read_bytes())
    print(
        canonical_bytes(
            {
                "status": result["status"],
                "gate": result["gate"],
                "path": path.as_posix(),
                "result_root_sha256": result["result_root_sha256"],
            }
        ).decode("ascii")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
