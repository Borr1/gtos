from __future__ import annotations

from scripts import analyze_lane2_c7_c9_path_scaling_triage as triage


def test_lane2_triage_classifies_c7_and_c9():
    payload = triage.build_payload()
    tasks = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert tasks["C-7"]["status"] == "DONE"
    assert tasks["C-9"]["status"] == "BLOCKED_WITH_REASON"
    assert tasks["C-7"]["promotion_allowed"] is False
    assert tasks["C-9"]["promotion_allowed"] is False


def test_c7_path9_is_feb_heavy_cross_cohort_but_not_stable_all_window():
    payload = triage.build_payload()
    c7 = payload["c7_path9_deep_dive"]
    path_summary = payload["c7_k54_v2_fixed_hp_path_summary"]

    assert c7["feb_2026_share"] > 0.60
    assert c7["top_symbol_share"] < 0.20
    assert c7["positive_group_count"] == c7["group_count"]
    assert c7["positive_symbol_count"] == 6
    assert c7["path_rank_by_auc_diff"] == 1
    assert path_summary["negative_path_count"] >= 1

    fold_diffs = {row["fold"]: row["auc_diff"] for row in payload["c7_fold_replication_scan"]}
    assert fold_diffs[2] > 0.15
    assert fold_diffs[4] < 0.0


def test_c9_blockers_preserve_partial_chain_without_promotion():
    payload = triage.build_payload()
    c9 = payload["c9_path_scaling_status"]

    assert c9["status"] == "BLOCKED_WITH_REASON"
    assert c9["v2b_scope_counters"]["wanted_resolved_rows_after_cutoff"] == 0
    assert c9["v3_fvg_only_rescue"]["mean_delta_vs_j46"] > 0.25
    assert any("L2 candidate reconstruction" in blocker for blocker in c9["blockers"])
    assert any("pending lifecycle" in blocker for blocker in c9["blockers"])
