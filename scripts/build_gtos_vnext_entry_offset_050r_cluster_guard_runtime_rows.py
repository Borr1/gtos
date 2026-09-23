#!/usr/bin/env python3
"""Build compact runtime rows for the entry-offset 0.50R cluster-guard wave."""

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

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family

SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_NAMES = (
    "build_main_orchestrator_action_after_entry_offset_concentration_guard_2026_05_17.py",
    "build_main_orchestrator_entry_offset_050r_candidate_decisions_2026_05_16.py",
    "build_main_orchestrator_entry_offset_050r_shadow_scorer_outputs_2026_05_16.py",
    "build_main_orchestrator_entry_offset_050r_source_capture_integration_2026_05_16.py",
    "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_OUTPUT_MANIFEST_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_SUMMARY_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_VERIFICATION_RESULT_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_MANIFEST_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_SUMMARY_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_VERIFICATION_RESULT_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_MANIFEST_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_SUMMARY_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_VERIFICATION_RESULT_2026-05-16.json",
    "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD_VERIFY_RESULT_2026-05-17.json",
    "verify_main_orchestrator_action_after_entry_offset_concentration_guard_2026_05_17.py",
    "verify_main_orchestrator_entry_offset_050r_candidate_decisions_2026_05_16.py",
    "verify_main_orchestrator_entry_offset_050r_shadow_scorer_outputs_2026_05_16.py",
    "verify_main_orchestrator_entry_offset_050r_source_capture_integration_2026_05_16.py",
)

