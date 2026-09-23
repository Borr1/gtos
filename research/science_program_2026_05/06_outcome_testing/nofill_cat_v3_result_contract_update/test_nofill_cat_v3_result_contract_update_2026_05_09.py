from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_nofill_cat_v3_result_contract_update_2026_05_09 as builder
import verify_nofill_cat_v3_result_contract_update_2026_05_09 as verifier


DATE = "2026-05-09"


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_builder_freezes_exact_v3_partition_and_zero_results() -> None:
    result = builder.build_artifacts()
    assert result["ok"] is True
    rulebook = load_json(f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json")
    assert rulebook["starting_evidence_locked"]["v3_row_count"] == 298
    assert rulebook["starting_evidence_locked"]["v3_terminal_family_counts"] == {
        "accepted": 225,
        "blocked": 0,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert rulebook["current_lane_result_records_produced"] == 0
    assert rulebook["current_lane_scored_metric_values"] == 0


def test_eligibility_ledger_contains_only_accepted_input_rows() -> None:
    builder.build_artifacts()
    rows = load_jsonl(f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl")
    assert len(rows) == 225
    assert {row["v3_terminal_family"] for row in rows} == {"accepted"}
    assert all(row["future_scoring_lane_may_consume"] is True for row in rows)
    assert all(row["current_lane_scoring_allowed"] is False for row in rows)
    assert all(row["r_performance_allowed"] is False for row in rows)
    assert all(row["broker_or_account_label_allowed"] is False for row in rows)
    assert sum(1 for row in rows if row["duplicate_key_denominator_member"]) == 182


def test_exclusion_ledger_blocks_source_control_impossible_and_reject_rows() -> None:
    builder.build_artifacts()
    rows = load_jsonl(f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl")
    assert len(rows) == 73
    ids = {row["packet_row_id"] for row in rows}
    assert {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051", "NOFILL-CAT-ROW-0241"} <= ids
    assert {"NOFILL-CAT-ROW-0130", "NOFILL-CAT-ROW-0143", "NOFILL-CAT-ROW-0165", "NOFILL-CAT-ROW-0178"} <= ids
    assert all(row["future_scoring_lane_may_consume"] is False for row in rows)
    assert all(row["row_level_denominator_member"] is False for row in rows)
    assert all(row["duplicate_key_denominator_member"] is False for row in rows)


def test_noleak_schema_forbids_result_and_broker_label_families() -> None:
    builder.build_artifacts()
    schema = load_json(f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json")
    forbidden = set(schema["forbidden_fields"])
    assert "broker_actual_r" in forbidden
    assert "account_history" in forbidden
    assert "live_trade_result" in forbidden
    assert "synthetic_r" in forbidden
    assert "win_rate" in forbidden
    assert "expectancy" in forbidden
    assert "BLOCK_CONTRACT_SOURCE_CONTROL_ROW_IN_DENOMINATOR" in schema["blocker_rules"]
    assert schema["source_hash_policy"]["all_key_source_artifacts_hashed"] is True


def test_duplicate_policy_and_saturation_review_are_present() -> None:
    builder.build_artifacts()
    rulebook = load_json(f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json")
    duplicate = rulebook["duplicate_denominator_policy"]
    assert duplicate["accepted_row_count"] == 225
    assert duplicate["accepted_unique_nofill_duplicate_keys"] == 182
    assert duplicate["accepted_duplicate_key_label_conflict_count"] == 0
    saturation = (OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md").read_text(encoding="utf-8")
    assert "What exact mistake would make source-control rows look like accepted result rows?" in saturation
    assert "What exact mistake would let the 65 rejects influence sample size?" in saturation


def test_verifier_passes_without_nested_pytest() -> None:
    builder.build_artifacts()
    os.environ["NOFILL_CAT_V3_RESULT_CONTRACT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_contract(run_pytest=False, write_audit=True)
    assert results["verification_status"]["status"] == "PASS"
    audit = load_json(f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json")
    assert audit["can_mark_goal_complete"] is True
    assert audit["completion_status"] == "PASS_FROZEN_RESULT_CONTRACT_CONTROL_LANE"
