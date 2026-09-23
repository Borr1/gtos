from __future__ import annotations

from scripts import build_expanded_oos_family_label_status as label_status


def test_target_families_selects_not_opened_only() -> None:
    matrix = {
        "families": [
            {"family": "A", "replay_or_label_status": "NOT_OPENED"},
            {"family": "B", "replay_or_label_status": "PATH_WORKS_NO_ACTIONS"},
            {"family": "C", "replay_or_label_status": "NOT_OPENED_CONTROL"},
        ]
    }

    rows = label_status.target_families(matrix)

    assert [row["family"] for row in rows] == ["A", "C"]


def test_family_with_matching_raw_replay_cohort_is_replay_ready() -> None:
    matrix = {
        "families": [
            {
                "family": "EURUSD with EURUSD/6E",
                "evidence_class": "SAME_MARKET_SOURCE_TRANSFER_AND_FUTURES_PROXY_TRANSFER",
                "replay_or_label_status": "NOT_OPENED",
                "converted_sources": ["EURUSD"],
                "next_action": "register replay",
            }
        ]
    }
    conversion_status = {
        "m15_inventory": [
            {
                "file_symbol": "EURUSD_SCID",
                "source_symbol": "EURUSD",
                "evidence_class": "SAME_MARKET_SOURCE_TRANSFER",
                "price_transform": "identity",
                "rows": 100,
                "first": "2026-04-15 00:00:00",
                "last": "2026-04-16 00:00:00",
                "gap_count": 0,
                "invalid_records_skipped": 0,
            }
        ]
    }
    replay_spec = {"cohorts": [{"cohort_key": "EURUSD_SCID|london|bullish|D1"}]}

    rows = label_status.build_family_status_rows(
        matrix=matrix,
        conversion_status=conversion_status,
        replay_spec=replay_spec,
    )

    assert rows[0]["label_status"] == "REPLAY_READY_HAS_REGISTERED_COHORT"
    assert rows[0]["matched_raw_replay_cohorts_by_file_symbol"] == {
        "EURUSD_SCID": ["EURUSD_SCID|london|bullish|D1"]
    }


def test_control_family_without_cohort_is_status_only() -> None:
    status = label_status.classify_family_status(
        source_rows=[
            {
                "file_symbol": "CL_PROXY",
                "source_symbol": "CLM26-NYMEX",
                "evidence_class": "CROSS_INSTRUMENT_TRANSFER",
                "rows": 100,
            }
        ],
        matched_cohorts={"CL_PROXY": []},
    )

    assert status == "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT"


def test_payload_preserves_no_promotion_and_opens_no_outcomes() -> None:
    matrix = {
        "families": [
            {
                "family": "S&P with ES/MES",
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "replay_or_label_status": "NOT_OPENED_CONTROL_EXPANSION",
                "converted_sources": ["ESM26-CME"],
                "next_action": "keep control",
            }
        ]
    }
    conversion_status = {
        "m15_inventory": [
            {
                "file_symbol": "SPX_ES",
                "source_symbol": "ESM26-CME",
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "price_transform": "identity",
                "rows": 100,
                "first": "2026-04-15 00:00:00",
                "last": "2026-04-16 00:00:00",
                "gap_count": 0,
                "invalid_records_skipped": 0,
            }
        ]
    }
    replay_spec = {"cohorts": [{"cohort_key": "USDJPY|tokyo|bearish|D1"}]}

    payload = label_status.build_payload(
        matrix=matrix,
        conversion_status=conversion_status,
        replay_spec=replay_spec,
    )

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["summary"]["target_families_from_matrix"] == 1
    assert payload["summary"]["opened_outcome_slices"] == 0
    assert payload["families"][0]["label_status"] == "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT"


def test_markdown_includes_boundary_and_status(tmp_path) -> None:
    payload = {
        "status": "FIRST_WAVE_LABEL_STATUS_AUDIT_CURRENT_NOT_TERMINAL",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "summary": {
            "target_families_from_matrix": 1,
            "opened_outcome_slices": 0,
            "status_counts": {"LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT": 1},
        },
        "families": [
            {
                "family": "EURUSD with EURUSD/6E",
                "label_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT",
                "source_rows": [],
                "matched_raw_replay_cohorts_by_file_symbol": {},
                "next_action": "register replay",
                "label_status_reason": "No matching cohort.",
                "outcome_slice_status": "NOT_OPENED_BY_LABEL_STATUS_AUDIT",
            }
        ],
        "completion_impact": ["status artifact only"],
        "remaining_goal_gaps": ["final synthesis absent"],
    }
    path = tmp_path / "audit.md"

    label_status.write_markdown(path, payload)

    text = path.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in text
    assert "No AI/API calls" in text
    assert "EURUSD with EURUSD/6E" in text
