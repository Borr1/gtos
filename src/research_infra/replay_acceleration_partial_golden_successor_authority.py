"""Recursive authority for a structurally repaired partial golden."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    RegularFileIdentity,
    immutable_write_bytes,
    open_regular_nofollow,
    read_regular_nofollow,
)
from src.research_infra.replay_acceleration_partial_golden_successor import (
    SUCCESSOR_GATE,
    SUCCESSOR_SCHEMA,
    rebind_partial_summary_source_plan_digest,
)


AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_successor_authority.v2"
)
AUTHORITY_GATE = "PARTIAL_GOLDEN_SUCCESSOR_RECURSIVELY_BOUND"
AUTHORITY_VERIFICATION_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_successor_authority_verification.v2"
)
AUTHORITY_ACCEPTED_GATE = (
    "PARTIAL_GOLDEN_SUCCESSOR_AUTHORITY_INDEPENDENTLY_ACCEPTED"
)
MANIFEST_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
AMENDMENT_SCHEMA = "gtos.replay_acceleration.partial_golden_amendment.v1"
MANIFEST_RECEIPT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_verification.v1"
)
AMENDMENT_RECEIPT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_amendment_verification.v1"
)
POSTSEAL_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_postseal_namespace_amendment.v1"
)
POSTSEAL_RECEIPT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_postseal_namespace_amendment_verification.v1"
)
LEDGER_ROLES = (
    "source",
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
    "bucket",
)


class SuccessorAuthorityError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise SuccessorAuthorityError(code)


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return _root(projection)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _absolute_lexical(path: Path, code: str) -> Path:
    text = os.fspath(path)
    lexical = Path(os.path.abspath(text))
    _require(path.is_absolute() and text == os.fspath(lexical), code)
    return lexical


def _read(path: Path, code: str) -> tuple[bytes, RegularFileIdentity]:
    try:
        return read_regular_nofollow(path, code=code)
    except ImmutableEvidenceError:
        raise SuccessorAuthorityError(code) from None


def _load(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    raw, _identity = _read(path, code)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise SuccessorAuthorityError(code) from None
    _require(type(value) is dict and raw == _canonical(value), code)
    return value, raw


def _file_record(path: Path, *, code: str) -> dict[str, Any]:
    lexical = _absolute_lexical(path, code)
    raw, identity = _read(lexical, code)
    return {
        "path": str(lexical),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "storage_device": identity.device,
        "storage_inode": identity.inode,
    }


def _compare_regular_files(
    predecessor_path: Path,
    successor_path: Path,
    *,
    code: str,
) -> dict[str, Any]:
    try:
        predecessor_fd, predecessor_identity = open_regular_nofollow(
            predecessor_path,
            code=code,
        )
        successor_fd, successor_identity = open_regular_nofollow(
            successor_path,
            code=code,
        )
    except ImmutableEvidenceError:
        try:
            os.close(predecessor_fd)
        except (NameError, OSError):
            pass
        raise SuccessorAuthorityError(code) from None
    digest = hashlib.sha256()
    bytes_read = 0
    rows = 0
    try:
        _require(predecessor_identity != successor_identity, code)
        while True:
            predecessor_chunk = os.read(predecessor_fd, 1024 * 1024)
            successor_chunk = os.read(successor_fd, 1024 * 1024)
            _require(predecessor_chunk == successor_chunk, code)
            if not predecessor_chunk:
                break
            digest.update(predecessor_chunk)
            bytes_read += len(predecessor_chunk)
            rows += predecessor_chunk.count(b"\n")
        predecessor_completed = os.fstat(predecessor_fd)
        successor_completed = os.fstat(successor_fd)
        _require(
            (
                predecessor_completed.st_dev,
                predecessor_completed.st_ino,
                predecessor_completed.st_size,
                predecessor_completed.st_mtime_ns,
                predecessor_completed.st_ctime_ns,
                predecessor_completed.st_nlink,
            )
            == (
                predecessor_identity.device,
                predecessor_identity.inode,
                predecessor_identity.size,
                predecessor_identity.mtime_ns,
                predecessor_identity.ctime_ns,
                predecessor_identity.link_count,
            )
            and (
                successor_completed.st_dev,
                successor_completed.st_ino,
                successor_completed.st_size,
                successor_completed.st_mtime_ns,
                successor_completed.st_ctime_ns,
                successor_completed.st_nlink,
            )
            == (
                successor_identity.device,
                successor_identity.inode,
                successor_identity.size,
                successor_identity.mtime_ns,
                successor_identity.ctime_ns,
                successor_identity.link_count,
            ),
            code,
        )
        return {
            "bytes": bytes_read,
            "rows": rows,
            "sha256": digest.hexdigest(),
            "distinct_storage_identity": True,
        }
    finally:
        os.close(predecessor_fd)
        os.close(successor_fd)


def _validate_manifest_core(manifest: Mapping[str, Any]) -> None:
    _require(
        manifest.get("schema") == MANIFEST_SCHEMA
        and manifest.get("gate")
        == "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
        and manifest.get("manifest_self_root_sha256")
        == _self_root(manifest, "manifest_self_root_sha256"),
        "predecessor_manifest_invalid",
    )
    current_golden_projection = {
        "scope": manifest.get("scope"),
        "contract_identity": manifest.get("contract_identity"),
        "legacy_code_authority_root_sha256": (
            manifest.get("legacy_code_authority") or {}
        ).get("authority_root_sha256"),
        "partial_summary": manifest.get("partial_summary"),
        "checkpoint_projection_root_sha256": manifest.get(
            "checkpoint_projection_root_sha256"
        ),
        "opaque_result_surface_root_sha256": manifest.get(
            "opaque_result_surface_root_sha256"
        ),
    }
    legacy_golden_projection = {
        "contract_identity": manifest.get("contract_identity"),
        "legacy_code_authority_root_sha256": (
            manifest.get("legacy_code_authority") or {}
        ).get("authority_root_sha256"),
        "partial_summary_sha256": (
            manifest.get("partial_summary") or {}
        ).get("sha256"),
        "checkpoint_projection_root_sha256": manifest.get(
            "checkpoint_projection_root_sha256"
        ),
        "opaque_result_surface_root_sha256": manifest.get(
            "opaque_result_surface_root_sha256"
        ),
    }
    _require(
        manifest.get("golden_root_sha256")
        in {
            _root(current_golden_projection),
            _root(legacy_golden_projection),
        },
        "predecessor_golden_root_invalid",
    )


def _validate_predecessor_receipts(
    *,
    manifest: Mapping[str, Any],
    manifest_receipt: Mapping[str, Any],
    amendment: Mapping[str, Any],
    amendment_receipt: Mapping[str, Any],
    postseal: Mapping[str, Any] | None,
    postseal_receipt: Mapping[str, Any] | None,
) -> None:
    _require(
        manifest_receipt.get("schema") == MANIFEST_RECEIPT_SCHEMA
        and manifest_receipt.get("gate")
        == "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED"
        and manifest_receipt.get("manifest_sha256") is not None
        and manifest_receipt.get("manifest_self_root_sha256")
        == manifest.get("manifest_self_root_sha256")
        and manifest_receipt.get("golden_root_sha256")
        == manifest.get("golden_root_sha256")
        and manifest_receipt.get("opaque_result_surface_root_sha256")
        == manifest.get("opaque_result_surface_root_sha256")
        and manifest_receipt.get("semantic_result_values_emitted") is False
        and manifest_receipt.get("legacy_evidence_modified") is False,
        "predecessor_manifest_receipt_invalid",
    )
    _require(
        amendment.get("schema") == AMENDMENT_SCHEMA
        and amendment.get("amendment_self_root_sha256")
        == _self_root(amendment, "amendment_self_root_sha256")
        and (amendment.get("partial_golden") or {}).get(
            "manifest_self_root_sha256"
        )
        == manifest.get("manifest_self_root_sha256")
        and (amendment.get("partial_golden") or {}).get("golden_root_sha256")
        == manifest.get("golden_root_sha256"),
        "predecessor_amendment_invalid",
    )
    _require(
        amendment_receipt.get("schema") == AMENDMENT_RECEIPT_SCHEMA
        and amendment_receipt.get("gate")
        == "PROSPECTIVE_AMENDMENT_INDEPENDENTLY_ACCEPTED"
        and amendment_receipt.get("manifest_sha256")
        == manifest_receipt.get("manifest_sha256")
        and amendment_receipt.get("manifest_self_root_sha256")
        == manifest.get("manifest_self_root_sha256")
        and amendment_receipt.get("golden_root_sha256")
        == manifest.get("golden_root_sha256")
        and amendment_receipt.get("amendment_self_root_sha256")
        == amendment.get("amendment_self_root_sha256")
        and amendment_receipt.get("continuation_authority_active") is False
        and amendment_receipt.get("other_arms_authorized") is False
        and amendment_receipt.get(
            "broker_live_vps_deployment_authorized"
        )
        is False,
        "predecessor_amendment_receipt_invalid",
    )
    if postseal is None or postseal_receipt is None:
        _require(
            postseal is None and postseal_receipt is None,
            "predecessor_postseal_authority_incomplete",
        )
        return
    _require(
        postseal.get("schema") == POSTSEAL_SCHEMA
        and postseal.get("amendment_self_root_sha256")
        == _self_root(postseal, "amendment_self_root_sha256")
        and (postseal.get("original_golden") or {}).get(
            "manifest_self_root_sha256"
        )
        == manifest.get("manifest_self_root_sha256")
        and (postseal.get("original_golden") or {}).get("golden_root_sha256")
        == manifest.get("golden_root_sha256"),
        "predecessor_postseal_authority_invalid",
    )
    _require(
        postseal_receipt.get("schema") == POSTSEAL_RECEIPT_SCHEMA
        and postseal_receipt.get("gate")
        == "POST_SEAL_NAMESPACE_AMENDMENT_INDEPENDENTLY_ACCEPTED"
        and postseal_receipt.get("manifest_self_root_sha256")
        == manifest.get("manifest_self_root_sha256")
        and postseal_receipt.get("golden_root_sha256")
        == manifest.get("golden_root_sha256")
        and postseal_receipt.get("amendment_self_root_sha256")
        == postseal.get("amendment_self_root_sha256"),
        "predecessor_postseal_receipt_invalid",
    )


def build_successor_authority(
    *,
    predecessor_manifest_path: Path,
    predecessor_amendment_path: Path,
    predecessor_manifest_receipt_path: Path,
    predecessor_amendment_receipt_path: Path,
    structural_successor_receipt_path: Path,
    predecessor_snapshot_namespace: Path,
    successor_namespace: Path,
    output_prefix: str,
    predecessor_postseal_amendment_path: Path | None = None,
    predecessor_postseal_receipt_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = _absolute_lexical(
        predecessor_manifest_path, "predecessor_manifest_path_invalid"
    )
    amendment_path = _absolute_lexical(
        predecessor_amendment_path, "predecessor_amendment_path_invalid"
    )
    manifest_receipt_path = _absolute_lexical(
        predecessor_manifest_receipt_path,
        "predecessor_manifest_receipt_path_invalid",
    )
    amendment_receipt_path = _absolute_lexical(
        predecessor_amendment_receipt_path,
        "predecessor_amendment_receipt_path_invalid",
    )
    structural_receipt_path = _absolute_lexical(
        structural_successor_receipt_path,
        "structural_successor_receipt_path_invalid",
    )
    predecessor_snapshot_namespace = _absolute_lexical(
        predecessor_snapshot_namespace,
        "predecessor_snapshot_namespace_path_invalid",
    )
    successor_namespace = _absolute_lexical(
        successor_namespace, "successor_namespace_path_invalid"
    )
    manifest, manifest_raw = _load(
        manifest_path, "predecessor_manifest_invalid"
    )
    amendment, amendment_raw = _load(
        amendment_path, "predecessor_amendment_invalid"
    )
    manifest_receipt, manifest_receipt_raw = _load(
        manifest_receipt_path, "predecessor_manifest_receipt_invalid"
    )
    amendment_receipt, amendment_receipt_raw = _load(
        amendment_receipt_path, "predecessor_amendment_receipt_invalid"
    )
    structural_receipt, structural_receipt_raw = _load(
        structural_receipt_path, "structural_successor_receipt_invalid"
    )
    postseal: dict[str, Any] | None = None
    postseal_raw: bytes | None = None
    postseal_receipt: dict[str, Any] | None = None
    postseal_receipt_raw: bytes | None = None
    if predecessor_postseal_amendment_path is not None:
        postseal_path = _absolute_lexical(
            predecessor_postseal_amendment_path,
            "predecessor_postseal_path_invalid",
        )
        postseal, postseal_raw = _load(
            postseal_path, "predecessor_postseal_authority_invalid"
        )
    else:
        postseal_path = None
    if predecessor_postseal_receipt_path is not None:
        postseal_receipt_path = _absolute_lexical(
            predecessor_postseal_receipt_path,
            "predecessor_postseal_receipt_path_invalid",
        )
        postseal_receipt, postseal_receipt_raw = _load(
            postseal_receipt_path,
            "predecessor_postseal_receipt_invalid",
        )
    else:
        postseal_receipt_path = None
    _validate_manifest_core(manifest)
    _require(
        manifest_receipt.get("manifest_sha256")
        == hashlib.sha256(manifest_raw).hexdigest()
        and amendment_receipt.get("amendment_sha256")
        == hashlib.sha256(amendment_raw).hexdigest(),
        "predecessor_receipt_file_hash_mismatch",
    )
    _validate_predecessor_receipts(
        manifest=manifest,
        manifest_receipt=manifest_receipt,
        amendment=amendment,
        amendment_receipt=amendment_receipt,
        postseal=postseal,
        postseal_receipt=postseal_receipt,
    )
    _require(
        structural_receipt.get("schema") == SUCCESSOR_SCHEMA
        and structural_receipt.get("gate") == SUCCESSOR_GATE
        and structural_receipt.get("receipt_root_sha256")
        == _self_root(structural_receipt, "receipt_root_sha256")
        and structural_receipt.get("changed_leaf_count") == 21
        and structural_receipt.get("serialized_replacement_count") == 21
        and structural_receipt.get("all_other_json_values_equal") is True
        and structural_receipt.get("economic_values_exposed") is False
        and structural_receipt.get("parity_continuation_authorized") is False,
        "structural_successor_receipt_invalid",
    )
    predecessor_partial_path = _absolute_lexical(
        Path(str(structural_receipt.get("predecessor_partial_summary") or "")),
        "structural_successor_predecessor_path_invalid",
    )
    successor_partial_path = _absolute_lexical(
        Path(str(structural_receipt.get("successor_partial_summary") or "")),
        "structural_successor_path_invalid",
    )
    _require(
        predecessor_partial_path.parent == predecessor_snapshot_namespace
        and predecessor_partial_path.name
        == f"{output_prefix}_PARTIAL_SUMMARY.json"
        and
        successor_partial_path.parent == successor_namespace
        and successor_partial_path.name
        == f"{output_prefix}_PARTIAL_SUMMARY.json",
        "structural_successor_namespace_mismatch",
    )
    predecessor_partial_raw, predecessor_partial_identity = _read(
        predecessor_partial_path, "predecessor_partial_summary_invalid"
    )
    successor_partial_raw, successor_partial_identity = _read(
        successor_partial_path, "successor_partial_summary_invalid"
    )
    _require(
        predecessor_partial_identity
        != successor_partial_identity
        and structural_receipt.get("predecessor_partial_summary_sha256")
        == hashlib.sha256(predecessor_partial_raw).hexdigest()
        and structural_receipt.get("successor_partial_summary_sha256")
        == hashlib.sha256(successor_partial_raw).hexdigest(),
        "structural_successor_partial_identity_mismatch",
    )
    reproduced, reproduced_core = rebind_partial_summary_source_plan_digest(
        predecessor_partial_raw,
        bound_source_plan_digest_sha256=str(
            structural_receipt.get("bound_source_plan_digest_sha256") or ""
        ),
    )
    _require(
        reproduced == successor_partial_raw
        and all(
            structural_receipt.get(key) == value
            for key, value in reproduced_core.items()
        ),
        "structural_successor_reproduction_mismatch",
    )
    namespace_record = manifest.get("namespace")
    surfaces = manifest.get("persisted_result_surfaces")
    partial_record = manifest.get("partial_summary")
    _require(
        type(namespace_record) is dict
        and type(surfaces) is list
        and type(partial_record) is dict
        and namespace_record.get("output_prefix") == output_prefix
        and [row.get("role") for row in surfaces] == list(LEDGER_ROLES),
        "predecessor_surface_inventory_invalid",
    )
    predecessor_source_namespace = _absolute_lexical(
        Path(str(namespace_record.get("path") or "")),
        "predecessor_namespace_path_invalid",
    )
    expected_names = {
        str(partial_record.get("name") or ""),
        *(str(row.get("name") or "") for row in surfaces),
    }
    observed_source_names = {
        path.name
        for path in predecessor_source_namespace.iterdir()
        if path.name.startswith(output_prefix + "_")
    }
    snapshot_names = {
        path.name
        for path in predecessor_snapshot_namespace.iterdir()
        if path.name.startswith(output_prefix + "_")
    }
    _require(
        snapshot_names == expected_names,
        "predecessor_snapshot_inventory_mismatch",
    )
    additions = sorted(observed_source_names - expected_names)
    if postseal is not None:
        accepted = (postseal.get("current_namespace") or {}).get(
            "accepted_filenames"
        )
        _require(
            type(accepted) is list
            and set(expected_names).issubset(set(accepted)),
            "postseal_namespace_inventory_mismatch",
        )
    source_partial_path = predecessor_source_namespace / str(
        partial_record["name"]
    )
    source_partial_raw, _source_partial_identity = _read(
        source_partial_path,
        "predecessor_source_partial_summary_invalid",
    )
    _require(
        source_partial_raw == predecessor_partial_raw
        and hashlib.sha256(source_partial_raw).hexdigest()
        == partial_record.get("sha256"),
        "predecessor_snapshot_partial_identity_mismatch",
    )
    copied: list[dict[str, Any]] = []
    successor_expected_names = {successor_partial_path.name}
    for row in surfaces:
        role = str(row["role"])
        name = str(row["name"])
        source_path = predecessor_source_namespace / name
        predecessor_path = predecessor_snapshot_namespace / name
        successor_path = successor_namespace / name
        source_to_snapshot = _compare_regular_files(
            source_path,
            predecessor_path,
            code=f"predecessor_snapshot_ledger_mismatch:{role}",
        )
        comparison = _compare_regular_files(
            predecessor_path,
            successor_path,
            code=f"copied_ledger_identity_mismatch:{role}",
        )
        _require(
            source_to_snapshot == comparison
            and comparison["bytes"] == row.get("bytes")
            and comparison["rows"] == row.get("rows")
            and comparison["sha256"] == row.get("sha256"),
            f"copied_ledger_identity_mismatch:{role}",
        )
        successor_expected_names.add(name)
        copied.append(
            {
                "role": role,
                "name": name,
                "bytes": comparison["bytes"],
                "rows": row.get("rows"),
                "sha256": comparison["sha256"],
                "predecessor_source_path": str(source_path),
                "predecessor_path": str(predecessor_path),
                "successor_path": str(successor_path),
                "distinct_storage_identity": comparison[
                    "distinct_storage_identity"
                ],
            }
        )
    successor_observed_names = {
        path.name
        for path in successor_namespace.iterdir()
        if path.name.startswith(output_prefix + "_")
    }
    _require(
        successor_observed_names == successor_expected_names,
        "successor_namespace_inventory_mismatch",
    )
    predecessor_files = {
        "manifest": {
            **_file_record(manifest_path, code="predecessor_manifest_invalid"),
            "manifest_self_root_sha256": manifest[
                "manifest_self_root_sha256"
            ],
            "golden_root_sha256": manifest["golden_root_sha256"],
            "opaque_result_surface_root_sha256": manifest[
                "opaque_result_surface_root_sha256"
            ],
        },
        "amendment": {
            **_file_record(amendment_path, code="predecessor_amendment_invalid"),
            "amendment_self_root_sha256": amendment[
                "amendment_self_root_sha256"
            ],
        },
        "manifest_verification_receipt": _file_record(
            manifest_receipt_path,
            code="predecessor_manifest_receipt_invalid",
        ),
        "amendment_verification_receipt": _file_record(
            amendment_receipt_path,
            code="predecessor_amendment_receipt_invalid",
        ),
        "postseal_amendment": (
            _file_record(
                postseal_path,
                code="predecessor_postseal_authority_invalid",
            )
            if postseal_path is not None
            else None
        ),
        "postseal_verification_receipt": (
            _file_record(
                postseal_receipt_path,
                code="predecessor_postseal_receipt_invalid",
            )
            if postseal_receipt_path is not None
            else None
        ),
    }
    core = {
        "schema": AUTHORITY_SCHEMA,
        "gate": AUTHORITY_GATE,
        "predecessor_authority": predecessor_files,
        "predecessor_namespace": {
            "source_path": str(predecessor_source_namespace),
            "snapshot_path": str(predecessor_snapshot_namespace),
            "output_prefix": output_prefix,
            "source_inventory_contaminated": bool(additions),
            "source_addition_count": len(additions),
            "source_addition_names_root_sha256": _root(additions),
            "snapshot_inventory_exact": True,
        },
        "structural_successor": {
            **_file_record(
                structural_receipt_path,
                code="structural_successor_receipt_invalid",
            ),
            "receipt_root_sha256": structural_receipt[
                "receipt_root_sha256"
            ],
            "predecessor_partial_summary_sha256": structural_receipt[
                "predecessor_partial_summary_sha256"
            ],
            "successor_partial_summary_sha256": structural_receipt[
                "successor_partial_summary_sha256"
            ],
            "changed_leaf_count": 21,
            "changed_leaf_path_root_sha256": structural_receipt[
                "changed_leaf_path_root_sha256"
            ],
        },
        "successor_namespace": {
            "path": str(successor_namespace),
            "output_prefix": output_prefix,
            "partial_summary_sha256": hashlib.sha256(
                successor_partial_raw
            ).hexdigest(),
            "inventory_exact": True,
        },
        "copied_ledger_byte_identity": copied,
        "predecessor_golden_root_sha256": manifest["golden_root_sha256"],
        "predecessor_opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
        "successor_opaque_result_surface_root_sha256": _root(
            [
                {
                    key: row[key]
                    for key in ("role", "name", "bytes", "rows", "sha256")
                }
                for row in copied
            ]
        ),
        "economic_values_exposed": False,
        "parity_continuation_authorized": False,
        "broker_live_authority": False,
    }
    return {**core, "authority_root_sha256": _root(core)}


def write_successor_authority(path: Path, value: Mapping[str, Any]) -> None:
    try:
        immutable_write_bytes(
            path,
            _canonical(value),
            code="successor_authority_output_exists_or_invalid",
        )
    except ImmutableEvidenceError:
        raise SuccessorAuthorityError(
            "successor_authority_output_exists_or_invalid"
        ) from None


def verify_successor_authority(path: Path) -> dict[str, Any]:
    path = _absolute_lexical(path, "successor_authority_path_invalid")
    authority, raw = _load(path, "successor_authority_invalid")
    _require(
        authority.get("schema") == AUTHORITY_SCHEMA
        and authority.get("gate") == AUTHORITY_GATE
        and authority.get("authority_root_sha256")
        == _self_root(authority, "authority_root_sha256")
        and authority.get("economic_values_exposed") is False
        and authority.get("parity_continuation_authorized") is False
        and authority.get("broker_live_authority") is False,
        "successor_authority_invalid",
    )
    predecessor = authority.get("predecessor_authority")
    structural = authority.get("structural_successor")
    successor_namespace = authority.get("successor_namespace")
    copied = authority.get("copied_ledger_byte_identity")
    _require(
        type(predecessor) is dict
        and type(structural) is dict
        and type(successor_namespace) is dict
        and type(copied) is list
        and [row.get("role") for row in copied] == list(LEDGER_ROLES),
        "successor_authority_invalid",
    )
    rebuilt = build_successor_authority(
        predecessor_manifest_path=Path(predecessor["manifest"]["path"]),
        predecessor_amendment_path=Path(predecessor["amendment"]["path"]),
        predecessor_manifest_receipt_path=Path(
            predecessor["manifest_verification_receipt"]["path"]
        ),
        predecessor_amendment_receipt_path=Path(
            predecessor["amendment_verification_receipt"]["path"]
        ),
        structural_successor_receipt_path=Path(structural["path"]),
        predecessor_snapshot_namespace=Path(
            authority["predecessor_namespace"]["snapshot_path"]
        ),
        successor_namespace=Path(successor_namespace["path"]),
        output_prefix=str(successor_namespace["output_prefix"]),
        predecessor_postseal_amendment_path=(
            Path(predecessor["postseal_amendment"]["path"])
            if predecessor.get("postseal_amendment") is not None
            else None
        ),
        predecessor_postseal_receipt_path=(
            Path(predecessor["postseal_verification_receipt"]["path"])
            if predecessor.get("postseal_verification_receipt") is not None
            else None
        ),
    )
    _require(rebuilt == authority, "successor_authority_recompute_mismatch")
    core = {
        "schema": AUTHORITY_VERIFICATION_SCHEMA,
        "gate": AUTHORITY_ACCEPTED_GATE,
        "authority_path": str(path),
        "authority_file_sha256": hashlib.sha256(raw).hexdigest(),
        "authority_root_sha256": authority["authority_root_sha256"],
        "predecessor_golden_root_sha256": authority[
            "predecessor_golden_root_sha256"
        ],
        "opaque_result_surface_root_sha256": authority[
            "successor_opaque_result_surface_root_sha256"
        ],
        "copied_ledger_count": len(copied),
        "changed_leaf_count": structural["changed_leaf_count"],
        "economic_values_exposed": False,
        "parity_continuation_authorized": False,
    }
    return {**core, "verification_root_sha256": _root(core)}
