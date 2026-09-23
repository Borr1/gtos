#!/usr/bin/env python3
"""Consume candidate-system synthesis rows into executable branch-local runtime bindings."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_runtime import (
    UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
    candidate_runtime_decision,
    candidate_runtime_rollup,
    candidate_runtime_self_test,
    component_runtime_binding,
    market_runtime_binding,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_CANDIDATE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_COMPONENT_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_COMPONENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_COMPONENT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_RUNTIME
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CANDIDATE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_RUNTIME_DECISION_LEDGER_2026-05-17.jsonl"
CANDIDATE_RUNTIME_SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_RUNTIME_SELF_TEST_LEDGER_2026-05-17.jsonl"
SCORER_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
SOURCE_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
NOFILL_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
GUARD_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
RECHECK_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
MARKET_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system candidate-runtime bundle. It consumes every candidate-system row into event-matchable "
    "runtime decisions, executes positive and negative scope self-tests, and binds every scorer/source/control/no-fill/"
    "guard/opportunity/recheck/market component to branch-local runtime contracts. It does not change live behavior, "
    "place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-SRC-{index:04d}",
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
    binding_rows: list[dict[str, Any]],
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
                row.get("candidate_runtime_component_family"),
            )
        ].append(row)
        by_family[(row.get("candidate_runtime_component_family"), row.get("candidate_runtime_status"))].append(row)
    for row in binding_rows:
        by_family[(row.get("component_type"), row.get("component_runtime_binding_status"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_runtime_binding_status"))].append(row)
    scope_rollups = [
        with_common(candidate_runtime_rollup(key, by_scope[key], index, "scope_candidate_runtime"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(candidate_runtime_rollup(key, by_family[key], index, "family_candidate_runtime_or_binding"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(candidate_runtime_rollup(key, by_market[key], index, "market_candidate_runtime_binding"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_candidate_runtime_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_runtime_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed candidate synthesis rows into executable candidate runtime decisions, self-tests, component bindings, and market runtime bindings.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_CANDIDATE_EXECUTION_LEDGER,
            INPUT_SCORER_COMPONENT_LEDGER,
            INPUT_SOURCE_COMPONENT_LEDGER,
            INPUT_SCORE_CONTROL_COMPONENT_LEDGER,
            INPUT_NOFILL_COMPONENT_LEDGER,
            INPUT_GUARD_COMPONENT_LEDGER,
            INPUT_OPPORTUNITY_COMPONENT_LEDGER,
            INPUT_RECHECK_COMPONENT_LEDGER,
            INPUT_MARKET_COMPONENT_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    candidate_rows_input = read_jsonl(INPUT_CANDIDATE_EXECUTION_LEDGER)
    scorer_rows_input = read_jsonl(INPUT_SCORER_COMPONENT_LEDGER)
    source_rows_input = read_jsonl(INPUT_SOURCE_COMPONENT_LEDGER)
    score_control_rows_input = read_jsonl(INPUT_SCORE_CONTROL_COMPONENT_LEDGER)
    nofill_rows_input = read_jsonl(INPUT_NOFILL_COMPONENT_LEDGER)
    guard_rows_input = read_jsonl(INPUT_GUARD_COMPONENT_LEDGER)
    opportunity_rows_input = read_jsonl(INPUT_OPPORTUNITY_COMPONENT_LEDGER)
    recheck_rows_input = read_jsonl(INPUT_RECHECK_COMPONENT_LEDGER)
    market_rows_input = read_jsonl(INPUT_MARKET_COMPONENT_LEDGER)

    runtime_rows = [
        with_common(candidate_runtime_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(candidate_rows_input, 1)
    ]
    self_test_rows = [
        with_common(candidate_runtime_self_test(row, index), generated_at, manifest_hash)
        for index, row in enumerate(runtime_rows, 1)
    ]
    scorer_bindings = [
        with_common(component_runtime_binding(row, index, "SCORER"), generated_at, manifest_hash)
        for index, row in enumerate(scorer_rows_input, 1)
    ]
    source_bindings = [
        with_common(component_runtime_binding(row, index, "SOURCE"), generated_at, manifest_hash)
        for index, row in enumerate(source_rows_input, 1)
    ]
    score_control_bindings = [
        with_common(component_runtime_binding(row, index, "SCORE_CONTROL"), generated_at, manifest_hash)
        for index, row in enumerate(score_control_rows_input, 1)
    ]
    nofill_bindings = [
        with_common(component_runtime_binding(row, index, "NOFILL"), generated_at, manifest_hash)
        for index, row in enumerate(nofill_rows_input, 1)
    ]
    guard_bindings = [
        with_common(component_runtime_binding(row, index, "GUARD"), generated_at, manifest_hash)
        for index, row in enumerate(guard_rows_input, 1)
    ]
    opportunity_bindings = [
        with_common(component_runtime_binding(row, index, "OPPORTUNITY"), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_rows_input, 1)
    ]
    recheck_bindings = [
        with_common(component_runtime_binding(row, index, "RECHECK"), generated_at, manifest_hash)
        for index, row in enumerate(recheck_rows_input, 1)
    ]
    market_bindings = [
        with_common(market_runtime_binding(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_rows_input, 1)
    ]
    all_binding_rows = (
        scorer_bindings
        + source_bindings
        + score_control_bindings
        + nofill_bindings
        + guard_bindings
        + opportunity_bindings
        + recheck_bindings
    )
    scope_rollups, family_rollups, market_rollups = build_rollups(runtime_rows, all_binding_rows, market_bindings, generated_at, manifest_hash)

    distributions = {
        "candidate_runtime_component_family": string_counter(runtime_rows, "candidate_runtime_component_family"),
        "candidate_runtime_status": string_counter(runtime_rows, "candidate_runtime_status"),
        "candidate_runtime_self_test_emission": string_counter(self_test_rows, "emitted_observation_class"),
        "scorer_runtime_binding_status": string_counter(scorer_bindings, "component_runtime_binding_status"),
        "source_runtime_binding_status": string_counter(source_bindings, "component_runtime_binding_status"),
        "score_control_runtime_binding_status": string_counter(score_control_bindings, "component_runtime_binding_status"),
        "nofill_runtime_binding_status": string_counter(nofill_bindings, "component_runtime_binding_status"),
        "guard_runtime_binding_status": string_counter(guard_bindings, "component_runtime_binding_status"),
        "opportunity_runtime_binding_status": string_counter(opportunity_bindings, "component_runtime_binding_status"),
        "recheck_runtime_binding_status": string_counter(recheck_bindings, "component_runtime_binding_status"),
        "market_runtime_binding_status": string_counter(market_bindings, "market_runtime_binding_status"),
        "market_runtime_binding_symbol": string_counter(market_bindings, "symbol"),
        "market_runtime_binding_tradability_status": string_counter(market_bindings, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every candidate-system execution row become an event-matchable runtime decision?",
        "Did every runtime decision execute positive scope match and negative scope mismatch self-tests?",
        "Which positive scorer and no-fill challenger rows emit default-off observations?",
        "Which negative no-fill rows emit avoid/inverse or entry-failure observations?",
        "Which source, guard, opportunity, score-control, and recheck components bind to fail-closed or repair contracts?",
        "Which market/timeframe/session/horizon components bind to shadow, replay, proxy/control, repair, or opportunity-preservation roles?",
        "Which runtime rows remain repair/stress/context rather than score-emitting components?",
        "What is the next same-resource execution layer after candidate runtime binding?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by candidate runtime decision, self-test, component binding, market binding, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    split_total = len(all_binding_rows)
    counts = {
        "input_candidate_execution_rows": len(candidate_rows_input),
        "input_market_component_rows": len(market_rows_input),
        "candidate_runtime_decision_rows": len(runtime_rows),
        "candidate_runtime_self_test_rows": len(self_test_rows),
        "scorer_runtime_binding_rows": len(scorer_bindings),
        "source_runtime_binding_rows": len(source_bindings),
        "score_control_runtime_binding_rows": len(score_control_bindings),
        "nofill_runtime_binding_rows": len(nofill_bindings),
        "guard_runtime_binding_rows": len(guard_bindings),
        "current_claim_opportunity_runtime_binding_rows": len(opportunity_bindings),
        "recheck_runtime_binding_rows": len(recheck_bindings),
        "market_runtime_binding_rows": len(market_bindings),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_candidate_rows_consumed = (
        len(runtime_rows) == len(candidate_rows_input) == input_result["counts"]["candidate_execution_rows"]
    )
    all_split_rows_consumed = split_total == input_result["counts"]["candidate_execution_rows"]
    all_market_rows_consumed = (
        len(market_bindings) == len(market_rows_input) == input_result["counts"]["market_component_rows"]
    )
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
        "all_candidate_rows_consumed": all_candidate_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
        "all_runtime_self_tests_executed": all_self_tests_executed,
        "bucket_distributions": distributions,
        "system_decision": {
            "candidate_runtime_component_family_counts": distributions["candidate_runtime_component_family"],
            "candidate_runtime_status_counts": distributions["candidate_runtime_status"],
            "market_runtime_binding_status_counts": distributions["market_runtime_binding_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE_RESULT: execute candidate-system rows as branch-local default-off runtime decisions, bind all component ledgers, and preserve market expansion runtime bindings for the next same-resource execution layer.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_candidate_rows_consumed": all_candidate_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
        "all_runtime_self_tests_executed": all_self_tests_executed,
    }
    write_jsonl(CANDIDATE_RUNTIME_LEDGER, runtime_rows)
    write_jsonl(CANDIDATE_RUNTIME_SELF_TEST_LEDGER, self_test_rows)
    write_jsonl(SCORER_RUNTIME_BINDING_LEDGER, scorer_bindings)
    write_jsonl(SOURCE_RUNTIME_BINDING_LEDGER, source_bindings)
    write_jsonl(SCORE_CONTROL_RUNTIME_BINDING_LEDGER, score_control_bindings)
    write_jsonl(NOFILL_RUNTIME_BINDING_LEDGER, nofill_bindings)
    write_jsonl(GUARD_RUNTIME_BINDING_LEDGER, guard_bindings)
    write_jsonl(OPPORTUNITY_RUNTIME_BINDING_LEDGER, opportunity_bindings)
    write_jsonl(RECHECK_RUNTIME_BINDING_LEDGER, recheck_bindings)
    write_jsonl(MARKET_RUNTIME_BINDING_LEDGER, market_bindings)
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
                "# Branch-Local Unified System Candidate Runtime Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Candidate runtime decision rows: `{counts['candidate_runtime_decision_rows']}`.",
                f"- Candidate runtime self-test rows: `{counts['candidate_runtime_self_test_rows']}`.",
                f"- No-fill runtime binding rows: `{counts['nofill_runtime_binding_rows']}`.",
                f"- Guard runtime binding rows: `{counts['guard_runtime_binding_rows']}`.",
                f"- Market runtime binding rows: `{counts['market_runtime_binding_rows']}`.",
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
        CANDIDATE_RUNTIME_LEDGER,
        CANDIDATE_RUNTIME_SELF_TEST_LEDGER,
        SCORER_RUNTIME_BINDING_LEDGER,
        SOURCE_RUNTIME_BINDING_LEDGER,
        SCORE_CONTROL_RUNTIME_BINDING_LEDGER,
        NOFILL_RUNTIME_BINDING_LEDGER,
        GUARD_RUNTIME_BINDING_LEDGER,
        OPPORTUNITY_RUNTIME_BINDING_LEDGER,
        RECHECK_RUNTIME_BINDING_LEDGER,
        MARKET_RUNTIME_BINDING_LEDGER,
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
