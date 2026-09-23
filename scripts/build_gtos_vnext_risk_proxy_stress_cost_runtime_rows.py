#!/usr/bin/env python3
"""Build compact runtime rows for risk/R/proxy/stress/cost wave evidence."""

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
WAVE_ID = "WAVE_RISK_R_PROXY_STRESS_COST_BEHAVIOR"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_risk_proxy_stress_cost_runtime_rows",
    "gtos_vnext_risk_proxy_stress_cost_runtime_summary",
)


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
    units = [
        row
        for row in rows
        if row.get("batch_wave_id") == WAVE_ID
        or (
            row.get("conversion_state") in master_ledger.OPEN_BATCH_STATES
            and master_ledger._batch_wave_id_for_row(row) == WAVE_ID
        )
    ]
    return sorted(units, key=lambda row: str(row.get("source_artifact_path") or "").casefold())


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
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_",
        "HISTORICAL_OHLC_GTOS_REPLAY_",
        "MAIN_ORCH48_",
        "READY8_",
        "R10_",
        "OTI2_",
        "G0_",
        "G12_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-18.jsonl",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
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
    route_candidate_id = _norm(row.get("route_candidate_id"))
    if route_candidate_id:
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


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _variant, _horizon = _route_parts(row)
    for key in ("symbol", "source_symbol", "market", "instrument", "candidate_symbol"):
        if value := _norm(row.get(key)):
            return value
    if route_symbol:
        return route_symbol
    candidate_id = _norm(row.get("candidate_id") or row.get("event_id"))
    if "_20" in candidate_id:
        return candidate_id.split("_20", 1)[0]
    return ""


def _route_session(row: dict[str, Any], path: Path) -> str:
    _symbol, route_session, _variant, _horizon = _route_parts(row)
    for key in ("route_session", "session", "kill_zone", "session_name"):
        if value := _norm(row.get(key)):
            return value
    if route_session:
        return route_session
    name = path.name.casefold()
    if "tokyo" in name:
        return "tokyo_kz"
    if "london" in name:
        return "london_core"
    if "_ny_" in name or "ny_core" in name:
        return "ny_core"
    for key in ("decision_time_utc", "decision_asof_utc", "bar_time_utc", "timestamp"):
        if value := _norm(row.get(key)):
            return _session_from_time(value)
    return ""


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol, _session, _variant, horizon = _route_parts(row)
    raw = _norm(row.get("horizon_id") or row.get("horizon") or row.get("horizon_m15_bars") or horizon)
    if raw and raw.isdigit():
        return f"h{raw}"
    return raw


def _market_timeframe(row: dict[str, Any], path: Path) -> str:
    for key in ("market_timeframe", "timeframe", "source_timeframe", "tf"):
        if value := _norm(row.get(key)):
            return value.upper()
    name = path.name.casefold()
    if "m1" in name:
        return "M1"
    if "m15" in name or "main_orch" in name:
        return "M15"
    if "h1" in name:
        return "H1"
    return ""


def _side(row: dict[str, Any]) -> str:
    for key in ("side", "selected_side", "direction", "trade_side"):
        value = _norm(row.get(key)).upper()
        if value in {"LONG", "SHORT"}:
            return value
    return ""


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "risk_proxy_stress_cost_runtime_row_id",
        "source_cost_cap_row_id",
        "cost_proxy_row_id",
        "rstyle_proxy_row_id",
        "branch_queue_id",
        "packet_row_id",
        "bucket_id",
        "row_id",
        "row_key",
        "source_row_id",
        "candidate_id",
        "event_id",
    ):
        if value := _norm(row.get(key)):
            return value
    for key, value in row.items():
        if key.endswith("_id") and _norm(value):
            return _norm(value)
    return _sha256_text(json.dumps(row, sort_keys=True, default=str))[:24]


