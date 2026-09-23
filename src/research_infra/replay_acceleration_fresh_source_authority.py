"""Seal a fresh, independently verified source bundle for current consumers.

Unlike the Task 4/8 successor authority, this contract does not invent a
predecessor bundle.  It admits only a cold source-only materialization whose
selection, persisted bundle, four-process attestations, independent verifier,
and current implementation identity all agree exactly.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_source_batch import (
    implementation_root as accepted_source_implementation_root,
)


AUTHORITY_SCHEMA = "gtos.replay_acceleration.fresh_current_bundle_authority.v1"
AUTHORITY_STATUS = "FRESH_CURRENT_SOURCE_BUNDLE_INDEPENDENTLY_VERIFIED"
BOUND_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.bound_fresh_current_bundle_authority.v1"
)
SELECTION_SCHEMA = "gtos.replay_acceleration.slice_selection.v1"
BUNDLE_SCHEMA = "gtos.replay_acceleration.persisted_source_bundle.v1"
RUN_SCHEMA = "gtos.replay_acceleration.source_stage_run.v1"
VERIFIER_SCHEMA = "gtos.replay_acceleration.verifier_envelope.v1"


class FreshSourceAuthorityError(ValueError):
    """Fresh source evidence failed its exact fail-closed contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "009abcdef" for char in value
    )


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FreshSourceAuthorityError(code)


def _has_symlink_component(path: Path) -> bool:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _load_json(path: Path, *, code: str) -> tuple[dict[str, Any], bytes]:
    target = Path(os.path.abspath(os.fspath(path)))
    _require(
        target.is_file() and not _has_symlink_component(target),
        code,
    )
    try:
        raw = target.read_bytes()
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FreshSourceAuthorityError(code) from exc
    _require(isinstance(payload, dict), code)
    return payload, raw


def _verify_root(payload: Mapping[str, Any], field: str, *, code: str) -> str:
    root = payload.get(field)
    projection = dict(payload)
    projection.pop(field, None)
    _require(_is_sha256(root) and root == stable_sha256(projection), code)
    return str(root)


def _authority_root(payload: Mapping[str, Any]) -> str:
    projection = dict(payload)
    projection.pop("authority_root_sha256", None)
    return stable_sha256(projection)


