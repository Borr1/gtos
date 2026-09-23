#!/usr/bin/env python3
"""Freeze GTOS-scope OHLC survivor rows into replay/source contracts."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
IMMEDIATE_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_IMMEDIATE_REPLAY_QUEUE_2026-05-15.jsonl"
AUDIT_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT_LEDGER_2026-05-15.jsonl"
CLUSTER_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_EVENT_CLUSTER_LEDGER_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_RESULT_2026-05-15.json"
CONTRACT_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_LEDGER_2026-05-15.jsonl"
CLUSTER_BINDING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CLUSTER_BINDING_LEDGER_2026-05-15.jsonl"
BLOCKER_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER_LEDGER_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Frozen replay/source contract only. It freezes discovery candidates for "
    "future source-safe replay and does not validate edge, R/PnL, expectancy, "
    "fillability, live-readiness, or promotion."
)

BLOCKERS = [
    "future_or_sealed_holdout_required_after_discovery_window",
    "entry_geometry_not_defined_by_ohlc_primitive",
    "spread_slippage_commission_not_applied",
    "pending_lifecycle_fillability_not_modeled",
    "no_live_behavior_change_without_owner_approval",
]


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {row["route_candidate_id"]: row for row in read_jsonl(path)}


def build_contract(row: dict[str, Any], audit: dict[str, Any], clusters: list[dict[str, Any]]) -> dict[str, Any]:
    start_times = [cluster["start_time_utc"] for cluster in clusters]
    end_times = [cluster["end_time_utc"] for cluster in clusters]
    discovery_start = min(start_times) if start_times else None
    discovery_end = max(end_times) if end_times else None
    frozen_rule_id = f"OHLC-GTOS-{row['symbol']}-{row['session']}-{row['primitive_id']}-H{row['horizon_bars']}"
    expected_direction = "long_context" if "LOW" in row["primitive_id"] or row["primitive_id"].endswith("_UP") else "short_context"
    if row["primitive_id"] == "LOWER_WICK_EXHAUSTION":
        expected_direction = "long_context"
    if row["primitive_id"] == "UPPER_WICK_EXHAUSTION":
        expected_direction = "short_context"

    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT",
        "frozen_rule_id": frozen_rule_id,
        "route_candidate_id": row["route_candidate_id"],
        "symbol": row["symbol"],
        "session": row["session"],
        "mapped_kill_zone": row["mapped_kill_zone"],
        "primitive_family": row["primitive_family"],
        "primitive_id": row["primitive_id"],
        "horizon_bars": row["horizon_bars"],
        "expected_direction_context": expected_direction,
        "frozen_primitive_definition_source": (
            "build_historical_ohlc_primitives_2026_05_15.py::primitive_events"
        ),
        "discovery_source": "data/historical_2026/*_M15.csv",
        "discovery_window_start_utc": discovery_start,
        "discovery_window_end_utc": discovery_end,
        "discovery_event_count": row["event_count"],
        "discovery_cluster_count": row["cluster_count"],
        "cluster_effective_ratio": row["cluster_effective_ratio"],
        "cluster_weighted_mean_directional_close_units": row[
            "cluster_weighted_mean_directional_close_units"
        ],
        "cluster_weighted_directional_positive_share": row[
            "cluster_weighted_directional_positive_share"
        ],
        "audit_bucket": row["audit_bucket"],
        "source_binding_cluster_rows": len(clusters),
        "future_validation_barrier": (
            "Rows at or before discovery_window_end_utc are contaminated for validation of this rule. "
            "Use post-window forward data or a separately sealed partition chosen before opening outcomes."
        ),
        "allowed_next_uses": [
            "future_replay_preregistration",
            "shadow_feature_capture_contract",
            "candidate_context_feature_design",
            "failure_mode_monitoring",
        ],
        "forbidden_next_uses": [
            "live_filter_or_trade_rule",
            "promotion_claim",
            "strategy_expectancy_claim",
            "R_or_PnL_claim_without_entry_and_cost_model",
        ],
        "blockers": BLOCKERS,
        "safe_flags": SAFE_FLAGS,
    }


def blocker_rows(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contract in contracts:
        for blocker in BLOCKERS:
            rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER",
                    "frozen_rule_id": contract["frozen_rule_id"],
                    "route_candidate_id": contract["route_candidate_id"],
                    "blocker_id": blocker,
                    "status": "OPEN",
                    "required_resolution_before_promotion": True,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows


def write_summary(result: dict[str, Any], symbol_counts: Counter[str]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Contract",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        f"Evidence class: `{result['evidence_class']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Symbols", ""])
    for symbol, count in sorted(symbol_counts.items()):
        lines.append(f"- `{symbol}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- These contracts freeze candidate definitions; they do not prove an edge.",
            "- Existing discovery rows are contaminated for validation of these frozen rules.",
            "- Entry geometry and cost/fill modeling remain open blockers.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    immediate = load_by_id(IMMEDIATE_QUEUE_PATH)
    audit_by_id = load_by_id(AUDIT_LEDGER_PATH)
    clusters_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cluster in read_jsonl(CLUSTER_LEDGER_PATH):
        if cluster["route_candidate_id"] in immediate:
            clusters_by_id[cluster["route_candidate_id"]].append(cluster)

    binding_rows: list[dict[str, Any]] = []
    for route_id, clusters in sorted(clusters_by_id.items()):
        for cluster in clusters:
            binding = dict(cluster)
            binding["contract_binding_status"] = "BOUND_TO_FROZEN_GTOS_REPLAY_CONTRACT"
            binding["safe_flags"] = SAFE_FLAGS
            binding_rows.append(binding)

    contracts: list[dict[str, Any]] = []
    for route_id, row in sorted(immediate.items()):
        contracts.append(build_contract(row, audit_by_id[route_id], clusters_by_id.get(route_id, [])))

    blockers = blocker_rows(contracts)
    symbol_counts = Counter(contract["symbol"] for contract in contracts)

    write_jsonl(CONTRACT_LEDGER_PATH, contracts)
    write_jsonl(CLUSTER_BINDING_PATH, binding_rows)
    write_jsonl(BLOCKER_LEDGER_PATH, blockers)

    result = {
        "schema": "historical_ohlc_gtos_replay_contract_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT",
        "claim_boundary": CLAIM_BOUNDARY,
        "counts": {
            "input_immediate_replay_rows": len(immediate),
            "contract_rows": len(contracts),
            "cluster_binding_rows": len(binding_rows),
            "blocker_rows": len(blockers),
        },
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "open_blockers": BLOCKERS,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, symbol_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
