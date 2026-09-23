import pytest
import yaml

from src.components.autocorrelation_risk import (
    attach_autocorrelation_risk_to_record,
    evaluate_autocorrelation_risk,
    rolling_return_autocorrelation,
)
from src.components.orchestrator import SessionOrchestrator


def _raw_from_returns(returns):
    close = 100.0
    candles = []
    for ret in returns:
        close *= 1.0 + ret
        candles.append({"close": close})
    return {"candles": {"H1": [{"close": 100.0}, *candles]}}


def test_rolling_h1_autocorrelation_detects_positive_and_decayed_momentum():
    positive = rolling_return_autocorrelation(
        [100.0, *[100.0 + (idx * idx * 0.01) for idx in range(1, 22)]],
        window=20,
    )
    negative = rolling_return_autocorrelation(
        [candle["close"] for candle in _raw_from_returns([0.01, -0.01] * 11)["candles"]["H1"]],
        window=20,
    )

    assert positive is not None and positive > 0.5
    assert negative is not None and negative < -0.5


def test_autocorrelation_risk_reduces_risk_when_h1_momentum_decays():
    decision = evaluate_autocorrelation_risk(
        current_risk_pct=1.0,
        raw_data=_raw_from_returns([0.01, -0.01] * 11),
        config={
            "risk": {
                "autocorrelation_sizing": {
                    "enabled": True,
                    "apply_to_execution": True,
                    "window": 20,
                    "min_autocorrelation": 0.0,
                    "decay_risk_multiplier": 0.5,
                }
            }
        },
    )

    assert decision.applied is True
    assert decision.reason == "h1_autocorrelation_decay_risk_reduction"
    assert decision.after_risk_pct == pytest.approx(0.5)
    assert decision.autocorrelation < 0
    assert decision.source_artifact_path == (
        ".context/01_knowledge_base/kb_edge_mechanisms_and_risks.md"
    )


def test_autocorrelation_risk_preserves_risk_when_h1_momentum_positive():
    raw_data = _raw_from_returns([0.001 * idx for idx in range(1, 23)])
    decision = evaluate_autocorrelation_risk(
        current_risk_pct=1.0,
        raw_data=raw_data,
        config={"risk": {"autocorrelation_sizing": {"enabled": True}}},
    )

    assert decision.applied is False
    assert decision.reason == "h1_autocorrelation_positive_no_adjustment"
    assert decision.after_risk_pct == pytest.approx(1.0)
    assert decision.autocorrelation > 0


def test_orchestrator_autocorrelation_risk_hook_attaches_record():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "risk": {
            "autocorrelation_sizing": {
                "enabled": True,
                "apply_to_execution": True,
                "window": 20,
                "min_autocorrelation": 0.0,
                "decay_risk_multiplier": 0.5,
            }
        }
    }
    record = {"decision_pipeline": {}, "instrumentation": {}}

    decision = orch._apply_autocorrelation_risk_sizing(
        current_risk_pct=2.0,
        raw_data=_raw_from_returns([0.01, -0.01] * 11),
        record=record,
    )

    assert decision.applied is True
    assert decision.after_risk_pct == pytest.approx(1.0)
    attached = record["decision_pipeline"]["autocorrelation_risk_sizing"]
    assert attached["reason"] == "h1_autocorrelation_decay_risk_reduction"
    assert record["instrumentation"]["autocorrelation_risk_applied"] is True
    assert record["instrumentation"]["autocorrelation_risk_multiplier"] == pytest.approx(0.5)


def test_attach_autocorrelation_risk_to_record_is_noop_for_missing_record():
    decision = evaluate_autocorrelation_risk(
        current_risk_pct=1.0,
        raw_data={},
        config={"risk": {"autocorrelation_sizing": {"enabled": True}}},
    )

    attach_autocorrelation_risk_to_record(None, decision)


def test_agent_config_wires_autocorrelation_risk_sizing_active():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    block = cfg["risk"]["autocorrelation_sizing"]

    assert block["enabled"] is True
    assert block["apply_to_execution"] is True
    assert block["window"] == 20
    assert block["min_autocorrelation"] == 0.0
    assert block["decay_risk_multiplier"] == 0.5
