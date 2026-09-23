"""Tests for Session Orchestrator (Phase 4)."""

import json
import os
import signal
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.components.orchestrator as orchestrator_module
from src.components.orchestrator import (
    SessionOrchestrator,
    _attach_permission_denial_outcome_to_record,
    _compose_effective_risk_with_selected_cell,
    _permission_denial_runtime_outcome,
    prescreen_mso,
    LONDON_START, LONDON_END, LONDON_CORE_END, NY_START, NY_END,
    LOCK_DIR,
)
from src.components.permissions import ExecutionDenial


def test_selected_cell_caps_runtime_risk_without_overwriting_lower_runtime_risk():
    capped, capped_record = _compose_effective_risk_with_selected_cell(2.0, 0.25)
    reduced, reduced_record = _compose_effective_risk_with_selected_cell(0.125, 0.25)
    zero, zero_record = _compose_effective_risk_with_selected_cell(0.0, 0.25)

    assert capped == pytest.approx(0.25)
    assert capped_record["status"] == "selected_cell_capped_runtime_risk"
    assert reduced == pytest.approx(0.125)
    assert reduced_record["status"] == "runtime_risk_below_or_equal_selected_cell"
    assert zero == pytest.approx(0.0)
    assert zero_record["status"] == "preserved_nonpositive_runtime_risk"


class TestExitEntryTimeResolution:
    def test_future_trade_state_entry_time_repairs_from_execution_fill_time(self):
        orch = object.__new__(SessionOrchestrator)
        orch._trade_entry_time = datetime(2026, 6, 1, 16, 16, 18, tzinfo=timezone.utc)
        orch._active_trade_record = {
            "execution": {"fill_time_utc": "2026-06-01T13:16:19+00:00"}
        }
        exit_time = datetime(2026, 6, 1, 13, 47, 26, tzinfo=timezone.utc)

        entry_time, source, status = orch._entry_time_for_exit(exit_time)

        assert entry_time == datetime(2026, 6, 1, 13, 16, 19, tzinfo=timezone.utc)
        assert source == "trade_record_execution_fill_time_utc"
        assert status == "ENTRY_TIME_FUTURE_REPAIRED_FROM_EXECUTION_FILL_TIME"


class TestPrescreenMSO:
    def _make_mso(self, d1_dir="bullish", h4_dir="bullish"):
        return SimpleNamespace(
            timeframes={
                "D1": SimpleNamespace(structure=SimpleNamespace(direction=d1_dir)),
                "H4": SimpleNamespace(structure=SimpleNamespace(direction=h4_dir)),
            }
        )

    def test_pass_bullish_aligned(self):
        passed, reason = prescreen_mso(self._make_mso("bullish", "bullish"))
        assert passed
        assert reason == ""

    def test_pass_bearish_aligned(self):
        passed, reason = prescreen_mso(self._make_mso("bearish", "bearish"))
        assert passed

    def test_pass_d1_ranging_h4_clear(self):
        """D1 transitional + H4 bullish → passes (H4 provides direction)."""
        passed, reason = prescreen_mso(self._make_mso("transitional", "bullish"))
        assert passed
        assert reason == ""

    def test_pass_d1_clear_h4_insufficient(self):
        """D1 bullish + H4 insufficient → passes (D1 provides direction)."""
        passed, reason = prescreen_mso(self._make_mso("bullish", "insufficient_data"))
        assert passed
        assert reason == ""

    def test_fail_both_unclear(self):
        """Both D1 and H4 unclear → no directional consensus → skip."""
        passed, reason = prescreen_mso(self._make_mso("transitional", "ranging"))
        assert not passed
        assert "no_direction" in reason

    def test_fail_h4_conflict(self):
        passed, reason = prescreen_mso(self._make_mso("bullish", "bearish"))
        assert not passed
        assert "conflict" in reason


