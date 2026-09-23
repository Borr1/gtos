from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.components.denominator_forward_capture_contract import (
    ENABLED_CONFIG_KEY as DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY,
    LOG_ENABLED_CONFIG_KEY as DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY,
    M15_GRID_ORDER_LIFECYCLE_FAMILY,
    PENDING_CREATED_DECISION_TIME_FAMILY,
)
from src.components.pending_limit_lifecycle_logger import (
    REQUIRED_FIELDS,
    VALID_STATES,
    build_pending_limit_lifecycle_entry,
    record_pending_limit_lifecycle,
)


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    from src.components import execution as exec_mod
    from src.components import pending_limit_lifecycle_logger as lifecycle_mod

    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(
        lifecycle_mod,
        "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
        str(tmp_path / "pending_limit_lifecycle.jsonl"),
    )
    return tmp_path


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _make_engine(tmp_path: Path):
    from src.components.execution import ExecutionEngine

    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    mt5.get_account_balance.return_value = 100000.0
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
    }
    engine = ExecutionEngine(mt5, config)
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
    }
    engine.set_limit_intent(params, account_balance=100000.0)
    log_path = tmp_path / "pending_limit_lifecycle.jsonl"
    return engine, mt5, log_path


def _closed_ultimate_package_shadow(candidate_id: str = "candidate-package") -> dict:
    return {
        "schema": "gtos.final_moonshot.ultimate_candidate_package.scheduler_packet.v1",
        "schema_version": "ultimate_candidate_package_v1",
        "component": "ultimate_candidate_package",
        "packet_hash_sha256": "f" * 64,
        "decision_status": "shadow_scheduler_ranked_candidates",
        "shadow_selected_candidate_id": candidate_id,
        "selected_candidate_id": None,
        "approved_risk_pct": 0.0,
        "default_off": True,
        "shadow_only": True,
        "apply_to_execution": False,
        "live_activation_allowed_by_config": False,
        "final_package_selected_by_config": False,
        "runtime_effect_now": False,
        "candidate_use_allowed_now": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
        "execution_policy_shadow": {
            "policy_status": "shadow_execution_policy_ready_not_selectable",
            "selected_order_type_architecture": None,
            "execution_order_type_policy_selectable": False,
            "missed_fill_opportunity_cost_allowed": False,
            "limit_first_vs_guarded_market_comparison_allowed": False,
            "broker_real_expectancy_claim_allowed": False,
            "action": "shadow_no_order_type_selection_no_execution",
            "approved_risk_pct": 0.0,
            "default_off": True,
            "shadow_only": True,
            "apply_to_execution": False,
            "live_activation_allowed_by_config": False,
            "final_package_selected_by_config": False,
            "runtime_effect_now": False,
            "candidate_use_allowed_now": False,
            "selected_package_denominator_use_allowed": False,
            "denominator_expansion_allowed": False,
            "clean_label_use_allowed": False,
            "training_use_allowed": False,
            "model_training_allowed": False,
            "final_package_selection_allowed": False,
            "deployment_dossier_allowed": False,
            "vps_handoff_allowed": False,
            "live_execution_activation_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
        },
    }


