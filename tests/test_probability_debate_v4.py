from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from src.components.orchestrator import SessionOrchestrator
from src.components.live_decision_packet_v4 import build_live_decision_packet_v4
from src.components.probability_debate_v4 import (
    ALL_ACTIONS,
    ProbabilityDebateTeamEngineV4,
    calibration_metrics,
    probability_debate_v4_execution_block_reason,
)


def _config(tmp_path: Path | None = None, *, apply_to_execution: bool = True) -> dict:
    log_path = (
        str(tmp_path / "probability_debate_v4.jsonl")
        if tmp_path is not None else "shadow_logs/probability_debate_team_engine_v4.jsonl"
    )
    return {
        "gtos_vnext_runtime": {
            "probability_debate_team_engine_v4": {
                "enabled": True,
                "apply_to_execution": apply_to_execution,
                "runtime_disposition": "active_v4_authority",
                "decision_log_enabled": True,
                "decision_log_path": log_path,
                "required_source_families": [
                    "selector",
                    "market_state",
                    "cost",
                    "lifecycle",
                    "source_completeness",
                ],
                "min_trade_probability": 0.55,
                "min_trade_ev_r": 0.0,
                "risk_actions_require_cost_source": True,
            }
        }
    }


def _complete_long_context() -> dict:
    return {
        "candidate_id": "candidate-1",
        "symbol": "XAUUSD",
        "route_session": "london",
        "candidate_direction": "LONG",
        "risk_reward_ratio": 2.0,
        "cost_r": 0.04,
        "open_position_present": False,
        "sources": [
            {
                "source_id": "selector-follow",
                "source_family": "selector",
                "stance": "FOLLOW",
                "direction": "LONG",
                "strength": 0.90,
                "confidence": 0.86,
                "reliability": 0.82,
                "freshness": 1.0,
                "source_completeness": 0.90,
                "cost_sensitivity": 0.04,
                "evidence_class": "production_code_runtime_evidence",
            },
            {
                "source_id": "market-follow",
                "source_family": "market_state",
                "stance": "FOLLOW",
                "direction": "LONG",
                "strength": 0.72,
                "confidence": 0.76,
                "reliability": 0.70,
                "freshness": 0.95,
                "source_completeness": 0.82,
                "evidence_class": "market_whiteboard_source_bound_runtime_evidence",
            },
            {
                "source_id": "cost-ok",
                "source_family": "cost",
                "stance": "FOLLOW",
                "direction": "LONG",
                "strength": 0.65,
                "confidence": 0.70,
                "reliability": 0.68,
                "freshness": 1.0,
                "source_completeness": 0.75,
                "cost_sensitivity": 0.04,
                "evidence_class": "pretrade_cost_runtime_evidence",
            },
            {
                "source_id": "lifecycle-flat",
                "source_family": "lifecycle",
                "stance": "DIRECT",
                "action": "wait",
                "strength": 0.45,
                "confidence": 0.65,
                "reliability": 0.65,
                "freshness": 1.0,
                "source_completeness": 0.70,
                "evidence_class": "ticket_bound_lifecycle_runtime_evidence",
            },
            {
                "source_id": "source-complete",
                "source_family": "source_completeness",
                "stance": "FOLLOW",
                "direction": "LONG",
                "strength": 0.80,
                "confidence": 0.80,
                "reliability": 0.80,
                "freshness": 1.0,
                "source_completeness": 0.88,
                "evidence_class": "runtime_source_completeness_evidence",
            },
        ],
    }


def _thesis(decision, action: str) -> dict:
    rows = {row["action"]: row for row in decision.to_record()["theses"]}
    return rows[action]


def test_probability_debate_v4_emits_all_eight_numeric_theses(tmp_path: Path) -> None:
    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(_complete_long_context())
    record = decision.to_record()

    assert [row["action"] for row in record["theses"]] == list(ALL_ACTIONS)
    assert decision.selected_action == "long"
    assert _thesis(decision, "long")["probability"] > 0.55
    assert _thesis(decision, "long")["EV"] > 0
    assert (
        "scale_requires_ticket_bound_lifecycle_approval"
        in _thesis(decision, "scale")["vetoes"]
    )
    assert record["broker_runtime_change_status"] is False
    assert record["validation_result_status"] is False
    assert record["outcome_result_rows_status"] is False
    assert len(record["source_event_hash_sha256"]) == 64
    assert len(record["packet_hash_sha256"]) == 64
    assert record["field_group_statuses"]["sources"]["source_count"] == 5
    assert record["field_group_statuses"]["theses"]["action_count"] == len(ALL_ACTIONS)


