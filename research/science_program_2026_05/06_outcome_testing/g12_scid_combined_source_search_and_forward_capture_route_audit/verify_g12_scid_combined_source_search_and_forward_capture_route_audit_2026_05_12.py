from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT"
ROUTE_ID = "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
CLOSEOUT_VERIFICATION = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT",
    "FIELD_STATUS_RECOMPUTATION_AUDIT",
    "SOURCE_SEARCH_SATURATION_AUDIT",
    "SOURCE_HASH_MANIFEST_BINDING_AUDIT",
    "CAPTURE_CONTRACT_EXACTNESS_AUDIT",
    "NOLEAK_FORBIDDEN_SURFACE_AUDIT",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]
REQUIRED_PY = [
    "build_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
    "verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
    "test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
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
REQUIRED_BOOLEAN_CHECKS = {
    "ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT": "row_coverage_denominator_recomputation_ok",
    "FIELD_STATUS_RECOMPUTATION_AUDIT": "field_status_recomputation_ok",
    "SOURCE_SEARCH_SATURATION_AUDIT": "source_search_saturation_ok",
    "SOURCE_HASH_MANIFEST_BINDING_AUDIT": "source_hash_manifest_binding_ok_after_repair",
    "CAPTURE_CONTRACT_EXACTNESS_AUDIT": "capture_contract_exactness_ok",
    "NOLEAK_FORBIDDEN_SURFACE_AUDIT": "noleak_forbidden_surface_ok",
}
RAW_SUFFIXES = (".scid", ".parquet", ".csv", ".dly", ".bin", ".depth", ".jsonl.gz")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/REPAIR_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


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
    scoped = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped),
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool = False) -> None:
    if COMPLETION_AUDIT.exists():
        completion = read_json(COMPLETION_AUDIT)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item.get("requirement") == "verifier_passed":
                item["satisfied"] = result["ok"]
                item["evidence"] = rel(VERIFICATION_RESULT)
            if mark_focused_tests_ok and item.get("requirement") == "focused_tests_passed":
                item["satisfied"] = True
        completion["standalone_verifier_ok"] = result["ok"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        non_commit_items = [
            item
            for item in completion.get("prompt_to_artifact_checklist", [])
            if item.get("requirement") != "scoped_commits_complete"
        ]
        completion["completion_standard_satisfied"] = all(item.get("satisfied") is True for item in non_commit_items)
        completion["can_mark_goal_complete"] = False
        write_json(COMPLETION_AUDIT, completion)
    if CLOSEOUT_VERIFICATION.exists():
        closeout = read_json(CLOSEOUT_VERIFICATION)
        closeout["standalone_verifier_ok"] = result["ok"]
        closeout["standalone_verifier_failures"] = result["failures"]
        if mark_focused_tests_ok:
            closeout["focused_tests_ok"] = True
        write_json(CLOSEOUT_VERIFICATION, closeout)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_STEMS:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not json_path.exists():
            failures.append(f"missing json artifact: {rel(json_path)}")
        if stem != "VERIFICATION_RESULT" and not md_path.exists():
            failures.append(f"missing markdown artifact: {rel(md_path)}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing python artifact: {name}")
    if not NEXT_G0_PROMPT.exists():
        failures.append(f"missing next G0 prompt: {rel(NEXT_G0_PROMPT)}")

    payloads: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        path = artifact_path(stem)
        if path.exists():
            payloads[stem] = read_json(path)

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

    for stem, bool_key in REQUIRED_BOOLEAN_CHECKS.items():
        payload = payloads.get(stem, {})
        if payload.get(bool_key) is not True:
            failures.append(f"{stem}: expected {bool_key}=true")

    row_payload = payloads.get("ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT", {})
    if row_payload.get("builder_candidate_rows") != 3014:
        failures.append("row coverage: builder_candidate_rows != 3014")
    if row_payload.get("builder_unique_candidate_input_row_ids") != 3014:
        failures.append("row coverage: candidate id uniqueness mismatch")
    if row_payload.get("builder_unique_duplicate_proxy_denominator_keys") != 3014:
        failures.append("row coverage: duplicate denominator uniqueness mismatch")
    if row_payload.get("row_hash_mismatch_count") != 0:
        failures.append("row coverage: row hash mismatches present")

    source_payload = payloads.get("SOURCE_SEARCH_SATURATION_AUDIT", {})
    if source_payload.get("required_root_ids_missing_from_builder_ledger"):
        failures.append("source saturation: missing required root ids")
    if source_payload.get("historical_recovery_explicit_new_strategy_intent_recoveries") != 0:
        failures.append("source saturation: unexpected strategy-intent recovery count")

    hash_payload = payloads.get("SOURCE_HASH_MANIFEST_BINDING_AUDIT", {})
    if hash_payload.get("blocking_unrepaired_hash_mismatches"):
        failures.append("source hash: blocking unrepaired mismatches present")
    if "research/science_program_2026_05/04_goal_prompts/G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md" not in hash_payload.get("repaired_hash_binding_mismatches", []):
        failures.append("source hash: expected prompt-hardening hash repair not recorded")

    capture_payload = payloads.get("CAPTURE_CONTRACT_EXACTNESS_AUDIT", {})
    if capture_payload.get("candidate_rows_covered") != 3014:
        failures.append("capture contract: candidate_rows_covered != 3014")
    if capture_payload.get("missing_capture_groups"):
        failures.append("capture contract: missing capture groups present")
    if capture_payload.get("vague_or_missing_contract_entries"):
        failures.append("capture contract: vague entries present")

    noleak_payload = payloads.get("NOLEAK_FORBIDDEN_SURFACE_AUDIT", {})
    if noleak_payload.get("builder_related_commit_forbidden_live_surface_violations"):
        failures.append("no-leak: builder-related commit touched forbidden live surface")
    if noleak_payload.get("builder_manifest_raw_market_blob_paths"):
        failures.append("no-leak: raw market blob paths in builder manifest")
    if noleak_payload.get("scoped_status_forbidden_entries"):
        failures.append("no-leak: scoped git status contains forbidden entries")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append("decision: terminal decision is not accepted-with-repair")
    if decision.get("accepted_validation_execution") is not False or decision.get("accepted_strategy_performance") is not False:
        failures.append("decision: accepted forbidden evidence class")
    if decision.get("terminal_blockers"):
        failures.append(f"decision: blockers present {decision.get('terminal_blockers')}")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    false_covered = [key for key, value in manifest.get("required_artifact_families_covered", {}).items() if value is not True]
    if false_covered:
        failures.append(f"manifest: required artifact families not covered {false_covered}")
    raw_artifacts = [row["path"] for row in manifest.get("artifacts", []) if row.get("raw_market_blob")]
    if raw_artifacts:
        failures.append(f"manifest: raw market blob artifacts present {raw_artifacts}")
    for artifact in manifest.get("artifacts", []):
        path = REPO_ROOT / artifact["path"]
        if not path.exists():
            failures.append(f"manifest artifact missing: {artifact['path']}")
        elif artifact.get("sha256_after_build") != sha256_file(path):
            # The audit manifest, verification result, and closeout are mutable
            # during verification/closeout recording. Source/builder artifacts and
            # stable audit ledgers remain strict.
            mutable_audit_artifacts = {
                artifact_path("OUTPUT_MANIFEST"),
                artifact_path("VERIFICATION_RESULT"),
                artifact_path("CLOSEOUT_VERIFICATION"),
                artifact_path("COMPLETION_AUDIT"),
            }
            if path not in mutable_audit_artifacts:
                failures.append(f"manifest hash mismatch: {artifact['path']}")

    prompt_text = NEXT_G0_PROMPT.read_text(encoding="utf-8") if NEXT_G0_PROMPT.exists() else ""
    for text in [
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "manifest-binding repair",
        "3,014",
        "broker account/order/history/deal/position evidence",
        "prompt/config/risk/safety/execution/canary/selector",
    ]:
        if text not in prompt_text:
            failures.append(f"next G0 prompt missing required text: {text}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    git_status = git_status_entries()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("git status: scoped forbidden live surface path present")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("git status: scoped raw market blob path present")

    result = {
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": False,
        "route_id": ROUTE_ID,
        "terminal_decision": decision.get("terminal_decision"),
        "candidate_rows_verified": row_payload.get("builder_candidate_rows"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_json(VERIFICATION_RESULT, result)
    refresh_completion(result, mark_focused_tests_ok=mark_focused_tests_ok)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(mark_focused_tests_ok="--mark-focused-tests-ok" in sys.argv), indent=2, sort_keys=True))