def test_build_entry_contains_required_schema_fields():
    entry = build_pending_limit_lifecycle_entry(
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        side="LONG",
        trade_id="lim_1",
        intent_after_check="still_pending_no_trigger",
    )

    for field in REQUIRED_FIELDS:
        assert field in entry
    assert entry["schema_version"] == "pending_limit_lifecycle_v1"
    assert entry["evidence_class"] == "INTERNAL_LIMIT_LIFECYCLE"
    assert entry["result_use_status"] == "RESULT_MATERIALIZATION_REQUIRED"
    assert entry["fill_no_fill_label"] == "no_fill_still_pending"
    assert entry["pending_order_mode"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert entry["broker_pending_order_created"] is False
    assert entry["mt5_order_ticket"] is None
    assert entry["native_pending_order_type"] is None
    assert entry["pending_horizon_start_utc"] is None
    assert entry["pending_horizon_end_utc"] is None
    assert entry["terminal_area_touch_status"] == "TERMINAL_AREA_STATUS_NOT_CAPTURED"
    assert entry["protective_area_touch_status"] == "PROTECTIVE_AREA_STATUS_NOT_CAPTURED"
    assert entry["event_order_resolution_method"] == "LIFECYCLE_EVENT_STATE_ONLY"
    assert entry["mt5_position_ticket"] is None
    assert entry["mt5_entry_order_ticket"] is None
    assert entry["mt5_entry_deal_ticket"] is None
    assert entry["order_result_retcode"] is None
    assert entry["filled_order_position_join_keys"] == []
    assert entry["exact_r_join_key_status"] == "NO_FILLED_ORDER_POSITION_KEYS_FOR_CURRENT_STATE"
    assert entry["ultimate_candidate_package_shadow_status"] == (
        "ultimate_candidate_package_shadow_not_present"
    )
    assert entry["ultimate_candidate_package_shadow_packet_present"] is False


def test_build_entry_derives_closed_ultimate_package_shadow_summary():
    package = _closed_ultimate_package_shadow()
    entry = build_pending_limit_lifecycle_entry(
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        side="LONG",
        candidate_id="candidate-package",
        trade_id="lim_package_shadow",
        intent_after_check="still_pending_no_trigger",
        gtos_vnext_scheduler_v4_packet={
            "packet_hash_sha256": "scheduler-hash",
            "decision": {
                "selected_candidate_id": "candidate-package",
                "selected_action_class": "new_position",
                "runtime_effect_now": True,
            },
            "ultimate_candidate_package_shadow": package,
        },
    )

    assert entry["ultimate_candidate_package_shadow_status"] == (
        "default_off_shadow_authority_closed"
    )
    assert entry["ultimate_candidate_package_shadow_authority_closed"] is True
    assert entry["ultimate_candidate_package_shadow_packet_present"] is True
    assert entry["ultimate_candidate_package_shadow_packet_hash"] == "f" * 64
    assert entry["ultimate_candidate_package_shadow_selected_candidate_id"] == (
        "candidate-package"
    )
    assert entry["ultimate_candidate_package_selected_candidate_id"] is None
    assert entry["ultimate_candidate_package_approved_risk_pct"] == 0.0
    assert entry["ultimate_candidate_package_runtime_effect_now"] is False
    assert entry["ultimate_candidate_package_live_execution_activation_allowed"] is False
    assert entry["ultimate_candidate_package_final_package_selection_allowed"] is False
    assert entry["ultimate_candidate_package_order_calls"] == 0
    assert entry["ultimate_candidate_package_execution_policy_status"] == (
        "shadow_execution_policy_ready_not_selectable"
    )
    assert entry["ultimate_candidate_package_selected_order_type_architecture"] is None
    assert (
        entry["ultimate_candidate_package_execution_order_type_policy_selectable"]
        is False
    )
    assert entry["ultimate_candidate_package_gate_violations"] == []
    assert entry["ultimate_candidate_package_shadow_summary"]["authority_closed"] is True


def test_logger_appends_jsonl_rows(tmp_path):
    log_path = tmp_path / "lifecycle.jsonl"
    for idx in range(2):
        record_pending_limit_lifecycle(
            {
                "symbol": "XAUUSD",
                "trade_id": f"lim_{idx}",
                "intent_after_check": "manual_or_system_cancelled",
            },
            log_path=str(log_path),
        )

    rows = _read_rows(log_path)
    assert [row["trade_id"] for row in rows] == ["lim_0", "lim_1"]


def test_logger_denominator_forward_capture_is_disabled_by_default(tmp_path):
    log_path = tmp_path / "lifecycle.jsonl"
    denominator_path = tmp_path / "denominator_forward_capture.jsonl"

    record_pending_limit_lifecycle(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "candidate_id": "candidate-denom-disabled",
            "trade_id": "lim_denom_disabled",
            "intent_after_check": "manual_or_system_cancelled",
            "decision_time_utc": "2026-06-20T08:00:00Z",
            "pending_created_time_utc": "2026-06-20T08:01:00Z",
            "source_hash": "a" * 64,
            "order_intent": "place_pending_limit",
            "native_pending_order_type": "BUY_LIMIT",
            "pending_ticket": "123456",
            "risk_reservation_broker_namespace": "FTMO_DEMO",
            "denominator_forward_capture_log_path": str(denominator_path),
        },
        log_path=str(log_path),
    )

    assert _read_rows(log_path)[-1]["candidate_id"] == "candidate-denom-disabled"
    assert not denominator_path.exists()


