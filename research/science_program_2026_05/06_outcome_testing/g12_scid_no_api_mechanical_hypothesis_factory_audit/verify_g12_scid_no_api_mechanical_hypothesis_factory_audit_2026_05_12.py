from __future__ import annotations

import ast
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NO_API_HYP_FACTORY_AUDIT"
ROUTE_ID = "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_CONTROL_EVIDENCE_ONLY"

REQUIRED_STEMS = [
    "CONTEXT_AND_INPUT_INVENTORY",
    "CARD_SCHEMA_COUNT_RECOMPUTATION",
    "SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT",
    "MATRIX_CROSSCHECK_AUDIT",
    "BOUNDARY_CAPTURE_MANIFEST_AUDIT",
    "NOLEAK_SCOPED_DIFF_AUDIT",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py",
    "verify_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py",
    "test_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py",
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
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_no_api_mechanical_hypothesis_factory_audit/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and path.endswith(RAW_SUFFIXES),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def refresh_completion_and_closeout(result: dict[str, Any], mark_focused_tests_ok: bool = False) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item.get("requirement") == "standalone_verifier_passed":
                item["satisfied"] = result["ok"]
                item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
            if mark_focused_tests_ok and item.get("requirement") == "focused_tests_passed":
                item["satisfied"] = True
                item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        completion["standalone_verifier_ok"] = result["ok"]
        non_commit_items = [
            item
            for item in completion.get("prompt_to_artifact_checklist", [])
            if item.get("requirement") != "scoped_commits_complete"
        ]
        completion["completion_standard_satisfied_before_commit"] = all(item.get("satisfied") is True for item in non_commit_items)
        completion["completion_standard_satisfied"] = all(item.get("satisfied") is True for item in completion.get("prompt_to_artifact_checklist", []))
        completion["can_mark_goal_complete"] = completion["completion_standard_satisfied"]
        write_json(completion_path, completion)
    closeout_path = artifact_path("CLOSEOUT_VERIFICATION")
    if closeout_path.exists():
        closeout = read_json(closeout_path)
        closeout["audit_standalone_verifier_ok"] = result["ok"]
        closeout["audit_standalone_verifier_failures"] = result["failures"]
        closeout["syntax_parse"] = result["syntax_parse"]
        closeout["scoped_git_status"] = result["scoped_git_status"]
        if mark_focused_tests_ok:
            closeout["audit_focused_tests_ok"] = True
        closeout["status"] = "VERIFIER_PASSED" if result["ok"] else "VERIFIER_FAILED"
        write_json(closeout_path, closeout)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not json_path.exists():
            failures.append(f"missing json artifact: {rel(json_path)}")
            continue
        payloads[stem] = read_json(json_path)
        if not md_path.exists():
            failures.append(f"missing md artifact: {rel(md_path)}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing python artifact: {name}")

    for stem, payload in payloads.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: promotion_verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: expected {flag}=false, got {payload.get(flag)!r}")

    context = payloads.get("CONTEXT_AND_INPUT_INVENTORY", {})
    if context.get("input_route_file_count") != 37 or context.get("all_input_route_artifacts_read") is not True:
        failures.append("context: input route inventory did not read all 37 files")
    if context.get("parse_failures"):
        failures.append("context: parse/read failures present")

    cards = payloads.get("CARD_SCHEMA_COUNT_RECOMPUTATION", {})
    if cards.get("card_count_recomputed") != 40:
        failures.append("cards: card_count != 40")
    if cards.get("unique_card_count_recomputed") != 40:
        failures.append("cards: unique_card_count != 40")
    if cards.get("schema_failures") or cards.get("all_40_card_schemas_machine_checkable") is not True:
        failures.append("cards: schema failures present")

    domains = payloads.get("SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT", {})
    if domains.get("domain_count_recomputed") != 8 or domains.get("all_eight_domains_present") is not True:
        failures.append("domains: eight-domain coverage failed")
    if any(count != 5 for count in domains.get("domain_counts_recomputed", {}).values()):
        failures.append("domains: cards per domain not exactly 5")
    if domains.get("outside_current_gtos_ob_framing_count_recomputed") != 33:
        failures.append("domains: outside-current-edge count != 33")
    if domains.get("domain_and_breadth_audit_ok") is not True:
        failures.append("domains: breadth/domain audit failed")

    matrices = payloads.get("MATRIX_CROSSCHECK_AUDIT", {})
    if matrices.get("matrix_crosscheck_ok") is not True:
        failures.append("matrices: matrix crosscheck failed")
    if matrices.get("readiness_status_counts_recomputed") != {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }:
        failures.append("matrices: readiness counts mismatch")
    if matrices.get("future_result_design_opened_now") is not False:
        failures.append("matrices: future result design opened")

    boundary = payloads.get("BOUNDARY_CAPTURE_MANIFEST_AUDIT", {})
    if boundary.get("candidate_rows_boundary_recomputed") != 3014:
        failures.append("boundary: candidate row boundary != 3014")
    if boundary.get("duplicate_proxy_denominator_key_boundary_recomputed") != 3014:
        failures.append("boundary: duplicate key boundary != 3014")
    if boundary.get("capture_group_count") != 10 or boundary.get("all_ten_capture_groups_preserved") is not True:
        failures.append("boundary: ten capture groups not preserved")
    if boundary.get("blocking_unrepaired_hash_mismatches") or boundary.get("missing_manifest_artifacts") or boundary.get("raw_manifest_entries"):
        failures.append("boundary: blocking manifest mismatch/missing/raw entry")
    if boundary.get("boundary_capture_manifest_audit_ok") is not True:
        failures.append("boundary: capture manifest audit failed")

    noleak = payloads.get("NOLEAK_SCOPED_DIFF_AUDIT", {})
    if noleak.get("no_leak_scoped_diff_ok") is not True:
        failures.append("noleak: scoped diff/no-leak audit failed")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append(f"decision: expected accept, got {decision.get('terminal_decision')}")
    if decision.get("terminal_blockers"):
        failures.append("decision: terminal blockers present")
    if decision.get("accepted_validation_execution") is not False or decision.get("accepted_strategy_performance") is not False:
        failures.append("decision: forbidden acceptance flag")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    if manifest.get("all_required_artifact_families_covered") is not True:
        failures.append("manifest: required artifact family missing")
    if any(row.get("raw_market_blob") for row in manifest.get("artifacts", [])):
        failures.append("manifest: raw market blob output artifact")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])
    status = git_status_entries()
    if status["no_scoped_forbidden_live_surface"] is not True or status["no_scoped_raw_market_blob"] is not True:
        failures.append("git status: scoped forbidden live surface or raw market blob")

    result = {
        "ok": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
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
        "changes_live_trading_behavior": False,
        "terminal_decision": decision.get("terminal_decision"),
        "card_count_verified": cards.get("card_count_recomputed"),
        "science_domains_verified": sorted(domains.get("domain_counts_recomputed", {})),
        "candidate_rows_verified": boundary.get("candidate_rows_boundary_recomputed"),
        "duplicate_proxy_denominator_keys_verified": boundary.get("duplicate_proxy_denominator_key_boundary_recomputed"),
        "capture_group_count_verified": boundary.get("capture_group_count"),
        "outside_current_gtos_ob_framing_count_verified": domains.get("outside_current_gtos_ob_framing_count_recomputed"),
        "syntax_parse": syntax,
        "scoped_git_status": status,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion_and_closeout(result, mark_focused_tests_ok=mark_focused_tests_ok)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify the G12 SCID no-API mechanical hypothesis factory audit route."
    )
    parser.add_argument(
        "--mark-focused-tests-ok",
        action="store_true",
        help="Mark the focused-test checklist row complete after the focused pytest command has passed.",
    )
    args = parser.parse_args()
    verification = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
