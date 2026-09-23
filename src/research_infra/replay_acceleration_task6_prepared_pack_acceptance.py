#!/usr/bin/env python3
"""Fail-closed acceptance for Task 6 prepared-day packs.

The completed Jan 1-2 reducer consumed an earlier pack whose record stream is
byte-identical to the corrected factor-neutral pack.  This verifier binds that
record-stream bridge, authenticates the consumed checkpoints and compact proof
shards, proves canonical source emission with the corrected build-only route,
and compares every causal/economic output against the accepted Task 5 run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    replay_acceleration_task5_compact_sink_acceptance as task5,
)
from src.research_infra import (
    replay_acceleration_task6_prepared_pack_runner as task6_runner,
)
from src.research_infra.replay_prepared_day_pack import (
    PreparedDayPackError,
    PreparedDayPackReader,
    factor_neutral_config_root,
)


SCHEMA = "gtos.replay_acceleration.task6_prepared_pack_acceptance.v1"
STATUS = "TASK6_PREPARED_DAY_PACK_EXACT_FACTOR_NEUTRAL_AND_CONSUMED"
TASK_NAME = "Replay-Acceleration Task 6"
EXPECTED_DAYS = ("2026-01-01", "2026-01-02")
EXPECTED_FACTOR_ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
SOURCE_REBIND_AUTHORITY = replay.ROOT / (
    ".hermes/receipts/task6/"
    "source-bundle-consumer-rebind-20260723-r2-task6-prepared-day-pack/"
    "SOURCE_BUNDLE_CONSUMER_REBIND_AUTHORITY.json"
)
EXPECTED_SOURCE_REBIND_FILE_SHA256 = (
    "6e018a1b0cbcd9b6189c2943514a8cfcdfe48b78eb58fc5417403cfc413bafca"
)
EXPECTED_SOURCE_REBIND_ROOT_SHA256 = (
    "57c3af1dd652c212a1752a8b028be358395df609510c43d34fb543965f2f0529"
)
EXPECTED_SOURCE_LEDGER_SHA256 = task6_runner.TASK5_SOURCE_LEDGER_SHA256
EVIDENCE_PARENT = replay.ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_"
    "2026_06_20/attempt_5_typed_sparse"
)
TASK5_REFERENCE_ROOT = EVIDENCE_PARENT / (
    "TASK5_COMPACT_SINK_JAN1_2_20260722T181555Z"
)
TASK6_EXECUTION_ROOT = EVIDENCE_PARENT / (
    "TASK6_PREPARED_PACK_JAN1_2_20260722T202135Z"
)
TASK6_CORRECTED_ROOT = EVIDENCE_PARENT / (
    "TASK6_FACTOR_NEUTRAL_PACK_REBUILD_JAN1_2_20260723T054500Z"
)
TASK5_ACCEPTANCE_RECEIPT = replay.ROOT / (
    ".hermes/receipts/task5/"
    "task5-compact-sink-20260723T040000Z-r2/"
    "TASK5_COMPACT_SINK_ACCEPTANCE.json"
)
EXPECTED_TASK5_ACCEPTANCE_FILE_SHA256 = (
    "49ce40ed3040365d246d220dffcd1b7cc6f6c41737d08d32469ede38cbbb0087"
)
EXPECTED_TASK5_ACCEPTANCE_ROOT_SHA256 = (
    "e3b583fb41cb798084ef9a5bdb2574f040ee5aa64934dfddebd9b44aa0451c16"
)
EXPECTED_REFERENCE_PARTIAL_SHA256 = (
    "0f69129e2488b8740799f732f0e0bfd1fd9e360619b8a147a68b7fb76cfed721"
)
EXPECTED_EXECUTION_PARTIAL_SHA256 = (
    "8831a302fcc48d9d1b0bba4298ee5bb483ac40c43f5b3462b897bd96a0915c66"
)
EXPECTED_EXECUTION_FINAL_SHA256 = (
    "00f25873c7c23af66bc2a790a33d75e0c66a005fa41b0efef20cf78ee6b8b8d7"
)
EXPECTED_CORRECTED_PARTIAL_SHA256 = (
    "ec9fd63695bab3aa1d59c3f7bb1c1cc728338f638e044facbe37c01acaa60c9a"
)
EXPECTED_CORRECTED_ENGINE_SHA256 = (
    "3c169dfe9de90a84aa4b3f90451b96e3210aa76f7660c2327703e9fbba21241f"
)
EXPECTED_CORRECTED_PACK_RECEIPT_SHA256 = (
    "eff73008235714e61421bdffc11d88f8932ca91520804dba801a2039c1a42057"
)
EXPECTED_REFERENCE_SEMANTIC_MANIFEST_SHA256 = (
    "2d55a75ae1228c6fe05ab73722c42c0959f04a744b6e2c0220badfd40c4b7a8c"
)
EXPECTED_EXECUTION_SEMANTIC_MANIFEST_SHA256 = (
    "bcc07550d97715a98e188bc0e14dbe7b4f1861e571616343993cb61cdae5e323"
)
EXPECTED_CONSUMED_PACKS = (
    {
        "manifest_sha256": (
            "537e21cdf6e446d1761279bbf49d1310f0284b59242262ab2c4a5a569aa70b93"
        ),
        "pack_root_sha256": (
            "bc98907e7235b8a89c8b8d730d99ae7054b1e38c1d1988ef628b7570ccec9b16"
        ),
    },
    {
        "manifest_sha256": (
            "683ee3f9af000b4dfb70275145b2ee1074275c759ff2faa08b889460611fd645"
        ),
        "pack_root_sha256": (
            "684783ba80fdf45903bd6c4b66795d32f2ea5faba7e4c9bf1a8403ef554be7c2"
        ),
    },
)
EXPECTED_CORRECTED_PACKS = (
    {
        "manifest_sha256": (
            "8b47ca918974a18c378e9fbf755695227d288fe06a4d1f1b70765b1e861b5cfd"
        ),
        "pack_root_sha256": (
            "b83649706b47e625c965a1060252162535b2f95db4c5048eddc082369a2f300a"
        ),
    },
    {
        "manifest_sha256": (
            "9be94296384fd44515b904498211f3a8f16ac4ab45c13256e877a5ebea7f8239"
        ),
        "pack_root_sha256": (
            "e6bdabadc8deb4ee1e64f4d994010007fac1e8114e886e4b3e95bbd4a1bb8a62"
        ),
    },
)
ALLOWED_SHARED_CONTRACT_SUCCESSOR_CODE_PATHS = frozenset(
    {
        "src/research_infra/"
        "replay_acceleration_attempt5_typed_sparse_runner.py",
    }
)


class Task6PreparedPackAcceptanceRejected(RuntimeError):
    """Task 6 evidence, pack identity, or semantics failed closed."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task6PreparedPackAcceptanceRejected(code)


def _load_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_json_invalid:{path.name}"
        ) from None
    _require(type(payload) is dict, f"task6_json_invalid:{path.name}")
    return payload


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
    except OSError:
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_file_unreadable:{Path(path).name}"
        ) from None
    return digest.hexdigest()


def _regular_file(path: Path, *, label: str) -> Path:
    path = Path(os.path.abspath(path))
    _require(
        path.is_file() and not path.is_symlink(),
        f"task6_{label}_file_invalid",
    )
    return path


