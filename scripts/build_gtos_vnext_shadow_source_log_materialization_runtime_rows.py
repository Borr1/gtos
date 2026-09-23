#!/usr/bin/env python3
"""Build vNext runtime rows from row-bearing shadow source logs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME"
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MASTER_LEDGER_PATH = ROUTE_DIR / (
    f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
)
OUTPUT_ROWS = ROUTE_DIR / (
    f"GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / (
    f"GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_RUNTIME_SURFACE = "source_capture_and_forward_runtime_friction"
OPEN_STATES = {"NOT_STARTED", "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION"}

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "primitive",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)

SESSION_ALIASES = {
    "london": "london_core",
    "london_core": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "ny_core": "ny_core",
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "asia": "tokyo_kz",
    "off_core": "off_core_session",
    "off_core_session": "off_core_session",
}

GAP_TOKEN_BY_COMPONENT = {
    "shadow_candidate_poi_source_gap": (
        "CANDIDATE_H1_SETUP_MISSING",
        "CANDIDATE_POI_MISSING",
    ),
    "shadow_framework_qualification_source_gap": (
        "CANDIDATE_FRAMEWORKS_EVALUATED_MISSING",
        "FRAMEWORK_QUALIFICATION_MISSING",
    ),
    "shadow_missing_exact_required_fields": (
        "MISSING_EXACT_REQUIRED_FIELDS",
        "MISSING_REQUIRED_FIELDS",
    ),
    "shadow_action_required_source_gap": (
        "ACTION_REQUIRED",
        "ACTION_REQUIRED_CODES",
    ),
    "shadow_join_status_source_gap": (
        "NOT_JOINED",
        "JOIN_ABSENT",
        "JOIN_MISSING",
        "JOIN_FAILED",
    ),
    "shadow_path_contract_source_gap": (
        "SOURCE_OHLC_FIRST_BAR_NOT_CAPTURED",
        "PATH_CONTRACT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
        "M15_OHLC_PATH_LABEL_ONLY",
    ),
    "shadow_external_source_blocker": (
        "EXTERNAL_SOURCE_BLOCKED",
        "BLOCKER",
    ),
}
GENERIC_GAP_COMPONENT = "shadow_generic_source_materialization_gap"
SOURCE_COMPONENTS = tuple(GAP_TOKEN_BY_COMPONENT) + (GENERIC_GAP_COMPONENT,)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _repo_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _read_master_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    if not MASTER_LEDGER_PATH.exists():
        return units
    with MASTER_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            path_text = _norm(row.get("source_artifact_path")).replace("\\", "/")
            if not path_text.startswith("shadow_logs/"):
                continue
            if row.get("affected_runtime_surface") != SOURCE_RUNTIME_SURFACE:
                continue
            evidence_family = _norm(row.get("evidence_family"))
            if (
                row.get("conversion_state") not in OPEN_STATES
                and row.get("batch_wave_id") != WAVE_ID
                and evidence_family
                not in {
                    "gtos_vnext_shadow_source_log_materialization",
                    "gtos_vnext_shadow_source_log_materialization_context",
                }
            ):
                continue
            units.append(row)
    return units


def _iter_file_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return []
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes[-2:] == [".jsonl", ".gz"] or path.suffix.lower() == ".jsonl":
        opener = gzip.open if path.suffix.lower() == ".gz" else open
        records: list[dict[str, Any]] = []
        with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    records.append(payload)
        return records
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        return [payload] if isinstance(payload, dict) and payload else []
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    return []


def _session_from_record(row: dict[str, Any]) -> str:
    raw = _norm(row.get("session") or row.get("session_tag") or row.get("kill_zone"))
    return SESSION_ALIASES.get(raw.casefold().replace("-", "_"), raw)


def _side_from_record(row: dict[str, Any]) -> str:
    raw = _norm(row.get("side") or row.get("direction")).upper()
    if raw in {"LONG", "BUY", "BULLISH"}:
        return "LONG"
    if raw in {"SHORT", "SELL", "BEARISH"}:
        return "SHORT"
    trade_parameters = row.get("trade_parameters")
    if isinstance(trade_parameters, dict):
        return _side_from_record(trade_parameters)
    snapshot = row.get("mso_snapshot")
    if isinstance(snapshot, dict):
        return _side_from_record(snapshot)
    return ""


def _symbol_from_record(row: dict[str, Any]) -> str:
    symbol = _norm(row.get("symbol") or row.get("broker_symbol") or row.get("candidate_symbol"))
    if symbol.upper() == "NDX100":
        return "NAS100"
    snapshot = row.get("mso_snapshot")
    if not symbol and isinstance(snapshot, dict):
        symbol = _norm(snapshot.get("symbol") or snapshot.get("broker_symbol"))
    return symbol


def _timeframe_from_record(row: dict[str, Any]) -> str:
    value = _norm(row.get("timeframe") or row.get("market_timeframe"))
    if value:
        return value.upper()
    source_range = row.get("source_ohlc_range")
    if isinstance(source_range, dict) and _norm(source_range.get("source_timeframe")):
        return _norm(source_range.get("source_timeframe")).upper()
    return "M15"


def _row_id(row: dict[str, Any], fallback: str) -> str:
    return (
        _norm(row.get("row_key"))
        or _norm(row.get("candidate_id"))
        or _norm(row.get("evaluation_id"))
        or _norm(row.get("created_at_utc"))
        or fallback
    )


def _walk_status_values(value: Any, parent_key: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            joined = f"{parent_key}.{key}" if parent_key else str(key)
            found.extend(_walk_status_values(item, joined))
        return found
    if isinstance(value, list):
        if value and any(
            token in parent_key.lower()
            for token in ("missing", "required", "action_required", "status", "codes")
        ):
            found.append((parent_key, ",".join(_norm(item) for item in value if _norm(item))))
        for index, item in enumerate(value[:20]):
            found.extend(_walk_status_values(item, f"{parent_key}[{index}]"))
        return found
    key_lower = parent_key.lower()
    if any(
        token in key_lower
        for token in (
            "capture_status",
            "join_status",
            "source_status",
            "blocker_status",
            "missing",
            "action_required",
            "path_ambiguity_status",
            "path_contract_status",
            "documented_limitation",
        )
    ):
        text = _norm(value)
        if text:
            found.append((parent_key, text))
    return found


def _component_from_gap_codes(gap_codes: Counter[str]) -> str:
    haystack = " ".join(gap_codes.keys()).upper()
    for component, tokens in GAP_TOKEN_BY_COMPONENT.items():
        if any(token in haystack for token in tokens):
            return component
    return GENERIC_GAP_COMPONENT


def _gap_codes(row: dict[str, Any]) -> Counter[str]:
    codes: Counter[str] = Counter()
    for field, value in _walk_status_values(row):
        if not value:
            continue
        upper = value.upper()
        if any(
            token in upper
            for token in (
                "MISSING",
                "NOT_JOINED",
                "JOIN_ABSENT",
                "JOIN_FAILED",
                "SOURCE_CAPTURE",
                "SOURCE_GAP",
                "SOURCE_OHLC_FIRST_BAR_NOT_CAPTURED",
                "ACTION_REQUIRED",
                "REPAIR_REQUIRED",
                "BLOCKER",
                "M15_OHLC_PATH_LABEL_ONLY",
                "PATH_CONTRACT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
            )
        ):
            code = f"{field}={upper}"
            codes[code] += 1
    snapshot = row.get("mso_snapshot")
    if isinstance(snapshot, dict):
        poi = snapshot.get("candidate_poi")
        if isinstance(poi, dict) and "MISSING" in _norm(poi.get("capture_status")).upper():
            codes["mso_snapshot.candidate_poi.capture_status=CANDIDATE_POI_MISSING"] += 1
        fwq = snapshot.get("framework_qualification")
        if isinstance(fwq, dict) and "MISSING" in _norm(fwq.get("capture_status")).upper():
            codes[
                "mso_snapshot.framework_qualification.capture_status=FRAMEWORK_QUALIFICATION_MISSING"
            ] += 1
    return codes


def _metric(value: float, *, count: int, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "count": count,
        "mean": 0.0 if count == 0 else value / count,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "shadow_source_log_aggregate",
    }


def _load_source_stats(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_stats: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for unit in units:
        path_text = _norm(unit.get("source_artifact_path"))
        path = _repo_path(path_text)
        records = _iter_file_records(path)
        source_sha = _sha256_file(path) if path.exists() and path.is_file() else ""
        gap_rows = 0
        anchor_rows = 0
        component_counts: Counter[str] = Counter()
        for line_no, record in enumerate(records, start=1):
            symbol = _symbol_from_record(record)
            session = _session_from_record(record)
            side = _side_from_record(record)
            timeframe = _timeframe_from_record(record)
            if symbol and session:
                anchor_rows += 1
            gap_codes = _gap_codes(record)
            if not gap_codes:
                continue
            gap_rows += 1
            component = _component_from_gap_codes(gap_codes)
            component_counts[component] += 1
            key = (path_text, component, symbol, session, side, timeframe)
            bucket = grouped.setdefault(
                key,
                {
                    "unit_ids": set(),
                    "source_path": path_text,
                    "source_artifact_hash": source_sha or _norm(unit.get("source_artifact_hash")),
                    "source_component": component,
                    "symbol": symbol,
                    "route_session": session,
                    "side": side,
                    "timeframe": timeframe,
                    "gap_row_count": 0,
                    "source_row_samples": [],
                    "gap_code_counts": Counter(),
                },
            )
            bucket["unit_ids"].add(_norm(unit.get("intelligence_unit_id")))
            bucket["gap_row_count"] += 1
            bucket["gap_code_counts"].update(gap_codes)
            if len(bucket["source_row_samples"]) < 10:
                bucket["source_row_samples"].append(_row_id(record, f"{path.name}:{line_no}"))
        source_stats.append(
            {
                "unit_id": _norm(unit.get("intelligence_unit_id")),
                "path": path_text,
                "exists": path.exists(),
                "rows": len(records),
                "gap_rows": gap_rows,
                "anchor_rows_with_symbol_and_session": anchor_rows,
                "source_artifact_hash": source_sha or _norm(unit.get("source_artifact_hash")),
                "source_component_counts": dict(sorted(component_counts.items())),
            }
        )
    runtime_inputs = list(grouped.values())
    runtime_inputs.sort(
        key=lambda row: (
            row["source_path"],
            row["source_component"],
            row["symbol"],
            row["route_session"],
            row["side"],
            row["timeframe"],
        )
    )
    return source_stats, runtime_inputs


def build_runtime_rows(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_stats, runtime_inputs = _load_source_stats(units)
    runtime_rows: list[dict[str, Any]] = []
    for index, item in enumerate(runtime_inputs, start=1):
        symbol = item["symbol"]
        source_component = item["source_component"]
        route_session = item["route_session"]
        side = item["side"]
        timeframe = item["timeframe"] or "M15"
        runtime_row_id = f"SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_{index:05d}"
        event_scope = {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": timeframe,
            "market_timeframe": timeframe,
            "route_session": route_session,
            "route_family": "source_discovery",
            "source_component": source_component,
        }
        if side:
            event_scope["side"] = side
        runtime_rows.append(
            {
                "schema_version": "gtos_vnext_shadow_source_log_materialization_runtime_row_v1",
                "wave_id": WAVE_ID,
                "shadow_source_log_materialization_runtime_row_id": runtime_row_id,
                "row_key": runtime_row_id,
                "source_row_id": runtime_row_id,
                "source_path": item["source_path"],
                "source_artifact": item["source_path"],
                "source_artifact_hash": item["source_artifact_hash"],
                "source_unit_ids": sorted(item["unit_ids"]),
                "source_row_samples": item["source_row_samples"],
                "gap_code_counts": dict(item["gap_code_counts"].most_common(25)),
                "gap_source_rows_represented": item["gap_row_count"],
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
                "timeframe": timeframe,
                "market_timeframe": timeframe,
                "route_session": route_session,
                "side": side,
                "route_family": "source_discovery",
                "source_component": source_component,
                "source_group": "shadow_source_log_materialization",
                "source_role": "shadow_source_log_materialization_guard",
                "source_name": "gtos_vnext_shadow_source_log_materialization_wave",
                "evidence_family": "gtos_vnext_shadow_source_log_materialization",
                "system_surface": "shadow_source_log_materialization_runtime",
                "action_family": "shadow_source_log_materialization_guard",
                "action_class": "shadow_source_capture_required",
                "r_evidence_class": "SHADOW_SOURCE_LOG_MATERIALIZATION_REQUIRED",
                "review_action": "MIXED_SOURCE_CAPTURE_GUARD",
                "decision": "MIXED",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "source_complete": False,
                "source_bound": bool(symbol and route_session),
                "source_acquisition_required": True,
                "source_acquisition_kind": "shadow_source_log_materialization_gap",
                "runtime_decision_effect": False,
                "event_scope": event_scope,
                "r_metrics": {
                    "proxy_score": _metric(
                        0.0,
                        count=item["gap_row_count"],
                        source_field="shadow_source_gap_no_candidate_use",
                    ),
                    "effective_n": _metric(
                        float(item["gap_row_count"]),
                        count=item["gap_row_count"],
                        source_field="shadow_source_gap_rows",
                    ),
                },
                "runtime_source_key": _sha256_text(
                    "|".join(
                        (
                            item["source_path"],
                            source_component,
                            symbol,
                            route_session,
                            side,
                            timeframe,
                        )
                    )
                ),
            }
        )
    return source_stats, runtime_rows


def _dimension_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field)))
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def summarize(
    units: list[dict[str, Any]],
    source_stats: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    total_source_rows = sum(int(item["rows"]) for item in source_stats)
    gap_rows = sum(int(item["gap_rows"]) for item in source_stats)
    return {
        "schema_version": "gtos_vnext_shadow_source_log_materialization_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_unit_count": len(units),
        "source_artifacts": source_stats,
        "source_row_count": total_source_rows,
        "source_gap_row_count": gap_rows,
        "source_complete_or_context_row_count": total_source_rows - gap_rows,
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": sum(
            int(row["gap_source_rows_represented"]) for row in runtime_rows
        ),
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
        "source_acquisition_required_rows": sum(
            int(row["gap_source_rows_represented"])
            for row in runtime_rows
            if row.get("source_acquisition_required")
        ),
        "source_units_with_gap_rows": sum(1 for item in source_stats if item["gap_rows"] > 0),
        "source_units_without_gap_rows": sum(1 for item in source_stats if item["gap_rows"] == 0),
        "empty_source_units": sum(1 for item in source_stats if item["rows"] == 0),
        "decision_counts": _dimension_counts(runtime_rows, "decision"),
        "r_evidence_class_counts": _dimension_counts(runtime_rows, "r_evidence_class"),
        "source_component_counts": _dimension_counts(runtime_rows, "source_component"),
        "source_role_counts": _dimension_counts(runtime_rows, "source_role"),
        "source_group_counts": _dimension_counts(runtime_rows, "source_group"),
        "action_class_counts": _dimension_counts(runtime_rows, "action_class"),
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "coverage_counts": {
            "symbols": _dimension_counts(runtime_rows, "symbol"),
            "markets": _dimension_counts(runtime_rows, "market"),
            "source_symbols": _dimension_counts(runtime_rows, "source_symbol"),
            "timeframes": _dimension_counts(runtime_rows, "timeframe"),
            "sessions": _dimension_counts(runtime_rows, "route_session"),
            "sides": _dimension_counts(runtime_rows, "side"),
            "entry_variants": _dimension_counts(runtime_rows, "entry_variant"),
            "target_stop_order_classes": _dimension_counts(runtime_rows, "target_stop_order_class"),
            "source_components": _dimension_counts(runtime_rows, "source_component"),
            "source_roles": _dimension_counts(runtime_rows, "source_role"),
            "primitives": _dimension_counts(runtime_rows, "primitive"),
        },
        "source_component_gap_row_counts": dict(
            sorted(
                Counter(
                    {
                        key: sum(
                            int(row["gap_source_rows_represented"])
                            for row in runtime_rows
                            if row["source_component"] == key
                        )
                        for key in SOURCE_COMPONENTS
                    }
                ).items()
            )
        ),
        "source_path_gap_row_counts": dict(
            sorted(
                (
                    item["path"],
                    item["gap_rows"],
                )
                for item in source_stats
            )
        ),
        "row_id_samples": [
            row.get("shadow_source_log_materialization_runtime_row_id")
            for row in runtime_rows[:10]
        ],
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build without writing outputs")
    args = parser.parse_args()

    units = _read_master_units()
    source_stats, runtime_rows = build_runtime_rows(units)
    summary = summarize(units, source_stats, runtime_rows)
    if not args.check:
        write_jsonl(OUTPUT_ROWS, runtime_rows)
        OUTPUT_SUMMARY.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
