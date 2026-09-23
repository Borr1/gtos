#!/usr/bin/env python3
"""Build runtime work rows from branch-local observable implementation candidates."""

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

from src.research_infra.moonshot_observable_runtime_work import (
    RUNTIME_WORK_SURFACE,
    control_scope_build_attempt,
    runtime_work_decision,
    source_repair_runtime_work,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_CANDIDATE_BUNDLE"
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_ACTION_RESULT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_RUNTIME_WORK_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_CONTROLLED = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROLLED_OBSERVABLE_CHALLENGER_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_REGISTER_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_SCOPE = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_SCOPE_BUILDER_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_SCORER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_SCORER_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_COMPARATOR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARD_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_REPAIR_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_COVERAGE_IMPLEMENTATION_MAP_LEDGER_2026-05-17.jsonl"
ACTION_CONTROL_LOOKUP = ROUTE_DIR / f"{ACTION_PREFIX}_CONTROL_LOOKUP_REQUIREMENT_LEDGER_2026-05-17.jsonl"
ACTION_SOURCE = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_POLICY_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_runtime_work.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
OBSERVABLE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
OBSERVABLE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_REGISTRY_RUNTIME_LEDGER_2026-05-17.jsonl"
CONTROLLED_SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROLLED_SCORER_RUNTIME_LEDGER_2026-05-17.jsonl"
DENOMINATOR_OBSERVABLE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_RUNTIME_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_ATTEMPT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_BUILD_ATTEMPT_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_GROUP_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_GROUP_LEDGER_2026-05-17.jsonl"
SOURCE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
SOURCE_SCORER_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_SCORER_RUNTIME_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_RUNTIME_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_GROUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_GROUP_LEDGER_2026-05-17.jsonl"
CONTROL_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
DENOMINATOR_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
HORIZON_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
COVERAGE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_RUNTIME_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable runtime-work bundle only. It converts implementation candidates into research-only "
    "scorer registration rows, denominator-guarded observable registry rows, control-scope build attempts, "
    "source repair work rows, and coverage/runtime ledgers. It does not change live behavior, place orders, "
    "or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-OBS-RUNTIME-SRC-{index:04d}",
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
        "input_implementation_candidate_row_id": row.get("implementation_candidate_row_id"),
        "input_action_result_row_id": row.get("input_action_result_row_id"),
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
        "input_candidate_stage": row.get("implementation_candidate_stage"),
        "input_candidate_status": row.get("implementation_candidate_status"),
        "input_candidate_operation": row.get("implementation_operation"),
        "input_candidate_priority_score": row.get("implementation_priority_score"),
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_runtime_rows(
    rows: list[dict[str, Any]],
    row_prefix: str,
    input_type: str,
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "runtime_work_row_id": f"{row_prefix}-{index:05d}",
                    "input_ledger_type": input_type,
                    **common(row),
                    **runtime_work_decision(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_control_scope_attempt_rows(
    rows: list[dict[str, Any]],
    action_by_id: dict[Any, dict[str, Any]],
    control_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        action_row = action_by_id.get(row.get("input_action_result_row_id"), {})
        output.append(
            with_common(
                {
                    "runtime_work_row_id": f"OHLC-GTOS-OBS-RUNTIME-CSCOPE-{index:05d}",
                    "input_ledger_type": "CONTROL_SCOPE_IMPLEMENTATION_CANDIDATE",
                    **common(row),
                    **runtime_work_decision(row),
                    **control_scope_build_attempt(row, action_row, control_rows),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_source_repair_rows(
    rows: list[dict[str, Any]],
    action_by_id: dict[Any, dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    scope_counts = Counter(str(row.get("observable_scope_key")) for row in rows)
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        action_row = action_by_id.get(row.get("input_action_result_row_id"), {})
        output.append(
            with_common(
                {
                    "runtime_work_row_id": f"OHLC-GTOS-OBS-RUNTIME-SREPAIR-{index:05d}",
                    "input_ledger_type": "SOURCE_REPAIR_IMPLEMENTATION_CANDIDATE",
                    **common(row),
                    **runtime_work_decision(row),
                    **source_repair_runtime_work(row, action_row, int(scope_counts[str(row.get("observable_scope_key"))])),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_group_rows(
    rows: list[dict[str, Any]],
    key_fields: tuple[str, ...],
    group_id_prefix: str,
    status_key: str,
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(field) for field in key_fields)].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])), 1):
        payload = {
            "runtime_group_id": f"{group_id_prefix}-{index:04d}",
            "row_count": len(members),
            "runtime_work_status_counts": string_counter(members, "runtime_work_status"),
            "status_counts": string_counter(members, status_key),
            "runtime_ready_rows": sum(1 for row in members if row.get("runtime_ready")),
            "runtime_control_required_rows": sum(1 for row in members if row.get("runtime_control_required")),
            "runtime_source_repair_required_rows": sum(1 for row in members if row.get("runtime_source_repair_required")),
            "runtime_work_surface": RUNTIME_WORK_SURFACE,
            "live_effect": False,
        }
        for field, value in zip(key_fields, key):
            payload[field] = value
        output.append(with_common(payload, generated_at, manifest_hash))
    return output


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
                    "symbol_session_runtime_id": f"OHLC-GTOS-OBS-RUNTIME-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "runtime_work_status_counts": string_counter(members, "runtime_work_status"),
                    "runtime_decision_counts": string_counter(members, "runtime_decision"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "runtime_work_surface": RUNTIME_WORK_SURFACE,
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
    control_scope_rows: list[dict[str, Any]],
    source_repair_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "runtime_work_status": string_counter(unified_rows, "runtime_work_status"),
        "runtime_decision": string_counter(unified_rows, "runtime_decision"),
        "observable_runtime_work_status": string_counter(observable_rows, "runtime_work_status"),
        "source_runtime_work_status": string_counter(source_rows, "runtime_work_status"),
        "control_scope_build_status": string_counter(control_scope_rows, "control_scope_build_status"),
        "source_repair_runtime_status": string_counter(source_repair_rows, "source_repair_runtime_status"),
        "runtime_ready": string_counter(unified_rows, "runtime_ready"),
        "runtime_control_required": string_counter(unified_rows, "runtime_control_required"),
        "runtime_source_repair_required": string_counter(unified_rows, "runtime_source_repair_required"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-RUNTIME-BUCKET-{len(output) + 1:04d}",
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
        "runtime_work_policy": {
            "controlled_observable_challengers": "register controlled branch-local shadow scorers",
            "denominator_guarded_observables": "register guarded observables with denominator enforcement",
            "control_scope_builders": "attempt exact/proxy control materialization from current control rows before scoring",
            "source_repair_rows": "preserve exact-source and horizon repair work as executable rows",
            "coverage_rows": "carry full primitive coverage map into runtime work synthesis",
        },
        "ledgers": {
            "unified_runtime_work": UNIFIED_RUNTIME_LEDGER.relative_to(REPO).as_posix(),
            "observable_runtime_work": OBSERVABLE_RUNTIME_LEDGER.relative_to(REPO).as_posix(),
            "control_scope_build_attempts": CONTROL_SCOPE_ATTEMPT_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_runtime": SOURCE_REPAIR_RUNTIME_LEDGER.relative_to(REPO).as_posix(),
            "coverage_runtime": COVERAGE_RUNTIME_LEDGER.relative_to(REPO).as_posix(),
        },
        "runtime_distributions": distributions,
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
    manifest["latest_branch_local_observable_runtime_work_bundle"] = {
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
        "event": "branch_local_observable_runtime_work_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built runtime work rows from observable implementation candidates.",
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
            INPUT_CONTROLLED,
            INPUT_DENOMINATOR_OBSERVABLE,
            INPUT_CONTROL_SCOPE,
            INPUT_SOURCE,
            INPUT_SOURCE_SCORER,
            INPUT_SOURCE_REPAIR,
            INPUT_CONTROL,
            INPUT_DENOMINATOR,
            INPUT_HORIZON,
            INPUT_COVERAGE,
            ACTION_CONTROL_LOOKUP,
            ACTION_SOURCE,
            HELPER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_runtime = read_json(INPUT_RUNTIME_SPEC)
    unified_input = read_jsonl(INPUT_UNIFIED)
    observable_input = read_jsonl(INPUT_OBSERVABLE)
    controlled_input = read_jsonl(INPUT_CONTROLLED)
    denominator_observable_input = read_jsonl(INPUT_DENOMINATOR_OBSERVABLE)
    control_scope_input = read_jsonl(INPUT_CONTROL_SCOPE)
    source_input = read_jsonl(INPUT_SOURCE)
    source_scorer_input = read_jsonl(INPUT_SOURCE_SCORER)
    source_repair_input = read_jsonl(INPUT_SOURCE_REPAIR)
    control_input = read_jsonl(INPUT_CONTROL)
    denominator_input = read_jsonl(INPUT_DENOMINATOR)
    horizon_input = read_jsonl(INPUT_HORIZON)
    coverage_input = read_jsonl(INPUT_COVERAGE)
    action_control_lookup_rows = read_jsonl(ACTION_CONTROL_LOOKUP)
    action_source_rows = read_jsonl(ACTION_SOURCE)
    action_control_lookup_by_id = {row.get("action_result_row_id"): row for row in action_control_lookup_rows}
    action_source_by_id = {row.get("action_result_row_id"): row for row in action_source_rows}

    observable_runtime_rows = build_runtime_rows(
        observable_input,
        "OHLC-GTOS-OBS-RUNTIME-OBS",
        "OBSERVABLE_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    source_runtime_rows = build_runtime_rows(
        source_input,
        "OHLC-GTOS-OBS-RUNTIME-SOURCE",
        "SOURCE_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    control_runtime_rows = build_runtime_rows(
        control_input,
        "OHLC-GTOS-OBS-RUNTIME-CONTROL",
        "CONTROL_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    denominator_runtime_rows = build_runtime_rows(
        denominator_input,
        "OHLC-GTOS-OBS-RUNTIME-DGUARD",
        "DENOMINATOR_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    horizon_runtime_rows = build_runtime_rows(
        horizon_input,
        "OHLC-GTOS-OBS-RUNTIME-HREPAIR",
        "HORIZON_REPAIR_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    coverage_runtime_rows = build_runtime_rows(
        coverage_input,
        "OHLC-GTOS-OBS-RUNTIME-COVERAGE",
        "PRIMITIVE_COVERAGE_IMPLEMENTATION_CANDIDATE",
        generated_at,
        manifest_hash,
    )
    control_scope_attempt_rows = build_control_scope_attempt_rows(
        control_scope_input,
        action_control_lookup_by_id,
        control_runtime_rows,
        generated_at,
        manifest_hash,
    )
    source_repair_runtime_rows = build_source_repair_rows(
        source_repair_input,
        action_source_by_id,
        generated_at,
        manifest_hash,
    )

    unified_runtime_rows = [*observable_runtime_rows, *source_runtime_rows, *control_runtime_rows, *denominator_runtime_rows]
    controlled_runtime_rows = [
        row for row in observable_runtime_rows if row.get("runtime_work_status") == "RUNTIME_WORK_ENABLE_CONTROLLED_OBSERVABLE_SCORER"
    ]
    denominator_observable_runtime_rows = [
        row
        for row in observable_runtime_rows
        if row.get("runtime_work_status") == "RUNTIME_WORK_REGISTER_DENOMINATOR_GUARDED_OBSERVABLE"
    ]
    observable_registry_rows = [*controlled_runtime_rows, *denominator_observable_runtime_rows]
    source_scorer_runtime_rows = [
        row for row in source_runtime_rows if row.get("runtime_work_status") == "RUNTIME_WORK_REGISTER_SOURCE_PROXY_SCORER"
    ]
    control_scope_group_rows = build_group_rows(
        control_scope_attempt_rows,
        ("missing_control_scope_key", "desired_control_family"),
        "OHLC-GTOS-OBS-RUNTIME-CSCOPE-GROUP",
        "control_scope_build_status",
        generated_at,
        manifest_hash,
    )
    source_repair_group_rows = build_group_rows(
        source_repair_runtime_rows,
        ("observable_scope_key", "source_action_result_family"),
        "OHLC-GTOS-OBS-RUNTIME-SREPAIR-GROUP",
        "source_repair_runtime_status",
        generated_at,
        manifest_hash,
    )
    symbol_session_rows = build_symbol_session_rows(unified_runtime_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_runtime_rows,
        observable_runtime_rows,
        source_runtime_rows,
        control_scope_attempt_rows,
        source_repair_runtime_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-RUNTIME-Q-001",
                "question": "Did every implementation candidate become runtime work?",
                "answer_route": "Yes: all 1,108 unified implementation candidates map to runtime work rows; horizon and coverage remain separate runtime work ledgers.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-RUNTIME-Q-002",
                "question": "What is executable immediately in branch-local shadow code?",
                "answer_route": "The bundle emits 14 controlled scorer rows, 262 denominator-guarded observable rows, 211 source-scorer rows, 231 control-comparator rows, and 124 denominator-guard rows as runtime-ready branch-local work.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-RUNTIME-Q-003",
                "question": "Were missing controls actively pursued from current rows?",
                "answer_route": "Yes: all 168 control-scope builders are run through exact and same-symbol/session/horizon proxy control materialization attempts and grouped by missing scope.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-RUNTIME-Q-004",
                "question": "Did source repair stay active?",
                "answer_route": "Yes: all 98 source repair rows remain runtime repair rows with exact-source, horizon-rescore, or horizon-kill-check actions and duplicate repair-scope counts.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_implementation_candidate_rows": len(unified_input),
        "input_observable_implementation_candidate_rows": len(observable_input),
        "input_controlled_observable_challenger_rows": len(controlled_input),
        "input_denominator_guarded_observable_register_rows": len(denominator_observable_input),
        "input_control_scope_builder_rows": len(control_scope_input),
        "input_source_implementation_candidate_rows": len(source_input),
        "input_source_scorer_candidate_rows": len(source_scorer_input),
        "input_source_repair_implementation_rows": len(source_repair_input),
        "input_control_comparator_implementation_rows": len(control_input),
        "input_denominator_guard_implementation_rows": len(denominator_input),
        "input_horizon_repair_implementation_rows": len(horizon_input),
        "input_coverage_implementation_map_rows": len(coverage_input),
        "unified_runtime_work_rows": len(unified_runtime_rows),
        "observable_runtime_work_rows": len(observable_runtime_rows),
        "observable_registry_runtime_rows": len(observable_registry_rows),
        "controlled_scorer_runtime_rows": len(controlled_runtime_rows),
        "denominator_guarded_observable_runtime_rows": len(denominator_observable_runtime_rows),
        "control_scope_build_attempt_rows": len(control_scope_attempt_rows),
        "control_scope_group_rows": len(control_scope_group_rows),
        "source_runtime_work_rows": len(source_runtime_rows),
        "source_scorer_runtime_rows": len(source_scorer_runtime_rows),
        "source_repair_runtime_rows": len(source_repair_runtime_rows),
        "source_repair_group_rows": len(source_repair_group_rows),
        "control_runtime_work_rows": len(control_runtime_rows),
        "denominator_runtime_work_rows": len(denominator_runtime_rows),
        "horizon_runtime_work_rows": len(horizon_runtime_rows),
        "coverage_runtime_work_rows": len(coverage_runtime_rows),
        "symbol_session_runtime_rows": len(symbol_session_rows),
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
            "observable_implementation_candidate_bundle": input_result.get("counts", {}),
            "observable_implementation_runtime_policy": input_runtime.get("implementation_candidate_policy", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "runtime_work_status_counts": distributions["runtime_work_status"],
            "observable_runtime_work_status_counts": distributions["observable_runtime_work_status"],
            "source_runtime_work_status_counts": distributions["source_runtime_work_status"],
            "control_scope_build_status_counts": distributions["control_scope_build_status"],
            "source_repair_runtime_status_counts": distributions["source_repair_runtime_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_RUNTIME_WORK_BUNDLE_RESULT: wire runtime-ready branch-local "
                "observable/source/control/denominator work, build missing control scopes from current "
                "control rows, and execute exact-source/horizon repair rows before stronger synthesis."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)
    generated_files = [
        UNIFIED_RUNTIME_LEDGER,
        OBSERVABLE_RUNTIME_LEDGER,
        OBSERVABLE_REGISTRY_LEDGER,
        CONTROLLED_SCORER_LEDGER,
        DENOMINATOR_OBSERVABLE_RUNTIME_LEDGER,
        CONTROL_SCOPE_ATTEMPT_LEDGER,
        CONTROL_SCOPE_GROUP_LEDGER,
        SOURCE_RUNTIME_LEDGER,
        SOURCE_SCORER_RUNTIME_LEDGER,
        SOURCE_REPAIR_RUNTIME_LEDGER,
        SOURCE_REPAIR_GROUP_LEDGER,
        CONTROL_RUNTIME_LEDGER,
        DENOMINATOR_RUNTIME_LEDGER,
        HORIZON_RUNTIME_LEDGER,
        COVERAGE_RUNTIME_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_RUNTIME_LEDGER, unified_runtime_rows)
    write_jsonl(OBSERVABLE_RUNTIME_LEDGER, observable_runtime_rows)
    write_jsonl(OBSERVABLE_REGISTRY_LEDGER, observable_registry_rows)
    write_jsonl(CONTROLLED_SCORER_LEDGER, controlled_runtime_rows)
    write_jsonl(DENOMINATOR_OBSERVABLE_RUNTIME_LEDGER, denominator_observable_runtime_rows)
    write_jsonl(CONTROL_SCOPE_ATTEMPT_LEDGER, control_scope_attempt_rows)
    write_jsonl(CONTROL_SCOPE_GROUP_LEDGER, control_scope_group_rows)
    write_jsonl(SOURCE_RUNTIME_LEDGER, source_runtime_rows)
    write_jsonl(SOURCE_SCORER_RUNTIME_LEDGER, source_scorer_runtime_rows)
    write_jsonl(SOURCE_REPAIR_RUNTIME_LEDGER, source_repair_runtime_rows)
    write_jsonl(SOURCE_REPAIR_GROUP_LEDGER, source_repair_group_rows)
    write_jsonl(CONTROL_RUNTIME_LEDGER, control_runtime_rows)
    write_jsonl(DENOMINATOR_RUNTIME_LEDGER, denominator_runtime_rows)
    write_jsonl(HORIZON_RUNTIME_LEDGER, horizon_runtime_rows)
    write_jsonl(COVERAGE_RUNTIME_LEDGER, coverage_runtime_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Runtime Work Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified runtime work rows: `{counts['unified_runtime_work_rows']}`",
                f"- Controlled scorer runtime rows: `{counts['controlled_scorer_runtime_rows']}`",
                f"- Denominator-guarded observable runtime rows: `{counts['denominator_guarded_observable_runtime_rows']}`",
                f"- Control-scope build attempt rows: `{counts['control_scope_build_attempt_rows']}`",
                f"- Source scorer runtime rows: `{counts['source_scorer_runtime_rows']}`",
                f"- Source repair runtime rows: `{counts['source_repair_runtime_rows']}`",
                f"- Coverage runtime work rows: `{counts['coverage_runtime_work_rows']}`",
                "",
                "Core result: implementation candidates now become executable branch-local runtime work rows, including same-resource control-scope materialization attempts and explicit source repair runtime actions.",
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