def _source_component(path: Path, row: dict[str, Any]) -> str:
    if component := _norm(row.get("source_component")):
        return component
    name = path.name.casefold()
    text = " ".join(_norm(value).casefold() for value in row.values() if isinstance(value, str))
    if "source_cost_cap" in name or "cost_cap" in name:
        return "risk_source_cost_cap"
    if "cost_fill" in name or "spread" in name or "cost_proxy" in name:
        return "risk_cost_fill_proxy"
    if "rstyle" in name:
        return "risk_rstyle_proxy_outcome"
    if "source_stress" in name or "stress_acquisition" in name:
        return "risk_source_stress_acquisition"
    if "stress" in name or "stress" in text:
        return "risk_stress_robustness"
    if "riskbank" in name or "risk_mc" in name or "s79" in name or "side_aware" in name:
        return "risk_sizing_policy"
    if "api_cost" in name or "cost_log" in name or "budget" in name:
        return "risk_ai_cost_control"
    if "proxy_gap" in name or "proxy_blocker" in name:
        return "risk_proxy_gap_status"
    if "touch_count" in name:
        return "risk_touch_count_proxy"
    return "risk_proxy_stress_cost_context"


def _text_blob(path: Path, row: dict[str, Any]) -> str:
    parts = [path.name]
    for value in row.values():
        if isinstance(value, (str, int, float, bool)):
            parts.append(str(value))
        elif isinstance(value, dict):
            parts.extend(str(key) for key in value.keys())
            parts.extend(str(value_) for value_ in value.values() if isinstance(value_, (str, int, float, bool)))
    return " ".join(parts).upper()


def _numeric_candidates(row: dict[str, Any]) -> list[tuple[str, float]]:
    fields = (
        "cost_adjusted_simulated_r",
        "net_proxy_r_weighted_mean",
        "net_proxy_r_mean",
        "proxy_r_mean",
        "stress_proxy_r",
        "stress_simulated_r",
        "proxy_score",
        "repaired_proxy_event_score",
        "source_return_minus_control",
        "score_minus_same_scope_default",
        "raw_neutral_target_movement_delta",
        "control_adjusted_residual_abs",
        "rstyle_midpoint_mean",
        "rstyle_lower_mean",
        "rstyle_upper_mean",
        "spread_proxy_value",
        "exp_drop_r",
        "delta_r",
        "score",
    )
    values: list[tuple[str, float]] = []
    for field_name in fields:
        numeric = _to_float(row.get(field_name))
        if numeric is not None:
            values.append((field_name, numeric))
    return values


def _decision(path: Path, row: dict[str, Any]) -> str:
    text = _text_blob(path, row)
    numeric_values = [value for _field, value in _numeric_candidates(row)]
    if any(
        token in text
        for token in (
            "ALL_NEGATIVE",
            "STRONG_NEGATIVE",
            "NEGATIVE_PROXY",
            "STOP_FIRST",
            "FAIL_CLOSED",
            "REJECTED",
            "AVOID",
            "SOURCE_REJECTED",
        )
    ):
        return "AVOID"
    if any(token in text for token in ("REPAIR", "REQUIRED_NOT_ACQUIRED", "NO_SCALAR", "STRADDLES_ZERO")):
        return "MIXED"
    if any(token in text for token in ("STRONG_POSITIVE", "POSITIVE_PROXY", "ACCEPTED", "PASS", "TARGET_FIRST")):
        return "FOLLOW"
    if numeric_values:
        if max(numeric_values) <= 0 and min(numeric_values) < 0:
            return "AVOID"
        if min(numeric_values) >= 0 and max(numeric_values) > 0:
            return "FOLLOW"
    return "MIXED"


def _proxy_class(path: Path, row: dict[str, Any], decision: str) -> str:
    text = _text_blob(path, row)
    if "STRONG_NEGATIVE" in text or "ALL_NEGATIVE" in text:
        return "STRONG_NEGATIVE_PROXY_R"
    if "NEGATIVE_PROXY" in text:
        return "NEGATIVE_PROXY_R"
    if "STRONG_POSITIVE" in text:
        return "STRONG_POSITIVE_PROXY_R"
    if "POSITIVE_PROXY" in text:
        return "POSITIVE_PROXY_R"
    if "STRADDLES_ZERO" in text or "AMBIGU" in text or "NO_SCALAR" in text:
        return "BOUNDED_AMBIGUOUS_PROXY_R"
    values = [value for _field, value in _numeric_candidates(row)]
    if values:
        mean = sum(values) / len(values)
        if mean <= -0.25:
            return "STRONG_NEGATIVE_PROXY_R"
        if mean < 0:
            return "NEGATIVE_PROXY_R"
        if mean >= 0.25:
            return "STRONG_POSITIVE_PROXY_R"
        if mean > 0:
            return "POSITIVE_PROXY_R"
    if decision == "AVOID":
        return "NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        return "POSITIVE_PROXY_R"
    return "FLAT_PROXY_R"


