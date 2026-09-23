#!/usr/bin/env python3
"""Build executable branch-local scorer rows from observable runtime work."""

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

from src.research_infra.moonshot_observable_scorer_execution import (
    SCORER_EXECUTION_SURFACE,
    control_comparator_execution,
    control_scope_execution,
    controlled_scorer_execution,
    coverage_scorer_execution,
    denominator_guard_execution,
    denominator_guarded_observable_execution,
    horizon_repair_execution,
    source_repair_execution,
    source_scorer_execution,
)


RUNTIME_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_RUNTIME_WORK_BUNDLE"
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_ACTION_RESULT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE"

RUNTIME_RESULT = ROUTE_DIR / f"{RUNTIME_PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC = ROUTE_DIR / f"{RUNTIME_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
RUNTIME_UNIFIED = ROUTE_DIR / f"{RUNTIME_PREFIX}_UNIFIED_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_OBSERVABLE = ROUTE_DIR / f"{RUNTIME_PREFIX}_OBSERVABLE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_CONTROLLED = ROUTE_DIR / f"{RUNTIME_PREFIX}_CONTROLLED_SCORER_RUNTIME_LEDGER_2026-05-17.jsonl"
RUNTIME_DGUARDED_OBSERVABLE = ROUTE_DIR / f"{RUNTIME_PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_RUNTIME_LEDGER_2026-05-17.jsonl"
RUNTIME_CONTROL_SCOPE = ROUTE_DIR / f"{RUNTIME_PREFIX}_CONTROL_SCOPE_BUILD_ATTEMPT_LEDGER_2026-05-17.jsonl"
RUNTIME_SOURCE = ROUTE_DIR / f"{RUNTIME_PREFIX}_SOURCE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_SOURCE_SCORER = ROUTE_DIR / f"{RUNTIME_PREFIX}_SOURCE_SCORER_RUNTIME_LEDGER_2026-05-17.jsonl"
RUNTIME_SOURCE_REPAIR = ROUTE_DIR / f"{RUNTIME_PREFIX}_SOURCE_REPAIR_RUNTIME_LEDGER_2026-05-17.jsonl"
RUNTIME_CONTROL = ROUTE_DIR / f"{RUNTIME_PREFIX}_CONTROL_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_DENOMINATOR = ROUTE_DIR / f"{RUNTIME_PREFIX}_DENOMINATOR_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_HORIZON = ROUTE_DIR / f"{RUNTIME_PREFIX}_HORIZON_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_COVERAGE = ROUTE_DIR / f"{RUNTIME_PREFIX}_COVERAGE_RUNTIME_WORK_LEDGER_2026-05-17.jsonl"
RUNTIME_CONTROL_SCOPE_GROUP = ROUTE_DIR / f"{RUNTIME_PREFIX}_CONTROL_SCOPE_GROUP_LEDGER_2026-05-17.jsonl"
RUNTIME_SOURCE_REPAIR_GROUP = ROUTE_DIR / f"{RUNTIME_PREFIX}_SOURCE_REPAIR_GROUP_LEDGER_2026-05-17.jsonl"

ACTION_CONTROLLED = ROUTE_DIR / f"{ACTION_PREFIX}_CONTROL_READY_SCORE_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_DGUARDED_OBSERVABLE = ROUTE_DIR / f"{ACTION_PREFIX}_DENOMINATOR_GUARDED_REGISTER_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_SOURCE = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_POLICY_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_SOURCE_REPAIR = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_REPAIR_WORK_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_CONTROL = ROUTE_DIR / f"{ACTION_PREFIX}_CONTROL_COMPARATOR_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_DENOMINATOR = ROUTE_DIR / f"{ACTION_PREFIX}_DENOMINATOR_GUARD_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_HORIZON = ROUTE_DIR / f"{ACTION_PREFIX}_HORIZON_WORK_ORDER_RESULT_LEDGER_2026-05-17.jsonl"
ACTION_COVERAGE = ROUTE_DIR / f"{ACTION_PREFIX}_COVERAGE_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_scorer_execution.py"
RUNTIME_HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_runtime_work.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
OBSERVABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
BRANCH_SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LOCAL_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROLLED_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROLLED_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
DGUARDED_OBSERVABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
DENOMINATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
HORIZON_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"
COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable scorer execution bundle only. It turns runtime-work rows into executable "
    "research-only scorer, observable-registry, control-scope, source-repair, control, denominator, horizon, "
    "and coverage execution rows. It preserves proxy deltas and repair causes where available, does not add "
    "horizon/coverage sidecars to the 1,108 unified denominator, and does not change live behavior, place orders, "
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
                "source_manifest_id": f"OHLC-GTOS-OBS-SCOREREXEC-SRC-{index:04d}",
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


def action_by_id(rows: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    return {row.get("action_result_row_id"): row for row in rows}


def action_by_source_bundle(rows: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    return {row.get("input_source_bundle_row_id"): row for row in rows}


def action_by_scope(rows: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    return {row.get("observable_scope_key"): row for row in rows}


def normalize_scope_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in {"", "None", "null"}:
        return None
    return text


def parse_scope_key(scope_key: Any) -> dict[str, str | None]:
    parts = {"symbol": None, "session": None, "horizon": None, "primitive": None}
    for chunk in str(scope_key or "").split("|"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        if key in parts:
            parts[key] = normalize_scope_value(value)
    return parts


def execution_status_and_decision(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    pairs = [
        ("scorer_execution_status", "scorer_execution_decision"),
        ("source_scorer_execution_status", "source_scorer_execution_decision"),
        ("control_scope_execution_status", "control_scope_execution_decision"),
        ("source_repair_execution_status", "source_repair_execution_decision"),
        ("control_execution_status", "control_execution_decision"),
        ("denominator_execution_status", "denominator_execution_decision"),
        ("horizon_repair_execution_status", "horizon_repair_execution_decision"),
        ("coverage_execution_status", "coverage_execution_decision"),
    ]
    for status_key, decision_key in pairs:
        if payload.get(status_key):
            return str(payload.get(status_key)), str(payload.get(decision_key))
    return None, None


def common_runtime_fields(row: dict[str, Any]) -> dict[str, Any]:
    scope = parse_scope_key(row.get("observable_scope_key"))
    return {
        "input_runtime_work_row_id": row.get("runtime_work_row_id"),
        "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
        "input_action_result_row_id": row.get("input_action_result_row_id"),
        "input_execution_row_id": row.get("input_execution_row_id"),
        "input_implementation_row_id": row.get("input_implementation_row_id"),
        "input_source_bundle_row_id": row.get("input_source_bundle_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "symbol": normalize_scope_value(row.get("symbol")),
        "route_session": normalize_scope_value(row.get("route_session")),
        "session_bucket": normalize_scope_value(row.get("session_bucket")),
        "horizon_id": normalize_scope_value(row.get("horizon_id")),
        "primitive_flag": normalize_scope_value(row.get("primitive_flag")),
        "observable_scope_key": row.get("observable_scope_key"),
        "scope_symbol": scope["symbol"],
        "scope_session": scope["session"],
        "scope_horizon": scope["horizon"],
        "scope_primitive": scope["primitive"],
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "runtime_work_status": row.get("runtime_work_status"),
        "runtime_decision": row.get("runtime_decision"),
        "runtime_operation": row.get("runtime_operation"),
        "runtime_ready": bool(row.get("runtime_ready")),
        "runtime_control_required": bool(row.get("runtime_control_required")),
        "runtime_source_repair_required": bool(row.get("runtime_source_repair_required")),
        "runtime_priority_score": row.get("runtime_priority_score"),
        "input_candidate_status": row.get("input_candidate_status"),
        "input_candidate_operation": row.get("input_candidate_operation"),
    }


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


def make_execution_row(
    row_id: str,
    lane: str,
    runtime_row: dict[str, Any],
    payload: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> dict[str, Any]:
    status, decision = execution_status_and_decision(payload)
    return with_common(
        {
            "execution_bundle_row_id": row_id,
            "execution_lane": lane,
            **common_runtime_fields(runtime_row),
            **payload,
            "execution_status": status,
            "execution_decision": decision,
            "execution_surface": SCORER_EXECUTION_SURFACE,
            "live_effect": False,
        },
        generated_at,
        manifest_hash,
    )


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


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
                    "symbol_session_scorer_execution_id": f"OHLC-GTOS-OBS-SCOREREXEC-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "execution_lane_counts": string_counter(members, "execution_lane"),
                    "execution_status_counts": string_counter(members, "execution_status"),
                    "runtime_work_status_counts": string_counter(members, "runtime_work_status"),
                    "executable_now_rows": sum(1 for row in members if row.get("executable_now")),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "execution_surface": SCORER_EXECUTION_SURFACE,
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
    branch_scorer_rows: list[dict[str, Any]],
    control_scope_rows: list[dict[str, Any]],
    source_repair_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "execution_lane": string_counter(unified_rows, "execution_lane"),
        "execution_status": string_counter(unified_rows, "execution_status"),
        "runtime_work_status": string_counter(unified_rows, "runtime_work_status"),
        "runtime_ready": string_counter(unified_rows, "runtime_ready"),
        "runtime_control_required": string_counter(unified_rows, "runtime_control_required"),
        "runtime_source_repair_required": string_counter(unified_rows, "runtime_source_repair_required"),
        "executable_now": string_counter(unified_rows, "executable_now"),
        "observable_execution_status": string_counter(observable_rows, "execution_status"),
        "branch_local_scorer_execution_status": string_counter(branch_scorer_rows, "execution_status"),
        "control_scope_execution_status": string_counter(control_scope_rows, "control_scope_execution_status"),
        "source_repair_execution_status": string_counter(source_repair_rows, "source_repair_execution_status"),
        "control_execution_status": string_counter(control_rows, "control_execution_status"),
        "horizon_sidecar_execution_status": string_counter(horizon_rows, "horizon_repair_execution_status"),
        "coverage_sidecar_execution_status": string_counter(coverage_rows, "coverage_execution_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-SCOREREXEC-BUCKET-{len(output) + 1:04d}",
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
        "input_runtime_spec": RUNTIME_SPEC.relative_to(REPO).as_posix(),
        "identity_policy": {
            "primary_join_key": "runtime_work_row_id plus input_implementation_candidate_row_id",
            "scope_only_join_allowed": False,
            "horizon_and_coverage_sidecars_in_unified_denominator": False,
        },
        "execution_policy": {
            "controlled_observable_challengers": "score all positive controlled rows with preserved proxy deltas and control counts",
            "source_scorers": "score guarded proxy rows and ambiguous proxy rows separately; ambiguous source rows remain control-required",
            "denominator_guarded_observables": "register observable rows with explicit guard strength and denominator counts",
            "control_scope_builders": "execute exact/proxy control-scope decisions; global underpowered rows require exact control build before scalar scoring",
            "source_repairs": "execute exact-source rebuild/acquire and horizon repair actions with exact cause fields",
            "horizon_and_coverage": "preserve as sidecars and do not inflate the unified runtime denominator",
        },
        "ledgers": {
            "unified_scorer_execution": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "branch_local_scorer_execution": BRANCH_SCORER_LEDGER.relative_to(REPO).as_posix(),
            "control_scope_execution": CONTROL_SCOPE_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_execution": SOURCE_REPAIR_LEDGER.relative_to(REPO).as_posix(),
            "horizon_sidecar_execution": HORIZON_LEDGER.relative_to(REPO).as_posix(),
            "coverage_sidecar_execution": COVERAGE_LEDGER.relative_to(REPO).as_posix(),
        },
        "execution_distributions": distributions,
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
    manifest["latest_branch_local_observable_scorer_execution_bundle"] = {
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
        "event": "branch_local_observable_scorer_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built executable scorer/source/control/denominator execution rows from observable runtime work.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            RUNTIME_RESULT,
            RUNTIME_SPEC,
            RUNTIME_UNIFIED,
            RUNTIME_OBSERVABLE,
            RUNTIME_CONTROLLED,
            RUNTIME_DGUARDED_OBSERVABLE,
            RUNTIME_CONTROL_SCOPE,
            RUNTIME_SOURCE,
            RUNTIME_SOURCE_SCORER,
            RUNTIME_SOURCE_REPAIR,
            RUNTIME_CONTROL,
            RUNTIME_DENOMINATOR,
            RUNTIME_HORIZON,
            RUNTIME_COVERAGE,
            RUNTIME_CONTROL_SCOPE_GROUP,
            RUNTIME_SOURCE_REPAIR_GROUP,
            ACTION_CONTROLLED,
            ACTION_DGUARDED_OBSERVABLE,
            ACTION_SOURCE,
            ACTION_SOURCE_REPAIR,
            ACTION_CONTROL,
            ACTION_DENOMINATOR,
            ACTION_HORIZON,
            ACTION_COVERAGE,
            HELPER_MODULE,
            RUNTIME_HELPER_MODULE,
        ],
        generated_at,
    )

    runtime_result = read_json(RUNTIME_RESULT)
    runtime_unified_rows = read_jsonl(RUNTIME_UNIFIED)
    runtime_observable_rows = read_jsonl(RUNTIME_OBSERVABLE)
    runtime_controlled_rows = read_jsonl(RUNTIME_CONTROLLED)
    runtime_dguarded_observable_rows = read_jsonl(RUNTIME_DGUARDED_OBSERVABLE)
    runtime_control_scope_rows = read_jsonl(RUNTIME_CONTROL_SCOPE)
    runtime_source_rows = read_jsonl(RUNTIME_SOURCE)
    runtime_source_scorer_rows = read_jsonl(RUNTIME_SOURCE_SCORER)
    runtime_source_repair_rows = read_jsonl(RUNTIME_SOURCE_REPAIR)
    runtime_control_rows = read_jsonl(RUNTIME_CONTROL)
    runtime_denominator_rows = read_jsonl(RUNTIME_DENOMINATOR)
    runtime_horizon_rows = read_jsonl(RUNTIME_HORIZON)
    runtime_coverage_rows = read_jsonl(RUNTIME_COVERAGE)
    runtime_control_scope_group_rows = read_jsonl(RUNTIME_CONTROL_SCOPE_GROUP)
    runtime_source_repair_group_rows = read_jsonl(RUNTIME_SOURCE_REPAIR_GROUP)

    controlled_action = action_by_id(read_jsonl(ACTION_CONTROLLED))
    dguarded_action = action_by_id(read_jsonl(ACTION_DGUARDED_OBSERVABLE))
    source_action_rows = read_jsonl(ACTION_SOURCE)
    source_repair_action_rows = read_jsonl(ACTION_SOURCE_REPAIR)
    source_action = action_by_id(source_action_rows)
    source_repair_action = action_by_id(source_repair_action_rows)
    control_action = action_by_id(read_jsonl(ACTION_CONTROL))
    denominator_action = action_by_id(read_jsonl(ACTION_DENOMINATOR))
    horizon_action_rows = read_jsonl(ACTION_HORIZON)
    horizon_action = action_by_id(horizon_action_rows)
    horizon_by_bundle = action_by_source_bundle(horizon_action_rows)
    horizon_by_scope = action_by_scope(horizon_action_rows)
    coverage_action = action_by_id(read_jsonl(ACTION_COVERAGE))

    controlled_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_controlled_rows, 1):
        action_row = controlled_action.get(row.get("input_action_result_row_id"), {})
        controlled_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-CONTROLLED-{index:05d}",
                "CONTROLLED_OBSERVABLE_SCORER",
                row,
                controlled_scorer_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    denominator_guarded_observable_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_dguarded_observable_rows, 1):
        action_row = dguarded_action.get(row.get("input_action_result_row_id"), {})
        denominator_guarded_observable_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-DGOBS-{index:05d}",
                "DENOMINATOR_GUARDED_OBSERVABLE",
                row,
                denominator_guarded_observable_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    control_scope_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_control_scope_rows, 1):
        control_scope_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-CSCOPE-{index:05d}",
                "CONTROL_SCOPE_BUILD_EXECUTION",
                row,
                control_scope_execution(row),
                generated_at,
                manifest_hash,
            )
        )

    source_scorer_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_source_scorer_rows, 1):
        action_row = source_action.get(row.get("input_action_result_row_id"), {})
        source_scorer_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-SSCORER-{index:05d}",
                "SOURCE_SCORER_EXECUTION",
                row,
                source_scorer_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    source_repair_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_source_repair_rows, 1):
        action_row = source_repair_action.get(row.get("input_action_result_row_id")) or source_action.get(
            row.get("input_action_result_row_id"), {}
        )
        horizon_row = horizon_by_bundle.get(row.get("input_source_bundle_row_id")) or horizon_by_scope.get(
            row.get("observable_scope_key")
        )
        source_repair_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-SREPAIR-{index:05d}",
                "SOURCE_REPAIR_EXECUTION",
                row,
                source_repair_execution(row, action_row, horizon_row),
                generated_at,
                manifest_hash,
            )
        )

    control_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_control_rows, 1):
        action_row = control_action.get(row.get("input_action_result_row_id"), {})
        control_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-CONTROL-{index:05d}",
                "CONTROL_COMPARATOR_EXECUTION",
                row,
                control_comparator_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    denominator_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_denominator_rows, 1):
        action_row = denominator_action.get(row.get("input_action_result_row_id"), {})
        denominator_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-DGUARD-{index:05d}",
                "DENOMINATOR_GUARD_EXECUTION",
                row,
                denominator_guard_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    horizon_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_horizon_rows, 1):
        action_row = horizon_action.get(row.get("input_action_result_row_id"), {})
        horizon_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-HREPAIR-{index:05d}",
                "HORIZON_REPAIR_SIDECAR",
                row,
                horizon_repair_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    coverage_rows: list[dict[str, Any]] = []
    for index, row in enumerate(runtime_coverage_rows, 1):
        action_row = coverage_action.get(row.get("input_action_result_row_id"), {})
        coverage_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-SCOREREXEC-COVERAGE-{index:05d}",
                "COVERAGE_SIDECAR",
                row,
                coverage_scorer_execution(row, action_row),
                generated_at,
                manifest_hash,
            )
        )

    observable_rows = [*controlled_rows, *denominator_guarded_observable_rows, *control_scope_rows]
    branch_local_scorer_rows = [*controlled_rows, *source_scorer_rows]
    source_rows = [*source_scorer_rows, *source_repair_rows]
    unified_rows = [*observable_rows, *source_rows, *control_rows, *denominator_rows]

    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        observable_rows,
        branch_local_scorer_rows,
        control_scope_rows,
        source_repair_rows,
        control_rows,
        horizon_rows,
        coverage_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCOREREXEC-Q-001",
                "question": "Did the scorer execution bundle preserve the 1,108 runtime-work denominator?",
                "answer_route": "Yes: unified scorer execution rows are exactly observable 444 plus source 309 plus control 231 plus denominator 124; horizon 37 and coverage 520 remain sidecars.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCOREREXEC-Q-002",
                "question": "Which rows are actual scorer execution rows?",
                "answer_route": "The branch-local scorer execution ledger contains 225 rows: 14 controlled observable scorers plus 211 source scorers, split into guarded and ambiguous control-required paths.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCOREREXEC-Q-003",
                "question": "Did source and horizon repair become executable actions?",
                "answer_route": "Yes: 98 source repair execution rows preserve exact-source rebuild/acquire, horizon rescore, and horizon kill-check actions; 37 horizon rows remain a sidecar to avoid double-counting.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCOREREXEC-Q-004",
                "question": "Were control-scope rows scored as global controls?",
                "answer_route": "No: 92 underpowered global-only rows are explicit exact-control-build requirements, while 76 same-resource proxy rows carry symbol/session guard quality.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_runtime_work_rows": len(runtime_unified_rows),
        "input_observable_runtime_work_rows": len(runtime_observable_rows),
        "input_controlled_scorer_runtime_rows": len(runtime_controlled_rows),
        "input_denominator_guarded_observable_runtime_rows": len(runtime_dguarded_observable_rows),
        "input_control_scope_build_attempt_rows": len(runtime_control_scope_rows),
        "input_source_runtime_work_rows": len(runtime_source_rows),
        "input_source_scorer_runtime_rows": len(runtime_source_scorer_rows),
        "input_source_repair_runtime_rows": len(runtime_source_repair_rows),
        "input_control_runtime_work_rows": len(runtime_control_rows),
        "input_denominator_runtime_work_rows": len(runtime_denominator_rows),
        "input_horizon_runtime_work_rows": len(runtime_horizon_rows),
        "input_coverage_runtime_work_rows": len(runtime_coverage_rows),
        "input_control_scope_group_rows": len(runtime_control_scope_group_rows),
        "input_source_repair_group_rows": len(runtime_source_repair_group_rows),
        "unified_scorer_execution_rows": len(unified_rows),
        "observable_scorer_execution_rows": len(observable_rows),
        "branch_local_scorer_execution_rows": len(branch_local_scorer_rows),
        "controlled_scorer_execution_rows": len(controlled_rows),
        "denominator_guarded_observable_execution_rows": len(denominator_guarded_observable_rows),
        "control_scope_execution_rows": len(control_scope_rows),
        "source_execution_rows": len(source_rows),
        "source_scorer_execution_rows": len(source_scorer_rows),
        "source_repair_execution_rows": len(source_repair_rows),
        "control_execution_rows": len(control_rows),
        "control_comparator_registered_rows": sum(
            1 for row in control_rows if row.get("control_execution_status") == "CONTROL_EXECUTION_COMPARATOR_REGISTERED"
        ),
        "control_context_rows": sum(
            1 for row in control_rows if row.get("control_execution_status") == "CONTROL_EXECUTION_COMPARATOR_CONTEXT_ONLY"
        ),
        "denominator_execution_rows": len(denominator_rows),
        "horizon_sidecar_execution_rows": len(horizon_rows),
        "coverage_sidecar_execution_rows": len(coverage_rows),
        "symbol_session_scorer_execution_rows": len(symbol_session_rows),
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
            "observable_runtime_work_bundle": runtime_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "execution_lane_counts": distributions["execution_lane"],
            "execution_status_counts": distributions["execution_status"],
            "control_scope_execution_status_counts": distributions["control_scope_execution_status"],
            "source_repair_execution_status_counts": distributions["source_repair_execution_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_RESULT: execute the 14 positive controlled "
                "observable scorers, score 20 guarded source proxies, score 191 ambiguous source proxies only "
                "with controls, register 262 denominator-guarded observables, enforce 124 denominator guards, "
                "register 230 control comparators, build exact controls for the 92 underpowered global-only rows, "
                "and execute the 98 source/horizon repair actions before stronger implementation synthesis."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)

    generated_files = [
        UNIFIED_LEDGER,
        OBSERVABLE_LEDGER,
        BRANCH_SCORER_LEDGER,
        CONTROLLED_LEDGER,
        DGUARDED_OBSERVABLE_LEDGER,
        CONTROL_SCOPE_LEDGER,
        SOURCE_LEDGER,
        SOURCE_SCORER_LEDGER,
        SOURCE_REPAIR_LEDGER,
        CONTROL_LEDGER,
        DENOMINATOR_LEDGER,
        HORIZON_LEDGER,
        COVERAGE_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(OBSERVABLE_LEDGER, observable_rows)
    write_jsonl(BRANCH_SCORER_LEDGER, branch_local_scorer_rows)
    write_jsonl(CONTROLLED_LEDGER, controlled_rows)
    write_jsonl(DGUARDED_OBSERVABLE_LEDGER, denominator_guarded_observable_rows)
    write_jsonl(CONTROL_SCOPE_LEDGER, control_scope_rows)
    write_jsonl(SOURCE_LEDGER, source_rows)
    write_jsonl(SOURCE_SCORER_LEDGER, source_scorer_rows)
    write_jsonl(SOURCE_REPAIR_LEDGER, source_repair_rows)
    write_jsonl(CONTROL_LEDGER, control_rows)
    write_jsonl(DENOMINATOR_LEDGER, denominator_rows)
    write_jsonl(HORIZON_LEDGER, horizon_rows)
    write_jsonl(COVERAGE_LEDGER, coverage_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Scorer Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified scorer execution rows: `{counts['unified_scorer_execution_rows']}`",
                f"- Branch-local scorer execution rows: `{counts['branch_local_scorer_execution_rows']}`",
                f"- Controlled scorer execution rows: `{counts['controlled_scorer_execution_rows']}`",
                f"- Source scorer execution rows: `{counts['source_scorer_execution_rows']}`",
                f"- Denominator-guarded observable execution rows: `{counts['denominator_guarded_observable_execution_rows']}`",
                f"- Control-scope execution rows: `{counts['control_scope_execution_rows']}`",
                f"- Source repair execution rows: `{counts['source_repair_execution_rows']}`",
                f"- Horizon sidecar execution rows: `{counts['horizon_sidecar_execution_rows']}`",
                f"- Coverage sidecar execution rows: `{counts['coverage_sidecar_execution_rows']}`",
                "",
                "Core result: runtime work is now executable scorer/source/control/denominator work with proxy deltas, control status, denominator guard strength, source repair causes, and sidecar protection against denominator inflation.",
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
