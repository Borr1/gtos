"""Independent stdlib verifier for persisted full-state resume checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.resume_result.v1"
CHECKPOINT_SCHEMA = "gtos.replay_acceleration.full_arm_checkpoint.v1"
SEAL_SCHEMA = "gtos.replay_acceleration.checkpoint_seal.v1"
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
SCENARIOS = (
    "uninterrupted",
    "interruption_before_seal",
    "interruption_after_seal",
)


class VerificationError(RuntimeError):
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


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def _verify_entry(
    *, base: Path, entry: Mapping[str, Any], arm: str, identity: Mapping[str, Any]
) -> dict[str, Any]:
    checkpoint_path = base / str(entry["checkpoint_path"])
    _require(checkpoint_path.is_file(), "checkpoint_missing")
    _require(
        _file_hash(checkpoint_path) == entry.get("checkpoint_file_sha256"),
        "checkpoint_file_hash_mismatch",
    )
    raw = checkpoint_path.read_bytes()
    _require(raw.endswith(b"\n"), "checkpoint_newline_missing")
    try:
        checkpoint = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("checkpoint_json_invalid") from exc
    _require(checkpoint.get("schema") == CHECKPOINT_SCHEMA, "checkpoint_schema_mismatch")
    _require(checkpoint.get("arm_id") == arm, "checkpoint_arm_mismatch")
    recorded = checkpoint.get("checkpoint_root_sha256")
    payload = dict(checkpoint)
    payload.pop("checkpoint_root_sha256", None)
    _require(recorded == _root(payload), "checkpoint_root_mismatch")
    _require(recorded == entry.get("checkpoint_root_sha256"), "checkpoint_manifest_root_mismatch")
    _require(
        checkpoint.get("state_root_sha256") == _root(checkpoint.get("state")),
        "checkpoint_state_root_mismatch",
    )
    _require(checkpoint.get("identity") == identity, "checkpoint_identity_mismatch")
    _require(checkpoint.get("sealed_shard_boundary") is True, "checkpoint_boundary_flag_invalid")
    if entry.get("sealed") is True:
        seal_path = base / str(entry.get("seal_path") or "")
        _require(seal_path.is_file(), "seal_missing")
        _require(_file_hash(seal_path) == entry.get("seal_file_sha256"), "seal_file_hash_mismatch")
        seal_raw = seal_path.read_bytes()
        _require(seal_raw.endswith(b"\n"), "seal_newline_missing")
        seal = json.loads(seal_raw)
        _require(seal.get("schema") == SEAL_SCHEMA, "seal_schema_mismatch")
        seal_root = seal.get("seal_root_sha256")
        seal_payload = dict(seal)
        seal_payload.pop("seal_root_sha256", None)
        _require(seal_root == _root(seal_payload), "seal_root_mismatch")
        _require(seal_root == entry.get("seal_root_sha256"), "seal_manifest_root_mismatch")
        _require(seal.get("checkpoint_file_sha256") == _file_hash(checkpoint_path), "seal_checkpoint_hash_mismatch")
        _require(seal.get("checkpoint_root_sha256") == recorded, "seal_checkpoint_root_mismatch")
    else:
        _require("seal_path" not in entry, "orphan_has_seal_path")
        inferred_seal = checkpoint_path.with_name(
            checkpoint_path.name.replace(".checkpoint.json", ".seal.json")
        )
        _require(not inferred_seal.exists(), "orphan_unexpectedly_sealed")
    return checkpoint


def verify_resume_result(result_path: Path) -> dict[str, Any]:
    raw = result_path.read_bytes()
    _require(raw.endswith(b"\n"), "result_newline_missing")
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("result_json_invalid") from exc
    _require(result.get("schema") == SCHEMA, "result_schema_mismatch")
    _require(result.get("status") == "ACCEPTED", "result_status_invalid")
    _require(result.get("gate") == "COMPLETE_RESUME_SEMANTICS_ACCEPTED", "result_gate_mismatch")
    recorded = result.get("result_root_sha256")
    payload = dict(result)
    payload.pop("result_root_sha256", None)
    _require(recorded == _root(payload), "result_root_mismatch")
    identity = result.get("identity") or {}
    _require(_root(identity) == result.get("identity_root_sha256"), "identity_root_mismatch")
    predecessors = result.get("predecessors") or {}
    predecessor_payloads: dict[str, Any] = {}
    for name in ("reducer", "typed_proof"):
        predecessor = predecessors.get(name) or {}
        path = Path(str(predecessor.get("path") or ""))
        _require(path.is_file(), "predecessor_missing")
        _require(_file_hash(path) == predecessor.get("file_sha256"), "predecessor_hash_mismatch")
        predecessor_payloads[name] = json.loads(path.read_bytes())
    reducer_result = predecessor_payloads["reducer"]
    arms = result.get("arms") or {}
    _require(set(arms) == set(ARMS), "arm_set_mismatch")
    route_arm_rows: list[dict[str, Any]] = []
    scenario_count = 0
    for arm in ARMS:
        arm_receipt = arms[arm]
        expected_final = reducer_result["arms"][arm]["final_state_root_sha256"]
        _require(
            arm_receipt.get("expected_final_state_root_sha256") == expected_final,
            "expected_final_state_root_mismatch",
        )
        scenarios = arm_receipt.get("scenarios") or {}
        _require(set(scenarios) == set(SCENARIOS), "scenario_set_mismatch")
        scenario_roots: list[dict[str, str]] = []
        for scenario in SCENARIOS:
            scenario_count += 1
            receipt = scenarios[scenario]
            checkpoints = receipt.get("checkpoints") or []
            _require(checkpoints, "scenario_checkpoints_missing")
            sealed: list[dict[str, Any]] = []
            orphan: list[dict[str, Any]] = []
            for entry in checkpoints:
                checkpoint = _verify_entry(
                    base=result_path.parent,
                    entry=entry,
                    arm=arm,
                    identity=identity,
                )
                (sealed if entry.get("sealed") else orphan).append(checkpoint)
            sealed.sort(key=lambda row: (row["shard_index"], row["attempt"]))
            prior_root = None
            for checkpoint in sealed:
                _require(
                    checkpoint.get("previous_checkpoint_root_sha256") == prior_root,
                    "checkpoint_chain_mismatch",
                )
                prior_root = checkpoint["checkpoint_root_sha256"]
            _require(sealed[-1]["state_root_sha256"] == expected_final, "scenario_final_state_mismatch")
            _require(receipt.get("final_state_root_sha256") == expected_final, "scenario_receipt_final_mismatch")
            _require(len(orphan) == receipt.get("orphan_checkpoint_count"), "orphan_count_mismatch")
            _require(len(sealed) == receipt.get("sealed_checkpoint_count"), "sealed_count_mismatch")
            if scenario == "interruption_before_seal":
                _require(len(orphan) == 1, "before_seal_orphan_missing")
                _require(receipt.get("replayed_event_count", 99) <= 4, "restart_loss_bound_exceeded")
            elif scenario == "interruption_after_seal":
                _require(not orphan, "after_seal_orphan_present")
                _require(receipt.get("replayed_event_count") == 0, "after_seal_replay_nonzero")
            scenario_payload = {
                "arm_id": arm,
                "scenario": scenario,
                "identity_root_sha256": result["identity_root_sha256"],
                "sealed_checkpoint_roots": [row["checkpoint_root_sha256"] for row in sealed],
                "orphan_checkpoint_roots": [row["checkpoint_root_sha256"] for row in orphan],
                "final_state_root_sha256": expected_final,
                "replayed_event_count": receipt["replayed_event_count"],
            }
            scenario_root = _root(scenario_payload)
            _require(scenario_root == receipt.get("scenario_root_sha256"), "scenario_root_mismatch")
            scenario_roots.append({"scenario": scenario, "root_sha256": scenario_root})
        route_arm_rows.append(
            {
                "arm_id": arm,
                "expected_final_state_root_sha256": expected_final,
                "scenario_roots": scenario_roots,
            }
        )
    route_payload = {
        "identity_root_sha256": result["identity_root_sha256"],
        "arms": route_arm_rows,
    }
    _require(_root(route_payload) == result.get("resume_route_root_sha256"), "resume_route_root_mismatch")
    _require(result.get("max_events_per_atomic_shard") == 4, "atomic_shard_bound_mismatch")
    failures = result.get("failure_injections") or []
    _require(len(failures) == 10, "failure_injection_count_mismatch")
    _require(
        all(row.get("status") == "REJECTED_AS_REQUIRED" for row in failures),
        "failure_injection_verdict_invalid",
    )
    code = result.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
    ):
        path = Path(str(code.get(path_key) or ""))
        _require(path.is_file(), "code_file_missing")
        _require(_file_hash(path) == code.get(hash_key), "code_hash_mismatch")
    execution = result.get("execution") or {}
    _require(execution.get("policy_callbacks_invoked") is False, "policy_callback_flag_invalid")
    _require(execution.get("successor_arm_execution_launched") is False, "successor_launch_flag_invalid")
    return {
        "status": "VERIFIED",
        "arm_count": 4,
        "scenario_count": scenario_count,
        "resume_route_root_sha256": result["resume_route_root_sha256"],
        "result_root_sha256": recorded,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _atomic_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(_canonical(payload) + b"\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_resume_result(args.result)
    if args.receipt:
        _atomic_receipt(args.receipt, receipt)
    print(_canonical(receipt).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
