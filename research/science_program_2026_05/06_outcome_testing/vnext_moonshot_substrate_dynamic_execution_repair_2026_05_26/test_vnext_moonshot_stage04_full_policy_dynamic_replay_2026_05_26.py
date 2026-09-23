from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage04_summary_is_dynamic_policy_not_static_label() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_{DATE_ID}.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["scope"] == "universal_bar_close_m15_first_pass_every_replayable_candidate"
    assert summary["same_bar_policy"] == "conservative"
    assert summary["replayable_candidate_rows"] > 100000
    assert "live_current_j46_j49" in summary["policy_expectancy_r"]
    assert "legacy_fixed_1.5r" in summary["policy_expectancy_r"]
    assert summary["first_incomplete_invariant_after_stage04"] == "STAGE_05_UNIVERSAL_CANDIDATE_ORIGIN_LAYER"


def test_stage04_first_output_row_contains_all_policy_results() -> None:
    index_rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    first_with_rows = next(row for row in index_rows if row["replayable_candidate_rows"] > 0)
    output_path = Path(first_with_rows["output_chunk_path"])
    first_row = None
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                first_row = json.loads(line)
                break
    assert first_row is not None
    policies = set(first_row["policy_results"])
    assert {
        "legacy_fixed_1.5r",
        "ai_target",
        "live_current_j46_j49",
        "partial_be_runner",
        "be_after_trigger",
        "trailing_runner",
        "time_stop_only",
        "early_cut_if_no_progress",
        "path_aware_runner",
    } <= policies
    assert first_row["old_static_terminal_outcome"] in {
        "target_first",
        "stop_first",
        "same_bar_ambiguous_unresolved",
        "timeout",
    }
