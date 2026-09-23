from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage09_forward_replay_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage09", MODULE_PATH)
stage09 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage09
spec.loader.exec_module(stage09)


def test_select_better_score_prefers_higher_fidelity_mode():
    current = {
        "best_available_replay_mode": "bar_close_m15",
        "replay_mode_priority": stage09.REPLAY_MODE_PRIORITY["bar_close_m15"],
        "simulated_r": 1.5,
    }
    candidate = {
        "best_available_replay_mode": "m1_path_aware",
        "replay_mode_priority": stage09.REPLAY_MODE_PRIORITY["m1_path_aware"],
        "simulated_r": -1.0,
    }

    selected = stage09.select_better_score(current, candidate)

    assert selected["best_available_replay_mode"] == "m1_path_aware"


def test_select_better_score_prefers_non_null_r_before_fidelity():
    current = {
        "best_available_replay_mode": "tick_or_sierra_path_aware",
        "replay_mode_priority": stage09.REPLAY_MODE_PRIORITY["tick_or_sierra_path_aware"],
        "simulated_r": None,
    }
    candidate = {
        "best_available_replay_mode": "m1_path_aware",
        "replay_mode_priority": stage09.REPLAY_MODE_PRIORITY["m1_path_aware"],
        "simulated_r": 1.5,
    }

    selected = stage09.select_better_score(current, candidate)

    assert selected["best_available_replay_mode"] == "m1_path_aware"
    assert selected["simulated_r"] == 1.5


def test_selected_from_previous_requires_follow_and_positive_risk():
    selected, risk_pct, reason = stage09.selected_from_previous(
        {
            "route_decision": "FOLLOW",
            "pre_ai_would_action": "NARROW_AI_TO_ROUTE",
            "risk_would_multiplier": 0.5,
        },
        current_risk_pct=2.0,
    )

    assert selected is True
    assert risk_pct == 1.0
    assert reason == "selected_follow"

    selected, risk_pct, reason = stage09.selected_from_previous(
        {
            "route_decision": "FOLLOW",
            "pre_ai_would_action": "SKIP_AI_AVOID_ONLY",
            "risk_would_multiplier": 1.0,
        },
        current_risk_pct=2.0,
    )

    assert selected is False
    assert risk_pct == 0.0
    assert reason == "pre_ai_skip_avoid_only"


def _route_decision(label: str) -> stage09.GTOSVNextRuntimeDecision:
    return stage09.GTOSVNextRuntimeDecision(
        decision=label,
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=label != "LEGACY",
        reason="fixture",
        evidence={"metrics": {"effective_n": {"sum": 100}}},
    )


def _pre_ai(action: str = "ALLOW_AI") -> stage09.GTOSVNextPreAIRoutingDecision:
    return stage09.GTOSVNextPreAIRoutingDecision(
        action=action,
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="fixture",
        event={"symbol": "XAUUSD"},
        would_action=action,
    )


def test_stage09_executable_stream_requires_follow_in_kz_before_prop_budgeting():
    row = {"route_session": "london", "session_bucket": "london"}
    legacy = _route_decision("LEGACY")
    mixed = _route_decision("MIXED")
    follow = _route_decision("FOLLOW")

    cfg = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "legacy_blocks_execution": False,
            "mixed_blocks_execution": False,
            "block_min_effective_n": 0,
        }
    }
    assert stage09.vnext_execution_block_reason(legacy, cfg) is None
    assert stage09.vnext_execution_block_reason(mixed, cfg) is None

    legacy_stream = stage09.classify_stage09_executable_stream(
        row=row,
        pre_ai=_pre_ai(),
        route_decision=legacy,
    )
    mixed_stream = stage09.classify_stage09_executable_stream(
        row=row,
        pre_ai=_pre_ai(),
        route_decision=mixed,
    )
    follow_stream = stage09.classify_stage09_executable_stream(
        row=row,
        pre_ai=_pre_ai(),
        route_decision=follow,
    )

    assert legacy_stream["executable_stream"] is False
    assert legacy_stream["prop_governance_eligible"] is False
    assert legacy_stream["preserve_current_system_behavior"] is True
    assert mixed_stream["executable_stream"] is False
    assert mixed_stream["prop_governance_eligible"] is False
    assert mixed_stream["preserve_current_system_behavior"] is True
    assert follow_stream["executable_stream"] is True
    assert follow_stream["prop_governance_eligible"] is True


def test_stage09_executable_stream_excludes_off_kz_and_pre_ai_avoid_before_prop_budgeting():
    follow = _route_decision("FOLLOW")
    off_kz = stage09.classify_stage09_executable_stream(
        row={"route_session": "off_kz", "session_bucket": "off_kz"},
        pre_ai=_pre_ai(),
        route_decision=follow,
    )
    pre_ai_avoid = stage09.classify_stage09_executable_stream(
        row={"route_session": "london", "session_bucket": "london"},
        pre_ai=_pre_ai("SKIP_AI_AVOID_ONLY"),
        route_decision=follow,
    )

    assert off_kz["executable_stream"] is False
    assert off_kz["reason"] == "off_kz_diagnostic_non_executable"
    assert pre_ai_avoid["executable_stream"] is False
    assert pre_ai_avoid["reason"] == "pre_ai_skip_avoid_only"

    inert = stage09.unevaluated_prop_selector_for_non_executable(
        decision=follow,
        before_risk_pct=2.0,
        reason=off_kz["reason"],
    )
    assert inert.action == "ALLOW"
    assert inert.apply_to_execution is False
    assert inert.after_risk_pct == 2.0
    assert inert.external_rule_projection[
        "prop_budget_applies_only_to_executable_stream"
    ] is True


