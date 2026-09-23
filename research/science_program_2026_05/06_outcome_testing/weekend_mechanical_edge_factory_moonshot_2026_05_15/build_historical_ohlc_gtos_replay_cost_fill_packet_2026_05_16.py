#!/usr/bin/env python3
"""Build historical OHLC GTOS replay cost/fill packet.

This packet consumes the OHLC challenger frontier and GTOS replay contracts,
preserves the full frontier denominator, joins the 6 frozen replay contracts
to their discovery events, and expands them into frozen entry/cost/fill proxy
grids. It is source/control evidence only: no validation, R/PnL, expectancy,
win-rate, live-readiness, promotion, or live behavior change is claimed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

FRONTIER_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl"
FRONTIER_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl"
REPLAY_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONTRACT_LEDGER_2026-05-15.jsonl"
CLUSTER_BINDING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CLUSTER_BINDING_LEDGER_2026-05-15.jsonl"
BLOCKER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER_LEDGER_2026-05-15.jsonl"
PRIMITIVE_EVENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl"
SLIPPAGE_PATH = REPO / "shadow_logs" / "slippage.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_RESULT_2026-05-16.json"
ROUTE_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ROUTE_STATUS_LEDGER_2026-05-16.jsonl"
TARGET_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_TARGET_ACTION_LEDGER_2026-05-16.jsonl"
TARGET_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_TARGET_CONTRACT_LEDGER_2026-05-16.jsonl"
EVENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_EVENT_LEDGER_2026-05-16.jsonl"
ENTRY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ENTRY_VARIANT_LEDGER_2026-05-16.jsonl"
COST_PROXY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_COST_PROXY_LEDGER_2026-05-16.jsonl"
COST_FILL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_GRID_LEDGER_2026-05-16.jsonl"
BLOCKER_RESOLUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_BLOCKER_RESOLUTION_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

TARGET_STATUS = "OHLC_FRONTIER_GTOS_REPLAY_CONTRACT_READY_SOURCE_REPLAY_AND_COST_FILL"
ENTRY_VARIANTS = [
    "SIGNAL_CLOSE_MARKET_PROXY",
    "NEXT_BAR_OPEN_MARKET_PROXY",
    "BODY_MID_RETEST_LIMIT_PROXY",
    "SWEEP_WICK_EXTREME_RETEST_PROXY",
]
COST_MODELS = [
    "ZERO_COST_CONTROL",
    "SYMBOL_MEDIAN_SPREAD_PROXY",
    "SYMBOL_MAX_SPREAD_PROXY",
    "STATIC_CONSERVATIVE_FALLBACK_PROXY",
]
STATIC_SPREAD_FALLBACK = {
    "GBPJPY": 1.5,
    "XAUUSD": 60.0,
}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay/cost-fill projection packet only. Rows are "
    "source-bound discovery events, frozen entry variants, and proxy cost/fill "
    "inputs; no validation, R/PnL, expectancy, win-rate, live-readiness, "
    "promotion, or live behavior change is claimed."
)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        FRONTIER_ROUTE_PATH,
        FRONTIER_ACTION_PATH,
        REPLAY_CONTRACT_PATH,
        CLUSTER_BINDING_PATH,
        BLOCKER_PATH,
        PRIMITIVE_EVENT_PATH,
        REPO / "data" / "historical_2026" / "GBPJPY_M15.csv",
        REPO / "data" / "historical_2026" / "XAUUSD_M15.csv",
        SLIPPAGE_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "status": "HASHED",
                }
            )
        else:
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                    "status": "MISSING_FAIL_CLOSED",
                }
            )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def numeric(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def event_key(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(row.get("symbol")),
        str(row.get("session")),
        str(row.get("primitive_id")),
        int(row.get("horizon_bars") or 0),
    )


def load_m15_bars(symbol: str) -> dict[str, dict[str, Any]]:
    path = REPO / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for raw in csv.DictReader(handle):
            iso = raw["time"].replace(" ", "T") + "Z"
            rows.append(
                {
                    "time_utc": iso,
                    "open": numeric(raw.get("open")),
                    "high": numeric(raw.get("high")),
                    "low": numeric(raw.get("low")),
                    "close": numeric(raw.get("close")),
                    "volume": numeric(raw.get("volume")),
                }
            )
    by_time: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        next_row = rows[index + 1] if index + 1 < len(rows) else None
        enriched = dict(row)
        if next_row:
            enriched["next_time_utc"] = next_row["time_utc"]
            enriched["next_open"] = next_row["open"]
        else:
            enriched["next_time_utc"] = None
            enriched["next_open"] = None
        by_time[row["time_utc"]] = enriched
    return by_time


def slippage_spread_proxy() -> dict[str, dict[str, Any]]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in read_jsonl(SLIPPAGE_PATH):
        if row.get("_parse_error"):
            continue
        value = numeric(row.get("spread_at_request"))
        symbol = row.get("symbol")
        if symbol and value is not None and value >= 0:
            values[symbol].append(value)
    proxies: dict[str, dict[str, Any]] = {}
    for symbol in set(values) | set(STATIC_SPREAD_FALLBACK):
        series = values.get(symbol, [])
        proxies[symbol] = {
            "symbol": symbol,
            "observed_spread_count": len(series),
            "observed_spread_median": rounded(statistics.median(series)) if series else None,
            "observed_spread_max": rounded(max(series)) if series else None,
            "static_fallback_spread": STATIC_SPREAD_FALLBACK.get(symbol),
        }
    return proxies


def cost_value(symbol: str, model: str, proxy: dict[str, dict[str, Any]]) -> tuple[float, str]:
    row = proxy.get(symbol, {})
    if model == "ZERO_COST_CONTROL":
        return 0.0, "ZERO_COST_CONTROL"
    if model == "SYMBOL_MEDIAN_SPREAD_PROXY" and row.get("observed_spread_median") is not None:
        return float(row["observed_spread_median"]), "OBSERVED_SLIPPAGE_LOG_SYMBOL_MEDIAN_SPREAD"
    if model == "SYMBOL_MAX_SPREAD_PROXY" and row.get("observed_spread_max") is not None:
        return float(row["observed_spread_max"]), "OBSERVED_SLIPPAGE_LOG_SYMBOL_MAX_SPREAD"
    return float(row.get("static_fallback_spread") or 0.0), "STATIC_SYMBOL_FALLBACK_SPREAD"


def side_from_contract(contract: dict[str, Any]) -> str:
    return "SHORT" if contract.get("expected_direction_context") == "short_context" else "LONG"


def entry_price_for_variant(variant: str, side: str, bar: dict[str, Any]) -> tuple[float | None, str]:
    if variant == "SIGNAL_CLOSE_MARKET_PROXY":
        return rounded(numeric(bar.get("close"))), "signal_bar_close"
    if variant == "NEXT_BAR_OPEN_MARKET_PROXY":
        return rounded(numeric(bar.get("next_open"))), "next_bar_open"
    if variant == "BODY_MID_RETEST_LIMIT_PROXY":
        open_price = numeric(bar.get("open"))
        close_price = numeric(bar.get("close"))
        if open_price is None or close_price is None:
            return None, "body_mid_missing_ohlc"
        return rounded((open_price + close_price) / 2.0), "signal_body_mid"
    if variant == "SWEEP_WICK_EXTREME_RETEST_PROXY":
        if side == "LONG":
            return rounded(numeric(bar.get("low"))), "signal_bar_low"
        return rounded(numeric(bar.get("high"))), "signal_bar_high"
    return None, "unknown_variant"


def fill_proxy_status(variant: str, entry_price: float | None, bar: dict[str, Any]) -> str:
    if entry_price is None:
        return "ENTRY_PROXY_PRICE_MISSING_FAIL_CLOSED"
    if variant in {"SIGNAL_CLOSE_MARKET_PROXY", "NEXT_BAR_OPEN_MARKET_PROXY"}:
        return "MARKET_PROXY_FILLED_BY_CONSTRUCTION_INPUT_ONLY"
    high = numeric(bar.get("high"))
    low = numeric(bar.get("low"))
    if high is None or low is None:
        return "OHLC_RANGE_MISSING_FAIL_CLOSED"
    if low <= entry_price <= high:
        return "LIMIT_PROXY_INSIDE_SIGNAL_BAR_OHLC_RANGE"
    return "LIMIT_PROXY_OUTSIDE_SIGNAL_BAR_RANGE_FAIL_CLOSED"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_cost_fill_packet",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_cost_fill_packet",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    route_rows = [row for row in read_jsonl(FRONTIER_ROUTE_PATH) if not row.get("_parse_error")]
    action_rows = [row for row in read_jsonl(FRONTIER_ACTION_PATH) if not row.get("_parse_error")]
    contract_rows = [row for row in read_jsonl(REPLAY_CONTRACT_PATH) if not row.get("_parse_error")]
    cluster_rows = [row for row in read_jsonl(CLUSTER_BINDING_PATH) if not row.get("_parse_error")]
    blocker_rows = [row for row in read_jsonl(BLOCKER_PATH) if not row.get("_parse_error")]

    target_route_ids = {row["route_candidate_id"] for row in contract_rows}
    target_route_rows = [row for row in route_rows if row.get("route_candidate_id") in target_route_ids]
    target_action_rows = [row for row in action_rows if row.get("route_candidate_id") in target_route_ids]
    contract_by_key = {event_key(row): row for row in contract_rows}
    contract_by_route = {row["route_candidate_id"]: row for row in contract_rows}
    bars_by_symbol = {symbol: load_m15_bars(symbol) for symbol in {row["symbol"] for row in contract_rows}}
    spread_proxy = slippage_spread_proxy()

    route_status_rows: list[dict[str, Any]] = []
    for row in route_rows:
        route_status_rows.append(
            {
                **row,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ROUTE_STATUS",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                "target_replay_member": row.get("route_candidate_id") in target_route_ids,
            }
        )

    target_contract_rows: list[dict[str, Any]] = []
    for row in contract_rows:
        target_contract_rows.append(
            {
                **row,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_TARGET_CONTRACT",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                "contract_scope": "DISCOVERY_SOURCE_REPLAY_AND_COST_FILL_INPUT_ONLY",
            }
        )

    target_action_out_rows = [
        {
            **row,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_TARGET_ACTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "source_manifest_hash": manifest_hash,
            "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
        }
        for row in target_action_rows
    ]

    primitive_events: list[dict[str, Any]] = []
    for row in read_jsonl(PRIMITIVE_EVENT_PATH):
        if row.get("_parse_error"):
            continue
        contract = contract_by_key.get(event_key(row))
        if not contract:
            continue
        primitive_events.append((row, contract))  # type: ignore[arg-type]

    event_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    cost_proxy_rows: list[dict[str, Any]] = []
    cost_fill_rows: list[dict[str, Any]] = []
    entry_counter = 0
    cost_fill_counter = 0

    for symbol in sorted({row["symbol"] for row in contract_rows}):
        for model in COST_MODELS:
            value, source = cost_value(symbol, model, spread_proxy)
            cost_proxy_rows.append(
                {
                    "cost_model": model,
                    "symbol": symbol,
                    "spread_proxy_value": rounded(value),
                    "spread_proxy_source": source,
                    "observed_spread_count": spread_proxy.get(symbol, {}).get("observed_spread_count", 0),
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_COST_PROXY",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                    "source_manifest_hash": manifest_hash,
                    "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                }
            )

    for event_index, pair in enumerate(primitive_events, 1):
        event, contract = pair  # type: ignore[misc]
        side = side_from_contract(contract)
        bar = bars_by_symbol.get(event["symbol"], {}).get(event["time_utc"], {})
        event_id = f"OHLC-GTOS-REPLAY-EVENT-{event_index:05d}"
        event_rows.append(
            {
                "event_id": event_id,
                "route_candidate_id": contract["route_candidate_id"],
                "frozen_rule_id": contract["frozen_rule_id"],
                "symbol": event.get("symbol"),
                "session": event.get("session"),
                "primitive_id": event.get("primitive_id"),
                "primitive_family": event.get("primitive_family"),
                "horizon_bars": event.get("horizon_bars"),
                "time_utc": event.get("time_utc"),
                "date": event.get("date"),
                "expected_direction_context": contract.get("expected_direction_context"),
                "side": side,
                "source_bar_status": "M15_BAR_JOINED" if bar else "M15_BAR_MISSING_FAIL_CLOSED",
                "contamination_status": "DISCOVERY_WINDOW_EVENT_NOT_VALIDATION",
                "descriptor_units_preserved": {
                    "directional_close_units": event.get("directional_close_units"),
                    "directional_favorable_excursion_units": event.get("directional_favorable_excursion_units"),
                    "directional_adverse_excursion_units": event.get("directional_adverse_excursion_units"),
                },
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_EVENT",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
        )
        for variant in ENTRY_VARIANTS:
            entry_counter += 1
            entry_price, entry_source = entry_price_for_variant(variant, side, bar)
            fill_status = fill_proxy_status(variant, entry_price, bar)
            entry_id = f"OHLC-GTOS-REPLAY-ENTRY-{entry_counter:05d}"
            entry_row = {
                "entry_variant_id": entry_id,
                "event_id": event_id,
                "route_candidate_id": contract["route_candidate_id"],
                "symbol": event.get("symbol"),
                "side": side,
                "entry_variant": variant,
                "entry_price_input_only": entry_price,
                "entry_price_source": entry_source,
                "fill_proxy_status": fill_status,
                "time_utc": event.get("time_utc"),
                "next_time_utc": bar.get("next_time_utc"),
                "signal_bar_open": bar.get("open"),
                "signal_bar_high": bar.get("high"),
                "signal_bar_low": bar.get("low"),
                "signal_bar_close": bar.get("close"),
                "next_bar_open": bar.get("next_open"),
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ENTRY_VARIANT",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
            entry_rows.append(entry_row)
            for model in COST_MODELS:
                cost_fill_counter += 1
                value, source = cost_value(str(event.get("symbol")), model, spread_proxy)
                cost_fill_rows.append(
                    {
                        "cost_fill_id": f"OHLC-GTOS-REPLAY-COSTFILL-{cost_fill_counter:05d}",
                        "entry_variant_id": entry_id,
                        "event_id": event_id,
                        "route_candidate_id": contract["route_candidate_id"],
                        "symbol": event.get("symbol"),
                        "side": side,
                        "entry_variant": variant,
                        "cost_model": model,
                        "entry_price_input_only": entry_price,
                        "spread_proxy_value": rounded(value),
                        "spread_proxy_source": source,
                        "fill_proxy_status": fill_status,
                        "projection_role": "ENTRY_COST_FILL_INPUT_GRID_ONLY_NO_OUTCOME_SCORE",
                        "contamination_status": "DISCOVERY_WINDOW_EVENT_NOT_VALIDATION",
                        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_GRID",
                        "claim_boundary": CLAIM_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                        "source_manifest_hash": manifest_hash,
                        "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                    }
                )

    blocker_resolution_rows: list[dict[str, Any]] = []
    for row in blocker_rows:
        blocker_id = row.get("blocker_id")
        if blocker_id == "future_or_sealed_holdout_required_after_discovery_window":
            proxy_status = "DISCOVERY_WINDOW_CONTAMINATION_LABELED_NOT_VALIDATION"
        elif blocker_id == "entry_geometry_not_defined_by_ohlc_primitive":
            proxy_status = "ENTRY_VARIANT_GRID_MATERIALIZED_SOURCE_SAFE"
        elif blocker_id == "spread_slippage_commission_not_applied":
            proxy_status = "COST_PROXY_GRID_MATERIALIZED_WITH_EXACT_GAP_LABELS"
        elif blocker_id == "pending_lifecycle_fillability_not_modeled":
            proxy_status = "FILL_PROXY_GRID_MATERIALIZED_OHLC_ONLY"
        else:
            proxy_status = "NO_LIVE_BEHAVIOR_CHANGE_RETAINED"
        blocker_resolution_rows.append(
            {
                **row,
                "proxy_resolution_status": proxy_status,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_BLOCKER_RESOLUTION",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
        )

    bucket_axes = {
        "frontier_status": Counter(row.get("frontier_status") for row in route_rows),
        "target_route_event_count": Counter({route_id: sum(1 for row in event_rows if row["route_candidate_id"] == route_id) for route_id in target_route_ids}),
        "entry_variant": Counter(row["entry_variant"] for row in entry_rows),
        "cost_model": Counter(row["cost_model"] for row in cost_fill_rows),
        "fill_proxy_status": Counter(row["fill_proxy_status"] for row in entry_rows),
        "blocker_proxy_resolution_status": Counter(row["proxy_resolution_status"] for row in blocker_resolution_rows),
    }
    bucket_rows: list[dict[str, Any]] = []
    for axis, counter in bucket_axes.items():
        for bucket, count in sorted(counter.items()):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": bucket,
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_BUCKET",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

    question_rows: list[dict[str, Any]] = [
        {
            "question_id": "OHLC-GTOS-REPLAY-COST-FILL-QUESTION-001",
            "question": "Which entry variant deserves source-safe replay against target/stop/fill paths?",
            "row_count": len(entry_rows),
            "next_same_resource_action": "join entry grid to source-safe target/stop path controls without claiming validation",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "question_id": "OHLC-GTOS-REPLAY-COST-FILL-QUESTION-002",
            "question": "Which cost proxy changes survivorship of source-safe entry/fill candidates?",
            "row_count": len(cost_fill_rows),
            "next_same_resource_action": "stress cost grid against source-safe target/stop path controls and preserve every cost model",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "question_id": "OHLC-GTOS-REPLAY-COST-FILL-QUESTION-003",
            "question": "Which blockers remain exact gaps after proxy materialization?",
            "row_count": len(blocker_resolution_rows),
            "next_same_resource_action": "convert remaining exact gaps into source acquisition or same-resource proxy packets",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_QUESTION",
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
    ]

    counts = {
        "blocker_resolution_rows": len(blocker_resolution_rows),
        "bucket_rows": len(bucket_rows),
        "cluster_binding_rows_consumed": len(cluster_rows),
        "cost_fill_grid_rows": len(cost_fill_rows),
        "cost_proxy_rows": len(cost_proxy_rows),
        "entry_variant_rows": len(entry_rows),
        "question_rows": len(question_rows),
        "route_status_rows": len(route_status_rows),
        "source_manifest_rows": len(manifest_rows),
        "target_action_rows": len(target_action_out_rows),
        "target_contract_rows": len(target_contract_rows),
        "target_event_rows": len(event_rows),
    }
    result = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_cost_fill_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This replay/cost-fill packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "frontier_status_counts": dict(sorted(bucket_axes["frontier_status"].items())),
        "target_route_event_counts": dict(sorted(bucket_axes["target_route_event_count"].items())),
        "entry_variant_counts": dict(sorted(bucket_axes["entry_variant"].items())),
        "cost_model_counts": dict(sorted(bucket_axes["cost_model"].items())),
        "fill_proxy_status_counts": dict(sorted(bucket_axes["fill_proxy_status"].items())),
        "blocker_proxy_resolution_status_counts": dict(sorted(bucket_axes["blocker_proxy_resolution_status"].items())),
        "entry_variant_count_per_event": len(ENTRY_VARIANTS),
        "cost_model_count_per_entry": len(COST_MODELS),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "join cost/fill grid to source-safe target/stop path controls",
            "split replay contracts by cluster binding and date concentration",
            "route remaining exact spread/slippage/fill gaps into owned/current/free source acquisition or proxy stress",
            "compare OHLC replay controls against no-fill and Route C challenger families",
        ],
    }

    write_jsonl(ROUTE_STATUS_PATH, route_status_rows)
    write_jsonl(TARGET_ACTION_PATH, target_action_out_rows)
    write_jsonl(TARGET_CONTRACT_PATH, target_contract_rows)
    write_jsonl(EVENT_PATH, event_rows)
    write_jsonl(ENTRY_VARIANT_PATH, entry_rows)
    write_jsonl(COST_PROXY_PATH, cost_proxy_rows)
    write_jsonl(COST_FILL_PATH, cost_fill_rows)
    write_jsonl(BLOCKER_RESOLUTION_PATH, blocker_resolution_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Cost/Fill Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet preserves the full OHLC frontier denominator and materializes source-safe replay/cost/fill input grids for the 6 GTOS replay contracts.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Target Route Event Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(bucket_axes["target_route_event_count"].items())),
                "",
                "## Immediate Work",
                "",
                "- Join cost/fill grid to source-safe target/stop path controls.",
                "- Split replay contracts by cluster binding and date concentration.",
                "- Route exact spread/slippage/fill gaps into owned/current/free source acquisition or proxy stress.",
                "- Compare OHLC replay controls against no-fill and Route C challenger families.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": counts, "target_route_event_counts": result["target_route_event_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
