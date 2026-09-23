from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src.research_infra import replay_acceleration_task7_isolated_runner as task7
from src.research_infra import replay_acceleration_task7_isolated_verifier as verifier


TASK7_ACCEPTANCE = verifier.ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/"
    "TASK7_ISOLATED_NOEVENT_JAN1_20260723T100000Z/"
    "TASK7_ISOLATED_REDUCERS_ACCEPTANCE.json"
)


def test_task7_authenticates_task6_and_corrected_no_event_pack() -> None:
    accepted = task7.authenticate_task6_acceptance()
    pack = task7.authenticate_jan1_pack()

    assert accepted["receipt_root_sha256"] == task7.TASK6_ACCEPTANCE_ROOT_SHA256
    assert pack["external_root_authenticated"] is True
    assert pack["pack_root_sha256"] == task7.TASK6_JAN1_PACK_ROOT_SHA256
    assert pack["window_count"] == 96
    assert pack["source_status_counts"] == {"source_skipped": 2304}


def test_task7_logical_label_never_changes_replay_factor_binding(tmp_path: Path) -> None:
    for arm in task7.ARM_ORDER:
        args = task7._worker_args(
            tmp_path / arm,
            task7.TASK6_CORRECTED_PACK_ROOT,
        )
        assert args.arm_id == "S0R0"
        assert args.expected_arm_fingerprint_sha256 == task7.semantic.EXPECTED_ARM_FINGERPRINT
        assert args.engineering_stop_after_day == "2026-01-01"
        assert args.end == task7.replay.ATTEMPT5_CONTRACT_END_DAY
        assert args.prepared_day_pack_root == task7.TASK6_CORRECTED_PACK_ROOT
        assert args.expected_prepared_day_pack_roots == {
            task7.TASK7_PACK_KEY: task7.TASK6_JAN1_PACK_ROOT_SHA256
        }
        assert args.build_prepared_day_pack_root is None
        assert args.tick_sparse_cache_root == task7.replay.ATTEMPT5_TICK_SPARSE_CACHE_ROOT
        assert args.tick_sparse_cache_window_end_after_day == "2026-01-02"


def test_task7_worker_spec_rejects_factorial_execution_or_wrong_pack_root(
    tmp_path: Path,
) -> None:
    core = {
        "schema": task7.WORKER_SPEC_SCHEMA,
        "logical_arm_id": "S1R1",
        "worker_kind": "logical_arm",
        "executed_baseline_arm_id": "S1R1",
        "output_dir": str(tmp_path / "out"),
        "prepared_day_pack_root": str(task7.TASK6_CORRECTED_PACK_ROOT),
        "expected_prepared_day_pack_root_sha256": task7.TASK6_JAN1_PACK_ROOT_SHA256,
        "task6_acceptance_receipt_sha256": task7.TASK6_ACCEPTANCE_FILE_SHA256,
    }
    spec = {**core, "request_root_sha256": task7.stable_sha256(core)}
    with pytest.raises(task7.Task7Rejected, match="task7_worker_factorial_execution_forbidden"):
        task7.validate_worker_spec(spec)

    core["executed_baseline_arm_id"] = "S0R0"
    core["expected_prepared_day_pack_root_sha256"] = "0" * 64
    spec = {**core, "request_root_sha256": task7.stable_sha256(core)}
    with pytest.raises(task7.Task7Rejected, match="task7_worker_pack_root_mismatch"):
        task7.validate_worker_spec(spec)


def test_task7_task6_hash_mismatch_fails_closed() -> None:
    with pytest.raises(task7.Task7Rejected, match="task6_acceptance_receipt_hash_mismatch"):
        task7.authenticate_task6_acceptance(expected_file_sha256="0" * 64)


