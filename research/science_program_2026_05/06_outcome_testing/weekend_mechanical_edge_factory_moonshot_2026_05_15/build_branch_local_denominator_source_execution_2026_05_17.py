#!/usr/bin/env python3
"""Execute denominator/source rebuild rows into branch-local decisions."""

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

from src.research_infra.moonshot_branch_local_denominator_source_execution import (
    DENOMINATOR_SOURCE_EXECUTION_SURFACE,
    exact_control_scope_execution,
    exact_control_target_execution,
    horizon_rebuild_execution,
    scope_action_execution,
    source_rebuild_execution,
)


REBUILD_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_REBUILD_BUNDLE"
SOURCE_MAT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_EXECUTION_BUNDLE"

REBUILD_RESULT = ROUTE_DIR / f"{REBUILD_PREFIX}_RESULT_2026-05-17.json"
REBUILD_RUNTIME = ROUTE_DIR / f"{REBUILD_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
REBUILD_UNIFIED = ROUTE_DIR / f"{REBUILD_PREFIX}_UNIFIED_DENOMINATOR_SOURCE_REBUILD_LEDGER_2026-05-17.jsonl"
REBUILD_EXACT_TARGET = ROUTE_DIR / f"{REBUILD_PREFIX}_EXACT_CONTROL_TARGET_DENOMINATOR_LEDGER_2026-05-17.jsonl"
REBUILD_EXACT_SCOPE = ROUTE_DIR / f"{REBUILD_PREFIX}_EXACT_CONTROL_SCOPE_DENOMINATOR_LEDGER_2026-05-17.jsonl"
REBUILD_MEMBER = ROUTE_DIR / f"{REBUILD_PREFIX}_CONTROL_MEMBER_DENOMINATOR_EVIDENCE_LEDGER_2026-05-17.jsonl"
REBUILD_SOURCE = ROUTE_DIR / f"{REBUILD_PREFIX}_SOURCE_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
REBUILD_HORIZON = ROUTE_DIR / f"{REBUILD_PREFIX}_HORIZON_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
REBUILD_SCOPE = ROUTE_DIR / f"{REBUILD_PREFIX}_SCOPE_REBUILD_ACTION_LEDGER_2026-05-17.jsonl"
REBUILD_SYMBOL_SESSION = ROUTE_DIR / f"{REBUILD_PREFIX}_SYMBOL_SESSION_DENOMINATOR_SOURCE_REBUILD_LEDGER_2026-05-17.jsonl"

SOURCE_MATERIALIZATION = ROUTE_DIR / f"{SOURCE_MAT_PREFIX}_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / DENOMINATOR_SOURCE_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_DENOMINATOR_SOURCE_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_TARGET_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_TARGET_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
HORIZON_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
SCOPE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_EXECUTION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local denominator/source execution bundle only. It converts denominator/source rebuild rows into "
    "exact-control, source-rebuild, and horizon-rebuild result decisions using current same-resource rows and "
    "proxy guards. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-SRC-EXEC-SRC-{index:04d}",
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
            "live_effect": False,
        }
    )
    return row


