#!/usr/bin/env python3
"""Build compact runtime rows for Sierra/depth source-acquisition evidence."""

from __future__ import annotations

import argparse
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
WAVE_ID = "WAVE_SIERRA_DEPTH_SOURCE_ACQUISITION_REPAIR"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_sierra_depth_source_acquisition_runtime_rows",
    "gtos_vnext_sierra_depth_source_acquisition_runtime_summary",
)

REQUIRED_TOKENS = (
    "ACQUISITION",
    "BLOCKED",
    "BROADER_SOURCE",
    "CAPTURE_REQUIRED",
    "DEFERRED",
    "FILE_SIZE_GUARD",
    "GAP",
    "INSUFFICIENT",
    "MISSING",
    "NO_EVENT",
    "NO_PRIOR",
    "NO_REGISTERED",
    "PENDING",
    "REPLAY_REQUIRED",
    "REQUIRES_WINDOW_REPLAY",
    "SOURCE_DATE",
    "SOURCE_GAP",
    "UNRECOVERED",
    "UNRESOLVED",
)
VALIDATED_TOKENS = (
    "FEATURES_EXTRACTED",
    "LOCAL_SIERRA_DEPTH_CAPTURED",
    "REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60",
    "SCID_M15_BARS_BUILT",
    "VALIDATED_FUTURES_PROXY_TRANSFER",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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


def _wave_units() -> list[dict[str, Any]]:
    rows = master_ledger.build_rows()
    units = [
        row
        for row in rows
        if row.get("conversion_state") in master_ledger.OPEN_BATCH_STATES
        and master_ledger._batch_wave_id_for_row(row) == WAVE_ID
    ]
    return sorted(units, key=lambda row: str(row.get("source_artifact_path") or "").casefold())


def _source_paths_from_existing_summary() -> list[tuple[Path, str]]:
    try:
        payload = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    artifacts = payload.get("source_artifacts") if isinstance(payload, dict) else None
    if not isinstance(artifacts, list):
        return []
    if int(payload.get("runtime_row_count") or 0) <= 0:
        return []
    # The compact wave is intentionally bounded to the open Sierra/depth source
    # acquisition units. If a prior experimental run expanded beyond that set,
    # ignore it and rebuild from the still-open master-ledger wave.
    if len(artifacts) > 600:
        return []
    paths: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        raw_path = _norm(item.get("path"))
        if not raw_path:
            continue
        path = _resolve_source_path(raw_path)
        if not path.exists():
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        paths.append((path, _norm(item.get("sha256_or_git_blob"))))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _source_paths() -> list[tuple[Path, str]]:
    existing = _source_paths_from_existing_summary()
    if existing:
        return existing
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
        "SIERRA_DEPTH_",
        "SIERRA_",
        "GTOS_VNEXT_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-16.jsonl",
        "_2026-05-16_CANDIDATE_LEDGER.jsonl",
        "_2026-05-16_CLASSIFICATION_LEDGER.jsonl",
        "_2026-05-16_PERMISSION_LEDGER.jsonl",
        "_2026-05-16_QUESTION_LEDGER.jsonl",
        "_2026-05-16_REQUIREMENT_ROW_LEDGER.jsonl",
        "_2026-05-16_ROOT_SCAN_LEDGER.jsonl",
        "_2026-05-16_SOURCE_ARTIFACT_LEDGER.jsonl",
        "_2026-05-16_UNIQUE_SOURCE_DATE_LEDGER.jsonl",
        "_2026-05-03.md",
        ".jsonl",
        ".json",
        ".md",
        ".txt",
        ".py",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


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
            rows: list[dict[str, Any]] = [payload]
            for value in payload.values():
                if isinstance(value, list):
                    rows.extend(row for row in value if isinstance(row, dict))
            return rows
    return []


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


def _candidate_time(row: dict[str, Any]) -> str:
    for key in (
        "canonical_m15_close_utc",
        "bar_start_utc",
        "bar_end_exclusive_utc",
        "future_bar_start_utc",
        "first_source_timestamp_utc",
        "last_source_timestamp_utc",
        "decision_time_utc",
        "source_path_start_utc",
    ):
        if value := _norm(row.get(key)):
            return value
    return ""


def _route_session(row: dict[str, Any], path: Path) -> str:
    for key in ("route_session", "session", "kill_zone", "session_bucket", "session_name"):
        if value := _norm(row.get(key)):
            value_lower = value.casefold()
            if value_lower in {"london", "london_core", "ldn"}:
                return "london_core"
            if value_lower in {"ny", "new_york", "ny_core", "new_york_core"}:
                return "ny_core"
            if value_lower in {"tokyo", "tokyo_kz", "asia"}:
                return "tokyo_kz"
            if value_lower in {"off_core", "off_core_session", "off_kz"}:
                return "off_core_session"
            if value_lower.startswith("london_core"):
                return "london_core"
            if value_lower.startswith("ny_core") or value_lower.startswith("new_york_core"):
                return "ny_core"
            if value_lower.startswith("tokyo_core") or value_lower.startswith("tokyo_kz"):
                return "tokyo_kz"
            return value
    name = path.name.casefold()
    if "tokyo" in name:
        return "tokyo_kz"
    if "london" in name:
        return "london_core"
    if "_ny_" in name or "ny_core" in name:
        return "ny_core"
    return _session_from_time(_candidate_time(row))


def _symbol(row: dict[str, Any]) -> str:
    for key in ("symbol", "route_c_symbol", "target_symbol", "market", "instrument"):
        if value := _norm(row.get(key)):
            return value
    route_id = _norm(row.get("route_id"))
    if "|" in route_id:
        first = route_id.split("|", 1)[0].strip()
        if first:
            return first
    return ""


def _source_symbol(row: dict[str, Any], symbol: str) -> str:
    for key in ("source_symbol", "sierra_symbol", "depth_symbol", "futures_symbol"):
        if value := _norm(row.get(key)):
            return value
    return symbol


def _market_timeframe(row: dict[str, Any], path: Path) -> str:
    for key in ("market_timeframe", "timeframe", "source_timeframe", "tf"):
        if value := _norm(row.get(key)):
            return value.upper()
    name = path.name.casefold()
    if "m1" in name:
        return "M1"
    if "m15" in name or "bar" in name or "event_window" in name:
        return "M15"
    if "h1" in name:
        return "H1"
    return "M15"


def _horizon_id(row: dict[str, Any]) -> str:
    for key in ("horizon_id", "horizon", "route_c_horizon_id"):
        if value := _norm(row.get(key)):
            return value
    return ""


def _side(row: dict[str, Any]) -> str:
    for key in ("side", "selected_side", "direction", "trade_side", "route_c_side"):
        value = _norm(row.get(key)).upper()
        if value in {"LONG", "SHORT"}:
            return value
    return ""


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "source_requirement_row_id",
        "gap_id",
        "request_id",
        "replay_id",
        "question_id",
        "route_c_queue_id",
        "route_id",
        "source_audit_key",
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


def _status_text(row: dict[str, Any], path: Path) -> str:
    fields = (
        "status",
        "primary_repair_status",
        "blocker_type",
        "requirement_status",
        "feature_status",
        "source_status",
        "queue_status",
        "decision",
        "question",
        "next_action",
        "implementation_action",
        "safe_flags",
        "not_completion",
        "source_proxy_family",
        "proxy_relation",
    )
    values = [path.name]
    for field_name in fields:
        value = row.get(field_name)
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, sort_keys=True, default=str))
        elif value not in (None, ""):
            values.append(str(value))
    return " ".join(values).upper()


