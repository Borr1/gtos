"""Standalone verifier for SCID combined source-search/capture route."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "SCID_COMBINED_SOURCE_CAPTURE"
ROUTE_ID = "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE"
EVIDENCE_CLASS = "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY"
TERMINAL_DECISION = "BUILT_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_G12_AUDIT_REQUIRED"
G12_PROMPT_NAME = "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
CLOSEOUT_VERIFICATION = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACTIVE_QUESTION_STACK_AND_CHECKPOINT_LEDGER",
    "SEARCHED_ROOT_LEDGER",
    "HISTORICAL_SOURCE_STATE_RECOVERY_ATTEMPT_LEDGER",
    "SOURCE_STATE_JOIN_RECOVERY_CANDIDATE_LEDGER",
    "ANTI_BOXING_ROUTE_DISCOVERY_LEDGER",
    "FORWARD_CAPTURE_CONTRACT",
    "SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION",
    "IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER",
    "RANKED_CONTINUATION_BUNDLE",
    "CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]
REQUIRED_PY = [
    "build_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
    "verify_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
    "test_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
]
REQUIRED_FIELD_GROUPS = {
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
}
REQUIRED_SEARCH_ROOTS = {
    "accepted_strategy_field_packet",
    "accepted_g12_g0_strategy_field_artifacts",
    "accepted_scid_candidate_input_and_neutral_artifacts",
    "source_control_sibling_routes",
    "shadow_logs_source_safe_nonbroker",
    "program_control_artifacts",
    "pipeline_state_artifacts",
    "knowledge_base_nonbroker_records",
    "repo_data_text_manifests_only",
    "repo_research_archive",
    "prior_worktree_gtos_otb",
    "prior_worktree_gtos_otl",
    "prior_recovery_cache",
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
RAW_MARKET_SUFFIXES = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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
        "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/",
        f"research/science_program_2026_05/04_goal_prompts/{G12_PROMPT_NAME}",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "forbidden_live_surface_path": scoped and path.startswith(forbidden_live_prefixes),
                "raw_market_blob_path": scoped and path.endswith(RAW_MARKET_SUFFIXES),
            }
        )
    scoped = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped,
        "no_forbidden_live_surface_in_scoped_entries": not any(row["forbidden_live_surface_path"] for row in scoped),
        "no_raw_market_blob_in_scoped_entries": not any(row["raw_market_blob_path"] for row in scoped),
    }


def refresh_manifest_hashes() -> None:
    if not OUTPUT_MANIFEST.exists():
        return
    manifest = load_json(OUTPUT_MANIFEST)
    for artifact in manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        if path.exists() and path.resolve() != OUTPUT_MANIFEST.resolve():
            artifact["sha256"] = sha256_file(path)
            artifact["bytes"] = path.stat().st_size
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_verification(result: dict[str, Any], mark_focused_tests_ok: bool = False) -> None:
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    if COMPLETION_AUDIT.exists():
        completion = load_json(COMPLETION_AUDIT)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        completion["completion_standard_satisfied"] = result["ok"]
        completion["can_mark_goal_complete"] = result["ok"]
        COMPLETION_AUDIT.write_text(json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    if CLOSEOUT_VERIFICATION.exists():
        closeout = load_json(CLOSEOUT_VERIFICATION)
        closeout["standalone_verifier_ok"] = result["ok"]
        closeout["verifier_pending"] = False
        if mark_focused_tests_ok:
            closeout["focused_tests_ok"] = True
            closeout["focused_tests_pending"] = False
        CLOSEOUT_VERIFICATION.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    refresh_manifest_hashes()


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
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
    prompt_path = PROMPT_DIR / G12_PROMPT_NAME
    if not prompt_path.exists():
        failures.append(f"missing next G12 prompt: {repo_path(prompt_path)}")

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
            failures.append(f"{stem}: promotion_verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: safe flag {flag} expected false got {payload.get(flag)!r}")

    candidate_path = ROUTE_DIR / f"{PREFIX}_CANDIDATE_SOURCE_CAPTURE_STATUS_{DATE_TAG}.jsonl"
    if not candidate_path.exists():
        failures.append(f"missing candidate source/capture status jsonl: {repo_path(candidate_path)}")
        candidate_rows = []
    else:
        candidate_rows = load_jsonl(candidate_path)
        ids = [row.get("candidate_input_row_id") for row in candidate_rows]
        dupes = [row.get("duplicate_proxy_denominator_key") for row in candidate_rows]
        if len(candidate_rows) != 3014:
            failures.append(f"candidate row count mismatch: {len(candidate_rows)}")
        if len(set(ids)) != 3014:
            failures.append(f"unique candidate id count mismatch: {len(set(ids))}")
        if len(set(dupes)) != 3014:
            failures.append(f"unique duplicate denominator key count mismatch: {len(set(dupes))}")
        status_counts: dict[str, Counter[str]] = {}
        for row in candidate_rows:
            if row.get("route_id") != ROUTE_ID:
                failures.append("candidate row route_id mismatch")
                break
            for flag in SAFE_FALSE_FLAGS:
                if row.get(flag) is not False:
                    failures.append(f"candidate row safe flag {flag} mismatch for {row.get('candidate_input_row_id')}")
                    break
            for field, status_payload in row.get("field_statuses", {}).items():
                status_counts.setdefault(field, Counter())[status_payload.get("status")] += 1
        for field in [
            "canonical_candidate_and_denominator",
            "source_symbol_session_partition",
            "source_control_coverage_not_computable_reasons",
        ]:
            if status_counts.get(field, {}).get("RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE") != 3014:
                failures.append(f"{field}: expected 3014 recovered rows")
        for field in [
            "intended_side_direction",
            "intended_entry_reference",
            "intended_stop_reference",
            "intended_target_reference",
            "poi_type_bounds_source",
            "framework_setup_family",
            "lifecycle_fill_cancel_expiry_source_status",
        ]:
            if status_counts.get(field, {}).get("NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN") != 3014:
                failures.append(f"{field}: expected 3014 non-generatable capture-contract rows")
        for field in ["lower_timeframe_asof_path_availability", "future_orderflow_depth_proxy_requirements"]:
            if status_counts.get(field, {}).get("RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN") != 3014:
                failures.append(f"{field}: expected 3014 recoverable market-context capture-contract rows")
        if status_counts.get("baseline_control_fields", {}).get("CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS") != 3014:
            failures.append("baseline_control_fields: expected 3014 control-contract rows")
        if status_counts.get("broker_account_order_history_deal_position_evidence", {}).get("FORBIDDEN_IN_THIS_EVIDENCE_CLASS") != 3014:
            failures.append("broker forbidden field count mismatch")

    if "SEARCHED_ROOT_LEDGER" in payloads:
        searched = set(payloads["SEARCHED_ROOT_LEDGER"].get("searched_root_ids", []))
        missing = REQUIRED_SEARCH_ROOTS - searched
        if missing:
            failures.append(f"searched roots missing: {sorted(missing)}")
        totals = payloads["SEARCHED_ROOT_LEDGER"].get("totals", {})
        if totals.get("text_files_scanned", 0) <= 0:
            failures.append("searched-root ledger scanned no text files")
        if payloads["SEARCHED_ROOT_LEDGER"].get("source_search_result") != "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS":
            failures.append("searched-root terminal source-search result mismatch")

    if "FORWARD_CAPTURE_CONTRACT" in payloads:
        groups = {row.get("field_group") for row in payloads["FORWARD_CAPTURE_CONTRACT"].get("field_groups", [])}
        missing = REQUIRED_FIELD_GROUPS - groups
        if missing:
            failures.append(f"capture contract missing field groups: {sorted(missing)}")
        for entry in payloads["FORWARD_CAPTURE_CONTRACT"].get("field_groups", []):
            for key in [
                "future_source_or_logger",
                "required_fields",
                "parser_requirement",
                "schema_version_required",
                "redaction_rule",
                "as_of_rule",
                "no_leak_rule",
                "g12_acceptance_requirement",
            ]:
                if key not in entry or entry[key] in (None, "", []):
                    failures.append(f"capture contract entry {entry.get('field_group')} missing {key}")

    if "OUTPUT_MANIFEST" in payloads:
        manifest = payloads["OUTPUT_MANIFEST"]
        covered = manifest.get("required_artifact_families_covered", {})
        missing = [key for key, value in covered.items() if value is not True]
        if missing:
            failures.append(f"manifest required artifact families false: {missing}")
        raw_paths = [row["path"] for row in manifest.get("artifacts", []) if row.get("raw_market_blob")]
        if raw_paths:
            failures.append(f"raw market blobs in manifest: {raw_paths[:10]}")

    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8")
        for text in [
            "Independent G12",
            "3,014",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "broker account/order/history/deal/position evidence",
            "prompt/config/risk/safety/execution/canary/selector",
            "strategy intent is inferred from price",
        ]:
            if text not in prompt_text:
                failures.append(f"G12 prompt missing required text: {text}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if not git_status["no_forbidden_live_surface_in_scoped_entries"]:
        failures.append("scoped git status includes forbidden live-surface path")
    if not git_status["no_raw_market_blob_in_scoped_entries"]:
        failures.append("scoped git status includes raw market blob path")

    result = {
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "candidate_rows_verified": len(candidate_rows),
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_verification(result, mark_focused_tests_ok=mark_focused_tests_ok)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(mark_focused_tests_ok="--mark-focused-tests-ok" in sys.argv), indent=2, sort_keys=True))
