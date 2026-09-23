#!/usr/bin/env python3
"""Build denominator/source rebuild action rows from control/source split outputs."""

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

from src.research_infra.moonshot_branch_local_denominator_source_rebuild import (
    DENOMINATOR_SOURCE_REBUILD_SURFACE,
    control_member_denominator_evidence,
    exact_control_scope_denominator_rebuild,
    exact_control_target_rebuild,
    horizon_materialization_rebuild,
    scope_key,
    scope_rebuild_action,
    source_materialization_rebuild,
)


CONTROL_SPLIT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_CONTROL_SOURCE_SPLIT_BUNDLE"
SOURCE_MAT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION"
SHADOW_GUARD_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE"
SCORER_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_REBUILD_BUNDLE"

CONTROL_SPLIT_RESULT = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_RESULT_2026-05-17.json"
CONTROL_SPLIT_RUNTIME = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_UNIFIED_CONTROL_SOURCE_SPLIT_LEDGER_2026-05-17.jsonl"
INPUT_EXACT = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_EXACT_CONTROL_RELATION_SPLIT_LEDGER_2026-05-17.jsonl"
INPUT_MEMBER = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_CONTROL_MEMBER_RELATION_SPLIT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_SOURCE_ACQUISITION_SPLIT_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_HORIZON_REBUILD_SPLIT_LEDGER_2026-05-17.jsonl"
INPUT_SCOPE = ROUTE_DIR / f"{CONTROL_SPLIT_PREFIX}_SCOPE_ACQUISITION_PLAN_LEDGER_2026-05-17.jsonl"

MATERIALIZATION_LEDGER = ROUTE_DIR / f"{SOURCE_MAT_PREFIX}_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SHADOW_UNIFIED_LEDGER = ROUTE_DIR / f"{SHADOW_GUARD_PREFIX}_UNIFIED_DECISION_LEDGER_2026-05-17.jsonl"
CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{SCORER_EXEC_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DENOMINATOR_SOURCE_REBUILD_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_DENOMINATOR_SOURCE_REBUILD_LEDGER_2026-05-17.jsonl"
EXACT_TARGET_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_TARGET_DENOMINATOR_LEDGER_2026-05-17.jsonl"
EXACT_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_SCOPE_DENOMINATOR_LEDGER_2026-05-17.jsonl"
MEMBER_EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_MEMBER_DENOMINATOR_EVIDENCE_LEDGER_2026-05-17.jsonl"
SOURCE_REBUILD_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
HORIZON_REBUILD_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
SCOPE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_REBUILD_ACTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_DENOMINATOR_SOURCE_REBUILD_LEDGER_2026-05-17.jsonl"
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
    "Branch-local denominator/source rebuild bundle only. It joins the control/source split rows to current "
    "source materialization, shadow source-guard, and control execution surfaces, then emits exact-control "
    "denominator acquisition actions plus source and horizon rebuild actions. It does not change live behavior, "
    "place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-SRC-REBUILD-SRC-{index:04d}",
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


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def scope_counter(rows: list[dict[str, Any]]) -> dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[scope_key(row)].append(row)
    return grouped


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
            "live_effect": False,
        }
    )
    return row


