"""Verifier for the SCID expansion candidate acceptance/design route."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "SCID_EXPANSION"
EVIDENCE_CLASS = "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_ONLY"
ORIGINAL_8_IDS = {
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001",
}
G0_4_IDS = {
    "G0-EXP-PARTITION-001",
    "G0-EXP-DOMAIN-MISSINGNESS-001",
    "G0-EXP-NEGCTRL-001",
    "G0-EXP-ROWSET-001",
}

REQUIRED_JSON = {
    "inventory": f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json",
    "matrix": f"{PREFIX}_SOURCE_FIELD_DESIGN_MATRIX_{DATE_TAG}.json",
    "criteria": f"{PREFIX}_ACCEPTANCE_REJECTION_CRITERIA_{DATE_TAG}.json",
    "quarantine": f"{PREFIX}_DENOMINATOR_QUARANTINE_PROOF_{DATE_TAG}.json",
    "ranking": f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json",
    "negative": f"{PREFIX}_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_{DATE_TAG}.json",
    "completion": f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    "manifest": f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
}
REQUIRED_TEXT = {
    "saturation": f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
    "builder": "build_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
    "verifier": "verify_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
    "focused_tests": "test_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(name: str) -> Any:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    loaded: dict[str, Any] = {}

    for key, name in REQUIRED_JSON.items():
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing required JSON artifact: {name}")
            continue
        try:
            loaded[key] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append(f"invalid JSON {name}: {exc}")

    for key, name in REQUIRED_TEXT.items():
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing required text/script artifact: {name}")
        elif path.stat().st_size <= 0:
            failures.append(f"empty required artifact: {name}")

    for key, payload in loaded.items():
        if key == "manifest":
            continue
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{key}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{key}: promotion verdict not preserved")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{key}: {flag} is not false")

    inventory = loaded.get("inventory", {})
    rows = inventory.get("rows", [])
    ids = {row.get("candidate_id") for row in rows}
    if inventory.get("accepted_40_is_floor_not_ceiling") is not True:
        failures.append("inventory: accepted_40_is_floor_not_ceiling not true")
    if inventory.get("preserved_original_8_count") != 8:
        failures.append("inventory: preserved original 8 count != 8")
    if inventory.get("preserved_g0_discovered_4_count") != 4:
        failures.append("inventory: preserved G0 4 count != 4")
    if inventory.get("r4_discovered_additional_count", 0) < 8:
        failures.append("inventory: R4 additional discovered count < 8")
    if not ORIGINAL_8_IDS.issubset(ids):
        failures.append("inventory: missing one or more original 8 candidate ids")
    if not G0_4_IDS.issubset(ids):
        failures.append("inventory: missing one or more G0 4 candidate ids")
    if len(rows) < 20:
        failures.append("inventory: candidate count < 20; accepted 40 floor may not have been expanded enough")
    if any(row.get("accepted_40_card_denominator_inclusion") is not False for row in rows):
        failures.append("inventory: at least one candidate entered accepted denominator")
    if any(not row.get("source_fields_or_groups") for row in rows):
        failures.append("inventory: at least one candidate lacks source fields")

    matrix = loaded.get("matrix", {})
    matrix_rows = matrix.get("rows", [])
    if len(matrix_rows) != len(rows):
        failures.append("matrix: row count does not match inventory")
    for row in matrix_rows:
        for field in ["source_fields_or_groups", "as_of_rules", "duplicate_policy", "forbidden_fields", "no_leak_requirements"]:
            if not row.get(field):
                failures.append(f"matrix: {row.get('candidate_id')} missing {field}")

    criteria = loaded.get("criteria", {})
    criteria_rows = criteria.get("rows", [])
    if len(criteria_rows) != len(rows):
        failures.append("criteria: row count does not match inventory")
    if criteria.get("novelty_alone_is_never_rejection_reason") is not True:
        failures.append("criteria: novelty rejection guard missing")
    for row in criteria_rows:
        if row.get("novelty_alone_is_rejection_reason") is not False:
            failures.append(f"criteria: novelty-alone rejection allowed for {row.get('candidate_id')}")
        if len(row.get("acceptance_criteria", [])) < 4 or len(row.get("rejection_criteria", [])) < 4:
            failures.append(f"criteria: weak criteria list for {row.get('candidate_id')}")

    quarantine = loaded.get("quarantine", {})
    if quarantine.get("accepted_40_card_denominator_count") != 40:
        failures.append("quarantine: accepted denominator count != 40")
    if quarantine.get("candidate_overlap_count") != 0:
        failures.append("quarantine: candidate ids overlap accepted 40 ids")
    if quarantine.get("all_candidates_denominator_inclusion_false") is not True:
        failures.append("quarantine: denominator inclusion false proof missing")
    if quarantine.get("accepted_40_is_floor_not_ceiling") is not True:
        failures.append("quarantine: floor-not-ceiling proof missing")

    ranking = loaded.get("ranking", {})
    ranking_rows = ranking.get("rows", [])
    if len(ranking_rows) != len(rows):
        failures.append("ranking: row count does not match inventory")
    totals = [row.get("total_score", 0) for row in ranking_rows]
    if totals != sorted(totals, reverse=True):
        failures.append("ranking: rows are not sorted by total_score descending")
    if len(ranking.get("prompt_packs", [])) < 3:
        failures.append("ranking: expected at least 3 prompt packs")
    for pack in ranking.get("prompt_packs", []):
        prompt_path = ROUTE_DIR.parents[3] / pack["prompt_path"]
        starter_path = ROUTE_DIR.parents[3] / pack["starter_path"]
        if not prompt_path.exists():
            failures.append(f"ranking: missing prompt pack {pack['prompt_path']}")
        if not starter_path.exists():
            failures.append(f"ranking: missing starter {pack['starter_path']}")
        if pack.get("starter_one_physical_line") is not True:
            failures.append(f"ranking: starter not one line {pack['starter_path']}")

    negative = loaded.get("negative", {})
    search = negative.get("searched_artifacts_proof", {})
    if len(search.get("artifact_search_scopes", [])) < 6:
        failures.append("negative audit: artifact search scopes too narrow")
    if len(search.get("local_heavy_roots_checked", [])) < 5:
        failures.append("negative audit: local-heavy roots not checked")
    if not search.get("source_inventory_summary", {}).get("source_inventory_count"):
        failures.append("negative audit: source inventory summary missing")
    if "floor" not in negative.get("anti_boxing_conclusion", "").lower():
        failures.append("negative audit: anti-boxing floor conclusion missing")

    saturation = (ROUTE_DIR / REQUIRED_TEXT["saturation"]).read_text(encoding="utf-8") if (ROUTE_DIR / REQUIRED_TEXT["saturation"]).exists() else ""
    for required_phrase in [
        "Original 8 preserved exactly",
        "G0 4 preserved exactly",
        "R4 additional families added",
        "Deliberately Not Answered",
    ]:
        if required_phrase not in saturation:
            failures.append(f"saturation: missing phrase {required_phrase}")

    completion = loaded.get("completion", {})
    if not completion.get("all_checklist_items_pass"):
        failures.append("completion: prompt-to-artifact checklist not all pass")
    if mark_focused_tests_ok:
        completion["verification_status"] = "VERIFIER_AND_FOCUSED_TESTS_PASSED"
        completion["can_mark_goal_complete_after_verifier_and_focused_tests"] = True
    else:
        completion["verification_status"] = "VERIFIER_PASSED_FOCUSED_TESTS_NOT_MARKED"
        completion["can_mark_goal_complete_after_verifier_and_focused_tests"] = False

    ok = not failures and mark_focused_tests_ok
    result = {
        "schema_version": "scid_expansion_candidate_acceptance_design_verifier_v1",
        "artifact_family": "verification_result",
        "generated_at_utc": utc_now(),
        "evidence_class": EVIDENCE_CLASS,
        "ok": ok,
        "failure_count": len(failures),
        "failures": failures,
        "focused_tests_marked_ok": mark_focused_tests_ok,
        "candidate_count_verified": len(rows),
        "preserved_original_8_count_verified": inventory.get("preserved_original_8_count"),
        "preserved_g0_4_count_verified": inventory.get("preserved_g0_discovered_4_count"),
        "r4_discovered_additional_count_verified": inventory.get("r4_discovered_additional_count"),
        "accepted_40_denominator_count_verified": quarantine.get("accepted_40_card_denominator_count"),
        "candidate_overlap_count_verified": quarantine.get("candidate_overlap_count"),
        "prompt_pack_count_verified": len(ranking.get("prompt_packs", [])),
        "can_mark_goal_complete": ok,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    (ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if "completion" in loaded:
        loaded["completion"].update(
            {
                "verification_status": completion["verification_status"],
                "can_mark_goal_complete_after_verifier_and_focused_tests": completion[
                    "can_mark_goal_complete_after_verifier_and_focused_tests"
                ],
                "verification_result_path": f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
            }
        )
        (ROUTE_DIR / REQUIRED_JSON["completion"]).write_text(
            json.dumps(loaded["completion"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["failure_count"] == 0 else 1)


if __name__ == "__main__":
    main()
