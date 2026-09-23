from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_partial_golden_verifier import (
    PartialGoldenVerificationError,
    verify_partial_golden_manifest,
)


AMENDMENT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_postseal_namespace_amendment.v1"
)
AMENDMENT_GATE = "POST_SEAL_NAMESPACE_AMENDMENT_PROSPECTIVELY_SEALED"
MANIFEST_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
MANIFEST_GATE = "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
BLOCKER_SCHEMA = (
    "gtos.replay_acceleration."
    "post_recovery_legacy_namespace_mismatch_blocker.v1"
)
TOMBSTONE_SCHEMA = (
    "gtos.final_moonshot.broad_live_as_if_replay_harness."
    "interrupted_summary.v1"
)
TOMBSTONE_STATUS = "interrupted_partial_not_final_proof"
TOMBSTONE_SEMANTICS = (
    "parseable tombstone generated from the last completed chunk; "
    "not a completed broad replay proof"
)


class PostSealAmendmentError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PostSealAmendmentError(code)


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _compact_root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)[:-1]).hexdigest()


def _file_digest(path: Path) -> str:
    state = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            state.update(block)
    return state.hexdigest()


def _load_mapping(path: Path, code: str) -> tuple[bytes, Mapping[str, Any]]:
    _require(path.is_file() and not path.is_symlink(), f"{code}_missing")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PostSealAmendmentError(f"{code}_invalid_json") from exc
    _require(isinstance(value, Mapping), f"{code}_not_mapping")
    return raw, value