def _jsonl_receipt(path: Path, *, label: str) -> dict[str, Any]:
    path = _regular_file(path, label=label)
    count = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                _require(bool(line.strip()), f"task6_{label}_blank_row")
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    raise Task6PreparedPackAcceptanceRejected(
                        f"task6_{label}_json_invalid:{line_number}"
                    ) from None
                _require(
                    isinstance(row, Mapping),
                    f"task6_{label}_row_invalid:{line_number}",
                )
                count += 1
    except UnicodeError:
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_{label}_encoding_invalid"
        ) from None
    return {
        "path": str(path),
        "row_count": count,
        "bytes": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


def compare_jsonl_file_exact(
    reference_path: Path,
    accelerated_path: Path,
    *,
    label: str,
) -> dict[str, Any]:
    reference = _jsonl_receipt(reference_path, label=f"{label}_reference")
    accelerated = _jsonl_receipt(
        accelerated_path,
        label=f"{label}_accelerated",
    )
    _require(
        reference["row_count"] == accelerated["row_count"]
        and reference["bytes"] == accelerated["bytes"]
        and reference["sha256"] == accelerated["sha256"],
        f"task6_{label}_file_mismatch",
    )
    return {
        "label": label,
        "status": "BYTE_EXACT",
        "row_count": reference["row_count"],
        "bytes": reference["bytes"],
        "sha256": reference["sha256"],
        "reference_path": reference["path"],
        "accelerated_path": accelerated["path"],
    }


def compare_jsonl_multiset_exact(
    reference_path: Path,
    accelerated_path: Path,
    *,
    label: str,
) -> dict[str, Any]:
    """Prove content equality when a superseded proof route reordered rows."""

    def inventory(path: Path, side: str) -> tuple[Counter[str], dict[str, Any]]:
        receipt = _jsonl_receipt(path, label=f"{label}_{side}")
        hashes: Counter[str] = Counter()
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                hashes[semantic.canonical_sha256(json.loads(line))] += 1
        return hashes, receipt

    reference, reference_receipt = inventory(reference_path, "reference")
    accelerated, accelerated_receipt = inventory(accelerated_path, "accelerated")
    _require(reference == accelerated, f"task6_{label}_content_mismatch")
    return {
        "label": label,
        "status": "ROW_MULTISET_EXACT_ORDER_DIFFERENT_ALLOWED_ONLY_FOR_SUPERSEDED_PROOF_EMISSION",
        "row_count": reference_receipt["row_count"],
        "reference_sha256": reference_receipt["sha256"],
        "accelerated_sha256": accelerated_receipt["sha256"],
        "raw_file_order_equal": (
            reference_receipt["sha256"] == accelerated_receipt["sha256"]
        ),
    }


def _consume_authenticated_pack(
    root: Path,
    *,
    expected_pack_root_sha256: str,
) -> dict[str, Any]:
    try:
        reader = PreparedDayPackReader(
            root,
            expected_pack_root_sha256=expected_pack_root_sha256,
        )
        for row in reader.manifest["window_inventory"]:
            reader.next_window(
                trading_day=str(row["trading_day"]),
                decision_time_utc=str(row["decision_time_utc"]),
                window_ordinal=int(row["window_ordinal"]),
            )
        reader.finish()
        return copy.deepcopy(reader.manifest)
    except PreparedDayPackError as exc:
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_prepared_pack_invalid:{exc}"
        ) from None


def validate_pack_record_bridge(
    *,
    consumed_pack_root: Path,
    corrected_pack_root: Path,
    expected_consumed_pack_root_sha256: str,
    expected_corrected_pack_root_sha256: str,
    expected_factor_neutral_config_root_sha256: str,
) -> dict[str, Any]:
    """Bind the consumed pack to the corrected factor-free record stream."""

    consumed_pack_root = Path(os.path.abspath(consumed_pack_root))
    corrected_pack_root = Path(os.path.abspath(corrected_pack_root))
    _require(
        consumed_pack_root != corrected_pack_root,
        "task6_pack_bridge_roots_not_distinct",
    )
    consumed = _consume_authenticated_pack(
        consumed_pack_root,
        expected_pack_root_sha256=expected_consumed_pack_root_sha256,
    )
    corrected = _consume_authenticated_pack(
        corrected_pack_root,
        expected_pack_root_sha256=expected_corrected_pack_root_sha256,
    )
    for field in ("window_inventory", "ordered_record_root_sha256", "shards"):
        _require(
            semantic.canonical_bytes(consumed.get(field))
            == semantic.canonical_bytes(corrected.get(field)),
            "task6_pack_record_stream_mismatch",
        )
    left_bindings = copy.deepcopy(consumed["bindings"])
    right_bindings = copy.deepcopy(corrected["bindings"])
    left_factor = left_bindings.pop("factor_neutral_config_root_sha256", None)
    right_factor = right_bindings.pop("factor_neutral_config_root_sha256", None)
    _require(
        semantic._is_sha256(left_factor)
        and semantic._is_sha256(right_factor)
        and right_factor == expected_factor_neutral_config_root_sha256,
        "task6_pack_factor_neutral_root_invalid",
    )
    _require(
        semantic.canonical_bytes(left_bindings)
        == semantic.canonical_bytes(right_bindings),
        "task6_pack_binding_difference_unexpected",
    )
    return {
        "status": "EXACT_RECORD_STREAM_BRIDGED_TO_FACTOR_NEUTRAL_PACK",
        "consumed_pack_root_sha256": consumed["pack_root_sha256"],
        "corrected_pack_root_sha256": corrected["pack_root_sha256"],
        "record_count": int(consumed["record_count"]),
        "ordered_record_root_sha256": consumed[
            "ordered_record_root_sha256"
        ],
        "shard_count": len(consumed["shards"]),
        "raw_bytes": sum(int(row["raw_bytes"]) for row in consumed["shards"]),
        "compressed_bytes": sum(
            int(row["compressed_bytes"]) for row in consumed["shards"]
        ),
        "consumed_factor_config_root_sha256": left_factor,
        "corrected_factor_neutral_config_root_sha256": right_factor,
        "only_binding_difference": "factor_neutral_config_root_sha256",
        "causal_or_economic_record_difference_count": 0,
    }


def validate_four_arm_factor_neutral_roots(
    roots: Mapping[str, str],
    *,
    expected_root_sha256: str,
) -> dict[str, Any]:
    _require(
        tuple(sorted(roots)) == tuple(sorted(EXPECTED_FACTOR_ARMS)),
        "task6_factor_neutral_arm_set_invalid",
    )
    for arm in EXPECTED_FACTOR_ARMS:
        _require(
            semantic._is_sha256(roots.get(arm))
            and roots[arm] == expected_root_sha256,
            f"task6_factor_neutral_root_mismatch:{arm}",
        )
    return {
        "status": "FOUR_ARM_PREPARATION_ROOT_IDENTICAL",
        "factor_neutral_config_root_sha256": expected_root_sha256,
        "arm_roots": dict(roots),
    }


