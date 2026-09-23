from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.poi_state_contract import finalize_poi_state, stable_poi_id
from src.components import concurrent_tracker as _ct
from src.components import orchestrator as orch_mod
from src.components.gtos_vnext_runtime import (
    GTOSVNextPropSafeSelectorDecision,
    GTOSVNextRuntimeDecision,
)
from src.components.live_decision_packet_v4 import (
    REQUIRED_FIELD_GROUPS as LIVE_DECISION_PACKET_V4_REQUIRED_GROUPS,
    validate_live_decision_packet_v4,
)
from src.components.orchestrator import SessionOrchestrator
from src.components.verification import VerificationResult
from src.mt5.mt5_interface import MAGIC_NUMBER


def _allowlist(path: Path, *, proof_class: str | None = None) -> Path:
    path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "partial_be_runner",
                        "proof_class": proof_class
                        or "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _config(tmp_path: Path, *, allowlist_path: Path, eligible_symbols=None, trade_capture=False):
    return {
        "deployment": {"phase": 3},
        "trading_enabled": True,
        "broker_profile": {
            "broker": "FTMO",
            "server": "FTMO-Server3",
            "broker_account_namespace": "operator_profile",
        },
        "market": {
            "symbol": "XAUUSD",
            "mt5_symbol": "XAUUSD",
            # The real execution caller supplies a fresh MT5 symbol-info
            # snapshot. This permission-stage fixture supplies the same
            # minimum geometry through its read-only market mapping.
            "point": 0.01,
            "trade_tick_size": 0.01,
            "trade_tick_value": 1.0,
            "trade_contract_size": 100.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "trade_stops_level": 0,
            "trade_freeze_level": 0,
            "trade_mode": 4,
            "swap_long": -74.12,
            "swap_short": -23.55,
            "swap_mode": 1,
            "swap_rollover3days": 3,
            "kill_zones": {
                "london": {"start_utc": "07:00", "end_utc": "10:30", "core_end_utc": "09:30"},
                "ny": {"start_utc": "13:00", "end_utc": "17:00", "core_end_utc": "17:00"},
            },
        },
        "risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_portfolio_drawdown_pct": 4.0,
            "max_consecutive_losses": 5,
            "min_rr": 1.5,
            "sl_absolute_min": 0.1,
            "max_spread_cents": 1000,
            "max_trades_per_kill_zone_enabled": False,
        },
        "trade_capture": {
            "enabled": trade_capture,
            "base_path": str(tmp_path / "records"),
            "save_mso": False,
            "save_prompt": False,
            "save_rejected": True,
        },
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "production_replacement_vnext_moonshot",
            "apply_to_execution": True,
            "moonshot_broader_origin_live_generation_enabled": True,
            "moonshot_broader_origin_execute_pre_ai_pre_l2": True,
            "moonshot_broader_origin_cross_asset_fetch_enabled": False,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": (
                eligible_symbols or ["XAUUSD"]
            ),
            "moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols": [],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist_path),
            "moonshot_dynamic_execution_router_broader_origin_min_group_rows": 20,
            "moonshot_dynamic_execution_router_require_configured_kill_zone": True,
            "decision_log_path": str(tmp_path / "gtos_vnext_runtime_decisions.jsonl"),
            "replacement_monitoring_log_path": str(
                tmp_path / "gtos_vnext_replacement_monitoring.jsonl"
            ),
            "moonshot_dynamic_execution_router_be_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_be_final_target_r": 1.5,
            "moonshot_dynamic_execution_router_partial_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
            "moonshot_dynamic_execution_router_momentum_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_momentum_final_target_r": 2.0,
            "moonshot_dynamic_execution_router_momentum_pullback_r": 0.4,
            "pending_policy_enabled": True,
            "ltf_path_execution_enabled": True,
            "ltf_path_execution_apply_to_execution": False,
            "prop_safe_selector_enabled": True,
            "prop_safe_selector_apply_to_execution": True,
            "prop_safe_selector_initial_balance": 100000.0,
        },
    }


def _candidate(**overrides):
    base = {
        "candidate_id": "broadorigin_test",
        "origin_family": "liquidity_sweep_reclaim",
        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
        "framework": "origin_liquidity_sweep_reclaim",
        "symbol": "XAUUSD",
        "side": "LONG",
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 101.5,
        "risk_reward_ratio": 1.5,
        "probability": 0.70,
        "candidate_probability": 0.70,
        "ev_r": 0.27,
        "expected_net_r": 0.27,
        "source_completeness": 1.0,
        "candidate_decision_quality_field_sources": {
            "probability": "unit_fixture.predecision_probability",
            "ev_r": "unit_fixture.predecision_ev_r",
            "expected_net_r": "unit_fixture.predecision_expected_net_r",
            "source_completeness": "unit_fixture.predecision_source_completeness",
        },
        "candidate_decision_quality_source_boundary": (
            "predecision_unit_fixture_no_outcome_fields"
        ),
        "source_window_complete": True,
        "source_path_feature_status": "raw_data_m15_asof_complete",
        "live_generation_status": "generated_live_asof",
        "source_fields": {
            "sweep_direction": "swept_prior_20_low_reclaimed_above",
            "range_atr14": 1.2,
            "trend_state_20": "flat",
        },
        "session": "london",
        "route_session": "london",
        "session_bucket": "london",
        "kill_zone": "london",
        "candle_open_utc": "2026-05-26T07:00:00Z",
        "candle_close_utc": "2026-05-26T07:15:00Z",
        "timeframe": "M15",
        "market_timeframe": "M15",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 101.5,
            "risk_reward_ratio": 1.5,
            "gtos_vnext_probability": 0.70,
            "gtos_vnext_expected_value_r": 0.27,
            "gtos_vnext_candidate_ev_r": 0.27,
        },
    }
    base.update(overrides)
    if "trade_parameters" not in overrides:
        base["trade_parameters"] = {
            "direction": base["direction"],
            "entry_price": base["entry_price"],
            "stop_loss": base["stop_loss"],
            "take_profit_1": base["take_profit_1"],
            "risk_reward_ratio": base["risk_reward_ratio"],
            "gtos_vnext_probability": base["probability"],
            "gtos_vnext_expected_value_r": base["ev_r"],
            "gtos_vnext_candidate_ev_r": base["ev_r"],
        }
    return base


class _FakeMT5:
    def __init__(self, *, equity=100000.0):
        self.equity = equity

    def is_connected(self):
        return True

    def get_tick(self, symbol):
        return SimpleNamespace(
            bid=99.99,
            ask=100.0,
            spread_cents=1.0,
        )

    def get_positions(self, symbol=None):
        return []

    def get_account_equity(self):
        return self.equity

    def get_account_balance(self):
        return self.equity

    def get_candles(self, symbol, timeframe, count):
        return []


