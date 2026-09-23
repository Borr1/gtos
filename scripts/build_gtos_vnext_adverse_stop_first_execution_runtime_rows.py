#!/usr/bin/env python3
"""Build runtime rows for adverse/stop-first execution evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_gtos_vnext_master_conversion_ledger as master_ledger
from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_ADVERSE_STOP_FIRST_EXECUTION_BEHAVIOR"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_adverse_stop_first_execution_runtime_rows",
    "gtos_vnext_adverse_stop_first_execution_runtime_summary",
)
SESSION_WILDCARD = "ALL_SESSIONS"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _line_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return 1
    if suffix not in COUNTABLE_SUFFIXES:
        return None
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _resolve_source_path(path_text: str) -> Path:
    source = Path(path_text)
    if source.is_absolute():
        return source
    candidate = REPO_ROOT / source
    if candidate.exists():
        return candidate
    tmp_candidate = Path("C:/tmp") / source
    if tmp_candidate.exists():
        return tmp_candidate
    return candidate


def _wave_units() -> list[dict[str, Any]]:
    rows = master_ledger.build_rows()
    return sorted(
        [
            row
            for row in rows
            if row.get("batch_wave_id") == WAVE_ID
            or (
                row.get("conversion_state") in master_ledger.OPEN_BATCH_STATES
                and master_ledger._batch_wave_id_for_row(row) == WAVE_ID
            )
        ],
        key=lambda row: str(row.get("source_artifact_path") or "").casefold(),
    )


def _source_paths() -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for unit in _wave_units():
        raw_path = _norm(unit.get("source_artifact_path"))
        if not raw_path:
            continue
        lower = raw_path.casefold()
        if any(token in lower for token in OUTPUT_NAME_TOKENS):
            continue
        path = _resolve_source_path(raw_path)
        if not path.exists():
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        paths.append((path, _norm(unit.get("source_artifact_hash"))))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _source_group(path: Path) -> str:
    name = path.name
    for prefix in (
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_",
        "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_",
        "HISTORICAL_OHLC_GTOS_REPLAY_",
        "MAIN_ORCH24_",
        "G12_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-18.jsonl",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_RESULT_2026-05-17.json",
        "_2026-05-17.py",
        ".jsonl",
        ".json",
        ".csv",
        ".md",
        ".txt",
        ".py",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route_candidate_id = _norm(row.get("route_candidate_id") or row.get("candidate_id"))
    if route_candidate_id and "|" in route_candidate_id:
        parts = [part.strip() for part in route_candidate_id.split("|")]
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    return "", "", "", ""


def _session_from_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    hour = parsed.hour
    if 0 <= hour < 4:
        return "tokyo_kz"
    if 7 <= hour < 12:
        return "london_core"
    if 13 <= hour < 18:
        return "ny_core"
    return "off_core_session"


def _session_from_candidate_id(candidate_id: str) -> str:
    if "_20" not in candidate_id:
        return ""
    _, time_part = candidate_id.split("_", 1)
    return _session_from_time(time_part)


def _clean_route_session(value: str) -> str:
    raw = _norm(value)
    key = raw.casefold().replace("-", "_").replace(" ", "_")
    if key in {"", "none", "na", "n/a", "null", "unknown", "all_sessions"}:
        return SESSION_WILDCARD if raw else ""
    return raw


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _variant, _horizon = _route_parts(row)
    for key in ("symbol", "source_symbol", "market", "instrument", "candidate_symbol"):
        if value := _norm(row.get(key)):
            return value
    if route_symbol:
        return route_symbol
    candidate_id = _norm(row.get("candidate_id") or row.get("event_id"))
    if "_20" in candidate_id:
        return candidate_id.split("_20", 1)[0].rstrip("_")
    return ""


def _route_session(row: dict[str, Any], path: Path) -> str:
    _symbol, route_session, _variant, _horizon = _route_parts(row)
    for key in ("route_session", "session", "kill_zone", "session_name"):
        if value := _clean_route_session(_norm(row.get(key))):
            return value
    if route_session:
        return _clean_route_session(route_session)
    candidate_id = _norm(row.get("candidate_id") or row.get("event_id"))
    if session := _session_from_candidate_id(candidate_id):
        return session
    name = path.name.casefold()
    if "tokyo" in name:
        return "tokyo_kz"
    if "london" in name:
        return "london_core"
    if "_ny_" in name or "ny_core" in name:
        return "ny_core"
    for key in ("decision_time_utc", "decision_asof_utc", "bar_time_utc", "timestamp"):
        if value := _norm(row.get(key)):
            if session := _session_from_time(value):
                return session
    return ""


def _market_timeframe(row: dict[str, Any], path: Path) -> str:
    for key in ("market_timeframe", "timeframe", "source_timeframe", "tf"):
        if value := _norm(row.get(key)):
            return value.upper()
    text = _text_blob(path, row).casefold()
    if "m1_" in text or "m1 " in text:
        return "M1"
    if "m5_" in text or "m5 " in text:
        return "M5"
    if "m15_" in text or "m15 " in text or "m15" in path.name.casefold():
        return "M15"
    if "h1" in text:
        return "H1"
    if "h4" in text:
        return "H4"
    return "M15"


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol, _session, _variant, horizon = _route_parts(row)
    raw = _norm(row.get("horizon_id") or row.get("horizon") or row.get("horizon_m15_bars") or horizon)
    if raw and raw.isdigit():
        return f"h{raw}"
    return raw


def _side(row: dict[str, Any]) -> str:
    for key in ("side", "selected_side", "direction", "trade_side"):
        value = _upper(row.get(key))
        if value in {"LONG", "SHORT"}:
            return value
    return ""


def _framework(row: dict[str, Any], path: Path) -> str:
    for key in ("framework", "setup_framework", "framework_name", "poi_framework"):
        if value := _norm(row.get(key)):
            return value
    text = _text_blob(path, row).casefold()
    if "fvg_ob" in text or "ob_" in text or "order_block" in text:
        return "ob_retest"
    if "breaker" in text:
        return "breaker_re_entry"
    if "fvg" in text:
        return "fvg_fill"
    return ""


def _route_family(row: dict[str, Any], path: Path) -> str:
    if value := _norm(row.get("route_family")):
        return value
    name = path.name.casefold()
    if name.startswith("main_orch24"):
        return "numeric_router"
    if "accepted_builder" in name:
        return "moonshot_accepted_builder_entry_adverse"
    return "moonshot_mechanical"


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "adverse_stop_first_branch_redesign_id",
        "adverse_stop_first_action_id",
        "adverse_stop_first_avoid_redesign_id",
        "entry_adverse_crosstab_bucket_id",
        "entry_adverse_detail_branch_id",
        "entry_adverse_combined_variant_id",
        "entry_adverse_entry_variant_detail_id",
        "entry_adverse_rejected_repair_id",
        "entry_adverse_scope_id",
        "entry_adverse_sidecar_context_id",
        "entry_adverse_unified_branch_local_implementation_id",
        "entry_adverse_followup_id",
        "entry_adverse_decision_id",
        "adverse_local_implementation_spec_id",
        "entry_adverse_score_id",
        "entry_adverse_evidence_detail_id",
        "entry_adverse_parameter_id",
        "entry_adverse_spec_id",
        "entry_adverse_export_id",
        "target_stop_contract_id",
        "branch_queue_id",
        "candidate_id",
        "event_id",
        "row_id",
        "row_key",
        "source_row_id",
    ):
        if value := _norm(row.get(key)):
            return value
    for key, value in row.items():
        if isinstance(key, str) and key.endswith("_id") and _norm(value):
            return _norm(value)
    stable_row = {str(key): value for key, value in row.items()}
    return _sha256_text(json.dumps(stable_row, sort_keys=True, default=str))[:24]


def _text_blob(path: Path, row: dict[str, Any]) -> str:
    parts = [path.name]
    for key, value in row.items():
        parts.append(str(key))
        if isinstance(value, (str, int, float, bool)):
            parts.append(str(value))
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.keys())
            parts.extend(str(item) for item in value.values() if isinstance(item, (str, int, float, bool)))
        elif isinstance(value, list):
            parts.extend(str(item) for item in value[:20] if isinstance(item, (str, int, float, bool)))
    return " ".join(parts)


def _source_component(path: Path, row: dict[str, Any]) -> str:
    name = path.name.casefold()
    text = _text_blob(path, row).casefold()
    if "gbpjpy_long_adverse_reclass_status" in row or "gbpjpy_long_adverse" in text:
        if _upper(row.get("gbpjpy_long_adverse_reclass_status")).startswith("RECLASSIFIED"):
            return "gbpjpy_long_adverse_avoid_reclass"
        return "gbpjpy_long_adverse_reclass_context"
    if "targetstop_na_binding" in name or "target_stop_contract" in name:
        return "targetstop_na_binding_repair"
    if "path_control_target_stop_contract" in name:
        return "target_stop_path_control"
    if "adverse_stop_first" in name:
        return "adverse_stop_first_execution"
    if "entry_adverse" in name:
        return "entry_adverse_execution"
    return "adverse_stop_first_execution"


def _target_stop_order_class(row: dict[str, Any], source_component: str) -> str:
    result = _upper(
        row.get("target_stop_order_class")
        or row.get("target_stop_result")
        or row.get("entry_target_stop_balance_class")
    )
    if "STOP_FIRST" in result:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in result:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "NO_TARGET_STOP" in result or "TARGETSTOP_NA" in result:
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "NO_FILL" in result or "UNFILLED" in result or "AMBIGU" in result:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    if source_component in {"targetstop_na_binding_repair", "target_stop_path_control"}:
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "STOP_FIRST" in _upper(row.get("adverse_stop_first_class")):
        return "STOP_FIRST_PROXY_DOMINANT"
    return ""


def _explicit_decision(row: dict[str, Any], source_component: str, target_stop_class: str) -> str:
    if _upper(row.get("gbpjpy_long_adverse_reclass_status")).startswith("RECLASSIFIED"):
        return "AVOID"
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        stop_first_class = _upper(row.get("adverse_stop_first_class"))
        action = _upper(
            row.get("adverse_redesign_action_class")
            or row.get("ordering_collapse_action_class")
            or row.get("entry_adverse_selector_action")
            or row.get("current_action")
        )
        if "SOURCE_REPAIR" in stop_first_class or "SOURCE_STRESS" in action:
            return "MIXED"
        return "AVOID"
    if target_stop_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "MIXED"
    for key in (
        "decision",
        "computed_decision",
        "branch_decision",
        "current_action",
        "implementation_action",
        "entry_adverse_selector_action",
        "entry_adverse_requirement",
        "action_class",
        "coverage_status",
        "status",
    ):
        value = _upper(row.get(key))
        if not value:
            continue
        if "ADVERSE_CLUSTER" in value and ("AVOID" in value or "REDESIGN" in value):
            return "AVOID"
        if any(token in value for token in ("AVOID", "NEGATIVE", "ENTRY_TOUCHED_THEN_SL", "STOP_FIRST")):
            return "AVOID"
        if any(token in value for token in ("SOURCE_REPAIR", "REPAIR", "REQUIRED", "MISSING", "AMBIGU", "REDESIGN")):
            return "MIXED"
        if any(token in value for token in ("FOLLOW", "POSITIVE", "IMPLEMENT", "KEEP", "PRESERVE")):
            return "FOLLOW"
    if source_component in {"targetstop_na_binding_repair", "target_stop_path_control"}:
        return "MIXED"
    return "MIXED"


def _action_class(decision: str, source_component: str, target_stop_class: str) -> str:
    if decision == "AVOID":
        if source_component == "gbpjpy_long_adverse_avoid_reclass":
            return "gbpjpy_long_adverse_avoid_filter"
        if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
            return "adverse_stop_first_avoid_filter"
        return "entry_adverse_avoid_filter"
    if decision == "FOLLOW":
        return "entry_adverse_follow_scorer"
    if source_component in {"targetstop_na_binding_repair", "target_stop_path_control"}:
        return "target_stop_binding_repair_guard"
    if target_stop_class == "TARGET_STOP_AMBIGUOUS_OR_MIXED":
        return "target_stop_ambiguity_context_guard"
    return "entry_adverse_context_guard"


def _source_role(decision: str, source_component: str, target_stop_class: str) -> str:
    if source_component == "gbpjpy_long_adverse_avoid_reclass":
        return "gbpjpy_long_adverse_avoid_guard"
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT" and decision == "AVOID":
        return "adverse_stop_first_avoid_guard"
    if source_component in {"targetstop_na_binding_repair", "target_stop_path_control"}:
        return "target_stop_source_binding_guard"
    if decision == "FOLLOW":
        return "entry_adverse_follow_pressure"
    return "entry_adverse_redesign_context"


def _r_evidence_class(source_component: str, target_stop_class: str) -> str:
    if source_component == "gbpjpy_long_adverse_avoid_reclass":
        return "GBPJPY_LONG_ADVERSE_RECLASS_PROXY_R"
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "ADVERSE_STOP_FIRST_PROXY_ORDERING"
    if target_stop_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "TARGETSTOP_NA_BINDING_REPAIR"
    if target_stop_class == "TARGET_STOP_AMBIGUOUS_OR_MIXED":
        return "TARGET_STOP_AMBIGUITY_CONTEXT"
    return "ENTRY_ADVERSE_EXECUTION_CONTEXT"


def _implementation_action(
    row: dict[str, Any],
    decision: str,
    source_component: str,
    target_stop_class: str,
) -> str:
    for key in (
        "implementation_action",
        "current_action",
        "entry_adverse_selector_action",
        "entry_adverse_requirement",
        "next_same_resource_computation",
        "adverse_redesign_action_class",
        "ordering_collapse_action_class",
    ):
        if value := _norm(row.get(key)):
            return value
    if decision == "AVOID" and source_component == "gbpjpy_long_adverse_avoid_reclass":
        return "REDESIGN_GBPJPY_LONG_ADVERSE_CLUSTER_AS_AVOID_FILTER"
    if decision == "AVOID" and target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY"
    if target_stop_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED"
    if decision == "FOLLOW":
        return "KEEP_ENTRY_ADVERSE_FOLLOW_CONTEXT"
    return "MERGE_ENTRY_ADVERSE_CONTEXT_AS_GUARD_INPUT"


def _numeric_candidates(row: dict[str, Any]) -> list[tuple[str, float]]:
    values: list[tuple[str, float]] = []
    for field_name in (
        "after_proxy_r",
        "before_proxy_r",
        "entry_adverse_builder_score",
        "entry_adverse_selector_score",
        "entry_adverse_spec_score",
        "entry_adverse_builder_parameter_score",
        "redesign_pressure_score",
        "fillability_rate",
        "target_first_rate",
        "stop_first_rate",
        "proxy_score",
        "score",
    ):
        numeric = _to_float(row.get(field_name))
        if numeric is not None:
            values.append((field_name, numeric))
    metrics = row.get("r_metrics")
    if isinstance(metrics, dict):
        for metric_name in ("cost_adjusted_simulated_r", "stress_simulated_r", "proxy_score"):
            metric = metrics.get(metric_name)
            if isinstance(metric, dict):
                numeric = _to_float(metric.get("sum") if metric.get("sum") is not None else metric.get("mean"))
                if numeric is not None:
                    values.append((metric_name, numeric))
    return values


def _row_weight(row: dict[str, Any]) -> int:
    for key in (
        "branch_count",
        "row_count",
        "candidate_rows",
        "source_rows_represented",
        "event_count",
        "sample_count",
        "binding_candidate_rows_for_entry",
        "bound_target_stop_contract_count",
        "n",
    ):
        value = _to_float(row.get(key))
        if value is not None and value > 0 and value <= 100000:
            return max(1, int(round(value)))
    return 1


def _metric_trace(total: float, count: float, source_field: str) -> dict[str, Any]:
    mean = total / count if count else None
    return {
        "sum": round(total, 12),
        "count": count,
        "mean": round(mean, 12) if mean is not None else None,
        "positive_rows": int(total > 0),
        "negative_rows": int(total < 0),
        "zero_rows": int(total == 0),
        "source_field": source_field,
        "source_shape": "adverse_stop_first_execution_compact_scope",
    }


@dataclass
class Group:
    source_path: str
    source_hash: str
    source_group: str
    symbol: str
    source_symbol: str
    symbol_family: str
    market_timeframe: str
    route_session: str
    side: str
    horizon_id: str
    framework: str
    route_family: str
    source_component: str
    target_stop_order_class: str
    decision: str
    action_class: str
    source_role: str
    r_evidence_class: str
    implementation_action: str
    rows: int = 0
    source_rows_represented: int = 0
    proxy_score_sum: float = 0.0
    cost_adjusted_sum: float = 0.0
    stress_sum: float = 0.0
    source_row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        weight = _row_weight(row)
        self.source_rows_represented += weight
        for field, value in _numeric_candidates(row):
            if field in {"after_proxy_r", "before_proxy_r", "proxy_score", "score", "redesign_pressure_score"}:
                self.proxy_score_sum += value
            elif "stress" in field:
                self.stress_sum += value
            else:
                self.cost_adjusted_sum += value
        if self.decision == "AVOID" and not self.proxy_score_sum:
            self.proxy_score_sum -= float(weight)
        if row_id := _row_id(row):
            if len(self.source_row_ids_sample) < 8:
                self.source_row_ids_sample.append(row_id)

    def to_row(self) -> dict[str, Any]:
        key_payload = "|".join(
            [
                self.source_group,
                self.symbol,
                self.source_symbol,
                self.symbol_family,
                self.market_timeframe,
                self.route_session,
                self.side,
                self.horizon_id,
                self.framework,
                self.route_family,
                self.source_component,
                self.target_stop_order_class,
                self.decision,
                self.action_class,
                self.source_role,
                self.r_evidence_class,
                self.implementation_action,
            ]
        )
        row_id = f"adverse_stop_first_execution:{_sha256_text(key_payload)[:24]}"
        scope = {
            key: value
            for key, value in {
                "symbol": self.symbol,
                "source_symbol": self.source_symbol,
                "symbol_family": self.symbol_family,
                "market": self.symbol or self.source_symbol,
                "market_timeframe": self.market_timeframe,
                "timeframe": self.market_timeframe,
                "route_session": self.route_session,
                "side": self.side,
                "horizon_id": self.horizon_id,
                "framework": self.framework,
                "route_family": self.route_family,
                "source_component": self.source_component,
                "action_class": self.action_class,
                "target_stop_order_class": self.target_stop_order_class,
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.source_rows_represented or self.rows),
                max(float(self.rows), 1.0),
                "adverse_stop_first_execution_source_rows",
            )
        }
        if self.proxy_score_sum:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_score_sum,
                max(float(self.rows), 1.0),
                "adverse_stop_first_execution_proxy_fields",
            )
        if self.cost_adjusted_sum:
            metrics["cost_adjusted_simulated_r"] = _metric_trace(
                self.cost_adjusted_sum,
                max(float(self.rows), 1.0),
                "adverse_stop_first_execution_cost_fields",
            )
        if self.stress_sum:
            metrics["stress_simulated_r"] = _metric_trace(
                self.stress_sum,
                max(float(self.rows), 1.0),
                "adverse_stop_first_execution_stress_fields",
            )
        return {
            "schema_version": "gtos_vnext_adverse_stop_first_execution_runtime_row_v1",
            "row_key": row_id,
            "adverse_stop_first_execution_runtime_row_id": row_id,
            "source_name": "gtos_vnext_adverse_stop_first_execution_wave",
            "evidence_family": "gtos_vnext_adverse_stop_first_execution",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": "adverse_stop_first_execution_runtime",
            "runtime_effect_now": "adverse_stop_first_execution_runtime_guard",
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "r_evidence_class": self.r_evidence_class,
            "review_action": self.decision,
            "decision": self.decision,
            "source_component": self.source_component,
            "route_family": self.route_family,
            "framework": self.framework,
            "symbol": self.symbol,
            "source_symbol": self.source_symbol,
            "symbol_family": self.symbol_family,
            "market_timeframe": self.market_timeframe,
            "timeframe": self.market_timeframe,
            "route_session": self.route_session,
            "side": self.side,
            "horizon_id": self.horizon_id,
            "target_stop_order_class": self.target_stop_order_class,
            "source_path": self.source_path,
            "drill_through_path": self.source_path,
            "source_artifact_hash_sha256": self.source_hash,
            "source_rows_represented": self.source_rows_represented,
            "source_row_ids_sample": self.source_row_ids_sample,
            "source_bound": bool((self.symbol or self.source_symbol or self.symbol_family) and self.route_session),
            "source_complete": self.decision in {"FOLLOW", "AVOID"},
            "runtime_candidate_use_permitted": self.decision == "FOLLOW",
            "candidate_use_allowed_now": self.decision == "FOLLOW",
            "r_metrics": metrics,
            "event_scope": scope,
        }


def _read_runtime_source_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(row, dict):
                        rows.append(row)
        except OSError:
            return []
        return rows
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            rows: list[dict[str, Any]] = [payload]
            for value in payload.values():
                if isinstance(value, list):
                    rows.extend(row for row in value if isinstance(row, dict))
            return rows
    if path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except OSError:
            return []
    return []


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, ...], Group] = {}
    source_stats: list[dict[str, Any]] = []
    for path, ledger_hash in _source_paths():
        path_text = _path_text(path)
        source_hash = ledger_hash or _sha256_file(path)
        line_count = _line_count(path)
        runtime_rows = _read_runtime_source_rows(path) if path.suffix.lower() in RUNTIME_SUFFIXES else []
        source_stats.append(
            {
                "path": path_text,
                "exists": True,
                "rows": line_count,
                "runtime_rows_read": len(runtime_rows),
                "sha256_or_git_blob": source_hash,
                "suffix": path.suffix.lower(),
            }
        )
        source_group = _source_group(path)
        for row in runtime_rows:
            source_component = _source_component(path, row)
            target_stop_class = _target_stop_order_class(row, source_component)
            decision = _explicit_decision(row, source_component, target_stop_class)
            action_class = _action_class(decision, source_component, target_stop_class)
            source_role = _source_role(decision, source_component, target_stop_class)
            r_evidence_class = _r_evidence_class(source_component, target_stop_class)
            implementation_action = _implementation_action(
                row,
                decision,
                source_component,
                target_stop_class,
            )
            symbol = _symbol(row)
            source_symbol = _norm(row.get("source_symbol")) or symbol
            key = (
                path_text,
                source_hash,
                source_group,
                symbol,
                source_symbol,
                resolve_vnext_symbol_family(symbol or source_symbol) if (symbol or source_symbol) else "",
                _market_timeframe(row, path),
                _route_session(row, path),
                _side(row),
                _horizon_id(row),
                _framework(row, path),
                _route_family(row, path),
                source_component,
                target_stop_class,
                decision,
                action_class,
                source_role,
                r_evidence_class,
                implementation_action,
            )
            if not (source_component or symbol or source_symbol):
                continue
            group = groups.get(key)
            if group is None:
                group = Group(*key)
                groups[key] = group
            group.add(row)

    rows = [group.to_row() for group in groups.values()]
    rows.sort(key=lambda row: row["row_key"])
    runtime_source_rows_represented = sum(int(row["source_rows_represented"]) for row in rows)
    counted_source_rows = sum(
        int(stat["rows"]) for stat in source_stats if isinstance(stat.get("rows"), int)
    )
    summary = {
        "schema_version": "gtos_vnext_adverse_stop_first_execution_runtime_summary_v1",
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": runtime_source_rows_represented,
        "wave_source_rows_counted": counted_source_rows,
        "wave_source_artifact_count": len(source_stats),
        "wave_source_artifact_suffix_counts": dict(
            sorted(Counter(stat["suffix"] for stat in source_stats).items())
        ),
        "row_count_unknown_source_artifact_count": sum(
            1 for stat in source_stats if stat.get("rows") is None
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in rows).items())
        ),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in rows).items())
        ),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "target_stop_order_class_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows if row.get("target_stop_order_class")).items())
        ),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "framework_counts": dict(
            sorted(Counter(row["framework"] for row in rows if row.get("framework")).items())
        ),
        "route_family_counts": dict(
            sorted(Counter(row["route_family"] for row in rows if row.get("route_family")).items())
        ),
        "source_artifacts": source_stats,
        "output_rows": str(OUTPUT_ROWS),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build rows without writing outputs")
    args = parser.parse_args()
    rows, summary = build_rows()
    if not args.check:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        OUTPUT_SUMMARY.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    printable = dict(summary)
    printable["source_artifacts"] = f"{len(summary['source_artifacts'])} artifacts"
    printable["source_group_counts"] = f"{len(summary['source_group_counts'])} groups"
    print(json.dumps(printable, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
