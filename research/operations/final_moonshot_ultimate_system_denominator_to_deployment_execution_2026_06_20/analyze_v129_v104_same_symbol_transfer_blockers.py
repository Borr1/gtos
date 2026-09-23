#!/usr/bin/env python3
"""Join V104 same-symbol winners to V129 targeted replay transfer blockers.

This is a route-owned B7 diagnostic, not a trading policy. It streams the heavy
V129 ledgers and emits the exact V104 trade keys that still fail to transfer in
the latest targeted proof slice.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
V104_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260605"
V129_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_V129_B7_TERMINAL_SOFT_SELECTED_POLICY_QUALITY_"
    "20260601_20260605_TARGETED_SOFT_TRANSFER"
)
ACTIVE_SYMBOLS = {"XAUUSD", "XAGUSD", "USDCAD", "USDJPY", "UKOIL_cash"}

SUMMARY_PATH = ROUTE / "V129_V104_SAME_SYMBOL_TRANSFER_BLOCKER_ANALYSIS.json"
LEDGER_PATH = ROUTE / "V129_V104_SAME_SYMBOL_TRANSFER_BLOCKER_LEDGER.jsonl"

BASE_FIELDS = (
    "canonical_replay_candidate_instance_key",
    "candidate_id",
    "decision_time_utc",
    "decision_window_id",
    "symbol",
    "side",
    "direction",
    "session",
    "origin_family",
    "candidate_origin_family",
    "framework",
    "current_framework",
    "selector_action",
    "effective_selector_action",
    "materialized_selector_action",
    "selector_reason",
    "effective_selector_reason",
    "materialized_selector_reason",
    "risk_decision",
    "risk_decision_reason",
    "order_status",
    "miss_reason",
    "broker_pretrade_cost_executable",
    "broker_pretrade_cost_executable_block_reason",
    "broker_pretrade_cost_r",
    "missed_cost_disposition",
    "cost_source_gap_status",
    "fill_realism_class",
    "fill_realism_executable",
    "fill_realism_reason",
    "counterfactual_order_fill_status",
    "counterfactual_order_terminal_outcome",
    "expected_net_r",
    "candidate_expected_net_r",
    "probability",
    "candidate_probability",
    "fill_probability",
    "candidate_fill_probability",
    "source_completeness",
    "source_bound_signal_r",
    "net_r",
    "gross_r",
    "final_r",
    "expected_cost_r",
    "approved_risk_pct",
    "risk_pct",
    "order_policy",
    "close_reason",
)

INTERESTING_SUBSTRINGS = (
    "risk_expression_ladder",
    "scheduler_terminal_vs_soft_guard",
    "terminal_veto",
    "soft_guard",
    "soft_reallocation",
    "reallocation",
    "selected_policy",
    "package_new_entry_authority",
    "package_fill_floor_authority",
    "package_marketable_entry_guard",
    "lifecycle",
    "source_required",
    "score",
)

KEY_FIELDS = (
    "canonical_replay_candidate_instance_key",
    "selected_scheduler_canonical_replay_candidate_instance_key",
    "finalizer_primary_probe_canonical_replay_candidate_instance_key",
    "risk_finalizer_canonical_replay_candidate_instance_key",
    "package_new_entry_authority_canonical_replay_candidate_instance_key",
)


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def first_present(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None


def side_value(row: dict[str, Any]) -> str:
    value = first_present(row, "side", "direction")
    return str(value or "").upper()


def tuple_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("decision_time_utc") or row.get("decision_time") or ""),
        side_value(row),
    )


def possible_keys(row: dict[str, Any]) -> set[str]:
    keys = set()
    for field in KEY_FIELDS:
        value = row.get(field)
        if value:
            keys.add(str(value))
    return keys


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in BASE_FIELDS:
        if field in row:
            out[field] = row.get(field)
    for field, value in row.items():
        if field in out:
            continue
        if any(part in field for part in INTERESTING_SUBSTRINGS):
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[field] = value
    return out


def add_match(store: dict[str, list[dict[str, Any]]], ledger: str, line_no: int, row: dict[str, Any]) -> None:
    bucket = store.setdefault(ledger, [])
    if len(bucket) >= 8:
        return
    item = compact_row(row)
    item["_ledger"] = ledger
    item["_line_no"] = line_no
    bucket.append(item)


def classify(record: dict[str, Any]) -> tuple[str, bool]:
    if record["v129_trade_rows"]:
        return "transferred_filled_in_v129", False
    if record["v129_order_rows"]:
        statuses = {str(row.get("order_status") or "") for row in record["v129_order_rows"]}
        if "expired_unfilled" in statuses or "pending_accepted" in statuses:
            return "order_present_not_filled_or_expired", True
        return "order_present_not_filled_other", True
    if not record["v129_candidate_rows"] and not record["v129_tuple_candidate_rows"]:
        return "candidate_not_generated_in_v129_targeted_slice", True
    missed_rows = record["v129_missed_rows"]
    if not missed_rows:
        if record["v129_scorecard_rows"]:
            return "scorecard_present_no_order_or_missed_row", True
        return "candidate_present_without_missed_or_order_explanation", True

    joined_reason = "|".join(str(row.get("miss_reason") or "") for row in missed_rows)
    joined_cost = "|".join(
        str(first_present(row, "missed_cost_disposition", "broker_pretrade_cost_executable_block_reason", "cost_source_gap_status") or "")
        for row in missed_rows
    )
    text = f"{joined_reason}|{joined_cost}".lower()
    cost_exec_values = {str(row.get("broker_pretrade_cost_executable")) for row in missed_rows}
    if "cost_refused" in text or "broker_net_pretrade_cost_packet_refused" in text or "cost_failed" in text:
        return "broker_cost_refused_or_cost_failed_non_executable", False
    if "source_gap" in text or "source_required" in text:
        return "source_gap_or_source_required_non_executable", False
    if "package_marketable_limit_entry_guard" in text or "passive_limit_too_close" in text or "pre_order_materialization_preflight" in text:
        return "order_geometry_or_preflight_guard_blocked", True
    if "lifecycle" in text or "pending_replacement" in text:
        return "lifecycle_or_replacement_authority_blocked", True
    if "risk_finalizer_rejected" in text:
        return "risk_finalizer_rejected_after_candidate_generation", True
    if "scheduler_materialization_skipped" in text or "scheduler_vetoed" in text:
        return "scheduler_materialization_or_selection_skipped", True
    if cost_exec_values == {"False"}:
        return "broker_cost_non_executable_uncategorized", False
    return "missed_other_recoverability_unknown", True


def main() -> int:
    v104_path = ROUTE / f"{V104_PREFIX}_TRADE_LEDGER.jsonl"
    target_keys: dict[str, dict[str, Any]] = {}
    tuple_to_keys: dict[tuple[str, str, str], set[str]] = defaultdict(set)

    for _line_no, row in load_jsonl(v104_path):
        if row.get("symbol") not in ACTIVE_SYMBOLS:
            continue
        key = str(row.get("canonical_replay_candidate_instance_key") or "")
        if not key:
            continue
        target_keys[key] = compact_row(row)
        target_keys[key]["v104_net_r"] = float(row.get("net_r") or 0.0)
        target_keys[key]["v104_final_r"] = float(row.get("final_r") or 0.0)
        target_keys[key]["v104_close_reason"] = row.get("close_reason")
        tuple_to_keys[tuple_key(row)].add(key)

    exact_matches: dict[str, dict[str, list[dict[str, Any]]]] = {
        key: {
            "candidate": [],
            "missed": [],
            "order": [],
            "trade": [],
            "scorecard": [],
            "tuple_candidate": [],
            "tuple_missed": [],
        }
        for key in target_keys
    }

    ledgers = {
        "candidate": ROUTE / f"{V129_PREFIX}_CANDIDATE_LEDGER.jsonl",
        "missed": ROUTE / f"{V129_PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "order": ROUTE / f"{V129_PREFIX}_ORDER_LEDGER.jsonl",
        "trade": ROUTE / f"{V129_PREFIX}_TRADE_LEDGER.jsonl",
        "scorecard": ROUTE / f"{V129_PREFIX}_SCORECARD_LEDGER.jsonl",
    }
    scanned_rows: Counter[str] = Counter()

    for ledger_name, path in ledgers.items():
        for line_no, row in load_jsonl(path):
            scanned_rows[ledger_name] += 1
            keys = possible_keys(row)
            for key in keys & target_keys.keys():
                add_match(exact_matches[key], ledger_name, line_no, row)
            if ledger_name in {"candidate", "missed"}:
                for key in tuple_to_keys.get(tuple_key(row), ()):
                    if key not in keys:
                        add_match(exact_matches[key], f"tuple_{ledger_name}", line_no, row)

    records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    class_net_r: Counter[str] = Counter()
    class_recoverable_net_r: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    symbol_net_r: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    reason_net_r: Counter[str] = Counter()

    for key, v104 in sorted(target_keys.items(), key=lambda item: item[1].get("decision_time_utc") or ""):
        matches = exact_matches[key]
        record = {
            "canonical_replay_candidate_instance_key": key,
            "v104_trade": v104,
            "v129_candidate_rows": matches["candidate"],
            "v129_missed_rows": matches["missed"],
            "v129_order_rows": matches["order"],
            "v129_trade_rows": matches["trade"],
            "v129_scorecard_rows": matches["scorecard"],
            "v129_tuple_candidate_rows": matches["tuple_candidate"],
            "v129_tuple_missed_rows": matches["tuple_missed"],
        }
        classification, recoverable = classify(record)
        record["blocker_class"] = classification
        record["recoverable_from_current_evidence"] = recoverable
        v104_net = float(v104.get("v104_net_r") or 0.0)
        class_counts[classification] += 1
        class_net_r[classification] += v104_net
        if recoverable:
            class_recoverable_net_r[classification] += v104_net
        symbol = str(v104.get("symbol") or "")
        symbol_counts[symbol] += 1
        symbol_net_r[symbol] += v104_net
        if record["v129_missed_rows"]:
            reason = str(record["v129_missed_rows"][0].get("miss_reason") or "missing")
        elif record["v129_order_rows"]:
            reason = str(record["v129_order_rows"][0].get("order_status") or "order_present")
        elif record["v129_trade_rows"]:
            reason = "filled"
        elif record["v129_candidate_rows"]:
            reason = "candidate_present_without_downstream_row"
        else:
            reason = "candidate_not_generated"
        reason_counts[reason] += 1
        reason_net_r[reason] += v104_net
        records.append(record)

    highest_recoverable = None
    if class_recoverable_net_r:
        name, value = max(class_recoverable_net_r.items(), key=lambda item: item[1])
        highest_recoverable = {
            "blocker_class": name,
            "v104_net_r": round(value, 10),
            "row_count": class_counts[name],
        }

    summary = {
        "schema": "gtos.route.v129_v104_same_symbol_transfer_blocker_analysis.v1",
        "v104_prefix": V104_PREFIX,
        "v129_prefix": V129_PREFIX,
        "window": "2026-06-01..2026-06-05",
        "active_symbols": sorted(ACTIVE_SYMBOLS),
        "target_v104_same_symbol_trade_rows": len(records),
        "target_v104_same_symbol_net_r": round(sum(float(row["v104_trade"].get("v104_net_r") or 0.0) for row in records), 10),
        "scanned_rows": dict(scanned_rows),
        "stage_presence_counts": {
            "candidate_exact": sum(1 for row in records if row["v129_candidate_rows"]),
            "missed_exact": sum(1 for row in records if row["v129_missed_rows"]),
            "order_exact": sum(1 for row in records if row["v129_order_rows"]),
            "trade_exact": sum(1 for row in records if row["v129_trade_rows"]),
            "tuple_candidate_only": sum(1 for row in records if row["v129_tuple_candidate_rows"] and not row["v129_candidate_rows"]),
            "tuple_missed_only": sum(1 for row in records if row["v129_tuple_missed_rows"] and not row["v129_missed_rows"]),
        },
        "blocker_class_counts": dict(class_counts),
        "blocker_class_v104_net_r": {key: round(value, 10) for key, value in class_net_r.items()},
        "recoverable_blocker_class_v104_net_r": {key: round(value, 10) for key, value in class_recoverable_net_r.items()},
        "highest_recoverable_blocker": highest_recoverable,
        "symbol_counts": dict(symbol_counts),
        "symbol_v104_net_r": {key: round(value, 10) for key, value in symbol_net_r.items()},
        "top_miss_or_stage_reasons": [
            {"reason": key, "count": count, "v104_net_r": round(reason_net_r[key], 10)}
            for key, count in reason_counts.most_common(20)
        ],
        "interpretation": (
            "This is a targeted same-window V104-to-V129 transfer analysis. "
            "It does not measure global source-bound reservoir transfer."
        ),
        "artifact_paths": {
            "summary": str(SUMMARY_PATH.relative_to(ROUTE)),
            "ledger": str(LEDGER_PATH.relative_to(ROUTE)),
        },
    }

    with LEDGER_PATH.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
