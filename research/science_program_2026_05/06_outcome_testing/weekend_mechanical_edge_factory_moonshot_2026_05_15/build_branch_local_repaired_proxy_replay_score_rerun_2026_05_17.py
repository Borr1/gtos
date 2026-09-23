#!/usr/bin/env python3
"""Rerun repaired-proxy scores with replay numeric metrics and control context."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_replay_score_rerun import (
    REPLAY_SCORE_RERUN_SURFACE,
    bucket_rows,
    control_context_lookup,
    control_context_rows,
    family_rows,
    rerun_score_row,
    research_boundary,
    symbol_summary_rows,
)


NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"

NUMERIC_RESULT = ROUTE_DIR / f"{NUMERIC_PREFIX}_RESULT_2026-05-17.json"
REPLAY_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
CONTROL_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_CONTROL_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_replay_score_rerun.py"
NUMERIC_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_replay_numeric_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_replay_score_rerun_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CONTROL_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_CONTEXT_LEDGER_2026-05-17.jsonl"
SCORE_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
AVOID_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_RERUN_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_RERUN_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
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


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-RERUN-SRC-{index:04d}",
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
    output.setdefault("replay_score_rerun_surface", REPLAY_SCORE_RERUN_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-SCORE-RERUN-SYSTEM-0001",
            "recommendation": (
                "Use score-rerun rows as the branch-local scorer/comparator state, carry repair-context rows into "
                "identifier and broker-geometry repair, and rebuild the exact/proxy bridge with rerun score fields."
            ),
            "next_branch_local_actions": [
                "rebuild_exact_proxy_bridge_with_replay_rerun_scores",
                "carry_repair_context_rows_into_identifier_geometry_repair",
                "aggregate_score_rerun_actions_by_symbol_scope_and_market",
                "route_positive_default_off_and_negative_avoid_rows_to_next_branch_local_comparator_packet",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Replay Score Rerun",
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
            (
                "Rebuild the exact/proxy bridge with replay rerun score fields, carry repair-context rows into "
                "identifier/geometry repair, and route scorer/comparator actions to the next branch-local packet."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    text = f"""

## Checkpoint 175 - Replay Numeric Metrics Rerun Registered Scope Scores

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 174. Registered default-off and avoid/redesign scopes were rerun with replay numeric metrics and same-timeframe control context.

Outputs:

- `{counts['control_context_rows']}` control context rows derived from the `173` control numeric rows.
- `{counts['score_rerun_rows']}` score rerun rows, preserving the full `5,324` replay numeric event denominator.
- `{counts['default_off_score_rerun_rows']}` default-off score rerun rows, `{counts['avoid_comparator_rerun_rows']}` avoid comparator rerun rows, and `{counts['repair_context_rerun_rows']}` repair-context rerun rows.
- `{counts['symbol_summary_rows']}` symbol summary rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row for exact/proxy bridge rebuild.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: rebuild the exact/proxy bridge with replay rerun score fields, carry repair-context rows into identifier/geometry repair, and route scorer/comparator actions to the next branch-local packet.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    numeric_result = read_json(NUMERIC_RESULT)
    replay_rows = read_jsonl(REPLAY_NUMERIC_EVENT_LEDGER)
    control_rows = read_jsonl(CONTROL_NUMERIC_EVENT_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            NUMERIC_RESULT,
            REPLAY_NUMERIC_EVENT_LEDGER,
            CONTROL_NUMERIC_EVENT_LEDGER,
            HELPER_MODULE,
            NUMERIC_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    context_rows = [with_common(row, generated_at, manifest_hash) for row in control_context_rows(control_rows)]
    contexts = control_context_lookup(context_rows)
    score_rows = [
        with_common(rerun_score_row(row, contexts.get(str(row.get("market_timeframe") or "")), index), generated_at, manifest_hash)
        for index, row in enumerate(replay_rows, 1)
    ]
    default_rows = family_rows(score_rows, "default_off_repaired_proxy_scorer")
    avoid_rows = family_rows(score_rows, "avoid_redesign_repaired_proxy_comparator")
    repair_rows = family_rows(score_rows, "source_or_broker_geometry_repair")
    symbol_rows = [with_common(row, generated_at, manifest_hash) for row in symbol_summary_rows(score_rows)]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash) for row in bucket_rows(score_rows, context_rows)
    ]
    counts = {
        "input_replay_numeric_event_rows": len(replay_rows),
        "input_control_numeric_event_rows": len(control_rows),
        "control_context_rows": len(context_rows),
        "score_rerun_rows": len(score_rows),
        "default_off_score_rerun_rows": len(default_rows),
        "avoid_comparator_rerun_rows": len(avoid_rows),
        "repair_context_rerun_rows": len(repair_rows),
        "symbol_summary_rows": len(symbol_rows),
        "system_action_rows": 1,
        "bucket_rows": len(bucket_output_rows),
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "upstream_counts": numeric_result.get("counts", {}),
        "score_rerun_denominator_preserved": counts["score_rerun_rows"]
        == numeric_result.get("counts", {}).get("replay_numeric_event_rows"),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(CONTROL_CONTEXT_LEDGER, context_rows)
    write_jsonl(SCORE_RERUN_LEDGER, score_rows)
    write_jsonl(DEFAULT_OFF_RERUN_LEDGER, default_rows)
    write_jsonl(AVOID_RERUN_LEDGER, avoid_rows)
    write_jsonl(REPAIR_CONTEXT_LEDGER, repair_rows)
    write_jsonl(SYMBOL_SUMMARY_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_replay_score_rerun_result"),
            (CONTROL_CONTEXT_LEDGER, "repaired_proxy_replay_score_control_context_ledger"),
            (SCORE_RERUN_LEDGER, "repaired_proxy_replay_score_rerun_ledger"),
            (DEFAULT_OFF_RERUN_LEDGER, "repaired_proxy_replay_default_score_rerun_ledger"),
            (AVOID_RERUN_LEDGER, "repaired_proxy_replay_avoid_score_rerun_ledger"),
            (REPAIR_CONTEXT_LEDGER, "repaired_proxy_replay_repair_context_rerun_ledger"),
            (SYMBOL_SUMMARY_LEDGER, "repaired_proxy_replay_score_symbol_summary_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_replay_score_system_action_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_replay_score_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_replay_score_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_replay_score_summary"),
            (BUILDER_MODULE, "repaired_proxy_replay_score_builder"),
            (VERIFIER_MODULE, "repaired_proxy_replay_score_verifier"),
        ]
    )
    append_jsonl(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_replay_score_rerun_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Reran registered repaired-proxy scores with replay numeric metrics and control context.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
