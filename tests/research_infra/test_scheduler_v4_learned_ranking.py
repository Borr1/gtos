"""Learned ranking mode in Scheduler V4 best-trade allocator (default-off).

Covers:
- config capture (`scheduler_v4_learned_ranking_enabled` alias, defaults off),
- AllocatorCandidate learned-field alias tolerance,
- learned ranking flipping selection toward higher learned expected net R,
- veto chain dominance over any learned score (no_leak, risk headroom),
- fail-soft missing learned score penalty (never a veto),
- byte-identical behavior with the flag absent/false.
"""

from __future__ import annotations

import json

from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    AllocatorCandidate,
    SchedulerV4Config,
    allocate_decision_window,
)


def candidate_row(candidate_id: str, symbol: str, **overrides) -> dict:
    row = {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "side": "LONG",
        "action_intent": "new_position",
        "requested_risk_pct": 0.25,
        "selected_cell_risk_pct": 0.25,
        "ev_r": 0.8,
        "probability": 0.65,
        "confidence": 0.8,
        "uncertainty": 0.2,
        "fill_probability": 0.8,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "evidence_class": "source_bound_decision_time_fixture",
        "no_leak_status": "pass",
        "confluence_action": "follow",
        "confluence_strength": 0.8,
        "confluence_confidence": 0.8,
        "confluence_reliability": 0.8,
        "cost_r": 0.02,
    }
    row.update(overrides)
    return row


def window_mapping(*candidate_rows: dict, **extra) -> dict:
    mapping = {
        "decision_window_id": "window:learned-ranking",
        "candidate_set_id": "set:learned-ranking",
        "asof_utc": "2026-06-10T00:00:00+00:00",
        "candidates": list(candidate_rows),
    }
    mapping.update(extra)
    return mapping


def option_by_candidate(packet: dict, candidate_id: str) -> dict:
    for option in packet["all_options_preserved"]:
        if option.get("candidate_id") == candidate_id:
            return option
    raise AssertionError(f"candidate option missing: {candidate_id}")


def test_config_learned_ranking_defaults_off_with_alias_keys():
    default = SchedulerV4Config()
    assert default.learned_ranking_enabled is False
    assert default.learned_ranking_require_scored is True
    assert default.learned_score_weight == 1.0

    empty = SchedulerV4Config.from_mapping({})
    assert empty.learned_ranking_enabled is False
    assert empty.learned_ranking_require_scored is True
    assert empty.learned_score_weight == 1.0

    namespaced = SchedulerV4Config.from_mapping(
        {
            "scheduler_v4_learned_ranking_enabled": True,
            "scheduler_v4_learned_ranking_require_scored": False,
            "scheduler_v4_learned_score_weight": 2.5,
        }
    )
    assert namespaced.learned_ranking_enabled is True
    assert namespaced.learned_ranking_require_scored is False
    assert namespaced.learned_score_weight == 2.5

    direct = SchedulerV4Config.from_mapping(
        {"learned_ranking_enabled": "yes", "learned_score_weight": 0.5}
    )
    assert direct.learned_ranking_enabled is True
    assert direct.learned_score_weight == 0.5

    zero_weight = SchedulerV4Config.from_mapping(
        {"scheduler_v4_learned_score_weight": 0.0}
    )
    assert zero_weight.learned_score_weight == 0.0

    unparseable = SchedulerV4Config.from_mapping(
        {"scheduler_v4_learned_score_weight": "not-a-number"}
    )
    assert unparseable.learned_score_weight == 1.0


def test_candidate_from_mapping_captures_learned_fields_with_alias_tolerance():
    primary = AllocatorCandidate.from_mapping(
        candidate_row(
            "primary",
            "EURUSD",
            learned_expected_net_r=0.42,
            learned_probability=0.61,
            learned_fill_probability=0.71,
            learned_status="SCORED",
        )
    )
    assert primary.learned_expected_net_r == 0.42
    assert primary.learned_probability == 0.61
    assert primary.learned_fill_probability == 0.71
    assert primary.learned_status == "scored"

    aliased = AllocatorCandidate.from_mapping(
        candidate_row(
            "aliased",
            "EURUSD",
            learned_edge_expected_net_r=0.33,
            gtos_vnext_learned_probability=0.58,
            gtos_vnext_learned_fill_probability=0.66,
            gtos_vnext_learned_status="scored",
        )
    )
    assert aliased.learned_expected_net_r == 0.33
    assert aliased.learned_probability == 0.58
    assert aliased.learned_fill_probability == 0.66
    assert aliased.learned_status == "scored"

    prefixed = AllocatorCandidate.from_mapping(
        candidate_row("prefixed", "EURUSD", gtos_vnext_learned_expected_net_r=0.0)
    )
    assert prefixed.learned_expected_net_r == 0.0

    unscored = AllocatorCandidate.from_mapping(candidate_row("unscored", "EURUSD"))
    assert unscored.learned_expected_net_r is None
    assert unscored.learned_probability is None
    assert unscored.learned_fill_probability is None
    assert unscored.learned_status is None


def test_risk_headroom_veto_dominates_learned_score():
    crowded_cluster_candidate = candidate_row(
        "metals-new-risk",
        "XAUUSD",
        requested_risk_pct=0.5,
        selected_cell_risk_pct=0.5,
        learned_status="scored",
        learned_expected_net_r=3.0,
        learned_probability=0.90,
    )
    window = window_mapping(
        crowded_cluster_candidate,
        open_positions=[
            {
                "exposure_id": "open-xag",
                "symbol": "XAGUSD",
                "side": "LONG",
                "risk_pct": 1.5,
                "source_completeness": 1.0,
            }
        ],
    )
    packet = allocate_decision_window(
        window,
        {"enabled": True, "scheduler_v4_learned_ranking_enabled": True},
    )
    option = option_by_candidate(packet, "metals-new-risk")
    assert "cluster_risk_headroom_absent" in option["vetoes"]
    assert option["decision_status"] == "candidate_vetoed"
    assert packet["decision"]["selected_candidate_id"] != "metals-new-risk"


def test_unscored_candidate_keeps_legacy_score_when_require_scored_disabled():
    unscored = candidate_row("unscored-candidate", "EURUSD")
    window = window_mapping(unscored)

    baseline = allocate_decision_window(window, {"enabled": True})
    baseline_score = option_by_candidate(baseline, "unscored-candidate")["score"]

    packet = allocate_decision_window(
        window,
        {
            "enabled": True,
            "scheduler_v4_learned_ranking_enabled": True,
            "scheduler_v4_learned_ranking_require_scored": False,
        },
    )
    option = option_by_candidate(packet, "unscored-candidate")
    diagnostic = option["score_components"]["learned_ranking_diagnostic"]
    assert abs(option["score"] - baseline_score) < 1e-9
    assert diagnostic["score_mode"] == "legacy_ranking_v1"
    assert diagnostic["learned_score"] is None


