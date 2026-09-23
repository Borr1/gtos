from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

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


MANIFEST_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
AMENDMENT_SCHEMA = "gtos.replay_acceleration.partial_golden_amendment.v1"
SUCCESSOR_MANIFEST_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_manifest.v2"
)
SUCCESSOR_AMENDMENT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_amendment.v2"
)
MANIFEST_GATE = "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
AMENDMENT_GATE = "PROSPECTIVE_ACCELERATED_S0R0_RESEARCH_ROUTE"
MODULE_NAME = "src.research_infra.replay_acceleration_partial_golden"
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

LEDGER_SUFFIXES = {
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
PROGRESS_FIELDS = (
    "chunk_id",
    "profile",
    "split",
    "start_day",
    "end_day",
    "day_count",
)
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


class PartialGoldenError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PartialGoldenError(code)


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


def _regular_file_descriptor(path: Path, code: str) -> tuple[int, tuple[int, int]]:
    try:
        descriptor, identity = open_regular_nofollow(path, code=code)
        return descriptor, (identity.device, identity.inode)
    except ImmutableEvidenceError:
        raise PartialGoldenError(code) from None


def _read_regular_bytes(path: Path, code: str) -> tuple[bytes, tuple[int, int]]:
    try:
        raw, identity = read_regular_nofollow(path, code=code)
        return raw, (identity.device, identity.inode)
    except ImmutableEvidenceError:
        raise PartialGoldenError(code) from None


def _validate_namespace(namespace: Path, output_prefix: str) -> None:
    _require(namespace.is_absolute(), "namespace_path_invalid")
    _require(not _path_has_symlink_component(namespace), "namespace_storage_invalid")
    try:
        state = os.lstat(namespace)
    except OSError as exc:
        raise PartialGoldenError("namespace_storage_invalid") from exc
    _require(stat.S_ISDIR(state.st_mode), "namespace_storage_invalid")
    _require(
        bool(output_prefix)
        and "/" not in output_prefix
        and "\\" not in output_prefix
        and output_prefix not in {".", ".."},
        "output_prefix_invalid",
    )


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "009abcdef" for character in text
    )


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


def _days(start_day: str, end_day: str) -> tuple[str, ...]:
    start = date.fromisoformat(start_day)
    end = date.fromisoformat(end_day)
    _require(start <= end, "invalid_scope")
    rows: list[str] = []
    cursor = start
    while cursor <= end:
        rows.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return tuple(rows)


def _git_blob(git_root: Path, commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=git_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    _require(process.returncode == 0, f"legacy_git_blob_missing:{path}")
    return process.stdout


def _git_head(git_root: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=git_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    _require(process.returncode == 0, "git_head_unavailable")
    return process.stdout.strip()


def _scan_jsonl(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    bytes_read = 0
    blank_rows = 0
    unterminated_rows = 0
    invalid_rows = 0
    non_mapping_rows = 0
    try:
        descriptor, opened = open_regular_nofollow(
            path,
            code="result_surface_storage_invalid",
        )
    except ImmutableEvidenceError:
        raise PartialGoldenError("result_surface_storage_invalid") from None
    identity = (opened.device, opened.inode)
    with os.fdopen(descriptor, "rb") as handle:
        for raw in handle:
            rows += 1
            bytes_read += len(raw)
            digest.update(raw)
            if not raw.strip():
                blank_rows += 1
            if not raw.endswith(b"\n"):
                unterminated_rows += 1
            try:
                value = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid_rows += 1
            else:
                if not isinstance(value, dict):
                    non_mapping_rows += 1
        completed = os.fstat(handle.fileno())
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
        "bytes": bytes_read,
        "rows": rows,
        "sha256": digest.hexdigest(),
        "blank_rows": blank_rows,
        "unterminated_rows": unterminated_rows,
        "invalid_json_rows": invalid_rows,
        "non_mapping_rows": non_mapping_rows,
        "strict_jsonl_framing": not any(
            (blank_rows, unterminated_rows, invalid_rows, non_mapping_rows)
        ),
        "storage_identity": identity,
    }


def _progress_projection(
    partial: Mapping[str, Any], expected_days: Sequence[str]
) -> list[dict[str, Any]]:
    fields = ("chunk_id", "profile", "split", "start_day", "end_day", "day_count")
    rows = [
        {field: row.get(field) for field in fields}
        for row in partial.get("progress_rows") or ()
        if isinstance(row, Mapping)
    ]
    actual_days = [str(row.get("start_day") or "") for row in rows]
    _require(actual_days == list(expected_days), "progress_scope_mismatch")
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
            for row in rows
        ),
        "progress_chunk_shape_invalid",
    )
    _require(
        len({row["chunk_id"] for row in rows}) == len(rows),
        "progress_chunk_identity_duplicate",
    )
    _require(len({str(row["profile"]) for row in rows}) == 1, "profile_drift")
    _require(len({str(row["split"]) for row in rows}) == 1, "split_drift")
    return rows


