#!/usr/bin/env python3
"""Build vNext runtime rows for OTI4 opening-drive source-contract evidence."""

from __future__ import annotations

import argparse
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

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "oti4_opening_drive_source_correction_or_contract_revision"
)
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_SUMMARY_{DATE}.json"

ROW_DECISION_JSON = SOURCE_DIR / "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_2026-05-08.json"
ROW_DECISION_JSONL = SOURCE_DIR / "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl"
SOURCE_CONTRACT_JSON = SOURCE_DIR / "OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_2026-05-08.json"
FAILURE_LEDGER_JSON = SOURCE_DIR / "OTI4_OPENING_DRIVE_FAILURE_AND_LEARNING_LEDGER_2026-05-08.json"

COUNTABLE_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".csv", ".yaml", ".yml"}
SOURCE_SESSION_MAP = {
    "london": "london_core",
    "ny": "ny_core",
    "tokyo": "tokyo_kz",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _line_count(path: Path) -> int | None:
    if path.suffix.lower() == ".json":
        return 1
    if path.suffix.lower() not in COUNTABLE_SUFFIXES:
        return None
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_paths() -> list[Path]:
    return sorted(
        [
            path
            for path in SOURCE_DIR.iterdir()
            if path.is_file() and path.name != "__pycache__"
        ],
        key=lambda path: path.name.casefold(),
    )


def _route_session(row: dict[str, Any]) -> str:
    raw = _norm(row.get("session")).casefold()
    return SOURCE_SESSION_MAP.get(raw, raw)


def _decision_shape(row_route_decision: str) -> tuple[str, str, str, str, str, str, bool]:
    if row_route_decision == "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT":
        return (
            "MIXED",
            "opening_drive_source_projection",
            "opening_drive_source_contract",
            "opening_drive_source_projection_context",
            "opening_drive_source_contract_context",
            "OPENING_DRIVE_SOURCE_CONTRACT_READY_NO_LABEL",
            True,
        )
    if row_route_decision == "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY":
        return (
            "MIXED",
            "opening_drive_source_gap",
            "source_repair_proof",
            "source_repair_execution_plan",
            "source_repair_queue_catalog",
            "SOURCE_REPAIR_FOR_EXACT_R",
            False,
        )
    return (
        "AVOID",
        "opening_drive_contract_exclusion",
        "opening_drive_contract_exclusion",
        "opening_drive_contract_exclusion",
        "opening_drive_contract_gate",
        "OPENING_DRIVE_CONTRACT_EXCLUSION",
        True,
    )


def _action_class(row_route_decision: str) -> str:
    return {
        "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": (
            "opening_drive_source_projection_ready"
        ),
        "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": (
            "opening_drive_source_gap_repair_required"
        ),
        "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": (
            "opening_drive_contract_exclude_breakout_side_mismatch"
        ),
        "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": (
            "opening_drive_contract_exclude_decision_before_range_close"
        ),
        "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": (
            "opening_drive_contract_exclude_no_breakout_asof"
        ),
    }.get(row_route_decision, "opening_drive_contract_context")


def _runtime_effect(decision: str, source_component: str) -> str:
    if source_component == "opening_drive_source_projection":
        return "opening_drive_source_contract_context_no_live_effect"
    if source_component == "opening_drive_source_gap":
        return "opening_drive_source_gap_risk_guard"
    if decision == "AVOID":
        return "opening_drive_contract_exclusion_filter"
    return "opening_drive_contract_context"


def _implementation_action(row_route_decision: str) -> str:
    return {
        "PATCH_SOURCE_PROJECTION_READY_FOR_FUTURE_CONTRACT_AUDIT": (
            "OPENING_DRIVE_SOURCE_PROJECTION_READY_FUTURE_CONTRACT_AUDIT"
        ),
        "SOURCE_BLOCKED_EXACT_RANGE_TICK_WINDOW_EMPTY": (
            "OPENING_DRIVE_SOURCE_GAP_REQUIRES_READ_ONLY_SOURCE_OR_CACHE"
        ),
        "CONTRACT_REVISED_EXCLUDE_BREAKOUT_SIDE_MISMATCH": (
            "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE_OPENING_DRIVE_EXCLUDE_BREAKOUT_SIDE_MISMATCH"
        ),
        "CONTRACT_REVISED_EXCLUDE_DECISION_BEFORE_FROZEN_RANGE_CLOSE": (
            "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE_OPENING_DRIVE_EXCLUDE_DECISION_BEFORE_RANGE_CLOSE"
        ),
        "CONTRACT_REVISED_EXCLUDE_NO_BREAKOUT_ASOF": (
            "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE_OPENING_DRIVE_EXCLUDE_NO_BREAKOUT_ASOF"
        ),
    }.get(row_route_decision, "OPENING_DRIVE_CONTRACT_CONTEXT")


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
        "source_shape": "opening_drive_source_contract_compact_scope",
    }