def derive_four_arm_factor_neutral_roots() -> dict[str, str]:
    args = task6_runner.task6_args(Path("task6-factor-root-derivation-not-run"))
    replay.bind_attempt5_finalizer_conflict_key_order()
    replay.configure_runtime_evidence_root(replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    contract = _load_json(Path(args.decision_contract))
    rows = (contract.get("factorial_contract") or {}).get("arms")
    _require(isinstance(rows, list), "task6_factorial_contract_invalid")
    fingerprints = {
        str(row.get("arm_id")): str(row.get("arm_fingerprint_sha256"))
        for row in rows
        if isinstance(row, Mapping)
    }
    roots: dict[str, str] = {}
    for arm in EXPECTED_FACTOR_ARMS:
        _require(
            semantic._is_sha256(fingerprints.get(arm)),
            f"task6_factorial_fingerprint_invalid:{arm}",
        )
        arm_args = copy.copy(args)
        arm_args.arm_id = arm
        arm_args.expected_arm_fingerprint_sha256 = fingerprints[arm]
        try:
            binding = replay.selection_sizing_factorial_binding_from_args(
                arm_args
            )
            config = replay.build_config(
                replay.PROFILE_REPAIRED,
                factorial_arm_binding=binding,
            )
            roots[arm] = factor_neutral_config_root(config)
        except (OSError, ValueError, PreparedDayPackError) as exc:
            raise Task6PreparedPackAcceptanceRejected(
                f"task6_factor_neutral_root_derivation_failed:{arm}:{exc}"
            ) from None
    return roots


_TASK6_RUNTIME_TOP_LEVEL_FIELDS = (
    "generated_at_utc",
    "route_id",
    "b7_5_contract_binding",
    "shared_execution_contract",
    "source_acceleration_authority",
    "capacity_safe_chunk_execution_contract",
    "source_authority_chunk_invariance_contract",
    "source_authority_preflight_checkpoints",
    "task2_semantic_checkpoint",
)
_SEPARATELY_AUTHENTICATED_IMPLEMENTATION_AUTHORITY_FIELDS = frozenset(
    {
        "b7_5_contract_binding",
        "shared_execution_contract",
        "source_acceleration_authority",
    }
)


def project_task6_runtime_envelope_pair(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Align only separately authenticated runtime/provenance mechanics."""

    left = copy.deepcopy(dict(reference))
    right = copy.deepcopy(dict(accelerated))
    classified: list[dict[str, str]] = []
    for field in _TASK6_RUNTIME_TOP_LEVEL_FIELDS:
        if semantic.canonical_bytes(left.get(field)) != semantic.canonical_bytes(
            right.get(field)
        ):
            classified.append(
                {
                    "path": field,
                    "rationale": "separately_authenticated_replay_only_runtime_or_provenance_envelope",
                }
            )
        if field in _SEPARATELY_AUTHENTICATED_IMPLEMENTATION_AUTHORITY_FIELDS:
            left[field] = None
            right[field] = None
        else:
            right[field] = copy.deepcopy(left.get(field))
    left_rows = left.get("progress_rows")
    right_rows = right.get("progress_rows")
    _require(
        isinstance(left_rows, list)
        and isinstance(right_rows, list)
        and len(left_rows) == len(right_rows),
        "task6_summary_progress_rows_invalid",
    )
    zero_fallback = {role: 0 for role in ("candidate", "missed", "order", "trade")}
    for index, (left_row, right_row) in enumerate(zip(left_rows, right_rows)):
        _require(
            isinstance(left_row, dict) and isinstance(right_row, dict),
            "task6_summary_progress_row_invalid",
        )
        if semantic.canonical_bytes(left_row.get("campaign_exact_cache")) != semantic.canonical_bytes(
            right_row.get("campaign_exact_cache")
        ):
            classified.append(
                {
                    "path": f"progress_rows/{index}/campaign_exact_cache",
                    "rationale": "prepared_stream_replaces_reducer_preparation_cache_activity",
                }
            )
        right_row["campaign_exact_cache"] = copy.deepcopy(
            left_row.get("campaign_exact_cache")
        )
        left_rel = left_row.get("candidate_relational_materialization")
        right_rel = right_row.get("candidate_relational_materialization")
        _require(
            isinstance(left_rel, dict) and isinstance(right_rel, dict),
            "task6_candidate_relational_audit_invalid",
        )
        for relational in (left_rel, right_rel):
            fallback = relational.get("fallback_only_instance_key_counts")
            _require(
                fallback is None or fallback == zero_fallback,
                "task6_candidate_relational_fallback_invalid",
            )
            relational["fallback_only_instance_key_counts"] = copy.deepcopy(
                zero_fallback
            )
        if "fallback_only_instance_key_counts" not in (
            reference.get("progress_rows") or [{}]
        )[index].get("candidate_relational_materialization", {}):
            classified.append(
                {
                    "path": (
                        f"progress_rows/{index}/candidate_relational_materialization/"
                        "fallback_only_instance_key_counts"
                    ),
                    "rationale": "explicit_zero_only_relational_audit_extension",
                }
            )
    return left, right, {
        "status": "TASK6_FINITE_RUNTIME_ENVELOPE_CLASSIFIED",
        "classified_paths": classified,
        "causal_or_economic_field_excluded": False,
        "unknown_field_excluded": False,
    }


def _validate_self_root(payload: Mapping[str, Any], *, label: str) -> None:
    projection = dict(payload)
    declared = projection.pop("receipt_root_sha256", None)
    _require(
        semantic._is_sha256(declared)
        and declared == replay.stable_sha256(projection),
        f"task6_{label}_receipt_root_invalid",
    )


_SHARED_CONTRACT_FIELDS = {
    "active_replay_symbol_universe",
    "broker_live_final_authority",
    "code_authority",
    "config_file_hashes",
    "effective_profile_config_hash_semantics",
    "effective_profile_config_hashes",
    "exact_profile_config_roots_sha256",
    "exact_risk_profile_bindings",
    "execution_options",
    "missing_code_paths",
    "schema",
    "shared_execution_contract_digest_sha256",
    "status",
    "ultimate_package_runtime_input_contract",
    "valid",
    "window_identity_excluded_from_shared_digest",
}
_SHARED_CONTRACT_NON_DIGEST_FIELDS = {
    "exact_profile_config_roots_sha256",
    "exact_risk_profile_bindings",
    "shared_execution_contract_digest_sha256",
    "status",
    "valid",
}


def validate_shared_execution_contract(
    shared: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    """Recompute and structurally authenticate one complete shared contract."""

    _require(
        isinstance(shared, Mapping) and set(shared) == _SHARED_CONTRACT_FIELDS,
        f"task6_{label}_shared_contract_fields_invalid",
    )
    semantic_payload = {
        key: copy.deepcopy(value)
        for key, value in shared.items()
        if key not in _SHARED_CONTRACT_NON_DIGEST_FIELDS
    }
    declared_digest = shared.get("shared_execution_contract_digest_sha256")
    _require(
        shared.get("schema")
        == "gtos.final_moonshot.broad_replay.shared_execution_contract.v1"
        and shared.get("valid") is True
        and shared.get("status") == "shared_execution_contract_bound"
        and shared.get("window_identity_excluded_from_shared_digest") is True
        and semantic._is_sha256(declared_digest)
        and declared_digest == replay.stable_sha256(semantic_payload),
        "task6_shared_contract_digest_invalid",
    )

    code_rows = shared.get("code_authority")
    _require(
        isinstance(code_rows, list)
        and bool(code_rows)
        and shared.get("missing_code_paths") == [],
        f"task6_{label}_shared_contract_code_invalid",
    )
    code_paths: list[str] = []
    for row in code_rows:
        _require(
            isinstance(row, Mapping)
            and set(row) == {"path", "sha256"}
            and isinstance(row.get("path"), str)
            and bool(row["path"])
            and semantic._is_sha256(row.get("sha256")),
            f"task6_{label}_shared_contract_code_invalid",
        )
        code_paths.append(str(row["path"]))
    _require(
        len(code_paths) == len(set(code_paths)),
        f"task6_{label}_shared_contract_code_invalid",
    )

    semantic_configs = shared.get("effective_profile_config_hashes")
    exact_configs = shared.get("exact_profile_config_roots_sha256")
    risk_bindings = shared.get("exact_risk_profile_bindings")
    _require(
        isinstance(semantic_configs, Mapping)
        and bool(semantic_configs)
        and isinstance(exact_configs, Mapping)
        and isinstance(risk_bindings, Mapping)
        and set(semantic_configs) == set(exact_configs) == set(risk_bindings),
        f"task6_{label}_shared_contract_config_invalid",
    )
    for profile in semantic_configs:
        risk = risk_bindings.get(profile)
        _require(
            semantic._is_sha256(semantic_configs[profile])
            and semantic._is_sha256(exact_configs[profile])
            and isinstance(risk, Mapping)
            and set(risk) == {"path", "sha256"}
            and isinstance(risk.get("path"), str)
            and bool(risk["path"])
            and semantic._is_sha256(risk.get("sha256")),
            f"task6_{label}_shared_contract_config_invalid",
        )
    config_files = shared.get("config_file_hashes")
    _require(
        isinstance(config_files, Mapping)
        and bool(config_files)
        and all(
            isinstance(path, str)
            and bool(path)
            and semantic._is_sha256(digest)
            for path, digest in config_files.items()
        ),
        f"task6_{label}_shared_contract_config_invalid",
    )
    hash_semantics = shared.get("effective_profile_config_hash_semantics")
    _require(
        isinstance(hash_semantics, Mapping)
        and set(hash_semantics)
        == {
            "projection",
            "excluded_runtime_fields",
            "raw_artifact_sha256_retained_in_runtime_and_ledgers",
        }
        and hash_semantics.get("projection")
        == "execution_semantic_config_excludes_diagnostic_provenance"
        and isinstance(hash_semantics.get("excluded_runtime_fields"), list)
        and hash_semantics.get(
            "raw_artifact_sha256_retained_in_runtime_and_ledgers"
        )
        is True,
        f"task6_{label}_shared_contract_config_invalid",
    )

    symbols = shared.get("active_replay_symbol_universe")
    package = shared.get("ultimate_package_runtime_input_contract")
    final_authority = shared.get("broker_live_final_authority")
    options = shared.get("execution_options")
    source_option = options.get("source_acceleration") if isinstance(options, Mapping) else None
    _require(
        isinstance(symbols, list)
        and len(symbols) == 24
        and symbols == sorted(set(symbols))
        and isinstance(package, Mapping)
        and package.get("valid") is True
        and package.get("live_broker_authority") is False
        and package.get("broker_mutation_enabled") is False
        and package.get("final_selection_claim") is False
        and final_authority
        == {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        }
        and isinstance(source_option, Mapping)
        and source_option.get("source_plan_digest_sha256")
        == semantic.EXPECTED_SOURCE_PLAN_DIGEST
        and source_option.get("policy_execution_entered") is False
        and source_option.get("candidate_cache_enabled") is False
        and source_option.get("policy_state_cache_enabled") is False,
        f"task6_{label}_shared_contract_safety_invalid",
    )
    return {
        "label": label,
        "shared_execution_contract_digest_sha256": declared_digest,
        "semantic_payload_root_sha256": replay.stable_sha256(semantic_payload),
        "code_authority_root_sha256": semantic.canonical_sha256(code_rows),
        "exact_profile_config_roots_sha256": dict(exact_configs),
        "exact_risk_profile_bindings": copy.deepcopy(dict(risk_bindings)),
    }


def validate_shared_contract_successor(
    consumed: Mapping[str, Any],
    corrected: Mapping[str, Any],
) -> dict[str, Any]:
    """Allow only the enumerated pack-orchestrator implementation successor."""

    consumed_proof = validate_shared_execution_contract(
        consumed,
        label="consumed",
    )
    try:
        corrected_proof = validate_shared_execution_contract(
            corrected,
            label="corrected",
        )
    except Task6PreparedPackAcceptanceRejected as exc:
        raise Task6PreparedPackAcceptanceRejected(
            "task6_shared_contract_successor_unexpected_difference"
        ) from exc
    consumed_rows = consumed.get("code_authority") or []
    corrected_rows = corrected.get("code_authority") or []
    _require(
        [row["path"] for row in consumed_rows]
        == [row["path"] for row in corrected_rows],
        "task6_shared_contract_successor_unexpected_difference",
    )
    changed_paths: list[str] = []
    for left, right in zip(consumed_rows, corrected_rows):
        path = str(left["path"])
        if left["sha256"] != right["sha256"]:
            _require(
                path in ALLOWED_SHARED_CONTRACT_SUCCESSOR_CODE_PATHS,
                "task6_shared_contract_successor_unexpected_difference",
            )
            changed_paths.append(path)

    left_projection = copy.deepcopy(dict(consumed))
    right_projection = copy.deepcopy(dict(corrected))
    for projection in (left_projection, right_projection):
        projection["shared_execution_contract_digest_sha256"] = None
        for row in projection["code_authority"]:
            if row["path"] in ALLOWED_SHARED_CONTRACT_SUCCESSOR_CODE_PATHS:
                row["sha256"] = None
    _require(
        semantic.canonical_bytes(left_projection)
        == semantic.canonical_bytes(right_projection),
        "task6_shared_contract_successor_unexpected_difference",
    )
    return {
        "status": "TASK6_SHARED_CONTRACT_SUCCESSOR_FINITE_AND_CAUSAL_EXACT",
        "consumed": consumed_proof,
        "corrected": corrected_proof,
        "allowed_code_path_changes": changed_paths,
        "causal_config_source_or_reducer_change_count": 0,
    }


def _validate_runtime_evidence_contract(
    runtime: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    expected_fields = {
        "contract_root_sha256",
        "data_roots",
        "inputs",
        "integration_repo_root",
        "legacy_evidence_mutation_enabled",
        "read_only_existing_evidence",
        "root",
        "schema",
    }
    _require(
        isinstance(runtime, Mapping) and set(runtime) == expected_fields,
        f"task6_{label}_runtime_contract_invalid",
    )
    core = copy.deepcopy(dict(runtime))
    declared = core.pop("contract_root_sha256", None)
    inputs = runtime.get("inputs")
    _require(
        runtime.get("schema") == "gtos.replay_acceleration.runtime_evidence_root.v1"
        and runtime.get("legacy_evidence_mutation_enabled") is False
        and runtime.get("read_only_existing_evidence") is True
        and semantic._is_sha256(declared)
        and declared == replay.stable_sha256(core)
        and isinstance(inputs, Mapping)
        and bool(inputs),
        f"task6_{label}_runtime_contract_invalid",
    )
    for name, row in inputs.items():
        _require(
            isinstance(name, str)
            and isinstance(row, Mapping)
            and type(row.get("present")) is bool
            and type(row.get("required_by_actual_replay_path")) is bool
            and (
                row.get("present") is False
                or (
                    isinstance(row.get("path"), str)
                    and bool(row["path"])
                    and semantic._is_sha256(row.get("sha256"))
                    and type(row.get("bytes")) is int
                    and row["bytes"] > 0
                )
            )
            and not (
                row.get("required_by_actual_replay_path") is True
                and row.get("present") is not True
            ),
            f"task6_{label}_runtime_contract_invalid",
        )
    return {
        "contract_root_sha256": declared,
        "input_count": len(inputs),
        "read_only_existing_evidence": True,
    }


def _validate_source_authority(
    source: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    expected_fields = {
        "bundle_validation_seconds",
        "candidate_cache_enabled",
        "config_projection_root_sha256",
        "cross_symbol_prewarm_barrier",
        "normalizer_code_root_sha256",
        "partition_count",
        "policy_execution_entered",
        "policy_state_cache_enabled",
        "schema",
        "selection_root_sha256",
        "source_bundle_consumer_rebind_authority",
        "source_bundle_root_sha256",
        "source_plan_digest_sha256",
        "symbol_count",
        "typed_cache_metrics",
    }
    _require(
        isinstance(source, Mapping)
        and set(source) == expected_fields
        and source.get("schema")
        == "gtos.replay_acceleration.real_source_authority.v1"
        and source.get("source_plan_digest_sha256")
        == semantic.EXPECTED_SOURCE_PLAN_DIGEST
        and source.get("symbol_count") == 24
        and source.get("partition_count") == 96
        and source.get("policy_execution_entered") is False
        and source.get("candidate_cache_enabled") is False
        and source.get("policy_state_cache_enabled") is False
        and semantic._is_sha256(source.get("source_bundle_root_sha256"))
        and semantic._is_sha256(source.get("selection_root_sha256"))
        and semantic._is_sha256(source.get("config_projection_root_sha256"))
        and semantic._is_sha256(source.get("normalizer_code_root_sha256")),
        f"task6_{label}_source_authority_invalid",
    )
    binding = source.get("source_bundle_consumer_rebind_authority")
    expected_binding_fields = {
        "authority",
        "authority_file_sha256",
        "authority_path",
        "authority_root_sha256",
        "binding_root_sha256",
        "broker_live_authority",
        "continuation_authorized",
        "economic_values_exposed",
        "policy_execution_entered",
        "schema",
        "source_plan_digest_sha256",
        "verified_successor_bundle",
        "verified_successor_selection",
    }
    _require(
        isinstance(binding, Mapping)
        and set(binding) == expected_binding_fields,
        f"task6_{label}_source_rebind_invalid",
    )
    binding_core = copy.deepcopy(dict(binding))
    binding_root = binding_core.pop("binding_root_sha256", None)
    authority = binding.get("authority")
    authority_projection = copy.deepcopy(dict(authority or {}))
    authority_root = authority_projection.pop("authority_root_sha256", None)
    successor_bundle = binding.get("verified_successor_bundle")
    successor_selection = binding.get("verified_successor_selection")
    _require(
        binding.get("schema")
        == "gtos.replay_acceleration.bound_source_bundle_consumer_rebind_authority.v1"
        and binding.get("source_plan_digest_sha256")
        == semantic.EXPECTED_SOURCE_PLAN_DIGEST
        and binding.get("policy_execution_entered") is False
        and binding.get("continuation_authorized") is False
        and binding.get("broker_live_authority") is False
        and binding.get("economic_values_exposed") is False
        and semantic._is_sha256(binding_root)
        and binding_root == replay.stable_sha256(binding_core)
        and isinstance(authority, Mapping)
        and authority.get("status")
        == "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        and authority.get("policy_execution_entered") is False
        and authority.get("broker_live_authority") is False
        and authority.get("economic_values_exposed") is False
        and authority.get("continuation_authorized") is False
        and semantic._is_sha256(authority_root)
        and authority_root == replay.stable_sha256(authority_projection)
        and authority_root == binding.get("authority_root_sha256")
        and isinstance(successor_bundle, Mapping)
        and successor_bundle.get("bundle_root_sha256")
        == source.get("source_bundle_root_sha256")
        and isinstance(successor_selection, Mapping)
        and successor_selection.get("selection_root_sha256")
        == source.get("selection_root_sha256"),
        f"task6_{label}_source_rebind_invalid",
    )
    authority_path = _regular_file(
        Path(str(binding.get("authority_path"))),
        label=f"{label}_source_rebind",
    )
    _require(
        _file_sha256(authority_path) == binding.get("authority_file_sha256"),
        f"task6_{label}_source_rebind_invalid",
    )
    return {
        "source_plan_digest_sha256": source["source_plan_digest_sha256"],
        "source_bundle_root_sha256": source["source_bundle_root_sha256"],
        "selection_root_sha256": source["selection_root_sha256"],
        "binding_root_sha256": binding_root,
        "authority_root_sha256": authority_root,
    }


def _validate_original_summary_authority(
    summary: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    arm = summary.get("b7_5_selection_sizing_factorial_arm_binding")
    shared = summary.get("shared_execution_contract")
    binding = summary.get("b7_5_contract_binding")
    runtime = summary.get("runtime_evidence_contract")
    source = summary.get("source_acceleration_authority")
    _require(
        isinstance(arm, Mapping)
        and arm.get("arm_id") == "S0R0"
        and arm.get("arm_fingerprint_sha256")
        == semantic.EXPECTED_ARM_FINGERPRINT
        and arm.get("valid") is True
        and arm.get("uses_outcome_fields") is False
        and arm.get("broker_mutation_enabled") is False
        and arm.get("live_broker_authority") is False,
        f"task6_{label}_arm_contract_invalid",
    )
    shared_proof = validate_shared_execution_contract(shared, label=label)
    _require(
        isinstance(binding, Mapping)
        and set(binding)
        == {
            "actual_shared_execution_contract_digest_sha256",
            "actual_source_plan_digests_sha256",
            "expected_shared_execution_contract_digest_sha256",
            "expected_source_plan_digest_sha256",
            "required",
            "selection_sizing_factorial_arm_binding",
            "status",
            "valid",
        }
        and binding.get("required") is True
        and binding.get("valid") is True
        and binding.get("status") == "b7_5_source_and_execution_contracts_bound"
        and binding.get("expected_source_plan_digest_sha256")
        == semantic.EXPECTED_SOURCE_PLAN_DIGEST
        and binding.get("actual_source_plan_digests_sha256")
        == [semantic.EXPECTED_SOURCE_PLAN_DIGEST]
        and binding.get("actual_shared_execution_contract_digest_sha256")
        == binding.get("expected_shared_execution_contract_digest_sha256")
        == shared_proof["shared_execution_contract_digest_sha256"]
        and semantic.canonical_bytes(
            binding.get("selection_sizing_factorial_arm_binding")
        )
        == semantic.canonical_bytes(arm),
        f"task6_{label}_b7_contract_invalid",
    )
    runtime_proof = _validate_runtime_evidence_contract(runtime, label=label)
    source_proof = _validate_source_authority(source, label=label)
    shared_source = shared.get("execution_options", {}).get(
        "source_acceleration"
    )
    for key in (
        "source_bundle_root_sha256",
        "selection_root_sha256",
        "source_plan_digest_sha256",
        "config_projection_root_sha256",
        "normalizer_code_root_sha256",
        "partition_count",
        "symbol_count",
        "policy_execution_entered",
        "candidate_cache_enabled",
        "policy_state_cache_enabled",
        "source_bundle_consumer_rebind_authority",
    ):
        _require(
            isinstance(shared_source, Mapping)
            and semantic.canonical_bytes(shared_source.get(key))
            == semantic.canonical_bytes(source.get(key)),
            f"task6_{label}_shared_source_binding_invalid",
        )
    _require(
        summary.get("live_broker_authority") is False
        and summary.get("broker_mutation_enabled") is False,
        f"task6_{label}_broker_boundary_open",
    )
    return {
        "status": "ORIGINAL_SUMMARY_AUTHORITY_STRICTLY_AUTHENTICATED",
        "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
        "shared_contract": shared_proof,
        "runtime_evidence": runtime_proof,
        "source_authority": source_proof,
    }


def _validate_source_rebind_authority() -> dict[str, Any]:
    path = _regular_file(SOURCE_REBIND_AUTHORITY, label="source_rebind")
    _require(
        _file_sha256(path) == EXPECTED_SOURCE_REBIND_FILE_SHA256,
        "task6_source_rebind_file_mismatch",
    )
    authority = _load_json(path)
    _require(
        authority.get("authority_root_sha256")
        == EXPECTED_SOURCE_REBIND_ROOT_SHA256
        and authority.get("status")
        == "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        and authority.get("broker_live_authority") is False
        and authority.get("policy_execution_entered") is False,
        "task6_source_rebind_authority_invalid",
    )
    return {
        "path": str(path),
        "sha256": EXPECTED_SOURCE_REBIND_FILE_SHA256,
        "authority_root_sha256": EXPECTED_SOURCE_REBIND_ROOT_SHA256,
        "status": authority["status"],
    }


def _validate_task5_acceptance_receipt() -> dict[str, Any]:
    path = _regular_file(TASK5_ACCEPTANCE_RECEIPT, label="task5_acceptance")
    _require(
        _file_sha256(path) == EXPECTED_TASK5_ACCEPTANCE_FILE_SHA256,
        "task6_task5_acceptance_file_mismatch",
    )
    receipt = _load_json(path)
    _validate_self_root(receipt, label="task5_acceptance")
    accelerated = receipt.get("accelerated_execution")
    manifests = receipt.get("semantic_source_manifests")
    bindings = receipt.get("semantic_manifest_receipt_shared_contract_bindings")
    _require(
        receipt.get("schema")
        == "gtos.replay_acceleration.task5_compact_sink_acceptance.v1"
        and receipt.get("status") == "TASK5_COMPACT_EVENT_SINK_EXACT_AND_BOUNDED"
        and receipt.get("task") == "Replay-Acceleration Task 5"
        and receipt.get("acceptance_authorized") is False
        and receipt.get("broker_live_authority") is False
        and receipt.get("broker_mutation_enabled") is False
        and receipt.get("meaningful_difference_count") == 0
        and receipt.get("unknown_difference_count") == 0
        and receipt.get("receipt_root_sha256")
        == EXPECTED_TASK5_ACCEPTANCE_ROOT_SHA256
        and isinstance(accelerated, Mapping)
        and accelerated.get("receipt_sha256")
        == "5ddbc4bdcd8b859643d1e5a29e8f707cbdf1e626a49d22a1e0774e7fa431ff5c"
        and accelerated.get("receipt_root_sha256")
        == "426df240c4f65999654ddfb9e6d69a3024cf5b2b0752e2e0f6d6ec6b7b08d32e"
        and isinstance(manifests, Mapping)
        and manifests.get("accelerated", {}).get(
            "shared_execution_contract_digest_sha256"
        )
        == accelerated.get("shared_execution_contract_digest_sha256")
        and bindings
        == [
            {
                "label": "reference",
                "shared_execution_contract_digest_sha256": (
                    receipt["reference_execution"]
                    ["shared_execution_contract_digest_sha256"]
                ),
            },
            {
                "label": "accelerated",
                "shared_execution_contract_digest_sha256": accelerated[
                    "shared_execution_contract_digest_sha256"
                ],
            },
        ],
        "task6_task5_acceptance_invalid",
    )
    execution_receipt = TASK5_REFERENCE_ROOT / "TASK2_SEMANTIC_SLICE_EXECUTION_RECEIPT.json"
    _require(
        _file_sha256(_regular_file(execution_receipt, label="task5_execution"))
        == accelerated["receipt_sha256"],
        "task6_task5_execution_receipt_mismatch",
    )
    return {
        "path": str(path),
        "sha256": EXPECTED_TASK5_ACCEPTANCE_FILE_SHA256,
        "receipt_root_sha256": EXPECTED_TASK5_ACCEPTANCE_ROOT_SHA256,
        "reference_execution_receipt_sha256": accelerated["receipt_sha256"],
        "status": receipt["status"],
    }


def _validate_semantic_manifest(
    root: Path,
    *,
    expected_file_sha256: str,
    expected_shared_digest: str,
    label: str,
) -> dict[str, Any]:
    manifest_path = semantic._semantic_paths(root)["manifest"]
    _require(
        _file_sha256(_regular_file(manifest_path, label=f"{label}_manifest"))
        == expected_file_sha256,
        f"task6_{label}_semantic_manifest_file_mismatch",
    )
    try:
        validated = semantic.validate_semantic_source_manifest(root)
    except semantic.SemanticAcceptanceError as exc:
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_{label}_semantic_manifest_invalid:{exc}"
        ) from None
    _require(
        validated.get("shared_execution_contract_digest_sha256")
        == expected_shared_digest,
        f"task6_{label}_semantic_manifest_contract_mismatch",
    )
    return {
        "path": str(manifest_path),
        "sha256": expected_file_sha256,
        **validated,
    }


def _validate_completed_execution_summary(
    execution_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    final_path = execution_root / f"{semantic.PREFIX}_SUMMARY.json"
    partial_path = execution_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    _require(
        _file_sha256(_regular_file(final_path, label="execution_final"))
        == EXPECTED_EXECUTION_FINAL_SHA256
        and _file_sha256(
            _regular_file(partial_path, label="execution_partial")
        )
        == EXPECTED_EXECUTION_PARTIAL_SHA256,
        "task6_execution_summary_file_mismatch",
    )
    final = _load_json(final_path)
    partial = _load_json(partial_path)
    builds = final.get("prepared_day_pack_build_receipts")
    checkpoints = final.get("prepared_day_pack_checkpoints")
    progress = final.get("progress_rows")
    _require(
        final.get("status")
        == "broad_live_as_if_replay_materialized_broker_live_closed"
        and final.get("prepared_day_pack_enabled") is True
        and final.get("engineering_stop_after_day") == EXPECTED_DAYS[-1]
        and final.get("engineering_stop_is_acceptance_gate") is False
        and isinstance(builds, list)
        and len(builds) == 2
        and isinstance(checkpoints, list)
        and len(checkpoints) == 2
        and isinstance(progress, list)
        and len(progress) == 2,
        "task6_completed_execution_summary_invalid",
    )
    _require(
        final.get("live_broker_authority") is False
        and final.get("broker_mutation_enabled") is False
        and all(
            int(value) == 0
            for value in (final.get("order_send_attempts") or {}).values()
        ),
        "task6_execution_broker_boundary_open",
    )
    checkpoint_proofs = []
    for index, (day, build, checkpoint) in enumerate(
        zip(EXPECTED_DAYS, builds, checkpoints)
    ):
        _require(
            isinstance(build, Mapping)
            and isinstance(checkpoint, Mapping)
            and build.get("status") == "SEALED_ARM_NEUTRAL_PREPARATION"
            and build.get("days") == [day]
            and build.get("record_count") == 96
            and checkpoint.get("status")
            == "authenticated_before_chronological_reducer"
            and checkpoint.get("days") == [day]
            and checkpoint.get("pack_root_sha256")
            == build.get("pack_root_sha256")
            and checkpoint.get("broker_mutation_enabled") is False
            and checkpoint.get("live_authority_touched") is False,
            f"task6_execution_pack_checkpoint_invalid:{index}",
        )
        _require(
            build.get("pack_root_sha256")
            == EXPECTED_CONSUMED_PACKS[index]["pack_root_sha256"]
            and _file_sha256(
                _regular_file(
                    Path(str(build["path"])) / "PREPARED_DAY_PACK_MANIFEST.json",
                    label=f"consumed_pack_manifest_{index}",
                )
            )
            == EXPECTED_CONSUMED_PACKS[index]["manifest_sha256"],
            f"task6_execution_pack_identity_mismatch:{index}",
        )
        checkpoint_proofs.append(
            {
                "day": day,
                "path": str(checkpoint["path"]),
                "pack_root_sha256": checkpoint["pack_root_sha256"],
                "status": checkpoint["status"],
            }
        )
    return final, {
        "status": "TASK6_PACKS_AUTHENTICATED_BEFORE_PRIVATE_CHRONOLOGICAL_REDUCER",
        "final_summary": {
            "path": str(final_path),
            "bytes": final_path.stat().st_size,
            "sha256": _file_sha256(final_path),
        },
        "partial_summary": {
            "path": str(partial_path),
            "bytes": partial_path.stat().st_size,
            "sha256": _file_sha256(partial_path),
        },
        "checkpoints": checkpoint_proofs,
    }


def _validate_execution_contract_bridge(
    execution_summary: Mapping[str, Any],
    corrected_summary: Mapping[str, Any],
    corrected_build: Mapping[str, Any],
) -> dict[str, Any]:
    execution_authority = _validate_original_summary_authority(
        execution_summary,
        label="execution",
    )
    corrected_authority = _validate_original_summary_authority(
        corrected_summary,
        label="corrected",
    )
    execution_arm = execution_summary[
        "b7_5_selection_sizing_factorial_arm_binding"
    ]
    corrected_arm = corrected_summary[
        "b7_5_selection_sizing_factorial_arm_binding"
    ]
    execution_shared = execution_summary["shared_execution_contract"]
    corrected_shared = corrected_summary["shared_execution_contract"]
    successor = validate_shared_contract_successor(
        execution_shared,
        corrected_shared,
    )
    execution_runtime = execution_summary["runtime_evidence_contract"]
    corrected_runtime = corrected_summary["runtime_evidence_contract"]
    _require(
        semantic.canonical_bytes(execution_arm)
        == semantic.canonical_bytes(corrected_arm)
        and execution_runtime.get("contract_root_sha256")
        == corrected_runtime.get("contract_root_sha256")
        == corrected_build.get("runtime_input_contract_root_sha256")
        and corrected_shared.get("shared_execution_contract_digest_sha256")
        == corrected_build.get("shared_execution_contract_digest_sha256"),
        "task6_execution_contract_bridge_invalid",
    )
    return {
        "status": "TASK6_EXECUTION_AND_CORRECTED_PREPARATION_CONTRACTS_BOUND",
        "arm_id": "S0R0",
        "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
        "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
        "runtime_input_contract_root_sha256": execution_runtime[
            "contract_root_sha256"
        ],
        "consumed_execution_shared_contract_digest_sha256": execution_shared[
            "shared_execution_contract_digest_sha256"
        ],
        "corrected_preparation_shared_contract_digest_sha256": corrected_build[
            "shared_execution_contract_digest_sha256"
        ],
        "implementation_successor": successor,
        "execution_authority": execution_authority,
        "corrected_authority": corrected_authority,
        "implementation_successor_digest_change_allowed": (
            bool(successor["allowed_code_path_changes"])
        ),
        "causal_and_economic_contract_change_allowed": False,
    }


def _validate_corrected_build(
    corrected_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    engine_path = corrected_root / "PREPARED_DAY_PACK_BUILD_ONLY_RECEIPT.json"
    receipt_path = corrected_root / task6_runner.PACK_ONLY_RECEIPT_NAME
    partial_path = corrected_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    _require(
        _file_sha256(_regular_file(engine_path, label="corrected_engine"))
        == EXPECTED_CORRECTED_ENGINE_SHA256
        and _file_sha256(
            _regular_file(receipt_path, label="corrected_pack_receipt")
        )
        == EXPECTED_CORRECTED_PACK_RECEIPT_SHA256
        and _file_sha256(
            _regular_file(partial_path, label="corrected_partial")
        )
        == EXPECTED_CORRECTED_PARTIAL_SHA256,
        "task6_corrected_evidence_file_mismatch",
    )
    engine = _load_json(engine_path)
    receipt = _load_json(receipt_path)
    partial = _load_json(partial_path)
    _validate_self_root(engine, label="engine_build")
    _validate_self_root(receipt, label="factor_neutral_build")
    source = engine.get("canonical_source_ledger")
    reset = engine.get("preparation_source_emission_reset")
    _require(
        engine.get("status") == "PREPARED_DAY_PACK_BUILD_ONLY_COMPLETE"
        and engine.get("policy_execution_entered") is False
        and engine.get("broker_live_authority") is False
        and engine.get("broker_mutation_enabled") is False
        and engine.get("economic_values_exposed") is False
        and isinstance(source, Mapping)
        and source.get("rows") == 867
        and source.get("sha256") == EXPECTED_SOURCE_LEDGER_SHA256
        and isinstance(reset, Mapping)
        and reset.get("source_or_economic_payload_changed") is False,
        "task6_corrected_engine_build_invalid",
    )
    packs = (receipt.get("prepared_day_packs") or {}).get("packs")
    engine_builds = engine.get("prepared_day_pack_build_receipts")
    _require(
        receipt.get("status")
        == "TASK6_FACTOR_NEUTRAL_PACKS_BUILT_AND_WORKER_STABLE"
        and receipt.get("factorial_values_present_in_preparation_config") is False
        and receipt.get("policy_execution_entered") is False
        and receipt.get("broker_live_authority") is False
        and receipt.get("broker_mutation_enabled") is False
        and receipt.get("engine_build_receipt_root_sha256")
        == engine.get("receipt_root_sha256")
        and isinstance(packs, list)
        and len(packs) == 2
        and isinstance(engine_builds, list)
        and len(engine_builds) == 2
        and all(row.get("one_worker_four_worker_identity") is True for row in packs),
        "task6_corrected_pack_receipt_invalid",
    )
    for index, row in enumerate(packs):
        engine_build = engine_builds[index]
        _require(
            row.get("pack_root_sha256")
            == EXPECTED_CORRECTED_PACKS[index]["pack_root_sha256"]
            == engine_build.get("pack_root_sha256")
            and _file_sha256(
                _regular_file(
                    Path(str(engine_build["path"]))
                    / "PREPARED_DAY_PACK_MANIFEST.json",
                    label=f"corrected_pack_manifest_{index}",
                )
            )
            == EXPECTED_CORRECTED_PACKS[index]["manifest_sha256"],
            f"task6_corrected_pack_identity_mismatch:{index}",
        )
    return engine, partial, {
        "status": "TASK6_CORRECTED_FACTOR_NEUTRAL_BUILD_AUTHENTICATED",
        "engine_build_receipt_root_sha256": engine["receipt_root_sha256"],
        "factor_neutral_build_receipt_root_sha256": receipt[
            "receipt_root_sha256"
        ],
        "preparation_source_emission_reset": dict(reset),
        "one_worker_four_worker_identity": True,
        "pack_roots": [row["pack_root_sha256"] for row in packs],
        "shared_execution_contract_digest_sha256": receipt[
            "shared_execution_contract_digest_sha256"
        ],
        "runtime_input_contract_root_sha256": receipt[
            "runtime_input_contract_root_sha256"
        ],
    }


def _semantic_output_comparison(
    reference_root: Path,
    execution_root: Path,
    *,
    reference_summary: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
) -> dict[str, Any]:
    role_proof = {
        "broker_order_lifecycle_capture_v4_packet/pre_order_capture_contract/"
        "execution_manager_packet_hash": "PREIMAGE"
    }
    comparisons = []
    for role in semantic.ROLE_SUFFIXES:
        if role == "source":
            continue
        try:
            comparisons.append(
                semantic.compare_role_rows(
                    role,
                    semantic._role_rows(reference_root, role),
                    semantic._role_rows(execution_root, role),
                    derived_hash_proofs=role_proof,
                )
            )
        except semantic.SemanticAcceptanceError as exc:
            raise Task6PreparedPackAcceptanceRejected(
                f"task6_role_semantic_mismatch:{role}:{exc}"
            ) from None
    try:
        preimages = task3.compare_order_preimages(reference_root, execution_root)
        exact_semantic = [
            task3._exact_semantic_file(
                semantic._semantic_paths(reference_root)[role],
                semantic._semantic_paths(execution_root)[role],
                role=role,
            )
            for role in ("candidate", "state")
        ]
        reference_projected, reference_sink = task5.project_task5_summary(
            reference_summary
        )
        execution_projected, execution_sink = task5.project_task5_summary(
            execution_summary
        )
        left, right, runtime_projection = project_task6_runtime_envelope_pair(
            reference_projected,
            execution_projected,
        )
        summary = semantic.compare_summary_semantics(
            left,
            right,
            end_day=EXPECTED_DAYS[-1],
        )
    except (
        semantic.SemanticAcceptanceError,
        task3.Task3ExactCacheRejected,
        task5.Task5CompactSinkAcceptanceRejected,
    ) as exc:
        raise Task6PreparedPackAcceptanceRejected(
            f"task6_semantic_projection_mismatch:{exc}"
        ) from None
    return {
        "status": "TASK6_CAUSAL_AND_ECONOMIC_OUTPUTS_SEMANTICALLY_EXACT",
        "role_comparisons": comparisons,
        "order_preimage_comparison": preimages,
        "exact_semantic_files": exact_semantic,
        "summary_semantics": summary,
        "task5_reference_sink_projection": reference_sink,
        "task6_execution_sink_projection": execution_sink,
        "task6_runtime_projection": runtime_projection,
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
    }


def run_acceptance(
    reference_root: Path,
    execution_root: Path,
    corrected_root: Path,
) -> dict[str, Any]:
    reference_root = Path(os.path.abspath(reference_root))
    execution_root = Path(os.path.abspath(execution_root))
    corrected_root = Path(os.path.abspath(corrected_root))
    _require(
        reference_root == TASK5_REFERENCE_ROOT.resolve(),
        "task6_reference_root_unbound",
    )
    _require(
        execution_root == TASK6_EXECUTION_ROOT.resolve(),
        "task6_execution_root_unbound",
    )
    _require(
        corrected_root == TASK6_CORRECTED_ROOT.resolve(),
        "task6_corrected_root_unbound",
    )
    _require(
        len({reference_root, execution_root, corrected_root}) == 3,
        "task6_evidence_roots_not_distinct",
    )
    reference_partial_path = (
        reference_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    _require(
        _file_sha256(
            _regular_file(reference_partial_path, label="reference_partial")
        )
        == EXPECTED_REFERENCE_PARTIAL_SHA256,
        "task6_reference_summary_file_mismatch",
    )
    reference_partial = _load_json(reference_partial_path)
    task5_acceptance = _validate_task5_acceptance_receipt()
    execution_final, execution_envelope = _validate_completed_execution_summary(
        execution_root
    )
    # Preserve Task 5's bounded-reconstruction measurement boundary: perform
    # it before semantic diff bookkeeping or prepared-record authentication can
    # raise this process's monotonic peak-RSS counter.
    reconstruction = task5.validate_sink_reconstruction(
        execution_root,
        execution_final,
    )
    execution_partial = _load_json(
        execution_root / f"{semantic.PREFIX}_PARTIAL_SUMMARY.json"
    )
    corrected_engine, corrected_partial, corrected_build = (
        _validate_corrected_build(corrected_root)
    )
    source_rebind = _validate_source_rebind_authority()
    reference_authority = _validate_original_summary_authority(
        reference_partial,
        label="reference",
    )
    execution_partial_authority = _validate_original_summary_authority(
        execution_partial,
        label="execution_partial",
    )
    execution_contract = _validate_execution_contract_bridge(
        execution_final,
        corrected_partial,
        corrected_build,
    )
    reference_manifest = _validate_semantic_manifest(
        reference_root,
        expected_file_sha256=EXPECTED_REFERENCE_SEMANTIC_MANIFEST_SHA256,
        expected_shared_digest=reference_partial["shared_execution_contract"][
            "shared_execution_contract_digest_sha256"
        ],
        label="reference",
    )
    execution_manifest = _validate_semantic_manifest(
        execution_root,
        expected_file_sha256=EXPECTED_EXECUTION_SEMANTIC_MANIFEST_SHA256,
        expected_shared_digest=execution_partial["shared_execution_contract"][
            "shared_execution_contract_digest_sha256"
        ],
        label="execution",
    )

    reference_source = semantic._role_path(reference_root, "source")
    execution_source = semantic._role_path(execution_root, "source")
    corrected_source = semantic._role_path(corrected_root, "source")
    canonical_source = compare_jsonl_file_exact(
        reference_source,
        corrected_source,
        label="source",
    )
    _require(
        canonical_source["sha256"] == EXPECTED_SOURCE_LEDGER_SHA256,
        "task6_source_authority_digest_mismatch",
    )
    superseded_source = compare_jsonl_multiset_exact(
        reference_source,
        execution_source,
        label="superseded_execution_source",
    )

    builds = execution_final["prepared_day_pack_build_receipts"]
    corrected_builds = corrected_engine["prepared_day_pack_build_receipts"]
    factor_root = str(
        corrected_builds[0]["campaign_exact_cache_audit"]["config_root_sha256"]
    )
    _require(
        all(
            row["campaign_exact_cache_audit"]["config_root_sha256"]
            == factor_root
            for row in corrected_builds
        ),
        "task6_corrected_pack_config_root_inconsistent",
    )
    four_arm_roots = derive_four_arm_factor_neutral_roots()
    four_arm_proof = validate_four_arm_factor_neutral_roots(
        four_arm_roots,
        expected_root_sha256=factor_root,
    )
    pack_bridges = []
    for index, day in enumerate(EXPECTED_DAYS):
        pack_bridges.append(
            validate_pack_record_bridge(
                consumed_pack_root=Path(str(builds[index]["path"])),
                corrected_pack_root=Path(str(corrected_builds[index]["path"])),
                expected_consumed_pack_root_sha256=(
                    EXPECTED_CONSUMED_PACKS[index]["pack_root_sha256"]
                ),
                expected_corrected_pack_root_sha256=(
                    EXPECTED_CORRECTED_PACKS[index]["pack_root_sha256"]
                ),
                expected_factor_neutral_config_root_sha256=factor_root,
            )
        )

    semantic_outputs = _semantic_output_comparison(
        reference_root,
        execution_root,
        reference_summary=reference_partial,
        execution_summary=execution_partial,
    )
    reference_progress = reference_partial.get("progress_rows") or []
    execution_progress = execution_final.get("progress_rows") or []
    _require(
        len(reference_progress) == len(execution_progress) == 2,
        "task6_performance_progress_invalid",
    )
    reference_dense = float(reference_progress[1]["economic_hot_path_seconds"])
    execution_dense = float(execution_progress[1]["economic_hot_path_seconds"])
    execution_no_event = float(execution_progress[0]["economic_hot_path_seconds"])
    dense_improvement = reference_dense - execution_dense
    core = {
        "schema": SCHEMA,
        "status": STATUS,
        "task": TASK_NAME,
        "acceptance_authorized": False,
        "task_gate_authorized": True,
        "reference_root": str(reference_root),
        "completed_execution_root": str(execution_root),
        "corrected_factor_neutral_build_root": str(corrected_root),
        "task5_accepted_reference": task5_acceptance,
        "strict_original_authority_authentication": {
            "reference": reference_authority,
            "execution_partial": execution_partial_authority,
            "semantic_source_manifests": {
                "reference": reference_manifest,
                "execution": execution_manifest,
            },
        },
        "execution_evidence": execution_envelope,
        "corrected_build_evidence": corrected_build,
        "source_rebind_authority": source_rebind,
        "execution_contract": execution_contract,
        "source_emission": {
            "canonical_corrected_source": canonical_source,
            "superseded_execution_source": superseded_source,
            "disposition": (
                "old_execution_source_rows_content_exact_but_proof_order_was_"
                "perturbed_by_shared_resolver;corrected_separate_resolver_is_"
                "byte_exact_to_task5"
            ),
            "causal_or_economic_source_difference_count": 0,
        },
        "prepared_pack_record_bridges": pack_bridges,
        "four_arm_factor_neutral_preparation": four_arm_proof,
        "semantic_outputs": semantic_outputs,
        "compact_sink_reconstruction": reconstruction,
        "performance": {
            "task5_reference_dense_day_economic_hot_path_seconds": reference_dense,
            "task6_prepared_pack_dense_day_economic_hot_path_seconds": execution_dense,
            "dense_day_economic_hot_path_improvement_seconds": dense_improvement,
            "dense_day_economic_hot_path_improvement_fraction": (
                dense_improvement / reference_dense
            ),
            "task6_no_event_day_economic_hot_path_seconds": execution_no_event,
            "no_event_day_economic_hot_path_target_seconds": 5.0,
            "no_event_day_economic_hot_path_target_passed": (
                execution_no_event <= 5.0
            ),
            "final_no_event_day_end_to_end_target_seconds": 5.0,
            "final_no_event_day_end_to_end_target_proven": False,
            "final_no_event_day_end_to_end_target_status": "UNPROVEN_UNTIL_TASK9",
            "final_dense_day_target_seconds": 180.0,
            "final_dense_day_target_passed": execution_dense <= 180.0,
            "standalone_end_to_end_speedup_claimed": False,
            "final_end_to_end_acceptance_deferred_to_task9": True,
            "next_measured_kernel_task": "Replay-Acceleration Task 8",
        },
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "causal_or_economic_field_normalized": False,
        "physical_reference_route_invoked": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    return {**core, "receipt_root_sha256": semantic.canonical_sha256(core)}


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(os.path.abspath(path))
    _require(
        not path.exists() and not path.is_symlink(),
        "task6_output_must_be_new",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    semantic.atomic_write_json(path, payload)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--execution-root", type=Path, required=True)
    parser.add_argument("--corrected-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_acceptance(
        args.reference_root,
        args.execution_root,
        args.corrected_root,
    )
    atomic_write_json(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
