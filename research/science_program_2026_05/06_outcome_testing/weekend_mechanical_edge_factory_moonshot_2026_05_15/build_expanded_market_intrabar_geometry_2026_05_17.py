#!/usr/bin/env python3
"""Build expanded-market intrabar high-low geometry rows from CP216 performance rows."""

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

from src.research_infra.moonshot_expanded_market_intrabar_geometry import (
    EXPANDED_MARKET_INTRABAR_GEOMETRY_SURFACE,
    aggregate_intrabar_rows,
    geometry_row_from_profile,
    intrabar_profile,
    noncomputable_row,
    profile_key,
    research_boundary,
    system_intrabar_rows,
)
from src.research_infra.moonshot_expanded_market_proxy_r_performance import load_ohlc_rows


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_intrabar_geometry.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_intrabar_geometry_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
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


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_intrabar_geometry_result"),
        (ROW_LEDGER, "expanded_market_intrabar_geometry_rows"),
        (AGGREGATE_LEDGER, "expanded_market_intrabar_geometry_aggregates"),
        (PROOF_LEDGER, "expanded_market_intrabar_geometry_source_access_proofs"),
        (SYSTEM_LEDGER, "expanded_market_intrabar_geometry_system"),
        (SUMMARY_PATH, "expanded_market_intrabar_geometry_summary"),
        (BUILDER_MODULE, "expanded_market_intrabar_geometry_builder"),
        (VERIFIER_MODULE, "expanded_market_intrabar_geometry_verifier"),
        (HELPER_MODULE, "expanded_market_intrabar_geometry_helper"),
        (TEST_MODULE, "expanded_market_intrabar_geometry_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    existing = manifest.setdefault("artifacts", [])
    new_keys = {(entry["path"], entry["type"]) for entry in entries}
    manifest["artifacts"] = [
        entry for entry in existing if (entry.get("path"), entry.get("type")) not in new_keys
    ] + entries
    manifest["latest_expanded_market_intrabar_geometry"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    kept_lines.append(stripped)
                    continue
                if payload.get("checkpoint") == 219 and payload.get("event") == "expanded_market_intrabar_geometry":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 219 - Expanded-Market Intrabar Geometry"
    text = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    start = text.find(marker)
    if start != -1:
        next_start = text.find("\n## Checkpoint ", start + len(marker))
        text = text[:start].rstrip() + ("\n\n" + text[next_start:].lstrip() if next_start != -1 else "\n")
    addition = f"""
{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 218. CP216 broad-market horizon-close proxy rows were replayed with OHLC high-low target/stop path geometry to separate target-first, stop-first, neither, and ambiguous same-bar cases.

Rows:
- input expanded-market performance rows: {counts['input_performance_rows']}
- intrabar geometry rows: {counts['intrabar_geometry_rows']}
- aggregate intrabar rows: {counts['aggregate_rows']}
- source/access proof rows: {counts['source_access_proof_rows']}
- unique intrabar profile keys replayed: {counts['unique_intrabar_profile_keys']}
- implement intrabar rows: {counts['implement_rows']}
- avoid-intelligence intrabar rows: {counts['avoid_rows']}
- kill intrabar rows: {counts['kill_rows']}
- redesign intrabar rows: {counts['redesign_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: compare intrabar geometry, side-pair, and temporal decisions into concrete branch-local implementation-selection rows.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Intrabar Geometry",
            "",
            "This checkpoint replays CP216 broad-market rows with OHLC high-low target/stop path geometry, preserving ambiguous same-bar cases explicitly.",
            "",
            "## Counts",
            "",
            f"- Input performance rows: `{counts['input_performance_rows']}`",
            f"- Intrabar geometry rows: `{counts['intrabar_geometry_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Source/access proof rows: `{counts['source_access_proof_rows']}`",
            f"- Unique intrabar profile keys replayed: `{counts['unique_intrabar_profile_keys']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Path Counts",
            "",
            f"`{json.dumps(counts['path_order_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Compare intrabar geometry, side-pair, and temporal decisions into branch-local implementation-selection rows.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    performance_rows = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    ohlc_cache: dict[str, list[dict[str, Any]]] = {}
    profile_cache: dict[tuple[str, ...], dict[str, Any]] = {}
    geometry_rows: list[dict[str, Any]] = []
    proof_rows: list[dict[str, Any]] = []

    for performance_row in performance_rows:
        key = profile_key(performance_row)
        if key not in profile_cache:
            source_path = str(performance_row.get("source_path"))
            if source_path not in ohlc_cache:
                ohlc_cache[source_path], _ = load_ohlc_rows(REPO, source_path)
            profile_cache[key] = intrabar_profile(performance_row, ohlc_cache[source_path])
        profile = profile_cache[key]
        if profile.get("profile_status") == "EXPANDED_MARKET_INTRABAR_GEOMETRY_REPLAYED":
            geometry_rows.append(geometry_row_from_profile(performance_row, profile, len(geometry_rows) + 1))
        else:
            proof_rows.append(noncomputable_row(performance_row, profile, len(proof_rows) + 1))

    aggregate_rows = aggregate_intrabar_rows(geometry_rows)
    system_rows = system_intrabar_rows(
        geometry_rows,
        aggregate_rows,
        proof_rows,
        len(performance_rows),
        len(profile_cache),
    )
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in geometry_rows)
    classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in geometry_rows)
    path_counts: Counter[str] = Counter()
    for row in geometry_rows:
        path_counts.update(row.get("path_order_counts") or {})
    counts = {
        "input_result_ok": bool(input_result.get("ok")),
        "input_performance_rows": len(performance_rows),
        "intrabar_geometry_rows": len(geometry_rows),
        "aggregate_rows": len(aggregate_rows),
        "source_access_proof_rows": len(proof_rows),
        "system_rows": len(system_rows),
        "unique_intrabar_profile_keys": len(profile_cache),
        "source_path_count": len({row.get("source_path") for row in geometry_rows}),
        "symbol_count": len({row.get("symbol") for row in geometry_rows}),
        "decision_counts": dict(sorted(decisions.items())),
        "class_counts": dict(sorted(classes.items())),
        "path_order_counts": dict(sorted(path_counts.items())),
        "implement_rows": sum(str(decision).startswith("IMPLEMENT") for decision in decisions.elements()),
        "avoid_rows": sum("AVOID" in str(decision) for decision in decisions.elements()),
        "kill_rows": sum(str(decision).startswith("KILL") for decision in decisions.elements()),
        "redesign_rows": sum(str(decision).startswith("REDESIGN") for decision in decisions.elements()),
    }

    write_jsonl(ROW_LEDGER, geometry_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(PROOF_LEDGER, proof_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [ROW_LEDGER, AGGREGATE_LEDGER, PROOF_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "input_performance_ledger": str(INPUT_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_access_proof_ledger": str(PROOF_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_intrabar_geometry_surface": EXPANDED_MARKET_INTRABAR_GEOMETRY_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 219,
            "event": "expanded_market_intrabar_geometry",
            "generated_utc": generated_at,
            "input_performance_rows": counts["input_performance_rows"],
            "intrabar_geometry_rows": counts["intrabar_geometry_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "source_access_proof_rows": counts["source_access_proof_rows"],
            "unique_intrabar_profile_keys": counts["unique_intrabar_profile_keys"],
            "continuation": "continue to implementation-selection rows from intrabar, side-pair, and temporal decisions.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
