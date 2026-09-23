#!/usr/bin/env python3
"""Consume implementation-execution decisions into executable branch-local artifacts."""

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

from src.research_infra.moonshot_branch_local_unified_system_executable_artifacts import (
    UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
    code_surface_artifact,
    current_claim_opportunity_route,
    executable_artifact_decision,
    executable_artifact_rollup,
    guard_binding_execution,
    market_source_action,
    nofill_comparator_outcome,
    recheck_execution_artifact,
    score_control_comparison_artifact,
    source_control_builder_execution,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXECUTION_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_MODULE_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DEFAULT_OFF_MODULE_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_BUILDER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_BUILDER_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_COMPARATOR_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_VARIANT_COMPARATOR_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_BINDING_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_BINDING_LEDGER_2026-05-17.jsonl"
INPUT_AUDIT_ROUTE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_AUDIT_ROUTE_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_TRANSFER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_TIMEFRAME_TRANSFER_DECISION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXECUTABLE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_ARTIFACT_DECISION_LEDGER_2026-05-17.jsonl"
CODE_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_SURFACE_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_BUILDER_EXECUTION_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_COMPARISON_LEDGER_2026-05-17.jsonl"
NOFILL_OUTCOME_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPARATOR_OUTCOME_LEDGER_2026-05-17.jsonl"
GUARD_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_BINDING_EXECUTION_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_ROUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_ROUTE_LEDGER_2026-05-17.jsonl"
RECHECK_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_EXECUTION_LEDGER_2026-05-17.jsonl"
MARKET_SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_SOURCE_ACTION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system executable-artifacts bundle. It consumes every implementation-execution row into "
    "a concrete code surface, source/control builder execution, score-control comparator, no-fill comparator outcome, "
    "guard binding execution, current-claim opportunity route, or recheck artifact, and consumes every market-transfer "
    "row into a source/proxy/control action. It does not change live behavior, place orders, or claim broker R/PnL, "
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-EXECUTABLE-SRC-{index:04d}",
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
    executable_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in executable_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("executable_artifact_family"),
            )
        ].append(row)
        by_family[(row.get("executable_artifact_family"), row.get("executable_artifact_status"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_source_action_status"))].append(row)
    scope_rollups = [
        with_common(executable_artifact_rollup(key, by_scope[key], index, "scope_executable_artifact"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(executable_artifact_rollup(key, by_family[key], index, "family_executable_artifact"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(executable_artifact_rollup(key, by_market[key], index, "market_source_action"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_executable_artifacts_bundle"] = {
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
        "event": "branch_local_unified_system_executable_artifacts_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed implementation-execution rows into code, source/control, no-fill, guard, score-control, audit, recheck, and market source-action artifacts.",
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
            INPUT_MODULE_SPEC_LEDGER,
            INPUT_SOURCE_BUILDER_LEDGER,
            INPUT_SCORE_CONTROL_LEDGER,
            INPUT_NOFILL_COMPARATOR_LEDGER,
            INPUT_GUARD_BINDING_LEDGER,
            INPUT_AUDIT_ROUTE_LEDGER,
            INPUT_MARKET_TRANSFER_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    execution_rows = read_jsonl(INPUT_EXECUTION_LEDGER)
    module_specs = read_jsonl(INPUT_MODULE_SPEC_LEDGER)
    source_builders = read_jsonl(INPUT_SOURCE_BUILDER_LEDGER)
    score_controls = read_jsonl(INPUT_SCORE_CONTROL_LEDGER)
    nofill_comparators = read_jsonl(INPUT_NOFILL_COMPARATOR_LEDGER)
    guard_bindings = read_jsonl(INPUT_GUARD_BINDING_LEDGER)
    audit_routes = read_jsonl(INPUT_AUDIT_ROUTE_LEDGER)
    market_transfers = read_jsonl(INPUT_MARKET_TRANSFER_LEDGER)

    executable_rows = [
        with_common(executable_artifact_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(execution_rows, 1)
    ]
    code_surfaces = [
        with_common(code_surface_artifact(row, index), generated_at, manifest_hash)
        for index, row in enumerate(module_specs, 1)
    ]
    source_control_rows = [
        with_common(source_control_builder_execution(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_builders, 1)
    ]
    score_comparisons = [
        with_common(score_control_comparison_artifact(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_controls, 1)
    ]
    nofill_outcomes = [
        with_common(nofill_comparator_outcome(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_comparators, 1)
    ]
    guard_executions = [
        with_common(guard_binding_execution(row, index), generated_at, manifest_hash)
        for index, row in enumerate(guard_bindings, 1)
    ]
    opportunity_routes = [
        with_common(current_claim_opportunity_route(row, index), generated_at, manifest_hash)
        for index, row in enumerate(audit_routes, 1)
    ]
    recheck_source_rows = [row for row in execution_rows if row.get("execution_decision_class") == "RECHECK_ROUTE"]
    recheck_rows = [
        with_common(recheck_execution_artifact(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_source_rows, 1)
    ]
    market_actions = [
        with_common(market_source_action(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_transfers, 1)
    ]
    scope_rollups, family_rollups, market_rollups = build_rollups(executable_rows, market_actions, generated_at, manifest_hash)

    distributions = {
        "executable_artifact_family": string_counter(executable_rows, "executable_artifact_family"),
        "executable_artifact_status": string_counter(executable_rows, "executable_artifact_status"),
        "code_surface_status": string_counter(code_surfaces, "code_surface_status"),
        "source_control_builder_execution_status": string_counter(source_control_rows, "source_control_builder_execution_status"),
        "score_control_comparison_status": string_counter(score_comparisons, "score_control_comparison_status"),
        "nofill_comparator_outcome_status": string_counter(nofill_outcomes, "nofill_comparator_outcome_status"),
        "guard_binding_execution_status": string_counter(guard_executions, "guard_binding_execution_status"),
        "opportunity_route_status": string_counter(opportunity_routes, "opportunity_route_status"),
        "recheck_execution_status": string_counter(recheck_rows, "recheck_execution_status"),
        "market_source_action_status": string_counter(market_actions, "market_source_action_status"),
        "market_source_symbol": string_counter(market_actions, "symbol"),
        "market_source_tradability_status": string_counter(market_actions, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-EXECUTABLE-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every implementation-execution row become a concrete executable artifact row?",
        "Which default-off module specs now have branch-local code-surface contracts?",
        "Which source/control builders are executable from current same-resource evidence versus source/proxy repair?",
        "Which no-fill comparator outcomes become positive challengers, avoid/inverse roles, stress rows, or replay/source repairs?",
        "Which guard bindings are attached before score or variant use?",
        "Which score-with-control rows compare now versus require source/control repair?",
        "Which current-claim rejections are preserved as opportunity routes?",
        "Which market/timeframe/session/horizon rows become source/proxy/control actions?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-EXECUTABLE-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by executable artifact, code surface, source/control, score-control, no-fill, guard, opportunity, recheck, market-action, rollup, and bucket ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    split_total = (
        len(code_surfaces)
        + len(source_control_rows)
        + len(score_comparisons)
        + len(nofill_outcomes)
        + len(guard_executions)
        + len(opportunity_routes)
        + len(recheck_rows)
    )
    counts = {
        "input_implementation_execution_rows": len(execution_rows),
        "input_market_transfer_rows": len(market_transfers),
        "executable_artifact_decision_rows": len(executable_rows),
        "code_surface_rows": len(code_surfaces),
        "source_control_builder_execution_rows": len(source_control_rows),
        "score_control_comparison_rows": len(score_comparisons),
        "nofill_comparator_outcome_rows": len(nofill_outcomes),
        "guard_binding_execution_rows": len(guard_executions),
        "current_claim_opportunity_route_rows": len(opportunity_routes),
        "recheck_execution_rows": len(recheck_rows),
        "market_source_action_rows": len(market_actions),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_rows_consumed = len(executable_rows) == len(execution_rows) == input_result["counts"]["execution_decision_rows"]
    all_split_rows_consumed = split_total == len(execution_rows)
    all_market_rows_consumed = len(market_actions) == len(market_transfers) == input_result["counts"]["market_transfer_decision_rows"]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_implementation_rows_consumed": all_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_transfer_rows_consumed": all_market_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "executable_artifact_family_counts": distributions["executable_artifact_family"],
            "market_source_action_status_counts": distributions["market_source_action_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_BUNDLE_RESULT: execute code surfaces, source/control builders, no-fill comparator outcomes, score-control comparisons, guard bindings, opportunity routes, rechecks, and market source actions into branch-local scorer/source/replay implementation.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_implementation_rows_consumed": all_rows_consumed,
        "all_split_rows_consumed": all_split_rows_consumed,
        "all_market_transfer_rows_consumed": all_market_rows_consumed,
    }
    write_jsonl(EXECUTABLE_DECISION_LEDGER, executable_rows)
    write_jsonl(CODE_SURFACE_LEDGER, code_surfaces)
    write_jsonl(SOURCE_CONTROL_LEDGER, source_control_rows)
    write_jsonl(SCORE_CONTROL_COMPARISON_LEDGER, score_comparisons)
    write_jsonl(NOFILL_OUTCOME_LEDGER, nofill_outcomes)
    write_jsonl(GUARD_EXECUTION_LEDGER, guard_executions)
    write_jsonl(OPPORTUNITY_ROUTE_LEDGER, opportunity_routes)
    write_jsonl(RECHECK_EXECUTION_LEDGER, recheck_rows)
    write_jsonl(MARKET_SOURCE_ACTION_LEDGER, market_actions)
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
                "# Branch-Local Unified System Executable Artifacts Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Executable artifact decision rows: `{counts['executable_artifact_decision_rows']}`.",
                f"- Code surface rows: `{counts['code_surface_rows']}`.",
                f"- Source/control builder execution rows: `{counts['source_control_builder_execution_rows']}`.",
                f"- No-fill comparator outcome rows: `{counts['nofill_comparator_outcome_rows']}`.",
                f"- Guard binding execution rows: `{counts['guard_binding_execution_rows']}`.",
                f"- Market source action rows: `{counts['market_source_action_rows']}`.",
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
        EXECUTABLE_DECISION_LEDGER,
        CODE_SURFACE_LEDGER,
        SOURCE_CONTROL_LEDGER,
        SCORE_CONTROL_COMPARISON_LEDGER,
        NOFILL_OUTCOME_LEDGER,
        GUARD_EXECUTION_LEDGER,
        OPPORTUNITY_ROUTE_LEDGER,
        RECHECK_EXECUTION_LEDGER,
        MARKET_SOURCE_ACTION_LEDGER,
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
