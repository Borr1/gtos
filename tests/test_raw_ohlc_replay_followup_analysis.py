import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.analyze_raw_ohlc_replay_followups import (
    analyze_raw_ohlc_replay_followups,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"raw_ohlc_followup_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_followup_separates_targets_from_negative_controls(tmp_path):
    summary_path, event_log = _write_fixture(tmp_path)

    summary = analyze_raw_ohlc_replay_followups(
        summary_path=summary_path,
        event_log_path=event_log,
        n_trials=200,
    )

    separation = summary["target_control_separation"]
    assert summary["source_scope"] == "FULL_AVAILABLE_CORPUS"
    assert separation["target_mean_r"] == 1.5
    assert separation["control_mean_r"] == -1.0
    assert separation["target_minus_control_mean_r"] == 2.5
    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_followup_report_contains_synthesis_and_ambiguity_ledger(tmp_path):
    summary_path, event_log = _write_fixture(tmp_path)
    summary = analyze_raw_ohlc_replay_followups(
        summary_path=summary_path,
        event_log_path=event_log,
        n_trials=200,
    )

    report = render_report(summary)

    assert "Direct Answers" in report
    assert "Ambiguity Ledger" in report
    assert "NO_PROMOTION_VERDICT" in report
    assert "same-dataset" in report


def test_followup_surfaces_pbo_variants_and_blocked_controls(tmp_path):
    summary_path, event_log = _write_blocked_fixture(tmp_path)

    summary = analyze_raw_ohlc_replay_followups(
        summary_path=summary_path,
        event_log_path=event_log,
        n_trials=200,
    )

    groups = {row["group"]: row for row in summary["group_summary"]}
    variants = {row["variant"]: row for row in summary["pbo_diagnostic"]["variants"]}

    assert groups["blocked_dominance_controls"]["resolved_r_n"] == 12
    assert groups["blocked_dominance_controls"]["mean_r"] == 0.5
    assert summary["target_control_separation"]["blocked_control_mean_r"] == 0.5
    assert summary["target_control_separation"]["target_minus_blocked_control_mean_r"] == 1.0
    assert variants["target_family_vs_negative_control_family"]["pbo"] == 0.0
    assert variants["target_family_vs_blocked_control_family"]["pbo"] == 0.0
    assert "blocked_control_child_selection" in variants


def _write_fixture(root):
    summary_path = root / "summary.json"
    event_log = root / "events.jsonl"
    summary = {
        "rows_replayed": 4,
        "max_candles_per_symbol": None,
        "max_events": None,
        "start": None,
        "end": None,
        "event_log_path": str(event_log),
        "active_cohorts": [
            {
                "cohort_key": "USDJPY|tokyo|bearish|D1",
                "role": "primary_controlled_child",
            },
            {
                "cohort_key": "GBPUSD|london|bearish|H4+H1_consensus",
                "role": "negative_control",
            },
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    rows = [
        _event("USDJPY|tokyo|bearish|D1", "2025-01-02T00:15:00+00:00", "TP", 1.5),
        _event("USDJPY|tokyo|bearish|D1", "2025-02-02T00:15:00+00:00", "TP", 1.5),
        _event("GBPUSD|london|bearish|H4+H1_consensus", "2025-01-02T07:15:00+00:00", "SL", -1.0),
        _event("GBPUSD|london|bearish|H4+H1_consensus", "2025-02-02T07:15:00+00:00", "SL", -1.0),
    ]
    with event_log.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return summary_path, event_log


def _write_blocked_fixture(root):
    summary_path = root / "blocked_summary.json"
    event_log = root / "blocked_events.jsonl"
    summary = {
        "rows_replayed": 36,
        "max_candles_per_symbol": None,
        "max_events": None,
        "start": None,
        "end": None,
        "event_log_path": str(event_log),
        "active_cohorts": [
            {
                "cohort_key": "USDJPY|tokyo|bearish|D1",
                "role": "primary_controlled_child",
            },
            {
                "cohort_key": "GBPUSD|london|bearish|H4+H1_consensus",
                "role": "negative_control",
            },
            {
                "cohort_key": "NAS100|ny|bullish|D1",
                "role": "dominance_watchlist",
            },
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    rows = []
    for month in range(1, 13):
        rows.append(_event("USDJPY|tokyo|bearish|D1", f"2025-{month:02d}-02T00:15:00+00:00", "TP", 1.5))
        rows.append(
            _event(
                "GBPUSD|london|bearish|H4+H1_consensus",
                f"2025-{month:02d}-02T07:15:00+00:00",
                "SL",
                -1.0,
            )
        )
        rows.append(_event("NAS100|ny|bullish|D1", f"2025-{month:02d}-02T13:15:00+00:00", "TP", 0.5))
    with event_log.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return summary_path, event_log


def _event(cohort_key, close_time, outcome, realized_r):
    symbol, session, *_ = cohort_key.split("|")
    return {
        "schema_version": "raw_ohlc_prequential_event_log_v1",
        "event_key": f"{cohort_key}|{close_time}",
        "candle_close_utc": close_time,
        "symbol": symbol,
        "session": session,
        "raw_cohort_key": cohort_key,
        "pre_ai_gate_status": "WOULD_SEND_AI",
        "would_send_ai": True,
        "mechanical_setup_status": "OK",
        "action": "TAKE",
        "decision_reason": "raw_cohort_match",
        "decision_locked_before_outcome": True,
        "outcome": outcome,
        "realized_r": realized_r,
        "alignment": {},
    }
