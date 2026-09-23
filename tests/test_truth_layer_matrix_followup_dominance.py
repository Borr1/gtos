import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.analyze_truth_layer_matrix_followup_dominance import (
    analyze_matrix_followup_dominance,
    load_followup_spec,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_matrix_followup_dominance_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_dominance_audit_flags_top_year_dependency(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    rows = []
    rows.extend(_rows("USDJPY", "london", "bearish|D1", "2022", [1.5, 1.5, -1.0]))
    rows.extend(_rows("USDJPY", "london", "bearish|D1", "2023", [1.5, -1.0, 1.5]))
    rows.extend(_rows("NAS100", "ny", "bullish|D1", "2022", [1.5] * 5))
    rows.extend(_rows("NAS100", "ny", "bullish|D1", "2023", [-1.0]))
    rows.extend(_rows("GBPJPY", "tokyo", "bullish|D1", "2022", [1.5]))
    _write_jsonl(truth_path, rows)

    summary = analyze_matrix_followup_dominance(input_path=truth_path, spec_path=spec_path)
    report = render_report(summary)
    by_key = {row["cohort_key"]: row for row in summary["cohorts"]}

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_key["USDJPY|london|bearish|D1"]["audit_status"].startswith("CLEARED")
    assert "single_year_dominance" in by_key["NAS100|ny|bullish|D1"]["audit_blockers"]
    assert by_key["NAS100|ny|bullish|D1"]["top_year"] == "2022"
    assert "Dominance Audit" in report
    assert "NO_PROMOTION_VERDICT" in report


def _write_spec(path):
    payload = {
        "schema_version": "truth_layer_matrix_followup_hypotheses_v1",
        "promotion_verdict_allowed": False,
        "population": {
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "primary_resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
        "audit_thresholds": {
            "min_total_resolved_n": 2,
            "min_year_resolved_n": 1,
            "max_single_year_resolved_share": 0.7,
            "max_single_month_resolved_share": 1.0,
            "require_all_valid_years_positive": True,
            "require_top_year_excluded_mean_r_positive": True,
        },
        "families": [
            {
                "family_id": "truth_layer_non_primary_strong_leads_v1",
                "lane": "lane_2_non_primary_strong_leads",
                "status": "pre_registered_for_diagnostic_followup",
                "cohorts": [
                    {
                        "cohort_key": "USDJPY|london|bearish|D1",
                        "candidate_id": "P3-TL-MATRIX-025",
                    }
                ],
            },
            {
                "family_id": "truth_layer_dominance_watchlist_v1",
                "lane": "lane_3_dominance_watchlist",
                "status": "dominance_audit_only",
                "cohorts": [
                    {
                        "cohort_key": "NAS100|ny|bullish|D1",
                        "candidate_id": "P3-TL-MATRIX-019",
                    }
                ],
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _rows(symbol, session, regime, year, values):
    rows = []
    for index, value in enumerate(values, start=1):
        outcome = "TP" if value > 0 else "SL"
        timestamp = f"{year}-{index:02d}-03T00:00:00+00:00"
        rows.append(
            {
                "opportunity_key": f"{symbol}|{timestamp}|{outcome}",
                "symbol": symbol,
                "session": session,
                "year": year,
                "month": timestamp[:7],
                "candle_close_utc": timestamp,
                "truth_regime": regime,
                "truth_outcome": outcome,
                "truth_realized_r": value,
                "truth_confidence": "HIGH",
                "truth_source_timeframe": "M1",
                "lower_tf_gap_count_in_horizon": 0,
                "lower_tf_first_gap_utc": None,
                "would_send_ai": True,
                "mechanical_setup_status": "OK",
                "ai_call_attempted": False,
                "ai_call_count": 0,
                "m1_gap_count_in_horizon": 0,
                "m1_first_gap_utc": None,
                "m1_refined_exit_time": timestamp,
                "m5_gap_count_in_horizon": 0,
            }
        )
    return rows


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

