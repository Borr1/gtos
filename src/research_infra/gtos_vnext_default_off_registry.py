"""Default-off callable registry for vNext scorer/filter/router rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from src.research_infra.gtos_vnext_evidence_system import (
    DATE,
    DEFAULT_OUTPUT_DIR,
    SCHEMA_VERSION,
    read_jsonl,
    stable_hash,
)


DEFAULT_SCORER_FILTER_ROUTER_LEDGER = (
    DEFAULT_OUTPUT_DIR / f"GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_{DATE}.jsonl"
)
SURFACE = "src/research_infra/gtos_vnext_default_off_registry.py"
MATCH_FIELDS = (
    "symbol",
    "source_symbol",
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_component",
    "action_class",
    "proxy_r_class",
    "target_stop_order_class",
)
EVENT_FIELD_ALIASES = {
    "symbol": ("symbol", "broker_symbol"),
    "source_symbol": ("source_symbol", "symbol", "broker_symbol"),
    "symbol_family": ("symbol_family", "family"),
    "market_timeframe": ("market_timeframe", "timeframe"),
    "route_session": ("route_session", "session", "kill_zone"),
    "horizon_id": ("horizon_id", "horizon"),
    "side": ("side", "selected_side", "direction", "candidate_side"),
    "source_component": ("source_component", "component", "source_component_name"),
    "action_class": ("action_class", "matched_action_class", "main_compiler_action_class"),
    "proxy_r_class": ("proxy_r_class",),
    "target_stop_order_class": ("target_stop_order_class",),
}
DEFAULT_EVENT_SOURCE_PATHS = (
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
)


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def event_value(event: dict[str, Any], field: str) -> str:
    for alias in EVENT_FIELD_ALIASES.get(field, (field,)):
        if alias in event and event.get(alias) not in (None, ""):
            return normalized(event.get(alias))
    return ""


def row_scope(row: dict[str, Any]) -> dict[str, str]:
    return {field: normalized(row.get(field)) for field in MATCH_FIELDS if normalized(row.get(field))}


def build_event_from_registry_row(row: dict[str, Any]) -> dict[str, str]:
    return row_scope(row)


def event_scope_from_source_row(row: dict[str, Any]) -> dict[str, str]:
    return {field: event_value(row, field) for field in MATCH_FIELDS if event_value(row, field)}


def registry_match_result(row: dict[str, Any], matched_fields: dict[str, str], event: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_default_off_registry_match",
        "registry_match_id": f"GTOS-VNEXT-REGISTRY-MATCH-{stable_hash([row.get('vnext_matrix_row_id'), matched_fields, event], length=24)}",
        "vnext_matrix_row_id": row.get("vnext_matrix_row_id"),
        "source_name": row.get("source_name"),
        "evidence_family": row.get("evidence_family"),
        "source_row_id": row.get("source_row_id"),
        "system_surface": row.get("system_surface"),
        "implementation_action": row.get("implementation_action"),
        "match_required_fields": matched_fields,
        "r_evidence_class": row.get("r_evidence_class"),
        "r_metrics": row.get("r_metrics"),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "runtime_score_allowed": False,
        "runtime_effect_now": False,
        "paid_api_or_vendor_call": False,
        "broker_operation": False,
    }


class GTOSVNextDefaultOffRegistry:
    """In-memory default-off registry over vNext scorer/filter/router rows."""

    def __init__(self, rows: Iterable[dict[str, Any]]):
        self.rows = list(rows)
        self.scopes = [row_scope(row) for row in self.rows]
        self._field_index: dict[str, dict[str, set[int]]] = {
            field: defaultdict(set) for field in MATCH_FIELDS
        }
        self._scope_key_index: dict[tuple[tuple[str, str], ...], list[int]] = defaultdict(list)
        self._match_index_cache: dict[tuple[tuple[str, str], ...], list[int]] = {}
        self.callable_indices: set[int] = set()
        for index, scope in enumerate(self.scopes):
            if not scope:
                continue
            self.callable_indices.add(index)
            self._scope_key_index[tuple(sorted(scope.items()))].append(index)
            for field, value in scope.items():
                self._field_index[field][value].add(index)

    @classmethod
    def from_jsonl(cls, path: Path | str = DEFAULT_SCORER_FILTER_ROUTER_LEDGER) -> "GTOSVNextDefaultOffRegistry":
        return cls(read_jsonl(path))

    def match_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        criteria = {
            field: event_value(event, field)
            for field in MATCH_FIELDS
            if event_value(event, field)
        }
        if not criteria:
            return []

        criteria_key = tuple(sorted(criteria.items()))
        if criteria_key not in self._match_index_cache:
            candidate_indices: list[int] = []
            for size in range(1, len(criteria_key) + 1):
                for subset in combinations(criteria_key, size):
                    candidate_indices.extend(self._scope_key_index.get(subset, ()))
            self._match_index_cache[criteria_key] = sorted(set(candidate_indices))

        candidate_indices = self._match_index_cache[criteria_key]
        matches: list[dict[str, Any]] = []
        for index in candidate_indices:
            scope = self.scopes[index]
            matches.append(registry_match_result(self.rows[index], scope, event))
        return matches

    def build_self_check_rows(self) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        match_cache: dict[tuple[tuple[str, str], ...], list[dict[str, Any]]] = {}
        for index, row in enumerate(self.rows, start=1):
            event = build_event_from_registry_row(row)
            cache_key = tuple(sorted(event.items()))
            if event and cache_key not in match_cache:
                match_cache[cache_key] = self.match_event(event)
            matches = match_cache.get(cache_key, []) if event else []
            match_ids = [match.get("vnext_matrix_row_id") for match in matches]
            self_id = row.get("vnext_matrix_row_id")
            status = "PASS_SELF_MATCH_FOUND" if self_id in match_ids else "CATALOG_ONLY_NO_EVENT_SCOPE"
            if event and self_id not in match_ids:
                status = "FAIL_SELF_MATCH_MISSING"
            output.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "gtos_vnext_default_off_registry_self_check",
                    "self_check_row_id": f"GTOS-VNEXT-REGISTRY-SELF-CHECK-{index:08d}",
                    "vnext_matrix_row_id": self_id,
                    "source_name": row.get("source_name"),
                    "evidence_family": row.get("evidence_family"),
                    "source_row_id": row.get("source_row_id"),
                    "self_check_status": status,
                    "event_scope": event,
                    "event_scope_field_count": len(event),
                    "registry_match_rows": len(matches),
                    "self_match_found": self_id in match_ids,
                    "matched_matrix_row_ids_sha256": stable_hash(match_ids) if matches else "",
                    "candidate_use_allowed_now": False,
                    "runtime_candidate_use_permitted": False,
                    "runtime_score_allowed": False,
                    "runtime_effect_now": False,
                    "paid_api_or_vendor_call": False,
                    "broker_operation": False,
                }
            )
        return output

    def build_catalog_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(self.rows, start=1):
            scope = self.scopes[index - 1]
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "gtos_vnext_default_off_registry_catalog_row",
                    "registry_catalog_row_id": f"GTOS-VNEXT-REGISTRY-CATALOG-{index:08d}",
                    "vnext_matrix_row_id": row.get("vnext_matrix_row_id"),
                    "source_name": row.get("source_name"),
                    "evidence_family": row.get("evidence_family"),
                    "source_row_id": row.get("source_row_id"),
                    "system_surface": row.get("system_surface"),
                    "implementation_action": row.get("implementation_action"),
                    "callable_event_match_enabled": bool(scope),
                    "required_event_fields": list(scope.keys()),
                    "required_event_scope": scope,
                    "r_evidence_class": row.get("r_evidence_class"),
                    "candidate_use_allowed_now": False,
                    "runtime_candidate_use_permitted": False,
                    "runtime_score_allowed": False,
                    "runtime_effect_now": False,
                    "paid_api_or_vendor_call": False,
                    "broker_operation": False,
                }
            )
        return rows


def summarize_default_off_registry(
    registry: GTOSVNextDefaultOffRegistry,
    self_check_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(row["self_check_status"] for row in self_check_rows)
    source_counts = Counter(row.get("source_name") for row in registry.rows)
    family_counts = Counter(row.get("evidence_family") for row in registry.rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_default_off_registry_summary",
        "input_registry_rows": len(registry.rows),
        "callable_event_match_rows": len(registry.callable_indices),
        "catalog_only_no_event_scope_rows": len(registry.rows) - len(registry.callable_indices),
        "self_check_rows": len(self_check_rows),
        "self_check_status_counts": dict(sorted(status_counts.items())),
        "source_name_counts": dict(sorted(source_counts.items())),
        "evidence_family_counts": dict(sorted(family_counts.items())),
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "runtime_score_allowed_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "broker_operation_rows": 0,
        "runtime_behavior": "DEFAULT_OFF_REGISTRY_ONLY_NO_LIVE_ENABLEMENT",
    }


def validate_event_source(
    registry: GTOSVNextDefaultOffRegistry,
    source_path: Path,
    *,
    repo: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups: dict[str, dict[str, Any]] = {}
    source_rows = 0
    parse_errors = 0
    matched_event_rows = 0
    registry_match_rows = 0
    unmatched_event_rows = 0
    source_row_hashes: list[str] = []
    path_text = str(source_path).replace("\\", "/")
    if repo is not None:
        try:
            path_text = str(source_path.resolve().relative_to(repo.resolve())).replace("\\", "/")
        except ValueError:
            pass

    with source_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            source_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue

            row_hash = stable_hash(row)
            source_row_hashes.append(row_hash)
            event_scope = event_scope_from_source_row(row)
            matches = registry.match_event(row)
            match_ids = [match["vnext_matrix_row_id"] for match in matches]
            match_source_counts = Counter(match["source_name"] for match in matches)
            match_family_counts = Counter(match["evidence_family"] for match in matches)
            match_action_counts = Counter(match["implementation_action"] for match in matches)
            match_rows = len(matches)
            registry_match_rows += match_rows
            if match_rows:
                matched_event_rows += 1
            else:
                unmatched_event_rows += 1

            key = stable_hash([path_text, event_scope, match_ids])
            if key not in groups:
                groups[key] = {
                    "schema_version": SCHEMA_VERSION,
                    "row_type": "gtos_vnext_default_off_registry_event_scope_rollup",
                    "event_scope_rollup_row_id": f"GTOS-VNEXT-EVENT-SCOPE-ROLLUP-{key[:24]}",
                    "source_path": path_text,
                    "event_scope": event_scope,
                    "event_scope_field_count": len(event_scope),
                    "source_event_rows": 0,
                    "matched_event_rows": 0,
                    "unmatched_event_rows": 0,
                    "registry_match_rows": 0,
                    "first_source_line_no": line_no,
                    "last_source_line_no": line_no,
                    "source_row_hashes": [],
                    "matched_matrix_row_ids_sha256": stable_hash(match_ids) if match_ids else "",
                    "match_source_name_counts": Counter(),
                    "match_evidence_family_counts": Counter(),
                    "match_implementation_action_counts": Counter(),
                    "candidate_use_allowed_now": False,
                    "runtime_candidate_use_permitted": False,
                    "runtime_score_allowed": False,
                    "runtime_effect_now": False,
                    "paid_api_or_vendor_call": False,
                    "broker_operation": False,
                }
            group = groups[key]
            group["source_event_rows"] += 1
            group["matched_event_rows"] += 1 if match_rows else 0
            group["unmatched_event_rows"] += 0 if match_rows else 1
            group["registry_match_rows"] += match_rows
            group["last_source_line_no"] = line_no
            group["source_row_hashes"].append(row_hash)
            group["match_source_name_counts"].update(match_source_counts)
            group["match_evidence_family_counts"].update(match_family_counts)
            group["match_implementation_action_counts"].update(match_action_counts)

    rollup_rows = []
    for group in groups.values():
        row_hashes = group.pop("source_row_hashes")
        group["source_row_hashes_sha256"] = stable_hash(row_hashes)
        group["match_source_name_counts"] = dict(sorted(group["match_source_name_counts"].items()))
        group["match_evidence_family_counts"] = dict(sorted(group["match_evidence_family_counts"].items()))
        group["match_implementation_action_counts"] = dict(sorted(group["match_implementation_action_counts"].items()))
        rollup_rows.append(group)

    source_summary = {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_default_off_registry_event_source_summary",
        "event_source_summary_row_id": f"GTOS-VNEXT-EVENT-SOURCE-{stable_hash(path_text, length=24)}",
        "source_path": path_text,
        "source_rows": source_rows,
        "parse_errors": parse_errors,
        "matched_event_rows": matched_event_rows,
        "unmatched_event_rows": unmatched_event_rows,
        "registry_match_rows": registry_match_rows,
        "event_scope_rollup_rows": len(rollup_rows),
        "source_row_hashes_sha256": stable_hash(source_row_hashes),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "runtime_score_allowed": False,
        "runtime_effect_now": False,
        "paid_api_or_vendor_call": False,
        "broker_operation": False,
    }
    return source_summary, sorted(rollup_rows, key=lambda row: row["event_scope_rollup_row_id"])


def summarize_event_validation(
    source_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "row_type": "gtos_vnext_default_off_registry_event_validation_summary",
        "event_source_count": len(source_rows),
        "source_rows_total": sum(row["source_rows"] for row in source_rows),
        "parse_errors_total": sum(row["parse_errors"] for row in source_rows),
        "matched_event_rows_total": sum(row["matched_event_rows"] for row in source_rows),
        "unmatched_event_rows_total": sum(row["unmatched_event_rows"] for row in source_rows),
        "registry_match_rows_total": sum(row["registry_match_rows"] for row in source_rows),
        "event_scope_rollup_rows": len(rollup_rows),
        "source_path_counts": {row["source_path"]: row["source_rows"] for row in source_rows},
        "runtime_behavior": "DEFAULT_OFF_EVENT_VALIDATION_ONLY_NO_LIVE_ENABLEMENT",
        "candidate_use_allowed_now_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "runtime_score_allowed_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "broker_operation_rows": 0,
    }
