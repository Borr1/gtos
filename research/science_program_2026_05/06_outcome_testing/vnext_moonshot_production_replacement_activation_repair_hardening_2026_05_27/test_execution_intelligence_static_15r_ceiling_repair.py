from __future__ import annotations

import json
from pathlib import Path

import build_execution_intelligence_static_15r_ceiling_repair as mod
import build_execution_intelligence_dynamic_router_replay as router_replay


def test_plain_jsonl_shard_writer_does_not_compress_jsonl(tmp_path):
    stem = tmp_path / "ledger"
    manifest = tmp_path / "ledger.manifest.jsonl"
    writer = mod.PlainJsonlShardWriter(
        ledger_name="unit",
        stem=stem,
        manifest_path=manifest,
        max_rows_per_shard=2,
    )
    writer.reset()
    for idx in range(3):
        writer.write({"row": idx})
    writer.close()

    entries = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    assert [entry["row_count"] for entry in entries] == [2, 1]
    for entry in entries:
        path = tmp_path / entry["path"].split("/")[-1]
        assert path.suffix == ".jsonl"
        assert entry["compressed"] is False
        assert json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def test_be_after_trigger_saves_late_stop_after_trigger():
    path = [
        {"i": 0, "time": "t0", "max_r": 1.1, "min_r": -0.2, "close_r": 1.0},
        {"i": 1, "time": "t1", "max_r": 1.2, "min_r": -0.1, "close_r": 0.1},
    ]

    fixed = mod.simulate_target_stop(path, "fixed_1_5r", 1.5)
    be = mod.simulate_be(path)

    assert fixed["gross_r"] == 0.1
    assert be["gross_r"] == 0.0
    assert be["exit_reason"] == "breakeven_stop"


def test_empty_path_marks_every_policy_non_replayable():
    results = mod.simulate_policies([], {}, None)

    assert set(results) == set(mod.POLICIES)
    assert all(row["simulation_status"] == "not_replayable_missing_source" for row in results.values())
    assert all(row["gross_r"] is None for row in results.values())


def test_runtime_support_has_multiple_implemented_policies_and_blockers():
    implemented = {
        policy
        for policy in mod.POLICIES
        if mod.runtime_support(policy)["runtime_supported_now"]
    }

    assert {
        "be_after_trigger",
        "partial_be_runner",
        "trailing_runner",
        "momentum_exhaustion",
        "time_stop",
    }.issubset(implemented)
    trailing = mod.runtime_support("trailing_runner")
    momentum = mod.runtime_support("momentum_exhaustion")
    assert trailing["runtime_supported_now"] is True
    assert momentum["runtime_supported_now"] is True
    assert trailing["test_evidence"].endswith(
        "test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router"
    )
    assert momentum["test_evidence"].endswith(
        "test_vnext_momentum_exhaustion_pending_fill_closes_on_pullback_from_router"
    )
    diagnostic = mod.runtime_support("m1_tick_path_exit")
    assert diagnostic["runtime_supported_now"] is False
    assert diagnostic["missing_code_path"]
    assert diagnostic["required_test"]


def test_final_dynamic_router_replay_summary_is_full_denominator_not_prior_projection():
    summary_path = Path(router_replay.SUMMARY)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["selected_rows_processed"] == 289600
    assert summary["condition_router_projection_gap_carried_forward_rows"] == 0
    assert summary["prior_condition_router_projection_dependency"] is False
    assert summary["router_refused_rows"] == 0
    assert sum(summary["policy_distribution"].values()) == 289600
    assert "fixed_1_5r" not in summary["policy_distribution"]
    assert set(summary["policy_distribution"]) == {
        "partial_be_runner",
        "momentum_exhaustion",
    }
    assert summary["final_dynamic_router_metrics"]["rows"] == (
        289600 - summary["non_replayable_rows"]
    )
    assert summary["global_policy_comparison_metrics"]["fixed_1_5r"]["rows"] == (
        289600 - summary["non_replayable_rows"]
    )
    assert summary["hindsight_best_regret"]["rows"] == (
        289600 - summary["non_replayable_rows"]
    )


def test_outside_session_rows_normalize_to_live_off_kz_router_bucket():
    bucket, reason = router_replay.session_bucket_for_row(
        {
            "selector_component": "broader_origin_outside_session_expansion",
            "route_session": "moonshot_h03_04",
        }
    )

    assert bucket == "off_kz_broad"
    assert "outside_session" in reason
