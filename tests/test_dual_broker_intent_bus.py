from __future__ import annotations

import json
from pathlib import Path

from src.components.dual_broker_intent_bus import (
    MARKET_ENTRY,
    PENDING_LIMIT,
    append_intent,
    build_intent_from_trade_record,
    build_intent_from_execution_inputs,
    canonical_intent_id,
    intent_to_trade_params,
    read_intents_from_offset,
    sanitize_primary_order_for_target_contract,
    source_target_boundary_violations,
)


def _intent(intent_type: str = MARKET_ENTRY) -> dict:
    return build_intent_from_execution_inputs(
        intent_type=intent_type,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        source_symbol="XAUUSD",
        source_mt5_symbol="XAUUSD",
        trade_params={
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "take_profit_2": 2380.0,
            "risk_reward_ratio": 2.0,
            "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
            "gtos_vnext_execution_policy_id": "policy-1",
        },
        source_trade_id="tr_primary_1",
        candidate_id="cand-1",
        effective_risk_pct=1.0,
        kill_zone="ny",
        trigger="unit_test",
    )


def test_canonical_intent_id_is_stable_for_identity_fields():
    first = _intent()
    second = _intent()
    second["recorded_at_utc"] = "2099-01-01T00:00:00+00:00"

    assert canonical_intent_id(first) == canonical_intent_id(second)
    assert first["intent_id"] == second["intent_id"]


def test_canonical_intent_id_ignores_lifecycle_sltp_rewrites():
    first = _intent()
    second = _intent()
    second["trade"]["stop_loss"] = first["trade"]["entry_price"]
    second["trade"]["take_profit_1"] = 2399.0
    second["trade"]["take_profit_2"] = 2405.0

    assert canonical_intent_id(first) == canonical_intent_id(second)


def test_append_intent_dedupes_and_reads_from_offset(tmp_path: Path):
    path = tmp_path / "intents.jsonl"
    intent = _intent(PENDING_LIMIT)

    first = append_intent(intent, path)
    duplicate = append_intent(intent, path)
    rows, offset = read_intents_from_offset(path, 0)
    later_rows, later_offset = read_intents_from_offset(path, offset)

    assert first["status"] == "appended"
    assert duplicate["status"] == "duplicate"
    assert len(rows) == 1
    assert rows[0]["intent_type"] == PENDING_LIMIT
    assert later_rows == []
    assert later_offset == offset


def test_append_intent_dedupes_legacy_stored_id_by_current_identity(tmp_path: Path):
    path = tmp_path / "intents.jsonl"
    intent = _intent()
    legacy_row = dict(intent)
    legacy_row["intent_id"] = "legacy-id-before-context-repair"
    path.write_text(json.dumps(legacy_row, sort_keys=True) + "\n", encoding="utf-8")

    duplicate = append_intent(intent, path)
    rows, _ = read_intents_from_offset(path, 0)

    assert duplicate["status"] == "duplicate"
    assert len(rows) == 1
    assert rows[0]["intent_id"] == "legacy-id-before-context-repair"


def test_append_intent_dedupes_pending_limit_source_fill_lifecycle(tmp_path: Path):
    path = tmp_path / "intents.jsonl"
    pending = _intent(PENDING_LIMIT)
    pending["source"]["trade_id"] = "lim_XAUUSD_2026-06-02_080000"
    pending["intent_id"] = canonical_intent_id(pending)
    filled = _intent(MARKET_ENTRY)
    filled["source"]["trade_id"] = "lim_filled_XAUUSD_2026-06-02_080000"
    filled["intent_id"] = canonical_intent_id(filled)

    assert pending["intent_id"] != filled["intent_id"]

    first = append_intent(pending, path)
    duplicate = append_intent(filled, path)
    rows, _ = read_intents_from_offset(path, 0)

    assert first["status"] == "appended"
    assert duplicate["status"] == "duplicate"
    assert len(rows) == 1
    assert rows[0]["intent_type"] == PENDING_LIMIT


def test_intent_to_trade_params_preserves_vnext_dynamic_context():
    params = intent_to_trade_params(_intent())

    assert params["direction"] == "LONG"
    assert params["entry_price"] == 2350.0
    assert params["stop_loss"] == 2340.0
    assert params["take_profit_1"] == 2370.0
    assert params["gtos_vnext_dynamic_policy_selected"] == "momentum_exhaustion"
    assert params["gtos_vnext_execution_policy_id"] == "policy-1"


