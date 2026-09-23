#!/usr/bin/env python3
"""Build action-result rows from branch-local observable execution decisions."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_observable_action_results import (
    ACTION_RESULT_SURFACE,
    control_action_result,
    control_lookup_requirement_result,
    controlled_observable_score_result,
    denominator_action_result,
    denominator_guarded_observable_result,
    horizon_work_order_result,
    observable_action_result,
    source_policy_action_result,
    coverage_action_result,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_ACTION_RESULT_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_POLICY = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_POLICY_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_WORK_ORDER_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_PRIMITIVE_COVERAGE_ACTION_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_action_results.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
OBSERVABLE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
CONTROL_READY_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_READY_SCORE_RESULT_LEDGER_2026-05-17.jsonl"
DENOMINATOR_REGISTER_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARDED_REGISTER_RESULT_LEDGER_2026-05-17.jsonl"
CONTROL_LOOKUP_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LOOKUP_REQUIREMENT_LEDGER_2026-05-17.jsonl"
SOURCE_POLICY_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_POLICY_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_WORK_RESULT_LEDGER_2026-05-17.jsonl"
CONTROL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_COMPARATOR_RESULT_LEDGER_2026-05-17.jsonl"
DENOMINATOR_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARD_RESULT_LEDGER_2026-05-17.jsonl"
HORIZON_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_WORK_ORDER_RESULT_LEDGER_2026-05-17.jsonl"
COVERAGE_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch-local observable action-result bundle only. It computes research-only proxy score deltas, "
    "control requirements, denominator-guard registrations, source repair work rows, horizon work rows, "
    "and primitive coverage action rows from the observable execution bundle. It does not change live "
    "behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-OBS-ACTION-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_execution_row_id": row.get("execution_row_id"),
        "input_implementation_row_id": row.get("input_implementation_row_id"),
        "input_source_bundle_row_id": row.get("input_source_bundle_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "observable_scope_key": row.get("observable_scope_key"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "input_execution_decision": row.get("execution_decision"),
        "input_execution_priority_score": row.get("execution_priority_score"),
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_lookup(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key)].append(row)
    return grouped


def build_observable_rows(
    rows: list[dict[str, Any]],
    control_by_scope: dict[Any, list[dict[str, Any]]],
    denominator_by_symbol: dict[Any, list[dict[str, Any]]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        scope = row.get("observable_scope_key")
        symbol = row.get("symbol")
        result = observable_action_result(row, control_by_scope.get(scope, []), denominator_by_symbol.get(symbol, []))
        output.append(
            with_common(
                {
                    "action_result_id": f"OHLC-GTOS-OBS-ACTION-OBS-000{index:02d}"[-34:],
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-OBS-{index:05d}",
                    "input_ledger_type": "OBSERVABLE_EXECUTION",
                    **common(row),
                    "control_match_execution_row_ids": [match.get("execution_row_id") for match in control_by_scope.get(scope, [])],
                    "denominator_match_execution_row_ids": [
                        match.get("execution_row_id") for match in denominator_by_symbol.get(symbol, [])
                    ],
                    **result,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_source_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-SOURCE-{index:05d}",
                    "input_ledger_type": "SOURCE_POLICY_EXECUTION",
                    **common(row),
                    **source_policy_action_result(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_control_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-CONTROL-{index:05d}",
                    "input_ledger_type": "CONTROL_EXECUTION",
                    **common(row),
                    **control_action_result(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_denominator_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-DGUARD-{index:05d}",
                    "input_ledger_type": "DENOMINATOR_EXECUTION",
                    **common(row),
                    **denominator_action_result(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_horizon_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-HREPAIR-{index:05d}",
                    "input_ledger_type": "HORIZON_WORK_ORDER_EXECUTION",
                    "input_work_order_id": row.get("execution_work_order_id"),
                    "source_horizon_repair_action_id": row.get("source_horizon_repair_action_id"),
                    "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
                    "current_source_flagged_n": row.get("current_source_flagged_n"),
                    "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
                    **common(row),
                    **horizon_work_order_result(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_coverage_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "action_result_row_id": f"OHLC-GTOS-OBS-ACTION-COVERAGE-{index:05d}",
                    "input_ledger_type": "PRIMITIVE_COVERAGE_ACTION",
                    "input_coverage_action_row_id": row.get("coverage_action_row_id"),
                    "input_primitive_coverage_row_id": row.get("input_primitive_coverage_row_id"),
                    "covered_status_counts": row.get("covered_status_counts"),
                    "implementation_stage_counts": row.get("implementation_stage_counts"),
                    **common(row),
                    **coverage_action_result(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])), 1):
        symbol, route_session = key
        output.append(
            with_common(
                {
                    "symbol_session_action_result_id": f"OHLC-GTOS-OBS-ACTION-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "action_stage_counts": string_counter(members, "action_stage"),
                    "action_result_status_counts": string_counter(members, "action_result_status"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "action_result_surface": ACTION_RESULT_SURFACE,
                    "live_effect": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    observable_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "action_stage": string_counter(unified_rows, "action_stage"),
        "action_result_status": string_counter(unified_rows, "action_result_status"),
        "observable_action_result_status": string_counter(observable_rows, "action_result_status"),
        "source_action_result_family": string_counter(source_rows, "source_action_result_family"),
        "source_action_result_status": string_counter(source_rows, "action_result_status"),
        "control_action_family": string_counter(control_rows, "control_action_family"),
        "control_action_result_status": string_counter(control_rows, "action_result_status"),
        "denominator_action_result_status": string_counter(denominator_rows, "action_result_status"),
        "horizon_action_result_status": string_counter(horizon_rows, "action_result_status"),
        "coverage_action_result_status": string_counter(coverage_rows, "action_result_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-ACTION-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, distributions


def build_runtime_spec(result: dict[str, Any], distributions: dict[str, dict[str, int]]) -> dict[str, Any]:
    return {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": result["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": result["source_manifest_hash"],
        "input_runtime_spec": INPUT_RUNTIME_SPEC.relative_to(REPO).as_posix(),
        "action_result_policy": {
            "control_ready_observables": "compute observable-minus-control proxy score deltas by exact observable scope",
            "denominator_guarded_observables": "register branch-local observable candidates only with denominator guard fields attached",
            "control_lookup_observables": "emit exact missing control scope and desired control family",
            "source_policy_rows": "split guarded proxy, ambiguity-control, exact-source repair, and horizon-repair action results",
            "coverage_rows": "preserve active full-coverage map in the current execution lane",
        },
        "ledgers": {
            "unified_action_results": UNIFIED_ACTION_LEDGER.relative_to(REPO).as_posix(),
            "observable_action_results": OBSERVABLE_ACTION_LEDGER.relative_to(REPO).as_posix(),
            "control_ready_scores": CONTROL_READY_LEDGER.relative_to(REPO).as_posix(),
            "denominator_guarded_register": DENOMINATOR_REGISTER_LEDGER.relative_to(REPO).as_posix(),
            "control_lookup_requirements": CONTROL_LOOKUP_LEDGER.relative_to(REPO).as_posix(),
            "source_policy_action_results": SOURCE_POLICY_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_work_results": SOURCE_REPAIR_LEDGER.relative_to(REPO).as_posix(),
            "control_comparator_results": CONTROL_RESULT_LEDGER.relative_to(REPO).as_posix(),
            "denominator_guard_results": DENOMINATOR_RESULT_LEDGER.relative_to(REPO).as_posix(),
            "horizon_work_order_results": HORIZON_RESULT_LEDGER.relative_to(REPO).as_posix(),
            "coverage_action_results": COVERAGE_RESULT_LEDGER.relative_to(REPO).as_posix(),
        },
        "action_distributions": distributions,
    }


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "safe_flags": SAFE_FLAGS,
                    "not_completion": True,
                }
            )
    manifest["latest_branch_local_observable_action_result_bundle"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "branch_local_observable_action_result_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built action-result rows from observable execution decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
            INPUT_UNIFIED,
            INPUT_OBSERVABLE,
            INPUT_SOURCE_POLICY,
            INPUT_CONTROL,
            INPUT_DENOMINATOR,
            INPUT_HORIZON,
            INPUT_COVERAGE,
            HELPER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_runtime = read_json(INPUT_RUNTIME_SPEC)
    unified_input = read_jsonl(INPUT_UNIFIED)
    observable_input = read_jsonl(INPUT_OBSERVABLE)
    source_input = read_jsonl(INPUT_SOURCE_POLICY)
    control_input = read_jsonl(INPUT_CONTROL)
    denominator_input = read_jsonl(INPUT_DENOMINATOR)
    horizon_input = read_jsonl(INPUT_HORIZON)
    coverage_input = read_jsonl(INPUT_COVERAGE)

    control_by_scope = build_lookup(control_input, "observable_scope_key")
    denominator_by_symbol = build_lookup(denominator_input, "symbol")

    observable_rows = build_observable_rows(
        observable_input,
        control_by_scope,
        denominator_by_symbol,
        generated_at,
        manifest_hash,
    )
    source_rows = build_source_rows(source_input, generated_at, manifest_hash)
    control_rows = build_control_rows(control_input, generated_at, manifest_hash)
    denominator_rows = build_denominator_rows(denominator_input, generated_at, manifest_hash)
    horizon_rows = build_horizon_rows(horizon_input, generated_at, manifest_hash)
    coverage_rows = build_coverage_rows(coverage_input, generated_at, manifest_hash)

    unified_rows = [*observable_rows, *source_rows, *control_rows, *denominator_rows]
    control_ready_rows = [
        row for row in observable_rows if row.get("input_execution_decision") == "OBSERVABLE_EXECUTE_SCORE_WITH_CONTROL_NOW"
    ]
    denominator_register_rows = [
        row
        for row in observable_rows
        if row.get("input_execution_decision") == "OBSERVABLE_EXECUTE_REGISTER_WITH_DENOMINATOR_GUARD"
    ]
    control_lookup_rows = [
        row for row in observable_rows if row.get("input_execution_decision") == "OBSERVABLE_EXECUTE_CONTROL_LOOKUP_REQUIRED"
    ]
    source_repair_rows = [row for row in source_rows if row.get("source_repair_required") is True]
    source_scoreable_rows = [row for row in source_rows if row.get("source_repair_required") is False]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        observable_rows,
        source_rows,
        control_rows,
        denominator_rows,
        horizon_rows,
        coverage_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-ACTION-Q-001",
                "question": "Did this packet score every control-ready observable row?",
                "answer_route": "Yes: every observable execution row marked score-with-control-now is emitted with observable-minus-control proxy score delta and exact control match count.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-ACTION-Q-002",
                "question": "Did denominator-guarded rows become registerable branch-local observable rows?",
                "answer_route": "Yes: every denominator-guarded observable row carries guard-count, guard-strength, and guard-status evidence before branch-local registration.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-ACTION-Q-003",
                "question": "Did control-missing rows become exact work rows instead of a summary?",
                "answer_route": "Yes: every control-lookup row carries the missing observable scope and desired control family.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-ACTION-Q-004",
                "question": "Did source repair and horizon rows stay active?",
                "answer_route": "Yes: all source repair/block rows and all horizon work orders are preserved as action-result rows with repair actions.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_execution_rows": len(unified_input),
        "input_observable_execution_rows": len(observable_input),
        "input_source_policy_execution_rows": len(source_input),
        "input_control_execution_rows": len(control_input),
        "input_denominator_execution_rows": len(denominator_input),
        "input_horizon_work_order_rows": len(horizon_input),
        "input_coverage_action_rows": len(coverage_input),
        "unified_action_result_rows": len(unified_rows),
        "observable_action_result_rows": len(observable_rows),
        "control_ready_score_result_rows": len(control_ready_rows),
        "denominator_guarded_register_result_rows": len(denominator_register_rows),
        "control_lookup_requirement_rows": len(control_lookup_rows),
        "source_policy_action_result_rows": len(source_rows),
        "source_scoreable_result_rows": len(source_scoreable_rows),
        "source_repair_work_result_rows": len(source_repair_rows),
        "control_comparator_result_rows": len(control_rows),
        "denominator_guard_result_rows": len(denominator_rows),
        "horizon_work_order_result_rows": len(horizon_rows),
        "coverage_action_result_rows": len(coverage_rows),
        "symbol_session_action_result_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "observable_execution_decision_bundle": input_result.get("counts", {}),
            "observable_execution_runtime_policy": input_runtime.get("execution_policy", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "action_stage_counts": distributions["action_stage"],
            "observable_action_result_status_counts": distributions["observable_action_result_status"],
            "source_action_result_family_counts": distributions["source_action_result_family"],
            "horizon_action_result_status_counts": distributions["horizon_action_result_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_ACTION_RESULT_BUNDLE_RESULT: apply branch-local observable result rows "
                "to scorer/source-repair implementation candidates, with control lookup and source repair rows "
                "remaining explicit computation work."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)
    generated_files = [
        UNIFIED_ACTION_LEDGER,
        OBSERVABLE_ACTION_LEDGER,
        CONTROL_READY_LEDGER,
        DENOMINATOR_REGISTER_LEDGER,
        CONTROL_LOOKUP_LEDGER,
        SOURCE_POLICY_LEDGER,
        SOURCE_REPAIR_LEDGER,
        CONTROL_RESULT_LEDGER,
        DENOMINATOR_RESULT_LEDGER,
        HORIZON_RESULT_LEDGER,
        COVERAGE_RESULT_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_ACTION_LEDGER, unified_rows)
    write_jsonl(OBSERVABLE_ACTION_LEDGER, observable_rows)
    write_jsonl(CONTROL_READY_LEDGER, control_ready_rows)
    write_jsonl(DENOMINATOR_REGISTER_LEDGER, denominator_register_rows)
    write_jsonl(CONTROL_LOOKUP_LEDGER, control_lookup_rows)
    write_jsonl(SOURCE_POLICY_LEDGER, source_rows)
    write_jsonl(SOURCE_REPAIR_LEDGER, source_repair_rows)
    write_jsonl(CONTROL_RESULT_LEDGER, control_rows)
    write_jsonl(DENOMINATOR_RESULT_LEDGER, denominator_rows)
    write_jsonl(HORIZON_RESULT_LEDGER, horizon_rows)
    write_jsonl(COVERAGE_RESULT_LEDGER, coverage_rows)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_session_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch-Local Observable Action Result Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified action-result rows: `{counts['unified_action_result_rows']}`",
                f"- Control-ready score rows: `{counts['control_ready_score_result_rows']}`",
                f"- Denominator-guarded registration rows: `{counts['denominator_guarded_register_result_rows']}`",
                f"- Control lookup requirement rows: `{counts['control_lookup_requirement_rows']}`",
                f"- Source policy action rows: `{counts['source_policy_action_result_rows']}`",
                f"- Source repair work rows: `{counts['source_repair_work_result_rows']}`",
                f"- Horizon work-order result rows: `{counts['horizon_work_order_result_rows']}`",
                f"- Coverage action-result rows: `{counts['coverage_action_result_rows']}`",
                "",
                "Core result: execution decisions now carry concrete branch-local action results, proxy deltas where controls exist, exact missing-control scopes where controls are absent, and source/horizon repair work rows where source policy requires repair.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
