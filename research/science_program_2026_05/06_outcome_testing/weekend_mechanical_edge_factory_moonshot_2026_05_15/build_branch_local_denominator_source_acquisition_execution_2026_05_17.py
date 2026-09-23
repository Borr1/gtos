#!/usr/bin/env python3
"""Execute denominator/source acquisition requirements into concrete rows."""

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

from src.research_infra.moonshot_branch_local_denominator_source_acquisition_execution import (
    DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_SURFACE,
    acquisition_requirement_execution,
    exact_control_scope_build_execution,
    exact_control_target_build_execution,
    horizon_repair_rescore_execution,
    source_exact_rebuild_execution,
)


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_CANDIDATE_BUNDLE"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_EXECUTION_BUNDLE"
REBUILD_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_REBUILD_BUNDLE"
SOURCE_MAT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_BUNDLE"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_RUNTIME = ROUTE_DIR / f"{ACTION_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
ACTION_UNIFIED = ROUTE_DIR / f"{ACTION_PREFIX}_UNIFIED_ACTION_CANDIDATE_LEDGER_2026-05-17.jsonl"
ACTION_EXACT_TARGET = ROUTE_DIR / f"{ACTION_PREFIX}_EXACT_CONTROL_TARGET_ACTION_LEDGER_2026-05-17.jsonl"
ACTION_EXACT_SCOPE = ROUTE_DIR / f"{ACTION_PREFIX}_EXACT_CONTROL_SCOPE_ACTION_LEDGER_2026-05-17.jsonl"
ACTION_SOURCE = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_PROXY_KILL_ACTION_LEDGER_2026-05-17.jsonl"
ACTION_HORIZON = ROUTE_DIR / f"{ACTION_PREFIX}_HORIZON_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
ACTION_ACQUISITION = ROUTE_DIR / f"{ACTION_PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"

EXEC_EXACT_TARGET = ROUTE_DIR / f"{EXEC_PREFIX}_EXACT_CONTROL_TARGET_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_SOURCE = ROUTE_DIR / f"{EXEC_PREFIX}_SOURCE_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
EXEC_HORIZON = ROUTE_DIR / f"{EXEC_PREFIX}_HORIZON_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"

REBUILD_MEMBER = ROUTE_DIR / f"{REBUILD_PREFIX}_CONTROL_MEMBER_DENOMINATOR_EVIDENCE_LEDGER_2026-05-17.jsonl"
REBUILD_SOURCE = ROUTE_DIR / f"{REBUILD_PREFIX}_SOURCE_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
REBUILD_HORIZON = ROUTE_DIR / f"{REBUILD_PREFIX}_HORIZON_MATERIALIZATION_REBUILD_LEDGER_2026-05-17.jsonl"
SOURCE_MATERIALIZATION = ROUTE_DIR / f"{SOURCE_MAT_PREFIX}_MATERIALIZATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_ACQUISITION_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_TARGET_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_TARGET_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_SCOPE_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_EXACT_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
HORIZON_EXEC_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_RESCORE_EXECUTION_LEDGER_2026-05-17.jsonl"
ACQUISITION_EXEC_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_REQUIREMENT_EXECUTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACQUISITION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local denominator/source acquisition-execution bundle only. It executes exact-control build attempts, "
    "source exact-rebuild contradiction checks, and horizon repair/rescore bounds from current same-resource rows. "
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-SRC-ACQEXEC-SRC-{index:04d}",
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


def group_by_key(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key)].append(row)
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
                    "symbol_session_acquisition_id": f"OHLC-GTOS-DENOM-SRC-ACQEXEC-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "denominator_source_acquisition_lane_counts": string_counter(members, "denominator_source_acquisition_lane"),
                    "denominator_source_acquisition_status_counts": string_counter(members, "denominator_source_acquisition_status"),
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
    exact_scope_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "denominator_source_acquisition_lane": string_counter(unified_rows, "denominator_source_acquisition_lane"),
        "denominator_source_acquisition_status": string_counter(unified_rows, "denominator_source_acquisition_status"),
        "keep_kill_redesign_decision": string_counter(unified_rows + exact_scope_rows, "keep_kill_redesign_decision"),
        "exact_scope_acquisition_status": string_counter(exact_scope_rows, "denominator_source_acquisition_status"),
        "acquisition_requirement_execution_status": string_counter(acquisition_rows, "denominator_source_acquisition_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
        "horizon_repair_upper_result_class": string_counter(
            [row for row in unified_rows if row.get("denominator_source_acquisition_lane") == "HORIZON_REPAIR_RESCORE_EXECUTION"],
            "repair_upper_proxy_r_style_result_class",
        ),
        "source_proxy_result_class": string_counter(
            [row for row in unified_rows if row.get("denominator_source_acquisition_lane") == "EXACT_SOURCE_REBUILD_EXECUTION"],
            "materialization_proxy_r_style_result_class",
        ),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-ACQEXEC-BUCKET-{len(output) + 1:04d}",
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
        "event": "branch_local_denominator_source_acquisition_execution_bundle_built",
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
    action_result = read_json(ACTION_RESULT)
    action_runtime = read_json(ACTION_RUNTIME)
    action_unified = read_jsonl(ACTION_UNIFIED)
    action_exact_target = read_jsonl(ACTION_EXACT_TARGET)
    action_exact_scope = read_jsonl(ACTION_EXACT_SCOPE)
    action_source = read_jsonl(ACTION_SOURCE)
    action_horizon = read_jsonl(ACTION_HORIZON)
    action_acquisition = read_jsonl(ACTION_ACQUISITION)
    exec_exact_target = read_jsonl(EXEC_EXACT_TARGET)
    exec_source = read_jsonl(EXEC_SOURCE)
    exec_horizon = read_jsonl(EXEC_HORIZON)
    member_rows = read_jsonl(REBUILD_MEMBER)
    rebuild_source = read_jsonl(REBUILD_SOURCE)
    rebuild_horizon = read_jsonl(REBUILD_HORIZON)
    source_materialization = read_jsonl(SOURCE_MATERIALIZATION)

    source_paths = [
        HELPER_MODULE,
        BUILDER_MODULE,
        ACTION_RESULT,
        ACTION_RUNTIME,
        ACTION_UNIFIED,
        ACTION_EXACT_TARGET,
        ACTION_EXACT_SCOPE,
        ACTION_SOURCE,
        ACTION_HORIZON,
        ACTION_ACQUISITION,
        EXEC_EXACT_TARGET,
        EXEC_SOURCE,
        EXEC_HORIZON,
        REBUILD_MEMBER,
        REBUILD_SOURCE,
        REBUILD_HORIZON,
        SOURCE_MATERIALIZATION,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    exec_exact_target_by_id = {row.get("denominator_source_execution_row_id"): row for row in exec_exact_target}
    exec_source_by_id = {row.get("denominator_source_execution_row_id"): row for row in exec_source}
    exec_horizon_by_id = {row.get("denominator_source_execution_row_id"): row for row in exec_horizon}
    source_rebuild_by_id = {row.get("denominator_source_rebuild_row_id"): row for row in rebuild_source}
    horizon_rebuild_by_id = {row.get("denominator_source_rebuild_row_id"): row for row in rebuild_horizon}
    materialization_by_code = {str(row.get("source_code_candidate_id")): row for row in source_materialization}
    member_by_target_repair = group_by_key(member_rows, "target_input_repair_execution_row_id")

    exact_target_rows: list[dict[str, Any]] = []
    for index, action_row in enumerate(action_exact_target, 1):
        execution_row = exec_exact_target_by_id.get(action_row.get("input_denominator_source_execution_row_id"), {})
        target_members = member_by_target_repair.get(execution_row.get("input_repair_execution_row_id"), [])
        exact_target_rows.append(
            make_row(
                "denominator_source_acquisition_execution_row_id",
                f"OHLC-GTOS-DENOM-SRC-ACQEXEC-TARGET-{index:05d}",
                exact_control_target_build_execution(action_row, execution_row, target_members),
                generated_at,
                manifest_hash,
            )
        )

    target_rows_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in exact_target_rows:
        target_rows_by_scope[scope_key(row)].append(row)
    exact_scope_rows = [
        make_row(
            "exact_control_scope_acquisition_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACQEXEC-SCOPE-{index:05d}",
            exact_control_scope_build_execution(row, target_rows_by_scope.get(scope_key(row), [])),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(action_exact_scope, 1)
    ]
    source_rows = [
        make_row(
            "denominator_source_acquisition_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACQEXEC-SOURCE-{index:05d}",
            source_exact_rebuild_execution(
                row,
                exec_source_by_id.get(row.get("input_denominator_source_execution_row_id"), {}),
                source_rebuild_by_id.get(row.get("input_denominator_source_rebuild_row_id"), {}),
                materialization_by_code.get(str(row.get("source_code_candidate_id"))),
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(action_source, 1)
    ]
    horizon_rows = [
        make_row(
            "denominator_source_acquisition_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACQEXEC-HORIZON-{index:05d}",
            horizon_repair_rescore_execution(
                row,
                exec_horizon_by_id.get(row.get("input_denominator_source_execution_row_id"), {}),
                horizon_rebuild_by_id.get(row.get("input_denominator_source_rebuild_row_id"), {}),
                materialization_by_code.get(str(row.get("source_code_candidate_id"))),
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(action_horizon, 1)
    ]
    unified_rows = [*exact_target_rows, *source_rows, *horizon_rows]
    executed_by_action = {row.get("input_action_candidate_row_id"): row for row in unified_rows}
    acquisition_rows = [
        make_row(
            "acquisition_requirement_execution_row_id",
            f"OHLC-GTOS-DENOM-SRC-ACQEXEC-REQ-{index:05d}",
            acquisition_requirement_execution(row, executed_by_action.get(row.get("input_action_candidate_row_id"))),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(action_acquisition, 1)
    ]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(unified_rows, exact_scope_rows, acquisition_rows, generated_at, manifest_hash)
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACQEXEC-Q-0001",
                "question": "Can exact-control targets reach N20 from owned current rows without relation-proxy fallback?",
                "answer_from_current_rows": "No exact-scope N20 target exists in the member evidence; proxy guards remain build-open.",
                "next_action": "search broader same-resource exact-control construction or keep proxy-guard only",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACQEXEC-Q-0002",
                "question": "Do negative source proxies get contradicted by current exact-source rebuild evidence?",
                "answer_from_current_rows": "No contradiction in the current action subset; negative proxy kills remain active while exact rebuild routes stay open.",
                "next_action": "execute broader exact-source acquisition/proxy split by symbol/session/horizon/source family",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACQEXEC-Q-0003",
                "question": "Which horizon rows can become scoreable if fail-closed source rows are repaired into targetable horizon rows?",
                "answer_from_current_rows": "All horizon rows receive repair upper-bound scores; kill-check rows stay conditional unless the repaired upper bound is still negative.",
                "next_action": "materialize horizon targetability repair details and kill/redesign/repair decisions by row",
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
            "action_bundle": ACTION_RESULT.relative_to(REPO).as_posix(),
            "action_unified_rows": len(action_unified),
            "action_exact_target_rows": len(action_exact_target),
            "action_exact_scope_rows": len(action_exact_scope),
            "action_source_rows": len(action_source),
            "action_horizon_rows": len(action_horizon),
            "action_acquisition_rows": len(action_acquisition),
            "member_evidence_rows_read": len(member_rows),
        },
        "outputs": {
            "unified_acquisition_execution_rows": len(unified_rows),
            "exact_control_scope_build_execution_rows": len(exact_scope_rows),
            "acquisition_requirement_execution_rows": len(acquisition_rows),
        },
        "next_required_computation": (
            "split exact-control proxy guards by relation/source family, source exact rebuild contradictions by "
            "symbol/session/horizon, and horizon repair upper bounds into row-level keep/kill/redesign/rescore decisions"
        ),
    }
    system_decision = {
        "denominator_source_acquisition_status_counts": string_counter(unified_rows, "denominator_source_acquisition_status"),
        "exact_scope_status_counts": string_counter(exact_scope_rows, "denominator_source_acquisition_status"),
        "keep_kill_redesign_counts": string_counter(unified_rows + exact_scope_rows, "keep_kill_redesign_decision"),
        "system_recommendation": (
            "BRANCH_LOCAL_DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_BUNDLE_RESULT: exact-control targets remain "
            "build-open because exact-scope controls are unavailable in current rows; source proxy kills remain active "
            "with no exact contradiction; horizon rows move to repair/redesign/kill-check upper-bound rescore."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_action_unified_rows": len(action_unified),
            "input_exact_control_target_action_rows": len(action_exact_target),
            "input_exact_control_scope_action_rows": len(action_exact_scope),
            "input_source_action_rows": len(action_source),
            "input_horizon_action_rows": len(action_horizon),
            "input_acquisition_requirement_rows": len(action_acquisition),
            "input_control_member_evidence_rows_read": len(member_rows),
            "unified_acquisition_execution_rows": len(unified_rows),
            "exact_control_target_build_execution_rows": len(exact_target_rows),
            "exact_control_scope_build_execution_rows": len(exact_scope_rows),
            "source_exact_rebuild_execution_rows": len(source_rows),
            "source_kill_confirmed_rows": sum(1 for row in source_rows if row.get("keep_kill_redesign_decision") == "KILL_PROXY"),
            "horizon_repair_rescore_execution_rows": len(horizon_rows),
            "horizon_repair_upper_bound_reaches_n20_rows": sum(
                1 for row in horizon_rows if row.get("repaired_targetable_upper_bound_reaches_n20")
            ),
            "acquisition_requirement_execution_rows": len(acquisition_rows),
            "symbol_session_acquisition_rows": len(symbol_session_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
            "runtime_spec_rows": 1,
        },
        "bucket_distributions": distributions,
        "source_manifest_hash": manifest_hash,
        "upstream_counts": {"denominator_source_action_candidate_bundle": action_result["counts"]},
        "system_decision": system_decision,
    }

    outputs = [
        RESULT_PATH,
        UNIFIED_LEDGER,
        EXACT_TARGET_LEDGER,
        EXACT_SCOPE_LEDGER,
        SOURCE_EXEC_LEDGER,
        HORIZON_EXEC_LEDGER,
        ACQUISITION_EXEC_LEDGER,
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
    write_jsonl(SOURCE_EXEC_LEDGER, source_rows)
    write_jsonl(HORIZON_EXEC_LEDGER, horizon_rows)
    write_jsonl(ACQUISITION_EXEC_LEDGER, acquisition_rows)
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
                "# Branch-Local Denominator Source Acquisition Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Unified acquisition execution rows: `{len(unified_rows)}`.",
                f"- Exact-control target build rows: `{len(exact_target_rows)}`.",
                f"- Exact-control scope build rows: `{len(exact_scope_rows)}`.",
                f"- Source exact-rebuild rows: `{len(source_rows)}` (`{result['counts']['source_kill_confirmed_rows']}` proxy kills confirmed by current rows).",
                f"- Horizon repair/rescore rows: `{len(horizon_rows)}` (`{result['counts']['horizon_repair_upper_bound_reaches_n20_rows']}` reach N20 under repaired targetability upper bound).",
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
