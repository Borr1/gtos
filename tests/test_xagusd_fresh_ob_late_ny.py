from __future__ import annotations

from src.research_infra.xagusd_fresh_ob_late_ny import (
    build_fresh_ob_row,
    build_fresh_ob_rows,
    extract_h1_ob_zone,
    first_seen_by_signature,
    fresh_ob_signature,
)


def _candidate(candidate_id: str, decision: str, entry: float, zone: str, **overrides):
    row = {
        "candidate_id": candidate_id,
        "symbol": "XAGUSD",
        "broker_symbol": "XAGUSD",
        "session": "ny",
        "kill_zone": "ny",
        "decision_time_utc": decision,
        "side": "SHORT",
        "framework": "ob_retest",
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": entry,
            "stop_loss": entry + 0.8,
            "take_profit_1": entry - 1.2,
        },
        "verification": {
            "checks": [
                {
                    "name": "h1_poi_exists",
                    "status": "PASS",
                    "detail": f"H1 OB found at {zone} near AI's POI",
                }
            ]
        },
    }
    row.update(overrides)
    return row


def test_extract_h1_ob_zone_from_verification_detail():
    zone = extract_h1_ob_zone(
        _candidate("c1", "2026-05-05T16:30:00+00:00", 73.222, "73.22-73.97")
    )

    assert zone["zone_source_status"] == "PARSED_FROM_H1_POI_CHECK"
    assert zone["zone_low"] == 73.22
    assert zone["zone_high"] == 73.97


def test_first_seen_distinguishes_old_and_fresh_signatures():
    old_am = _candidate("old_am", "2026-05-05T14:15:00+00:00", 75.471, "75.47-75.79")
    old_pm = _candidate("old_pm", "2026-05-05T16:15:00+00:00", 75.471, "75.47-75.79")
    fresh = _candidate("fresh", "2026-05-05T16:30:00+00:00", 73.222, "73.22-73.97")
    first_seen = first_seen_by_signature([(1, old_pm), (2, fresh), (3, old_am)])

    assert first_seen[fresh_ob_signature(old_pm)]["candidate_id"] == "old_am"
    assert first_seen[fresh_ob_signature(fresh)]["candidate_id"] == "fresh"


def test_fresh_ob_row_keeps_near_close_unresolved_unscored():
    candidate = _candidate("fresh", "2026-05-05T16:30:00+00:00", 73.222, "73.22-73.97")
    first_seen = {fresh_ob_signature(candidate): {"candidate_id": "fresh", "decision_time_utc": "2026-05-05T16:30:00+00:00"}}

    row = build_fresh_ob_row(
        2,
        candidate,
        generated_at_utc="2026-05-06T00:00:00+00:00",
        first_seen=first_seen,
        path_row={
            "candidate_id": "fresh",
            "asof_latest_candle_utc": "2026-05-05T17:00:00+00:00",
            "path_label": "entry_touched_unresolved",
            "touched_entry": True,
            "hit_tp1": False,
            "hit_sl": False,
        },
        opportunity_row={
            "candidate_id": "fresh",
            "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
            "opportunity_lifecycle_state": "NEW_AFTER_COOLDOWN",
        },
    )

    assert row["fresh_ob_late_ny_status"] == "FRESH_OB_LATE_NY_NEW_SIGNATURE"
    assert row["near_close_resolution_status"] == "NEAR_CLOSE_ENTRY_TOUCHED_UNRESOLVED_DO_NOT_SCORE"
    assert row["tracking_status"] == "TRACK_FRESH_OB_LATE_NY_NO_OUTCOME_CLAIM"
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert row["no_execution"] is True


def test_build_fresh_ob_rows_filters_late_ny_xagusd_only():
    rows = [
        (1, _candidate("old", "2026-05-05T14:15:00+00:00", 75.471, "75.47-75.79")),
        (2, _candidate("carry", "2026-05-05T16:15:00+00:00", 75.471, "75.47-75.79")),
        (3, _candidate("fresh", "2026-05-05T16:30:00+00:00", 73.222, "73.22-73.97")),
        (
            4,
            _candidate(
                "other_symbol",
                "2026-05-05T16:30:00+00:00",
                73.222,
                "73.22-73.97",
                symbol="XAUUSD",
            ),
        ),
    ]
    out = build_fresh_ob_rows(
        rows,
        generated_at_utc="2026-05-06T00:00:00+00:00",
        decision_date_prefix="2026-05-05",
    )

    assert [row["candidate_id"] for row in out] == ["carry", "fresh"]
    assert out[0]["fresh_ob_late_ny_status"] == "OLD_OB_DUPLICATE_CARRYOVER"
    assert out[1]["fresh_ob_late_ny_status"] == "FRESH_OB_LATE_NY_NEW_SIGNATURE"
