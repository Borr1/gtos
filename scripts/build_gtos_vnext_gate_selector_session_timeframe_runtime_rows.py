#!/usr/bin/env python3
"""Build compact runtime rows for gate/selector/session/timeframe evidence."""

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
WAVE_ID = "WAVE_GATE_SELECTOR_SESSION_TIMEFRAME_BEHAVIOR"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_gate_selector_session_timeframe_runtime_rows",
    "gtos_vnext_gate_selector_session_timeframe_runtime_summary",
)
SESSION_WILDCARD = "ALL_SESSIONS"
KNOWN_ROUTE_FAMILIES = {
    "moonshot_mechanical",
    "moonshot_control_screen",
    "moonshot_control_screen_route_queue",
    "moonshot_gtos_replay_blocker",
    "moonshot_accepted_builder",
    "moonshot_accepted_builder_binding",
    "moonshot_accepted_builder_branch",
    "moonshot_accepted_builder_entry_adverse",
    "moonshot_accepted_builder_family",
    "moonshot_accepted_builder_m15",
    "moonshot_accepted_builder_m1",
    "moonshot_accepted_builder_positive",
    "moonshot_accepted_builder_source",
    "moonshot_accepted_builder_rejected_repair",
    "numeric_router",
    "cp281_native_rule",
    "mechanical_ai_selector",
    "nofill_mechanical",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    return str(value).strip().casefold() in {"1", "true", "yes", "y", "on"}


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
        "HISTORICAL_OHLC_GTOS_REPLAY_",
        "MAIN_ORCH48_",
        "MAIN_ORCH24_",
        "READY8_",
        "R8DISC_",
        "G0_SCID_",
        "G0NAPI_",
        "G12_",
        "UNC004_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-18.jsonl",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_LEDGER_2026-05-15.jsonl",
        "_2026-05-18.jsonl",
        "_2026-05-17.jsonl",
        "_2026-05-16.jsonl",
        "_2026-05-15.jsonl",
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
    if route_candidate_id:
        parts = [part.strip() for part in route_candidate_id.split("|")]
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    selector_scope = _norm(row.get("selector_scope_key") or row.get("mechanical_scope_key"))
    if selector_scope and "|" in selector_scope:
        parts = [part.strip() for part in selector_scope.split("|")]
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


def _clean_route_session(value: str) -> str:
    raw = _norm(value)
    key = raw.casefold().replace("-", "_").replace(" ", "_")
    if key in {"", "none", "na", "n/a", "null", "unknown", "other", "all_available_or_unmapped_sessions"}:
        return SESSION_WILDCARD if raw else ""
    return raw


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _variant, _horizon = _route_parts(row)
    for key in (
        "symbol",
        "source_symbol",
        "market",
        "instrument",
        "candidate_symbol",
        "selected_symbol",
    ):
        if value := _norm(row.get(key)):
            return value
    if route_symbol:
        return route_symbol
    candidate_id = _norm(row.get("candidate_id") or row.get("event_id") or row.get("row_key"))
    if "_20" in candidate_id:
        return candidate_id.split("_20", 1)[0]
    return ""


def _route_session(row: dict[str, Any], path: Path, source_component: str = "") -> str:
    _symbol, route_session, _variant, _horizon = _route_parts(row)
    for key in ("route_session", "session", "kill_zone", "session_name", "mapped_route_session"):
        if value := _clean_route_session(_norm(row.get(key))):
            return value
    if route_session:
        return _clean_route_session(route_session)
    name = path.name.casefold()
    if "tokyo" in name:
        return "tokyo_kz"
    if "london" in name:
        return "london_core"
    if "_ny_" in name or "ny_core" in name:
        return "ny_core"
    for key in ("decision_time_utc", "decision_asof_utc", "bar_time_utc", "timestamp", "created_at_utc"):
        if value := _norm(row.get(key)):
            session = _session_from_time(value)
            if session:
                return _clean_route_session(session)
    if source_component.startswith("gate_") or "confidence" in source_component:
        return SESSION_WILDCARD
    return ""


def _market_timeframe(row: dict[str, Any], path: Path) -> str:
    for key in ("market_timeframe", "timeframe", "source_timeframe", "tf"):
        if value := _norm(row.get(key)):
            return value.upper()
    name = path.name.casefold()
    if "m1" in name:
        return "M1"
    if "m5" in name:
        return "M5"
    if "m15" in name:
        return "M15"
    if "h1" in name:
        return "H1"
    if "h4" in name:
        return "H4"
    if "d1" in name:
        return "D1"
    return ""


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol, _session, _variant, horizon = _route_parts(row)
    raw = _norm(row.get("horizon_id") or row.get("horizon") or row.get("horizon_m15_bars") or horizon)
    if raw and raw.isdigit():
        return f"h{raw}"
    return raw


def _side(row: dict[str, Any]) -> str:
    for key in ("side", "selected_side", "direction", "trade_side"):
        value = _norm(row.get(key)).upper()
        if value in {"LONG", "SHORT"}:
            return value
    return ""


def _framework(row: dict[str, Any], path: Path) -> str:
    for key in ("framework", "setup_framework", "framework_name", "poi_framework"):
        if value := _norm(row.get(key)):
            return value
    text = _text_blob(path, row).casefold()
    if "breaker" in text:
        return "breaker_re_entry"
    if "fvg" in text:
        return "fvg_fill"
    if "ob_retest" in text or "order_block" in text:
        return "ob_retest"
    return ""


def _route_family(row: dict[str, Any], path: Path, source_component: str, framework: str) -> str:
    if value := _norm(row.get("route_family")):
        if value in KNOWN_ROUTE_FAMILIES:
            return value
    text = _text_blob(path, row).casefold()
    if "mechanical_selector" in text or "selector" in source_component:
        return "mechanical_ai_selector"
    if source_component.startswith("nofill_"):
        return "nofill_mechanical"
    if framework == "ob_retest":
        return "moonshot_mechanical"
    if framework == "fvg_fill":
        return "moonshot_mechanical"
    if framework == "breaker_re_entry":
        return "moonshot_mechanical"
    return "numeric_router"


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "gate_selector_session_timeframe_runtime_row_id",
        "gate_surface_row_id",
        "confidence_active_guard_row_id",
        "production_change_dossier_row_id",
        "selector_recommendation_row_id",
        "touch_count_gate_join_row_id",
        "row_id",
        "row_key",
        "source_row_id",
        "candidate_id",
        "event_id",
    ):
        if value := _norm(row.get(key)):
            return value
    for key, value in row.items():
        if isinstance(key, str) and key.endswith("_id") and _norm(value):
            return _norm(value)
    stable_row = {str(key): value for key, value in row.items()}
    return _sha256_text(json.dumps(stable_row, sort_keys=True, default=str))[:24]


