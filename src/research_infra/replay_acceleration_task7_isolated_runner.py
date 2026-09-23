#!/usr/bin/env python3
"""Production-real Task 7 subprocess isolation over the accepted S0R0 reducer.

Task 7 proves that one accepted chronological reducer can be instantiated in
fresh, private processes and deterministically aggregated.  The four names are
logical isolation namespaces only.  Factorial S1/R1 policy execution remains
closed until the post-acceleration contract is sealed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (
    replay_acceleration_task2_semantic_slice_runner as semantic,
)
from src.research_infra import (
    replay_acceleration_task6_prepared_pack_runner as task6,
)
from src.research_infra.replay_prepared_day_pack import PreparedDayPackReader


ROOT = Path(__file__).resolve().parents[2]
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
REVERSED_ARM_ORDER = tuple(reversed(ARM_ORDER))
EXECUTED_BASELINE_ARM_ID = "S0R0"
TASK7_DAY = "2026-01-01"
TASK7_SPLIT = "development"
TASK7_PACK_KEY = (TASK7_SPLIT, TASK7_DAY, TASK7_DAY)
TASK7_EXPECTED_WINDOW_COUNT = 96
TASK7_EXPECTED_DECISION_ROWS = 24 * TASK7_EXPECTED_WINDOW_COUNT

TASK6_ACCEPTANCE_RECEIPT = ROOT / (
    ".hermes/receipts/task6/"
    "task6-prepared-pack-review-repaired-20260722T220211Z/"
    "TASK6_PREPARED_PACK_ACCEPTANCE.json"
)
TASK6_ACCEPTANCE_FILE_SHA256 = (
    "fbe9f7de9854e213f57ee19e37c1513302222394f9e80ae73ee1df16c6346819"
)
TASK6_ACCEPTANCE_ROOT_SHA256 = (
    "3137c0bb8e5f9dede3ae8cbc9ef5d3d1da7abd698b975f59fe8fc66fdfb892a3"
)
TASK6_CORRECTED_PARENT = ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/"
    "TASK6_FACTOR_NEUTRAL_PACK_REBUILD_JAN1_2_20260723T054500Z"
)
TASK6_CORRECTED_PACK_ROOT = TASK6_CORRECTED_PARENT / "prepared-day-packs"
TASK6_JAN1_PACK_ROOT_SHA256 = (
    "b83649706b47e625c965a1060252162535b2f95db4c5048eddc082369a2f300a"
)
TASK6_REFERENCE_EXECUTION_ROOT = ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/"
    "TASK6_PREPARED_PACK_JAN1_2_20260722T202135Z"
)

WORKER_SPEC_SCHEMA = "gtos.replay_acceleration.task7.worker_spec.v1"
WORKER_RECEIPT_SCHEMA = "gtos.replay_acceleration.task7.worker_receipt.v1"
ACCEPTANCE_SCHEMA = "gtos.replay_acceleration.task7.acceptance.v1"
WORKER_RECEIPT_NAME = "TASK7_ISOLATED_WORKER_RECEIPT.json"
ACCEPTANCE_NAME = "TASK7_ISOLATED_REDUCERS_ACCEPTANCE.json"
HOST_PRESSURE_AVAILABLE_BYTES = 1024 * 1024 * 1024
CRITICAL_HOST_AVAILABLE_BYTES = 128 * 1024 * 1024

ROLE_SUFFIXES = {
    "decision": "_DECISION_LEDGER.jsonl",
    "scorecard": "_SCORECARD_LEDGER.jsonl",
    "order": "_ORDER_LEDGER.jsonl",
    "trade": "_TRADE_LEDGER.jsonl",
    "oracle": "_ORDERED_PATH_ORACLE_LEDGER.jsonl",
    "missed": "_MISSED_OPPORTUNITY_LEDGER.jsonl",
    "bucket": "_BUCKET_LEDGER.jsonl",
    "semantic_candidate": "_SEMANTIC_CANDIDATE_LEDGER.jsonl",
    "semantic_state": "_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl",
    "semantic_order_preimage": "_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl",
}


class Task7Rejected(RuntimeError):
    """Stable fail-closed Task 7 rejection."""


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
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(ch in "009abcdef" for ch in text)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(payload) + b"\n")
    os.replace(temporary, path)


def _load_rooted_json(path: Path, *, root_field: str, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Task7Rejected(f"{code}_json_invalid") from exc
    if not isinstance(payload, dict):
        raise Task7Rejected(f"{code}_not_mapping")
    recorded = payload.get(root_field)
    projection = dict(payload)
    projection.pop(root_field, None)
    if not _is_sha256(recorded) or recorded != stable_sha256(projection):
        raise Task7Rejected(f"{code}_root_invalid")
    return payload


def authenticate_task6_acceptance(
    receipt_path: Path = TASK6_ACCEPTANCE_RECEIPT,
    *,
    expected_file_sha256: str = TASK6_ACCEPTANCE_FILE_SHA256,
) -> dict[str, Any]:
    path = Path(receipt_path)
    if path.is_symlink() or not path.is_file():
        raise Task7Rejected("task6_acceptance_receipt_invalid")
    if file_sha256(path) != expected_file_sha256:
        raise Task7Rejected("task6_acceptance_receipt_hash_mismatch")
    payload = _load_rooted_json(
        path,
        root_field="receipt_root_sha256",
        code="task6_acceptance_receipt",
    )
    corrected = payload.get("corrected_build_evidence")
    corrected = corrected if isinstance(corrected, Mapping) else {}
    bridges = payload.get("prepared_pack_record_bridges")
    bridges = bridges if isinstance(bridges, list) else []
    jan1_bridge = next(
        (
            row
            for row in bridges
            if isinstance(row, Mapping)
            and row.get("corrected_pack_root_sha256")
            == TASK6_JAN1_PACK_ROOT_SHA256
        ),
        None,
    )
    if (
        payload.get("status")
        != "TASK6_PREPARED_DAY_PACK_EXACT_FACTOR_NEUTRAL_AND_CONSUMED"
        or payload.get("task_gate_authorized") is not True
        or payload.get("receipt_root_sha256")
        != TASK6_ACCEPTANCE_ROOT_SHA256
        or payload.get("meaningful_difference_count") != 0
        or payload.get("unknown_difference_count") != 0
        or corrected.get("one_worker_four_worker_identity") is not True
        or corrected.get("pack_roots", [None])[0]
        != TASK6_JAN1_PACK_ROOT_SHA256
        or not isinstance(jan1_bridge, Mapping)
        or jan1_bridge.get("causal_or_economic_record_difference_count") != 0
        or int(jan1_bridge.get("record_count") or 0)
        != TASK7_EXPECTED_WINDOW_COUNT
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
    ):
        raise Task7Rejected("task6_acceptance_scope_invalid")
    return payload


def authenticate_jan1_pack(
    prepared_pack_root: Path = TASK6_CORRECTED_PACK_ROOT,
    *,
    expected_pack_root_sha256: str = TASK6_JAN1_PACK_ROOT_SHA256,
) -> dict[str, Any]:
    root = Path(prepared_pack_root)
    if root.is_symlink() or not root.is_dir():
        raise Task7Rejected("task7_prepared_pack_root_invalid")
    pack_path = root / TASK7_SPLIT / f"{TASK7_DAY}_{TASK7_DAY}"
    reader = PreparedDayPackReader(
        pack_path,
        expected_pack_root_sha256=expected_pack_root_sha256,
    )
    inventory = reader.manifest.get("window_inventory")
    if not isinstance(inventory, list) or len(inventory) != TASK7_EXPECTED_WINDOW_COUNT:
        raise Task7Rejected("task7_prepared_pack_window_count_invalid")
    decision_times: list[str] = []
    source_status_counts: dict[str, int] = {}
    for expected_ordinal, inventory_row in enumerate(inventory):
        if (
            not isinstance(inventory_row, Mapping)
            or inventory_row.get("trading_day") != TASK7_DAY
            or inventory_row.get("window_ordinal") != expected_ordinal
        ):
            raise Task7Rejected("task7_prepared_pack_inventory_invalid")
        record = reader.next_window(
            trading_day=TASK7_DAY,
            decision_time_utc=str(inventory_row.get("decision_time_utc") or ""),
            window_ordinal=expected_ordinal,
        )
        guard = record.get("calendar_no_session_breadth_guard")
        if not isinstance(guard, Mapping) or guard.get("active") is not True:
            raise Task7Rejected("task7_no_event_guard_invalid")
        symbols = record.get("symbols")
        if not isinstance(symbols, list) or len(symbols) != 24:
            raise Task7Rejected("task7_prepared_pack_symbol_scope_invalid")
        for symbol in symbols:
            if not isinstance(symbol, Mapping):
                raise Task7Rejected("task7_prepared_pack_symbol_invalid")
            status = str(symbol.get("status") or "")
            source_status_counts[status] = source_status_counts.get(status, 0) + 1
        decision_times.append(str(record.get("decision_time_utc") or ""))
    reader.finish()
    if source_status_counts != {"source_skipped": TASK7_EXPECTED_DECISION_ROWS}:
        raise Task7Rejected("task7_prepared_pack_no_event_status_invalid")
    return {
        "path": str(pack_path),
        "pack_root_sha256": reader.pack_root_sha256,
        "external_root_authenticated": reader.external_root_authenticated,
        "window_count": len(decision_times),
        "decision_times_utc": decision_times,
        "decision_time_root_sha256": stable_sha256(decision_times),
        "source_status_counts": source_status_counts,
        "factor_neutral_config_root_sha256": reader.bindings.get(
            "factor_neutral_config_root_sha256"
        ),
        "source_identity_root_sha256": reader.bindings.get(
            "source_identity_root_sha256"
        ),
    }


def _find_role_path(root: Path, role: str) -> Path:
    suffix = ROLE_SUFFIXES[role]
    search_root = (
        Path(f"{root}.semantic-diagnostic")
        if role.startswith("semantic_")
        else Path(root)
    )
    paths = sorted(search_root.glob(f"*{suffix}"))
    if len(paths) != 1 or paths[0].is_symlink() or not paths[0].is_file():
        raise Task7Rejected(f"task7_role_path_invalid:{role}")
    return paths[0]


def scan_day_jsonl(
    path: Path,
    *,
    day: str = TASK7_DAY,
    allow_bucket_aggregate_rows: bool = False,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    rows = 0
    byte_count = 0
    total_rows = 0
    parsed_rows: list[dict[str, Any]] = []
    with Path(path).open("rb") as handle:
        for raw in handle:
            total_rows += 1
            if not raw.endswith(b"\n"):
                raise Task7Rejected("task7_jsonl_framing_invalid")
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise Task7Rejected("task7_jsonl_row_invalid") from exc
            if not isinstance(row, dict):
                raise Task7Rejected("task7_jsonl_row_not_mapping")
            if "trading_day" not in row:
                if (
                    allow_bucket_aggregate_rows
                    and row.get("row_type") == "bucket"
                    and row.get("profile")
                    and row.get("split")
                ):
                    continue
                raise Task7Rejected("task7_jsonl_trading_day_missing")
            if row.get("trading_day") != day:
                continue
            digest.update(raw)
            byte_count += len(raw)
            rows += 1
            if rows <= 4:
                parsed_rows.append(row)
    return {
        "path": str(path),
        "file_sha256": file_sha256(path),
        "file_bytes": Path(path).stat().st_size,
        "total_rows": total_rows,
        "day": day,
        "day_rows": rows,
        "day_bytes": byte_count,
        "ordered_day_bytes_sha256": digest.hexdigest(),
        "first_rows": parsed_rows,
    }


def scan_role_set(root: Path) -> dict[str, dict[str, Any]]:
    return {
        role: scan_day_jsonl(
            _find_role_path(Path(root), role),
            allow_bucket_aggregate_rows=(role == "bucket"),
        )
        for role in ROLE_SUFFIXES
    }


def semantic_role_projection(receipts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        role: {
            "row_count": int(receipts[role]["day_rows"]),
            "ordered_bytes_sha256": receipts[role]["ordered_day_bytes_sha256"],
        }
        for role in ROLE_SUFFIXES
    }


def _state_timeline(
    role_receipts: Mapping[str, Mapping[str, Any]],
    *,
    decision_times: Sequence[str],
    broker_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    state_path = Path(str(role_receipts["semantic_state"]["path"]))
    rows: list[dict[str, Any]] = []
    with state_path.open("rb") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("trading_day") == TASK7_DAY:
                rows.append(row)
    if [row.get("boundary") for row in rows] != ["pre_day", "post_day"]:
        raise Task7Rejected("task7_state_boundaries_invalid")
    for row in rows:
        account = row.get("account_preimage")
        projection = row.get("state_projection")
        if not isinstance(account, Mapping) or not isinstance(projection, Mapping):
            raise Task7Rejected("task7_state_checkpoint_invalid")
        reservations = {
            key: account.get(key)
            for key in (
                "accepted_risk_orders_by_day",
                "accepted_risk_pct_by_day",
                "accepted_risk_orders_by_day_session",
                "accepted_risk_pct_by_day_session",
                "accepted_risk_orders_by_day_decision_time",
                "accepted_risk_pct_by_day_decision_time",
                "accepted_risk_orders_by_day_decision_cluster_side",
                "accepted_risk_pct_by_day_decision_cluster_side",
                "pending_orders",
                "open_positions",
            )
        }
        expected_projection = {
            "schema": "gtos.replay_acceleration.pre_day_state.v1",
            "account_root_sha256": stable_sha256(account),
            "broker_root_sha256": stable_sha256(broker_boundary),
            "event_queue_root_sha256": stable_sha256(account.get("event_queue", [])),
            "reservation_root_sha256": stable_sha256(reservations),
            "selected_order_sequence": 0,
        }
        if dict(projection) != expected_projection:
            raise Task7Rejected("task7_state_projection_invalid")
        if row.get("state_root_sha256") != stable_sha256(expected_projection):
            raise Task7Rejected("task7_state_root_invalid")
    pre = copy.deepcopy(rows[0]["account_preimage"])
    post = copy.deepcopy(rows[1]["account_preimage"])
    expected_post = copy.deepcopy(pre)
    daily_start = expected_post.get("daily_start_balance")
    if not isinstance(daily_start, dict):
        raise Task7Rejected("task7_daily_start_balance_invalid")
    daily_start.setdefault(TASK7_DAY, expected_post.get("balance"))
    if expected_post != post:
        raise Task7Rejected("task7_no_event_state_transition_invalid")
    if any(
        (
            post.get("event_queue"),
            post.get("pending_orders"),
            post.get("open_positions"),
            post.get("closed_trades"),
            int(post.get("event_sequence") or 0) != 0,
        )
    ):
        raise Task7Rejected("task7_no_event_state_not_empty")
    post_root = str(rows[1]["state_root_sha256"])
    timeline = [
        {"decision_time_utc": value, "state_root_sha256": post_root}
        for value in decision_times
    ]
    return {
        "scope": "no_event_day_derived_invariant_timeline",
        "observed_state_checkpoint_count": 2,
        "per_window_state_observed": False,
        "timestamp_count": len(timeline),
        "pre_day_state_root_sha256": rows[0]["state_root_sha256"],
        "post_day_state_root_sha256": post_root,
        "timeline_root_sha256": stable_sha256(timeline),
        "candidate_rich_timestamp_parity_deferred_to_tasks_8_9": True,
    }


def validate_worker_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    if spec.get("schema") != WORKER_SPEC_SCHEMA:
        raise Task7Rejected("task7_worker_spec_schema_invalid")
    logical_arm_id = str(spec.get("logical_arm_id") or "")
    worker_kind = str(spec.get("worker_kind") or "")
    if logical_arm_id not in ARM_ORDER or worker_kind not in {"baseline", "logical_arm"}:
        raise Task7Rejected("task7_worker_spec_identity_invalid")
    if worker_kind == "baseline" and logical_arm_id != "S0R0":
        raise Task7Rejected("task7_baseline_identity_invalid")
    if spec.get("executed_baseline_arm_id") != EXECUTED_BASELINE_ARM_ID:
        raise Task7Rejected("task7_worker_factorial_execution_forbidden")
    output_dir = Path(str(spec.get("output_dir") or ""))
    prepared_root = Path(str(spec.get("prepared_day_pack_root") or ""))
    if output_dir.exists() or output_dir.is_symlink():
        raise Task7Rejected("task7_worker_output_must_be_new")
    if prepared_root.resolve() != TASK6_CORRECTED_PACK_ROOT.resolve():
        raise Task7Rejected("task7_worker_pack_parent_mismatch")
    if spec.get("expected_prepared_day_pack_root_sha256") != TASK6_JAN1_PACK_ROOT_SHA256:
        raise Task7Rejected("task7_worker_pack_root_mismatch")
    request_root = spec.get("request_root_sha256")
    projection = dict(spec)
    projection.pop("request_root_sha256", None)
    if request_root != stable_sha256(projection):
        raise Task7Rejected("task7_worker_spec_root_invalid")
    return dict(spec)


def _worker_args(output_dir: Path, prepared_root: Path) -> argparse.Namespace:
    args = task6.task6_args(output_dir)
    args.task2_semantic_checkpoint_after_day = None
    args.engineering_stop_after_day = TASK7_DAY
    args.build_prepared_day_pack_root = None
    args.prepared_day_pack_root = prepared_root
    args.prepared_day_pack_build_only = False
    args.expected_prepared_day_pack_roots = {
        TASK7_PACK_KEY: TASK6_JAN1_PACK_ROOT_SHA256
    }
    args.prepared_pack_encoding_workers = 1
    args.arm_id = EXECUTED_BASELINE_ARM_ID
    args.expected_arm_fingerprint_sha256 = semantic.EXPECTED_ARM_FINGERPRINT
    # Jan 1 is a strict subset of the already authenticated Jan 1-2 sparse
    # cache window. Bind that exact superset so every isolated process reuses
    # sealed source attestations instead of rehashing multi-gigabyte raw files.
    args.tick_sparse_cache_root = replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
    args.tick_sparse_cache_window_end_after_day = "2026-01-02"
    return args


def validate_tick_cache_superset_reuse(receipt: Mapping[str, Any]) -> None:
    if (
        receipt.get("window_start_utc") != "2025-12-31T00:00:00+00:00"
        or receipt.get("window_end_utc") != "2026-01-04T00:00:00+00:00"
        or int(receipt.get("entry_count") or 0) != 4
        or int(receipt.get("raw_source_full_hash_count", -1)) != 0
        or int(receipt.get("sealed_cache_reuse_count") or 0) != 4
    ):
        raise Task7Rejected("task7_tick_cache_superset_reuse_invalid")


def _seed_private_typed_cache(destination: Path) -> dict[str, Any]:
    """Copy the accepted Task 6 cache into one worker-private namespace."""

    source = TASK6_CORRECTED_PARENT / "typed-cache"
    destination = Path(destination)
    if source.is_symlink() or not source.is_dir():
        raise Task7Rejected("task7_typed_cache_seed_missing")
    if destination.exists() or destination.is_symlink():
        raise Task7Rejected("task7_private_typed_cache_must_be_new")
    started = time.monotonic()
    shutil.copytree(source, destination, copy_function=shutil.copy2)
    files = sorted(path for path in destination.rglob("*") if path.is_file())
    if not files or any(path.is_symlink() for path in files):
        raise Task7Rejected("task7_private_typed_cache_seed_invalid")
    inventory = [
        {
            "path": path.relative_to(destination).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in files
    ]
    return {
        "source": str(source),
        "destination": str(destination),
        "file_count": len(inventory),
        "bytes": sum(row["bytes"] for row in inventory),
        "inventory_root_sha256": stable_sha256(inventory),
        "copy_wall_seconds": time.monotonic() - started,
        "private_copy_not_shared_mutable_cache": True,
    }


def execute_worker_spec(spec_path: Path) -> Path:
    spec_path = Path(spec_path)
    if spec_path.is_symlink() or not spec_path.is_file():
        raise Task7Rejected("task7_worker_spec_path_invalid")
    raw_spec = spec_path.read_bytes()
    spec = validate_worker_spec(json.loads(raw_spec))
    output_dir = Path(spec["output_dir"])
    prepared_root = Path(spec["prepared_day_pack_root"])
    pack = authenticate_jan1_pack(prepared_root)
    args = _worker_args(output_dir, prepared_root)
    replay.bind_attempt5_finalizer_conflict_key_order()
    runtime_contract = replay.configure_runtime_evidence_root(
        replay.ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    )
    args.bound_source_bundle_consumer_rebind_authority = (
        replay.source_bundle_consumer_rebind_authority_from_args(args)
    )
    namespace = replay.configure_output_namespace(output_dir)
    typed_cache_seed = _seed_private_typed_cache(
        Path(args.source_acceleration_cache_root)
    )
    semantic.bind_source_acceleration_authority(args)
    shared = task6._bind_current_shared_contract(args)
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.monotonic()
    cpu_start = time.process_time()
    partial = replay.run_replay_engine(args)
    wall_seconds = time.monotonic() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    progress = partial.get("progress_rows")
    pack_checkpoints = partial.get("prepared_day_pack_checkpoints")
    continuity = partial.get("capacity_safe_chunk_execution_contract")
    continuity = continuity if isinstance(continuity, Mapping) else {}
    checkpoints = continuity.get("checkpoints")
    if (
        partial.get("status")
        != "broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed"
        or not isinstance(progress, list)
        or len(progress) != 1
        or progress[0].get("start_day") != TASK7_DAY
        or progress[0].get("end_day") != TASK7_DAY
        or not isinstance(pack_checkpoints, list)
        or len(pack_checkpoints) != 1
        or pack_checkpoints[0].get("pack_root_sha256")
        != TASK6_JAN1_PACK_ROOT_SHA256
        or pack_checkpoints[0].get("external_root_authenticated") is not True
        or not isinstance(checkpoints, list)
        or len(checkpoints) != 1
        or checkpoints[0].get("broker_object_continuity") is not True
        or checkpoints[0].get("account_object_continuity") is not True
        or checkpoints[0].get("selected_order_sequence_monotonic") is not True
    ):
        raise Task7Rejected("task7_worker_reducer_result_invalid")
    broker_boundary = progress[0].get("broker_boundary")
    if (
        not isinstance(broker_boundary, Mapping)
        or broker_boundary.get("broker_adapter") != "SimulatedBroker"
        or broker_boundary.get("order_send_attempts") != 0
        or broker_boundary.get("broker_mutation_enabled") is not False
        or progress[0].get("live_broker_authority") is not False
        or progress[0].get("broker_mutation_enabled") is not False
        or partial.get("live_broker_authority") is not False
        or partial.get("broker_mutation_enabled") is not False
        or int(progress[0].get("selected_order_sequence") or 0) != 0
    ):
        raise Task7Rejected("task7_worker_broker_boundary_invalid")
    role_receipts = scan_role_set(namespace)
    tick_prewarm_receipt = (
        Path(namespace) / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json"
    )
    if tick_prewarm_receipt.is_symlink() or not tick_prewarm_receipt.is_file():
        raise Task7Rejected("task7_tick_cache_prewarm_receipt_missing")
    tick_prewarm = json.loads(tick_prewarm_receipt.read_bytes())
    validate_tick_cache_superset_reuse(tick_prewarm)
    if (
        int(role_receipts["decision"]["day_rows"])
        != TASK7_EXPECTED_DECISION_ROWS
        or any(
            int(role_receipts[role]["day_rows"]) != 0
            for role in (
                "scorecard",
                "order",
                "trade",
                "oracle",
                "missed",
                "semantic_candidate",
                "semantic_order_preimage",
            )
        )
        or int(role_receipts["semantic_state"]["day_rows"]) != 2
    ):
        raise Task7Rejected("task7_worker_no_event_role_counts_invalid")
    timeline = _state_timeline(
        role_receipts,
        decision_times=pack["decision_times_utc"],
        broker_boundary=broker_boundary,
    )
    semantic_projection = semantic_role_projection(role_receipts)
    semantic_root = stable_sha256(semantic_projection)
    partial_summary_path = Path(replay.output_paths(args.output_prefix)["partial_summary"])
    core = {
        "schema": WORKER_RECEIPT_SCHEMA,
        "status": "TASK7_ISOLATED_BASELINE_REDUCER_COMPLETE",
        "logical_arm_id": spec["logical_arm_id"],
        "worker_kind": spec["worker_kind"],
        "executed_baseline_arm_id": EXECUTED_BASELINE_ARM_ID,
        "factorial_policy_execution": False,
        "worker_pid": os.getpid(),
        "worker_parent_pid": os.getppid(),
        "request": {
            "path": str(spec_path),
            "file_sha256": hashlib.sha256(raw_spec).hexdigest(),
            "request_root_sha256": spec["request_root_sha256"],
        },
        "namespace": str(namespace),
        "private_namespaces": {
            "output": str(namespace),
            "typed_source_cache": str(args.source_acceleration_cache_root),
            "compact_event_sink": str(Path(namespace) / "compact-event-shards"),
        },
        "private_typed_cache_seed": typed_cache_seed,
        "prepared_day_pack": {
            key: value for key, value in pack.items() if key != "decision_times_utc"
        },
        "authenticated_prepared_pack_tick_cache_superset_reuse": {
            "enabled": True,
            "scope": "jan1_execution_with_authenticated_jan1_2_tick_window",
            "tick_authority_still_bound": True,
            "tick_sparse_cache_root": str(args.tick_sparse_cache_root),
            "window_end_after_day": "2026-01-02",
            "prewarm_receipt": str(tick_prewarm_receipt),
            "prewarm_receipt_sha256": file_sha256(tick_prewarm_receipt),
            "raw_source_full_hash_count": 0,
            "sealed_cache_reuse_count": 4,
        },
        "execution_contract": {
            "arm_id": EXECUTED_BASELINE_ARM_ID,
            "arm_fingerprint_sha256": semantic.EXPECTED_ARM_FINGERPRINT,
            "source_plan_digest_sha256": semantic.EXPECTED_SOURCE_PLAN_DIGEST,
            "shared_execution_contract_digest_sha256": shared.get(
                "shared_execution_contract_digest_sha256"
            ),
            "runtime_input_contract_root_sha256": runtime_contract.get(
                "contract_root_sha256"
            ),
        },
        "semantic_roles": role_receipts,
        "semantic_projection": semantic_projection,
        "semantic_projection_root_sha256": semantic_root,
        "no_event_state_timeline": timeline,
        "continuity": {
            "broker_object_continuity": True,
            "account_object_continuity": True,
            "selected_order_sequence_monotonic": True,
            "selected_order_sequence": 0,
        },
        "broker_boundary": dict(broker_boundary),
        "partial_summary": {
            "path": str(partial_summary_path),
            "file_sha256": file_sha256(partial_summary_path),
            "bytes": partial_summary_path.stat().st_size,
        },
        "measurement": {
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "peak_rss_bytes": int(usage_after.ru_maxrss),
            "minor_page_faults": int(usage_after.ru_minflt - usage_before.ru_minflt),
            "major_page_faults": int(usage_after.ru_majflt - usage_before.ru_majflt),
            "blocks_read": int(usage_after.ru_inblock - usage_before.ru_inblock),
            "blocks_written": int(usage_after.ru_oublock - usage_before.ru_oublock),
            "economic_hot_path_seconds": progress[0].get(
                "economic_hot_path_seconds"
            ),
            "proof_finalization_seconds": progress[0].get(
                "proof_finalization_seconds"
            ),
        },
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
    }
    receipt = {**core, "worker_receipt_root_sha256": stable_sha256(core)}
    receipt_path = Path(namespace) / WORKER_RECEIPT_NAME
    _atomic_write(receipt_path, receipt)
    return receipt_path


def _make_spec(
    *,
    output_root: Path,
    logical_arm_id: str,
    worker_kind: str,
    ordinal: int,
) -> tuple[Path, Path]:
    label = "baseline" if worker_kind == "baseline" else f"logical-{logical_arm_id.lower()}"
    output_dir = Path(output_root) / "workers" / f"{ordinal:02d}-{label}"
    spec_path = Path(output_root) / "requests" / f"{ordinal:02d}-{label}.json"
    core = {
        "schema": WORKER_SPEC_SCHEMA,
        "logical_arm_id": logical_arm_id,
        "worker_kind": worker_kind,
        "executed_baseline_arm_id": EXECUTED_BASELINE_ARM_ID,
        "output_dir": str(output_dir),
        "prepared_day_pack_root": str(TASK6_CORRECTED_PACK_ROOT),
        "expected_prepared_day_pack_root_sha256": TASK6_JAN1_PACK_ROOT_SHA256,
        "task6_acceptance_receipt_sha256": TASK6_ACCEPTANCE_FILE_SHA256,
    }
    spec = {**core, "request_root_sha256": stable_sha256(core)}
    _atomic_write(spec_path, spec)
    return spec_path, output_dir


def _process_group_exists(process_group_id: int) -> bool:
    try:
        import psutil
    except ImportError as exc:  # pragma: no cover - production dependency
        raise Task7Rejected("task7_psutil_required") from exc
    for process in psutil.process_iter(("pid", "status")):
        try:
            if (
                os.getpgid(process.pid) == process_group_id
                and process.info.get("status") != psutil.STATUS_ZOMBIE
            ):
                return True
        except (ProcessLookupError, PermissionError, psutil.NoSuchProcess):
            continue
    return False


def _terminate_all(active: Mapping[int, subprocess.Popen[bytes]]) -> None:
    """Terminate complete isolated worker process groups and reap leaders."""

    for process in active.values():
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and any(
        _process_group_exists(process.pid) for process in active.values()
    ):
        for process in active.values():
            process.poll()
        time.sleep(0.05)
    for process in active.values():
        if _process_group_exists(process.pid):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
    for process in active.values():
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired as exc:
            raise Task7Rejected("task7_worker_process_group_cleanup_failed") from exc
    if any(_process_group_exists(process.pid) for process in active.values()):
        raise Task7Rejected("task7_worker_process_group_cleanup_failed")


def _resource_pressure_policy(
    *,
    host_pressure_preexisting: bool,
    aggregate_rss_bytes: int,
    max_aggregate_rss_bytes: int,
    host_available_bytes: int,
    global_swap_out_growth_bytes: int,
    swap_growth_budget_bytes: int,
) -> tuple[bool, bool]:
    """Return child/resource-measurement and critical-host failures.

    macOS exposes swap-in/out only as machine-wide counters.  When pressure
    predates the worker, growth in that counter is evidence about the host,
    not proof that this child swapped.  Attribution remains advisory, but a
    material counter delta makes the bounded-resource measurement invalid and
    therefore fails regardless of whether host pressure predated the worker.
    """

    del host_pressure_preexisting
    rss_failure = aggregate_rss_bytes > max_aggregate_rss_bytes
    critical_host = host_available_bytes < CRITICAL_HOST_AVAILABLE_BYTES
    material_swap = global_swap_out_growth_bytes > swap_growth_budget_bytes
    return rss_failure or material_swap, critical_host


def _monitor_processes(
    specs: Sequence[Path],
    *,
    max_workers: int,
    max_aggregate_rss_bytes: int,
) -> tuple[list[Path], dict[str, Any]]:
    try:
        import psutil
    except ImportError as exc:  # pragma: no cover - production dependency
        raise Task7Rejected("task7_psutil_required") from exc
    if not 1 <= max_workers <= 2:
        raise Task7Rejected("task7_max_workers_out_of_bounds")
    pending = deque(Path(path) for path in specs)
    active: dict[int, subprocess.Popen[bytes]] = {}
    active_specs: dict[int, Path] = {}
    active_logs: dict[int, tuple[Any, Any]] = {}
    completed: list[Path] = []
    peak_rss = 0
    peak_active = 0
    samples = 0
    virtual_start = psutil.virtual_memory()
    swap_start = psutil.swap_memory()
    host_pressure_preexisting = bool(
        virtual_start.percent >= 90.0
        or int(virtual_start.available) < HOST_PRESSURE_AVAILABLE_BYTES
        or int(swap_start.used) > 0
    )
    max_swap_used = int(swap_start.used)
    min_available = int(psutil.virtual_memory().available)
    command_prefix = [
        sys.executable,
        "-m",
        "src.research_infra.replay_acceleration_isolated_reducers",
        "--mode",
        "production-worker",
        "--worker-spec",
    ]
    try:
        while pending or active:
            while pending and len(active) < max_workers:
                spec_path = pending.popleft()
                process = subprocess.Popen(
                    [*command_prefix, str(spec_path)],
                    cwd=ROOT,
                    stdout=(stdout_log := tempfile.TemporaryFile()),
                    stderr=(stderr_log := tempfile.TemporaryFile()),
                    start_new_session=True,
                )
                active[process.pid] = process
                active_specs[process.pid] = spec_path
                active_logs[process.pid] = (stdout_log, stderr_log)
                peak_active = max(peak_active, len(active))
            aggregate_rss = 0
            for pid in tuple(active):
                try:
                    process = psutil.Process(pid)
                    aggregate_rss += int(process.memory_info().rss)
                    for child in process.children(recursive=True):
                        aggregate_rss += int(child.memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            virtual = psutil.virtual_memory()
            swap = psutil.swap_memory()
            samples += 1
            peak_rss = max(peak_rss, aggregate_rss)
            max_swap_used = max(max_swap_used, int(swap.used))
            min_available = min(min_available, int(virtual.available))
            swap_out_growth = max(0, int(swap.sout) - int(swap_start.sout))
            material_swap_budget = max(64 * 1024 * 1024, peak_rss // 4)
            material_failure, memory_failure = _resource_pressure_policy(
                host_pressure_preexisting=host_pressure_preexisting,
                aggregate_rss_bytes=aggregate_rss,
                max_aggregate_rss_bytes=max_aggregate_rss_bytes,
                host_available_bytes=int(virtual.available),
                global_swap_out_growth_bytes=swap_out_growth,
                swap_growth_budget_bytes=material_swap_budget,
            )
            if aggregate_rss > max_aggregate_rss_bytes:
                raise Task7Rejected("task7_aggregate_rss_cap_breached")
            if material_failure:
                raise Task7Rejected("task7_material_swap_growth_detected")
            if memory_failure:
                raise Task7Rejected("task7_memory_pressure_failure")
            for pid, process in tuple(active.items()):
                returncode = process.poll()
                if returncode is None:
                    continue
                process.wait()
                stdout_log, stderr_log = active_logs.pop(pid)
                stdout_log.seek(0)
                stderr_log.seek(0)
                stdout = stdout_log.read()
                stderr = stderr_log.read()
                stdout_log.close()
                stderr_log.close()
                spec_path = active_specs.pop(pid)
                active.pop(pid)
                if returncode != 0:
                    message = stderr.decode("utf-8", errors="replace")[-4000:]
                    raise Task7Rejected(
                        f"task7_worker_failed:{spec_path.name}:{returncode}:{message}"
                    )
                try:
                    lines = [line for line in stdout.splitlines() if line.strip()]
                    worker_output = json.loads(lines[-1] if lines else b"")
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise Task7Rejected("task7_worker_stdout_invalid") from exc
                receipt_path = Path(str(worker_output.get("receipt") or ""))
                if receipt_path.is_symlink() or not receipt_path.is_file():
                    raise Task7Rejected("task7_worker_receipt_missing")
                completed.append(receipt_path)
            if pending or active:
                time.sleep(0.1)
    except BaseException:
        try:
            _terminate_all(active)
        finally:
            for stdout_log, stderr_log in active_logs.values():
                stdout_log.close()
                stderr_log.close()
        raise
    swap_end = psutil.swap_memory()
    swap_out_growth = max(0, int(swap_end.sout) - int(swap_start.sout))
    material_swap_budget = max(64 * 1024 * 1024, peak_rss // 4)
    material_failure, memory_failure = _resource_pressure_policy(
        host_pressure_preexisting=host_pressure_preexisting,
        aggregate_rss_bytes=peak_rss,
        max_aggregate_rss_bytes=max_aggregate_rss_bytes,
        host_available_bytes=min_available,
        global_swap_out_growth_bytes=swap_out_growth,
        swap_growth_budget_bytes=material_swap_budget,
    )
    if peak_rss > max_aggregate_rss_bytes:
        raise Task7Rejected("task7_aggregate_rss_cap_breached")
    if material_failure:
        raise Task7Rejected("task7_material_swap_growth_detected")
    if memory_failure:
        raise Task7Rejected("task7_memory_pressure_failure")
    return completed, {
        "sample_count": samples,
        "configured_max_workers": max_workers,
        "peak_active_workers": peak_active,
        "max_aggregate_rss_bytes": max_aggregate_rss_bytes,
        "peak_aggregate_child_tree_rss_bytes": peak_rss,
        "minimum_host_available_memory_bytes": min_available,
        "host_available_memory_start_bytes": int(virtual_start.available),
        "host_memory_percent_start": float(virtual_start.percent),
        "host_pressure_preexisting": host_pressure_preexisting,
        "swap_used_start_bytes": int(swap_start.used),
        "swap_used_peak_bytes": max_swap_used,
        "swap_used_end_bytes": int(swap_end.used),
        "swap_out_start_bytes": int(swap_start.sout),
        "swap_out_end_bytes": int(swap_end.sout),
        "raw_swap_out_growth_bytes": swap_out_growth,
        "material_swap_growth_budget_bytes": material_swap_budget,
        "swap_counter_scope": "machine_wide_not_child_attributable",
        "preexisting_pressure_swap_growth_advisory_only": (
            host_pressure_preexisting and swap_out_growth > 0
        ),
        "preexisting_pressure_never_bypasses_material_delta_gate": True,
        "material_swap_growth_detected": False,
        "memory_pressure_failure": False,
    }


def _load_worker_receipt(path: Path) -> dict[str, Any]:
    payload = _load_rooted_json(
        Path(path),
        root_field="worker_receipt_root_sha256",
        code="task7_worker_receipt",
    )
    if (
        payload.get("schema") != WORKER_RECEIPT_SCHEMA
        or payload.get("status") != "TASK7_ISOLATED_BASELINE_REDUCER_COMPLETE"
        or payload.get("executed_baseline_arm_id") != EXECUTED_BASELINE_ARM_ID
        or payload.get("factorial_policy_execution") is not False
        or payload.get("live_broker_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
        or payload.get("real_order_transmission_possible") is not False
    ):
        raise Task7Rejected("task7_worker_receipt_scope_invalid")
    return payload


def compare_role_projections(
    left: Mapping[str, Mapping[str, Any]],
    right: Mapping[str, Mapping[str, Any]],
    *,
    code: str,
) -> dict[str, Any]:
    left_projection = semantic_role_projection(left)
    right_projection = semantic_role_projection(right)
    if left_projection != right_projection:
        for role in ROLE_SUFFIXES:
            if left_projection[role] != right_projection[role]:
                raise Task7Rejected(f"{code}:{role}")
        raise Task7Rejected(code)
    return {
        "status": "EXACT_ORDERED_JAN1_ROLE_PARITY",
        "role_count": len(left_projection),
        "projection_root_sha256": stable_sha256(left_projection),
        "roles": left_projection,
    }


def run_task7(
    output_dir: Path,
    *,
    max_workers: int = 2,
    max_aggregate_rss_bytes: int = 6 * 1024 * 1024 * 1024,
) -> Path:
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise Task7Rejected("task7_output_dir_must_be_new")
    output_dir.mkdir(parents=True)
    task6_acceptance = authenticate_task6_acceptance()
    pack = authenticate_jan1_pack()
    reference_roles = scan_role_set(TASK6_REFERENCE_EXECUTION_ROOT)

    baseline_spec, _baseline_output = _make_spec(
        output_root=output_dir,
        logical_arm_id="S0R0",
        worker_kind="baseline",
        ordinal=0,
    )
    baseline_paths, baseline_resources = _monitor_processes(
        [baseline_spec],
        max_workers=1,
        max_aggregate_rss_bytes=max_aggregate_rss_bytes,
    )
    if len(baseline_paths) != 1:
        raise Task7Rejected("task7_baseline_receipt_count_invalid")
    baseline = _load_worker_receipt(baseline_paths[0])
    baseline_parity = compare_role_projections(
        baseline["semantic_roles"],
        reference_roles,
        code="task7_baseline_task6_parity_mismatch",
    )
    if (
        baseline.get("no_event_state_timeline", {}).get("timestamp_count")
        != TASK7_EXPECTED_WINDOW_COUNT
        or baseline.get("prepared_day_pack", {}).get("pack_root_sha256")
        != TASK6_JAN1_PACK_ROOT_SHA256
    ):
        raise Task7Rejected("task7_baseline_timeline_or_pack_invalid")

    fanout_specs = [
        _make_spec(
            output_root=output_dir,
            logical_arm_id=arm,
            worker_kind="logical_arm",
            ordinal=index,
        )[0]
        for index, arm in enumerate(REVERSED_ARM_ORDER, start=1)
    ]
    fanout_paths, fanout_resources = _monitor_processes(
        fanout_specs,
        max_workers=max_workers,
        max_aggregate_rss_bytes=max_aggregate_rss_bytes,
    )
    logical_receipts: dict[str, dict[str, Any]] = {}
    logical_receipt_paths: dict[str, Path] = {}
    for path in fanout_paths:
        payload = _load_worker_receipt(path)
        arm = str(payload.get("logical_arm_id") or "")
        if arm in logical_receipts or arm not in ARM_ORDER:
            raise Task7Rejected("task7_logical_arm_receipt_set_invalid")
        logical_receipts[arm] = payload
        logical_receipt_paths[arm] = path
    if set(logical_receipts) != set(ARM_ORDER):
        raise Task7Rejected("task7_logical_arm_receipt_set_invalid")

    baseline_semantic_root = baseline["semantic_projection_root_sha256"]
    baseline_timeline_root = baseline["no_event_state_timeline"][
        "timeline_root_sha256"
    ]
    logical_manifest: dict[str, dict[str, Any]] = {}
    for arm in ARM_ORDER:
        payload = logical_receipts[arm]
        compare_role_projections(
            payload["semantic_roles"],
            baseline["semantic_roles"],
            code=f"task7_logical_arm_parity_mismatch:{arm}",
        )
        if (
            payload.get("semantic_projection_root_sha256") != baseline_semantic_root
            or payload.get("no_event_state_timeline", {}).get(
                "timeline_root_sha256"
            )
            != baseline_timeline_root
            or payload.get("execution_contract", {}).get("arm_id")
            != EXECUTED_BASELINE_ARM_ID
        ):
            raise Task7Rejected(f"task7_logical_arm_state_root_mismatch:{arm}")
        path = logical_receipt_paths[arm]
        logical_manifest[arm] = {
            "logical_arm_id": arm,
            "executed_baseline_arm_id": EXECUTED_BASELINE_ARM_ID,
            "path": str(path),
            "file_sha256": file_sha256(path),
            "worker_receipt_root_sha256": payload[
                "worker_receipt_root_sha256"
            ],
            "worker_pid": payload["worker_pid"],
            "namespace": payload["namespace"],
            "semantic_projection_root_sha256": baseline_semantic_root,
            "timeline_root_sha256": baseline_timeline_root,
        }
    all_receipts = [baseline, *logical_receipts.values()]
    pids = [int(payload["worker_pid"]) for payload in all_receipts]
    namespaces = [str(payload["namespace"]) for payload in all_receipts]
    cache_namespaces = [
        str(payload["private_namespaces"]["typed_source_cache"])
        for payload in all_receipts
    ]
    if len(set(pids)) != 5 or len(set(namespaces)) != 5 or len(set(cache_namespaces)) != 5:
        raise Task7Rejected("task7_process_or_namespace_isolation_invalid")
    canonical_aggregate = {
        arm: {
            "executed_baseline_arm_id": logical_manifest[arm][
                "executed_baseline_arm_id"
            ],
            "semantic_projection_root_sha256": logical_manifest[arm][
                "semantic_projection_root_sha256"
            ],
            "timeline_root_sha256": logical_manifest[arm][
                "timeline_root_sha256"
            ],
        }
        for arm in ARM_ORDER
    }
    forward_root = stable_sha256(canonical_aggregate)
    reverse_root = stable_sha256(
        {arm: canonical_aggregate[arm] for arm in reversed(ARM_ORDER)}
    )
    if forward_root != reverse_root:
        raise Task7Rejected("task7_aggregate_order_dependence_detected")
    core = {
        "schema": ACCEPTANCE_SCHEMA,
        "status": "TASK7_ISOLATED_CHRONOLOGICAL_REDUCERS_ACCEPTED",
        "task": "Replay-Acceleration Task 7",
        "scope": {
            "day": TASK7_DAY,
            "baseline_execution_count": 1,
            "logical_arm_execution_count": 4,
            "executed_baseline_arm_id": EXECUTED_BASELINE_ARM_ID,
            "logical_arm_ids": list(ARM_ORDER),
            "factorial_policy_execution": False,
            "candidate_rich_timestamp_parity_deferred_to_tasks_8_9": True,
        },
        "task6_acceptance": {
            "path": str(TASK6_ACCEPTANCE_RECEIPT),
            "file_sha256": TASK6_ACCEPTANCE_FILE_SHA256,
            "receipt_root_sha256": task6_acceptance["receipt_root_sha256"],
        },
        "prepared_day_pack": {
            key: value for key, value in pack.items() if key != "decision_times_utc"
        },
        "reference_execution_root": str(TASK6_REFERENCE_EXECUTION_ROOT),
        "baseline": {
            "path": str(baseline_paths[0]),
            "file_sha256": file_sha256(baseline_paths[0]),
            "worker_receipt_root_sha256": baseline[
                "worker_receipt_root_sha256"
            ],
            "worker_pid": baseline["worker_pid"],
            "namespace": baseline["namespace"],
            "semantic_projection_root_sha256": baseline_semantic_root,
            "timeline_root_sha256": baseline_timeline_root,
            "task6_jan1_exact_parity": baseline_parity,
        },
        "logical_arms": logical_manifest,
        "canonical_aggregate": {
            "launch_order": list(REVERSED_ARM_ORDER),
            "canonical_order": list(ARM_ORDER),
            "root_sha256": forward_root,
            "reverse_materialization_root_sha256": reverse_root,
            "canonical_mapping_serialization_order_independent": True,
            "execution_order_independence_claimed": False,
        },
        "process_isolation": {
            "unique_worker_pid_count": len(set(pids)),
            "unique_output_namespace_count": len(set(namespaces)),
            "unique_typed_cache_namespace_count": len(set(cache_namespaces)),
            "private_broker_account_event_state": True,
            "path_root_only_ipc": True,
        },
        "resources": {
            "baseline": baseline_resources,
            "four_logical_arms": fanout_resources,
        },
        "semantic_or_economic_difference_count": 0,
        "unknown_difference_count": 0,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
        "acceptance_authorized": False,
        "task_gate_authorized": True,
    }
    receipt = {**core, "receipt_root_sha256": stable_sha256(core)}
    receipt_path = output_dir / ACCEPTANCE_NAME
    _atomic_write(receipt_path, receipt)
    return receipt_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("production-task7", "production-worker"),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--worker-spec", type=Path)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument(
        "--max-aggregate-rss-bytes",
        type=int,
        default=6 * 1024 * 1024 * 1024,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "production-worker":
        if args.worker_spec is None or args.output_dir is not None:
            raise Task7Rejected("task7_worker_cli_scope_invalid")
        receipt = execute_worker_spec(args.worker_spec)
    else:
        if args.output_dir is None or args.worker_spec is not None:
            raise Task7Rejected("task7_orchestrator_cli_scope_invalid")
        receipt = run_task7(
            args.output_dir,
            max_workers=args.max_workers,
            max_aggregate_rss_bytes=args.max_aggregate_rss_bytes,
        )
    print(json.dumps({"receipt": str(receipt)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