def _validate_manifest(
    manifest_path: Path, *, git_root: Path
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    raw, manifest = _load_mapping(manifest_path, "manifest")
    namespace = manifest.get("namespace")
    _require(isinstance(namespace, Mapping), "manifest_namespace_missing")
    prefix = str(namespace.get("output_prefix") or "")
    _require(prefix, "manifest_namespace_missing")
    tombstone_name = f"{prefix}_SUMMARY.json"
    try:
        verification = verify_partial_golden_manifest(
            manifest_path,
            git_root=git_root,
            allowed_namespace_additions=(tombstone_name,),
        )
    except (PartialGoldenVerificationError, OSError, ValueError) as exc:
        raise PostSealAmendmentError(
            "manifest_independent_verification_failed"
        ) from exc
    _require(
        hashlib.sha256(raw).hexdigest() == verification.get("manifest_sha256"),
        "manifest_changed_after_verification",
    )
    return manifest, verification


def _validate_blocker(
    blocker_path: Path, manifest: Mapping[str, Any]
) -> Mapping[str, Any]:
    _raw, blocker = _load_mapping(blocker_path, "blocker")
    _require(blocker.get("schema") == BLOCKER_SCHEMA, "blocker_schema_mismatch")
    projection = dict(blocker)
    projection.pop("receipt_root_sha256", None)
    _require(
        blocker.get("receipt_root_sha256") == _compact_root(projection),
        "blocker_self_root_mismatch",
    )
    _require(
        blocker.get("route_verdict") == "HUMAN_OR_EXTERNAL_BLOCKER",
        "blocker_route_verdict_mismatch",
    )
    authority = blocker.get("authority_state")
    _require(isinstance(authority, Mapping), "blocker_authority_missing")
    for key in (
        "manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
    ):
        _require(
            authority.get(key) == manifest.get(key),
            f"blocker_authority_mismatch:{key}",
        )
    mismatch = blocker.get("namespace_mismatch")
    _require(isinstance(mismatch, Mapping), "blocker_namespace_mismatch_missing")
    _require(mismatch.get("missing_file_count") == 0, "blocker_missing_files_present")
    _require(
        mismatch.get("unexpected_file_count") == 1,
        "blocker_unexpected_file_count_mismatch",
    )
    return blocker


def _surface_projection(
    manifest: Mapping[str, Any], namespace: Path
) -> tuple[dict[str, int], list[str]]:
    role_bytes: dict[str, int] = {}
    names: list[str] = []
    for row in manifest["persisted_result_surfaces"]:
        _require(isinstance(row, Mapping), "manifest_surface_invalid")
        role = str(row.get("role") or "")
        name = str(row.get("name") or "")
        byte_count = row.get("bytes")
        _require(role and role not in role_bytes, "manifest_surface_role_duplicate")
        _require(name and name not in names, "manifest_surface_name_duplicate")
        _require(
            isinstance(byte_count, int) and not isinstance(byte_count, bool),
            f"manifest_surface_bytes_invalid:{role}",
        )
        path = namespace / name
        _require(path.is_file() and not path.is_symlink(), f"sealed_surface_missing:{role}")
        _require(path.stat().st_size == byte_count, f"sealed_surface_size_mismatch:{role}")
        _require(_file_digest(path) == row.get("sha256"), f"sealed_surface_hash_mismatch:{role}")
        role_bytes[role] = byte_count
        names.append(name)
    partial = manifest["partial_summary"]
    partial_name = str(partial.get("name") or "")
    partial_path = namespace / partial_name
    _require(
        partial_path.is_file() and not partial_path.is_symlink(),
        "sealed_partial_summary_missing",
    )
    _require(
        partial_path.stat().st_size == partial.get("bytes"),
        "sealed_partial_summary_size_mismatch",
    )
    _require(
        _file_digest(partial_path) == partial.get("sha256"),
        "sealed_partial_summary_hash_mismatch",
    )
    names.append(partial_name)
    return role_bytes, sorted(names)


def _tombstone_projection(
    tombstone: Mapping[str, Any], *, role_bytes: Mapping[str, int], end_day: str
) -> tuple[dict[str, int], list[str]]:
    _require(tombstone.get("schema") == TOMBSTONE_SCHEMA, "tombstone_schema_mismatch")
    _require(tombstone.get("status") == TOMBSTONE_STATUS, "tombstone_status_mismatch")
    _require(tombstone.get("interrupted_run") is True, "tombstone_interrupted_flag_mismatch")
    _require(
        tombstone.get("last_completed_end_day") == end_day,
        "tombstone_end_day_mismatch",
    )
    _require(
        tombstone.get("interrupted_summary_semantics") == TOMBSTONE_SEMANTICS,
        "tombstone_semantics_mismatch",
    )
    generated = tombstone.get("generated_at_utc")
    _require(isinstance(generated, str) and generated, "tombstone_timestamp_missing")
    ledger_bytes = tombstone.get("ledger_file_bytes_at_interrupt")
    _require(isinstance(ledger_bytes, Mapping), "tombstone_ledger_bytes_missing")
    non_null: dict[str, int] = {}
    null_roles: list[str] = []
    for raw_role, value in ledger_bytes.items():
        role = str(raw_role)
        if value is None:
            null_roles.append(role)
            continue
        _require(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0,
            f"tombstone_role_bytes_invalid:{role}",
        )
        non_null[role] = value
    _require(non_null == dict(role_bytes), "tombstone_role_bytes_mismatch")
    return non_null, sorted(null_roles)


def build_postseal_namespace_amendment(
    *,
    manifest_path: Path,
    blocker_receipt_path: Path,
    git_root: Path | None = None,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path).resolve()
    blocker_receipt_path = Path(blocker_receipt_path).resolve()
    manifest, manifest_verification = _validate_manifest(
        manifest_path,
        git_root=(git_root or Path(__file__).resolve().parents[2]),
    )
    blocker = _validate_blocker(blocker_receipt_path, manifest)
    namespace_record = manifest["namespace"]
    namespace = Path(str(namespace_record["path"])).resolve()
    prefix = str(namespace_record["output_prefix"])
    _require(namespace.is_dir(), "namespace_missing")
    role_bytes, original_names = _surface_projection(manifest, namespace)

    mismatch = blocker["namespace_mismatch"]
    unexpected = mismatch.get("unexpected_file")
    _require(isinstance(unexpected, Mapping), "blocker_unexpected_file_missing")
    tombstone_name = str(unexpected.get("filename") or "")
    _require(tombstone_name == f"{prefix}_SUMMARY.json", "tombstone_name_mismatch")
    tombstone_path = namespace / tombstone_name
    _require(
        tombstone_path.is_file() and not tombstone_path.is_symlink(),
        "tombstone_missing",
    )
    _require(
        tombstone_path.stat().st_size == unexpected.get("bytes"),
        "tombstone_size_mismatch",
    )
    _require(
        _file_digest(tombstone_path) == unexpected.get("sha256"),
        "tombstone_hash_mismatch",
    )
    _raw, tombstone = _load_mapping(tombstone_path, "tombstone")
    projected_role_bytes, null_roles = _tombstone_projection(
        tombstone,
        role_bytes=role_bytes,
        end_day=str(manifest["scope"]["end_day"]),
    )

    current_names = sorted(
        path.name
        for path in namespace.iterdir()
        if path.is_file() and path.name.startswith(prefix + "_")
    )
    accepted_names = sorted([*original_names, tombstone_name])
    _require(current_names == accepted_names, "current_namespace_inventory_mismatch")
    _require(
        mismatch.get("expected_file_count") == len(original_names),
        "blocker_expected_count_mismatch",
    )
    _require(
        mismatch.get("observed_file_count") == len(current_names),
        "blocker_observed_count_mismatch",
    )

    amendment: dict[str, Any] = {
        "schema": AMENDMENT_SCHEMA,
        "gate": AMENDMENT_GATE,
        "status": "EXACTLY_ONE_POST_SEAL_DERIVATIVE_BOUND",
        "original_golden": {
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_verification["manifest_sha256"],
            "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
            "manifest_verification_root_sha256": manifest_verification[
                "verification_root_sha256"
            ],
            "golden_root_sha256": manifest["golden_root_sha256"],
            "opaque_result_surface_root_sha256": manifest[
                "opaque_result_surface_root_sha256"
            ],
            "inventory_exact_at_seal": True,
            "sealed_file_count": len(original_names),
            "sealed_filenames": original_names,
            "sealed_role_bytes": role_bytes,
            "original_manifest_modified": False,
            "original_golden_rerooted": False,
        },
        "blocker_binding": {
            "path": str(blocker_receipt_path),
            "receipt_root_sha256": blocker["receipt_root_sha256"],
        },
        "current_namespace": {
            "path": str(namespace),
            "output_prefix": prefix,
            "accepted_file_count": len(accepted_names),
            "accepted_filenames": accepted_names,
            "acceptance_rule": (
                "original_exact_inventory_plus_one_specifically_bound_derivative"
            ),
        },
        "derivative_tombstone": {
            "filename": tombstone_name,
            "bytes": unexpected["bytes"],
            "sha256": unexpected["sha256"],
            "schema": tombstone["schema"],
            "status": tombstone["status"],
            "interrupted_run": True,
            "generated_at_utc": tombstone["generated_at_utc"],
            "last_completed_end_day": tombstone["last_completed_end_day"],
            "interrupted_summary_semantics": tombstone[
                "interrupted_summary_semantics"
            ],
            "role_bytes": projected_role_bytes,
            "null_roles": null_roles,
            "derivative_not_completed_replay_proof": True,
        },
        "fail_closed_contract": {
            "changed_sealed_file_rejected": True,
            "changed_tombstone_rejected": True,
            "missing_original_rejected": True,
            "second_extra_rejected": True,
            "role_byte_mismatch_rejected": True,
            "generic_ignore_patterns_permitted": False,
        },
        "permissions": {
            "actual_accelerated_s0r0_jan_1_7": True,
            "jan_8_31_continuation": "CONDITIONAL_ON_EXACT_REAL_ROUTE_PARITY",
            "other_arms": False,
            "broker_live_vps_deployment": False,
            "legacy_evidence_mutation": False,
        },
        "outcome_blindness": {
            "economic_values_exposed": False,
            "tombstone_values_projected_only_from_allowlisted_structural_fields": True,
            "ledger_files_verified_as_opaque_bytes": True,
        },
    }
    amendment["amendment_self_root_sha256"] = _root(amendment)
    return amendment


def write_postseal_amendment(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise PostSealAmendmentError("amendment_output_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(_canonical(value))
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blocker-receipt", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    amendment = build_postseal_namespace_amendment(
        manifest_path=args.manifest,
        blocker_receipt_path=args.blocker_receipt,
        git_root=args.git_root,
    )
    write_postseal_amendment(args.output, amendment)
    print(
        json.dumps(
            {
                "gate": amendment["gate"],
                "amendment_self_root_sha256": amendment[
                    "amendment_self_root_sha256"
                ],
                "economic_values_exposed": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
