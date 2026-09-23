#!/usr/bin/env python3
"""Build and consume exact Jan 1-2 arm-neutral prepared-day packs."""

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
    replay_acceleration_task2_semantic_slice_runner as semantic,
)
from src.research_infra import (
    replay_acceleration_task5_compact_sink_runner as task5,
)
from src.research_infra.replay_prepared_day_pack import (
    PreparedDayPackError,
    PreparedDayPackReader,
    assert_no_factor_reads,
    seal_prepared_day_pack,
)


SCHEMA = "gtos.replay_acceleration.task6_prepared_day_pack_execution.v1"
STATUS = "TASK6_PREPARED_DAY_PACK_JAN1_2_COMPLETE"
RECEIPT_NAME = "TASK6_PREPARED_DAY_PACK_EXECUTION_RECEIPT.json"
PACK_ONLY_RECEIPT_NAME = "TASK6_FACTOR_NEUTRAL_PACK_BUILD_RECEIPT.json"
END_DAY = "2026-01-02"
EXPECTED_DAILY_RECORD_COUNTS = (96, 96)
TASK3_TICK_AUTHORITY_SUMMARY = replay.CODE_ROUTE / (
    "attempt_5_typed_sparse/"
    "TASK3_EXACT_CACHE_FINAL_WARM_JAN1_2_20260722T151017Z/"
    f"{replay.ATTEMPT5_OUTPUT_PREFIX}_PARTIAL_SUMMARY.json"
)
TASK3_TICK_AUTHORITY_SUMMARY_SHA256 = (
    "381b651eeffb75aae9edf7aeeb32e8e5d44b1aa606428cd431a170bf11a446e7"
)
TASK5_SOURCE_LEDGER = replay.CODE_ROUTE / (
    "attempt_5_typed_sparse/"
    "TASK5_COMPACT_SINK_JAN1_2_20260722T181555Z/"
    f"{replay.ATTEMPT5_OUTPUT_PREFIX}_SOURCE_UNIVERSE_LEDGER.jsonl"
)
TASK5_SOURCE_LEDGER_SHA256 = (
    "9bc4f3b19ff85e4d386dad23e424bcca9575f15e34558a78702c4e694fdd68f8"
)
TICK_SOURCE_CONTRACT_ROOT_SHA256 = (
    "a3780e9aaff859e8f019c3f6407ca7d7e40e96212e6cce393fce91f735a24f74"
)
TICK_DIAGNOSTIC_CONTRACT_ROOT_SHA256 = (
    "091e46664b62506660dd3f61459e027f543f0d97373f5fb11ef00e97e135f996"
)