def test_primary_order_sanitizer_keeps_only_source_record_reference():
    primary_order = {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "ticket": 12345,
        "entry_order_ticket": 12345,
        "entry_deal_ticket": 12346,
        "entry_price": 2350.25,
        "initial_volume": 0.42,
        "commission": -3.2,
        "swap": -1.1,
        "contract_size": 100.0,
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
    }

    sanitized = sanitize_primary_order_for_target_contract(primary_order)

    assert sanitized == {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "source_reference_policy": "source_path_reference_only_no_target_broker_truth",
    }


def test_build_intent_strips_primary_broker_truth_from_primary_order():
    intent = build_intent_from_execution_inputs(
        intent_type=MARKET_ENTRY,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        source_symbol="XAUUSD",
        source_mt5_symbol="XAUUSD",
        trade_params={
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
        },
        source_trade_id="tr_primary_no_copy",
        primary_order={
            "ticket": 234432798,
            "entry_order_ticket": 234432798,
            "entry_deal_ticket": 234432799,
            "entry_price": 2350.11,
            "initial_volume": 0.50,
            "commission": -4.0,
            "swap": -2.0,
        },
    )

    assert intent["primary_order"] == {}
    assert source_target_boundary_violations(intent) == []


def test_append_intent_sanitizes_unsanitized_external_primary_order(tmp_path: Path):
    path = tmp_path / "intents.jsonl"
    intent = _intent()
    intent["primary_order"] = {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "entry_order_ticket": 1001,
        "entry_deal_ticket": 1002,
        "initial_volume": 0.25,
        "entry_price": 2350.25,
    }

    result = append_intent(intent, path)
    rows, _ = read_intents_from_offset(path, 0)

    assert result["status"] == "appended"
    assert rows[0]["primary_order"] == {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "source_reference_policy": "source_path_reference_only_no_target_broker_truth",
    }
    assert source_target_boundary_violations(rows[0]) == []


def test_source_target_boundary_detector_rejects_forbidden_primary_order_fields():
    intent = _intent()
    intent["primary_order"] = {"record_path": "source.json", "ticket": 123, "initial_volume": 0.3}

    assert source_target_boundary_violations(intent) == [
        "primary_order_forbidden_source_field:initial_volume",
        "primary_order_forbidden_source_field:ticket",
    ]


def test_build_intent_from_current_trade_record_execution_schema(tmp_path: Path):
    record = {
        "metadata": {
            "trade_id": "XAUUSD_primary_record",
            "symbol": "XAUUSD",
            "candidate_id": "broadorigin_1",
            "kill_zone": "london",
        },
        "execution": {
            "trade_id": "lim_filled_XAUUSD_1",
            "broker_fill_state": "filled",
            "fill_time_utc": "2026-06-02T08:00:00+00:00",
            "entry_order_ticket": 12345,
            "entry_deal_ticket": 12346,
            "position_ticket": 12345,
            "direction": "SHORT",
            "entry_price": 2350.0,
            "requested_limit_price": 2351.0,
            "stop_loss": 2360.0,
            "take_profit_1": 2330.0,
            "risk_pct": 0.5,
            "broker_symbol": "XAUUSD",
        },
        "decision_pipeline": {
            "gtos_vnext_moonshot_dynamic_execution": {
                "selected_policy": "partial_be_runner",
                "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                "applied": True,
                "replaced_policy": "retired_static_baseline_comparator",
                "candidate_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                "decision_status": "vnext_candidate_ready",
                "source_quality_action": "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
                "exit_management_action": "ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER",
                "prop_action": "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
                "fixed_target_role": "partial_runner",
                "source_event": {
                    "selected_cell_risk_allowed": True,
                    "selected_cell_risk_pct": 0.5,
                    "selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-UNIT",
                    "selected_cell_risk_decision_basis": "unit selected-cell proof",
                    "selected_cell_risk_unresolved_reasons": [
                        "condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry"
                    ],
                    "selected_cell_risk_execution_critical_unresolved_reasons": [],
                    "selected_cell_risk_selected_policy": "partial_be_runner",
                    "selected_cell_risk_source_policy": "be_after_trigger",
                    "selected_cell_risk_policy_identity_status": "policy_invariant_broker_geometry_for_selected_execution_policy",
                },
            },
            "gtos_vnext_candidate_intelligence_packet": {
                "dynamic_policy": {
                    "dynamic_trigger_final_pullback": {
                        "selected_policy": "partial_be_runner",
                        "partial_trigger_r": 1.0,
                        "partial_final_target_r": 3.0,
                        "partial_close_ratio": 0.5,
                        "repaired_dynamic_final_target_r": 3.0,
                    }
                }
            },
        },
    }

    intent = build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    )

    assert intent is not None
    assert intent["intent_type"] == MARKET_ENTRY
    assert intent["source"]["symbol"] == "XAUUSD"
    assert intent["source"]["trade_id"] == "lim_filled_XAUUSD_1"
    assert intent["trade"]["direction"] == "SHORT"
    assert intent["dynamic_context"]["gtos_vnext_production_execution_path"] is True
    assert intent["dynamic_context"]["gtos_vnext_dynamic_policy_applied"] is True
    assert intent["dynamic_context"]["gtos_vnext_dynamic_be_trigger_r"] == 1.0
    assert intent["dynamic_context"]["gtos_vnext_dynamic_final_target_r"] == 3.0
    assert intent["dynamic_context"]["gtos_vnext_dynamic_partial_close_ratio"] == 0.5
    assert intent["dynamic_context"]["gtos_vnext_selected_cell_risk_selected_policy"] == "partial_be_runner"
    assert intent["dynamic_context"]["gtos_vnext_selected_cell_risk_source_policy"] == "be_after_trigger"
    assert (
        intent["dynamic_context"]["gtos_vnext_selected_cell_risk_policy_identity_status"]
        == "policy_invariant_broker_geometry_for_selected_execution_policy"
    )
    assert (
        intent["dynamic_context"]["gtos_vnext_commission_model_status"]
        == "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
    )
    assert intent["primary_order"] == {
        "record_path": str(tmp_path / "record.json"),
        "source_reference_policy": "source_path_reference_only_no_target_broker_truth",
    }
    assert source_target_boundary_violations(intent) == []


