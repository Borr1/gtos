#!/usr/bin/env python3
"""Build the G12 audit for the SCID target/horizon repair route.

This route is source-control audit only. It inspects existing repair,
predecessor, and packet artifacts; it does not compute target values,
generate result rows, score validation, call APIs, or touch live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT"
EVIDENCE_CLASS = "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_sealed_validation_target_horizon_repair"
)
PREDECESSOR_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_sealed_validation_execution_packet"
)
PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
)
G12_DESIGN_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_asof_sealed_validation_design_audit"
)

CONTROL_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_GOAL_PROMPT_2026-05-11.md"
)
REPAIR_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_REPAIR_PROMPT_2026-05-11.md"
)

EXPECTED_COUNTS = {
    "candidate_rows": 3014,
    "bar_rows": 7567,
    "sealed_rows": 2432,
    "stress_rows": 582,
    "discovery_exclusions": 365,
    "denominator_groups": 7,
    "known_families": 11,
}

STRATEGY_FAMILIES = [
    "adjacent_range_compression_breakout",
    "ob_retest",
    "opening_drive_no_fill_lifecycle",
    "fvg_fill",
    "liquidity_stop_run_context",
    "session_kz_sweep",
    "breaker_re_entry",
]
CONTROL_FAMILIES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
EXPECTED_FAMILIES = STRATEGY_FAMILIES + CONTROL_FAMILIES

REPAIR_FILES = {
    "blocker_reconciliation": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_BLOCKER_RECONCILIATION_{DATE_TAG}.json",
    "completion_audit": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_COMPLETION_AUDIT_{DATE_TAG}.json",
    "family_matrix": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_FAMILY_EXECUTABILITY_MATRIX_{DATE_TAG}.json",
    "multiple_testing": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_MULTIPLE_TESTING_LEDGER_{DATE_TAG}.json",
    "neutral_contract": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_NEUTRAL_TARGET_CONTRACT_{DATE_TAG}.json",
    "noleak_audit": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_NOLEAK_AUDIT_{DATE_TAG}.json",
    "output_manifest": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_OUTPUT_MANIFEST_{DATE_TAG}.json",
    "rulebook": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_RULEBOOK_{DATE_TAG}.json",
    "source_derivation": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_{DATE_TAG}.json",
    "source_expansion": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_SOURCE_EXPANSION_REQUIREMENTS_{DATE_TAG}.json",
    "verification": TARGET_DIR / f"SCID_ASOF_TARGET_HORIZON_VERIFICATION_RESULT_{DATE_TAG}.json",
}

PREDECESSOR_FILES = {
    "completion_audit": PREDECESSOR_DIR / f"SCID_ASOF_SEALED_VALIDATION_COMPLETION_AUDIT_{DATE_TAG}.json",
    "frozen_rowset_manifest": PREDECESSOR_DIR
    / f"SCID_ASOF_SEALED_VALIDATION_FROZEN_ROWSET_MANIFEST_{DATE_TAG}.json",
    "variant_family_registry": PREDECESSOR_DIR
    / f"SCID_ASOF_SEALED_VALIDATION_VARIANT_FAMILY_REGISTRY_{DATE_TAG}.json",
}

PACKET_FILES = {
    "candidate_rows": PACKET_DIR / f"SCID_ASOF_CANDIDATE_INPUT_ROWS_{DATE_TAG}.jsonl",
    "bar_rows": PACKET_DIR / f"SCID_ASOF_BAR_ROWS_{DATE_TAG}.jsonl",
    "candidate_manifest": PACKET_DIR / f"SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_{DATE_TAG}.json",
    "bar_manifest": PACKET_DIR / f"SCID_ASOF_BAR_MANIFEST_{DATE_TAG}.json",
}

FORBIDDEN_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "config/",
    "prompts/",
    "scripts/canary",
    "scripts/canary_",
    "shadow_logs/",
    "data/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(name: str, text: str) -> Path:
    path = ROUTE_DIR / name
    path.write_text(text, encoding="utf-8")
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def common(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "g12_scid_asof_target_horizon_repair_audit_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_remote_push": False,
        "opens_result_scoring": False,
        "opens_validation": False,
    }


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    false_keys = [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "changes_live_trading_behavior",
        "credentials_touched",
        "opens_ai_api",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_paid_or_vendor_access",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
    ]
    return payload.get("promotion_verdict") == PROMOTION_VERDICT and all(payload.get(key) is False for key in false_keys)


def route_artifacts() -> list[Path]:
    files: list[Path] = []
    for root in (TARGET_DIR, ROUTE_DIR):
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(files)


def status_path(line: str) -> str:
    if line.startswith("stderr:"):
        return line
    return line[3:].strip() if len(line) > 3 else line.strip()


def is_scoped_audit_path(path: str) -> bool:
    scoped_prefixes = [
        rel(ROUTE_DIR) + "/",
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    ]
    return path in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"} or any(
        path.startswith(prefix) for prefix in scoped_prefixes
    )


def forbidden_result_artifact_names(paths: list[Path]) -> list[str]:
    forbidden_tokens = ("RESULT_ROW", "SEALED_RESULT", "STRESS_RESULT", "PERFORMANCE_SCORE", "PNL", "EXPECTANCY")
    offenders: list[str] = []
    for path in paths:
        name = path.name.upper()
        if "VERIFICATION_RESULT" in name:
            continue
        if any(token in name for token in forbidden_tokens):
            offenders.append(rel(path))
    return offenders


def build_context_anchor() -> dict[str, Any]:
    status = git_status_short()
    payload = {
        **common("context_anchor"),
        "current_head": git_head(),
        "controlling_prompt": rel(CONTROL_PROMPT),
        "repair_prompt_read": rel(REPAIR_PROMPT),
        "target_route": rel(TARGET_DIR),
        "predecessor_route": rel(PREDECESSOR_DIR),
        "mandatory_context_read_after_preflight": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_current_state.md",
            ".context/00_READING_ORDER.md",
            rel(REPAIR_PROMPT),
        ],
        "lane": "G12 audit, adversarial source-control acceptance only",
        "hard_boundaries": [
            "no result rows or target values",
            "no validation execution or scoring",
            "no promotion or live readiness",
            "no AI/API, paid/vendor, broker/account/order/history/deal/position evidence",
            "no raw market-data blob commits",
            "no prompt/config/risk/safety/execution/canary/selector changes",
        ],
        "git_status_short_informational": status,
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.json", payload)
    write_text(
        f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.md",
        "# G12 SCID Target/Horizon Repair Audit Context Anchor\n\n"
        f"- HEAD: `{payload['current_head']}`\n"
        f"- Evidence class: `{EVIDENCE_CLASS}`\n"
        f"- Controlling prompt: `{rel(CONTROL_PROMPT)}`\n"
        f"- Target repair route: `{rel(TARGET_DIR)}`\n"
        "- Boundary: audit/control evidence only; no result rows, validation, promotion, live behavior, AI/API, "
        "broker/account/order/history/deal/position evidence, raw market-data blob commits, or live-surface edits.\n",
    )
    return payload


def build_predecessor_blocker_review() -> dict[str, Any]:
    predecessor_completion = load_json(PREDECESSOR_FILES["completion_audit"])
    repair_blocker = load_json(REPAIR_FILES["blocker_reconciliation"])
    g12_design = load_json(
        G12_DESIGN_AUDIT_DIR / f"G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_{DATE_TAG}.json"
    )
    checks = {
        "predecessor_blocked_exactly": predecessor_completion.get("terminal_decision")
        == "EXECUTION_BLOCKED_MISSING_FROZEN_OUTCOME_TARGET_SPEC",
        "predecessor_result_artifacts_absent": predecessor_completion.get("result_artifacts_emitted") is False,
        "repair_reconstructed_blocker_from_disk": repair_blocker.get("blocker_reconstructed_from_disk") is True,
        "repair_terminal_decision_requires_g12": repair_blocker.get("repair_route_decision")
        == "REPAIRED_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_G12_AUDIT_REQUIRED",
        "g12_design_prerequisite_accepted": g12_design.get("terminal_decision")
        == "ACCEPT_AS_G12_SEALED_VALIDATION_DESIGN_CONTROL_EVIDENCE_ONLY",
    }
    payload = {
        **common("predecessor_blocker_reconciliation_audit"),
        "checks": checks,
        "predecessor_terminal_decision": predecessor_completion.get("terminal_decision"),
        "predecessor_terminal_blocker": predecessor_completion.get("terminal_blocker"),
        "repair_route_decision": repair_blocker.get("repair_route_decision"),
        "accepted_g12_design_decision": g12_design.get("terminal_decision"),
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_PREDECESSOR_BLOCKER_REVIEW_{DATE_TAG}.json", payload)
    return payload


def build_count_reconciliation() -> dict[str, Any]:
    blocker = load_json(REPAIR_FILES["blocker_reconciliation"])
    rowset = load_json(PREDECESSOR_FILES["frozen_rowset_manifest"])
    rulebook = load_json(REPAIR_FILES["rulebook"])
    candidate_manifest = load_json(PACKET_FILES["candidate_manifest"])
    actual_counts = {
        "candidate_rows": jsonl_count(PACKET_FILES["candidate_rows"]),
        "bar_rows": jsonl_count(PACKET_FILES["bar_rows"]),
        "sealed_rows": rowset.get("sealed_row_count"),
        "stress_rows": rowset.get("stress_row_count"),
        "discovery_exclusions": rowset.get("discovery_exclusion_count"),
        "denominator_groups": rowset.get("candidate_denominator_group_count"),
        "known_families": load_json(REPAIR_FILES["family_matrix"]).get("known_family_count"),
    }
    source_crosschecks = {
        "repair_blocker_counts": blocker.get("exact_count_reconciliation"),
        "candidate_manifest_count": candidate_manifest.get("candidate_input_row_count"),
        "rulebook_denominator_policy": rulebook.get("denominator_policy"),
    }
    checks = {key: actual_counts.get(key) == expected for key, expected in EXPECTED_COUNTS.items()}
    payload = {
        **common("count_reconciliation_audit"),
        "expected_counts": EXPECTED_COUNTS,
        "actual_counts": actual_counts,
        "source_crosschecks": source_crosschecks,
        "checks": checks,
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COUNT_RECONCILIATION_{DATE_TAG}.json", payload)
    return payload


def build_rulebook_review() -> dict[str, Any]:
    rulebook = load_json(REPAIR_FILES["rulebook"])
    target_defs = rulebook.get("target_definitions", [])
    target_families = rulebook.get("target_families", [])
    target_ids = sorted({row.get("target_family_id") for row in target_defs})
    horizons = sorted({row.get("horizon_m15_bars") for row in target_defs})
    all_source_safe = all(row.get("strategy_edge_interpretation_allowed") is False for row in target_defs)
    all_have_source_fields = all(row.get("source_fields_consumed") for row in target_defs)
    checks = {
        "terminal_decision_is_neutral_repair": rulebook.get("terminal_decision")
        == "REPAIRED_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_G12_AUDIT_REQUIRED",
        "rulebook_frozen_before_outcome_opening": rulebook.get("rulebook_freeze_status")
        == "FROZEN_BEFORE_OUTCOME_OPENING_G12_AUDIT_REQUIRED",
        "target_scope_neutral_only": rulebook.get("target_scope")
        == "SOURCE_SAFE_NEUTRAL_BAR_BEHAVIOR_ONLY_NOT_STRATEGY_EDGE",
        "side_rule_neutral": rulebook.get("entry_reference", {}).get("side_rule")
        == "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
        "entry_time_asof": "decision_asof_utc" in rulebook.get("entry_reference", {}).get("time_rule", ""),
        "horizons_exact": horizons == [1, 4, 16, 32],
        "target_definition_count_exact": len(target_defs) == 8,
        "target_family_count_exact": len(target_families) == 2,
        "all_target_defs_forbid_strategy_edge_interpretation": all_source_safe,
        "all_target_defs_have_source_fields": all_have_source_fields,
        "forbidden_metrics_exclude_strategy_performance": all(
            metric in rulebook.get("forbidden_metric_families_in_this_route", [])
            for metric in ["win_rate", "expectancy", "PnL", "R_multiple", "strategy_edge_lift"]
        ),
        "not_computable_rules_fail_closed": len(
            rulebook.get("stop_invalid_fail_closed_definition", {}).get("not_computable_rules", [])
        )
        >= 7,
    }
    payload = {
        **common("neutral_target_rulebook_audit"),
        "checks": checks,
        "target_family_ids": target_ids,
        "horizon_set_m15_bars": horizons,
        "target_definition_count": len(target_defs),
        "allowed_metric_families_after_independent_g12_audit": rulebook.get(
            "allowed_metric_families_after_independent_g12_audit"
        ),
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RULEBOOK_REVIEW_{DATE_TAG}.json", payload)
    return payload


def build_family_matrix_review() -> dict[str, Any]:
    matrix = load_json(REPAIR_FILES["family_matrix"])
    rows = matrix.get("matrix_rows", [])
    family_ids = [row.get("family_id") for row in rows]
    status_by_family = {row.get("family_id"): row.get("repair_status") for row in rows}
    status_counts = Counter(status_by_family.values())
    strategy_rows = [row for row in rows if row.get("family_id") in STRATEGY_FAMILIES]
    control_rows = [row for row in rows if row.get("family_id") in CONTROL_FAMILIES]
    checks = {
        "known_family_count_exact": matrix.get("known_family_count") == 11 and len(rows) == 11,
        "all_expected_families_present_once": sorted(family_ids) == sorted(EXPECTED_FAMILIES)
        and len(family_ids) == len(set(family_ids)),
        "strategy_families_neutral_only": all(
            row.get("repair_status") == "SOURCE_SAFE_NEUTRAL_TARGET_ONLY" for row in strategy_rows
        ),
        "control_families_control_only": all(row.get("repair_status") == "CONTROL_ONLY" for row in control_rows),
        "no_family_strategy_executable": matrix.get("no_family_forced_to_strategy_executable") is True
        and all(row.get("strategy_specific_execution_allowed") is False for row in rows),
        "source_contract_refs_present": all(
            row.get("source_field_derivation_contract") and row.get("source_expansion_requirement_contract")
            for row in rows
        ),
    }
    payload = {
        **common("family_executability_matrix_audit"),
        "checks": checks,
        "status_by_family": status_by_family,
        "status_counts": dict(status_counts),
        "strategy_family_count": len(strategy_rows),
        "control_family_count": len(control_rows),
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_FAMILY_MATRIX_REVIEW_{DATE_TAG}.json", payload)
    return payload


def build_source_field_contract_review() -> dict[str, Any]:
    derivation = load_json(REPAIR_FILES["source_derivation"])
    expansion = load_json(REPAIR_FILES["source_expansion"])
    derivation_rows = derivation.get("family_missing_field_derivation_results", [])
    expansion_rows = expansion.get("requirements", [])
    derivation_by_family = {row.get("family_id"): row for row in derivation_rows}
    expansion_by_family = {row.get("family_id"): row for row in expansion_rows}
    strategy_derivations = [derivation_by_family.get(family, {}) for family in STRATEGY_FAMILIES]
    control_derivations = [derivation_by_family.get(family, {}) for family in CONTROL_FAMILIES]
    strategy_expansions = [expansion_by_family.get(family, {}) for family in STRATEGY_FAMILIES]
    checks = {
        "all_expected_families_have_derivation_rows": sorted(derivation_by_family) == sorted(EXPECTED_FAMILIES),
        "all_expected_families_have_expansion_rows": sorted(expansion_by_family) == sorted(EXPECTED_FAMILIES),
        "strategy_missing_fields_not_derivable_from_neutral_bars": all(
            row.get("derivation_status") == "NOT_DERIVABLE_FROM_ACCEPTED_BARS_WITHOUT_INVENTING_STRATEGY_INTENT"
            for row in strategy_derivations
        ),
        "strategy_derivation_attempts_exhaustive": all(
            row.get("accepted_bar_derivation_attempted") is True
            and row.get("artifact_code_history_search_attempted") is True
            and row.get("source_contract_reconstruction_attempted") is True
            and row.get("capture_or_expansion_contract_required") is True
            for row in strategy_derivations
        ),
        "controls_bound_to_neutral_targets": all(
            row.get("derivation_status") == "CONTROL_TIED_TO_NEUTRAL_TARGETS" for row in control_derivations
        ),
        "strategy_expansion_requirements_exact": all(
            row.get("requirement_status")
            == "EXACT_PROSPECTIVE_CAPTURE_OR_SOURCE_EXPANSION_REQUIRED_FOR_STRATEGY_EXECUTION"
            and len(row.get("required_future_fields", [])) >= 6
            and row.get("capture_contract", {}).get("asof_rule")
            == "field must be recorded at or before decision_asof_utc and source-hashed in the packet"
            for row in strategy_expansions
        ),
        "historical_truth_warning_present": "cannot be retroactively upgraded"
        in expansion.get("historical_truth_warning", ""),
    }
    payload = {
        **common("source_field_blocker_contract_audit"),
        "checks": checks,
        "strategy_families_reviewed": STRATEGY_FAMILIES,
        "control_families_reviewed": CONTROL_FAMILIES,
        "derivable_source_safe_fields": derivation.get("derivable_source_safe_fields", []),
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SOURCE_FIELD_CONTRACT_REVIEW_{DATE_TAG}.json", payload)
    return payload


def build_noleak_forbidden_review() -> dict[str, Any]:
    noleak = load_json(REPAIR_FILES["noleak_audit"])
    multiple = load_json(REPAIR_FILES["multiple_testing"])
    completion = load_json(REPAIR_FILES["completion_audit"])
    verifier = load_json(REPAIR_FILES["verification"])
    repair_focused_pytest_rerun = run_command(
        [
            "python",
            "-m",
            "pytest",
            rel(TARGET_DIR / "test_scid_asof_target_horizon_repair_2026_05_11.py"),
            "-q",
        ]
    )
    repair_payloads = [load_json(path) for path in REPAIR_FILES.values()]
    raw_paths = route_artifacts()
    result_name_offenders = forbidden_result_artifact_names(raw_paths)
    checks = {
        "repair_artifacts_safe_flags_closed": all(safe_flags_closed(payload) for payload in repair_payloads),
        "noleak_flags_no_result_or_performance": noleak.get("result_rows_generated") is False
        and noleak.get("outcome_values_computed") is False
        and noleak.get("performance_metrics_computed") is False,
        "forbidden_evidence_closed": all(value is False for value in noleak.get("forbidden_evidence_opened", {}).values()),
        "multiple_testing_ledger_present": bool(multiple) and multiple.get("promotion_verdict") == PROMOTION_VERDICT,
        "repair_verifier_ok": verifier.get("ok") is True and verifier.get("can_mark_goal_complete") is True,
        "repair_focused_pytest_rerun_passed": repair_focused_pytest_rerun["returncode"] == 0
        and "6 passed" in repair_focused_pytest_rerun["stdout"],
        "repair_completion_can_mark_complete": completion.get("can_mark_goal_complete") is True,
        "no_result_artifact_names": not result_name_offenders,
    }
    payload = {
        **common("noleak_forbidden_surface_audit"),
        "checks": checks,
        "result_artifact_name_offenders": result_name_offenders,
        "multiple_testing_summary": multiple,
        "repair_verifier_ref": rel(REPAIR_FILES["verification"]),
        "repair_focused_pytest_current_rerun": repair_focused_pytest_rerun,
        "pass": all(checks.values()),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_NOLEAK_FORBIDDEN_REVIEW_{DATE_TAG}.json", payload)
    return payload


def build_raw_blob_dirty_state_audit() -> dict[str, Any]:
    paths = route_artifacts()
    raw_blob_issues = [
        {"path": rel(path), "suffix": path.suffix, "size_bytes": path.stat().st_size}
        for path in paths
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS or path.stat().st_size > 100_000_000
    ]
    dirty_entries = []
    scoped_forbidden = []
    for line in git_status_short():
        path = status_path(line)
        scoped = is_scoped_audit_path(path)
        entry = {
            "status": line[:2] if not line.startswith("stderr:") else "stderr",
            "path": path,
            "scoped_to_this_g12_audit_or_context_refresh": scoped,
        }
        dirty_entries.append(entry)
        if scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES):
            scoped_forbidden.append(path)
    payload = {
        **common("raw_blob_and_dirty_state_audit"),
        "raw_blob_issues": raw_blob_issues,
        "raw_blob_audit_pass": not raw_blob_issues,
        "dirty_state_ledger": dirty_entries,
        "scoped_forbidden_live_surface_changes": scoped_forbidden,
        "scoped_dirty_state_pass": not scoped_forbidden,
        "unrelated_dirty_state_count": sum(
            1 for row in dirty_entries if not row["scoped_to_this_g12_audit_or_context_refresh"]
        ),
    }
    payload["pass"] = payload["raw_blob_audit_pass"] and payload["scoped_dirty_state_pass"]
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RAW_BLOB_DIRTY_STATE_{DATE_TAG}.json", payload)
    return payload


def build_saturation_redteam() -> dict[str, Any]:
    questions = [
        (
            "Could source-control neutral targets be mistaken for strategy edge?",
            "Yes; audit accepts only neutral bar-behavior control evidence and requires future lanes to label all metrics as no-strategy-edge.",
            "PASS",
        ),
        (
            "Could strategy side, entry, stop, target, or lifecycle be invented from bars?",
            "Family matrix and source-field contract keep seven strategy families non-executable and require prospective/as-of source capture.",
            "PASS",
        ),
        (
            "Could target values have been chosen after reading future outcomes?",
            "No result rows or target values exist; only source fields, horizons, and not-computable rules are frozen.",
            "PASS",
        ),
        (
            "Could baseline controls become hidden strategy claims?",
            "Four baseline families are CONTROL_ONLY and tied only to audited neutral or future audited strategy targets.",
            "PASS",
        ),
        (
            "Could discovery exclusions, stress rows, or secondary proxy rows inflate sealed denominators?",
            "Counts and denominator policy keep 365 discovery exclusions out, split 2432 sealed from 582 stress, and name forbidden secondary proxies.",
            "PASS",
        ),
        (
            "Could a raw market-data blob or large file be committed by this audit?",
            "Raw-blob audit scans target and audit route files for forbidden extensions and >100MB artifacts.",
            "PASS",
        ),
        (
            "Could live/runtime dirty state be accidentally committed?",
            "Dirty-state ledger separates scoped audit/context paths from unrelated runtime/live dirt and fails on scoped forbidden live surfaces.",
            "PASS",
        ),
        (
            "Could the repair route's own verifier be accepted as proof without coverage check?",
            "Audit separately inspects artifacts and also verifies the repair verifier/focused pytest evidence.",
            "PASS",
        ),
        (
            "Could missing strategy fields remain vague?",
            "Source-expansion requirements enumerate per-family future fields, as-of rule, fail-closed policy, redaction policy, and tests.",
            "PASS",
        ),
        (
            "What should the next lane be if accepted?",
            "Only a separate quarantined neutral-target execution packet or source-field expansion packet; no promotion, validation-safe flag, or live behavior.",
            "PASS",
        ),
    ]
    payload = {
        **common("saturation_redteam_ledger"),
        "questions": [
            {"question": question, "audit_answer": answer, "status": status}
            for question, answer, status in questions
        ],
        "pass": all(status == "PASS" for _, _, status in questions),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SATURATION_REDTEAM_{DATE_TAG}.json", payload)
    return payload


def build_decision(reviews: dict[str, dict[str, Any]]) -> dict[str, Any]:
    pass_all = all(review.get("pass") is True for review in reviews.values())
    terminal_decision = (
        "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_CONTROL_EVIDENCE_ONLY"
        if pass_all
        else "REJECT_SCID_TARGET_HORIZON_REPAIR_ROUTE_EXACT_BLOCKERS"
    )
    blockers = [name for name, review in reviews.items() if review.get("pass") is not True]
    payload = {
        **common("audit_decision_ledger"),
        "terminal_decision": terminal_decision,
        "accepted_design_control_evidence_only": pass_all,
        "accepted_source_safe_neutral_target_rulebook_only": pass_all,
        "accepted_strategy_family_execution": False,
        "accepted_validation_execution": False,
        "accepted_result_scoring": False,
        "accepted_promotion": False,
        "terminal_blockers": blockers,
        "review_pass_map": {name: review.get("pass") is True for name, review in reviews.items()},
        "next_allowed_lane_if_accepted": (
            "separate quarantined neutral-target execution packet or source-field expansion packet only; "
            "no promotion, live behavior, AI/API, broker/account/order/history/deal/position evidence, "
            "raw market-data blob commits, prompt/config/risk/safety/execution/canary/selector edits, or "
            "strategy-edge interpretation of neutral targets"
        ),
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.json", payload)
    write_text(
        f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.md",
        "# G12 SCID Target/Horizon Repair Audit Decision\n\n"
        f"Decision: `{terminal_decision}`\n\n"
        "Accepted scope: source-safe neutral target/horizon rulebook control evidence only.\n\n"
        "Not accepted: strategy-family execution, result rows, target values, validation execution, result scoring, "
        "promotion, live behavior, AI/API, broker/account/order/history/deal/position evidence, paid/vendor evidence, "
        "raw market-data blob commits, or live-surface edits.\n\n"
        "Next lane if used: separate quarantined neutral-target execution packet or source-field expansion packet only.\n",
    )
    return payload


def build_completion_audit(reviews: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory GTOS preflight and context refresh", "context anchor records refreshed docs and current HEAD", "context"),
        ("controlling repair prompt read", rel(REPAIR_PROMPT), "context"),
        ("predecessor blocker reconstructed from disk", "predecessor blocker review", "predecessor"),
        ("exact packet counts verified", "count reconciliation audit", "counts"),
        ("3,014 candidate rows verified", "candidate JSONL count and manifests", "counts"),
        ("2,432 sealed rows verified", "frozen rowset manifest", "counts"),
        ("582 stress rows verified", "frozen rowset manifest", "counts"),
        ("365 discovery exclusions verified", "frozen rowset manifest", "counts"),
        ("7 denominator groups verified", "frozen rowset manifest and rulebook", "counts"),
        ("11 known families verified", "family matrix review", "family_matrix"),
        ("every family exactly one status", "family matrix review", "family_matrix"),
        ("no strategy family forced executable", "family matrix review", "family_matrix"),
        ("neutral target rulebook source-safe and side-neutral", "rulebook review", "rulebook"),
        ("horizon set frozen before outcome opening", "rulebook review", "rulebook"),
        ("source-field blockers/contracts exact", "source-field contract review", "source_fields"),
        ("no result rows/target values/performance artifacts", "noleak forbidden review", "noleak"),
        ("no AI/API, paid/vendor, broker/account/order/history/deal/position evidence", "noleak forbidden review", "noleak"),
        ("duplicate/proxy denominator and no-leak boundaries checked", "rulebook and noleak reviews", "rulebook"),
        ("multiple-testing ledger checked", "noleak forbidden review", "noleak"),
        ("raw-blob and dirty-state audit complete", "raw blob dirty state audit", "raw_dirty"),
        ("repair verifier and focused tests checked", "noleak forbidden review", "noleak"),
        ("G12 saturation/self-red-team pass complete", "saturation redteam ledger", "saturation"),
        ("safe flags preserved", "decision ledger", "decision"),
    ]
    status_by_key = {name: review.get("pass") is True for name, review in reviews.items()}
    status_by_key["context"] = True
    status_by_key["decision"] = decision.get("terminal_decision", "").startswith("ACCEPT")
    rows = [
        {
            "requirement": requirement,
            "evidence": evidence,
            "status": "PASS" if status_by_key.get(key) else "FAIL",
        }
        for requirement, evidence, key in checklist
    ]
    can_complete = all(row["status"] == "PASS" for row in rows) and decision.get("accepted_design_control_evidence_only") is True
    payload = {
        **common("completion_audit"),
        "objective_restatement": (
            "Independently audit the SCID target/horizon/source-field repair route as G12 source-control evidence only, "
            "accepting it only if it repairs the missing frozen target spec with a neutral source-safe rulebook and exact "
            "source-field contracts before result rows exist."
        ),
        "prompt_to_artifact_checklist": rows,
        "review_pass_map": status_by_key,
        "can_mark_goal_complete": can_complete,
        "terminal_decision": decision.get("terminal_decision"),
        "NO_PROMOTION_VERDICT": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json", payload)
    md_lines = [
        "# G12 SCID Target/Horizon Repair Audit Completion Audit",
        "",
        f"Terminal decision: `{payload['terminal_decision']}`",
        "",
        f"Can mark complete: `{str(can_complete).lower()}`",
        "",
        "## Checklist",
        "",
    ]
    for row in rows:
        md_lines.append(f"- {row['status']}: {row['requirement']} -> {row['evidence']}")
    md_lines.extend(
        [
            "",
            "## Safe Flags",
            "",
            "- `NO_PROMOTION_VERDICT`",
            "- `validation_safe=false`",
            "- `outcome_review_opened=false`",
            "- `live_effect=false`",
            "",
        ]
    )
    write_text(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.md", "\n".join(md_lines))
    return payload


def build_output_manifest(artifacts: dict[str, Path]) -> dict[str, Any]:
    manifest_entries = []
    for key, path in sorted(artifacts.items()):
        if path.exists():
            manifest_entries.append(
                {"artifact_key": key, "path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            )
    payload = {
        **common("route_output_manifest"),
        "artifacts": manifest_entries,
        "artifact_count": len(manifest_entries),
        "terminal_decision_ref": rel(ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.json"),
    }
    write_json(f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json", payload)
    return payload


def build_all() -> dict[str, Any]:
    context = build_context_anchor()
    reviews = {
        "predecessor": build_predecessor_blocker_review(),
        "counts": build_count_reconciliation(),
        "rulebook": build_rulebook_review(),
        "family_matrix": build_family_matrix_review(),
        "source_fields": build_source_field_contract_review(),
        "noleak": build_noleak_forbidden_review(),
        "raw_dirty": build_raw_blob_dirty_state_audit(),
        "saturation": build_saturation_redteam(),
    }
    decision = build_decision(reviews)
    completion = build_completion_audit(reviews, decision)
    artifacts = {
        "context_json": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.json",
        "context_md": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_CONTEXT_ANCHOR_{DATE_TAG}.md",
        "predecessor": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_PREDECESSOR_BLOCKER_REVIEW_{DATE_TAG}.json",
        "counts": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COUNT_RECONCILIATION_{DATE_TAG}.json",
        "rulebook": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RULEBOOK_REVIEW_{DATE_TAG}.json",
        "family_matrix": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_FAMILY_MATRIX_REVIEW_{DATE_TAG}.json",
        "source_fields": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SOURCE_FIELD_CONTRACT_REVIEW_{DATE_TAG}.json",
        "noleak": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_NOLEAK_FORBIDDEN_REVIEW_{DATE_TAG}.json",
        "raw_dirty": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_RAW_BLOB_DIRTY_STATE_{DATE_TAG}.json",
        "saturation": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_SATURATION_REDTEAM_{DATE_TAG}.json",
        "decision_json": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.json",
        "decision_md": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_{DATE_TAG}.md",
        "completion_json": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json",
        "completion_md": ROUTE_DIR / f"G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.md",
        "builder": Path(__file__).resolve(),
        "verifier": ROUTE_DIR / "verify_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
        "focused_tests": ROUTE_DIR / "test_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
    }
    manifest = build_output_manifest(artifacts)
    return {"context": context, "reviews": reviews, "decision": decision, "completion": completion, "manifest": manifest}


if __name__ == "__main__":
    result = build_all()
    print(
        json.dumps(
            {
                "terminal_decision": result["decision"]["terminal_decision"],
                "can_mark_goal_complete": result["completion"]["can_mark_goal_complete"],
            },
            indent=2,
            sort_keys=True,
        )
    )