def _target_stop_order_class(path: Path, row: dict[str, Any]) -> str:
    text = _text_blob(path, row)
    if "STOP_FIRST" in text:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in text:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "TARGET_STOP" in text and ("FLIP" in text or "AMBIGU" in text or "STRADDLES_ZERO" in text):
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    if "NOT_SOURCE_BOUND" in text:
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    return ""


def _action_class(decision: str, source_component: str, proxy_class: str) -> str:
    if source_component == "risk_sizing_policy":
        return "risk_sizing_context"
    if decision == "AVOID":
        return "risk_proxy_cost_avoid_filter"
    if decision == "FOLLOW":
        return "risk_proxy_follow_scorer"
    if "AMBIGUOUS" in proxy_class or "risk_source" in source_component:
        return "risk_proxy_stress_context_guard"
    return "risk_proxy_stress_context"


def _source_role(row: dict[str, Any], source_component: str, decision: str) -> str:
    text = " ".join(_norm(value).upper() for value in row.values() if isinstance(value, str))
    if "REPAIR" in text or "REQUIRED_NOT_ACQUIRED" in text or "FAIL_CLOSED" in text:
        return "risk_proxy_stress_cost_repair_guard"
    if source_component == "risk_sizing_policy":
        return "risk_sizing_policy_context"
    if decision == "AVOID":
        return "risk_proxy_stress_cost_avoid_guard"
    if decision == "FOLLOW":
        return "risk_proxy_stress_cost_follow_pressure"
    return "risk_proxy_stress_cost_context"


def _r_evidence_class(row: dict[str, Any], source_component: str, source_role: str) -> str:
    if "repair" in source_role or "source_cost_cap" in source_component or "source_stress" in source_component:
        return "RISK_PROXY_STRESS_COST_REPAIR"
    if source_component == "risk_sizing_policy":
        return "RISK_SIZING_POLICY"
    if source_component == "risk_ai_cost_control":
        return "AI_COST_CONTROL"
    return "RISK_PROXY_STRESS_COST"


def _implementation_action(path: Path, row: dict[str, Any], decision: str, source_role: str) -> str:
    for key in (
        "implementation_action",
        "next_same_resource_action",
        "repair_implementation_action",
        "cost_cap_policy",
        "branch_result_binary",
        "source_cost_cap_detail_status",
        "source_builder_result_status",
        "source_result_status",
    ):
        if value := _norm(row.get(key)):
            return value
    if "repair" in source_role:
        return "RISK_PROXY_STRESS_COST_REPAIR_REQUIRED"
    if decision == "AVOID":
        return "REGISTER_RISK_PROXY_COST_AVOID_FILTER"
    if decision == "FOLLOW":
        return "REGISTER_RISK_PROXY_FOLLOW_SCORER"
    return "KEEP_RISK_PROXY_STRESS_COST_AS_CONTEXT"


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
        "source_shape": "risk_proxy_stress_cost_compact_scope",
    }