CORE_RUNTIME_SOURCE_NAMES = {
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl",
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
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _count_rows(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return 1 if path.exists() and path.stat().st_size else 0
    if suffix not in {".jsonl", ".py", ".md", ".txt", ".csv"}:
        return None
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _candidate_time(row: dict[str, Any]) -> str:
    candidate_id = _norm(row.get("candidate_id"))
    marker = "_20"
    if marker in candidate_id:
        return candidate_id[candidate_id.index(marker) + 1 :]
    return _norm(row.get("decision_time_utc") or row.get("generated_utc"))


def _route_session(row: dict[str, Any]) -> str:
    if value := _norm(row.get("route_session") or row.get("session")):
        return value
    value = _candidate_time(row)
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
    if value := _norm(row.get("symbol") or row.get("source_symbol")):
        return value
    candidate_id = _norm(row.get("candidate_id"))
    if "_20" in candidate_id:
        return candidate_id.split("_20", 1)[0]
    return ""


def _row_id(row: dict[str, Any]) -> str:
    for key in ("candidate_id", "row_id", "source_row_id", "event_id"):
        if value := _norm(row.get(key)):
            return value
    return _sha256_text(json.dumps(row, sort_keys=True, default=str))[:24]


def _proxy_value(row: dict[str, Any]) -> float | None:
    for key in (
        "entry_offset_proxy_r_reference",
        "selected_shift_proxy_r",
        "shift_050_proxy_r",
        "entry_offset_050r_proxy_r",
        "strategy_proxy_r",
    ):
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _source_rows(path: Path) -> list[dict[str, Any]]:
    if path.name not in CORE_RUNTIME_SOURCE_NAMES:
        return []
    rows = _read_jsonl(path)
    selected: list[dict[str, Any]] = []
    for row in rows:
        if path.name == "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_2026-05-16.jsonl":
            action = _norm(row.get("action_class")).upper()
            if action in {"IMPLEMENT_DEFAULT_OFF", "KILL", "REDESIGN", "SOURCE_REPAIR"}:
                selected.append(row)
            continue
        status = _norm(row.get("entry_offset_concentration_guard_status")).upper()
        if status and status != "NOT_TARGET_ROW":
            selected.append(row)
    return selected


def _decision(row: dict[str, Any]) -> str:
    action = _norm(row.get("action_class")).upper()
    status = _norm(row.get("entry_offset_concentration_guard_status")).upper()
    branch = _norm(row.get("branch_decision") or row.get("implementation_decision")).upper()
    if status == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED":
        return "FOLLOW"
    if status in {"PREFILL_REFERENCE_CLUSTER_GUARDED"}:
        return "MIXED"
    if status == "NO_FILL_CONTROL_SOURCE_COST_FILL_REPAIR_REQUIRED":
        return "AVOID"
    if action == "IMPLEMENT_DEFAULT_OFF":
        return "FOLLOW"
    if action == "KILL" or "NO_FILL" in branch or "KILL" in branch:
        return "AVOID"
    return "MIXED"


def _source_component(row: dict[str, Any], decision: str) -> str:
    action = _norm(row.get("action_class")).upper()
    status = _norm(row.get("entry_offset_concentration_guard_status")).upper()
    branch = _norm(row.get("branch_decision") or row.get("implementation_decision")).upper()
    if action == "SOURCE_REPAIR" or "SOURCE_REPAIR" in branch:
        return "nofill_near_miss_source_requirement"
    if status == "PREFILL_REFERENCE_CLUSTER_GUARDED":
        return "nofill_near_miss_source_requirement"
    if decision == "MIXED":
        return "nofill_near_miss_source_requirement"
    return "nofill_near_miss_offset"


def _source_role(row: dict[str, Any], decision: str) -> str:
    status = _norm(row.get("entry_offset_concentration_guard_status")).lower()
    if status == "entry_offset_owner_cluster_guarded":
        return "entry_offset_050r_cluster_guarded_owner"
    if status == "prefill_reference_cluster_guarded":
        return "entry_offset_050r_prefill_owner_reference"
    if status == "no_fill_control_source_cost_fill_repair_required":
        return "entry_offset_050r_no_fill_control"
    if decision == "FOLLOW":
        return "entry_offset_050r_default_off_follow"
    if decision == "AVOID":
        return "entry_offset_050r_no_fill_avoid"
    return "entry_offset_050r_source_or_redesign_context"


def _action_class(row: dict[str, Any], decision: str, component: str) -> str:
    status = _norm(row.get("entry_offset_concentration_guard_status")).upper()
    if decision == "FOLLOW":
        return "entry_offset_050r_cluster_guarded_follow"
    if decision == "AVOID":
        return "entry_offset_050r_offset_avoid_filter"
    if component == "nofill_near_miss_source_requirement" and status == "PREFILL_REFERENCE_CLUSTER_GUARDED":
        return "entry_offset_050r_prefill_reference_context"
    if component == "nofill_near_miss_source_requirement":
        return "entry_offset_050r_source_requirement_guard"
    return "entry_offset_050r_context_guard"


def _implementation_action(decision: str, component: str) -> str:
    if decision == "FOLLOW":
        return "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_FOLLOW"
    if decision == "AVOID":
        return "ENTRY_OFFSET_050R_NO_FILL_PENDING_OFFSET_AVOID"
    if component == "nofill_near_miss_source_requirement":
        return "ENTRY_OFFSET_050R_SOURCE_REQUIREMENT_OR_OWNER_REFERENCE_CONTEXT"
    return "ENTRY_OFFSET_050R_CONTEXT_GUARD"


def _target_stop_order_class(decision: str) -> str:
    if decision == "FOLLOW":
        return "TARGET_FIRST_PROXY_DOMINANT"
    if decision == "AVOID":
        return "NO_FILL_OR_UNFILLED_DOMINANT"
    return "TARGET_STOP_AMBIGUOUS_OR_MIXED"


def _proxy_r_class(decision: str) -> str:
    if decision == "FOLLOW":
        return "POSITIVE_PROXY_R"
    if decision == "AVOID":
        return "NEGATIVE_PROXY_R"
    return "ENTRY_OFFSET_CONTEXT_OR_SOURCE_REQUIREMENT"


def _metric_trace(total: float, count: float, positive: int, negative: int, zero: int, source_field: str) -> dict[str, Any]:
    mean = total / count if count else None
    return {
        "count": count,
        "mean": round(mean, 12) if mean is not None else None,
        "negative_rows": negative,
        "positive_rows": positive,
        "source_field": source_field,
        "source_shape": "entry_offset_050r_cluster_guard_compact_scope",
        "sum": round(total, 12),
        "zero_rows": zero,
    }


@dataclass
class Group:
    source_path: str
    source_hash: str
    source_group: str
    source_role: str
    symbol: str
    source_symbol: str
    symbol_family: str
    market_timeframe: str
    route_session: str
    side: str
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
    cluster_keys: Counter[str] = field(default_factory=Counter)
    row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.effective_n_sum += 1.0
        if row_id := _row_id(row):
            if len(self.row_ids_sample) < 8:
                self.row_ids_sample.append(row_id)
        if cluster_key := _norm(row.get("entry_offset_concentration_cluster_key")):
            self.cluster_keys[cluster_key] += 1
        proxy = _proxy_value(row)
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
                self.source_role,
                self.symbol,
                self.source_symbol,
                self.symbol_family,
                self.market_timeframe,
                self.route_session,
                self.side,
                self.entry_variant,
                self.source_component,
                self.decision,
                self.action_class,
                self.target_stop_order_class,
            ]
        )
        row_id = f"entry_offset_050r_cluster_guard:{_sha256_text(key_payload)[:24]}"
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
                "entry_offset_050r_source_rows",
            )
        }
        if self.proxy_count:
            metrics["proxy_score"] = _metric_trace(
                self.proxy_sum,
                self.proxy_count,
                self.proxy_positive,
                self.proxy_negative,
                self.proxy_zero,
                "entry_offset_050r_proxy_score",
            )
            metrics["stress_simulated_r"] = metrics["proxy_score"]
        source_bound = bool(
            (self.symbol or self.source_symbol or self.symbol_family)
            and self.route_session
            and self.side
        )
        return {
            "schema_version": "gtos_vnext_entry_offset_050r_cluster_guard_runtime_row_v1",
            "row_key": row_id,
            "entry_offset_050r_cluster_guard_runtime_row_id": row_id,
            "source_name": "gtos_vnext_entry_offset_050r_cluster_guard_wave",
            "evidence_family": "gtos_vnext_entry_offset_050r_cluster_guard",
            "source_group": self.source_group,
            "source_role": self.source_role,
            "system_surface": "nofill_pending_execution_behavior",
            "runtime_effect_now": {
                "FOLLOW": "entry_offset_050r_cluster_guarded_follow_context",
                "AVOID": "entry_offset_050r_pending_offset_avoid_guard",
            }.get(self.decision, "entry_offset_050r_source_or_owner_reference_context"),
            "implementation_action": self.implementation_action,
            "action_class": self.action_class,
            "r_evidence_class": {
                "FOLLOW": "ENTRY_OFFSET_050R_CLUSTER_GUARDED_POSITIVE_PROXY",
                "AVOID": "ENTRY_OFFSET_050R_NO_FILL_PENDING_OFFSET_AVOID",
            }.get(self.decision, "ENTRY_OFFSET_050R_SOURCE_REQUIREMENT_OR_REFERENCE_CONTEXT"),
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
            "entry_variant": self.entry_variant,
            "proxy_r_class": self.proxy_r_class,
            "target_stop_order_class": self.target_stop_order_class,
            "source_path": self.source_path,
            "drill_through_path": self.source_path,
            "source_artifact_hash_sha256": self.source_hash,
            "source_rows_represented": self.rows,
            "source_row_ids_sample": self.row_ids_sample,
            "entry_offset_cluster_key_counts": dict(sorted(self.cluster_keys.items())),
            "source_bound": source_bound,
            "source_complete": self.decision in {"FOLLOW", "AVOID"},
            "runtime_candidate_use_permitted": self.decision in {"FOLLOW", "AVOID"},
            "candidate_use_allowed_now": self.decision in {"FOLLOW", "AVOID"},
            "r_metrics": metrics,
            "event_scope": scope,
        }


