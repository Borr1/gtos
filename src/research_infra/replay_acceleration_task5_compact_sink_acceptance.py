#!/usr/bin/env python3
"""Accept Task 5 only through exact semantics and bounded reconstruction.

Task 5 is an enabling proof-path change, not a standalone end-to-end speedup
claim.  This verifier authenticates every compact shard, reconstructs the two
spooled roles through the canonical legacy transforms, and then applies the
accepted Task 4 semantic comparator after removing only the explicitly named
Task 5 timing/proof envelope fields.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as semantic,
)
from src.research_infra import (
    replay_acceleration_task3_exact_cache_acceptance as task3,
)
from src.research_infra import (
    replay_acceleration_task4_shared_preparation_acceptance as task4,
)
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink


SCHEMA = "gtos.replay_acceleration.task5_compact_sink_acceptance.v1"
STATUS = "TASK5_COMPACT_EVENT_SINK_EXACT_AND_BOUNDED"
TASK_NAME = "Replay-Acceleration Task 5"
LEGACY_RELATIONAL_SCHEMA = (
    "gtos.final_moonshot.broad_replay."
    "candidate_relational_materialization.v1"
)
TASK5_RELATIONAL_SCHEMA = "gtos.replay_acceleration.compact_event_relational_audit.v1"
MAX_RECONSTRUCTION_RSS_BYTES = 512 * 1024 * 1024
EXPECTED_CHECKPOINT_COUNT = 2
EXPECTED_ROLE_COUNTS = (
    {"decision": 2304, "missed": 0},
    {"decision": 2304, "missed": 8807},
)


class Task5CompactSinkAcceptanceRejected(RuntimeError):
    """Task 5 evidence or semantics failed closed."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task5CompactSinkAcceptanceRejected(code)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Task5CompactSinkAcceptanceRejected(
            f"task5_json_invalid:{Path(path).name}"
        ) from None
    _require(type(payload) is dict, f"task5_json_invalid:{Path(path).name}")
    return payload


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value * 1024 if sys.platform.startswith("linux") else value


def _legacy_jsonl_bytes(row: Mapping[str, Any]) -> bytes:
    return (json.dumps(row, sort_keys=True, default=str) + "\n").encode("utf-8")


def validate_manifest_receipt_shared_contract_binding(
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, str]:
    manifest_digest = str(
        manifest.get("shared_execution_contract_digest_sha256") or ""
    )
    receipt_digest = str(
        receipt.get("shared_execution_contract_digest_sha256") or ""
    )
    _require(
        semantic._is_sha256(manifest_digest)
        and manifest_digest == receipt_digest,
        f"task5_manifest_receipt_shared_contract_mismatch:{label}",
    )
    return {
        "label": label,
        "shared_execution_contract_digest_sha256": manifest_digest,
    }


