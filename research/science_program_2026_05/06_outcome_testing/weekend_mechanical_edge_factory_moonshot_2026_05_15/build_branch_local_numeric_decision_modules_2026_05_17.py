#!/usr/bin/env python3
"""Build executable numeric decision modules from numeric result rows."""

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

from src.research_infra.moonshot_numeric_decision_modules import (
    NUMERIC_DECISION_MODULE_SURFACE,
    avoid_inverse_filter_spec,
    execute_numeric_module_event,
    module_record_from_numeric_result,
    source_geometry_repair_spec,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_DECISION_MODULES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_NUMERIC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_GEOMETRY_REPAIR_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / NUMERIC_DECISION_MODULE_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_NUMERIC_DECISION_MODULE_LEDGER_2026-05-17.jsonl"
SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_MODULE_LEDGER_2026-05-17.jsonl"
AVOID_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_FILTER_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GEOMETRY_REPAIR_SPEC_LEDGER_2026-05-17.jsonl"
CONTEXT_STRESS_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTEXT_STRESS_MODULE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_HORIZON_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local numeric decision modules. This packet consumes the numeric result ledger into executable research-only "
    "module records, scorer modules, avoid/inverse filters, source-geometry repair specs, context/stress modules, and "
    "per-row executable self-tests. It writes runnable module references and does not change live behavior, place orders, "
    "or claim live readiness."
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
                "source_manifest_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
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


def matching_event(module: dict[str, Any]) -> dict[str, Any]:
    return {
        "numeric_scope_key": module.get("numeric_scope_key"),
        "symbol": module.get("symbol"),
        "route_session": module.get("route_session"),
        "horizon_id": module.get("horizon_id"),
        "primitive_flag": module.get("primitive_flag"),
        "source_component": module.get("source_component"),
        "event_probe": "matching_scope_probe",
    }


def mismatch_event(module: dict[str, Any]) -> dict[str, Any]:
    return {
        "numeric_scope_key": f"mismatch::{module.get('numeric_scope_key')}",
        "symbol": f"mismatch::{module.get('symbol')}",
        "route_session": module.get("route_session"),
        "horizon_id": module.get("horizon_id"),
        "primitive_flag": module.get("primitive_flag"),
        "source_component": module.get("source_component"),
        "event_probe": "mismatching_scope_probe",
    }


def self_test_row(module: dict[str, Any], index: int) -> dict[str, Any]:
    matched = execute_numeric_module_event(matching_event(module), module)
    mismatched = execute_numeric_module_event(mismatch_event(module), module)
    return {
        "numeric_decision_module_self_test_row_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-SELF-TEST-{index:06d}",
        "input_numeric_decision_module_row_id": module.get("numeric_decision_module_row_id"),
        "input_numeric_result_row_id": module.get("input_numeric_result_row_id"),
        "numeric_module_key": module.get("numeric_module_key"),
        "numeric_module_role": module.get("numeric_module_role"),
        "match_event_status": matched.get("numeric_module_event_status"),
        "match_event_score": matched.get("numeric_module_event_score"),
        "match_avoid_inverse_filter_emitted": matched.get("avoid_inverse_filter_emitted"),
        "match_source_geometry_repair_action": matched.get("source_geometry_repair_action"),
        "mismatch_event_status": mismatched.get("numeric_module_event_status"),
        "mismatch_event_score": mismatched.get("numeric_module_event_score"),
        "mismatch_avoid_inverse_filter_emitted": mismatched.get("avoid_inverse_filter_emitted"),
        "mismatch_source_geometry_repair_action": mismatched.get("source_geometry_repair_action"),
        "match_event_passed": matched.get("event_match") is True,
        "mismatch_event_passed": mismatched.get("event_match") is False,
        "self_test_passed": matched.get("event_match") is True and mismatched.get("event_match") is False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "summary_only_terminal": False,
    }


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def rollup_rows(modules: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in modules:
        groups[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("numeric_module_role"))].append(row)
    output = []
    for index, key in enumerate(sorted(groups, key=lambda item: tuple(str(part) for part in item)), 1):
        rows = groups[key]
        score_values = [row.get("decision_proxy_value") for row in rows if isinstance(row.get("decision_proxy_value"), (int, float))]
        output.append(
            with_common(
                {
                    "numeric_decision_module_rollup_row_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-ROLLUP-{index:05d}",
                    "symbol": key[0],
                    "route_session": key[1],
                    "horizon_id": key[2],
                    "numeric_module_role": key[3],
                    "row_count": len(rows),
                    "score_value_count": len(score_values),
                    "score_mean": round(sum(score_values) / len(score_values), 10) if score_values else None,
                    "score_min": min(score_values) if score_values else None,
                    "score_max": max(score_values) if score_values else None,
                    "decision_counts": string_counter(rows, "keep_kill_redesign_implement_decision"),
                    "status_counts": string_counter(rows, "numeric_module_status"),
                    "runtime_score_allowed": False,
                    "unconditional_scalar_use_allowed": False,
                    "candidate_use_allowed_now": False,
                    "summary_only_terminal": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def bucket_rows(
    modules: list[dict[str, Any]],
    source_specs: list[dict[str, Any]],
    avoid_specs: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    specs = [
        ("numeric_module_role", modules, "numeric_module_role"),
        ("numeric_module_status", modules, "numeric_module_status"),
        ("decision", modules, "keep_kill_redesign_implement_decision"),
        ("proxy_r_class", modules, "proxy_r_class"),
        ("target_stop_order_class", modules, "target_stop_order_class"),
        ("source_geometry_repair_action", modules, "source_geometry_repair_action"),
        ("avoid_inverse_filter_action", avoid_specs, "filter_action"),
        ("source_repair_spec_action", source_specs, "repair_action"),
        ("match_event_status", self_tests, "match_event_status"),
        ("mismatch_event_status", self_tests, "mismatch_event_status"),
        ("self_test_passed", self_tests, "self_test_passed"),
    ]
    output = []
    for bucket_name, rows, key in specs:
        for value, count in string_counter(rows, key).items():
            output.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-BUCKET-{len(output) + 1:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output


def question_rows(counts: dict[str, Any], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    questions = [
        (
            "scorer_module_default_off_shadow",
            "Which positive/default-off modules should be wired into the branch-local research scorer registry first?",
            "consume SCORER_MODULE_LEDGER rows into default-off registry specs with exact source/control guards",
        ),
        (
            "avoid_inverse_filter_application",
            "Which strong-negative proxy rows produce avoid/inverse filter emissions under exact scope match?",
            "consume AVOID_INVERSE_FILTER_LEDGER rows into failure-feature and avoid-rule comparators",
        ),
        (
            "source_geometry_repair_execution",
            "Which missing geometry/source rows can be repaired from same-resource source joins before exact R?",
            "execute SOURCE_GEOMETRY_REPAIR_SPEC_LEDGER rows against source/control builders",
        ),
        (
            "context_stress_guard_merge",
            "Which context/stress modules should become guard inputs rather than scalar scorers?",
            "merge CONTEXT_STRESS_MODULE_LEDGER rows into guard-bound context features",
        ),
    ]
    return [
        with_common(
            {
                "numeric_decision_module_question_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-Q-{index:04d}",
                "question_key": key,
                "question": question,
                "next_action": next_action,
                "current_counts": counts,
            },
            generated_at,
            manifest_hash,
        )
        for index, (key, question, next_action) in enumerate(questions, 1)
    ]


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_numeric_decision_modules"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    event = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "branch_local_numeric_decision_modules_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed numeric result rows into executable default-off scorer, avoid/inverse, repair, and context/stress modules with per-row self-tests.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch-Local Numeric Decision Modules",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Module Role Counts", ""])
    for role, count in result["bucket_distributions"]["numeric_module_role"].items():
        lines.append(f"- `{role}`: `{count}`")
    lines.extend(
        [
            "",
            "## Immediate Consumption",
            "",
            "The module ledgers are executable against `src.research_infra.moonshot_numeric_decision_modules.execute_numeric_module_event`; the self-test ledger records one matching and one mismatching probe for every numeric row.",
            "",
        ]
    )
    write_text(SUMMARY_PATH, "\n".join(lines))


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_NUMERIC_LEDGER,
            INPUT_SOURCE_REPAIR_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    numeric_rows = read_jsonl(INPUT_NUMERIC_LEDGER)
    source_repair_input_ids = {str(row.get("input_numeric_result_row_id")) for row in read_jsonl(INPUT_SOURCE_REPAIR_LEDGER)}

    module_rows = [
        with_common(module_record_from_numeric_result(row, index), generated_at, manifest_hash)
        for index, row in enumerate(numeric_rows, 1)
    ]
    modules_by_numeric_id = {str(row.get("input_numeric_result_row_id")): row for row in module_rows}
    scorer_rows = [
        row
        for row in module_rows
        if row.get("numeric_module_role")
        in {"DEFAULT_OFF_NUMERIC_SCORER_MODULE", "DEFAULT_OFF_PROXY_CHALLENGER_SCORER_MODULE"}
    ]
    avoid_rows = [row for row in module_rows if row.get("numeric_module_role") == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE"]
    source_spec_rows = [
        with_common(source_geometry_repair_spec(numeric_row, index), generated_at, manifest_hash)
        for index, numeric_row in enumerate(
            [row for row in numeric_rows if str(row.get("numeric_result_row_id")) in source_repair_input_ids],
            1,
        )
    ]
    avoid_spec_rows = [
        with_common(avoid_inverse_filter_spec(numeric_rows_by_id, index), generated_at, manifest_hash)
        for index, numeric_rows_by_id in enumerate(
            [row for row in numeric_rows if modules_by_numeric_id[str(row.get("numeric_result_row_id"))].get("numeric_module_role") == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE"],
            1,
        )
    ]
    context_rows = [
        row
        for row in module_rows
        if row.get("numeric_module_role") in {"CONTEXT_STRESS_OR_REDESIGN_MODULE", "RECHECK_NUMERIC_DECISION_MODULE"}
    ]
    self_tests = [with_common(self_test_row(row, index), generated_at, manifest_hash) for index, row in enumerate(module_rows, 1)]
    rollups = rollup_rows(module_rows, generated_at, manifest_hash)
    buckets = bucket_rows(module_rows, source_spec_rows, avoid_spec_rows, self_tests, generated_at, manifest_hash)

    counts = {
        "input_numeric_result_rows": len(numeric_rows),
        "input_source_geometry_repair_rows": len(source_repair_input_ids),
        "numeric_decision_module_rows": len(module_rows),
        "scorer_module_rows": len(scorer_rows),
        "avoid_inverse_filter_rows": len(avoid_spec_rows),
        "source_geometry_repair_spec_rows": len(source_spec_rows),
        "context_stress_module_rows": len(context_rows),
        "self_test_rows": len(self_tests),
        "self_test_pass_rows": sum(1 for row in self_tests if row.get("self_test_passed") is True),
        "symbol_session_horizon_rollup_rows": len(rollups),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_rows),
    }
    distributions = {
        "numeric_module_role": string_counter(module_rows, "numeric_module_role"),
        "numeric_module_status": string_counter(module_rows, "numeric_module_status"),
        "decision": string_counter(module_rows, "keep_kill_redesign_implement_decision"),
        "proxy_r_class": string_counter(module_rows, "proxy_r_class"),
        "target_stop_order_class": string_counter(module_rows, "target_stop_order_class"),
        "source_geometry_repair_action": string_counter(module_rows, "source_geometry_repair_action"),
        "avoid_inverse_filter_action": string_counter(avoid_spec_rows, "filter_action"),
        "source_repair_spec_action": string_counter(source_spec_rows, "repair_action"),
        "match_event_status": string_counter(self_tests, "match_event_status"),
        "mismatch_event_status": string_counter(self_tests, "mismatch_event_status"),
        "self_test_passed": string_counter(self_tests, "self_test_passed"),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "counts": counts,
        "bucket_distributions": distributions,
        "input_numeric_result_rows_consumed": counts["numeric_decision_module_rows"] == input_result["counts"]["numeric_result_rows"],
        "all_module_rows_have_executable_callable": all(
            row.get("event_callable_name") == "execute_numeric_module_event" for row in module_rows
        ),
        "all_self_tests_passed": counts["self_test_rows"] == counts["self_test_pass_rows"],
        "source_repair_specs_cover_prior_repair_rows": counts["source_geometry_repair_spec_rows"]
        == input_result["counts"]["source_geometry_repair_rows"],
        "avoid_specs_cover_strong_negative_rows": counts["avoid_inverse_filter_rows"]
        == distributions["numeric_module_role"].get("AVOID_INVERSE_OR_FAILURE_FILTER_MODULE", 0),
        "no_summary_only_terminal_rows": all(row.get("summary_only_terminal") is False for row in module_rows + self_tests),
        "output_files": {
            "numeric_decision_module_ledger": MODULE_LEDGER.relative_to(REPO).as_posix(),
            "scorer_module_ledger": SCORER_LEDGER.relative_to(REPO).as_posix(),
            "avoid_inverse_filter_ledger": AVOID_LEDGER.relative_to(REPO).as_posix(),
            "source_geometry_repair_spec_ledger": SOURCE_REPAIR_SPEC_LEDGER.relative_to(REPO).as_posix(),
            "context_stress_module_ledger": CONTEXT_STRESS_LEDGER.relative_to(REPO).as_posix(),
            "self_test_ledger": SELF_TEST_LEDGER.relative_to(REPO).as_posix(),
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "module_registration_callable": "module_record_from_numeric_result",
        "event_execution_callable": "execute_numeric_module_event",
        "repair_spec_callable": "source_geometry_repair_spec",
        "avoid_inverse_spec_callable": "avoid_inverse_filter_spec",
        "input": {
            "numeric_result_ledger": INPUT_NUMERIC_LEDGER.relative_to(REPO).as_posix(),
            "source_geometry_repair_ledger": INPUT_SOURCE_REPAIR_LEDGER.relative_to(REPO).as_posix(),
        },
        "output": result["output_files"],
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
    questions = question_rows(counts, generated_at, manifest_hash)
    outputs = [
        RESULT_PATH,
        RUNTIME_SPEC_PATH,
        MODULE_LEDGER,
        SCORER_LEDGER,
        AVOID_LEDGER,
        SOURCE_REPAIR_SPEC_LEDGER,
        CONTEXT_STRESS_LEDGER,
        SELF_TEST_LEDGER,
        SYMBOL_SESSION_HORIZON_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_jsonl(MODULE_LEDGER, module_rows)
    write_jsonl(SCORER_LEDGER, scorer_rows)
    write_jsonl(AVOID_LEDGER, avoid_spec_rows)
    write_jsonl(SOURCE_REPAIR_SPEC_LEDGER, source_spec_rows)
    write_jsonl(CONTEXT_STRESS_LEDGER, context_rows)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(SYMBOL_SESSION_HORIZON_ROLLUP_LEDGER, rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(result)
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
