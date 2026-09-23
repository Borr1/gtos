from __future__ import annotations

import json
from pathlib import Path

from build_g0_nofill_cat_v2_synthesis_control_route_2026_05_09 import (
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    PROMOTION_VERDICT,
    ROUTE_DIR,
    ROW_LEDGER,
    future_route_ranking,
    read_jsonl,
    recompute_counts,
    required_output_files,
)


def test_recompute_counts_from_upstream_row_ledger() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))

    assert counts["partition"] == EXPECTED_PARTITION
    assert counts["accepted_split"] == EXPECTED_ACCEPTED_SPLIT
    assert counts["accepted_label_counts"] == dict(sorted(EXPECTED_LABEL_COUNTS.items()))
    assert counts["duplicate_posture"]["accepted_row_level_source_inputs"] == 225
    assert counts["duplicate_posture"]["accepted_unique_nofill_duplicate_keys"] == 182
    assert counts["duplicate_posture"]["oti5_noncanonical_duplicate_projections_rejected"] == 39


def test_blocked_and_rejected_rows_remain_outside_denominators() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))

    for row in counts["blocked_rows"] + counts["rejected_rows"]:
        assert row["categorical_input_label"] is None
        assert row["categorical_lifecycle_label"] is None
        assert row["in_accepted_packet_denominator"] is False
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False


def test_future_route_ranking_keeps_result_lane_closed() -> None:
    routes = future_route_ranking()

    assert routes[0]["route_id"] == "NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER"
    closed = [route for route in routes if route["route_id"] == "NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE"]
    assert len(closed) == 1
    assert closed[0]["route_type"] == "CLOSED_ROUTE"
    assert closed[0]["source_feasibility"] == "NOT_AUTHORIZED"


def test_generated_required_json_artifacts_are_parseable_and_safe() -> None:
    required_json = [
        name
        for name in required_output_files()
        if name.endswith(".json") and name.startswith("G0_NOFILL_CAT_V2_")
    ]

    assert required_json
    for name in required_json:
        path = ROUTE_DIR / name
        assert path.exists(), name
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["promotion_verdict"] == PROMOTION_VERDICT
        assert data["validation_safe"] is False
        assert data["outcome_review_opened"] is False
        assert data["live_effect"] is False


def test_required_markdown_artifacts_preserve_promotion_posture() -> None:
    required_markdown = [
        name
        for name in required_output_files()
        if name.endswith(".md") and name.startswith("G0_NOFILL_CAT_V2_")
    ]

    assert required_markdown
    for name in required_markdown:
        path = ROUTE_DIR / name
        assert path.exists(), name
        assert PROMOTION_VERDICT in path.read_text(encoding="utf-8")
