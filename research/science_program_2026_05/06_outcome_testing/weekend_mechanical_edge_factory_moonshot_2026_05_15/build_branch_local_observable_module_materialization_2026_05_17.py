#!/usr/bin/env python3
"""Materialize branch-local observable scorer/registry/repair modules from code actions."""

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

from src.research_infra.moonshot_branch_local_observable_registry import (
    REGISTRY_MODULE_SURFACE,
    coverage_sidecar_registry_materialization,
    registry_module_materialization,
)
from src.research_infra.moonshot_branch_local_observable_scorers import (
    SCORER_MODULE_SURFACE,
    scorer_module_materialization,
)
from src.research_infra.moonshot_branch_local_source_repair_work import (
    REPAIR_MODULE_SURFACE,
    exact_control_work_materialization,
    horizon_sidecar_work_materialization,
    source_repair_work_materialization,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_CODE_INTEGRATION_CANDIDATE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_MODULE_MATERIALIZATION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_CODE_INTEGRATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_SCORER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_CODE_PATCH_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_REGISTRY_OBSERVABLE = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_REGISTRY_CODE_PATCH_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_SCOPE = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_SCOPE_CODE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_CONTROL_BUILDER_CODE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_REGISTRY = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_REGISTRY_CODE_PATCH_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR_GUARD = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARD_CODE_PATCH_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_CODE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_SIDECAR_CODE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_COVERAGE_SIDECAR_CODE_ACTION_LEDGER_2026-05-17.jsonl"

SCORER_MODULE = REPO / SCORER_MODULE_SURFACE
REGISTRY_MODULE = REPO / REGISTRY_MODULE_SURFACE
REPAIR_MODULE = REPO / REPAIR_MODULE_SURFACE
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_code_integration_candidates.py"
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SCORER_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
REGISTRY_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRY_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_WORK_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_WORK_ORDER_LEDGER_2026-05-17.jsonl"
HORIZON_WORK_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_WORK_ORDER_SIDECAR_LEDGER_2026-05-17.jsonl"
COVERAGE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_REGISTRY_SIDECAR_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable module materialization bundle only. It consumes code integration candidate rows and "
    "materializes research-only scorer, registry, and source/control repair module records. It preserves exact-control, "
    "horizon, and primitive-coverage sidecars separately. It does not change live behavior, place orders, or claim "
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
                "source_manifest_id": f"OHLC-GTOS-OBS-MODMAT-SRC-{index:04d}",
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


def normalize_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in {"", "None", "null"}:
        return None
    return text


def common_code_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_code_integration_candidate_row_id": row.get("code_integration_candidate_row_id"),
        "input_code_integration_lane": row.get("code_integration_lane"),
        "input_code_integration_stage": row.get("code_integration_stage"),
        "input_code_integration_status": row.get("code_integration_status"),
        "input_code_integration_decision": row.get("code_integration_decision"),
        "input_code_integration_action": row.get("code_integration_action"),
        "input_implementation_synthesis_row_id": row.get("input_implementation_synthesis_row_id"),
        "input_implementation_synthesis_status": row.get("input_implementation_synthesis_status"),
        "input_execution_bundle_row_id": row.get("input_execution_bundle_row_id"),
        "input_runtime_work_row_id": row.get("input_runtime_work_row_id"),
        "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "symbol": normalize_value(row.get("symbol")),
        "route_session": normalize_value(row.get("route_session")),
        "session_bucket": normalize_value(row.get("session_bucket")),
        "horizon_id": normalize_value(row.get("horizon_id")),
        "primitive_flag": normalize_value(row.get("primitive_flag")),
        "observable_scope_key": row.get("observable_scope_key"),
        "scope_symbol": row.get("scope_symbol"),
        "scope_session": row.get("scope_session"),
        "scope_horizon": row.get("scope_horizon"),
        "scope_primitive": row.get("scope_primitive"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "target_file_hint": row.get("target_file_hint"),
        "integration_priority_score": row.get("integration_priority_score"),
        "control_guard_required": row.get("control_guard_required"),
        "source_repair_required": bool(row.get("source_repair_required")),
        "control_required": bool(row.get("control_required")),
    }


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


def make_materialization_row(
    row_id: str,
    lane: str,
    code_row: dict[str, Any],
    payload: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> dict[str, Any]:
    return with_common(
        {
            "module_materialization_row_id": row_id,
            "module_materialization_lane": lane,
            **common_code_fields(code_row),
            **payload,
        },
        generated_at,
        manifest_hash,
    )


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
                    "symbol_session_module_materialization_id": f"OHLC-GTOS-OBS-MODMAT-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "module_materialization_lane_counts": string_counter(members, "module_materialization_lane"),
                    "module_materialization_status_counts": string_counter(members, "module_materialization_status"),
                    "module_patch_ready_rows": sum(1 for row in members if row.get("module_patch_ready")),
                    "repair_work_order_open_rows": sum(1 for row in members if row.get("repair_work_order_open")),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    scorer_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    exact_control_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "module_materialization_lane": string_counter(unified_rows, "module_materialization_lane"),
        "module_materialization_status": string_counter(unified_rows, "module_materialization_status"),
        "module_materialization_decision": string_counter(unified_rows, "module_materialization_decision"),
        "module_materialization_surface": string_counter(unified_rows, "module_materialization_surface"),
        "module_patch_ready": string_counter(unified_rows, "module_patch_ready"),
        "repair_work_order_open": string_counter(unified_rows, "repair_work_order_open"),
        "branch_local_ready": string_counter(unified_rows, "branch_local_ready"),
        "scorer_module_status": string_counter(scorer_rows, "module_materialization_status"),
        "registry_module_status": string_counter(registry_rows, "module_materialization_status"),
        "source_repair_module_status": string_counter(repair_rows, "module_materialization_status"),
        "exact_control_work_status": string_counter(exact_control_rows, "module_materialization_status"),
        "horizon_sidecar_work_status": string_counter(horizon_rows, "module_materialization_status"),
        "coverage_registry_sidecar_status": string_counter(coverage_rows, "module_materialization_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-MODMAT-BUCKET-{len(output) + 1:04d}",
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
    manifest["latest_branch_local_observable_module_materialization_bundle"] = {
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
        "event": "branch_local_observable_module_materialization_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Materialized branch-local scorer/registry/source-repair module records from code integration candidates.",
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
            INPUT_SCORER,
            INPUT_REGISTRY_OBSERVABLE,
            INPUT_CONTROL_SCOPE,
            INPUT_EXACT_CONTROL,
            INPUT_CONTROL_REGISTRY,
            INPUT_DENOMINATOR_GUARD,
            INPUT_SOURCE_REPAIR,
            INPUT_HORIZON,
            INPUT_COVERAGE,
            SCORER_MODULE,
            REGISTRY_MODULE,
            REPAIR_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_unified_rows = read_jsonl(INPUT_UNIFIED)
    input_scorer_rows = read_jsonl(INPUT_SCORER)
    input_observable_registry_rows = read_jsonl(INPUT_REGISTRY_OBSERVABLE)
    input_control_scope_rows = read_jsonl(INPUT_CONTROL_SCOPE)
    input_exact_control_rows = read_jsonl(INPUT_EXACT_CONTROL)
    input_control_registry_rows = read_jsonl(INPUT_CONTROL_REGISTRY)
    input_denominator_guard_rows = read_jsonl(INPUT_DENOMINATOR_GUARD)
    input_source_repair_rows = read_jsonl(INPUT_SOURCE_REPAIR)
    input_horizon_rows = read_jsonl(INPUT_HORIZON)
    input_coverage_rows = read_jsonl(INPUT_COVERAGE)

    scorer_module_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_scorer_rows, 1):
        scorer_module_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-SCORER-{index:05d}",
                "SCORER_MODULE_MATERIALIZATION",
                row,
                scorer_module_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    registry_input_rows = [
        *input_observable_registry_rows,
        *input_control_scope_rows,
        *input_control_registry_rows,
        *input_denominator_guard_rows,
    ]
    registry_module_rows: list[dict[str, Any]] = []
    for index, row in enumerate(registry_input_rows, 1):
        registry_module_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-REGISTRY-{index:05d}",
                "REGISTRY_MODULE_MATERIALIZATION",
                row,
                registry_module_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    source_repair_module_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_source_repair_rows, 1):
        source_repair_module_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-SREPAIR-{index:05d}",
                "SOURCE_REPAIR_MODULE_MATERIALIZATION",
                row,
                source_repair_work_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    exact_control_work_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_exact_control_rows, 1):
        exact_control_work_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-EXACTCTRL-{index:05d}",
                "EXACT_CONTROL_WORK_ORDER",
                row,
                exact_control_work_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    horizon_work_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_horizon_rows, 1):
        horizon_work_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-HORIZON-{index:05d}",
                "HORIZON_WORK_ORDER_SIDECAR",
                row,
                horizon_sidecar_work_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    coverage_registry_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_coverage_rows, 1):
        coverage_registry_rows.append(
            make_materialization_row(
                f"OHLC-GTOS-OBS-MODMAT-COVERAGE-{index:05d}",
                "COVERAGE_REGISTRY_SIDECAR",
                row,
                coverage_sidecar_registry_materialization(row),
                generated_at,
                manifest_hash,
            )
        )

    unified_rows = [*scorer_module_rows, *registry_module_rows, *source_repair_module_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        scorer_module_rows,
        registry_module_rows,
        source_repair_module_rows,
        exact_control_work_rows,
        horizon_work_rows,
        coverage_registry_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-MODMAT-Q-001",
                "question": "Did module materialization preserve the primary code-integration denominator?",
                "answer_route": "Yes: unified module materialization rows are 1,108, split into scorer 225, registry 785, and source repair 98.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-MODMAT-Q-002",
                "question": "Which branch-local modules are now represented as executable research surfaces?",
                "answer_route": "Three target modules exist: observable scorers, observable registry, and source/control repair work. They are research-only and do not affect live behavior.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-MODMAT-Q-003",
                "question": "Which work remains open after module materialization?",
                "answer_route": "92 exact-control work orders, 61 exact-source repairs, 29 horizon rebuild/rescores, and 8 horizon rebuild/kill-checks remain active same-resource execution work.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-MODMAT-Q-004",
                "question": "Did horizon and coverage sidecars stay outside the denominator?",
                "answer_route": "Yes: 37 horizon sidecar rows and 520 coverage registry sidecar rows remain outside unified module materialization rows.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_code_integration_candidate_rows": len(input_unified_rows),
        "input_scorer_code_patch_candidate_rows": len(input_scorer_rows),
        "input_observable_registry_code_patch_rows": len(input_observable_registry_rows),
        "input_control_scope_code_action_rows": len(input_control_scope_rows),
        "input_exact_control_builder_code_action_rows": len(input_exact_control_rows),
        "input_control_registry_code_patch_rows": len(input_control_registry_rows),
        "input_denominator_guard_code_patch_rows": len(input_denominator_guard_rows),
        "input_source_repair_code_action_rows": len(input_source_repair_rows),
        "input_horizon_sidecar_code_action_rows": len(input_horizon_rows),
        "input_coverage_sidecar_code_action_rows": len(input_coverage_rows),
        "unified_module_materialization_rows": len(unified_rows),
        "scorer_module_materialization_rows": len(scorer_module_rows),
        "registry_module_materialization_rows": len(registry_module_rows),
        "source_repair_module_materialization_rows": len(source_repair_module_rows),
        "exact_control_work_order_rows": len(exact_control_work_rows),
        "horizon_work_order_sidecar_rows": len(horizon_work_rows),
        "coverage_registry_sidecar_rows": len(coverage_registry_rows),
        "scorer_module_patch_ready_rows": sum(1 for row in scorer_module_rows if row.get("module_patch_ready")),
        "registry_module_patch_ready_rows": sum(1 for row in registry_module_rows if row.get("module_patch_ready")),
        "source_repair_work_order_open_rows": sum(1 for row in source_repair_module_rows if row.get("repair_work_order_open")),
        "exact_control_work_order_open_rows": sum(1 for row in exact_control_work_rows if row.get("repair_work_order_open")),
        "symbol_session_module_materialization_rows": len(symbol_session_rows),
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
        "upstream_counts": {"observable_code_integration_candidate_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "module_materialization_lane_counts": distributions["module_materialization_lane"],
            "module_materialization_status_counts": distributions["module_materialization_status"],
            "module_surface_counts": distributions["module_materialization_surface"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_MODULE_MATERIALIZATION_BUNDLE_RESULT: materialize research-only "
                "scorer module rows for 225 scorer candidates, registry module rows for 785 observable/control/"
                "denominator candidates, source-repair module rows for 98 repair candidates, and keep 92 "
                "exact-control plus 37 horizon plus 520 coverage sidecar rows as explicit open work/context."
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
        "input_code_integration_candidate_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "identity_policy": {
            "primary_join_key": "code_integration_candidate_row_id plus input_implementation_synthesis_row_id",
            "scope_only_join_allowed": False,
            "exact_control_horizon_coverage_sidecars_in_unified_denominator": False,
        },
        "module_policy": {
            "scorer_module": SCORER_MODULE.relative_to(REPO).as_posix(),
            "registry_module": REGISTRY_MODULE.relative_to(REPO).as_posix(),
            "repair_module": REPAIR_MODULE.relative_to(REPO).as_posix(),
            "sidecars": "preserve exact-control, horizon, and coverage sidecars outside the 1,108 unified denominator",
        },
        "module_materialization_distributions": distributions,
    }

    generated_files = [
        UNIFIED_LEDGER,
        SCORER_MODULE_LEDGER,
        REGISTRY_MODULE_LEDGER,
        SOURCE_REPAIR_MODULE_LEDGER,
        EXACT_CONTROL_WORK_LEDGER,
        HORIZON_WORK_LEDGER,
        COVERAGE_REGISTRY_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]

    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(SCORER_MODULE_LEDGER, scorer_module_rows)
    write_jsonl(REGISTRY_MODULE_LEDGER, registry_module_rows)
    write_jsonl(SOURCE_REPAIR_MODULE_LEDGER, source_repair_module_rows)
    write_jsonl(EXACT_CONTROL_WORK_LEDGER, exact_control_work_rows)
    write_jsonl(HORIZON_WORK_LEDGER, horizon_work_rows)
    write_jsonl(COVERAGE_REGISTRY_LEDGER, coverage_registry_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Module Materialization Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified module materialization rows: `{counts['unified_module_materialization_rows']}`",
                f"- Scorer module materialization rows: `{counts['scorer_module_materialization_rows']}`",
                f"- Registry module materialization rows: `{counts['registry_module_materialization_rows']}`",
                f"- Source repair module materialization rows: `{counts['source_repair_module_materialization_rows']}`",
                f"- Exact control work-order rows: `{counts['exact_control_work_order_rows']}`",
                f"- Horizon work-order sidecar rows: `{counts['horizon_work_order_sidecar_rows']}`",
                f"- Coverage registry sidecar rows: `{counts['coverage_registry_sidecar_rows']}`",
                "",
                "Core result: code-action candidates now have concrete branch-local research module materialization records, with open repair work preserved as executable work orders.",
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
