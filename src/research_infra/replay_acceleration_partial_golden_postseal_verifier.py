from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence

from src.research_infra.replay_acceleration_partial_golden_verifier import (
    PartialGoldenVerificationError,
    verify_partial_golden_manifest,
)


AMENDMENT_SCHEMA = (
    "gtos.replay_acceleration.partial_golden_postseal_namespace_amendment.v1"
)
AMENDMENT_GATE = "POST_SEAL_NAMESPACE_AMENDMENT_PROSPECTIVELY_SEALED"
ACCEPTED_GATE = "POST_SEAL_NAMESPACE_AMENDMENT_INDEPENDENTLY_ACCEPTED"
MANIFEST_SCHEMA = "gtos.replay_acceleration.partial_golden_manifest.v1"
MANIFEST_GATE = "PARTIAL_GOLDEN_SEALED_FOR_BOUNDED_EQUIVALENCE"
BLOCKER_SCHEMA = (
    "gtos.replay_acceleration."
    "post_recovery_legacy_namespace_mismatch_blocker.v1"
)
TOMBSTONE_SCHEMA = (
    "gtos.final_moonshot.broad_live_as_if_replay_harness."
    "interrupted_summary.v1"
)
TOMBSTONE_STATUS = "interrupted_partial_not_final_proof"
TOMBSTONE_SEMANTICS = (
    "parseable tombstone generated from the last completed chunk; "
    "not a completed broad replay proof"
)
AMENDMENT_KEYS = frozenset(
    {
        "schema",
        "gate",
        "status",
        "original_golden",
        "blocker_binding",
        "current_namespace",
        "derivative_tombstone",
        "fail_closed_contract",
        "permissions",
        "outcome_blindness",
        "amendment_self_root_sha256",
    }
)
ORIGINAL_GOLDEN_KEYS = frozenset(
    {
        "manifest_path",
        "manifest_sha256",
        "manifest_self_root_sha256",
        "manifest_verification_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
        "inventory_exact_at_seal",
        "sealed_file_count",
        "sealed_filenames",
        "sealed_role_bytes",
        "original_manifest_modified",
        "original_golden_rerooted",
    }
)
BLOCKER_BINDING_KEYS = frozenset({"path", "receipt_root_sha256"})
CURRENT_NAMESPACE_KEYS = frozenset(
    {
        "path",
        "output_prefix",
        "accepted_file_count",
        "accepted_filenames",
        "acceptance_rule",
    }
)
DERIVATIVE_TOMBSTONE_KEYS = frozenset(
    {
        "filename",
        "bytes",
        "sha256",
        "schema",
        "status",
        "interrupted_run",
        "generated_at_utc",
        "last_completed_end_day",
        "interrupted_summary_semantics",
        "role_bytes",
        "null_roles",
        "derivative_not_completed_replay_proof",
    }
)
FAIL_CLOSED_KEYS = frozenset(
    {
        "changed_sealed_file_rejected",
        "changed_tombstone_rejected",
        "missing_original_rejected",
        "second_extra_rejected",
        "role_byte_mismatch_rejected",
        "generic_ignore_patterns_permitted",
    }
)
PERMISSION_KEYS = frozenset(
    {
        "actual_accelerated_s0r0_jan_1_7",
        "jan_8_31_continuation",
        "other_arms",
        "broker_live_vps_deployment",
        "legacy_evidence_mutation",
    }
)
OUTCOME_BLINDNESS_KEYS = frozenset(
    {
        "economic_values_exposed",
        "tombstone_values_projected_only_from_allowlisted_structural_fields",
        "ledger_files_verified_as_opaque_bytes",
    }
)
AMENDMENT_STATUS = "EXACTLY_ONE_POST_SEAL_DERIVATIVE_BOUND"
NAMESPACE_ACCEPTANCE_RULE = (
    "original_exact_inventory_plus_one_specifically_bound_derivative"
)
JAN_8_31_PERMISSION = "CONDITIONAL_ON_EXACT_REAL_ROUTE_PARITY"
UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|\+00:00)$"
)
FORBIDDEN_KEY_FRAGMENTS = (
    "pnl",
    "profit",
    "win_count",
    "loss_count",
    "win_rate",
    "net_r",
    "total_r",
    "reward_value",
    "drawdown_value",
)