def _source_transfer_validated(row: dict[str, Any], path: Path) -> bool:
    if any(
        _truthy(row.get(key))
        for key in (
            "orderflow_runtime_validated",
            "proxy_transfer_validated",
            "futures_to_cfd_transfer_validated",
            "source_transfer_validated",
        )
    ):
        return True
    text = _status_text(row, path)
    return any(token in text for token in VALIDATED_TOKENS)


def _source_acquisition_required(row: dict[str, Any], path: Path) -> bool:
    text = _status_text(row, path)
    if "FEATURES_EXTRACTED" in text and not any(token in text for token in ("BLOCKED", "MISSING", "GAP")):
        return False
    if "REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60" in text:
        return False
    return any(token in text for token in REQUIRED_TOKENS)


def _source_component(path: Path, row: dict[str, Any], required: bool) -> str:
    text = _status_text(row, path)
    if not required:
        if "REPAIRED_IN_WINDOW_CLEAR" in text:
            return "sierra_depth_in_window_clear_repair"
        return "sierra_depth_live_feature_status"
    if "NO_REGISTERED" in text or "PROXY" in text and "MISSING" in text:
        return "sierra_depth_source_gap"
    if any(token in text for token in ("NO_EVENT", "NO_PRIOR", "INSUFFICIENT", "EMPTY", "BLOCKED")):
        return "sierra_depth_window_sample_block"
    if any(token in text for token in ("MISSING", "UNRECOVERED", "GAP", "SOURCE_DATE")):
        return "sierra_depth_source_gap"
    if any(token in text for token in ("PENDING", "FILE_SIZE_GUARD", "DEFERRED")):
        return "sierra_depth_live_feature_status"
    return "sierra_depth_source_acquisition"


