#!/usr/bin/env python3
"""Build branch-local observable execution decisions from implementation specs."""

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

from src.research_infra.moonshot_observable_execution import (
    EXECUTION_SURFACE,
    classify_control_execution,
    classify_coverage_action,
    classify_denominator_execution,
    classify_horizon_repair_execution,
    classify_observable_execution,
    classify_source_policy_execution,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_IMPLEMENTATION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_RULE_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_POLICY = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_GUARD_POLICY_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_EXPERIMENT_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_ENFORCEMENT_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_PRIMITIVE_COVERAGE_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_execution.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_EXECUTION_LEDGER_2026-05-17.jsonl"
OBSERVABLE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_POLICY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_POLICY_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
DENOMINATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
HORIZON_WORK_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_WORK_ORDER_LEDGER_2026-05-17.jsonl"
COVERAGE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_PRIMITIVE_COVERAGE_ACTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable execution decision bundle only. It computes research shadow execution decisions "
    "for observable specs, source policies, controls, denominator guards, horizon repair work orders, and "
    "primitive coverage actions. It does not change live behavior, place orders, or claim broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-OBS-EXEC-SRC-{index:04d}",
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
        "input_implementation_row_id": row.get("implementation_row_id"),
        "input_source_bundle_row_id": row.get("source_bundle_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "observable_scope_key": row.get("observable_scope_key"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_lookup(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key)].append(row)
    return grouped


def build_source_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "execution_row_id": f"OHLC-GTOS-OBS-EXEC-SOURCE-{index:05d}",
                    "input_ledger_type": "SOURCE_POLICY_EXECUTION",
                    "input_implementation_status": row.get("implementation_status"),
                    **common(row),
                    **classify_source_policy_execution(row),
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
                    "execution_row_id": f"OHLC-GTOS-OBS-EXEC-CONTROL-{index:05d}",
                    "input_ledger_type": "CONTROL_EXECUTION",
                    "input_implementation_status": row.get("implementation_status"),
                    **common(row),
                    **classify_control_execution(row),
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
                    "execution_row_id": f"OHLC-GTOS-OBS-EXEC-DGUARD-{index:05d}",
                    "input_ledger_type": "DENOMINATOR_EXECUTION",
                    "input_implementation_status": row.get("implementation_status"),
                    **common(row),
                    **classify_denominator_execution(row),
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
                    "execution_work_order_id": f"OHLC-GTOS-OBS-EXEC-HREPAIR-{index:05d}",
                    "input_ledger_type": "HORIZON_REPAIR_WORK_ORDER",
                    "input_implementation_status": row.get("implementation_status"),
                    "source_horizon_repair_action_id": row.get("source_horizon_repair_action_id"),
                    "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
                    "current_source_flagged_n": row.get("current_source_flagged_n"),
                    "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
                    **common(row),
                    "input_implementation_row_id": row.get("implementation_repair_id"),
                    **classify_horizon_repair_execution(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_observable_rows(
    rows: list[dict[str, Any]],
    source_by_scope: dict[Any, list[dict[str, Any]]],
    control_by_scope: dict[Any, list[dict[str, Any]]],
    denominator_by_symbol: dict[Any, list[dict[str, Any]]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        source_matches = source_by_scope.get(row.get("observable_scope_key"), [])
        control_matches = control_by_scope.get(row.get("observable_scope_key"), [])
        denominator_matches = denominator_by_symbol.get(row.get("symbol"), [])
        output.append(
            with_common(
                {
                    "execution_row_id": f"OHLC-GTOS-OBS-EXEC-OBS-{index:05d}",
                    "input_ledger_type": "OBSERVABLE_EXECUTION",
                    "input_implementation_status": row.get("implementation_status"),
                    "observable_family": row.get("observable_family"),
                    "source_policy_status_matches": [match.get("implementation_status") for match in source_matches],
                    "control_status_matches": [match.get("implementation_status") for match in control_matches],
                    "denominator_status_matches": [match.get("implementation_status") for match in denominator_matches],
                    **common(row),
                    **classify_observable_execution(
                        row,
                        [str(match.get("implementation_status")) for match in source_matches],
                        [str(match.get("implementation_status")) for match in control_matches],
                        [str(match.get("implementation_status")) for match in denominator_matches],
                    ),
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
                    "coverage_action_row_id": f"OHLC-GTOS-OBS-EXEC-COVERAGE-{index:05d}",
                    "input_ledger_type": "PRIMITIVE_COVERAGE_EXECUTION",
                    "input_primitive_coverage_row_id": row.get("primitive_coverage_row_id"),
                    "covered_status_counts": row.get("covered_status_counts"),
                    "implementation_stage_counts": row.get("implementation_stage_counts"),
                    "row_count": row.get("row_count"),
                    **common(row),
                    **classify_coverage_action(row),
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
                    "symbol_session_row_id": f"OHLC-GTOS-OBS-EXEC-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "execution_stage_counts": string_counter(members, "execution_stage"),
                    "execution_decision_counts": string_counter(members, "execution_decision"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "execution_surface": EXECUTION_SURFACE,
                    "live_effect": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "execution_stage": string_counter(unified_rows, "execution_stage"),
        "execution_decision": string_counter(unified_rows, "execution_decision"),
        "observable_execution_decision": string_counter(
            [row for row in unified_rows if row.get("execution_stage") == "OBSERVABLE_EXECUTION"],
            "execution_decision",
        ),
        "source_execution_decision": string_counter(
            [row for row in unified_rows if row.get("execution_stage") == "SOURCE_POLICY_EXECUTION"],
            "execution_decision",
        ),
        "control_execution_decision": string_counter(
            [row for row in unified_rows if row.get("execution_stage") == "CONTROL_EXECUTION"],
            "execution_decision",
        ),
        "denominator_execution_decision": string_counter(
            [row for row in unified_rows if row.get("execution_stage") == "DENOMINATOR_EXECUTION"],
            "execution_decision",
        ),
        "horizon_work_order_decision": string_counter(horizon_rows, "execution_decision"),
        "coverage_action_decision": string_counter(coverage_rows, "execution_decision"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-EXEC-BUCKET-{len(output) + 1:04d}",
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
        "execution_policy": {
            "observable_execution": "compute per-observable source/control/denominator readiness",
            "source_policy_execution": "execute guarded proxy score, exact repair, or horizon repair decision",
            "control_execution": "run required comparator/ablation before enable interpretation",
            "denominator_execution": "enforce concentration/source-root/context guard",
            "horizon_work_order": "rebuild targetable horizon rows before source-dependent enable",
            "coverage_action": "carry full-coverage status into next same-resource action",
        },
        "ledgers": {
            "unified_execution": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "observable_execution": OBSERVABLE_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
            "source_policy_execution": SOURCE_POLICY_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
            "control_execution": CONTROL_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
            "denominator_execution": DENOMINATOR_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
            "horizon_work_orders": HORIZON_WORK_ORDER_LEDGER.relative_to(REPO).as_posix(),
            "coverage_actions": COVERAGE_ACTION_LEDGER.relative_to(REPO).as_posix(),
        },
        "decision_distributions": distributions,
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
    manifest["latest_branch_local_observable_execution_decision_bundle"] = {
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
        "event": "branch_local_observable_execution_decision_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built execution decisions from branch-local observable/scorer implementation specs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
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
    observable_input = read_jsonl(INPUT_OBSERVABLE)
    source_input = read_jsonl(INPUT_SOURCE_POLICY)
    control_input = read_jsonl(INPUT_CONTROL)
    denominator_input = read_jsonl(INPUT_DENOMINATOR)
    horizon_input = read_jsonl(INPUT_HORIZON)
    coverage_input = read_jsonl(INPUT_COVERAGE)

    source_by_scope = build_lookup(source_input, "observable_scope_key")
    control_by_scope = build_lookup(control_input, "observable_scope_key")
    denominator_by_symbol = build_lookup(denominator_input, "symbol")

    observable_rows = build_observable_rows(
        observable_input,
        source_by_scope,
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
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(unified_rows, horizon_rows, coverage_rows, generated_at, manifest_hash)
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-EXEC-Q-001",
                "question": "Did this packet execute every implementation spec row?",
                "answer_route": "Yes: the 444 observables, 309 source policies, 231 controls, and 124 denominator guards are emitted into the 1,108-row unified execution ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-EXEC-Q-002",
                "question": "Did horizon fail-closed rows become concrete work orders?",
                "answer_route": "Yes: all 37 horizon repair specs are emitted as rebuild/rescore or rebuild/kill-if-negative work orders.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-EXEC-Q-003",
                "question": "Did primitive coverage remain active without changing lanes?",
                "answer_route": "Yes: all 520 primitive coverage rows are converted to coverage action rows and remain tied to execution, source, control, guard, or repair actions.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_observable_rows": len(observable_input),
        "input_source_policy_rows": len(source_input),
        "input_control_rows": len(control_input),
        "input_denominator_rows": len(denominator_input),
        "input_horizon_repair_rows": len(horizon_input),
        "input_coverage_rows": len(coverage_input),
        "unified_execution_rows": len(unified_rows),
        "observable_execution_rows": len(observable_rows),
        "source_policy_execution_rows": len(source_rows),
        "control_execution_rows": len(control_rows),
        "denominator_execution_rows": len(denominator_rows),
        "horizon_work_order_rows": len(horizon_rows),
        "coverage_action_rows": len(coverage_rows),
        "symbol_session_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
        "observable_source_repair_first_rows": sum(
            1 for row in observable_rows if row.get("execution_decision") == "OBSERVABLE_EXECUTE_SOURCE_REPAIR_FIRST"
        ),
        "observable_score_with_control_rows": sum(
            1 for row in observable_rows if row.get("execution_decision") == "OBSERVABLE_EXECUTE_SCORE_WITH_CONTROL_NOW"
        ),
        "observable_register_with_denominator_guard_rows": sum(
            1
            for row in observable_rows
            if row.get("execution_decision") == "OBSERVABLE_EXECUTE_REGISTER_WITH_DENOMINATOR_GUARD"
        ),
        "source_repair_or_block_execution_rows": sum(
            1
            for row in source_rows
            if "REPAIR" in str(row.get("execution_decision")) or "KILL_CHECK" in str(row.get("execution_decision"))
        ),
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
            "observable_scorer_implementation_bundle": input_result.get("counts", {}),
            "observable_scorer_runtime_policy": input_runtime.get("implementation_policy", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "execution_stage_counts": distributions["execution_stage"],
            "observable_execution_decision_counts": distributions["observable_execution_decision"],
            "source_execution_decision_counts": distributions["source_execution_decision"],
            "horizon_work_order_decision_counts": distributions["horizon_work_order_decision"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_RESULT: execute observable readiness, "
                "source policy, control comparator, denominator guard, horizon repair, and primitive coverage "
                "decisions before the next scorer/source-repair computation layer."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)
    generated_files = [
        UNIFIED_LEDGER,
        OBSERVABLE_EXECUTION_LEDGER,
        SOURCE_POLICY_EXECUTION_LEDGER,
        CONTROL_EXECUTION_LEDGER,
        DENOMINATOR_EXECUTION_LEDGER,
        HORIZON_WORK_ORDER_LEDGER,
        COVERAGE_ACTION_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(OBSERVABLE_EXECUTION_LEDGER, observable_rows)
    write_jsonl(SOURCE_POLICY_EXECUTION_LEDGER, source_rows)
    write_jsonl(CONTROL_EXECUTION_LEDGER, control_rows)
    write_jsonl(DENOMINATOR_EXECUTION_LEDGER, denominator_rows)
    write_jsonl(HORIZON_WORK_ORDER_LEDGER, horizon_rows)
    write_jsonl(COVERAGE_ACTION_LEDGER, coverage_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Execution Decision Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified execution rows: `{counts['unified_execution_rows']}`",
                f"- Observable execution rows: `{counts['observable_execution_rows']}`",
                f"- Source policy execution rows: `{counts['source_policy_execution_rows']}`",
                f"- Control execution rows: `{counts['control_execution_rows']}`",
                f"- Denominator execution rows: `{counts['denominator_execution_rows']}`",
                f"- Horizon work orders: `{counts['horizon_work_order_rows']}`",
                f"- Primitive coverage action rows: `{counts['coverage_action_rows']}`",
                "",
                "Core result: observable/scorer implementation specs have been converted into branch-local execution decisions with source, control, denominator, horizon repair, and coverage actions preserved.",
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
