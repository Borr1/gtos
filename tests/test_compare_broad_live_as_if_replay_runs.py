import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/compare_broad_live_as_if_replay_runs.py"
)


def load_compare_module():
    spec = importlib.util.spec_from_file_location("compare_broad_replay", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def summary(prefix: str, trade_rows: int, net_r: float) -> dict:
    return {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "date_start": "2026-05-13",
        "date_end": "2026-05-17",
        "split_profile_stats": [
            {
                "trade_rows": trade_rows,
                "net_r": net_r,
                "gross_r": net_r,
                "final_r": net_r,
                "cash_pnl": net_r * 100.0,
            }
        ],
    }


def test_run_metrics_exposes_route_verifier_row_count_contract(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    prefix = "BROAD_LIVE_AS_IF_REPLAY_COUNTS"
    payload = summary(prefix, 2, 0.5)
    payload.update(
        {
            "candidate_rows": 7,
            "decision_rows": 11,
            "scorecard_rows": 5,
            "missed_opportunity_rows": 6,
        }
    )
    payload["split_profile_stats"][0].update(
        {
            "order_event_rows": 4,
            "order_rows": 3,
            "missed_opportunity_rows": 6,
        }
    )
    write_json(tmp_path / f"{prefix}_SUMMARY.json", payload)

    metrics = module.run_metrics(prefix)

    assert {
        key: metrics[key]
        for key in (
            "candidate_rows",
            "decision_rows",
            "scorecard_rows",
            "order_event_rows",
            "trades",
            "missed_rows",
        )
    } == {
        "candidate_rows": 7,
        "decision_rows": 11,
        "scorecard_rows": 5,
        "order_event_rows": 4,
        "trades": 2,
        "missed_rows": 6,
    }
    assert module.diff_metrics({"decision_rows": 3}, metrics)["decision_rows"] == 8


def test_run_metrics_prefers_serialized_physical_partition_without_flow_summary(
    tmp_path,
):
    module = load_compare_module()
    module.ROUTE = tmp_path
    prefix = "BROAD_LIVE_AS_IF_REPLAY_PHYSICAL_PARTITION"
    payload = summary(prefix, 6, 2.12544422)
    payload["split_profile_stats"][0].update(
        {
            "headline_trade_rows": 4,
            "headline_net_r": 2.12544422,
            "headline_gross_r": 2.43627912,
            "headline_final_r": 2.43627912,
            "headline_cash_pnl": 992.6201607,
            "physical_scoreable_trade_rows": 5,
            "physical_unscoreable_trade_rows": 1,
            "entry_fill_executable_terminal_r_unscoreable_trade_rows": 1,
            "physical_net_r": 4.03591467,
            "physical_gross_r": 4.43627912,
            "physical_final_r": 4.43627912,
            "physical_cash_pnl": 2204.18020365,
            "physical_risk_cash": 3027.8690165,
            "physical_risk_pct": 3.0,
            "physical_win_count": 4,
            "physical_loss_count": 1,
            "physical_flat_count": 0,
            # Legacy/headline aliases intentionally conflict with physical truth.
            "cash_pnl": 992.6201607,
            "risk_cash": 2142.02493426,
            "risk_pct": 2.125,
            "win_count": 3,
            "loss_count": 1,
            "flat_count": 0,
        }
    )
    write_json(tmp_path / f"{prefix}_SUMMARY.json", payload)

    metrics = module.run_metrics(prefix)

    assert metrics["headline_cash_pnl"] == 992.6201607
    assert {
        key: metrics[key]
        for key in (
            "physical_trades",
            "physical_scoreable_trades",
            "physical_unscoreable_trades",
            "entry_fill_executable_trades",
            "terminal_r_unscoreable_trades",
            "physical_net_r",
            "physical_gross_r",
            "physical_final_r",
            "physical_cash_pnl",
            "physical_risk_cash",
            "physical_risk_pct",
            "physical_wins",
            "physical_losses",
            "physical_flats",
        )
    } == {
        "physical_trades": 6,
        "physical_scoreable_trades": 5,
        "physical_unscoreable_trades": 1,
        "entry_fill_executable_trades": 6,
        "terminal_r_unscoreable_trades": 1,
        "physical_net_r": 4.03591467,
        "physical_gross_r": 4.43627912,
        "physical_final_r": 4.43627912,
        "physical_cash_pnl": 2204.18020365,
        "physical_risk_cash": 3027.8690165,
        "physical_risk_pct": 3.0,
        "physical_wins": 4,
        "physical_losses": 1,
        "physical_flats": 0,
    }


def test_compare_rolls_up_order_executable_transfer_inside_summary_window(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(tmp_path / f"{baseline}_SUMMARY.json", summary(baseline, 1, 1.0))
    write_json(tmp_path / f"{candidate}_SUMMARY.json", summary(candidate, 1, -1.0))
    write_json(
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_BASE_SUMMARY.json",
        {"exact_replay_window_transfer": {}},
    )
    write_json(
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_CANDIDATE_SUMMARY.json",
        {"exact_replay_window_transfer": {}},
    )

    for prefix, net_r in ((baseline, 1.0), (candidate, -1.0)):
        common = {
            "canonical_replay_candidate_instance_key": f"{prefix}-key",
            "candidate_id": f"{prefix}-candidate",
            "decision_time_utc": "2026-05-14T10:00:00Z",
            "symbol": "BTCUSD",
            "side": "LONG",
            "net_r": net_r,
            "gross_r": net_r,
            "final_r": net_r,
            "cash_pnl": net_r * 100.0,
            "package_replay_order_executable_candidate_use_allowed": True,
        }
        write_jsonl(
            tmp_path / f"{prefix}_TRADE_LEDGER.jsonl",
            [
                {
                    **common,
                    "package_replay_order_executable_transfer_status": "trade_bound",
                    "package_replay_order_executable_bound_trade_id": f"{prefix}-trade",
                },
                {
                    **common,
                    "canonical_replay_candidate_instance_key": f"{prefix}-outside",
                    "decision_time_utc": "2026-05-20T10:00:00Z",
                },
            ],
        )
        write_jsonl(
            tmp_path / f"{prefix}_ORDER_LEDGER.jsonl",
            [
                {
                    **common,
                    "order_time_utc": "2026-05-14T10:01:00Z",
                    "package_replay_order_executable_transfer_status": "order_bound",
                    "package_replay_order_executable_bound_order_id": f"{prefix}-order",
                }
            ],
        )
        write_jsonl(
            tmp_path / f"{prefix}_SCORECARD_LEDGER.jsonl",
            [
                {
                    **common,
                    "package_replay_order_executable_transfer_status": "final_blocked",
                    "package_replay_order_executable_final_blocker_class": "headroom",
                    "package_replay_order_executable_final_blocker_reason": "risk_headroom_zero",
                }
            ],
        )
        write_jsonl(
            tmp_path / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
            [
                {
                    **common,
                    "package_replay_order_executable_transfer_status": "final_blocked",
                    "package_replay_order_executable_final_blocker_class": "marketable_guard",
                    "package_replay_order_executable_final_blocker_reason": "marketable_guard_blocked",
                    "missed_opportunity_net_r": 2.5,
                }
            ],
        )

    result = module.compare(baseline, candidate)
    candidate_rollup = result["candidate_order_executable_transfer_rollup"]

    assert result["trade_key_counts"]["candidate"] == 1
    assert result["trade_key_counts"]["candidate_outside_summary_window"] == 1
    assert candidate_rollup["transfer_status_counts"] == {
        "missed:final_blocked": 1,
        "order:order_bound": 1,
        "scorecard:final_blocked": 1,
        "trade:trade_bound": 1,
    }
    assert candidate_rollup["blocker_counts"] == {
        "missed:marketable_guard": 1,
        "scorecard:headroom": 1,
    }
    assert candidate_rollup["unbound_allowed_counts"] == {}
    assert candidate_rollup["comparator_failures"] == {}


def test_row_in_summary_window_prefers_trading_day_at_midnight_boundary():
    module = load_compare_module()
    summary_row = {
        "date_start": "2026-06-01",
        "date_end": "2026-06-05",
    }

    assert module.row_in_summary_window(
        {
            "trading_day": "2026-06-05",
            "decision_time_utc": "2026-06-06T00:00:00Z",
        },
        summary_row,
    ) is True
    assert module.row_in_summary_window(
        {
            "trading_day": "2026-06-06",
            "decision_time_utc": "2026-06-05T23:59:59Z",
        },
        summary_row,
    ) is False


def test_trade_rollup_reports_risk_ladder_and_fill_realism_splits():
    module = load_compare_module()

    result = module.trade_rollup(
        [
            {
                "canonical_replay_candidate_instance_key": "full-pass",
                "decision_time_utc": "2026-05-14T10:00:00Z",
                "symbol": "XAUUSD",
                "side": "LONG",
                "route_session": "london",
                "net_r": 1.5,
                "gross_r": 1.7,
                "final_r": 1.6,
                "cash_pnl": -999.0,
                "pnl_cash": 175.0,
                "risk_cash": 100.0,
                "risk_expression_ladder": {
                    "ladder_tier": "full",
                    "tier_causes": ["signed_package_authority", "top_ranked"],
                },
                "fill_realism_class": "ordered_tick_entry_touch",
                "fill_realism_executable": True,
                "fill_realism_reason": "ordered_tick_truth_satisfied",
            },
            {
                "canonical_replay_candidate_instance_key": "reduced-proxy",
                "decision_time_utc": "2026-05-14T10:15:00Z",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "route_session": "ny",
                "net_r": -0.4,
                "gross_r": -0.2,
                "final_r": -0.3,
                "cash_pnl": -40.0,
                "risk_cash": 50.0,
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder_tier_causes": "headroom_limited|fill_floor_routed",
                "fill_realism_class": "m15_proxy",
                "fill_realism_executable": False,
                "fill_realism_reason": "postdecision_m15_proxy_not_executable_order_fill_truth",
            },
        ]
    )

    assert result["risk_ladder_tier_counts"] == {"full": 1, "reduced": 1}
    assert result["full_risk_count"] == 1
    assert result["reduced_risk_count"] == 1
    assert result["cash_pnl"] == 135.0
    assert result["ladder_cause_histogram"] == {
        "fill_floor_routed": 1,
        "headroom_limited": 1,
        "signed_package_authority": 1,
        "top_ranked": 1,
    }
    assert result["fill_realism_class_counts"] == {
        "m15_proxy": 1,
        "ordered_tick_entry_touch": 1,
    }
    assert result["fill_realism_executable_counts"] == {"False": 1, "True": 1}
    assert result["fill_realism_class_net_r"] == {
        "m15_proxy": -0.4,
        "ordered_tick_entry_touch": 1.5,
    }


def test_trade_rollup_counts_terminal_unscoreable_without_flat_or_r_claim() -> None:
    module = load_compare_module()

    result = module.trade_rollup(
        [
            {
                "symbol": "XAUUSD",
                "side": "LONG",
                "net_proxy_r": 1.0,
                "gross_r": 1.1,
                "final_r": 1.1,
                "pnl_cash": 100.0,
            },
            {
                "symbol": "XAUUSD",
                "side": "SHORT",
                "net_proxy_r": -0.5,
                "gross_r": -0.4,
                "final_r": -0.4,
                "pnl_cash": -50.0,
            },
            {
                "symbol": "XAUUSD",
                "side": "LONG",
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "net_proxy_r": None,
                "gross_r": None,
                "final_r": None,
                "pnl_cash": None,
            },
        ]
    )

    assert result["count"] == 3
    assert result["scoreable_count"] == 2
    assert result["unscoreable_count"] == 1
    assert result["terminal_r_unscoreable_count"] == 1
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["flats"] == 0
    assert result["net_r"] == 0.5
    assert result["gross_r"] == 0.7
    assert result["final_r"] == 0.7
    assert result["cash_pnl"] == 50.0


def test_behavior_dossier_separates_headline_from_all_physical_behavior():
    module = load_compare_module()
    result = {
        "window": "2026-06-01..2026-06-19",
        "baseline": {
            "prefix": "BASE",
            "headline_trades": 95,
            "headline_net_r": 22.8,
            "headline_gross_r": 28.7,
            "headline_final_r": 28.7,
            "headline_cash_pnl": 3098.0,
            "headline_wins": 52,
            "headline_losses": 43,
            "headline_flats": 0,
            "physical_trades": 95,
            "physical_net_r": 22.8,
            "physical_gross_r": 28.7,
            "physical_final_r": 28.7,
            "physical_cash_pnl": 3098.0,
            "physical_wins": 52,
            "physical_losses": 43,
            "physical_flats": 0,
        },
        "candidate": {
            "prefix": "CANDIDATE",
            "headline_trades": 4,
            "headline_net_r": 1.59,
            "headline_gross_r": 1.92,
            "headline_final_r": 1.92,
            "headline_cash_pnl": -67.9,
            "headline_wins": 3,
            "headline_losses": 1,
            "headline_flats": 0,
            "physical_trades": 42,
            "physical_net_r": 15.08,
            "physical_gross_r": 17.52,
            "physical_final_r": 17.52,
            "physical_cash_pnl": 188.9,
            "physical_wins": 23,
            "physical_losses": 19,
            "physical_flats": 0,
        },
        "summary_delta": {
            "headline_trades": -91,
            "headline_net_r": -21.21,
            "headline_gross_r": -26.78,
            "headline_final_r": -26.78,
            "headline_cash_pnl": -3165.9,
            "headline_wins": -49,
            "headline_losses": -42,
            "headline_flats": 0,
            "physical_trades": -53,
            "physical_net_r": -7.72,
            "physical_gross_r": -11.18,
            "physical_final_r": -11.18,
            "physical_cash_pnl": -2909.1,
            "physical_wins": -29,
            "physical_losses": -24,
            "physical_flats": 0,
        },
        "trade_identity_comparison_status": "not_computed_missing_baseline_trade_ledger",
        "added_trades": {},
        "removed_trades": {},
    }

    dossier = module.behavior_dossier(result)

    assert "Candidate headline: trades `4`, net `1.59`" in dossier
    assert "Candidate all physical: trades `42`, net `15.08`" in dossier
    assert "Headline delta: trades `-91`, net `-21.21`" in dossier
    assert "Physical delta: trades `-53`, net `-7.72`" in dossier


def test_compare_fails_when_summary_windows_differ(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    baseline_summary = summary(baseline, 0, 0.0)
    candidate_summary = summary(candidate, 0, 0.0)
    candidate_summary["date_end"] = "2026-05-18"
    write_json(tmp_path / f"{baseline}_SUMMARY.json", baseline_summary)
    write_json(tmp_path / f"{candidate}_SUMMARY.json", candidate_summary)

    try:
        module.compare(baseline, candidate)
    except ValueError as exc:
        assert "comparison_requires_same_summary_window" in str(exc)
    else:
        raise AssertionError("expected same-window comparison failure")


def test_compare_reads_baseline_and_candidate_from_distinct_artifact_roots(tmp_path):
    module = load_compare_module()
    baseline_root = tmp_path / "legacy"
    candidate_root = tmp_path / "active"
    baseline_root.mkdir()
    candidate_root.mkdir()
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(
        baseline_root / f"{baseline}_SUMMARY.json",
        summary(baseline, 1, 1.0),
    )
    write_json(
        candidate_root / f"{candidate}_SUMMARY.json",
        summary(candidate, 1, 2.0),
    )
    baseline_trade_path = baseline_root / f"{baseline}_TRADE_LEDGER.jsonl"
    candidate_trade_path = candidate_root / f"{candidate}_TRADE_LEDGER.jsonl"
    write_jsonl(
        baseline_trade_path,
        [
            {
                "canonical_replay_candidate_instance_key": "baseline-only",
                "decision_time_utc": "2026-05-14T10:00:00Z",
                "net_r": 1.0,
            }
        ],
    )
    write_jsonl(
        candidate_trade_path,
        [
            {
                "canonical_replay_candidate_instance_key": "candidate-only",
                "decision_time_utc": "2026-05-14T10:00:00Z",
                "net_r": 2.0,
            }
        ],
    )

    result = module.compare(
        baseline,
        candidate,
        baseline_root=baseline_root,
        candidate_root=candidate_root,
    )

    assert result["summary_delta"]["net_r"] == 1.0
    assert result["trade_key_counts"]["baseline"] == 1
    assert result["trade_key_counts"]["candidate"] == 1
    assert result["removed_trades"]["sample_keys"] == ["baseline-only"]
    assert result["added_trades"]["sample_keys"] == ["candidate-only"]
    assert result["removed_trade_keys"] == ["baseline-only"]
    assert result["added_trade_keys"] == ["candidate-only"]
    assert result["common_trade_keys"] == []
    assert result["artifacts"]["baseline_artifact_root"] == str(baseline_root)
    assert result["artifacts"]["candidate_artifact_root"] == str(candidate_root)
    assert result["trade_identity_comparison_authority"]["baseline"][
        "byte_count"
    ] == baseline_trade_path.stat().st_size
    assert result["trade_identity_comparison_authority"]["baseline"][
        "sha256"
    ] == module.sha256_file(baseline_trade_path)
    assert result["trade_identity_comparison_authority"]["candidate"][
        "byte_count"
    ] == candidate_trade_path.stat().st_size
    assert result["trade_identity_comparison_authority"]["candidate"][
        "sha256"
    ] == module.sha256_file(candidate_trade_path)


def test_compare_does_not_claim_trade_identity_delta_when_expected_ledger_missing(
    tmp_path,
):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(tmp_path / f"{baseline}_SUMMARY.json", summary(baseline, 1, 1.0))
    write_json(tmp_path / f"{candidate}_SUMMARY.json", summary(candidate, 1, 2.0))
    write_jsonl(
        tmp_path / f"{candidate}_TRADE_LEDGER.jsonl",
        [
            {
                "canonical_replay_candidate_instance_key": "candidate-only",
                "decision_time_utc": "2026-05-14T10:00:00Z",
                "net_r": 2.0,
            }
        ],
    )

    result = module.compare(baseline, candidate)

    assert result["trade_identity_comparison_status"] == (
        "not_computed_missing_baseline_trade_ledger"
    )
    assert result["trade_identity_comparison_authority"]["baseline"] == {
        "role": "baseline",
        "status": "missing_baseline_trade_ledger",
        "comparable": False,
        "path": str(tmp_path / f"{baseline}_TRADE_LEDGER.jsonl"),
        "path_present": False,
        "path_nonempty": False,
        "expected_rows_inside_summary_window": 1,
        "observed_rows_inside_summary_window": 0,
        "unique_identity_keys_inside_summary_window": 0,
        "duplicate_identity_rows_inside_summary_window": 0,
        "rows_outside_summary_window": 0,
    }
    assert result["trade_key_counts"]["candidate"] == 1
    assert result["trade_key_counts"]["common"] is None
    assert result["trade_key_counts"]["added"] is None
    assert result["trade_key_counts"]["removed"] is None
    assert result["added_trade_keys"] == []
    assert result["removed_trade_keys"] == []
    assert result["common_trade_keys"] == []
    assert result["added_transfer_net_positive"] is None
    assert result["removed_transfer_net_positive"] is None
    assert result["added_minus_removed_net_r"] is None
    assert result["removed_trade_current_projection_rollup"]["status"] == (
        "not_computed_missing_baseline_trade_ledger"
    )


def test_compare_classifies_every_removed_trade_against_current_projection(tmp_path):
    module = load_compare_module()
    baseline_root = tmp_path / "legacy"
    candidate_root = tmp_path / "active"
    baseline_root.mkdir()
    candidate_root.mkdir()
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(baseline_root / f"{baseline}_SUMMARY.json", summary(baseline, 3, 1.5))
    write_json(candidate_root / f"{candidate}_SUMMARY.json", summary(candidate, 0, 0.0))
    baseline_rows = [
        {
            "canonical_replay_candidate_instance_key": "candidate-missing@@2026-05-14T08:00:00Z",
            "candidate_id": "candidate-missing",
            "decision_time_utc": "2026-05-14T08:00:00Z",
            "symbol": "XAUUSD",
            "side": "LONG",
            "net_r": 2.0,
            "m1_proxy_replay_authority": True,
        },
        {
            "canonical_replay_candidate_instance_key": "selector-blocked@@2026-05-14T09:00:00Z",
            "candidate_id": "selector-blocked",
            "decision_time_utc": "2026-05-14T09:00:00Z",
            "symbol": "EURUSD",
            "side": "SHORT",
            "net_r": -1.0,
            "m1_proxy_replay_authority": True,
        },
        {
            "canonical_replay_candidate_instance_key": "fill-blocked@@2026-05-14T10:00:00Z",
            "candidate_id": "fill-blocked",
            "decision_time_utc": "2026-05-14T10:00:00Z",
            "symbol": "GER40",
            "side": "LONG",
            "net_r": 0.5,
            "headline_result_authority": True,
        },
    ]
    write_jsonl(baseline_root / f"{baseline}_TRADE_LEDGER.jsonl", baseline_rows)
    write_jsonl(candidate_root / f"{candidate}_TRADE_LEDGER.jsonl", [])
    projection_path = (
        candidate_root
        / "CANDIDATE_INSTANCE_PARITY_PROJECTION_CANDIDATE_LEDGER.jsonl"
    )
    write_jsonl(
        projection_path,
        [
            {
                "candidate_instance_parity_key": "selector-blocked@@2026-05-14T09:00:00Z",
                "decision_time_utc": "2026-05-14T09:00:00Z",
                "candidate_present": True,
                "exact_deviation_stage": "selector",
                "exact_deviation_reason": "selector_reject:cost_refused",
                "scorecard_present": False,
                "scheduler_selected": False,
                "order_present": False,
                "trade_present": False,
            },
            {
                "candidate_instance_parity_key": "fill-blocked@@2026-05-14T10:00:00Z",
                "decision_time_utc": "2026-05-14T10:00:00Z",
                "candidate_present": True,
                "exact_deviation_stage": "terminal_fallback",
                "exact_deviation_reason": "ordered_tick_truth_missing",
                "scorecard_present": True,
                "scheduler_selected": True,
                "order_present": True,
                "trade_present": False,
            },
        ],
    )

    result = module.compare(
        baseline,
        candidate,
        baseline_root=baseline_root,
        candidate_root=candidate_root,
    )
    rows = result["removed_trade_current_projection_rows"]
    rollup = result["removed_trade_current_projection_rollup"]

    assert len(rows) == 3
    assert rollup["candidate_projection_match_count"] == 2
    assert rollup["candidate_projection_missing_count"] == 1
    assert rollup["blocker_stage_counts"] == {
        "candidate_generation_absent_current_config": 1,
        "order_fillability_lifecycle": 1,
        "selector_admission": 1,
    }
    assert rollup["baseline_net_r_by_blocker_stage"] == {
        "candidate_generation_absent_current_config": 2.0,
        "order_fillability_lifecycle": 0.5,
        "selector_admission": -1.0,
    }
    assert rollup["baseline_result_authority_counts"] == {
        "m1_proxy_diagnostic_authority": 2,
        "ordered_tick_headline_authority": 1,
    }
    assert result["artifacts"]["candidate_instance_parity_projection"] == str(
        projection_path
    )


def test_compare_statuses_missing_axis_transfer_summary(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(tmp_path / f"{baseline}_SUMMARY.json", summary(baseline, 0, 0.0))
    write_json(tmp_path / f"{candidate}_SUMMARY.json", summary(candidate, 0, 0.0))

    result = module.compare(baseline, candidate)

    assert result["baseline_axis_transfer"] == {}
    assert result["candidate_axis_transfer"] == {}
    assert result["baseline_axis_transfer_status"]["status"] == (
        "missing_baseline_parity_summary"
    )
    assert result["candidate_axis_transfer_status"]["status"] == (
        "missing_candidate_parity_summary"
    )
    assert result["axis_transfer_delta_status"] == (
        "not_computed_missing_baseline_parity_summary_"
        "and_missing_candidate_parity_summary"
    )
    assert result["axis_transfer_delta"] == {}
    assert result["axis_transfer_scope_comparison"]["status"] == (
        "not_computed_axis_transfer_delta_not_computed"
    )
    assert result["axis_transfer_denominator_comparison"]["status"] == (
        "deprecated_non_additive_signal_not_denominator"
    )


def test_compare_computes_axis_transfer_delta_when_summaries_present(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    write_json(tmp_path / f"{baseline}_SUMMARY.json", summary(baseline, 0, 0.0))
    write_json(tmp_path / f"{candidate}_SUMMARY.json", summary(candidate, 0, 0.0))
    write_json(
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_BASE_SUMMARY.json",
        {
            "exact_replay_window_transfer": {
                "profiles": {
                    "repaired_package_conversion_v3": {
                        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 10.0,
                        "package_axes_available_inside_replay_window": 1101,
                        "filled_trade_axes": 2,
                    }
                }
            }
        },
    )
    write_json(
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_CANDIDATE_SUMMARY.json",
        {
            "exact_replay_window_transfer": {
                "profiles": {
                    "repaired_package_conversion_v3": {
                        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 14.5,
                        "package_axes_available_inside_replay_window": 1101,
                        "filled_trade_axes": 5,
                    }
                }
            }
        },
    )

    result = module.compare(baseline, candidate)

    assert result["baseline_axis_transfer_status"]["status"] == "present"
    assert result["candidate_axis_transfer_status"]["status"] == "present"
    assert result["axis_transfer_delta_status"] == "computed"
    assert result["axis_transfer_delta"][
        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
    ] == 4.5
    assert result["axis_transfer_delta"]["filled_trade_axes"] == 3
    assert result["axis_transfer_scope_comparison"]["status"] == (
        "same_window_axis_scope_values_differ"
    )
    assert result["axis_transfer_scope_comparison"]["field_deltas"][
        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
    ] == 4.5
    assert "package_axes_available_inside_replay_window" not in result[
        "axis_transfer_scope_comparison"
    ]["different_fields"]


def test_compare_finds_short_artifact_tag_parity_summary_by_broad_summary_path(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = (
        "BROAD_LIVE_AS_IF_REPLAY_V122I_FABLE_B4_HOSTILE_5D_FILL_REALISM_"
        "20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH"
    )

    write_json(tmp_path / f"{baseline}_SUMMARY.json", summary(baseline, 0, 0.0))
    write_json(tmp_path / f"{candidate}_SUMMARY.json", summary(candidate, 0, 0.0))
    write_json(
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_BASE_SUMMARY.json",
        {
            "artifacts": {"broad_replay_summary": str(tmp_path / f"{baseline}_SUMMARY.json")},
            "exact_replay_window_transfer": {
                "profiles": {
                    "repaired_package_conversion_v3": {
                        "source_bound_r_available": 10.0,
                        "filled_trade_axes": 1,
                    }
                }
            },
        },
    )
    write_json(
        tmp_path
        / "SOURCE_BOUND_TO_EXECUTED_PARITY_V122I_FABLE_B4_HOSTILE_5D_FILL_REALISM_SUMMARY.json",
        {
            "artifacts": {"broad_replay_summary": str(tmp_path / f"{candidate}_SUMMARY.json")},
            "exact_replay_window_transfer": {
                "profiles": {
                    "repaired_package_conversion_v3": {
                        "source_bound_r_available": 12.0,
                        "filled_trade_axes": 3,
                    }
                }
            },
        },
    )

    result = module.compare(baseline, candidate)

    assert result["candidate_axis_transfer_status"]["status"] == "present"
    assert result["candidate_axis_transfer_status"]["path"].endswith(
        "SOURCE_BOUND_TO_EXECUTED_PARITY_V122I_FABLE_B4_HOSTILE_5D_FILL_REALISM_SUMMARY.json"
    )
    assert result["axis_transfer_delta_status"] == "computed"
    assert result["axis_transfer_delta"]["filled_trade_axes"] == 2


def test_compare_behavior_artifact_stem_is_baseline_specific():
    module = load_compare_module()

    assert module.comparison_artifact_stem("CANDIDATE", "BASELINE_A") == (
        "CANDIDATE_VS_BASELINE_A"
    )
    assert module.comparison_artifact_stem("CANDIDATE", "BASELINE_B") == (
        "CANDIDATE_VS_BASELINE_B"
    )
    assert (
        module.comparison_artifact_stem("CANDIDATE", "BASELINE_A")
        != module.comparison_artifact_stem("CANDIDATE", "BASELINE_B")
    )

    long_candidate = "BROAD_LIVE_AS_IF_REPLAY_" + ("CANDIDATE_" * 20)
    long_baseline = "BROAD_LIVE_AS_IF_REPLAY_" + ("BASELINE_" * 20)
    long_stem = module.comparison_artifact_stem(long_candidate, long_baseline)
    assert len(long_stem) <= module.MAX_COMPARISON_ARTIFACT_STEM_CHARS
    assert module.comparison_artifact_stem(long_candidate, long_baseline) == long_stem
    assert long_stem != module.comparison_artifact_stem(
        long_candidate,
        long_baseline + "X",
    )


def test_compare_marks_missing_order_trade_transfer_status_as_failure(tmp_path):
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASE"
    candidate = "BROAD_LIVE_AS_IF_REPLAY_CANDIDATE"

    for prefix in (baseline, candidate):
        write_json(tmp_path / f"{prefix}_SUMMARY.json", summary(prefix, 1, 0.0))
        write_json(
            tmp_path / f"SOURCE_BOUND_TO_EXECUTED_PARITY_{prefix.removeprefix('BROAD_LIVE_AS_IF_REPLAY_')}_SUMMARY.json",
            {"exact_replay_window_transfer": {}},
        )
        row = {
            "canonical_replay_candidate_instance_key": f"{prefix}-key",
            "candidate_id": f"{prefix}-candidate",
            "decision_time_utc": "2026-05-14T10:00:00Z",
            "symbol": "BTCUSD",
            "side": "LONG",
            "package_replay_order_executable_candidate_use_allowed": True,
        }
        write_jsonl(tmp_path / f"{prefix}_TRADE_LEDGER.jsonl", [row])
        write_jsonl(tmp_path / f"{prefix}_ORDER_LEDGER.jsonl", [row])
        write_jsonl(tmp_path / f"{prefix}_SCORECARD_LEDGER.jsonl", [])
        write_jsonl(tmp_path / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl", [])

    result = module.compare(baseline, candidate)
    failures = result["candidate_order_executable_transfer_rollup"][
        "comparator_failures"
    ]

    assert failures["order:order_executable_true_without_transfer_status"] == 1
    assert failures["trade:order_executable_true_without_transfer_status"] == 1