@dataclass
class Group:
    symbol: str
    symbol_family: str
    route_session: str
    side: str
    row_route_decision: str
    exact_blocker_code: str
    decision: str
    source_component: str
    source_group: str
    source_role: str
    system_surface: str
    r_evidence_class: str
    source_complete: bool
    rows: int = 0
    source_contract_keys: set[str] = field(default_factory=set)
    source_row_ids_sample: list[str] = field(default_factory=list)
    packet_row_ids_sample: list[str] = field(default_factory=list)
    range_tick_count: int = 0
    breakout_scan_bar_count: int = 0

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        if value := _norm(row.get("source_contract_key")):
            self.source_contract_keys.add(value)
        if value := _norm(row.get("source_row_id")):
            if len(self.source_row_ids_sample) < 5:
                self.source_row_ids_sample.append(value)
        if value := _norm(row.get("packet_row_id")):
            if len(self.packet_row_ids_sample) < 5:
                self.packet_row_ids_sample.append(value)
        range_bars = row.get("source_hashed_range_bars")
        if isinstance(range_bars, dict):
            self.range_tick_count += int(range_bars.get("tick_count") or 0)
        breakout_bars = row.get("source_hashed_breakout_scan_bars")
        if isinstance(breakout_bars, dict):
            self.breakout_scan_bar_count += int(breakout_bars.get("bar_count") or 0)
        blocker_probe = row.get("blocker_source_probe")
        if isinstance(blocker_probe, dict):
            self.range_tick_count += int(blocker_probe.get("range_tick_count") or 0)

    def to_row(self, source_hash: str) -> dict[str, Any]:
        key_payload = "|".join(
            [
                self.symbol,
                self.route_session,
                self.side,
                self.row_route_decision,
                self.exact_blocker_code,
                self.source_component,
            ]
        )
        row_id = f"opening_drive_source_contract:{_sha256_text(key_payload)[:24]}"
        action_class = _action_class(self.row_route_decision)
        implementation_action = _implementation_action(self.row_route_decision)
        scope = {
            "symbol": self.symbol,
            "source_symbol": self.symbol,
            "symbol_family": self.symbol_family,
            "market": self.symbol,
            "market_timeframe": "M15",
            "timeframe": "M15",
            "route_session": self.route_session,
            "side": self.side,
            "source_component": self.source_component,
            "route_family": "nofill_opening_drive",
            "action_class": action_class,
            "row_route_decision": self.row_route_decision,
        }
        metrics = {
            "effective_n": _metric_trace(
                float(self.rows),
                max(float(self.rows), 1.0),
                "opening_drive_source_contract_rows",
            )
        }
        if self.range_tick_count:
            metrics["range_tick_count"] = _metric_trace(
                float(self.range_tick_count),
                max(float(self.rows), 1.0),
                "source_hashed_range_tick_count",
            )
        if self.breakout_scan_bar_count:
            metrics["breakout_scan_bar_count"] = _metric_trace(
                float(self.breakout_scan_bar_count),
                max(float(self.rows), 1.0),
                "source_hashed_breakout_scan_bar_count",
            )
        return {
            "schema_version": "gtos_vnext_opening_drive_source_contract_runtime_row_v1",
            "row_key": row_id,
            "opening_drive_source_contract_runtime_row_id": row_id,
            "source_name": "gtos_vnext_opening_drive_source_contract_wave",
            "evidence_family": "gtos_vnext_opening_drive_source_contract",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": self.system_surface,
            "runtime_effect_now": _runtime_effect(self.decision, self.source_component),
            "implementation_action": implementation_action,
            "action_class": action_class,
            "r_evidence_class": self.r_evidence_class,
            "decision": self.decision,
            "source_component": self.source_component,
            "route_family": "nofill_opening_drive",
            "target_stop_order_class": "NO_FILL_OR_UNFILLED_DOMINANT",
            "row_route_decision": self.row_route_decision,
            "exact_blocker_code": self.exact_blocker_code,
            "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
            "symbol": self.symbol,
            "source_symbol": self.symbol,
            "symbol_family": self.symbol_family,
            "market": self.symbol,
            "market_timeframe": "M15",
            "timeframe": "M15",
            "source_timeframe": "M1",
            "route_session": self.route_session,
            "side": self.side,
            "source_path": _path_text(ROW_DECISION_JSONL),
            "drill_through_path": _path_text(ROW_DECISION_JSONL),
            "source_artifact_hash_sha256": source_hash,
            "source_rows_represented": self.rows,
            "source_contract_key_count": len(self.source_contract_keys),
            "source_contract_keys_sample": sorted(self.source_contract_keys)[:5],
            "source_row_ids_sample": self.source_row_ids_sample,
            "packet_row_ids_sample": self.packet_row_ids_sample,
            "source_bound": True,
            "source_complete": self.source_complete,
            "validation_safe": False,
            "live_effect": False,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "outcome_review_opened": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "r_metrics": metrics,
            "event_scope": scope,
        }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_hash = _sha256_file(ROW_DECISION_JSONL)
    source_rows = _read_jsonl(ROW_DECISION_JSONL)
    row_decision_payload = _read_json(ROW_DECISION_JSON)
    source_contract_payload = _read_json(SOURCE_CONTRACT_JSON)
    failure_payload = _read_json(FAILURE_LEDGER_JSON)

    groups: dict[tuple[str, ...], Group] = {}
    for row in source_rows:
        row_route_decision = _norm(row.get("row_route_decision"))
        (
            decision,
            source_component,
            source_group,
            source_role,
            system_surface,
            r_evidence_class,
            source_complete,
        ) = _decision_shape(row_route_decision)
        symbol = _norm(row.get("symbol"))
        exact_blocker_code = _norm(row.get("exact_blocker_code"))
        key = (
            symbol,
            resolve_vnext_symbol_family(symbol),
            _route_session(row),
            _norm(row.get("side")).upper(),
            row_route_decision,
            exact_blocker_code,
            decision,
            source_component,
            source_group,
            source_role,
            system_surface,
            r_evidence_class,
            str(source_complete),
        )
        group = groups.get(key)
        if group is None:
            group = Group(
                symbol=symbol,
                symbol_family=resolve_vnext_symbol_family(symbol),
                route_session=_route_session(row),
                side=_norm(row.get("side")).upper(),
                row_route_decision=row_route_decision,
                exact_blocker_code=exact_blocker_code,
                decision=decision,
                source_component=source_component,
                source_group=source_group,
                source_role=source_role,
                system_surface=system_surface,
                r_evidence_class=r_evidence_class,
                source_complete=source_complete,
            )
            groups[key] = group
        group.add(row)

    rows = [group.to_row(source_hash) for group in groups.values()]
    rows.sort(key=lambda row: row["row_key"])

    source_stats: list[dict[str, Any]] = []
    for path in _source_paths():
        runtime_rows_read = 0
        source_packet_rows_read = 0
        contract_terms_read = 0
        if path == ROW_DECISION_JSONL:
            runtime_rows_read = len(source_rows)
        elif path == ROW_DECISION_JSON:
            runtime_rows_read = len(row_decision_payload.get("rows") or [])
        elif path == SOURCE_CONTRACT_JSON:
            source_packet_rows_read = len(source_contract_payload.get("source_packet_rows") or [])
            runtime_rows_read = source_packet_rows_read
        elif path == FAILURE_LEDGER_JSON:
            contract_terms = failure_payload.get("future_contract_terms")
            contract_terms_read = 1 if isinstance(contract_terms, dict) and contract_terms else 0
            runtime_rows_read = contract_terms_read
        source_stats.append(
            {
                "path": _path_text(path),
                "exists": True,
                "rows": _line_count(path),
                "runtime_rows_read": runtime_rows_read,
                "source_packet_rows_read": source_packet_rows_read,
                "contract_terms_read": contract_terms_read,
                "sha256_or_git_blob": _sha256_file(path),
                "suffix": path.suffix.lower(),
            }
        )

    source_rows_represented = sum(int(row["source_rows_represented"]) for row in rows)
    counted_source_rows = sum(
        int(stat["rows"]) for stat in source_stats if isinstance(stat.get("rows"), int)
    )
    source_row_decision_counts = Counter(row.get("row_route_decision") for row in source_rows)
    source_symbol_counts = Counter(row.get("symbol") for row in source_rows)
    source_session_counts = Counter(_route_session(row) for row in source_rows)
    source_side_counts = Counter(_norm(row.get("side")).upper() for row in source_rows)
    summary = {
        "schema_version": "gtos_vnext_opening_drive_source_contract_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "target_runtime_rows_read": len(source_rows),
        "source_packet_rows_read": len(source_contract_payload.get("source_packet_rows") or []),
        "contract_terms_read": int(bool(failure_payload.get("future_contract_terms"))),
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
        "row_route_decision_counts": dict(sorted(Counter(row["row_route_decision"] for row in rows).items())),
        "source_row_route_decision_counts": dict(sorted(source_row_decision_counts.items())),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows).items())),
        "source_symbol_counts": dict(sorted(source_symbol_counts.items())),
        "timeframe_counts": dict(sorted(Counter(row["timeframe"] for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(row["route_session"] for row in rows).items())),
        "source_session_counts": dict(sorted(source_session_counts.items())),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows).items())),
        "source_side_counts": dict(sorted(source_side_counts.items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "system_surface_counts": dict(sorted(Counter(row["system_surface"] for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(Counter(row["r_evidence_class"] for row in rows).items())),
        "source_contract_key_count": sum(int(row.get("source_contract_key_count") or 0) for row in rows),
        "blank_anchor_counts": {
            key: count
            for key, count in {
                "symbol": sum(1 for row in rows if not row.get("symbol")),
                "route_session": sum(1 for row in rows if not row.get("route_session")),
                "side": sum(1 for row in rows if not row.get("side")),
            }.items()
            if count
        },
        "source_artifacts": source_stats,
        "output_rows": _path_text(OUTPUT_ROWS),
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
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