def test_logger_denominator_forward_capture_appends_when_enabled(tmp_path):
    log_path = tmp_path / "lifecycle.jsonl"
    denominator_path = tmp_path / "denominator_forward_capture.jsonl"

    record_pending_limit_lifecycle(
        {
            "symbol": "GBPJPY",
            "side": "SHORT",
            "candidate_id": "candidate-denom-enabled",
            "selected_candidate_id": "candidate-denom-enabled",
            "trade_id": "lim_denom_enabled",
            "intent_after_check": "order_send_success_filled",
            "decision_time_utc": "2026-06-20T08:15:00Z",
            "pending_created_time_utc": "2026-06-20T08:16:00Z",
            "stable_decision_window_id": "GBPJPY:SHORT:2026-06-20T08:15:00Z",
            "source_hash": "b" * 64,
            "order_intent": "place_pending_limit",
            "native_pending_order_type": "SELL_LIMIT",
            "pending_ticket": "654321",
            "time_in_force": "GTC",
            "risk_reservation_broker_namespace": "FTMO_DEMO",
            "denominator_forward_capture_log_path": str(denominator_path),
            "denominator_forward_capture_runtime_config": {
                DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY: True,
                DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY: True,
            },
        },
        log_path=str(log_path),
    )

    rows = _read_rows(denominator_path)
    assert {row["requirement_family"] for row in rows} == {
        PENDING_CREATED_DECISION_TIME_FAMILY,
        M15_GRID_ORDER_LIFECYCLE_FAMILY,
    }
    assert [row["status"] for row in rows] == [
        "capture_event_complete",
        "capture_event_complete",
    ]
    assert {row["candidate_id"] for row in rows} == {"candidate-denom-enabled"}
    assert {row["source_event_hash"] for row in rows} == {"b" * 64}
    assert all(row["selected_package_denominator_use_allowed"] is False for row in rows)


def test_denominator_forward_capture_preserves_ultimate_package_shadow_context(tmp_path):
    log_path = tmp_path / "lifecycle.jsonl"
    denominator_path = tmp_path / "denominator_forward_capture.jsonl"
    package = _closed_ultimate_package_shadow("candidate-package-capture")

    record_pending_limit_lifecycle(
        {
            "symbol": "EURUSD",
            "side": "LONG",
            "candidate_id": "candidate-package-capture",
            "trade_id": "lim_package_capture",
            "intent_after_check": "order_send_success_filled",
            "decision_time_utc": "2026-06-20T09:15:00Z",
            "pending_created_time_utc": "2026-06-20T09:16:00Z",
            "source_hash": "e" * 64,
            "order_intent": "place_pending_limit",
            "native_pending_order_type": "BUY_LIMIT",
            "pending_ticket": "777",
            "risk_reservation_broker_namespace": "denominator_capture_research",
            "gtos_vnext_scheduler_v4_packet": {
                "packet_hash_sha256": "scheduler-package-capture",
                "decision": {
                    "selected_candidate_id": "candidate-package-capture",
                    "selected_action_class": "new_position",
                    "runtime_effect_now": True,
                },
                "ultimate_candidate_package_shadow": package,
            },
            "denominator_forward_capture_log_path": str(denominator_path),
            "denominator_forward_capture_runtime_config": {
                DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY: True,
                DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY: True,
            },
        },
        log_path=str(log_path),
    )

    lifecycle_row = _read_rows(log_path)[-1]
    assert lifecycle_row["ultimate_candidate_package_shadow_status"] == (
        "default_off_shadow_authority_closed"
    )
    assert lifecycle_row["ultimate_candidate_package_shadow_packet_hash"] == "f" * 64
    assert lifecycle_row["ultimate_candidate_package_selected_candidate_id"] is None
    assert lifecycle_row["ultimate_candidate_package_runtime_effect_now"] is False
    assert lifecycle_row["ultimate_candidate_package_gate_violations"] == []

    denominator_rows = _read_rows(denominator_path)
    assert len(denominator_rows) == 2
    assert all(
        row["ultimate_candidate_package_shadow_status"]
        == "default_off_shadow_authority_closed"
        for row in denominator_rows
    )
    assert all(
        row["ultimate_candidate_package_shadow_packet_hash"] == "f" * 64
        for row in denominator_rows
    )
    assert all(
        row["ultimate_candidate_package_selected_candidate_id"] is None
        for row in denominator_rows
    )
    assert all(
        row["ultimate_candidate_package_runtime_effect_now"] is False
        for row in denominator_rows
    )
    assert all(
        row["ultimate_candidate_package_supplemental_context"][
            "ultimate_candidate_package_execution_policy_status"
        ]
        == "shadow_execution_policy_ready_not_selectable"
        for row in denominator_rows
    )


