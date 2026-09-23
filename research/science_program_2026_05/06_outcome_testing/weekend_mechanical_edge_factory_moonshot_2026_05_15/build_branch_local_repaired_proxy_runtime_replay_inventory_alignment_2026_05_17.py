#!/usr/bin/env python3
"""Align runtime replay recommendations with unified system decision inventory."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_inventory_alignment import (
    RUNTIME_REPLAY_INVENTORY_ALIGNMENT_SURFACE,
    inventory_alignment_bucket_rows,
    research_boundary,
    signal_inventory_alignment_rows,
    symbol_inventory_alignment_rows,
    system_inventory_alignment_rows,
)


RECOMMENDATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RECOMMENDATION"
UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_INVENTORY_ALIGNMENT"

RECOMMENDATION_RESULT = ROUTE_DIR / f"{RECOMMENDATION_PREFIX}_RESULT_2026-05-17.json"
SIGNAL_ROUTE_LEDGER = ROUTE_DIR / f"{RECOMMENDATION_PREFIX}_SIGNAL_ROUTE_LEDGER_2026-05-17.jsonl"
SYMBOL_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{RECOMMENDATION_PREFIX}_SYMBOL_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
UNIFIED_RESULT = ROUTE_DIR / f"{UNIFIED_PREFIX}_RESULT_2026-05-17.json"
UNIFIED_CANDIDATE_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"
UNIFIED_SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_inventory_alignment.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_recommendation.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_inventory_alignment_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SIGNAL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNAL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-INVENTORY-SRCMAN-{index:04d}",
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
    output.setdefault("runtime_replay_inventory_alignment_surface", RUNTIME_REPLAY_INVENTORY_ALIGNMENT_SURFACE)
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
        "# Repaired Proxy Runtime Replay Inventory Alignment",
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
    lines.extend(["", "## Continuation", "", "Use alignment classes to separate represented replay signals from review gaps.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 190 - Runtime Replay Inventory Alignment\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 190 - Runtime Replay Inventory Alignment

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 189. Replay signal routes were compared with sanitized branch-local unified system decision inventory facts.

Outputs:

- `{counts['signal_inventory_alignment_rows']}` signal inventory alignment rows from `{counts['input_signal_route_rows']}` replay signal route rows.
- `{counts['symbol_inventory_alignment_rows']}` symbol/session/horizon inventory alignment rows.
- `{counts['system_inventory_alignment_rows']}` system inventory alignment row.
- Alignment class split captured in bucket and result artifacts without copying legacy defensive fields from historical inventory rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: use alignment classes to separate represented replay signals from exact/broad scope review gaps.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    recommendation_result = read_json(RECOMMENDATION_RESULT)
    unified_result = read_json(UNIFIED_RESULT)
    signal_rows_in = read_jsonl(SIGNAL_ROUTE_LEDGER)
    symbol_recommendation_rows_in = read_jsonl(SYMBOL_RECOMMENDATION_LEDGER)
    unified_rows_in = read_jsonl(UNIFIED_CANDIDATE_LEDGER)
    unified_scope_rows_in = read_jsonl(UNIFIED_SCOPE_ROLLUP_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            RECOMMENDATION_RESULT,
            SIGNAL_ROUTE_LEDGER,
            SYMBOL_RECOMMENDATION_LEDGER,
            UNIFIED_RESULT,
            UNIFIED_CANDIDATE_LEDGER,
            UNIFIED_SCOPE_ROLLUP_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    alignment_rows = [
        with_common(row, generated_at, manifest_hash) for row in signal_inventory_alignment_rows(signal_rows_in, unified_rows_in)
    ]
    symbol_rows = [
        with_common(row, generated_at, manifest_hash) for row in symbol_inventory_alignment_rows(alignment_rows)
    ]
    system_rows = [
        with_common(row, generated_at, manifest_hash) for row in system_inventory_alignment_rows(alignment_rows, symbol_rows)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in inventory_alignment_bucket_rows(alignment_rows, symbol_rows, system_rows)
    ]
    class_counts = Counter(str(row.get("inventory_alignment_class")) for row in alignment_rows)
    counts = {
        "input_recommendation_result_ok": int(bool(recommendation_result.get("ok"))),
        "input_unified_result_ok": int(bool(unified_result.get("artifact"))),
        "input_signal_route_rows": len(signal_rows_in),
        "input_symbol_recommendation_rows": len(symbol_recommendation_rows_in),
        "input_unified_candidate_rows": len(unified_rows_in),
        "input_unified_scope_rollup_rows": len(unified_scope_rows_in),
        "signal_inventory_alignment_rows": len(alignment_rows),
        "exact_scope_compatible_rows": class_counts.get("INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE", 0),
        "exact_scope_present_different_action_rows": class_counts.get(
            "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION", 0
        ),
        "broad_scope_compatible_rows": class_counts.get("INVENTORY_ALIGNMENT_BROAD_SCOPE_COMPATIBLE", 0),
        "broad_scope_present_different_action_rows": class_counts.get(
            "INVENTORY_ALIGNMENT_BROAD_SCOPE_PRESENT_DIFFERENT_ACTION", 0
        ),
        "no_scope_inventory_rows": class_counts.get("INVENTORY_ALIGNMENT_NO_SCOPE_IN_UNIFIED_INVENTORY", 0),
        "replay_scope_unmatched_review_rows": class_counts.get("INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW", 0),
        "symbol_inventory_alignment_rows": len(symbol_rows),
        "system_inventory_alignment_rows": len(system_rows),
        "bucket_rows": len(bucket_rows),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_inventory_alignment": system_rows[0]["system_inventory_alignment"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(SIGNAL_INVENTORY_ALIGNMENT_LEDGER, alignment_rows)
    write_jsonl(SYMBOL_INVENTORY_ALIGNMENT_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_INVENTORY_ALIGNMENT_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_replay_inventory_alignment_result"),
            (SIGNAL_INVENTORY_ALIGNMENT_LEDGER, "repaired_proxy_runtime_replay_signal_inventory_alignment_ledger"),
            (SYMBOL_INVENTORY_ALIGNMENT_LEDGER, "repaired_proxy_runtime_replay_symbol_inventory_alignment_ledger"),
            (SYSTEM_INVENTORY_ALIGNMENT_LEDGER, "repaired_proxy_runtime_replay_system_inventory_alignment_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_replay_inventory_alignment_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_replay_inventory_alignment_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_replay_inventory_alignment_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_replay_inventory_alignment_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_replay_inventory_alignment_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_replay_inventory_alignment_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Aligned runtime replay recommendation routes with sanitized unified system inventory facts.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
