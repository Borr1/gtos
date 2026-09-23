#!/usr/bin/env python3
"""Build implementation/action candidates from denominator/source execution rows."""

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

from src.research_infra.moonshot_branch_local_denominator_source_action_candidates import (
    DENOMINATOR_SOURCE_ACTION_SURFACE,
    acquisition_requirement_from_action,
    exact_control_scope_action_candidate,
    exact_control_target_action_candidate,
    horizon_repair_action_candidate,
    scope_rollup_action_candidate,
    source_proxy_kill_action_candidate,
)


EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_CANDIDATE_BUNDLE"

EXEC_RESULT = ROUTE_DIR / f"{EXEC_PREFIX}_RESULT_2026-05-17.json"
EXEC_RUNTIME = ROUTE_DIR / f"{EXEC_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXEC_UNIFIED = ROUTE_DIR / f"{EXEC_PREFIX}_UNIFIED_DENOMINATOR_SOURCE_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_EXACT_TARGET = ROUTE_DIR / f"{EXEC_PREFIX}_EXACT_CONTROL_TARGET_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_EXACT_SCOPE = ROUTE_DIR / f"{EXEC_PREFIX}_EXACT_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_SOURCE = ROUTE_DIR / f"{EXEC_PREFIX}_SOURCE_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_HORIZON = ROUTE_DIR / f"{EXEC_PREFIX}_HORIZON_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_SCOPE = ROUTE_DIR / f"{EXEC_PREFIX}_SCOPE_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DENOMINATOR_SOURCE_ACTION_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_ACTION_CANDIDATE_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_TABLE = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_DECISION_TABLE_2026-05-17.jsonl"
EXACT_TARGET_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_TARGET_ACTION_LEDGER_2026-05-17.jsonl"
EXACT_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_SCOPE_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PROXY_KILL_ACTION_LEDGER_2026-05-17.jsonl"
HORIZON_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_ACTION_LEDGER_2026-05-17.jsonl"
ACQUISITION_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACTION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local denominator/source action-candidate bundle only. It converts execution decisions into "
    "research implementation/action candidates, source/control acquisition requirements, and scope rollups. "
    "It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, "
    "validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-SRC-ACTION-SRC-{index:04d}",
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
                    "symbol_session_action_id": f"OHLC-GTOS-DENOM-SRC-ACTION-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "denominator_source_action_lane_counts": string_counter(members, "denominator_source_action_lane"),
                    "denominator_source_action_status_counts": string_counter(members, "denominator_source_action_status"),
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
    implementation_rows: list[dict[str, Any]],
    exact_scope_rows: list[dict[str, Any]],
    scope_rollup_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "denominator_source_action_lane": string_counter(unified_rows, "denominator_source_action_lane"),
        "denominator_source_action_status": string_counter(unified_rows, "denominator_source_action_status"),
        "implementation_candidate_family": string_counter(implementation_rows, "implementation_candidate_family"),
        "keep_kill_redesign_decision": string_counter(implementation_rows, "keep_kill_redesign_decision"),
        "exact_scope_action_status": string_counter(exact_scope_rows, "denominator_source_action_status"),
        "scope_rollup_action_status": string_counter(scope_rollup_rows, "denominator_source_action_status"),
        "acquisition_requirement_family": string_counter(acquisition_rows, "acquisition_requirement_family"),
        "acquisition_requirement_status": string_counter(acquisition_rows, "acquisition_requirement_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-ACTION-BUCKET-{len(output) + 1:04d}",
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
        if rel in existing:
            continue
        generated.append(
            {
                "path": rel,
                "artifact": result["artifact"],
                "generated_utc": result["generated_utc"],
                "safe_flags": SAFE_FLAGS,
                "not_completion": True,
                "source_manifest_hash": result["source_manifest_hash"],
            }
        )
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "event": "branch_local_denominator_source_action_candidate_bundle_built",
        "artifact": result["artifact"],
        "generated_utc": result["generated_utc"],
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "source_manifest_hash": result["source_manifest_hash"],
        "system_decision": result["system_decision"],
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    generated_at = now_utc()
    exec_result = read_json(EXEC_RESULT)
    exec_runtime = read_json(EXEC_RUNTIME)
    exec_unified = read_jsonl(EXEC_UNIFIED)
    exec_exact_target = read_jsonl(EXEC_EXACT_TARGET)
    exec_exact_scope = read_jsonl(EXEC_EXACT_SCOPE)
    exec_source = read_jsonl(EXEC_SOURCE)
    exec_horizon = read_jsonl(EXEC_HORIZON)
    exec_scope = read_jsonl(EXEC_SCOPE)

    source_paths = [
        HELPER_MODULE,
        BUILDER_MODULE,
        EXEC_RESULT,
        EXEC_RUNTIME,
        EXEC_UNIFIED,
        EXEC_EXACT_TARGET,
        EXEC_EXACT_SCOPE,
        EXEC_SOURCE,
        EXEC_HORIZON,
        EXEC_SCOPE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    exact_target_rows = [
        make_row(
            "denominator_source_action_candidate_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-TARGET-{index:05d}",
            exact_control_target_action_candidate(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exec_exact_target, 1)
    ]
    exact_scope_rows = [
        make_row(
            "exact_control_scope_action_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-SCOPECTRL-{index:05d}",
            exact_control_scope_action_candidate(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exec_exact_scope, 1)
    ]
    source_rows = [
        make_row(
            "denominator_source_action_candidate_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-SOURCE-{index:05d}",
            source_proxy_kill_action_candidate(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exec_source, 1)
    ]
    horizon_rows = [
        make_row(
            "denominator_source_action_candidate_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-HORIZON-{index:05d}",
            horizon_repair_action_candidate(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exec_horizon, 1)
    ]
    scope_rollup_rows = [
        make_row(
            "scope_rollup_action_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-SCOPEROLL-{index:05d}",
            scope_rollup_action_candidate(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(exec_scope, 1)
    ]
    unified_rows = [*exact_target_rows, *source_rows, *horizon_rows]
    implementation_rows = [*exact_target_rows, *exact_scope_rows, *source_rows, *horizon_rows]
    acquisition_rows = [
        make_row(
            "acquisition_requirement_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACTION-ACQ-{index:05d}",
            acquisition_requirement_from_action(row),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(unified_rows, 1)
    ]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        implementation_rows,
        exact_scope_rows,
        scope_rollup_rows,
        acquisition_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTION-Q-0001",
                "question": "Which exact-control target rows can be materially repaired from current same-resource controls before scalar interpretation?",
                "next_action": "run exact-control target denominator build by source_code_candidate_id and scope",
                "row_scope": "92 exact-control target action rows",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTION-Q-0002",
                "question": "Do any of the 61 negative source proxies reverse after exact-source rebuild or stronger same-resource proxy acquisition?",
                "next_action": "execute exact-source rebuild/acquisition and keep proxy-kill unless contradicted",
                "row_scope": "61 source proxy kill rows",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTION-Q-0003",
                "question": "Which horizon repair, redesign, or kill-check rows survive targetability repair and rescore?",
                "next_action": "materialize horizon targetability repair/redesign ledgers and rescore all 37 rows",
                "row_scope": "37 horizon action rows",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTION-Q-0004",
                "question": "Do the four guarded scope proxies remain useful after exact denominator build and concentration stress?",
                "next_action": "register only guarded branch-local proxy candidates and require exact denominator check",
                "row_scope": "4 exact-control scope guarded proxy rows",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    runtime_spec = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "inputs": {
            "execution_bundle": EXEC_RESULT.relative_to(REPO).as_posix(),
            "execution_unified_rows": len(exec_unified),
            "execution_exact_target_rows": len(exec_exact_target),
            "execution_exact_scope_rows": len(exec_exact_scope),
            "execution_source_rows": len(exec_source),
            "execution_horizon_rows": len(exec_horizon),
            "execution_scope_rows": len(exec_scope),
        },
        "outputs": {
            "unified_action_rows": len(unified_rows),
            "implementation_decision_rows": len(implementation_rows),
            "acquisition_requirement_rows": len(acquisition_rows),
            "scope_rollup_rows": len(scope_rollup_rows),
        },
        "next_required_computation": (
            "execute exact-control denominator builds, source exact rebuild/acquisition, and horizon "
            "repair/redesign/kill-check rescore; preserve source proxy kills unless contradicted by exact rebuild"
        ),
    }
    system_decision = {
        "denominator_source_action_status_counts": string_counter(unified_rows, "denominator_source_action_status"),
        "implementation_candidate_family_counts": string_counter(implementation_rows, "implementation_candidate_family"),
        "keep_kill_redesign_counts": string_counter(implementation_rows, "keep_kill_redesign_decision"),
        "acquisition_requirement_family_counts": string_counter(acquisition_rows, "acquisition_requirement_family"),
        "system_recommendation": (
            "BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_CANDIDATE_BUNDLE_RESULT: keep the 61 source proxy kills out "
            "of implementation unless exact rebuild contradicts them; register only four guarded control-scope "
            "proxy candidates while building exact denominators; execute all 19 scope builds and 37 horizon "
            "repair/redesign/kill-check rows before candidate use."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_execution_unified_rows": len(exec_unified),
            "input_exact_control_target_execution_rows": len(exec_exact_target),
            "input_exact_control_scope_execution_rows": len(exec_exact_scope),
            "input_source_rebuild_execution_rows": len(exec_source),
            "input_horizon_rebuild_execution_rows": len(exec_horizon),
            "input_scope_action_execution_rows": len(exec_scope),
            "unified_action_candidate_rows": len(unified_rows),
            "implementation_decision_rows": len(implementation_rows),
            "exact_control_target_action_rows": len(exact_target_rows),
            "exact_control_scope_action_rows": len(exact_scope_rows),
            "guarded_scope_proxy_rows": sum(1 for row in exact_scope_rows if row.get("keep_kill_redesign_decision") == "KEEP_GUARDED_PROXY"),
            "exact_scope_build_required_rows": sum(1 for row in exact_scope_rows if row.get("keep_kill_redesign_decision") == "BUILD_REQUIRED"),
            "source_proxy_kill_action_rows": len(source_rows),
            "horizon_repair_action_rows": len(horizon_rows),
            "horizon_repair_rows": sum(1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "REPAIR"),
            "horizon_redesign_rows": sum(1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "REDESIGN"),
            "horizon_kill_check_rows": sum(1 for row in horizon_rows if row.get("keep_kill_redesign_decision") == "KILL_CHECK"),
            "scope_rollup_action_rows": len(scope_rollup_rows),
            "acquisition_requirement_rows": len(acquisition_rows),
            "symbol_session_action_rows": len(symbol_session_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
            "runtime_spec_rows": 1,
        },
        "bucket_distributions": distributions,
        "source_manifest_hash": manifest_hash,
        "upstream_counts": {"denominator_source_execution_bundle": exec_result["counts"]},
        "system_decision": system_decision,
    }

    outputs = [
        RESULT_PATH,
        UNIFIED_LEDGER,
        IMPLEMENTATION_TABLE,
        EXACT_TARGET_LEDGER,
        EXACT_SCOPE_LEDGER,
        SOURCE_ACTION_LEDGER,
        HORIZON_ACTION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        ACQUISITION_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
        SUMMARY_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(IMPLEMENTATION_TABLE, implementation_rows)
    write_jsonl(EXACT_TARGET_LEDGER, exact_target_rows)
    write_jsonl(EXACT_SCOPE_LEDGER, exact_scope_rows)
    write_jsonl(SOURCE_ACTION_LEDGER, source_rows)
    write_jsonl(HORIZON_ACTION_LEDGER, horizon_rows)
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollup_rows)
    write_jsonl(ACQUISITION_LEDGER, acquisition_rows)
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
                "# Branch-Local Denominator Source Action Candidate Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Unified primary action rows: `{len(unified_rows)}`.",
                f"- Implementation decision rows: `{len(implementation_rows)}`.",
                f"- Exact-control scope rows: `{len(exact_scope_rows)}` (`{result['counts']['guarded_scope_proxy_rows']}` guarded proxy, `{result['counts']['exact_scope_build_required_rows']}` build-required).",
                f"- Source proxy kill rows: `{len(source_rows)}`.",
                f"- Horizon action rows: `{len(horizon_rows)}` (`{result['counts']['horizon_repair_rows']}` repair, `{result['counts']['horizon_redesign_rows']}` redesign, `{result['counts']['horizon_kill_check_rows']}` kill-check).",
                "- No live behavior, validation, promotion, broker R/PnL, win-rate, or expectancy claim is made.",
                "",
            ]
        ),
    )
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"artifact": PREFIX, "ok": True, "counts": result["counts"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
