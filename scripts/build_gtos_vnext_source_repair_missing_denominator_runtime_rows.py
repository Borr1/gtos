#!/usr/bin/env python3
"""Build compact runtime rows for source-repair and missing-denominator evidence."""

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
WAVE_ID = "WAVE_SOURCE_REPAIR_MISSING_DENOMINATOR_BEHAVIOR"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_source_repair_missing_denominator_runtime_rows",
    "gtos_vnext_source_repair_missing_denominator_runtime_summary",
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
        "MAIN_ORCH24_",
        "READY8_",
        "HAZ005_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-18.jsonl",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_2026-05-19.md",
        "_2026-05-18.jsonl",
        "_2026-05-17.jsonl",
        "_2026-05-16.jsonl",
        "_2026-05-15.jsonl",
        ".jsonl",
        ".json",
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


def _candidate_time(row: dict[str, Any]) -> str:
    candidate_id = _norm(row.get("candidate_id") or row.get("event_id"))
    if "_" in candidate_id:
        return candidate_id.split("_", 1)[1]
    for key in (
        "decision_time_utc",
        "decision_asof_utc",
        "source_path_start_utc",
        "probe_window_start_utc",
        "bar_time_utc",
    ):
        if value := _norm(row.get(key)):
            return value
    return ""


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _variant, _horizon = _route_parts(row)
    for key in ("symbol", "source_symbol", "market", "instrument"):
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
    return _session_from_time(_candidate_time(row))


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol, _session, _variant, horizon = _route_parts(row)
    return _norm(row.get("horizon_id") or row.get("horizon") or horizon)


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
        "source_repair_proof_row_id",
        "source_repair_plan_row_id",
        "source_repair_selector_surface_row_id",
        "denominator_source_execution_row_id",
        "denominator_guard_result_row_id",
        "denominator_default_off_application_row_id",
        "denominator_default_off_scorer_row_id",
        "denominator_control_construction_row_id",
        "fail_closed_repair_row_id",
        "bar_packet_row_id",
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
    explicit = _norm(row.get("source_component"))
    if explicit:
        return explicit
    name = path.name.casefold()
    text = " ".join(
        _norm(row.get(key)).casefold()
        for key in (
            "required_source_class",
            "source_component",
            "repair_action",
            "implementation_action",
            "offline_repair_action",
            "numeric_router_action",
            "source_repair_system_decision",
        )
        if _norm(row.get(key))
    )
    if "ready8" in name or "scid" in name or "bar_packet" in name:
        return "sierra_scid_source_bound_m15_bar_replay"
    if "registry" in name:
        return "registry_scorer_module"
    if "scorer" in name:
        return "default_off_scorer_application"
    if "default_off_application" in name or "application" in name:
        return "default_off_application"
    if "selector_surface" in name:
        return "source_repair_proof"
    if "denominator" in name or "missing" in name or "source_join" in text:
        return "source_repair_proof"
    return "source_repair_proof"


def _implementation_action(path: Path, row: dict[str, Any], source_component: str) -> str:
    for key in (
        "repair_action",
        "implementation_action",
        "offline_repair_action",
        "numeric_router_action",
        "denominator_source_execution_decision",
        "source_repair_system_decision",
        "source_repair_selector_surface_status",
        "action_result_decision",
    ):
        if value := _norm(row.get(key)):
            return value
    name = path.name.casefold()
    if source_component == "sierra_scid_source_bound_m15_bar_replay":
        return "SOURCE_CAPTURE_REPAIR_REQUIRED"
    if "denominator" in name:
        return "EXACT_DENOMINATOR_SOURCE_REBUILD_REQUIRED"
    return "SOURCE_JOIN_REPAIR_REQUIRED"