class _FakeExecution:
    def __init__(self):
        self.pending_intent = None
        self.active_trade = None
        self.open_trade_calls = []
        self.set_limit_calls = []

    def open_trade(self, **kwargs):
        self.open_trade_calls.append(kwargs)
        return SimpleNamespace(
            trade_id="market_1",
            ticket=1001,
            direction=kwargs["trade_params"]["direction"],
            entry_price=kwargs["trade_params"]["entry_price"],
            stop_loss=kwargs["trade_params"]["stop_loss"],
            take_profit_1=kwargs["trade_params"]["take_profit_1"],
        )

    def set_limit_intent(self, **kwargs):
        self.set_limit_calls.append(kwargs)
        return SimpleNamespace(
            trade_id="limit_1",
            direction=kwargs["trade_params"]["direction"],
            limit_price=kwargs["trade_params"]["entry_price"],
            stop_loss=kwargs["trade_params"]["stop_loss"],
            take_profit_1=kwargs["trade_params"]["take_profit_1"],
            expiry_candles=4,
            pending_order_mode="local",
            broker_pending_order_created=False,
            mt5_order_ticket=None,
            native_pending_order_type=None,
        )


def _saved_trade_records(tmp_path: Path):
    return sorted(
        path
        for path in (tmp_path / "records" / "XAUUSD").glob("*.json")
        if path.name != "_pending_records_index.json"
    )


def _orchestrator(tmp_path: Path, config: dict, *, equity=100000.0):
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = config
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    orch.mt5 = _FakeMT5(equity=equity)
    orch.execution = _FakeExecution()
    orch.session_state = {
        "date": "2026-05-26",
        "trades_today": 0,
        "daily_pnl_pct": 0.0,
        "portfolio_drawdown_pct": 0.0,
        "consecutive_losses": 0,
        "start_equity": 100000.0,
        "start_balance": 100000.0,
        "current_kill_zone": None,
        "trades_london": 0,
    }
    orch._drawdown_mgr = SimpleNamespace(get_risk_pct=lambda equity: 1.0)
    orch._pending_trade_record_path = None
    orch._active_trade_record_path = None
    orch._active_trade_record = None
    orch._ci_context_text = ""
    orch._data_incomplete_streak = 0
    orch._v3_runtime_package_cache = None
    orch._calendar = []
    orch._news_calendar = SimpleNamespace(enabled=False)
    orch._log_rows = []
    orch._log_candle = lambda *args, **kwargs: orch._log_rows.append((args, kwargs))
    orch._record_forward_capture_evaluation_shadow = lambda **kwargs: None
    orch._monitor_expired_poi_watches = lambda raw_data, kill_zone: None
    orch._init_trade_tracking = lambda trade_state: None
    orch._build_gtos_vnext_ltf_path_state = lambda **kwargs: {
        "source_complete": True,
        "same_bar_ambiguous": False,
        "path_source_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
    }
    orch._apply_autocorrelation_risk_sizing = (
        lambda current_risk_pct, raw_data, record: SimpleNamespace(
            after_risk_pct=current_risk_pct,
            applied=False,
        )
    )
    orch._apply_gtos_vnext_risk_adjustment = (
        lambda current_risk_pct, vnext_decision, record: SimpleNamespace(
            after_risk_pct=current_risk_pct,
            applied=False,
        )
    )
    orch._get_open_positions_for_correlation = lambda: []
    return orch


def test_broader_origin_moonshot_context_marks_runtime_kill_zone_configured(tmp_path):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    orch = _orchestrator(tmp_path, _config(tmp_path, allowlist_path=allowlist))

    context = orch._vnext_broader_origin_moonshot_context(
        candidate=_candidate(),
        kill_zone="london",
        prop_selector=SimpleNamespace(action="ALLOW"),
        analysis=SimpleNamespace(
            trade_parameters=SimpleNamespace(entry_price=100.0, stop_loss=99.0)
        ),
    )

    assert context["kill_zone_position"] == "in_london_runtime_configured_kill_zone"


def test_broader_origin_record_identity_is_candidate_unique(tmp_path):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    orch = _orchestrator(
        tmp_path,
        _config(tmp_path, allowlist_path=allowlist, trade_capture=True),
    )
    orch._refresh_vnext_candidate_intelligence_packet = lambda *args, **kwargs: None
    candidate = _candidate(candidate_id="broadorigin_unique_123")
    analysis = SimpleNamespace(
        model_dump=lambda mode="json": {
            "decision": "CANDIDATE",
            "confidence_score": 100,
            "framework": candidate["framework"],
            "reasoning": {"setup_grade": "A+"},
            "trade_parameters": candidate["trade_parameters"],
        }
    )

    record = orch._create_vnext_broader_origin_record(
        candidate=candidate,
        analysis=analysis,
        raw_data={"candle_close_utc": candidate["candle_close_utc"]},
        mso={},
        kill_zone="london",
    )

    assert record["metadata"]["candidate_id"] == "broadorigin_unique_123"
    assert record["metadata"]["parent_candle_trade_id"] == "XAUUSD_2026-05-26_london_0715"
    assert record["metadata"]["trade_id"] == (
        "XAUUSD_2026-05-26_london_0715_broadorigin_unique_123"
    )


def test_synthetic_broader_origin_analysis_preserves_atomic_poi_state():
    source_times = [
        "2026-05-26T06:15:00+00:00",
        "2026-05-26T06:30:00+00:00",
        "2026-05-26T06:45:00+00:00",
    ]
    poi_state = finalize_poi_state(
        {
            "poi_id": stable_poi_id(
                symbol="XAUUSD",
                timeframe="M15",
                poi_type="fair_value_gap",
                direction="bullish",
                source_candle_times=source_times,
                zone_low=99.5,
                zone_high=100.0,
            ),
            "poi_type": "fair_value_gap",
            "poi_timeframe": "M15",
            "poi_direction": "bullish",
            "poi_zone_low": 99.5,
            "poi_zone_high": 100.0,
            "poi_source_candle_times": source_times,
            "poi_created_at_utc": "2026-05-26T07:00:00+00:00",
            "poi_state_asof_utc": "2026-05-26T07:15:00+00:00",
            "poi_age_hours": 0.25,
            "poi_touch_count": 0,
            "poi_first_touch_time_utc": "",
            "poi_last_touch_time_utc": "",
            "poi_mitigation_status": "untouched",
            "poi_filled": False,
            "poi_invalidated": False,
            "poi_invalidation_time_utc": "",
            "poi_invalidation_reason": "",
            "poi_state_uses_outcome_fields": False,
        }
    )
    candidate = _candidate(
        origin_family="current_fvg_fill",
        candidate_origin_family="origin_current_fvg_fill",
        framework="fvg_fill",
        current_framework="fvg_fill",
        poi_state=poi_state,
        poi_id=poi_state["poi_id"],
        poi_state_hash_sha256=poi_state["poi_state_hash_sha256"],
        source_fields={
            "current_framework": "fvg_fill",
            "poi_state": poi_state,
            "poi_id": poi_state["poi_id"],
            "poi_state_hash_sha256": poi_state["poi_state_hash_sha256"],
        },
    )

    analysis = orch_mod._make_synthetic_moonshot_analysis(candidate)
    trade_params = analysis.trade_parameters

    assert trade_params.poi_id == poi_state["poi_id"]
    assert trade_params.poi_state_hash_sha256 == poi_state["poi_state_hash_sha256"]
    assert trade_params.poi_state == poi_state
    assert trade_params.source_fields["poi_state"] == poi_state