def _clean_code_component(component: str, path: Path, row: dict[str, Any]) -> str:
    component_text = component.casefold()
    if not component or not (
        component_text.startswith("src/")
        or component_text.startswith("src\\")
        or "/" in component_text
        or "\\" in component_text
        or ".py" in component_text
        or "::" in component_text
    ):
        return component
    gate_surface = _norm(row.get("gate_surface")).casefold()
    if gate_surface:
        return f"gate_{gate_surface}".replace("-", "_").replace(" ", "_")
    text = _text_blob(path, row).casefold()
    if "touch_count" in text:
        return "gate_touch_count"
    if "sl_beyond" in text:
        return "gate_sl_beyond_ob"
    if "pre_ai" in text and "poi" in text:
        return "gate_pre_ai_poi_availability"
    if "confidence" in text:
        return "confidence_filter_quarantine"
    if "correlation" in text:
        return "gate_cross_instrument_correlation"
    return "gate_filter_selector_runtime_mapping"


def _source_component(path: Path, row: dict[str, Any]) -> str:
    component = _clean_code_component(_norm(row.get("source_component")), path, row)
    if component:
        return component
    gate_surface = _norm(row.get("gate_surface")).casefold()
    if gate_surface:
        return f"gate_{gate_surface}".replace("-", "_").replace(" ", "_")
    name = path.name.casefold()
    text = _text_blob(path, row).casefold()
    if "confidence" in name or "confidence" in text:
        return "confidence_filter_quarantine"
    if "touch_count" in name or "touch_count" in text:
        return "gate_touch_count"
    if "sl_beyond" in name or "sl_beyond" in text:
        return "gate_sl_beyond_ob"
    if "pre_ai" in name and "poi" in text:
        return "gate_pre_ai_poi_availability"
    if "correlation" in name or "correlation" in text:
        return "gate_cross_instrument_correlation"
    if "ltf_selector" in name or "ltf_selector" in text:
        return "ltf_selector_repair"
    if "fvg_ob" in name or "fvg_ob" in text or "fvg" in text:
        return "fvg_ob_framework_repair"
    if "kill_scope" in name or "kill_label" in name:
        return "kill_scope_preservation"
    if "selector" in name or "selector" in text:
        return "selector_shadow_source_guard"
    if "session" in name or "timeframe" in name:
        return "session_timeframe_selector"
    if "framework" in name or "gate" in name:
        return "framework_gate_selector"
    if "k54" in name or "k55" in name or "ml_shadow" in name:
        return "ml_shadow_selector"
    return "gate_selector_session_timeframe_context"


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


