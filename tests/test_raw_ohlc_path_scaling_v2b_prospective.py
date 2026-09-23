from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts import evaluate_raw_ohlc_path_scaling_v2b_prospective as mod


SPEC = Path(
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json"
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"v2b_prospective_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _event(
    event_id: str,
    variant: str,
    net_r: float,
    *,
    clock: str = "2026-05-01T13:00:00+00:00",
    raw_cohort_key: str = "NAS100|ny|bullish|D1",
    role: str = "primary_controlled_child",
    selected_timeframe: str = "M1",
) -> dict:
    return {
        "schema_version": "raw_ohlc_path_scaling_v2_structural_level_event",
        "event_key": event_id,
        "candle_close_utc": clock,
        "variant_id": variant,
        "symbol": raw_cohort_key.split("|")[0],
        "session": raw_cohort_key.split("|")[1],
        "selected_timeframe": selected_timeframe,
        "mechanical_side": "LONG",
        "raw_cohort_key": raw_cohort_key,
        "role": role,
        "net_r_by_cost": {"0.05": net_r},
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _broad_positive_rows() -> list[dict]:
    rows = []
    cohorts = [
        ("NAS100|ny|bullish|D1", "primary_controlled_child", 0.20),
        ("XAUUSD|ny|bullish|D1", "primary_controlled_child", 0.20),
        ("USDJPY|tokyo|bearish|H4", "cleared_non_primary_strong_lead", 0.20),
        ("XAGUSD|ny|bearish|D1", "cleared_non_primary_strong_lead", 0.20),
        ("GBPUSD|ny|bearish|H4", "negative_control", 0.05),
        ("US30_cash|ny|bullish|D1", "dominance_watchlist", 0.10),
    ]
    for idx, (cohort, role, delta) in enumerate(cohorts):
        key = f"e{idx}"
        rows.append(_event(key, mod.BASELINE_VARIANT, 0.0, raw_cohort_key=cohort, role=role))
        rows.append(_event(key, mod.PRIMARY_VARIANT, delta, raw_cohort_key=cohort, role=role))
    return rows


def _summary(path: Path) -> Path:
    path.write_text(json.dumps({"coverage_diagnostics": {"lower_tf_start_violations": 0}}), encoding="utf-8")
    return path


def test_v2b_prospective_filters_out_same_event_rows(tmp_path):
    event_log = tmp_path / "events.jsonl"
    _write_jsonl(
        event_log,
        [
            _event("before", mod.BASELINE_VARIANT, 0.0, clock="2026-04-30T17:00:00+00:00"),
            _event("before", mod.PRIMARY_VARIANT, 1.0, clock="2026-04-30T17:00:00+00:00"),
        ],
    )

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=_summary(tmp_path / "summary.json"),
    )

    assert payload["validation_status"] == "BLOCKED_NO_POST_CUTOFF_ROWS"
    assert payload["diagnostics"]["pairwise_vs_j46"]["paired_resolved_n"] == 0
    assert payload["scope_counters"]["rows_rejected_at_or_before_cutoff"] == 2
    assert payload["status_ladder"][0]["status"] == "BLOCKED_NO_POST_CUTOFF_ROWS"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_v2b_prospective_distinguishes_post_cutoff_rows_without_wanted_rows(tmp_path):
    event_log = tmp_path / "events.jsonl"
    _write_jsonl(
        event_log,
        [
            _event("forward_irrelevant", "BASE_RAW_FIXED_TP", 0.1, selected_timeframe="M5"),
        ],
    )

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=_summary(tmp_path / "summary.json"),
    )

    assert payload["validation_status"] == "BLOCKED_NO_WANTED_POST_CUTOFF_ROWS"
    assert payload["scope_counters"]["rows_after_cutoff"] == 1
    assert payload["scope_counters"]["wanted_rows_after_cutoff"] == 0
    assert payload["status_ladder"][0]["status"] == "PASS"
    assert payload["status_ladder"][1]["status"] == "BLOCKED_NO_WANTED_POST_CUTOFF_ROWS"
    assert payload["row_diagnostics"]["lower_tf_availability"]["selected_timeframe_counts_after_cutoff"] == {"M5": 1}


