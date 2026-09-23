"""Independent stdlib verifier for persisted candidate-boundary result bytes.

This module deliberately does not import the writer, candidate generator,
factorial implementation, or any shared root builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.candidate_boundary_result.v1"
PROBE_SCHEMA = "gtos.replay_acceleration.candidate_boundary_probe.v1"
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
FACTOR_TOKEN = "b7_5_selection_sizing_factorial_"


class VerificationError(RuntimeError):
    """Stable persisted-byte verification failure."""


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


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def verify_candidate_boundary_result(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    _require(raw.endswith(b"\n"), "result_newline_missing")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("result_json_invalid") from exc
    _require(isinstance(payload, dict), "result_not_object")
    _require(payload.get("schema") == SCHEMA, "result_schema_mismatch")
    _require(payload.get("status") == "ACCEPTED", "result_status_not_accepted")
    _require(
        payload.get("gate") == "CANDIDATE_BASE_BOUNDARY_ACCEPTED",
        "result_gate_mismatch",
    )
    recorded_root = payload.get("result_root_sha256")
    root_payload = dict(payload)
    root_payload.pop("result_root_sha256", None)
    _require(recorded_root == _root(root_payload), "result_root_mismatch")

    probe = payload.get("candidate_probe")
    _require(isinstance(probe, dict), "candidate_probe_missing")
    _require(probe.get("schema") == PROBE_SCHEMA, "candidate_probe_schema_mismatch")
    _require(tuple(probe.get("arm_order") or ()) == ARMS, "arm_order_mismatch")
    arms = probe.get("arms")
    _require(isinstance(arms, dict) and set(arms) == set(ARMS), "arm_set_mismatch")
    roots: set[str] = set()
    read_sets: set[tuple[str, ...]] = set()
    for arm_id in ARMS:
        arm = arms[arm_id]
        _require(isinstance(arm, dict), "arm_receipt_not_object")
        roots.add(str(arm.get("candidate_base_root_sha256") or ""))
        read_set = tuple(arm.get("candidate_base_config_read_set") or ())
        read_sets.add(read_set)
        _require(
            not any(FACTOR_TOKEN in path_value for path_value in read_set),
            "candidate_factor_read_detected",
        )
        scheduler_reads = arm.get("scheduler_factor_read_set") or []
        _require(
            bool(scheduler_reads)
            and all(FACTOR_TOKEN in path_value for path_value in scheduler_reads),
            "scheduler_factor_read_set_invalid",
        )
        _require(arm.get("factor_binding_valid") is True, "factor_binding_invalid")
    _require(len(roots) == 1 and "" not in roots, "candidate_root_mismatch")
    _require(len(read_sets) == 1, "candidate_read_set_mismatch")
    _require(probe.get("candidate_base_count", 0) > 0, "candidate_probe_empty")
    _require(
        probe.get("candidate_base_factor_read_intersection") == [],
        "candidate_factor_intersection_nonempty",
    )
    _require(
        probe.get("shared_boundary_stage") == "candidate_base_materialized",
        "shared_boundary_stage_invalid",
    )
    _require(
        probe.get("cross_symbol_barrier_required") is True,
        "cross_symbol_barrier_not_required",
    )
    classifications = probe.get("stage_classification") or {}
    for stage in (
        "candidate_evaluation",
        "scheduler_eligibility",
        "risk_and_order_materialization",
        "portfolio_lifecycle",
    ):
        _require(classifications.get(stage) == "arm_local", "arm_local_boundary_weakened")
    _require(
        probe.get("successor_arm_execution_launched") is False,
        "successor_arm_execution_flag_invalid",
    )
    _require(
        payload.get("outcome_blind_structural_only") is True,
        "outcome_blind_flag_invalid",
    )
    _require(payload.get("policy_execution_entered") is False, "policy_execution_flag_invalid")
    _require(
        payload.get("successor_arm_execution_launched") is False,
        "successor_execution_flag_invalid",
    )
    injections = payload.get("failure_injections")
    _require(isinstance(injections, list) and len(injections) == 5, "failure_injection_count_invalid")
    _require(
        all(
            isinstance(item, dict) and item.get("status") == "REJECTED_AS_REQUIRED"
            for item in injections
        ),
        "failure_injection_verdict_invalid",
    )

    for predecessor in (payload.get("accepted_predecessors") or {}).values():
        _require(isinstance(predecessor, Mapping), "predecessor_identity_invalid")
        predecessor_path = Path(str(predecessor.get("path") or ""))
        _require(predecessor_path.is_file(), "predecessor_file_missing")
        _require(
            _file_hash(predecessor_path) == predecessor.get("file_sha256"),
            "predecessor_file_hash_mismatch",
        )
    code_identity = payload.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
    ):
        code_path = Path(str(code_identity.get(path_key) or ""))
        _require(code_path.is_file(), "code_identity_file_missing")
        _require(_file_hash(code_path) == code_identity.get(hash_key), "code_identity_mismatch")

    return {
        "status": "VERIFIED",
        "result_root_sha256": recorded_root,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "arm_count": len(ARMS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    verified = verify_candidate_boundary_result(args.result)
    rendered = _canonical(verified) + b"\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_name(f".{args.receipt.name}.tmp-{os.getpid()}")
        temporary.write_bytes(rendered)
        os.replace(temporary, args.receipt)
    print(rendered.decode("ascii").rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
