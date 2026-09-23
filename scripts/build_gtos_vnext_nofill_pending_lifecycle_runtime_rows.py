#!/usr/bin/env python3
"""Build compact runtime rows for the no-fill and pending-lifecycle wave."""

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
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_SUMMARY_{DATE}.json"

NOFILL_TOKENS = ("nofill", "no_fill", "pending", "prefill")
EXCLUDED_WAVE_TOKENS = (
    "gtos_vnext_nofill_pending_lifecycle_runtime",
    "local_repaired_proxy",
    "system_transfer_nearmiss_market_entry_join",
    "unified_system_candidate",
    "system_transfer_market_gap_primitive_expansion",
    "expanded_market",
)
RUNTIME_SUFFIXES = {".jsonl", ".json"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv"}


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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _path_in_nofill_pending_wave(path_text: str) -> bool:
    lower = path_text.casefold().replace("\\", "/")
    if not any(token in lower for token in NOFILL_TOKENS):
        return False
    if any(token in lower for token in EXCLUDED_WAVE_TOKENS):
        return False
    return True


def _source_paths() -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    for path, git_hash, _algorithm in master_ledger.iter_source_files():
        text = _path_text(path)
        if _path_in_nofill_pending_wave(text):
            paths.append((path, git_hash))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _source_group(path: Path) -> str:
    name = path.name
    for prefix in (
        "HISTORICAL_OHLC_GTOS_REPLAY_",
        "MAIN_ORCH24_",
        "G0_",
        "G12_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-18.jsonl",
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_ROWS_2026-05-09.jsonl",
        "_2026-05-17.jsonl",
        "_2026-05-16.jsonl",
        "_2026-05-15.jsonl",
        "_2026-05-10.jsonl",
        "_2026-05-09.jsonl",
        "_2026-05-08.jsonl",
        ".jsonl",
        ".json",
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
    candidate_id = _norm(row.get("candidate_id"))
    if "_" in candidate_id:
        return candidate_id.split("_", 1)[1]
    for key in (
        "decision_time_utc",
        "decision_asof_utc",
        "source_path_start_utc",
        "probe_window_start_utc",
    ):
        if value := _norm(row.get(key)):
            return value
    return ""


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _variant, _horizon = _route_parts(row)
    if value := _norm(row.get("symbol") or row.get("source_symbol") or route_symbol):
        return value
    candidate_id = _norm(row.get("candidate_id"))
    if "_20" in candidate_id:
        return candidate_id.split("_20", 1)[0]
    return ""


def _route_session(row: dict[str, Any]) -> str:
    _symbol_value, route_session, _variant, _horizon = _route_parts(row)
    if value := _norm(row.get("route_session") or row.get("session") or route_session):
        return value
    return _session_from_time(_candidate_time(row))


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol_value, _session, _variant, horizon = _route_parts(row)
    return _norm(row.get("horizon_id") or horizon)


def _entry_variant(row: dict[str, Any]) -> str:
    _symbol_value, _session, variant, _horizon = _route_parts(row)
    return _norm(
        row.get("entry_variant")
        or row.get("source_entry_variant")
        or row.get("market_entry_variant")
        or row.get("split_variant")
        or row.get("branch_type")
        or variant
    )


def _market_timeframe(row: dict[str, Any], path: Path) -> str:
    value = _norm(row.get("market_timeframe") or row.get("timeframe") or row.get("source_timeframe"))
    if value:
        return value
    name = path.name.casefold()
    if "m1" in name:
        return "M1"
    if "m15" in name or "main_orch24" in name or "pending" in name or "prefill" in name:
        return "M15"
    return ""


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "execution_friction_branch_id",
        "avoid_filter_branch_id",
        "system_transfer_branch_id",
        "near_miss_entry_control_market_branch_id",
        "near_miss_entry_control_offset_branch_id",
        "near_miss_entry_control_source_requirement_id",
        "branch_id",
        "split_id",
        "packet_row_id",
        "row_id",
        "source_row_id",
        "candidate_id",
        "event_id",
        "cost_sensitivity_signature_id",
    ):
        if value := _norm(row.get(key)):
            return value
    return _sha256_text(json.dumps(row, sort_keys=True, default=str))[:24]


def _first_numeric(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _target_stop_order_class(row: dict[str, Any]) -> str:
    text = " ".join(
        _norm(row.get(key)).upper()
        for key in (
            "target_stop_result",
            "market_first_touch_status",
            "first_touch_status_offset_proxy",
            "ltf_terminal_outcome_status",
            "categorical_lifecycle_label",
            "source_closure_label",
        )
        if _norm(row.get(key))
    )
    if "STOP_TOUCH_FIRST" in text or "STOP_TOUCH_BEFORE_TARGET" in text or "STOP_FIRST" in text:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_TOUCH_FIRST" in text or "TARGET_FIRST" in text:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "SAME_M15" in text or "AMBIG" in text:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    if "NO_TARGET_OR_STOP_TOUCH" in text or "NO_FILL" in text or "UNFILLED" in text:
        return "NO_FILL_OR_UNFILLED_DOMINANT"
    return ""


def _source_component(path: Path, row: dict[str, Any]) -> str:
    name = path.name.casefold()
    text = " ".join(
        _norm(row.get(key)).casefold()
        for key in (
            "evidence_class",
            "primitive_family",
            "source_requirement_status",
            "source_requirement_action",
            "implementation_decision",
            "current_action",
            "next_action",
            "branch_decision",
        )
        if _norm(row.get(key))
    )
    if "source_requirement" in name or "source_requirement" in text or "source_capture" in text:
        return "nofill_near_miss_source_requirement"
    if "market_entry" in name:
        return "nofill_near_miss_market_entry"
    if "offset" in name or "entry_offset" in name:
        return "nofill_near_miss_offset"
    if "source_confidence" in name:
        return "nofill_far_miss_source_confidence"
    if "retest" in name and "avoid" not in name:
        return "nofill_far_miss_retest"
    if "family" in name and "far_miss" in name:
        return "nofill_far_miss_family"
    if "geometry" in name and "invalid" in name:
        return "nofill_near_miss_source_requirement"
    if "geometry" in name and "repair_proxy" in name:
        return "nofill_near_miss_offset"
    if any(token in name for token in ("execution_friction", "far_miss", "avoid_retest", "cost_threshold")):
        return "nofill_far_miss_avoid"
    if "prefill" in name and "offset" in text:
        return "nofill_near_miss_offset"
    if "pending" in text and "no lifecycle source" in text:
        return "nofill_far_miss_retest"
    decision = _norm(row.get("action_class")).upper()
    return "nofill_far_miss_avoid" if decision in {"KILL", "REDESIGN"} else "nofill_far_miss_retest"


def _decision(path: Path, row: dict[str, Any], source_component: str) -> str:
    target_stop_class = _target_stop_order_class(row)
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "AVOID"
    if target_stop_class == "TARGET_FIRST_PROXY_DOMINANT" and source_component == "nofill_near_miss_market_entry":
        return "FOLLOW"

    branch_result = _norm(row.get("branch_result_binary")).upper()
    decision_direction = _norm(row.get("decision_direction")).upper()
    if branch_result == "REJECTED" or decision_direction in {"KILL_OR_REDESIGN", "KEEP_REPAIR_OR_AVOID"}:
        return "AVOID"
    if (
        branch_result == "ACCEPTED"
        and decision_direction == "KEEP_CHALLENGER"
        and source_component != "nofill_far_miss_avoid"
    ):
        return "FOLLOW"

    numeric = _first_numeric(
        row,
        "after_proxy_r",
        "selected_shift_proxy_r",
        "linked_entry_offset_selected_proxy_r",
        "action_decision_recomputed_proxy_r",
        "market_entry_signed_delta_over_rolling_range",
        "market_entry_signed_delta_vs_near_limit",
        "directional_close_units",
    )
    if numeric is not None:
        if numeric > 0 and source_component == "nofill_near_miss_market_entry":
            return "FOLLOW"
        if numeric < 0:
            return "AVOID"

    text = " ".join(
        _norm(row.get(key)).upper()
        for key in (
            "action_class",
            "implementation_decision",
            "current_action",
            "next_action",
            "coverage_status",
            "geometry_status",
            "source_requirement_status",
            "categorical_lifecycle_label",
            "v3_terminal_state",
            "label_class",
            "source_closure_label",
        )
        if _norm(row.get(key))
    )
    if any(token in text for token in ("KILL", "AVOID", "STOP_FIRST", "INVALID_GEOMETRY")):
        return "AVOID"
    if source_component == "nofill_far_miss_avoid":
        return "AVOID"
    if any(token in text for token in ("REPAIR", "REDESIGN", "BLOCKED", "SOURCE", "AMBIG", "NO_SCORE")):
        return "MIXED"
    if any(token in text for token in ("KEEP", "IMPLEMENT", "ACCEPTED", "READY")):
        return "FOLLOW"
    return "MIXED"


def _action_class(source_component: str, decision: str) -> str:
    if decision == "AVOID":
        return "nofill_lifecycle_avoid_filter"
    if decision == "FOLLOW" and source_component == "nofill_near_miss_market_entry":
        return "nofill_lifecycle_market_entry_follow"
    if decision == "FOLLOW":
        return "nofill_lifecycle_retest_follow"
    if source_component == "nofill_near_miss_source_requirement":
        return "nofill_lifecycle_source_requirement_guard"
    return "nofill_lifecycle_context_guard"


def _implementation_action(source_component: str, decision: str) -> str:
    if decision == "AVOID":
        if source_component == "nofill_near_miss_offset":
            return "NOFILL_PENDING_OFFSET_AVOID_GUARD"
        return "NOFILL_PENDING_FAR_MISS_AVOID_GUARD"
    if decision == "FOLLOW" and source_component == "nofill_near_miss_market_entry":
        return "NOFILL_PENDING_MARKET_ENTRY_NOW_CANDIDATE"
    if decision == "FOLLOW":
        return "NOFILL_PENDING_RETEST_KEEP_CONTEXT"
    if source_component == "nofill_near_miss_source_requirement":
        return "NOFILL_PENDING_SOURCE_REQUIREMENT_CONTEXT"
    return "NOFILL_PENDING_LIFECYCLE_CONTEXT"


def _metric_trace(total: float, count: float, positive: int, negative: int, zero: int, source_field: str) -> dict[str, Any]:
    mean = total / count if count else None
    return {
        "sum": round(total, 12),
        "count": count,
        "mean": round(mean, 12) if mean is not None else None,
        "positive_rows": positive,
        "negative_rows": negative,
        "zero_rows": zero,
        "source_field": source_field,
        "source_shape": "nofill_pending_lifecycle_compact_scope",
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
    entry_variant: str
    source_component: str
    decision: str
    action_class: str
    target_stop_order_class: str
    proxy_r_class: str
    implementation_action: str
    rows: int = 0
    proxy_sum: float = 0.0
    proxy_count: float = 0.0
    proxy_positive: int = 0
    proxy_negative: int = 0
    proxy_zero: int = 0
    effective_n_sum: float = 0.0
    row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.effective_n_sum += 1.0
        if row_id := _row_id(row):
            if len(self.row_ids_sample) < 5:
                self.row_ids_sample.append(row_id)
        proxy = _first_numeric(
            row,
            "after_proxy_r",
            "selected_shift_proxy_r",
            "linked_entry_offset_selected_proxy_r",
            "action_decision_recomputed_proxy_r",
            "market_entry_signed_delta_over_rolling_range",
            "market_entry_signed_delta_vs_near_limit",
            "directional_close_units",
        )
        if proxy is not None:
            signed = abs(proxy) if self.decision == "FOLLOW" else -abs(proxy) if self.decision == "AVOID" else proxy
            self.proxy_sum += signed
            self.proxy_count += 1.0
            self.proxy_positive += int(signed > 0)
            self.proxy_negative += int(signed < 0)
            self.proxy_zero += int(signed == 0)

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
                self.entry_variant,
                self.source_component,
                self.decision,
                self.action_class,
                self.target_stop_order_class,
            ]
        )
        row_id = f"nofill_pending_lifecycle:{_sha256_text(key_payload)[:24]}"
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
                "entry_variant": self.entry_variant,
                "source_component": self.source_component,
                "route_family": "nofill_mechanical",
                "action_class": self.action_class,
                "target_stop_order_class": self.target_stop_order_class,
                "proxy_r_class": self.proxy_r_class,
            }.items()
            if value
        }
        metrics = {
            "effective_n": _metric_trace(
                self.effective_n_sum,
                max(float(self.rows), 1.0),
                int(self.effective_n_sum > 0),
                0,
                int(self.effective_n_sum == 0),
                "nofill_pending_lifecycle_source_rows",
            )
        }
        if self.proxy_count:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_sum,
                self.proxy_count,
                self.proxy_positive,
                self.proxy_negative,
                self.proxy_zero,
                "nofill_pending_lifecycle_proxy_score",
            )
            metrics["stress_simulated_r"] = metrics["proxy_score"]
        return {
            "schema_version": "gtos_vnext_nofill_pending_lifecycle_runtime_row_v1",
            "row_key": row_id,
            "nofill_pending_lifecycle_runtime_row_id": row_id,
            "source_name": "gtos_vnext_nofill_pending_lifecycle_wave",
            "evidence_family": "gtos_vnext_nofill_pending_lifecycle",
            "source_group": self.source_group,
            "source_role": "nofill_pending_lifecycle_runtime_rollup",
            "system_surface": "nofill_pending_execution_behavior",
            "runtime_effect_now": {
                "FOLLOW": "nofill_pending_lifecycle_follow_or_market_entry",
                "AVOID": "nofill_pending_lifecycle_avoid_or_skip_pending",
            }.get(self.decision, "nofill_pending_lifecycle_source_context"),
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "r_evidence_class": {
                "FOLLOW": "NOFILL_PENDING_POSITIVE_PROXY_OR_RETEST",
                "AVOID": "NOFILL_PENDING_NEGATIVE_PROXY_OR_STOP_FIRST",
            }.get(self.decision, "NOFILL_PENDING_SOURCE_REQUIREMENT_OR_CONTEXT"),
            "decision": self.decision,
            "source_component": self.source_component,
            "route_family": "nofill_mechanical",
            "symbol": self.symbol,
            "source_symbol": self.source_symbol,
            "symbol_family": self.symbol_family,
            "market_timeframe": self.market_timeframe,
            "timeframe": self.market_timeframe,
            "route_session": self.route_session,
            "side": self.side,
            "horizon_id": self.horizon_id,
            "entry_variant": self.entry_variant,
            "proxy_r_class": self.proxy_r_class,
            "target_stop_order_class": self.target_stop_order_class,
            "source_path": self.source_path,
            "drill_through_path": self.source_path,
            "source_artifact_hash_sha256": self.source_hash,
            "source_rows_represented": self.rows,
            "source_row_ids_sample": self.row_ids_sample,
            "source_bound": bool((self.symbol or self.source_symbol or self.symbol_family) and self.route_session and self.side),
            "source_complete": self.decision in {"FOLLOW", "AVOID"},
            "runtime_candidate_use_permitted": self.decision in {"FOLLOW", "AVOID"},
            "candidate_use_allowed_now": self.decision in {"FOLLOW", "AVOID"},
            "r_metrics": metrics,
            "event_scope": scope,
        }


