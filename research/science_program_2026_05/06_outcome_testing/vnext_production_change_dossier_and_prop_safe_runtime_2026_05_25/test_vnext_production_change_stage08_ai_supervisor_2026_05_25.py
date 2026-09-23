from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_vnext_production_change_stage08_ai_supervisor_2026_05_25.py")
spec = importlib.util.spec_from_file_location("vnext_prod_stage08", MODULE_PATH)
stage08 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage08)


def _rows() -> list[dict]:
    return [
        json.loads(line)
        for line in (stage08.REPO_ROOT / stage08.STAGE08_LEDGER_PATH)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def _summary() -> dict:
    return json.loads(
        (stage08.REPO_ROOT / stage08.STAGE08_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def _scenario(scenario_id: str) -> dict:
    for row in _rows():
        if row.get("scenario_id") == scenario_id:
            return row
    raise AssertionError(f"missing scenario {scenario_id}")


def test_stage08_supervisor_scenarios_cover_health_and_fail_safe_actions():
    rows = [row for row in _rows() if row.get("row_type") == "runtime_supervisor_scenario"]
    summary = _summary()

    assert {row["scenario_id"] for row in rows} == stage08.REQUIRED_SCENARIOS
    assert not stage08.verify_summary(summary, _rows())
    assert summary["runtime_scenario_action_counts"]["HEALTHY"] > 0
    assert summary["runtime_scenario_action_counts"]["WARN"] > 0
    assert summary["runtime_scenario_action_counts"]["DISABLE_AI_NARROWING"] > 0
    assert summary["runtime_scenario_action_counts"]["SUPERVISOR_DISABLED"] > 0


def test_stage08_fail_safe_turns_off_active_ai_narrowing_effects():
    malformed = _scenario("disable_malformed_threshold")

    assert malformed["action"] == "DISABLE_AI_NARROWING"
    assert malformed["disable_ai_narrowing"] is True
    assert malformed["pre_ai_apply_to_ai_call_after"] is False
    assert malformed["ai_policy_apply_to_ai_call_after"] is False


def test_stage08_format_repair_fixtures_preserve_schema_boundary():
    rows = [row for row in _rows() if row.get("row_type") == "format_repair_fixture"]
    parsed = {row["fixture_id"]: row["parsed_after_supervisor_repair"] for row in rows}
    repaired = {row["fixture_id"]: row["repaired"] for row in rows}

    assert repaired["preamble_fenced_json"] is True
    assert parsed["preamble_fenced_json"] is True
    assert parsed["already_valid_json"] is True
    assert parsed["no_json_object"] is False


def test_stage08_replay_surface_rows_are_preserved():
    summary = _summary()

    assert summary["stage08_surface"]["group_count"] == 51
    assert summary["stage08_surface"]["row_count"] == 149
    assert summary["format_repair_fixture_count"] == 3