class TestPreAIPoiProximityGate:
    def _make_far_ob_mso(self):
        return SimpleNamespace(
            timeframes={
                "H1": SimpleNamespace(
                    order_blocks=[
                        SimpleNamespace(
                            mitigated=False,
                            type="bullish",
                            low=100.0,
                            high=101.0,
                        )
                    ],
                    breaker_blocks=[],
                ),
                "M15": SimpleNamespace(fair_value_gaps=[]),
            }
        )

    def _config(self, *, apply=True):
        return {
            "model_a": {"enabled_frameworks": ["ob_retest"]},
            "pre_ai_gates": {
                "poi_proximity_enabled": True,
                "poi_proximity_apply_to_ai_call": apply,
                "poi_proximity_tolerance_pct": 0.01,
                "poi_proximity_source_path": (
                    ".context/02_session_handoffs/"
                    "15_apr13_pool_type_fix_prescreen_handoff.md"
                ),
            },
        }

    def test_runtime_hook_skips_ai_when_active_framework_poi_is_far(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        raw_data = {"candles": {"M15": [{"close": 120.0}]}}

        record = orch._evaluate_poi_proximity_pre_ai_gate(
            mso=self._make_far_ob_mso(),
            raw_data=raw_data,
            bias_result={"bias": "bullish"},
            poi_gate_config=self._config(apply=True),
        )

        assert record["skipped"] is True
        assert record["would_skip"] is True
        assert record["reason"] == "bullish_price_far_from_pois_15.8pct_for_ob_retest"
        assert raw_data["pre_ai_poi_proximity_gate"] == record

    def test_runtime_hook_can_shadow_without_skipping_ai(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        raw_data = {"candles": {"M15": [{"close": 120.0}]}}

        record = orch._evaluate_poi_proximity_pre_ai_gate(
            mso=self._make_far_ob_mso(),
            raw_data=raw_data,
            bias_result={"bias": "bullish"},
            poi_gate_config=self._config(apply=False),
        )

        assert record["skipped"] is False
        assert record["would_skip"] is True
        assert raw_data["pre_ai_poi_proximity_gate"] == record


class TestPendingFillTradeRecordCapture:
    def test_pending_telemetry_explains_live_generated_zero_static_match_rows(self):
        telemetry = SessionOrchestrator._gtos_vnext_pending_telemetry(
            vnext_pre_ai=None,
            vnext_decision=SimpleNamespace(
                decision="FOLLOW",
                reason="broader_origin_candidate_contract_live_generated_pre_ai",
                matched=True,
                evidence={"matched_rows": 0, "metrics": {}},
            ),
            vnext_risk_adjustment=SimpleNamespace(
                multiplier=1.0,
                would_multiplier=1.0,
                reason="vnext_risk_follow",
            ),
            vnext_moonshot_dynamic_execution=SimpleNamespace(
                source_event={
                    "broader_origin_allowed": True,
                    "broader_origin_metrics": {
                        "selected_count": 557,
                        "performance_rows": 557,
                    },
                    "selected_cell_risk_allowed": True,
                    "selected_cell_risk_pct": 0.25,
                    "selected_cell_risk_cell_id": "STAGE13-FN-RISK-CELL-000218",
                },
                selected_policy="partial_be_runner",
                execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
                applied=True,
                replaced_policy="retired_static_baseline_comparator",
                candidate_action="TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                decision_status="vnext_candidate_ready",
                source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
                exit_management_action="ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER",
                prop_action="ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
                fixed_target_role="baseline_comparator_only",
            ),
        )

        assert telemetry["gtos_vnext_matched"] is True
        assert telemetry["gtos_vnext_matched_rows"] == 0
        assert "live_generated_broader_origin_pre_ai_decision" in telemetry[
            "gtos_vnext_matched_rows_status"
        ]
        assert telemetry["gtos_vnext_broader_origin_selected_rows"] == 557
        assert telemetry["gtos_vnext_selected_cell_risk_pct"] == 0.25

    def test_promoted_pending_record_gets_execution_block(self, tmp_path):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._mt5_symbol = "XAUUSD"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "records")}}
        orch.execution = SimpleNamespace(
            active_trade=SimpleNamespace(
                trade_id="lim_XAUUSD_2026-06-01_120000",
                ticket=242190777,
                entry_order_ticket=242190777,
                entry_deal_ticket=0,
                entry_order_retcode=10009,
                direction="SHORT",
                entry_price=3340.25,
                stop_loss=3346.25,
                take_profit_1=3334.25,
                take_profit_2=3322.25,
                take_profit_3=0.0,
                initial_volume=0.5,
                current_volume=0.5,
                sl_distance=6.0,
                risk_pct_at_entry=0.25,
                cash_risk_amount=250.0,
                gtos_vnext_dynamic_policy_selected="partial_be_runner",
                gtos_vnext_execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
                gtos_vnext_dynamic_policy_applied=True,
                gtos_vnext_dynamic_policy_replaced_policy="static_fixed_target",
                gtos_vnext_dynamic_policy_candidate_action="TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                gtos_vnext_dynamic_policy_decision_status="vnext_candidate_ready",
                gtos_vnext_dynamic_policy_source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
                gtos_vnext_dynamic_policy_exit_management_action=(
                    "ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER"
                ),
                gtos_vnext_dynamic_policy_prop_action="ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
                gtos_vnext_dynamic_policy_fixed_target_role="baseline_comparator_only",
                gtos_vnext_dynamic_be_trigger_r=1.0,
                gtos_vnext_dynamic_final_target_r=3.0,
                gtos_vnext_dynamic_be_trigger_price=3334.25,
                gtos_vnext_dynamic_final_target_price=3322.25,
                gtos_vnext_dynamic_time_stop_bars=32,
                gtos_vnext_selector_row_id="STAGE13-FN-RISK-CELL-000001",
                gtos_vnext_selected_cell_risk_pct=0.25,
                gtos_vnext_selected_cell_risk_cell_id="STAGE13-FN-RISK-CELL-000001",
                gtos_vnext_source_event_hash="sourcehash",
            )
        )
        orch._latest_filled_lifecycle_row_for_active_trade = lambda: {
            "broker_symbol": "XAUUSD",
            "entry_price": 3341.0,
            "executed_entry_price": 3340.25,
            "execution_price_delta_from_limit": -0.75,
            "broker_order_action": "TRADE_ACTION_DEAL",
            "broker_order_entry_mode": "MARKET_ORDER",
            "broker_fill_state": "filled",
            "fill_time_utc": "2026-06-01T12:01:00+00:00",
            "filled_order_position_join_keys": ["mt5_position_ticket:242190777"],
            "exact_r_join_key_status": "FILLED_ORDER_POSITION_KEYS_CAPTURED",
            "gtos_vnext_prop_safe_selector_after_risk_pct": 0.25,
            "source_branch": "gtos_vnext_ltf_path_pending_monitor",
            "check_context": "inside_kz_ltf_sleep",
            "checked_candle_time_utc": "2026-06-01T12:00:00+00:00",
            "source_timeframe": "M1",
            "record_path": "knowledge_base/trade_records/XAUUSD/2026-06-01_london_1200.json",
        }
        orch._refresh_vnext_candidate_intelligence_packet = (
            lambda record, **kwargs: record.setdefault("decision_pipeline", {}).setdefault(
                "gtos_vnext_candidate_intelligence_packet",
                {"final_order_decision": kwargs.get("final_order_decision")},
            )
        )
        record = {
            "metadata": {
                "trade_id": "XAUUSD_2026-06-01_london_1200",
                "date": "2026-06-01",
                "symbol": "XAUUSD",
                "kill_zone": "london",
                "candle_time": "2026-06-01T12:00:00+00:00",
            },
            "decision_pipeline": {"final_outcome": "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"},
            "limit_intent": {
                "trade_id": "lim_XAUUSD_2026-06-01_120000",
                "limit_price": 3341.0,
            },
            "instrumentation": {},
        }

        orch._attach_pending_fill_execution_to_record(record)

        assert record["decision_pipeline"]["final_outcome"] == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"
        assert record["execution"]["broker_fill_state"] == "filled"
        assert record["execution"]["ticket"] == 242190777
        assert record["execution"]["entry_deal_ticket"] is None
        assert record["execution"]["take_profit_1"] == 3334.25
        assert record["execution"]["take_profit_2"] == 3322.25
        assert record["execution"]["active_take_profit"] == 3322.25
        assert record["execution"]["broker_take_profit"] == 3322.25
        assert record["execution"]["gtos_vnext_dynamic_policy_applied"] is True
        assert record["execution"]["gtos_vnext_dynamic_be_trigger_r"] == 1.0
        assert record["execution"]["gtos_vnext_dynamic_final_target_r"] == 3.0
        assert record["execution"]["gtos_vnext_dynamic_be_trigger_price"] == 3334.25
        assert record["execution"]["gtos_vnext_dynamic_final_target_price"] == 3322.25
        assert (
            record["execution"]["entry_deal_ticket_status"]
            == "mt5_result_deal_ticket_absent_using_order_position_join_keys"
        )
        assert "mt5_entry_deal_ticket:0" not in record["execution"][
            "filled_order_position_join_keys"
        ]
        assert record["execution"]["gtos_vnext_selected_cell_risk_pct"] == 0.25
        assert (
            record["instrumentation"]["gtos_vnext_limit_fill_execution_capture_status"]
            == "captured_from_trade_state_and_pending_limit_lifecycle"
        )
        saved = tmp_path / "records" / "XAUUSD" / "2026-06-01_london_1200.json"
        assert saved.exists()

    def test_clear_pending_record_persists_sl_too_close_terminal_state(
        self, tmp_path, monkeypatch,
    ):
        lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
        trade_id = "lim_EURJPY_2026-06-01_131526"
        lifecycle_path.write_text(
            json.dumps({
                "symbol": "EURJPY",
                "trade_id": trade_id,
                "timestamp_utc": "2026-06-01T13:17:27.782457+00:00",
                "intent_after_check": "cancelled_sl_too_close",
                "reason": "sl_too_close",
                "broker_fill_state": "not_filled",
                "order_send_attempted": False,
                "order_send_success": False,
                "sl_too_close_abort": True,
            }) + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            orchestrator_module,
            "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
            str(lifecycle_path),
        )
        base_path = tmp_path / "records"
        record_dir = base_path / "EURJPY"
        record_dir.mkdir(parents=True)
        record_path = record_dir / "2026-06-01_ny_1315.json"
        record_path.write_text(
            json.dumps({
                "metadata": {
                    "trade_id": "EURJPY_2026-06-01_ny_1315",
                    "date": "2026-06-01",
                    "symbol": "EURJPY",
                    "kill_zone": "ny",
                    "candle_time": "2026-06-01T13:15:00+00:00",
                },
                "decision_pipeline": {
                    "final_outcome": "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN",
                },
                "limit_intent": {"trade_id": trade_id},
                "instrumentation": {},
            }),
            encoding="utf-8",
        )

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "EURJPY"
        orch.config = {"trade_capture": {"base_path": str(base_path)}}
        orch._pending_trade_record_path = str(record_path)

        orch._clear_pending_trade_record(
            trade_id,
            reason="vnext_ltf_path_no_fill",
        )

        saved = json.loads(record_path.read_text(encoding="utf-8"))
        assert saved["decision_pipeline"]["final_outcome"] == (
            "LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE"
        )
        assert saved["limit_intent"]["terminal_state"] == "cancelled_sl_too_close"
        assert saved["limit_intent"]["terminal_reason"] == "sl_too_close"
        assert saved["instrumentation"][
            "gtos_vnext_pending_limit_terminal_record_source"
        ] == "pending_limit_lifecycle"
        assert orch._pending_trade_record_path is None

    def test_pending_lifecycle_ticket_reconnect_prefers_real_record(self, tmp_path):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "BTCUSD"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "records")}}
        orch.execution = SimpleNamespace(
            active_trade=SimpleNamespace(ticket=242190777, direction="SHORT")
        )
        lifecycle_row = {
            "symbol": "BTCUSD",
            "broker_symbol": "BTCUSD",
            "candidate_id": "broadorigin_106777432745ee99599b8e76",
            "trade_id": "lim_BTCUSD_2026-06-01_120031",
            "trade_state_ticket": 242190777,
            "mt5_position_ticket": 242190777,
            "broker_fill_state": "filled",
            "order_send_success": True,
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_execution_policy_id": (
                "vnext_exec_partial_50_at_1r_be_runner_to_3r"
            ),
        }
        orch._latest_filled_lifecycle_row_for_active_trade = lambda: lifecycle_row

        record_path = (
            tmp_path
            / "records"
            / "BTCUSD"
            / "2026-06-01_off_configured_session_1200.json"
        )
        record_path.parent.mkdir(parents=True)
        record_path.write_text(
            json.dumps(
                {
                    "metadata": {
                        "trade_id": "BTCUSD_2026-06-01_off_configured_session_1200",
                        "symbol": "BTCUSD",
                        "date": "2026-06-01",
                        "kill_zone": "off_configured_session",
                        "candle_time": "2026-06-01T12:00:00+00:00",
                    },
                    "limit_intent": {
                        "trade_id": "lim_BTCUSD_2026-06-01_120031",
                    },
                    "moonshot_broader_origin_candidate": {
                        "candidate_id": "broadorigin_106777432745ee99599b8e76",
                    },
                    "decision_pipeline": {
                        "gtos_vnext_candidate_intelligence_packet": {
                            "candidate_identity": {
                                "candidate_id": (
                                    "broadorigin_106777432745ee99599b8e76"
                                ),
                            }
                        }
                    },
                    "exit": None,
                }
            ),
            encoding="utf-8",
        )

        result = orch._trade_record_from_pending_lifecycle_ticket()

        assert result is not None
        matched_path, record, reason = result
        assert matched_path == record_path
        assert reason == "pending_lifecycle_ticket_match"
        assert record["metadata"]["trade_id"] == (
            "BTCUSD_2026-06-01_off_configured_session_1200"
        )
        assert record["instrumentation"]["gtos_vnext_recovered_lifecycle_status"] == ""
        assert "broadorigin_106777432745ee99599b8e76" in (
            SessionOrchestrator._trade_record_identity_keys(record)
        )

    def test_pending_lifecycle_reconnect_supersedes_unreconciled_broker_closed_record(
        self, tmp_path
    ):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "JP225"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "namespaced")}}
        orch.execution = SimpleNamespace(
            active_trade=SimpleNamespace(ticket=242405337, direction="LONG")
        )
        record_path = (
            tmp_path
            / "legacy_records"
            / "JP225"
            / "2026-06-02_moonshot_h03_04_0345_broadorigin_f2601.json"
        )
        lifecycle_row = {
            "symbol": "JP225",
            "broker_symbol": "JP225",
            "candidate_id": "broadorigin_f2601",
            "trade_id": "lim_JP225_2026-06-02_034510",
            "trade_state_ticket": 242405337,
            "mt5_position_ticket": 242405337,
            "broker_fill_state": "filled",
            "order_send_success": True,
            "record_path": str(record_path),
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_execution_policy_id": (
                "vnext_exec_partial_50_at_1r_be_runner_to_3r"
            ),
        }
        orch._latest_filled_lifecycle_row_for_active_trade = lambda: lifecycle_row
        record_path.parent.mkdir(parents=True)
        record_path.write_text(
            json.dumps(
                {
                    "metadata": {
                        "trade_id": "lim_JP225_2026-06-02_034510",
                        "candidate_id": "broadorigin_f2601",
                        "symbol": "JP225",
                    },
                    "limit_intent": {
                        "trade_id": "lim_JP225_2026-06-02_034510",
                    },
                    "decision_pipeline": {
                        "gtos_vnext_candidate_intelligence_packet": {
                            "candidate_identity": {
                                "candidate_id": "broadorigin_f2601",
                                "framework": "origin_liquidity_sweep_reclaim",
                                "origin_family": "liquidity_sweep_reclaim",
                                "side": "LONG",
                            }
                        }
                    },
                    "exit": {
                        "exit_type": "broker_closed",
                        "actual_r": 0.4606,
                        "broker_deal_reconciled": False,
                        "broker_close_deal_id": None,
                        "broker_close_order_id": None,
                    },
                }
            ),
            encoding="utf-8",
        )

        result = orch._trade_record_from_pending_lifecycle_ticket()

        assert result is not None
        matched_path, record, reason = result
        assert matched_path == record_path
        assert reason == "pending_lifecycle_ticket_match"
        assert record["exit"] is None
        assert record["decision_pipeline"]["gtos_vnext_candidate_intelligence_packet"][
            "candidate_identity"
        ]["framework"] == "origin_liquidity_sweep_reclaim"
        assert record["instrumentation"]["gtos_vnext_stale_terminal_exit_superseded"] is True
        stale_exit = record["lifecycle"]["stale_terminal_exit_superseded"]
        assert stale_exit["superseded_exit"]["exit_type"] == "broker_closed"
        assert stale_exit["lifecycle_ticket"] == 242405337

    def test_lifecycle_recovery_record_derives_metadata_from_trade_id(self):
        record = SessionOrchestrator._trade_record_from_lifecycle_row(
            {
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "candidate_id": "broadorigin_7a6daacd94f848e651899530",
                "trade_id": "NAS100_2026-05-29_moonshot_h06_07_0615",
                "selected_policy": "partial_be_runner",
                "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                "broker_lifecycle_status": "PARTIAL_CLOSED_RESIDUAL_OPEN_BROKER",
                "open_position_present": True,
            }
        )

        assert record is not None
        assert record["metadata"]["date"] == "2026-05-29"
        assert record["metadata"]["kill_zone"] == "moonshot_h06_07"
        assert record["metadata"]["candle_time"] == "2026-05-29T06:15:00+00:00"
        assert record["metadata"]["symbol"] == "NAS100"
        assert record["metadata"]["broker_symbol"] == "NDX100"


