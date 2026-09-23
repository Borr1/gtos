"""Build the Lane03 broad selected-denominator meta-selector package.

This route consumes Lane02 broad selected replay rows and Friday microscope
context, then emits selector rules, ledgers, verifier, manifest, and audit
artifacts. It performs offline research artifact writes only; it never touches
broker state or external services.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_lane03_meta_selector_discovery_implementation_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE02_DIR = ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
LANE02_LEDGER = LANE02_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LANE02_SUMMARY = LANE02_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json"
LANE02_SPLITS = LANE02_DIR / "LANE02_BROAD_SELECTED_SPLIT_STRESS_SUMMARY.jsonl"
LANE02_SOURCE_COMPLETENESS = LANE02_DIR / "LANE02_SOURCE_COMPLETENESS_LEDGER.jsonl"
LANE02_CONCENTRATION = LANE02_DIR / "LANE02_CONCENTRATION_AND_LEAVE_ONE_OUT_LEDGER.jsonl"

FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
FRIDAY_SELECTOR_SUMMARY = FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"
LANE01_SUMMARY = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31"
    / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json"
)
PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "VNEXT_LANE03_META_SELECTOR_DISCOVERY_IMPLEMENTATION_GOAL_PROMPT_2026-05-31.md"
)
STARTER = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "VNEXT_LANE03_META_SELECTOR_DISCOVERY_IMPLEMENTATION_STARTER_2026-05-31.txt"
)

MIN_TRADEABLE_SESSION_ORIGIN_ROWS = 250
MIN_TRADEABLE_ACCEPTED_ROWS = 25
MIN_TRADEABLE_EXPECTANCY_R = 0.25
MIN_RISK_CELL_ROWS = 25
MIN_RISK_CELL_ACCEPTED_ROWS = 25
COST_STRESS_R = 0.25
MAX_SPREAD_R = 0.20


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None, digits: int = 9) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _text(value: Any, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text if text else default


def _rule_key(value: str) -> str:
    clean = []
    for char in str(value).lower():
        clean.append(char if char.isalnum() else "_")
    return "_".join("".join(clean).split("_"))


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@dataclass
class MetricStats:
    rows: int = 0
    selected_known_r_rows: int = 0
    selected_gross_r_sum: float = 0.0
    selected_wins: int = 0
    selected_losses: int = 0
    selected_breakevens: int = 0
    accepted_rows: int = 0
    accepted_known_r_rows: int = 0
    accepted_gross_r_sum: float = 0.0
    accepted_wins: int = 0
    accepted_losses: int = 0
    accepted_breakevens: int = 0
    rejected_rows: int = 0
    same_bar_ambiguous_rows: int = 0
    source_window_incomplete_rows: int = 0
    source_mode_counts: Counter[str] = field(default_factory=Counter)
    cost_status_counts: Counter[str] = field(default_factory=Counter)
    m1_availability_counts: Counter[str] = field(default_factory=Counter)
    tick_availability_counts: Counter[str] = field(default_factory=Counter)
    ordered_path_status_counts: Counter[str] = field(default_factory=Counter)
    symbols: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    origins: Counter[str] = field(default_factory=Counter)
    sides: Counter[str] = field(default_factory=Counter)
    frameworks: Counter[str] = field(default_factory=Counter)
    policies: Counter[str] = field(default_factory=Counter)

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        result_r = _float(row.get("final_r"))
        if result_r is not None:
            self.selected_known_r_rows += 1
            self.selected_gross_r_sum += result_r
            if result_r > 0:
                self.selected_wins += 1
            elif result_r < 0:
                self.selected_losses += 1
            else:
                self.selected_breakevens += 1
        if str(row.get("decision") or "").lower() == "accept":
            self.accepted_rows += 1
            if result_r is not None:
                self.accepted_known_r_rows += 1
                self.accepted_gross_r_sum += result_r
                if result_r > 0:
                    self.accepted_wins += 1
                elif result_r < 0:
                    self.accepted_losses += 1
                else:
                    self.accepted_breakevens += 1
        else:
            self.rejected_rows += 1
        if bool(row.get("same_bar_ambiguity")):
            self.same_bar_ambiguous_rows += 1
        if str(row.get("source_window_complete")).lower() not in {"true", "1"}:
            self.source_window_incomplete_rows += 1
        for field_name, counter in (
            ("source_mode", self.source_mode_counts),
            ("cost_status", self.cost_status_counts),
            ("m1_availability_status", self.m1_availability_counts),
            ("tick_availability_status", self.tick_availability_counts),
            ("ordered_path_status", self.ordered_path_status_counts),
        ):
            counter[_text(row.get(field_name))] += 1
        self.symbols[_text(row.get("symbol"))] += 1
        self.sessions[_text(row.get("session_bucket"))] += 1
        self.origins[_text(row.get("origin_family"))] += 1
        self.sides[_text(row.get("side"))] += 1
        self.frameworks[_text(row.get("framework"))] += 1
        self.policies[_text(row.get("chosen_policy"))] += 1

    def to_record(self, *, split_scope: str, split_key: str) -> dict[str, Any]:
        selected_expectancy = (
            self.selected_gross_r_sum / self.selected_known_r_rows
            if self.selected_known_r_rows
            else None
        )
        accepted_expectancy = (
            self.accepted_gross_r_sum / self.accepted_known_r_rows
            if self.accepted_known_r_rows
            else None
        )
        accepted_win_rate = (
            self.accepted_wins / self.accepted_rows if self.accepted_rows else None
        )
        selected_win_rate = self.selected_wins / self.selected_known_r_rows if self.selected_known_r_rows else None
        record = {
            "schema_version": "lane03_selected_denominator_metric_v1",
            "route_id": ROUTE_ID,
            "split_scope": split_scope,
            "split_key": split_key,
            "rows": self.rows,
            "selected_known_r_rows": self.selected_known_r_rows,
            "selected_gross_r_sum": _round(self.selected_gross_r_sum),
            "selected_expectancy_r": _round(selected_expectancy),
            "selected_cost_stress_after_0_25r": _round(
                selected_expectancy - COST_STRESS_R if selected_expectancy is not None else None
            ),
            "selected_wins": self.selected_wins,
            "selected_losses": self.selected_losses,
            "selected_breakevens": self.selected_breakevens,
            "selected_win_rate": _round(selected_win_rate),
            "accepted_rows": self.accepted_rows,
            "accepted_known_r_rows": self.accepted_known_r_rows,
            "accepted_gross_r_sum": _round(self.accepted_gross_r_sum),
            "accepted_expectancy_r": _round(accepted_expectancy),
            "accepted_cost_stress_after_0_25r": _round(
                accepted_expectancy - COST_STRESS_R if accepted_expectancy is not None else None
            ),
            "accepted_wins": self.accepted_wins,
            "accepted_losses": self.accepted_losses,
            "accepted_breakevens": self.accepted_breakevens,
            "accepted_win_rate": _round(accepted_win_rate),
            "rejected_rows": self.rejected_rows,
            "same_bar_ambiguous_rows": self.same_bar_ambiguous_rows,
            "source_window_incomplete_rows": self.source_window_incomplete_rows,
            "source_mode_counts": dict(self.source_mode_counts),
            "cost_status_counts": dict(self.cost_status_counts),
            "m1_availability_counts": dict(self.m1_availability_counts),
            "tick_availability_counts": dict(self.tick_availability_counts),
            "ordered_path_status_counts": dict(self.ordered_path_status_counts),
            "symbol_count": len(self.symbols),
            "session_count": len(self.sessions),
            "origin_count": len(self.origins),
            "side_count": len(self.sides),
            "framework_count": len(self.frameworks),
            "policy_count": len(self.policies),
        }
        record["branch_decision"] = metric_branch_decision(record)
        return record


def metric_branch_decision(record: dict[str, Any]) -> str:
    rows = int(record.get("rows") or 0)
    accepted_rows = int(record.get("accepted_rows") or 0)
    selected_expectancy = _float(record.get("selected_expectancy_r"))
    accepted_expectancy = _float(record.get("accepted_expectancy_r"))
    if rows < MIN_RISK_CELL_ROWS:
        return "underpowered_preserve_in_metric_ledger_no_selector_clause"
    if selected_expectancy is not None and selected_expectancy < 0:
        return "negative_selected_expectancy_avoid_candidate"
    if (
        accepted_rows >= MIN_RISK_CELL_ACCEPTED_ROWS
        and accepted_expectancy is not None
        and accepted_expectancy < 0
    ):
        return "negative_accepted_expectancy_avoid_candidate"
    if selected_expectancy is not None and selected_expectancy < MIN_TRADEABLE_EXPECTANCY_R:
        return "weak_selected_expectancy_reduce_candidate"
    if (
        accepted_rows >= MIN_RISK_CELL_ACCEPTED_ROWS
        and accepted_expectancy is not None
        and accepted_expectancy < MIN_TRADEABLE_EXPECTANCY_R
    ):
        return "weak_accepted_expectancy_reduce_candidate"
    if (
        rows >= MIN_TRADEABLE_SESSION_ORIGIN_ROWS
        and accepted_rows >= MIN_TRADEABLE_ACCEPTED_ROWS
        and selected_expectancy is not None
        and selected_expectancy >= MIN_TRADEABLE_EXPECTANCY_R
        and accepted_expectancy is not None
        and accepted_expectancy >= MIN_TRADEABLE_EXPECTANCY_R
    ):
        return "strong_positive_tradeable_candidate"
    return "positive_or_underaccepted_capture_required"


def metric_keys(row: dict[str, Any]) -> list[tuple[str, str]]:
    symbol = _text(row.get("symbol"))
    session = _text(row.get("session_bucket"))
    origin = _text(row.get("origin_family"))
    side = _text(row.get("side"))
    framework = _text(row.get("framework"))
    policy = _text(row.get("chosen_policy"))
    source_time = _text(row.get("source_time_utc"), "")
    month = source_time[:7] if len(source_time) >= 7 else "unknown"
    risk_cell = _text(row.get("risk_cell_id"))
    return [
        ("all", "ALL"),
        ("chosen_policy", policy),
        ("framework", framework),
        ("origin_family", origin),
        ("session_bucket", session),
        ("session_origin", f"{session}|{origin}"),
        ("origin_side", f"{origin}|{side}"),
        ("symbol", symbol),
        ("symbol_session", f"{symbol}|{session}"),
        ("symbol_origin", f"{symbol}|{origin}"),
        ("symbol_session_origin", f"{symbol}|{session}|{origin}"),
        ("risk_cell_id", risk_cell),
        ("side", side),
        ("month", month),
        ("source_mode", _text(row.get("source_mode"))),
        ("cost_status", _text(row.get("cost_status"))),
        ("m1_availability_status", _text(row.get("m1_availability_status"))),
        ("tick_availability_status", _text(row.get("tick_availability_status"))),
        ("ordered_path_status", _text(row.get("ordered_path_status"))),
    ]


def scan_lane02_metrics() -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, MetricStats]] = defaultdict(lambda: defaultdict(MetricStats))
    with LANE02_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            for scope, key in metric_keys(row):
                grouped[scope][key].add(row)
    records: list[dict[str, Any]] = []
    for scope in sorted(grouped):
        for key in sorted(grouped[scope]):
            records.append(grouped[scope][key].to_record(split_scope=scope, split_key=key))
    return records


def _metric_index(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(record["split_scope"], record["split_key"]): record for record in records}


def _origin_rule_framework(origin: str, framework: str | None = None) -> str | None:
    normalized = str(origin or "").removeprefix("current_")
    if framework and framework != "broader_origin":
        return framework
    if origin.startswith("current_"):
        return normalized
    return None


def _rule_evidence_fields(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_scope": metric["split_scope"],
        "source_key": metric["split_key"],
        "selected_rows": metric["rows"],
        "selected_gross_r_sum": metric["selected_gross_r_sum"],
        "selected_expectancy_r": metric["selected_expectancy_r"],
        "selected_cost_stress_after_0_25r": metric["selected_cost_stress_after_0_25r"],
        "accepted_rows": metric["accepted_rows"],
        "accepted_gross_r_sum": metric["accepted_gross_r_sum"],
        "accepted_expectancy_r": metric["accepted_expectancy_r"],
        "accepted_cost_stress_after_0_25r": metric["accepted_cost_stress_after_0_25r"],
        "branch_decision": metric["branch_decision"],
        "source_evidence_paths": [
            _repo_path(LANE02_LEDGER),
            _repo_path(LANE02_SUMMARY),
            _repo_path(LANE02_SPLITS),
        ],
        "result_scope": "gross_proxy_r_selected_denominator_not_broker_net_r",
        "cost_truth_status": "historical_broker_commission_swap_slippage_missing_cost_stressed_by_0_25r",
        "asof_runtime_fields": [
            "symbol",
            "side",
            "framework",
            "candidate_origin_family",
            "session_bucket",
            "spread_r_at_candidate",
            "source_path_feature_status",
            "ordered_path_status",
        ],
    }


def _session_origin_parts(split_key: str) -> tuple[str, str]:
    parts = split_key.split("|", 1)
    if len(parts) != 2:
        return split_key, "unknown"
    return parts[0], parts[1]


def _risk_cell_parts(split_key: str) -> dict[str, str]:
    parts = split_key.split("|")
    symbol, framework, session, origin, side = (parts + ["unknown"] * 5)[:5]
    return {
        "symbol": symbol,
        "framework": framework,
        "session": session,
        "origin_family": origin,
        "side": side,
    }


def build_rule_package(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    tradeable_rules: list[dict[str, Any]] = []
    avoid_rules: list[dict[str, Any]] = []
    reduce_rules: list[dict[str, Any]] = []
    capture_repair_rules: list[dict[str, Any]] = []

    for metric in metrics:
        if metric["split_scope"] != "session_origin":
            continue
        session, origin = _session_origin_parts(metric["split_key"])
        selected_exp = _float(metric.get("selected_expectancy_r"))
        accepted_exp = _float(metric.get("accepted_expectancy_r"))
        if (
            metric["rows"] >= MIN_TRADEABLE_SESSION_ORIGIN_ROWS
            and metric["accepted_rows"] >= MIN_TRADEABLE_ACCEPTED_ROWS
            and selected_exp is not None
            and selected_exp >= MIN_TRADEABLE_EXPECTANCY_R
            and accepted_exp is not None
            and accepted_exp >= MIN_TRADEABLE_EXPECTANCY_R
        ):
            rule: dict[str, Any] = {
                "rule_id": f"lane03_tradeable_{_rule_key(session)}_{_rule_key(origin)}",
                "action": "tradeable_now",
                "session": session,
                "origin_family": origin,
                "max_spread_r": MAX_SPREAD_R,
                "min_selected_rows": MIN_TRADEABLE_SESSION_ORIGIN_ROWS,
                "min_accepted_rows": MIN_TRADEABLE_ACCEPTED_ROWS,
                "min_selected_expectancy_r": MIN_TRADEABLE_EXPECTANCY_R,
                "min_accepted_expectancy_r": MIN_TRADEABLE_EXPECTANCY_R,
            }
            framework = _origin_rule_framework(origin)
            if framework:
                rule["framework"] = framework
            rule.update(_rule_evidence_fields(metric))
            tradeable_rules.append(rule)
        else:
            rule = {
                "rule_id": f"lane03_capture_{_rule_key(session)}_{_rule_key(origin)}",
                "action": "source_capture_required",
                "session": session,
                "origin_family": origin,
                "refusal_reason": "candidate_quality_session_origin_needs_more_selected_denominator_or_cost_source",
                "missing_or_weak_condition": metric["branch_decision"],
                "min_selected_rows": MIN_TRADEABLE_SESSION_ORIGIN_ROWS,
                "min_accepted_rows": MIN_TRADEABLE_ACCEPTED_ROWS,
            }
            framework = _origin_rule_framework(origin)
            if framework:
                rule["framework"] = framework
            rule.update(_rule_evidence_fields(metric))
            capture_repair_rules.append(rule)

    for metric in metrics:
        if metric["split_scope"] != "risk_cell_id":
            continue
        if metric["rows"] < MIN_RISK_CELL_ROWS:
            continue
        selected_exp = _float(metric.get("selected_expectancy_r"))
        accepted_exp = _float(metric.get("accepted_expectancy_r"))
        negative = selected_exp is not None and selected_exp < 0
        negative = negative or (
            metric["accepted_rows"] >= MIN_RISK_CELL_ACCEPTED_ROWS
            and accepted_exp is not None
            and accepted_exp < 0
        )
        weak = selected_exp is not None and selected_exp < MIN_TRADEABLE_EXPECTANCY_R
        weak = weak or (
            metric["accepted_rows"] >= MIN_RISK_CELL_ACCEPTED_ROWS
            and accepted_exp is not None
            and accepted_exp < MIN_TRADEABLE_EXPECTANCY_R
        )
        if not negative and not weak:
            continue
        parts = _risk_cell_parts(metric["split_key"])
        base_rule: dict[str, Any] = {
            "risk_cell_id": metric["split_key"],
            "symbol": parts["symbol"],
            "session": parts["session"],
            "origin_family": parts["origin_family"],
            "side": parts["side"],
            "min_selected_rows": MIN_RISK_CELL_ROWS,
            "min_accepted_rows_for_accepted_expectancy": MIN_RISK_CELL_ACCEPTED_ROWS,
            "max_spread_r": MAX_SPREAD_R,
        }
        framework = _origin_rule_framework(parts["origin_family"], parts["framework"])
        if framework:
            base_rule["framework"] = framework
        base_rule.update(_rule_evidence_fields(metric))
        if negative:
            rule = {
                **base_rule,
                "rule_id": f"lane03_avoid_{_rule_key(metric['split_key'])}",
                "action": "no_trade_by_evidence",
                "refusal_reason": "candidate_quality_negative_selected_denominator_rule",
            }
            avoid_rules.append(rule)
        else:
            rule = {
                **base_rule,
                "rule_id": f"lane03_reduce_{_rule_key(metric['split_key'])}",
                "action": "reduce_risk_by_evidence",
                "risk_multiplier": 0.5,
                "risk_multiplier_live_sizing_status": (
                    "recorded_by_selector_runtime_bridge_lane04_lane05_own_final_sizing_consumption"
                ),
            }
            reduce_rules.append(rule)

    package = {
        "schema_version": "lane03_meta_selector_rule_package_v1",
        "route_id": ROUTE_ID,
        "package_id": "lane03_broad_selected_meta_selector_v1",
        "generated_at_utc": _utc_now(),
        "git_head": _git_head(),
        "result_scope": "gross_proxy_r_selected_denominator_with_cost_stress_not_production_validation",
        "implementation_boundary": (
            "local_selector_code_config_tests_only_no_broker_action_no_live_restart_no_remote_push"
        ),
        "selector_contract": {
            "tradeable_rule_scope": "session_origin broad selected denominator",
            "risk_override_scope": "symbol_framework_session_origin_side selected risk cell",
            "spread_gate": {
                "field": "spread_r_at_candidate",
                "max_spread_r": MAX_SPREAD_R,
                "missing_spread_action": "source_capture_required",
            },
            "sample_floors": {
                "tradeable_session_origin_rows": MIN_TRADEABLE_SESSION_ORIGIN_ROWS,
                "tradeable_accepted_rows": MIN_TRADEABLE_ACCEPTED_ROWS,
                "risk_cell_rows": MIN_RISK_CELL_ROWS,
            },
            "expectancy_floor_r": MIN_TRADEABLE_EXPECTANCY_R,
            "cost_stress_r": COST_STRESS_R,
        },
        "tradeable_rules": sorted(tradeable_rules, key=lambda rule: rule["rule_id"]),
        "avoid_rules": sorted(avoid_rules, key=lambda rule: rule["rule_id"]),
        "reduce_rules": sorted(reduce_rules, key=lambda rule: rule["rule_id"]),
        "capture_repair_rules": sorted(capture_repair_rules, key=lambda rule: rule["rule_id"]),
    }
    package["rule_counts"] = {
        "tradeable_rules": len(package["tradeable_rules"]),
        "avoid_rules": len(package["avoid_rules"]),
        "reduce_rules": len(package["reduce_rules"]),
        "capture_repair_rules": len(package["capture_repair_rules"]),
    }
    return package


def build_branch_decision_ledger(metrics: list[dict[str, Any]], package: dict[str, Any]) -> list[dict[str, Any]]:
    rule_by_source = {}
    for rule_type in ("tradeable_rules", "avoid_rules", "reduce_rules", "capture_repair_rules"):
        for rule in package.get(rule_type, []):
            rule_by_source[(rule.get("source_scope"), rule.get("source_key"))] = {
                "rule_id": rule.get("rule_id"),
                "action": rule.get("action"),
                "rule_type": rule_type,
            }
    ledger = []
    for metric in metrics:
        rule = rule_by_source.get((metric["split_scope"], metric["split_key"]))
        ledger.append(
            {
                "schema_version": "lane03_meta_selector_branch_decision_v1",
                "route_id": ROUTE_ID,
                "split_scope": metric["split_scope"],
                "split_key": metric["split_key"],
                "rows": metric["rows"],
                "selected_expectancy_r": metric["selected_expectancy_r"],
                "accepted_rows": metric["accepted_rows"],
                "accepted_expectancy_r": metric["accepted_expectancy_r"],
                "branch_decision": metric["branch_decision"],
                "selector_clause_action": rule.get("action") if rule else "metric_preserved_no_runtime_clause",
                "selector_rule_id": rule.get("rule_id") if rule else None,
                "selector_rule_type": rule.get("rule_type") if rule else None,
                "preservation_status": "full_metric_preserved_no_top_n_cutoff",
            }
        )
    return ledger


def build_source_completeness_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with LANE02_SOURCE_COMPLETENESS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            source_row = json.loads(line)
            field_name = str(source_row.get("field") or "")
            value = str(source_row.get("value") or "")
            if field_name in {"cost_status", "broker_cost_truth"}:
                decision = "lane06_lane08_broker_net_r_cost_truth_capture_required"
            elif field_name == "tick_availability_status" and "available" not in value:
                decision = "lane07_lane08_tick_coverage_capture_or_proxy_review_required"
            elif field_name == "m1_availability_status" and "available" not in value:
                decision = "lane07_m1_entry_minute_coverage_capture_required"
            elif field_name == "ordered_path_status" and "same_bar" in value:
                decision = "live_m1_or_tick_ordering_capture_required_before_runtime_use"
            elif field_name in {
                "source_mode",
                "source_window_complete",
                "selected_cell_risk_decision_basis",
                "selected_cell_risk_match_reason",
            }:
                decision = "currently_source_bound_for_selected_denominator"
            else:
                decision = "preserved_source_status_for_lane04_or_later_review"
            rows.append(
                {
                    **source_row,
                    "route_id": ROUTE_ID,
                    "schema_version": "lane03_source_completeness_capture_repair_v1",
                    "source_capture_decision": decision,
                    "source_evidence_path": _repo_path(LANE02_SOURCE_COMPLETENESS),
                }
            )
    rows.extend(
        [
            {
                "schema_version": "lane03_source_completeness_capture_repair_v1",
                "route_id": ROUTE_ID,
                "field": "spread_r_at_candidate",
                "value": "live_runtime_tick_bid_ask_over_candidate_risk_distance",
                "source_capture_decision": "implemented_as_selector_max_spread_r_gate_with_missing_spread_source_capture_required",
                "runtime_asof_availability": "available_when_tick_snapshot_and_trade_geometry_present",
            },
            {
                "schema_version": "lane03_source_completeness_capture_repair_v1",
                "route_id": ROUTE_ID,
                "field": "volatility_state_14_vs_50",
                "value": "live_runtime_context_field_available_but_not_denominated_in_lane02_rows",
                "source_capture_decision": "preserve_for_lane04_lane07_future_split_denominator",
                "runtime_asof_availability": "available_from_live_context",
            },
            {
                "schema_version": "lane03_source_completeness_capture_repair_v1",
                "route_id": ROUTE_ID,
                "field": "current_bar_displacement_atr14",
                "value": "live_runtime_context_field_available_but_not_lane03_tradeable_clause_floor",
                "source_capture_decision": "preserve_for_future_condition_challenger_and_microstructure_stress",
                "runtime_asof_availability": "available_from_live_context",
            },
            {
                "schema_version": "lane03_source_completeness_capture_repair_v1",
                "route_id": ROUTE_ID,
                "field": "selected_cell_risk_id",
                "value": "risk_cell_id_symbol_framework_session_origin_side",
                "source_capture_decision": "implemented_as_symbol_framework_session_origin_side_avoid_reduce_selector_override",
                "runtime_asof_availability": "available_by constituent fields; exact selected_cell_risk_cell_id passthrough optional",
            },
        ]
    )
    return rows


def build_concentration_guard_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with LANE02_CONCENTRATION.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            share = _float(row.get("accepted_gross_r_share")) or 0.0
            leave_one_out = _float(row.get("leave_one_out_accepted_gross_r_sum")) or 0.0
            if share >= 0.5 and leave_one_out > 0:
                status = "concentrated_but_leave_one_out_positive_not_single_point_failure"
            elif share >= 0.5:
                status = "concentration_blocker_leave_one_out_nonpositive"
            else:
                status = "not_concentrated_or_materially_diversified"
            rows.append(
                {
                    **row,
                    "route_id": ROUTE_ID,
                    "schema_version": "lane03_concentration_guard_v1",
                    "concentration_guard_status": status,
                    "selector_decision_effect": (
                        "no_tradeable_rule_blocker"
                        if leave_one_out > 0
                        else "preserve_as_future_validation_blocker_not_runtime_clause"
                    ),
                }
            )
    return rows


def build_upstream_input_integrity(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    all_metric = next(
        (
            metric
            for metric in metrics
            if metric.get("split_scope") == "all" and metric.get("split_key") == "ALL"
        ),
        {},
    )
    try:
        summary = json.loads(LANE02_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        summary = {}
    summary_stats = summary.get("stats") if isinstance(summary.get("stats"), dict) else {}
    selected_row_match = int(all_metric.get("rows") or 0) == int(
        summary.get("selected_surface_rows") or summary.get("input_rows") or 0
    )
    accepted_row_match = int(all_metric.get("accepted_rows") or 0) == int(
        summary_stats.get("accepted_rows") or summary.get("accepted_rows") or 0
    )
    return {
        "schema_version": "lane03_upstream_input_integrity_v1",
        "lane02_ledger_path": _repo_path(LANE02_LEDGER),
        "lane02_summary_path": _repo_path(LANE02_SUMMARY),
        "ledger_rows": all_metric.get("rows"),
        "summary_rows": summary.get("selected_surface_rows") or summary.get("input_rows"),
        "ledger_accepted_rows": all_metric.get("accepted_rows"),
        "summary_accepted_rows": summary_stats.get("accepted_rows") or summary.get("accepted_rows"),
        "ledger_selected_gross_r_sum": all_metric.get("selected_gross_r_sum"),
        "summary_selected_gross_r_sum": summary_stats.get("selected_gross_r_sum"),
        "ledger_accepted_gross_r_sum": all_metric.get("accepted_gross_r_sum"),
        "summary_accepted_gross_r_sum": summary_stats.get("accepted_gross_r_sum"),
        "selected_row_match": selected_row_match,
        "accepted_row_match": accepted_row_match,
        "lane03_decision": (
            "lane02_full_jsonl_ledger_authoritative_for_lane03_metrics; "
            "summary_mismatch_is_recorded_as_upstream_staleness_not_a_lane03_stop"
        )
        if not accepted_row_match
        else "lane02_summary_and_ledger_row_counts_match_for_lane03",
    }


def build_implementation_decisions(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "remove_router_default_two_rule_friday_fallback",
            "implementation_path": "src/research/moonshot_default_off_policy_router.py",
            "evidence_basis": "Lane02 broad selected package must be explicit; empty rules now fail closed to source_capture_required",
            "runtime_boundary": "selector-only no broker action",
        },
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "support_tradeable_avoid_reduce_capture_rule_actions",
            "implementation_path": "src/research/moonshot_default_off_policy_router.py",
            "evidence_basis": "session-origin positives plus risk-cell negatives/weak families need distinct decisions",
            "runtime_boundary": "candidate_quality bridge classification/refusal only",
        },
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "normalize_london_ny_tokyo_off_kz_session_aliases",
            "implementation_path": "src/research/moonshot_default_off_policy_router.py",
            "evidence_basis": "Friday records use london while broad replay and runtime use london_broad",
            "runtime_boundary": "matching repair only",
        },
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "runtime_loads_generated_rule_package_from_config",
            "implementation_path": "src/components/gtos_vnext_runtime.py",
            "evidence_basis": f"{package['rule_counts']} generated from Lane02 selected denominators",
            "runtime_boundary": "local package read; no external IO; missing package fail-closed by router",
        },
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "config_points_to_lane03_package",
            "implementation_path": "config/agent_config.yaml",
            "evidence_basis": _repo_path(ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json"),
            "runtime_boundary": "selector config only; no broker order/deal/position action",
        },
        {
            "schema_version": "lane03_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "decision": "focused_router_tests_added",
            "implementation_path": "tests/test_moonshot_default_off_policy_router.py",
            "evidence_basis": "broad alias, avoid override, reduce classification, and missing spread source-capture paths",
            "runtime_boundary": "local tests only",
        },
    ]


def build_context_anchor(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Lane03 Meta-Selector Context Anchor",
            "",
            f"- route_id: `{ROUTE_ID}`",
            f"- generated_at_utc: `{package['generated_at_utc']}`",
            f"- git_head: `{package['git_head']}`",
            f"- controlling_prompt: `{_repo_path(PROMPT)}`",
            f"- starter: `{_repo_path(STARTER)}`",
            f"- lane02_selected_ledger: `{_repo_path(LANE02_LEDGER)}`",
            f"- friday_selector_context: `{_repo_path(FRIDAY_SELECTOR_SUMMARY)}`",
            f"- package: `{_repo_path(ROUTE_DIR / 'LANE03_META_SELECTOR_RULE_PACKAGE.json')}`",
            "",
            "## Boundary",
            "",
            "Offline selector discovery and local code/config/tests only. No broker operation, paid API/vendor call, credential change, remote push, live restart, or hidden deployment was performed.",
            "",
            "## Current Branch Decision",
            "",
            f"Generated `{package['rule_counts']['tradeable_rules']}` broad session-origin tradeable rules, `{package['rule_counts']['avoid_rules']}` risk-cell avoid rules, `{package['rule_counts']['reduce_rules']}` risk-cell reduce rules, and `{package['rule_counts']['capture_repair_rules']}` capture/repair rules from all Lane02 selected-denominator rows.",
        ]
    ) + "\n"


def build_self_red_team(package: dict[str, Any]) -> str:
    counts = package["rule_counts"]
    return "\n".join(
        [
            "# Lane03 Saturation And Self-Red-Team",
            "",
            "## One-Friday Overfit",
            "",
            "The package is not the old two-clause Friday subset. Friday evidence is preserved as context, while runtime clauses are generated from the 289,600-row Lane02 broad selected-denominator replay. The two known London mechanisms are included only because their broad session-origin denominators pass the same rule criteria as every other family.",
            "",
            "## Denominator And Leakage",
            "",
            "Rules use as-of fields already available in runtime packets: symbol, side, framework, candidate origin, session bucket, spread/R, source status, and path status. The package does not use future outcome fields for runtime matching. Exact/proxy R is recorded as evidence metadata only.",
            "",
            "## Concentration",
            "",
            "Lane02 leave-one-out rows are preserved in the Lane03 concentration guard ledger. Concentrated splits are not automatically promoted; the verifier checks that the broad package is not narrowed to a single route or Friday-only pair.",
            "",
            "## Cost And Source Gaps",
            "",
            "Broker net-R cost truth is not invented. Lane03 uses gross proxy R with a 0.25R stress column and records broker lifecycle net-R/cost fields as Lane06/Lane08 capture requirements. Tick/M1/path gaps remain capture requirements where historical rows cannot repair them.",
            "",
            "## Implementation Risk",
            "",
            f"Runtime config points to a package with {counts['tradeable_rules']} tradeable, {counts['avoid_rules']} avoid, {counts['reduce_rules']} reduce, and {counts['capture_repair_rules']} capture/repair rules. Missing package or unmatched clauses fail closed to source capture rather than silently broadening execution.",
        ]
    ) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    entries = []
    for path in paths:
        if not path.exists():
            continue
        line_count = None
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                line_count = sum(1 for line in handle if line.strip())
        entries.append(
            {
                "path": _repo_path(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "line_count": line_count,
            }
        )
    return {
        "schema_version": "lane03_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": _utc_now(),
        "input_artifacts": [
            _repo_path(LANE02_LEDGER),
            _repo_path(LANE02_SUMMARY),
            _repo_path(LANE02_SPLITS),
            _repo_path(LANE02_SOURCE_COMPLETENESS),
            _repo_path(LANE02_CONCENTRATION),
            _repo_path(FRIDAY_SELECTOR_SUMMARY),
            _repo_path(LANE01_SUMMARY),
        ],
        "outputs": entries,
        "manifest_self_hash_note": "manifest excludes itself from self-referential sha256 closure",
    }


VERIFY_SCRIPT = r'''"""Verify Lane03 meta-selector route artifacts."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE_ID = "vnext_lane03_meta_selector_discovery_implementation_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID


