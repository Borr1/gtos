#!/usr/bin/env python3
"""Certify the sealed B7.5 January selection/sizing development matrix.

This is a window adapter over the byte-frozen June matrix analyzer.  It changes
only the sealed window controls and the resulting window disposition.  Every
June core namespace, binding, verifier, lifecycle, identity, economics,
stress, suppression, stability, and self-hash invariant remains authoritative.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
CORE_ANALYZER_PATH = ROUTE / "analyze_b7_5_selection_sizing_matrix.py"
CORE_ANALYZER_SHA256 = (
    "9fbfb6ee79e02b67c507ab7b373b38f777d84dae569f352710d55183f9920fd5"
)
CONTROL_PATH = ROUTE / "B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_WINDOW_CONTROL.json"
CONTROL_FILE_SHA256 = (
    "83cd158cc4ddeb0edb4a67c71637c56d711c0e92725c8335bc1a9da0ad238932"
)
CONTROL_SELF_HASH_SHA256 = (
    "cf2e0af3c338cdfa3a7db8b6de3ce1be25ce0b8287d5a74083d3c2f8ff601f34"
)
ANALYZER_PATH = Path(__file__).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    )


def load_frozen_core() -> Any:
    actual = sha256_file(CORE_ANALYZER_PATH)
    if actual != CORE_ANALYZER_SHA256:
        raise RuntimeError(
            "january_core_analyzer_sha256_mismatch:"
            f"expected={CORE_ANALYZER_SHA256}:actual={actual}"
        )
    module_name = "b7_5_june_matrix_core_for_development_january"
    spec = importlib.util.spec_from_file_location(module_name, CORE_ANALYZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("january_core_analyzer_import_spec_invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CORE = load_frozen_core()


def load_sealed_window_control() -> dict[str, Any]:
    actual_file_hash = sha256_file(CONTROL_PATH)
    if actual_file_hash != CONTROL_FILE_SHA256:
        raise RuntimeError(
            "january_window_control_sha256_mismatch:"
            f"expected={CONTROL_FILE_SHA256}:actual={actual_file_hash}"
        )
    payload = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("january_window_control_not_object")
    candidate = copy.deepcopy(payload)
    self_hash = candidate.get("self_hash")
    if not isinstance(self_hash, dict):
        raise RuntimeError("january_window_control_self_hash_missing")
    embedded = self_hash.pop("sha256", None)
    if (
        embedded != CONTROL_SELF_HASH_SHA256
        or CORE.stable_sha256(candidate) != CONTROL_SELF_HASH_SHA256
    ):
        raise RuntimeError("january_window_control_self_hash_invalid")
    return payload


WINDOW_CONTROL = load_sealed_window_control()
WINDOW = WINDOW_CONTROL["window"]
PROTOCOL_WINDOW_BINDING = WINDOW_CONTROL["protocol_window_binding"]
CONTRACT_WINDOW_BINDING = WINDOW_CONTROL["decision_contract_window_binding"]
SOURCE_AUTHORITY_BINDING = WINDOW_CONTROL["source_authority_amendment_binding"]
NAMESPACE = WINDOW_CONTROL["namespace"]
WINDOW_NEUTRAL = WINDOW_CONTROL["window_neutral_bindings"]
AUTHORIZATION = WINDOW_CONTROL["authorization_boundary"]
COLD_READER_BINDING = WINDOW_NEUTRAL["cold_evidence_reader"]

DENOMINATOR_ROUTE = REPO_ROOT / NAMESPACE["artifact_root"]
PROTOCOL_PATH = REPO_ROOT / WINDOW_NEUTRAL["protocol"]["path"]
PREDECESSOR_CONTRACT_PATH = (
    REPO_ROOT / WINDOW_NEUTRAL["decision_contract"]["path"]
)
CONTRACT_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
CONTRACT_FILE_SHA256 = (
    "51becc82fc9668352f4e054df516c415fb51d9a34f17ac2cc0a3167812da374b"
)
CONTRACT_SELF_HASH_SHA256 = (
    "f0d01052bdf3c84bfab128acbc5447b9ac52b73abb33d4142bd9decbf2e2e9c8"
)
EXECUTION_SEAL_PATH = (
    REPO_ROOT
    / ".hermes/evidence/phase-d/"
    "january-post-acceleration-source-20260723T225928Z/"
    "JANUARY_EXECUTION_SEAL_R3.json"
)
EXECUTION_SEAL_FILE_SHA256 = (
    "fe09e0e9d72fce92673486257102a1c9c8d3960b3f745a358b314fefc371c90e"
)
EXECUTION_SEAL_ROOT_SHA256 = (
    "ccd06020b64e3b0d5ad5c5c6b90bf23e752f03c247606503b98c42e8b5eddc21"
)
POST_COLD_VERIFICATION_BINDINGS = {
    "S0R0": {
        "path": (
            ".hermes/receipts/phase-d/"
            "JANUARY_S0R0_R2_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json"
        ),
        "file_sha256": (
            "1cc19c0ca3d56c750319ec6394cefd92f3d9e1690ccf375a61c73075407e8b14"
        ),
        "verification_root_sha256": (
            "43e5614bd9383a39c3fa83a9c0270b8e27f7fb6c86132354796c25835852f98f"
        ),
        "arm_receipt_file_sha256": (
            "5692b101bea0e85cc4ff4b45c3fa47e8b126b785b1d47ed0a678c95371c2355b"
        ),
        "arm_receipt_root_sha256": (
            "106404f66362fcada38b8e31a4403ae0ede550946e25c48f976651e9aab626a9"
        ),
    },
    "S1R0": {
        "path": (
            ".hermes/receipts/phase-d/"
            "JANUARY_S1R0_R1_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json"
        ),
        "file_sha256": (
            "5ffc2df0066d6799a4eff4b8d1219aba8f9dc908fc7d2aec745e87b9040ea42a"
        ),
        "verification_root_sha256": (
            "22f1bd1e2fd6e44ca6e89af15ca7138873ace9392e074e2df204a13670f90b9f"
        ),
        "arm_receipt_file_sha256": (
            "8089593f6a442fd16c886e4248ef8f6366e099a9c1c9714cee8642da4e4d8d69"
        ),
        "arm_receipt_root_sha256": (
            "c4cf1e8b8f40712717907e7f52d81f6de8326f7cd743e8a13318f902c24f2307"
        ),
    },
    "S0R1": {
        "path": (
            ".hermes/receipts/phase-d/"
            "JANUARY_S0R1_R1_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json"
        ),
        "file_sha256": (
            "578ed1917cc5cb7518ad4658b4ffc717934f71360ec05be06a490a71598b34ab"
        ),
        "verification_root_sha256": (
            "486a510806985f6dbdb8d68e430a58112fbd77e3c3c21a55703527c3fba3f577"
        ),
        "arm_receipt_file_sha256": (
            "155a2765ce9b1dd61d2241f421a78441145ef33c778b2fbdf9e93eaffd2323d8"
        ),
        "arm_receipt_root_sha256": (
            "8dd877b6776cc8bff478e572c31a94d930e84cc2faa41c24c609d5b03cb506c3"
        ),
    },
    "S1R1": {
        "path": (
            ".hermes/receipts/phase-d/"
            "JANUARY_S1R1_R1_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json"
        ),
        "file_sha256": (
            "6b7a21b16c2d9b8d5dd4281e45aa478de8f2b2f1fce69be3a2d606fd1d41444a"
        ),
        "verification_root_sha256": (
            "12dda195a899d811321f7bf6e4e2793cd185390b1b50d52d54ded49ea6f7dc1a"
        ),
        "arm_receipt_file_sha256": (
            "2d52eda17809d29f4d23bb07c04653e6881e2c1a2797836307a0180470c80ce3"
        ),
        "arm_receipt_root_sha256": (
            "1ea8319032cdcb360f97b581af14eb4d32963d48064f0776cdc47d6b61c78bee"
        ),
    },
}
SOURCE_AUTHORITY_AMENDMENT_PATH = REPO_ROOT / SOURCE_AUTHORITY_BINDING["path"]
COLD_EVIDENCE_READER_PATH = REPO_ROOT / COLD_READER_BINDING["path"]
OUTPUT_PATH = REPO_ROOT / NAMESPACE["output_path"]
WINDOW_ID = str(WINDOW["window_id"])
WINDOW_ROLE = str(WINDOW["role"])
WINDOW_START = str(WINDOW["start"])
WINDOW_END = str(WINDOW["end"])
WINDOW_END_EXCLUSIVE = "2026-02-01"
SOURCE_PLAN_SHA256 = str(WINDOW["source_plan_digest_sha256"])
PROTOCOL_SOURCE_PLAN_SHA256 = str(
    WINDOW["protocol_source_plan_digest_sha256"]
)
NEXT_PROTOCOL_WINDOW = str(AUTHORIZATION["valid_matrix_authorizes_only"])
ARM_ORDER = tuple(NAMESPACE["arm_order"])
JANUARY_PREFIXES = dict(NAMESPACE["prefixes"])
POST_ACCELERATION_ROLE_SUFFIXES = {
    role: f"_{suffix}"
    for role, suffix in CORE.NAMESPACE_SUFFIXES.items()
}
POST_ACCELERATION_JSONL_ROLES = tuple(
    role
    for role, suffix in POST_ACCELERATION_ROLE_SUFFIXES.items()
    if suffix.endswith(".jsonl")
)
POST_ACCELERATION_JSON_ROLES = tuple(
    role
    for role, suffix in POST_ACCELERATION_ROLE_SUFFIXES.items()
    if suffix.endswith(".json")
)

PROTOCOL_FILE_SHA256 = str(WINDOW_NEUTRAL["protocol"]["file_sha256"])
SOURCE_AUTHORITY_AMENDMENT_FILE_SHA256 = str(
    SOURCE_AUTHORITY_BINDING["file_sha256"]
)
SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256 = str(
    SOURCE_AUTHORITY_BINDING["self_hash_sha256"]
)
COLD_EVIDENCE_READER_FILE_SHA256 = str(
    COLD_READER_BINDING["file_sha256"]
)


def _load_bound_json(
    path: Path,
    expected_file_sha256: str,
    *,
    label: str,
) -> dict[str, Any]:
    actual = sha256_file(path)
    if actual != expected_file_sha256:
        raise RuntimeError(
            f"{label}_sha256_mismatch:"
            f"expected={expected_file_sha256}:actual={actual}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label}_not_object")
    return payload


POST_ACCELERATION_CONTRACT = _load_bound_json(
    CONTRACT_PATH,
    CONTRACT_FILE_SHA256,
    label="january_post_acceleration_contract",
)
EXECUTION_SEAL = _load_bound_json(
    EXECUTION_SEAL_PATH,
    EXECUTION_SEAL_FILE_SHA256,
    label="january_execution_seal",
)

_post_contract_for_hash = copy.deepcopy(POST_ACCELERATION_CONTRACT)
_post_contract_self_hash = _post_contract_for_hash.get("self_hash")
if not isinstance(_post_contract_self_hash, dict):
    raise RuntimeError("january_post_acceleration_contract_self_hash_missing")
_post_contract_embedded_hash = _post_contract_self_hash.pop("sha256", None)
if (
    _post_contract_embedded_hash != CONTRACT_SELF_HASH_SHA256
    or CORE.stable_sha256(_post_contract_for_hash)
    != CONTRACT_SELF_HASH_SHA256
):
    raise RuntimeError("january_post_acceleration_contract_self_hash_invalid")

_execution_seal_for_hash = copy.deepcopy(EXECUTION_SEAL)
_execution_seal_embedded_root = _execution_seal_for_hash.pop(
    "execution_seal_root_sha256",
    None,
)
if (
    _execution_seal_embedded_root != EXECUTION_SEAL_ROOT_SHA256
    or CORE.stable_sha256(_execution_seal_for_hash)
    != EXECUTION_SEAL_ROOT_SHA256
):
    raise RuntimeError("january_execution_seal_root_invalid")

_post_contract_arms = {
    str(row.get("arm_id")): row
    for row in POST_ACCELERATION_CONTRACT.get(
        "factorial_contract",
        {},
    ).get("arms", [])
    if isinstance(row, dict)
}
_execution_seal_arms = EXECUTION_SEAL.get("arms")
if (
    POST_ACCELERATION_CONTRACT.get("schema")
    != "gtos.b7_5.post_acceleration_decision_contract.v1"
    or POST_ACCELERATION_CONTRACT.get("status")
    != "SEALED_POST_ACCELERATION_REPLAY_FREE_DECISION_CONTRACT_VALID"
    or POST_ACCELERATION_CONTRACT.get("valid") is not True
    or EXECUTION_SEAL.get("schema")
    != "gtos.b7_5.post_acceleration_execution_seal.v1"
    or EXECUTION_SEAL.get("status")
    != "SEALED_POST_ACCELERATION_EXECUTION_CONTRACT_VALID"
    or EXECUTION_SEAL.get("valid") is not True
    or not isinstance(_execution_seal_arms, dict)
    or set(_post_contract_arms) != set(ARM_ORDER)
    or set(_execution_seal_arms) != set(ARM_ORDER)
):
    raise RuntimeError("january_post_acceleration_authority_shape_invalid")

COMMON_EXECUTION_INPUT_SHA256 = str(
    POST_ACCELERATION_CONTRACT["input_bindings"][
        "common_execution_input_digest_sha256"
    ]
)
PROTOCOL_ECONOMICS_SHA256 = str(
    POST_ACCELERATION_CONTRACT["protocol_economics_digest_sha256"]
)
NEUTRAL_SELECTION_SEED_SHA256 = str(
    POST_ACCELERATION_CONTRACT["factorial_contract"][
        "neutral_selection_seed_sha256"
    ]
)
ARM_FINGERPRINTS = {
    arm_id: str(_post_contract_arms[arm_id]["arm_fingerprint_sha256"])
    for arm_id in ARM_ORDER
}
BINDING_PAYLOADS = {
    arm_id: str(
        _execution_seal_arms[arm_id]["factorial_binding_payload_sha256"]
    )
    for arm_id in ARM_ORDER
}
SHARED_EXECUTION_CONTRACTS = {
    arm_id: str(
        _execution_seal_arms[arm_id][
            "shared_execution_contract_digest_sha256"
        ]
    )
    for arm_id in ARM_ORDER
}
EXACT_PROFILE_CONFIG_ROOTS = {
    arm_id: {
        str(NAMESPACE["expected_profile"]): str(
            _execution_seal_arms[arm_id][
                "exact_profile_config_root_sha256"
            ]
        )
    }
    for arm_id in ARM_ORDER
}
_risk_profile_inputs = [
    row
    for row in POST_ACCELERATION_CONTRACT["input_bindings"][
        "common_behavior_inputs"
    ]
    if isinstance(row, dict) and row.get("input_id") == "ftmo_risk_profile"
]
if len(_risk_profile_inputs) != 1:
    raise RuntimeError("january_exact_risk_profile_binding_missing")
EXACT_RISK_PROFILE_BINDINGS = {
    str(NAMESPACE["expected_profile"]): {
        "path": str(_risk_profile_inputs[0]["path"]),
        "sha256": str(_risk_profile_inputs[0]["sha256"]),
    }
}
DENOMINATOR = dict(POST_ACCELERATION_CONTRACT["denominator"])
MATCHED_RISK = dict(POST_ACCELERATION_CONTRACT["matched_risk"])
THRESHOLDS = dict(POST_ACCELERATION_CONTRACT["thresholds"])
CONTRACT_WINDOW_BINDING = next(
    row
    for row in POST_ACCELERATION_CONTRACT["window_source_plan_bindings"]
    if row.get("window_id") == WINDOW_ID
)

if (
    DENOMINATOR != WINDOW_NEUTRAL["denominator"]
    or MATCHED_RISK != WINDOW_NEUTRAL["matched_risk"]
    or {
        key: THRESHOLDS[key]
        for key in (
            "minimum_scoreable_risk_coverage",
            "maximum_arm_scoreability_gap",
            "symmetric_cash_per_risk_dollar_materiality",
        )
    }
    != {
        key: WINDOW_NEUTRAL["thresholds"][key]
        for key in (
            "minimum_scoreable_risk_coverage",
            "maximum_arm_scoreability_gap",
            "symmetric_cash_per_risk_dollar_materiality",
        )
    }
):
    raise RuntimeError("january_post_acceleration_economics_drift")


def load_frozen_cold_evidence_reader() -> Any:
    actual = sha256_file(COLD_EVIDENCE_READER_PATH)
    if actual != COLD_EVIDENCE_READER_FILE_SHA256:
        raise RuntimeError(
            "january_cold_evidence_reader_sha256_mismatch:"
            f"expected={COLD_EVIDENCE_READER_FILE_SHA256}:actual={actual}"
        )
    module_name = "b7_5_cold_evidence_for_development_january"
    spec = importlib.util.spec_from_file_location(
        module_name,
        COLD_EVIDENCE_READER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("january_cold_evidence_reader_import_spec_invalid")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if (
        module.ARCHIVE_SCHEMA != COLD_READER_BINDING["archive_schema"]
        or module.ARCHIVE_PASS_STATUS
        != COLD_READER_BINDING["archive_pass_status"]
        or not hasattr(module, "RawOrColdResolver")
        or not hasattr(module, "ColdEvidenceError")
    ):
        raise RuntimeError("january_cold_evidence_reader_contract_divergent")
    return module


COLD_EVIDENCE = load_frozen_cold_evidence_reader()

if (
    ARM_ORDER != CORE.ARM_ORDER
    or NAMESPACE["required_suffixes"] != CORE.NAMESPACE_SUFFIXES
    or set(ARM_FINGERPRINTS) != set(ARM_ORDER)
    or set(BINDING_PAYLOADS) != set(ARM_ORDER)
    or set(SHARED_EXECUTION_CONTRACTS) != set(ARM_ORDER)
):
    raise RuntimeError("january_window_control_core_surface_divergent")

JANUARY_FROZEN = CORE.FrozenBindings(
    source_plan_sha256=SOURCE_PLAN_SHA256,
    contract_file_sha256=CONTRACT_FILE_SHA256,
    contract_self_hash_sha256=CONTRACT_SELF_HASH_SHA256,
    common_execution_input_sha256=COMMON_EXECUTION_INPUT_SHA256,
    protocol_file_sha256=PROTOCOL_FILE_SHA256,
    protocol_economics_digest_sha256=PROTOCOL_ECONOMICS_SHA256,
    neutral_selection_seed_sha256=NEUTRAL_SELECTION_SEED_SHA256,
    arm_fingerprints=ARM_FINGERPRINTS,
    binding_payloads=BINDING_PAYLOADS,
    shared_execution_contracts=SHARED_EXECUTION_CONTRACTS,
    denominator=DENOMINATOR,
    matched_risk=MATCHED_RISK,
    expected_candidate_count=int(NAMESPACE["expected_candidate_count"]),
    expected_decision_count=int(NAMESPACE["expected_decision_count"]),
    expected_scorecard_count=int(NAMESPACE["expected_scorecard_count"]),
    expected_symbol_count=int(NAMESPACE["expected_symbol_count"]),
    expected_profile=str(NAMESPACE["expected_profile"]),
    minimum_scoreable_risk_coverage=float(
        THRESHOLDS["minimum_scoreable_risk_coverage"]
    ),
    maximum_arm_scoreability_gap=float(
        THRESHOLDS["maximum_arm_scoreability_gap"]
    ),
    materiality=float(THRESHOLDS["symmetric_cash_per_risk_dollar_materiality"]),
)


class JanuaryAuditError(CORE.MatrixAuditError):
    """Fail-closed January production-control error."""


@dataclass(frozen=True)
class AnalyzerConfig:
    artifact_root: Path = DENOMINATOR_ROUTE
    protocol_path: Path = PROTOCOL_PATH
    contract_path: Path = CONTRACT_PATH
    source_authority_amendment_path: Path = SOURCE_AUTHORITY_AMENDMENT_PATH
    control_path: Path = CONTROL_PATH
    output_path: Path = OUTPUT_PATH
    prefixes: Mapping[str, str] = field(
        default_factory=lambda: dict(JANUARY_PREFIXES)
    )
    frozen: Any = JANUARY_FROZEN


DEFAULT_CONFIG = AnalyzerConfig()
_CORE_ADAPTER_LOCK = threading.RLock()
_IDENTITY_TIME_RE = re.compile(
    r"@@(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))"
)


@dataclass(frozen=True)
class LogicalStatProjection:
    """Minimal stable stat surface for one cold logical JSONL path."""

    st_dev: int
    st_ino: int
    st_size: int
    st_mtime_ns: int
    st_blocks: int
    st_mode: int = 0o100444

    @property
    def st_mtime(self) -> float:
        return self.st_mtime_ns / 1_000_000_000


class RawOrColdLogicalPath:
    """Path-like logical identity backed by the frozen raw-or-cold reader."""

    def __init__(self, logical_path: Path, resolver: Any):
        self.logical_path = Path(os.path.abspath(logical_path))
        self.resolver = resolver
        self._initial_mode: str | None = None
        self._initial_storage_token: Any = None
        self._cold_metadata: dict[str, Any] | None = None

    def __fspath__(self) -> str:
        return str(self.logical_path)

    def __str__(self) -> str:
        return str(self.logical_path)

    def __repr__(self) -> str:
        return f"RawOrColdLogicalPath({self.logical_path!r})"

    def __hash__(self) -> int:
        return hash(self.logical_path)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RawOrColdLogicalPath):
            return self.logical_path == other.logical_path
        try:
            return self.logical_path == Path(os.fspath(other))  # type: ignore[arg-type]
        except TypeError:
            return False

    def __iter__(self) -> Iterator[Mapping[str, Any]]:
        """Yield mapping rows from a fresh logical stream on every iteration."""

        with self.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                if isinstance(row, Mapping):
                    yield row

    @property
    def name(self) -> str:
        return self.logical_path.name

    @property
    def parent(self) -> Path:
        return self.logical_path.parent

    @property
    def suffix(self) -> str:
        return self.logical_path.suffix

    def resolve(self, strict: bool = False) -> Path:
        return self.logical_path.resolve(strict=strict)

    def _mode(self) -> str:
        mode = str(self.resolver.mode(self.logical_path))
        if self._initial_mode is None:
            self._initial_mode = mode
        elif mode != self._initial_mode:
            raise COLD_EVIDENCE.ColdEvidenceError(
                "logical_evidence_storage_mode_changed:"
                f"{self.logical_path}:{self._initial_mode}->{mode}"
            )
        return mode

    @staticmethod
    def _raw_token(observed: Any) -> list[Any]:
        return [
            "raw",
            int(observed.st_dev),
            int(observed.st_ino),
            int(observed.st_size),
            int(observed.st_mtime_ns),
        ]

    @staticmethod
    def _cold_token(metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "storage_mode": metadata.get("storage_mode"),
            "storage_identity": copy.deepcopy(metadata.get("storage_identity")),
            "manifest_file_sha256": metadata.get("manifest_file_sha256"),
            "manifest_self_hash_sha256": metadata.get(
                "manifest_self_hash_sha256"
            ),
            "logical_bytes": metadata.get("logical_bytes"),
            "sha256": metadata.get("sha256"),
            "physical_line_count": metadata.get("physical_line_count"),
            "json_object_row_count": metadata.get("json_object_row_count"),
            "blank_line_count": metadata.get("blank_line_count"),
            "ends_with_lf": metadata.get("ends_with_lf"),
        }

    def _cold_logical_metadata(self) -> dict[str, Any]:
        if self._cold_metadata is None:
            metadata = self.resolver.logical_metadata(
                self.logical_path,
                verify_full=False,
                parse_json=False,
            )
            self._cold_metadata = copy.deepcopy(dict(metadata))
            self._initial_storage_token = self._cold_token(metadata)
        return self._cold_metadata

    def exists(self) -> bool:
        exists = bool(self.resolver.exists(self.logical_path))
        if exists:
            self._mode()
        return exists

    def is_file(self) -> bool:
        return self.exists()

    def is_symlink(self) -> bool:
        if not self.resolver.exists(self.logical_path):
            return False
        self._mode()
        return False

    def stat(self, *, follow_symlinks: bool = True) -> Any:
        del follow_symlinks
        mode = self._mode()
        if mode == "raw":
            observed = self.logical_path.stat()
            token = self._raw_token(observed)
            if self._initial_storage_token is None:
                self._initial_storage_token = token
            return observed
        metadata = self._cold_logical_metadata()
        identity = CORE.stable_sha256(self._cold_token(metadata))
        return LogicalStatProjection(
            st_dev=int(identity[0:16], 16),
            st_ino=int(identity[16:32], 16),
            st_size=int(metadata["logical_bytes"]),
            st_mtime_ns=int(identity[32:48], 16),
            st_blocks=max(1, (int(metadata["logical_bytes"]) + 511) // 512),
        )

    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> Any:
        del buffering
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise COLD_EVIDENCE.ColdEvidenceError(
                f"logical_evidence_write_forbidden:{self.logical_path}:{mode}"
            )
        self._mode()
        if mode == "rb":
            if encoding is not None or errors is not None or newline is not None:
                raise ValueError("binary mode does not take text arguments")
            return self.resolver.open_binary(self.logical_path)
        if mode not in {"r", "rt"}:
            raise ValueError(f"unsupported logical evidence mode: {mode}")
        if newline is not None:
            raise ValueError("custom newline mode is not supported")
        return self.resolver.open_text(
            self.logical_path,
            encoding=encoding or "utf-8",
            errors=errors or "strict",
        )

    def read_bytes(self) -> bytes:
        with self.open("rb") as handle:
            return handle.read()

    def read_text(
        self,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        with self.open(
            "r",
            encoding=encoding or "utf-8",
            errors=errors or "strict",
        ) as handle:
            return str(handle.read())

    def full_metadata(self) -> dict[str, Any]:
        mode = self._mode()
        metadata = self.resolver.logical_metadata(
            self.logical_path,
            verify_full=True,
            parse_json=True,
        )
        if mode == "raw":
            final_token: Any = copy.deepcopy(metadata.get("storage_identity"))
            initial = self._initial_storage_token
            if isinstance(initial, list) and initial and initial[0] == "raw":
                initial = initial[1:]
        else:
            final_token = self._cold_token(metadata)
            initial = self._initial_storage_token
        if initial is None or initial != final_token:
            raise COLD_EVIDENCE.ColdEvidenceError(
                f"logical_evidence_storage_identity_changed:{self.logical_path}"
            )
        return copy.deepcopy(dict(metadata))


class NamespaceStorageSession:
    """Resolve and attest every January JSONL namespace as raw XOR cold."""

    def __init__(self, config: AnalyzerConfig):
        self.resolver = COLD_EVIDENCE.RawOrColdResolver()
        self._arm_by_prefix = {
            prefix: arm_id for arm_id, prefix in config.prefixes.items()
        }
        self._paths: dict[str, tuple[str, str, RawOrColdLogicalPath]] = {}

    def namespace_paths(
        self,
        original: Any,
        root: Path,
        prefix: str,
    ) -> dict[str, Any]:
        paths = original(root, prefix)
        arm_id = self._arm_by_prefix.get(prefix)
        if arm_id is None:
            raise JanuaryAuditError(
                f"cold_evidence_unknown_namespace_prefix:{prefix}"
            )
        resolved: dict[str, Any] = {}
        for kind, path in paths.items():
            if path.suffix != ".jsonl":
                resolved[kind] = path
                continue
            key = str(Path(os.path.abspath(path)))
            existing = self._paths.get(key)
            if existing is None:
                facade = RawOrColdLogicalPath(path, self.resolver)
                self._paths[key] = (arm_id, kind, facade)
            else:
                prior_arm, prior_kind, facade = existing
                if (prior_arm, prior_kind) != (arm_id, kind):
                    raise JanuaryAuditError(
                        f"cold_evidence_logical_path_collision:{key}"
                    )
            resolved[kind] = facade
        return resolved

    def audit_record(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        mode_counts: dict[str, int] = {}
        for logical_path in sorted(self._paths):
            arm_id, kind, facade = self._paths[logical_path]
            metadata = facade.full_metadata()
            storage_mode = str(metadata.get("storage_mode"))
            mode_counts[storage_mode] = mode_counts.get(storage_mode, 0) + 1
            storage_identity = metadata.pop("storage_identity", None)
            full_reverified = bool(
                storage_mode == "raw"
                or metadata.get("full_logical_reverification") is True
            )
            entries.append(
                {
                    "arm_id": arm_id,
                    "artifact": kind,
                    **metadata,
                    "storage_identity_sha256": CORE.stable_sha256(
                        storage_identity
                    ),
                    "full_logical_reverification": full_reverified,
                }
            )
        expected_count = len(ARM_ORDER) * sum(
            str(suffix).endswith(".jsonl")
            for suffix in CORE.NAMESPACE_SUFFIXES.values()
        )
        all_full = bool(
            entries
            and all(row["full_logical_reverification"] for row in entries)
        )
        valid = bool(len(entries) == expected_count and all_full)
        if not valid:
            raise JanuaryAuditError(
                "development_january_namespace_storage_attestation_invalid:"
                f"expected={expected_count}:actual={len(entries)}:"
                f"all_full={all_full}"
            )
        return {
            "schema": (
                "gtos.b7_5.selection_sizing.raw_or_cold_namespace_resolution.v1"
            ),
            "status": "PASS_RAW_OR_COLD_NAMESPACE_LOGICAL_IDENTITY_VERIFIED",
            "valid": True,
            "reader": {
                "path": str(COLD_EVIDENCE_READER_PATH),
                "file_sha256": COLD_EVIDENCE_READER_FILE_SHA256,
                "archive_schema": COLD_READER_BINDING["archive_schema"],
                "archive_pass_status": COLD_READER_BINDING[
                    "archive_pass_status"
                ],
                "resolution_contract": COLD_READER_BINDING[
                    "resolution_contract"
                ],
            },
            "expected_jsonl_artifact_count": expected_count,
            "verified_jsonl_artifact_count": len(entries),
            "storage_mode_counts": mode_counts,
            "all_logical_bytes_hashes_rows_and_newlines_reverified": all_full,
            "entries": entries,
        }


def _path_equal(left: Path, right: Path) -> bool:
    return Path(os.path.abspath(left)) == Path(os.path.abspath(right))


def production_mode(config: AnalyzerConfig) -> bool:
    return config.frozen == JANUARY_FROZEN


def validate_production_config(config: AnalyzerConfig) -> None:
    expected_paths = {
        "artifact_root": DENOMINATOR_ROUTE,
        "protocol": PROTOCOL_PATH,
        "decision_contract": CONTRACT_PATH,
        "source_authority_amendment_r3": SOURCE_AUTHORITY_AMENDMENT_PATH,
        "window_control": CONTROL_PATH,
        "output": OUTPUT_PATH,
    }
    actual_paths = {
        "artifact_root": config.artifact_root,
        "protocol": config.protocol_path,
        "decision_contract": config.contract_path,
        "source_authority_amendment_r3": (
            config.source_authority_amendment_path
        ),
        "window_control": config.control_path,
        "output": config.output_path,
    }
    failures: list[str] = []
    if config.frozen != JANUARY_FROZEN:
        failures.append("frozen_bindings_mismatch")
    if dict(config.prefixes) != JANUARY_PREFIXES:
        failures.append("exact_january_prefix_map_required")
    for label, expected in expected_paths.items():
        actual = actual_paths[label]
        if not _path_equal(actual, expected):
            failures.append(f"{label}:sealed_path_mismatch")
            continue
        if actual.is_symlink():
            failures.append(f"{label}:symlink_forbidden")
        if label == "artifact_root":
            if not actual.is_dir():
                failures.append(f"{label}:missing")
        elif label != "output" and not actual.is_file():
            failures.append(f"{label}:missing")
    if failures:
        raise JanuaryAuditError(
            "january_production_config_invalid:" + "|".join(failures)
        )


def _read_json_object(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload, record = CORE.read_json_object(path)
    return payload, record


def _verify_embedded_self_hash(payload: Mapping[str, Any]) -> bool:
    candidate = copy.deepcopy(dict(payload))
    self_hash = candidate.get("self_hash")
    if not isinstance(self_hash, dict):
        return False
    expected = self_hash.pop("sha256", None)
    return isinstance(expected, str) and expected == CORE.stable_sha256(candidate)


def validate_execution_seal_bindings(
    seal: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = copy.deepcopy(dict(seal))
    embedded_root = candidate.pop("execution_seal_root_sha256", None)
    decision_binding = seal.get("decision_contract_binding")
    decision_binding = (
        decision_binding if isinstance(decision_binding, Mapping) else {}
    )
    source_binding = seal.get("source_authority_binding")
    source_binding = (
        source_binding if isinstance(source_binding, Mapping) else {}
    )
    pack_binding = seal.get("prepared_day_pack_binding")
    pack_binding = (
        pack_binding if isinstance(pack_binding, Mapping) else {}
    )
    arms = seal.get("arms")
    arms = arms if isinstance(arms, Mapping) else {}
    actual_arms = {
        arm_id: {
            "arm_fingerprint_sha256": row.get(
                "arm_fingerprint_sha256"
            ),
            "factorial_binding_payload_sha256": row.get(
                "factorial_binding_payload_sha256"
            ),
            "shared_execution_contract_digest_sha256": row.get(
                "shared_execution_contract_digest_sha256"
            ),
            "exact_profile_config_root_sha256": row.get(
                "exact_profile_config_root_sha256"
            ),
        }
        for arm_id, row in arms.items()
        if isinstance(row, Mapping)
    }
    expected_arms = {
        arm_id: {
            "arm_fingerprint_sha256": ARM_FINGERPRINTS[arm_id],
            "factorial_binding_payload_sha256": BINDING_PAYLOADS[arm_id],
            "shared_execution_contract_digest_sha256": (
                SHARED_EXECUTION_CONTRACTS[arm_id]
            ),
            "exact_profile_config_root_sha256": (
                EXACT_PROFILE_CONFIG_ROOTS[arm_id][
                    str(NAMESPACE["expected_profile"])
                ]
            ),
        }
        for arm_id in ARM_ORDER
    }
    checks = {
        "schema": (
            seal.get("schema"),
            "gtos.b7_5.post_acceleration_execution_seal.v1",
        ),
        "status": (
            seal.get("status"),
            "SEALED_POST_ACCELERATION_EXECUTION_CONTRACT_VALID",
        ),
        "valid": (seal.get("valid"), True),
        "execution_seal_root": (
            embedded_root,
            EXECUTION_SEAL_ROOT_SHA256,
        ),
        "execution_seal_root_recomputed": (
            CORE.stable_sha256(candidate),
            EXECUTION_SEAL_ROOT_SHA256,
        ),
        "decision_contract_file_sha256": (
            decision_binding.get("file_sha256"),
            CONTRACT_FILE_SHA256,
        ),
        "decision_contract_self_hash": (
            decision_binding.get("self_hash_sha256"),
            CONTRACT_SELF_HASH_SHA256,
        ),
        "decision_contract_schema": (
            decision_binding.get("schema"),
            contract.get("schema"),
        ),
        "decision_contract_status": (
            decision_binding.get("status"),
            contract.get("status"),
        ),
        "window_binding": (
            seal.get("window_binding"),
            CONTRACT_WINDOW_BINDING,
        ),
        "source_plan_digest": (
            source_binding.get("source_plan_digest_sha256"),
            SOURCE_PLAN_SHA256,
        ),
        "source_binding_root": (
            source_binding.get("binding_root_sha256"),
            "a00fa9241e0792a0a74a202ed191134ddd0e8e2e8b4873cb847e72a556bf926f",
        ),
        "arm_bindings": (actual_arms, expected_arms),
        "all_four_shared_digests_unique": (
            seal.get("all_four_arm_shared_digests_unique"),
            True,
        ),
        "prepared_pack_arm_neutral": (
            pack_binding.get("arm_neutral"),
            True,
        ),
        "prepared_pack_factor_reads_forbidden": (
            pack_binding.get("factor_reads_forbidden"),
            True,
        ),
        "prepared_pack_bytes_authenticated": (
            pack_binding.get(
                "all_persisted_pack_bytes_authenticated_before_seal"
            ),
            True,
        ),
        "broker_mutation_enabled": (
            seal.get("broker_mutation_enabled"),
            False,
        ),
        "broker_live_authority": (
            seal.get("broker_live_authority"),
            False,
        ),
        "real_order_transmission_possible": (
            seal.get("real_order_transmission_possible"),
            False,
        ),
        "economic_values_exposed": (
            seal.get("economic_values_exposed"),
            False,
        ),
        "march_outcome_read": (seal.get("march_outcome_read"), False),
    }
    divergent = [
        label for label, (actual, expected) in checks.items()
        if actual != expected
    ]
    if divergent:
        raise JanuaryAuditError(
            "january_post_acceleration_execution_seal_divergent:"
            + "|".join(divergent)
        )
    return {
        "path": str(EXECUTION_SEAL_PATH),
        "file_sha256": EXECUTION_SEAL_FILE_SHA256,
        "execution_seal_root_sha256": EXECUTION_SEAL_ROOT_SHA256,
        "source_authority_binding_root_sha256": source_binding.get(
            "binding_root_sha256"
        ),
        "prepared_pack_authority_root_sha256": pack_binding.get(
            "authority_root_sha256"
        ),
        "all_four_arm_bindings_exact": True,
        "broker_live_authority": False,
        "real_order_transmission_possible": False,
    }


def validate_post_cold_verification_bindings() -> dict[str, Any]:
    records: dict[str, Any] = {}
    for arm_id in ARM_ORDER:
        binding = POST_COLD_VERIFICATION_BINDINGS[arm_id]
        path = REPO_ROOT / str(binding["path"])
        receipt = _load_bound_json(
            path,
            str(binding["file_sha256"]),
            label=f"january_{arm_id.lower()}_post_cold_verification",
        )
        receipt_for_hash = copy.deepcopy(receipt)
        embedded_root = receipt_for_hash.pop(
            "verification_root_sha256",
            None,
        )
        arm_receipt_binding = receipt.get("arm_receipt")
        arm_receipt_binding = (
            arm_receipt_binding
            if isinstance(arm_receipt_binding, Mapping)
            else {}
        )
        arm_receipt_path = Path(
            str(arm_receipt_binding.get("path") or "")
        )
        expected_arm_receipt_file = str(
            binding["arm_receipt_file_sha256"]
        )
        expected_arm_receipt_root = str(
            binding["arm_receipt_root_sha256"]
        )
        if (
            receipt.get("schema")
            != "gtos.b7_5.post_acceleration_arm_independent_verification.v1"
            or receipt.get("status")
            != "PASS_POST_ACCELERATION_ARM_ARTIFACTS_INDEPENDENTLY_VERIFIED"
            or receipt.get("arm_id") != arm_id
            or embedded_root != binding["verification_root_sha256"]
            or CORE.stable_sha256(receipt_for_hash) != embedded_root
            or receipt.get("all_logical_bytes_verified") is not True
            or receipt.get(
                "all_hashes_and_row_counts_match_producer_receipt"
            )
            is not True
            or receipt.get("broker_mutation_enabled") is not False
            or receipt.get("broker_live_authority") is not False
            or receipt.get("real_order_transmission_possible") is not False
            or receipt.get("window") != CONTRACT_WINDOW_BINDING
            or receipt.get("decision_contract", {}).get("file_sha256")
            != CONTRACT_FILE_SHA256
            or receipt.get("decision_contract", {}).get(
                "self_hash_sha256"
            )
            != CONTRACT_SELF_HASH_SHA256
            or receipt.get("execution_seal", {}).get("file_sha256")
            != EXECUTION_SEAL_FILE_SHA256
            or receipt.get("execution_seal", {}).get(
                "execution_seal_root_sha256"
            )
            != EXECUTION_SEAL_ROOT_SHA256
            or arm_receipt_binding.get("file_sha256")
            != expected_arm_receipt_file
            or arm_receipt_binding.get("receipt_root_sha256")
            != expected_arm_receipt_root
            or not arm_receipt_path.is_file()
            or sha256_file(arm_receipt_path) != expected_arm_receipt_file
        ):
            raise JanuaryAuditError(
                f"january_{arm_id.lower()}_post_cold_verification_divergent"
            )
        arm_receipt = json.loads(
            arm_receipt_path.read_text(encoding="utf-8")
        )
        arm_receipt_for_hash = copy.deepcopy(arm_receipt)
        arm_embedded_root = arm_receipt_for_hash.pop(
            "receipt_root_sha256",
            None,
        )
        artifact_inventory = arm_receipt.get("artifact_inventory")
        artifact_inventory = (
            artifact_inventory
            if isinstance(artifact_inventory, Mapping)
            else {}
        )
        artifact_inventory_for_hash = copy.deepcopy(
            dict(artifact_inventory)
        )
        artifact_inventory_root = artifact_inventory_for_hash.pop(
            "inventory_root_sha256",
            None,
        )
        producer_artifacts = artifact_inventory.get("artifacts")
        producer_artifacts = (
            producer_artifacts
            if isinstance(producer_artifacts, Mapping)
            else {}
        )
        output_prefix = arm_receipt.get("output_prefix")
        artifact_rows_valid = bool(
            set(producer_artifacts) == set(POST_ACCELERATION_ROLE_SUFFIXES)
        )
        if artifact_rows_valid:
            for role, suffix in POST_ACCELERATION_ROLE_SUFFIXES.items():
                artifact = producer_artifacts.get(role)
                if not isinstance(artifact, Mapping):
                    artifact_rows_valid = False
                    break
                expected_name = f"{str(output_prefix or '')}{suffix}"
                if (
                    artifact.get("path") != expected_name
                    or not isinstance(artifact.get("bytes"), int)
                    or isinstance(artifact.get("bytes"), bool)
                    or artifact.get("bytes", -1) < 0
                    or not is_sha256(artifact.get("sha256"))
                ):
                    artifact_rows_valid = False
                    break
                if role in POST_ACCELERATION_JSONL_ROLES and (
                    not isinstance(artifact.get("rows"), int)
                    or isinstance(artifact.get("rows"), bool)
                    or artifact.get("rows", -1) < 0
                ):
                    artifact_rows_valid = False
                    break
                if role in POST_ACCELERATION_JSON_ROLES and "rows" in artifact:
                    artifact_rows_valid = False
                    break
        ledger_counts = artifact_inventory.get("ledger_row_counts")
        expected_ledger_counts = {
            role: producer_artifacts.get(role, {}).get("rows")
            for role in POST_ACCELERATION_JSONL_ROLES
        }
        verification_pack = receipt.get("prepared_pack_authority")
        verification_pack = (
            verification_pack
            if isinstance(verification_pack, Mapping)
            else {}
        )
        producer_pack = arm_receipt.get("prepared_pack_authority")
        producer_pack = (
            producer_pack
            if isinstance(producer_pack, Mapping)
            else {}
        )
        seal_pack = EXECUTION_SEAL.get("prepared_day_pack_binding")
        seal_pack = seal_pack if isinstance(seal_pack, Mapping) else {}
        producer_pack_roots = producer_pack.get(
            "prepared_day_pack_roots"
        )
        if (
            arm_embedded_root != expected_arm_receipt_root
            or CORE.stable_sha256(arm_receipt_for_hash)
            != arm_embedded_root
            or arm_receipt.get("schema")
            != "gtos.b7_5.post_acceleration_arm_execution.v1"
            or arm_receipt.get("status")
            != "POST_ACCELERATION_ARM_EXECUTION_COMPLETE"
            or arm_receipt.get("arm_id") != arm_id
            or arm_receipt.get("arm_fingerprint_sha256")
            != ARM_FINGERPRINTS[arm_id]
            or arm_receipt.get(
                "shared_execution_contract_digest_sha256"
            )
            != SHARED_EXECUTION_CONTRACTS[arm_id]
            or arm_receipt.get("decision_contract_self_hash_sha256")
            != CONTRACT_SELF_HASH_SHA256
            or arm_receipt.get("execution_seal_root_sha256")
            != EXECUTION_SEAL_ROOT_SHA256
            or arm_receipt.get("source_authority_binding_root_sha256")
            != "a00fa9241e0792a0a74a202ed191134ddd0e8e2e8b4873cb847e72a556bf926f"
            or arm_receipt.get("window") != CONTRACT_WINDOW_BINDING
            or arm_receipt.get("broker_mutation_enabled") is not False
            or arm_receipt.get("broker_live_authority") is not False
            or arm_receipt.get("real_order_transmission_possible") is not False
            or output_prefix != JANUARY_PREFIXES[arm_id]
            or artifact_inventory.get("artifact_count")
            != len(POST_ACCELERATION_ROLE_SUFFIXES)
            or artifact_inventory_root
            != receipt.get("artifact_inventory_root_sha256")
            or CORE.stable_sha256(artifact_inventory_for_hash)
            != artifact_inventory_root
            or receipt.get("artifact_count")
            != len(POST_ACCELERATION_ROLE_SUFFIXES)
            or not is_sha256(
                receipt.get("verified_artifact_identity_root_sha256")
            )
            or receipt.get("outcome_bearing_counts_emitted") is not False
            or receipt.get("economic_json_objects_decoded") != 0
            or receipt.get("economic_values_decoded_or_emitted")
            is not False
            or not artifact_rows_valid
            or ledger_counts != expected_ledger_counts
            or artifact_inventory.get(
                "all_artifacts_regular_non_symlink_files"
            )
            is not True
            or artifact_inventory.get("all_expected_artifacts_present")
            is not True
            or artifact_inventory.get(
                "ledger_counts_reconciled_to_completed_summary"
            )
            is not True
            or artifact_inventory.get(
                "zero_real_order_send_attempts_reconciled"
            )
            is not True
            or artifact_inventory.get("order_send_attempts_by_profile")
            != {str(NAMESPACE["expected_profile"]): 0}
            or artifact_inventory.get("completed_summary_status")
            != "broad_live_as_if_replay_materialized_broker_live_closed"
            or artifact_inventory.get("partial_summary_status")
            != "partial_in_progress_not_final_proof"
            or producer_artifacts.get("summary", {}).get("status")
            != "broad_live_as_if_replay_materialized_broker_live_closed"
            or producer_artifacts.get("partial_summary", {}).get("status")
            != "partial_in_progress_not_final_proof"
            or not isinstance(producer_pack_roots, Mapping)
            or not producer_pack_roots
            or producer_pack.get("path") != seal_pack.get("authority_path")
            or producer_pack.get("file_sha256")
            != seal_pack.get("authority_file_sha256")
            or producer_pack.get("authority_root_sha256")
            != seal_pack.get("authority_root_sha256")
            or producer_pack.get("prepared_day_pack_root")
            != seal_pack.get("prepared_day_pack_root")
            or producer_pack_roots
            != seal_pack.get("prepared_day_pack_roots")
            or verification_pack.get("authority_file_sha256")
            != producer_pack.get("file_sha256")
            or verification_pack.get("authority_root_sha256")
            != producer_pack.get("authority_root_sha256")
            or verification_pack.get(
                "prepared_day_pack_roots_sha256"
            )
            != CORE.stable_sha256(dict(producer_pack_roots))
            or verification_pack.get(
                "all_declared_pack_bytes_independently_authenticated"
            )
            is not True
            or not is_sha256(
                verification_pack.get(
                    "prepared_pack_stored_byte_identity_root_sha256"
                )
            )
        ):
            raise JanuaryAuditError(
                f"january_{arm_id.lower()}_arm_receipt_divergent"
            )
        records[arm_id] = {
            "path": str(path),
            "file_sha256": binding["file_sha256"],
            "verification_root_sha256": embedded_root,
            "arm_receipt_path": str(arm_receipt_path),
            "arm_receipt_file_sha256": expected_arm_receipt_file,
            "arm_receipt_root_sha256": expected_arm_receipt_root,
            "artifact_inventory_root_sha256": artifact_inventory_root,
            "verified_artifact_identity_root_sha256": receipt.get(
                "verified_artifact_identity_root_sha256"
            ),
            "artifact_count": receipt.get("artifact_count"),
            "producer_artifact_inventory": copy.deepcopy(
                dict(artifact_inventory)
            ),
            "prepared_pack_authority": copy.deepcopy(
                dict(verification_pack)
            ),
            "all_logical_bytes_verified": True,
            "broker_live_authority": False,
            "real_order_transmission_possible": False,
        }
    return records


def reconcile_analyzed_artifacts_to_receipts(
    base_audit: Mapping[str, Any],
    verification_bindings: Mapping[str, Any],
    namespace_storage: Mapping[str, Any],
    *,
    arm_order: Sequence[str] = ARM_ORDER,
) -> dict[str, Any]:
    """Bind every analyzed logical byte to its producer and verifier receipt."""

    failures: list[dict[str, Any]] = []
    per_arm: dict[str, Any] = {}
    audit_arms = base_audit.get("arms")
    audit_arms = audit_arms if isinstance(audit_arms, Mapping) else {}
    storage_rows = namespace_storage.get("entries")
    storage_rows = storage_rows if isinstance(storage_rows, list) else []
    storage_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    duplicate_storage_keys: list[tuple[str, str]] = []
    selected_arms = set(arm_order)
    for row in storage_rows:
        if not isinstance(row, Mapping):
            continue
        key = (str(row.get("arm_id") or ""), str(row.get("artifact") or ""))
        if key[0] not in selected_arms:
            continue
        if key in storage_by_key:
            duplicate_storage_keys.append(key)
        else:
            storage_by_key[key] = row
    for arm_id, role in duplicate_storage_keys:
        failures.append(
            {
                "arm_id": arm_id,
                "artifact": role,
                "reason": "duplicate_namespace_storage_identity",
            }
        )

    expected_storage_keys = {
        (arm_id, role)
        for arm_id in arm_order
        for role in POST_ACCELERATION_JSONL_ROLES
    }
    for arm_id, role in sorted(expected_storage_keys - set(storage_by_key)):
        failures.append(
            {
                "arm_id": arm_id,
                "artifact": role,
                "reason": "namespace_storage_identity_missing",
            }
        )
    for arm_id, role in sorted(set(storage_by_key) - expected_storage_keys):
        failures.append(
            {
                "arm_id": arm_id,
                "artifact": role,
                "reason": "namespace_storage_identity_unexpected",
            }
        )

    for arm_id in arm_order:
        failure_start = len(failures)
        arm = audit_arms.get(arm_id)
        arm = arm if isinstance(arm, Mapping) else {}
        binding = verification_bindings.get(arm_id)
        binding = binding if isinstance(binding, Mapping) else {}
        current_artifacts = arm.get("artifacts")
        current_artifacts = (
            current_artifacts
            if isinstance(current_artifacts, Mapping)
            else {}
        )
        inventory = binding.get("producer_artifact_inventory")
        inventory = inventory if isinstance(inventory, Mapping) else {}
        producer_artifacts = inventory.get("artifacts")
        producer_artifacts = (
            producer_artifacts
            if isinstance(producer_artifacts, Mapping)
            else {}
        )
        inventory_for_hash = copy.deepcopy(dict(inventory))
        inventory_root = inventory_for_hash.pop(
            "inventory_root_sha256",
            None,
        )
        if (
            set(current_artifacts) != set(POST_ACCELERATION_ROLE_SUFFIXES)
            or set(producer_artifacts)
            != set(POST_ACCELERATION_ROLE_SUFFIXES)
            or inventory.get("artifact_count")
            != len(POST_ACCELERATION_ROLE_SUFFIXES)
            or binding.get("artifact_count")
            != len(POST_ACCELERATION_ROLE_SUFFIXES)
            or inventory_root
            != binding.get("artifact_inventory_root_sha256")
            or CORE.stable_sha256(inventory_for_hash) != inventory_root
        ):
            failures.append(
                {
                    "arm_id": arm_id,
                    "reason": "producer_artifact_inventory_binding_invalid",
                }
            )

        prefix = str(arm.get("prefix") or "")
        logical_identities: dict[str, dict[str, Any]] = {}
        matched_count = 0
        for role, suffix in POST_ACCELERATION_ROLE_SUFFIXES.items():
            producer = producer_artifacts.get(role)
            producer = producer if isinstance(producer, Mapping) else {}
            current = current_artifacts.get(role)
            current = current if isinstance(current, Mapping) else {}
            expected_name = f"{prefix}{suffix}"
            current_identity = {
                "bytes": current.get("bytes"),
                "sha256": current.get("sha256"),
            }
            producer_identity = {
                "bytes": producer.get("bytes"),
                "sha256": producer.get("sha256"),
            }
            logical_identity = {
                "logical_path": expected_name,
                **current_identity,
            }
            if role in POST_ACCELERATION_JSONL_ROLES:
                current_identity["rows"] = current.get("rows")
                producer_identity["rows"] = producer.get("rows")
                logical_identity["rows"] = current.get("rows")
            logical_identities[role] = logical_identity
            path_valid = bool(
                expected_name
                and producer.get("path") == expected_name
                and Path(str(current.get("path") or "")).name
                == expected_name
            )
            stable_valid = bool(
                current.get("stable_pre_parse_post") is True
                and current.get("namespace_initial_sha256")
                == current.get("sha256")
                and current.get("namespace_post_audit_sha256")
                == current.get("sha256")
            )
            if (
                not path_valid
                or not stable_valid
                or current_identity != producer_identity
            ):
                failures.append(
                    {
                        "arm_id": arm_id,
                        "artifact": role,
                        "reason": (
                            "producer_current_artifact_identity_mismatch"
                        ),
                    }
                )
            else:
                matched_count += 1

            if role in POST_ACCELERATION_JSONL_ROLES:
                storage = storage_by_key.get((arm_id, role), {})
                storage_identity = {
                    "bytes": storage.get("logical_bytes"),
                    "sha256": storage.get("sha256"),
                    "rows": storage.get("physical_line_count"),
                }
                if (
                    Path(str(storage.get("path") or "")).name
                    != expected_name
                    or storage_identity != current_identity
                    or storage.get("json_object_row_count")
                    != current.get("rows")
                    or storage.get("blank_line_count") != 0
                    or (
                        current.get("bytes") != 0
                        and storage.get("ends_with_lf") is not True
                    )
                    or storage.get("full_logical_reverification") is not True
                ):
                    failures.append(
                        {
                            "arm_id": arm_id,
                            "artifact": role,
                            "reason": (
                                "current_namespace_full_logical_"
                                "reverification_mismatch"
                            ),
                        }
                    )

        actual_identity_root = CORE.stable_sha256(logical_identities)
        expected_identity_root = binding.get(
            "verified_artifact_identity_root_sha256"
        )
        if actual_identity_root != expected_identity_root:
            failures.append(
                {
                    "arm_id": arm_id,
                    "reason": "verified_artifact_identity_root_mismatch",
                    "expected_root_sha256": expected_identity_root,
                    "actual_root_sha256": actual_identity_root,
                }
            )
        per_arm[arm_id] = {
            "valid": len(failures) == failure_start,
            "artifact_count": len(logical_identities),
            "producer_current_identity_match_count": matched_count,
            "artifact_inventory_root_sha256": inventory_root,
            "verified_artifact_identity_root_sha256": actual_identity_root,
            "independent_verifier_identity_root_sha256": (
                expected_identity_root
            ),
        }

    valid = bool(
        namespace_storage.get("valid") is True
        and not failures
        and len(per_arm) == len(arm_order)
        and all(row.get("valid") is True for row in per_arm.values())
    )
    return {
        "schema": (
            "gtos.b7_5.selection_sizing."
            "analyzed_artifact_receipt_reconciliation.v1"
        ),
        "status": (
            "PASS_ANALYZED_BYTES_EXACTLY_BOUND_TO_ARM_RECEIPTS"
            if valid
            else "FAIL_ANALYZED_BYTES_NOT_BOUND_TO_ARM_RECEIPTS"
        ),
        "valid": valid,
        "arm_count": len(per_arm),
        "artifact_count": sum(
            int(row.get("artifact_count") or 0)
            for row in per_arm.values()
        ),
        "per_arm": per_arm,
        "failure_count": len(failures),
        "failures": failures,
    }


def _single_window_row(
    rows: Any,
    *,
    identity_field: str,
    artifact: str,
) -> dict[str, Any]:
    materialized = rows if isinstance(rows, list) else []
    matched = [
        row
        for row in materialized
        if isinstance(row, dict) and row.get(identity_field) == WINDOW_ID
    ]
    if len(matched) != 1:
        raise JanuaryAuditError(
            f"{artifact}_development_january_binding_count_invalid:{len(matched)}"
        )
    return matched[0]


def validate_selected_window_bindings(
    protocol: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    protocol_row = _single_window_row(
        protocol.get("windows"),
        identity_field="id",
        artifact="protocol",
    )
    expected_protocol_row = PROTOCOL_WINDOW_BINDING
    if protocol_row != expected_protocol_row:
        raise JanuaryAuditError("protocol_development_january_binding_divergent")

    contract_row = _single_window_row(
        contract.get("window_source_plan_bindings"),
        identity_field="window_id",
        artifact="decision_contract",
    )
    expected_contract_row = CONTRACT_WINDOW_BINDING
    if contract_row != expected_contract_row:
        raise JanuaryAuditError(
            "decision_contract_development_january_binding_divergent"
        )

    protocol_order = protocol.get("execution_order")
    contract_order = contract.get("execution_order")
    if not isinstance(protocol_order, list) or protocol_order != contract_order:
        raise JanuaryAuditError("development_execution_order_binding_divergent")
    january_step = "development_january_all_four_arms"
    april_step = "adverse_development_april_all_four_arms"
    if protocol_order.count(january_step) != 1:
        raise JanuaryAuditError("development_january_execution_step_count_invalid")
    index = protocol_order.index(january_step)
    if index + 1 >= len(protocol_order) or protocol_order[index + 1] != april_step:
        raise JanuaryAuditError("development_january_next_step_not_april")
    return {
        "protocol_window": copy.deepcopy(protocol_row),
        "decision_contract_window": copy.deepcopy(contract_row),
        "next_protocol_step": april_step,
    }


def validate_source_authority_amendment_bindings(
    amendment: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove the immutable protocol-to-R3 January authority transition."""

    expected = SOURCE_AUTHORITY_BINDING
    amendment_self_hash = amendment.get("self_hash")
    amendment_self_hash = (
        amendment_self_hash if isinstance(amendment_self_hash, Mapping) else {}
    )
    scope = amendment.get("scope")
    scope = scope if isinstance(scope, Mapping) else {}
    transition = amendment.get("active_source_plan_transition")
    transition = transition if isinstance(transition, Mapping) else {}
    reproduction = amendment.get("reproduction_audit")
    reproduction = reproduction if isinstance(reproduction, Mapping) else {}
    outcome = amendment.get("outcome_boundary")
    outcome = outcome if isinstance(outcome, Mapping) else {}
    factorial = amendment.get("immutable_factorial_closure")
    factorial = factorial if isinstance(factorial, Mapping) else {}

    amendment_checks = {
        "schema": (amendment.get("schema"), expected["schema"]),
        "status": (amendment.get("status"), expected["status"]),
        "embedded_self_hash": (
            amendment_self_hash.get("sha256"),
            SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256,
        ),
        "canonical_self_hash": (
            _verify_embedded_self_hash(amendment),
            True,
        ),
        "decision_window_id": (
            scope.get("decision_window_id"),
            expected["decision_window_id"],
        ),
        "source_window_contract_window_id": (
            scope.get("source_window_contract_window_id"),
            expected["source_window_contract_window_id"],
        ),
        "window_start": (scope.get("start"), WINDOW_START),
        "window_end": (scope.get("end"), WINDOW_END),
        "repair_class": (scope.get("repair_class"), "source_authority_only"),
        "factorial_treatment_change": (
            scope.get("factorial_treatment_change"),
            False,
        ),
        "binding_action": (
            transition.get("binding_action"),
            expected["binding_action"],
        ),
        "protocol_source_plan_digest": (
            transition.get(
                "protocol_and_sealed_contract_source_plan_digest_sha256"
            ),
            PROTOCOL_SOURCE_PLAN_SHA256,
        ),
        "active_source_plan_digest": (
            transition.get("current_reproduced_source_plan_digest_sha256"),
            SOURCE_PLAN_SHA256,
        ),
        "old_and_r3_source_plan_arms_may_not_mix": (
            transition.get("old_and_r3_source_plan_arms_may_not_mix"),
            True,
        ),
        "resolver_run_count": (
            reproduction.get("resolver_run_count"),
            expected["resolver_run_count"],
        ),
        "resolver_runs_identical": (
            reproduction.get("resolver_runs_identical"),
            True,
        ),
        "reproduced_source_plan_digest": (
            reproduction.get("reproduced_source_plan_digest_sha256"),
            SOURCE_PLAN_SHA256,
        ),
        "replay_launched": (reproduction.get("replay_launched"), False),
        "run_campaign_call_count": (
            reproduction.get("run_campaign_call_count"),
            0,
        ),
        "outcome_artifact_read_count": (
            reproduction.get("outcome_artifact_read_count"),
            0,
        ),
        "outcome_ledger_read_count": (
            reproduction.get("outcome_ledger_read_count"),
            0,
        ),
        "march_outcome_read": (reproduction.get("march_outcome_read"), False),
        "replay_launched_at_seal": (
            outcome.get("replay_launched_at_seal"),
            False,
        ),
        "amendment_is_arm_varying_treatment": (
            factorial.get("amendment_is_arm_varying_treatment"),
            False,
        ),
        "engineering_june_04_r2_binding_unchanged": (
            factorial.get("engineering_june_04_r2_binding_unchanged"),
            True,
        ),
    }
    amendment_divergent = [
        label
        for label, (actual, sealed) in amendment_checks.items()
        if actual != sealed
    ]
    if amendment_divergent:
        raise JanuaryAuditError(
            "development_january_r3_amendment_divergent:"
            + "|".join(amendment_divergent)
        )

    source_chain = contract.get("source_amendment_chain")
    source_chain = (
        source_chain if isinstance(source_chain, Mapping) else {}
    )
    r3 = source_chain.get("r3")
    r3 = r3 if isinstance(r3, Mapping) else {}
    source_plan_authority = contract.get("source_plan_authority")
    source_plan_authority = (
        source_plan_authority
        if isinstance(source_plan_authority, Mapping)
        else {}
    )
    contract_checks = {
        "common_across_all_arms": (
            source_chain.get("common_across_all_arms"),
            True,
        ),
        "amendment_is_arm_varying_treatment": (
            source_chain.get("arm_varying_treatment"),
            False,
        ),
        "r3_path": (r3.get("path"), expected["path"]),
        "r3_file_sha256": (
            r3.get("file_sha256"),
            SOURCE_AUTHORITY_AMENDMENT_FILE_SHA256,
        ),
        "r3_self_hash_sha256": (
            r3.get("self_hash_sha256"),
            SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256,
        ),
        "r3_active_source_plan_digest": (
            source_plan_authority.get(WINDOW_ID),
            SOURCE_PLAN_SHA256,
        ),
        "old_source_cells_may_not_mix": (
            source_plan_authority.get("old_source_cells_may_not_mix"),
            True,
        ),
    }
    contract_divergent = [
        label
        for label, (actual, sealed) in contract_checks.items()
        if actual != sealed
    ]
    if contract_divergent:
        raise JanuaryAuditError(
            "development_january_contract_r3_binding_divergent:"
            + "|".join(contract_divergent)
        )

    return {
        "active_amendment": "R3",
        "amendment_path": expected["path"],
        "amendment_file_sha256": SOURCE_AUTHORITY_AMENDMENT_FILE_SHA256,
        "amendment_self_hash_sha256": (
            SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256
        ),
        "protocol_source_plan_digest_sha256": PROTOCOL_SOURCE_PLAN_SHA256,
        "active_source_plan_digest_sha256": SOURCE_PLAN_SHA256,
        "replay_free_reproduction": True,
        "common_across_all_arms": True,
        "march_outcome_read": False,
    }


