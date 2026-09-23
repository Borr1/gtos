#!/usr/bin/env python3
"""Profile the accepted post-Task-7 Jan 1-2 dense replay without tracing drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import threading
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_task2_semantic_slice_runner as semantic,
)
from src.research_infra import (
    replay_acceleration_task6_prepared_pack_runner as task6,
)
from src.research_infra import (
    replay_acceleration_task7_isolated_runner as task7,
)
from src.research_infra import (
    replay_acceleration_task3_exact_cache_acceptance as task3_acceptance,
)


ROOT = Path(__file__).resolve().parents[2]
DAY1 = "2026-01-01"
DAY2 = "2026-01-02"
JAN2_PACK_ROOT_SHA256 = (
    "e6bdabadc8deb4ee1e64f4d994010007fac1e8114e886e4b3e95bbd4a1bb8a62"
)
TASK8_PACK_ROOTS = {
    ("development", DAY1, DAY1): task7.TASK6_JAN1_PACK_ROOT_SHA256,
    ("development", DAY2, DAY2): JAN2_PACK_ROOT_SHA256,
}
PROFILE_SCHEMA = "gtos.replay_acceleration.task8_sampling_profile.v1"
PROFILE_STATUS = "TASK8_POST_TASK7_DENSE_PROFILE_COMPLETE"
PROFILE_RECEIPT_NAME = "TASK8_DENSE_SAMPLING_PROFILE.json"
PARTIAL_PROFILE_RECEIPT_NAME = "TASK8_DENSE_SAMPLING_PROFILE.partial.json"
COLLAPSED_STACK_NAME = "TASK8_DENSE_SAMPLING_PROFILE.collapsed"
STAGE_PROFILE_SCHEMA = "gtos.replay_acceleration.task8_stage_profile.v1"
STAGE_PROFILE_STATUS = "TASK8_POST_TASK7_DENSE_STAGE_PROFILE_COMPLETE"
STAGE_PROFILE_RECEIPT_NAME = "TASK8_DENSE_STAGE_PROFILE.json"
SAMPLE_INTERVAL_SECONDS = 0.01
CHECKPOINT_INTERVAL_SECONDS = 15.0
TASK8_PARITY_SCHEMA = "gtos.replay_acceleration.task8.semantic_parity.v1"
TASK8_VOLATILITY_CONTRACT_SCHEMA = (
    "gtos.replay_acceleration.task8.runtime_clock_closure.v1"
)
TASK8_SEMANTIC_EXACT_ROLES = frozenset(task7.ROLE_SUFFIXES) - {
    "order",
    "semantic_order_preimage",
}
TASK8_ORDER_DERIVED_HASH_PROOFS = {
    (
        "broker_order_lifecycle_capture_v4_packet/pre_order_capture_contract/"
        "execution_manager_packet_hash"
    ): "PREIMAGE"
}


class Task8ProfileRejected(RuntimeError):
    """The Task 8 production-real profiling route failed closed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=512)
def _render_profile_path(filename: str) -> str:
    path = Path(filename)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return str(path)


def _frame_label(filename: str, function: str, lineno: int | None = None) -> str:
    rendered = _render_profile_path(filename)
    if lineno is None:
        return f"{rendered}:{function}"
    return f"{rendered}:{lineno}:{function}"


