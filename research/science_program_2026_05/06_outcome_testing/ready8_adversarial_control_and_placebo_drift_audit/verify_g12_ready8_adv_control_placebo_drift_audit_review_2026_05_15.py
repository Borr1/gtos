"""Verifier for the G12 READY8 adversarial-control review package."""

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
DATE_TAG = "2026-05-15"
PREFIX = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT"
ROUTE_ID = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT"
EVIDENCE_CLASS = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION"
)
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
]
REQUIRED_STEMS = [
    "RECOMPUTATION_LEDGER",
    "DISCREPANCY_REPAIR_LEDGER",
    "QUESTION_AMBIGUITY_ROUTE_LEDGER",
    "DECISION_LEDGER",
    "SATURATION_SELF_RED_TEAM_LEDGER",
    "COMPLETION_AUDIT",
    "FOCUSED_TEST_RESULT",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
    "verify_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
    "test_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
]
SCOPED_PREFIXES = (
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
    "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/",
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
    failures: list[str] = []
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


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
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
                "forbidden_live_surface": path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "raw_market_blob": path.lower().endswith(RAW_SUFFIXES),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_forbidden_live_surface": not any(row["forbidden_live_surface"] for row in scoped_entries),
        "no_raw_market_blob": not any(row["raw_market_blob"] for row in scoped_entries),
    }


