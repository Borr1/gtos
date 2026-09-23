#!/usr/bin/env python3
"""Build historical OHLC GTOS replay target/stop path-control packet.

Consumes the replay cost/fill grid and adds source-safe M15 path descriptors:
post-signal fillability, target/stop touch ordering, same-bar ambiguity, and
cost sensitivity. This is discovery/source-control evidence only. It does not
claim validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or a
live behavior change.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

COST_FILL_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_RESULT_2026-05-16.json"
COST_FILL_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_GRID_LEDGER_2026-05-16.jsonl"
COST_FILL_EVENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_EVENT_LEDGER_2026-05-16.jsonl"
ENTRY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ENTRY_VARIANT_LEDGER_2026-05-16.jsonl"
PRIMITIVE_EVENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl"
SLIPPAGE_PATH = REPO / "shadow_logs" / "slippage.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_RESULT_2026-05-16.json"
COST_FILL_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"
PATH_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_GRID_LEDGER_2026-05-16.jsonl"
EVENT_DESCRIPTOR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_EVENT_DESCRIPTOR_LEDGER_2026-05-16.jsonl"
AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

TARGET_MULTIPLES = [0.5, 1.0, 1.5, 2.0]
STOP_MULTIPLES = [0.5, 1.0, 1.5, 2.0]
SPREAD_TO_PRICE_DIVISOR = 100.0

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay path-control packet only. Rows are M15 "
    "source-path descriptors, post-signal fillability proxies, target/stop "
    "touch-order controls, and ambiguity labels; no validation, R/PnL, "
    "expectancy, win-rate, live-readiness, promotion, or live behavior change "
    "is claimed."
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
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


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
        COST_FILL_RESULT_PATH,
        COST_FILL_GRID_PATH,
        COST_FILL_EVENT_PATH,
        ENTRY_VARIANT_PATH,
        PRIMITIVE_EVENT_PATH,
        REPO / "data" / "historical_2026" / "GBPJPY_M15.csv",
        REPO / "data" / "historical_2026" / "XAUUSD_M15.csv",
        SLIPPAGE_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
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


def event_join_key(row: dict[str, Any]) -> tuple[str, str, str, int, str]:
    return (
        str(row.get("symbol")),
        str(row.get("session")),
        str(row.get("primitive_id")),
        int(row.get("horizon_bars") or 0),
        str(row.get("time_utc")),
    )


def load_m15_bars(symbol: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    path = REPO / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows, {}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "time_utc": raw["time"].replace(" ", "T") + "Z",
                    "open": numeric(raw.get("open")),
                    "high": numeric(raw.get("high")),
                    "low": numeric(raw.get("low")),
                    "close": numeric(raw.get("close")),
                    "volume": numeric(raw.get("volume")),
                }
            )
    by_time = {row["time_utc"]: idx for idx, row in enumerate(rows)}
    return rows, by_time


def side_sign(side: str) -> int:
    return -1 if str(side).upper() == "SHORT" else 1


def spread_price_distance(spread_proxy_value: float | None) -> float | None:
    if spread_proxy_value is None:
        return None
    return spread_proxy_value / SPREAD_TO_PRICE_DIVISOR


def effective_entry(entry_price: float | None, spread_distance: float | None, side: str) -> float | None:
    if entry_price is None or spread_distance is None:
        return None
    sign = side_sign(side)
    return entry_price + sign * spread_distance


def future_window(
    bars: list[dict[str, Any]],
    bar_index: int | None,
    horizon_bars: int,
) -> list[tuple[int, dict[str, Any]]]:
    if bar_index is None:
        return []
    output: list[tuple[int, dict[str, Any]]] = []
    for offset in range(1, horizon_bars + 1):
        idx = bar_index + offset
        if idx >= len(bars):
            break
        output.append((offset, bars[idx]))
    return output


def price_touched(bar: dict[str, Any], price: float | None) -> bool:
    high = numeric(bar.get("high"))
    low = numeric(bar.get("low"))
    if price is None or high is None or low is None:
        return False
    return low <= price <= high


def first_fill_offset(
    entry_variant: str,
    entry_price: float | None,
    future: list[tuple[int, dict[str, Any]]],
) -> tuple[int | None, str]:
    if entry_price is None:
        return None, "ENTRY_PRICE_MISSING_FAIL_CLOSED"
    if entry_variant == "SIGNAL_CLOSE_MARKET_PROXY":
        return 0, "MARKET_PROXY_SIGNAL_CLOSE_PATH_STARTS_NEXT_BAR"
    if entry_variant == "NEXT_BAR_OPEN_MARKET_PROXY":
        return 1, "MARKET_PROXY_NEXT_OPEN_PATH_STARTS_NEXT_BAR"
    for offset, bar in future:
        if price_touched(bar, entry_price):
            return offset, "LIMIT_PROXY_POST_SIGNAL_RETOUCH_FOUND"
    return None, "LIMIT_PROXY_NOT_RETOUCHED_POST_SIGNAL_WITHIN_CONTRACT_HORIZON"


def path_after_fill(
    future: list[tuple[int, dict[str, Any]]],
    fill_offset: int | None,
) -> list[tuple[int, dict[str, Any]]]:
    if fill_offset is None:
        return []
    if fill_offset == 0:
        return future
    return [(offset, bar) for offset, bar in future if offset >= fill_offset]


def touch_status(
    side: str,
    target_price: float,
    stop_price: float,
    path: list[tuple[int, dict[str, Any]]],
) -> tuple[str, int | None, int | None, int | None]:
    target_offset: int | None = None
    stop_offset: int | None = None
    for offset, bar in path:
        high = numeric(bar.get("high"))
        low = numeric(bar.get("low"))
        if high is None or low is None:
            continue
        if side_sign(side) > 0:
            target_hit = high >= target_price
            stop_hit = low <= stop_price
        else:
            target_hit = low <= target_price
            stop_hit = high >= stop_price
        if target_hit and target_offset is None:
            target_offset = offset
        if stop_hit and stop_offset is None:
            stop_offset = offset
        if target_offset is not None and stop_offset is not None:
            break
    if target_offset is None and stop_offset is None:
        return "NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON", None, None, None
    if target_offset is not None and stop_offset is None:
        return "TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY", target_offset, None, target_offset
    if target_offset is None and stop_offset is not None:
        return "STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY", None, stop_offset, stop_offset
    if target_offset == stop_offset:
        return "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS", target_offset, stop_offset, target_offset
    if target_offset < stop_offset:
        return "TARGET_TOUCH_BEFORE_STOP_M15_PROXY", target_offset, stop_offset, target_offset
    return "STOP_TOUCH_BEFORE_TARGET_M15_PROXY", target_offset, stop_offset, stop_offset


def path_extremes(
    side: str,
    entry: float | None,
    unit: float | None,
    path: list[tuple[int, dict[str, Any]]],
) -> dict[str, Any]:
    if entry is None or unit is None or unit <= 0 or not path:
        return {
            "path_descriptor_status": "PATH_DESCRIPTOR_UNAVAILABLE_FAIL_CLOSED",
            "path_bar_count": len(path),
            "directional_close_units": None,
            "directional_favorable_excursion_units": None,
            "directional_adverse_excursion_units": None,
        }
    highs = [numeric(bar.get("high")) for _, bar in path if numeric(bar.get("high")) is not None]
    lows = [numeric(bar.get("low")) for _, bar in path if numeric(bar.get("low")) is not None]
    closes = [numeric(bar.get("close")) for _, bar in path if numeric(bar.get("close")) is not None]
    if not highs or not lows or not closes:
        return {
            "path_descriptor_status": "PATH_DESCRIPTOR_UNAVAILABLE_FAIL_CLOSED",
            "path_bar_count": len(path),
            "directional_close_units": None,
            "directional_favorable_excursion_units": None,
            "directional_adverse_excursion_units": None,
        }
    if side_sign(side) > 0:
        favorable = (max(highs) - entry) / unit
        adverse = (entry - min(lows)) / unit
        close_units = (closes[-1] - entry) / unit
    else:
        favorable = (entry - min(lows)) / unit
        adverse = (max(highs) - entry) / unit
        close_units = (entry - closes[-1]) / unit
    return {
        "path_descriptor_status": "PATH_DESCRIPTOR_COMPUTED_M15_OHLC",
        "path_bar_count": len(path),
        "directional_close_units": rounded(close_units),
        "directional_favorable_excursion_units": rounded(favorable),
        "directional_adverse_excursion_units": rounded(adverse),
    }


def target_stop_contract_rows(generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counter = 0
    for target_multiple in TARGET_MULTIPLES:
        for stop_multiple in STOP_MULTIPLES:
            counter += 1
            rows.append(
                {
                    "target_stop_contract_id": f"OHLC-GTOS-PATH-TARGETSTOP-{counter:03d}",
                    "target_multiple_of_rolling_median_range": target_multiple,
                    "stop_multiple_of_rolling_median_range": stop_multiple,
                    "unit_source": "primitive_event_rolling_median_range",
                    "path_source": "post_signal_m15_ohlc_until_frozen_contract_horizon",
                    "same_bar_ordering_policy": "same M15 target+stop touch is ambiguous, not ordered",
                    "generated_utc": generated_at,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "source_manifest_hash": manifest_hash,
                }
            )
    return rows


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_path_control_packet",
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
        "route": "historical_ohlc_gtos_replay_path_control_packet",
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
    cost_fill_result = read_json(COST_FILL_RESULT_PATH)
    cost_fill_rows = [row for row in read_jsonl(COST_FILL_GRID_PATH) if not row.get("_parse_error")]
    event_rows = [row for row in read_jsonl(COST_FILL_EVENT_PATH) if not row.get("_parse_error")]
    entry_rows = [row for row in read_jsonl(ENTRY_VARIANT_PATH) if not row.get("_parse_error")]
    primitive_rows = [row for row in read_jsonl(PRIMITIVE_EVENT_PATH) if not row.get("_parse_error")]

    event_by_id = {row["event_id"]: row for row in event_rows}
    entry_by_id = {row["entry_variant_id"]: row for row in entry_rows}
    primitive_by_key = {event_join_key(row): row for row in primitive_rows}
    target_contracts = target_stop_contract_rows(generated_at, manifest_hash)
    target_by_id = {row["target_stop_contract_id"]: row for row in target_contracts}

    symbols = sorted({str(row.get("symbol")) for row in cost_fill_rows if row.get("symbol")})
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    index_by_symbol_time: dict[str, dict[str, int]] = {}
    for symbol in symbols:
        bars, by_time = load_m15_bars(symbol)
        bars_by_symbol[symbol] = bars
        index_by_symbol_time[symbol] = by_time

    cost_status_rows: list[dict[str, Any]] = []
    event_descriptor_rows: list[dict[str, Any]] = []
    ambiguity_rows: list[dict[str, Any]] = []
    bucket_rows: list[dict[str, Any]] = []

    status_counter: Counter[str] = Counter()
    fill_status_counter: Counter[str] = Counter()
    first_touch_counter: Counter[str] = Counter()
    route_touch_counter: Counter[tuple[str, str]] = Counter()
    entry_touch_counter: Counter[tuple[str, str]] = Counter()
    cost_touch_counter: Counter[tuple[str, str]] = Counter()
    target_stop_touch_counter: Counter[tuple[str, str]] = Counter()
    event_descriptor_counter: Counter[str] = Counter()
    path_grid_count = 0
    ambiguous_count = 0

    with PATH_GRID_PATH.open("w", encoding="utf-8") as grid_handle:
        for cost_row in cost_fill_rows:
            event = event_by_id.get(str(cost_row.get("event_id")))
            entry = entry_by_id.get(str(cost_row.get("entry_variant_id")))
            primitive = primitive_by_key.get(event_join_key(event or {})) if event else None
            symbol = str(cost_row.get("symbol"))
            side = str(cost_row.get("side"))
            horizon_bars = int((event or {}).get("horizon_bars") or 0)
            source_time = str((event or {}).get("time_utc"))
            bar_index = index_by_symbol_time.get(symbol, {}).get(source_time)
            future = future_window(bars_by_symbol.get(symbol, []), bar_index, horizon_bars)
            entry_price = numeric(cost_row.get("entry_price_input_only"))
            spread_value = numeric(cost_row.get("spread_proxy_value"))
            spread_distance = spread_price_distance(spread_value)
            effective = effective_entry(entry_price, spread_distance, side)
            unit = numeric((primitive or {}).get("rolling_median_range"))
            fill_offset, fill_status = first_fill_offset(
                str(cost_row.get("entry_variant")),
                entry_price,
                future,
            )
            path = path_after_fill(future, fill_offset)
            descriptor = path_extremes(side, effective, unit, path)
            if not event:
                cost_status = "EVENT_ROW_MISSING_FAIL_CLOSED"
            elif not entry:
                cost_status = "ENTRY_ROW_MISSING_FAIL_CLOSED"
            elif not primitive:
                cost_status = "ROLLING_RANGE_SOURCE_MISSING_FAIL_CLOSED"
            elif bar_index is None:
                cost_status = "SOURCE_BAR_INDEX_MISSING_FAIL_CLOSED"
            elif len(future) < horizon_bars:
                cost_status = "FUTURE_WINDOW_TRUNCATED_FAIL_CLOSED"
            elif fill_offset is None:
                cost_status = "POST_SIGNAL_ENTRY_NOT_FILLED_WITHIN_HORIZON"
            elif effective is None or unit is None or unit <= 0:
                cost_status = "EFFECTIVE_ENTRY_OR_UNIT_MISSING_FAIL_CLOSED"
            else:
                cost_status = "PATH_CONTROL_READY_M15_OHLC"
            status_counter[cost_status] += 1
            fill_status_counter[fill_status] += 1
            event_descriptor_counter[descriptor["path_descriptor_status"]] += 1

            cost_status_rows.append(
                {
                    "cost_fill_id": cost_row.get("cost_fill_id"),
                    "entry_variant_id": cost_row.get("entry_variant_id"),
                    "event_id": cost_row.get("event_id"),
                    "route_candidate_id": cost_row.get("route_candidate_id"),
                    "symbol": symbol,
                    "side": side,
                    "entry_variant": cost_row.get("entry_variant"),
                    "cost_model": cost_row.get("cost_model"),
                    "entry_price_input_only": rounded(entry_price),
                    "spread_proxy_value": rounded(spread_value),
                    "spread_proxy_price_distance": rounded(spread_distance),
                    "effective_entry_price": rounded(effective),
                    "rolling_median_range": rounded(unit),
                    "horizon_bars": horizon_bars,
                    "source_time_utc": source_time,
                    "fill_offset_bars": fill_offset,
                    "fill_timing_status": fill_status,
                    "cost_path_status": cost_status,
                    "path_descriptor_status": descriptor["path_descriptor_status"],
                    "path_bar_count": descriptor["path_bar_count"],
                    "directional_close_units_after_cost": descriptor["directional_close_units"],
                    "directional_favorable_excursion_units_after_cost": descriptor[
                        "directional_favorable_excursion_units"
                    ],
                    "directional_adverse_excursion_units_after_cost": descriptor[
                        "directional_adverse_excursion_units"
                    ],
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                    "source_manifest_hash": manifest_hash,
                }
            )

            event_descriptor_rows.append(
                {
                    "cost_fill_id": cost_row.get("cost_fill_id"),
                    "event_id": cost_row.get("event_id"),
                    "route_candidate_id": cost_row.get("route_candidate_id"),
                    "symbol": symbol,
                    "side": side,
                    "cost_model": cost_row.get("cost_model"),
                    "entry_variant": cost_row.get("entry_variant"),
                    "fill_timing_status": fill_status,
                    "cost_path_status": cost_status,
                    **descriptor,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_EVENT_DESCRIPTOR",
                    "safe_flags": SAFE_FLAGS,
                    "source_manifest_hash": manifest_hash,
                }
            )

            for target_contract in target_contracts:
                path_grid_count += 1
                target_multiple = float(target_contract["target_multiple_of_rolling_median_range"])
                stop_multiple = float(target_contract["stop_multiple_of_rolling_median_range"])
                if cost_status != "PATH_CONTROL_READY_M15_OHLC" or effective is None or unit is None:
                    first_status = cost_status
                    target_price = None
                    stop_price = None
                    target_offset = None
                    stop_offset = None
                    first_touch_offset = None
                else:
                    sign = side_sign(side)
                    target_price = effective + sign * target_multiple * unit
                    stop_price = effective - sign * stop_multiple * unit
                    first_status, target_offset, stop_offset, first_touch_offset = touch_status(
                        side,
                        target_price,
                        stop_price,
                        path,
                    )
                first_touch_counter[first_status] += 1
                route_touch_counter[(str(cost_row.get("route_candidate_id")), first_status)] += 1
                entry_touch_counter[(str(cost_row.get("entry_variant")), first_status)] += 1
                cost_touch_counter[(str(cost_row.get("cost_model")), first_status)] += 1
                target_stop_touch_counter[(str(target_contract["target_stop_contract_id"]), first_status)] += 1
                if first_status == "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS":
                    ambiguous_count += 1
                    ambiguity_rows.append(
                        {
                            "path_control_id": f"OHLC-GTOS-PATH-CONTROL-{path_grid_count:06d}",
                            "cost_fill_id": cost_row.get("cost_fill_id"),
                            "event_id": cost_row.get("event_id"),
                            "route_candidate_id": cost_row.get("route_candidate_id"),
                            "symbol": symbol,
                            "side": side,
                            "entry_variant": cost_row.get("entry_variant"),
                            "cost_model": cost_row.get("cost_model"),
                            "target_stop_contract_id": target_contract["target_stop_contract_id"],
                            "ambiguous_bar_offset": first_touch_offset,
                            "ambiguity_status": first_status,
                            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY",
                            "safe_flags": SAFE_FLAGS,
                            "claim_boundary": CLAIM_BOUNDARY,
                            "source_manifest_hash": manifest_hash,
                        }
                    )
                grid_handle.write(
                    json.dumps(
                        {
                            "pc": path_grid_count,
                            "cf": int(str(cost_row.get("cost_fill_id")).rsplit("-", 1)[-1]),
                            "tc": int(str(target_contract["target_stop_contract_id"]).rsplit("-", 1)[-1]),
                            "tp": rounded(target_price),
                            "sp": rounded(stop_price),
                            "fo": fill_offset,
                            "st": first_status,
                            "to": target_offset,
                            "so": stop_offset,
                            "xo": first_touch_offset,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            if isinstance(bucket, tuple):
                bucket_value = "|".join(str(part) for part in bucket)
            else:
                bucket_value = str(bucket)
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": bucket_value,
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("cost_path_status", status_counter)
    add_bucket("fill_timing_status", fill_status_counter)
    add_bucket("first_touch_status", first_touch_counter)
    add_bucket("route_candidate_id__first_touch_status", route_touch_counter)
    add_bucket("entry_variant__first_touch_status", entry_touch_counter)
    add_bucket("cost_model__first_touch_status", cost_touch_counter)
    add_bucket("target_stop_contract__first_touch_status", target_stop_touch_counter)
    add_bucket("path_descriptor_status", event_descriptor_counter)

    question_rows = [
        {
            "question_id": "OHLC-GTOS-PATH-CONTROL-QUESTION-001",
            "question": "Which entry variants survive post-signal M15 fillability rather than only signal-bar containment?",
            "row_count": len(cost_status_rows),
            "next_same_resource_action": "split market versus retest-limit variants by post-signal fill timing and same-bar ambiguity",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-PATH-CONTROL-QUESTION-002",
            "question": "Which target/stop contracts are mostly ambiguous under M15 OHLC and need LTF/tick reconstruction?",
            "row_count": ambiguous_count,
            "next_same_resource_action": "route ambiguous same-M15 touches into owned/current/free M1/tick reconstruction or stress bounds",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-PATH-CONTROL-QUESTION-003",
            "question": "Which cost models flip target/stop touch ordering descriptors relative to zero-cost control?",
            "row_count": path_grid_count,
            "next_same_resource_action": "build cost-sensitivity deltas by event, entry variant, and target/stop contract",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-PATH-CONTROL-QUESTION-004",
            "question": "Which route families remain path-control-descriptive after target/stop ordering but still require source-safe validation partitions?",
            "row_count": len(set(row.get("route_candidate_id") for row in cost_fill_rows)),
            "next_same_resource_action": "split by route/date/cluster concentration, compare against no-fill and Route C families, and seek source-safe holdout/proxy routes",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "ambiguity_rows": len(ambiguity_rows),
        "bucket_rows": len(bucket_rows),
        "cost_fill_input_rows": len(cost_fill_rows),
        "cost_fill_status_rows": len(cost_status_rows),
        "event_descriptor_rows": len(event_descriptor_rows),
        "path_control_grid_rows": path_grid_count,
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "target_stop_contract_rows": len(target_contracts),
    }
    result = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_path_control_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This path-control packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "target_multiple_grid": TARGET_MULTIPLES,
        "stop_multiple_grid": STOP_MULTIPLES,
        "target_stop_contract_count_per_cost_fill": len(TARGET_MULTIPLES) * len(STOP_MULTIPLES),
        "spread_to_price_conversion": {
            "source_field": "spread_proxy_value",
            "source_units": "slippage_shadow_logger spread_at_request = (ask - bid) * 100",
            "price_distance_formula": "spread_proxy_value / 100.0",
            "entry_adjustment": "adverse full spread from OHLC reference: LONG adds spread distance, SHORT subtracts spread distance",
        },
        "path_control_grid_compact_schema": {
            "pc": "path_control_sequence_number; reconstruct OHLC-GTOS-PATH-CONTROL-{pc:06d}",
            "cf": "cost_fill_sequence_number; join/reconstruct OHLC-GTOS-REPLAY-COSTFILL-{cf:05d}",
            "tc": "target_stop_contract_sequence_number; join/reconstruct OHLC-GTOS-PATH-TARGETSTOP-{tc:03d}",
            "tp": "target_price",
            "sp": "stop_price",
            "fo": "fill_offset_bars",
            "st": "first_touch_status",
            "to": "target_touch_offset_bars",
            "so": "stop_touch_offset_bars",
            "xo": "first_touch_offset_bars",
        },
        "input_cost_fill_result_counts": cost_fill_result.get("counts", {}),
        "cost_path_status_counts": dict(sorted(status_counter.items())),
        "fill_timing_status_counts": dict(sorted(fill_status_counter.items())),
        "first_touch_status_counts": dict(sorted(first_touch_counter.items())),
        "path_descriptor_status_counts": dict(sorted(event_descriptor_counter.items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "build cost-sensitivity delta packet by zero-cost versus observed/fallback spread proxies",
            "route same-M15 target/stop ambiguity into M1/tick reconstruction or conservative stress bounds",
            "split post-signal unfilled limit entries from market-entry variants",
            "compare path-control descriptors against no-fill and Route C source-control families",
        ],
    }

    write_jsonl(COST_FILL_STATUS_PATH, cost_status_rows)
    write_jsonl(TARGET_STOP_CONTRACT_PATH, target_contracts)
    write_jsonl(EVENT_DESCRIPTOR_PATH, event_descriptor_rows)
    write_jsonl(AMBIGUITY_PATH, ambiguity_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Path-Control Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet joins the 15,328 replay cost/fill rows to post-signal M15 target/stop path controls.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## First-Touch Status Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(first_touch_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Build cost-sensitivity deltas by zero-cost versus observed/fallback spread proxies.",
                "- Route same-M15 target/stop ambiguity into M1/tick reconstruction or conservative stress bounds.",
                "- Split post-signal unfilled limit entries from market-entry variants.",
                "- Compare path-control descriptors against no-fill and Route C source-control families.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": counts, "first_touch_status_counts": result["first_touch_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
