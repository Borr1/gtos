#!/usr/bin/env python3
"""Triage OHLC survivor rows against GTOS symbol/session scope."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO))

from src.research_infra.stratification import DEFAULT_KILL_ZONES

INPUT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CLUSTER_ROUTE_QUEUE_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE_RESULT_2026-05-15.json"
LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE_LEDGER_2026-05-15.jsonl"
IMMEDIATE_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_IMMEDIATE_REPLAY_QUEUE_2026-05-15.jsonl"
TRANSFER_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_SOURCE_TRANSFER_QUEUE_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "GTOS scope triage only. This is not sealed validation, R/PnL, "
    "expectancy, fillability, live-readiness, or a promotion verdict."
)

CURRENT_FLEET_SYMBOLS = {
    "XAUUSD",
    "XAGUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
}

OBSERVER_ONLY_SYMBOLS = {"GBPUSD"}

SESSION_TO_KZ = {
    "tokyo_kz": "tokyo",
    "london_core": "london",
    "ny_core": "ny",
}


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


def triage_row(row: dict[str, Any]) -> dict[str, Any]:
    symbol = row["symbol"]
    session = row["session"]
    configured_sessions = DEFAULT_KILL_ZONES.get(symbol, {})
    mapped_kz = SESSION_TO_KZ.get(session)
    configured_session_match = bool(mapped_kz and mapped_kz in configured_sessions)
    current_fleet = symbol in CURRENT_FLEET_SYMBOLS
    observer_only = symbol in OBSERVER_ONLY_SYMBOLS
    configured_but_not_current = symbol in DEFAULT_KILL_ZONES and not current_fleet
    off_or_unmapped_session = mapped_kz is None

    if current_fleet and configured_session_match and not observer_only:
        scope_bucket = "GTOS_IMMEDIATE_REPLAY_CANDIDATE"
        next_route = "purged_or_forward_replay_design_with_cost_fill_before_strategy_projection"
    elif current_fleet and configured_session_match and observer_only:
        scope_bucket = "GTOS_OBSERVER_ONLY_REPLAY_CANDIDATE"
        next_route = "observer_only_source_replay_no_execution_implication"
    elif current_fleet and not configured_session_match:
        scope_bucket = "CURRENT_SYMBOL_OUTSIDE_CONFIGURED_SESSION"
        next_route = "source_transfer_or_session-boundary_diagnostic_only"
    elif configured_but_not_current and configured_session_match:
        scope_bucket = "CONFIGURED_BACKTEST_ONLY_SOURCE_TRANSFER_CANDIDATE"
        next_route = "source_transfer_research_only_no_live_fleet_assumption"
    elif configured_but_not_current:
        scope_bucket = "CONFIGURED_BACKTEST_ONLY_OUTSIDE_SESSION"
        next_route = "low_priority_source_transfer_diagnostic_only"
    elif off_or_unmapped_session:
        scope_bucket = "OUT_OF_SCOPE_SYMBOL_OR_OFF_SESSION_DIAGNOSTIC"
        next_route = "mechanism_import_only_no_gtos_replay_priority"
    else:
        scope_bucket = "OUT_OF_SCOPE_SYMBOL_DIAGNOSTIC"
        next_route = "mechanism_import_only_no_gtos_replay_priority"

    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_class": "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE",
        "route_candidate_id": row["route_candidate_id"],
        "symbol": symbol,
        "session": session,
        "mapped_kill_zone": mapped_kz,
        "configured_sessions": sorted(configured_sessions.keys()),
        "current_fleet_symbol": current_fleet,
        "observer_only_symbol": observer_only,
        "configured_session_match": configured_session_match,
        "scope_bucket": scope_bucket,
        "next_route": next_route,
        "primitive_family": row["primitive_family"],
        "primitive_id": row["primitive_id"],
        "horizon_bars": row["horizon_bars"],
        "event_count": row["event_count"],
        "cluster_count": row["cluster_count"],
        "cluster_effective_ratio": row["cluster_effective_ratio"],
        "cluster_weighted_mean_directional_close_units": row[
            "cluster_weighted_mean_directional_close_units"
        ],
        "cluster_weighted_directional_positive_share": row[
            "cluster_weighted_directional_positive_share"
        ],
        "audit_bucket": row["audit_bucket"],
        "required_next_controls": [
            "purged train/test or frozen forward route",
            "cost/fill model before strategy projection",
            "instrument-specific session and spread eligibility",
            "owner approval before any live behavior change",
        ],
        "safe_flags": SAFE_FLAGS,
    }


def write_summary(result: dict[str, Any], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Historical OHLC GTOS Scope Triage",
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
    lines.extend(["", "## Scope Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Immediate replay queue rows are research candidates only.",
            "- Current-symbol off-session rows are not live-trade candidates.",
            "- Backtest-only configured symbols require source-transfer proof before reuse.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rows = [triage_row(row) for row in read_jsonl(INPUT_PATH)]
    bucket_counts = Counter(row["scope_bucket"] for row in rows)
    immediate = [row for row in rows if row["scope_bucket"] == "GTOS_IMMEDIATE_REPLAY_CANDIDATE"]
    transfer = [
        row
        for row in rows
        if row["scope_bucket"]
        in {
            "CONFIGURED_BACKTEST_ONLY_SOURCE_TRANSFER_CANDIDATE",
            "CURRENT_SYMBOL_OUTSIDE_CONFIGURED_SESSION",
        }
    ]

    write_jsonl(LEDGER_PATH, rows)
    write_jsonl(IMMEDIATE_QUEUE_PATH, immediate)
    write_jsonl(TRANSFER_QUEUE_PATH, transfer)

    result = {
        "schema": "historical_ohlc_gtos_scope_triage_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_GTOS_SCOPE_TRIAGE",
        "claim_boundary": CLAIM_BOUNDARY,
        "parameters": {
            "input": "all rows from HISTORICAL_OHLC_SURVIVOR_CLUSTER_ROUTE_QUEUE; no top-N cap",
            "session_mapping": SESSION_TO_KZ,
            "current_fleet_symbols": sorted(CURRENT_FLEET_SYMBOLS),
            "observer_only_symbols": sorted(OBSERVER_ONLY_SYMBOLS),
            "kill_zone_source": "src.research_infra.stratification.DEFAULT_KILL_ZONES",
        },
        "counts": {
            "input_cluster_resilient_rows": len(rows),
            "triage_rows": len(rows),
            "immediate_replay_queue_rows": len(immediate),
            "source_transfer_queue_rows": len(transfer),
        },
        "scope_bucket_counts": dict(sorted(bucket_counts.items())),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, bucket_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
