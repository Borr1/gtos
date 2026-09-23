from __future__ import annotations

import json
from pathlib import Path

from verify_g0_fpb_discovery_synthesis_control_route import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
PREFIX = "G0_FPB_SYNTHESIS"


def load(name: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def walk_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_keys(value)


def test_exact_counts_and_family_baseline_coverage():
    evidence = load("EVIDENCE_CHAIN_RECONCILIATION_LEDGER")
    assert evidence["all_counts_reconciled"] is True
    checks = {row["check_id"]: row for row in evidence["count_checks"]}
    assert checks["raw_candidate_attempts"]["expected"] == 13_540_033
    assert checks["duplicate_candidate_keys"]["expected"] == 687_275
    assert checks["unique_denominator_path_label_rows"]["expected"] == 12_852_758
    assert checks["opened_family_count"]["expected"] == 11
    assert checks["baseline_control_family_count"]["expected"] == 4
    assert all(row["status"] == "PASS" for row in checks.values())

    family = load("DISCOVERY_FAMILY_BEHAVIOR_LEDGER")
    assert family["opened_family_count"] == 11
    assert len(family["family_rows"]) == 11
    baseline = load("ADVERSARIAL_BASELINE_CONTROL_LEDGER")
    assert baseline["all_four_baseline_controls_included"] is True
    assert baseline["baseline_control_families"] == [
        "baseline_random_session_control",
        "baseline_shifted_entry_control",
        "baseline_momentum_continuation",
        "baseline_mean_reversion",
    ]


def test_discovery_only_safe_flags_and_no_forbidden_metric_keys():
    forbidden_metric_keys = {
        "actual_r",
        "broker_actual_r",
        "pnl",
        "win_rate",
        "expectancy",
        "mean_r",
        "median_r",
        "total_r",
        "performance_score",
    }
    for path in ROUTE_DIR.glob(f"{PREFIX}_*_{DATE_TAG}.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT", path.name
        assert payload["validation_safe"] is False, path.name
        assert payload["outcome_review_opened"] is False, path.name
        assert payload["live_effect"] is False, path.name
        assert payload["opens_validation"] is False, path.name
        assert payload["opens_result_scoring"] is False, path.name
        assert payload["opens_mt5_order_account_history_behavior"] is False, path.name
        assert payload["opens_live_trading_behavior"] is False, path.name
        assert payload["opens_paid_api_or_databento_route"] is False, path.name
        assert forbidden_metric_keys.isdisjoint(set(walk_keys(payload))), path.name


def test_selected_route_has_prompt_and_falsification_criteria():
    ranking = load("ROUTE_RANKING_LEDGER")
    selected = ranking["selected_next_route"]
    assert selected["route_id"] == "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET"
    assert selected["rank"] == 1
    assert selected["next_prompt_path"].endswith(
        "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET_GOAL_PROMPT_2026-05-11.md"
    )
    assert len(selected["falsification_criteria"]) >= 4
    prompt_path = (
        ROUTE_DIR.parents[1]
        / "04_goal_prompts"
        / "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET_GOAL_PROMPT_2026-05-11.md"
    )
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY" in prompt_text
    assert "does not authorize validation execution" in prompt_text
    assert "NO_PROMOTION_VERDICT" in prompt_text


def test_verifier_passes_after_context_refresh():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
