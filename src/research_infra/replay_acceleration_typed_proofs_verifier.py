"""Independent stdlib verifier for GTOS typed structural proof bytes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import struct
import tempfile
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
ACTION_NAMES = {
    1: "enqueue",
    2: "reserve",
    3: "submit",
    4: "activate",
    5: "replace_pending",
    6: "memory_update",
    7: "close",
    8: "seal",
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
MEMORY_KEYS = {1: "bounded_structural_memory"}


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


def _hex_or_none(value: bytes) -> str | None:
    return None if value == ZERO_HASH else value.hex()


def _group_roots(groups: Mapping[Any, list[str]], field: str) -> dict[str, str]:
    return {
        str(key): _root({field: key, "record_roots_sha256": roots})
        for key, roots in sorted(groups.items(), key=lambda item: str(item[0]))
    }


def _reconstruct_projection(
    *,
    arm: str,
    day: str,
    cursor: list[int],
    action: str,
    aux_code: int,
    primary: bytes,
    secondary: bytes,
    auxiliary: bytes,
) -> dict[str, Any]:
    projection: dict[str, Any] = {
        "action": action,
        "arm_namespace": arm,
        "cursor": cursor,
        "selected_day": day,
    }
    if action == "replace_pending":
        _require(primary != ZERO_HASH and secondary != ZERO_HASH, "typed_replacement_hash_missing")
        projection["old_candidate"] = primary.hex()
        projection["new_candidate"] = secondary.hex()
        _require(auxiliary != ZERO_HASH, "typed_replacement_reservation_missing")
        projection["reservation_id"] = auxiliary.hex()
    elif action == "memory_update":
        _require(primary == ZERO_HASH and secondary == ZERO_HASH, "typed_memory_candidate_present")
        _require(auxiliary != ZERO_HASH, "typed_memory_value_missing")
        _require(aux_code in MEMORY_KEYS, "typed_memory_key_code_unknown")
        projection["memory_key"] = MEMORY_KEYS[aux_code]
        projection["memory_value"] = auxiliary.hex()
    else:
        _require(aux_code == 0, "typed_aux_code_without_memory")
        if primary != ZERO_HASH:
            projection["candidate"] = primary.hex()
        _require(secondary == ZERO_HASH, "typed_secondary_hash_unexpected")
        if auxiliary != ZERO_HASH:
            _require(action == "reserve", "typed_auxiliary_hash_unexpected")
            projection["reservation_id"] = auxiliary.hex()
    return projection


def _verify_arm_shard(
    *,
    result_path: Path,
    result: Mapping[str, Any],
    arm: str,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    typed_path = result_path.parent / str(manifest["typed_path"])
    projection_path = result_path.parent / str(manifest["legacy_projection_path"])
    _require(typed_path.is_file(), "typed_file_missing")
    _require(projection_path.is_file(), "projection_file_missing")
    _require(_file_hash(typed_path) == manifest.get("typed_file_sha256"), "typed_file_hash_mismatch")
    _require(
        _file_hash(projection_path) == manifest.get("legacy_projection_sha256"),
        "projection_file_hash_mismatch",
    )
    typed_size = typed_path.stat().st_size
    with typed_path.open("rb") as typed_handle, projection_path.open("rb") as projection_handle:
        header_bytes = typed_handle.read(HEADER.size)
        _require(len(header_bytes) == HEADER.size, "typed_header_truncated")
        (
            magic,
            version,
            raw_arm,
            raw_day,
            schema_hash,
            source_root,
            candidate_root,
            reducer_root,
            record_count,
        ) = HEADER.unpack(header_bytes)
        _require(magic == MAGIC, "header_magic_mismatch")
        _require(version == VERSION, "header_version_mismatch")
        _require(raw_arm.decode("ascii") == arm, "header_arm_mismatch")
        day = raw_day.decode("ascii")
        _require(schema_hash == FORMAT_SCHEMA_HASH, "header_schema_mismatch")
        _require(
            source_root.hex()
            == result["reducer_predecessor_source_barrier_root_sha256"],
            "header_source_root_mismatch",
        )
        _require(
            candidate_root.hex()
            == result["reducer_predecessor_candidate_base_root_sha256"],
            "header_candidate_root_mismatch",
        )
        _require(reducer_root.hex() == manifest["reducer_state_root_sha256"], "header_reducer_root_mismatch")
        _require(record_count == manifest.get("record_count"), "header_record_count_mismatch")
        _require(
            typed_size == HEADER.size + record_count * RECORD.size,
            "typed_file_size_mismatch",
        )
        _require(hashlib.sha256(header_bytes).hexdigest() == manifest.get("header_sha256"), "header_hash_mismatch")
        window_groups: dict[int, list[str]] = {}
        ledger_groups: dict[str, list[str]] = {}
        prior_cursor: tuple[int, int, int] | None = None
        for expected_sequence in range(record_count):
            raw_record = typed_handle.read(RECORD.size)
            _require(len(raw_record) == RECORD.size, "typed_record_truncated")
            (
                sequence,
                day_index,
                window_index,
                event_index,
                action_code,
                ledger_code,
                aux_code,
                flags,
                primary,
                secondary,
                auxiliary,
                projection_hash,
            ) = RECORD.unpack(raw_record)
            _require(sequence == expected_sequence, "record_sequence_mismatch")
            cursor = (day_index, window_index, event_index)
            _require(prior_cursor is None or cursor > prior_cursor, "record_cursor_not_increasing")
            prior_cursor = cursor
            _require(action_code in ACTION_NAMES, "record_action_unknown")
            action = ACTION_NAMES[action_code]
            ledger_name = LEDGER_NAMES[action]
            _require(ledger_code == LEDGER_CODES[ledger_name], "record_ledger_code_mismatch")
            _require(flags == 0, "record_flags_nonzero")
            projection = _reconstruct_projection(
                arm=arm,
                day=day,
                cursor=list(cursor),
                action=action,
                aux_code=aux_code,
                primary=primary,
                secondary=secondary,
                auxiliary=auxiliary,
            )
            projection_bytes = _canonical(projection)
            _require(
                hashlib.sha256(projection_bytes).digest() == projection_hash,
                "record_projection_hash_mismatch",
            )
            _require(
                projection_handle.readline() == projection_bytes + b"\n",
                "legacy_projection_roundtrip_mismatch",
            )
            record_root = hashlib.sha256(raw_record).hexdigest()
            window_groups.setdefault(window_index, []).append(record_root)
            ledger_groups.setdefault(ledger_name, []).append(record_root)
        _require(typed_handle.read(1) == b"", "typed_trailing_bytes")
        _require(projection_handle.read(1) == b"", "projection_trailing_bytes")
    window_roots = _group_roots(window_groups, "window_index")
    ledger_roots = _group_roots(ledger_groups, "ledger")
    _require(window_roots == manifest.get("window_roots"), "window_roots_mismatch")
    _require(ledger_roots == manifest.get("ledger_roots"), "ledger_roots_mismatch")
    day_payload = {
        "arm_id": arm,
        "selected_day": day,
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "typed_file_sha256": _file_hash(typed_path),
        "legacy_projection_sha256": _file_hash(projection_path),
        "window_roots": window_roots,
        "ledger_roots": ledger_roots,
        "record_count": record_count,
    }
    day_root = _root(day_payload)
    _require(day_root == manifest.get("day_root_sha256"), "day_root_mismatch")
    return {"record_count": record_count, "day_root_sha256": day_root}


def verify_typed_proof_result(result_path: Path) -> dict[str, Any]:
    raw = result_path.read_bytes()
    _require(raw.endswith(b"\n"), "result_newline_missing")
    try:
        source_result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("result_json_invalid") from exc
    _require(source_result.get("schema") == SCHEMA, "result_schema_mismatch")
    _require(source_result.get("status") == "ACCEPTED", "result_status_invalid")
    _require(source_result.get("gate") == "TYPED_STREAMING_PROOF_PLANE_ACCEPTED", "result_gate_mismatch")
    recorded_root = source_result.get("result_root_sha256")
    root_payload = dict(source_result)
    root_payload.pop("result_root_sha256", None)
    _require(recorded_root == _root(root_payload), "result_root_mismatch")
    predecessor = source_result.get("reducer_predecessor") or {}
    predecessor_path = Path(str(predecessor.get("path") or ""))
    _require(predecessor_path.is_file(), "reducer_predecessor_missing")
    _require(_file_hash(predecessor_path) == predecessor.get("file_sha256"), "reducer_predecessor_hash_mismatch")
    predecessor_payload = json.loads(predecessor_path.read_bytes())
    result = dict(source_result)
    result["reducer_predecessor_source_barrier_root_sha256"] = predecessor_payload[
        "cross_symbol_barrier"
    ]["source_barrier_root_sha256"]
    result["reducer_predecessor_candidate_base_root_sha256"] = predecessor_payload[
        "candidate_base_root_sha256"
    ]
    arms = result.get("arms") or {}
    _require(set(arms) == set(ARMS), "arm_manifest_invalid")
    record_total = 0
    arm_day_roots: list[dict[str, str]] = []
    for arm in ARMS:
        reducer_manifest = predecessor_payload["arms"][arm]
        manifest = dict(arms[arm])
        manifest["reducer_state_root_sha256"] = reducer_manifest[
            "final_state_root_sha256"
        ]
        verified = _verify_arm_shard(
            result_path=result_path,
            result=result,
            arm=arm,
            manifest=manifest,
        )
        record_total += verified["record_count"]
        arm_day_roots.append(
            {"arm_id": arm, "day_root_sha256": verified["day_root_sha256"]}
        )
    campaign_payload = {
        "schema": FORMAT_SCHEMA,
        "reducer_result_root_sha256": predecessor_payload["result_root_sha256"],
        "source_barrier_root_sha256": result[
            "reducer_predecessor_source_barrier_root_sha256"
        ],
        "candidate_base_root_sha256": result[
            "reducer_predecessor_candidate_base_root_sha256"
        ],
        "arm_day_roots": arm_day_roots,
    }
    _require(
        _root(campaign_payload) == result.get("campaign_root_sha256"),
        "campaign_root_mismatch",
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
        "record_count": record_total,
        "projection_roundtrip_exact": True,
        "campaign_root_sha256": result["campaign_root_sha256"],
        "result_root_sha256": recorded_root,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _mutate_file(path: Path, mutation: str) -> None:
    data = bytearray(path.read_bytes())
    if mutation == "bit_flip":
        data[HEADER.size + RECORD.size - 1] ^= 1
    elif mutation == "truncation":
        data = data[:-1]
    elif mutation == "append":
        data.extend(b"X")
    elif mutation == "record_reorder":
        first = bytes(data[HEADER.size : HEADER.size + RECORD.size])
        second = bytes(data[HEADER.size + RECORD.size : HEADER.size + 2 * RECORD.size])
        data[HEADER.size : HEADER.size + RECORD.size] = second
        data[HEADER.size + RECORD.size : HEADER.size + 2 * RECORD.size] = first
    elif mutation == "wrong_arm":
        data[10:14] = b"XXXX"
    elif mutation == "wrong_schema":
        data[24] ^= 1
    elif mutation == "wrong_source":
        data[56] ^= 1
    else:
        raise VerificationError("failure_mutation_unknown")
    path.write_bytes(data)


def run_typed_failure_injection_matrix(result_path: Path) -> list[dict[str, str]]:
    expected = {
        "bit_flip": "typed_file_hash_mismatch",
        "truncation": "typed_file_hash_mismatch",
        "append": "typed_file_hash_mismatch",
        "projection_mismatch": "projection_file_hash_mismatch",
        "record_reorder": "record_sequence_mismatch",
        "wrong_arm": "header_arm_mismatch",
        "wrong_schema": "header_schema_mismatch",
        "wrong_source": "header_source_root_mismatch",
    }
    verdicts: list[dict[str, str]] = []
    for case, expected_code in expected.items():
        with tempfile.TemporaryDirectory(prefix="gtos-typed-proof-injection-") as temp:
            copied_root = Path(temp) / "route"
            shutil.copytree(result_path.parent, copied_root)
            copied_result_path = copied_root / result_path.name
            result = json.loads(copied_result_path.read_bytes())
            predecessor_path = Path(result["reducer_predecessor"]["path"])
            predecessor = json.loads(predecessor_path.read_bytes())
            arm = "S0R0"
            manifest = copy.deepcopy(result["arms"][arm])
            manifest["reducer_state_root_sha256"] = predecessor["arms"][arm][
                "final_state_root_sha256"
            ]
            typed_path = copied_root / manifest["typed_path"]
            projection_path = copied_root / manifest["legacy_projection_path"]
            if case == "projection_mismatch":
                projection = bytearray(projection_path.read_bytes())
                projection[0] ^= 1
                projection_path.write_bytes(projection)
            else:
                _mutate_file(typed_path, case)
                if case in {"record_reorder", "wrong_arm", "wrong_schema", "wrong_source"}:
                    manifest["typed_file_sha256"] = _file_hash(typed_path)
                    if case in {"wrong_arm", "wrong_schema", "wrong_source"}:
                        manifest["header_sha256"] = hashlib.sha256(
                            typed_path.read_bytes()[: HEADER.size]
                        ).hexdigest()
            verifier_result = dict(result)
            verifier_result["reducer_predecessor_source_barrier_root_sha256"] = predecessor[
                "cross_symbol_barrier"
            ]["source_barrier_root_sha256"]
            verifier_result["reducer_predecessor_candidate_base_root_sha256"] = predecessor[
                "candidate_base_root_sha256"
            ]
            try:
                _verify_arm_shard(
                    result_path=copied_result_path,
                    result=verifier_result,
                    arm=arm,
                    manifest=manifest,
                )
            except VerificationError as exc:
                if str(exc) != expected_code:
                    raise VerificationError("failure_injection_wrong_rejection") from exc
                verdicts.append(
                    {
                        "case": case,
                        "status": "REJECTED_AS_REQUIRED",
                        "code": expected_code,
                    }
                )
            else:
                raise VerificationError("failure_injection_not_rejected")
    return verdicts


def _atomic_receipt(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(_canonical(payload) + b"\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--failure-receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_typed_proof_result(args.result)
    if args.receipt:
        _atomic_receipt(args.receipt, receipt)
    if args.failure_receipt:
        _atomic_receipt(args.failure_receipt, run_typed_failure_injection_matrix(args.result))
    print(_canonical(receipt).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
