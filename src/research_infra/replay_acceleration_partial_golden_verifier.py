from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    immutable_write_bytes,
    open_regular_nofollow,
    read_regular_nofollow,
)
from src.research_infra.replay_acceleration_contract_split import (
    ContractSplitError,
    split_shared_execution_contract,
)
from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
    SuccessorAuthorityError,
    verify_successor_authority,
)


EXPECTED_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
SUCCESSOR_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v2"
EXPECTED_GATE = "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
ACCEPTED_GATE = "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED"
AMENDMENT_SCHEMA = "gtos.replay_acceleration.partial_golden_amendment.v1"
SUCCESSOR_AMENDMENT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_amendment.v2"
)
AMENDMENT_GATE = "PROSPECTIVE_ACCELERATED_S0R0_RESEARCH_ROUTE"
AMENDMENT_ACCEPTED_GATE = "PROSPECTIVE_AMENDMENT_INDEPENDENTLY_ACCEPTED"
SHARED_EXECUTION_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.shared_execution_contract.v1"
)
SHARED_EXECUTION_PAYLOAD_KEYS = frozenset(
    {
        "schema",
        "code_authority",
        "missing_code_paths",
        "effective_profile_config_hashes",
        "effective_profile_config_hash_semantics",
        "config_file_hashes",
        "ultimate_package_runtime_input_contract",
        "active_replay_symbol_universe",
        "execution_options",
        "window_identity_excluded_from_shared_digest",
        "broker_live_final_authority",
    }
)
SHARED_EXECUTION_CONTRACT_KEYS = frozenset(
    {
        *SHARED_EXECUTION_PAYLOAD_KEYS,
        "valid",
        "status",
        "shared_execution_contract_digest_sha256",
    }
)
MANIFEST_KEYS = frozenset(
    {
        "schema",
        "gate",
        "sealed_at_utc",
        "authority_update",
        "scope",
        "outcome_blindness",
        "namespace",
        "accepted_acceleration_base",
        "sealer_head_commit",
        "contract_identity",
        "legacy_code_authority",
        "partial_summary",
        "bounded_checkpoint_contract",
        "persisted_result_surfaces",
        "checkpoint_projection_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_root_sha256",
        "command_receipt",
        "manifest_self_root_sha256",
    }
)
SUCCESSOR_MANIFEST_KEYS = MANIFEST_KEYS | {"successor_authority"}
SCOPE_KEYS = frozenset(
    {
        "start_day",
        "end_day",
        "days",
        "day_count",
        "arm_id",
        "profile",
        "split",
        "bounded_golden_only",
        "full_month_completion_claim",
    }
)
CONTRACT_IDENTITY_KEYS = frozenset(
    {
        "arm_id",
        "arm_fingerprint_sha256",
        "selection_factor",
        "sizing_factor",
        "selection_mode",
        "sizing_mode",
        "shared_execution_contract_digest_sha256",
        "source_plan_digest_sha256",
    }
)
SUCCESSOR_CONTRACT_IDENTITY_KEYS = CONTRACT_IDENTITY_KEYS | {
    "economic_execution_contract_digest_sha256"
}
PROGRESS_KEYS = frozenset(
    {"chunk_id", "profile", "split", "start_day", "end_day", "day_count"}
)
CAPACITY_CHECKPOINT_KEYS = frozenset(
    {
        *PROGRESS_KEYS,
        "cleanup_status",
        "account_object_continuity",
        "broker_object_continuity",
        "selected_order_sequence_monotonic",
        "starting_order_sequence",
        "ending_order_sequence",
        "explicit_gc_completed",
    }
)
SOURCE_CHECKPOINT_KEYS = frozenset(
    {
        "profile",
        "split",
        "execution_days",
        "execution_days_subset_of_source_authority",
        "source_plan_valid",
        "source_plan_matches_canonical",
        "static_sources_match_canonical",
        "tick_component_sources_match_canonical",
        "m1_execution_day_authority_matches_canonical",
        "source_plan_resolved_symbol_count",
        "source_plan_missing_symbols",
        "canonical_source_plan_digest_sha256",
        "source_plan_digest_sha256",
    }
)
AMENDMENT_KEYS = frozenset(
    {
        "schema",
        "gate",
        "authority_update",
        "partial_golden",
        "permissions",
        "parity_required_surfaces",
        "activation",
        "amendment_self_root_sha256",
    }
)
AUTHORIZED_DAYS = (
    "2026-01-01",
    "2026-01-02",
    "2026-01-03",
    "2026-01-04",
    "2026-01-05",
    "2026-01-06",
    "2026-01-07",
)
AUTHORITY_UPDATE = "BORHEN_2026_07_19_PARTIAL_GOLDEN_ACCELERATED_S0R0"
RESULT_SURFACE_SUFFIXES = {
    "source": "SOURCE_UNIVERSE_LEDGER.jsonl",
    "decision": "DECISION_LEDGER.jsonl",
    "candidate": "CANDIDATE_LEDGER.jsonl",
    "candidate_index": "CANDIDATE_INDEX_LEDGER.jsonl",
    "scorecard": "SCORECARD_LEDGER.jsonl",
    "order": "ORDER_LEDGER.jsonl",
    "trade": "TRADE_LEDGER.jsonl",
    "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "BUCKET_LEDGER.jsonl",
    "comparison": "COMPARISON_LEDGER.jsonl",
    "packet_sidecar": "PACKET_SIDECAR_LEDGER.jsonl",
}
PARITY_REQUIRED_SURFACES = (
    "source",
    "candidate_identity_and_union",
    "ordering",
    "decisions",
    "misses",
    "scorecards",
    "orders",
    "trades",
    "lifecycle_and_replacement",
    "account_and_broker_terminal_state",
    "reservations",
    "complete_persisted_result_bytes",
)
CAPACITY_SCHEMA = (
    "gtos.final_moonshot.broad_replay.capacity_safe_chunk_execution.v2"
)
CAPACITY_STATUS = "capacity_safe_chunk_execution_in_progress"
SOURCE_SCHEMA = (
    "gtos.final_moonshot.broad_replay.source_authority_chunk_invariance.v2"
)
SOURCE_STATUS = "source_authority_chunk_invariance_incomplete"
RFC3339_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


class PartialGoldenVerificationError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PartialGoldenVerificationError(code)


def _encoded(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "009abcdef" for character in text
    )


def _is_commit(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 40
        and all(character in "009abcdef" for character in value)
    )


def _strict_nonnegative_int(value: Any, code: str) -> int:
    _require(type(value) is int and value >= 0, code)
    return value


def _strict_string(value: Any, code: str) -> str:
    _require(type(value) is str and bool(value), code)
    return value


def _strict_day(value: Any, code: str) -> str:
    text = _strict_string(value, code)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise PartialGoldenVerificationError(code) from exc
    _require(parsed.isoformat() == text, code)
    return text


def _strict_utc_timestamp(value: Any, code: str) -> str:
    text = _strict_string(value, code)
    _require(RFC3339_UTC.fullmatch(text) is not None, code)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise PartialGoldenVerificationError(code) from exc
    _require(parsed.isoformat().endswith("+00:00"), code)
    return text


def _safe_filename(value: Any, code: str) -> str:
    text = _strict_string(value, code)
    path = PurePosixPath(text)
    _require(
        path.name == text
        and "/" not in text
        and "\\" not in text
        and text not in {".", ".."},
        code,
    )
    return text


def _lexical_absolute_path(value: Any, code: str) -> Path:
    text = _strict_string(value, code)
    path = Path(text)
    _require(
        path.is_absolute()
        and os.path.normpath(text) == text
        and all(part not in {"", ".", ".."} for part in path.parts[1:]),
        code,
    )
    return path


def _path_has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            if stat.S_ISLNK(os.lstat(current).st_mode):
                return True
        except FileNotFoundError:
            return False
    return False


def _regular_file_descriptor(
    path: Path, code: str
) -> tuple[int, tuple[int, int]]:
    try:
        descriptor, identity = open_regular_nofollow(path, code=code)
        return descriptor, (identity.device, identity.inode)
    except ImmutableEvidenceError:
        raise PartialGoldenVerificationError(code) from None


