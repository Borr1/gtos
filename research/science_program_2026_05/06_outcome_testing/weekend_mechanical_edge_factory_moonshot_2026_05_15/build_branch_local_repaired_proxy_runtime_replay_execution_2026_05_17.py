#!/usr/bin/env python3
"""Execute branch-local runtime registry modules against replay score rows."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_execution import (
    RUNTIME_REPLAY_EXECUTION_SURFACE,
    nonregistration_replay_carry_rows,
    replay_execution_bucket_rows,
    replay_module_match_rows,
    replay_registry_execution_rows,
    replay_symbol_outcome_rows,
    research_boundary,
)


REGISTRY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_REGISTRY"
SCORE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_EXECUTION"

REGISTRY_RESULT = ROUTE_DIR / f"{REGISTRY_PREFIX}_RESULT_2026-05-17.json"
REGISTRY_MODULE_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REGISTRY_REVIEW_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_NONREGISTRATION_REGISTRY_REVIEW_LEDGER_2026-05-17.jsonl"
SCORE_RESULT = ROUTE_DIR / f"{SCORE_PREFIX}_RESULT_2026-05-17.json"
SCORE_RERUN_LEDGER = ROUTE_DIR / f"{SCORE_PREFIX}_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
SCORE_SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{SCORE_PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_execution.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_candidate_registry.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_EXECUTION_LEDGER_2026-05-17.jsonl"
MODULE_MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MODULE_MATCH_LEDGER_2026-05-17.jsonl"
SYMBOL_OUTCOME_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_OUTCOME_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REPLAY_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_REPLAY_CARRY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def replace_sprint_event(path: Path, row: dict[str, Any]) -> None:
    event = row.get("event")
    route = row.get("route")
    retained: list[str] = []
    if path.exists():
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    retained.append(line.rstrip("\r\n"))
                    continue
                if existing.get("event") == event and existing.get("route") == route:
                    continue
                retained.append(line.rstrip("\r\n"))
    retained.append(json.dumps(row, sort_keys=True))
    write_text(path, "\n".join(retained) + "\n")


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
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-SRCMAN-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "research_boundary": research_boundary(),
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    output = dict(row)
    output["generated_utc"] = generated_at
    output["source_manifest_hash"] = manifest_hash
    output.setdefault("runtime_replay_execution_surface", RUNTIME_REPLAY_EXECUTION_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def update_output_manifest(entries: list[tuple[Path, str]]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    artifacts = manifest.setdefault("artifacts", [])
    existing = {str(item.get("path")) for item in artifacts}
    for path, artifact_type in entries:
        rel = path.relative_to(REPO).as_posix()
        if rel in existing:
            continue
        artifacts.append({"path": rel, "status": "created", "type": artifact_type})
        existing.add(rel)
    write_json(OUTPUT_MANIFEST, manifest)


def system_action_row(counts: dict[str, int], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    return with_common(
        {
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-SYSTEM-0001",
            "recommendation": (
                "Use replay registry execution rows as the branch-local outcome surface for current guarded modules; "
                "carry repair-context and nonregistration rows separately."
            ),
            "next_branch_local_actions": [
                "compare_runtime_replay_execution_to_symbol_rollups",
                "route_triggered_replay_module_signals_to_system_recommendation",
                "preserve_unmatched_replay_rows_for_scope_review",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Runtime Replay Execution",
        "",
        f"Generated UTC: `{generated_at}`",
        "",
        "Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.extend(
        [
            "",
            "## Continuation",
            "",
            "Compare replay execution outcomes to symbol rollups and route triggered module signals.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 188 - Runtime Replay Execution\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 188 - Runtime Replay Execution

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 187. Runtime registry modules were executed against the replay score rerun ledger while preserving the full replay denominator.

Outputs:

- `{counts['replay_registry_execution_rows']}` replay registry execution rows from `{counts['input_score_rerun_rows']}` replay score rerun rows.
- `{counts['replay_module_match_rows']}` module-match rows over matched registry modules.
- `{counts['symbol_outcome_rows']}` symbol/session/horizon outcome rollups.
- `{counts['nonregistration_replay_carry_rows']}` nonregistration rows kept outside replay execution.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: route replay-triggered module signals into a system recommendation and preserve unmatched rows for scope review.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    registry_result = read_json(REGISTRY_RESULT)
    score_result = read_json(SCORE_RESULT)
    registry_rows_in = read_jsonl(REGISTRY_MODULE_LEDGER)
    score_rows_in = read_jsonl(SCORE_RERUN_LEDGER)
    score_symbol_summary_rows_in = read_jsonl(SCORE_SYMBOL_SUMMARY_LEDGER)
    nonregistration_rows_in = read_jsonl(NONREGISTRATION_REGISTRY_REVIEW_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            REGISTRY_RESULT,
            REGISTRY_MODULE_LEDGER,
            NONREGISTRATION_REGISTRY_REVIEW_LEDGER,
            SCORE_RESULT,
            SCORE_RERUN_LEDGER,
            SCORE_SYMBOL_SUMMARY_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    execution_rows = [
        with_common(row, generated_at, manifest_hash) for row in replay_registry_execution_rows(score_rows_in, registry_rows_in)
    ]
    match_rows = [
        with_common(row, generated_at, manifest_hash) for row in replay_module_match_rows(score_rows_in, registry_rows_in)
    ]
    symbol_rows = [with_common(row, generated_at, manifest_hash) for row in replay_symbol_outcome_rows(execution_rows)]
    nonregistration_carry_rows = [
        with_common(row, generated_at, manifest_hash) for row in nonregistration_replay_carry_rows(nonregistration_rows_in)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in replay_execution_bucket_rows(execution_rows, match_rows, symbol_rows, nonregistration_carry_rows)
    ]
    execution_status = Counter(str(row.get("replay_registry_execution_status")) for row in execution_rows)
    module_outcomes = Counter(str(row.get("module_event_outcome")) for row in match_rows)
    counts = {
        "input_registry_result_ok": int(bool(registry_result.get("ok"))),
        "input_score_result_ok": int(bool(score_result.get("ok"))),
        "input_registry_module_rows": len(registry_rows_in),
        "input_score_rerun_rows": len(score_rows_in),
        "input_score_symbol_summary_rows": len(score_symbol_summary_rows_in),
        "input_nonregistration_registry_review_rows": len(nonregistration_rows_in),
        "replay_registry_execution_rows": len(execution_rows),
        "replay_rows_with_matching_registry": sum(
            1 for row in execution_rows if int(row.get("matching_registry_module_rows") or 0) > 0
        ),
        "replay_rows_without_matching_registry": execution_status.get(
            "REPLAY_REGISTRY_EXECUTION_NO_MATCHING_RUNTIME_CANDIDATE", 0
        ),
        "repair_context_replay_rows": execution_status.get(
            "REPLAY_REGISTRY_EXECUTION_REPAIR_CONTEXT_NO_RUNTIME_CANDIDATE", 0
        ),
        "triggered_or_accepted_replay_rows": execution_status.get(
            "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL", 0
        ),
        "replay_module_match_rows": len(match_rows),
        "default_off_module_accepted_rows": module_outcomes.get("DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL", 0),
        "avoid_redesign_module_triggered_rows": module_outcomes.get(
            "AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL", 0
        ),
        "symbol_outcome_rows": len(symbol_rows),
        "nonregistration_replay_carry_rows": len(nonregistration_carry_rows),
        "bucket_rows": len(bucket_rows),
        "system_action_rows": 1,
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(REPLAY_EXECUTION_LEDGER, execution_rows)
    write_jsonl(MODULE_MATCH_LEDGER, match_rows)
    write_jsonl(SYMBOL_OUTCOME_LEDGER, symbol_rows)
    write_jsonl(NONREGISTRATION_REPLAY_CARRY_LEDGER, nonregistration_carry_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_execution_result"),
            (REPLAY_EXECUTION_LEDGER, "repaired_proxy_runtime_replay_execution_ledger"),
            (MODULE_MATCH_LEDGER, "repaired_proxy_runtime_replay_module_match_ledger"),
            (SYMBOL_OUTCOME_LEDGER, "repaired_proxy_runtime_replay_symbol_outcome_ledger"),
            (NONREGISTRATION_REPLAY_CARRY_LEDGER, "repaired_proxy_runtime_replay_nonregistration_carry_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_runtime_replay_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_execution_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Executed branch-local runtime registry modules against replay score rerun rows.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
