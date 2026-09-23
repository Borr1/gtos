#!/usr/bin/env python3
"""Classify B4 fill/source-realism blockers from broad replay missed ledgers.

The classifier is diagnostic-only. It does not promote diagnostic/proxy rows
into executable trades. Its job is to separate source/fillability truth gaps
from cost, selector, scheduler, and risk blockers before the next replay.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROUTE = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def opportunity_net_r(row: Mapping[str, Any]) -> float | None:
    value = row.get("opportunity_net_proxy_r")
    if finite_number(value):
        return float(value)
    return None


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
            if isinstance(row, dict):
                yield row


def classify_stage(row: Mapping[str, Any]) -> str:
    fill_class = safe(row.get("fill_realism_class"))
    cost_disposition = safe(row.get("missed_cost_disposition"))
    broker_cost_executable = row.get("broker_pretrade_cost_executable")
    reason_blob = "|".join(
        safe(row.get(key))
        for key in (
            "missed_non_executable_diagnostic_reason",
            "miss_reason",
            "missed_package_replay_order_executable_final_blocker_reason",
            "fill_realism_reason",
        )
    )
    if (
        cost_disposition == "scoreable_missed_cost_refused_non_executable_diagnostic"
        or broker_cost_executable is False
        or "cost_refused" in reason_blob
        or "cost_authority_blocked" in reason_blob
        or "cost_failed" in reason_blob
    ):
        return "B6_cost_refusal_or_cost_authority"
    if fill_class in {"m15_proxy", "source_gap", "first_touch_optimistic"}:
        return "B4_source_realism_or_missing_ordered_source"
    if fill_class == "not_filled" or "not_filled" in reason_blob or "entry_not_filled" in reason_blob:
        return "B4_honest_not_filled_or_lifecycle_expiry"
    if "marketable_limit_entry_guard_blocked" in reason_blob or "passive_limit_too_close" in reason_blob:
        return "B4_order_geometry_guard"
    if "scheduler_" in reason_blob or "risk_finalizer_" in reason_blob:
        return "B2_B3_scheduler_risk_reallocation_or_admission"
    if "selector_" in reason_blob or "dynamic_router" in reason_blob or "admission_quality" in reason_blob:
        return "selector_admission_policy"
    return "other_unclassified"


@dataclass
class Aggregate:
    rows: int = 0
    scoreable_rows: int = 0
    unscoreable_rows: int = 0
    opportunity_net_r_sum: float = 0.0
    positive_rows: int = 0
    positive_r_sum: float = 0.0
    negative_rows: int = 0
    negative_r_sum: float = 0.0
    flat_or_unscoreable_rows: int = 0
    expected_net_r_sum_diagnostic_only: float = 0.0
    diagnostic_proxy_mark_rows: int = 0
    diagnostic_proxy_mark_net_r_sum: float = 0.0
    diagnostic_proxy_mark_positive_rows: int = 0
    diagnostic_proxy_mark_positive_r_sum: float = 0.0
    diagnostic_proxy_mark_negative_rows: int = 0
    diagnostic_proxy_mark_negative_r_sum: float = 0.0

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        expected_net_r = row.get("expected_net_r")
        if finite_number(expected_net_r):
            self.expected_net_r_sum_diagnostic_only += float(expected_net_r)
        value = opportunity_net_r(row)
        if value is None:
            self.unscoreable_rows += 1
            self.flat_or_unscoreable_rows += 1
            proxy_mark = row.get("counterfactual_order_close_mark_r")
            expected_cost = row.get("expected_cost_r")
            if finite_number(proxy_mark) and finite_number(expected_cost):
                proxy_net = float(proxy_mark) - float(expected_cost)
                self.diagnostic_proxy_mark_rows += 1
                self.diagnostic_proxy_mark_net_r_sum += proxy_net
                if proxy_net > 0:
                    self.diagnostic_proxy_mark_positive_rows += 1
                    self.diagnostic_proxy_mark_positive_r_sum += proxy_net
                elif proxy_net < 0:
                    self.diagnostic_proxy_mark_negative_rows += 1
                    self.diagnostic_proxy_mark_negative_r_sum += proxy_net
            return
        self.scoreable_rows += 1
        self.opportunity_net_r_sum += value
        if value > 0:
            self.positive_rows += 1
            self.positive_r_sum += value
        elif value < 0:
            self.negative_rows += 1
            self.negative_r_sum += value
        else:
            self.flat_or_unscoreable_rows += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "scoreable_rows": self.scoreable_rows,
            "unscoreable_rows": self.unscoreable_rows,
            "opportunity_net_r_sum": round(self.opportunity_net_r_sum, 10),
            "positive_rows": self.positive_rows,
            "positive_r_sum": round(self.positive_r_sum, 10),
            "negative_rows": self.negative_rows,
            "negative_r_sum": round(self.negative_r_sum, 10),
            "flat_or_unscoreable_rows": self.flat_or_unscoreable_rows,
            "expected_net_r_sum_diagnostic_only": round(self.expected_net_r_sum_diagnostic_only, 10),
            "diagnostic_proxy_mark_rows": self.diagnostic_proxy_mark_rows,
            "diagnostic_proxy_mark_net_r_sum": round(self.diagnostic_proxy_mark_net_r_sum, 10),
            "diagnostic_proxy_mark_positive_rows": self.diagnostic_proxy_mark_positive_rows,
            "diagnostic_proxy_mark_positive_r_sum": round(self.diagnostic_proxy_mark_positive_r_sum, 10),
            "diagnostic_proxy_mark_negative_rows": self.diagnostic_proxy_mark_negative_rows,
            "diagnostic_proxy_mark_negative_r_sum": round(self.diagnostic_proxy_mark_negative_r_sum, 10),
        }


def bucket_key(row: Mapping[str, Any], bucket_type: str, stage: str) -> str:
    if bucket_type == "stage":
        return stage
    if bucket_type == "fill_realism":
        return safe(row.get("fill_realism_class"))
    if bucket_type == "stage_fill":
        return f"{stage}|{safe(row.get('fill_realism_class'))}"
    if bucket_type == "stage_reason":
        reason = row.get("missed_non_executable_diagnostic_reason") or row.get("miss_reason") or row.get("fill_realism_reason")
        return f"{stage}|{safe(reason)}"
    if bucket_type == "symbol_stage":
        return f"{safe(row.get('symbol'))}|{stage}"
    if bucket_type == "session_stage":
        return f"{safe(row.get('session'))}|{stage}"
    if bucket_type == "source_stage":
        source = row.get("origin_family") or row.get("current_framework") or row.get("framework")
        return f"{safe(source)}|{stage}"
    if bucket_type == "order_policy_stage":
        policy = row.get("order_policy") or row.get("effective_order_type") or row.get("order_execution_path")
        return f"{safe(policy)}|{stage}"
    if bucket_type == "action_stage":
        action = row.get("effective_selector_action") or row.get("selector_action") or row.get("action")
        return f"{safe(action)}|{stage}"
    raise ValueError(f"unknown bucket type: {bucket_type}")


def sort_bucket_items(items: Mapping[str, Aggregate]) -> list[tuple[str, Aggregate]]:
    return sorted(
        items.items(),
        key=lambda item: (
            item[1].scoreable_rows,
            abs(item[1].opportunity_net_r_sum),
            item[1].rows,
        ),
        reverse=True,
    )


def top_buckets(items: Mapping[str, Aggregate], limit: int) -> list[dict[str, Any]]:
    return [{"key": key, **aggregate.as_dict()} for key, aggregate in sort_bucket_items(items)[:limit]]


def compact_example(row: Mapping[str, Any], stage: str) -> dict[str, Any]:
    keys = (
        "symbol",
        "session",
        "side",
        "decision_time_utc",
        "candidate_id",
        "canonical_replay_candidate_instance_key",
        "fill_realism_class",
        "fill_realism_reason",
        "missed_non_executable_diagnostic_reason",
        "miss_reason",
        "opportunity_net_proxy_r",
        "expected_net_r",
        "broker_pretrade_cost_executable",
        "missed_cost_disposition",
        "package_execution_result_scope",
        "selector_action",
        "effective_selector_action",
        "risk_decision",
        "order_status",
        "origin_family",
        "current_framework",
    )
    payload = {key: row.get(key) for key in keys}
    payload["stage_bucket"] = stage
    return payload


def classify_missed_ledger(prefix: str, *, route: Path = ROUTE, generated_at: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    missed_path = route / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    if not missed_path.exists():
        raise SystemExit(f"missing missed-opportunity ledger: {missed_path}")

    bucket_types = (
        "stage",
        "fill_realism",
        "stage_fill",
        "stage_reason",
        "symbol_stage",
        "session_stage",
        "source_stage",
        "order_policy_stage",
        "action_stage",
    )
    aggregates: dict[str, dict[str, Aggregate]] = {
        bucket_type: defaultdict(Aggregate) for bucket_type in bucket_types
    }
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scoreable_rows: list[dict[str, Any]] = []
    counters: dict[str, Counter[str]] = {
        "source_boundary_counts": Counter(),
        "lazy_tick_source_validation_event_counts": Counter(),
        "missed_cost_disposition_counts": Counter(),
        "package_execution_result_scope_counts": Counter(),
        "fill_realism_executable_counts": Counter(),
        "broker_pretrade_cost_executable_counts": Counter(),
        "risk_ladder_tier_counts": Counter(),
        "top_risk_ladder_reasons": Counter(),
    }
    row_count = 0

    for row in iter_jsonl(missed_path):
        row_count += 1
        stage = classify_stage(row)
        for bucket_type in bucket_types:
            aggregates[bucket_type][bucket_key(row, bucket_type, stage)].add(row)
        if len(examples[stage]) < 5:
            examples[stage].append(compact_example(row, stage))
        value = opportunity_net_r(row)
        if value is not None:
            scoreable = compact_example(row, stage)
            for key in ("opportunity_gross_r", "expected_cost_r"):
                scoreable[key] = row.get(key)
            scoreable_rows.append(scoreable)

        counters["source_boundary_counts"][safe(row.get("fill_realism_source_boundary"))] += 1
        events = row.get("lazy_tick_source_validation_events")
        if isinstance(events, list):
            if not events:
                counters["lazy_tick_source_validation_event_counts"]["empty_list"] += 1
            for event in events:
                counters["lazy_tick_source_validation_event_counts"][safe((event or {}).get("status"))] += 1
        else:
            counters["lazy_tick_source_validation_event_counts"][safe(events)] += 1
        counters["missed_cost_disposition_counts"][safe(row.get("missed_cost_disposition"))] += 1
        counters["package_execution_result_scope_counts"][safe(row.get("package_execution_result_scope"))] += 1
        counters["fill_realism_executable_counts"][safe(row.get("fill_realism_executable"))] += 1
        counters["broker_pretrade_cost_executable_counts"][safe(row.get("broker_pretrade_cost_executable"))] += 1
        ladder = row.get("risk_expression_ladder")
        if isinstance(ladder, Mapping):
            counters["risk_ladder_tier_counts"][safe(ladder.get("ladder_tier"))] += 1
            counters["top_risk_ladder_reasons"][safe(ladder.get("risk_decision_reason"))] += 1
        else:
            counters["risk_ladder_tier_counts"]["missing"] += 1

    scoreable_rows.sort(key=lambda row: row.get("opportunity_net_proxy_r") or 0, reverse=True)
    bucket_rows: list[dict[str, Any]] = []
    for bucket_type in bucket_types:
        for key, aggregate in sort_bucket_items(aggregates[bucket_type]):
            bucket_rows.append({"bucket_type": bucket_type, "key": key, **aggregate.as_dict()})

    summary: dict[str, Any] = {
        "schema": "broad_live_as_if_replay_b4_source_realism_blocker_classification_v1",
        "prefix": prefix,
        "generated_at_utc": generated_at or utc_now(),
        "input_ledger": str(missed_path),
        "rows": row_count,
        "stage_buckets": top_buckets(aggregates["stage"], 20),
        "fill_realism_buckets": top_buckets(aggregates["fill_realism"], 20),
        "stage_fill_buckets": top_buckets(aggregates["stage_fill"], 40),
        "top_stage_reasons": top_buckets(aggregates["stage_reason"], 50),
        "top_symbol_stage": top_buckets(aggregates["symbol_stage"], 50),
        "top_session_stage": top_buckets(aggregates["session_stage"], 50),
        "top_source_stage": top_buckets(aggregates["source_stage"], 50),
        "top_order_policy_stage": top_buckets(aggregates["order_policy_stage"], 50),
        "top_action_stage": top_buckets(aggregates["action_stage"], 50),
        "source_boundary_counts": dict(counters["source_boundary_counts"].most_common()),
        "lazy_tick_source_validation_event_counts": dict(counters["lazy_tick_source_validation_event_counts"].most_common()),
        "missed_cost_disposition_counts": dict(counters["missed_cost_disposition_counts"].most_common()),
        "package_execution_result_scope_counts": dict(counters["package_execution_result_scope_counts"].most_common()),
        "fill_realism_executable_counts": dict(counters["fill_realism_executable_counts"].most_common()),
        "broker_pretrade_cost_executable_counts": dict(counters["broker_pretrade_cost_executable_counts"].most_common()),
        "risk_ladder_tier_counts": dict(counters["risk_ladder_tier_counts"].most_common()),
        "top_risk_ladder_reasons": dict(counters["top_risk_ladder_reasons"].most_common(50)),
        "top_positive_scoreable_missed": scoreable_rows[:25],
        "top_negative_scoreable_missed": list(reversed(scoreable_rows[-25:])),
        "stage_examples": examples,
        "interpretation": {
            "b4_status": "remaining missed rows are not all B4 source leaks; cost refusal dominates rows and scoreable R is net negative",
            "next_dependency_decision": "B4 still needs source-realism classification/hydration for m15_proxy/source_gap classes, but B6 cost calibration is the largest row-count blocker after B4 classification",
            "execution_guard": "do not make cost-refused rows executable; keep them scoreable/missed until B6 calibration proves stale floor or mapping bug",
        },
    }
    return summary, bucket_rows


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, help="Broad replay prefix without artifact suffix")
    parser.add_argument("--route", type=Path, default=ROUTE, help="Route directory")
    args = parser.parse_args(argv)

    summary, bucket_rows = classify_missed_ledger(args.prefix, route=args.route)
    write_json(args.route / f"{args.prefix}_B4_SOURCE_REALISM_BLOCKER_CLASSIFICATION.json", summary)
    write_jsonl(args.route / f"{args.prefix}_B4_SOURCE_REALISM_BLOCKER_BUCKET_LEDGER.jsonl", bucket_rows)
    print(args.route / f"{args.prefix}_B4_SOURCE_REALISM_BLOCKER_CLASSIFICATION.json")
    print(args.route / f"{args.prefix}_B4_SOURCE_REALISM_BLOCKER_BUCKET_LEDGER.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
