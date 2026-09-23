from __future__ import annotations

import yaml

from src.research.moonshot_v3_runtime_packages import (
    apply_execution_policy_v3_default_off,
    apply_scheduler_v3_default_off,
    build_selector_v3_packet,
    build_v3_runtime_packet,
    load_v3_runtime_package_set,
)


def _complete_money_risk_state(**overrides):
    state = {
        "account_balance": 100000.0,
        "account_equity": 100000.0,
        "day_start_baseline": 100000.0,
        "realized_broker_or_proxy_pnl": 0.0,
        "open_worst_case_sl_risk_pct": 1.0,
        "pending_worst_case_sl_risk_pct": 0.5,
        "new_trade_worst_case_risk_pct": 0.5,
        "approved_trade_risk_pct": 0.5,
        "selected_cell_risk_pct": 0.5,
        "actual_sl_distance_status": "verified",
        "lot_contract_geometry_status": "verified",
        "spread_slippage_commission_swap_buffer_pct": 0.1,
        "daily_overlay_limit_pct": 4.0,
        "external_daily_loss_limit_pct": 5.0,
        "external_total_loss_limit_pct": 10.0,
        "realized_cushion_pct": 5.0,
        "drawdown_compression_state": "normal",
        "portfolio_ceiling_pct": 4.0,
        "correlation_cluster_ceiling_pct": 2.0,
        "same_symbol_risk_pct_before": 0.0,
        "correlated_cluster_risk_pct_before": 0.0,
    }
    state.update(overrides)
    return state


def test_agent_config_points_to_default_off_v3_packages():
    config = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    runtime = config["gtos_vnext_runtime"]

    assert runtime["selector_v3_enabled"] is False
    assert runtime["selector_v3_apply_to_execution"] is False
    assert runtime["selector_v3_default_off_package_path"].endswith("SELECTOR_V3_DEFAULT_OFF_PACKAGE.json")
    assert runtime["scheduler_v3_enabled"] is False
    assert runtime["scheduler_v3_apply_to_execution"] is False
    assert runtime["scheduler_v3_default_off_package_path"].endswith("SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json")
    assert runtime["execution_policy_v3_enabled"] is False
    assert runtime["execution_policy_v3_apply_to_execution"] is False
    assert runtime["execution_policy_v3_default_off_package_path"].endswith(
        "V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json"
    )


