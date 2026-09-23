from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts import build_vnext_live_starvation_intelligence as intel


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _config(path: Path) -> None:
    path.write_text(
        """
gtos_vnext_runtime:
  moonshot_dynamic_execution_router_broker_native_eligible_symbols:
    - XAUUSD
    - NAS100
    - XAGUSD
    - US30_cash
    - USDJPY
    - GBPJPY
    - GBPUSD
    - EURUSD
    - AUDJPY
    - AUDUSD
    - BTCUSD
    - CHFJPY
    - ETHUSD
    - EURGBP
    - EURJPY
    - GER40
    - JP225
    - NZDUSD
    - SPX500
    - UK100
    - UKOIL_cash
    - USDCAD
    - USDCHF
    - USOIL_cash
  moonshot_dynamic_execution_router_activated_origin_families:
    - cross_asset_lead_lag
    - liquidity_sweep_reclaim
""".lstrip(),
        encoding="utf-8",
    )


def test_build_starvation_matrix_covers_symbols_origins_and_refusals(tmp_path, monkeypatch):
    cfg = tmp_path / "agent_config.yaml"
    runtime_log = tmp_path / "runtime.jsonl"
    replacement_log = tmp_path / "replacement.jsonl"
    records = tmp_path / "records"
    records.mkdir()
    _config(cfg)
    _write_jsonl(
        runtime_log,
        [
            {
                "timestamp_utc": "2026-05-28T10:00:01+00:00",
                "candle_time_utc": "2026-05-28T10:00:00Z",
                "phase": "broader_origin_pre_ai_candidate",
                "symbol": "XAUUSD",
                "kill_zone": "ny",
                "decision": {
                    "event": {
                        "symbol": "XAUUSD",
                        "route_family": "cross_asset_lead_lag",
                        "route_session": "ny",
                        "source_mode": "LIVE_RAW_M15",
                    },
                    "evidence": {"broader_origin_candidate_id": "cand-1"},
                },
            },
            {
                "timestamp_utc": "2026-05-28T10:00:02+00:00",
                "candle_time_utc": "2026-05-28T10:00:00Z",
                "phase": "moonshot_dynamic_execution",
                "symbol": "XAUUSD",
                "kill_zone": "ny",
                "decision": {
                    "selected_policy": "partial_be_runner",
                    "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
                    "candidate_use_allowed_now": False,
                    "refusal_reasons": ["selected_cell_risk_not_verified_or_zero"],
                    "replaced_policy": "retired_static_baseline_comparator",
                    "source_event": {
                        "symbol": "XAUUSD",
                        "origin_family": "cross_asset_lead_lag",
                        "source_mode": "LIVE_RAW_M15",
                        "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
                        "prop_governor_action": "ALLOW",
                    },
                },
            },
        ],
    )
    _write_jsonl(replacement_log, [])
    monkeypatch.setattr(intel, "ORDER_LIFECYCLE_LEDGER", tmp_path / "orders.jsonl")
    monkeypatch.setattr(intel, "DYNAMIC_LIFECYCLE_LEDGER", tmp_path / "dynamic.jsonl")
    monkeypatch.setattr(intel, "BROKER_DEAL_LEDGER", tmp_path / "deals.jsonl")

    rows, summary, refusal_breakdowns = intel.build(
        hours=12,
        now=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        post_reload_cutoff=datetime(2026, 5, 28, 11, 0, tzinfo=timezone.utc),
        config_path=cfg,
        runtime_log=runtime_log,
        replacement_log=replacement_log,
        trade_record_root=records,
    )

    assert summary["expected_symbol_origin_cells"] == 48
    assert summary["ledger_rows"] == 48
    assert summary["raw_candidate_rows"] == 1
    assert summary["dynamic_skip_rows"] == 1
    assert summary["final_broker_ready_candidates"] == 0
    assert summary["flat_broker_classification"] == "flat_broker_state_explained_by_live_refusals"
    assert summary["post_reload_stale_label_hits"] == 0
    assert len(refusal_breakdowns) == 1
    assert refusal_breakdowns[0]["selected_cell_risk_refusal_cause"] in {
        "session_or_hour_key_mismatch",
        "missing_ledger_row",
    }
    assert intel.verify(summary, rows, refusal_breakdowns)["ok"] is True


