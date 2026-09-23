#!/usr/bin/env python3
"""Run the owner-approved corrected accelerated Jan 1-2 Task 2 slice.

The command exposes only a fresh output namespace. Dates, source plan, arm,
policy, sizing, symbol universe, chronology, cache route, and broker boundary
are immutable in this wrapper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_physical_reference_runner as physical,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE_DIR = physical.SOURCE_BUNDLE_DIR
SOURCE_SELECTION = physical.SOURCE_SELECTION
SOURCE_REBIND_AUTHORITY = physical.SOURCE_REBIND_AUTHORITY
EXPECTED_SOURCE_PLAN_DIGEST = physical.EXPECTED_SOURCE_PLAN_DIGEST
EXPECTED_ARM_FINGERPRINT = physical.EXPECTED_ARM_FINGERPRINT
EXPECTED_ECONOMIC_CONTRACT_DIGEST = physical.EXPECTED_ECONOMIC_CONTRACT_DIGEST
RECEIPT_NAME = "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
END_DAY = "2026-01-02"
DIRECT_SEMANTIC_MANIFEST_SCHEMA = (
    "gtos.replay_acceleration.task2_direct_semantic_source_manifest.v1"
)
DIRECT_SEMANTIC_JSONL_ROLES = (
    *physical.MATERIALIZED_SURFACE_ROLES,
    "semantic_candidate",
    "semantic_state_checkpoint",
    "semantic_order_preimage",
)


class SemanticSliceRejected(RuntimeError):
    """The restricted corrected accelerated slice was invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _scan_jsonl(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    byte_count = 0
    with path.open("rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                raise SemanticSliceRejected(
                    f"semantic_slice_jsonl_framing_invalid:{path.name}"
                )
            digest.update(raw)
            byte_count += len(raw)
            rows += 1
    return {
        "bytes": byte_count,
        "rows": rows,
        "sha256": digest.hexdigest(),
    }


def write_direct_semantic_source_manifest(
    *,
    namespace: Path,
    outputs: Mapping[str, Path],
    semantic_outputs: Mapping[str, Path],
    runtime_input_contract_root_sha256: str,
    shared_execution_contract_digest_sha256: str,
) -> dict[str, Any]:
    """Seal every direct-file input to the bounded semantic comparison."""

    namespace = Path(namespace).resolve()
    paths = {
        **{
            role: Path(outputs[role]).resolve()
            for role in physical.MATERIALIZED_SURFACE_ROLES
        },
        **{
            role: Path(semantic_outputs[role]).resolve()
            for role in (
                "semantic_candidate",
                "semantic_state_checkpoint",
                "semantic_order_preimage",
            )
        },
        "partial_summary": Path(outputs["partial_summary"]).resolve(),
    }
    files: dict[str, dict[str, Any]] = {}
    for role in DIRECT_SEMANTIC_JSONL_ROLES:
        path = paths[role]
        if not path.is_file() or path.is_symlink():
            raise SemanticSliceRejected(f"semantic_slice_surface_missing:{role}")
        files[role] = {
            "path": str(path),
            "format": "jsonl",
            **_scan_jsonl(path),
        }
    summary_path = paths["partial_summary"]
    if not summary_path.is_file() or summary_path.is_symlink():
        raise SemanticSliceRejected("semantic_slice_surface_missing:partial_summary")
    try:
        summary = json.loads(summary_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise SemanticSliceRejected("semantic_slice_partial_summary_invalid") from None
    if not isinstance(summary, Mapping):
        raise SemanticSliceRejected("semantic_slice_partial_summary_invalid")
    files["partial_summary"] = {
        "path": str(summary_path),
        "format": "json",
        "bytes": summary_path.stat().st_size,
        "sha256": _sha256(summary_path),
    }
    core = {
        "schema": DIRECT_SEMANTIC_MANIFEST_SCHEMA,
        "acceptance_authorized": False,
        "transport": "bounded_direct_hot_files",
        "streaming_proof_archive_used": False,
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": END_DAY,
            "day_count": 2,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id": "S0R0",
            "chunk_size": 1,
        },
        "source_identity": {
            "source_plan_digest_sha256": EXPECTED_SOURCE_PLAN_DIGEST,
            "arm_fingerprint_sha256": EXPECTED_ARM_FINGERPRINT,
            "arm_id": "S0R0",
            "profile": replay.PROFILE_REPAIRED,
            "source_bundle_dir": str(SOURCE_BUNDLE_DIR.resolve()),
            "source_selection_sha256": _sha256(SOURCE_SELECTION),
            "source_rebind_authority_sha256": _sha256(SOURCE_REBIND_AUTHORITY),
        },
        "execution_contract": {
            "runtime_input_contract_root_sha256": (
                runtime_input_contract_root_sha256
            ),
            "shared_execution_contract_digest_sha256": (
                shared_execution_contract_digest_sha256
            ),
            "economic_execution_contract_digest_sha256": (
                EXPECTED_ECONOMIC_CONTRACT_DIGEST
            ),
        },
        "namespace": str(namespace),
        "files": files,
        "direct_hot_file_count": len(files),
        "causal_or_economic_field_excluded": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    manifest = {
        **core,
        "source_manifest_root_sha256": replay.stable_sha256(core),
    }
    manifest_path = Path(semantic_outputs["semantic_source_manifest"])
    if manifest_path.exists() or manifest_path.is_symlink():
        raise SemanticSliceRejected("semantic_slice_manifest_must_be_new")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    replay.atomic_write_json(manifest_path, manifest)
    return manifest


def semantic_slice_args(output_dir: Path) -> argparse.Namespace:
    """Return the one cache-enabled corrected Jan 1-2 invocation."""

    output_dir = Path(output_dir)
    args = physical.physical_reference_args(output_dir)
    # Preserve the accepted full-January source authority while stopping the
    # economic reducer only after the second post-cleanup day checkpoint.
    args.max_days = None
    args.accepted_physical_reference = False
    args.physical_reference_checkpoint_after_day = None
    args.task2_semantic_checkpoint_after_day = END_DAY
    args.runtime_evidence_root = replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    args.source_acceleration_cache_root = output_dir / "typed-cache"
    args.tick_sparse_cache_root = replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    args.source_prewarm_workers = 4
    # The production streaming archive is intentionally coupled to its real
    # Jan-7 parity interlock.  This owner-approved Jan-1-2 comparator instead
    # seals all direct ledgers after the contiguous run completes.
    args.streaming_proof_archive_root = None
    args.max_streaming_proof_archive_bytes = 0
    return args


def bind_source_acceleration_authority(args: argparse.Namespace) -> None:
    """Mirror the engine's typed-source binding before hashing its contract."""

    accelerator = replay.RealReplaySourceAccelerator.from_accepted_bundle(
        source_bundle_dir=Path(args.source_acceleration_bundle_dir),
        selection_path=Path(args.source_acceleration_selection),
        typed_cache_root=Path(args.source_acceleration_cache_root),
        expected_bundle_root=str(args.expected_source_bundle_root_sha256),
        expected_source_plan_digest=str(
            args.expected_source_plan_digest_sha256
        ),
    )
    args.source_acceleration_authority = (
        replay.bound_source_acceleration_authority(args, accelerator)
    )


def validate_shared_contract_preflight(
    args: argparse.Namespace,
    shared: Mapping[str, Any],
) -> None:
    """Prove the wrapper and engine will hash the same prepared arguments."""

    factorial = replay.selection_sizing_factorial_binding_from_args(args)
    recomputed = replay.broad_replay_shared_execution_contract(
        profiles=args.profiles,
        active_symbols=replay.active_replay_symbol_universe(
            replay.requested_replay_symbols(args.symbols)
        ),
        execution_options=replay.broad_replay_execution_options_from_args(
            args,
            factorial_arm_binding=factorial,
        ),
        runtime_input_contract=replay.ultimate_package_runtime_input_contract(),
        factorial_arm_binding=factorial,
    )
    expected = shared.get("shared_execution_contract_digest_sha256")
    if (
        recomputed.get("valid") is not True
        or expected != recomputed.get("shared_execution_contract_digest_sha256")
        or expected != args.expected_shared_execution_contract_sha256
    ):
        raise SemanticSliceRejected("semantic_slice_shared_contract_preflight_invalid")


def _validate_progress(
    partial: Mapping[str, Any],
    checkpoint: Mapping[str, Any] | None,
) -> None:
    progress = partial.get("progress_rows")
    if (
        partial.get("status") != "partial_in_progress_not_final_proof"
        or not isinstance(progress, list)
        or len(progress) != 2
        or [row.get("start_day") for row in progress]
        != ["2026-01-01", "2026-01-02"]
        or [row.get("end_day") for row in progress]
        != ["2026-01-01", "2026-01-02"]
        or not isinstance(checkpoint, Mapping)
        or checkpoint.get("status")
        != "JAN1_2_POST_CLEANUP_CHECKPOINT_COMPLETE"
        or checkpoint.get("canonical_source_plan_digest_sha256")
        != EXPECTED_SOURCE_PLAN_DIGEST
        or checkpoint.get("acceptance_authorized") is not False
        or checkpoint.get("broker_live_authority") is not False
        or checkpoint.get("broker_mutation_enabled") is not False
    ):
        raise SemanticSliceRejected("semantic_slice_checkpoint_result_invalid")


def run_semantic_slice(output_dir: Path) -> dict[str, Any]:
    """Execute and structurally seal the corrected accelerated slice."""

    output_dir = Path(output_dir)
    args = semantic_slice_args(output_dir)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    bind_source_acceleration_authority(args)
    shared = physical._bind_shared_contract(args)
    validate_shared_contract_preflight(args, shared)
    started = time.monotonic()
    partial = replay.run_replay_engine(args)
    wall_seconds = time.monotonic() - started
    checkpoint_authority = getattr(
        args,
        "task2_semantic_checkpoint_authority",
        None,
    )
    _validate_progress(partial, checkpoint_authority)

    outputs = replay.output_paths(args.output_prefix)
    surfaces = []
    for role in physical.MATERIALIZED_SURFACE_ROLES:
        path = outputs[role]
        if not path.is_file() or path.is_symlink():
            raise SemanticSliceRejected(f"semantic_slice_surface_missing:{role}")
        surfaces.append({"role": role, **_scan_jsonl(path)})
    summary_path = outputs["partial_summary"]
    semantic_outputs = replay.semantic_output_paths(args.output_prefix)
    direct_manifest = write_direct_semantic_source_manifest(
        namespace=namespace,
        outputs=outputs,
        semantic_outputs=semantic_outputs,
        runtime_input_contract_root_sha256=str(
            runtime_contract.get("contract_root_sha256")
        ),
        shared_execution_contract_digest_sha256=str(
            shared.get("shared_execution_contract_digest_sha256")
        ),
    )
    semantic_manifest = semantic_outputs["semantic_source_manifest"]

    core = {
        "schema": "gtos.replay_acceleration.task2_semantic_slice_execution.v1",
        "status": "TASK2_ACCELERATED_JAN1_2_COMPLETE",
        "namespace": str(namespace),
        "output_prefix": args.output_prefix,
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": END_DAY,
            "day_count": 2,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id": "S0R0",
            "symbol_count": len(replay.active_replay_symbol_universe(None)),
            "chunk_size": 1,
        },
        "task2_semantic_checkpoint_authority": checkpoint_authority,
        "source_plan_digest_sha256": EXPECTED_SOURCE_PLAN_DIGEST,
        "arm_fingerprint_sha256": EXPECTED_ARM_FINGERPRINT,
        "runtime_input_contract_root_sha256": runtime_contract.get(
            "contract_root_sha256"
        ),
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "economic_execution_contract_digest_sha256": (
            EXPECTED_ECONOMIC_CONTRACT_DIGEST
        ),
        "implementation_authority": {
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                text=True,
            ).strip(),
            "semantic_slice_runner_sha256": _sha256(Path(__file__).resolve()),
            "replay_engine_sha256": _sha256(Path(replay.__file__).resolve()),
            "timewarp_reducer_sha256": _sha256(
                ROOT
                / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
            ),
            "selector_v4_sha256": _sha256(ROOT / "src/components/selector_v4.py"),
        },
        "partial_summary": {
            "path": str(summary_path),
            "bytes": summary_path.stat().st_size,
            "sha256": _sha256(summary_path),
        },
        "proof_transport": "bounded_direct_hot_files",
        "streaming_proof_archive_used": False,
        "semantic_source_manifest": {
            "path": str(semantic_manifest),
            "bytes": semantic_manifest.stat().st_size,
            "sha256": _sha256(semantic_manifest),
            "source_manifest_root_sha256": direct_manifest[
                "source_manifest_root_sha256"
            ],
        },
        "persisted_surfaces": surfaces,
        "measurement": {
            "wall_seconds": wall_seconds,
            "evidence_class": "corrected_accelerated_semantic_acceptance_slice",
        },
        "typed_partition_cache_used": True,
        "sparse_tick_cache_used": True,
        "policy_execution_entered": True,
        "physical_reference_route_invoked": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    replay.atomic_write_json(namespace / RECEIPT_NAME, receipt)
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh namespace below the sealed attempt-5 root.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_semantic_slice(args.output_dir)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
