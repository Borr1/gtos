#!/usr/bin/env python3
"""Run the exact Jan 1-2 tracer with Task 5 compact proof spooling enabled."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
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
from src.research_infra import (
    replay_acceleration_task2_semantic_slice_runner as semantic,
)
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink


SCHEMA = "gtos.replay_acceleration.task5_compact_sink_execution.v1"
STATUS = "TASK5_COMPACT_SINK_JAN1_2_COMPLETE"
RECEIPT_NAME = "TASK5_COMPACT_SINK_EXECUTION_RECEIPT.json"
MAX_SHARD_BYTES = 128 * 1024 * 1024
EXPECTED_ROLE_COUNTS = (
    {"decision": 2304, "missed": 0},
    {"decision": 2304, "missed": 8807},
)


class Task5CompactSinkRejected(RuntimeError):
    """The compact-sink real-route tracer failed closed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def task5_args(output_dir: Path) -> argparse.Namespace:
    args = semantic.semantic_slice_args(Path(output_dir))
    args.compact_event_sink = True
    args.compact_event_max_shard_bytes = MAX_SHARD_BYTES
    return args


def validate_compact_event_checkpoints(
    partial: Mapping[str, Any],
) -> dict[str, Any]:
    progress = partial.get("progress_rows")
    checkpoints = partial.get("compact_event_sink_checkpoints")
    if (
        not isinstance(progress, list)
        or len(progress) != 2
        or not isinstance(checkpoints, list)
        or len(checkpoints) != 2
    ):
        raise Task5CompactSinkRejected("task5_checkpoint_count_invalid")
    validated = []
    for index, (progress_row, checkpoint, expected) in enumerate(
        zip(progress, checkpoints, EXPECTED_ROLE_COUNTS)
    ):
        if not isinstance(progress_row, Mapping) or not isinstance(
            checkpoint, Mapping
        ):
            raise Task5CompactSinkRejected("task5_checkpoint_invalid")
        authority = checkpoint.get("authority")
        if (
            checkpoint.get("enabled") is not True
            or not isinstance(authority, Mapping)
            or authority.get("status") != "sealed"
            or authority.get("resident_canonical_row_count") != 0
            or int(authority.get("max_shard_bytes") or 0) != MAX_SHARD_BYTES
            or not isinstance(authority.get("row_counts"), Mapping)
            or any(
                int(authority["row_counts"].get(role) or 0) != count
                for role, count in expected.items()
            )
            or float(checkpoint.get("economic_hot_path_seconds") or 0.0) <= 0.0
            or float(checkpoint.get("proof_finalization_seconds") or 0.0) <= 0.0
        ):
            raise Task5CompactSinkRejected("task5_checkpoint_contract_invalid")
        root = Path(str(authority.get("root") or ""))
        reopened = ReplayCompactEventSink.open_sealed(
            root=root,
            expected_authority_root_sha256=str(
                authority.get("authority_root_sha256") or ""
            ),
        )
        reopened_counts = {
            role: sum(1 for _row in reopened.iter_rows(role))
            for role in ("decision", "missed")
        }
        if reopened_counts != expected:
            raise Task5CompactSinkRejected("task5_reconstruction_count_invalid")
        shards = authority.get("role_shards")
        if not isinstance(shards, Mapping) or any(
            int(shard.get("bytes") or 0) > MAX_SHARD_BYTES
            for role in ("decision", "missed")
            for shard in (shards.get(role) or ())
            if isinstance(shard, Mapping)
        ):
            raise Task5CompactSinkRejected("task5_shard_bound_invalid")
        validated.append(
            {
                "index": index,
                "chunk_id": checkpoint.get("chunk_id"),
                "economic_hot_path_seconds": checkpoint.get(
                    "economic_hot_path_seconds"
                ),
                "proof_finalization_seconds": checkpoint.get(
                    "proof_finalization_seconds"
                ),
                "authority_root_sha256": authority.get(
                    "authority_root_sha256"
                ),
                "row_counts": reopened_counts,
                "compressed_bytes": {
                    role: sum(
                        int(shard.get("bytes") or 0)
                        for shard in (shards.get(role) or ())
                        if isinstance(shard, Mapping)
                    )
                    for role in ("decision", "missed")
                },
                "raw_bytes": {
                    role: int(authority["raw_byte_counts"].get(role) or 0)
                    for role in ("decision", "missed")
                },
            }
        )
    return {
        "status": "TASK5_COMPACT_EVENT_SHARDS_REOPENED_AND_VERIFIED",
        "resident_canonical_row_count": 0,
        "checkpoints": validated,
    }