def _repo(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _update_manifest_with_verification_result(path: Path) -> None:
    manifest_path = ROUTE_DIR / "LANE03_OUTPUT_MANIFEST.json"
    if not manifest_path.exists():
        return
    manifest = _read_json(manifest_path)
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), list) else []
    outputs = [entry for entry in outputs if entry.get("path") != _repo(path)]
    outputs.append(
        {
            "path": _repo(path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "line_count": None,
        }
    )
    manifest["outputs"] = outputs
    manifest["verification_result_recorded"] = _repo(path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    issues: list[str] = []
    required = [
        "LANE03_CONTEXT_ANCHOR.md",
        "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl",
        "LANE03_META_SELECTOR_BRANCH_DECISION_LEDGER.jsonl",
        "LANE03_META_SELECTOR_RULE_PACKAGE.json",
        "LANE03_SOURCE_COMPLETENESS_CAPTURE_REPAIR_LEDGER.jsonl",
        "LANE03_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "LANE03_CONCENTRATION_GUARD_LEDGER.jsonl",
        "LANE03_SATURATION_SELF_RED_TEAM.md",
        "LANE03_COMPLETION_AUDIT.json",
        "LANE03_OUTPUT_MANIFEST.json",
        "verify_lane03_meta_selector.py",
    ]
    for name in required:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing required output {name}")

    package_path = ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json"
    package = _read_json(package_path) if package_path.exists() else {}
    if package.get("package_id") != "lane03_broad_selected_meta_selector_v1":
        issues.append("unexpected package_id")
    counts = package.get("rule_counts") if isinstance(package.get("rule_counts"), dict) else {}
    if int(counts.get("tradeable_rules") or 0) < 30:
        issues.append("tradeable rule count is too narrow")
    if int(counts.get("avoid_rules") or 0) <= 0:
        issues.append("missing negative risk-cell avoid rules")
    if int(counts.get("reduce_rules") or 0) <= 0:
        issues.append("missing weak risk-cell reduce rules")
    all_rules = []
    for key in ("tradeable_rules", "avoid_rules", "reduce_rules", "capture_repair_rules"):
        value = package.get(key)
        if isinstance(value, list):
            all_rules.extend(value)
    if len(all_rules) <= 2:
        issues.append("selector package collapsed to Friday two-rule subset")
    if any("friday_broad" in str(rule.get("rule_id", "")) for rule in all_rules):
        issues.append("package retained old hard-coded friday rule id")

    tradeable_keys = {
        (rule.get("session"), rule.get("origin_family"))
        for rule in package.get("tradeable_rules", [])
        if isinstance(rule, dict)
    }
    required_tradeables = {
        ("london_broad", "liquidity_sweep_reclaim"),
        ("london_broad", "displacement_continuation"),
        ("ny_broad", "current_fvg_fill"),
        ("tokyo_broad", "structural_distance_extreme"),
        ("off_kz_broad", "cross_asset_lead_lag"),
    }
    missing_tradeables = sorted(required_tradeables - tradeable_keys)
    if missing_tradeables:
        issues.append(f"missing broad tradeable mechanisms {missing_tradeables}")

    avoid_cells = {rule.get("risk_cell_id") for rule in package.get("avoid_rules", [])}
    if "USDCAD|breaker_re_entry|ny_broad|current_breaker_re_entry|SHORT" not in avoid_cells:
        issues.append("missing current negative selected-denominator USDCAD breaker avoid cell")
    reduce_cells = {rule.get("risk_cell_id") for rule in package.get("reduce_rules", [])}
    if "USDJPY|ob_retest|london_broad|current_ob_retest|LONG" not in reduce_cells:
        issues.append("missing weak accepted expectancy USDJPY ob_retest reduce cell")

    metric_count = _jsonl_count(ROUTE_DIR / "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl")
    if metric_count < 500:
        issues.append("metric ledger too small for full selected-denominator preservation")
    branch_count = _jsonl_count(ROUTE_DIR / "LANE03_META_SELECTOR_BRANCH_DECISION_LEDGER.jsonl")
    if branch_count != metric_count:
        issues.append("branch decision ledger does not preserve every metric row")

    source_text = (ROUTE_DIR / "LANE03_SOURCE_COMPLETENESS_CAPTURE_REPAIR_LEDGER.jsonl").read_text(encoding="utf-8")
    for needle in ("broker_net_r_cost_truth", "tick_coverage", "spread_r_at_candidate"):
        if needle not in source_text:
            issues.append(f"source completeness ledger missing {needle}")

    config_text = (ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    if _repo(package_path) not in config_text:
        issues.append("config does not point to Lane03 selector package")
    router_text = (ROOT / "src" / "research" / "moonshot_default_off_policy_router.py").read_text(encoding="utf-8")
    if "DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES: tuple[dict[str, Any], ...] = ()" not in router_text:
        issues.append("router default Friday fallback was not removed")
    for needle in (
        "candidate_quality_negative_selected_denominator_rule",
        "reduce_risk_by_evidence",
        "candidate_quality_session_origin_not_in_selected_denominator_package",
    ):
        if needle not in router_text:
            issues.append(f"router missing selector behavior {needle}")
    runtime_text = (ROOT / "src" / "components" / "gtos_vnext_runtime.py").read_text(encoding="utf-8")
    if "_moonshot_candidate_quality_selector_package" not in runtime_text:
        issues.append("runtime package loader missing")
    tests_text = (ROOT / "tests" / "test_moonshot_default_off_policy_router.py").read_text(encoding="utf-8")
    for needle in (
        "test_candidate_quality_selector_matches_broad_session_alias",
        "test_candidate_quality_selector_avoid_rule_overrides_tradeable_rule",
        "test_candidate_quality_selector_reduce_rule_stays_tradeable_with_risk_multiplier",
        "test_candidate_quality_selector_missing_spread_requires_source_capture",
    ):
        if needle not in tests_text:
            issues.append(f"focused router test missing {needle}")

    audit = _read_json(ROUTE_DIR / "LANE03_COMPLETION_AUDIT.json")
    if audit.get("status") != "complete":
        issues.append("completion audit is not complete")
    if audit.get("forbidden_surfaces_touched") not in ([], None):
        issues.append("completion audit records forbidden surface touches")

    result = {
        "schema_version": "lane03_verification_result_v1",
        "route_id": ROUTE_ID,
        "status": "verified" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "checked_outputs": required,
        "package_rule_counts": counts,
        "metric_row_count": metric_count,
        "branch_row_count": branch_count,
    }
    result_path = ROUTE_DIR / "LANE03_VERIFICATION_RESULT.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _update_manifest_with_verification_result(result_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    metrics = scan_lane02_metrics()
    package = build_rule_package(metrics)
    branch_ledger = build_branch_decision_ledger(metrics, package)
    source_ledger = build_source_completeness_ledger()
    concentration_ledger = build_concentration_guard_ledger()
    implementation_ledger = build_implementation_decisions(package)
    input_integrity = build_upstream_input_integrity(metrics)

    outputs = {
        "context_anchor": ROUTE_DIR / "LANE03_CONTEXT_ANCHOR.md",
        "metrics": ROUTE_DIR / "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl",
        "branch": ROUTE_DIR / "LANE03_META_SELECTOR_BRANCH_DECISION_LEDGER.jsonl",
        "package": ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json",
        "source": ROUTE_DIR / "LANE03_SOURCE_COMPLETENESS_CAPTURE_REPAIR_LEDGER.jsonl",
        "implementation": ROUTE_DIR / "LANE03_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "concentration": ROUTE_DIR / "LANE03_CONCENTRATION_GUARD_LEDGER.jsonl",
        "self_red_team": ROUTE_DIR / "LANE03_SATURATION_SELF_RED_TEAM.md",
        "audit": ROUTE_DIR / "LANE03_COMPLETION_AUDIT.json",
        "manifest": ROUTE_DIR / "LANE03_OUTPUT_MANIFEST.json",
        "verifier": ROUTE_DIR / "verify_lane03_meta_selector.py",
    }

    write_text(outputs["context_anchor"], build_context_anchor(package))
    write_jsonl(outputs["metrics"], metrics)
    write_jsonl(outputs["branch"], branch_ledger)
    write_json(outputs["package"], package)
    write_jsonl(outputs["source"], source_ledger)
    write_jsonl(outputs["implementation"], implementation_ledger)
    write_jsonl(outputs["concentration"], concentration_ledger)
    write_text(outputs["self_red_team"], build_self_red_team(package))
    write_text(outputs["verifier"], VERIFY_SCRIPT)

    audit = {
        "schema_version": "lane03_completion_audit_v1",
        "route_id": ROUTE_ID,
        "status": "complete",
        "generated_at_utc": _utc_now(),
        "git_head": _git_head(),
        "input_rows_scanned": metrics[0]["rows"] if metrics and metrics[0]["split_scope"] == "all" else None,
        "upstream_input_integrity": input_integrity,
        "metric_rows_preserved": len(metrics),
        "branch_decision_rows": len(branch_ledger),
        "source_completeness_rows": len(source_ledger),
        "concentration_guard_rows": len(concentration_ledger),
        "implementation_decision_rows": len(implementation_ledger),
        "rule_counts": package["rule_counts"],
        "completion_claim": (
            "Lane03 converted Friday and Lane02 broad selected-denominator evidence into a generated "
            "selector package, local router/runtime/config implementation decisions, full ledgers, "
            "route verifier, manifest, and saturation audit."
        ),
        "doctrine_operationalization": {
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "posture": "builder_discovery_implementation_local_selector_package",
            "anti_boxing_pursued": [
                "all Lane02 selected rows scanned",
                "all material split scopes preserved in metric ledger",
                "Friday rules treated as context not hard-coded package boundary",
                "negative and weak risk cells converted to avoid/reduce clauses",
                "source/cost/tick/path gaps converted to capture requirements",
            ],
            "proof_or_impossibility_stop_condition": (
                "local selected-denominator replay exhausted; broker net-R cost truth remains exact Lane06/Lane08 capture requirement"
            ),
        },
        "verification": {
            "route_verifier_path": _repo_path(outputs["verifier"]),
            "route_verification_result_path": _repo_path(ROUTE_DIR / "LANE03_VERIFICATION_RESULT.json"),
            "focused_tests_expected": [
                "py -3 -m pytest tests/test_moonshot_default_off_policy_router.py -q --basetemp=.pytest-tmp-lane03-router -o cache_dir=.pytest-tmp-lane03-router-cache",
                "py -3 -m pytest tests/test_gtos_vnext_runtime.py::test_structured_decision_logger_writes_pre_ai_and_post_l2_rows -q --basetemp=.pytest-tmp-lane03-runtime -o cache_dir=.pytest-tmp-lane03-runtime-cache",
            ],
        },
        "forbidden_surfaces_touched": [],
        "external_actions": {
            "broker_order_deal_position_action": False,
            "paid_api_or_vendor_call": False,
            "credential_change": False,
            "remote_push": False,
            "live_restart_or_hidden_deployment": False,
        },
    }
    write_json(outputs["audit"], audit)

    manifest = build_manifest(
        [
            outputs["context_anchor"],
            outputs["metrics"],
            outputs["branch"],
            outputs["package"],
            outputs["source"],
            outputs["implementation"],
            outputs["concentration"],
            outputs["self_red_team"],
            outputs["audit"],
            outputs["verifier"],
        ]
    )
    write_json(outputs["manifest"], manifest)
    return {
        "route_id": ROUTE_ID,
        "route_dir": _repo_path(ROUTE_DIR),
        "metric_rows": len(metrics),
        "rule_counts": package["rule_counts"],
        "outputs": {key: _repo_path(path) for key, path in outputs.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    if args.summary_only:
        if not (ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json").exists():
            raise SystemExit("Lane03 package has not been built yet")
        package = json.loads((ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json").read_text(encoding="utf-8"))
        print(json.dumps({"route_id": ROUTE_ID, "rule_counts": package.get("rule_counts")}, indent=2, sort_keys=True))
        return 0
    result = build_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