def update_completion_and_focused(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    completion = read_json(completion_path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    completion["focused_tests_ok"] = bool(mark_focused_tests_ok or completion.get("focused_tests_ok") is True)
    completion["can_mark_goal_complete_after_verifier_and_tests"] = result["ok"] and completion["focused_tests_ok"]
    write_json(completion_path, completion)
    write_md(completion_path.with_suffix(".md"), "Completion Audit", completion)

    focused_path = artifact_path("FOCUSED_TEST_RESULT")
    focused = read_json(focused_path)
    if mark_focused_tests_ok:
        focused["status"] = "PASSED"
    focused["standalone_verifier_ok_at_last_update"] = result["ok"]
    write_json(focused_path, focused)
    write_md(focused_path.with_suffix(".md"), "Focused Test Result", focused)


def refresh_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = manifest_path.with_suffix(".md")
    manifest = read_json(manifest_path)
    artifact_paths = []
    for path in ROUTE_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith(PREFIX) or path.name in REQUIRED_PY:
            if path.suffix.lower() in {".json", ".md", ".py"}:
                artifact_paths.append(path)
    rows = []
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
            row["self_hash_policy"] = "self-referential manifest artifact hash omitted"
        rows.append(row)
    manifest["artifacts"] = rows
    manifest["artifact_count"] = len(rows)
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
            failures.append(f"missing JSON artifact: {rel(json_path)}")
            continue
        payloads[stem] = read_json(json_path)
        if not md_path.exists():
            failures.append(f"missing MD artifact: {rel(md_path)}")

    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing Python artifact: {name}")

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

    recomp = payloads.get("RECOMPUTATION_LEDGER", {})
    discrepancy = payloads.get("DISCREPANCY_REPAIR_LEDGER", {})
    decision = payloads.get("DECISION_LEDGER", {})
    questions = payloads.get("QUESTION_AMBIGUITY_ROUTE_LEDGER", {})
    saturation = payloads.get("SATURATION_SELF_RED_TEAM_LEDGER", {})
    completion = payloads.get("COMPLETION_AUDIT", {})
    manifest = payloads.get("OUTPUT_MANIFEST", {})

    expected_counts = {
        "adv001_placebo": 4288,
        "adv003_placebo": 12611,
        "baseline_drift": 3546,
        "duplicate_artifact": 3270,
        "comparison_mapping": 10563,
        "explained_weakened": 2622,
        "residual": 1,
        "concentration": 79746,
        "stress_vs_sealed": 45913,
        "underpower": 79746,
    }
    for key, expected in expected_counts.items():
        actual = recomp.get("row_count_recomputation", {}).get(key)
        if actual != expected:
            failures.append(f"{key}: expected {expected}, got {actual}")

    expected_class_counts = {
        "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
        "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
        "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
        "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
        "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318,
    }
    if recomp.get("control_envelope_classification_counts") != expected_class_counts:
        failures.append("control-envelope classification distribution mismatch")
    if recomp.get("control_envelope_math_mismatch_count") != 0:
        failures.append("control-envelope math mismatches remain")
    if recomp.get("control_match_missing_rows") != 0:
        failures.append("control-match missing rows remain")
    if recomp.get("target_manifest_hash_audit", {}).get("mismatch_count") != 0:
        failures.append("target manifest hash mismatches remain")
    if recomp.get("target_verifier_ok") is not True or recomp.get("target_verifier_can_mark_goal_complete") is not True:
        failures.append("target verifier is not accepted")
    if recomp.get("target_completion_can_mark_goal_complete") is not True:
        failures.append("target completion audit is not accepted")
    if recomp.get("control_cards_are_not_edge_cards") is not True:
        failures.append("ADV controls were not verified as controls")
    if recomp.get("explained_weakened_key_set_matches_mapping") is not True:
        failures.append("explained/weakened ledger key set mismatch")
    if recomp.get("residual_key_set_matches_mapping") is not True:
        failures.append("residual ledger key set mismatch")
    if sorted(recomp.get("nonadv_cards_observed", [])) != ["BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]:
        failures.append("non-ADV card set mismatch")

    if discrepancy.get("same_g12_repairable_items_remaining") != 0:
        failures.append("same-G12 repairable items remain")
    if discrepancy.get("issues") != []:
        failures.append("discrepancy issues remain")
    if decision.get("accepted") is not True:
        failures.append("decision does not accept artifact")
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision mismatch")
    if decision.get("terminal_blockers") != []:
        failures.append("terminal blockers present")
    if questions.get("unresolved_blockers") != [] or questions.get("ambiguities") != []:
        failures.append("unresolved blockers or ambiguities remain")
    if not questions.get("source_roots_inspected"):
        failures.append("source roots not recorded")
    if saturation.get("same_g12_repairable_items_remaining") != 0:
        failures.append("saturation ledger reports remaining repairable items")
    if saturation.get("artifact_inspection_gap_set") != [] or saturation.get("actionable_ambiguity_set") != []:
        failures.append("saturation gaps remain")
    if not completion.get("prompt_to_artifact_checklist") or not all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    ):
        failures.append("completion checklist incomplete")

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = manifest_path.with_suffix(".md")
    artifact_rows = manifest.get("artifacts", [])
    if not artifact_rows:
        failures.append("output manifest has no rows")
    for row in artifact_rows:
        path = ROOT / row["path"]
        if row.get("raw_market_blob") is True:
            failures.append(f"raw market blob in manifest: {row['path']}")
        if not path.exists():
            failures.append(f"missing manifest artifact: {row['path']}")
            continue
        if path.resolve() in {manifest_path.resolve(), manifest_md_path.resolve()}:
            if row.get("sha256") is not None:
                failures.append("manifest self-row hash is not null")
            continue
        if row.get("sha256") != sha256_file(path):
            failures.append(f"manifest hash mismatch: {row['path']}")

    syntax = syntax_parse()
    failures.extend(syntax["failures"])
    status = git_status_entries()
    if status["no_forbidden_live_surface"] is not True or status["no_raw_market_blob"] is not True:
        failures.append("scoped git status touches forbidden live surface or raw blob")

    focused_ok = bool(mark_focused_tests_ok or payloads.get("FOCUSED_TEST_RESULT", {}).get("status") == "PASSED")
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
        "focused_tests_marked_ok": focused_ok,
        "can_mark_goal_complete": not failures and focused_ok,
        "expected_counts_verified": expected_counts,
        "classification_counts_verified": expected_class_counts,
        "syntax_parse": syntax,
        "scoped_git_status": status,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    write_md(artifact_path("VERIFICATION_RESULT", ".md"), "Verification Result", result)
    update_completion_and_focused(result, mark_focused_tests_ok)
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
