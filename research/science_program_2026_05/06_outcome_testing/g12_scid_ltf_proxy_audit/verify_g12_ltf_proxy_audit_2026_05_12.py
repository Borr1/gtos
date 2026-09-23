"""Verifier for the G12 SCID LTF/orderflow/proxy source-expansion audit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_LTF_OF_PROXY_EXPANSION_AUDIT"
ROUTE_ID = "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT"
EVIDENCE_CLASS = "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_CONTROL_EVIDENCE_ONLY"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
CONTROL_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

JSON_STEMS = {
    "CONTEXT_ANCHOR": "context_anchor",
    "CANDIDATE_BOUNDARY_CAPTURE_GROUP_RECOMPUTATION_AUDIT": "candidate_boundary_capture_groups_ok",
    "SOURCE_INVENTORY_HASH_DEFERRAL_AUDIT": "source_inventory_hash_deferral_ok",
    "ACQUISITION_LADDER_SATURATION_AUDIT": "acquisition_ladder_saturation_ok",
    "COVERAGE_MATRIX_RECOMPUTATION_AUDIT": "coverage_matrices_ok",
    "PROXY_VALIDITY_APPROVAL_ASOF_AUDIT": "proxy_validity_approval_asof_ok",
    "NOLEAK_FORBIDDEN_SURFACE_AUDIT": "noleak_forbidden_surface_ok",
    "DECISION_LEDGER": "decision_ledger",
    "COMPLETION_AUDIT": "completion_audit",
    "CLOSEOUT_VERIFICATION": "closeout_verification",
    "OUTPUT_MANIFEST": "output_manifest",
}
PYTHON_ARTIFACTS = [
    ROUTE_DIR / "build_g12_ltf_proxy_audit_2026_05_12.py",
    ROUTE_DIR / "verify_g12_ltf_proxy_audit_2026_05_12.py",
    ROUTE_DIR / "test_g12_ltf_proxy_audit_2026_05_12.py",
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
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}
RAW_SUFFIXES = {".scid", ".depth", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
    "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def git_status_entries() -> dict[str, Any]:
    result = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=False)
    entries = []
    for line in (result.stdout or "").splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        entries.append(
            {
                "raw": line,
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and Path(path).suffix.lower() in RAW_SUFFIXES,
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": result.returncode,
        "stderr": (result.stderr or "").splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
        "unrelated_dirty_entry_count": len(entries) - len(scoped_entries),
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    verification_path = artifact_path("VERIFICATION_RESULT")
    write_json(verification_path, result)

    completion_path = artifact_path("COMPLETION_AUDIT")
    closeout_path = artifact_path("CLOSEOUT_VERIFICATION")
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if completion_path.exists():
        completion = read_json(completion_path)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item["requirement"] == "g12_audit_standalone_verifier_passed":
                item["satisfied"] = result["ok"]
                item["evidence"] = rel(verification_path)
            if item["requirement"] == "g12_audit_focused_tests_passed" and mark_focused_tests_ok:
                item["satisfied"] = True
                item["evidence"] = rel(Path(__file__).with_name("test_g12_ltf_proxy_audit_2026_05_12.py"))
        completion["standalone_verifier_ok"] = result["ok"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        completion["missing_incomplete_or_weakly_verified_requirements"] = [
            item["requirement"] for item in completion.get("prompt_to_artifact_checklist", []) if not item["satisfied"]
        ]
        completion["completion_standard_satisfied"] = not completion["missing_incomplete_or_weakly_verified_requirements"]
        completion["can_mark_goal_complete"] = completion["completion_standard_satisfied"]
        write_json(completion_path, completion)
        write_md(completion_path.with_suffix(".md"), "Completion Audit", completion)
    if closeout_path.exists():
        closeout = read_json(closeout_path)
        closeout["g12_audit_verifier"] = {
            "returncode": 0 if result["ok"] else 1,
            "status": "passed" if result["ok"] else "failed",
            "result_path": rel(verification_path),
            "failures": result["failures"],
        }
        if mark_focused_tests_ok:
            closeout["g12_audit_focused_pytest"] = {
                "returncode": 0,
                "status": "passed_after_focused_pytest_command",
                "test_path": rel(PYTHON_ARTIFACTS[-1]),
            }
        closeout["g12_audit_verifier_ok"] = result["ok"]
        if mark_focused_tests_ok:
            closeout["g12_audit_focused_tests_ok"] = True
        closeout["closeout_ok"] = (
            closeout.get("source_route_verifier_ok") is True
            and closeout.get("source_route_focused_tests_ok") is True
            and closeout.get("g12_audit_verifier_ok") is True
            and closeout.get("g12_audit_focused_tests_ok") is True
        )
        write_json(closeout_path, closeout)
        write_md(closeout_path.with_suffix(".md"), "Closeout Verification", closeout)
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for artifact in manifest.get("artifacts", []):
            path = ROOT / artifact["path"]
            artifact["exists_after_build"] = path.exists()
            artifact["sha256_after_build"] = sha256_file(path) if path.exists() else None
        write_json(manifest_path, manifest)
        write_md(manifest_path.with_suffix(".md"), "Output Manifest", manifest)


def verify(write: bool = True, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    loaded: dict[str, Any] = {}
    for stem, ok_key in JSON_STEMS.items():
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not json_path.exists():
            failures.append(f"missing json artifact: {rel(json_path)}")
            continue
        loaded[stem] = read_json(json_path)
        if stem != "VERIFICATION_RESULT" and not md_path.exists():
            failures.append(f"missing markdown artifact: {rel(md_path)}")
        payload = loaded[stem]
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        for flag, expected in SAFE_FLAGS.items():
            if payload.get(flag) != expected:
                failures.append(f"{stem}: {flag} expected {expected!r}, observed {payload.get(flag)!r}")
        if ok_key.endswith("_ok") and payload.get(ok_key) is not True:
            failures.append(f"{stem}: {ok_key} not true")

    for path in PYTHON_ARTIFACTS:
        if not path.exists():
            failures.append(f"missing python artifact: {rel(path)}")
    syntax = syntax_parse([path for path in PYTHON_ARTIFACTS if path.exists()])
    failures.extend(syntax["failures"])

    candidate = loaded.get("CANDIDATE_BOUNDARY_CAPTURE_GROUP_RECOMPUTATION_AUDIT", {})
    summary = candidate.get("candidate_summary_recomputed", {})
    if summary.get("candidate_rows") != 3014:
        failures.append("candidate boundary: candidate_rows != 3014")
    if summary.get("unique_candidate_input_row_ids") != 3014:
        failures.append("candidate boundary: unique candidate ids != 3014")
    if summary.get("unique_duplicate_proxy_denominator_keys") != 3014:
        failures.append("candidate boundary: unique duplicate keys != 3014")
    if len(candidate.get("ten_capture_groups_recomputed_from_reconciliation", [])) != 10:
        failures.append("candidate boundary: ten capture groups not preserved")
    if candidate.get("builder_reconciliation_mismatches"):
        failures.append("candidate boundary: builder/reconciliation mismatches present")

    inventory = loaded.get("SOURCE_INVENTORY_HASH_DEFERRAL_AUDIT", {})
    if inventory.get("source_inventory_count_recomputed") != 844:
        failures.append("inventory: expected 844 source rows")
    if inventory.get("hash_mismatch_count") != 0:
        failures.append("inventory: hash mismatches present")
    if inventory.get("missing_hash_or_deferral_count") != 0:
        failures.append("inventory: rows missing hash or deferral")
    if inventory.get("raw_market_blob_commits_added") != 0:
        failures.append("inventory: raw market blob commit count nonzero")
    if inventory.get("forbidden_broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append("inventory: forbidden broker/account/order evidence consumed")

    ladder = loaded.get("ACQUISITION_LADDER_SATURATION_AUDIT", {})
    if ladder.get("searched_root_count_recomputed") != 14:
        failures.append("ladder: expected 14 searched roots")
    if ladder.get("selected_source_count_sum_recomputed") != 844:
        failures.append("ladder: selected source count does not sum to 844")
    if ladder.get("searched_beyond_current_worktree") is not True:
        failures.append("ladder: did not search beyond current worktree")
    if ladder.get("root_exists_mismatches"):
        failures.append("ladder: root existence mismatches present")

    coverage = loaded.get("COVERAGE_MATRIX_RECOMPUTATION_AUDIT", {})
    if coverage.get("result_denominator_opened") is not False:
        failures.append("coverage: result denominator opened")
    if coverage.get("missing_candidate_groups"):
        failures.append("coverage: candidate groups missing")
    if coverage.get("matrix_source_count_mismatches"):
        failures.append("coverage: matrix source count mismatches present")

    proxy = loaded.get("PROXY_VALIDITY_APPROVAL_ASOF_AUDIT", {})
    if proxy.get("all_proxy_rows_context_only") is not True:
        failures.append("proxy: proxy rows not all context-only")
    if proxy.get("broker_native_cfd_truth_claims") != 0:
        failures.append("proxy: broker-native CFD truth claims present")
    if proxy.get("proxy_label_failures"):
        failures.append("proxy: label failures present")
    if proxy.get("vague_gate_failures"):
        failures.append("approval: vague gate failures present")
    if proxy.get("unresolved_vague_blockers"):
        failures.append("approval: unresolved vague blockers present")

    noleak = loaded.get("NOLEAK_FORBIDDEN_SURFACE_AUDIT", {})
    if noleak.get("safe_flag_violations"):
        failures.append("noleak: safe flag violations present")
    if noleak.get("control_prompt_required_phrase_gaps"):
        failures.append("noleak: control prompt phrase gaps present")
    if noleak.get("related_commit_forbidden_surface_violations"):
        failures.append("noleak: related commit forbidden surface violations present")
    if noleak.get("builder_manifest_raw_market_blob_paths"):
        failures.append("noleak: builder manifest contains raw market blob paths")

    decision = loaded.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append("decision: terminal decision not accepted")
    if decision.get("terminal_blockers"):
        failures.append(f"decision: terminal blockers present {decision.get('terminal_blockers')}")

    closeout = loaded.get("CLOSEOUT_VERIFICATION", {})
    if closeout.get("source_route_verifier_ok") is not True:
        failures.append("closeout: source route verifier did not pass")
    if closeout.get("source_route_focused_tests_ok") is not True:
        failures.append("closeout: source route focused tests did not pass")

    manifest = loaded.get("OUTPUT_MANIFEST", {})
    if manifest.get("raw_market_blob_artifacts"):
        failures.append("manifest: raw market blob artifacts present")
    missing_manifest = [row["path"] for row in manifest.get("artifacts", []) if not (ROOT / row["path"]).exists()]
    if missing_manifest:
        failures.append(f"manifest: artifacts missing {missing_manifest[:5]}")

    prompt_text = CONTROL_PROMPT.read_text(encoding="utf-8") if CONTROL_PROMPT.exists() else ""
    for phrase in (
        "do not invent hypothetical blockers",
        "do not penalize correctly-labeled proxy/context sources",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "live_effect=false",
    ):
        if phrase not in prompt_text:
            failures.append(f"control prompt missing phrase: {phrase}")

    status = git_status_entries()
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append("git status: scoped forbidden live surface path present")
    if not status["no_scoped_raw_market_blob"]:
        failures.append("git status: scoped raw market blob path present")

    result = {
        "ok": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": decision.get("terminal_decision"),
        "candidate_rows_verified": summary.get("candidate_rows"),
        "source_inventory_count_verified": inventory.get("source_inventory_count_recomputed"),
        "syntax": syntax,
        "scoped_git_status": status,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
        "verification_note": (
            "This verifier checks the G12 audit artifacts and source-route verifier/test closeout. "
            "Run focused pytest, then rerun with --mark-focused-tests-ok to finalize completion flags."
        ),
    }
    if write:
        refresh_completion(result, mark_focused_tests_ok)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(write=True, mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