def _read_regular_bytes(
    path: Path, code: str
) -> tuple[bytes, tuple[int, int]]:
    try:
        raw, identity = read_regular_nofollow(path, code=code)
        return raw, (identity.device, identity.inode)
    except ImmutableEvidenceError:
        raise PartialGoldenVerificationError(code) from None


def _canonical_inventory_path(value: Any) -> str:
    _require(type(value) is str and bool(value), "shared_inventory_path_invalid")
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and path.as_posix() == value
        and "\\" not in value
        and all(part not in {"", ".", ".."} for part in path.parts),
        "shared_inventory_path_invalid",
    )
    return value


def _shared_execution_payload(shared: Mapping[str, Any]) -> dict[str, Any]:
    _require(
        set(shared) == SHARED_EXECUTION_CONTRACT_KEYS,
        "shared_execution_contract_schema_invalid",
    )
    _require(
        shared.get("schema") == SHARED_EXECUTION_CONTRACT_SCHEMA
        and shared.get("valid") is True
        and shared.get("status") == "shared_execution_contract_bound"
        and shared.get("missing_code_paths") == []
        and shared.get("window_identity_excluded_from_shared_digest") is True,
        "shared_execution_contract_schema_invalid",
    )
    code_rows = shared.get("code_authority")
    config_hashes = shared.get("config_file_hashes")
    active_symbols = shared.get("active_replay_symbol_universe")
    effective_hashes = shared.get("effective_profile_config_hashes")
    _require(
        isinstance(code_rows, list)
        and bool(code_rows)
        and isinstance(config_hashes, Mapping)
        and isinstance(active_symbols, list)
        and bool(active_symbols)
        and active_symbols == sorted(set(active_symbols))
        and isinstance(effective_hashes, Mapping)
        and bool(effective_hashes),
        "shared_execution_contract_schema_invalid",
    )
    inventory_paths: list[str] = []
    for row in code_rows:
        _require(
            isinstance(row, Mapping) and set(row) == {"path", "sha256"},
            "code_authority_row_invalid",
        )
        path = _canonical_inventory_path(row.get("path"))
        _require(_is_sha256(row.get("sha256")), "code_authority_row_invalid")
        inventory_paths.append(path)
    for path, digest in config_hashes.items():
        inventory_paths.append(_canonical_inventory_path(path))
        _require(_is_sha256(digest), "config_authority_invalid")
    _require(
        len(inventory_paths) == len(set(inventory_paths)),
        "shared_inventory_duplicate_path",
    )
    _require(
        all(type(name) is str and bool(name) for name in effective_hashes)
        and all(_is_sha256(value) for value in effective_hashes.values()),
        "shared_effective_config_hash_invalid",
    )
    payload = {
        key: shared[key] for key in SHARED_EXECUTION_PAYLOAD_KEYS
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _require(
        shared.get("shared_execution_contract_digest_sha256") == digest,
        "shared_execution_digest_recompute_mismatch",
    )
    return payload


def _immutable_commit(git_root: Path, value: str) -> str:
    commit = str(value or "")
    _require(
        len(commit) in {40, 64}
        and all(character in "009abcdef" for character in commit),
        "legacy_code_commit_not_immutable",
    )
    process = subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
        cwd=git_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    _require(
        process.returncode == 0 and process.stdout.strip() == commit,
        "legacy_code_commit_not_immutable",
    )
    return commit


def _file_digest(path: Path) -> str:
    state = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            state.update(block)
    return state.hexdigest()


def _exact_keys(value: Any, expected: frozenset[str], code: str) -> None:
    _require(isinstance(value, Mapping), code)
    _require(set(value) == expected, code)


def _mapping_rows(value: Any, keys: frozenset[str], code: str) -> None:
    _require(isinstance(value, list), code)
    for row in value:
        _exact_keys(row, keys, code)


def _validate_manifest_schema(manifest: Mapping[str, Any]) -> None:
    is_successor = manifest.get("schema") == SUCCESSOR_SCHEMA
    _require(
        manifest.get("schema") in {EXPECTED_SCHEMA, SUCCESSOR_SCHEMA},
        "manifest_schema_mismatch",
    )
    _exact_keys(
        manifest,
        SUCCESSOR_MANIFEST_KEYS if is_successor else MANIFEST_KEYS,
        "manifest_unknown_fields",
    )
    _exact_keys(manifest.get("scope"), SCOPE_KEYS, "scope_unknown_fields")
    _exact_keys(
        manifest.get("outcome_blindness"),
        frozenset(
            {
                "semantic_result_values_emitted",
                "persisted_result_files_hashed_as_opaque_bytes",
                "manifest_contains_only_structural_counts_and_identities",
            }
        ),
        "outcome_blindness_unknown_fields",
    )
    _exact_keys(
        manifest.get("namespace"),
        frozenset(
            {
                "path",
                "output_prefix",
                "inventory_exact",
                "legacy_evidence_modified",
            }
        ),
        "namespace_unknown_fields",
    )
    _exact_keys(
        manifest.get("contract_identity"),
        (
            SUCCESSOR_CONTRACT_IDENTITY_KEYS
            if is_successor
            else CONTRACT_IDENTITY_KEYS
        ),
        "contract_identity_unknown_fields",
    )
    if is_successor:
        _exact_keys(
            manifest.get("successor_authority"),
            frozenset(
                {
                    "path",
                    "file_sha256",
                    "authority_root_sha256",
                    "verification_root_sha256",
                    "predecessor_golden_root_sha256",
                }
            ),
            "successor_authority_unknown_fields",
        )
    authority = manifest.get("legacy_code_authority")
    _exact_keys(
        authority,
        frozenset(
            {
                "legacy_code_commit",
                "code_files",
                "config_files",
                "authority_root_sha256",
            }
        ),
        "legacy_code_authority_unknown_fields",
    )
    _mapping_rows(
        authority.get("code_files"),
        frozenset({"path", "sha256"}),
        "code_authority_unknown_fields",
    )
    _mapping_rows(
        authority.get("config_files"),
        frozenset({"path", "sha256"}),
        "config_authority_unknown_fields",
    )
    _exact_keys(
        manifest.get("partial_summary"),
        frozenset(
            {
                "name",
                "bytes",
                "sha256",
                "original_status",
                "original_global_contracts_remain_incomplete",
            }
        ),
        "partial_summary_unknown_fields",
    )
    checkpoint = manifest.get("bounded_checkpoint_contract")
    _exact_keys(
        checkpoint,
        frozenset({"scope_days", "progress", "capacity", "source"}),
        "checkpoint_contract_unknown_fields",
    )
    _mapping_rows(
        checkpoint.get("progress"),
        PROGRESS_KEYS,
        "progress_unknown_fields",
    )
    capacity = checkpoint.get("capacity")
    _exact_keys(
        capacity,
        frozenset(
            {
                "original_schema",
                "original_status",
                "original_full_scope_valid",
                "original_planned_chunk_count",
                "bounded_completed_chunk_count",
                "bounded_current_chunk_pending",
                "bounded_cleanup_valid",
                "checkpoints",
            }
        ),
        "capacity_unknown_fields",
    )
    _mapping_rows(
        capacity.get("checkpoints"),
        CAPACITY_CHECKPOINT_KEYS,
        "capacity_checkpoint_unknown_fields",
    )
    source = checkpoint.get("source")
    _exact_keys(
        source,
        frozenset(
            {
                "original_schema",
                "original_status",
                "original_full_scope_valid",
                "original_planned_chunk_count",
                "bounded_completed_chunk_count",
                "bounded_current_chunk_pending",
                "bounded_source_invariance_valid",
                "checkpoints",
            }
        ),
        "source_unknown_fields",
    )
    _mapping_rows(
        source.get("checkpoints"),
        SOURCE_CHECKPOINT_KEYS,
        "source_checkpoint_unknown_fields",
    )
    _mapping_rows(
        manifest.get("persisted_result_surfaces"),
        frozenset({"role", "name", "bytes", "rows", "sha256"}),
        "result_surface_unknown_fields",
    )
    _require(
        isinstance(manifest.get("command_receipt"), list)
        and all(isinstance(value, str) for value in manifest["command_receipt"]),
        "command_receipt_invalid",
    )


def _validate_manifest_leaf_types(manifest: Mapping[str, Any]) -> None:
    is_successor = manifest.get("schema") == SUCCESSOR_SCHEMA
    _require(
        manifest.get("schema") in {EXPECTED_SCHEMA, SUCCESSOR_SCHEMA},
        "manifest_schema_mismatch",
    )
    _require(manifest.get("gate") == EXPECTED_GATE, "manifest_gate_mismatch")
    _strict_utc_timestamp(manifest.get("sealed_at_utc"), "sealed_at_utc_invalid")
    _require(
        manifest.get("authority_update") == AUTHORITY_UPDATE,
        "authority_update_invalid",
    )
    _require(
        _is_commit(manifest.get("accepted_acceleration_base")),
        "accepted_acceleration_base_invalid",
    )
    _require(
        _is_commit(manifest.get("sealer_head_commit")),
        "sealer_head_commit_invalid",
    )

    scope = manifest["scope"]
    _require(
        scope.get("start_day") == AUTHORIZED_DAYS[0]
        and scope.get("end_day") == AUTHORIZED_DAYS[-1]
        and scope.get("days") == list(AUTHORIZED_DAYS)
        and type(scope.get("day_count")) is int
        and scope.get("day_count") == len(AUTHORIZED_DAYS)
        and scope.get("arm_id") == "S0R0"
        and type(scope.get("bounded_golden_only")) is bool
        and scope.get("bounded_golden_only") is True
        and type(scope.get("full_month_completion_claim")) is bool
        and scope.get("full_month_completion_claim") is False,
        "authorized_scope_mismatch",
    )
    _strict_string(scope.get("profile"), "scope_identity_invalid")
    _strict_string(scope.get("split"), "scope_identity_invalid")
    for day_value in scope["days"]:
        _strict_day(day_value, "authorized_scope_mismatch")

    namespace = manifest["namespace"]
    _lexical_absolute_path(namespace.get("path"), "namespace_path_invalid")
    prefix = _safe_filename(
        namespace.get("output_prefix"), "namespace_output_prefix_invalid"
    )
    _require(not prefix.endswith(".json"), "namespace_output_prefix_invalid")
    _require(
        type(namespace.get("inventory_exact")) is bool
        and namespace.get("inventory_exact") is True
        and type(namespace.get("legacy_evidence_modified")) is bool
        and namespace.get("legacy_evidence_modified") is False,
        "namespace_authority_invalid",
    )

    identity = manifest["contract_identity"]
    _require(
        identity.get("arm_id") == "S0R0"
        and identity.get("selection_factor") == "S0"
        and identity.get("sizing_factor") == "R0"
        and identity.get("selection_mode") == "neutral_hash_hard_eligible"
        and identity.get("sizing_mode") == "fixed_equal_account_risk",
        "contract_identity_invalid",
    )
    for field in (
        "arm_fingerprint_sha256",
        "shared_execution_contract_digest_sha256",
        "source_plan_digest_sha256",
    ):
        _require(_is_sha256(identity.get(field)), "contract_identity_hash_invalid")
    if is_successor:
        _require(
            _is_sha256(
                identity.get("economic_execution_contract_digest_sha256")
            ),
            "contract_identity_hash_invalid",
        )
        successor_authority = manifest["successor_authority"]
        _lexical_absolute_path(
            successor_authority.get("path"),
            "successor_authority_path_invalid",
        )
        for field in (
            "file_sha256",
            "authority_root_sha256",
            "verification_root_sha256",
            "predecessor_golden_root_sha256",
        ):
            _require(
                _is_sha256(successor_authority.get(field)),
                "successor_authority_hash_invalid",
            )

    authority = manifest["legacy_code_authority"]
    _require(
        _is_commit(authority.get("legacy_code_commit")),
        "legacy_code_commit_not_immutable",
    )
    _require(
        _is_sha256(authority.get("authority_root_sha256")),
        "code_authority_root_invalid",
    )
    inventory_paths: list[str] = []
    for row in [*authority["code_files"], *authority["config_files"]]:
        inventory_paths.append(_canonical_inventory_path(row.get("path")))
        _require(_is_sha256(row.get("sha256")), "code_authority_row_invalid")
    _require(
        len(inventory_paths) == len(set(inventory_paths)),
        "code_authority_path_duplicate",
    )

    partial = manifest["partial_summary"]
    _safe_filename(partial.get("name"), "partial_summary_identity_invalid")
    _strict_nonnegative_int(partial.get("bytes"), "partial_summary_size_invalid")
    _require(_is_sha256(partial.get("sha256")), "partial_summary_hash_invalid")
    _require(
        partial.get("original_status") == "partial_in_progress_not_final_proof"
        and type(partial.get("original_global_contracts_remain_incomplete"))
        is bool
        and partial.get("original_global_contracts_remain_incomplete") is True,
        "partial_summary_authority_invalid",
    )

    checkpoint = manifest["bounded_checkpoint_contract"]
    _require(
        checkpoint.get("scope_days") == list(AUTHORIZED_DAYS),
        "checkpoint_scope_invalid",
    )
    progress = checkpoint["progress"]
    _require(
        isinstance(progress, list) and len(progress) == len(AUTHORIZED_DAYS),
        "progress_shape_invalid",
    )
    for row in progress:
        for field in ("chunk_id", "profile", "split"):
            _strict_string(row.get(field), "progress_leaf_invalid")
        _strict_day(row.get("start_day"), "progress_leaf_invalid")
        _strict_day(row.get("end_day"), "progress_leaf_invalid")
        _require(
            type(row.get("day_count")) is int and row.get("day_count") == 1,
            "progress_leaf_invalid",
        )

    capacity = checkpoint["capacity"]
    _require(
        capacity.get("original_schema") == CAPACITY_SCHEMA
        and capacity.get("original_status") == CAPACITY_STATUS
        and type(capacity.get("original_full_scope_valid")) is bool
        and capacity.get("original_full_scope_valid") is False
        and type(capacity.get("bounded_current_chunk_pending")) is bool
        and capacity.get("bounded_current_chunk_pending") is False
        and type(capacity.get("bounded_cleanup_valid")) is bool
        and capacity.get("bounded_cleanup_valid") is True,
        "capacity_contract_invalid",
    )
    planned_count = _strict_nonnegative_int(
        capacity.get("original_planned_chunk_count"),
        "capacity_contract_invalid",
    )
    _require(planned_count >= len(AUTHORIZED_DAYS), "capacity_contract_invalid")
    _require(
        type(capacity.get("bounded_completed_chunk_count")) is int
        and capacity.get("bounded_completed_chunk_count") == len(AUTHORIZED_DAYS)
        and len(capacity["checkpoints"]) == len(AUTHORIZED_DAYS),
        "capacity_contract_invalid",
    )
    for row in capacity["checkpoints"]:
        for field in ("chunk_id", "profile", "split"):
            _strict_string(row.get(field), "capacity_checkpoint_invalid")
        _strict_day(row.get("start_day"), "capacity_checkpoint_invalid")
        _strict_day(row.get("end_day"), "capacity_checkpoint_invalid")
        _require(
            type(row.get("day_count")) is int
            and row.get("day_count") == 1
            and row.get("cleanup_status") == "completed",
            "capacity_checkpoint_invalid",
        )
        for field in (
            "account_object_continuity",
            "broker_object_continuity",
            "selected_order_sequence_monotonic",
            "explicit_gc_completed",
        ):
            _require(type(row.get(field)) is bool, "capacity_checkpoint_invalid")
        _strict_nonnegative_int(
            row.get("starting_order_sequence"), "capacity_checkpoint_invalid"
        )
        _strict_nonnegative_int(
            row.get("ending_order_sequence"), "capacity_checkpoint_invalid"
        )

    source = checkpoint["source"]
    _require(
        source.get("original_schema") == SOURCE_SCHEMA
        and source.get("original_status") == SOURCE_STATUS
        and type(source.get("original_full_scope_valid")) is bool
        and source.get("original_full_scope_valid") is False
        and type(source.get("bounded_current_chunk_pending")) is bool
        and source.get("bounded_current_chunk_pending") is False
        and type(source.get("bounded_source_invariance_valid")) is bool
        and source.get("bounded_source_invariance_valid") is True,
        "source_contract_invalid",
    )
    _require(
        type(source.get("original_planned_chunk_count")) is int
        and source.get("original_planned_chunk_count") == planned_count
        and type(source.get("bounded_completed_chunk_count")) is int
        and source.get("bounded_completed_chunk_count") == len(AUTHORIZED_DAYS)
        and len(source["checkpoints"]) == len(AUTHORIZED_DAYS),
        "source_contract_invalid",
    )
    for row in source["checkpoints"]:
        _strict_string(row.get("profile"), "source_checkpoint_invalid")
        _strict_string(row.get("split"), "source_checkpoint_invalid")
        execution_days = row.get("execution_days")
        _require(
            isinstance(execution_days, list) and len(execution_days) == 1,
            "source_checkpoint_invalid",
        )
        _strict_day(execution_days[0], "source_checkpoint_invalid")
        for field in (
            "execution_days_subset_of_source_authority",
            "source_plan_valid",
            "source_plan_matches_canonical",
            "static_sources_match_canonical",
            "tick_component_sources_match_canonical",
            "m1_execution_day_authority_matches_canonical",
        ):
            _require(type(row.get(field)) is bool, "source_checkpoint_invalid")
        _require(
            type(row.get("source_plan_resolved_symbol_count")) is int
            and row.get("source_plan_resolved_symbol_count") == 24
            and row.get("source_plan_missing_symbols") == [],
            "source_checkpoint_invalid",
        )
        _require(
            _is_sha256(row.get("canonical_source_plan_digest_sha256"))
            and _is_sha256(row.get("source_plan_digest_sha256")),
            "source_checkpoint_invalid",
        )

    surfaces = manifest["persisted_result_surfaces"]
    _require(isinstance(surfaces, list) and bool(surfaces), "result_surfaces_missing")
    for row in surfaces:
        _strict_string(row.get("role"), "result_surface_leaf_invalid")
        _safe_filename(row.get("name"), "result_surface_name_mismatch")
        _strict_nonnegative_int(row.get("bytes"), "result_surface_leaf_invalid")
        _strict_nonnegative_int(row.get("rows"), "result_surface_leaf_invalid")
        _require(_is_sha256(row.get("sha256")), "result_surface_leaf_invalid")
    for field in (
        "checkpoint_projection_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_root_sha256",
        "manifest_self_root_sha256",
    ):
        _require(_is_sha256(manifest.get(field)), "manifest_root_invalid")
    _require(
        isinstance(manifest.get("command_receipt"), list)
        and all(type(value) is str for value in manifest["command_receipt"]),
        "command_receipt_invalid",
    )


def _validate_amendment_schema(amendment: Mapping[str, Any]) -> None:
    is_successor = amendment.get("schema") == SUCCESSOR_AMENDMENT_SCHEMA
    _require(
        amendment.get("schema")
        in {AMENDMENT_SCHEMA, SUCCESSOR_AMENDMENT_SCHEMA},
        "amendment_schema_mismatch",
    )
    _exact_keys(amendment, AMENDMENT_KEYS, "amendment_unknown_fields")
    _exact_keys(
        amendment.get("partial_golden"),
        frozenset(
            {
                "manifest_self_root_sha256",
                "golden_root_sha256",
                "scope",
                "contract_identity",
                *(
                    ("successor_authority_root_sha256",)
                    if is_successor
                    else ()
                ),
            }
        ),
        "amendment_partial_golden_unknown_fields",
    )
    _exact_keys(
        amendment["partial_golden"].get("scope"),
        SCOPE_KEYS,
        "amendment_scope_unknown_fields",
    )
    _exact_keys(
        amendment["partial_golden"].get("contract_identity"),
        (
            SUCCESSOR_CONTRACT_IDENTITY_KEYS
            if is_successor
            else CONTRACT_IDENTITY_KEYS
        ),
        "amendment_contract_identity_unknown_fields",
    )
    _exact_keys(
        amendment.get("permissions"),
        frozenset(
            {
                "actual_accelerated_s0r0_research_equivalence_jan_1_7",
                "same_state_s0r0_research_continuation_jan_8_31",
                "other_arms",
                "broker_live_vps_deployment",
                "legacy_evidence_mutation",
            }
        ),
        "amendment_permissions_unknown_fields",
    )
    _exact_keys(
        amendment.get("activation"),
        frozenset(
            {
                "jan_1_7_research_equivalence",
                "jan_8_31_continuation",
                "integrated_acceleration_commit",
                "integrated_execution_contract_root_sha256",
            }
        ),
        "amendment_activation_unknown_fields",
    )
    _require(
        isinstance(amendment.get("parity_required_surfaces"), list)
        and all(
            isinstance(value, str)
            for value in amendment["parity_required_surfaces"]
        ),
        "amendment_parity_surfaces_invalid",
    )


def _validate_amendment_leaf_types(amendment: Mapping[str, Any]) -> None:
    is_successor = amendment.get("schema") == SUCCESSOR_AMENDMENT_SCHEMA
    _require(
        amendment.get("schema")
        in {AMENDMENT_SCHEMA, SUCCESSOR_AMENDMENT_SCHEMA},
        "amendment_schema_mismatch",
    )
    _require(amendment.get("gate") == AMENDMENT_GATE, "amendment_gate_mismatch")
    _require(
        amendment.get("authority_update") == AUTHORITY_UPDATE,
        "amendment_authority_update_invalid",
    )
    golden = amendment["partial_golden"]
    _require(
        _is_sha256(golden.get("manifest_self_root_sha256"))
        and _is_sha256(golden.get("golden_root_sha256")),
        "amendment_partial_golden_hash_invalid",
    )
    scope = golden["scope"]
    _require(
        scope.get("start_day") == AUTHORIZED_DAYS[0]
        and scope.get("end_day") == AUTHORIZED_DAYS[-1]
        and scope.get("days") == list(AUTHORIZED_DAYS)
        and type(scope.get("day_count")) is int
        and scope.get("day_count") == len(AUTHORIZED_DAYS)
        and scope.get("arm_id") == "S0R0"
        and type(scope.get("profile")) is str
        and bool(scope.get("profile"))
        and type(scope.get("split")) is str
        and bool(scope.get("split"))
        and type(scope.get("bounded_golden_only")) is bool
        and scope.get("bounded_golden_only") is True
        and type(scope.get("full_month_completion_claim")) is bool
        and scope.get("full_month_completion_claim") is False,
        "authorized_scope_mismatch",
    )
    identity = golden["contract_identity"]
    _require(
        identity.get("arm_id") == "S0R0"
        and identity.get("selection_factor") == "S0"
        and identity.get("sizing_factor") == "R0"
        and identity.get("selection_mode") == "neutral_hash_hard_eligible"
        and identity.get("sizing_mode") == "fixed_equal_account_risk"
        and _is_sha256(identity.get("arm_fingerprint_sha256"))
        and _is_sha256(identity.get("shared_execution_contract_digest_sha256"))
        and _is_sha256(identity.get("source_plan_digest_sha256")),
        "amendment_contract_identity_invalid",
    )
    if is_successor:
        _require(
            _is_sha256(
                identity.get("economic_execution_contract_digest_sha256")
            )
            and _is_sha256(
                golden.get("successor_authority_root_sha256")
            ),
            "amendment_successor_authority_invalid",
        )
    permissions = amendment["permissions"]
    _require(
        type(
            permissions.get(
                "actual_accelerated_s0r0_research_equivalence_jan_1_7"
            )
        )
        is bool
        and permissions.get(
            "actual_accelerated_s0r0_research_equivalence_jan_1_7"
        )
        is True
        and permissions.get(
            "same_state_s0r0_research_continuation_jan_8_31"
        )
        == "CONDITIONAL_ON_INDEPENDENT_EXACT_FULL_RESULT_PARITY"
        and type(permissions.get("other_arms")) is bool
        and permissions.get("other_arms") is False
        and type(permissions.get("broker_live_vps_deployment")) is bool
        and permissions.get("broker_live_vps_deployment") is False
        and type(permissions.get("legacy_evidence_mutation")) is bool
        and permissions.get("legacy_evidence_mutation") is False,
        "amendment_permissions_invalid",
    )
    _require(
        amendment.get("parity_required_surfaces")
        == list(PARITY_REQUIRED_SURFACES),
        "parity_surface_contract_mismatch",
    )
    activation = amendment["activation"]
    _require(
        activation.get("jan_1_7_research_equivalence")
        == "ACTIVE_AFTER_INDEPENDENT_GOLDEN_SEAL"
        and activation.get("jan_8_31_continuation")
        == "NOT_ACTIVE_UNTIL_EXACT_PARITY"
        and activation.get("integrated_acceleration_commit") is None
        and activation.get("integrated_execution_contract_root_sha256") is None,
        "amendment_activation_invalid",
    )
    _require(
        _is_sha256(amendment.get("amendment_self_root_sha256")),
        "amendment_self_root_invalid",
    )


def _calendar_days(start: str, end: str) -> list[str]:
    cursor = date.fromisoformat(start)
    final = date.fromisoformat(end)
    _require(cursor <= final, "invalid_scope")
    result: list[str] = []
    while cursor <= final:
        result.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return result


def _scan_lines(path: Path) -> dict[str, Any]:
    sha = hashlib.sha256()
    byte_count = 0
    row_count = 0
    blank = 0
    unterminated = 0
    malformed = 0
    non_object = 0
    try:
        descriptor, opened = open_regular_nofollow(
            path,
            code="result_surface_storage_invalid",
        )
    except ImmutableEvidenceError:
        raise PartialGoldenVerificationError(
            "result_surface_storage_invalid"
        ) from None
    identity = (opened.device, opened.inode)
    with os.fdopen(descriptor, "rb") as source:
        for line in source:
            row_count += 1
            byte_count += len(line)
            sha.update(line)
            blank += int(not line.strip())
            unterminated += int(not line.endswith(b"\n"))
            try:
                decoded = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed += 1
            else:
                non_object += int(not isinstance(decoded, dict))
        completed = os.fstat(source.fileno())
        _require(
            (
                completed.st_dev,
                completed.st_ino,
                completed.st_size,
                completed.st_mtime_ns,
                completed.st_ctime_ns,
                completed.st_nlink,
            )
            == (
                opened.device,
                opened.inode,
                opened.size,
                opened.mtime_ns,
                opened.ctime_ns,
                opened.link_count,
            ),
            "result_surface_changed_during_read",
        )
    return {
        "bytes": byte_count,
        "rows": row_count,
        "sha256": sha.hexdigest(),
        "strict_jsonl_framing": not any((blank, unterminated, malformed, non_object)),
        "storage_identity": identity,
    }


def _project_identity(partial: Mapping[str, Any]) -> dict[str, Any]:
    binding = partial.get("b7_5_contract_binding")
    arm = partial.get("b7_5_selection_sizing_factorial_arm_binding")
    shared = partial.get("shared_execution_contract")
    _require(isinstance(binding, Mapping), "binding_missing")
    _require(isinstance(arm, Mapping), "arm_binding_missing")
    _require(isinstance(shared, Mapping), "shared_contract_missing")
    _shared_execution_payload(shared)
    sources = list(binding.get("actual_source_plan_digests_sha256") or ())
    _require(binding.get("required") is True, "binding_not_required")
    _require(binding.get("valid") is True, "binding_invalid")
    _require(len(sources) == 1, "source_digest_cardinality")
    shared_digest = shared.get("shared_execution_contract_digest_sha256")
    _require(
        shared_digest
        == binding.get("actual_shared_execution_contract_digest_sha256")
        == binding.get("expected_shared_execution_contract_digest_sha256"),
        "shared_digest_mismatch",
    )
    _require(
        sources[0] == binding.get("expected_source_plan_digest_sha256"),
        "source_digest_mismatch",
    )
    _require(arm.get("arm_id") == "S0R0", "wrong_arm")
    _require(
        arm.get("selection_factor") == "S0"
        and arm.get("sizing_factor") == "R0"
        and arm.get("selection_mode") == "neutral_hash_hard_eligible"
        and arm.get("sizing_mode") == "fixed_equal_account_risk",
        "arm_factor_contract_mismatch",
    )
    _require(
        _is_sha256(arm.get("arm_fingerprint_sha256"))
        and _is_sha256(shared_digest)
        and _is_sha256(sources[0]),
        "contract_identity_hash_invalid",
    )
    return {
        "arm_id": "S0R0",
        "arm_fingerprint_sha256": arm.get("arm_fingerprint_sha256"),
        "selection_factor": arm.get("selection_factor"),
        "sizing_factor": arm.get("sizing_factor"),
        "selection_mode": arm.get("selection_mode"),
        "sizing_mode": arm.get("sizing_mode"),
        "shared_execution_contract_digest_sha256": shared_digest,
        "source_plan_digest_sha256": sources[0],
    }


def _project_progress(
    partial: Mapping[str, Any], days: Sequence[str]
) -> list[dict[str, Any]]:
    names = ("chunk_id", "profile", "split", "start_day", "end_day", "day_count")
    result = [
        {name: item.get(name) for name in names}
        for item in partial.get("progress_rows") or ()
        if isinstance(item, Mapping)
    ]
    _require(
        [row.get("start_day") for row in result] == list(days),
        "progress_scope_mismatch",
    )
    _require(
        all(
            type(row["chunk_id"]) is str
            and type(row["profile"]) is str
            and bool(row["profile"])
            and type(row["split"]) is str
            and bool(row["split"])
            and type(row["start_day"]) is str
            and row["start_day"] == row["end_day"]
            and type(row["day_count"]) is int
            and row["day_count"] == 1
            and row["chunk_id"]
            == (
                f"{row['profile']}:{row['split']}:"
                f"{row['start_day']}:{row['end_day']}"
            )
            for row in result
        ),
        "progress_shape_invalid",
    )
    _require(
        len({row["chunk_id"] for row in result}) == len(result),
        "progress_chunk_identity_duplicate",
    )
    _require(len({row["profile"] for row in result}) == 1, "profile_drift")
    _require(len({row["split"] for row in result}) == 1, "split_drift")
    return result


def _project_capacity(
    partial: Mapping[str, Any], progress: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    contract = partial.get("capacity_safe_chunk_execution_contract")
    _require(isinstance(contract, Mapping), "capacity_contract_missing")
    checkpoints = contract.get("checkpoints") or ()
    _require(len(checkpoints) == len(progress), "capacity_count_mismatch")
    names = (
        "chunk_id",
        "profile",
        "split",
        "start_day",
        "end_day",
        "day_count",
        "cleanup_status",
        "account_object_continuity",
        "broker_object_continuity",
        "selected_order_sequence_monotonic",
        "starting_order_sequence",
        "ending_order_sequence",
        "explicit_gc_completed",
    )
    result: list[dict[str, Any]] = []
    previous: int | None = None
    for marker, checkpoint in zip(progress, checkpoints, strict=True):
        _require(isinstance(checkpoint, Mapping), "capacity_checkpoint_invalid")
        row = {name: checkpoint.get(name) for name in names}
        _require(
            all(
                row[field] == marker[field]
                for field in (
                    "chunk_id",
                    "profile",
                    "split",
                    "start_day",
                    "end_day",
                    "day_count",
                )
            ),
            "capacity_identity_mismatch",
        )
        _require(row["cleanup_status"] == "completed", "cleanup_incomplete")
        _require(
            row["account_object_continuity"] is True
            and row["broker_object_continuity"] is True
            and row["selected_order_sequence_monotonic"] is True
            and row["explicit_gc_completed"] is True,
            "capacity_continuity_invalid",
        )
        _require(
            type(row["starting_order_sequence"]) is int
            and row["starting_order_sequence"] >= 0
            and type(row["ending_order_sequence"]) is int
            and row["ending_order_sequence"] >= 0,
            "capacity_checkpoint_sequence_invalid",
        )
        start_sequence = row["starting_order_sequence"]
        end_sequence = row["ending_order_sequence"]
        _require(end_sequence >= start_sequence, "sequence_regression")
        if previous is not None:
            _require(start_sequence == previous, "sequence_handoff_mismatch")
        previous = end_sequence
        result.append(row)
    _require(
        int(contract.get("completed_chunk_count") or 0) == len(result)
        and int(contract.get("cleanup_checkpoint_count") or 0) == len(result),
        "capacity_aggregate_count_mismatch",
    )
    for key in (
        "cleanup_complete_for_all_completed_chunks",
        "same_account_state_reused_across_chunks",
        "same_simulated_broker_reused_across_chunks",
        "selected_order_sequence_monotonic_across_chunks",
        "completed_chunk_day_scoped_source_caches_released",
        "completed_replay_source_caches_released",
        "completed_source_authority_scoped_caches_released",
    ):
        _require(contract.get(key) is True, f"capacity_aggregate_invalid:{key}")
    _require(
        contract.get("current_chunk_cleanup_pending") is False,
        "capacity_chunk_pending",
    )
    return {
        "original_schema": contract.get("schema"),
        "original_status": contract.get("status"),
        "original_full_scope_valid": contract.get("valid") is True,
        "original_planned_chunk_count": contract.get("planned_chunk_count"),
        "bounded_completed_chunk_count": len(result),
        "bounded_current_chunk_pending": False,
        "bounded_cleanup_valid": True,
        "checkpoints": result,
    }


def _project_sources(
    partial: Mapping[str, Any],
    progress: Sequence[Mapping[str, Any]],
    canonical_digest: str,
) -> dict[str, Any]:
    contract = partial.get("source_authority_chunk_invariance_contract")
    _require(isinstance(contract, Mapping), "source_contract_missing")
    checkpoints = contract.get("checkpoints") or ()
    _require(len(checkpoints) == len(progress), "source_count_mismatch")
    names = (
        "profile",
        "split",
        "execution_days",
        "execution_days_subset_of_source_authority",
        "source_plan_valid",
        "source_plan_matches_canonical",
        "static_sources_match_canonical",
        "tick_component_sources_match_canonical",
        "m1_execution_day_authority_matches_canonical",
        "source_plan_resolved_symbol_count",
        "source_plan_missing_symbols",
        "canonical_source_plan_digest_sha256",
        "source_plan_digest_sha256",
    )
    result: list[dict[str, Any]] = []
    truth_fields = names[3:9]
    for marker, checkpoint in zip(progress, checkpoints, strict=True):
        _require(isinstance(checkpoint, Mapping), "source_checkpoint_invalid")
        row = {name: checkpoint.get(name) for name in names}
        _require(
            row["execution_days"] == [marker["start_day"]],
            "source_checkpoint_day_mismatch",
        )
        _require(
            row["profile"] == marker["profile"]
            and row["split"] == marker["split"],
            "source_checkpoint_identity_mismatch",
        )
        _require(all(row[key] is True for key in truth_fields), "source_invariance_failed")
        _require(
            row["source_plan_resolved_symbol_count"] == 24
            and row["source_plan_missing_symbols"] == [],
            "source_symbol_coverage_failed",
        )
        _require(
            _is_sha256(row["canonical_source_plan_digest_sha256"])
            and _is_sha256(row["source_plan_digest_sha256"])
            and row["canonical_source_plan_digest_sha256"]
            == row["source_plan_digest_sha256"]
            == canonical_digest,
            "source_checkpoint_digest_mismatch",
        )
        result.append(row)
    _require(
        int(contract.get("completed_chunk_count") or 0) == len(result)
        and int(contract.get("checkpoint_count") or 0) == len(result),
        "source_aggregate_count_mismatch",
    )
    _require(contract.get("current_chunk_pending") is False, "source_chunk_pending")
    for key in (
        "all_source_plans_valid",
        "all_chunk_source_plans_match_canonical",
        "all_execution_days_inside_authority_scope",
    ):
        _require(contract.get(key) is True, f"source_aggregate_invalid:{key}")
    return {
        "original_schema": contract.get("schema"),
        "original_status": contract.get("status"),
        "original_full_scope_valid": contract.get("valid") is True,
        "original_planned_chunk_count": contract.get("planned_chunk_count"),
        "bounded_completed_chunk_count": len(result),
        "bounded_current_chunk_pending": False,
        "bounded_source_invariance_valid": True,
        "checkpoints": result,
    }


def _git_object(git_root: Path, commit: str, path: str) -> bytes:
    invocation = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=git_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    _require(invocation.returncode == 0, f"git_blob_missing:{path}")
    return invocation.stdout


def _verify_code_authority(
    manifest: Mapping[str, Any], partial: Mapping[str, Any], git_root: Path
) -> None:
    authority = manifest.get("legacy_code_authority")
    shared = partial.get("shared_execution_contract")
    _require(isinstance(authority, Mapping), "manifest_code_authority_missing")
    _require(isinstance(shared, Mapping), "partial_shared_contract_missing")
    _shared_execution_payload(shared)
    commit = _immutable_commit(
        git_root,
        str(authority.get("legacy_code_commit") or ""),
    )
    partial_code = list(shared.get("code_authority") or ())
    partial_configs = dict(shared.get("config_file_hashes") or {})
    manifest_code = list(authority.get("code_files") or ())
    manifest_configs = list(authority.get("config_files") or ())
    expected_code = [
        {"path": str(row.get("path") or ""), "sha256": str(row.get("sha256") or "")}
        for row in partial_code
        if isinstance(row, Mapping)
    ]
    expected_configs = [
        {"path": str(path), "sha256": str(value)}
        for path, value in sorted(partial_configs.items())
    ]
    _require(manifest_code == expected_code, "code_authority_projection_mismatch")
    _require(manifest_configs == expected_configs, "config_authority_projection_mismatch")
    for row in manifest_code + manifest_configs:
        observed = hashlib.sha256(
            _git_object(git_root, commit, row["path"])
        ).hexdigest()
        _require(observed == row["sha256"], f"git_authority_hash_mismatch:{row['path']}")
    projection = {
        "legacy_code_commit": commit,
        "code_files": manifest_code,
        "config_files": manifest_configs,
    }
    _require(
        authority.get("authority_root_sha256") == _digest(projection),
        "code_authority_root_mismatch",
    )


def _expected_result_surface_contracts(
    partial: Mapping[str, Any], output_prefix: str
) -> list[dict[str, Any]]:
    expected_counts = partial.get("ledger_write_row_counts_so_far")
    expected_bytes = partial.get("ledger_file_bytes_flushed_before_partial_summary")
    _require(isinstance(expected_counts, Mapping), "ledger_counts_missing")
    _require(isinstance(expected_bytes, Mapping), "ledger_bytes_missing")
    _require(
        set(expected_bytes) == {*RESULT_SURFACE_SUFFIXES, "summary"}
        and expected_bytes.get("summary") is None,
        "ledger_byte_contract_invalid",
    )
    materialized_roles = [
        role
        for role in RESULT_SURFACE_SUFFIXES
        if expected_bytes.get(role) is not None
    ]
    _require(
        set(expected_counts) == set(materialized_roles),
        "ledger_count_contract_invalid",
    )
    for role, flag in (
        ("candidate", "candidate_ledger_omitted"),
        ("candidate_index", "candidate_index_ledger_omitted"),
        ("packet_sidecar", "packet_sidecar_ledger_omitted"),
    ):
        _require(
            type(partial.get(flag)) is bool
            and partial.get(flag) is (role not in materialized_roles),
            f"ledger_omission_contract_invalid:{role}",
        )
    result: list[dict[str, Any]] = []
    for role in materialized_roles:
        byte_count = _strict_nonnegative_int(
            expected_bytes[role], f"ledger_contract_type_invalid:{role}"
        )
        row_count = _strict_nonnegative_int(
            expected_counts[role], f"ledger_contract_type_invalid:{role}"
        )
        result.append(
            {
                "role": role,
                "name": f"{output_prefix}_{RESULT_SURFACE_SUFFIXES[role]}",
                "bytes": byte_count,
                "rows": row_count,
            }
        )
    return result


def verify_partial_golden_manifest(
    manifest_path: Path,
    *,
    git_root: Path,
    allowed_namespace_additions: Sequence[str] = (),
) -> dict[str, Any]:
    manifest_path = Path(os.path.abspath(manifest_path))
    _require(
        not _path_has_symlink_component(manifest_path),
        "manifest_storage_invalid",
    )
    raw, _manifest_identity = _read_regular_bytes(
        manifest_path, "manifest_storage_invalid"
    )
    try:
        manifest = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenVerificationError("manifest_invalid_json") from exc
    _require(isinstance(manifest, Mapping), "manifest_not_mapping")
    _validate_manifest_schema(manifest)
    _validate_manifest_leaf_types(manifest)
    _require(raw == _encoded(manifest), "manifest_not_canonical")
    self_projection = dict(manifest)
    self_projection.pop("manifest_self_root_sha256", None)
    _require(
        manifest.get("manifest_self_root_sha256") == _digest(self_projection),
        "manifest_self_root_mismatch",
    )
    _require(
        manifest.get("outcome_blindness")
        == {
            "semantic_result_values_emitted": False,
            "persisted_result_files_hashed_as_opaque_bytes": True,
            "manifest_contains_only_structural_counts_and_identities": True,
        },
        "outcome_blindness_invalid",
    )

    scope = manifest["scope"]
    days = _calendar_days(scope["start_day"], scope["end_day"])
    _require(days == list(AUTHORIZED_DAYS), "authorized_scope_mismatch")
    namespace_record = manifest["namespace"]
    namespace = _lexical_absolute_path(
        namespace_record["path"], "namespace_path_invalid"
    )
    _require(
        not _path_has_symlink_component(namespace),
        "namespace_storage_invalid",
    )
    try:
        namespace_state = os.lstat(namespace)
    except OSError as exc:
        raise PartialGoldenVerificationError("namespace_storage_invalid") from exc
    _require(stat.S_ISDIR(namespace_state.st_mode), "namespace_storage_invalid")
    prefix = namespace_record["output_prefix"]
    partial_record = manifest["partial_summary"]
    expected_partial_name = f"{prefix}_PARTIAL_SUMMARY.json"
    _require(
        partial_record["name"] == expected_partial_name,
        "partial_summary_identity_mismatch",
    )
    partial_path = namespace / expected_partial_name
    partial_raw, partial_identity = _read_regular_bytes(
        partial_path, "partial_summary_storage_invalid"
    )
    _require(
        partial_record["sha256"] == hashlib.sha256(partial_raw).hexdigest(),
        "partial_summary_hash_mismatch",
    )
    _require(
        partial_record["bytes"] == len(partial_raw),
        "partial_summary_size_mismatch",
    )
    try:
        partial = json.loads(partial_raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenVerificationError("partial_summary_invalid_json") from exc
    _require(isinstance(partial, Mapping), "partial_summary_not_mapping")
    _require(partial.get("output_prefix") == prefix, "partial_prefix_mismatch")
    _require(
        partial.get("status") == partial_record["original_status"]
        == "partial_in_progress_not_final_proof",
        "partial_summary_identity_mismatch",
    )

    identity = _project_identity(partial)
    successor_authority_verification: dict[str, Any] | None = None
    if manifest.get("schema") == SUCCESSOR_SCHEMA:
        try:
            contract_split = split_shared_execution_contract(
                partial["shared_execution_contract"]
            )
            successor_authority_verification = verify_successor_authority(
                Path(manifest["successor_authority"]["path"])
            )
        except (ContractSplitError, SuccessorAuthorityError, KeyError):
            raise PartialGoldenVerificationError(
                "successor_authority_invalid"
            ) from None
        identity = {
            **identity,
            "economic_execution_contract_digest_sha256": contract_split[
                "economic_execution_contract_digest_sha256"
            ],
        }
        authority_record = manifest["successor_authority"]
        _require(
            authority_record.get("file_sha256")
            == successor_authority_verification.get("authority_file_sha256")
            and authority_record.get("authority_root_sha256")
            == successor_authority_verification.get("authority_root_sha256")
            and authority_record.get("verification_root_sha256")
            == successor_authority_verification.get("verification_root_sha256")
            and authority_record.get("predecessor_golden_root_sha256")
            == successor_authority_verification.get(
                "predecessor_golden_root_sha256"
            )
            and successor_authority_verification.get(
                "opaque_result_surface_root_sha256"
            )
            == manifest.get("opaque_result_surface_root_sha256"),
            "successor_authority_binding_mismatch",
        )
    _require(manifest["contract_identity"] == identity, "contract_identity_mismatch")
    progress = _project_progress(partial, days)
    _require(
        scope["profile"] == progress[0]["profile"]
        and scope["split"] == progress[0]["split"]
        and partial.get("profiles_requested") == [scope["profile"]],
        "scope_identity_mismatch",
    )
    capacity = _project_capacity(partial, progress)
    sources = _project_sources(
        partial, progress, str(identity["source_plan_digest_sha256"])
    )
    _require(
        capacity["original_planned_chunk_count"]
        == sources["original_planned_chunk_count"]
        and type(capacity["original_planned_chunk_count"]) is int
        and capacity["original_planned_chunk_count"] >= len(days),
        "checkpoint_planned_count_mismatch",
    )
    checkpoint = {
        "scope_days": days,
        "progress": progress,
        "capacity": capacity,
        "source": sources,
    }
    _require(
        manifest["bounded_checkpoint_contract"] == checkpoint,
        "checkpoint_projection_mismatch",
    )
    checkpoint_root = _digest(checkpoint)
    _require(
        manifest["checkpoint_projection_root_sha256"] == checkpoint_root,
        "checkpoint_root_mismatch",
    )

    expected_surfaces = _expected_result_surface_contracts(partial, prefix)
    surfaces = manifest["persisted_result_surfaces"]
    _require(
        len(surfaces) == len(expected_surfaces)
        and all(
            {
                "role": row["role"],
                "name": row["name"],
                "bytes": row["bytes"],
                "rows": row["rows"],
            }
            == expected
            for row, expected in zip(surfaces, expected_surfaces, strict=True)
        ),
        "result_surface_inventory_mismatch",
    )
    names = {expected_partial_name}
    identities = {partial_identity}
    observed: list[dict[str, Any]] = []
    for row in surfaces:
        role = row["role"]
        expected_name = f"{prefix}_{RESULT_SURFACE_SUFFIXES[role]}"
        _require(row["name"] == expected_name, "result_surface_name_mismatch")
        path = namespace / expected_name
        scan = _scan_lines(path)
        _require(
            scan["storage_identity"] not in identities,
            "result_surface_storage_invalid",
        )
        identities.add(scan["storage_identity"])
        _require(scan["sha256"] == row["sha256"], f"ledger_hash_mismatch:{role}")
        _require(scan["bytes"] == row["bytes"], f"ledger_size_mismatch:{role}")
        _require(scan["rows"] == row["rows"], f"ledger_rows_mismatch:{role}")
        _require(
            scan["strict_jsonl_framing"] is True,
            f"ledger_framing_invalid:{role}",
        )
        names.add(expected_name)
        observed.append(
            {
                "role": role,
                "name": expected_name,
                "bytes": scan["bytes"],
                "rows": scan["rows"],
                "sha256": scan["sha256"],
            }
        )

    additions = tuple(allowed_namespace_additions)
    _require(
        len(additions) == len(set(additions)),
        "namespace_addition_contract_invalid",
    )
    for addition in additions:
        _safe_filename(addition, "namespace_addition_contract_invalid")
        _require(
            addition.startswith(prefix + "_") and addition not in names,
            "namespace_addition_contract_invalid",
        )
    inventory = {
        path.name
        for path in namespace.iterdir()
        if path.name.startswith(prefix + "_")
    }
    _require(
        inventory == names | set(additions),
        "namespace_inventory_mismatch",
    )
    surface_root = _digest(observed)
    _require(
        manifest["opaque_result_surface_root_sha256"] == surface_root,
        "result_surface_root_mismatch",
    )
    _verify_code_authority(manifest, partial, git_root.resolve())
    code_root = manifest["legacy_code_authority"]["authority_root_sha256"]
    golden_projection = {
        "scope": dict(scope),
        "contract_identity": identity,
        "legacy_code_authority_root_sha256": code_root,
        "partial_summary": dict(partial_record),
        "checkpoint_projection_root_sha256": checkpoint_root,
        "opaque_result_surface_root_sha256": surface_root,
        **(
            {
                "successor_authority_root_sha256": manifest[
                    "successor_authority"
                ]["authority_root_sha256"]
            }
            if successor_authority_verification is not None
            else {}
        ),
    }
    golden_root = _digest(golden_projection)
    _require(manifest["golden_root_sha256"] == golden_root, "golden_root_mismatch")
    receipt_core = {
        "schema": (
            "gtos.replay_acceleration.partial_golden_verification.v2"
            if successor_authority_verification is not None
            else "gtos.replay_acceleration.partial_golden_verification.v1"
        ),
        "gate": ACCEPTED_GATE,
        "manifest_path": str(manifest_path),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
        "golden_root_sha256": golden_root,
        "checkpoint_projection_root_sha256": checkpoint_root,
        "opaque_result_surface_root_sha256": surface_root,
        "verified_day_count": len(days),
        "verified_result_surface_count": len(observed),
        "verified_namespace_additions": list(additions),
        "semantic_result_values_emitted": False,
        "legacy_evidence_modified": False,
        **(
            {
                "successor_authority_root_sha256": manifest[
                    "successor_authority"
                ]["authority_root_sha256"],
                "successor_authority_verification_root_sha256": (
                    successor_authority_verification[
                        "verification_root_sha256"
                    ]
                ),
                "economic_execution_contract_digest_sha256": identity[
                    "economic_execution_contract_digest_sha256"
                ],
            }
            if successor_authority_verification is not None
            else {}
        ),
    }
    return {
        **receipt_core,
        "verification_root_sha256": _digest(receipt_core),
    }


def verify_prospective_amendment(
    amendment_path: Path,
    manifest_path: Path,
    *,
    git_root: Path | None = None,
) -> dict[str, Any]:
    manifest_verification = verify_partial_golden_manifest(
        manifest_path,
        git_root=(git_root or Path(__file__).resolve().parents[2]),
    )
    amendment_path = Path(os.path.abspath(amendment_path))
    manifest_path = Path(os.path.abspath(manifest_path))
    amendment_raw, _amendment_identity = _read_regular_bytes(
        amendment_path, "amendment_storage_invalid"
    )
    manifest_raw, _manifest_identity = _read_regular_bytes(
        manifest_path, "manifest_storage_invalid"
    )
    _require(
        hashlib.sha256(manifest_raw).hexdigest()
        == manifest_verification["manifest_sha256"],
        "bound_manifest_changed_after_verification",
    )
    try:
        amendment = json.loads(amendment_raw)
        manifest = json.loads(manifest_raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenVerificationError("amendment_or_manifest_invalid_json") from exc
    _require(isinstance(amendment, Mapping), "amendment_not_mapping")
    _require(isinstance(manifest, Mapping), "manifest_not_mapping")
    _validate_amendment_schema(amendment)
    _validate_manifest_schema(manifest)
    _require(amendment_raw == _encoded(amendment), "amendment_not_canonical")
    is_successor = amendment.get("schema") == SUCCESSOR_AMENDMENT_SCHEMA
    _require(
        amendment.get("schema")
        in {AMENDMENT_SCHEMA, SUCCESSOR_AMENDMENT_SCHEMA},
        "amendment_schema_mismatch",
    )
    _require(amendment.get("gate") == AMENDMENT_GATE, "amendment_gate_mismatch")
    amendment_projection = dict(amendment)
    amendment_projection.pop("amendment_self_root_sha256", None)
    _require(
        amendment.get("amendment_self_root_sha256") == _digest(amendment_projection),
        "amendment_self_root_mismatch",
    )
    manifest_projection = dict(manifest)
    manifest_projection.pop("manifest_self_root_sha256", None)
    _require(
        manifest.get("schema") in {EXPECTED_SCHEMA, SUCCESSOR_SCHEMA}
        and manifest.get("gate") == EXPECTED_GATE
        and manifest.get("manifest_self_root_sha256") == _digest(manifest_projection),
        "bound_manifest_invalid",
    )

    golden = amendment.get("partial_golden")
    _require(isinstance(golden, Mapping), "partial_golden_binding_missing")
    _require(
        golden.get("manifest_self_root_sha256")
        == manifest.get("manifest_self_root_sha256")
        and golden.get("golden_root_sha256") == manifest.get("golden_root_sha256")
        and golden.get("scope") == manifest.get("scope")
        and golden.get("contract_identity") == manifest.get("contract_identity"),
        "partial_golden_binding_mismatch",
    )
    if is_successor:
        _require(
            manifest.get("schema") == SUCCESSOR_SCHEMA
            and golden.get("successor_authority_root_sha256")
            == manifest.get("successor_authority", {}).get(
                "authority_root_sha256"
            )
            and manifest_verification.get(
                "successor_authority_root_sha256"
            )
            == golden.get("successor_authority_root_sha256"),
            "successor_authority_binding_mismatch",
        )
    else:
        _require(
            manifest.get("schema") == EXPECTED_SCHEMA,
            "amendment_manifest_schema_mismatch",
        )
    permissions = amendment.get("permissions")
    _require(isinstance(permissions, Mapping), "permissions_missing")
    _require(
        permissions.get("actual_accelerated_s0r0_research_equivalence_jan_1_7")
        is True,
        "bounded_equivalence_not_authorized",
    )
    _require(
        permissions.get("same_state_s0r0_research_continuation_jan_8_31")
        == "CONDITIONAL_ON_INDEPENDENT_EXACT_FULL_RESULT_PARITY",
        "continuation_not_conditional",
    )
    _require(
        permissions.get("other_arms") is False
        and permissions.get("broker_live_vps_deployment") is False
        and permissions.get("legacy_evidence_mutation") is False,
        "prohibited_authority_open",
    )
    activation = amendment.get("activation")
    _require(isinstance(activation, Mapping), "activation_missing")
    _require(
        activation.get("jan_1_7_research_equivalence")
        == "ACTIVE_AFTER_INDEPENDENT_GOLDEN_SEAL",
        "bounded_activation_invalid",
    )
    _require(
        activation.get("jan_8_31_continuation") == "NOT_ACTIVE_UNTIL_EXACT_PARITY",
        "continuation_activation_open",
    )
    _require(
        activation.get("integrated_acceleration_commit") is None
        and activation.get("integrated_execution_contract_root_sha256") is None,
        "unsealed_integration_identity_present",
    )
    _require(
        amendment.get("parity_required_surfaces")
        == list(PARITY_REQUIRED_SURFACES),
        "parity_surface_contract_mismatch",
    )
    _validate_amendment_leaf_types(amendment)
    receipt_core = {
        "schema": (
            "gtos.replay_acceleration.partial_golden_amendment_verification.v2"
            if is_successor
            else "gtos.replay_acceleration.partial_golden_amendment_verification.v1"
        ),
        "gate": AMENDMENT_ACCEPTED_GATE,
        "amendment_sha256": hashlib.sha256(amendment_raw).hexdigest(),
        "amendment_self_root_sha256": amendment["amendment_self_root_sha256"],
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "manifest_verification_root_sha256": manifest_verification[
            "verification_root_sha256"
        ],
        "continuation_authority_active": False,
        "other_arms_authorized": False,
        "broker_live_vps_deployment_authorized": False,
        **(
            {
                "successor_authority_root_sha256": golden[
                    "successor_authority_root_sha256"
                ],
                "successor_authority_verification_root_sha256": (
                    manifest_verification[
                        "successor_authority_verification_root_sha256"
                    ]
                ),
                "economic_execution_contract_digest_sha256": golden[
                    "contract_identity"
                ]["economic_execution_contract_digest_sha256"],
            }
            if is_successor
            else {}
        ),
    }
    return {
        **receipt_core,
        "verification_root_sha256": _digest(receipt_core),
    }


def _write(path: Path, value: Mapping[str, Any]) -> None:
    try:
        immutable_write_bytes(
            path,
            _encoded(value),
            code="immutable_output_exists_or_storage_invalid",
        )
    except ImmutableEvidenceError:
        raise PartialGoldenVerificationError(
            "immutable_output_exists_or_storage_invalid"
        ) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--git-root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--amendment", type=Path)
    parser.add_argument("--amendment-receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    receipt = verify_partial_golden_manifest(args.manifest, git_root=args.git_root)
    if args.receipt:
        _write(args.receipt, receipt)
    output: dict[str, Any] = {"manifest_verification": receipt}
    if args.amendment:
        amendment_receipt = verify_prospective_amendment(
            args.amendment,
            args.manifest,
            git_root=args.git_root,
        )
        output["amendment_verification"] = amendment_receipt
        if args.amendment_receipt:
            _write(args.amendment_receipt, amendment_receipt)
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