def _capacity_projection(
    partial: Mapping[str, Any], progress: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    contract = partial.get("capacity_safe_chunk_execution_contract")
    _require(isinstance(contract, Mapping), "capacity_contract_missing")
    checkpoints = contract.get("checkpoints") or ()
    _require(len(checkpoints) == len(progress), "capacity_checkpoint_count_mismatch")
    projected: list[dict[str, Any]] = []
    prior_end: int | None = None
    fields = (
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
    for progress_row, checkpoint in zip(progress, checkpoints, strict=True):
        _require(isinstance(checkpoint, Mapping), "capacity_checkpoint_invalid")
        row = {field: checkpoint.get(field) for field in fields}
        _require(
            all(row[field] == progress_row[field] for field in PROGRESS_FIELDS),
            "capacity_checkpoint_identity_mismatch",
        )
        _require(row["cleanup_status"] == "completed", "chunk_cleanup_incomplete")
        _require(
            row["account_object_continuity"] is True
            and row["broker_object_continuity"] is True
            and row["selected_order_sequence_monotonic"] is True
            and row["explicit_gc_completed"] is True,
            "capacity_checkpoint_continuity_failed",
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
        _require(end_sequence >= start_sequence, "order_sequence_regressed")
        if prior_end is not None:
            _require(start_sequence == prior_end, "order_sequence_handoff_mismatch")
        prior_end = end_sequence
        projected.append(row)
    _require(
        int(contract.get("completed_chunk_count") or 0) == len(progress)
        and int(contract.get("cleanup_checkpoint_count") or 0) == len(progress),
        "capacity_completed_count_mismatch",
    )
    _require(
        contract.get("current_chunk_cleanup_pending") is False
        and contract.get("cleanup_complete_for_all_completed_chunks") is True
        and contract.get("same_account_state_reused_across_chunks") is True
        and contract.get("same_simulated_broker_reused_across_chunks") is True
        and contract.get("selected_order_sequence_monotonic_across_chunks") is True
        and contract.get("completed_chunk_day_scoped_source_caches_released") is True
        and contract.get("completed_replay_source_caches_released") is True
        and contract.get("completed_source_authority_scoped_caches_released") is True,
        "capacity_bounded_cleanup_contract_failed",
    )
    return {
        "original_schema": contract.get("schema"),
        "original_status": contract.get("status"),
        "original_full_scope_valid": contract.get("valid") is True,
        "original_planned_chunk_count": contract.get("planned_chunk_count"),
        "bounded_completed_chunk_count": len(projected),
        "bounded_current_chunk_pending": False,
        "bounded_cleanup_valid": True,
        "checkpoints": projected,
    }


def _source_projection(
    partial: Mapping[str, Any],
    progress: Sequence[Mapping[str, Any]],
    bound_source_digest: str,
) -> dict[str, Any]:
    contract = partial.get("source_authority_chunk_invariance_contract")
    _require(isinstance(contract, Mapping), "source_contract_missing")
    checkpoints = contract.get("checkpoints") or ()
    _require(len(checkpoints) == len(progress), "source_checkpoint_count_mismatch")
    projected: list[dict[str, Any]] = []
    fields = (
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
    for progress_row, checkpoint in zip(progress, checkpoints, strict=True):
        _require(isinstance(checkpoint, Mapping), "source_checkpoint_invalid")
        row = {field: checkpoint.get(field) for field in fields}
        _require(
            row["execution_days"] == [progress_row["start_day"]],
            "source_checkpoint_day_mismatch",
        )
        _require(
            row["profile"] == progress_row["profile"]
            and row["split"] == progress_row["split"],
            "source_checkpoint_identity_mismatch",
        )
        _require(
            all(
                row[field] is True
                for field in (
                    "execution_days_subset_of_source_authority",
                    "source_plan_valid",
                    "source_plan_matches_canonical",
                    "static_sources_match_canonical",
                    "tick_component_sources_match_canonical",
                    "m1_execution_day_authority_matches_canonical",
                )
            ),
            "source_checkpoint_invariance_failed",
        )
        _require(
            int(row["source_plan_resolved_symbol_count"] or 0) == 24
            and row["source_plan_missing_symbols"] == [],
            "source_checkpoint_symbol_coverage_failed",
        )
        _require(
            _is_sha256(row["canonical_source_plan_digest_sha256"])
            and _is_sha256(row["source_plan_digest_sha256"])
            and row["canonical_source_plan_digest_sha256"]
            == row["source_plan_digest_sha256"]
            == bound_source_digest,
            "source_checkpoint_digest_mismatch",
        )
        projected.append(row)
    _require(
        int(contract.get("completed_chunk_count") or 0) == len(progress)
        and int(contract.get("checkpoint_count") or 0) == len(progress),
        "source_completed_count_mismatch",
    )
    _require(
        contract.get("current_chunk_pending") is False
        and contract.get("all_source_plans_valid") is True
        and contract.get("all_chunk_source_plans_match_canonical") is True
        and contract.get("all_execution_days_inside_authority_scope") is True,
        "source_bounded_contract_failed",
    )
    return {
        "original_schema": contract.get("schema"),
        "original_status": contract.get("status"),
        "original_full_scope_valid": contract.get("valid") is True,
        "original_planned_chunk_count": contract.get("planned_chunk_count"),
        "bounded_completed_chunk_count": len(projected),
        "bounded_current_chunk_pending": False,
        "bounded_source_invariance_valid": True,
        "checkpoints": projected,
    }


def _contract_identity(partial: Mapping[str, Any]) -> dict[str, Any]:
    binding = partial.get("b7_5_contract_binding")
    arm = partial.get("b7_5_selection_sizing_factorial_arm_binding")
    shared = partial.get("shared_execution_contract")
    _require(isinstance(binding, Mapping), "binding_missing")
    _require(isinstance(arm, Mapping), "arm_binding_missing")
    _require(isinstance(shared, Mapping), "shared_execution_contract_missing")
    _shared_execution_payload(shared)
    source_digests = list(binding.get("actual_source_plan_digests_sha256") or ())
    _require(binding.get("required") is True and binding.get("valid") is True, "binding_invalid")
    _require(len(source_digests) == 1, "source_digest_cardinality_invalid")
    _require(
        binding.get("actual_shared_execution_contract_digest_sha256")
        == binding.get("expected_shared_execution_contract_digest_sha256")
        == shared.get("shared_execution_contract_digest_sha256"),
        "shared_execution_digest_mismatch",
    )
    _require(
        source_digests[0] == binding.get("expected_source_plan_digest_sha256"),
        "bound_source_digest_mismatch",
    )
    _require(arm.get("arm_id") == "S0R0", "arm_not_s0r0")
    _require(
        arm.get("selection_factor") == "S0"
        and arm.get("sizing_factor") == "R0"
        and arm.get("selection_mode") == "neutral_hash_hard_eligible"
        and arm.get("sizing_mode") == "fixed_equal_account_risk",
        "arm_factor_contract_mismatch",
    )
    _require(
        _is_sha256(arm.get("arm_fingerprint_sha256")),
        "arm_fingerprint_invalid",
    )
    _require(
        _is_sha256(shared.get("shared_execution_contract_digest_sha256"))
        and _is_sha256(source_digests[0]),
        "contract_identity_hash_invalid",
    )
    return {
        "arm_id": "S0R0",
        "arm_fingerprint_sha256": arm.get("arm_fingerprint_sha256"),
        "selection_factor": arm.get("selection_factor"),
        "sizing_factor": arm.get("sizing_factor"),
        "selection_mode": arm.get("selection_mode"),
        "sizing_mode": arm.get("sizing_mode"),
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "source_plan_digest_sha256": source_digests[0],
    }


def _legacy_code_authority(
    partial: Mapping[str, Any], *, git_root: Path, legacy_code_commit: str
) -> dict[str, Any]:
    shared = partial.get("shared_execution_contract")
    _require(isinstance(shared, Mapping), "shared_execution_contract_missing")
    _shared_execution_payload(shared)
    resolved_commit = _immutable_commit(git_root, legacy_code_commit)
    rows = shared.get("code_authority") or ()
    configs = shared.get("config_file_hashes") or {}
    _require(isinstance(rows, list) and rows, "code_authority_missing")
    expected: list[dict[str, str]] = []
    for row in rows:
        _require(isinstance(row, Mapping), "code_authority_row_invalid")
        path = str(row.get("path") or "")
        sha256 = str(row.get("sha256") or "")
        _require(path and len(sha256) == 64, "code_authority_row_invalid")
        actual = hashlib.sha256(
            _git_blob(git_root, resolved_commit, path)
        ).hexdigest()
        _require(actual == sha256, f"legacy_code_hash_mismatch:{path}")
        expected.append({"path": path, "sha256": sha256})
    config_rows: list[dict[str, str]] = []
    _require(isinstance(configs, Mapping), "config_authority_invalid")
    for path, value in sorted(configs.items()):
        sha256 = str(value or "")
        actual = hashlib.sha256(
            _git_blob(git_root, resolved_commit, str(path))
        ).hexdigest()
        _require(actual == sha256, f"legacy_config_hash_mismatch:{path}")
        config_rows.append({"path": str(path), "sha256": sha256})
    projection = {
        "legacy_code_commit": resolved_commit,
        "code_files": expected,
        "config_files": config_rows,
    }
    return {**projection, "authority_root_sha256": _root(projection)}


def _ledger_inventory(
    namespace: Path,
    output_prefix: str,
    partial: Mapping[str, Any],
    *,
    partial_identity: tuple[int, int],
) -> list[dict[str, Any]]:
    expected_counts = partial.get("ledger_write_row_counts_so_far")
    expected_bytes = partial.get("ledger_file_bytes_flushed_before_partial_summary")
    _require(isinstance(expected_counts, Mapping), "ledger_counts_missing")
    _require(isinstance(expected_bytes, Mapping), "ledger_bytes_missing")
    _require(
        set(expected_bytes) == {*LEDGER_SUFFIXES, "summary"}
        and expected_bytes.get("summary") is None,
        "ledger_byte_contract_invalid",
    )
    materialized_roles = [
        role for role in LEDGER_SUFFIXES if expected_bytes.get(role) is not None
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
            partial.get(flag) is (role not in materialized_roles),
            f"ledger_omission_contract_invalid:{role}",
        )

    rows: list[dict[str, Any]] = []
    expected_names = {f"{output_prefix}_PARTIAL_SUMMARY.json"}
    identities = {partial_identity}
    for role, suffix in LEDGER_SUFFIXES.items():
        path = namespace / f"{output_prefix}_{suffix}"
        expected_size = expected_bytes[role]
        if role not in materialized_roles:
            _require(not path.exists(), f"unexpected_ledger_materialized:{role}")
            continue
        expected_count = expected_counts[role]
        _require(
            type(expected_size) is int
            and expected_size >= 0
            and type(expected_count) is int
            and expected_count >= 0,
            f"ledger_contract_type_invalid:{role}",
        )
        expected_names.add(path.name)
        scan = _scan_jsonl(path)
        _require(
            scan["storage_identity"] not in identities,
            "result_surface_storage_invalid",
        )
        identities.add(scan["storage_identity"])
        _require(
            scan["bytes"] == expected_size,
            f"ledger_byte_count_mismatch:{role}",
        )
        _require(
            scan["rows"] == expected_count,
            f"ledger_row_count_mismatch:{role}",
        )
        _require(
            scan["strict_jsonl_framing"] is True,
            f"ledger_framing_invalid:{role}",
        )
        rows.append(
            {
                "role": role,
                "name": path.name,
                "bytes": scan["bytes"],
                "rows": scan["rows"],
                "sha256": scan["sha256"],
            }
        )
    matching = {
        path.name
        for path in namespace.iterdir()
        if path.name.startswith(output_prefix + "_")
    }
    _require(matching == expected_names, "namespace_inventory_mismatch")
    return rows


def _self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return _root(projection)


def build_partial_golden_manifest(
    *,
    namespace: Path,
    output_prefix: str,
    start_day: str,
    end_day: str,
    legacy_code_commit: str,
    git_root: Path,
    sealed_at_utc: str,
    command_receipt: Sequence[str] = (),
    accepted_acceleration_base: str = "0d4faafc35f5d93ee8a54bc16d4e37b1c137394c",
    successor_authority_path: Path | None = None,
) -> dict[str, Any]:
    namespace = Path(os.path.abspath(namespace))
    git_root = git_root.resolve()
    _validate_namespace(namespace, output_prefix)
    partial_path = namespace / f"{output_prefix}_PARTIAL_SUMMARY.json"
    partial_raw, partial_identity = _read_regular_bytes(
        partial_path, "partial_summary_storage_invalid"
    )
    try:
        partial = json.loads(partial_raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PartialGoldenError("partial_summary_invalid_json") from exc
    _require(isinstance(partial, Mapping), "partial_summary_not_mapping")
    _require(
        partial.get("status") == "partial_in_progress_not_final_proof",
        "partial_summary_status_invalid",
    )
    _require(partial.get("output_prefix") == output_prefix, "prefix_mismatch")
    expected_days = _days(start_day, end_day)
    _require(expected_days == AUTHORIZED_DAYS, "authorized_scope_mismatch")
    _require(
        type(sealed_at_utc) is str
        and sealed_at_utc.endswith("Z")
        and "T" in sealed_at_utc,
        "sealed_at_utc_invalid",
    )
    progress = _progress_projection(partial, expected_days)
    identity = _contract_identity(partial)
    successor_authority: dict[str, Any] | None = None
    if successor_authority_path is not None:
        try:
            successor_verification = verify_successor_authority(
                Path(successor_authority_path)
            )
            contract_split = split_shared_execution_contract(
                partial["shared_execution_contract"]
            )
        except (SuccessorAuthorityError, ContractSplitError) as exc:
            raise PartialGoldenError(
                f"successor_authority_invalid:{exc}"
            ) from None
        _require(
            successor_verification.get("opaque_result_surface_root_sha256")
            is not None,
            "successor_authority_invalid",
        )
        identity = {
            **identity,
            "economic_execution_contract_digest_sha256": contract_split[
                "economic_execution_contract_digest_sha256"
            ],
        }
        successor_authority = {
            "path": str(Path(successor_authority_path).absolute()),
            "file_sha256": successor_verification[
                "authority_file_sha256"
            ],
            "authority_root_sha256": successor_verification[
                "authority_root_sha256"
            ],
            "verification_root_sha256": successor_verification[
                "verification_root_sha256"
            ],
            "predecessor_golden_root_sha256": successor_verification[
                "predecessor_golden_root_sha256"
            ],
        }
    capacity = _capacity_projection(partial, progress)
    source = _source_projection(
        partial, progress, str(identity["source_plan_digest_sha256"])
    )
    _require(
        partial.get("profiles_requested") == [progress[0]["profile"]],
        "partial_summary_identity_mismatch",
    )
    _require(
        capacity["original_planned_chunk_count"]
        == source["original_planned_chunk_count"]
        and type(capacity["original_planned_chunk_count"]) is int
        and capacity["original_planned_chunk_count"] >= len(expected_days),
        "checkpoint_planned_count_mismatch",
    )
    code_authority = _legacy_code_authority(
        partial,
        git_root=git_root,
        legacy_code_commit=legacy_code_commit,
    )
    ledgers = _ledger_inventory(
        namespace,
        output_prefix,
        partial,
        partial_identity=partial_identity,
    )
    result_surface_projection = [
        {
            "role": row["role"],
            "name": row["name"],
            "bytes": row["bytes"],
            "rows": row["rows"],
            "sha256": row["sha256"],
        }
        for row in ledgers
    ]
    checkpoint_projection = {
        "scope_days": list(expected_days),
        "progress": progress,
        "capacity": capacity,
        "source": source,
    }
    scope = {
        "start_day": start_day,
        "end_day": end_day,
        "days": list(expected_days),
        "day_count": len(expected_days),
        "arm_id": "S0R0",
        "profile": progress[0]["profile"],
        "split": progress[0]["split"],
        "bounded_golden_only": True,
        "full_month_completion_claim": False,
    }
    partial_summary = {
        "name": partial_path.name,
        "bytes": len(partial_raw),
        "sha256": hashlib.sha256(partial_raw).hexdigest(),
        "original_status": partial.get("status"),
        "original_global_contracts_remain_incomplete": True,
    }
    golden_projection = {
        "scope": scope,
        "contract_identity": identity,
        "legacy_code_authority_root_sha256": code_authority[
            "authority_root_sha256"
        ],
        "partial_summary": partial_summary,
        "checkpoint_projection_root_sha256": _root(checkpoint_projection),
        "opaque_result_surface_root_sha256": _root(result_surface_projection),
        **(
            {
                "successor_authority_root_sha256": successor_authority[
                    "authority_root_sha256"
                ]
            }
            if successor_authority is not None
            else {}
        ),
    }
    manifest: dict[str, Any] = {
        "schema": (
            SUCCESSOR_MANIFEST_SCHEMA
            if successor_authority is not None
            else MANIFEST_SCHEMA
        ),
        "gate": MANIFEST_GATE,
        "sealed_at_utc": sealed_at_utc,
        "authority_update": AUTHORITY_UPDATE,
        "scope": scope,
        "outcome_blindness": {
            "semantic_result_values_emitted": False,
            "persisted_result_files_hashed_as_opaque_bytes": True,
            "manifest_contains_only_structural_counts_and_identities": True,
        },
        "namespace": {
            "path": str(namespace),
            "output_prefix": output_prefix,
            "inventory_exact": True,
            "legacy_evidence_modified": False,
        },
        "accepted_acceleration_base": accepted_acceleration_base,
        "sealer_head_commit": _git_head(git_root),
        "contract_identity": identity,
        "legacy_code_authority": code_authority,
        "partial_summary": partial_summary,
        "bounded_checkpoint_contract": checkpoint_projection,
        "persisted_result_surfaces": result_surface_projection,
        "checkpoint_projection_root_sha256": golden_projection[
            "checkpoint_projection_root_sha256"
        ],
        "opaque_result_surface_root_sha256": golden_projection[
            "opaque_result_surface_root_sha256"
        ],
        "golden_root_sha256": _root(golden_projection),
        "command_receipt": list(command_receipt),
        **(
            {"successor_authority": successor_authority}
            if successor_authority is not None
            else {}
        ),
    }
    manifest["manifest_self_root_sha256"] = _self_root(
        manifest, "manifest_self_root_sha256"
    )
    return manifest


def build_prospective_amendment(manifest: Mapping[str, Any]) -> dict[str, Any]:
    scope = manifest.get("scope")
    _require(
        isinstance(scope, Mapping)
        and scope.get("start_day") == AUTHORIZED_DAYS[0]
        and scope.get("end_day") == AUTHORIZED_DAYS[-1]
        and scope.get("days") == list(AUTHORIZED_DAYS)
        and scope.get("day_count") == len(AUTHORIZED_DAYS)
        and scope.get("arm_id") == "S0R0",
        "authorized_scope_mismatch",
    )
    is_successor = manifest.get("schema") == SUCCESSOR_MANIFEST_SCHEMA
    _require(
        manifest.get("schema") in {MANIFEST_SCHEMA, SUCCESSOR_MANIFEST_SCHEMA},
        "manifest_schema_invalid",
    )
    successor_authority = manifest.get("successor_authority")
    _require(
        (not is_successor and successor_authority is None)
        or (
            is_successor
            and isinstance(successor_authority, Mapping)
            and _is_sha256(successor_authority.get("authority_root_sha256"))
        ),
        "successor_authority_invalid",
    )
    amendment: dict[str, Any] = {
        "schema": (
            SUCCESSOR_AMENDMENT_SCHEMA if is_successor else AMENDMENT_SCHEMA
        ),
        "gate": AMENDMENT_GATE,
        "authority_update": manifest["authority_update"],
        "partial_golden": {
            "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
            "golden_root_sha256": manifest["golden_root_sha256"],
            "scope": manifest["scope"],
            "contract_identity": manifest["contract_identity"],
            **(
                {
                    "successor_authority_root_sha256": successor_authority[
                        "authority_root_sha256"
                    ]
                }
                if is_successor
                else {}
            ),
        },
        "permissions": {
            "actual_accelerated_s0r0_research_equivalence_jan_1_7": True,
            "same_state_s0r0_research_continuation_jan_8_31": (
                "CONDITIONAL_ON_INDEPENDENT_EXACT_FULL_RESULT_PARITY"
            ),
            "other_arms": False,
            "broker_live_vps_deployment": False,
            "legacy_evidence_mutation": False,
        },
        "parity_required_surfaces": list(PARITY_REQUIRED_SURFACES),
        "activation": {
            "jan_1_7_research_equivalence": "ACTIVE_AFTER_INDEPENDENT_GOLDEN_SEAL",
            "jan_8_31_continuation": "NOT_ACTIVE_UNTIL_EXACT_PARITY",
            "integrated_acceleration_commit": None,
            "integrated_execution_contract_root_sha256": None,
        },
    }
    amendment["amendment_self_root_sha256"] = _self_root(
        amendment, "amendment_self_root_sha256"
    )
    return amendment


def write_partial_golden_manifest(path: Path, value: Mapping[str, Any]) -> None:
    try:
        immutable_write_bytes(
            path,
            _canonical_bytes(value),
            code="immutable_output_exists_or_storage_invalid",
        )
    except ImmutableEvidenceError:
        raise PartialGoldenError(
            "immutable_output_exists_or_storage_invalid"
        ) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--start-day", required=True)
    parser.add_argument("--end-day", required=True)
    parser.add_argument("--legacy-code-commit", required=True)
    parser.add_argument("--git-root", type=Path, default=Path.cwd())
    parser.add_argument("--sealed-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--amendment-output", type=Path, required=True)
    parser.add_argument("--successor-authority", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    receipt = [sys.executable, "-m", MODULE_NAME, *(argv or sys.argv[1:])]
    manifest = build_partial_golden_manifest(
        namespace=args.namespace,
        output_prefix=args.output_prefix,
        start_day=args.start_day,
        end_day=args.end_day,
        legacy_code_commit=args.legacy_code_commit,
        git_root=args.git_root,
        sealed_at_utc=args.sealed_at_utc,
        command_receipt=receipt,
        successor_authority_path=args.successor_authority,
    )
    amendment = build_prospective_amendment(manifest)
    write_partial_golden_manifest(args.output, manifest)
    write_partial_golden_manifest(args.amendment_output, amendment)
    print(
        json.dumps(
            {
                "gate": manifest["gate"],
                "golden_root_sha256": manifest["golden_root_sha256"],
                "manifest": str(args.output),
                "amendment": str(args.amendment_output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