class Task6PreparedPackRejected(RuntimeError):
    """The Task 6 real-route tracer failed closed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def task6_args(output_dir: Path) -> argparse.Namespace:
    output_dir = Path(output_dir)
    args = task5.task5_args(output_dir)
    args.task2_semantic_checkpoint_after_day = None
    args.engineering_stop_after_day = END_DAY
    args.expected_shared_execution_contract_sha256 = None
    args.build_prepared_day_pack_root = output_dir / "prepared-day-packs"
    args.prepared_day_pack_root = None
    args.prepared_pack_encoding_workers = 4
    args.prepared_pack_target_raw_shard_bytes = 32 * 1024 * 1024
    args.prepared_day_pack_build_only = False
    args.tick_authority_cache_summary = TASK3_TICK_AUTHORITY_SUMMARY
    args.expected_tick_authority_cache_summary_sha256 = (
        TASK3_TICK_AUTHORITY_SUMMARY_SHA256
    )
    args.tick_authority_cache_source_ledger = TASK5_SOURCE_LEDGER
    args.expected_tick_authority_cache_source_ledger_sha256 = (
        TASK5_SOURCE_LEDGER_SHA256
    )
    args.expected_tick_source_contract_root_sha256 = (
        TICK_SOURCE_CONTRACT_ROOT_SHA256
    )
    args.expected_tick_diagnostic_contract_root_sha256 = (
        TICK_DIAGNOSTIC_CONTRACT_ROOT_SHA256
    )
    return args


def task6_pack_only_args(output_dir: Path) -> argparse.Namespace:
    args = task6_args(output_dir)
    args.prepared_day_pack_build_only = True
    return args


def _bind_current_shared_contract(args: argparse.Namespace) -> dict[str, Any]:
    factorial = replay.selection_sizing_factorial_binding_from_args(args)
    profile_configs = {
        str(profile): replay.build_config(
            str(profile),
            factorial_arm_binding=factorial,
        )
        for profile in args.profiles
    }
    shared = replay.broad_replay_shared_execution_contract(
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
        profile_configs=profile_configs,
    )
    if shared.get("valid") is not True:
        raise Task6PreparedPackRejected("task6_shared_contract_invalid")
    args.expected_shared_execution_contract_sha256 = shared[
        "shared_execution_contract_digest_sha256"
    ]
    return shared


def _iter_pack_records(reader: PreparedDayPackReader):
    for row in reader.manifest["window_inventory"]:
        yield reader.next_window(
            trading_day=str(row["trading_day"]),
            decision_time_utc=str(row["decision_time_utc"]),
            window_ordinal=int(row["window_ordinal"]),
        )
    reader.finish()


def validate_factor_read_audit(build: Mapping[str, Any]) -> dict[str, Any]:
    reads = build.get("factor_reads")
    if (
        build.get("factor_reads_detected") is not False
        or not isinstance(reads, list)
        or any(not isinstance(path, str) or not path for path in reads)
    ):
        raise Task6PreparedPackRejected("task6_factor_read_audit_invalid")
    try:
        assert_no_factor_reads(reads, factor_namespace_absent=True)
    except PreparedDayPackError:
        raise Task6PreparedPackRejected(
            "task6_factor_read_audit_invalid"
        ) from None
    return {
        "factor_read_count": len(reads),
        "factor_reads_detected": False,
        "factor_namespace_absent": True,
    }


def validate_prepared_pack_builds(
    builds: Any,
    *,
    one_worker_root: Path,
) -> dict[str, Any]:
    if not isinstance(builds, list) or len(builds) != 2:
        raise Task6PreparedPackRejected("task6_pack_build_count_invalid")
    validated: list[dict[str, Any]] = []
    for index, (build, expected_count) in enumerate(
        zip(builds, EXPECTED_DAILY_RECORD_COUNTS)
    ):
        if not isinstance(build, Mapping):
            raise Task6PreparedPackRejected("task6_pack_build_invalid")
        factor_read_audit = validate_factor_read_audit(build)
        path = Path(str(build.get("path") or ""))
        reader = PreparedDayPackReader(path)
        if (
            build.get("status") != "SEALED_ARM_NEUTRAL_PREPARATION"
            or build.get("pack_root_sha256") != reader.pack_root_sha256
            or build.get("account_state_read") is not False
            or build.get("broker_state_read") is not False
            or build.get("broker_mutation_enabled") is not False
            or int(build.get("record_count") or 0) != expected_count
        ):
            raise Task6PreparedPackRejected("task6_pack_contract_invalid")
        mirror_path = (
            Path(one_worker_root)
            / str(build.get("split"))
            / f"{build['days'][0]}_{build['days'][-1]}"
        )
        mirror = seal_prepared_day_pack(
            output_dir=mirror_path,
            records=_iter_pack_records(reader),
            bindings=reader.bindings,
            encoding_worker_count=1,
            target_raw_shard_bytes=int(
                reader.manifest["target_raw_shard_bytes"]
            ),
        )
        if mirror != reader.manifest:
            raise Task6PreparedPackRejected(
                "task6_one_four_worker_pack_identity_mismatch"
            )
        validated.append(
            {
                "index": index,
                "days": list(build["days"]),
                "pack_root_sha256": reader.pack_root_sha256,
                "record_count": expected_count,
                "shard_count": len(reader.manifest["shards"]),
                "raw_bytes": int(build["raw_bytes"]),
                "compressed_bytes": int(build["compressed_bytes"]),
                "factor_read_audit": factor_read_audit,
                "preparation_wall_seconds": float(
                    build["preparation_wall_seconds"]
                ),
                "one_worker_mirror_path": str(mirror_path),
                "one_worker_four_worker_identity": True,
            }
        )
    return {
        "status": "TASK6_PACKS_AUTHENTICATED_ARM_NEUTRAL_AND_WORKER_STABLE",
        "packs": validated,
        "pack_roots": [row["pack_root_sha256"] for row in validated],
    }


def validate_prepared_packs(
    partial: Mapping[str, Any],
    *,
    one_worker_root: Path,
) -> dict[str, Any]:
    builds = partial.get("prepared_day_pack_build_receipts")
    checkpoints = partial.get("prepared_day_pack_checkpoints")
    if (
        partial.get("prepared_day_pack_enabled") is not True
        or not isinstance(checkpoints, list)
        or len(checkpoints) != 2
    ):
        raise Task6PreparedPackRejected("task6_pack_checkpoint_count_invalid")
    validated = validate_prepared_pack_builds(
        builds,
        one_worker_root=one_worker_root,
    )
    for index, (build, checkpoint, pack) in enumerate(
        zip(builds, checkpoints, validated["packs"])
    ):
        if (
            not isinstance(checkpoint, Mapping)
            or checkpoint.get("status")
            != "authenticated_before_chronological_reducer"
            or checkpoint.get("pack_root_sha256")
            != pack["pack_root_sha256"]
            or checkpoint.get("days") != build.get("days")
            or checkpoint.get("split") != build.get("split")
            or checkpoint.get("broker_mutation_enabled") is not False
            or checkpoint.get("live_authority_touched") is not False
        ):
            raise Task6PreparedPackRejected(
                f"task6_pack_checkpoint_invalid:{index}"
            )
    return validated


def _surface_receipts() -> list[dict[str, Any]]:
    outputs = replay.output_paths(replay.ATTEMPT5_OUTPUT_PREFIX)
    semantic_outputs = replay.semantic_output_paths(replay.ATTEMPT5_OUTPUT_PREFIX)
    rows = []
    for role in (
        "source",
        "decision",
        "scorecard",
        "order",
        "trade",
        "oracle",
        "missed",
        "bucket",
    ):
        path = outputs[role]
        rows.append({"role": role, **semantic._scan_jsonl(path)})
    for role in (
        "semantic_candidate",
        "semantic_state_checkpoint",
        "semantic_order_preimage",
    ):
        path = semantic_outputs[role]
        rows.append({"role": role, **semantic._scan_jsonl(path)})
    return rows


def run_task6_slice(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    args = task6_args(output_dir)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    semantic.bind_source_acceleration_authority(args)
    shared = _bind_current_shared_contract(args)
    started = time.monotonic()
    partial = replay.run_replay_engine(args)
    wall_seconds = time.monotonic() - started
    compact_validation = task5.validate_compact_event_checkpoints(partial)
    pack_validation = validate_prepared_packs(
        partial,
        one_worker_root=namespace / "prepared-day-packs-one-worker",
    )
    progress = partial.get("progress_rows")
    if not isinstance(progress, list) or len(progress) != 2:
        raise Task6PreparedPackRejected("task6_progress_invalid")
    outputs = replay.output_paths(args.output_prefix)
    summary_path = outputs["partial_summary"]
    core = {
        "schema": SCHEMA,
        "status": STATUS,
        "namespace": str(namespace),
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": END_DAY,
            "day_count": 2,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id": "S0R0",
            "chunk_size": 1,
        },
        "prepared_day_packs": pack_validation,
        "compact_event_sink": compact_validation,
        "tick_authority_cache": {
            "status": "AUTHENTICATED_REPLAY_CACHE_REUSED",
            "authority_summary_path": str(TASK3_TICK_AUTHORITY_SUMMARY),
            "authority_summary_sha256": (
                TASK3_TICK_AUTHORITY_SUMMARY_SHA256
            ),
            "source_ledger_path": str(TASK5_SOURCE_LEDGER),
            "source_ledger_sha256": TASK5_SOURCE_LEDGER_SHA256,
            "source_contract_root_sha256": (
                TICK_SOURCE_CONTRACT_ROOT_SHA256
            ),
            "diagnostic_contract_root_sha256": (
                TICK_DIAGNOSTIC_CONTRACT_ROOT_SHA256
            ),
            "raw_manifest_payload_read": False,
            "raw_tick_payload_read_for_authority": False,
        },
        "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
        "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
        "runtime_input_contract_root_sha256": runtime_contract.get(
            "contract_root_sha256"
        ),
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "implementation_authority": {
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=semantic.ROOT, text=True
            ).strip(),
            "task6_runner_sha256": _sha256(Path(__file__).resolve()),
            "prepared_pack_sha256": _sha256(
                semantic.ROOT / "src/research_infra/replay_prepared_day_pack.py"
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
        "persisted_surfaces": _surface_receipts(),
        "measurement": {
            "wall_seconds": wall_seconds,
            "preparation_wall_seconds": sum(
                float(row["preparation_wall_seconds"])
                for row in pack_validation["packs"]
            ),
            "economic_hot_path_seconds": sum(
                float(row["economic_hot_path_seconds"])
                for row in compact_validation["checkpoints"]
            ),
            "proof_finalization_seconds": sum(
                float(row["proof_finalization_seconds"])
                for row in compact_validation["checkpoints"]
            ),
            "process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
        "engineering_stop_after_day": END_DAY,
        "engineering_stop_is_acceptance_gate": False,
        "policy_execution_entered": True,
        "physical_reference_route_invoked": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    replay.atomic_write_json(namespace / RECEIPT_NAME, receipt)
    return receipt


def run_task6_pack_only(output_dir: Path) -> dict[str, Any]:
    """Build the corrected factor-free packs without entering any arm reducer."""

    output_dir = Path(output_dir)
    args = task6_pack_only_args(output_dir)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    semantic.bind_source_acceleration_authority(args)
    shared = _bind_current_shared_contract(args)
    engine_receipt = replay.run_replay_engine(args)
    if (
        engine_receipt.get("status")
        != "PREPARED_DAY_PACK_BUILD_ONLY_COMPLETE"
        or engine_receipt.get("policy_execution_entered") is not False
        or engine_receipt.get("broker_live_authority") is not False
        or engine_receipt.get("broker_mutation_enabled") is not False
    ):
        raise Task6PreparedPackRejected("task6_pack_only_engine_result_invalid")
    validation = validate_prepared_pack_builds(
        engine_receipt.get("prepared_day_pack_build_receipts"),
        one_worker_root=namespace / "prepared-day-packs-one-worker",
    )
    core = {
        "schema": "gtos.replay_acceleration.task6_factor_neutral_pack_build.v1",
        "status": "TASK6_FACTOR_NEUTRAL_PACKS_BUILT_AND_WORKER_STABLE",
        "namespace": str(namespace),
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": END_DAY,
            "day_count": 2,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id_used_only_for_full_config_construction": "S0R0",
        },
        "prepared_day_packs": validation,
        "engine_build_receipt_root_sha256": engine_receipt.get(
            "receipt_root_sha256"
        ),
        "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
        "runtime_input_contract_root_sha256": runtime_contract.get(
            "contract_root_sha256"
        ),
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "factorial_values_present_in_preparation_config": False,
        "policy_execution_entered": False,
        "physical_reference_route_invoked": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    replay.atomic_write_json(namespace / PACK_ONLY_RECEIPT_NAME, receipt)
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pack-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = (
        run_task6_pack_only(args.output_dir)
        if args.pack_only
        else run_task6_slice(args.output_dir)
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
