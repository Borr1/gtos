"""Prospective byte authority for the fixed parity verifier import closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research_infra.replay_acceleration_immutable_evidence import (
    ImmutableEvidenceError,
    RegularFileIdentity,
    assert_regular_identity,
    read_regular_nofollow,
)


SCHEMA = "gtos.replay_acceleration.fixed_verifier_code_authority.v1"
MODULE_FILES = (
    (
        "src.research_infra.replay_acceleration_real_parity_verifier",
        "replay_acceleration_real_parity_verifier.py",
    ),
    (
        "src.research_infra.replay_acceleration_partial_golden_verifier",
        "replay_acceleration_partial_golden_verifier.py",
    ),
    (
        "src.research_infra.replay_acceleration_streaming_archive_verifier",
        "replay_acceleration_streaming_archive_verifier.py",
    ),
    (
        "src.research_infra.replay_acceleration_partial_golden_successor_authority",
        "replay_acceleration_partial_golden_successor_authority.py",
    ),
    (
        "src.research_infra.replay_acceleration_partial_golden_successor",
        "replay_acceleration_partial_golden_successor.py",
    ),
    (
        "src.research_infra.replay_acceleration_contract_split",
        "replay_acceleration_contract_split.py",
    ),
    (
        "src.research_infra.replay_acceleration_fixed_verifier_authority",
        "replay_acceleration_fixed_verifier_authority.py",
    ),
    (
        "src.research_infra.replay_acceleration_immutable_evidence",
        "replay_acceleration_immutable_evidence.py",
    ),
)


class FixedVerifierAuthorityError(RuntimeError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _root(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_fixed_verifier_code_authority(
    module_directory: Path,
) -> tuple[dict[str, Any], dict[str, RegularFileIdentity]]:
    directory = Path(module_directory).absolute()
    files: list[dict[str, Any]] = []
    identities: dict[str, RegularFileIdentity] = {}
    try:
        for module, filename in MODULE_FILES:
            path = directory / filename
            raw, identity = read_regular_nofollow(
                path,
                code="fixed_verifier_code_authority_invalid",
            )
            files.append(
                {
                    "module": module,
                    "path": str(path),
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            identities[str(path)] = identity
    except ImmutableEvidenceError:
        raise FixedVerifierAuthorityError(
            "fixed_verifier_code_authority_invalid"
        ) from None
    core = {"schema": SCHEMA, "files": files}
    return (
        {**core, "authority_root_sha256": _root(core)},
        identities,
    )


def validate_fixed_verifier_code_authority(
    authority: Mapping[str, Any],
    *,
    module_directory: Path,
) -> dict[str, RegularFileIdentity]:
    expected, identities = build_fixed_verifier_code_authority(
        module_directory
    )
    if type(authority) is not dict or authority != expected:
        raise FixedVerifierAuthorityError(
            "fixed_verifier_code_authority_mismatch"
        )
    return identities


def assert_fixed_verifier_code_identity(
    identities: Mapping[str, RegularFileIdentity],
) -> None:
    try:
        for path, identity in identities.items():
            assert_regular_identity(
                Path(path),
                identity,
                code="fixed_verifier_code_identity_changed",
            )
    except ImmutableEvidenceError:
        raise FixedVerifierAuthorityError(
            "fixed_verifier_code_identity_changed"
        ) from None
