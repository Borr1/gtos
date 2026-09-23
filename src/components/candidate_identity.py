"""Shared, current-field candidate identity canonicalization.

``candidate_id`` is a legacy compatibility value.  The cross-stage authorities
are:

* an emission lineage derived from current source provenance and invariant to
  downstream target/stop policy; and
* an executable instance minted only after final geometry and order policy are
  known.

Validators always rebuild atoms from the current candidate.  Stored atoms are
receipts to compare, never the recomputation authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Mapping


EMISSION_LINEAGE_SCHEMA = "gtos.broad_origin_emission_lineage.v1"
EXECUTABLE_INSTANCE_SCHEMA = "gtos.broad_origin_executable_instance.v1"
SELECTOR_INPUT_GEOMETRY_SCHEMA = "gtos.selector_input_candidate_geometry.v1"
SELECTOR_INPUT_GEOMETRY_SOURCE_BOUNDARY = (
    "selector_input_preselection_non_authoritative_geometry_snapshot"
)

EMISSION_LINEAGE_ID_PREFIX = "emissionlineage_"
EXECUTABLE_INSTANCE_ID_PREFIX = "execinstance_"

IDENTITY_STATUS_MATERIALIZED = "materialized"
EXECUTABLE_STATUS_NOT_FINAL = "not_final_generator_boundary"

EMISSION_LINEAGE_SOURCE_BOUNDARY = (
    "closed_predecision_source_anchor_no_outcome_target_stop_invariant"
)
EXECUTABLE_INSTANCE_SOURCE_BOUNDARY = (
    "post_transform_final_predecision_geometry_and_order_policy"
)
EXECUTABLE_NOT_FINAL_SOURCE_BOUNDARY = (
    "generator_candidate_geometry_before_selector_and_final_order_policy"
)

EMISSION_LINEAGE_FIELD_NAMES = (
    "emission_lineage_schema",
    "emission_lineage_id",
    "emission_lineage_hash_sha256",
    "emission_lineage_status",
    "emission_lineage_source_boundary",
    "emission_lineage_atoms",
    "emission_lineage_missing_atoms",
    "emission_lineage_origin_family",
    "emission_lineage_symbol",
    "emission_lineage_generation_side",
    "emission_lineage_source_anchor",
)

EXECUTABLE_INSTANCE_FIELD_NAMES = (
    "executable_instance_schema",
    "executable_instance_id",
    "executable_instance_hash_sha256",
    "executable_instance_status",
    "executable_instance_source_boundary",
    "executable_instance_decision_time_utc",
    "executable_instance_order_type",
    "executable_instance_time_in_force",
    "executable_instance_expiry_time_utc",
    "executable_instance_atoms",
    "executable_instance_missing_atoms",
)

SELECTOR_INPUT_GEOMETRY_FIELD_NAMES = (
    "selector_input_geometry_schema",
    "selector_input_geometry_sha256",
    "selector_input_geometry_status",
    "selector_input_geometry_source_boundary",
    "selector_input_geometry_atoms",
    "selector_input_geometry_missing_atoms",
)


def canonical_identity_sha256(payload: Any) -> str:
    normalized = _identity_primitive(payload)
    material = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _identity_primitive(value: Any) -> Any:
    """Normalize only explicitly supported deterministic JSON primitives."""

    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("candidate identity cannot encode NaN or infinity")
        return value
    if isinstance(value, datetime):
        return canonical_utc(value)
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("candidate identity mapping keys must be strings")
            normalized[key] = _identity_primitive(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_identity_primitive(item) for item in value]
    raise TypeError(
        "candidate identity supports only deterministic JSON primitives; "
        f"got {type(value).__name__}"
    )


def canonical_utc(value: Any) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return ""
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def canonical_symbol(value: Any) -> str:
    # Broker punctuation is identity-bearing (for example ``US30.cash`` and
    # ``US30_cash`` need not be the same instrument).  Alias resolution, when
    # authoritative, must happen before this boundary.
    return str(value or "").strip().upper()


def canonical_side(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"L", "LONG", "BUY"}:
        return "LONG"
    if text in {"S", "SHORT", "SELL"}:
        return "SHORT"
    return text


def canonical_order_type(value: Any) -> str:
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {
        "LIMIT",
        "LIMIT_ORDER",
        "PENDING_LIMIT",
        "BUY_LIMIT",
        "SELL_LIMIT",
    }:
        return "LIMIT"
    if text in {"MARKET", "MARKET_ORDER", "BUY", "SELL"}:
        return "MARKET"
    if text in {"STOP", "STOP_ORDER", "BUY_STOP", "SELL_STOP"}:
        return "STOP"
    if text in {"STOP_LIMIT", "BUY_STOP_LIMIT", "SELL_STOP_LIMIT"}:
        return "STOP_LIMIT"
    return text


def canonical_time_in_force(value: Any) -> str | None:
    text = str(value or "").strip().upper().replace("-", "_")
    aliases = {
        "GTC": "GTC",
        "GOOD_TIL_CANCELLED": "GTC",
        "GOOD_TILL_CANCELLED": "GTC",
        "DAY": "DAY",
        "IOC": "IOC",
        "IMMEDIATE_OR_CANCEL": "IOC",
        "FOK": "FOK",
        "FILL_OR_KILL": "FOK",
    }
    return aliases.get(text, text or None)


def canonical_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _source_fields(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    fields = candidate.get("source_fields")
    return fields if isinstance(fields, Mapping) else {}


def _trade_parameters(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    params = candidate.get("trade_parameters")
    return params if isinstance(params, Mapping) else {}


def _first_present(candidate: Mapping[str, Any], *keys: str) -> Any:
    for surface in (candidate, _trade_parameters(candidate)):
        for key in keys:
            value = surface.get(key)
            if value not in (None, ""):
                return value
    return None


def _poi_values(candidate: Mapping[str, Any]) -> list[str]:
    fields = _source_fields(candidate)
    poi_state = candidate.get("poi_state")
    if not isinstance(poi_state, Mapping):
        poi_state = fields.get("poi_state")
    poi_state = poi_state if isinstance(poi_state, Mapping) else {}
    values = [
        candidate.get("poi_id"),
        fields.get("poi_id"),
        poi_state.get("poi_id"),
    ]
    return [str(value).strip() for value in values if str(value or "").strip()]


def _source_salt(candidate: Mapping[str, Any]) -> Any:
    fields = _source_fields(candidate)
    return candidate.get("emission_source_salt", fields.get("source_detail"))


_FORBIDDEN_SOURCE_SALT_KEY_FRAGMENTS = (
    "target",
    "take_profit",
    "stop_loss",
    "outcome",
    "result",
    "pnl",
    "realized",
    "postdecision",
)


def _validate_source_salt(value: Any, path: str = "source_salt") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            text = str(key).strip().lower()
            if any(fragment in text for fragment in _FORBIDDEN_SOURCE_SALT_KEY_FRAGMENTS):
                raise ValueError(
                    f"emission source salt contains forbidden policy/outcome key {path}.{key}"
                )
            _validate_source_salt(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_source_salt(item, f"{path}[{index}]")


def emission_lineage_atoms_from_candidate(
    candidate: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Rebuild lineage atoms from current candidate/source projections."""

    poi_values = _poi_values(candidate)
    poi_id = poi_values[0] if poi_values else ""
    candle_open = canonical_utc(
        candidate.get("candle_open_utc")
        or _source_fields(candidate).get("candle_open_utc")
    )
    if poi_id:
        source_anchor: dict[str, Any] = {"kind": "poi_id", "poi_id": poi_id}
    else:
        salt = _source_salt(candidate)
        if salt is not None:
            _validate_source_salt(salt)
        source_anchor = {
            "kind": "closed_bar_source",
            "candle_open_utc": candle_open,
            "source_salt_sha256": (
                canonical_identity_sha256(salt) if salt is not None else None
            ),
        }
    atoms = {
        "origin_family": str(candidate.get("origin_family") or "").strip(),
        "symbol": canonical_symbol(candidate.get("symbol")),
        "generation_side": canonical_side(
            candidate.get("emission_generation_side") or candidate.get("side")
        ),
        "source_anchor": source_anchor,
    }
    missing = [
        name
        for name, value in (
            ("origin_family", atoms["origin_family"]),
            ("symbol", atoms["symbol"]),
            ("generation_side", atoms["generation_side"]),
            ("source_anchor", poi_id or candle_open),
        )
        if not value
    ]
    return atoms, missing