def build_fresh_source_authority(
    *,
    selection_path: Path,
    bundle_dir: Path,
    cold_run_path: Path,
    independent_verification_path: Path,
    expected_source_plan_digest_sha256: str,
    task9_acceptance_file_sha256: str,
    task9_acceptance_root_sha256: str,
) -> dict[str, Any]:
    """Build one authority without reading policy or outcome artifacts."""

    _require(_is_sha256(expected_source_plan_digest_sha256), "source_plan_invalid")
    _require(_is_sha256(task9_acceptance_file_sha256), "task9_file_hash_invalid")
    _require(_is_sha256(task9_acceptance_root_sha256), "task9_root_invalid")
    selection_path = Path(selection_path).resolve()
    bundle_dir = Path(bundle_dir).resolve()
    bundle_path = bundle_dir / "bundle.json"
    seal_path = bundle_dir / "SEALED"
    cold_run_path = Path(cold_run_path).resolve()
    independent_verification_path = Path(independent_verification_path).resolve()

    selection, selection_raw = _load_json(
        selection_path, code="fresh_source_selection_invalid"
    )
    bundle, bundle_raw = _load_json(bundle_path, code="fresh_source_bundle_invalid")
    cold_run, cold_raw = _load_json(
        cold_run_path, code="fresh_source_cold_run_invalid"
    )
    verification, verification_raw = _load_json(
        independent_verification_path,
        code="fresh_source_independent_verification_invalid",
    )
    selection_root = _verify_root(
        selection, "selection_root_sha256", code="fresh_source_selection_invalid"
    )
    bundle_root = _verify_root(
        bundle, "bundle_root_sha256", code="fresh_source_bundle_invalid"
    )
    cold_root = _verify_root(
        cold_run, "run_root_sha256", code="fresh_source_cold_run_invalid"
    )
    verification_root = _verify_root(
        verification,
        "envelope_root_sha256",
        code="fresh_source_independent_verification_invalid",
    )
    try:
        seal_bytes = seal_path.read_bytes()
    except OSError as exc:
        raise FreshSourceAuthorityError("fresh_source_bundle_seal_invalid") from exc
    current_implementation_root = accepted_source_implementation_root()
    attestations = cold_run.get("source_attestations")
    barrier = bundle.get("cross_symbol_barrier")
    receipt = verification.get("receipt")
    _require(
        selection.get("schema") == SELECTION_SCHEMA
        and selection.get("status") == "PROSPECTIVE_SOURCE_SELECTION_SEALED"
        and selection.get("expected_source_plan_digest_sha256")
        == expected_source_plan_digest_sha256
        and selection.get("source_only") is True
        and selection.get("policy_execution_entered") is False,
        "fresh_source_selection_scope_invalid",
    )
    _require(
        bundle.get("schema") == BUNDLE_SCHEMA
        and bundle.get("status") == "SEALED_SOURCE_EQUIVALENCE_BUNDLE"
        and bundle.get("selection_root_sha256") == selection_root
        and bundle.get("expected_source_plan_digest_sha256")
        == expected_source_plan_digest_sha256
        and bundle.get("accepted_cache_implementation_root")
        == current_implementation_root
        and bundle.get("policy_execution_entered") is False
        and seal_bytes == bundle_root.encode("ascii") + b"\n"
        and isinstance(barrier, Mapping)
        and barrier.get("sealed") is True
        and barrier.get("policy_execution_entered") is False
        and int(barrier.get("symbol_count") or 0) == 24,
        "fresh_source_bundle_scope_invalid",
    )
    _require(
        cold_run.get("schema") == RUN_SCHEMA
        and cold_run.get("status") == "SOURCE_STAGE_EQUIVALENT"
        and cold_run.get("expected_mode") == "cold"
        and cold_run.get("selection_root_sha256") == selection_root
        and cold_run.get("bundle_root_sha256") == bundle_root
        and cold_run.get("source_stage_only") is True
        and cold_run.get("whole_replay_claim") is False
        and cold_run.get("policy_execution_entered") is False
        and isinstance(attestations, Mapping)
        and int(attestations.get("count") or 0) == 4
        and attestations.get("fresh_processes") is True
        and attestations.get("policy_execution_entered") is False
        and set((attestations.get("roots") or {}).keys())
        == {"S0R0", "S1R0", "S0R1", "S1R1"},
        "fresh_source_cold_run_scope_invalid",
    )
    _require(
        verification.get("schema") == VERIFIER_SCHEMA
        and verification.get("status") == "VERIFIED"
        and isinstance(receipt, Mapping)
        and receipt.get("status") == "VERIFIED",
        "fresh_source_independent_verification_scope_invalid",
    )

    core = {
        "schema": AUTHORITY_SCHEMA,
        "status": AUTHORITY_STATUS,
        "source_plan_digest_sha256": expected_source_plan_digest_sha256,
        "selected_day": selection.get("selected_day"),
        "selection": {
            "path": str(selection_path),
            "file_sha256": hashlib.sha256(selection_raw).hexdigest(),
            "selection_root_sha256": selection_root,
        },
        "bundle": {
            "path": str(bundle_path),
            "directory": str(bundle_dir),
            "file_sha256": hashlib.sha256(bundle_raw).hexdigest(),
            "bundle_root_sha256": bundle_root,
            "accepted_cache_implementation_root": current_implementation_root,
            "slice_code_identity_root": bundle.get("slice_code_identity_root"),
            "physical_partition_count": len(bundle.get("physical_partitions") or ()),
            "logical_partition_count": len(bundle.get("logical_partitions") or ()),
        },
        "cold_materialization": {
            "path": str(cold_run_path),
            "file_sha256": hashlib.sha256(cold_raw).hexdigest(),
            "run_root_sha256": cold_root,
            "four_process_attestation_roots": copy.deepcopy(attestations["roots"]),
            "policy_execution_entered": False,
        },
        "independent_verification": {
            "path": str(independent_verification_path),
            "file_sha256": hashlib.sha256(verification_raw).hexdigest(),
            "envelope_root_sha256": verification_root,
            "receipt_file_sha256": verification.get("receipt_file_sha256"),
            "status": "VERIFIED",
        },
        "task9_accelerator_binding": {
            "acceptance_file_sha256": task9_acceptance_file_sha256,
            "acceptance_root_sha256": task9_acceptance_root_sha256,
            "current_source_implementation_root_sha256": current_implementation_root,
        },
        "fresh_current_bundle_not_predecessor_successor_relabel": True,
        "cold_materialization_required": True,
        "independent_physical_logical_verification_required": True,
        "source_only": True,
        "policy_execution_entered": False,
        "economic_values_exposed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
    }
    return {**core, "authority_root_sha256": stable_sha256(core)}


