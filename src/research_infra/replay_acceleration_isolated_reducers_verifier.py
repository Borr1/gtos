"""Independent stdlib replay of persisted isolated-reducer shards."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.replay_acceleration.isolated_reducer_result.v1"
SHARD_SCHEMA = "gtos.replay_acceleration.isolated_reducer_shard.v1"
ARMS = ("S0R0", "S1R0", "S0R1", "S1R1")


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


def _token(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def _initial_state(shard: Mapping[str, Any]) -> dict[str, Any]:
    arm = str(shard["arm_id"])
    barrier = shard["source_barrier"]
    day = str(barrier["selected_day"])
    return {
        "arm_id": arm,
        "candidate_base_root": shard["candidate_base_root_sha256"],
        "source_barrier_root": barrier["source_barrier_root_sha256"],
        "selected_day": day,
        "binding_projection_sha256": shard["final_state"]["binding_projection_sha256"],
        "account": {"active_day": day, "processed_windows": [], "event_count": 0},
        "broker": {},
        "queue": [],
        "pending": {},
        "open": {},
        "closed": {},
        "reservations": {},
        "risk_counters": {},
        "adaptive_memory": {},
        "replacement": {},
        "candidate_orders": {},
        "order_sequence": 0,
        "last_cursor": None,
        "sealed": False,
        "ledger": [],
    }


def _refresh(state: dict[str, Any]) -> None:
    state["risk_counters"] = {
        "queued_slots": len(state["queue"]),
        "pending_slots": len(state["pending"]),
        "open_slots": len(state["open"]),
        "closed_lifecycle_count": len(state["closed"]),
        "reservation_slots": len(state["reservations"]),
        "replacement_count": len(state["replacement"]),
    }


def _find_order(state: Mapping[str, Any], candidate: str, status: str) -> str:
    order_id = state["candidate_orders"].get(candidate)
    _require(
        bool(order_id) and state["broker"].get(order_id, {}).get("status") == status,
        "persisted_transition_order_missing",
    )
    return str(order_id)


def _replay(shard: Mapping[str, Any]) -> dict[str, Any]:
    state = _initial_state(shard)
    _refresh(state)
    last_cursor: tuple[int, int, int] | None = None
    for event in shard["events"]:
        _require(not state["sealed"], "persisted_event_after_seal")
        _require(event.get("arm_namespace") == state["arm_id"], "persisted_arm_namespace_mismatch")
        _require(
            event.get("source_barrier_root") == state["source_barrier_root"],
            "persisted_barrier_mismatch",
        )
        _require(
            event.get("candidate_base_root") == state["candidate_base_root"],
            "persisted_candidate_root_mismatch",
        )
        _require(event.get("selected_day") == state["selected_day"], "persisted_day_mismatch")
        raw_cursor = event.get("cursor")
        _require(
            isinstance(raw_cursor, list)
            and len(raw_cursor) == 3
            and all(isinstance(item, int) and not isinstance(item, bool) for item in raw_cursor),
            "persisted_cursor_invalid",
        )
        cursor = tuple(raw_cursor)
        _require(last_cursor is None or cursor > last_cursor, "persisted_cursor_not_increasing")
        last_cursor = cursor
        state["last_cursor"] = list(cursor)
        window = f"W{cursor[1]:03d}"
        if window not in state["account"]["processed_windows"]:
            state["account"]["processed_windows"].append(window)
        action = str(event.get("action") or "")
        candidate = str(event.get("candidate") or "")
        if action == "enqueue":
            _require(
                candidate
                and candidate not in state["candidate_orders"]
                and candidate not in state["queue"],
                "persisted_enqueue_invalid",
            )
            state["queue"].append(candidate)
        elif action == "reserve":
            _require(
                candidate in state["queue"] and candidate not in state["reservations"],
                "persisted_reservation_invalid",
            )
            state["reservations"][candidate] = event["reservation_id"]
        elif action == "submit":
            _require(
                candidate in state["queue"] and candidate in state["reservations"],
                "persisted_submit_invalid",
            )
            state["queue"].remove(candidate)
            state["order_sequence"] += 1
            order_id = _token(state["arm_id"], state["order_sequence"], candidate)
            state["candidate_orders"][candidate] = order_id
            state["broker"][order_id] = {
                "sequence": state["order_sequence"],
                "candidate": candidate,
                "status": "pending",
            }
            state["pending"][order_id] = candidate
        elif action == "activate":
            order_id = _find_order(state, candidate, "pending")
            state["pending"].pop(order_id)
            state["open"][order_id] = candidate
            state["broker"][order_id]["status"] = "open"
        elif action == "replace_pending":
            old = str(event.get("old_candidate") or "")
            new = str(event.get("new_candidate") or "")
            old_order = state["candidate_orders"].get(old)
            _require(bool(old_order) and old_order in state["pending"], "persisted_replacement_invalid")
            state["pending"].pop(old_order)
            state["broker"][old_order]["status"] = "replaced"
            state["reservations"].pop(old, None)
            state["replacement"][old] = new
            state["reservations"][new] = event["reservation_id"]
            state["order_sequence"] += 1
            new_order = _token(state["arm_id"], state["order_sequence"], new)
            state["candidate_orders"][new] = new_order
            state["broker"][new_order] = {
                "sequence": state["order_sequence"],
                "candidate": new,
                "status": "pending",
            }
            state["pending"][new_order] = new
        elif action == "memory_update":
            state["adaptive_memory"][event["memory_key"]] = event["memory_value"]
        elif action == "close":
            order_id = _find_order(state, candidate, "open")
            state["open"].pop(order_id)
            state["closed"][order_id] = candidate
            state["broker"][order_id]["status"] = "closed"
            state["reservations"].pop(candidate, None)
        elif action == "seal":
            _require(not state["queue"], "persisted_seal_queue_nonempty")
            state["sealed"] = True
        else:
            raise VerificationError("persisted_action_unknown")
        state["account"]["event_count"] += 1
        _refresh(state)
        state["ledger"].append(
            {
                "cursor": list(cursor),
                "action": action,
                "candidate": candidate or None,
                "old_candidate": event.get("old_candidate"),
                "new_candidate": event.get("new_candidate"),
            }
        )
    return state


def _neutral(state: Mapping[str, Any]) -> dict[str, Any]:
    broker = [
        {
            "sequence": record["sequence"],
            "candidate": record["candidate"],
            "status": record["status"],
        }
        for _, record in sorted(
            state["broker"].items(), key=lambda item: int(item[1]["sequence"])
        )
    ]
    return {
        "candidate_base_root": state["candidate_base_root"],
        "source_barrier_root": state["source_barrier_root"],
        "selected_day": state["selected_day"],
        "account": state["account"],
        "broker": broker,
        "queue": state["queue"],
        "pending_candidates": sorted(state["pending"].values()),
        "open_candidates": sorted(state["open"].values()),
        "closed_candidates": sorted(state["closed"].values()),
        "reservation_candidates": sorted(state["reservations"]),
        "risk_counters": state["risk_counters"],
        "adaptive_memory": state["adaptive_memory"],
        "replacement": state["replacement"],
        "order_sequence": state["order_sequence"],
        "last_cursor": state["last_cursor"],
        "sealed": state["sealed"],
        "ledger": state["ledger"],
    }


def verify_isolated_reducer_result(result_path: Path) -> dict[str, Any]:
    raw = result_path.read_bytes()
    _require(raw.endswith(b"\n"), "result_newline_missing")
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("result_json_invalid") from exc
    _require(result.get("schema") == SCHEMA, "result_schema_mismatch")
    _require(result.get("status") == "ACCEPTED", "result_status_invalid")
    _require(
        result.get("gate") == "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED",
        "result_gate_mismatch",
    )
    recorded = result.get("result_root_sha256")
    root_payload = dict(result)
    root_payload.pop("result_root_sha256", None)
    _require(recorded == _root(root_payload), "result_root_mismatch")
    _require(tuple(result.get("arm_order") or ()) == ARMS, "arm_order_mismatch")
    barrier = result.get("cross_symbol_barrier") or {}
    _require(
        barrier.get("symbol_count") == 24
        and barrier.get("logical_partition_count") == 120
        and barrier.get("all_symbols_preprocessed_before_mutable_reduction") is True,
        "barrier_scope_invalid",
    )
    arm_manifest = result.get("arms") or {}
    _require(set(arm_manifest) == set(ARMS), "arm_manifest_invalid")
    state_roots: set[str] = set()
    neutral_roots: set[str] = set()
    for arm in ARMS:
        manifest = arm_manifest[arm]
        shard_path = result_path.parent / manifest["path"]
        _require(shard_path.is_file(), "arm_shard_missing")
        _require(
            _file_hash(shard_path) == manifest.get("file_sha256"),
            "arm_shard_file_hash_mismatch",
        )
        shard_raw = shard_path.read_bytes()
        _require(shard_raw.endswith(b"\n"), "arm_shard_newline_missing")
        shard = json.loads(shard_raw)
        _require(shard.get("schema") == SHARD_SCHEMA, "arm_shard_schema_mismatch")
        _require(shard.get("arm_id") == arm, "arm_shard_namespace_mismatch")
        replayed = _replay(shard)
        _require(replayed == shard.get("final_state"), "arm_shard_replay_mismatch")
        state_root = _root(replayed)
        neutral_root = _root(_neutral(replayed))
        _require(state_root == shard.get("final_state_root_sha256"), "arm_state_root_mismatch")
        _require(neutral_root == shard.get("neutral_state_root_sha256"), "neutral_state_root_mismatch")
        _require(state_root == manifest.get("final_state_root_sha256"), "manifest_state_root_mismatch")
        _require(neutral_root == manifest.get("neutral_state_root_sha256"), "manifest_neutral_root_mismatch")
        _require(shard.get("policy_callbacks_invoked") is False, "policy_callback_flag_invalid")
        _require(
            shard.get("successor_arm_execution_launched") is False,
            "successor_execution_flag_invalid",
        )
        state_roots.add(state_root)
        neutral_roots.add(neutral_root)
    _require(len(state_roots) == 4, "arm_state_roots_not_isolated")
    _require(len(neutral_roots) == 1, "arm_neutral_roots_mismatch")
    _require(len(result.get("failure_injections") or []) == 7, "failure_injection_count_invalid")
    permutation = result.get("arm_order_permutation") or {}
    _require(
        permutation.get("orders") == [list(ARMS), list(reversed(ARMS))]
        and permutation.get("per_arm_state_roots_equal") is True,
        "arm_order_permutation_invalid",
    )
    execution = result.get("execution") or {}
    _require(execution.get("mutable_reducers_parallelized") is False, "mutable_parallelism_invalid")
    _require(execution.get("policy_callbacks_invoked") is False, "policy_callbacks_invalid")
    _require(execution.get("successor_arm_execution_launched") is False, "successor_launch_invalid")
    predecessor = result.get("candidate_boundary_predecessor") or {}
    predecessor_path = Path(str(predecessor.get("path") or ""))
    _require(predecessor_path.is_file(), "predecessor_missing")
    _require(_file_hash(predecessor_path) == predecessor.get("file_sha256"), "predecessor_hash_mismatch")
    code = result.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
    ):
        code_path = Path(str(code.get(path_key) or ""))
        _require(code_path.is_file(), "code_file_missing")
        _require(_file_hash(code_path) == code.get(hash_key), "code_hash_mismatch")
    return {
        "status": "VERIFIED",
        "arm_count": 4,
        "result_root_sha256": recorded,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_isolated_reducer_result(args.result)
    rendered = _canonical(receipt) + b"\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_name(f".{args.receipt.name}.tmp-{os.getpid()}")
        temporary.write_bytes(rendered)
        os.replace(temporary, args.receipt)
    print(rendered.decode("ascii").rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