def test_verify_flags_post_reload_stale_label(tmp_path, monkeypatch):
    cfg = tmp_path / "agent_config.yaml"
    runtime_log = tmp_path / "runtime.jsonl"
    replacement_log = tmp_path / "replacement.jsonl"
    records = tmp_path / "records"
    records.mkdir()
    _config(cfg)
    _write_jsonl(
        runtime_log,
        [
            {
                "timestamp_utc": "2026-05-28T10:00:02+00:00",
                "candle_time_utc": "2026-05-28T10:00:00Z",
                "phase": "moonshot_dynamic_execution",
                "symbol": "XAUUSD",
                "decision": {
                    "selected_policy": "momentum_exhaustion",
                    "candidate_use_allowed_now": False,
                    "refusal_reasons": ["framework_not_activated_in_stage13_full_moonshot_selector"],
                    "replaced_policy": "live_current_j46_j49",
                    "source_event": {"symbol": "XAUUSD", "origin_family": "liquidity_sweep_reclaim"},
                },
            }
        ],
    )
    _write_jsonl(replacement_log, [])
    monkeypatch.setattr(intel, "ORDER_LIFECYCLE_LEDGER", tmp_path / "orders.jsonl")
    monkeypatch.setattr(intel, "DYNAMIC_LIFECYCLE_LEDGER", tmp_path / "dynamic.jsonl")
    monkeypatch.setattr(intel, "BROKER_DEAL_LEDGER", tmp_path / "deals.jsonl")

    rows, summary, refusal_breakdowns = intel.build(
        hours=12,
        now=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
        post_reload_cutoff=datetime(2026, 5, 28, 9, 0, tzinfo=timezone.utc),
        config_path=cfg,
        runtime_log=runtime_log,
        replacement_log=replacement_log,
        trade_record_root=records,
    )
    result = intel.verify(summary, rows, refusal_breakdowns)

    assert summary["post_reload_stale_label_hits"] == 1
    assert result["ok"] is False
    assert any(issue["code"] == "post_reload_stale_label_hits" for issue in result["issues"])


def test_risk_refusal_cause_classifies_zero_spread_cost_cell():
    cause = intel._risk_refusal_cause(
        source={
            "selected_cell_risk_match_reason": "matching_selected_cell_risk_zero_or_unresolved"
        },
        nearest={
            "exact_unresolved_or_excluded_reasons": [
                "risk_zero_spread_cost_exceeds_20pct_of_median_sl"
            ],
            "failed_dimensions": [],
        },
    )

    assert cause == "zero_risk_row"


def test_pre_current_reload_selector_bridge_mismatch_is_scoped_as_historical():
    row = {
        "timestamp_utc": "2026-05-28T18:30:00+00:00",
        "symbol": "ETHUSD",
        "kill_zone": "off_configured_session",
    }
    source = {
        "symbol": "ETHUSD",
        "broker_symbol": "ETHUSD",
        "side": "SHORT",
        "framework": "origin_liquidity_sweep_reclaim",
        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
        "route_session": "off_configured_session",
        "session_bucket": "off_kz_broad",
        "source_mode": "LIVE_RAW_M15",
        "source_path_feature_status": "raw_data_m15_asof_complete",
        "live_generation_status": "generated_live_asof",
        "source_window_complete": True,
    }
    decision = {
        "selected_policy": "partial_be_runner",
        "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "refusal_reasons": [
            "framework_not_activated_in_stage13_full_moonshot_selector"
        ],
    }
    breakdown = intel._refusal_breakdown_row(
        row=row,
        source=source,
        decision=decision,
        runtime_cfg={
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_allow_stage13_be_selector_policy_bridge": True,
        },
        allowlist_entries=[
            {
                "symbol": "ETHUSD",
                "origin_family": "liquidity_sweep_reclaim",
                "side": "SHORT",
                "route_session": "off_configured_session",
                "selected_policy": "be_after_trigger",
                "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                "metrics": {
                    "selected_count": 50,
                    "expectancy_r": 0.2,
                    "profit_factor": 1.4,
                },
            }
        ],
        risk_rows=[],
        broker_aliases={},
        promotion_evidence={"verified": True, "status": "verified"},
        post_reload_cutoff=datetime(2026, 5, 28, 20, 28, tzinfo=timezone.utc),
    )

    assert breakdown["selector_classification"] == (
        "historical_selector_contract_mismatch_repaired_after_reload"
    )
    assert breakdown["selector_evidence_backed_exclusion"] is True
    assert breakdown["exact_failed_dimensions"] == []