def _source_repair_kind(path: Path, row: dict[str, Any], action: str) -> str:
    name = path.name.casefold()
    text = " ".join(
        _norm(row.get(key)).casefold()
        for key in (
            "required_source_class",
            "exact_missing_field_proof",
            "repair_action",
            "missing_field_source",
            "denominator_source_execution_decision",
            "source_repair_system_decision",
            "source_repair_selector_surface_status",
        )
        if _norm(row.get(key))
    )
    if "broker" in name or "broker" in text or "slippage" in text:
        return "broker_execution_geometry_missing"
    if "denominator" in name or "denominator" in text:
        return "exact_denominator_missing_or_rebuild_required"
    if "prior16" in name or "bar_packet" in name or "scid" in name:
        return "source_bar_packet_missing_or_repaired"
    if "selector_surface" in name or "selector" in text:
        return "selector_surface_execution_identity_missing"
    if "source_join" in action.casefold() or "source_join" in text:
        return "source_join_missing"
    return "source_repair_required"


def _missing_field_count(row: dict[str, Any]) -> int:
    value = _to_float(row.get("missing_field_count") or row.get("missing_required_field_count"))
    if value is not None:
        return int(value)
    proof = row.get("exact_missing_field_proof")
    if isinstance(proof, dict):
        fields = proof.get("missing_fields")
        if isinstance(fields, list):
            return len(fields)
    if isinstance(proof, list):
        return len(proof)
    return 0


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
        "source_shape": "source_repair_missing_denominator_compact_scope",
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
    source_repair_kind: str
    implementation_action: str
    rows: int = 0
    missing_field_count: int = 0
    exact_rebuild_required_rows: int = 0
    row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.missing_field_count += _missing_field_count(row)
        self.exact_rebuild_required_rows += int(
            _truthy(row.get("exact_rebuild_required"))
            or _truthy(row.get("requires_source_join_before_exact_r"))
            or _truthy(row.get("requires_prospective_execution_identity_capture"))
        )
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
                self.source_repair_kind,
                self.implementation_action,
            ]
        )
        row_id = f"source_repair_missing_denominator:{_sha256_text(key_payload)[:24]}"
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
                "action_class": "source_repair_missing_denominator_guard",
                "source_repair_kind": self.source_repair_kind,
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.rows),
                max(float(self.rows), 1.0),
                "source_repair_missing_denominator_rows",
            )
        }
        return {
            "schema_version": "gtos_vnext_source_repair_missing_denominator_runtime_row_v1",
            "row_key": row_id,
            "source_repair_missing_denominator_runtime_row_id": row_id,
            "source_name": "gtos_vnext_source_repair_missing_denominator_wave",
            "evidence_family": "gtos_vnext_source_repair_missing_denominator",
            "source_group": "source_repair_proof",
            "source_role": "source_repair_execution_plan",
            "system_surface": "source_repair_queue_catalog",
            "runtime_effect_now": "exact_r_source_repair_risk_guard",
            "implementation_action": self.implementation_action,
            "action_class": "source_repair_missing_denominator_guard",
            "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R",
            "decision": "MIXED",
            "source_component": self.source_component,
            "source_repair_kind": self.source_repair_kind,
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
            "missing_field_count": self.missing_field_count,
            "exact_rebuild_required_rows": self.exact_rebuild_required_rows,
            "source_bound": bool(self.symbol or self.source_symbol or self.symbol_family),
            "source_complete": False,
            "runtime_candidate_use_permitted": False,
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
            action = _implementation_action(path, row, source_component)
            repair_kind = _source_repair_kind(path, row, action)
            side = _side(row)
            route_session = _route_session(row, path)
            key = (
                path_text,
                source_hash,
                source_group,
                symbol,
                source_symbol,
                resolve_vnext_symbol_family(symbol or source_symbol) if (symbol or source_symbol) else "",
                _market_timeframe(row, path),
                route_session,
                side,
                _horizon_id(row),
                source_component,
                repair_kind,
                action,
            )
            if not (symbol or source_symbol or route_session or source_component or repair_kind):
                continue
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
    summary = {
        "schema_version": "gtos_vnext_source_repair_missing_denominator_runtime_summary_v1",
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
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in rows).items())
        ),
        "source_repair_kind_counts": dict(
            sorted(Counter(row["source_repair_kind"] for row in rows).items())
        ),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "missing_field_count": sum(int(row.get("missing_field_count") or 0) for row in rows),
        "exact_rebuild_required_rows": sum(
            int(row.get("exact_rebuild_required_rows") or 0) for row in rows
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
