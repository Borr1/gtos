from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_EXPANSION_AUDIT"
ROUTE_ID = "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_CONTROL_EVIDENCE_ONLY"
NEXT_G0_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
NEXT_G0_STARTER = (
    ROUTE_DIR / "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_STARTER_2026-05-12.txt"
)

REQUIRED_STEMS = [
    "CONTEXT_AND_TARGET_INPUT_INVENTORY",
    "CANDIDATE_COUNT_AUDIT",
    "SOURCE_FIELD_DESIGN_AUDIT",
    "DENOMINATOR_QUARANTINE_AUDIT",
    "NOVELTY_ANTI_BOXING_AUDIT",
    "SOURCE_SEARCH_AUDIT",
    "NEGATIVE_EVIDENCE_AUDIT",
    "BLOCKER_FOLLOWUP_LEDGER",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_scid_expansion_candidate_acceptance_design_audit_2026_05_12.py",
    "verify_g12_scid_expansion_candidate_acceptance_design_audit_2026_05_12.py",
    "test_g12_scid_expansion_candidate_acceptance_design_audit_2026_05_12.py",
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
    "changes_trading_risk_safety_prompt_decision_behavior",
]
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".zip", ".bin", ".jsonl.gz")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def syntax_parse() -> dict[str, Any]:
    failures = []
    for name in REQUIRED_PY:
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing python file: {name}")
            continue
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
                "scoped_raw_market_blob": scoped and path.lower().endswith(RAW_SUFFIXES),
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


def update_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if not completion_path.exists():
        return
    completion = read_json(completion_path)
    for item in completion.get("prompt_to_artifact_checklist", []):
        if item.get("requirement") == "G12 standalone verifier passed":
            item["satisfied"] = result["ok"]
            item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
        elif item.get("requirement") == "G12 focused tests passed" and mark_focused_tests_ok:
            item["satisfied"] = True
            item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit = [
        item for item in completion.get("prompt_to_artifact_checklist", []) if item["requirement"] != "Scoped commits complete"
    ]
    completion["standalone_verifier_ok"] = result["ok"]
    completion["focused_tests_ok"] = mark_focused_tests_ok
    completion["completion_standard_satisfied_before_final_commit"] = all(item.get("satisfied") is True for item in non_commit)
    completion["can_mark_goal_complete_after_commit"] = completion["completion_standard_satisfied_before_final_commit"]
    write_json(completion_path, completion)
    artifact_path("COMPLETION_AUDIT", ".md").write_text(
        "# Completion Audit\n\n```json\n"
        + json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )


