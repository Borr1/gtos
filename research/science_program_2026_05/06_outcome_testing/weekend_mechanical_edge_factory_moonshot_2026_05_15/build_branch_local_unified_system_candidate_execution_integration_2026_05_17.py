#!/usr/bin/env python3
"""Consume candidate implementation execution outputs into integration rows."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_execution_integration import (
    UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
    execution_integration_decision,
    execution_integration_rollup,
    guard_bound_integration_row,
    market_system_integration_row,
    nofill_result_row,
    opportunity_integration_row,
    recheck_integration_row,
    registry_module_row,
    score_control_result_row,
    source_control_result_row,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_IMPLEMENTATION_EXECUTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_MODULE_ARTIFACT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_OUTPUT_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_COMPARATOR_OUTPUT_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_COMPARATOR_OUTPUT_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_REGISTRY_ARTIFACT_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_OPPORTUNITY_SYSTEM_INPUT_OUTPUT_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RUN_OUTPUT_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_PRIORITY_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXECUTION_INTEGRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_INTEGRATION_DECISION_LEDGER_2026-05-17.jsonl"
REGISTRY_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
NOFILL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_RESULT_LEDGER_2026-05-17.jsonl"
GUARD_BOUND_INTEGRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_BOUND_INTEGRATION_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_INTEGRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_OPPORTUNITY_INTEGRATION_LEDGER_2026-05-17.jsonl"
RECHECK_INTEGRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_INTEGRATION_LEDGER_2026-05-17.jsonl"
MARKET_SYSTEM_INTEGRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_SYSTEM_INTEGRATION_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
MARKET_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system candidate execution-integration bundle. It consumes candidate implementation execution "
    "outputs into concrete registry module rows, source/control result rows, score-control result rows, no-fill result "
    "rows, guard-bound integration rows, opportunity/recheck integration rows, market-system integration rows, and a "
    "system recommendation row. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


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
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
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


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_rollups(
    integration_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in integration_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("execution_integration_family"),
            )
        ].append(row)
        by_family[(row.get("execution_integration_family"), row.get("execution_integration_status"))].append(row)
    for row in component_rows:
        family = (
            row.get("registry_module_status")
            or row.get("source_control_result_status")
            or row.get("score_control_result_status")
            or row.get("nofill_result_status")
            or row.get("guard_bound_status")
            or row.get("opportunity_integration_status")
            or row.get("recheck_integration_status")
        )
        by_family[(row.get("unified_system_candidate_execution_integration"), family)].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_system_integration_status"))].append(row)
    scope_rollups = [
        with_common(execution_integration_rollup(key, by_scope[key], index, "scope_candidate_execution_integration"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(execution_integration_rollup(key, by_family[key], index, "family_candidate_execution_integration"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(execution_integration_rollup(key, by_market[key], index, "market_candidate_execution_integration"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_market, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    return scope_rollups, family_rollups, market_rollups


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True}
            )
    manifest["latest_branch_local_unified_system_candidate_execution_integration_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_execution_integration_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed implementation execution outputs into concrete registry/source/no-fill/guard/market integration rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_EXECUTION_LEDGER,
            INPUT_SCORER_LEDGER,
            INPUT_SOURCE_LEDGER,
            INPUT_SCORE_CONTROL_LEDGER,
            INPUT_NOFILL_LEDGER,
            INPUT_GUARD_LEDGER,
            INPUT_OPPORTUNITY_LEDGER,
            INPUT_RECHECK_LEDGER,
            INPUT_MARKET_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    execution_input = read_jsonl(INPUT_EXECUTION_LEDGER)
    scorer_input = read_jsonl(INPUT_SCORER_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_LEDGER)

    integration_rows = [
        with_common(execution_integration_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(execution_input, 1)
    ]
    registry_rows = [
        with_common(registry_module_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(scorer_input, 1)
    ]
    source_rows = [
        with_common(source_control_result_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_input, 1)
    ]
    score_control_rows = [
        with_common(score_control_result_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_rows = [
        with_common(nofill_result_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_rows = [
        with_common(guard_bound_integration_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(guard_input, 1)
    ]
    opportunity_rows = [
        with_common(opportunity_integration_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_input, 1)
    ]
    recheck_rows = [
        with_common(recheck_integration_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_input, 1)
    ]
    market_rows = [
        with_common(market_system_integration_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_input, 1)
    ]
    component_rows = registry_rows + source_rows + score_control_rows + nofill_rows + guard_rows + opportunity_rows + recheck_rows
    scope_rollups, family_rollups, market_rollups = build_rollups(integration_rows, component_rows, market_rows, generated_at, manifest_hash)
    distributions = {
        "execution_integration_family": string_counter(integration_rows, "execution_integration_family"),
        "execution_integration_status": string_counter(integration_rows, "execution_integration_status"),
        "integration_positive_role": string_counter(integration_rows, "integration_positive_role"),
        "integration_negative_role": string_counter(integration_rows, "integration_negative_role"),
        "registry_module_status": string_counter(registry_rows, "registry_module_status"),
        "source_control_result_status": string_counter(source_rows, "source_control_result_status"),
        "score_control_result_status": string_counter(score_control_rows, "score_control_result_status"),
        "nofill_result_status": string_counter(nofill_rows, "nofill_result_status"),
        "guard_bound_status": string_counter(guard_rows, "guard_bound_status"),
        "opportunity_integration_status": string_counter(opportunity_rows, "opportunity_integration_status"),
        "recheck_integration_status": string_counter(recheck_rows, "recheck_integration_status"),
        "market_system_integration_status": string_counter(market_rows, "market_system_integration_status"),
        "market_system_integration_symbol": string_counter(market_rows, "symbol"),
        "market_system_integration_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by execution integration, registry, source/control result, no-fill result, guard-bound, market-system, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(
            [
                "Did every implementation execution result become a concrete integration decision?",
                "Which scorer module artifacts became branch-local registry rows?",
                "Which source/control outputs became result rows ready for same-scope rejoin?",
                "Which score-control outputs became comparator result rows or repair/context rows?",
                "Which no-fill outputs became challenger, avoid/inverse, stress, or source-repair result rows?",
                "Which guard artifacts became fail-closed guard-bound integration rows?",
                "Which opportunity and recheck outputs became system integration rows?",
                "Which market-priority outputs became market-system integration rows?",
                "What same-resource system layer follows from the integration rows?",
            ],
            1,
        )
    ]
    counts = {
        "input_execution_result_rows": len(execution_input),
        "input_scorer_module_artifact_rows": len(scorer_input),
        "input_source_control_output_rows": len(source_input),
        "input_score_control_output_rows": len(score_control_input),
        "input_nofill_output_rows": len(nofill_input),
        "input_guard_artifact_rows": len(guard_input),
        "input_opportunity_output_rows": len(opportunity_input),
        "input_recheck_output_rows": len(recheck_input),
        "input_market_priority_execution_rows": len(market_input),
        "execution_integration_decision_rows": len(integration_rows),
        "registry_module_rows": len(registry_rows),
        "source_control_result_rows": len(source_rows),
        "score_control_result_rows": len(score_control_rows),
        "nofill_result_rows": len(nofill_rows),
        "guard_bound_integration_rows": len(guard_rows),
        "opportunity_integration_rows": len(opportunity_rows),
        "recheck_integration_rows": len(recheck_rows),
        "market_system_integration_rows": len(market_rows),
        "system_recommendation_rows": 1,
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    split_total = len(component_rows)
    all_execution_rows_consumed = len(integration_rows) == len(execution_input) == input_result["counts"]["candidate_implementation_execution_result_rows"]
    all_component_execution_rows_consumed = split_total == input_result["counts"]["candidate_implementation_execution_result_rows"]
    all_market_execution_rows_consumed = len(market_rows) == len(market_input) == input_result["counts"]["market_priority_execution_output_rows"]
    system_recommendation_rows = [
        with_common(
            {
                "system_recommendation_row_id": "OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-SYSTEM-RECOMMENDATION-0001",
                "execution_integration_recommendation": (
                    "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION_BUNDLE_RESULT: consume registry, "
                    "source/control, score-control, no-fill, guard-bound, opportunity, recheck, and market-system integration rows "
                    "into the next concrete result/scoring layer; keep all modules default-off and source/control guarded."
                ),
                "execution_integration_decision_rows": len(integration_rows),
                "registry_module_rows": len(registry_rows),
                "source_control_result_rows": len(source_rows),
                "score_control_result_rows": len(score_control_rows),
                "nofill_result_rows": len(nofill_rows),
                "guard_bound_integration_rows": len(guard_rows),
                "market_system_integration_rows": len(market_rows),
                "not_terminal": True,
                "next_same_resource_layer": "consume integration rows into branch-local integrated scoring/result bundle with guard-bound registry modules and comparator result tables",
            },
            generated_at,
            manifest_hash,
        )
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_execution_rows_consumed": all_execution_rows_consumed,
        "all_component_execution_rows_consumed": all_component_execution_rows_consumed,
        "all_market_execution_rows_consumed": all_market_execution_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "execution_integration_family_counts": distributions["execution_integration_family"],
            "execution_integration_status_counts": distributions["execution_integration_status"],
            "market_system_integration_status_counts": distributions["market_system_integration_status"],
            "system_recommendation": system_recommendation_rows[0]["execution_integration_recommendation"],
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_execution_rows_consumed": all_execution_rows_consumed,
        "all_component_execution_rows_consumed": all_component_execution_rows_consumed,
        "all_market_execution_rows_consumed": all_market_execution_rows_consumed,
    }
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        EXECUTION_INTEGRATION_LEDGER,
        REGISTRY_MODULE_LEDGER,
        SOURCE_CONTROL_RESULT_LEDGER,
        SCORE_CONTROL_RESULT_LEDGER,
        NOFILL_RESULT_LEDGER,
        GUARD_BOUND_INTEGRATION_LEDGER,
        OPPORTUNITY_INTEGRATION_LEDGER,
        RECHECK_INTEGRATION_LEDGER,
        MARKET_SYSTEM_INTEGRATION_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(EXECUTION_INTEGRATION_LEDGER, integration_rows)
    write_jsonl(REGISTRY_MODULE_LEDGER, registry_rows)
    write_jsonl(SOURCE_CONTROL_RESULT_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_RESULT_LEDGER, score_control_rows)
    write_jsonl(NOFILL_RESULT_LEDGER, nofill_rows)
    write_jsonl(GUARD_BOUND_INTEGRATION_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_INTEGRATION_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_INTEGRATION_LEDGER, recheck_rows)
    write_jsonl(MARKET_SYSTEM_INTEGRATION_LEDGER, market_rows)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, system_recommendation_rows)
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(MARKET_ROLLUP_LEDGER, market_rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Candidate Execution Integration Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Execution integration decision rows: `{counts['execution_integration_decision_rows']}`.",
                f"- Registry module rows: `{counts['registry_module_rows']}`.",
                f"- Source/control result rows: `{counts['source_control_result_rows']}`.",
                f"- No-fill result rows: `{counts['nofill_result_rows']}`.",
                f"- Guard-bound integration rows: `{counts['guard_bound_integration_rows']}`.",
                f"- Market-system integration rows: `{counts['market_system_integration_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
