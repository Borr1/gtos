#!/usr/bin/env python3
"""Certify the sealed B7.5 June selection/sizing factorial matrix.

The builder is deliberately replay-free and reads only the four explicitly
bound engineering prefixes.  It refuses incomplete namespaces before opening
any outcome artifact, reuses the route verifier's pure scan functions, and
publishes one deterministic self-hashed audit after all inputs are complete.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
DENOMINATOR_ROUTE = (
    REPO_ROOT
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
VERIFIER_PATH = DENOMINATOR_ROUTE / "verify_denominator_to_deployment_execution.py"
VERIFIER_CODE_AUTHORITY_PATH = str(VERIFIER_PATH.relative_to(REPO_ROOT))
FROZEN_VERIFIER_SHA256 = (
    "4d93308430561b7f886c88633c64a494fecdb0b3e114dff128652ebaec4dac28"
)
PROTOCOL_PATH = ROUTE / "B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json"
CONTRACT_PATH = ROUTE / "B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
OUTPUT_PATH = (
    ROUTE
    / "B7_5_SELECTION_SIZING_ENGINEERING_JUNE_04_SOURCE_REPAIRED_CAP_R2_MATRIX_AUDIT.json"
)
ANALYZER_PATH = Path(__file__).resolve()

PREFIX_STEM = "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_"
PREFIX_TAIL = "_SOURCE_REPAIRED_CAP_R2"
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
DEFAULT_PREFIXES = {arm: f"{PREFIX_STEM}{arm}{PREFIX_TAIL}" for arm in ARM_ORDER}

NAMESPACE_SUFFIXES = {
    "summary": "SUMMARY.json",
    "partial_summary": "PARTIAL_SUMMARY.json",
    "source": "SOURCE_UNIVERSE_LEDGER.jsonl",
    "decision": "DECISION_LEDGER.jsonl",
    "scorecard": "SCORECARD_LEDGER.jsonl",
    "order": "ORDER_LEDGER.jsonl",
    "trade": "TRADE_LEDGER.jsonl",
    "missed": "MISSED_OPPORTUNITY_LEDGER.jsonl",
    "oracle": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "bucket": "BUCKET_LEDGER.jsonl",
    "comparison": "COMPARISON_LEDGER.jsonl",
}
COMPLETED_PARTIAL_SUMMARY_SCHEMA = (
    "gtos.final_moonshot.broad_live_as_if_replay_harness.partial_summary.v1"
)
COMPLETED_PARTIAL_SUMMARY_SEMANTICS_SUFFIX = (
    "final_summary_required_for_completed_run"
)
JSONL_KINDS = tuple(
    kind for kind, suffix in NAMESPACE_SUFFIXES.items() if suffix.endswith(".jsonl")
)

SCAN_FUNCTIONS = (
    "scan_broad_factorial_risk_lifecycle_summary",
    "scan_broad_physical_trade_summary_parity",
    "scan_broad_order_trade_cost_authority",
    "scan_broad_selected_quality_source_contract",
    "scan_broad_missed_opportunity_semantics",
    "scan_broad_entry_fill_terminal_r_lifecycle_contract",
    "scan_cross_ledger_candidate_instance_identity",
    "scan_broad_selector_materialization_and_r_identity",
    "scan_broad_stop_hazard_cap_execution_authority",
    "scan_broad_executable_risk_and_fillability_atomicity",
    "scan_broad_selected_policy_replay_authority",
    "scan_broad_order_trade_path_provenance",
)
SUMMARY_ISSUE_FUNCTIONS = (
    "broad_summary_package_new_entry_authority_payload_contract_issues",
    "broad_summary_candidate_relational_materialization_issues",
    "broad_summary_ultimate_package_runtime_input_contract_issues",
    "broad_summary_capacity_safe_chunk_execution_issues",
    "broad_summary_source_authority_chunk_invariance_issues",
)
EXECUTABLE_RISK_ATOMICITY_SCAN = "executable_risk_fillability_atomicity"
EXECUTABLE_RISK_ATOMICITY_AGGREGATE_REASON = (
    "executable_risk_fillability_atomicity_leak"
)
EXECUTABLE_RISK_ATOMICITY_FIXED_BASIS_REASON = (
    "risk_cash_not_bound_to_final_risk_pct"
)
R0_FIXED_CASH_BASIS_SOURCE = (
    "sealed_frozen_initial_equity_not_current_balance"
)
R0_FIXED_CASH_DETAIL_FIELD = "b7_5_selection_sizing_factorial_risk_cash"
R0_FACTORIAL_BINDING_FIELD = "b7_5_selection_sizing_factorial_binding"
CANONICAL_EXECUTABLE_FINAL_RISK_ATOM_SCHEMA = (
    "gtos.runtime.canonical_executable_final_risk_atom.v1"
)
RISK_ALIASES = (
    "risk_pct",
    "final_approved_risk_pct",
    "runtime_final_risk_pct",
    "approved_risk_pct",
)
NESTED_RISK_ALIASES = (
    "final_approved_risk_pct",
    "runtime_final_risk_pct",
    "approved_risk_pct",
)
STRESS_SCENARIOS = {
    "extra_cost_0.05r_per_trade": 0.05,
    "extra_cost_0.10r_per_trade": 0.10,
    "extra_cost_0.20r_per_trade": 0.20,
}

FLOAT_TOLERANCE = 1e-8
CAP_TOLERANCE = 1e-9


class MatrixAuditError(RuntimeError):
    """Base class for fail-closed audit input errors."""


class IncompleteNamespaceError(MatrixAuditError):
    """Raised before any artifact is opened when a namespace is incomplete."""


@dataclass(frozen=True)
class FrozenBindings:
    source_plan_sha256: str
    contract_file_sha256: str
    contract_self_hash_sha256: str
    common_execution_input_sha256: str
    protocol_file_sha256: str
    protocol_economics_digest_sha256: str
    neutral_selection_seed_sha256: str
    arm_fingerprints: Mapping[str, str]
    binding_payloads: Mapping[str, str]
    shared_execution_contracts: Mapping[str, str]
    denominator: Mapping[str, Any]
    matched_risk: Mapping[str, Any]
    expected_candidate_count: int = 6981
    expected_decision_count: int = 2304
    expected_scorecard_count: int = 96
    expected_symbol_count: int = 24
    expected_profile: str = "repaired_package_conversion_v3"
    minimum_scoreable_risk_coverage: float = 0.8
    maximum_arm_scoreability_gap: float = 0.05
    materiality: float = 0.1


DEFAULT_FROZEN = FrozenBindings(
    source_plan_sha256=(
        "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
    ),
    contract_file_sha256=(
        "e55103455bc7c6b6c0ad6e1814e163a61a8ae050d4051feea219007076b8b2f6"
    ),
    contract_self_hash_sha256=(
        "a17277c24fed922e3aeb60656831ec8c0f60f5ff44523ec76f765f0eb84890fa"
    ),
    common_execution_input_sha256=(
        "b09f3e8a894e26c3066fb429207174e2f5d163ffe8bbb6bd7134395321438336"
    ),
    protocol_file_sha256=(
        "55ccc9a95647179fcf3e43acb2445b9b8ab4f2b146752cacc05b84bb8444be1a"
    ),
    protocol_economics_digest_sha256=(
        "7f2af455b5f126b0a76b014d9850bf2b7b6e066a18eb60978e78990794a5665b"
    ),
    neutral_selection_seed_sha256=(
        "0c6b87233ad895d981b6ace153e1c355862dde7989e66abd4ca99c93b4edaf3a"
    ),
    arm_fingerprints={
        "S0R0": "89fbe44e2adfe68c66550b9b18b4ec16a6325585c7d1d1c579f89bdc7839adb9",
        "S1R0": "080be2bf3e05acee849681546b2c8c63b6e800c86a79ccf2ff737f8b09533d10",
        "S0R1": "a96b106daa3c9ee0a1a4635b8943985db0e917c5e9020e81e9e853e3c56bbad9",
        "S1R1": "3db57b801f080f4c35b0bafb13c0a07b84b7ce44ab2d252f34109067acd6c35e",
    },
    binding_payloads={
        "S0R0": "3edc2bdd4438531daedb8e985059ded8c7ac267cde99dcf9c8456bc63ee3fd15",
        "S1R0": "08be312e29b614cbb9490edf7d6f43468954d134e3be4aff6688ca9ec8a3aabe",
        "S0R1": "bfcf8890fa831b7ebccb35ff8cdc5d93993837b763d461a54e4cd466d928b3fd",
        "S1R1": "e72236633ef992d5289fb7b246ed5fccd4a94216f621567fd49dd41d9e25b4f3",
    },
    shared_execution_contracts={
        "S0R0": "e20079e70216d9eb3cbf3243bbbda53445f93750e8c7a7cf3b2afed530a3f221",
        "S1R0": "4c4f91c240c12b671b13c1793ca0f6c28645cc8aed91599ee29c4fa214fd4642",
        "S0R1": "ab2b85e260719559ddeb268e8858d37ab67581c67c93044ba6756a23f35c53a0",
        "S1R1": "38017e04aec08fde2938c96d185b5dad1236ec7ea99a2f4488c2574304a828cd",
    },
    denominator={
        "initial_equity_cash": 100000.0,
        "fixed_account_risk_unit_pct": 0.1,
        "fixed_account_risk_unit_cash": 100.0,
        "fixed_denominator_portfolio_r_cash": 100.0,
    },
    matched_risk={
        "same_ex_ante_rules_all_arms": True,
        "daily_accepted_risk_pct_cap": 4.0,
        "peak_open_plus_pending_risk_pct_cap": 4.0,
        "cluster_risk_pct_cap": 1.5,
        "opening_window_risk_pct_cap": 1.0,
        "pending_to_open_transfer_once": True,
        "expiry_or_close_release_once": True,
        "ex_post_rescaling_forbidden": True,
    },
)


@dataclass(frozen=True)
class AnalyzerConfig:
    artifact_root: Path = DENOMINATOR_ROUTE
    protocol_path: Path = PROTOCOL_PATH
    contract_path: Path = CONTRACT_PATH
    output_path: Path = OUTPUT_PATH
    prefixes: Mapping[str, str] = field(default_factory=lambda: dict(DEFAULT_PREFIXES))
    frozen: FrozenBindings = DEFAULT_FROZEN


@dataclass
class ArmSurface:
    arm_id: str
    prefix: str
    summary: dict[str, Any]
    paths: dict[str, Path]
    artifacts: dict[str, dict[str, Any]]
    candidate_keys: set[str] = field(default_factory=set)
    decision_windows: set[str] = field(default_factory=set)
    hard_pools: dict[str, dict[str, Any]] = field(default_factory=dict)
    scorecard_selected: dict[str, dict[str, Any]] = field(default_factory=dict)
    order_events_by_id: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    order_instances: dict[str, dict[str, Any]] = field(default_factory=dict)
    trades: dict[str, dict[str, Any]] = field(default_factory=dict)
    trade_ids: set[str] = field(default_factory=set)
    missed_by_key: dict[str, dict[str, Any]] = field(default_factory=dict)
    missed: dict[str, Any] = field(default_factory=dict)
    economics: dict[str, Any] = field(default_factory=dict)
    binding_mismatch_count: int = 0
    binding_mismatch_samples: list[dict[str, Any]] = field(default_factory=list)
    authority_violation_count: int = 0
    authority_violation_samples: list[dict[str, Any]] = field(default_factory=list)
    relational_identity_failures: list[dict[str, Any]] = field(default_factory=list)
    relational_identity_audit: dict[str, Any] = field(default_factory=dict)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def stable_sha256(payload: Any) -> str:
    return sha256_bytes(canonical_bytes(payload))


def read_json_object(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MatrixAuditError(f"invalid_json:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise MatrixAuditError(f"json_not_object:{path}")
    return payload, {
        "path": str(path),
        "bytes": len(raw),
        "rows": 1,
        "sha256": sha256_bytes(raw),
    }


def numeric(value: Any, *, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise MatrixAuditError(f"numeric_missing_or_invalid:{label}:{value!r}") from exc
    if not math.isfinite(result):
        raise MatrixAuditError(f"numeric_nonfinite:{label}:{value!r}")
    return result


def integer(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise MatrixAuditError(f"integer_invalid:{label}:{value!r}")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise MatrixAuditError(f"integer_missing_or_invalid:{label}:{value!r}") from exc
    if not math.isfinite(parsed) or not parsed.is_integer():
        raise MatrixAuditError(f"integer_missing_or_invalid:{label}:{value!r}")
    return int(parsed)


def close(left: Any, right: Any, tolerance: float = FLOAT_TOLERANCE) -> bool:
    try:
        a = float(left)
        b = float(right)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance


def identity_key(row: Mapping[str, Any]) -> str:
    for key in (
        "canonical_replay_candidate_instance_key",
        "candidate_instance_parity_key",
        "source_bound_replay_candidate_instance_key",
    ):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc") or row.get("decision_time") or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""


def arm_factors(arm_id: str) -> tuple[str, str, str, str]:
    selection = arm_id[:2]
    sizing = arm_id[2:]
    return (
        selection,
        sizing,
        "neutral_hash_hard_eligible"
        if selection == "S0"
        else "quality_ranked_current",
        "fixed_equal_account_risk" if sizing == "R0" else "dynamic_runtime",
    )


def expected_flat_binding(arm_id: str, frozen: FrozenBindings) -> dict[str, Any]:
    selection, sizing, selection_mode, sizing_mode = arm_factors(arm_id)
    denominator = frozen.denominator
    matched = frozen.matched_risk
    return {
        "b7_5_selection_sizing_factorial_decision_contract_sha256": frozen.contract_self_hash_sha256,
        "b7_5_selection_sizing_factorial_common_execution_input_digest_sha256": frozen.common_execution_input_sha256,
        "b7_5_selection_sizing_factorial_binding_payload_sha256": frozen.binding_payloads[arm_id],
        "b7_5_selection_sizing_factorial_protocol_economics_digest_sha256": frozen.protocol_economics_digest_sha256,
        "b7_5_selection_sizing_factorial_arm_id": arm_id,
        "b7_5_selection_sizing_factorial_arm_fingerprint_sha256": frozen.arm_fingerprints[arm_id],
        "b7_5_selection_sizing_factorial_selection_factor": selection,
        "b7_5_selection_sizing_factorial_sizing_factor": sizing,
        "b7_5_selection_sizing_factorial_selection_mode": selection_mode,
        "b7_5_selection_sizing_factorial_sizing_mode": sizing_mode,
        "b7_5_selection_sizing_factorial_neutral_selection_seed_sha256": frozen.neutral_selection_seed_sha256,
        "b7_5_selection_sizing_factorial_initial_equity_cash": denominator["initial_equity_cash"],
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_pct": denominator["fixed_account_risk_unit_pct"],
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_cash": denominator["fixed_account_risk_unit_cash"],
        "b7_5_selection_sizing_factorial_fixed_denominator_portfolio_r_cash": denominator["fixed_denominator_portfolio_r_cash"],
        "b7_5_selection_sizing_factorial_daily_accepted_risk_pct_cap": matched["daily_accepted_risk_pct_cap"],
        "b7_5_selection_sizing_factorial_peak_open_plus_pending_risk_pct_cap": matched["peak_open_plus_pending_risk_pct_cap"],
        "b7_5_selection_sizing_factorial_cluster_risk_pct_cap": matched["cluster_risk_pct_cap"],
        "b7_5_selection_sizing_factorial_opening_window_risk_pct_cap": matched["opening_window_risk_pct_cap"],
        "b7_5_selection_sizing_factorial_pending_to_open_transfer_once": True,
        "b7_5_selection_sizing_factorial_expiry_or_close_release_once": True,
        "b7_5_selection_sizing_factorial_ex_post_rescaling_forbidden": True,
        "b7_5_selection_sizing_factorial_uses_outcome_fields": False,
        "b7_5_selection_sizing_factorial_live_broker_authority": False,
        "b7_5_selection_sizing_factorial_broker_mutation_enabled": False,
    }


def namespace_paths(root: Path, prefix: str) -> dict[str, Path]:
    return {kind: root / f"{prefix}_{suffix}" for kind, suffix in NAMESPACE_SUFFIXES.items()}


def preflight_namespaces(config: AnalyzerConfig) -> dict[str, dict[str, Path]]:
    """Check only directory entries/stat metadata; never open partial outcomes."""

    if set(config.prefixes) != set(ARM_ORDER):
        raise IncompleteNamespaceError("exact_four_arm_prefix_map_required")
    if config.frozen == DEFAULT_FROZEN:
        prefix_failures = [
            f"{arm_id}:default_prefix_mismatch"
            for arm_id in ARM_ORDER
            if config.prefixes[arm_id] != DEFAULT_PREFIXES[arm_id]
        ]
        if prefix_failures:
            raise IncompleteNamespaceError(
                "incomplete_matrix_namespace:" + "|".join(prefix_failures)
            )
    all_paths: dict[str, dict[str, Path]] = {}
    failures: list[str] = []
    root = config.artifact_root.resolve()
    for arm_id in ARM_ORDER:
        paths = namespace_paths(config.artifact_root, config.prefixes[arm_id])
        all_paths[arm_id] = paths
        for kind, path in paths.items():
            if path.parent.resolve() != root:
                failures.append(f"{arm_id}:{kind}:outside_artifact_root")
            elif path.is_symlink():
                failures.append(f"{arm_id}:{kind}:symlink_forbidden")
            elif not path.is_file():
                failures.append(f"{arm_id}:{kind}:missing")
            elif kind != "comparison" and path.stat().st_size <= 0:
                failures.append(f"{arm_id}:{kind}:empty")
    if failures:
        raise IncompleteNamespaceError("incomplete_matrix_namespace:" + "|".join(failures))
    return all_paths


def validate_production_path_bindings(config: AnalyzerConfig) -> None:
    """Seal production reads to the declared route and immutable control paths."""

    if config.frozen != DEFAULT_FROZEN:
        return
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
        if Path(os.path.abspath(actual_path)) != Path(os.path.abspath(expected_path)):
            failures.append(f"{label}:sealed_path_mismatch")
            continue
        if actual_path.is_symlink():
            failures.append(f"{label}:symlink_forbidden")
            continue
        if label == "output":
            continue
        try:
            if actual_path.resolve(strict=True) != expected_path.resolve(strict=True):
                failures.append(f"{label}:sealed_path_mismatch")
        except OSError:
            failures.append(f"{label}:missing")
    if failures:
        raise MatrixAuditError("production_path_binding_invalid:" + "|".join(failures))


def stat_identity(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def file_fingerprint(path: Path) -> dict[str, Any]:
    try:
        before = stat_identity(path)
        digest = sha256_file(path)
        after = stat_identity(path)
    except OSError as exc:
        raise IncompleteNamespaceError(f"namespace_file_unavailable:{path}:{exc}") from exc
    if before != after:
        raise MatrixAuditError(f"namespace_file_mutated_while_hashing:{path}")
    return {"bytes": after[2], "sha256": digest, "stat_identity": list(after)}


def validate_partial_completion_markers(
    paths_by_arm: Mapping[str, Mapping[str, Path]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    """Open only partial summaries after metadata completeness, before other outcomes."""

    records: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    failures: list[str] = []
    for arm_id in ARM_ORDER:
        path = paths_by_arm[arm_id]["partial_summary"]
        payload, record = read_json_object(path)
        semantics = str(payload.get("partial_summary_semantics") or "")
        if payload.get("schema") != COMPLETED_PARTIAL_SUMMARY_SCHEMA:
            failures.append(f"{arm_id}:partial_summary:completion_schema_invalid")
        if not semantics.endswith(COMPLETED_PARTIAL_SUMMARY_SEMANTICS_SUFFIX):
            failures.append(f"{arm_id}:partial_summary:completion_semantics_invalid")
        prefix = payload.get("output_prefix")
        expected_prefix = path.name[: -len("_PARTIAL_SUMMARY.json")]
        if prefix != expected_prefix:
            failures.append(f"{arm_id}:partial_summary:prefix_mismatch")
        records[arm_id] = (payload, record)
    if failures:
        raise IncompleteNamespaceError(
            "incomplete_matrix_namespace:" + "|".join(failures)
        )
    return records


def capture_namespace_fingerprints(
    paths_by_arm: Mapping[str, Mapping[str, Path]],
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        arm_id: {
            kind: file_fingerprint(path)
            for kind, path in paths_by_arm[arm_id].items()
        }
        for arm_id in ARM_ORDER
    }


def load_verifier(path: Path = VERIFIER_PATH) -> Any:
    spec = importlib.util.spec_from_file_location("b7_5_matrix_verifier", path)
    if spec is None or spec.loader is None:
        raise MatrixAuditError(f"verifier_import_spec_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    missing = [name for name in (*SCAN_FUNCTIONS, *SUMMARY_ISSUE_FUNCTIONS) if not hasattr(module, name)]
    if not hasattr(module, "ExactRelationalCandidateSource"):
        missing.append("ExactRelationalCandidateSource")
    if missing:
        raise MatrixAuditError("verifier_api_missing:" + "|".join(sorted(missing)))
    return module


def recursive_authority_violations(value: Any, path: str = "$") -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            child = f"{path}.{key}"
            if key in {
                "broker_mutation_enabled",
                "broker_live_authority",
                "live_broker_authority",
                "final_selection_claim",
                "canary_authority",
                "deployment_authority",
                "production_authority",
            } and nested is not False:
                yield child
            if key in {"order_send_attempts", "broker_send_attempts"}:
                values = nested.values() if isinstance(nested, Mapping) else (nested,)
                for value in values:
                    try:
                        if integer(value, label=child) != 0:
                            yield child
                            break
                    except MatrixAuditError:
                        yield child
                        break
            yield from recursive_authority_violations(nested, child)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from recursive_authority_violations(nested, f"{path}[{index}]")


def validate_flat_binding(
    surface: ArmSurface,
    row: Mapping[str, Any],
    *,
    kind: str,
    line_number: int,
    expected: Mapping[str, Any],
) -> None:
    mismatches = [key for key, value in expected.items() if row.get(key) != value]
    if mismatches:
        surface.binding_mismatch_count += 1
        if len(surface.binding_mismatch_samples) < 12:
            surface.binding_mismatch_samples.append(
                {"artifact": kind, "line": line_number, "fields": mismatches[:25]}
            )
    record_authority_violations(
        surface,
        row,
        artifact=kind,
        location=f"line:{line_number}",
    )


def record_authority_violations(
    surface: ArmSurface,
    payload: Any,
    *,
    artifact: str,
    location: str,
) -> None:
    for violation in recursive_authority_violations(payload):
        surface.authority_violation_count += 1
        if len(surface.authority_violation_samples) < 12:
            surface.authority_violation_samples.append(
                {"artifact": artifact, "location": location, "path": violation}
            )


def hard_pool_from_scorecard(row: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    finalizer = row.get("risk_admitted_scheduler_finalizer")
    finalizer = finalizer if isinstance(finalizer, Mapping) else {}
    window = str(
        finalizer.get("b7_5_selection_sizing_factorial_decision_window_id")
        or row.get("decision_window_id")
        or row.get("stable_decision_window_id")
        or ""
    ).strip()
    raw_keys = finalizer.get("b7_5_selection_sizing_factorial_hard_eligible_instance_keys")
    if not isinstance(raw_keys, list):
        raise MatrixAuditError(f"scorecard_hard_pool_keys_missing:{window or 'unknown'}")
    keys = [str(value) for value in raw_keys]
    if not window or any(not value for value in keys) or len(keys) != len(set(keys)):
        raise MatrixAuditError(f"scorecard_hard_pool_identity_invalid:{window or 'unknown'}")
    count = integer(
        finalizer.get("b7_5_selection_sizing_factorial_hard_eligible_pool_count"),
        label=f"hard_pool_count:{window}",
    )
    digest = str(
        finalizer.get("b7_5_selection_sizing_factorial_hard_eligible_pool_digest_sha256")
        or ""
    )
    sorted_keys = sorted(keys)
    if count != len(sorted_keys) or digest != stable_sha256(sorted_keys):
        raise MatrixAuditError(f"scorecard_hard_pool_digest_or_count_invalid:{window}")
    return window, {"count": count, "keys": sorted_keys, "digest": digest}


def record_relational_failure(
    surface: ArmSurface,
    reason: str,
    **detail: Any,
) -> None:
    surface.relational_identity_failures.append({"reason": reason, **detail})


def update_scorecard_identity(
    surface: ArmSurface,
    row: Mapping[str, Any],
    *,
    window: str,
    hard_pool: Mapping[str, Any],
    line_number: int,
) -> None:
    identity_fields = (
        "selected_candidate_instance_key",
        "selected_scheduler_canonical_replay_candidate_instance_key",
        "selected_scheduler_selected_candidate_instance_key",
    )
    values = {
        field_name: str(row.get(field_name) or "").strip()
        for field_name in identity_fields
    }
    present = {value for value in values.values() if value}
    if not present:
        return
    if len(present) != 1 or any(not value for value in values.values()):
        record_relational_failure(
            surface,
            "scorecard_selected_identity_alias_mismatch",
            line=line_number,
            window=window,
            values=values,
        )
        return
    selected_key = next(iter(present))
    if selected_key not in set(hard_pool.get("keys") or []):
        record_relational_failure(
            surface,
            "scorecard_selected_identity_outside_hard_pool",
            line=line_number,
            window=window,
            candidate_instance_key=selected_key,
        )
    if selected_key in surface.scorecard_selected:
        record_relational_failure(
            surface,
            "scorecard_selected_identity_duplicate",
            line=line_number,
            candidate_instance_key=selected_key,
        )
        return
    surface.scorecard_selected[selected_key] = {
        "decision_window_id": window,
        "candidate_instance_key": selected_key,
    }


def update_order_event(
    surface: ArmSurface,
    row: Mapping[str, Any],
    *,
    line_number: int,
) -> None:
    candidate_key = identity_key(row)
    order_id = str(row.get("simulated_order_id") or "").strip()
    stage = str(row.get("order_event_stage") or "").strip()
    if not candidate_key:
        record_relational_failure(
            surface,
            "order_candidate_instance_identity_missing",
            line=line_number,
        )
    if not order_id:
        record_relational_failure(
            surface,
            "order_id_missing",
            line=line_number,
            candidate_instance_key=candidate_key,
        )
        return
    if stage != "accepted_pending" and not stage.startswith("terminal_"):
        record_relational_failure(
            surface,
            "order_event_stage_invalid",
            line=line_number,
            order_id=order_id,
            stage=stage,
        )
    surface.order_events_by_id.setdefault(order_id, []).append(
        {
            "line": line_number,
            "candidate_instance_key": candidate_key,
            "decision_window_id": str(row.get("decision_window_id") or "").strip(),
            "stage": stage,
            "order_status": str(row.get("order_status") or "").strip(),
            "fill_status": str(row.get("fill_status") or "").strip(),
        }
    )


def update_missed(surface: ArmSurface, row: Mapping[str, Any]) -> None:
    missed = surface.missed
    missed["rows"] += 1
    key = identity_key(row)
    if not key:
        raise MatrixAuditError(f"missed_identity_missing:{surface.arm_id}")
    if key in surface.missed_by_key:
        raise MatrixAuditError(f"missed_identity_duplicate:{surface.arm_id}:{key}")
    status = str(row.get("missed_opportunity_r_scoreability_status") or "")
    diagnostic = bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or status == "diagnostic_opportunity_r_scoreable"
    )
    headline = row.get("missed_opportunity_headline_r_scoreable") is True
    diagnostic_net_r: float | None = None
    if diagnostic:
        diagnostic_net_r = numeric(
            row.get("opportunity_net_proxy_r"),
            label="missed.opportunity_net_proxy_r",
        )
        missed["diagnostic_scoreable_rows"] += 1
        if diagnostic_net_r > 0:
            missed["diagnostic_positive_rows"] += 1
            missed["diagnostic_positive_net_r"] += diagnostic_net_r
        elif diagnostic_net_r < 0:
            missed["diagnostic_negative_rows"] += 1
            missed["diagnostic_negative_net_r"] += diagnostic_net_r
        else:
            missed["diagnostic_flat_rows"] += 1
    if headline:
        missed["headline_scoreable_rows"] += 1
    surface.missed_by_key[key] = {
        "diagnostic_scoreable": diagnostic,
        "headline_scoreable": headline,
        "diagnostic_net_r": diagnostic_net_r,
        "scoreability_status": status,
    }


def update_trade(surface: ArmSurface, row: Mapping[str, Any]) -> None:
    key = identity_key(row)
    if not key:
        raise MatrixAuditError(f"trade_identity_missing:{surface.arm_id}")
    if key in surface.trades:
        raise MatrixAuditError(f"trade_identity_duplicate:{surface.arm_id}:{key}")
    risk_cash = numeric(row.get("risk_cash"), label=f"{surface.arm_id}.trade.risk_cash")
    risk_pct = numeric(row.get("risk_pct"), label=f"{surface.arm_id}.trade.risk_pct")
    if risk_cash <= 0 or risk_pct <= 0:
        raise MatrixAuditError(f"trade_risk_not_positive:{surface.arm_id}:{key}")
    raw_net = row.get("net_proxy_r")
    scoreable = raw_net is not None
    order_id = str(row.get("simulated_order_id") or "").strip()
    trade_id = str(row.get("simulated_trade_id") or "").strip()
    if not order_id:
        record_relational_failure(
            surface,
            "trade_order_id_missing",
            candidate_instance_key=key,
        )
    if not trade_id or trade_id in surface.trade_ids:
        record_relational_failure(
            surface,
            "trade_id_missing_or_duplicate",
            candidate_instance_key=key,
            simulated_trade_id=trade_id,
        )
    elif trade_id:
        surface.trade_ids.add(trade_id)
    trade = {
        "candidate_instance_key": key,
        "simulated_order_id": order_id,
        "simulated_trade_id": trade_id,
        "risk_cash": risk_cash,
        "risk_pct": risk_pct,
        "scoreable": scoreable,
        "net_r": None,
        "gross_r": None,
        "cost_r": numeric(
            row.get("expected_cost_r"), label=f"{surface.arm_id}.trade.expected_cost_r"
        ),
        "pnl_cash": None,
        "event_time": str(
            row.get("exit_time_utc")
            or row.get("close_time_utc")
            or row.get("terminal_time_utc")
            or ""
        ),
    }
    if scoreable:
        trade["net_r"] = numeric(raw_net, label=f"{surface.arm_id}.trade.net_proxy_r")
        trade["gross_r"] = numeric(
            row.get("gross_r"), label=f"{surface.arm_id}.trade.gross_r"
        )
        trade["pnl_cash"] = numeric(
            row.get("pnl_cash"), label=f"{surface.arm_id}.trade.pnl_cash"
        )
        expected_cash = risk_cash * float(trade["net_r"])
        if abs(float(trade["pnl_cash"]) - expected_cash) > 1e-6:
            record_relational_failure(
                surface,
                "scoreable_trade_cash_r_identity_mismatch",
                candidate_instance_key=key,
                expected_pnl_cash=expected_cash,
                actual_pnl_cash=trade["pnl_cash"],
            )
        if not trade["event_time"]:
            raise MatrixAuditError(f"scoreable_trade_event_time_missing:{surface.arm_id}:{key}")
    else:
        non_null = [
            field_name
            for field_name in ("net_proxy_r", "gross_r", "pnl_cash")
            if row.get(field_name) is not None
        ]
        if non_null:
            record_relational_failure(
                surface,
                "unscoreable_trade_economic_imputation_forbidden",
                candidate_instance_key=key,
                fields=non_null,
            )
    surface.trades[key] = trade


def scan_jsonl_into_surface(
    path: Path,
    *,
    kind: str,
    surface: ArmSurface,
    expected_binding: Mapping[str, Any],
) -> dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            digest.update(raw)
            byte_count += len(raw)
            if not raw.strip():
                continue
            row_count += 1
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise MatrixAuditError(f"invalid_jsonl:{path}:{line_number}:{exc}") from exc
            if not isinstance(row, dict):
                raise MatrixAuditError(f"jsonl_row_not_object:{path}:{line_number}")
            validate_flat_binding(
                surface,
                row,
                kind=kind,
                line_number=line_number,
                expected=expected_binding,
            )
            if kind in {"missed", "order", "trade"}:
                key = identity_key(row)
                if not key:
                    raise MatrixAuditError(
                        f"candidate_identity_missing:{surface.arm_id}:{kind}:{line_number}"
                    )
                surface.candidate_keys.add(key)
            if kind == "scorecard":
                window, pool = hard_pool_from_scorecard(row)
                if window in surface.hard_pools:
                    raise MatrixAuditError(
                        f"scorecard_decision_window_duplicate:{surface.arm_id}:{window}"
                    )
                surface.decision_windows.add(window)
                surface.hard_pools[window] = pool
                update_scorecard_identity(
                    surface,
                    row,
                    window=window,
                    hard_pool=pool,
                    line_number=line_number,
                )
            elif kind == "order":
                update_order_event(
                    surface,
                    row,
                    line_number=line_number,
                )
            elif kind == "trade":
                update_trade(surface, row)
            elif kind == "missed":
                update_missed(surface, row)
    return {
        "path": str(path),
        "bytes": byte_count,
        "rows": row_count,
        "sha256": digest.hexdigest(),
    }


def summary_profile_stats(summary: Mapping[str, Any], profile: str) -> Mapping[str, Any]:
    rows = summary.get("split_profile_stats")
    if not isinstance(rows, list):
        return {}
    matched = [row for row in rows if isinstance(row, Mapping) and row.get("profile") == profile]
    return matched[0] if len(matched) == 1 else {}


def add_failure(failures: list[dict[str, Any]], code: str, **detail: Any) -> None:
    failures.append({"code": code, **detail})


def validate_summary_binding(
    surface: ArmSurface,
    frozen: FrozenBindings,
    failures: list[dict[str, Any]],
) -> None:
    arm_id = surface.arm_id
    summary = surface.summary
    prefix = surface.prefix
    selection, sizing, selection_mode, sizing_mode = arm_factors(arm_id)
    expected = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "output_prefix": prefix,
        "date_start": "2026-06-04",
        "date_end": "2026-06-04",
        "configured_symbol_count": frozen.expected_symbol_count,
        "active_replay_symbol_count": frozen.expected_symbol_count,
        "candidate_rows": frozen.expected_candidate_count,
        "scorecard_rows": frozen.expected_scorecard_count,
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "packet_sidecar_ledger_omitted": True,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            add_failure(
                failures,
                "summary_field_mismatch",
                arm_id=arm_id,
                field=key,
                expected=value,
                actual=summary.get(key),
            )
    send_attempts = summary.get("order_send_attempts")
    expected_send_attempts = {frozen.expected_profile: 0}
    if send_attempts not in (0, expected_send_attempts):
        add_failure(
            failures,
            "summary_field_mismatch",
            arm_id=arm_id,
            field="order_send_attempts",
            expected=expected_send_attempts,
            actual=send_attempts,
        )
    if summary.get("profiles") != [frozen.expected_profile]:
        add_failure(failures, "profile_binding_mismatch", arm_id=arm_id)
    contract_binding = summary.get("b7_5_contract_binding")
    contract_binding = contract_binding if isinstance(contract_binding, Mapping) else {}
    binding_expectations = {
        "valid": True,
        "expected_source_plan_digest_sha256": frozen.source_plan_sha256,
        "actual_source_plan_digests_sha256": [frozen.source_plan_sha256],
        "expected_shared_execution_contract_digest_sha256": frozen.shared_execution_contracts[arm_id],
        "actual_shared_execution_contract_digest_sha256": frozen.shared_execution_contracts[arm_id],
    }
    for key, value in binding_expectations.items():
        if contract_binding.get(key) != value:
            add_failure(
                failures,
                "source_or_shared_contract_binding_mismatch",
                arm_id=arm_id,
                field=key,
                expected=value,
                actual=contract_binding.get(key),
            )
    arm_binding = summary.get("b7_5_selection_sizing_factorial_arm_binding")
    arm_binding = arm_binding if isinstance(arm_binding, Mapping) else {}
    arm_expectations = {
        "valid": True,
        "arm_id": arm_id,
        "arm_fingerprint_sha256": frozen.arm_fingerprints[arm_id],
        "binding_payload_sha256": frozen.binding_payloads[arm_id],
        "common_execution_input_digest_sha256": frozen.common_execution_input_sha256,
        "decision_contract_sha256": frozen.contract_self_hash_sha256,
        "protocol_economics_digest_sha256": frozen.protocol_economics_digest_sha256,
        "neutral_selection_seed_sha256": frozen.neutral_selection_seed_sha256,
        "selection_factor": selection,
        "sizing_factor": sizing,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "denominator": dict(frozen.denominator),
        "matched_risk": dict(frozen.matched_risk),
        "uses_outcome_fields": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
    }
    for key, value in arm_expectations.items():
        if arm_binding.get(key) != value:
            add_failure(
                failures,
                "arm_binding_mismatch",
                arm_id=arm_id,
                field=key,
                expected=value,
                actual=arm_binding.get(key),
            )
    shared = summary.get("shared_execution_contract")
    shared = shared if isinstance(shared, Mapping) else {}
    declared_shared_digest = shared.get("shared_execution_contract_digest_sha256")
    shared_payload = copy.deepcopy(dict(shared))
    for wrapper_field in (
        "valid",
        "status",
        "shared_execution_contract_digest_sha256",
    ):
        shared_payload.pop(wrapper_field, None)
    recomputed_shared_digest = stable_sha256(shared_payload)
    code_authority = shared.get("code_authority")
    code_authority = code_authority if isinstance(code_authority, list) else []
    verifier_entries = [
        entry
        for entry in code_authority
        if isinstance(entry, Mapping)
        and entry.get("path") == VERIFIER_CODE_AUTHORITY_PATH
    ]
    verifier_authority_valid = bool(
        len(verifier_entries) == 1
        and verifier_entries[0].get("sha256") == FROZEN_VERIFIER_SHA256
    )
    if not verifier_authority_valid:
        add_failure(
            failures,
            "shared_execution_contract_verifier_authority_invalid",
            arm_id=arm_id,
            expected_path=VERIFIER_CODE_AUTHORITY_PATH,
            expected_sha256=FROZEN_VERIFIER_SHA256,
            actual_entries=verifier_entries,
        )
    if (
        shared.get("valid") is not True
        or shared.get("status") != "shared_execution_contract_bound"
        or declared_shared_digest != frozen.shared_execution_contracts[arm_id]
        or recomputed_shared_digest != declared_shared_digest
    ):
        add_failure(
            failures,
            "shared_execution_contract_invalid",
            arm_id=arm_id,
            declared_sha256=declared_shared_digest,
            recomputed_sha256=recomputed_shared_digest,
            frozen_sha256=frozen.shared_execution_contracts[arm_id],
        )


def validate_arm_relational_identity(
    surface: ArmSurface,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_to_order_id: dict[str, str] = {}
    order_event_identities: list[str] = []
    for order_id, events in surface.order_events_by_id.items():
        candidate_keys = {
            str(event.get("candidate_instance_key") or "") for event in events
        }
        windows = {str(event.get("decision_window_id") or "") for event in events}
        accepted = [event for event in events if event.get("stage") == "accepted_pending"]
        terminal = [
            event
            for event in events
            if str(event.get("stage") or "").startswith("terminal_")
        ]
        if "" in candidate_keys or len(candidate_keys) != 1:
            record_relational_failure(
                surface,
                "order_id_candidate_identity_not_singleton",
                order_id=order_id,
                candidate_instance_keys=sorted(candidate_keys),
            )
            continue
        candidate_key = next(iter(candidate_keys))
        if "" in windows or len(windows) != 1:
            record_relational_failure(
                surface,
                "order_id_decision_window_not_singleton",
                order_id=order_id,
                decision_windows=sorted(windows),
            )
        if len(events) != 2 or len(accepted) != 1 or len(terminal) != 1:
            record_relational_failure(
                surface,
                "order_accepted_terminal_event_cardinality_invalid",
                order_id=order_id,
                event_count=len(events),
                accepted_count=len(accepted),
                terminal_count=len(terminal),
            )
            continue
        if candidate_key in candidate_to_order_id:
            record_relational_failure(
                surface,
                "candidate_has_multiple_order_instances",
                candidate_instance_key=candidate_key,
                order_ids=[candidate_to_order_id[candidate_key], order_id],
            )
            continue
        accepted_event = accepted[0]
        terminal_event = terminal[0]
        if accepted_event.get("order_status") not in {
            "pending_accepted",
            "accepted_not_filled_pending_until_expiry",
            "pending_accepted_entry_fill_terminal_r_unscoreable",
        }:
            record_relational_failure(
                surface,
                "accepted_order_status_invalid",
                order_id=order_id,
                order_status=accepted_event.get("order_status"),
            )
        terminal_stage = str(terminal_event.get("stage") or "")
        filled = terminal_stage == "terminal_filled"
        if filled and (
            terminal_event.get("order_status") != "filled"
            or terminal_event.get("fill_status") != "filled"
        ):
            record_relational_failure(
                surface,
                "terminal_filled_status_invalid",
                order_id=order_id,
            )
        if terminal_stage == "terminal_expired_unfilled" and (
            terminal_event.get("order_status") != "expired_unfilled"
        ):
            record_relational_failure(
                surface,
                "terminal_expired_status_invalid",
                order_id=order_id,
            )
        candidate_to_order_id[candidate_key] = order_id
        stages = [str(event.get("stage") or "") for event in events]
        for stage in stages:
            order_event_identities.append(f"{candidate_key}@@{stage}")
        surface.order_instances[candidate_key] = {
            "candidate_instance_key": candidate_key,
            "decision_window_id": next(iter(windows)) if len(windows) == 1 else "",
            "simulated_order_id": order_id,
            "stages": stages,
            "terminal_stage": terminal_stage,
            "filled": filled,
        }

    selected_keys = set(surface.scorecard_selected)
    order_keys = set(surface.order_instances)
    if selected_keys != order_keys:
        record_relational_failure(
            surface,
            "scorecard_selected_order_instance_partition_mismatch",
            selected_without_order=sorted(selected_keys - order_keys),
            order_without_selected=sorted(order_keys - selected_keys),
        )
    for candidate_key in sorted(selected_keys & order_keys):
        if (
            surface.scorecard_selected[candidate_key]["decision_window_id"]
            != surface.order_instances[candidate_key]["decision_window_id"]
        ):
            record_relational_failure(
                surface,
                "scorecard_order_decision_window_mismatch",
                candidate_instance_key=candidate_key,
            )

    trade_keys = set(surface.trades)
    filled_order_keys = {
        key for key, order in surface.order_instances.items() if order["filled"]
    }
    if trade_keys != filled_order_keys:
        record_relational_failure(
            surface,
            "filled_order_trade_partition_mismatch",
            filled_without_trade=sorted(filled_order_keys - trade_keys),
            trade_without_filled_order=sorted(trade_keys - filled_order_keys),
        )
    for candidate_key in sorted(trade_keys & filled_order_keys):
        if (
            surface.trades[candidate_key]["simulated_order_id"]
            != surface.order_instances[candidate_key]["simulated_order_id"]
        ):
            record_relational_failure(
                surface,
                "trade_order_id_transfer_mismatch",
                candidate_instance_key=candidate_key,
                trade_order_id=surface.trades[candidate_key]["simulated_order_id"],
                lifecycle_order_id=surface.order_instances[candidate_key][
                    "simulated_order_id"
                ],
            )

    if surface.relational_identity_failures:
        add_failure(
            failures,
            "candidate_scorecard_order_fill_identity_invalid",
            arm_id=surface.arm_id,
            count=len(surface.relational_identity_failures),
            samples=surface.relational_identity_failures[:16],
        )
    order_instance_bindings = [
        copy.deepcopy(surface.order_instances[key])
        for key in sorted(surface.order_instances)
    ]
    return {
        "valid": not surface.relational_identity_failures,
        "scorecard_selected_instance_count": len(selected_keys),
        "order_instance_count": len(order_keys),
        "order_event_count": sum(len(events) for events in surface.order_events_by_id.values()),
        "filled_order_instance_count": len(filled_order_keys),
        "trade_instance_count": len(trade_keys),
        "scorecard_selected_instance_digest_sha256": stable_sha256(sorted(selected_keys)),
        "order_instance_digest_sha256": stable_sha256(sorted(order_keys)),
        "order_event_identity_digest_sha256": stable_sha256(
            sorted(order_event_identities)
        ),
        "filled_order_instance_digest_sha256": stable_sha256(
            sorted(filled_order_keys)
        ),
        "trade_instance_digest_sha256": stable_sha256(sorted(trade_keys)),
        "scorecard_selected_bindings": [
            copy.deepcopy(surface.scorecard_selected[key])
            for key in sorted(surface.scorecard_selected)
        ],
        "order_instance_bindings": order_instance_bindings,
        "order_instance_binding_digest_sha256": stable_sha256(
            order_instance_bindings
        ),
        "failure_count": len(surface.relational_identity_failures),
        "failures": surface.relational_identity_failures[:16],
    }


def load_arm_surface(
    arm_id: str,
    paths: dict[str, Path],
    config: AnalyzerConfig,
    failures: list[dict[str, Any]],
    partial_bundle: tuple[dict[str, Any], dict[str, Any]],
) -> ArmSurface:
    summary, summary_record = read_json_object(paths["summary"])
    partial, partial_record = partial_bundle
    surface = ArmSurface(
        arm_id=arm_id,
        prefix=config.prefixes[arm_id],
        summary=summary,
        paths=paths,
        artifacts={"summary": summary_record, "partial_summary": partial_record},
        missed={
            "rows": 0,
            "diagnostic_scoreable_rows": 0,
            "diagnostic_positive_rows": 0,
            "diagnostic_positive_net_r": 0.0,
            "diagnostic_negative_rows": 0,
            "diagnostic_negative_net_r": 0.0,
            "diagnostic_flat_rows": 0,
            "headline_scoreable_rows": 0,
        },
    )
    record_authority_violations(
        surface,
        summary,
        artifact="summary",
        location="root",
    )
    record_authority_violations(
        surface,
        partial,
        artifact="partial_summary",
        location="root",
    )
    validate_summary_binding(surface, config.frozen, failures)
    expected_binding = expected_flat_binding(arm_id, config.frozen)
    for kind in JSONL_KINDS:
        surface.artifacts[kind] = scan_jsonl_into_surface(
            paths[kind],
            kind=kind,
            surface=surface,
            expected_binding=expected_binding,
        )
    surface.relational_identity_audit = validate_arm_relational_identity(
        surface,
        failures,
    )
    declared = summary.get("ledger_write_row_counts")
    declared = declared if isinstance(declared, Mapping) else {}
    for kind in JSONL_KINDS:
        actual = surface.artifacts[kind]["rows"]
        if declared.get(kind) != actual:
            add_failure(
                failures,
                "serialized_row_count_mismatch",
                arm_id=arm_id,
                artifact=kind,
                declared=declared.get(kind),
                actual=actual,
            )
    if surface.binding_mismatch_count:
        add_failure(
            failures,
            "flat_factorial_binding_mismatch",
            arm_id=arm_id,
            count=surface.binding_mismatch_count,
        )
    if surface.authority_violation_count:
        add_failure(
            failures,
            "recursive_authority_violation",
            arm_id=arm_id,
            count=surface.authority_violation_count,
        )
    if len(surface.candidate_keys) != config.frozen.expected_candidate_count:
        add_failure(
            failures,
            "candidate_relational_count_mismatch",
            arm_id=arm_id,
            expected=config.frozen.expected_candidate_count,
            actual=len(surface.candidate_keys),
        )
    if len(surface.decision_windows) != config.frozen.expected_scorecard_count:
        add_failure(
            failures,
            "scorecard_decision_window_count_mismatch",
            arm_id=arm_id,
            expected=config.frozen.expected_scorecard_count,
            actual=len(surface.decision_windows),
        )
    stats = summary_profile_stats(summary, config.frozen.expected_profile)
    if integer(stats.get("decision_rows", -1), label=f"{arm_id}.decision_rows") != config.frozen.expected_decision_count:
        add_failure(failures, "decision_count_mismatch", arm_id=arm_id)
    return surface


def validate_namespace_stability(
    paths_by_arm: Mapping[str, Mapping[str, Path]],
    initial: Mapping[str, Mapping[str, Mapping[str, Any]]],
    surfaces: Mapping[str, ArmSurface],
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    stable_count = 0
    total_count = 0
    for arm_id in ARM_ORDER:
        surface = surfaces[arm_id]
        for kind, path in paths_by_arm[arm_id].items():
            total_count += 1
            final = file_fingerprint(path)
            opened = surface.artifacts[kind]
            before = initial[arm_id][kind]
            stable = bool(
                before["sha256"] == opened["sha256"] == final["sha256"]
                and before["bytes"] == opened["bytes"] == final["bytes"]
            )
            opened.update(
                {
                    "namespace_initial_sha256": before["sha256"],
                    "namespace_post_audit_sha256": final["sha256"],
                    "stable_pre_parse_post": stable,
                }
            )
            if stable:
                stable_count += 1
            else:
                add_failure(
                    failures,
                    "namespace_artifact_mutated_during_audit",
                    arm_id=arm_id,
                    artifact=kind,
                    initial_sha256=before["sha256"],
                    opened_sha256=opened["sha256"],
                    final_sha256=final["sha256"],
                )
    return {
        "stable_artifact_count": stable_count,
        "total_artifact_count": total_count,
        "all_artifacts_stable": stable_count == total_count,
        "method": "sha256_before_parse_equals_opened_parse_equals_sha256_after_all_verifier_scans",
    }


def trade_economics(surface: ArmSurface, frozen: FrozenBindings) -> dict[str, Any]:
    rows = list(surface.trades.values())
    scoreable = [row for row in rows if row["scoreable"]]
    total_risk_cash = sum(row["risk_cash"] for row in rows)
    scoreable_risk_cash = sum(row["risk_cash"] for row in scoreable)
    if total_risk_cash <= 0:
        raise MatrixAuditError(f"accepted_risk_cash_not_positive:{surface.arm_id}")
    cash = sum(float(row["pnl_cash"]) for row in scoreable)
    net_r = sum(float(row["net_r"]) for row in scoreable)
    gross_r = sum(float(row["gross_r"]) for row in scoreable)
    cost_r = sum(row["cost_r"] for row in rows)
    risk_pct = sum(row["risk_pct"] for row in rows)
    ordered = sorted(scoreable, key=lambda row: str(row["event_time"]))
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for row in ordered:
        cumulative += float(row["pnl_cash"])
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, peak - cumulative)
    tail = min((float(row["net_r"]) for row in scoreable), default=0.0)
    wins = sum(float(row["net_r"]) > 0 for row in scoreable)
    losses = sum(float(row["net_r"]) < 0 for row in scoreable)
    flats = len(scoreable) - wins - losses
    stats = summary_profile_stats(surface.summary, frozen.expected_profile)
    return {
        "physical_trade_rows": len(rows),
        "scoreable_trade_rows": len(scoreable),
        "unscoreable_trade_rows": len(rows) - len(scoreable),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "scoreable_net_cash": round(cash, 8),
        "accepted_risk_cash": round(total_risk_cash, 8),
        "scoreable_accepted_risk_cash": round(scoreable_risk_cash, 8),
        "scoreable_risk_coverage": round(scoreable_risk_cash / total_risk_cash, 12),
        "cash_per_accepted_risk_dollar": round(cash / total_risk_cash, 12),
        "fixed_denominator_portfolio_r": round(
            cash / float(frozen.denominator["fixed_denominator_portfolio_r_cash"]), 8
        ),
        "physical_net_r": round(net_r, 8),
        "physical_gross_r": round(gross_r, 8),
        "execution_cost_r": round(cost_r, 8),
        "aggregate_risk_pct": round(risk_pct, 8),
        "max_drawdown_cash": round(max_drawdown, 8),
        "tail_loss_net_r": round(tail, 8),
        "headline_net_r": numeric(
            stats.get("headline_net_r"), label=f"{surface.arm_id}.headline_net_r"
        ),
        "stress": copy.deepcopy(stats.get("physical_stress")),
    }


def expected_physical_stress(surface: ArmSurface) -> dict[str, Any]:
    returns = [
        float(trade["net_r"])
        for trade in surface.trades.values()
        if trade["scoreable"]
    ]
    guarded: list[dict[str, Any]] = []
    for stress_id, extra_cost in STRESS_SCENARIOS.items():
        stressed = [value - extra_cost for value in returns]
        guarded.append(
            {
                "stress_id": stress_id,
                "net_r": round(sum(stressed), 8),
                "min_trade_r": round(min(stressed), 8) if stressed else None,
                "loss_count": sum(value < 0.0 for value in stressed),
            }
        )
    return {
        "trade_count": len(returns),
        "raw_net_r": round(sum(returns), 8),
        "guarded_stress_rows": guarded if returns else [],
    }


def validate_physical_stress(
    surface: ArmSurface,
    frozen: FrozenBindings,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    stats = summary_profile_stats(surface.summary, frozen.expected_profile)
    raw = stats.get("physical_stress")
    expected = expected_physical_stress(surface)
    issues: list[dict[str, Any]] = []
    if not isinstance(raw, Mapping):
        issues.append({"reason": "physical_stress_missing_or_not_mapping"})
        raw = {}
    if set(raw) != {"trade_count", "raw_net_r", "guarded_stress_rows"}:
        issues.append(
            {
                "reason": "physical_stress_root_schema_mismatch",
                "fields": sorted(str(key) for key in raw),
            }
        )
    try:
        trade_count = integer(
            raw.get("trade_count"),
            label=f"{surface.arm_id}.physical_stress.trade_count",
        )
    except MatrixAuditError:
        trade_count = None
        issues.append({"reason": "physical_stress_trade_count_invalid"})
    raw_net_r = optional_numeric(raw.get("raw_net_r"))
    if raw_net_r is None:
        issues.append({"reason": "physical_stress_raw_net_r_nonfinite_or_missing"})
    if trade_count != expected["trade_count"]:
        issues.append(
            {
                "reason": "physical_stress_trade_count_ledger_mismatch",
                "expected": expected["trade_count"],
                "actual": trade_count,
            }
        )
    if raw_net_r is None or not close(raw_net_r, expected["raw_net_r"], 1e-8):
        issues.append(
            {
                "reason": "physical_stress_raw_net_r_ledger_mismatch",
                "expected": expected["raw_net_r"],
                "actual": raw.get("raw_net_r"),
            }
        )
    rows = raw.get("guarded_stress_rows")
    rows = rows if isinstance(rows, list) else []
    if not isinstance(raw.get("guarded_stress_rows"), list):
        issues.append({"reason": "physical_stress_guarded_rows_not_list"})
    actual_by_id: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(
                {"reason": "physical_stress_guarded_row_not_mapping", "index": index}
            )
            continue
        stress_id = str(row.get("stress_id") or "")
        if stress_id in actual_by_id:
            issues.append(
                {
                    "reason": "physical_stress_guarded_id_duplicate",
                    "stress_id": stress_id,
                }
            )
            continue
        actual_by_id[stress_id] = row
    expected_by_id = {
        row["stress_id"]: row for row in expected["guarded_stress_rows"]
    }
    if set(actual_by_id) != set(expected_by_id):
        issues.append(
            {
                "reason": "physical_stress_guarded_id_partition_mismatch",
                "expected": sorted(expected_by_id),
                "actual": sorted(actual_by_id),
            }
        )
    for stress_id in sorted(set(actual_by_id) & set(expected_by_id)):
        actual = actual_by_id[stress_id]
        expected_row = expected_by_id[stress_id]
        if set(actual) != {"stress_id", "net_r", "min_trade_r", "loss_count"}:
            issues.append(
                {
                    "reason": "physical_stress_guarded_row_schema_mismatch",
                    "stress_id": stress_id,
                    "fields": sorted(str(key) for key in actual),
                }
            )
        net_r = optional_numeric(actual.get("net_r"))
        min_trade_r = optional_numeric(actual.get("min_trade_r"))
        try:
            loss_count = integer(
                actual.get("loss_count"),
                label=f"{surface.arm_id}.{stress_id}.loss_count",
            )
        except MatrixAuditError:
            loss_count = None
        if (
            net_r is None
            or min_trade_r is None
            or loss_count is None
            or not close(net_r, expected_row["net_r"], 1e-8)
            or not close(min_trade_r, expected_row["min_trade_r"], 1e-8)
            or loss_count != expected_row["loss_count"]
        ):
            issues.append(
                {
                    "reason": "physical_stress_guarded_row_ledger_mismatch",
                    "stress_id": stress_id,
                    "expected": expected_row,
                    "actual": dict(actual),
                }
            )
    if issues:
        add_failure(
            failures,
            "physical_stress_contract_invalid",
            arm_id=surface.arm_id,
            count=len(issues),
            samples=issues[:16],
        )
    return {
        "valid": not issues,
        "schema": "gtos.b7_5.physical_stress_ledger_reconciliation.v1",
        "serialized": copy.deepcopy(dict(raw)),
        "ledger_recomputed": expected,
        "failure_count": len(issues),
        "failures": issues[:16],
    }


def validate_economics_parity(
    surface: ArmSurface,
    frozen: FrozenBindings,
    failures: list[dict[str, Any]],
) -> None:
    economics = trade_economics(surface, frozen)
    surface.economics = economics
    surface.economics["stress"] = validate_physical_stress(
        surface,
        frozen,
        failures,
    )
    stats = summary_profile_stats(surface.summary, frozen.expected_profile)
    checks = {
        "physical_risk_cash": economics["accepted_risk_cash"],
        "physical_risk_pct": economics["aggregate_risk_pct"],
        "physical_scoreable_trade_rows": economics["scoreable_trade_rows"],
        "physical_unscoreable_trade_rows": economics["unscoreable_trade_rows"],
        "physical_cash_pnl": economics["scoreable_net_cash"],
        "physical_net_r": economics["physical_net_r"],
        "physical_gross_r": economics["physical_gross_r"],
        "physical_expected_cost_r": economics["execution_cost_r"],
    }
    for field_name, expected in checks.items():
        actual = stats.get(field_name)
        equal = actual == expected if isinstance(expected, int) else close(actual, expected, 1e-6)
        if not equal:
            add_failure(
                failures,
                "serialized_trade_summary_parity_mismatch",
                arm_id=surface.arm_id,
                field=field_name,
                expected=expected,
                actual=actual,
            )
    if surface.arm_id.endswith("R0"):
        for key, trade in surface.trades.items():
            if not close(trade["risk_cash"], frozen.denominator["fixed_account_risk_unit_cash"]):
                add_failure(failures, "r0_trade_risk_cash_not_fixed", arm_id=surface.arm_id, key=key)
            if not close(trade["risk_pct"], frozen.denominator["fixed_account_risk_unit_pct"]):
                add_failure(failures, "r0_trade_risk_pct_not_fixed", arm_id=surface.arm_id, key=key)
        accepted_seen: set[str] = set()
        with surface.paths["order"].open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                order_status = str(row.get("order_status") or "")
                accepted_pending = bool(
                    row.get("order_event_stage") == "accepted_pending"
                    or order_status.startswith("pending_accepted")
                )
                if not accepted_pending:
                    continue
                order_id = str(row.get("simulated_order_id") or "")
                if not order_id or order_id in accepted_seen:
                    add_failure(failures, "r0_accepted_order_identity_invalid", arm_id=surface.arm_id, line=line_number)
                    continue
                accepted_seen.add(order_id)
                for field_name, target in (
                    ("risk_cash", frozen.denominator["fixed_account_risk_unit_cash"]),
                    ("risk_pct", frozen.denominator["fixed_account_risk_unit_pct"]),
                    ("reserved_risk_pct", frozen.denominator["fixed_account_risk_unit_pct"]),
                ):
                    if not close(row.get(field_name), target):
                        add_failure(
                            failures,
                            "r0_accepted_order_risk_not_fixed",
                            arm_id=surface.arm_id,
                            line=line_number,
                            field=field_name,
                        )


def optional_numeric(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def executable_risk_atomicity_row_is_bound(
    row: Mapping[str, Any],
    ledger_name: str,
) -> bool:
    if ledger_name == "trade":
        return True
    order_status = str(row.get("order_status") or "").strip().lower()
    fill_status = str(row.get("fill_status") or "").strip().lower()
    return bool(
        row.get("simulated_trade_id")
        or order_status
        in {
            "filled",
            "pending_accepted",
            "accepted_not_filled_pending_until_expiry",
        }
        or fill_status.startswith("filled")
    )


def canonical_risk_atom_hash_matches(atom: Mapping[str, Any]) -> bool:
    atom_hash = str(atom.get("atom_hash_sha256") or "").strip().lower()
    if len(atom_hash) != 64 or any(value not in "009abcdef" for value in atom_hash):
        return False
    payload = dict(atom)
    payload.pop("atom_hash_sha256", None)
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256_bytes(material.encode("utf-8")) == atom_hash


def expected_factorial_binding_payload(
    arm_id: str,
    frozen: FrozenBindings,
) -> dict[str, Any]:
    selection, sizing, selection_mode, sizing_mode = arm_factors(arm_id)
    return {
        "arm_fingerprint_sha256": frozen.arm_fingerprints[arm_id],
        "arm_id": arm_id,
        "broker_mutation_enabled": False,
        "common_execution_input_digest_sha256": frozen.common_execution_input_sha256,
        "decision_contract_sha256": frozen.contract_self_hash_sha256,
        "denominator": dict(frozen.denominator),
        "final_selection_claim": False,
        "fixed_account_risk_unit_pct": frozen.denominator[
            "fixed_account_risk_unit_pct"
        ],
        "live_broker_authority": False,
        "matched_risk": dict(frozen.matched_risk),
        "neutral_selection_seed_sha256": frozen.neutral_selection_seed_sha256,
        "protocol_economics": {
            "denominator": dict(frozen.denominator),
            "matched_risk": dict(frozen.matched_risk),
        },
        "protocol_economics_digest_sha256": (
            frozen.protocol_economics_digest_sha256
        ),
        "selection_factor": selection,
        "selection_mode": selection_mode,
        "sizing_factor": sizing,
        "sizing_mode": sizing_mode,
        "uses_outcome_fields": False,
    }


def validate_r0_fixed_dollar_atomicity_row(
    surface: ArmSurface,
    row: Mapping[str, Any],
    *,
    ledger_name: str,
    row_number: int,
    frozen: FrozenBindings,
) -> dict[str, Any]:
    """Independently prove one execution row uses the sealed R0 dollar atom."""

    failures: list[str] = []

    def fail(code: str) -> None:
        if code not in failures:
            failures.append(code)

    expected_pct = float(frozen.denominator["fixed_account_risk_unit_pct"])
    expected_cash = float(frozen.denominator["fixed_account_risk_unit_cash"])
    expected_equity = float(frozen.denominator["initial_equity_cash"])
    if not surface.arm_id.endswith("R0"):
        fail("r1_fixed_dollar_reconciliation_forbidden")
    flat_expectations = {
        "b7_5_selection_sizing_factorial_arm_id": surface.arm_id,
        "b7_5_selection_sizing_factorial_sizing_factor": "R0",
        "b7_5_selection_sizing_factorial_sizing_mode": "fixed_equal_account_risk",
        "b7_5_selection_sizing_factorial_initial_equity_cash": expected_equity,
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_pct": expected_pct,
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_cash": expected_cash,
    }
    for field_name, expected in flat_expectations.items():
        actual = row.get(field_name)
        if isinstance(expected, float):
            if not close(actual, expected, 1e-9):
                fail(f"flat_{field_name}_mismatch")
        elif actual != expected:
            fail(f"flat_{field_name}_mismatch")

    risk_authority = row.get("risk_authority")
    if not isinstance(risk_authority, Mapping):
        fail("risk_authority_missing")
        risk_authority = {}
    binding = risk_authority.get(R0_FACTORIAL_BINDING_FIELD)
    if not isinstance(binding, Mapping):
        fail("r0_factorial_binding_missing")
        binding = {}
    selection, _sizing, selection_mode, _sizing_mode = arm_factors(surface.arm_id)
    expected_binding_payload = expected_factorial_binding_payload(
        surface.arm_id,
        frozen,
    )
    binding_expectations = {
        "requested": True,
        "enabled": True,
        "valid": True,
        "status": "factorial_arm_bound_broker_live_closed",
        "failures": [],
        "arm_id": surface.arm_id,
        "arm_fingerprint_sha256": frozen.arm_fingerprints[surface.arm_id],
        "binding_payload_sha256": frozen.binding_payloads[surface.arm_id],
        "common_execution_input_digest_sha256": frozen.common_execution_input_sha256,
        "decision_contract_sha256": frozen.contract_self_hash_sha256,
        "protocol_economics_digest_sha256": frozen.protocol_economics_digest_sha256,
        "neutral_selection_seed_sha256": frozen.neutral_selection_seed_sha256,
        "selection_factor": selection,
        "selection_mode": selection_mode,
        "sizing_factor": "R0",
        "sizing_mode": "fixed_equal_account_risk",
        "denominator": dict(frozen.denominator),
        "matched_risk": dict(frozen.matched_risk),
        "protocol_economics": {
            "denominator": dict(frozen.denominator),
            "matched_risk": dict(frozen.matched_risk),
        },
        "uses_outcome_fields": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }
    for field_name, expected in binding_expectations.items():
        if binding.get(field_name) != expected:
            fail(f"r0_factorial_binding_{field_name}_mismatch")
    for field_name, expected in (
        ("fixed_account_risk_unit_pct", expected_pct),
        ("fixed_account_risk_unit_cash", expected_cash),
        ("initial_equity_cash", expected_equity),
    ):
        if not close(binding.get(field_name), expected, 1e-9):
            fail(f"r0_factorial_binding_{field_name}_mismatch")
    if binding.get("denominator") != dict(frozen.denominator):
        fail("r0_factorial_binding_denominator_mismatch")
    binding_payload = binding.get("binding_payload")
    if not isinstance(binding_payload, Mapping):
        fail("r0_factorial_binding_payload_missing")
        binding_payload = {}
    if dict(binding_payload) != expected_binding_payload:
        fail("r0_factorial_binding_payload_mismatch")
    computed_binding_payload_sha256 = stable_sha256(binding_payload)
    if computed_binding_payload_sha256 != frozen.binding_payloads[surface.arm_id]:
        fail("r0_factorial_binding_payload_hash_invalid")
    if binding.get("binding_payload_sha256") != computed_binding_payload_sha256:
        fail("r0_factorial_binding_payload_declared_hash_mismatch")

    detail = risk_authority.get(R0_FIXED_CASH_DETAIL_FIELD)
    if not isinstance(detail, Mapping):
        fail("r0_fixed_cash_detail_missing")
        detail = {}
    outer_detail = row.get(R0_FIXED_CASH_DETAIL_FIELD)
    if outer_detail is not None:
        if not isinstance(outer_detail, Mapping) or dict(outer_detail) != dict(detail):
            fail("outer_nested_r0_fixed_cash_detail_mismatch")
    if detail.get("cash_basis_source") != R0_FIXED_CASH_BASIS_SOURCE:
        fail("r0_fixed_cash_basis_source_mismatch")
    if detail.get("fixed_equal_account_risk_cash_applied") is not True:
        fail("r0_fixed_cash_applied_not_true")

    detail_values = {
        "risk_cash": (expected_cash, 1e-8),
        "fixed_account_risk_unit_pct": (expected_pct, 1e-12),
        "fixed_account_risk_unit_cash": (expected_cash, 1e-8),
        "fixed_account_risk_initial_equity_cash": (expected_equity, 1e-8),
    }
    for field_name, (expected, tolerance) in detail_values.items():
        if not close(detail.get(field_name), expected, tolerance):
            fail(f"r0_fixed_cash_detail_{field_name}_mismatch")

    unit_pct = optional_numeric(detail.get("fixed_account_risk_unit_pct"))
    unit_cash = optional_numeric(detail.get("fixed_account_risk_unit_cash"))
    initial_equity = optional_numeric(
        detail.get("fixed_account_risk_initial_equity_cash")
    )
    if (
        unit_pct is None
        or unit_cash is None
        or initial_equity is None
        or abs(initial_equity * unit_pct / 100.0 - unit_cash) > 1e-8
    ):
        fail("r0_frozen_basis_arithmetic_mismatch")

    ignored_balance = optional_numeric(
        detail.get("fixed_account_risk_current_balance_ignored")
    )
    if ignored_balance is None or ignored_balance <= 0.0:
        fail("r0_current_balance_ignored_missing_or_invalid")
    current_balance = None
    for field_name in ("risk_sizing_balance_before", "balance_before", "equity_before"):
        current_balance = optional_numeric(risk_authority.get(field_name))
        if current_balance is not None:
            break
    if current_balance is None:
        current_balance = optional_numeric(row.get("balance_before"))
    if current_balance is None or current_balance <= 0.0:
        fail("r0_current_balance_source_missing_or_invalid")
    elif ignored_balance is None or abs(current_balance - ignored_balance) > 1e-8:
        fail("r0_current_balance_ignored_provenance_mismatch")

    atom = risk_authority.get("canonical_executable_final_risk_atom")
    if not isinstance(atom, Mapping):
        fail("canonical_final_risk_atom_missing")
        atom = {}
    outer_atom = row.get("canonical_executable_final_risk_atom")
    if outer_atom is not None:
        if not isinstance(outer_atom, Mapping) or dict(outer_atom) != dict(atom):
            fail("outer_nested_canonical_final_risk_atom_mismatch")
    if atom.get("schema_version") != CANONICAL_EXECUTABLE_FINAL_RISK_ATOM_SCHEMA:
        fail("canonical_final_risk_atom_schema_mismatch")
    if not canonical_risk_atom_hash_matches(atom):
        fail("canonical_final_risk_atom_hash_invalid")
    if atom.get("uses_outcome_fields") is not False:
        fail("canonical_final_risk_atom_outcome_boundary_invalid")
    if atom.get("live_broker_authority") is not False:
        fail("canonical_final_risk_atom_live_authority_invalid")
    if atom.get("broker_mutation_enabled") is not False:
        fail("canonical_final_risk_atom_broker_mutation_boundary_invalid")
    if atom.get("b7_5_selection_sizing_factorial_fixed_unit_enforced") is not True:
        fail("canonical_final_risk_atom_fixed_unit_not_enforced")
    if atom.get("b7_5_selection_sizing_factorial_fixed_unit_unavailable") is not False:
        fail("canonical_final_risk_atom_fixed_unit_unavailable")
    atom_risk = optional_numeric(atom.get("final_risk_pct"))
    if atom_risk is None or abs(atom_risk - expected_pct) > 1e-12:
        fail("canonical_final_risk_atom_pct_mismatch")
    if str(atom.get("candidate_id") or "") != str(row.get("candidate_id") or ""):
        fail("canonical_final_risk_atom_candidate_mismatch")
    if (
        not str(atom.get("decision_time_utc") or "")
        or str(atom.get("decision_time_utc") or "")
        != str(row.get("decision_time_utc") or "")
    ):
        fail("canonical_final_risk_atom_decision_time_mismatch")

    for field_name in RISK_ALIASES:
        if not close(row.get(field_name), expected_pct, 1e-12):
            fail(f"outer_{field_name}_mismatch")
    for field_name in NESTED_RISK_ALIASES:
        if not close(risk_authority.get(field_name), expected_pct, 1e-12):
            fail(f"nested_{field_name}_mismatch")
    for field_name, value in (
        ("outer_risk_cash", row.get("risk_cash")),
        ("nested_risk_cash", risk_authority.get("risk_cash")),
        ("nested_order_risk_cash", risk_authority.get("order_risk_cash")),
    ):
        if not close(value, expected_cash, 1e-8):
            fail(f"{field_name}_mismatch")

    generic_balance_cash = (
        current_balance * expected_pct / 100.0
        if current_balance is not None
        else None
    )
    generic_false_positive = bool(
        generic_balance_cash is not None
        and abs(expected_cash - generic_balance_cash) > 1e-6
    )
    return {
        "ledger": ledger_name,
        "row_number": row_number,
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc"),
        "simulated_order_id": row.get("simulated_order_id"),
        "simulated_trade_id": row.get("simulated_trade_id"),
        "symbol": row.get("symbol"),
        "risk_pct": expected_pct,
        "atom_risk_pct": atom_risk,
        "reference_risk_pct": atom_risk,
        "risk_sizing_balance_before": current_balance,
        "generic_evolving_balance_expected_risk_cash": generic_balance_cash,
        "sealed_frozen_basis_risk_cash": expected_cash,
        "generic_false_positive": generic_false_positive,
        "proof": {
            "flat_factorial_binding": {
                key: row.get(key) for key in sorted(flat_expectations)
            },
            "nested_binding_payload_sha256": binding.get(
                "binding_payload_sha256"
            ),
            "computed_nested_binding_payload_sha256": (
                computed_binding_payload_sha256
            ),
            "canonical_atom_hash_sha256": atom.get("atom_hash_sha256"),
            "outer_risk_aliases": {
                key: row.get(key) for key in RISK_ALIASES
            },
            "nested_risk_aliases": {
                key: risk_authority.get(key) for key in NESTED_RISK_ALIASES
            },
            "risk_cash_aliases": {
                "outer_risk_cash": row.get("risk_cash"),
                "nested_risk_cash": risk_authority.get("risk_cash"),
                "nested_order_risk_cash": risk_authority.get("order_risk_cash"),
            },
            "fixed_cash_detail": dict(detail),
        },
        "valid": not failures,
        "failures": failures,
    }


def exact_counter_projection(
    value: Any,
    *,
    label: str,
    failures: list[dict[str, Any]],
) -> dict[str, int]:
    if not isinstance(value, Mapping):
        failures.append({"code": f"{label}_not_mapping"})
        return {}
    projection: dict[str, int] = {}
    for raw_key, raw_count in value.items():
        key = str(raw_key)
        try:
            projection[key] = integer(raw_count, label=f"{label}.{key}")
        except MatrixAuditError:
            failures.append(
                {
                    "code": f"{label}_count_not_exact_integer",
                    "key": key,
                    "value": repr(raw_count),
                }
            )
    return projection


def reconcile_r0_fixed_dollar_atomicity(
    surface: ArmSurface,
    raw_scan: Mapping[str, Any],
    frozen: FrozenBindings,
) -> dict[str, Any]:
    """Clear only the generic evolving-balance false positive for sealed R0."""

    failures: list[dict[str, Any]] = []
    raw_bad_counts = exact_counter_projection(
        raw_scan.get("bad_counts"),
        label="raw_bad_counts",
        failures=failures,
    )
    raw_bad_counts = {
        key: count for key, count in raw_bad_counts.items() if count != 0
    }
    paired_keys = {
        f"{ledger}:{reason}"
        for ledger in ("order", "trade")
        for reason in (
            EXECUTABLE_RISK_ATOMICITY_AGGREGATE_REASON,
            EXECUTABLE_RISK_ATOMICITY_FIXED_BASIS_REASON,
        )
    }
    paired_present = bool(set(raw_bad_counts) & paired_keys)
    if not surface.arm_id.endswith("R0"):
        if paired_present:
            failures.append({"code": "r1_fixed_dollar_reconciliation_forbidden"})
        return {
            "schema": "gtos.b7_5.r0_fixed_dollar_atomicity_reconciliation.v1",
            "status": (
                "failed_r1_reconciliation_forbidden"
                if paired_present
                else "not_applicable_r1_raw_scan_unchanged"
            ),
            "applicable": False,
            "valid": not failures,
            "arm_id": surface.arm_id,
            "raw_bad_counts": raw_bad_counts,
            "reconciled_bad_counts": {},
            "unreconciled_bad_counts": raw_bad_counts,
            "effective_bad_counts": raw_bad_counts,
            "cleared_bad_count_keys": [],
            "failure_count": len(failures),
            "failures": failures,
        }
    if not paired_present:
        return {
            "schema": "gtos.b7_5.r0_fixed_dollar_atomicity_reconciliation.v1",
            "status": "not_needed_no_paired_fixed_basis_bad_counts",
            "applicable": False,
            "valid": not failures,
            "arm_id": surface.arm_id,
            "raw_bad_counts": raw_bad_counts,
            "reconciled_bad_counts": {},
            "unreconciled_bad_counts": raw_bad_counts,
            "effective_bad_counts": raw_bad_counts,
            "cleared_bad_count_keys": [],
            "failure_count": len(failures),
            "failures": failures,
        }

    unexpected_bad_keys = sorted(set(raw_bad_counts) - paired_keys)
    if unexpected_bad_keys:
        failures.append(
            {
                "code": "unexpected_atomicity_bad_count_keys",
                "keys": unexpected_bad_keys,
            }
        )
    row_counts = exact_counter_projection(
        raw_scan.get("row_counts"),
        label="raw_row_counts",
        failures=failures,
    )
    evidence_rows: list[dict[str, Any]] = []
    expected_row_counts: dict[str, int] = {}
    expected_bad_counts: dict[str, int] = {}
    expected_samples: list[dict[str, Any]] = []
    for ledger_name in ("order", "trade"):
        total_rows = 0
        execution_rows = 0
        false_positive_rows = 0
        path = surface.paths[ledger_name]
        with path.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                total_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise MatrixAuditError(
                        f"r0_atomicity_invalid_jsonl:{path}:{row_number}:{exc}"
                    ) from exc
                if not isinstance(row, Mapping):
                    raise MatrixAuditError(
                        f"r0_atomicity_row_not_mapping:{path}:{row_number}"
                    )
                if not executable_risk_atomicity_row_is_bound(row, ledger_name):
                    continue
                execution_rows += 1
                evidence = validate_r0_fixed_dollar_atomicity_row(
                    surface,
                    row,
                    ledger_name=ledger_name,
                    row_number=row_number,
                    frozen=frozen,
                )
                evidence_rows.append(evidence)
                if not evidence["valid"]:
                    failures.append(
                        {
                            "code": "r0_execution_row_frozen_basis_invalid",
                            "ledger": ledger_name,
                            "row_number": row_number,
                            "reasons": evidence["failures"],
                        }
                    )
                if evidence["generic_false_positive"]:
                    false_positive_rows += 1
                    expected_samples.append(evidence)
        expected_row_counts[f"{ledger_name}_rows"] = total_rows
        expected_row_counts[f"{ledger_name}_execution_bound_rows"] = execution_rows
        expected_row_counts[f"{ledger_name}_atomic_rows_valid"] = (
            execution_rows - false_positive_rows
        )
        if false_positive_rows:
            expected_bad_counts[
                f"{ledger_name}:{EXECUTABLE_RISK_ATOMICITY_AGGREGATE_REASON}"
            ] = false_positive_rows
            expected_bad_counts[
                f"{ledger_name}:{EXECUTABLE_RISK_ATOMICITY_FIXED_BASIS_REASON}"
            ] = false_positive_rows

    normalized_row_counts = {
        key: count for key, count in row_counts.items() if count != 0
    }
    normalized_expected_row_counts = {
        key: count for key, count in expected_row_counts.items() if count != 0
    }
    if normalized_row_counts != normalized_expected_row_counts:
        failures.append(
            {
                "code": "atomicity_row_counts_mismatch",
                "expected": normalized_expected_row_counts,
                "actual": normalized_row_counts,
            }
        )
    if raw_bad_counts != expected_bad_counts:
        failures.append(
            {
                "code": "paired_atomicity_bad_counts_mismatch",
                "expected": expected_bad_counts,
                "actual": raw_bad_counts,
            }
        )

    raw_samples_value = raw_scan.get("sample_bad")
    raw_samples = raw_samples_value if isinstance(raw_samples_value, list) else []
    expected_samples = expected_samples[:16]
    sample_diagnostic_mismatches: list[dict[str, Any]] = []
    for index, expected in enumerate(expected_samples):
        if index >= len(raw_samples):
            break
        actual = raw_samples[index]
        if not isinstance(actual, Mapping):
            sample_diagnostic_mismatches.append(
                {"code": "atomicity_sample_not_mapping", "index": index}
            )
            continue
        sample_mismatches: list[str] = []
        for field_name in (
            "ledger",
            "row_number",
            "candidate_id",
            "decision_time_utc",
            "simulated_order_id",
            "simulated_trade_id",
            "symbol",
        ):
            if actual.get(field_name) != expected.get(field_name):
                sample_mismatches.append(field_name)
        for field_name in (
            "risk_pct",
            "atom_risk_pct",
            "reference_risk_pct",
            "risk_sizing_balance_before",
        ):
            if not close(actual.get(field_name), expected.get(field_name), 1e-8):
                sample_mismatches.append(field_name)
        if actual.get("reasons") != [EXECUTABLE_RISK_ATOMICITY_FIXED_BASIS_REASON]:
            sample_mismatches.append("reasons")
        if sample_mismatches:
            sample_diagnostic_mismatches.append(
                {
                    "code": "atomicity_reported_sample_mismatch",
                    "index": index,
                    "fields": sample_mismatches,
                }
            )

    valid = not failures
    unreconciled_bad_counts = (
        {key: count for key, count in raw_bad_counts.items() if key not in paired_keys}
        if valid
        else raw_bad_counts
    )
    reconciled_bad_counts = (
        {key: count for key, count in raw_bad_counts.items() if key in paired_keys}
        if valid
        else {}
    )
    cleared = sorted(reconciled_bad_counts)
    return {
        "schema": "gtos.b7_5.r0_fixed_dollar_atomicity_reconciliation.v1",
        "status": (
            "reconciled_exact_frozen_initial_equity_basis"
            if valid
            else "failed_closed_frozen_basis_not_proven"
        ),
        "applicable": True,
        "valid": valid,
        "arm_id": surface.arm_id,
        "cash_basis_source": R0_FIXED_CASH_BASIS_SOURCE,
        "initial_equity_cash": frozen.denominator["initial_equity_cash"],
        "fixed_account_risk_unit_pct": frozen.denominator[
            "fixed_account_risk_unit_pct"
        ],
        "fixed_account_risk_unit_cash": frozen.denominator[
            "fixed_account_risk_unit_cash"
        ],
        "execution_bound_row_count": len(evidence_rows),
        "generic_false_positive_row_count": sum(
            bool(row["generic_false_positive"]) for row in evidence_rows
        ),
        "execution_row_complete_proof_sha256": stable_sha256(evidence_rows),
        "raw_bad_counts": raw_bad_counts,
        "expected_bad_counts": expected_bad_counts,
        "reconciled_bad_counts": reconciled_bad_counts,
        "unreconciled_bad_counts": unreconciled_bad_counts,
        "effective_bad_counts": unreconciled_bad_counts,
        "cleared_bad_count_keys": cleared,
        "raw_scan_output_preserved": True,
        "sample_bad_diagnostic_only": {
            "acceptance_dependency": False,
            "raw_value_is_list": isinstance(raw_samples_value, list),
            "reported_count": len(raw_samples),
            "independent_expected_prefix_count": len(expected_samples),
            "mismatches": sample_diagnostic_mismatches,
        },
        "failure_count": len(failures),
        "failures": failures,
    }


def run_verifier_scans(
    surface: ArmSurface,
    verifier: Any,
    failures: list[dict[str, Any]],
    frozen: FrozenBindings,
) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = surface.paths
    candidate_source = verifier.ExactRelationalCandidateSource(
        (paths["missed"], paths["order"], paths["trade"])
    )
    invocations = {
        "factorial_risk_lifecycle_summary": lambda: verifier.scan_broad_factorial_risk_lifecycle_summary(surface.summary),
        "physical_trade_summary_parity": lambda: verifier.scan_broad_physical_trade_summary_parity(surface.summary, paths["trade"]),
        "order_trade_cost_authority": lambda: verifier.scan_broad_order_trade_cost_authority({"order": paths["order"], "oracle": paths["oracle"], "trade": paths["trade"]}),
        "selected_quality_source": lambda: verifier.scan_broad_selected_quality_source_contract({"scorecard": paths["scorecard"], "order": paths["order"], "trade": paths["trade"]}),
        "missed_opportunity_semantics": lambda: verifier.scan_broad_missed_opportunity_semantics(paths["missed"]),
        "entry_fill_terminal_lifecycle": lambda: verifier.scan_broad_entry_fill_terminal_r_lifecycle_contract({"order": paths["order"], "trade": paths["trade"]}),
        "candidate_instance_identity": lambda: verifier.scan_cross_ledger_candidate_instance_identity({"candidate": candidate_source, "scorecard": paths["scorecard"], "order": paths["order"], "trade": paths["trade"], "missed": paths["missed"]}),
        "selector_materialization_r_identity": lambda: verifier.scan_broad_selector_materialization_and_r_identity({"scorecard": paths["scorecard"], "order": paths["order"], "trade": paths["trade"], "missed": paths["missed"]}),
        "stop_hazard_cap_execution_authority": lambda: verifier.scan_broad_stop_hazard_cap_execution_authority({"order": paths["order"], "trade": paths["trade"]}),
        "executable_risk_fillability_atomicity": lambda: verifier.scan_broad_executable_risk_and_fillability_atomicity({"order": paths["order"], "trade": paths["trade"]}),
        "selected_policy_replay_authority": lambda: verifier.scan_broad_selected_policy_replay_authority({"order": paths["order"], "trade": paths["trade"]}),
        "order_trade_path_provenance": lambda: verifier.scan_broad_order_trade_path_provenance({"order": paths["order"], "trade": paths["trade"]}),
    }
    scans: dict[str, Any] = {}
    for name, invocation in invocations.items():
        try:
            result = invocation()
        except Exception as exc:  # verifier exceptions are audit failures, not skips
            result = {"bad_counts": {"scan_exception": 1}, "exception": f"{type(exc).__name__}:{exc}"}
        scan_record = copy.deepcopy(result)
        bad_counts = result.get("bad_counts") if isinstance(result, Mapping) else None
        if name == EXECUTABLE_RISK_ATOMICITY_SCAN and isinstance(result, Mapping):
            reconciliation = reconcile_r0_fixed_dollar_atomicity(
                surface,
                result,
                frozen,
            )
            if isinstance(scan_record, dict):
                # The verifier's raw fields, including bad_counts and sample_bad,
                # remain byte-for-byte equivalent values.  Only this separately
                # named effective view is used for the matrix gate.
                scan_record["r0_fixed_dollar_basis_reconciliation"] = reconciliation
                scan_record["effective_bad_counts"] = copy.deepcopy(
                    reconciliation["effective_bad_counts"]
                )
            bad_counts = reconciliation["effective_bad_counts"]
            if not reconciliation["valid"]:
                add_failure(
                    failures,
                    "r0_fixed_dollar_atomicity_reconciliation_failed",
                    arm_id=surface.arm_id,
                    status=reconciliation["status"],
                    reconciliation_failures=reconciliation["failures"],
                )
        scans[name] = scan_record
        failing_bad_counts: dict[str, Any] = {}
        if not isinstance(bad_counts, Mapping):
            failing_bad_counts["missing_bad_counts"] = 1
        else:
            for raw_key, raw_value in bad_counts.items():
                key = str(raw_key)
                try:
                    count = integer(raw_value, label=f"verifier.{name}.{key}")
                except MatrixAuditError:
                    failing_bad_counts[key] = f"invalid_non_integer:{raw_value!r}"
                    continue
                if count != 0:
                    failing_bad_counts[key] = count
        if failing_bad_counts:
            add_failure(
                failures,
                "verifier_scan_failed",
                arm_id=surface.arm_id,
                scan=name,
                bad_counts=failing_bad_counts,
            )
    summary_issues: dict[str, Any] = {}
    for function_name in SUMMARY_ISSUE_FUNCTIONS:
        try:
            issues = list(getattr(verifier, function_name)(surface.summary))
        except Exception as exc:
            issues = [f"summary_issue_scan_exception:{type(exc).__name__}:{exc}"]
        summary_issues[function_name] = issues
        if issues:
            add_failure(
                failures,
                "summary_contract_failed",
                arm_id=surface.arm_id,
                contract=function_name,
                issues=issues,
            )
    return scans, summary_issues


def validate_lifecycle(
    surface: ArmSurface,
    frozen: FrozenBindings,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    audit = surface.summary.get("b7_5_selection_sizing_factorial_risk_lifecycle")
    audit = audit if isinstance(audit, Mapping) else {}
    required = {
        "required": True,
        "valid": True,
        "status": "factorial_risk_lifecycle_contract_valid",
        "arm_id": surface.arm_id,
        "matched_risk": dict(frozen.matched_risk),
        "failure_count": 0,
        "failures": [],
        "uses_outcome_fields_for_selection_or_sizing": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
    }
    for field_name, expected in required.items():
        if audit.get(field_name) != expected:
            add_failure(
                failures,
                "factorial_lifecycle_field_mismatch",
                arm_id=surface.arm_id,
                field=field_name,
                expected=expected,
                actual=audit.get(field_name),
            )
    accepted = integer(audit.get("accepted_order_count", -1), label=f"{surface.arm_id}.accepted")
    terminal = integer(audit.get("close_or_expiry_event_count", -1), label=f"{surface.arm_id}.terminal")
    released = integer(audit.get("close_or_expiry_release_count", -1), label=f"{surface.arm_id}.released")
    transfers = integer(audit.get("pending_to_open_transfer_count", -1), label=f"{surface.arm_id}.transfers")
    if (
        accepted < 0
        or accepted != len(surface.order_instances)
        or terminal != accepted
        or released != accepted
        or transfers != len(surface.trades)
    ):
        add_failure(
            failures,
            "factorial_lifecycle_count_mismatch",
            arm_id=surface.arm_id,
            accepted=accepted,
            terminal=terminal,
            released=released,
            transfers=transfers,
            order_instances=len(surface.order_instances),
            physical_trades=len(surface.trades),
        )
    peak_caps = (
        ("peak_daily_accepted_risk_pct", "daily_accepted_risk_pct_cap"),
        ("peak_open_plus_pending_risk_pct", "peak_open_plus_pending_risk_pct_cap"),
        ("peak_opening_window_risk_pct", "opening_window_risk_pct_cap"),
    )
    for peak_field, cap_field in peak_caps:
        peak = numeric(audit.get(peak_field), label=f"{surface.arm_id}.{peak_field}")
        cap = numeric(frozen.matched_risk[cap_field], label=cap_field)
        if peak < -CAP_TOLERANCE or peak > cap + CAP_TOLERANCE:
            add_failure(failures, "factorial_risk_cap_breached", arm_id=surface.arm_id, field=peak_field, peak=peak, cap=cap)
    cluster_cap = numeric(frozen.matched_risk["cluster_risk_pct_cap"], label="cluster_cap")
    clusters = audit.get("peak_cluster_risk_pct")
    if accepted > 0 and not isinstance(clusters, Mapping):
        add_failure(failures, "factorial_cluster_peaks_missing", arm_id=surface.arm_id)
    elif isinstance(clusters, Mapping):
        for cluster, raw in clusters.items():
            peak = numeric(raw, label=f"{surface.arm_id}.cluster.{cluster}")
            if peak < -CAP_TOLERANCE or peak > cluster_cap + CAP_TOLERANCE:
                add_failure(failures, "factorial_cluster_cap_breached", arm_id=surface.arm_id, cluster=cluster, peak=peak)
    for field_name in (
        "terminal_daily_accepted_risk_pct",
        "terminal_pending_risk_pct",
        "terminal_open_risk_pct",
    ):
        value = numeric(audit.get(field_name), label=f"{surface.arm_id}.{field_name}")
        if abs(value) > CAP_TOLERANCE:
            add_failure(failures, "factorial_terminal_risk_not_zero", arm_id=surface.arm_id, field=field_name, value=value)
    return {
        "accepted_order_count": accepted,
        "pending_to_open_transfer_count": transfers,
        "close_or_expiry_event_count": terminal,
        "close_or_expiry_release_count": released,
        "peak_daily_accepted_risk_pct": audit.get("peak_daily_accepted_risk_pct"),
        "peak_open_plus_pending_risk_pct": audit.get("peak_open_plus_pending_risk_pct"),
        "peak_opening_window_risk_pct": audit.get("peak_opening_window_risk_pct"),
        "peak_cluster_risk_pct": copy.deepcopy(audit.get("peak_cluster_risk_pct")),
        "terminal_daily_accepted_risk_pct": audit.get("terminal_daily_accepted_risk_pct"),
        "terminal_pending_risk_pct": audit.get("terminal_pending_risk_pct"),
        "terminal_open_risk_pct": audit.get("terminal_open_risk_pct"),
    }


def validate_protocol_and_contract(
    config: AnalyzerConfig,
    failures: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol, protocol_record = read_json_object(config.protocol_path)
    contract, contract_record = read_json_object(config.contract_path)
    frozen = config.frozen
    if protocol_record["sha256"] != frozen.protocol_file_sha256:
        add_failure(failures, "protocol_file_hash_mismatch")
    if contract_record["sha256"] != frozen.contract_file_sha256:
        add_failure(failures, "decision_contract_file_hash_mismatch")
    for artifact, payload in (("protocol", protocol), ("decision_contract", contract)):
        violations = list(recursive_authority_violations(payload))
        if violations:
            add_failure(
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
    actual_self_hash = stable_sha256(contract_for_hash)
    if actual_self_hash != frozen.contract_self_hash_sha256:
        add_failure(failures, "decision_contract_self_hash_mismatch", actual=actual_self_hash)
    expected_contract = {
        "schema": "gtos.b7_5.selection_sizing_decision_contract.v2",
        "status": "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID",
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
    }
    for key, value in expected_contract.items():
        if contract.get(key) != value:
            add_failure(failures, "decision_contract_boundary_mismatch", field=key)
    if contract.get("denominator") != dict(frozen.denominator) or contract.get("matched_risk") != dict(frozen.matched_risk):
        add_failure(failures, "decision_contract_economics_mismatch")
    attribution = contract.get("factorial_contract", {}).get("attribution") if isinstance(contract.get("factorial_contract"), Mapping) else None
    expected_attribution = {
        "selection": "S1R0-S0R0",
        "sizing": "S0R1-S0R0",
        "interaction": "S1R1-S1R0-S0R1+S0R0",
        "total_incumbent_value": "S1R1-S0R0",
    }
    if attribution != expected_attribution:
        add_failure(failures, "factorial_attribution_contract_mismatch")
    return protocol, contract, {"protocol": protocol_record, "decision_contract": contract_record}


def contrast(values: Mapping[str, float]) -> dict[str, float]:
    return {
        "selection": round(values["S1R0"] - values["S0R0"], 12),
        "sizing": round(values["S0R1"] - values["S0R0"], 12),
        "interaction": round(
            values["S1R1"] - values["S1R0"] - values["S0R1"] + values["S0R0"],
            12,
        ),
        "total_incumbent_value": round(values["S1R1"] - values["S0R0"], 12),
    }


def trade_rollup(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    scoreable = [row for row in materialized if row.get("scoreable")]
    return {
        "count": len(materialized),
        "scoreable_count": len(scoreable),
        "positive_count": sum(float(row["net_r"]) > 0 for row in scoreable),
        "negative_count": sum(float(row["net_r"]) < 0 for row in scoreable),
        "net_r": round(sum(float(row["net_r"]) for row in scoreable), 8),
        "pnl_cash": round(sum(float(row["pnl_cash"]) for row in scoreable), 8),
        "risk_cash": round(sum(float(row["risk_cash"]) for row in materialized), 8),
    }


def missed_transition_rollup(
    missed_surface: ArmSurface,
    source_trade_surface: ArmSurface,
    candidate_keys: Iterable[str],
) -> dict[str, Any]:
    keys = list(candidate_keys)
    missing = [key for key in keys if key not in missed_surface.missed_by_key]
    rows = [
        missed_surface.missed_by_key[key]
        for key in keys
        if key in missed_surface.missed_by_key
    ]
    scoreable = [row for row in rows if row["diagnostic_scoreable"]]
    values = [float(row["diagnostic_net_r"]) for row in scoreable]
    comparable_count = 0
    exact_r_match_count = 0
    r_mismatch_keys: list[str] = []
    non_comparable: list[dict[str, str]] = []
    for key in keys:
        missed = missed_surface.missed_by_key.get(key)
        trade = source_trade_surface.trades.get(key)
        if missed is None:
            continue
        if trade is None:
            non_comparable.append(
                {"candidate_instance_key": key, "reason": "source_order_not_filled"}
            )
            continue
        if not trade["scoreable"]:
            non_comparable.append(
                {"candidate_instance_key": key, "reason": "source_trade_unscoreable"}
            )
            continue
        if not missed["diagnostic_scoreable"]:
            non_comparable.append(
                {
                    "candidate_instance_key": key,
                    "reason": "missed_diagnostic_r_unscoreable",
                }
            )
            continue
        comparable_count += 1
        if close(trade["net_r"], missed["diagnostic_net_r"], 1e-8):
            exact_r_match_count += 1
        else:
            r_mismatch_keys.append(key)
    return {
        "expected_count": len(keys),
        "reconciled_count": len(rows),
        "missing_keys": missing,
        "diagnostic_scoreable_count": len(scoreable),
        "diagnostic_positive_count": sum(value > 0 for value in values),
        "diagnostic_negative_count": sum(value < 0 for value in values),
        "diagnostic_net_r": round(sum(values), 8),
        "comparable_trade_missed_r_count": comparable_count,
        "exact_trade_missed_r_match_count": exact_r_match_count,
        "trade_missed_r_mismatch_keys": r_mismatch_keys,
        "non_comparable_count": len(non_comparable),
        "non_comparable_transitions": non_comparable,
    }


def order_rollup(surface: ArmSurface, keys: Iterable[str]) -> dict[str, Any]:
    instances = [surface.order_instances[key] for key in keys]
    terminal_stage_counts: dict[str, int] = {}
    for order in instances:
        stage = str(order["terminal_stage"])
        terminal_stage_counts[stage] = terminal_stage_counts.get(stage, 0) + 1
    return {
        "order_instance_count": len(instances),
        "order_event_count": sum(len(order["stages"]) for order in instances),
        "filled_order_instance_count": sum(bool(order["filled"]) for order in instances),
        "terminal_stage_counts": terminal_stage_counts,
        "order_id_bindings": [
            {
                "candidate_instance_key": order["candidate_instance_key"],
                "simulated_order_id": order["simulated_order_id"],
                "terminal_stage": order["terminal_stage"],
            }
            for order in instances
        ],
    }


def transition(
    baseline: ArmSurface,
    candidate: ArmSurface,
) -> dict[str, Any]:
    baseline_keys = set(baseline.trades)
    candidate_keys = set(candidate.trades)
    added_keys = sorted(candidate_keys - baseline_keys)
    removed_keys = sorted(baseline_keys - candidate_keys)
    common_keys = sorted(baseline_keys & candidate_keys)
    baseline_order_keys = set(baseline.order_instances)
    candidate_order_keys = set(candidate.order_instances)
    added_order_keys = sorted(candidate_order_keys - baseline_order_keys)
    removed_order_keys = sorted(baseline_order_keys - candidate_order_keys)
    common_order_keys = sorted(baseline_order_keys & candidate_order_keys)
    baseline_event_keys = {
        f"{key}@@{stage}"
        for key, order in baseline.order_instances.items()
        for stage in order["stages"]
    }
    candidate_event_keys = {
        f"{key}@@{stage}"
        for key, order in candidate.order_instances.items()
        for stage in order["stages"]
    }
    stage_transitions = [
        {
            "candidate_instance_key": key,
            "baseline_stages": baseline.order_instances[key]["stages"],
            "candidate_stages": candidate.order_instances[key]["stages"],
            "baseline_terminal_stage": baseline.order_instances[key]["terminal_stage"],
            "candidate_terminal_stage": candidate.order_instances[key]["terminal_stage"],
        }
        for key in common_order_keys
        if (
            baseline.order_instances[key]["stages"]
            != candidate.order_instances[key]["stages"]
            or baseline.order_instances[key]["terminal_stage"]
            != candidate.order_instances[key]["terminal_stage"]
        )
    ]
    added = trade_rollup(candidate.trades[key] for key in added_keys)
    removed = trade_rollup(baseline.trades[key] for key in removed_keys)
    common_cash_delta = round(
        sum(float(candidate.trades[key]["pnl_cash"] or 0.0) for key in common_keys)
        - sum(float(baseline.trades[key]["pnl_cash"] or 0.0) for key in common_keys),
        8,
    )
    q_delta = round(
        candidate.economics["cash_per_accepted_risk_dollar"]
        - baseline.economics["cash_per_accepted_risk_dollar"],
        12,
    )
    suppression_only = bool(
        q_delta > FLOAT_TOLERANCE
        and (removed_keys or removed_order_keys)
        and not added_keys
        and not added_order_keys
        and abs(common_cash_delta) <= FLOAT_TOLERANCE
    )
    removed_to_missed = missed_transition_rollup(candidate, baseline, removed_keys)
    added_from_missed = missed_transition_rollup(baseline, candidate, added_keys)
    removed_order_to_missed = missed_transition_rollup(
        candidate,
        baseline,
        removed_order_keys,
    )
    added_order_from_missed = missed_transition_rollup(
        baseline,
        candidate,
        added_order_keys,
    )
    suppression_present = bool(removed_keys or removed_order_keys)
    return {
        "baseline_arm": baseline.arm_id,
        "candidate_arm": candidate.arm_id,
        "candidate_universe_equal": baseline.candidate_keys == candidate.candidate_keys,
        "scorecard_windows_equal": baseline.decision_windows == candidate.decision_windows,
        "added_trade_keys": added_keys,
        "removed_trade_keys": removed_keys,
        "common_trade_count": len(common_keys),
        "added_trades": added,
        "removed_trades": removed,
        "removed_trade_to_candidate_missed_reconciliation": removed_to_missed,
        "added_trade_from_baseline_missed_reconciliation": added_from_missed,
        "added_order_instance_keys": added_order_keys,
        "removed_order_instance_keys": removed_order_keys,
        "common_order_instance_count": len(common_order_keys),
        "added_order_instances": order_rollup(candidate, added_order_keys),
        "removed_order_instances": order_rollup(baseline, removed_order_keys),
        "added_order_event_keys": sorted(candidate_event_keys - baseline_event_keys),
        "removed_order_event_keys": sorted(baseline_event_keys - candidate_event_keys),
        "common_order_event_count": len(baseline_event_keys & candidate_event_keys),
        "common_order_stage_transitions": stage_transitions,
        "common_order_id_transitions": [
            {
                "candidate_instance_key": key,
                "baseline_simulated_order_id": baseline.order_instances[key][
                    "simulated_order_id"
                ],
                "candidate_simulated_order_id": candidate.order_instances[key][
                    "simulated_order_id"
                ],
            }
            for key in common_order_keys
        ],
        "removed_order_to_candidate_missed_reconciliation": removed_order_to_missed,
        "added_order_from_baseline_missed_reconciliation": added_order_from_missed,
        "common_trade_scoreable_cash_delta": common_cash_delta,
        "primary_q_delta": q_delta,
        "missed_diagnostic_positive_rows_delta": candidate.missed["diagnostic_positive_rows"] - baseline.missed["diagnostic_positive_rows"],
        "missed_diagnostic_positive_net_r_delta": round(candidate.missed["diagnostic_positive_net_r"] - baseline.missed["diagnostic_positive_net_r"], 8),
        "missed_diagnostic_negative_rows_delta": candidate.missed["diagnostic_negative_rows"] - baseline.missed["diagnostic_negative_rows"],
        "missed_diagnostic_negative_net_r_delta": round(candidate.missed["diagnostic_negative_net_r"] - baseline.missed["diagnostic_negative_net_r"], 8),
        "trade_suppression_present": bool(removed_keys),
        "order_suppression_present": bool(removed_order_keys),
        "execution_suppression_present": suppression_present,
        "positive_delta_with_execution_suppression": bool(
            q_delta > FLOAT_TOLERANCE and suppression_present
        ),
        "positive_by_suppression_only": suppression_only,
        "positive_delta_with_non_comparable_suppression": bool(
            q_delta > FLOAT_TOLERANCE
            and (
                removed_to_missed["non_comparable_count"]
                or removed_order_to_missed["non_comparable_count"]
            )
        ),
        "economic_improvement_claim_authorized": False,
    }


def materiality_class(value: float, threshold: float, suppression_present: bool) -> str:
    if suppression_present and value > 0:
        return "non_claimable_positive_with_execution_suppression"
    if value > threshold:
        return "material_positive"
    if value < -threshold:
        return "material_negative"
    return "inconclusive_inside_closed_symmetric_band"


def directional_class(value: float, suppression_present: bool) -> str:
    if suppression_present and value > FLOAT_TOLERANCE:
        return "non_claimable_positive_with_execution_suppression"
    if value > FLOAT_TOLERANCE:
        return "positive"
    if value < -FLOAT_TOLERANCE:
        return "negative"
    return "flat"


def finalize_self_hash(payload: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(payload)
    payload["self_hash"] = {
        "algorithm": "sha256",
        "canonicalization": "utf8_json_sort_keys_compact_separators_ensure_ascii_false",
        "excluded_path": "self_hash.sha256",
    }
    payload["self_hash"]["sha256"] = stable_sha256(payload)
    return payload


def build_audit(config: AnalyzerConfig, *, verifier_module: Any | None = None) -> dict[str, Any]:
    validate_production_path_bindings(config)
    production_mode = config.frozen == DEFAULT_FROZEN
    injected_verifier = verifier_module is not None
    if production_mode and injected_verifier:
        raise MatrixAuditError("production_verifier_module_injection_forbidden")
    paths_by_arm = preflight_namespaces(config)
    partial_bundles = validate_partial_completion_markers(paths_by_arm)
    initial_fingerprints = capture_namespace_fingerprints(paths_by_arm)
    analyzer_initial_fingerprint = file_fingerprint(ANALYZER_PATH)
    verifier_initial_fingerprint = file_fingerprint(VERIFIER_PATH)
    if (
        production_mode
        and verifier_initial_fingerprint["sha256"] != FROZEN_VERIFIER_SHA256
    ):
        raise MatrixAuditError(
            "production_frozen_verifier_sha256_mismatch:"
            f"expected={FROZEN_VERIFIER_SHA256}:"
            f"actual={verifier_initial_fingerprint['sha256']}"
        )
    failures: list[dict[str, Any]] = []
    protocol, contract, control_records = validate_protocol_and_contract(config, failures)
    control_records["matrix_analyzer"] = {
        "path": str(ANALYZER_PATH),
        "bytes": analyzer_initial_fingerprint["bytes"],
        "sha256": analyzer_initial_fingerprint["sha256"],
    }
    control_records["verifier"] = {
        "path": str(VERIFIER_PATH),
        "bytes": verifier_initial_fingerprint["bytes"],
        "sha256": verifier_initial_fingerprint["sha256"],
        "frozen_expected_sha256": FROZEN_VERIFIER_SHA256,
        "frozen_sha256_match": (
            verifier_initial_fingerprint["sha256"] == FROZEN_VERIFIER_SHA256
        ),
        "code_authority_path": VERIFIER_CODE_AUTHORITY_PATH,
        "provenance_status": (
            "SEALED_PRODUCTION_VERIFIER_SOURCE_BOUND"
            if production_mode
            else "TEST_ONLY_INJECTED_VERIFIER_NON_PRODUCTION"
        ),
        "production_audit_authority": production_mode,
        "injected_verifier_module": injected_verifier,
        "scan_results_attributed_to_frozen_verifier": not injected_verifier,
        "required_scan_functions": list(SCAN_FUNCTIONS),
        "required_summary_issue_functions": list(SUMMARY_ISSUE_FUNCTIONS),
    }
    verifier = verifier_module if verifier_module is not None else load_verifier()
    surfaces: dict[str, ArmSurface] = {}
    per_arm_verification: dict[str, Any] = {}
    per_arm_lifecycle: dict[str, Any] = {}
    for arm_id in ARM_ORDER:
        surface = load_arm_surface(
            arm_id,
            paths_by_arm[arm_id],
            config,
            failures,
            partial_bundles[arm_id],
        )
        validate_economics_parity(surface, config.frozen, failures)
        scans, summary_issues = run_verifier_scans(
            surface,
            verifier,
            failures,
            config.frozen,
        )
        lifecycle = validate_lifecycle(surface, config.frozen, failures)
        surfaces[arm_id] = surface
        per_arm_verification[arm_id] = {
            "direct_scans": scans,
            "summary_contract_issues": summary_issues,
        }
        per_arm_lifecycle[arm_id] = lifecycle

    reference_candidates = surfaces["S0R0"].candidate_keys
    reference_windows = surfaces["S0R0"].decision_windows
    for arm_id in ARM_ORDER[1:]:
        if surfaces[arm_id].candidate_keys != reference_candidates:
            add_failure(
                failures,
                "cross_arm_candidate_universe_mismatch",
                arm_id=arm_id,
                missing_count=len(reference_candidates - surfaces[arm_id].candidate_keys),
                extra_count=len(surfaces[arm_id].candidate_keys - reference_candidates),
            )
        if surfaces[arm_id].decision_windows != reference_windows:
            add_failure(failures, "cross_arm_scorecard_window_mismatch", arm_id=arm_id)
    hard_pool_pairs: dict[str, Any] = {}
    for label, left, right in (
        ("fixed_risk_selection_pair", "S0R0", "S1R0"),
        ("dynamic_risk_selection_pair", "S0R1", "S1R1"),
    ):
        equal = surfaces[left].hard_pools == surfaces[right].hard_pools
        hard_pool_pairs[label] = {"left": left, "right": right, "equal": equal}
        if not equal:
            add_failure(failures, "selection_pair_hard_pool_mismatch", pair=label)

    coverage_values = {
        arm_id: surfaces[arm_id].economics["scoreable_risk_coverage"]
        for arm_id in ARM_ORDER
    }
    for arm_id, coverage in coverage_values.items():
        if coverage + FLOAT_TOLERANCE < config.frozen.minimum_scoreable_risk_coverage:
            add_failure(
                failures,
                "arm_scoreable_risk_coverage_below_floor",
                arm_id=arm_id,
                coverage=coverage,
                floor=config.frozen.minimum_scoreable_risk_coverage,
            )
    coverage_gap = max(coverage_values.values()) - min(coverage_values.values())
    if coverage_gap > config.frozen.maximum_arm_scoreability_gap + FLOAT_TOLERANCE:
        add_failure(
            failures,
            "cross_arm_scoreable_risk_coverage_gap_exceeded",
            gap=coverage_gap,
            maximum=config.frozen.maximum_arm_scoreability_gap,
        )

    scalar_metrics = (
        "cash_per_accepted_risk_dollar",
        "fixed_denominator_portfolio_r",
        "physical_net_r",
        "headline_net_r",
        "accepted_risk_cash",
        "aggregate_risk_pct",
        "scoreable_risk_coverage",
        "execution_cost_r",
        "max_drawdown_cash",
        "tail_loss_net_r",
    )
    effects = {
        metric: contrast(
            {arm_id: float(surfaces[arm_id].economics[metric]) for arm_id in ARM_ORDER}
        )
        for metric in scalar_metrics
    }
    transitions = {
        "selection_at_r0": transition(surfaces["S0R0"], surfaces["S1R0"]),
        "sizing_at_s0": transition(surfaces["S0R0"], surfaces["S0R1"]),
        "selection_at_r1": transition(surfaces["S0R1"], surfaces["S1R1"]),
        "sizing_at_s1": transition(surfaces["S1R0"], surfaces["S1R1"]),
        "total_incumbent": transition(surfaces["S0R0"], surfaces["S1R1"]),
    }
    for transition_name, payload in transitions.items():
        for reconciliation_name in (
            "removed_trade_to_candidate_missed_reconciliation",
            "added_trade_from_baseline_missed_reconciliation",
            "removed_order_to_candidate_missed_reconciliation",
            "added_order_from_baseline_missed_reconciliation",
        ):
            reconciliation = payload[reconciliation_name]
            missing_keys = reconciliation["missing_keys"]
            if missing_keys:
                add_failure(
                    failures,
                    "cross_arm_order_fill_missed_transition_identity_mismatch",
                    transition=transition_name,
                    reconciliation=reconciliation_name,
                    missing_count=len(missing_keys),
                    missing_samples=missing_keys[:12],
                )
            r_mismatch_keys = reconciliation["trade_missed_r_mismatch_keys"]
            if r_mismatch_keys:
                add_failure(
                    failures,
                    "cross_arm_trade_missed_diagnostic_r_mismatch",
                    transition=transition_name,
                    reconciliation=reconciliation_name,
                    mismatch_count=len(r_mismatch_keys),
                    mismatch_samples=r_mismatch_keys[:12],
                )
    primary_values = effects["cash_per_accepted_risk_dollar"]
    primary_suppression = {
        "selection": transitions["selection_at_r0"]["positive_delta_with_execution_suppression"],
        "sizing": transitions["sizing_at_s0"]["positive_delta_with_execution_suppression"],
        "interaction": bool(
            primary_values["interaction"] > FLOAT_TOLERANCE
            and any(
                transitions[name]["execution_suppression_present"]
                for name in (
                    "selection_at_r0",
                    "sizing_at_s0",
                    "selection_at_r1",
                    "sizing_at_s1",
                )
            )
        ),
        "total_incumbent_value": transitions["total_incumbent"]["positive_delta_with_execution_suppression"],
    }
    primary_classification = {
        effect_name: materiality_class(
            value,
            config.frozen.materiality,
            primary_suppression[effect_name],
        )
        for effect_name, value in primary_values.items()
    }
    stress_scalar_values: dict[str, dict[str, float]] = {
        "raw_net_r": {
            arm_id: float(
                surfaces[arm_id].economics["stress"]["ledger_recomputed"][
                    "raw_net_r"
                ]
            )
            for arm_id in ARM_ORDER
        },
        "trade_count": {
            arm_id: float(
                surfaces[arm_id].economics["stress"]["ledger_recomputed"][
                    "trade_count"
                ]
            )
            for arm_id in ARM_ORDER
        },
    }
    incomplete_stress_metrics: dict[str, list[str]] = {}
    for stress_id in STRESS_SCENARIOS:
        for field_name in ("net_r", "min_trade_r", "loss_count"):
            metric = f"{stress_id}.{field_name}"
            values: dict[str, float] = {}
            missing_arms: list[str] = []
            for arm_id in ARM_ORDER:
                rows = surfaces[arm_id].economics["stress"][
                    "ledger_recomputed"
                ]["guarded_stress_rows"]
                by_id = {row["stress_id"]: row for row in rows}
                value = by_id.get(stress_id, {}).get(field_name)
                if value is None:
                    missing_arms.append(arm_id)
                else:
                    values[arm_id] = float(value)
            if missing_arms:
                incomplete_stress_metrics[metric] = missing_arms
            else:
                stress_scalar_values[metric] = values
    stress_effects: dict[str, Any] = {
        metric: {
            "status": "exact_structured_contrast",
            "contrasts": contrast(values),
            "classification": {
                effect_name: directional_class(
                    effect_value,
                    primary_suppression[effect_name],
                )
                for effect_name, effect_value in contrast(values).items()
            },
        }
        for metric, values in stress_scalar_values.items()
    }
    for metric, missing_arms in incomplete_stress_metrics.items():
        stress_effects[metric] = {
            "status": "not_comparable_missing_scoreable_stress_rows",
            "missing_arms": missing_arms,
        }

    namespace_stability = validate_namespace_stability(
        paths_by_arm,
        initial_fingerprints,
        surfaces,
        failures,
    )
    verifier_final_fingerprint = file_fingerprint(VERIFIER_PATH)
    analyzer_final_fingerprint = file_fingerprint(ANALYZER_PATH)
    verifier_stable = bool(
        verifier_initial_fingerprint["sha256"]
        == verifier_final_fingerprint["sha256"]
        and verifier_initial_fingerprint["bytes"]
        == verifier_final_fingerprint["bytes"]
    )
    control_records["verifier"].update(
        {
            "post_audit_sha256": verifier_final_fingerprint["sha256"],
            "stable_during_audit": verifier_stable,
        }
    )
    if not verifier_stable:
        add_failure(failures, "verifier_source_mutated_during_audit")
    analyzer_stable = bool(
        analyzer_initial_fingerprint["sha256"]
        == analyzer_final_fingerprint["sha256"]
        and analyzer_initial_fingerprint["bytes"]
        == analyzer_final_fingerprint["bytes"]
    )
    control_records["matrix_analyzer"].update(
        {
            "post_audit_sha256": analyzer_final_fingerprint["sha256"],
            "stable_during_audit": analyzer_stable,
        }
    )
    if not analyzer_stable:
        add_failure(failures, "matrix_analyzer_source_mutated_during_audit")

    valid = not failures
    development_authorized = bool(valid and production_mode)
    arm_payloads = {
        arm_id: {
            "prefix": surface.prefix,
            "artifacts": surface.artifacts,
            "binding_field_count": len(expected_flat_binding(arm_id, config.frozen)),
            "binding_mismatch_count": surface.binding_mismatch_count,
            "binding_mismatch_samples": surface.binding_mismatch_samples,
            "authority_violation_count": surface.authority_violation_count,
            "authority_violation_samples": surface.authority_violation_samples,
            "candidate_instance_count": len(surface.candidate_keys),
            "candidate_instance_digest_sha256": stable_sha256(sorted(surface.candidate_keys)),
            "decision_window_count": len(surface.decision_windows),
            "decision_window_digest_sha256": stable_sha256(sorted(surface.decision_windows)),
            "hard_pool_projection_digest_sha256": stable_sha256(surface.hard_pools),
            "candidate_scorecard_order_fill_identity": (
                surface.relational_identity_audit
            ),
            "economics": surface.economics,
            "missed_outcomes": {
                key: round(value, 8) if isinstance(value, float) else value
                for key, value in surface.missed.items()
            },
            "lifecycle": per_arm_lifecycle[arm_id],
            "verification": per_arm_verification[arm_id],
        }
        for arm_id, surface in surfaces.items()
    }
    audit = {
        "schema": "gtos.b7_5.selection_sizing.engineering_june_matrix_audit.v1",
        "status": (
            "PASS_ENGINEERING_MATRIX_DEVELOPMENT_WINDOWS_AUTHORIZED"
            if development_authorized
            else (
                "PASS_TEST_ONLY_NON_PRODUCTION_AUDIT"
                if valid
                else "FAIL_ENGINEERING_MATRIX_DEVELOPMENT_WINDOWS_BLOCKED"
            )
        ),
        "valid": valid,
        "scope": {
            "window_id": "engineering_june_04",
            "window_start": "2026-06-04",
            "window_end": "2026-06-04",
            "arms": list(ARM_ORDER),
            "replay_launched_by_builder": False,
            "outcome_artifact_glob_used": False,
            "march_outcome_read": False,
            "audit_mode": (
                "sealed_production_audit"
                if production_mode
                else "test_only_non_production"
            ),
        },
        "control_inputs": {
            **control_records,
            "protocol_schema": protocol.get("schema"),
            "decision_contract_schema": contract.get("schema"),
            "source_plan_sha256": config.frozen.source_plan_sha256,
            "contract_self_hash_sha256": config.frozen.contract_self_hash_sha256,
            "common_execution_input_sha256": config.frozen.common_execution_input_sha256,
        },
        "arms": arm_payloads,
        "namespace_stability": namespace_stability,
        "cross_arm_identity": {
            "candidate_universe_equal": all(
                surface.candidate_keys == reference_candidates for surface in surfaces.values()
            ),
            "scorecard_windows_equal": all(
                surface.decision_windows == reference_windows for surface in surfaces.values()
            ),
            "selection_pair_hard_pools": hard_pool_pairs,
            "order_instance_counts": {
                arm_id: len(surface.order_instances)
                for arm_id, surface in surfaces.items()
            },
            "order_event_counts": {
                arm_id: sum(
                    len(events) for events in surface.order_events_by_id.values()
                )
                for arm_id, surface in surfaces.items()
            },
            "filled_order_instance_counts": {
                arm_id: sum(
                    bool(order["filled"])
                    for order in surface.order_instances.values()
                )
                for arm_id, surface in surfaces.items()
            },
        },
        "scoreable_risk_coverage": {
            "by_arm": coverage_values,
            "minimum_required": config.frozen.minimum_scoreable_risk_coverage,
            "maximum_cross_arm_gap": round(coverage_gap, 12),
            "maximum_allowed_cross_arm_gap": config.frozen.maximum_arm_scoreability_gap,
        },
        "factorial_effects": {
            "primary_metric": "scoreable_net_cash_divided_by_total_accepted_risk_cash",
            "formulas": {
                "selection": "S1R0-S0R0",
                "sizing": "S0R1-S0R0",
                "interaction": "S1R1-S1R0-S0R1+S0R0",
                "total_incumbent_value": "S1R1-S0R0",
            },
            "scalar_effects": effects,
            "primary_symmetric_materiality": config.frozen.materiality,
            "primary_classification": primary_classification,
            "physical_stress_effects": stress_effects,
        },
        "suppression_and_missed_reconciliation": {
            "positive_by_suppression_forbidden": True,
            "primary_effect_execution_suppression_present": primary_suppression,
            "transitions": transitions,
            "economic_improvement_claim_authorized": False,
            "june_window_is_engineering_smoke_only": True,
        },
        "failures": failures,
        "failure_count": len(failures),
        "disposition": {
            "engineering_matrix_hard_valid": valid,
            "development_windows_authorized": development_authorized,
            "factor_or_policy_promotion_authorized": False,
            "broker_mutation_enabled": False,
            "live_broker_authority": False,
            "canary_authority": False,
            "final_selection_claim": False,
            "march_outcome_read": False,
        },
    }
    return finalize_self_hash(audit)


def verify_self_hash(payload: Mapping[str, Any]) -> bool:
    candidate = copy.deepcopy(dict(payload))
    self_hash = candidate.get("self_hash")
    if not isinstance(self_hash, dict):
        return False
    expected = self_hash.pop("sha256", None)
    return isinstance(expected, str) and expected == stable_sha256(candidate)


def write_audit(path: Path, payload: Mapping[str, Any]) -> None:
    if not verify_self_hash(payload):
        raise MatrixAuditError("audit_self_hash_invalid_before_write")
    path.parent.mkdir(parents=True, exist_ok=True)
    material = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(material, encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DENOMINATOR_ROUTE)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    parser.add_argument("--decision-contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    for arm_id in ARM_ORDER:
        parser.add_argument(
            f"--{arm_id.lower()}-prefix",
            default=DEFAULT_PREFIXES[arm_id],
        )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run the complete audit and print its status without writing output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AnalyzerConfig(
        artifact_root=args.artifact_root.resolve(),
        protocol_path=args.protocol.resolve(),
        contract_path=args.decision_contract.resolve(),
        output_path=args.output.resolve(),
        prefixes={arm_id: getattr(args, f"{arm_id.lower()}_prefix") for arm_id in ARM_ORDER},
    )
    try:
        audit = build_audit(config)
    except IncompleteNamespaceError as exc:
        print(json.dumps({"status": "INCOMPLETE_MATRIX_NAMESPACE", "error": str(exc)}, sort_keys=True))
        return 2
    except MatrixAuditError as exc:
        print(json.dumps({"status": "MATRIX_AUDIT_INPUT_INVALID", "error": str(exc)}, sort_keys=True))
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
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if audit["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
