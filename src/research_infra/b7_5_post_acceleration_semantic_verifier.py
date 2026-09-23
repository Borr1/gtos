"""Independent June parent binding and post-acceleration semantic comparator."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as semantic,
)
from src.research_infra.replay_canonical_bytes import (
    canonical_bytes as _sealing_canonical_bytes,
)


ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / (
    "research/operations/"
    "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
)
PARENT_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-attempt5-20260719/"
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
LFS_OBJECT_ROOT = Path("/Users/borr/GTOSActive/repo/.git/lfs/objects")
PARENT_MANIFEST_SCHEMA = "gtos.b7_5.june_cap_r2_parent_manifest.v1"
COMPARISON_SCHEMA = "gtos.b7_5.post_acceleration_semantic_parity.v1"
JUNE_SOURCE_PLAN_SHA256 = (
    "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
)
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
DECISION_CONTRACT_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
EXECUTION_SEAL_PATH = ROUTE / "B7_5_POST_ACCELERATION_EXECUTION_SEAL.json"
ARM_RECEIPT_NAME = "B7_5_POST_ACCELERATION_ARM_RECEIPT.json"
SEMANTIC_PARITY_NAME = "B7_5_POST_ACCELERATION_SEMANTIC_PARITY.json"
CONTRACT_IDENTITY_SENTINEL = "<SEALED_POST_ACCELERATION_CONTRACT_IDENTITY>"
SOURCE_DISCOVERY_COUNT_SENTINEL = "<NONCAUSAL_SOURCE_DISCOVERY_CANDIDATE_COUNT>"
CAPPED_DIAGNOSTIC_SENTINEL = "<NONCAUSAL_CAPPED_CONFLICT_DIAGNOSTIC>"

_TOP_LEVEL_CONTRACT_IDENTITIES = {
    "b7_5_selection_sizing_factorial_arm_fingerprint_sha256": (
        "arm_fingerprint_sha256"
    ),
    "b7_5_selection_sizing_factorial_binding_payload_sha256": (
        "binding_payload_sha256"
    ),
    "b7_5_selection_sizing_factorial_common_execution_input_digest_sha256": (
        "common_execution_input_digest_sha256"
    ),
    "b7_5_selection_sizing_factorial_decision_contract_sha256": (
        "decision_contract_sha256"
    ),
}
_NESTED_CONTRACT_IDENTITIES = {
    "arm_fingerprint_sha256",
    "binding_payload_sha256",
    "common_execution_input_digest_sha256",
    "decision_contract_sha256",
}
_SOURCE_OVERLAP_ROW_TYPE = "m1_source_overlap_validation"
_SOURCE_SELECTED_M1_ROW_TYPE = "m1_symbol_day_source"
_JUNE_EXPECTED_SYMBOL_COUNT = 24

PHASE_C_PROJECTION_RATIONALES = {
    "post_acceleration_contract_identity": {
        "classification": "sealed_provenance_successor_not_behavior",
        "excluded_fields": sorted(_TOP_LEVEL_CONTRACT_IDENTITIES),
        "nested_scope": "b7_5_selection_sizing_factorial_binding_only",
        "proof": (
            "old values must equal the immutable CAP_R2 acceptance audit and "
            "new values must equal the validated decision contract, execution "
            "seal, and arm execution receipt"
        ),
        "semantic_or_economic_value_hidden": False,
    },
    "source_discovery_transport": {
        "classification": "preselection_diagnostic_transport_only",
        "excluded_parent_row_type": _SOURCE_OVERLAP_ROW_TYPE,
        "normalized_fields": [
            "candidate_source_count",
            "populated_candidate_source_count",
        ],
        "proof": (
            "the parent contains one overlap-consistency diagnostic per symbol "
            "and reports two equivalent discovery candidates; the authenticated "
            "fresh bundle carries only the already accepted member. Every "
            "selected source path, payload hash, authority hash, row count, "
            "status, symbol, day, and tick/bar membership remains exact"
        ),
        "semantic_or_economic_value_hidden": False,
    },
    "capped_conflict_diagnostic": {
        "classification": "noncausal_bounded_stale_input_diagnostic_only",
        "excluded_field": "risk_finalizer_stale_surface_conflicts",
        "proof": (
            "every persisted tuple is schema checked and connected through its "
            "stale-to-canonical conflict chain to an authoritative effective field "
            "persisted in the same scorecard row, including the one explicitly "
            "AST-proven executable-reason alias; the producer has no decision "
            "consumer, and the complete conflict count, sorted conflict-key set, "
            "and all effective fields remain exact"
        ),
        "explicit_effective_field_aliases": {
            "replay_candidate_use_allowed_now_reason": [
                "package_replay_executable_candidate_use_allowed_reason"
            ],
        },
        "persisted_stale_tuple_subset_may_differ": True,
        "disconnected_stage_tuple_rule": (
            "permitted_only_when_the_persisted_first_32_is_provably_truncated_"
            "and_the_same_key_has_an_exact_effective_field_witness"
        ),
        "diagnostic_numeric_witness_absolute_tolerance": 5e-9,
        "semantic_or_economic_value_hidden": False,
    },
}

AUDIT_BINDINGS = {
    "S0R0": {
        "file_sha256": "aeae8b9fb05061d358d0113d19b8be5b42d648c410b65ea0803fa744c5a80176",
        "self_hash_sha256": "f2149de6c79e8cef46f27aeebf8e6b8b88c53763479e7e5fd6f19d3beb8a4dcf",
    },
    "S1R0": {
        "file_sha256": "9d9f218e3db9f29e8ff47b9a4e53a8a47f196d1d3cda20c2f4ae91565b83bcd1",
        "self_hash_sha256": "6683d9b7077dcb9b28c4575e09c973c65a16d6960cb6ea973c82ad89d73679eb",
    },
    "S0R1": {
        "file_sha256": "dd833bcc7fcbb92ae8661df22115986cce1a16de57878410efd667b61b24524a",
        "self_hash_sha256": "76d59407195bdbca6f3a7e392b942822055628885883e06489b33e7195ea700a",
    },
    "S1R1": {
        "file_sha256": "f1d86c737cf31c17b354862e8e92ca37fa8f1d1ae30ed966ecdb09974a26e788",
        "self_hash_sha256": "f70ee4b65eeee61755f3f47e4d83fa69e780be532b1505aa984c0afb5a59da79",
    },
}
MATRIX_AUDIT_FILE_SHA256 = (
    "93f652cc4a826fedbf56a0f8f861f7b8052e90a59536bf9294696d11423b91cb"
)
MATRIX_AUDIT_SELF_HASH_SHA256 = (
    "9c05d91618785d461f15041caadfdc1948b1249a48798cafe343141382ddba4c"
)

ROLE_SUFFIXES = {
    "source": "_SOURCE_UNIVERSE_LEDGER.jsonl",
    "decision": "_DECISION_LEDGER.jsonl",
    "scorecard": "_SCORECARD_LEDGER.jsonl",
    "order": "_ORDER_LEDGER.jsonl",
    "trade": "_TRADE_LEDGER.jsonl",
    "oracle": "_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "_BUCKET_LEDGER.jsonl",
    "comparison": "_COMPARISON_LEDGER.jsonl",
    "partial_summary": "_PARTIAL_SUMMARY.json",
    "summary": "_SUMMARY.json",
}
JSONL_ROLES = tuple(
    role for role in ROLE_SUFFIXES if role not in {"partial_summary", "summary"}
)
LFS_POINTER = re.compile(
    rb"\Aversion https://git-lfs.github.com/spec/v1\n"
    rb"oid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n\Z"
)


class PhaseCSemanticError(ValueError):
    """A parent binding or meaningful semantic comparison failed closed."""


def canonical_bytes(value: Any) -> bytes:
    """R-P1, landed 2026-07-26 under the R2 verification-split contract.

    This encoder used ``allow_nan=True``. Because parity is decided on BYTES,
    ``b"NaN" == b"NaN"`` — so two runs that both produced an undefined economic
    value compared EQUAL and this verifier reported zero differences. The
    28 sealing encoders all use ``allow_nan=False`` and raise on the same input.

    The fix landed in ``replay_semantic_parity`` in July and could not land here:
    this file was SHA-bound in the R1 decision contract, and editing it made the
    next replay fail closed with
    ``selection_sizing_decision_contract_input_drift``. OD-2's split moved it to
    ``input_bindings.verification_tooling``, which the enforcement loop does not
    read, so the hole closes now.
    """

    return _sealing_canonical_bytes(value)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "009abcdef" for char in value
    )


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PhaseCSemanticError(code)


def _self_hash(payload: Mapping[str, Any], field: str) -> str:
    projection = copy.deepcopy(dict(payload))
    if field == "self_hash.sha256":
        self_hash = projection.get("self_hash")
        _require(isinstance(self_hash, dict), "parent_audit_self_hash_missing")
        self_hash.pop("sha256", None)
    else:
        projection.pop(field, None)
    return stable_sha256(projection)


def _audit_path(arm_id: str) -> Path:
    return ROUTE / f"B7_5_SELECTION_SIZING_{arm_id}_SOURCE_REPAIRED_CAP_R2_ACCEPTANCE_AUDIT.json"


def _load_audit(arm_id: str) -> tuple[dict[str, Any], Path]:
    _require(arm_id in ARM_ORDER, "parent_arm_invalid")
    path = _audit_path(arm_id)
    try:
        raw = path.read_bytes()
        audit = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PhaseCSemanticError("parent_audit_invalid") from exc
    expected = AUDIT_BINDINGS[arm_id]
    _require(
        isinstance(audit, dict)
        and hashlib.sha256(raw).hexdigest() == expected["file_sha256"]
        and audit.get("arm_id") == arm_id
        and audit.get("self_hash", {}).get("sha256")
        == expected["self_hash_sha256"]
        and _self_hash(audit, "self_hash.sha256")
        == expected["self_hash_sha256"]
        and audit.get("source_and_contract_binding", {}).get(
            "source_plan_digest_sha256"
        )
        == JUNE_SOURCE_PLAN_SHA256,
        "parent_audit_identity_mismatch",
    )
    return audit, path


def _resolve_artifact(
    logical_path: Path,
    *,
    expected_sha256: str,
    expected_bytes: int,
    verify_payload_hash: bool,
) -> dict[str, Any]:
    _require(logical_path.is_file() and not logical_path.is_symlink(), "parent_logical_artifact_missing")
    raw_head = logical_path.read_bytes() if logical_path.stat().st_size <= 256 else b""
    pointer = LFS_POINTER.fullmatch(raw_head)
    if pointer is not None:
        oid = pointer.group(1).decode("ascii")
        declared_size = int(pointer.group(2))
        _require(
            oid == expected_sha256 and declared_size == expected_bytes,
            "parent_lfs_pointer_identity_mismatch",
        )
        resolved = LFS_OBJECT_ROOT / oid[:2] / oid[2:4] / oid
        transport = "git_lfs_object"
    else:
        oid = None
        resolved = logical_path
        transport = "working_tree_file"
    _require(
        resolved.is_file()
        and not resolved.is_symlink()
        and resolved.stat().st_size == expected_bytes,
        "parent_resolved_artifact_size_mismatch",
    )
    if verify_payload_hash:
        _require(
            file_sha256(resolved) == expected_sha256,
            "parent_resolved_artifact_sha256_mismatch",
        )
    return {
        "logical_path": str(logical_path),
        "resolved_path": str(resolved),
        "transport": transport,
        "lfs_oid_sha256": oid,
        "bytes": expected_bytes,
        "sha256": expected_sha256,
        "payload_hash_verified": bool(verify_payload_hash),
    }


def build_parent_manifest(
    arm_id: str,
    *,
    verify_payload_hashes: bool = True,
) -> dict[str, Any]:
    """Resolve every accepted parent byte surface without mutating it."""

    audit, audit_path = _load_audit(arm_id)
    prefix = str(audit.get("artifact_prefix") or "")
    files = audit.get("artifact_integrity", {}).get("files")
    _require(prefix and isinstance(files, Mapping), "parent_audit_artifacts_missing")
    artifacts: dict[str, Any] = {}
    for role, suffix in ROLE_SUFFIXES.items():
        expected = files.get(role)
        _require(isinstance(expected, Mapping), f"parent_role_missing:{role}")
        artifacts[role] = _resolve_artifact(
            PARENT_ROOT / f"{prefix}{suffix}",
            expected_sha256=str(expected.get("sha256") or ""),
            expected_bytes=int(expected.get("bytes") or 0),
            verify_payload_hash=verify_payload_hashes,
        )
        if role in JSONL_ROLES:
            artifacts[role]["rows"] = int(expected.get("rows") or 0)
    matrix_path = ROUTE / "B7_5_SELECTION_SIZING_ENGINEERING_JUNE_04_SOURCE_REPAIRED_CAP_R2_MATRIX_AUDIT.json"
    matrix_raw = matrix_path.read_bytes()
    matrix = json.loads(matrix_raw)
    _require(
        hashlib.sha256(matrix_raw).hexdigest() == MATRIX_AUDIT_FILE_SHA256
        and matrix.get("self_hash", {}).get("sha256")
        == MATRIX_AUDIT_SELF_HASH_SHA256
        and _self_hash(matrix, "self_hash.sha256")
        == MATRIX_AUDIT_SELF_HASH_SHA256,
        "parent_matrix_audit_invalid",
    )
    core = {
        "schema": PARENT_MANIFEST_SCHEMA,
        "status": "JUNE_CAP_R2_PARENT_BYTES_RESOLVED_READ_ONLY",
        "arm_id": arm_id,
        "artifact_prefix": prefix,
        "source_plan_digest_sha256": JUNE_SOURCE_PLAN_SHA256,
        "acceptance_audit": {
            "path": str(audit_path),
            "file_sha256": AUDIT_BINDINGS[arm_id]["file_sha256"],
            "self_hash_sha256": AUDIT_BINDINGS[arm_id]["self_hash_sha256"],
            "status": audit.get("status"),
        },
        "matrix_audit": {
            "path": str(matrix_path),
            "file_sha256": MATRIX_AUDIT_FILE_SHA256,
            "self_hash_sha256": MATRIX_AUDIT_SELF_HASH_SHA256,
            "status": matrix.get("status"),
        },
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "logical_bytes": sum(row["bytes"] for row in artifacts.values()),
        "all_payload_hashes_verified": bool(verify_payload_hashes),
        "namespace_mutated": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "manifest_root_sha256": stable_sha256(core)}


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("rb") as handle:
        for index, raw in enumerate(handle):
            _require(raw.endswith(b"\n"), f"jsonl_framing_invalid:{index}")
            try:
                row = json.loads(raw)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise PhaseCSemanticError(f"jsonl_row_invalid:{index}") from exc
            _require(isinstance(row, dict), f"jsonl_row_not_mapping:{index}")
            yield row


def accelerated_artifact_paths(output_dir: Path, prefix: str) -> dict[str, Path]:
    root = Path(output_dir)
    return {role: root / f"{prefix}{suffix}" for role, suffix in ROLE_SUFFIXES.items()}


def _derived_hash_proofs() -> dict[str, Any]:
    proofs = dict(semantic._CAMPAIGN_DERIVED_HASH_PROOF_CLASSES)
    proofs[
        "broker_order_lifecycle_capture_v4_packet/"
        "pre_order_capture_contract/execution_manager_packet_hash"
    ] = "PREIMAGE"
    proofs["missed:risk_authority_packet_hash_sha256"] = (
        "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH"
    )
    return proofs


def _has_packet_sidecar_material_compact_packets_call(tree: ast.AST) -> bool:
    """Recognize the bound packet-sidecar preimage without formatting coupling."""

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "evaluate_symbol_candidates_with_batched_proof_hashes"
    ]
    if len(functions) != 1:
        return False
    function = functions[0]
    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node is not function
        for node in ast.walk(function)
    ):
        return False

    def assignment_store_count(name: str) -> int:
        return sum(
            1
            for node in ast.walk(function)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            if any(
                isinstance(candidate, ast.Name) and candidate.id == name
                for candidate in ast.walk(target)
            )
        )

    if assignment_store_count("packet_sidecar_material") != 1:
        return False
    if assignment_store_count("packet_sidecar_future") != 1:
        return False
    material_stores = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == "packet_sidecar_material"
    ]
    if len(material_stores) != 1:
        return False

    def exact_material_assignment(statement: ast.stmt) -> bool:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id != "packet_sidecar_material"
        ):
            return False
        encode = statement.value
        if (
            not isinstance(encode, ast.Call)
            or not isinstance(encode.func, ast.Attribute)
            or encode.func.attr != "encode"
            or len(encode.args) != 1
            or not isinstance(encode.args[0], ast.Constant)
            or encode.args[0].value != "utf-8"
            or encode.keywords
        ):
            return False
        stable = encode.func.value
        if (
            not isinstance(stable, ast.Call)
            or not isinstance(stable.func, ast.Name)
            or stable.func.id != "_stable_sha256_material"
            or len(stable.args) != 1
            or stable.keywords
        ):
            return False
        compact = stable.args[0]
        if (
            not isinstance(compact, ast.Call)
            or not isinstance(compact.func, ast.Name)
            or compact.func.id != "compact_payload"
            or len(compact.args) != 1
            or not isinstance(compact.args[0], ast.Name)
            or compact.args[0].id != "packets"
            or len(compact.keywords) != 1
            or compact.keywords[0].arg != "max_bytes"
        ):
            return False
        max_bytes = compact.keywords[0].value
        return (
            isinstance(max_bytes, ast.Attribute)
            and max_bytes.attr == "candidate_ledger_packet_max_bytes"
            and isinstance(max_bytes.value, ast.Name)
            and max_bytes.value.id == "campaign"
        )

    def exact_submit(statement: ast.stmt) -> bool:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id != "packet_sidecar_future"
        ):
            return False
        submit = statement.value
        return (
            isinstance(submit, ast.Call)
            and isinstance(submit.func, ast.Attribute)
            and submit.func.attr == "submit"
            and isinstance(submit.func.value, ast.Name)
            and submit.func.value.id == "executor"
            and len(submit.args) == 2
            and isinstance(submit.args[0], ast.Name)
            and submit.args[0].id == "_sha256_hexdigest"
            and isinstance(submit.args[1], ast.Name)
            and submit.args[1].id == "packet_sidecar_material"
            and not submit.keywords
        )

    pending_loops = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == "pending"
        and {"packets", "future"}.issubset(
            {
                target.id
                for target in ast.walk(node.target)
                if isinstance(target, ast.Name)
            }
        )
    ]
    if len(pending_loops) != 1:
        return False
    matches = 0
    block = pending_loops[0].body
    for index, statement in enumerate(block[:-1]):
        if exact_material_assignment(statement) and exact_submit(block[index + 1]):
            matches += 1
    return matches == 1


def _phase_c_historical_hash_noncausal_contract() -> dict[str, Any]:
    """Bind historical hash-only producers to the current decision contract."""

    decision = json.loads(DECISION_CONTRACT_PATH.read_bytes())
    inputs = {
        row.get("input_id"): row
        for row in decision.get("input_bindings", {}).get(
            "common_behavior_inputs", []
        )
        if isinstance(row, Mapping)
    }
    producer_path = ROOT / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    headroom_path = ROOT / "src/components/prop_firm_headroom_v4.py"
    producer_binding = inputs.get("v4_timewarp_reducer")
    headroom_binding = inputs.get("prop_firm_headroom_v4")
    source = producer_path.read_text(encoding="utf-8")
    headroom_source = headroom_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(producer_path))
    _require(
        isinstance(producer_binding, Mapping)
        and isinstance(headroom_binding, Mapping)
        and producer_binding.get("sha256") == file_sha256(producer_path)
        and headroom_binding.get("sha256") == file_sha256(headroom_path)
        and "packet_sidecar_omitted_compact_broad_replay_hash_only" in source
        and '"payload_hash_sha256": stable_sha256(payload)' in source
        and _has_packet_sidecar_material_compact_packets_call(tree)
        and "captured_at_utc = (\n            str(decision_time_for_option)" in source
        and 'packet["packet_hash_sha256"] = stable_sha256(packet)' in source
        and 'reason="snapshot_not_broker_real"' in headroom_source,
        "historical_hash_producer_contract_changed",
    )
    executable_reason_alias_keys = {
        "package_replay_executable_candidate_use_allowed_reason",
        "replay_candidate_use_allowed_now_reason",
    }

    def executable_reason_assignments(node: ast.AST) -> set[str]:
        assigned: set[str] = set()
        for candidate in ast.walk(node):
            if (
                isinstance(candidate, ast.Assign)
                and len(candidate.targets) == 1
                and isinstance(candidate.targets[0], ast.Subscript)
                and isinstance(candidate.targets[0].value, ast.Name)
                and candidate.targets[0].value.id == "package_probe_quality"
                and isinstance(candidate.targets[0].slice, ast.Constant)
                and candidate.targets[0].slice.value
                in executable_reason_alias_keys
                and isinstance(candidate.value, ast.Name)
                and candidate.value.id == "package_executable_reason"
            ):
                assigned.add(str(candidate.targets[0].slice.value))
        return assigned

    executable_reason_alias_assignment_proven = any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "package_executable_reason"
        and executable_reason_alias_keys <= executable_reason_assignments(node)
        for node in ast.walk(tree)
    )
    _require(
        executable_reason_alias_assignment_proven,
        "historical_conflict_effective_field_alias_contract_changed",
    )
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    fields = {
        "packet_sidecar_hash_sha256",
        "payload_hash_sha256",
        "risk_authority_packet_hash_sha256",
        "risk_finalizer_stale_surface_conflicts",
    }
    occurrences: Counter[str] = Counter()
    decision_consumers: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or node.value not in fields:
            continue
        field = str(node.value)
        occurrences[field] += 1
        current: ast.AST | None = node
        while current is not None:
            owner = parents.get(current)
            if isinstance(owner, ast.Compare):
                decision_consumers[field] += 1
                break
            if isinstance(owner, (ast.If, ast.While, ast.IfExp)) and getattr(
                owner, "test", None
            ) is current:
                decision_consumers[field] += 1
                break
            current = owner
    _require(
        decision_consumers["packet_sidecar_hash_sha256"] == 0
        and decision_consumers["risk_authority_packet_hash_sha256"] == 0
        and decision_consumers["risk_finalizer_stale_surface_conflicts"] == 0
        and occurrences["risk_finalizer_stale_surface_conflicts"] == 2,
        "historical_hash_or_conflict_diagnostic_consumer_boundary_changed",
    )
    return {
        "status": "PHASE_C_HISTORICAL_HASH_ONLY_NONCAUSAL_PRODUCER_BOUND",
        "producer_path": str(producer_path.relative_to(ROOT)),
        "producer_sha256": file_sha256(producer_path),
        "prop_headroom_producer_path": str(headroom_path.relative_to(ROOT)),
        "prop_headroom_producer_sha256": file_sha256(headroom_path),
        "producer_hashes_bound_by_decision_contract": True,
        "simulated_capture_clock_source": "causal_decision_time",
        "broker_real_freshness_or_authority_consumed": False,
        "candidate_packet_hash_decision_consumer_count": 0,
        "flattened_risk_hash_decision_consumer_count": 0,
        "capped_conflict_diagnostic_decision_consumer_count": 0,
        "capped_conflict_diagnostic_ast_occurrence_count": 2,
        "capped_conflict_effective_field_alias_assignment_proven": True,
        "capped_conflict_effective_field_aliases": {
            key: list(value)
            for key, value in _CONFLICT_CANONICAL_WITNESS_ALIASES.items()
        },
        "candidate_packet_hash_ast_occurrence_count": occurrences[
            "packet_sidecar_hash_sha256"
        ],
        "candidate_packet_preimage_persistence_status": (
            "historical_compact_stack_omitted_hash_only"
        ),
        "finalizer_payload_preimage_persistence_status": (
            "historical_full_payload_truncated_after_hash"
        ),
    }


def _contract_identity_expectations(
    *,
    parent_manifest: Mapping[str, Any],
    accelerated_output_dir: Path,
    accelerated_prefix: str,
) -> dict[str, Any]:
    """Bind both predecessor and successor provenance before projecting it."""

    from src.research_infra import (
        b7_5_post_acceleration_runner as phase_c,
    )
    from src.research_infra import (
        replay_acceleration_attempt5_typed_sparse_runner as replay,
    )

    arm_id = str(parent_manifest.get("arm_id") or "")
    parent_audit, _path = _load_audit(arm_id)
    parent_binding = parent_audit.get("source_and_contract_binding")
    _require(isinstance(parent_binding, Mapping), "parent_contract_binding_missing")
    decision = json.loads(DECISION_CONTRACT_PATH.read_bytes())
    _require(isinstance(decision, dict), "successor_decision_contract_invalid")
    decision_arm = next(
        (
            row
            for row in decision.get("factorial_contract", {}).get("arms", [])
            if isinstance(row, Mapping) and row.get("arm_id") == arm_id
        ),
        None,
    )
    _require(isinstance(decision_arm, Mapping), "successor_decision_arm_missing")
    binding = replay.selection_sizing_factorial_binding_from_args(
        argparse.Namespace(
            decision_contract=DECISION_CONTRACT_PATH,
            arm_id=arm_id,
            expected_arm_fingerprint_sha256=decision_arm[
                "arm_fingerprint_sha256"
            ],
            runtime_evidence_root=replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT,
        )
    )
    _require(isinstance(binding, Mapping), "successor_factorial_binding_invalid")
    seal = phase_c.validate_execution_seal(
        EXECUTION_SEAL_PATH,
        decision_contract_path=DECISION_CONTRACT_PATH,
        arm_id=arm_id,
    )
    receipt_path = Path(accelerated_output_dir) / ARM_RECEIPT_NAME
    receipt = json.loads(receipt_path.read_bytes())
    receipt_root = receipt.get("receipt_root_sha256")
    receipt_projection = copy.deepcopy(receipt)
    receipt_projection.pop("receipt_root_sha256", None)
    arm_seal = seal["arms"][arm_id]
    inventory = receipt.get("artifact_inventory")
    inventory_projection = copy.deepcopy(inventory)
    if isinstance(inventory_projection, dict):
        inventory_projection.pop("inventory_root_sha256", None)
    expected_artifact_names = {
        f"{accelerated_prefix}{suffix}" for suffix in ROLE_SUFFIXES.values()
    }
    allowed_names = expected_artifact_names | {
        ARM_RECEIPT_NAME,
        SEMANTIC_PARITY_NAME,
    }
    observed_names = {
        path.name
        for path in Path(accelerated_output_dir).iterdir()
        if path.is_file() or path.is_symlink()
    }
    _require(
        isinstance(receipt, dict)
        and receipt_root == stable_sha256(receipt_projection)
        and receipt.get("status") == "POST_ACCELERATION_ARM_EXECUTION_COMPLETE"
        and receipt.get("arm_id") == arm_id
        and receipt.get("output_prefix") == accelerated_prefix
        and Path(str(receipt.get("namespace") or "")).resolve()
        == Path(accelerated_output_dir).resolve()
        and receipt.get("decision_contract_self_hash_sha256")
        == binding["decision_contract_sha256"]
        and receipt.get("execution_seal_root_sha256")
        == seal["execution_seal_root_sha256"]
        and receipt.get("arm_fingerprint_sha256")
        == binding["arm_fingerprint_sha256"]
        and receipt.get("shared_execution_contract_digest_sha256")
        == arm_seal["shared_execution_contract_digest_sha256"]
        and receipt.get("summary_status")
        == phase_c.COMPLETED_REPLAY_STATUS
        and isinstance(inventory, Mapping)
        and inventory.get("inventory_root_sha256")
        == stable_sha256(inventory_projection)
        and inventory.get("all_expected_artifacts_present") is True
        and inventory.get("ledger_counts_reconciled_to_completed_summary") is True
        and observed_names <= allowed_names
        and expected_artifact_names <= observed_names
        and receipt.get("prepared_pack_authority", {}).get(
            "authority_root_sha256"
        )
        == seal.get("prepared_day_pack_binding", {}).get(
            "authority_root_sha256"
        )
        and receipt.get("broker_live_authority") is False
        and receipt.get("broker_mutation_enabled") is False
        and receipt.get("real_order_transmission_possible") is False,
        "successor_arm_receipt_invalid",
    )
    inventory_artifacts = inventory.get("artifacts")
    _require(
        isinstance(inventory_artifacts, Mapping)
        and set(inventory_artifacts) == set(ROLE_SUFFIXES),
        "successor_arm_artifact_inventory_invalid",
    )
    for role, suffix in ROLE_SUFFIXES.items():
        row = inventory_artifacts.get(role)
        target = Path(accelerated_output_dir) / f"{accelerated_prefix}{suffix}"
        _require(
            isinstance(row, Mapping)
            and row.get("path") == target.name
            and target.is_file()
            and not target.is_symlink()
            and row.get("bytes") == target.stat().st_size
            and row.get("sha256") == file_sha256(target),
            f"successor_arm_artifact_inventory_invalid:{role}",
        )
        if role in JSONL_ROLES:
            _require(
                row.get("rows") == sum(1 for _ in iter_jsonl(target)),
                f"successor_arm_artifact_row_count_invalid:{role}",
            )
    parent = {
        "arm_fingerprint_sha256": parent_binding.get("arm_fingerprint_sha256"),
        "binding_payload_sha256": parent_binding.get("binding_payload_sha256"),
        "common_execution_input_digest_sha256": parent_binding.get(
            "common_execution_input_digest_sha256"
        ),
        "decision_contract_sha256": parent_binding.get(
            "decision_contract_self_hash_sha256"
        ),
    }
    successor = {
        key: binding[key]
        for key in (
            "arm_fingerprint_sha256",
            "binding_payload_sha256",
            "common_execution_input_digest_sha256",
            "decision_contract_sha256",
        )
    }
    _require(
        all(_is_sha256(value) for value in (*parent.values(), *successor.values()))
        and parent != successor,
        "contract_identity_expectations_invalid",
    )
    return {
        "arm_id": arm_id,
        "parent": parent,
        "successor": successor,
        "parent_acceptance_audit_file_sha256": AUDIT_BINDINGS[arm_id][
            "file_sha256"
        ],
        "successor_decision_contract_file_sha256": file_sha256(
            DECISION_CONTRACT_PATH
        ),
        "successor_execution_seal_root_sha256": seal[
            "execution_seal_root_sha256"
        ],
        "successor_arm_receipt_root_sha256": receipt_root,
        "values_independently_bound_before_projection": True,
    }


_CONFLICT_CANONICAL_SOURCES = frozenset(
    {
        "scheduler_decision_inputs",
        "package_probe_quality",
        "scheduler_option",
        "candidate",
        "packets",
        "valid_package_new_entry_authority",
        "verified_immutable_signed_execution_payload",
        "atomic_execution_fillability_tuple",
    }
)
_CONFLICT_STALE_SOURCES = frozenset(
    {
        "legacy_finalizer_merge",
        "scheduler_decision_inputs",
        "package_probe_quality",
        "scheduler_option",
        "candidate",
        "packets",
        "priority_surface_first_present",
        "mutable_execution_consumer_projection",
    }
)
_CONFLICT_CANONICAL_WITNESS_ALIASES = {
    "replay_candidate_use_allowed_now_reason": (
        "package_replay_executable_candidate_use_allowed_reason",
    ),
}


def _finalizer_conflict_diag_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return f"<mapping:{len(value)}>"
    if isinstance(value, (list, tuple, set)):
        return f"<sequence:{len(value)}>"
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _validate_capped_conflict_diagnostic(
    container: Mapping[str, Any],
    conflicts: Any,
    *,
    canonical_witness_index: Mapping[str, set[Any]],
    canonical_conflict_reachability: Mapping[str, list[Any]],
) -> dict[str, int]:
    count = container.get("risk_finalizer_stale_surface_conflict_count")
    keys = container.get("risk_finalizer_stale_surface_conflict_keys")
    _require(
        isinstance(conflicts, list)
        and all(isinstance(row, Mapping) for row in conflicts)
        and type(count) is int
        and count > 0
        and len(conflicts) == min(count, 32)
        and isinstance(keys, list)
        and keys == sorted(set(keys))
        and all(isinstance(key, str) and key for key in keys),
        "capped_conflict_diagnostic_invalid",
    )
    observed: set[bytes] = set()
    chain_connected_count = 0
    truncated_disconnected_count = 0

    def values_match(left: Any, right: Any) -> bool:
        if left == right:
            return True
        if (
            isinstance(left, (int, float))
            and not isinstance(left, bool)
            and isinstance(right, (int, float))
            and not isinstance(right, bool)
        ):
            return abs(float(left) - float(right)) <= 5e-9
        return False

    for index, row in enumerate(conflicts):
        _require(
            set(row)
            == {
                "key",
                "canonical_source",
                "stale_source",
                "canonical_value",
                "stale_value",
            }
            and isinstance(row.get("key"), str)
            and row["key"] in keys
            and row.get("canonical_source") in _CONFLICT_CANONICAL_SOURCES
            and row.get("stale_source") in _CONFLICT_STALE_SOURCES,
            f"capped_conflict_tuple_invalid:{index}",
        )
        encoded = canonical_bytes(row)
        _require(
            encoded not in observed,
            f"capped_conflict_tuple_duplicate:{index}",
        )
        observed.add(encoded)
        reachable = canonical_conflict_reachability.get(row["key"], [])
        chain_connected = any(
            values_match(endpoint, known)
            for endpoint in (
                row.get("canonical_value"),
                row.get("stale_value"),
            )
            for known in reachable
        )
        truncated_disconnected = bool(
            not chain_connected
            and len(conflicts) == 32
            and isinstance(count, int)
            and count > len(conflicts)
        )
        _require(
            bool(canonical_witness_index.get(row["key"], set()))
            and (chain_connected or truncated_disconnected),
            f"capped_conflict_canonical_value_mismatch:{row['key']}",
        )
        if chain_connected:
            chain_connected_count += 1
        else:
            truncated_disconnected_count += 1
    return {
        "tuple_count": len(conflicts),
        "chain_connected_tuple_count": chain_connected_count,
        "truncated_disconnected_tuple_count": truncated_disconnected_count,
    }


def _canonical_field_witness_index(value: Any) -> dict[str, set[Any]]:
    index: dict[str, set[Any]] = {}

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for raw_key, child in item.items():
                key = str(raw_key)
                if key.startswith("risk_finalizer_stale_surface_conflict"):
                    continue
                index.setdefault(key, set()).add(
                    _finalizer_conflict_diag_value(child)
                )
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    for canonical_key, aliases in _CONFLICT_CANONICAL_WITNESS_ALIASES.items():
        for alias in aliases:
            index.setdefault(canonical_key, set()).update(index.get(alias, set()))
    return index


def _canonical_conflict_reachability(
    value: Any,
    *,
    witness_index: Mapping[str, set[Any]],
) -> dict[str, list[Any]]:
    edges: dict[str, list[tuple[Any, Any]]] = {}

    def collect(item: Any) -> None:
        if isinstance(item, Mapping):
            conflicts = item.get("risk_finalizer_stale_surface_conflicts")
            if isinstance(conflicts, list):
                for row in conflicts:
                    if isinstance(row, Mapping) and isinstance(
                        row.get("key"), str
                    ):
                        edges.setdefault(row["key"], []).append(
                            (
                                row.get("canonical_value"),
                                row.get("stale_value"),
                            )
                        )
            for child in item.values():
                collect(child)
        elif isinstance(item, list):
            for child in item:
                collect(child)

    def values_match(left: Any, right: Any) -> bool:
        if left == right:
            return True
        return bool(
            isinstance(left, (int, float))
            and not isinstance(left, bool)
            and isinstance(right, (int, float))
            and not isinstance(right, bool)
            and abs(float(left) - float(right)) <= 5e-9
        )

    collect(value)
    result: dict[str, list[Any]] = {}
    for key, key_edges in edges.items():
        witnesses = witness_index.get(key, set())
        reachable = [
            endpoint
            for edge in key_edges
            for endpoint in edge
            if any(values_match(endpoint, witness) for witness in witnesses)
        ]
        changed = True
        while changed:
            changed = False
            for edge in key_edges:
                if any(
                    values_match(endpoint, known)
                    for endpoint in edge
                    for known in reachable
                ):
                    for endpoint in edge:
                        if not any(
                            values_match(endpoint, known) for known in reachable
                        ):
                            reachable.append(endpoint)
                            changed = True
        result[key] = reachable
    return result


def _project_phase_c_row(
    value: Any,
    *,
    role: str,
    side_expectations: Mapping[str, str],
    observed: Counter[str],
    path: tuple[str, ...] = (),
    inside_factorial_binding: bool = False,
    root_row: Mapping[str, Any] | None = None,
    canonical_witness_index: Mapping[str, set[Any]] | None = None,
    canonical_conflict_reachability: Mapping[str, list[Any]] | None = None,
) -> Any:
    if root_row is None and isinstance(value, Mapping):
        root_row = value
        canonical_witness_index = _canonical_field_witness_index(value)
        canonical_conflict_reachability = _canonical_conflict_reachability(
            value,
            witness_index=canonical_witness_index,
        )
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        binding_scope = inside_factorial_binding or (
            "b7_5_selection_sizing_factorial_binding" in path
        )
        for raw_key, item in value.items():
            key = str(raw_key)
            next_path = (*path, key)
            identity_key: str | None = None
            if not path and key in _TOP_LEVEL_CONTRACT_IDENTITIES:
                identity_key = _TOP_LEVEL_CONTRACT_IDENTITIES[key]
            elif binding_scope and key in _NESTED_CONTRACT_IDENTITIES:
                identity_key = key
            if identity_key is not None:
                _require(
                    item == side_expectations[identity_key],
                    "unbound_contract_identity:" + "/".join(next_path),
                )
                result[key] = CONTRACT_IDENTITY_SENTINEL
                observed["contract_identity:" + "/".join(next_path)] += 1
                continue
            if key == "risk_finalizer_stale_surface_conflicts":
                _require(role == "scorecard", "capped_diagnostic_outside_scorecard")
                _require(
                    isinstance(root_row, Mapping)
                    and isinstance(canonical_witness_index, Mapping),
                    # The reachability graph is built once from the complete
                    # persisted scorecard row, not one capped copy at a time.
                    "capped_conflict_root_row_invalid",
                )
                _require(
                    isinstance(canonical_conflict_reachability, Mapping),
                    "capped_conflict_root_row_invalid",
                )
                conflict_observation = _validate_capped_conflict_diagnostic(
                    value,
                    item,
                    canonical_witness_index=canonical_witness_index,
                    canonical_conflict_reachability=(
                        canonical_conflict_reachability
                    ),
                )
                result[key] = CAPPED_DIAGNOSTIC_SENTINEL
                observed["capped_conflict_diagnostic"] += 1
                for observation_key, observation_count in (
                    conflict_observation.items()
                ):
                    observed[
                        f"capped_conflict_diagnostic:{observation_key}"
                    ] += observation_count
                continue
            result[key] = _project_phase_c_row(
                item,
                role=role,
                side_expectations=side_expectations,
                observed=observed,
                path=next_path,
                inside_factorial_binding=(
                    binding_scope
                    or key == "b7_5_selection_sizing_factorial_binding"
                ),
                root_row=root_row,
                canonical_witness_index=canonical_witness_index,
                canonical_conflict_reachability=(
                    canonical_conflict_reachability
                ),
            )
        return result
    if isinstance(value, list):
        return [
            _project_phase_c_row(
                item,
                role=role,
                side_expectations=side_expectations,
                observed=observed,
                path=(*path, str(index)),
                inside_factorial_binding=inside_factorial_binding,
                root_row=root_row,
                canonical_witness_index=canonical_witness_index,
                canonical_conflict_reachability=(
                    canonical_conflict_reachability
                ),
            )
            for index, item in enumerate(value)
        ]
    return value


def _project_source_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    side: str,
    expectations: Mapping[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _require(side in {"parent", "successor"}, "source_projection_side_invalid")
    projected: list[dict[str, Any]] = []
    observed: Counter[str] = Counter()
    overlap_keys: set[tuple[str, str]] = set()
    selected_keys: set[tuple[str, str]] = set()
    raw_count = 0
    for raw_count, raw in enumerate(rows, start=1):
        _require(isinstance(raw, Mapping), "source_projection_row_invalid")
        row = _project_phase_c_row(
            raw,
            role="source",
            side_expectations=expectations,
            observed=observed,
        )
        row_type = str(row.get("row_type") or "")
        key = (str(row.get("symbol") or ""), str(row.get("trading_day") or ""))
        if row_type == _SOURCE_OVERLAP_ROW_TYPE:
            _require(
                side == "parent"
                and all(key)
                and key not in overlap_keys
                and row.get("status") == "m1_source_overlap_consistent"
                and row.get("timeframe") == "M1"
                and row.get("evidence_class")
                == "source_bound_asof_timewarp_decision_input"
                and row.get("source_truth_scope")
                == "ordered_price_path_only_not_broker_order_lifecycle_truth"
                and isinstance(row.get("candidate_source_paths"), list)
                and len(row["candidate_source_paths"]) == 2
                and row.get("source_path") in row["candidate_source_paths"]
                and _is_sha256(row.get("candidate_day_sha256"))
                and row.get("live_broker_authority") is False
                and row.get("broker_mutation_enabled") is False,
                "source_overlap_diagnostic_invalid",
            )
            overlap_keys.add(key)
            observed["parent_overlap_diagnostic_row"] += 1
            continue
        if row_type == _SOURCE_SELECTED_M1_ROW_TYPE:
            expected_count = 2 if side == "parent" else 1
            _require(
                all(key)
                and key not in selected_keys
                and row.get("candidate_source_count") == expected_count
                and row.get("populated_candidate_source_count") == expected_count
                and row.get("source_overlap_consistent") is True,
                "source_discovery_count_contract_invalid",
            )
            selected_keys.add(key)
            row["candidate_source_count"] = SOURCE_DISCOVERY_COUNT_SENTINEL
            row["populated_candidate_source_count"] = SOURCE_DISCOVERY_COUNT_SENTINEL
            observed["source_discovery_candidate_count"] += 2
        projected.append(row)
    _require(
        len(selected_keys) == _JUNE_EXPECTED_SYMBOL_COUNT
        and (
            overlap_keys == selected_keys
            if side == "parent"
            else not overlap_keys
        )
        and all(
            observed[f"contract_identity:{field}"] == raw_count
            for field in _TOP_LEVEL_CONTRACT_IDENTITIES
        ),
        "source_projection_inventory_invalid",
    )
    return projected, {
        "side": side,
        "raw_row_count": raw_count,
        "projected_row_count": len(projected),
        "selected_m1_symbol_day_count": len(selected_keys),
        "excluded_overlap_diagnostic_row_count": len(overlap_keys),
        "observed_projection_paths": dict(sorted(observed.items())),
    }


def _project_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    role: str,
    expectations: Mapping[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    observed: Counter[str] = Counter()
    projected: list[dict[str, Any]] = []
    row_count = 0
    for index, row in enumerate(rows):
        row_count += 1
        if role in {"order", "trade"}:
            try:
                semantic._validate_runtime_hash_preimages(
                    role, row, row_index=index
                )
            except semantic.SemanticAcceptanceError as exc:
                raise PhaseCSemanticError(str(exc)) from exc
        projected.append(
            _project_phase_c_row(
                row,
                role=role,
                side_expectations=expectations,
                observed=observed,
            )
        )
    _require(
        all(
            observed[f"contract_identity:{field}"] == row_count
            for field in _TOP_LEVEL_CONTRACT_IDENTITIES
        ),
        f"contract_identity_row_coverage_invalid:{role}",
    )
    return projected, dict(sorted(observed.items()))


def _phase_c_add_hash_owner(
    target: dict[str, str],
    *,
    key: str,
    value: Any,
    label: str,
) -> None:
    _require(_is_sha256(value), f"hash_closure_value_invalid:{label}:{key}")
    previous = target.get(key)
    _require(
        previous is None or previous == value,
        f"hash_closure_alias_conflict:{label}:{key}",
    )
    target[key] = str(value)


def _collect_phase_c_hash_alias_state(
    rows_by_role: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    side: str,
) -> dict[str, Any]:
    """Authenticate all persisted derived-hash aliases by candidate identity."""

    _require(side in {"parent", "successor"}, "hash_closure_side_invalid")
    packet: dict[str, dict[str, str]] = {
        role: {} for role in ("missed", "order", "trade", "oracle")
    }
    risk: dict[str, dict[str, str]] = {
        role: {} for role in ("missed", "order", "trade", "oracle")
    }
    probe: dict[str, str] = {}
    selected_probe: dict[str, str] = {}
    primary_probe: dict[str, str] = {}
    order_probe: dict[str, str] = {}
    missed_meta: dict[str, dict[str, Any]] = {}
    evaluated_missed_keys: set[str] = set()
    probe_caps_by_window: dict[str, dict[str, int]] = {}
    finalizer_payload_hash_count = 0
    scorecard_count = 0
    raw_preimages_by_role = {"order": 0, "trade": 0}

    for role in packet:
        for index, row in enumerate(rows_by_role.get(role, ())):
            _require(isinstance(row, Mapping), f"hash_closure_row_invalid:{role}")
            try:
                key = semantic._identity_key(row, label=f"{side}:{role}")
                if role in {"order", "trade"}:
                    semantic._validate_runtime_hash_preimages(
                        role, row, row_index=index
                    )
                    raw_preimages_by_role[role] += 1
            except semantic.SemanticAcceptanceError as exc:
                raise PhaseCSemanticError(str(exc)) from exc
            packet_hash = row.get(
                "candidate_packet_sidecar_hash_sha256",
                row.get("packet_sidecar_hash_sha256"),
            )
            _phase_c_add_hash_owner(
                packet[role],
                key=key,
                value=packet_hash,
                label=f"{side}:{role}:packet",
            )
            risk_hash = row.get("risk_authority_packet_hash_sha256")
            if risk_hash is not None:
                _phase_c_add_hash_owner(
                    risk[role],
                    key=key,
                    value=risk_hash,
                    label=f"{side}:{role}:risk",
                )
            if role == "missed":
                missed_meta[key] = {
                    "trading_day": row.get("trading_day"),
                    "decision_window_id": row.get("decision_window_id"),
                    "risk_finalizer_rank": row.get("risk_finalizer_rank"),
                    "risk_authority": row.get("risk_authority"),
                    "risk_authority_status": row.get("risk_authority_status"),
                    "risk_decision": row.get("risk_decision"),
                }
                if row.get("risk_decision") != "risk_probe_materialized":
                    evaluated_missed_keys.add(key)
            if role == "order":
                nested = row.get("risk_authority")
                nested = nested if isinstance(nested, Mapping) else {}
                probe_hash = nested.get(
                    "risk_finalizer_probe_packet_hash_sha256"
                )
                if probe_hash is not None:
                    _phase_c_add_hash_owner(
                        order_probe,
                        key=key,
                        value=probe_hash,
                        label=f"{side}:order:probe",
                    )

    for row in rows_by_role.get("scorecard", ()):
        _require(isinstance(row, Mapping), "hash_closure_row_invalid:scorecard")
        scorecard_count += 1
        finalizer = row.get("risk_admitted_scheduler_finalizer")
        if not isinstance(finalizer, Mapping):
            continue
        decision_window_id = row.get("decision_window_id")
        preserved_count = finalizer.get("probe_rows_preserved_count")
        total_count = finalizer.get("probe_rows_total_count")
        if (
            isinstance(decision_window_id, str)
            and type(preserved_count) is int
            and type(total_count) is int
        ):
            cap = {
                "preserved_count": preserved_count,
                "total_count": total_count,
            }
            previous = probe_caps_by_window.get(decision_window_id)
            _require(
                previous is None or previous == cap,
                f"finalizer_probe_cap_conflict:{decision_window_id}",
            )
            probe_caps_by_window[decision_window_id] = cap
        payload_hash = finalizer.get("payload_hash_sha256")
        if payload_hash is not None:
            _require(
                _is_sha256(payload_hash)
                and finalizer.get("payload_compacted_for_broad_replay") is True
                and type(preserved_count) is int
                and type(total_count) is int
                and 0 <= preserved_count <= total_count,
                "finalizer_compact_hash_closure_invalid",
            )
            finalizer_payload_hash_count += 1
        for field, target in (
            ("probe_rows", probe),
            ("selected_probe_rows", selected_probe),
        ):
            rows = finalizer.get(field) or []
            _require(
                isinstance(rows, list)
                and all(isinstance(probe_row, Mapping) for probe_row in rows),
                "finalizer_probe_inventory_invalid",
            )
            local: set[str] = set()
            for probe_row in rows:
                try:
                    key = semantic._identity_key(
                        probe_row, label=f"{side}:scorecard:{field}"
                    )
                except semantic.SemanticAcceptanceError as exc:
                    raise PhaseCSemanticError(str(exc)) from exc
                _require(
                    key not in local,
                    f"finalizer_probe_identity_duplicate:{field}:{key}",
                )
                local.add(key)
                _phase_c_add_hash_owner(
                    target,
                    key=key,
                    value=probe_row.get(
                        "risk_authority_packet_hash_sha256"
                    ),
                    label=f"{side}:scorecard:{field}",
                )
        primary_hash = row.get(
            "finalizer_primary_probe_risk_authority_packet_hash_sha256"
        )
        if primary_hash is not None:
            try:
                key = semantic._identity_key(
                    {
                        "canonical_replay_candidate_instance_key": row.get(
                            "finalizer_primary_probe_canonical_replay_candidate_instance_key"
                        ),
                        "candidate_id": row.get(
                            "finalizer_primary_probe_candidate_id"
                        ),
                        "decision_time_utc": row.get(
                            "finalizer_primary_probe_decision_time_utc"
                        ),
                    },
                    label=f"{side}:scorecard:primary_probe",
                )
            except semantic.SemanticAcceptanceError as exc:
                raise PhaseCSemanticError(str(exc)) from exc
            _phase_c_add_hash_owner(
                primary_probe,
                key=key,
                value=primary_hash,
                label=f"{side}:scorecard:primary_probe",
            )

    for key, value in selected_probe.items():
        _require(
            probe.get(key) == value,
            f"selected_probe_hash_alias_mismatch:{key}",
        )
    for key, value in primary_probe.items():
        terminal_value = risk["missed"].get(key) or risk["order"].get(key)
        _require(
            probe.get(key) == value or terminal_value == value,
            f"primary_probe_hash_alias_mismatch:{key}",
        )
    for key, value in order_probe.items():
        _require(
            probe.get(key) == value,
            f"order_probe_hash_alias_mismatch:{key}",
        )

    selected_keys = set(packet["order"])
    _require(
        set(packet["trade"]) == selected_keys
        and set(packet["oracle"]) == selected_keys
        and not (selected_keys & set(packet["missed"])),
        "candidate_terminal_partition_invalid",
    )
    for key in selected_keys:
        _require(
            packet["order"][key]
            == packet["trade"][key]
            == packet["oracle"][key],
            f"candidate_packet_alias_mismatch:{key}",
        )
        _require(
            risk["order"].get(key)
            == risk["trade"].get(key)
            == risk["oracle"].get(key),
            f"selected_risk_alias_mismatch:{key}",
        )
    return {
        "packet": packet,
        "risk": risk,
        "probe": probe,
        "selected_probe": selected_probe,
        "primary_probe": primary_probe,
        "order_probe": order_probe,
        "missed_meta": missed_meta,
        "evaluated_missed_keys": evaluated_missed_keys,
        "probe_caps_by_window": probe_caps_by_window,
        "candidate_terminal_identity_count": len(packet["missed"])
        + len(selected_keys),
        "missed_identity_count": len(packet["missed"]),
        "selected_identity_count": len(selected_keys),
        "scorecard_count": scorecard_count,
        "finalizer_payload_hash_count": finalizer_payload_hash_count,
        "raw_preimages_by_role": raw_preimages_by_role,
    }


def validate_phase_c_hash_closure(
    *,
    parent_artifacts: Mapping[str, Mapping[str, Any]],
    successor_artifacts: Mapping[str, Path],
) -> dict[str, Any]:
    """Validate identity partitions and every non-local derived-hash family."""

    roles = ("missed", "order", "trade", "oracle", "scorecard")
    parent_rows = {
        role: iter_jsonl(Path(str(parent_artifacts[role]["resolved_path"])))
        for role in roles
    }
    successor_rows = {
        role: iter_jsonl(successor_artifacts[role]) for role in roles
    }
    parent = _collect_phase_c_hash_alias_state(parent_rows, side="parent")
    successor = _collect_phase_c_hash_alias_state(
        successor_rows, side="successor"
    )
    for field in (
        "candidate_terminal_identity_count",
        "missed_identity_count",
        "selected_identity_count",
        "scorecard_count",
        "finalizer_payload_hash_count",
    ):
        _require(
            parent[field] == successor[field],
            f"hash_closure_count_mismatch:{field}",
        )
    for role in parent["packet"]:
        _require(
            set(parent["packet"][role]) == set(successor["packet"][role]),
            f"candidate_terminal_identity_set_mismatch:{role}",
        )
    _require(
        set(parent["probe"]) == set(successor["probe"]),
        "finalizer_probe_identity_set_mismatch",
    )
    changed_missed_risk = {
        key
        for key, value in parent["risk"]["missed"].items()
        if successor["risk"]["missed"].get(key) != value
    }
    _require(
        changed_missed_risk == parent["evaluated_missed_keys"]
        == successor["evaluated_missed_keys"],
        "missed_risk_evaluated_partition_mismatch",
    )
    aliased: set[str] = set()
    omitted: set[str] = set()
    for key in changed_missed_risk:
        _require(
            parent["missed_meta"].get(key) == successor["missed_meta"].get(key),
            f"missed_risk_row_projection_mismatch:{key}",
        )
        if (
            parent["probe"].get(key) == parent["risk"]["missed"].get(key)
            and successor["probe"].get(key)
            == successor["risk"]["missed"].get(key)
        ):
            aliased.add(key)
            continue
        _require(
            key not in parent["probe"] and key not in successor["probe"],
            f"missed_risk_probe_alias_mismatch:{key}",
        )
        meta = parent["missed_meta"][key]
        window_id = meta.get("decision_window_id")
        rank = meta.get("risk_finalizer_rank")
        parent_cap = parent["probe_caps_by_window"].get(window_id)
        successor_cap = successor["probe_caps_by_window"].get(window_id)
        _require(
            meta.get("risk_authority")
            == "timewarp_v4_runtime_risk_authority_v1"
            and meta.get("risk_authority_status")
            == "pre_scheduler_risk_authority_materialized"
            and type(rank) is int
            and isinstance(parent_cap, Mapping)
            and parent_cap == successor_cap
            and rank > parent_cap["preserved_count"]
            and rank <= parent_cap["total_count"],
            f"missed_risk_probe_omission_not_deterministic:{key}",
        )
        omitted.add(key)
    historical = _phase_c_historical_hash_noncausal_contract()
    terminal_identities = set().union(
        *(set(parent["packet"][role]) for role in parent["packet"])
    )
    proof_classes = dict(_derived_hash_proofs())
    for pattern in (
        "candidate_packet_sidecar_hash_sha256",
        "packet_sidecar_hash_sha256",
    ):
        proof_classes[pattern] = {
            key: "HISTORICAL_HASH_ONLY_NONCAUSAL"
            for key in terminal_identities
        }
    proof_classes["oracle:risk_authority_packet_hash_sha256"] = {
        key: "IDENTITY_ALIAS" for key in parent["packet"]["oracle"]
    }
    proof_classes["missed:risk_authority_packet_hash_sha256"] = {
        key: "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH"
        for key in changed_missed_risk
    }
    core = {
        "status": "PHASE_C_DERIVED_HASH_IDENTITY_CLOSURE_VALID",
        "proof_classes": proof_classes,
        "historical_hash_only_noncausal_contract": historical,
        "candidate_terminal_identity_count": parent[
            "candidate_terminal_identity_count"
        ],
        "missed_identity_count": parent["missed_identity_count"],
        "selected_identity_count": parent["selected_identity_count"],
        "scorecard_count": parent["scorecard_count"],
        "finalizer_payload_hash_count": parent[
            "finalizer_payload_hash_count"
        ],
        "changed_missed_risk_identity_count": len(changed_missed_risk),
        "changed_missed_risk_probe_alias_count": len(aliased),
        "changed_missed_risk_deterministically_omitted_count": len(omitted),
        "changed_missed_risk_identity_root_sha256": stable_sha256(
            sorted(changed_missed_risk)
        ),
        "raw_preimages_validated_by_role": {
            "parent": parent["raw_preimages_by_role"],
            "successor": successor["raw_preimages_by_role"],
        },
        "identity_cross_ledger_closure_validated_roles": [
            "scorecard",
            "oracle",
            "missed",
        ],
    }
    return {**core, "closure_root_sha256": stable_sha256(core)}


def _compare_prevalidated_rows(
    role: str,
    reference_rows: Iterable[Mapping[str, Any]],
    accelerated_rows: Iterable[Mapping[str, Any]],
    *,
    derived_hash_proofs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Task-2 comparator logic after raw hash preimages were authenticated."""

    sentinel = object()
    projected = semantic._ArrayRoot()
    raw_reference = semantic._ArrayRoot()
    raw_accelerated = semantic._ArrayRoot()
    observed: Counter[str] = Counter()
    observed_proof_classes: Counter[str] = Counter()
    mismatched_rows = 0
    excluded_count = 0
    for index, pair in enumerate(
        zip_longest(reference_rows, accelerated_rows, fillvalue=sentinel)
    ):
        reference, accelerated = pair
        _require(
            reference is not sentinel and accelerated is not sentinel,
            f"semantic_row_count_mismatch:{role}",
        )
        _require(
            isinstance(reference, Mapping) and isinstance(accelerated, Mapping),
            f"semantic_row_not_mapping:{role}:{index}",
        )
        raw_reference.update(reference)
        raw_accelerated.update(accelerated)
        differences = semantic._difference_paths(reference, accelerated)
        mismatched_rows += bool(differences)
        if role in semantic.EXACT_ROLES and differences:
            raise PhaseCSemanticError(f"semantic_row_mismatch:{role}:{index}")
        left = copy.deepcopy(dict(reference))
        right = copy.deepcopy(dict(accelerated))
        for path in differences:
            entry = semantic._entry_for_path(role, path)
            if entry is None:
                raise PhaseCSemanticError(
                    f"semantic_row_mismatch:{role}:{index}:{'/'.join(path)}"
                )
            left_value = semantic._path_value(reference, path)
            right_value = semantic._path_value(accelerated, path)
            if entry["value_class"] == "wall_clock_timestamp":
                _require(
                    semantic._is_utc_timestamp(left_value)
                    and semantic._is_utc_timestamp(right_value),
                    f"volatile_timestamp_invalid:{role}:{index}",
                )
                replacement = semantic.RUNTIME_SENTINEL
            else:
                _require(
                    _is_sha256(left_value) and _is_sha256(right_value),
                    f"derived_hash_invalid:{role}:{index}",
                )
                pattern = "/".join(entry["path"])
                if pattern in semantic._LOCAL_PREIMAGE_DERIVED_PATTERNS:
                    proof_class: Any = "PREIMAGE"
                elif (
                    pattern == "risk_authority_packet_hash_sha256"
                    and role in {"order", "trade"}
                    and isinstance(reference.get("risk_authority"), Mapping)
                    and isinstance(accelerated.get("risk_authority"), Mapping)
                ):
                    proof_class = "PREIMAGE"
                else:
                    proof_class = (derived_hash_proofs or {}).get(
                        f"{role}:{pattern}",
                        (derived_hash_proofs or {}).get(pattern),
                    )
                    if isinstance(proof_class, Mapping):
                        reference_identity = semantic._identity_key(
                            reference, label=f"{role}:reference:{index}"
                        )
                        accelerated_identity = semantic._identity_key(
                            accelerated, label=f"{role}:accelerated:{index}"
                        )
                        _require(
                            reference_identity == accelerated_identity,
                            f"derived_hash_identity_mismatch:{role}:{index}:{pattern}",
                        )
                        proof_class = proof_class.get(reference_identity)
                _require(
                    proof_class
                    in {
                        "PREIMAGE",
                        "IDENTITY_ALIAS",
                        "HISTORICAL_HASH_ONLY_NONCAUSAL",
                        "TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH",
                    },
                    f"derived_hash_closure_unproven:{role}:{index}:{pattern}",
                )
                observed_proof_classes[str(proof_class)] += 1
                replacement = semantic.HASH_SENTINEL
            semantic._set_path(left, path, replacement)
            semantic._set_path(right, path, replacement)
            observed["/".join(entry["path"])] += 1
            excluded_count += 1
        _require(
            canonical_bytes(left) == canonical_bytes(right),
            f"semantic_projection_mismatch:{role}:{index}",
        )
        projected.update(left)
    return {
        "role": role,
        "status": "SEMANTICALLY_EQUIVALENT",
        "row_count": projected.count,
        "ordered_semantic_projection_root_sha256": projected.hexdigest(),
        "phase_c_projected_reference_root_sha256": raw_reference.hexdigest(),
        "phase_c_projected_accelerated_root_sha256": raw_accelerated.hexdigest(),
        "projected_rows_with_allowlisted_runtime_differences": mismatched_rows,
        "excluded_volatile_difference_count": excluded_count,
        "observed_allowlisted_paths": dict(sorted(observed.items())),
        "observed_derived_hash_proof_classes": dict(
            sorted(observed_proof_classes.items())
        ),
        "raw_runtime_hash_preimages_validated_before_phase_c_projection": (
            role in {"order", "trade"}
        ),
        "identity_cross_ledger_hash_closure_required": role
        in {"scorecard", "oracle", "missed"},
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "economic_values_exposed": False,
    }