class TestKillZoneDetection:
    def _make_orchestrator(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        # Set KZ instance vars that __init__ normally loads from config
        orch._london_start = LONDON_START
        orch._london_end = LONDON_END
        orch._london_core_end = LONDON_CORE_END
        orch._ny_start = NY_START
        orch._ny_end = NY_END
        # Dynamic KZ windows dict used by _get_active_kill_zone
        orch._kz_windows = {
            "london": {
                "start_min": LONDON_START[0] * 60 + LONDON_START[1],
                "end_min": LONDON_END[0] * 60 + LONDON_END[1],
                "core_end_min": LONDON_CORE_END[0] * 60 + LONDON_CORE_END[1],
                "crosses_midnight": False,
            },
            "ny": {
                "start_min": NY_START[0] * 60 + NY_START[1],
                "end_min": NY_END[0] * 60 + NY_END[1],
                "core_end_min": NY_END[0] * 60 + NY_END[1],
                "crosses_midnight": False,
            },
        }
        return orch

    def test_london_kz(self):
        orch = self._make_orchestrator()
        # 08:00 UTC → London
        now = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) == "london"

    def test_ny_kz(self):
        orch = self._make_orchestrator()
        # 14:00 UTC → NY
        now = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) == "ny"

    def test_no_kz_between(self):
        orch = self._make_orchestrator()
        # 11:00 UTC → between KZs
        now = datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) is None

    def test_no_kz_before_london(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 5, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) is None

    def test_london_boundary_start(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 7, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) == "london"

    def test_london_extended_window(self):
        orch = self._make_orchestrator()
        # 09:30 UTC → now inside extended London (09:30-10:30)
        now = datetime(2026, 4, 1, 9, 30, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) == "london"
        assert orch._is_extended_london(now)

    def test_london_core_not_extended(self):
        orch = self._make_orchestrator()
        # 08:00 UTC → core London, not extended
        now = datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) == "london"
        assert not orch._is_extended_london(now)

    def test_london_boundary_end(self):
        orch = self._make_orchestrator()
        # 10:30 UTC → just past London end (exclusive)
        now = datetime(2026, 4, 1, 10, 30, tzinfo=timezone.utc)
        assert orch._get_active_kill_zone(now) is None

    def test_is_between_kz(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc)
        assert orch._is_between_kz(now)

    def test_is_after_all_kz(self):
        orch = self._make_orchestrator()
        # 17:30 + 120min = past all (15:30 + 120 = 17:30)
        now = datetime(2026, 4, 1, 17, 31, tzinfo=timezone.utc)
        assert orch._is_after_all_kz(now)


class TestTimeoutTrailingAnchor:
    def _make_orchestrator(self, entry_time: str):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.execution = SimpleNamespace(
            active_trade=SimpleNamespace(entry_time=entry_time)
        )
        return orch

    def test_late_fill_uses_entry_time_as_timeout_anchor(self):
        kz_end = datetime(2026, 5, 11, 9, 30, tzinfo=timezone.utc)
        entry = datetime(2026, 5, 11, 10, 45, tzinfo=timezone.utc)
        orch = self._make_orchestrator(entry.isoformat())

        assert orch._timeout_trailing_anchor_time(kz_end) == entry

    def test_pre_kz_end_fill_uses_kz_end_as_timeout_anchor(self):
        kz_end = datetime(2026, 5, 11, 9, 30, tzinfo=timezone.utc)
        entry = datetime(2026, 5, 11, 8, 15, tzinfo=timezone.utc)
        orch = self._make_orchestrator(entry.isoformat())

        assert orch._timeout_trailing_anchor_time(kz_end) == kz_end


class TestPendingLimitOutsideKzLoop:
    @pytest.mark.parametrize("branch", ["between_kz", "after_all_kz", "pre_kz"])
    def test_main_loop_checks_pending_limits_in_every_non_kz_state(self, monkeypatch, branch):
        fixed_now = datetime(2026, 4, 14, 11, 0, tzinfo=timezone.utc)

        class _FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                if tz is None:
                    return fixed_now.replace(tzinfo=None)
                return fixed_now.astimezone(tz)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.running = True
        orch._symbol = "US30"
        orch.session_state = {
            "date": fixed_now.strftime("%Y-%m-%d"),
            "current_kill_zone": "london",
        }
        orch.execution = SimpleNamespace(
            active_trade=None,
            pending_intent=object(),
        )

        calls = []
        monkeypatch.setattr(orchestrator_module, "datetime", _FrozenDatetime)
        monkeypatch.setattr(orchestrator_module, "_write_heartbeat", lambda extra=None: None)
        orch._new_day = lambda today: calls.append(("new_day", today))
        orch._get_active_kill_zone = lambda now: None
        orch._is_between_kz = lambda now: branch == "between_kz"
        orch._is_after_all_kz = lambda now: branch == "after_all_kz"
        orch._check_trade_and_capture = lambda: calls.append(("trade_check", branch))
        orch._monitor_expired_poi_watches_from_mt5 = (
            lambda context: calls.append(("expired_poi_watch", context))
        )
        orch._manage_timeout_trailing = lambda: calls.append(("timeout_trailing", branch))
        orch._check_pending_limit_outside_kz = lambda: calls.append(("pending_limit", branch))
        orch._next_kz_start_time = lambda now: fixed_now + timedelta(hours=1)
        orch._interruptible_sleep = lambda seconds: setattr(orch, "running", False)
        orch._monitored_sleep = lambda seconds: setattr(orch, "running", False)

        orch._main_loop()

        assert ("pending_limit", branch) in calls
        assert calls.count(("pending_limit", branch)) == 1
        assert ("new_day", fixed_now.strftime("%Y-%m-%d")) not in calls