def _row_weight(row: dict[str, Any]) -> int:
    for key in (
        "branch_count",
        "row_count",
        "event_count",
        "source_rows_represented",
        "pass_unique_duplicate_denominator_count",
        "control_unique_duplicate_denominator_count",
        "observed_spread_count",
        "window_requirement_rows",
        "support_rows_matched",
    ):
        value = _to_float(row.get(key))
        if value is not None and value > 0:
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
    source_component: str
    decision: str
    proxy_r_class: str
    target_stop_order_class: str
    action_class: str
    source_role: str
    r_evidence_class: str
    implementation_action: str
    rows: int = 0
    source_rows_represented: int = 0
    source_acquisition_required_rows: int = 0
    cost_adjusted_sum: float = 0.0
    proxy_score_sum: float = 0.0
    stress_sum: float = 0.0
    row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        weight = _row_weight(row)
        self.source_rows_represented += weight
        text = _text_blob(Path(self.source_path), row)
        self.source_acquisition_required_rows += int(
            "REQUIRED_NOT_ACQUIRED" in text or "FAIL_CLOSED" in text or _truthy(row.get("source_acquisition_required"))
        )
        for field_name, value in _numeric_candidates(row):
            if "stress" in field_name:
                self.stress_sum += value
            elif "cost" in field_name or "rstyle" in field_name:
                self.cost_adjusted_sum += value
            else:
                self.proxy_score_sum += value
        if row_id := _row_id(row):
            if len(self.row_ids_sample) < 5:
                self.row_ids_sample.append(row_id)

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
                self.source_component,
                self.decision,
                self.proxy_r_class,
                self.target_stop_order_class,
                self.action_class,
                self.source_role,
                self.r_evidence_class,
                self.implementation_action,
            ]
        )
        row_id = f"risk_proxy_stress_cost:{_sha256_text(key_payload)[:24]}"
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
                "source_component": self.source_component,
                "route_family": "numeric_router",
                "action_class": self.action_class,
                "proxy_r_class": self.proxy_r_class,
                "target_stop_order_class": self.target_stop_order_class,
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.source_rows_represented or self.rows),
                max(float(self.rows), 1.0),
                "risk_proxy_stress_cost_source_rows",
            )
        }
        if self.cost_adjusted_sum:
            metrics["cost_adjusted_simulated_r"] = _metric_trace(
                self.cost_adjusted_sum,
                max(float(self.rows), 1.0),
                "risk_proxy_stress_cost_cost_fields",
            )
        if self.proxy_score_sum:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_score_sum,
                max(float(self.rows), 1.0),
                "risk_proxy_stress_cost_proxy_fields",
            )
        if self.stress_sum:
            metrics["stress_simulated_r"] = _metric_trace(
                self.stress_sum,
                max(float(self.rows), 1.0),
                "risk_proxy_stress_cost_stress_fields",
            )
        return {
            "schema_version": "gtos_vnext_risk_proxy_stress_cost_runtime_row_v1",
            "row_key": row_id,
            "risk_proxy_stress_cost_runtime_row_id": row_id,
            "source_name": "gtos_vnext_risk_proxy_stress_cost_wave",
            "evidence_family": "gtos_vnext_risk_proxy_stress_cost",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": "risk_proxy_stress_cost_runtime",
            "runtime_effect_now": "risk_proxy_stress_cost_runtime_pressure",
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "r_evidence_class": self.r_evidence_class,
            "decision": self.decision,
            "source_component": self.source_component,
            "proxy_r_class": self.proxy_r_class,
            "target_stop_order_class": self.target_stop_order_class,
            "route_family": "numeric_router",
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
            "source_row_ids_sample": self.row_ids_sample,
            "source_acquisition_required": self.source_acquisition_required_rows > 0,
            "source_acquisition_required_rows": self.source_acquisition_required_rows,
            "source_bound": bool(self.symbol or self.source_symbol or self.symbol_family),
            "source_complete": self.decision in {"FOLLOW", "AVOID"} and self.source_acquisition_required_rows == 0,
            "runtime_candidate_use_permitted": self.decision == "FOLLOW",
            "candidate_use_allowed_now": False,
            "r_metrics": metrics,
            "event_scope": scope,
        }


def _read_runtime_source_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
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
        return rows
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            return [payload]
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
            symbol = _symbol(row)
            source_symbol = _norm(row.get("source_symbol")) or symbol
            source_component = _source_component(path, row)
            decision = _decision(path, row)
            proxy_class = _proxy_class(path, row, decision)
            target_stop_order_class = _target_stop_order_class(path, row)
            action_class = _action_class(decision, source_component, proxy_class)
            source_role = _source_role(row, source_component, decision)
            r_evidence_class = _r_evidence_class(row, source_component, source_role)
            implementation_action = _implementation_action(path, row, decision, source_role)
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
                source_component,
                decision,
                proxy_class,
                target_stop_order_class,
                action_class,
                source_role,
                r_evidence_class,
                implementation_action,
            )
            if not (source_component or symbol or source_symbol or _route_session(row, path)):
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
        "schema_version": "gtos_vnext_risk_proxy_stress_cost_runtime_summary_v1",
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
        "proxy_r_class_counts": dict(sorted(Counter(row["proxy_r_class"] for row in rows).items())),
        "target_stop_order_class_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows if row.get("target_stop_order_class")).items())
        ),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "source_acquisition_required_rows": sum(
            int(row.get("source_acquisition_required_rows") or 0) for row in rows
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
