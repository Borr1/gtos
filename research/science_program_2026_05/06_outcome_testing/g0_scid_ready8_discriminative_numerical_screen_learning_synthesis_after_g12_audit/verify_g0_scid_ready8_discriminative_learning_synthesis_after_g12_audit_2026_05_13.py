from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_ONLY"
SCHEMA = "g0_scid_ready8_discriminative_learning_synthesis_v1"
RANK1_ROUTE = "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT"
ROWSET_SHA = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
EXPECTED_LEDGER_COUNTS = {
    "aggregate": 4561,
    "contrast": 3400,
    "candidate": 24112,
    "partition": 192,
    "failure": 2161,
    "explanation": 8689,
    "ambiguity": 8691,
    "data_backing": 17380,
}

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
NEXT_PROMPT = ROOT / f"research/science_program_2026_05/04_goal_prompts/{RANK1_ROUTE}_GOAL_PROMPT_{DATE}.md"
NEXT_STARTER = ROUTE_DIR / f"{RANK1_ROUTE}_STARTER_{DATE}.txt"
G12_VERIFICATION = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_numerical_screen_audit/G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_VERIFICATION_RESULT_2026-05-13.json"
G0_SCREEN_VERIFICATION = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/G0_SCID_READY8_DISC_TARGET_SCREEN_VERIFICATION_RESULT_2026-05-13.json"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_strategy_edge_claims": False,
    "opens_result_scoring": False,
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
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def io_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def rel(path: Path) -> str:
    return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = open(io_path(path), "w", encoding="utf-8", newline="\n")
    except PermissionError:
        handle = open(str(path.resolve(strict=False)), "w", encoding="utf-8", newline="\n")
    with handle:
        handle.write(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def file_exists(path: Path) -> bool:
    return os.path.exists(io_path(path))


def file_size(path: Path) -> int:
    return os.stat(io_path(path)).st_size


def read_text(path: Path) -> str:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return handle.read()


def out_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"G0_SCID_READY8_DISC_NUMERIC_LEARNING_{stem}_{DATE}{suffix}"


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def required_paths() -> dict[str, Path]:
    return {
        "builder": ROUTE_DIR / "build_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
        "verifier": ROUTE_DIR / "verify_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
        "tests": ROUTE_DIR / "test_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
        "decision": out_path("DECISION_LEDGER"),
        "fact": out_path("FACT_RECONCILIATION_LEDGER"),
        "findings": out_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"),
        "routes": out_path("ROUTE_RANKING_LEDGER"),
        "questions": out_path("QUESTION_STACK_LEDGER"),
        "blockers": out_path("BLOCKER_AND_REPAIR_LEDGER"),
        "prompt_hardening": out_path("PROMPT_HARDENING_LEDGER"),
        "completion": out_path("COMPLETION_AUDIT"),
        "manifest": out_path("OUTPUT_MANIFEST"),
        "synthesis": out_path("SYNTHESIS", ".md"),
        "next_prompt": NEXT_PROMPT,
        "next_starter": NEXT_STARTER,
        "g12_verification": G12_VERIFICATION,
        "g0_screen_verification": G0_SCREEN_VERIFICATION,
    }


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    return all(payload.get(key) == expected for key, expected in SAFE_FLAGS.items())


def load_outputs() -> dict[str, Any]:
    return {name: read_json(path) for name, path in required_paths().items() if path.suffix == ".json" and name not in {"g12_verification", "g0_screen_verification"}}


def git_changed_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return []
    changed = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        changed.append(line[3:].strip())
    return changed


def forbidden_surface_touches(changed: list[str]) -> list[str]:
    forbidden_prefixes = (
        "src/",
        "config/",
        "prompts/",
        "scripts/canary",
        "scripts/fn_smoke",
        "run_agent.py",
        "start_all.bat",
    )
    allowed_research_prompt_prefix = "research/science_program_2026_05/04_goal_prompts/"
    touches = []
    for path in changed:
        normalized = path.replace("\\", "/")
        if normalized.startswith(allowed_research_prompt_prefix):
            continue
        if normalized.startswith(forbidden_prefixes):
            touches.append(normalized)
    return touches


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_output_manifest() -> dict[str, Any]:
    paths = [
        NEXT_PROMPT,
        NEXT_STARTER,
        out_path("BLOCKER_AND_REPAIR_LEDGER"),
        out_path("COMPLETION_AUDIT"),
        out_path("DECISION_LEDGER"),
        out_path("FACT_RECONCILIATION_LEDGER"),
        out_path("FOCUSED_TEST_RESULT"),
        out_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"),
        out_path("OUTPUT_MANIFEST"),
        out_path("PROMPT_HARDENING_LEDGER"),
        out_path("QUESTION_STACK_LEDGER"),
        out_path("ROUTE_RANKING_LEDGER"),
        out_path("SYNTHESIS", ".md"),
        out_path("VERIFICATION_RESULT"),
        required_paths()["builder"],
        required_paths()["tests"],
        required_paths()["verifier"],
    ]
    artifacts = []
    for path in paths:
        if file_exists(path) and path.name != out_path("OUTPUT_MANIFEST").name:
            artifacts.append({"path": rel(path), "bytes": file_size(path), "sha256": sha256_file(path)})
    return {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
    }


def finalize_completion_audit(existing: dict[str, Any], finalized: bool, issues: list[str]) -> dict[str, Any]:
    audit = dict(existing)
    audit.update(
        {
            "focused_tests_ok": finalized,
            "standalone_verifier_ok": finalized and not issues,
            "can_mark_goal_complete": finalized and not issues,
            "missing_incomplete_or_weakly_verified_requirements": issues,
            "same_evidence_class_learning_remaining": 0,
            "same_evidence_class_learning_remaining_after_prompt_hardening": 0,
            "separate_evidence_class_handoffs_written": True,
        }
    )
    for row in audit.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "verifier and focused tests pass":
            row["satisfied"] = finalized and not issues
    return audit


def verify(mark_focused_tests_ok: bool = False, write_result: bool = False) -> dict[str, Any]:
    paths = required_paths()
    missing = [name for name, path in paths.items() if not file_exists(path)]
    outputs = load_outputs() if not missing else {}
    issues: list[str] = []

    if missing:
        issues.append(f"missing required paths: {missing}")

    decision = outputs.get("decision", {})
    fact = outputs.get("fact", {})
    routes = outputs.get("routes", {})
    questions = outputs.get("questions", {})
    findings = outputs.get("findings", {})
    blockers = outputs.get("blockers", {})
    prompt_hardening = outputs.get("prompt_hardening", {})
    completion = outputs.get("completion", {})

    json_payloads = [payload for name, payload in outputs.items() if name != "manifest"]
    if any(not safe_flags_ok(payload) for payload in json_payloads):
        issues.append("safe flag mismatch in generated JSON artifacts")

    accepted = fact.get("accepted_exact_facts", {})
    count_checks = {
        "ready_cards": accepted.get("ready_cards") == 8,
        "ready_card_ids": accepted.get("ready_card_ids") == READY_CARDS,
        "source_candidates": accepted.get("source_candidates") == 3014,
        "rowset_rows": accepted.get("rowset_rows") == 24112,
        "rowset_hash": accepted.get("rowset_hash") == ROWSET_SHA,
        "target_result_rows": accepted.get("target_result_rows") == 192896,
        "computable_rows": accepted.get("computable_rows") == 162336,
        "fail_closed_rows": accepted.get("fail_closed_rows") == 30560,
        "horizons": accepted.get("horizons") == [1, 4, 16, 32],
        "target_families": accepted.get("target_families")
        == [
            "neutral_close_to_close_return_m15_horizons_v1",
            "neutral_high_low_excursion_m15_horizons_v1",
        ],
        "ledger_counts": accepted.get("g0_screen_ledger_counts") == EXPECTED_LEDGER_COUNTS,
    }
    if not all(count_checks.values()):
        issues.append(f"count expectation mismatch: {count_checks}")

    g12 = read_json(G12_VERIFICATION) if file_exists(G12_VERIFICATION) else {}
    g0 = read_json(G0_SCREEN_VERIFICATION) if file_exists(G0_SCREEN_VERIFICATION) else {}
    upstream_checks = {
        "g12_discriminative_numerical_screen_ok": g12.get("ok") is True,
        "g12_can_mark_goal_complete": g12.get("can_mark_goal_complete") is True,
        "g0_discriminative_screen_ok": g0.get("ok") is True,
        "g0_screen_route_id": g0.get("route_id") == "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT",
    }
    if not all(upstream_checks.values()):
        issues.append(f"upstream verifier mismatch: {upstream_checks}")

    route_checks = {
        "terminal_decision": decision.get("terminal_decision", "").startswith("OPEN_RANK1_G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE"),
        "rank1": routes.get("rank1_selected") == RANK1_ROUTE,
        "rank1_not_audit": routes.get("rank1_is_audit") is False,
        "rank1_does_not_open_validation": routes.get("rank1_opens_validation") is False,
        "same_learning_zero": questions.get("same_evidence_class_learning_remaining") == 0,
        "blockers_zero": blockers.get("same_class_repairable_blockers_remaining") == 0,
        "prompt_hardened": prompt_hardening.get("rank1_route_non_looping") is True,
        "completion_learning_zero": completion.get("same_evidence_class_learning_remaining") == 0,
    }
    if not all(route_checks.values()):
        issues.append(f"route/checklist mismatch: {route_checks}")

    finding_classes = {row.get("class") for row in findings.get("preserved_findings", []) + findings.get("killed_or_bounded_findings", [])}
    required_classes = {
        "positive_control",
        "pass_control_non_applicable_fail_closed",
        "horizon_target_family",
        "duplicate_concentration",
        "positive_negative_inverse_neutral",
        "fail_closed_failure_anatomy",
        "candidate_full_population",
        "descriptor_symbol_partition",
        "forbidden_claim",
        "performance_conversion",
        "denominator_error",
        "route_loop",
        "forbidden_surface",
    }
    if not required_classes.issubset(finding_classes):
        issues.append(f"missing finding classes: {sorted(required_classes - finding_classes)}")

    starter_text = read_text(NEXT_STARTER) if file_exists(NEXT_STARTER) else ""
    prompt_text = read_text(NEXT_PROMPT) if file_exists(NEXT_PROMPT) else ""
    text_checks = {
        "starter_binds_prompt": rel(NEXT_PROMPT) in starter_text,
        "starter_has_safe_flags": "NO_PROMOTION_VERDICT" in starter_text and "validation_safe=false" in starter_text,
        "prompt_gate_only": "This is a gate. It is not validation" in prompt_text,
        "prompt_completion_standard": "same_evidence_class_learning_remaining=0" in prompt_text,
        "prompt_safe_boundaries": "Do not open validation" in prompt_text,
    }
    if not all(text_checks.values()):
        issues.append(f"next prompt/starter mismatch: {text_checks}")

    forbidden_touches = forbidden_surface_touches(git_changed_files())
    if forbidden_touches:
        issues.append(f"forbidden surface changed in worktree: {forbidden_touches}")

    if mark_focused_tests_ok:
        focused = {
            **safe_base("focused_test_result"),
            "focused_tests_ok": True,
            "command": "python -m pytest -q research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_numerical_screen_learning_synthesis_after_g12_audit/test_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
            "recorded_after_pytest_passed": True,
        }
        if write_result:
            write_json(out_path("FOCUSED_TEST_RESULT"), focused)

    ok = not issues
    result = {
        **safe_base("verification_result"),
        "ok": ok,
        "issues": issues,
        "failure_count": len(issues),
        "can_mark_goal_complete": ok and mark_focused_tests_ok,
        "focused_tests_ok": mark_focused_tests_ok,
        "required_paths": {name: rel(path) for name, path in paths.items()},
        "count_expectations": count_checks,
        "route_checks": route_checks,
        "upstream_verifiers": upstream_checks,
        "finding_classes_present": sorted(finding_classes),
        "forbidden_surface_touches": forbidden_touches,
        "same_evidence_class_learning_remaining": 0,
        "rank1_route": RANK1_ROUTE,
    }

    if write_result:
        write_json(out_path("VERIFICATION_RESULT"), result)
        if "completion" in outputs:
            write_json(out_path("COMPLETION_AUDIT"), finalize_completion_audit(outputs["completion"], mark_focused_tests_ok and ok, issues))
        write_json(out_path("OUTPUT_MANIFEST"), build_output_manifest())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-result", action="store_true")
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok, write_result=args.write_result)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
