from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROUTE_DIR = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
MODULE_PATH = ROUTE_DIR / "build_vnext_full_replay_stage06_terminal_metrics_2026_05_24.py"


def load_module():
    spec = importlib.util.spec_from_file_location("stage06_terminal_metrics", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_decision_promotes_positive_source_bound_slice():
    stage06 = load_module()
    row = {
        "candidate_count": 30,
        "dominance_row_count": 30,
        "best_available_r_metrics": {"mean_r": 0.35},
        "pollution_row_sums": {
            "source_required_rows": 0,
            "broad_unanchored_rows": 0,
            "stale_legacy_rows": 0,
        },
        "counterfactual_change_count": 0,
        "missed_winner_avoided_loser_counts": {
            "captured_winner": 12,
            "avoided_loser": 10,
            "missed_winner": 2,
            "accepted_loser": 3,
        },
    }

    decision, _rationale, next_action = stage06.classify_final_decision(row)

    assert decision == "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER"
    assert next_action == "promotion_candidate_requires_owner_review"


def test_final_decision_kills_counterfactual_sensitive_pollution():
    stage06 = load_module()
    row = {
        "candidate_count": 100,
        "best_available_r_metrics": {"mean_r": 0.1},
        "pollution_row_sums": {
            "source_required_rows": 0,
            "broad_unanchored_rows": 4,
            "stale_legacy_rows": 0,
        },
        "counterfactual_change_count": 3,
        "missed_winner_avoided_loser_counts": {},
    }

    decision, rationale, next_action = stage06.classify_final_decision(row)

    assert decision == "KILL_OR_REMOVE_NOISY_PRESSURE"
    assert "changes action" in rationale
    assert next_action == "pollution_remove_candidate"


def test_prop_path_computes_drawdown_and_daily_loss_breach():
    stage06 = load_module()
    events = [
        {"date": "2026-01-01", "time": "2026-01-01 10:00:00", "r": 1.0},
        {"date": "2026-01-01", "time": "2026-01-01 10:15:00", "r": -4.0},
        {"date": "2026-01-02", "time": "2026-01-02 10:00:00", "r": 2.0},
    ]

    metrics = stage06.simulate_prop_path(events, risk_pct=2.0)

    assert metrics["trade_count"] == 3
    assert metrics["daily_loss_breach"] is True
    assert metrics["max_drawdown_pct"] == 8.0
    assert metrics["final_return_pct"] == -2.0


def test_running_stats_reports_median_and_loss_streak():
    stage06 = load_module()
    stats = stage06.RunningStats()
    for value in [1.5, -1.0, -1.0, 0.0]:
        stats.update(value)

    metrics = stats.as_metrics()

    assert metrics["performance_count"] == 4
    assert metrics["median_r"] == -0.5
    assert metrics["max_loss_streak"] == 2
    assert metrics["max_drawdown_r"] == 2.0