def project_task5_summary(
    summary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate then remove the finite Task 5 non-semantic envelope."""

    projected = copy.deepcopy(dict(summary))
    checkpoints = projected.pop("compact_event_sink_checkpoints", None)
    enabled = projected.pop("compact_event_sink_enabled", None)
    progress = projected.get("progress_rows")
    _require(
        enabled is True
        and isinstance(checkpoints, list)
        and len(checkpoints) == EXPECTED_CHECKPOINT_COUNT
        and isinstance(progress, list)
        and len(progress) == EXPECTED_CHECKPOINT_COUNT,
        "task5_summary_proof_envelope_invalid",
    )
    classified: list[dict[str, Any]] = [
        {
            "path": "compact_event_sink_enabled",
            "rationale": "proof_transport_selection_only",
        },
        {
            "path": "compact_event_sink_checkpoints",
            "rationale": "authenticated_proof_transport_and_runtime_measurement",
        },
    ]
    for index, (row, checkpoint, expected_counts) in enumerate(
        zip(progress, checkpoints, EXPECTED_ROLE_COUNTS)
    ):
        _require(
            isinstance(row, dict)
            and isinstance(checkpoint, Mapping)
            and row.get("compact_event_sink") == checkpoint
            and type(row.get("economic_hot_path_seconds")) in {int, float}
            and float(row["economic_hot_path_seconds"]) > 0.0
            and type(row.get("proof_finalization_seconds")) in {int, float}
            and float(row["proof_finalization_seconds"]) > 0.0,
            f"task5_progress_proof_envelope_invalid:{index}",
        )
        authority = checkpoint.get("authority")
        _require(
            checkpoint.get("enabled") is True
            and isinstance(authority, Mapping)
            and authority.get("status") == "sealed"
            and authority.get("resident_canonical_row_count") == 0
            and isinstance(authority.get("row_counts"), Mapping)
            and all(
                int(authority["row_counts"].get(role) or 0) == count
                for role, count in expected_counts.items()
            ),
            f"task5_progress_sink_authority_invalid:{index}",
        )
        for field, rationale in (
            ("economic_hot_path_seconds", "host_runtime_measurement"),
            ("proof_finalization_seconds", "host_runtime_measurement"),
            ("compact_event_sink", "authenticated_proof_transport_envelope"),
        ):
            row.pop(field)
            classified.append(
                {"path": f"progress_rows/{index}/{field}", "rationale": rationale}
            )
        relational = row.get("candidate_relational_materialization")
        _require(
            isinstance(relational, dict) and relational.get("exact") is True,
            f"task5_incremental_relational_audit_invalid:{index}",
        )
        if relational.get("schema") == TASK5_RELATIONAL_SCHEMA:
            _require(
                "status" not in relational,
                f"task5_incremental_relational_status_unexpected:{index}",
            )
            relational["schema"] = LEGACY_RELATIONAL_SCHEMA
            relational["status"] = "exact_candidate_equals_missed_order_trade_union"
            classified.extend(
                [
                    {
                        "path": (
                            f"progress_rows/{index}/candidate_relational_"
                            "materialization/schema"
                        ),
                        "rationale": "equivalent_incremental_audit_implementation_schema",
                    },
                    {
                        "path": (
                            f"progress_rows/{index}/candidate_relational_"
                            "materialization/status"
                        ),
                        "rationale": "legacy_exact_status_materialized_by_verifier",
                    },
                ]
            )
        else:
            _require(
                relational.get("schema") == LEGACY_RELATIONAL_SCHEMA
                and relational.get("status")
                == "exact_candidate_equals_missed_order_trade_union",
                f"task5_incremental_relational_schema_invalid:{index}",
            )
    return projected, {
        "status": "TASK5_FINITE_PROOF_ENVELOPE_VALIDATED",
        "classified_paths": classified,
        "causal_or_economic_field_excluded": False,
        "unknown_field_excluded": False,
    }


def _reconstructed_rows(
    *,
    sink: ReplayCompactEventSink,
    role: str,
    profile: str,
    split: str,
    chunk_id: str,
    factorial_arm_binding: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    ledger = sink.ledger(role)
    if role == "decision":
        compacted = replay.iter_compact_asof_decision_rows(ledger)
        row_type = "asof_decision"
    elif role == "missed":
        ledger.set_materialization_transform(
            lambda row: replay.normalize_replay_quality_fields(
                row,
                row_type="missed_opportunity",
            )
        )
        compacted = replay.iter_compact_missed_opportunity_rows(ledger)
        row_type = "missed_opportunity"
    else:
        raise Task5CompactSinkAcceptanceRejected(
            f"task5_reconstruction_role_invalid:{role}"
        )
    return replay.iter_annotated_rows(
        compacted,
        profile=profile,
        split=split,
        chunk_id=chunk_id,
        row_type=row_type,
        factorial_arm_binding=factorial_arm_binding,
    )


def validate_sink_reconstruction(
    accelerated_root: Path,
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Reopen every shard and hash exact canonical reconstructed output."""

    checkpoints = summary.get("compact_event_sink_checkpoints")
    binding = summary.get("b7_5_selection_sizing_factorial_arm_binding")
    _require(
        isinstance(checkpoints, list)
        and len(checkpoints) == EXPECTED_CHECKPOINT_COUNT
        and isinstance(binding, Mapping)
        and binding.get("valid") is True
        and binding.get("arm_id") == "S0R0",
        "task5_reconstruction_inputs_invalid",
    )
    hashers = {role: hashlib.sha256() for role in ("decision", "missed")}
    counts = {role: 0 for role in hashers}
    started = time.perf_counter()
    checkpoint_proofs = []
    for index, (checkpoint, expected_counts) in enumerate(
        zip(checkpoints, EXPECTED_ROLE_COUNTS)
    ):
        _require(isinstance(checkpoint, Mapping), "task5_checkpoint_invalid")
        authority = checkpoint.get("authority")
        _require(isinstance(authority, Mapping), "task5_checkpoint_invalid")
        root = Path(str(authority.get("root") or ""))
        sink = ReplayCompactEventSink.open_sealed(
            root=root,
            expected_authority_root_sha256=str(
                authority.get("authority_root_sha256") or ""
            ),
        )
        reopened = sink.seal()
        declared = dict(authority)
        declared.pop("root", None)
        _require(
            semantic.canonical_bytes(reopened) == semantic.canonical_bytes(declared),
            f"task5_checkpoint_authority_mismatch:{index}",
        )
        chunk_id = str(checkpoint.get("chunk_id") or "")
        profile = str(checkpoint.get("profile") or "")
        split = str(checkpoint.get("split") or "")
        _require(
            chunk_id
            == f"{profile}:{split}:2026-01-0{index + 1}:2026-01-0{index + 1}",
            f"task5_checkpoint_chronology_invalid:{index}",
        )
        observed_counts = {}
        for role in ("decision", "missed"):
            role_count = 0
            for row in _reconstructed_rows(
                sink=sink,
                role=role,
                profile=profile,
                split=split,
                chunk_id=chunk_id,
                factorial_arm_binding=binding,
            ):
                hashers[role].update(_legacy_jsonl_bytes(row))
                counts[role] += 1
                role_count += 1
            observed_counts[role] = role_count
        _require(
            observed_counts == expected_counts,
            f"task5_checkpoint_reconstruction_count_invalid:{index}",
        )
        checkpoint_proofs.append(
            {
                "index": index,
                "chunk_id": chunk_id,
                "authority_root_sha256": authority["authority_root_sha256"],
                "manifest_sha256": reopened["manifest_sha256"],
                "row_counts": observed_counts,
                "max_shard_bytes": int(reopened["max_shard_bytes"]),
                "max_raw_event_bytes": int(sink.max_raw_event_bytes),
                "legacy_manifest_consumer_bound_applied": (
                    "max_raw_event_bytes" not in reopened
                ),
            }
        )
    elapsed = time.perf_counter() - started
    role_proofs = []
    for role in ("decision", "missed"):
        path = semantic._role_path(accelerated_root, role)
        observed_sha = hashers[role].hexdigest()
        expected_sha = semantic.file_sha256(path)
        _require(
            observed_sha == expected_sha,
            f"task5_reconstructed_{role}_file_mismatch",
        )
        role_proofs.append(
            {
                "role": role,
                "status": "BYTE_EXACT_RECONSTRUCTION",
                "rows": counts[role],
                "bytes": path.stat().st_size,
                "sha256": observed_sha,
            }
        )
    peak_rss = _peak_rss_bytes()
    _require(
        peak_rss <= MAX_RECONSTRUCTION_RSS_BYTES,
        "task5_reconstruction_rss_cap_exceeded",
    )
    return {
        "status": "TASK5_COMPACT_SHARDS_AUTHENTICATED_AND_RECONSTRUCTED_EXACT",
        "elapsed_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "peak_rss_cap_bytes": MAX_RECONSTRUCTION_RSS_BYTES,
        "resident_canonical_row_count": 0,
        "checkpoint_proofs": checkpoint_proofs,
        "role_proofs": role_proofs,
    }


def run_acceptance(reference_root: Path, accelerated_root: Path) -> dict[str, Any]:
    reference_root = Path(os.path.abspath(reference_root))
    accelerated_root = Path(os.path.abspath(accelerated_root))
    _require(reference_root != accelerated_root, "task5_roots_not_distinct")
    reference_identity = semantic._fresh_execution_identity(reference_root)
    accelerated_identity = semantic._fresh_execution_identity(accelerated_root)
    reference_manifest = semantic.validate_semantic_source_manifest(reference_root)
    accelerated_manifest = semantic.validate_semantic_source_manifest(accelerated_root)
    reference_receipt = _load_json(
        reference_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
    )
    accelerated_receipt = _load_json(
        accelerated_root / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
    )
    manifest_receipt_bindings = [
        validate_manifest_receipt_shared_contract_binding(
            reference_manifest,
            reference_receipt,
            label="reference",
        ),
        validate_manifest_receipt_shared_contract_binding(
            accelerated_manifest,
            accelerated_receipt,
            label="accelerated",
        ),
    ]
    for field in (
        "source_plan_digest_sha256",
        "arm_fingerprint_sha256",
        "economic_execution_contract_digest_sha256",
        "runtime_input_contract_root_sha256",
    ):
        _require(
            reference_receipt.get(field) == accelerated_receipt.get(field),
            f"task5_execution_contract_mismatch:{field}",
        )
    _require(
        reference_receipt.get("broker_live_authority") is False
        and accelerated_receipt.get("broker_live_authority") is False
        and reference_receipt.get("broker_mutation_enabled") is False
        and accelerated_receipt.get("broker_mutation_enabled") is False,
        "task5_broker_authority_open",
    )

    reference_summary = _load_json(
        reference_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    accelerated_summary = _load_json(
        accelerated_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    # Measure the compact reconstruction before the legacy semantic comparator,
    # whose independent diff bookkeeping is intentionally outside this cap.
    reconstruction = validate_sink_reconstruction(
        accelerated_root,
        accelerated_summary,
    )

    role_proof = {
        "broker_order_lifecycle_capture_v4_packet/pre_order_capture_contract/"
        "execution_manager_packet_hash": "PREIMAGE"
    }
    role_comparisons = []
    for role in semantic.ROLE_SUFFIXES:
        try:
            role_comparisons.append(
                semantic.compare_role_rows(
                    role,
                    semantic._role_rows(reference_root, role),
                    semantic._role_rows(accelerated_root, role),
                    derived_hash_proofs=role_proof,
                )
            )
        except semantic.SemanticAcceptanceError as exc:
            raise Task5CompactSinkAcceptanceRejected(
                f"task5_role_semantic_mismatch:{role}:{exc}"
            ) from None

    projected_summary, proof_projection = project_task5_summary(
        accelerated_summary
    )
    try:
        summary_comparison, cache_audit, implementation_authority = (
            task3.compare_summary_with_cache_provenance(
                reference_summary,
                projected_summary,
                cache_validator=task4.validate_task4_cache_audits,
                reference_cache_validator=task4.validate_task4_cache_audits,
            )
        )
        preimages = task3.compare_order_preimages(reference_root, accelerated_root)
        exact_semantic_files = [
            task3._exact_semantic_file(
                semantic._semantic_paths(reference_root)[role],
                semantic._semantic_paths(accelerated_root)[role],
                role=role,
            )
            for role in ("candidate", "state")
        ]
        sealed_raw_tick_cache = task3.validate_sealed_tick_cache_prewarm(
            accelerated_root
        )
    except task3.Task3ExactCacheRejected as exc:
        raise Task5CompactSinkAcceptanceRejected(str(exc)) from None
    reference_wall = task3._measurement(reference_receipt)
    accelerated_wall = task3._measurement(accelerated_receipt)
    core = {
        "schema": SCHEMA,
        "status": STATUS,
        "task": TASK_NAME,
        "acceptance_authorized": False,
        "reference_execution": reference_identity,
        "accelerated_execution": accelerated_identity,
        "semantic_source_manifests": {
            "reference": reference_manifest,
            "accelerated": accelerated_manifest,
        },
        "semantic_manifest_receipt_shared_contract_bindings": (
            manifest_receipt_bindings
        ),
        "execution_contract": {
            field: reference_receipt[field]
            for field in (
                "source_plan_digest_sha256",
                "arm_fingerprint_sha256",
                "economic_execution_contract_digest_sha256",
                "runtime_input_contract_root_sha256",
            )
        },
        "semantic_projection": proof_projection,
        "role_comparisons": role_comparisons,
        "order_preimage_comparison": preimages,
        "exact_semantic_files": exact_semantic_files,
        "summary_semantics": summary_comparison,
        "campaign_exact_cache": cache_audit,
        "accelerator_implementation_authority": implementation_authority,
        "sealed_raw_tick_cache_precondition": sealed_raw_tick_cache,
        "compact_sink_reconstruction": reconstruction,
        "performance": {
            "reference_wall_seconds": reference_wall,
            "task5_pre_streaming_finalization_wall_seconds": accelerated_wall,
            "task5_pre_streaming_finalization_slower_seconds": (
                accelerated_wall - reference_wall
            ),
            "standalone_end_to_end_speedup_claimed": False,
            "standalone_performance_disposition": (
                "REJECTED_AS_STANDALONE_SPEEDUP_ENABLING_MECHANISM_CARRIED_FORWARD"
            ),
            "final_end_to_end_acceptance_deferred_to_task9": True,
        },
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "causal_or_economic_field_normalized": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    return {**core, "receipt_root_sha256": semantic.canonical_sha256(core)}


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    if path.exists() or path.is_symlink():
        raise Task5CompactSinkAcceptanceRejected("task5_output_must_be_new")
    path.parent.mkdir(parents=True, exist_ok=True)
    semantic.atomic_write_json(path, payload)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--accelerated-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_acceptance(args.reference_root, args.accelerated_root)
    atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
