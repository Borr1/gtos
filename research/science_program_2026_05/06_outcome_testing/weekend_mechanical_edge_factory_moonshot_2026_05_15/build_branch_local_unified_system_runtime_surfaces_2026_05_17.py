#!/usr/bin/env python3
"""Consume executable artifact rows into branch-local runtime surfaces."""

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

from src.research_infra.moonshot_branch_local_unified_system_runtime_surfaces import (
    UNIFIED_SYSTEM_RUNTIME_SURFACE,
    guard_runtime_surface,
    market_source_runtime_surface,
    nofill_replay_surface,
    opportunity_runtime_surface,
    recheck_runtime_surface,
    runtime_surface_decision,
    runtime_surface_rollup,
    runtime_surface_self_test,
    scorer_registry_surface,
    score_control_runtime_surface,
    source_replay_surface,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_EXECUTABLE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXECUTABLE_ARTIFACT_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_CODE_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CODE_SURFACE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_BUILDER_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_COMPARISON_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_OUTCOME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_COMPARATOR_OUTCOME_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_BINDING_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_ROUTE_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_SOURCE_ACTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_RUNTIME_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
RUNTIME_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_RUNTIME_SURFACE_DECISION_LEDGER_2026-05-17.jsonl"
SCORER_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_REGISTRY_LEDGER_2026-05-17.jsonl"
SOURCE_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPLAY_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_RUNTIME_LEDGER_2026-05-17.jsonl"
NOFILL_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_REPLAY_SCORER_LEDGER_2026-05-17.jsonl"
GUARD_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_RUNTIME_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_RUNTIME_LEDGER_2026-05-17.jsonl"
RECHECK_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_RUNTIME_LEDGER_2026-05-17.jsonl"
MARKET_SOURCE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_SOURCE_RUNTIME_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_SELF_TEST_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system runtime-surfaces bundle. It consumes every executable artifact row into branch-local "
    "runtime surface behavior, applies scope self-tests to every surface row, and consumes every market source action "
    "into a market/source runtime surface. It does not change live behavior, place orders, or claim broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-RUNTIME-SRC-{index:04d}",
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
    runtime_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in runtime_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("runtime_surface_family"),
            )
        ].append(row)
        by_family[(row.get("runtime_surface_family"), row.get("runtime_surface_status"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_source_runtime_status"))].append(row)
    scope_rollups = [
        with_common(runtime_surface_rollup(key, by_scope[key], index, "scope_runtime_surface"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(runtime_surface_rollup(key, by_family[key], index, "family_runtime_surface"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(runtime_surface_rollup(key, by_market[key], index, "market_source_runtime_surface"), generated_at, manifest_hash)
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
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_branch_local_unified_system_runtime_surfaces_bundle"] = {
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
        "event": "branch_local_unified_system_runtime_surfaces_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed executable artifacts into branch-local runtime surfaces, self-tests, scorer/source/no-fill/guard/opportunity/recheck surfaces, and market source runtime actions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_EXECUTABLE_LEDGER,
            INPUT_CODE_SURFACE_LEDGER,
            INPUT_SOURCE_CONTROL_LEDGER,
            INPUT_SCORE_CONTROL_LEDGER,
            INPUT_NOFILL_OUTCOME_LEDGER,
            INPUT_GUARD_EXECUTION_LEDGER,
            INPUT_OPPORTUNITY_LEDGER,
            INPUT_RECHECK_LEDGER,
            INPUT_MARKET_SOURCE_ACTION_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    executable_rows = read_jsonl(INPUT_EXECUTABLE_LEDGER)
    code_surface_rows = read_jsonl(INPUT_CODE_SURFACE_LEDGER)
    source_control_rows = read_jsonl(INPUT_SOURCE_CONTROL_LEDGER)
    score_control_rows = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_rows = read_jsonl(INPUT_NOFILL_OUTCOME_LEDGER)
    guard_rows = read_jsonl(INPUT_GUARD_EXECUTION_LEDGER)
    opportunity_rows = read_jsonl(INPUT_OPPORTUNITY_LEDGER)
    recheck_rows_input = read_jsonl(INPUT_RECHECK_LEDGER)
    market_action_rows = read_jsonl(INPUT_MARKET_SOURCE_ACTION_LEDGER)

    runtime_rows = [
        with_common(runtime_surface_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(executable_rows, 1)
    ]
    scorer_rows = [
        with_common(scorer_registry_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(code_surface_rows, 1)
    ]
    source_rows = [
        with_common(source_replay_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_control_rows, 1)
    ]
    score_control_runtime_rows = [
        with_common(score_control_runtime_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_rows, 1)
    ]
    nofill_runtime_rows = [
        with_common(nofill_replay_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_rows, 1)
    ]
    guard_runtime_rows = [
        with_common(guard_runtime_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(guard_rows, 1)
    ]
    opportunity_runtime_rows = [
        with_common(opportunity_runtime_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_rows, 1)
    ]
    recheck_runtime_rows = [
        with_common(recheck_runtime_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_rows_input, 1)
    ]
    market_runtime_rows = [
        with_common(market_source_runtime_surface(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_action_rows, 1)
    ]
    self_test_rows = [
        with_common(runtime_surface_self_test(row, index), generated_at, manifest_hash)
        for index, row in enumerate(runtime_rows, 1)
    ]
    scope_rollups, family_rollups, market_rollups = build_rollups(runtime_rows, market_runtime_rows, generated_at, manifest_hash)

    distributions = {
        "runtime_surface_family": string_counter(runtime_rows, "runtime_surface_family"),
        "runtime_surface_status": string_counter(runtime_rows, "runtime_surface_status"),
        "scorer_registry_status": string_counter(scorer_rows, "scorer_registry_status"),
        "source_replay_status": string_counter(source_rows, "source_replay_status"),
        "score_control_runtime_status": string_counter(score_control_runtime_rows, "score_control_runtime_status"),
        "nofill_replay_status": string_counter(nofill_runtime_rows, "nofill_replay_status"),
        "guard_runtime_status": string_counter(guard_runtime_rows, "guard_runtime_status"),
        "opportunity_runtime_status": string_counter(opportunity_runtime_rows, "opportunity_runtime_status"),
        "recheck_runtime_status": string_counter(recheck_runtime_rows, "recheck_runtime_status"),
        "market_source_runtime_status": string_counter(market_runtime_rows, "market_source_runtime_status"),
        "surface_self_test_emission": string_counter(self_test_rows, "emitted_observation_class"),
        "market_runtime_symbol": string_counter(market_runtime_rows, "symbol"),
        "market_runtime_tradability_status": string_counter(market_runtime_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-RUNTIME-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every executable artifact row become a branch-local runtime surface decision?",
        "Did every runtime surface execute a scope self-test with positive match and negative mismatch behavior?",
        "Which code surfaces are registered as default-off scorer runtime surfaces?",
        "Which source/control builder rows are runtime replay or source/proxy acquisition surfaces?",
        "Which no-fill comparator outcomes become positive challenger, avoid/inverse, stress, or repair runtime surfaces?",
        "Which guard bindings are fail-closed runtime surfaces?",
        "Which current-claim rejections remain opportunity routes at runtime?",
        "Which market/timeframe/session/horizon rows become market source runtime surfaces?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-RUNTIME-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by runtime surface, scorer, source, no-fill, guard, opportunity, recheck, market, self-test, rollup, and bucket ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    split_total = (
        len(scorer_rows)
        + len(source_rows)
        + len(score_control_runtime_rows)
        + len(nofill_runtime_rows)
        + len(guard_runtime_rows)
        + len(opportunity_runtime_rows)
        + len(recheck_runtime_rows)
    )
    counts = {
        "input_executable_artifact_rows": len(executable_rows),
        "input_market_source_action_rows": len(market_action_rows),
        "runtime_surface_decision_rows": len(runtime_rows),
        "scorer_registry_rows": len(scorer_rows),
        "source_replay_implementation_rows": len(source_rows),
        "score_control_runtime_rows": len(score_control_runtime_rows),
        "nofill_replay_scorer_rows": len(nofill_runtime_rows),
        "guard_runtime_rows": len(guard_runtime_rows),
        "current_claim_opportunity_runtime_rows": len(opportunity_runtime_rows),
        "recheck_runtime_rows": len(recheck_runtime_rows),
        "market_source_runtime_rows": len(market_runtime_rows),
        "surface_self_test_rows": len(self_test_rows),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_rows_consumed = len(runtime_rows) == len(executable_rows) == input_result["counts"]["executable_artifact_decision_rows"]
    all_split_rows_consumed = split_total == len(executable_rows)
    all_market_rows_consumed = len(market_runtime_rows) == len(market_action_rows) == input_result["counts"]["market_source_action_rows"]
    all_self_tests_executed = len(self_test_rows) == len(runtime_rows) and all(
        row.get("positive_scope_match_result") is True and row.get("negative_scope_mismatch_result") is False
        for row in self_test_rows
    )
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_executable_rows_consumed": all_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_source_rows_consumed": all_market_rows_consumed,
        "all_runtime_surface_self_tests_executed": all_self_tests_executed,
        "bucket_distributions": distributions,
        "system_decision": {
            "runtime_surface_family_counts": distributions["runtime_surface_family"],
            "market_source_runtime_status_counts": distributions["market_source_runtime_status"],
            "surface_self_test_emission_counts": distributions["surface_self_test_emission"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_BUNDLE_RESULT: execute default-off runtime surfaces into branch-local scorer/source/replay implementation, preserving no-fill avoid/inverse intelligence, exact-control builders, guards, opportunity routes, and market expansion rows.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_executable_rows_consumed": all_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_source_rows_consumed": all_market_rows_consumed,
        "all_runtime_surface_self_tests_executed": all_self_tests_executed,
    }
    write_jsonl(RUNTIME_SURFACE_LEDGER, runtime_rows)
    write_jsonl(SCORER_REGISTRY_LEDGER, scorer_rows)
    write_jsonl(SOURCE_REPLAY_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_RUNTIME_LEDGER, score_control_runtime_rows)
    write_jsonl(NOFILL_REPLAY_LEDGER, nofill_runtime_rows)
    write_jsonl(GUARD_RUNTIME_LEDGER, guard_runtime_rows)
    write_jsonl(OPPORTUNITY_RUNTIME_LEDGER, opportunity_runtime_rows)
    write_jsonl(RECHECK_RUNTIME_LEDGER, recheck_runtime_rows)
    write_jsonl(MARKET_SOURCE_RUNTIME_LEDGER, market_runtime_rows)
    write_jsonl(SELF_TEST_LEDGER, self_test_rows)
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
                "# Branch-Local Unified System Runtime Surfaces Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Runtime surface decision rows: `{counts['runtime_surface_decision_rows']}`.",
                f"- Scorer registry rows: `{counts['scorer_registry_rows']}`.",
                f"- Source replay implementation rows: `{counts['source_replay_implementation_rows']}`.",
                f"- No-fill replay scorer rows: `{counts['nofill_replay_scorer_rows']}`.",
                f"- Surface self-test rows: `{counts['surface_self_test_rows']}`.",
                f"- Market source runtime rows: `{counts['market_source_runtime_rows']}`.",
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
        RUNTIME_SURFACE_LEDGER,
        SCORER_REGISTRY_LEDGER,
        SOURCE_REPLAY_LEDGER,
        SCORE_CONTROL_RUNTIME_LEDGER,
        NOFILL_REPLAY_LEDGER,
        GUARD_RUNTIME_LEDGER,
        OPPORTUNITY_RUNTIME_LEDGER,
        RECHECK_RUNTIME_LEDGER,
        MARKET_SOURCE_RUNTIME_LEDGER,
        SELF_TEST_LEDGER,
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