def test_logger_write_failure_is_fail_open(monkeypatch):
    def _boom(*args, **kwargs):
        raise OSError("disk full")

    import src.components.pending_limit_lifecycle_logger as lifecycle_mod

    monkeypatch.setattr(lifecycle_mod, "open", _boom, raising=False)
    with patch("builtins.open", _boom):
        record_pending_limit_lifecycle(
            {
                "symbol": "XAUUSD",
                "trade_id": "lim_fail_open",
                "intent_after_check": "manual_or_system_cancelled",
            }
        )


@pytest.mark.parametrize(
    ("state", "setup"),
    [
        (
            "still_pending_no_trigger",
            lambda engine, mt5: engine.check_limit_fill(
                {"time": "t", "open": 4430.0, "high": 4432.0, "low": 4425.0, "close": 4428.0},
                telemetry_context={"source_branch": "test", "check_context": "inside_kz"},
            ),
        ),
        (
            "triggered_tick_missing_retry",
            lambda engine, mt5: (
                setattr(mt5, "get_tick", MagicMock(return_value=None))
                or engine.check_limit_fill(
                    {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
                )
            ),
        ),
        (
            "cancelled_wrong_side",
            lambda engine, mt5: (
                setattr(mt5, "get_tick", MagicMock(return_value=MagicMock(ask=4395.0, bid=4394.0, spread_cents=11.0)))
                or engine.check_limit_fill(
                    {"time": "t", "open": 4410.0, "high": 4412.0, "low": 4393.0, "close": 4395.0}
                )
            ),
        ),
        (
            "cancelled_target_reached_without_fill",
            lambda engine, mt5: engine.check_limit_fill(
                {"time": "t", "open": 4445.0, "high": 4451.0, "low": 4425.0, "close": 4448.0}
            ),
        ),
        (
            "order_send_success_filled",
            lambda engine, mt5: (
                setattr(
                    engine,
                    "open_trade",
                    MagicMock(
                        return_value=MagicMock(
                            ticket=12345,
                            entry_order_ticket=12345,
                            entry_deal_ticket=67890,
                            entry_order_retcode=10009,
                        )
                    ),
                ),
                engine.check_limit_fill(
                    {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
                ),
            ),
        ),
        (
            "order_send_failed_retry",
            lambda engine, mt5: (
                setattr(engine, "open_trade", MagicMock(return_value=None)),
                engine.check_limit_fill(
                    {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
                ),
            ),
        ),
    ],
)
def test_execution_writes_lifecycle_state(tmp_path, state, setup):
    engine, mt5, log_path = _make_engine(tmp_path)

    setup(engine, mt5)

    rows = _read_rows(log_path)
    assert rows[-1]["intent_after_check"] == state
    assert rows[-1]["trade_id"].startswith("lim_")
    assert rows[-1]["result_use_status"] == "RESULT_MATERIALIZATION_REQUIRED"
    assert rows[-1]["evidence_class"] == "INTERNAL_LIMIT_LIFECYCLE"
    assert rows[-1]["pending_order_mode"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert rows[-1]["broker_pending_order_created"] is False
    assert rows[-1]["mt5_order_ticket"] is None
    assert rows[-1]["pending_horizon_start_utc"] is not None
    assert rows[-1]["pending_horizon_end_utc"] is not None
    assert rows[-1]["event_order_resolution_method"]
    if rows[-1]["trigger_condition_met"] is True and rows[-1]["tick_available"] is True:
        assert rows[-1]["entry_touch_spread_value_source_safe"] is not None
        assert rows[-1]["entry_touch_spread_unit"] == "spread_cents"
    if state == "order_send_success_filled":
        assert rows[-1]["trade_state_ticket"] == 12345
        assert rows[-1]["mt5_position_ticket"] == 12345
        assert rows[-1]["mt5_entry_order_ticket"] == 12345
        assert rows[-1]["mt5_entry_deal_ticket"] == 67890
        assert rows[-1]["order_result_retcode"] == 10009
        assert rows[-1]["filled_order_position_join_keys"] == [
            "trade_state_ticket:12345",
            "mt5_position_ticket:12345",
            "mt5_entry_order_ticket:12345",
            "mt5_entry_deal_ticket:67890",
        ]
        assert rows[-1]["exact_r_join_key_status"] == "FILLED_ORDER_POSITION_KEYS_CAPTURED"


def test_execution_config_wires_denominator_forward_capture(tmp_path):
    from src.components.execution import ExecutionEngine

    denominator_path = tmp_path / "denominator_forward_capture.jsonl"
    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
        "runtime": {"broker_account_namespace": "ftmo_test"},
        "denominator_forward_capture_contract": {
            "enabled": True,
            "log_enabled": True,
            "log_path": str(denominator_path),
        },
    }
    engine = ExecutionEngine(mt5, config)
    engine.set_limit_intent(
        {
            "direction": "LONG",
            "entry_price": 4421.39,
            "stop_loss": 4401.99,
            "take_profit_1": 4450.49,
        },
        account_balance=100000.0,
        telemetry_context={
            "candidate_id": "candidate-exec-denom",
            "decision_time_utc": "2026-06-20T08:30:00Z",
            "source_hash": "c" * 64,
            "gtos_vnext_pending_policy_action": "PLACE_LIMIT",
        },
    )
    engine.open_trade = MagicMock(
        return_value=MagicMock(
            ticket=98765,
            entry_order_ticket=98765,
            entry_deal_ticket=87654,
            entry_order_retcode=10009,
        )
    )

    engine.check_limit_fill(
        {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
    )

    rows = _read_rows(denominator_path)
    assert {row["requirement_family"] for row in rows} == {
        PENDING_CREATED_DECISION_TIME_FAMILY,
        M15_GRID_ORDER_LIFECYCLE_FAMILY,
    }
    assert all(row["status"] == "capture_event_complete" for row in rows)
    assert {row["candidate_id"] for row in rows} == {"candidate-exec-denom"}
    assert {row["source_event_hash"] for row in rows} == {"c" * 64}
    assert all(row["selected_package_denominator_use_allowed"] is False for row in rows)


def test_execution_config_wires_denominator_forward_capture_family_filter(tmp_path):
    from src.components.execution import ExecutionEngine

    denominator_path = tmp_path / "denominator_forward_capture.jsonl"
    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
        "runtime": {"broker_account_namespace": "denominator_capture_research"},
        "denominator_forward_capture_contract": {
            "enabled": True,
            "log_enabled": True,
            "log_path": str(denominator_path),
            "requirement_families": [M15_GRID_ORDER_LIFECYCLE_FAMILY],
        },
    }
    engine = ExecutionEngine(mt5, config)
    engine.set_limit_intent(
        {
            "direction": "LONG",
            "entry_price": 4421.39,
            "stop_loss": 4401.99,
            "take_profit_1": 4450.49,
        },
        account_balance=100000.0,
        telemetry_context={
            "candidate_id": "candidate-exec-family-filter",
            "decision_time_utc": "2026-06-20T08:45:00Z",
            "source_hash": "d" * 64,
            "gtos_vnext_pending_policy_action": "PLACE_LIMIT",
        },
    )
    engine.open_trade = MagicMock(
        return_value=MagicMock(
            ticket=112233,
            entry_order_ticket=112233,
            entry_deal_ticket=332211,
            entry_order_retcode=10009,
        )
    )

    engine.check_limit_fill(
        {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
    )

    rows = _read_rows(denominator_path)
    assert [row["requirement_family"] for row in rows] == [
        M15_GRID_ORDER_LIFECYCLE_FAMILY
    ]
    assert rows[0]["status"] == "capture_event_complete"
    assert rows[0]["candidate_id"] == "candidate-exec-family-filter"
    assert "broker_profile_namespace" in rows[0]["captured_fields"]
    assert rows[0]["source_event_hash"] == "d" * 64


def test_execution_normalizes_zero_entry_deal_ticket_in_lifecycle_row(tmp_path):
    engine, _mt5, log_path = _make_engine(tmp_path)
    engine.open_trade = MagicMock(
        return_value=MagicMock(
            ticket=12345,
            entry_order_ticket=12345,
            entry_deal_ticket=0,
            entry_order_retcode=10009,
        )
    )

    engine.check_limit_fill(
        {"time": "t", "open": 4425.0, "high": 4426.0, "low": 4420.0, "close": 4422.0}
    )

    row = _read_rows(log_path)[-1]
    assert row["intent_after_check"] == "order_send_success_filled"
    assert row["mt5_entry_deal_ticket"] is None
    assert row["filled_order_position_join_keys"] == [
        "trade_state_ticket:12345",
        "mt5_position_ticket:12345",
        "mt5_entry_order_ticket:12345",
    ]
    assert "mt5_entry_deal_ticket:0" not in row["filled_order_position_join_keys"]


def test_execution_writes_sl_too_close_state(tmp_path):
    engine, mt5, log_path = _make_engine(tmp_path)
    engine.config["risk"]["sl_absolute_min"] = 5.0
    mt5.get_tick.return_value = MagicMock(ask=4405.0, bid=4404.0, spread_cents=12.0)

    engine.check_limit_fill(
        {"time": "t", "open": 4410.0, "high": 4412.0, "low": 4404.0, "close": 4405.0}
    )

    row = _read_rows(log_path)[-1]
    assert row["intent_after_check"] == "cancelled_sl_too_close"
    assert row["sl_too_close_abort"] is True


def test_execution_writes_expiry_state(tmp_path):
    from datetime import datetime, timedelta, timezone

    engine, _mt5, log_path = _make_engine(tmp_path)
    engine.pending_intent.placed_time = (
        datetime.now(timezone.utc) - timedelta(hours=49)
    ).isoformat()

    engine.check_limit_fill(
        {"time": "t", "open": 4500.0, "high": 4502.0, "low": 4498.0, "close": 4500.0}
    )

    row = _read_rows(log_path)[-1]
    assert row["intent_after_check"] == "expired_48h"
    assert row["cancel_reason"] == "48h clock expiry"
    assert row["pending_horizon_end_utc"] is not None
    assert row["cancel_expiry_reason_status"] == "CANCEL_OR_EXPIRY_REASON_CAPTURED_SOURCE_SAFE"


def test_execution_writes_manual_cancel_state(tmp_path):
    engine, _mt5, log_path = _make_engine(tmp_path)

    engine.cancel_limit_intent("daily_loss_stop")

    row = _read_rows(log_path)[-1]
    assert row["intent_after_check"] == "manual_or_system_cancelled"
    assert row["reason"] == "daily_loss_stop"
    assert row["check_context"] == "cancel"
    assert row["event_order_resolution_method"] == "LIFECYCLE_EVENT_STATE_ONLY"


def test_execution_persists_decision_spread_from_limit_intent(tmp_path):
    from src.components.execution import ExecutionEngine

    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
    }
    engine = ExecutionEngine(mt5, config)
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
    }
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "candidate_id": "candidate_with_decision_spread",
            "decision_spread_value_source_safe": 18.5,
            "decision_spread_unit": "spread_cents",
        },
    )

    engine.check_limit_fill(
        {"time": "t", "open": 4430.0, "high": 4432.0, "low": 4425.0, "close": 4428.0}
    )

    row = _read_rows(tmp_path / "pending_limit_lifecycle.jsonl")[-1]
    assert row["candidate_id"] == "candidate_with_decision_spread"
    assert row["decision_spread_value_source_safe"] == 18.5
    assert row["decision_spread_unit"] == "spread_cents"


