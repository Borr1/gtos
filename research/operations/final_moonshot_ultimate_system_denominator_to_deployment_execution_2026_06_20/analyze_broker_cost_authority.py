#!/usr/bin/env python3
"""Summarize broker-calibrated replay cost versus old timewarp proxy cost."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE = Path(__file__).resolve().parent


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for attempt in range(6):
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)
            return
        except TimeoutError:
            if attempt >= 5:
                raise
            time.sleep(0.25 * (attempt + 1))


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def group_key(row: Mapping[str, Any], ledger: str) -> tuple[str, ...]:
    return (
        ledger,
        str(row.get("broad_replay_profile") or row.get("profile") or "unknown"),
        str(row.get("split") or "unknown"),
        str(row.get("symbol") or "unknown"),
        str(row.get("session_bucket") or row.get("route_session") or row.get("session") or "unknown"),
        str(row.get("side") or "unknown"),
        str(row.get("framework") or row.get("current_framework") or "unknown"),
        str(row.get("cost_quote_source") or "unknown"),
    )


def update_stat(stat: dict[str, Any], row: Mapping[str, Any]) -> None:
    old_cost = safe_float(row.get("candidate_cost_r_fallback_diagnostic"))
    broker_cost = safe_float(
        row.get("broker_calibrated_expected_cost_r"),
        safe_float(row.get("expected_cost_r")),
    )
    replay_expected_cost = safe_float(row.get("expected_cost_r"), broker_cost)
    delta = safe_float(row.get("old_proxy_vs_broker_calibrated_delta_r"), broker_cost - old_cost)
    stat["row_count"] += 1
    stat["old_proxy_cost_r_sum"] += old_cost
    stat["broker_calibrated_cost_r_sum"] += broker_cost
    stat["replay_expected_cost_r_sum"] += replay_expected_cost
    stat["broker_minus_old_proxy_cost_r_sum"] += delta
    stat["replay_expected_minus_old_proxy_cost_r_sum"] += replay_expected_cost - old_cost
    stat["replay_expected_minus_broker_calibrated_cost_r_sum"] += (
        replay_expected_cost - broker_cost
    )
    if row.get("candidate_cost_r_fallback_is_authority") is True:
        stat["old_proxy_authority_row_count"] += 1
    if row.get("symbol_specific_untradeable_cost_floor") is True:
        stat["symbol_specific_untradeable_cost_floor_row_count"] += 1
    status = str(row.get("pretrade_cost_packet_status") or "unknown")
    stat["pretrade_cost_packet_status_counts"][status] += 1
    if row.get("cost_quote_source"):
        stat["cost_quote_source_counts"][str(row.get("cost_quote_source"))] += 1
    final_r = row.get("final_r")
    net_r = row.get("net_proxy_r", row.get("net_r"))
    if final_r not in (None, ""):
        gross = safe_float(final_r)
        stat["gross_r_sum"] += gross
        stat["filled_trade_count"] += 1
        if gross > 0:
            stat["win_count"] += 1
        elif gross < 0:
            stat["loss_count"] += 1
        else:
            stat["flat_count"] += 1
    if net_r not in (None, ""):
        stat["net_r_sum"] += safe_float(net_r)


def finalize_stat(key: tuple[str, ...], stat: dict[str, Any]) -> dict[str, Any]:
    (
        ledger,
        profile,
        split,
        symbol,
        session,
        side,
        framework,
        cost_quote_source,
    ) = key
    count = max(1, int(stat["row_count"]))
    return {
        "ledger": ledger,
        "broad_replay_profile": profile,
        "split": split,
        "symbol": symbol,
        "session": session,
        "side": side,
        "framework": framework,
        "cost_quote_source": cost_quote_source,
        "row_count": stat["row_count"],
        "old_proxy_authority_row_count": stat["old_proxy_authority_row_count"],
        "symbol_specific_untradeable_cost_floor_row_count": stat[
            "symbol_specific_untradeable_cost_floor_row_count"
        ],
        "old_proxy_cost_r_sum": round(stat["old_proxy_cost_r_sum"], 9),
        "broker_calibrated_cost_r_sum": round(stat["broker_calibrated_cost_r_sum"], 9),
        "replay_expected_cost_r_sum": round(stat["replay_expected_cost_r_sum"], 9),
        "broker_minus_old_proxy_cost_r_sum": round(
            stat["broker_minus_old_proxy_cost_r_sum"],
            9,
        ),
        "replay_expected_minus_old_proxy_cost_r_sum": round(
            stat["replay_expected_minus_old_proxy_cost_r_sum"],
            9,
        ),
        "replay_expected_minus_broker_calibrated_cost_r_sum": round(
            stat["replay_expected_minus_broker_calibrated_cost_r_sum"],
            9,
        ),
        "old_proxy_cost_r_avg": round(stat["old_proxy_cost_r_sum"] / count, 9),
        "broker_calibrated_cost_r_avg": round(
            stat["broker_calibrated_cost_r_sum"] / count,
            9,
        ),
        "replay_expected_cost_r_avg": round(
            stat["replay_expected_cost_r_sum"] / count,
            9,
        ),
        "broker_minus_old_proxy_cost_r_avg": round(
            stat["broker_minus_old_proxy_cost_r_sum"] / count,
            9,
        ),
        "replay_expected_minus_old_proxy_cost_r_avg": round(
            stat["replay_expected_minus_old_proxy_cost_r_sum"] / count,
            9,
        ),
        "replay_expected_minus_broker_calibrated_cost_r_avg": round(
            stat["replay_expected_minus_broker_calibrated_cost_r_sum"] / count,
            9,
        ),
        "filled_trade_count": stat["filled_trade_count"],
        "win_count": stat["win_count"],
        "loss_count": stat["loss_count"],
        "flat_count": stat["flat_count"],
        "gross_r_sum": round(stat["gross_r_sum"], 9),
        "net_r_sum": round(stat["net_r_sum"], 9),
        "pretrade_cost_packet_status_counts": dict(
            sorted(stat["pretrade_cost_packet_status_counts"].items())
        ),
        "cost_quote_source_counts": dict(sorted(stat["cost_quote_source_counts"].items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    prefix = str(args.prefix)
    ledger_paths = {
        "candidate": ROUTE / f"{prefix}_CANDIDATE_LEDGER.jsonl",
        "trade": ROUTE / f"{prefix}_TRADE_LEDGER.jsonl",
        "missed": ROUTE / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "order": ROUTE / f"{prefix}_ORDER_LEDGER.jsonl",
    }
    grouped: dict[tuple[str, ...], dict[str, Any]] = defaultdict(
        lambda: {
            "row_count": 0,
            "old_proxy_authority_row_count": 0,
            "symbol_specific_untradeable_cost_floor_row_count": 0,
            "old_proxy_cost_r_sum": 0.0,
            "broker_calibrated_cost_r_sum": 0.0,
            "replay_expected_cost_r_sum": 0.0,
            "broker_minus_old_proxy_cost_r_sum": 0.0,
            "replay_expected_minus_old_proxy_cost_r_sum": 0.0,
            "replay_expected_minus_broker_calibrated_cost_r_sum": 0.0,
            "filled_trade_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "flat_count": 0,
            "gross_r_sum": 0.0,
            "net_r_sum": 0.0,
            "pretrade_cost_packet_status_counts": defaultdict(int),
            "cost_quote_source_counts": defaultdict(int),
        }
    )
    input_counts: dict[str, int] = {}
    for ledger, path in ledger_paths.items():
        count = 0
        for row in read_jsonl(path):
            count += 1
            if row.get("broker_calibrated_expected_cost_r") is None:
                continue
            update_stat(grouped[group_key(row, ledger)], row)
        input_counts[ledger] = count
    rows = [finalize_stat(key, stat) for key, stat in grouped.items()]
    rows.sort(
        key=lambda row: (
            row["ledger"],
            row["broad_replay_profile"],
            row["split"],
            row["symbol"],
            row["session"],
            row["side"],
            row["framework"],
            row["cost_quote_source"],
        )
    )
    summary_by_ledger: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "group_count": 0,
            "row_count": 0,
            "old_proxy_cost_r_sum": 0.0,
            "broker_calibrated_cost_r_sum": 0.0,
            "replay_expected_cost_r_sum": 0.0,
            "broker_minus_old_proxy_cost_r_sum": 0.0,
            "replay_expected_minus_old_proxy_cost_r_sum": 0.0,
            "replay_expected_minus_broker_calibrated_cost_r_sum": 0.0,
            "filled_trade_count": 0,
            "gross_r_sum": 0.0,
            "net_r_sum": 0.0,
        }
    )
    for row in rows:
        stat = summary_by_ledger[row["ledger"]]
        stat["group_count"] += 1
        for key in (
            "row_count",
            "old_proxy_cost_r_sum",
            "broker_calibrated_cost_r_sum",
            "replay_expected_cost_r_sum",
            "broker_minus_old_proxy_cost_r_sum",
            "replay_expected_minus_old_proxy_cost_r_sum",
            "replay_expected_minus_broker_calibrated_cost_r_sum",
            "filled_trade_count",
            "gross_r_sum",
            "net_r_sum",
        ):
            stat[key] += row[key]
    for stat in summary_by_ledger.values():
        for key, value in list(stat.items()):
            if isinstance(value, float):
                stat[key] = round(value, 9)
    ledger_path = ROUTE / f"{prefix}_COST_DELTA_LEDGER.jsonl"
    summary_path = ROUTE / f"{prefix}_COST_DELTA_SUMMARY.json"
    write_jsonl(ledger_path, rows)
    write_json(
        summary_path,
        {
            "schema": "gtos.final_moonshot.broker_cost_authority_delta.v1",
            "prefix": prefix,
            "status": "broker_cost_authority_delta_materialized",
            "input_counts": input_counts,
            "ledger_group_count": len(rows),
            "summary_by_ledger": dict(sorted(summary_by_ledger.items())),
            "artifacts": {
                "cost_delta_ledger": str(ledger_path),
                "cost_delta_summary": str(summary_path),
            },
            "broker_live_authority": False,
            "final_selection_claim": False,
        },
    )
    print(
        json.dumps(
            {
                "status": "broker_cost_authority_delta_materialized",
                "ledger_rows": len(rows),
                "summary": str(summary_path),
                "ledger": str(ledger_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
