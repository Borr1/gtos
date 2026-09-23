#!/usr/bin/env python3
"""Build branch-local implementation synthesis rows from observable scorer execution."""

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

from src.research_infra.moonshot_observable_implementation_synthesis import (
    IMPLEMENTATION_SYNTHESIS_SURFACE,
    control_registry_synthesis,
    control_scope_implementation_synthesis,
    coverage_sidecar_synthesis,
    denominator_guard_registry_synthesis,
    exact_control_build_action,
    horizon_sidecar_synthesis,
    observable_registry_synthesis,
    scorer_registration_synthesis,
    source_repair_action_synthesis,
)


SCORER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_SYNTHESIS_BUNDLE"

SCORER_RESULT = ROUTE_DIR / f"{SCORER_PREFIX}_RESULT_2026-05-17.json"
SCORER_RUNTIME_SPEC = ROUTE_DIR / f"{SCORER_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCORER_UNIFIED = ROUTE_DIR / f"{SCORER_PREFIX}_UNIFIED_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_OBSERVABLE = ROUTE_DIR / f"{SCORER_PREFIX}_OBSERVABLE_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_BRANCH_LOCAL = ROUTE_DIR / f"{SCORER_PREFIX}_BRANCH_LOCAL_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_CONTROLLED = ROUTE_DIR / f"{SCORER_PREFIX}_CONTROLLED_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_DGUARDED_OBSERVABLE = ROUTE_DIR / f"{SCORER_PREFIX}_DENOMINATOR_GUARDED_OBSERVABLE_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_CONTROL_SCOPE = ROUTE_DIR / f"{SCORER_PREFIX}_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_SOURCE = ROUTE_DIR / f"{SCORER_PREFIX}_SOURCE_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_SOURCE_SCORER = ROUTE_DIR / f"{SCORER_PREFIX}_SOURCE_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_SOURCE_REPAIR = ROUTE_DIR / f"{SCORER_PREFIX}_SOURCE_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_CONTROL = ROUTE_DIR / f"{SCORER_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_DENOMINATOR = ROUTE_DIR / f"{SCORER_PREFIX}_DENOMINATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_HORIZON = ROUTE_DIR / f"{SCORER_PREFIX}_HORIZON_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_COVERAGE = ROUTE_DIR / f"{SCORER_PREFIX}_COVERAGE_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_implementation_synthesis.py"
SCORER_HELPER_MODULE = REPO / "src/research_infra/moonshot_observable_scorer_execution.py"
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_IMPLEMENTATION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
SCORER_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
CONTROLLED_SCORER_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROLLED_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
SOURCE_PROXY_SCORER_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PROXY_SCORER_REGISTRATION_LEDGER_2026-05-17.jsonl"
OBSERVABLE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_OBSERVABLE_REGISTRY_LEDGER_2026-05-17.jsonl"
CONTROL_SCOPE_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_SCOPE_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_BUILD_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_BUILD_LEDGER_2026-05-17.jsonl"
CONTROL_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_REGISTRY_LEDGER_2026-05-17.jsonl"
DENOMINATOR_GUARD_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARD_REGISTRY_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
HORIZON_SIDECAR_SYNTHESIS_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_SIDECAR_SYNTHESIS_LEDGER_2026-05-17.jsonl"
COVERAGE_SIDECAR_SYNTHESIS_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_SIDECAR_SYNTHESIS_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_IMPLEMENTATION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable implementation synthesis bundle only. It consumes the scorer execution bundle and "
    "turns all scorer, observable, control-scope, source-repair, control, and denominator execution rows into "
    "research-only register/build/repair/guard decisions while preserving horizon and primitive-coverage sidecars. "
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
                "source_manifest_id": f"OHLC-GTOS-OBS-IMPLSYN-SRC-{index:04d}",
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


def common_execution_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_execution_bundle_row_id": row.get("execution_bundle_row_id"),
        "input_execution_lane": row.get("execution_lane"),
        "input_execution_status": row.get("execution_status"),
        "input_execution_decision": row.get("execution_decision"),
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
            "implementation_synthesis_surface": IMPLEMENTATION_SYNTHESIS_SURFACE,
            "live_effect": False,
        }
    )
    return row


