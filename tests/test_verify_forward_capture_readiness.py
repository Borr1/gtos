from __future__ import annotations

import json

from scripts import verify_forward_capture_readiness as mod


def test_verifier_reports_missing_jsonl_as_waiting(tmp_path):
    payload = mod.build_report(tmp_path)
    by_name = {row["name"]: row for row in payload["jsonl_checks"]}

    assert by_name["pending_limit_lifecycle"]["status"] == "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE_OR_NOT_YET_WIRED"
    assert by_name["strategy_follow_evaluations"]["expected_schema"] == "strategy_follow_evaluation_v1"
    assert by_name["strategy_follow_candidates"]["expected_schema"] == "strategy_follow_candidate_v1"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_verifier_accepts_latest_jsonl_schema(tmp_path):
    path = tmp_path / "shadow_logs"
    path.mkdir()
    (path / "pending_limit_lifecycle.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "pending_limit_lifecycle_v1",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    row = mod.check_jsonl(
        tmp_path,
        "pending_limit_lifecycle",
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "pending_limit_lifecycle_v1",
    )
    assert row["status"] == "OK"
    assert row["line_count"] == 1


def test_verifier_checks_json_artifact_schema(tmp_path):
    target = tmp_path / "research" / "program_control"
    target.mkdir(parents=True)
    (target / "FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json").write_text(
        json.dumps(
            {
                "schema_version": "forward_capture_source_map_v1",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
            }
        ),
        encoding="utf-8",
    )

    row = mod.check_json(
        tmp_path,
        "forward_capture_source_map",
        "research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json",
        "forward_capture_source_map_v1",
    )
    assert row["status"] == "OK"


def test_render_md_contains_check_sections(tmp_path):
    payload = mod.build_report(tmp_path)
    md = mod.render_md(payload)
    assert "JSONL Checks" in md
    assert "JSON Artifact Checks" in md