class PostSealAmendmentVerificationError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PostSealAmendmentVerificationError(code)


def _exact_keys(value: Any, expected: frozenset[str], code: str) -> None:
    _require(isinstance(value, Mapping) and set(value) == expected, code)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
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
        raise PostSealAmendmentVerificationError(code) from exc
    _require(parsed.isoformat() == text, code)
    return text


def _strict_utc_timestamp(value: Any, code: str) -> str:
    text = _strict_string(value, code)
    _require(UTC_TIMESTAMP.fullmatch(text) is not None, code)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise PostSealAmendmentVerificationError(code) from exc
    _require(
        parsed.utcoffset() is not None
        and parsed.utcoffset().total_seconds() == 0,
        code,
    )
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


def _strict_string_list(
    value: Any, code: str, *, filenames: bool = False
) -> list[str]:
    _require(type(value) is list, code)
    validator = _safe_filename if filenames else _strict_string
    result = [validator(item, code) for item in value]
    _require(len(set(result)) == len(result) and result == sorted(result), code)
    return result


def _strict_role_bytes(value: Any, code: str) -> dict[str, int]:
    _require(isinstance(value, Mapping), code)
    result: dict[str, int] = {}
    for role, byte_count in value.items():
        role_name = _strict_string(role, code)
        _require(role_name not in result, code)
        result[role_name] = _strict_nonnegative_int(byte_count, code)
    return result


def _validate_amendment_schema(amendment: Mapping[str, Any]) -> None:
    _exact_keys(amendment, AMENDMENT_KEYS, "amendment_unknown_fields")
    _exact_keys(
        amendment.get("original_golden"),
        ORIGINAL_GOLDEN_KEYS,
        "amendment_original_golden_unknown_fields",
    )
    _exact_keys(
        amendment.get("blocker_binding"),
        BLOCKER_BINDING_KEYS,
        "amendment_blocker_binding_unknown_fields",
    )
    _exact_keys(
        amendment.get("current_namespace"),
        CURRENT_NAMESPACE_KEYS,
        "amendment_current_namespace_unknown_fields",
    )
    _exact_keys(
        amendment.get("derivative_tombstone"),
        DERIVATIVE_TOMBSTONE_KEYS,
        "amendment_derivative_tombstone_unknown_fields",
    )
    _exact_keys(
        amendment.get("fail_closed_contract"),
        FAIL_CLOSED_KEYS,
        "amendment_fail_closed_unknown_fields",
    )
    _exact_keys(
        amendment.get("permissions"),
        PERMISSION_KEYS,
        "amendment_permissions_unknown_fields",
    )
    _exact_keys(
        amendment.get("outcome_blindness"),
        OUTCOME_BLINDNESS_KEYS,
        "amendment_outcome_blindness_unknown_fields",
    )