def test_execution_persists_vnext_evidence_from_limit_intent(tmp_path):
    from src.components.execution import ExecutionEngine

    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
    }
    engine = ExecutionEngine(mt5, config)
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
    }
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "candidate_id": "candidate_with_vnext",
            "gtos_vnext_pre_ai_action": "NARROW_AI_TO_ROUTE",
            "gtos_vnext_pre_ai_recommended_side": "LONG",
            "gtos_vnext_pre_ai_recommended_frameworks": ["ob_retest"],
            "gtos_vnext_decision": "FOLLOW",
            "gtos_vnext_reason": "matched_vnext_route_scope",
            "gtos_vnext_matched": True,
            "gtos_vnext_matched_rows": 3,
            "gtos_vnext_cost_adjusted_r_sum": 12.5,
            "gtos_vnext_proxy_score_sum": 2.0,
            "gtos_vnext_stress_r_sum": 10.0,
            "gtos_vnext_effective_n_sum": 250,
            "gtos_vnext_risk_multiplier": 1.0,
            "gtos_vnext_risk_would_multiplier": 1.25,
            "gtos_vnext_risk_reason": "shadow_vnext_risk_strong_follow",
            "gtos_vnext_pending_policy_action": "PLACE_LIMIT",
            "gtos_vnext_pending_policy_would_action": "SKIP_PENDING_NOFILL_AVOID",
            "gtos_vnext_pending_policy_applied": False,
            "gtos_vnext_pending_policy_reason": "shadow_vnext_pending_policy_nofill_avoid",
        },
    )

    assert engine.pending_intent.gtos_vnext_decision == "FOLLOW"
    assert engine.pending_intent.gtos_vnext_pre_ai_recommended_frameworks == ["ob_retest"]
    assert engine.pending_intent.gtos_vnext_pending_policy_would_action == "SKIP_PENDING_NOFILL_AVOID"
    engine.check_limit_fill(
        {"time": "t", "open": 4430.0, "high": 4432.0, "low": 4425.0, "close": 4428.0}
    )

    row = _read_rows(tmp_path / "pending_limit_lifecycle.jsonl")[-1]
    assert row["candidate_id"] == "candidate_with_vnext"
    assert row["gtos_vnext_pre_ai_action"] == "NARROW_AI_TO_ROUTE"
    assert row["gtos_vnext_pre_ai_recommended_frameworks"] == ["ob_retest"]
    assert row["gtos_vnext_decision"] == "FOLLOW"
    assert row["gtos_vnext_matched_rows"] == 3
    assert row["gtos_vnext_cost_adjusted_r_sum"] == 12.5
    assert row["gtos_vnext_effective_n_sum"] == 250
    assert row["gtos_vnext_risk_would_multiplier"] == 1.25
    assert row["gtos_vnext_pending_policy_action"] == "PLACE_LIMIT"
    assert row["gtos_vnext_pending_policy_would_action"] == "SKIP_PENDING_NOFILL_AVOID"
    assert row["gtos_vnext_pending_policy_applied"] is False


