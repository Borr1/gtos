#!/usr/bin/env python3
"""Apply numeric decision modules to all numeric result rows."""

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

from src.research_infra.moonshot_numeric_module_registry_router import (
    NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
    build_numeric_module_registry,
    event_from_numeric_result,
    route_numeric_event,
    router_application_row,
    scope_router_decision,
    source_repair_execution_row,
)


NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES"
MODULE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_DECISION_MODULES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_MODULE_ROUTER_APPLICATION"

INPUT_NUMERIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_MODULE_RESULT = ROUTE_DIR / f"{MODULE_PREFIX}_RESULT_2026-05-17.json"
INPUT_MODULE_LEDGER = ROUTE_DIR / f"{MODULE_PREFIX}_NUMERIC_DECISION_MODULE_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR_SPEC_LEDGER = ROUTE_DIR / f"{MODULE_PREFIX}_SOURCE_GEOMETRY_REPAIR_SPEC_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE
MODULE_HELPER = REPO / "src/research_infra/moonshot_numeric_decision_modules.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTABLE_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_SPEC_2026-05-17.json"
APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"
SCORER_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_OUTPUT_LEDGER_2026-05-17.jsonl"
AVOID_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_FILTER_OUTPUT_LEDGER_2026-05-17.jsonl"
REPAIR_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_OUTPUT_LEDGER_2026-05-17.jsonl"
CONTEXT_OUTPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTEXT_STRESS_OUTPUT_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
SCOPE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_DECISION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local numeric module router application. This packet runs executable numeric decision modules against all "
    "numeric result rows, emits scorer/avoid/source-repair/context outputs, executes source-repair specs into exact "
    "current-packet repair statuses, and writes scope decisions. It does not place orders or change live behavior."
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
                "source_manifest_id": f"OHLC-GTOS-NUMERIC-MODULE-ROUTER-SRC-{index:04d}",
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


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def bucket_rows(
    application_rows: list[dict[str, Any]],
    repair_execution_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    specs = [
        ("router_application_action", application_rows, "router_application_action"),
        ("numeric_module_event_status", application_rows, "numeric_module_event_status"),
        ("numeric_module_role", application_rows, "numeric_module_role"),
        ("proxy_r_class", application_rows, "proxy_r_class"),
        ("source_repair_execution_status", repair_execution_rows, "source_repair_execution_status"),
        ("exact_repair_possible_from_current_packet", repair_execution_rows, "exact_repair_possible_from_current_packet"),
        ("router_scope_decision", scope_rows, "router_scope_decision"),
        ("scope_symbol", scope_rows, "symbol"),
    ]
    output = []
    for bucket_name, rows, key in specs:
        for value, count in string_counter(rows, key).items():
            output.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-NUMERIC-MODULE-ROUTER-BUCKET-{len(output) + 1:04d}",
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
            "registry_source_surface",
            "Which routed score outputs become branch-local registry source surfaces now?",
            "consume SCORER_OUTPUT_LEDGER into default-off registry source code with source/control guards",
        ),
        (
            "avoid_comparator_surface",
            "Which routed avoid outputs become avoid/inverse comparator score rows now?",
            "consume AVOID_FILTER_OUTPUT_LEDGER into avoided-entry comparator scoring and failure-feature ledgers",
        ),
        (
            "source_repair_execution_surface",
            "Which source repair rows are exact-current-packet repairable and which need broker/source fields?",
            "consume SOURCE_REPAIR_EXECUTION_LEDGER into exact repair attempts, source acquisition proof, or broker-geometry proof",
        ),
        (
            "scope_decision_surface",
            "Which symbol/session/horizon/source scopes are scorer, avoid, repair, or context guard decisions?",
            "consume SCOPE_DECISION_LEDGER into branch-system recommendation rows",
        ),
    ]
    return [
        with_common(
            {
                "numeric_module_router_question_id": f"OHLC-GTOS-NUMERIC-MODULE-ROUTER-Q-{index:04d}",
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
    manifest["latest_branch_local_numeric_module_router_application"] = {
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
        "event": "branch_local_numeric_module_router_application_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Applied executable numeric decision modules to all numeric result rows and emitted scorer, avoid, repair, context, and scope decision outputs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch-Local Numeric Module Router Application",
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
    lines.extend(["", "## Router Actions", ""])
    for action, count in result["bucket_distributions"]["router_application_action"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.append("")
    write_text(SUMMARY_PATH, "\n".join(lines))


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_NUMERIC_LEDGER,
            INPUT_MODULE_RESULT,
            INPUT_MODULE_LEDGER,
            INPUT_SOURCE_REPAIR_SPEC_LEDGER,
            HELPER_MODULE,
            MODULE_HELPER,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    numeric_rows = read_jsonl(INPUT_NUMERIC_LEDGER)
    module_result = read_json(INPUT_MODULE_RESULT)
    module_rows = read_jsonl(INPUT_MODULE_LEDGER)
    source_repair_specs = read_jsonl(INPUT_SOURCE_REPAIR_SPEC_LEDGER)
    registry = build_numeric_module_registry(module_rows)

    application_rows = []
    for index, numeric_row in enumerate(numeric_rows, 1):
        routed = route_numeric_event(event_from_numeric_result(numeric_row), registry)
        application_rows.append(with_common(router_application_row(numeric_row, routed, index), generated_at, manifest_hash))

    scorer_rows = [row for row in application_rows if row.get("router_application_action") == "REGISTER_DEFAULT_OFF_SCORER_SURFACE"]
    avoid_rows = [row for row in application_rows if row.get("router_application_action") == "REGISTER_AVOID_INVERSE_FILTER_SURFACE"]
    repair_rows = [row for row in application_rows if row.get("router_application_action") == "EXECUTE_SOURCE_GEOMETRY_REPAIR_PATH"]
    context_rows = [row for row in application_rows if row.get("router_application_action") == "BIND_CONTEXT_STRESS_GUARD_SURFACE"]
    source_repair_execution_rows = [
        with_common(source_repair_execution_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_repair_specs, 1)
    ]
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in application_rows:
        groups[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("source_component"))].append(row)
    scope_rows = [
        with_common(scope_router_decision(groups[key], index, key), generated_at, manifest_hash)
        for index, key in enumerate(sorted(groups, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    buckets = bucket_rows(application_rows, source_repair_execution_rows, scope_rows, generated_at, manifest_hash)
    counts = {
        "input_numeric_result_rows": len(numeric_rows),
        "input_numeric_decision_module_rows": len(module_rows),
        "input_source_repair_spec_rows": len(source_repair_specs),
        "event_application_rows": len(application_rows),
        "scorer_output_rows": len(scorer_rows),
        "avoid_filter_output_rows": len(avoid_rows),
        "source_repair_output_rows": len(repair_rows),
        "context_stress_output_rows": len(context_rows),
        "source_repair_execution_rows": len(source_repair_execution_rows),
        "source_repair_exact_current_packet_possible_rows": sum(
            1 for row in source_repair_execution_rows if row.get("exact_repair_possible_from_current_packet") is True
        ),
        "scope_decision_rows": len(scope_rows),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_rows),
    }
    distributions = {
        "router_application_action": string_counter(application_rows, "router_application_action"),
        "numeric_module_event_status": string_counter(application_rows, "numeric_module_event_status"),
        "numeric_module_role": string_counter(application_rows, "numeric_module_role"),
        "proxy_r_class": string_counter(application_rows, "proxy_r_class"),
        "source_repair_execution_status": string_counter(source_repair_execution_rows, "source_repair_execution_status"),
        "exact_repair_possible_from_current_packet": string_counter(
            source_repair_execution_rows, "exact_repair_possible_from_current_packet"
        ),
        "router_scope_decision": string_counter(scope_rows, "router_scope_decision"),
        "scope_symbol": string_counter(scope_rows, "symbol"),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "numeric_module_registry_router_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "counts": counts,
        "bucket_distributions": distributions,
        "all_numeric_rows_applied": counts["event_application_rows"] == len(numeric_rows),
        "all_modules_registered": registry["module_count"] == module_result["counts"]["numeric_decision_module_rows"],
        "all_router_events_matched": all(row.get("module_lookup_method") in {"numeric_result_row_id", "unique_numeric_scope_key"} for row in application_rows),
        "split_outputs_sum_to_application_rows": len(scorer_rows) + len(avoid_rows) + len(repair_rows) + len(context_rows)
        == len(application_rows),
        "source_repair_execution_rows_cover_specs": counts["source_repair_execution_rows"]
        == module_result["counts"]["source_geometry_repair_spec_rows"],
        "no_summary_only_terminal_rows": all(
            row.get("summary_only_terminal") is False for row in application_rows + source_repair_execution_rows + scope_rows
        ),
    }
    executable_spec = {
        "artifact": f"{PREFIX}_EXECUTABLE_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "numeric_module_registry_router_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "registry_callable": "build_numeric_module_registry",
        "event_conversion_callable": "event_from_numeric_result",
        "event_router_callable": "route_numeric_event",
        "application_row_callable": "router_application_row",
        "source_repair_execution_callable": "source_repair_execution_row",
        "scope_decision_callable": "scope_router_decision",
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
    questions = question_rows(counts, generated_at, manifest_hash)
    outputs = [
        RESULT_PATH,
        EXECUTABLE_SPEC_PATH,
        APPLICATION_LEDGER,
        SCORER_OUTPUT_LEDGER,
        AVOID_OUTPUT_LEDGER,
        REPAIR_OUTPUT_LEDGER,
        CONTEXT_OUTPUT_LEDGER,
        SOURCE_REPAIR_EXECUTION_LEDGER,
        SCOPE_DECISION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(EXECUTABLE_SPEC_PATH, json.dumps(executable_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(APPLICATION_LEDGER, application_rows)
    write_jsonl(SCORER_OUTPUT_LEDGER, scorer_rows)
    write_jsonl(AVOID_OUTPUT_LEDGER, avoid_rows)
    write_jsonl(REPAIR_OUTPUT_LEDGER, repair_rows)
    write_jsonl(CONTEXT_OUTPUT_LEDGER, context_rows)
    write_jsonl(SOURCE_REPAIR_EXECUTION_LEDGER, source_repair_execution_rows)
    write_jsonl(SCOPE_DECISION_LEDGER, scope_rows)
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
