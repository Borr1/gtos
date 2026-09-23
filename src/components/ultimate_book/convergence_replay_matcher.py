"""Observation-only reservoir matcher for ultimate convergence replay records."""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .convergence_replay_record import canonical_side


SCHEMA_VERSION = "ultimate_convergence_replay_matcher_v1"
LFS_POINTER_HEADER = "version https://git-lfs.github.com/spec/v1"

DEFAULT_SOURCE_PATHS = {
    "selector_v3_package": "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_DEFAULT_OFF_PACKAGE.json",
    "selector_v3_full_evidence": "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_FULL_SELECTOR_EVIDENCE_LEDGER.jsonl.gz",
    "selector_v3_join_ledger": "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_SELECTOR_SCHEDULER_EXECUTION_JOIN_LEDGER.jsonl.gz",
    "scheduler_v3_package": "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json",
    "scheduler_v3_blocked_edge": "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_BLOCKED_EDGE_RECOVERY_LEDGER.jsonl.gz",
    "wave4r_microscope": "research/operations/final_moonshot_wave4r_v4_vs_v3_frozen_replay_results_gate_2026_06_05/WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl",
    "wave4r_summary": "research/operations/final_moonshot_wave4r_v4_vs_v3_frozen_replay_results_gate_2026_06_05/WAVE4R_RESULTS_SUMMARY.json",
    "cp281_rule_ledger": "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_RULE_LEDGER_2026-05-18.jsonl",
    "cp281_replay_summary": "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_SUMMARY_2026-05-18.json",
    "vnext_build_matrix": "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl",
    "vnext_build_summary": "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_BUILD_MATRIX_SUMMARY_2026-05-18.json",
}