def _validate_amendment_leaf_types(amendment: Mapping[str, Any]) -> None:
    _require(
        amendment.get("schema") == AMENDMENT_SCHEMA,
        "amendment_schema_mismatch",
    )
    _require(amendment.get("gate") == AMENDMENT_GATE, "amendment_gate_mismatch")
    _require(
        amendment.get("status") == AMENDMENT_STATUS,
        "amendment_status_mismatch",
    )

    original = amendment["original_golden"]
    _lexical_absolute_path(
        original.get("manifest_path"), "amendment_original_golden_invalid"
    )
    for field in (
        "manifest_sha256",
        "manifest_self_root_sha256",
        "manifest_verification_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
    ):
        _require(
            _is_sha256(original.get(field)),
            "amendment_original_golden_invalid",
        )
    _require(
        type(original.get("inventory_exact_at_seal")) is bool
        and original.get("inventory_exact_at_seal") is True
        and type(original.get("original_manifest_modified")) is bool
        and original.get("original_manifest_modified") is False
        and type(original.get("original_golden_rerooted")) is bool
        and original.get("original_golden_rerooted") is False,
        "amendment_original_golden_invalid",
    )
    sealed_count = _strict_nonnegative_int(
        original.get("sealed_file_count"),
        "amendment_original_golden_invalid",
    )
    sealed_names = _strict_string_list(
        original.get("sealed_filenames"),
        "amendment_original_golden_invalid",
        filenames=True,
    )
    _require(
        sealed_count == len(sealed_names),
        "amendment_original_golden_invalid",
    )
    _strict_role_bytes(
        original.get("sealed_role_bytes"),
        "amendment_original_golden_invalid",
    )

    blocker = amendment["blocker_binding"]
    _lexical_absolute_path(
        blocker.get("path"), "amendment_blocker_binding_invalid"
    )
    _require(
        _is_sha256(blocker.get("receipt_root_sha256")),
        "amendment_blocker_binding_invalid",
    )

    current = amendment["current_namespace"]
    _lexical_absolute_path(
        current.get("path"), "amendment_current_namespace_invalid"
    )
    _safe_filename(
        current.get("output_prefix"), "amendment_current_namespace_invalid"
    )
    accepted_count = _strict_nonnegative_int(
        current.get("accepted_file_count"),
        "amendment_current_namespace_invalid",
    )
    accepted_names = _strict_string_list(
        current.get("accepted_filenames"),
        "amendment_current_namespace_invalid",
        filenames=True,
    )
    _require(
        accepted_count == len(accepted_names)
        and current.get("acceptance_rule") == NAMESPACE_ACCEPTANCE_RULE,
        "amendment_current_namespace_invalid",
    )

    derivative = amendment["derivative_tombstone"]
    _safe_filename(
        derivative.get("filename"), "amendment_tombstone_invalid"
    )
    _strict_nonnegative_int(
        derivative.get("bytes"), "amendment_tombstone_invalid"
    )
    _require(
        _is_sha256(derivative.get("sha256")),
        "amendment_tombstone_invalid",
    )
    _require(
        derivative.get("schema") == TOMBSTONE_SCHEMA
        and derivative.get("status") == TOMBSTONE_STATUS
        and type(derivative.get("interrupted_run")) is bool
        and derivative.get("interrupted_run") is True
        and derivative.get("interrupted_summary_semantics")
        == TOMBSTONE_SEMANTICS
        and type(derivative.get("derivative_not_completed_replay_proof"))
        is bool
        and derivative.get("derivative_not_completed_replay_proof") is True,
        "amendment_tombstone_invalid",
    )
    _strict_utc_timestamp(
        derivative.get("generated_at_utc"), "amendment_tombstone_invalid"
    )
    _strict_day(
        derivative.get("last_completed_end_day"),
        "amendment_tombstone_invalid",
    )
    _strict_role_bytes(
        derivative.get("role_bytes"), "amendment_tombstone_invalid"
    )
    _strict_string_list(
        derivative.get("null_roles"), "amendment_tombstone_invalid"
    )

    fail_closed = amendment["fail_closed_contract"]
    _require(
        all(
            type(fail_closed.get(field)) is bool
            and fail_closed.get(field) is True
            for field in FAIL_CLOSED_KEYS
            - {"generic_ignore_patterns_permitted"}
        )
        and type(fail_closed.get("generic_ignore_patterns_permitted")) is bool
        and fail_closed.get("generic_ignore_patterns_permitted") is False,
        "amendment_fail_closed_invalid",
    )

    permissions = amendment["permissions"]
    _require(
        type(permissions.get("actual_accelerated_s0r0_jan_1_7")) is bool
        and permissions.get("actual_accelerated_s0r0_jan_1_7") is True
        and permissions.get("jan_8_31_continuation") == JAN_8_31_PERMISSION
        and type(permissions.get("other_arms")) is bool
        and permissions.get("other_arms") is False
        and type(permissions.get("broker_live_vps_deployment")) is bool
        and permissions.get("broker_live_vps_deployment") is False
        and type(permissions.get("legacy_evidence_mutation")) is bool
        and permissions.get("legacy_evidence_mutation") is False,
        "amendment_permissions_invalid",
    )

    outcome = amendment["outcome_blindness"]
    _require(
        type(outcome.get("economic_values_exposed")) is bool
        and outcome.get("economic_values_exposed") is False
        and type(
            outcome.get(
                "tombstone_values_projected_only_from_allowlisted_structural_fields"
            )
        )
        is bool
        and outcome.get(
            "tombstone_values_projected_only_from_allowlisted_structural_fields"
        )
        is True
        and type(outcome.get("ledger_files_verified_as_opaque_bytes")) is bool
        and outcome.get("ledger_files_verified_as_opaque_bytes") is True,
        "amendment_outcome_blindness_invalid",
    )
    _require(
        _is_sha256(amendment.get("amendment_self_root_sha256")),
        "amendment_self_root_invalid",
    )


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _compact_root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)[:-1]).hexdigest()