class TestSleepRaceGuards:
    def _make_orchestrator(self, entry_time: str | None = None):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        if entry_time is not None:
            orch.execution = SimpleNamespace(
                active_trade=SimpleNamespace(entry_time=entry_time)
            )
        else:
            orch.running = True
            orch._symbol = "XAUUSD"
            orch.execution = SimpleNamespace(active_trade=None)
        return orch

    def test_interruptible_sleep_does_not_sleep_negative_remaining(self, monkeypatch):
        orch = self._make_orchestrator()
        times = iter([100.0, 100.0, 101.001])
        sleeps = []

        monkeypatch.setattr(orchestrator_module, "_write_heartbeat", lambda extra=None: None)
        monkeypatch.setattr(orchestrator_module.time, "time", lambda: next(times))
        monkeypatch.setattr(orchestrator_module.time, "sleep", lambda seconds: sleeps.append(seconds))

        orch._interruptible_sleep(1.0)

        assert sleeps == []
        assert orch.running is True

    def test_monitored_sleep_does_not_delegate_negative_chunk(self, monkeypatch):
        orch = self._make_orchestrator()
        times = iter([200.0, 200.0, 201.001])
        delegated_chunks = []

        monkeypatch.setattr(orchestrator_module.time, "time", lambda: next(times))
        orch._interruptible_sleep = lambda seconds: delegated_chunks.append(seconds)
        orch._check_trade_and_capture = lambda: None

        orch._monitored_sleep(1.0)

        assert delegated_chunks == []

    def test_unparseable_entry_time_falls_back_to_kz_end(self):
        kz_end = datetime(2026, 5, 11, 9, 30, tzinfo=timezone.utc)
        orch = self._make_orchestrator("not-a-date")

        assert orch._timeout_trailing_anchor_time(kz_end) == kz_end

    def test_manage_timeout_trailing_does_not_close_late_fill_before_post_fill_window(self):
        now = datetime.now(timezone.utc)
        trade = SimpleNamespace(entry_time=(now - timedelta(minutes=119)).isoformat())

        class FakeExecution:
            def __init__(self):
                self.active_trade = trade
                self.close_calls = []

            def handle_timeout_trailing(self):
                return "trailing"

            def close_position(self, reason):
                self.close_calls.append(reason)
                self.active_trade = None
                return True

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.execution = FakeExecution()
        orch._active_trade_record = None
        orch._update_mfe_mae_from_tick = lambda: None
        orch._last_kz_end_time = lambda: now - timedelta(minutes=180)

        orch._manage_timeout_trailing()

        assert orch.execution.active_trade is trade
        assert orch.execution.close_calls == []

    def test_manage_timeout_trailing_closes_after_post_fill_window(self):
        now = datetime.now(timezone.utc)
        trade = SimpleNamespace(entry_time=(now - timedelta(minutes=121)).isoformat())

        class FakeExecution:
            def __init__(self):
                self.active_trade = trade
                self.close_calls = []

            def handle_timeout_trailing(self):
                return "trailing"

            def close_position(self, reason):
                self.close_calls.append(reason)
                self.active_trade = None
                return True

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.execution = FakeExecution()
        orch._active_trade_record = None
        orch._update_mfe_mae_from_tick = lambda: None
        orch._last_kz_end_time = lambda: now - timedelta(minutes=180)

        orch._manage_timeout_trailing()

        assert orch.execution.active_trade is None
        assert orch.execution.close_calls == ["timeout_2h"]


class TestNextM15Close:
    def _make_orchestrator(self):
        return SessionOrchestrator.__new__(SessionOrchestrator)

    def test_at_00_gives_15(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 8, 0, 30, tzinfo=timezone.utc)
        result = orch._next_m15_close(now)
        assert result.minute == 15
        assert result.second == 5  # 5s buffer

    def test_at_14_gives_15(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 8, 14, 0, tzinfo=timezone.utc)
        result = orch._next_m15_close(now)
        assert result.minute == 15

    def test_at_45_gives_next_hour(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 8, 45, 30, tzinfo=timezone.utc)
        result = orch._next_m15_close(now)
        assert result.hour == 9
        assert result.minute == 0

    def test_at_59_gives_next_hour(self):
        orch = self._make_orchestrator()
        now = datetime(2026, 4, 1, 8, 59, 0, tzinfo=timezone.utc)
        result = orch._next_m15_close(now)
        assert result.hour == 9
        assert result.minute == 0


class TestSessionMemory:
    def _make_orchestrator(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.session_memory = []
        return orch

    def test_format_empty(self):
        orch = self._make_orchestrator()
        assert orch._format_session_memory() == ""

    def test_format_with_entries(self):
        orch = self._make_orchestrator()
        orch.session_memory = [
            {"time": "08:15 UTC", "kill_zone": "london",
             "decision": "NO_TRADE", "summary": "NO_TRADE — insufficient sweep"},
        ]
        result = orch._format_session_memory()
        assert "08:15 UTC" in result
        assert "NO_TRADE" in result

    def test_sliding_window_max_6(self):
        orch = self._make_orchestrator()
        for i in range(8):
            analysis = SimpleNamespace(
                decision="NO_TRADE",
                no_trade_reason=f"reason_{i}",
                trade_parameters=None,
                reasoning=None,
                confidence_score=0,
            )
            orch._update_session_memory(analysis, "london")

        london_entries = [e for e in orch.session_memory if e["kill_zone"] == "london"]
        assert len(london_entries) <= 6


class TestNewDay:
    def test_resets_state(self, tmp_path, monkeypatch):
        # Bug 2 fix (Thursday 2026-04-23 audit): _new_day now also persists
        # the date via SESSION_STATE_DIR. Redirect to tmp_path so the test
        # doesn't touch real pipeline_state/. This also means _new_day now
        # requires self._symbol to be set (used as persistence key).
        from src.components import orchestrator as _orch_mod
        monkeypatch.setattr(_orch_mod, "SESSION_STATE_DIR", tmp_path)

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch.session_state = {"date": "2026-03-31", "trades_today": 1}
        orch.session_memory = [{"test": True}]
        orch.candle_log = [{"test": True}]
        orch._kz_windows = {
            "london": {"start_min": 420, "end_min": 630, "core_end_min": 570, "crosses_midnight": False},
            "ny": {"start_min": 780, "end_min": 930, "core_end_min": 930, "crosses_midnight": False},
        }
        orch._ci_context_text = ""
        # _new_day reads self.execution.pending_intent (stale-limit cleanup path)
        # and self.mt5.get_account_balance() (start_balance recording, wrapped in
        # try/except). Provide minimal stubs since __init__ is bypassed.
        orch.execution = SimpleNamespace(pending_intent=None)
        orch.mt5 = SimpleNamespace(
            get_account_balance=lambda: (_ for _ in ()).throw(RuntimeError("no mt5"))
        )
        orch._new_day("2026-04-01")

        assert orch.session_state["date"] == "2026-04-01"
        assert orch.session_state["trades_today"] == 0
        assert orch.session_state["trades_london"] == 0
        assert orch.session_state["trades_ny"] == 0
        assert orch.session_memory == []
        assert orch.candle_log == []


class TestPIDLocking:
    @pytest.fixture(autouse=True)
    def _isolate_lock_dir(self, tmp_path, monkeypatch):
        from src.components import orchestrator as _orch
        tmp_meta = tmp_path / "meta"
        tmp_meta.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(_orch, "LOCK_DIR", str(tmp_meta))
        self.LOCK_PATH = str(tmp_meta / ".orchestrator_XAUUSD.lock")
        yield

    def _make_orch(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._lock_path = self.LOCK_PATH
        return orch

    def test_acquire_creates_lock(self):
        orch = self._make_orch()
        orch._acquire_lock()
        lock = Path(self.LOCK_PATH)
        assert lock.exists()
        with open(lock) as f:
            data = json.load(f)
        assert data["pid"] == os.getpid()

    def test_stale_lock_overridden(self):
        """A lock from a dead process should be overridden."""
        lock = Path(self.LOCK_PATH)
        lock.parent.mkdir(parents=True, exist_ok=True)
        with open(lock, "w") as f:
            json.dump({"pid": 99999999, "started": "old"}, f)

        orch = self._make_orch()
        orch._acquire_lock()  # Should not raise
        with open(lock) as f:
            data = json.load(f)
        assert data["pid"] == os.getpid()

    def test_release_removes_lock(self):
        orch = self._make_orch()
        orch._acquire_lock()
        orch._release_lock()
        assert not Path(self.LOCK_PATH).exists()


class TestSignalHandler:
    def test_signal_sets_running_false(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.running = True
        orch._signal_handler(signal.SIGTERM, None)
        assert orch.running is False


class TestCandleLog:
    def test_log_candle(self):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.candle_log = []
        orch._log_candle("NO_TRADE", "ranging D1", "london")
        assert len(orch.candle_log) == 1
        assert orch.candle_log[0]["decision"] == "NO_TRADE"
        assert orch.candle_log[0]["kill_zone"] == "london"


class TestDeploymentPhaseRuntimeOutcome:
    def test_phase_2_permission_denial_routes_to_log_only_no_order(self):
        denial = ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_2_log_only",
            {"phase": 2},
        )

        outcome = _permission_denial_runtime_outcome(denial)

        assert outcome["final_outcome"] == "LOG_ONLY_DEPLOYMENT_PHASE"
        assert outcome["candle_decision"] == "LOG_ONLY_DEPLOYMENT_PHASE"
        assert outcome["execution_action"] == "LOG_ONLY_NO_ORDER"
        assert outcome["deployment_phase"] == 2

    def test_phase_1_permission_denial_remains_rejected_order(self):
        denial = ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_1_block_all_orders",
            {"phase": 1},
        )

        outcome = _permission_denial_runtime_outcome(denial)

        assert outcome["final_outcome"] == "REJECTED_GATE0_DEPLOYMENT_PHASE"
        assert outcome["candle_decision"] == "REJECTED"
        assert outcome["execution_action"] == "REJECT_ORDER"

    def test_phase_2_permission_denial_attaches_log_only_evidence_to_record(self):
        denial = ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_2_log_only",
            {"phase": 2},
        )
        outcome = _permission_denial_runtime_outcome(denial)
        record = {"decision_pipeline": {}}

        _attach_permission_denial_outcome_to_record(record, denial, outcome)

        assert record["decision_pipeline"] == {
            "final_outcome": "LOG_ONLY_DEPLOYMENT_PHASE",
            "permission_gate": "gate0_deployment_phase",
            "permission_reason": "deployment_phase_2_log_only",
            "permission_execution_action": "LOG_ONLY_NO_ORDER",
            "deployment_phase": 2,
        }


