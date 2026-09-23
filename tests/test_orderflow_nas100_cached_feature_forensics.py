from __future__ import annotations

from scripts import analyze_orderflow_nas100_cached_feature_forensics as mod


def _row(
    event_id: str,
    event_class: str,
    date: str,
    depth: float,
    thin: float,
    *,
    synthetic_r: float | None = None,
    actual_r: float | None = None,
) -> dict:
    row = {
        "event_id": event_id,
        "symbol": "NAS100",
        "data_status": "ok",
        "event_class": event_class,
        "canonical_m15_close_utc": f"{date}T07:30:00+00:00",
        "event15_median_total_depth20": depth,
        "event15_thin_depth20_rate": thin,
        "event15_median_depth20_imbalance": 0.1 if event_class == "candidate" else 0.0,
        "event15_median_wall_concentration20": 0.1,
        "event15_near10_pull_pressure": 0.5,
        "event15_near10_net_liquidity": -10.0,
        "pre60_median_total_depth20": depth + 10,
        "pre60_thin_depth20_rate": thin,
    }
    if synthetic_r is not None:
        row["candidate__synthetic_realized_r"] = synthetic_r
    if actual_r is not None:
        row["candidate__realized_r_available"] = True
        row["candidate__realized_r"] = actual_r
    return row


def test_median_delta_and_label_coverage_separate_synthetic_from_actual():
    rows = [
        _row("c1", "candidate", "2026-04-28", 80, 0.3, synthetic_r=-1.0),
        _row("c2", "candidate", "2026-04-29", 90, 0.2, synthetic_r=1.0, actual_r=-1.0),
        _row("x1", "structural_context", "2026-04-28", 120, 0.1),
        _row("x2", "structural_context", "2026-04-29", 130, 0.1),
    ]

    delta = mod.median_delta(rows, "event15_median_total_depth20")
    coverage = mod.label_coverage(rows)

    assert delta["candidate_minus_context"] == -40.0
    assert coverage["synthetic_label_n"] == 2
    assert coverage["actual_r_n"] == 1
    assert coverage["actual_label_status"] == "BLOCKED_ACTUAL_R_SPARSE_OR_ONE_SIDED"


def test_leave_one_date_reports_sign_flip_when_one_date_drives_delta():
    rows = [
        _row("c1", "candidate", "2026-04-28", 50, 0.3),
        _row("c2", "candidate", "2026-04-29", 200, 0.1),
        _row("x1", "structural_context", "2026-04-28", 100, 0.1),
        _row("x2", "structural_context", "2026-04-29", 100, 0.1),
    ]

    check = mod.leave_one_date(rows, "event15_median_total_depth20")

    assert check["full_delta"] == 25.0
    assert check["sign_flip_count"] == 1


def test_concentration_tracks_candidate_date_and_hour_share():
    rows = [
        _row("c1", "candidate", "2026-04-28", 80, 0.3),
        _row("c2", "candidate", "2026-04-28", 85, 0.3),
        _row("c3", "candidate", "2026-04-29", 90, 0.2),
        _row("x1", "structural_context", "2026-04-28", 120, 0.1),
    ]

    conc = mod.concentration(rows)

    assert conc["candidate_by_date"]["top_key"] == "2026-04-28"
    assert conc["candidate_by_date"]["top_share"] == 0.666667


def test_build_payload_uses_cached_rows_and_preserves_no_promotion():
    mbo_payload = {
        "feature_rows": [
            _row("c1", "candidate", "2026-04-28", 80, 0.3, synthetic_r=-1.0),
            _row("c2", "candidate", "2026-04-29", 90, 0.2, synthetic_r=1.0),
            _row("x1", "structural_context", "2026-04-28", 120, 0.1),
            _row("x2", "structural_context", "2026-04-29", 130, 0.1),
        ],
        "group_diagnostics": {"g": {"status": "ok", "rows_processed": 10}},
    }
    mbp_rows = []
    for row in mbo_payload["feature_rows"]:
        mbp = dict(row)
        mbp["event15_median_total_depth10"] = mbp.pop("event15_median_total_depth20")
        mbp["event15_thin_depth10_rate"] = mbp.pop("event15_thin_depth20_rate")
        mbp["event15_median_depth10_imbalance"] = mbp.pop("event15_median_depth20_imbalance")
        mbp["event15_median_near_far_ratio"] = 0.3
        mbp["event15_median_max_bid_wall"] = 10
        mbp["event15_median_max_ask_wall"] = 10
        mbp["pre60_median_total_depth10"] = mbp.pop("pre60_median_total_depth20")
        mbp["pre60_thin_depth10_rate"] = mbp.pop("pre60_thin_depth20_rate")
        mbp_rows.append(mbp)

    payload = mod.build_payload(mbo_payload, {"feature_rows": mbp_rows})

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["inputs"]["data_policy"] == "cached_json_only_no_databento_fetch"
    assert payload["feeds"]["MBO_TOP20"]["coverage"]["candidate_rows"] == 2
    assert payload["runtime_diagnostics"]["mbo_rows_processed_total"] == 10
