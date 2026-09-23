"""Verifier for the G12 ADV-002 source-control audit package."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002"
DATE_TAG = "2026-05-13"
PREFIX = "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT"
ROUTE_ID = "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT"
EVIDENCE_CLASS = "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

REQUIRED_STEMS = [
    "TARGET_ARTIFACT_AUDIT",
    "REPAIR_LEDGER",
    "EXACT_REQUIREMENT_ROWS",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
    "verify_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
    "test_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "may_open_outcomes_or_results_in_this_route",
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
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_r11_adv_002_source_control_audit/",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")
RAW_SUFFIXES = (".parquet", ".scid", ".depth", ".zip", ".bin", ".gz")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


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
    proc = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=ROOT, text=True, capture_output=True, check=False)
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
    path = artifact_path("COMPLETION_AUDIT")
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    completion["focused_tests_ok"] = bool(mark_focused_tests_ok or completion.get("focused_tests_ok") is True)
    completion["can_mark_goal_complete_after_commit"] = result["ok"] and completion["focused_tests_ok"]
    write_json(path, completion)
    write_md(path.with_suffix(".md"), "Completion Audit", completion)


def refresh_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = manifest_path.with_suffix(".md")
    manifest = read_json(manifest_path)
    artifact_paths = []
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            artifact_paths.append(path)
    artifacts = []
    for path in sorted(set(artifact_paths)):
        row = {
            "path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "raw_market_blob": path.suffix.lower() in RAW_SUFFIXES,
        }
        if path.resolve() in {manifest_path.resolve(), manifest_md_path.resolve()}:
            row["sha256"] = None
            row["self_hash_policy"] = "self-referential manifest artifact hash omitted; use external git/blob hash"
        artifacts.append(row)
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    write_json(manifest_path, manifest)
    write_md(manifest_md_path, "Output Manifest", manifest)


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
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            failures.append(f"{stem}: promotion_verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: expected {flag}=false, got {payload.get(flag)!r}")

    target = payloads.get("TARGET_ARTIFACT_AUDIT", {})
    repair = payloads.get("REPAIR_LEDGER", {})
    requirements = payloads.get("EXACT_REQUIREMENT_ROWS", {})
    decision = payloads.get("DECISION_LEDGER", {})
    completion = payloads.get("COMPLETION_AUDIT", {})
    manifest = payloads.get("OUTPUT_MANIFEST", {})

    if target.get("target_verifier_ok") is not True:
        failures.append("target verifier was not ok")
    if target.get("target_completion_focused_tests_ok") is not True:
        failures.append("target focused tests were not marked ok")
    if target.get("safe_flag_failures"):
        failures.append("target safe flag failures present")
    if target.get("manifest_hash_audit", {}).get("mismatch_count") != 0:
        failures.append("target manifest hash mismatches remain")
    if len(target.get("source_requirements_present", [])) != 5:
        failures.append("target source requirements not exactly five")
    if len(target.get("mechanisms_present", [])) != 6:
        failures.append("target mechanisms not exactly six")

    if repair.get("post_repair_manifest_mismatch_count") != 0:
        failures.append("repair ledger did not close manifest mismatches")
    if {row.get("status") for row in repair.get("repairs", [])} != {"CLOSED"}:
        failures.append("not all repair rows are closed")

    req_rows = requirements.get("rows", [])
    expected_req_ids = {
        "ADV002-REQ-CANDIDATE-ID",
        "ADV002-REQ-DUPLICATE-KEY",
        "ADV002-REQ-SOURCE-HASH",
        "ADV002-REQ-GROUP-MEMBERSHIP",
        "ADV002-REQ-COLLISION-POLICY",
        "ADV002-REQ-ASOF-NOLEAK",
        "ADV002-REQ-CAPTURE-ROWS",
    }
    if {row.get("requirement_row_id") for row in req_rows} != expected_req_ids:
        failures.append("exact requirement rows do not match expected set")
    if requirements.get("vague_blockers") != []:
        failures.append("vague blockers present")

    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision mismatch")
    if decision.get("terminal_blockers") != []:
        failures.append("terminal blockers present")
    if decision.get("accepted_g12_control_evidence_only") is not True:
        failures.append("decision does not accept G12 control evidence")
    if decision.get("accepted_validation") is not False or decision.get("accepted_results_or_performance") is not False:
        failures.append("decision accepts forbidden validation/results")

    checklist = completion.get("prompt_to_artifact_checklist", [])
    if not checklist or not all(row.get("satisfied") for row in checklist):
        failures.append("completion checklist incomplete")
    if completion.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("completion terminal decision mismatch")

    artifact_rows = manifest.get("artifacts", [])
    if not artifact_rows:
        failures.append("output manifest has no artifact rows")
    if any(row.get("raw_market_blob") for row in artifact_rows):
        failures.append("output manifest includes raw market blob")
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    for row in artifact_rows:
        path = ROOT / row["path"]
        if path.resolve() in {manifest_path.resolve(), manifest_path.with_suffix(".md").resolve()}:
            if row.get("sha256") is not None:
                failures.append("output manifest self-derived hash is not null")
            continue
        if not path.exists():
            failures.append(f"manifest artifact missing: {row['path']}")
            continue
        if row.get("sha256") != sha256_file(path):
            failures.append(f"manifest artifact hash mismatch: {row['path']}")

    syntax = syntax_parse()
    failures.extend(syntax["failures"])
    status = git_status_entries()
    if status["no_scoped_forbidden_live_surface"] is not True or status["no_scoped_raw_market_blob"] is not True:
        failures.append("git status includes scoped forbidden live surface or raw blob")

    focused_ok = bool(mark_focused_tests_ok or completion.get("focused_tests_ok") is True)
    result = {
        "artifact_family": "verification_result",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "terminal_decision": decision.get("terminal_decision"),
        "can_mark_goal_complete": not failures and focused_ok,
        "focused_tests_marked_ok": focused_ok,
        "target_manifest_mismatch_count_verified": target.get("manifest_hash_audit", {}).get("mismatch_count"),
        "exact_requirement_row_count_verified": len(req_rows),
        "syntax_parse": syntax,
        "scoped_git_status": status,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    write_md(artifact_path("VERIFICATION_RESULT", ".md"), "Verification Result", result)
    update_completion(result, mark_focused_tests_ok)
    refresh_manifest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
