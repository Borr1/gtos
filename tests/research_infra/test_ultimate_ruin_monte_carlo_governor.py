"""Focused tests for the ruin-aware Monte Carlo engine + governor calibration."""

from __future__ import annotations

import json
from pathlib import Path

from src.components.risk_governor_v4 import GovernorConfigV4
from src.research_infra.ultimate_ruin_monte_carlo_governor import (
    BOUNDARY,
    DAY_RECORD_SCHEMA_VERSION,
    EVENT_KIND_FILLED,
    EVENT_KIND_NOT_FILLED,
    EVENT_KIND_RISK_REJECTED,
    build_day_records,
    calibrate,
    cluster_correlation_lookup,
    hash_uniform,
    main,
    simulate_paths,
    wilson_upper_bound,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# Synthetic ledger route dir (filled + risk-rejected + accepted-not-filled)
# ---------------------------------------------------------------------------


def _synthetic_route_dir(tmp_path: Path) -> Path:
    route = tmp_path / "route"
    prefix = "ULTIMATE_ROLLING_DYNAMIC_20260508"
    # candidate ledger must exist for discover_partition_ledgers to keep the day
    _write_jsonl(route / f"{prefix}_CANDIDATE_MICROSCOPE_LEDGER.jsonl", [
        {"candidate_id": "c_filled", "trading_day": "2026-05-08"},
    ])
    _write_jsonl(route / f"{prefix}_SIMULATED_ORDER_LEDGER.jsonl", [
        {
            "candidate_id": "c_filled",
            "simulated_order_id": "o1",
            "order_status": "filled",
            "symbol": "GBPJPY",
            "side": "LONG",
            "decision_time_utc": "2026-05-08T00:30:00+00:00",
            "fill_time_utc": "2026-05-08T00:31:00+00:00",
            "requested_risk_pct": 0.5,
            "risk_pct": 0.5,
            "trading_day": "2026-05-08",
        },
        {
            "candidate_id": "c_rejected",
            "simulated_order_id": "o2",
            "order_status": "risk_rejected",
            "symbol": "EURUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-08T01:00:00+00:00",
            "requested_risk_pct": 0.0,  # replay allocator approved zero
            "scheduler_approved_risk_pct": 1.5,
            "selected_cell_risk_pct": 2.0,
            "risk_per_trade_pct": 2.0,
            "counterfactual_fill_status": "filled_from_ordered_m1_path",
            "counterfactual_final_r": -1.0,
            "expiry_utc": "2026-05-08T03:00:00+00:00",
            "trading_day": "2026-05-08",
        },
        {
            "candidate_id": "c_unfilled",
            "simulated_order_id": "o3",
            "order_status": "accepted_not_filled_pending_until_expiry",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "decision_time_utc": "2026-05-08T02:00:00+00:00",
            "requested_risk_pct": 0.5,
            "expiry_utc": "2026-05-08T04:00:00+00:00",
            "trading_day": "2026-05-08",
        },
    ])
    _write_jsonl(route / f"{prefix}_SIMULATED_TRADE_LEDGER.jsonl", [
        {
            "candidate_id": "c_filled",
            "simulated_order_id": "o1",
            "net_proxy_r": 0.8,
            "net_r": 0.8,
            "mae_r": -0.4,
            "be_reached": False,
            "fill_time_utc": "2026-05-08T00:31:00+00:00",
            "exit_time_utc": "2026-05-08T01:30:00+00:00",
            "risk_pct": 0.5,
            "trading_day": "2026-05-08",
        },
    ])
    _write_jsonl(route / f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl", [
        {
            "candidate_id": "c_rejected",
            "fill_status": "not_sent_risk_rejected",
            "counterfactual_fill_status": "filled_from_ordered_m1_path",
            "counterfactual_final_r": -1.0,
            "mae_r": -1.2,
            "fill_time_utc": "2026-05-08T01:05:00+00:00",
            "close_mark_time_utc": "2026-05-08T02:10:00+00:00",
        },
    ])
    return route


