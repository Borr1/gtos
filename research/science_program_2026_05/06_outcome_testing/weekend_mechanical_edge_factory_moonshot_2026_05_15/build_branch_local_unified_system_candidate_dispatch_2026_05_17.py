#!/usr/bin/env python3
"""Consume candidate runtime bindings into concrete branch-local dispatch artifacts."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_dispatch import (
    UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
    candidate_dispatch_decision,
    candidate_dispatch_rollup,
    candidate_dispatch_self_test,
    component_dispatch_plan,
    market_transfer_dispatch,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_CANDIDATE_RUNTIME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_RUNTIME_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_CANDIDATE_RUNTIME_SELF_TEST_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_RUNTIME_SELF_TEST_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_RUNTIME_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_DISPATCH
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CANDIDATE_DISPATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_DISPATCH_DECISION_LEDGER_2026-05-17.jsonl"
CANDIDATE_DISPATCH_SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_DISPATCH_SELF_TEST_LEDGER_2026-05-17.jsonl"
SCORER_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
NOFILL_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
GUARD_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
RECHECK_DISPATCH_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
MARKET_TRANSFER_DISPATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TRANSFER_DISPATCH_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system candidate-dispatch bundle. It consumes every executable candidate-runtime row and "
    "component/market runtime binding into concrete dispatch surfaces: scorer registry materialization, source/control "
    "builder plans, score-with-control plans, no-fill challenger/avoid modules, fail-closed guard bindings, "
    "current-claim opportunity routes, recheck plans, and market/timeframe transfer actions. It does not change live "
    "behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-SRC-{index:04d}",
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
    dispatch_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in dispatch_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("candidate_dispatch_family"),
            )
        ].append(row)
        by_family[(row.get("candidate_dispatch_family"), row.get("candidate_dispatch_status"))].append(row)
    for row in component_rows:
        by_family[(row.get("component_type"), row.get("component_dispatch_plan_status"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_transfer_dispatch_status"))].append(row)
    scope_rollups = [
        with_common(candidate_dispatch_rollup(key, by_scope[key], index, "scope_candidate_dispatch"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(candidate_dispatch_rollup(key, by_family[key], index, "family_candidate_dispatch_or_plan"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(candidate_dispatch_rollup(key, by_market[key], index, "market_transfer_dispatch"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_candidate_dispatch_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_dispatch_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed candidate runtime bindings into scorer/source/control/no-fill/guard/opportunity/recheck/market dispatch artifacts.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_CANDIDATE_RUNTIME_LEDGER,
            INPUT_CANDIDATE_RUNTIME_SELF_TEST_LEDGER,
            INPUT_SCORER_RUNTIME_BINDING_LEDGER,
            INPUT_SOURCE_RUNTIME_BINDING_LEDGER,
            INPUT_SCORE_CONTROL_RUNTIME_BINDING_LEDGER,
            INPUT_NOFILL_RUNTIME_BINDING_LEDGER,
            INPUT_GUARD_RUNTIME_BINDING_LEDGER,
            INPUT_OPPORTUNITY_RUNTIME_BINDING_LEDGER,
            INPUT_RECHECK_RUNTIME_BINDING_LEDGER,
            INPUT_MARKET_RUNTIME_BINDING_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    candidate_runtime_input = read_jsonl(INPUT_CANDIDATE_RUNTIME_LEDGER)
    scorer_input = read_jsonl(INPUT_SCORER_RUNTIME_BINDING_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_RUNTIME_BINDING_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_RUNTIME_BINDING_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_RUNTIME_BINDING_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_RUNTIME_BINDING_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_RUNTIME_BINDING_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_RUNTIME_BINDING_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_RUNTIME_BINDING_LEDGER)

    dispatch_rows = [
        with_common(candidate_dispatch_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(candidate_runtime_input, 1)
    ]
    self_test_rows = [
        with_common(candidate_dispatch_self_test(row, index), generated_at, manifest_hash)
        for index, row in enumerate(dispatch_rows, 1)
    ]
    scorer_dispatch = [
        with_common(component_dispatch_plan(row, index, "SCORER"), generated_at, manifest_hash)
        for index, row in enumerate(scorer_input, 1)
    ]
    source_dispatch = [
        with_common(component_dispatch_plan(row, index, "SOURCE"), generated_at, manifest_hash)
        for index, row in enumerate(source_input, 1)
    ]
    score_control_dispatch = [
        with_common(component_dispatch_plan(row, index, "SCORE_CONTROL"), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_dispatch = [
        with_common(component_dispatch_plan(row, index, "NOFILL"), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_dispatch = [
        with_common(component_dispatch_plan(row, index, "GUARD"), generated_at, manifest_hash)
        for index, row in enumerate(guard_input, 1)
    ]
    opportunity_dispatch = [
        with_common(component_dispatch_plan(row, index, "OPPORTUNITY"), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_input, 1)
    ]
    recheck_dispatch = [
        with_common(component_dispatch_plan(row, index, "RECHECK"), generated_at, manifest_hash)
        for index, row in enumerate(recheck_input, 1)
    ]
    market_dispatch = [
        with_common(market_transfer_dispatch(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_input, 1)
    ]
    all_component_dispatch = (
        scorer_dispatch
        + source_dispatch
        + score_control_dispatch
        + nofill_dispatch
        + guard_dispatch
        + opportunity_dispatch
        + recheck_dispatch
    )
    scope_rollups, family_rollups, market_rollups = build_rollups(
        dispatch_rows, all_component_dispatch, market_dispatch, generated_at, manifest_hash
    )

    distributions = {
        "candidate_dispatch_family": string_counter(dispatch_rows, "candidate_dispatch_family"),
        "candidate_dispatch_status": string_counter(dispatch_rows, "candidate_dispatch_status"),
        "candidate_dispatch_self_test_execution_class": string_counter(self_test_rows, "executed_dispatch_class"),
        "scorer_dispatch_plan_status": string_counter(scorer_dispatch, "component_dispatch_plan_status"),
        "source_control_dispatch_plan_status": string_counter(source_dispatch, "component_dispatch_plan_status"),
        "score_control_dispatch_plan_status": string_counter(score_control_dispatch, "component_dispatch_plan_status"),
        "nofill_dispatch_plan_status": string_counter(nofill_dispatch, "component_dispatch_plan_status"),
        "guard_dispatch_plan_status": string_counter(guard_dispatch, "component_dispatch_plan_status"),
        "opportunity_dispatch_plan_status": string_counter(opportunity_dispatch, "component_dispatch_plan_status"),
        "recheck_dispatch_plan_status": string_counter(recheck_dispatch, "component_dispatch_plan_status"),
        "market_transfer_dispatch_status": string_counter(market_dispatch, "market_transfer_dispatch_status"),
        "market_transfer_dispatch_symbol": string_counter(market_dispatch, "symbol"),
        "market_transfer_dispatch_tradability_status": string_counter(market_dispatch, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every candidate runtime row become a concrete scorer/source/control/no-fill/guard/opportunity/recheck dispatch decision?",
        "Did every dispatch decision execute positive scope match and negative mismatch behavior?",
        "Which positive scorer rows materialize default-off branch-local scorer registrations?",
        "Which positive no-fill rows materialize challenger comparators against status quo?",
        "Which negative no-fill rows become avoid/inverse or entry-failure modules instead of discarded claims?",
        "Which source/control required rows become builder plans with source hashes and missing-source proofs?",
        "Which guard rows become fail-closed registry bindings before any score use?",
        "Which market/timeframe/session/horizon rows dispatch to shadow, replay, proxy/control, repair, or preserved-opportunity actions?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by candidate dispatch, self-test, component plan, market dispatch, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    split_total = len(all_component_dispatch)
    counts = {
        "input_candidate_runtime_rows": len(candidate_runtime_input),
        "input_market_runtime_binding_rows": len(market_input),
        "candidate_dispatch_decision_rows": len(dispatch_rows),
        "candidate_dispatch_self_test_rows": len(self_test_rows),
        "scorer_dispatch_plan_rows": len(scorer_dispatch),
        "source_control_dispatch_plan_rows": len(source_dispatch),
        "score_control_dispatch_plan_rows": len(score_control_dispatch),
        "nofill_dispatch_plan_rows": len(nofill_dispatch),
        "guard_dispatch_plan_rows": len(guard_dispatch),
        "current_claim_opportunity_dispatch_plan_rows": len(opportunity_dispatch),
        "recheck_dispatch_plan_rows": len(recheck_dispatch),
        "market_transfer_dispatch_rows": len(market_dispatch),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_candidate_runtime_rows_consumed = (
        len(dispatch_rows) == len(candidate_runtime_input) == input_result["counts"]["candidate_runtime_decision_rows"]
    )
    all_component_runtime_rows_consumed = split_total == input_result["counts"]["candidate_runtime_decision_rows"]
    all_market_runtime_rows_consumed = (
        len(market_dispatch) == len(market_input) == input_result["counts"]["market_runtime_binding_rows"]
    )
    all_dispatch_self_tests_executed = len(self_test_rows) == len(dispatch_rows) and all(
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
        "all_candidate_runtime_rows_consumed": all_candidate_runtime_rows_consumed,
        "all_component_runtime_rows_consumed": all_component_runtime_rows_consumed,
        "all_market_runtime_rows_consumed": all_market_runtime_rows_consumed,
        "all_dispatch_self_tests_executed": all_dispatch_self_tests_executed,
        "bucket_distributions": distributions,
        "system_decision": {
            "candidate_dispatch_family_counts": distributions["candidate_dispatch_family"],
            "candidate_dispatch_status_counts": distributions["candidate_dispatch_status"],
            "market_transfer_dispatch_status_counts": distributions["market_transfer_dispatch_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_RESULT: materialize executable candidate runtime bindings into branch-local scorer/source/control/no-fill/guard/opportunity/recheck/market dispatch surfaces and continue same-resource execution.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_candidate_runtime_rows_consumed": all_candidate_runtime_rows_consumed,
        "all_component_runtime_rows_consumed": all_component_runtime_rows_consumed,
        "all_market_runtime_rows_consumed": all_market_runtime_rows_consumed,
        "all_dispatch_self_tests_executed": all_dispatch_self_tests_executed,
    }
    write_jsonl(CANDIDATE_DISPATCH_LEDGER, dispatch_rows)
    write_jsonl(CANDIDATE_DISPATCH_SELF_TEST_LEDGER, self_test_rows)
    write_jsonl(SCORER_DISPATCH_PLAN_LEDGER, scorer_dispatch)
    write_jsonl(SOURCE_CONTROL_DISPATCH_PLAN_LEDGER, source_dispatch)
    write_jsonl(SCORE_CONTROL_DISPATCH_PLAN_LEDGER, score_control_dispatch)
    write_jsonl(NOFILL_DISPATCH_PLAN_LEDGER, nofill_dispatch)
    write_jsonl(GUARD_DISPATCH_PLAN_LEDGER, guard_dispatch)
    write_jsonl(OPPORTUNITY_DISPATCH_PLAN_LEDGER, opportunity_dispatch)
    write_jsonl(RECHECK_DISPATCH_PLAN_LEDGER, recheck_dispatch)
    write_jsonl(MARKET_TRANSFER_DISPATCH_LEDGER, market_dispatch)
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
                "# Branch-Local Unified System Candidate Dispatch Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Candidate dispatch decision rows: `{counts['candidate_dispatch_decision_rows']}`.",
                f"- Candidate dispatch self-test rows: `{counts['candidate_dispatch_self_test_rows']}`.",
                f"- No-fill dispatch plan rows: `{counts['nofill_dispatch_plan_rows']}`.",
                f"- Guard dispatch plan rows: `{counts['guard_dispatch_plan_rows']}`.",
                f"- Market transfer dispatch rows: `{counts['market_transfer_dispatch_rows']}`.",
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
        CANDIDATE_DISPATCH_LEDGER,
        CANDIDATE_DISPATCH_SELF_TEST_LEDGER,
        SCORER_DISPATCH_PLAN_LEDGER,
        SOURCE_CONTROL_DISPATCH_PLAN_LEDGER,
        SCORE_CONTROL_DISPATCH_PLAN_LEDGER,
        NOFILL_DISPATCH_PLAN_LEDGER,
        GUARD_DISPATCH_PLAN_LEDGER,
        OPPORTUNITY_DISPATCH_PLAN_LEDGER,
        RECHECK_DISPATCH_PLAN_LEDGER,
        MARKET_TRANSFER_DISPATCH_LEDGER,
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
