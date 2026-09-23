"""Independent verifier for the final replay-acceleration route decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


RESULT_SCHEMA = "gtos.replay_acceleration.final_route_decision.v1"
AMENDMENT_SCHEMA = "gtos.replay_acceleration.prospective_contract_amendment.v1"
EXPECTED_GATE = "HUMAN_OR_EXTERNAL_BLOCKER"
EXPECTED_STATUS = "BLOCKED_EXTERNAL_GOLDEN_INCOMPLETE"
EXPECTED_STAGES = {
    "authoritative_source": "BOUNDED_EQUIVALENCE_ACCEPTED_FOR_REPLAY_SLICE",
    "normalization": "NORMALIZATION_EQUIVALENCE_ACCEPTED",
    "candidate_boundary": "CANDIDATE_BASE_BOUNDARY_ACCEPTED",
    "isolated_reducers": "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED",
    "typed_proofs": "TYPED_STREAMING_PROOF_PLANE_ACCEPTED",
    "resume": "COMPLETE_RESUME_SEMANTICS_ACCEPTED",
    "resource_architecture": "RESOURCE_STORAGE_ARCHITECTURE_ACCEPTED",
    "progressive_two_day": "PROGRESSIVE_TWO_DAY_EQUIVALENCE_ACCEPTED",
}
WARNING_BYTES = 34 * 1024**3
HARD_FLOOR_BYTES = 28 * 1024**3
FORBIDDEN_KEY_FRAGMENTS = (
    "pnl",
    "win_count",
    "loss_count",
    "win_loss",
    "r_total",
    "march_outcome",
    "comparative_economic",
)


class VerificationError(RuntimeError):
    """Stable independent final-route verification failure."""


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


def _is_hash(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _scan_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            _require(
                not any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS),
                "forbidden_output_key_present",
            )
            _scan_keys(child)
    elif isinstance(value, list):
        for child in value:
            _scan_keys(child)


def _load(path: Path, prefix: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise VerificationError(f"{prefix}_missing") from exc
    _require(raw.endswith(b"\n"), f"{prefix}_newline_missing")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{prefix}_json_invalid") from exc
    _require(isinstance(payload, dict), f"{prefix}_json_invalid")
    return raw, payload


def _verify_amendment(path: Path, reference: Mapping[str, Any]) -> dict[str, Any]:
    raw, amendment = _load(path, "amendment")
    _require(hashlib.sha256(raw).hexdigest() == reference.get("file_sha256"), "amendment_file_hash_mismatch")
    _require(len(raw) == reference.get("file_bytes"), "amendment_file_size_mismatch")
    _require(amendment.get("schema") == AMENDMENT_SCHEMA, "amendment_schema_mismatch")
    _require(amendment.get("status") == "DRAFT_NOT_AUTHORITY_DO_NOT_EXECUTE", "amendment_status_invalid")
    recorded = amendment.get("amendment_root_sha256")
    payload = dict(amendment)
    payload.pop("amendment_root_sha256", None)
    _require(_is_hash(recorded) and recorded == _root(payload), "amendment_root_mismatch")
    _require(recorded == reference.get("amendment_root_sha256"), "amendment_reference_root_mismatch")
    _require(amendment.get("bounded_preprocessing_authority") is True, "amendment_bounded_authority_invalid")
    for key in (
        "full_accelerated_s0r0_authority",
        "successor_arm_authority",
        "broker_or_live_authority",
        "deployment_authority",
    ):
        _require(amendment.get(key) is False, f"amendment_{key}_invalid")
    _require(amendment.get("forbidden_output_fields_read") == [], "amendment_forbidden_output_read")
    _scan_keys(amendment)
    return amendment


def verify_final_route_decision(result_path: Path) -> dict[str, Any]:
    raw, result = _load(result_path, "result")
    _require(result.get("schema") == RESULT_SCHEMA, "result_schema_mismatch")
    _require(result.get("status") == EXPECTED_STATUS, "result_status_mismatch")
    _require(result.get("gate") == EXPECTED_GATE, "result_gate_mismatch")
    recorded = result.get("result_root_sha256")
    payload = dict(result)
    payload.pop("result_root_sha256", None)
    _require(_is_hash(recorded) and recorded == _root(payload), "result_root_mismatch")
    _scan_keys(result)
    layers = result.get("accepted_bounded_layers") or []
    _require(len(layers) == result.get("accepted_bounded_layer_count") == 8, "accepted_layer_count_mismatch")
    _require({row.get("stage") for row in layers} == set(EXPECTED_STAGES), "accepted_layer_set_mismatch")
    for row in layers:
        stage = row["stage"]
        path = Path(str(row.get("path") or ""))
        predecessor_raw, predecessor = _load(path, f"predecessor_{stage}")
        _require(hashlib.sha256(predecessor_raw).hexdigest() == row.get("file_sha256"), "accepted_layer_file_hash_mismatch")
        _require(len(predecessor_raw) == row.get("file_bytes"), "accepted_layer_file_size_mismatch")
        _require(predecessor.get("status") == row.get("status") == "ACCEPTED", "accepted_layer_status_mismatch")
        _require(predecessor.get("gate") == row.get("gate") == EXPECTED_STAGES[stage], "accepted_layer_gate_mismatch")
        _require(predecessor.get("schema") == row.get("schema"), "accepted_layer_schema_mismatch")
        _require(predecessor.get("result_root_sha256") == row.get("result_root_sha256"), "accepted_layer_root_mismatch")
    amendment_ref = result.get("prospective_amendment") or {}
    amendment_path = Path(str(amendment_ref.get("path") or ""))
    amendment = _verify_amendment(amendment_path, amendment_ref)
    _require(amendment_ref.get("status") == amendment["status"], "amendment_reference_status_mismatch")
    golden = result.get("legacy_golden_observation") or {}
    _require(golden.get("pid") == 34389, "legacy_pid_mismatch")
    _require(golden.get("expected_output_prefix_present_in_process") is True, "legacy_prefix_observation_missing")
    _require(golden.get("sealed_golden_artifact_count_in_worktree") == 0, "legacy_golden_count_changed")
    _require(golden.get("sealed_full_month_golden_available") is False, "legacy_golden_availability_invalid")
    _require(golden.get("progress_rows_read") is False, "legacy_progress_rows_read")
    _require(golden.get("forbidden_output_fields_read") == [], "legacy_forbidden_output_read")
    _require(golden.get("process_namespace_inspected") is False, "legacy_namespace_inspected")
    _require(golden.get("modified_or_signaled") is False, "legacy_process_modified")
    blocker = result.get("external_blocker") or {}
    _require(blocker.get("code") == "sealed_full_month_legacy_s0r0_golden_unavailable", "external_blocker_code_mismatch")
    _require(blocker.get("final_accelerated_route_prerequisite") is True, "external_blocker_final_gate_invalid")
    _require(blocker.get("bounded_implementation_prerequisite") is False, "external_blocker_bounded_gate_invalid")
    authority = result.get("execution_authority") or {}
    _require(authority.get("bounded_immutable_preprocessing") is True, "bounded_preprocessing_authority_missing")
    _require(authority.get("bounded_candidate_origin_projection") is True, "bounded_candidate_authority_missing")
    for key in (
        "full_accelerated_s0r0",
        "successor_arms",
        "broker_live_vps_canary_deployment",
        "production_trading",
    ):
        _require(authority.get(key) is False, f"execution_authority_{key}_invalid")
    measured = result.get("measured_route_decision") or {}
    _require(measured.get("fastest_tested_run_label") == "cold_w1_a", "fastest_route_label_mismatch")
    _require(measured.get("immutable_prebarrier_worker_count") == 1, "fastest_route_immutable_workers_mismatch")
    _require(measured.get("candidate_generation_worker_count") == 1, "fastest_route_candidate_workers_mismatch")
    _require(measured.get("dominant_stage") == "all_symbol_snapshot", "dominant_stage_mismatch")
    _require(measured.get("whole_replay_speedup_claim") is False, "measured_whole_replay_claim")
    _require(measured.get("warm_speedup_claim") is False, "measured_warm_speedup_claim")
    _require(measured.get("two_worker_speedup_claim") is False, "measured_worker_speedup_claim")
    progressive_path = next(Path(row["path"]) for row in layers if row["stage"] == "progressive_two_day")
    progressive = json.loads(progressive_path.read_bytes())
    runs = progressive.get("measurements", {}).get("runs") or []
    fastest = min(runs, key=lambda row: float(row["end_to_end_wall_seconds"]))
    _require(fastest.get("run_label") == measured.get("fastest_tested_run_label"), "fastest_route_recalculation_mismatch")
    _require(fastest.get("end_to_end_wall_seconds") == measured.get("fastest_tested_wall_seconds"), "fastest_wall_recalculation_mismatch")
    _require(result.get("forbidden_output_fields_read") == [], "result_forbidden_output_read")
    for key in (
        "policy_execution_entered",
        "successor_arm_execution_launched",
        "whole_replay_speedup_claim",
        "warm_speedup_claim",
    ):
        _require(result.get(key) is False, f"result_{key}_invalid")
    storage = result.get("resource_and_storage") or {}
    _require(storage.get("warning_bytes") == WARNING_BYTES, "disk_warning_mismatch")
    _require(storage.get("hard_floor_bytes") == HARD_FLOOR_BYTES, "disk_floor_mismatch")
    _require(storage.get("available_bytes", 0) >= WARNING_BYTES, "recorded_disk_below_warning")
    _require(storage.get("files_deleted") == 0 and storage.get("bytes_reclaimed") == 0, "retention_reclaim_invalid")
    _require(storage.get("broad_lfs_hydration_performed") is False, "broad_lfs_hydration_invalid")
    _require(storage.get("lfs_prune_performed") is False, "lfs_prune_invalid")
    _require(storage.get("unique_proof_evidence_preserved") is True, "proof_preservation_invalid")
    live = os.statvfs(Path.cwd())
    _require(live.f_bavail * live.f_frsize >= HARD_FLOOR_BYTES, "live_disk_below_hard_floor")
    code = result.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
        ("test_path", "test_sha256"),
    ):
        path = Path(str(code.get(path_key) or ""))
        _require(path.is_file(), "code_identity_file_missing")
        _require(_file_hash(path) == code.get(hash_key), "code_identity_hash_mismatch")
    return {
        "status": "VERIFIED",
        "gate": EXPECTED_GATE,
        "result_root_sha256": recorded,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "accepted_bounded_layer_count": len(layers),
        "full_accelerated_route_authority": False,
    }


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(_canonical(payload) + b"\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_final_route_decision(args.result)
    if args.receipt:
        _write(args.receipt, receipt)
    print(_canonical(receipt).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