def compare_parent_roles(
    *,
    parent_manifest: Mapping[str, Any],
    accelerated_output_dir: Path,
    accelerated_prefix: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compare every ordered ledger row with the Task-2 explicit allowlist."""

    artifacts = parent_manifest.get("artifacts")
    _require(isinstance(artifacts, Mapping), "parent_manifest_artifacts_invalid")
    accelerated = accelerated_artifact_paths(
        accelerated_output_dir, accelerated_prefix
    )
    hash_closure = validate_phase_c_hash_closure(
        parent_artifacts=artifacts,
        successor_artifacts=accelerated,
    )
    derived_hash_proofs = hash_closure["proof_classes"]
    identities = _contract_identity_expectations(
        parent_manifest=parent_manifest,
        accelerated_output_dir=accelerated_output_dir,
        accelerated_prefix=accelerated_prefix,
    )
    producer_source = (
        ROOT / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    ).read_text(encoding="utf-8")
    _require(
        producer_source.count('"risk_finalizer_stale_surface_conflicts"') == 2
        and '.get("risk_finalizer_stale_surface_conflicts"' not in producer_source,
        "capped_conflict_diagnostic_consumer_boundary_changed",
    )
    comparisons: list[dict[str, Any]] = []
    projection_observations: dict[str, Any] = {}
    for role in JSONL_ROLES:
        parent = artifacts.get(role)
        _require(isinstance(parent, Mapping), f"parent_manifest_role_missing:{role}")
        target = accelerated[role]
        _require(target.is_file() and not target.is_symlink(), f"accelerated_role_missing:{role}")
        if role == "comparison":
            _require(
                int(parent.get("rows") or 0) == 0
                and int(parent.get("bytes") or 0) == 0
                and target.stat().st_size == 0
                and file_sha256(target)
                == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "comparison_ledger_not_exactly_empty",
            )
            result = {
                "role": role,
                "status": "EXACT_EMPTY_LEDGER_EQUIVALENT",
                "row_count": 0,
                "ordered_semantic_projection_root_sha256": stable_sha256([]),
                "meaningful_difference_count": 0,
                "unknown_difference_count": 0,
                "economic_values_exposed": False,
            }
            projection_observations[role] = {"exact_empty_ledger": True}
        elif role == "source":
            left, left_observation = _project_source_rows(
                iter_jsonl(Path(str(parent["resolved_path"]))),
                side="parent",
                expectations=identities["parent"],
            )
            right, right_observation = _project_source_rows(
                iter_jsonl(target),
                side="successor",
                expectations=identities["successor"],
            )
            _require(
                {
                    (row.get("symbol"), row.get("trading_day"))
                    for row in left
                    if row.get("row_type") == _SOURCE_SELECTED_M1_ROW_TYPE
                }
                == {
                    (row.get("symbol"), row.get("trading_day"))
                    for row in right
                    if row.get("row_type") == _SOURCE_SELECTED_M1_ROW_TYPE
                },
                "source_selected_membership_mismatch",
            )
            result = _compare_prevalidated_rows(
                role,
                left,
                right,
                derived_hash_proofs=derived_hash_proofs,
            )
            projection_observations[role] = {
                "parent": left_observation,
                "successor": right_observation,
                "selected_source_membership_exact": True,
            }
        else:
            left, left_observation = _project_rows(
                iter_jsonl(Path(str(parent["resolved_path"]))),
                role=role,
                expectations=identities["parent"],
            )
            right, right_observation = _project_rows(
                iter_jsonl(target),
                role=role,
                expectations=identities["successor"],
            )
            result = _compare_prevalidated_rows(
                role,
                left,
                right,
                derived_hash_proofs=derived_hash_proofs,
            )
            projection_observations[role] = {
                "parent": left_observation,
                "successor": right_observation,
            }
        expected_rows = int(parent.get("rows") or 0)
        if role == "source":
            expected_rows -= int(
                projection_observations[role]["parent"][
                    "excluded_overlap_diagnostic_row_count"
                ]
            )
        _require(
            int(result["row_count"]) == expected_rows,
            f"parent_row_count_binding_mismatch:{role}",
        )
        result["parent_raw_artifact"] = {
            "rows": int(parent.get("rows") or 0),
            "bytes": int(parent.get("bytes") or 0),
            "sha256": parent.get("sha256"),
        }
        result["successor_raw_artifact"] = {
            "rows": sum(1 for _ in iter_jsonl(target)),
            "bytes": target.stat().st_size,
            "sha256": file_sha256(target),
        }
        comparisons.append(result)
    return comparisons, {
        "contract_identity_bindings": identities,
        "projection_rationales": copy.deepcopy(PHASE_C_PROJECTION_RATIONALES),
        "projection_observations": projection_observations,
        "derived_hash_closure": {
            key: value
            for key, value in hash_closure.items()
            if key != "proof_classes"
        },
        "capped_conflict_diagnostic_producer_occurrence_count": 2,
        "capped_conflict_diagnostic_decision_consumer_count": 0,
    }


SUMMARY_SEMANTIC_FIELDS = (
    "active_replay_symbol_count",
    "active_replay_symbol_universe",
    "b7_5_selection_sizing_factorial_risk_lifecycle",
    "broker_mutation_enabled",
    "bucket_rows",
    "candidate_cost_r_formula_authority",
    "candidate_cost_r_formula_use",
    "candidate_generation_authority",
    "candidate_index_ledger_omitted",
    "candidate_ledger_omitted",
    "candidate_rows",
    "configured_symbol_count",
    "configured_symbol_universe",
    "cost_authority",
    "cost_authority_sources",
    "coverage_status",
    "date_end",
    "date_start",
    "days_by_split",
    "ledger_write_row_counts",
    "live_broker_authority",
    "missed_opportunity_rows",
    "oracle_rows",
    "order_rows",
    "order_send_attempts",
    "profile_count",
    "profiles",
    "risk_admitted_scheduler_finalizer_evidence",
    "scorecard_rows",
    "selected_day_count",
    "source_universe_rows",
    "split_profile_stats",
    "symbol_count",
    "symbol_universe",
    "terminal_execution_materialization_status",
    "terminal_execution_materialized",
    "trade_rows",
)

SUMMARY_SUCCESSOR_ONLY_FIELDS = frozenset(
    {
        "campaign_exact_cache_profiles",
        "compact_event_sink_checkpoints",
        "compact_event_sink_enabled",
        "engineering_stop_after_day",
        "engineering_stop_is_acceptance_gate",
        "prepared_day_pack_build_receipts",
        "prepared_day_pack_checkpoints",
        "prepared_day_pack_enabled",
        "real_s0r0_parity_gate",
        "runtime_evidence_contract",
        "source_acceleration_authority",
        "streaming_capacity_checks",
        "streaming_proof_archive",
        "streaming_proof_archive_campaign_verification",
        "streaming_proof_archive_shards",
    }
)
SUMMARY_CLASSIFIED_DIFFERENT_FIELDS = frozenset(
    {
        "artifacts",
        "b7_5_contract_binding",
        "b7_5_selection_sizing_factorial_arm_binding",
        "broad_replay_compact_ledgers",
        "capacity_safe_chunk_execution_contract",
        "generated_at_utc",
        "ledger_write_row_counts",
        "progress_rows",
        "route_id",
        "shared_execution_contract",
        "source_authority_preflight_checkpoints",
        "source_universe_rows",
    }
)


def _classify_summary_fields(
    reference: Mapping[str, Any],
    accelerated: Mapping[str, Any],
) -> dict[str, Any]:
    """Require every top-level summary difference to have a named treatment."""

    parent_keys = set(reference)
    successor_keys = set(accelerated)
    parent_only = parent_keys - successor_keys
    successor_only = successor_keys - parent_keys
    _require(not parent_only, "summary_parent_field_missing_from_successor")
    unknown_successor = successor_only - SUMMARY_SUCCESSOR_ONLY_FIELDS
    _require(
        not unknown_successor,
        "summary_unknown_successor_field:"
        + ",".join(sorted(str(value) for value in unknown_successor)),
    )
    differing = {
        key
        for key in parent_keys & successor_keys
        if canonical_bytes(reference[key]) != canonical_bytes(accelerated[key])
    }
    unknown_differences = differing - SUMMARY_CLASSIFIED_DIFFERENT_FIELDS
    _require(
        not unknown_differences,
        "summary_unknown_difference:"
        + ",".join(sorted(str(value) for value in unknown_differences)),
    )
    return {
        "parent_field_count": len(parent_keys),
        "successor_field_count": len(successor_keys),
        "exact_common_field_count": len(parent_keys & successor_keys)
        - len(differing),
        "classified_different_fields": sorted(differing),
        "classified_successor_only_fields": sorted(successor_only),
        "unknown_difference_count": 0,
    }


def compare_summary_projection(
    reference_path: Path,
    accelerated_path: Path,
    *,
    source_projection: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare an explicit causal/economic summary projection only."""

    reference = json.loads(Path(reference_path).read_bytes())
    accelerated = json.loads(Path(accelerated_path).read_bytes())
    _require(
        isinstance(reference, dict) and isinstance(accelerated, dict),
        "summary_not_mapping",
    )
    field_classification = _classify_summary_fields(reference, accelerated)
    _require(
        reference.get("status")
        == accelerated.get("status")
        == "broad_live_as_if_replay_materialized_broker_live_closed",
        "summary_completion_status_invalid",
    )
    left = {field: copy.deepcopy(reference.get(field)) for field in SUMMARY_SEMANTIC_FIELDS}
    right = {field: copy.deepcopy(accelerated.get(field)) for field in SUMMARY_SEMANTIC_FIELDS}
    parent_source = source_projection.get("parent")
    successor_source = source_projection.get("successor")
    _require(
        isinstance(parent_source, Mapping)
        and isinstance(successor_source, Mapping),
        "summary_source_projection_missing",
    )
    expected_parent_count = int(parent_source["raw_row_count"])
    expected_successor_count = int(successor_source["raw_row_count"])
    for projection in (left, right):
        _require(
            isinstance(projection.get("ledger_write_row_counts"), Mapping),
            "summary_ledger_counts_missing",
        )
    _require(
        left["source_universe_rows"] == expected_parent_count
        and left["ledger_write_row_counts"]["source"] == expected_parent_count
        and right["source_universe_rows"] == expected_successor_count
        and right["ledger_write_row_counts"]["source"] == expected_successor_count
        and expected_parent_count - expected_successor_count
        == int(parent_source["excluded_overlap_diagnostic_row_count"])
        == _JUNE_EXPECTED_SYMBOL_COUNT,
        "summary_source_count_reconciliation_invalid",
    )
    left["source_universe_rows"] = SOURCE_DISCOVERY_COUNT_SENTINEL
    right["source_universe_rows"] = SOURCE_DISCOVERY_COUNT_SENTINEL
    left["ledger_write_row_counts"]["source"] = SOURCE_DISCOVERY_COUNT_SENTINEL
    right["ledger_write_row_counts"]["source"] = SOURCE_DISCOVERY_COUNT_SENTINEL
    if canonical_bytes(left) != canonical_bytes(right):
        for field in SUMMARY_SEMANTIC_FIELDS:
            if canonical_bytes(left[field]) != canonical_bytes(right[field]):
                raise PhaseCSemanticError(f"summary_semantic_mismatch:{field}")
        raise PhaseCSemanticError("summary_semantic_mismatch")
    return {
        "status": "SUMMARY_CAUSAL_ECONOMIC_PROJECTION_EXACT",
        "included_fields": list(SUMMARY_SEMANTIC_FIELDS),
        "complete_top_level_field_classification": field_classification,
        "parent_summary_file_sha256": file_sha256(Path(reference_path)),
        "successor_summary_file_sha256": file_sha256(Path(accelerated_path)),
        "classified_transport_and_provenance_fields_bound_by_parent_manifest_and_successor_arm_receipt": sorted(
            SUMMARY_CLASSIFIED_DIFFERENT_FIELDS
            - set(SUMMARY_SEMANTIC_FIELDS)
        ),
        "projection_root_sha256": stable_sha256(left),
        "source_count_reconciliation": {
            "parent_raw_source_rows": expected_parent_count,
            "successor_raw_source_rows": expected_successor_count,
            "excluded_parent_overlap_diagnostic_rows": (
                expected_parent_count - expected_successor_count
            ),
            "selected_source_membership_exact": True,
        },
        "meaningful_difference_count": 0,
        "economic_values_exposed": False,
    }


def compare_arm(
    *,
    parent_manifest: Mapping[str, Any],
    accelerated_output_dir: Path,
    accelerated_prefix: str,
) -> dict[str, Any]:
    artifacts = parent_manifest["artifacts"]
    accelerated = accelerated_artifact_paths(
        accelerated_output_dir, accelerated_prefix
    )
    roles, phase_c_projection = compare_parent_roles(
        parent_manifest=parent_manifest,
        accelerated_output_dir=accelerated_output_dir,
        accelerated_prefix=accelerated_prefix,
    )
    summary = compare_summary_projection(
        Path(str(artifacts["summary"]["resolved_path"])),
        accelerated["summary"],
        source_projection=phase_c_projection["projection_observations"]["source"],
    )
    core = {
        "schema": COMPARISON_SCHEMA,
        "status": "POST_ACCELERATION_JUNE_ARM_SEMANTICALLY_EQUIVALENT",
        "arm_id": parent_manifest["arm_id"],
        "parent_manifest_root_sha256": parent_manifest["manifest_root_sha256"],
        "source_plan_digest_sha256": JUNE_SOURCE_PLAN_SHA256,
        "role_comparisons": roles,
        "summary_comparison": summary,
        "phase_c_projection": phase_c_projection,
        "explicit_volatility_allowlist": semantic.ALLOWLIST_RECEIPT,
        "meaningful_difference_count": 0,
        "unknown_difference_count": 0,
        "acceptance_authorized": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "comparison_root_sha256": stable_sha256(core)}
