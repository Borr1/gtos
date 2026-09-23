from __future__ import annotations

from pathlib import Path

from src.research_infra import (
    replay_acceleration_task5_compact_sink_runner as task5,
)


def test_task5_args_enable_only_bounded_append_only_sink_roles(tmp_path: Path) -> None:
    args = task5.task5_args(tmp_path / "run")

    assert args.compact_event_sink is True
    assert args.compact_event_max_shard_bytes == 128 * 1024 * 1024
    assert args.chunk_size == 1
    assert args.profiles == [task5.replay.PROFILE_REPAIRED]
    assert args.omit_candidate_ledger is True
    assert args.omit_candidate_index_ledger is True
    assert args.compact_decision_ledger is True
    assert args.compact_missed_ledger is True
    assert args.accepted_physical_reference is False
    assert args.task2_semantic_checkpoint_after_day == "2026-01-02"
