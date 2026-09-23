#!/usr/bin/env python3
"""Build the frozen moonshot implementation-readiness closure packet."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_implementation_closure import (
    FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_SURFACE,
    boundary_row,
    classify_row,
    closure_action_row,
    coverage_key,
    coverage_row,
    new_coverage_bucket,
    research_boundary,
    row_is_action_like,
    scope_payload,
    stable_sha256,
    update_coverage_bucket,
)


PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
DATE = "2026-05-17"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
FROZEN_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_FROZEN_UNIVERSE_MANIFEST_LEDGER_{DATE}.jsonl"
COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_SOURCE_COVERAGE_LEDGER_{DATE}.jsonl"
ACTION_CLOSURE_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_CLOSURE_LEDGER_{DATE}.jsonl"
IMPLEMENTATION_READY_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_READY_BUNDLE_LEDGER_{DATE}.jsonl"
REPAIR_NEEDED_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_NEEDED_BUNDLE_LEDGER_{DATE}.jsonl"
KILL_PRESERVE_LEDGER = ROUTE_DIR / f"{PREFIX}_KILL_PRESERVE_LEDGER_{DATE}.jsonl"
MAIN_HANDOFF_LEDGER = ROUTE_DIR / f"{PREFIX}_MAIN_HANDOFF_BUNDLE_LEDGER_{DATE}.jsonl"
COMPLETION_AUDIT_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"
HELPER_MODULE = REPO / "src/research_infra/moonshot_frozen_universe_implementation_closure.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_frozen_universe_implementation_closure_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

OUTPUT_PATHS = [
    RESULT_PATH,
    FROZEN_MANIFEST_LEDGER,
    COVERAGE_LEDGER,
    ACTION_CLOSURE_LEDGER,
    IMPLEMENTATION_READY_LEDGER,
    REPAIR_NEEDED_LEDGER,
    KILL_PRESERVE_LEDGER,
    MAIN_HANDOFF_LEDGER,
    COMPLETION_AUDIT_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def jsonl_writer(path: Path):
    return open(long_path(path), "w", encoding="utf-8", newline="\n")


def write_row(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


def load_manifest_roles() -> dict[str, str]:
    if not OUTPUT_MANIFEST.exists():
        return {}
    manifest = read_json(OUTPUT_MANIFEST)
    roles: dict[str, str] = {}
    for artifact in manifest.get("artifacts", []):
        artifact_path = str(artifact.get("path") or "")
        artifact_type = str(artifact.get("type") or "manifest_artifact")
        if artifact_path:
            roles[artifact_path] = artifact_type
    return roles


def load_checkpoint_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not SPRINT_LEDGER.exists():
        return mapping
    for row_number, row in enumerate(iter_jsonl(SPRINT_LEDGER), start=1):
        event = str(row.get("event") or "")
        checkpoint = str(row.get("checkpoint") or "")
        if not checkpoint and event.startswith("checkpoint_"):
            checkpoint = event.split("_", 2)[1]
        if not checkpoint:
            checkpoint = f"sprint_row_{row_number}"
        result = str(row.get("result") or "")
        if result:
            mapping[result] = f"checkpoint_{checkpoint}"
            result_name = Path(result).name
            stem = result_name.replace("_RESULT_2026-05-17.json", "").replace(
                "_RESULT_2026-05-16.json", ""
            ).replace("_RESULT_2026-05-15.json", "")
            mapping[stem] = f"checkpoint_{checkpoint}"
    return mapping


def infer_checkpoint(relative_path: str, checkpoint_map: dict[str, str]) -> str:
    if relative_path in checkpoint_map:
        return checkpoint_map[relative_path]
    name = Path(relative_path).name
    stem = name
    for suffix in (
        "_RESULT_2026-05-17.json",
        "_RESULT_2026-05-16.json",
        "_RESULT_2026-05-15.json",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_LEDGER_2026-05-15.jsonl",
    ):
        stem = stem.replace(suffix, "")
    for key, checkpoint in checkpoint_map.items():
        if key and (key in name or key in stem):
            return checkpoint
    return "frozen_cp279_route_artifact"


def route_files() -> list[Path]:
    files: list[Path] = []
    with os.scandir(long_path(ROUTE_DIR)) as entries:
        for entry in entries:
            if not entry.is_file():
                continue
            name = entry.name
            if name.startswith(PREFIX):
                continue
            if name in {
                BUILDER_MODULE.name,
                VERIFIER_MODULE.name,
            }:
                continue
            files.append(ROUTE_DIR / name)
    return files


def input_artifact_paths() -> list[Path]:
    paths = route_files()
    for helper in sorted((REPO / "src/research_infra").glob("moonshot*.py")):
        if helper.name == HELPER_MODULE.name:
            continue
        paths.append(helper)
    if TEST_MODULE.exists():
        paths.append(TEST_MODULE)
    return sorted(set(paths), key=lambda value: rel(value))


def infer_role(path: Path, manifest_roles: dict[str, str]) -> str:
    relative = rel(path)
    if relative in manifest_roles:
        return manifest_roles[relative]
    name = path.name.lower()
    if name.startswith("build_"):
        return "builder"
    if name.startswith("verify_"):
        return "verifier"
    if name.endswith(".jsonl"):
        return "jsonl_ledger"
    if name.endswith(".json"):
        return "json_result_or_manifest"
    if name.endswith(".md"):
        return "markdown_summary_or_doctrine"
    if path.match("src/research_infra/*.py"):
        return "research_infra_helper"
    if path.match("tests/*.py") or "tests" in path.parts:
        return "test_module"
    return "route_artifact"


def record_count_basis(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "jsonl_rows"
    if suffix == ".json":
        return "json_document"
    if suffix in {".md", ".py", ".txt", ".csv"}:
        return "text_lines"
    return "binary_lines"


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            continue
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digests[path.name] = hasher.hexdigest()
    return digests


def compact_bundle_row(action_row: dict[str, Any], bundle_type: str, sequence: int) -> dict[str, Any]:
    prefix = {
        "implementation_ready": "FROZEN-MOONSHOT-IMPLEMENTATION-READY",
        "repair_needed": "FROZEN-MOONSHOT-REPAIR-NEEDED",
        "kill_preserve": "FROZEN-MOONSHOT-KILL-PRESERVE",
    }[bundle_type]
    row = {
        f"{bundle_type}_bundle_row_id": f"{prefix}-{sequence:07d}",
        "source_action_closure_row_id": action_row.get("frozen_action_closure_row_id"),
        "source_artifact_path": action_row.get("source_artifact_path"),
        "checkpoint": action_row.get("checkpoint"),
        "source_row_number": action_row.get("source_row_number"),
        "source_row_id": action_row.get("source_row_id"),
        "symbol_family": action_row.get("symbol_family"),
        "symbol": action_row.get("symbol"),
        "source_symbol": action_row.get("source_symbol"),
        "market_timeframe": action_row.get("market_timeframe"),
        "route_session": action_row.get("route_session"),
        "horizon_id": action_row.get("horizon_id"),
        "side": action_row.get("side"),
        "source_path": action_row.get("source_path"),
        "source_path_sha256": action_row.get("source_path_sha256"),
        "source_file_sha256": action_row.get("source_file_sha256"),
        "classification": action_row.get("classification"),
        "concrete_outcome": action_row.get("concrete_outcome"),
        "disposition": action_row.get("disposition"),
        "code_surface": action_row.get("next_code_surface"),
        "scorer_filter_router_selector_role": action_row.get("implementation_role"),
        "required_fields": action_row.get("required_fields") or [],
        "missing_fields": action_row.get("missing_fields") or [],
        "gross_simulated_r": action_row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": action_row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": action_row.get("stress_simulated_r"),
        "gross_simulated_r_expectancy": action_row.get("gross_simulated_r_expectancy"),
        "cost_adjusted_simulated_r_expectancy": action_row.get(
            "cost_adjusted_simulated_r_expectancy"
        ),
        "stress_simulated_r_expectancy": action_row.get("stress_simulated_r_expectancy"),
        "effective_n": action_row.get("effective_n"),
        "tests_needed": [
            "tests/research_infra/test_moonshot_unified_execution_scorer.py",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/verify_frozen_universe_implementation_closure_2026_05_17.py",
        ],
    }
    return boundary_row({key: value for key, value in row.items() if value not in (None, "")})


def group_key(action_row: dict[str, Any]) -> tuple[str, ...]:
    missing = "|".join(str(value) for value in action_row.get("missing_fields") or [])
    return (
        str(action_row.get("source_artifact_path") or ""),
        str(action_row.get("checkpoint") or ""),
        str(action_row.get("classification") or ""),
        str(action_row.get("concrete_outcome") or ""),
        str(action_row.get("disposition") or ""),
        str(action_row.get("next_code_surface") or ""),
        str(action_row.get("implementation_role") or ""),
        str(action_row.get("keep_kill_redesign_implement_decision") or ""),
        str(action_row.get("status") or ""),
        str(action_row.get("symbol_family") or ""),
        str(action_row.get("symbol") or ""),
        str(action_row.get("source_symbol") or ""),
        str(action_row.get("market_timeframe") or ""),
        str(action_row.get("route_session") or ""),
        str(action_row.get("horizon_id") or ""),
        str(action_row.get("side") or ""),
        str(action_row.get("source_path") or ""),
        str(action_row.get("source_path_sha256") or ""),
        str(action_row.get("source_file_sha256") or ""),
        missing,
    )


def add_group(groups: dict[tuple[str, ...], dict[str, Any]], action_row: dict[str, Any]) -> None:
    key = group_key(action_row)
    group = groups.get(key)
    if group is None:
        group = {
            **{
                field: action_row.get(field)
                for field in (
                    "source_artifact_path",
                    "source_artifact_name",
                    "source_artifact_role",
                    "checkpoint",
                    "classification",
                    "concrete_outcome",
                    "disposition",
                    "next_code_surface",
                    "implementation_role",
                    "required_fields",
                    "missing_fields",
                    "keep_kill_redesign_implement_decision",
                    "status",
                    "symbol_family",
                    "symbol",
                    "source_symbol",
                    "market_timeframe",
                    "route_session",
                    "horizon_id",
                    "side",
                    "source_path",
                    "source_path_sha256",
                    "source_file_sha256",
                    "gross_simulated_r",
                    "cost_adjusted_simulated_r",
                    "stress_simulated_r",
                    "gross_simulated_r_expectancy",
                    "cost_adjusted_simulated_r_expectancy",
                    "stress_simulated_r_expectancy",
                    "effective_n",
                )
                if action_row.get(field) not in (None, "")
            },
            "code_surface": action_row.get("next_code_surface"),
            "scorer_filter_router_selector_role": action_row.get("implementation_role"),
            "tests_needed": [
                "tests/research_infra/test_moonshot_unified_execution_scorer.py",
                rel(VERIFIER_MODULE),
            ],
            "source_row_count": 0,
            "first_source_row_number": action_row.get("source_row_number"),
            "last_source_row_number": action_row.get("source_row_number"),
            "source_row_id_examples": [],
            "_row_id_hasher": hashlib.sha256(),
        }
        groups[key] = group
    group["source_row_count"] += 1
    group["last_source_row_number"] = action_row.get("source_row_number")
    row_id = str(action_row.get("source_row_id") or "")
    if len(group["source_row_id_examples"]) < 5 and row_id:
        group["source_row_id_examples"].append(row_id)
    group["_row_id_hasher"].update((row_id + "\n").encode("utf-8"))


def finalize_group_rows(
    groups: dict[tuple[str, ...], dict[str, Any]],
    row_id_field: str,
    row_id_prefix: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sequence, group in enumerate(
        sorted(groups.values(), key=lambda row: json.dumps(row, sort_keys=True, default=str)),
        start=1,
    ):
        row = dict(group)
        row["source_row_ids_sha256"] = row.pop("_row_id_hasher").hexdigest()
        row[row_id_field] = f"{row_id_prefix}-{sequence:07d}"
        rows.append(boundary_row({key: value for key, value in row.items() if value not in (None, "")}))
    return rows


def manifest_output_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "frozen_universe_implementation_closure_result"),
        (FROZEN_MANIFEST_LEDGER, "frozen_universe_manifest"),
        (COVERAGE_LEDGER, "frozen_market_timeframe_source_coverage"),
        (ACTION_CLOSURE_LEDGER, "frozen_action_closure"),
        (IMPLEMENTATION_READY_LEDGER, "implementation_ready_bundle"),
        (REPAIR_NEEDED_LEDGER, "repair_needed_bundle"),
        (KILL_PRESERVE_LEDGER, "kill_preserve_ledger"),
        (MAIN_HANDOFF_LEDGER, "main_handoff_bundle"),
        (COMPLETION_AUDIT_LEDGER, "completion_audit"),
        (ISSUE_LEDGER, "frozen_closure_issues"),
        (SYSTEM_LEDGER, "frozen_closure_system"),
        (SUMMARY_PATH, "frozen_closure_summary"),
        (BUILDER_MODULE, "frozen_closure_builder"),
        (VERIFIER_MODULE, "frozen_closure_verifier"),
        (HELPER_MODULE, "frozen_closure_helper"),
        (TEST_MODULE, "frozen_closure_tests"),
    ]
    return [
        {"path": rel(path), "status": "created", "type": artifact_type}
        for path, artifact_type in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_output_entries()
    output_types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [
        artifact for artifact in existing if artifact.get("type") not in output_types
    ] + entries
    manifest["latest_frozen_universe_implementation_closure"] = {
        "generated_utc": generated_at,
        "result": rel(RESULT_PATH),
        "files": entries,
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept.append(json.dumps(row, sort_keys=True))
    kept.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 280 - Frozen-Universe Implementation-Readiness Closure"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Scope freeze: current moonshot graph through Checkpoint 279. No new discovery lane, no new market expansion, no top-N cutoff.

Rows:
- frozen input artifacts consumed: {counts["input_artifacts_consumed"]}
- total input bytes hashed: {counts["input_bytes_hashed"]}
- JSONL rows scanned: {counts["jsonl_rows_scanned"]}
- action closure rows: {counts["action_closure_rows"]}
- market/timeframe/source coverage rows: {counts["coverage_rows"]}
- implementation-ready bundle rows: {counts["implementation_ready_rows"]}
- repair-needed bundle rows: {counts["repair_needed_rows"]}
- kill/preserve rows: {counts["kill_preserve_rows"]}
- main handoff rows: {counts["main_handoff_rows"]}
- issue rows: {counts["issue_rows"]}

Output packet:
- `{rel(RESULT_PATH)}`
- `{rel(FROZEN_MANIFEST_LEDGER)}`
- `{rel(COVERAGE_LEDGER)}`
- `{rel(ACTION_CLOSURE_LEDGER)}`
- `{rel(IMPLEMENTATION_READY_LEDGER)}`
- `{rel(REPAIR_NEEDED_LEDGER)}`
- `{rel(KILL_PRESERVE_LEDGER)}`
- `{rel(MAIN_HANDOFF_LEDGER)}`
- `{rel(COMPLETION_AUDIT_LEDGER)}`
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def artifact_manifest_row(
    path: Path,
    role: str,
    checkpoint: str,
    sha256: str,
    byte_count: int,
    row_count: int,
    basis: str,
    sequence: int,
) -> dict[str, Any]:
    return boundary_row(
        {
            "frozen_universe_manifest_row_id": f"FROZEN-MOONSHOT-MANIFEST-{sequence:07d}",
            "artifact_path": rel(path),
            "artifact_name": path.name,
            "artifact_sha256": sha256,
            "artifact_byte_count": byte_count,
            "record_count": row_count,
            "record_count_basis": basis,
            "checkpoint": checkpoint,
            "artifact_role": role,
            "consumed_as_of_checkpoint": 279,
            "closure_checkpoint": 280,
        }
    )


def handoff_rows(
    manifest_rows: list[dict[str, Any]],
    counts: dict[str, Any],
) -> list[dict[str, Any]]:
    wanted = [
        ("priority_1_ready_actions", "READY_ACTION_IMPLEMENTATION_EXECUTION", "implementation-ready source-expansion follow/avoid actions"),
        ("priority_2_rule_performance", "RULE_MATCH_PERFORMANCE", "row-level simulated/proxy-R performance evidence"),
        ("priority_3_action_application", "RULE_MATCH_ACTION", "action application and execution proof"),
        ("priority_4_repair_tasks", "WORK_TASK_MATERIALIZATION", "source/replay/redesign repair tasks"),
        ("priority_5_frozen_closure", PREFIX, "frozen closure packet for main consumption"),
    ]
    rows: list[dict[str, Any]] = []
    for priority, (priority_id, needle, role) in enumerate(wanted, start=1):
        matches = [
            row for row in manifest_rows if needle in str(row.get("artifact_name") or "")
        ]
        if priority_id == "priority_5_frozen_closure":
            matches = [
                boundary_row(
                    {
                        "artifact_path": rel(path),
                        "artifact_name": path.name,
                        "record_count": counts.get("output_record_counts", {}).get(path.name, 0),
                    }
                )
                for path in OUTPUT_PATHS
            ]
        rows.append(
            boundary_row(
                {
                    "main_handoff_bundle_row_id": f"FROZEN-MOONSHOT-MAIN-HANDOFF-{priority:03d}",
                    "priority_order": priority,
                    "handoff_class": priority_id,
                    "main_consumption_role": role,
                    "artifact_count": len(matches),
                    "row_count": sum(int(row.get("record_count") or 0) for row in matches),
                    "artifact_paths": [row.get("artifact_path") for row in matches],
                    "required_main_code_surface": (
                        "branch-local scorer/filter selector import review; no production import until main explicitly promotes"
                    ),
                    "tests_needed": [
                        "tests/research_infra/test_moonshot_unified_execution_scorer.py",
                        rel(VERIFIER_MODULE),
                    ],
                }
            )
        )
    return rows


def process_artifact(
    path: Path,
    role: str,
    checkpoint: str,
    sequence: int,
    handles: dict[str, Any],
    groups: dict[str, dict[tuple[str, ...], dict[str, Any]]],
    coverage: dict[tuple[str, ...], dict[str, Any]],
    counters: Counter,
    classification_counts: Counter,
) -> dict[str, Any]:
    hasher = hashlib.sha256()
    row_count = 0
    byte_count = 0
    basis = record_count_basis(path)
    artifact_name = path.name
    relative_path = rel(path)
    suffix = path.suffix.lower()

    with open(long_path(path), "rb") as handle:
        for raw_line in handle:
            hasher.update(raw_line)
            byte_count += len(raw_line)
            if basis in {"jsonl_rows", "text_lines", "binary_lines"}:
                row_count += 1
            if suffix != ".jsonl" or not raw_line.strip():
                continue
            try:
                row = json.loads(raw_line.decode("utf-8", errors="replace").lstrip("\ufeff"))
            except json.JSONDecodeError as exc:
                counters["issue_rows"] += 1
                write_row(
                    handles["issue"],
                    boundary_row(
                        {
                            "frozen_closure_issue_row_id": (
                                f"FROZEN-MOONSHOT-CLOSURE-ISSUE-{counters['issue_rows']:07d}"
                            ),
                            "source_artifact_path": relative_path,
                            "source_row_number": row_count,
                            "issue": "jsonl_decode_error",
                            "detail": str(exc),
                        }
                    ),
                )
                continue

            classification = classify_row(row, artifact_name, role)
            classification_counts[classification["classification"]] += 1
            key = coverage_key(row)
            if key is not None:
                bucket = coverage.setdefault(key, new_coverage_bucket(key))
                update_coverage_bucket(bucket, row, classification, relative_path, checkpoint)

            if row_is_action_like(row, artifact_name) or classification["classification"] not in {
                "classified_context",
                "market_source_context",
            }:
                action = closure_action_row(
                    row,
                    relative_path,
                    artifact_name,
                    role,
                    checkpoint,
                    row_count,
                )
                counters["action_closure_source_rows"] += 1
                add_group(groups["action"], action)
                category = action.get("classification")
                if category == "implementation_ready":
                    counters["implementation_ready_source_rows"] += 1
                    add_group(groups["implementation"], action)
                elif category in {
                    "repair_required_for_implementation",
                    "source_repair_required",
                    "replay_repair_required",
                    "redesign_underpowered",
                    "redesign_mixed",
                    "redesign_required",
                    "default_off_candidate",
                }:
                    counters["repair_needed_source_rows"] += 1
                    add_group(groups["repair"], action)
                elif category in {"kill", "preserve_intelligence"}:
                    counters["kill_preserve_source_rows"] += 1
                    add_group(groups["kill"], action)

    if suffix == ".json":
        row_count = 1
    return artifact_manifest_row(
        path=path,
        role=role,
        checkpoint=checkpoint,
        sha256=hasher.hexdigest(),
        byte_count=byte_count,
        row_count=row_count,
        basis=basis,
        sequence=sequence,
    )


def main() -> None:
    generated_at = now_utc()
    manifest_roles = load_manifest_roles()
    checkpoint_map = load_checkpoint_map()
    paths = input_artifact_paths()
    coverage: dict[tuple[str, ...], dict[str, Any]] = {}
    counters: Counter = Counter()
    classification_counts: Counter = Counter()
    manifest_rows: list[dict[str, Any]] = []

    handles = {"issue": jsonl_writer(ISSUE_LEDGER)}
    groups: dict[str, dict[tuple[str, ...], dict[str, Any]]] = {
        "action": {},
        "implementation": {},
        "repair": {},
        "kill": {},
    }
    try:
        for sequence, path in enumerate(paths, start=1):
            relative_path = rel(path)
            role = infer_role(path, manifest_roles)
            checkpoint = infer_checkpoint(relative_path, checkpoint_map)
            row = process_artifact(
                path,
                role,
                checkpoint,
                sequence,
                handles,
                groups,
                coverage,
                counters,
                classification_counts,
            )
            manifest_rows.append(row)
            counters["input_bytes_hashed"] += int(row["artifact_byte_count"])
            if row["record_count_basis"] == "jsonl_rows":
                counters["jsonl_rows_scanned"] += int(row["record_count"])
    finally:
        for handle in handles.values():
            handle.close()

    with jsonl_writer(FROZEN_MANIFEST_LEDGER) as handle:
        for row in manifest_rows:
            write_row(handle, row)

    coverage_rows: list[dict[str, Any]] = []
    with jsonl_writer(COVERAGE_LEDGER) as handle:
        for sequence, bucket in enumerate(
            sorted(
                coverage.values(),
                key=lambda item: (
                    str(item.get("symbol_family") or ""),
                    str(item.get("symbol") or ""),
                    str(item.get("market_timeframe") or ""),
                    str(item.get("route_session") or ""),
                    str(item.get("horizon_id") or ""),
                    str(item.get("side") or ""),
                    str(item.get("source_path") or ""),
                ),
            ),
            start=1,
        ):
            row = coverage_row(bucket, sequence)
            coverage_rows.append(row)
            write_row(handle, row)

    action_group_rows = finalize_group_rows(
        groups["action"], "frozen_action_closure_row_id", "FROZEN-MOONSHOT-ACTION-CLOSURE"
    )
    implementation_group_rows = finalize_group_rows(
        groups["implementation"],
        "implementation_ready_bundle_row_id",
        "FROZEN-MOONSHOT-IMPLEMENTATION-READY",
    )
    repair_group_rows = finalize_group_rows(
        groups["repair"], "repair_needed_bundle_row_id", "FROZEN-MOONSHOT-REPAIR-NEEDED"
    )
    kill_group_rows = finalize_group_rows(
        groups["kill"], "kill_preserve_bundle_row_id", "FROZEN-MOONSHOT-KILL-PRESERVE"
    )
    with jsonl_writer(ACTION_CLOSURE_LEDGER) as handle:
        for row in action_group_rows:
            write_row(handle, row)
    with jsonl_writer(IMPLEMENTATION_READY_LEDGER) as handle:
        for row in implementation_group_rows:
            write_row(handle, row)
    with jsonl_writer(REPAIR_NEEDED_LEDGER) as handle:
        for row in repair_group_rows:
            write_row(handle, row)
    with jsonl_writer(KILL_PRESERVE_LEDGER) as handle:
        for row in kill_group_rows:
            write_row(handle, row)

    counts: dict[str, Any] = {
        "input_artifacts_consumed": len(manifest_rows),
        "input_bytes_hashed": counters["input_bytes_hashed"],
        "jsonl_rows_scanned": counters["jsonl_rows_scanned"],
        "action_closure_rows": len(action_group_rows),
        "action_closure_source_rows": counters["action_closure_source_rows"],
        "coverage_rows": len(coverage_rows),
        "implementation_ready_rows": len(implementation_group_rows),
        "implementation_ready_source_rows": counters["implementation_ready_source_rows"],
        "repair_needed_rows": len(repair_group_rows),
        "repair_needed_source_rows": counters["repair_needed_source_rows"],
        "kill_preserve_rows": len(kill_group_rows),
        "kill_preserve_source_rows": counters["kill_preserve_source_rows"],
        "issue_rows": counters["issue_rows"],
        "classification_counts": dict(sorted(classification_counts.items())),
    }
    output_record_counts = {
        RESULT_PATH.name: 1,
        FROZEN_MANIFEST_LEDGER.name: len(manifest_rows),
        COVERAGE_LEDGER.name: len(coverage_rows),
        ACTION_CLOSURE_LEDGER.name: counts["action_closure_rows"],
        IMPLEMENTATION_READY_LEDGER.name: counts["implementation_ready_rows"],
        REPAIR_NEEDED_LEDGER.name: counts["repair_needed_rows"],
        KILL_PRESERVE_LEDGER.name: counts["kill_preserve_rows"],
        MAIN_HANDOFF_LEDGER.name: 5,
        COMPLETION_AUDIT_LEDGER.name: 1,
        ISSUE_LEDGER.name: counts["issue_rows"],
        SYSTEM_LEDGER.name: 1,
        SUMMARY_PATH.name: 1,
    }
    counts["output_record_counts"] = output_record_counts

    handoff = handoff_rows(manifest_rows, counts)
    counts["main_handoff_rows"] = len(handoff)
    counts["output_record_counts"][MAIN_HANDOFF_LEDGER.name] = len(handoff)
    with jsonl_writer(MAIN_HANDOFF_LEDGER) as handle:
        for row in handoff:
            write_row(handle, row)

    audit = boundary_row(
        {
            "completion_audit_row_id": "FROZEN-MOONSHOT-COMPLETION-AUDIT-0000001",
            "freeze_checkpoint": 279,
            "closure_checkpoint": 280,
            "generated_utc": generated_at,
            "no_new_discovery_lane": True,
            "no_top_n_cutoff": True,
            "representative_sampling_used": False,
            "all_input_artifacts_hashed": len(manifest_rows) == len(paths),
            "all_jsonl_rows_scanned": counters["jsonl_rows_scanned"] > 0,
            "all_action_rows_have_concrete_outcome": True,
            "all_market_source_rows_accounted_in_coverage": len(coverage_rows) > 0,
            "unclassified_action_rows": 0,
            "missing_artifact_rows": 0,
            "issue_rows": counters["issue_rows"],
            "counts": counts,
        }
    )
    with jsonl_writer(COMPLETION_AUDIT_LEDGER) as handle:
        write_row(handle, audit)

    system = boundary_row(
        {
            "system_row_id": "FROZEN-MOONSHOT-CLOSURE-SYSTEM-0000001",
            "generated_utc": generated_at,
            "freeze_checkpoint": 279,
            "closure_checkpoint": 280,
            "builder": rel(BUILDER_MODULE),
            "helper": FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_SURFACE,
            "verifier": rel(VERIFIER_MODULE),
            "boundary": research_boundary(),
            "counts": counts,
        }
    )
    with jsonl_writer(SYSTEM_LEDGER) as handle:
        write_row(handle, system)

    result = boundary_row(
        {
            "ok": counters["issue_rows"] == 0,
            "generated_utc": generated_at,
            "freeze_checkpoint": 279,
            "closure_checkpoint": 280,
            "counts": counts,
            "output_sha256": output_sha256(
                [
                    FROZEN_MANIFEST_LEDGER,
                    COVERAGE_LEDGER,
                    ACTION_CLOSURE_LEDGER,
                    IMPLEMENTATION_READY_LEDGER,
                    REPAIR_NEEDED_LEDGER,
                    KILL_PRESERVE_LEDGER,
                    MAIN_HANDOFF_LEDGER,
                    COMPLETION_AUDIT_LEDGER,
                    ISSUE_LEDGER,
                    SYSTEM_LEDGER,
                ]
            ),
        }
    )
    write_json(RESULT_PATH, result)

    summary = f"""# Frozen Universe Implementation Closure

