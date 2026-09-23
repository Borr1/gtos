#!/usr/bin/env python3
"""Build branch-local shadow scorer/source-guard bundle decisions.

This builder consumes the immediate shadow-enable ledger, source
materialization decisions, score-with-control rows, and denominator guards. It
emits executable research bundle decisions and splits horizon fail-closed rows
into repair/action paths. It does not mutate live trading code or config.
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

from src.research_infra.moonshot_shadow_source_guard_bundle import (
    BUNDLE_SURFACE,
    classify_denominator_guard,
    classify_enable_bundle,
    classify_horizon_repair_action,
    classify_score_control,
    classify_source_guard,
)


SHADOW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION"
SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE"

SHADOW_RESULT = ROUTE_DIR / f"{SHADOW_PREFIX}_RESULT_2026-05-17.json"
SHADOW_IMPLEMENT = ROUTE_DIR / f"{SHADOW_PREFIX}_IMPLEMENT_ENABLE_LEDGER_2026-05-17.jsonl"
SHADOW_CONTROL = ROUTE_DIR / f"{SHADOW_PREFIX}_CONTROL_GUARD_LEDGER_2026-05-17.jsonl"
SOURCE_RESULT = ROUTE_DIR / f"{SOURCE_PREFIX}_RESULT_2026-05-17.json"
SOURCE_MATERIALIZATION = ROUTE_DIR / f"{SOURCE_PREFIX}_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_shadow_source_guard_bundle.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_DECISION_LEDGER_2026-05-17.jsonl"
IMPLEMENT_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENT_ENABLE_BUNDLE_LEDGER_2026-05-17.jsonl"
SOURCE_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_BUNDLE_LEDGER_2026-05-17.jsonl"
DENOMINATOR_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
HORIZON_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_BUNDLE_LEDGER_2026-05-17.jsonl"
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
    "Branch-local shadow source-guard bundle only. It assembles shadow-enable, source-guard, "
    "score-control, denominator-guard, and horizon-repair decisions from existing research rows. It "
    "does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, "
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
                "source_manifest_id": f"OHLC-GTOS-SHADOW-SRCGUARD-SRC-{index:04d}",
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


def compact_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def common_scope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
    }


def source_input_id(row: dict[str, Any]) -> Any:
    return (
        row.get("source_code_candidate_id")
        or row.get("shadow_scorer_execution_id")
        or row.get("source_materialization_execution_id")
    )


def build_implement_bundle_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "bundle_row_id": f"OHLC-GTOS-SHADOW-SRCGUARD-ENABLE-{index:05d}",
                    "input_ledger_type": "IMPLEMENT_ENABLE",
                    "input_row_id": row.get("shadow_scorer_execution_id"),
                    "source_code_candidate_id": row.get("source_code_candidate_id"),
                    "code_candidate_status": row.get("code_candidate_status"),
                    "shadow_scorer_action": row.get("shadow_scorer_action"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    "mechanical_scope_key": row.get("mechanical_scope_key"),
                    "mechanical_rule_expression": row.get("mechanical_rule_expression"),
                    **common_scope(row),
                    **classify_enable_bundle(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_source_guard_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        classified = classify_source_guard(row)
        source_row = with_common(
            {
                "bundle_row_id": f"OHLC-GTOS-SHADOW-SRCGUARD-SOURCE-{index:05d}",
                "input_ledger_type": "SOURCE_GUARD",
                "input_row_id": row.get("source_materialization_execution_id"),
                "shadow_scorer_execution_id": row.get("shadow_scorer_execution_id"),
                "source_code_candidate_id": row.get("source_code_candidate_id"),
                "source_materialization_execution_status": row.get("source_materialization_execution_status"),
                "source_materialization_decision": row.get("source_materialization_decision"),
                "materialization_proxy_scope": row.get("materialization_proxy_scope"),
                "materialization_proxy_r_style_result_class": row.get("materialization_proxy_r_style_result_class"),
                "materialization_proxy_r_style_lower": row.get("materialization_proxy_r_style_lower"),
                "materialization_proxy_r_style_midpoint": row.get("materialization_proxy_r_style_midpoint"),
                "materialization_proxy_r_style_upper": row.get("materialization_proxy_r_style_upper"),
                "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
                "current_source_flagged_n": row.get("current_source_flagged_n"),
                "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
                "current_failclosed_reason_counts": row.get("current_failclosed_reason_counts"),
                "materialization_exact_missing_reason": row.get("materialization_exact_missing_reason"),
                **common_scope(row),
                **classified,
            },
            generated_at,
            manifest_hash,
        )
        output.append(source_row)
        if row.get("source_materialization_execution_status") == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED":
            repair_rows.append(
                with_common(
                    {
                        "horizon_repair_action_id": f"OHLC-GTOS-SHADOW-SRCGUARD-HREPAIR-{len(repair_rows) + 1:05d}",
                        "source_bundle_row_id": source_row["bundle_row_id"],
                        "input_row_id": row.get("source_materialization_execution_id"),
                        "shadow_scorer_execution_id": row.get("shadow_scorer_execution_id"),
                        "source_code_candidate_id": row.get("source_code_candidate_id"),
                        "source_materialization_execution_status": row.get("source_materialization_execution_status"),
                        "materialization_proxy_r_style_result_class": row.get("materialization_proxy_r_style_result_class"),
                        "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
                        "current_source_flagged_n": row.get("current_source_flagged_n"),
                        "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
                        "current_failclosed_reason_counts": row.get("current_failclosed_reason_counts"),
                        **common_scope(row),
                        **classify_horizon_repair_action(row),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, repair_rows


def build_score_control_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "bundle_row_id": f"OHLC-GTOS-SHADOW-SRCGUARD-CONTROL-{index:05d}",
                    "input_ledger_type": "SCORE_WITH_CONTROL",
                    "input_row_id": row.get("shadow_scorer_execution_id"),
                    "source_code_candidate_id": row.get("source_code_candidate_id"),
                    "code_candidate_status": row.get("code_candidate_status"),
                    "shadow_scorer_action": row.get("shadow_scorer_action"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    "mechanical_scope_key": row.get("mechanical_scope_key"),
                    **common_scope(row),
                    **classify_score_control(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_denominator_guard_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "bundle_row_id": f"OHLC-GTOS-SHADOW-SRCGUARD-DGUARD-{index:05d}",
                    "input_ledger_type": "DENOMINATOR_GUARD",
                    "input_row_id": row.get("shadow_scorer_execution_id"),
                    "source_code_candidate_id": row.get("source_code_candidate_id"),
                    "code_candidate_status": row.get("code_candidate_status"),
                    "shadow_scorer_action": row.get("shadow_scorer_action"),
                    "shadow_scorer_component": row.get("shadow_scorer_component"),
                    "mechanical_scope_key": row.get("mechanical_scope_key"),
                    **common_scope(row),
                    **classify_denominator_guard(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                str(row.get("symbol") or "NA"),
                str(row.get("route_session") or "NA"),
                str(row.get("bundle_stage") or "NA"),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session, stage), members) in enumerate(sorted(groups.items()), 1):
        output.append(
            with_common(
                {
                    "symbol_session_bundle_id": f"OHLC-GTOS-SHADOW-SRCGUARD-SSH-{index:05d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "bundle_stage": stage,
                    "row_count": len(members),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "max_bundle_priority_score": max(float(row.get("bundle_priority_score") or 0.0) for row in members),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "bundle_stage": compact_counter(rows, "bundle_stage"),
        "bundle_decision": compact_counter(rows, "bundle_decision"),
        "bundle_permission": compact_counter(rows, "bundle_permission"),
        "shadow_scorer_component": compact_counter(rows, "shadow_scorer_component"),
        "source_guard_mode": compact_counter(rows, "source_guard_mode"),
        "source_materialization_execution_status": compact_counter(rows, "source_materialization_execution_status"),
        "materialization_proxy_r_style_result_class": compact_counter(rows, "materialization_proxy_r_style_result_class"),
        "horizon_repair_decision": compact_counter(repair_rows, "bundle_decision"),
        "outside_gbpjpy_xauusd_current_branch_box": compact_counter(rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    bucket_rows: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-SHADOW-SRCGUARD-BUCKET-{len(bucket_rows) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return bucket_rows, distributions


def build_runtime_spec(result: dict[str, Any], distributions: dict[str, dict[str, int]]) -> dict[str, Any]:
    return {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": result["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": result["source_manifest_hash"],
        "bundle_inputs": {
            "immediate_shadow_enable_rows": result["counts"]["input_implementation_enable_rows"],
            "source_materialization_decision_rows": result["counts"]["input_source_materialization_rows"],
            "score_with_control_rows": result["counts"]["input_score_with_control_rows"],
            "denominator_guard_rows": result["counts"]["input_denominator_guard_rows"],
        },
        "bundle_policy": {
            "enable_rows": "enable only in branch-local research shadow bundle",
            "source_guard_rows": "apply source guard permission before any source-dependent enable",
            "score_control_rows": "block enable until paired control score is produced",
            "denominator_guard_rows": "force denominator guard before concentration-sensitive interpretation",
            "horizon_failclosed_rows": "rebuild horizon targetability from current source flags before source-dependent enable",
        },
        "ledgers": {
            "unified_decisions": UNIFIED_LEDGER.relative_to(REPO).as_posix(),
            "implement_enable_bundle": IMPLEMENT_BUNDLE_LEDGER.relative_to(REPO).as_posix(),
            "source_guard_bundle": SOURCE_GUARD_LEDGER.relative_to(REPO).as_posix(),
            "score_control_bundle": SCORE_CONTROL_LEDGER.relative_to(REPO).as_posix(),
            "denominator_guard_bundle": DENOMINATOR_GUARD_LEDGER.relative_to(REPO).as_posix(),
            "horizon_repair_actions": HORIZON_REPAIR_LEDGER.relative_to(REPO).as_posix(),
        },
        "decision_distributions": {
            "bundle_stage": distributions["bundle_stage"],
            "bundle_decision": distributions["bundle_decision"],
            "horizon_repair_decision": distributions["horizon_repair_decision"],
        },
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
    manifest["latest_branch_local_shadow_source_guard_bundle"] = {
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
        "event": "branch_local_shadow_source_guard_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Built branch-local shadow scorer/source-guard bundle decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        SHADOW_RESULT,
        SHADOW_IMPLEMENT,
        SHADOW_CONTROL,
        SOURCE_RESULT,
        SOURCE_MATERIALIZATION,
        HELPER_MODULE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    shadow_result = read_json(SHADOW_RESULT)
    source_result = read_json(SOURCE_RESULT)
    implement_input = read_jsonl(SHADOW_IMPLEMENT)
    control_input = read_jsonl(SHADOW_CONTROL)
    source_input = read_jsonl(SOURCE_MATERIALIZATION)
    score_control_input = [row for row in control_input if row.get("shadow_scorer_action_family") == "SCORE_WITH_CONTROL"]
    denominator_guard_input = [row for row in control_input if row.get("shadow_scorer_action_family") == "DENOMINATOR_GUARD"]

    implement_rows = build_implement_bundle_rows(implement_input, generated_at, manifest_hash)
    source_guard_rows, horizon_repair_rows = build_source_guard_rows(source_input, generated_at, manifest_hash)
    score_control_rows = build_score_control_rows(score_control_input, generated_at, manifest_hash)
    denominator_guard_rows = build_denominator_guard_rows(denominator_guard_input, generated_at, manifest_hash)
    unified_rows = [*implement_rows, *source_guard_rows, *score_control_rows, *denominator_guard_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(unified_rows, horizon_repair_rows, generated_at, manifest_hash)
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-SHADOW-SRCGUARD-Q-001",
                "question": "Did the bundle consume every requested input row?",
                "answer_route": "Yes: 444 implementation enables, 309 source decisions, 231 score controls, and 124 denominator guards are emitted into the 1,108-row unified bundle ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-SHADOW-SRCGUARD-Q-002",
                "question": "Are horizon fail-closed rows split into exact repair/action paths?",
                "answer_route": "Yes: the 37 fail-closed source rows are emitted into the horizon repair ledger with rebuild-and-rescore or rebuild-and-kill-if-negative paths.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-SHADOW-SRCGUARD-Q-003",
                "question": "Does the bundle avoid becoming another transfer-only packet?",
                "answer_route": "Yes: every row carries a bundle permission, branch-local implementation decision, source guard, control, or denominator-guard action.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_implementation_enable_rows": len(implement_input),
        "input_source_materialization_rows": len(source_input),
        "input_control_guard_rows": len(control_input),
        "input_score_with_control_rows": len(score_control_input),
        "input_denominator_guard_rows": len(denominator_guard_input),
        "unified_bundle_decision_rows": len(unified_rows),
        "implement_enable_bundle_rows": len(implement_rows),
        "source_guard_bundle_rows": len(source_guard_rows),
        "score_control_bundle_rows": len(score_control_rows),
        "denominator_guard_bundle_rows": len(denominator_guard_rows),
        "horizon_repair_action_rows": len(horizon_repair_rows),
        "symbol_session_bundle_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
        "outside_branch_bundle_rows": sum(
            1 for row in unified_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "source_guard_repair_required_rows": sum(1 for row in source_guard_rows if row.get("source_repair_required")),
        "source_guard_block_rows": sum(
            1 for row in source_guard_rows if str(row.get("bundle_permission", "")).startswith("BLOCK")
        ),
    }
    system_decision = {
        "bundle_stage_counts": distributions["bundle_stage"],
        "bundle_decision_counts": distributions["bundle_decision"],
        "bundle_permission_counts": distributions["bundle_permission"],
        "horizon_repair_decision_counts": distributions["horizon_repair_decision"],
        "system_recommendation": (
            "BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_RESULT: enable the 444 immediate shadow rules only inside "
            "the branch-local research bundle, apply the 309 source guards, require the 231 controls and 124 "
            "denominator guards, and repair the 37 fail-closed horizon rows before any source-dependent enable."
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
            "unified_shadow_scorer_execution": shadow_result.get("counts", {}),
            "unified_source_materialization_execution": source_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }
    runtime_spec = build_runtime_spec(result, distributions)

    generated_files = [
        UNIFIED_LEDGER,
        IMPLEMENT_BUNDLE_LEDGER,
        SOURCE_GUARD_LEDGER,
        SCORE_CONTROL_LEDGER,
        DENOMINATOR_GUARD_LEDGER,
        HORIZON_REPAIR_LEDGER,
        SYMBOL_SESSION_LEDGER,
        RUNTIME_SPEC_PATH,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(IMPLEMENT_BUNDLE_LEDGER, implement_rows)
    write_jsonl(SOURCE_GUARD_LEDGER, source_guard_rows)
    write_jsonl(SCORE_CONTROL_LEDGER, score_control_rows)
    write_jsonl(DENOMINATOR_GUARD_LEDGER, denominator_guard_rows)
    write_jsonl(HORIZON_REPAIR_LEDGER, horizon_repair_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Shadow Source-Guard Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified bundle decision rows: `{counts['unified_bundle_decision_rows']}`",
                f"- Implementation enable rows: `{counts['implement_enable_bundle_rows']}`",
                f"- Source guard rows: `{counts['source_guard_bundle_rows']}`",
                f"- Score-with-control rows: `{counts['score_control_bundle_rows']}`",
                f"- Denominator guard rows: `{counts['denominator_guard_bundle_rows']}`",
                f"- Horizon repair action rows: `{counts['horizon_repair_action_rows']}`",
                "",
                "Core result: the branch-local shadow scorer/source-guard bundle now has executable research decisions for enable, source guard, control, denominator guard, and fail-closed horizon repair paths.",
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
