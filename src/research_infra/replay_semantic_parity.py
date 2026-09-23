"""Fail-closed semantic projections for accelerated replay ledgers.

The projection is intentionally narrower than a generic JSON normalizer.  A
role has to be registered explicitly, and volatile paths are handled by a
role-specific rule that also rebuilds every hash whose meaning depends on the
volatile envelope.  Causal timestamps and economic fields are never removed.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from itertools import zip_longest
from typing import Any

from src.research_infra.replay_canonical_bytes import (
    NonFiniteCanonicalValueError,
    canonical_bytes as _shared_canonical_bytes,
)


SEMANTIC_PARITY_SCHEMA = "gtos.replay_acceleration.semantic_parity.v1"
SEMANTIC_PROOF_ROW_SCHEMA = "gtos.replay_acceleration.semantic_proof_row.v1"
SEMANTIC_DIAGNOSTIC_STATUS = (
    "DECLARED_RUNTIME_ENVELOPE_SEMANTIC_DIAGNOSTIC_PASS"
)
SEMANTIC_INCOMPLETE_STATUS = (
    "UNBOUND_RUNTIME_ENVELOPE_SEMANTIC_DIAGNOSTIC_INCOMPLETE"
)
SUPPORTED_ROLES = ("scorecard", "order", "trade", "oracle", "missed")
ROLE_ROW_TYPES = {
    "scorecard": "scheduler_scorecard",
    "order": "simulated_order",
    "trade": "simulated_trade",
    "oracle": "ordered_path_oracle",
    "missed": "missed_opportunity",
}
_RUNTIME_ENVELOPE_SENTINEL = "<normalized-runtime-envelope>"
_SHA256_HEX_LENGTH = 64
_ORDER_LIFECYCLE_SCHEMA = "broker_order_lifecycle_capture_v4_packet_v1"
_ORDER_LIFECYCLE_COMPONENT = "broker_order_lifecycle_capture_v4"
_ROW_PROVENANCE_SCHEMA = "broad_live_as_if_replay_row_provenance_v1"
_SCORECARD_PROJECTION_SCHEMA = (
    "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
)
_SCORECARD_ALIAS_FIELDS = (
    "pre_risk_finalizer_scheduler_option_trace",
    "post_risk_finalizer_scheduler_option_trace",
)
_SCORECARD_OMITTED_STATUS = (
    "canonical_trace_preserved_exact_duplicate_aliases_omitted"
)
_SCORECARD_NO_ALIAS_STATUS = "canonical_trace_preserved_no_aliases_present"
_SCORECARD_DISTINCT_ALIAS_STATUS = (
    "canonical_trace_preserved_distinct_aliases_not_compacted"
)
_MISSED_PROJECTION_SCHEMA = "compact_broad_replay_missed_opportunity_v1"
_CANDIDATE_CONTEXT_FIELDS = (
    "campaign",
    "profile",
    "decision_window_id",
    "candidate_id",
    "canonical_replay_candidate_instance_key",
    "decision_time_utc",
)
_CANDIDATE_ROW_TYPES = {"candidate", "candidate_index", "semantic_candidate"}
_SEMANTIC_CANDIDATE_SCHEMA = "gtos.replay_acceleration.semantic_candidate.v1"
_SEMANTIC_CANDIDATE_PROVENANCE_SCHEMA = (
    "gtos.replay_acceleration.semantic_candidate_provenance.v1"
)
_COMPACT_CANDIDATE_INDEX_SCHEMA = "compact_broad_replay_candidate_index_v1"
_SIDECAR_OWNER_FIELDS = {
    *_CANDIDATE_CONTEXT_FIELDS,
    "simulated_order_id",
    "payload_root_sha256",
}


class SemanticParityError(ValueError):
    """Raised when a projection cannot prove that normalization is safe."""


def canonical_bytes(value: Any) -> bytes:
    # Delegates to the single authoritative encoder.  The previous local copy
    # used ``allow_nan=True``, which serialised NaN/Infinity to bare tokens;
    # because parity is decided on bytes, two runs that both produced an
    # undefined economic value then compared EQUAL.  The shared encoder fails
    # closed and names the offending path.  See replay_canonical_bytes.
    return _shared_canonical_bytes(value)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class _CanonicalArrayHasher:
    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self._digest.update(b"[")
        self._count = 0

    @property
    def count(self) -> int:
        return self._count

    def update(self, value: Any) -> None:
        if self._count:
            self._digest.update(b",")
        self._digest.update(canonical_bytes(value))
        self._count += 1

    def hexdigest(self) -> str:
        digest = self._digest.copy()
        digest.update(b"]")
        return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != _SHA256_HEX_LENGTH:
        return False
    return all(character in "009abcdef" for character in value)


def _packet_hash(value: Mapping[str, Any]) -> str:
    return canonical_sha256(
        {
            key: item
            for key, item in value.items()
            if key not in {"generated_at_utc", "packet_hash_sha256"}
        }
    )


def _exact_day(value: Any, *, side: str) -> date:
    if type(value) is not str or len(value) != 10:
        raise _semantic_proof_inventory_error(side)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise _semantic_proof_inventory_error(side) from None
    if parsed.isoformat() != value:
        raise _semantic_proof_inventory_error(side)
    return parsed


def _nonblank_timestamp(value: Any) -> bool:
    if (
        type(value) is not str
        or value != value.strip()
        or "T" not in value
        or not value.endswith(("Z", "+00:00"))
    ):
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


def _validate_scorecard_topology(
    row: Mapping[str, Any],
    *,
    row_index: int,
) -> None:
    trace = row.get("scheduler_option_trace")
    status = row.get("scheduler_option_trace_projection_status")
    omitted = row.get("scheduler_option_trace_omitted_duplicate_aliases")
    if (
        not isinstance(trace, list)
        or not trace
        or status
        not in {
            _SCORECARD_OMITTED_STATUS,
            _SCORECARD_NO_ALIAS_STATUS,
            _SCORECARD_DISTINCT_ALIAS_STATUS,
        }
        or not isinstance(omitted, list)
        or any(not isinstance(field, str) for field in omitted)
        or len(omitted) != len(set(omitted))
        or not set(omitted).issubset(_SCORECARD_ALIAS_FIELDS)
        or row.get("scheduler_option_trace_projection_sha256")
        != canonical_sha256(trace)
    ):
        raise SemanticParityError(
            f"semantic_scorecard_topology_unproven:{row_index}"
        )
    alias_values = {
        field: row.get(field) for field in _SCORECARD_ALIAS_FIELDS
    }
    if status == _SCORECARD_OMITTED_STATUS:
        if (
            not omitted
            or any(field in row for field in omitted)
            or any(
                value == trace
                for field, value in alias_values.items()
                if field not in omitted and value not in (None, "", [], {})
            )
        ):
            raise SemanticParityError(
                f"semantic_scorecard_topology_unproven:{row_index}"
            )
        return
    if omitted:
        raise SemanticParityError(
            f"semantic_scorecard_topology_unproven:{row_index}"
        )
    present_aliases = [
        value
        for value in alias_values.values()
        if value not in (None, "", [], {})
    ]
    if status == _SCORECARD_NO_ALIAS_STATUS:
        valid = not present_aliases
    else:
        valid = bool(present_aliases) and all(
            value != trace for value in present_aliases
        )
    if not valid:
        raise SemanticParityError(
            f"semantic_scorecard_topology_unproven:{row_index}"
        )


def _validate_role_row(
    role: str,
    row: Mapping[str, Any],
    *,
    row_index: int,
) -> None:
    if (
        row.get("row_type") != ROLE_ROW_TYPES[role]
        or row.get("row_provenance_schema") != _ROW_PROVENANCE_SCHEMA
        or (
            role == "scorecard"
            and row.get("compact_scorecard_projection_schema")
            != _SCORECARD_PROJECTION_SCHEMA
        )
        or (
            role == "missed"
            and row.get("missed_opportunity_compact_schema")
            != _MISSED_PROJECTION_SCHEMA
        )
    ):
        raise SemanticParityError(
            f"semantic_row_schema_invalid:{role}:{row_index}"
        )
    if role == "scorecard":
        _validate_scorecard_topology(row, row_index=row_index)
    if "selected_order_sequence" in row and type(
        row.get("selected_order_sequence")
    ) is not int:
        raise SemanticParityError(
            f"semantic_integral_field_invalid:{role}:{row_index}"
        )

    lifecycle = row.get("broker_order_lifecycle_capture_v4_packet")
    if role == "order" and not isinstance(lifecycle, Mapping):
        raise SemanticParityError(
            f"order_runtime_envelope_missing:{row_index}"
        )
    if lifecycle is None:
        return
    if role not in {"order", "trade"} or not isinstance(lifecycle, Mapping):
        raise SemanticParityError(
            f"semantic_lifecycle_packet_invalid:{role}:{row_index}"
        )
    if (
        lifecycle.get("schema_version") != _ORDER_LIFECYCLE_SCHEMA
        or lifecycle.get("component") != _ORDER_LIFECYCLE_COMPONENT
    ):
        raise SemanticParityError(
            f"{role}_runtime_envelope_schema_not_allowlisted:{row_index}"
        )
    generated_at_utc = lifecycle.get("generated_at_utc")
    if not _nonblank_timestamp(generated_at_utc):
        raise SemanticParityError(
            f"{role}_runtime_envelope_timestamp_invalid:{row_index}"
        )
    if lifecycle.get("packet_hash_sha256") != _packet_hash(lifecycle):
        raise SemanticParityError(
            f"{role}_runtime_envelope_packet_hash_invalid:{row_index}"
        )


def _validated_order_execution_preimage(
    row: Mapping[str, Any],
    *,
    row_index: int,
    provenance_preimages: Mapping[str, Mapping[str, Any]] | None,
    provenance_owners: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    sidecar_id = str(row.get("execution_packet_sidecar_id") or "").strip()
    preimage = (
        provenance_preimages.get(sidecar_id)
        if sidecar_id and isinstance(provenance_preimages, Mapping)
        else None
    )
    if not isinstance(preimage, Mapping):
        raise SemanticParityError(f"semantic_preimage_missing:order:{row_index}")
    required_preimage_fields = {
        "execution_manager_packet",
        "broker_order_lifecycle_capture_v4_packet",
    }
    if set(preimage) != required_preimage_fields:
        raise SemanticParityError(
            f"semantic_preimage_incomplete:order:{row_index}"
        )
    execution_packet = preimage.get("execution_manager_packet")
    broker_packet = preimage.get("broker_order_lifecycle_capture_v4_packet")
    row_broker_packet = row.get("broker_order_lifecycle_capture_v4_packet")
    if not isinstance(execution_packet, Mapping) or not isinstance(
        broker_packet, Mapping
    ):
        raise SemanticParityError(
            f"semantic_preimage_payload_invalid:order:{row_index}"
        )
    if canonical_bytes(broker_packet) != canonical_bytes(row_broker_packet):
        raise SemanticParityError(
            f"semantic_preimage_broker_packet_mismatch:order:{row_index}"
        )
    if (
        execution_packet.get("schema_version") != "execution_manager_v4_packet_v1"
        or execution_packet.get("component") != "execution_manager_v4"
    ):
        raise SemanticParityError(
            f"semantic_preimage_execution_schema_invalid:order:{row_index}"
        )
    if not _nonblank_timestamp(execution_packet.get("generated_at_utc")):
        raise SemanticParityError(
            f"semantic_preimage_timestamp_invalid:order:{row_index}"
        )
    if not str(execution_packet.get("action") or "").strip():
        raise SemanticParityError(
            f"semantic_preimage_incomplete:order:{row_index}"
        )
    nested_lifecycle = execution_packet.get(
        "broker_order_lifecycle_capture_v4"
    )
    if not isinstance(nested_lifecycle, Mapping) or (
        nested_lifecycle.get("schema_version") != _ORDER_LIFECYCLE_SCHEMA
        or nested_lifecycle.get("component") != _ORDER_LIFECYCLE_COMPONENT
    ):
        raise SemanticParityError(
            f"semantic_preimage_nested_lifecycle_invalid:order:{row_index}"
        )
    if not _nonblank_timestamp(nested_lifecycle.get("generated_at_utc")):
        raise SemanticParityError(
            f"semantic_preimage_timestamp_invalid:order:{row_index}"
        )
    if nested_lifecycle.get("packet_hash_sha256") != _packet_hash(
        nested_lifecycle
    ):
        raise SemanticParityError(
            f"semantic_preimage_nested_packet_hash_invalid:order:{row_index}"
        )
    broker_pre_order = broker_packet.get("pre_order_capture_contract")
    embedded_execution_hash = (
        broker_pre_order.get("execution_manager_packet_hash")
        if isinstance(broker_pre_order, Mapping)
        else None
    )
    if embedded_execution_hash != _packet_hash(execution_packet):
        raise SemanticParityError(
            f"semantic_preimage_execution_hash_mismatch:order:{row_index}"
        )
    execution_hash = canonical_sha256(execution_packet)
    declared_execution_hash = row.get(
        "semantic_execution_manager_packet_sha256",
        row.get("execution_manager_packet_hash_sha256"),
    )
    if declared_execution_hash != execution_hash:
        raise SemanticParityError(
            f"semantic_execution_manager_hash_mismatch:order:{row_index}"
        )
    sidecar_hash = canonical_sha256(preimage)
    declared_sidecar_hash = row.get(
        "semantic_order_preimage_sha256",
        row.get("execution_packet_sidecar_hash_sha256"),
    )
    if declared_sidecar_hash != sidecar_hash:
        raise SemanticParityError(
            f"semantic_sidecar_hash_mismatch:order:{row_index}"
        )
    owner = (
        provenance_owners.get(sidecar_id)
        if sidecar_id and isinstance(provenance_owners, Mapping)
        else None
    )
    if provenance_owners is not None:
        row_owner = {
            field: row.get(field)
            for field in _CANDIDATE_CONTEXT_FIELDS
        }
        row_owner["simulated_order_id"] = row.get("simulated_order_id")
        if (
            not isinstance(owner, Mapping)
            or set(owner) != _SIDECAR_OWNER_FIELDS
            or owner.get("payload_root_sha256") != sidecar_hash
            or any(
                type(owner.get(field)) is not str
                or not str(owner.get(field)).strip()
                for field in _SIDECAR_OWNER_FIELDS
                if field != "payload_root_sha256"
            )
            or any(owner.get(field) != value for field, value in row_owner.items())
        ):
            raise SemanticParityError(
                f"semantic_sidecar_owner_mismatch:order:{row_index}"
            )
        execution_identity = execution_packet.get("identity")
        execution_timing = execution_packet.get("entry_timing")
        broker_identity = broker_packet.get("identity")
        if (
            not isinstance(execution_identity, Mapping)
            or not isinstance(execution_timing, Mapping)
            or not isinstance(broker_identity, Mapping)
            or execution_identity.get("candidate_id") != owner["candidate_id"]
            or execution_timing.get("decision_time_utc")
            != owner["decision_time_utc"]
            or broker_identity.get("candidate_id") != owner["candidate_id"]
            or broker_identity.get("decision_time_utc")
            != owner["decision_time_utc"]
        ):
            raise SemanticParityError(
                f"semantic_sidecar_owner_mismatch:order:{row_index}"
            )
    return copy.deepcopy(dict(preimage))


def _normalize_order_runtime_envelope(
    row: dict[str, Any],
    *,
    row_index: int,
    provenance_preimages: Mapping[str, Mapping[str, Any]] | None,
    provenance_owners: Mapping[str, Mapping[str, Any]] | None,
) -> list[list[str]]:
    packet = row.get("broker_order_lifecycle_capture_v4_packet")
    if not isinstance(packet, Mapping) or "generated_at_utc" not in packet:
        return []
    packet = copy.deepcopy(dict(packet))
    if (
        packet.get("schema_version") != _ORDER_LIFECYCLE_SCHEMA
        or packet.get("component") != _ORDER_LIFECYCLE_COMPONENT
    ):
        raise SemanticParityError(
            f"order_runtime_envelope_schema_not_allowlisted:{row_index}"
        )
    generated_at_utc = packet.get("generated_at_utc")
    if not _nonblank_timestamp(generated_at_utc):
        raise SemanticParityError(
            f"order_runtime_envelope_timestamp_invalid:{row_index}"
        )
    pre_order_contract = packet.get("pre_order_capture_contract")
    if not isinstance(pre_order_contract, Mapping):
        raise SemanticParityError(
            f"order_runtime_envelope_pre_order_contract_invalid:{row_index}"
        )
    pre_order_contract = copy.deepcopy(dict(pre_order_contract))
    nested_execution_hash = pre_order_contract.get(
        "execution_manager_packet_hash"
    )
    if not _is_sha256(nested_execution_hash):
        raise SemanticParityError(
            f"order_runtime_envelope_execution_hash_invalid:{row_index}"
        )
    packet_hash = packet.get("packet_hash_sha256")
    packet_hash_material = {
        key: value
        for key, value in packet.items()
        if key not in {"generated_at_utc", "packet_hash_sha256"}
    }
    if packet_hash != canonical_sha256(packet_hash_material):
        raise SemanticParityError(
            f"order_runtime_envelope_packet_hash_invalid:{row_index}"
        )

    preimage = _validated_order_execution_preimage(
        row,
        row_index=row_index,
        provenance_preimages=provenance_preimages,
        provenance_owners=provenance_owners,
    )
    execution_packet = copy.deepcopy(
        dict(preimage["execution_manager_packet"])
    )
    nested_lifecycle = copy.deepcopy(
        dict(execution_packet["broker_order_lifecycle_capture_v4"])
    )
    nested_generated_at_utc = nested_lifecycle.get("generated_at_utc")
    execution_generated_at_utc = execution_packet.get("generated_at_utc")
    if not _nonblank_timestamp(
        nested_generated_at_utc
    ) or not _nonblank_timestamp(execution_generated_at_utc):
        raise SemanticParityError(
            f"semantic_preimage_timestamp_invalid:order:{row_index}"
        )
    nested_lifecycle["generated_at_utc"] = _RUNTIME_ENVELOPE_SENTINEL
    nested_lifecycle["packet_hash_sha256"] = _packet_hash(nested_lifecycle)
    execution_packet["generated_at_utc"] = _RUNTIME_ENVELOPE_SENTINEL
    execution_packet[
        "broker_order_lifecycle_capture_v4"
    ] = nested_lifecycle

    packet["generated_at_utc"] = _RUNTIME_ENVELOPE_SENTINEL
    pre_order_contract[
        "execution_manager_packet_hash"
    ] = _packet_hash(execution_packet)
    packet["pre_order_capture_contract"] = pre_order_contract
    packet["packet_hash_sha256"] = canonical_sha256(
        {
            key: value
            for key, value in packet.items()
            if key not in {"generated_at_utc", "packet_hash_sha256"}
        }
    )
    row["broker_order_lifecycle_capture_v4_packet"] = packet
    execution_hash = canonical_sha256(execution_packet)
    sidecar_hash = canonical_sha256(
        {
            "execution_manager_packet": execution_packet,
            "broker_order_lifecycle_capture_v4_packet": packet,
        }
    )
    row["execution_manager_packet_hash_sha256"] = execution_hash
    row["execution_packet_sidecar_hash_sha256"] = sidecar_hash
    semantic_paths: list[list[str]] = []
    if "semantic_execution_manager_packet_sha256" in row:
        row["semantic_execution_manager_packet_sha256"] = execution_hash
        semantic_paths.append(
            [str(row_index), "semantic_execution_manager_packet_sha256"]
        )
    if "semantic_order_preimage_sha256" in row:
        row["semantic_order_preimage_sha256"] = sidecar_hash
        semantic_paths.append(
            [str(row_index), "semantic_order_preimage_sha256"]
        )
    prefix = str(row_index)
    return [
        [
            prefix,
            "broker_order_lifecycle_capture_v4_packet",
            "generated_at_utc",
        ],
        [
            prefix,
            "broker_order_lifecycle_capture_v4_packet",
            "pre_order_capture_contract",
            "execution_manager_packet_hash",
        ],
        [
            prefix,
            "broker_order_lifecycle_capture_v4_packet",
            "packet_hash_sha256",
        ],
        [prefix, "execution_manager_packet_hash_sha256"],
        [prefix, "execution_packet_sidecar_hash_sha256"],
        *semantic_paths,
    ]


def _normalize_outer_runtime_timestamp(
    row: dict[str, Any],
    *,
    row_index: int,
) -> list[list[str]]:
    packet = row.get("broker_order_lifecycle_capture_v4_packet")
    if not isinstance(packet, Mapping) or "generated_at_utc" not in packet:
        return []
    packet = copy.deepcopy(dict(packet))
    packet["generated_at_utc"] = _RUNTIME_ENVELOPE_SENTINEL
    row["broker_order_lifecycle_capture_v4_packet"] = packet
    return [
        [
            str(row_index),
            "broker_order_lifecycle_capture_v4_packet",
            "generated_at_utc",
        ]
    ]


def project_role_rows(
    role: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    provenance_preimages: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a value-free ordered semantic contract for one ledger role."""

    role = str(role)
    if role not in SUPPORTED_ROLES:
        raise SemanticParityError(f"semantic_role_not_allowlisted:{role}")
    projected_root = _CanonicalArrayHasher()
    normalized_paths: list[list[str]] = []
    for index, source_row in enumerate(rows):
        if not isinstance(source_row, Mapping):
            raise SemanticParityError(f"semantic_row_not_mapping:{role}:{index}")
        _validate_role_row(role, source_row, row_index=index)
        row = copy.deepcopy(dict(source_row))
        if (
            role == "order"
            and provenance_preimages is not None
            and row.get("selected_order_attempt_primary") is True
        ):
            normalized_paths.extend(
                _normalize_order_runtime_envelope(
                    row,
                    row_index=index,
                    provenance_preimages=provenance_preimages,
                    provenance_owners=None,
                )
            )
        elif role in {"order", "trade"}:
            normalized_paths.extend(
                _normalize_outer_runtime_timestamp(row, row_index=index)
            )
        projected_root.update(row)
    return {
        "schema": SEMANTIC_PARITY_SCHEMA,
        "role": role,
        "row_count": projected_root.count,
        "ordered_rows_root_sha256": projected_root.hexdigest(),
        "normalized_paths": normalized_paths,
        "economic_values_exposed": False,
    }


