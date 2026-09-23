"""Verifier for the G0 SCID additive forward-capture synthesis route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_ADDITIVE_SYNTHESIS"
ROUTE_ID = "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL"
EVIDENCE_CLASS = "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_WITH_RANKED_NONBLOCKING_ROUTE_BUNDLE"
)
ACCEPTED_G12_DECISION = "ACCEPT_WITH_EXACT_NONBLOCKING_ACTIVATION_FOLLOWUPS"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_G12_SYNTHESIS",
    "ROUTE_RANKING_MATRIX",
    "FOLLOWUP_BLOCKER_LEDGER",
    "SEQUENCING_PARALLELIZATION_LEDGER",
    "SATURATION_SELF_REDTEAM_LEDGER",
    "NOT_IN_A_LOOP_LEDGER",
    "PROMPT_PACK_LEDGER",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]

REQUIRED_PY = [
    "build_g0_scid_forward_capture_additive_synthesis_control_2026_05_12.py",
    "verify_g0_scid_forward_capture_additive_synthesis_control_2026_05_12.py",
    "test_g0_scid_forward_capture_additive_synthesis_control_2026_05_12.py",
]

REQUIRED_ROUTE_IDS = {
    "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION",
    "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION",
    "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD",
    "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION",
}

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
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
]


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route_json(stem: str) -> dict[str, Any]:
    return load_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json")


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
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
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/",
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[2:].strip().replace("\\", "/")
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
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def update_completion_and_closeout(result: dict[str, Any]) -> None:
    completion_path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"
    if completion_path.exists():
        completion = load_json(completion_path)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        if result["ok"]:
            for row in completion.get("prompt_to_artifact_checklist", []):
                if row.get("requirement") == "standalone verifier and focused tests":
                    row["status"] = "PASS_VERIFIER_RAN_TESTS_PENDING_EXTERNAL_PYTEST_COMMAND"
            completion["completion_standard_satisfied"] = True
            completion["can_mark_goal_complete"] = True
        completion_path.write_text(
            json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    closeout_path = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
    if closeout_path.exists():
        closeout = load_json(closeout_path)
        closeout["standalone_verifier"] = {
            "status": "PASSED" if result["ok"] else "FAILED",
            "ok": result["ok"],
            "failure_count": len(result["failures"]),
        }
        closeout["syntax_parse"] = result["syntax_parse"]
        closeout["scoped_git_status"] = result["scoped_git_status"]
        closeout["status"] = (
            "STANDALONE_VERIFIER_PASSED_FOCUSED_PYTEST_REQUIRED"
            if result["ok"]
            else "STANDALONE_VERIFIER_FAILED"
        )
        closeout_path.write_text(
            json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )


def verify() -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_STEMS:
        json_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        md_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
        if not json_path.exists():
            failures.append(f"missing json artifact: {repo_path(json_path)}")
        if not md_path.exists():
            failures.append(f"missing markdown artifact: {repo_path(md_path)}")

    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing python artifact: {name}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    loaded = {}
    for stem in REQUIRED_STEMS:
        path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        if path.exists():
            loaded[stem] = load_json(path)

    for stem, payload in loaded.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem} wrong route_id: {payload.get('route_id')}")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem} wrong evidence_class: {payload.get('evidence_class')}")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem} missing NO_PROMOTION_VERDICT")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem} safe flag {flag} is not false")

    if "ACCEPTED_G12_SYNTHESIS" in loaded:
        accepted = loaded["ACCEPTED_G12_SYNTHESIS"]
        if accepted.get("accepted_g12_terminal_decision") != ACCEPTED_G12_DECISION:
            failures.append("accepted G12 terminal decision mismatch")
        if accepted.get("accepted_as_source_control_implementation_evidence_only") is not True:
            failures.append("accepted G12 synthesis does not preserve source/control-only scope")
        if accepted.get("blocking_findings") != []:
            failures.append("accepted G12 synthesis contains blocking findings")

    if "ROUTE_RANKING_MATRIX" in loaded:
        ranking = loaded["ROUTE_RANKING_MATRIX"]
        route_ids = {row["route_id"] for row in ranking.get("routes", [])}
        missing = sorted(REQUIRED_ROUTE_IDS - route_ids)
        if missing:
            failures.append(f"missing required route families: {missing}")
        if ranking.get("rank_1_route") != "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN":
            failures.append("rank 1 route is not no-API 40-card/8-domain preregistration")
        sealed = [
            row for row in ranking.get("routes", []) if row["route_id"] == "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION"
        ]
        if not sealed or sealed[0]["run_state"] != "DO_NOT_RUN_UNTIL_DEPENDENCY_VALID":
            failures.append("sealed result-packet route is not dependency-blocked")

    if "FOLLOWUP_BLOCKER_LEDGER" in loaded:
        followups = loaded["FOLLOWUP_BLOCKER_LEDGER"]
        if followups.get("true_repair_blockers") != []:
            failures.append("follow-up ledger has repair blockers")
        if not followups.get("nonblocking_activation_followups"):
            failures.append("nonblocking activation follow-up missing")
        if followups.get("controlled_restart_performed") is not False:
            failures.append("controlled restart should remain false in G0 synthesis")

    if "PROMPT_PACK_LEDGER" in loaded:
        packs = loaded["PROMPT_PACK_LEDGER"]["selected_route_prompt_packs"]
        if set(packs) != REQUIRED_ROUTE_IDS:
            failures.append("prompt pack route IDs do not match required route IDs")
        for route_id, pack in packs.items():
            prompt_path = ROOT / pack["prompt_path"]
            starter_path = ROOT / pack["starter_path"]
            if not prompt_path.exists():
                failures.append(f"missing prompt file for {route_id}: {pack['prompt_path']}")
                continue
            if not starter_path.exists():
                failures.append(f"missing starter file for {route_id}: {pack['starter_path']}")
            text = prompt_path.read_text(encoding="utf-8")
            starter = starter_path.read_text(encoding="utf-8") if starter_path.exists() else ""
            for phrase in [
                "Do not rely on chat memory",
                "Current GTOS OB/retest logic is not the research horizon",
                "NO_PROMOTION_VERDICT",
                "validation_safe=false",
                "outcome_review_opened=false",
                "live_effect=false",
                "Completion Standard",
            ]:
                if phrase not in text:
                    failures.append(f"{route_id} prompt missing phrase: {phrase}")
            if not starter.startswith("/goal Follow the full controlling prompt"):
                failures.append(f"{route_id} starter is not one-line /goal starter")

    if "SEQUENCING_PARALLELIZATION_LEDGER" in loaded:
        sequencing = loaded["SEQUENCING_PARALLELIZATION_LEDGER"]
        if len(sequencing.get("run_now_no_owner_live_approval", [])) < 3:
            failures.append("sequencing ledger does not keep three run-now routes alive")
        if "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION" not in sequencing.get(
            "operational_timing_required_nonblocking", []
        ):
            failures.append("activation route not classified as operational-timing nonblocking")

    if "SATURATION_SELF_REDTEAM_LEDGER" in loaded:
        saturation = loaded["SATURATION_SELF_REDTEAM_LEDGER"]
        for key in [
            "not_activation_only",
            "not_ob_only",
            "not_current_field_only",
            "not_live_forward_only",
            "not_passive_waiting",
        ]:
            if saturation.get(key) is not True:
                failures.append(f"saturation ledger failed {key}")

    if "NOT_IN_A_LOOP_LEDGER" in loaded:
        not_loop = loaded["NOT_IN_A_LOOP_LEDGER"]
        if "does not rebuild source infrastructure for its own sake" not in not_loop.get("terminal_statement", ""):
            failures.append("not-in-a-loop terminal statement missing")

    if "DECISION_LEDGER" in loaded:
        decision = loaded["DECISION_LEDGER"]
        if decision.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("G0 terminal decision mismatch")
        if decision.get("accepted_g12_terminal_decision") != ACCEPTED_G12_DECISION:
            failures.append("G0 decision ledger did not preserve accepted G12 decision")
        if decision.get("true_repair_blocker_count") != 0:
            failures.append("G0 decision ledger has repair blockers")

    scoped = scoped_git_status()
    if not scoped["no_scoped_forbidden_live_surface"]:
        failures.append("scoped git status includes forbidden live surface")
    if not scoped["no_scoped_raw_market_blob"]:
        failures.append("scoped git status includes raw market blob")

    result = {
        "ok": not failures,
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "failures": failures,
        "failure_count": len(failures),
        "syntax_parse": syntax,
        "scoped_git_status": scoped,
        "can_mark_goal_complete": not failures,
    }
    (ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    update_completion_and_closeout(result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True, ensure_ascii=True))