def _numeric_candidates(row: dict[str, Any]) -> list[tuple[str, float]]:
    values: list[tuple[str, float]] = []
    for field_name in (
        "cost_adjusted_simulated_r",
        "net_proxy_r_weighted_mean",
        "net_proxy_r_mean",
        "proxy_r_mean",
        "stress_proxy_r",
        "stress_simulated_r",
        "proxy_score",
        "score",
        "mean_r",
        "expectancy_r",
        "delta_r",
        "win_rate_delta",
        "lift",
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


def _explicit_decision(row: dict[str, Any]) -> str:
    for key in (
        "decision",
        "computed_decision",
        "primary_decision",
        "selector_decision",
        "recommendation_decision",
        "implementation_decision",
        "recommended_next_action",
        "selector_recommendation_status",
        "production_change_dossier_status",
        "capture_status",
        "status",
        "verdict",
        "outcome",
        "action_class",
    ):
        value = _norm(row.get(key)).upper()
        if not value:
            continue
        if any(token in value for token in ("AVOID", "REJECT", "BLOCK", "KILL", "QUARANTINE", "NEGATIVE", "FAIL_CLOSED")):
            return "AVOID"
        if any(token in value for token in ("REPAIR", "REQUIRED", "GAP", "DEFER", "DORMANT", "MISSING", "UNKNOWN", "AMBIGU")):
            return "MIXED"
        if any(token in value for token in ("FOLLOW", "PASS", "ACCEPT", "IMPLEMENT_READY", "IMPLEMENT", "PRESERVE", "KEEP")):
            return "FOLLOW"
    return ""


def _decision(path: Path, row: dict[str, Any]) -> str:
    explicit = _explicit_decision(row)
    if explicit:
        return explicit
    text = _text_blob(path, row).upper()
    if any(token in text for token in ("REJECT", "BLOCK", "KILL", "AVOID", "QUARANTINE", "FAIL_CLOSED")):
        return "AVOID"
    if any(token in text for token in ("REPAIR", "REQUIRED", "GAP", "MISSING", "AMBIGU", "DORMANT")):
        return "MIXED"
    if any(token in text for token in ("FOLLOW", "PASS", "ACCEPTED", "IMPLEMENT_READY", "KEEP")):
        return "FOLLOW"
    values = [value for _field, value in _numeric_candidates(row)]
    if values:
        if max(values) <= 0 and min(values) < 0:
            return "AVOID"
        if min(values) >= 0 and max(values) > 0:
            return "FOLLOW"
    return "MIXED"


def _action_class(decision: str, source_component: str) -> str:
    if source_component == "confidence_filter_quarantine":
        return "confidence_quarantine_filter"
    if "repair" in source_component:
        return "framework_gate_repair_filter" if decision == "AVOID" else "framework_gate_repair_context"
    if source_component.startswith("gate_") and decision == "AVOID":
        return "gate_filter_selector_avoid_filter"
    if source_component.startswith("gate_"):
        return "gate_filter_selector_context_guard"
    if "selector" in source_component and decision == "FOLLOW":
        return "selector_follow_scorer"
    if decision == "AVOID":
        return "gate_selector_avoid_filter"
    if decision == "FOLLOW":
        return "gate_selector_follow_scorer"
    return "gate_selector_context_guard"


def _source_role(path: Path, row: dict[str, Any], source_component: str, decision: str) -> str:
    text = _text_blob(path, row).upper()
    if "REPAIR" in text or "REQUIRED" in text or "GAP" in text or "MISSING" in text:
        return "gate_selector_repair_guard"
    if source_component == "confidence_filter_quarantine":
        return "confidence_filter_shadow_guard"
    if decision == "AVOID":
        return "gate_selector_avoid_guard"
    if decision == "FOLLOW":
        return "gate_selector_follow_pressure"
    return "gate_selector_session_timeframe_context"


def _r_evidence_class(source_component: str, source_role: str) -> str:
    if "repair" in source_role or "repair" in source_component:
        return "GATE_SELECTOR_REPAIR"
    if source_component == "confidence_filter_quarantine":
        return "CONFIDENCE_FILTER_POLICY"
    if "session" in source_component or "timeframe" in source_component:
        return "SESSION_TIMEFRAME_SELECTOR"
    return "GATE_SELECTOR_FRAMEWORK"


def _implementation_action(path: Path, row: dict[str, Any], decision: str, source_role: str) -> str:
    for key in (
        "implementation_action",
        "implementation_decision",
        "recommended_next_action",
        "selector_recommendation_status",
        "production_change_dossier_status",
        "capture_status",
        "next_action",
    ):
        if value := _norm(row.get(key)):
            return value
    if "repair" in source_role:
        return "GATE_SELECTOR_REPAIR_OR_SOURCE_CAPTURE_REQUIRED"
    if decision == "AVOID":
        return "IMPLEMENT_GATE_SELECTOR_AVOID_FILTER_SCOPE"
    if decision == "FOLLOW":
        return "REGISTER_GATE_SELECTOR_FOLLOW_SCORER_SCOPE"
    return "KEEP_GATE_SELECTOR_SESSION_TIMEFRAME_CONTEXT"


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
        "source_shape": "gate_selector_session_timeframe_compact_scope",
    }