def emission_lineage_hash_from_atoms(atoms: Mapping[str, Any]) -> str:
    return canonical_identity_sha256(
        {"schema": EMISSION_LINEAGE_SCHEMA, **dict(atoms)}
    )


def build_emission_lineage_fields(candidate: Mapping[str, Any]) -> dict[str, Any]:
    atoms, missing = emission_lineage_atoms_from_candidate(candidate)
    digest = emission_lineage_hash_from_atoms(atoms) if not missing else ""
    return {
        "emission_lineage_schema": EMISSION_LINEAGE_SCHEMA,
        "emission_lineage_id": (
            f"{EMISSION_LINEAGE_ID_PREFIX}{digest[:24]}" if digest else None
        ),
        "emission_lineage_hash_sha256": digest or None,
        "emission_lineage_status": (
            IDENTITY_STATUS_MATERIALIZED if digest else "missing_required_atoms"
        ),
        "emission_lineage_source_boundary": EMISSION_LINEAGE_SOURCE_BOUNDARY,
        "emission_lineage_atoms": atoms,
        "emission_lineage_missing_atoms": missing,
        "emission_lineage_origin_family": atoms["origin_family"],
        "emission_lineage_symbol": atoms["symbol"],
        "emission_lineage_generation_side": atoms["generation_side"],
        "emission_lineage_source_anchor": atoms["source_anchor"],
    }


