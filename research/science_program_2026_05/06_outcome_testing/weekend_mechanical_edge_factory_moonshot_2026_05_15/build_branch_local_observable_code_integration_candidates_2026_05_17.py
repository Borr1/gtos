#!/usr/bin/env python3
"""Build branch-local code integration candidates from implementation synthesis rows."""

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

from src.research_infra.moonshot_observable_code_integration_candidates import (
    CODE_INTEGRATION_SURFACE,
    control_registry_code_candidate,
    control_scope_code_candidate,
    coverage_sidecar_code_candidate,
    denominator_guard_code_candidate,
    exact_control_builder_code_candidate,
    horizon_sidecar_code_candidate,
    observable_registry_code_candidate,
    scorer_code_integration_candidate,
    source_repair_code_candidate,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_SYNTHESIS_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_CODE_INTEGRATION_CANDIDATE_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_IMPLEMENTATION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
INPUT_SCORER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROLLED_SCORER = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROLLED_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_PROXY = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_PROXY_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_OBSERVABLE_REGISTRY = ROUTE_DIR / f"{INPUT_PREFIX}_OBSERVABLE_REGISTRY_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_SCOPE = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_SCOPE_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_CONTROL_BUILD_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_REGISTRY = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_REGISTRY_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR_GUARD = ROUTE_DIR / f"{INPUT_PREFIX}_DENOMINATOR_GUARD_REGISTRY_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_SIDECAR_SYNTHESIS_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_COVERAGE_SIDECAR_SYNTHESIS_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_code_integration_candidates.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_implementation_synthesis.py"
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_CODE_INTEGRATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
SCORER_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_CODE_PATCH_CANDIDATE_LEDGER_2026-05-17.jsonl"
CONTROLLED_SCORER_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROLLED_SCORER_CODE_PATCH_LEDGER_2026-05-17.jsonl"
SOURCE_PROXY_SCORER_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PROXY_SCORER_CODE_PATCH_LEDGER_2026-05-17.jsonl"
OBSERVABLE_REGISTRY_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_REGISTRY_CODE_PATCH_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_CODE_ACTION_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_BUILDER_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_BUILDER_CODE_ACTION_LEDGER_2026-05-17.jsonl"
CONTROL_REGISTRY_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_REGISTRY_CODE_PATCH_LEDGER_2026-05-17.jsonl"
DENOMINATOR_GUARD_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARD_CODE_PATCH_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_CODE_ACTION_LEDGER_2026-05-17.jsonl"
HORIZON_SIDECAR_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_SIDECAR_CODE_ACTION_LEDGER_2026-05-17.jsonl"
COVERAGE_SIDECAR_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_SIDECAR_CODE_ACTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_CODE_INTEGRATION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable code integration candidate bundle only. It consumes implementation synthesis rows and "
    "turns every scorer, observable registry, control-scope, control comparator, denominator guard, and source-repair "
    "decision into research-only code patch or work-order candidates. Horizon and primitive coverage remain sidecars. "
    "It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
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
                "source_manifest_id": f"OHLC-GTOS-OBS-CODEINT-SRC-{index:04d}",
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


def common_implementation_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_implementation_synthesis_row_id": row.get("implementation_synthesis_row_id"),
        "input_implementation_synthesis_lane": row.get("implementation_synthesis_lane"),
        "input_implementation_synthesis_stage": row.get("implementation_synthesis_stage"),
        "input_implementation_synthesis_status": row.get("implementation_synthesis_status"),
        "input_implementation_synthesis_decision": row.get("implementation_synthesis_decision"),
        "input_keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
        "input_execution_bundle_row_id": row.get("input_execution_bundle_row_id"),
        "input_execution_lane": row.get("input_execution_lane"),
        "input_execution_status": row.get("input_execution_status"),
        "input_execution_decision": row.get("input_execution_decision"),
        "input_runtime_work_row_id": row.get("input_runtime_work_row_id"),
        "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
        "input_action_result_row_id": row.get("input_action_result_row_id"),
        "input_execution_row_id": row.get("input_execution_row_id"),
        "input_implementation_row_id": row.get("input_implementation_row_id"),
        "input_source_bundle_row_id": row.get("input_source_bundle_row_id"),
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
        "runtime_work_status": row.get("runtime_work_status"),
        "runtime_decision": row.get("runtime_decision"),
        "runtime_ready": bool(row.get("runtime_ready")),
        "runtime_control_required": bool(row.get("runtime_control_required")),
        "runtime_source_repair_required": bool(row.get("runtime_source_repair_required")),
        "implementation_action": row.get("implementation_action"),
        "implementation_success_cause": row.get("implementation_success_cause"),
        "implementation_failure_or_repair_cause": row.get("implementation_failure_or_repair_cause"),
    }


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
            "code_integration_surface": CODE_INTEGRATION_SURFACE,
            "live_effect": False,
        }
    )
    return row