def test_current_selector_exclusion_makes_selected_cell_risk_not_applicable():
    row = {
        "timestamp_utc": "2026-05-28T22:30:06+00:00",
        "symbol": "GBPUSD",
        "kill_zone": "moonshot_h22_23",
    }
    source = {
        "symbol": "GBPUSD",
        "broker_symbol": "GBPUSD",
        "side": "LONG",
        "framework": "origin_cross_asset_lead_lag",
        "candidate_origin_family": "origin_cross_asset_lead_lag",
        "route_session": "moonshot_h22_23",
        "session_bucket": "moonshot_h22_23_broad",
        "source_mode": "LIVE_CROSS_ASSET_RAW_M15",
        "source_path_feature_status": "cross_asset_raw_data_asof_complete",
        "live_generation_status": "generated_live_asof",
        "source_window_complete": True,
        "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
        "selected_cell_risk_selected_policy": "partial_be_runner",
    }
    decision = {
        "selected_policy": "partial_be_runner",
        "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "refusal_reasons": [
            "framework_not_activated_in_stage13_full_moonshot_selector",
            "selected_cell_risk_not_verified_or_zero",
        ],
    }
    breakdown = intel._refusal_breakdown_row(
        row=row,
        source=source,
        decision=decision,
        runtime_cfg={
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "cross_asset_lead_lag"
            ],
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "cross_asset_lead_lag"
            ],
            "moonshot_dynamic_execution_router_allow_stage13_be_selector_policy_bridge": True,
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
        },
        allowlist_entries=[
            {
                "symbol": "GBPJPY",
                "origin_family": "cross_asset_lead_lag",
                "side": "LONG",
                "route_session": "moonshot_h22_23",
                "utc_hour_bucket": "h22_23",
                "selected_policy": "be_after_trigger",
                "proof_class": "positive_outside_session_origin_native_dynamic_replay_row_level_proof",
                "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                "metrics": {
                    "selected_count": 82,
                    "expectancy_r": 0.04,
                    "profit_factor": 1.09,
                },
            }
        ],
        risk_rows=[
            {
                "symbol": "GBPJPY",
                "broker_alias": "GBPJPY",
                "family": "cross_asset_lead_lag",
                "side": "LONG",
                "route_session": "moonshot_h22_23",
                "selected_policy": "be_after_trigger",
                "selector_component": "broader_origin",
                "effective_risk_per_trade_pct": 0.0,
                "risk_cell_id": "STAGE13-FN-RISK-CELL-000491",
                "risk_decision_basis": "risk_zero_spread_cost_exceeds_20pct_of_median_sl",
                "exact_unresolved_or_excluded_reasons": [
                    "risk_zero_spread_cost_exceeds_20pct_of_median_sl"
                ],
            }
        ],
        broker_aliases={},
        promotion_evidence={"verified": True, "status": "verified", "checked_rows": 289600},
        post_reload_cutoff=datetime(2026, 5, 28, 22, 28, tzinfo=timezone.utc),
    )

    assert breakdown["selector_classification"] == "outside_activated_stage13_selector"
    assert breakdown["selector_evidence_backed_exclusion"] is True
    assert breakdown["selected_cell_risk_refusal_cause"] == "symbol_alias_or_symbol_key_mismatch"
    assert breakdown["selected_cell_risk_evidence_backed_exclusion"] is True
    assert breakdown["selected_cell_risk_repair_decision"] == (
        "reject_with_exact_selector_dimension_proof_selected_cell_not_applicable"
    )


def test_verify_fails_current_selector_bridge_mismatch_without_repair():
    summary = {
        "ledger_rows": 1,
        "expected_symbol_origin_cells": 1,
        "symbol_count": 24,
        "origin_family_count": 1,
        "post_reload_stale_label_hits": 0,
        "refusal_reason_counts": {
            "framework_not_activated_in_stage13_full_moonshot_selector": 1
        },
    }
    breakdown = {
        "refusal_reasons": [
            "framework_not_activated_in_stage13_full_moonshot_selector"
        ],
        "post_reload_current_contract": True,
        "selector_classification": "selector_contract_mismatch_should_route_under_current_bridge",
        "selector_evidence_backed_exclusion": False,
        "nearest_allowlist_candidate": {"failed_dimensions": []},
        "exact_failed_dimensions": [],
    }

    result = intel.verify(summary, [], [breakdown])

    assert result["ok"] is False
    assert any(
        issue["code"] == "framework_refusal_contract_mismatch_unrepaired"
        for issue in result["issues"]
    )