def write_task2_compatibility_receipt(
    *,
    namespace: Path,
    task5_receipt: Mapping[str, Any],
    output_prefix: str = replay.ATTEMPT5_OUTPUT_PREFIX,
) -> dict[str, Any]:
    """Bind the Task 5 run to the existing Jan 1-2 semantic verifier input."""

    core = dict(task5_receipt)
    core.pop("receipt_root_sha256", None)
    core.update(
        {
            "schema": "gtos.replay_acceleration.task2_semantic_slice_execution.v1",
            "status": "TASK2_ACCELERATED_JAN1_2_COMPLETE",
            "output_prefix": output_prefix,
            "proof_transport": "bounded_direct_hot_files",
            "streaming_proof_archive_used": False,
        }
    )
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    replay.atomic_write_json(Path(namespace) / semantic.RECEIPT_NAME, receipt)
    return receipt


def run_task5_slice(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    args = task5_args(output_dir)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    semantic.bind_source_acceleration_authority(args)
    shared = physical._bind_shared_contract(args)
    semantic.validate_shared_contract_preflight(args, shared)
    started = time.monotonic()
    partial = replay.run_replay_engine(args)
    wall_seconds = time.monotonic() - started
    checkpoint_authority = getattr(
        args,
        "task2_semantic_checkpoint_authority",
        None,
    )
    semantic._validate_progress(partial, checkpoint_authority)
    compact_validation = validate_compact_event_checkpoints(partial)

    outputs = replay.output_paths(args.output_prefix)
    semantic_outputs = replay.semantic_output_paths(args.output_prefix)
    direct_manifest = semantic.write_direct_semantic_source_manifest(
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
    persisted_surfaces = [
        {"role": role, **semantic._scan_jsonl(outputs[role])}
        for role in physical.MATERIALIZED_SURFACE_ROLES
    ]
    summary_path = outputs["partial_summary"]
    semantic_manifest = semantic_outputs["semantic_source_manifest"]
    core = {
        "schema": SCHEMA,
        "status": STATUS,
        "namespace": str(namespace),
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": semantic.END_DAY,
            "day_count": 2,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id": "S0R0",
            "chunk_size": 1,
        },
        "compact_event_sink": compact_validation,
        "task2_semantic_checkpoint_authority": checkpoint_authority,
        "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
        "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
        "runtime_input_contract_root_sha256": runtime_contract.get(
            "contract_root_sha256"
        ),
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "economic_execution_contract_digest_sha256": (
            semantic.EXPECTED_ECONOMIC_CONTRACT_DIGEST
        ),
        "implementation_authority": {
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=semantic.ROOT, text=True
            ).strip(),
            "task5_runner_sha256": _sha256(Path(__file__).resolve()),
            "compact_sink_sha256": _sha256(
                semantic.ROOT / "src/research_infra/replay_compact_event_sink.py"
            ),
            "replay_engine_sha256": _sha256(Path(replay.__file__).resolve()),
            "timewarp_reducer_sha256": _sha256(
                semantic.ROOT
                / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
            ),
        },
        "partial_summary": {
            "path": str(summary_path),
            "bytes": summary_path.stat().st_size,
            "sha256": _sha256(summary_path),
        },
        "semantic_source_manifest": {
            "path": str(semantic_manifest),
            "bytes": semantic_manifest.stat().st_size,
            "sha256": _sha256(semantic_manifest),
            "source_manifest_root_sha256": direct_manifest[
                "source_manifest_root_sha256"
            ],
        },
        "persisted_surfaces": persisted_surfaces,
        "measurement": {
            "wall_seconds": wall_seconds,
            "process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
            "economic_hot_path_seconds": sum(
                float(row["economic_hot_path_seconds"])
                for row in compact_validation["checkpoints"]
            ),
            "proof_finalization_seconds": sum(
                float(row["proof_finalization_seconds"])
                for row in compact_validation["checkpoints"]
            ),
        },
        "typed_partition_cache_used": True,
        "sparse_tick_cache_used": True,
        "policy_execution_entered": True,
        "physical_reference_route_invoked": False,
        "proof_transport": "bounded_direct_hot_files",
        "streaming_proof_archive_used": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    replay.atomic_write_json(namespace / RECEIPT_NAME, receipt)
    write_task2_compatibility_receipt(
        namespace=namespace,
        task5_receipt=receipt,
        output_prefix=args.output_prefix,
    )
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_task5_slice(args.output_dir)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