def _difference_paths(
    reference: Any,
    accelerated: Any,
    *,
    path: tuple[str, ...] = (),
) -> list[tuple[str, ...]]:
    if isinstance(reference, Mapping) and isinstance(accelerated, Mapping):
        differences: list[tuple[str, ...]] = []
        keys = sorted(set(reference) | set(accelerated), key=str)
        for key in keys:
            key_text = str(key)
            if key not in reference or key not in accelerated:
                differences.append((*path, key_text))
                continue
            differences.extend(
                _difference_paths(
                    reference[key],
                    accelerated[key],
                    path=(*path, key_text),
                )
            )
        return differences
    if isinstance(reference, list) and isinstance(accelerated, list):
        if len(reference) != len(accelerated):
            return [path]
        differences = []
        for index, (left, right) in enumerate(zip(reference, accelerated)):
            differences.extend(
                _difference_paths(left, right, path=(*path, str(index)))
            )
        return differences
    return [] if canonical_bytes(reference) == canonical_bytes(accelerated) else [path]


def _candidate_identity(
    row: Mapping[str, Any],
    *,
    role: str,
    index: int,
    side: str,
    required: bool,
) -> tuple[str, ...] | None:
    values = [row.get(field) for field in _CANDIDATE_CONTEXT_FIELDS]
    if all(type(value) is str and value.strip() for value in values):
        return tuple(str(value).strip() for value in values)
    if required:
        raise SemanticParityError(
            f"candidate_identity_incomplete:{role}:{index}:{side}"
        )
    return None


