#!/usr/bin/env python3
"""Materialize exact-control implementation code paths into a runtime router bundle."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_runtime_router import (
    EXACT_CONTROL_RUNTIME_ROUTER_SURFACE,
    duplicate_scope_audit_row,
    effective_scope_registration,
    register_exact_control_code_path,
    route_exact_control_event,
    scope_key,
)


IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_IMPLEMENTATION_CANDIDATE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_RUNTIME_ROUTER_BUNDLE"

INPUT_IMPLEMENTATION_RESULT = ROUTE_DIR / f"{IMPL_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_IMPL = ROUTE_DIR / f"{IMPL_PREFIX}_SCOPE_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_IMPL = ROUTE_DIR / f"{IMPL_PREFIX}_BLOCKER_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_IMPL = ROUTE_DIR / f"{IMPL_PREFIX}_EVENT_IMPLEMENTATION_OBSERVATION_LEDGER_2026-05-17.jsonl"
INPUT_CODE_PATH = ROUTE_DIR / f"{IMPL_PREFIX}_CODE_PATH_SPEC_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_RUNTIME_ROUTER_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CODE_PATH_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_PATH_REGISTRATION_LEDGER_2026-05-17.jsonl"
EFFECTIVE_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_EFFECTIVE_SCOPE_REGISTRATION_LEDGER_2026-05-17.jsonl"
EVENT_ROUTING_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_RUNTIME_ROUTING_LEDGER_2026-05-17.jsonl"
DUPLICATE_AUDIT_LEDGER = ROUTE_DIR / f"{PREFIX}_DUPLICATE_SCOPE_AUDIT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control runtime-router bundle. It materializes implementation code-path specs into duplicate-safe "
    "effective scope registrations and event routing rows. It does not change live behavior, place orders, or claim broker "
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_runtime_router_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_runtime_router_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Materialized exact-control code-path specs into duplicate-safe effective scope registrations and event routing rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_IMPLEMENTATION_RESULT,
            INPUT_SCOPE_IMPL,
            INPUT_BLOCKER_IMPL,
            INPUT_EVENT_IMPL,
            INPUT_CODE_PATH,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    implementation_result = read_json(INPUT_IMPLEMENTATION_RESULT)
    scope_impl_rows = read_jsonl(INPUT_SCOPE_IMPL)
    blocker_impl_rows = read_jsonl(INPUT_BLOCKER_IMPL)
    event_impl_rows = read_jsonl(INPUT_EVENT_IMPL)
    code_path_rows = read_jsonl(INPUT_CODE_PATH)

    code_path_registration_rows = []
    for index, row in enumerate(code_path_rows, 1):
        registration = register_exact_control_code_path(row)
        registration["exact_control_runtime_code_path_registration_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-CODEPATH-{index:05d}"
        )
        code_path_registration_rows.append(with_common(registration, generated_at, manifest_hash))

    grouped_registrations: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in code_path_registration_rows:
        grouped_registrations[scope_key(row)].append(row)

    effective_scope_rows = []
    for index, key in enumerate(sorted(grouped_registrations, key=lambda value: tuple(str(part) for part in value)), 1):
        row = effective_scope_registration(grouped_registrations[key])
        row["exact_control_effective_scope_registration_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-SCOPE-{index:04d}"
        )
        effective_scope_rows.append(with_common(row, generated_at, manifest_hash))

    effective_by_scope = {scope_key(row): row for row in effective_scope_rows}
    event_routing_rows = []
    for index, event in enumerate(event_impl_rows, 1):
        row = route_exact_control_event(event, effective_by_scope.get(scope_key(event)))
        row["exact_control_event_runtime_routing_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-EVENT-{index:06d}"
        )
        event_routing_rows.append(with_common(row, generated_at, manifest_hash))

    duplicate_audit_rows = []
    for index, scope_row in enumerate(effective_scope_rows, 1):
        row = duplicate_scope_audit_row(scope_row)
        row["exact_control_duplicate_scope_audit_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-DUPAUDIT-{index:04d}"
        )
        duplicate_audit_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "runtime_registration_status": string_counter(code_path_registration_rows, "runtime_registration_status"),
        "runtime_code_path_lineage": string_counter(code_path_registration_rows, "runtime_code_path_lineage"),
        "effective_scope_registration_status": string_counter(effective_scope_rows, "effective_scope_registration_status"),
        "runtime_event_routing_status": string_counter(event_routing_rows, "runtime_event_routing_status"),
        "effective_runtime_family": string_counter(effective_scope_rows, "effective_runtime_family"),
        "duplicate_handling_status": string_counter(duplicate_audit_rows, "duplicate_scope_audit_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_scope_implementation_rows": len(scope_impl_rows),
        "input_blocker_implementation_rows": len(blocker_impl_rows),
        "input_event_implementation_observation_rows": len(event_impl_rows),
        "input_code_path_spec_rows": len(code_path_rows),
        "code_path_registration_rows": len(code_path_registration_rows),
        "effective_scope_registration_rows": len(effective_scope_rows),
        "event_runtime_routing_rows": len(event_routing_rows),
        "duplicate_scope_audit_rows": len(duplicate_audit_rows),
        "default_off_runtime_registration_rows": sum(
            1
            for row in code_path_registration_rows
            if row.get("runtime_registration_status") == "EXACT_CONTROL_RUNTIME_REGISTER_DEFAULT_OFF_SCORER_CODE_PATH"
        ),
        "split_redesign_runtime_registration_rows": sum(
            1
            for row in code_path_registration_rows
            if row.get("runtime_registration_status") == "EXACT_CONTROL_RUNTIME_REGISTER_SPLIT_REDESIGN_CODE_PATH"
        ),
        "default_off_effective_scope_rows": sum(
            1
            for row in effective_scope_rows
            if row.get("effective_scope_registration_status") == "EXACT_CONTROL_RUNTIME_EFFECTIVE_DEFAULT_OFF_SCORER_SCOPE"
        ),
        "split_redesign_effective_scope_rows": sum(
            1
            for row in effective_scope_rows
            if row.get("effective_scope_registration_status") == "EXACT_CONTROL_RUNTIME_EFFECTIVE_SPLIT_REDESIGN_SCOPE"
        ),
        "runtime_event_default_off_score_rows": sum(
            1
            for row in event_routing_rows
            if row.get("runtime_event_routing_status") == "EXACT_CONTROL_RUNTIME_EVENT_DEFAULT_OFF_SCORE_EMITTED"
        ),
        "runtime_event_redesign_signal_rows": sum(
            1
            for row in event_routing_rows
            if row.get("runtime_event_routing_status") == "EXACT_CONTROL_RUNTIME_EVENT_REDESIGN_SIGNAL_ROUTED"
        ),
        "runtime_event_denominator_context_rows": sum(
            1
            for row in event_routing_rows
            if row.get("runtime_event_routing_status") == "EXACT_CONTROL_RUNTIME_EVENT_DENOMINATOR_CONTEXT"
        ),
        "total_duplicate_code_path_count": sum(int(row.get("duplicate_code_path_count") or 0) for row in effective_scope_rows),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-Q-001",
                "question": "Were all implementation code-path specs materialized?",
                "answer_route": f"Yes: all {counts['code_path_registration_rows']} code-path specs were registered with duplicate runtime use disabled.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-Q-002",
                "question": "Did duplicate blocker/scope lineages inflate event routing?",
                "answer_route": f"No: {counts['code_path_registration_rows']} code paths collapsed into {counts['effective_scope_registration_rows']} effective scope registrations before event routing.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-Q-003",
                "question": "Were all event observations consumed into runtime rows?",
                "answer_route": f"Yes: all {counts['event_runtime_routing_rows']} event observations were routed once per effective scope.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-RUNTIME-Q-004",
                "question": "What remains next?",
                "answer_route": "Use the runtime rows to integrate branch-local scorer/redesign modules further or move directly into the next source/horizon computation route.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "denominator_exact_control_implementation_candidate_bundle": implementation_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "runtime_registration_status_counts": distributions["runtime_registration_status"],
            "effective_scope_status_counts": distributions["effective_scope_registration_status"],
            "event_routing_status_counts": distributions["runtime_event_routing_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_RUNTIME_ROUTER_BUNDLE_RESULT: consume code-path specs into duplicate-safe effective scope routing, preserving all lineage rows without live effect.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_runtime_router_surface": EXACT_CONTROL_RUNTIME_ROUTER_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "distributions": distributions,
    }
    outputs = [
        CODE_PATH_REGISTRATION_LEDGER,
        EFFECTIVE_SCOPE_LEDGER,
        EVENT_ROUTING_LEDGER,
        DUPLICATE_AUDIT_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(CODE_PATH_REGISTRATION_LEDGER, code_path_registration_rows)
    write_jsonl(EFFECTIVE_SCOPE_LEDGER, effective_scope_rows)
    write_jsonl(EVENT_ROUTING_LEDGER, event_routing_rows)
    write_jsonl(DUPLICATE_AUDIT_LEDGER, duplicate_audit_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Runtime Router Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Code-path registrations: `{counts['code_path_registration_rows']}`.",
                f"- Effective scope registrations: `{counts['effective_scope_registration_rows']}`.",
                f"- Event routing rows: `{counts['event_runtime_routing_rows']}`.",
                f"- Duplicate scope audit rows: `{counts['duplicate_scope_audit_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *outputs], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
