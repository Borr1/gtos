from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage06_ltf_entry_nofill_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage06", MODULE_PATH)
stage06 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage06)


def _runtime_rows() -> list[dict]:
    rows = [
        json.loads(line)
        for line in (stage06.REPO_ROOT / stage06.STAGE06_LEDGER_PATH)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    return [row for row in rows if row.get("row_type") == "runtime_scenario"]


def _summary() -> dict:
    return json.loads(
        (stage06.REPO_ROOT / stage06.STAGE06_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def _row(scenario_id: str) -> dict:
    for row in _runtime_rows():
        if row["scenario_id"] == scenario_id:
            return row
    raise AssertionError(f"missing scenario {scenario_id}")


def test_stage06_ltf_runtime_scenarios_cover_all_actions():
    rows = _runtime_rows()
    summary = _summary()

    assert {row["scenario_id"] for row in rows} == stage06.REQUIRED_SCENARIOS
    assert not stage06.verify_summary(summary, rows)
    assert summary["runtime_scenario_would_action_counts"]["MONITOR_LTF_PATH"] > 0
    assert summary["runtime_scenario_would_action_counts"]["MARKET_ENTRY_NOW"] > 0
    assert summary["runtime_scenario_would_action_counts"]["ADJUST_LIMIT_ENTRY"] > 0
    assert summary["runtime_scenario_would_action_counts"]["SKIP_LTF_NOFILL_AVOID"] > 0


def test_stage06_shadow_gate_preserves_current_default_action():
    shadow = _row("shadow_market_entry_touch_records_would_action")
    active = _row("active_market_entry_on_ltf_touch")

    assert shadow["action"] == "PLACE_LIMIT"
    assert shadow["would_action"] == "MARKET_ENTRY_NOW"
    assert shadow["applied"] is False
    assert active["action"] == "MARKET_ENTRY_NOW"
    assert active["applied"] is True


def test_stage06_adjusted_entry_and_source_gap_monitoring():
    adjusted = _row("active_adjust_limit_entry_from_offset_evidence")
    source_gap = _row("active_monitor_source_gap")

    assert adjusted["action"] == "ADJUST_LIMIT_ENTRY"
    assert adjusted["adjusted_entry_price"] == 101.0
    assert source_gap["action"] == "MONITOR_LTF_PATH"
    assert source_gap["decision_record"]["path_state"]["source_complete"] is False


def test_stage06_replay_counts_and_surface_rows_are_preserved():
    summary = _summary()

    assert summary["m15_vs_ltf_disagreement"]["logical_row_count"] == 405729
    assert summary["nofill_pending_lifecycle"]["logical_row_count"] == 253234
    assert summary["missed_winner_avoided_loser"]["logical_row_count"] == 253234
    assert summary["path_outcome_r"]["logical_row_count"] == 1978947
    assert summary["production_change_ltf_surface"]["row_count"] == 1064
    assert summary["m15_vs_ltf_disagreement"][
        "would_change_execution_or_decision"
    ]["True"] > 0