def _row_trading_day(
    row: Mapping[str, Any],
    *,
    role: str,
    index: int,
    side: str,
) -> date:
    explicit_day = row.get("trading_day")
    decision_time = row.get("decision_time_utc") or row.get("decision_time")
    try:
        parsed_explicit: date | None = None
        if explicit_day is not None:
            if type(explicit_day) is not str or len(explicit_day) != 10:
                raise ValueError
            parsed_explicit = date.fromisoformat(explicit_day)
            if parsed_explicit.isoformat() != explicit_day:
                raise ValueError
        parsed_decision: date | None = None
        if decision_time is not None:
            if type(decision_time) is not str or len(decision_time) < 10:
                raise ValueError
            parsed_decision = date.fromisoformat(decision_time[:10])
            if parsed_decision.isoformat() != decision_time[:10]:
                raise ValueError
        if parsed_explicit is None and parsed_decision is None:
            raise ValueError
        if (
            parsed_explicit is not None
            and parsed_decision is not None
            and parsed_explicit != parsed_decision
        ):
            raise ValueError
        resolved_day = parsed_explicit or parsed_decision
        assert resolved_day is not None
        return resolved_day
    except ValueError:
        raise SemanticParityError(
            f"candidate_trading_day_invalid:{role}:{index}:{side}"
        ) from None


