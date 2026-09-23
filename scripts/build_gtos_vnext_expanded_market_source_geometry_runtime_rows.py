#!/usr/bin/env python3
"""Build compact runtime rows for the expanded-market source-geometry wave."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MOONSHOT_ROUTE = Path(
    r"research\science_program_2026_05\06_outcome_testing\weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ACTION_CLASS_PERF_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ALT_SOURCE_SCORE_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_REVIEW_EXECUTION_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_REPAIR_REACH_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_TEMPORAL_ROBUSTNESS_ROW_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_MARKET_TIMEFRAME_SOURCE_COVERAGE_LEDGER_2026-05-17.jsonl",
)

REPO_SOURCE_PATHS = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
    / "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_LEDGER_2026-05-18.jsonl",
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
    / "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_LEAKAGE_INTAKE_LEDGER_2026-05-18.jsonl",
)

SOURCE_COMPONENT_BY_STATUS = {
    "OHLC_CSV_REACHABLE": "expanded_market_ohlc_source_reachable",
    "NO_ALTERNATE_LOCAL_OHLC_SOURCE_FOR_SYMBOL_TIMEFRAME": "expanded_market_source_gap",
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


def _source_group(path: Path) -> str:
    name = path.name
    for prefix in (
        "HISTORICAL_OHLC_GTOS_REPLAY_",
        "MAIN_ORCH48_MOONSHOT_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-18.jsonl",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def _row_id(row: dict[str, Any]) -> str:
    for key in (
        "expanded_market_action_class_performance_row_id",
        "expanded_market_alternate_source_scoring_row_id",
        "final_branch_artifact_row_id",
        "final_review_row_id",
        "intrabar_geometry_row_id",
        "expanded_market_performance_row_id",
        "expanded_market_side_pair_robustness_row_id",
        "expanded_market_source_consensus_robustness_row_id",
        "expanded_market_source_expansion_action_application_row_id",
        "expanded_market_source_expansion_action_execution_row_id",
        "expanded_market_source_expansion_discovered_source_row_id",
        "expanded_market_source_expansion_gap_row_id",
        "expanded_market_source_repair_reachability_row_id",
        "expanded_market_supplemental_performance_row_id",
        "temporal_robustness_row_id",
        "frozen_market_timeframe_source_coverage_row_id",
        "final_review_overlay_row_id",
        "main_candidate_row_id",
        "source_final_review_row_id",
        "intake_row_id",
        "source_leakage_reduction_row_id",
        "vnext_matrix_row_id",
        "row_key",
    ):
        value = _norm(row.get(key))
        if value:
            return value
    return ""


def _source_component(row: dict[str, Any]) -> str:
    value = _norm(row.get("source_component"))
    if value:
        return value
    status = _norm(row.get("source_access_status"))
    if status in SOURCE_COMPONENT_BY_STATUS:
        return SOURCE_COMPONENT_BY_STATUS[status]
    value = _norm(row.get("performance_source_family") or row.get("branch_family"))
    if value:
        return value
    return "expanded_market_source_geometry"


def _side(row: dict[str, Any]) -> str:
    return _norm(
        row.get("side")
        or row.get("selected_side")
        or row.get("overall_winner_side")
        or row.get("winner_side")
    )


def _decision(row: dict[str, Any]) -> str:
    action_text = " ".join(
        _norm(row.get(key)).upper()
        for key in (
            "action_class",
            "follow_inverse_default_off_avoid_class",
            "keep_kill_redesign_implement_decision",
            "source_expansion_gap_status",
            "source_access_status",
            "latest_disposition",
            "action_application_status",
            "action_execution_status",
            "final_review_evidence_status",
            "main_compiler_action",
            "main_compiler_final_review_action",
            "source_decision",
            "source_final_review_decision",
            "branch_local_candidate_status_after_final_review",
        )
        if _norm(row.get(key))
    )
    if "AVOID" in action_text or "NEGATIVE" in action_text or "KILL" in action_text:
        return "AVOID"
    if "FOLLOW" in action_text or "IMPLEMENT" in action_text or "POSITIVE" in action_text:
        return "FOLLOW"
    if any(token in action_text for token in ("REPAIR", "REDESIGN", "GAP", "MISSING")):
        return "MIXED"

    value = (
        row.get("cost_adjusted_simulated_r")
        if row.get("cost_adjusted_simulated_r") is not None
        else row.get("observed_cost_adjusted_simulated_r")
    )
    if value is None:
        value = row.get("overall_winner_cost_adjusted_simulated_r")
    metric = _to_float(value)
    if metric is None:
        return "MIXED"
    if metric > 0:
        return "FOLLOW"
    if metric < 0:
        return "AVOID"
    return "MIXED"


def _metric_value(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _effective_n(row: dict[str, Any]) -> float:
    value = _metric_value(
        row,
        "effective_n",
        "effective_n_sum",
        "matched_effective_n_sum",
        "row_count",
        "parsed_ohlc_rows",
    )
    return value if value is not None else 1.0


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
        "source_shape": "expanded_market_source_geometry_compact_scope",
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
    decision: str
    rows: int = 0
    effective_n_sum: float = 0.0
    cost_sum: float = 0.0
    cost_count: float = 0.0
    cost_positive: int = 0
    cost_negative: int = 0
    cost_zero: int = 0
    stress_sum: float = 0.0
    stress_count: float = 0.0
    stress_positive: int = 0
    stress_negative: int = 0
    stress_zero: int = 0
    row_ids_sample: list[str] = field(default_factory=list)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.effective_n_sum += _effective_n(row)
        if row_id := _row_id(row):
            if len(self.row_ids_sample) < 3:
                self.row_ids_sample.append(row_id)
        cost = _metric_value(
            row,
            "cost_adjusted_simulated_r",
            "observed_cost_adjusted_simulated_r",
            "overall_winner_cost_adjusted_simulated_r",
        )
        if cost is not None:
            self.cost_sum += cost
            self.cost_count += 1.0
            self.cost_positive += int(cost > 0)
            self.cost_negative += int(cost < 0)
            self.cost_zero += int(cost == 0)
        stress = _metric_value(
            row,
            "stress_simulated_r",
            "observed_stress_simulated_r",
            "overall_winner_stress_simulated_r",
        )
        if stress is not None:
            self.stress_sum += stress
            self.stress_count += 1.0
            self.stress_positive += int(stress > 0)
            self.stress_negative += int(stress < 0)
            self.stress_zero += int(stress == 0)

    def to_row(self) -> dict[str, Any]:
        action_class = {
            "FOLLOW": "expanded_market_source_geometry_follow_scorer",
            "AVOID": "expanded_market_source_geometry_avoid_filter",
        }.get(self.decision, "expanded_market_source_geometry_context_guard")
        implementation_action = {
            "FOLLOW": "EXPANDED_MARKET_SOURCE_GEOMETRY_FOLLOW_SCORER",
            "AVOID": "EXPANDED_MARKET_SOURCE_GEOMETRY_AVOID_FILTER",
        }.get(self.decision, "EXPANDED_MARKET_SOURCE_GEOMETRY_CONTEXT_GUARD")
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
            ]
        )
        row_id = f"expanded_market_source_geometry:{_sha256_text(key_payload)[:24]}"
        scope = {
            key: value
            for key, value in {
                "symbol": self.symbol,
                "source_symbol": self.source_symbol,
                "symbol_family": self.symbol_family,
                "market_timeframe": self.market_timeframe,
                "timeframe": self.market_timeframe,
                "route_session": self.route_session,
                "side": self.side,
                "horizon_id": self.horizon_id,
                "source_component": self.source_component,
                "route_family": "nofill_mechanical"
                if self.source_component.startswith("nofill_")
                else "moonshot_mechanical",
                "action_class": action_class,
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
                "expanded_market_source_geometry_effective_n",
            )
        }
        if self.cost_count:
            metrics["cost_adjusted_simulated_r"] = _metric_trace(
                self.cost_sum,
                self.cost_count,
                self.cost_positive,
                self.cost_negative,
                self.cost_zero,
                "expanded_market_source_geometry_cost_adjusted_simulated_r",
            )
        if self.stress_count:
            metrics["stress_simulated_r"] = _metric_trace(
                self.stress_sum,
                self.stress_count,
                self.stress_positive,
                self.stress_negative,
                self.stress_zero,
                "expanded_market_source_geometry_stress_simulated_r",
            )
        return {
            "schema_version": "gtos_vnext_expanded_market_source_geometry_runtime_row_v1",
            "row_key": row_id,
            "source_geometry_runtime_row_id": row_id,
            "source_name": "moonshot_expanded_market_source_geometry",
            "evidence_family": "expanded_market_source_geometry",
            "source_group": self.source_group,
            "source_role": "expanded_market_source_geometry_runtime_rollup",
            "system_surface": "expanded_market_source_geometry_router",
            "runtime_effect_now": {
                "FOLLOW": "expanded_market_source_geometry_follow_pressure",
                "AVOID": "expanded_market_source_geometry_avoid_filter",
            }.get(self.decision, "expanded_market_source_geometry_context_guard"),
            "implementation_action": implementation_action,
            "action_class": action_class,
            "r_evidence_class": {
                "FOLLOW": "EXPANDED_MARKET_SOURCE_GEOMETRY_POSITIVE_PROXY",
                "AVOID": "EXPANDED_MARKET_SOURCE_GEOMETRY_NEGATIVE_PROXY",
            }.get(self.decision, "EXPANDED_MARKET_SOURCE_GEOMETRY_CONTEXT_OR_REPAIR"),
            "decision": self.decision,
            "source_component": self.source_component,
            "route_family": scope.get("route_family"),
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
            "source_bound": bool(
                (self.symbol or self.source_symbol or self.symbol_family)
                and self.market_timeframe
                and self.source_component
            ),
            "source_complete": self.decision in {"FOLLOW", "AVOID"},
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "r_metrics": metrics,
        }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, ...], Group] = {}
    source_stats: list[dict[str, Any]] = []
    for path in [*(MOONSHOT_ROUTE / name for name in SOURCE_NAMES), *REPO_SOURCE_PATHS]:
        if not path.exists():
            source_stats.append({"path": str(path), "exists": False, "rows": 0})
            continue
        source_hash = _sha256_file(path)
        source_group = _source_group(path)
        row_count = 0
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    continue
                row_count += 1
                symbol = _norm(row.get("symbol") or row.get("source_symbol"))
                source_symbol = _norm(row.get("source_symbol") or row.get("symbol"))
                key = (
                    str(path),
                    source_hash,
                    source_group,
                    symbol,
                    source_symbol,
                    _norm(row.get("symbol_family")),
                    _norm(row.get("market_timeframe") or row.get("source_timeframe")),
                    _norm(row.get("route_session")),
                    _side(row),
                    _norm(row.get("horizon_id")),
                    _source_component(row),
                    _decision(row),
                )
                group = groups.get(key)
                if group is None:
                    group = Group(*key)
                    groups[key] = group
                group.add(row)
        source_stats.append({
            "path": str(path),
            "exists": True,
            "rows": row_count,
            "sha256": source_hash,
        })
    rows = [group.to_row() for group in groups.values()]
    rows.sort(key=lambda row: row["row_key"])
    decision_counts = Counter(row["decision"] for row in rows)
    source_group_counts = Counter(row["source_group"] for row in rows)
    component_counts = Counter(row["source_component"] for row in rows)
    represented_rows = sum(int(row["source_rows_represented"]) for row in rows)
    summary = {
        "schema_version": "gtos_vnext_expanded_market_source_geometry_runtime_summary_v1",
        "runtime_row_count": len(rows),
        "source_rows_represented": represented_rows,
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_group_counts": dict(sorted(source_group_counts.items())),
        "source_component_counts": dict(sorted(component_counts.items())),
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
        OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