@pytest.fixture(autouse=True)
def _stable_risk(monkeypatch):
    _ct.reset_cache()
    monkeypatch.setattr(
        orch_mod,
        "check_correlation_risk",
        lambda **kwargs: SimpleNamespace(final_risk_pct=kwargs["base_risk_pct"], adjusted=False),
    )
    monkeypatch.setattr(
        orch_mod,
        "_evaluate_cross_instrument_correlation",
        lambda **kwargs: SimpleNamespace(action="ALLOW", correlated_positions=[], threshold=0.4),
    )
    monkeypatch.setattr(orch_mod, "should_block_trading", lambda *args, **kwargs: (False, ""))
    yield
    _ct.reset_cache()


def test_broader_origin_process_candle_executes_without_primary_analyzer_or_old_l2(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    orch = _orchestrator(tmp_path, config)
    raw_data = {
        "symbol": "XAUUSD",
        "candle_close_utc": "2026-05-26T07:15:00Z",
        "candles": {"M15": []},
    }
    mso = SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z")
    monkeypatch.setattr(orch_mod, "compute_market_state", lambda raw, cfg: mso)
    monkeypatch.setattr(orch_mod, "prescreen_mso", lambda _mso: (True, "ok"))
    monkeypatch.setattr(
        orch_mod,
        "verify_candidate",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("old L2 called")),
    )
    monkeypatch.setattr(
        orch_mod,
        "generate_live_broader_origin_candidates",
        lambda **kwargs: [_candidate()],
    )
    orch.analyzer = SimpleNamespace(
        analyze=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("PrimaryAnalyzer called")
        )
    )
    orch._update_daily_pnl = lambda: None
    orch._check_kill_zone_trade_cap = lambda kill_zone: False
    orch._check_and_trigger_daily_loss_stop = lambda kill_zone: False
    orch._check_sprt_class_halt_gate = lambda kill_zone: False
    orch._should_skip_first_ny_candle = lambda kill_zone: False
    orch._ingest_live_data_with_reconnect = lambda kill_zone: raw_data

    orch._process_candle("london")

    assert orch.execution.set_limit_calls
    trade_params = orch.execution.set_limit_calls[0]["trade_params"]
    assert trade_params["gtos_vnext_dynamic_policy_selected"] == "partial_be_runner"
    assert trade_params["gtos_vnext_dynamic_policy_applied"] is True
    assert trade_params["gtos_vnext_prop_safe_selector_action"] == "ALLOW"
    assert trade_params["gtos_vnext_prop_safe_selector_reason"]
    assert trade_params["gtos_vnext_pretrade_cost_model"]["status"] == "PASSED"
    assert trade_params["gtos_vnext_prop_firm_headroom_snapshot_v4"][
        "schema_version"
    ] == "prop_firm_headroom_snapshot_v4"
    assert trade_params["gtos_vnext_prop_firm_headroom_snapshot_v4"][
        "source_status"
    ] == "source_bound_broker_real_account_headroom"
    telemetry = orch.execution.set_limit_calls[0]["telemetry_context"]
    assert telemetry["gtos_vnext_dynamic_policy_selected"] == "partial_be_runner"
    assert telemetry["gtos_vnext_dynamic_policy_applied"] is True
    assert telemetry["gtos_vnext_dynamic_policy_replaced_policy"] == "retired_static_baseline_comparator"
    saved = _saved_trade_records(tmp_path)
    assert saved, "broader-origin execution must write the normal trade-record surface"