# ---------------------------------------------------------------------------
# Hand-built day records (engine-level tests need no files)
# ---------------------------------------------------------------------------


def _event(
    candidate_id: str,
    decision_time: str,
    exit_time: str,
    *,
    requested: float,
    final_r: float | None,
    mae_r: float | None,
    cluster: str = "fx",
    filled: bool = True,
    be_reached: bool = False,
    kind: str = EVENT_KIND_FILLED,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "fill_time_utc": decision_time,
        "exit_time_utc": exit_time,
        "symbol": "EURUSD",
        "cluster": cluster,
        "side": "LONG",
        "requested_risk_pct": requested,
        "final_r": final_r,
        "mae_r": mae_r,
        "be_reached": be_reached,
        "filled": filled,
        "was_risk_rejected": kind == EVENT_KIND_RISK_REJECTED,
        "event_kind": kind,
    }


def _day(events: list[dict], *, trading_day: str = "2026-05-08") -> dict:
    return {
        "schema_version": DAY_RECORD_SCHEMA_VERSION,
        "campaign": "TEST",
        "trading_day": trading_day,
        "events": events,
        "n_events": len(events),
        **BOUNDARY,
    }


def _good_day() -> dict:
    # two sequential winners, shallow mae
    return _day(
        [
            _event("g1", "2026-05-11T09:00:00+00:00", "2026-05-11T10:00:00+00:00",
                   requested=1.0, final_r=1.0, mae_r=-0.2),
            _event("g2", "2026-05-11T11:00:00+00:00", "2026-05-11T12:00:00+00:00",
                   requested=1.0, final_r=1.0, mae_r=-0.2),
        ],
        trading_day="2026-05-11",
    )


def _bad_day() -> dict:
    # two OVERLAPPING deep-mae events: harmless at low risk scale, daily
    # breach territory once the scale multiplies the open heat
    return _day(
        [
            _event("b1", "2026-05-12T09:00:00+00:00", "2026-05-12T12:00:00+00:00",
                   requested=1.0, final_r=-0.2, mae_r=-2.0),
            _event("b2", "2026-05-12T09:30:00+00:00", "2026-05-12T12:30:00+00:00",
                   requested=1.0, final_r=-0.2, mae_r=-2.0),
        ],
        trading_day="2026-05-12",
    )


def _catastrophic_day() -> dict:
    # three overlapping events whose conservative mae lows pierce the -5%
    # daily limit as soon as the first 2.0% slice is admitted (2.0 * 2.6R)
    return _day(
        [
            _event("c1", "2026-05-08T10:00:00+00:00", "2026-05-08T12:00:00+00:00",
                   requested=2.0, final_r=-2.5, mae_r=-2.6),
            _event("c2", "2026-05-08T10:05:00+00:00", "2026-05-08T12:10:00+00:00",
                   requested=2.0, final_r=-2.5, mae_r=-2.6),
            _event("c3", "2026-05-08T10:10:00+00:00", "2026-05-08T12:20:00+00:00",
                   requested=2.0, final_r=-2.5, mae_r=-2.6),
        ]
    )


# ---------------------------------------------------------------------------
# build_day_records
# ---------------------------------------------------------------------------


