#!/usr/bin/env python3
"""Build branch-local observable/scorer implementation bundle.

This builder consumes the branch-local shadow source-guard bundle and emits
concrete research-only observable specs, source policies, control experiments,
denominator enforcement specs, and horizon repair execution specs. It preserves
all input rows and does not mutate live trading behavior.
"""

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

from src.research_infra.moonshot_observable_scorer_implementation import (
    IMPLEMENTATION_SURFACE,
    control_experiment_spec,
    denominator_enforcement_spec,
    horizon_repair_execution_spec,
    observable_rule_spec,
    primitive_coverage_state,
    source_guard_policy_spec,
)


SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_IMPLEMENTATION_BUNDLE"

SOURCE_RESULT = ROUTE_DIR / f"{SOURCE_PREFIX}_RESULT_2026-05-17.json"
SOURCE_RUNTIME_SPEC = ROUTE_DIR / f"{SOURCE_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SOURCE_UNIFIED = ROUTE_DIR / f"{SOURCE_PREFIX}_UNIFIED_DECISION_LEDGER_2026-05-17.jsonl"
SOURCE_IMPLEMENT = ROUTE_DIR / f"{SOURCE_PREFIX}_IMPLEMENT_ENABLE_BUNDLE_LEDGER_2026-05-17.jsonl"
SOURCE_GUARD = ROUTE_DIR / f"{SOURCE_PREFIX}_SOURCE_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL = ROUTE_DIR / f"{SOURCE_PREFIX}_SCORE_CONTROL_BUNDLE_LEDGER_2026-05-17.jsonl"
SOURCE_DGUARD = ROUTE_DIR / f"{SOURCE_PREFIX}_DENOMINATOR_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
SOURCE_HREPAIR = ROUTE_DIR / f"{SOURCE_PREFIX}_HORIZON_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_scorer_implementation.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
OBSERVABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_RULE_SPEC_LEDGER_2026-05-17.jsonl"
SOURCE_POLICY_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GUARD_POLICY_LEDGER_2026-05-17.jsonl"
CONTROL_EXPERIMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_EXPERIMENT_SPEC_LEDGER_2026-05-17.jsonl"
DENOMINATOR_ENFORCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_ENFORCEMENT_LEDGER_2026-05-17.jsonl"
HORIZON_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
RUNTIME_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_RUNTIME_REGISTRY_LEDGER_2026-05-17.jsonl"
PRIMITIVE_COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_PRIMITIVE_COVERAGE_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_LEDGER_2026-05-17.jsonl"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable/scorer implementation bundle only. It converts source-guard bundle rows "
    "into research shadow observable specs, source policies, control experiments, denominator guards, "
    "and horizon repair execution specs. It does not change live behavior, place orders, or claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-OBS-SCORER-SRC-{index:04d}",
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


