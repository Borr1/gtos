"""Shared guards for the offline Wave 21 full-flow truth path.

The mode is deliberately explicit and default-off.  The probability guard is
a refusal, not a calibration model: an action-support score whose producer
disclaims outcome calibration cannot supply probability or EV authority.

The one licensed exception is a validated geometry-bound outcome calibration
packet (``src.research_infra.geometry_bound_outcome_model``): an immutable,
hash-sealed two-stage Jeffreys packet bound to the candidate's FINAL
post-router target/stop geometry contract hash.  Acceptance requires the
caller to attest the model artifact sha256 -- a packet can never self-declare
economic authority -- and any missing or failing atom refuses fail-closed.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from src.research_infra.geometry_bound_outcome_model import (
    PACKET_SCHEMA as GEOMETRY_BOUND_OUTCOME_PACKET_SCHEMA,
    REASON_MODEL_VERSION_UNSUPPORTED as _REASON_MODEL_VERSION_UNSUPPORTED,
    SUPPORTED_MODEL_VERSION as GEOMETRY_BOUND_OUTCOME_MODEL_VERSION,
    validate_geometry_bound_outcome_calibration_packet,
)


WAVE21_FULL_FLOW_TRUTH_MODE_KEY = "wave21_full_flow_truth_mode_enabled"
NO_OUTCOME_CALIBRATION_CLAIM = (
    "runtime_reliability_prior_no_outcome_calibration_claim"
)
PROBABILITY_TRUTH_STATUS = "NOT_EVALUABLE_NO_GEOMETRY_BOUND_OUTCOME_MODEL"
PROBABILITY_TRUTH_SOURCE_REQUIRED_FIELD = "geometry_bound_outcome_calibration"
GEOMETRY_BOUND_OUTCOME_CALIBRATION_KEY = "geometry_bound_outcome_calibration"
GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS = (
    "EVALUATED_GEOMETRY_BOUND_OUTCOME_CALIBRATION"
)
GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON = (
    "geometry_bound_outcome_calibration_all_atoms_validated"
)

_FALSE_AUTHORITY_KEYS = frozenset(
    {
        "ev",
        "ev_r",
        "expectancy",
        "executable_expected_value",
        "p",
        "probability",
        "probability_pct",
        "probability_raw",
        "selection_score",
    }
)
_NO_OUTCOME_THESIS_DIAGNOSTIC_KEYS = frozenset(
    {
        "action",
        "direction",
        "disagreement_state",
        "evidence_class",
        "missing_source_penalty",
        "opposition",
        "source_completeness",
        "source_ids",
        "support",
        "uncertainty",
    }
)
_PROBABILITY_DEBATE_DIAGNOSTIC_KEYS = frozenset(
    {
        "artifact_paths",
        "broker_runtime_change_status",
        "enabled",
        "outcome_result_rows_status",
        "schema_version",
        "source_summary",
        "theses",
        "validation_result_status",
    }
)


def wave21_full_flow_truth_mode_enabled(config: Mapping[str, Any] | None) -> bool:
    """Return true only for an explicit runtime boolean ``True``."""

    config = config if isinstance(config, Mapping) else {}
    runtime = config.get("gtos_vnext_runtime")
    runtime = runtime if isinstance(runtime, Mapping) else {}
    return runtime.get(WAVE21_FULL_FLOW_TRUTH_MODE_KEY) is True


def _is_false_authority_key(key: Any) -> bool:
    normalized = str(key or "").strip().lower()
    return bool(
        normalized in _FALSE_AUTHORITY_KEYS
        or normalized.startswith("p_")
        or normalized.endswith("_p")
        or normalized.endswith("_probability")
        or normalized.endswith("_probability_pct")
        or normalized.endswith("_probability_raw")
        or normalized.endswith("_ev")
        or normalized.endswith("_ev_r")
        or normalized.endswith("_expectancy")
        or normalized.endswith("expectancy_r")
        or normalized.endswith("expected_value")
        or normalized.endswith("expected_value_r")
        or "expected_net" in normalized
        or (
            "calibration" in normalized
            and not ("broker" in normalized and "cost" in normalized)
        )
    )


def _no_outcome_calibration_status(value: Mapping[str, Any]) -> str | None:
    calibration = value.get("confidence_calibration")
    if not isinstance(calibration, Mapping):
        return None
    status = calibration.get("calibration_source_status")
    return str(status) if status == NO_OUTCOME_CALIBRATION_CLAIM else None


def _is_probability_debate_record(value: Mapping[str, Any]) -> bool:
    if value.get("schema_version") == "probability_debate_team_engine_v4":
        return True
    theses = value.get("theses")
    if isinstance(theses, Mapping):
        thesis_rows = tuple(theses.values())
    elif isinstance(theses, (list, tuple)):
        thesis_rows = theses
    else:
        thesis_rows = ()
    return bool(
        any(
            isinstance(thesis, Mapping)
            and _no_outcome_calibration_status(thesis)
            for thesis in thesis_rows
        )
        and any(
            key in value
            for key in (
                "ranked_actions",
                "rejected_alternatives",
                "selected_action",
                "selected_thesis",
            )
        )
    )


def _accepted_geometry_bound_outcome_disposition() -> dict[str, Any]:
    return {
        "status": GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS,
        "reason": GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON,
        "source_required_field": PROBABILITY_TRUTH_SOURCE_REQUIRED_FIELD,
        "economic_authority_allowed": True,
    }


def is_preserved_geometry_bound_outcome_calibration(value: Any) -> bool:
    """True only for a self-consistent accepted packet-plus-disposition wrapper.

    The truth-mode strip removes every unlicensed probability surface; the one
    thing licensed to survive is a validated geometry-bound outcome packet.
    Survival demands the exact accepted disposition AND a packet whose own
    hash seal and every recomputed atom hold against its own bindings -- any
    tamper breaks the seal and the wrapper is stripped like everything else.
    """

    if not isinstance(value, Mapping):
        return False
    packet = value.get("packet")
    disposition = value.get("disposition")
    if not isinstance(packet, Mapping) or not isinstance(disposition, Mapping):
        return False
    if dict(disposition) != _accepted_geometry_bound_outcome_disposition():
        return False
    return not validate_geometry_bound_outcome_calibration_packet(
        packet,
        geometry_contract_hash_sha256=str(
            packet.get("geometry_contract_hash_sha256") or ""
        )
        or None,
        expected_model_artifact_sha256=str(
            packet.get("model_artifact_sha256") or ""
        )
        or None,
    )


def strip_probability_economic_authority(value: Any) -> Any:
    """Recursively remove probability, EV, and calibration aliases.

    A producer-marked no-calibration thesis keeps its former probability only
    as ``action_support_score``.  Broker cost calibration remains independent.
    The single licensed probability source -- a validated geometry-bound
    outcome calibration wrapper under ``geometry_bound_outcome_calibration``
    -- survives verbatim, but only when its hash seal and every recomputed
    atom hold (``is_preserved_geometry_bound_outcome_calibration``).
    """

    if isinstance(value, Mapping):
        if _is_probability_debate_record(value):
            return {
                str(key): strip_probability_economic_authority(child)
                for key, child in value.items()
                if key in _PROBABILITY_DEBATE_DIAGNOSTIC_KEYS
            }
        status = _no_outcome_calibration_status(value)
        if status:
            score = value.get("probability", value.get("action_support_score"))
            clean = {
                str(key): strip_probability_economic_authority(child)
                for key, child in value.items()
                if key in _NO_OUTCOME_THESIS_DIAGNOSTIC_KEYS
            }
            clean["action_support_score"] = score
            clean["action_support_score_status"] = status
            return clean
        clean = {}
        for key, child in value.items():
            if (
                str(key) == GEOMETRY_BOUND_OUTCOME_CALIBRATION_KEY
                and is_preserved_geometry_bound_outcome_calibration(child)
            ):
                clean[str(key)] = copy.deepcopy(child)
                continue
            if _is_false_authority_key(key):
                continue
            clean[str(key)] = strip_probability_economic_authority(child)
        return clean
    if isinstance(value, list):
        return [strip_probability_economic_authority(item) for item in value]
    if isinstance(value, tuple):
        return tuple(strip_probability_economic_authority(item) for item in value)
    return copy.deepcopy(value)


def apply_probability_truth_to_event(
    event: Mapping[str, Any],
    *,
    probability_debate: Mapping[str, Any],
) -> dict[str, Any]:
    """Sanitize a Selector event and stamp its terminal truth disposition."""

    projected = strip_probability_economic_authority(event)
    projected["probability_debate"] = strip_probability_economic_authority(
        probability_debate
    )
    projected.update(
        {
            "probability_truth_status": PROBABILITY_TRUTH_STATUS,
            "probability_truth_reason": (
                "geometry_bound_outcome_calibration_source_required"
            ),
            "probability_truth_source_required_field": (
                PROBABILITY_TRUTH_SOURCE_REQUIRED_FIELD
            ),
            "probability_truth_economic_authority_allowed": False,
        }
    )
    return projected


def geometry_bound_outcome_calibration_disposition(
    packet: Mapping[str, Any] | None,
    geometry_contract: Mapping[str, Any] | None,
    *,
    expected_model_artifact_sha256: str | None = None,
) -> dict[str, Any]:
    """Disposition a supplied outcome packet against the FINAL geometry contract.

    Fail-closed everywhere.  The only accepting path is a packet at the
    supported model version whose every atom validates
    (``validate_geometry_bound_outcome_calibration_packet``) against the final
    post-router geometry contract hash AND the caller-attested
    ``expected_model_artifact_sha256``.  Without the caller attestation no
    packet is ever accepted, so legacy two-argument callers keep the refusal
    behavior byte-for-byte.  Geometry staleness dominates every other check.
    """

    packet = packet if isinstance(packet, Mapping) else {}
    geometry = geometry_contract if isinstance(geometry_contract, Mapping) else {}
    packet_hash = str(packet.get("geometry_contract_hash_sha256") or "")
    geometry_hash = str(
        geometry.get("packet_hash_sha256")
        or geometry.get("source_event_hash_sha256")
        or ""
    )
    if not packet:
        reason = "geometry_bound_outcome_calibration_source_required"
    elif packet_hash and geometry_hash and packet_hash != geometry_hash:
        reason = "geometry_bound_outcome_calibration_stale_after_geometry_change"
    elif (
        packet.get("schema") == GEOMETRY_BOUND_OUTCOME_PACKET_SCHEMA
        and packet.get("model_version") == GEOMETRY_BOUND_OUTCOME_MODEL_VERSION
    ):
        failures = validate_geometry_bound_outcome_calibration_packet(
            packet,
            geometry_contract_hash_sha256=geometry_hash or None,
            expected_model_artifact_sha256=expected_model_artifact_sha256,
        )
        if not failures:
            return _accepted_geometry_bound_outcome_disposition()
        reason = (
            "geometry_bound_outcome_calibration_model_version_unsupported"
            if failures[0] == _REASON_MODEL_VERSION_UNSUPPORTED
            else failures[0]
        )
    else:
        reason = "geometry_bound_outcome_calibration_model_version_unsupported"
    return {
        "status": PROBABILITY_TRUTH_STATUS,
        "reason": reason,
        "source_required_field": PROBABILITY_TRUTH_SOURCE_REQUIRED_FIELD,
        "economic_authority_allowed": False,
    }


__all__ = [
    "GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON",
    "GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS",
    "GEOMETRY_BOUND_OUTCOME_CALIBRATION_KEY",
    "PROBABILITY_TRUTH_SOURCE_REQUIRED_FIELD",
    "PROBABILITY_TRUTH_STATUS",
    "WAVE21_FULL_FLOW_TRUTH_MODE_KEY",
    "apply_probability_truth_to_event",
    "geometry_bound_outcome_calibration_disposition",
    "is_preserved_geometry_bound_outcome_calibration",
    "strip_probability_economic_authority",
    "wave21_full_flow_truth_mode_enabled",
]