def test_live_decision_packet_binds_probability_debate_team_record_shape(
    tmp_path: Path,
) -> None:
    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(_complete_long_context())
    packet = build_live_decision_packet_v4(
        record={
            "decision_pipeline": {
                "probability_debate_team_engine_v4": decision.to_record(),
            }
        },
        legacy_packet={
            "candidate_identity": {
                "candidate_id": "candidate-1",
                "broker_symbol": "XAUUSD",
            },
            "source_m15": {
                "candle_close_utc": "2026-01-01T00:00:00+00:00",
                "timeframe": "M15",
            },
            "source_completeness": {"source_window_complete": True},
            "order_readiness": {"order_path": "replay"},
        },
        candidate={"candidate_id": "candidate-1", "symbol": "XAUUSD"},
        raw_data={
            "symbol": "XAUUSD",
            "source_hash": "fixture-source-hash",
            "candle_close_utc": "2026-01-01T00:00:00+00:00",
        },
        runtime_config={},
    )

    group = packet["field_groups"]["probability_debate_numeric_theses"]
    assert group["group_source_status"] == "captured_present"
    assert not [
        field
        for field in group["missing_fields"]
        if str(field).startswith("numeric_theses.")
    ]
    assert set(group["numeric_theses"]) == {
        "long",
        "short",
        "no_trade",
        "wait",
        "scale",
        "reduce",
        "close",
        "reverse",
    }


def test_follow_is_not_automatic_permission_when_sources_are_missing(tmp_path: Path) -> None:
    context = {
        "candidate_id": "candidate-missing-cost",
        "symbol": "XAUUSD",
        "candidate_direction": "LONG",
        "risk_reward_ratio": 2.0,
        "sources": [
            {
                "source_id": "selector-follow-only",
                "source_family": "selector",
                "stance": "FOLLOW",
                "direction": "LONG",
                "strength": 0.95,
                "confidence": 0.90,
                "reliability": 0.80,
                "freshness": 1.0,
                "source_completeness": 0.80,
            }
        ],
    }

    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(context)
    long_thesis = _thesis(decision, "long")

    assert "risk_action_requires_cost_source" in long_thesis["vetoes"]
    assert decision.selected_action in {"no-trade", "wait"}
    assert decision.source_summary["missing_source_families"] == [
        "market_state",
        "cost",
        "lifecycle",
        "source_completeness",
    ]


def test_risk_actions_veto_every_missing_required_source_family(tmp_path: Path) -> None:
    context = _complete_long_context()
    context["sources"] = [
        source
        for source in context["sources"]
        if source["source_family"] not in {"market_state", "lifecycle", "source_completeness"}
    ]

    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(context)
    long_vetoes = set(_thesis(decision, "long")["vetoes"])
    short_vetoes = set(_thesis(decision, "short")["vetoes"])

    for expected in (
        "risk_action_requires_lifecycle_source",
        "risk_action_requires_market_state_source",
        "risk_action_requires_source_completeness_source",
    ):
        assert expected in long_vetoes
        assert expected in short_vetoes
    assert "risk_action_requires_cost_source" not in long_vetoes


def test_probability_debate_rejects_future_result_evidence_as_source(
    tmp_path: Path,
) -> None:
    context = _complete_long_context()
    context["sources"] = [
        {
            **context["sources"][0],
            "evidence_class": "post_decision_outcome_final_r_result_row",
        },
        *context["sources"][1:],
    ]

    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(context)
    record = decision.to_record()
    invalid_source = record["source_summary"]["sources"][0]
    long_thesis = _thesis(decision, "long")

    assert invalid_source["source_contract_status"] == "source_contract_violation"
    assert invalid_source["usable_weight"] == 0.0
    assert "selector" in record["source_summary"]["missing_source_families"]
    assert any(
        "forbidden_future_or_result_evidence_class" in item
        for item in record["source_summary"]["invalid_source_evidence_class_fields"]
    )
    assert "risk_action_requires_selector_source" in long_thesis["vetoes"]


def test_probability_debate_allows_negated_broker_real_cash_proxy_label(
    tmp_path: Path,
) -> None:
    context = _complete_long_context()
    context["sources"][2]["evidence_class"] = "proxy cost not broker-real cash"

    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(context)
    record = decision.to_record()
    cost_source = record["source_summary"]["sources"][2]

    assert cost_source["source_contract_status"] == "predecision_source_allowed"
    assert cost_source["source_contract_violation"] is None
    assert "cost" not in record["source_summary"]["missing_source_families"]


