"""Verifier for G0EXP R1 local-heavy/parser/hash/lineage source controls."""

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
DATE_TAG = "2026-05-13"
PREFIX = "G0EXP_R1"
ROUTE_ID = "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL"
EVIDENCE_CLASS = "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER",
    "PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX",
    "ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF",
    "NO_RAW_MARKET_BLOB_COMMIT_AUDIT",
    "BLOCKER_PURSUIT_LEDGER",
    "DENOMINATOR_QUARANTINE_PROOF",
    "ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER",
    "SATURATION_SELF_RED_TEAM_LEDGER",
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
ASSIGNED_IDS = {"R4-EXP-ROOT-001", "R4-EXP-PARSER-001", "EXP-ADV-001", "R4-EXP-CODEHIST-001"}
REQUIRED_ROOT_LABELS = {
    "current_worktree",
    "absolute_main_repo_data",
    "absolute_main_repo_data_ticks",
    "tmp_gtos_nextwave_worktrees",
    "tmp_gtos_otb_prior_worktrees",
    "sierrachart_root",
}
RAW_SUFFIXES = {".parquet", ".scid", ".depth", ".jsonl.gz", ".zip", ".bin", ".db", ".sqlite", ".feather", ".h5", ".hdf5", ".xlsx"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


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


def git_status_rows() -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = path.startswith(rel(ROUTE_DIR)) or path.startswith(
            "research/science_program_2026_05/04_goal_prompts/G12_G0EXP_R1_"
        ) or path in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"}
        rows.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "raw_market_blob": Path(path).suffix.lower() in RAW_SUFFIXES or path.endswith(".jsonl.gz"),
                "forbidden_live_surface": path.startswith(("src/", "prompts/", "config/", "run_agent.py")),
            }
        )
    return rows


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = artifact_path("COMPLETION_AUDIT")
    md_path = artifact_path("COMPLETION_AUDIT", ".md")
    if not path.exists():
        return
    payload = read_json(path)
    payload["standalone_verifier_ok"] = result["ok"]
    payload["standalone_verifier_failures"] = result["failures"]
    payload["focused_tests_ok"] = bool(mark_focused_tests_ok)
    for row in payload.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "verifier and focused tests exist":
            row["satisfied"] = result["ok"]
            row["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit = [
        row
        for row in payload.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "scoped artifacts committed"
    ]
    payload["completion_standard_satisfied_before_commit"] = all(row.get("satisfied") is True for row in non_commit)
    payload["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in payload.get("prompt_to_artifact_checklist", [])
    )
    payload["can_mark_goal_complete"] = payload["completion_standard_satisfied_before_commit"]
    write_json(path, payload)
    lines = [
        "# G0EXP R1 Completion Audit",
        "",
        f"- **route_id:** `{ROUTE_ID}`",
        f"- **evidence_class:** `{EVIDENCE_CLASS}`",
        f"- **can_mark_goal_complete_before_commit:** `{str(payload['can_mark_goal_complete']).lower()}`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def verify(mark_focused_tests_ok: bool = False, write_result: bool = True) -> dict[str, Any]:
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
        try:
            payloads[stem] = read_json(json_path)
            failures.extend(safe_flag_failures(payloads[stem], stem))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid json {rel(json_path)}: {exc}")

    root = payloads.get("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER", {})
    root_labels = {row.get("label") for row in root.get("scanned_roots", [])}
    if not REQUIRED_ROOT_LABELS.issubset(root_labels):
        failures.append("source root ledger missing required root labels")
    if root.get("present_root_count", 0) < 5:
        failures.append("source root ledger has too few present roots")
    if root.get("hash_deferral_count", 0) < 1:
        failures.append("source root ledger lacks hash deferral records")
    if root.get("no_raw_market_blob_content_copied") is not True:
        failures.append("source root ledger did not assert no raw content copy")

    parser = payloads.get("PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX", {})
    parser_rows = parser.get("parser_rows", [])
    if parser.get("parser_file_count", 0) < 10:
        failures.append("parser matrix has too few parser/control files")
    if not any("scid" in row.get("path", "").lower() for row in parser_rows):
        failures.append("parser matrix lacks SCID-related parser/control file")
    if not all(row.get("parser_code_hash") and row.get("shape_fingerprint") for row in parser_rows[:20]):
        failures.append("parser matrix rows missing hashes or shape fingerprints")

    lineage = payloads.get("ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF", {})
    if lineage.get("all_required_inputs_exist") is not True:
        failures.append("lineage manifest has missing required inputs")
    if lineage.get("all_route_scripts_hashed") is not True:
        failures.append("lineage manifest did not hash route scripts")
    if lineage.get("raw_market_blob_outputs"):
        failures.append("lineage manifest reports raw market blob outputs")

    no_raw = payloads.get("NO_RAW_MARKET_BLOB_COMMIT_AUDIT", {})
    if no_raw.get("audit_status") != "PASS_NO_RAW_MARKET_BLOB_COMMIT_BY_THIS_ROUTE":
        failures.append("no raw market blob audit did not pass")
    if no_raw.get("no_forbidden_live_surface_in_scope") is not True:
        failures.append("forbidden live surface appears in scoped route status")

    blocker = payloads.get("BLOCKER_PURSUIT_LEDGER", {})
    assigned = blocker.get("assigned_family_rows", [])
    if {row.get("candidate_id") for row in assigned} != ASSIGNED_IDS:
        failures.append("blocker pursuit ledger does not cover assigned ids exactly")
    if blocker.get("all_assigned_families_reduced_to_closed_or_exact") is not True:
        failures.append("assigned families not reduced to closed/exact")

    denom = payloads.get("DENOMINATOR_QUARANTINE_PROOF", {})
    if denom.get("accepted_40_count_recomputed_from_upstream") != 40:
        failures.append("accepted-40 count not preserved")
    if denom.get("r1_new_denominator_rows_added") != 0:
        failures.append("R1 added denominator rows")
    if denom.get("result_or_validation_opened") is not False:
        failures.append("denominator proof opened result/validation")

    decision = payloads.get("ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER", {})
    if len(decision.get("adjacent_overflow_decisions", [])) < 6:
        failures.append("route decision ledger did not preserve adjacent/new overflow families")
    if any(row.get("accepted_40_card_denominator_inclusion") is not False for row in decision.get("adjacent_overflow_decisions", [])):
        failures.append("adjacent overflow row entered accepted-40 denominator")

    saturation = payloads.get("SATURATION_SELF_RED_TEAM_LEDGER", {})
    risks = {row.get("risk") for row in saturation.get("checks", [])}
    for risk in {"worktree_blindness", "ignored_heavy_data", "parser_drift", "eol_hash_drift", "manifest_self_hash", "raw_blob_risk", "accidental_denominator_admission"}:
        if risk not in risks:
            failures.append(f"saturation ledger missing {risk}")
    if saturation.get("same_evidence_class_gaps_remaining") != []:
        failures.append("saturation ledger reports unresolved same-evidence-class gaps")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    if manifest.get("raw_market_blob_artifact_count") != 0:
        failures.append("output manifest contains raw market blob artifact")
    for row in manifest.get("artifacts", []):
        path = ROOT / row["path"]
        if path.exists() and row.get("sha256") != sha256_file(path):
            failures.append(f"output manifest hash mismatch: {row['path']}")

    next_prompt = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
    next_starter = ROUTE_DIR / "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_STARTER_2026-05-13.txt"
    if not next_prompt.exists() or not next_starter.exists():
        failures.append("next G12 prompt or starter missing")
    else:
        starter = next_starter.read_text(encoding="utf-8").strip()
        if not starter.startswith("/goal Follow the full controlling prompt"):
            failures.append("next starter does not bind controlling prompt")
        if "\n" in starter:
            failures.append("next starter is not one physical line")

    py_files = [
        ROUTE_DIR / "build_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
        ROUTE_DIR / "verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
        ROUTE_DIR / "test_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
    ]
    syntax = syntax_parse(py_files)
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    scoped_status = git_status_rows()
    scoped_raw = [row for row in scoped_status if row["scoped"] and row["raw_market_blob"]]
    scoped_live = [row for row in scoped_status if row["scoped"] and row["forbidden_live_surface"]]
    if scoped_raw:
        failures.append(f"raw market blob in scoped status: {scoped_raw}")
    if scoped_live:
        failures.append(f"forbidden live surface in scoped status: {scoped_live}")

    result = {
        "schema_version": "g0exp_r1_verification_result_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": not failures,
        "failures": failures,
        "artifact_count_verified": len(REQUIRED_STEMS),
        "assigned_family_count_verified": len(assigned),
        "present_root_count_verified": root.get("present_root_count"),
        "parser_file_count_verified": parser.get("parser_file_count"),
        "schema_shape_file_count_verified": parser.get("schema_shape_file_count"),
        "adjacent_overflow_count_verified": len(decision.get("adjacent_overflow_decisions", [])),
        "accepted_40_count_verified": denom.get("accepted_40_count_recomputed_from_upstream"),
        "r1_new_denominator_rows_added": denom.get("r1_new_denominator_rows_added"),
        "syntax_parse": syntax,
        "scoped_status_has_raw_market_blob": bool(scoped_raw),
        "scoped_status_has_forbidden_live_surface": bool(scoped_live),
        "can_mark_goal_complete": not failures,
        "focused_tests_marked_ok": bool(mark_focused_tests_ok),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    if write_result:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        write_md(artifact_path("VERIFICATION_RESULT", ".md"), "G0EXP R1 Verification Result", result)
        refresh_completion(result, mark_focused_tests_ok)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok, write_result=True)
    print(json.dumps({"ok": result["ok"], "failure_count": len(result["failures"]), "failures": result["failures"]}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