def _rooted(root: Path, path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def is_lfs_pointer_file(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.readline().strip() == LFS_POINTER_HEADER
    except Exception:
        return False


def _jsonl_opener(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_jsonl(path: Path, *, limit: int | None = None) -> Iterable[dict[str, Any]]:
    with _jsonl_opener(path) as handle:
        emitted = 0
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)
            emitted += 1
            if limit is not None and emitted >= limit:
                break


def count_jsonl_rows(path: Path, *, limit: int | None = None) -> int:
    count = 0
    with _jsonl_opener(path) as handle:
        for line in handle:
            if line.strip():
                count += 1
                if limit is not None and count >= limit:
                    return count
    return count


def source_availability_row(root: Path, key: str, rel_path: str, *, count_rows: bool = False) -> dict[str, Any]:
    path = _rooted(root, rel_path)
    row: dict[str, Any] = {
        "schema_version": "ultimate_convergence_source_availability_row_v1",
        "source_key": key,
        "path": rel_path,
        "exists": path.exists(),
        "read_status": "missing",
        "bytes": None,
        "row_count": None,
        "lfs_pointer": False,
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
    }
    if not path.exists():
        return row
    row["bytes"] = path.stat().st_size
    pointer = is_lfs_pointer_file(path)
    row["lfs_pointer"] = pointer
    if pointer:
        row["read_status"] = "lfs_pointer_not_hydrated"
        return row
    try:
        if path.suffix in {".json", ".md", ".xml"}:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8", errors="replace"))
            row["read_status"] = "readable"
        elif path.suffix == ".jsonl" or path.name.endswith(".jsonl.gz"):
            row["read_status"] = "readable"
            if count_rows:
                row["row_count"] = count_jsonl_rows(path)
        else:
            row["read_status"] = "present_unclassified"
    except Exception as exc:
        row["read_status"] = f"read_error:{type(exc).__name__}:{exc}"
    return row


def source_availability_ledger(root: Path, *, count_rows: bool = False) -> list[dict[str, Any]]:
    return [
        source_availability_row(root, key, path, count_rows=count_rows)
        for key, path in DEFAULT_SOURCE_PATHS.items()
    ]


def _load_json(root: Path, rel_path: str) -> dict[str, Any]:
    path = _rooted(root, rel_path)
    if not path.exists() or is_lfs_pointer_file(path):
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _normalize_key_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip().upper()


def _selector_key(row: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _normalize_key_value(row.get("symbol")),
        _normalize_key_value(canonical_side(side=row.get("side"))),
        _normalize_key_value(row.get("session_bucket")),
        _normalize_key_value(row.get("framework")),
        _normalize_key_value(row.get("origin_family")),
    )


def _cp281_key(row: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _normalize_key_value(row.get("symbol_family")),
        _normalize_key_value(row.get("symbol")),
        _normalize_key_value(row.get("source_symbol")),
        _normalize_key_value(row.get("market_timeframe")),
        _normalize_key_value(row.get("route_session")),
        _normalize_key_value(row.get("horizon_id")),
        _normalize_key_value(canonical_side(side=row.get("side"))),
        _normalize_key_value(row.get("source_path_sha256")),
        _normalize_key_value(row.get("source_file_sha256")),
    )


def _scheduler_key(row: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _normalize_key_value(row.get("symbol")),
        _normalize_key_value(canonical_side(side=row.get("side"))),
        _normalize_key_value(row.get("session_bucket")),
        _normalize_key_value(row.get("framework")),
        _normalize_key_value(row.get("origin_family")),
    )


def _index_rows(rows: Iterable[Mapping[str, Any]], key_func) -> dict[tuple[str | None, ...], list[dict[str, Any]]]:
    index: dict[tuple[str | None, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = key_func(row)
        if any(part is not None for part in key):
            index[key].append(dict(row))
    return dict(index)


def build_reservoir_indexes(root: Path, *, scheduler_row_limit: int | None = None) -> dict[str, Any]:
    selector_pkg = _load_json(root, DEFAULT_SOURCE_PATHS["selector_v3_package"])
    selector_rules = selector_pkg.get("runtime_selector_rules") or []

    cp281_path = _rooted(root, DEFAULT_SOURCE_PATHS["cp281_rule_ledger"])
    cp281_rules = [] if (not cp281_path.exists() or is_lfs_pointer_file(cp281_path)) else list(iter_jsonl(cp281_path))

    scheduler_path = _rooted(root, DEFAULT_SOURCE_PATHS["scheduler_v3_blocked_edge"])
    scheduler_rows = (
        []
        if (not scheduler_path.exists() or is_lfs_pointer_file(scheduler_path))
        else list(iter_jsonl(scheduler_path, limit=scheduler_row_limit))
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_availability": source_availability_ledger(root, count_rows=False),
        "selector_v3_rules": selector_rules,
        "selector_v3_index": _index_rows(selector_rules, _selector_key),
        "scheduler_v3_rows": scheduler_rows,
        "scheduler_v3_index": _index_rows(scheduler_rows, _scheduler_key),
        "cp281_rules": cp281_rules,
        "cp281_index": _index_rows(
            [
                {**row, **(row.get("match_scope") if isinstance(row.get("match_scope"), Mapping) else {})}
                for row in cp281_rules
            ],
            _cp281_key,
        ),
        "counts": {
            "selector_v3_rules": len(selector_rules),
            "scheduler_v3_rows_loaded": len(scheduler_rows),
            "cp281_rules": len(cp281_rules),
        },
    }


def _missing_fields(record: Mapping[str, Any], fields: Iterable[str]) -> list[str]:
    return [field for field in fields if record.get(field) in (None, "")]


def _match_rows(index: Mapping[tuple[str | None, ...], list[dict[str, Any]]], key: tuple[str | None, ...]) -> list[dict[str, Any]]:
    if any(part is None for part in key):
        return []
    return list(index.get(key, []))


def _selector_matches(record: Mapping[str, Any], indexes: Mapping[str, Any]) -> list[dict[str, Any]]:
    missing = _missing_fields(record, ("symbol", "side", "session_bucket", "framework", "origin_family"))
    key = _selector_key(record)
    rows = _match_rows(indexes.get("selector_v3_index", {}), key)
    if not rows:
        return [{
            "reservoir": "selector_v3_source_bound_proxy",
            "match_status": "no_exact_rule_match" if not missing else "missing_match_fields",
            "missing_match_fields": missing,
            "matched_on": ["symbol", "side", "session_bucket", "framework", "origin_family"],
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }]
    return [
        {
            "reservoir": "selector_v3_source_bound_proxy",
            "match_status": "exact_runtime_rule_match",
            "matched_on": ["symbol", "side", "session_bucket", "framework", "origin_family"],
            "rule_id": row.get("rule_id"),
            "selector_v3_action": row.get("selector_v3_action") or row.get("action"),
            "risk_multiplier": row.get("risk_multiplier"),
            "known_proxy_r_rows": row.get("known_proxy_r_rows"),
            "proxy_r_sum": row.get("proxy_r_sum"),
            "expectancy_r": row.get("expectancy_r"),
            "evidence_class": "source_bound_proxy_R_research_materialization",
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }
        for row in rows
    ]


def _scheduler_matches(record: Mapping[str, Any], indexes: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows_by_candidate = [
        row for row in indexes.get("scheduler_v3_rows", [])
        if record.get("candidate_id") and row.get("candidate_id") == record.get("candidate_id")
    ]
    rows = rows_by_candidate or _match_rows(indexes.get("scheduler_v3_index", {}), _scheduler_key(record))
    missing = _missing_fields(record, ("candidate_id", "symbol", "side", "session_bucket", "framework", "origin_family"))
    if not rows:
        return [{
            "reservoir": "scheduler_v3_source_bound_proxy",
            "match_status": "no_exact_scheduler_match" if not missing else "missing_match_fields",
            "missing_match_fields": missing,
            "matched_on": ["candidate_id", "symbol", "side", "session_bucket", "framework", "origin_family"],
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }]
    return [
        {
            "reservoir": "scheduler_v3_source_bound_proxy",
            "match_status": "exact_candidate_match" if row.get("candidate_id") == record.get("candidate_id") else "exact_context_match",
            "matched_on": ["candidate_id"] if row.get("candidate_id") == record.get("candidate_id") else ["symbol", "side", "session_bucket", "framework", "origin_family"],
            "candidate_id": row.get("candidate_id"),
            "scheduler_v3_decision": row.get("scheduler_v3_decision"),
            "scheduler_v3_action": row.get("scheduler_v3_action"),
            "scheduler_v3_action_class": row.get("scheduler_v3_action_class"),
            "result_r": row.get("result_r"),
            "result_r_class": row.get("result_r_class"),
            "evidence_class": "source_bound_proxy_R_research_materialization",
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }
        for row in rows
    ]


def _cp281_matches(record: Mapping[str, Any], indexes: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "symbol_family",
        "symbol",
        "source_symbol",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "side",
        "source_path_sha256",
        "source_file_sha256",
    )
    missing = _missing_fields(record, fields)
    rows = _match_rows(indexes.get("cp281_index", {}), _cp281_key(record))
    if not rows:
        return [{
            "reservoir": "cp281_ready_runtime_mapping",
            "match_status": "no_exact_cp281_match" if not missing else "missing_match_fields",
            "missing_match_fields": missing,
            "matched_on": list(fields),
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }]
    return [
        {
            "reservoir": "cp281_ready_runtime_mapping",
            "match_status": "exact_cp281_rule_match",
            "matched_on": list(fields),
            "cp281_rule_row_id": row.get("cp281_rule_row_id"),
            "action_class": row.get("action_class"),
            "candidate_use_allowed_now": row.get("candidate_use_allowed_now"),
            "runtime_candidate_use_permitted": row.get("runtime_candidate_use_permitted"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
            "evidence_class": "default_off_research_to_runtime_rule_mapping_and_simulated_R",
            "direct_execution_authority": False,
            "broker_runtime_change_status": False,
        }
        for row in rows
    ]


def match_record(record: Mapping[str, Any], indexes: Mapping[str, Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    matches.extend(_selector_matches(record, indexes))
    matches.extend(_scheduler_matches(record, indexes))
    matches.extend(_cp281_matches(record, indexes))
    return matches


def attach_reservoir_matches(record: Mapping[str, Any], indexes: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(record)
    matches = match_record(record, indexes)
    exact = [row for row in matches if str(row.get("match_status", "")).startswith("exact_")]
    out["reservoir_matches"] = matches
    out["match_summary"] = {
        "schema_version": "ultimate_convergence_match_summary_v1",
        "match_count": len(matches),
        "exact_match_count": len(exact),
        "matched_reservoirs": sorted({row.get("reservoir") for row in exact if row.get("reservoir")}),
        "direct_execution_authority": False,
        "broker_runtime_change_status": False,
    }
    return out


__all__ = [
    "DEFAULT_SOURCE_PATHS",
    "SCHEMA_VERSION",
    "attach_reservoir_matches",
    "build_reservoir_indexes",
    "is_lfs_pointer_file",
    "match_record",
    "source_availability_ledger",
    "source_availability_row",
]
