"""Verifier for the G12 SCID anti-boxing route intake audit."""

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
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_cross_domain_anti_boxing_route_intake"
)
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_ANTI_BOXING"
TARGET_PREFIX = "SCID_ANTI_BOXING"
EVIDENCE_CLASS = "G12_SCID_ANTI_BOXING_ROUTE_INTAKE_AUDIT_ONLY"
TARGET_EVIDENCE_CLASS = "SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_ANTI_BOXING_ROUTE_INTAKE_CONTROL_EVIDENCE_ONLY"

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

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "DECISION_LEDGER",
    "ROUTE_FAMILY_RECOMPUTATION_AUDIT",
    "DOMAIN_COVERAGE_AUDIT",
    "PROMPT_PACK_AUDIT",
    "SOURCE_CONTRACT_AUDIT",
    "ANTI_BOXING_NOVELTY_AUDIT",
    "NEGATIVE_EVIDENCE_TREATMENT_AUDIT",
    "NO_LEAK_FORBIDDEN_SURFACE_AUDIT",
    "BLOCKER_FOLLOWUP_LEDGER",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = ["SATURATION_SELF_RED_TEAM"]
REQUIRED_PY = [
    "build_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py",
    "verify_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py",
    "test_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py",
]
TARGET_REQUIRED_STEMS = [
    "ROUTE_FAMILY_INVENTORY",
    "DOMAIN_COVERAGE_AND_GAP_LEDGER",
    "PROMPT_PACK_MANIFEST",
    "SOURCE_CONTRACT_TEMPLATES",
    "NEGATIVE_EVIDENCE_LEDGER",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
]

REQUIRED_SOURCE_CONTRACT_FIELDS = [
    "template_id",
    "source_family",
    "required_fields",
    "searched_root_expectations",
    "as_of_rule",
    "hash_deferral_policy",
    "no_leak_rules",
    "duplicate_policy",
    "forbidden_fields",
    "fail_closed_statuses",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def target_path(stem: str, suffix: str = ".json") -> Path:
    return TARGET_DIR / f"{TARGET_PREFIX}_{stem}_{DATE_TAG}{suffix}"


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


def safe_flags_failures(name: str, payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"{name}: promotion_verdict mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{name}: evidence_class mismatch: {payload.get('evidence_class')}")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{name}: {flag} is not false")
    return failures


def target_safe_flags_failures(name: str, payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"target {name}: promotion_verdict mismatch")
    if payload.get("evidence_class") != TARGET_EVIDENCE_CLASS:
        failures.append(f"target {name}: evidence_class mismatch: {payload.get('evidence_class')}")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"target {name}: {flag} is not false")
    return failures


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_route_intake_audit/",
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/",
        "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
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
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
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


def refresh_completion_and_manifest(result: dict[str, Any], mark_target_tests_ok: bool, mark_focused_tests_ok: bool) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        completion["target_verifier_ok"] = result["target_verifier_ok"]
        completion["target_focused_tests_ok"] = bool(mark_target_tests_ok)
        completion["g12_focused_tests_ok"] = bool(mark_focused_tests_ok)
        completion["all_checklist_items_satisfied"] = all(
            row.get("satisfied") for row in completion.get("prompt_to_artifact_checklist", [])
        )
        completion["can_mark_goal_complete_after_verifier_tests_and_commit"] = (
            completion["all_checklist_items_satisfied"]
            and result["ok"]
            and result["target_verifier_ok"]
            and bool(mark_target_tests_ok)
            and bool(mark_focused_tests_ok)
        )
        write_json(completion_path, completion)

    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for row in manifest.get("files", []):
            path = ROOT / row["path"]
            row["exists"] = path.exists()
            row["sha256"] = sha256_file(path)
        write_json(manifest_path, manifest)


