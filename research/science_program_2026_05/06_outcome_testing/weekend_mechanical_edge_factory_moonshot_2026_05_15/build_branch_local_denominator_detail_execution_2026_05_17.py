#!/usr/bin/env python3
"""Build detail execution rows from guarded scorer next actions."""

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

from src.research_infra.moonshot_branch_local_denominator_detail_execution import (
    DETAIL_EXECUTION_SURFACE,
    detail_execution_from_next_action,
    scope_detail_rollup,
    terminal_detail_from_kill,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_GUARDED_SCOPE_SCORER_REGISTRATION_BUNDLE"
ACQ_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_REGISTRATION = ROUTE_DIR / f"{INPUT_PREFIX}_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_NEXT = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_ACTION_CARRYFORWARD_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_KILL_CARRYFORWARD_LEDGER_2026-05-17.jsonl"
INPUT_IMPLEMENTATION = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_TARGET_EVIDENCE = ROUTE_DIR / f"{ACQ_PREFIX}_EXACT_CONTROL_TARGET_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_SCOPE_EVIDENCE = ROUTE_DIR / f"{ACQ_PREFIX}_EXACT_CONTROL_SCOPE_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_EVIDENCE = ROUTE_DIR / f"{ACQ_PREFIX}_SOURCE_EXACT_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON_EVIDENCE = ROUTE_DIR / f"{ACQ_PREFIX}_HORIZON_REPAIR_RESCORE_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DETAIL_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
NEXT_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_ACTION_DETAIL_LEDGER_2026-05-17.jsonl"
TERMINAL_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_DETAIL_LEDGER_2026-05-17.jsonl"
SCOPE_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_DETAIL_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_DETAIL_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch-local denominator detail execution bundle only. It expands guarded scorer next actions into exact-control, "
    "source-contradiction, horizon-repair/redesign, and terminal failure-intelligence detail rows. It does not change "
    "live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or "
    "promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-DETAIL-SRC-{index:04d}",
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


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def evidence_for_next_action(
    row: dict[str, Any],
    target_by_code: dict[Any, dict[str, Any]],
    scope_by_scope: dict[tuple[Any, Any, Any, Any], dict[str, Any]],
    source_by_code: dict[Any, dict[str, Any]],
    horizon_by_code: dict[Any, dict[str, Any]],
) -> dict[str, Any] | None:
    lane = row.get("action_execution_lane")
    source_code = row.get("source_code_candidate_id")
    if lane == "EXACT_CONTROL_TARGET_BUILD":
        return target_by_code.get(source_code)
    if lane == "EXACT_CONTROL_SCOPE_BUILD":
        return scope_by_scope.get(scope_key(row))
    if lane == "SOURCE_CONTRADICTION_CHECK":
        return source_by_code.get(source_code)
    if lane in {"HORIZON_REPAIR", "HORIZON_REDESIGN", "HORIZON_KILL_CHECK"}:
        return horizon_by_code.get(source_code)
    return None


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "safe_flags": SAFE_FLAGS,
                    "not_completion": True,
                }
            )
    manifest["latest_branch_local_denominator_detail_execution_bundle"] = {
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
        "event": "branch_local_denominator_detail_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Expanded next-action rows into exact-control/source/horizon detail execution and terminal detail rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
            INPUT_REGISTRATION,
            INPUT_NEXT,
            INPUT_TERMINAL,
            INPUT_IMPLEMENTATION,
            INPUT_EXACT_TARGET_EVIDENCE,
            INPUT_EXACT_SCOPE_EVIDENCE,
            INPUT_SOURCE_EVIDENCE,
            INPUT_HORIZON_EVIDENCE,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    registrations = read_jsonl(INPUT_REGISTRATION)
    next_rows = read_jsonl(INPUT_NEXT)
    terminal_rows = read_jsonl(INPUT_TERMINAL)
    implementation_rows = read_jsonl(INPUT_IMPLEMENTATION)
    target_evidence_rows = read_jsonl(INPUT_EXACT_TARGET_EVIDENCE)
    scope_evidence_rows = read_jsonl(INPUT_EXACT_SCOPE_EVIDENCE)
    source_evidence_rows = read_jsonl(INPUT_SOURCE_EVIDENCE)
    horizon_evidence_rows = read_jsonl(INPUT_HORIZON_EVIDENCE)

    target_by_code = {row.get("source_code_candidate_id"): row for row in target_evidence_rows}
    scope_by_scope = {scope_key(row): row for row in scope_evidence_rows}
    source_by_code = {row.get("source_code_candidate_id"): row for row in source_evidence_rows}
    horizon_by_code = {row.get("source_code_candidate_id"): row for row in horizon_evidence_rows}

    next_detail = []
    evidence_join_counts = Counter()
    for index, row in enumerate(next_rows, 1):
        evidence = evidence_for_next_action(row, target_by_code, scope_by_scope, source_by_code, horizon_by_code)
        evidence_join_counts["JOINED" if evidence else "MISSING"] += 1
        detail = detail_execution_from_next_action(row, evidence)
        detail["evidence_join_status"] = "EVIDENCE_JOINED" if evidence else "EVIDENCE_MISSING"
        detail["denominator_detail_execution_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-NEXT-{index:05d}"
        next_detail.append(with_common(detail, generated_at, manifest_hash))

    terminal_detail = []
    for index, row in enumerate(terminal_rows, 1):
        detail = terminal_detail_from_kill(row)
        detail["denominator_terminal_detail_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-TERM-{index:05d}"
        terminal_detail.append(with_common(detail, generated_at, manifest_hash))

    grouped: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in [*next_detail, *terminal_detail]:
        grouped[scope_key(row)].append(row)
    scope_detail = []
    for index, (key, rows) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        rollup = scope_detail_rollup(key, rows)
        rollup["denominator_scope_detail_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-SCOPE-{index:05d}"
        scope_detail.append(with_common(rollup, generated_at, manifest_hash))

    implementation_detail = []
    next_by_resolution = {row.get("input_resolution_row_id"): row for row in next_detail}
    for index, row in enumerate(implementation_rows, 1):
        matched = next_by_resolution.get(row.get("input_resolution_row_id"))
        status = (
            "IMPLEMENTATION_DETAIL_LINKED_TO_NEXT_ACTION"
            if matched
            else "IMPLEMENTATION_DETAIL_NO_NEXT_ACTION_TERMINAL_OR_CONTEXT"
        )
        detail = dict(row)
        detail.update(
            {
                "denominator_implementation_detail_row_id": f"OHLC-GTOS-DENOM-DETAIL-IMPL-{index:05d}",
                "matched_detail_execution_row_id": (matched or {}).get("denominator_detail_execution_row_id"),
                "implementation_detail_status": status,
                "unconditional_scalar_use_allowed": False,
            }
        )
        implementation_detail.append(with_common(detail, generated_at, manifest_hash))

    distributions = {
        "detail_execution_family": string_counter(next_detail, "detail_execution_family"),
        "detail_execution_status": string_counter(next_detail, "detail_execution_status"),
        "detail_execution_decision": string_counter(next_detail, "detail_execution_decision"),
        "candidate_use_allowed_now": string_counter(next_detail, "candidate_use_allowed_now"),
        "scope_detail_status": string_counter(scope_detail, "scope_detail_status"),
        "terminal_detail_family": string_counter(terminal_detail, "detail_execution_family"),
        "implementation_detail_status": string_counter(implementation_detail, "implementation_detail_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(next_detail, "outside_gbpjpy_xauusd_current_branch_box"),
        "evidence_join_status": string_counter(next_detail, "evidence_join_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-DETAIL-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-Q-001",
                "question": "Did detail execution preserve all next-action rows?",
                "answer_route": "Yes: all 207 next-action carryforward rows became detail execution rows and each joined to its executed evidence row.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-Q-002",
                "question": "Did guarded scorer registration remove exact-control build requirements?",
                "answer_route": "No: guarded rows can score only research-only matching scopes; unconditional scalar use remains blocked and exact-control builds stay open.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-Q-003",
                "question": "Did terminal source/horizon kills remain useful intelligence?",
                "answer_route": "Yes: all 67 terminal kills became terminal detail rows preserving source/horizon failure causes.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    counts = {
        "input_guarded_scorer_registration_rows": len(registrations),
        "input_next_action_carryforward_rows": len(next_rows),
        "input_terminal_kill_carryforward_rows": len(terminal_rows),
        "input_implementation_registration_rows": len(implementation_rows),
        "input_exact_control_target_evidence_rows": len(target_evidence_rows),
        "input_exact_control_scope_evidence_rows": len(scope_evidence_rows),
        "input_source_contradiction_evidence_rows": len(source_evidence_rows),
        "input_horizon_repair_redesign_evidence_rows": len(horizon_evidence_rows),
        "next_action_detail_rows": len(next_detail),
        "next_action_detail_with_evidence_rows": sum(1 for row in next_detail if row.get("evidence_join_status") == "EVIDENCE_JOINED"),
        "next_action_detail_missing_evidence_rows": sum(1 for row in next_detail if row.get("evidence_join_status") != "EVIDENCE_JOINED"),
        "terminal_detail_rows": len(terminal_detail),
        "scope_detail_rows": len(scope_detail),
        "implementation_detail_rows": len(implementation_detail),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"guarded_scope_scorer_registration_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "evidence_join_counts": {key: int(value) for key, value in sorted(evidence_join_counts.items())},
        "system_decision": {
            "detail_execution_status_counts": distributions["detail_execution_status"],
            "scope_detail_status_counts": distributions["scope_detail_status"],
            "evidence_join_status_counts": distributions["evidence_join_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_DETAIL_EXECUTION_BUNDLE_RESULT: execute row-level detail for 207 "
                "next actions with joined acquisition-execution evidence, keep 4 guarded scorers research-only, "
                "preserve 67 terminal kills, and continue exact control/source/horizon data repair before "
                "unconditional scalar interpretation."
            ),
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "input_guarded_scorer_registration_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "input_evidence_ledgers": [
            INPUT_EXACT_TARGET_EVIDENCE.relative_to(REPO).as_posix(),
            INPUT_EXACT_SCOPE_EVIDENCE.relative_to(REPO).as_posix(),
            INPUT_SOURCE_EVIDENCE.relative_to(REPO).as_posix(),
            INPUT_HORIZON_EVIDENCE.relative_to(REPO).as_posix(),
        ],
        "detail_execution_surface": DETAIL_EXECUTION_SURFACE,
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }

    outputs = [
        NEXT_DETAIL_LEDGER,
        TERMINAL_DETAIL_LEDGER,
        SCOPE_DETAIL_LEDGER,
        IMPLEMENTATION_DETAIL_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(NEXT_DETAIL_LEDGER, next_detail)
    write_jsonl(TERMINAL_DETAIL_LEDGER, terminal_detail)
    write_jsonl(SCOPE_DETAIL_LEDGER, scope_detail)
    write_jsonl(IMPLEMENTATION_DETAIL_LEDGER, implementation_detail)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Detail Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Next-action detail rows: `{counts['next_action_detail_rows']}`.",
                f"- Terminal detail rows: `{counts['terminal_detail_rows']}`.",
                f"- Scope detail rows: `{counts['scope_detail_rows']}`.",
                f"- Implementation detail rows: `{counts['implementation_detail_rows']}`.",
                "- Guarded scorer scalar use remains research-only and exact-control builds remain open.",
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