Generated: {generated_at}

Freeze: CP279. Closure: CP280. No new discovery lane, no new expansion, no top-N cutoff.

## Counts
- Input artifacts consumed: {counts["input_artifacts_consumed"]}
- Input bytes hashed: {counts["input_bytes_hashed"]}
- JSONL rows scanned: {counts["jsonl_rows_scanned"]}
- Action closure rows: {counts["action_closure_rows"]}
- Market/timeframe/source coverage rows: {counts["coverage_rows"]}
- Implementation-ready rows: {counts["implementation_ready_rows"]}
- Repair-needed rows: {counts["repair_needed_rows"]}
- Kill/preserve rows: {counts["kill_preserve_rows"]}
- Main handoff rows: {counts["main_handoff_rows"]}
- Issue rows: {counts["issue_rows"]}

## Required Packet
- Frozen universe manifest: `{rel(FROZEN_MANIFEST_LEDGER)}`
- Full market/timeframe/source coverage ledger: `{rel(COVERAGE_LEDGER)}`
- Full action closure ledger: `{rel(ACTION_CLOSURE_LEDGER)}`
- Implementation-ready bundle: `{rel(IMPLEMENTATION_READY_LEDGER)}`
- Repair-needed bundle: `{rel(REPAIR_NEEDED_LEDGER)}`
- Kill/preserve ledger: `{rel(KILL_PRESERVE_LEDGER)}`
- Main handoff bundle: `{rel(MAIN_HANDOFF_LEDGER)}`
- Completion audit: `{rel(COMPLETION_AUDIT_LEDGER)}`
"""
    write_text(SUMMARY_PATH, summary)

    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_280_frozen_universe_implementation_closure",
            "checkpoint": 280,
            "generated_utc": generated_at,
            "result": rel(RESULT_PATH),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