class TestWriteNoTrade:
    """Verify orchestrator writes NoTradeRecord when analysis returns NO_TRADE."""

    def test_write_no_trade_called_on_no_trade_analysis(self, tmp_path):
        """After AI returns NO_TRADE, orchestrator should persist a NoTradeRecord."""
        from unittest.mock import MagicMock, patch
        from src.models.trade_models import NoTradeRecord

        # Set up a minimal orchestrator
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.kb = MagicMock()
        orch.kb.write_no_trade = MagicMock(return_value="nt_2026-04-11_0730")
        orch._symbol = "XAUUSD"
        orch.candle_log = []

        # Call the helper directly
        orch._write_no_trade_record(
            reason="Daily bias unclear",
            kill_zone="london",
            candle_time="2026-04-11T07:30:00Z",
            analysis_dict={"reasoning": {"daily_bias": {"direction": "ranging"}}},
        )

        orch.kb.write_no_trade.assert_called_once()
        record = orch.kb.write_no_trade.call_args[0][0]
        assert isinstance(record, NoTradeRecord)
        assert record.reason == "Daily bias unclear"
        assert record.decision == "NO_TRADE"

    def test_write_no_trade_does_not_block_on_error(self, tmp_path):
        """If KB write fails, the pipeline should NOT crash."""
        from unittest.mock import MagicMock

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.kb = MagicMock()
        orch.kb.write_no_trade.side_effect = OSError("disk full")
        orch._symbol = "XAUUSD"
        orch.candle_log = []

        # Should not raise
        orch._write_no_trade_record(
            reason="test",
            kill_zone="london",
            candle_time="2026-04-11T07:30:00Z",
        )


class TestDailyPnlUpdate:
    """Verify _update_daily_pnl populates session_state from MT5."""

    def test_updates_daily_pnl_from_deals(self):
        """T2.8: daily_pnl_pct is now MTM — (equity - start_equity) / start_equity.
        start_equity must be seeded (normally by ``_new_day``); here we pin it
        to 100000 so the ``99980`` equity yields the expected -0.02%.
        """
        from unittest.mock import MagicMock
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = MagicMock()
        orch.mt5.get_history_deals.return_value = [
            {"profit": -50.0}, {"profit": 30.0}
        ]
        orch.mt5.get_account_balance.return_value = 100000.0
        orch.mt5.get_account_equity.return_value = 99980.0
        orch._symbol = "XAUUSD"
        orch.session_state = {"start_balance": 100000.0, "start_equity": 100000.0}

        orch._update_daily_pnl()

        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-0.02, abs=0.001)
        assert orch.session_state["portfolio_drawdown_pct"] == pytest.approx(0.02, abs=0.001)

    def test_consecutive_losses_counted(self):
        """T2.8: ``_update_daily_pnl`` makes a single all-symbols
        ``get_history_deals`` call (the old symbol-specific realized-P&L
        call was dropped when MTM took over). Consec losses still counted
        off the last deals in reverse chronological order.
        """
        from unittest.mock import MagicMock
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = MagicMock()
        orch.mt5.get_history_deals.return_value = [
            {"profit": 10.0}, {"profit": -5.0}, {"profit": -3.0}, {"profit": -1.0},
        ]
        orch.mt5.get_account_balance.return_value = 100000.0
        orch.mt5.get_account_equity.return_value = 100000.0
        orch._symbol = "XAUUSD"
        orch.session_state = {"start_balance": 100000.0, "start_equity": 100000.0}

        orch._update_daily_pnl()

        # Last 3 deals are losses (counting from end)
        assert orch.session_state["consecutive_losses"] == 3

    def test_does_not_crash_on_mt5_error(self):
        from unittest.mock import MagicMock
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = MagicMock()
        orch.mt5.get_history_deals.side_effect = Exception("MT5 disconnected")
        orch._symbol = "XAUUSD"
        orch.session_state = {"start_balance": 100000.0}

        # Should not raise
        orch._update_daily_pnl()


class TestEmergencyStops:
    """Verify portfolio drawdown and consecutive loss stops."""

    def _make_orch(self):
        from unittest.mock import MagicMock
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.mt5 = MagicMock()
        orch._symbol = "XAUUSD"
        orch.config = {
            "risk": {
                "max_portfolio_drawdown_pct": 4.0,
                "max_consecutive_losses": 5,
                "max_trades_per_kill_zone_enabled": True,
                "max_trades_per_kill_zone": 2,
            },
        }
        orch.candle_log = []
        orch.session_state = {
            "start_balance": 100000.0,
            "portfolio_drawdown_pct": 0.0,
            "consecutive_losses": 0,
            "trades_london": 0,
        }
        # Mock _update_daily_pnl to not overwrite test values
        orch._update_daily_pnl = MagicMock()
        # execution is needed for cancel_limit_intent on emergency stops
        orch.execution = MagicMock()
        orch.execution.pending_intent = None
        orch._clear_pending_trade_record = MagicMock()
        return orch

    def test_portfolio_drawdown_blocks_trading(self):
        orch = self._make_orch()
        orch.session_state["portfolio_drawdown_pct"] = 5.0  # > 4% limit

        orch._process_candle("london")

        assert len(orch.candle_log) == 1
        assert orch.candle_log[0]["decision"] == "EMERGENCY_STOP"
        assert "portfolio_drawdown" in orch.candle_log[0]["detail"]
        orch.execution.cancel_limit_intent.assert_called_once_with("portfolio_drawdown_stop")

    def test_consecutive_losses_blocks_trading(self):
        orch = self._make_orch()
        orch.session_state["consecutive_losses"] = 5  # >= 5 limit

        orch._process_candle("london")

        assert len(orch.candle_log) == 1
        assert orch.candle_log[0]["decision"] == "EMERGENCY_STOP"
        assert "consecutive_losses" in orch.candle_log[0]["detail"]
        orch.execution.cancel_limit_intent.assert_called_once_with("consecutive_losses_stop")

    def test_kill_zone_trade_cap_blocks_third_trade_setup(self):
        orch = self._make_orch()
        orch.session_state["trades_london"] = 2

        orch._process_candle("london")

        assert len(orch.candle_log) == 1
        assert orch.candle_log[0]["decision"] == "EMERGENCY_STOP"
        assert "kill_zone_trade_cap:london trades=2 >= 2" in orch.candle_log[0]["detail"]
        orch.execution.cancel_limit_intent.assert_not_called()

    def test_vnext_runtime_makes_kill_zone_count_cap_evidence_only(self):
        orch = self._make_orch()
        orch.config["gtos_vnext_runtime"] = {
            "enabled": True,
            "apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
        }
        orch.session_state["trades_london"] = 2

        blocked = orch._check_kill_zone_trade_cap("london")

        assert blocked is False
        assert orch.candle_log == []
        orch.execution.cancel_limit_intent.assert_not_called()

    def test_kill_zone_trade_cap_cancels_pending_third_order(self):
        orch = self._make_orch()
        orch.session_state["trades_london"] = 2
        orch.execution.pending_intent = SimpleNamespace(trade_id="pending-3")

        orch._process_candle("london")

        assert orch.candle_log[0]["decision"] == "EMERGENCY_STOP"
        orch.execution.cancel_limit_intent.assert_called_once_with("kill_zone_trade_cap_stop")
        orch._clear_pending_trade_record.assert_called_once_with(
            "pending-3",
            reason="kz_trade_cap_stop",
        )

