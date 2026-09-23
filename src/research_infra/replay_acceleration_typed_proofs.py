"""Bounded typed streaming proof shards for replay acceleration.

The binary format carries only structural reducer events.  It is fixed-width,
streamed one record at a time, and paired with an exact allowlisted JSONL
projection so independent consumers can prove legacy-projection equivalence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import struct
import sys
import time
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.typed_proof_result.v1"
FORMAT_SCHEMA = "gtos.replay_acceleration.typed_day_shard.v1"
MAGIC = b"GTOSPF01"
VERSION = 1
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")
HEADER = struct.Struct(">8sH4s10s32s32s32s32sI")
RECORD = struct.Struct(">IHHHBBBB32s32s32s32s")
FORMAT_SCHEMA_HASH = hashlib.sha256(FORMAT_SCHEMA.encode("ascii")).digest()
ZERO_HASH = b"\x00" * 32
REDUCER_RESULT_PATH = Path(
    "research/operations/replay_acceleration_isolated_reducers_2026_07_19/"
    "ISOLATED_REDUCER_RESULT.json"
)

ACTION_CODES = {
    "enqueue": 1,
    "reserve": 2,
    "submit": 3,
    "activate": 4,
    "replace_pending": 5,
    "memory_update": 6,
    "close": 7,
    "seal": 8,
}
LEDGER_NAMES = {
    "enqueue": "queue",
    "reserve": "queue",
    "submit": "broker",
    "activate": "broker",
    "replace_pending": "lifecycle",
    "close": "lifecycle",
    "memory_update": "adaptive",
    "seal": "seal",
}
LEDGER_CODES = {name: index + 1 for index, name in enumerate(sorted(set(LEDGER_NAMES.values())))}
PROJECTION_FIELDS = (
    "action",
    "arm_namespace",
    "candidate",
    "cursor",
    "memory_key",
    "memory_value",
    "new_candidate",
    "old_candidate",
    "reservation_id",
    "selected_day",
)
MEMORY_KEYS = {"bounded_structural_memory": 1}


class TypedProofError(RuntimeError):
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


def _decode_hash(value: Any, *, allow_empty: bool = True) -> bytes:
    text = str(value or "")
    if not text and allow_empty:
        return ZERO_HASH
    if len(text) != 64:
        raise TypedProofError("typed_hash_invalid")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise TypedProofError("typed_hash_invalid") from exc


def _projection(event: Mapping[str, Any]) -> dict[str, Any]:
    return {field: event[field] for field in PROJECTION_FIELDS if field in event}


def _pack_record(sequence: int, event: Mapping[str, Any]) -> tuple[bytes, bytes, int, str]:
    action = str(event.get("action") or "")
    if action not in ACTION_CODES:
        raise TypedProofError("typed_action_unknown")
    cursor = event.get("cursor")
    if not isinstance(cursor, list) or len(cursor) != 3:
        raise TypedProofError("typed_cursor_invalid")
    ledger_name = LEDGER_NAMES[action]
    memory_key = str(event.get("memory_key") or "")
    aux_code = MEMORY_KEYS.get(memory_key, 0)
    if action == "memory_update" and aux_code == 0:
        raise TypedProofError("typed_memory_key_unknown")
    projection = _projection(event)
    projection_bytes = canonical_bytes(projection)
    packed = RECORD.pack(
        sequence,
        int(cursor[0]),
        int(cursor[1]),
        int(cursor[2]),
        ACTION_CODES[action],
        LEDGER_CODES[ledger_name],
        aux_code,
        0,
        _decode_hash(event.get("candidate") or event.get("old_candidate")),
        _decode_hash(event.get("new_candidate")),
        _decode_hash(event.get("reservation_id") or event.get("memory_value")),
        hashlib.sha256(projection_bytes).digest(),
    )
    return packed, projection_bytes, int(cursor[1]), ledger_name


def _root_groups(groups: Mapping[Any, list[str]], field: str) -> dict[str, str]:
    return {
        str(key): stable_sha256({field: key, "record_roots_sha256": roots})
        for key, roots in sorted(groups.items(), key=lambda item: str(item[0]))
    }


def _write_arm_shard(
    *,
    output_dir: Path,
    arm_id: str,
    reducer_shard: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    events = reducer_shard.get("events")
    if not isinstance(events, list) or not events:
        raise TypedProofError("reducer_events_missing")
    barrier = reducer_shard.get("source_barrier") or {}
    source_root = str(barrier.get("source_barrier_root_sha256") or "")
    candidate_root = str(reducer_shard.get("candidate_base_root_sha256") or "")
    reducer_root = str(reducer_shard.get("final_state_root_sha256") or "")
    selected_day = str(barrier.get("selected_day") or "")
    if len(selected_day.encode("ascii")) != 10:
        raise TypedProofError("selected_day_invalid")
    header = HEADER.pack(
        MAGIC,
        VERSION,
        arm_id.encode("ascii"),
        selected_day.encode("ascii"),
        FORMAT_SCHEMA_HASH,
        _decode_hash(source_root, allow_empty=False),
        _decode_hash(candidate_root, allow_empty=False),
        _decode_hash(reducer_root, allow_empty=False),
        len(events),
    )
    typed_path = output_dir / "shards" / f"{arm_id}.day.gtp"
    projection_path = output_dir / "projections" / f"{arm_id}.legacy.jsonl"
    typed_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    typed_tmp = typed_path.with_name(f".{typed_path.name}.tmp-{os.getpid()}")
    projection_tmp = projection_path.with_name(
        f".{projection_path.name}.tmp-{os.getpid()}"
    )
    window_groups: dict[int, list[str]] = {}
    ledger_groups: dict[str, list[str]] = {}
    timings = {
        "record_encoding_ns": 0,
        "projection_serialization_ns": 0,
        "record_hashing_ns": 0,
        "stream_write_ns": 0,
    }
    projection_bytes_total = 0
    with typed_tmp.open("wb") as typed_handle, projection_tmp.open("wb") as projection_handle:
        write_start = time.perf_counter_ns()
        typed_handle.write(header)
        timings["stream_write_ns"] += time.perf_counter_ns() - write_start
        for sequence, event in enumerate(events):
            encode_start = time.perf_counter_ns()
            packed, projected, window_index, ledger_name = _pack_record(sequence, event)
            timings["record_encoding_ns"] += time.perf_counter_ns() - encode_start
            serialization_start = time.perf_counter_ns()
            projected_line = projected + b"\n"
            timings["projection_serialization_ns"] += (
                time.perf_counter_ns() - serialization_start
            )
            hash_start = time.perf_counter_ns()
            record_root = hashlib.sha256(packed).hexdigest()
            timings["record_hashing_ns"] += time.perf_counter_ns() - hash_start
            window_groups.setdefault(window_index, []).append(record_root)
            ledger_groups.setdefault(ledger_name, []).append(record_root)
            write_start = time.perf_counter_ns()
            typed_handle.write(packed)
            projection_handle.write(projected_line)
            timings["stream_write_ns"] += time.perf_counter_ns() - write_start
            projection_bytes_total += len(projected_line)
        typed_handle.flush()
        projection_handle.flush()
        os.fsync(typed_handle.fileno())
        os.fsync(projection_handle.fileno())
    os.replace(typed_tmp, typed_path)
    os.replace(projection_tmp, projection_path)
    roots_start = time.perf_counter_ns()
    window_roots = _root_groups(window_groups, "window_index")
    ledger_roots = _root_groups(ledger_groups, "ledger")
    typed_hash = file_sha256(typed_path)
    projection_hash = file_sha256(projection_path)
    day_payload = {
        "arm_id": arm_id,
        "selected_day": selected_day,
        "header_sha256": hashlib.sha256(header).hexdigest(),
        "typed_file_sha256": typed_hash,
        "legacy_projection_sha256": projection_hash,
        "window_roots": window_roots,
        "ledger_roots": ledger_roots,
        "record_count": len(events),
    }
    day_root = stable_sha256(day_payload)
    timings["root_building_ns"] = time.perf_counter_ns() - roots_start
    typed_record_bytes = len(events) * RECORD.size
    if typed_record_bytes >= projection_bytes_total:
        raise TypedProofError("typed_record_bytes_not_below_projection_bytes")
    return (
        {
            "typed_path": typed_path.relative_to(output_dir).as_posix(),
            "legacy_projection_path": projection_path.relative_to(output_dir).as_posix(),
            "typed_file_sha256": typed_hash,
            "legacy_projection_sha256": projection_hash,
            "header_sha256": hashlib.sha256(header).hexdigest(),
            "record_count": len(events),
            "header_bytes": HEADER.size,
            "typed_record_bytes": typed_record_bytes,
            "typed_total_bytes": typed_path.stat().st_size,
            "legacy_projection_bytes": projection_bytes_total,
            "window_roots": window_roots,
            "ledger_roots": ledger_roots,
            "day_root_sha256": day_root,
        },
        timings,
    )


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    os.replace(temporary, path)


def write_typed_proof_result(output_dir: Path) -> Path:
    reducer_raw = REDUCER_RESULT_PATH.read_bytes()
    reducer_result = json.loads(reducer_raw)
    if reducer_result.get("gate") != "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED":
        raise TypedProofError("reducer_predecessor_not_accepted")
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.perf_counter_ns()
    process_start = time.process_time_ns()
    arms: dict[str, dict[str, Any]] = {}
    stage_ns: dict[str, int] = {}
    for arm in ARMS:
        reducer_manifest = reducer_result["arms"][arm]
        reducer_path = REDUCER_RESULT_PATH.parent / reducer_manifest["path"]
        if file_sha256(reducer_path) != reducer_manifest["file_sha256"]:
            raise TypedProofError("reducer_shard_hash_mismatch")
        reducer_shard = json.loads(reducer_path.read_bytes())
        arm_manifest, timings = _write_arm_shard(
            output_dir=output_dir,
            arm_id=arm,
            reducer_shard=reducer_shard,
        )
        arms[arm] = arm_manifest
        for key, value in timings.items():
            stage_ns[key] = stage_ns.get(key, 0) + value
    campaign_payload = {
        "schema": FORMAT_SCHEMA,
        "reducer_result_root_sha256": reducer_result["result_root_sha256"],
        "source_barrier_root_sha256": reducer_result["cross_symbol_barrier"][
            "source_barrier_root_sha256"
        ],
        "candidate_base_root_sha256": reducer_result["candidate_base_root_sha256"],
        "arm_day_roots": [
            {"arm_id": arm, "day_root_sha256": arms[arm]["day_root_sha256"]}
            for arm in ARMS
        ],
    }
    campaign_root = stable_sha256(campaign_payload)
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    writer_path = Path(__file__).resolve()
    verifier_path = writer_path.with_name("replay_acceleration_typed_proofs_verifier.py")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "TYPED_STREAMING_PROOF_PLANE_ACCEPTED",
        "format": {
            "schema": FORMAT_SCHEMA,
            "magic_ascii": MAGIC.decode("ascii"),
            "version": VERSION,
            "header_bytes": HEADER.size,
            "record_bytes": RECORD.size,
            "encoding": "fixed_width_big_endian",
            "compression": "none_for_bounded_equivalence",
        },
        "arms": arms,
        "campaign_root_sha256": campaign_root,
        "reducer_predecessor": {
            "path": REDUCER_RESULT_PATH.as_posix(),
            "file_sha256": hashlib.sha256(reducer_raw).hexdigest(),
            "result_root_sha256": reducer_result["result_root_sha256"],
        },
        "measurement": {
            "scope": "typed_structural_proof_serialization_only",
            "wall_ns": time.perf_counter_ns() - wall_start,
            "cpu_ns": time.process_time_ns() - process_start,
            "stage_ns": stage_ns,
            "peak_rss_native": int(usage_after.ru_maxrss),
            "peak_rss_unit": "bytes_on_darwin_kib_elsewhere",
            "minor_page_faults": int(usage_after.ru_minflt - usage_before.ru_minflt),
            "major_page_faults": int(usage_after.ru_majflt - usage_before.ru_majflt),
            "blocks_read": int(usage_after.ru_inblock - usage_before.ru_inblock),
            "blocks_written": int(usage_after.ru_oublock - usage_before.ru_oublock),
            "whole_replay_speed_claim": False,
        },
        "failure_injection_cases_required": [
            "append",
            "bit_flip",
            "projection_mismatch",
            "record_reorder",
            "truncation",
            "wrong_arm",
            "wrong_schema",
            "wrong_source",
        ],
        "code_identity": {
            "writer_path": writer_path.relative_to(Path.cwd()).as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.relative_to(Path.cwd()).as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
        },
        "execution": {
            "policy_callbacks_invoked": False,
            "successor_arm_execution_launched": False,
            "structural_proof_only": True,
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
    result_path = output_dir / "TYPED_PROOF_RESULT.json"
    _atomic_json(result_path, result)
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    result_path = write_typed_proof_result(args.output_dir)
    result = json.loads(result_path.read_bytes())
    print(
        json.dumps(
            {
                "gate": result["gate"],
                "campaign_root_sha256": result["campaign_root_sha256"],
                "result_root_sha256": result["result_root_sha256"],
                "output": result_path.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
