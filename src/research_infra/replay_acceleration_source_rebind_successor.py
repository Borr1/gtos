#!/usr/bin/env python3
"""Seal a source-byte-identical replay-consumer implementation successor.

This is a source-stage-only operation.  It compares the finite source and
normalization projections of an independently verified successor bundle with
its accepted predecessor, and never enters policy or economic execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.source_bundle_consumer_rebind_authority.v1"
)
TRANSFORMATION_SCHEMA = (
    "gtos.replay_acceleration.source_bundle_consumer_rebind_transformation.v1"
)


class SourceRebindRejected(RuntimeError):
    """The proposed source-only successor was not byte/semantic equivalent."""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise SourceRebindRejected("source_rebind_noncanonical_value") from None


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _valid_root(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_canonical(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise SourceRebindRejected(code) from None
    if type(payload) is not dict or raw != canonical_bytes(payload) + b"\n":
        raise SourceRebindRejected(code)
    return payload


def verify_self_root(
    payload: Mapping[str, Any], field: str, *, code: str
) -> str:
    declared = payload.get(field)
    projection = dict(payload)
    projection.pop(field, None)
    if type(declared) is not str or declared != root(projection):
        raise SourceRebindRejected(code)
    return declared


def atomic_write_new(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    if path.exists() or path.is_symlink():
        raise SourceRebindRejected("source_rebind_output_must_be_new")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        material = canonical_bytes(dict(payload)) + b"\n"
        offset = 0
        while offset < len(material):
            written = os.write(descriptor, material[offset:])
            if written <= 0:
                raise SourceRebindRejected("source_rebind_atomic_write_failed")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _bundle_source_projection(bundle: Mapping[str, Any]) -> dict[str, Any]:
    physical_fields = (
        "index",
        "partition_id",
        "symbol",
        "physical_timeframe",
        "logical_timeframes",
        "source_path_root",
        "byte_count",
        "record_count",
        "payload_root",
        "csv_header",
        "normalized_record_count",
        "normalized_root_sha256",
        "selected_day_record_count",
        "selected_day_root_sha256",
    )
    physical = bundle.get("physical_partitions")
    logical = bundle.get("logical_partitions")
    if (
        not isinstance(physical, list)
        or not isinstance(logical, list)
        or len(physical) != 96
        or len(logical) != 120
        or any(not isinstance(row, Mapping) for row in physical)
        or any(not isinstance(row, Mapping) for row in logical)
    ):
        raise SourceRebindRejected("source_rebind_bundle_inventory_invalid")
    return {
        "schema": bundle.get("schema"),
        "status": bundle.get("status"),
        "source_stage_label": bundle.get("source_stage_label"),
        "expected_source_plan_digest_sha256": bundle.get(
            "expected_source_plan_digest_sha256"
        ),
        "selected_day": bundle.get("selected_day"),
        "cross_symbol_barrier": bundle.get("cross_symbol_barrier"),
        "policy_execution_entered": bundle.get("policy_execution_entered"),
        "postdecision_tick_classification": bundle.get(
            "postdecision_tick_classification"
        ),
        "physical_partitions": [
            {field: row.get(field) for field in physical_fields}
            for row in physical
        ],
        "logical_partitions": logical,
    }


def _selection_source_projection(selection: Mapping[str, Any]) -> dict[str, Any]:
    physical = selection.get("physical_partitions")
    if not isinstance(physical, list):
        raise SourceRebindRejected("source_rebind_selection_inventory_invalid")
    normalized_physical = []
    for raw in physical:
        if not isinstance(raw, Mapping):
            raise SourceRebindRejected("source_rebind_selection_inventory_invalid")
        row = json.loads(json.dumps(raw))
        row.pop("source_stat", None)
        identity = row.get("source_identity")
        if isinstance(identity, dict):
            identity.pop("source_stat", None)
        normalized_physical.append(row)
    return {
        "schema": selection.get("schema"),
        "status": selection.get("status"),
        "selection_rule": selection.get("selection_rule"),
        "expected_source_plan_digest_sha256": selection.get(
            "expected_source_plan_digest_sha256"
        ),
        "selected_day": selection.get("selected_day"),
        "scope": selection.get("scope"),
        "eligible_day_summaries": selection.get("eligible_day_summaries"),
        "logical_partitions": selection.get("logical_partitions"),
        "physical_partitions": normalized_physical,
        "postdecision_tick_inventory": selection.get(
            "postdecision_tick_inventory"
        ),
        "source_ledger_sha256": (
            selection.get("source_ledger", {}).get("sha256")
            if isinstance(selection.get("source_ledger"), Mapping)
            else None
        ),
        "policy_execution_entered": selection.get("policy_execution_entered"),
        "source_only": selection.get("source_only"),
    }


_SUCCESSOR_RUN_FIELDS = frozenset(
    {
        "accepted_base_commit",
        "bundle_root_sha256",
        "cache_hits",
        "command",
        "counts",
        "cross_symbol_barrier",
        "cwd",
        "disk",
        "executed_at_utc",
        "expected_mode",
        "measurements",
        "policy_execution_entered",
        "run_label",
        "run_root_sha256",
        "schema",
        "scratch",
        "selection_root_sha256",
        "slice_code_identity",
        "source_attestations",
        "source_stage_only",
        "status",
        "swap",
        "whole_replay_claim",
        "workspace",
    }
)
_VERIFIER_ENVELOPE_FIELDS = frozenset(
    {
        "command",
        "envelope_root_sha256",
        "executed_at_utc",
        "measurements",
        "orchestrator_command",
        "receipt",
        "receipt_file_sha256",
        "schema",
        "status",
    }
)
_VERIFIER_RECEIPT_FIELDS = frozenset(
    {
        "bundle_root_sha256",
        "cache_implementation_imported",
        "counts",
        "policy_execution_entered",
        "roots",
        "schema",
        "selection_root_sha256",
        "status",
        "writer_imported",
    }
)


def validate_successor_run(run: Mapping[str, Any]) -> dict[str, Any]:
    """Authenticate the complete source-only run envelope."""

    if set(run) != _SUCCESSOR_RUN_FIELDS:
        raise SourceRebindRejected("source_rebind_successor_run_invalid")
    verify_self_root(
        run,
        "run_root_sha256",
        code="source_rebind_successor_run_invalid",
    )
    counts = run.get("counts")
    barrier = run.get("cross_symbol_barrier")
    attestations = run.get("source_attestations")
    cache_hits = run.get("cache_hits")
    expected_arms = {"S0R0", "S1R0", "S0R1", "S1R1"}
    if (
        run.get("schema") != "gtos.replay_acceleration.source_stage_run.v1"
        or run.get("status") != "SOURCE_STAGE_EQUIVALENT"
        or run.get("source_stage_only") is not True
        or run.get("policy_execution_entered") is not False
        or run.get("whole_replay_claim") is not False
        or run.get("expected_mode") != "cold"
        or not _valid_root(run.get("bundle_root_sha256"))
        or not _valid_root(run.get("selection_root_sha256"))
        or not isinstance(counts, Mapping)
        or counts.get("physical_partitions") != 96
        or counts.get("logical_partitions") != 120
        or counts.get("symbols") != 24
        or not isinstance(barrier, Mapping)
        or barrier.get("physical_partition_count") != 96
        or barrier.get("logical_partition_count") != 120
        or barrier.get("symbol_count") != 24
        or barrier.get("sealed") is not True
        or barrier.get("policy_execution_entered") is not False
        or not isinstance(cache_hits, Mapping)
        or cache_hits.get("hits") != 0
        or cache_hits.get("misses") != 96
        or not isinstance(attestations, Mapping)
        or attestations.get("count") != 4
        or attestations.get("fresh_processes") is not True
        or attestations.get("policy_execution_entered") is not False
        or set(attestations.get("roots") or {}) != expected_arms
        or any(
            not _valid_root(value)
            for value in (attestations.get("roots") or {}).values()
        )
    ):
        raise SourceRebindRejected("source_rebind_successor_run_invalid")
    return {
        "run_root_sha256": run["run_root_sha256"],
        "bundle_root_sha256": run["bundle_root_sha256"],
        "selection_root_sha256": run["selection_root_sha256"],
        "source_attestation_roots": dict(attestations["roots"]),
    }


def validate_independent_verifier_envelope(
    envelope: Mapping[str, Any],
    *,
    envelope_path: Path,
) -> dict[str, Any]:
    """Authenticate the envelope and its separately persisted verifier bytes."""

    if set(envelope) != _VERIFIER_ENVELOPE_FIELDS:
        raise SourceRebindRejected("source_rebind_independent_verifier_invalid")
    verify_self_root(
        envelope,
        "envelope_root_sha256",
        code="source_rebind_independent_verifier_invalid",
    )
    receipt = envelope.get("receipt")
    receipt_path = Path(envelope_path).with_suffix(".verifier.json")
    persisted_receipt = load_canonical(
        receipt_path,
        code="source_rebind_independent_verifier_receipt_invalid",
    )
    roots = receipt.get("roots") if isinstance(receipt, Mapping) else None
    counts = receipt.get("counts") if isinstance(receipt, Mapping) else None
    if (
        envelope.get("schema")
        != "gtos.replay_acceleration.verifier_envelope.v1"
        or envelope.get("status") != "VERIFIED"
        or not isinstance(receipt, Mapping)
        or set(receipt) != _VERIFIER_RECEIPT_FIELDS
        or persisted_receipt != receipt
        or envelope.get("receipt_file_sha256") != file_sha256(receipt_path)
        or receipt.get("schema")
        != "gtos.replay_acceleration.independent_verification.v1"
        or receipt.get("status") != "VERIFIED"
        or receipt.get("policy_execution_entered") is not False
        or receipt.get("writer_imported") is not False
        or receipt.get("cache_implementation_imported") is not False
        or not _valid_root(receipt.get("bundle_root_sha256"))
        or not _valid_root(receipt.get("selection_root_sha256"))
        or counts
        != {
            "logical_partitions": 120,
            "persisted_byte_pairs_equal": 96,
            "physical_partitions": 96,
            "symbols": 24,
        }
        or not isinstance(roots, Mapping)
        or set(roots) != {"physical_recomputed", "logical_recomputed"}
        or any(not _valid_root(value) for value in roots.values())
    ):
        raise SourceRebindRejected("source_rebind_independent_verifier_invalid")
    return {
        "envelope_root_sha256": envelope["envelope_root_sha256"],
        "receipt_file_sha256": envelope["receipt_file_sha256"],
        "receipt": dict(receipt),
    }


def seal_successor(
    *,
    predecessor_bundle_path: Path,
    predecessor_selection_path: Path,
    successor_bundle_path: Path,
    successor_selection_path: Path,
    successor_run_path: Path,
    independent_verifier_path: Path,
    transformation_output: Path,
    authority_output: Path,
    reason: str = (
        "task2_account_preimage_correctness_repair_with_source_bytes_"
        "and_normalized_rows_exact"
    ),
) -> dict[str, Any]:
    if (
        type(reason) is not str
        or not reason
        or any(character not in "abcdefghijklmnopqrstuvwxyz009_" for character in reason)
    ):
        raise SourceRebindRejected("source_rebind_reason_invalid")
    predecessor_bundle = load_canonical(
        predecessor_bundle_path, code="source_rebind_predecessor_bundle_invalid"
    )
    successor_bundle = load_canonical(
        successor_bundle_path, code="source_rebind_successor_bundle_invalid"
    )
    predecessor_selection = load_canonical(
        predecessor_selection_path,
        code="source_rebind_predecessor_selection_invalid",
    )
    successor_selection = load_canonical(
        successor_selection_path,
        code="source_rebind_successor_selection_invalid",
    )
    successor_run = load_canonical(
        successor_run_path, code="source_rebind_successor_run_invalid"
    )
    verifier = load_canonical(
        independent_verifier_path,
        code="source_rebind_independent_verifier_invalid",
    )
    predecessor_bundle_root = verify_self_root(
        predecessor_bundle,
        "bundle_root_sha256",
        code="source_rebind_predecessor_bundle_invalid",
    )
    successor_bundle_root = verify_self_root(
        successor_bundle,
        "bundle_root_sha256",
        code="source_rebind_successor_bundle_invalid",
    )
    predecessor_selection_root = verify_self_root(
        predecessor_selection,
        "selection_root_sha256",
        code="source_rebind_predecessor_selection_invalid",
    )
    successor_selection_root = verify_self_root(
        successor_selection,
        "selection_root_sha256",
        code="source_rebind_successor_selection_invalid",
    )
    predecessor_bundle_projection = _bundle_source_projection(predecessor_bundle)
    successor_bundle_projection = _bundle_source_projection(successor_bundle)
    predecessor_selection_projection = _selection_source_projection(
        predecessor_selection
    )
    successor_selection_projection = _selection_source_projection(
        successor_selection
    )
    run_validation = validate_successor_run(successor_run)
    verifier_validation = validate_independent_verifier_envelope(
        verifier,
        envelope_path=independent_verifier_path,
    )
    verification_receipt = verifier_validation["receipt"]
    if (
        predecessor_bundle_projection != successor_bundle_projection
        or predecessor_selection_projection != successor_selection_projection
        or predecessor_bundle.get("accepted_cache_implementation_root")
        == successor_bundle.get("accepted_cache_implementation_root")
        or successor_bundle.get("selection_root_sha256")
        != successor_selection_root
        or run_validation.get("bundle_root_sha256") != successor_bundle_root
        or run_validation.get("selection_root_sha256")
        != successor_selection_root
        or verification_receipt.get("bundle_root_sha256")
        != successor_bundle_root
        or verification_receipt.get("selection_root_sha256")
        != successor_selection_root
    ):
        raise SourceRebindRejected("source_rebind_successor_not_equivalent")
    transformation_core = {
        "schema": TRANSFORMATION_SCHEMA,
        "status": "SOURCE_BYTES_AND_NORMALIZED_ROWS_EXACT",
        "source_plan_exact": True,
        "selected_day_exact": True,
        "source_payloads_exact": True,
        "normalized_rows_exact": True,
        "selected_day_rows_exact": True,
        "cross_symbol_barrier_exact": True,
        "physical_partition_count": 96,
        "logical_partition_count": 120,
        "unexpected_difference_count": 0,
        "predecessor_bundle_source_projection_root_sha256": root(
            predecessor_bundle_projection
        ),
        "successor_bundle_source_projection_root_sha256": root(
            successor_bundle_projection
        ),
        "predecessor_selection_source_projection_root_sha256": root(
            predecessor_selection_projection
        ),
        "successor_selection_source_projection_root_sha256": root(
            successor_selection_projection
        ),
        "independent_physical_recomputed_root_sha256": verification_receipt.get(
            "roots", {}
        ).get("physical_recomputed"),
        "independent_logical_recomputed_root_sha256": verification_receipt.get(
            "roots", {}
        ).get("logical_recomputed"),
        "policy_execution_entered": False,
        "economic_values_exposed": False,
        "broker_live_authority": False,
    }
    transformation = {
        **transformation_core,
        "transformation_root_sha256": root(transformation_core),
    }
    atomic_write_new(transformation_output, transformation)
    bundle_transform = {
        "transformation_path": str(Path(transformation_output).resolve()),
        "transformation_sha256": file_sha256(transformation_output),
        "transformation_root_sha256": transformation[
            "transformation_root_sha256"
        ],
        "source_plan_exact": True,
        "source_payloads_exact": True,
        "normalized_rows_exact": True,
        "selected_day_rows_exact": True,
        "cross_symbol_barrier_exact": True,
        "physical_partition_count": 96,
        "logical_partitions_root_sha256": root(
            successor_bundle_projection["logical_partitions"]
        ),
        "physical_source_semantics_root_sha256": root(
            successor_bundle_projection["physical_partitions"]
        ),
        "unexpected_difference_count": 0,
    }
    selection_transform = {
        "selected_day": successor_selection.get("selected_day"),
        "source_ledger_sha256": successor_selection_projection[
            "source_ledger_sha256"
        ],
        "source_plan_digest_sha256": successor_selection.get(
            "expected_source_plan_digest_sha256"
        ),
        "source_semantics_exact": True,
        "source_stat_identity_refreshed": (
            predecessor_selection_root != successor_selection_root
        ),
        "unexpected_difference_count": 0,
    }
    authority_core = {
        "schema": AUTHORITY_SCHEMA,
        "status": "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR",
        "reason": reason,
        "continuation_authorized": False,
        "policy_execution_entered": False,
        "economic_values_exposed": False,
        "broker_live_authority": False,
        "predecessor_bundle": {
            "path": str(Path(predecessor_bundle_path).resolve()),
            "sha256": file_sha256(predecessor_bundle_path),
            "bundle_root_sha256": predecessor_bundle_root,
            "implementation_root_sha256": predecessor_bundle.get(
                "accepted_cache_implementation_root"
            ),
        },
        "predecessor_selection": {
            "path": str(Path(predecessor_selection_path).resolve()),
            "sha256": file_sha256(predecessor_selection_path),
            "selection_root_sha256": predecessor_selection_root,
        },
        "successor_bundle": {
            "path": str(Path(successor_bundle_path).resolve()),
            "sha256": file_sha256(successor_bundle_path),
            "bundle_root_sha256": successor_bundle_root,
            "implementation_root_sha256": successor_bundle.get(
                "accepted_cache_implementation_root"
            ),
        },
        "successor_selection": {
            "path": str(Path(successor_selection_path).resolve()),
            "sha256": file_sha256(successor_selection_path),
            "selection_root_sha256": successor_selection_root,
        },
        "bundle_transformation": bundle_transform,
        "selection_transformation": selection_transform,
        "fresh_cold_runs": [
            {
                "path": str(Path(successor_run_path).resolve()),
                "sha256": file_sha256(successor_run_path),
                "run_root_sha256": successor_run.get("run_root_sha256"),
                "source_attestation_roots": successor_run.get(
                    "source_attestations", {}
                ).get("roots"),
            }
        ],
        "independent_verifiers": [
            {
                "path": str(Path(independent_verifier_path).resolve()),
                "sha256": file_sha256(independent_verifier_path),
                "envelope_root_sha256": verifier.get("envelope_root_sha256"),
                "receipt_file_sha256": verifier.get("receipt_file_sha256"),
                "physical_recomputed_root_sha256": verification_receipt.get(
                    "roots", {}
                ).get("physical_recomputed"),
                "logical_recomputed_root_sha256": verification_receipt.get(
                    "roots", {}
                ).get("logical_recomputed"),
            }
        ],
    }
    authority = {
        **authority_core,
        "authority_root_sha256": root(authority_core),
    }
    atomic_write_new(authority_output, authority)
    return authority


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predecessor-bundle", type=Path, required=True)
    parser.add_argument("--predecessor-selection", type=Path, required=True)
    parser.add_argument("--successor-bundle", type=Path, required=True)
    parser.add_argument("--successor-selection", type=Path, required=True)
    parser.add_argument("--successor-run", type=Path, required=True)
    parser.add_argument("--independent-verifier", type=Path, required=True)
    parser.add_argument("--transformation-output", type=Path, required=True)
    parser.add_argument("--authority-output", type=Path, required=True)
    parser.add_argument(
        "--reason",
        default=(
            "task2_account_preimage_correctness_repair_with_source_bytes_"
            "and_normalized_rows_exact"
        ),
    )
    args = parser.parse_args()
    try:
        authority = seal_successor(
            predecessor_bundle_path=args.predecessor_bundle,
            predecessor_selection_path=args.predecessor_selection,
            successor_bundle_path=args.successor_bundle,
            successor_selection_path=args.successor_selection,
            successor_run_path=args.successor_run,
            independent_verifier_path=args.independent_verifier,
            transformation_output=args.transformation_output,
            authority_output=args.authority_output,
            reason=args.reason,
        )
    except SourceRebindRejected as exc:
        print(json.dumps({"status": "REJECTED", "code": str(exc)}))
        return 2
    print(json.dumps(authority, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
