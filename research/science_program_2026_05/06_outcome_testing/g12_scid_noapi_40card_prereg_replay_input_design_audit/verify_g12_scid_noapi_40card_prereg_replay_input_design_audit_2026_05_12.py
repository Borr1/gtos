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
PREFIX = "G12_SCID_NOAPI_PREREG_AUDIT"
ROUTE_ID = "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY"
TERMINAL_ACCEPT_WITH_FOLLOWUPS = "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN_CONTROL_EVIDENCE_ONLY"

REQUIRED_STEMS = [
    "CONTEXT_AND_TARGET_INPUT_INVENTORY",
    "CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER",
    "REPLAY_INPUT_PACKET_AUDIT_LEDGER",
    "BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT",
    "EXPANSION_CANDIDATE_QUARANTINE_AUDIT",
    "SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT",
    "NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT",
    "HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT",
    "SATURATION_FAIRNESS_LEDGER",
    "DECISION_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
    "verify_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
    "test_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
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
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")


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


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool = False) -> None:
    completion_path = artifact_path("COMPLETION_AUDIT")
    if not completion_path.exists():
        return
    completion = read_json(completion_path)
    for item in completion.get("prompt_to_artifact_checklist", []):
        if item.get("requirement") == "G12 standalone verifier passed":
            item["satisfied"] = result["ok"]
            item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
        if mark_focused_tests_ok and item.get("requirement") == "G12 focused tests passed":
            item["satisfied"] = True
            item["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    completion["standalone_verifier_ok"] = result["ok"]
    if mark_focused_tests_ok:
        completion["focused_tests_ok"] = True
    non_commit_items = [
        item for item in completion.get("prompt_to_artifact_checklist", []) if item.get("requirement") != "scoped commits complete"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(item.get("satisfied") is True for item in non_commit_items)
    completion["completion_standard_satisfied"] = all(item.get("satisfied") is True for item in completion.get("prompt_to_artifact_checklist", []))
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(completion_path, completion)


def refresh_output_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = artifact_path("OUTPUT_MANIFEST", ".md")
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    excluded = {manifest_path.resolve(), manifest_md_path.resolve()}
    artifact_paths = []
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.resolve() not in excluded and (
            path.suffix.lower() in {".json", ".md", ".py", ".txt"} or path.name == ".gitignore"
        ):
            artifact_paths.append(path)
    g0_prompt = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    if g0_prompt.exists():
        artifact_paths.append(g0_prompt)
    artifacts = []
    for path in sorted(set(artifact_paths)):
        artifacts.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "raw_market_blob": path.name.lower().endswith(RAW_SUFFIXES),
            }
        )
    manifest["artifact_count"] = len(artifacts)
    manifest["artifacts"] = artifacts
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    manifest["manifest_self_hash_policy"] = "Output manifest JSON/MD are excluded from their own blocking hash list; verifier recomputes current artifact hashes."
    write_json(manifest_path, manifest)
    manifest_md_path.write_text(
        "# Output Manifest\n\n```json\n" + json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n```\n",
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
    if context.get("all_required_inputs_read") is not True:
        failures.append("context: not all required target/upstream inputs were read")
    if context.get("parse_failures"):
        failures.append("context: parse/read failures present")

    recompute = payloads.get("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER", {})
    if recompute.get("accepted_card_count_recomputed") != 40:
        failures.append("card/domain: accepted card count != 40")
    if recompute.get("domain_count_recomputed") != 8:
        failures.append("card/domain: domain count != 8")
    if any(value != 5 for value in recompute.get("domain_counts_recomputed", {}).values()):
        failures.append("card/domain: one or more domains do not have exactly five cards")
    if recompute.get("readiness_split_recomputed") != {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }:
        failures.append("card/domain: readiness split mismatch")
    if recompute.get("outside_current_gtos_ob_framing_count_recomputed") != 33:
        failures.append("card/domain: outside-current-GTOS/OB count != 33")
    if recompute.get("ok") is not True:
        failures.append("card/domain: recomputation ledger failed")

    replay = payloads.get("REPLAY_INPUT_PACKET_AUDIT_LEDGER", {})
    if replay.get("replay_packet_count") != 8 or replay.get("packets_only_for_preregisterable_now_cards") is not True or replay.get("ok") is not True:
        failures.append("replay packet audit failed")

    blocked = payloads.get("BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT", {})
    if blocked.get("blocked_card_count") != 32 or blocked.get("blocked_rows_only_for_blocked_cards") is not True or blocked.get("ok") is not True:
        failures.append("blocked dependency exactness audit failed")

    expansion = payloads.get("EXPANSION_CANDIDATE_QUARANTINE_AUDIT", {})
    if expansion.get("expansion_candidate_count") != 8 or expansion.get("expansion_candidates_entered_accepted_denominator") is not False or expansion.get("ok") is not True:
        failures.append("expansion quarantine audit failed")

    pursuit = payloads.get("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT", {})
    if pursuit.get("pursued_group_count") != 10 or pursuit.get("resolved_inside_this_prompt_count") != 8 or pursuit.get("remaining_exact_dependency_blocker_count") != 2 or pursuit.get("ok") is not True:
        failures.append("same-evidence-class blocker pursuit audit failed")

    noleak = payloads.get("NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT", {})
    if noleak.get("suspicious_forbidden_reference_count") != 0 or noleak.get("ok") is not True:
        failures.append("no-leak/forbidden-surface audit failed")

    hash_audit = payloads.get("HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT", {})
    if hash_audit.get("blocking_hash_mismatches") or hash_audit.get("missing_manifest_artifacts"):
        failures.append("hash audit has blocking mismatches or missing artifacts")
    if len(hash_audit.get("nonblocking_manifest_self_hash_mismatches", [])) != 1:
        failures.append("hash audit should record exactly one nonblocking target manifest self-hash mismatch")
    if hash_audit.get("target_verifier_and_tests_passed") is not True or hash_audit.get("ok") is not True:
        failures.append("target verifier/tests did not pass")

    fairness = payloads.get("SATURATION_FAIRNESS_LEDGER", {})
    if fairness.get("did_not_reject_novelty_or_outside_current_edge") is not True:
        failures.append("fairness audit rejected novelty/outside-current edge")
    if fairness.get("did_not_accept_silent_denominator_expansion") is not True or fairness.get("ok") is not True:
        failures.append("fairness audit failed denominator-expansion guard")

    decision = payloads.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") not in {TERMINAL_ACCEPT, TERMINAL_ACCEPT_WITH_FOLLOWUPS}:
        failures.append(f"decision: unexpected terminal decision {decision.get('terminal_decision')}")
    if decision.get("terminal_blockers"):
        failures.append("decision: terminal blockers present")
    if decision.get("accepted_validation_execution") is not False or decision.get("accepted_strategy_performance") is not False:
        failures.append("decision: forbidden accepted validation/performance flag")

    prompt_path = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
    starter_path = ROUTE_DIR / "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_STARTER_2026-05-12.txt"
    if not prompt_path.exists() or not starter_path.exists():
        failures.append("next G0 prompt/starter missing")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    if manifest.get("all_required_artifact_families_covered") is not True:
        failures.append("output manifest missing required artifact families")
    if any(row.get("raw_market_blob") for row in manifest.get("artifacts", [])):
        failures.append("output manifest includes raw market blob")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])
    status = git_status_entries()
    if status["no_scoped_forbidden_live_surface"] is not True or status["no_scoped_raw_market_blob"] is not True:
        failures.append("git status: scoped forbidden live surface or raw market blob")

    result = {
        "ok": not failures,
        "failures": failures,
        "failure_count": len(failures),
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": decision.get("terminal_decision"),
        "card_count_verified": recompute.get("accepted_card_count_recomputed"),
        "domain_count_verified": recompute.get("domain_count_recomputed"),
        "readiness_split_verified": recompute.get("readiness_split_recomputed"),
        "outside_current_gtos_ob_framing_count_verified": recompute.get("outside_current_gtos_ob_framing_count_recomputed"),
        "replay_packet_count_verified": replay.get("replay_packet_count"),
        "blocked_dependency_count_verified": blocked.get("blocked_card_count"),
        "expansion_candidate_count_verified": expansion.get("expansion_candidate_count"),
        "nonblocking_manifest_self_hash_mismatch_count": len(hash_audit.get("nonblocking_manifest_self_hash_mismatches", [])),
        "target_verifier_and_tests_passed": hash_audit.get("target_verifier_and_tests_passed"),
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
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion(result, mark_focused_tests_ok=mark_focused_tests_ok)
    refresh_output_manifest(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    verification = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
