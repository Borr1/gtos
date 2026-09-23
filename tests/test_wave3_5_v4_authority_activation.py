from __future__ import annotations

from types import SimpleNamespace

import yaml

from src.components.market_whiteboard_v2 import candidate_context_from_runtime


def _config() -> dict:
    with open("config/agent_config.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_wave3_5_market_whiteboard_derives_source_status_without_tick_duplication() -> None:
    trade_params = SimpleNamespace(
        trade_parameters=SimpleNamespace(
            direction="LONG",
            gtos_vnext_source_event_hash="event-sha",
            gtos_vnext_selector_row_id="selector-row",
            kill_zone="london",
        )
    )

    context = candidate_context_from_runtime(trade_params, None, "XAUUSD")
    source_status = context["source_status"]

    assert source_status["m1"]["source_state"] == "decision-available"
    assert source_status["session"]["source_state"] == "decision-available"
    assert source_status["volatility"]["source_state"] == "proxy"
    assert source_status["correlation"]["source_state"] == "proxy"
    assert "tick" not in source_status
    assert "spread" not in source_status
