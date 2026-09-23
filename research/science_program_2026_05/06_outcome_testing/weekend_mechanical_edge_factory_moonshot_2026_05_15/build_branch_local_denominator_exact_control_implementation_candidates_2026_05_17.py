#!/usr/bin/env python3
"""Consume exact-control scorer/redesign rows into implementation candidate specs."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_denominator_exact_control_implementation_candidates import (
    EXACT_CONTROL_IMPLEMENTATION_SURFACE,
    exact_control_blocker_implementation_candidate,
    exact_control_code_path_spec,
    exact_control_event_implementation_observation,
    exact_control_scope_implementation_candidate,
    scope_key,
)


SCORER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_SCORER_REDESIGN_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_IMPLEMENTATION_CANDIDATE_BUNDLE"

INPUT_SCORER_RESULT = ROUTE_DIR / f"{SCORER_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_RUNTIME = ROUTE_DIR / f"{SCORER_PREFIX}_SCOPE_RUNTIME_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_RUNTIME = ROUTE_DIR / f"{SCORER_PREFIX}_BLOCKER_RUNTIME_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_SCORE = ROUTE_DIR / f"{SCORER_PREFIX}_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
INPUT_SCOPE_SCORER = ROUTE_DIR / f"{SCORER_PREFIX}_SCOPE_DEFAULT_OFF_SCORER_LEDGER_2026-05-17.jsonl"
INPUT_REDESIGN = ROUTE_DIR / f"{SCORER_PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_IMPLEMENTATION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_IMPL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
BLOCKER_IMPL_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
EVENT_IMPL_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_IMPLEMENTATION_OBSERVATION_LEDGER_2026-05-17.jsonl"
CODE_PATH_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_PATH_SPEC_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control implementation-candidate bundle. It consumes scorer/redesign execution rows into "
    "default-off code-path candidates, split/redesign candidates, and event observations. It does not change live "
    "behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or "
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_implementation_candidate_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_implementation_candidate_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed exact-control scorer/redesign rows into branch-local implementation candidates and code-path specs.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def recommendation_rows(
    counts: dict[str, int],
    distributions: dict[str, dict[str, int]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    rows = [
        {
            "system_recommendation_row_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SYSREC-001",
            "recommendation_status": "IMPLEMENT_DEFAULT_OFF_EXACT_CONTROL_SCORERS_BRANCH_LOCAL",
            "row_count": counts["blocker_default_off_scorer_candidate_rows"],
            "recommendation": "Materialize the 44 blocker-level exact-control positive rows as default-off scorer candidates keyed by exact symbol/session/horizon/primitive scope.",
        },
        {
            "system_recommendation_row_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SYSREC-002",
            "recommendation_status": "IMPLEMENT_SPLIT_REDESIGN_BRANCH_LOCAL",
            "row_count": counts["blocker_split_redesign_candidate_rows"],
            "recommendation": "Materialize the 67 negative-target/positive-alignment rows as split/redesign candidates, not deletions.",
        },
        {
            "system_recommendation_row_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SYSREC-003",
            "recommendation_status": "PRESERVE_EVENT_OBSERVATION_DENOMINATOR",
            "row_count": counts["event_implementation_observation_rows"],
            "recommendation": "Preserve every event observation row for score, redesign-signal, and denominator context accounting.",
        },
        {
            "system_recommendation_row_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SYSREC-004",
            "recommendation_status": "KEEP_UNDERLYING_MECHANISM_WHEN_CURRENT_CLAIM_WEAK",
            "row_count": counts["blocker_split_redesign_candidate_rows"],
            "recommendation": "Use split/redesign, avoid/inverse, source-confidence, horizon, or entry-geometry routes before any current-claim rejection.",
        },
        {
            "system_recommendation_row_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SYSREC-005",
            "recommendation_status": "NEXT_ACTION_CONSUME_CODE_PATH_SPECS",
            "row_count": counts["code_path_spec_rows"],
            "recommendation": "Consume the generated code-path specs into branch-local modules or execute the next source/horizon detail route directly.",
        },
    ]
    return [with_common(row, generated_at, manifest_hash) for row in rows]


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_SCORER_RESULT,
            INPUT_SCOPE_RUNTIME,
            INPUT_BLOCKER_RUNTIME,
            INPUT_EVENT_SCORE,
            INPUT_SCOPE_SCORER,
            INPUT_REDESIGN,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    scorer_result = read_json(INPUT_SCORER_RESULT)
    scope_rows = read_jsonl(INPUT_SCOPE_RUNTIME)
    blocker_rows = read_jsonl(INPUT_BLOCKER_RUNTIME)
    event_rows = read_jsonl(INPUT_EVENT_SCORE)
    scorer_rows = read_jsonl(INPUT_SCOPE_SCORER)
    redesign_rows = read_jsonl(INPUT_REDESIGN)

    scorer_by_blocker_id = {row.get("input_blocker_runtime_decision_row_id"): row for row in scorer_rows}
    redesign_by_blocker_id = {row.get("input_blocker_runtime_decision_row_id"): row for row in redesign_rows}

    scope_impl_rows = []
    for index, scope in enumerate(scope_rows, 1):
        row = exact_control_scope_implementation_candidate(scope)
        row["exact_control_scope_implementation_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-SCOPE-{index:04d}"
        scope_impl_rows.append(with_common(row, generated_at, manifest_hash))

    blocker_impl_rows = []
    for index, blocker in enumerate(blocker_rows, 1):
        blocker_id = blocker.get("exact_control_blocker_runtime_decision_row_id")
        row = exact_control_blocker_implementation_candidate(
            blocker,
            scorer_by_blocker_id.get(blocker_id),
            redesign_by_blocker_id.get(blocker_id),
        )
        row["exact_control_blocker_implementation_candidate_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-BLOCKER-{index:05d}"
        )
        blocker_impl_rows.append(with_common(row, generated_at, manifest_hash))

    event_impl_rows = []
    for index, event in enumerate(event_rows, 1):
        row = exact_control_event_implementation_observation(event)
        row["exact_control_event_implementation_observation_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-EVENT-{index:06d}"
        )
        event_impl_rows.append(with_common(row, generated_at, manifest_hash))

    code_path_rows = []
    for candidate in [*scope_impl_rows, *blocker_impl_rows]:
        row = exact_control_code_path_spec(candidate, len(code_path_rows) + 1)
        code_path_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "exact_control_scope_implementation_status": string_counter(
            scope_impl_rows, "exact_control_scope_implementation_status"
        ),
        "exact_control_blocker_implementation_status": string_counter(
            blocker_impl_rows, "exact_control_blocker_implementation_status"
        ),
        "exact_control_event_implementation_status": string_counter(
            event_impl_rows, "exact_control_event_implementation_status"
        ),
        "implementation_candidate_family": string_counter([*scope_impl_rows, *blocker_impl_rows], "implementation_candidate_family"),
        "code_path_status": string_counter(code_path_rows, "code_path_status"),
        "redesign_family": string_counter(
            [row for row in [*scope_impl_rows, *blocker_impl_rows] if row.get("redesign_family")],
            "redesign_family",
        ),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            blocker_impl_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_scope_runtime_spec_rows": len(scope_rows),
        "input_blocker_runtime_decision_rows": len(blocker_rows),
        "input_event_score_rows": len(event_rows),
        "input_scope_default_off_scorer_rows": len(scorer_rows),
        "input_redesign_execution_rows": len(redesign_rows),
        "scope_implementation_rows": len(scope_impl_rows),
        "blocker_implementation_candidate_rows": len(blocker_impl_rows),
        "event_implementation_observation_rows": len(event_impl_rows),
        "code_path_spec_rows": len(code_path_rows),
        "system_recommendation_rows": 5,
        "blocker_default_off_scorer_candidate_rows": sum(
            1
            for row in blocker_impl_rows
            if row.get("exact_control_blocker_implementation_status")
            == "EXACT_CONTROL_BLOCKER_IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
        ),
        "blocker_split_redesign_candidate_rows": sum(
            1
            for row in blocker_impl_rows
            if row.get("exact_control_blocker_implementation_status")
            == "EXACT_CONTROL_BLOCKER_IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
        ),
        "event_score_observation_rows": sum(
            1
            for row in event_impl_rows
            if row.get("exact_control_event_implementation_status")
            == "EXACT_CONTROL_EVENT_IMPLEMENTATION_SCORE_OBSERVATION"
        ),
        "event_redesign_signal_observation_rows": sum(
            1
            for row in event_impl_rows
            if row.get("exact_control_event_implementation_status")
            == "EXACT_CONTROL_EVENT_IMPLEMENTATION_REDESIGN_SIGNAL_OBSERVATION"
        ),
        "event_denominator_context_observation_rows": sum(
            1
            for row in event_impl_rows
            if row.get("exact_control_event_implementation_status")
            == "EXACT_CONTROL_EVENT_IMPLEMENTATION_DENOMINATOR_CONTEXT_OBSERVATION"
        ),
        "bucket_rows": len(buckets),
        "question_rows": 5,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    system_rows = recommendation_rows(counts, distributions, generated_at, manifest_hash)
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-Q-001",
                "question": "Were scorer/redesign rows consumed into implementation candidates rather than another queue?",
                "answer_route": f"Yes: {counts['blocker_implementation_candidate_rows']} blocker implementation rows and {counts['code_path_spec_rows']} code-path specs were emitted.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-Q-002",
                "question": "Were split/redesign rows treated as deletion or cleanup?",
                "answer_route": f"No: {counts['blocker_split_redesign_candidate_rows']} blocker rows and 14 scope rows preserve split/redesign implementation paths.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-Q-003",
                "question": "Are all event rows preserved for implementation observation?",
                "answer_route": f"Yes: all {counts['event_implementation_observation_rows']} scorer/redesign event rows were carried forward.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-Q-004",
                "question": "Does any candidate become unconditional runtime or live behavior?",
                "answer_route": "No: every row remains branch-local, default-off, candidate_use_allowed_now=false, runtime_score_allowed=false, and live_effect=false.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-IMPL-Q-005",
                "question": "What is the immediate concrete continuation?",
                "answer_route": "Consume the code-path specs into branch-local scorer/redesign modules or attack the next source/horizon detail route directly.",
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
            "denominator_exact_control_scorer_redesign_bundle": scorer_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "scope_implementation_status_counts": distributions["exact_control_scope_implementation_status"],
            "blocker_implementation_status_counts": distributions["exact_control_blocker_implementation_status"],
            "event_implementation_status_counts": distributions["exact_control_event_implementation_status"],
            "code_path_status_counts": distributions["code_path_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_IMPLEMENTATION_CANDIDATE_BUNDLE_RESULT: consume exact-control scorer/redesign execution into default-off code-path candidates while preserving split/redesign opportunity intelligence.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_implementation_surface": EXACT_CONTROL_IMPLEMENTATION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "distributions": distributions,
    }
    outputs = [
        SCOPE_IMPL_LEDGER,
        BLOCKER_IMPL_LEDGER,
        EVENT_IMPL_LEDGER,
        CODE_PATH_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_IMPL_LEDGER, scope_impl_rows)
    write_jsonl(BLOCKER_IMPL_LEDGER, blocker_impl_rows)
    write_jsonl(EVENT_IMPL_LEDGER, event_impl_rows)
    write_jsonl(CODE_PATH_LEDGER, code_path_rows)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Implementation Candidate Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope implementation rows: `{counts['scope_implementation_rows']}`.",
                f"- Blocker implementation candidate rows: `{counts['blocker_implementation_candidate_rows']}`.",
                f"- Event implementation observation rows: `{counts['event_implementation_observation_rows']}`.",
                f"- Code-path spec rows: `{counts['code_path_spec_rows']}`.",
                f"- System recommendation rows: `{counts['system_recommendation_rows']}`.",
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
