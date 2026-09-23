from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
PREFIX = "G12_SCID_FC_BLOCKED15_AUDIT"
ROUTE_ID = "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
NEXT_G0_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    f"G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_{DATE}.md"
)
NEXT_G0_STARTER = ROUTE_DIR / f"NEXT_G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_STARTER_{DATE}.txt"

JSON_STEMS = {
    "CONTEXT_AND_INPUT_INVENTORY": "context_and_inputs_ok",
    "BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT": "blocked15_ok",
    "SOURCE_SEARCH_SATURATION_AUDIT": "source_search_ok",
    "RECOVERED_ROW_SCHEMA_REDACTION_AUDIT": "recovered_rows_ok",
    "PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT": "contract_ok",
    "DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT": "denominator_ok",
    "TARGET_VERIFIER_TEST_RERUN_LEDGER": "target_rerun_ok",
    "DECISION_LEDGER": "decision",
    "COMPLETION_AUDIT": "completion",
    "OUTPUT_MANIFEST": "manifest",
}
PYTHON_ARTIFACTS = [
    ROUTE_DIR / "build_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
    ROUTE_DIR / "verify_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
    ROUTE_DIR / "test_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12.py",
]
SAFE_FLAGS: dict[str, Any] = {
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
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".zip", ".bin", ".dly")
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_future_capture_blocked15_source_state_materialization_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append({"path": rel(path), "error": str(exc)})
    return {"ok": not failures, "failures": failures}


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        rows.append(
            {
                "raw": line,
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and Path(path).suffix.lower() in RAW_SUFFIXES,
            }
        )
    scoped_rows = [row for row in rows if row["scoped"]]
    return {
        "entries": rows,
        "scoped_entries": scoped_rows,
        "unscoped_entry_count": len(rows) - len(scoped_rows),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_rows),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_rows),
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    verification_path = artifact_path("VERIFICATION_RESULT")
    write_json(verification_path, result)

    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item["requirement"] == "G12 standalone verifier passed":
                item["satisfied"] = result["ok"]
                item["evidence"] = rel(verification_path)
            if item["requirement"] == "G12 focused tests passed" and mark_focused_tests_ok:
                item["satisfied"] = True
                item["evidence"] = rel(PYTHON_ARTIFACTS[-1])
        completion["standalone_verifier_ok"] = result["ok"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        missing = [item["requirement"] for item in completion.get("prompt_to_artifact_checklist", []) if not item["satisfied"]]
        completion["missing_incomplete_or_weakly_verified_requirements"] = missing
        completion["completion_standard_satisfied"] = not missing
        completion["can_mark_goal_complete"] = not missing
        write_json(completion_path, completion)
        write_md(completion_path.with_suffix(".md"), "Completion Audit", completion)

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for row in manifest.get("artifacts", []):
            path = REPO_ROOT / row["path"]
            row["exists_after_verify"] = path.exists()
            row["sha256_after_verify"] = sha256_file(path) if path.exists() and path.is_file() else None
        write_json(manifest_path, manifest)
        write_md(manifest_path.with_suffix(".md"), "Output Manifest", manifest)


def verify(write: bool = True, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    loaded: dict[str, Any] = {}
    for stem in JSON_STEMS:
        path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append({"issue": "missing_json_artifact", "path": rel(path)})
            continue
        loaded[stem] = read_json(path)
        if stem != "VERIFICATION_RESULT" and not md_path.exists():
            failures.append({"issue": "missing_markdown_artifact", "path": rel(md_path)})
        payload = loaded[stem]
        if payload.get("route_id") != ROUTE_ID:
            failures.append({"artifact": stem, "issue": "route_id_mismatch"})
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append({"artifact": stem, "issue": "evidence_class_mismatch"})
        for flag, expected in SAFE_FLAGS.items():
            if payload.get(flag) != expected:
                failures.append({"artifact": stem, "issue": "safe_flag_mismatch", "flag": flag, "observed": payload.get(flag), "expected": expected})

    for path in PYTHON_ARTIFACTS:
        if not path.exists():
            failures.append({"issue": "missing_python_artifact", "path": rel(path)})
    syntax = syntax_parse([path for path in PYTHON_ARTIFACTS if path.exists()])
    failures.extend(syntax["failures"])

    context = loaded.get("CONTEXT_AND_INPUT_INVENTORY", {})
    if context.get("all_target_artifacts_exist_and_hash") is not True:
        failures.append({"artifact": "context", "issue": "target_artifacts_not_all_present_and_hashed"})

    blocked15 = loaded.get("BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT", {})
    if blocked15.get("ok") is not True:
        failures.append({"artifact": "blocked15", "issue": "blocked15_audit_not_ok", "failures": blocked15.get("failures")})
    if blocked15.get("recomputed_blocked15_count") != 15:
        failures.append({"artifact": "blocked15", "issue": "recomputed_blocked15_count_not_15"})
    if blocked15.get("all_ten_capture_groups_visible") is not True or len(blocked15.get("accepted_capture_groups_recomputed", [])) != 10:
        failures.append({"artifact": "blocked15", "issue": "ten_capture_groups_not_visible"})

    source_search = loaded.get("SOURCE_SEARCH_SATURATION_AUDIT", {})
    if source_search.get("ok") is not True:
        failures.append({"artifact": "source_search", "issue": "source_search_not_ok", "failures": source_search.get("failures")})
    required_categories = source_search.get("required_search_categories", {})
    if not required_categories or not all(required_categories.values()):
        failures.append({"artifact": "source_search", "issue": "required_search_categories_not_all_true", "categories": required_categories})

    recovered = loaded.get("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT", {})
    if recovered.get("ok") is not True:
        failures.append({"artifact": "recovered_rows", "issue": "recovered_row_audit_not_ok", "failures": recovered.get("failures")})
    if recovered.get("recovered_row_count") != 1213:
        failures.append({"artifact": "recovered_rows", "issue": "row_count_not_1213"})
    if recovered.get("forbidden_row_key_hits"):
        failures.append({"artifact": "recovered_rows", "issue": "forbidden_key_hits_present", "hits": recovered.get("forbidden_row_key_hits")})

    contract = loaded.get("PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT", {})
    if contract.get("ok") is not True:
        failures.append({"artifact": "contract", "issue": "contract_audit_not_ok", "failures": contract.get("failures")})
    if contract.get("contract_count") != 10:
        failures.append({"artifact": "contract", "issue": "contract_count_not_10"})
    if contract.get("all_cards_remain_blocked_for_results") is not True:
        failures.append({"artifact": "contract", "issue": "cards_not_all_blocked_for_results"})

    denominator = loaded.get("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT", {})
    if denominator.get("ok") is not True:
        failures.append({"artifact": "denominator", "issue": "denominator_audit_not_ok", "failures": denominator.get("failures")})
    if denominator.get("accepted_denominator_count") != 40:
        failures.append({"artifact": "denominator", "issue": "accepted_denominator_count_not_40"})
    if denominator.get("accepted_40_denominator_unchanged") is not True:
        failures.append({"artifact": "denominator", "issue": "accepted_denominator_changed"})

    target_rerun = loaded.get("TARGET_VERIFIER_TEST_RERUN_LEDGER", {})
    if target_rerun.get("target_verifier_ok") is not True or target_rerun.get("target_focused_tests_ok") is not True:
        failures.append({"artifact": "target_rerun", "issue": "target_verifier_or_tests_failed"})

    decision = loaded.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append({"artifact": "decision", "issue": "terminal_decision_not_accept", "decision": decision.get("terminal_decision")})
    if decision.get("terminal_blockers"):
        failures.append({"artifact": "decision", "issue": "terminal_blockers_present", "blockers": decision.get("terminal_blockers")})

    if not NEXT_G0_PROMPT.exists() or not NEXT_G0_STARTER.exists():
        failures.append({"artifact": "next_g0", "issue": "accepted_next_g0_prompt_or_starter_missing"})
    else:
        prompt_text = NEXT_G0_PROMPT.read_text(encoding="utf-8")
        for phrase in ("NO_PROMOTION_VERDICT", "validation_safe", "outcome_review_opened", "live_effect", "no validation/results"):
            if phrase not in prompt_text:
                failures.append({"artifact": "next_g0", "issue": "prompt_missing_required_phrase", "phrase": phrase})

    manifest = loaded.get("OUTPUT_MANIFEST", {})
    missing_manifest_paths = [row["path"] for row in manifest.get("artifacts", []) if not (REPO_ROOT / row["path"]).exists()]
    if missing_manifest_paths:
        failures.append({"artifact": "manifest", "issue": "manifest_paths_missing", "paths": missing_manifest_paths[:10]})
    if manifest.get("raw_market_blob_artifacts"):
        failures.append({"artifact": "manifest", "issue": "raw_market_blob_artifacts_present", "rows": manifest.get("raw_market_blob_artifacts")})

    status = git_status_entries()
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append({"artifact": "git_status", "issue": "scoped_forbidden_live_surface_present"})
    if not status["no_scoped_raw_market_blob"]:
        failures.append({"artifact": "git_status", "issue": "scoped_raw_market_blob_present"})

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures[:100],
        "syntax": syntax,
        "scoped_git_status": status,
        "terminal_decision": decision.get("terminal_decision"),
        "verified_counts": decision.get("verified_counts"),
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
    }
    if write:
        refresh_completion(result, mark_focused_tests_ok)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(write=True, mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
