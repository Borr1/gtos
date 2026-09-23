"""Independent opaque verifier for real Jan 1-7 S0R0 persisted results."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import stat
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from src.research_infra.replay_acceleration_partial_golden_verifier import (
    PartialGoldenVerificationError,
    verify_partial_golden_manifest,
)
from src.research_infra.replay_acceleration_contract_split import (
    ContractSplitError,
    split_shared_execution_contract,
)
from src.research_infra.replay_acceleration_fixed_verifier_authority import (
    MODULE_FILES as FIXED_VERIFIER_MODULE_FILES,
    SCHEMA as FIXED_VERIFIER_CODE_AUTHORITY_SCHEMA,
)
from src.research_infra.replay_acceleration_partial_golden_successor_authority import (
    SuccessorAuthorityError,
    verify_successor_authority,
)
from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    immutable_write_bytes,
)
from src.research_infra.replay_acceleration_streaming_archive_verifier import (
    verify_campaign,
    verify_campaign_with_role_line_consumer,
)


MANIFEST_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
MANIFEST_SCHEMA_V2 = "gtos.replay_acceleration.partial_golden_manifest.v2"
REQUEST_SCHEMA = "gtos.replay_acceleration.real_s0r0_gate_request.v1"
REQUEST_SCHEMA_V2 = "gtos.replay_acceleration.real_s0r0_gate_request.v2"
RECEIPT_SCHEMA = "gtos.replay_acceleration.real_s0r0_parity_receipt.v1"
REPORT_SCHEMA = "gtos.replay_acceleration.real_s0r0_parity_report.v1"
RECEIPT_SCHEMA_V2 = "gtos.replay_acceleration.real_s0r0_parity_receipt.v2"
REPORT_SCHEMA_V2 = "gtos.replay_acceleration.real_s0r0_parity_report.v2"
ARCHIVE_TRANSFORMATION_SCHEMA = (
    "gtos.replay_acceleration.partial_summary_archive_transformation.v1"
)
ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS = (
    "generated_at_utc",
    "streaming_proof_archive",
    "streaming_proof_archive_shards",
    "streaming_capacity_checks",
)
ACCELERATION_ENVELOPE_TRANSFORMATION_SCHEMA = (
    "gtos.replay_acceleration.partial_summary_acceleration_envelope.v2"
)
ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS = (
    "generated_at_utc",
    "shared_execution_contract",
    "b7_5_contract_binding",
    "runtime_evidence_contract",
    "source_acceleration_authority",
    "attempt5_execution_identity",
    "real_s0r0_parity_gate",
    "route_id",
)
ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES = (
    "capacity_safe_chunk_execution_contract.checkpoints[*].gc_collected_objects",
    "ledger_file_bytes_flushed_before_partial_summary.decision",
    "ledger_file_bytes_flushed_before_partial_summary.scorecard",
    "ledger_file_bytes_flushed_before_partial_summary.missed",
)
ATTEMPT5_EXECUTION_IDENTITY_KEYS = frozenset(
    {
        "schema",
        "status",
        "output_namespace",
        "output_prefix",
        "start_day",
        "parity_day",
        "contract_end_day",
        "arm_id",
        "expected_shared_execution_contract_sha256",
        "expected_source_plan_digest_sha256",
        "expected_arm_fingerprint_sha256",
        "expected_source_bundle_root_sha256",
        "expected_tick_source_manifest_sha256",
        "prospective_golden_authority",
        "runner_path",
        "runner_sha256",
        "source_bundle_consumer_rebind_authority",
        "source_prewarm_workers",
        "tick_diagnostic_manifest_bindings",
        "tick_source_manifest",
        "tick_sparse_cache",
        "policy_execution_entered",
        "legacy_replay_route_invoked",
        "other_arms_launched",
        "broker_live_authority",
        "broker_mutation_enabled",
        "economic_values_exposed",
        "identity_root_sha256",
    }
)
RUNTIME_EVIDENCE_CONTRACT_KEYS = frozenset(
    {
        "schema",
        "root",
        "integration_repo_root",
        "data_roots",
        "inputs",
        "legacy_evidence_mutation_enabled",
        "read_only_existing_evidence",
        "contract_root_sha256",
    }
)
RUNTIME_EVIDENCE_INPUT_NAMES = frozenset(
    {
        "accepted_member_ledger",
        "fillability_labels",
        "member_axis",
        "pending_source_coverage",
        "reconstructed_selection",
        "sleeve_registry",
        "source_materializer",
    }
)
RUNTIME_EVIDENCE_REQUIRED_INPUT_NAMES = frozenset(
    {
        "accepted_member_ledger",
        "fillability_labels",
        "member_axis",
        "reconstructed_selection",
        "sleeve_registry",
    }
)
SHARED_SOURCE_ACCELERATION_KEYS = frozenset(
    {
        "schema",
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
        "prewarm_worker_count",
    }
)
SOURCE_ACCELERATION_AUTHORITY_KEYS = frozenset(
    {
        *SHARED_SOURCE_ACCELERATION_KEYS,
        "cross_symbol_prewarm_barrier",
        "bundle_validation_seconds",
        "typed_cache_metrics",
    }
) - {"prewarm_worker_count"}
SOURCE_PREWARM_BARRIER_KEYS = frozenset(
    {
        "requested",
        "worker_count",
        "barrier_complete",
        "seconds",
        "partition_count",
        "partition_set_root_sha256",
    }
)
SOURCE_TYPED_CACHE_METRIC_KEYS = frozenset(
    {
        "bytes_read",
        "bytes_written",
        "cold_partition_count",
        "hashing_seconds",
        "normalization_seconds",
        "normalized_row_count",
        "serialization_seconds",
        "verification_seconds",
        "warm_partition_count",
    }
)
SOURCE_REBIND_KEYS = frozenset(
    {
        "schema",
        "authority",
        "authority_path",
        "authority_file_sha256",
        "authority_root_sha256",
        "source_plan_digest_sha256",
        "verified_successor_bundle",
        "verified_successor_selection",
        "policy_execution_entered",
        "continuation_authorized",
        "broker_live_authority",
        "economic_values_exposed",
        "binding_root_sha256",
    }
)
ATTEMPT5_RUNNER_RELATIVE_PATH = (
    "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
)
TICK_EXPORT_MANIFEST_KEYS = frozenset(
    {
        "account",
        "chunk_minutes",
        "created_at_utc",
        "errors",
        "files",
        "label",
        "manifest_path",
        "mt5_client_kind",
        "output_dir",
        "read_only",
        "schema_version",
        "source_provenance",
        "symbols",
        "terminal",
        "windows",
    }
)
ACCELERATION_ENVELOPE_KEYS = frozenset(
    {
        "schema",
        "golden_partial_summary",
        "accelerated_partial_summary",
        "allowed_top_level_changes",
        "allowed_nested_changes",
        "golden_nested_runtime_fields_root_sha256",
        "accelerated_nested_runtime_fields_root_sha256",
        "stable_projection_root_sha256",
        "legacy_shared_execution_contract_digest_sha256",
        "accelerated_shared_execution_contract_digest_sha256",
        "economic_execution_contract_digest_sha256",
        "accelerator_implementation_authority_root_sha256",
        "golden_envelope_root_sha256",
        "accelerated_envelope_root_sha256",
        "economic_values_exposed",
        "transformation_root_sha256",
    }
)
ARCHIVE_TRANSFORMATION_KEYS = frozenset(
    {
        "schema",
        "campaign_manifest_path",
        "campaign_manifest_root_sha256",
        "terminal_checkpoint_chain_root_sha256",
        "pre_archive_partial_summary",
        "post_archive_partial_summary",
        "allowed_top_level_changes",
        "stable_projection_root_sha256",
        "transformation_root_sha256",
    }
)
ARCHIVE_PRE_SUMMARY_KEYS = frozenset(
    {"path", "bytes", "sha256", "checkpoint_root_sha256"}
)
ARCHIVE_POST_SUMMARY_KEYS = frozenset({"path", "bytes", "sha256"})
FIXED_VERIFIER_MODULE = (
    "src.research_infra.replay_acceleration_real_parity_verifier"
)
PROSPECTIVE_GOLDEN_AUTHORITY_KEYS = frozenset(
    {
        "golden_manifest_path",
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_path",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_module",
        "fixed_verifier_path",
        "fixed_verifier_file_sha256",
    }
)
PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS = PROSPECTIVE_GOLDEN_AUTHORITY_KEYS | {
    "successor_authority_path",
    "successor_authority_file_sha256",
    "successor_authority_root_sha256",
    "successor_authority_verification_root_sha256",
    "economic_execution_contract_digest_sha256",
    "fixed_verifier_code_authority",
    "fixed_verifier_code_authority_root_sha256",
}
ROLES = (
    "source",
    "decision",
    "scorecard",
    "order",
    "trade",
    "oracle",
    "missed",
    "bucket",
)
EMPTY_SURFACE_CONTRACT = {
    "bytes": 0,
    "rows": 0,
    "sha256": hashlib.sha256(b"").hexdigest(),
}
REQUEST_KEYS = frozenset(
    {
        "schema",
        "output_prefix",
        "accelerated_namespace_path",
        "prospective_golden_authority",
        "scope",
        "source_plan_digest_sha256",
        "shared_execution_contract_sha256",
        "arm_fingerprint_sha256",
        "persisted_result_surfaces",
        "partial_summary",
        "partial_summary_archive_transformation",
        "policy_execution_entered",
        "actual_run_campaign_path",
        "synthetic_reducer_harness",
        "candidate_cache_enabled",
        "policy_state_cache_enabled",
        "other_arms_launched",
        "live_broker_authority",
        "broker_mutation_enabled",
        "economic_values_exposed",
        "gate_request_root_sha256",
    }
)
REQUEST_V2_KEYS = REQUEST_KEYS | {
    "economic_execution_contract_sha256",
    "accelerator_implementation_authority_root_sha256",
    "partial_summary_acceleration_envelope_transformation",
}
REQUEST_SCOPE_KEYS = frozenset(
    {"start_day", "completed_through_day", "day_count", "arm_id"}
)
DIRECT_SURFACE_KEYS = frozenset({"role", "name", "bytes", "rows", "sha256"})
ARCHIVED_SURFACE_KEYS = frozenset(
    {
        *DIRECT_SURFACE_KEYS,
        "storage",
        "archive_campaign_manifest_path",
        "archive_campaign_manifest_root_sha256",
        "hot_tombstone",
    }
)
PARTIAL_REQUEST_KEYS = frozenset(
    {"name", "snapshot_path", "bytes", "rows", "sha256"}
)
PARTIAL_TOP_LEVEL_RUNTIME_ENVELOPE_KEYS = frozenset(
    {"generated_at_utc"}
)
CATEGORY_TERMS = {
    "candidate_identity_union": ("candidate",),
    "ordering_decisions_scorecards": (
        "order",
        "selected",
        "decision",
        "rank",
        "scorecard",
    ),
    "misses": ("missed",),
    "lifecycle_replacement": (
        "lifecycle",
        "replacement",
        "pending",
        "open",
        "closed",
        "queue",
    ),
    "account_broker_terminal": (
        "account",
        "broker",
        "terminal",
        "balance",
        "equity",
    ),
    "costs_reservations": (
        "cost",
        "reservation",
        "commission",
        "spread",
        "swap",
        "slippage",
    ),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def root(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def self_root(value: Mapping[str, Any], field: str) -> str:
    projection = dict(value)
    projection.pop(field, None)
    return root(projection)


def partial_golden_self_root(
    value: Mapping[str, Any],
    field: str,
) -> str:
    projection = dict(value)
    projection.pop(field, None)
    payload = (
        json.dumps(
            projection,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    return hashlib.sha256(payload).hexdigest()


def golden_manifest_self_root(value: Mapping[str, Any]) -> str:
    return partial_golden_self_root(value, "manifest_self_root_sha256")


def _lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _path_has_symlink_component(path: Path) -> bool:
    lexical = _lexical_path(path)
    current = Path(lexical.anchor)
    for component in lexical.parts[1:]:
        current /= component
        if current.is_symlink():
            return True
    return False


def _open_regular_nofollow(path: Path, *, code: str) -> int:
    lexical = _lexical_path(path)
    if _path_has_symlink_component(lexical):
        raise ValueError(code)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    parent_descriptor = -1
    try:
        parent_descriptor = os.open(lexical.anchor, directory_flags)
        for component in lexical.parts[1:-1]:
            next_descriptor = os.open(
                component,
                directory_flags | nofollow,
                dir_fd=parent_descriptor,
            )
            os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        descriptor = os.open(
            lexical.name,
            os.O_RDONLY | nofollow,
            dir_fd=parent_descriptor,
        )
    except OSError:
        raise ValueError(code) from None
    finally:
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        raise ValueError(code)
    return descriptor


class BoundRegularFile:
    def __init__(self, path: Path, *, code: str) -> None:
        self.path = _lexical_path(path)
        self.code = str(code)
        self.descriptor = _open_regular_nofollow(self.path, code=self.code)
        self._opened = os.fstat(self.descriptor)

    @property
    def identity(self) -> tuple[int, int]:
        return self._opened.st_dev, self._opened.st_ino

    def _assert_descriptor_unchanged(self) -> None:
        observed = os.fstat(self.descriptor)
        if (
            observed.st_dev != self._opened.st_dev
            or observed.st_ino != self._opened.st_ino
            or observed.st_size != self._opened.st_size
            or observed.st_mtime_ns != self._opened.st_mtime_ns
        ):
            raise ValueError("parity_evidence_changed_during_read")

    def assert_path_unchanged(self) -> None:
        if _path_has_symlink_component(self.path):
            raise ValueError("parity_evidence_path_changed")
        try:
            descriptor = _open_regular_nofollow(
                self.path,
                code="parity_evidence_path_changed",
            )
        except ValueError:
            raise ValueError("parity_evidence_path_changed") from None
        try:
            observed = os.fstat(descriptor)
            if (observed.st_dev, observed.st_ino) != self.identity:
                raise ValueError("parity_evidence_path_changed")
        finally:
            os.close(descriptor)
        self._assert_descriptor_unchanged()

    def chunks(self) -> Iterator[bytes]:
        offset = 0
        while True:
            chunk = os.pread(self.descriptor, 1024 * 1024, offset)
            if not chunk:
                break
            offset += len(chunk)
            yield chunk
        self._assert_descriptor_unchanged()

    def read_bytes(self) -> bytes:
        return b"".join(self.chunks())

    def lines(self) -> Iterator[bytes]:
        pending = b""
        for chunk in self.chunks():
            pending += chunk
            while True:
                boundary = pending.find(b"\n")
                if boundary < 0:
                    break
                yield pending[: boundary + 1]
                pending = pending[boundary + 1 :]
        if pending:
            yield pending
        self._assert_descriptor_unchanged()

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1


class BoundEvidence:
    def __init__(self) -> None:
        self._files: dict[Path, BoundRegularFile] = {}

    def __enter__(self) -> "BoundEvidence":
        return self

    def __exit__(self, *_unused: object) -> None:
        for bound in reversed(tuple(self._files.values())):
            bound.close()

    def bind(
        self,
        path: Path,
        *,
        code: str,
        namespace: Path | None = None,
    ) -> BoundRegularFile:
        lexical = _lexical_path(path)
        if namespace is not None:
            try:
                lexical.relative_to(_lexical_path(namespace))
            except ValueError:
                raise ValueError(code) from None
        bound = self._files.get(lexical)
        if bound is None:
            bound = BoundRegularFile(lexical, code=code)
            self._files[lexical] = bound
        return bound

    def assert_paths_unchanged(self) -> None:
        for bound in self._files.values():
            bound.assert_path_unchanged()


def _temporary_bound(
    path: Path | BoundRegularFile,
    *,
    code: str,
) -> tuple[BoundRegularFile, bool]:
    if isinstance(path, BoundRegularFile):
        return path, False
    return BoundRegularFile(Path(path), code=code), True


def file_sha256(path: Path | BoundRegularFile) -> str:
    bound, temporary = _temporary_bound(
        path,
        code="parity_evidence_file_invalid",
    )
    try:
        digest = hashlib.sha256()
        for chunk in bound.chunks():
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        if temporary:
            bound.close()


def load_canonical(path: Path | BoundRegularFile) -> dict[str, Any]:
    bound, temporary = _temporary_bound(
        path,
        code="noncanonical_json_artifact",
    )
    try:
        raw = bound.read_bytes()
    finally:
        if temporary:
            bound.close()
    value = json.loads(raw)
    if type(value) is not dict or raw != canonical_bytes(value) + b"\n":
        raise ValueError("noncanonical_json_artifact")
    return value


def load_json_mapping(
    path: Path | BoundRegularFile,
    *,
    code: str,
) -> dict[str, Any]:
    bound, temporary = _temporary_bound(path, code=code)
    try:
        raw = bound.read_bytes()
    finally:
        if temporary:
            bound.close()
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError(code) from None
    if type(value) is not dict:
        raise ValueError(code)
    return value


def is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "009abcdef" for character in text
    )


def _bound_regular_file_inside(
    path: Path,
    namespace: Path,
    *,
    evidence: BoundEvidence,
    code: str,
) -> BoundRegularFile:
    lexical = _lexical_path(path)
    if _path_has_symlink_component(lexical):
        raise ValueError(code)
    return evidence.bind(lexical, code=code, namespace=namespace)


def stream_contract(path: Path | BoundRegularFile) -> dict[str, Any]:
    bound, temporary = _temporary_bound(
        path,
        code="persisted_ledger_file_invalid",
    )
    digest = hashlib.sha256()
    rows = 0
    final = b""
    size = 0
    try:
        for chunk in bound.chunks():
            digest.update(chunk)
            rows += chunk.count(b"\n")
            size += len(chunk)
            final = chunk[-1:]
    finally:
        if temporary:
            bound.close()
    if size and final != b"\n":
        raise ValueError("persisted_ledger_framing_mismatch")
    return {"bytes": size, "rows": rows, "sha256": digest.hexdigest()}


class CandidateUnionAccumulator:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self._present = 0
        self._missing = 0
        self._row_counts: dict[int, int] = {}

    def add(self, source_index: int, raw: bytes) -> None:
        row_index = self._row_counts.get(source_index, 0)
        try:
            row = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError):
            raise ValueError("persisted_ledger_json_invalid") from None
        if type(row) is not dict:
            raise ValueError("persisted_ledger_row_not_mapping")
        key = str(
            row.get("canonical_replay_candidate_instance_key") or ""
        ).strip()
        if key:
            self._present += 1
        else:
            self._missing += 1
        self._digest.update(
            canonical_bytes(
                {
                    "source_index": source_index,
                    "row_index": row_index,
                    "profile": str(row.get("profile") or ""),
                    "canonical_replay_candidate_instance_key": key,
                }
            )
        )
        self._digest.update(b"\n")
        self._row_counts[source_index] = row_index + 1

    def result(self) -> tuple[str, int, int]:
        return self._digest.hexdigest(), self._present, self._missing


def candidate_union_root_from_lines(
    sources: Iterable[Iterable[bytes]],
) -> tuple[str, int, int]:
    accumulator = CandidateUnionAccumulator()
    for source_index, lines in enumerate(sources):
        for raw in lines:
            accumulator.add(source_index, raw)
    return accumulator.result()


def path_lines(path: Path | BoundRegularFile):
    bound, temporary = _temporary_bound(
        path,
        code="persisted_ledger_file_invalid",
    )
    try:
        yield from bound.lines()
    finally:
        if temporary:
            bound.close()


def category_projection(
    value: Any,
    *,
    terms: tuple[str, ...],
    path: tuple[str, ...] = (),
) -> list[list[Any]]:
    matches: list[list[Any]] = []
    if isinstance(value, Mapping):
        for key in sorted(value, key=str):
            key_text = str(key)
            child_path = (*path, key_text)
            child = value[key]
            if any(term in key_text.lower() for term in terms):
                matches.append([list(child_path), child])
            matches.extend(category_projection(child, terms=terms, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            matches.extend(
                category_projection(
                    child,
                    terms=terms,
                    path=(*path, str(index)),
                )
            )
    return matches


def partial_semantic_contract(
    value: Mapping[str, Any],
    *,
    runtime_envelope_keys: frozenset[str] = (
        PARTIAL_TOP_LEVEL_RUNTIME_ENVELOPE_KEYS
    ),
) -> dict[str, Any]:
    core = {
        str(field): item
        for field, item in value.items()
        if str(field) not in runtime_envelope_keys
    }
    categories = {}
    for name, terms in CATEGORY_TERMS.items():
        projection = category_projection(core, terms=terms)
        categories[name] = {
            "match_count": len(projection),
            "root_sha256": root(projection),
        }
    return {
        "core_root_sha256": root(core),
        "categories": categories,
    }


def _archive_stable_summary_projection(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        str(field): item
        for field, item in value.items()
        if str(field) not in ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS
    }


def _is_absolute_lexical_path(value: Any) -> bool:
    if type(value) is not str or not value:
        return False
    path = Path(value)
    return path.is_absolute() and str(Path(os.path.abspath(value))) == value


def _is_nonnegative_number(value: Any) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _validate_bound_source_rebind(
    value: Any,
    *,
    source_plan_digest_sha256: str,
    source_bundle_root_sha256: str,
    selection_root_sha256: str,
) -> None:
    if type(value) is not dict or set(value) != SOURCE_REBIND_KEYS:
        raise ValueError("acceleration_envelope_source_rebind_invalid")
    core = dict(value)
    binding_root = core.pop("binding_root_sha256", None)
    authority = value.get("authority")
    bundle = value.get("verified_successor_bundle")
    selection = value.get("verified_successor_selection")
    if (
        value.get("schema")
        != (
            "gtos.replay_acceleration."
            "bound_source_bundle_consumer_rebind_authority.v1"
        )
        or binding_root != root(core)
        or not is_sha256(value.get("authority_root_sha256"))
        or not is_sha256(value.get("authority_file_sha256"))
        or not _is_absolute_lexical_path(value.get("authority_path"))
        or value.get("source_plan_digest_sha256")
        != source_plan_digest_sha256
        or value.get("policy_execution_entered") is not False
        or value.get("continuation_authorized") is not False
        or value.get("broker_live_authority") is not False
        or value.get("economic_values_exposed") is not False
        or type(authority) is not dict
        or authority.get("authority_root_sha256")
        != value.get("authority_root_sha256")
        or authority.get("policy_execution_entered") is not False
        or authority.get("continuation_authorized") is not False
        or authority.get("broker_live_authority") is not False
        or authority.get("economic_values_exposed") is not False
        or type(bundle) is not dict
        or set(bundle)
        != {
            "path",
            "file_sha256",
            "bundle_root_sha256",
            "implementation_root_sha256",
        }
        or not _is_absolute_lexical_path(bundle.get("path"))
        or not is_sha256(bundle.get("file_sha256"))
        or not is_sha256(bundle.get("implementation_root_sha256"))
        or bundle.get("bundle_root_sha256")
        != source_bundle_root_sha256
        or type(selection) is not dict
        or set(selection)
        != {"path", "file_sha256", "selection_root_sha256"}
        or not _is_absolute_lexical_path(selection.get("path"))
        or not is_sha256(selection.get("file_sha256"))
        or selection.get("selection_root_sha256") != selection_root_sha256
    ):
        raise ValueError("acceleration_envelope_source_rebind_invalid")


def _validate_runtime_evidence_contract(value: Any) -> None:
    if type(value) is not dict or set(value) != RUNTIME_EVIDENCE_CONTRACT_KEYS:
        raise ValueError("acceleration_envelope_runtime_evidence_invalid")
    core = dict(value)
    contract_root = core.pop("contract_root_sha256", None)
    inputs = value.get("inputs")
    data_roots = value.get("data_roots")
    if (
        value.get("schema")
        != "gtos.replay_acceleration.runtime_evidence_root.v1"
        or contract_root != root(core)
        or not _is_absolute_lexical_path(value.get("root"))
        or value.get("integration_repo_root") != value.get("root")
        or type(data_roots) is not list
        or not data_roots
        or len(set(data_roots)) != len(data_roots)
        or any(not _is_absolute_lexical_path(path) for path in data_roots)
        or type(inputs) is not dict
        or set(inputs) != RUNTIME_EVIDENCE_INPUT_NAMES
        or value.get("legacy_evidence_mutation_enabled") is not False
        or value.get("read_only_existing_evidence") is not True
    ):
        raise ValueError("acceleration_envelope_runtime_evidence_invalid")
    for name in sorted(RUNTIME_EVIDENCE_INPUT_NAMES):
        record = inputs[name]
        required = name in RUNTIME_EVIDENCE_REQUIRED_INPUT_NAMES
        expected_keys = (
            {
                "path",
                "present",
                "required_by_actual_replay_path",
                "bytes",
                "sha256",
            }
            if required
            else {"path", "present", "required_by_actual_replay_path"}
        )
        if (
            type(record) is not dict
            or set(record) != expected_keys
            or not _is_absolute_lexical_path(record.get("path"))
            or record.get("present") is not required
            or record.get("required_by_actual_replay_path") is not required
            or (
                required
                and (
                    type(record.get("bytes")) is not int
                    or record.get("bytes", 0) <= 0
                    or not is_sha256(record.get("sha256"))
                )
            )
        ):
            raise ValueError(
                "acceleration_envelope_runtime_evidence_invalid"
            )


def _validate_source_acceleration_authority(
    value: Any,
    *,
    shared_execution_contract: Any,
    source_plan_digest_sha256: str,
) -> dict[str, Any]:
    execution_options = (
        shared_execution_contract.get("execution_options")
        if type(shared_execution_contract) is dict
        else None
    )
    shared = (
        execution_options.get("source_acceleration")
        if type(execution_options) is dict
        else None
    )
    if (
        type(shared) is not dict
        or set(shared) != SHARED_SOURCE_ACCELERATION_KEYS
        or type(value) is not dict
        or set(value) != SOURCE_ACCELERATION_AUTHORITY_KEYS
    ):
        raise ValueError("acceleration_envelope_source_authority_invalid")
    stable_keys = SHARED_SOURCE_ACCELERATION_KEYS - {"prewarm_worker_count"}
    if any(value.get(key) != shared.get(key) for key in stable_keys):
        raise ValueError("acceleration_envelope_source_authority_invalid")
    rebind = shared.get("source_bundle_consumer_rebind_authority")
    if (
        shared.get("schema")
        != "gtos.replay_acceleration.real_source_authority.v1"
        or shared.get("source_plan_digest_sha256")
        != source_plan_digest_sha256
        or any(
            not is_sha256(shared.get(key))
            for key in (
                "source_bundle_root_sha256",
                "selection_root_sha256",
                "source_plan_digest_sha256",
                "config_projection_root_sha256",
                "normalizer_code_root_sha256",
            )
        )
        or type(shared.get("partition_count")) is not int
        or shared.get("partition_count", 0) <= 0
        or type(shared.get("symbol_count")) is not int
        or shared.get("symbol_count", 0) <= 0
        or type(shared.get("prewarm_worker_count")) is not int
        or shared.get("prewarm_worker_count", 0) <= 0
        or shared.get("policy_execution_entered") is not False
        or shared.get("candidate_cache_enabled") is not False
        or shared.get("policy_state_cache_enabled") is not False
    ):
        raise ValueError("acceleration_envelope_source_authority_invalid")
    _validate_bound_source_rebind(
        rebind,
        source_plan_digest_sha256=source_plan_digest_sha256,
        source_bundle_root_sha256=str(shared["source_bundle_root_sha256"]),
        selection_root_sha256=str(shared["selection_root_sha256"]),
    )
    barrier = value.get("cross_symbol_prewarm_barrier")
    metrics = value.get("typed_cache_metrics")
    if (
        type(barrier) is not dict
        or set(barrier) != SOURCE_PREWARM_BARRIER_KEYS
        or barrier.get("requested") is not True
        or barrier.get("barrier_complete") is not True
        or barrier.get("worker_count") != shared.get("prewarm_worker_count")
        or barrier.get("partition_count") != shared.get("partition_count")
        or not is_sha256(barrier.get("partition_set_root_sha256"))
        or not _is_nonnegative_number(barrier.get("seconds"))
        or not _is_nonnegative_number(value.get("bundle_validation_seconds"))
        or type(metrics) is not dict
        or set(metrics) != SOURCE_TYPED_CACHE_METRIC_KEYS
    ):
        raise ValueError("acceleration_envelope_source_authority_invalid")
    for key in (
        "bytes_read",
        "bytes_written",
        "cold_partition_count",
        "normalized_row_count",
        "warm_partition_count",
    ):
        if type(metrics.get(key)) is not int or metrics.get(key, -1) < 0:
            raise ValueError(
                "acceleration_envelope_source_authority_invalid"
            )
    for key in (
        "hashing_seconds",
        "normalization_seconds",
        "serialization_seconds",
        "verification_seconds",
    ):
        if not _is_nonnegative_number(metrics.get(key)):
            raise ValueError(
                "acceleration_envelope_source_authority_invalid"
            )
    return shared


def _validate_tick_export_manifest_bytes(
    raw: bytes,
    *,
    expected_sha256: str,
    required_window_start_utc: str | None = None,
    required_window_end_utc: str | None = None,
    require_no_errors: bool = False,
) -> None:
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("acceleration_envelope_tick_manifest_invalid")
    try:
        manifest = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError(
            "acceleration_envelope_tick_manifest_invalid"
        ) from None
    windows = manifest.get("windows") if type(manifest) is dict else None
    symbols = manifest.get("symbols") if type(manifest) is dict else None
    if (
        type(manifest) is not dict
        or set(manifest) != TICK_EXPORT_MANIFEST_KEYS
        or manifest.get("schema_version") != "mt5_research_tick_export_v1"
        or manifest.get("read_only") is not True
        or type(manifest.get("errors")) is not list
        or (require_no_errors and manifest.get("errors") != [])
        or any(
            type(row) is not dict
            or set(row) != {"error", "file_symbol", "mt5_symbol", "window"}
            or any(not str(row.get(key) or "") for key in row)
            for row in manifest.get("errors", [])
        )
        or type(manifest.get("account")) is not dict
        or type(manifest.get("terminal")) is not dict
        or type(manifest.get("source_provenance")) is not dict
        or type(manifest.get("files")) is not dict
        or not manifest.get("files")
        or not _is_nonnegative_number(manifest.get("chunk_minutes"))
        or float(manifest.get("chunk_minutes", 0.0)) <= 0.0
        or any(
            type(manifest.get(key)) is not str or not manifest.get(key)
            for key in (
                "created_at_utc",
                "label",
                "manifest_path",
                "mt5_client_kind",
                "output_dir",
            )
        )
        or type(symbols) is not list
        or not symbols
        or any(
            type(row) is not dict
            or set(row) != {"file_symbol", "mt5_symbol"}
            or not str(row.get("file_symbol") or "")
            or not str(row.get("mt5_symbol") or "")
            for row in symbols
        )
        or type(windows) is not list
        or not windows
        or any(
            type(row) is not dict
            or set(row) != {"start", "end", "label"}
            or type(row.get("start")) is not str
            or type(row.get("end")) is not str
            or type(row.get("label")) is not str
            or not row.get("label")
            or row.get("start", "") >= row.get("end", "")
            for row in windows
        )
    ):
        raise ValueError("acceleration_envelope_tick_manifest_invalid")
    if (
        required_window_start_utc is not None
        and required_window_end_utc is not None
        and not any(
            row["start"] <= required_window_start_utc
            and row["end"] >= required_window_end_utc
            for row in windows
        )
    ):
        raise ValueError("acceleration_envelope_tick_manifest_invalid")


def _validate_attempt5_execution_identity(
    identity: Any,
    *,
    partial: Mapping[str, Any],
    partial_path: Path,
    shared_source_authority: Mapping[str, Any],
    expected_output_prefix: str,
    expected_shared_execution_contract_sha256: str,
    expected_source_plan_digest_sha256: str,
    expected_arm_fingerprint_sha256: str,
    expected_prospective_golden_authority: Mapping[str, Any],
    evidence: BoundEvidence,
) -> None:
    if type(identity) is not dict or set(identity) != ATTEMPT5_EXECUTION_IDENTITY_KEYS:
        raise ValueError("acceleration_envelope_identity_invalid")
    identity_core = dict(identity)
    identity_root = identity_core.pop("identity_root_sha256", None)
    if identity_root != root(identity_core):
        raise ValueError("acceleration_envelope_identity_invalid")
    runner_path = identity.get("runner_path")
    shared_contract = partial.get("shared_execution_contract")
    code_authority = (
        shared_contract.get("code_authority")
        if type(shared_contract) is dict
        else None
    )
    canonical_runner_path = _lexical_path(
        Path(__file__).with_name(
            "replay_acceleration_attempt5_typed_sparse_runner.py"
        )
    )
    runner_sha256 = identity.get("runner_sha256")
    runner_rows = [
        row
        for row in (code_authority if type(code_authority) is list else ())
        if type(row) is dict
        and set(row) == {"path", "sha256"}
        and row.get("path") == ATTEMPT5_RUNNER_RELATIVE_PATH
        and row.get("sha256") == runner_sha256
    ]
    if (
        runner_path != str(canonical_runner_path)
        or not is_sha256(runner_sha256)
        or len(runner_rows) != 1
        or hashlib.sha256(
            evidence.bind(
                canonical_runner_path,
                code="acceleration_envelope_runner_invalid",
            ).read_bytes()
        ).hexdigest()
        != runner_sha256
    ):
        raise ValueError("acceleration_envelope_runner_invalid")
    tick_cache = identity.get("tick_sparse_cache")
    diagnostics = identity.get("tick_diagnostic_manifest_bindings")
    rebind = identity.get("source_bundle_consumer_rebind_authority")
    if (
        identity.get("schema")
        != "gtos.replay_acceleration.attempt5_typed_sparse_identity.v1"
        or identity.get("status")
        != "ATTEMPT5_TYPED_SPARSE_S0R0_JAN1_7_BOUND"
        or identity.get("arm_id") != "S0R0"
        or identity.get("start_day") != "2026-01-01"
        or identity.get("parity_day") != "2026-01-07"
        or identity.get("contract_end_day") != "2026-01-31"
        or identity.get("output_namespace") != str(partial_path.parent)
        or identity.get("output_prefix") != expected_output_prefix
        or partial.get("output_prefix") != expected_output_prefix
        or partial.get("route_id") != partial_path.parent.name
        or identity.get("prospective_golden_authority")
        != expected_prospective_golden_authority
        or identity.get("expected_shared_execution_contract_sha256")
        != expected_shared_execution_contract_sha256
        or identity.get("expected_source_plan_digest_sha256")
        != expected_source_plan_digest_sha256
        or identity.get("expected_arm_fingerprint_sha256")
        != expected_arm_fingerprint_sha256
        or identity.get("expected_source_bundle_root_sha256")
        != shared_source_authority.get("source_bundle_root_sha256")
        or not is_sha256(identity.get("expected_tick_source_manifest_sha256"))
        or identity.get("source_prewarm_workers")
        != shared_source_authority.get("prewarm_worker_count")
        or rebind
        != shared_source_authority.get(
            "source_bundle_consumer_rebind_authority"
        )
        or not _is_absolute_lexical_path(identity.get("tick_source_manifest"))
        or type(diagnostics) is not list
        or not diagnostics
        or len(
            {
                row.get("path")
                for row in diagnostics
                if type(row) is dict
            }
        )
        != len(diagnostics)
        or any(
            type(row) is not dict
            or set(row) != {"path", "sha256"}
            or not _is_absolute_lexical_path(row.get("path"))
            or not is_sha256(row.get("sha256"))
            for row in diagnostics
        )
        or type(tick_cache) is not dict
        or set(tick_cache)
        != {
            "schema",
            "root",
            "window_start_utc",
            "window_end_utc",
            "source_plan_or_replay_semantics_changed",
        }
        or tick_cache.get("schema")
        != "gtos.replay_acceleration.sparse_tick_window_cache.v1"
        or not _is_absolute_lexical_path(tick_cache.get("root"))
        or tick_cache.get("window_start_utc")
        != "2025-12-31T00:00:00+00:00"
        or tick_cache.get("window_end_utc")
        != "2026-01-09T00:00:00+00:00"
        or tick_cache.get("source_plan_or_replay_semantics_changed") is not False
        or identity.get("policy_execution_entered") is not False
        or identity.get("legacy_replay_route_invoked") is not False
        or identity.get("other_arms_launched") is not False
        or identity.get("broker_live_authority") is not False
        or identity.get("broker_mutation_enabled") is not False
        or identity.get("economic_values_exposed") is not False
    ):
        raise ValueError("acceleration_envelope_identity_invalid")
    tick_manifest_path = _lexical_path(
        Path(str(identity["tick_source_manifest"]))
    )
    _validate_tick_export_manifest_bytes(
        evidence.bind(
            tick_manifest_path,
            code="acceleration_envelope_tick_manifest_invalid",
        ).read_bytes(),
        expected_sha256=str(identity["expected_tick_source_manifest_sha256"]),
        required_window_start_utc=str(tick_cache["window_start_utc"]),
        required_window_end_utc=str(tick_cache["window_end_utc"]),
        require_no_errors=True,
    )
    for row in diagnostics:
        _validate_tick_export_manifest_bytes(
            evidence.bind(
                _lexical_path(Path(str(row["path"]))),
                code="acceleration_envelope_tick_manifest_invalid",
            ).read_bytes(),
            expected_sha256=str(row["sha256"]),
        )


def _acceleration_stable_summary_projection(
    value: Mapping[str, Any],
    *,
    partial_path: Path,
    expected_output_prefix: str | None,
    expected_prospective_golden_authority: Mapping[str, Any] | None,
    expected_shared_execution_contract_sha256: str | None,
    expected_source_plan_digest_sha256: str | None,
    expected_arm_fingerprint_sha256: str | None,
    archived_result_surface_roles: frozenset[str],
    evidence: BoundEvidence,
) -> tuple[dict[str, Any], dict[str, Any]]:
    projection = copy.deepcopy(dict(value))
    runtime_fields: dict[str, Any] = {}

    is_accelerated = expected_shared_execution_contract_sha256 is not None
    identity = projection.get("attempt5_execution_identity")
    if not is_accelerated:
        if (
            identity is not None
            or projection.get("runtime_evidence_contract") is not None
            or projection.get("source_acceleration_authority") is not None
        ):
            raise ValueError("acceleration_envelope_golden_authority_invalid")
    else:
        if (
            expected_output_prefix is None
            or expected_prospective_golden_authority is None
            or expected_source_plan_digest_sha256 is None
            or expected_arm_fingerprint_sha256 is None
            or "real_s0r0_parity_gate" not in projection
            or projection["real_s0r0_parity_gate"] is not None
        ):
            raise ValueError("acceleration_envelope_prior_parity_gate_invalid")
        _validate_runtime_evidence_contract(
            projection.get("runtime_evidence_contract")
        )
        shared_source_authority = _validate_source_acceleration_authority(
            projection.get("source_acceleration_authority"),
            shared_execution_contract=projection.get(
                "shared_execution_contract"
            ),
            source_plan_digest_sha256=expected_source_plan_digest_sha256,
        )
        _validate_attempt5_execution_identity(
            identity,
            partial=projection,
            partial_path=partial_path,
            shared_source_authority=shared_source_authority,
            expected_output_prefix=expected_output_prefix,
            expected_shared_execution_contract_sha256=(
                expected_shared_execution_contract_sha256
            ),
            expected_source_plan_digest_sha256=(
                expected_source_plan_digest_sha256
            ),
            expected_arm_fingerprint_sha256=expected_arm_fingerprint_sha256,
            expected_prospective_golden_authority=(
                expected_prospective_golden_authority
            ),
            evidence=evidence,
        )

    capacity = projection.get("capacity_safe_chunk_execution_contract")
    if capacity is not None:
        if type(capacity) is not dict or type(capacity.get("checkpoints")) is not list:
            raise ValueError("acceleration_envelope_gc_counter_invalid")
        gc_counters: list[dict[str, int]] = []
        for index, checkpoint in enumerate(capacity["checkpoints"]):
            if type(checkpoint) is not dict:
                raise ValueError("acceleration_envelope_gc_counter_invalid")
            if "gc_collected_objects" not in checkpoint:
                continue
            observed = checkpoint["gc_collected_objects"]
            if type(observed) is not int or observed < 0:
                raise ValueError("acceleration_envelope_gc_counter_invalid")
            gc_counters.append({"checkpoint_index": index, "value": observed})
            checkpoint["gc_collected_objects"] = 0
        runtime_fields[
            ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES[0]
        ] = gc_counters

    ledger_bytes = projection.get(
        "ledger_file_bytes_flushed_before_partial_summary"
    )
    if ledger_bytes is not None:
        if type(ledger_bytes) is not dict:
            raise ValueError("acceleration_envelope_archive_bytes_invalid")
        for index, role in enumerate(("decision", "scorecard", "missed"), 1):
            if role not in ledger_bytes or role not in archived_result_surface_roles:
                continue
            observed = ledger_bytes[role]
            if type(observed) is not int or observed < 0:
                raise ValueError("acceleration_envelope_archive_bytes_invalid")
            runtime_fields[
                ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES[index]
            ] = observed
            ledger_bytes[role] = 0

    ignored = {
        *ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS,
        *ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS,
    }
    return (
        {
            str(field): item
            for field, item in projection.items()
            if str(field) not in ignored
        },
        runtime_fields,
    )


def _binding_without_implementation_digest(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("acceleration_envelope_binding_invalid")
    projection = dict(value)
    projection.pop("actual_shared_execution_contract_digest_sha256", None)
    projection.pop("expected_shared_execution_contract_digest_sha256", None)
    return projection


def _verify_fixed_verifier_code_authority(
    authority: Any,
    *,
    evidence: BoundEvidence,
) -> str:
    if type(authority) is not dict:
        raise ValueError("fixed_verifier_code_authority_invalid")
    files = authority.get("files")
    core = {"schema": authority.get("schema"), "files": files}
    if (
        authority.get("schema") != FIXED_VERIFIER_CODE_AUTHORITY_SCHEMA
        or type(files) is not list
        or len(files) != len(FIXED_VERIFIER_MODULE_FILES)
        or authority.get("authority_root_sha256") != root(core)
    ):
        raise ValueError("fixed_verifier_code_authority_invalid")
    for row, (module, filename) in zip(
        files,
        FIXED_VERIFIER_MODULE_FILES,
        strict=True,
    ):
        expected_path = _lexical_path(Path(__file__).parent / filename)
        if (
            type(row) is not dict
            or set(row) != {"module", "path", "bytes", "sha256"}
            or row.get("module") != module
            or row.get("path") != str(expected_path)
            or type(row.get("bytes")) is not int
            or row.get("bytes", -1) < 0
            or not is_sha256(row.get("sha256"))
        ):
            raise ValueError("fixed_verifier_code_authority_invalid")
        bound = evidence.bind(
            expected_path,
            code="fixed_verifier_code_authority_invalid",
        )
        raw = bound.read_bytes()
        if (
            len(raw) != row["bytes"]
            or hashlib.sha256(raw).hexdigest() != row["sha256"]
        ):
            raise ValueError("fixed_verifier_code_authority_mismatch")
    return str(authority["authority_root_sha256"])


def _verify_partial_summary_acceleration_envelope(
    *,
    transformation: Any,
    golden_partial_path: BoundRegularFile,
    accelerated_partial_path: BoundRegularFile,
    golden_partial: Mapping[str, Any],
    accelerated_partial: Mapping[str, Any],
    request: Mapping[str, Any],
    evidence: BoundEvidence,
) -> tuple[
    str,
    frozenset[str],
    dict[str, Any],
    dict[str, Any],
]:
    if type(transformation) is not dict or set(transformation) != (
        ACCELERATION_ENVELOPE_KEYS
    ):
        raise ValueError("acceleration_envelope_transformation_invalid")
    golden_contract = transformation.get("golden_partial_summary")
    accelerated_contract = transformation.get("accelerated_partial_summary")
    if (
        transformation.get("schema")
        != ACCELERATION_ENVELOPE_TRANSFORMATION_SCHEMA
        or transformation.get("allowed_top_level_changes")
        != list(ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS)
        or transformation.get("allowed_nested_changes")
        != list(ACCELERATION_ENVELOPE_ALLOWED_NESTED_CHANGES)
        or type(golden_contract) is not dict
        or set(golden_contract) != {"path", "bytes", "sha256"}
        or type(accelerated_contract) is not dict
        or set(accelerated_contract) != {"path", "bytes", "sha256"}
        or transformation.get("economic_values_exposed") is not False
        or transformation.get("transformation_root_sha256")
        != self_root(transformation, "transformation_root_sha256")
    ):
        raise ValueError("acceleration_envelope_transformation_invalid")
    golden_stream = stream_contract(golden_partial_path)
    accelerated_stream = stream_contract(accelerated_partial_path)
    if (
        golden_contract
        != {
            "path": str(golden_partial_path.path),
            "bytes": golden_stream["bytes"],
            "sha256": golden_stream["sha256"],
        }
        or accelerated_contract
        != {
            "path": str(accelerated_partial_path.path),
            "bytes": accelerated_stream["bytes"],
            "sha256": accelerated_stream["sha256"],
        }
    ):
        raise ValueError("acceleration_envelope_identity_mismatch")
    try:
        golden_split = split_shared_execution_contract(
            golden_partial["shared_execution_contract"]
        )
        accelerated_split = split_shared_execution_contract(
            accelerated_partial["shared_execution_contract"]
        )
    except (KeyError, ContractSplitError):
        raise ValueError("acceleration_envelope_contract_invalid") from None
    economic_digest = request.get("economic_execution_contract_sha256")
    shared_digest = request.get("shared_execution_contract_sha256")
    implementation_root = request.get(
        "accelerator_implementation_authority_root_sha256"
    )
    archived_result_surface_roles = frozenset(
        str(row.get("role"))
        for row in (request.get("persisted_result_surfaces") or ())
        if type(row) is dict and row.get("storage") == "verified_zstd_campaign"
    )
    if (
        golden_split["economic_execution_contract_digest_sha256"]
        != economic_digest
        or accelerated_split["economic_execution_contract_digest_sha256"]
        != economic_digest
        or accelerated_partial["shared_execution_contract"].get(
            "shared_execution_contract_digest_sha256"
        )
        != shared_digest
        or accelerated_split[
            "accelerator_implementation_authority_root_sha256"
        ]
        != implementation_root
        or _binding_without_implementation_digest(
            golden_partial.get("b7_5_contract_binding")
        )
        != _binding_without_implementation_digest(
            accelerated_partial.get("b7_5_contract_binding")
        )
    ):
        raise ValueError("acceleration_envelope_contract_mismatch")
    golden_projection, golden_runtime_fields = (
        _acceleration_stable_summary_projection(
            golden_partial,
            partial_path=golden_partial_path.path,
            expected_output_prefix=None,
            expected_prospective_golden_authority=None,
            expected_shared_execution_contract_sha256=None,
            expected_source_plan_digest_sha256=None,
            expected_arm_fingerprint_sha256=None,
            archived_result_surface_roles=archived_result_surface_roles,
            evidence=evidence,
        )
    )
    accelerated_projection, accelerated_runtime_fields = (
        _acceleration_stable_summary_projection(
            accelerated_partial,
            partial_path=accelerated_partial_path.path,
            expected_output_prefix=str(request.get("output_prefix") or ""),
            expected_prospective_golden_authority=request.get(
                "prospective_golden_authority"
            ),
            expected_shared_execution_contract_sha256=str(shared_digest),
            expected_source_plan_digest_sha256=str(
                request.get("source_plan_digest_sha256")
            ),
            expected_arm_fingerprint_sha256=str(
                request.get("arm_fingerprint_sha256")
            ),
            archived_result_surface_roles=archived_result_surface_roles,
            evidence=evidence,
        )
    )
    stable_root = root(golden_projection)
    expected = {
        "stable_projection_root_sha256": stable_root,
        "golden_nested_runtime_fields_root_sha256": root(
            golden_runtime_fields
        ),
        "accelerated_nested_runtime_fields_root_sha256": root(
            accelerated_runtime_fields
        ),
        "legacy_shared_execution_contract_digest_sha256": golden_partial[
            "shared_execution_contract"
        ]["shared_execution_contract_digest_sha256"],
        "accelerated_shared_execution_contract_digest_sha256": shared_digest,
        "economic_execution_contract_digest_sha256": economic_digest,
        "accelerator_implementation_authority_root_sha256": implementation_root,
        "golden_envelope_root_sha256": root(
            {
                key: golden_partial.get(key)
                for key in ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
            }
        ),
        "accelerated_envelope_root_sha256": root(
            {
                key: accelerated_partial.get(key)
                for key in ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS
            }
        ),
    }
    if (
        stable_root
        != root(accelerated_projection)
        or any(transformation.get(key) != value for key, value in expected.items())
    ):
        raise ValueError("acceleration_envelope_semantic_mismatch")
    return (
        str(transformation["transformation_root_sha256"]),
        frozenset(
            {
                *PARTIAL_TOP_LEVEL_RUNTIME_ENVELOPE_KEYS,
                *ACCELERATION_ENVELOPE_ALLOWED_TOP_LEVEL_KEYS,
            }
        ),
        golden_projection,
        accelerated_projection,
    )


def _verify_partial_summary_archive_transformation(
    *,
    transformation: Mapping[str, Any] | None,
    verified_campaigns: Mapping[Path, Mapping[str, Any]],
    accelerated_partial_path: BoundRegularFile,
    accelerated_partial: Mapping[str, Any],
    request_partial: Mapping[str, Any],
    evidence: BoundEvidence,
) -> tuple[str, frozenset[str]]:
    if not verified_campaigns:
        if transformation is not None:
            raise ValueError(
                "partial_summary_archive_transformation_campaign_mismatch"
            )
        return root(None), PARTIAL_TOP_LEVEL_RUNTIME_ENVELOPE_KEYS
    if type(transformation) is not dict or len(verified_campaigns) != 1:
        raise ValueError(
            "partial_summary_archive_transformation_campaign_mismatch"
        )

    campaign_path_value = transformation.get("campaign_manifest_path")
    if type(campaign_path_value) is not str:
        raise ValueError(
            "partial_summary_archive_transformation_campaign_mismatch"
        )
    campaign_path = _lexical_path(Path(campaign_path_value))
    if (
        not Path(campaign_path_value).is_absolute()
        or str(campaign_path) != campaign_path_value
        or campaign_path not in verified_campaigns
    ):
        raise ValueError(
            "partial_summary_archive_transformation_campaign_mismatch"
        )
    campaign_report = verified_campaigns[campaign_path]
    terminal_summary = campaign_report.get(
        "terminal_pre_archive_partial_summary"
    )
    pre_contract = transformation.get("pre_archive_partial_summary")
    post_contract = transformation.get("post_archive_partial_summary")
    if (
        type(terminal_summary) is not dict
        or type(pre_contract) is not dict
        or type(post_contract) is not dict
        or transformation.get("campaign_manifest_root_sha256")
        != campaign_report.get("campaign_manifest_root_sha256")
        or transformation.get("terminal_checkpoint_chain_root_sha256")
        != campaign_report.get("terminal_checkpoint_chain_root_sha256")
        or transformation.get("terminal_checkpoint_chain_root_sha256")
        != terminal_summary.get("checkpoint_chain_root_sha256")
    ):
        raise ValueError(
            "partial_summary_archive_transformation_campaign_mismatch"
        )

    pre_path_value = pre_contract.get("path")
    post_path_value = post_contract.get("path")
    terminal_path_value = terminal_summary.get("snapshot_path")
    if (
        type(pre_path_value) is not str
        or type(post_path_value) is not str
        or type(terminal_path_value) is not str
    ):
        raise ValueError(
            "partial_summary_archive_transformation_identity_mismatch"
        )
    pre_path = _lexical_path(Path(pre_path_value))
    post_path = _lexical_path(Path(post_path_value))
    terminal_path = _lexical_path(Path(terminal_path_value))
    if (
        not Path(pre_path_value).is_absolute()
        or not Path(post_path_value).is_absolute()
        or str(pre_path) != pre_path_value
        or str(post_path) != post_path_value
        or pre_path != terminal_path
        or post_path != accelerated_partial_path.path
        or pre_contract.get("bytes") != terminal_summary.get("bytes")
        or pre_contract.get("sha256") != terminal_summary.get("sha256")
        or pre_contract.get("checkpoint_root_sha256")
        != terminal_summary.get("checkpoint_root_sha256")
        or post_contract.get("bytes") != request_partial.get("bytes")
        or post_contract.get("sha256") != request_partial.get("sha256")
    ):
        raise ValueError(
            "partial_summary_archive_transformation_identity_mismatch"
        )
    pre_archive_partial_path = evidence.bind(
        pre_path,
        code="partial_summary_archive_transformation_identity_mismatch",
    )
    if pre_archive_partial_path.identity == accelerated_partial_path.identity:
        raise ValueError(
            "partial_summary_archive_transformation_identity_mismatch"
        )
    pre_stream_contract = stream_contract(pre_archive_partial_path)
    post_stream_contract = stream_contract(accelerated_partial_path)
    if (
        {
            key: pre_stream_contract[key]
            for key in ("bytes", "sha256")
        }
        != {
            key: pre_contract[key]
            for key in ("bytes", "sha256")
        }
        or {
            key: post_stream_contract[key]
            for key in ("bytes", "sha256")
        }
        != {
            key: post_contract[key]
            for key in ("bytes", "sha256")
        }
    ):
        raise ValueError(
            "partial_summary_archive_transformation_identity_mismatch"
        )
    pre_archive_partial = load_json_mapping(
        pre_archive_partial_path,
        code="partial_summary_archive_transformation_identity_mismatch",
    )
    pre_projection_root = root(
        _archive_stable_summary_projection(pre_archive_partial)
    )
    post_projection_root = root(
        _archive_stable_summary_projection(accelerated_partial)
    )
    if (
        pre_projection_root != post_projection_root
        or pre_projection_root
        != transformation.get("stable_projection_root_sha256")
    ):
        raise ValueError(
            "partial_summary_archive_transformation_semantic_mismatch"
        )
    return (
        str(transformation["transformation_root_sha256"]),
        frozenset(
            {
                *PARTIAL_TOP_LEVEL_RUNTIME_ENVELOPE_KEYS,
                *ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS,
            }
        ),
    )


def verify_real_parity(
    *,
    golden_manifest_path: Path,
    accelerated_namespace: Path,
    gate_request: Mapping[str, Any],
    git_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    with BoundEvidence() as evidence:
        report, receipt = _verify_real_parity(
            golden_manifest_path=golden_manifest_path,
            accelerated_namespace=accelerated_namespace,
            gate_request=gate_request,
            git_root=git_root,
            evidence=evidence,
        )
        evidence.assert_paths_unchanged()
        return report, receipt


def _verify_real_parity(
    *,
    golden_manifest_path: Path,
    accelerated_namespace: Path,
    gate_request: Mapping[str, Any],
    git_root: Path | None,
    evidence: BoundEvidence,
) -> tuple[dict[str, Any], dict[str, Any]]:
    golden_manifest_input = _lexical_path(Path(golden_manifest_path))
    request = dict(gate_request)
    scope = request.get("scope")
    request_partial = request.get("partial_summary")
    request_surface_records = request.get("persisted_result_surfaces")
    archive_transformation = request.get(
        "partial_summary_archive_transformation"
    )
    acceleration_envelope_transformation = request.get(
        "partial_summary_acceleration_envelope_transformation"
    )
    prospective_authority = request.get("prospective_golden_authority")
    accelerated_namespace_input = _lexical_path(Path(accelerated_namespace))
    is_successor = request.get("schema") == REQUEST_SCHEMA_V2
    if (
        set(request) != (REQUEST_V2_KEYS if is_successor else REQUEST_KEYS)
        or request.get("schema")
        not in {REQUEST_SCHEMA, REQUEST_SCHEMA_V2}
        or request.get("gate_request_root_sha256")
        != self_root(request, "gate_request_root_sha256")
        or not isinstance(scope, Mapping)
        or set(scope) != REQUEST_SCOPE_KEYS
        or type(prospective_authority) is not dict
        or set(prospective_authority)
        != (
            PROSPECTIVE_GOLDEN_AUTHORITY_V2_KEYS
            if is_successor
            else PROSPECTIVE_GOLDEN_AUTHORITY_KEYS
        )
        or prospective_authority.get("fixed_verifier_module")
        != FIXED_VERIFIER_MODULE
        or type(request.get("accelerated_namespace_path")) is not str
        or not Path(str(request.get("accelerated_namespace_path"))).is_absolute()
        or not isinstance(request_partial, Mapping)
        or set(request_partial) != PARTIAL_REQUEST_KEYS
        or not isinstance(request_surface_records, list)
        or [str(item.get("role")) for item in request_surface_records]
        != list(ROLES)
        or request.get("policy_execution_entered") is not True
        or request.get("actual_run_campaign_path") is not True
        or request.get("synthetic_reducer_harness") is not False
        or request.get("candidate_cache_enabled") is not False
        or request.get("policy_state_cache_enabled") is not False
        or request.get("other_arms_launched") is not False
        or request.get("live_broker_authority") is not False
        or request.get("broker_mutation_enabled") is not False
        or request.get("economic_values_exposed") is not False
        or scope.get("start_day") != "2026-01-01"
        or scope.get("completed_through_day") != "2026-01-07"
        or type(scope.get("day_count")) is not int
        or scope.get("day_count") != 7
        or scope.get("arm_id") != "S0R0"
        or not is_sha256(request.get("source_plan_digest_sha256"))
        or not is_sha256(request.get("shared_execution_contract_sha256"))
        or not is_sha256(request.get("arm_fingerprint_sha256"))
        or (
            is_successor
            and (
                not is_sha256(
                    request.get("economic_execution_contract_sha256")
                )
                or not is_sha256(
                    request.get(
                        "accelerator_implementation_authority_root_sha256"
                    )
                )
                or type(acceleration_envelope_transformation) is not dict
            )
        )
    ):
        raise ValueError("real_gate_request_invalid")
    for item in request_surface_records:
        if not isinstance(item, Mapping):
            raise ValueError("real_gate_request_invalid")
        expected_keys = (
            ARCHIVED_SURFACE_KEYS
            if item.get("storage") == "verified_zstd_campaign"
            else DIRECT_SURFACE_KEYS
        )
        if (
            set(item) != expected_keys
            or type(item.get("bytes")) is not int
            or type(item.get("rows")) is not int
            or item.get("bytes", -1) < 0
            or item.get("rows", -1) < 0
            or not is_sha256(item.get("sha256"))
            or not str(item.get("name") or "")
        ):
            raise ValueError("real_gate_request_invalid")
        if item.get("storage") == "verified_zstd_campaign" and (
            not is_sha256(item.get("archive_campaign_manifest_root_sha256"))
            or not str(item.get("archive_campaign_manifest_path") or "")
            or type(item.get("hot_tombstone")) is not dict
            or set(item["hot_tombstone"]) != set(EMPTY_SURFACE_CONTRACT)
            or item["hot_tombstone"] != EMPTY_SURFACE_CONTRACT
        ):
            raise ValueError("real_gate_request_invalid")
    has_archived_surfaces = any(
        item.get("storage") == "verified_zstd_campaign"
        for item in request_surface_records
    )
    if has_archived_surfaces != (type(archive_transformation) is dict):
        raise ValueError("real_gate_request_invalid")
    if type(archive_transformation) is dict:
        pre_summary = archive_transformation.get(
            "pre_archive_partial_summary"
        )
        post_summary = archive_transformation.get(
            "post_archive_partial_summary"
        )
        if (
            set(archive_transformation) != ARCHIVE_TRANSFORMATION_KEYS
            or archive_transformation.get("schema")
            != ARCHIVE_TRANSFORMATION_SCHEMA
            or archive_transformation.get("allowed_top_level_changes")
            != list(ARCHIVE_TRANSFORMATION_ALLOWED_TOP_LEVEL_KEYS)
            or type(pre_summary) is not dict
            or set(pre_summary) != ARCHIVE_PRE_SUMMARY_KEYS
            or type(post_summary) is not dict
            or set(post_summary) != ARCHIVE_POST_SUMMARY_KEYS
            or any(
                type(summary.get("path")) is not str
                or not Path(str(summary["path"])).is_absolute()
                or type(summary.get("bytes")) is not int
                or summary.get("bytes", -1) < 0
                or not is_sha256(summary.get("sha256"))
                for summary in (pre_summary, post_summary)
            )
            or not is_sha256(pre_summary.get("checkpoint_root_sha256"))
            or not is_sha256(
                archive_transformation.get(
                    "campaign_manifest_root_sha256"
                )
            )
            or not is_sha256(
                archive_transformation.get(
                    "terminal_checkpoint_chain_root_sha256"
                )
            )
            or not is_sha256(
                archive_transformation.get("stable_projection_root_sha256")
            )
            or archive_transformation.get("transformation_root_sha256")
            != self_root(
                archive_transformation,
                "transformation_root_sha256",
            )
        ):
            raise ValueError("real_gate_request_invalid")
    if (
        type(request_partial.get("bytes")) is not int
        or type(request_partial.get("rows")) is not int
        or request_partial.get("bytes", -1) < 0
        or request_partial.get("rows", -1) < 0
        or not is_sha256(request_partial.get("sha256"))
        or not str(request_partial.get("name") or "")
        or not str(request_partial.get("snapshot_path") or "")
    ):
        raise ValueError("real_gate_request_invalid")

    authority_hash_fields = (
        "golden_manifest_file_sha256",
        "golden_manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "golden_amendment_file_sha256",
        "golden_amendment_self_root_sha256",
        "fixed_verifier_file_sha256",
    )
    authority_path_fields = (
        "golden_manifest_path",
        "golden_amendment_path",
        "fixed_verifier_path",
        *(("successor_authority_path",) if is_successor else ()),
    )
    if (
        any(
            not is_sha256(prospective_authority.get(field))
            for field in authority_hash_fields
        )
        or any(
            type(prospective_authority.get(field)) is not str
            or not Path(str(prospective_authority[field])).is_absolute()
            or str(
                _lexical_path(Path(str(prospective_authority[field])))
            )
            != str(prospective_authority[field])
            for field in authority_path_fields
        )
    ):
        raise ValueError("gate_request_golden_authority_mismatch")
    bound_manifest_path = _lexical_path(
        Path(str(prospective_authority["golden_manifest_path"]))
    )
    bound_amendment_path = _lexical_path(
        Path(str(prospective_authority["golden_amendment_path"]))
    )
    bound_verifier_path = _lexical_path(
        Path(str(prospective_authority["fixed_verifier_path"]))
    )
    request_namespace_path = _lexical_path(
        Path(str(request["accelerated_namespace_path"]))
    )
    if (
        _path_has_symlink_component(golden_manifest_input)
        or _path_has_symlink_component(bound_manifest_path)
        or _path_has_symlink_component(bound_amendment_path)
        or _path_has_symlink_component(bound_verifier_path)
        or golden_manifest_input != bound_manifest_path
        or accelerated_namespace_input != request_namespace_path
        or bound_verifier_path != _lexical_path(Path(__file__))
    ):
        raise ValueError("gate_request_golden_authority_mismatch")
    manifest_file = evidence.bind(
        bound_manifest_path,
        code="gate_request_golden_authority_mismatch",
    )
    amendment_file = evidence.bind(
        bound_amendment_path,
        code="gate_request_golden_authority_mismatch",
    )
    verifier_file = evidence.bind(
        bound_verifier_path,
        code="gate_request_golden_authority_mismatch",
    )
    manifest_file_sha256 = file_sha256(manifest_file)
    amendment_file_sha256 = file_sha256(amendment_file)
    verifier_file_sha256 = file_sha256(verifier_file)
    manifest = load_json_mapping(
        manifest_file,
        code="partial_golden_manifest_invalid",
    )
    amendment = load_json_mapping(
        amendment_file,
        code="partial_golden_amendment_invalid",
    )
    amendment_partial_golden = amendment.get("partial_golden")
    if (
        manifest_file_sha256
        != prospective_authority["golden_manifest_file_sha256"]
        or manifest.get("manifest_self_root_sha256")
        != prospective_authority["golden_manifest_self_root_sha256"]
        or manifest.get("manifest_self_root_sha256")
        != partial_golden_self_root(manifest, "manifest_self_root_sha256")
        or manifest.get("golden_root_sha256")
        != prospective_authority["golden_root_sha256"]
        or manifest.get("opaque_result_surface_root_sha256")
        != prospective_authority["opaque_result_surface_root_sha256"]
        or amendment_file_sha256
        != prospective_authority["golden_amendment_file_sha256"]
        or amendment.get("amendment_self_root_sha256")
        != prospective_authority["golden_amendment_self_root_sha256"]
        or amendment.get("amendment_self_root_sha256")
        != partial_golden_self_root(
            amendment,
            "amendment_self_root_sha256",
        )
        or not isinstance(amendment_partial_golden, Mapping)
        or amendment_partial_golden.get("manifest_self_root_sha256")
        != prospective_authority["golden_manifest_self_root_sha256"]
        or amendment_partial_golden.get("golden_root_sha256")
        != prospective_authority["golden_root_sha256"]
        or verifier_file_sha256
        != prospective_authority["fixed_verifier_file_sha256"]
    ):
        raise ValueError("gate_request_golden_authority_mismatch")
    successor_verification: dict[str, Any] | None = None
    fixed_code_authority_root = hashlib.sha256(b"").hexdigest()
    if is_successor:
        bound_successor_authority_path = _lexical_path(
            Path(str(prospective_authority["successor_authority_path"]))
        )
        successor_authority_file = evidence.bind(
            bound_successor_authority_path,
            code="gate_request_golden_authority_mismatch",
        )
        try:
            successor_verification = verify_successor_authority(
                bound_successor_authority_path
            )
            fixed_code_authority_root = _verify_fixed_verifier_code_authority(
                prospective_authority.get("fixed_verifier_code_authority"),
                evidence=evidence,
            )
        except (SuccessorAuthorityError, ValueError):
            raise ValueError("gate_request_golden_authority_mismatch") from None
        manifest_successor = manifest.get("successor_authority")
        contract_identity = manifest.get("contract_identity")
        if (
            hashlib.sha256(successor_authority_file.read_bytes()).hexdigest()
            != prospective_authority["successor_authority_file_sha256"]
            or successor_verification.get("authority_root_sha256")
            != prospective_authority["successor_authority_root_sha256"]
            or successor_verification.get("verification_root_sha256")
            != prospective_authority[
                "successor_authority_verification_root_sha256"
            ]
            or fixed_code_authority_root
            != prospective_authority[
                "fixed_verifier_code_authority_root_sha256"
            ]
            or not isinstance(manifest_successor, Mapping)
            or manifest_successor.get("authority_root_sha256")
            != successor_verification.get("authority_root_sha256")
            or not isinstance(contract_identity, Mapping)
            or contract_identity.get(
                "economic_execution_contract_digest_sha256"
            )
            != request.get("economic_execution_contract_sha256")
            or request.get("economic_execution_contract_sha256")
            != prospective_authority[
                "economic_execution_contract_digest_sha256"
            ]
        ):
            raise ValueError("gate_request_golden_authority_mismatch")
    golden_manifest_path = bound_manifest_path

    namespace_record = manifest.get("namespace")
    partial_summary_record = manifest.get("partial_summary")
    golden_surface_records = manifest.get("persisted_result_surfaces")
    if (
        manifest.get("schema")
        != (MANIFEST_SCHEMA_V2 if is_successor else MANIFEST_SCHEMA)
        or not isinstance(namespace_record, Mapping)
        or not isinstance(partial_summary_record, Mapping)
        or not isinstance(golden_surface_records, list)
        or [str(item.get("role")) for item in golden_surface_records]
        != list(ROLES)
    ):
        raise ValueError("persisted_surface_inventory_mismatch")
    golden_namespace = _lexical_path(
        Path(str(namespace_record.get("path") or ""))
    )
    accelerated_namespace = accelerated_namespace_input
    if (
        _path_has_symlink_component(golden_namespace)
        or _path_has_symlink_component(accelerated_namespace)
        or not golden_namespace.is_dir()
        or not accelerated_namespace.is_dir()
    ):
        raise ValueError("parity_namespace_storage_invalid")
    output_prefix = str(namespace_record.get("output_prefix") or "")
    expected_golden_names = {
        str(partial_summary_record.get("name") or ""),
        *(str(item.get("name") or "") for item in golden_surface_records),
    }
    try:
        observed_golden_names = {
            path.name
            for path in golden_namespace.iterdir()
            if path.name.startswith(output_prefix + "_")
        }
    except OSError:
        raise ValueError("golden_namespace_inventory_mismatch") from None
    if (
        not output_prefix
        or "" in expected_golden_names
        or len(expected_golden_names) != len(ROLES) + 1
        or observed_golden_names != expected_golden_names
    ):
        raise ValueError("golden_namespace_inventory_mismatch")
    if (
        golden_namespace == accelerated_namespace
        or golden_namespace in accelerated_namespace.parents
        or accelerated_namespace in golden_namespace.parents
    ):
        raise ValueError("parity_namespace_not_separate")

    try:
        golden_verification = verify_partial_golden_manifest(
            golden_manifest_path,
            git_root=(git_root or Path(__file__).resolve().parents[2]),
        )
    except (PartialGoldenVerificationError, OSError, ValueError):
        evidence.assert_paths_unchanged()
        raise ValueError("partial_golden_authority_invalid") from None
    evidence.assert_paths_unchanged()
    if (
        golden_verification.get("gate")
        != "PARTIAL_GOLDEN_INDEPENDENTLY_ACCEPTED"
        or golden_verification.get("semantic_result_values_emitted") is not False
        or golden_verification.get("legacy_evidence_modified") is not False
        or golden_verification.get("manifest_self_root_sha256")
        != manifest.get("manifest_self_root_sha256")
        or golden_verification.get("golden_root_sha256")
        != manifest.get("golden_root_sha256")
        or (
            is_successor
            and (
                golden_verification.get("successor_authority_root_sha256")
                != prospective_authority[
                    "successor_authority_root_sha256"
                ]
                or golden_verification.get(
                    "successor_authority_verification_root_sha256"
                )
                != prospective_authority[
                    "successor_authority_verification_root_sha256"
                ]
            )
        )
    ):
        raise ValueError("partial_golden_authority_invalid")
    manifest_scope = manifest.get("scope")
    contract_identity = manifest.get("contract_identity")
    if (
        not isinstance(manifest_scope, Mapping)
        or not isinstance(contract_identity, Mapping)
        or request.get("output_prefix") != output_prefix
        or request_partial.get("name") != partial_summary_record.get("name")
        or scope.get("start_day") != manifest_scope.get("start_day")
        or scope.get("completed_through_day") != manifest_scope.get("end_day")
        or scope.get("day_count") != manifest_scope.get("day_count")
        or scope.get("arm_id") != manifest_scope.get("arm_id")
        or request.get("source_plan_digest_sha256")
        != contract_identity.get("source_plan_digest_sha256")
        or (
            not is_successor
            and request.get("shared_execution_contract_sha256")
            != contract_identity.get(
                "shared_execution_contract_digest_sha256"
            )
        )
        or (
            is_successor
            and request.get("economic_execution_contract_sha256")
            != contract_identity.get(
                "economic_execution_contract_digest_sha256"
            )
        )
        or request.get("arm_fingerprint_sha256")
        != contract_identity.get("arm_fingerprint_sha256")
    ):
        raise ValueError("gate_request_golden_authority_mismatch")

    expected_accelerated_names = {
        str(request_partial["name"]),
        *(str(item["name"]) for item in request_surface_records),
    }
    try:
        observed_accelerated_names = {
            path.name
            for path in accelerated_namespace.iterdir()
            if path.name.startswith(output_prefix + "_")
        }
    except OSError:
        raise ValueError("accelerated_namespace_inventory_mismatch") from None
    if (
        "" in expected_accelerated_names
        or len(expected_accelerated_names) != len(ROLES) + 1
        or observed_accelerated_names != expected_accelerated_names
    ):
        raise ValueError("accelerated_namespace_inventory_mismatch")

    golden_surfaces = {
        str(item["role"]): item for item in golden_surface_records
    }
    request_surfaces = {
        str(item["role"]): item for item in request_surface_records
    }
    verified_surfaces: list[dict[str, Any]] = []
    golden_paths: dict[str, BoundRegularFile] = {}
    accelerated_paths: dict[str, BoundRegularFile] = {}
    verified_campaigns: dict[Path, dict[str, Any]] = {}
    campaign_manifests: dict[Path, dict[str, Any]] = {}
    campaign_files: dict[Path, BoundRegularFile] = {}
    campaign_roles: dict[Path, set[str]] = {}
    union_roles = ("missed", "order", "trade")
    accelerated_union_accumulator = CandidateUnionAccumulator()
    # Archive identity, decompressed integrity, and downstream candidate
    # projection are one pass over the same no-follow evidence descriptors.
    for request_record in request_surface_records:
        if request_record.get("storage") != "verified_zstd_campaign":
            continue
        campaign_path = _lexical_path(
            Path(str(request_record["archive_campaign_manifest_path"]))
        )
        campaign_file = evidence.bind(
            campaign_path,
            code="archive_campaign_identity_mismatch",
        )
        campaign_manifest = campaign_manifests.get(campaign_path)
        if campaign_manifest is None:
            campaign_manifest = load_canonical(campaign_file)
            campaign_manifests[campaign_path] = campaign_manifest
            campaign_files[campaign_path] = campaign_file
        if (
            campaign_manifest.get("schema")
            != "gtos.replay_acceleration.streaming_proof_campaign.v1"
            or campaign_manifest.get("campaign_manifest_root_sha256")
            != self_root(
                campaign_manifest,
                "campaign_manifest_root_sha256",
            )
            or campaign_manifest.get("campaign_manifest_root_sha256")
            != request_record.get("archive_campaign_manifest_root_sha256")
            or campaign_manifest.get("output_prefix")
            != request.get("output_prefix")
        ):
            raise ValueError("archive_campaign_identity_mismatch")
        campaign_roles.setdefault(campaign_path, set()).add(
            str(request_record["role"])
        )
    if len(campaign_manifests) > 1:
        raise ValueError("archive_campaign_coherence_mismatch")
    for campaign_path, campaign_manifest in campaign_manifests.items():
        projected_roles = tuple(
            role for role in union_roles if role in campaign_roles[campaign_path]
        )
        if projected_roles:
            campaign_report = verify_campaign_with_role_line_consumer(
                campaign_path,
                roles=projected_roles,
                consumer=lambda role, raw: accelerated_union_accumulator.add(
                    union_roles.index(role),
                    raw,
                ),
            )
        else:
            campaign_report = verify_campaign(campaign_path)
        if (
            campaign_report.get("campaign_manifest_path")
            != str(campaign_path)
            or campaign_report.get("campaign_manifest_sha256")
            != file_sha256(campaign_files[campaign_path])
            or campaign_report.get("campaign_manifest_root_sha256")
            != campaign_manifest.get("campaign_manifest_root_sha256")
        ):
            raise ValueError("archive_campaign_identity_mismatch")
        verified_campaigns[campaign_path] = campaign_report
        evidence.assert_paths_unchanged()
    if verified_campaigns:
        campaign_report = next(iter(verified_campaigns.values()))
        partition_calendars: dict[str, list[tuple[str, str]]] = {
            role: [
                (str(row["start_day"]), str(row["end_day"]))
                for row in campaign_report["verified_role_partitions"]
                if row.get("role") == role
            ]
            for role in ("decision", "scorecard", "missed")
        }
        calendar_values = list(partition_calendars.values())
        if (
            not calendar_values
            or not calendar_values[0]
            or any(value != calendar_values[0] for value in calendar_values[1:])
            or calendar_values[0][0][0] != scope.get("start_day")
            or calendar_values[0][-1][1]
            != scope.get("completed_through_day")
        ):
            raise ValueError("archive_campaign_scope_mismatch")
    for role in ROLES:
        golden_record = golden_surfaces[role]
        request_record = request_surfaces[role]
        if golden_record.get("name") != request_record.get("name"):
            raise ValueError("persisted_surface_name_mismatch")
        golden_path = _bound_regular_file_inside(
            golden_namespace / str(golden_record["name"]),
            golden_namespace,
            evidence=evidence,
            code="partial_golden_authority_invalid",
        )
        accelerated_input = _lexical_path(
            accelerated_namespace / str(request_record["name"])
        )
        if _path_has_symlink_component(accelerated_input):
            raise ValueError("accelerated_surface_aliases_golden")
        accelerated_path = _bound_regular_file_inside(
            accelerated_input,
            accelerated_namespace,
            evidence=evidence,
            code="accelerated_surface_storage_invalid",
        )
        if accelerated_path.identity == golden_path.identity:
            raise ValueError("accelerated_surface_aliases_golden")
        golden_paths[role] = golden_path
        golden_contract = stream_contract(golden_path)
        if request_record.get("storage") == "verified_zstd_campaign":
            if (
                stream_contract(accelerated_path)
                != request_record["hot_tombstone"]
            ):
                raise ValueError("archived_hot_surface_not_empty")
            campaign_path = _lexical_path(
                Path(str(request_record["archive_campaign_manifest_path"]))
            )
            cumulative = {
                str(item["role"]): item
                for item in verified_campaigns[campaign_path][
                    "cumulative_surfaces"
                ]
            }
            accelerated_contract = {
                key: cumulative[role][key]
                for key in ("bytes", "rows", "sha256")
            }
        else:
            accelerated_contract = stream_contract(accelerated_path)
            accelerated_paths[role] = accelerated_path
        if (
            golden_contract != accelerated_contract
            or golden_contract
            != {
                key: golden_record[key] for key in ("bytes", "rows", "sha256")
            }
            or accelerated_contract
            != {
                key: request_record[key] for key in ("bytes", "rows", "sha256")
            }
        ):
            raise ValueError(f"persisted_ledger_byte_mismatch:{role}")
        verified_surfaces.append({"role": role, **accelerated_contract})

    golden_partial_path = _bound_regular_file_inside(
        golden_namespace / str(manifest["partial_summary"]["name"]),
        golden_namespace,
        evidence=evidence,
        code="partial_golden_authority_invalid",
    )
    accelerated_partial_input = _lexical_path(
        Path(str(request_partial["snapshot_path"]))
    )
    if _path_has_symlink_component(accelerated_partial_input):
        raise ValueError("accelerated_surface_aliases_golden")
    try:
        accelerated_partial_input.relative_to(accelerated_namespace)
    except ValueError:
        raise ValueError("partial_summary_snapshot_outside_namespace") from None
    accelerated_partial_path = evidence.bind(
        accelerated_partial_input,
        code="partial_summary_snapshot_identity_mismatch",
        namespace=accelerated_namespace,
    )
    if accelerated_partial_path.identity == golden_partial_path.identity:
        raise ValueError("accelerated_surface_aliases_golden")
    if stream_contract(accelerated_partial_path) != {
        key: request_partial[key] for key in ("bytes", "rows", "sha256")
    }:
        raise ValueError("partial_summary_snapshot_identity_mismatch")
    golden_partial = load_json_mapping(
        golden_partial_path,
        code="partial_summary_json_invalid",
    )
    accelerated_partial = load_json_mapping(
        accelerated_partial_path,
        code="partial_summary_json_invalid",
    )
    (
        archive_transformation_root_sha256,
        partial_runtime_envelope_keys,
    ) = _verify_partial_summary_archive_transformation(
        transformation=archive_transformation,
        verified_campaigns=verified_campaigns,
        accelerated_partial_path=accelerated_partial_path,
        accelerated_partial=accelerated_partial,
        request_partial=request_partial,
        evidence=evidence,
    )
    golden_semantic_input: Mapping[str, Any] = golden_partial
    accelerated_semantic_input: Mapping[str, Any] = accelerated_partial
    if is_successor:
        (
            acceleration_envelope_root_sha256,
            acceleration_runtime_envelope_keys,
            golden_semantic_input,
            accelerated_semantic_input,
        ) = _verify_partial_summary_acceleration_envelope(
            transformation=acceleration_envelope_transformation,
            golden_partial_path=golden_partial_path,
            accelerated_partial_path=accelerated_partial_path,
            golden_partial=golden_partial,
            accelerated_partial=accelerated_partial,
            request=request,
            evidence=evidence,
        )
        partial_runtime_envelope_keys = frozenset(
            {
                *partial_runtime_envelope_keys,
                *acceleration_runtime_envelope_keys,
            }
        )
        semantic_runtime_envelope_keys = frozenset()
    else:
        if acceleration_envelope_transformation is not None:
            raise ValueError("acceleration_envelope_authority_unexpected")
        acceleration_envelope_root_sha256 = root(None)
        semantic_runtime_envelope_keys = partial_runtime_envelope_keys
    golden_semantics = partial_semantic_contract(
        golden_semantic_input,
        runtime_envelope_keys=semantic_runtime_envelope_keys,
    )
    accelerated_semantics = partial_semantic_contract(
        accelerated_semantic_input,
        runtime_envelope_keys=semantic_runtime_envelope_keys,
    )
    category_equality = {
        name: golden_semantics["categories"][name]
        == accelerated_semantics["categories"][name]
        and int(golden_semantics["categories"][name]["match_count"]) > 0
        for name in CATEGORY_TERMS
    }
    if (
        golden_semantics["core_root_sha256"]
        != accelerated_semantics["core_root_sha256"]
        or not all(category_equality.values())
    ):
        raise ValueError("partial_summary_semantic_mismatch")

    golden_union = candidate_union_root_from_lines(
        path_lines(golden_paths[role]) for role in union_roles
    )
    for source_index, role in enumerate(union_roles):
        if role not in accelerated_paths:
            continue
        for raw in path_lines(accelerated_paths[role]):
            accelerated_union_accumulator.add(source_index, raw)
    accelerated_union = accelerated_union_accumulator.result()
    if golden_union != accelerated_union or accelerated_union[2] != 0:
        raise ValueError("candidate_identity_union_mismatch")
    surface_root = root(verified_surfaces)
    golden_verification_root = root(golden_verification)
    archive_campaign_verifications = [
        {
            "campaign_manifest_path": str(path),
            "campaign_manifest_sha256": verification[
                "campaign_manifest_sha256"
            ],
            "campaign_manifest_root_sha256": campaign_manifests[path][
                "campaign_manifest_root_sha256"
            ],
            "verification_root_sha256": verification[
                "verification_root_sha256"
            ],
            "verified_role_partitions_root_sha256": verification[
                "verified_role_partitions_root_sha256"
            ],
        }
        for path, verification in sorted(
            verified_campaigns.items(), key=lambda item: str(item[0])
        )
    ]
    report_core = {
        "schema": REPORT_SCHEMA_V2 if is_successor else REPORT_SCHEMA,
        "valid": True,
        "gate": "EXACT_FULL_RESULT_PARITY_ACCEPTED",
        "output_prefix": request["output_prefix"],
        "scope": dict(request["scope"]),
        "contract_identity": dict(contract_identity),
        "all_persisted_ledger_bytes_equal": True,
        "persisted_result_surface_root_sha256": surface_root,
        "persisted_result_surfaces": verified_surfaces,
        "archive_campaign_verifications": archive_campaign_verifications,
        "archive_campaign_verification_set_root_sha256": root(
            archive_campaign_verifications
        ),
        "partial_summary_semantic_root_sha256": accelerated_semantics[
            "core_root_sha256"
        ],
        "partial_summary_archive_transformation_root_sha256": (
            archive_transformation_root_sha256
        ),
        **(
            {
                "partial_summary_acceleration_envelope_transformation_root_sha256": (
                    acceleration_envelope_root_sha256
                ),
                "successor_authority_root_sha256": prospective_authority[
                    "successor_authority_root_sha256"
                ],
                "successor_authority_verification_root_sha256": (
                    prospective_authority[
                        "successor_authority_verification_root_sha256"
                    ]
                ),
                "economic_execution_contract_digest_sha256": request[
                    "economic_execution_contract_sha256"
                ],
                "accelerated_shared_execution_contract_digest_sha256": request[
                    "shared_execution_contract_sha256"
                ],
                "accelerator_implementation_authority_root_sha256": request[
                    "accelerator_implementation_authority_root_sha256"
                ],
                "fixed_verifier_code_authority_root_sha256": (
                    fixed_code_authority_root
                ),
            }
            if is_successor
            else {}
        ),
        "semantic_category_equality": category_equality,
        "semantic_category_roots": {
            name: accelerated_semantics["categories"][name]
            for name in CATEGORY_TERMS
        },
        "candidate_identity_union_root_sha256": accelerated_union[0],
        "candidate_identity_union_count": accelerated_union[1],
        "candidate_identity_missing_count": accelerated_union[2],
        "golden_manifest_sha256": golden_verification["manifest_sha256"],
        "golden_manifest_self_root_sha256": manifest[
            "manifest_self_root_sha256"
        ],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "golden_amendment_sha256": amendment_file_sha256,
        "golden_amendment_self_root_sha256": amendment[
            "amendment_self_root_sha256"
        ],
        "fixed_verifier_file_sha256": verifier_file_sha256,
        "partial_golden_verification_root_sha256": golden_verification_root,
        "gate_request_root_sha256": request["gate_request_root_sha256"],
        "economic_values_exposed": False,
        "independent_writer_imported": False,
        "independent_runner_imported": False,
        "other_arms_launched": False,
        "broker_live_authority": False,
    }
    report = {**report_core, "report_root_sha256": root(report_core)}
    receipt_core = {
        "schema": RECEIPT_SCHEMA_V2 if is_successor else RECEIPT_SCHEMA,
        "status": "EXACT_FULL_RESULT_PARITY_ACCEPTED",
        "parity_accepted": True,
        "gate_request_root_sha256": request["gate_request_root_sha256"],
        "parity_report_root_sha256": report["report_root_sha256"],
        "golden_manifest_sha256": golden_verification["manifest_sha256"],
        "golden_manifest_self_root_sha256": manifest[
            "manifest_self_root_sha256"
        ],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "golden_amendment_sha256": amendment_file_sha256,
        "golden_amendment_self_root_sha256": amendment[
            "amendment_self_root_sha256"
        ],
        "fixed_verifier_file_sha256": verifier_file_sha256,
        "partial_golden_verification_root_sha256": golden_verification_root,
        "persisted_result_surface_root_sha256": surface_root,
        "partial_summary_semantic_root_sha256": accelerated_semantics[
            "core_root_sha256"
        ],
        "partial_summary_archive_transformation_root_sha256": (
            archive_transformation_root_sha256
        ),
        **(
            {
                "partial_summary_acceleration_envelope_transformation_root_sha256": (
                    acceleration_envelope_root_sha256
                ),
                "successor_authority_root_sha256": prospective_authority[
                    "successor_authority_root_sha256"
                ],
                "successor_authority_verification_root_sha256": (
                    prospective_authority[
                        "successor_authority_verification_root_sha256"
                    ]
                ),
                "economic_execution_contract_digest_sha256": request[
                    "economic_execution_contract_sha256"
                ],
                "accelerated_shared_execution_contract_digest_sha256": request[
                    "shared_execution_contract_sha256"
                ],
                "accelerator_implementation_authority_root_sha256": request[
                    "accelerator_implementation_authority_root_sha256"
                ],
                "fixed_verifier_code_authority_root_sha256": (
                    fixed_code_authority_root
                ),
            }
            if is_successor
            else {}
        ),
        "output_prefix": request["output_prefix"],
        "completed_through_day": request["scope"]["completed_through_day"],
        "accelerated_s0r0_research_route_authorized": True,
        "same_state_continuation_through_2026_01_31_authorized": True,
        "other_arms_launched": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    receipt = {**receipt_core, "receipt_root_sha256": root(receipt_core)}
    return report, receipt


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    try:
        immutable_write_bytes(
            path,
            canonical_bytes(value) + b"\n",
            code="immutable_parity_output_exists_or_invalid",
        )
    except ImmutableEvidenceError:
        raise ValueError("immutable_parity_output_exists_or_invalid") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-manifest", type=Path, required=True)
    parser.add_argument("--accelerated-namespace", type=Path, required=True)
    parser.add_argument("--gate-request", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()
    request = load_canonical(args.gate_request)
    report, receipt = verify_real_parity(
        golden_manifest_path=args.golden_manifest,
        accelerated_namespace=args.accelerated_namespace,
        gate_request=request,
    )
    atomic_write(args.report_output, report)
    atomic_write(args.receipt_output, receipt)
    print(
        canonical_bytes(
            {
                "status": receipt["status"],
                "report_root_sha256": report["report_root_sha256"],
                "receipt_root_sha256": receipt["receipt_root_sha256"],
                "economic_values_exposed": False,
            }
        ).decode("ascii")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