def test_structured_disagreement_prefers_wait_or_no_trade(tmp_path: Path) -> None:
    context = _complete_long_context()
    context["sources"] = [
        context["sources"][0],
        {
            "source_id": "avoid-cost",
            "source_family": "cost",
            "stance": "AVOID",
            "direction": "LONG",
            "strength": 0.92,
            "confidence": 0.88,
            "reliability": 0.80,
            "freshness": 1.0,
            "source_completeness": 0.80,
            "cost_sensitivity": 0.95,
            "invalidation_type": "cost_drag",
        },
        {
            "source_id": "mixed-market",
            "source_family": "market_state",
            "stance": "MIXED",
            "direction": "LONG",
            "strength": 0.90,
            "confidence": 0.80,
            "reliability": 0.75,
            "freshness": 1.0,
            "source_completeness": 0.75,
            "conflict_reason": "long_signal_inside_adverse_cost_state",
        },
        context["sources"][3],
        context["sources"][4],
    ]

    decision = ProbabilityDebateTeamEngineV4(_config(tmp_path)).evaluate(context)

    assert decision.selected_action in {"wait", "no-trade"}
    assert _thesis(decision, "long")["disagreement_state"] in {
        "mixed_structured_disagreement",
        "high_structured_disagreement",
    }


def test_calibration_metrics_compute_brier_ece_logloss_and_bins() -> None:
    result = calibration_metrics(
        [
            {"probability": 0.90, "outcome": 1},
            {"probability": 0.80, "outcome": 1},
            {"probability": 0.30, "outcome": 0},
            {"probability": 0.20, "outcome": 0},
        ],
        bin_count=5,
    )

    assert result["status"] == "calibration_metrics_computed"
    assert result["row_count"] == 4
    assert result["Brier"] < 0.08
    assert result["ECE"] >= 0
    assert result["logloss"] > 0
    assert len(result["reliability_bins"]) == 5


def test_probability_debate_execution_block_honors_apply_flag(tmp_path: Path) -> None:
    context = {
        "candidate_id": "candidate-wait",
        "symbol": "XAUUSD",
        "candidate_direction": "LONG",
        "sources": [
            {
                "source_id": "mixed-selector",
                "source_family": "selector",
                "stance": "MIXED",
                "direction": "LONG",
                "strength": 0.80,
                "confidence": 0.70,
                "reliability": 0.60,
                "freshness": 1.0,
                "source_completeness": 0.65,
            }
        ],
    }
    default_off_decision = ProbabilityDebateTeamEngineV4(
        _config(tmp_path, apply_to_execution=False)
    ).evaluate(context)
    active_decision = ProbabilityDebateTeamEngineV4(
        _config(tmp_path, apply_to_execution=True)
    ).evaluate(context)

    assert probability_debate_v4_execution_block_reason(
        default_off_decision,
        _config(tmp_path, apply_to_execution=False),
    ) is None
    assert probability_debate_v4_execution_block_reason(
        active_decision,
        _config(tmp_path, apply_to_execution=True),
    ) is not None


def test_orchestrator_attaches_probability_debate_v4_packet(tmp_path: Path) -> None:
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _config(tmp_path)
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    orch._vnext_effective_candle_time = lambda raw: "2026-06-04T12:00:00Z"
    analysis = SimpleNamespace(
        trade_parameters=SimpleNamespace(
            direction="LONG",
            risk_reward_ratio=2.0,
        )
    )
    vnext_decision = SimpleNamespace(
        decision="FOLLOW",
        matched=True,
        reason="test_follow",
        event={"side": "LONG", "symbol": "XAUUSD"},
        evidence={
            "metrics": {
                "effective_n": {"sum": 30},
                "proxy_score": {"sum": 8.0},
                "cost_adjusted_simulated_r": {"sum": 4.0},
            }
        },
    )
    record: dict = {"candidate_id": "candidate-runtime"}

    decision = orch._evaluate_probability_debate_team_v4(
        analysis=analysis,
        raw_data={
            "candidate_id": "candidate-runtime",
            "source_complete": True,
            "selected_cell_pretrade_cost_r": 0.04,
        },
        kill_zone="london",
        record=record,
        vnext_decision=vnext_decision,
    )

    assert decision is not None
    packet = record["decision_pipeline"]["probability_debate_team_engine_v4"]
    assert packet["selected_action"] == "long"
    assert record["instrumentation"]["probability_debate_v4_apply_to_execution"] is True
    rows = [
        json.loads(line)
        for line in (tmp_path / "probability_debate_v4.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["decision"]["selected_action"] == "long"
