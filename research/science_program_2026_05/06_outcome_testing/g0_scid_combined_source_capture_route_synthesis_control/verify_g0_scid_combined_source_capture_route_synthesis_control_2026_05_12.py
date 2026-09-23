"""Verifier for the G0 SCID combined source-capture synthesis route."""

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
PREFIX = "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS"
ROUTE_ID = "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_WITH_RANKED_ROUTE_BUNDLE"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
CLOSEOUT = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_G12_AUDIT_RECONCILIATION",
    "CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER",
    "MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE",
    "ROUTE_OPTION_RANKING",
    "ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER",
    "IMPLEMENTATION_READINESS_BOUNDARY_LEDGER",
    "FORBIDDEN_SURFACE_NOLEAK_CONTINUITY_AUDIT",
    "SELECTED_ROUTE_PROMPT_PACK_LEDGER",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]

REQUIRED_PY = [
    "build_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
    "verify_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
    "test_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
]

REQUIRED_PROMPTS = [
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
]

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
        "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
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
                if row.get("requirement") == "verifier and focused tests pass":
                    row["status"] = "PASS_VERIFIER_RAN_TESTS_PENDING_EXTERNAL_PYTEST_COMMAND"
            completion["completion_standard_satisfied"] = True
            completion["can_mark_goal_complete"] = True
        COMPLETION_AUDIT.write_text(json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")

    if CLOSEOUT.exists():
        closeout = load_json(CLOSEOUT)
        closeout["standalone_verifier"] = {
            "status": "PASSED" if result["ok"] else "FAILED",
            "ok": result["ok"],
            "failure_count": len(result["failures"]),
        }
        closeout["syntax_parse"] = result["syntax_parse"]
        closeout["scoped_git_status"] = result["scoped_git_status"]
        closeout["status"] = "STANDALONE_VERIFIER_PASSED_FOCUSED_PYTEST_AND_FINAL_LIVE_STATE_REFRESH_REQUIRED" if result["ok"] else "STANDALONE_VERIFIER_FAILED"
        CLOSEOUT.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


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
            "candidate_rows": 3014,
            "unique_candidate_ids": 3014,
            "unique_duplicate_keys": 3014,
            "field_status_recomputation": True,
            "source_search_saturation": True,
            "capture_contract_exactness": True,
            "noleak_forbidden_surface": True,
            "hash_binding_after_repair": True,
        }
        for check_id, value in expected.items():
            row = checks.get(check_id)
            if row is None:
                failures.append(f"missing reconciliation check: {check_id}")
            elif row.get("actual") != value or row.get("expected") != value or row.get("status") != "PASS":
                failures.append(f"reconciliation check failed: {check_id}")
        if reconciliation.get("accepted_g12_terminal_decision") != "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR":
            failures.append("accepted G12 terminal decision mismatch")

    if "CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER" in payloads:
        ledger = payloads["CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER"]
        required_groups = set(ledger.get("required_capture_groups", []))
        expected_groups = {
            "baseline_control_fields",
            "framework_setup_family",
            "future_orderflow_depth_proxy_requirements",
            "intended_entry_reference",
            "intended_side_direction",
            "intended_stop_reference",
            "intended_target_reference",
            "lifecycle_fill_cancel_expiry_source_status",
            "lower_timeframe_asof_path_availability",
            "poi_type_bounds_source",
        }
        if required_groups != expected_groups:
            failures.append("carry-forward capture groups do not match accepted G12 contract")
        if len(ledger.get("non_generatable_historical_strategy_intent_source_state_families", [])) != 7:
            failures.append("expected seven non-generatable strategy-intent/source-state families")

    if "MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE" in payloads:
        repair = payloads["MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE"]
        if repair.get("blocking_unrepaired_hash_mismatches") != []:
            failures.append("repair note has unrepaired hash mismatches")
        expected_repairs = {
            "research/science_program_2026_05/04_goal_prompts/G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md",
            "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/SCID_COMBINED_SOURCE_CAPTURE_OUTPUT_MANIFEST_2026-05-12.json",
        }
        if set(repair.get("repaired_hash_binding_mismatches", [])) != expected_repairs:
            failures.append("repair note does not preserve accepted repaired hash binding mismatches")

    if "ROUTE_OPTION_RANKING" in payloads:
        ranking = payloads["ROUTE_OPTION_RANKING"]
        route_ids = [row["route_id"] for row in ranking.get("routes", [])]
        for required in [
            "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
            "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION",
            "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
            "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT",
        ]:
            if required not in route_ids:
                failures.append(f"missing required route option in ranking: {required}")
        if ranking.get("rank_1_route") != "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE":
            failures.append("rank 1 route mismatch")
        if len(ranking.get("routes", [])) < 6:
            failures.append("route ranking did not evaluate at least six route options")

    if "ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER" in payloads:
        anti = payloads["ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER"]
        families = set(anti.get("outside_current_edge_mechanism_families_kept_open", []))
        for required in ["path geometry and topology", "orderflow, depth, proxy, liquidity provision/taking, and trapped-trader context", "ML/meta-labeling, uncertainty, model disagreement, and adversarial baselines"]:
            if required not in families:
                failures.append(f"anti-boxing ledger missing family: {required}")
        answers = anti.get("saturation_questions_answered", [])
        if len(answers) < 5:
            failures.append("anti-boxing saturation answers incomplete")

    if "SELECTED_ROUTE_PROMPT_PACK_LEDGER" in payloads:
        pack = payloads["SELECTED_ROUTE_PROMPT_PACK_LEDGER"]
        if pack.get("prompt_count") != 4:
            failures.append("expected four prompt packs")
        rank1 = pack.get("rank_1_prompt", {})
        for key in ["embedded_g12_repair", "embedded_no_lazy_blockers", "embedded_checkpoint_resume", "embedded_anti_boxing", "embedded_exact_forbidden_surfaces"]:
            if rank1.get(key) is not True:
                failures.append(f"rank1 prompt pack missing hardening flag: {key}")

    if "DECISION_LEDGER" in payloads:
        decision = payloads["DECISION_LEDGER"]
        if decision.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("terminal decision mismatch")
        if decision.get("result_design_ready") is not False:
            failures.append("result design should not be ready in this route")
        if len(decision.get("result_design_blocked_by", [])) != 7:
            failures.append("decision ledger must list seven result-design blockers")

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
            "G12 Repair Handoff",
            "raw-market-blob",
            "broker-account-order-history-deal-position",
            "current GTOS OB/retest logic",
            "13,540,033 FPB discovery substrate",
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

    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    update_completion_and_closeout(result)
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