def _file_digest(path: Path) -> str:
    state = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            state.update(block)
    return state.hexdigest()


def _load(path: Path, code: str) -> tuple[bytes, Mapping[str, Any]]:
    _require(path.is_file() and not path.is_symlink(), f"{code}_missing")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PostSealAmendmentVerificationError(f"{code}_invalid_json") from exc
    _require(isinstance(value, Mapping), f"{code}_not_mapping")
    return raw, value


def _check_keys(value: Any, prefix: str = "") -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            lowered = key.lower()
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                _require(fragment not in lowered, f"forbidden_key:{prefix}{key}")
            _check_keys(child, f"{prefix}{key}.")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_keys(child, f"{prefix}{index}.")


def _validate_manifest(
    manifest_path: Path,
    *,
    git_root: Path,
) -> tuple[
    Mapping[str, Any],
    Path,
    str,
    dict[str, int],
    list[str],
    Mapping[str, Any],
]:
    raw, manifest = _load(manifest_path, "manifest")
    namespace_record = manifest.get("namespace")
    _require(isinstance(namespace_record, Mapping), "manifest_namespace_missing")
    prefix = str(namespace_record.get("output_prefix") or "")
    _require(prefix, "manifest_namespace_invalid")
    tombstone_name = f"{prefix}_SUMMARY.json"
    try:
        verification = verify_partial_golden_manifest(
            manifest_path,
            git_root=git_root,
            allowed_namespace_additions=(tombstone_name,),
        )
    except (PartialGoldenVerificationError, OSError, ValueError) as exc:
        raise PostSealAmendmentVerificationError(
            "manifest_independent_verification_failed"
        ) from exc
    _require(
        hashlib.sha256(raw).hexdigest() == verification.get("manifest_sha256"),
        "manifest_changed_after_verification",
    )
    namespace = Path(str(namespace_record.get("path")))
    surfaces = manifest["persisted_result_surfaces"]
    partial = manifest["partial_summary"]
    role_bytes = {str(row["role"]): int(row["bytes"]) for row in surfaces}
    names = sorted(
        [str(partial["name"]), *(str(row["name"]) for row in surfaces)]
    )
    return manifest, namespace, prefix, role_bytes, names, verification


def _validate_blocker(
    blocker_path: Path, manifest: Mapping[str, Any]
) -> Mapping[str, Any]:
    _raw, blocker = _load(blocker_path, "blocker")
    _require(blocker.get("schema") == BLOCKER_SCHEMA, "blocker_schema_mismatch")
    projection = dict(blocker)
    projection.pop("receipt_root_sha256", None)
    _require(
        blocker.get("receipt_root_sha256") == _compact_root(projection),
        "blocker_self_root_mismatch",
    )
    authority = blocker.get("authority_state")
    _require(isinstance(authority, Mapping), "blocker_authority_missing")
    for key in (
        "manifest_self_root_sha256",
        "golden_root_sha256",
        "opaque_result_surface_root_sha256",
    ):
        _require(
            authority.get(key) == manifest.get(key),
            f"blocker_authority_mismatch:{key}",
        )
    mismatch = blocker.get("namespace_mismatch")
    _require(isinstance(mismatch, Mapping), "blocker_namespace_mismatch_missing")
    _require(mismatch.get("missing_file_count") == 0, "blocker_missing_files_present")
    _require(
        mismatch.get("unexpected_file_count") == 1,
        "blocker_unexpected_file_count_mismatch",
    )
    return blocker