class SamplingProfiler:
    """Low-overhead Python stack sampler for one target thread."""

    def __init__(
        self,
        *,
        target_thread_id: int,
        interval_seconds: float = SAMPLE_INTERVAL_SECONDS,
        checkpoint_path: Path | None = None,
        checkpoint_interval_seconds: float = CHECKPOINT_INTERVAL_SECONDS,
    ) -> None:
        if interval_seconds <= 0.0:
            raise ValueError("task8_sampling_interval_invalid")
        if checkpoint_path is not None and checkpoint_interval_seconds <= 0.0:
            raise ValueError("task8_checkpoint_interval_invalid")
        self.target_thread_id = int(target_thread_id)
        self.interval_seconds = float(interval_seconds)
        self.checkpoint_path = (
            Path(checkpoint_path) if checkpoint_path is not None else None
        )
        self.checkpoint_interval_seconds = float(checkpoint_interval_seconds)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._leaf_functions: Counter[str] = Counter()
        self._leaf_lines: Counter[str] = Counter()
        self._stacks: Counter[str] = Counter()
        self._sample_count = 0
        self._missing_frame_count = 0
        self._started = 0.0
        self._stopped = 0.0
        self._checkpoint_count = 0

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("task8_sampling_profiler_already_started")
        self._started = time.monotonic()
        self._thread = threading.Thread(
            target=self._run,
            name="gtos-task8-sampling-profiler",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        next_checkpoint = self._started + self.checkpoint_interval_seconds
        while not self._stop.wait(self.interval_seconds):
            frame = sys._current_frames().get(self.target_thread_id)
            if frame is None:
                self._missing_frame_count += 1
                continue
            leaf_frame = frame
            stack: list[str] = []
            while frame is not None:
                stack.append(
                    _frame_label(
                        frame.f_code.co_filename,
                        frame.f_code.co_name,
                    )
                )
                frame = frame.f_back
            stack.reverse()
            if not stack:
                self._missing_frame_count += 1
                continue
            self._leaf_functions[
                _frame_label(
                    leaf_frame.f_code.co_filename,
                    leaf_frame.f_code.co_name,
                )
            ] += 1
            self._leaf_lines[
                _frame_label(
                    leaf_frame.f_code.co_filename,
                    leaf_frame.f_code.co_name,
                    leaf_frame.f_lineno,
                )
            ] += 1
            self._stacks[";".join(stack)] += 1
            self._sample_count += 1
            now = time.monotonic()
            if self.checkpoint_path is not None and now >= next_checkpoint:
                self._write_checkpoint(now=now)
                next_checkpoint = now + self.checkpoint_interval_seconds

    def _write_checkpoint(self, *, now: float) -> None:
        if self.checkpoint_path is None:
            return
        self._checkpoint_count += 1
        core = {
            "schema": "gtos.replay_acceleration.task8_sampling_checkpoint.v1",
            "status": "TASK8_SAMPLING_PROFILE_IN_PROGRESS",
            "checkpoint_sequence": self._checkpoint_count,
            "sampling_profile": self._snapshot(
                elapsed=max(0.0, now - self._started),
                limit=200,
            ),
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "real_order_transmission_possible": False,
            "acceptance_authorized": False,
        }
        replay.atomic_write_json(
            self.checkpoint_path,
            {**core, "checkpoint_root_sha256": replay.stable_sha256(core)},
        )

    def stop(self) -> None:
        if self._thread is None:
            raise RuntimeError("task8_sampling_profiler_not_started")
        self._stop.set()
        self._thread.join(timeout=max(5.0, self.interval_seconds * 10.0))
        if self._thread.is_alive():
            raise RuntimeError("task8_sampling_profiler_stop_failed")
        self._stopped = time.monotonic()

    @staticmethod
    def _ranked(counter: Counter[str], total: int, limit: int) -> list[dict[str, Any]]:
        return [
            {
                "frame": frame,
                "samples": count,
                "sample_fraction": round(count / total, 8) if total else 0.0,
            }
            for frame, count in counter.most_common(limit)
        ]

    def _snapshot(self, *, elapsed: float, limit: int) -> dict[str, Any]:
        return {
            "schema": "gtos.replay_acceleration.python_sampling_profile.v1",
            "sampler": "sys._current_frames_target_thread",
            "target_thread_id": self.target_thread_id,
            "configured_interval_seconds": self.interval_seconds,
            "elapsed_seconds": elapsed,
            "sample_count": self._sample_count,
            "missing_frame_count": self._missing_frame_count,
            "effective_sample_interval_seconds": (
                elapsed / self._sample_count if self._sample_count else None
            ),
            "top_leaf_functions": self._ranked(
                self._leaf_functions, self._sample_count, limit
            ),
            "top_leaf_lines": self._ranked(
                self._leaf_lines, self._sample_count, limit
            ),
            "top_stacks": self._ranked(self._stacks, self._sample_count, limit),
            "complete_stack_count": len(self._stacks),
        }

    def receipt(self, *, limit: int = 200) -> dict[str, Any]:
        if self._stopped <= self._started:
            raise RuntimeError("task8_sampling_profiler_incomplete")
        elapsed = self._stopped - self._started
        return self._snapshot(elapsed=elapsed, limit=limit)

    def collapsed_bytes(self) -> bytes:
        rows = [
            f"{stack} {count}\n"
            for stack, count in sorted(self._stacks.items())
        ]
        return "".join(rows).encode("utf-8")


def task8_args(output_dir: Path) -> argparse.Namespace:
    args = task6.task6_args(Path(output_dir))
    args.task2_semantic_checkpoint_after_day = None
    args.engineering_stop_after_day = DAY2
    args.build_prepared_day_pack_root = None
    args.prepared_day_pack_root = task7.TASK6_CORRECTED_PACK_ROOT
    args.prepared_day_pack_build_only = False
    args.expected_prepared_day_pack_roots = dict(TASK8_PACK_ROOTS)
    args.prepared_pack_encoding_workers = 1
    args.arm_id = "S0R0"
    args.expected_arm_fingerprint_sha256 = semantic.EXPECTED_ARM_FINGERPRINT
    args.tick_sparse_cache_root = replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    args.tick_sparse_cache_window_end_after_day = DAY2
    return args


def _day_projection(root: Path, day: str) -> dict[str, Any]:
    receipts = {
        role: task7.scan_day_jsonl(
            task7._find_role_path(Path(root), role),
            day=day,
            allow_bucket_aggregate_rows=(role == "bucket"),
        )
        for role in task7.ROLE_SUFFIXES
    }
    return task7.semantic_role_projection(receipts)


def task8_runtime_clock_closure_contract() -> dict[str, Any]:
    exclusions = [
        {
            "surface": "order",
            "path": (
                "broker_order_lifecycle_capture_v4_packet/"
                "pre_order_capture_contract/execution_manager_packet_hash"
            ),
            "value_class": "derived_hash",
            "proof": "selected_order_preimage_recomputed",
        },
        {
            "surface": "order",
            "path": "broker_order_lifecycle_capture_v4_packet/packet_hash_sha256",
            "value_class": "derived_hash",
            "proof": "lifecycle_packet_preimage_recomputed",
        },
        *[
            {
                "surface": "semantic_order_preimage_payload",
                "path": path,
                "value_class": value_class,
                "proof": proof,
            }
            for path, value_class, proof in (
                (
                    "execution_manager_packet/generated_at_utc",
                    "wall_clock_timestamp",
                    "valid_utc_runtime_envelope_only",
                ),
                (
                    "execution_manager_packet/broker_order_lifecycle_capture_v4/"
                    "generated_at_utc",
                    "wall_clock_timestamp",
                    "valid_utc_runtime_envelope_only",
                ),
                (
                    "broker_order_lifecycle_capture_v4_packet/"
                    "pre_order_capture_contract/execution_manager_packet_hash",
                    "derived_hash",
                    "selected_order_preimage_recomputed",
                ),
                (
                    "broker_order_lifecycle_capture_v4_packet/packet_hash_sha256",
                    "derived_hash",
                    "lifecycle_packet_preimage_recomputed",
                ),
            )
        ],
        *[
            {
                "surface": "semantic_order_preimage_row",
                "path": path,
                "value_class": "derived_hash",
                "proof": "canonical_parent_preimage_recomputed",
            }
            for path in (
                "final_producer_order_row_sha256",
                "owner/payload_root_sha256",
                "persisted_order_row_sha256",
                "pre_normalization_producer_order_row_sha256",
                "producer_order_row_sha256",
                "semantic_execution_manager_packet_sha256",
                "semantic_order_preimage_id",
                "sidecar_payload_sha256",
            )
        ],
        *[
            {
                "surface": "semantic_order_preimage_payload_exposure_alias",
                "path": (
                    "execution_manager_packet/scheduler_v4/packet/"
                    "exposure_snapshot/open_positions/{position_index}/metadata/"
                    + tail
                ),
                "value_class": "derived_hash",
                "proof": "exposure_identity_to_selected_order_preimage_alias",
            }
            for tail in (
                "broker_order_lifecycle_capture_v4_packet/packet_hash_sha256",
                "broker_order_lifecycle_capture_v4_packet/"
                "pre_order_capture_contract/execution_manager_packet_hash",
            )
        ],
    ]
    core = {
        "schema": TASK8_VOLATILITY_CONTRACT_SCHEMA,
        "scope": "task6_reference_vs_task8_profiled_jan1_2",
        "exclusions": exclusions,
        "broad_recursive_deletion": False,
        "result_specific_exception": False,
        "causal_or_economic_field_excluded": False,
        "meaningful_difference_allowed": False,
        "unknown_difference_allowed": False,
        "acceptance_authorized": False,
    }
    return {**core, "contract_root_sha256": replay.stable_sha256(core)}


def _task8_semantic_parity(
    *,
    namespace: Path,
    output_projection: Mapping[str, Mapping[str, Any]],
    reference_projection: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    for day in (DAY1, DAY2):
        for role in TASK8_SEMANTIC_EXACT_ROLES:
            if output_projection[day][role] != reference_projection[day][role]:
                raise Task8ProfileRejected(
                    f"task8_task6_exact_parity_mismatch:{day}:{role}"
                )
    reference_root = task7.TASK6_REFERENCE_EXECUTION_ROOT
    try:
        order = task3_acceptance.semantic.compare_role_rows(
            "order",
            task3_acceptance.semantic._role_rows(reference_root, "order"),
            task3_acceptance.semantic._role_rows(namespace, "order"),
            derived_hash_proofs=TASK8_ORDER_DERIVED_HASH_PROOFS,
        )
        preimages = task3_acceptance.compare_order_preimages(
            reference_root,
            namespace,
        )
    except (
        task3_acceptance.Task3ExactCacheRejected,
        task3_acceptance.semantic.SemanticAcceptanceError,
    ) as exc:
        raise Task8ProfileRejected(f"task8_task6_semantic_parity_mismatch:{exc}") from None
    if (
        order.get("meaningful_difference_count") != 0
        or order.get("unknown_difference_count") != 0
        or preimages.get("meaningful_difference_count") != 0
        or preimages.get("unknown_difference_count") != 0
    ):
        raise Task8ProfileRejected("task8_task6_semantic_parity_not_clean")
    return {
        "schema": TASK8_PARITY_SCHEMA,
        "status": "TASK8_PROFILED_EXECUTION_TASK6_SEMANTIC_PARITY",
        "exact_roles": sorted(TASK8_SEMANTIC_EXACT_ROLES),
        "order_semantic_comparison": order,
        "selected_order_preimage_comparison": preimages,
        "runtime_clock_closure_contract": task8_runtime_clock_closure_contract(),
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "acceptance_authorized": False,
    }


def _validate_profiled_execution(
    partial: Mapping[str, Any],
    *,
    namespace: Path,
) -> dict[str, Any]:
    progress = partial.get("progress_rows")
    checkpoints = partial.get("prepared_day_pack_checkpoints")
    if (
        not isinstance(progress, list)
        or len(progress) != 2
        or not isinstance(checkpoints, list)
        or len(checkpoints) != 2
        or [row.get("start_day") for row in progress] != [DAY1, DAY2]
        or [row.get("end_day") for row in progress] != [DAY1, DAY2]
        or partial.get("live_broker_authority") is not False
        or partial.get("broker_mutation_enabled") is not False
    ):
        raise Task8ProfileRejected("task8_profiled_execution_scope_invalid")
    expected_roots = [
        task7.TASK6_JAN1_PACK_ROOT_SHA256,
        JAN2_PACK_ROOT_SHA256,
    ]
    if any(
        checkpoint.get("pack_root_sha256") != expected_root
        or checkpoint.get("external_root_authenticated") is not True
        or checkpoint.get("broker_mutation_enabled") is not False
        or checkpoint.get("live_authority_touched") is not False
        for checkpoint, expected_root in zip(checkpoints, expected_roots)
    ):
        raise Task8ProfileRejected("task8_prepared_pack_checkpoint_invalid")
    prewarm_path = namespace / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    prewarm = json.loads(prewarm_path.read_bytes())
    task7.validate_tick_cache_superset_reuse(prewarm)
    output_projection = {
        day: _day_projection(namespace, day) for day in (DAY1, DAY2)
    }
    reference_projection = {
        day: _day_projection(task7.TASK6_REFERENCE_EXECUTION_ROOT, day)
        for day in (DAY1, DAY2)
    }
    semantic_parity = _task8_semantic_parity(
        namespace=namespace,
        output_projection=output_projection,
        reference_projection=reference_projection,
    )
    return {
        "status": "TASK8_PROFILED_EXECUTION_TASK6_SEMANTIC_PARITY",
        "days": {
            day: {
                "projection_root_sha256": replay.stable_sha256(
                    output_projection[day]
                ),
                "roles": output_projection[day],
            }
            for day in (DAY1, DAY2)
        },
        "semantic_parity": semantic_parity,
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "tick_sparse_cache_raw_source_full_hash_count": prewarm.get(
            "raw_source_full_hash_count"
        ),
        "tick_sparse_cache_sealed_reuse_count": prewarm.get(
            "sealed_cache_reuse_count"
        ),
    }


def run_task8_exact_execution(
    output_dir: Path,
    *,
    typed_cache_authority_root: Path | None = None,
    sampling_profiler: SamplingProfiler | None = None,
    stage_profiler: Any | None = None,
) -> dict[str, Any]:
    """Run and verify the exact Jan 1-2 route without requiring sampling.

    Task 8 keeps its historical private Task-6 seed by default.  Task 9 may
    instead bind a complete, independently authenticated read-only typed cache;
    the replay remains responsible for proving that cache produced the exact
    Task-6 semantics.
    """

    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise Task8ProfileRejected("task8_output_dir_must_be_new")
    args = task8_args(output_dir)
    if typed_cache_authority_root is not None:
        cache_root = Path(typed_cache_authority_root)
        if cache_root.is_symlink() or not cache_root.is_dir():
            raise Task8ProfileRejected("task8_typed_cache_authority_invalid")
        args.source_acceleration_cache_root = cache_root
    args.replay_stage_profiler = stage_profiler
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    typed_cache_seed = None
    if typed_cache_authority_root is None:
        typed_cache_seed = task7._seed_private_typed_cache(
            Path(args.source_acceleration_cache_root)
        )
    semantic.bind_source_acceleration_authority(args)
    shared = task6._bind_current_shared_contract(args)
    wall_started = time.monotonic()
    cpu_started = time.process_time()
    if sampling_profiler is not None:
        sampling_profiler.start()
    try:
        partial = replay.run_replay_engine(args)
    finally:
        if sampling_profiler is not None:
            sampling_profiler.stop()
    wall_seconds = time.monotonic() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    parity_started = time.monotonic()
    if stage_profiler is None:
        parity = _validate_profiled_execution(partial, namespace=namespace)
    else:
        with stage_profiler.stage("verification"):
            parity = _validate_profiled_execution(partial, namespace=namespace)
    parity_seconds = time.monotonic() - parity_started
    return {
        "args": args,
        "namespace": namespace,
        "runtime_contract": runtime_contract,
        "shared_contract": shared,
        "typed_cache_seed": typed_cache_seed,
        "partial": partial,
        "parity": parity,
        "engine_wall_seconds": wall_seconds,
        "engine_cpu_seconds": cpu_seconds,
        "parity_verification_seconds": parity_seconds,
    }


def run_task8_profile(output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    sampler = SamplingProfiler(
        target_thread_id=threading.get_ident(),
        interval_seconds=SAMPLE_INTERVAL_SECONDS,
        checkpoint_path=output_dir / PARTIAL_PROFILE_RECEIPT_NAME,
        checkpoint_interval_seconds=CHECKPOINT_INTERVAL_SECONDS,
    )
    execution = run_task8_exact_execution(
        output_dir,
        sampling_profiler=sampler,
    )
    namespace = Path(execution["namespace"])
    runtime_contract = execution["runtime_contract"]
    shared = execution["shared_contract"]
    typed_cache_seed = execution["typed_cache_seed"]
    partial = execution["partial"]
    parity = execution["parity"]
    wall_seconds = float(execution["engine_wall_seconds"])
    cpu_seconds = float(execution["engine_cpu_seconds"])
    collapsed_path = namespace / COLLAPSED_STACK_NAME
    collapsed_path.write_bytes(sampler.collapsed_bytes())
    sampling = sampler.receipt()
    progress = partial["progress_rows"]
    core = {
        "schema": PROFILE_SCHEMA,
        "status": PROFILE_STATUS,
        "namespace": str(namespace),
        "scope": {
            "start_day": DAY1,
            "end_day": DAY2,
            "dense_day": DAY2,
            "arm_id": "S0R0",
            "prepared_pack_roots": {
                ":".join(key): value for key, value in TASK8_PACK_ROOTS.items()
            },
        },
        "task7_baseline_commit": "d0acfa88b",
        "execution_contract": {
            "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
            "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
            "shared_execution_contract_digest_sha256": shared.get(
                "shared_execution_contract_digest_sha256"
            ),
            "runtime_input_contract_root_sha256": runtime_contract.get(
                "contract_root_sha256"
            ),
        },
        "parity": parity,
        "measurement": {
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
            "no_event_economic_hot_path_seconds": progress[0].get(
                "economic_hot_path_seconds"
            ),
            "dense_economic_hot_path_seconds": progress[1].get(
                "economic_hot_path_seconds"
            ),
            "no_event_proof_finalization_seconds": progress[0].get(
                "proof_finalization_seconds"
            ),
            "dense_proof_finalization_seconds": progress[1].get(
                "proof_finalization_seconds"
            ),
        },
        "sampling_profile": sampling,
        "sampling_checkpoint": {
            "path": str(namespace / PARTIAL_PROFILE_RECEIPT_NAME),
            "checkpoint_count": sampler._checkpoint_count,
        },
        "collapsed_stacks": {
            "path": str(collapsed_path),
            "bytes": collapsed_path.stat().st_size,
            "sha256": _sha256(collapsed_path),
        },
        "private_typed_cache_seed": typed_cache_seed,
        "policy_execution_entered": True,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "acceptance_authorized": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    receipt_path = namespace / PROFILE_RECEIPT_NAME
    replay.atomic_write_json(receipt_path, receipt)
    return receipt_path


def _compact_stage_progress(row: Mapping[str, Any]) -> dict[str, Any]:
    compact_sink = row.get("compact_event_sink")
    authority = (
        compact_sink.get("authority")
        if isinstance(compact_sink, Mapping)
        else None
    )
    if not isinstance(authority, Mapping):
        authority = {}
    summary = row.get("summary")
    if not isinstance(summary, Mapping):
        summary = {}
    return {
        "start_day": row.get("start_day"),
        "end_day": row.get("end_day"),
        "economic_hot_path_seconds": row.get("economic_hot_path_seconds"),
        "proof_finalization_seconds": row.get("proof_finalization_seconds"),
        "summary": dict(summary),
        "compact_event_authority": {
            key: authority.get(key)
            for key in (
                "authority_root_sha256",
                "manifest_sha256",
                "row_counts",
                "raw_byte_counts",
            )
        },
    }


def run_task8_stage_profile(output_dir: Path) -> Path:
    """Run exact parity with deterministic stage timing from a real module."""

    from src.research_infra import (
        replay_acceleration_progressive_benchmark as benchmark,
    )

    profiler = benchmark.ReplayStageProfiler(enabled=True)
    execution = run_task8_exact_execution(
        Path(output_dir),
        stage_profiler=profiler,
    )
    namespace = Path(execution["namespace"])
    partial = execution["partial"]
    parity = execution["parity"]
    progress = [
        _compact_stage_progress(row)
        for row in partial["progress_rows"]
    ]
    if len(progress) != 2:
        raise Task8ProfileRejected("task8_stage_profile_progress_invalid")
    no_event_total = float(progress[0]["economic_hot_path_seconds"]) + float(
        progress[0]["proof_finalization_seconds"]
    )
    dense_total = float(progress[1]["economic_hot_path_seconds"]) + float(
        progress[1]["proof_finalization_seconds"]
    )
    runtime_contract = execution["runtime_contract"]
    shared = execution["shared_contract"]
    compact_parity = {
        "status": parity.get("status"),
        "day_projection_roots": {
            day: parity.get("days", {}).get(day, {}).get(
                "projection_root_sha256"
            )
            for day in (DAY1, DAY2)
        },
        "semantic_parity_root_sha256": replay.stable_sha256(
            parity.get("semantic_parity")
        ),
        "meaningful_difference_count": parity.get(
            "meaningful_difference_count"
        ),
        "unknown_difference_count": parity.get("unknown_difference_count"),
        "tick_sparse_cache_raw_source_full_hash_count": parity.get(
            "tick_sparse_cache_raw_source_full_hash_count"
        ),
        "tick_sparse_cache_sealed_reuse_count": parity.get(
            "tick_sparse_cache_sealed_reuse_count"
        ),
        "full_parity_root_sha256": replay.stable_sha256(parity),
        "acceptance_authorized": False,
    }
    core = {
        "schema": STAGE_PROFILE_SCHEMA,
        "status": STAGE_PROFILE_STATUS,
        "namespace": str(namespace),
        "scope": {
            "start_day": DAY1,
            "end_day": DAY2,
            "dense_day": DAY2,
            "arm_id": "S0R0",
            "prepared_pack_roots": {
                ":".join(key): value for key, value in TASK8_PACK_ROOTS.items()
            },
        },
        "execution_contract": {
            "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
            "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
            "shared_execution_contract_digest_sha256": shared.get(
                "shared_execution_contract_digest_sha256"
            ),
            "runtime_input_contract_root_sha256": runtime_contract.get(
                "contract_root_sha256"
            ),
        },
        "parity": compact_parity,
        "measurement": {
            "engine_wall_seconds": float(execution["engine_wall_seconds"]),
            "engine_cpu_seconds": float(execution["engine_cpu_seconds"]),
            "parity_verification_seconds": float(
                execution["parity_verification_seconds"]
            ),
            "process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
            "no_event_economic_hot_path_seconds": progress[0][
                "economic_hot_path_seconds"
            ],
            "no_event_proof_finalization_seconds": progress[0][
                "proof_finalization_seconds"
            ],
            "no_event_total_seconds": no_event_total,
            "dense_economic_hot_path_seconds": progress[1][
                "economic_hot_path_seconds"
            ],
            "dense_proof_finalization_seconds": progress[1][
                "proof_finalization_seconds"
            ],
            "dense_total_seconds": dense_total,
        },
        "progress": progress,
        "stage_profile": profiler.to_payload(),
        "policy_execution_entered": True,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "acceptance_authorized": False,
    }
    receipt = {**core, "receipt_root_sha256": replay.stable_sha256(core)}
    receipt_path = namespace / STAGE_PROFILE_RECEIPT_NAME
    replay.atomic_write_json(receipt_path, receipt)
    return receipt_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--stage-profile",
        action="store_true",
        help="Collect deterministic engine stage timing instead of stack samples.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt_path = (
        run_task8_stage_profile(args.output_dir)
        if args.stage_profile
        else run_task8_profile(args.output_dir)
    )
    payload = json.loads(receipt_path.read_bytes())
    summary = {
        "status": payload["status"],
        "receipt": str(receipt_path),
        "receipt_root_sha256": payload["receipt_root_sha256"],
        "wall_seconds": payload["measurement"].get(
            "wall_seconds",
            payload["measurement"].get("engine_wall_seconds"),
        ),
        "dense_economic_hot_path_seconds": payload["measurement"][
            "dense_economic_hot_path_seconds"
        ],
    }
    if "sampling_profile" in payload:
        summary.update(
            {
                "sample_count": payload["sampling_profile"]["sample_count"],
                "top_leaf_functions": payload["sampling_profile"][
                    "top_leaf_functions"
                ][:20],
            }
        )
    else:
        summary["stage_profile"] = payload["stage_profile"]
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
