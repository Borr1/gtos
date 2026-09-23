"""Atomic full-state checkpoint and resume semantics for bounded replay shards."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.research_infra import replay_acceleration_isolated_reducers as reducers


SCHEMA = "gtos.replay_acceleration.resume_result.v1"
CHECKPOINT_SCHEMA = "gtos.replay_acceleration.full_arm_checkpoint.v1"
SEAL_SCHEMA = "gtos.replay_acceleration.checkpoint_seal.v1"
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
SCENARIOS = (
    "uninterrupted",
    "interruption_before_seal",
    "interruption_after_seal",
)
REDUCER_RESULT_PATH = Path(
    "research/operations/replay_acceleration_isolated_reducers_2026_07_19/"
    "ISOLATED_REDUCER_RESULT.json"
)
TYPED_RESULT_PATH = Path(
    "research/operations/replay_acceleration_typed_proofs_2026_07_19/"
    "TYPED_PROOF_RESULT.json"
)


class ResumeError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(canonical_bytes(payload) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _identity() -> dict[str, str]:
    reducer_result = json.loads(REDUCER_RESULT_PATH.read_bytes())
    typed_result = json.loads(TYPED_RESULT_PATH.read_bytes())
    if reducer_result.get("gate") != "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED":
        raise ResumeError("reducer_predecessor_not_accepted")
    if typed_result.get("gate") != "TYPED_STREAMING_PROOF_PLANE_ACCEPTED":
        raise ResumeError("typed_predecessor_not_accepted")
    config_identity = {
        "atomic_shard_partition": "decision_window",
        "full_state_serialization": True,
        "max_unsealed_shards": 1,
        "mutable_reducer_parallelism": False,
    }
    code_identity = {
        "resume_writer_sha256": file_sha256(Path(__file__).resolve()),
        "reducer_sha256": file_sha256(Path(reducers.__file__).resolve()),
    }
    return {
        "source_barrier_root": reducer_result["cross_symbol_barrier"][
            "source_barrier_root_sha256"
        ],
        "candidate_base_root": reducer_result["candidate_base_root_sha256"],
        "reducer_result_root": reducer_result["result_root_sha256"],
        "typed_campaign_root": typed_result["campaign_root_sha256"],
        "config_identity_root": stable_sha256(config_identity),
        "code_identity_root": stable_sha256(code_identity),
        "checkpoint_schema_root": hashlib.sha256(
            CHECKPOINT_SCHEMA.encode("ascii")
        ).hexdigest(),
    }


def _load_reducer_arm(arm: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = json.loads(REDUCER_RESULT_PATH.read_bytes())
    manifest = result["arms"][arm]
    shard_path = REDUCER_RESULT_PATH.parent / manifest["path"]
    if file_sha256(shard_path) != manifest["file_sha256"]:
        raise ResumeError("reducer_shard_hash_mismatch")
    shard = json.loads(shard_path.read_bytes())
    return shard, list(shard["events"])


def _group_by_window(events: Iterable[Mapping[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current_window: int | None = None
    for raw in events:
        event = dict(raw)
        cursor = event.get("cursor")
        if not isinstance(cursor, list) or len(cursor) != 3:
            raise ResumeError("event_cursor_invalid")
        window = int(cursor[1])
        if current_window is None or window != current_window:
            if current_window is not None and window <= current_window:
                raise ResumeError("event_window_not_increasing")
            groups.append([])
            current_window = window
        groups[-1].append(event)
    return groups


def _new_state(arm: str, shard: Mapping[str, Any]) -> reducers.ArmState:
    final_state = shard["final_state"]
    return reducers.ArmState(
        arm_id=arm,
        candidate_base_root=shard["candidate_base_root_sha256"],
        source_barrier_root=shard["source_barrier"]["source_barrier_root_sha256"],
        selected_day=shard["source_barrier"]["selected_day"],
        binding_projection_sha256=final_state["binding_projection_sha256"],
    )


def _restore_state(payload: Mapping[str, Any]) -> reducers.ArmState:
    state = reducers.ArmState(
        arm_id=str(payload["arm_id"]),
        candidate_base_root=str(payload["candidate_base_root"]),
        source_barrier_root=str(payload["source_barrier_root"]),
        selected_day=str(payload["selected_day"]),
        binding_projection_sha256=str(payload["binding_projection_sha256"]),
    )
    for field_name in reducers.MUTABLE_FIELDS:
        setattr(state, field_name, copy.deepcopy(payload[field_name]))
    state.order_sequence = int(payload["order_sequence"])
    last_cursor = payload.get("last_cursor")
    state.last_cursor = tuple(last_cursor) if last_cursor is not None else None
    state.sealed = bool(payload["sealed"])
    return state


def _checkpoint_paths(
    directory: Path, shard_index: int, attempt: int
) -> tuple[Path, Path]:
    stem = f"shard-{shard_index:03d}.attempt-{attempt:03d}"
    return directory / f"{stem}.checkpoint.json", directory / f"{stem}.seal.json"


def _write_checkpoint(
    *,
    directory: Path,
    arm: str,
    scenario: str,
    shard_index: int,
    attempt: int,
    event_start_index: int,
    event_end_index: int,
    previous_checkpoint_root: str | None,
    identity: Mapping[str, str],
    state: reducers.ArmState,
    seal: bool,
) -> dict[str, Any]:
    checkpoint_path, seal_path = _checkpoint_paths(directory, shard_index, attempt)
    state_payload = state.payload()
    envelope: dict[str, Any] = {
        "schema": CHECKPOINT_SCHEMA,
        "arm_id": arm,
        "scenario": scenario,
        "shard_index": shard_index,
        "attempt": attempt,
        "event_start_index": event_start_index,
        "event_end_index": event_end_index,
        "next_event_index": event_end_index + 1,
        "previous_checkpoint_root_sha256": previous_checkpoint_root,
        "identity": dict(identity),
        "state": state_payload,
        "state_root_sha256": stable_sha256(state_payload),
        "sealed_shard_boundary": True,
    }
    envelope["checkpoint_root_sha256"] = stable_sha256(envelope)
    _atomic_json(checkpoint_path, envelope)
    entry: dict[str, Any] = {
        "checkpoint_path": checkpoint_path.as_posix(),
        "checkpoint_file_sha256": file_sha256(checkpoint_path),
        "checkpoint_root_sha256": envelope["checkpoint_root_sha256"],
        "state_root_sha256": envelope["state_root_sha256"],
        "shard_index": shard_index,
        "attempt": attempt,
        "event_count": event_end_index - event_start_index + 1,
        "sealed": seal,
    }
    if seal:
        seal_payload: dict[str, Any] = {
            "schema": SEAL_SCHEMA,
            "arm_id": arm,
            "scenario": scenario,
            "shard_index": shard_index,
            "attempt": attempt,
            "checkpoint_file_sha256": entry["checkpoint_file_sha256"],
            "checkpoint_root_sha256": entry["checkpoint_root_sha256"],
        }
        seal_payload["seal_root_sha256"] = stable_sha256(seal_payload)
        _atomic_json(seal_path, seal_payload)
        entry["seal_path"] = seal_path.as_posix()
        entry["seal_file_sha256"] = file_sha256(seal_path)
        entry["seal_root_sha256"] = seal_payload["seal_root_sha256"]
    return entry


def _validate_checkpoint(
    checkpoint_path: Path,
    seal_path: Path,
    *,
    expected_arm: str,
    expected_identity: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    checkpoint_raw = checkpoint_path.read_bytes()
    seal_raw = seal_path.read_bytes()
    if not seal_raw.endswith(b"\n"):
        raise ResumeError("checkpoint_framing_invalid")
    try:
        seal = json.loads(seal_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResumeError("checkpoint_json_invalid") from exc
    if seal.get("schema") != SEAL_SCHEMA:
        raise ResumeError("seal_schema_mismatch")
    seal_root = seal.get("seal_root_sha256")
    seal_payload = dict(seal)
    seal_payload.pop("seal_root_sha256", None)
    if seal_root != stable_sha256(seal_payload):
        raise ResumeError("seal_root_mismatch")
    if seal.get("checkpoint_file_sha256") != hashlib.sha256(checkpoint_raw).hexdigest():
        raise ResumeError("checkpoint_file_hash_mismatch")
    if not checkpoint_raw.endswith(b"\n"):
        raise ResumeError("checkpoint_framing_invalid")
    try:
        checkpoint = json.loads(checkpoint_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResumeError("checkpoint_json_invalid") from exc
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise ResumeError("checkpoint_schema_mismatch")
    if checkpoint.get("arm_id") != expected_arm:
        raise ResumeError("checkpoint_arm_mismatch")
    checkpoint_root = checkpoint.get("checkpoint_root_sha256")
    checkpoint_payload = dict(checkpoint)
    checkpoint_payload.pop("checkpoint_root_sha256", None)
    if checkpoint_root != stable_sha256(checkpoint_payload):
        raise ResumeError("checkpoint_root_mismatch")
    if seal.get("checkpoint_root_sha256") != checkpoint_root:
        raise ResumeError("seal_checkpoint_root_mismatch")
    if checkpoint.get("state_root_sha256") != stable_sha256(checkpoint.get("state")):
        raise ResumeError("checkpoint_state_root_mismatch")
    identity = checkpoint.get("identity")
    if not isinstance(identity, dict):
        raise ResumeError("checkpoint_identity_missing")
    for key, value in expected_identity.items():
        if identity.get(key) != value:
            raise ResumeError(f"checkpoint_identity_mismatch:{key}")
    return checkpoint, seal


def load_latest_sealed_checkpoint(
    directory: Path,
    *,
    expected_arm: str,
    expected_identity: Mapping[str, str],
    require_checkpoint: bool = False,
) -> tuple[reducers.ArmState | None, dict[str, Any]]:
    admitted: list[dict[str, Any]] = []
    orphan_paths: list[str] = []
    for checkpoint_path in sorted(directory.glob("*.checkpoint.json")):
        seal_path = checkpoint_path.with_name(
            checkpoint_path.name.replace(".checkpoint.json", ".seal.json")
        )
        if not seal_path.is_file():
            orphan_paths.append(checkpoint_path.as_posix())
            continue
        checkpoint, _ = _validate_checkpoint(
            checkpoint_path,
            seal_path,
            expected_arm=expected_arm,
            expected_identity=expected_identity,
        )
        admitted.append(checkpoint)
    if not admitted:
        if require_checkpoint:
            raise ResumeError("no_sealed_checkpoint")
        return None, {"admitted": [], "orphans": orphan_paths}
    admitted.sort(key=lambda row: (int(row["shard_index"]), int(row["attempt"])))
    latest = admitted[-1]
    return _restore_state(latest["state"]), {
        "admitted": admitted,
        "orphans": orphan_paths,
    }


def _scenario(
    *,
    output_dir: Path,
    arm: str,
    scenario: str,
    identity: Mapping[str, str],
    reducer_shard: Mapping[str, Any],
    groups: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    directory = output_dir / "checkpoints" / arm / scenario
    state = _new_state(arm, reducer_shard)
    entries: list[dict[str, Any]] = []
    previous_root: str | None = None
    event_start = 0
    replayed_event_count = 0

    def apply_group(index: int) -> None:
        nonlocal state
        for event in groups[index]:
            reducers.apply_structural_event(state, event)

    if scenario == "uninterrupted":
        for shard_index, group in enumerate(groups):
            apply_group(shard_index)
            entry = _write_checkpoint(
                directory=directory,
                arm=arm,
                scenario=scenario,
                shard_index=shard_index,
                attempt=0,
                event_start_index=event_start,
                event_end_index=event_start + len(group) - 1,
                previous_checkpoint_root=previous_root,
                identity=identity,
                state=state,
                seal=True,
            )
            entries.append(entry)
            previous_root = entry["checkpoint_root_sha256"]
            event_start += len(group)
    elif scenario == "interruption_before_seal":
        apply_group(0)
        first = _write_checkpoint(
            directory=directory,
            arm=arm,
            scenario=scenario,
            shard_index=0,
            attempt=0,
            event_start_index=0,
            event_end_index=len(groups[0]) - 1,
            previous_checkpoint_root=None,
            identity=identity,
            state=state,
            seal=True,
        )
        entries.append(first)
        previous_root = first["checkpoint_root_sha256"]
        event_start = len(groups[0])
        apply_group(1)
        orphan = _write_checkpoint(
            directory=directory,
            arm=arm,
            scenario=scenario,
            shard_index=1,
            attempt=0,
            event_start_index=event_start,
            event_end_index=event_start + len(groups[1]) - 1,
            previous_checkpoint_root=previous_root,
            identity=identity,
            state=state,
            seal=False,
        )
        entries.append(orphan)
        resumed_state, scan = load_latest_sealed_checkpoint(
            directory,
            expected_arm=arm,
            expected_identity=identity,
            require_checkpoint=True,
        )
        if resumed_state is None or len(scan["orphans"]) != 1:
            raise ResumeError("before_seal_orphan_not_excluded")
        state = resumed_state
        replayed_event_count = len(groups[1])
        apply_group(1)
        replayed = _write_checkpoint(
            directory=directory,
            arm=arm,
            scenario=scenario,
            shard_index=1,
            attempt=1,
            event_start_index=event_start,
            event_end_index=event_start + len(groups[1]) - 1,
            previous_checkpoint_root=previous_root,
            identity=identity,
            state=state,
            seal=True,
        )
        entries.append(replayed)
        previous_root = replayed["checkpoint_root_sha256"]
        event_start += len(groups[1])
        for shard_index in range(2, len(groups)):
            apply_group(shard_index)
            entry = _write_checkpoint(
                directory=directory,
                arm=arm,
                scenario=scenario,
                shard_index=shard_index,
                attempt=0,
                event_start_index=event_start,
                event_end_index=event_start + len(groups[shard_index]) - 1,
                previous_checkpoint_root=previous_root,
                identity=identity,
                state=state,
                seal=True,
            )
            entries.append(entry)
            previous_root = entry["checkpoint_root_sha256"]
            event_start += len(groups[shard_index])
    elif scenario == "interruption_after_seal":
        for shard_index in (0, 1):
            apply_group(shard_index)
            entry = _write_checkpoint(
                directory=directory,
                arm=arm,
                scenario=scenario,
                shard_index=shard_index,
                attempt=0,
                event_start_index=event_start,
                event_end_index=event_start + len(groups[shard_index]) - 1,
                previous_checkpoint_root=previous_root,
                identity=identity,
                state=state,
                seal=True,
            )
            entries.append(entry)
            previous_root = entry["checkpoint_root_sha256"]
            event_start += len(groups[shard_index])
        resumed_state, scan = load_latest_sealed_checkpoint(
            directory,
            expected_arm=arm,
            expected_identity=identity,
            require_checkpoint=True,
        )
        if resumed_state is None or scan["orphans"]:
            raise ResumeError("after_seal_checkpoint_not_admitted")
        state = resumed_state
        for shard_index in range(2, len(groups)):
            apply_group(shard_index)
            entry = _write_checkpoint(
                directory=directory,
                arm=arm,
                scenario=scenario,
                shard_index=shard_index,
                attempt=0,
                event_start_index=event_start,
                event_end_index=event_start + len(groups[shard_index]) - 1,
                previous_checkpoint_root=previous_root,
                identity=identity,
                state=state,
                seal=True,
            )
            entries.append(entry)
            previous_root = entry["checkpoint_root_sha256"]
            event_start += len(groups[shard_index])
    else:
        raise ResumeError("resume_scenario_unknown")

    final_state = state.payload()
    final_root = stable_sha256(final_state)
    sealed_roots = [entry["checkpoint_root_sha256"] for entry in entries if entry["sealed"]]
    orphan_roots = [entry["checkpoint_root_sha256"] for entry in entries if not entry["sealed"]]
    scenario_root = stable_sha256(
        {
            "arm_id": arm,
            "scenario": scenario,
            "identity_root_sha256": stable_sha256(identity),
            "sealed_checkpoint_roots": sealed_roots,
            "orphan_checkpoint_roots": orphan_roots,
            "final_state_root_sha256": final_root,
            "replayed_event_count": replayed_event_count,
        }
    )
    return {
        "checkpoints": entries,
        "final_state_root_sha256": final_root,
        "scenario_root_sha256": scenario_root,
        "replayed_event_count": replayed_event_count,
        "orphan_checkpoint_count": len(orphan_roots),
        "sealed_checkpoint_count": len(sealed_roots),
    }


def _reseal(checkpoint_path: Path, seal_path: Path, checkpoint: dict[str, Any]) -> None:
    checkpoint.pop("checkpoint_root_sha256", None)
    checkpoint["checkpoint_root_sha256"] = stable_sha256(checkpoint)
    _atomic_json(checkpoint_path, checkpoint)
    seal = json.loads(seal_path.read_bytes())
    seal.update(
        {
            "checkpoint_file_sha256": file_sha256(checkpoint_path),
            "checkpoint_root_sha256": checkpoint["checkpoint_root_sha256"],
        }
    )
    seal.pop("seal_root_sha256", None)
    seal["seal_root_sha256"] = stable_sha256(seal)
    _atomic_json(seal_path, seal)


FAILURE_EXPECTED = {
    "bit_flip": "checkpoint_file_hash_mismatch",
    "append_after_seal": "checkpoint_file_hash_mismatch",
    "seal_mismatch": "seal_root_mismatch",
    "stale_source": "checkpoint_identity_mismatch:source_barrier_root",
    "stale_candidate": "checkpoint_identity_mismatch:candidate_base_root",
    "stale_config": "checkpoint_identity_mismatch:config_identity_root",
    "stale_code": "checkpoint_identity_mismatch:code_identity_root",
    "stale_proof_route": "checkpoint_identity_mismatch:typed_campaign_root",
    "wrong_arm": "checkpoint_arm_mismatch",
    "interruption_before_seal": "no_sealed_checkpoint",
}


def run_resume_failure_injections(output_dir: Path) -> list[dict[str, str]]:
    identity = _identity()
    reducer_shard, events = _load_reducer_arm("S0R0")
    groups = _group_by_window(events)
    verdicts: list[dict[str, str]] = []
    for case, expected in FAILURE_EXPECTED.items():
        directory = output_dir / "resume-failure-injections" / case
        state = _new_state("S0R0", reducer_shard)
        for event in groups[0]:
            reducers.apply_structural_event(state, event)
        entry = _write_checkpoint(
            directory=directory,
            arm="S0R0",
            scenario="failure_injection",
            shard_index=0,
            attempt=0,
            event_start_index=0,
            event_end_index=len(groups[0]) - 1,
            previous_checkpoint_root=None,
            identity=identity,
            state=state,
            seal=case != "interruption_before_seal",
        )
        checkpoint_path = Path(entry["checkpoint_path"])
        seal_path = checkpoint_path.with_name(
            checkpoint_path.name.replace(".checkpoint.json", ".seal.json")
        )
        if case == "bit_flip":
            raw = bytearray(checkpoint_path.read_bytes())
            raw[len(raw) // 2] ^= 1
            checkpoint_path.write_bytes(raw)
        elif case == "append_after_seal":
            checkpoint_path.write_bytes(checkpoint_path.read_bytes() + b"X")
        elif case == "seal_mismatch":
            seal = json.loads(seal_path.read_bytes())
            seal["checkpoint_root_sha256"] = "0" * 64
            _atomic_json(seal_path, seal)
        elif case.startswith("stale_"):
            key = {
                "stale_source": "source_barrier_root",
                "stale_candidate": "candidate_base_root",
                "stale_config": "config_identity_root",
                "stale_code": "code_identity_root",
                "stale_proof_route": "typed_campaign_root",
            }[case]
            checkpoint = json.loads(checkpoint_path.read_bytes())
            checkpoint["identity"][key] = "0" * 64
            _reseal(checkpoint_path, seal_path, checkpoint)
        elif case == "wrong_arm":
            checkpoint = json.loads(checkpoint_path.read_bytes())
            checkpoint["arm_id"] = "S1R0"
            _reseal(checkpoint_path, seal_path, checkpoint)
        try:
            load_latest_sealed_checkpoint(
                directory,
                expected_arm="S0R0",
                expected_identity=identity,
                require_checkpoint=True,
            )
        except ResumeError as exc:
            if str(exc) != expected:
                raise ResumeError("failure_injection_wrong_rejection") from exc
            verdicts.append(
                {"case": case, "status": "REJECTED_AS_REQUIRED", "code": expected}
            )
        else:
            raise ResumeError("failure_injection_not_rejected")
    return verdicts


def _relativize_entries(entries: list[dict[str, Any]], base: Path) -> None:
    for entry in entries:
        entry["checkpoint_path"] = Path(entry["checkpoint_path"]).relative_to(base).as_posix()
        if "seal_path" in entry:
            entry["seal_path"] = Path(entry["seal_path"]).relative_to(base).as_posix()


def write_resume_result(output_dir: Path) -> Path:
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    identity = _identity()
    arms: dict[str, dict[str, Any]] = {}
    max_events_per_shard = 0
    for arm in ARMS:
        reducer_shard, events = _load_reducer_arm(arm)
        groups = _group_by_window(events)
        max_events_per_shard = max(max_events_per_shard, *(len(group) for group in groups))
        expected_root = str(reducer_shard["final_state_root_sha256"])
        scenarios: dict[str, dict[str, Any]] = {}
        for scenario in SCENARIOS:
            receipt = _scenario(
                output_dir=output_dir,
                arm=arm,
                scenario=scenario,
                identity=identity,
                reducer_shard=reducer_shard,
                groups=groups,
            )
            if receipt["final_state_root_sha256"] != expected_root:
                raise ResumeError("resume_final_state_root_mismatch")
            _relativize_entries(receipt["checkpoints"], output_dir)
            scenarios[scenario] = receipt
        arms[arm] = {
            "expected_final_state_root_sha256": expected_root,
            "scenarios": scenarios,
        }
    if max_events_per_shard != 4:
        raise ResumeError("unexpected_atomic_shard_bound")
    with tempfile.TemporaryDirectory(prefix="gtos-resume-failure-") as temporary:
        failures = run_resume_failure_injections(Path(temporary))
    resume_route_payload = {
        "identity_root_sha256": stable_sha256(identity),
        "arms": [
            {
                "arm_id": arm,
                "expected_final_state_root_sha256": arms[arm][
                    "expected_final_state_root_sha256"
                ],
                "scenario_roots": [
                    {
                        "scenario": scenario,
                        "root_sha256": arms[arm]["scenarios"][scenario][
                            "scenario_root_sha256"
                        ],
                    }
                    for scenario in SCENARIOS
                ],
            }
            for arm in ARMS
        ],
    }
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    writer_path = Path(__file__).resolve()
    verifier_path = writer_path.with_name("replay_acceleration_resume_verifier.py")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "COMPLETE_RESUME_SEMANTICS_ACCEPTED",
        "identity": identity,
        "identity_root_sha256": stable_sha256(identity),
        "arms": arms,
        "max_events_per_atomic_shard": max_events_per_shard,
        "restart_loss_bound": "one_unsealed_decision_window_shard",
        "failure_injections": failures,
        "resume_route_root_sha256": stable_sha256(resume_route_payload),
        "predecessors": {
            "reducer": {
                "path": REDUCER_RESULT_PATH.as_posix(),
                "file_sha256": file_sha256(REDUCER_RESULT_PATH),
                "result_root_sha256": json.loads(REDUCER_RESULT_PATH.read_bytes())[
                    "result_root_sha256"
                ],
            },
            "typed_proof": {
                "path": TYPED_RESULT_PATH.as_posix(),
                "file_sha256": file_sha256(TYPED_RESULT_PATH),
                "result_root_sha256": json.loads(TYPED_RESULT_PATH.read_bytes())[
                    "result_root_sha256"
                ],
            },
        },
        "measurement": {
            "scope": "bounded_checkpoint_resume_only",
            "wall_ns": time.perf_counter_ns() - wall_start,
            "cpu_ns": time.process_time_ns() - cpu_start,
            "peak_rss_native": int(usage_after.ru_maxrss),
            "peak_rss_unit": "bytes_on_darwin_kib_elsewhere",
            "minor_page_faults": int(usage_after.ru_minflt - usage_before.ru_minflt),
            "major_page_faults": int(usage_after.ru_majflt - usage_before.ru_majflt),
            "blocks_read": int(usage_after.ru_inblock - usage_before.ru_inblock),
            "blocks_written": int(usage_after.ru_oublock - usage_before.ru_oublock),
            "whole_replay_speed_claim": False,
        },
        "code_identity": {
            "writer_path": writer_path.relative_to(Path.cwd()).as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.relative_to(Path.cwd()).as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
        },
        "execution": {
            "policy_callbacks_invoked": False,
            "successor_arm_execution_launched": False,
            "structural_resume_only": True,
        },
        "exact_command_receipt": [
            sys.executable,
            "-m",
            __name__,
            "--output-dir",
            output_dir.as_posix(),
        ],
    }
    result["result_root_sha256"] = stable_sha256(result)
    result_path = output_dir / "RESUME_RESULT.json"
    _atomic_json(result_path, result)
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    result_path = write_resume_result(args.output_dir)
    payload = json.loads(result_path.read_bytes())
    print(
        json.dumps(
            {
                "gate": payload["gate"],
                "resume_route_root_sha256": payload["resume_route_root_sha256"],
                "result_root_sha256": payload["result_root_sha256"],
                "output": result_path.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