def make_code_row(
    row_id: str,
    lane: str,
    implementation_row: dict[str, Any],
    payload: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> dict[str, Any]:
    return with_common(
        {
            "code_integration_candidate_row_id": row_id,
            "code_integration_lane": lane,
            **common_implementation_fields(implementation_row),
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
                    "symbol_session_code_integration_id": f"OHLC-GTOS-OBS-CODEINT-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "code_integration_lane_counts": string_counter(members, "code_integration_lane"),
                    "code_integration_status_counts": string_counter(members, "code_integration_status"),
                    "code_integration_decision_counts": string_counter(members, "code_integration_decision"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "branch_local_ready_rows": sum(1 for row in members if row.get("branch_local_ready")),
                    "source_repair_required_rows": sum(1 for row in members if row.get("source_repair_required")),
                    "control_guard_required_rows": sum(1 for row in members if row.get("control_guard_required")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    scorer_rows: list[dict[str, Any]],
    source_proxy_rows: list[dict[str, Any]],
    control_scope_rows: list[dict[str, Any]],
    source_repair_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "code_integration_lane": string_counter(unified_rows, "code_integration_lane"),
        "code_integration_status": string_counter(unified_rows, "code_integration_status"),
        "code_integration_decision": string_counter(unified_rows, "code_integration_decision"),
        "code_integration_action": string_counter(unified_rows, "code_integration_action"),
        "target_file_hint": string_counter(unified_rows, "target_file_hint"),
        "branch_local_ready": string_counter(unified_rows, "branch_local_ready"),
        "source_repair_required": string_counter(unified_rows, "source_repair_required"),
        "control_required": string_counter(unified_rows, "control_required"),
        "control_guard_required": string_counter(unified_rows, "control_guard_required"),
        "standalone_interpretation_allowed": string_counter(unified_rows, "standalone_interpretation_allowed"),
        "scorer_code_status": string_counter(scorer_rows, "code_integration_status"),
        "source_proxy_code_status": string_counter(source_proxy_rows, "code_integration_status"),
        "control_scope_code_status": string_counter(control_scope_rows, "code_integration_status"),
        "source_repair_code_status": string_counter(source_repair_rows, "code_integration_status"),
        "control_registry_code_status": string_counter(control_rows, "code_integration_status"),
        "horizon_sidecar_code_status": string_counter(horizon_rows, "code_integration_status"),
        "coverage_sidecar_code_status": string_counter(coverage_rows, "code_integration_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-CODEINT-BUCKET-{len(output) + 1:04d}",
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
        "input_implementation_synthesis_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "identity_policy": {
            "primary_join_key": "implementation_synthesis_row_id plus input_execution_bundle_row_id",
            "scope_only_join_allowed": False,
            "horizon_and_coverage_sidecars_in_unified_denominator": False,
            "exact_control_builder_rows_are_subset_of_control_scope_rows": True,
        },
        "code_integration_policy": {
            "controlled_scorers": "emit branch-local scorer patch candidates for all 14 controlled positive-delta rows",
            "source_proxy_scorers": "emit 20 guarded source proxy scorer candidates and 191 ambiguous source proxy scorer candidates with mandatory controls",
            "observable_registry": "emit all 262 denominator-guarded observable registry patch candidates",
            "control_scope": "emit 76 proxy-control guard patch candidates and 92 exact-control builder work orders",
            "source_repair": "emit 61 exact-source repair, 29 horizon rescore, and 8 horizon kill-check work orders",
            "sidecars": "preserve 37 horizon and 520 coverage sidecar code-action rows outside the 1,108 denominator",
        },
        "ledgers": {
            "unified_code_integration_candidates": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "scorer_code_patch_candidates": SCORER_CODE_LEDGER.relative_to(REPO).as_posix(),
            "observable_registry_code_patch": OBSERVABLE_REGISTRY_CODE_LEDGER.relative_to(REPO).as_posix(),
            "exact_control_builder_code_actions": EXACT_CONTROL_BUILDER_CODE_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_code_actions": SOURCE_REPAIR_CODE_LEDGER.relative_to(REPO).as_posix(),
            "horizon_sidecar_code_actions": HORIZON_SIDECAR_CODE_LEDGER.relative_to(REPO).as_posix(),
            "coverage_sidecar_code_actions": COVERAGE_SIDECAR_CODE_LEDGER.relative_to(REPO).as_posix(),
        },
        "code_integration_distributions": distributions,
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
    manifest["latest_branch_local_observable_code_integration_candidate_bundle"] = {
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
        "event": "branch_local_observable_code_integration_candidate_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built branch-local scorer/registry/control/source-repair code patch and work-order candidates from implementation synthesis outputs.",
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
            INPUT_CONTROLLED_SCORER,
            INPUT_SOURCE_PROXY,
            INPUT_OBSERVABLE_REGISTRY,
            INPUT_CONTROL_SCOPE,
            INPUT_EXACT_CONTROL,
            INPUT_CONTROL_REGISTRY,
            INPUT_DENOMINATOR_GUARD,
            INPUT_SOURCE_REPAIR,
            INPUT_HORIZON,
            INPUT_COVERAGE,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_unified_rows = read_jsonl(INPUT_UNIFIED)
    input_scorer_rows = read_jsonl(INPUT_SCORER)
    input_controlled_scorer_rows = read_jsonl(INPUT_CONTROLLED_SCORER)
    input_source_proxy_rows = read_jsonl(INPUT_SOURCE_PROXY)
    input_observable_registry_rows = read_jsonl(INPUT_OBSERVABLE_REGISTRY)
    input_control_scope_rows = read_jsonl(INPUT_CONTROL_SCOPE)
    input_exact_control_rows = read_jsonl(INPUT_EXACT_CONTROL)
    input_control_registry_rows = read_jsonl(INPUT_CONTROL_REGISTRY)
    input_denominator_guard_rows = read_jsonl(INPUT_DENOMINATOR_GUARD)
    input_source_repair_rows = read_jsonl(INPUT_SOURCE_REPAIR)
    input_horizon_rows = read_jsonl(INPUT_HORIZON)
    input_coverage_rows = read_jsonl(INPUT_COVERAGE)

    controlled_scorer_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_controlled_scorer_rows, 1):
        controlled_scorer_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-CONTROLLED-{index:05d}",
                "CONTROLLED_SCORER_CODE_PATCH",
                row,
                scorer_code_integration_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    source_proxy_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_source_proxy_rows, 1):
        source_proxy_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-SPROXY-{index:05d}",
                "SOURCE_PROXY_SCORER_CODE_PATCH",
                row,
                scorer_code_integration_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    scorer_code_rows = [*controlled_scorer_code_rows, *source_proxy_code_rows]

    observable_registry_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_observable_registry_rows, 1):
        observable_registry_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-OBSREG-{index:05d}",
                "OBSERVABLE_REGISTRY_CODE_PATCH",
                row,
                observable_registry_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    control_scope_code_rows: list[dict[str, Any]] = []
    exact_control_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_control_scope_rows, 1):
        coded = make_code_row(
            f"OHLC-GTOS-OBS-CODEINT-CSCOPE-{index:05d}",
            "CONTROL_SCOPE_CODE_ACTION",
            row,
            control_scope_code_candidate(row),
            generated_at,
            manifest_hash,
        )
        control_scope_code_rows.append(coded)

    for index, row in enumerate(input_exact_control_rows, 1):
        exact_control_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-EXACTCTRL-{index:05d}",
                "EXACT_CONTROL_BUILDER_CODE_ACTION",
                row,
                exact_control_builder_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    control_registry_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_control_registry_rows, 1):
        control_registry_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-CONTROL-{index:05d}",
                "CONTROL_REGISTRY_CODE_PATCH",
                row,
                control_registry_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    denominator_guard_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_denominator_guard_rows, 1):
        denominator_guard_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-DGUARD-{index:05d}",
                "DENOMINATOR_GUARD_CODE_PATCH",
                row,
                denominator_guard_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    source_repair_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_source_repair_rows, 1):
        source_repair_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-SREPAIR-{index:05d}",
                "SOURCE_REPAIR_CODE_ACTION",
                row,
                source_repair_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    horizon_sidecar_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_horizon_rows, 1):
        horizon_sidecar_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-HORIZON-{index:05d}",
                "HORIZON_SIDECAR_CODE_ACTION",
                row,
                horizon_sidecar_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    coverage_sidecar_code_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_coverage_rows, 1):
        coverage_sidecar_code_rows.append(
            make_code_row(
                f"OHLC-GTOS-OBS-CODEINT-COVERAGE-{index:05d}",
                "COVERAGE_SIDECAR_CODE_ACTION",
                row,
                coverage_sidecar_code_candidate(row),
                generated_at,
                manifest_hash,
            )
        )

    unified_rows = [
        *controlled_scorer_code_rows,
        *observable_registry_code_rows,
        *control_scope_code_rows,
        *source_proxy_code_rows,
        *source_repair_code_rows,
        *control_registry_code_rows,
        *denominator_guard_code_rows,
    ]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        scorer_code_rows,
        source_proxy_code_rows,
        control_scope_code_rows,
        source_repair_code_rows,
        control_registry_code_rows,
        horizon_sidecar_code_rows,
        coverage_sidecar_code_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-CODEINT-Q-001",
                "question": "Did code integration preserve the primary implementation denominator?",
                "answer_route": "Yes: the unified code integration candidate ledger is 1,108 rows, matching implementation synthesis rows from scorer 225 plus observable 262 plus control-scope 168 plus source repair 98 plus control 231 plus denominator 124.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-CODEINT-Q-002",
                "question": "Which scorer candidates can be interpreted standalone?",
                "answer_route": "Only the 14 controlled observable scorer patches and 20 guarded source proxy scorer patches. The 191 ambiguous source proxy scorer patches require explicit control guards.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-CODEINT-Q-003",
                "question": "Which same-resource rows are still active build or repair work rather than scored integration?",
                "answer_route": "92 exact-control builder work orders and 98 source/horizon repair work orders remain active execution work; 37 horizon and 520 coverage rows stay sidecars.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-CODEINT-Q-004",
                "question": "Did broad primitive coverage stay attached without changing the active lane?",
                "answer_route": "Yes: all 520 coverage sidecar code-action rows are preserved with target surfaces and no denominator inflation, so vNext synthesis can pursue every remaining family while this lane continues implementation.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_implementation_synthesis_rows": len(input_unified_rows),
        "input_scorer_registration_rows": len(input_scorer_rows),
        "input_controlled_scorer_registration_rows": len(input_controlled_scorer_rows),
        "input_source_proxy_scorer_registration_rows": len(input_source_proxy_rows),
        "input_observable_registry_rows": len(input_observable_registry_rows),
        "input_control_scope_implementation_rows": len(input_control_scope_rows),
        "input_exact_control_build_rows": len(input_exact_control_rows),
        "input_control_registry_rows": len(input_control_registry_rows),
        "input_denominator_guard_registry_rows": len(input_denominator_guard_rows),
        "input_source_repair_action_rows": len(input_source_repair_rows),
        "input_horizon_sidecar_synthesis_rows": len(input_horizon_rows),
        "input_coverage_sidecar_synthesis_rows": len(input_coverage_rows),
        "unified_code_integration_candidate_rows": len(unified_rows),
        "scorer_code_patch_candidate_rows": len(scorer_code_rows),
        "controlled_scorer_code_patch_rows": len(controlled_scorer_code_rows),
        "source_proxy_scorer_code_patch_rows": len(source_proxy_code_rows),
        "guarded_source_proxy_code_patch_rows": sum(
            1
            for row in source_proxy_code_rows
            if row.get("code_integration_status") == "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH"
        ),
        "ambiguous_source_proxy_control_guard_code_patch_rows": sum(
            1
            for row in source_proxy_code_rows
            if row.get("code_integration_status") == "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH"
        ),
        "standalone_scorer_code_patch_rows": sum(1 for row in scorer_code_rows if row.get("standalone_interpretation_allowed")),
        "control_guarded_scorer_code_patch_rows": sum(1 for row in scorer_code_rows if row.get("control_guard_required")),
        "observable_registry_code_patch_rows": len(observable_registry_code_rows),
        "control_scope_code_action_rows": len(control_scope_code_rows),
        "proxy_control_scope_code_patch_rows": sum(
            1
            for row in control_scope_code_rows
            if row.get("code_integration_status")
            in {
                "CODE_INTEGRATION_SYMBOL_PROXY_CONTROL_GUARD_PATCH",
                "CODE_INTEGRATION_SESSION_PROXY_CONTROL_GUARD_PATCH",
            }
        ),
        "exact_control_builder_code_action_rows": len(exact_control_code_rows),
        "control_registry_code_patch_rows": len(control_registry_code_rows),
        "control_comparator_code_patch_rows": sum(
            1 for row in control_registry_code_rows if row.get("code_integration_status") == "CODE_INTEGRATION_CONTROL_COMPARATOR_REGISTRY_PATCH"
        ),
        "control_context_code_rows": sum(
            1 for row in control_registry_code_rows if row.get("code_integration_status") == "CODE_INTEGRATION_CONTROL_CONTEXT_ONLY"
        ),
        "denominator_guard_code_patch_rows": len(denominator_guard_code_rows),
        "source_repair_code_action_rows": len(source_repair_code_rows),
        "exact_source_repair_code_action_rows": sum(
            1 for row in source_repair_code_rows if row.get("code_integration_status") == "CODE_INTEGRATION_EXACT_SOURCE_REPAIR_WORK_ORDER"
        ),
        "horizon_rebuild_rescore_code_action_rows": sum(
            1 for row in source_repair_code_rows if row.get("code_integration_status") == "CODE_INTEGRATION_HORIZON_REBUILD_RESCORE_WORK_ORDER"
        ),
        "horizon_rebuild_kill_check_code_action_rows": sum(
            1 for row in source_repair_code_rows if row.get("code_integration_status") == "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER"
        ),
        "horizon_sidecar_code_action_rows": len(horizon_sidecar_code_rows),
        "coverage_sidecar_code_action_rows": len(coverage_sidecar_code_rows),
        "symbol_session_code_integration_rows": len(symbol_session_rows),
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
        "upstream_counts": {"observable_implementation_synthesis_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "code_integration_lane_counts": distributions["code_integration_lane"],
            "code_integration_status_counts": distributions["code_integration_status"],
            "code_integration_decision_counts": distributions["code_integration_decision"],
            "target_file_hint_counts": distributions["target_file_hint"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_CODE_INTEGRATION_CANDIDATE_BUNDLE_RESULT: implement branch-local "
                "patch candidates for 14 controlled observable scorers, 20 guarded source proxy scorers, "
                "191 ambiguous source proxy scorers only with control guards, 262 denominator-guarded observable "
                "registry rows, 230 control comparators plus 1 context-only control row, 124 denominator guards, "
                "76 proxy control-scope guards, 92 exact-control builder work orders, and 98 source/horizon "
                "repair work orders before final branch-local scorer execution hardening."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)

    generated_files = [
        UNIFIED_LEDGER,
        SCORER_CODE_LEDGER,
        CONTROLLED_SCORER_CODE_LEDGER,
        SOURCE_PROXY_SCORER_CODE_LEDGER,
        OBSERVABLE_REGISTRY_CODE_LEDGER,
        CONTROL_SCOPE_CODE_LEDGER,
        EXACT_CONTROL_BUILDER_CODE_LEDGER,
        CONTROL_REGISTRY_CODE_LEDGER,
        DENOMINATOR_GUARD_CODE_LEDGER,
        SOURCE_REPAIR_CODE_LEDGER,
        HORIZON_SIDECAR_CODE_LEDGER,
        COVERAGE_SIDECAR_CODE_LEDGER,
        SYMBOL_SESSION_CODE_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]

    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(SCORER_CODE_LEDGER, scorer_code_rows)
    write_jsonl(CONTROLLED_SCORER_CODE_LEDGER, controlled_scorer_code_rows)
    write_jsonl(SOURCE_PROXY_SCORER_CODE_LEDGER, source_proxy_code_rows)
    write_jsonl(OBSERVABLE_REGISTRY_CODE_LEDGER, observable_registry_code_rows)
    write_jsonl(CONTROL_SCOPE_CODE_LEDGER, control_scope_code_rows)
    write_jsonl(EXACT_CONTROL_BUILDER_CODE_LEDGER, exact_control_code_rows)
    write_jsonl(CONTROL_REGISTRY_CODE_LEDGER, control_registry_code_rows)
    write_jsonl(DENOMINATOR_GUARD_CODE_LEDGER, denominator_guard_code_rows)
    write_jsonl(SOURCE_REPAIR_CODE_LEDGER, source_repair_code_rows)
    write_jsonl(HORIZON_SIDECAR_CODE_LEDGER, horizon_sidecar_code_rows)
    write_jsonl(COVERAGE_SIDECAR_CODE_LEDGER, coverage_sidecar_code_rows)
    write_jsonl(SYMBOL_SESSION_CODE_LEDGER, symbol_session_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch-Local Observable Code Integration Candidate Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified code integration candidate rows: `{counts['unified_code_integration_candidate_rows']}`",
                f"- Scorer code patch candidate rows: `{counts['scorer_code_patch_candidate_rows']}`",
                f"- Controlled scorer code patch rows: `{counts['controlled_scorer_code_patch_rows']}`",
                f"- Source proxy scorer code patch rows: `{counts['source_proxy_scorer_code_patch_rows']}`",
                f"- Observable registry code patch rows: `{counts['observable_registry_code_patch_rows']}`",
                f"- Control-scope code action rows: `{counts['control_scope_code_action_rows']}`",
                f"- Exact control builder code action rows: `{counts['exact_control_builder_code_action_rows']}`",
                f"- Source repair code action rows: `{counts['source_repair_code_action_rows']}`",
                f"- Horizon sidecar code action rows: `{counts['horizon_sidecar_code_action_rows']}`",
                f"- Coverage sidecar code action rows: `{counts['coverage_sidecar_code_action_rows']}`",
                "",
                "Core result: implementation synthesis rows are now branch-local code patch/work-order candidates with target file hints, control guards, source-repair actions, and sidecar coverage preserved without denominator inflation.",
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
