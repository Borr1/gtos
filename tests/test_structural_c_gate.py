from __future__ import annotations

from types import SimpleNamespace

import yaml

from src.components.orchestrator import SessionOrchestrator
from src.components.structural_c_gate import evaluate_structural_c_gate


def _cfg(**overrides):
    block = {
        "enabled": True,
        "apply_to_ai_call": True,
        "only_when_deterministic_bias_absent": True,
        "d1_lag_h4_h1_consensus_enabled": True,
        "d1_lag_nas100_blocked_candles": 54,
        "d1_lag_nas100_rally_pct": 4.20,
        "t6_cgate_pass_wr_pct": 69.4,
        "t6_cgate_pass_total_r": 44.2,
        "q_score_correlation_r": -0.06,
        "q_score_correlation_p": 0.574,
    }
    block.update(overrides)
    return {"structural_c_gate": block}


def _mso(d1=None, h4=None, h1="bullish", m15="unavailable"):
    def tf(direction):
        return SimpleNamespace(structure=SimpleNamespace(direction=direction))

    timeframes = {}
    for name, direction in (("D1", d1), ("H4", h4), ("H1", h1), ("M15", m15)):
        if direction is not None:
            timeframes[name] = tf(direction)
    return SimpleNamespace(timeframes=timeframes)


def test_h1_bias_and_non_opposing_m15_routes_ai_side_when_higher_tf_bias_absent():
    decision = evaluate_structural_c_gate(
        mso=_mso(h1="bullish", m15="transitional"),
        bias_result={"bias": "no_bias", "h1": "bullish", "m15": "transitional"},
        config=_cfg(),
    )

    assert decision.action == "NARROW_AI_TO_SIDE"
    assert decision.side == "LONG"
    assert decision.bias == "bullish"
    assert decision.reason == "structural_c_gate_h1_bias_m15_not_opposing"
    assert decision.evidence["t6_cgate_pass_wr_pct"] == 69.4
    assert decision.evidence["q_score_correlation_r"] == -0.06


def test_opposing_m15_skips_ai_when_structural_c_gate_active():
    decision = evaluate_structural_c_gate(
        mso=_mso(h1="bullish", m15="bearish"),
        bias_result={"bias": "no_bias", "h1": "bullish", "m15": "bearish"},
        config=_cfg(),
    )

    assert decision.action == "SKIP_AI_M15_OPPOSES_H1"
    assert decision.would_action == "SKIP_AI_M15_OPPOSES_H1"
    assert decision.side == "LONG"
    assert decision.reason == "structural_c_gate_m15_opposes_h1"


def test_missing_h1_bias_skips_ai_instead_of_spending_primary_call():
    decision = evaluate_structural_c_gate(
        mso=_mso(h1="transitional", m15="bullish"),
        bias_result={"bias": "no_bias", "h1": "transitional", "m15": "bullish"},
        config=_cfg(),
    )

    assert decision.action == "SKIP_AI_NO_H1_BIAS"
    assert decision.reason == "structural_c_gate_no_h1_directional_bias"


def test_existing_higher_timeframe_bias_preserves_legacy_ai_path():
    decision = evaluate_structural_c_gate(
        mso=_mso(h1="bullish", m15="bearish"),
        bias_result={"bias": "bullish", "h1": "bullish", "m15": "bearish"},
        config=_cfg(),
    )

    assert decision.action == "ALLOW_AI"
    assert decision.reason == "higher_timeframe_bias_already_available"


def test_d1_lag_h4_h1_consensus_routes_against_stale_d1_bias():
    decision = evaluate_structural_c_gate(
        mso=_mso(d1="bearish", h4="bullish", h1="bullish", m15="transitional"),
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bullish",
            "h1": "bullish",
            "m15": "transitional",
        },
        config=_cfg(),
    )

    assert decision.action == "NARROW_AI_TO_SIDE"
    assert decision.side == "LONG"
    assert decision.bias == "bullish"
    assert decision.reason == "structural_c_gate_d1_lag_h4_h1_consensus"
    assert decision.evidence["d1_lag_h4_h1_consensus"] is True
    assert decision.evidence["source_path"] == (
        ".context/02_session_handoffs/33_apr19_session_close_handoff.md"
    )
    assert decision.evidence["nas100_w14_blocked_candles"] == 54
    assert decision.evidence["nas100_w14_rally_pct"] == 4.20