def validate_window_neutral_contract_bindings(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    contract_for_hash = copy.deepcopy(dict(contract))
    self_hash = contract_for_hash.get("self_hash")
    if isinstance(self_hash, dict):
        self_hash.pop("sha256", None)
    actual_self_hash = CORE.stable_sha256(contract_for_hash)
    arms = contract.get("factorial_contract", {}).get("arms")
    arms = arms if isinstance(arms, list) else []
    actual_arm_fingerprints = {
        str(row.get("arm_id")): row.get("arm_fingerprint_sha256")
        for row in arms
        if isinstance(row, dict)
    }
    computed_binding_payloads = {
        arm_id: CORE.stable_sha256(
            CORE.expected_factorial_binding_payload(
                arm_id,
                JANUARY_FROZEN,
            )
        )
        for arm_id in ARM_ORDER
    }
    checks = {
        "decision_contract_self_hash": (
            actual_self_hash,
            CONTRACT_SELF_HASH_SHA256,
        ),
        "common_execution_input_digest": (
            contract.get("input_bindings", {}).get(
                "common_execution_input_digest_sha256"
            ),
            COMMON_EXECUTION_INPUT_SHA256,
        ),
        "protocol_economics_digest": (
            contract.get("protocol_economics_digest_sha256"),
            PROTOCOL_ECONOMICS_SHA256,
        ),
        "neutral_selection_seed": (
            contract.get("factorial_contract", {}).get(
                "neutral_selection_seed_sha256"
            ),
            NEUTRAL_SELECTION_SEED_SHA256,
        ),
        "arm_fingerprints": (actual_arm_fingerprints, ARM_FINGERPRINTS),
        "binding_payloads": (computed_binding_payloads, BINDING_PAYLOADS),
        "denominator": (contract.get("denominator"), DENOMINATOR),
        "matched_risk": (contract.get("matched_risk"), MATCHED_RISK),
    }
    divergent = [
        label for label, (actual, expected) in checks.items() if actual != expected
    ]
    if divergent:
        raise JanuaryAuditError(
            "development_january_window_neutral_contract_divergent:"
            + "|".join(divergent)
        )
    return {
        "decision_contract_self_hash_sha256": actual_self_hash,
        "common_execution_input_digest_sha256": COMMON_EXECUTION_INPUT_SHA256,
        "protocol_economics_digest_sha256": PROTOCOL_ECONOMICS_SHA256,
        "neutral_selection_seed_sha256": NEUTRAL_SELECTION_SEED_SHA256,
        "arm_fingerprints": copy.deepcopy(ARM_FINGERPRINTS),
        "binding_payloads": copy.deepcopy(computed_binding_payloads),
    }


def validate_production_control(config: AnalyzerConfig) -> dict[str, Any]:
    validate_production_config(config)
    frozen_hashes = {
        "june_core_analyzer": (CORE_ANALYZER_PATH, CORE_ANALYZER_SHA256),
        "verifier": (CORE.VERIFIER_PATH, CORE.FROZEN_VERIFIER_SHA256),
        "cold_evidence_reader": (
            COLD_EVIDENCE_READER_PATH,
            COLD_EVIDENCE_READER_FILE_SHA256,
        ),
        "protocol": (config.protocol_path, PROTOCOL_FILE_SHA256),
        "decision_contract": (config.contract_path, CONTRACT_FILE_SHA256),
        "predecessor_decision_contract": (
            PREDECESSOR_CONTRACT_PATH,
            str(WINDOW_NEUTRAL["decision_contract"]["file_sha256"]),
        ),
        "execution_seal": (
            EXECUTION_SEAL_PATH,
            EXECUTION_SEAL_FILE_SHA256,
        ),
        "source_authority_amendment_r3": (
            config.source_authority_amendment_path,
            SOURCE_AUTHORITY_AMENDMENT_FILE_SHA256,
        ),
        "window_control": (config.control_path, CONTROL_FILE_SHA256),
    }
    records: dict[str, Any] = {}
    for label, (path, expected) in frozen_hashes.items():
        actual = sha256_file(path)
        if actual != expected:
            raise JanuaryAuditError(
                f"{label}_sha256_mismatch:expected={expected}:actual={actual}"
            )
        records[label] = {"path": str(path), "sha256": actual}

    control, control_record = _read_json_object(config.control_path)
    if (
        control.get("schema")
        != "gtos.b7_5.selection_sizing.development_window_control.v1"
        or control.get("status")
        != "SEALED_DEVELOPMENT_JANUARY_CONTROL_BEFORE_FACTORIAL_REPLAY"
        or control.get("valid") is not True
        or not _verify_embedded_self_hash(control)
        or control.get("self_hash", {}).get("sha256")
        != CONTROL_SELF_HASH_SHA256
    ):
        raise JanuaryAuditError("development_january_window_control_invalid")
    namespace = control.get("namespace")
    namespace = namespace if isinstance(namespace, dict) else {}
    if (
        namespace.get("prefixes") != JANUARY_PREFIXES
        or namespace.get("required_suffixes") != CORE.NAMESPACE_SUFFIXES
        or namespace.get("expected_candidate_count")
        != JANUARY_FROZEN.expected_candidate_count
        or namespace.get("expected_decision_count")
        != JANUARY_FROZEN.expected_decision_count
        or namespace.get("expected_scorecard_count")
        != JANUARY_FROZEN.expected_scorecard_count
        or namespace.get("expected_symbol_count")
        != JANUARY_FROZEN.expected_symbol_count
        or namespace.get("expected_profile") != JANUARY_FROZEN.expected_profile
    ):
        raise JanuaryAuditError("development_january_namespace_control_divergent")
    window = control.get("window")
    window = window if isinstance(window, dict) else {}
    protocol_window = control.get("protocol_window_binding")
    contract_window = control.get("decision_contract_window_binding")
    source_authority_binding = control.get(
        "source_authority_amendment_binding"
    )
    if (
        not isinstance(protocol_window, dict)
        or not isinstance(contract_window, dict)
        or source_authority_binding != SOURCE_AUTHORITY_BINDING
        or window.get("window_id") != WINDOW_ID
        or window.get("role") != WINDOW_ROLE
        or window.get("start") != WINDOW_START
        or window.get("end") != WINDOW_END
        or window.get("source_plan_digest_sha256") != SOURCE_PLAN_SHA256
        or window.get("protocol_source_plan_digest_sha256")
        != PROTOCOL_SOURCE_PLAN_SHA256
        or protocol_window.get("id") != WINDOW_ID
        or protocol_window.get("role") != WINDOW_ROLE
        or protocol_window.get("start") != WINDOW_START
        or protocol_window.get("end") != WINDOW_END
        or contract_window.get("window_id") != WINDOW_ID
        or contract_window.get("role") != WINDOW_ROLE
        or contract_window.get("start") != WINDOW_START
        or contract_window.get("end") != WINDOW_END
        or contract_window.get("source_plan_digest_sha256")
        != SOURCE_PLAN_SHA256
    ):
        raise JanuaryAuditError("development_january_window_control_divergent")

    protocol, protocol_record = _read_json_object(config.protocol_path)
    contract, contract_record = _read_json_object(config.contract_path)
    amendment, amendment_record = _read_json_object(
        config.source_authority_amendment_path
    )
    selected = validate_selected_window_bindings(protocol, contract)
    source_authority = validate_source_authority_amendment_bindings(
        amendment,
        contract,
    )
    neutral = validate_window_neutral_contract_bindings(contract)
    execution_seal = validate_execution_seal_bindings(
        EXECUTION_SEAL,
        contract,
    )
    post_cold_verification = validate_post_cold_verification_bindings()
    return {
        **records,
        "window_control": {
            **control_record,
            "self_hash_sha256": CONTROL_SELF_HASH_SHA256,
            "self_hash_valid": True,
        },
        "protocol": protocol_record,
        "decision_contract": contract_record,
        "source_authority_amendment_r3": {
            **amendment_record,
            "self_hash_sha256": (
                SOURCE_AUTHORITY_AMENDMENT_SELF_HASH_SHA256
            ),
            "self_hash_valid": True,
        },
        "selected_window_binding": selected,
        "source_authority_binding": source_authority,
        "window_neutral_contract_binding": neutral,
        "post_acceleration_execution_seal_binding": execution_seal,
        "post_cold_arm_verification_bindings": post_cold_verification,
    }


_FROZEN_CORE_UPDATE_SCORECARD_IDENTITY = CORE.update_scorecard_identity
_FROZEN_CORE_UPDATE_MISSED = CORE.update_missed
_FROZEN_CORE_MISSED_TRANSITION_ROLLUP = CORE.missed_transition_rollup


def project_post_acceleration_summary_for_frozen_core(
    arm_id: str,
    summary: Mapping[str, Any],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate full-cache bindings, then project the producer's semantic digest.

    The post-acceleration producer intentionally seals the two full-cache
    bindings outside the arm-neutral semantic payload.  They are authenticated
    separately here and are the only fields removed before the immutable June
    digest validator is called.
    """

    projected = copy.deepcopy(dict(summary))
    shared = projected.get("shared_execution_contract")
    shared = shared if isinstance(shared, dict) else {}
    expected_profile_roots = EXACT_PROFILE_CONFIG_ROOTS[arm_id]
    expected_risk_bindings = EXACT_RISK_PROFILE_BINDINGS
    if (
        shared.get("exact_profile_config_roots_sha256")
        != expected_profile_roots
    ):
        CORE.add_failure(
            failures,
            "post_acceleration_exact_profile_config_root_mismatch",
            arm_id=arm_id,
            expected=expected_profile_roots,
            actual=shared.get("exact_profile_config_roots_sha256"),
        )
    if shared.get("exact_risk_profile_bindings") != expected_risk_bindings:
        CORE.add_failure(
            failures,
            "post_acceleration_exact_risk_profile_binding_mismatch",
            arm_id=arm_id,
            expected=expected_risk_bindings,
            actual=shared.get("exact_risk_profile_bindings"),
        )
    shared.pop("exact_profile_config_roots_sha256", None)
    shared.pop("exact_risk_profile_bindings", None)
    projected["shared_execution_contract"] = shared
    return projected


def _selected_key_list(
    row: Mapping[str, Any],
    field_name: str,
) -> list[str] | None:
    raw = row.get(field_name)
    if raw is None:
        return None
    if not isinstance(raw, list):
        return []
    return [str(value or "").strip() for value in raw]


def scorecard_selected_key_set(row: Mapping[str, Any]) -> list[str]:
    """Return the authoritative ordered selected set for causal comparison."""

    scheduler = _selected_key_list(
        row,
        "selected_scheduler_selected_candidate_instance_keys",
    )
    admitted = _selected_key_list(
        row,
        "risk_admitted_final_selected_candidate_instance_keys",
    )
    if scheduler is not None and admitted is not None:
        if (
            any(not value for value in scheduler)
            or any(not value for value in admitted)
            or len(scheduler) != len(set(scheduler))
            or len(admitted) != len(set(admitted))
            or set(scheduler) != set(admitted)
        ):
            return []
        return scheduler
    singular = str(row.get("selected_candidate_instance_key") or "").strip()
    return [singular] if singular else []


def update_scorecard_identity_set(
    surface: Any,
    row: Mapping[str, Any],
    *,
    window: str,
    hard_pool: Mapping[str, Any],
    line_number: int,
) -> None:
    """Bind every selected economic candidate, including multi-order windows."""

    list_fields = (
        "selected_scheduler_selected_candidate_instance_keys",
        "risk_admitted_final_selected_candidate_instance_keys",
    )
    raw_lists = {
        field_name: _selected_key_list(row, field_name)
        for field_name in list_fields
    }
    if all(value is None for value in raw_lists.values()):
        _FROZEN_CORE_UPDATE_SCORECARD_IDENTITY(
            surface,
            row,
            window=window,
            hard_pool=hard_pool,
            line_number=line_number,
        )
        return
    if any(value is None for value in raw_lists.values()):
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_set_missing",
            line=line_number,
            window=window,
            present_fields=[
                key for key, value in raw_lists.items() if value is not None
            ],
        )
        return
    scheduler = raw_lists[list_fields[0]] or []
    admitted = raw_lists[list_fields[1]] or []
    invalid_lists = bool(
        any(not value for value in scheduler)
        or any(not value for value in admitted)
        or len(scheduler) != len(set(scheduler))
        or len(admitted) != len(set(admitted))
    )
    if invalid_lists or set(scheduler) != set(admitted):
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_set_mismatch",
            line=line_number,
            window=window,
            scheduler_selected=scheduler,
            risk_admitted_selected=admitted,
        )
        return

    selected_keys = list(scheduler)
    singular_fields = (
        "selected_candidate_instance_key",
        "selected_scheduler_selected_candidate_instance_key",
    )
    singular = {
        field_name: str(row.get(field_name) or "").strip()
        for field_name in singular_fields
    }
    canonical = str(
        row.get(
            "selected_scheduler_canonical_replay_candidate_instance_key"
        )
        or ""
    ).strip()
    if not selected_keys:
        if any(singular.values()) or canonical:
            CORE.record_relational_failure(
                surface,
                "scorecard_empty_selected_set_has_singular_identity",
                line=line_number,
                window=window,
                singular=singular,
                canonical=canonical,
            )
        return
    if (
        any(not value for value in singular.values())
        or len(set(singular.values())) != 1
        or next(iter(singular.values())) not in set(selected_keys)
        or not canonical
        or canonical not in set(selected_keys)
    ):
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_alias_mismatch",
            line=line_number,
            window=window,
            singular=singular,
            canonical=canonical,
            selected_keys=selected_keys,
        )
        return

    optional_top_level = _selected_key_list(
        row,
        "selected_candidate_instance_keys",
    )
    if (
        optional_top_level is not None
        and (
            any(not value for value in optional_top_level)
            or len(optional_top_level) != len(set(optional_top_level))
            or set(optional_top_level) != set(selected_keys)
        )
    ):
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_set_mismatch",
            line=line_number,
            window=window,
            scheduler_selected=selected_keys,
            top_level_selected=optional_top_level,
        )
        return

    hard_pool_keys = set(hard_pool.get("keys") or [])
    outside = sorted(set(selected_keys) - hard_pool_keys)
    if outside:
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_outside_hard_pool",
            line=line_number,
            window=window,
            candidate_instance_keys=outside,
        )
        return
    duplicate = sorted(
        key for key in selected_keys if key in surface.scorecard_selected
    )
    if duplicate:
        CORE.record_relational_failure(
            surface,
            "scorecard_selected_identity_duplicate",
            line=line_number,
            window=window,
            candidate_instance_keys=duplicate,
        )
        return
    for selected_key in selected_keys:
        surface.scorecard_selected[selected_key] = {
            "decision_window_id": window,
            "candidate_instance_key": selected_key,
        }


def update_missed_with_exact_evidence_class(
    surface: Any,
    row: Mapping[str, Any],
) -> None:
    _FROZEN_CORE_UPDATE_MISSED(surface, row)
    key = CORE.identity_key(row)
    if key in surface.missed_by_key:
        surface.missed_by_key[key][
            "non_executable_diagnostic_scoreable"
        ] = (
            row.get(
                "missed_opportunity_non_executable_diagnostic_scoreable"
            )
            is True
        )


def missed_transition_rollup_distinct_economics(
    original: Any,
    missed_surface: Any,
    source_trade_surface: Any,
    candidate_keys: Iterable[str],
) -> dict[str, Any]:
    """Keep identity closure while separating physical and counterfactual R."""

    keys = list(candidate_keys)
    result = original(
        missed_surface,
        source_trade_surface,
        keys,
    )
    retained_mismatches: list[str] = []
    classified: list[dict[str, Any]] = []
    for key in result.get("trade_missed_r_mismatch_keys", []):
        missed = missed_surface.missed_by_key.get(key)
        trade = source_trade_surface.trades.get(key)
        if (
            isinstance(missed, Mapping)
            and isinstance(trade, Mapping)
            and trade.get("scoreable") is True
            and missed.get("diagnostic_scoreable") is True
            and missed.get("headline_scoreable") is False
            and missed.get("non_executable_diagnostic_scoreable") is True
            and missed.get("scoreability_status")
            == "diagnostic_opportunity_r_scoreable"
        ):
            physical = float(trade["net_r"])
            counterfactual = float(missed["diagnostic_net_r"])
            classified.append(
                {
                    "candidate_instance_key": key,
                    "physical_trade_net_r": physical,
                    "counterfactual_missed_diagnostic_net_r": counterfactual,
                    "net_r_delta": round(physical - counterfactual, 12),
                }
            )
        else:
            retained_mismatches.append(key)
    result["trade_missed_r_mismatch_keys"] = retained_mismatches
    result["physical_vs_non_executable_diagnostic_count"] = len(classified)
    result[
        "physical_vs_non_executable_diagnostic_differences"
    ] = classified
    result["same_economic_object_r_mismatch_count"] = len(
        retained_mismatches
    )
    return result


def reconcile_hard_pool_sequences(
    left_arm: str,
    right_arm: str,
    left_rows: Sequence[Mapping[str, Any]],
    right_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require equal pools until a factor-caused selected-state divergence."""

    def indexed_causal_sequence(
        rows: Sequence[Mapping[str, Any]],
    ) -> tuple[
        dict[str, Mapping[str, Any]],
        list[tuple[str, str]],
        list[str],
        list[dict[str, Any]],
    ]:
        by_window: dict[str, Mapping[str, Any]] = {}
        sequence: list[tuple[str, str]] = []
        duplicates: list[str] = []
        order_failures: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            window = str(row.get("window") or "")
            sort_key = str(row.get("sort_key") or "")
            if not window or not sort_key or window in by_window:
                duplicates.append(window)
            else:
                by_window[window] = row
                sequence.append((sort_key, window))
                if len(sequence) > 1 and sequence[-1] <= sequence[-2]:
                    order_failures.append(
                        {
                            "index": index,
                            "previous": list(sequence[-2]),
                            "current": list(sequence[-1]),
                        }
                    )
        return by_window, sequence, duplicates, order_failures

    (
        left_by_window,
        left_sequence,
        left_duplicates,
        left_order_failures,
    ) = indexed_causal_sequence(left_rows)
    (
        right_by_window,
        right_sequence,
        right_duplicates,
        right_order_failures,
    ) = indexed_causal_sequence(right_rows)
    window_missing_left = sorted(
        set(right_by_window) - set(left_by_window)
    )
    window_missing_right = sorted(
        set(left_by_window) - set(right_by_window)
    )
    first_selected_divergence: str | None = None
    first_selected_divergence_sort_key: str | None = None
    pre_divergence_mismatches: list[dict[str, Any]] = []
    post_divergence_mismatches: list[dict[str, Any]] = []
    causal_sequence_mismatches: list[dict[str, Any]] = []
    for index in range(max(len(left_sequence), len(right_sequence))):
        left_identity = (
            left_sequence[index] if index < len(left_sequence) else None
        )
        right_identity = (
            right_sequence[index] if index < len(right_sequence) else None
        )
        if left_identity != right_identity:
            causal_sequence_mismatches.append(
                {
                    "index": index,
                    "left": (
                        list(left_identity)
                        if left_identity is not None
                        else None
                    ),
                    "right": (
                        list(right_identity)
                        if right_identity is not None
                        else None
                    ),
                }
            )
    causal_sequence_equal = not causal_sequence_mismatches
    all_windows = [
        window
        for _sort_key, window in left_sequence
        if window in right_by_window
    ]
    for window in all_windows:
        left = left_by_window[window]
        right = right_by_window[window]
        sort_key = str(left.get("sort_key") or "")
        left_pool = sorted(
            str(value) for value in left.get("hard_pool_keys", [])
        )
        right_pool = sorted(
            str(value) for value in right.get("hard_pool_keys", [])
        )
        left_selected = sorted(
            str(value) for value in left.get("selected_keys", [])
        )
        right_selected = sorted(
            str(value) for value in right.get("selected_keys", [])
        )
        pool_equal = left_pool == right_pool
        selected_equal = left_selected == right_selected
        if not pool_equal:
            mismatch = {
                "window": window,
                "sort_key": sort_key,
                "left_pool_digest_sha256": CORE.stable_sha256(left_pool),
                "right_pool_digest_sha256": CORE.stable_sha256(right_pool),
                "left_pool_count": len(left_pool),
                "right_pool_count": len(right_pool),
            }
            if first_selected_divergence is None:
                pre_divergence_mismatches.append(mismatch)
            else:
                post_divergence_mismatches.append(mismatch)
        if (
            first_selected_divergence is None
            and pool_equal
            and not selected_equal
        ):
            first_selected_divergence = window
            first_selected_divergence_sort_key = sort_key

    valid = not (
        left_duplicates
        or right_duplicates
        or left_order_failures
        or right_order_failures
        or not causal_sequence_equal
        or window_missing_left
        or window_missing_right
        or pre_divergence_mismatches
    )
    return {
        "left": left_arm,
        "right": right_arm,
        "valid": valid,
        "causal_rule": (
            "hard_pools_equal_until_first_equal_pool_factor_selected_set_"
            "divergence_then_arm_private_chronological_state_may_mediate"
        ),
        "window_count": len(all_windows),
        "causal_sequence_equal": causal_sequence_equal,
        "causal_sequence_mismatch_count": len(
            causal_sequence_mismatches
        ),
        "causal_sequence_mismatch_samples": (
            causal_sequence_mismatches[:12]
        ),
        "causal_order_failure_samples": {
            left_arm: left_order_failures[:12],
            right_arm: right_order_failures[:12],
        },
        "all_hard_pools_equal": not (
            pre_divergence_mismatches or post_divergence_mismatches
        ),
        "first_selected_state_divergence_window": first_selected_divergence,
        "first_selected_state_divergence_sort_key": (
            first_selected_divergence_sort_key
        ),
        "pre_divergence_hard_pool_mismatch_count": len(
            pre_divergence_mismatches
        ),
        "post_divergence_hard_pool_mismatch_count": len(
            post_divergence_mismatches
        ),
        "pre_divergence_hard_pool_mismatch_samples": (
            pre_divergence_mismatches[:12]
        ),
        "post_divergence_hard_pool_mismatch_samples": (
            post_divergence_mismatches[:12]
        ),
        "duplicate_window_samples": {
            left_arm: left_duplicates[:12],
            right_arm: right_duplicates[:12],
        },
        "missing_window_samples": {
            left_arm: window_missing_left[:12],
            right_arm: window_missing_right[:12],
        },
        "post_divergence_differences_are_evidence_not_suppressed": True,
    }


JANUARY_TERMINAL_SENTINEL_FIELDS = frozenset(
    {
        "broad_replay_profile",
        "broker_mutation_enabled",
        "bucket_source_family",
        "calendar_no_session_breadth_guard",
        "campaign",
        "candidate_count",
        "chunk_day_count",
        "chunk_end_day",
        "chunk_id",
        "chunk_start_day",
        "decision_time_utc",
        "decision_timeframes_present",
        "evidence_class",
        "final_selection_claim",
        "live_broker_authority",
        "live_replay_mode",
        "m1_or_tick_attached_to_decision",
        "marketable_guard_profile",
        "no_broker_boundary",
        "no_future_decision_rows",
        "orchestrator_adapter_reason",
        "orchestrator_class_direct_instantiation",
        "package_execution_result_scope",
        "phase",
        "profile",
        "raw_baseline_diagnostic_only",
        "raw_data_construction_mode",
        "raw_data_status",
        "repair_seed_window",
        "row_provenance_schema",
        "row_type",
        "source_row_type",
        "source_session_status",
        "split",
        "surface_contract",
        "symbol",
        "trading_day",
    }
)
JANUARY_TERMINAL_DECISION_SYMBOLS = (
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
)
JANUARY_TERMINAL_NO_SESSION_SYMBOLS = tuple(
    symbol
    for symbol in JANUARY_TERMINAL_DECISION_SYMBOLS
    if symbol not in {"BTCUSD", "ETHUSD"}
)
JANUARY_TERMINAL_SENTINEL_CAMPAIGNS = {
    arm_id: (
        f"{JANUARY_PREFIXES[arm_id].lower()}_"
        "repaired_package_conversion_v3"
    )
    for arm_id in ARM_ORDER
}
JANUARY_TERMINAL_SURFACE_CONTRACT = {
    "broker_adapter": "SimulatedBroker",
    "broker_mutation": False,
    "broker_order_lifecycle_capture_v4": (
        "src.components.broker_order_lifecycle_capture_v4."
        "build_broker_order_lifecycle_capture_v4"
    ),
    "candidate_generation": (
        "src.components.broader_origin_generators."
        "generate_live_broader_origin_candidates"
    ),
    "data_source": "HistoricalMT5Adapter",
    "decision_cycle_core": (
        "src.components.v4_live_replay_decision_core.V4DecisionCycleCore"
    ),
    "dynamic_target_stop_geometry_v4": (
        "src.components.dynamic_target_stop_geometry_v4."
        "build_target_stop_geometry_v4_contract"
    ),
    "execution_manager_v4": (
        "src.components.execution_manager_v4."
        "evaluate_execution_manager_v4"
    ),
    "exit_policy_v4": (
        "src.components.exit_policy_v4.evaluate_exit_policy_v4"
    ),
    "live_decision_packet_v4": (
        "src.components.live_decision_packet_v4."
        "build_live_decision_packet_v4"
    ),
    "live_ingestion": "src.components.data_ingestion.ingest_live_data",
    "market_state": "src.components.market_state.compute_market_state",
    "paid_api": False,
    "path_truth_index": "PathTruthIndex",
    "probability_debate_v4": (
        "src.components.probability_debate_v4."
        "evaluate_probability_debate_team_v4"
    ),
    "prop_firm_headroom_v4": (
        "src.components.prop_firm_headroom_v4."
        "evaluate_prop_firm_headroom_snapshot_v4"
    ),
    "remote_push": False,
    "same_symbol_lifecycle_v4": (
        "src.components.same_symbol_lifecycle_v4."
        "evaluate_same_symbol_lifecycle_v4"
    ),
    "scheduler_v4_best_trade_allocator": (
        "src.research.moonshot_scheduler_v4_best_trade_allocator."
        "allocate_decision_window"
    ),
    "selector_v4": (
        "src.components.selector_v4.evaluate_selector_v4_admission"
    ),
    "time_source": "ReplayClock",
}
JANUARY_TERMINAL_SENTINEL_FIXED_VALUES = {
    "broad_replay_profile": "repaired_package_conversion_v3",
    "broker_mutation_enabled": False,
    "bucket_source_family": None,
    "candidate_count": 0,
    "chunk_day_count": 1,
    "chunk_end_day": "2026-01-31",
    "chunk_id": (
        "repaired_package_conversion_v3:development:"
        "2026-01-31:2026-01-31"
    ),
    "chunk_start_day": "2026-01-31",
    "decision_time_utc": "2026-02-01T00:00:00+00:00",
    "decision_timeframes_present": ["D1", "H4", "H1", "M15"],
    "evidence_class": "source_bound_asof_timewarp_decision_input",
    "final_selection_claim": False,
    "live_broker_authority": False,
    "live_replay_mode": True,
    "m1_or_tick_attached_to_decision": False,
    "marketable_guard_profile": True,
    "no_broker_boundary": (
        "no_live_broker_account_order_deal_position_mutation_"
        "no_remote_push_no_paid_api"
    ),
    "no_future_decision_rows": True,
    "orchestrator_adapter_reason": (
        "production Orchestrator boot wires live broker process, signal "
        "handlers, LLM backend, and persistent runtime logging; replay "
        "invokes the same live component surfaces through a read-only "
        "adapter with broker mutation disabled"
    ),
    "orchestrator_class_direct_instantiation": False,
    "package_execution_result_scope": "repaired_executable_package_replay",
    "phase": "repaired_package_conversion_v3_development",
    "profile": "repaired_package_conversion_v3",
    "raw_baseline_diagnostic_only": False,
    "raw_data_construction_mode": (
        "live_ingestion_with_historical_mt5_adapter"
    ),
    "raw_data_status": "calendar_no_session_breadth_guard_day_skipped",
    "repair_seed_window": False,
    "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
    "row_type": "asof_decision",
    "source_row_type": None,
    "source_session_status": "calendar_no_session_breadth_stress_day",
    "split": "development",
    "trading_day": "2026-01-31",
}
JANUARY_TERMINAL_GUARD_FIELDS = frozenset(
    {
        "active",
        "enabled",
        "min_symbols",
        "no_session_labels",
        "no_session_symbol_count",
        "no_session_symbols",
        "reason",
        "source_boundary",
        "trading_day",
    }
)
JANUARY_TERMINAL_NO_SESSION_LABEL_FIELDS = frozenset(
    {
        "absolute_min_rows",
        "candidate_source_count",
        "diagnostic_fallback_only",
        "effective_min_rows",
        "evidence_class",
        "expected_m1_rows_from_m15_session",
        "m15_day_rows",
        "m1_to_m15_expected_coverage_ratio",
        "mapped_symbol",
        "no_session_reference",
        "not_redacted_account_native",
        "path",
        "path_replay_allowed",
        "populated_candidate_source_count",
        "row_count",
        "rows",
        "session_scaled_floor_applied",
        "session_scaled_min_rows",
        "sha256",
        "source_broker",
        "source_day_authority_hash_sha256",
        "source_day_authority_id",
        "source_family",
        "source_gaps",
        "source_overlap_consistent",
        "source_path",
        "source_role",
        "source_session_status",
        "source_truth_scope",
        "symbol",
        "terminal_lifecycle_close_allowed",
        "timeframe",
        "trading_day",
    }
)
JANUARY_TERMINAL_NO_SESSION_LABEL_FIXED_VALUES = {
    "absolute_min_rows": 1000,
    "candidate_source_count": 1,
    "diagnostic_fallback_only": False,
    "effective_min_rows": 0,
    "evidence_class": "source_bound_asof_timewarp_decision_input",
    "expected_m1_rows_from_m15_session": 0,
    "m15_day_rows": 0,
    "m1_to_m15_expected_coverage_ratio": None,
    "no_session_reference": "m1_and_m15_zero_rows_for_symbol_day",
    "not_redacted_account_native": True,
    "path_replay_allowed": False,
    "populated_candidate_source_count": 0,
    "row_count": 0,
    "rows": 0,
    "session_scaled_floor_applied": False,
    "session_scaled_min_rows": None,
    "source_broker": "FTMO",
    "source_family": "bridge_ftmo_m1_202601",
    "source_gaps": [],
    "source_overlap_consistent": True,
    "source_role": "owner_authorized_research_hydration",
    "source_session_status": "ftmo_verified_no_session_day",
    "source_truth_scope": (
        "ordered_price_path_only_not_broker_order_lifecycle_truth"
    ),
    "terminal_lifecycle_close_allowed": False,
    "timeframe": "M1",
    "trading_day": "2026-01-31",
}


def is_january_terminal_no_session_sentinel(
    row: Mapping[str, Any],
    *,
    arm_id: str,
    frozen: Any,
) -> bool:
    """Recognize only the zero-economic Jan-31 exclusive-midnight sentinel."""

    expected_binding = CORE.expected_flat_binding(arm_id, frozen)
    if any(row.get(key) != value for key, value in expected_binding.items()):
        return False
    allowed = set(expected_binding) | set(JANUARY_TERMINAL_SENTINEL_FIELDS)
    if set(row) != allowed:
        return False
    if any(
        row.get(key) != value
        for key, value in JANUARY_TERMINAL_SENTINEL_FIXED_VALUES.items()
    ):
        return False
    if (
        row.get("campaign")
        != JANUARY_TERMINAL_SENTINEL_CAMPAIGNS.get(arm_id)
        or row.get("symbol") not in JANUARY_TERMINAL_DECISION_SYMBOLS
        or row.get("surface_contract") != JANUARY_TERMINAL_SURFACE_CONTRACT
    ):
        return False
    guard = row.get("calendar_no_session_breadth_guard")
    if (
        not isinstance(guard, Mapping)
        or set(guard) != set(JANUARY_TERMINAL_GUARD_FIELDS)
    ):
        return False
    guard_required = {
        "active": True,
        "enabled": True,
        "min_symbols": 1,
        "trading_day": "2026-01-31",
        "reason": "calendar_no_session_breadth_guard_active",
        "source_boundary": "source_bound_asof_timewarp_decision_input",
    }
    if any(guard.get(key) != value for key, value in guard_required.items()):
        return False
    symbols = guard.get("no_session_symbols")
    labels = guard.get("no_session_labels")
    count = guard.get("no_session_symbol_count")
    if (
        not isinstance(symbols, list)
        or not isinstance(labels, list)
        or symbols != list(JANUARY_TERMINAL_NO_SESSION_SYMBOLS)
        or count != len(symbols)
        or count != len(labels)
        or count == 0
        or len(symbols) != len(set(str(value) for value in symbols))
    ):
        return False
    for symbol, label in zip(symbols, labels, strict=True):
        if (
            not isinstance(label, Mapping)
            or set(label) != set(JANUARY_TERMINAL_NO_SESSION_LABEL_FIELDS)
            or any(
                label.get(key) != value
                for key, value in (
                    JANUARY_TERMINAL_NO_SESSION_LABEL_FIXED_VALUES.items()
                )
            )
            or label.get("symbol") != symbol
            or label.get("mapped_symbol") != symbol
            or label.get("path") != label.get("source_path")
            or Path(str(label.get("path") or "")).name
            != f"{symbol}_M1.csv"
            or not is_sha256(label.get("sha256"))
            or not is_sha256(
                label.get("source_day_authority_hash_sha256")
            )
            or label.get("source_day_authority_id")
            != (
                "source_day:"
                f"{label.get('source_day_authority_hash_sha256')[:24]}"
            )
        ):
            return False
    return True


def validate_post_acceleration_protocol_and_contract(
    config: Any,
    failures: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol, protocol_record = CORE.read_json_object(config.protocol_path)
    contract, contract_record = CORE.read_json_object(config.contract_path)
    frozen = config.frozen
    if protocol_record["sha256"] != frozen.protocol_file_sha256:
        CORE.add_failure(failures, "protocol_file_hash_mismatch")
    if contract_record["sha256"] != frozen.contract_file_sha256:
        CORE.add_failure(failures, "decision_contract_file_hash_mismatch")
    for artifact, payload in (
        ("protocol", protocol),
        ("decision_contract", contract),
    ):
        violations = list(CORE.recursive_authority_violations(payload))
        if violations:
            CORE.add_failure(
                failures,
                "control_input_authority_violation",
                artifact=artifact,
                count=len(violations),
                samples=violations[:12],
            )
    contract_for_hash = copy.deepcopy(contract)
    self_hash = contract_for_hash.get("self_hash")
    if isinstance(self_hash, dict):
        self_hash.pop("sha256", None)
    actual_self_hash = CORE.stable_sha256(contract_for_hash)
    if actual_self_hash != frozen.contract_self_hash_sha256:
        CORE.add_failure(
            failures,
            "decision_contract_self_hash_mismatch",
            actual=actual_self_hash,
        )
    expected_contract = {
        "schema": "gtos.b7_5.post_acceleration_decision_contract.v1",
        "status": (
            "SEALED_POST_ACCELERATION_REPLAY_FREE_DECISION_CONTRACT_VALID"
        ),
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
    }
    for key, value in expected_contract.items():
        if contract.get(key) != value:
            CORE.add_failure(
                failures,
                "decision_contract_boundary_mismatch",
                field=key,
            )
    authority = contract.get("authority_boundary")
    authority = authority if isinstance(authority, Mapping) else {}
    expected_authority = {
        "broker_live_final_authority": False,
        "broker_mutation_enabled": False,
        "decision_contract_only": True,
        "outcomes_evaluated": False,
        "real_order_transmission_possible": False,
        "replay_launched": False,
    }
    if authority != expected_authority:
        CORE.add_failure(
            failures,
            "decision_contract_authority_boundary_mismatch",
        )
    if (
        contract.get("denominator") != dict(frozen.denominator)
        or contract.get("matched_risk") != dict(frozen.matched_risk)
    ):
        CORE.add_failure(failures, "decision_contract_economics_mismatch")
    attribution = contract.get("factorial_contract", {}).get(
        "attribution"
    )
    expected_attribution = {
        "selection": "S1R0-S0R0",
        "sizing": "S0R1-S0R0",
        "interaction": "S1R1-S1R0-S0R1+S0R0",
        "total_incumbent_value": "S1R1-S0R0",
    }
    if attribution != expected_attribution:
        CORE.add_failure(
            failures,
            "factorial_attribution_contract_mismatch",
        )
    return protocol, contract, {
        "protocol": protocol_record,
        "decision_contract": contract_record,
    }


def validate_post_acceleration_core_paths(config: Any) -> None:
    expected = {
        "artifact_root": DENOMINATOR_ROUTE,
        "protocol": PROTOCOL_PATH,
        "decision_contract": CONTRACT_PATH,
        "output": OUTPUT_PATH,
    }
    actual = {
        "artifact_root": config.artifact_root,
        "protocol": config.protocol_path,
        "decision_contract": config.contract_path,
        "output": config.output_path,
    }
    failures: list[str] = []
    for label, expected_path in expected.items():
        actual_path = actual[label]
        if not _path_equal(actual_path, expected_path):
            failures.append(f"{label}:sealed_path_mismatch")
        elif actual_path.is_symlink():
            failures.append(f"{label}:symlink_forbidden")
        elif label == "artifact_root" and not actual_path.is_dir():
            failures.append(f"{label}:missing")
        elif label not in {"artifact_root", "output"} and not actual_path.is_file():
            failures.append(f"{label}:missing")
    if failures:
        raise JanuaryAuditError(
            "january_core_production_path_binding_invalid:"
            + "|".join(failures)
        )


def _january_summary_binding_validator(
    original: Any,
    surface: Any,
    frozen: Any,
    failures: list[dict[str, Any]],
) -> None:
    for field_name, expected in (
        ("date_start", WINDOW_START),
        ("date_end", WINDOW_END),
    ):
        actual = surface.summary.get(field_name)
        if actual != expected:
            CORE.add_failure(
                failures,
                "january_summary_window_mismatch",
                arm_id=surface.arm_id,
                field=field_name,
                expected=expected,
                actual=actual,
            )
    proxy = copy.copy(surface)
    proxy.summary = (
        project_post_acceleration_summary_for_frozen_core(
            surface.arm_id,
            surface.summary,
            failures,
        )
        if frozen == JANUARY_FROZEN
        else copy.deepcopy(surface.summary)
    )
    proxy.summary["date_start"] = "2026-06-04"
    proxy.summary["date_end"] = "2026-06-04"
    original(proxy, frozen, failures)


@contextmanager
def adapt_frozen_june_core(config: AnalyzerConfig, *, production: bool) -> Any:
    """Temporarily bind the imported immutable core to the January window."""

    with _CORE_ADAPTER_LOCK:
        originals = {
            "DEFAULT_FROZEN": CORE.DEFAULT_FROZEN,
            "DEFAULT_PREFIXES": CORE.DEFAULT_PREFIXES,
            "OUTPUT_PATH": CORE.OUTPUT_PATH,
            "validate_summary_binding": CORE.validate_summary_binding,
            "validate_protocol_and_contract": (
                CORE.validate_protocol_and_contract
            ),
            "validate_production_path_bindings": (
                CORE.validate_production_path_bindings
            ),
            "update_scorecard_identity": CORE.update_scorecard_identity,
            "update_missed": CORE.update_missed,
            "missed_transition_rollup": CORE.missed_transition_rollup,
            "namespace_paths": CORE.namespace_paths,
        }
        original_validator = CORE.validate_summary_binding
        storage_session = NamespaceStorageSession(config)

        def january_validator(
            surface: Any,
            frozen: Any,
            failures: list[dict[str, Any]],
        ) -> None:
            _january_summary_binding_validator(
                original_validator,
                surface,
                frozen,
                failures,
            )

        try:
            if production:
                CORE.DEFAULT_FROZEN = JANUARY_FROZEN
                CORE.DEFAULT_PREFIXES = dict(JANUARY_PREFIXES)
                CORE.OUTPUT_PATH = OUTPUT_PATH
            CORE.validate_summary_binding = january_validator
            if production:
                CORE.validate_protocol_and_contract = (
                    validate_post_acceleration_protocol_and_contract
                )
                CORE.validate_production_path_bindings = (
                    validate_post_acceleration_core_paths
                )
            CORE.update_scorecard_identity = update_scorecard_identity_set
            CORE.update_missed = update_missed_with_exact_evidence_class
            CORE.missed_transition_rollup = (
                lambda missed_surface, source_trade_surface, candidate_keys: (
                    missed_transition_rollup_distinct_economics(
                        originals["missed_transition_rollup"],
                        missed_surface,
                        source_trade_surface,
                        candidate_keys,
                    )
                )
            )
            CORE.namespace_paths = lambda root, prefix: (
                storage_session.namespace_paths(
                    originals["namespace_paths"],
                    root,
                    prefix,
                )
            )
            yield storage_session
        finally:
            CORE.DEFAULT_FROZEN = originals["DEFAULT_FROZEN"]
            CORE.DEFAULT_PREFIXES = originals["DEFAULT_PREFIXES"]
            CORE.OUTPUT_PATH = originals["OUTPUT_PATH"]
            CORE.validate_summary_binding = originals["validate_summary_binding"]
            CORE.validate_protocol_and_contract = originals[
                "validate_protocol_and_contract"
            ]
            CORE.validate_production_path_bindings = originals[
                "validate_production_path_bindings"
            ]
            CORE.update_scorecard_identity = originals[
                "update_scorecard_identity"
            ]
            CORE.update_missed = originals["update_missed"]
            CORE.missed_transition_rollup = originals[
                "missed_transition_rollup"
            ]
            CORE.namespace_paths = originals["namespace_paths"]


def _parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 10:
        text += "T00:00:00+00:00"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _in_january(value: Any) -> bool:
    parsed = _parse_utc(value)
    start = _parse_utc(WINDOW_START)
    end = _parse_utc(WINDOW_END_EXCLUSIVE)
    return bool(parsed is not None and start is not None and end is not None and start <= parsed < end)


def _row_window_evidence(row: Mapping[str, Any]) -> list[tuple[str, Any]]:
    evidence: list[tuple[str, Any]] = []
    for field_name in ("decision_time_utc", "decision_time"):
        value = row.get(field_name)
        if value not in (None, ""):
            evidence.append((field_name, value))
            break
    window_id = str(row.get("decision_window_id") or "")
    if window_id.startswith("timewarp:"):
        evidence.append(("decision_window_id", window_id.removeprefix("timewarp:")))
    key = CORE.identity_key(row)
    match = _IDENTITY_TIME_RE.search(key) if key else None
    if match is not None:
        evidence.append(("candidate_instance_key", match.group("timestamp")))
    return evidence


def validate_namespace_window_membership(
    config: AnalyzerConfig,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    checked_rows: dict[str, dict[str, int]] = {}
    accepted_terminal_sentinels: list[dict[str, Any]] = []
    required_kinds = ("decision", "scorecard", "order", "trade", "missed")
    for arm_id in ARM_ORDER:
        paths = CORE.namespace_paths(config.artifact_root, config.prefixes[arm_id])
        checked_rows[arm_id] = {}
        for kind in required_kinds:
            row_count = 0
            path = paths[kind]
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    row_count += 1
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise JanuaryAuditError(
                            f"january_window_scan_invalid_json:{path}:{line_number}:{exc}"
                        ) from exc
                    if not isinstance(row, dict):
                        raise JanuaryAuditError(
                            f"january_window_scan_row_not_object:{path}:{line_number}"
                        )
                    evidence = _row_window_evidence(row)
                    if not evidence:
                        failures.append(
                            {
                                "arm_id": arm_id,
                                "artifact": kind,
                                "line": line_number,
                                "reason": "decision_window_evidence_missing",
                            }
                        )
                        continue
                    invalid = [
                        {"field": field_name, "value": value}
                        for field_name, value in evidence
                        if not _in_january(value)
                    ]
                    if invalid:
                        if (
                            kind == "decision"
                            and invalid
                            == [
                                {
                                    "field": "decision_time_utc",
                                    "value": (
                                        "2026-02-01T00:00:00+00:00"
                                    ),
                                }
                            ]
                            and is_january_terminal_no_session_sentinel(
                                row,
                                arm_id=arm_id,
                                frozen=config.frozen,
                            )
                        ):
                            accepted_terminal_sentinels.append(
                                {
                                    "arm_id": arm_id,
                                    "artifact": kind,
                                    "line": line_number,
                                    "symbol": row.get("symbol"),
                                    "trading_day": row.get("trading_day"),
                                    "decision_time_utc": row.get(
                                        "decision_time_utc"
                                    ),
                                }
                            )
                            continue
                        failures.append(
                            {
                                "arm_id": arm_id,
                                "artifact": kind,
                                "line": line_number,
                                "reason": "decision_window_outside_development_january",
                                "invalid_evidence": invalid,
                            }
                        )
                    checked_rows[arm_id][kind] = row_count
    expected_sentinel_identities = {
        (arm_id, symbol)
        for arm_id in ARM_ORDER
        for symbol in JANUARY_TERMINAL_DECISION_SYMBOLS
    }
    observed_sentinel_identities = [
        (str(row.get("arm_id") or ""), str(row.get("symbol") or ""))
        for row in accepted_terminal_sentinels
    ]
    observed_sentinel_set = set(observed_sentinel_identities)
    if production_mode(config) and (
        len(observed_sentinel_identities)
        != len(expected_sentinel_identities)
        or observed_sentinel_set != expected_sentinel_identities
    ):
        failures.append(
            {
                "reason": "terminal_no_session_sentinel_inventory_invalid",
                "expected_count": len(expected_sentinel_identities),
                "actual_count": len(observed_sentinel_identities),
                "duplicate_count": (
                    len(observed_sentinel_identities)
                    - len(observed_sentinel_set)
                ),
                "missing_samples": [
                    {"arm_id": arm_id, "symbol": symbol}
                    for arm_id, symbol in sorted(
                        expected_sentinel_identities
                        - observed_sentinel_set
                    )[:24]
                ],
                "unexpected_samples": [
                    {"arm_id": arm_id, "symbol": symbol}
                    for arm_id, symbol in sorted(
                        observed_sentinel_set
                        - expected_sentinel_identities
                    )[:24]
                ],
            }
        )
    return {
        "valid": not failures,
        "window_id": WINDOW_ID,
        "start_inclusive": WINDOW_START,
        "end_inclusive": WINDOW_END,
        "checked_artifact_kinds": list(required_kinds),
        "checked_rows": checked_rows,
        "accepted_terminal_no_session_sentinel_count": len(
            accepted_terminal_sentinels
        ),
        "accepted_terminal_no_session_sentinel_root_sha256": (
            CORE.stable_sha256(accepted_terminal_sentinels)
        ),
        "terminal_sentinel_contract": (
            "jan31_zero_candidate_no_session_asof_row_at_exclusive_midnight"
        ),
        "failure_count": len(failures),
        "failure_samples": failures[:32],
    }


def scan_scorecard_causal_projection(
    config: AnalyzerConfig,
    arm_id: str,
) -> list[dict[str, Any]]:
    paths = CORE.namespace_paths(
        config.artifact_root,
        config.prefixes[arm_id],
    )
    rows: list[dict[str, Any]] = []
    with paths["scorecard"].open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise JanuaryAuditError(
                    f"january_scorecard_causal_row_not_object:"
                    f"{arm_id}:{line_number}"
                )
            window, pool = CORE.hard_pool_from_scorecard(row)
            rows.append(
                {
                    "window": window,
                    "sort_key": str(
                        row.get("decision_time_utc")
                        or row.get("candidate_instance_time_utc")
                        or window
                    ),
                    "hard_pool_keys": list(pool["keys"]),
                    "selected_keys": scorecard_selected_key_set(row),
                }
            )
    rows.sort(key=lambda row: (row["sort_key"], row["window"]))
    return rows


def reconcile_selection_pair_hard_pools(
    config: AnalyzerConfig,
) -> dict[str, Any]:
    projections = {
        arm_id: scan_scorecard_causal_projection(config, arm_id)
        for arm_id in ARM_ORDER
    }
    return {
        label: reconcile_hard_pool_sequences(
            left,
            right,
            projections[left],
            projections[right],
        )
        for label, left, right in (
            ("fixed_risk_selection_pair", "S0R0", "S1R0"),
            ("dynamic_risk_selection_pair", "S0R1", "S1R1"),
        )
    }


def apply_successor_hard_pool_reconciliation(
    base_audit: Mapping[str, Any],
    reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    if not CORE.verify_self_hash(base_audit):
        raise JanuaryAuditError(
            "january_pre_hard_pool_core_audit_self_hash_invalid"
        )
    payload = copy.deepcopy(dict(base_audit))
    payload.pop("self_hash", None)
    failures = list(payload.get("failures") or [])
    retained: list[dict[str, Any]] = []
    invalid_pairs: set[str] = set()
    for failure in failures:
        if failure.get("code") != "selection_pair_hard_pool_mismatch":
            retained.append(failure)
            continue
        pair = str(failure.get("pair") or "")
        causal = reconciliation.get(pair)
        if isinstance(causal, Mapping) and causal.get("valid") is True:
            continue
        invalid_pairs.add(pair)
        retained.append(failure)
    for pair, causal in reconciliation.items():
        if (
            isinstance(causal, Mapping)
            and causal.get("valid") is not True
            and pair not in invalid_pairs
        ):
            retained.append(
                {
                    "code": (
                        "selection_pair_hard_pool_causal_"
                        "reconciliation_invalid"
                    ),
                    "pair": pair,
                    "pre_divergence_mismatch_count": causal.get(
                        "pre_divergence_hard_pool_mismatch_count"
                    ),
                }
            )
    payload.setdefault("cross_arm_identity", {})[
        "selection_pair_hard_pools"
    ] = copy.deepcopy(dict(reconciliation))
    payload["failures"] = retained
    payload["valid"] = not retained
    audit_mode = payload.get("scope", {}).get("audit_mode")
    if payload["valid"]:
        payload["status"] = (
            "PASS_ENGINEERING_MATRIX_DEVELOPMENT_WINDOWS_AUTHORIZED"
            if audit_mode == "sealed_production_audit"
            else "PASS_TEST_ONLY_NON_PRODUCTION_AUDIT"
        )
    else:
        payload["status"] = (
            "FAIL_ENGINEERING_MATRIX_DEVELOPMENT_WINDOWS_BLOCKED"
        )
    return CORE.finalize_self_hash(payload)


def _core_config(config: AnalyzerConfig) -> Any:
    return CORE.AnalyzerConfig(
        artifact_root=config.artifact_root,
        protocol_path=config.protocol_path,
        contract_path=config.contract_path,
        output_path=config.output_path,
        prefixes=dict(config.prefixes),
        frozen=config.frozen,
    )


FROZEN_VERIFIER_ROW_COVERAGE_CONTRACT = (
    ("candidate_instance_identity", "counts", "scorecard"),
    ("candidate_instance_identity", "counts", "order"),
    ("candidate_instance_identity", "counts", "trade"),
    ("candidate_instance_identity", "counts", "missed"),
    ("entry_fill_terminal_lifecycle", "row_counts", "order"),
    ("entry_fill_terminal_lifecycle", "row_counts", "trade"),
)


def _exact_nonnegative_integer(value: Any) -> bool:
    return bool(
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def reconcile_frozen_verifier_row_coverage(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind frozen-verifier row consumption to the core's exact artifact scans."""

    arms = payload.get("arms")
    arms = arms if isinstance(arms, Mapping) else {}
    checks: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for arm_id in ARM_ORDER:
        arm = arms.get(arm_id)
        arm = arm if isinstance(arm, Mapping) else {}
        artifacts = arm.get("artifacts")
        artifacts = artifacts if isinstance(artifacts, Mapping) else {}
        verification = arm.get("verification")
        verification = (
            verification if isinstance(verification, Mapping) else {}
        )
        direct_scans = verification.get("direct_scans")
        direct_scans = (
            direct_scans if isinstance(direct_scans, Mapping) else {}
        )
        for scan_name, count_container_name, artifact_name in (
            FROZEN_VERIFIER_ROW_COVERAGE_CONTRACT
        ):
            expected_path = (
                f"arms.{arm_id}.artifacts.{artifact_name}.rows"
            )
            observed_path = (
                f"arms.{arm_id}.verification.direct_scans.{scan_name}."
                f"{count_container_name}.{artifact_name}_rows"
            )
            artifact = artifacts.get(artifact_name)
            artifact = artifact if isinstance(artifact, Mapping) else {}
            scan = direct_scans.get(scan_name)
            scan = scan if isinstance(scan, Mapping) else {}
            count_container = scan.get(count_container_name)
            count_container = (
                count_container
                if isinstance(count_container, Mapping)
                else {}
            )
            expected_present = "rows" in artifact
            observed_key = f"{artifact_name}_rows"
            observed_present = observed_key in count_container
            expected_rows = artifact.get("rows")
            observed_rows = count_container.get(observed_key)
            reason: str | None = None
            if not expected_present:
                reason = "expected_artifact_row_count_missing"
            elif not _exact_nonnegative_integer(expected_rows):
                reason = "expected_artifact_row_count_invalid"
            elif not observed_present:
                reason = "observed_verifier_row_count_missing"
            elif not _exact_nonnegative_integer(observed_rows):
                reason = "observed_verifier_row_count_invalid"
            elif observed_rows != expected_rows:
                reason = "verifier_artifact_row_count_mismatch"
            check = {
                "arm_id": arm_id,
                "scan": scan_name,
                "artifact": artifact_name,
                "expected_field_path": expected_path,
                "observed_field_path": observed_path,
                "expected_rows": expected_rows,
                "observed_rows": observed_rows,
                "valid": reason is None,
            }
            if reason is not None:
                check["reason"] = reason
                failures.append(copy.deepcopy(check))
            checks.append(check)

    expected_check_count = len(ARM_ORDER) * len(
        FROZEN_VERIFIER_ROW_COVERAGE_CONTRACT
    )
    passed_check_count = sum(row["valid"] is True for row in checks)
    valid = bool(
        len(checks) == expected_check_count
        and passed_check_count == expected_check_count
        and not failures
    )
    return {
        "schema": (
            "gtos.b7_5.selection_sizing."
            "frozen_verifier_row_coverage_reconciliation.v1"
        ),
        "status": (
            "PASS_FROZEN_VERIFIER_ROW_COVERAGE_RECONCILED"
            if valid
            else "FAIL_FROZEN_VERIFIER_ROW_COVERAGE_INCOMPLETE"
        ),
        "valid": valid,
        "expected_check_count": expected_check_count,
        "passed_check_count": passed_check_count,
        "failure_count": len(failures),
        "candidate_row_coverage_boundary": (
            "exact_relational_candidate_source_is_deduplicated_from_missed_"
            "order_trade_and_is_not_a_direct_artifact_row_count"
        ),
        "checks": checks,
        "failures": failures,
    }


def finalize_january_audit(
    base_audit: Mapping[str, Any],
    *,
    production: bool,
    control_record: Mapping[str, Any] | None,
    window_membership: Mapping[str, Any],
    namespace_storage: Mapping[str, Any],
    adapter_initial_sha256: str,
    adapter_final_sha256: str,
) -> dict[str, Any]:
    if not CORE.verify_self_hash(base_audit):
        raise JanuaryAuditError("january_core_audit_self_hash_invalid")
    payload = copy.deepcopy(dict(base_audit))
    payload.pop("self_hash", None)
    failures = list(payload.get("failures") or [])
    frozen_verifier_row_coverage = reconcile_frozen_verifier_row_coverage(
        payload
    )
    payload["frozen_verifier_row_coverage_reconciliation"] = (
        frozen_verifier_row_coverage
    )
    if frozen_verifier_row_coverage.get("valid") is not True:
        failures.append(
            {
                "code": "january_frozen_verifier_row_coverage_invalid",
                "count": 1,
                "mismatch_count": frozen_verifier_row_coverage.get(
                    "failure_count"
                ),
                "samples": frozen_verifier_row_coverage.get("failures", [])[
                    :24
                ],
            }
        )
    if production:
        control_bindings = (
            control_record.get("post_cold_arm_verification_bindings")
            if isinstance(control_record, Mapping)
            else None
        )
        control_bindings = (
            control_bindings
            if isinstance(control_bindings, Mapping)
            else {}
        )
        receipt_artifact_reconciliation = (
            reconcile_analyzed_artifacts_to_receipts(
                payload,
                control_bindings,
                namespace_storage,
            )
        )
        if receipt_artifact_reconciliation.get("valid") is not True:
            failures.append(
                {
                    "code": (
                        "january_analyzed_artifact_receipt_"
                        "reconciliation_invalid"
                    ),
                    "count": receipt_artifact_reconciliation.get(
                        "failure_count"
                    ),
                    "samples": receipt_artifact_reconciliation.get(
                        "failures",
                        [],
                    )[:24],
                }
            )
    else:
        receipt_artifact_reconciliation = {
            "schema": (
                "gtos.b7_5.selection_sizing."
                "analyzed_artifact_receipt_reconciliation.v1"
            ),
            "status": "TEST_ONLY_NOT_PRODUCTION_AUTHORITY",
            "valid": False,
            "production_authority": False,
        }
    payload["analyzed_artifact_receipt_reconciliation"] = (
        receipt_artifact_reconciliation
    )
    if window_membership.get("valid") is not True:
        failures.append(
            {
                "code": "january_window_membership_invalid",
                "count": window_membership.get("failure_count"),
                "samples": window_membership.get("failure_samples"),
            }
        )
    valid = bool(payload.get("valid") is True and not failures)
    verifier_control = payload.get("control_inputs", {}).get("verifier", {})
    production_evidence = bool(
        production
        and verifier_control.get("production_audit_authority") is True
        and verifier_control.get("injected_verifier_module") is False
        and verifier_control.get("frozen_sha256_match") is True
        and namespace_storage.get("valid") is True
        and namespace_storage.get(
            "all_logical_bytes_hashes_rows_and_newlines_reverified"
        )
        is True
        and receipt_artifact_reconciliation.get("valid") is True
        and namespace_storage.get("reader", {}).get("file_sha256")
        == COLD_EVIDENCE_READER_FILE_SHA256
    )
    if production and not production_evidence:
        raise JanuaryAuditError("january_production_verifier_authority_invalid")
    april_authorized = bool(valid and production_evidence)

    payload["schema"] = (
        "gtos.b7_5.selection_sizing.development_january_matrix_audit.v1"
    )
    if production:
        payload["status"] = (
            "PASS_DEVELOPMENT_JANUARY_MATRIX_ADVERSE_DEVELOPMENT_APRIL_AUTHORIZED"
            if april_authorized
            else "FAIL_DEVELOPMENT_JANUARY_MATRIX_ADVERSE_DEVELOPMENT_APRIL_BLOCKED"
        )
    else:
        payload["status"] = (
            "PASS_TEST_ONLY_NON_PRODUCTION_JANUARY_AUDIT"
            if valid
            else "FAIL_TEST_ONLY_NON_PRODUCTION_JANUARY_AUDIT"
        )
    payload["valid"] = valid
    payload["scope"] = {
        "window_id": WINDOW_ID,
        "window_role": WINDOW_ROLE,
        "window_start": WINDOW_START,
        "window_end": WINDOW_END,
        "arms": list(ARM_ORDER),
        "replay_launched_by_builder": False,
        "outcome_artifact_glob_used": False,
        "march_outcome_read": False,
        "audit_mode": (
            "sealed_production_development_window_audit"
            if production
            else "test_only_non_production"
        ),
    }
    payload["window_membership"] = copy.deepcopy(dict(window_membership))
    payload["namespace_storage"] = copy.deepcopy(dict(namespace_storage))
    payload.setdefault("control_inputs", {})[
        "development_january_window_control"
    ] = (
        copy.deepcopy(dict(control_record))
        if control_record is not None
        else {
            "production_authority": False,
            "status": "test_only_control_not_consulted",
        }
    )
    payload["control_inputs"]["development_january_adapter"] = {
        "path": str(ANALYZER_PATH),
        "initial_sha256": adapter_initial_sha256,
        "post_audit_sha256": adapter_final_sha256,
        "stable_during_audit": adapter_initial_sha256 == adapter_final_sha256,
        "june_core_path": str(CORE_ANALYZER_PATH),
        "june_core_sha256": CORE_ANALYZER_SHA256,
        "june_core_modified": False,
    }
    suppression = payload.get("suppression_and_missed_reconciliation")
    if isinstance(suppression, dict):
        suppression.pop("june_window_is_engineering_smoke_only", None)
        suppression["window_role"] = WINDOW_ROLE
        suppression["development_window"] = True
        suppression["economic_improvement_claim_authorized"] = False
    payload["failures"] = failures
    payload["failure_count"] = len(failures)
    payload["disposition"] = {
        "development_january_matrix_hard_valid": valid,
        "window_matrix_accepted_for_pooled_development_analysis": april_authorized,
        "adverse_development_april_authorized": april_authorized,
        "next_protocol_window": NEXT_PROTOCOL_WINDOW if april_authorized else None,
        "development_disposition_frozen": False,
        "factor_or_policy_promotion_authorized": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "canary_authority": False,
        "final_selection_claim": False,
        "challenge_window_authorized": False,
        "march_outcome_read": False,
    }
    return CORE.finalize_self_hash(payload)


def build_audit(
    config: AnalyzerConfig = DEFAULT_CONFIG,
    *,
    verifier_module: Any | None = None,
) -> dict[str, Any]:
    production = production_mode(config)
    if production and verifier_module is not None:
        raise JanuaryAuditError("production_verifier_module_injection_forbidden")
    control_record = validate_production_control(config) if production else None
    adapter_initial_sha256 = sha256_file(ANALYZER_PATH)
    try:
        with adapt_frozen_june_core(config, production=production) as storage:
            base_audit = CORE.build_audit(
                _core_config(config),
                verifier_module=verifier_module,
            )
            if production:
                hard_pool_reconciliation = (
                    reconcile_selection_pair_hard_pools(config)
                )
                base_audit = apply_successor_hard_pool_reconciliation(
                    base_audit,
                    hard_pool_reconciliation,
                )
            window_membership = validate_namespace_window_membership(config)
            namespace_storage = storage.audit_record()
    except COLD_EVIDENCE.ColdEvidenceError as exc:
        raise JanuaryAuditError(
            f"development_january_cold_evidence_invalid:{exc}"
        ) from exc
    adapter_final_sha256 = sha256_file(ANALYZER_PATH)
    if adapter_initial_sha256 != adapter_final_sha256:
        raise JanuaryAuditError("january_adapter_mutated_during_audit")
    if production and sha256_file(CONTROL_PATH) != CONTROL_FILE_SHA256:
        raise JanuaryAuditError("january_window_control_mutated_during_audit")
    return finalize_january_audit(
        base_audit,
        production=production,
        control_record=control_record,
        window_membership=window_membership,
        namespace_storage=namespace_storage,
        adapter_initial_sha256=adapter_initial_sha256,
        adapter_final_sha256=adapter_final_sha256,
    )


def verify_self_hash(payload: Mapping[str, Any]) -> bool:
    return CORE.verify_self_hash(payload)


def write_audit(path: Path, payload: Mapping[str, Any]) -> None:
    CORE.write_audit(path, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run the complete sealed January audit without writing output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = DEFAULT_CONFIG
    try:
        audit = build_audit(config)
    except CORE.IncompleteNamespaceError as exc:
        print(
            json.dumps(
                {"status": "INCOMPLETE_JANUARY_MATRIX_NAMESPACE", "error": str(exc)},
                sort_keys=True,
            )
        )
        return 2
    except (JanuaryAuditError, CORE.MatrixAuditError) as exc:
        print(
            json.dumps(
                {"status": "JANUARY_MATRIX_AUDIT_INPUT_INVALID", "error": str(exc)},
                sort_keys=True,
            )
        )
        return 2
    if not args.check:
        write_audit(config.output_path, audit)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "valid": audit["valid"],
                "failure_count": audit["failure_count"],
                "self_hash_sha256": audit["self_hash"]["sha256"],
                "output_path": None if args.check else str(config.output_path),
                "check_only": bool(args.check),
                "next_protocol_window": audit["disposition"][
                    "next_protocol_window"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if audit["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