def _source_acquisition_kind(path: Path, row: dict[str, Any], component: str, required: bool) -> str:
    text = _status_text(row, path)
    if not required:
        if component == "sierra_depth_in_window_clear_repair":
            return "in_window_clear_repaired"
        return "depth_transfer_status_context"
    if component == "sierra_depth_window_sample_block":
        return "depth_window_sample_blocked_or_insufficient"
    if component == "sierra_depth_source_gap":
        return "missing_exact_depth_source_or_proxy"
    if "PENDING" in text or "FILE_SIZE_GUARD" in text:
        return "live_depth_feature_extraction_pending"
    return "source_acquisition_required"


def _implementation_action(component: str, required: bool) -> str:
    if not required:
        return "SIERRA_DEPTH_TRANSFER_STATUS_CONTEXT"
    if component == "sierra_depth_window_sample_block":
        return "SIERRA_DEPTH_WINDOW_SAMPLE_REPAIR_REQUIRED"
    if component == "sierra_depth_source_gap":
        return "SIERRA_DEPTH_SOURCE_ACQUISITION_REQUIRED"
    return "SIERRA_DEPTH_SOURCE_ACQUISITION_REQUIRED"


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
        "source_shape": "sierra_depth_source_acquisition_compact_scope",
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
    source_component: str
    source_acquisition_kind: str
    source_acquisition_required: bool
    source_transfer_validated: bool
    implementation_action: str
    rows: int = 0
    row_ids_sample: list[str] = field(default_factory=list)
    status_counts: Counter = field(default_factory=Counter)
    blocker_type_counts: Counter = field(default_factory=Counter)
    requirement_status_counts: Counter = field(default_factory=Counter)
    feature_status_counts: Counter = field(default_factory=Counter)
    primary_repair_status_counts: Counter = field(default_factory=Counter)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        if row_id := _row_id(row):
            if len(self.row_ids_sample) < 5:
                self.row_ids_sample.append(row_id)
        for field_name, target in (
            ("status", self.status_counts),
            ("blocker_type", self.blocker_type_counts),
            ("requirement_status", self.requirement_status_counts),
            ("feature_status", self.feature_status_counts),
            ("primary_repair_status", self.primary_repair_status_counts),
        ):
            if value := _norm(row.get(field_name)):
                target[value] += 1

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
                self.source_acquisition_kind,
                str(self.source_acquisition_required),
                str(self.source_transfer_validated),
                self.implementation_action,
            ]
        )
        row_id = f"sierra_depth_source_acquisition:{_sha256_text(key_payload)[:24]}"
        scope = {
            key: value
            for key, value in {
                "symbol": self.symbol,
                "symbol_family": self.symbol_family,
                "market": self.symbol or self.source_symbol,
                "market_timeframe": self.market_timeframe,
                "timeframe": self.market_timeframe,
                "route_session": self.route_session,
                "side": self.side,
                "horizon_id": self.horizon_id,
                "source_component": self.source_component,
                "route_family": "numeric_router",
                "action_class": "sierra_depth_source_acquisition_guard",
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.rows),
                max(float(self.rows), 1.0),
                "sierra_depth_source_acquisition_rows",
            )
        }
        return {
            "schema_version": "gtos_vnext_sierra_depth_source_acquisition_runtime_row_v1",
            "row_key": row_id,
            "sierra_depth_source_acquisition_runtime_row_id": row_id,
            "source_name": "gtos_vnext_sierra_depth_source_acquisition_wave",
            "evidence_family": "gtos_vnext_sierra_depth_source_acquisition",
            "source_group": "sierra_depth_source_acquisition",
            "source_role": (
                "depth_source_acquisition_gate"
                if self.source_acquisition_required
                else "depth_source_transfer_context"
            ),
            "system_surface": "sierra_depth_source_acquisition_runtime_gate",
            "runtime_effect_now": (
                "depth_transfer_source_acquisition_risk_guard"
                if self.source_acquisition_required
                else "depth_transfer_status_context"
            ),
            "implementation_action": self.implementation_action,
            "action_class": "sierra_depth_source_acquisition_guard",
            "r_evidence_class": (
                "SOURCE_ACQUISITION_FOR_DEPTH_TRANSFER"
                if self.source_acquisition_required
                else "SOURCE_DEPTH_TRANSFER_CONTEXT"
            ),
            "decision": "MIXED",
            "source_component": self.source_component,
            "source_acquisition_kind": self.source_acquisition_kind,
            "source_acquisition_required": self.source_acquisition_required,
            "source_transfer_validated": self.source_transfer_validated,
            "orderflow_runtime_validated": self.source_transfer_validated,
            "proxy_transfer_validated": self.source_transfer_validated,
            "futures_to_cfd_transfer_validated": self.source_transfer_validated,
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
            "source_rows_represented": self.rows,
            "source_row_ids_sample": self.row_ids_sample,
            "status_counts": dict(sorted(self.status_counts.items())),
            "blocker_type_counts": dict(sorted(self.blocker_type_counts.items())),
            "requirement_status_counts": dict(sorted(self.requirement_status_counts.items())),
            "feature_status_counts": dict(sorted(self.feature_status_counts.items())),
            "primary_repair_status_counts": dict(sorted(self.primary_repair_status_counts.items())),
            "source_bound": bool(self.symbol or self.source_symbol or self.symbol_family),
            "source_complete": not self.source_acquisition_required,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "r_metrics": metrics,
            "event_scope": scope,
        }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[Any, ...], Group] = {}
    source_stats: list[dict[str, Any]] = []
    for path, ledger_hash in _source_paths():
        path_text = _path_text(path)
        source_hash = ledger_hash or _sha256_file(path)
        runtime_rows = _read_runtime_source_rows(path) if path.suffix.lower() in RUNTIME_SUFFIXES else []
        line_count = len(runtime_rows) if runtime_rows else _line_count(path)
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
            source_symbol = _source_symbol(row, symbol)
            route_session = _route_session(row, path)
            required = _source_acquisition_required(row, path)
            validated = _source_transfer_validated(row, path) and not required
            source_component = _source_component(path, row, required)
            action = _implementation_action(source_component, required)
            source_acquisition_kind = _source_acquisition_kind(
                path,
                row,
                source_component,
                required,
            )
            if not (symbol or source_symbol or route_session or source_component):
                continue
            key = (
                path_text,
                source_hash,
                source_group,
                symbol,
                source_symbol,
                resolve_vnext_symbol_family(symbol or source_symbol)
                if (symbol or source_symbol)
                else "",
                _market_timeframe(row, path),
                route_session,
                _side(row),
                _horizon_id(row),
                source_component,
                source_acquisition_kind,
                required,
                validated,
                action,
            )
            group = groups.get(key)
            if group is None:
                group = Group(*key)
                groups[key] = group
            group.add(row)

    rows = [group.to_row() for group in groups.values()]
    rows.sort(key=lambda row: row["row_key"])
    source_rows_represented = sum(int(row["source_rows_represented"]) for row in rows)
    counted_source_rows = sum(
        int(stat["rows"]) for stat in source_stats if isinstance(stat.get("rows"), int)
    )
    source_component_counts = Counter(row["source_component"] for row in rows)
    source_acquisition_kind_counts = Counter(row["source_acquisition_kind"] for row in rows)
    summary = {
        "schema_version": "gtos_vnext_sierra_depth_source_acquisition_runtime_summary_v1",
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "wave_source_rows_counted": counted_source_rows,
        "wave_source_artifact_count": len(source_stats),
        "wave_source_artifact_suffix_counts": dict(
            sorted(Counter(stat["suffix"] for stat in source_stats).items())
        ),
        "row_count_unknown_source_artifact_count": sum(
            1 for stat in source_stats if stat.get("rows") is None
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_acquisition_kind_counts": dict(sorted(source_acquisition_kind_counts.items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "source_symbol_counts": dict(
            sorted(Counter(row["source_symbol"] for row in rows if row.get("source_symbol")).items())
        ),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "source_acquisition_required_rows": sum(
            1 for row in rows if row.get("source_acquisition_required")
        ),
        "source_acquisition_required_source_rows": sum(
            int(row.get("source_rows_represented") or 0)
            for row in rows
            if row.get("source_acquisition_required")
        ),
        "source_transfer_validated_rows": sum(
            1 for row in rows if row.get("source_transfer_validated")
        ),
        "status_counts": dict(
            sorted(
                Counter(
                    key
                    for row in rows
                    for key, count in (row.get("status_counts") or {}).items()
                    for _ in range(int(count))
                ).items()
            )
        ),
        "blocker_type_counts": dict(
            sorted(
                Counter(
                    key
                    for row in rows
                    for key, count in (row.get("blocker_type_counts") or {}).items()
                    for _ in range(int(count))
                ).items()
            )
        ),
        "requirement_status_counts": dict(
            sorted(
                Counter(
                    key
                    for row in rows
                    for key, count in (row.get("requirement_status_counts") or {}).items()
                    for _ in range(int(count))
                ).items()
            )
        ),
        "feature_status_counts": dict(
            sorted(
                Counter(
                    key
                    for row in rows
                    for key, count in (row.get("feature_status_counts") or {}).items()
                    for _ in range(int(count))
                ).items()
            )
        ),
        "primary_repair_status_counts": dict(
            sorted(
                Counter(
                    key
                    for row in rows
                    for key, count in (row.get("primary_repair_status_counts") or {}).items()
                    for _ in range(int(count))
                ).items()
            )
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
    printable["status_counts"] = f"{len(summary['status_counts'])} statuses"
    print(json.dumps(printable, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
