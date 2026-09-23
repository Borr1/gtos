"""Production-derived, archive-first replay semantic diagnostics.

This module is deliberately non-authorizing. Exact persisted-byte parity remains
owned by ``replay_acceleration_real_parity_verifier`` and the real gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from src.research_infra.replay_acceleration_streaming_archive_verifier import (
    BoundEvidence,
    verify_campaign_with_role_line_consumer,
)
from src.research_infra.replay_semantic_parity import (
    SEMANTIC_PROOF_ROW_SCHEMA,
    canonical_sha256,
    compare_semantic_streams,
)


SEMANTIC_SOURCE_MANIFEST_SCHEMA = (
    "gtos.replay_acceleration.semantic_source_manifest.v1"
)
SEMANTIC_COMPARISON_SCOPE_SCHEMA = (
    "gtos.replay_acceleration.semantic_comparison_scope.v1"
)
SEMANTIC_DIAGNOSTIC_ADAPTER_SCHEMA = (
    "gtos.replay_acceleration.production_semantic_diagnostic.v1"
)
_SEMANTIC_CANDIDATE_SCHEMA = (
    "gtos.replay_acceleration.semantic_candidate.v1"
)
_SEMANTIC_CANDIDATE_PROVENANCE_SCHEMA = (
    "gtos.replay_acceleration.semantic_candidate_provenance.v1"
)
_SEMANTIC_STATE_CHECKPOINT_SCHEMA = (
    "gtos.replay_acceleration.semantic_state_checkpoint.v1"
)
_SEMANTIC_ORDER_PREIMAGE_SCHEMA = (
    "gtos.replay_acceleration.semantic_order_preimage.v1"
)
_ROW_PROVENANCE_SCHEMA = "broad_live_as_if_replay_row_provenance_v1"
_ARCHIVE_VERIFICATION_SCHEMA = (
    "gtos.replay_acceleration.streaming_proof_campaign_verification.v1"
)
_CHECKPOINT_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.streaming_checkpoint_authority.v1"
)
_FILE_ROLES = (
    "candidate",
    "order",
    "trade",
    "oracle",
    "state_checkpoint",
    "order_preimage",
)
_ARCHIVE_ROLES = ("scorecard", "missed")
_FILE_CONTRACT_KEYS = {"path", "bytes", "sha256", "row_count"}
_ARTIFACT_CONTRACT_KEYS = {"path", "bytes", "sha256"}
_SOURCE_IDENTITY_KEYS = {
    "campaign_id",
    "profile",
    "arm_id",
    "output_prefix",
    "run_identity_root_sha256",
    "source_plan_digest_sha256",
    "arm_fingerprint_sha256",
    "shared_execution_contract_sha256",
    "accelerated_code_config_authority_root_sha256",
}
_COMPARISON_SCOPE_KEYS = {
    "schema",
    "campaign_id",
    "profile",
    "arm_id",
    "source_plan_digest_sha256",
    "arm_fingerprint_sha256",
    "shared_execution_contract_sha256",
    "calendar_root_sha256",
    "direct_roles",
    "semantic_roles",
    "archive_roles",
    "comparison_scope_root_sha256",
}
_SOURCE_MANIFEST_KEYS = {
    "schema",
    "evidence_root",
    "namespaces",
    "source_identity",
    "calendar",
    "files",
    "archive",
    "comparison_scope",
    "evidence_set_root_sha256",
    "acceptance_authorized",
    "diagnostic_only",
    "economic_values_exposed",
    "source_manifest_root_sha256",
}
_ARCHIVE_DESCRIPTOR_KEYS = {
    "campaign_manifest",
    "verification_receipt",
    "terminal_checkpoint_snapshot",
    "terminal_arm_id",
    "verification_root_sha256",
    "checkpoint_authority_root_sha256",
    "checkpoint_chain_set_root_sha256",
    "terminal_checkpoint_chain_root_sha256",
    "verified_shard_receipt_set_root_sha256",
    "role_reconstruction_chain_roots_sha256",
    "verified_role_partitions",
    "verified_role_partition_roots_sha256",
    "verified_role_partitions_root_sha256",
    "cumulative_surfaces",
    "hot_tombstones",
    "hot_tombstone_set_root_sha256",
    "shard_count",
}
_FORBIDDEN_EXACT_ORDER_FIELDS = {
    "selected_order_attempt_primary",
    "selected_order_sequence",
    "semantic_order_preimage_schema",
    "semantic_order_preimage_sha256",
    "semantic_execution_manager_packet_sha256",
}
_EXPECTED_FILE_NAMES = {
    "candidate": "SEMANTIC_CANDIDATE_LEDGER.jsonl",
    "order": "ORDER_LEDGER.jsonl",
    "trade": "TRADE_LEDGER.jsonl",
    "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "state_checkpoint": "SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl",
    "order_preimage": "SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
}


def _lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def _nonblank_string(value: Any) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _exact_campaign_days(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError("semantic_campaign_days_invalid")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or len(value) != 10:
            raise ValueError("semantic_campaign_days_invalid")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("semantic_campaign_days_invalid") from None
        if parsed.isoformat() != value:
            raise ValueError("semantic_campaign_days_invalid")
        normalized.append(value)
    if normalized != sorted(set(normalized)):
        raise ValueError("semantic_campaign_days_invalid")
    return tuple(normalized)


def _json_mapping(raw: bytes, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError(code) from None
    if type(value) is not dict:
        raise ValueError(code)
    return value


def _atomic_write_json(
    path: Path,
    value: Mapping[str, Any],
    *,
    must_be_new: bool,
) -> None:
    path = _lexical_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or (must_be_new and path.exists()):
        raise ValueError("semantic_output_must_be_new")
    if path.exists():
        observed = path.stat()
        if not path.is_file() or observed.st_nlink != 1:
            raise ValueError("semantic_output_invalid")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("semantic_output_temporary_exists")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _artifact_contract(raw: bytes, path: Path) -> dict[str, Any]:
    return {
        "path": str(_lexical_path(path)),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _jsonl_rows_and_contract(
    raw: bytes,
    path: Path,
    *,
    role: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines(keepends=True)):
        if not line.strip() or not line.endswith(b"\n"):
            raise ValueError(f"semantic_source_jsonl_invalid:{role}:{index}")
        rows.append(
            _json_mapping(
                line,
                code=f"semantic_source_jsonl_invalid:{role}:{index}",
            )
        )
    contract = {
        **_artifact_contract(raw, path),
        "row_count": len(rows),
    }
    return rows, contract


def _validate_file_contract(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, Mapping)
        or set(value) != _FILE_CONTRACT_KEYS
        or not _nonblank_string(value.get("path"))
        or not Path(str(value["path"])).is_absolute()
        or type(value.get("bytes")) is not int
        or int(value["bytes"]) < 0
        or type(value.get("row_count")) is not int
        or int(value["row_count"]) < 0
        or not _is_sha256(value.get("sha256"))
    ):
        raise ValueError("semantic_source_manifest_invalid")
    return dict(value)


def _validate_artifact_contract(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, Mapping)
        or set(value) != _ARTIFACT_CONTRACT_KEYS
        or not _nonblank_string(value.get("path"))
        or not Path(str(value["path"])).is_absolute()
        or type(value.get("bytes")) is not int
        or int(value["bytes"]) < 0
        or not _is_sha256(value.get("sha256"))
    ):
        raise ValueError("semantic_source_manifest_invalid")
    return dict(value)


def _self_rooted_proof_row(**values: Any) -> dict[str, Any]:
    row = {"schema": SEMANTIC_PROOF_ROW_SCHEMA, **values}
    row["proof_root_sha256"] = canonical_sha256(row)
    return row


def _materialize_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    label: str,
) -> list[dict[str, Any]]:
    materialized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"semantic_{label}_row_not_mapping:{index}")
        materialized.append(dict(row))
    return materialized


def _partition(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "ordered_rows_root_sha256": canonical_sha256(list(rows)),
    }


def _produce_semantic_proof_rows(
    *,
    campaign_days: Sequence[str],
    state_checkpoint_rows: Iterable[Mapping[str, Any]],
    candidate_rows: Iterable[Mapping[str, Any]],
    missed_rows: Iterable[Mapping[str, Any]],
    order_rows: Iterable[Mapping[str, Any]],
    trade_rows: Iterable[Mapping[str, Any]],
    order_preimage_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Derive self-rooted proof rows from already authenticated source rows."""

    days = _exact_campaign_days(campaign_days)
    states = _materialize_rows(
        state_checkpoint_rows,
        label="state_checkpoint",
    )
    candidates = _materialize_rows(candidate_rows, label="candidate")
    missed = _materialize_rows(missed_rows, label="missed")
    orders = _materialize_rows(order_rows, label="order")
    trades = _materialize_rows(trade_rows, label="trade")
    preimages = _materialize_rows(
        order_preimage_rows,
        label="order_preimage",
    )
    if len(states) != len(days) * 2:
        raise ValueError("semantic_state_checkpoint_inventory_invalid")

    proofs: list[dict[str, Any]] = []
    expected_state_inventory = [
        (day, boundary)
        for day in days
        for boundary in ("pre_day", "post_day")
    ]
    for index, (row, expected) in enumerate(
        zip(states, expected_state_inventory, strict=True)
    ):
        state_projection = row.get("state_projection")
        if (
            row.get("schema") != _SEMANTIC_STATE_CHECKPOINT_SCHEMA
            or row.get("trading_day") != expected[0]
            or row.get("boundary") != expected[1]
            or not isinstance(state_projection, Mapping)
            or row.get("state_root_sha256")
            != canonical_sha256(state_projection)
        ):
            raise ValueError(
                f"semantic_state_checkpoint_inventory_invalid:{index}"
            )
        proofs.append(
            _self_rooted_proof_row(
                proof_sequence=len(proofs),
                proof_type="state_checkpoint",
                trading_day=expected[0],
                boundary=expected[1],
                state_projection=dict(state_projection),
                state_root_sha256=row["state_root_sha256"],
            )
        )

    proofs.append(
        _self_rooted_proof_row(
            proof_sequence=len(proofs),
            proof_type="terminal_partition",
            trading_day=days[-1],
            partitions={
                "candidate": _partition(candidates),
                "missed": _partition(missed),
                "order": _partition(orders),
                "trade": _partition(trades),
            },
        )
    )
    for index, row in enumerate(preimages):
        owner = row.get("owner")
        payload_text = row.get("sidecar_payload_canonical_json")
        try:
            payload = json.loads(payload_text) if isinstance(payload_text, str) else None
        except json.JSONDecodeError:
            payload = None
        canonical_payload = (
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=True,
            )
            if isinstance(payload, Mapping)
            else None
        )
        payload_sha256 = (
            hashlib.sha256(payload_text.encode("ascii")).hexdigest()
            if isinstance(payload_text, str)
            else None
        )
        if (
            row.get("schema") != _SEMANTIC_ORDER_PREIMAGE_SCHEMA
            or type(row.get("trading_day")) is not str
            or not str(row.get("execution_packet_sidecar_id") or "").strip()
            or not isinstance(payload_text, str)
            or canonical_payload != payload_text
            or not _is_sha256(row.get("sidecar_payload_sha256"))
            or payload_sha256 != row.get("sidecar_payload_sha256")
            or not isinstance(owner, Mapping)
            or owner.get("payload_root_sha256")
            != row.get("sidecar_payload_sha256")
        ):
            raise ValueError(f"semantic_order_preimage_inventory_invalid:{index}")
        proofs.append(
            _self_rooted_proof_row(
                proof_sequence=len(proofs),
                proof_type="order_sidecar_preimage",
                trading_day=row["trading_day"],
                execution_packet_sidecar_id=row[
                    "execution_packet_sidecar_id"
                ],
                sidecar_payload_canonical_json=payload_text,
                sidecar_payload_sha256=row["sidecar_payload_sha256"],
                owner=dict(owner),
            )
        )
    return proofs