def _metric_from_row(row: dict[str, Any], metric: str) -> float | None:
    metrics = row.get("r_metrics")
    if isinstance(metrics, dict) and isinstance(metrics.get(metric), dict):
        trace = metrics[metric]
        value = _to_float(trace.get("sum") if trace.get("sum") is not None else trace.get("mean"))
        if value is not None:
            return value
    return _to_float(row.get(metric))


def _row_weight(row: dict[str, Any]) -> int:
    for key in (
        "decision_rows",
        "event_rows",
        "registry_match_rows",
        "implementation_ready_candidate_rows",
        "expected_candidate_found_in_registry_rows",
        "source_rows_represented",
        "row_count",
        "event_count",
        "sample_count",
        "n",
    ):
        value = _to_float(row.get(key))
        if value is not None and value > 0:
            return max(1, int(round(value)))
    metrics = row.get("r_metrics")
    if isinstance(metrics, dict):
        effective = metrics.get("effective_n")
        if isinstance(effective, dict):
            value = _to_float(effective.get("sum") or effective.get("count"))
            if value is not None and value > 0 and value <= 100000:
                return max(1, int(round(value)))
    return 1


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
    decision: str
    action_class: str
    source_role: str
    r_evidence_class: str
    implementation_action: str
    rows: int = 0
    source_rows_represented: int = 0
    cost_adjusted_sum: float = 0.0
    proxy_score_sum: float = 0.0
    stress_sum: float = 0.0
    source_row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.source_rows_represented += _row_weight(row)
        for metric in ("cost_adjusted_simulated_r", "net_proxy_r_mean", "mean_r", "expectancy_r"):
            value = _metric_from_row(row, metric)
            if value is not None:
                self.cost_adjusted_sum += value
        for metric in ("proxy_score", "score", "lift", "win_rate_delta"):
            value = _metric_from_row(row, metric)
            if value is not None:
                self.proxy_score_sum += value
        for metric in ("stress_simulated_r", "stress_proxy_r"):
            value = _metric_from_row(row, metric)
            if value is not None:
                self.stress_sum += value
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
                self.decision,
                self.action_class,
                self.source_role,
                self.r_evidence_class,
                self.implementation_action,
            ]
        )
        row_id = f"gate_selector_session_timeframe:{_sha256_text(key_payload)[:24]}"
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
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.source_rows_represented or self.rows),
                max(float(self.rows), 1.0),
                "gate_selector_session_timeframe_source_rows",
            )
        }
        if self.cost_adjusted_sum:
            metrics["cost_adjusted_simulated_r"] = _metric_trace(
                self.cost_adjusted_sum,
                max(float(self.rows), 1.0),
                "gate_selector_session_timeframe_cost_fields",
            )
        if self.proxy_score_sum:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_score_sum,
                max(float(self.rows), 1.0),
                "gate_selector_session_timeframe_proxy_fields",
            )
        if self.stress_sum:
            metrics["stress_simulated_r"] = _metric_trace(
                self.stress_sum,
                max(float(self.rows), 1.0),
                "gate_selector_session_timeframe_stress_fields",
            )
        return {
            "schema_version": "gtos_vnext_gate_selector_session_timeframe_runtime_row_v1",
            "row_key": row_id,
            "gate_selector_session_timeframe_runtime_row_id": row_id,
            "source_name": "gtos_vnext_gate_selector_session_timeframe_wave",
            "evidence_family": "gtos_vnext_gate_selector_session_timeframe",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": "gate_selector_session_timeframe_runtime",
            "runtime_effect_now": "gate_selector_session_timeframe_runtime_pressure",
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "r_evidence_class": self.r_evidence_class,
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
            "source_path": self.source_path,
            "drill_through_path": self.source_path,
            "source_artifact_hash_sha256": self.source_hash,
            "source_rows_represented": self.source_rows_represented,
            "source_row_ids_sample": self.source_row_ids_sample,
            "source_bound": bool((self.symbol or self.source_symbol or self.symbol_family) and self.route_session),
            "source_complete": self.decision in {"FOLLOW", "AVOID"},
            "runtime_candidate_use_permitted": self.decision == "FOLLOW",
            "candidate_use_allowed_now": False,
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


def _gate_decision_count_rows(path: Path, row: dict[str, Any]) -> list[dict[str, Any]]:
    counts = row.get("decision_counts") or row.get("pre_ai_gate_reason_counts")
    if not isinstance(counts, dict) or not counts:
        return [row]
    expanded: list[dict[str, Any]] = []
    for key, value in counts.items():
        count = _to_float(value)
        if count is None or count <= 0:
            continue
        copied = dict(row)
        key_text = str(key)
        copied["source_rows_represented"] = int(round(count))
        copied["decision_count_key"] = key_text
        if "reject" in key_text.casefold() or "no_" in key_text.casefold():
            copied["computed_decision"] = "AVOID"
        elif "pass" in key_text.casefold() or "follow" in key_text.casefold():
            copied["computed_decision"] = "FOLLOW"
        else:
            copied["computed_decision"] = _decision(path, row)
        copied["source_row_id"] = f"{_row_id(row)}:{key_text}"
        expanded.append(copied)
    return expanded or [row]


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
        for source_row in runtime_rows:
            for row in _gate_decision_count_rows(path, source_row):
                source_component = _source_component(path, row)
                symbol = _symbol(row)
                source_symbol = _norm(row.get("source_symbol")) or symbol
                route_session = _route_session(row, path, source_component)
                framework = _framework(row, path)
                route_family = _route_family(row, path, source_component, framework)
                decision = _decision(path, row)
                action_class = _action_class(decision, source_component)
                source_role = _source_role(path, row, source_component, decision)
                r_evidence_class = _r_evidence_class(source_component, source_role)
                implementation_action = _implementation_action(path, row, decision, source_role)
                key = (
                    path_text,
                    source_hash,
                    source_group,
                    symbol,
                    source_symbol,
                    resolve_vnext_symbol_family(symbol or source_symbol) if (symbol or source_symbol) else "",
                    _market_timeframe(row, path),
                    route_session,
                    _side(row),
                    _horizon_id(row),
                    framework,
                    route_family,
                    source_component,
                    decision,
                    action_class,
                    source_role,
                    r_evidence_class,
                    implementation_action,
                )
                if not (source_component or symbol or source_symbol or route_session):
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
        "schema_version": "gtos_vnext_gate_selector_session_timeframe_runtime_summary_v1",
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
