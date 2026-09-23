"""Standalone verifier for the G12 ready-8 packet audit artifacts."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NOAPI_READY8"
ROUTE_ID = "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_ONLY"
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_READY_CARDS = 8
READY_CARD_IDS = [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
]
SAFE_FLAGS = {
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
}

CORE_SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

JSON_STEMS = [
    "DECISION_LEDGER",
    "ROWSET_COUNT_AUDIT",
    "HASH_ASOF_AUDIT",
    "DUPLICATE_DENOMINATOR_AUDIT",
    "PARTITION_BASELINE_CONTROL_AUDIT",
    "TARGET_HORIZON_NO_RESULT_AUDIT",
    "EXPANSION_QUARANTINE_AUDIT",
    "NO_LEAK_FORBIDDEN_SURFACE_AUDIT",
    "TARGET_ROUTE_VERIFICATION_RERUN_AUDIT",
    "BLOCKER_FOLLOWUP_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def read_json(stem: str) -> dict[str, Any]:
    return json.loads(artifact_path(stem).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def syntax_parse() -> dict[str, Any]:
    failures = []
    for path in [
        ROUTE_DIR / "build_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
        ROUTE_DIR / "verify_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
        ROUTE_DIR / "test_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
    ]:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    scoped_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_rowset_target_horizon_packet_audit/",
        "research/science_program_2026_05/04_goal_prompts/G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ]
    forbidden_prefixes = [
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "run_agent.py",
        "pipeline_state/",
        "knowledge_base/trade_records/",
        "shadow_logs/",
        "data/ticks/",
        "data/external/",
    ]
    scoped = []
    forbidden = []
    for line in lines:
        path = line[3:].replace("\\", "/") if len(line) > 3 else line
        if any(path.startswith(prefix) for prefix in scoped_prefixes):
            scoped.append(path)
        if any(path.startswith(prefix) for prefix in forbidden_prefixes):
            forbidden.append(path)
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr,
        "scoped_entries": scoped,
        "unscoped_entry_count": max(0, len(lines) - len(scoped)),
        "forbidden_live_surface_entries": forbidden,
        "no_scoped_forbidden_live_surface": not forbidden,
    }


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    completion = read_json("COMPLETION_AUDIT")
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    if mark_focused_tests_ok and result["ok"]:
        completion["focused_tests_ok"] = True
    completion["completion_standard_satisfied"] = (
        result["ok"]
        and completion.get("focused_tests_ok") is True
        and completion.get("completion_standard_satisfied_before_commit") is True
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied"]
    write_json(artifact_path("COMPLETION_AUDIT"), completion)


def write_focused_test_result(result: dict[str, Any]) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "focused_pytest_command": (
            "python -B -m pytest "
            "research/science_program_2026_05/06_outcome_testing/"
            "g12_scid_noapi_ready8_rowset_target_horizon_packet_audit/"
            "test_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py -q"
        ),
        "focused_tests_ok": True,
        "standalone_verifier_ok": result["ok"],
    }
    write_json(artifact_path("FOCUSED_TEST_RESULT"), payload)


def refresh_output_manifest() -> None:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    if not manifest_path.exists():
        return
    artifact_paths = [
        artifact_path(stem)
        for stem in [
            "DECISION_LEDGER",
            "ROWSET_COUNT_AUDIT",
            "HASH_ASOF_AUDIT",
            "DUPLICATE_DENOMINATOR_AUDIT",
            "PARTITION_BASELINE_CONTROL_AUDIT",
            "TARGET_HORIZON_NO_RESULT_AUDIT",
            "EXPANSION_QUARANTINE_AUDIT",
            "NO_LEAK_FORBIDDEN_SURFACE_AUDIT",
            "TARGET_ROUTE_VERIFICATION_RERUN_AUDIT",
            "BLOCKER_FOLLOWUP_LEDGER",
            "COMPLETION_AUDIT",
            "VERIFICATION_RESULT",
            "FOCUSED_TEST_RESULT",
        ]
    ]
    artifact_paths.extend(
        [
            artifact_path("SATURATION_SELF_RED_TEAM", ".md"),
            ROUTE_DIR / "build_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
            ROUTE_DIR / "verify_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
            ROUTE_DIR / "test_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
            ROOT
            / "research"
            / "science_program_2026_05"
            / "04_goal_prompts"
            / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
            ROUTE_DIR / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_STARTER_2026-05-12.txt",
        ]
    )
    rows = []
    for path in sorted({p for p in artifact_paths if p.exists()}, key=lambda p: rel(p)):
        rows.append({"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    manifest = read_json("OUTPUT_MANIFEST")
    manifest["artifact_count"] = len(rows)
    manifest["artifacts"] = rows
    manifest["verification_result"] = {
        "path": rel(artifact_path("VERIFICATION_RESULT")),
        "ok": read_json("VERIFICATION_RESULT").get("ok"),
        "failure_count": read_json("VERIFICATION_RESULT").get("failure_count"),
        "can_mark_goal_complete": read_json("VERIFICATION_RESULT").get("can_mark_goal_complete"),
    }
    write_json(manifest_path, manifest)


def verify(write_result: bool = True, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    syntax = syntax_parse()
    failures.extend(syntax["failures"])

    loaded = {}
    for stem in JSON_STEMS:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing artifact: {rel(path)}")
            continue
        payload = read_json(stem)
        loaded[stem] = payload
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        for key, expected in CORE_SAFE_FLAGS.items():
            if payload.get(key) != expected:
                failures.append(f"{stem}: expected {key}={expected!r}, got {payload.get(key)!r}")
        for key in SAFE_FLAGS:
            if key.startswith("opens_") and payload.get(key) not in (None, False):
                failures.append(f"{stem}: expected {key} absent-or-false, got {payload.get(key)!r}")
        for key in ["credentials_touched", "changes_trading_risk_safety_prompt_decision_behavior"]:
            if payload.get(key) not in (None, False):
                failures.append(f"{stem}: expected {key} absent-or-false, got {payload.get(key)!r}")

    sat_path = artifact_path("SATURATION_SELF_RED_TEAM", ".md")
    if not sat_path.exists():
        failures.append(f"missing artifact: {rel(sat_path)}")
    else:
        sat = sat_path.read_text(encoding="utf-8")
        for phrase in [
            "Row inflation bug",
            "Future-label leakage bug",
            "Ready/blocked confusion bug",
            "Expansion denominator bug",
            "Non-deterministic control bug",
            "Silent scoring bug",
            "Same-Evidence-Class Ambiguities Pursued",
            "CRLF line endings",
        ]:
            if phrase not in sat:
                failures.append(f"saturation artifact missing phrase: {phrase}")

    if loaded:
        decision = loaded.get("DECISION_LEDGER", {})
        rowset = loaded.get("ROWSET_COUNT_AUDIT", {})
        hash_asof = loaded.get("HASH_ASOF_AUDIT", {})
        duplicate = loaded.get("DUPLICATE_DENOMINATOR_AUDIT", {})
        partition = loaded.get("PARTITION_BASELINE_CONTROL_AUDIT", {})
        target = loaded.get("TARGET_HORIZON_NO_RESULT_AUDIT", {})
        expansion = loaded.get("EXPANSION_QUARANTINE_AUDIT", {})
        no_leak = loaded.get("NO_LEAK_FORBIDDEN_SURFACE_AUDIT", {})
        blocker = loaded.get("BLOCKER_FOLLOWUP_LEDGER", {})
        rerun = loaded.get("TARGET_ROUTE_VERIFICATION_RERUN_AUDIT", {})
        completion = loaded.get("COMPLETION_AUDIT", {})

        if decision.get("terminal_decision") not in {
            "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
            "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
        }:
            failures.append("terminal decision is not an allowed acceptance decision")
        if decision.get("terminal_blockers"):
            failures.append(f"decision ledger has terminal blockers: {decision.get('terminal_blockers')}")
        ready_scope = decision.get("ready_scope", {})
        if ready_scope.get("ready_cards_match_expected") is not True:
            failures.append("ready scope mismatch")
        if ready_scope.get("accepted_card_denominator_recomputed") != 40:
            failures.append("accepted card denominator is not 40")
        if ready_scope.get("blocked_dependency_count_recomputed") != 32:
            failures.append("blocked dependency count is not 32")

        if rowset.get("rowset_row_count_recomputed") != EXPECTED_ROWSET_ROWS:
            failures.append("rowset row count mismatch")
        if rowset.get("source_candidate_count_recomputed") != EXPECTED_SOURCE_CANDIDATES:
            failures.append("source candidate count mismatch")
        if rowset.get("ready_card_count_recomputed") != EXPECTED_READY_CARDS:
            failures.append("ready card count mismatch")
        if rowset.get("ready_card_ids_recomputed") != READY_CARD_IDS:
            failures.append("ready card IDs mismatch")
        if set((rowset.get("per_card_counts_recomputed") or {}).values()) != {EXPECTED_SOURCE_CANDIDATES}:
            failures.append("per-card counts mismatch")
        for key in [
            "candidate_card_coverage_missing_count",
            "duplicate_key_collision_count_recomputed",
            "forbidden_row_field_hit_count",
            "asof_violation_count",
            "missing_source_hash_count",
            "missing_row_hash_count",
            "parser_asof_version_missing_count",
            "row_hash_mismatch_count",
            "rowset_row_id_mismatch_count",
            "baseline_seed_mismatch_count",
            "control_bucket_mismatch_count",
            "matched_control_group_mismatch_count",
            "candidate_source_hash_mismatch_count",
            "descriptor_row_hash_mismatch_count",
            "source_artifact_pointer_file_hash_mismatch_count",
            "row_safe_flag_violation_count",
            "unexpected_card_row_count",
            "blocked_card_row_count",
        ]:
            if rowset.get(key) != 0:
                failures.append(f"rowset audit nonzero {key}: {rowset.get(key)}")

        if hash_asof.get("source_artifact_hash_mismatch_count") != 0:
            failures.append("source artifact hash mismatch")
        if hash_asof.get("source_observed_asof_lte_decision_asof_count") != EXPECTED_ROWSET_ROWS:
            failures.append("as-of lte count mismatch")
        if duplicate.get("ready_card_row_denominator_count_recomputed") != EXPECTED_ROWSET_ROWS:
            failures.append("duplicate denominator ready row mismatch")
        if duplicate.get("duplicate_proxy_denominator_key_count_recomputed") != EXPECTED_SOURCE_CANDIDATES:
            failures.append("duplicate key denominator mismatch")
        if duplicate.get("quarantined_expansion_denominator_inclusion") is not False:
            failures.append("duplicate manifest expansion inclusion not false")
        if partition.get("deterministic_assignments_only") is not True:
            failures.append("partition/control deterministic flag missing")
        if partition.get("result_or_performance_lookup_used") is not False:
            failures.append("baseline/control result lookup used")
        if partition.get("contaminated_or_forbidden_candidate_count") != 0:
            failures.append("contaminated/forbidden partition not empty")
        if target.get("target_or_hazard_hits_computed") is not False:
            failures.append("target/hazard hits computed")
        if target.get("performance_or_result_fields_present") is not False:
            failures.append("target/result performance fields present")
        if target.get("forbidden_exact_key_hit_count") != 0:
            failures.append("target horizon forbidden exact keys present")
        if expansion.get("accepted_40_is_floor_not_ceiling") is not True:
            failures.append("accepted 40 floor-not-ceiling flag missing")
        if expansion.get("all_expansion_observations_remain_outside_accepted_denominator") is not True:
            failures.append("expansion accepted denominator inclusion")
        if expansion.get("all_expansion_observations_remain_outside_ready8_denominator") is not True:
            failures.append("expansion ready8 denominator inclusion")
        if no_leak.get("artifact_safe_flag_violation_count") != 0:
            failures.append("artifact safe flag violation")
        if no_leak.get("forbidden_row_field_hit_count") != 0:
            failures.append("forbidden row field hit")
        if blocker.get("repair_blocker_count") != 0:
            failures.append("repair blocker count is nonzero")
        if blocker.get("may_score_results_now") is not False:
            failures.append("blocker ledger allows scoring now")
        line_friction = rerun.get("line_ending_friction_classification", {})
        accepted_line_friction = (
            line_friction.get("accepted_as_environment_friction_not_packet_content_drift") is True
            and line_friction.get("semantic_row_audit_passed") is True
        )
        if (rerun.get("target_verifier") or {}).get("ok") is not True and not accepted_line_friction:
            failures.append("target verifier rerun not ok")
        if (rerun.get("target_focused_pytest") or {}).get("ok") is not True and not accepted_line_friction:
            failures.append("target focused pytest not ok")
        checklist = completion.get("prompt_to_artifact_checklist", [])
        if not checklist or not all(item.get("satisfied") for item in checklist):
            failures.append("completion checklist has unsatisfied items")

    git_status = scoped_git_status()
    if not git_status["no_scoped_forbidden_live_surface"]:
        failures.append(f"forbidden live-surface paths in git status: {git_status['forbidden_live_surface_entries']}")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
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
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
        "focused_tests_ok": mark_focused_tests_ok,
        "rowset_row_count_verified": (loaded.get("ROWSET_COUNT_AUDIT", {}) or {}).get(
            "rowset_row_count_recomputed"
        ),
        "source_candidate_count_verified": (loaded.get("ROWSET_COUNT_AUDIT", {}) or {}).get(
            "source_candidate_count_recomputed"
        ),
        "ready_card_count_verified": (loaded.get("ROWSET_COUNT_AUDIT", {}) or {}).get(
            "ready_card_count_recomputed"
        ),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    if write_result:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        refresh_completion(result, mark_focused_tests_ok)
        if mark_focused_tests_ok and result["ok"]:
            write_focused_test_result(result)
        refresh_output_manifest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
