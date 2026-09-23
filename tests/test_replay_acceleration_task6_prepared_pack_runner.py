from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_task6_prepared_pack_runner as task6,
)


def test_task6_args_build_and_consume_arm_neutral_packs(tmp_path: Path) -> None:
    args = task6.task6_args(tmp_path / "run")

    assert args.task2_semantic_checkpoint_after_day is None
    assert args.engineering_stop_after_day == "2026-01-02"
    assert args.expected_shared_execution_contract_sha256 is None
    assert args.build_prepared_day_pack_root == (
        tmp_path / "run" / "prepared-day-packs"
    )
    assert args.prepared_day_pack_root is None
    assert args.prepared_pack_encoding_workers == 4
    assert args.prepared_pack_target_raw_shard_bytes == 32 * 1024 * 1024
    assert args.prepared_day_pack_build_only is False
    assert args.compact_event_sink is True
    assert args.profiles == [task6.replay.PROFILE_REPAIRED]
    assert args.accepted_physical_reference is False
    assert args.tick_authority_cache_summary == task6.TASK3_TICK_AUTHORITY_SUMMARY
    assert (
        args.expected_tick_authority_cache_summary_sha256
        == task6.TASK3_TICK_AUTHORITY_SUMMARY_SHA256
    )
    assert args.tick_authority_cache_source_ledger == task6.TASK5_SOURCE_LEDGER
    assert (
        args.expected_tick_authority_cache_source_ledger_sha256
        == task6.TASK5_SOURCE_LEDGER_SHA256
    )

    pack_only = task6.task6_pack_only_args(tmp_path / "pack-only")
    assert pack_only.prepared_day_pack_build_only is True


def test_task6_factor_read_audit_allows_broad_factor_free_config_reads() -> None:
    assert task6.validate_factor_read_audit(
        {
            "factor_reads_detected": False,
            "factor_reads": [
                "*",
                "broad_live_as_if_replay_harness.*",
                "gtos_vnext_runtime.*",
                "data.lookback.M15",
            ],
        }
    ) == {
        "factor_read_count": 4,
        "factor_reads_detected": False,
        "factor_namespace_absent": True,
    }


def test_task6_factor_read_audit_rejects_explicit_harness_factor_path() -> None:
    with pytest.raises(
        task6.Task6PreparedPackRejected,
        match="^task6_factor_read_audit_invalid$",
    ):
        task6.validate_factor_read_audit(
            {
                "factor_reads_detected": False,
                "factor_reads": [
                    "broad_live_as_if_replay_harness."
                    "b7_5_selection_sizing_factorial_arm_binding.arm_id"
                ],
            }
        )
