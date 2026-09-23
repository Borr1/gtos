#!/usr/bin/env python3
"""Build branch-local source lookup evidence for repaired-proxy repair acquisition requirements."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_repair_acquisition_lookup import (
    REPAIR_ACQUISITION_LOOKUP_SURFACE,
    field_fulfillment_rows,
    lookup_bucket_rows,
    lookup_execution_rows,
    repair_rerun_readiness_rows,
    rerun_gate_rows,
    research_boundary,
    scan_source_records,
    source_candidate_lookup_rows,
    source_names_by_requirement,
)


ACQ_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_FIELD_ACQUISITION"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_WORK_EXECUTION"
SCORE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD"
SPEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_ACQUISITION_SOURCE_LOOKUP"

ACQ_RESULT = ROUTE_DIR / f"{ACQ_PREFIX}_RESULT_2026-05-17.json"
ACQUISITION_REQUIREMENT_LEDGER = ROUTE_DIR / f"{ACQ_PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LEDGER = ROUTE_DIR / f"{ACQ_PREFIX}_SOURCE_CANDIDATE_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
EXACT_PROXY_BRIDGE_LEDGER = ROUTE_DIR / f"{SPEC_PREFIX}_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
REBUILT_SCORE_BRIDGE_LEDGER = ROUTE_DIR / f"{SCORE_PREFIX}_REBUILT_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_acquisition_lookup.py"
ACQ_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_repair_acquisition.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_repair_acquisition_source_lookup_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_CANDIDATE_LOOKUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CANDIDATE_LOOKUP_LEDGER_2026-05-17.jsonl"
LOOKUP_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_LOOKUP_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_FULFILLMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_FIELD_FULFILLMENT_LEDGER_2026-05-17.jsonl"
REPAIR_RERUN_READINESS_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_RERUN_READINESS_LEDGER_2026-05-17.jsonl"
RERUN_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"
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
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-SRCMAN-{len(rows) + 1:05d}",
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
    output.setdefault("repair_acquisition_lookup_surface", REPAIR_ACQUISITION_LOOKUP_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def existing(paths: Iterable[Path]) -> list[Path]:
    output: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.exists() and path not in seen:
            output.append(path)
            seen.add(path)
    return sorted(output, key=lambda item: item.as_posix())


def source_path_map() -> dict[str, list[Path]]:
    shadow = REPO / "shadow_logs"
    knowledge = REPO / "knowledge_base"
    pipeline = REPO / "pipeline_state"
    data = REPO / "data"
    trade_records = list((knowledge / "trade_records").rglob("*.json")) if (knowledge / "trade_records").exists() else []
    no_trade_docs = list((knowledge / "no_trades").rglob("*.yaml")) if (knowledge / "no_trades").exists() else []
    pipeline_json = list(pipeline.glob("*.json")) if pipeline.exists() else []
    mt5_deals = list((data / "account_history").glob("mt5_deals_*.jsonl")) if (data / "account_history").exists() else []
    return {
        "candidate_records_or_decision_rows": existing(
            [
                shadow / "candidate_registry_audit.jsonl",
                shadow / "decision_layer_diagnostics_join.jsonl",
                knowledge / "index/_trade_index.json",
                knowledge / "index/trade_record_inventory_index_2026-05-05.json",
            ]
        ),
        "shadow_candidate_feature_rows": existing(
            [
                shadow / "candidate_features_log.jsonl",
                shadow / "candidate_mso_snapshot_joins.jsonl",
                shadow / "candidate_path_follow.jsonl",
                shadow / "candidate_path_contract_audit.jsonl",
                shadow / "candidate_ltf_path_order.jsonl",
            ]
        ),
        "trade_record_rows": existing(trade_records + [knowledge / "index/_trade_index.json"]),
        "mt5_order_history": existing(mt5_deals + list(shadow.glob("pending_limit_lifecycle*.jsonl"))),
        "mt5_deal_history": existing(mt5_deals),
        "broker_actual_r_exports": existing(
            [
                shadow / "broker_actual_r_audit.jsonl",
                shadow / "trade_index_lifecycle_audit.jsonl",
                shadow / "pending_limit_lifecycle_join_backfill.jsonl",
            ]
        ),
        "candidate_lock_or_snapshot_metadata": existing(
            [
                shadow / "candidate_mso_snapshot_joins.jsonl",
                shadow / "candidate_registry_audit.jsonl",
                shadow / "opportunity_lifecycle_audit.jsonl",
            ]
            + pipeline_json
        ),
        "decision_packet_metadata": existing(trade_records + no_trade_docs),
        "execution_intent_metadata": existing(list(shadow.glob("pending_limit_lifecycle*.jsonl")) + pipeline_json),
        "scope_registry_rows": existing(
            [
                ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / f"{SPEC_PREFIX}_DEFAULT_OFF_SCOPE_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / f"{SPEC_PREFIX}_AVOID_SCOPE_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / f"{SPEC_PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl",
            ]
        ),
        "execution_spec_rows": existing(
            [
                EXACT_PROXY_BRIDGE_LEDGER,
                ROUTE_DIR / f"{SPEC_PREFIX}_DEFAULT_OFF_SCORER_SPEC_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / f"{SPEC_PREFIX}_AVOID_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / f"{SPEC_PREFIX}_REPAIR_TASK_LEDGER_2026-05-17.jsonl",
                REBUILT_SCORE_BRIDGE_LEDGER,
            ]
        ),
        "numeric_shadow_event_rows": existing(
            [
                ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_SHADOW_SCORER_COMPUTE_NUMERIC_EVENT_SCORE_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl",
                ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl",
            ]
        ),
    }


def iter_json_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            if isinstance(nested, dict):
                yield nested
            elif isinstance(nested, list):
                for item in nested[:100]:
                    if isinstance(item, dict):
                        yield item
    elif isinstance(value, list):
        for item in value[:100]:
            if isinstance(item, dict):
                yield item


def iter_source_records(paths: list[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError:
                        yield {"source_path": path.relative_to(REPO).as_posix(), "line_number": line_number}
                        continue
                    if isinstance(value, dict):
                        value.setdefault("source_path", path.relative_to(REPO).as_posix())
                        yield value
                    else:
                        yield {"source_path": path.relative_to(REPO).as_posix(), "value": value}
        elif suffix == ".json":
            try:
                with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
                    value = json.load(handle)
            except (json.JSONDecodeError, OSError):
                yield {"source_path": path.relative_to(REPO).as_posix()}
                continue
            for row in iter_json_dicts(value):
                row = dict(row)
                row.setdefault("source_path", path.relative_to(REPO).as_posix())
                yield row
        else:
            with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
                yield {"source_path": path.relative_to(REPO).as_posix(), "raw_text": handle.read()}


def index_by(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(field)): row for row in rows if row.get(field)}


def enriched_requirements(
    requirement_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    exact_bridge_rows: list[dict[str, Any]],
    rebuilt_bridge_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    execution_by_id = index_by(execution_rows, "repair_execution_row_id")
    exact_by_id = index_by(exact_bridge_rows, "exact_proxy_bridge_row_id")
    rebuilt_by_id = index_by(rebuilt_bridge_rows, "score_rebuilt_bridge_row_id")
    output: list[dict[str, Any]] = []
    for requirement in requirement_rows:
        enriched = dict(requirement)
        execution = execution_by_id.get(str(requirement.get("input_repair_execution_row_id")), {})
        for key in ("input_score_rebuilt_bridge_row_id", "source_component", "symbol", "route_session", "horizon_id"):
            if not enriched.get(key) and execution.get(key):
                enriched[key] = execution.get(key)
        exact = exact_by_id.get(str(enriched.get("input_exact_proxy_bridge_row_id")), {})
        for key in (
            "input_repaired_proxy_event_application_row_id",
            "input_numeric_result_row_id",
            "primitive_flag",
            "source_component",
            "symbol",
            "route_session",
            "horizon_id",
        ):
            if not enriched.get(key) and exact.get(key):
                enriched[key] = exact.get(key)
        rebuilt = rebuilt_by_id.get(str(enriched.get("input_score_rebuilt_bridge_row_id")), {})
        for key in ("input_score_scope_summary_row_id", "aggregate_scope_key", "primitive_flag"):
            if not enriched.get(key) and rebuilt.get(key):
                enriched[key] = rebuilt.get(key)
        output.append(enriched)
    return output


def update_output_manifest(entries: list[tuple[Path, str]]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    artifacts = manifest.setdefault("artifacts", [])
    existing_paths = {str(item.get("path")) for item in artifacts}
    for path, artifact_type in entries:
        rel = path.relative_to(REPO).as_posix()
        if rel in existing_paths:
            continue
        artifacts.append({"path": rel, "status": "created", "type": artifact_type})
        existing_paths.add(rel)
    write_json(OUTPUT_MANIFEST, manifest)


def system_action_row(counts: dict[str, int], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    return with_common(
        {
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-LOOKUP-SYSTEM-0001",
            "recommendation": (
                "Keep repair execution and exact/proxy rerun gated until source lookup produces row-unique acquired "
                "fields; preserve not-found lookup proof by source candidate and requirement."
            ),
            "next_branch_local_actions": [
                "inspect_not_fulfilled_lookup_rows_by_source_family",
                "add_new_branch_local_source_paths_only_if_identifiers_exist",
                "rerun_repair_execution_after_row_unique_field_acquisition",
                "rerun_exact_proxy_bridge_only_after_repair_rerun_ready_rows_exist",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Repair Acquisition Source Lookup",
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
                "Rerun repair execution only after row-unique acquired fields exist. The exact/proxy bridge rerun "
                "remains behind the repair readiness gate."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 181 - Repair Acquisition Source Lookup\n"
    existing_text = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing_text = handle.read()
    if marker in existing_text:
        write_text(ACTIVE_LEDGER, existing_text.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 181 - Repair Acquisition Source Lookup

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 180. Acquisition requirements were run through branch-local source lookups with exact join-key acquisition required for field fulfillment.

Outputs:

- `{counts['lookup_execution_rows']}` requirement-source lookup execution rows from `{counts['acquisition_requirement_rows']}` acquisition requirements.
- `{counts['source_candidate_lookup_rows']}` source-candidate lookup rows over `{counts['source_manifest_rows']}` hashed source/code files.
- `{counts['field_fulfillment_rows']}` field fulfillment rows and `{counts['repair_rerun_readiness_rows']}` repair rerun readiness rows.
- `{counts['repair_rerun_ready_rows']}` repair rows are ready for repair rerun after this lookup pass.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: inspect not-fulfilled lookup rows by source family, add only row-key-bearing branch-local sources, then rerun repair execution before any exact/proxy bridge rerun.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    acq_result = read_json(ACQ_RESULT)
    requirement_rows_raw = read_jsonl(ACQUISITION_REQUIREMENT_LEDGER)
    source_candidate_rows_raw = read_jsonl(SOURCE_CANDIDATE_LEDGER)
    execution_rows = read_jsonl(REPAIR_EXECUTION_LEDGER)
    exact_bridge_rows = read_jsonl(EXACT_PROXY_BRIDGE_LEDGER)
    rebuilt_bridge_rows = read_jsonl(REBUILT_SCORE_BRIDGE_LEDGER)
    requirement_rows = enriched_requirements(
        requirement_rows_raw,
        execution_rows,
        exact_bridge_rows,
        rebuilt_bridge_rows,
    )
    path_map = source_path_map()
    names_by_requirement = source_names_by_requirement(requirement_rows, source_candidate_rows_raw)
    scan_results: dict[str, dict[str, Any]] = {}
    for source_name, paths in sorted(path_map.items()):
        relevant_requirements = [
            row
            for row in requirement_rows
            if source_name in names_by_requirement.get(str(row.get("acquisition_requirement_row_id")), [])
        ]
        scan_results[source_name] = scan_source_records(source_name, iter_source_records(paths), relevant_requirements)

    all_source_paths: list[Path] = []
    for paths in path_map.values():
        all_source_paths.extend(paths)
    source_rows, manifest_hash = source_manifest_rows(
        [
            ACQ_RESULT,
            ACQUISITION_REQUIREMENT_LEDGER,
            SOURCE_CANDIDATE_LEDGER,
            REPAIR_EXECUTION_LEDGER,
            EXACT_PROXY_BRIDGE_LEDGER,
            REBUILT_SCORE_BRIDGE_LEDGER,
            HELPER_MODULE,
            ACQ_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
            *all_source_paths,
        ],
        generated_at,
    )

    path_counts = {name: len(paths) for name, paths in path_map.items()}
    source_lookup_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in source_candidate_lookup_rows(source_candidate_rows_raw, scan_results, path_counts)
    ]
    lookup_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in lookup_execution_rows(requirement_rows, source_candidate_rows_raw, scan_results)
    ]
    fulfillment_rows = [
        with_common(row, generated_at, manifest_hash) for row in field_fulfillment_rows(requirement_rows, lookup_rows)
    ]
    readiness_rows = [
        with_common(row, generated_at, manifest_hash) for row in repair_rerun_readiness_rows(fulfillment_rows)
    ]
    gate_rows = [with_common(row, generated_at, manifest_hash) for row in rerun_gate_rows(readiness_rows)]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in lookup_bucket_rows(lookup_rows, fulfillment_rows, readiness_rows, source_lookup_rows)
    ]

    counts = {
        "input_acquisition_result_ok": int(bool(acq_result.get("ok"))),
        "acquisition_requirement_rows": len(requirement_rows),
        "input_source_candidate_rows": len(source_candidate_rows_raw),
        "source_candidate_lookup_rows": len(source_lookup_rows),
        "lookup_execution_rows": len(lookup_rows),
        "field_fulfillment_rows": len(fulfillment_rows),
        "field_fulfilled_rows": sum(
            1
            for row in fulfillment_rows
            if row.get("field_fulfillment_status") == "FIELD_FULFILLED_BY_BRANCH_LOCAL_LOOKUP"
        ),
        "repair_rerun_readiness_rows": len(readiness_rows),
        "repair_rerun_ready_rows": sum(1 for row in readiness_rows if row.get("repair_rerun_ready") is True),
        "rerun_gate_rows": len(gate_rows),
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
        "source_path_counts": path_counts,
        "source_manifest_hash": manifest_hash,
        "repair_rerun_gate_status": gate_rows[0]["repair_rerun_gate_status"],
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(SOURCE_CANDIDATE_LOOKUP_LEDGER, source_lookup_rows)
    write_jsonl(LOOKUP_EXECUTION_LEDGER, lookup_rows)
    write_jsonl(FIELD_FULFILLMENT_LEDGER, fulfillment_rows)
    write_jsonl(REPAIR_RERUN_READINESS_LEDGER, readiness_rows)
    write_jsonl(RERUN_GATE_LEDGER, gate_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_repair_acquisition_source_lookup_result"),
            (SOURCE_CANDIDATE_LOOKUP_LEDGER, "repaired_proxy_repair_acquisition_source_candidate_lookup_ledger"),
            (LOOKUP_EXECUTION_LEDGER, "repaired_proxy_repair_acquisition_lookup_execution_ledger"),
            (FIELD_FULFILLMENT_LEDGER, "repaired_proxy_repair_acquisition_field_fulfillment_ledger"),
            (REPAIR_RERUN_READINESS_LEDGER, "repaired_proxy_repair_acquisition_repair_rerun_readiness_ledger"),
            (RERUN_GATE_LEDGER, "repaired_proxy_repair_acquisition_source_lookup_rerun_gate_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_repair_acquisition_source_lookup_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_repair_acquisition_source_lookup_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_repair_acquisition_source_lookup_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_repair_acquisition_source_lookup_summary"),
            (BUILDER_MODULE, "repaired_proxy_repair_acquisition_source_lookup_builder"),
            (VERIFIER_MODULE, "repaired_proxy_repair_acquisition_source_lookup_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_repair_acquisition_source_lookup_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Ran branch-local source lookups for acquisition requirements and rebuilt repair rerun readiness.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