def executable_instance_atoms_from_candidate(
    candidate: Mapping[str, Any],
    *,
    require_final_order: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    """Rebuild exact post-transform executable atoms from current fields."""

    lineage = build_emission_lineage_fields(candidate)
    order_type = canonical_order_type(
        _first_present(candidate, "final_order_type", "order_type")
    )
    if not require_final_order and not order_type:
        order_type = canonical_order_type(candidate.get("candidate_order_type_hint"))
    decision_time = canonical_utc(
        candidate.get("decision_time_utc")
        or candidate.get("source_asof_utc")
        or candidate.get("candle_close_utc")
    )
    atoms = {
        "emission_lineage_hash_sha256": lineage.get(
            "emission_lineage_hash_sha256"
        ),
        "decision_time_utc": decision_time,
        "symbol": canonical_symbol(candidate.get("symbol")),
        "side": canonical_side(candidate.get("side") or candidate.get("direction")),
        "entry_price": canonical_number(
            _first_present(candidate, "entry_price", "entry_reference", "entry")
        ),
        "stop_loss": canonical_number(
            _first_present(
                candidate,
                "stop_loss",
                "stop_or_invalidation",
                "stop_price",
                "sl",
            )
        ),
        "take_profit_1": canonical_number(
            _first_present(
                candidate,
                "take_profit_1",
                "target_reference",
                "take_profit",
                "target_price",
                "tp",
            )
        ),
        "order_type": order_type,
        "time_in_force": canonical_time_in_force(
            _first_present(candidate, "time_in_force", "tif")
        ),
        "expiry_time_utc": (
            canonical_utc(_first_present(candidate, "expiry_time_utc", "expiry"))
            or None
        ),
    }
    required = (
        "emission_lineage_hash_sha256",
        "decision_time_utc",
        "symbol",
        "side",
        "entry_price",
        "stop_loss",
        "take_profit_1",
    )
    if require_final_order:
        required = (*required, "order_type")
    missing = [key for key in required if atoms.get(key) in (None, "")]
    if require_final_order and order_type in {"LIMIT", "STOP", "STOP_LIMIT"}:
        if not atoms["time_in_force"]:
            missing.append("time_in_force")
        elif atoms["time_in_force"] != "GTC" and not atoms["expiry_time_utc"]:
            missing.append("expiry_time_utc_or_gtc")
    return atoms, missing


def executable_instance_hash_from_atoms(atoms: Mapping[str, Any]) -> str:
    return canonical_identity_sha256(
        {"schema": EXECUTABLE_INSTANCE_SCHEMA, **dict(atoms)}
    )


def build_executable_instance_fields(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    atoms, missing = executable_instance_atoms_from_candidate(
        candidate,
        require_final_order=True,
    )
    digest = executable_instance_hash_from_atoms(atoms) if not missing else ""
    return {
        "executable_instance_schema": EXECUTABLE_INSTANCE_SCHEMA,
        "executable_instance_id": (
            f"{EXECUTABLE_INSTANCE_ID_PREFIX}{digest[:24]}" if digest else None
        ),
        "executable_instance_hash_sha256": digest or None,
        "executable_instance_status": (
            IDENTITY_STATUS_MATERIALIZED if digest else "missing_required_atoms"
        ),
        "executable_instance_source_boundary": EXECUTABLE_INSTANCE_SOURCE_BOUNDARY,
        "executable_instance_decision_time_utc": atoms["decision_time_utc"] or None,
        "executable_instance_order_type": atoms["order_type"] or None,
        "executable_instance_time_in_force": atoms["time_in_force"],
        "executable_instance_expiry_time_utc": atoms["expiry_time_utc"],
        "executable_instance_atoms": atoms,
        "executable_instance_missing_atoms": missing,
    }


def executable_instance_not_final_fields(candidate: Mapping[str, Any]) -> dict[str, Any]:
    _, missing = executable_instance_atoms_from_candidate(
        candidate,
        require_final_order=True,
    )
    return {
        "executable_instance_schema": EXECUTABLE_INSTANCE_SCHEMA,
        "executable_instance_id": None,
        "executable_instance_hash_sha256": None,
        "executable_instance_status": EXECUTABLE_STATUS_NOT_FINAL,
        "executable_instance_source_boundary": EXECUTABLE_NOT_FINAL_SOURCE_BOUNDARY,
        "executable_instance_decision_time_utc": None,
        "executable_instance_order_type": None,
        "executable_instance_time_in_force": None,
        "executable_instance_expiry_time_utc": None,
        "executable_instance_atoms": None,
        "executable_instance_missing_atoms": sorted(
            set([*missing, "final_order_policy_boundary"])
        ),
    }


def selector_input_geometry_atoms_from_candidate(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Non-authoritative Selector input snapshot using shared normalizers."""

    atoms, _ = executable_instance_atoms_from_candidate(
        candidate,
        require_final_order=False,
    )
    return {"schema": SELECTOR_INPUT_GEOMETRY_SCHEMA, **atoms}


def selector_input_geometry_sha256(candidate: Mapping[str, Any]) -> str:
    return canonical_identity_sha256(
        selector_input_geometry_atoms_from_candidate(candidate)
    )


def build_selector_input_geometry_fields(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    atoms, missing = executable_instance_atoms_from_candidate(
        candidate,
        require_final_order=False,
    )
    payload = {"schema": SELECTOR_INPUT_GEOMETRY_SCHEMA, **atoms}
    digest = canonical_identity_sha256(payload) if not missing else None
    return {
        "selector_input_geometry_schema": SELECTOR_INPUT_GEOMETRY_SCHEMA,
        "selector_input_geometry_sha256": digest,
        "selector_input_geometry_status": (
            IDENTITY_STATUS_MATERIALIZED if digest else "missing_required_atoms"
        ),
        "selector_input_geometry_source_boundary": (
            SELECTOR_INPUT_GEOMETRY_SOURCE_BOUNDARY
        ),
        "selector_input_geometry_atoms": atoms,
        "selector_input_geometry_missing_atoms": missing,
    }


def _identity_claimed(candidate: Mapping[str, Any], names: tuple[str, ...]) -> bool:
    return any(candidate.get(name) not in (None, "", [], ()) for name in names)


def _lineage_projection_failures(candidate: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    poi_values = _poi_values(candidate)
    if len(set(poi_values)) > 1:
        failures.append("emission_lineage_poi_projection_conflict")
    fields = _source_fields(candidate)
    source_family = str(
        fields.get("origin_family") or fields.get("generation_rule") or ""
    ).strip()
    if source_family and source_family != str(candidate.get("origin_family") or "").strip():
        failures.append("emission_lineage_origin_family_projection_conflict")
    return failures


def candidate_identity_contract_failures(
    candidate: Mapping[str, Any],
    *,
    require_emission: bool = False,
    require_executable: bool = False,
) -> tuple[str, ...]:
    """Validate v1 receipts against current fields, with explicit stage rules."""

    failures: list[str] = []
    emission_claimed = _identity_claimed(candidate, EMISSION_LINEAGE_FIELD_NAMES)
    if require_emission or emission_claimed:
        expected = build_emission_lineage_fields(candidate)
        if not emission_claimed:
            failures.append("emission_lineage_required_missing")
        failures.extend(_lineage_projection_failures(candidate))
        for field in EMISSION_LINEAGE_FIELD_NAMES:
            if candidate.get(field) != expected.get(field):
                failures.append(f"{field}_current_projection_mismatch")
        if expected["emission_lineage_status"] != IDENTITY_STATUS_MATERIALIZED:
            failures.append("emission_lineage_current_required_atoms_missing")

    executable_status = candidate.get("executable_instance_status")
    executable_claimed = _identity_claimed(
        candidate, EXECUTABLE_INSTANCE_FIELD_NAMES
    )
    if executable_status == EXECUTABLE_STATUS_NOT_FINAL:
        expected_not_final = executable_instance_not_final_fields(candidate)
        for field in EXECUTABLE_INSTANCE_FIELD_NAMES:
            if candidate.get(field) != expected_not_final.get(field):
                failures.append(f"{field}_not_final_projection_mismatch")
        if require_executable:
            failures.append("executable_instance_required_not_materialized")
    elif require_executable or executable_claimed:
        expected = build_executable_instance_fields(candidate)
        if not executable_claimed:
            failures.append("executable_instance_required_missing")
        for field in EXECUTABLE_INSTANCE_FIELD_NAMES:
            if candidate.get(field) != expected.get(field):
                failures.append(f"{field}_current_projection_mismatch")
        if expected["executable_instance_status"] != IDENTITY_STATUS_MATERIALIZED:
            failures.append("executable_instance_current_required_atoms_missing")

    return tuple(dict.fromkeys(failures))


__all__ = [
    "EMISSION_LINEAGE_FIELD_NAMES",
    "EMISSION_LINEAGE_ID_PREFIX",
    "EMISSION_LINEAGE_SCHEMA",
    "EMISSION_LINEAGE_SOURCE_BOUNDARY",
    "EXECUTABLE_INSTANCE_FIELD_NAMES",
    "EXECUTABLE_INSTANCE_ID_PREFIX",
    "EXECUTABLE_INSTANCE_SCHEMA",
    "EXECUTABLE_INSTANCE_SOURCE_BOUNDARY",
    "EXECUTABLE_NOT_FINAL_SOURCE_BOUNDARY",
    "EXECUTABLE_STATUS_NOT_FINAL",
    "IDENTITY_STATUS_MATERIALIZED",
    "SELECTOR_INPUT_GEOMETRY_SCHEMA",
    "SELECTOR_INPUT_GEOMETRY_FIELD_NAMES",
    "SELECTOR_INPUT_GEOMETRY_SOURCE_BOUNDARY",
    "build_selector_input_geometry_fields",
    "build_emission_lineage_fields",
    "build_executable_instance_fields",
    "candidate_identity_contract_failures",
    "canonical_identity_sha256",
    "canonical_number",
    "canonical_order_type",
    "canonical_side",
    "canonical_symbol",
    "canonical_time_in_force",
    "canonical_utc",
    "emission_lineage_atoms_from_candidate",
    "emission_lineage_hash_from_atoms",
    "executable_instance_atoms_from_candidate",
    "executable_instance_hash_from_atoms",
    "executable_instance_not_final_fields",
    "selector_input_geometry_atoms_from_candidate",
    "selector_input_geometry_sha256",
]