def test_build_intent_from_trade_record_blocks_fatal_selected_cell_unresolved_reason(
    tmp_path: Path,
):
    record = {
        "metadata": {"trade_id": "XAUUSD_record", "symbol": "XAUUSD"},
        "execution": {
            "trade_id": "lim_filled_XAUUSD_blocked",
            "broker_fill_state": "filled",
            "fill_time_utc": "2026-06-02T08:00:00+00:00",
            "entry_order_ticket": 12345,
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "gtos_vnext_production_execution_path": True,
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-BLOCKED",
            "gtos_vnext_selected_cell_risk_selected_policy": "partial_be_runner",
            "gtos_vnext_selected_cell_risk_policy_identity_status": "policy_invariant_broker_geometry_for_selected_execution_policy",
            "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons": [
                "commission_model_unverified"
            ],
            "gtos_vnext_commission_model_status": "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP",
        },
    }

    assert build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    ) is None


def test_build_intent_from_trade_record_defers_incomplete_vnext_context(tmp_path: Path):
    record = {
        "metadata": {"trade_id": "XAUUSD_record", "symbol": "XAUUSD"},
        "execution": {
            "trade_id": "lim_filled_XAUUSD_incomplete",
            "broker_fill_state": "filled",
            "fill_time_utc": "2026-06-02T08:00:00+00:00",
            "entry_order_ticket": 12345,
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-EARLY",
            "gtos_vnext_selected_cell_risk_pct": 0.25,
        },
    }

    assert build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    ) is None


def test_build_intent_from_trade_record_skips_ambiguous_execution(tmp_path: Path):
    record = {
        "metadata": {"trade_id": "XAUUSD_record", "symbol": "XAUUSD"},
        "execution": {
            "trade_id": "lim_XAUUSD_ambiguous",
            "direction": "SHORT",
            "entry_price": 2350.0,
            "stop_loss": 2360.0,
            "take_profit_1": 2330.0,
        },
    }

    assert build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    ) is None


def test_build_intent_from_trade_record_skips_terminal_exit_update(tmp_path: Path):
    record = {
        "metadata": {"trade_id": "XAUUSD_record", "symbol": "XAUUSD"},
        "execution": {
            "trade_id": "lim_XAUUSD_closed",
            "broker_fill_state": "filled",
            "fill_time_utc": "2026-06-02T08:00:00+00:00",
            "entry_order_ticket": 12345,
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
        },
        "exit": {"exit_reason": "breakeven", "close_time_utc": "2026-06-02T08:05:00+00:00"},
    }

    assert build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    ) is None


def test_build_intent_from_trade_record_skips_terminal_pending_update(tmp_path: Path):
    record = {
        "metadata": {"trade_id": "XAUUSD_record", "symbol": "XAUUSD"},
        "limit_intent": {
            "trade_id": "lim_XAUUSD_cancelled",
            "direction": "LONG",
            "limit_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
            "terminal_state": "cleared_without_fill",
            "broker_fill_state": "not_filled",
        },
    }

    assert build_intent_from_trade_record(
        record,
        record_path=tmp_path / "record.json",
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
    ) is None
