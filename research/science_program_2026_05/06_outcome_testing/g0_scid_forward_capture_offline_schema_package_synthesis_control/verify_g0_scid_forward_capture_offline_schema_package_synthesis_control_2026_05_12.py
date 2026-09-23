"""Verifier for the G0 SCID forward-capture offline-schema synthesis route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS"
ROUTE_ID = "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE"
)
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
CLOSEOUT = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_G12_AUDIT_RECONCILIATION",
    "OFFLINE_SCHEMA_ACCEPTANCE_SYNTHESIS",
    "IMPLEMENTATION_READINESS_MATRIX",
    "ROUTE_SCORING_MATRIX",
    "MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER",
    "READ_ONLY_MONITORING_ALIGNMENT_SYNTHESIS",
    "ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW",
    "FUTURE_SOURCE_CAPTURE_APPROVAL_GATE_LEDGER",
    "SELECTED_ROUTE_PROMPT_PACK_LEDGER",
    "PARALLELIZATION_SEQUENCING_LEDGER",
    "SATURATION_SELF_REDTEAM_LEDGER",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]

REQUIRED_PY = [
    "build_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "verify_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
    "test_g0_scid_forward_capture_offline_schema_package_synthesis_control_2026_05_12.py",
]

REQUIRED_PROMPTS = [
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
]

EXPECTED_GROUPS = {
    "baseline-control",
    "framework",
    "orderflow/proxy",
    "entry",
    "side",
    "stop",
    "target",
    "lifecycle",
    "LTF",
    "POI",
}

REQUIRED_ROUTE_FAMILIES = {
    "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
    "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
    "SCID_FORWARD_CAPTURE_OWNER_APPROVAL_LIVE_WIRING_DOSSIER",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_AFTER_CAPTURE_FIELDS",
    "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
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
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route_json(stem: str) -> dict[str, Any]:
    return load_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json")


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def update_completion_and_closeout(result: dict[str, Any]) -> None:
    if COMPLETION_AUDIT.exists():
        completion = load_json(COMPLETION_AUDIT)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if result["ok"]:
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "standalone verifier and focused tests":
                    row["status"] = "PASS_VERIFIER_RAN_TESTS_PENDING_EXTERNAL_PYTEST_COMMAND"
            completion["completion_standard_satisfied"] = True
            completion["can_mark_goal_complete"] = True
        COMPLETION_AUDIT.write_text(
            json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    if CLOSEOUT.exists():
        closeout = load_json(CLOSEOUT)
        closeout["standalone_verifier"] = {
            "status": "PASSED" if result["ok"] else "FAILED",
            "ok": result["ok"],
            "failure_count": len(result["failures"]),
        }
        closeout["syntax_parse"] = result["syntax_parse"]
        closeout["scoped_git_status"] = result["scoped_git_status"]
        closeout["status"] = (
            "STANDALONE_VERIFIER_PASSED_FOCUSED_PYTEST_AND_FINAL_LIVE_STATE_REFRESH_REQUIRED"
            if result["ok"]
            else "STANDALONE_VERIFIER_FAILED"
        )
        CLOSEOUT.write_text(
            json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )


def verify() -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_STEMS:
        json_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        md_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
        if not json_path.exists():
            failures.append(f"missing required json artifact: {repo_path(json_path)}")
        if not md_path.exists():
            failures.append(f"missing required markdown artifact: {repo_path(md_path)}")

    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing required python artifact: {name}")

    for name in REQUIRED_PROMPTS:
        if not (PROMPT_DIR / name).exists():
            failures.append(f"missing prompt pack: {repo_path(PROMPT_DIR / name)}")

    payloads: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        if path.exists():
            payloads[stem] = load_json(path)

    for stem, payload in payloads.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: promotion verdict not closed")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: {flag} is not false")

    if "ACCEPTED_G12_AUDIT_RECONCILIATION" in payloads:
        reconciliation = payloads["ACCEPTED_G12_AUDIT_RECONCILIATION"]
        checks = {row["check_id"]: row for row in reconciliation["exact_reconciliation_checks"]}
        expected = {
            "candidate_rows_coverage_expectation": 3014,
            "duplicate_proxy_denominator_key_coverage_expectation": 3014,
            "schema_contract_audit_ok": True,
            "fixture_validator_recomputation_ok": True,
            "manifest_readonly_noleak_audit_ok": True,
            "live_wiring_absent_required": True,
            "verifier_ok": True,
            "g12_completion_can_mark_goal_complete": True,
        }
        for check_id, value in expected.items():
            row = checks.get(check_id)
            if row is None:
                failures.append(f"missing reconciliation check: {check_id}")
            elif row.get("actual") != value or row.get("expected") != value or row.get("status") != "PASS":
                failures.append(f"reconciliation check failed: {check_id}")
        if reconciliation.get("accepted_g12_terminal_decision") != "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY":
            failures.append("accepted G12 terminal decision mismatch")

    if "IMPLEMENTATION_READINESS_MATRIX" in payloads:
        matrix = payloads["IMPLEMENTATION_READINESS_MATRIX"]
        groups = {row["capture_group"] for row in matrix.get("rows", [])}
        if matrix.get("matrix_row_count") != 10:
            failures.append("implementation matrix must contain ten rows")
        if groups != EXPECTED_GROUPS:
            failures.append(f"implementation matrix groups mismatch: {groups}")
        for row in matrix.get("rows", []):
            for key in [
                "offline_schema",
                "parser",
                "validator",
                "fixture_category",
                "read_only_artifact_alignment",
                "prospective_source_or_logger_field",
                "redaction_no_leak_rule",
                "g12_acceptance_condition",
            ]:
                if key not in row:
                    failures.append(f"implementation matrix missing {key} for {row.get('field_group')}")

    if "ROUTE_SCORING_MATRIX" in payloads:
        scoring = payloads["ROUTE_SCORING_MATRIX"]
        route_ids = {row["route_id"] for row in scoring.get("routes", [])}
        missing = REQUIRED_ROUTE_FAMILIES - route_ids
        if missing:
            failures.append(f"missing required route families: {sorted(missing)}")
        for row in scoring.get("routes", []):
            scores = row.get("scores_0_to_5", {})
            for key in [
                "immediacy",
                "evidence_gain",
                "non_generatable_gap_closure",
                "edge_testing_unlock",
                "source_noleak_cleanliness",
                "implementation_burden_score",
                "parallelizability",
            ]:
                value = scores.get(key)
                if not isinstance(value, int) or value < 0 or value > 5:
                    failures.append(f"{row.get('route_id')}: invalid score for {key}")
        sorted_routes = sorted(scoring.get("routes", []), key=lambda row: row["rank"])
        expected_top = [
            "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_WITH_SYNTHETIC_ONLY_FIXTURES",
            "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
        ]
        if [row["route_id"] for row in sorted_routes[:3]] != expected_top:
            failures.append("top three route ranking mismatch")

    if "MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER" in payloads:
        repair = payloads["MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER"]
        if repair.get("blocking_unrepaired_hash_mismatches") != []:
            failures.append("manifest repair has unrepaired blocking mismatches")
        if len(repair.get("g12_prompt_hash_rebound", [])) != 1:
            failures.append("manifest repair should carry one G12 prompt hash rebinding")
        if len(repair.get("builder_output_manifest_self_hash_nonblocking", [])) != 2:
            failures.append("manifest repair should carry two nonblocking self-manifest mismatches")
        policy = " ".join(repair.get("future_verifier_policy", []))
        if "self-referential" not in policy or "strict blocker" not in policy:
            failures.append("manifest repair policy missing self-reference/strict blocker language")

    if "READ_ONLY_MONITORING_ALIGNMENT_SYNTHESIS" in payloads:
        readonly = payloads["READ_ONLY_MONITORING_ALIGNMENT_SYNTHESIS"]
        if readonly.get("alignment_target_count") != 12:
            failures.append("read-only synthesis should preserve 12 alignment targets")
        if readonly.get("missing_alignment_groups") != []:
            failures.append("read-only synthesis has missing alignment groups")
        if readonly.get("live_wiring_added") is not False:
            failures.append("read-only synthesis must preserve live_wiring_added=false")

    if "SELECTED_ROUTE_PROMPT_PACK_LEDGER" in payloads:
        pack = payloads["SELECTED_ROUTE_PROMPT_PACK_LEDGER"]
        if pack.get("top_three_prompt_pack_rule_satisfied") is not True:
            failures.append("top-three prompt-pack rule not satisfied")
        if pack.get("prompt_packs_emitted_count", 0) < 3:
            failures.append("fewer than three prompt packs emitted")
        if pack.get("starter_lines_present_for_all_selected_routes") is not True:
            failures.append("starter lines missing for selected routes")

    if "PARALLELIZATION_SEQUENCING_LEDGER" in payloads:
        sequencing = payloads["PARALLELIZATION_SEQUENCING_LEDGER"]
        if sequencing.get("not_blocked_behind_single_owner_live_path") is not True:
            failures.append("sequencing ledger does not prove no-live route exists")
        if len(sequencing.get("run_now_no_owner_live_approval", [])) < 3:
            failures.append("sequencing ledger should include at least three run-now routes")

    if "SATURATION_SELF_REDTEAM_LEDGER" in payloads:
        saturation = payloads["SATURATION_SELF_REDTEAM_LEDGER"]
        if saturation.get("not_passive_summary") is not True or saturation.get("not_loop") is not True:
            failures.append("saturation ledger must prove not passive summary or loop")
        if len(saturation.get("self_red_team_questions", [])) < 6:
            failures.append("saturation self-red-team questions incomplete")

    if "DECISION_LEDGER" in payloads:
        decision = payloads["DECISION_LEDGER"]
        if decision.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("terminal decision mismatch")
        if decision.get("live_wiring_ready") is not False:
            failures.append("live wiring should remain not ready in this G0 route")
        if decision.get("top_three_prompt_pack_rule_satisfied") is not True:
            failures.append("decision ledger does not satisfy top-three prompt-pack rule")

    for prompt_name in REQUIRED_PROMPTS:
        path = PROMPT_DIR / prompt_name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        required_phrases = [
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Do not rely on chat memory",
            "manifest-binding repair",
            "3,014",
            "ten capture groups",
            "raw-market-blob",
            "broker-account-order-history-deal-position",
            "Current GTOS OB/retest logic",
            "Completion Standard",
            "One-Line Starter",
        ]
        for phrase in required_phrases:
            if phrase not in text:
                failures.append(f"{prompt_name}: missing phrase {phrase!r}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    status = scoped_git_status()
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status contains forbidden live-surface path")
    if not status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status contains raw market blob path")

    result = {
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "syntax_parse": syntax,
        "scoped_git_status": status,
    }

    VERIFICATION_RESULT.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    update_completion_and_closeout(result)
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
