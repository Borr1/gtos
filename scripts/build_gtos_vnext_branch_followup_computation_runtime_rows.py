#!/usr/bin/env python3
"""Build runtime rows for CP280 branch follow-up computation evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
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
WAVE_ID = "WAVE_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_branch_followup_computation_runtime_rows",
    "gtos_vnext_branch_followup_computation_runtime_summary",
)
ROW_BEARING_TOKENS = (
    "binding_preserve_ledger",
    "branch_ledger",
    "bucket_ledger",
    "family_action_ledger",
    "m15_ledger",
    "m1_ledger",
    "positive_ledger",
    "source_router_ledger",
)


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
        lower = raw_path.casefold().replace("\\", "/")
        if not raw_path:
            continue
        if any(token in lower for token in OUTPUT_NAME_TOKENS):
            continue
        if "entry_adverse_ledger" in lower:
            continue
        if not any(token in lower for token in ROW_BEARING_TOKENS):
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


def _source_file_group(path: Path) -> str:
    name = path.name
    prefix = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    suffix = "_LEDGER_2026-05-16.jsonl"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name.lower()


def _row_kind(path: Path) -> str:
    name = path.name.casefold()
    for token, kind in (
        ("binding_preserve", "binding"),
        ("family_action", "family"),
        ("source_router", "source"),
        ("positive", "positive"),
        ("m15", "m15"),
        ("m1", "m1"),
        ("bucket", "bucket"),
        ("branch", "branch"),
    ):
        if token in name:
            return kind
    return "branch"


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route_candidate_id = _norm(row.get("route_candidate_id"))
    if route_candidate_id and "|" in route_candidate_id:
        parts = [part.strip() for part in route_candidate_id.split("|")]
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    return "", "", "", ""


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _primitive, _horizon = _route_parts(row)
    return _norm(row.get("symbol") or row.get("source_symbol") or route_symbol)


def _route_session(row: dict[str, Any]) -> str:
    _symbol_part, route_session, _primitive, _horizon = _route_parts(row)
    return _norm(row.get("route_session") or route_session)


def _primitive(row: dict[str, Any]) -> str:
    _symbol_part, _session, primitive, _horizon = _route_parts(row)
    return primitive


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol_part, _session, _primitive, horizon = _route_parts(row)
    raw = _norm(row.get("horizon_id") or row.get("horizon") or horizon)
    if raw and raw.isdigit():
        return f"h{raw}"
    return raw


def _side(row: dict[str, Any]) -> str:
    value = _upper(row.get("side") or row.get("direction"))
    if value in {"LONG", "SHORT"}:
        return value
    primitive = _primitive(row).casefold()
    if "sweep_low" in primitive or "close_breakout_up" in primitive:
        return "LONG"
    if "sweep_high" in primitive or "close_breakout_down" in primitive:
        return "SHORT"
    return ""


def _market_timeframe(kind: str) -> str:
    if kind == "m1":
        return "M1"
    if kind == "m15":
        return "M15"
    return ""


def _source_component(kind: str) -> str:
    return f"gtos_branch_followup_{kind}"


def _route_family(kind: str) -> str:
    return f"moonshot_branch_followup_{kind}"


def _target_stop_order_class(row: dict[str, Any]) -> str:
    raw = _upper(
        row.get("target_stop_order_class")
        or row.get("target_stop_result")
        or row.get("entry_target_stop_balance_class")
        or row.get("binding_preserve_status")
    )
    if "STOP_FIRST" in raw:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in raw:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "TARGETSTOP_NA" in raw or "NO_TARGET_STOP" in raw or "NO_SCALAR" in raw:
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "AMBIGU" in raw or "NO_FILL" in raw or "STRADDLES" in raw:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return ""


def _decision(kind: str, row: dict[str, Any]) -> str:
    if kind == "binding":
        return "MIXED"
    if kind == "bucket":
        return "MIXED"
    if kind == "m15":
        sign = _upper(row.get("m15_interval_sign_class"))
        if sign == "INTERVAL_ALL_POSITIVE" or "MIDPOINT_POSITIVE" in sign:
            return "FOLLOW"
        if sign == "INTERVAL_ALL_NEGATIVE":
            return "AVOID"
        return "MIXED"
    if kind == "m1":
        if _to_float(row.get("m1_support_midpoint_mean")) is not None:
            return "FOLLOW"
        return "MIXED"
    if kind == "positive":
        status = _upper(row.get("positive_replay_status"))
        if "STRESS_INTERVAL_ONLY" in status:
            return "MIXED"
        return "FOLLOW"
    if kind == "source":
        sign = _upper(row.get("source_stress_interval_sign_class"))
        if sign == "INTERVAL_ALL_NEGATIVE":
            return "AVOID"
        if sign == "INTERVAL_ALL_POSITIVE":
            return "FOLLOW"
        return "MIXED"
    if kind == "family":
        family = _upper(row.get("action_family"))
        score_class = _upper(row.get("family_score_class"))
        score = _to_float(row.get("family_score_proxy"))
        if family == "POSITIVE" and score is not None and score > 0:
            return "FOLLOW"
        if "TARGET_STABLE" in score_class or "POSITIVE_BRANCH_CONFLICT" in score_class:
            return "FOLLOW"
        if "NEGATIVE" in score_class or "STOP_FIRST" in score_class or "AVOID" in score_class:
            return "AVOID"
        if score is not None and score > 0 and "REPAIR" not in score_class:
            return "FOLLOW"
        return "MIXED"
    score_class = _upper(row.get("score_direction_class"))
    if score_class == "CONSERVATIVE_POSITIVE_PROXY":
        return "FOLLOW"
    if score_class in {"CONSERVATIVE_NEGATIVE_PROXY", "MIDPOINT_NEGATIVE_INTERVAL_RISK"}:
        return "AVOID"
    return "MIXED"


def _action_class(kind: str, decision: str, row: dict[str, Any]) -> str:
    if decision == "FOLLOW":
        if kind == "m1":
            return "branch_followup_m1_follow_scorer"
        if kind == "m15":
            return "branch_followup_m15_follow_scorer"
        if kind == "positive":
            return "branch_followup_positive_follow_scorer"
        if kind == "source":
            return "branch_followup_source_follow_scorer"
        return "branch_followup_follow_scorer"
    if decision == "AVOID":
        return "avoid_filter"
    if kind == "binding":
        return "branch_followup_binding_guard"
    if kind == "source":
        return "branch_followup_source_acquisition_guard"
    if kind == "m15":
        return "branch_followup_m15_bounds_guard"
    return "context_guard"


def _source_role(kind: str, decision: str, row: dict[str, Any]) -> str:
    if kind == "binding":
        return "branch_followup_binding_guard"
    if kind == "source":
        return "branch_followup_source_acquisition_guard"
    if decision == "AVOID":
        return "branch_followup_avoid_guard"
    if decision == "FOLLOW":
        return "branch_followup_follow_pressure"
    return "branch_followup_context_guard"


def _runtime_source_group(kind: str, decision: str, row: dict[str, Any]) -> str:
    if kind == "binding":
        return "branch_followup_binding_no_scalar_guard"
    if kind == "bucket":
        return "branch_followup_bucket_context"
    if kind == "m15":
        sign = _upper(row.get("m15_interval_sign_class"))
        if decision == "FOLLOW" and sign == "INTERVAL_ALL_POSITIVE":
            return "branch_followup_m15_target_first_follow"
        if decision == "FOLLOW":
            return "branch_followup_m15_bounds_positive_follow"
        if decision == "AVOID":
            return "branch_followup_m15_stop_first_avoid"
        return "branch_followup_m15_bounds_context"
    if kind == "m1":
        if "CONFLICT" in _upper(row.get("m1_conflict_score_class")):
            return "branch_followup_m1_support_conflict_follow"
        return "branch_followup_m1_support_stable_follow"
    if kind == "positive":
        if decision == "FOLLOW":
            return "branch_followup_positive_replay_follow"
        return "branch_followup_positive_stress_context"
    if kind == "source":
        if decision == "FOLLOW":
            return "branch_followup_source_positive_cost_guard"
        if decision == "AVOID":
            return "branch_followup_source_negative_avoid"
        return "branch_followup_source_straddle_acquisition_context"
    if kind == "family":
        family = _norm(row.get("action_family")).casefold() or "unknown"
        suffix = "follow" if decision == "FOLLOW" else "avoid" if decision == "AVOID" else "context"
        return f"branch_followup_family_{family}_{suffix}"
    if decision == "FOLLOW":
        return "branch_followup_branch_positive_follow"
    if decision == "AVOID":
        return "branch_followup_branch_negative_avoid"
    return "branch_followup_branch_interval_context"


def _r_evidence_class(kind: str, decision: str, row: dict[str, Any]) -> str:
    if kind == "binding":
        return "BRANCH_FOLLOWUP_BINDING_NO_SCALAR"
    if kind == "source":
        if decision == "AVOID":
            return "BRANCH_FOLLOWUP_SOURCE_NEGATIVE_PROXY"
        return "BRANCH_FOLLOWUP_SOURCE_ACQUISITION_REQUIRED"
    if kind == "m15":
        if decision == "AVOID":
            return "BRANCH_FOLLOWUP_M15_STOP_FIRST_PROXY"
        if decision == "FOLLOW":
            return "BRANCH_FOLLOWUP_M15_TARGET_FIRST_PROXY"
        return "BRANCH_FOLLOWUP_M15_BOUNDS_CONTEXT"
    if kind == "m1":
        return "BRANCH_FOLLOWUP_M1_SUPPORT_PROXY"
    if kind == "positive":
        return "BRANCH_FOLLOWUP_POSITIVE_REPLAY_PROXY" if decision == "FOLLOW" else "BRANCH_FOLLOWUP_POSITIVE_STRESS_CONTEXT"
    if kind == "family":
        if decision == "AVOID":
            return "BRANCH_FOLLOWUP_FAMILY_AVOID_PROXY"
        if decision == "FOLLOW":
            return "BRANCH_FOLLOWUP_FAMILY_FOLLOW_PROXY"
        return "BRANCH_FOLLOWUP_FAMILY_CONTEXT"
    if kind == "bucket":
        return "BRANCH_FOLLOWUP_BUCKET_CONTEXT"
    if decision == "AVOID":
        return "BRANCH_FOLLOWUP_BRANCH_NEGATIVE_PROXY"
    if decision == "FOLLOW":
        return "BRANCH_FOLLOWUP_BRANCH_POSITIVE_PROXY"
    return "BRANCH_FOLLOWUP_BRANCH_INTERVAL_CONTEXT"


def _proxy_r_class(decision: str, row: dict[str, Any]) -> str:
    text = " ".join(
        _upper(row.get(key))
        for key in (
            "score_direction_class",
            "sealed_proxy_class",
            "source_risk_score_class",
            "m15_interval_sign_class",
            "positive_replay_score_class",
            "family_score_class",
        )
    )
    if decision == "AVOID":
        if "CONSERVATIVE_NEGATIVE" in text or "ALL_NEGATIVE" in text:
            return "STRONG_NEGATIVE_PROXY_R"
        return "NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        if "CONSERVATIVE_POSITIVE" in text or "ALL_POSITIVE" in text:
            return "STRONG_POSITIVE_PROXY_R"
        return "POSITIVE_PROXY_R"
    if "STRADDLES" in text or "BOUNDS" in text:
        return "BOUNDED_AMBIGUOUS_PROXY_R"
    return ""


def _implementation_action(kind: str, decision: str, row: dict[str, Any]) -> str:
    for key in (
        "next_computation_class",
        "source_router_followup_class",
        "family_followup_class",
        "m15_followup_class",
        "m1_followup_class",
        "positive_followup_class",
        "branch_primary_followup_class",
        "binding_preserve_status",
        "primary_export_class",
    ):
        if value := _norm(row.get(key)):
            return value
    if decision == "AVOID":
        return "BRANCH_FOLLOWUP_AVOID_FILTER"
    if decision == "FOLLOW":
        return "BRANCH_FOLLOWUP_FOLLOW_SCORER"
    return f"BRANCH_FOLLOWUP_{kind.upper()}_CONTEXT_GUARD"


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "binding_preserve_id",
        "followup_computation_branch_id",
        "bucket_id",
        "followup_family_action_id",
        "m15_followup_id",
        "m1_followup_id",
        "positive_followup_id",
        "source_followup_id",
        "branch_queue_id",
        "row_key",
        "source_row_id",
    ):
        if value := _norm(row.get(key)):
            return value
    stable_row = {str(key): value for key, value in row.items()}
    return _sha256_text(json.dumps(stable_row, sort_keys=True, default=str))[:24]


def _row_weight(row: dict[str, Any]) -> int:
    for key in ("row_count", "source_support_rows", "proxy_variant_count", "family_action_count", "export_action_count"):
        value = _to_float(row.get(key))
        if value is not None and 0 < value <= 100000:
            return max(1, int(round(value)))
    return 1


def _numeric_candidates(row: dict[str, Any]) -> list[tuple[str, float]]:
    values: list[tuple[str, float]] = []
    for field_name in (
        "mechanical_triage_score_proxy",
        "family_score_proxy",
        "m1_support_minus_branch_midpoint",
        "positive_midpoint_mean",
        "interval_midpoint_mean",
        "stress_midpoint_mean",
        "rstyle_midpoint_mean",
        "branch_midpoint_mean",
    ):
        numeric = _to_float(row.get(field_name))
        if numeric is not None:
            values.append(("proxy_score", numeric))
    for field_name in (
        "rstyle_midpoint_mean",
        "interval_midpoint_mean",
        "positive_midpoint_mean",
        "stress_midpoint_mean",
        "branch_midpoint_mean",
    ):
        numeric = _to_float(row.get(field_name))
        if numeric is not None:
            values.append(("cost_adjusted_simulated_r", numeric))
    for field_name in (
        "rstyle_lower_mean",
        "interval_lower_mean",
        "positive_lower_mean",
        "stress_lower_mean",
    ):
        numeric = _to_float(row.get(field_name))
        if numeric is not None:
            values.append(("stress_simulated_r", numeric))
    return values


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
        "source_shape": "branch_followup_computation_compact_scope",
    }


@dataclass
class Group:
    source_path: str
    source_hash: str
    source_group: str
    kind: str
    symbol: str
    source_symbol: str
    symbol_family: str
    market_timeframe: str
    route_session: str
    side: str
    horizon_id: str
    primitive: str
    route_family: str
    source_component: str
    action_family: str
    target_stop_order_class: str
    proxy_r_class: str
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
        for metric_name, value in _numeric_candidates(row):
            if metric_name == "proxy_score":
                self.proxy_score_sum += value
            elif metric_name == "cost_adjusted_simulated_r":
                self.cost_adjusted_sum += value
            elif metric_name == "stress_simulated_r":
                self.stress_sum += value
        if self.decision == "AVOID" and not self.proxy_score_sum:
            self.proxy_score_sum -= float(weight)
        if row_id := _row_id(row):
            if len(self.source_row_ids_sample) < 8:
                self.source_row_ids_sample.append(row_id)

    def to_row(self) -> dict[str, Any]:
        key_payload = "|".join(
            [
                self.source_group,
                self.kind,
                self.symbol,
                self.source_symbol,
                self.symbol_family,
                self.market_timeframe,
                self.route_session,
                self.side,
                self.horizon_id,
                self.primitive,
                self.route_family,
                self.source_component,
                self.action_family,
                self.target_stop_order_class,
                self.proxy_r_class,
                self.decision,
                self.action_class,
                self.source_role,
                self.r_evidence_class,
                self.implementation_action,
            ]
        )
        row_id = f"branch_followup_computation:{_sha256_text(key_payload)[:24]}"
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
                "primitive": self.primitive,
                "route_family": self.route_family,
                "source_component": self.source_component,
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.source_rows_represented or self.rows),
                max(float(self.rows), 1.0),
                "branch_followup_source_rows",
            )
        }
        if self.proxy_score_sum:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_score_sum,
                max(float(self.rows), 1.0),
                "branch_followup_proxy_fields",
            )
        if self.cost_adjusted_sum:
            metrics["cost_adjusted_simulated_r"] = _metric_trace(
                self.cost_adjusted_sum,
                max(float(self.rows), 1.0),
                "branch_followup_midpoint_fields",
            )
        if self.stress_sum:
            metrics["stress_simulated_r"] = _metric_trace(
                self.stress_sum,
                max(float(self.rows), 1.0),
                "branch_followup_lower_bound_fields",
            )
        return {
            "schema_version": "gtos_vnext_branch_followup_computation_runtime_row_v1",
            "row_key": row_id,
            "branch_followup_computation_runtime_row_id": row_id,
            "source_name": "gtos_vnext_branch_followup_computation_wave",
            "evidence_family": "gtos_vnext_branch_followup_computation",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": "branch_followup_computation_runtime",
            "runtime_effect_now": "branch_followup_computation_runtime_pressure",
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "action_family": self.action_family,
            "r_evidence_class": self.r_evidence_class,
            "review_action": self.decision,
            "decision": self.decision,
            "source_component": self.source_component,
            "route_family": self.route_family,
            "symbol": self.symbol,
            "source_symbol": self.source_symbol,
            "symbol_family": self.symbol_family,
            "market_timeframe": self.market_timeframe,
            "timeframe": self.market_timeframe,
            "route_session": self.route_session,
            "side": self.side,
            "horizon_id": self.horizon_id,
            "primitive": self.primitive,
            "entry_variant": "",
            "target_stop_order_class": self.target_stop_order_class,
            "proxy_r_class": self.proxy_r_class,
            "source_acquisition_required": self.source_role == "branch_followup_source_acquisition_guard",
            "source_path": self.source_path,
            "drill_through_path": self.source_path,
            "source_artifact_hash_sha256": self.source_hash,
            "source_rows_represented": self.source_rows_represented,
            "source_row_ids_sample": self.source_row_ids_sample,
            "source_bound": bool((self.symbol or self.source_symbol or self.symbol_family) and self.route_session),
            "source_complete": self.decision in {"FOLLOW", "AVOID"}
            and self.source_role != "branch_followup_source_acquisition_guard",
            "runtime_candidate_use_permitted": self.decision == "FOLLOW"
            and self.source_role != "branch_followup_source_acquisition_guard",
            "candidate_use_allowed_now": self.decision == "FOLLOW"
            and self.source_role != "branch_followup_source_acquisition_guard",
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
        kind = _row_kind(path)
        source_group = _source_file_group(path)
        for row in runtime_rows:
            decision = _decision(kind, row)
            action_class = _action_class(kind, decision, row)
            source_role = _source_role(kind, decision, row)
            r_evidence_class = _r_evidence_class(kind, decision, row)
            target_stop_class = _target_stop_order_class(row)
            proxy_r_class = _proxy_r_class(decision, row)
            symbol = _symbol(row)
            source_symbol = _norm(row.get("source_symbol")) or symbol
            key = (
                path_text,
                source_hash,
                source_group,
                kind,
                symbol,
                source_symbol,
                resolve_vnext_symbol_family(symbol or source_symbol) if (symbol or source_symbol) else "",
                _market_timeframe(kind),
                _route_session(row),
                _side(row),
                _horizon_id(row),
                _primitive(row),
                _route_family(kind),
                _source_component(kind),
                _norm(row.get("action_family")),
                target_stop_class,
                proxy_r_class,
                decision,
                action_class,
                source_role,
                r_evidence_class,
                _implementation_action(kind, decision, row),
            )
            if not (symbol or source_symbol or key[13]):
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
        "schema_version": "gtos_vnext_branch_followup_computation_runtime_summary_v1",
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
        "action_family_counts": dict(
            sorted(Counter(row["action_family"] for row in rows if row.get("action_family")).items())
        ),
        "target_stop_order_class_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows if row.get("target_stop_order_class")).items())
        ),
        "proxy_r_class_counts": dict(
            sorted(Counter(row["proxy_r_class"] for row in rows if row.get("proxy_r_class")).items())
        ),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "market_timeframe_counts": dict(
            sorted(Counter(row["market_timeframe"] for row in rows if row.get("market_timeframe")).items())
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
