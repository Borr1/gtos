"""Execute sealed B7.5 arms through the accepted post-acceleration engine.

This wrapper exposes only the scientific arm, sealed window/source authority,
fresh output namespace, and immutable prepared-pack/cache locations.  It never
opens broker or live-order authority and calls the generalized replay engine,
not the Task-2 Jan-1-7 acceptance entrypoint.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_fresh_source_authority as fresh_source,
)
from src.research_infra.replay_acceleration_integrated_source import (
    RealReplaySourceAccelerator,
)
from src.research_infra.replay_prepared_day_pack import (
    MANIFEST_NAME,
    PACK_SCHEMA,
    PreparedDayPackError,
    PreparedDayPackReader,
    SEALED_NAME,
    assert_no_factor_reads,
)


ROOT = Path(__file__).resolve().parents[2]
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
PACK_BUILD_ARM_ID = "S1R1"
EXECUTION_SEAL_SCHEMA = "gtos.b7_5.post_acceleration_execution_seal.v1"
EXECUTION_SEAL_STATUS = "SEALED_POST_ACCELERATION_EXECUTION_CONTRACT_VALID"
PACK_BUILD_SEAL_SCHEMA = "gtos.b7_5.post_acceleration_pack_build_seal.v1"
PACK_BUILD_SEAL_STATUS = "SEALED_POST_ACCELERATION_PACK_BUILD_ONLY_VALID"
RUN_RECEIPT_SCHEMA = "gtos.b7_5.post_acceleration_arm_execution.v1"
PREPARED_PACK_RECEIPT_SCHEMA = "gtos.b7_5.post_acceleration_prepared_pack.v1"
PREPARED_PACK_REBIND_SCHEMA = (
    "gtos.b7_5.post_acceleration_prepared_pack_rebind_authority.v2"
)
PREPARED_PACK_REBIND_STATUS = (
    "POST_ACCELERATION_PREPARED_PACK_REBOUND_TO_CURRENT_CONTRACT"
)
PROFILE = replay.PROFILE_REPAIRED
MAX_SHARD_BYTES = 128 * 1024 * 1024
COMPLETED_REPLAY_STATUS = "broad_live_as_if_replay_materialized_broker_live_closed"
PARTIAL_SUMMARY_STATUS = "partial_in_progress_not_final_proof"
ARM_ARTIFACT_SUFFIXES = {
    "source": "_SOURCE_UNIVERSE_LEDGER.jsonl",
    "decision": "_DECISION_LEDGER.jsonl",
    "scorecard": "_SCORECARD_LEDGER.jsonl",
    "order": "_ORDER_LEDGER.jsonl",
    "trade": "_TRADE_LEDGER.jsonl",
    "oracle": "_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "_BUCKET_LEDGER.jsonl",
    "comparison": "_COMPARISON_LEDGER.jsonl",
    "partial_summary": "_PARTIAL_SUMMARY.json",
    "summary": "_SUMMARY.json",
}
ARM_JSONL_ROLES = tuple(
    role
    for role in ARM_ARTIFACT_SUFFIXES
    if role not in {"partial_summary", "summary"}
)
_SAFE_OUTPUT_PREFIX = re.compile(r"[A-Za-z0-9_]+")
SOURCE_SELECTION_REBIND_EXCLUSIONS = (
    {
        "path": "selection_command",
        "reason": (
            "invocation provenance only; the retained projection binds the selected "
            "day, source ledger, membership, ordering, paths, hashes, sizes, and "
            "stable file identity"
        ),
    },
    {
        "path": "selection_root_sha256",
        "reason": (
            "derived from the complete selection including selection_command; "
            "semantic_projection_sha256 independently binds every retained field"
        ),
    },
    {
        "path": "physical_partitions[*].source_stat.ctime_ns",
        "reason": (
            "declared observational noncausal file metadata; content identity remains "
            "bound by device, inode, byte_count, mtime_ns, and exact source SHA256"
        ),
    },
    {
        "path": "physical_partitions[*].source_identity.source_stat.ctime_ns",
        "reason": (
            "duplicate declared observational noncausal file metadata; the complete "
            "stable source identity and exact content SHA256 remain retained"
        ),
    },
)

RUNNER_OPTIONS = {
    "profile": PROFILE,
    "chunk_size": 1,
    "max_candidates_per_symbol_window": 0,
    "smoke_subset": False,
    "skip_tick_source": False,
    "use_native_h1": False,
    "omit_candidate_ledger": True,
    "omit_candidate_index_ledger": True,
    "omit_packet_sidecar_ledger": True,
    "compact_missed_ledger": True,
    "compact_decision_ledger": True,
    "compact_scorecard_ledger": True,
    "compact_event_sink": True,
    "compact_event_max_shard_bytes": MAX_SHARD_BYTES,
    "prepared_day_pack": True,
    "candidate_relational_union": True,
    "gc_between_chunks": True,
    "source_prewarm_workers": 4,
    "broker_adapter": "SimulatedBroker",
    "broker_live_authority": False,
    "broker_mutation_enabled": False,
    "real_order_transmission_possible": False,
}
_PACK_SHARED_SEMANTIC_FIELDS = (
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
)


class PostAccelerationRunnerError(RuntimeError):
    """A Phase-C execution or contract failed closed."""


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
        raise PostAccelerationRunnerError(code)


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    target = Path(path)
    try:
        payload = json.loads(target.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PostAccelerationRunnerError(code) from exc
    _require(isinstance(payload, dict), code)
    return payload


def self_hash(payload: Mapping[str, Any], field: str) -> str:
    projection = copy.deepcopy(dict(payload))
    projection.pop(field, None)
    return stable_sha256(projection)


def source_selection_rebind_projection(
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only explicitly declared noncausal selection volatility."""

    _require(
        selection.get("schema") == "gtos.replay_acceleration.slice_selection.v1"
        and selection.get("status") == "PROSPECTIVE_SOURCE_SELECTION_SEALED"
        and selection.get("source_only") is True
        and selection.get("policy_execution_entered") is False
        and _is_sha256(selection.get("selection_root_sha256"))
        and isinstance(selection.get("selection_command"), list),
        "source_selection_rebind_scope_invalid",
    )
    stat_contract = selection.get("source_stat_identity_contract")
    _require(
        isinstance(stat_contract, Mapping)
        and stat_contract.get("content_identity_fields")
        == ["device", "inode", "byte_count", "mtime_ns"]
        and stat_contract.get("content_sha256_required") is True
        and stat_contract.get("observational_noncausal_fields") == ["ctime_ns"],
        "source_selection_rebind_stat_contract_invalid",
    )
    projection = copy.deepcopy(dict(selection))
    projection.pop("selection_command")
    projection.pop("selection_root_sha256")
    partitions = projection.get("physical_partitions")
    _require(
        isinstance(partitions, list) and bool(partitions),
        "source_selection_rebind_partition_inventory_invalid",
    )
    for index, partition in enumerate(partitions):
        _require(
            isinstance(partition, dict),
            f"source_selection_rebind_partition_invalid:{index}",
        )
        identity = partition.get("source_identity")
        stat = partition.get("source_stat")
        identity_stat = (
            identity.get("source_stat") if isinstance(identity, Mapping) else None
        )
        _require(
            isinstance(stat, dict)
            and isinstance(identity_stat, dict)
            and type(stat.get("ctime_ns")) is int
            and type(identity_stat.get("ctime_ns")) is int,
            f"source_selection_rebind_partition_stat_invalid:{index}",
        )
        stat.pop("ctime_ns")
        identity_stat.pop("ctime_ns")
    return projection


def resolve_canonical_window_binding(
    decision_contract: Mapping[str, Any],
    *,
    window_id: str,
    start: str,
    end: str,
    source_plan_digest_sha256: str,
) -> dict[str, Any]:
    """Resolve one exact sealed window; aliases and partial matches fail closed."""

    windows = decision_contract.get("window_source_plan_bindings")
    _require(isinstance(windows, list), "decision_window_inventory_invalid")
    matches = [
        row
        for row in windows
        if isinstance(row, Mapping)
        and row.get("window_id") == window_id
        and row.get("start") == start
        and row.get("end") == end
        and row.get("source_plan_digest_sha256") == source_plan_digest_sha256
    ]
    _require(len(matches) == 1, "execution_window_not_canonical")
    return copy.deepcopy(dict(matches[0]))


def validate_output_prefix(output_prefix: str) -> str:
    """Restrict Phase-C output names to one inert basename."""

    _require(
        isinstance(output_prefix, str)
        and bool(_SAFE_OUTPUT_PREFIX.fullmatch(output_prefix))
        and ".." not in output_prefix
        and "_B7_5_" in output_prefix.upper(),
        "post_acceleration_prefix_invalid",
    )
    return output_prefix


def validate_fresh_output_namespace(output_dir: Path) -> Path:
    """Require a new, non-symlink namespace below the attempt-5 evidence root."""

    root = replay.ATTEMPT5_NAMESPACE_ROOT.resolve()
    requested = Path(output_dir)
    target = requested.resolve(strict=False)
    _require(
        target != root and target.is_relative_to(root),
        "post_acceleration_output_namespace_outside_attempt5",
    )
    relative = target.relative_to(root)
    current = root
    for component in relative.parts[:-1]:
        current = current / component
        if current.exists():
            _require(
                current.is_dir() and not current.is_symlink(),
                "post_acceleration_output_namespace_symlink_component",
            )
    _require(
        not os.path.lexists(target),
        "post_acceleration_output_namespace_not_fresh",
    )
    return target


def _strict_jsonl_row_count(path: Path) -> int:
    count = 0
    with Path(path).open("rb") as handle:
        for index, raw in enumerate(handle):
            _require(raw.endswith(b"\n"), f"arm_artifact_jsonl_framing_invalid:{index}")
            count += 1
    return count


def _zero_order_send_attempts_by_profile(
    summary: Mapping[str, Any],
) -> dict[str, int] | None:
    profiles = summary.get("profiles")
    attempts = summary.get("order_send_attempts")
    if not (
        isinstance(profiles, list)
        and profiles
        and all(isinstance(profile, str) and profile for profile in profiles)
        and len(profiles) == len(set(profiles))
        and type(summary.get("profile_count")) is int
        and summary["profile_count"] == len(profiles)
        and isinstance(attempts, Mapping)
        and set(attempts) == set(profiles)
        and all(type(value) is int and value == 0 for value in attempts.values())
    ):
        return None
    return {profile: int(attempts[profile]) for profile in profiles}