def _load_tombstone(
    *, namespace: Path, prefix: str, blocker: Mapping[str, Any]
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    unexpected = blocker["namespace_mismatch"].get("unexpected_file")
    _require(isinstance(unexpected, Mapping), "blocker_unexpected_file_missing")
    name = str(unexpected.get("filename") or "")
    _require(name == f"{prefix}_SUMMARY.json", "tombstone_name_mismatch")
    path = namespace / name
    _require(path.is_file() and not path.is_symlink(), "tombstone_missing")
    _require(path.stat().st_size == unexpected.get("bytes"), "tombstone_size_mismatch")
    _require(_file_digest(path) == unexpected.get("sha256"), "tombstone_hash_mismatch")
    _raw, tombstone = _load(path, "tombstone")
    return tombstone, {
        "filename": name,
        "bytes": unexpected["bytes"],
        "sha256": unexpected["sha256"],
    }


def _tombstone_metadata(
    tombstone: Mapping[str, Any], *, role_bytes: Mapping[str, int], end_day: str
) -> tuple[dict[str, Any], dict[str, int], list[str]]:
    _require(tombstone.get("schema") == TOMBSTONE_SCHEMA, "tombstone_schema_mismatch")
    _require(tombstone.get("status") == TOMBSTONE_STATUS, "tombstone_status_mismatch")
    _require(tombstone.get("interrupted_run") is True, "tombstone_interrupted_flag_mismatch")
    _require(tombstone.get("last_completed_end_day") == end_day, "tombstone_end_day_mismatch")
    _require(
        tombstone.get("interrupted_summary_semantics") == TOMBSTONE_SEMANTICS,
        "tombstone_semantics_mismatch",
    )
    generated_at = tombstone.get("generated_at_utc")
    _require(isinstance(generated_at, str) and generated_at, "tombstone_timestamp_missing")
    raw_role_bytes = tombstone.get("ledger_file_bytes_at_interrupt")
    _require(isinstance(raw_role_bytes, Mapping), "tombstone_ledger_bytes_missing")
    projected: dict[str, int] = {}
    null_roles: list[str] = []
    for raw_role, value in raw_role_bytes.items():
        role = str(raw_role)
        if value is None:
            null_roles.append(role)
            continue
        _require(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0,
            f"tombstone_role_bytes_invalid:{role}",
        )
        projected[role] = value
    _require(projected == dict(role_bytes), "tombstone_role_bytes_mismatch")
    metadata = {
        "schema": TOMBSTONE_SCHEMA,
        "status": TOMBSTONE_STATUS,
        "interrupted_run": True,
        "generated_at_utc": generated_at,
        "last_completed_end_day": end_day,
        "interrupted_summary_semantics": TOMBSTONE_SEMANTICS,
        "derivative_not_completed_replay_proof": True,
    }
    return metadata, projected, sorted(null_roles)


def verify_postseal_namespace_amendment(
    *,
    amendment_path: Path,
    manifest_path: Path,
    blocker_receipt_path: Path,
    git_root: Path | None = None,
) -> dict[str, Any]:
    amendment_path = Path(amendment_path).resolve()
    manifest_path = Path(manifest_path).resolve()
    blocker_receipt_path = Path(blocker_receipt_path).resolve()
    amendment_raw, amendment = _load(amendment_path, "amendment")
    _validate_amendment_schema(amendment)
    _check_keys(amendment)
    _require(amendment_raw == _canonical(amendment), "amendment_not_canonical")
    projection = dict(amendment)
    projection.pop("amendment_self_root_sha256", None)
    _require(
        amendment.get("amendment_self_root_sha256") == _root(projection),
        "amendment_self_root_mismatch",
    )
    _validate_amendment_leaf_types(amendment)

    (
        manifest,
        namespace,
        prefix,
        role_bytes,
        original_names,
        manifest_verification,
    ) = _validate_manifest(
        manifest_path,
        git_root=(git_root or Path(__file__).resolve().parents[2]),
    )
    blocker = _validate_blocker(blocker_receipt_path, manifest)
    tombstone, identity = _load_tombstone(
        namespace=namespace, prefix=prefix, blocker=blocker
    )
    metadata, observed_role_bytes, null_roles = _tombstone_metadata(
        tombstone,
        role_bytes=role_bytes,
        end_day=str(manifest["scope"]["end_day"]),
    )
    accepted_names = sorted([*original_names, identity["filename"]])
    current_names = sorted(
        path.name
        for path in namespace.iterdir()
        if path.is_file() and path.name.startswith(prefix + "_")
    )
    _require(current_names == accepted_names, "current_namespace_inventory_mismatch")

    expected_original = {
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_verification["manifest_sha256"],
        "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
        "manifest_verification_root_sha256": manifest_verification[
            "verification_root_sha256"
        ],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "opaque_result_surface_root_sha256": manifest[
            "opaque_result_surface_root_sha256"
        ],
        "inventory_exact_at_seal": True,
        "sealed_file_count": len(original_names),
        "sealed_filenames": original_names,
        "sealed_role_bytes": role_bytes,
        "original_manifest_modified": False,
        "original_golden_rerooted": False,
    }
    _require(
        amendment.get("original_golden") == expected_original,
        "amendment_original_golden_mismatch",
    )
    _require(
        amendment.get("blocker_binding")
        == {
            "path": str(blocker_receipt_path),
            "receipt_root_sha256": blocker["receipt_root_sha256"],
        },
        "amendment_blocker_binding_mismatch",
    )
    derivative = amendment.get("derivative_tombstone")
    _require(isinstance(derivative, Mapping), "amendment_tombstone_missing")
    expected_metadata = {**identity, **metadata}
    for key, value in expected_metadata.items():
        _require(
            derivative.get(key) == value,
            "amendment_tombstone_metadata_mismatch",
        )
    _require(
        derivative.get("role_bytes") == observed_role_bytes,
        "amendment_role_bytes_mismatch",
    )
    _require(
        derivative.get("null_roles") == null_roles,
        "amendment_null_roles_mismatch",
    )
    _require(
        amendment.get("current_namespace")
        == {
            "path": str(namespace),
            "output_prefix": prefix,
            "accepted_file_count": len(accepted_names),
            "accepted_filenames": accepted_names,
            "acceptance_rule": (
                "original_exact_inventory_plus_one_specifically_bound_derivative"
            ),
        },
        "amendment_current_namespace_mismatch",
    )
    fail_closed = amendment.get("fail_closed_contract")
    _require(isinstance(fail_closed, Mapping), "amendment_fail_closed_missing")
    _require(
        fail_closed.get("generic_ignore_patterns_permitted") is False,
        "generic_ignore_patterns_permitted",
    )
    permissions = amendment.get("permissions")
    _require(isinstance(permissions, Mapping), "amendment_permissions_missing")
    _require(permissions.get("other_arms") is False, "other_arms_authorized")
    _require(
        permissions.get("broker_live_vps_deployment") is False,
        "broker_live_authorized",
    )
    _require(
        permissions.get("jan_8_31_continuation")
        == "CONDITIONAL_ON_EXACT_REAL_ROUTE_PARITY",
        "jan_8_31_open_before_parity",
    )
    outcome = amendment.get("outcome_blindness")
    _require(isinstance(outcome, Mapping), "outcome_blindness_missing")
    _require(outcome.get("economic_values_exposed") is False, "economic_values_exposed")

    receipt_core: dict[str, Any] = {
        "schema": (
            "gtos.replay_acceleration."
            "partial_golden_postseal_namespace_amendment_verification.v1"
        ),
        "gate": ACCEPTED_GATE,
        "valid": True,
        "amendment_self_root_sha256": amendment["amendment_self_root_sha256"],
        "manifest_sha256": manifest_verification["manifest_sha256"],
        "manifest_self_root_sha256": manifest["manifest_self_root_sha256"],
        "manifest_verification_root_sha256": manifest_verification[
            "verification_root_sha256"
        ],
        "golden_root_sha256": manifest["golden_root_sha256"],
        "blocker_receipt_root_sha256": blocker["receipt_root_sha256"],
        "tombstone_sha256": identity["sha256"],
        "sealed_file_count": len(original_names),
        "current_namespace_file_count": len(current_names),
        "original_inventory_exact_at_seal": True,
        "current_inventory_exact_under_amendment": True,
        "writer_implementation_imported": False,
        "verifier_source_sha256": _file_digest(Path(__file__).resolve()),
        "economic_values_exposed": False,
    }
    return {**receipt_core, "verification_root_sha256": _root(receipt_core)}


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise PostSealAmendmentVerificationError("verification_output_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(_canonical(value))
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blocker-receipt", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    receipt = verify_postseal_namespace_amendment(
        amendment_path=args.amendment,
        manifest_path=args.manifest,
        blocker_receipt_path=args.blocker_receipt,
        git_root=args.git_root,
    )
    _atomic_write(args.output, receipt)
    print(
        json.dumps(
            {
                "gate": receipt["gate"],
                "verification_root_sha256": receipt["verification_root_sha256"],
                "economic_values_exposed": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
