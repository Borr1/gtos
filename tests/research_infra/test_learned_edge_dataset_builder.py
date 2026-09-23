"""Focused tests for the learned-edge counterfactual training-frame builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.learned_edge_dataset_builder import (
    DISPOSITION_FILLED,
    DISPOSITION_MISSED,
    DISPOSITION_RISK_REJECTED,
    DISPOSITION_UNRESOLVED,
    FEATURE_WHITELIST,
    SealedPartitionError,
    build_training_frame,
    build_training_rows,
    discover_partition_ledgers,
    extract_features,
    feature_guard_violations,
    partition_role_for_day,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _candidate(candidate_id: str, *, symbol: str = "EURUSD", side: str = "LONG",
               decision_time: str = "2026-05-15T07:15:00+00:00") -> dict:
    return {
        "candidate_id": candidate_id,
        "trading_day": "2026-05-15",
        "phase": "ultimate_rolling_expanded_20260515",
        "symbol": symbol,
        "side": side,
        "direction": side,
        "decision_time_utc": decision_time,
        "origin_family": "liquidity_sweep_reclaim",
        "framework": "origin_liquidity_sweep_reclaim",
        "route_session": "london",
        "session_bucket": "london",
        "utc_hour_bucket": "h07_08",
        "kill_zone": "london",
        "candidate_probability": 0.61,
        "candidate_ev_r": 0.42,
        "expected_cost_r": 0.12,
        "risk_reward_ratio": 1.5,
        "entry_price": 1.1000,
        "entry_reference": 1.0995,
        "stop_loss": 1.0950,
        "take_profit_1": 1.1075,
        "simulated_open_positions_seen": 1,
        "simulated_pending_orders_seen": 0,
        "dynamic_geometry_policy": "momentum_exhaustion",
        "dynamic_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "probability_packet": {
            "selected_thesis": {
                "probability": 0.58,
                "uncalibrated_probability": 0.66,
                "uncertainty": 0.22,
                "missing_source_penalty": 0.08,
                "source_completeness": 0.8,
                "disagreement_state": "low",
            }
        },
    }


def _make_day(tmp_path: Path, prefix: str = "ULTIMATE_ROLLING_DYNAMIC") -> Path:
    route = tmp_path / "route"
    day = "20260515"
    # 4 candidates: filled winner, risk-rejected counterfactual, missed loser,
    # unresolved; plus a duplicate competing with the filled one.
    cands = [
        _candidate("cand_filled"),
        _candidate("cand_dup", side="LONG"),  # same decision_time/symbol/side group as cand_filled
        _candidate("cand_riskrej", symbol="XAUUSD"),
        _candidate("cand_missed", symbol="GBPUSD"),
        _candidate("cand_unresolved", symbol="USDJPY"),
    ]
    _write_jsonl(route / f"{prefix}_{day}_CANDIDATE_MICROSCOPE_LEDGER.jsonl", cands)
    _write_jsonl(
        route / f"{prefix}_{day}_SIMULATED_TRADE_LEDGER.jsonl",
        [{
            "candidate_id": "cand_filled",
            "net_proxy_r": 1.8,
            "net_r": 1.8,
            "terminal_outcome": "target_reached_before_stop",
            "mfe_r": 2.1,
            "mae_r": -0.3,
            "same_bar_ambiguity": False,
        }],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        [{
            "candidate_id": "cand_riskrej",
            "fill_status": "not_sent_risk_rejected",
            "counterfactual_path_scored": True,
            "counterfactual_fill_status": "filled_from_ordered_m1_path",
            "counterfactual_final_r": -1.1,
            "counterfactual_terminal_outcome": "stop_reached_before_target",
            "same_bar_ambiguity": False,
            "ordered_tick_truth_satisfied": False,
            "mfe_r": 0.2,
            "mae_r": -1.0,
        }],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [{
            "candidate_id": "cand_missed",
            "opportunity_close_reason": "stop_reached_before_target",
            "opportunity_path_scored": True,
            "net_proxy_r": -1.15,
            "ordered_tick_truth_satisfied": False,
        }],
    )
    _write_jsonl(route / f"{prefix}_{day}_SIMULATED_ORDER_LEDGER.jsonl", [])
    return route


def test_discovery_groups_by_prefix_and_day(tmp_path):
    route = _make_day(tmp_path)
    sets, notes = discover_partition_ledgers([route])
    assert len(sets) == 1
    assert sets[0].trading_day_token == "20260515"
    assert sets[0].campaign_prefix == "ULTIMATE_ROLLING_DYNAMIC"
    assert set(sets[0].paths) == {"candidate", "trade", "oracle", "missed", "order"}
    assert notes == []


def test_campaign_conflict_prefers_rolling_and_reports(tmp_path):
    route = _make_day(tmp_path)
    # Add a competing campaign for the same day.
    _write_jsonl(
        route / "ULTIMATE_EXPANDED_DYNAMIC_20260515_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
        [_candidate("cand_other")],
    )
    sets, notes = discover_partition_ledgers([route])
    assert len(sets) == 1
    assert sets[0].campaign_prefix == "ULTIMATE_ROLLING_DYNAMIC"
    assert notes and "campaign_conflict" in notes[0]


def test_dispositions_labels_and_weights(tmp_path):
    route = _make_day(tmp_path)
    sets, _ = discover_partition_ledgers([route])
    rows, summary = build_training_rows(sets[0])
    by_id = {r["candidate_id"]: r for r in rows}

    filled = by_id["cand_filled"]
    assert filled["disposition"] == DISPOSITION_FILLED
    assert filled["label_fill"] == 1
    assert filled["label_target_before_stop"] == 1
    assert filled["label_net_r"] == pytest.approx(1.8)
    assert filled["label_outcome_valid"] is True
    # duplicate group of 2 (cand_filled + cand_dup share time/symbol/side)
    assert filled["n_competing_in_group"] == 2
    assert filled["weight_duplicate_group"] == pytest.approx(0.5)
    assert filled["weight_outcome_head"] == pytest.approx(0.5 * 0.7)

    riskrej = by_id["cand_riskrej"]
    assert riskrej["disposition"] == DISPOSITION_RISK_REJECTED
    assert riskrej["label_fill"] == 1
    assert riskrej["label_target_before_stop"] == 0
    assert riskrej["label_net_r"] == pytest.approx(-1.1)

    missed = by_id["cand_missed"]
    assert missed["disposition"] == DISPOSITION_MISSED
    assert missed["label_fill"] == 1
    assert missed["label_net_r"] == pytest.approx(-1.15)

    unresolved = by_id["cand_unresolved"]
    assert unresolved["disposition"] == DISPOSITION_UNRESOLVED
    assert unresolved["label_fill"] is None
    assert unresolved["weight_outcome_head"] == 0.0

    assert summary["disposition_counts"][DISPOSITION_FILLED] == 1
    assert summary["disposition_counts"][DISPOSITION_RISK_REJECTED] == 1
    assert summary["disposition_counts"][DISPOSITION_MISSED] == 1
    # cand_dup and cand_unresolved have no outcome rows -> unresolved.
    assert summary["disposition_counts"][DISPOSITION_UNRESOLVED] == 2


def test_winsorization_and_ambiguous_exclusion(tmp_path):
    route = tmp_path / "route"
    prefix, day = "ULTIMATE_ROLLING_DYNAMIC", "20260516"
    cand = _candidate("cand_big")
    cand["trading_day"] = "2026-05-16"
    cand_amb = _candidate("cand_amb", symbol="JP225")
    cand_amb["trading_day"] = "2026-05-16"
    _write_jsonl(route / f"{prefix}_{day}_CANDIDATE_MICROSCOPE_LEDGER.jsonl", [cand, cand_amb])
    _write_jsonl(
        route / f"{prefix}_{day}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [
            {
                "candidate_id": "cand_big",
                "opportunity_close_reason": "target_reached_before_stop",
                "opportunity_path_scored": True,
                "net_proxy_r": 9.7,
            },
            {
                "candidate_id": "cand_amb",
                "opportunity_close_reason": "source_required_same_bar_target_stop_sequence_no_proxy_r",
                "opportunity_path_scored": True,
                "net_proxy_r": 1.0,
            },
        ],
    )
    sets, _ = discover_partition_ledgers([route])
    rows, _ = build_training_rows(sets[0])
    by_id = {r["candidate_id"]: r for r in rows}
    assert by_id["cand_big"]["label_net_r"] == pytest.approx(5.0)  # winsorized
    assert by_id["cand_big"]["label_net_r_raw"] == pytest.approx(9.7)
    amb = by_id["cand_amb"]
    assert amb["label_truth_tier"] == "m1_proxy_ambiguous"
    assert amb["label_outcome_valid"] is False
    assert amb["weight_outcome_head"] == 0.0
    assert amb["weight_fill_head"] == pytest.approx(0.25)


def test_feature_whitelist_guard():
    features = {name: None for name in FEATURE_WHITELIST}
    assert feature_guard_violations(features) == []
    bad = dict(features)
    bad["f_selector_action"] = "trade"
    violations = feature_guard_violations(bad)
    assert any("feature_not_whitelisted" in v for v in violations)


def test_extract_features_geometry_and_competition():
    cand = _candidate("c1")
    features = extract_features(cand, n_competing_in_group=3)
    assert features["f_limit_offset_r"] == pytest.approx(0.0005 / 0.0050)
    assert features["f_stop_distance_rel"] == pytest.approx(0.0050 / 1.1000)
    assert features["f_n_competing_in_group"] == 3.0
    assert features["f_asset_class"] == "fx"
    assert features["f_day_of_week"] == "fri"
    assert feature_guard_violations(features) == []


def test_sealed_partition_refused(tmp_path):
    route = _make_day(tmp_path)
    registry = tmp_path / "registry.jsonl"
    _write_jsonl(
        registry,
        [
            {"row_kind": "registry_header"},
            {
                "row_kind": "partition",
                "partition_id": "sealed_test",
                "role": "SEALED",
                "date_range": ["2026-05-15", "2026-05-15"],
            },
        ],
    )
    with pytest.raises(SealedPartitionError):
        build_training_frame([route], registry_path=registry, out_path=tmp_path / "out.jsonl")


def test_partition_role_assignment_and_output(tmp_path):
    route = _make_day(tmp_path)
    registry = tmp_path / "registry.jsonl"
    _write_jsonl(
        registry,
        [
            {"row_kind": "registry_header"},
            {
                "row_kind": "partition",
                "partition_id": "validation_walkforward_gate",
                "role": "VALIDATION",
                "date_range": ["2026-05-14", "2026-05-29"],
                "excluded_days": ["2026-05-18"],
            },
        ],
    )
    out = tmp_path / "frame.jsonl"
    result = build_training_frame([route], registry_path=registry, out_path=out)
    assert result["header"]["total_rows"] == 5
    rows = result["rows"]
    assert all(r["partition_role"] == "VALIDATION" for r in rows)
    # excluded day check
    role, pid = partition_role_for_day("2026-05-18", [
        {"row_kind": "partition", "partition_id": "p", "role": "VALIDATION",
         "date_range": ["2026-05-14", "2026-05-29"], "excluded_days": ["2026-05-18"]},
    ])
    assert role is None and pid is None
    # file round-trips
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 6  # header + 5 rows
    header = json.loads(lines[0])
    assert header["schema_version"] == "ultimate_learned_edge_training_frame_v1"
    assert header["broker_runtime_change_status"] is False
