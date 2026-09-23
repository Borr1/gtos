"""Verifier for the G0 SCID no-API preregistration synthesis package."""

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

DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_NOAPI_PREREG_SYNTHESIS"
ROUTE_ID = "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS"
EVIDENCE_CLASS = "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_NOAPI_PREREG_SYNTHESIS_WITH_RANKED_NEXT_ROUTE_BUNDLE"

REQUIRED_JSON_STEMS = [
    "DECISION_LEDGER",
    "ROUTE_RANKING_MATRIX",
    "READY_8_ROUTE_LEDGER",
    "BLOCKED_32_ROUTE_LEDGER",
    "EXPANSION_CANDIDATE_LEDGER",
    "NONBLOCKING_FOLLOWUP_LEDGER",
    "PARALLELIZATION_PLAN",
    "COMPLETION_AUDIT",
    "VERIFICATION_RESULT",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = [
    "DECISION_LEDGER",
    "ROUTE_RANKING_MATRIX",
    "READY_8_ROUTE_LEDGER",
    "BLOCKED_32_ROUTE_LEDGER",
    "EXPANSION_CANDIDATE_LEDGER",
    "NONBLOCKING_FOLLOWUP_LEDGER",
    "PARALLELIZATION_PLAN",
    "SATURATION_SELF_RED_TEAM",
    "OUTPUT_MANIFEST",
]
REQUIRED_PY = [
    "build_g0_scid_noapi_prereg_synthesis_2026_05_12.py",
    "verify_g0_scid_noapi_prereg_synthesis_2026_05_12.py",
    "test_g0_scid_noapi_prereg_synthesis_2026_05_12.py",
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
REQUIRED_ROUTE_IDS = {
    "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
    "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
    "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
    "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
    "SCID_TARGET_MANIFEST_SELF_HASH_POLICY_MAINTENANCE",
    "SCID_DORMANT_SEALED_RESULT_GATE_AFTER_PACKET_SOURCE_COMPLETION",
}


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


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R1_READY8_MATERIALIZE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R2_LTF_PROXY_SOURCE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R3_FUTURE_CAPTURE_SOURCE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R4_EXPANSION_DESIGN_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R5_ANTI_BOXING_INTAKE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R6_SELF_HASH_MAINT_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_R7_DORMANT_RESULT_GATE_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
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


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = artifact_path("COMPLETION_AUDIT")
    if not path.exists():
        return
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    if mark_focused_tests_ok:
        completion["focused_tests_ok"] = True
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "standalone verifier and focused tests pass":
            row["satisfied"] = result["ok"] and bool(mark_focused_tests_ok)
            row["evidence"] = rel(artifact_path("VERIFICATION_RESULT"))
    non_commit_rows = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "scoped artifacts and context refresh committed"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(row.get("satisfied") is True for row in non_commit_rows)
    completion["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(path, completion)


def refresh_output_manifest(result: dict[str, Any]) -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = artifact_path("OUTPUT_MANIFEST", ".md")
    ranking_path = artifact_path("ROUTE_RANKING_MATRIX")
    if not manifest_path.exists() or not ranking_path.exists():
        return
    ranking = read_json(ranking_path)
    excluded = {manifest_path.resolve(), manifest_md_path.resolve()}
    paths: set[Path] = set()
    for path in ROUTE_DIR.iterdir():
        if path.is_file() and path.resolve() not in excluded and path.suffix.lower() in {".json", ".md", ".py", ".txt"}:
            paths.add(path)
    for route in ranking.get("routes", []):
        prompt_path = ROOT / route.get("prompt_path", "")
        if prompt_path.exists():
            paths.add(prompt_path)
    manifest = read_json(manifest_path)
    manifest["artifact_count"] = len(paths)
    manifest["artifacts"] = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(paths)
    ]
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    write_json(manifest_path, manifest)
    manifest_md_path.write_text(
        "\n".join(
            [
                "# Output Manifest",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def verify(mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    for stem in REQUIRED_JSON_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing json artifact: {rel(path)}")
            continue
        loaded[stem] = read_json(path)
    for stem in REQUIRED_MD_STEMS:
        path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append(f"missing markdown artifact: {rel(path)}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing python artifact: {name}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    for stem, payload in loaded.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: missing NO_PROMOTION_VERDICT")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: expected {flag}=false, got {payload.get(flag)!r}")

    decision = loaded.get("DECISION_LEDGER", {})
    facts = decision.get("accepted_facts", {})
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("decision: terminal decision mismatch")
    if facts.get("accepted_card_count") != 40:
        failures.append("decision: accepted card count != 40")
    if facts.get("science_domain_count") != 8:
        failures.append("decision: science domain count != 8")
    if set(facts.get("cards_per_domain", {}).values()) != {5}:
        failures.append("decision: cards/domain not all 5")
    if facts.get("readiness_split") != {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }:
        failures.append("decision: readiness split mismatch")
    if facts.get("outside_current_gtos_ob_framing_count") != 33:
        failures.append("decision: outside-current-GTOS/OB count != 33")
    if facts.get("replay_input_packet_design_count") != 8:
        failures.append("decision: replay packet count != 8")
    if facts.get("blocked_dependency_row_count") != 32:
        failures.append("decision: blocked dependency count != 32")
    if facts.get("quarantined_expansion_candidate_count") != 8:
        failures.append("decision: expansion candidate count != 8")
    if facts.get("same_evidence_class_capture_groups_pursued") != 10:
        failures.append("decision: capture groups pursued != 10")
    if facts.get("capture_groups_resolved_inside_packet_design_scope") != 8:
        failures.append("decision: resolved capture groups != 8")
    if facts.get("remaining_exact_dependency_blockers") != 2:
        failures.append("decision: remaining exact dependency blockers != 2")

    ranking = loaded.get("ROUTE_RANKING_MATRIX", {})
    routes = ranking.get("routes", [])
    route_ids = {row.get("route_id") for row in routes}
    if route_ids != REQUIRED_ROUTE_IDS:
        failures.append(f"ranking: route ids mismatch {sorted(route_ids)}")
    if ranking.get("rank_1_route") != "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION":
        failures.append("ranking: wrong rank 1 route")
    if ranking.get("immediate_result_execution_is_allowed_now") is not False:
        failures.append("ranking: immediate result execution must be false")
    if not ranking.get("accepted_40_is_floor_not_ceiling"):
        failures.append("ranking: accepted 40 floor-not-ceiling flag missing")
    for row in routes:
        if row.get("may_open_outcomes_or_results_in_this_route") is not False:
            failures.append(f"ranking: {row.get('route_id')} opens outcomes/results in this route")
        prompt_path = ROOT / row.get("prompt_path", "")
        starter_path = ROOT / row.get("starter_path", "")
        if not prompt_path.exists():
            failures.append(f"ranking: missing prompt {row.get('prompt_path')}")
            continue
        if not starter_path.exists():
            failures.append(f"ranking: missing starter {row.get('starter_path')}")
            continue
        prompt_text = prompt_path.read_text(encoding="utf-8")
        starter_text = starter_path.read_text(encoding="utf-8").strip()
        if "\n" in starter_text or len(starter_text) >= 4000:
            failures.append(f"ranking: starter invalid for {row.get('route_id')}")
        for phrase in [
            "Do not rely on chat memory",
            "Current GTOS OB/retest logic is not the research horizon",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            if phrase not in prompt_text:
                failures.append(f"prompt {row.get('route_id')}: missing phrase {phrase}")
        if not starter_text.startswith("/goal Follow the full controlling prompt"):
            failures.append(f"starter {row.get('route_id')}: missing /goal prefix")

    ready = loaded.get("READY_8_ROUTE_LEDGER", {})
    if ready.get("ready_card_count") != 8:
        failures.append("ready ledger: card count != 8")
    if not ready.get("ready_cards_all_routed_to_rank_1"):
        failures.append("ready ledger: not all routed to rank 1")
    if any(row.get("may_score_results_now") for row in ready.get("ready_cards", [])):
        failures.append("ready ledger: a ready card may score results now")

    blocked = loaded.get("BLOCKED_32_ROUTE_LEDGER", {})
    if blocked.get("blocked_card_count") != 32:
        failures.append("blocked ledger: card count != 32")
    if blocked.get("blocked_readiness_split") != {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    }:
        failures.append("blocked ledger: readiness split mismatch")
    assigned = blocked.get("assigned_route_counts", {})
    if assigned.get("SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17", 0) != 17:
        failures.append("blocked ledger: LTF/orderflow route count != 17")
    if assigned.get("SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15", 0) != 15:
        failures.append("blocked ledger: future-capture route count != 15")

    expansion = loaded.get("EXPANSION_CANDIDATE_LEDGER", {})
    if expansion.get("preserved_target_expansion_candidate_count") != 8:
        failures.append("expansion ledger: preserved target expansion count != 8")
    if expansion.get("total_quarantined_expansion_candidate_count", 0) < 8:
        failures.append("expansion ledger: total quarantined count < 8")
    if not expansion.get("all_expansion_candidates_remain_outside_accepted_denominator"):
        failures.append("expansion ledger: denominator quarantine missing")

    followup = loaded.get("NONBLOCKING_FOLLOWUP_LEDGER", {})
    if followup.get("nonblocking_followup_count") != 1:
        failures.append("followup ledger: expected one nonblocking followup")
    if followup.get("self_hash_issue_is_nonblocking") is not True:
        failures.append("followup ledger: self-hash issue not nonblocking")
    if followup.get("fake_blocker_rejected") is not True:
        failures.append("followup ledger: fake blocker not rejected")

    parallel = loaded.get("PARALLELIZATION_PLAN", {})
    run_now = set(parallel.get("run_now_parallel_routes", []))
    if not {
        "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION",
        "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17",
        "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
        "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE",
        "SCID_NOAPI_CROSS_DOMAIN_ANTI_BOXING_ROUTE_INTAKE",
    }.issubset(run_now):
        failures.append("parallel plan: expected run-now routes missing")
    if parallel.get("do_not_run_until_dependency_valid") != [
        "SCID_DORMANT_SEALED_RESULT_GATE_AFTER_PACKET_SOURCE_COMPLETION"
    ]:
        failures.append("parallel plan: dormant sealed result gate classification mismatch")

    saturation_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if saturation_path.exists():
        saturation = saturation_path.read_text(encoding="utf-8")
        for phrase in ["OB-only", "passive waiting", "self-hash mismatch as a fake blocker", "No outcome/result"]:
            if phrase not in saturation:
                failures.append(f"saturation: missing phrase {phrase}")

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live surface")
    if not git_status["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": TERMINAL_DECISION,
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
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures,
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
        "card_count_verified": facts.get("accepted_card_count"),
        "domain_count_verified": facts.get("science_domain_count"),
        "readiness_split_verified": facts.get("readiness_split"),
        "outside_current_gtos_ob_framing_count_verified": facts.get("outside_current_gtos_ob_framing_count"),
        "ready_packet_count_verified": ready.get("ready_card_count"),
        "blocked_dependency_count_verified": blocked.get("blocked_card_count"),
        "preserved_expansion_candidate_count_verified": expansion.get("preserved_target_expansion_candidate_count"),
        "total_expansion_candidate_count_verified": expansion.get("total_quarantined_expansion_candidate_count"),
    }
    write_json(artifact_path("VERIFICATION_RESULT"), result)
    refresh_completion(result, mark_focused_tests_ok)
    refresh_output_manifest(result)
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
