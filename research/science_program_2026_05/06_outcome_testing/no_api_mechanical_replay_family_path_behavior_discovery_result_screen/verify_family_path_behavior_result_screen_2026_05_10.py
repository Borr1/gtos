#!/usr/bin/env python3
"""Verify the no-API family path-behavior discovery result screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


ROUTE_ID = "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN"
SCHEMA_VERSION = "family_path_behavior_discovery_result_screen_v1"
DATE = "2026-05-10"
PREFIX = "FPB"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
G12_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md"
)

EXPECTED_COUNTS = {
    "raw_candidate_attempts": 13_540_033,
    "duplicate_candidate_keys": 687_275,
    "unique_nonduplicate_candidate_path_label_denominator": 12_852_758,
    "path_label_row_count": 12_852_758,
}

OPENED_FAMILIES = {
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout",
}

BASELINE_CONTROLS = {
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
}

LABEL_VOCABULARY = {
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END",
}

FORBIDDEN_TRUE_FLAGS = [
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
    "opens_remote_push",
    "opens_registry_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]

FORBIDDEN_DATA_KEYS = {
    "pnl",
    "actual_r",
    "broker_actual_r",
    "win_rate",
    "expectancy",
    "account_history",
    "deal",
    "position",
    "ticket",
    "order_id",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_path(route_dir: Path, name: str) -> Path:
    return route_dir / f"{PREFIX}_{name}_{DATE}.json"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def flag_failures(payload: Mapping[str, Any], label: str) -> list[str]:
    failures = []
    for flag in FORBIDDEN_TRUE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{label}: {flag} is not false")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append(f"{label}: promotion_verdict is not NO_PROMOTION_VERDICT")
    return failures


def forbidden_key_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_DATA_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(forbidden_key_hits(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(forbidden_key_hits(child, f"{path}[{index}]"))
    return hits


def verify(route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    failures: list[str] = []
    required = {
        "context": json_path(route_dir, "CONTEXT_ANCHOR"),
        "denominator": json_path(route_dir, "DENOMINATOR_DUPLICATE_POLICY"),
        "lfs": json_path(route_dir, "LFS_MATERIALIZATION_AUDIT"),
        "matrix": json_path(route_dir, "FULL_POPULATION_AGGREGATE_MATRIX"),
        "compact": json_path(route_dir, "COMPACT_CAP_DIAGNOSTICS"),
        "baseline": json_path(route_dir, "BASELINE_CONTROL_LEDGER"),
        "selection": json_path(route_dir, "SELECTION_BIAS_MULTIPLE_TESTING_LEDGER"),
        "failure": json_path(route_dir, "FAILURE_ANATOMY_NEXT_HYPOTHESIS_LEDGER"),
        "instruction": json_path(route_dir, "CONTEXT_INSTRUCTION_COVERAGE_LEDGER"),
        "noleak": json_path(route_dir, "NOLEAK_DIRTY_STATE_AUDIT"),
        "saturation": json_path(route_dir, "SATURATION_SELF_REDTEAM_PASS"),
        "manifest": json_path(route_dir, "OUTPUT_MANIFEST"),
        "completion": json_path(route_dir, "COMPLETION_AUDIT"),
    }
    payloads: dict[str, dict[str, Any]] = {}
    for label, path in required.items():
        if not path.exists():
            failures.append(f"missing required artifact: {display_path(path)}")
            continue
        payloads[label] = read_json(path)
        failures.extend(flag_failures(payloads[label], label))
        key_hits = forbidden_key_hits(payloads[label])
        if key_hits:
            failures.append(f"{label}: forbidden data keys found {key_hits[:20]}")

    matrix = payloads.get("matrix", {})
    denominator = payloads.get("denominator", {})
    lfs = payloads.get("lfs", {})
    baseline = payloads.get("baseline", {})
    compact = payloads.get("compact", {})
    instruction = payloads.get("instruction", {})
    noleak = payloads.get("noleak", {})
    saturation = payloads.get("saturation", {})
    completion = payloads.get("completion", {})

    for key, expected in EXPECTED_COUNTS.items():
        if matrix.get(key) != expected:
            failures.append(f"matrix {key} expected {expected}, got {matrix.get(key)}")
    if denominator.get("counts_match_accepted_headline") is not True:
        failures.append("denominator policy does not match accepted headline counts")
    if matrix.get("aggregation_mode") != "full_stream_recomputed_from_accepted_source_rows_aggregate_only":
        failures.append("matrix aggregation mode is not full-stream aggregate-only")
    if matrix.get("compact_sample_used_for_decisive_ranking") is not False:
        failures.append("matrix allows compact sample decisive ranking")
    if compact.get("decisive_ranking_uses_compact_sample") is not False:
        failures.append("compact diagnostics allow compact decisive ranking")
    if compact.get("full_stream_aggregate_used_for_route_priority") is not True:
        failures.append("compact diagnostics do not confirm full-stream route priority")
    if set(matrix.get("opened_families") or []) != OPENED_FAMILIES:
        failures.append("opened family set does not match required 11 families")
    if set(matrix.get("baseline_control_families") or []) != BASELINE_CONTROLS:
        failures.append("baseline control family set does not match required four controls")
    if set(matrix.get("label_vocabulary") or []) != LABEL_VOCABULARY:
        failures.append("label vocabulary does not match exact required set")
    if baseline.get("all_four_baseline_controls_included") is not True:
        failures.append("baseline ledger does not include all four baseline controls")
    if lfs.get("all_lfs_checks_pass") is not True:
        failures.append("LFS/materialization audit did not pass")
    if instruction.get("all_requirements_covered") is not True:
        failures.append("instruction coverage ledger is not complete")
    if noleak.get("passes") is not True:
        failures.append("no-leak/dirty-state audit did not pass")
    if noleak.get("raw_jsonl_rows_written_by_this_route") is not False:
        failures.append("route wrote raw JSONL rows")
    if saturation.get("terminal_status") != "SATURATION_PASS_COMPLETE":
        failures.append("saturation pass did not complete")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion audit did not satisfy completion standard")
    if completion.get("can_mark_goal_complete") is not True:
        failures.append("completion audit does not allow goal completion")
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append("completion audit has missing/incomplete/weak requirements")
    if not G12_PROMPT.exists():
        failures.append(f"mandatory post-result G12 prompt missing: {display_path(G12_PROMPT)}")
    else:
        g12_text = G12_PROMPT.read_text(encoding="utf-8", errors="replace")
        for required_phrase in [
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER",
        ]:
            if required_phrase not in g12_text:
                failures.append(f"G12 prompt missing required phrase: {required_phrase}")

    for path in route_dir.glob("*"):
        if path.is_file() and path.stat().st_size > 100_000_000:
            failures.append(f"new route file exceeds 100MB: {display_path(path)}")

    result = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "verification_result",
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
        "duplicate_candidate_keys": matrix.get("duplicate_candidate_keys"),
        "unique_nonduplicate_denominator": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
        "opened_family_count": matrix.get("opened_family_count"),
        "baseline_control_family_count": len(matrix.get("baseline_control_families") or []),
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
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }
    output_path = route_dir / f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify(args.route_dir)
    if not args.quiet or not result["ok"]:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
