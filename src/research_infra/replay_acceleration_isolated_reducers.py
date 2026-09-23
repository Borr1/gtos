"""Four isolated chronological structural reducers for replay acceleration.

The reducers exercise mutable replay state without invoking selection, sizing,
broker economics, or any successor treatment.  Inputs are opaque structural
tokens bound to the accepted source barrier and candidate-base result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA = "gtos.replay_acceleration.isolated_reducer_result.v1"
SHARD_SCHEMA = "gtos.replay_acceleration.isolated_reducer_shard.v1"
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
SELECTION_PATH = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
    "SOURCE_SELECTION_RECEIPT.json"
)
CANDIDATE_RESULT_PATH = Path(
    "research/operations/replay_acceleration_candidate_boundary_2026_07_19/"
    "CANDIDATE_BOUNDARY_RESULT.json"
)


class ReducerError(RuntimeError):
    """Stable fail-closed reducer error."""


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
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).hexdigest()


def _order_id(arm_id: str, sequence: int, candidate: str) -> str:
    return _token(arm_id, sequence, candidate)


@dataclass
class ArmState:
    arm_id: str
    candidate_base_root: str
    source_barrier_root: str
    selected_day: str
    binding_projection_sha256: str
    account: dict[str, Any] = field(default_factory=dict)
    broker: dict[str, dict[str, Any]] = field(default_factory=dict)
    queue: list[str] = field(default_factory=list)
    pending: dict[str, str] = field(default_factory=dict)
    open: dict[str, str] = field(default_factory=dict)
    closed: dict[str, str] = field(default_factory=dict)
    reservations: dict[str, str] = field(default_factory=dict)
    risk_counters: dict[str, int] = field(default_factory=dict)
    adaptive_memory: dict[str, str] = field(default_factory=dict)
    replacement: dict[str, str] = field(default_factory=dict)
    candidate_orders: dict[str, str] = field(default_factory=dict)
    order_sequence: int = 0
    last_cursor: tuple[int, int, int] | None = None
    sealed: bool = False
    ledger: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.account = {
            "active_day": self.selected_day,
            "processed_windows": [],
            "event_count": 0,
        }
        self._refresh_counters()

    def _refresh_counters(self) -> None:
        self.risk_counters = {
            "queued_slots": len(self.queue),
            "pending_slots": len(self.pending),
            "open_slots": len(self.open),
            "closed_lifecycle_count": len(self.closed),
            "reservation_slots": len(self.reservations),
            "replacement_count": len(self.replacement),
        }

    def payload(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "candidate_base_root": self.candidate_base_root,
            "source_barrier_root": self.source_barrier_root,
            "selected_day": self.selected_day,
            "binding_projection_sha256": self.binding_projection_sha256,
            "account": self.account,
            "broker": self.broker,
            "queue": self.queue,
            "pending": self.pending,
            "open": self.open,
            "closed": self.closed,
            "reservations": self.reservations,
            "risk_counters": self.risk_counters,
            "adaptive_memory": self.adaptive_memory,
            "replacement": self.replacement,
            "candidate_orders": self.candidate_orders,
            "order_sequence": self.order_sequence,
            "last_cursor": list(self.last_cursor) if self.last_cursor is not None else None,
            "sealed": self.sealed,
            "ledger": self.ledger,
        }

    def neutral_payload(self) -> dict[str, Any]:
        broker = [
            {
                "sequence": record["sequence"],
                "candidate": record["candidate"],
                "status": record["status"],
            }
            for _, record in sorted(
                self.broker.items(), key=lambda item: int(item[1]["sequence"])
            )
        ]
        return {
            "candidate_base_root": self.candidate_base_root,
            "source_barrier_root": self.source_barrier_root,
            "selected_day": self.selected_day,
            "account": self.account,
            "broker": broker,
            "queue": self.queue,
            "pending_candidates": sorted(self.pending.values()),
            "open_candidates": sorted(self.open.values()),
            "closed_candidates": sorted(self.closed.values()),
            "reservation_candidates": sorted(self.reservations),
            "risk_counters": self.risk_counters,
            "adaptive_memory": self.adaptive_memory,
            "replacement": self.replacement,
            "order_sequence": self.order_sequence,
            "last_cursor": list(self.last_cursor) if self.last_cursor is not None else None,
            "sealed": self.sealed,
            "ledger": self.ledger,
        }


MUTABLE_FIELDS = (
    "account",
    "broker",
    "queue",
    "pending",
    "open",
    "closed",
    "reservations",
    "risk_counters",
    "adaptive_memory",
    "replacement",
    "candidate_orders",
    "ledger",
)


def allocate_arm_states(
    *,
    candidate_base_root: str,
    source_barrier_root: str,
    selected_day: str,
    binding_roots: Mapping[str, str] | None = None,
) -> dict[str, ArmState]:
    binding_roots = binding_roots or {
        arm: _token("structural-binding", arm) for arm in ARM_ORDER
    }
    return {
        arm: ArmState(
            arm_id=arm,
            candidate_base_root=candidate_base_root,
            source_barrier_root=source_barrier_root,
            selected_day=selected_day,
            binding_projection_sha256=str(binding_roots[arm]),
        )
        for arm in ARM_ORDER
    }


def assert_arm_state_isolation(states: Mapping[str, ArmState]) -> None:
    if set(states) != set(ARM_ORDER):
        raise ReducerError("arm_state_set_mismatch")
    seen: set[int] = set()
    for arm_id in ARM_ORDER:
        state = states[arm_id]
        if state.arm_id != arm_id:
            raise ReducerError("arm_namespace_mismatch")
        for field_name in MUTABLE_FIELDS:
            identity = id(getattr(state, field_name))
            if identity in seen:
                raise ReducerError("arm_state_mutable_alias_detected")
            seen.add(identity)


def _cursor(event: Mapping[str, Any]) -> tuple[int, int, int]:
    raw = event.get("cursor")
    if not isinstance(raw, list) or len(raw) != 3:
        raise ReducerError("event_cursor_invalid")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in raw):
        raise ReducerError("event_cursor_invalid")
    return raw[0], raw[1], raw[2]


def _candidate_order(state: ArmState, candidate: str, status: str) -> str:
    order_id = state.candidate_orders.get(candidate)
    if not order_id or state.broker.get(order_id, {}).get("status") != status:
        raise ReducerError(f"{status}_order_missing")
    return order_id


def apply_structural_event(state: ArmState, event: Mapping[str, Any]) -> None:
    if state.sealed:
        raise ReducerError("event_after_seal")
    if event.get("arm_namespace") != state.arm_id:
        raise ReducerError("arm_namespace_mismatch")
    if event.get("source_barrier_root") != state.source_barrier_root:
        raise ReducerError("source_barrier_root_mismatch")
    if event.get("candidate_base_root") != state.candidate_base_root:
        raise ReducerError("candidate_base_root_mismatch")
    if event.get("selected_day") != state.selected_day:
        raise ReducerError("selected_day_mismatch")
    cursor = _cursor(event)
    if state.last_cursor is not None and cursor <= state.last_cursor:
        raise ReducerError("event_cursor_not_strictly_increasing")
    state.last_cursor = cursor
    window = f"W{cursor[1]:03d}"
    if window not in state.account["processed_windows"]:
        state.account["processed_windows"].append(window)
    action = str(event.get("action") or "")
    candidate = str(event.get("candidate") or "")

    if action == "enqueue":
        if not candidate or candidate in state.candidate_orders or candidate in state.queue:
            raise ReducerError("enqueue_candidate_not_fresh")
        state.queue.append(candidate)
    elif action == "reserve":
        if candidate not in state.queue or candidate in state.reservations:
            raise ReducerError("reservation_candidate_not_queued")
        reservation_id = str(event.get("reservation_id") or "")
        if len(reservation_id) != 64:
            raise ReducerError("reservation_id_invalid")
        state.reservations[candidate] = reservation_id
    elif action == "submit":
        if candidate not in state.queue or candidate not in state.reservations:
            raise ReducerError("submit_candidate_not_reserved")
        state.queue.remove(candidate)
        state.order_sequence += 1
        order_id = _order_id(state.arm_id, state.order_sequence, candidate)
        state.candidate_orders[candidate] = order_id
        state.broker[order_id] = {
            "sequence": state.order_sequence,
            "candidate": candidate,
            "status": "pending",
        }
        state.pending[order_id] = candidate
    elif action == "activate":
        order_id = _candidate_order(state, candidate, "pending")
        state.pending.pop(order_id)
        state.open[order_id] = candidate
        state.broker[order_id]["status"] = "open"
    elif action == "replace_pending":
        old_candidate = str(event.get("old_candidate") or "")
        new_candidate = str(event.get("new_candidate") or "")
        old_order = state.candidate_orders.get(old_candidate)
        if not old_order or old_order not in state.pending:
            raise ReducerError("replacement_pending_order_missing")
        if new_candidate in state.candidate_orders or new_candidate in state.queue:
            raise ReducerError("replacement_candidate_not_fresh")
        state.pending.pop(old_order)
        state.broker[old_order]["status"] = "replaced"
        state.reservations.pop(old_candidate, None)
        state.replacement[old_candidate] = new_candidate
        reservation_id = str(event.get("reservation_id") or "")
        if len(reservation_id) != 64:
            raise ReducerError("reservation_id_invalid")
        state.reservations[new_candidate] = reservation_id
        state.order_sequence += 1
        new_order = _order_id(state.arm_id, state.order_sequence, new_candidate)
        state.candidate_orders[new_candidate] = new_order
        state.broker[new_order] = {
            "sequence": state.order_sequence,
            "candidate": new_candidate,
            "status": "pending",
        }
        state.pending[new_order] = new_candidate
    elif action == "memory_update":
        key = str(event.get("memory_key") or "")
        value = str(event.get("memory_value") or "")
        if not key or len(value) != 64:
            raise ReducerError("adaptive_memory_update_invalid")
        state.adaptive_memory[key] = value
    elif action == "close":
        order_id = _candidate_order(state, candidate, "open")
        state.open.pop(order_id)
        state.closed[order_id] = candidate
        state.broker[order_id]["status"] = "closed"
        state.reservations.pop(candidate, None)
    elif action == "seal":
        if state.queue:
            raise ReducerError("seal_with_nonempty_queue")
        state.sealed = True
    else:
        raise ReducerError("event_action_unknown")

    state.account["event_count"] += 1
    state._refresh_counters()
    state.ledger.append(
        {
            "cursor": list(cursor),
            "action": action,
            "candidate": candidate or None,
            "old_candidate": event.get("old_candidate"),
            "new_candidate": event.get("new_candidate"),
        }
    )


def structural_event_schedule(
    *,
    arm_id: str,
    candidate_base_root: str,
    source_barrier_root: str,
    selected_day: str,
) -> list[dict[str, Any]]:
    candidates = [_token(candidate_base_root, "candidate-slot", index) for index in range(3)]
    first, second, replacement = candidates
    base = {
        "arm_namespace": arm_id,
        "candidate_base_root": candidate_base_root,
        "source_barrier_root": source_barrier_root,
        "selected_day": selected_day,
    }
    rows = [
        ([0, 0, 0], "enqueue", {"candidate": first}),
        ([0, 0, 1], "reserve", {"candidate": first, "reservation_id": _token(first, "reserve")}),
        ([0, 0, 2], "submit", {"candidate": first}),
        ([0, 1, 3], "activate", {"candidate": first}),
        ([0, 1, 4], "enqueue", {"candidate": second}),
        ([0, 1, 5], "reserve", {"candidate": second, "reservation_id": _token(second, "reserve")}),
        ([0, 1, 6], "submit", {"candidate": second}),
        (
            [0, 2, 7],
            "replace_pending",
            {
                "old_candidate": second,
                "new_candidate": replacement,
                "reservation_id": _token(replacement, "reserve"),
            },
        ),
        (
            [0, 2, 8],
            "memory_update",
            {
                "memory_key": "bounded_structural_memory",
                "memory_value": _token(candidate_base_root, "memory"),
            },
        ),
        ([0, 3, 9], "close", {"candidate": first}),
        ([0, 3, 10], "activate", {"candidate": replacement}),
        ([0, 3, 11], "seal", {}),
    ]
    return [{**base, "cursor": cursor, "action": action, **extra} for cursor, action, extra in rows]


def _load_probe_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    selection = json.loads(SELECTION_PATH.read_bytes())
    candidate_result = json.loads(CANDIDATE_RESULT_PATH.read_bytes())
    if selection.get("status") != "PROSPECTIVE_SOURCE_SELECTION_SEALED":
        raise ReducerError("source_selection_not_accepted")
    if candidate_result.get("gate") != "CANDIDATE_BASE_BOUNDARY_ACCEPTED":
        raise ReducerError("candidate_boundary_not_accepted")
    probe = candidate_result.get("candidate_probe") or {}
    arms = probe.get("arms") or {}
    candidate_roots = {
        str((arms.get(arm) or {}).get("candidate_base_root_sha256") or "")
        for arm in ARM_ORDER
    }
    if len(candidate_roots) != 1 or "" in candidate_roots:
        raise ReducerError("candidate_base_roots_not_equal")
    logical = selection.get("logical_partitions")
    if not isinstance(logical, list):
        raise ReducerError("logical_partitions_missing")
    symbols = sorted({str(row.get("symbol") or "") for row in logical})
    if len(symbols) != 24 or len(logical) != 120 or "" in symbols:
        raise ReducerError("cross_symbol_barrier_scope_invalid")
    barrier_payload = {
        "selected_day": selection.get("selected_day"),
        "selection_root_sha256": selection.get("selection_root_sha256"),
        "symbols": symbols,
        "logical_partitions": [
            {
                "symbol": row.get("symbol"),
                "timeframe": row.get("timeframe"),
                "physical_partition_id": row.get("physical_partition_id"),
            }
            for row in logical
        ],
    }
    barrier = {
        "symbol_count": len(symbols),
        "logical_partition_count": len(logical),
        "selected_day": selection.get("selected_day"),
        "source_barrier_root_sha256": stable_sha256(barrier_payload),
        "all_symbols_preprocessed_before_mutable_reduction": True,
    }
    return selection, candidate_result, barrier


def run_structural_reducer_probe(
    *, arm_order: Iterable[str] = ARM_ORDER
) -> dict[str, Any]:
    arm_order = tuple(arm_order)
    if set(arm_order) != set(ARM_ORDER) or len(arm_order) != len(ARM_ORDER):
        raise ReducerError("arm_order_invalid")
    selection, candidate_result, barrier = _load_probe_inputs()
    candidate_probe = candidate_result["candidate_probe"]
    candidate_base_root = candidate_probe["arms"]["S0R0"][
        "candidate_base_root_sha256"
    ]
    binding_roots = {
        arm: candidate_probe["arms"][arm]["scheduler_factor_projection_sha256"]
        for arm in ARM_ORDER
    }
    states = allocate_arm_states(
        candidate_base_root=candidate_base_root,
        source_barrier_root=barrier["source_barrier_root_sha256"],
        selected_day=str(selection["selected_day"]),
        binding_roots=binding_roots,
    )
    assert_arm_state_isolation(states)
    arm_receipts: dict[str, dict[str, Any]] = {}
    for arm in arm_order:
        events = structural_event_schedule(
            arm_id=arm,
            candidate_base_root=candidate_base_root,
            source_barrier_root=barrier["source_barrier_root_sha256"],
            selected_day=str(selection["selected_day"]),
        )
        for event in events:
            apply_structural_event(states[arm], event)
        state_payload = states[arm].payload()
        arm_receipts[arm] = {
            "events": events,
            "final_state": state_payload,
            "final_state_root_sha256": stable_sha256(state_payload),
            "neutral_state_root_sha256": stable_sha256(states[arm].neutral_payload()),
        }
    assert_arm_state_isolation(states)
    if len({row["final_state_root_sha256"] for row in arm_receipts.values()}) != 4:
        raise ReducerError("arm_state_roots_not_isolated")
    if len({row["neutral_state_root_sha256"] for row in arm_receipts.values()}) != 1:
        raise ReducerError("arm_neutral_projection_mismatch")
    return {
        "arm_order": list(arm_order),
        "cross_symbol_barrier": barrier,
        "candidate_base_root_sha256": candidate_base_root,
        "arms": arm_receipts,
        "mutable_reducers_parallelized": False,
        "immutable_preprocessing_before_barrier_only": True,
        "policy_callbacks_invoked": False,
        "successor_arm_execution_launched": False,
    }


FAILURE_CODES = {
    "out_of_order": "event_cursor_not_strictly_increasing",
    "after_seal": "event_after_seal",
    "wrong_barrier": "source_barrier_root_mismatch",
    "wrong_candidate_root": "candidate_base_root_mismatch",
    "wrong_arm": "arm_namespace_mismatch",
    "missing_pending_replacement": "replacement_pending_order_missing",
    "mutable_alias": "arm_state_mutable_alias_detected",
}


def execute_failure_injection(case: str) -> None:
    candidate_root = "a" * 64
    barrier_root = "b" * 64
    day = "2026-01-02"
    states = allocate_arm_states(
        candidate_base_root=candidate_root,
        source_barrier_root=barrier_root,
        selected_day=day,
    )
    if case == "mutable_alias":
        states["S1R0"].queue = states["S0R0"].queue
        assert_arm_state_isolation(states)
        return
    state = states["S0R0"]
    events = structural_event_schedule(
        arm_id="S0R0",
        candidate_base_root=candidate_root,
        source_barrier_root=barrier_root,
        selected_day=day,
    )
    if case == "out_of_order":
        apply_structural_event(state, events[0])
        apply_structural_event(state, events[0])
    elif case == "after_seal":
        for event in events:
            apply_structural_event(state, event)
        extra = dict(events[-2])
        extra.update(
            {
                "cursor": [0, 4, 12],
                "action": "memory_update",
                "memory_key": "late",
                "memory_value": _token("late"),
            }
        )
        apply_structural_event(state, extra)
    elif case == "wrong_barrier":
        event = dict(events[0])
        event["source_barrier_root"] = "c" * 64
        apply_structural_event(state, event)
    elif case == "wrong_candidate_root":
        event = dict(events[0])
        event["candidate_base_root"] = "c" * 64
        apply_structural_event(state, event)
    elif case == "wrong_arm":
        event = dict(events[0])
        event["arm_namespace"] = "S1R0"
        apply_structural_event(state, event)
    elif case == "missing_pending_replacement":
        apply_structural_event(state, events[7])
    else:
        raise ReducerError("failure_injection_unknown")


def run_reducer_failure_injections() -> list[dict[str, str]]:
    verdicts: list[dict[str, str]] = []
    for case, expected in FAILURE_CODES.items():
        try:
            execute_failure_injection(case)
        except ReducerError as exc:
            if str(exc) != expected:
                raise ReducerError("failure_injection_wrong_rejection") from exc
            verdicts.append(
                {"case": case, "status": "REJECTED_AS_REQUIRED", "code": expected}
            )
        else:
            raise ReducerError("failure_injection_not_rejected")
    return verdicts


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    os.replace(temporary, path)


def write_isolated_reducer_result(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    probe = run_structural_reducer_probe()
    reverse_probe = run_structural_reducer_probe(arm_order=reversed(ARM_ORDER))
    for arm in ARM_ORDER:
        if (
            probe["arms"][arm]["final_state_root_sha256"]
            != reverse_probe["arms"][arm]["final_state_root_sha256"]
        ):
            raise ReducerError("arm_order_permutation_state_mismatch")
    probe_wall_ns = time.perf_counter_ns() - wall_start
    probe_cpu_ns = time.process_time_ns() - cpu_start
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    arm_manifest: dict[str, dict[str, Any]] = {}
    for arm in ARM_ORDER:
        receipt = probe["arms"][arm]
        shard = {
            "schema": SHARD_SCHEMA,
            "arm_id": arm,
            "candidate_base_root_sha256": probe["candidate_base_root_sha256"],
            "source_barrier": probe["cross_symbol_barrier"],
            "events": receipt["events"],
            "final_state": receipt["final_state"],
            "final_state_root_sha256": receipt["final_state_root_sha256"],
            "neutral_state_root_sha256": receipt["neutral_state_root_sha256"],
            "policy_callbacks_invoked": False,
            "successor_arm_execution_launched": False,
        }
        shard_path = output_dir / "arms" / f"{arm}.json"
        _atomic_write(shard_path, shard)
        arm_manifest[arm] = {
            "path": shard_path.relative_to(output_dir).as_posix(),
            "file_sha256": file_sha256(shard_path),
            "final_state_root_sha256": receipt["final_state_root_sha256"],
            "neutral_state_root_sha256": receipt["neutral_state_root_sha256"],
        }
    writer_path = Path(__file__).resolve()
    verifier_path = writer_path.with_name(
        "replay_acceleration_isolated_reducers_verifier.py"
    )
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED",
        "arm_order": list(ARM_ORDER),
        "arms": arm_manifest,
        "cross_symbol_barrier": probe["cross_symbol_barrier"],
        "candidate_base_root_sha256": probe["candidate_base_root_sha256"],
        "candidate_boundary_predecessor": {
            "path": CANDIDATE_RESULT_PATH.as_posix(),
            "file_sha256": file_sha256(CANDIDATE_RESULT_PATH),
            "result_root_sha256": json.loads(CANDIDATE_RESULT_PATH.read_bytes())[
                "result_root_sha256"
            ],
        },
        "failure_injections": run_reducer_failure_injections(),
        "arm_order_permutation": {
            "orders": [list(ARM_ORDER), list(reversed(ARM_ORDER))],
            "per_arm_state_roots_equal": True,
        },
        "code_identity": {
            "writer_path": writer_path.relative_to(Path.cwd()).as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.relative_to(Path.cwd()).as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
        },
        "execution": {
            "mutable_reducers_parallelized": False,
            "policy_callbacks_invoked": False,
            "successor_arm_execution_launched": False,
            "structural_equivalence_only": True,
        },
        "measurement": {
            "scope": "bounded_structural_reducer_only",
            "wall_ns": probe_wall_ns,
            "cpu_ns": probe_cpu_ns,
            "peak_rss_native": int(usage_after.ru_maxrss),
            "peak_rss_unit": "bytes_on_darwin_kib_elsewhere",
            "minor_page_faults": int(usage_after.ru_minflt - usage_before.ru_minflt),
            "major_page_faults": int(usage_after.ru_majflt - usage_before.ru_majflt),
            "blocks_read": int(usage_after.ru_inblock - usage_before.ru_inblock),
            "blocks_written": int(usage_after.ru_oublock - usage_before.ru_oublock),
            "whole_replay_speed_claim": False
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
    result_path = output_dir / "ISOLATED_REDUCER_RESULT.json"
    _atomic_write(result_path, result)
    return result_path


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if "--mode" in raw_argv:
        from src.research_infra.replay_acceleration_task7_isolated_runner import (
            main as production_main,
        )

        return production_main(raw_argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(raw_argv)
    path = write_isolated_reducer_result(args.output_dir)
    payload = json.loads(path.read_bytes())
    print(
        json.dumps(
            {
                "gate": payload["gate"],
                "result_root_sha256": payload["result_root_sha256"],
                "output": path.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