def build_arm_artifact_inventory(
    *,
    namespace: Path,
    output_prefix: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Bind every persisted arm output and reconcile final summary row counts."""

    prefix = validate_output_prefix(output_prefix)
    root = Path(namespace).resolve()
    expected_names = {
        f"{prefix}{suffix}" for suffix in ARM_ARTIFACT_SUFFIXES.values()
    }
    observed_names = {
        path.name
        for path in root.iterdir()
        if path.is_file() or path.is_symlink()
    }
    _require(
        observed_names == expected_names,
        "post_acceleration_output_artifact_set_invalid",
    )
    artifacts: dict[str, Any] = {}
    ledger_counts: dict[str, int] = {}
    for role, suffix in ARM_ARTIFACT_SUFFIXES.items():
        path = root / f"{prefix}{suffix}"
        _require(
            path.is_file() and not path.is_symlink(),
            f"post_acceleration_output_artifact_invalid:{role}",
        )
        row: dict[str, Any] = {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        if role in ARM_JSONL_ROLES:
            row["rows"] = _strict_jsonl_row_count(path)
            ledger_counts[role] = row["rows"]
        else:
            payload = _load_json(path, code=f"arm_{role}_invalid")
            row["status"] = payload.get("status")
        artifacts[role] = row
    summary = _load_json(
        root / f"{prefix}{ARM_ARTIFACT_SUFFIXES['summary']}",
        code="arm_completed_summary_invalid",
    )
    partial = _load_json(
        root / f"{prefix}{ARM_ARTIFACT_SUFFIXES['partial_summary']}",
        code="arm_partial_summary_invalid",
    )
    zero_order_send_attempts = _zero_order_send_attempts_by_profile(summary)
    _require(
        summary.get("status") == COMPLETED_REPLAY_STATUS
        and summary.get("date_start") == start
        and summary.get("date_end") == end
        and summary.get("ledger_write_row_counts") == ledger_counts
        and summary.get("live_broker_authority") is False
        and summary.get("broker_mutation_enabled") is False
        and zero_order_send_attempts is not None,
        "arm_completed_summary_reconciliation_invalid",
    )
    _require(
        partial.get("status") == PARTIAL_SUMMARY_STATUS,
        "arm_partial_summary_status_invalid",
    )
    core = {
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "ledger_row_counts": ledger_counts,
        "completed_summary_status": summary["status"],
        "partial_summary_status": partial["status"],
        "order_send_attempts_by_profile": zero_order_send_attempts,
        "zero_real_order_send_attempts_reconciled": True,
        "all_expected_artifacts_present": True,
        "all_artifacts_regular_non_symlink_files": True,
        "ledger_counts_reconciled_to_completed_summary": True,
    }
    return {**core, "inventory_root_sha256": stable_sha256(core)}


def _placeholder_args(output_dir: Path) -> argparse.Namespace:
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


def decision_contract_arm(
    decision_contract_path: Path,
    arm_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = _load_json(
        decision_contract_path, code="post_acceleration_decision_contract_invalid"
    )
    arms = contract.get("factorial_contract", {}).get("arms", [])
    arm = next(
        (
            row
            for row in arms
            if isinstance(row, Mapping) and row.get("arm_id") == arm_id
        ),
        None,
    )
    _require(isinstance(arm, Mapping), "post_acceleration_arm_missing")
    return contract, dict(arm)


def discover_prepared_pack_roots(
    prepared_day_pack_root: Path,
) -> dict[tuple[str, str, str], str]:
    """Inventory only the exact canonical pack tree, never a matching subset."""

    root = Path(prepared_day_pack_root)
    _require(root.is_dir() and not root.is_symlink(), "prepared_pack_root_invalid")
    result: dict[tuple[str, str, str], str] = {}
    manifest_fields = {
        "schema",
        "status",
        "format",
        "compression",
        "max_shard_bytes",
        "max_record_bytes",
        "target_raw_shard_bytes",
        "bindings",
        "window_inventory",
        "record_count",
        "ordered_record_root_sha256",
        "shards",
        "pack_root_sha256",
    }
    shard_fields = {
        "path",
        "shard_index",
        "row_count",
        "first_record_ordinal",
        "last_record_ordinal",
        "raw_bytes",
        "compressed_bytes",
        "raw_sha256",
        "compressed_sha256",
    }
    try:
        root_entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise PostAccelerationRunnerError("prepared_pack_root_tree_invalid") from exc
    _require(bool(root_entries), "prepared_pack_inventory_empty")
    for split_path in root_entries:
        _require(
            not split_path.is_symlink()
            and split_path.is_dir()
            and bool(re.fullmatch(r"[A-Za-z0-9_-]+", split_path.name)),
            "prepared_pack_root_tree_invalid",
        )
        scope_paths = sorted(split_path.iterdir(), key=lambda path: path.name)
        _require(bool(scope_paths), "prepared_pack_root_tree_invalid")
        for scope_path in scope_paths:
            _require(
                not scope_path.is_symlink()
                and scope_path.is_dir()
                and bool(
                    re.fullmatch(
                        r"\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}",
                        scope_path.name,
                    )
                ),
                "prepared_pack_root_tree_invalid",
            )
            scope_entries = {
                path.name: path
                for path in scope_path.iterdir()
            }
            _require(
                set(scope_entries) == {MANIFEST_NAME, SEALED_NAME, "shards"}
                and all(not path.is_symlink() for path in scope_entries.values())
                and scope_entries[MANIFEST_NAME].is_file()
                and scope_entries[SEALED_NAME].is_file()
                and scope_entries["shards"].is_dir(),
                "prepared_pack_root_tree_invalid",
            )
            manifest_path = scope_entries[MANIFEST_NAME]
            manifest = _load_json(
                manifest_path,
                code="prepared_pack_manifest_invalid",
            )
            bindings = manifest.get("bindings")
            days = tuple(
                str(value)
                for value in (
                    bindings.get("days")
                    if isinstance(bindings, Mapping)
                    else ()
                )
            )
            pack_root = manifest.get("pack_root_sha256")
            shards = manifest.get("shards")
            _require(
                set(manifest) == manifest_fields
                and manifest.get("schema") == PACK_SCHEMA
                and manifest.get("status") == "SEALED"
                and manifest.get("format") == "ordered_canonical_jsonl_shards"
                and manifest.get("compression") == "zstd_level_1"
                and isinstance(bindings, Mapping)
                and bool(days)
                and _is_sha256(pack_root)
                and scope_path.name == f"{days[0]}_{days[-1]}"
                and pack_root
                == stable_sha256(
                    {
                        key: value
                        for key, value in manifest.items()
                        if key != "pack_root_sha256"
                    }
                )
                and isinstance(shards, list)
                and bool(shards),
                "prepared_pack_manifest_scope_invalid",
            )
            try:
                seal_text = scope_entries[SEALED_NAME].read_text(
                    encoding="ascii"
                )
            except (OSError, UnicodeError) as exc:
                raise PostAccelerationRunnerError(
                    "prepared_pack_root_tree_invalid"
                ) from exc
            _require(
                seal_text == f"{pack_root}\n",
                "prepared_pack_root_tree_invalid",
            )
            expected_shards: set[str] = set()
            for shard_index, shard in enumerate(shards):
                expected_name = f"shard-{shard_index:05d}.jsonl.zst"
                _require(
                    isinstance(shard, Mapping)
                    and set(shard) == shard_fields
                    and shard.get("path") == f"shards/{expected_name}"
                    and shard.get("shard_index") == shard_index
                    and _is_sha256(shard.get("raw_sha256"))
                    and _is_sha256(shard.get("compressed_sha256")),
                    "prepared_pack_root_tree_invalid",
                )
                expected_shards.add(expected_name)
            shard_entries = {
                path.name: path
                for path in scope_entries["shards"].iterdir()
            }
            _require(
                set(shard_entries) == expected_shards
                and all(
                    not path.is_symlink() and path.is_file()
                    for path in shard_entries.values()
                )
                and all(
                    shard_entries[f"shard-{index:05d}.jsonl.zst"].stat().st_size
                    == int(shard["compressed_bytes"])
                    for index, shard in enumerate(shards)
                ),
                "prepared_pack_root_tree_invalid",
            )
            key = (split_path.name, days[0], days[-1])
            _require(key not in result, "prepared_pack_duplicate_scope")
            result[key] = str(pack_root)
    _require(bool(result), "prepared_pack_inventory_empty")
    return result


def _serialized_pack_roots(
    roots: Mapping[tuple[str, str, str], str],
) -> dict[str, str]:
    return {
        f"{split}:{start}:{end}": digest
        for (split, start, end), digest in sorted(roots.items())
    }


def build_prepared_pack_source_identity_binding(
    manifest_bindings: Any,
) -> dict[str, Any]:
    """Bind each prepared-pack scope to its exact source-identity root."""

    _require(
        isinstance(manifest_bindings, list) and bool(manifest_bindings),
        "prepared_pack_source_identity_inventory_invalid",
    )
    roots_by_scope: dict[str, str] = {}
    for index, row in enumerate(manifest_bindings):
        _require(
            isinstance(row, Mapping),
            f"prepared_pack_source_identity_row_invalid:{index}",
        )
        split = row.get("split")
        days = row.get("days")
        source_root = row.get("source_identity_root_sha256")
        _require(
            isinstance(split, str)
            and bool(split)
            and isinstance(days, list)
            and len(days) in {1, 2}
            and all(isinstance(day, str) and day for day in days),
            f"prepared_pack_source_identity_scope_invalid:{index}",
        )
        _require(
            _is_sha256(source_root),
            "prepared_pack_source_identity_root_invalid",
        )
        scope = f"{split}:{days[0]}:{days[-1]}"
        _require(
            scope not in roots_by_scope,
            "prepared_pack_source_identity_scope_duplicate",
        )
        roots_by_scope[scope] = str(source_root)
    ordered = dict(sorted(roots_by_scope.items()))
    return {
        "roots_by_scope": ordered,
        "scope_count": len(ordered),
        "all_scope_roots_explicitly_bound": True,
        "binding_root_sha256": stable_sha256(ordered),
    }


def validate_prepared_pack_authority_manifest_roots(
    authority: Mapping[str, Any],
) -> dict[tuple[str, str, str], str]:
    """Recompute roots from manifests instead of trusting a caller dictionary."""

    root = Path(str(authority.get("prepared_day_pack_root") or "")).resolve()
    declared = authority.get("prepared_day_pack_roots")
    _require(
        isinstance(declared, Mapping),
        "prepared_pack_authority_root_inventory_invalid",
    )
    actual = discover_prepared_pack_roots(root)
    _require(
        dict(declared) == _serialized_pack_roots(actual),
        "prepared_pack_authority_manifest_root_mismatch",
    )
    return actual


def build_standard_args(
    *,
    output_dir: Path,
    output_prefix: str,
    window_id: str,
    start: str,
    end: str,
    arm_id: str,
    decision_contract_path: Path,
    source_bundle_dir: Path,
    source_selection_path: Path,
    source_authority_path: Path,
    source_authority_file_sha256: str,
    source_authority_root_sha256: str,
    source_bundle_root_sha256: str,
    source_plan_digest_sha256: str,
    typed_cache_root: Path,
    tick_sparse_cache_root: Path,
    prepared_day_pack_root: Path | None,
    prepared_pack_authority_path: Path | None = None,
    build_prepared_day_pack_root: Path | None = None,
    prepared_day_pack_build_only: bool = False,
) -> argparse.Namespace:
    """Construct the fixed execution surface without free policy controls."""

    _require(arm_id in ARM_ORDER, "post_acceleration_arm_invalid")
    validate_output_prefix(output_prefix)
    contract, arm = decision_contract_arm(decision_contract_path, arm_id)
    canonical_window = resolve_canonical_window_binding(
        contract,
        window_id=window_id,
        start=start,
        end=end,
        source_plan_digest_sha256=source_plan_digest_sha256,
    )
    args = _placeholder_args(Path(output_dir))
    args.window_id = canonical_window["window_id"]
    args.start = start
    args.end = end
    args.max_days = None
    args.chunk_size = RUNNER_OPTIONS["chunk_size"]
    args.output_prefix = output_prefix
    args.profiles = [PROFILE]
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
    args.compact_event_sink = True
    args.compact_event_max_shard_bytes = MAX_SHARD_BYTES
    args.gc_between_chunks = True
    args.finalize_existing_prefix = False
    args.runtime_evidence_root = replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    selection = _load_json(
        source_selection_path,
        code="source_selection_tick_authority_invalid",
    )
    source_ledger = selection.get("source_ledger")
    _require(
        isinstance(source_ledger, Mapping)
        and _is_sha256(source_ledger.get("sha256"))
        and type(source_ledger.get("byte_count")) is int
        and source_ledger.get("byte_count") > 0
        and isinstance(source_ledger.get("consumed_row_counts"), Mapping)
        and int(
            source_ledger["consumed_row_counts"].get(
                "tick_symbol_source"
            )
            or 0
        )
        > 0,
        "source_selection_tick_authority_invalid",
    )
    sealed_tick_ledger = Path(str(source_ledger.get("path") or ""))
    _require(
        sealed_tick_ledger.is_absolute()
        and sealed_tick_ledger.is_file()
        and not sealed_tick_ledger.is_symlink()
        and sealed_tick_ledger.stat().st_size == source_ledger["byte_count"]
        and file_sha256(sealed_tick_ledger) == source_ledger["sha256"],
        "source_selection_tick_authority_invalid",
    )
    args.tick_source_manifest = None
    args.expected_tick_source_manifest_sha256 = None
    args.tick_diagnostic_manifests = []
    args.expected_tick_diagnostic_manifest_sha256s = []
    args.sealed_tick_source_ledger = sealed_tick_ledger
    args.expected_sealed_tick_source_ledger_sha256 = source_ledger["sha256"]
    args.sealed_tick_full_component_set = True
    args.source_acceleration_bundle_dir = Path(source_bundle_dir)
    args.source_acceleration_selection = Path(source_selection_path)
    args.source_bundle_consumer_rebind_authority = Path(source_authority_path)
    args.expected_source_bundle_consumer_rebind_authority_sha256 = (
        source_authority_file_sha256
    )
    args.expected_source_bundle_consumer_rebind_authority_root_sha256 = (
        source_authority_root_sha256
    )
    args.source_acceleration_cache_root = Path(typed_cache_root)
    args.tick_sparse_cache_root = Path(tick_sparse_cache_root)
    args.expected_source_bundle_root_sha256 = source_bundle_root_sha256
    args.expected_source_plan_digest_sha256 = source_plan_digest_sha256
    args.source_prewarm_workers = 4
    args.accepted_physical_reference = False
    args.physical_reference_checkpoint_after_day = None
    args.task2_semantic_checkpoint_after_day = None
    args.parity_gate_after_day = None
    args.parity_gate_request = None
    args.parity_report = None
    args.parity_receipt = None
    args.stop_after_parity_gate = False
    args.streaming_proof_archive_root = None
    args.max_streaming_proof_archive_bytes = 0
    args.decision_contract = Path(decision_contract_path)
    args.arm_id = arm_id
    args.expected_arm_fingerprint_sha256 = arm["arm_fingerprint_sha256"]
    args.expected_economic_execution_contract_sha256 = None
    args.expected_shared_execution_contract_sha256 = None
    args.engineering_stop_after_day = None
    args.tick_sparse_cache_window_end_after_day = None
    args.prepared_day_pack_root = (
        Path(prepared_day_pack_root) if prepared_day_pack_root is not None else None
    )
    args.prepared_pack_authority = (
        Path(prepared_pack_authority_path)
        if prepared_pack_authority_path is not None
        else None
    )
    args.build_prepared_day_pack_root = (
        Path(build_prepared_day_pack_root)
        if build_prepared_day_pack_root is not None
        else None
    )
    args.prepared_day_pack_build_only = bool(prepared_day_pack_build_only)
    args.prepared_pack_encoding_workers = 4
    args.prepared_pack_target_raw_shard_bytes = 32 * 1024 * 1024
    args.expected_prepared_day_pack_roots = (
        discover_prepared_pack_roots(Path(prepared_day_pack_root))
        if prepared_day_pack_root is not None
        else {}
    )
    _require(
        contract.get("authority_boundary", {}).get("broker_mutation_enabled")
        is False,
        "post_acceleration_decision_contract_broker_boundary_invalid",
    )
    return args


def bind_fresh_source(args: argparse.Namespace) -> dict[str, Any]:
    bound = fresh_source.validate_fresh_source_authority(
        authority_path=Path(args.source_bundle_consumer_rebind_authority),
        expected_authority_file_sha256=str(
            args.expected_source_bundle_consumer_rebind_authority_sha256
        ),
        expected_authority_root_sha256=str(
            args.expected_source_bundle_consumer_rebind_authority_root_sha256
        ),
        bundle_dir=Path(args.source_acceleration_bundle_dir),
        selection_path=Path(args.source_acceleration_selection),
        expected_bundle_root_sha256=str(args.expected_source_bundle_root_sha256),
        expected_source_plan_digest_sha256=str(
            args.expected_source_plan_digest_sha256
        ),
    )
    accelerator = RealReplaySourceAccelerator.from_accepted_bundle(
        source_bundle_dir=Path(args.source_acceleration_bundle_dir),
        selection_path=Path(args.source_acceleration_selection),
        typed_cache_root=Path(args.source_acceleration_cache_root),
        expected_bundle_root=str(args.expected_source_bundle_root_sha256),
        expected_source_plan_digest=str(args.expected_source_plan_digest_sha256),
    )
    args.bound_source_bundle_consumer_rebind_authority = bound
    args.source_acceleration_authority = replay.bound_source_acceleration_authority(
        args, accelerator
    )
    return bound


def current_shared_contract(args: argparse.Namespace) -> dict[str, Any]:
    factorial = replay.selection_sizing_factorial_binding_from_args(args)
    _require(isinstance(factorial, Mapping), "factorial_binding_missing")
    profile_configs = {
        profile: replay.build_config(
            profile,
            factorial_arm_binding=factorial,
        )
        for profile in args.profiles
    }
    shared = replay.broad_replay_shared_execution_contract(
        profiles=args.profiles,
        active_symbols=replay.active_replay_symbol_universe(
            replay.requested_replay_symbols(args.symbols)
        ),
        execution_options=replay.broad_replay_execution_options_from_args(
            args,
            factorial_arm_binding=factorial,
        ),
        runtime_input_contract=replay.ultimate_package_runtime_input_contract(),
        factorial_arm_binding=factorial,
        profile_configs=profile_configs,
    )
    _require(shared.get("valid") is True, "shared_execution_contract_invalid")
    return shared


def pack_build_execution_binding(
    *,
    arm_id: str,
    shared: Mapping[str, Any],
    factorial: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the exact build-mode transport that must match before replay."""

    options = shared.get("execution_options")
    _require(
        arm_id == PACK_BUILD_ARM_ID
        and isinstance(options, Mapping)
        and options.get("prepared_day_pack_enabled") is True
        and options.get("prepared_day_pack_build_enabled") is True
        and _is_sha256(shared.get("shared_execution_contract_digest_sha256"))
        and _is_sha256(factorial.get("binding_payload_sha256")),
        "prepared_pack_build_execution_binding_invalid",
    )
    return {
        "arm_id_used_only_for_full_config_construction": arm_id,
        "shared_execution_contract_digest_sha256": shared[
            "shared_execution_contract_digest_sha256"
        ],
        "code_authority_root_sha256": stable_sha256(shared["code_authority"]),
        "exact_profile_config_root_sha256": shared[
            "exact_profile_config_roots_sha256"
        ][PROFILE],
        "factorial_binding_payload_sha256": factorial[
            "binding_payload_sha256"
        ],
        "prepared_day_pack_build_enabled": True,
        "policy_execution_forbidden": True,
    }


def validate_pack_build_execution_binding(
    *,
    seal: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> dict[str, Any]:
    """Require exact equality with the sealed build-mode transport."""

    sealed = seal.get("pack_build_execution_binding")
    _require(
        isinstance(sealed, Mapping)
        and dict(sealed) == dict(actual),
        "prepared_pack_build_execution_binding_mismatch",
    )
    return dict(sealed)


def validate_pack_source_cross_binding(
    *,
    pack_authority: Mapping[str, Any],
    execution_source_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Reject a valid same-window pack made from any other source authority."""

    required = {
        "path",
        "file_sha256",
        "authority_root_sha256",
        "bundle_root_sha256",
        "selection_root_sha256",
        "source_plan_digest_sha256",
        "binding_root_sha256",
    }
    pack_source = pack_authority.get("source_authority_binding")
    execution_projection = {
        key: execution_source_binding.get(key)
        for key in required
    }
    _require(
        isinstance(pack_source, Mapping)
        and set(pack_source) >= required
        and all(_is_sha256(execution_projection[key]) for key in required - {"path"})
        and dict(pack_source) == execution_projection,
        "execution_seal_prepared_pack_source_mismatch",
    )
    return execution_projection


def build_execution_seal(
    *,
    decision_contract_path: Path,
    window_id: str,
    start: str,
    end: str,
    source_plan_digest_sha256: str,
    source_bundle_dir: Path,
    source_selection_path: Path,
    source_authority_path: Path,
    source_authority_file_sha256: str,
    source_authority_root_sha256: str,
    source_bundle_root_sha256: str,
    typed_cache_root: Path,
    tick_sparse_cache_root: Path,
    prepared_pack_authority_path: Path | None,
) -> dict[str, Any]:
    """Compute a pack-build bootstrap or final pack-bound execution seal."""

    replay.configure_runtime_evidence_root(replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    decision_path = Path(decision_contract_path).resolve()
    decision = _load_json(decision_path, code="decision_contract_invalid")
    decision_self_hash = decision.get("self_hash", {}).get("sha256")
    _require(_is_sha256(decision_self_hash), "decision_contract_self_hash_invalid")
    window = resolve_canonical_window_binding(
        decision,
        window_id=window_id,
        start=start,
        end=end,
        source_plan_digest_sha256=source_plan_digest_sha256,
    )
    pack_authority_path = (
        Path(prepared_pack_authority_path).resolve()
        if prepared_pack_authority_path is not None
        else None
    )
    pack_authority = None
    if pack_authority_path is not None:
        pack_authority = validate_prepared_pack_rebind_authority(
            pack_authority_path,
            decision_contract_path=decision_path,
            # Pack-rebind construction already authenticates every logical
            # record and seals the engine receipt.  The final seal rechecks
            # that immutable authority, exact tree, manifests, and hashes
            # without repeating the costly JSON decode of every pack record.
            full_byte_authentication=False,
        )
        _require(
            pack_authority.get("window_binding") == window,
            "execution_seal_prepared_pack_window_mismatch",
        )
    arms_by_id = {
        row["arm_id"]: row
        for row in decision.get("factorial_contract", {}).get("arms", [])
        if isinstance(row, Mapping)
    }
    arm_bindings: dict[str, Any] = {}
    source_binding_roots: set[str] = set()
    for arm_id in ARM_ORDER:
        args = build_standard_args(
            output_dir=ROOT / ".phase-c-contract-placeholder",
            output_prefix=f"BROAD_LIVE_AS_IF_REPLAY_B7_5_CONTRACT_{arm_id}",
            window_id=window_id,
            start=start,
            end=end,
            arm_id=arm_id,
            decision_contract_path=decision_path,
            source_bundle_dir=source_bundle_dir,
            source_selection_path=source_selection_path,
            source_authority_path=source_authority_path,
            source_authority_file_sha256=source_authority_file_sha256,
            source_authority_root_sha256=source_authority_root_sha256,
            source_bundle_root_sha256=source_bundle_root_sha256,
            source_plan_digest_sha256=source_plan_digest_sha256,
            typed_cache_root=typed_cache_root,
            tick_sparse_cache_root=tick_sparse_cache_root,
            prepared_day_pack_root=None,
        )
        # Shared-contract construction needs the feature enabled; exact pack
        # bytes are bound separately by prepared_day_pack_binding below.
        args.prepared_day_pack_root = ROOT / ".phase-c-prepared-pack-placeholder"
        bound_source = bind_fresh_source(args)
        source_binding_roots.add(str(bound_source["binding_root_sha256"]))
        shared = current_shared_contract(args)
        factorial = replay.selection_sizing_factorial_binding_from_args(args)
        arm_bindings[arm_id] = {
            "arm_fingerprint_sha256": arms_by_id[arm_id][
                "arm_fingerprint_sha256"
            ],
            "factorial_binding_payload_sha256": factorial[
                "binding_payload_sha256"
            ],
            "shared_execution_contract_digest_sha256": shared[
                "shared_execution_contract_digest_sha256"
            ],
            "code_authority_root_sha256": stable_sha256(
                shared["code_authority"]
            ),
            "exact_profile_config_root_sha256": shared[
                "exact_profile_config_roots_sha256"
            ][PROFILE],
        }
    authority = _load_json(source_authority_path, code="source_authority_invalid")
    _require(
        len(source_binding_roots) == 1,
        "execution_seal_source_binding_not_unique",
    )
    source_binding = {
        "path": str(Path(source_authority_path).resolve()),
        "file_sha256": source_authority_file_sha256,
        "authority_root_sha256": source_authority_root_sha256,
        "bundle_root_sha256": source_bundle_root_sha256,
        "selection_root_sha256": authority.get("selection", {}).get(
            "selection_root_sha256"
        ),
        "source_plan_digest_sha256": source_plan_digest_sha256,
        "binding_root_sha256": next(iter(source_binding_roots)),
    }
    _require(
        all(_is_sha256(source_binding[key]) for key in source_binding if key != "path"),
        "execution_seal_source_binding_invalid",
    )
    pack_build_binding: dict[str, Any] | None = None
    if pack_authority_path is None:
        build_args = build_standard_args(
            output_dir=ROOT / ".phase-c-pack-build-contract-placeholder",
            output_prefix="BROAD_LIVE_AS_IF_REPLAY_B7_5_PACK_BUILD_CONTRACT",
            window_id=window_id,
            start=start,
            end=end,
            arm_id=PACK_BUILD_ARM_ID,
            decision_contract_path=decision_path,
            source_bundle_dir=source_bundle_dir,
            source_selection_path=source_selection_path,
            source_authority_path=source_authority_path,
            source_authority_file_sha256=source_authority_file_sha256,
            source_authority_root_sha256=source_authority_root_sha256,
            source_bundle_root_sha256=source_bundle_root_sha256,
            source_plan_digest_sha256=source_plan_digest_sha256,
            typed_cache_root=typed_cache_root,
            tick_sparse_cache_root=tick_sparse_cache_root,
            prepared_day_pack_root=None,
            build_prepared_day_pack_root=(
                ROOT / ".phase-c-pack-build-contract-placeholder"
                / "prepared-day-packs"
            ),
            prepared_day_pack_build_only=True,
        )
        build_source = bind_fresh_source(build_args)
        _require(
            build_source["binding_root_sha256"]
            == source_binding["binding_root_sha256"],
            "execution_seal_source_binding_not_unique",
        )
        build_shared = current_shared_contract(build_args)
        build_factorial = replay.selection_sizing_factorial_binding_from_args(
            build_args
        )
        _require(
            isinstance(build_factorial, Mapping),
            "factorial_binding_missing",
        )
        pack_build_binding = pack_build_execution_binding(
            arm_id=PACK_BUILD_ARM_ID,
            shared=build_shared,
            factorial=build_factorial,
        )
        prepared_day_pack_binding = {
            "required": True,
            "arm_neutral": True,
            "factor_reads_forbidden": True,
            "bootstrap_pack_build_only": True,
            "root_sealed_after_contract_before_first_arm": True,
            "policy_execution_forbidden": True,
        }
        schema = PACK_BUILD_SEAL_SCHEMA
        status = PACK_BUILD_SEAL_STATUS
        root_field = "pack_build_seal_root_sha256"
    else:
        _require(
            isinstance(pack_authority, Mapping),
            "execution_seal_prepared_pack_authority_missing",
        )
        validated_source_binding = validate_pack_source_cross_binding(
            pack_authority=pack_authority,
            execution_source_binding=source_binding,
        )
        prepared_day_pack_binding = {
            "required": True,
            "arm_neutral": True,
            "factor_reads_forbidden": True,
            "authority_path": str(pack_authority_path),
            "authority_file_sha256": file_sha256(pack_authority_path),
            "authority_root_sha256": pack_authority["authority_root_sha256"],
            "prepared_day_pack_root": pack_authority[
                "prepared_day_pack_root"
            ],
            "prepared_day_pack_roots": copy.deepcopy(
                pack_authority["prepared_day_pack_roots"]
            ),
            "source_authority_binding": copy.deepcopy(
                validated_source_binding
            ),
            "all_persisted_pack_bytes_authenticated_before_seal": True,
            "old_contract_identities_are_provenance_only": True,
        }
        schema = EXECUTION_SEAL_SCHEMA
        status = EXECUTION_SEAL_STATUS
        root_field = "execution_seal_root_sha256"
    core = {
        "schema": schema,
        "status": status,
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
        "decision_contract_binding": {
            "path": str(decision_path.relative_to(ROOT)),
            "file_sha256": file_sha256(decision_path),
            "self_hash_sha256": decision_self_hash,
            "schema": decision.get("schema"),
            "status": decision.get("status"),
        },
        "window_binding": window,
        "source_authority_binding": {
            **copy.deepcopy(source_binding),
            "fresh_current_bundle": True,
            "policy_execution_entered": False,
        },
        "runner_options": copy.deepcopy(RUNNER_OPTIONS),
        "prepared_day_pack_binding": prepared_day_pack_binding,
        "arms": arm_bindings,
        "all_four_arm_shared_digests_unique": len(
            {
                row["shared_execution_contract_digest_sha256"]
                for row in arm_bindings.values()
            }
        )
        == 4,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    if pack_build_binding is not None:
        core["pack_build_execution_binding"] = pack_build_binding
    _require(core["all_four_arm_shared_digests_unique"], "shared_digests_not_unique")
    return {**core, root_field: stable_sha256(core)}


def build_pack_build_seal(**kwargs: Any) -> dict[str, Any]:
    """Build the replay-free seal accepted only by arm-neutral pack creation."""

    return build_execution_seal(
        **kwargs,
        prepared_pack_authority_path=None,
    )


def validate_pack_build_seal(
    path: Path,
    *,
    decision_contract_path: Path,
    arm_id: str,
) -> dict[str, Any]:
    seal = _load_json(path, code="pack_build_seal_invalid")
    root = seal.get("pack_build_seal_root_sha256")
    binding = seal.get("prepared_day_pack_binding")
    _require(
        seal.get("schema") == PACK_BUILD_SEAL_SCHEMA
        and seal.get("status") == PACK_BUILD_SEAL_STATUS
        and seal.get("valid") is True
        and _is_sha256(root)
        and root == self_hash(seal, "pack_build_seal_root_sha256")
        and seal.get("runner_options") == RUNNER_OPTIONS
        and isinstance(binding, Mapping)
        and binding
        == {
            "required": True,
            "arm_neutral": True,
            "factor_reads_forbidden": True,
            "bootstrap_pack_build_only": True,
            "root_sealed_after_contract_before_first_arm": True,
            "policy_execution_forbidden": True,
        }
        and seal.get("broker_live_authority") is False
        and seal.get("broker_mutation_enabled") is False
        and seal.get("real_order_transmission_possible") is False
        and seal.get("economic_values_exposed") is False,
        "pack_build_seal_invalid",
    )
    decision_path = Path(decision_contract_path).resolve()
    decision = _load_json(decision_path, code="decision_contract_invalid")
    decision_binding = seal.get("decision_contract_binding")
    pack_build_binding = seal.get("pack_build_execution_binding")
    _require(
        isinstance(decision_binding, Mapping)
        and decision_binding.get("file_sha256") == file_sha256(decision_path)
        and decision_binding.get("self_hash_sha256")
        == decision.get("self_hash", {}).get("sha256")
        and arm_id == PACK_BUILD_ARM_ID
        and arm_id in (seal.get("arms") or {})
        and isinstance(pack_build_binding, Mapping)
        and pack_build_binding.get(
            "arm_id_used_only_for_full_config_construction"
        )
        == PACK_BUILD_ARM_ID
        and pack_build_binding.get("prepared_day_pack_build_enabled") is True
        and pack_build_binding.get("policy_execution_forbidden") is True,
        "pack_build_seal_decision_or_arm_mismatch",
    )
    return seal


def validate_execution_seal(
    path: Path,
    *,
    decision_contract_path: Path,
    arm_id: str,
) -> dict[str, Any]:
    seal = _load_json(path, code="execution_seal_invalid")
    root = seal.get("execution_seal_root_sha256")
    _require(
        seal.get("schema") == EXECUTION_SEAL_SCHEMA
        and seal.get("status") == EXECUTION_SEAL_STATUS
        and seal.get("valid") is True
        and _is_sha256(root)
        and root == self_hash(seal, "execution_seal_root_sha256")
        and seal.get("runner_options") == RUNNER_OPTIONS
        and seal.get("broker_live_authority") is False
        and seal.get("broker_mutation_enabled") is False
        and seal.get("real_order_transmission_possible") is False
        and seal.get("economic_values_exposed") is False,
        "execution_seal_invalid",
    )
    decision_path = Path(decision_contract_path).resolve()
    binding = seal.get("decision_contract_binding")
    pack_binding = seal.get("prepared_day_pack_binding")
    _require(
        isinstance(binding, Mapping)
        and binding.get("file_sha256") == file_sha256(decision_path)
        and isinstance(pack_binding, Mapping)
        and arm_id in (seal.get("arms") or {}),
        "execution_seal_decision_or_arm_mismatch",
    )
    pack_authority_path = Path(str(pack_binding.get("authority_path") or "")).resolve()
    pack_authority = validate_prepared_pack_rebind_authority(
        pack_authority_path,
        decision_contract_path=decision_path,
        full_byte_authentication=False,
    )
    source_binding = seal.get("source_authority_binding")
    _require(
        pack_binding.get("authority_file_sha256")
        == file_sha256(pack_authority_path)
        and pack_binding.get("authority_root_sha256")
        == pack_authority.get("authority_root_sha256")
        and pack_binding.get("prepared_day_pack_root")
        == pack_authority.get("prepared_day_pack_root")
        and pack_binding.get("prepared_day_pack_roots")
        == pack_authority.get("prepared_day_pack_roots")
        and isinstance(source_binding, Mapping)
        and pack_binding.get("source_authority_binding")
        == validate_pack_source_cross_binding(
            pack_authority=pack_authority,
            execution_source_binding={
                key: source_binding.get(key)
                for key in (
                    "path",
                    "file_sha256",
                    "authority_root_sha256",
                    "bundle_root_sha256",
                    "selection_root_sha256",
                    "source_plan_digest_sha256",
                    "binding_root_sha256",
                )
            },
        ),
        "execution_seal_prepared_pack_binding_invalid",
    )
    return seal


def validate_args_against_execution_seal(
    args: argparse.Namespace,
    seal: Mapping[str, Any],
) -> None:
    """Fail before replay when any sealed window or source input drifts."""

    window = seal.get("window_binding")
    source = seal.get("source_authority_binding")
    arm = (seal.get("arms") or {}).get(str(args.arm_id))
    _require(
        isinstance(window, Mapping)
        and window.get("window_id") == args.window_id
        and window.get("start") == args.start
        and window.get("end") == args.end
        and window.get("source_plan_digest_sha256")
        == args.expected_source_plan_digest_sha256,
        "execution_seal_window_mismatch",
    )
    _require(
        isinstance(source, Mapping)
        and Path(str(source.get("path") or "")).resolve()
        == Path(args.source_bundle_consumer_rebind_authority).resolve()
        and source.get("file_sha256")
        == args.expected_source_bundle_consumer_rebind_authority_sha256
        and source.get("authority_root_sha256")
        == args.expected_source_bundle_consumer_rebind_authority_root_sha256
        and source.get("bundle_root_sha256")
        == args.expected_source_bundle_root_sha256
        and source.get("source_plan_digest_sha256")
        == args.expected_source_plan_digest_sha256,
        "execution_seal_source_mismatch",
    )
    _require(
        isinstance(arm, Mapping)
        and arm.get("arm_fingerprint_sha256")
        == args.expected_arm_fingerprint_sha256,
        "execution_seal_arm_mismatch",
    )
    pack = seal.get("prepared_day_pack_binding")
    expected_roots = _serialized_pack_roots(args.expected_prepared_day_pack_roots)
    _require(
        args.prepared_day_pack_build_only is True
        or (
            isinstance(pack, Mapping)
            and Path(str(pack.get("authority_path") or "")).resolve()
            == Path(args.prepared_pack_authority).resolve()
            and Path(str(pack.get("prepared_day_pack_root") or "")).resolve()
            == Path(args.prepared_day_pack_root).resolve()
            and pack.get("prepared_day_pack_roots") == expected_roots
        ),
        "execution_seal_prepared_pack_mismatch",
    )


def validate_prepared_pack_builds(
    builds: Any,
    *,
    prepared_day_pack_root: Path,
) -> list[dict[str, Any]]:
    """Authenticate every pack byte and its explicit factor-read audit."""

    root = Path(prepared_day_pack_root).resolve()
    _require(
        isinstance(builds, list) and bool(builds),
        "prepared_pack_build_inventory_invalid",
    )
    validated: list[dict[str, Any]] = []
    seen_scopes: set[tuple[str, tuple[str, ...]]] = set()
    for index, build in enumerate(builds):
        _require(isinstance(build, Mapping), f"prepared_pack_build_invalid:{index}")
        split = str(build.get("split") or "")
        days = tuple(str(value) for value in (build.get("days") or ()))
        reads = build.get("factor_reads")
        _require(
            build.get("status") == "SEALED_ARM_NEUTRAL_PREPARATION"
            and split
            and days
            and isinstance(reads, list)
            and all(isinstance(value, str) and value for value in reads)
            and build.get("factor_reads_detected") is False
            and build.get("account_state_read") is False
            and build.get("broker_state_read") is False
            and build.get("broker_mutation_enabled") is False
            and build.get("live_authority_touched") is False,
            f"prepared_pack_build_contract_invalid:{index}",
        )
        scope = (split, days)
        _require(scope not in seen_scopes, "prepared_pack_build_scope_duplicate")
        seen_scopes.add(scope)
        try:
            assert_no_factor_reads(reads, factor_namespace_absent=True)
        except PreparedDayPackError as exc:
            raise PostAccelerationRunnerError(
                f"prepared_pack_factor_read_detected:{index}"
            ) from exc
        path = Path(str(build.get("path") or "")).resolve()
        expected_path = root / split / f"{days[0]}_{days[-1]}"
        _require(
            path == expected_path and path.is_relative_to(root),
            f"prepared_pack_build_path_mismatch:{index}",
        )
        expected_root = str(build.get("pack_root_sha256") or "")
        try:
            reader = PreparedDayPackReader(
                path,
                expected_pack_root_sha256=expected_root,
            )
            inventory = reader.manifest["window_inventory"]
            for row in inventory:
                reader.next_window(
                    trading_day=str(row["trading_day"]),
                    decision_time_utc=str(row["decision_time_utc"]),
                    window_ordinal=int(row["window_ordinal"]),
                )
            reader.finish()
        except PreparedDayPackError as exc:
            raise PostAccelerationRunnerError(
                f"prepared_pack_byte_authentication_failed:{index}"
            ) from exc
        manifest = reader.manifest
        _require(
            tuple(reader.bindings["days"]) == days
            and int(build.get("record_count") or 0) == manifest["record_count"]
            and int(build.get("shard_count") or 0) == len(manifest["shards"])
            and int(build.get("raw_bytes") or 0)
            == sum(int(row["raw_bytes"]) for row in manifest["shards"])
            and int(build.get("compressed_bytes") or 0)
            == sum(int(row["compressed_bytes"]) for row in manifest["shards"]),
            f"prepared_pack_build_manifest_mismatch:{index}",
        )
        validated.append(
            {
                "split": split,
                "days": list(days),
                "path": str(path),
                "pack_root_sha256": reader.pack_root_sha256,
                "record_count": int(manifest["record_count"]),
                "shard_count": len(manifest["shards"]),
                "raw_bytes": int(build["raw_bytes"]),
                "compressed_bytes": int(build["compressed_bytes"]),
                "factor_read_count": len(reads),
                "factor_reads_detected": False,
                "all_persisted_bytes_authenticated": True,
            }
        )
    return validated


def reconcile_predecessor_pack_build_transport(
    *,
    pack_build_seal_path: Path,
    predecessor_pack_receipt: Mapping[str, Any],
    engine_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate legacy R4's one unsealed build-mode flag without relabeling it."""

    seal_path = Path(pack_build_seal_path).resolve()
    seal = _load_json(seal_path, code="predecessor_pack_build_seal_invalid")
    seal_root = seal.get("pack_build_seal_root_sha256")
    arm_id = predecessor_pack_receipt.get(
        "arm_id_used_only_for_full_config_construction"
    )
    sealed_arm = (
        seal.get("arms", {}).get(arm_id)
        if isinstance(seal.get("arms"), Mapping)
        else None
    )
    shared = engine_receipt.get("shared_execution_contract")
    _require(
        seal.get("schema") == PACK_BUILD_SEAL_SCHEMA
        and seal.get("status") == PACK_BUILD_SEAL_STATUS
        and seal.get("valid") is True
        and _is_sha256(seal_root)
        and seal_root == self_hash(seal, "pack_build_seal_root_sha256")
        and seal_root
        == predecessor_pack_receipt.get("pack_build_seal_root_sha256")
        and arm_id == PACK_BUILD_ARM_ID
        and isinstance(sealed_arm, Mapping)
        and isinstance(shared, Mapping)
        and shared.get("valid") is True
        and shared.get("status") == "shared_execution_contract_bound",
        "predecessor_pack_build_seal_invalid",
    )
    semantic_payload = {
        key: copy.deepcopy(shared.get(key))
        for key in _PACK_SHARED_SEMANTIC_FIELDS
    }
    actual_digest = stable_sha256(semantic_payload)
    execution_options = semantic_payload.get("execution_options")
    _require(
        isinstance(execution_options, Mapping)
        and execution_options.get("prepared_day_pack_enabled") is True
        and execution_options.get("prepared_day_pack_build_enabled") is True
        and actual_digest
        == shared.get("shared_execution_contract_digest_sha256")
        == predecessor_pack_receipt.get(
            "pack_build_shared_execution_contract_digest_sha256"
        ),
        "predecessor_pack_build_actual_digest_invalid",
    )
    consumer_projection = copy.deepcopy(semantic_payload)
    consumer_projection["execution_options"][
        "prepared_day_pack_build_enabled"
    ] = False
    sealed_consumer_digest = stable_sha256(consumer_projection)
    factorial = execution_options.get(
        "b7_5_selection_sizing_factorial_arm"
    )
    _require(isinstance(factorial, Mapping), "predecessor_pack_factorial_invalid")
    actual_binding = pack_build_execution_binding(
        arm_id=str(arm_id),
        shared=shared,
        factorial=factorial,
    )
    directly_sealed = seal.get("pack_build_execution_binding")
    _require(
        (
            (
                isinstance(directly_sealed, Mapping)
                and dict(directly_sealed) == actual_binding
            )
            or (
                directly_sealed is None
                and sealed_consumer_digest
                == sealed_arm.get("shared_execution_contract_digest_sha256")
            )
        )
        and stable_sha256(shared.get("code_authority"))
        == sealed_arm.get("code_authority_root_sha256")
        and shared.get("exact_profile_config_roots_sha256", {}).get(PROFILE)
        == sealed_arm.get("exact_profile_config_root_sha256")
        and factorial.get("arm_id") == arm_id
        and factorial.get("arm_fingerprint_sha256")
        == sealed_arm.get("arm_fingerprint_sha256")
        and factorial.get("binding_payload_sha256")
        == sealed_arm.get("factorial_binding_payload_sha256"),
        "predecessor_pack_build_transport_reconciliation_invalid",
    )
    return {
        "status": (
            "PACK_BUILD_TRANSPORT_DIRECTLY_SEALED"
            if isinstance(directly_sealed, Mapping)
            else "LEGACY_PACK_BUILD_TRANSPORT_EXACTLY_RECONCILED"
        ),
        "pack_build_seal": {
            "path": str(seal_path),
            "file_sha256": file_sha256(seal_path),
            "pack_build_seal_root_sha256": seal_root,
        },
        "arm_id_used_only_for_full_config_construction": arm_id,
        "actual_build_mode_shared_execution_contract_digest_sha256": (
            actual_digest
        ),
        "sealed_consumer_mode_shared_execution_contract_digest_sha256": (
            sealed_consumer_digest
        ),
        "code_authority_root_sha256": sealed_arm[
            "code_authority_root_sha256"
        ],
        "exact_profile_config_root_sha256": sealed_arm[
            "exact_profile_config_root_sha256"
        ],
        "factorial_binding_payload_sha256": sealed_arm[
            "factorial_binding_payload_sha256"
        ],
        "classified_difference_count": (
            0 if isinstance(directly_sealed, Mapping) else 1
        ),
        "classified_differences": (
            []
            if isinstance(directly_sealed, Mapping)
            else [
                {
                    "path": (
                        "shared_execution_contract.execution_options."
                        "prepared_day_pack_build_enabled"
                    ),
                    "sealed_consumer_value": False,
                    "actual_build_value": True,
                    "reason": (
                        "mechanical arm-neutral pack-construction transport; "
                        "code, exact config, factorial binding, and every other "
                        "shared semantic field match the authenticated seal"
                    ),
                }
            ]
        ),
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "original_seal_relabelled": False,
        "pack_rebuild_required": False,
    }


def build_prepared_pack_rebind_authority(
    *,
    decision_contract_path: Path,
    window_id: str,
    start: str,
    end: str,
    source_plan_digest_sha256: str,
    source_bundle_dir: Path,
    source_selection_path: Path,
    source_authority_path: Path,
    source_authority_file_sha256: str,
    source_authority_root_sha256: str,
    source_bundle_root_sha256: str,
    typed_cache_root: Path,
    tick_sparse_cache_root: Path,
    prepared_day_pack_root: Path,
    predecessor_pack_receipt_path: Path,
    predecessor_engine_receipt_path: Path,
    predecessor_pack_build_seal_path: Path,
) -> dict[str, Any]:
    """Authenticate an existing arm-neutral pack under the current decision bytes."""

    decision_path = Path(decision_contract_path).resolve()
    decision = _load_json(decision_path, code="decision_contract_invalid")
    window = resolve_canonical_window_binding(
        decision,
        window_id=window_id,
        start=start,
        end=end,
        source_plan_digest_sha256=source_plan_digest_sha256,
    )
    decision_self_hash = decision.get("self_hash", {}).get("sha256")
    _require(_is_sha256(decision_self_hash), "decision_contract_self_hash_invalid")

    predecessor_path = Path(predecessor_pack_receipt_path).resolve()
    predecessor = _load_json(
        predecessor_path, code="predecessor_prepared_pack_receipt_invalid"
    )
    predecessor_root = predecessor.get("receipt_root_sha256")
    _require(
        predecessor.get("schema") == PREPARED_PACK_RECEIPT_SCHEMA
        and predecessor.get("status")
        == "POST_ACCELERATION_ARM_NEUTRAL_PREPARED_PACK_COMPLETE"
        and _is_sha256(predecessor_root)
        and predecessor_root == self_hash(predecessor, "receipt_root_sha256")
        and predecessor.get("policy_execution_entered") is False
        and predecessor.get("broker_live_authority") is False
        and predecessor.get("broker_mutation_enabled") is False
        and predecessor.get("real_order_transmission_possible") is False
        and predecessor.get("economic_values_exposed") is False,
        "predecessor_prepared_pack_receipt_invalid",
    )
    predecessor_window = predecessor.get("window")
    _require(
        isinstance(predecessor_window, Mapping)
        and predecessor_window.get("start") == start
        and predecessor_window.get("end") == end
        and predecessor_window.get("source_plan_digest_sha256")
        == source_plan_digest_sha256,
        "predecessor_prepared_pack_window_mismatch",
    )

    engine_path = Path(predecessor_engine_receipt_path).resolve()
    engine = _load_json(engine_path, code="predecessor_pack_engine_receipt_invalid")
    engine_root = engine.get("receipt_root_sha256")
    _require(
        engine.get("status") == "PREPARED_DAY_PACK_BUILD_ONLY_COMPLETE"
        and _is_sha256(engine_root)
        and engine_root == self_hash(engine, "receipt_root_sha256")
        and engine_root == predecessor.get("engine_build_receipt_root_sha256")
        and engine.get("policy_execution_entered") is False
        and engine.get("broker_live_authority") is False
        and engine.get("broker_mutation_enabled") is False
        and engine.get("economic_values_exposed") is False,
        "predecessor_pack_engine_receipt_invalid",
    )
    pack_build_transport = reconcile_predecessor_pack_build_transport(
        pack_build_seal_path=predecessor_pack_build_seal_path,
        predecessor_pack_receipt=predecessor,
        engine_receipt=engine,
    )
    root = Path(prepared_day_pack_root).resolve()
    _require(
        root == Path(str(predecessor.get("prepared_day_pack_root") or "")).resolve(),
        "predecessor_prepared_pack_root_mismatch",
    )
    builds = validate_prepared_pack_builds(
        engine.get("prepared_day_pack_build_receipts"),
        prepared_day_pack_root=root,
    )
    discovered = discover_prepared_pack_roots(root)
    _require(
        predecessor.get("prepared_day_pack_roots")
        == _serialized_pack_roots(discovered)
        == {
            f"{row['split']}:{row['days'][0]}:{row['days'][-1]}": row[
                "pack_root_sha256"
            ]
            for row in builds
        },
        "predecessor_prepared_pack_manifest_root_mismatch",
    )

    args = build_standard_args(
        output_dir=ROOT / ".phase-c-pack-rebind-placeholder",
        output_prefix="BROAD_LIVE_AS_IF_REPLAY_B7_5_PACK_REBIND",
        window_id=window_id,
        start=start,
        end=end,
        arm_id="S1R1",
        decision_contract_path=decision_path,
        source_bundle_dir=source_bundle_dir,
        source_selection_path=source_selection_path,
        source_authority_path=source_authority_path,
        source_authority_file_sha256=source_authority_file_sha256,
        source_authority_root_sha256=source_authority_root_sha256,
        source_bundle_root_sha256=source_bundle_root_sha256,
        source_plan_digest_sha256=source_plan_digest_sha256,
        typed_cache_root=typed_cache_root,
        tick_sparse_cache_root=tick_sparse_cache_root,
        prepared_day_pack_root=root,
    )
    bound_source = bind_fresh_source(args)
    predecessor_real_source = engine.get("source_acceleration_authority")
    predecessor_bound_source = (
        predecessor_real_source.get("source_bundle_consumer_rebind_authority")
        if isinstance(predecessor_real_source, Mapping)
        else None
    )
    _require(
        isinstance(predecessor_bound_source, Mapping)
        and predecessor.get("source_authority_binding_root_sha256")
        == predecessor_bound_source.get("binding_root_sha256")
        == self_hash(predecessor_bound_source, "binding_root_sha256"),
        "predecessor_prepared_pack_source_authority_invalid",
    )
    predecessor_selection_binding = predecessor_bound_source.get(
        "verified_successor_selection"
    )
    current_selection_binding = bound_source.get("verified_successor_selection")
    _require(
        isinstance(predecessor_selection_binding, Mapping)
        and isinstance(current_selection_binding, Mapping),
        "prepared_pack_source_selection_binding_invalid",
    )
    predecessor_selection_path = Path(
        str(predecessor_selection_binding.get("path") or "")
    ).resolve()
    current_selection_path = Path(source_selection_path).resolve()
    predecessor_selection = _load_json(
        predecessor_selection_path,
        code="predecessor_pack_source_selection_invalid",
    )
    current_selection = _load_json(
        current_selection_path,
        code="current_pack_source_selection_invalid",
    )
    _require(
        predecessor_selection_path.is_file()
        and not predecessor_selection_path.is_symlink()
        and file_sha256(predecessor_selection_path)
        == predecessor_selection_binding.get("file_sha256")
        and predecessor_selection.get("selection_root_sha256")
        == predecessor_selection_binding.get("selection_root_sha256")
        == self_hash(predecessor_selection, "selection_root_sha256")
        and current_selection_path.is_file()
        and not current_selection_path.is_symlink()
        and current_selection_path
        == Path(str(current_selection_binding.get("path") or "")).resolve()
        and file_sha256(current_selection_path)
        == current_selection_binding.get("file_sha256")
        and current_selection.get("selection_root_sha256")
        == current_selection_binding.get("selection_root_sha256")
        == self_hash(current_selection, "selection_root_sha256"),
        "prepared_pack_source_selection_identity_invalid",
    )
    predecessor_source_projection = source_selection_rebind_projection(
        predecessor_selection
    )
    current_source_projection = source_selection_rebind_projection(current_selection)
    predecessor_source_projection_root = stable_sha256(
        predecessor_source_projection
    )
    current_source_projection_root = stable_sha256(current_source_projection)
    _require(
        predecessor_source_projection == current_source_projection
        and predecessor_source_projection_root == current_source_projection_root,
        "predecessor_prepared_pack_source_semantic_mismatch",
    )
    manifest_bindings: list[dict[str, Any]] = []
    for (split, first_day, last_day), pack_root in sorted(discovered.items()):
        manifest_path = root / split / f"{first_day}_{last_day}" / MANIFEST_NAME
        manifest = _load_json(manifest_path, code="prepared_pack_manifest_invalid")
        manifest_bindings.append(
            {
                "split": split,
                "days": [first_day] if first_day == last_day else [first_day, last_day],
                "path": str(manifest_path),
                "file_sha256": file_sha256(manifest_path),
                "bytes": manifest_path.stat().st_size,
                "pack_root_sha256": pack_root,
                "source_identity_root_sha256": manifest.get("bindings", {}).get(
                    "source_identity_root_sha256"
                ),
                "factor_neutral_config_root_sha256": manifest.get(
                    "bindings", {}
                ).get("factor_neutral_config_root_sha256"),
            }
        )
    prepared_pack_source_identity_binding = (
        build_prepared_pack_source_identity_binding(manifest_bindings)
    )
    core = {
        "schema": PREPARED_PACK_REBIND_SCHEMA,
        "status": PREPARED_PACK_REBIND_STATUS,
        "valid": True,
        "decision_contract_binding": {
            "path": str(decision_path.relative_to(ROOT)),
            "file_sha256": file_sha256(decision_path),
            "self_hash_sha256": decision_self_hash,
        },
        "window_binding": window,
        "source_authority_binding": {
            "path": str(Path(source_authority_path).resolve()),
            "file_sha256": source_authority_file_sha256,
            "authority_root_sha256": source_authority_root_sha256,
            "bundle_root_sha256": source_bundle_root_sha256,
            "selection_root_sha256": current_selection_binding[
                "selection_root_sha256"
            ],
            "source_plan_digest_sha256": source_plan_digest_sha256,
            "binding_root_sha256": bound_source["binding_root_sha256"],
        },
        "source_selection_semantic_equivalence": {
            "status": "EXACT_RETAINED_FIELDS_EQUAL",
            "predecessor_selection": {
                "path": str(predecessor_selection_path),
                "file_sha256": predecessor_selection_binding["file_sha256"],
                "selection_root_sha256": predecessor_selection_binding[
                    "selection_root_sha256"
                ],
            },
            "current_selection": {
                "path": str(current_selection_path),
                "file_sha256": current_selection_binding["file_sha256"],
                "selection_root_sha256": current_selection_binding[
                    "selection_root_sha256"
                ],
            },
            "semantic_projection_sha256": current_source_projection_root,
            "excluded_fields": [
                copy.deepcopy(row) for row in SOURCE_SELECTION_REBIND_EXCLUSIONS
            ],
            "meaningful_source_difference_count": 0,
            "unknown_difference_count": 0,
        },
        "prepared_pack_source_identity_binding": (
            prepared_pack_source_identity_binding
        ),
        "prepared_day_pack_root": str(root),
        "prepared_day_pack_roots": _serialized_pack_roots(discovered),
        "prepared_day_packs": builds,
        "manifest_bindings": manifest_bindings,
        "predecessor_pack_receipt": {
            "path": str(predecessor_path),
            "file_sha256": file_sha256(predecessor_path),
            "receipt_root_sha256": predecessor_root,
            "superseded_decision_contract_self_hash_sha256": predecessor.get(
                "decision_contract_self_hash_sha256"
            ),
            "superseded_execution_seal_root_sha256": predecessor.get(
                "execution_seal_root_sha256"
            ),
            "old_contract_identities_are_provenance_only": True,
        },
        "predecessor_engine_receipt": {
            "path": str(engine_path),
            "file_sha256": file_sha256(engine_path),
            "receipt_root_sha256": engine_root,
        },
        "predecessor_pack_build_transport_reconciliation": (
            pack_build_transport
        ),
        "all_persisted_pack_bytes_authenticated": True,
        "factor_reads_forbidden_and_audited": True,
        "factorial_values_present_in_preparation_config": False,
        "policy_execution_entered": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    return {**core, "authority_root_sha256": stable_sha256(core)}


def validate_prepared_pack_rebind_authority(
    path: Path,
    *,
    decision_contract_path: Path,
    full_byte_authentication: bool = False,
) -> dict[str, Any]:
    """Validate the current contract-to-pack binding and current pack bytes."""

    authority_path = Path(path).resolve()
    authority = _load_json(
        authority_path, code="prepared_pack_rebind_authority_invalid"
    )
    root_hash = authority.get("authority_root_sha256")
    decision_path = Path(decision_contract_path).resolve()
    decision = _load_json(decision_path, code="decision_contract_invalid")
    binding = authority.get("decision_contract_binding")
    source_binding = authority.get("source_authority_binding")
    source_equivalence = authority.get(
        "source_selection_semantic_equivalence"
    )
    transport = authority.get(
        "predecessor_pack_build_transport_reconciliation"
    )
    _require(
        authority.get("schema") == PREPARED_PACK_REBIND_SCHEMA
        and authority.get("status") == PREPARED_PACK_REBIND_STATUS
        and authority.get("valid") is True
        and _is_sha256(root_hash)
        and root_hash == self_hash(authority, "authority_root_sha256")
        and isinstance(binding, Mapping)
        and binding.get("file_sha256") == file_sha256(decision_path)
        and binding.get("self_hash_sha256")
        == decision.get("self_hash", {}).get("sha256")
        and isinstance(source_binding, Mapping)
        and set(source_binding)
        == {
            "path",
            "file_sha256",
            "authority_root_sha256",
            "bundle_root_sha256",
            "selection_root_sha256",
            "source_plan_digest_sha256",
            "binding_root_sha256",
        }
        and all(
            _is_sha256(value)
            for key, value in source_binding.items()
            if key != "path"
        )
        and isinstance(source_equivalence, Mapping)
        and source_equivalence.get("status") == "EXACT_RETAINED_FIELDS_EQUAL"
        and source_equivalence.get("meaningful_source_difference_count") == 0
        and source_equivalence.get("unknown_difference_count") == 0
        and isinstance(transport, Mapping)
        and transport.get("status")
        in {
            "PACK_BUILD_TRANSPORT_DIRECTLY_SEALED",
            "LEGACY_PACK_BUILD_TRANSPORT_EXACTLY_RECONCILED",
        }
        and transport.get("meaningful_difference_count") == 0
        and transport.get("unknown_difference_count") == 0
        and transport.get("original_seal_relabelled") is False
        and authority.get("all_persisted_pack_bytes_authenticated") is True
        and authority.get("factor_reads_forbidden_and_audited") is True
        and authority.get("policy_execution_entered") is False
        and authority.get("broker_live_authority") is False
        and authority.get("broker_mutation_enabled") is False
        and authority.get("real_order_transmission_possible") is False
        and authority.get("economic_values_exposed") is False,
        "prepared_pack_rebind_authority_invalid",
    )
    actual = validate_prepared_pack_authority_manifest_roots(authority)
    manifests = authority.get("manifest_bindings")
    _require(
        isinstance(manifests, list) and len(manifests) == len(actual),
        "prepared_pack_authority_manifest_inventory_invalid",
    )
    for row in manifests:
        _require(
            isinstance(row, Mapping),
            "prepared_pack_authority_manifest_inventory_invalid",
        )
        manifest_path = Path(str(row.get("path") or ""))
        _require(
            manifest_path.is_file()
            and not manifest_path.is_symlink()
            and manifest_path.stat().st_size == row.get("bytes")
            and file_sha256(manifest_path) == row.get("file_sha256"),
            "prepared_pack_authority_manifest_byte_mismatch",
        )
    source_identity_binding = authority.get(
        "prepared_pack_source_identity_binding"
    )
    _require(
        isinstance(source_identity_binding, Mapping)
        and dict(source_identity_binding)
        == build_prepared_pack_source_identity_binding(manifests),
        "prepared_pack_source_identity_binding_invalid",
    )
    if full_byte_authentication:
        predecessor_engine = authority.get("predecessor_engine_receipt")
        _require(
            isinstance(predecessor_engine, Mapping),
            "prepared_pack_authority_engine_receipt_invalid",
        )
        engine_path = Path(str(predecessor_engine.get("path") or ""))
        engine = _load_json(
            engine_path, code="prepared_pack_authority_engine_receipt_invalid"
        )
        _require(
            engine_path.is_file()
            and not engine_path.is_symlink()
            and file_sha256(engine_path)
            == predecessor_engine.get("file_sha256")
            and engine.get("receipt_root_sha256")
            == predecessor_engine.get("receipt_root_sha256")
            == self_hash(engine, "receipt_root_sha256"),
            "prepared_pack_authority_engine_receipt_invalid",
        )
        validate_prepared_pack_builds(
            engine.get("prepared_day_pack_build_receipts"),
            prepared_day_pack_root=Path(authority["prepared_day_pack_root"]),
        )
    return authority


def run_prepared_pack_build(
    *,
    args: argparse.Namespace,
    execution_seal_path: Path,
) -> dict[str, Any]:
    """Build the shared arm-neutral pack without entering any arm reducer."""

    seal = validate_pack_build_seal(
        execution_seal_path,
        decision_contract_path=Path(args.decision_contract),
        arm_id=str(args.arm_id),
    )
    validate_args_against_execution_seal(args, seal)
    _require(
        args.prepared_day_pack_build_only is True
        and args.prepared_day_pack_root is None
        and args.build_prepared_day_pack_root is not None,
        "prepared_pack_build_mode_invalid",
    )
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    bound_source = bind_fresh_source(args)
    pack_build_contract = current_shared_contract(args)
    factorial = replay.selection_sizing_factorial_binding_from_args(args)
    _require(isinstance(factorial, Mapping), "factorial_binding_missing")
    actual_pack_build_binding = pack_build_execution_binding(
        arm_id=str(args.arm_id),
        shared=pack_build_contract,
        factorial=factorial,
    )
    validate_pack_build_execution_binding(
        seal=seal,
        actual=actual_pack_build_binding,
    )
    args.expected_shared_execution_contract_sha256 = pack_build_contract[
        "shared_execution_contract_digest_sha256"
    ]
    validate_fresh_output_namespace(Path(args.output_dir))
    namespace = replay.configure_output_namespace(Path(args.output_dir))
    expected_build_root = namespace / "prepared-day-packs"
    _require(
        Path(args.build_prepared_day_pack_root).resolve()
        == expected_build_root.resolve(),
        "prepared_pack_build_root_not_namespace_owned",
    )
    engine_receipt = replay.run_replay_engine(args)
    _require(
        engine_receipt.get("status") == "PREPARED_DAY_PACK_BUILD_ONLY_COMPLETE"
        and engine_receipt.get("policy_execution_entered") is False
        and engine_receipt.get("broker_live_authority") is False
        and engine_receipt.get("broker_mutation_enabled") is False
        and engine_receipt.get("economic_values_exposed") is False,
        "prepared_pack_engine_result_invalid",
    )
    builds = validate_prepared_pack_builds(
        engine_receipt.get("prepared_day_pack_build_receipts"),
        prepared_day_pack_root=expected_build_root,
    )
    core = {
        "schema": PREPARED_PACK_RECEIPT_SCHEMA,
        "status": "POST_ACCELERATION_ARM_NEUTRAL_PREPARED_PACK_COMPLETE",
        "window": copy.deepcopy(seal["window_binding"]),
        "namespace": str(namespace),
        "prepared_day_pack_root": str(expected_build_root),
        "prepared_day_packs": builds,
        "prepared_day_pack_roots": {
            f"{row['split']}:{row['days'][0]}:{row['days'][-1]}": row[
                "pack_root_sha256"
            ]
            for row in builds
        },
        "decision_contract_self_hash_sha256": seal[
            "decision_contract_binding"
        ]["self_hash_sha256"],
        "pack_build_seal_root_sha256": seal[
            "pack_build_seal_root_sha256"
        ],
        "arm_id_used_only_for_full_config_construction": args.arm_id,
        "pack_build_shared_execution_contract_digest_sha256": (
            pack_build_contract["shared_execution_contract_digest_sha256"]
        ),
        "pack_build_execution_binding": actual_pack_build_binding,
        "runtime_input_contract_root_sha256": runtime_contract[
            "contract_root_sha256"
        ],
        "source_authority_binding_root_sha256": bound_source[
            "binding_root_sha256"
        ],
        "engine_build_receipt_root_sha256": engine_receipt[
            "receipt_root_sha256"
        ],
        "factorial_values_present_in_preparation_config": False,
        "policy_execution_entered": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    replay.atomic_write_json(
        namespace / "B7_5_POST_ACCELERATION_PREPARED_PACK_RECEIPT.json",
        receipt,
    )
    return receipt


def run_sealed_arm(
    *,
    args: argparse.Namespace,
    execution_seal_path: Path,
) -> dict[str, Any]:
    """Run one arm only after independently recomputing its sealed digest."""

    seal = validate_execution_seal(
        execution_seal_path,
        decision_contract_path=Path(args.decision_contract),
        arm_id=str(args.arm_id),
    )
    validate_args_against_execution_seal(args, seal)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    bound_source = bind_fresh_source(args)
    shared = current_shared_contract(args)
    arm_seal = seal["arms"][args.arm_id]
    _require(
        shared["shared_execution_contract_digest_sha256"]
        == arm_seal["shared_execution_contract_digest_sha256"],
        "execution_seal_shared_digest_mismatch",
    )
    args.expected_shared_execution_contract_sha256 = arm_seal[
        "shared_execution_contract_digest_sha256"
    ]
    validate_fresh_output_namespace(Path(args.output_dir))
    namespace = replay.configure_output_namespace(Path(args.output_dir))
    summary = replay.run_replay_engine(args)
    _require(
        summary.get("status") == COMPLETED_REPLAY_STATUS,
        "post_acceleration_arm_incomplete",
    )
    inventory = build_arm_artifact_inventory(
        namespace=namespace,
        output_prefix=str(args.output_prefix),
        start=str(args.start),
        end=str(args.end),
    )
    pack_binding = seal["prepared_day_pack_binding"]
    core = {
        "schema": RUN_RECEIPT_SCHEMA,
        "status": "POST_ACCELERATION_ARM_EXECUTION_COMPLETE",
        "arm_id": args.arm_id,
        "window": copy.deepcopy(seal["window_binding"]),
        "namespace": str(namespace),
        "output_prefix": args.output_prefix,
        "decision_contract_self_hash_sha256": seal[
            "decision_contract_binding"
        ]["self_hash_sha256"],
        "execution_seal_root_sha256": seal["execution_seal_root_sha256"],
        "arm_fingerprint_sha256": arm_seal["arm_fingerprint_sha256"],
        "shared_execution_contract_digest_sha256": shared[
            "shared_execution_contract_digest_sha256"
        ],
        "runtime_input_contract_root_sha256": runtime_contract[
            "contract_root_sha256"
        ],
        "source_authority_binding_root_sha256": bound_source[
            "binding_root_sha256"
        ],
        "prepared_pack_authority": {
            "path": pack_binding["authority_path"],
            "file_sha256": pack_binding["authority_file_sha256"],
            "authority_root_sha256": pack_binding["authority_root_sha256"],
            "prepared_day_pack_root": pack_binding["prepared_day_pack_root"],
            "prepared_day_pack_roots": copy.deepcopy(
                pack_binding["prepared_day_pack_roots"]
            ),
        },
        "summary_status": COMPLETED_REPLAY_STATUS,
        "artifact_inventory": inventory,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "economic_values_exposed": False,
    }
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    replay.atomic_write_json(namespace / "B7_5_POST_ACCELERATION_ARM_RECEIPT.json", receipt)
    return receipt


def _add_common_execution_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--arm-id", choices=ARM_ORDER, required=True)
    parser.add_argument("--decision-contract", type=Path, required=True)
    parser.add_argument("--execution-seal", type=Path, required=True)
    parser.add_argument("--source-bundle-dir", type=Path, required=True)
    parser.add_argument("--source-selection", type=Path, required=True)
    parser.add_argument("--source-authority", type=Path, required=True)
    parser.add_argument("--source-authority-file-sha256", required=True)
    parser.add_argument("--source-authority-root-sha256", required=True)
    parser.add_argument("--source-bundle-root-sha256", required=True)
    parser.add_argument("--source-plan-digest-sha256", required=True)
    parser.add_argument("--typed-cache-root", type=Path, required=True)
    parser.add_argument("--tick-sparse-cache-root", type=Path, required=True)


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-runner-options", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    pack = subparsers.add_parser("build-pack")
    _add_common_execution_arguments(pack)
    arm = subparsers.add_parser("run-arm")
    _add_common_execution_arguments(arm)
    arm.add_argument("--prepared-day-pack-root", type=Path, required=True)
    arm.add_argument("--prepared-pack-authority", type=Path, required=True)
    return parser


def _standard_args_from_cli(args: argparse.Namespace) -> argparse.Namespace:
    build_pack = args.command == "build-pack"
    return build_standard_args(
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
        window_id=args.window_id,
        start=args.start,
        end=args.end,
        arm_id=args.arm_id,
        decision_contract_path=args.decision_contract,
        source_bundle_dir=args.source_bundle_dir,
        source_selection_path=args.source_selection,
        source_authority_path=args.source_authority,
        source_authority_file_sha256=args.source_authority_file_sha256,
        source_authority_root_sha256=args.source_authority_root_sha256,
        source_bundle_root_sha256=args.source_bundle_root_sha256,
        source_plan_digest_sha256=args.source_plan_digest_sha256,
        typed_cache_root=args.typed_cache_root,
        tick_sparse_cache_root=args.tick_sparse_cache_root,
        prepared_day_pack_root=(
            None if build_pack else args.prepared_day_pack_root
        ),
        prepared_pack_authority_path=(
            None if build_pack else args.prepared_pack_authority
        ),
        build_prepared_day_pack_root=(
            args.output_dir / "prepared-day-packs" if build_pack else None
        ),
        prepared_day_pack_build_only=build_pack,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _cli().parse_args(argv)
    if args.show_runner_options:
        print(json.dumps(RUNNER_OPTIONS, sort_keys=True))
        return 0
    if args.command not in {"build-pack", "run-arm"}:
        raise PostAccelerationRunnerError(
            "sealed Phase-C command required; free CLI replay is disabled"
        )
    run_args = _standard_args_from_cli(args)
    receipt = (
        run_prepared_pack_build(
            args=run_args,
            execution_seal_path=args.execution_seal,
        )
        if args.command == "build-pack"
        else run_sealed_arm(
            args=run_args,
            execution_seal_path=args.execution_seal,
        )
    )
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
