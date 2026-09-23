#!/usr/bin/env python3
"""Consume execution-integration rows into integrated scoring/result tables."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_integrated_scoring_result import (
    UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
    default_off_module_result,
    guard_binding_result,
    integrated_decision,
    integrated_result_rollup,
    market_transfer_decision,
    nofill_comparator_result_table,
    opportunity_result,
    recheck_result,
    score_control_result_table,
    source_control_builder_result,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_INTEGRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXECUTION_INTEGRATION_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_BOUND_INTEGRATION_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_OPPORTUNITY_INTEGRATION_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_INTEGRATION_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_SYSTEM_INTEGRATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INTEGRATED_SCORING_LEDGER = ROUTE_DIR / f"{PREFIX}_INTEGRATED_SCORING_DECISION_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_MODULE_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_MODULE_RESULT_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_BUILDER_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_BUILDER_RESULT_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_RESULT_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_RESULT_TABLE_LEDGER_2026-05-17.jsonl"
NOFILL_COMPARATOR_RESULT_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPARATOR_RESULT_TABLE_LEDGER_2026-05-17.jsonl"
GUARD_BINDING_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_BINDING_RESULT_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_OPPORTUNITY_RESULT_LEDGER_2026-05-17.jsonl"
RECHECK_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_RESULT_LEDGER_2026-05-17.jsonl"
MARKET_TRANSFER_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TRANSFER_DECISION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system candidate integrated scoring/result bundle. It consumes execution-integration rows into "
    "integrated scoring decisions, default-off module results, source/control builder results, score-control result tables, "
    "no-fill comparator result tables, guard-binding results, opportunity/recheck results, market-transfer decisions, and a "
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-RESULT-SRC-{index:04d}",
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
    decision_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in decision_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("integrated_result_decision"),
            )
        ].append(row)
        by_family[(row.get("integrated_result_decision"), row.get("integrated_result_role"))].append(row)
    for row in component_rows:
        family = (
            row.get("module_result_status")
            or row.get("source_builder_decision")
            or row.get("score_control_decision")
            or row.get("nofill_comparator_decision")
            or row.get("guard_binding_status")
            or row.get("opportunity_result_status")
            or row.get("recheck_result_status")
        )
        by_family[(row.get("unified_system_candidate_integrated_scoring_result"), family)].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_transfer_decision"))].append(row)
    scope_rollups = [
        with_common(integrated_result_rollup(key, by_scope[key], index, "scope_integrated_scoring_result"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(integrated_result_rollup(key, by_family[key], index, "family_integrated_scoring_result"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(integrated_result_rollup(key, by_market[key], index, "market_integrated_scoring_result"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_candidate_integrated_scoring_result_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_integrated_scoring_result_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed execution-integration rows into integrated scoring/result decisions and component tables.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_INTEGRATION_LEDGER,
            INPUT_REGISTRY_LEDGER,
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
    integration_input = read_jsonl(INPUT_INTEGRATION_LEDGER)
    registry_input = read_jsonl(INPUT_REGISTRY_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_LEDGER)

    decision_rows = [with_common(integrated_decision(row, index), generated_at, manifest_hash) for index, row in enumerate(integration_input, 1)]
    module_rows = [with_common(default_off_module_result(row, index), generated_at, manifest_hash) for index, row in enumerate(registry_input, 1)]
    source_rows = [with_common(source_control_builder_result(row, index), generated_at, manifest_hash) for index, row in enumerate(source_input, 1)]
    score_control_rows = [
        with_common(score_control_result_table(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_rows = [
        with_common(nofill_comparator_result_table(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_rows = [with_common(guard_binding_result(row, index), generated_at, manifest_hash) for index, row in enumerate(guard_input, 1)]
    opportunity_rows = [with_common(opportunity_result(row, index), generated_at, manifest_hash) for index, row in enumerate(opportunity_input, 1)]
    recheck_rows = [with_common(recheck_result(row, index), generated_at, manifest_hash) for index, row in enumerate(recheck_input, 1)]
    market_rows = [with_common(market_transfer_decision(row, index), generated_at, manifest_hash) for index, row in enumerate(market_input, 1)]
    component_rows = module_rows + source_rows + score_control_rows + nofill_rows + guard_rows + opportunity_rows + recheck_rows

    scope_rollups, family_rollups, market_rollups = build_rollups(decision_rows, component_rows, market_rows, generated_at, manifest_hash)
    distributions = {
        "integrated_result_decision": string_counter(decision_rows, "integrated_result_decision"),
        "integrated_result_role": string_counter(decision_rows, "integrated_result_role"),
        "keep_kill_redesign_implement_decision": string_counter(decision_rows, "keep_kill_redesign_implement_decision"),
        "integrated_proxy_delta_band": string_counter(decision_rows, "integrated_proxy_delta_band"),
        "module_result_status": string_counter(module_rows, "module_result_status"),
        "module_result_decision": string_counter(module_rows, "module_result_decision"),
        "source_builder_decision": string_counter(source_rows, "source_builder_decision"),
        "score_control_decision": string_counter(score_control_rows, "score_control_decision"),
        "nofill_comparator_decision": string_counter(nofill_rows, "nofill_comparator_decision"),
        "guard_binding_status": string_counter(guard_rows, "guard_binding_status"),
        "opportunity_result_status": string_counter(opportunity_rows, "opportunity_result_status"),
        "recheck_result_status": string_counter(recheck_rows, "recheck_result_status"),
        "market_transfer_decision": string_counter(market_rows, "market_transfer_decision"),
        "market_transfer_symbol": string_counter(market_rows, "symbol"),
        "market_transfer_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-RESULT-BUCKET-{len(buckets) + 1:04d}",
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
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-RESULT-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by integrated scoring decisions, module/source/control/no-fill/guard/opportunity/market result tables, rollups, buckets, and source manifest.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(
            [
                "Did every execution-integration row become an integrated keep/redesign/source/control/implement decision?",
                "Which positive rows become default-off module or no-fill challenger result tables?",
                "Which negative rows become avoid/inverse or entry-failure intelligence instead of deletion?",
                "Which source/control rows become executable builder results with missing-source proofs?",
                "Which no-fill rows become challenger, avoid/inverse, repair, or stress decisions?",
                "Which guard rows bind fail-closed before any scorer or comparator use?",
                "Which market/timeframe rows become source repair, shadow, proxy/control, replay-only, system-input, or current-claim-preserved decisions?",
                "What same-resource system layer follows from the integrated result tables?",
            ],
            1,
        )
    ]
    counts = {
        "input_execution_integration_decision_rows": len(integration_input),
        "input_registry_module_rows": len(registry_input),
        "input_source_control_result_rows": len(source_input),
        "input_score_control_result_rows": len(score_control_input),
        "input_nofill_result_rows": len(nofill_input),
        "input_guard_bound_rows": len(guard_input),
        "input_opportunity_integration_rows": len(opportunity_input),
        "input_recheck_integration_rows": len(recheck_input),
        "input_market_system_integration_rows": len(market_input),
        "integrated_scoring_decision_rows": len(decision_rows),
        "default_off_module_result_rows": len(module_rows),
        "source_control_builder_result_rows": len(source_rows),
        "score_control_result_table_rows": len(score_control_rows),
        "nofill_comparator_result_table_rows": len(nofill_rows),
        "guard_binding_result_rows": len(guard_rows),
        "opportunity_result_rows": len(opportunity_rows),
        "recheck_result_rows": len(recheck_rows),
        "market_transfer_decision_rows": len(market_rows),
        "system_recommendation_rows": 1,
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_integration_rows_consumed = (
        len(decision_rows)
        == len(integration_input)
        == input_result["counts"]["execution_integration_decision_rows"]
    )
    all_component_rows_consumed = len(component_rows) == input_result["counts"]["execution_integration_decision_rows"]
    all_market_rows_consumed = (
        len(market_rows)
        == len(market_input)
        == input_result["counts"]["market_system_integration_rows"]
    )
    system_recommendation_rows = [
        with_common(
            {
                "system_recommendation_row_id": "OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-RESULT-SYSTEM-RECOMMENDATION-0001",
                "integrated_result_recommendation": (
                    "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT_BUNDLE_RESULT: consume integrated "
                    "module/source/control/no-fill/guard/market result tables into branch-local scorer registry code, "
                    "source-control builder execution, no-fill status-quo comparator scoring, avoid/inverse feature emission, "
                    "and market-transfer action dispatch with fail-closed guards."
                ),
                "integrated_scoring_decision_rows": len(decision_rows),
                "default_off_module_result_rows": len(module_rows),
                "source_control_builder_result_rows": len(source_rows),
                "nofill_comparator_result_table_rows": len(nofill_rows),
                "guard_binding_result_rows": len(guard_rows),
                "market_transfer_decision_rows": len(market_rows),
                "not_terminal": True,
                "next_same_resource_layer": "execute integrated result tables into branch-local scorer registry code, source-control builder outputs, no-fill comparator scoring, avoid/inverse features, guard dispatch, and market-transfer actions",
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
        "all_integration_rows_consumed": all_integration_rows_consumed,
        "all_component_rows_consumed": all_component_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "integrated_result_decision_counts": distributions["integrated_result_decision"],
            "keep_kill_redesign_implement_decision_counts": distributions["keep_kill_redesign_implement_decision"],
            "market_transfer_decision_counts": distributions["market_transfer_decision"],
            "system_recommendation": system_recommendation_rows[0]["integrated_result_recommendation"],
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_integration_rows_consumed": all_integration_rows_consumed,
        "all_component_rows_consumed": all_component_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
    }
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        INTEGRATED_SCORING_LEDGER,
        DEFAULT_OFF_MODULE_RESULT_LEDGER,
        SOURCE_CONTROL_BUILDER_RESULT_LEDGER,
        SCORE_CONTROL_RESULT_TABLE_LEDGER,
        NOFILL_COMPARATOR_RESULT_TABLE_LEDGER,
        GUARD_BINDING_RESULT_LEDGER,
        OPPORTUNITY_RESULT_LEDGER,
        RECHECK_RESULT_LEDGER,
        MARKET_TRANSFER_DECISION_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(INTEGRATED_SCORING_LEDGER, decision_rows)
    write_jsonl(DEFAULT_OFF_MODULE_RESULT_LEDGER, module_rows)
    write_jsonl(SOURCE_CONTROL_BUILDER_RESULT_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_RESULT_TABLE_LEDGER, score_control_rows)
    write_jsonl(NOFILL_COMPARATOR_RESULT_TABLE_LEDGER, nofill_rows)
    write_jsonl(GUARD_BINDING_RESULT_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_RESULT_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_RESULT_LEDGER, recheck_rows)
    write_jsonl(MARKET_TRANSFER_DECISION_LEDGER, market_rows)
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
                "# Branch-Local Unified System Candidate Integrated Scoring Result Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Integrated scoring decision rows: `{counts['integrated_scoring_decision_rows']}`.",
                f"- Default-off module result rows: `{counts['default_off_module_result_rows']}`.",
                f"- Source/control builder result rows: `{counts['source_control_builder_result_rows']}`.",
                f"- No-fill comparator result-table rows: `{counts['nofill_comparator_result_table_rows']}`.",
                f"- Guard-binding result rows: `{counts['guard_binding_result_rows']}`.",
                f"- Market-transfer decision rows: `{counts['market_transfer_decision_rows']}`.",
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