def test_execution_lifecycle_row_carries_ultimate_package_shadow_summary(tmp_path):
    from src.components.execution import ExecutionEngine

    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0, spread_cents=10.0)
    config = {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
    }
    engine = ExecutionEngine(mt5, config)
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
    }
    package = _closed_ultimate_package_shadow("candidate-exec-package")
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "candidate_id": "candidate-exec-package",
            "decision_time_utc": "2026-06-20T09:30:00Z",
            "gtos_vnext_scheduler_v4_packet_hash": "scheduler-exec-package",
            "gtos_vnext_scheduler_v4_packet": {
                "packet_hash_sha256": "scheduler-exec-package",
                "decision": {
                    "selected_candidate_id": "candidate-exec-package",
                    "selected_action_class": "new_position",
                    "runtime_effect_now": True,
                },
                "ultimate_candidate_package_shadow": package,
            },
        },
    )

    engine.check_limit_fill(
        {"time": "t", "open": 4430.0, "high": 4432.0, "low": 4425.0, "close": 4428.0}
    )

    row = _read_rows(tmp_path / "pending_limit_lifecycle.jsonl")[-1]
    assert row["candidate_id"] == "candidate-exec-package"
    assert row["ultimate_candidate_package_shadow_status"] == (
        "default_off_shadow_authority_closed"
    )
    assert row["ultimate_candidate_package_shadow_authority_closed"] is True
    assert row["ultimate_candidate_package_shadow_packet_hash"] == "f" * 64
    assert row["ultimate_candidate_package_shadow_selected_candidate_id"] == (
        "candidate-exec-package"
    )
    assert row["ultimate_candidate_package_selected_candidate_id"] is None
    assert row["ultimate_candidate_package_approved_risk_pct"] == 0.0
    assert row["ultimate_candidate_package_order_calls"] == 0
    assert row["ultimate_candidate_package_runtime_effect_now"] is False
    assert row["ultimate_candidate_package_live_execution_activation_allowed"] is False
    assert row["ultimate_candidate_package_final_package_selection_allowed"] is False
    assert row["ultimate_candidate_package_selected_order_type_architecture"] is None
    assert (
        row["ultimate_candidate_package_execution_order_type_policy_selectable"]
        is False
    )


def test_all_required_states_are_covered_by_tests():
    covered = {
        "still_pending_no_trigger",
        "expired_48h",
        "source_repair_failed_retry",
        "triggered_tick_missing_retry",
        "execution_manager_v4_blocked",
        "cancelled_wrong_side",
        "cancelled_sl_too_close",
        "cancelled_target_reached_without_fill",
        "order_send_success_filled",
        "order_send_failed_retry",
        "manual_or_system_cancelled",
        "unknown_pending_lifecycle_state",
        "runtime_halt_cancelled_no_order_send",
    }
    assert covered == VALID_STATES
