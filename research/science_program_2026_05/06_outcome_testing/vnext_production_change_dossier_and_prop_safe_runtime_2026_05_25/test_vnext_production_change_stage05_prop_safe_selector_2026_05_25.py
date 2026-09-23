from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage05_prop_safe_selector_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage05", MODULE_PATH)
stage05 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage05)


def _rows() -> list[dict]:
    path = stage05.REPO_ROOT / stage05.PROP_SELECTOR_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _summary() -> dict:
    return json.loads(
        (stage05.REPO_ROOT / stage05.STAGE05_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def _row(scenario_id: str) -> dict:
    for row in _rows():
        if row["scenario_id"] == scenario_id:
            return row
    raise AssertionError(f"missing scenario {scenario_id}")


def test_stage05_prop_selector_covers_required_budget_scenarios():
    rows = _rows()
    summary = _summary()

    assert {row["scenario_id"] for row in rows} == stage05.REQUIRED_SCENARIOS
    assert not stage05.verify_rows(rows, summary)
    assert summary["selector_action_counts"]["ALLOW"] > 0
    assert summary["selector_action_counts"]["REDUCE_RISK"] > 0
    assert summary["selector_action_counts"]["DEFER_UNTIL_RESET"] > 0
    assert summary["selector_action_counts"]["BLOCK"] > 0


def test_stage05_redacted_account_reset_and_intraday_profit_math():
    before = _row("reset_before_0000_gmt3")
    after = _row("reset_after_0000_gmt3")
    profit = _row("intraday_profit_plus_2pct_daily_cushion_7000")

    assert before["reset_window"]["next_reset_utc"] == "2026-05-25T21:00:00+00:00"
    assert before["reset_window"]["next_reset_malaysia_time"] == "2026-05-26T05:00:00+08:00"
    assert after["reset_window"]["reset_window_start_utc"] == "2026-05-25T21:00:00+00:00"
    assert profit["external_daily_loss_amount"] == 5000.0
    assert profit["external_daily_floor"] == 95000.0
    assert profit["remaining_daily_cushion"] == 7000.0


def test_stage05_budget_actions_preserve_opportunity_before_blocking():
    reduce = _row("reduced_risk_instead_of_block")
    defer = _row("defer_until_reset")
    block = _row("hard_block_only_when_projected_breach_exists")

    assert reduce["selector_action"] == "REDUCE_RISK"
    assert reduce["after_risk_pct"] == 1.5
    assert defer["selector_action"] == "DEFER_UNTIL_RESET"
    assert defer["remaining_overall_cushion"] > 0
    assert block["selector_action"] == "BLOCK"
    assert block["remaining_overall_cushion"] < 0


def test_stage05_dossier_reports_required_replay_metrics():
    summary = _summary()
    prop = summary["prop_replay_metrics"]
    missed = summary["missed_winner_avoided_loser_metrics"]
    robust = summary["robustness_metrics"]

    assert prop["row_count"] == 24
    assert prop["breach_rows"] == 24
    assert prop["deterministic_pass_rows"] == 0
    assert prop["max_trades_day"] == 931
    assert prop["max_loss_streak"] == 54
    assert missed["logical_row_count"] == 253234
    assert "avoided_loser" in missed["classification_counts"]
    assert "missed_winner" in missed["classification_counts"]
    assert robust["logical_row_count"] == 6954
    assert robust["symbols"]
    assert robust["sessions"]
    assert robust["frameworks"]
