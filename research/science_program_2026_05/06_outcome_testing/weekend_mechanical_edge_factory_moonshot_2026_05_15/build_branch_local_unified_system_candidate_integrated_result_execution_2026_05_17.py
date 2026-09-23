#!/usr/bin/env python3
"""Execute integrated scoring/result tables into branch-local dispatch outputs."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_integrated_result_execution import (
    UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
    guard_dispatch_output,
    integrated_result_execution,
    integrated_result_execution_rollup,
    market_transfer_dispatch,
    nofill_comparator_execution_output,
    opportunity_execution_output,
    recheck_execution_output,
    score_control_execution_output,
    scorer_registry_dispatch,
    source_control_execution_output,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_INTEGRATED_SCORING_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_MODULE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DEFAULT_OFF_MODULE_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_BUILDER_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_RESULT_TABLE_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_COMPARATOR_RESULT_TABLE_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_BINDING_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_OPPORTUNITY_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_TRANSFER_DECISION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_INTEGRATED_RESULT_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_REGISTRY_DISPATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_REGISTRY_DISPATCH_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_EXECUTION_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_EXECUTION_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
NOFILL_COMPARATOR_EXECUTION_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPARATOR_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
GUARD_DISPATCH_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_DISPATCH_OUTPUT_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_EXECUTION_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_OPPORTUNITY_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
RECHECK_EXECUTION_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_EXECUTION_OUTPUT_LEDGER_2026-05-17.jsonl"
MARKET_TRANSFER_DISPATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TRANSFER_DISPATCH_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system candidate integrated-result execution bundle. It consumes integrated scoring/result tables "
    "into scorer registry dispatch outputs, source/control execution outputs, score-control execution outputs, no-fill "
    "comparator execution outputs, guard dispatch outputs, opportunity/recheck execution outputs, market-transfer dispatch "
    "rows, and a system recommendation row. It does not change live behavior, place orders, or claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-SRC-{index:04d}",
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
                row.get("integrated_result_execution_family"),
            )
        ].append(row)
        by_family[(row.get("integrated_result_execution_family"), row.get("integrated_result_execution_status"))].append(row)
    for row in component_rows:
        family = (
            row.get("scorer_registry_dispatch_status")
            or row.get("source_control_execution_status")
            or row.get("score_control_execution_status")
            or row.get("nofill_comparator_execution_status")
            or row.get("guard_dispatch_status")
            or row.get("opportunity_execution_status")
            or row.get("recheck_execution_status")
        )
        by_family[(row.get("unified_system_candidate_integrated_result_execution"), family)].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_transfer_dispatch_action"))].append(row)
    scope_rollups = [
        with_common(integrated_result_execution_rollup(key, by_scope[key], index, "scope_integrated_result_execution"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(integrated_result_execution_rollup(key, by_family[key], index, "family_integrated_result_execution"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(integrated_result_execution_rollup(key, by_market[key], index, "market_integrated_result_execution"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_candidate_integrated_result_execution_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_integrated_result_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed integrated result tables into branch-local registry/source/no-fill/guard/market dispatch outputs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_DECISION_LEDGER,
            INPUT_MODULE_LEDGER,
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
    decision_input = read_jsonl(INPUT_DECISION_LEDGER)
    module_input = read_jsonl(INPUT_MODULE_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_LEDGER)

    execution_rows = [with_common(integrated_result_execution(row, index), generated_at, manifest_hash) for index, row in enumerate(decision_input, 1)]
    registry_rows = [with_common(scorer_registry_dispatch(row, index), generated_at, manifest_hash) for index, row in enumerate(module_input, 1)]
    source_rows = [with_common(source_control_execution_output(row, index), generated_at, manifest_hash) for index, row in enumerate(source_input, 1)]
    score_control_rows = [
        with_common(score_control_execution_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_rows = [
        with_common(nofill_comparator_execution_output(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_rows = [with_common(guard_dispatch_output(row, index), generated_at, manifest_hash) for index, row in enumerate(guard_input, 1)]
    opportunity_rows = [with_common(opportunity_execution_output(row, index), generated_at, manifest_hash) for index, row in enumerate(opportunity_input, 1)]
    recheck_rows = [with_common(recheck_execution_output(row, index), generated_at, manifest_hash) for index, row in enumerate(recheck_input, 1)]
    market_rows = [with_common(market_transfer_dispatch(row, index), generated_at, manifest_hash) for index, row in enumerate(market_input, 1)]
    component_rows = registry_rows + source_rows + score_control_rows + nofill_rows + guard_rows + opportunity_rows + recheck_rows

    scope_rollups, family_rollups, market_rollups = build_rollups(execution_rows, component_rows, market_rows, generated_at, manifest_hash)
    distributions = {
        "integrated_result_execution_family": string_counter(execution_rows, "integrated_result_execution_family"),
        "integrated_result_execution_status": string_counter(execution_rows, "integrated_result_execution_status"),
        "scorer_registry_dispatch_status": string_counter(registry_rows, "scorer_registry_dispatch_status"),
        "source_control_execution_status": string_counter(source_rows, "source_control_execution_status"),
        "score_control_execution_status": string_counter(score_control_rows, "score_control_execution_status"),
        "nofill_comparator_execution_status": string_counter(nofill_rows, "nofill_comparator_execution_status"),
        "avoid_inverse_feature_emitted": string_counter(nofill_rows, "avoid_inverse_feature_emitted"),
        "status_quo_comparator_scoring_ready": string_counter(nofill_rows, "status_quo_comparator_scoring_ready"),
        "guard_dispatch_status": string_counter(guard_rows, "guard_dispatch_status"),
        "opportunity_execution_status": string_counter(opportunity_rows, "opportunity_execution_status"),
        "recheck_execution_status": string_counter(recheck_rows, "recheck_execution_status"),
        "market_transfer_dispatch_action": string_counter(market_rows, "market_transfer_dispatch_action"),
        "market_transfer_symbol": string_counter(market_rows, "symbol"),
        "market_transfer_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-BUCKET-{len(buckets) + 1:04d}",
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
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by integrated-result execution, scorer registry, source/control, no-fill, guard, opportunity, market dispatch, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(
            [
                "Did every integrated scoring decision become an execution dispatch row?",
                "Which module result rows emitted default-off scorer registry dispatch outputs?",
                "Which source/control result rows emitted exact, repair/proxy, or context execution outputs?",
                "Which no-fill result rows emitted status-quo comparator scoring versus avoid/inverse features?",
                "Which guard rows emitted fail-closed dispatch outputs?",
                "Which market-transfer rows dispatched source repair, shadow, proxy/control, replay-only, system-input, or current-claim-preservation actions?",
                "What same-resource execution layer follows from these dispatch outputs?",
            ],
            1,
        )
    ]
    counts = {
        "input_integrated_scoring_decision_rows": len(decision_input),
        "input_default_off_module_result_rows": len(module_input),
        "input_source_control_builder_result_rows": len(source_input),
        "input_score_control_result_table_rows": len(score_control_input),
        "input_nofill_comparator_result_table_rows": len(nofill_input),
        "input_guard_binding_result_rows": len(guard_input),
        "input_opportunity_result_rows": len(opportunity_input),
        "input_recheck_result_rows": len(recheck_input),
        "input_market_transfer_decision_rows": len(market_input),
        "integrated_result_execution_rows": len(execution_rows),
        "scorer_registry_dispatch_rows": len(registry_rows),
        "source_control_execution_output_rows": len(source_rows),
        "score_control_execution_output_rows": len(score_control_rows),
        "nofill_comparator_execution_output_rows": len(nofill_rows),
        "guard_dispatch_output_rows": len(guard_rows),
        "opportunity_execution_output_rows": len(opportunity_rows),
        "recheck_execution_output_rows": len(recheck_rows),
        "market_transfer_dispatch_rows": len(market_rows),
        "system_recommendation_rows": 1,
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_integrated_result_rows_consumed = (
        len(execution_rows)
        == len(decision_input)
        == input_result["counts"]["integrated_scoring_decision_rows"]
    )
    all_component_result_rows_consumed = len(component_rows) == input_result["counts"]["integrated_scoring_decision_rows"]
    all_market_transfer_rows_consumed = (
        len(market_rows)
        == len(market_input)
        == input_result["counts"]["market_transfer_decision_rows"]
    )
    system_recommendation_rows = [
        with_common(
            {
                "system_recommendation_row_id": "OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-SYSTEM-RECOMMENDATION-0001",
                "integrated_result_execution_recommendation": (
                    "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION_BUNDLE_RESULT: consume dispatch "
                    "outputs into executable branch-local scorer registry module materialization, source-control builder "
                    "runs, no-fill comparator score tables, avoid/inverse feature tables, guard-enforced router code, and "
                    "market-transfer action queues."
                ),
                "integrated_result_execution_rows": len(execution_rows),
                "scorer_registry_dispatch_rows": len(registry_rows),
                "source_control_execution_output_rows": len(source_rows),
                "nofill_comparator_execution_output_rows": len(nofill_rows),
                "guard_dispatch_output_rows": len(guard_rows),
                "market_transfer_dispatch_rows": len(market_rows),
                "not_terminal": True,
                "next_same_resource_layer": "materialize dispatch outputs into branch-local registry/router code, source-control builder runs, no-fill comparator score tables, avoid/inverse feature tables, guard enforcement, and market-transfer action queues",
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
        "all_integrated_result_rows_consumed": all_integrated_result_rows_consumed,
        "all_component_result_rows_consumed": all_component_result_rows_consumed,
        "all_market_transfer_rows_consumed": all_market_transfer_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "integrated_result_execution_family_counts": distributions["integrated_result_execution_family"],
            "integrated_result_execution_status_counts": distributions["integrated_result_execution_status"],
            "market_transfer_dispatch_action_counts": distributions["market_transfer_dispatch_action"],
            "system_recommendation": system_recommendation_rows[0]["integrated_result_execution_recommendation"],
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_integrated_result_rows_consumed": all_integrated_result_rows_consumed,
        "all_component_result_rows_consumed": all_component_result_rows_consumed,
        "all_market_transfer_rows_consumed": all_market_transfer_rows_consumed,
    }
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        EXECUTION_LEDGER,
        SCORER_REGISTRY_DISPATCH_LEDGER,
        SOURCE_CONTROL_EXECUTION_OUTPUT_LEDGER,
        SCORE_CONTROL_EXECUTION_OUTPUT_LEDGER,
        NOFILL_COMPARATOR_EXECUTION_OUTPUT_LEDGER,
        GUARD_DISPATCH_OUTPUT_LEDGER,
        OPPORTUNITY_EXECUTION_OUTPUT_LEDGER,
        RECHECK_EXECUTION_OUTPUT_LEDGER,
        MARKET_TRANSFER_DISPATCH_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(EXECUTION_LEDGER, execution_rows)
    write_jsonl(SCORER_REGISTRY_DISPATCH_LEDGER, registry_rows)
    write_jsonl(SOURCE_CONTROL_EXECUTION_OUTPUT_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_EXECUTION_OUTPUT_LEDGER, score_control_rows)
    write_jsonl(NOFILL_COMPARATOR_EXECUTION_OUTPUT_LEDGER, nofill_rows)
    write_jsonl(GUARD_DISPATCH_OUTPUT_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_EXECUTION_OUTPUT_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_EXECUTION_OUTPUT_LEDGER, recheck_rows)
    write_jsonl(MARKET_TRANSFER_DISPATCH_LEDGER, market_rows)
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
                "# Branch-Local Unified System Candidate Integrated Result Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Integrated result execution rows: `{counts['integrated_result_execution_rows']}`.",
                f"- Scorer registry dispatch rows: `{counts['scorer_registry_dispatch_rows']}`.",
                f"- Source/control execution output rows: `{counts['source_control_execution_output_rows']}`.",
                f"- No-fill comparator execution output rows: `{counts['nofill_comparator_execution_output_rows']}`.",
                f"- Guard dispatch output rows: `{counts['guard_dispatch_output_rows']}`.",
                f"- Market-transfer dispatch rows: `{counts['market_transfer_dispatch_rows']}`.",
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
