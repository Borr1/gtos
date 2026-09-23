"""Verifier for the G0 no-API ready-8 future result-opening gate."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

from build_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13 import (
    EVIDENCE_CLASS,
    NEXT_RESULT_PROMPT,
    NEXT_RESULT_STARTER,
    PREFIX,
    ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    SAFE_FLAGS,
    TERMINAL_OPEN,
    build_artifacts,
    git_status_snapshot,
    output_path,
    rel,
    sha256_file,
    write_json,
    write_output_manifest,
)


DATE_TAG = "2026-05-13"
REQUIRED_JSON_STEMS = [
    "DECISION_LEDGER",
    "GATE_EVIDENCE_RECONCILIATION_LEDGER",
    "SAME_EVIDENCE_CLASS_REPAIR_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
OPTIONAL_REFRESH_JSON_STEMS = ["VERIFICATION_RESULT", "FOCUSED_TEST_RESULT"]
REQUIRED_MD_STEMS = ["SATURATION_SELF_RED_TEAM"]
REQUIRED_PY = [
    "build_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
    "verify_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
    "test_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return output_path(stem, suffix)


def syntax_parse() -> dict[str, Any]:
    failures = []
    for name in REQUIRED_PY:
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing python artifact: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def load_required_artifacts(failures: list[str]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for stem in REQUIRED_JSON_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing json artifact: {rel(path)}")
            continue
        loaded[stem] = read_json(path)
    for stem in REQUIRED_MD_STEMS:
        path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append(f"missing markdown artifact: {rel(path)}")
    for path in [NEXT_RESULT_PROMPT, NEXT_RESULT_STARTER]:
        if not path.exists():
            failures.append(f"missing future prompt/starter artifact: {rel(path)}")
    return loaded


def artifact_safe_flags_ok(stem: str, payload: dict[str, Any], failures: list[str]) -> None:
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{stem}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{stem}: evidence_class mismatch")
    for key, expected in SAFE_FLAGS.items():
        if payload.get(key) != expected:
            failures.append(f"{stem}: expected {key}={expected!r}, got {payload.get(key)!r}")


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = artifact_path("COMPLETION_AUDIT")
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    if mark_focused_tests_ok and result["ok"]:
        completion["focused_tests_ok"] = True
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "standalone verifier and focused tests pass":
            row["satisfied"] = bool(result["ok"] and mark_focused_tests_ok)
            row["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit_rows = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "scoped artifacts committed"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(
        row.get("satisfied") is True for row in non_commit_rows
    )
    completion["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(path, completion)


def write_focused_test_result(result: dict[str, Any]) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "focused_tests_ok": True,
        "focused_pytest_command": (
            "python -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0napi_ready8_future_result_opening_gate_after_g12_audit/"
            "test_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py -q"
        ),
        "standalone_verifier_ok": result["ok"],
    }
    payload.update({key: value for key, value in SAFE_FLAGS.items() if key.startswith("opens_") or key in {
        "credentials_touched",
        "changes_trading_risk_safety_prompt_decision_behavior",
    }})
    write_json(artifact_path("FOCUSED_TEST_RESULT"), payload)


def refresh_output_manifest(result: dict[str, Any]) -> None:
    write_output_manifest()
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest = read_json(manifest_path)
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    manifest["artifacts"] = [
        {"path": row["path"], "sha256": sha256_file(ROOT / row["path"]), "bytes": (ROOT / row["path"]).stat().st_size}
        for row in manifest.get("artifacts", [])
        if (ROOT / row["path"]).exists()
    ]
    manifest["artifact_count"] = len(manifest["artifacts"])
    write_json(manifest_path, manifest)


def verify(write_result: bool = True, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    syntax = syntax_parse()
    failures.extend(syntax["failures"])
    loaded = load_required_artifacts(failures)
    recomputed = build_artifacts(write_outputs=False)

    for stem, payload in loaded.items():
        if isinstance(payload, dict):
            artifact_safe_flags_ok(stem, payload, failures)

    decision = loaded.get("DECISION_LEDGER", {})
    reconciliation = loaded.get("GATE_EVIDENCE_RECONCILIATION_LEDGER", {})
    repair = loaded.get("SAME_EVIDENCE_CLASS_REPAIR_LEDGER", {})
    completion = loaded.get("COMPLETION_AUDIT", {})
    output_manifest = loaded.get("OUTPUT_MANIFEST", {})

    if decision.get("terminal_decision") != TERMINAL_OPEN:
        failures.append("G0 decision did not open the future result-packet prompt")
    if decision.get("terminal_blockers"):
        failures.append(f"G0 decision has terminal blockers: {decision.get('terminal_blockers')}")
    if decision.get("may_score_results_now") is not False:
        failures.append("G0 gate allows scoring now")
    if decision.get("result_scoring_opened_by_this_gate") is not False:
        failures.append("G0 gate opened result scoring instead of only a future prompt")
    if decision.get("next_result_prompt", {}).get("prompt_sha256") != sha256_file(NEXT_RESULT_PROMPT):
        failures.append("next result prompt sha mismatch")
    if decision.get("next_result_prompt", {}).get("starter_sha256") != sha256_file(NEXT_RESULT_STARTER):
        failures.append("next result starter sha mismatch")

    if recomputed["terminal_decision"] != decision.get("terminal_decision"):
        failures.append("recomputed terminal decision mismatch")
    if recomputed["evidence_failures"]:
        failures.append(f"recomputed evidence failures: {recomputed['evidence_failures']}")

    rowset_counts = reconciliation.get("rowset_counts", {})
    expected_counts = {
        "rowset_row_count_recomputed": 24112,
        "source_candidate_count_recomputed": 3014,
        "duplicate_proxy_denominator_key_count_recomputed": 3014,
        "ready_card_count_recomputed": 8,
        "row_hash_mismatch_count": 0,
        "asof_violation_count": 0,
        "forbidden_row_field_hit_count": 0,
        "baseline_seed_mismatch_count": 0,
        "control_bucket_mismatch_count": 0,
        "matched_control_group_mismatch_count": 0,
        "row_safe_flag_violation_count": 0,
        "blocked_card_row_count": 0,
        "unexpected_card_row_count": 0,
    }
    for key, expected in expected_counts.items():
        if rowset_counts.get(key) != expected:
            failures.append(f"reconciliation {key} expected {expected}, got {rowset_counts.get(key)!r}")
    if rowset_counts.get("ready_card_ids_recomputed") != [
        "ADV-001",
        "ADV-003",
        "BEH-001",
        "HAZ-001",
        "HAZ-005",
        "MAC-001",
        "MAC-004",
        "UNC-004",
    ]:
        failures.append("ready-card IDs changed")

    hashes = reconciliation.get("hash_reconciliation", {})
    if hashes.get("raw_matches_manifest") is not True:
        failures.append("raw rowset hash does not match manifest")
    if hashes.get("lf_normalized_matches_manifest") is not True:
        failures.append("LF-normalized rowset hash does not match manifest")
    if hashes.get("gitattributes_line_present") is not True:
        failures.append("gitattributes LF line missing")
    if hashes.get("source_artifact_hash_mismatch_count") != 0:
        failures.append("source artifact hash mismatch")

    target_contract = reconciliation.get("target_horizon_no_result_contract", {})
    if target_contract.get("target_or_hazard_hits_computed") is not False:
        failures.append("target/hazard hits computed in gate")
    if target_contract.get("performance_or_result_fields_present") is not False:
        failures.append("performance/result fields present in gate")
    if target_contract.get("forbidden_exact_key_hit_count") != 0:
        failures.append("target contract forbidden exact keys present")
    if target_contract.get("current_route_may_compute_values") is not False:
        failures.append("G0 gate may compute target values")

    quarantine = reconciliation.get("blocked_and_expansion_quarantine", {})
    if quarantine.get("blocked_32_dependency_row_count") != 32:
        failures.append("blocked dependency count changed")
    if quarantine.get("blocked_32_not_mixed_into_ready8_materialization") is not True:
        failures.append("blocked cards mixed into ready8 materialization")
    if quarantine.get("all_expansion_observations_remain_outside_accepted_denominator") is not True:
        failures.append("expansion entered accepted denominator")
    if quarantine.get("all_expansion_observations_remain_outside_ready8_denominator") is not True:
        failures.append("expansion entered ready8 denominator")

    followups = repair.get("same_class_followups_pursued", [])
    followup_status = {row.get("followup_id"): row for row in followups}
    if followup_status.get("READY8-G0-GATE-001", {}).get("terminal_status") != "CLEARED_BY_G0_GATE_OPEN_DECISION":
        failures.append("G0 gate follow-up not cleared")
    if followup_status.get("READY8-EOL-HASH-001", {}).get("terminal_status") != "REPAIRED_AND_CLEARED":
        failures.append("EOL hash follow-up not repaired")
    if repair.get("repair_blocker_count") != 0:
        failures.append("repair blockers remain")

    sat_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if sat_path.exists():
        saturation = sat_path.read_text(encoding="utf-8")
        for phrase in [
            "3,014 source candidates",
            "24,112 ready-card rows",
            "OB-boxed",
            "CRLF/LF hash friction",
            "Same-Evidence-Class Ambiguities Pursued",
            "Silent scoring bug",
        ]:
            if phrase not in saturation:
                failures.append(f"saturation missing phrase: {phrase}")

    if NEXT_RESULT_PROMPT.exists():
        prompt = NEXT_RESULT_PROMPT.read_text(encoding="utf-8")
        for phrase in [
            "SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_ONLY",
            "3,014",
            "24,112",
            "ADV-001",
            "UNC-004",
            "neutral_close_to_close_return_m15_horizons_v1",
            "neutral_high_low_excursion_m15_horizons_v1",
            "Adjacent families may be inventoried and routed as sidecars",
            "Do not compute or claim R, PnL, win rate, expectancy",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "live_effect=false",
        ]:
            if phrase not in prompt:
                failures.append(f"future result prompt missing phrase: {phrase}")
    if NEXT_RESULT_STARTER.exists():
        starter = NEXT_RESULT_STARTER.read_text(encoding="utf-8").strip()
        if "\n" in starter:
            failures.append("future result starter is not one physical line")
        if not starter.startswith("/goal Follow the full controlling prompt"):
            failures.append("future result starter missing /goal prefix")
        for phrase in ["8 ready cards", "3014 source candidates", "24112 ready rows", "NO_PROMOTION_VERDICT"]:
            if phrase not in starter:
                failures.append(f"future result starter missing phrase: {phrase}")

    checklist = completion.get("prompt_to_artifact_checklist", [])
    non_commit_rows = [row for row in checklist if row.get("requirement") != "scoped artifacts committed"]
    for row in non_commit_rows:
        if row.get("requirement") == "standalone verifier and focused tests pass":
            continue
        if row.get("satisfied") is not True:
            failures.append(f"completion checklist unsatisfied: {row.get('requirement')}")
    if output_manifest.get("artifact_count", 0) < 10:
        failures.append("output manifest artifact count too low")

    git_status = git_status_snapshot()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": decision.get("terminal_decision"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
        "focused_tests_ok": mark_focused_tests_ok,
        "ready_card_count_verified": rowset_counts.get("ready_card_count_recomputed"),
        "source_candidate_count_verified": rowset_counts.get("source_candidate_count_recomputed"),
        "rowset_row_count_verified": rowset_counts.get("rowset_row_count_recomputed"),
        "raw_rowset_hash_matches_manifest": hashes.get("raw_matches_manifest"),
        "lf_rowset_hash_matches_manifest": hashes.get("lf_normalized_matches_manifest"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    if write_result:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        refresh_completion(result, mark_focused_tests_ok)
        if mark_focused_tests_ok and result["ok"]:
            write_focused_test_result(result)
        refresh_output_manifest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