def test_build_day_records_joins_orders_trades_and_counterfactuals(tmp_path):
    records = build_day_records([_synthetic_route_dir(tmp_path)])
    assert len(records) == 1
    record = records[0]
    assert record["schema_version"] == DAY_RECORD_SCHEMA_VERSION
    assert record["campaign"] == "ULTIMATE_ROLLING_DYNAMIC"
    assert record["trading_day"] == "2026-05-08"
    assert record["n_events"] == 3
    assert record["n_filled_replay"] == 1
    assert record["n_risk_rejected_counterfactual"] == 1
    assert record["n_accepted_not_filled"] == 1
    for key, value in BOUNDARY.items():
        assert record[key] is value

    events = {event["candidate_id"]: event for event in record["events"]}
    filled = events["c_filled"]
    assert filled["event_kind"] == EVENT_KIND_FILLED
    assert filled["filled"] is True
    assert filled["final_r"] == 0.8
    assert filled["mae_r"] == -0.4
    assert filled["requested_risk_pct"] == 0.5
    assert filled["cluster"] == "jpy_fx"
    assert filled["exit_time_utc"] == "2026-05-08T01:30:00+00:00"

    rejected = events["c_rejected"]
    assert rejected["event_kind"] == EVENT_KIND_RISK_REJECTED
    assert rejected["was_risk_rejected"] is True
    assert rejected["filled"] is True  # counterfactual path filled
    assert rejected["final_r"] == -1.0
    assert rejected["mae_r"] == -1.2
    # replay requested 0.0 -> falls back to scheduler_approved_risk_pct
    assert rejected["requested_risk_pct"] == 1.5
    assert rejected["exit_time_utc"] == "2026-05-08T02:10:00+00:00"

    unfilled = events["c_unfilled"]
    assert unfilled["event_kind"] == EVENT_KIND_NOT_FILLED
    assert unfilled["filled"] is False
    assert unfilled["final_r"] is None


def test_rejected_counterfactual_reenters_under_new_governor():
    rejected_only = _day(
        [
            _event("r1", "2026-05-08T09:00:00+00:00", "2026-05-08T10:00:00+00:00",
                   requested=1.5, final_r=-1.0, mae_r=-1.2,
                   kind=EVENT_KIND_RISK_REJECTED),
        ]
    )
    result = simulate_paths(
        [rejected_only], GovernorConfigV4(), n_paths=10, horizon_days=3, seed=3
    )
    # the replay-rejected order trades in every sampled day and loses 1.5%
    assert result["e_daily_r"] == -1.5
    assert result["day_outcomes"][0]["n_admitted"] == 1


# ---------------------------------------------------------------------------
# Simulation determinism + breach detection
# ---------------------------------------------------------------------------


def test_simulation_same_seed_is_byte_identical():
    records = [_good_day(), _bad_day()]
    cfg = GovernorConfigV4()
    first = simulate_paths(records, cfg, n_paths=50, horizon_days=10, seed=42)
    second = simulate_paths(records, cfg, n_paths=50, horizon_days=10, seed=42)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_hash_rng_depends_only_on_seed_and_counter():
    assert hash_uniform(7, "day_sample", 0, 0) == hash_uniform(7, "day_sample", 0, 0)
    assert hash_uniform(7, "day_sample", 0, 0) != hash_uniform(8, "day_sample", 0, 0)
    value = hash_uniform(123, "x", 1)
    assert 0.0 <= value < 1.0


def test_catastrophic_day_must_breach_daily_limit():
    result = simulate_paths(
        [_catastrophic_day()], GovernorConfigV4(), n_paths=20, horizon_days=5, seed=7
    )
    assert result["p_any_daily_breach_horizon"] == 1.0
    assert result["p_daily_breach_per_day"] > 0.0
    assert result["counts"]["breach_days"] > 0
    assert result["p_overall_10pct"] == 1.0  # repeated -5% days ruin the path
    outcome = result["day_outcomes"][0]
    assert outcome["breached"] is True
    assert outcome["conservative_low_pct"] <= -5.0


def test_good_day_only_never_breaches():
    result = simulate_paths(
        [_good_day()], GovernorConfigV4(), n_paths=20, horizon_days=10, seed=9
    )
    assert result["p_daily_breach_per_day"] == 0.0
    assert result["p_any_daily_breach_horizon"] == 0.0
    assert result["p_overall_10pct"] == 0.0
    assert result["e_daily_r"] > 0.0
    assert result["e_log_growth"] > 0.0


def test_empty_day_records_fail_explicit():
    result = simulate_paths([], GovernorConfigV4(), n_paths=10, horizon_days=5, seed=1)
    assert result["status"] == "no_day_records_or_empty_horizon"
    for key, value in BOUNDARY.items():
        assert result[key] is value