class TestAdoptedVnextTradeRecovery:
    def test_reconnect_adopted_position_from_pending_lifecycle_ticket(
        self,
        tmp_path,
        monkeypatch,
    ):
        lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
        slippage_path = tmp_path / "slippage.jsonl"
        trade_record_dir = tmp_path / "trade_records" / "XAUUSD"
        trade_record_dir.mkdir(parents=True)
        record_path = trade_record_dir / "2026-05-28_moonshot_h23_00_2345.json"
        record = {
            "trade_id": "XAUUSD_2026-05-28_moonshot_h23_00_2345",
            "metadata": {
                "trade_id": "XAUUSD_2026-05-28_moonshot_h23_00_2345",
                "symbol": "XAUUSD",
            },
            "limit_intent": {"trade_id": "lim_XAUUSD_2026-05-28_234505"},
            "decision_pipeline": {
                "gtos_vnext_candidate_intelligence_packet": {
                    "candidate_identity": {
                        "candidate_id": "broadorigin_79ae9b3c516c8729bee3716c",
                        "trade_id": "XAUUSD_2026-05-28_moonshot_h23_00_2345",
                    }
                }
            },
            "exit": None,
            "instrumentation": {
                "candidate_id": "broadorigin_79ae9b3c516c8729bee3716c",
                "trade_id": "lim_XAUUSD_2026-05-28_234505",
                "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                "gtos_vnext_execution_policy_id": (
                    "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                ),
                "gtos_vnext_dynamic_policy_applied": True,
                "gtos_vnext_recovered_partial_closed": False,
                "gtos_vnext_recovered_residual_open": False,
            },
        }
        record_path.write_text(json.dumps(record), encoding="utf-8")
        lifecycle_path.write_text(
            json.dumps(
                {
                    "symbol": "XAUUSD",
                    "side": "SHORT",
                    "broker_fill_state": "filled",
                    "order_send_success": True,
                    "trade_state_ticket": 241725208,
                    "mt5_position_ticket": 241725208,
                    "mt5_entry_order_ticket": 241725208,
                    "candidate_id": "broadorigin_79ae9b3c516c8729bee3716c",
                    "trade_id": "lim_XAUUSD_2026-05-28_234505",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        slippage_path.write_text(
            json.dumps(
                {
                    "ticket": 241725208,
                    "symbol": "XAUUSD",
                    "slippage_event_type": "entry",
                    "partial_exit_lifecycle": "ENTRY_FULL_POSITION_OPENED",
                    "fill_price": 3001.0,
                    "executed_entry_price": 3001.0,
                    "executed_stop_price": 3011.0,
                    "executed_lot_size": 0.10,
                    "cash_risk_amount": 250.0,
                    "ts": "2026-05-28T23:46:00+00:00",
                }
            )
            + "\n"
            + json.dumps(
                {
                    "ticket": 241725208,
                    "symbol": "XAUUSD",
                    "partial_close": True,
                    "partial_exit_lifecycle": "PARTIAL_EXIT",
                    "close_time": "2026-05-28T23:58:00+00:00",
                    "ts": "2026-05-28T23:58:00+00:00",
                    "fill_price": 2991.0,
                    "volume_closed": 0.05,
                    "initial_volume": 0.10,
                    "remaining_volume": 0.10,
                    "sl_distance": 10.0,
                    "cash_risk_amount": 0.0,
                    "close_reason": "tp1_partial_vnext_partial_be_runner",
                    "mt5_order_id": 12345,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            orchestrator_module,
            "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
            str(lifecycle_path),
        )
        monkeypatch.setattr(
            orchestrator_module,
            "SLIPPAGE_LOG_PATH",
            str(slippage_path),
        )

        trade = SimpleNamespace(
            ticket=241725208,
            direction="SHORT",
            trade_id="adopted_241725208",
            gtos_vnext_dynamic_policy_selected=None,
            gtos_vnext_execution_policy_id=None,
        )

        class FakeExecution:
            def __init__(self):
                self.active_trade = trade
                self.hydrate_calls = []

            def hydrate_vnext_dynamic_policy_from_record(self, rec, **kwargs):
                self.hydrate_calls.append((rec, kwargs))
                self.active_trade.gtos_vnext_dynamic_policy_selected = (
                    rec["instrumentation"]["gtos_vnext_dynamic_policy_selected"]
                )
                self.active_trade.gtos_vnext_execution_policy_id = (
                    rec["instrumentation"]["gtos_vnext_execution_policy_id"]
                )
                return True

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "trade_records")}}
        orch.execution = FakeExecution()
        init_calls = []
        orch._init_trade_tracking = lambda trade_state: init_calls.append(trade_state)

        orch._reconnect_trade_record()

        assert orch._active_trade_record["trade_id"] == record["trade_id"]
        assert orch._active_trade_record["metadata"] == record["metadata"]
        assert orch._active_trade_record["instrumentation"][
            "gtos_vnext_dynamic_policy_selected"
        ] == "partial_be_runner"
        assert orch._active_trade_record_path == str(record_path)
        assert trade.trade_id == "lim_XAUUSD_2026-05-28_234505"
        assert trade.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
        assert trade.gtos_vnext_execution_policy_id == (
            "vnext_exec_partial_50_at_1r_be_runner_to_3r"
        )
        assert orch.execution.hydrate_calls[0][1] == {
            "modify_broker_tp": False,
            "repair_recovered_sltp": True,
        }
        assert orch._active_trade_record["instrumentation"][
            "gtos_vnext_recovered_partial_closed"
        ] is True
        recovered = orch._active_trade_record["instrumentation"][
            "gtos_vnext_recovered_partial_close_events"
        ]
        assert recovered[0]["price"] == 2991.0
        assert recovered[0]["volume_closed"] == 0.05
        assert recovered[0]["remaining_volume"] == pytest.approx(0.05)
        assert recovered[0]["cash_risk_amount"] == 250.0
        assert init_calls == [trade]

    def test_reconnect_adopted_position_from_lifecycle_row_when_record_missing(
        self,
        tmp_path,
        monkeypatch,
    ):
        lifecycle_path = tmp_path / "pending_limit_lifecycle.jsonl"
        lifecycle_path.write_text(
            json.dumps(
                {
                    "symbol": "NAS100",
                    "broker_symbol": "NDX100",
                    "side": "LONG",
                    "broker_fill_state": "filled",
                    "order_send_success": True,
                    "trade_state_ticket": 241779188,
                    "mt5_position_ticket": 241779188,
                    "mt5_entry_order_ticket": 241779188,
                    "candidate_id": "broadorigin_7a6daacd94f848e651899530",
                    "trade_id": "lim_NAS100_2026-05-29_061505",
                    "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                    "gtos_vnext_execution_policy_id": (
                        "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                    ),
                    "gtos_vnext_dynamic_policy_applied": True,
                    "gtos_vnext_dynamic_be_trigger_r": 1.0,
                    "gtos_vnext_dynamic_final_target_r": 3.0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            orchestrator_module,
            "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
            str(lifecycle_path),
        )

        trade = SimpleNamespace(
            ticket=241779188,
            direction="LONG",
            trade_id="adopted_241779188",
            gtos_vnext_dynamic_policy_selected=None,
            gtos_vnext_execution_policy_id=None,
        )

        class FakeExecution:
            def __init__(self):
                self.active_trade = trade
                self.hydrate_calls = []

            def hydrate_vnext_dynamic_policy_from_record(self, rec, **kwargs):
                self.hydrate_calls.append((rec, kwargs))
                self.active_trade.gtos_vnext_dynamic_policy_selected = (
                    rec["instrumentation"]["gtos_vnext_dynamic_policy_selected"]
                )
                self.active_trade.gtos_vnext_execution_policy_id = (
                    rec["instrumentation"]["gtos_vnext_execution_policy_id"]
                )
                return True

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "NAS100"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "trade_records")}}
        orch.execution = FakeExecution()
        init_calls = []
        orch._init_trade_tracking = lambda trade_state: init_calls.append(trade_state)

        orch._reconnect_trade_record()

        assert orch._active_trade_record_path == str(lifecycle_path)
        assert orch._active_trade_record["instrumentation"][
            "gtos_vnext_dynamic_policy_selected"
        ] == "partial_be_runner"
        assert trade.trade_id == "lim_NAS100_2026-05-29_061505"
        assert trade.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
        assert trade.gtos_vnext_execution_policy_id == (
            "vnext_exec_partial_50_at_1r_be_runner_to_3r"
        )
        assert orch.execution.hydrate_calls[0][1] == {
            "modify_broker_tp": False,
            "repair_recovered_sltp": True,
        }
        assert init_calls == [trade]

    def test_reconnect_adopted_position_from_lane06_broker_lifecycle_fallback(
        self,
        tmp_path,
        monkeypatch,
    ):
        pending_path = tmp_path / "pending_limit_lifecycle.jsonl"
        pending_path.write_text("", encoding="utf-8")
        lane06_path = tmp_path / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
        lane06_path.write_text(
            json.dumps(
                {
                    "schema_version": "lane06_broker_lifecycle_v1",
                    "symbol": "NAS100",
                    "broker_symbol": "NDX100",
                    "side": "LONG",
                    "ticket": 241779188,
                    "entry_order_tickets": [241779188],
                    "entry_deal_tickets": [225628115],
                    "broker_lifecycle_status": "PARTIAL_CLOSED_RESIDUAL_OPEN_BROKER",
                    "candidate_id": "broadorigin_7a6daacd94f848e651899530",
                    "trade_id": "NAS100_2026-05-29_moonshot_h06_07_0615",
                    "selected_policy": "partial_be_runner",
                    "execution_policy_id": (
                        "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                    ),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            orchestrator_module,
            "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
            str(pending_path),
        )
        monkeypatch.setattr(
            orchestrator_module,
            "LANE06_BROKER_LIFECYCLE_LOG_PATH",
            str(lane06_path),
        )

        trade = SimpleNamespace(
            ticket=241779188,
            direction="LONG",
            trade_id="adopted_241779188",
            gtos_vnext_dynamic_policy_selected=None,
            gtos_vnext_execution_policy_id=None,
        )

        class FakeExecution:
            def __init__(self):
                self.active_trade = trade
                self.hydrate_calls = []

            def hydrate_vnext_dynamic_policy_from_record(self, rec, **kwargs):
                self.hydrate_calls.append((rec, kwargs))
                self.active_trade.gtos_vnext_dynamic_policy_selected = (
                    rec["instrumentation"]["gtos_vnext_dynamic_policy_selected"]
                )
                self.active_trade.gtos_vnext_execution_policy_id = (
                    rec["instrumentation"]["gtos_vnext_execution_policy_id"]
                )
                return True

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "NAS100"
        orch.config = {"trade_capture": {"base_path": str(tmp_path / "trade_records")}}
        orch.execution = FakeExecution()
        init_calls = []
        orch._init_trade_tracking = lambda trade_state: init_calls.append(trade_state)

        orch._reconnect_trade_record()

        assert orch._active_trade_record_path == str(lane06_path)
        assert trade.trade_id == "NAS100_2026-05-29_moonshot_h06_07_0615"
        assert trade.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
        assert trade.gtos_vnext_execution_policy_id == (
            "vnext_exec_partial_50_at_1r_be_runner_to_3r"
        )
        assert orch.execution.hydrate_calls[0][1] == {
            "modify_broker_tp": False,
            "repair_recovered_sltp": True,
        }
        assert orch._active_trade_record["instrumentation"][
            "gtos_vnext_recovered_partial_closed"
        ] is True
        assert init_calls == [trade]


class TestSPRTWiring:
    """Verify SPRT is called automatically on trade exit."""

    def test_finalize_exit_calls_sprt_update(self, tmp_path):
        from unittest.mock import MagicMock, patch
        from src.components.sprt_monitor import SPRTMonitor, SPRTResult, CUSUMResult

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._trade_entry_price = 3000.0
        orch._trade_entry_time = datetime(2026, 4, 11, 7, 30, tzinfo=timezone.utc)
        orch._trade_direction = "LONG"
        orch._trade_sl_distance = 10.0
        orch._last_tick_price = 3015.0  # Winner: +1.5R
        orch._mfe_price = 3020.0
        orch._mae_price = 2998.0
        orch._active_trade_record = {"decision_pipeline": {}}
        orch.config = {"trade_capture": {"base_path": str(tmp_path)}}

        # Mock SPRT monitor
        mock_sprt = MagicMock(spec=SPRTMonitor)
        mock_sprt.update_all.return_value = (
            SPRTResult("XAUUSD", "CONTINUE", 0.55, 2.77, -1.56, 1, 1, 0),
            CUSUMResult("XAUUSD", False, False, 0.38, 0.0),
        )
        orch._sprt_monitor = mock_sprt

        # Mock trade record save
        with patch("src.components.orchestrator.update_exit"), \
             patch("src.components.orchestrator.save_trade_record"):
            trade_snapshot = SimpleNamespace(
                partial_close_events=[],
                initial_volume=0.1,
            )
            orch._finalize_exit(trade_snapshot, "tp1_hit")

        # SPRT should have been called with won=True (price went up for LONG)
        mock_sprt.update_all.assert_called_once_with("XAUUSD", True)

    def test_sprt_error_does_not_crash_exit(self, tmp_path):
        from unittest.mock import MagicMock, patch

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._trade_entry_price = 3000.0
        orch._trade_entry_time = datetime(2026, 4, 11, 7, 30, tzinfo=timezone.utc)
        orch._trade_direction = "LONG"
        orch._trade_sl_distance = 10.0
        orch._last_tick_price = 2990.0  # Loser
        orch._mfe_price = 3005.0
        orch._mae_price = 2988.0
        orch._active_trade_record = {"decision_pipeline": {}}
        orch.config = {"trade_capture": {"base_path": str(tmp_path)}}

        mock_sprt = MagicMock()
        mock_sprt.update_all.side_effect = Exception("disk full")
        orch._sprt_monitor = mock_sprt

        with patch("src.components.orchestrator.update_exit"), \
             patch("src.components.orchestrator.save_trade_record"):
            trade_snapshot = SimpleNamespace(
                partial_close_events=[],
                initial_volume=0.1,
            )
            # Should not raise
            orch._finalize_exit(trade_snapshot, "sl_hit")


class TestPendingIntentPersistence:
    """Crash-recovery persistence for ExecutionEngine.pending_intent.

    pending_intent lives on ExecutionEngine (not SessionOrchestrator), but
    the orchestrator drives the limit-order lifecycle via self.execution.
    These tests exercise the pkl-based persistence contract from handoff 18.
    """

    @pytest.fixture(autouse=True)
    def _tmp_meta_dir(self, tmp_path, monkeypatch):
        # Redirect persistence to a temp dir so tests never touch real state.
        from src.components import execution as exec_mod
        monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path))
        self.tmp_path = tmp_path
        yield

    def _make_engine(self, symbol="XAUUSD"):
        from unittest.mock import MagicMock
        from src.components.execution import ExecutionEngine
        mt5 = MagicMock()
        mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0)
        config = {
            "market": {
                "symbol": symbol,
                "kill_zones": {
                    "london": {"start_utc": "07:00", "end_utc": "10:30"},
                    "ny": {"start_utc": "13:00", "end_utc": "15:30"},
                },
            },
            "risk": {"risk_per_trade_pct": 1.0},
        }
        return ExecutionEngine(mt5, config)

    def _make_params(self):
        return {
            "direction": "LONG", "entry_price": 4421.39,
            "stop_loss": 4401.99, "take_profit_1": 4450.49,
            "take_profit_2": 0.0, "take_profit_3": 0.0,
            "risk_reward_ratio": 1.5,
        }

    def test_pending_intent_persists_across_instances(self):
        """Set intent on engine A, create engine B, verify state was loaded."""
        engine_a = self._make_engine()
        intent = engine_a.set_limit_intent(self._make_params(), account_balance=100_000.0)
        assert engine_a.pending_intent is intent

        # New engine simulates a process restart — should load from disk
        engine_b = self._make_engine()
        assert engine_b.pending_intent is not None
        assert engine_b.pending_intent.direction == "LONG"
        assert engine_b.pending_intent.limit_price == 4421.39
        assert engine_b.pending_intent.stop_loss == 4401.99
        assert engine_b.pending_intent.trade_id == intent.trade_id

    def test_pending_intent_clears_deletes_file(self):
        """Setting pending_intent to None must remove the on-disk pkl."""
        engine = self._make_engine()
        engine.set_limit_intent(self._make_params(), account_balance=100_000.0)
        pkl = Path(engine._pending_intent_path)
        assert pkl.exists()

        engine.cancel_limit_intent("test")
        assert engine.pending_intent is None
        assert not pkl.exists()

    def test_pending_intent_stale_discarded(self):
        """An intent older than 24h must be discarded on load, file deleted."""
        import pickle
        from src.components.execution import PendingLimitIntent

        engine = self._make_engine()
        old_time = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        stale = PendingLimitIntent(
            direction="LONG", limit_price=4421.39, stop_loss=4401.99,
            take_profit_1=4450.49, risk_pct=1.0, trade_id="lim_stale",
            placed_time=old_time,
        )
        pkl = Path(engine._pending_intent_path)
        pkl.parent.mkdir(parents=True, exist_ok=True)
        with open(pkl, "wb") as f:
            pickle.dump(stale, f)

        # New engine boot should discard and delete the stale file
        fresh = self._make_engine()
        assert fresh.pending_intent is None
        assert not pkl.exists()

    def test_pending_intent_stale_before_first_kz_discarded(self, monkeypatch):
        """Intent placed yesterday (before today's first KZ) must be discarded.

        Deterministic via module-ref monkeypatch of ``datetime`` in
        ``src.components.execution``.  Production reads ``datetime.now(tz)``
        at _load_pending_intent() line ~257; we freeze that call to a fixed
        UTC instant so the "previous UTC day" branch is always exercised,
        regardless of the wall-clock time the suite runs at.

        Historical flake window (pre-fix): any run where wall-clock UTC hour
        was in [20, 24) would compute ``placed_dt = now - 20h`` on the SAME
        UTC date as ``now``; production staleness check #2 requires
        ``placed_dt.date() < now.date()`` so it did NOT discard, and the
        assertion ``fresh.pending_intent is None`` failed.  The in-test
        ``today_seven`` skip guard did not catch this window.
        """
        import pickle
        from datetime import datetime as _real_datetime
        from src.components import execution as _exec_mod
        from src.components.execution import PendingLimitIntent

        # Freeze "now" to a fixed UTC instant that is unambiguously AFTER
        # today's first KZ start (07:00 UTC) and leaves plenty of headroom
        # for "placed_dt = fixed_now - 20h" to land on the previous UTC
        # date.  14:00 UTC on 2026-04-22 -> placed_dt = 18:00 UTC on
        # 2026-04-21, which is:
        #   - within 24h of fixed_now (staleness check #1 does NOT fire)
        #   - strictly before today's 07:00 UTC first-KZ start
        #   - on a strictly earlier UTC date
        # so staleness check #2 (previous-UTC-day + before-first-KZ) must
        # fire and the intent must be discarded.
        fixed_now = _real_datetime(2026, 4, 22, 14, 0, 0, tzinfo=timezone.utc)

        class _FrozenDatetime(_real_datetime):
            """datetime subclass whose .now() returns fixed_now.

            Subclassing (not wrapping) preserves isinstance() checks and
            ``datetime.fromisoformat``, ``datetime.timedelta`` arithmetic,
            and every other classmethod the production code uses.
            """

            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                if tz is None:
                    return fixed_now.replace(tzinfo=None)
                return fixed_now.astimezone(tz)

            @classmethod
            def utcnow(cls):  # type: ignore[override]
                return fixed_now.replace(tzinfo=None)

        monkeypatch.setattr(_exec_mod, "datetime", _FrozenDatetime)

        engine = self._make_engine()
        placed_dt = fixed_now - timedelta(hours=20)

        stale = PendingLimitIntent(
            direction="LONG", limit_price=4421.39, stop_loss=4401.99,
            take_profit_1=4450.49, risk_pct=1.0, trade_id="lim_yesterday",
            placed_time=placed_dt.isoformat(),
        )
        pkl = Path(engine._pending_intent_path)
        pkl.parent.mkdir(parents=True, exist_ok=True)
        with open(pkl, "wb") as f:
            pickle.dump(stale, f)

        fresh = self._make_engine()
        assert fresh.pending_intent is None
        assert not pkl.exists()

    def test_pending_intent_corrupt_file_discarded(self, caplog):
        """Garbage bytes -> log warning, delete file, start clean."""
        engine = self._make_engine()
        pkl = Path(engine._pending_intent_path)
        pkl.parent.mkdir(parents=True, exist_ok=True)
        pkl.write_bytes(b"this is not valid pickle data \x00\x01\x02")

        import logging as _logging
        with caplog.at_level(_logging.WARNING, logger="src.components.execution"):
            fresh = self._make_engine()

        assert fresh.pending_intent is None
        assert not pkl.exists()
        assert any("Corrupt pending_intent" in r.message for r in caplog.records)

    def test_pending_intent_atomic_write_no_partial_file(self):
        """Save path must not leave a .tmp file behind after a successful write."""
        engine = self._make_engine()
        engine.set_limit_intent(self._make_params(), account_balance=100_000.0)
        tmps = list(self.tmp_path.glob("pending_intent_*.tmp"))
        assert tmps == [], f"unexpected tmp files left: {tmps}"

    def test_pending_intent_symbol_isolation(self):
        """Two engines with different symbols must not share persisted state."""
        gold = self._make_engine("XAUUSD")
        gold.set_limit_intent(self._make_params(), account_balance=100_000.0)
        assert gold.pending_intent is not None

        us30 = self._make_engine("US30_cash")
        # US30 has no intent on disk -> starts clean
        assert us30.pending_intent is None

        # Gold's file still exists
        assert Path(gold._pending_intent_path).exists()

    # ------------------------------------------------------------------
    # Handoff 19: schema_version guard + orphan .tmp cleanup
    # ------------------------------------------------------------------

    def test_pending_intent_schema_version_roundtrip(self):
        """A freshly-written intent has schema_version=1 and reloads cleanly."""
        from src.components.execution import PendingLimitIntent

        engine_a = self._make_engine()
        intent = engine_a.set_limit_intent(self._make_params(), account_balance=100_000.0)
        assert isinstance(intent, PendingLimitIntent)
        assert getattr(intent, "schema_version", None) == 1

        engine_b = self._make_engine()
        assert engine_b.pending_intent is not None
        assert engine_b.pending_intent.schema_version == 1

    def test_pending_intent_schema_version_mismatch_discarded(self, caplog):
        """A pickle whose schema_version != 1 must be discarded on load."""
        import pickle
        from src.components.execution import PendingLimitIntent

        engine = self._make_engine()
        now_iso = datetime.now(timezone.utc).isoformat()
        wrong = PendingLimitIntent(
            direction="LONG", limit_price=4421.39, stop_loss=4401.99,
            take_profit_1=4450.49, risk_pct=1.0, trade_id="lim_badver",
            placed_time=now_iso,
        )
        # Force an unsupported schema_version on the pickled intent.
        wrong.schema_version = 99  # type: ignore[assignment]
        pkl = Path(engine._pending_intent_path)
        pkl.parent.mkdir(parents=True, exist_ok=True)
        with open(pkl, "wb") as f:
            pickle.dump(wrong, f)

        import logging as _logging
        with caplog.at_level(_logging.WARNING, logger="src.components.execution"):
            fresh = self._make_engine()

        assert fresh.pending_intent is None
        assert not pkl.exists()
        assert any("schema version mismatch" in r.message for r in caplog.records)

    def test_pending_intent_orphan_tmp_cleanup_on_init(self):
        """Orphan .{pid}.tmp files left by a crashed save are swept at boot."""
        # Seed the dir with two orphan tmp files BEFORE the engine is created.
        orphan1 = self.tmp_path / "pending_intent_XAUUSD.1234.tmp"
        orphan2 = self.tmp_path / "pending_intent_US30.5678.tmp"
        orphan1.write_bytes(b"orphan-1")
        orphan2.write_bytes(b"orphan-2")
        assert orphan1.exists() and orphan2.exists()

        # Creating the engine runs _load_pending_intent which sweeps tmps.
        engine = self._make_engine()
        assert engine.pending_intent is None
        assert not orphan1.exists(), "orphan tmp #1 must be cleaned on init"
        assert not orphan2.exists(), "orphan tmp #2 must be cleaned on init"


class TestGracefulShutdownMarker:
    """Regression coverage for the 2026-04-30 live bug where the marker's
    ``valid_until_utc`` was hardcoded to the next dead-zone exit (23:45 UTC),
    suppressing watchdog respawn for ~24h whenever an orch shut down between
    KZs (e.g. 23:46 UTC graceful shutdown after end-of-NY → next valid KZ for
    Tokyo orchs at 00:00 UTC arrived 14 min later, but watchdog skipped
    respawn for the entire next trading day). Fix caps ``valid_until`` at
    ``min(next_dead_zone_exit, next_kz_start − 2min)``.
    """

    def _make_orch(self, symbol="XAUUSD", with_tokyo=False):
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = symbol
        windows = {
            "london": {
                "start_min": 7 * 60,             # 07:00 UTC
                "end_min": 10 * 60 + 30,         # 10:30 UTC
                "core_end_min": 9 * 60,
                "crosses_midnight": False,
            },
            "ny": {
                "start_min": 13 * 60,            # 13:00 UTC
                "end_min": 17 * 60,              # 17:00 UTC
                "core_end_min": 17 * 60,
                "crosses_midnight": False,
            },
        }
        if with_tokyo:
            windows["tokyo"] = {
                "start_min": 0,                  # 00:00 UTC
                "end_min": 3 * 60,               # 03:00 UTC
                "core_end_min": 3 * 60,
                "crosses_midnight": False,
            }
        orch._kz_windows = windows
        return orch

    def _read_marker(self, tmp_path, symbol):
        path = tmp_path / "pipeline_state" / f".orch_shutdown_{symbol}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_kz_upcoming_today_caps_valid_until_at_kz_start_minus_buffer(
        self, tmp_path, monkeypatch,
    ):
        """LIVE-BUG REGRESSION. Shutdown at 23:46 UTC with Tokyo at 00:00 UTC.
        Pre-fix: marker valid_until = 23:45 UTC tomorrow (suppressed all day).
        Post-fix: marker valid_until = 23:58 UTC (00:00 − 2min buffer)."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="USDJPY", with_tokyo=True)
        shutdown_at = datetime(2026, 4, 29, 23, 46, 10, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "USDJPY")
        valid_until = datetime.fromisoformat(marker["valid_until_utc"])
        # Tokyo starts at 00:00 UTC tomorrow → valid_until = 23:58 UTC today.
        assert valid_until == datetime(2026, 4, 29, 23, 58, tzinfo=timezone.utc)
        assert marker["next_kz_start_utc"] is not None

    def test_between_london_and_ny_caps_at_ny_start(self, tmp_path, monkeypatch):
        """Shutdown at 11:00 UTC (after London end) → marker valid until
        12:58 UTC (NY 13:00 − 2min)."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="XAUUSD")
        shutdown_at = datetime(2026, 4, 30, 11, 0, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "XAUUSD")
        valid_until = datetime.fromisoformat(marker["valid_until_utc"])
        assert valid_until == datetime(2026, 4, 30, 12, 58, tzinfo=timezone.utc)

    def test_post_ny_caps_at_tomorrows_first_kz(
        self, tmp_path, monkeypatch,
    ):
        """Shutdown at 17:30 UTC (post-NY, no more KZs today) → lookahead
        finds tomorrow's London at 07:00 UTC; valid_until = 06:58 UTC tomorrow.

        This is critical: a 17:30 UTC shutdown must NOT pin valid_until to
        23:45 UTC same day (next dead-zone exit) — tomorrow's London is
        sooner, and we need the watchdog to respawn before then."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="XAUUSD")
        shutdown_at = datetime(2026, 4, 30, 17, 30, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "XAUUSD")
        valid_until = datetime.fromisoformat(marker["valid_until_utc"])
        assert valid_until == datetime(2026, 5, 1, 6, 58, tzinfo=timezone.utc)
        next_kz = datetime.fromisoformat(marker["next_kz_start_utc"])
        assert next_kz == datetime(2026, 5, 1, 7, 0, tzinfo=timezone.utc)

    def test_post_2345_caps_at_tomorrows_first_kz(
        self, tmp_path, monkeypatch,
    ):
        """Shutdown at 23:50 UTC with no Tokyo configured → tomorrow's
        London 07:00 UTC drives the cap; valid_until = 06:58 UTC tomorrow.

        Pre-fix and naive lookahead: would have used today's 23:45 UTC
        which is in the past, OR tomorrow's 23:45 UTC dead-zone exit (24h
        away). Both wrong."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="XAUUSD")
        shutdown_at = datetime(2026, 4, 30, 23, 50, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "XAUUSD")
        valid_until = datetime.fromisoformat(marker["valid_until_utc"])
        assert valid_until == datetime(2026, 5, 1, 6, 58, tzinfo=timezone.utc)

    def test_no_kz_configured_falls_back_to_dead_zone_exit(
        self, tmp_path, monkeypatch,
    ):
        """Edge case: orch with no KZs at all (theoretical — every live
        instrument has at least 1) → fallback to next dead-zone exit."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="XAUUSD")
        orch._kz_windows = {}  # no KZs at all
        shutdown_at = datetime(2026, 4, 30, 11, 0, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "XAUUSD")
        valid_until = datetime.fromisoformat(marker["valid_until_utc"])
        assert valid_until == datetime(2026, 4, 30, 23, 45, tzinfo=timezone.utc)
        assert marker["next_kz_start_utc"] is None

    def test_marker_payload_shape(self, tmp_path, monkeypatch):
        """Marker payload contains the expected keys for watchdog + diagnostics."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="GBPJPY", with_tokyo=True)
        shutdown_at = datetime(2026, 4, 30, 11, 0, tzinfo=timezone.utc)

        orch._write_graceful_shutdown_marker(now=shutdown_at)

        marker = self._read_marker(tmp_path, "GBPJPY")
        assert marker["symbol"] == "GBPJPY"
        assert marker["reason"] == "all_kill_zones_complete_no_active_trade"
        assert marker["shutdown_at_utc"] == shutdown_at.isoformat()
        assert "valid_until_utc" in marker
        assert "next_kz_start_utc" in marker

    def test_no_now_arg_uses_real_clock(self, tmp_path, monkeypatch):
        """Production callers pass no `now` → method falls through to
        datetime.now(timezone.utc); the marker still writes successfully."""
        monkeypatch.chdir(tmp_path)
        orch = self._make_orch(symbol="XAUUSD")

        orch._write_graceful_shutdown_marker()  # no `now` argument

        marker = self._read_marker(tmp_path, "XAUUSD")
        # Just sanity-check the marker exists and has a parseable timestamp;
        # exact value depends on wall-clock and is not asserted here.
        assert datetime.fromisoformat(marker["shutdown_at_utc"])
        assert datetime.fromisoformat(marker["valid_until_utc"])
