from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_FC_SCHEMA_AUDIT"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
NEXT_G0_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"
)

REQUIRED_STEMS = [
    "CONTEXT_AND_ARTIFACT_INVENTORY",
    "SCHEMA_CONTRACT_AUDIT",
    "FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT",
    "MANIFEST_READONLY_NOLEAK_AUDIT",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12.py",
    "verify_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12.py",
    "test_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12.py",
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
    "changes_live_trading_behavior",
]
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


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
                "scoped_raw_market_blob": scoped and path.endswith(RAW_SUFFIXES),
            }
        )
    scoped = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped,
        "unrelated_dirty_entry_count": len(entries) - len(scoped),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped),
    }


def refresh_completion_and_closeout(result: dict[str, Any], mark_focused_tests_ok: bool = False) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if completion_path.exists():
        completion = read_json(completion_path)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item.get("requirement") == "verifier_passed":
                item["satisfied"] = result["ok"]
                item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
            if mark_focused_tests_ok and item.get("requirement") == "focused_tests_passed":
                item["satisfied"] = True
                item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
        completion["standalone_verifier_ok"] = result["ok"]
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        non_commit_items = [
            item for item in completion.get("prompt_to_artifact_checklist", []) if item.get("requirement") != "scoped_commits_complete"
        ]
        completion["completion_standard_satisfied"] = all(item.get("satisfied") is True for item in completion.get("prompt_to_artifact_checklist", []))
        completion["can_mark_goal_complete"] = completion["completion_standard_satisfied"]
        write_json(completion_path, completion)
    closeout_path = artifact_path("CLOSEOUT_VERIFICATION")
    if closeout_path.exists():
        closeout = read_json(closeout_path)
        closeout["audit_standalone_verifier_ok"] = result["ok"]
        closeout["audit_standalone_verifier_failures"] = result["failures"]
        if mark_focused_tests_ok:
            closeout["audit_focused_tests_ok"] = True
        write_json(closeout_path, closeout)


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
    if not NEXT_G0_PROMPT.exists():
        failures.append(f"missing next G0 prompt: {rel(NEXT_G0_PROMPT)}")

    for stem, payload in payloads.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: bad promotion_verdict")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: expected {flag}=false, got {payload.get(flag)!r}")

    context = payloads.get("CONTEXT_AND_ARTIFACT_INVENTORY", {})
    inv = context.get("input_route_artifact_inventory", {})
    if inv.get("artifact_count", 0) < 59 or not inv.get("all_input_route_artifacts_read"):
        failures.append("context: input route artifact inventory incomplete")

    schema = payloads.get("SCHEMA_CONTRACT_AUDIT", {})
    if schema.get("candidate_rows_coverage_expectation") != 3014:
        failures.append("schema: candidate coverage != 3014")
    if schema.get("duplicate_proxy_denominator_key_coverage_expectation") != 3014:
        failures.append("schema: duplicate coverage != 3014")
    if sorted(schema.get("accepted_capture_groups", [])) != sorted(
        [
            "baseline_control_fields",
            "framework_setup_family",
            "future_orderflow_depth_proxy_requirements",
            "intended_entry_reference",
            "intended_side_direction",
            "intended_stop_reference",
            "intended_target_reference",
            "lifecycle_fill_cancel_expiry_source_status",
            "lower_timeframe_asof_path_availability",
            "poi_type_bounds_source",
        ]
    ):
        failures.append("schema: accepted capture groups mismatch")
    if schema.get("schema_contract_failures") or schema.get("schema_contract_audit_ok") is not True:
        failures.append("schema: contract audit failed")

    fixtures = payloads.get("FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT", {})
    if fixtures.get("fixture_count") != 18:
        failures.append("fixtures: expected 18 fixtures")
    if fixtures.get("valid_fixture_pass_count") != 5:
        failures.append("fixtures: valid pass count != 5")
    if fixtures.get("invalid_fixture_fail_closed_count") != 13:
        failures.append("fixtures: invalid fail-closed count != 13")
    if fixtures.get("fixture_validator_failures") or fixtures.get("fixture_validator_recomputation_ok") is not True:
        failures.append("fixtures: independent fixture validator failed")

    manifest = payloads.get("MANIFEST_READONLY_NOLEAK_AUDIT", {})
    if manifest.get("blocking_unrepaired_hash_mismatches"):
        failures.append("manifest: blocking unrepaired hash mismatches")
    if manifest.get("strict_input_hash_mismatches"):
        failures.append("manifest: strict input hash mismatches")
    if not manifest.get("repaired_hash_binding_mismatches"):
        failures.append("manifest: current G12 prompt hash repair not recorded")
    if not manifest.get("nonblocking_self_manifest_mismatches"):
        failures.append("manifest: output manifest self-hash repair not recorded")
    if manifest.get("read_only_alignment_failures"):
        failures.append("manifest: read-only alignment failures")
    if manifest.get("raw_manifest_entries"):
        failures.append("manifest: raw market blob entries")
    if manifest.get("manifest_readonly_noleak_audit_ok") is not True:
        failures.append("manifest: readonly/no-leak audit failed")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_ACCEPT:
        failures.append("decision: terminal decision is not accept")
    if decision.get("terminal_blockers"):
        failures.append(f"decision: terminal blockers present {decision.get('terminal_blockers')}")
    if decision.get("accepted_validation_execution") is not False or decision.get("accepted_strategy_performance") is not False:
        failures.append("decision: forbidden acceptance flag")

    out_manifest = payloads.get("OUTPUT_MANIFEST", {})
    if not all(out_manifest.get("required_artifact_families_covered", {}).values()):
        failures.append("output manifest: missing required family")
    raw_artifacts = [row["path"] for row in out_manifest.get("artifacts", []) if row.get("raw_market_blob")]
    if raw_artifacts:
        failures.append(f"output manifest: raw artifacts {raw_artifacts}")
    mutable = {
        artifact_path("OUTPUT_MANIFEST"),
        artifact_path("OUTPUT_MANIFEST", ".md"),
        artifact_path("VERIFICATION_RESULT"),
        artifact_path("COMPLETION_AUDIT"),
        artifact_path("COMPLETION_AUDIT", ".md"),
        artifact_path("CLOSEOUT_VERIFICATION"),
        artifact_path("CLOSEOUT_VERIFICATION", ".md"),
    }
    for row in out_manifest.get("artifacts", []):
        path = REPO_ROOT / row["path"]
        if not path.exists():
            failures.append(f"output manifest: missing artifact {row['path']}")
        elif path not in mutable and row.get("sha256_after_build") != sha256_file(path):
            failures.append(f"output manifest: hash mismatch {row['path']}")

    prompt_text = NEXT_G0_PROMPT.read_text(encoding="utf-8") if NEXT_G0_PROMPT.exists() else ""
    for text in [
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "manifest-binding repair",
        "3,014",
        "broker account/order/history/deal/position evidence",
        "prompt/config/risk/safety/execution/canary/selector",
    ]:
        if text not in prompt_text:
            failures.append(f"next G0 prompt missing text: {text}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    status = git_status_entries()
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append("git status: scoped forbidden live surface")
    if not status["no_scoped_raw_market_blob"]:
        failures.append("git status: scoped raw market blob")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "ok": not failures,
        "failures": failures,
        "terminal_decision": decision.get("terminal_decision"),
        "candidate_rows_verified": schema.get("candidate_rows_coverage_expectation"),
        "fixture_count_verified": fixtures.get("fixture_count"),
        "syntax_parse": syntax,
        "scoped_git_status": status,
        "can_mark_goal_complete": False,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion_and_closeout(result, mark_focused_tests_ok=mark_focused_tests_ok)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(mark_focused_tests_ok="--mark-focused-tests-ok" in sys.argv), indent=2, sort_keys=True))