def test_d1_lag_m15_opposes_h4_h1_consensus_skips_ai():
    decision = evaluate_structural_c_gate(
        mso=_mso(d1="bearish", h4="bullish", h1="bullish", m15="bearish"),
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bullish",
            "h1": "bullish",
            "m15": "bearish",
        },
        config=_cfg(),
    )

    assert decision.action == "SKIP_AI_M15_OPPOSES_H1"
    assert decision.side == "LONG"
    assert decision.reason == "structural_c_gate_d1_lag_m15_opposes_h4_h1_consensus"


def test_d1_lag_config_off_preserves_legacy_d1_path():
    decision = evaluate_structural_c_gate(
        mso=_mso(d1="bearish", h4="bullish", h1="bullish", m15="transitional"),
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bullish",
            "h1": "bullish",
            "m15": "transitional",
        },
        config=_cfg(d1_lag_h4_h1_consensus_enabled=False),
    )

    assert decision.action == "ALLOW_AI"
    assert decision.reason == "higher_timeframe_bias_already_available"


def test_shadow_mode_records_would_action_without_changing_ai_call():
    decision = evaluate_structural_c_gate(
        mso=_mso(h1="bearish", m15="unavailable"),
        bias_result={"bias": "no_bias", "h1": "bearish", "m15": "unavailable"},
        config=_cfg(apply_to_ai_call=False),
    )

    assert decision.action == "ALLOW_AI"
    assert decision.would_action == "NARROW_AI_TO_SIDE"
    assert decision.side == "SHORT"


def test_orchestrator_structural_c_gate_hook_attaches_runtime_decision():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _cfg()
    raw_data = {}

    decision = orch._evaluate_structural_c_gate_pre_ai(
        mso=_mso(h1="bearish", m15="bearish"),
        raw_data=raw_data,
        kill_zone="london",
        bias_result={"bias": "no_bias", "h1": "bearish", "m15": "bearish"},
    )

    assert decision.action == "NARROW_AI_TO_SIDE"
    assert raw_data["structural_c_gate_decision"]["side"] == "SHORT"
    assert raw_data["structural_c_gate_decision"]["evidence"]["source_line_no"] == 85


def test_orchestrator_applies_d1_lag_route_to_runtime_bias():
    decision = evaluate_structural_c_gate(
        mso=_mso(d1="bearish", h4="bullish", h1="bullish", m15="transitional"),
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bullish",
            "h1": "bullish",
            "m15": "transitional",
        },
        config=_cfg(),
    )

    routed = SessionOrchestrator._apply_structural_c_gate_pre_ai_route(
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bullish",
            "h1": "bullish",
            "m15": "transitional",
        },
        structural_c_gate=decision,
    )

    assert routed["bias"] == "bullish"
    assert routed["source"] == "structural_c_gate_d1_lag_h4_h1_consensus"
    assert routed["structural_c_gate_original_bias"] == "bearish"
    assert routed["structural_c_gate_original_source"] == "D1"
    assert routed["structural_c_gate"]["side"] == "LONG"


def test_agent_config_activates_structural_c_gate_runtime_path():
    with open("config/agent_config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    block = cfg["structural_c_gate"]
    assert block["enabled"] is True
    assert block["apply_to_ai_call"] is True
    assert block["only_when_deterministic_bias_absent"] is True
    assert block["d1_lag_h4_h1_consensus_enabled"] is True
    assert block["d1_lag_nas100_blocked_candles"] == 54
    assert block["d1_lag_nas100_rally_pct"] == 4.20
    assert block["t6_cgate_pass_total_r"] == 44.2