def make_row(row_id_key: str, row_id: str, payload: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    payload[row_id_key] = row_id
    return with_common(payload, generated_at, manifest_hash)


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def source_code_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_code_candidate_id")): row for row in rows}


def group_by_scope(rows: list[dict[str, Any]]) -> dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[scope_key(row)].append(row)
    return grouped


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {name: int(counter[name]) for name in sorted(counter)}


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
                    "symbol_session_denominator_source_execution_id": f"OHLC-GTOS-DENOM-SRC-EXEC-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "denominator_source_execution_lane_counts": string_counter(
                        members, "denominator_source_execution_lane"
                    ),
                    "denominator_source_execution_status_counts": string_counter(
                        members, "denominator_source_execution_status"
                    ),
                    "keep_kill_redesign_counts": string_counter(members, "keep_kill_redesign_decision"),
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
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "denominator_source_execution_lane": string_counter(unified_rows, "denominator_source_execution_lane"),
        "denominator_source_execution_status": string_counter(unified_rows, "denominator_source_execution_status"),
        "keep_kill_redesign_decision": string_counter([*source_rows, *horizon_rows, *scope_rows], "keep_kill_redesign_decision"),
        "exact_target_status": string_counter(exact_target_rows, "denominator_source_execution_status"),
        "exact_scope_status": string_counter(exact_scope_rows, "denominator_source_execution_status"),
        "source_execution_status": string_counter(source_rows, "denominator_source_execution_status"),
        "source_proxy_result_class": string_counter(source_rows, "materialization_proxy_r_style_result_class"),
        "horizon_execution_status": string_counter(horizon_rows, "denominator_source_execution_status"),
        "horizon_proxy_result_class": string_counter(horizon_rows, "horizon_proxy_r_style_result_class"),
        "scope_action_status": string_counter(scope_rows, "denominator_source_execution_status"),
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
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-EXEC-BUCKET-{len(output) + 1:04d}",
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
    manifest["latest_branch_local_denominator_source_execution_bundle"] = {
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
        "event": "branch_local_denominator_source_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed exact-control, exact-source, and horizon rebuild rows into keep/kill/redesign/proxy-scored decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            REBUILD_RESULT,
            REBUILD_RUNTIME,
            REBUILD_UNIFIED,
            REBUILD_EXACT_TARGET,
            REBUILD_EXACT_SCOPE,
            REBUILD_MEMBER,
            REBUILD_SOURCE,
            REBUILD_HORIZON,
            REBUILD_SCOPE,
            REBUILD_SYMBOL_SESSION,
            SOURCE_MATERIALIZATION,
            HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    rebuild_result = read_json(REBUILD_RESULT)
    rebuild_unified = read_jsonl(REBUILD_UNIFIED)
    exact_target_input = read_jsonl(REBUILD_EXACT_TARGET)
    exact_scope_input = read_jsonl(REBUILD_EXACT_SCOPE)
    source_input = read_jsonl(REBUILD_SOURCE)
    horizon_input = read_jsonl(REBUILD_HORIZON)
    scope_input = read_jsonl(REBUILD_SCOPE)
    source_materialization_input = read_jsonl(SOURCE_MATERIALIZATION)
    materialization_index = source_code_index(source_materialization_input)

    exact_target_rows = [
        make_row(
            "denominator_source_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-EXEC-EXACTTARGET-{index:05d}",
            exact_control_target_execution(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exact_target_input, 1)
    ]
    exact_scope_rows = [
        make_row(
            "exact_control_scope_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-EXEC-EXACTSCOPE-{index:05d}",
            exact_control_scope_execution(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exact_scope_input, 1)
    ]
    source_rows = [
        make_row(
            "denominator_source_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-EXEC-SOURCE-{index:05d}",
            source_rebuild_execution(row, materialization_index.get(str(row.get("source_code_candidate_id")))),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(source_input, 1)
    ]
    horizon_rows = [
        make_row(
            "denominator_source_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-EXEC-HORIZON-{index:05d}",
            horizon_rebuild_execution(row, materialization_index.get(str(row.get("source_code_candidate_id")))),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(horizon_input, 1)
    ]

    exact_scope_by_scope = {scope_key(row): row for row in exact_scope_rows}
    source_by_scope = group_by_scope(source_rows)
    horizon_by_scope = group_by_scope(horizon_rows)
    scope_rows = [
        make_row(
            "scope_action_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-EXEC-SCOPE-{index:05d}",
            scope_action_execution(
                row,
                exact_scope_by_scope.get(scope_key(row)),
                source_by_scope.get(scope_key(row), []),
                horizon_by_scope.get(scope_key(row), []),
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(scope_input, 1)
    ]

    unified_rows = [*exact_target_rows, *source_rows, *horizon_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        exact_target_rows,
        exact_scope_rows,
        source_rows,
        horizon_rows,
        scope_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-EXEC-Q-001",
                "question": "Did exact-control scope execution repair exact denominators from current rows?",
                "answer_route": "No. Current exact rows remain absent. Four scopes have proxy n20 guard rows; nineteen scopes stay underpowered and require exact-control denominator construction before scalar use.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-EXEC-Q-002",
                "question": "What decision follows from the 61 exact-source rebuild rows?",
                "answer_route": "All 61 exact-source rows have negative proxy-R intervals; the proxy candidates are killed while exact-source rebuild requirements remain preserved for contradiction checks.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-EXEC-Q-003",
                "question": "What decision follows from the 37 horizon rows?",
                "answer_route": "Seventeen require targetable-horizon repair and rescore, twelve require high-failclosed redesign/rescore, and eight require kill-check repair if rebuilt targetable rows remain negative.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-EXEC-Q-004",
                "question": "Did this packet add another transfer layer?",
                "answer_route": "No. It consumes the 23/61/37 rebuild action scopes and emits result decisions, keep/kill/redesign states, proxy score classes, and implementation implications.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_rebuild_unified_rows": len(rebuild_unified),
        "input_exact_control_target_rows": len(exact_target_input),
        "input_exact_control_scope_rows": len(exact_scope_input),
        "input_source_rebuild_rows": len(source_input),
        "input_horizon_rebuild_rows": len(horizon_input),
        "input_scope_action_rows": len(scope_input),
        "input_source_materialization_rows": len(source_materialization_input),
        "unified_denominator_source_execution_rows": len(unified_rows),
        "exact_control_target_execution_rows": len(exact_target_rows),
        "exact_control_scope_execution_rows": len(exact_scope_rows),
        "source_rebuild_execution_rows": len(source_rows),
        "horizon_rebuild_execution_rows": len(horizon_rows),
        "scope_action_execution_rows": len(scope_rows),
        "symbol_session_execution_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
        "exact_control_scope_proxy_n20_rows": sum(
            1
            for row in exact_scope_rows
            if row.get("denominator_source_execution_status")
            == "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_PROXY_N20_SCORE_WITH_GUARD"
        ),
        "exact_control_scope_underpowered_rows": sum(
            1
            for row in exact_scope_rows
            if row.get("denominator_source_execution_status")
            == "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_PROXY_UNDER_N20_BUILD_REQUIRED"
        ),
        "source_proxy_kill_rows": sum(
            1 for row in source_rows if row.get("keep_kill_redesign_decision") == "KILL_PROXY"
        ),
        "horizon_kill_check_rows": sum(
            1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "KILL_CHECK"
        ),
        "horizon_redesign_rows": sum(
            1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "REDESIGN"
        ),
        "horizon_repair_rows": sum(
            1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "REPAIR"
        ),
    }
    runtime_spec = with_common(
        {
            "runtime_spec_id": "OHLC-GTOS-DENOM-SRC-EXEC-RUNTIME-0001",
            "artifact": PREFIX,
            "inputs": {
                "rebuild_result": REBUILD_RESULT.relative_to(REPO).as_posix(),
                "rebuild_unified": REBUILD_UNIFIED.relative_to(REPO).as_posix(),
                "source_materialization": SOURCE_MATERIALIZATION.relative_to(REPO).as_posix(),
            },
            "outputs": {
                "unified": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
                "exact_target": EXACT_TARGET_LEDGER.relative_to(REPO).as_posix(),
                "exact_scope": EXACT_SCOPE_LEDGER.relative_to(REPO).as_posix(),
                "source": SOURCE_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
                "horizon": HORIZON_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
                "scope": SCOPE_EXECUTION_LEDGER.relative_to(REPO).as_posix(),
            },
            "execution_contract": "consume every exact-control/source/horizon rebuild row and emit result decisions without top-N truncation",
        },
        generated_at,
        manifest_hash,
    )
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": counts,
        "bucket_distributions": distributions,
        "source_manifest_hash": manifest_hash,
        "upstream_counts": {"denominator_source_rebuild_bundle": rebuild_result.get("counts", {})},
        "system_decision": {
            "denominator_source_execution_status_counts": distributions["denominator_source_execution_status"],
            "scope_action_status_counts": distributions["scope_action_status"],
            "keep_kill_redesign_counts": distributions["keep_kill_redesign_decision"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_SOURCE_EXECUTION_BUNDLE_RESULT: kill all negative exact-source proxy "
                "candidates pending contradiction by exact rebuild; keep four exact-control scope proxy guards while "
                "building exact denominators; repair/redesign/kill-check horizon scopes before implementation use."
            ),
        },
    }

    summary = "\n".join(
        [
            "# Branch-Local Denominator Source Execution Bundle",
            "",
            f"Generated UTC: `{generated_at}`",
            "",
            f"- Unified execution rows: `{len(unified_rows)}`.",
            f"- Exact-control scope execution rows: `{len(exact_scope_rows)}` (`{counts['exact_control_scope_proxy_n20_rows']}` proxy n20, `{counts['exact_control_scope_underpowered_rows']}` underpowered build-required).",
            f"- Source rebuild execution rows: `{len(source_rows)}` (`{counts['source_proxy_kill_rows']}` negative proxy kills with exact rebuild preserved).",
            f"- Horizon rebuild execution rows: `{len(horizon_rows)}` (`{counts['horizon_repair_rows']}` repair/rescore, `{counts['horizon_redesign_rows']}` high-failclosed redesign, `{counts['horizon_kill_check_rows']}` kill-check).",
            "- No live behavior, validation, promotion, broker R/PnL, win-rate, or expectancy claim is made.",
            "",
        ]
    )

    output_paths = [
        RESULT_PATH,
        UNIFIED_LEDGER,
        EXACT_TARGET_LEDGER,
        EXACT_SCOPE_LEDGER,
        SOURCE_EXECUTION_LEDGER,
        HORIZON_EXECUTION_LEDGER,
        SCOPE_EXECUTION_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
        SUMMARY_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(EXACT_TARGET_LEDGER, exact_target_rows)
    write_jsonl(EXACT_SCOPE_LEDGER, exact_scope_rows)
    write_jsonl(SOURCE_EXECUTION_LEDGER, source_rows)
    write_jsonl(HORIZON_EXECUTION_LEDGER, horizon_rows)
    write_jsonl(SCOPE_EXECUTION_LEDGER, scope_rows)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_session_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(SUMMARY_PATH, summary)
    append_manifest(output_paths, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
