"""Verifier for the G0 SCID as-of synthesis and validation-design route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
)
DATE_TAG = "2026-05-11"
PREFIX = "G0_SCID_ASOF"
ROUTE_ID = "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN"
EVIDENCE_CLASS = "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_ONLY"
NEXT_G12_PROMPT = PROMPT_DIR / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-11.md"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"

EXPECTED_COUNTS = {
    "source_control_bar_rows": 7567,
    "candidate_generator_input_only_rows": 3014,
    "accepted_bounded_scid_segments": 9,
    "candidate_denominator_economic_groups": 7,
    "discovery_exclusions": 365,
    "adversarial_baselines": 4,
}
EXPECTED_BASELINES = {
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
}
REQUIRED_FILES = [
    f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.md",
    f"{PREFIX}_SYNTHESIS_DECISION_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_ACCEPTED_PACKET_RECONCILIATION_{DATE_TAG}.json",
    f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl",
    f"{PREFIX}_VALIDATION_DESIGN_RULEBOOK_{DATE_TAG}.json",
    f"{PREFIX}_NOLEAK_FIELD_CONTRACT_{DATE_TAG}.json",
    f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json",
    f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json",
    f"{PREFIX}_MULTIPLE_TESTING_DEBT_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_FALSIFICATION_STOP_CONDITIONS_{DATE_TAG}.json",
    f"{PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
    "build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
    "verify_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
    "test_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_scored_candidate_generation",
    "opens_replay_path_label_result_outcomes",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]
ROW_FORBIDDEN_KEYS = {
    "actual_r",
    "broker_actual_r",
    "path_label",
    "result",
    "pnl",
    "expectancy",
    "win_rate",
    "performance",
    "cost",
    "slippage",
    "account",
    "order",
    "deal",
    "position",
}


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    scoped_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-11.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_market_suffixes = (".scid", ".depth", ".parquet", ".csv", ".jsonl.gz", ".bin", ".dly")
    entries = []
    for line in proc.stdout.strip().splitlines():
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in scoped_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "forbidden_live_surface_path": path.startswith(forbidden_live_prefixes),
                "raw_market_extension": path.endswith(raw_market_suffixes),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "no_forbidden_live_surface_in_scoped_entries": not any(
            row["forbidden_live_surface_path"] for row in scoped_entries
        ),
        "no_raw_market_blobs_in_scoped_entries": not any(row["raw_market_extension"] for row in scoped_entries),
    }


def json_payloads() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for path in ROUTE_DIR.glob(f"{PREFIX}_*.json"):
        if path.name == VERIFICATION_RESULT.name:
            continue
        payloads[path.name] = load_json(path)
    return payloads


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path.name}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def update_completion_audit(ok: bool, failures: list[str]) -> None:
    if not COMPLETION_AUDIT.exists():
        return
    payload = load_json(COMPLETION_AUDIT)
    payload["standalone_verifier_ok"] = ok
    payload["standalone_verifier_failures"] = failures
    payload["can_mark_goal_complete"] = ok
    payload["completion_standard_satisfied"] = ok
    payload["can_mark_goal_complete_reason"] = (
        "standalone verifier emitted ok=true and all prompt coverage checks passed"
        if ok
        else "standalone verifier failed; see standalone_verifier_failures"
    )
    COMPLETION_AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    failures: list[str] = []

    for name in REQUIRED_FILES:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing required route artifact: {name}")
    if not NEXT_G12_PROMPT.exists():
        failures.append(f"missing next G12 prompt: {repo_path(NEXT_G12_PROMPT)}")

    payloads = json_payloads()
    for name, payload in payloads.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{name}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{name}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{name}: promotion_verdict not closed")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{name}: {flag} is not false")

    reconciliation = load_json(ROUTE_DIR / f"{PREFIX}_ACCEPTED_PACKET_RECONCILIATION_{DATE_TAG}.json")
    checks = {row["check_id"]: row for row in reconciliation["exact_count_checks"]}
    for check_id, expected in EXPECTED_COUNTS.items():
        row = checks.get(check_id)
        if row is None:
            failures.append(f"missing count check: {check_id}")
        elif row.get("expected") != expected or row.get("actual") != expected or row.get("status") != "PASS":
            failures.append(f"failed count check: {check_id} -> {row}")
    if reconciliation.get("terminal_decision") != "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY":
        failures.append("accepted G12 packet terminal decision mismatch")
    if reconciliation.get("no_terminal_packet_blockers") is not True:
        failures.append("terminal packet blockers remain")
    repaired = reconciliation.get("warnings_repaired", {})
    if repaired.get("FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW") is not True:
        failures.append("FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW not repaired")
    if repaired.get("TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE") is not True:
        failures.append("TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE not repaired")

    source_candidates = load_jsonl(PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl")
    source_ids = [row["candidate_input_row_id"] for row in source_candidates]
    partition_rows = load_jsonl(ROUTE_DIR / f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl")
    partition_ids = [row["candidate_input_row_id"] for row in partition_rows]
    if len(partition_rows) != EXPECTED_COUNTS["candidate_generator_input_only_rows"]:
        failures.append("row partition count mismatch")
    if len(set(partition_ids)) != len(partition_ids):
        failures.append("duplicate candidate ids in row partition")
    if set(partition_ids) != set(source_ids):
        failures.append("row partition ids do not exactly match source candidate input ids")
    allowed_partitions = {"SEALED_VALIDATION_CANDIDATE_DESIGN", "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"}
    if not set(row["partition_assignment"] for row in partition_rows).issubset(allowed_partitions):
        failures.append("unexpected row partition assignment")
    for row in partition_rows:
        if row.get("discovery_exposure_flag") is not False:
            failures.append(f"discovery exposure flag not false: {row.get('candidate_input_row_id')}")
            break
        if row.get("safe_flags", {}).get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"safe flag missing on row: {row.get('candidate_input_row_id')}")
            break
        if len(row.get("included_bar_hashes", [])) != row.get("included_bar_hash_count"):
            failures.append(f"included bar hash count mismatch: {row.get('candidate_input_row_id')}")
            break
        forbidden_keys = ROW_FORBIDDEN_KEYS.intersection(row.keys())
        if forbidden_keys:
            failures.append(f"forbidden row keys present: {sorted(forbidden_keys)}")
            break

    duplicate_rules = load_json(ROUTE_DIR / f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json")
    if duplicate_rules.get("candidate_denominator_group_count") != 7:
        failures.append("candidate denominator group count is not 7")
    primary = duplicate_rules.get("primary_counting_source_by_group", {})
    if primary.get("XAUUSD_GOLD_FUTURES_PROXY") != "XAUUSD_GC":
        failures.append("XAUUSD primary denominator is not GC")
    if primary.get("US30_DOW_FUTURES_PROXY") != "US30_YM":
        failures.append("US30 primary denominator is not YM")
    if duplicate_rules.get("duplicate_key_collisions") != 0:
        failures.append("duplicate/proxy denominator collisions found")

    baseline_plan = load_json(ROUTE_DIR / f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json")
    if set(baseline_plan.get("four_adversarial_baselines_preserved", [])) != EXPECTED_BASELINES:
        failures.append("four adversarial baselines not preserved")
    if len(baseline_plan.get("robustness_tests_required_before_promotion_discussion", [])) < 12:
        failures.append("robustness plan is too thin")

    science = load_json(ROUTE_DIR / f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json")
    if len(science.get("families", [])) < 9:
        failures.append("science horizon does not cover required families")
    if any(row.get("claim_status") != "NO_CLAIM_WORKS" for row in science.get("families", [])):
        failures.append("science horizon contains a working-claim")

    redteam = load_json(ROUTE_DIR / f"{PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json")
    if len(redteam.get("redteam_questions", [])) < 8:
        failures.append("saturation red-team is incomplete")
    if redteam.get("remaining_same_evidence_class_gaps"):
        failures.append("remaining same-evidence-class gaps are present")
    if redteam.get("remaining_vague_blockers"):
        failures.append("remaining vague blockers are present")

    next_ranking = load_json(ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.json")
    if next_ranking.get("active_next_route") != "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT":
        failures.append("active next route is not the G12 design audit")
    if next_ranking.get("validation_execution_prompt_emitted") is not False:
        failures.append("validation execution prompt was emitted")
    prompt_text = NEXT_G12_PROMPT.read_text(encoding="utf-8") if NEXT_G12_PROMPT.exists() else ""
    for phrase in (
        "G12 SCID As-Of Sealed Validation Design Audit",
        "Forbidden: validation execution",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
    ):
        if phrase not in prompt_text:
            failures.append(f"next G12 prompt missing phrase: {phrase}")

    dirty = run_git_status()
    if dirty["returncode"] != 0:
        failures.append("git status failed for dirty-state scoped diff check")
    if not dirty["no_forbidden_live_surface_in_scoped_entries"]:
        failures.append("scoped diff contains forbidden live-surface path")
    if not dirty["no_raw_market_blobs_in_scoped_entries"]:
        failures.append("scoped diff contains raw market-data blob")

    syntax = syntax_parse(
        [
            ROUTE_DIR / "build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
            ROUTE_DIR / "verify_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
            ROUTE_DIR / "test_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
        ]
    )
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    ok = not failures
    update_completion_audit(ok, failures)
    result = {
        "schema_version": "g0_scid_asof_synthesis_validation_design_verification_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": ok,
        "can_mark_goal_complete": ok,
        "failures": failures,
        "count_checks": EXPECTED_COUNTS,
        "row_partition_count": len(partition_rows) if "partition_rows" in locals() else None,
        "dirty_state_scoped_diff": {
            "scoped_entry_count": len(dirty["scoped_entries"]),
            "no_forbidden_live_surface_in_scoped_entries": dirty["no_forbidden_live_surface_in_scoped_entries"],
            "no_raw_market_blobs_in_scoped_entries": dirty["no_raw_market_blobs_in_scoped_entries"],
            "git_status_stderr": dirty["stderr"],
        },
        "syntax_check": syntax,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