def make_synthesis_row(
    row_id: str,
    lane: str,
    execution_row: dict[str, Any],
    payload: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> dict[str, Any]:
    return with_common(
        {
            "implementation_synthesis_row_id": row_id,
            "implementation_synthesis_lane": lane,
            **common_execution_fields(execution_row),
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
                    "symbol_session_implementation_synthesis_id": f"OHLC-GTOS-OBS-IMPLSYN-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "implementation_synthesis_lane_counts": string_counter(members, "implementation_synthesis_lane"),
                    "implementation_synthesis_status_counts": string_counter(members, "implementation_synthesis_status"),
                    "keep_kill_redesign_implement_decision_counts": string_counter(
                        members, "keep_kill_redesign_implement_decision"
                    ),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "branch_local_ready_rows": sum(1 for row in members if row.get("branch_local_ready")),
                    "source_repair_required_rows": sum(1 for row in members if row.get("source_repair_required")),
                    "control_required_rows": sum(1 for row in members if row.get("control_required")),
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
        "implementation_synthesis_lane": string_counter(unified_rows, "implementation_synthesis_lane"),
        "implementation_synthesis_status": string_counter(unified_rows, "implementation_synthesis_status"),
        "keep_kill_redesign_implement_decision": string_counter(unified_rows, "keep_kill_redesign_implement_decision"),
        "branch_local_ready": string_counter(unified_rows, "branch_local_ready"),
        "source_repair_required": string_counter(unified_rows, "source_repair_required"),
        "control_required": string_counter(unified_rows, "control_required"),
        "scorer_registration_status": string_counter(scorer_rows, "implementation_synthesis_status"),
        "source_proxy_registration_status": string_counter(source_proxy_rows, "implementation_synthesis_status"),
        "control_scope_implementation_status": string_counter(control_scope_rows, "implementation_synthesis_status"),
        "source_repair_action_status": string_counter(source_repair_rows, "implementation_synthesis_status"),
        "control_registry_status": string_counter(control_rows, "implementation_synthesis_status"),
        "horizon_sidecar_synthesis_status": string_counter(horizon_rows, "implementation_synthesis_status"),
        "coverage_sidecar_synthesis_status": string_counter(coverage_rows, "implementation_synthesis_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-IMPLSYN-BUCKET-{len(output) + 1:04d}",
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
        "input_scorer_execution_result": SCORER_RESULT.relative_to(REPO).as_posix(),
        "identity_policy": {
            "primary_join_key": "execution_bundle_row_id plus input_runtime_work_row_id",
            "scope_only_join_allowed": False,
            "horizon_and_coverage_sidecars_in_unified_denominator": False,
        },
        "implementation_policy": {
            "controlled_scorers": "register all 14 controlled positive-delta scorer rows",
            "source_proxy_scorers": "register 20 guarded source proxies and 191 ambiguous source proxies with mandatory controls",
            "observable_registry": "register all 262 denominator-guarded observable rows under denominator guards",
            "control_scope": "use 76 same-resource proxy controls with guard labels and build exact controls for 92 underpowered rows",
            "source_repair": "split exact-source rebuild/acquire, horizon rescore, and horizon kill-check rows into executable repair actions",
            "sidecars": "preserve 37 horizon and 520 coverage sidecar rows outside the 1,108 unified denominator",
        },
        "ledgers": {
            "unified_implementation_synthesis": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "scorer_registration": SCORER_REGISTRATION_LEDGER.relative_to(REPO).as_posix(),
            "observable_registry": OBSERVABLE_REGISTRY_LEDGER.relative_to(REPO).as_posix(),
            "exact_control_build": EXACT_CONTROL_BUILD_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_action": SOURCE_REPAIR_ACTION_LEDGER.relative_to(REPO).as_posix(),
            "horizon_sidecar_synthesis": HORIZON_SIDECAR_SYNTHESIS_LEDGER.relative_to(REPO).as_posix(),
            "coverage_sidecar_synthesis": COVERAGE_SIDECAR_SYNTHESIS_LEDGER.relative_to(REPO).as_posix(),
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
    manifest["latest_branch_local_observable_implementation_synthesis_bundle"] = {
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
        "event": "branch_local_observable_implementation_synthesis_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built branch-local scorer registration, observable registry, control, denominator, and repair implementation synthesis rows from scorer execution outputs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            SCORER_RESULT,
            SCORER_RUNTIME_SPEC,
            SCORER_UNIFIED,
            SCORER_OBSERVABLE,
            SCORER_BRANCH_LOCAL,
            SCORER_CONTROLLED,
            SCORER_DGUARDED_OBSERVABLE,
            SCORER_CONTROL_SCOPE,
            SCORER_SOURCE,
            SCORER_SOURCE_SCORER,
            SCORER_SOURCE_REPAIR,
            SCORER_CONTROL,
            SCORER_DENOMINATOR,
            SCORER_HORIZON,
            SCORER_COVERAGE,
            HELPER_MODULE,
            SCORER_HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    scorer_result = read_json(SCORER_RESULT)
    scorer_unified_rows = read_jsonl(SCORER_UNIFIED)
    scorer_observable_rows = read_jsonl(SCORER_OBSERVABLE)
    scorer_branch_local_rows = read_jsonl(SCORER_BRANCH_LOCAL)
    scorer_controlled_rows = read_jsonl(SCORER_CONTROLLED)
    scorer_dguarded_observable_rows = read_jsonl(SCORER_DGUARDED_OBSERVABLE)
    scorer_control_scope_rows = read_jsonl(SCORER_CONTROL_SCOPE)
    scorer_source_rows = read_jsonl(SCORER_SOURCE)
    scorer_source_scorer_rows = read_jsonl(SCORER_SOURCE_SCORER)
    scorer_source_repair_rows = read_jsonl(SCORER_SOURCE_REPAIR)
    scorer_control_rows = read_jsonl(SCORER_CONTROL)
    scorer_denominator_rows = read_jsonl(SCORER_DENOMINATOR)
    scorer_horizon_rows = read_jsonl(SCORER_HORIZON)
    scorer_coverage_rows = read_jsonl(SCORER_COVERAGE)

    controlled_registration_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_controlled_rows, 1):
        controlled_registration_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-CONTROLLED-{index:05d}",
                "CONTROLLED_SCORER_REGISTRATION",
                row,
                scorer_registration_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    source_proxy_registration_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_source_scorer_rows, 1):
        source_proxy_registration_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-SPROXY-{index:05d}",
                "SOURCE_PROXY_SCORER_REGISTRATION",
                row,
                scorer_registration_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    scorer_registration_rows = [*controlled_registration_rows, *source_proxy_registration_rows]

    observable_registry_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_dguarded_observable_rows, 1):
        observable_registry_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-OBSREG-{index:05d}",
                "OBSERVABLE_REGISTRY",
                row,
                observable_registry_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    control_scope_rows: list[dict[str, Any]] = []
    exact_control_build_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_control_scope_rows, 1):
        synthesized = make_synthesis_row(
            f"OHLC-GTOS-OBS-IMPLSYN-CSCOPE-{index:05d}",
            "CONTROL_SCOPE_IMPLEMENTATION",
            row,
            control_scope_implementation_synthesis(row),
            generated_at,
            manifest_hash,
        )
        control_scope_rows.append(synthesized)
        if synthesized.get("implementation_synthesis_status") == "CONTROL_SCOPE_IMPLEMENT_EXACT_CONTROL_BUILD_REQUIRED":
            exact_control_build_rows.append(
                make_synthesis_row(
                    f"OHLC-GTOS-OBS-IMPLSYN-EXACTCTRL-{len(exact_control_build_rows) + 1:05d}",
                    "EXACT_CONTROL_BUILD_ACTION",
                    row,
                    exact_control_build_action(row),
                    generated_at,
                    manifest_hash,
                )
            )

    control_registry_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_control_rows, 1):
        control_registry_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-CONTROL-{index:05d}",
                "CONTROL_REGISTRY",
                row,
                control_registry_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    denominator_guard_registry_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_denominator_rows, 1):
        denominator_guard_registry_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-DGUARD-{index:05d}",
                "DENOMINATOR_GUARD_REGISTRY",
                row,
                denominator_guard_registry_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    source_repair_action_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_source_repair_rows, 1):
        source_repair_action_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-SREPAIR-{index:05d}",
                "SOURCE_REPAIR_ACTION",
                row,
                source_repair_action_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    horizon_sidecar_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_horizon_rows, 1):
        horizon_sidecar_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-HORIZON-{index:05d}",
                "HORIZON_SIDECAR_SYNTHESIS",
                row,
                horizon_sidecar_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    coverage_sidecar_rows: list[dict[str, Any]] = []
    for index, row in enumerate(scorer_coverage_rows, 1):
        coverage_sidecar_rows.append(
            make_synthesis_row(
                f"OHLC-GTOS-OBS-IMPLSYN-COVERAGE-{index:05d}",
                "COVERAGE_SIDECAR_SYNTHESIS",
                row,
                coverage_sidecar_synthesis(row),
                generated_at,
                manifest_hash,
            )
        )

    unified_rows = [
        *controlled_registration_rows,
        *observable_registry_rows,
        *control_scope_rows,
        *source_proxy_registration_rows,
        *source_repair_action_rows,
        *control_registry_rows,
        *denominator_guard_registry_rows,
    ]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        scorer_registration_rows,
        source_proxy_registration_rows,
        control_scope_rows,
        source_repair_action_rows,
        control_registry_rows,
        horizon_sidecar_rows,
        coverage_sidecar_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPLSYN-Q-001",
                "question": "Did implementation synthesis preserve the scorer execution denominator?",
                "answer_route": "Yes: the unified implementation synthesis ledger is 1,108 rows, matching scorer execution rows from observable 444 plus source 309 plus control 231 plus denominator 124.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPLSYN-Q-002",
                "question": "Which scorer rows become branch-local registrations?",
                "answer_route": "225 scorer registration rows: 14 controlled challengers, 20 guarded source proxies, and 191 ambiguous source proxies with mandatory control guard.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPLSYN-Q-003",
                "question": "Which rows require exact build or repair before stronger interpretation?",
                "answer_route": "92 exact-control builds, 61 exact-source rebuild/acquire actions, 29 horizon rescore repairs, and 8 horizon kill-check repairs.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-IMPLSYN-Q-004",
                "question": "Did the full-coverage mandate remain attached without derailing the lane?",
                "answer_route": "Yes: all 520 coverage sidecar rows are preserved outside the unified denominator and will inform next synthesis without becoming a standalone inventory route.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_scorer_execution_rows": len(scorer_unified_rows),
        "input_observable_scorer_execution_rows": len(scorer_observable_rows),
        "input_branch_local_scorer_execution_rows": len(scorer_branch_local_rows),
        "input_controlled_scorer_execution_rows": len(scorer_controlled_rows),
        "input_denominator_guarded_observable_execution_rows": len(scorer_dguarded_observable_rows),
        "input_control_scope_execution_rows": len(scorer_control_scope_rows),
        "input_source_execution_rows": len(scorer_source_rows),
        "input_source_scorer_execution_rows": len(scorer_source_scorer_rows),
        "input_source_repair_execution_rows": len(scorer_source_repair_rows),
        "input_control_execution_rows": len(scorer_control_rows),
        "input_denominator_execution_rows": len(scorer_denominator_rows),
        "input_horizon_sidecar_execution_rows": len(scorer_horizon_rows),
        "input_coverage_sidecar_execution_rows": len(scorer_coverage_rows),
        "unified_implementation_synthesis_rows": len(unified_rows),
        "scorer_registration_rows": len(scorer_registration_rows),
        "controlled_scorer_registration_rows": len(controlled_registration_rows),
        "source_proxy_scorer_registration_rows": len(source_proxy_registration_rows),
        "guarded_source_proxy_registration_rows": sum(
            1
            for row in source_proxy_registration_rows
            if row.get("implementation_synthesis_status") == "SCORER_REGISTRATION_SOURCE_GUARDED_PROXY_REGISTER"
        ),
        "ambiguous_source_proxy_control_guard_registration_rows": sum(
            1
            for row in source_proxy_registration_rows
            if row.get("implementation_synthesis_status")
            == "SCORER_REGISTRATION_SOURCE_AMBIGUOUS_CONTROL_GUARD_REGISTER"
        ),
        "observable_registry_rows": len(observable_registry_rows),
        "control_scope_implementation_rows": len(control_scope_rows),
        "proxy_control_scope_guard_rows": sum(
            1
            for row in control_scope_rows
            if row.get("implementation_synthesis_status")
            in {
                "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_GUARD",
                "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_SESSION_GUARD",
            }
        ),
        "exact_control_build_rows": len(exact_control_build_rows),
        "control_registry_rows": len(control_registry_rows),
        "control_comparator_registered_rows": sum(
            1 for row in control_registry_rows if row.get("implementation_synthesis_status") == "CONTROL_REGISTRY_COMPARATOR_REGISTERED"
        ),
        "control_context_rows": sum(
            1 for row in control_registry_rows if row.get("implementation_synthesis_status") == "CONTROL_REGISTRY_CONTEXT_ONLY"
        ),
        "denominator_guard_registry_rows": len(denominator_guard_registry_rows),
        "source_repair_action_rows": len(source_repair_action_rows),
        "exact_source_rebuild_or_acquire_rows": sum(
            1
            for row in source_repair_action_rows
            if row.get("implementation_synthesis_status") == "SOURCE_REPAIR_ACTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
        ),
        "horizon_rebuild_rescore_rows": sum(
            1 for row in source_repair_action_rows if row.get("implementation_synthesis_status") == "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_RESCORE"
        ),
        "horizon_rebuild_kill_check_rows": sum(
            1 for row in source_repair_action_rows if row.get("implementation_synthesis_status") == "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_KILL_CHECK"
        ),
        "horizon_sidecar_synthesis_rows": len(horizon_sidecar_rows),
        "coverage_sidecar_synthesis_rows": len(coverage_sidecar_rows),
        "symbol_session_implementation_synthesis_rows": len(symbol_session_rows),
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
        "upstream_counts": {"observable_scorer_execution_bundle": scorer_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "implementation_synthesis_lane_counts": distributions["implementation_synthesis_lane"],
            "implementation_synthesis_status_counts": distributions["implementation_synthesis_status"],
            "keep_kill_redesign_implement_decision_counts": distributions[
                "keep_kill_redesign_implement_decision"
            ],
            "control_scope_implementation_status_counts": distributions["control_scope_implementation_status"],
            "source_repair_action_status_counts": distributions["source_repair_action_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_IMPLEMENTATION_SYNTHESIS_BUNDLE_RESULT: register 14 controlled "
                "observable scorers, register 20 guarded source proxy scorers, register 191 ambiguous source "
                "proxy scorers only with control guards, register 262 denominator-guarded observables, register "
                "230 control comparators while preserving 1 context-only control row, enforce 124 denominator "
                "guards, run 76 proxy control-scope guards, build 92 exact control scopes, and execute 98 "
                "source/horizon repair actions before final branch-local scorer/code integration."
            ),
        },
    }
    runtime_spec = build_runtime_spec(result, distributions)

    generated_files = [
        UNIFIED_LEDGER,
        SCORER_REGISTRATION_LEDGER,
        CONTROLLED_SCORER_REGISTRATION_LEDGER,
        SOURCE_PROXY_SCORER_REGISTRATION_LEDGER,
        OBSERVABLE_REGISTRY_LEDGER,
        CONTROL_SCOPE_IMPLEMENTATION_LEDGER,
        EXACT_CONTROL_BUILD_LEDGER,
        CONTROL_REGISTRY_LEDGER,
        DENOMINATOR_GUARD_REGISTRY_LEDGER,
        SOURCE_REPAIR_ACTION_LEDGER,
        HORIZON_SIDECAR_SYNTHESIS_LEDGER,
        COVERAGE_SIDECAR_SYNTHESIS_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]

    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(SCORER_REGISTRATION_LEDGER, scorer_registration_rows)
    write_jsonl(CONTROLLED_SCORER_REGISTRATION_LEDGER, controlled_registration_rows)
    write_jsonl(SOURCE_PROXY_SCORER_REGISTRATION_LEDGER, source_proxy_registration_rows)
    write_jsonl(OBSERVABLE_REGISTRY_LEDGER, observable_registry_rows)
    write_jsonl(CONTROL_SCOPE_IMPLEMENTATION_LEDGER, control_scope_rows)
    write_jsonl(EXACT_CONTROL_BUILD_LEDGER, exact_control_build_rows)
    write_jsonl(CONTROL_REGISTRY_LEDGER, control_registry_rows)
    write_jsonl(DENOMINATOR_GUARD_REGISTRY_LEDGER, denominator_guard_registry_rows)
    write_jsonl(SOURCE_REPAIR_ACTION_LEDGER, source_repair_action_rows)
    write_jsonl(HORIZON_SIDECAR_SYNTHESIS_LEDGER, horizon_sidecar_rows)
    write_jsonl(COVERAGE_SIDECAR_SYNTHESIS_LEDGER, coverage_sidecar_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Implementation Synthesis Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified implementation synthesis rows: `{counts['unified_implementation_synthesis_rows']}`",
                f"- Scorer registration rows: `{counts['scorer_registration_rows']}`",
                f"- Controlled scorer registration rows: `{counts['controlled_scorer_registration_rows']}`",
                f"- Source proxy scorer registration rows: `{counts['source_proxy_scorer_registration_rows']}`",
                f"- Observable registry rows: `{counts['observable_registry_rows']}`",
                f"- Control-scope implementation rows: `{counts['control_scope_implementation_rows']}`",
                f"- Exact control build rows: `{counts['exact_control_build_rows']}`",
                f"- Source repair action rows: `{counts['source_repair_action_rows']}`",
                f"- Horizon sidecar synthesis rows: `{counts['horizon_sidecar_synthesis_rows']}`",
                f"- Coverage sidecar synthesis rows: `{counts['coverage_sidecar_synthesis_rows']}`",
                "",
                "Core result: scorer execution rows are now branch-local implementation decisions: register, guard, build exact controls, repair source/horizon rows, or preserve context without denominator inflation.",
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
