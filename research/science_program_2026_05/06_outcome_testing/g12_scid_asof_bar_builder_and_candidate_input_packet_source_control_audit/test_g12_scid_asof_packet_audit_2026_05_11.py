from __future__ import annotations

import build_g12_scid_asof_packet_audit_2026_05_11 as audit


def test_forbidden_scanner_allows_bar_window_fields() -> None:
    patterns = audit.forbidden_patterns()

    assert audit.forbidden_matches_for_name("bar_window_start_utc", patterns) == []
    assert audit.forbidden_matches_for_name("bar_window_end_utc", patterns) == []


def test_forbidden_scanner_rejects_result_and_broker_terms() -> None:
    patterns = audit.forbidden_patterns()
    for field in [
        "win_rate",
        "winning_trade",
        "loss",
        "pnl",
        "expectancy",
        "slippage",
        "broker_order",
        "deal",
        "position",
        "path_label",
        "result",
    ]:
        assert audit.forbidden_matches_for_name(field, patterns), field


def test_candidate_rows_are_input_only_and_hash_to_existing_bars() -> None:
    bars = audit.read_jsonl(audit.BAR_ROWS)
    candidates = audit.read_jsonl(audit.CANDIDATE_ROWS)
    review = audit.candidate_input_review(candidates, bars)

    assert review["summary"]["checks_pass"] is True
    assert review["summary"]["candidate_input_row_count"] == audit.EXPECTED_CANDIDATE_ROWS
    assert review["checks"]["included_bars_exist_and_are_asof"] is True


def test_bar_rows_are_source_bounded_and_fail_closed() -> None:
    bars = audit.read_jsonl(audit.BAR_ROWS)
    review = audit.bar_boundary_review(bars)

    assert review["summary"]["checks_pass"] is True
    assert review["summary"]["bar_row_count"] == audit.EXPECTED_BAR_ROWS
    assert review["checks"]["all_source_bytes_inside_segment"] is True
    assert review["checks"]["empty_gap_session_bars_fail_closed"] is True


def test_duplicate_proxy_controls_keep_only_primary_candidate_sources() -> None:
    bars = audit.read_jsonl(audit.BAR_ROWS)
    candidates = audit.read_jsonl(audit.CANDIDATE_ROWS)
    review = audit.duplicate_proxy_review(candidates, bars)

    assert review["summary"]["checks_pass"] is True
    assert set(review["candidate_sources"]) == audit.EXPECTED_PRIMARY_SOURCES
    assert "XAUUSD_MGC" not in review["candidate_sources"]
    assert "US30_MYM" not in review["candidate_sources"]


def test_verifier_accepts_completed_audit_route() -> None:
    result = audit.verify_route(write_result=False)

    assert result["ok"] is True
    assert result["summary"]["failed_checks"] == []
