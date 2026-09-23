#!/usr/bin/env python3
"""Consume runtime surfaces into branch-local candidate-system synthesis rows."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_synthesis import (
    UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
    candidate_execution_row,
    candidate_system_rollup,
    guard_component_row,
    market_component_row,
    nofill_component_row,
    opportunity_component_row,
    recheck_component_row,
    scorer_component_row,
    score_control_component_row,
    source_component_row,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_RUNTIME_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SURFACE_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_REGISTRY_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPLAY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPLAY_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_RUNTIME_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_REPLAY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_REPLAY_SCORER_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_RUNTIME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_RUNTIME_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_RUNTIME_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RUNTIME_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_RUNTIME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_SOURCE_RUNTIME_LEDGER_2026-05-17.jsonl"
INPUT_SELF_TEST_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SURFACE_SELF_TEST_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CANDIDATE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORER_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_COMPONENT_LEDGER_2026-05-17.jsonl"
SOURCE_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_COMPONENT_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_COMPONENT_LEDGER_2026-05-17.jsonl"
NOFILL_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPONENT_LEDGER_2026-05-17.jsonl"
GUARD_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_COMPONENT_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_COMPONENT_LEDGER_2026-05-17.jsonl"
RECHECK_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_COMPONENT_LEDGER_2026-05-17.jsonl"
MARKET_COMPONENT_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_COMPONENT_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
ROLE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_ROLE_ROLLUP_LEDGER_2026-05-17.jsonl"
MARKET_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system candidate-synthesis bundle. It consumes every runtime surface row into a candidate "
    "execution role, consumes every runtime component ledger into branch-local candidate components, and preserves "
    "all market/source runtime rows. It does not change live behavior, place orders, or claim broker R/PnL, realized "
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SRC-{index:04d}",
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
    candidate_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_role: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("candidate_system_role"),
            )
        ].append(row)
        by_role[(row.get("candidate_system_role"), row.get("candidate_execution_status"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("candidate_component_status"))].append(row)
    scope_rollups = [
        with_common(candidate_system_rollup(key, by_scope[key], index, "scope_candidate_execution"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    role_rollups = [
        with_common(candidate_system_rollup(key, by_role[key], index, "role_candidate_execution"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_role, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(candidate_system_rollup(key, by_market[key], index, "market_candidate_component"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_market, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    return scope_rollups, role_rollups, market_rollups


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_branch_local_unified_system_candidate_synthesis_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_synthesis_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed runtime surfaces into candidate-system execution roles and component ledgers.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_RUNTIME_SURFACE_LEDGER,
            INPUT_SCORER_REGISTRY_LEDGER,
            INPUT_SOURCE_REPLAY_LEDGER,
            INPUT_SCORE_CONTROL_LEDGER,
            INPUT_NOFILL_REPLAY_LEDGER,
            INPUT_GUARD_RUNTIME_LEDGER,
            INPUT_OPPORTUNITY_LEDGER,
            INPUT_RECHECK_LEDGER,
            INPUT_MARKET_RUNTIME_LEDGER,
            INPUT_SELF_TEST_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    runtime_rows = read_jsonl(INPUT_RUNTIME_SURFACE_LEDGER)
    scorer_rows_input = read_jsonl(INPUT_SCORER_REGISTRY_LEDGER)
    source_rows_input = read_jsonl(INPUT_SOURCE_REPLAY_LEDGER)
    score_control_rows_input = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_rows_input = read_jsonl(INPUT_NOFILL_REPLAY_LEDGER)
    guard_rows_input = read_jsonl(INPUT_GUARD_RUNTIME_LEDGER)
    opportunity_rows_input = read_jsonl(INPUT_OPPORTUNITY_LEDGER)
    recheck_rows_input = read_jsonl(INPUT_RECHECK_LEDGER)
    market_rows_input = read_jsonl(INPUT_MARKET_RUNTIME_LEDGER)
    self_test_rows = read_jsonl(INPUT_SELF_TEST_LEDGER)
    self_tests_by_runtime_id = {row.get("input_runtime_surface_decision_row_id"): row for row in self_test_rows}

    candidate_rows = [
        with_common(candidate_execution_row(row, self_tests_by_runtime_id.get(row.get("runtime_surface_decision_row_id")), index), generated_at, manifest_hash)
        for index, row in enumerate(runtime_rows, 1)
    ]
    scorer_rows = [with_common(scorer_component_row(row, index), generated_at, manifest_hash) for index, row in enumerate(scorer_rows_input, 1)]
    source_rows = [with_common(source_component_row(row, index), generated_at, manifest_hash) for index, row in enumerate(source_rows_input, 1)]
    score_control_rows = [
        with_common(score_control_component_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_rows_input, 1)
    ]
    nofill_rows = [with_common(nofill_component_row(row, index), generated_at, manifest_hash) for index, row in enumerate(nofill_rows_input, 1)]
    guard_rows = [with_common(guard_component_row(row, index), generated_at, manifest_hash) for index, row in enumerate(guard_rows_input, 1)]
    opportunity_rows = [
        with_common(opportunity_component_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_rows_input, 1)
    ]
    recheck_rows = [
        with_common(recheck_component_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_rows_input, 1)
    ]
    market_rows = [with_common(market_component_row(row, index), generated_at, manifest_hash) for index, row in enumerate(market_rows_input, 1)]
    scope_rollups, role_rollups, market_rollups = build_rollups(candidate_rows, market_rows, generated_at, manifest_hash)

    distributions = {
        "candidate_system_role": string_counter(candidate_rows, "candidate_system_role"),
        "candidate_execution_status": string_counter(candidate_rows, "candidate_execution_status"),
        "runtime_surface_family": string_counter(candidate_rows, "runtime_surface_family"),
        "scorer_component_status": string_counter(scorer_rows, "candidate_component_status"),
        "source_component_status": string_counter(source_rows, "candidate_component_status"),
        "score_control_component_status": string_counter(score_control_rows, "candidate_component_status"),
        "nofill_component_status": string_counter(nofill_rows, "candidate_component_status"),
        "guard_component_status": string_counter(guard_rows, "candidate_component_status"),
        "opportunity_component_status": string_counter(opportunity_rows, "candidate_component_status"),
        "recheck_component_status": string_counter(recheck_rows, "candidate_component_status"),
        "market_component_status": string_counter(market_rows, "candidate_component_status"),
        "market_component_symbol": string_counter(market_rows, "symbol"),
        "market_component_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every runtime surface become a candidate-system execution role?",
        "Did every runtime split ledger become a branch-local candidate component ledger?",
        "Which candidate roles are scorer, no-fill challenger, avoid/inverse, non-scalar action, or repair/stress/context?",
        "Which scorer and no-fill components are ready default-off versus held for control or repair?",
        "Which source/control components remain exact, replay-attached, proxy/acquisition, or repair routes?",
        "Which guard components enforce fail-closed behavior?",
        "Which current-claim rejection rows preserve opportunity routes?",
        "Which market/source runtime rows become candidate market components?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by candidate execution, component, market, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    split_total = (
        len(scorer_rows)
        + len(source_rows)
        + len(score_control_rows)
        + len(nofill_rows)
        + len(guard_rows)
        + len(opportunity_rows)
        + len(recheck_rows)
    )
    counts = {
        "input_runtime_surface_rows": len(runtime_rows),
        "input_surface_self_test_rows": len(self_test_rows),
        "input_market_source_runtime_rows": len(market_rows_input),
        "candidate_execution_rows": len(candidate_rows),
        "scorer_component_rows": len(scorer_rows),
        "source_component_rows": len(source_rows),
        "score_control_component_rows": len(score_control_rows),
        "nofill_component_rows": len(nofill_rows),
        "guard_component_rows": len(guard_rows),
        "current_claim_opportunity_component_rows": len(opportunity_rows),
        "recheck_component_rows": len(recheck_rows),
        "market_component_rows": len(market_rows),
        "scope_rollup_rows": len(scope_rollups),
        "role_rollup_rows": len(role_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_runtime_rows_consumed = len(candidate_rows) == len(runtime_rows) == input_result["counts"]["runtime_surface_decision_rows"]
    all_split_rows_consumed = split_total == len(runtime_rows)
    all_market_rows_consumed = len(market_rows) == len(market_rows_input) == input_result["counts"]["market_source_runtime_rows"]
    all_self_tests_joined = all(row.get("self_test_row_id") for row in candidate_rows)
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_runtime_rows_consumed": all_runtime_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
        "all_self_tests_joined": all_self_tests_joined,
        "bucket_distributions": distributions,
        "system_decision": {
            "candidate_system_role_counts": distributions["candidate_system_role"],
            "candidate_execution_status_counts": distributions["candidate_execution_status"],
            "market_component_status_counts": distributions["market_component_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_RESULT: assemble default-off branch-local candidate system components from scorer, source/replay, no-fill, guard, opportunity, recheck, and market expansion runtime surfaces.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_runtime_rows_consumed": all_runtime_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_rows_consumed": all_market_rows_consumed,
        "all_self_tests_joined": all_self_tests_joined,
    }
    write_jsonl(CANDIDATE_EXECUTION_LEDGER, candidate_rows)
    write_jsonl(SCORER_COMPONENT_LEDGER, scorer_rows)
    write_jsonl(SOURCE_COMPONENT_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_COMPONENT_LEDGER, score_control_rows)
    write_jsonl(NOFILL_COMPONENT_LEDGER, nofill_rows)
    write_jsonl(GUARD_COMPONENT_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_COMPONENT_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_COMPONENT_LEDGER, recheck_rows)
    write_jsonl(MARKET_COMPONENT_LEDGER, market_rows)
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(ROLE_ROLLUP_LEDGER, role_rollups)
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
                "# Branch-Local Unified System Candidate Synthesis Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Candidate execution rows: `{counts['candidate_execution_rows']}`.",
                f"- Scorer component rows: `{counts['scorer_component_rows']}`.",
                f"- Source component rows: `{counts['source_component_rows']}`.",
                f"- No-fill component rows: `{counts['nofill_component_rows']}`.",
                f"- Guard component rows: `{counts['guard_component_rows']}`.",
                f"- Market component rows: `{counts['market_component_rows']}`.",
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
        CANDIDATE_EXECUTION_LEDGER,
        SCORER_COMPONENT_LEDGER,
        SOURCE_COMPONENT_LEDGER,
        SCORE_CONTROL_COMPONENT_LEDGER,
        NOFILL_COMPONENT_LEDGER,
        GUARD_COMPONENT_LEDGER,
        OPPORTUNITY_COMPONENT_LEDGER,
        RECHECK_COMPONENT_LEDGER,
        MARKET_COMPONENT_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        ROLE_ROLLUP_LEDGER,
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
