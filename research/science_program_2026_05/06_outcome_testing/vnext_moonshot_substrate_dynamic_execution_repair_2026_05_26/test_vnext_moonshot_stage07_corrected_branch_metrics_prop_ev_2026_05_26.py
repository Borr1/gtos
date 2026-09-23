from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def load_jsonl(name: str) -> list[dict]:
    path = ROUTE_DIR / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_stage07_summary_advances_to_stage08() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["events_replayed"] == 214536
    assert summary["legacy_fixed_1_5r_rejected_as_activation_truth"] is True
    assert summary["segmented_prop_attempts_not_continuous_account"] is True
    assert summary["first_incomplete_invariant_after_stage07"] == "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"
    assert state["first_incomplete_invariant"] == "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"


def test_stage07_branch_metrics_use_corrected_dynamic_labels() -> None:
    rows = load_jsonl(f"VNEXT_MOONSHOT_CORRECTED_BRANCH_METRICS_LEDGER_{DATE_ID}.jsonl")
    raw_policies = {
        row["policy_name"]
        for row in rows
        if row["branch_id"] == "raw_repaired_all_replayable" and row.get("policy_name")
    }
    assert {
        "legacy_fixed_1.5r",
        "live_current_j46_j49",
        "be_after_trigger",
        "partial_be_runner",
        "trailing_runner",
    }.issubset(raw_policies)
    live_raw = next(
        row
        for row in rows
        if row["branch_id"] == "raw_repaired_all_replayable" and row["policy_name"] == "live_current_j46_j49"
    )
    assert live_raw["row_count"] == 214536
    assert live_raw["corrected_dynamic_label_source"] == "Stage04 policy_results.final_r"
    assert live_raw["fixed_1_5r_used_as_activation_truth"] is False
    assert "legacy_winner_to_policy_nonpositive" in live_raw["legacy_fixed_1_5r_transition_counts"]


def test_stage07_prop_ev_attempt_rows_cover_actions_and_ev() -> None:
    rows = load_jsonl(f"VNEXT_MOONSHOT_PROP_EV_ATTEMPT_LEDGER_{DATE_ID}.jsonl")
    policies = {row["prop_policy"] for row in rows}
    assert "EV_OPTIMIZED_REDUCE_OR_DEFER" in policies
    assert "ACCOUNT_ABANDON_OR_RESTART" in policies
    assert "BLOCK_ALL_NEAR_LIMIT" in policies
    assert all(row["segmented_account_attempts_modelled"] is True for row in rows)
    assert any(row["action_counts"] for row in rows)
    assert any(row["expected_payout_proxy_usd_fee599_payout8000"] is not None for row in rows)


def test_stage07_registry_only_origins_are_bounded() -> None:
    rows = load_jsonl(f"VNEXT_MOONSHOT_CORRECTED_BRANCH_METRICS_LEDGER_{DATE_ID}.jsonl")
    registry_rows = [row for row in rows if row["selection_class"] == "candidate_origin_registry_only"]
    assert len(registry_rows) >= 10
    assert all(row["prop_replay_eligible"] is False for row in registry_rows)
    assert any(row["branch_id"] == "origin_registry_only_cross_asset_lead_lag" for row in registry_rows)
