"""Verifier for the ADV-002 duplicate-key collision route package."""

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
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-13"
PREFIX = "SCID_ANTI_BOXING_R11_ADV_002"
ROUTE_ID = "ADV-002"
EVIDENCE_CLASS = "ADV-002_SOURCE_CONTROL_DESIGN_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

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
REQUIRED_JSON_STEMS = [
    "CONTEXT_ANCHOR",
    "SOURCE_CONTRACT_LEDGER",
    "ROUTE_DECISION_LEDGER",
    "DUPLICATE_DENOMINATOR_POLICY",
    "ASOF_NOLEAK_DUPLICATE_POLICY",
    "SEARCHED_ROOT_LEDGER",
    "NEGATIVE_EVIDENCE_BLOCKER_LEDGER",
    "SATURATION_SELF_RED_TEAM",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = ["SATURATION_SELF_RED_TEAM"]
REQUIRED_PY = [
    "build_scid_anti_boxing_r11_adv_002_2026_05_13.py",
    "verify_scid_anti_boxing_r11_adv_002_2026_05_13.py",
    "test_scid_anti_boxing_r11_adv_002_2026_05_13.py",
]
REQUIRED_SOURCE_REQUIREMENTS = {
    "candidate id",
    "duplicate key",
    "source hash",
    "group membership version",
    "collision policy",
}
REQUIRED_MECHANISMS = {
    "denominator_drift",
    "group_membership_instability",
    "canonical_row_ambiguity",
    "cross_card_duplication",
    "session_symbol_timeframe_collision",
    "row_hash_eol_friction",
}
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py")
RAW_BLOB_SUFFIXES = (".parquet", ".scid", ".depth", ".zip", ".gz", ".bin")


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def safe_flags_ok(name: str, payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"{name}: promotion_verdict mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{name}: evidence_class mismatch {payload.get('evidence_class')!r}")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{name}: {flag} is not false")
    return failures


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_ANTI_BOXING_R11_ADV_002_",
        "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_R11_ADV_002_",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
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
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and path.endswith(RAW_BLOB_SUFFIXES),
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


def validate_prompts() -> list[str]:
    failures = []
    prompt_files = [
        PROMPT_DIR / f"G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_{DATE_TAG}.md",
        PROMPT_DIR / f"G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS_GOAL_PROMPT_{DATE_TAG}.md",
    ]
    starter_files = [
        ROUTE_DIR / f"G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_STARTER_{DATE_TAG}.txt",
        ROUTE_DIR / f"G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS_STARTER_{DATE_TAG}.txt",
    ]
    for path in prompt_files:
        if not path.exists():
            failures.append(f"missing future prompt: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "duplicate-key collision",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "No validation/results/R/PnL/win-rate/expectancy/performance",
            "Completion standard",
        ]:
            if phrase not in text:
                failures.append(f"{rel(path)} missing phrase {phrase!r}")
    for path in starter_files:
        if not path.exists():
            failures.append(f"missing starter: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8").strip()
        if "\n" in text:
            failures.append(f"starter is not one physical line: {rel(path)}")
        if not text.startswith("/goal Follow the full controlling prompt"):
            failures.append(f"starter does not bind controlling prompt: {rel(path)}")
    return failures


def refresh_completion_and_manifest(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "verifier and focused tests exist":
                    row["satisfied"] = result["ok"]
        completion["all_checklist_items_satisfied"] = all(
            row.get("satisfied") for row in completion.get("prompt_to_artifact_checklist", [])
        )
        completion["can_mark_goal_complete"] = result["ok"] and completion["all_checklist_items_satisfied"]
        write_json(completion_path, completion)

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for row in manifest.get("files", []):
            path = ROOT / row["path"]
            row["exists"] = path.exists()
            if path.resolve() == manifest_path.resolve():
                row["sha256"] = None
                row["self_hash_policy"] = "self-referential manifest hash omitted; use external git/blob hash for the manifest itself"
            else:
                row["sha256"] = sha256_file(path)
        write_json(manifest_path, manifest)


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    required_json_paths = [artifact_path(stem) for stem in REQUIRED_JSON_STEMS]
    required_md_paths = [artifact_path(stem, ".md") for stem in REQUIRED_MD_STEMS]
    required_py_paths = [ROUTE_DIR / filename for filename in REQUIRED_PY]

    for path in required_json_paths + required_md_paths + required_py_paths:
        if not path.exists():
            failures.append(f"missing required file: {rel(path)}")

    payloads: dict[str, Any] = {}
    for stem, path in zip(REQUIRED_JSON_STEMS, required_json_paths):
        if path.exists():
            try:
                payloads[stem] = read_json(path)
            except json.JSONDecodeError as exc:
                failures.append(f"invalid json {rel(path)}: {exc}")

    for name, payload in payloads.items():
        failures.extend(safe_flags_ok(name, payload))

    context = payloads.get("CONTEXT_ANCHOR", {})
    if context.get("route_family_id") != ROUTE_ID:
        failures.append("context anchor route id mismatch")
    if len(context.get("active_question_stack", [])) < 6:
        failures.append("context anchor active question stack too short")

    contracts = payloads.get("SOURCE_CONTRACT_LEDGER", {})
    contract_requirements = {row.get("requirement") for row in contracts.get("contracts", [])}
    if not REQUIRED_SOURCE_REQUIREMENTS.issubset(contract_requirements):
        failures.append(f"source contracts missing {sorted(REQUIRED_SOURCE_REQUIREMENTS - contract_requirements)}")
    if contracts.get("all_required_source_requirements_covered") is not True:
        failures.append("source contracts do not mark all requirements covered")
    for row in contracts.get("contracts", []):
        if not row.get("accepted_field_names") or not row.get("minimum_contract"):
            failures.append(f"source contract incomplete: {row.get('requirement')}")

    decision = payloads.get("ROUTE_DECISION_LEDGER", {})
    mechanisms = {row.get("mechanism") for row in decision.get("decisions", [])}
    if not REQUIRED_MECHANISMS.issubset(mechanisms):
        failures.append(f"route decisions missing {sorted(REQUIRED_MECHANISMS - mechanisms)}")
    if decision.get("mechanism_requirements_all_covered") is not True:
        failures.append("route decisions do not mark mechanisms covered")

    duplicate = payloads.get("DUPLICATE_DENOMINATOR_POLICY", {})
    collision_classes = {row.get("class") for row in duplicate.get("collision_classes", [])}
    for expected in [
        "exact_row_duplicate",
        "projection_duplicate",
        "cross_card_duplicate",
        "proxy_or_contract_duplicate",
        "session_symbol_timeframe_collision",
        "hash_eol_equivalent_text_duplicate",
    ]:
        if expected not in collision_classes:
            failures.append(f"duplicate policy missing class {expected}")
    if "outcomes" in duplicate.get("canonical_row_hierarchy", [""])[-1]:
        pass
    else:
        failures.append("duplicate policy canonical hierarchy does not prohibit outcome-derived canonical choice")

    asof = payloads.get("ASOF_NOLEAK_DUPLICATE_POLICY", {})
    for field in ["candidate_input_row_id", "duplicate_proxy_denominator_key", "source_hash", "group_membership_version", "collision_policy"]:
        if field not in asof.get("field_allowlist", []):
            failures.append(f"as-of allowlist missing {field}")
    for token in ["pnl", "r_multiple", "win_loss", "broker_account_history"]:
        if token not in asof.get("field_denylist", []):
            failures.append(f"denylist missing {token}")

    searched = payloads.get("SEARCHED_ROOT_LEDGER", {})
    if len(searched.get("root_rows", [])) < 6:
        failures.append("searched root ledger has too few roots")
    aggregate_hits = searched.get("aggregate_term_hits", {})
    for key in ["candidate_id", "duplicate_key", "source_hash", "group_membership_version", "collision_policy", "eol_hash_policy"]:
        if aggregate_hits.get(key, 0) <= 0:
            failures.append(f"searched root ledger lacks hits for {key}")
    if not searched.get("forbidden_or_out_of_class_roots"):
        failures.append("searched root ledger lacks forbidden/out-of-class root accounting")

    blockers = payloads.get("NEGATIVE_EVIDENCE_BLOCKER_LEDGER", {})
    if blockers.get("blocker_count", 0) < 6:
        failures.append("blocker ledger too short")
    if blockers.get("no_vague_future_work") is not True:
        failures.append("blocker ledger allows vague future work")
    for row in blockers.get("blockers", []):
        if not row.get("next_requirement"):
            failures.append(f"blocker missing exact next requirement: {row.get('blocker_id')}")

    saturation = payloads.get("SATURATION_SELF_RED_TEAM", {})
    if saturation.get("saturation_verdict") != "PASS_SOURCE_CONTROL_DESIGN_SATURATED_NO_RESULT_OPENING":
        failures.append("saturation verdict mismatch")
    if len(saturation.get("questions", [])) < 6:
        failures.append("saturation questions too short")
    saturation_md = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if saturation_md.exists():
        text = saturation_md.read_text(encoding="utf-8")
        for phrase in ["No outcome/result labels", "broker account/order/history/deal/position", "NO_PROMOTION_VERDICT"]:
            if phrase not in text:
                failures.append(f"saturation md missing {phrase!r}")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("instruction_coverage", {}).get("goal_session_research_discipline_read") is not True:
        failures.append("completion audit missing goal-session discipline coverage")
    checklist = completion.get("prompt_to_artifact_checklist", [])
    has_focused_row = any(row.get("requirement") == "verifier and focused tests exist" for row in checklist)
    if not has_focused_row:
        failures.append("completion audit missing focused-test checklist row")
    if not mark_focused_tests_ok and completion.get("all_checklist_items_satisfied") is True:
        # The verifier must be idempotent after closeout. A completed audit is valid
        # on rerun when the focused-test row is present and the previous marker is set.
        if completion.get("focused_tests_ok") is not True:
            failures.append("completion audit closed without focused-test marker")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    if manifest.get("file_count") != len(manifest.get("files", [])):
        failures.append("manifest file_count mismatch")
    for row in manifest.get("files", []):
        path = ROOT / row.get("path", "")
        if not path.exists():
            failures.append(f"manifest file missing: {row.get('path')}")

    failures.extend(validate_prompts())
    syntax = syntax_parse([path for path in required_py_paths if path.exists()])
    failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped changes include forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped changes include raw market blob")

    focused_complete = bool(mark_focused_tests_ok or completion.get("focused_tests_ok") is True)
    result = {
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "route_family_id": ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "can_mark_goal_complete": not failures and focused_complete,
        "source_requirement_count_verified": len(contract_requirements),
        "mechanism_count_verified": len(mechanisms),
        "searched_root_count_verified": len(searched.get("root_rows", [])),
        "blocker_count_verified": blockers.get("blocker_count"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion_and_manifest(result, mark_focused_tests_ok=mark_focused_tests_ok)
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