def test_simulation_result_carries_boundary_stamps():
    result = simulate_paths(
        [_good_day()], GovernorConfigV4(), n_paths=5, horizon_days=2, seed=1
    )
    for key, value in BOUNDARY.items():
        assert result[key] is value
    assert result["evidence_class"] == (
        "post_asof_timewarp_replay_label_not_decision_input"
    )


# ---------------------------------------------------------------------------
# Wilson bound
# ---------------------------------------------------------------------------


def test_wilson_upper_bound_behaviour():
    assert wilson_upper_bound(0, 0) == 1.0
    assert wilson_upper_bound(0, 4000) < 0.001
    assert wilson_upper_bound(1, 1000) > wilson_upper_bound(0, 1000)
    assert wilson_upper_bound(1000, 1000) == 1.0


# ---------------------------------------------------------------------------
# Calibration (common random numbers; tighter target -> lower risk scale)
# ---------------------------------------------------------------------------


def test_calibration_tightening_target_picks_lower_risk_scale():
    records = [_good_day(), _bad_day()]
    shared = dict(
        n_paths=200, horizon_days=20, seed=11, kappa_grid=(0.5,), reserve_grid=(0.5,)
    )
    loose = calibrate(records, target_p_daily=1.0, **shared)
    tight = calibrate(records, target_p_daily=0.001, **shared)

    assert loose["best"] is not None and tight["best"] is not None
    assert tight["best"]["risk_scale"] < loose["best"]["risk_scale"]
    assert tight["best"]["risk_scale"] <= 1.0  # scales >=1.5 breach on the bad day
    assert tight["n_feasible"] < len(tight["frontier"])
    for row in tight["frontier"]:
        if row["risk_scale"] >= 1.5:
            assert row["feasible"] is False
    # common random numbers: identical theta rows across the two runs
    assert loose["frontier"][0]["p_daily_breach_per_day"] == (
        tight["frontier"][0]["p_daily_breach_per_day"]
    )
    for key, value in BOUNDARY.items():
        assert tight[key] is value


def test_count_cap_ablation_runs_all_caps_with_deltas():
    result = calibrate(
        [_good_day(), _bad_day()],
        target_p_daily=1.0,
        n_paths=50,
        horizon_days=10,
        seed=5,
        risk_scale_grid=(1.0,),
        kappa_grid=(0.5,),
        reserve_grid=(0.5,),
        count_caps=(None, 3, 5),
    )
    rows = result["count_cap_ablation"]["rows"]
    assert [row["max_concurrent_cap"] for row in rows] == [None, 3, 5]
    for row in rows:
        assert row["p_daily_breach_per_day"] is not None
        assert "delta_e_log_growth_vs_uncapped" in row
        assert "delta_p_daily_breach_vs_uncapped" in row
    uncapped = rows[0]
    assert uncapped["delta_e_log_growth_vs_uncapped"] == 0.0


def test_cluster_correlation_lookup_overrides():
    lookup = cluster_correlation_lookup({"fx|jpy_fx": 0.9})
    assert lookup("fx", "fx") == 1.0
    assert lookup("jpy_fx", "fx") == 0.9
    assert lookup("fx", "crypto") == 0.25  # documented default constant


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_main_writes_report(tmp_path, capsys):
    route = _synthetic_route_dir(tmp_path)
    out = tmp_path / "out" / "ruin_mc.json"
    exit_code = main(
        [
            "--route-dir", str(route),
            "--out", str(out),
            "--paths", "20",
            "--horizon", "5",
            "--seed", "13",
        ]
    )
    assert exit_code == 0
    payload = json.loads(out.read_text())
    assert payload["schema_version"] == "ultimate_ruin_mc_report_v1"
    assert payload["n_day_records"] == 1
    assert payload["simulation"]["status"] == "simulated"
    for key, value in BOUNDARY.items():
        assert payload[key] is value
    headline = json.loads(capsys.readouterr().out.strip())
    assert headline["n_day_records"] == 1
    assert "p_daily_breach_per_day" in headline