def _report_core_valid(report: Mapping[str, Any]) -> bool:
    report_core = dict(report)
    verification_root = report_core.pop("verification_root_sha256", None)
    return bool(
        report.get("schema") == _ARCHIVE_VERIFICATION_SCHEMA
        and report.get("valid") is True
        and report.get("writer_imported") is False
        and report.get("runner_imported") is False
        and report.get("economic_values_exposed") is False
        and verification_root == canonical_sha256(report_core)
    )


def _partition_days(partitions: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    days: list[str] = []
    for item in partitions:
        try:
            start = date.fromisoformat(str(item["start_day"]))
            end = date.fromisoformat(str(item["end_day"]))
        except (KeyError, TypeError, ValueError):
            raise ValueError("semantic_archive_partition_invalid") from None
        if start > end:
            raise ValueError("semantic_archive_partition_invalid")
        current = start
        while current <= end:
            days.append(current.isoformat())
            current += timedelta(days=1)
    return tuple(days)


def _archive_descriptor(
    *,
    campaign_raw: bytes,
    campaign_path: Path,
    verification_raw: bytes,
    verification_path: Path,
    report: Mapping[str, Any],
    campaign_days: tuple[str, ...],
) -> dict[str, Any]:
    if not _report_core_valid(report):
        raise ValueError("semantic_archive_verification_invalid")
    campaign = _json_mapping(
        campaign_raw,
        code="semantic_archive_campaign_manifest_invalid",
    )
    if (
        _lexical_path(Path(str(report.get("campaign_manifest_path") or "")))
        != _lexical_path(campaign_path)
        or report.get("campaign_manifest_sha256")
        != hashlib.sha256(campaign_raw).hexdigest()
        or report.get("campaign_manifest_root_sha256")
        != campaign.get("campaign_manifest_root_sha256")
    ):
        raise ValueError("semantic_archive_campaign_identity_mismatch")
    checkpoint_authority = report.get("checkpoint_authority")
    if (
        not isinstance(checkpoint_authority, Mapping)
        or checkpoint_authority.get("schema")
        != _CHECKPOINT_AUTHORITY_SCHEMA
    ):
        raise ValueError("semantic_archive_checkpoint_authority_invalid")
    verified = report.get("verified_role_partitions")
    if not isinstance(verified, list):
        raise ValueError("semantic_archive_partition_invalid")
    role_partitions: dict[str, list[dict[str, Any]]] = {}
    role_partition_roots: dict[str, str] = {}
    for role in _ARCHIVE_ROLES:
        items = [dict(item) for item in verified if item.get("role") == role]
        if not items or _partition_days(items) != campaign_days:
            raise ValueError(f"semantic_archive_partition_invalid:{role}")
        role_partitions[role] = items
        role_partition_roots[role] = canonical_sha256(items)
    cumulative = report.get("cumulative_surfaces")
    if not isinstance(cumulative, list):
        raise ValueError("semantic_archive_cumulative_surface_invalid")
    cumulative_by_role = {
        role: dict(next(item for item in cumulative if item.get("role") == role))
        for role in _ARCHIVE_ROLES
    }
    hot_tombstones = report.get("hot_tombstones")
    if not isinstance(hot_tombstones, list):
        raise ValueError("semantic_archive_tombstones_invalid")
    descriptor = {
        "campaign_manifest": {
            **_artifact_contract(campaign_raw, campaign_path),
            "campaign_manifest_root_sha256": report[
                "campaign_manifest_root_sha256"
            ],
        },
        "verification_receipt": _artifact_contract(
            verification_raw,
            verification_path,
        ),
        "verification_root_sha256": report["verification_root_sha256"],
        "checkpoint_authority_root_sha256": canonical_sha256(
            checkpoint_authority
        ),
        "checkpoint_chain_set_root_sha256": report[
            "checkpoint_chain_set_root_sha256"
        ],
        "terminal_checkpoint_chain_root_sha256": report[
            "terminal_checkpoint_chain_root_sha256"
        ],
        "verified_shard_receipt_set_root_sha256": report[
            "verified_shard_receipt_set_root_sha256"
        ],
        "role_reconstruction_chain_roots_sha256": dict(
            report["role_reconstruction_chain_roots_sha256"]
        ),
        "verified_role_partitions": role_partitions,
        "verified_role_partition_roots_sha256": role_partition_roots,
        "verified_role_partitions_root_sha256": report[
            "verified_role_partitions_root_sha256"
        ],
        "cumulative_surfaces": cumulative_by_role,
        "hot_tombstones": [dict(item) for item in hot_tombstones],
        "hot_tombstone_set_root_sha256": report[
            "hot_tombstone_set_root_sha256"
        ],
        "shard_count": report["shard_count"],
    }
    if any(
        not _is_sha256(descriptor[field])
        for field in (
            "verification_root_sha256",
            "checkpoint_authority_root_sha256",
            "checkpoint_chain_set_root_sha256",
            "terminal_checkpoint_chain_root_sha256",
            "verified_shard_receipt_set_root_sha256",
            "verified_role_partitions_root_sha256",
            "hot_tombstone_set_root_sha256",
        )
    ) or type(descriptor["shard_count"]) is not int:
        raise ValueError("semantic_archive_verification_invalid")
    return descriptor


def _expected_evidence_path_names(output_prefix: str) -> dict[str, str]:
    return {
        role: f"{output_prefix}_{suffix}"
        for role, suffix in _EXPECTED_FILE_NAMES.items()
    }


def write_semantic_source_manifest(
    *,
    source_manifest_path: Path,
    evidence_paths: Mapping[str, Path],
    archive_manifest_path: Path,
    archive_verification_receipt_path: Path,
    campaign_id: str,
    profile: str,
    arm_id: str,
    campaign_days: Sequence[str],
) -> dict[str, Any]:
    """Seal one archive-bound semantic source manifest for one run/profile."""

    days = _exact_campaign_days(campaign_days)
    if (
        set(evidence_paths) != set(_FILE_ROLES)
        or not _nonblank_string(campaign_id)
        or not _nonblank_string(profile)
        or not _nonblank_string(arm_id)
    ):
        raise ValueError("semantic_source_identity_invalid")
    manifest_path = _lexical_path(source_manifest_path)
    paths = {role: _lexical_path(Path(path)) for role, path in evidence_paths.items()}
    campaign_path = _lexical_path(archive_manifest_path)
    verification_path = _lexical_path(archive_verification_receipt_path)
    common_root = _lexical_path(
        Path(
            os.path.commonpath(
                [
                    str(manifest_path),
                    str(campaign_path),
                    str(verification_path),
                    *(str(path) for path in paths.values()),
                ]
            )
        )
    )
    if not common_root.is_dir():
        raise ValueError("semantic_source_evidence_root_invalid")

    with BoundEvidence(archive_root=common_root) as evidence:
        campaign_bound = evidence.bind(
            campaign_path,
            code="semantic_archive_campaign_manifest_unreadable",
        )
        verification_bound = evidence.bind(
            verification_path,
            code="semantic_archive_verification_receipt_unreadable",
        )
        campaign_raw = campaign_bound.read_bytes()
        verification_raw = verification_bound.read_bytes()
        report = _json_mapping(
            verification_raw,
            code="semantic_archive_verification_receipt_invalid",
        )
        if not _report_core_valid(report):
            raise ValueError("semantic_archive_verification_invalid")
        terminal_summary = report.get("terminal_pre_archive_partial_summary")
        if not isinstance(terminal_summary, Mapping):
            raise ValueError("semantic_archive_checkpoint_snapshot_invalid")
        terminal_snapshot_path = _lexical_path(
            Path(str(terminal_summary.get("snapshot_path") or ""))
        )
        if (
            not terminal_snapshot_path.is_absolute()
            or type(terminal_summary.get("bytes")) is not int
            or not _is_sha256(terminal_summary.get("sha256"))
        ):
            raise ValueError("semantic_archive_checkpoint_snapshot_invalid")
        terminal_snapshot_bound = evidence.bind(
            terminal_snapshot_path,
            code="semantic_archive_checkpoint_snapshot_invalid",
        )
        terminal_snapshot_raw = terminal_snapshot_bound.read_bytes()
        if (
            len(terminal_snapshot_raw) != terminal_summary["bytes"]
            or hashlib.sha256(terminal_snapshot_raw).hexdigest()
            != terminal_summary["sha256"]
        ):
            raise ValueError("semantic_archive_checkpoint_snapshot_invalid")
        terminal_snapshot = _json_mapping(
            terminal_snapshot_raw,
            code="semantic_archive_checkpoint_snapshot_invalid",
        )
        arm_binding = terminal_snapshot.get(
            "b7_5_selection_sizing_factorial_arm_binding"
        )
        files: dict[str, dict[str, Any]] = {}
        for role in _FILE_ROLES:
            bound = evidence.bind(
                paths[role],
                code=f"semantic_source_{role}_unreadable",
            )
            _rows, contract = _jsonl_rows_and_contract(
                bound.read_bytes(),
                paths[role],
                role=role,
            )
            files[role] = contract
        archive = _archive_descriptor(
            campaign_raw=campaign_raw,
            campaign_path=campaign_path,
            verification_raw=verification_raw,
            verification_path=verification_path,
            report=report,
            campaign_days=days,
        )
        archive["terminal_checkpoint_snapshot"] = _artifact_contract(
            terminal_snapshot_raw,
            terminal_snapshot_path,
        )
        archive["terminal_arm_id"] = arm_id
        evidence.assert_paths_unchanged()

    checkpoint_authority = report["checkpoint_authority"]
    output_prefix = checkpoint_authority["output_prefix"]
    if (
        not _nonblank_string(output_prefix)
        or not isinstance(arm_binding, Mapping)
        or arm_binding.get("arm_id") != arm_id
        or arm_binding.get("arm_fingerprint_sha256")
        != checkpoint_authority.get("arm_fingerprint_sha256")
    ):
        raise ValueError("semantic_source_identity_invalid")
    expected_names = _expected_evidence_path_names(output_prefix)
    if any(paths[role].name != expected_names[role] for role in _FILE_ROLES):
        raise ValueError("semantic_source_file_topology_invalid")
    exact_namespace = paths["order"].parent
    semantic_namespace = paths["candidate"].parent
    if (
        any(paths[role].parent != exact_namespace for role in ("order", "trade", "oracle"))
        or any(
            paths[role].parent != semantic_namespace
            for role in ("candidate", "state_checkpoint", "order_preimage")
        )
        or manifest_path.parent != semantic_namespace
        or semantic_namespace
        != exact_namespace.parent / f"{exact_namespace.name}.semantic-diagnostic"
        or not campaign_path.is_relative_to(exact_namespace)
        or not verification_path.is_relative_to(exact_namespace)
        or not terminal_snapshot_path.is_relative_to(exact_namespace)
    ):
        raise ValueError("semantic_source_file_topology_invalid")

    source_identity = {
        "campaign_id": campaign_id,
        "profile": profile,
        "arm_id": arm_id,
        "output_prefix": output_prefix,
        "run_identity_root_sha256": checkpoint_authority[
            "run_identity_root_sha256"
        ],
        "source_plan_digest_sha256": checkpoint_authority[
            "source_plan_digest_sha256"
        ],
        "arm_fingerprint_sha256": checkpoint_authority[
            "arm_fingerprint_sha256"
        ],
        "shared_execution_contract_sha256": checkpoint_authority[
            "shared_execution_contract_sha256"
        ],
        "accelerated_code_config_authority_root_sha256": (
            checkpoint_authority[
                "accelerated_code_config_authority_root_sha256"
            ]
        ),
    }
    if any(
        not _is_sha256(source_identity[field])
        for field in (
            "run_identity_root_sha256",
            "source_plan_digest_sha256",
            "arm_fingerprint_sha256",
            "shared_execution_contract_sha256",
            "accelerated_code_config_authority_root_sha256",
        )
    ):
        raise ValueError("semantic_source_identity_invalid")
    calendar = {
        "days": list(days),
        "day_count": len(days),
        "calendar_root_sha256": canonical_sha256(list(days)),
    }
    comparison_scope_core = {
        "schema": SEMANTIC_COMPARISON_SCOPE_SCHEMA,
        "campaign_id": campaign_id,
        "profile": profile,
        "arm_id": arm_id,
        "source_plan_digest_sha256": source_identity[
            "source_plan_digest_sha256"
        ],
        "arm_fingerprint_sha256": source_identity["arm_fingerprint_sha256"],
        "shared_execution_contract_sha256": source_identity[
            "shared_execution_contract_sha256"
        ],
        "calendar_root_sha256": calendar["calendar_root_sha256"],
        "direct_roles": ["order", "trade", "oracle"],
        "semantic_roles": ["candidate", "state_checkpoint", "order_preimage"],
        "archive_roles": list(_ARCHIVE_ROLES),
    }
    comparison_scope = {
        **comparison_scope_core,
        "comparison_scope_root_sha256": canonical_sha256(
            comparison_scope_core
        ),
    }
    namespaces = {
        "exact": str(exact_namespace),
        "semantic": str(semantic_namespace),
    }
    evidence_set_core = {
        "source_identity_root_sha256": canonical_sha256(source_identity),
        "files": files,
        "archive": archive,
    }
    manifest_core = {
        "schema": SEMANTIC_SOURCE_MANIFEST_SCHEMA,
        "evidence_root": str(common_root),
        "namespaces": namespaces,
        "source_identity": source_identity,
        "calendar": calendar,
        "files": files,
        "archive": archive,
        "comparison_scope": comparison_scope,
        "evidence_set_root_sha256": canonical_sha256(evidence_set_core),
        "acceptance_authorized": False,
        "diagnostic_only": True,
        "economic_values_exposed": False,
    }
    manifest = {
        **manifest_core,
        "source_manifest_root_sha256": canonical_sha256(manifest_core),
    }
    _atomic_write_json(manifest_path, manifest, must_be_new=False)
    return manifest


def _validate_source_manifest_structure(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path,
) -> dict[str, Any]:
    if type(manifest) is not dict or set(manifest) != _SOURCE_MANIFEST_KEYS:
        raise ValueError("semantic_source_manifest_invalid")
    core = dict(manifest)
    root_value = core.pop("source_manifest_root_sha256", None)
    if (
        manifest.get("schema") != SEMANTIC_SOURCE_MANIFEST_SCHEMA
        or root_value != canonical_sha256(core)
        or manifest.get("acceptance_authorized") is not False
        or manifest.get("diagnostic_only") is not True
        or manifest.get("economic_values_exposed") is not False
    ):
        raise ValueError("semantic_source_manifest_invalid")
    evidence_root_value = manifest.get("evidence_root")
    if (
        not _nonblank_string(evidence_root_value)
        or not Path(str(evidence_root_value)).is_absolute()
    ):
        raise ValueError("semantic_source_manifest_invalid")
    source_identity = manifest.get("source_identity")
    if (
        not isinstance(source_identity, Mapping)
        or set(source_identity) != _SOURCE_IDENTITY_KEYS
        or any(
            not _nonblank_string(source_identity.get(field))
            for field in ("campaign_id", "profile", "arm_id", "output_prefix")
        )
        or any(
            not _is_sha256(source_identity.get(field))
            for field in _SOURCE_IDENTITY_KEYS
            - {"campaign_id", "profile", "arm_id", "output_prefix"}
        )
        or source_identity.get("campaign_id")
        != (
            f"{str(source_identity.get('output_prefix')).lower()}_"
            f"{source_identity.get('profile')}"
        )
    ):
        raise ValueError("semantic_source_manifest_invalid")
    calendar = manifest.get("calendar")
    if not isinstance(calendar, Mapping) or set(calendar) != {
        "days",
        "day_count",
        "calendar_root_sha256",
    }:
        raise ValueError("semantic_source_manifest_invalid")
    days = _exact_campaign_days(calendar.get("days"))
    if (
        type(calendar.get("day_count")) is not int
        or calendar.get("day_count") != len(days)
        or calendar.get("calendar_root_sha256")
        != canonical_sha256(list(days))
    ):
        raise ValueError("semantic_source_manifest_invalid")
    files = manifest.get("files")
    if not isinstance(files, Mapping) or set(files) != set(_FILE_ROLES):
        raise ValueError("semantic_source_manifest_invalid")
    validated_files = {
        role: _validate_file_contract(files[role]) for role in _FILE_ROLES
    }
    archive = manifest.get("archive")
    if not isinstance(archive, Mapping) or set(archive) != _ARCHIVE_DESCRIPTOR_KEYS:
        raise ValueError("semantic_source_manifest_invalid")
    campaign_contract = dict(archive.get("campaign_manifest") or {})
    campaign_root = campaign_contract.pop("campaign_manifest_root_sha256", None)
    if (
        _validate_artifact_contract(campaign_contract) != campaign_contract
        or not _is_sha256(campaign_root)
        or _validate_artifact_contract(archive.get("verification_receipt"))
        != dict(archive["verification_receipt"])
        or _validate_artifact_contract(
            archive.get("terminal_checkpoint_snapshot")
        )
        != dict(archive["terminal_checkpoint_snapshot"])
        or not _nonblank_string(archive.get("terminal_arm_id"))
        or archive.get("terminal_arm_id") != source_identity.get("arm_id")
        or any(
            not _is_sha256(archive.get(field))
            for field in (
                "verification_root_sha256",
                "checkpoint_authority_root_sha256",
                "checkpoint_chain_set_root_sha256",
                "terminal_checkpoint_chain_root_sha256",
                "verified_shard_receipt_set_root_sha256",
                "verified_role_partitions_root_sha256",
                "hot_tombstone_set_root_sha256",
            )
        )
        or type(archive.get("shard_count")) is not int
        or int(archive["shard_count"]) < 1
    ):
        raise ValueError("semantic_source_manifest_invalid")
    role_partitions = archive.get("verified_role_partitions")
    role_partition_roots = archive.get("verified_role_partition_roots_sha256")
    cumulative = archive.get("cumulative_surfaces")
    if (
        not isinstance(role_partitions, Mapping)
        or set(role_partitions) != set(_ARCHIVE_ROLES)
        or not isinstance(role_partition_roots, Mapping)
        or set(role_partition_roots) != set(_ARCHIVE_ROLES)
        or not isinstance(cumulative, Mapping)
        or set(cumulative) != set(_ARCHIVE_ROLES)
        or not isinstance(archive.get("hot_tombstones"), list)
        or not isinstance(
            archive.get("role_reconstruction_chain_roots_sha256"),
            Mapping,
        )
    ):
        raise ValueError("semantic_source_manifest_invalid")
    for role in _ARCHIVE_ROLES:
        items = role_partitions[role]
        if (
            not isinstance(items, list)
            or _partition_days(items) != days
            or role_partition_roots[role] != canonical_sha256(items)
            or not isinstance(cumulative[role], Mapping)
            or cumulative[role].get("role") != role
        ):
            raise ValueError("semantic_source_manifest_invalid")
    comparison_scope = manifest.get("comparison_scope")
    if (
        not isinstance(comparison_scope, Mapping)
        or set(comparison_scope) != _COMPARISON_SCOPE_KEYS
    ):
        raise ValueError("semantic_source_manifest_invalid")
    comparison_core = dict(comparison_scope)
    comparison_root = comparison_core.pop("comparison_scope_root_sha256", None)
    if (
        comparison_scope.get("schema") != SEMANTIC_COMPARISON_SCOPE_SCHEMA
        or comparison_root != canonical_sha256(comparison_core)
        or comparison_scope.get("campaign_id") != source_identity["campaign_id"]
        or comparison_scope.get("profile") != source_identity["profile"]
        or comparison_scope.get("arm_id") != source_identity["arm_id"]
        or comparison_scope.get("source_plan_digest_sha256")
        != source_identity["source_plan_digest_sha256"]
        or comparison_scope.get("arm_fingerprint_sha256")
        != source_identity["arm_fingerprint_sha256"]
        or comparison_scope.get("shared_execution_contract_sha256")
        != source_identity["shared_execution_contract_sha256"]
        or comparison_scope.get("calendar_root_sha256")
        != calendar["calendar_root_sha256"]
        or comparison_scope.get("direct_roles") != ["order", "trade", "oracle"]
        or comparison_scope.get("semantic_roles")
        != ["candidate", "state_checkpoint", "order_preimage"]
        or comparison_scope.get("archive_roles") != list(_ARCHIVE_ROLES)
    ):
        raise ValueError("semantic_source_manifest_invalid")
    expected_evidence_set_root = canonical_sha256(
        {
            "source_identity_root_sha256": canonical_sha256(source_identity),
            "files": validated_files,
            "archive": dict(archive),
        }
    )
    if manifest.get("evidence_set_root_sha256") != expected_evidence_set_root:
        raise ValueError("semantic_source_manifest_invalid")
    namespaces = manifest.get("namespaces")
    if (
        not isinstance(namespaces, Mapping)
        or set(namespaces) != {"exact", "semantic"}
        or any(
            not _nonblank_string(namespaces.get(key))
            or not Path(str(namespaces[key])).is_absolute()
            for key in ("exact", "semantic")
        )
    ):
        raise ValueError("semantic_source_manifest_invalid")
    exact_namespace = _lexical_path(Path(str(namespaces["exact"])))
    semantic_namespace = _lexical_path(Path(str(namespaces["semantic"])))
    output_prefix = str(source_identity["output_prefix"])
    expected_names = _expected_evidence_path_names(output_prefix)
    for role, contract in validated_files.items():
        path = _lexical_path(Path(str(contract["path"])))
        expected_parent = (
            exact_namespace
            if role in {"order", "trade", "oracle"}
            else semantic_namespace
        )
        if path.parent != expected_parent or path.name != expected_names[role]:
            raise ValueError("semantic_source_file_topology_invalid")
    campaign_path = _lexical_path(
        Path(str(archive["campaign_manifest"]["path"]))
    )
    verification_path = _lexical_path(
        Path(str(archive["verification_receipt"]["path"]))
    )
    terminal_snapshot_path = _lexical_path(
        Path(str(archive["terminal_checkpoint_snapshot"]["path"]))
    )
    if (
        _lexical_path(manifest_path).parent != semantic_namespace
        or semantic_namespace
        != exact_namespace.parent / f"{exact_namespace.name}.semantic-diagnostic"
        or not campaign_path.is_relative_to(exact_namespace)
        or not verification_path.is_relative_to(exact_namespace)
        or not terminal_snapshot_path.is_relative_to(exact_namespace)
    ):
        raise ValueError("semantic_source_file_topology_invalid")
    all_paths = [
        _lexical_path(manifest_path),
        *(
            _lexical_path(Path(str(contract["path"])))
            for contract in validated_files.values()
        ),
        _lexical_path(Path(str(archive["campaign_manifest"]["path"]))),
        _lexical_path(Path(str(archive["verification_receipt"]["path"]))),
        _lexical_path(
            Path(str(archive["terminal_checkpoint_snapshot"]["path"]))
        ),
    ]
    expected_root = _lexical_path(
        Path(os.path.commonpath([str(path) for path in all_paths]))
    )
    if expected_root != _lexical_path(Path(str(evidence_root_value))):
        raise ValueError("semantic_source_evidence_root_invalid")
    return dict(manifest)


def _prepare_source_manifest(path: Path) -> dict[str, Any]:
    manifest_path = _lexical_path(path)
    with BoundEvidence(archive_root=manifest_path.parent) as evidence:
        bound = evidence.bind(
            manifest_path,
            code="semantic_source_manifest_unreadable",
        )
        raw = bound.read_bytes()
        manifest = _validate_source_manifest_structure(
            _json_mapping(raw, code="semantic_source_manifest_invalid"),
            manifest_path=manifest_path,
        )
        evidence.assert_paths_unchanged()
    return {
        "path": manifest_path,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "manifest": manifest,
    }


def _parse_archive_row(role: str, raw: bytes) -> dict[str, Any]:
    return _json_mapping(raw, code=f"semantic_archive_row_invalid:{role}")


def _verified_archive_rows(
    campaign_manifest_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rows = {"scorecard": [], "missed": []}

    def consume(role: str, raw: bytes) -> None:
        rows[role].append(_parse_archive_row(role, raw))

    report = verify_campaign_with_role_line_consumer(
        campaign_manifest_path,
        roles=_ARCHIVE_ROLES,
        consumer=consume,
    )
    return rows, report


def _validate_archive_report_against_manifest(
    manifest: Mapping[str, Any],
    report: Mapping[str, Any],
) -> None:
    if not _report_core_valid(report):
        raise ValueError("semantic_archive_verification_invalid")
    archive = manifest["archive"]
    source_identity = manifest["source_identity"]
    checkpoint_authority = report.get("checkpoint_authority")
    terminal_summary = report.get("terminal_pre_archive_partial_summary")
    if not isinstance(checkpoint_authority, Mapping) or not isinstance(
        terminal_summary,
        Mapping,
    ):
        raise ValueError("semantic_archive_source_identity_mismatch")
    terminal_snapshot_contract = {
        "path": str(
            _lexical_path(
                Path(str(terminal_summary.get("snapshot_path") or ""))
            )
        ),
        "bytes": terminal_summary.get("bytes"),
        "sha256": terminal_summary.get("sha256"),
    }
    if terminal_snapshot_contract != archive["terminal_checkpoint_snapshot"]:
        raise ValueError("semantic_archive_checkpoint_snapshot_invalid")
    archive_source_identity = {
        "output_prefix": checkpoint_authority.get("output_prefix"),
        "run_identity_root_sha256": checkpoint_authority.get(
            "run_identity_root_sha256"
        ),
        "source_plan_digest_sha256": checkpoint_authority.get(
            "source_plan_digest_sha256"
        ),
        "arm_fingerprint_sha256": checkpoint_authority.get(
            "arm_fingerprint_sha256"
        ),
        "shared_execution_contract_sha256": checkpoint_authority.get(
            "shared_execution_contract_sha256"
        ),
        "accelerated_code_config_authority_root_sha256": (
            checkpoint_authority.get(
                "accelerated_code_config_authority_root_sha256"
            )
        ),
        "arm_id": archive.get("terminal_arm_id"),
    }
    if any(
        source_identity.get(field) != value
        for field, value in archive_source_identity.items()
    ):
        raise ValueError("semantic_archive_source_identity_mismatch")
    expected = {
        "verification_root_sha256": report.get("verification_root_sha256"),
        "checkpoint_authority_root_sha256": canonical_sha256(
            report.get("checkpoint_authority")
        ),
        "checkpoint_chain_set_root_sha256": report.get(
            "checkpoint_chain_set_root_sha256"
        ),
        "terminal_checkpoint_chain_root_sha256": report.get(
            "terminal_checkpoint_chain_root_sha256"
        ),
        "verified_shard_receipt_set_root_sha256": report.get(
            "verified_shard_receipt_set_root_sha256"
        ),
        "role_reconstruction_chain_roots_sha256": report.get(
            "role_reconstruction_chain_roots_sha256"
        ),
        "verified_role_partitions_root_sha256": report.get(
            "verified_role_partitions_root_sha256"
        ),
        "hot_tombstone_set_root_sha256": report.get(
            "hot_tombstone_set_root_sha256"
        ),
        "shard_count": report.get("shard_count"),
    }
    for key, value in expected.items():
        if archive.get(key) != value:
            raise ValueError(f"semantic_archive_manifest_binding_mismatch:{key}")
    if (
        archive["campaign_manifest"]["path"]
        != str(_lexical_path(Path(str(report["campaign_manifest_path"]))))
        or archive["campaign_manifest"]["sha256"]
        != report.get("campaign_manifest_sha256")
        or archive["campaign_manifest"]["campaign_manifest_root_sha256"]
        != report.get("campaign_manifest_root_sha256")
    ):
        raise ValueError("semantic_archive_campaign_identity_mismatch")
    role_partitions = {
        role: [
            dict(item)
            for item in report["verified_role_partitions"]
            if item.get("role") == role
        ]
        for role in _ARCHIVE_ROLES
    }
    cumulative = {
        role: dict(
            next(
                item
                for item in report["cumulative_surfaces"]
                if item.get("role") == role
            )
        )
        for role in _ARCHIVE_ROLES
    }
    if (
        archive["verified_role_partitions"] != role_partitions
        or archive["verified_role_partition_roots_sha256"]
        != {
            role: canonical_sha256(items)
            for role, items in role_partitions.items()
        }
        or archive["cumulative_surfaces"] != cumulative
        or archive["hot_tombstones"] != report.get("hot_tombstones")
    ):
        raise ValueError("semantic_archive_manifest_binding_mismatch")


def _row_day(row: Mapping[str, Any]) -> str | None:
    explicit = row.get("trading_day")
    explicit_day: str | None = None
    if explicit is not None:
        if type(explicit) is not str:
            return None
        try:
            parsed = date.fromisoformat(explicit)
        except ValueError:
            return None
        if parsed.isoformat() != explicit:
            return None
        explicit_day = explicit
    decision = row.get("decision_time_utc") or row.get("decision_time")
    decision_day: str | None = None
    if decision is not None:
        if type(decision) is not str or len(decision) < 10:
            return None
        try:
            parsed = date.fromisoformat(decision[:10])
        except ValueError:
            return None
        decision_day = parsed.isoformat()
    if explicit_day and decision_day and explicit_day != decision_day:
        return None
    return explicit_day or decision_day


def _validate_source_rows(
    *,
    role: str,
    rows: Sequence[Mapping[str, Any]],
    campaign_id: str,
    profile: str,
    campaign_days: set[str],
) -> None:
    expected_row_type = {
        "order": "simulated_order",
        "trade": "simulated_trade",
        "oracle": "ordered_path_oracle",
        "scorecard": "scheduler_scorecard",
        "missed": "missed_opportunity",
    }
    for index, row in enumerate(rows):
        owner = row.get("owner") if role == "order_preimage" else None
        scoped_campaign = (
            owner.get("campaign")
            if isinstance(owner, Mapping)
            else row.get("campaign")
        )
        scoped_profile = (
            owner.get("profile")
            if isinstance(owner, Mapping)
            else row.get("profile")
        )
        if (
            scoped_campaign != campaign_id
            or scoped_profile != profile
            or _row_day(row) not in campaign_days
        ):
            raise ValueError(f"semantic_source_row_scope_invalid:{role}:{index}")
        if role == "candidate":
            if (
                row.get("row_type") != "semantic_candidate"
                or row.get("schema") != _SEMANTIC_CANDIDATE_SCHEMA
                or row.get("row_provenance_schema")
                != _SEMANTIC_CANDIDATE_PROVENANCE_SCHEMA
            ):
                raise ValueError(f"semantic_source_row_schema_invalid:{role}:{index}")
        elif role == "state_checkpoint":
            if row.get("schema") != _SEMANTIC_STATE_CHECKPOINT_SCHEMA:
                raise ValueError(f"semantic_source_row_schema_invalid:{role}:{index}")
        elif role == "order_preimage":
            owner = row.get("owner")
            if (
                row.get("schema") != _SEMANTIC_ORDER_PREIMAGE_SCHEMA
                or not isinstance(owner, Mapping)
                or owner.get("campaign") != campaign_id
                or owner.get("profile") != profile
            ):
                raise ValueError(f"semantic_source_row_schema_invalid:{role}:{index}")
        else:
            if (
                row.get("row_type") != expected_row_type[role]
                or row.get("row_provenance_schema") != _ROW_PROVENANCE_SCHEMA
                or row.get("broad_replay_profile") != profile
            ):
                raise ValueError(f"semantic_source_row_schema_invalid:{role}:{index}")
        if role == "order" and _FORBIDDEN_EXACT_ORDER_FIELDS.intersection(row):
            raise ValueError(f"semantic_exact_order_contaminated:{index}")


def _load_authenticated_source(
    prepared: Mapping[str, Any],
    archive_rows: dict[str, list[dict[str, Any]]],
    archive_report: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    manifest_path = _lexical_path(Path(prepared["path"]))
    manifest = prepared["manifest"]
    if not isinstance(manifest, Mapping):
        raise ValueError("semantic_source_manifest_invalid")
    _validate_archive_report_against_manifest(manifest, archive_report)
    source_identity = manifest["source_identity"]
    profile = str(source_identity["profile"])
    campaign_id = str(source_identity["campaign_id"])
    campaign_days = set(manifest["calendar"]["days"])
    evidence_root = _lexical_path(Path(str(manifest["evidence_root"])))

    with BoundEvidence(archive_root=evidence_root) as evidence:
        rebound_manifest = evidence.bind(
            manifest_path,
            code="semantic_source_manifest_unreadable",
        )
        rebound_raw = rebound_manifest.read_bytes()
        if (
            hashlib.sha256(rebound_raw).hexdigest() != prepared["raw_sha256"]
            or _json_mapping(rebound_raw, code="semantic_source_manifest_invalid")
            != manifest
        ):
            raise ValueError("semantic_source_manifest_changed_after_archive_verify")
        campaign_contract = manifest["archive"]["campaign_manifest"]
        campaign_bound = evidence.bind(
            Path(str(campaign_contract["path"])),
            code="semantic_archive_campaign_manifest_unreadable",
        )
        campaign_raw = campaign_bound.read_bytes()
        if (
            len(campaign_raw) != campaign_contract["bytes"]
            or hashlib.sha256(campaign_raw).hexdigest()
            != campaign_contract["sha256"]
        ):
            raise ValueError("semantic_archive_campaign_identity_mismatch")
        receipt_contract = manifest["archive"]["verification_receipt"]
        receipt_bound = evidence.bind(
            Path(str(receipt_contract["path"])),
            code="semantic_archive_verification_receipt_unreadable",
        )
        receipt_raw = receipt_bound.read_bytes()
        if (
            len(receipt_raw) != receipt_contract["bytes"]
            or hashlib.sha256(receipt_raw).hexdigest()
            != receipt_contract["sha256"]
            or _json_mapping(
                receipt_raw,
                code="semantic_archive_verification_receipt_invalid",
            )
            != archive_report
        ):
            raise ValueError("semantic_archive_verification_receipt_mismatch")

        terminal_snapshot_contract = manifest["archive"][
            "terminal_checkpoint_snapshot"
        ]
        terminal_snapshot_bound = evidence.bind(
            Path(str(terminal_snapshot_contract["path"])),
            code="semantic_archive_checkpoint_snapshot_invalid",
        )
        terminal_snapshot_raw = terminal_snapshot_bound.read_bytes()
        if (
            len(terminal_snapshot_raw) != terminal_snapshot_contract["bytes"]
            or hashlib.sha256(terminal_snapshot_raw).hexdigest()
            != terminal_snapshot_contract["sha256"]
        ):
            raise ValueError("semantic_archive_checkpoint_snapshot_invalid")
        terminal_snapshot = _json_mapping(
            terminal_snapshot_raw,
            code="semantic_archive_checkpoint_snapshot_invalid",
        )
        arm_binding = terminal_snapshot.get(
            "b7_5_selection_sizing_factorial_arm_binding"
        )
        if (
            not isinstance(arm_binding, Mapping)
            or arm_binding.get("arm_id") != source_identity["arm_id"]
            or arm_binding.get("arm_fingerprint_sha256")
            != source_identity["arm_fingerprint_sha256"]
        ):
            raise ValueError("semantic_archive_source_identity_mismatch")

        loaded: dict[str, list[dict[str, Any]]] = {}
        for role in _FILE_ROLES:
            contract = manifest["files"][role]
            bound = evidence.bind(
                Path(str(contract["path"])),
                code=f"semantic_source_{role}_unreadable",
            )
            rows, observed = _jsonl_rows_and_contract(
                bound.read_bytes(),
                Path(str(contract["path"])),
                role=role,
            )
            if observed != contract:
                raise ValueError(f"semantic_source_identity_mismatch:{role}")
            loaded[role] = rows
        evidence.assert_paths_unchanged()

    for role in _FILE_ROLES:
        _validate_source_rows(
            role=role,
            rows=loaded[role],
            campaign_id=campaign_id,
            profile=profile,
            campaign_days=campaign_days,
        )
    for role in _ARCHIVE_ROLES:
        _validate_source_rows(
            role=role,
            rows=archive_rows[role],
            campaign_id=campaign_id,
            profile=profile,
            campaign_days=campaign_days,
        )
        expected_rows = manifest["archive"]["cumulative_surfaces"][role]["rows"]
        if len(archive_rows[role]) != expected_rows:
            raise ValueError(f"semantic_archive_row_count_mismatch:{role}")
        loaded[role] = archive_rows[role]
    return loaded


def _bind_primary_order_preimages(
    order_rows: Sequence[Mapping[str, Any]],
    preimage_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    bound_orders = [dict(row) for row in order_rows]
    seen_indexes: set[int] = set()
    for index, preimage in enumerate(preimage_rows):
        persisted_index = preimage.get("persisted_order_stream_index")
        sequence = preimage.get("selected_order_sequence")
        owner = preimage.get("owner")
        if (
            preimage.get("selected_order_attempt_primary") is not True
            or type(persisted_index) is not int
            or persisted_index < 0
            or persisted_index >= len(bound_orders)
            or persisted_index in seen_indexes
            or type(sequence) is not int
            or sequence < 1
            or not isinstance(owner, Mapping)
        ):
            raise ValueError(f"semantic_order_binding_invalid:{index}")
        exact_order = bound_orders[persisted_index]
        if (
            _FORBIDDEN_EXACT_ORDER_FIELDS.intersection(exact_order)
            or preimage.get("persisted_order_row_sha256")
            != canonical_sha256(exact_order)
            or preimage.get("execution_packet_sidecar_id")
            != exact_order.get("execution_packet_sidecar_id")
            or owner.get("campaign") != exact_order.get("campaign")
            or owner.get("profile")
            != (
                exact_order.get("profile")
                or exact_order.get("broad_replay_profile")
            )
            or owner.get("decision_window_id")
            != exact_order.get("decision_window_id")
            or owner.get("canonical_replay_candidate_instance_key")
            != exact_order.get("canonical_replay_candidate_instance_key")
            or owner.get("candidate_id") != exact_order.get("candidate_id")
            or owner.get("simulated_order_id")
            != exact_order.get("simulated_order_id")
            or owner.get("decision_time_utc")
            != exact_order.get("decision_time_utc")
        ):
            raise ValueError(f"semantic_order_binding_mismatch:{index}")
        exact_order.update(
            {
                "selected_order_attempt_primary": True,
                "selected_order_sequence": sequence,
                "semantic_order_preimage_schema": preimage.get("schema"),
                "semantic_order_preimage_sha256": preimage.get(
                    "sidecar_payload_sha256"
                ),
                "semantic_execution_manager_packet_sha256": preimage.get(
                    "semantic_execution_manager_packet_sha256"
                ),
            }
        )
        seen_indexes.add(persisted_index)
    return bound_orders


def _manifest_archive_path(prepared: Mapping[str, Any]) -> Path:
    manifest = prepared.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("semantic_source_manifest_invalid")
    return Path(str(manifest["archive"]["campaign_manifest"]["path"]))


def run_production_semantic_diagnostic(
    *,
    reference_source_manifest_path: Path,
    accelerated_source_manifest_path: Path,
) -> dict[str, Any]:
    """Verify two source-bound archives first, then compare their semantics."""

    reference_prepared = _prepare_source_manifest(
        Path(reference_source_manifest_path)
    )
    accelerated_prepared = _prepare_source_manifest(
        Path(accelerated_source_manifest_path)
    )

    # Both archive walks and their role consumption complete before any direct
    # candidate/order/trade/oracle/proof file is opened.
    reference_archive, reference_archive_report = _verified_archive_rows(
        _manifest_archive_path(reference_prepared)
    )
    accelerated_archive, accelerated_archive_report = _verified_archive_rows(
        _manifest_archive_path(accelerated_prepared)
    )

    reference_manifest = reference_prepared["manifest"]
    accelerated_manifest = accelerated_prepared["manifest"]
    if (
        reference_manifest["comparison_scope"][
            "comparison_scope_root_sha256"
        ]
        != accelerated_manifest["comparison_scope"][
            "comparison_scope_root_sha256"
        ]
    ):
        raise ValueError("semantic_source_comparison_scope_mismatch")

    reference_source = _load_authenticated_source(
        reference_prepared,
        reference_archive,
        reference_archive_report,
    )
    accelerated_source = _load_authenticated_source(
        accelerated_prepared,
        accelerated_archive,
        accelerated_archive_report,
    )
    profile = str(reference_manifest["source_identity"]["profile"])
    campaign_days = _exact_campaign_days(reference_manifest["calendar"]["days"])
    reference_orders = _bind_primary_order_preimages(
        reference_source["order"],
        reference_source["order_preimage"],
    )
    accelerated_orders = _bind_primary_order_preimages(
        accelerated_source["order"],
        accelerated_source["order_preimage"],
    )

    reference_proofs = _produce_semantic_proof_rows(
        campaign_days=campaign_days,
        state_checkpoint_rows=reference_source["state_checkpoint"],
        candidate_rows=reference_source["candidate"],
        missed_rows=reference_source["missed"],
        order_rows=reference_orders,
        trade_rows=reference_source["trade"],
        order_preimage_rows=reference_source["order_preimage"],
    )
    accelerated_proofs = _produce_semantic_proof_rows(
        campaign_days=campaign_days,
        state_checkpoint_rows=accelerated_source["state_checkpoint"],
        candidate_rows=accelerated_source["candidate"],
        missed_rows=accelerated_source["missed"],
        order_rows=accelerated_orders,
        trade_rows=accelerated_source["trade"],
        order_preimage_rows=accelerated_source["order_preimage"],
    )
    comparison = compare_semantic_streams(
        {
            "scorecard": reference_source["scorecard"],
            "order": reference_orders,
            "trade": reference_source["trade"],
            "oracle": reference_source["oracle"],
            "missed": reference_source["missed"],
        },
        {
            "scorecard": accelerated_source["scorecard"],
            "order": accelerated_orders,
            "trade": accelerated_source["trade"],
            "oracle": accelerated_source["oracle"],
            "missed": accelerated_source["missed"],
        },
        reference_proof_rows=reference_proofs,
        accelerated_proof_rows=accelerated_proofs,
        reference_candidate_rows=reference_source["candidate"],
        accelerated_candidate_rows=accelerated_source["candidate"],
        expected_campaign_days=campaign_days,
    )
    adapter_core = {
        "schema": SEMANTIC_DIAGNOSTIC_ADAPTER_SCHEMA,
        "status": comparison["status"],
        "parity_status": comparison["parity_status"],
        "acceptance_authorized": False,
        "diagnostic_complete": comparison["diagnostic_complete"],
        "profile": profile,
        "campaign_days": list(campaign_days),
        "comparison_scope_root_sha256": reference_manifest[
            "comparison_scope"
        ]["comparison_scope_root_sha256"],
        "comparison": comparison,
        "reference_archive_verification_root_sha256": (
            reference_archive_report["verification_root_sha256"]
        ),
        "accelerated_archive_verification_root_sha256": (
            accelerated_archive_report["verification_root_sha256"]
        ),
        "reference_source_manifest_root_sha256": reference_manifest[
            "source_manifest_root_sha256"
        ],
        "accelerated_source_manifest_root_sha256": accelerated_manifest[
            "source_manifest_root_sha256"
        ],
        "reference_evidence_set_root_sha256": reference_manifest[
            "evidence_set_root_sha256"
        ],
        "accelerated_evidence_set_root_sha256": accelerated_manifest[
            "evidence_set_root_sha256"
        ],
        "exact_persisted_byte_acceptance_delegated": True,
        "economic_values_exposed": False,
    }
    return {
        **adapter_core,
        "adapter_root_sha256": canonical_sha256(adapter_core),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the non-authorizing archive-bound semantic diagnostic."
    )
    parser.add_argument("--reference-source-manifest", type=Path, required=True)
    parser.add_argument("--accelerated-source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = run_production_semantic_diagnostic(
        reference_source_manifest_path=args.reference_source_manifest,
        accelerated_source_manifest_path=args.accelerated_source_manifest,
    )
    _atomic_write_json(args.output, receipt, must_be_new=True)
    return 0


__all__ = [
    "SEMANTIC_SOURCE_MANIFEST_SCHEMA",
    "SEMANTIC_DIAGNOSTIC_ADAPTER_SCHEMA",
    "write_semantic_source_manifest",
    "run_production_semantic_diagnostic",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