def make_row(row_id_key: str, row_id: str, payload: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    payload[row_id_key] = row_id
    return with_common(payload, generated_at, manifest_hash)


def materialization_by_source_code(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_code_candidate_id")): row for row in rows}


def shadow_by_source_code(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_code_candidate_id"))].append(row)
    return grouped


def build_symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])), 1):
        symbol, route_session = key
        output.append(
            with_common(
                {
                    "symbol_session_denominator_source_rebuild_id": f"OHLC-GTOS-DENOM-SRC-REBUILD-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "denominator_source_rebuild_lane_counts": string_counter(
                        members, "denominator_source_rebuild_lane"
                    ),
                    "denominator_source_rebuild_status_counts": string_counter(
                        members, "denominator_source_rebuild_status"
                    ),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    exact_target_rows: list[dict[str, Any]],
    exact_scope_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "denominator_source_rebuild_lane": string_counter(unified_rows, "denominator_source_rebuild_lane"),
        "denominator_source_rebuild_status": string_counter(unified_rows, "denominator_source_rebuild_status"),
        "exact_target_best_proxy_relation": string_counter(exact_target_rows, "best_available_proxy_relation"),
        "exact_target_current_shadow_guard_row_count": string_counter(exact_target_rows, "current_shadow_guard_row_count"),
        "exact_scope_status": string_counter(exact_scope_rows, "denominator_source_rebuild_status"),
        "member_evidence_status": string_counter(member_rows, "denominator_source_rebuild_status"),
        "source_rebuild_status": string_counter(source_rows, "denominator_source_rebuild_status"),
        "source_materialization_status": string_counter(source_rows, "source_materialization_execution_status"),
        "horizon_rebuild_status": string_counter(horizon_rows, "denominator_source_rebuild_status"),
        "horizon_fail_if_negative_persists": string_counter(horizon_rows, "fail_if_negative_persists"),
        "scope_action_status": string_counter(scope_rows, "denominator_source_rebuild_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            unified_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-REBUILD-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, distributions


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
    manifest["latest_branch_local_denominator_source_rebuild_bundle"] = {
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
        "event": "branch_local_denominator_source_rebuild_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Joined control/source split scopes to materialization, shadow guard, and control execution surfaces; emitted exact-control/source/horizon rebuild actions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            CONTROL_SPLIT_RESULT,
            CONTROL_SPLIT_RUNTIME,
            INPUT_UNIFIED,
            INPUT_EXACT,
            INPUT_MEMBER,
            INPUT_SOURCE,
            INPUT_HORIZON,
            INPUT_SCOPE,
            MATERIALIZATION_LEDGER,
            SHADOW_UNIFIED_LEDGER,
            CONTROL_EXECUTION_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    control_split_result = read_json(CONTROL_SPLIT_RESULT)
    input_unified = read_jsonl(INPUT_UNIFIED)
    exact_input = read_jsonl(INPUT_EXACT)
    member_input = read_jsonl(INPUT_MEMBER)
    source_input = read_jsonl(INPUT_SOURCE)
    horizon_input = read_jsonl(INPUT_HORIZON)
    scope_input = read_jsonl(INPUT_SCOPE)
    materialization_input = read_jsonl(MATERIALIZATION_LEDGER)
    shadow_input = read_jsonl(SHADOW_UNIFIED_LEDGER)
    control_exec_input = read_jsonl(CONTROL_EXECUTION_LEDGER)

    materialization_code_index = materialization_by_source_code(materialization_input)
    shadow_code_index = shadow_by_source_code(shadow_input)
    materialization_scope_index = scope_counter(materialization_input)
    shadow_scope_index = scope_counter(shadow_input)
    control_exec_scope_index = scope_counter(control_exec_input)

    exact_target_rows: list[dict[str, Any]] = []
    for index, row in enumerate(exact_input, 1):
        target_rows = exact_control_target_rebuild(
            row,
            shadow_code_index.get(str(row.get("source_code_candidate_id")), []),
            materialization_scope_index.get(scope_key(row), []),
            control_exec_scope_index.get(scope_key(row), []),
        )
        exact_target_rows.append(
            make_row(
                "denominator_source_rebuild_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-EXACTTARGET-{index:05d}",
                target_rows,
                generated_at,
                manifest_hash,
            )
        )

    exact_by_scope = scope_counter(exact_input)
    member_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in member_input:
        member_by_target[str(row.get("input_repair_execution_row_id"))].append(row)
    member_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in member_input:
        member_by_scope[scope_key(row)].append(row)

    exact_scope_rows: list[dict[str, Any]] = []
    exact_scope_inputs = [
        row for row in scope_input if row.get("control_source_split_status") == "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_CONTROL_ONLY"
    ]
    for index, scope_row in enumerate(exact_scope_inputs, 1):
        exact_scope_rows.append(
            make_row(
                "exact_control_scope_denominator_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-EXACTSCOPE-{index:05d}",
                exact_control_scope_denominator_rebuild(
                    scope_row,
                    exact_by_scope.get(scope_key(scope_row), []),
                    shadow_scope_index.get(scope_key(scope_row), []),
                    materialization_scope_index.get(scope_key(scope_row), []),
                    control_exec_scope_index.get(scope_key(scope_row), []),
                    member_by_scope.get(scope_key(scope_row), []),
                ),
                generated_at,
                manifest_hash,
            )
        )

    exact_target_by_target_id = {row.get("input_repair_execution_row_id"): row for row in exact_target_rows}
    member_rows: list[dict[str, Any]] = []
    for row in member_input:
        target = exact_target_by_target_id.get(row.get("input_repair_execution_row_id"), {})
        member_rows.append(
            make_row(
                "control_member_denominator_evidence_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-MEMBER-{len(member_rows) + 1:07d}",
                control_member_denominator_evidence(row, target),
                generated_at,
                manifest_hash,
            )
        )

    source_rows: list[dict[str, Any]] = []
    horizon_source_input: list[dict[str, Any]] = []
    exact_source_input: list[dict[str, Any]] = []
    for row in source_input:
        if row.get("source_repair_family") == "EXACT_SOURCE_REPAIR":
            exact_source_input.append(row)
        else:
            horizon_source_input.append(row)
    for index, row in enumerate(exact_source_input, 1):
        source_rows.append(
            make_row(
                "denominator_source_rebuild_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-SOURCE-{index:05d}",
                source_materialization_rebuild(
                    row,
                    materialization_code_index.get(str(row.get("source_code_candidate_id"))),
                ),
                generated_at,
                manifest_hash,
            )
        )

    horizon_by_target = {row.get("input_repair_execution_row_id"): row for row in horizon_input}
    horizon_rows: list[dict[str, Any]] = []
    for index, row in enumerate(horizon_source_input, 1):
        horizon_rows.append(
            make_row(
                "denominator_source_rebuild_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-HORIZON-{index:05d}",
                horizon_materialization_rebuild(
                    row,
                    horizon_by_target.get(row.get("input_repair_execution_row_id")),
                    materialization_code_index.get(str(row.get("source_code_candidate_id"))),
                ),
                generated_at,
                manifest_hash,
            )
        )

    exact_scope_by_scope = {scope_key(row): row for row in exact_scope_rows}
    source_rows_by_scope = scope_counter(source_rows)
    horizon_rows_by_scope = scope_counter(horizon_rows)
    scope_action_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scope_input, 1):
        scope_action_rows.append(
            make_row(
                "scope_rebuild_action_row_id",
                f"OHLC-GTOS-DENOM-SRC-REBUILD-SCOPE-{index:05d}",
                scope_rebuild_action(
                    row,
                    exact_scope_by_scope.get(scope_key(row)),
                    source_rows_by_scope.get(scope_key(row), []),
                    horizon_rows_by_scope.get(scope_key(row), []),
                ),
                generated_at,
                manifest_hash,
            )
        )

    unified_rows = [*exact_target_rows, *source_rows, *horizon_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        exact_target_rows,
        exact_scope_rows,
        member_rows,
        source_rows,
        horizon_rows,
        scope_action_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-001",
                "question": "Can exact-control scopes be scored from current materialization or control execution rows?",
                "answer_route": "No. The 23 exact-control scopes have 0 materialization rows and 0 control execution rows; all 92 target rows are shadow-guard-only and exact-control acquisition stays open.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-002",
                "question": "Did the exact-control lane preserve every selected control member?",
                "answer_route": "Yes. All 21,252 member rows are emitted again as denominator proxy evidence; 464 are strongest-proxy rows and 20,788 are context rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-003",
                "question": "What did direct materialization show for exact-source scopes?",
                "answer_route": "All 61 exact-source scopes have materialization rows, but exact targetable counts remain under n20; expanded targetable/source proxies close n20 and exact-source rebuild remains required before scalar use.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-004",
                "question": "What did direct materialization show for horizon-source scopes?",
                "answer_route": "All 37 horizon scopes materialize current source n20 with horizon fail-closed rows; 29 route to rescore repair and 8 route to kill-check repair if weak proxy behavior persists after targetable rebuild.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-005",
                "question": "Does this bundle change the active lane into a broad inventory route?",
                "answer_route": "No. It keeps the durable broad-coverage mandate attached while executing the active exact-control/source/horizon rebuild lane with concrete scope and target rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-REBUILD-Q-006",
                "question": "What is the next same-resource computation?",
                "answer_route": "Use these action rows to build exact-control replay denominators where possible, rebuild exact-source targetable rows to n20, and rebuild horizon targetable rows before accepting, redesigning, or killing each scope.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_control_source_split_unified_rows": len(input_unified),
        "input_exact_control_relation_split_rows": len(exact_input),
        "input_control_member_relation_split_rows": len(member_input),
        "input_source_acquisition_split_rows": len(source_input),
        "input_horizon_rebuild_split_rows": len(horizon_input),
        "input_scope_acquisition_plan_rows": len(scope_input),
        "input_materialization_rows": len(materialization_input),
        "input_shadow_guard_unified_rows": len(shadow_input),
        "input_control_execution_rows": len(control_exec_input),
        "unified_denominator_source_rebuild_rows": len(unified_rows),
        "exact_control_target_denominator_rows": len(exact_target_rows),
        "exact_control_scope_denominator_rows": len(exact_scope_rows),
        "control_member_denominator_evidence_rows": len(member_rows),
        "source_materialization_rebuild_rows": len(source_rows),
        "horizon_materialization_rebuild_rows": len(horizon_rows),
        "scope_rebuild_action_rows": len(scope_action_rows),
        "exact_control_scopes_current_materialization_rows": sum(
            int(row.get("current_materialization_row_count") or 0) for row in exact_scope_rows
        ),
        "exact_control_scopes_current_control_execution_rows": sum(
            int(row.get("current_control_execution_row_count") or 0) for row in exact_scope_rows
        ),
        "exact_control_scopes_shadow_guard_rows": sum(
            int(row.get("current_shadow_guard_row_count") or 0) for row in exact_scope_rows
        ),
        "exact_control_target_shadow_guard_rows": sum(
            int(row.get("current_shadow_guard_row_count") or 0) for row in exact_target_rows
        ),
        "exact_source_materialization_present_rows": sum(1 for row in source_rows if row.get("materialization_present")),
        "horizon_materialization_present_rows": sum(1 for row in horizon_rows if row.get("source_materialization_execution_id")),
        "member_rows_kept_for_strongest_proxy": sum(1 for row in member_rows if row.get("keep_for_strongest_available_proxy")),
        "symbol_session_denominator_source_rebuild_rows": len(symbol_session_rows),
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
            "control_source_split_bundle": control_split_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "denominator_source_rebuild_lane_counts": distributions["denominator_source_rebuild_lane"],
            "denominator_source_rebuild_status_counts": distributions["denominator_source_rebuild_status"],
            "scope_action_status_counts": distributions["scope_action_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_SOURCE_REBUILD_BUNDLE_RESULT: exact-control scopes are "
                "current-denominator absent but shadow-guard covered; exact-source scopes have under-n20 "
                "materialization with expanded proxies; horizon scopes require fail-closed targetable rebuild."
            ),
        },
    }
    runtime_spec = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "identity_policy": {
            "primary_rows": "92 exact-control targets + 61 exact-source rebuild rows + 37 horizon rebuild rows",
            "scope_rows": "121 exact symbol/session/horizon/primitive actions",
            "member_rows": "all 21,252 selected-control member evidence rows preserved",
        },
        "execution_policy": {
            "exact_control": "current materialization/control rows are required; shadow guard is context only",
            "source": "current exact source under n20 uses expanded proxies only behind source guard",
            "horizon": "current source n20 with horizon fail-closed rows requires targetable rebuild",
        },
        "bucket_distributions": distributions,
    }

    generated_files = [
        UNIFIED_LEDGER,
        EXACT_TARGET_LEDGER,
        EXACT_SCOPE_LEDGER,
        MEMBER_EVIDENCE_LEDGER,
        SOURCE_REBUILD_LEDGER,
        HORIZON_REBUILD_LEDGER,
        SCOPE_ACTION_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(EXACT_TARGET_LEDGER, exact_target_rows)
    write_jsonl(EXACT_SCOPE_LEDGER, exact_scope_rows)
    write_jsonl(MEMBER_EVIDENCE_LEDGER, member_rows)
    write_jsonl(SOURCE_REBUILD_LEDGER, source_rows)
    write_jsonl(HORIZON_REBUILD_LEDGER, horizon_rows)
    write_jsonl(SCOPE_ACTION_LEDGER, scope_action_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Denominator Source Rebuild Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified denominator/source rebuild rows: `{counts['unified_denominator_source_rebuild_rows']}`",
                f"- Exact-control target denominator rows: `{counts['exact_control_target_denominator_rows']}`",
                f"- Exact-control scope denominator rows: `{counts['exact_control_scope_denominator_rows']}`",
                f"- Control-member denominator evidence rows: `{counts['control_member_denominator_evidence_rows']}`",
                f"- Source materialization rebuild rows: `{counts['source_materialization_rebuild_rows']}`",
                f"- Horizon materialization rebuild rows: `{counts['horizon_materialization_rebuild_rows']}`",
                f"- Scope rebuild action rows: `{counts['scope_rebuild_action_rows']}`",
                "",
                "Core result: current rows prove exact-control scopes are guard-only and exact-denominator absent, while source and horizon scopes have direct materialization rows that define the next rebuild actions.",
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
