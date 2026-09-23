"""Verifier for the G12 G0EXP R1 source-control audit."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
AUDIT_DIR = Path(__file__).resolve().parent
R1_DIR = (
    ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g0exp_r1_local_heavy_root_parser_hash_lineage_source_control"
)
DATE_TAG = "2026-05-13"
PREFIX = "G12_G0EXP_R1"
ROUTE_ID = "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT"
EVIDENCE_CLASS = "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_G0EXP_R1_SOURCE_CONTROL_AUDIT_WITH_SAME_CLASS_HASH_REPAIR"

REQUIRED_STEMS = [
    "RECOMPUTATION_EVIDENCE",
    "REPAIR_LEDGER",
    "VERIFIER_TEST_EVIDENCE",
    "DECISION_LEDGER",
    "NEXT_PROMPT_GUIDANCE",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
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


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return AUDIT_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"- **ok:** `{str(payload.get('ok')).lower()}`",
        f"- **failure_count:** `{len(payload.get('failures', []))}`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_flag_failures(payload: dict[str, Any], name: str) -> list[str]:
    failures = []
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{name}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{name}: evidence_class mismatch")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append(f"{name}: promotion_verdict mismatch")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{name}: {flag} is not false")
    return failures


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def verify(write_result: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, Any] = {}
    for stem in REQUIRED_STEMS:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not json_path.exists():
            failures.append(f"missing json artifact {rel(json_path)}")
            continue
        if not md_path.exists():
            failures.append(f"missing md artifact {rel(md_path)}")
        payload = read_json(json_path)
        payloads[stem] = payload
        failures.extend(safe_flag_failures(payload, stem))

    recomputation = payloads.get("RECOMPUTATION_EVIDENCE", {})
    if recomputation.get("r1_output_manifest_mismatches_after_repair") != []:
        failures.append("R1 output manifest still has mismatches after repair")
    if not recomputation.get("required_upstream_input_hash_rows") or not all(
        row.get("exists") for row in recomputation.get("required_upstream_input_hash_rows", [])
    ):
        failures.append("required upstream input hash rows missing or non-existent")

    repair = payloads.get("REPAIR_LEDGER", {})
    if repair.get("terminal_repair_status") != "CLOSED":
        failures.append("repair ledger not closed")
    if repair.get("remaining_exact_source_access_export_capture_requirements") != []:
        failures.append("repair ledger reports remaining source/access/export/capture requirements")

    verifier = payloads.get("VERIFIER_TEST_EVIDENCE", {})
    if verifier.get("r1_verifier_ok") is not True:
        failures.append("R1 verifier did not pass")
    if verifier.get("focused_tests_ok") is not True:
        failures.append("R1 focused tests did not pass")
    r1_final = verifier.get("r1_final_verification_result", {})
    if r1_final.get("ok") is not True or r1_final.get("focused_tests_marked_ok") is not True:
        failures.append("R1 final verification result is not focused-tests-marked ok")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision mismatch")
    assigned = decision.get("assigned_family_audit", {})
    if assigned.get("all_assigned_families_reduced_to_closed_or_exact") is not True:
        failures.append("assigned families are not closed/exact")
    if assigned.get("assigned_family_count") != 4:
        failures.append("assigned family count is not 4")
    parser = decision.get("parser_fingerprint_audit", {})
    if parser.get("missing_required_fingerprint_field_count") != 0:
        failures.append("parser matrix has missing required fingerprint fields")
    quarantine = decision.get("quarantine_audit", {})
    if quarantine.get("r1_new_denominator_rows_added") != 0:
        failures.append("R1 added denominator rows")
    if quarantine.get("adjacent_overflow_entered_accepted_40") != []:
        failures.append("adjacent overflow entered accepted-40 denominator")
    no_raw = decision.get("no_raw_blob_audit", {})
    if no_raw.get("raw_market_blob_artifact_count") != 0:
        failures.append("raw market blob appears in R1 manifest")
    if decision.get("safe_flag_audit", {}).get("safe_flag_failures") != []:
        failures.append("safe flag failures present")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion audit not satisfied")
    if completion.get("can_mark_goal_complete_after_scoped_commit") is not True:
        failures.append("completion audit does not allow goal completion after commit")
    checklist = completion.get("prompt_to_artifact_checklist", [])
    if not checklist or any(row.get("satisfied") is not True for row in checklist):
        failures.append("prompt-to-artifact checklist has unsatisfied rows")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    if manifest.get("raw_market_blob_artifact_count") != 0:
        failures.append("audit output manifest reports raw blob artifact")
    for row in manifest.get("artifacts", []):
        path = ROOT / row["path"]
        if not path.exists():
            failures.append(f"audit manifest path missing: {row['path']}")
        elif row.get("sha256") != sha256_file(path):
            failures.append(f"audit manifest hash mismatch: {row['path']}")

    syntax = syntax_parse(
        [
            AUDIT_DIR / "build_g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_2026_05_13.py",
            AUDIT_DIR / "verify_g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_2026_05_13.py",
            AUDIT_DIR / "test_g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_2026_05_13.py",
            R1_DIR / "verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
        ]
    )
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    result = {
        "schema_version": "g12_g0exp_r1_audit_verification_result_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": not failures,
        "failures": failures,
        "failure_count": len(failures),
        "terminal_decision": decision.get("terminal_decision"),
        "r1_verifier_ok": verifier.get("r1_verifier_ok"),
        "focused_tests_ok": verifier.get("focused_tests_ok"),
        "r1_output_manifest_mismatch_count_after_repair": len(
            recomputation.get("r1_output_manifest_mismatches_after_repair", [])
        ),
        "completion_standard_satisfied": completion.get("completion_standard_satisfied"),
        "syntax_parse": syntax,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    if write_result:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        write_md(artifact_path("VERIFICATION_RESULT", ".md"), "G12 G0EXP R1 Verification Result", result)
    return result


def main() -> None:
    result = verify(write_result=True)
    print(json.dumps({"ok": result["ok"], "failure_count": len(result["failures"]), "failures": result["failures"]}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
