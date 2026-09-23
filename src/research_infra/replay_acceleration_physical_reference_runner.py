#!/usr/bin/env python3
"""Run the sealed Jan 1-7 S0R0 physical replay reference.

This entrypoint intentionally exposes no date, symbol, factor, sizing, cache,
or policy controls.  It consumes the accepted source bundle through the legacy
CSV normalizer and the accepted tick manifests through the legacy lazy reader,
then stops immediately after the Jan 7 post-cleanup checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra.replay_acceleration_contract_split import (
    split_shared_execution_contract,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE_DIR = ROOT / (
    ".hermes/evidence/task8/source-bundle-consumer-rebind-20260723-r6-task8-scoped-source-identity/"
    "materialization-current/bundle"
)
SOURCE_SELECTION = ROOT / (
    ".hermes/evidence/task4/source-bundle-selection-refresh-20260722-r5/"
    "CURRENT_SOURCE_SELECTION_RECEIPT.json"
)
SOURCE_REBIND_AUTHORITY = ROOT / (
    ".hermes/receipts/task8/source-bundle-consumer-rebind-20260723-r6-task8-scoped-source-identity/"
    "SOURCE_BUNDLE_CONSUMER_REBIND_AUTHORITY.json"
)
DECISION_CONTRACT = ROOT / (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
)
EXPECTED_SOURCE_PLAN_DIGEST = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)
EXPECTED_ARM_FINGERPRINT = (
    "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
)
EXPECTED_ECONOMIC_CONTRACT_DIGEST = (
    "7682e9d8d4448b57a9fe461f273d98df03145da8bad198b3b4aee49d5966b62d"
)
RECEIPT_NAME = "PHYSICAL_REFERENCE_EXECUTION_RECEIPT.json"
MATERIALIZED_SURFACE_ROLES = (
    "source",
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
    "bucket",
)
OMITTED_PREFIX_ROLES = (
    "candidate",
    "candidate_index",
    "packet_sidecar",
    "comparison",
    "summary",
)


class PhysicalReferenceRejected(RuntimeError):
    """The immutable physical-reference scope or result was invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonl_scan(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    byte_count = 0
    with path.open("rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                raise PhysicalReferenceRejected(
                    f"physical_reference_jsonl_framing_invalid:{path.name}"
                )
            digest.update(raw)
            byte_count += len(raw)
            rows += 1
    return {
        "name": path.name,
        "bytes": byte_count,
        "rows": rows,
        "sha256": digest.hexdigest(),
    }


def _placeholder_parse_args(output_dir: Path) -> argparse.Namespace:
    """Use the canonical parser defaults without exposing its tuning surface."""

    placeholder = "0" * 64
    return replay.parse_args(
        [
            "--output-dir",
            str(output_dir),
            "--golden-manifest",
            str(Path(__file__).resolve()),
            "--expected-golden-manifest-sha256",
            placeholder,
            "--expected-golden-manifest-self-root-sha256",
            placeholder,
            "--expected-golden-root-sha256",
            placeholder,
            "--expected-opaque-result-surface-root-sha256",
            placeholder,
            "--golden-amendment",
            str(Path(__file__).resolve()),
            "--expected-golden-amendment-sha256",
            placeholder,
            "--expected-golden-amendment-self-root-sha256",
            placeholder,
            "--expected-fixed-parity-verifier-sha256",
            placeholder,
        ]
    )


def physical_reference_args(output_dir: Path) -> argparse.Namespace:
    """Return the one immutable physical-reference invocation."""

    args = _placeholder_parse_args(Path(output_dir))
    args.start = replay.ATTEMPT5_START_DAY
    args.end = replay.ATTEMPT5_CONTRACT_END_DAY
    args.max_days = None
    args.chunk_size = 1
    args.output_prefix = replay.ATTEMPT5_OUTPUT_PREFIX
    args.profiles = [replay.PROFILE_REPAIRED]
    args.max_candidates_per_symbol_window = 0
    args.smoke_subset = False
    args.symbols = None
    args.skip_tick_source = False
    args.use_native_h1 = False
    args.omit_candidate_ledger = True
    args.omit_candidate_index_ledger = True
    args.omit_packet_sidecar_ledger = True
    args.compact_missed_ledger = True
    args.compact_decision_ledger = True
    args.compact_scorecard_ledger = True
    args.gc_between_chunks = True
    args.finalize_existing_prefix = False
    args.runtime_evidence_root = None
    args.tick_source_manifest = replay.ATTEMPT5_TICK_SOURCE_MANIFEST
    args.expected_tick_source_manifest_sha256 = (
        replay.ATTEMPT5_TICK_SOURCE_MANIFEST_SHA256
    )
    args.tick_diagnostic_manifests = [
        path for path, _sha in replay.ATTEMPT5_TICK_DIAGNOSTIC_MANIFEST_BINDINGS
    ]
    args.expected_tick_diagnostic_manifest_sha256s = [
        sha for _path, sha in replay.ATTEMPT5_TICK_DIAGNOSTIC_MANIFEST_BINDINGS
    ]
    args.source_acceleration_bundle_dir = SOURCE_BUNDLE_DIR
    args.source_acceleration_selection = SOURCE_SELECTION
    args.source_bundle_consumer_rebind_authority = SOURCE_REBIND_AUTHORITY
    args.expected_source_bundle_consumer_rebind_authority_sha256 = (
        replay.ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256
    )
    args.expected_source_bundle_consumer_rebind_authority_root_sha256 = (
        replay.ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256
    )
    args.source_acceleration_cache_root = None
    args.tick_sparse_cache_root = None
    args.expected_source_bundle_root_sha256 = (
        replay.ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256
    )
    args.expected_source_plan_digest_sha256 = EXPECTED_SOURCE_PLAN_DIGEST
    args.source_prewarm_workers = 1
    args.accepted_physical_reference = True
    args.physical_reference_checkpoint_after_day = replay.ATTEMPT5_PARITY_DAY
    args.parity_gate_after_day = None
    args.parity_gate_request = None
    args.parity_report = None
    args.parity_receipt = None
    args.stop_after_parity_gate = False
    args.streaming_proof_archive_root = None
    args.decision_contract = DECISION_CONTRACT
    args.arm_id = "S0R0"
    args.expected_arm_fingerprint_sha256 = EXPECTED_ARM_FINGERPRINT
    args.expected_economic_execution_contract_sha256 = (
        EXPECTED_ECONOMIC_CONTRACT_DIGEST
    )
    args.expected_shared_execution_contract_sha256 = None
    return args


def _bind_shared_contract(args: argparse.Namespace) -> Mapping[str, Any]:
    factorial = replay.selection_sizing_factorial_binding_from_args(args)
    runtime_inputs = replay.ultimate_package_runtime_input_contract()
    shared = replay.broad_replay_shared_execution_contract(
        profiles=args.profiles,
        active_symbols=replay.active_replay_symbol_universe(
            replay.requested_replay_symbols(args.symbols)
        ),
        execution_options=replay.broad_replay_execution_options_from_args(
            args,
            factorial_arm_binding=factorial,
        ),
        runtime_input_contract=runtime_inputs,
        factorial_arm_binding=factorial,
    )
    if shared.get("valid") is not True:
        raise PhysicalReferenceRejected("physical_reference_shared_contract_invalid")
    args.expected_shared_execution_contract_sha256 = shared[
        "shared_execution_contract_digest_sha256"
    ]
    split = split_shared_execution_contract(shared)
    if (
        split["economic_execution_contract_digest_sha256"]
        != EXPECTED_ECONOMIC_CONTRACT_DIGEST
    ):
        raise PhysicalReferenceRejected(
            "physical_reference_economic_contract_drift"
        )
    return shared


def _remove_omitted_zero_byte_outputs(outputs: Mapping[str, Path]) -> None:
    for role in OMITTED_PREFIX_ROLES:
        path = outputs[role]
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size != 0:
            raise PhysicalReferenceRejected(
                f"physical_reference_unexpected_omitted_output:{role}"
            )
        path.unlink()


def run_physical_reference(output_dir: Path) -> dict[str, Any]:
    """Execute and structurally seal one cold physical reference."""

    args = physical_reference_args(output_dir)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    shared = _bind_shared_contract(args)
    namespace = replay.configure_output_namespace(Path(output_dir))
    started = time.monotonic()
    partial = replay.run_replay_engine(args)
    wall_seconds = time.monotonic() - started
    progress = partial.get("progress_rows") or []
    if (
        partial.get("status") != "partial_in_progress_not_final_proof"
        or len(progress) != 7
        or progress[-1].get("end_day") != replay.ATTEMPT5_PARITY_DAY
        or not isinstance(
            getattr(args, "physical_source_reference_authority", None),
            Mapping,
        )
    ):
        raise PhysicalReferenceRejected(
            "physical_reference_checkpoint_result_invalid"
        )

    outputs = replay.output_paths(args.output_prefix)
    _remove_omitted_zero_byte_outputs(outputs)
    surfaces = []
    for role in MATERIALIZED_SURFACE_ROLES:
        path = outputs[role]
        if not path.is_file() or path.is_symlink():
            raise PhysicalReferenceRejected(
                f"physical_reference_surface_missing:{role}"
            )
        surfaces.append({"role": role, **_jsonl_scan(path)})
    surface_root = replay.stable_sha256(surfaces)
    partial_path = outputs["partial_summary"]
    core = {
        "schema": "gtos.replay_acceleration.physical_reference_execution.v1",
        "status": "PHYSICAL_REFERENCE_JAN1_7_COMPLETE",
        "namespace": str(namespace),
        "output_prefix": args.output_prefix,
        "scope": {
            "start_day": replay.ATTEMPT5_START_DAY,
            "end_day": replay.ATTEMPT5_PARITY_DAY,
            "day_count": 7,
            "profile": replay.PROFILE_REPAIRED,
            "arm_id": "S0R0",
        },
        "source_reference_authority": dict(
            args.physical_source_reference_authority
        ),
        "runtime_input_contract_root_sha256": runtime_contract.get(
            "contract_root_sha256"
        ),
        "shared_execution_contract_digest_sha256": shared[
            "shared_execution_contract_digest_sha256"
        ],
        "economic_execution_contract_digest_sha256": (
            EXPECTED_ECONOMIC_CONTRACT_DIGEST
        ),
        "partial_summary": {
            "name": partial_path.name,
            "bytes": partial_path.stat().st_size,
            "sha256": _sha256(partial_path),
        },
        "persisted_result_surfaces": surfaces,
        "opaque_result_surface_root_sha256": surface_root,
        "measurement": {
            "wall_seconds": wall_seconds,
            "evidence_class": "reference_execution_not_speedup_claim",
        },
        "physical_csv_legacy_normalizer": True,
        "typed_partition_cache_used": False,
        "sparse_tick_cache_used": False,
        "policy_execution_entered": True,
        "economic_values_exposed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    receipt = {
        **core,
        "receipt_root_sha256": replay.stable_sha256(core),
    }
    replay.atomic_write_json(namespace / RECEIPT_NAME, receipt)
    return receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh namespace below the sealed attempt-5 root.",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    receipt = run_physical_reference(args.output_dir)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