def _first_nonblank_text(
    row: Mapping[str, Any],
    fields: Sequence[str],
) -> str | None:
    for field in fields:
        value = row.get(field)
        if type(value) is str and value.strip():
            return value.strip()
    return None


def _order_lifecycle_event_identity(
    row: Mapping[str, Any],
    *,
    index: int,
    side: str,
) -> tuple[str, str, str]:
    order_id = str(row.get("simulated_order_id") or "").strip()
    event_stage = _first_nonblank_text(
        row,
        (
            "order_event_stage",
            "order_snapshot_type",
            "event_type",
            "order_status",
        ),
    )
    event_time = _first_nonblank_text(
        row,
        (
            "event_time_utc",
            "fill_time_utc",
            "exit_time_utc",
            "close_time_utc",
            "expiry_utc",
            "decision_time_utc",
            "decision_time",
        ),
    )
    if not order_id or event_stage is None or event_time is None:
        raise SemanticParityError(
            f"order_lifecycle_event_identity_incomplete:{index}:{side}"
        )
    return order_id, event_stage, event_time


class _SideRelationalState:
    def __init__(
        self,
        side: str,
        *,
        candidate_identities: set[tuple[str, ...]] | None = None,
        campaign_days: set[date] | None = None,
    ) -> None:
        self.side = side
        self.candidate_identities = set(candidate_identities or ())
        self.campaign_days = set(campaign_days) if campaign_days is not None else None
        self.scorecard_candidate_fallback = candidate_identities is None
        self.order_identities: dict[str, tuple[str, ...]] = {}
        self.order_sidecar_owners: dict[
            str, tuple[str, tuple[str, ...], date]
        ] = {}
        self.order_lifecycle_event_identities: set[tuple[str, str, str]] = set()
        self.primary_order_sequences: dict[date, list[int]] = defaultdict(list)

    def observe(
        self,
        role: str,
        row: Mapping[str, Any],
        *,
        index: int,
    ) -> None:
        if self.campaign_days is not None:
            trading_day = _row_trading_day(
                row,
                role=role,
                index=index,
                side=self.side,
            )
            if trading_day not in self.campaign_days:
                raise SemanticParityError(
                    f"semantic_row_outside_campaign:{role}:{index}:{self.side}"
                )
        if role == "scorecard":
            identity = _candidate_identity(
                row,
                role=role,
                index=index,
                side=self.side,
                required=False,
            )
            if self.scorecard_candidate_fallback:
                if identity is not None:
                    self.candidate_identities.add(identity)
            elif identity is not None and identity not in self.candidate_identities:
                raise SemanticParityError(
                    f"dangling_candidate_reference:{role}:{index}:{self.side}"
                )
            return
        identity = _candidate_identity(
            row,
            role=role,
            index=index,
            side=self.side,
            required=True,
        )
        assert identity is not None
        if identity not in self.candidate_identities:
            raise SemanticParityError(
                f"dangling_candidate_reference:{role}:{index}:{self.side}"
            )
        if role == "missed":
            return
        if role == "order":
            event_identity = _order_lifecycle_event_identity(
                row,
                index=index,
                side=self.side,
            )
            if event_identity in self.order_lifecycle_event_identities:
                raise SemanticParityError(
                    f"duplicate_order_lifecycle_event:{index}:{self.side}"
                )
            self.order_lifecycle_event_identities.add(event_identity)
            order_id = str(row.get("simulated_order_id") or "").strip()
            if not order_id:
                raise SemanticParityError(
                    f"order_identity_incomplete:order:{index}:{self.side}"
                )
            previous = self.order_identities.get(order_id)
            if previous is not None and previous != identity:
                raise SemanticParityError(
                    f"repeated_order_identity_mismatch:{order_id}:{self.side}"
                )
            self.order_identities[order_id] = identity
            primary_marker = row.get("selected_order_attempt_primary")
            if primary_marker is not None and type(primary_marker) is not bool:
                raise SemanticParityError(
                    f"semantic_order_sequence_mismatch:{self.side}"
                )
            if primary_marker is True:
                sequence = row.get("selected_order_sequence")
                if type(sequence) is not int or sequence < 1:
                    raise SemanticParityError(
                        f"semantic_order_sequence_mismatch:{self.side}"
                    )
                trading_day = _row_trading_day(
                    row,
                    role=role,
                    index=index,
                    side=self.side,
                )
                self.primary_order_sequences[trading_day].append(sequence)
            sidecar_id = str(
                row.get("execution_packet_sidecar_id") or ""
            ).strip()
            if sidecar_id:
                owner = (
                    order_id,
                    identity,
                    _row_trading_day(
                        row,
                        role=role,
                        index=index,
                        side=self.side,
                    ),
                )
                previous_owner = self.order_sidecar_owners.get(sidecar_id)
                if previous_owner is not None and previous_owner != owner:
                    raise SemanticParityError(
                        "sidecar_reused_by_distinct_order:"
                        f"{sidecar_id}:{self.side}"
                    )
                expected_sidecar_id = canonical_sha256(
                    {
                        "campaign": str(row.get("campaign") or ""),
                        "candidate_id": str(row.get("candidate_id") or ""),
                        "simulated_order_id": order_id,
                        "type": "execution_manager_v4",
                    }
                )
                if sidecar_id != expected_sidecar_id:
                    raise SemanticParityError(
                        f"semantic_sidecar_identity_mismatch:{index}:{self.side}"
                    )
                self.order_sidecar_owners[sidecar_id] = owner
            return
        order_id = str(row.get("simulated_order_id") or "").strip()
        matching_identity = self.order_identities.get(order_id)
        if not order_id or matching_identity is None:
            raise SemanticParityError(
                f"dangling_order_reference:{role}:{index}:{self.side}"
            )
        if matching_identity != identity:
            raise SemanticParityError(
                f"order_candidate_reference_mismatch:{role}:{index}:{self.side}"
            )