def verify(mark_target_tests_ok: bool = False, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, Any] = {}
    target_payloads: dict[str, Any] = {}

    for stem in REQUIRED_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing required G12 artifact: {rel(path)}")
            continue
        try:
            payloads[stem] = read_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"invalid json {rel(path)}: {exc}")

    for stem in REQUIRED_MD_STEMS:
        path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append(f"missing required G12 artifact: {rel(path)}")

    py_paths = [ROUTE_DIR / name for name in REQUIRED_PY]
    for path in py_paths:
        if not path.exists():
            failures.append(f"missing required G12 script/test: {rel(path)}")

    for stem in TARGET_REQUIRED_STEMS:
        path = target_path(stem)
        if not path.exists():
            failures.append(f"missing required target artifact: {rel(path)}")
            continue
        try:
            target_payloads[stem] = read_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"invalid target json {rel(path)}: {exc}")

    for stem, payload in payloads.items():
        failures.extend(safe_flags_failures(stem, payload))
    for stem, payload in target_payloads.items():
        failures.extend(target_safe_flags_failures(stem, payload))

    route = payloads.get("ROUTE_FAMILY_RECOMPUTATION_AUDIT", {})
    if route.get("route_family_count") != 40 or route.get("route_family_count_exactly_40") is not True:
        failures.append("G12 did not verify exactly 40 route families")
    if route.get("domain_count") != 10 or route.get("all_required_domains_covered") is not True:
        failures.append("G12 did not verify 10 required domains")
    if route.get("exact_four_families_per_domain") is not True:
        failures.append("G12 did not verify four families per domain")
    if route.get("failures"):
        failures.append(f"route recomputation failures: {route.get('failures')}")

    domain = payloads.get("DOMAIN_COVERAGE_AUDIT", {})
    if domain.get("all_required_domains_have_route_family") is not True:
        failures.append("domain audit did not cover all route family domains")
    if domain.get("all_required_domains_have_prompt_pack") is not True:
        failures.append("domain audit did not cover all prompt pack domains")

    prompt = payloads.get("PROMPT_PACK_AUDIT", {})
    if prompt.get("prompt_pack_count") != 12 or prompt.get("prompt_pack_count_exactly_12") is not True:
        failures.append("prompt pack audit did not verify exactly 12 packs")
    if prompt.get("all_starters_one_physical_line") is not True:
        failures.append("not all starters are one physical line")
    if prompt.get("all_starters_bind_controlling_prompt") is not True:
        failures.append("not all starters bind controlling prompt")
    if prompt.get("failures"):
        failures.append(f"prompt pack audit failures: {prompt.get('failures')}")

    source = payloads.get("SOURCE_CONTRACT_AUDIT", {})
    if source.get("template_count") != 10 or source.get("template_count_exactly_10") is not True:
        failures.append("source contract audit did not verify exactly 10 templates")
    if source.get("failures"):
        failures.append(f"source contract failures: {source.get('failures')}")
    repair = source.get("same_evidence_class_repair_applied", {})
    if repair.get("status") != "APPLIED_BEFORE_G12_CLOSEOUT":
        failures.append("same-evidence-class source-contract repair not recorded")

    novelty = payloads.get("ANTI_BOXING_NOVELTY_AUDIT", {})
    if novelty.get("all_40_have_non_ob_rationale") is not True:
        failures.append("not all 40 route families have non-OB rationale")

    negative = payloads.get("NEGATIVE_EVIDENCE_TREATMENT_AUDIT", {})
    if negative.get("all_negative_rows_preserve_learning") is not True:
        failures.append("negative evidence does not preserve learning for every row")
    if negative.get("has_boxed_route_rejection") is not True:
        failures.append("negative evidence lacks boxed-route rejection")

    no_leak = payloads.get("NO_LEAK_FORBIDDEN_SURFACE_AUDIT", {})
    if no_leak.get("forbidden_surfaces_closed") is not True:
        failures.append("forbidden surfaces are not closed")

    blocker = payloads.get("BLOCKER_FOLLOWUP_LEDGER", {})
    if blocker.get("can_accept_after_repairs") is not True:
        failures.append("blocker ledger does not allow acceptance after repairs")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append(f"unexpected terminal decision: {decision.get('terminal_decision')}")
    if decision.get("child_routes_launched") is not False:
        failures.append("decision ledger says child routes were launched")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("all_checklist_items_satisfied") is not True:
        failures.append("completion audit checklist is not fully satisfied")

    target_verification = target_payloads.get("VERIFICATION_RESULT", {})
    target_verifier_ok = target_verification.get("ok") is True
    if not target_verifier_ok:
        failures.append("target verifier result is not ok=true")

    g0_prompt = ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md"
    g0_starter = ROUTE_DIR / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_STARTER_2026-05-12.txt"
    if not g0_prompt.exists():
        failures.append(f"missing G0 sequencing prompt: {rel(g0_prompt)}")
    if not g0_starter.exists():
        failures.append(f"missing G0 sequencing starter: {rel(g0_starter)}")
    elif "\n" in g0_starter.read_text(encoding="utf-8").strip():
        failures.append("G0 sequencing starter is not one physical line")

    saturation_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if saturation_path.exists():
        saturation = saturation_path.read_text(encoding="utf-8")
        for phrase in [
            "shallow prompt factory",
            "OB-only logic",
            "Same-Evidence-Class Repair",
            "No outcome/result",
            "broker account/order/history/deal/position",
        ]:
            if phrase not in saturation:
                failures.append(f"saturation self-red-team missing phrase: {phrase}")

    syntax = syntax_parse([path for path in py_paths if path.exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped changes include forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped changes include raw market blob")

    result = {
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "ok": not failures,
        "failures": failures,
        "target_verifier_ok": target_verifier_ok,
        "target_focused_tests_ok": bool(mark_target_tests_ok),
        "g12_focused_tests_ok": bool(mark_focused_tests_ok),
        "can_mark_goal_complete": not failures and target_verifier_ok and bool(mark_target_tests_ok) and bool(mark_focused_tests_ok),
        "terminal_decision": decision.get("terminal_decision"),
        "route_family_count_verified": route.get("route_family_count"),
        "required_domain_count_verified": route.get("domain_count"),
        "prompt_pack_count_verified": prompt.get("prompt_pack_count"),
        "source_contract_template_count_verified": source.get("template_count"),
        "negative_evidence_count_verified": negative.get("negative_evidence_count"),
        "same_evidence_class_repair_status": repair.get("status"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion_and_manifest(result, mark_target_tests_ok, mark_focused_tests_ok)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-target-tests-ok", action="store_true")
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(
        mark_target_tests_ok=args.mark_target_tests_ok,
        mark_focused_tests_ok=args.mark_focused_tests_ok,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