def _source_group(path: Path) -> str:
    name = path.name
    for prefix in ("MAIN_ORCH24_",):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_2026-05-17.json",
        "_2026-05-16.json",
        ".jsonl",
        ".json",
        ".py",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, ...], Group] = {}
    source_stats: list[dict[str, Any]] = []
    target_runtime_rows_read = 0
    for name in SOURCE_NAMES:
        path = SOURCE_DIR / name
        if not path.exists():
            source_stats.append(
                {
                    "exists": False,
                    "path": _path_text(path),
                    "rows": None,
                    "runtime_rows_read": 0,
                    "sha256_or_git_blob": "",
                    "suffix": path.suffix.lower(),
                }
            )
            continue
        path_text = _path_text(path)
        source_hash = _sha256_file(path)
        rows = _source_rows(path)
        target_runtime_rows_read += len(rows)
        source_stats.append(
            {
                "exists": True,
                "path": path_text,
                "rows": _count_rows(path),
                "runtime_rows_read": len(rows),
                "sha256_or_git_blob": source_hash,
                "suffix": path.suffix.lower(),
            }
        )
        for row in rows:
            decision = _decision(row)
            component = _source_component(row, decision)
            symbol = _symbol(row)
            source_symbol = _norm(row.get("source_symbol")) or symbol
            side = _norm(row.get("side")).upper()
            route_session = _route_session(row)
            key = (
                path_text,
                source_hash,
                _source_group(path),
                _source_role(row, decision),
                symbol,
                source_symbol,
                resolve_vnext_symbol_family(symbol) if symbol else "",
                "M15",
                route_session,
                side,
                "entry_offset_050r",
                component,
                decision,
                _action_class(row, decision, component),
                _target_stop_order_class(decision),
                _proxy_r_class(decision),
                _implementation_action(decision, component),
            )
            if not (symbol or side or route_session):
                continue
            group = groups.get(key)
            if group is None:
                group = Group(*key)
                groups[key] = group
            group.add(row)

    rows = [group.to_row() for group in groups.values()]
    rows.sort(key=lambda row: row["row_key"])
    counted_source_rows = sum(
        int(stat["rows"]) for stat in source_stats if isinstance(stat.get("rows"), int)
    )
    runtime_source_rows = sum(int(row["source_rows_represented"]) for row in rows)
    blank_anchor_counts = {
        field: sum(1 for row in rows if not row.get(field))
        for field in ("symbol", "route_session", "side", "entry_variant")
    }
    blank_anchor_counts = {key: value for key, value in blank_anchor_counts.items() if value}
    summary = {
        "schema_version": "gtos_vnext_entry_offset_050r_cluster_guard_runtime_summary_v1",
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": runtime_source_rows,
        "target_runtime_rows_read": target_runtime_rows_read,
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
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "target_stop_order_class_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows).items())
        ),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "market_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "timeframe_counts": dict(sorted(Counter(row["timeframe"] for row in rows if row.get("timeframe")).items())),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "entry_variant_counts": dict(
            sorted(Counter(row["entry_variant"] for row in rows if row.get("entry_variant")).items())
        ),
        "exit_coverage_counts": dict(
            sorted(Counter(row["target_stop_order_class"] for row in rows if row.get("target_stop_order_class")).items())
        ),
        "blank_anchor_counts": blank_anchor_counts,
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
    printable = dict(summary)
    printable["source_artifacts"] = f"{len(summary['source_artifacts'])} artifacts"
    print(json.dumps(printable, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
