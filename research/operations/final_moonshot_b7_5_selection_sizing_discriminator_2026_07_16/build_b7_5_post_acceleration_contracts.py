#!/usr/bin/env python3
"""Seal the outcome-blind B7.5 contract over the accepted accelerator.

The historical v2 contract is deliberately preserved as an immutable
predecessor.  This builder creates a successor decision contract from sealed
protocol, current behavior/config/package bytes, and accepted acceleration
evidence.  A separate execution seal is built after a window's source bundle
has been independently authenticated; keeping the two artifacts separate
avoids a self-hash cycle because the replay shared-contract digest contains
the decision-contract self hash.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
RUNTIME_EVIDENCE_ROOT = Path("/Users/borr/GTOSActive/repo")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 import (  # noqa: E402,E501
    build_b7_5_selection_sizing_decision_contract as sealed,
)

DECISION_SCHEMA = "gtos.b7_5.post_acceleration_decision_contract.v1"
DECISION_STATUS = "SEALED_POST_ACCELERATION_REPLAY_FREE_DECISION_CONTRACT_VALID"
DECISION_OUTPUT_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
EXECUTION_OUTPUT_PATH = ROUTE / "B7_5_POST_ACCELERATION_EXECUTION_SEAL.json"
PACK_REBIND_OUTPUT_PATH = (
    ROUTE / "B7_5_POST_ACCELERATION_PREPARED_PACK_REBIND_AUTHORITY.json"
)

PREDECESSOR_RELATIVE_PATH = (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_SELECTION_SIZING_DECISION_CONTRACT.json"
)
PREDECESSOR_FILE_SHA256 = (
    "614fe667024a844972cf5df02e9a923da6fe4b8087bf385769de0d69d32b741a"
)
PREDECESSOR_SELF_HASH_SHA256 = (
    "f15ddbe2c67ee803ca88260887dc694594f793f6cbb85e0fc719f4fe14f74222"
)
PRE_CONTRACT_BASELINE_HEAD = "fa21b13f5a98380a98f790781f5e859e34c9205e"

TASK9_ACCEPTANCE_RELATIVE_PATH = (
    ".hermes/receipts/task9/task9-acceptance-20260723T052324Z/"
    "TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json"
)
TASK9_ACCEPTANCE_FILE_SHA256 = (
    "afa44b4437e749bc369d5615f9aea8205084e50c3724532cc96b2b7e5df9acd5"
)
TASK9_ACCEPTANCE_ROOT_SHA256 = (
    "9cfbc5b7bbd2d0fc47e7b7b84437dc3163518087f99a483d16f847376487a5be"
)
TASK9_REBIND_RELATIVE_PATH = (
    ".hermes/receipts/task9/"
    "task9-final-validation-review-rebind-20260723T071500Z/"
    "TASK9_FINAL_VALIDATION_REVIEW_REBIND.json"
)
TASK9_REBIND_FILE_SHA256 = (
    "4067480783d7d530b22c98850d97d2b3e8bd683ddb8e7849a47487a39f6565d6"
)
TASK9_REBIND_ROOT_SHA256 = (
    "a89bf1056df3e2d21850ca991178a824d3b2a937fb0fd77b5fa7e85cdf60adbe"
)

JUNE_SOURCE_PLAN_SHA256 = (
    "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
)
JANUARY_SOURCE_PLAN_SHA256 = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)

CANONICALIZATION = "utf8_json_sort_keys_compact_separators_ensure_ascii"


class PostAccelerationContractError(ValueError):
    """A successor contract input or invariant failed closed."""


@dataclass(frozen=True)
class InputSpec:
    input_id: str
    kind: str
    relative_path: str
    source_root: str = "workspace"


COMMON_INPUT_SPECS = (
    InputSpec("sealed_experiment_protocol", "protocol", sealed.PROTOCOL_RELATIVE_PATH),
    InputSpec("sealed_source_amendment_r1", "protocol_amendment", sealed.AMENDMENT_R1_RELATIVE_PATH),
    InputSpec("sealed_source_amendment_r2", "protocol_amendment", sealed.AMENDMENT_R2_RELATIVE_PATH),
    InputSpec("sealed_source_amendment_r3", "protocol_amendment", sealed.AMENDMENT_R3_RELATIVE_PATH),
    InputSpec("predecessor_decision_contract", "immutable_predecessor", PREDECESSOR_RELATIVE_PATH),
    InputSpec(
        "post_acceleration_contract_builder",
        "behavior_code",
        "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/build_b7_5_post_acceleration_contracts.py",
    ),
    InputSpec("post_acceleration_runner", "behavior_code", "src/research_infra/b7_5_post_acceleration_runner.py"),
    InputSpec("fresh_source_authority", "behavior_code", "src/research_infra/replay_acceleration_fresh_source_authority.py"),
    InputSpec("post_acceleration_semantic_verifier", "verification_code", "src/research_infra/b7_5_post_acceleration_semantic_verifier.py"),
    InputSpec("task2_semantic_acceptance", "verification_code", "src/research_infra/replay_acceleration_task2_semantic_acceptance.py"),
    InputSpec("attempt5_typed_sparse_runner", "behavior_code", "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"),
    InputSpec("workspace_paths", "behavior_code", "src/components/workspace_paths.py"),
    InputSpec("v4_timewarp_reducer", "behavior_code", "src/research_infra/v4_timewarp_simulated_live_research_loop.py"),
    InputSpec("prop_firm_headroom_v4", "behavior_code", "src/components/prop_firm_headroom_v4.py"),
    InputSpec(
        "selected_package_replay_bridge",
        "behavior_code",
        f"{sealed.EXECUTION_ROUTE}/run_selected_package_replay_bridge.py",
    ),
    InputSpec("selector_v4", "behavior_code", "src/components/selector_v4.py"),
    InputSpec("scheduler_v4", "behavior_code", "src/research/moonshot_scheduler_v4_best_trade_allocator.py"),
    InputSpec("execution_manager_v4", "behavior_code", "src/components/execution_manager_v4.py"),
    InputSpec("broker_net_cost_engine", "behavior_code", "src/components/broker_net_cost_engine.py"),
    InputSpec("same_symbol_lifecycle_v4", "behavior_code", "src/components/same_symbol_lifecycle_v4.py"),
    InputSpec("pending_nofill_lifecycle_v4", "behavior_code", "src/components/pending_nofill_lifecycle_v4.py"),
    InputSpec("exit_policy_v4", "behavior_code", "src/components/exit_policy_v4.py"),
    InputSpec("source_batch", "acceleration_code", "src/research_infra/replay_acceleration_source_batch.py"),
    InputSpec("integrated_source", "acceleration_code", "src/research_infra/replay_acceleration_integrated_source.py"),
    InputSpec("integrated_source_verifier", "verification_code", "src/research_infra/replay_acceleration_integrated_source_verifier.py"),
    InputSpec("immutable_evidence", "verification_code", "src/research_infra/replay_acceleration_immutable_evidence.py"),
    InputSpec("real_gate", "verification_code", "src/research_infra/replay_acceleration_real_gate.py"),
    InputSpec("contract_split", "verification_code", "src/research_infra/replay_acceleration_contract_split.py"),
    InputSpec("semantic_diagnostic", "verification_code", "src/research_infra/replay_semantic_diagnostic.py"),
    InputSpec("real_parity_verifier", "verification_code", "src/research_infra/replay_acceleration_real_parity_verifier.py"),
    InputSpec("streaming_archive", "proof_code", "src/research_infra/replay_acceleration_streaming_archive.py"),
    InputSpec("streaming_archive_verifier", "proof_code", "src/research_infra/replay_acceleration_streaming_archive_verifier.py"),
    InputSpec("compact_event_sink", "acceleration_code", "src/research_infra/replay_compact_event_sink.py"),
    InputSpec("prepared_day_pack", "acceleration_code", "src/research_infra/replay_prepared_day_pack.py"),
    InputSpec("task7_isolated_runner", "acceleration_code", "src/research_infra/replay_acceleration_task7_isolated_runner.py"),
    InputSpec("task9_final_validation", "acceleration_code", "src/research_infra/replay_acceleration_task9_final_validation.py"),
    InputSpec(
        "source_bound_execution_parity",
        "verification_code",
        f"{sealed.EXECUTION_ROUTE}/build_source_bound_execution_parity.py",
    ),
    InputSpec(
        "denominator_to_deployment_verifier",
        "verification_code",
        f"{sealed.EXECUTION_ROUTE}/verify_denominator_to_deployment_execution.py",
    ),
    InputSpec(
        "cap_lifecycle_repair_audit_r1",
        "accepted_predecision_safety_authority",
        "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_CAP_LIFECYCLE_REPAIR_AUDIT_R1.json",
    ),
    InputSpec("agent_config", "config", "config/agent_config.yaml"),
    InputSpec("ftmo_server3_profile", "config", "config/profiles/operator_profile.yaml"),
    InputSpec("ftmo_risk_profile", "config", "config/profiles/ftmo.yaml"),
)

PACKAGE_INPUT_SPECS = (
    InputSpec(
        "ultimate_candidate_package_sleeve_registry",
        "package_authority",
        f"{sealed.EXECUTION_ROUTE}/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl",
        "runtime_evidence",
    ),
    InputSpec(
        "ultimate_candidate_package_member_axis",
        "package_authority",
        f"{sealed.EXECUTION_ROUTE}/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl",
        "runtime_evidence",
    ),
)


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


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PostAccelerationContractError(code)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "009abcdef" for char in value
    )


def canonical_self_hash(payload: Mapping[str, Any]) -> str:
    projection = copy.deepcopy(dict(payload))
    self_hash = projection.get("self_hash")
    _require(isinstance(self_hash, dict), "self_hash_metadata_missing")
    self_hash.pop("sha256", None)
    return stable_sha256(projection)


def verify_self_hash(payload: Mapping[str, Any]) -> bool:
    self_hash = payload.get("self_hash")
    return bool(
        isinstance(self_hash, Mapping)
        and _is_sha256(self_hash.get("sha256"))
        and self_hash.get("sha256") == canonical_self_hash(payload)
    )


def _read_json(path: Path, *, code: str) -> tuple[dict[str, Any], str]:
    try:
        raw = Path(path).read_bytes()
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PostAccelerationContractError(code) from exc
    _require(isinstance(payload, dict), code)
    return payload, hashlib.sha256(raw).hexdigest()


def _input_path(spec: InputSpec) -> Path:
    root = RUNTIME_EVIDENCE_ROOT if spec.source_root == "runtime_evidence" else ROOT
    path = (root / spec.relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PostAccelerationContractError(
            f"input_path_escape:{spec.input_id}"
        ) from exc
    _require(path.is_file() and not path.is_symlink(), f"input_missing:{spec.input_id}")
    return path


def hash_inputs(specs: Sequence[InputSpec]) -> list[dict[str, Any]]:
    _require(len({row.input_id for row in specs}) == len(specs), "duplicate_input_id")
    rows: list[dict[str, Any]] = []
    for spec in specs:
        path = _input_path(spec)
        size = path.stat().st_size
        _require(size > 0, f"input_empty:{spec.input_id}")
        rows.append(
            {
                "input_id": spec.input_id,
                "kind": spec.kind,
                "path": spec.relative_path,
                "sha256": file_sha256(path),
                "bytes": size,
                "source_root": spec.source_root,
            }
        )
    return rows


def _validate_predecessor() -> dict[str, Any]:
    path = ROOT / PREDECESSOR_RELATIVE_PATH
    payload, digest = _read_json(path, code="predecessor_contract_invalid")
    _require(digest == PREDECESSOR_FILE_SHA256, "predecessor_file_sha256_mismatch")
    _require(
        payload.get("schema") == sealed.SCHEMA
        and payload.get("status") == "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID"
        and payload.get("valid") is True
        and sealed.verify_contract_self_hash(payload)
        and payload.get("self_hash", {}).get("sha256")
        == PREDECESSOR_SELF_HASH_SHA256,
        "predecessor_contract_invalid",
    )
    return payload


def _validate_rooted_receipt(
    relative_path: str,
    *,
    expected_file_sha256: str,
    expected_root_sha256: str,
) -> dict[str, Any]:
    payload, digest = _read_json(ROOT / relative_path, code="task9_receipt_invalid")
    root = payload.get("receipt_root_sha256")
    projection = dict(payload)
    projection.pop("receipt_root_sha256", None)
    _require(digest == expected_file_sha256, "task9_receipt_file_sha256_mismatch")
    _require(
        root == expected_root_sha256 and root == stable_sha256(projection),
        "task9_receipt_root_mismatch",
    )
    return payload


def _acceleration_acceptance_binding() -> dict[str, Any]:
    acceptance = _validate_rooted_receipt(
        TASK9_ACCEPTANCE_RELATIVE_PATH,
        expected_file_sha256=TASK9_ACCEPTANCE_FILE_SHA256,
        expected_root_sha256=TASK9_ACCEPTANCE_ROOT_SHA256,
    )
    rebind = _validate_rooted_receipt(
        TASK9_REBIND_RELATIVE_PATH,
        expected_file_sha256=TASK9_REBIND_FILE_SHA256,
        expected_root_sha256=TASK9_REBIND_ROOT_SHA256,
    )
    transition = acceptance.get("transition")
    performance = acceptance.get("owner_adjusted_performance_disposition")
    _require(
        acceptance.get("schema") == "gtos.replay_acceleration.task9.final_acceptance.v1"
        and acceptance.get("acceptance_authorized") is True
        and isinstance(transition, Mapping)
        and transition.get("mission_phase_b_complete") is True
        and transition.get("mission_phase_c_authorized") is True
        and acceptance.get("broker_live_authority") is False
        and acceptance.get("broker_mutation_enabled") is False
        and acceptance.get("real_order_transmission_possible") is False
        and acceptance.get("economic_values_exposed") is False
        and isinstance(performance, Mapping)
        and performance.get("performance_target_pass_claimed") is False
        and performance.get("treatment")
        == "continue_by_explicit_owner_correctness_first_direction",
        "task9_acceptance_scope_invalid",
    )
    _require(
        rebind.get("schema") == "gtos.replay_acceleration.task9.review_rebind.v1"
        and rebind.get("exact_semantic_parity_all_trials") is True
        and rebind.get("broker_live_authority") is False
        and rebind.get("broker_mutation_enabled") is False
        and rebind.get("real_order_transmission_possible") is False
        and rebind.get("economic_values_exposed") is False,
        "task9_rebind_scope_invalid",
    )
    return {
        "task9_acceptance": {
            "path": TASK9_ACCEPTANCE_RELATIVE_PATH,
            "file_sha256": TASK9_ACCEPTANCE_FILE_SHA256,
            "receipt_root_sha256": TASK9_ACCEPTANCE_ROOT_SHA256,
            "status": acceptance["status"],
            "mission_phase_b_complete": True,
            "mission_phase_c_authorized": True,
        },
        "task9_review_rebind": {
            "path": TASK9_REBIND_RELATIVE_PATH,
            "file_sha256": TASK9_REBIND_FILE_SHA256,
            "receipt_root_sha256": TASK9_REBIND_ROOT_SHA256,
            "status": rebind["status"],
            "exact_semantic_parity_all_trials": True,
        },
        "performance_target_pass_claimed": False,
        "owner_adjusted_correctness_first_continuation": True,
        "speedup_claimed": False,
        "broker_live_authority": False,
        "real_order_transmission_possible": False,
    }


def build_decision_contract() -> dict[str, Any]:
    protocol, protocol_sha = sealed.read_and_validate_protocol(ROOT)
    r1, r1_sha = sealed.read_and_validate_amendment_r1(
        ROOT, protocol_file_sha256=protocol_sha
    )
    r2, r2_sha = sealed.read_and_validate_amendment_r2(
        ROOT, protocol_file_sha256=protocol_sha
    )
    r3, r3_sha = sealed.read_and_validate_amendment_r3(
        ROOT,
        protocol_file_sha256=protocol_sha,
        amendment_r1_file_sha256=r1_sha,
        amendment_r2_file_sha256=r2_sha,
    )
    _validate_predecessor()
    common_inputs = hash_inputs(COMMON_INPUT_SPECS)
    package_inputs = hash_inputs(PACKAGE_INPUT_SPECS)
    common_behavior_digest = stable_sha256(common_inputs)
    package_digest = stable_sha256(package_inputs)
    common_projection = {
        "common_behavior_input_digest_sha256": common_behavior_digest,
        "package_authority_input_digest_sha256": package_digest,
    }
    common_execution_digest = stable_sha256(common_projection)
    protocol_economics = sealed.sealed_protocol_economics(protocol)
    arms = [
        sealed.arm_fingerprint(
            protocol,
            arm,
            common_execution_input_digest_sha256=common_execution_digest,
        )
        for arm in protocol["arms"]
    ]
    _require(
        len({row["arm_fingerprint_sha256"] for row in arms}) == 4,
        "arm_fingerprints_not_unique",
    )
    windows = sealed.build_window_bindings(
        protocol,
        r1,
        r2,
        r3,
        amendment_r1_file_sha256=r1_sha,
        amendment_r2_file_sha256=r2_sha,
        amendment_r3_file_sha256=r3_sha,
    )
    windows_by_id = {row["window_id"]: row for row in windows}
    _require(
        windows_by_id["engineering_june_04"]["source_plan_digest_sha256"]
        == JUNE_SOURCE_PLAN_SHA256
        and windows_by_id["development_january"]["source_plan_digest_sha256"]
        == JANUARY_SOURCE_PLAN_SHA256,
        "active_source_plan_binding_mismatch",
    )

    payload: dict[str, Any] = {
        "schema": DECISION_SCHEMA,
        "status": DECISION_STATUS,
        "valid": True,
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "outcome_ledger_read_count": 0,
        "outcome_artifact_read_count": 0,
        "march_outcome_read": False,
        "pre_contract_baseline_head": PRE_CONTRACT_BASELINE_HEAD,
        "predecessor_contract_binding": {
            "path": PREDECESSOR_RELATIVE_PATH,
            "file_sha256": PREDECESSOR_FILE_SHA256,
            "self_hash_sha256": PREDECESSOR_SELF_HASH_SHA256,
            "schema": sealed.SCHEMA,
            "status": "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID",
            "preserved_immutable": True,
            "regeneration_forbidden": True,
        },
        "protocol_binding": {
            "path": sealed.PROTOCOL_RELATIVE_PATH,
            "file_sha256": protocol_sha,
            "schema": protocol["schema"],
            "status": protocol["status"],
            "sealed_at_utc": protocol["sealed_at_utc"],
        },
        "source_amendment_chain": {
            "r1": {"path": sealed.AMENDMENT_R1_RELATIVE_PATH, "file_sha256": r1_sha, "self_hash_sha256": r1["self_hash"]["sha256"]},
            "r2": {"path": sealed.AMENDMENT_R2_RELATIVE_PATH, "file_sha256": r2_sha, "self_hash_sha256": r2["self_hash"]["sha256"]},
            "r3": {"path": sealed.AMENDMENT_R3_RELATIVE_PATH, "file_sha256": r3_sha, "self_hash_sha256": r3["self_hash"]["sha256"]},
            "common_across_all_arms": True,
            "arm_varying_treatment": False,
        },
        "acceleration_acceptance_binding": _acceleration_acceptance_binding(),
        "input_bindings": {
            "common_behavior_inputs": common_inputs,
            "common_behavior_input_digest_sha256": common_behavior_digest,
            "package_authority_inputs": package_inputs,
            "package_authority_input_digest_sha256": package_digest,
            "common_execution_input_projection": common_projection,
            "common_execution_input_digest_sha256": common_execution_digest,
            "file_mtime_ctime_and_git_dirty_state_excluded": True,
        },
        "factorial_contract": {
            "neutral_selection_seed_sha256": protocol["neutral_selection_seed_sha256"],
            "neutral_selection_key": protocol["neutral_selection_key"],
            "neutral_selection_forbidden_inputs": copy.deepcopy(protocol["neutral_selection_forbidden_inputs"]),
            "factors": copy.deepcopy(protocol["factors"]),
            "only_declared_factor_deltas_may_vary_between_arms": True,
            "arms": arms,
            "attribution": copy.deepcopy(protocol["attribution"]),
        },
        "denominator": copy.deepcopy(protocol["denominator"]),
        "matched_risk": copy.deepcopy(protocol["matched_risk"]),
        "protocol_economics": protocol_economics,
        "protocol_economics_digest_sha256": stable_sha256(protocol_economics),
        "window_source_plan_bindings": windows,
        "window_source_plan_binding_digest_sha256": stable_sha256(windows),
        "source_plan_authority": {
            "engineering_june_04": JUNE_SOURCE_PLAN_SHA256,
            "development_january": JANUARY_SOURCE_PLAN_SHA256,
            "old_source_cells_may_not_mix": True,
        },
        "execution_order": copy.deepcopy(protocol["execution_order"]),
        "metrics": copy.deepcopy(protocol["metrics"]),
        "thresholds": copy.deepcopy(protocol["thresholds"]),
        "actions": copy.deepcopy(protocol["actions"]),
        "truth_rules": copy.deepcopy(protocol["truth_rules"]),
        "execution_seal_boundary": {
            "separate_artifact_required_before_policy_execution": True,
            "reason": "shared_execution_digest_contains_decision_contract_self_hash",
            "execution_seal_path": str(EXECUTION_OUTPUT_PATH.relative_to(ROOT)),
            "source_bundle_and_shared_digests_not_freely_declared": True,
        },
        "authority_boundary": {
            "decision_contract_only": True,
            "replay_launched": False,
            "outcomes_evaluated": False,
            "broker_live_final_authority": False,
            "broker_mutation_enabled": False,
            "real_order_transmission_possible": False,
        },
        "self_hash": {
            "algorithm": "sha256",
            "canonicalization": CANONICALIZATION,
            "excluded_path": "self_hash.sha256",
        },
    }
    payload["self_hash"]["sha256"] = canonical_self_hash(payload)
    _require(verify_self_hash(payload), "decision_contract_self_hash_failed")
    return payload


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def check_existing(path: Path, expected: Mapping[str, Any]) -> None:
    actual, _digest = _read_json(path, code="decision_contract_missing_or_invalid")
    _require(verify_self_hash(actual), "decision_contract_self_hash_mismatch")
    _require(actual == expected, "decision_contract_stale_or_input_drifted")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("decision", "pack-build-seal", "pack-rebind", "execution"),
        default="decision",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--decision-contract", type=Path, default=DECISION_OUTPUT_PATH)
    parser.add_argument("--window-id")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--source-plan-digest-sha256")
    parser.add_argument("--source-bundle-dir", type=Path)
    parser.add_argument("--source-selection", type=Path)
    parser.add_argument("--source-authority", type=Path)
    parser.add_argument("--source-authority-file-sha256")
    parser.add_argument("--source-authority-root-sha256")
    parser.add_argument("--source-bundle-root-sha256")
    parser.add_argument("--typed-cache-root", type=Path)
    parser.add_argument("--tick-sparse-cache-root", type=Path)
    parser.add_argument("--prepared-day-pack-root", type=Path)
    parser.add_argument("--predecessor-pack-receipt", type=Path)
    parser.add_argument("--predecessor-engine-receipt", type=Path)
    parser.add_argument("--predecessor-pack-build-seal", type=Path)
    parser.add_argument(
        "--prepared-pack-authority",
        type=Path,
        default=PACK_REBIND_OUTPUT_PATH,
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "decision":
        output = args.output or DECISION_OUTPUT_PATH
        payload = build_decision_contract()
        if args.check:
            check_existing(output, payload)
        else:
            atomic_write_json(output, payload)
        status = (
            "VALID_CURRENT_POST_ACCELERATION_DECISION_CONTRACT"
            if args.check
            else payload["status"]
        )
        result = {
            "status": status,
            "output": str(output),
            "self_hash_sha256": payload["self_hash"]["sha256"],
            "common_execution_input_digest_sha256": payload["input_bindings"]["common_execution_input_digest_sha256"],
            "arm_fingerprints": {
                row["arm_id"]: row["arm_fingerprint_sha256"]
                for row in payload["factorial_contract"]["arms"]
            },
            "replay_launched": False,
            "outcomes_evaluated": False,
            "broker_live_authority": False,
        }
    else:
        from src.research_infra import b7_5_post_acceleration_runner as phase_c

        required = {
            "window_id": args.window_id,
            "start": args.start,
            "end": args.end,
            "source_plan_digest_sha256": args.source_plan_digest_sha256,
            "source_bundle_dir": args.source_bundle_dir,
            "source_selection": args.source_selection,
            "source_authority": args.source_authority,
            "source_authority_file_sha256": args.source_authority_file_sha256,
            "source_authority_root_sha256": args.source_authority_root_sha256,
            "source_bundle_root_sha256": args.source_bundle_root_sha256,
            "typed_cache_root": args.typed_cache_root,
            "tick_sparse_cache_root": args.tick_sparse_cache_root,
        }
        if args.mode == "pack-rebind":
            required.update(
                {
                    "prepared_day_pack_root": args.prepared_day_pack_root,
                    "predecessor_pack_receipt": args.predecessor_pack_receipt,
                    "predecessor_engine_receipt": args.predecessor_engine_receipt,
                    "predecessor_pack_build_seal": (
                        args.predecessor_pack_build_seal
                    ),
                }
            )
        elif args.mode == "execution":
            required["prepared_pack_authority"] = args.prepared_pack_authority
        elif args.mode == "pack-build-seal":
            _require(
                args.output is not None,
                "pack_build_seal_output_required",
            )
        _require(
            all(value is not None and str(value).strip() for value in required.values()),
            f"{args.mode.replace('-', '_')}_arguments_incomplete",
        )
        common = {
            "decision_contract_path": args.decision_contract,
            "window_id": str(args.window_id),
            "start": str(args.start),
            "end": str(args.end),
            "source_plan_digest_sha256": str(args.source_plan_digest_sha256),
            "source_bundle_dir": Path(args.source_bundle_dir),
            "source_selection_path": Path(args.source_selection),
            "source_authority_path": Path(args.source_authority),
            "source_authority_file_sha256": str(
                args.source_authority_file_sha256
            ),
            "source_authority_root_sha256": str(
                args.source_authority_root_sha256
            ),
            "source_bundle_root_sha256": str(args.source_bundle_root_sha256),
            "typed_cache_root": Path(args.typed_cache_root),
            "tick_sparse_cache_root": Path(args.tick_sparse_cache_root),
        }
        if args.mode == "pack-build-seal":
            output = Path(args.output)
            payload = phase_c.build_pack_build_seal(**common)
            if args.check:
                actual, _digest = _read_json(
                    output, code="pack_build_seal_missing_or_invalid"
                )
                _require(
                    actual.get("pack_build_seal_root_sha256")
                    == phase_c.self_hash(
                        actual,
                        "pack_build_seal_root_sha256",
                    )
                    and actual == payload,
                    "pack_build_seal_stale_or_input_drifted",
                )
            else:
                atomic_write_json(output, payload)
            result = {
                "status": (
                    "VALID_CURRENT_POST_ACCELERATION_PACK_BUILD_SEAL"
                    if args.check
                    else payload["status"]
                ),
                "output": str(output),
                "pack_build_seal_root_sha256": payload[
                    "pack_build_seal_root_sha256"
                ],
                "arm_shared_execution_digests": {
                    arm_id: row["shared_execution_contract_digest_sha256"]
                    for arm_id, row in payload["arms"].items()
                },
                "replay_launched": False,
                "outcomes_evaluated": False,
                "broker_live_authority": False,
            }
        elif args.mode == "pack-rebind":
            output = args.output or PACK_REBIND_OUTPUT_PATH
            payload = phase_c.build_prepared_pack_rebind_authority(
                **common,
                prepared_day_pack_root=Path(args.prepared_day_pack_root),
                predecessor_pack_receipt_path=Path(
                    args.predecessor_pack_receipt
                ),
                predecessor_engine_receipt_path=Path(
                    args.predecessor_engine_receipt
                ),
                predecessor_pack_build_seal_path=Path(
                    args.predecessor_pack_build_seal
                ),
            )
            if args.check:
                actual, _digest = _read_json(
                    output, code="prepared_pack_rebind_missing_or_invalid"
                )
                _require(
                    actual.get("authority_root_sha256")
                    == phase_c.self_hash(actual, "authority_root_sha256")
                    and actual == payload,
                    "prepared_pack_rebind_stale_or_input_drifted",
                )
            else:
                atomic_write_json(output, payload)
            result = {
                "status": (
                    "VALID_CURRENT_POST_ACCELERATION_PREPARED_PACK_REBIND"
                    if args.check
                    else payload["status"]
                ),
                "output": str(output),
                "authority_root_sha256": payload["authority_root_sha256"],
                "prepared_day_pack_roots": payload[
                    "prepared_day_pack_roots"
                ],
                "replay_launched": False,
                "outcomes_evaluated": False,
                "broker_live_authority": False,
            }
        else:
            output = args.output or EXECUTION_OUTPUT_PATH
            payload = phase_c.build_execution_seal(
                **common,
                prepared_pack_authority_path=Path(
                    args.prepared_pack_authority
                ),
            )
            if args.check:
                actual, _digest = _read_json(
                    output, code="execution_seal_missing_or_invalid"
                )
                _require(
                    actual.get("execution_seal_root_sha256")
                    == phase_c.self_hash(actual, "execution_seal_root_sha256")
                    and actual == payload,
                    "execution_seal_stale_or_input_drifted",
                )
            else:
                atomic_write_json(output, payload)
            result = {
                "status": (
                    "VALID_CURRENT_POST_ACCELERATION_EXECUTION_SEAL"
                    if args.check
                    else payload["status"]
                ),
                "output": str(output),
                "execution_seal_root_sha256": payload[
                    "execution_seal_root_sha256"
                ],
                "arm_shared_execution_digests": {
                    arm_id: row["shared_execution_contract_digest_sha256"]
                    for arm_id, row in payload["arms"].items()
                },
                "replay_launched": False,
                "outcomes_evaluated": False,
                "broker_live_authority": False,
            }
    print(
        json.dumps(result, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