def test_stage09_no_paid_ai_replay_uses_mechanical_follow_contract():
    selected = stage09.vnext_ai_policy_no_paid_call_replay_decision(
        {
            "action": "MECHANICAL_FOLLOW_NO_AI",
            "would_action": "MECHANICAL_FOLLOW_NO_AI",
            "would_allow_ai_call": False,
        },
        production_selected=True,
    )
    diagnostic = stage09.vnext_ai_policy_no_paid_call_replay_decision(
        {
            "action": "CALL_AI_CONSTRAINED_VALIDATOR",
            "would_action": "CALL_AI_CONSTRAINED_VALIDATOR",
            "would_allow_ai_call": True,
        },
        production_selected=True,
    )

    assert selected["selected"] is True
    assert selected["reason"] == "selected_mechanical_follow_no_ai"
    assert diagnostic["selected"] is False
    assert diagnostic["status"] == "diagnostic_ai_required_not_selected"


def test_metric_accumulator_tracks_prop_budget_and_outcome_metrics():
    metrics = stage09.ScenarioMetrics("fixture")
    row = {
        "candle_time_utc": "2026-05-25T00:30:00+00:00",
        "symbol": "XAUUSD",
        "route_session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "route_family": "ob_retest",
    }
    metrics.add(
        row=row,
        selected=True,
        risk_pct=1.0,
        reason="selected_fixture",
        score={
            "simulated_r": 1.5,
            "terminal_outcome": "target_first",
            "best_available_replay_mode": "m1_path_aware",
        },
        missed=None,
    )
    metrics.add(
        row={**row, "candle_time_utc": "2026-05-25T01:00:00+00:00"},
        selected=False,
        risk_pct=0.0,
        reason="route_avoid_not_follow",
        score={
            "simulated_r": -1.0,
            "terminal_outcome": "stop_first",
            "best_available_replay_mode": "m1_path_aware",
        },
        missed={"classification": "avoided_loser"},
    )

    record = metrics.to_record()

    assert record["selected_count"] == 1
    assert record["performance_count"] == 1
    assert record["total_r"] == 1.5
    assert record["avoided_losers"] == 1
    assert record["min_daily_cushion"] > 0
    assert record["min_overall_cushion"] > 0


def _summary_fixture(*, selected_count: int, total_r: float, expectancy_r: float | None, profit_factor: float | None) -> dict:
    summary = {
        "candidate_rows": 253234,
        "written_replay_rows": 253234,
        "scenario_metrics": {
            name: {
                "selected_count": selected_count,
                "performance_count": selected_count,
                "total_r": total_r,
                "expectancy_r": expectancy_r,
                "profit_factor": profit_factor,
                "phase1_8pct_pass_proxy": True,
                "phase2_5pct_pass_proxy": True,
                "missed_winners": 0,
                "avoided_losers": 0,
                "accepted_winners": selected_count,
                "max_drawdown_pct": 0,
                "max_loss_streak": 0,
                "min_daily_cushion": 5000,
                "min_overall_cushion": 10000,
                "risk_reductions": 0,
                "deferred_trades": 0,
                "blocked_trades": 0,
            }
            for name in stage09.REQUIRED_SCENARIOS
        },
        "leakage_guard": {
            "future_outcome_inputs_used_count": 0,
            "paid_api_calls_made": 0,
            "broker_mutations_made": 0,
        },
        "redacted_account_budget_math": {
            "daily_loss_limit_pct": 5.0,
            "overall_max_loss_pct": 10.0,
        },
    }
    summary["scenario_metrics"]["baseline_current_shadow"]["selected_count"] = 100
    summary["scenario_metrics"]["new_ai_policy_no_paid_call"]["selected_count"] = selected_count
    summary["scenario_metrics"]["new_ai_policy_no_paid_call"]["expectancy_r"] = expectancy_r
    return summary


def test_verify_summary_accepts_viable_candidate_metrics():
    summary = _summary_fixture(
        selected_count=80,
        total_r=20.0,
        expectancy_r=0.25,
        profit_factor=1.5,
    )
    index_rows = [{"row_count": 253234}]

    assert stage09.verify_summary(summary, index_rows) == []


def test_verify_summary_rejects_catastrophic_or_no_trade_candidate():
    summary = _summary_fixture(
        selected_count=0,
        total_r=0.0,
        expectancy_r=None,
        profit_factor=None,
    )
    summary["scenario_metrics"]["new_production_change_mechanical"].update(
        {
            "phase1_8pct_pass_proxy": False,
            "phase2_5pct_pass_proxy": False,
            "blocked_trades": 216161,
            "missed_winners": 104440,
        }
    )
    index_rows = [{"row_count": 253234}]

    failures = stage09.verify_summary(summary, index_rows)

    assert any("production_candidate_failed" in failure for failure in failures)
    assert any("selected_count_zero" in failure for failure in failures)
