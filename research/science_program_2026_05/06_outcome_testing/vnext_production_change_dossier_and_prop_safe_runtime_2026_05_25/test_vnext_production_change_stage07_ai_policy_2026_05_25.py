from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage07_ai_policy_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage07", MODULE_PATH)
stage07 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage07)


def _rows() -> list[dict]:
    return [
        json.loads(line)
        for line in (stage07.REPO_ROOT / stage07.STAGE07_LEDGER_PATH)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def _summary() -> dict:
    return json.loads(
        (stage07.REPO_ROOT / stage07.STAGE07_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def _scenario(scenario_id: str) -> dict:
    for row in _rows():
        if row.get("scenario_id") == scenario_id:
            return row
    raise AssertionError(f"missing scenario {scenario_id}")


def test_stage07_ai_policy_scenarios_cover_mechanical_first_actions():
    rows = [row for row in _rows() if row.get("row_type") == "runtime_prompt_packet_scenario"]
    summary = _summary()

    assert {row["scenario_id"] for row in rows} == stage07.REQUIRED_SCENARIOS
    assert not stage07.verify_summary(summary, _rows())
    assert summary["runtime_scenario_would_action_counts"]["SKIP_AI_MECHANICAL_AVOID"] > 0
    assert summary["runtime_scenario_would_action_counts"]["CALL_AI_NARROWED_ROUTE"] > 0
    assert summary["runtime_scenario_would_action_counts"]["CALL_AI_MIXED_RESOLUTION"] > 0
    assert summary["runtime_scenario_would_action_counts"]["BLOCK_LEGACY_BROAD_FALLBACK"] > 0


def test_stage07_shadow_gate_preserves_current_ai_path_until_activation():
    shadow = _scenario("shadow_avoid_records_would_skip")
    active = _scenario("active_avoid_skips_ai")

    assert shadow["action"] == "CALL_AI_CURRENT_PATH"
    assert shadow["would_action"] == "SKIP_AI_MECHANICAL_AVOID"
    assert shadow["allowed"] is True
    assert active["action"] == "SKIP_AI_MECHANICAL_AVOID"
    assert active["allowed"] is False


def test_stage07_prompt_packets_are_hashed_and_schema_checked():
    rows = _rows()
    prompt_rows = [row for row in rows if row.get("row_type") == "runtime_prompt_packet_scenario"]
    parser_rows = [row for row in rows if row.get("row_type") == "schema_parser_fixture"]

    assert all(len(row["prompt_packet_sha256"]) == 64 for row in prompt_rows)
    assert all(len(row["prompt_text_sha256"]) == 64 for row in prompt_rows)
    parsed = {row["fixture_id"]: row["parsed"] for row in parser_rows}
    assert parsed["valid_no_trade_json"] is True
    assert parsed["valid_candidate_fenced_json"] is True
    assert parsed["malformed_missing_reasoning"] is False
    assert parsed["malformed_not_json"] is False


def test_stage07_replay_surface_rows_are_preserved():
    summary = _summary()

    assert summary["stage07_surface"]["group_count"] == 127
    assert summary["stage07_surface"]["row_count"] == 627
    assert summary["prompt_packet_hash_count"] == summary["prompt_packet_count"]
