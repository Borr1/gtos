"""`accepted` must be computed, never asserted. These tests try to forge a green.

`accept.build_receipt` is the instrument that decides whether the train lane
ships. Three ways a receipt could look green while meaning nothing are closed in
the code; each has a test here that tries to open it again.
"""

from __future__ import annotations

from src.research_infra.train_engine import accept, identity


def _trade(**overrides: object) -> dict[str, object]:
    row = {
        "candidate_id": "broadorigin_a47895e43883d1a0c1059541",
        "decision_time_utc": "2026-01-02T07:15:00+00:00",
        "symbol": "XAUUSD",
        "direction": "SHORT",
        "entry_time_utc": "2026-01-02T07:15:00+00:00",
        "entry_price": 4377.82,
        "exit_time_utc": "2026-01-02T07:54:24.605000+00:00",
        "close_reason": "selected_policy_replay:stop_loss",
        "final_r": -1.0,
        "cost_r": 0.09544224,
        "net_r": -1.09544224,
        "risk_cash": 250.0,
        "approved_risk_pct": 0.25,
        "headline_result_exclusion_reason": "headline_result_eligible",
    }
    row.update(overrides)
    return row


_POOL = {"rows": 8807, "diagnostic_scoreable_rows": 1539, "positive_net_r": 335.8}


def _economics(trades=None) -> dict[str, object]:
    return {
        "trades": list(trades if trades is not None else [_trade()]),
        "orders": [],
        "counts": {"trade": 1, "order": 0, "scorecard": 96, "missed": 8807},
        "missed_digest": dict(_POOL),
    }


def _report(**overrides: object) -> dict[str, object]:
    report = {
        "arm": "S1R1",
        "window_start": "2026-01-01",
        "stop_after_day": "2026-01-02",
        "wall_seconds": 441.7,
        "rusage": {"maxrss_bytes": 3_110_000_000},
        "receipt_counts": dict(accept.PUBLISHED_FIXTURE_COUNTS),
        "progress_rows": [
            {"start_day": "2026-01-02", "economic_hot_path_seconds": 385.2}
        ],
        "error": None,
        "patches_applied": ["authority_hash_content_memo"],
    }
    report.update(overrides)
    return report


def _baseline(**overrides: object) -> dict[str, object]:
    report = _report(wall_seconds=657.0)
    report["rusage"] = {"maxrss_bytes": 8_310_000_000}
    report["progress_rows"] = [
        {"start_day": "2026-01-02", "economic_hot_path_seconds": 525.5}
    ]
    report["patches_applied"] = []
    report.update(overrides)
    return report


def test_a_clean_pair_is_accepted_and_the_ratios_are_computed() -> None:
    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics(),
    )
    assert receipt["accepted"] is True
    assert receipt["refusals"] == []
    assert receipt["outcome_identity"]["verdict"] == "OUTCOME_IDENTICAL"
    assert receipt["speed"]["wall_speedup_x"] == round(657.0 / 441.7, 4)
    assert receipt["speed"]["maxrss_ratio"] == round(3.11e9 / 8.31e9, 4)
    assert receipt["speed"]["hot_path_speedup_x"] == round(525.5 / 385.2, 4)


def test_a_moved_trade_refuses() -> None:
    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics([_trade(net_r=-1.1)]),
    )
    assert receipt["accepted"] is False
    assert "outcome_identity_failed" in receipt["refusals"]


def test_an_errored_run_refuses_even_when_the_trades_match() -> None:
    """A run that raised after writing its ledgers would otherwise compare
    clean against itself."""

    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(error="Traceback ..."),
        candidate_economics=_economics(),
    )
    assert receipt["accepted"] is False
    assert "candidate_run_errored" in receipt["refusals"]

    receipt = accept.build_receipt(
        baseline=_baseline(error="Traceback ..."),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics(),
    )
    assert "baseline_run_errored" in receipt["refusals"]


def test_a_baseline_that_is_not_the_published_fixture_cannot_license_anything() -> None:
    """Two runs of a DIFFERENT window would compare identical to each other and
    say nothing about the fixture the estate has published counts for."""

    wrong = dict(accept.PUBLISHED_FIXTURE_COUNTS)
    wrong["trade_rows"] = 4
    receipt = accept.build_receipt(
        baseline=_baseline(receipt_counts=wrong),
        baseline_economics=_economics(),
        candidate=_report(receipt_counts=wrong),
        candidate_economics=_economics(),
    )
    assert receipt["accepted"] is False
    assert "baseline_is_not_the_published_fixture" in receipt["refusals"]


def test_the_published_fixture_counts_are_the_ones_the_estate_publishes() -> None:
    assert accept.PUBLISHED_FIXTURE_COUNTS == {
        "candidate_rows": 8812,
        "order_rows": 10,
        "trade_rows": 5,
        "scorecard_rows": 96,
        "missed_opportunity_rows": 8807,
    }


def test_the_receipt_says_it_is_not_an_arm_of_record() -> None:
    """H5: --days sets engineering_stop_after_day, which the sealed path
    hardcodes to None. Every receipt must carry that, not rely on memory."""

    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics(),
    )
    assert receipt["fixture"]["is_sealed_arm_of_record"] is False
    assert "TRAINING_EVIDENCE" in receipt["evidence_class"]
    assert "H5" in receipt["fixture"]["bounded_fixture_note"]


def test_the_profiler_asymmetry_is_declared_rather_than_left_to_the_reader() -> None:
    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(profile={"samples": 11897}),
        candidate_economics=_economics(),
    )
    assert receipt["speed"]["candidate_profiled"] is True
    assert "LOWER bound" in receipt["speed"]["profiler_overhead_note"]


def test_no_profiler_means_no_spurious_caveat() -> None:
    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics(),
    )
    assert receipt["speed"]["profiler_overhead_note"] == ""


def test_the_residual_map_reports_shares_of_wall_not_raw_seconds_alone() -> None:
    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(
            profile={
                "samples": 100,
                "self_seconds": {"a.py:f:1": 44.17},
                "cumulative_seconds": {"a.py:f:1": 88.34},
            }
        ),
        candidate_economics=_economics(),
    )
    residual = receipt["residual_map"]
    assert residual["top_self_time"][0]["share_of_wall"] == 0.1
    assert residual["top_cumulative"][0]["share_of_wall"] == 0.2


def test_the_tuple_version_travels_with_the_verdict() -> None:
    """An acceptance claim must never be readable against a tuple it was not
    measured under."""

    receipt = accept.build_receipt(
        baseline=_baseline(),
        baseline_economics=_economics(),
        candidate=_report(),
        candidate_economics=_economics(),
    )
    assert receipt["outcome_identity"]["tuple_version"] == identity.TUPLE_VERSION