@pytest.mark.parametrize(
    "runtime_override",
    [
        {"enabled": False},
        {"apply_to_execution": False},
        {"moonshot_broader_origin_live_generation_enabled": False},
        {"moonshot_broader_origin_execute_pre_ai_pre_l2": False},
        {"moonshot_dynamic_execution_router_enabled": False},
        {"moonshot_dynamic_execution_router_apply_to_execution": False},
    ],
)
def test_broader_origin_pre_ai_path_honors_activation_flags(
    tmp_path,
    monkeypatch,
    runtime_override,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    config["gtos_vnext_runtime"].update(runtime_override)
    orch = _orchestrator(tmp_path, config)

    def fail_generation(**kwargs):
        raise AssertionError("broader-origin generator must not run when flag is disabled")

    monkeypatch.setattr(orch_mod, "generate_live_broader_origin_candidates", fail_generation)
    consumed = orch._process_vnext_broader_origin_candidates(
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z"},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert consumed is True
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    assert "old_primary_analyzer_l2_fallback" in str(orch._log_rows[-1])


def test_broader_origin_candidate_blocked_by_vnext_native_prescreen(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    monkeypatch.setattr(
        orch_mod,
        "generate_live_broader_origin_candidates",
        lambda **kwargs: [_candidate()],
    )
    monkeypatch.setattr(orch_mod, "prescreen_mso", lambda mso: (False, "no_valid_h1_poi"))

    consumed = orch._process_vnext_broader_origin_candidates(
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z"},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert consumed is True
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    assert orch._log_rows[-1][0][0] == "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED"
    assert orch._last_vnext_broader_origin_safety_gate_block["candidate_count"] == 1
    assert (
        orch._last_vnext_broader_origin_safety_gate_block["candidates"][0]["candidate_id"]
        == "broadorigin_test"
    )
    runtime_rows = [
        json.loads(line)
        for line in (tmp_path / "gtos_vnext_runtime_decisions.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    monitor_rows = [
        json.loads(line)
        for line in (tmp_path / "gtos_vnext_replacement_monitoring.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert runtime_rows[-1]["phase"] == "broader_origin_safety_gate_blocked"
    assert (
        runtime_rows[-1]["decision"]["evidence"]["final_outcome"]
        == "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED"
    )
    assert monitor_rows[-1]["snapshot"]["phase"] == "broader_origin_safety_gate_blocked"
    assert monitor_rows[-1]["snapshot"]["router_decision"]["post_l2_matched"] is True
    source_state = monitor_rows[-1]["snapshot"]["source_capture_completeness"]
    assert source_state["source_complete"] is False
    assert source_state["source_path_feature_status"] == (
        "raw_data_m15_missing_or_not_attached"
    )
    assert source_state["safety_gate_reason"] == (
        "vnext_broader_origin_prescreen:no_valid_h1_poi"
    )
    assert source_state["candidate_count"] == 1


def test_broader_origin_candidate_blocked_by_vnext_native_news_gate(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    orch._news_calendar = SimpleNamespace(
        enabled=True,
        should_skip=lambda symbol, current_time: (True, "high_impact_usd_news"),
    )
    monkeypatch.setattr(
        orch_mod,
        "generate_live_broader_origin_candidates",
        lambda **kwargs: [_candidate()],
    )
    monkeypatch.setattr(orch_mod, "prescreen_mso", lambda mso: (True, "ok"))

    consumed = orch._process_vnext_broader_origin_candidates(
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z"},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert consumed is True
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    assert orch._log_rows[-1][0][0] == "SKIP_GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED"
    monitor_rows = [
        json.loads(line)
        for line in (tmp_path / "gtos_vnext_replacement_monitoring.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert monitor_rows[-1]["snapshot"]["phase"] == "broader_origin_safety_gate_blocked"
    assert (
        monitor_rows[-1]["snapshot"]["router_decision"]["post_l2_reason"]
        == "vnext_broader_origin_news:high_impact_usd_news"
    )


def test_broader_origin_no_candidate_consumes_before_old_path(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    monkeypatch.setattr(
        orch_mod,
        "generate_live_broader_origin_candidates",
        lambda **kwargs: [],
    )

    consumed = orch._process_vnext_broader_origin_candidates(
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z"},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert consumed is True
    no_candidate = orch._last_vnext_broader_origin_no_candidate
    assert no_candidate["capture_mode"] == "native_live_no_candidate_writer"
    assert no_candidate["capture_reason"] == "live_process_no_candidate_packet_writer"
    assert no_candidate["symbol"] == "XAUUSD"
    assert no_candidate["broker_symbol"] == "XAUUSD"
    assert no_candidate["kill_zone"] == "london"
    assert no_candidate["candle_close_utc"] == "2026-05-26T07:15:00Z"
    assert no_candidate["candidate_count"] == 0
    assert no_candidate["old_primary_analyzer_called"] is False
    assert no_candidate["old_l2_required"] is False
    assert no_candidate["decision_path"] == (
        "vnext_broader_origin_no_candidate_consumed_before_old_primary_"
        "analyzer_and_l2"
    )
    runtime_rows = [
        json.loads(line)
        for line in (tmp_path / "gtos_vnext_runtime_decisions.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert runtime_rows[-1]["phase"] == "broader_origin_no_candidate"
    assert runtime_rows[-1]["decision"]["evidence"]["old_l2_required"] is False
    monitor_rows = [
        json.loads(line)
        for line in (tmp_path / "gtos_vnext_replacement_monitoring.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    source_state = monitor_rows[-1]["snapshot"]["source_capture_completeness"]
    assert source_state["source_complete"] is False
    assert source_state["source_path_feature_status"] == (
        "raw_data_m15_missing_or_not_attached"
    )
    assert source_state["no_candidate_reason"] == (
        "no_live_broader_origin_candidate_from_closed_m15_source_contract"
    )
    assert source_state["null_zero_reasons"]["m15_candles"] == (
        "no_m15_candles_in_raw_data_for_no_candidate_packet"
    )
    assert orch._log_rows[-1][0][0] == (
        "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_NO_CANDIDATE"
    )


def test_broader_origin_vnext_execution_block_is_projection_until_dynamic_source_backing(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    orch = _orchestrator(tmp_path, config)
    monkeypatch.setattr(
        orch_mod,
        "vnext_execution_block_reason",
        lambda decision, cfg: "vnext_source_component_avoid_veto",
    )

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z", "candles": {"M15": []}},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
    assert not orch.execution.open_trade_calls
    assert orch.execution.set_limit_calls
    saved = _saved_trade_records(tmp_path)
    assert saved
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    projection = record["decision_pipeline"][
        "gtos_vnext_pre_dynamic_execution_block_projection"
    ]
    assert projection == {
        "would_block": True,
        "reason": "vnext_source_component_avoid_veto",
        "terminal_authority": (
            "deferred_until_moonshot_dynamic_execution_and_geometry_repair"
        ),
    }
    assert record["instrumentation"][
        "gtos_vnext_pre_dynamic_execution_block_deferred"
    ] is True
    packet = record["decision_pipeline"]["gtos_vnext_candidate_intelligence_packet"]
    assert packet["final_order_decision"]["order_path"] == "pending_limit"


def test_broader_origin_zero_risk_after_vnext_sizing_prevents_order_placement(
    tmp_path,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    orch._apply_gtos_vnext_risk_adjustment = (
        lambda current_risk_pct, vnext_decision, record: SimpleNamespace(
            after_risk_pct=0.0,
            applied=True,
        )
    )

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z", "candles": {"M15": []}},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_ZERO_RISK"
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls


def test_broader_origin_repairs_gate1_geometry_before_terminal_rejection(
    tmp_path,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    config["risk"]["sl_absolute_min"] = 0.1
    orch = _orchestrator(tmp_path, config)
    candidate = _candidate(
        entry_price=100.0,
        stop_loss=99.95,
        take_profit_1=100.075,
        risk_reward_ratio=1.5,
        trade_parameters={
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 99.95,
            "take_profit_1": 100.075,
            "risk_reward_ratio": 1.5,
        },
        source_fields={
            "sweep_direction": "swept_prior_20_low_reclaimed_above",
            "atr14": 0.5,
            "range_atr14": 1.2,
            "trend_state_20": "flat",
        },
    )
    mso = SimpleNamespace(
        timestamp_utc="2026-05-26T07:15:00Z",
        timeframes={"M15": SimpleNamespace(atr_14=0.5)},
    )

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=candidate,
        raw_data={
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-26T07:15:00Z",
            "candles": {"M15": []},
        },
        mso=mso,
        kill_zone="london",
    )

    assert outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
    trade_params = orch.execution.set_limit_calls[0]["trade_params"]
    assert trade_params["stop_loss"] == pytest.approx(99.25)
    assert trade_params["take_profit_1"] == pytest.approx(102.25)
    assert trade_params["risk_reward_ratio"] == pytest.approx(3.0)
    assert trade_params["gtos_vnext_dynamic_policy_selected"] == "partial_be_runner"
    saved = _saved_trade_records(tmp_path)
    assert saved
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    repair = record["decision_pipeline"]["gtos_vnext_executable_geometry_repair"]
    assert repair["status"] == "repaired"
    assert "structural_atr_broker_stop_expansion" in repair["actions"]
    assert "dynamic_target_recomputed_from_repaired_risk" in repair["actions"]
    assert record["decision_pipeline"]["gate1_result"]["passed"] is True
    packet = record["decision_pipeline"]["gtos_vnext_candidate_intelligence_packet"]
    assert packet["candidate_identity"]["candidate_id"] == "broadorigin_test"
    assert packet["candidate_identity"]["broker_symbol"] == "XAUUSD"
    assert packet["geometry"]["repair_path"]["entered"] is True
    assert packet["geometry"]["repaired"]["geometry"]["stop_loss"] == pytest.approx(99.25)
    assert packet["gates"]["gate1_final_after_repair"]["ran_after_repair"] is True
    assert packet["dynamic_policy"]["selected_policy"] == "partial_be_runner"
    assert packet["dynamic_policy"]["execution_policy_id"] == (
        "vnext_exec_partial_50_at_1r_be_runner_to_3r"
    )
    assert packet["selected_cell_risk_proof"]["ran"] is True
    assert packet["risk_lot_calculation"]["lot_recompute"]["status"] in {
        "not_available",
        "computed",
        "failed",
        "failed_exception",
    }
    assert packet["prop_governor"]["after_geometry_repair"]["action"] == "ALLOW"
    assert packet["final_order_decision"]["order_path"] == "pending_limit"


def test_broader_origin_record_attaches_live_decision_packet_v4_and_jsonl(
    tmp_path,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    packet_log = tmp_path / "live_decision_packets_v4.jsonl"
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    config["gtos_vnext_runtime"]["live_decision_packet_v4_enabled"] = True
    config["gtos_vnext_runtime"]["live_decision_packet_v4_log_path"] = str(packet_log)
    orch = _orchestrator(tmp_path, config)

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-26T07:15:00Z",
            "candles": {"M15": []},
        },
        mso=SimpleNamespace(
            timestamp_utc="2026-05-26T07:15:00Z",
            timeframes={"M15": SimpleNamespace(atr_14=1.0)},
        ),
        kill_zone="london",
    )

    assert outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
    saved = _saved_trade_records(tmp_path)
    assert saved
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    packet = record["decision_pipeline"]["live_decision_packet_v4"]
    assert packet["schema_name"] == "LiveDecisionPacketV4"
    assert packet["capture_mode"] == "native_live_writer_capture_only"
    assert packet["broker_runtime_change_status"] is False
    assert packet["validation_result_status"] is False
    assert packet["outcome_result_rows_status"] is False
    assert all(value is False for value in packet["forbidden_surface_boundary"].values())
    assert set(LIVE_DECISION_PACKET_V4_REQUIRED_GROUPS).issubset(
        packet["field_groups"]
    )
    assert len(packet["source_event_hash_sha256"]) == 64
    assert len(packet["packet_hash_sha256"]) == 64
    assert packet["field_groups"]["source_window_hash_and_no_leak_contract"][
        "no_leak_status"
    ] == "PASS_PRE_DECISION_SOURCE_HASH_EXCLUDES_POST_DECISION_FIELDS"
    assert packet["field_groups"]["follow_avoid_mixed_numeric_confluence"][
        "permission_rule"
    ].startswith("FOLLOW_is_not_automatic_trade_permission")
    assert packet["field_groups"]["broker_dual_broker_local_truth"]["no_copy_rule"] == (
        "do_not_copy_redacted_account_lots_fills_cash_cost_specs_lifecycle_truth_to_FTMO"
    )
    runtime_contract = packet["runtime_evidence_contract"]
    assert "candidate_identity.candidate_id" in runtime_contract["duplicate_policy"]
    assert "future validation must freeze" in runtime_contract[
        "partition_holdout_requirements"
    ]
    assert "live_decision_packet_v4_enabled=false" in runtime_contract["rollback_path"]
    assert {
        row["group"]
        for row in packet["source_gap_rows"]
        if row["status"] in {"prospective_capture_required", "captured_incomplete"}
    } >= {
        "selector_allocator_final_say",
        "same_symbol_lifecycle_and_ticket_state",
        "probability_debate_numeric_theses",
        "follow_avoid_mixed_numeric_confluence",
        "feature_label_forward_capture_contract",
    }
    assert validate_live_decision_packet_v4(packet) == []
    rows = [
        json.loads(line)
        for line in packet_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    assert rows[-1]["packet_hash_sha256"] == packet["packet_hash_sha256"]


def test_selected_cell_no_exact_match_packet_carries_exact_refusal_proof():
    packet = SessionOrchestrator._vnext_selected_cell_risk_packet(
        {
            "selected_policy": "partial_be_runner",
            "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
            "router_record": {
                "route_dimensions": {
                    "selected_cell_risk_allowed": False,
                    "selected_cell_risk_required": True,
                    "selected_cell_risk_decision_basis": (
                        "no_exact_selected_cell_risk_match:session_or_hour_key_mismatch"
                    ),
                    "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
                    "selected_cell_risk_selected_policy": "partial_be_runner",
                    "selected_cell_risk_execution_policy_id": (
                        "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                    ),
                    "selected_cell_risk_policy_identity_status": (
                        "selected_policy_inherited_from_dynamic_router_record"
                    ),
                    "selected_cell_risk_source_ledger_path": "risk-ledger.jsonl",
                    "selected_cell_risk_capture_contract": {
                        "status": "exact_selected_cell_source_row_capture_required",
                        "source_ledger_path": "risk-ledger.jsonl",
                        "required_join_keys": [
                            "symbol",
                            "side",
                            "selected_policy",
                        ],
                    },
                }
            },
            "source_event": {
                "selected_cell_risk_refusal_cause": "session_or_hour_key_mismatch",
                "selected_cell_risk_failed_dimensions": [
                    {
                        "field": "route_session",
                        "live": ["moonshot_h22_23"],
                        "risk_row": "london",
                    }
                ],
                "selected_cell_risk_nearest_candidate": {
                    "risk_cell_id": "risk-london-session-only",
                    "route_session": "london",
                },
                "selected_cell_risk_unresolved_reasons": [
                    "session_or_hour_key_mismatch"
                ],
            },
        }
    )

    assert packet["ran"] is True
    assert packet["status"] == "not_verified_or_zero"
    assert packet["decision_basis"] == (
        "no_exact_selected_cell_risk_match:session_or_hour_key_mismatch"
    )
    assert packet["refusal_cause"] == "session_or_hour_key_mismatch"
    assert packet["failed_dimensions"] == [
        {
            "field": "route_session",
            "live": ["moonshot_h22_23"],
            "risk_row": "london",
        }
    ]
    assert packet["nearest_candidate"]["risk_cell_id"] == "risk-london-session-only"
    assert packet["unresolved_reasons"] == ["session_or_hour_key_mismatch"]
    assert packet["source_ledger_path"] == "risk-ledger.jsonl"
    assert packet["capture_contract"]["status"] == (
        "exact_selected_cell_source_row_capture_required"
    )


def test_broader_origin_gate3_rejection_packet_carries_policy_intent_and_null_reasons(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "src.judgment.cost_choices.withholds",
        lambda question, facts=None, **kwargs: question == "permissions_spread" and bool((facts or {}).get("cents_above_the_max")),
    )
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    config["risk"]["max_spread_cents"] = 0.25
    orch = _orchestrator(tmp_path, config)

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-26T07:15:00Z",
            "candles": {"M15": []},
        },
        mso=SimpleNamespace(
            timestamp_utc="2026-05-26T07:15:00Z",
            timeframes={"M15": SimpleNamespace(atr_14=1.0)},
        ),
        kill_zone="london",
    )

    assert outcome == "REJECTED_GATE3_CIRCUIT_BREAKER"
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    saved = _saved_trade_records(tmp_path)
    assert saved
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    packet = record["decision_pipeline"]["gtos_vnext_candidate_intelligence_packet"]
    assert packet["capture_mode"] == "native_live_writer"
    assert packet["dynamic_policy"]["ran"] is True
    assert packet["dynamic_policy"]["not_run_reason"] is None
    assert packet["dynamic_policy"]["selected_policy"] == "partial_be_runner"
    assert packet["dynamic_policy"]["execution_policy_id"] == (
        "vnext_exec_partial_50_at_1r_be_runner_to_3r"
    )
    assert packet["dynamic_policy"]["selected_policy_source"] == "dynamic_router_result"
    assert packet["selected_cell_risk_proof"]["ran"] is True
    assert packet["selected_cell_risk_proof"]["match_reason"] == (
        "risk_ledger_not_required_by_runtime_config"
    )
    assert packet["gates"]["gate3"]["output"]["passed"] is False
    assert packet["gates"]["gate3"]["output"]["details"]["denial_reason"] == (
        "spread_too_wide"
    )
    assert packet["geometry"]["repair_path"]["entered"] is True
    assert packet["geometry"]["repair_path"]["status"] == "repaired"
    assert packet["final_order_decision"]["order_path"] == (
        "permission_rejected_after_repaired_geometry"
    )
    assert packet["selector_bridge_proof"]["dynamic_router_ran"] is True
    assert packet["order_readiness"]["order_path"] == (
        "permission_rejected_after_repaired_geometry"
    )
    assert packet["source_completeness"]["source_path_feature_status"] == (
        "raw_data_m15_asof_complete"
    )
    assert packet["old_system_absence_proof"]["absence_status"] == "explicit_absent"


def test_broader_origin_pre_geometry_concurrent_cap_waits_for_selected_cell_risk(
    tmp_path,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "risk_cell_id": "risk-xau-london-partial",
                "symbol": "XAUUSD",
                "broker_alias": "XAUUSD",
                "selector_component": "broader_origin",
                "family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "side": "LONG",
                "route_session": "london",
                "selected_policy": "partial_be_runner",
                "effective_risk_per_trade_pct": 0.25,
                "risk_decision_basis": "unit_selected_cell_positive",
                "exact_unresolved_or_excluded_reasons": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    config["risk"]["max_concurrent"] = 4
    runtime_cfg = config["gtos_vnext_runtime"]
    runtime_cfg["moonshot_dynamic_execution_router_require_selected_cell_risk_ledger"] = True
    runtime_cfg["moonshot_dynamic_execution_router_selected_cell_risk_ledger_path"] = str(
        risk_ledger
    )
    orch = _orchestrator(tmp_path, config)
    orch.mt5._positions = [
        SimpleNamespace(magic=MAGIC_NUMBER, symbol=f"SYM{i}", ticket=100 + i)
        for i in range(4)
    ]

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-26T07:15:00Z",
            "candles": {"M15": []},
        },
        mso=SimpleNamespace(
            timestamp_utc="2026-05-26T07:15:00Z",
            timeframes={"M15": SimpleNamespace(atr_14=1.0)},
        ),
        kill_zone="london",
    )

    assert outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
    assert len(orch.execution.set_limit_calls) == 1
    saved = _saved_trade_records(tmp_path)
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    assert record["decision_pipeline"]["pre_geometry_concurrent_cap_reached_advisory"] == {
        "deferred": True,
        "reason": "concurrent_cap_reached",
        "details": {"filled_positions": 4, "max_concurrent": 4},
        "terminal_authority": (
            "final_gate3_after_dynamic_router_selected_cell_risk_"
            "geometry_repair_and_prop_governor"
        ),
    }
    packet = record["decision_pipeline"]["gtos_vnext_candidate_intelligence_packet"]
    assert packet["dynamic_policy"]["ran"] is True
    assert packet["selected_cell_risk_proof"]["status"] == "verified_positive"
    assert packet["selected_cell_risk_proof"]["risk_pct"] == 0.25
    assert packet["gates"]["gate3"]["output"]["passed"] is True
    assert packet["final_order_decision"]["order_path"] == "pending_limit"


def test_pre_dynamic_prop_budget_projection_does_not_terminally_block_dynamic_router(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=True)
    orch = _orchestrator(tmp_path, config)
    calls = []

    def fake_prop_selector(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return GTOSVNextPropSafeSelectorDecision(
                action="DEFER_UNTIL_RESET",
                would_action="DEFER_UNTIL_RESET",
                enabled=True,
                apply_to_execution=True,
                applied=True,
                decision="FOLLOW",
                before_risk_pct=kwargs["current_risk_pct"],
                after_risk_pct=0.0,
                max_allowed_new_trade_risk_pct=0.0,
                reason="prop_safe_selector_defer_until_reset_gtos_internal_daily_overlay_budget",
                exposure_breakdown={"new_trade_sl_risk_pct": kwargs["current_risk_pct"]},
            )
        return GTOSVNextPropSafeSelectorDecision(
            action="ALLOW",
            would_action="ALLOW",
            enabled=True,
            apply_to_execution=True,
            applied=False,
            decision="FOLLOW",
            before_risk_pct=kwargs["current_risk_pct"],
            after_risk_pct=kwargs["current_risk_pct"],
            max_allowed_new_trade_risk_pct=0.25,
            reason="prop_safe_selector_budget_allows_full_risk",
        )

    monkeypatch.setattr(orch_mod, "evaluate_vnext_prop_safe_selector", fake_prop_selector)

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(),
        raw_data={
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-26T07:15:00Z",
            "candles": {"M15": []},
        },
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
    assert len(calls) == 2
    assert calls[1]["current_risk_pct"] > 0
    saved = _saved_trade_records(tmp_path)
    record = json.loads(saved[0].read_text(encoding="utf-8"))
    projection = record["decision_pipeline"][
        "gtos_vnext_prop_safe_selector_pre_dynamic_projection"
    ]
    assert projection["action"] == "DEFER_UNTIL_RESET"
    assert record["instrumentation"][
        "gtos_vnext_prop_safe_selector_pre_dynamic_projection_only"
    ] is True


def test_open_position_risk_uses_ticket_bound_vnext_lifecycle_not_base_config(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    config["risk"]["risk_per_trade_pct"] = 2.0
    lifecycle = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle.write_text(
        json.dumps(
            {
                "symbol": "NAS100",
                "broker_symbol": "NDX100",
                "broker_fill_state": "filled",
                "trade_state_ticket": 241779188,
                "mt5_position_ticket": 241779188,
                "gtos_vnext_selected_cell_risk_pct": 0.25,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(orch_mod, "PENDING_LIMIT_LIFECYCLE_LOG_PATH", str(lifecycle))
    orch = _orchestrator(tmp_path, config)
    orch.mt5.get_positions = lambda symbol=None: [
        SimpleNamespace(symbol="NDX100", ticket=241779188, identifier=241779188)
    ]

    positions = SessionOrchestrator._get_open_positions_for_correlation(orch)

    assert positions[0]["symbol"] == "NDX100"
    assert positions[0]["risk_pct"] == 0.25
    assert positions[0]["risk_pct_source"] == (
        "ticket_bound_pending_lifecycle_vnext_selected_cell"
    )
    assert positions[0]["risk_pct_missing_reason"] is None
    assert positions[0]["risk_amount"] is None
    assert positions[0]["risk_amount_source"] == "missing_position_stop_loss"
    assert positions[0]["risk_amount_missing_reason"] == "position_stop_loss_missing"
    assert positions[0]["ticket"] == 241779188
    assert positions[0]["identifier"] == 241779188


def test_open_position_risk_values_current_position_loss_to_stop(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    config["market"].update(
        {
            "trade_tick_size": 0.1,
            "trade_tick_value": 1.0,
        }
    )
    lifecycle = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle.write_text(
        json.dumps(
            {
                "symbol": "XAUUSD",
                "broker_symbol": "XAUUSD",
                "broker_fill_state": "filled",
                "trade_state_ticket": 777,
                "mt5_position_ticket": 777,
                "gtos_vnext_selected_cell_risk_pct": 0.25,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(orch_mod, "PENDING_LIMIT_LIFECYCLE_LOG_PATH", str(lifecycle))
    orch = _orchestrator(tmp_path, config)
    orch.mt5._mt5 = SimpleNamespace(
        order_calc_profit=lambda order_type, symbol, volume, price_open, target_price: (
            (target_price - price_open if int(order_type) == 0 else price_open - target_price)
            / 0.1
            * 1.0
            * volume
        )
    )
    orch.mt5.get_positions = lambda symbol=None: [
        SimpleNamespace(
            symbol="XAUUSD",
            ticket=777,
            identifier=777,
            type=0,
            volume=2.0,
            price_open=100.0,
            sl=95.0,
            profit=50.0,
        )
    ]

    positions = SessionOrchestrator._get_open_positions_for_correlation(orch)
    summary = SessionOrchestrator._open_position_risk_exposure_summary(
        orch,
        positions,
        100000.0,
    )

    assert positions[0]["risk_amount"] == 150.0
    assert positions[0]["risk_amount_source"] == (
        "current_position_profit_to_stop_loss_broker_order_calc_profit"
    )
    assert summary["open_position_risk_amount"] == 150.0
    assert summary["open_position_risk_valued_count"] == 1
    assert summary["open_position_risk_pct_fallback_count"] == 0
    assert summary["open_position_risk_missing_count"] == 0


def test_open_position_cash_risk_requires_broker_profit_model(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    lifecycle = tmp_path / "pending_limit_lifecycle.jsonl"
    lifecycle.write_text(
        json.dumps(
            {
                "symbol": "XAUUSD",
                "broker_symbol": "XAUUSD",
                "broker_fill_state": "filled",
                "trade_state_ticket": 778,
                "mt5_position_ticket": 778,
                "gtos_vnext_selected_cell_risk_pct": 0.25,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(orch_mod, "PENDING_LIMIT_LIFECYCLE_LOG_PATH", str(lifecycle))
    orch = _orchestrator(tmp_path, config)
    orch.mt5.get_positions = lambda symbol=None: [
        SimpleNamespace(
            symbol="XAUUSD",
            ticket=778,
            identifier=778,
            type=0,
            volume=2.0,
            price_open=100.0,
            sl=95.0,
            profit=50.0,
        )
    ]

    positions = SessionOrchestrator._get_open_positions_for_correlation(orch)
    summary = SessionOrchestrator._open_position_risk_exposure_summary(
        orch,
        positions,
        100000.0,
    )

    assert positions[0]["risk_amount"] is None
    assert positions[0]["risk_amount_source"] == "unverified_stop_loss_profit_model"
    assert positions[0]["risk_amount_missing_reason"] == (
        "position_profit_at_stop_broker_order_calc_profit_required_unavailable"
    )
    assert summary["open_position_risk_amount"] == 0.0
    assert summary["open_position_risk_valued_count"] == 0
    assert summary["open_position_risk_pct_fallback_count"] == 0
    assert summary["open_position_risk_missing_count"] == 1


def test_no_candidate_m1_capture_state_reads_runtime_namespace(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    orch._runtime_namespace = "redacted_account_live_bee34003"
    monkeypatch.chdir(tmp_path)
    pipeline_state = tmp_path / "pipeline_state"
    pipeline_state.mkdir()
    (pipeline_state / "m1_capture_state.json").write_text(
        json.dumps(
            {
                "updated_at_utc": "2026-06-02T18:00:00+00:00",
                "symbols": {
                    "XAUUSD": {
                        "broker_symbol": "LEGACY",
                        "last_closed_candle_time_utc": "2026-06-02T17:59:00+00:00",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (pipeline_state / "m1_capture_state_redacted_account_live_bee34003.json").write_text(
        json.dumps(
            {
                "updated_at_utc": "2026-06-02T18:15:00+00:00",
                "symbols": {
                    "XAUUSD": {
                        "broker_symbol": "XAUUSD",
                        "last_closed_candle_time_utc": "2026-06-02T18:14:00+00:00",
                        "last_cycle_status": "ok",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    state = orch._vnext_m1_capture_state_snapshot()

    assert state is not None
    assert state["path"].endswith("m1_capture_state_redacted_account_live_bee34003.json")
    assert state["runtime_namespace"] == "redacted_account_live_bee34003"
    assert state["broker_symbol"] == "XAUUSD"
    assert state["last_closed_candle_time_utc"] == "2026-06-02T18:14:00+00:00"


def test_broader_origin_market_record_persists_order_deal_identity(
    tmp_path,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    orch = _orchestrator(tmp_path, config)
    record = {
        "metadata": {
            "trade_id": "XAUUSD_2026-06-02_london_0700",
            "date": "2026-06-02",
            "symbol": "XAUUSD",
            "kill_zone": "london",
            "candle_time": "2026-06-02T07:00:00+00:00",
        },
        "decision_pipeline": {},
    }
    to_record = SimpleNamespace(to_record=lambda: {"status": "ok"})
    trade_state = SimpleNamespace(
        trade_id="tr_market_identity",
        ticket=242700001,
        entry_order_ticket=242700001,
        entry_deal_ticket=242700002,
        entry_order_retcode=10009,
        direction="LONG",
        entry_price=2500.0,
        stop_loss=2490.0,
        take_profit_1=2520.0,
    )

    orch._save_vnext_broader_origin_market_record(
        record=record,
        tc_cfg={"base_path": str(tmp_path / "records")},
        trade_state=trade_state,
        effective_risk_pct=0.25,
        vnext_pending_policy=to_record,
        vnext_ltf_path_execution=to_record,
        vnext_prop_safe_selector=to_record,
        vnext_moonshot_dynamic_execution=to_record,
    )

    execution = record["execution"]
    assert execution["entry_order_ticket"] == 242700001
    assert execution["entry_deal_ticket"] == 242700002
    assert execution["entry_deal_ticket_status"] == "mt5_result_deal_ticket_present"
    assert execution["order_result_retcode"] == 10009
    assert execution["filled_order_position_join_keys"] == [
        "trade_state_ticket:242700001",
        "mt5_position_ticket:242700001",
        "mt5_entry_order_ticket:242700001",
        "mt5_entry_deal_ticket:242700002",
    ]
    assert execution["exact_r_join_key_status"] == "FILLED_ORDER_POSITION_KEYS_CAPTURED"


def test_open_position_risk_missing_lifecycle_does_not_default_to_base_config(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    config["risk"]["risk_per_trade_pct"] = 2.0
    monkeypatch.setattr(
        orch_mod,
        "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
        str(tmp_path / "missing_pending_limit_lifecycle.jsonl"),
    )
    orch = _orchestrator(tmp_path, config)
    orch.mt5.get_positions = lambda symbol=None: [
        SimpleNamespace(symbol="XAUUSD", ticket=999, identifier=999)
    ]

    positions = SessionOrchestrator._get_open_positions_for_correlation(orch)

    assert positions[0]["risk_pct"] == 0.0
    assert positions[0]["risk_pct_source"] == "missing_not_defaulted_to_base"
    assert positions[0]["risk_pct_missing_reason"] == (
        "pending_lifecycle_log_missing_no_base_risk_default"
    )


def test_stale_no_candidate_consume_false_cannot_reactivate_old_path(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist)
    config["gtos_vnext_runtime"]["moonshot_broader_origin_consume_no_candidate"] = False
    orch = _orchestrator(tmp_path, config)
    monkeypatch.setattr(
        orch_mod,
        "generate_live_broader_origin_candidates",
        lambda **kwargs: [],
    )

    consumed = orch._process_vnext_broader_origin_candidates(
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z"},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert consumed is True
    assert orch._last_vnext_broader_origin_no_candidate["decision_path"] == (
        "vnext_broader_origin_no_candidate_consumed_before_old_primary_analyzer_and_l2"
    )
    assert "old_candidate_generation_may_continue" not in json.dumps(
        orch._last_vnext_broader_origin_no_candidate
    )


def test_no_broader_origin_candidate_does_not_call_primary_analyzer_or_old_l2(
    tmp_path,
    monkeypatch,
):
    allowlist = _allowlist(tmp_path / "allowlist.json")
    config = _config(tmp_path, allowlist_path=allowlist, trade_capture=False)
    orch = _orchestrator(tmp_path, config)
    raw_data = {
        "symbol": "XAUUSD",
        "candle_close_utc": "2026-05-26T07:15:00Z",
        "candles": {"M15": [{"time": "2026-05-26T07:00:00Z", "close": 100.0}]},
    }
    mso = SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z")
    async def analyze(**kwargs):
        raise AssertionError("PrimaryAnalyzer called")

    monkeypatch.setattr(orch_mod, "compute_market_state", lambda raw, cfg: mso)
    monkeypatch.setattr(orch_mod, "generate_live_broader_origin_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        orch_mod,
        "prescreen_mso",
        lambda _mso: (_ for _ in ()).throw(AssertionError("old prescreen called")),
    )
    monkeypatch.setattr(orch_mod, "should_block_trading", lambda *args, **kwargs: (False, ""))
    monkeypatch.setattr(orch_mod, "notify_candidate", lambda **kwargs: None)
    monkeypatch.setattr(orch_mod, "log_candidate_features", lambda **kwargs: None)
    monkeypatch.setattr(
        orch_mod,
        "verify_candidate",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("old L2 called")),
    )
    monkeypatch.setattr(orch_mod, "vnext_execution_block_reason", lambda decision, cfg: "vnext_runtime_avoid_veto")

    orch.analyzer = SimpleNamespace(
        analyze=analyze,
        last_system_prompt="",
        last_user_message="",
        _last_usage=None,
    )
    orch.eval_logger = SimpleNamespace(log_evaluation=lambda **kwargs: None, _candle_index_in_kz=1)
    orch.session_memory = []
    orch._calendar = None
    orch._news_calendar = SimpleNamespace(enabled=False)
    orch.devils_advocate = SimpleNamespace(evaluate=lambda **kwargs: None)
    orch._xau_d1_direction_value = "disabled"
    orch._update_daily_pnl = lambda: None
    orch._check_kill_zone_trade_cap = lambda kill_zone: False
    orch._check_and_trigger_daily_loss_stop = lambda kill_zone: False
    orch._check_sprt_class_halt_gate = lambda kill_zone: False
    orch._should_skip_first_ny_candle = lambda kill_zone: False
    orch._ingest_live_data_with_reconnect = lambda kill_zone: raw_data
    orch._log_ob_retest_event = lambda *args, **kwargs: None
    orch._compute_deterministic_bias = lambda _mso: {
        "bias": "bullish",
        "d1": "bullish",
        "h4": "bullish",
        "h1": "bullish",
    }
    orch._evaluate_gtos_vnext_pre_ai = lambda **kwargs: SimpleNamespace(action="ALLOW_AI")
    orch._evaluate_structural_c_gate_pre_ai = lambda **kwargs: SimpleNamespace(action="ALLOW")
    orch._apply_structural_c_gate_pre_ai_route = lambda bias_result, structural_c_gate: bias_result
    orch._evaluate_gtos_vnext_ai_policy = lambda **kwargs: SimpleNamespace(allowed=True, reason="ok")
    orch._evaluate_ai_call_policy = lambda **kwargs: SimpleNamespace(allowed=True, reason="ok", context={})
    orch._format_session_memory = lambda: ""
    orch._compute_align_context = lambda _mso, bias_result: ""
    orch._format_gtos_vnext_ai_role_context = lambda **kwargs: ""
    orch._gtos_vnext_ai_route_mismatch = lambda **kwargs: None
    orch._update_session_memory = lambda analysis, kill_zone: None
    orch._extract_align_score = lambda text: 0
    orch._get_current_spread = lambda: 1.0
    orch._record_forward_capture_candidate_shadow = lambda **kwargs: None
    orch._record_gtos_vnext_replacement_monitoring = lambda **kwargs: None
    orch._evaluate_gtos_vnext_runtime = lambda **kwargs: GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={"symbol": "XAUUSD", "route_session": "london", "side": "LONG"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="test_vnext_runtime_avoid_veto",
        evidence={"matched_rows": 12},
    )

    orch._process_candle("london")

    assert orch._last_vnext_broader_origin_no_candidate["decision_path"].endswith(
        "primary_analyzer_and_l2"
    )
    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    assert orch._log_rows[-1][0][0] == (
        "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_NO_CANDIDATE"
    )


@pytest.mark.parametrize(
    ("candidate_overrides", "config_overrides", "equity", "expected"),
    [
        (
            {"source_path_feature_status": "historical_replay_only"},
            {},
            100000.0,
            "source_path_not_asof_computed",
        ),
        (
            {},
            {"allowlist_proof_class": "broad_label_not_row_level_proof"},
            100000.0,
            "framework_not_activated_in_stage13_full_moonshot_selector",
        ),
        (
            {},
            {"eligible_symbols": ["GBPJPY"]},
            100000.0,
            "symbol_not_in_broker_native_activation_map",
        ),
        (
            {
                "candle_open_utc": "2026-05-26T03:00:00Z",
                "candle_close_utc": "2026-05-26T03:15:00Z",
                "route_session": "off_configured_session",
                "session": "off_configured_session",
                "session_bucket": "off_configured_session",
                "kill_zone": "off_configured_session",
            },
            {},
            100000.0,
            "outside_configured_kill_zone_or_missing_schedule",
        ),
        (
            {"same_bar_ambiguous": True},
            {},
            100000.0,
            "selected_policy_ordered_ltf_or_tick_path_required",
        ),
            (
                {},
                {},
                94900.0,
                "DEFERRED_GTOS_VNEXT_PROP_RESET",
            ),
    ],
)
def test_broader_origin_refusals_do_not_place_market_or_pending_orders(
    tmp_path,
    candidate_overrides,
    config_overrides,
    equity,
    expected,
):
    allowlist = _allowlist(
        tmp_path / "allowlist.json",
        proof_class=config_overrides.get("allowlist_proof_class"),
    )
    config = _config(
        tmp_path,
        allowlist_path=allowlist,
        eligible_symbols=config_overrides.get("eligible_symbols"),
    )
    orch = _orchestrator(tmp_path, config, equity=equity)

    outcome = orch._execute_vnext_broader_origin_candidate(
        candidate=_candidate(**candidate_overrides),
        raw_data={"symbol": "XAUUSD", "candle_close_utc": "2026-05-26T07:15:00Z", "candles": {"M15": []}},
        mso=SimpleNamespace(timestamp_utc="2026-05-26T07:15:00Z"),
        kill_zone="london",
    )

    assert not orch.execution.open_trade_calls
    assert not orch.execution.set_limit_calls
    if expected.startswith("SKIPPED_") or expected.startswith("DEFERRED_"):
        assert outcome == expected
    else:
        assert outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"
        assert expected in str(orch._log_rows[-1])
