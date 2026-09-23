#!/usr/bin/env python3
"""Build decisive branch-local recommendations from code-surface execution rows."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_recommendations import (
    RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS_SURFACE,
    aggregate_recommendation_rows,
    recommendation_rows,
    research_boundary,
    system_recommendation_rows,
)


EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS"

EXEC_RESULT = ROUTE_DIR / f"{EXEC_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_recommendations.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_table_recommendations_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "runtime_replay_geometry_table_recommendations_result"),
        (RECOMMENDATION_LEDGER, "runtime_replay_geometry_table_recommendations"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_table_recommendation_aggregates"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_table_recommendations_system"),
        (SUMMARY_PATH, "runtime_replay_geometry_table_recommendations_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_table_recommendations_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_table_recommendations_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_table_recommendations_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_table_recommendations"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 212,
        "event": "runtime_replay_geometry_table_recommendations",
        "generated_utc": generated_at,
        "recommendation_rows": counts["recommendation_rows"],
        "aggregate_recommendation_rows": counts["aggregate_recommendation_rows"],
        "repair_recommendation_rows": counts["repair_recommendation_rows"],
        "continuation": "merge recommendation rows into the broader branch-local moonshot recommendation inventory.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 212 - Runtime Replay Geometry Table Recommendations

Generated: {generated_at}

Trigger: continuation after Checkpoint 211. Passing code-surface executions were consumed into decisive branch-local scorer and avoid recommendations.

Rows:
- recommendation rows: {counts['recommendation_rows']}
- aggregate recommendation rows: {counts['aggregate_recommendation_rows']}
- repair recommendation rows: {counts['repair_recommendation_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: merge recommendation rows into the broader branch-local moonshot recommendation inventory.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Runtime Replay Geometry Table Recommendations",
            "",
            "Checkpoint 212 consumes passing code-surface executions into decisive branch-local recommendations.",
            "",
            "## Counts",
            "",
            f"- Recommendation rows: `{counts['recommendation_rows']}`",
            f"- Aggregate recommendation rows: `{counts['aggregate_recommendation_rows']}`",
            f"- Repair recommendation rows: `{counts['repair_recommendation_rows']}`",
            "",
            "## Continuation",
            "",
            "Merge recommendation rows into the broader branch-local moonshot recommendation inventory.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    exec_result = read_json(EXEC_RESULT)
    execution_rows = read_jsonl(EXECUTION_LEDGER)
    rows = recommendation_rows(execution_rows)
    aggregates = aggregate_recommendation_rows(rows)
    system_rows = system_recommendation_rows(rows, aggregates)

    counts = {
        "input_execution_result_ok": 1 if exec_result.get("ok") else 0,
        "input_execution_rows": len(execution_rows),
        "recommendation_rows": len(rows),
        "aggregate_recommendation_rows": len(aggregates),
        "repair_recommendation_rows": sum(
            1 for row in rows if row.get("recommendation_kind") == "REPAIR_BRANCH_LOCAL_CODE_SURFACE_RECOMMENDATION"
        ),
        "system_rows": len(system_rows),
        "recommendation_kind_counts": count_by(rows, "recommendation_kind"),
        "recommendation_action_counts": count_by(rows, "recommendation_action"),
        "aggregate_recommendation_action_counts": count_by(aggregates, "aggregate_recommendation_action"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_table_recommendations_surface": RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "execution_result": str(EXEC_RESULT.relative_to(REPO)).replace("\\", "/"),
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "recommendation_ledger": str(RECOMMENDATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(RECOMMENDATION_LEDGER, rows)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "recommendation_ledger_sha256": sha256_file(RECOMMENDATION_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