def test_task7_ordered_day_scan_detects_first_causal_difference(tmp_path: Path) -> None:
    left = tmp_path / "left.jsonl"
    right = tmp_path / "right.jsonl"
    left.write_text(
        json.dumps({"trading_day": "2026-01-01", "value": 1}, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    right.write_text(
        json.dumps({"trading_day": "2026-01-01", "value": 2}, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    left_scan = task7.scan_day_jsonl(left)
    right_scan = task7.scan_day_jsonl(right)
    assert left_scan["day_rows"] == right_scan["day_rows"] == 1
    assert left_scan["ordered_day_bytes_sha256"] != right_scan["ordered_day_bytes_sha256"]


def test_task7_monitor_rejects_more_than_two_workers_before_launch() -> None:
    with pytest.raises(task7.Task7Rejected, match="task7_max_workers_out_of_bounds"):
        task7._monitor_processes(
            [],
            max_workers=3,
            max_aggregate_rss_bytes=1,
        )


def test_task7_resource_policy_never_uses_preexisting_pressure_as_delta_bypass() -> None:
    material_failure, memory_failure = task7._resource_pressure_policy(
        host_pressure_preexisting=True,
        aggregate_rss_bytes=128 * 1024**2,
        max_aggregate_rss_bytes=256 * 1024**2,
        host_available_bytes=64 * 1024**2,
        global_swap_out_growth_bytes=512 * 1024**2,
        swap_growth_budget_bytes=64 * 1024**2,
    )
    assert material_failure is True
    assert memory_failure is True


def test_task7_resource_policy_rejects_new_pressure_on_clean_host() -> None:
    material_failure, memory_failure = task7._resource_pressure_policy(
        host_pressure_preexisting=False,
        aggregate_rss_bytes=128 * 1024**2,
        max_aggregate_rss_bytes=256 * 1024**2,
        host_available_bytes=64 * 1024**2,
        global_swap_out_growth_bytes=512 * 1024**2,
        swap_growth_budget_bytes=64 * 1024**2,
    )
    assert material_failure is True
    assert memory_failure is True


def test_task7_tick_cache_reuse_accepts_literal_zero_raw_hashes() -> None:
    task7.validate_tick_cache_superset_reuse(
        {
            "window_start_utc": "2025-12-31T00:00:00+00:00",
            "window_end_utc": "2026-01-04T00:00:00+00:00",
            "entry_count": 4,
            "raw_source_full_hash_count": 0,
            "sealed_cache_reuse_count": 4,
        }
    )

    with pytest.raises(task7.Task7Rejected, match="task7_tick_cache_superset_reuse_invalid"):
        task7.validate_tick_cache_superset_reuse(
            {
                "window_start_utc": "2025-12-31T00:00:00+00:00",
                "window_end_utc": "2026-01-04T00:00:00+00:00",
                "entry_count": 4,
                "raw_source_full_hash_count": 1,
                "sealed_cache_reuse_count": 3,
            }
        )


def test_task7_existing_output_namespace_fails_before_worker_launch(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(task7.Task7Rejected, match="task7_output_dir_must_be_new"):
        task7.run_task7(output)


def test_task7_failure_cleanup_kills_and_reaps_complete_process_group() -> None:
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import subprocess,sys,time;"
                "subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
                "time.sleep(60)"
            ),
        ],
        start_new_session=True,
    )
    try:
        time.sleep(0.2)
        task7._terminate_all({process.pid: process})
        assert process.poll() is not None
        assert task7._process_group_exists(process.pid) is False
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_task7_independent_verifier_recomputes_review_repaired_gate() -> None:
    result = verifier.verify_task7_acceptance(TASK7_ACCEPTANCE)

    assert result["status"] == "TASK7_INDEPENDENT_VERIFICATION_PASS_REVIEW_REPAIRED"
    assert result["task6_reference_projection_root_sha256"] == result[
        "baseline_semantic_projection_root_sha256"
    ]
    assert result["execution_order_independence_claimed"] is False
    assert result["per_window_state_observation_claimed"] is False
    assert result["live_broker_authority"] is False
    assert result["real_order_transmission_possible"] is False


def _accepted_baseline_worker() -> tuple[dict[str, object], Path, Path]:
    acceptance = json.loads(TASK7_ACCEPTANCE.read_text(encoding="utf-8"))
    worker_path = Path(acceptance["baseline"]["path"])
    worker = json.loads(worker_path.read_text(encoding="utf-8"))
    pack_path = Path(acceptance["prepared_day_pack"]["path"])
    return worker, worker_path, pack_path


def test_task7_independent_verifier_rejects_worker_live_flag_tamper() -> None:
    worker, worker_path, pack_path = _accepted_baseline_worker()
    worker["real_order_transmission_possible"] = True

    with pytest.raises(
        verifier.Task7VerificationError,
        match="worker_scope_or_live_boundary_invalid",
    ):
        verifier._verify_worker_artifacts(
            worker,
            worker_path=worker_path,
            expected_logical_arm="S0R0",
            expected_worker_kind="baseline",
            pack_root=pack_path,
            verified_tick_content={},
        )


def test_task7_independent_verifier_rejects_partial_summary_broker_tamper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker, worker_path, pack_path = _accepted_baseline_worker()
    partial_path = Path(worker["partial_summary"]["path"])
    original_loader = verifier._json_mapping

    def tampered_loader(path: Path, code: str) -> dict[str, object]:
        payload = original_loader(path, code)
        if verifier._absolute(path) == verifier._absolute(partial_path):
            payload = copy.deepcopy(payload)
            payload["live_broker_authority"] = True
        return payload

    monkeypatch.setattr(verifier, "_json_mapping", tampered_loader)
    with pytest.raises(
        verifier.Task7VerificationError,
        match="worker_partial_summary_scope_invalid",
    ):
        verifier._verify_worker_artifacts(
            worker,
            worker_path=worker_path,
            expected_logical_arm="S0R0",
            expected_worker_kind="baseline",
            pack_root=pack_path,
            verified_tick_content={},
        )


def test_task7_independent_verifier_rejects_prewarm_hash_tamper() -> None:
    worker, _worker_path, _pack_path = _accepted_baseline_worker()
    worker["authenticated_prepared_pack_tick_cache_superset_reuse"][
        "prewarm_receipt_sha256"
    ] = "0" * 64

    with pytest.raises(
        verifier.Task7VerificationError,
        match="worker_tick_cache_prewarm_hash_invalid",
    ):
        verifier._verify_tick_cache(worker, verified_content={})
