#!/usr/bin/env python3
"""Build near-miss entry-offset and market-entry controls for confirmed no-fills."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS"
DATE = "2026-05-16"

FRICTION_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_CONTROL_RESULT_2026-05-16.json"
FRICTION_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BRANCH_LEDGER_2026-05-16.jsonl"
FRICTION_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_SIGNATURE_LEDGER_2026-05-16.jsonl"
FRICTION_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_ENTRY_LEDGER_2026-05-16.jsonl"

EXACT_SPREAD_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_RESULT_2026-05-16.json"
EXACT_SPREAD_PATH_CONTROL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_DESCRIPTOR_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"

NOFILL_REPAIR_RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_RESULT_2026-05-16.json"
NOFILL_REPAIR_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BRANCH_LEDGER_2026-05-16.jsonl"
NOFILL_AMBIGUITY_RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_RESULT_2026-05-16.json"
NOFILL_AMBIGUITY_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_BRANCH_STATUS_LEDGER_2026-05-16.jsonl"
NOFILL_AMBIGUITY_M15_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M15_CONTROL_LEDGER_2026-05-16.jsonl"
NOFILL_AMBIGUITY_M1_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_AMBIGUITY_SPLIT_M1_STRESS_LEDGER_2026-05-16.jsonl"

M1_SPREAD_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json"
M1_SPREAD_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ENTRY_LEDGER_2026-05-16.jsonl"
M1_SPREAD_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_COST_MODEL_LEDGER_2026-05-16.jsonl"
M1_SPREAD_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_SPREAD_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_FAMILY_LEDGER_2026-05-16.jsonl"

PATH_COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
PATH_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_GRID_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"
COST_FILL_ENTRY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_ENTRY_VARIANT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
OFFSET_BRANCH_PATH = ROUTE_DIR / f"{PREFIX}_OFFSET_BRANCH_LEDGER_{DATE}.jsonl"
MARKET_ENTRY_BRANCH_PATH = ROUTE_DIR / f"{PREFIX}_MARKET_ENTRY_BRANCH_LEDGER_{DATE}.jsonl"
SOURCE_REQUIREMENT_PATH = ROUTE_DIR / f"{PREFIX}_SOURCE_REQUIREMENT_LEDGER_{DATE}.jsonl"
BUCKET_PATH = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_{DATE}.jsonl"
QUESTION_PATH = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"

NEAR_MISS_BUCKETS = {
    "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD",
    "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXISTING_SPREAD_PROXY_ENVELOPE",
}

MARKET_ENTRY_VARIANTS = ["SIGNAL_CLOSE_MARKET_PROXY", "NEXT_BAR_OPEN_MARKET_PROXY"]
OFFSET_POLICIES = [
    "MINIMUM_EXACT_TOUCH_OFFSET",
    "FULL_EXACT_FIRST_SPREAD_OFFSET",
]

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS confirmed no-fill near-miss entry-control packet only. "
    "Rows build entry-offset-to-fill proxy controls and signal/next-bar market-entry "
    "branch comparisons for confirmed no-fill near misses. Target/stop ordering remains "
    "source-control proxy evidence from historical OHLC/M1/tick-derived ledgers; no "
    "validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior "
    "change is claimed."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest(extra_paths: Iterable[Path]) -> tuple[list[dict[str, Any]], str]:
    paths = [
        FRICTION_RESULT_PATH,
        FRICTION_BRANCH_PATH,
        FRICTION_SIGNATURE_PATH,
        FRICTION_ENTRY_PATH,
        EXACT_SPREAD_RESULT_PATH,
        EXACT_SPREAD_PATH_CONTROL_PATH,
        EXACT_SPREAD_DESCRIPTOR_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_STRESS_PATH,
        NOFILL_REPAIR_RESULT_PATH,
        NOFILL_REPAIR_BRANCH_PATH,
        NOFILL_AMBIGUITY_RESULT_PATH,
        NOFILL_AMBIGUITY_BRANCH_PATH,
        NOFILL_AMBIGUITY_M15_PATH,
        NOFILL_AMBIGUITY_M1_PATH,
        M1_SPREAD_RESULT_PATH,
        M1_SPREAD_ENTRY_PATH,
        M1_SPREAD_COST_MODEL_PATH,
        M1_SPREAD_SIGNATURE_PATH,
        M1_SPREAD_FAMILY_PATH,
        PATH_COST_STATUS_PATH,
        PATH_GRID_PATH,
        TARGET_STOP_CONTRACT_PATH,
        COST_FILL_ENTRY_VARIANT_PATH,
        *extra_paths,
    ]
    unique_paths = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique_paths.append(path)
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/") if path.is_relative_to(REPO) else str(path),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in unique_paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def numeric(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def rounded(value: float | None, digits: int = 9) -> float | None:
    return round(value, digits) if value is not None else None


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def side_sign(side: str) -> int:
    return -1 if str(side).upper() == "SHORT" else 1


def family_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("route_candidate_id")),
            str(row.get("entry_variant")),
            str(row.get("target_stop_contract_id")),
        ]
    )


def source_event_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("event_id")), str(row.get("route_candidate_id"))


def cost_fill_id_from_cf(cf: Any) -> str:
    return f"OHLC-GTOS-REPLAY-COSTFILL-{int(cf):05d}"


def target_stop_contract_id_from_tc(tc: Any) -> str:
    return f"OHLC-GTOS-PATH-TARGETSTOP-{int(tc):03d}"


def load_m15_bars(symbol: str) -> tuple[list[dict[str, Any]], dict[str, int], Path]:
    path = REPO / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows, {}, path
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
    return rows, {str(row["time_utc"]): idx for idx, row in enumerate(rows)}, path


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
        "directional_close_units": rounded(close_units, 6),
        "directional_favorable_excursion_units": rounded(favorable, 6),
        "directional_adverse_excursion_units": rounded(adverse, 6),
    }


def fill_offset_from_time(source_time_utc: str | None, fill_time_utc: str | None, horizon_bars: int) -> int | None:
    source_time = parse_utc(source_time_utc)
    fill_time = parse_utc(fill_time_utc)
    if source_time is None or fill_time is None:
        return None
    minutes = (fill_time - source_time).total_seconds() / 60.0
    if minutes < 15:
        return 1
    offset = int(minutes // 15)
    return min(max(offset, 1), horizon_bars)


def offset_price(entry_price: float | None, side: str, offset_distance: float | None) -> float | None:
    if entry_price is None or offset_distance is None:
        return None
    return rounded(entry_price + side_sign(side) * offset_distance)


def target_price(side: str, entry: float, rolling_range: float, target_multiple: float) -> float:
    return entry + side_sign(side) * rolling_range * target_multiple


def stop_price(side: str, entry: float, rolling_range: float, stop_multiple: float) -> float:
    return entry - side_sign(side) * rolling_range * stop_multiple


def offset_source(policy: str, entry: dict[str, Any]) -> tuple[float | None, str, str]:
    miss = numeric(entry.get("miss_distance_to_zero_entry_price"))
    first_spread = numeric(entry.get("first_tick_spread_price_distance"))
    if policy == "MINIMUM_EXACT_TOUCH_OFFSET":
        return miss, "authoritative_closest_fill_side_price", "OFFSET_TO_FIRST_CONFIRMED_CLOSEST_APPROACH"
    if policy == "FULL_EXACT_FIRST_SPREAD_OFFSET":
        return first_spread, "first_tick_spread_price_distance", "OFFSET_BY_EXACT_FIRST_TICK_SPREAD"
    return None, "UNKNOWN_OFFSET_SOURCE", "UNKNOWN_OFFSET_POLICY"


def offset_fill_status(offset_distance: float | None, miss_distance: float | None, source_field: str) -> str:
    if offset_distance is None or miss_distance is None:
        return "OFFSET_SOURCE_DISTANCE_MISSING_FAIL_CLOSED"
    if offset_distance + 1e-12 >= miss_distance:
        if source_field == "first_tick_spread_price_distance":
            return "OFFSET_PROXY_FILLED_BY_EXACT_FIRST_SPREAD_ENVELOPE"
        return "OFFSET_PROXY_FILLED_BY_AUTHORITATIVE_CLOSEST_APPROACH"
    return "OFFSET_PROXY_STILL_UNFILLED_FAIL_CLOSED"


def entry_delta_bucket(delta_units: float | None) -> str:
    if delta_units is None:
        return "ENTRY_DELTA_UNAVAILABLE"
    if delta_units < 0:
        return "MARKET_ENTRY_BETTER_THAN_RETEST_LIMIT_BY_UNIT_SIGN"
    if delta_units == 0:
        return "MARKET_ENTRY_EQUALS_RETEST_LIMIT"
    if delta_units <= 0.5:
        return "MARKET_ENTRY_WITHIN_HALF_RANGE_UNIT_OF_RETEST"
    if delta_units <= 1.0:
        return "MARKET_ENTRY_WITHIN_ONE_RANGE_UNIT_OF_RETEST"
    return "MARKET_ENTRY_MORE_THAN_ONE_RANGE_UNIT_FROM_RETEST"


def add_bucket_rows(
    bucket_rows: list[dict[str, Any]],
    axis: str,
    counter: Counter[Any],
) -> None:
    for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
        bucket_rows.append(
            {
                "bucket_axis": axis,
                "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                "count": count,
                "evidence_class": f"{PREFIX}_BUCKET",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )


def main() -> int:
    generated_at = now_utc()

    friction_result = read_json(FRICTION_RESULT_PATH)
    m1_spread_result = read_json(M1_SPREAD_RESULT_PATH)
    exact_spread_result = read_json(EXACT_SPREAD_RESULT_PATH)
    nofill_repair_result = read_json(NOFILL_REPAIR_RESULT_PATH)
    nofill_ambiguity_result = read_json(NOFILL_AMBIGUITY_RESULT_PATH)

    friction_entry_rows = [row for row in read_jsonl(FRICTION_ENTRY_PATH) if not row.get("_parse_error")]
    friction_signature_rows = [row for row in read_jsonl(FRICTION_SIGNATURE_PATH) if not row.get("_parse_error")]
    friction_branch_rows = [row for row in read_jsonl(FRICTION_BRANCH_PATH) if not row.get("_parse_error")]
    path_cost_rows = [row for row in read_jsonl(PATH_COST_STATUS_PATH) if not row.get("_parse_error")]
    path_grid_rows = [row for row in read_jsonl(PATH_GRID_PATH) if not row.get("_parse_error")]
    entry_variant_rows = [row for row in read_jsonl(COST_FILL_ENTRY_VARIANT_PATH) if not row.get("_parse_error")]
    exact_path_rows = [row for row in read_jsonl(EXACT_SPREAD_PATH_CONTROL_PATH) if not row.get("_parse_error")]
    exact_delta_rows = [row for row in read_jsonl(EXACT_SPREAD_DESCRIPTOR_DELTA_PATH) if not row.get("_parse_error")]
    exact_unavailable_rows = [row for row in read_jsonl(EXACT_SPREAD_UNAVAILABLE_STRESS_PATH) if not row.get("_parse_error")]
    nofill_repair_rows = [row for row in read_jsonl(NOFILL_REPAIR_BRANCH_PATH) if not row.get("_parse_error")]
    nofill_ambiguity_rows = [row for row in read_jsonl(NOFILL_AMBIGUITY_BRANCH_PATH) if not row.get("_parse_error")]
    m1_spread_entry_rows = [row for row in read_jsonl(M1_SPREAD_ENTRY_PATH) if not row.get("_parse_error")]
    m1_spread_signature_rows = [row for row in read_jsonl(M1_SPREAD_SIGNATURE_PATH) if not row.get("_parse_error")]

    entry_by_id = {row["entry_variant_id"]: row for row in friction_entry_rows}
    signature_by_id = {row["cost_sensitivity_signature_id"]: row for row in friction_signature_rows}
    market_cost_by_event_variant: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    cost_by_id = {}
    for row in path_cost_rows:
        cost_by_id[row["cost_fill_id"]] = row
        if row.get("entry_variant") in MARKET_ENTRY_VARIANTS:
            market_cost_by_event_variant[(row["event_id"], row["entry_variant"])].append(row)

    entry_variant_by_id = {row["entry_variant_id"]: row for row in entry_variant_rows}
    path_grid_by_cost_target: dict[tuple[str, str], dict[str, Any]] = {}
    for row in path_grid_rows:
        if row.get("cf") is None or row.get("tc") is None:
            continue
        path_grid_by_cost_target[(cost_fill_id_from_cf(row["cf"]), target_stop_contract_id_from_tc(row["tc"]))] = row

    exact_path_ids = {row.get("cost_sensitivity_signature_id") for row in exact_path_rows}
    exact_delta_ids = {row.get("cost_sensitivity_signature_id") for row in exact_delta_rows}
    exact_unavailable_ids = {row.get("cost_sensitivity_signature_id") for row in exact_unavailable_rows}
    m1_entry_events = {row.get("event_id") for row in m1_spread_entry_rows}
    m1_signature_ids = {row.get("cost_sensitivity_signature_id") for row in m1_spread_signature_rows}
    nofill_geometry_symbol_side = Counter((row.get("symbol"), row.get("side")) for row in nofill_repair_rows + nofill_ambiguity_rows)

    near_branch_rows = [
        row
        for row in friction_branch_rows
        if row.get("confirmed_nofill_signature") and row.get("execution_friction_distance_bucket") in NEAR_MISS_BUCKETS
    ]
    near_entry_ids = sorted({row["entry_variant_id"] for row in near_branch_rows})
    near_entry_rows = [entry_by_id[entry_id] for entry_id in near_entry_ids if entry_id in entry_by_id]
    near_symbols = sorted({row["symbol"] for row in near_branch_rows})
    bars_by_symbol = {}
    index_by_symbol_time = {}
    m15_paths = []
    for symbol in near_symbols:
        bars, by_time, path = load_m15_bars(symbol)
        bars_by_symbol[symbol] = bars
        index_by_symbol_time[symbol] = by_time
        m15_paths.append(path)

    manifest_rows, manifest_hash = source_manifest(m15_paths)

    offset_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    source_requirement_rows: list[dict[str, Any]] = []

    for near_seq, branch in enumerate(near_branch_rows, 1):
        entry = entry_by_id.get(branch["entry_variant_id"], {})
        signature = signature_by_id.get(branch["cost_sensitivity_signature_id"], {})
        symbol = str(branch["symbol"])
        side = str(branch["side"])
        entry_price = numeric(entry.get("entry_price_input_only"))
        rolling_range = numeric(entry.get("rolling_median_range"))
        target_multiple = numeric(branch.get("target_multiple"))
        stop_multiple = numeric(branch.get("stop_multiple"))
        horizon_bars = int(entry.get("horizon_bars") or 0)
        source_time = str(entry.get("source_time_utc"))
        bar_index = index_by_symbol_time.get(symbol, {}).get(source_time)
        future = future_window(bars_by_symbol.get(symbol, []), bar_index, horizon_bars)
        fill_time = entry.get("first_tick_closest_utc") or entry.get("first_m1_closest_utc")
        fill_offset = fill_offset_from_time(source_time, fill_time, horizon_bars)
        miss_distance = numeric(entry.get("miss_distance_to_zero_entry_price"))
        exact_path_status = (
            "EXACT_SPREAD_PATH_CONTROL_DIRECT_JOIN_AVAILABLE"
            if branch["cost_sensitivity_signature_id"] in exact_path_ids
            else "EXACT_SPREAD_PATH_CONTROL_DIRECT_JOIN_ABSENT_FOR_NEAR_MISS_SIGNATURE"
        )
        exact_delta_status = (
            "EXACT_SPREAD_DESCRIPTOR_DELTA_DIRECT_JOIN_AVAILABLE"
            if branch["cost_sensitivity_signature_id"] in exact_delta_ids
            else "EXACT_SPREAD_DESCRIPTOR_DELTA_DIRECT_JOIN_ABSENT_FOR_NEAR_MISS_SIGNATURE"
        )
        exact_unavailable_status = (
            "EXACT_SPREAD_UNAVAILABLE_STRESS_JOIN_PRESENT"
            if branch["cost_sensitivity_signature_id"] in exact_unavailable_ids
            else "EXACT_SPREAD_UNAVAILABLE_STRESS_JOIN_ABSENT"
        )
        m1_overlap_status = (
            "M1_SPREAD_ADJUSTED_REPLAY_DIRECT_SIGNATURE_JOIN_AVAILABLE"
            if branch["cost_sensitivity_signature_id"] in m1_signature_ids
            else (
                "M1_SPREAD_ADJUSTED_REPLAY_EVENT_JOIN_AVAILABLE"
                if branch["event_id"] in m1_entry_events
                else "M1_SPREAD_ADJUSTED_REPLAY_DIRECT_JOIN_ABSENT_FOR_NEAR_MISS_SIGNATURE"
            )
        )
        geometry_status = (
            "NOFILL_GEOMETRY_SYMBOL_SIDE_CONTEXT_AVAILABLE_NO_DIRECT_EVENT_JOIN"
            if nofill_geometry_symbol_side.get((branch["symbol"], branch["side"]), 0)
            else "NOFILL_GEOMETRY_DIRECT_JOIN_ABSENT_SYMBOL_SIDE_NOT_IN_GEOMETRY_PACKET"
        )

        for policy in OFFSET_POLICIES:
            offset_distance, source_field, policy_status = offset_source(policy, entry)
            shifted_entry = offset_price(entry_price, side, offset_distance)
            source_distance_status = offset_fill_status(offset_distance, miss_distance, source_field)
            if shifted_entry is not None and rolling_range is not None and target_multiple is not None and stop_multiple is not None:
                branch_target = target_price(side, shifted_entry, rolling_range, target_multiple)
                branch_stop = stop_price(side, shifted_entry, rolling_range, stop_multiple)
                path = path_after_fill(future, fill_offset)
                first_touch_status, target_offset, stop_offset, first_touch_offset = touch_status(
                    side,
                    branch_target,
                    branch_stop,
                    path,
                )
                descriptor = path_extremes(side, shifted_entry, rolling_range, path)
                path_source_status = (
                    "OFFSET_PATH_RECOMPUTED_FROM_HISTORICAL_M15"
                    if len(future) >= horizon_bars and fill_offset is not None
                    else "OFFSET_PATH_SOURCE_INCOMPLETE_FAIL_CLOSED"
                )
            else:
                branch_target = None
                branch_stop = None
                target_offset = None
                stop_offset = None
                first_touch_offset = None
                first_touch_status = "OFFSET_TARGET_STOP_INPUT_MISSING_FAIL_CLOSED"
                descriptor = path_extremes(side, None, rolling_range, [])
                path_source_status = "OFFSET_TARGET_STOP_INPUT_MISSING_FAIL_CLOSED"
            offset_rows.append(
                {
                    "near_miss_entry_control_offset_branch_id": f"OHLC-GTOS-NEARMISS-OFFSET-BRANCH-{len(offset_rows) + 1:05d}",
                    "near_miss_source_row_sequence": near_seq,
                    "execution_friction_branch_id": branch["execution_friction_branch_id"],
                    "execution_friction_signature_id": branch["execution_friction_signature_id"],
                    "cost_sensitivity_signature_id": branch["cost_sensitivity_signature_id"],
                    "entry_variant_id": branch["entry_variant_id"],
                    "event_id": branch["event_id"],
                    "route_candidate_id": branch["route_candidate_id"],
                    "symbol": branch["symbol"],
                    "side": side,
                    "source_entry_variant": branch["entry_variant"],
                    "target_stop_contract_id": branch["target_stop_contract_id"],
                    "target_multiple": target_multiple,
                    "stop_multiple": stop_multiple,
                    "source_near_miss_bucket": branch["execution_friction_distance_bucket"],
                    "offset_policy": policy,
                    "offset_policy_status": policy_status,
                    "offset_source_field": source_field,
                    "offset_distance": rounded(offset_distance),
                    "miss_distance_to_zero_entry_price": rounded(miss_distance),
                    "offset_distance_over_miss": rounded(offset_distance / miss_distance, 9) if offset_distance is not None and miss_distance else None,
                    "original_entry_price_input_only": rounded(entry_price),
                    "offset_entry_price_input_only": shifted_entry,
                    "authoritative_closest_fill_side_price": entry.get("authoritative_closest_fill_side_price"),
                    "first_tick_spread_price_distance": entry.get("first_tick_spread_price_distance"),
                    "offset_fill_proxy_status": source_distance_status,
                    "fill_time_utc": fill_time,
                    "fill_offset_bars_m15_proxy": fill_offset,
                    "probe_window_start_utc": entry.get("probe_window_start_utc"),
                    "probe_window_end_utc": entry.get("probe_window_end_utc"),
                    "rolling_median_range": rounded(rolling_range),
                    "target_price_offset_proxy": rounded(branch_target),
                    "stop_price_offset_proxy": rounded(branch_stop),
                    "first_touch_status_offset_proxy": first_touch_status,
                    "target_touch_offset_bars": target_offset,
                    "stop_touch_offset_bars": stop_offset,
                    "first_touch_offset_bars": first_touch_offset,
                    "offset_path_source_status": path_source_status,
                    "same_m15_ambiguity_rows_for_family": branch.get("same_m15_ambiguity_rows_for_family"),
                    "has_same_m15_ambiguity": branch.get("has_same_m15_ambiguity"),
                    "exact_path_control_join_status": exact_path_status,
                    "exact_descriptor_delta_join_status": exact_delta_status,
                    "exact_unavailable_stress_join_status": exact_unavailable_status,
                    "m1_spread_replay_overlap_status": m1_overlap_status,
                    "nofill_geometry_context_status": geometry_status,
                    **descriptor,
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": f"{PREFIX}_OFFSET_BRANCH",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

        for market_variant in MARKET_ENTRY_VARIANTS:
            market_cost_rows = sorted(
                market_cost_by_event_variant.get((branch["event_id"], market_variant), []),
                key=lambda row: str(row.get("cost_model")),
            )
            if not market_cost_rows:
                market_rows.append(
                    {
                        "near_miss_entry_control_market_branch_id": f"OHLC-GTOS-NEARMISS-MARKET-BRANCH-{len(market_rows) + 1:05d}",
                        "near_miss_source_row_sequence": near_seq,
                        "execution_friction_branch_id": branch["execution_friction_branch_id"],
                        "cost_sensitivity_signature_id": branch["cost_sensitivity_signature_id"],
                        "event_id": branch["event_id"],
                        "route_candidate_id": branch["route_candidate_id"],
                        "symbol": branch["symbol"],
                        "side": side,
                        "source_entry_variant": branch["entry_variant"],
                        "market_entry_variant": market_variant,
                        "target_stop_contract_id": branch["target_stop_contract_id"],
                        "market_entry_join_status": "MARKET_ENTRY_COST_STATUS_MISSING_FAIL_CLOSED",
                        "source_manifest_hash": manifest_hash,
                        "evidence_class": f"{PREFIX}_MARKET_ENTRY_BRANCH",
                        "safe_flags": SAFE_FLAGS,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )
                continue
            for cost_row in market_cost_rows:
                grid = path_grid_by_cost_target.get((cost_row["cost_fill_id"], branch["target_stop_contract_id"]), {})
                market_entry = numeric(cost_row.get("entry_price_input_only"))
                signed_delta = (
                    side_sign(side) * (market_entry - entry_price)
                    if market_entry is not None and entry_price is not None
                    else None
                )
                delta_units = signed_delta / rolling_range if signed_delta is not None and rolling_range else None
                variant_row = entry_variant_by_id.get(str(cost_row.get("entry_variant_id")), {})
                market_rows.append(
                    {
                        "near_miss_entry_control_market_branch_id": f"OHLC-GTOS-NEARMISS-MARKET-BRANCH-{len(market_rows) + 1:05d}",
                        "near_miss_source_row_sequence": near_seq,
                        "execution_friction_branch_id": branch["execution_friction_branch_id"],
                        "execution_friction_signature_id": branch["execution_friction_signature_id"],
                        "cost_sensitivity_signature_id": branch["cost_sensitivity_signature_id"],
                        "entry_variant_id": branch["entry_variant_id"],
                        "event_id": branch["event_id"],
                        "route_candidate_id": branch["route_candidate_id"],
                        "symbol": branch["symbol"],
                        "side": side,
                        "source_entry_variant": branch["entry_variant"],
                        "market_entry_variant": market_variant,
                        "market_entry_variant_id": cost_row.get("entry_variant_id"),
                        "market_cost_fill_id": cost_row.get("cost_fill_id"),
                        "cost_model": cost_row.get("cost_model"),
                        "target_stop_contract_id": branch["target_stop_contract_id"],
                        "target_multiple": branch.get("target_multiple"),
                        "stop_multiple": branch.get("stop_multiple"),
                        "source_near_miss_bucket": branch["execution_friction_distance_bucket"],
                        "source_entry_price_input_only": rounded(entry_price),
                        "market_entry_price_input_only": rounded(market_entry),
                        "market_effective_entry_price": cost_row.get("effective_entry_price"),
                        "market_entry_price_source": variant_row.get("entry_price_source"),
                        "market_fill_timing_status": cost_row.get("fill_timing_status"),
                        "market_path_status": cost_row.get("cost_path_status"),
                        "market_path_descriptor_status": cost_row.get("path_descriptor_status"),
                        "market_spread_proxy_price_distance": cost_row.get("spread_proxy_price_distance"),
                        "market_entry_signed_delta_vs_near_limit": rounded(signed_delta),
                        "market_entry_signed_delta_over_rolling_range": rounded(delta_units),
                        "market_entry_delta_bucket": entry_delta_bucket(rounded(delta_units)),
                        "market_first_touch_status": grid.get("st", "PATH_GRID_JOIN_MISSING_FAIL_CLOSED"),
                        "market_target_price": grid.get("tp"),
                        "market_stop_price": grid.get("sp"),
                        "market_fill_offset_bars": grid.get("fo"),
                        "market_target_touch_offset_bars": grid.get("to"),
                        "market_stop_touch_offset_bars": grid.get("so"),
                        "market_first_touch_offset_bars": grid.get("xo"),
                        "market_branch_join_status": "MARKET_ENTRY_PATH_CONTROL_JOINED" if grid else "MARKET_ENTRY_PATH_GRID_MISSING_FAIL_CLOSED",
                        "same_m15_ambiguity_rows_for_family": branch.get("same_m15_ambiguity_rows_for_family"),
                        "has_same_m15_ambiguity": branch.get("has_same_m15_ambiguity"),
                        "exact_path_control_join_status": exact_path_status,
                        "exact_descriptor_delta_join_status": exact_delta_status,
                        "m1_spread_replay_overlap_status": m1_overlap_status,
                        "nofill_geometry_context_status": geometry_status,
                        "source_manifest_hash": manifest_hash,
                        "evidence_class": f"{PREFIX}_MARKET_ENTRY_BRANCH",
                        "safe_flags": SAFE_FLAGS,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )

        requirement_specs = [
            (
                "EXACT_TICK_NEAR_MISS_DISTANCE",
                "SATISFIED_EXACT_TICK_FIRST_SPREAD_AND_CLOSEST_TOUCH"
                if entry.get("authoritative_distance_source") == "EXACT_TICK_FILL_SIDE_PRICE"
                and entry.get("first_tick_spread_price_distance") is not None
                else "EXACT_TICK_DISTANCE_SOURCE_MISSING_OR_PROXY_ONLY_FAIL_CLOSED",
                "keep exact tick distance as source-bound near-miss offset input",
            ),
            (
                "OFFSET_TARGET_STOP_PATH",
                "SATISFIED_RECOMPUTED_FROM_HISTORICAL_M15"
                if bar_index is not None and len(future) >= horizon_bars
                else "M15_PATH_SOURCE_GAP_FAIL_CLOSED",
                "use M15 path proxy only; route same-bar or fill-bar ordering to LTF/tick replay",
            ),
            (
                "EXACT_SPREAD_PATH_CONTROL_JOIN",
                exact_path_status,
                "direct exact-spread path controls do not cover this near-miss signature when absent; preserve as source requirement",
            ),
            (
                "M1_SPREAD_ADJUSTED_REPLAY_JOIN",
                m1_overlap_status,
                "dedicated M1 near-miss replay is required when direct source-alignment replay has no overlap",
            ),
            (
                "NOFILL_GEOMETRY_REPAIR_SPLIT_JOIN",
                geometry_status,
                "geometry repair/split ledgers are source-hashed context; no direct historical-event join is inferred when absent",
            ),
        ]
        for surface, status, action in requirement_specs:
            source_requirement_rows.append(
                {
                    "near_miss_entry_control_source_requirement_id": f"OHLC-GTOS-NEARMISS-SOURCE-REQ-{len(source_requirement_rows) + 1:05d}",
                    "near_miss_source_row_sequence": near_seq,
                    "execution_friction_branch_id": branch["execution_friction_branch_id"],
                    "execution_friction_signature_id": branch["execution_friction_signature_id"],
                    "cost_sensitivity_signature_id": branch["cost_sensitivity_signature_id"],
                    "entry_variant_id": branch["entry_variant_id"],
                    "event_id": branch["event_id"],
                    "route_candidate_id": branch["route_candidate_id"],
                    "symbol": branch["symbol"],
                    "side": side,
                    "source_entry_variant": branch["entry_variant"],
                    "target_stop_contract_id": branch["target_stop_contract_id"],
                    "source_requirement_surface": surface,
                    "source_requirement_status": status,
                    "source_requirement_action": action,
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": f"{PREFIX}_SOURCE_REQUIREMENT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    bucket_rows: list[dict[str, Any]] = []
    add_bucket_rows(bucket_rows, "near_miss_input_bucket", Counter(row["execution_friction_distance_bucket"] for row in near_branch_rows))
    add_bucket_rows(bucket_rows, "near_miss_symbol_side", Counter((row["symbol"], row["side"]) for row in near_branch_rows))
    add_bucket_rows(bucket_rows, "near_miss_entry_variant", Counter(row["entry_variant"] for row in near_branch_rows))
    add_bucket_rows(bucket_rows, "offset_policy_status", Counter((row["offset_policy"], row["offset_fill_proxy_status"]) for row in offset_rows))
    add_bucket_rows(bucket_rows, "offset_first_touch_status", Counter(row["first_touch_status_offset_proxy"] for row in offset_rows))
    add_bucket_rows(bucket_rows, "offset_path_source_status", Counter(row["offset_path_source_status"] for row in offset_rows))
    add_bucket_rows(bucket_rows, "market_variant_cost_first_touch", Counter((row.get("market_entry_variant"), row.get("cost_model"), row.get("market_first_touch_status")) for row in market_rows))
    add_bucket_rows(bucket_rows, "market_entry_delta_bucket", Counter(row.get("market_entry_delta_bucket") for row in market_rows))
    add_bucket_rows(bucket_rows, "market_branch_join_status", Counter(row.get("market_branch_join_status") for row in market_rows))
    add_bucket_rows(bucket_rows, "source_requirement_status", Counter((row["source_requirement_surface"], row["source_requirement_status"]) for row in source_requirement_rows))
    add_bucket_rows(bucket_rows, "exact_spread_join_status", Counter(row["exact_path_control_join_status"] for row in offset_rows))
    add_bucket_rows(bucket_rows, "m1_spread_overlap_status", Counter(row["m1_spread_replay_overlap_status"] for row in offset_rows))
    add_bucket_rows(bucket_rows, "nofill_geometry_context_status", Counter(row["nofill_geometry_context_status"] for row in offset_rows))

    exact_near_rows = [row for row in near_branch_rows if row["execution_friction_distance_bucket"] == "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD"]
    offset_target_first = [row for row in offset_rows if str(row["first_touch_status_offset_proxy"]).startswith("TARGET_TOUCH")]
    offset_ambiguous = [row for row in offset_rows if "AMBIGUOUS" in str(row["first_touch_status_offset_proxy"])]
    market_target_first = [row for row in market_rows if str(row.get("market_first_touch_status")).startswith("TARGET")]
    missing_m1_overlap = [
        row
        for row in source_requirement_rows
        if row["source_requirement_surface"] == "M1_SPREAD_ADJUSTED_REPLAY_JOIN"
        and "ABSENT" in row["source_requirement_status"]
    ]
    question_rows = [
        {
            "question_id": "OHLC-GTOS-NEARMISS-ENTRY-CONTROLS-QUESTION-001",
            "question": "How many confirmed no-fill signatures are exact-spread near misses and therefore eligible for immediate offset-to-fill controls?",
            "row_count": len(exact_near_rows),
            "next_same_resource_action": "use the offset branch ledger as the full near-miss denominator before any fillability claim",
            "evidence_class": f"{PREFIX}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-ENTRY-CONTROLS-QUESTION-002",
            "question": "Which offset-to-fill proxy branches become target-first versus stop-first or ambiguous under M15 target/stop path controls?",
            "row_count": len(offset_rows),
            "target_first_rows": len(offset_target_first),
            "ambiguous_rows": len(offset_ambiguous),
            "next_same_resource_action": "split offset branches by target/stop ordering and route same-M15 ambiguity to M1/tick stress",
            "evidence_class": f"{PREFIX}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-ENTRY-CONTROLS-QUESTION-003",
            "question": "How do signal-close and next-bar-open market-entry controls compare against the same near-miss target/stop contracts?",
            "row_count": len(market_rows),
            "target_first_rows": len(market_target_first),
            "next_same_resource_action": "compare market-entry branch descriptors against offset branches and exact-source requirements",
            "evidence_class": f"{PREFIX}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-ENTRY-CONTROLS-QUESTION-004",
            "question": "Which near-miss rows lack direct M1 spread-adjusted replay overlap and therefore need a dedicated near-miss M1 replay packet?",
            "row_count": len(missing_m1_overlap),
            "next_same_resource_action": "build a dedicated M1 near-miss replay only for the preserved full near-miss denominator",
            "evidence_class": f"{PREFIX}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NEARMISS-ENTRY-CONTROLS-QUESTION-005",
            "question": "Do exact-spread path-control, no-fill geometry, or M1 replay packets directly cover these near-miss signatures?",
            "row_count": len(source_requirement_rows),
            "next_same_resource_action": "treat absent direct joins as explicit source requirements rather than passive blockers",
            "evidence_class": f"{PREFIX}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "friction_branch_input_rows": len(friction_branch_rows),
        "friction_entry_input_rows": len(friction_entry_rows),
        "friction_signature_input_rows": len(friction_signature_rows),
        "market_entry_branch_rows": len(market_rows),
        "m1_spread_entry_input_rows": len(m1_spread_entry_rows),
        "m1_spread_signature_input_rows": len(m1_spread_signature_rows),
        "near_miss_branch_rows": len(near_branch_rows),
        "near_miss_entry_rows": len(near_entry_rows),
        "offset_branch_rows": len(offset_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "source_requirement_rows": len(source_requirement_rows),
        "unique_near_miss_events": len({row["event_id"] for row in near_branch_rows}),
        "unique_near_miss_entry_ids": len(near_entry_ids),
    }

    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_confirmed_nofill_near_miss_entry_controls_v1",
        "generated_utc": generated_at,
        "evidence_class": f"{PREFIX}_CONTROL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This near-miss entry-control packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "near_miss_bucket_counts": dict(sorted(Counter(row["execution_friction_distance_bucket"] for row in near_branch_rows).items())),
        "offset_first_touch_status_counts": dict(sorted(Counter(row["first_touch_status_offset_proxy"] for row in offset_rows).items())),
        "market_first_touch_status_counts": dict(sorted(Counter(row.get("market_first_touch_status") for row in market_rows).items())),
        "source_requirement_status_counts": dict(sorted(Counter(row["source_requirement_status"] for row in source_requirement_rows).items())),
        "direct_overlap_counts": {
            "near_miss_signatures_with_exact_spread_path_control": len({row["cost_sensitivity_signature_id"] for row in near_branch_rows} & exact_path_ids),
            "near_miss_signatures_with_exact_descriptor_delta": len({row["cost_sensitivity_signature_id"] for row in near_branch_rows} & exact_delta_ids),
            "near_miss_signatures_with_m1_spread_adjusted_replay": len({row["cost_sensitivity_signature_id"] for row in near_branch_rows} & m1_signature_ids),
            "near_miss_events_with_m1_spread_adjusted_replay": len({row["event_id"] for row in near_branch_rows} & m1_entry_events),
        },
        "upstream_counts": {
            "friction_result_counts": friction_result.get("counts", {}),
            "exact_spread_result_counts": exact_spread_result.get("counts", {}),
            "m1_spread_result_counts": m1_spread_result.get("counts", {}),
            "nofill_repair_result_counts": nofill_repair_result.get("counts", {}),
            "nofill_ambiguity_result_counts": nofill_ambiguity_result.get("counts", {}),
        },
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "replay the 112 exact-spread near-miss signatures through dedicated M1 fill-bar ordering where available",
            "compare offset-to-fill proxy branches against signal-close and next-bar market-entry controls by target/stop ordering",
            "split branches by absent exact-spread/M1/geometry direct joins before any interpretation",
            "join the near-miss market-entry packet back into cost/fill/path synthesis while preserving all rows",
        ],
    }

    write_jsonl(OFFSET_BRANCH_PATH, offset_rows)
    write_jsonl(MARKET_ENTRY_BRANCH_PATH, market_rows)
    write_jsonl(SOURCE_REQUIREMENT_PATH, source_requirement_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Confirmed No-Fill Near-Miss Entry Controls",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet materializes branch-local near-miss entry-offset and market-entry controls. It preserves every confirmed near-miss branch row and records direct source-join absences as source requirements, not completion blockers.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Offset First-Touch Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in output["offset_first_touch_status_counts"].items()),
                "",
                "## Market First-Touch Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in output["market_first_touch_status_counts"].items()),
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
