#!/usr/bin/env python3
"""Consume candidate implementation actions into concrete execution artifacts."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_implementation_execution import (
    UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
    candidate_implementation_execution_result,
    candidate_implementation_execution_rollup,
    guard_registry_artifact,
    market_priority_execution_output,
    nofill_comparator_output,
    opportunity_system_input_output,
    recheck_run_output,
    score_control_comparator_output,
    scorer_module_artifact,
    source_control_run_output,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_CANDIDATE_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_IMPLEMENTATION_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_CODE_INTEGRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_CODE_INTEGRATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_CONTROL_RUN_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_RUN_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_EXECUTION_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_EXECUTION_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_REGISTRY_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_SYSTEM_INPUT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_SYSTEM_INPUT_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_RUN_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RUN_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_PRIORITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_PRIORITY_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CANDIDATE_IMPLEMENTATION_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_IMPLEMENTATION_EXECUTION_RESULT_LEDGER_2026-05-17.jsonl"
SCORER_MODULE_ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_MODULE_ARTIFACT_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_OUTPUT_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_COMPARATOR_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_COMPARATOR_OUTPUT_LEDGER_2026-05-17.jsonl"
NOFILL_COMPARATOR_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPARATOR_OUTPUT_LEDGER_2026-05-17.jsonl"
GUARD_REGISTRY_ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_REGISTRY_ARTIFACT_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_SYSTEM_INPUT_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_OPPORTUNITY_SYSTEM_INPUT_OUTPUT_LEDGER_2026-05-17.jsonl"
RECHECK_RUN_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_RUN_OUTPUT_LEDGER_2026-05-17.jsonl"
MARKET_PRIORITY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_PRIORITY_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system candidate-implementation execution bundle. It consumes every candidate implementation "
    "action row into concrete scorer-module artifacts, source/control run outputs, score-control comparator outputs, "
    "no-fill comparator outputs, guard registry artifacts, opportunity system inputs, recheck outputs, market-priority "
    "execution outputs, and a system recommendation row. It does not change live behavior, place orders, or claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-SRC-{index:04d}",
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
    execution_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("implementation_execution_family"),
            )
        ].append(row)
        by_family[(row.get("implementation_execution_family"), row.get("implementation_execution_status"))].append(row)
    for row in component_rows:
        family = (
            row.get("scorer_module_artifact_status")
            or row.get("source_control_output_status")
            or row.get("score_control_output_status")
            or row.get("nofill_output_status")
            or row.get("guard_registry_artifact_status")
            or row.get("opportunity_output_status")
            or row.get("recheck_output_status")
        )
        by_family[(row.get("unified_system_candidate_implementation_execution"), family)].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_priority_execution_status"))].append(row)
    scope_rollups = [
        with_common(
            candidate_implementation_execution_rollup(key, by_scope[key], index, "scope_candidate_implementation_execution"),
            generated_at,
            manifest_hash,
        )
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(
            candidate_implementation_execution_rollup(key, by_family[key], index, "family_candidate_implementation_execution"),
            generated_at,
            manifest_hash,
        )
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(
            candidate_implementation_execution_rollup(key, by_market[key], index, "market_candidate_implementation_execution"),
            generated_at,
            manifest_hash,
        )
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
    manifest["latest_branch_local_unified_system_candidate_implementation_execution_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_implementation_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed candidate implementation actions into concrete scorer/source/comparator/guard/market execution outputs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_CANDIDATE_IMPLEMENTATION_LEDGER,
            INPUT_SCORER_CODE_INTEGRATION_LEDGER,
            INPUT_SOURCE_CONTROL_RUN_LEDGER,
            INPUT_SCORE_CONTROL_EXECUTION_LEDGER,
            INPUT_NOFILL_EXECUTION_LEDGER,
            INPUT_GUARD_REGISTRY_LEDGER,
            INPUT_OPPORTUNITY_SYSTEM_INPUT_LEDGER,
            INPUT_RECHECK_RUN_LEDGER,
            INPUT_MARKET_PRIORITY_LEDGER,
            INPUT_SYSTEM_RECOMMENDATION_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    candidate_input = read_jsonl(INPUT_CANDIDATE_IMPLEMENTATION_LEDGER)
    scorer_input = read_jsonl(INPUT_SCORER_CODE_INTEGRATION_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_CONTROL_RUN_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_EXECUTION_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_EXECUTION_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_REGISTRY_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_SYSTEM_INPUT_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_RUN_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_PRIORITY_LEDGER)
    system_recommendation_input = read_jsonl(INPUT_SYSTEM_RECOMMENDATION_LEDGER)

    execution_rows = [
        with_common(candidate_implementation_execution_result(row, index), generated_at, manifest_hash)
        for index, row in enumerate(candidate_input, 1)
    ]
    scorer_rows = [
        with_common(scorer_module_artifact(row, index), generated_at, manifest_hash)
        for index, row in enumerate(scorer_input, 1)
    ]
    source_rows = [
        with_common(source_control_run_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_input, 1)
    ]
    score_control_rows = [
        with_common(score_control_comparator_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_rows = [
        with_common(nofill_comparator_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_rows = [
        with_common(guard_registry_artifact(row, index), generated_at, manifest_hash)
        for index, row in enumerate(guard_input, 1)
    ]
    opportunity_rows = [
        with_common(opportunity_system_input_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_input, 1)
    ]
    recheck_rows = [
        with_common(recheck_run_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_input, 1)
    ]
    market_rows = [
        with_common(market_priority_execution_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_input, 1)
    ]
    component_rows = scorer_rows + source_rows + score_control_rows + nofill_rows + guard_rows + opportunity_rows + recheck_rows
    scope_rollups, family_rollups, market_rollups = build_rollups(execution_rows, component_rows, market_rows, generated_at, manifest_hash)
    distributions = {
        "implementation_execution_family": string_counter(execution_rows, "implementation_execution_family"),
        "implementation_execution_status": string_counter(execution_rows, "implementation_execution_status"),
        "implementation_output_component": string_counter(execution_rows, "implementation_output_component"),
        "proxy_delta_band": string_counter(execution_rows, "proxy_delta_band"),
        "scorer_module_artifact_status": string_counter(scorer_rows, "scorer_module_artifact_status"),
        "source_control_output_status": string_counter(source_rows, "source_control_output_status"),
        "score_control_output_status": string_counter(score_control_rows, "score_control_output_status"),
        "nofill_output_status": string_counter(nofill_rows, "nofill_output_status"),
        "guard_registry_artifact_status": string_counter(guard_rows, "guard_registry_artifact_status"),
        "opportunity_output_status": string_counter(opportunity_rows, "opportunity_output_status"),
        "recheck_output_status": string_counter(recheck_rows, "recheck_output_status"),
        "market_priority_execution_status": string_counter(market_rows, "market_priority_execution_status"),
        "market_priority_execution_symbol": string_counter(market_rows, "symbol"),
        "market_priority_execution_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-BUCKET-{len(buckets) + 1:04d}",
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
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by candidate implementation execution, component output, market-priority execution, rollup, bucket, source-manifest, and system-recommendation ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(
            [
                "Did every candidate implementation row become a concrete execution result row?",
                "Which default-off scorer integration candidates became module artifacts?",
                "Which source/control run actions became executable output contracts?",
                "Which score-control rows became comparator outputs, context, or repair requirements?",
                "Which no-fill rows became challenger comparators, avoid/inverse filters, stress controls, or repair outputs?",
                "Which guard rows became fail-closed registry artifacts?",
                "Which current-claim opportunity rows became system-input outputs?",
                "Which market/timeframe/session/horizon priority rows were consumed into execution outputs?",
                "What next concrete system layer follows from the execution outputs?",
            ],
            1,
        )
    ]
    counts = {
        "input_candidate_implementation_rows": len(candidate_input),
        "input_scorer_code_integration_rows": len(scorer_input),
        "input_source_control_run_rows": len(source_input),
        "input_score_control_execution_rows": len(score_control_input),
        "input_nofill_execution_rows": len(nofill_input),
        "input_guard_registry_rows": len(guard_input),
        "input_opportunity_system_input_rows": len(opportunity_input),
        "input_recheck_run_rows": len(recheck_input),
        "input_market_priority_rows": len(market_input),
        "input_market_priority_action_rows": len(market_input),
        "input_system_recommendation_rows": len(system_recommendation_input),
        "candidate_implementation_execution_result_rows": len(execution_rows),
        "scorer_module_artifact_rows": len(scorer_rows),
        "source_control_output_rows": len(source_rows),
        "score_control_comparator_output_rows": len(score_control_rows),
        "nofill_comparator_output_rows": len(nofill_rows),
        "guard_registry_artifact_rows": len(guard_rows),
        "opportunity_system_input_output_rows": len(opportunity_rows),
        "recheck_run_output_rows": len(recheck_rows),
        "market_priority_execution_output_rows": len(market_rows),
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
    all_candidate_implementation_rows_consumed = (
        len(execution_rows) == len(candidate_input) == input_result["counts"]["candidate_implementation_decision_rows"]
    )
    all_component_implementation_rows_consumed = split_total == input_result["counts"]["candidate_implementation_decision_rows"]
    all_market_priority_rows_consumed = (
        len(market_rows) == len(market_input) == input_result["counts"]["market_priority_action_rows"]
    )
    system_recommendation_rows = [
        with_common(
            {
                "system_recommendation_row_id": "OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-SYSTEM-RECOMMENDATION-0001",
                "implementation_execution_recommendation": (
                    "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION_BUNDLE_RESULT: keep the "
                    "candidate-implementation denominator intact, execute scorer module artifacts default-off, emit source/control "
                    "run outputs, execute no-fill challenger and avoid/inverse comparator outputs, bind guard registry artifacts, "
                    "consume opportunity and recheck outputs, and use market-priority execution outputs as the next concrete system "
                    "integration source."
                ),
                "candidate_implementation_execution_result_rows": len(execution_rows),
                "scorer_module_artifact_rows": len(scorer_rows),
                "source_control_output_rows": len(source_rows),
                "score_control_comparator_output_rows": len(score_control_rows),
                "nofill_comparator_output_rows": len(nofill_rows),
                "guard_registry_artifact_rows": len(guard_rows),
                "market_priority_execution_output_rows": len(market_rows),
                "input_system_recommendation_row_ids": [
                    row.get("system_recommendation_row_id") for row in system_recommendation_input
                ],
                "positive_rows_become": "default_off_scorer_modules_or_positive_nofill_challenger_outputs",
                "negative_rows_become": "avoid_inverse_entry_failure_filters_or_failure_intelligence_outputs",
                "source_control_required_rows_become": "source_control_run_outputs_or repair/proxy output contracts",
                "market_transfer_rows_become": "source_repair_shadow_proxy_control_replay_system_input_or_opportunity_execution_outputs",
                "not_terminal": True,
                "next_same_resource_layer": "consume execution outputs into concrete branch-local candidate registry modules, source/control result rows, no-fill comparator result rows, and guard-bound system integration candidates",
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
        "all_candidate_implementation_rows_consumed": all_candidate_implementation_rows_consumed,
        "all_component_implementation_rows_consumed": all_component_implementation_rows_consumed,
        "all_market_priority_rows_consumed": all_market_priority_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "implementation_execution_family_counts": distributions["implementation_execution_family"],
            "implementation_execution_status_counts": distributions["implementation_execution_status"],
            "market_priority_execution_status_counts": distributions["market_priority_execution_status"],
            "system_recommendation": system_recommendation_rows[0]["implementation_execution_recommendation"],
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_candidate_implementation_rows_consumed": all_candidate_implementation_rows_consumed,
        "all_component_implementation_rows_consumed": all_component_implementation_rows_consumed,
        "all_market_priority_rows_consumed": all_market_priority_rows_consumed,
    }
    write_jsonl(CANDIDATE_IMPLEMENTATION_EXECUTION_LEDGER, execution_rows)
    write_jsonl(SCORER_MODULE_ARTIFACT_LEDGER, scorer_rows)
    write_jsonl(SOURCE_CONTROL_OUTPUT_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_COMPARATOR_OUTPUT_LEDGER, score_control_rows)
    write_jsonl(NOFILL_COMPARATOR_OUTPUT_LEDGER, nofill_rows)
    write_jsonl(GUARD_REGISTRY_ARTIFACT_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_SYSTEM_INPUT_OUTPUT_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_RUN_OUTPUT_LEDGER, recheck_rows)
    write_jsonl(MARKET_PRIORITY_EXECUTION_LEDGER, market_rows)
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
                "# Branch-Local Unified System Candidate Implementation Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Candidate implementation execution result rows: `{counts['candidate_implementation_execution_result_rows']}`.",
                f"- Scorer module artifact rows: `{counts['scorer_module_artifact_rows']}`.",
                f"- Source/control output rows: `{counts['source_control_output_rows']}`.",
                f"- No-fill comparator output rows: `{counts['nofill_comparator_output_rows']}`.",
                f"- Guard registry artifact rows: `{counts['guard_registry_artifact_rows']}`.",
                f"- Market priority execution output rows: `{counts['market_priority_execution_output_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        CANDIDATE_IMPLEMENTATION_EXECUTION_LEDGER,
        SCORER_MODULE_ARTIFACT_LEDGER,
        SOURCE_CONTROL_OUTPUT_LEDGER,
        SCORE_CONTROL_COMPARATOR_OUTPUT_LEDGER,
        NOFILL_COMPARATOR_OUTPUT_LEDGER,
        GUARD_REGISTRY_ARTIFACT_LEDGER,
        OPPORTUNITY_SYSTEM_INPUT_OUTPUT_LEDGER,
        RECHECK_RUN_OUTPUT_LEDGER,
        MARKET_PRIORITY_EXECUTION_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
