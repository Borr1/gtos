from __future__ import annotations

import json
from pathlib import Path

import build_scid_asof_target_horizon_repair_2026_05_11 as route
import verify_scid_asof_target_horizon_repair_2026_05_11 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = route.PREFIX
DATE_TAG = route.DATE_TAG


def load_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_blocker_reconciliation_and_counts() -> None:
    blocker = load_json("BLOCKER_RECONCILIATION")

    assert blocker["blocker_reconstructed_from_disk"] is True
    assert blocker["predecessor_terminal_decision"] == "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
    checks = blocker["exact_count_reconciliation"]
    assert checks["candidate_rows"]["actual"] == 3014
    assert checks["bar_rows"]["actual"] == 7567
    assert checks["sealed_rows"]["actual"] == 2432
    assert checks["stress_rows"]["actual"] == 582
    assert checks["discovery_exclusions"]["actual"] == 365
    assert checks["denominator_groups"]["actual"] == 7
    assert checks["known_families"]["actual"] == 11
    assert all(item["pass"] for item in checks.values())


def test_neutral_rulebook_is_frozen_and_not_strategy_edge() -> None:
    rulebook = load_json("RULEBOOK")
    neutral = load_json("NEUTRAL_TARGET_CONTRACT")
    multiple = load_json("MULTIPLE_TESTING_LEDGER")

    assert rulebook["target_scope"] == "SOURCE_SAFE_NEUTRAL_BAR_BEHAVIOR_ONLY_NOT_STRATEGY_EDGE"
    assert rulebook["horizon_set_m15_bars"] == [1, 4, 16, 32]
    assert len(rulebook["target_definitions"]) == 8
    assert all(row["strategy_edge_interpretation_allowed"] is False for row in rulebook["target_definitions"])
    assert neutral["contract_status"] == "SOURCE_SAFE_NEUTRAL_TARGETS_FROZEN_G12_AUDIT_REQUIRED"
    assert multiple["neutral_target_definition_count"] == 8
    assert multiple["this_route_adds_result_rows"] is False


def test_all_families_decided_without_forcing_strategy_execution() -> None:
    matrix = load_json("FAMILY_EXECUTABILITY_MATRIX")
    rows = matrix["matrix_rows"]

    assert matrix["all_known_families_decided"] is True
    assert len(rows) == 11
    assert {row["repair_status"] for row in rows} == {"SOURCE_SAFE_NEUTRAL_TARGET_ONLY", "CONTROL_ONLY"}
    assert sum(row["repair_status"] == "SOURCE_SAFE_NEUTRAL_TARGET_ONLY" for row in rows) == 7
    assert sum(row["repair_status"] == "CONTROL_ONLY" for row in rows) == 4
    assert all(row["strategy_specific_execution_allowed"] is False for row in rows)


def test_missing_strategy_fields_reduced_to_expansion_contracts() -> None:
    derivation = load_json("SOURCE_FIELD_DERIVATION_CONTRACT")
    expansion_ledger = load_json("SOURCE_FIELD_EXPANSION_EXECUTION_LEDGER")
    requirements = load_json("SOURCE_EXPANSION_REQUIREMENTS")

    assert len(derivation["family_missing_field_derivation_results"]) == 11
    assert all(row["accepted_bar_derivation_attempted"] for row in derivation["family_missing_field_derivation_results"])
    assert all(row["artifact_code_history_search_attempted"] for row in derivation["family_missing_field_derivation_results"])
    assert expansion_ledger["all_families_pursued_to_same_class_closure"] is True
    strategy_reqs = [
        row for row in requirements["requirements"] if row["requirement_status"].startswith("EXACT_PROSPECTIVE")
    ]
    assert len(strategy_reqs) == 7
    assert all(row["required_future_fields"] for row in strategy_reqs)


def test_verifier_accepts_route_without_writing() -> None:
    result = verifier.verify_route(write_result=False, run_focused_tests=False)

    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True
    assert result["raw_blob_audit"]["issues"] == []


def test_timestamp_horizon_addition_uses_m15_utc() -> None:
    assert route.add_m15_bars("2026-05-10T22:15:00.000Z", 4) == "2026-05-10T23:15:00.000Z"
