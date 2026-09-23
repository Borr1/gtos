"""Verifier for the G0 FPB sealed partition and baseline packet."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
PREFIX = "G0_FPB_SEALED_PARTITION"
ROUTE_ID = "G0_FPB_SEALED_PARTITION_AND_ADVERSARIAL_BASELINE_PACKET"
NEXT_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_GOAL_PROMPT_2026-05-11.md"
)
VERIFICATION_JSON = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"

EXPECTED_ARTIFACT_KEYS = {
    "CONTEXT_ANCHOR",
    "EVIDENCE_RECONCILIATION_LEDGER",
    "PARTITION_LEDGER",
    "DISCOVERY_EXPOSURE_LEDGER",
    "PURGE_EMBARGO_DUPLICATE_POLICY",
    "ADVERSARIAL_BASELINE_PACKET",
    "CONCENTRATION_AND_STRESS_REQUIREMENTS",
    "AMBIGUITY_UNRESOLVED_POLICY",
    "SOURCE_ASOF_NOLEAK_CONTRACT",
    "FALSIFICATION_CRITERIA",
    "HARDENING_COVERAGE_LEDGER",
    "NO_LAZY_BLOCKER_LEDGER",
    "SEARCHED_ROOT_SOURCE_SATURATION_LEDGER",
    "HOSTILE_EDGE_REVIEW_LEDGER",
    "NEGATIVE_FAILURE_ANATOMY_LEDGER",
    "SELECTION_BIAS_MULTIPLE_TESTING_CARRY_FORWARD",
    "PROCESS_LIMITATION_COUNTERMEASURES",
    "SATURATION_SELF_REDTEAM",
    "NEXT_PROMPT_PACK",
    "NOLEAK_DIRTY_STATE_AUDIT",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_mt5_order_account_history_behavior",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]

FORBIDDEN_METRIC_KEYS = {
    "actual_r",
    "broker_actual_r",
    "pnl",
    "win_rate",
    "expectancy",
    "mean_r",
    "median_r",
    "total_r",
    "performance_score",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(key: str, ext: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{key}_{DATE_TAG}.{ext}"


def walk_keys(obj: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(str(key))
            keys.update(walk_keys(value))
    elif isinstance(obj, list):
        for value in obj:
            keys.update(walk_keys(value))
    return keys


def verify() -> dict[str, Any]:
    failures: list[str] = []
    parsed: dict[str, dict[str, Any]] = {}

    for key in sorted(EXPECTED_ARTIFACT_KEYS):
        for ext in ("json", "md"):
            path = artifact_path(key, ext)
            if not path.exists():
                failures.append(f"missing artifact: {path.name}")
        json_path = artifact_path(key, "json")
        if json_path.exists():
            payload = load_json(json_path)
            parsed[key] = payload
            if payload.get("route_id") != ROUTE_ID:
                failures.append(f"{json_path.name}: route_id mismatch")
            if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                failures.append(f"{json_path.name}: promotion verdict mismatch")
            for flag in SAFE_FALSE_FLAGS:
                if payload.get(flag) is not False:
                    failures.append(f"{json_path.name}: {flag} is not false")
            forbidden = FORBIDDEN_METRIC_KEYS.intersection(walk_keys(payload))
            if forbidden:
                failures.append(f"{json_path.name}: forbidden metric keys present {sorted(forbidden)}")

    evidence = parsed.get("EVIDENCE_RECONCILIATION_LEDGER", {})
    if evidence.get("all_counts_preserved") is not True:
        failures.append("evidence reconciliation did not preserve counts")
    checks = {row.get("check_id"): row for row in evidence.get("count_checks", [])}
    expected = {
        "raw_candidate_attempts": 13_540_033,
        "duplicate_candidate_keys": 687_275,
        "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
        "path_label_row_count": 12_852_758,
        "opened_family_count": 11,
        "baseline_control_family_count": 4,
        "selected_source_count": 365,
        "excluded_source_slice_count": 3135,
    }
    for key, value in expected.items():
        row = checks.get(key)
        if not row or row.get("expected") != value or row.get("actual") != value or row.get("status") != "PASS":
            failures.append(f"count check failed: {key}")

    partition = parsed.get("PARTITION_LEDGER", {})
    sealed = partition.get("sealed_historical_validation_pool", {})
    if sealed.get("current_source_rows") != 0 or sealed.get("current_candidate_rows") != 0:
        failures.append("current sealed validation pool must be zero")
    if partition.get("validation_execution_prompt_emitted") is not False:
        failures.append("validation execution prompt must not be emitted")
    if partition.get("source_control_unblocker_prompt_emitted") is not True:
        failures.append("source-control unblocker prompt must be emitted")
    discovery = partition.get("discovery_pool", {})
    if discovery.get("source_rows") != 365:
        failures.append("discovery pool selected source rows mismatch")
    if discovery.get("unique_path_label_rows") != 12_852_758:
        failures.append("discovery pool unique row count mismatch")

    baseline = parsed.get("ADVERSARIAL_BASELINE_PACKET", {})
    if baseline.get("all_four_baselines_frozen") is not True:
        failures.append("all four baselines are not frozen")
    if {row.get("family_id") for row in baseline.get("baseline_controls", [])} != {
        "baseline_random_session_control",
        "baseline_shifted_entry_control",
        "baseline_momentum_continuation",
        "baseline_mean_reversion",
    }:
        failures.append("baseline control set mismatch")

    concentration = parsed.get("CONCENTRATION_AND_STRESS_REQUIREMENTS", {})
    caps = concentration.get("caps", {})
    for cap in (
        "single_source_hash_max_share",
        "single_symbol_max_share",
        "single_timeframe_max_share",
        "single_session_kz_max_share",
        "effective_n_family_floor",
        "effective_n_combined_floor",
    ):
        if cap not in caps:
            failures.append(f"missing concentration cap: {cap}")
    if len(concentration.get("required_stress_tests", [])) < 8:
        failures.append("not enough required stress tests")

    ambiguity = parsed.get("AMBIGUITY_UNRESOLVED_POLICY", {})
    if set(ambiguity.get("fail_closed_labels_before_validation", [])) != {
        "SAME_BAR_CONTEXT_AMBIGUOUS",
        "UNRESOLVED_BY_WINDOW",
        "UNRESOLVED_AT_SOURCE_END",
    }:
        failures.append("ambiguity fail-closed label set mismatch")

    source_contract = parsed.get("SOURCE_ASOF_NOLEAK_CONTRACT", {})
    if source_contract.get("field_count", 0) < 20:
        failures.append("source contract has fewer than 20 fields")
    for field in source_contract.get("fields", []):
        if not field.get("exact_requirement") or field.get("no_leak_gate") != "PASS_REQUIRED_BEFORE_VALIDATION":
            failures.append(f"source contract field incomplete: {field.get('field_name')}")

    no_lazy = parsed.get("NO_LAZY_BLOCKER_LEDGER", {})
    if no_lazy.get("remaining_vague_blockers"):
        failures.append("no-lazy ledger has vague blockers")
    if no_lazy.get("remaining_same_evidence_class_gaps"):
        failures.append("no-lazy ledger has same-evidence-class gaps")

    source_saturation = parsed.get("SEARCHED_ROOT_SOURCE_SATURATION_LEDGER", {})
    if not source_saturation.get("input_hashes"):
        failures.append("source saturation lacks input hashes")
    if source_saturation.get("broker_or_account_sources_read") is not False:
        failures.append("source saturation read broker/account sources")
    searched_roots = source_saturation.get("searched_roots", [])
    if len(searched_roots) < 8:
        failures.append("source saturation searched too few roots")

    hostile = parsed.get("HOSTILE_EDGE_REVIEW_LEDGER", {})
    if set(hostile.get("selected_family_reviews", {}).keys()) != {
        "adjacent_range_compression_breakout",
        "ob_retest",
        "opening_drive_no_fill_lifecycle",
    }:
        failures.append("hostile review selected family set mismatch")
    if "fvg_fill" not in hostile.get("deferred_or_excluded_family_reviews", {}):
        failures.append("hostile review lacks deferred family coverage")

    saturation = parsed.get("SATURATION_SELF_REDTEAM", {})
    if len(saturation.get("questions_answered", [])) < 10:
        failures.append("saturation pass answered too few questions")
    if saturation.get("remaining_same_evidence_class_gaps"):
        failures.append("saturation pass has remaining gaps")

    next_pack = parsed.get("NEXT_PROMPT_PACK", {})
    if next_pack.get("next_prompt_type") != "SOURCE_CONTROL_UNBLOCKER_NOT_VALIDATION":
        failures.append("next prompt is not source-control unblocker")
    if next_pack.get("validation_execution_prompt_emitted") is not False:
        failures.append("next prompt pack emitted validation execution prompt")
    if not NEXT_PROMPT.exists():
        failures.append("next source-control prompt missing")
    else:
        text = NEXT_PROMPT.read_text(encoding="utf-8")
        required_text = [
            "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Forbidden: validation execution",
        ]
        for needle in required_text:
            if needle not in text:
                failures.append(f"next prompt missing required text: {needle}")

    noleak = parsed.get("NOLEAK_DIRTY_STATE_AUDIT", {})
    if noleak.get("passes") is not True:
        failures.append("no-leak dirty-state audit did not pass")
    if noleak.get("forbidden_live_surface_dirty_paths"):
        failures.append("forbidden live-surface dirty paths present")
    if noleak.get("broker_account_order_history_read") is not False:
        failures.append("broker/account/order/history read flag is not false")

    completion = parsed.get("COMPLETION_AUDIT", {})
    checklist = completion.get("prompt_to_artifact_checklist", [])
    if not checklist:
        failures.append("completion checklist is empty")
    non_pass = [row for row in checklist if row.get("status") != "PASS"]
    if non_pass:
        failures.append(f"completion checklist has non-PASS rows: {non_pass}")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard not satisfied")
    if completion.get("current_sealed_historical_validation_source_rows") != 0:
        failures.append("completion audit must report zero current sealed rows")

    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path.name} syntax parse failed: {exc}")

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "artifact_json_count": len(parsed),
        "current_sealed_historical_validation_source_rows": sealed.get("current_source_rows"),
        "source_control_unblocker_prompt": str(NEXT_PROMPT.relative_to(ROOT)).replace("\\", "/"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_mt5_order_account_history_behavior": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }
    VERIFICATION_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