def test_v2b_prospective_distinguishes_unresolved_forward_rows(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("forward_unresolved", mod.BASELINE_VARIANT, 0.0, selected_timeframe="M5"),
        _event("forward_unresolved", mod.PRIMARY_VARIANT, 0.0, selected_timeframe="M5"),
    ]
    for row in rows:
        row["net_r_by_cost"] = {"0.05": None}
    _write_jsonl(event_log, rows)

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=_summary(tmp_path / "summary.json"),
    )

    assert payload["validation_status"] == "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS"
    assert payload["scope_counters"]["rows_after_cutoff"] == 2
    assert payload["scope_counters"]["wanted_rows_after_cutoff"] == 2
    assert payload["scope_counters"]["wanted_resolved_rows_after_cutoff"] == 0
    assert payload["status_ladder"][2]["status"] == "BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS"
    assert payload["row_diagnostics"]["missing_net_r"]["by_variant"] == {
        mod.BASELINE_VARIANT: 1,
        mod.PRIMARY_VARIANT: 1,
    }
    assert payload["row_diagnostics"]["missing_net_r"]["by_selected_timeframe"] == {"M5": 2}
    assert payload["row_diagnostics"]["lower_tf_availability"]["wanted_lower_tf_rows_after_cutoff"] == 2
    assert "any prospective event rows" in payload["synthesis"]["answered_questions"][0]
    assert payload["synthesis"]["answered_questions"][0].endswith("Yes.")
    assert payload["synthesis"]["answered_questions"][2].endswith("No.")


def test_v2b_prospective_gate_passes_on_broad_positive_rows(tmp_path):
    event_log = tmp_path / "events.jsonl"
    _write_jsonl(event_log, _broad_positive_rows())

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=_summary(tmp_path / "summary.json"),
        min_all_enabled_n=6,
        min_target_n=4,
    )

    assert payload["validation_status"] == "RESEARCH_VALIDATION_PASS_NO_PROMOTION"
    assert all(gate["passed"] is True for gate in payload["acceptance_gates"].values())
    assert payload["status_ladder"][3]["status"] == "SAMPLE_FLOOR_REACHED"
    assert payload["diagnostics"]["cohort_breadth"]["positive_raw_cohort_count"] == 6
    assert payload["diagnostics"]["cohort_breadth"]["largest_positive_raw_cohort_share"] < 0.45


def test_v2b_prospective_reports_resolved_pairs_below_sample_floor(tmp_path):
    event_log = tmp_path / "events.jsonl"
    _write_jsonl(event_log, _broad_positive_rows())

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=_summary(tmp_path / "summary.json"),
        min_all_enabled_n=999,
        min_target_n=999,
    )

    assert payload["validation_status"] == "INTERIM_NOT_EVALUABLE_SAMPLE_FLOOR"
    assert payload["status_ladder"][2]["status"] == "PASS"
    assert payload["status_ladder"][3]["status"] == "BELOW_SAMPLE_FLOOR"
    assert payload["acceptance_gates"]["sample_floor"]["passed"] is False


def test_v2b_prospective_blocks_when_no_leak_summary_missing(tmp_path):
    event_log = tmp_path / "events.jsonl"
    _write_jsonl(event_log, _broad_positive_rows())

    payload = mod.build_payload(
        spec_path=SPEC,
        event_log_path=event_log,
        runner_summary_path=None,
        min_all_enabled_n=6,
        min_target_n=4,
    )

    assert payload["acceptance_gates"]["no_leak"]["passed"] is None
    assert payload["validation_status"] == "BLOCKED_BY_UNVERIFIED_METHODOLOGY_DIAGNOSTIC"
