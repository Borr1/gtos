#!/usr/bin/env python3
"""Execute branch-local observable exact-control/source/horizon repair work orders."""

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

from src.research_infra.moonshot_branch_local_repair_execution import (
    REPAIR_EXECUTION_SURFACE,
    coverage_carryforward_execution,
    exact_control_repair_execution,
    horizon_sidecar_repair_execution,
    source_repair_work_execution,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_MODULE_MATERIALIZATION_BUNDLE"
SCORER_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_MODULE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_CONTROL_WORK_ORDER_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_WORK_ORDER_SIDECAR_LEDGER_2026-05-17.jsonl"
INPUT_COVERAGE = ROUTE_DIR / f"{INPUT_PREFIX}_COVERAGE_REGISTRY_SIDECAR_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_EXECUTION = ROUTE_DIR / f"{SCORER_EXEC_PREFIX}_SOURCE_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_SCOPE_EXECUTION = ROUTE_DIR / f"{SCORER_EXEC_PREFIX}_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / REPAIR_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
HORIZON_SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"
COVERAGE_CARRYFORWARD_LEDGER = ROUTE_DIR / f"{PREFIX}_COVERAGE_CARRYFORWARD_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local observable repair execution bundle only. It executes exact-control, source-repair, and horizon "
    "sidecar work orders from current same-resource rows into proxy/control-scored work-result rows. It preserves "
    "the 1,108 module-materialization denominator, keeps horizon and primitive-coverage sidecars separate, does not "
    "change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
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
                "source_manifest_id": f"OHLC-GTOS-OBS-REPAIREXEC-SRC-{index:04d}",
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


def make_execution_row(
    row_id: str,
    module_row: dict[str, Any],
    payload: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> dict[str, Any]:
    payload.update(
        {
            "repair_execution_row_id": row_id,
            "input_module_materialization_lane": module_row.get("module_materialization_lane"),
        }
    )
    return with_common(payload, generated_at, manifest_hash)


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
                    "symbol_session_repair_execution_id": f"OHLC-GTOS-OBS-REPAIREXEC-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "repair_execution_lane_counts": string_counter(members, "repair_execution_lane"),
                    "repair_execution_status_counts": string_counter(members, "repair_execution_status"),
                    "can_score_now_rows": sum(1 for row in members if row.get("can_score_now")),
                    "requirement_open_rows": sum(
                        1
                        for row in members
                        if row.get("source_repair_requirement_open") or row.get("exact_control_requirement_open")
                    ),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    primary_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    exact_control_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "repair_execution_lane": string_counter(primary_rows, "repair_execution_lane"),
        "repair_execution_status": string_counter(primary_rows, "repair_execution_status"),
        "repair_execution_result_class": string_counter(primary_rows, "repair_execution_result_class"),
        "can_score_now": string_counter(primary_rows, "can_score_now"),
        "source_repair_requirement_open": string_counter(source_rows, "source_repair_requirement_open"),
        "exact_control_requirement_open": string_counter(exact_control_rows, "exact_control_requirement_open"),
        "source_repair_family": string_counter(source_rows, "source_repair_family"),
        "source_repair_status": string_counter(source_rows, "repair_execution_status"),
        "exact_control_status": string_counter(exact_control_rows, "repair_execution_status"),
        "horizon_sidecar_status": string_counter(horizon_rows, "repair_execution_status"),
        "coverage_carryforward_status": string_counter(coverage_rows, "repair_execution_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(primary_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-OBS-REPAIREXEC-BUCKET-{len(output) + 1:04d}",
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
    manifest["latest_branch_local_observable_repair_execution_bundle"] = {
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
        "event": "branch_local_observable_repair_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed exact-control/source/horizon repair work orders into proxy/control-scored research rows.",
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
            INPUT_SOURCE_REPAIR,
            INPUT_EXACT_CONTROL,
            INPUT_HORIZON,
            INPUT_COVERAGE,
            INPUT_SOURCE_EXECUTION,
            INPUT_CONTROL_SCOPE_EXECUTION,
            HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_unified_rows = read_jsonl(INPUT_UNIFIED)
    source_module_rows = read_jsonl(INPUT_SOURCE_REPAIR)
    exact_control_module_rows = read_jsonl(INPUT_EXACT_CONTROL)
    horizon_module_rows = read_jsonl(INPUT_HORIZON)
    coverage_module_rows = read_jsonl(INPUT_COVERAGE)
    source_execution_rows = read_jsonl(INPUT_SOURCE_EXECUTION)
    control_scope_execution_rows = read_jsonl(INPUT_CONTROL_SCOPE_EXECUTION)

    source_execution_by_bundle = {row.get("execution_bundle_row_id"): row for row in source_execution_rows}
    control_scope_execution_by_bundle = {row.get("execution_bundle_row_id"): row for row in control_scope_execution_rows}

    source_repair_execution_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_module_rows, 1):
        payload = source_repair_work_execution(row, source_execution_by_bundle.get(row.get("input_execution_bundle_row_id")))
        source_repair_execution_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-REPAIREXEC-SOURCE-{index:05d}",
                row,
                payload,
                generated_at,
                manifest_hash,
            )
        )

    exact_control_execution_rows: list[dict[str, Any]] = []
    for index, row in enumerate(exact_control_module_rows, 1):
        payload = exact_control_repair_execution(
            row,
            control_scope_execution_by_bundle.get(row.get("input_execution_bundle_row_id")),
        )
        exact_control_execution_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-REPAIREXEC-EXACTCTRL-{index:05d}",
                row,
                payload,
                generated_at,
                manifest_hash,
            )
        )

    source_repair_rows_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_repair_execution_rows:
        if row.get("observable_scope_key"):
            source_repair_rows_by_scope[str(row.get("observable_scope_key"))].append(row)

    horizon_sidecar_execution_rows: list[dict[str, Any]] = []
    for index, row in enumerate(horizon_module_rows, 1):
        payload = horizon_sidecar_repair_execution(
            row,
            source_repair_rows_by_scope.get(str(row.get("observable_scope_key")), []),
        )
        horizon_sidecar_execution_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-REPAIREXEC-HORIZON-{index:05d}",
                row,
                payload,
                generated_at,
                manifest_hash,
            )
        )

    coverage_carryforward_rows: list[dict[str, Any]] = []
    for index, row in enumerate(coverage_module_rows, 1):
        payload = coverage_carryforward_execution(row)
        coverage_carryforward_rows.append(
            make_execution_row(
                f"OHLC-GTOS-OBS-REPAIREXEC-COVERAGE-{index:05d}",
                row,
                payload,
                generated_at,
                manifest_hash,
            )
        )

    unified_repair_rows = [*source_repair_execution_rows, *exact_control_execution_rows]
    symbol_session_rows = build_symbol_session_rows(unified_repair_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_repair_rows,
        source_repair_execution_rows,
        exact_control_execution_rows,
        horizon_sidecar_execution_rows,
        coverage_carryforward_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-REPAIREXEC-Q-001",
                "question": "Did repair execution move beyond work-order materialization?",
                "answer_route": "Yes: 98 source-repair rows and 92 exact-control rows were executed into proxy/control-scored work-result rows from current same-resource scorer/control inputs.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-REPAIREXEC-Q-002",
                "question": "Did exact-control rows become usable scalar rows?",
                "answer_route": "No exact same-scope n20 controls are present in current rows; global proxy controls were computed and exact-scope control requirements remain open.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-REPAIREXEC-Q-003",
                "question": "Did source-repair rows produce lower-level metrics?",
                "answer_route": "Yes: source proxy scores, horizon proxy scores where present, fail-closed ratios, targetable ratios, duplicate scope counts, and exact repair causes are preserved per row.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-REPAIREXEC-Q-004",
                "question": "Did horizon and coverage remain sidecars?",
                "answer_route": "Yes: 37 horizon sidecar rows and 520 primitive-coverage carryforward rows remain outside the 190-row repair execution denominator.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-OBS-REPAIREXEC-Q-005",
                "question": "What concrete lane follows this packet?",
                "answer_route": "Use exact-control global-proxy failures and exact-source/horizon requirements to build exact source/control acquisition or stronger proxy replay rows while keeping coverage map breadth active.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    source_repair_with_proxy_score = sum(1 for row in source_repair_execution_rows if row.get("source_proxy_score") is not None)
    exact_control_with_proxy_score = sum(
        1 for row in exact_control_execution_rows if row.get("control_proxy_score_lower_bound") is not None
    )
    linked_horizon_rows = sum(
        1 for row in horizon_sidecar_execution_rows if row.get("linked_source_repair_execution_count", 0) > 0
    )
    counts = {
        "input_unified_module_materialization_rows": len(input_unified_rows),
        "input_source_repair_module_materialization_rows": len(source_module_rows),
        "input_exact_control_work_order_rows": len(exact_control_module_rows),
        "input_horizon_work_order_sidecar_rows": len(horizon_module_rows),
        "input_coverage_registry_sidecar_rows": len(coverage_module_rows),
        "input_source_repair_execution_rows": len(source_execution_rows),
        "input_control_scope_execution_rows": len(control_scope_execution_rows),
        "unified_repair_execution_rows": len(unified_repair_rows),
        "source_repair_work_execution_rows": len(source_repair_execution_rows),
        "exact_control_repair_execution_rows": len(exact_control_execution_rows),
        "horizon_repair_sidecar_execution_rows": len(horizon_sidecar_execution_rows),
        "coverage_carryforward_rows": len(coverage_carryforward_rows),
        "source_repair_with_proxy_score_rows": source_repair_with_proxy_score,
        "exact_control_with_proxy_score_rows": exact_control_with_proxy_score,
        "repaired_or_control_scored_rows": source_repair_with_proxy_score + exact_control_with_proxy_score,
        "exact_control_requirement_open_rows": sum(1 for row in exact_control_execution_rows if row.get("exact_control_requirement_open")),
        "source_repair_requirement_open_rows": sum(1 for row in source_repair_execution_rows if row.get("source_repair_requirement_open")),
        "horizon_sidecar_linked_scope_rows": linked_horizon_rows,
        "symbol_session_repair_execution_rows": len(symbol_session_rows),
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
            "observable_module_materialization_bundle": input_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "repair_execution_lane_counts": distributions["repair_execution_lane"],
            "repair_execution_status_counts": distributions["repair_execution_status"],
            "source_repair_family_counts": distributions["source_repair_family"],
            "system_recommendation": (
                "BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_RESULT: execute all 98 source repair work rows "
                "and all 92 exact-control work rows into proxy/control-scored research rows; preserve 37 horizon "
                "sidecars and 520 primitive-coverage rows outside the denominator; continue with exact source/control "
                "acquisition or stronger proxy replay rows where requirements remain open."
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
        "input_module_materialization_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "identity_policy": {
            "primary_join_key": "input_execution_bundle_row_id plus input_module_materialization_row_id",
            "primary_repair_denominator": "98 source repair rows + 92 exact-control rows = 190",
            "horizon_and_coverage_sidecars_in_primary_denominator": False,
            "scope_only_join_allowed_for_primary": False,
        },
        "execution_policy": {
            "exact_control": "score exact-control work orders only from exact/symbol/session/global control counts already computed; withhold scalar interpretation when exact same-scope controls remain absent",
            "source_repair": "preserve source/horizon proxy metrics and exact repair causes from current same-resource scorer execution rows",
            "horizon_sidecar": "link by scope to source-repair rows but keep outside the primary denominator",
            "coverage": "carry forward primitive coverage map outside the primary denominator",
        },
        "repair_execution_distributions": distributions,
    }

    generated_files = [
        UNIFIED_REPAIR_LEDGER,
        SOURCE_REPAIR_LEDGER,
        EXACT_CONTROL_LEDGER,
        HORIZON_SIDECAR_LEDGER,
        COVERAGE_CARRYFORWARD_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_REPAIR_LEDGER, unified_repair_rows)
    write_jsonl(SOURCE_REPAIR_LEDGER, source_repair_execution_rows)
    write_jsonl(EXACT_CONTROL_LEDGER, exact_control_execution_rows)
    write_jsonl(HORIZON_SIDECAR_LEDGER, horizon_sidecar_execution_rows)
    write_jsonl(COVERAGE_CARRYFORWARD_LEDGER, coverage_carryforward_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Observable Repair Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified repair execution rows: `{counts['unified_repair_execution_rows']}`",
                f"- Source repair work execution rows: `{counts['source_repair_work_execution_rows']}`",
                f"- Exact-control repair execution rows: `{counts['exact_control_repair_execution_rows']}`",
                f"- Horizon repair sidecar execution rows: `{counts['horizon_repair_sidecar_execution_rows']}`",
                f"- Primitive coverage carryforward rows: `{counts['coverage_carryforward_rows']}`",
                f"- Repaired or control-scored rows: `{counts['repaired_or_control_scored_rows']}`",
                "",
                "Core result: open repair work orders are now concrete execution outcomes with exact cause, proxy score, control denominator, and next-action fields.",
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
