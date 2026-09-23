#!/usr/bin/env python3
"""Route runtime replay execution outcomes into branch-local recommendations."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_recommendation import (
    RUNTIME_REPLAY_RECOMMENDATION_SURFACE,
    nonregistration_recommendation_rows,
    recommendation_bucket_rows,
    repair_context_recommendation_rows,
    replay_signal_route_rows,
    research_boundary,
    symbol_recommendation_rows,
    system_recommendation_rows,
    unmatched_scope_review_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RECOMMENDATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_EXECUTION_LEDGER_2026-05-17.jsonl"
MODULE_MATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MODULE_MATCH_LEDGER_2026-05-17.jsonl"
SYMBOL_OUTCOME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_OUTCOME_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REPLAY_CARRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONREGISTRATION_REPLAY_CARRY_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_recommendation.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_recommendation_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SIGNAL_ROUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNAL_ROUTE_LEDGER_2026-05-17.jsonl"
SYMBOL_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_UNMATCHED_SCOPE_REVIEW_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_recommendation_surface", RUNTIME_REPLAY_RECOMMENDATION_SURFACE)
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


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Runtime Replay Recommendation",
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
    lines.extend(["", "## Continuation", "", "Compare recommended replay signals against system-level decision inventory.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 189 - Runtime Replay Recommendation\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 189 - Runtime Replay Recommendation

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 188. Replay execution rows were routed into branch-local signal, context, unmatched-scope, repair, and nonregistration recommendation surfaces.

Outputs:

- `{counts['replay_signal_route_rows']}` signal route rows from `{counts['input_replay_execution_rows']}` replay execution rows.
- `{counts['symbol_recommendation_rows']}` symbol recommendation rows.
- `{counts['unmatched_scope_review_rows']}` unmatched scope review rows and `{counts['repair_context_recommendation_rows']}` repair-context recommendation rows.
- `{counts['nonregistration_recommendation_rows']}` nonregistration recommendation rows and `{counts['system_recommendation_rows']}` system recommendation row.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: compare recommended replay signals against the broader system decision inventory and preserve review rows.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    execution_rows_in = read_jsonl(REPLAY_EXECUTION_LEDGER)
    module_match_rows_in = read_jsonl(MODULE_MATCH_LEDGER)
    symbol_rows_in = read_jsonl(SYMBOL_OUTCOME_LEDGER)
    nonregistration_rows_in = read_jsonl(NONREGISTRATION_REPLAY_CARRY_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            REPLAY_EXECUTION_LEDGER,
            MODULE_MATCH_LEDGER,
            SYMBOL_OUTCOME_LEDGER,
            NONREGISTRATION_REPLAY_CARRY_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    route_rows = [with_common(row, generated_at, manifest_hash) for row in replay_signal_route_rows(execution_rows_in)]
    symbol_recs = [
        with_common(row, generated_at, manifest_hash) for row in symbol_recommendation_rows(symbol_rows_in, route_rows)
    ]
    unmatched_rows = [with_common(row, generated_at, manifest_hash) for row in unmatched_scope_review_rows(route_rows)]
    repair_rows = [
        with_common(row, generated_at, manifest_hash) for row in repair_context_recommendation_rows(route_rows)
    ]
    nonregistration_recs = [
        with_common(row, generated_at, manifest_hash) for row in nonregistration_recommendation_rows(nonregistration_rows_in)
    ]
    system_rows = [with_common(row, generated_at, manifest_hash) for row in system_recommendation_rows(symbol_recs, route_rows)]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in recommendation_bucket_rows(
            route_rows,
            symbol_recs,
            unmatched_rows,
            repair_rows,
            nonregistration_recs,
            system_rows,
        )
    ]
    route_counts = Counter(str(row.get("replay_signal_route_class")) for row in route_rows)
    symbol_rec_counts = Counter(str(row.get("symbol_recommendation")) for row in symbol_recs)
    counts = {
        "input_runtime_replay_result_ok": int(bool(input_result.get("ok"))),
        "input_replay_execution_rows": len(execution_rows_in),
        "input_module_match_rows": len(module_match_rows_in),
        "input_symbol_outcome_rows": len(symbol_rows_in),
        "input_nonregistration_replay_carry_rows": len(nonregistration_rows_in),
        "replay_signal_route_rows": len(route_rows),
        "default_off_signal_route_rows": route_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0),
        "avoid_redesign_signal_route_rows": route_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0),
        "context_only_route_rows": route_counts.get("REPLAY_SIGNAL_CONTEXT_ONLY_BRANCH_LOCAL", 0),
        "unmatched_scope_review_rows": len(unmatched_rows),
        "repair_context_recommendation_rows": len(repair_rows),
        "symbol_recommendation_rows": len(symbol_recs),
        "default_off_symbol_recommendation_rows": symbol_rec_counts.get(
            "BRANCH_LOCAL_DEFAULT_OFF_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON", 0
        ),
        "avoid_redesign_symbol_recommendation_rows": symbol_rec_counts.get(
            "BRANCH_LOCAL_AVOID_REDESIGN_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON", 0
        ),
        "nonregistration_recommendation_rows": len(nonregistration_recs),
        "system_recommendation_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["system_recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(SIGNAL_ROUTE_LEDGER, route_rows)
    write_jsonl(SYMBOL_RECOMMENDATION_LEDGER, symbol_recs)
    write_jsonl(UNMATCHED_SCOPE_REVIEW_LEDGER, unmatched_rows)
    write_jsonl(REPAIR_CONTEXT_RECOMMENDATION_LEDGER, repair_rows)
    write_jsonl(NONREGISTRATION_RECOMMENDATION_LEDGER, nonregistration_recs)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_recommendation_result"),
            (SIGNAL_ROUTE_LEDGER, "repaired_proxy_runtime_replay_signal_route_ledger"),
            (SYMBOL_RECOMMENDATION_LEDGER, "repaired_proxy_runtime_replay_symbol_recommendation_ledger"),
            (UNMATCHED_SCOPE_REVIEW_LEDGER, "repaired_proxy_runtime_replay_unmatched_scope_review_ledger"),
            (REPAIR_CONTEXT_RECOMMENDATION_LEDGER, "repaired_proxy_runtime_replay_repair_context_recommendation_ledger"),
            (NONREGISTRATION_RECOMMENDATION_LEDGER, "repaired_proxy_runtime_replay_nonregistration_recommendation_ledger"),
            (SYSTEM_RECOMMENDATION_LEDGER, "repaired_proxy_runtime_replay_system_recommendation_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_recommendation_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_recommendation_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_recommendation_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_recommendation_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_recommendation_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_recommendation_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Routed runtime replay execution outcomes into branch-local recommendations.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
