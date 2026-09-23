from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896
ROUTE_ID = "G0_SCID_NOAPI_READY8_TARGET_RESULT_SYNTHESIS_AND_QUARANTINED_NUMERICAL_SCREEN"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PACKET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_jsonl(path: Path, parse: bool = True) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            if parse:
                json.loads(line)
            count += 1
    return count


def target_file(card_id: str, family: str) -> Path:
    card = card_id.replace("-", "_")
    suffix = "CLOSE_TO_CLOSE" if family == TARGET_FAMILIES[0] else "HIGH_LOW_EXCURSION"
    return PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_ROWS_{card}_{suffix}_{DATE}.jsonl"


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    required = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_remote_push": False,
    }
    return all(payload.get(key) == expected for key, expected in required.items())


def verify() -> dict[str, Any]:
    issues: list[str] = []
    required_json = {
        "decision": ROUTE_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_DECISION_LEDGER_{DATE}.json",
        "matrix": ROUTE_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json",
        "partition": ROUTE_DIR / f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json",
        "baseline": ROUTE_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json",
        "duplicate": ROUTE_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json",
        "interaction": ROUTE_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json",
        "negative": ROUTE_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json",
        "open_questions": ROUTE_DIR / f"G0_SCID_READY8_OPEN_DISCOVERY_QUESTIONS_AND_NEXT_ROUTES_{DATE}.json",
        "repair": ROUTE_DIR / f"G0_SCID_READY8_SAME_EVIDENCE_CLASS_REPAIR_LEDGER_{DATE}.json",
        "recursive": ROUTE_DIR / f"G0_SCID_READY8_RECURSIVE_DISCOVERY_LEDGER_{DATE}.json",
        "coverage": ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json",
        "self": ROUTE_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"G0_SCID_READY8_COMPLETION_AUDIT_{DATE}.json",
        "manifest": ROUTE_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_OUTPUT_MANIFEST_{DATE}.json",
        "candidate_schema": ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_SCHEMA_{DATE}.json",
    }
    payloads: dict[str, Any] = {}
    for name, path in required_json.items():
        if not path.exists():
            issues.append(f"missing_json::{name}::{rel(path)}")
            continue
        payloads[name] = read_json(path)
        if isinstance(payloads[name], dict) and not safe_flags_ok(payloads[name]):
            issues.append(f"safe_flags_not_preserved::{name}")

    candidate_path = ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl"
    if not candidate_path.exists():
        issues.append(f"missing_jsonl::candidate_examples::{rel(candidate_path)}")
        candidate_count = 0
    else:
        candidate_count = count_jsonl(candidate_path, parse=True)
        if candidate_count != EXPECTED_ROWSET_ROWS:
            issues.append(f"candidate_example_count::{candidate_count}!=24112")
        if candidate_path.stat().st_size > 100_000_000:
            issues.append(f"candidate_example_ledger_over_100mb::{candidate_path.stat().st_size}")

    input_line_count = 0
    for card in READY_CARDS:
        for family in TARGET_FAMILIES:
            path = target_file(card, family)
            if not path.exists():
                issues.append(f"missing_target_file::{rel(path)}")
                continue
            input_line_count += count_jsonl(path, parse=False)
    if input_line_count != EXPECTED_TARGET_ROWS:
        issues.append(f"input_target_row_count::{input_line_count}!={EXPECTED_TARGET_ROWS}")

    matrix_rows = payloads.get("matrix", {}).get("rows", [])
    if len(matrix_rows) != len(READY_CARDS) * len(HORIZONS) * len(TARGET_FAMILIES):
        issues.append(f"matrix_row_count::{len(matrix_rows)}!=64")
    if matrix_rows and not all(row.get("matches_adv_001_fingerprint") for row in matrix_rows):
        issues.append("matrix_not_all_match_adv001")

    baseline_rows = payloads.get("baseline", {}).get("rows", [])
    if len(baseline_rows) != 2 * len(READY_CARDS) * len(HORIZONS) * len(TARGET_FAMILIES):
        issues.append(f"baseline_delta_row_count::{len(baseline_rows)}!=128")
    if baseline_rows and not all(row.get("movement_fingerprint_match") for row in baseline_rows):
        issues.append("baseline_deltas_not_all_fingerprint_match")

    duplicate = payloads.get("duplicate", {})
    contributors = duplicate.get("ranked_complete_duplicate_key_contributors", [])
    if len(contributors) != EXPECTED_SOURCE_CANDIDATES:
        issues.append(f"duplicate_contributor_count::{len(contributors)}!=3014")
    if duplicate.get("all_duplicate_keys_have_all_card_horizon_family_rows") is not True:
        issues.append("duplicate_rows_not_full_card_horizon_family_expansion")

    coverage = payloads.get("coverage", {})
    if coverage.get("known_same_evidence_class_intelligence_remaining") != 0:
        issues.append("coverage_remaining_not_zero")
    if coverage.get("sampling_or_approximation_used") is not False:
        issues.append("coverage_sampling_or_approximation_used")

    self_interrogation = payloads.get("self", {})
    if self_interrogation.get("same_evidence_class_items_remaining_after_final_loop") != 0:
        issues.append("self_interrogation_remaining_not_zero")

    completion = payloads.get("completion", {})
    checklist = completion.get("prompt_to_artifact_checklist", [])
    if not checklist or not all(item.get("satisfied") for item in checklist):
        issues.append("completion_checklist_not_all_satisfied")
    if len(completion.get("mandatory_question_answers", [])) != 17:
        issues.append("completion_mandatory_question_answers_not_17")

    manifest = payloads.get("manifest", {})
    manifest_paths = {item.get("path") for item in manifest.get("artifacts", [])}
    needed_manifest_entries = {
        rel(Path(__file__)),
        rel(ROUTE_DIR / f"build_g0_scid_ready8_numerical_screen_{DATE.replace('-', '_')}.py"),
        rel(ROUTE_DIR / f"test_g0_scid_ready8_numerical_screen_{DATE.replace('-', '_')}.py"),
        rel(candidate_path),
        rel(ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_SCHEMA_{DATE}.json"),
    }
    missing_manifest = sorted(needed_manifest_entries - manifest_paths)
    if missing_manifest:
        issues.append(f"manifest_missing_entries::{missing_manifest}")

    g12_prompt = ROOT / f"research/science_program_2026_05/04_goal_prompts/G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_{DATE}.md"
    source_prompt = ROOT / f"research/science_program_2026_05/04_goal_prompts/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_GOAL_PROMPT_{DATE}.md"
    if not g12_prompt.exists():
        issues.append(f"missing_next_g12_prompt::{rel(g12_prompt)}")
    if not source_prompt.exists():
        issues.append(f"missing_source_design_prompt::{rel(source_prompt)}")

    return {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "issues": issues,
        "input_target_row_count": input_line_count,
        "candidate_example_rows": candidate_count,
        "matrix_rows": len(matrix_rows),
        "baseline_delta_rows": len(baseline_rows),
        "duplicate_contributor_rows": len(contributors),
        "known_same_evidence_class_intelligence_remaining": coverage.get("known_same_evidence_class_intelligence_remaining"),
        "same_evidence_class_items_remaining_after_final_loop": self_interrogation.get("same_evidence_class_items_remaining_after_final_loop"),
        "safe_flags_checked": True,
    }


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
