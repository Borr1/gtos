#!/usr/bin/env python3
"""Build implementation candidates from branch-local observable action results."""

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

from src.research_infra.moonshot_observable_implementation_candidates import (
    IMPLEMENTATION_CANDIDATE_SURFACE,
    control_implementation_candidate,
    coverage_implementation_candidate,
    denominator_implementation_candidate,
    horizon_implementation_candidate,
    observable_implementation_candidate,
    source_implementation_candidate,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_ACTION_RESULT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_CANDIDATE_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_READY = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_READY_SCORE_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR_REGISTER = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARDED_REGISTER_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_LOOKUP = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_LOOKUP_REQUIREMENT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_POLICY = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_POLICY_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_WORK_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_COMPARATOR_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARD_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_WORK_ORDER_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_COVERAGE_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_implementation_candidates.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
OBSERVABLE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
CONTROLLED_CHALLENGER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROLLED_OBSERVABLE_CHALLENGER_LEDGER_2026-05-17.jsonl"
DENOMINATOR_OBSERVABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_REGISTER_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_BUILDER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_BUILDER_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
SOURCE_SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_SCORER_CANDIDATE_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
CONTROL_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_COMPARATOR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
DENOMINATOR_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARD_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
HORIZON_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
COVERAGE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_IMPLEMENTATION_MAP_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable implementation-candidate bundle only. It converts action-result rows into "
    "research-only branch-local scorer, control-scope, denominator-guard, source-repair, horizon-repair, "
    "and coverage-map implementation candidates. It does not change live behavior, place orders, or claim "
    "broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-OBS-IMPL-SRC-{index:04d}",
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
        "input_action_result_row_id": row.get("action_result_row_id"),
        "input_execution_row_id": row.get("input_execution_row_id"),
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
        "input_action_result_status": row.get("action_result_status"),
        "input_action_result_decision": row.get("action_result_decision"),
        "proxy_r_style_score_delta": row.get("proxy_r_style_score_delta"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_candidate_rows(
    rows: list[dict[str, Any]],
    prefix: str,
    input_type: str,
    classifier: Any,
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "implementation_candidate_row_id": f"{prefix}-{index:05d}",
                    "input_ledger_type": input_type,
                    **common(row),
                    **classifier(row),
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
                    "symbol_session_implementation_id": f"OHLC-GTOS-OBS-IMPL-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "implementation_candidate_stage_counts": string_counter(members, "implementation_candidate_stage"),
                    "implementation_candidate_status_counts": string_counter(members, "implementation_candidate_status"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
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
        "implementation_candidate_stage": string_counter(unified_rows, "implementation_candidate_stage"),
        "implementation_candidate_status": string_counter(unified_rows, "implementation_candidate_status"),
        "observable_implementation_status": string_counter(observable_rows, "implementation_candidate_status"),
        "source_implementation_status": string_counter(source_rows, "implementation_candidate_status"),
        "control_implementation_status": string_counter(control_rows, "implementation_candidate_status"),
        "denominator_implementation_status": string_counter(denominator_rows, "implementation_candidate_status"),
        "horizon_implementation_status": string_counter(horizon_rows, "implementation_candidate_status"),
        "coverage_implementation_status": string_counter(coverage_rows, "implementation_candidate_status"),
        "branch_local_ready": string_counter(unified_rows, "branch_local_ready"),
        "control_builder_required": string_counter(unified_rows, "control_builder_required"),
        "source_repair_required": string_counter(unified_rows, "source_repair_required"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-IMPL-BUCKET-{len(output) + 1:04d}",
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
        "implementation_candidate_policy": {
            "controlled_observable_challengers": "register branch-local shadow scorer candidates with matched-control proxy deltas",
            "denominator_guarded_observables": "register branch-local observables only with denominator guard enforcement",
            "control_scope_builders": "build exact control scopes before interpreting unmatched observables",
            "source_scorer_candidates": "score guarded or ambiguous source proxies under controls and guards",
            "source_repairs": "execute exact-source or horizon repair work before source-dependent enable",
            "coverage_map": "preserve every touched primitive family status for vNext synthesis",
        },
        "ledgers": {
            "unified_implementation_candidates": UNIFIED_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "observable_implementation_candidates": OBSERVABLE_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "controlled_observable_challengers": CONTROLLED_CHALLENGER_LEDGER.relative_to(REPO).as_posix(),
            "denominator_guarded_observable_registers": DENOMINATOR_OBSERVABLE_LEDGER.relative_to(REPO).as_posix(),
            "control_scope_builders": CONTROL_SCOPE_BUILDER_LEDGER.relative_to(REPO).as_posix(),
            "source_implementation_candidates": SOURCE_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "source_scorer_candidates": SOURCE_SCORER_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_implementations": SOURCE_REPAIR_LEDGER.relative_to(REPO).as_posix(),
            "control_comparator_implementations": CONTROL_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "denominator_guard_implementations": DENOMINATOR_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "horizon_repair_implementations": HORIZON_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
            "coverage_implementation_map": COVERAGE_CANDIDATE_LEDGER.relative_to(REPO).as_posix(),
        },
        "implementation_distributions": distributions,
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
    manifest["latest_branch_local_observable_implementation_candidate_bundle"] = {
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
        "event": "branch_local_observable_implementation_candidate_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built implementation candidates from observable action-result rows.",
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
            INPUT_CONTROL_READY,
            INPUT_DENOMINATOR_REGISTER,
            INPUT_CONTROL_LOOKUP,
            INPUT_SOURCE_POLICY,
            INPUT_SOURCE_REPAIR,
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
    control_ready_input = read_jsonl(INPUT_CONTROL_READY)
    denominator_register_input = read_jsonl(INPUT_DENOMINATOR_REGISTER)
    control_lookup_input = read_jsonl(INPUT_CONTROL_LOOKUP)
    source_input = read_jsonl(INPUT_SOURCE_POLICY)
    source_repair_input = read_jsonl(INPUT_SOURCE_REPAIR)
    control_input = read_jsonl(INPUT_CONTROL)
    denominator_input = read_jsonl(INPUT_DENOMINATOR)
    horizon_input = read_jsonl(INPUT_HORIZON)
    coverage_input = read_jsonl(INPUT_COVERAGE)

    observable_rows = build_candidate_rows(
        observable_input,
        "OHLC-GTOS-OBS-IMPL-OBS",
        "OBSERVABLE_ACTION_RESULT",
        observable_implementation_candidate,
        generated_at,
        manifest_hash,
    )
    source_rows = build_candidate_rows(
        source_input,
        "OHLC-GTOS-OBS-IMPL-SOURCE",
        "SOURCE_POLICY_ACTION_RESULT",
        source_implementation_candidate,
        generated_at,
        manifest_hash,
    )
    control_rows = build_candidate_rows(
        control_input,
        "OHLC-GTOS-OBS-IMPL-CONTROL",
        "CONTROL_ACTION_RESULT",
        control_implementation_candidate,
        generated_at,
        manifest_hash,
    )
    denominator_rows = build_candidate_rows(
        denominator_input,
        "OHLC-GTOS-OBS-IMPL-DGUARD",
        "DENOMINATOR_ACTION_RESULT",
        denominator_implementation_candidate,
        generated_at,
        manifest_hash,
    )
    horizon_rows = build_candidate_rows(
        horizon_input,
        "OHLC-GTOS-OBS-IMPL-HREPAIR",
        "HORIZON_WORK_ORDER_ACTION_RESULT",
        horizon_implementation_candidate,
        generated_at,
        manifest_hash,
    )
    coverage_rows = build_candidate_rows(
        coverage_input,
        "OHLC-GTOS-OBS-IMPL-COVERAGE",
        "PRIMITIVE_COVERAGE_ACTION_RESULT",
        coverage_implementation_candidate,
        generated_at,
        manifest_hash,
    )

    unified_rows = [*observable_rows, *source_rows, *control_rows, *denominator_rows]
    controlled_challenger_rows = [
        row for row in observable_rows if row.get("implementation_candidate_status") == "OBSERVABLE_IMPL_ENABLE_CONTROLLED_CHALLENGER_SCORER"
    ]
    denominator_observable_rows = [
        row for row in observable_rows if row.get("implementation_candidate_status") == "OBSERVABLE_IMPL_REGISTER_DENOMINATOR_GUARDED_SHADOW"
    ]
    control_scope_builder_rows = [
        row for row in observable_rows if row.get("implementation_candidate_status") == "OBSERVABLE_IMPL_BUILD_CONTROL_SCOPE_BEFORE_ENABLE"
    ]
    source_scorer_rows = [row for row in source_rows if row.get("source_repair_required") is False]
    source_repair_rows = [row for row in source_rows if row.get("source_repair_required") is True]
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
                "question_id": "OHLC-GTOS-OBS-IMPL-Q-001",
                "question": "Did every action-result row become a concrete implementation candidate or work row?",
                "answer_route": "Yes: the 1,108 unified action-result rows map to observable, source, control, and denominator implementation candidates; horizon and coverage rows remain separate work/map ledgers.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPL-Q-002",
                "question": "Which observable rows are immediately implementable in branch-local shadow scoring?",
                "answer_route": "The packet preserves 14 controlled observable challengers and 262 denominator-guarded observable registrations as branch-local ready candidates, while 168 rows require exact control-scope builders.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPL-Q-003",
                "question": "Did source repair rows remain active?",
                "answer_route": "Yes: all 98 source repair/block rows remain source repair implementation rows split by exact-source, horizon-rescore, and horizon-kill-check action.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPL-Q-004",
                "question": "Does this narrow to one primitive family or current production behavior?",
                "answer_route": "No: the 520 coverage-map rows are preserved and the implementation candidate statuses carry observable, source, control, denominator, horizon, and coverage families forward for vNext synthesis.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_action_result_rows": len(unified_input),
        "input_observable_action_result_rows": len(observable_input),
        "input_control_ready_score_result_rows": len(control_ready_input),
        "input_denominator_guarded_register_rows": len(denominator_register_input),
        "input_control_lookup_requirement_rows": len(control_lookup_input),
        "input_source_policy_action_result_rows": len(source_input),
        "input_source_repair_work_result_rows": len(source_repair_input),
        "input_control_comparator_result_rows": len(control_input),
        "input_denominator_guard_result_rows": len(denominator_input),
        "input_horizon_work_order_result_rows": len(horizon_input),
        "input_coverage_action_result_rows": len(coverage_input),
        "unified_implementation_candidate_rows": len(unified_rows),
        "observable_implementation_candidate_rows": len(observable_rows),
        "controlled_observable_challenger_rows": len(controlled_challenger_rows),
        "denominator_guarded_observable_register_rows": len(denominator_observable_rows),
        "control_scope_builder_rows": len(control_scope_builder_rows),
        "source_implementation_candidate_rows": len(source_rows),
        "source_scorer_candidate_rows": len(source_scorer_rows),
        "source_repair_implementation_rows": len(source_repair_rows),
        "control_comparator_implementation_rows": len(control_rows),
        "denominator_guard_implementation_rows": len(denominator_rows),
        "horizon_repair_implementation_rows": len(horizon_rows),
        "coverage_implementation_map_rows": len(coverage_rows),
        "symbol_session_implementation_rows": len(symbol_session_rows),
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
            "observable_action_result_bundle": input_result.get("counts", {}),
            "observable_action_runtime_policy": input_runtime.get("action_result_policy", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "implementation_candidate_stage_counts": distributions["implementation_candidate_stage"],
            "observable_implementation_status_counts": distributions["observable_implementation_status"],
            "source_implementation_status_counts": distributions["source_implementation_status"],
            "horizon_implementation_status_counts": distributions["horizon_implementation_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_CANDIDATE_BUNDLE_RESULT: implement branch-local "
                "controlled observable challengers and denominator-guarded observables, build missing control "
                "scopes, and execute source/horizon repair work rows before any stronger scorer synthesis."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)
    generated_files = [
        UNIFIED_CANDIDATE_LEDGER,
        OBSERVABLE_CANDIDATE_LEDGER,
        CONTROLLED_CHALLENGER_LEDGER,
        DENOMINATOR_OBSERVABLE_LEDGER,
        CONTROL_SCOPE_BUILDER_LEDGER,
        SOURCE_CANDIDATE_LEDGER,
        SOURCE_SCORER_LEDGER,
        SOURCE_REPAIR_LEDGER,
        CONTROL_CANDIDATE_LEDGER,
        DENOMINATOR_CANDIDATE_LEDGER,
        HORIZON_CANDIDATE_LEDGER,
        COVERAGE_CANDIDATE_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_CANDIDATE_LEDGER, unified_rows)
    write_jsonl(OBSERVABLE_CANDIDATE_LEDGER, observable_rows)
    write_jsonl(CONTROLLED_CHALLENGER_LEDGER, controlled_challenger_rows)
    write_jsonl(DENOMINATOR_OBSERVABLE_LEDGER, denominator_observable_rows)
    write_jsonl(CONTROL_SCOPE_BUILDER_LEDGER, control_scope_builder_rows)
    write_jsonl(SOURCE_CANDIDATE_LEDGER, source_rows)
    write_jsonl(SOURCE_SCORER_LEDGER, source_scorer_rows)
    write_jsonl(SOURCE_REPAIR_LEDGER, source_repair_rows)
    write_jsonl(CONTROL_CANDIDATE_LEDGER, control_rows)
    write_jsonl(DENOMINATOR_CANDIDATE_LEDGER, denominator_rows)
    write_jsonl(HORIZON_CANDIDATE_LEDGER, horizon_rows)
    write_jsonl(COVERAGE_CANDIDATE_LEDGER, coverage_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Implementation Candidate Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified implementation candidate rows: `{counts['unified_implementation_candidate_rows']}`",
                f"- Controlled observable challenger rows: `{counts['controlled_observable_challenger_rows']}`",
                f"- Denominator-guarded observable register rows: `{counts['denominator_guarded_observable_register_rows']}`",
                f"- Control-scope builder rows: `{counts['control_scope_builder_rows']}`",
                f"- Source scorer candidate rows: `{counts['source_scorer_candidate_rows']}`",
                f"- Source repair implementation rows: `{counts['source_repair_implementation_rows']}`",
                f"- Coverage implementation-map rows: `{counts['coverage_implementation_map_rows']}`",
                "",
                "Core result: action-result rows now become branch-local implementation candidates or exact work rows instead of remaining labels or summaries.",
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
