from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage06_summary_advances_to_branch_metrics() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["feature_rows"] == summary["expected_stage04_replayable_rows"]
    assert summary["feature_rows"] == 214536
    assert summary["forbidden_leakage_fields_used"] is False
    assert summary["first_incomplete_invariant_after_stage06"] == "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"
    assert state["first_incomplete_invariant"] == "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"


def test_stage06_field_classification_separates_asof_and_labels() -> None:
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FIELD_CLASSIFICATION_LEDGER_{DATE_ID}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    classes = {row["field_safety_class"] for row in rows}
    assert "decision_safe_asof" in classes
    assert "post_outcome_label" in classes
    assert "missing" in classes
    assert "forward_capture_required" in classes
    assert "forbidden_leakage" in classes
    assert any(row["field_name"] == "mfe_r" and row["allowed_for_decision_feature"] is False for row in rows)
    assert any(row["field_name"] == "trend_state_20" and row["allowed_for_decision_feature"] is True for row in rows)


def test_stage06_distribution_ledger_has_denominator_and_selected_scopes() -> None:
    rows = [
        json.loads(line)
        for line in (ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_DISTRIBUTION_LEDGER_{DATE_ID}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    scopes = {row["coverage_scope"] for row in rows}
    assert "denominator_all_replayable_m15_dynamic_rows" in scopes
    assert "selected_positive_live_current_j46_j49" in scopes
    assert any(scope.startswith("full_stage04_terminal_counts::") for scope in scopes)
    assert all(row["no_arbitrary_top_n"] is True for row in rows)


def test_stage06_feature_ledger_first_row_has_market_awareness_keys() -> None:
    ledger = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
    first = json.loads(next(line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()))
    for key in [
        "trend_state_20",
        "volatility_state_14_vs_50",
        "compression_expansion_state",
        "session_subwindow",
        "kill_zone_position",
        "news_calendar_coverage_status",
        "liquidity_sweep_proxy_state",
        "live_current_j46_j49_final_r",
        "mfe_r",
        "mae_r",
        "adverse_excursion_bucket",
        "policy_reversal_bucket",
        "mfe_mae_timing_status",
    ]:
        assert key in first
    assert first["forbidden_leakage_fields_used"] is False
