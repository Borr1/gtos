"""Independent persisted-byte verifier for the progressive replay slice.

This module intentionally shares no writer canonicalization, bundle loader,
manifest verifier, candidate projection, or root-building implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any, Mapping


RESULT_SCHEMA = "gtos.replay_acceleration.progressive_result.v1"
RUN_SCHEMA = "gtos.replay_acceleration.progressive_run.v1"
SEAL_SCHEMA = "gtos.replay_acceleration.progressive_run_seal.v1"
EXPECTED_DAYS = ["2026-01-02", "2026-01-05"]
EXPECTED_SYMBOLS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP",
    "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225",
    "NAS100", "NZDUSD", "SPX500", "UK100", "UKOIL_cash", "US30_cash",
    "USDCAD", "USDCHF", "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]
EXPECTED_TIMEFRAMES = ["D1", "H4", "H1", "M15", "M1"]
EXPECTED_ARMS = {"S0R0", "S1R0", "S0R1", "S1R1"}
EXPECTED_SURFACES = {
    "candidate_identity_union",
    "hard_pool",
    "selected_ordering",
    "risk_atoms",
    "scorecards",
    "orders_fills",
    "misses",
    "lifecycle_replacement",
    "costs_reservations",
    "terminal_state",
}
EXPECTED_FAILURES = {
    "bit_flip",
    "truncation",
    "append",
    "partition_reorder",
    "manifest_schema_mismatch",
    "source_mismatch",
    "normalized_manifest_mismatch",
    "config_mismatch",
    "code_mismatch",
    "stale_cache",
    "interruption_before_seal",
    "interruption_after_seal",
    "barrier_missing_symbol",
    "day_reorder",
}
WARNING_BYTES = 34 * 1024**3
HARD_FLOOR_BYTES = 28 * 1024**3
QUOTA_BYTES = 1024**3
FORBIDDEN_KEY_FRAGMENTS = (
    "pnl",
    "win_count",
    "loss_count",
    "win_loss",
    "r_total",
    "march_outcome",
    "treatment_economic",
    "comparative_economic",
)


class VerificationError(RuntimeError):
    """Stable independent verification failure."""


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
                "forbidden_economic_key_present",
            )
            _scan_keys(child)
    elif isinstance(value, list):
        for child in value:
            _scan_keys(child)


def _load_json_bytes(path: Path, *, newline_code: str, json_code: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise VerificationError(json_code) from exc
    _require(raw.endswith(b"\n"), newline_code)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(json_code) from exc
    _require(isinstance(payload, dict), json_code)
    return raw, payload


def _verify_run(path: Path, inventory: Mapping[str, Any]) -> dict[str, Any]:
    raw, run = _load_json_bytes(
        path, newline_code="run_newline_missing", json_code="run_json_invalid"
    )
    _require(run.get("schema") == RUN_SCHEMA, "run_schema_mismatch")
    recorded = run.get("run_root_sha256")
    payload = dict(run)
    payload.pop("run_root_sha256", None)
    _require(_is_hash(recorded) and recorded == _root(payload), "run_root_mismatch")
    _require(hashlib.sha256(raw).hexdigest() == inventory.get("file_sha256"), "run_file_hash_mismatch")
    _require(len(raw) == inventory.get("file_bytes"), "run_file_size_mismatch")
    _require(recorded == inventory.get("run_root_sha256"), "run_inventory_root_mismatch")
    seal_path = Path(str(inventory.get("seal_path") or ""))
    seal_raw, seal = _load_json_bytes(
        seal_path, newline_code="run_seal_newline_missing", json_code="run_seal_json_invalid"
    )
    _require(seal.get("schema") == SEAL_SCHEMA, "run_seal_schema_mismatch")
    _require(seal.get("run_root_sha256") == recorded, "run_seal_root_mismatch")
    _require(seal.get("run_file_sha256") == hashlib.sha256(raw).hexdigest(), "run_seal_file_hash_mismatch")
    _require(seal.get("run_file_bytes") == len(raw), "run_seal_file_size_mismatch")
    _require(hashlib.sha256(seal_raw).hexdigest() == inventory.get("seal_file_sha256"), "run_seal_inventory_hash_mismatch")
    _require(run.get("status") == "SEALED", "run_status_invalid")
    _require(run.get("selected_days") == EXPECTED_DAYS, "run_days_mismatch")
    _require(run.get("measurement_label") == "two_day_candidate_origin_and_structural_projection_not_whole_replay", "run_measurement_label_invalid")
    _require(run.get("whole_replay_claim") is False, "run_whole_replay_claim")
    for key in (
        "policy_execution_entered",
        "candidate_evaluation_entered",
        "scheduler_entered",
        "broker_mutation_enabled",
        "successor_arm_execution_launched",
    ):
        _require(run.get(key) is False, f"run_{key}_invalid")
    _require(run.get("cross_symbol_barrier_preserved") is True, "run_barrier_flag_invalid")
    _require(run.get("candidate_generation_worker_count") == 1, "run_candidate_worker_invalid")
    _require(run.get("immutable_prebarrier_worker_count") in {1, 2}, "run_immutable_worker_invalid")
    coverage = run.get("source_coverage") or {}
    _require(coverage.get("symbol_count") == 24, "run_source_symbol_count_mismatch")
    _require(coverage.get("logical_partition_count") == 120, "run_partition_count_mismatch")
    _require(coverage.get("timeframes") == EXPECTED_TIMEFRAMES, "run_timeframes_mismatch")
    _require(coverage.get("selected_days") == EXPECTED_DAYS, "run_source_days_mismatch")
    for key in (
        "coverage_root_sha256",
        "normalized_bundle_root_sha256",
        "source_bundle_root_sha256",
        "selection_root_sha256",
    ):
        _require(_is_hash(coverage.get(key)), f"run_{key}_invalid")
    _require(coverage.get("full_payload_bytes_read", 0) > 0, "run_source_bytes_missing")
    _require(coverage.get("full_row_count", 0) > 0, "run_source_rows_missing")
    days = run.get("day_receipts") or []
    _require([row.get("day") for row in days] == EXPECTED_DAYS, "run_day_receipts_mismatch")
    _require([row.get("day_index") for row in days] == [0, 1], "run_day_indices_mismatch")
    for row in days:
        count = row.get("decision_window_count")
        _require(isinstance(count, int) and count > 0, "run_day_window_count_invalid")
        _require(row.get("snapshot_count") == count * 24, "run_day_snapshot_count_mismatch")
        _require(isinstance(row.get("candidate_count"), int) and row["candidate_count"] >= 0, "run_day_candidate_count_invalid")
        _require(_is_hash(row.get("day_root_sha256")), "run_day_root_invalid")
        _require(str(row.get("first_decision_time_utc", "")) < str(row.get("last_decision_time_utc", "")), "run_day_time_order_invalid")
    _require(run.get("decision_window_count") == sum(row["decision_window_count"] for row in days), "run_window_total_mismatch")
    _require(run.get("snapshot_count") == run["decision_window_count"] * 24, "run_snapshot_total_mismatch")
    _require(run.get("candidate_structure_count") == sum(row["candidate_count"] for row in days), "run_candidate_total_mismatch")
    _require(_is_hash(run.get("campaign_candidate_identity_root_sha256")), "run_campaign_root_invalid")
    _require(run.get("factor_config_reads") == [], "run_factor_reads_present")
    _require(_is_hash(run.get("config_execution_projection_sha256")), "run_config_projection_invalid")
    _require(
        run.get("read_only_config_overrides")
        == {
            "market_state.side_effect_writes_enabled": False,
            "market_state.structure_shadow_log_enabled": False,
        },
        "run_read_only_config_override_invalid",
    )
    arms = run.get("four_arm_candidate_base_projection") or {}
    _require(set(arms) == EXPECTED_ARMS, "run_arm_projection_set_mismatch")
    _require(len(set(arms.values())) == 1 and all(_is_hash(value) for value in arms.values()), "run_arm_projection_root_mismatch")
    permutations = run.get("arm_order_permutations") or []
    _require(len(permutations) == 3, "run_permutation_count_mismatch")
    _require(
        all(set(row.get("arm_order") or []) == EXPECTED_ARMS for row in permutations),
        "run_permutation_arm_set_mismatch",
    )
    _require(len({row.get("aggregate_root_sha256") for row in permutations}) == 1, "run_permutation_root_mismatch")
    structural = run.get("structural_comparator_roots") or {}
    _require(set(structural) == EXPECTED_SURFACES, "run_structural_surface_set_mismatch")
    _require(all(_is_hash(value) for value in structural.values()), "run_structural_surface_root_invalid")
    stages = run.get("stage_wall_seconds") or {}
    for name in (
        "prospective_selection_revalidation",
        "config_load",
        "immutable_partition_verification_and_adapter_load",
        "all_symbol_snapshot",
        "cross_symbol_barrier",
        "candidate_origin_generation_single_worker",
        "allowlisted_projection_and_hashing",
        "receipt_serialization_probe",
    ):
        _require(isinstance(stages.get(name), (int, float)) and stages[name] >= 0, "run_stage_measurement_missing")
    resources = run.get("resources") or {}
    for key in (
        "cpu_user_seconds",
        "cpu_system_seconds",
        "minor_page_faults",
        "major_page_faults",
        "peak_rss_bytes",
        "explicit_bytes_read",
        "explicit_run_receipt_bytes_written",
    ):
        _require(isinstance(resources.get(key), (int, float)) and resources[key] >= 0, "run_resource_measurement_invalid")
    _require(
        resources["explicit_run_receipt_bytes_written"] == len(raw),
        "run_explicit_written_bytes_mismatch",
    )
    _require(run.get("end_to_end_wall_seconds", 0) > 0, "run_wall_measurement_invalid")
    _scan_keys(run)
    return run


def verify_progressive_result(result_path: Path) -> dict[str, Any]:
    raw, result = _load_json_bytes(
        result_path,
        newline_code="result_newline_missing",
        json_code="result_json_invalid",
    )
    _require(result.get("schema") == RESULT_SCHEMA, "result_schema_mismatch")
    _require(result.get("status") == "ACCEPTED", "result_status_invalid")
    _require(result.get("gate") == "PROGRESSIVE_TWO_DAY_EQUIVALENCE_ACCEPTED", "result_gate_mismatch")
    recorded = result.get("result_root_sha256")
    payload = dict(result)
    payload.pop("result_root_sha256", None)
    _require(_is_hash(recorded) and recorded == _root(payload), "result_root_mismatch")
    _scan_keys(result)
    scope = result.get("scope") or {}
    _require(scope.get("selected_days") == EXPECTED_DAYS, "result_days_mismatch")
    _require(scope.get("symbols") == EXPECTED_SYMBOLS, "result_symbols_mismatch")
    _require(scope.get("symbol_count") == 24, "result_symbol_count_mismatch")
    _require(scope.get("logical_partitions") == 120, "result_partition_count_mismatch")
    _require(scope.get("timeframes") == EXPECTED_TIMEFRAMES, "result_timeframes_mismatch")
    for key in (
        "policy_execution_entered",
        "successor_arm_execution_launched",
        "whole_replay_claim",
    ):
        _require(result.get(key) is False, f"result_{key}_invalid")
    _require(result.get("outcome_blind_structural_only") is True, "result_outcome_blind_flag_invalid")
    boundary = result.get("execution_boundary") or {}
    for key in (
        "policy_execution_entered",
        "candidate_evaluation_entered",
        "scheduler_entered",
        "broker_mutation_enabled",
        "successor_arm_execution_launched",
        "actual_successor_treatment_output_compared",
    ):
        _require(boundary.get(key) is False, f"result_boundary_{key}_invalid")
    inventory = result.get("run_inventory") or []
    _require(len(inventory) == 4, "result_run_inventory_count_mismatch")
    runs = []
    for item in inventory:
        path = Path(str(item.get("path") or ""))
        _require(path.is_file(), "result_run_file_missing")
        runs.append(_verify_run(path, item))
    _require([run["cache_state_label"] for run in runs].count("cold") == 2, "result_cold_run_count_mismatch")
    _require([run["cache_state_label"] for run in runs].count("warm") == 2, "result_warm_run_count_mismatch")
    _require({run["immutable_prebarrier_worker_count"] for run in runs} == {1, 2}, "result_worker_coverage_mismatch")
    deterministic_fields = (
        "campaign_candidate_identity_root_sha256",
        "day_receipts",
        "decision_window_count",
        "snapshot_count",
        "candidate_structure_count",
        "config_read_set",
        "config_execution_projection_sha256",
        "read_only_config_overrides",
        "factor_config_reads",
        "four_arm_candidate_base_projection",
        "arm_order_permutations",
        "structural_comparator_roots",
    )
    for field in deterministic_fields:
        _require(len({_root(run[field]) for run in runs}) == 1, f"result_determinism_{field}_mismatch")
    determinism = result.get("determinism") or {}
    _require(determinism.get("fresh_process_runs") == 4, "result_fresh_process_count_mismatch")
    _require(determinism.get("cold_runs") == 2 and determinism.get("warm_runs") == 2, "result_cache_run_count_mismatch")
    _require(determinism.get("legal_immutable_prebarrier_worker_counts") == [1, 2], "result_legal_workers_mismatch")
    _require(determinism.get("candidate_generation_worker_count") == 1, "result_candidate_worker_mismatch")
    _require(determinism.get("factor_config_reads") == [], "result_factor_reads_present")
    _require(determinism.get("all_structural_roots_identical") is True, "result_determinism_flag_invalid")
    failures = result.get("failure_injections") or []
    _require({row.get("case") for row in failures} == EXPECTED_FAILURES, "result_failure_matrix_mismatch")
    _require(all(row.get("status") == "REJECTED_AS_REQUIRED" for row in failures), "result_failure_verdict_invalid")
    structural = result.get("structural_comparator") or {}
    _require(structural.get("actual_policy_output") is False, "result_structural_policy_claim_invalid")
    _require(set((structural.get("roots") or {})) == EXPECTED_SURFACES, "result_structural_surfaces_mismatch")
    measurements = result.get("measurements") or {}
    _require(
        isinstance(measurements.get("peak_scratch_allocated_bytes"), int)
        and 0 <= measurements["peak_scratch_allocated_bytes"] < QUOTA_BYTES,
        "result_peak_scratch_invalid",
    )
    selection = result.get("selection_receipt") or {}
    selection_path = Path(str(selection.get("path") or ""))
    _require(selection_path.is_file(), "result_selection_receipt_missing")
    _require(_file_hash(selection_path) == selection.get("file_sha256"), "result_selection_receipt_hash_mismatch")
    _require(selection.get("source_structural_metadata_only") is True, "result_selection_scope_invalid")
    predecessors = result.get("predecessors") or []
    _require(len(predecessors) == 6, "result_predecessor_count_mismatch")
    for item in predecessors:
        path = Path(str(item.get("path") or ""))
        _require(path.is_file(), "result_predecessor_missing")
        _require(_file_hash(path) == item.get("file_sha256"), "result_predecessor_hash_mismatch")
        _require(_is_hash(item.get("result_root_sha256")), "result_predecessor_root_invalid")
        _require(bool(item.get("gate")), "result_predecessor_gate_missing")
    code = result.get("code_identity") or {}
    for path_key, hash_key in (
        ("writer_path", "writer_sha256"),
        ("independent_verifier_path", "independent_verifier_sha256"),
        ("test_path", "test_sha256"),
        ("config_path", "config_sha256"),
    ):
        path = Path(str(code.get(path_key) or ""))
        _require(path.is_file(), "result_code_file_missing")
        _require(_file_hash(path) == code.get(hash_key), "result_code_hash_mismatch")
    disk = result.get("disk") or {}
    _require(disk.get("warning_bytes") == WARNING_BYTES, "result_disk_warning_mismatch")
    _require(disk.get("hard_floor_bytes") == HARD_FLOOR_BYTES, "result_disk_floor_mismatch")
    _require(disk.get("bounded_slice_quota_bytes") == QUOTA_BYTES, "result_slice_quota_mismatch")
    _require(0 <= disk.get("bounded_slice_allocated_bytes", QUOTA_BYTES) < QUOTA_BYTES, "result_slice_allocation_invalid")
    live = os.statvfs(Path.cwd())
    _require(live.f_bavail * live.f_frsize >= HARD_FLOOR_BYTES, "live_disk_below_hard_floor")
    retention = result.get("retention") or {}
    _require(retention.get("files_deleted") == 0, "result_files_deleted")
    _require(retention.get("bytes_reclaimed") == 0, "result_bytes_reclaimed")
    _require(retention.get("broad_lfs_hydration_performed") is False, "result_broad_lfs_hydration")
    _require(retention.get("lfs_prune_performed") is False, "result_lfs_prune")
    _require(retention.get("unique_proof_evidence_preserved") is True, "result_proof_preservation_invalid")
    return {
        "status": "VERIFIED",
        "result_root_sha256": recorded,
        "persisted_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "fresh_process_runs": len(runs),
        "decision_window_count": scope["decision_window_count"],
        "snapshot_count": scope["snapshot_count"],
    }


def _usage_snapshot() -> dict[str, Any]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(usage.ru_maxrss)
    if sys.platform.startswith("linux"):
        peak_rss *= 1024
    return {
        "cpu_user_seconds": usage.ru_utime,
        "cpu_system_seconds": usage.ru_stime,
        "minor_page_faults": usage.ru_minflt,
        "major_page_faults": usage.ru_majflt,
        "block_input_operations": usage.ru_inblock,
        "block_output_operations": usage.ru_oublock,
        "peak_rss_bytes": peak_rss,
    }


def _verification_paths(result_path: Path, result: Mapping[str, Any]) -> set[Path]:
    paths = {result_path}
    for item in result.get("run_inventory") or []:
        paths.add(Path(str(item.get("path") or "")))
        paths.add(Path(str(item.get("seal_path") or "")))
    selection = result.get("selection_receipt") or {}
    paths.add(Path(str(selection.get("path") or "")))
    for item in result.get("predecessors") or []:
        paths.add(Path(str(item.get("path") or "")))
    code = result.get("code_identity") or {}
    for key in ("writer_path", "independent_verifier_path", "test_path", "config_path"):
        paths.add(Path(str(code.get(key) or "")))
    return {path for path in paths if path.is_file()}


def verify_progressive_result_measured(result_path: Path) -> dict[str, Any]:
    before = _usage_snapshot()
    started = time.perf_counter()
    receipt = verify_progressive_result(result_path)
    result = json.loads(result_path.read_bytes())
    paths = _verification_paths(result_path, result)
    after = _usage_snapshot()
    measurement = {
        "label": "independent_persisted_byte_verification",
        "wall_seconds": time.perf_counter() - started,
        "cpu_user_seconds": after["cpu_user_seconds"] - before["cpu_user_seconds"],
        "cpu_system_seconds": after["cpu_system_seconds"] - before["cpu_system_seconds"],
        "minor_page_faults": after["minor_page_faults"] - before["minor_page_faults"],
        "major_page_faults": after["major_page_faults"] - before["major_page_faults"],
        "block_input_operations": after["block_input_operations"] - before["block_input_operations"],
        "block_output_operations": after["block_output_operations"] - before["block_output_operations"],
        "peak_rss_bytes": after["peak_rss_bytes"],
        "explicit_bytes_read": (
            sum(path.stat().st_size for path in paths) + result_path.stat().st_size
        ),
        "byte_counters_available": False,
        "persisted_file_count": len(paths),
    }
    receipt["verification_measurement"] = measurement
    receipt["receipt_root_sha256"] = _root(receipt)
    return receipt


def _write_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(_canonical(payload) + b"\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    receipt = verify_progressive_result_measured(args.result)
    if args.receipt:
        _write_receipt(args.receipt, receipt)
    print(_canonical(receipt).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
