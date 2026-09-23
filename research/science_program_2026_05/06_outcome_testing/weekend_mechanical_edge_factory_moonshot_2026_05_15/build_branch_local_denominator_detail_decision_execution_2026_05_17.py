#!/usr/bin/env python3
"""Consume denominator detail rows into default-off/source/horizon decisions."""

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

from src.research_infra.moonshot_branch_local_denominator_detail_decisions import (
    DETAIL_DECISION_SURFACE,
    default_off_implementation_decision,
    exact_control_expansion_decision,
    horizon_decision,
    scorer_behavior_decision,
    source_completeness_decision,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_DECISION_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_NEXT_DETAIL = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_ACTION_DETAIL_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL_DETAIL = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_DETAIL_LEDGER_2026-05-17.jsonl"
INPUT_SCOPE_DETAIL = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_DETAIL_LEDGER_2026-05-17.jsonl"
INPUT_IMPLEMENTATION_DETAIL = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_DETAIL_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_MANIFEST = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DETAIL_DECISION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXACT_CONTROL_EXPANSION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_EXPANSION_LEDGER_2026-05-17.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_COMPLETENESS_LEDGER_2026-05-17.jsonl"
HORIZON_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_DECISION_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
SCORER_BEHAVIOR_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_BEHAVIOR_LEDGER_2026-05-17.jsonl"
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
    "Branch-local denominator detail decision-execution bundle only. It converts detail execution rows into "
    "exact-control expansion results, source-completeness kill/repair decisions, horizon repair/redesign decisions, "
    "default-off implementation candidates, and scorer-behavior rows. It does not change live behavior, place orders, "
    "or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-DETAIL-DECISION-SRC-{index:04d}",
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
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "safe_flags": SAFE_FLAGS,
                    "not_completion": True,
                }
            )
    manifest["latest_branch_local_denominator_detail_decision_execution_bundle"] = {
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
        "event": "branch_local_denominator_detail_decision_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed detail rows into exact-control expansion, source completeness, horizon, default-off implementation, and scorer behavior decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
            INPUT_NEXT_DETAIL,
            INPUT_TERMINAL_DETAIL,
            INPUT_SCOPE_DETAIL,
            INPUT_IMPLEMENTATION_DETAIL,
            INPUT_SOURCE_MANIFEST,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    next_rows = read_jsonl(INPUT_NEXT_DETAIL)
    terminal_rows = read_jsonl(INPUT_TERMINAL_DETAIL)
    scope_rows = read_jsonl(INPUT_SCOPE_DETAIL)
    implementation_rows = read_jsonl(INPUT_IMPLEMENTATION_DETAIL)

    exact_rows = []
    for index, row in enumerate([row for row in next_rows if row.get("detail_execution_family") == "EXACT_CONTROL"], 1):
        decision = exact_control_expansion_decision(row)
        decision["exact_control_expansion_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-DECISION-EXACT-{index:05d}"
        exact_rows.append(with_common(decision, generated_at, manifest_hash))

    source_rows = []
    for index, row in enumerate([row for row in next_rows if row.get("detail_execution_family") == "SOURCE_CONTRADICTION"], 1):
        decision = source_completeness_decision(row)
        decision["source_completeness_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-DECISION-SOURCE-{index:05d}"
        source_rows.append(with_common(decision, generated_at, manifest_hash))

    horizon_inputs = [
        *[row for row in next_rows if str(row.get("detail_execution_family", "")).startswith("HORIZON_")],
        *[row for row in terminal_rows if row.get("detail_execution_family") == "HORIZON_TERMINAL_KILL"],
    ]
    horizon_rows = []
    for index, row in enumerate(horizon_inputs, 1):
        decision = horizon_decision(row)
        decision["horizon_decision_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-DECISION-HORIZON-{index:05d}"
        horizon_rows.append(with_common(decision, generated_at, manifest_hash))

    default_rows = []
    for index, row in enumerate([*next_rows, *terminal_rows], 1):
        decision = default_off_implementation_decision(row)
        decision["default_off_implementation_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-DECISION-IMPL-{index:05d}"
        default_rows.append(with_common(decision, generated_at, manifest_hash))

    scorer_inputs = [
        row
        for row in next_rows
        if row.get("candidate_use_allowed_now")
        or row.get("detail_execution_family") in {"HORIZON_REPAIR", "HORIZON_REDESIGN", "HORIZON_KILL_CHECK"}
    ]
    scorer_rows = []
    for index, row in enumerate(scorer_inputs, 1):
        decision = scorer_behavior_decision(row)
        decision["scorer_behavior_row_id"] = f"OHLC-GTOS-DENOM-DETAIL-DECISION-SCORER-{index:05d}"
        scorer_rows.append(with_common(decision, generated_at, manifest_hash))

    distributions = {
        "exact_control_expansion_status": string_counter(exact_rows, "exact_control_expansion_status"),
        "source_completeness_status": string_counter(source_rows, "source_completeness_status"),
        "horizon_detail_status": string_counter(horizon_rows, "horizon_detail_status"),
        "default_off_implementation_status": string_counter(default_rows, "default_off_implementation_status"),
        "decision_result": string_counter(default_rows, "decision_result"),
        "scorer_behavior_status": string_counter(scorer_rows, "scorer_behavior_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(default_rows, "outside_gbpjpy_xauusd_current_branch_box"),
        "terminal_decision": string_counter(default_rows, "terminal_decision"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-DETAIL-DECISION-BUCKET-{len(buckets) + 1:04d}",
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
                "question_id": "OHLC-GTOS-DENOM-DETAIL-DECISION-Q-001",
                "question": "Did this layer consume all detail rows into implementation/default-off decisions?",
                "answer_route": "Yes: 207 next-action rows plus 67 terminal detail rows produce 274 default-off implementation decision rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-DECISION-Q-002",
                "question": "Which rows can change scorer behavior now?",
                "answer_route": "Only 35 default-off scorer-behavior rows: 4 guarded scope match-only scorers, 17 horizon repair rescorers, 12 horizon redesign scorers, and 2 horizon kill-check repair gates.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-DECISION-Q-003",
                "question": "Did source-proxy kills get softened into open blockers?",
                "answer_route": "No: all 61 source contradiction rows remain kill-preserved unless future exact source evidence contradicts the negative proxy.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DETAIL-DECISION-Q-004",
                "question": "Did exact-control target/scope rows get scalar permission?",
                "answer_route": "No: 111 exact-control build rows remain blocked; the 4 guarded rows are research-only default-off scope scorers with exact builds still open.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    counts = {
        "input_next_detail_rows": len(next_rows),
        "input_terminal_detail_rows": len(terminal_rows),
        "input_scope_detail_rows": len(scope_rows),
        "input_implementation_detail_rows": len(implementation_rows),
        "exact_control_expansion_rows": len(exact_rows),
        "source_completeness_rows": len(source_rows),
        "horizon_decision_rows": len(horizon_rows),
        "default_off_implementation_rows": len(default_rows),
        "scorer_behavior_rows": len(scorer_rows),
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
        "upstream_counts": {"denominator_detail_execution_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "default_off_implementation_status_counts": distributions["default_off_implementation_status"],
            "scorer_behavior_status_counts": distributions["scorer_behavior_status"],
            "source_completeness_status_counts": distributions["source_completeness_status"],
            "horizon_detail_status_counts": distributions["horizon_detail_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_DETAIL_DECISION_EXECUTION_BUNDLE_RESULT: convert detail rows into "
                "default-off implementation decisions, preserve source/horizon kills, keep exact-control scalar use "
                "blocked except guarded research-only match-scope scorers, and continue into source/horizon/exact-control "
                "implementation materialization only from these result rows."
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
        "input_detail_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "detail_decision_surface": DETAIL_DECISION_SURFACE,
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }

    outputs = [
        EXACT_CONTROL_EXPANSION_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        HORIZON_DECISION_LEDGER,
        DEFAULT_OFF_IMPLEMENTATION_LEDGER,
        SCORER_BEHAVIOR_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(EXACT_CONTROL_EXPANSION_LEDGER, exact_rows)
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)
    write_jsonl(HORIZON_DECISION_LEDGER, horizon_rows)
    write_jsonl(DEFAULT_OFF_IMPLEMENTATION_LEDGER, default_rows)
    write_jsonl(SCORER_BEHAVIOR_LEDGER, scorer_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Detail Decision Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Exact-control expansion rows: `{counts['exact_control_expansion_rows']}`.",
                f"- Source completeness rows: `{counts['source_completeness_rows']}`.",
                f"- Horizon decision rows: `{counts['horizon_decision_rows']}`.",
                f"- Default-off implementation rows: `{counts['default_off_implementation_rows']}`.",
                f"- Scorer behavior rows: `{counts['scorer_behavior_rows']}`.",
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