def refresh_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = artifact_path("OUTPUT_MANIFEST", ".md")
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    excluded = {manifest_path.resolve(), manifest_md_path.resolve()}
    artifact_paths = []
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.resolve() not in excluded and path.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            artifact_paths.append(path)
    if NEXT_G0_PROMPT.exists():
        artifact_paths.append(NEXT_G0_PROMPT)
    artifacts = []
    for path in sorted(set(artifact_paths)):
        artifacts.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.suffix.lower() in {".scid", ".depth", ".parquet", ".zip", ".bin"},
            }
        )
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    write_json(manifest_path, manifest)
    manifest_md_path.write_text(
        "# Output Manifest\n\n```json\n"
        + json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )


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

    context = payloads.get("CONTEXT_AND_TARGET_INPUT_INVENTORY", {})
    counts = payloads.get("CANDIDATE_COUNT_AUDIT", {})
    source = payloads.get("SOURCE_FIELD_DESIGN_AUDIT", {})
    quarantine = payloads.get("DENOMINATOR_QUARANTINE_AUDIT", {})
    novelty = payloads.get("NOVELTY_ANTI_BOXING_AUDIT", {})
    search = payloads.get("SOURCE_SEARCH_AUDIT", {})
    negative = payloads.get("NEGATIVE_EVIDENCE_AUDIT", {})
    followup = payloads.get("BLOCKER_FOLLOWUP_LEDGER", {})
    decision = payloads.get("DECISION_LEDGER", {})
    manifest = payloads.get("OUTPUT_MANIFEST", {})

    if context.get("all_required_inputs_disk_backed") is not True:
        failures.append("context: not all required inputs are disk-backed")
    if counts.get("candidate_count_recomputed") != 24:
        failures.append("counts: total candidate count is not 24")
    expected_origins = {
        "preserved_original_8_from_target_input_design": 8,
        "preserved_g0_discovered_4_from_g0_synthesis": 4,
        "r4_artifact_search_discovered_additional_family": 12,
    }
    if counts.get("candidate_origin_counts_recomputed") != expected_origins:
        failures.append("counts: origin split is not exact 8/4/12")
    if counts.get("accepted_40_is_floor_not_ceiling") is not True or counts.get("all_candidates_denominator_inclusion_false") is not True:
        failures.append("counts: floor/quarantine flags failed")
    if counts.get("ok") is not True:
        failures.append("counts: audit ok flag false")

    if source.get("matrix_covers_inventory_exactly") is not True or source.get("criteria_covers_inventory_exactly") is not True:
        failures.append("source: matrix/criteria do not cover inventory exactly")
    if source.get("matrix_missing_required_controls") or source.get("weak_criteria_candidate_ids"):
        failures.append("source: missing controls or weak criteria")
    if source.get("novelty_guard_covers_all_candidates") is not True or source.get("ok") is not True:
        failures.append("source: novelty guard or ok flag failed")

    if quarantine.get("accepted_40_count_recomputed_from_source_mapping") != 40:
        failures.append("quarantine: accepted mapping count is not 40")
    if quarantine.get("accepted_40_count_recomputed_from_terminal_status") != 40:
        failures.append("quarantine: accepted terminal count is not 40")
    if quarantine.get("accepted_domain_count_recomputed") != 8:
        failures.append("quarantine: domain count is not 8")
    if set(quarantine.get("accepted_domain_counts_recomputed", {}).values()) != {5}:
        failures.append("quarantine: domain counts are not 5 each")
    if quarantine.get("candidate_overlap_count") != 0:
        failures.append("quarantine: candidate overlap with accepted 40 is nonzero")
    if quarantine.get("candidate_result_label_key_hits") or quarantine.get("safe_flag_failures"):
        failures.append("quarantine: result-label keys or safe-flag failures present")
    if quarantine.get("ok") is not True:
        failures.append("quarantine: audit ok flag false")

    if novelty.get("ok") is not True or not all(novelty.get("anti_boxing_checks", {}).values()):
        failures.append("novelty: anti-boxing checks failed")
    if len(novelty.get("r4_required_family_ids_present", [])) != 12:
        failures.append("novelty: not all R4 families present")

    if search.get("ok") is not True or not all(search.get("checks", {}).values()):
        failures.append("source search: checks failed")
    if search.get("source_inventory_count", 0) < 1:
        failures.append("source search: source inventory missing")

    if negative.get("ok") is not True or negative.get("negative_evidence_row_count", 0) < 6:
        failures.append("negative evidence: audit failed")

    if followup.get("ok") is not True or followup.get("terminal_blockers"):
        failures.append("followup: blockers present or target verifier failed")
    if not NEXT_G0_PROMPT.exists() or not NEXT_G0_STARTER.exists():
        failures.append("next G0 prompt or starter missing")
    elif len(NEXT_G0_STARTER.read_text(encoding="utf-8").splitlines()) != 1:
        failures.append("next G0 starter is not one physical line")

    if decision.get("terminal_decision") != TERMINAL_ACCEPT or decision.get("terminal_blockers"):
        failures.append("decision: terminal decision not accepted or blockers present")
    if decision.get("accepted_validation_execution") is not False or decision.get("accepted_strategy_performance") is not False:
        failures.append("decision: forbidden validation/performance acceptance")

    if manifest.get("all_required_artifact_families_covered") is not True:
        failures.append("manifest: required families not covered")
    if any(row.get("raw_market_blob") for row in manifest.get("artifacts", [])):
        failures.append("manifest: raw market blob present")

    syntax = syntax_parse()
    if not syntax["ok"]:
        failures.extend(syntax["failures"])
    status = git_status_entries()
    if status["no_scoped_forbidden_live_surface"] is not True or status["no_scoped_raw_market_blob"] is not True:
        failures.append("git status: scoped forbidden live surface or raw market blob")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "terminal_decision": decision.get("terminal_decision"),
        "candidate_count_verified": counts.get("candidate_count_recomputed"),
        "origin_counts_verified": counts.get("candidate_origin_counts_recomputed"),
        "accepted_40_count_verified": quarantine.get("accepted_40_count_recomputed_from_source_mapping"),
        "candidate_overlap_count_verified": quarantine.get("candidate_overlap_count"),
        "source_inventory_count_verified": search.get("source_inventory_count"),
        "target_verifier_ok": followup.get("target_verifier_ok"),
        "next_g0_prompt": rel(NEXT_G0_PROMPT),
        "syntax_parse": syntax,
        "scoped_git_status": status,
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
        "focused_tests_marked_ok": mark_focused_tests_ok,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    artifact_path("VERIFICATION_RESULT", ".md").write_text(
        "# Verification Result\n\n```json\n"
        + json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True)
        + "\n```\n",
        encoding="utf-8",
    )
    update_completion(result, mark_focused_tests_ok)
    refresh_manifest(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