def _compare_candidate_streams(
    reference_rows: Iterable[Mapping[str, Any]],
    accelerated_rows: Iterable[Mapping[str, Any]],
    *,
    campaign_days: set[date] | None = None,
) -> dict[str, Any]:
    sentinel = object()
    reference_root = _CanonicalArrayHasher()
    accelerated_root = _CanonicalArrayHasher()
    reference_identities: set[tuple[str, ...]] = set()
    accelerated_identities: set[tuple[str, ...]] = set()
    reference_instance_identities: dict[tuple[str, str, str], tuple[str, ...]] = {}
    accelerated_instance_identities: dict[
        tuple[str, str, str], tuple[str, ...]
    ] = {}
    for index, pair in enumerate(
        zip_longest(reference_rows, accelerated_rows, fillvalue=sentinel)
    ):
        reference_row, accelerated_row = pair
        if reference_row is sentinel or accelerated_row is sentinel:
            raise SemanticParityError("semantic_candidate_row_count_mismatch")
        if not isinstance(reference_row, Mapping) or not isinstance(
            accelerated_row, Mapping
        ):
            raise SemanticParityError(
                f"semantic_candidate_row_not_mapping:{index}"
            )
        for side, row, identities, instance_identities in (
            (
                "reference",
                reference_row,
                reference_identities,
                reference_instance_identities,
            ),
            (
                "accelerated",
                accelerated_row,
                accelerated_identities,
                accelerated_instance_identities,
            ),
        ):
            row_type = row.get("row_type")
            schema_valid = bool(
                row_type == "semantic_candidate"
                and row.get("schema") == _SEMANTIC_CANDIDATE_SCHEMA
                and row.get("row_provenance_schema")
                == _SEMANTIC_CANDIDATE_PROVENANCE_SCHEMA
            ) or bool(
                row_type == "candidate_index"
                and row.get("candidate_index_schema")
                == _COMPACT_CANDIDATE_INDEX_SCHEMA
                and row.get("row_provenance_schema") == _ROW_PROVENANCE_SCHEMA
            ) or bool(
                row_type == "candidate"
                and row.get("row_provenance_schema") == _ROW_PROVENANCE_SCHEMA
            )
            if row_type not in _CANDIDATE_ROW_TYPES or not schema_valid:
                raise SemanticParityError(
                    f"semantic_candidate_row_schema_invalid:{index}:{side}"
                )
            identity = _candidate_identity(
                row,
                role="candidate",
                index=index,
                side=side,
                required=True,
            )
            assert identity is not None
            if campaign_days is not None:
                candidate_day = _row_trading_day(
                    row,
                    role="candidate",
                    index=index,
                    side=side,
                )
                if candidate_day not in campaign_days:
                    raise SemanticParityError(
                        f"semantic_row_outside_campaign:candidate:{index}:{side}"
                    )
            instance_key = (identity[0], identity[1], identity[4])
            previous_identity = instance_identities.get(instance_key)
            if previous_identity is not None:
                error = (
                    "duplicate_candidate_identity"
                    if previous_identity == identity
                    else "candidate_identity_collision"
                )
                raise SemanticParityError(f"{error}:{index}:{side}")
            if identity in identities:
                raise SemanticParityError(
                    f"duplicate_candidate_identity:{index}:{side}"
                )
            instance_identities[instance_key] = identity
            identities.add(identity)
        if canonical_bytes(reference_row) != canonical_bytes(accelerated_row):
            raise SemanticParityError(
                f"semantic_candidate_row_mismatch:{index}"
            )
        reference_root.update(reference_row)
        accelerated_root.update(accelerated_row)
    if reference_root.hexdigest() != accelerated_root.hexdigest():
        raise SemanticParityError("semantic_candidate_projection_mismatch")
    return {
        "reference_identities": reference_identities,
        "accelerated_identities": accelerated_identities,
        "reference_partition": {
            "row_count": reference_root.count,
            "ordered_rows_root_sha256": reference_root.hexdigest(),
        },
        "accelerated_partition": {
            "row_count": accelerated_root.count,
            "ordered_rows_root_sha256": accelerated_root.hexdigest(),
        },
    }


