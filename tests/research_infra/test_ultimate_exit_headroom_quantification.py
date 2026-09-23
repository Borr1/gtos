"""Focused tests for the exit headroom quantification (coarse anatomy pass)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.ultimate_exit_headroom_quantification import (
    GO_THRESHOLD_R_PER_DAY,
    abort_rule_fires,
    build_headroom_report,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _milestones(reached_025: str | None = None, reached_05: str | None = None) -> dict:
    return {
        "0.25r": {"reached": reached_025 is not None, "first_touch_utc": reached_025},
        "0.5r": {"reached": reached_05 is not None, "first_touch_utc": reached_05},
    }


def test_abort_rule_time_ordering():
    # Loser: MAE -0.9 at 02:45, never reached 0.25R -> rule fires.
    loser = {
        "mae_r": -0.9,
        "mae_time_utc": "2026-05-15T02:45:00+00:00",
        "milestones": _milestones(),
    }
    assert abort_rule_fires(loser, abort_r=0.6, progress_floor_r=0.25) is True
    # Winner: 0.25R touched BEFORE the MAE extreme -> rule must NOT fire.
    winner = {
        "mae_r": -0.9,
        "mae_time_utc": "2026-05-15T03:00:00+00:00",
        "milestones": _milestones(reached_025="2026-05-15T02:30:00+00:00"),
    }
    assert abort_rule_fires(winner, abort_r=0.6, progress_floor_r=0.25) is False
    # Winner whose progress came AFTER the adverse extreme -> killed.
    late_winner = {
        "mae_r": -0.9,
        "mae_time_utc": "2026-05-15T02:00:00+00:00",
        "milestones": _milestones(reached_025="2026-05-15T04:00:00+00:00"),
    }
    assert abort_rule_fires(late_winner, abort_r=0.6, progress_floor_r=0.25) is True
    # MAE shallower than the abort threshold -> never fires.
    shallow = {"mae_r": -0.3, "mae_time_utc": None, "milestones": _milestones()}
    assert abort_rule_fires(shallow, abort_r=0.6, progress_floor_r=0.25) is False
    # Missing MAE timestamp with reached milestone -> conservative non-fire.
    no_time = {
        "mae_r": -0.9,
        "mae_time_utc": None,
        "milestones": _milestones(reached_025="2026-05-15T02:30:00+00:00"),
    }
    assert abort_rule_fires(no_time, abort_r=0.6, progress_floor_r=0.25) is False


def _make_route(tmp_path: Path) -> Path:
    route = tmp_path / "route"
    prefix, day = "ULTIMATE_ROLLING_DYNAMIC", "20260515"
    _write_jsonl(
        route / f"{prefix}_{day}_CANDIDATE_MICROSCOPE_LEDGER.jsonl",
        [
            {"candidate_id": "w1", "symbol": "XAUUSD", "origin_family": "displacement_continuation",
             "session_bucket": "london", "trading_day": "2026-05-15"},
            {"candidate_id": "l1", "symbol": "XAUUSD", "origin_family": "displacement_continuation",
             "session_bucket": "london", "trading_day": "2026-05-15"},
        ],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_SIMULATED_TRADE_LEDGER.jsonl",
        [
            {"candidate_id": "w1", "milestones": _milestones(reached_025="2026-05-15T02:30:00+00:00")},
            {"candidate_id": "l1", "milestones": _milestones()},
        ],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_WINNER_ANATOMY_LEDGER.jsonl",
        [{
            "candidate_id": "w1", "symbol": "XAUUSD", "trading_day": "2026-05-15",
            "final_r": 2.0, "mfe_r": 2.6, "giveback_r": 0.6, "mae_r": -0.2,
            "mae_time_utc": "2026-05-15T02:20:00+00:00",
        }],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_LOSER_ANATOMY_LEDGER.jsonl",
        [{
            "candidate_id": "l1", "symbol": "XAUUSD", "trading_day": "2026-05-15",
            "final_r": -1.0, "mfe_r": 0.1, "mae_r": -1.2,
            "mae_time_utc": "2026-05-15T03:00:00+00:00",
            "avoidability": "early_adverse_candidate",
        }],
    )
    _write_jsonl(
        route / f"{prefix}_{day}_EXIT_GEOMETRY_HARVEST_LEDGER.jsonl",
        [
            {"candidate_id": "w1", "symbol": "XAUUSD", "final_r": 2.0,
             "counterfactual_final_r": 2.3, "counterfactual_path_scored": True},
            {"candidate_id": "x1", "symbol": "EURUSD", "final_r": None,
             "counterfactual_final_r": -1.0, "counterfactual_path_scored": True},
        ],
    )
    _write_jsonl(route / f"{prefix}_{day}_MISSED_OPPORTUNITY_LEDGER.jsonl", [])
    _write_jsonl(route / f"{prefix}_{day}_ORDERED_PATH_ORACLE_LEDGER.jsonl", [])
    _write_jsonl(route / f"{prefix}_{day}_SIMULATED_ORDER_LEDGER.jsonl", [])
    return route


def test_headroom_report_math(tmp_path):
    report = build_headroom_report([_make_route(tmp_path)])
    assert report["winners"] == 1
    assert report["losers"] == 1
    assert report["n_trading_days"] == 1
    # Winner giveback 0.6 captured.
    assert report["winner_giveback_global"]["sum"] == pytest.approx(0.6)
    # Harvest delta only from the row with both actual and counterfactual: +0.3.
    assert report["harvest_counterfactual_global"]["positive_delta_sum_r"] == pytest.approx(0.3)
    # Abort rule x=0.6/p=0.25: loser fires (saved 0.4), winner safe (0.25R before MAE,
    # and winner MAE -0.2 is shallower anyway) -> net +0.4.
    grid = {(row["abort_r"], row["progress_floor_r"]): row for row in report["abort_rule_grid"]}
    rule = grid[(0.6, 0.25)]
    assert rule["losers_fired"] == 1
    assert rule["winners_killed"] == 0
    assert rule["net_headroom_r"] == pytest.approx(0.4)
    # Global headroom per day = giveback 0.6 + harvest 0.3 + best abort net.
    best = report["best_abort_rule"]["net_headroom_r"]
    assert report["global_headroom_r_per_day"] == pytest.approx(0.6 + 0.3 + best)
    # Family go/no-go present for metals with the documented threshold.
    fam = {row["asset_class"]: row for row in report["family_go_no_go"]}
    assert "metals" in fam
    assert fam["metals"]["tournament_go"] == (
        fam["metals"]["headroom_r_per_day"] >= GO_THRESHOLD_R_PER_DAY
    )
    # Avoidability tally carried through.
    assert report["loser_avoidability_counts"] == {"early_adverse_candidate": 1}
    # Boundary stamps.
    assert report["broker_runtime_change_status"] is False