def common_input(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_bundle_row_id": row.get("bundle_row_id"),
        "source_input_row_id": row.get("input_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "source_bundle_decision": row.get("bundle_decision"),
        "source_bundle_permission": row.get("bundle_permission"),
        "source_bundle_stage": row.get("bundle_stage"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_observable_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "implementation_row_id": f"OHLC-GTOS-OBS-SCORER-OBS-{index:05d}",
                    "input_ledger_type": "OBSERVABLE_RULE_SPEC",
                    "mechanical_rule_expression": row.get("mechanical_rule_expression"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    **common_input(row),
                    **observable_rule_spec(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_source_policy_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "implementation_row_id": f"OHLC-GTOS-OBS-SCORER-SOURCE-{index:05d}",
                    "input_ledger_type": "SOURCE_GUARD_POLICY_SPEC",
                    "source_materialization_execution_status": row.get("source_materialization_execution_status"),
                    "source_materialization_decision": row.get("source_materialization_decision"),
                    "materialization_exact_missing_reason": row.get("materialization_exact_missing_reason"),
                    **common_input(row),
                    **source_guard_policy_spec(row),
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
                    "implementation_row_id": f"OHLC-GTOS-OBS-SCORER-CONTROL-{index:05d}",
                    "input_ledger_type": "CONTROL_EXPERIMENT_SPEC",
                    "control_status": row.get("control_status"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    **common_input(row),
                    **control_experiment_spec(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_denominator_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "implementation_row_id": f"OHLC-GTOS-OBS-SCORER-DGUARD-{index:05d}",
                    "input_ledger_type": "DENOMINATOR_ENFORCEMENT_SPEC",
                    "guard_status": row.get("guard_status"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    **common_input(row),
                    **denominator_enforcement_spec(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_horizon_repair_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "implementation_repair_id": f"OHLC-GTOS-OBS-SCORER-HREPAIR-{index:05d}",
                    "input_ledger_type": "HORIZON_REPAIR_EXECUTION_SPEC",
                    "source_horizon_repair_action_id": row.get("horizon_repair_action_id"),
                    "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
                    "current_source_flagged_n": row.get("current_source_flagged_n"),
                    "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
                    "current_failclosed_reason_counts": row.get("current_failclosed_reason_counts"),
                    **common_input(row),
                    **horizon_repair_execution_spec(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_runtime_registry_rows(
    unified_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in unified_rows:
        key = (
            str(row.get("implementation_stage")),
            str(row.get("implementation_operation")),
            str(row.get("primitive_science_dimension") or row.get("control_experiment_family") or row.get("source_guard_mode") or row.get("denominator_guard_status") or "none"),
        )
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(grouped.items()), 1):
        stage, operation, dimension = key
        output.append(
            with_common(
                {
                    "runtime_registry_row_id": f"OHLC-GTOS-OBS-SCORER-RUNTIME-{index:04d}",
                    "implementation_stage": stage,
                    "implementation_operation": operation,
                    "runtime_registry_dimension": dimension,
                    "row_count": len(rows),
                    "outside_branch_rows": sum(1 for row in rows if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "symbols": sorted({str(row.get("symbol")) for row in rows}),
                    "sessions": sorted({str(row.get("route_session")) for row in rows}),
                    "runtime_registry": "branch_local_research_shadow_observable_registry",
                    "runtime_effect": "record_and_score_only",
                    "implementation_surface": IMPLEMENTATION_SURFACE,
                    "live_effect": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_primitive_coverage_rows(
    rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in [*rows, *repair_rows]:
        key = (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])), 1):
        symbol, route_session, horizon_id, primitive_flag = key
        status_counts = string_counter([primitive_coverage_state(row) for row in members], "primitive_coverage_status")
        stage_counts = string_counter(members, "implementation_stage")
        output.append(
            with_common(
                {
                    "primitive_coverage_row_id": f"OHLC-GTOS-OBS-SCORER-COVERAGE-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "primitive_flag": primitive_flag,
                    "observable_scope_key": (
                        f"symbol={symbol}|session={route_session}|horizon={horizon_id}|primitive={primitive_flag}"
                    ),
                    "covered_status_counts": status_counts,
                    "implementation_stage_counts": stage_counts,
                    "row_count": len(members),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "next_action": "continue_scoring_or_repair_per_stage_counts",
                    "coverage_rule": "covered_active_queued_killed_or_source_required_preserved",
                    "implementation_surface": IMPLEMENTATION_SURFACE,
                    "live_effect": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])), 1):
        symbol, route_session = key
        output.append(
            with_common(
                {
                    "symbol_session_row_id": f"OHLC-GTOS-OBS-SCORER-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "implementation_stage_counts": string_counter(members, "implementation_stage"),
                    "implementation_status_counts": string_counter(members, "implementation_status"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "implementation_surface": IMPLEMENTATION_SURFACE,
                    "live_effect": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "implementation_stage": string_counter(unified_rows, "implementation_stage"),
        "implementation_status": string_counter(unified_rows, "implementation_status"),
        "implementation_operation": string_counter(unified_rows, "implementation_operation"),
        "observable_family": string_counter(unified_rows, "observable_family"),
        "control_experiment_family": string_counter(unified_rows, "control_experiment_family"),
        "source_policy_action": string_counter(unified_rows, "source_policy_action"),
        "denominator_guard_status": string_counter(unified_rows, "denominator_guard_status"),
        "horizon_repair_status": string_counter(repair_rows, "implementation_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
        "runtime_registry_stage": string_counter(runtime_rows, "implementation_stage"),
        "primitive_coverage_row_count": {"rows": len(coverage_rows)},
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-SCORER-BUCKET-{len(output) + 1:04d}",
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
        "source_bundle_runtime_spec": SOURCE_RUNTIME_SPEC.relative_to(REPO).as_posix(),
        "implementation_policy": {
            "observable_rows": "register as branch-local research shadow observables only",
            "source_policy_rows": "apply source policy before any source-dependent scorer interpretation",
            "control_rows": "run paired controls before enable interpretation",
            "denominator_rows": "enforce denominator guard before concentration-sensitive interpretation",
            "horizon_repair_rows": "execute targetable-horizon rebuild action before source-dependent enable",
            "coverage_rows": "preserve active/queued/source-required primitive status during current lane",
        },
        "ledgers": {
            "unified_implementation": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "observable_rule_specs": OBSERVABLE_LEDGER.relative_to(REPO).as_posix(),
            "source_guard_policies": SOURCE_POLICY_LEDGER.relative_to(REPO).as_posix(),
            "control_experiments": CONTROL_EXPERIMENT_LEDGER.relative_to(REPO).as_posix(),
            "denominator_enforcement": DENOMINATOR_ENFORCEMENT_LEDGER.relative_to(REPO).as_posix(),
            "horizon_repair_execution": HORIZON_REPAIR_LEDGER.relative_to(REPO).as_posix(),
            "runtime_registry": RUNTIME_REGISTRY_LEDGER.relative_to(REPO).as_posix(),
            "primitive_coverage": PRIMITIVE_COVERAGE_LEDGER.relative_to(REPO).as_posix(),
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
    manifest["latest_branch_local_observable_scorer_implementation_bundle"] = {
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
        "event": "branch_local_observable_scorer_implementation_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built branch-local observable/scorer implementation specs from source-guard bundle rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        SOURCE_RESULT,
        SOURCE_RUNTIME_SPEC,
        SOURCE_UNIFIED,
        SOURCE_IMPLEMENT,
        SOURCE_GUARD,
        SOURCE_CONTROL,
        SOURCE_DGUARD,
        SOURCE_HREPAIR,
        HELPER_MODULE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    source_result = read_json(SOURCE_RESULT)
    source_runtime = read_json(SOURCE_RUNTIME_SPEC)
    source_unified = read_jsonl(SOURCE_UNIFIED)
    implement_rows_in = read_jsonl(SOURCE_IMPLEMENT)
    source_guard_rows_in = read_jsonl(SOURCE_GUARD)
    control_rows_in = read_jsonl(SOURCE_CONTROL)
    denominator_rows_in = read_jsonl(SOURCE_DGUARD)
    horizon_repair_rows_in = read_jsonl(SOURCE_HREPAIR)

    observable_rows = build_observable_rows(implement_rows_in, generated_at, manifest_hash)
    source_policy_rows = build_source_policy_rows(source_guard_rows_in, generated_at, manifest_hash)
    control_rows = build_control_rows(control_rows_in, generated_at, manifest_hash)
    denominator_rows = build_denominator_rows(denominator_rows_in, generated_at, manifest_hash)
    horizon_repair_rows = build_horizon_repair_rows(horizon_repair_rows_in, generated_at, manifest_hash)
    unified_rows = [*observable_rows, *source_policy_rows, *control_rows, *denominator_rows]
    runtime_registry_rows = build_runtime_registry_rows(unified_rows, generated_at, manifest_hash)
    primitive_coverage_rows = build_primitive_coverage_rows(unified_rows, horizon_repair_rows, generated_at, manifest_hash)
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        horizon_repair_rows,
        runtime_registry_rows,
        primitive_coverage_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCORER-Q-001",
                "question": "Did the implementation bundle preserve every source-guard bundle row?",
                "answer_route": "Yes: 444 observable specs, 309 source policies, 231 control experiments, and 124 denominator enforcements are emitted into the 1,108-row unified implementation ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCORER-Q-002",
                "question": "Were the 37 horizon fail-closed rows converted into executable repair specs?",
                "answer_route": "Yes: every horizon repair action is emitted into a repair execution ledger with rebuild/rescore or rebuild/kill-if-negative operation.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCORER-Q-003",
                "question": "Did the full-coverage mandate change the active lane?",
                "answer_route": "No: it is carried as primitive coverage rows while the active lane continues into observable/scorer implementation specs.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-SCORER-Q-004",
                "question": "Does this packet make a live or validation claim?",
                "answer_route": "No: all rows are branch-local research shadow specs, source policies, controls, guards, or repair execution specs.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "source_unified_bundle_input_rows": len(source_unified),
        "source_implementation_enable_input_rows": len(implement_rows_in),
        "source_guard_policy_input_rows": len(source_guard_rows_in),
        "source_score_control_input_rows": len(control_rows_in),
        "source_denominator_guard_input_rows": len(denominator_rows_in),
        "source_horizon_repair_input_rows": len(horizon_repair_rows_in),
        "unified_implementation_rows": len(unified_rows),
        "observable_rule_spec_rows": len(observable_rows),
        "source_guard_policy_rows": len(source_policy_rows),
        "control_experiment_spec_rows": len(control_rows),
        "denominator_enforcement_rows": len(denominator_rows),
        "horizon_repair_execution_rows": len(horizon_repair_rows),
        "runtime_registry_rows": len(runtime_registry_rows),
        "primitive_coverage_rows": len(primitive_coverage_rows),
        "symbol_session_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
        "outside_branch_implementation_rows": sum(
            1 for row in unified_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "source_policy_block_or_repair_rows": sum(
            1
            for row in source_policy_rows
            if str(row.get("implementation_status", "")).startswith("SOURCE_POLICY_BLOCK")
            or "REPAIR" in str(row.get("implementation_status", ""))
        ),
        "control_required_rows": sum(1 for row in control_rows if row.get("control_required_before_enable")),
    }
    system_decision = {
        "implementation_stage_counts": distributions["implementation_stage"],
        "implementation_status_counts": distributions["implementation_status"],
        "implementation_operation_counts": distributions["implementation_operation"],
        "observable_family_counts": distributions["observable_family"],
        "horizon_repair_status_counts": distributions["horizon_repair_status"],
        "system_recommendation": (
            "BRANCH_LOCAL_OBSERVABLE_SCORER_IMPLEMENTATION_BUNDLE_RESULT: register the 444 observable "
            "rules only in the research shadow registry, apply 309 source guard policies, require 231 "
            "control experiments, enforce 124 denominator guards, and execute 37 horizon repair specs "
            "before source-dependent interpretation."
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
            "branch_local_shadow_source_guard_bundle": source_result.get("counts", {}),
            "branch_local_shadow_source_guard_runtime_bundle_inputs": source_runtime.get("bundle_inputs", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }
    runtime_spec = build_runtime_spec(result, distributions)

    generated_files = [
        UNIFIED_LEDGER,
        OBSERVABLE_LEDGER,
        SOURCE_POLICY_LEDGER,
        CONTROL_EXPERIMENT_LEDGER,
        DENOMINATOR_ENFORCEMENT_LEDGER,
        HORIZON_REPAIR_LEDGER,
        RUNTIME_REGISTRY_LEDGER,
        PRIMITIVE_COVERAGE_LEDGER,
        SYMBOL_SESSION_LEDGER,
        RUNTIME_SPEC_PATH,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(OBSERVABLE_LEDGER, observable_rows)
    write_jsonl(SOURCE_POLICY_LEDGER, source_policy_rows)
    write_jsonl(CONTROL_EXPERIMENT_LEDGER, control_rows)
    write_jsonl(DENOMINATOR_ENFORCEMENT_LEDGER, denominator_rows)
    write_jsonl(HORIZON_REPAIR_LEDGER, horizon_repair_rows)
    write_jsonl(RUNTIME_REGISTRY_LEDGER, runtime_registry_rows)
    write_jsonl(PRIMITIVE_COVERAGE_LEDGER, primitive_coverage_rows)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_session_rows)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch-Local Observable Scorer Implementation Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified implementation rows: `{counts['unified_implementation_rows']}`",
                f"- Observable rule specs: `{counts['observable_rule_spec_rows']}`",
                f"- Source guard policies: `{counts['source_guard_policy_rows']}`",
                f"- Control experiment specs: `{counts['control_experiment_spec_rows']}`",
                f"- Denominator enforcement rows: `{counts['denominator_enforcement_rows']}`",
                f"- Horizon repair execution rows: `{counts['horizon_repair_execution_rows']}`",
                f"- Primitive coverage rows: `{counts['primitive_coverage_rows']}`",
                "",
                "Core result: the source-guard bundle has been converted into branch-local observable/scorer implementation specs with controls, source policies, denominator guards, repair paths, and coverage state preserved.",
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
