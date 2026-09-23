from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
PREFIX = "G0_FPB_SYNTHESIS"
ROUTE_ID = "G0_NO_API_MECHANICAL_REPLAY_FPB_DISCOVERY_SYNTHESIS_CONTROL_ROUTE"
VERIFICATION_JSON = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
NEXT_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET_GOAL_PROMPT_2026-05-11.md"
)
CURRENT_STATE = ROOT / ".context" / "00_core" / "research_current_state.md"

EXPECTED_ARTIFACT_KEYS = {
    "EVIDENCE_CHAIN_RECONCILIATION_LEDGER",
    "DISCOVERY_FAMILY_BEHAVIOR_LEDGER",
    "ADVERSARIAL_BASELINE_CONTROL_LEDGER",
    "SELECTION_BIAS_LEDGER",
    "MULTIPLE_TESTING_LEDGER",
    "CONCENTRATION_DUPLICATE_RISK_LEDGER",
    "AMBIGUITY_UNRESOLVED_BURDEN_LEDGER",
    "BASELINE_ANOMALY_LEDGER",
    "FAMILY_SLICE_FRAGILITY_LEDGER",
    "SEALED_VALIDATION_READINESS_LEDGER",
    "ROUTE_RANKING_LEDGER",
    "NO_LAZY_BLOCKER_LEDGER",
    "SEARCHED_ROOT_SOURCE_SATURATION_LEDGER",
    "HARDENING_COVERAGE_LEDGER",
    "HOSTILE_EDGE_REVIEW_LEDGER",
    "HISTORICAL_PARTITION_READINESS_LEDGER",
    "AI_API_COST_BOUNDARY_LEDGER",
    "PROCESS_LIMITATION_COUNTERMEASURE_LEDGER",
    "NEGATIVE_RESULT_FAILURE_ANATOMY_LEDGER",
    "CONTEXT_ANCHOR_INSTRUCTION_COVERAGE_LEDGER",
    "SATURATION_SELF_REDTEAM_PASS",
    "NEXT_PROMPT_PACK",
    "NOLEAK_DIRTY_STATE_AUDIT",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_mt5_order_account_history_behavior",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(key: str, ext: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{key}_{DATE_TAG}.{ext}"


def verify() -> dict[str, Any]:
    failures: list[str] = []
    parsed: dict[str, dict[str, Any]] = {}

    for key in sorted(EXPECTED_ARTIFACT_KEYS):
        for ext in ["json", "md"]:
            path = artifact_path(key, ext)
            if not path.exists():
                failures.append(f"missing artifact: {path.name}")
        json_path = artifact_path(key, "json")
        if json_path.exists():
            payload = load_json(json_path)
            parsed[key] = payload
            if payload.get("route_id") != ROUTE_ID:
                failures.append(f"{json_path.name}: route_id mismatch")
            if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                failures.append(f"{json_path.name}: promotion_verdict mismatch")
            for flag in SAFE_FALSE_FLAGS:
                if payload.get(flag) is not False:
                    failures.append(f"{json_path.name}: {flag} is not false")

    evidence = parsed.get("EVIDENCE_CHAIN_RECONCILIATION_LEDGER", {})
    if evidence.get("all_counts_reconciled") is not True:
        failures.append("evidence chain did not reconcile all counts")
    checks = {row.get("check_id"): row for row in evidence.get("count_checks", [])}
    expected = {
        "raw_candidate_attempts": 13_540_033,
        "duplicate_candidate_keys": 687_275,
        "unique_denominator_path_label_rows": 12_852_758,
        "opened_family_count": 11,
        "baseline_control_family_count": 4,
    }
    for key, value in expected.items():
        row = checks.get(key)
        if not row or row.get("expected") != value or row.get("status") != "PASS":
            failures.append(f"count check failed or missing: {key}")

    family = parsed.get("DISCOVERY_FAMILY_BEHAVIOR_LEDGER", {})
    if family.get("opened_family_count") != 11:
        failures.append("family behavior ledger does not cover 11 families")
    if len(family.get("family_rows", [])) != 11:
        failures.append("family_rows length is not 11")

    baseline = parsed.get("ADVERSARIAL_BASELINE_CONTROL_LEDGER", {})
    if baseline.get("all_four_baseline_controls_included") is not True:
        failures.append("baseline control ledger did not include all four baselines")
    if len(baseline.get("baseline_control_families", [])) != 4:
        failures.append("baseline control count is not 4")

    ranking = parsed.get("ROUTE_RANKING_LEDGER", {})
    ranked_routes = ranking.get("ranked_routes", [])
    if len(ranked_routes) < 7:
        failures.append("route ranking ledger has fewer than 7 routes")
    selected = ranking.get("selected_next_route", {})
    if selected.get("rank") != 1 or selected.get("route_id") != "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET":
        failures.append("selected next route mismatch")
    if not selected.get("falsification_criteria"):
        failures.append("selected route lacks falsification criteria")

    completion = parsed.get("COMPLETION_AUDIT", {})
    checklist = completion.get("prompt_to_artifact_checklist", [])
    non_pass = [row for row in checklist if row.get("status") != "PASS"]
    if non_pass:
        failures.append(f"completion checklist has non-PASS rows: {non_pass}")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard not satisfied")
    if completion.get("can_mark_goal_complete") is not True:
        failures.append("can_mark_goal_complete is not true")
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append("completion audit has missing/incomplete/weak requirements")

    noleak = parsed.get("NOLEAK_DIRTY_STATE_AUDIT", {})
    if noleak.get("passes") is not True:
        failures.append("no-leak dirty-state audit did not pass")
    if noleak.get("forbidden_live_surface_status_entries"):
        failures.append("forbidden live-surface status entries are present")
    if noleak.get("broker_account_order_history_read") is not False:
        failures.append("broker/account/order/history read flag is not false")

    source = parsed.get("SEARCHED_ROOT_SOURCE_SATURATION_LEDGER", {})
    if not source.get("input_hashes"):
        failures.append("source saturation ledger lacks input hashes")
    if source.get("broker_or_account_sources_read") is not False:
        failures.append("source saturation read broker/account source")

    saturation = parsed.get("SATURATION_SELF_REDTEAM_PASS", {})
    if len(saturation.get("questions_answered", [])) < 12:
        failures.append("saturation pass does not answer 12 questions")
    if saturation.get("remaining_same_evidence_class_gaps"):
        failures.append("saturation pass has remaining same-evidence-class gaps")

    if not NEXT_PROMPT.exists():
        failures.append("next prompt file missing")
    else:
        text = NEXT_PROMPT.read_text(encoding="utf-8")
        for needle in [
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "G0_SEALED_PARTITION_AND_BASELINE_PACKET_ONLY",
            "does not authorize validation execution",
        ]:
            if needle not in text:
                failures.append(f"next prompt missing required text: {needle}")

    current_state_text = CURRENT_STATE.read_text(encoding="utf-8") if CURRENT_STATE.exists() else ""
    if ROUTE_ID not in current_state_text:
        failures.append("research_current_state does not mention this route id")
    if "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET" not in current_state_text:
        failures.append("research_current_state does not mention selected next route")

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "artifact_json_count": len(parsed),
        "selected_next_prompt": str(NEXT_PROMPT.relative_to(ROOT)).replace("\\", "/"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_mt5_order_account_history_behavior": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }
    VERIFICATION_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