def _project_single_row(
    role: str,
    row: Mapping[str, Any],
    *,
    row_index: int,
    provenance_preimages: Mapping[str, Mapping[str, Any]] | None,
    provenance_owners: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[dict[str, Any], list[list[str]]]:
    _validate_role_row(role, row, row_index=row_index)
    projected = copy.deepcopy(dict(row))
    normalized_paths: list[list[str]] = []
    if (
        role == "order"
        and provenance_preimages is not None
        and row.get("selected_order_attempt_primary") is True
    ):
        normalized_paths.extend(
            _normalize_order_runtime_envelope(
                projected,
                row_index=row_index,
                provenance_preimages=provenance_preimages,
                provenance_owners=provenance_owners,
            )
        )
    elif role in {"order", "trade"}:
        normalized_paths.extend(
            _normalize_outer_runtime_timestamp(
                projected,
                row_index=row_index,
            )
        )
    return projected, normalized_paths


def _compare_stream_core(
    reference: Mapping[str, Iterable[Mapping[str, Any]]],
    accelerated: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    reference_provenance_preimages: (
        Mapping[str, Mapping[str, Any]] | None
    ),
    accelerated_provenance_preimages: (
        Mapping[str, Mapping[str, Any]] | None
    ),
    reference_provenance_owners: (
        Mapping[str, Mapping[str, Any]] | None
    ) = None,
    accelerated_provenance_owners: (
        Mapping[str, Mapping[str, Any]] | None
    ) = None,
    reference_candidate_identities: set[tuple[str, ...]] | None = None,
    accelerated_candidate_identities: set[tuple[str, ...]] | None = None,
    campaign_days: set[date] | None = None,
) -> dict[str, Any]:
    _validate_role_inventory(reference, side="reference")
    _validate_role_inventory(accelerated, side="accelerated")
    sentinel = object()
    reference_relations = _SideRelationalState(
        "reference",
        candidate_identities=reference_candidate_identities,
        campaign_days=campaign_days,
    )
    accelerated_relations = _SideRelationalState(
        "accelerated",
        candidate_identities=accelerated_candidate_identities,
        campaign_days=campaign_days,
    )
    role_receipts: list[dict[str, Any]] = []
    reference_partitions: dict[str, dict[str, Any]] = {}
    accelerated_partitions: dict[str, dict[str, Any]] = {}
    outer_timestamp_only = {
        (
            "broker_order_lifecycle_capture_v4_packet",
            "generated_at_utc",
        )
    }
    base_order_runtime_closure = {
        *outer_timestamp_only,
        (
            "broker_order_lifecycle_capture_v4_packet",
            "pre_order_capture_contract",
            "execution_manager_packet_hash",
        ),
        (
            "broker_order_lifecycle_capture_v4_packet",
            "packet_hash_sha256",
        ),
    }
    full_order_runtime_closure = {
        *base_order_runtime_closure,
        ("execution_manager_packet_hash_sha256",),
        ("execution_packet_sidecar_hash_sha256",),
    }
    reference_streams = {
        role: iter(reference[role]) for role in SUPPORTED_ROLES
    }
    accelerated_streams = {
        role: iter(accelerated[role]) for role in SUPPORTED_ROLES
    }
    for role in SUPPORTED_ROLES:
        reference_projected_root = _CanonicalArrayHasher()
        accelerated_projected_root = _CanonicalArrayHasher()
        reference_raw_root = _CanonicalArrayHasher()
        accelerated_raw_root = _CanonicalArrayHasher()
        reference_normalized_path_count = 0
        accelerated_normalized_path_count = 0
        pairs = zip_longest(
            reference_streams[role],
            accelerated_streams[role],
            fillvalue=sentinel,
        )
        for index, pair in enumerate(pairs):
            reference_row, accelerated_row = pair
            if reference_row is sentinel or accelerated_row is sentinel:
                raise SemanticParityError(
                    f"semantic_row_count_mismatch:{role}"
                )
            if not isinstance(reference_row, Mapping) or not isinstance(
                accelerated_row, Mapping
            ):
                raise SemanticParityError(
                    f"semantic_row_not_mapping:{role}:{index}"
                )
            # A non-finite economic value is never a legitimate accepted output:
            # all 28 sealing encoders in this package refuse it. This comparator
            # used to serialise it with allow_nan=True, so two rows both holding
            # NaN compared byte-EQUAL and parity passed. The shared encoder now
            # raises, and _difference_paths bottoms out in it — so convert that
            # to the comparator's own error type rather than pre-walking every
            # row, which cost ~15% of comparison time for a redundant check.
            try:
                differences = set(
                    _difference_paths(reference_row, accelerated_row)
                )
            except NonFiniteCanonicalValueError as exc:
                raise SemanticParityError(
                    f"semantic_row_non_finite:{role}:{index}:{exc}"
                ) from exc
            if (
                role == "order"
                and differences != outer_timestamp_only
                and differences & full_order_runtime_closure
                and (
                    reference_provenance_preimages is None
                    or accelerated_provenance_preimages is None
                )
            ):
                raise SemanticParityError(
                    f"semantic_preimage_missing:order:{index}"
                )
            reference_projected, reference_paths = _project_single_row(
                role,
                reference_row,
                row_index=index,
                provenance_preimages=(
                    reference_provenance_preimages
                    if role == "order"
                    else None
                ),
                provenance_owners=(
                    reference_provenance_owners
                    if role == "order"
                    else None
                ),
            )
            accelerated_projected, accelerated_paths = _project_single_row(
                role,
                accelerated_row,
                row_index=index,
                provenance_preimages=(
                    accelerated_provenance_preimages
                    if role == "order"
                    else None
                ),
                provenance_owners=(
                    accelerated_provenance_owners
                    if role == "order"
                    else None
                ),
            )
            if differences:
                allowed = False
                if role in {"order", "trade"} and differences == outer_timestamp_only:
                    allowed = True
                elif (
                    role == "order"
                    and reference_provenance_preimages is not None
                    and accelerated_provenance_preimages is not None
                    and differences <= full_order_runtime_closure
                ):
                    allowed = True
                if not allowed:
                    if role == "order" and differences & base_order_runtime_closure:
                        raise SemanticParityError(
                            f"runtime_envelope_difference_incomplete:{role}:{index}"
                        )
                    raise SemanticParityError(
                        f"semantic_row_mismatch:{role}:{index}"
                    )
            if (
                canonical_bytes(reference_projected)
                != canonical_bytes(accelerated_projected)
                or reference_paths != accelerated_paths
            ):
                raise SemanticParityError(
                    f"semantic_projection_mismatch:{role}"
                )
            reference_relations.observe(
                role,
                reference_row,
                index=index,
            )
            accelerated_relations.observe(
                role,
                accelerated_row,
                index=index,
            )
            reference_projected_root.update(reference_projected)
            accelerated_projected_root.update(accelerated_projected)
            reference_raw_root.update(reference_row)
            accelerated_raw_root.update(accelerated_row)
            reference_normalized_path_count += len(reference_paths)
            accelerated_normalized_path_count += len(accelerated_paths)
        if (
            reference_projected_root.count != accelerated_projected_root.count
            or reference_projected_root.hexdigest()
            != accelerated_projected_root.hexdigest()
            or reference_normalized_path_count
            != accelerated_normalized_path_count
        ):
            raise SemanticParityError(f"semantic_projection_mismatch:{role}")
        role_receipts.append(
            {
                "role": role,
                "row_count": reference_projected_root.count,
                "ordered_rows_root_sha256": (
                    reference_projected_root.hexdigest()
                ),
                "normalized_path_count": reference_normalized_path_count,
            }
        )
        if role in {"missed", "order", "trade"}:
            reference_partitions[role] = {
                "row_count": reference_raw_root.count,
                "ordered_rows_root_sha256": reference_raw_root.hexdigest(),
            }
            accelerated_partitions[role] = {
                "row_count": accelerated_raw_root.count,
                "ordered_rows_root_sha256": accelerated_raw_root.hexdigest(),
            }
    return {
        "roles": role_receipts,
        "reference_partitions": reference_partitions,
        "accelerated_partitions": accelerated_partitions,
        "reference_order_sidecar_owners": (
            reference_relations.order_sidecar_owners
        ),
        "accelerated_order_sidecar_owners": (
            accelerated_relations.order_sidecar_owners
        ),
        "reference_primary_order_sequences": dict(
            reference_relations.primary_order_sequences
        ),
        "accelerated_primary_order_sequences": dict(
            accelerated_relations.primary_order_sequences
        ),
    }


def _proof_self_root(row: Mapping[str, Any]) -> str:
    projection = dict(row)
    projection.pop("proof_root_sha256", None)
    return canonical_sha256(projection)


def _semantic_proof_inventory_error(side: str) -> SemanticParityError:
    return SemanticParityError(f"semantic_proof_inventory_invalid:{side}")


def _parse_semantic_proofs(
    rows: Iterable[Mapping[str, Any]],
    *,
    side: str,
    expected_campaign_days: tuple[date, ...] | None,
) -> dict[str, Any]:
    proof_roots: list[str] = []
    states: list[dict[str, Any]] = []
    terminal_partition: dict[str, Any] | None = None
    terminal_partition_day: date | None = None
    preimages: dict[str, dict[str, Any]] = {}
    sidecar_days: dict[str, date] = {}
    sidecar_owners: dict[str, dict[str, Any]] = {}
    previous_rank = -1
    ranks = {
        "state_checkpoint": 0,
        "terminal_partition": 1,
        "order_sidecar_preimage": 2,
    }
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise _semantic_proof_inventory_error(side)
        proof_type = str(row.get("proof_type") or "")
        if (
            row.get("schema") != SEMANTIC_PROOF_ROW_SCHEMA
            or type(row.get("proof_sequence")) is not int
            or row.get("proof_sequence") != index
            or row.get("proof_root_sha256") != _proof_self_root(row)
            or proof_type not in ranks
            or ranks[proof_type] < previous_rank
        ):
            raise _semantic_proof_inventory_error(side)
        previous_rank = ranks[proof_type]
        proof_roots.append(str(row["proof_root_sha256"]))
        if proof_type == "state_checkpoint":
            state_projection = row.get("state_projection")
            required_state_fields = {
                "schema",
                "account_root_sha256",
                "broker_root_sha256",
                "event_queue_root_sha256",
                "reservation_root_sha256",
                "selected_order_sequence",
            }
            if (
                set(row)
                != {
                    "schema",
                    "proof_sequence",
                    "proof_type",
                    "trading_day",
                    "boundary",
                    "state_projection",
                    "state_root_sha256",
                    "proof_root_sha256",
                }
                or not isinstance(state_projection, Mapping)
                or set(state_projection) != required_state_fields
                or state_projection.get("schema")
                != "gtos.replay_acceleration.pre_day_state.v1"
                or row.get("state_root_sha256")
                != canonical_sha256(state_projection)
                or row.get("boundary") not in {"pre_day", "post_day"}
                or type(
                    state_projection.get("selected_order_sequence")
                ) is not int
                or any(
                    not _is_sha256(state_projection.get(field))
                    for field in (
                        "account_root_sha256",
                        "broker_root_sha256",
                        "event_queue_root_sha256",
                        "reservation_root_sha256",
                    )
                )
            ):
                raise _semantic_proof_inventory_error(side)
            trading_day = _exact_day(row.get("trading_day"), side=side)
            states.append(
                {
                    "day": trading_day,
                    "boundary": str(row["boundary"]),
                    "state_root_sha256": str(row["state_root_sha256"]),
                    "selected_order_sequence": state_projection[
                        "selected_order_sequence"
                    ],
                }
            )
            continue
        if proof_type == "terminal_partition":
            partitions = row.get("partitions")
            if (
                terminal_partition is not None
                or set(row)
                != {
                    "schema",
                    "proof_sequence",
                    "proof_type",
                    "trading_day",
                    "partitions",
                    "proof_root_sha256",
                }
                or not isinstance(partitions, Mapping)
                or set(partitions) != {"candidate", "missed", "order", "trade"}
            ):
                raise _semantic_proof_inventory_error(side)
            validated_partitions: dict[str, dict[str, Any]] = {}
            for role in ("candidate", "missed", "order", "trade"):
                contract = partitions.get(role)
                if (
                    not isinstance(contract, Mapping)
                    or set(contract)
                    != {"row_count", "ordered_rows_root_sha256"}
                    or type(contract.get("row_count")) is not int
                    or int(contract["row_count"]) < 0
                    or not _is_sha256(
                        contract.get("ordered_rows_root_sha256")
                    )
                ):
                    raise _semantic_proof_inventory_error(side)
                validated_partitions[role] = dict(contract)
            terminal_partition_day = _exact_day(
                row.get("trading_day"),
                side=side,
            )
            terminal_partition = validated_partitions
            continue
        if set(row) != {
            "schema",
            "proof_sequence",
            "proof_type",
            "trading_day",
            "execution_packet_sidecar_id",
            "sidecar_payload_canonical_json",
            "sidecar_payload_sha256",
            "owner",
            "proof_root_sha256",
        }:
            raise _semantic_proof_inventory_error(side)
        sidecar_id = str(
            row.get("execution_packet_sidecar_id") or ""
        ).strip()
        payload_text = row.get("sidecar_payload_canonical_json")
        owner = row.get("owner")
        if (
            not sidecar_id
            or sidecar_id in preimages
            or not isinstance(payload_text, str)
            or not isinstance(owner, Mapping)
            or set(owner) != _SIDECAR_OWNER_FIELDS
        ):
            raise _semantic_proof_inventory_error(side)
        try:
            payload_bytes = payload_text.encode("ascii")
            payload = json.loads(payload_bytes)
        except (UnicodeError, json.JSONDecodeError):
            raise _semantic_proof_inventory_error(side) from None
        payload_root = hashlib.sha256(payload_bytes).hexdigest()
        if (
            not isinstance(payload, Mapping)
            or canonical_bytes(payload) != payload_bytes
            or row.get("sidecar_payload_sha256") != payload_root
            or owner.get("payload_root_sha256") != payload_root
            or any(
                type(owner.get(field)) is not str
                or not str(owner.get(field)).strip()
                for field in _SIDECAR_OWNER_FIELDS
                if field != "payload_root_sha256"
            )
        ):
            raise _semantic_proof_inventory_error(side)
        sidecar_days[sidecar_id] = _exact_day(
            row.get("trading_day"),
            side=side,
        )
        preimages[sidecar_id] = dict(payload)
        sidecar_owners[sidecar_id] = dict(owner)
    if (
        terminal_partition is None
        or not states
        or len(states) % 2
        or [item["boundary"] for item in states]
        != [boundary for _ in range(len(states) // 2) for boundary in ("pre_day", "post_day")]
    ):
        raise _semantic_proof_inventory_error(side)
    days = [states[index]["day"] for index in range(0, len(states), 2)]
    if any(
        states[index]["day"] != states[index + 1]["day"]
        for index in range(0, len(states), 2)
    ):
        raise _semantic_proof_inventory_error(side)
    if expected_campaign_days is not None and tuple(days) != expected_campaign_days:
        raise _semantic_proof_inventory_error(side)
    day_set = set(days)
    if (
        len(day_set) != len(days)
        or terminal_partition_day != days[-1]
        or any(
            sidecar_day not in day_set for sidecar_day in sidecar_days.values()
        )
    ):
        raise _semantic_proof_inventory_error(side)
    for day_index, day_value in enumerate(days):
        pre_state = states[day_index * 2]
        post_state = states[day_index * 2 + 1]
        if (
            pre_state["selected_order_sequence"]
            > post_state["selected_order_sequence"]
        ):
            raise SemanticParityError(
                f"semantic_order_sequence_mismatch:{side}"
            )
        if day_index == 0:
            continue
        previous_post = states[(day_index - 1) * 2 + 1]
        current_pre = pre_state
        if (
            previous_post["state_root_sha256"]
            != current_pre["state_root_sha256"]
            or previous_post["selected_order_sequence"]
            != current_pre["selected_order_sequence"]
        ):
            raise SemanticParityError(
                f"semantic_state_chain_mismatch:{side}:{day_value.isoformat()}"
            )
    return {
        "states": states,
        "terminal_partition": terminal_partition,
        "preimages": preimages,
        "sidecar_days": sidecar_days,
        "sidecar_owners": sidecar_owners,
        "campaign_days": days,
        "proof_row_count": len(proof_roots),
        "proof_rows_root_sha256": canonical_sha256(proof_roots),
    }


def _compare_proof_states(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
) -> None:
    reference_states = reference["states"]
    accelerated_states = accelerated["states"]
    if not reference_states or not accelerated_states:
        raise SemanticParityError("semantic_pre_day_state_missing")
    if (
        reference_states[0]["state_root_sha256"]
        != accelerated_states[0]["state_root_sha256"]
    ):
        raise SemanticParityError("semantic_pre_day_state_mismatch")
    if len(reference_states) != len(accelerated_states):
        raise SemanticParityError("semantic_state_inventory_mismatch")
    for reference_state, accelerated_state in zip(
        reference_states,
        accelerated_states,
        strict=True,
    ):
        if (
            reference_state["day"] != accelerated_state["day"]
            or reference_state["boundary"] != accelerated_state["boundary"]
            or reference_state["state_root_sha256"]
            != accelerated_state["state_root_sha256"]
            or reference_state["selected_order_sequence"]
            != accelerated_state["selected_order_sequence"]
        ):
            raise SemanticParityError("semantic_state_checkpoint_mismatch")


def _expected_campaign_day_tuple(
    values: Sequence[str] | None,
) -> tuple[date, ...] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)) or not values:
        raise SemanticParityError("semantic_campaign_days_invalid")
    days: list[date] = []
    for value in values:
        try:
            days.append(_exact_day(value, side="campaign"))
        except SemanticParityError:
            raise SemanticParityError("semantic_campaign_days_invalid") from None
    if days != sorted(set(days)):
        raise SemanticParityError("semantic_campaign_days_invalid")
    return tuple(days)


def _reconcile_selected_order_sequences(
    proofs: Mapping[str, Any],
    observed: Mapping[date, list[int]],
    *,
    side: str,
) -> None:
    states = proofs["states"]
    campaign_days = proofs["campaign_days"]
    if any(day not in set(campaign_days) for day in observed):
        raise SemanticParityError(f"semantic_order_sequence_mismatch:{side}")
    prior_sequence: int | None = None
    for day_index, day_value in enumerate(campaign_days):
        pre_sequence = states[day_index * 2]["selected_order_sequence"]
        post_sequence = states[day_index * 2 + 1]["selected_order_sequence"]
        if prior_sequence is not None and pre_sequence != prior_sequence:
            raise SemanticParityError(
                f"semantic_order_sequence_mismatch:{side}"
            )
        expected = list(range(pre_sequence + 1, post_sequence + 1))
        actual = list(observed.get(day_value, ()))
        if actual != expected or len(actual) != len(set(actual)):
            raise SemanticParityError(
                f"semantic_order_sequence_mismatch:{side}"
            )
        prior_sequence = post_sequence


def compare_semantic_streams(
    reference: Mapping[str, Iterable[Mapping[str, Any]]],
    accelerated: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    reference_proof_rows: Iterable[Mapping[str, Any]],
    accelerated_proof_rows: Iterable[Mapping[str, Any]],
    reference_candidate_rows: Iterable[Mapping[str, Any]] | None = None,
    accelerated_candidate_rows: Iterable[Mapping[str, Any]] | None = None,
    expected_campaign_days: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run a one-pass, proof-bound diagnostic without acceptance authority."""

    _validate_role_inventory(reference, side="reference")
    _validate_role_inventory(accelerated, side="accelerated")
    expected_days = _expected_campaign_day_tuple(expected_campaign_days)
    reference_proofs = _parse_semantic_proofs(
        reference_proof_rows,
        side="reference",
        expected_campaign_days=expected_days,
    )
    accelerated_proofs = _parse_semantic_proofs(
        accelerated_proof_rows,
        side="accelerated",
        expected_campaign_days=expected_days,
    )
    _compare_proof_states(reference_proofs, accelerated_proofs)
    candidate_comparison: dict[str, Any] | None = None
    if (
        reference_candidate_rows is None
        and accelerated_candidate_rows is None
    ):
        reference_candidate_identities = None
        accelerated_candidate_identities = None
    elif (
        reference_candidate_rows is None
        or accelerated_candidate_rows is None
    ):
        raise SemanticParityError("semantic_candidate_stream_pair_incomplete")
    else:
        candidate_comparison = _compare_candidate_streams(
            reference_candidate_rows,
            accelerated_candidate_rows,
            campaign_days=set(expected_days) if expected_days is not None else None,
        )
        reference_candidate_identities = candidate_comparison[
            "reference_identities"
        ]
        accelerated_candidate_identities = candidate_comparison[
            "accelerated_identities"
        ]
    comparison = _compare_stream_core(
        reference,
        accelerated,
        reference_provenance_preimages=reference_proofs["preimages"],
        accelerated_provenance_preimages=accelerated_proofs["preimages"],
        reference_provenance_owners=reference_proofs["sidecar_owners"],
        accelerated_provenance_owners=accelerated_proofs["sidecar_owners"],
        reference_candidate_identities=reference_candidate_identities,
        accelerated_candidate_identities=accelerated_candidate_identities,
        campaign_days=set(expected_days) if expected_days is not None else None,
    )
    _reconcile_selected_order_sequences(
        reference_proofs,
        comparison["reference_primary_order_sequences"],
        side="reference",
    )
    _reconcile_selected_order_sequences(
        accelerated_proofs,
        comparison["accelerated_primary_order_sequences"],
        side="accelerated",
    )
    persisted_partition_roles = ("missed", "order", "trade")
    reference_persisted_partitions = {
        role: reference_proofs["terminal_partition"][role]
        for role in persisted_partition_roles
    }
    accelerated_persisted_partitions = {
        role: accelerated_proofs["terminal_partition"][role]
        for role in persisted_partition_roles
    }
    if comparison["reference_partitions"] != reference_persisted_partitions:
        raise SemanticParityError(
            "semantic_terminal_partition_mismatch:reference"
        )
    if comparison["accelerated_partitions"] != accelerated_persisted_partitions:
        raise SemanticParityError(
            "semantic_terminal_partition_mismatch:accelerated"
        )
    reference_candidate_partition = reference_proofs[
        "terminal_partition"
    ]["candidate"]
    accelerated_candidate_partition = accelerated_proofs[
        "terminal_partition"
    ]["candidate"]
    if candidate_comparison is None:
        if reference_candidate_partition != accelerated_candidate_partition:
            raise SemanticParityError(
                "semantic_candidate_partition_declaration_mismatch"
            )
    else:
        if (
            candidate_comparison["reference_partition"]
            != reference_candidate_partition
        ):
            raise SemanticParityError(
                "semantic_candidate_partition_mismatch:reference"
            )
        if (
            candidate_comparison["accelerated_partition"]
            != accelerated_candidate_partition
        ):
            raise SemanticParityError(
                "semantic_candidate_partition_mismatch:accelerated"
            )
    for side, owners, proofs in (
        (
            "reference",
            comparison["reference_order_sidecar_owners"],
            reference_proofs,
        ),
        (
            "accelerated",
            comparison["accelerated_order_sidecar_owners"],
            accelerated_proofs,
        ),
    ):
        if (
            set(owners) != set(proofs["preimages"])
            or set(owners) != set(proofs["sidecar_days"])
            or set(owners) != set(proofs["sidecar_owners"])
        ):
            raise SemanticParityError(
                f"semantic_sidecar_inventory_mismatch:{side}"
            )
        for sidecar_id, owner in owners.items():
            if owner[2] != proofs["sidecar_days"][sidecar_id]:
                raise SemanticParityError(
                    f"semantic_sidecar_day_mismatch:{side}:{sidecar_id}"
                )
    role_receipts = comparison["roles"]
    diagnostic_complete = bool(
        candidate_comparison is not None and expected_days is not None
    )
    receipt_core = {
        "schema": SEMANTIC_PARITY_SCHEMA,
        "status": (
            SEMANTIC_DIAGNOSTIC_STATUS
            if diagnostic_complete
            else SEMANTIC_INCOMPLETE_STATUS
        ),
        "parity_status": (
            "PASS_DIAGNOSTIC_ONLY"
            if diagnostic_complete
            else "INCOMPLETE_DIAGNOSTIC_ONLY"
        ),
        "acceptance_authorized": False,
        "diagnostic_complete": diagnostic_complete,
        "campaign_calendar_bound": expected_days is not None,
        "roles": role_receipts,
        "roles_root_sha256": canonical_sha256(role_receipts),
        "reference_proof_rows_root_sha256": reference_proofs[
            "proof_rows_root_sha256"
        ],
        "accelerated_proof_rows_root_sha256": accelerated_proofs[
            "proof_rows_root_sha256"
        ],
        "first_pre_day_state_root_sha256": reference_proofs["states"][0][
            "state_root_sha256"
        ],
        "candidate_partition_declared_root_sha256": reference_proofs[
            "terminal_partition"
        ]["candidate"]["ordered_rows_root_sha256"],
        "candidate_partition_recomputed": candidate_comparison is not None,
        "campaign_days_root_sha256": canonical_sha256(
            [day.isoformat() for day in reference_proofs["campaign_days"]]
        ),
        "sidecar_owner_bindings_verified": True,
        "selected_order_sequence_reconciled": True,
        "persisted_terminal_partitions_recomputed": True,
        "economic_values_exposed": False,
    }
    return {
        **receipt_core,
        "diagnostic_root_sha256": canonical_sha256(receipt_core),
    }


def _validate_role_inventory(
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    side: str,
) -> None:
    roles = tuple(str(role) for role in ledgers)
    if set(roles) != set(SUPPORTED_ROLES):
        raise SemanticParityError(f"semantic_role_inventory_mismatch:{side}")


def compare_semantic_ledgers(
    reference: Mapping[str, Iterable[Mapping[str, Any]]],
    accelerated: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    reference_provenance_preimages: (
        Mapping[str, Mapping[str, Any]] | None
    ) = None,
    accelerated_provenance_preimages: (
        Mapping[str, Mapping[str, Any]] | None
    ) = None,
) -> dict[str, Any]:
    """Compare ordered replay ledgers in one pass per supplied role stream."""

    comparison = _compare_stream_core(
        reference,
        accelerated,
        reference_provenance_preimages=reference_provenance_preimages,
        accelerated_provenance_preimages=accelerated_provenance_preimages,
    )
    role_receipts = comparison["roles"]
    return {
        "schema": SEMANTIC_PARITY_SCHEMA,
        "status": SEMANTIC_INCOMPLETE_STATUS,
        "parity_status": "INCOMPLETE_DIAGNOSTIC_ONLY",
        "acceptance_authorized": False,
        "diagnostic_complete": False,
        "roles": role_receipts,
        "roles_root_sha256": canonical_sha256(role_receipts),
        "economic_values_exposed": False,
    }


__all__ = [
    "SEMANTIC_DIAGNOSTIC_STATUS",
    "SEMANTIC_INCOMPLETE_STATUS",
    "SEMANTIC_PARITY_SCHEMA",
    "SEMANTIC_PROOF_ROW_SCHEMA",
    "SUPPORTED_ROLES",
    "SemanticParityError",
    "canonical_bytes",
    "canonical_sha256",
    "compare_semantic_ledgers",
    "compare_semantic_streams",
    "project_role_rows",
]