def _proxy_class(decision: str) -> str:
    if decision == "FOLLOW":
        return "POSITIVE_PROXY_R"
    if decision == "AVOID":
        return "NEGATIVE_PROXY_R"
    return "NOFILL_PENDING_CONTEXT_PROXY"


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
    for path, git_hash in _source_paths():
        path_text = _path_text(path)
        line_count = _line_count(path)
        source_hash = git_hash or _sha256_file(path)
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
            symbol_family = resolve_vnext_symbol_family(symbol) if symbol else ""
            route_session = _route_session(row)
            side = _norm(row.get("side")).upper()
            source_component = _source_component(path, row)
            decision = _decision(path, row, source_component)
            action_class = _action_class(source_component, decision)
            target_stop_order_class = _target_stop_order_class(row)
            key = (
                path_text,
                source_hash,
                source_group,
                symbol,
                source_symbol,
                symbol_family,
                _market_timeframe(row, path),
                route_session,
                side,
                _horizon_id(row),
                _entry_variant(row),
                source_component,
                decision,
                action_class,
                target_stop_order_class,
                _proxy_class(decision),
                _implementation_action(source_component, decision),
            )
            if not (symbol or source_symbol or side or route_session or source_component):
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
        "schema_version": "gtos_vnext_nofill_pending_lifecycle_runtime_summary_v1",
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "wave_source_rows_counted": counted_source_rows,
        "wave_source_artifact_count": len(source_stats),
        "wave_source_artifact_suffix_counts": dict(
            sorted(Counter(stat["suffix"] for stat in source_stats).items())
        ),
        "row_count_unknown_source_artifact_count": sum(1 for stat in source_stats if stat.get("rows") is None),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(row["source_component"] for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "target_stop_order_class_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows if row.get("target_stop_order_class")).items())
        ),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
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