def validate_fresh_source_authority(
    *,
    authority_path: Path,
    expected_authority_file_sha256: str,
    expected_authority_root_sha256: str,
    bundle_dir: Path,
    selection_path: Path,
    expected_bundle_root_sha256: str,
    expected_source_plan_digest_sha256: str,
) -> dict[str, Any]:
    """Authenticate an existing authority and its live consumer preimages."""

    authority_path = Path(authority_path).resolve()
    authority, authority_raw = _load_json(
        authority_path, code="fresh_source_authority_invalid"
    )
    actual_root = _verify_root(
        authority,
        "authority_root_sha256",
        code="fresh_source_authority_invalid",
    )
    actual_file_sha = hashlib.sha256(authority_raw).hexdigest()
    _require(
        actual_file_sha == expected_authority_file_sha256
        and actual_root == expected_authority_root_sha256
        and authority.get("schema") == AUTHORITY_SCHEMA
        and authority.get("status") == AUTHORITY_STATUS
        and authority.get("source_plan_digest_sha256")
        == expected_source_plan_digest_sha256
        and authority.get("source_only") is True
        and authority.get("policy_execution_entered") is False
        and authority.get("economic_values_exposed") is False
        and authority.get("broker_live_authority") is False
        and authority.get("broker_mutation_enabled") is False
        and authority.get("real_order_transmission_possible") is False,
        "fresh_source_authority_identity_mismatch",
    )
    verified_bundle_dir = Path(bundle_dir).resolve()
    verified_selection_path = Path(selection_path).resolve()
    bundle_binding = authority.get("bundle")
    selection_binding = authority.get("selection")
    _require(
        isinstance(bundle_binding, Mapping)
        and isinstance(selection_binding, Mapping)
        and Path(str(bundle_binding.get("directory") or "")).resolve()
        == verified_bundle_dir
        and Path(str(selection_binding.get("path") or "")).resolve()
        == verified_selection_path
        and bundle_binding.get("bundle_root_sha256")
        == expected_bundle_root_sha256,
        "fresh_source_authority_path_binding_mismatch",
    )
    rebuilt = build_fresh_source_authority(
        selection_path=verified_selection_path,
        bundle_dir=verified_bundle_dir,
        cold_run_path=Path(str(authority["cold_materialization"]["path"])),
        independent_verification_path=Path(
            str(authority["independent_verification"]["path"])
        ),
        expected_source_plan_digest_sha256=expected_source_plan_digest_sha256,
        task9_acceptance_file_sha256=str(
            authority["task9_accelerator_binding"]["acceptance_file_sha256"]
        ),
        task9_acceptance_root_sha256=str(
            authority["task9_accelerator_binding"]["acceptance_root_sha256"]
        ),
    )
    _require(rebuilt == authority, "fresh_source_authority_evidence_drift")
    binding_core = {
        "schema": BOUND_AUTHORITY_SCHEMA,
        "authority_path": str(authority_path),
        "authority_file_sha256": actual_file_sha,
        "authority_root_sha256": actual_root,
        "authority": copy.deepcopy(authority),
        "verified_successor_bundle": {
            "path": str(verified_bundle_dir / "bundle.json"),
            "file_sha256": bundle_binding["file_sha256"],
            "bundle_root_sha256": expected_bundle_root_sha256,
            "implementation_root_sha256": bundle_binding[
                "accepted_cache_implementation_root"
            ],
        },
        "verified_successor_selection": {
            "path": str(verified_selection_path),
            "file_sha256": selection_binding["file_sha256"],
            "selection_root_sha256": selection_binding[
                "selection_root_sha256"
            ],
        },
        "source_plan_digest_sha256": expected_source_plan_digest_sha256,
        "policy_execution_entered": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    return {**binding_core, "binding_root_sha256": stable_sha256(binding_core)}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    data = canonical_json_bytes(payload) + b"\n"
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise FreshSourceAuthorityError("fresh_source_authority_write_failed")
            offset += written
        os.fsync(descriptor)
        os.fchmod(descriptor, 0o444)
    finally:
        os.close(descriptor)
    os.replace(temporary, target)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--cold-run", type=Path, required=True)
    parser.add_argument("--independent-verification", type=Path, required=True)
    parser.add_argument("--expected-source-plan-digest-sha256", required=True)
    parser.add_argument("--task9-acceptance-file-sha256", required=True)
    parser.add_argument("--task9-acceptance-root-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    authority = build_fresh_source_authority(
        selection_path=args.selection,
        bundle_dir=args.bundle_dir,
        cold_run_path=args.cold_run,
        independent_verification_path=args.independent_verification,
        expected_source_plan_digest_sha256=(
            args.expected_source_plan_digest_sha256
        ),
        task9_acceptance_file_sha256=args.task9_acceptance_file_sha256,
        task9_acceptance_root_sha256=args.task9_acceptance_root_sha256,
    )
    if args.check:
        actual, raw = _load_json(args.output, code="fresh_source_authority_invalid")
        _require(
            hashlib.sha256(raw).hexdigest() == file_sha256(args.output)
            and actual == authority,
            "fresh_source_authority_stale_or_drifted",
        )
    else:
        _require(
            not args.output.exists() and not args.output.is_symlink(),
            "fresh_source_authority_output_must_be_new",
        )
        _atomic_write_json(args.output, authority)
    print(
        json.dumps(
            {
                "status": authority["status"],
                "output": str(args.output),
                "authority_root_sha256": authority["authority_root_sha256"],
                "bundle_root_sha256": authority["bundle"]["bundle_root_sha256"],
                "source_plan_digest_sha256": authority[
                    "source_plan_digest_sha256"
                ],
                "policy_execution_entered": False,
                "broker_live_authority": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
