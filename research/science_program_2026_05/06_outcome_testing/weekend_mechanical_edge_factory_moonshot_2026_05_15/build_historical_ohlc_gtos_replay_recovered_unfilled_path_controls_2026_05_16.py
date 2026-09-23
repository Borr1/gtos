#!/usr/bin/env python3
"""Recompute path controls for recovered unfilled entry probes."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(ROUTE_DIR))

import build_historical_ohlc_gtos_replay_path_control_packet_2026_05_16 as pathmod  # noqa: E402


UNFILLED_PROBE_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_RESULT_2026-05-16.json"
ENTRY_WINDOW_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ENTRY_WINDOW_PROBE_LEDGER_2026-05-16.jsonl"
SIGNATURE_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_SIGNATURE_PROBE_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_CONTROL_RESULT_2026-05-16.json"
ENTRY_PATH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_ENTRY_PATH_LEDGER_2026-05-16.jsonl"
SIGNATURE_PATH_CONTROL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS recovered-unfilled path-control packet only. Rows "
    "recompute target/stop M15 path descriptors for recovered exact-tick fills "
    "and separate M1 bid-bar proxy recoveries as fill-side-unresolved stress "
    "controls; no validation, R/PnL, expectancy, win-rate, live-readiness, "
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
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def floor_m15(value: datetime) -> datetime:
    return value.replace(minute=(value.minute // 15) * 15, second=0, microsecond=0)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        UNFILLED_PROBE_RESULT_PATH,
        ENTRY_WINDOW_PROBE_PATH,
        SIGNATURE_PROBE_PATH,
        COST_STATUS_PATH,
        REPO / "data/historical_2026/GBPJPY_M15.csv",
        REPO / "data/historical_2026/XAUUSD_M15.csv",
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def recovered_fill_time(row: dict[str, Any]) -> tuple[str | None, str]:
    status = row["unfilled_probe_status"]
    if status == "TICK_FILL_SIDE_TOUCH_RECOVERED":
        return row.get("first_tick_fill_touch_utc"), "EXACT_TICK_FILL_SIDE_TOUCH"
    if status == "M1_BID_BAR_TOUCH_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED":
        return row.get("first_m1_touch_utc"), "M1_BID_BAR_TOUCH_PROXY_FILL_SIDE_UNRESOLVED"
    return None, "NO_RECOVERED_FILL"


def recovered_path_status(row: dict[str, Any], fill_bar_first_touch_offset: int | None) -> str:
    if row["unfilled_probe_status"] == "TICK_FILL_SIDE_TOUCH_RECOVERED":
        if fill_bar_first_touch_offset == 0:
            return "EXACT_TICK_RECOVERED_FILL_PATH_WITH_FILL_BAR_ORDER_AMBIGUITY"
        return "EXACT_TICK_RECOVERED_FILL_PATH_AFTER_FILL_BAR_ORDERED_M15"
    if fill_bar_first_touch_offset == 0:
        return "M1_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED_WITH_FILL_BAR_ORDER_AMBIGUITY"
    return "M1_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED_PATH_STRESS"


def touch_status_with_fill_bar(
    side: str,
    target_price: float,
    stop_price: float,
    path: list[tuple[int, dict[str, Any]]],
) -> tuple[str, int | None, int | None, int | None]:
    target_offset: int | None = None
    stop_offset: int | None = None
    for offset, bar in path:
        high = pathmod.numeric(bar.get("high"))
        low = pathmod.numeric(bar.get("low"))
        if high is None or low is None:
            continue
        if pathmod.side_sign(side) > 0:
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
        return "NO_TARGET_OR_STOP_TOUCH_WITHIN_RECOVERED_PATH_HORIZON", None, None, None
    if target_offset is not None and stop_offset is None:
        return "TARGET_TOUCH_FIRST_OR_ONLY_M15_PROXY", target_offset, None, target_offset
    if target_offset is None and stop_offset is not None:
        return "STOP_TOUCH_FIRST_OR_ONLY_M15_PROXY", None, stop_offset, stop_offset
    if target_offset == stop_offset:
        return "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS", target_offset, stop_offset, target_offset
    if target_offset < stop_offset:
        return "TARGET_TOUCH_BEFORE_STOP_M15_PROXY", target_offset, stop_offset, target_offset
    return "STOP_TOUCH_BEFORE_TARGET_M15_PROXY", target_offset, stop_offset, stop_offset


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_recovered_unfilled_path_control_packet",
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
        "route": "historical_ohlc_gtos_replay_recovered_unfilled_path_control_packet",
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
    probe_result = read_json(UNFILLED_PROBE_RESULT_PATH)
    entry_rows = [row for row in read_jsonl(ENTRY_WINDOW_PROBE_PATH) if not row.get("_parse_error")]
    signature_rows = [row for row in read_jsonl(SIGNATURE_PROBE_PATH) if not row.get("_parse_error")]
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    cost_by_entry = {
        row["entry_variant_id"]: row
        for row in cost_rows
        if row.get("cost_model") == "ZERO_COST_CONTROL"
    }
    recovered_entry_rows = [
        row
        for row in entry_rows
        if row["unfilled_probe_status"]
        in {"TICK_FILL_SIDE_TOUCH_RECOVERED", "M1_BID_BAR_TOUCH_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED"}
    ]
    recovered_entry_ids = {row["entry_variant_id"] for row in recovered_entry_rows}
    recovered_signature_rows = [row for row in signature_rows if row["entry_variant_id"] in recovered_entry_ids]
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    index_by_symbol_time: dict[str, dict[str, int]] = {}
    for symbol in sorted({row["symbol"] for row in recovered_entry_rows}):
        bars, by_time = pathmod.load_m15_bars(symbol)
        bars_by_symbol[symbol] = bars
        index_by_symbol_time[symbol] = by_time

    entry_path_rows: list[dict[str, Any]] = []
    entry_context_by_id: dict[str, dict[str, Any]] = {}
    for seq, row in enumerate(recovered_entry_rows, 1):
        fill_time, fill_source = recovered_fill_time(row)
        cost = cost_by_entry.get(row["entry_variant_id"], {})
        source_time = parse_utc(str(cost.get("source_time_utc")))
        horizon_bars = int(cost.get("horizon_bars") or 0)
        horizon_end = source_time + timedelta(minutes=15 * (horizon_bars + 1))
        fill_dt = parse_utc(fill_time) if fill_time else None
        fill_bar_time = floor_m15(fill_dt) if fill_dt else None
        symbol = row["symbol"]
        fill_bar_index = index_by_symbol_time.get(symbol, {}).get(iso_utc(fill_bar_time)) if fill_bar_time else None
        horizon_end_index = index_by_symbol_time.get(symbol, {}).get(iso_utc(horizon_end - timedelta(minutes=15)))
        path: list[tuple[int, dict[str, Any]]] = []
        if fill_bar_index is not None and horizon_end_index is not None:
            bars = bars_by_symbol.get(symbol, [])
            for idx in range(fill_bar_index, min(horizon_end_index, len(bars) - 1) + 1):
                path.append((idx - fill_bar_index, bars[idx]))
        unit = pathmod.numeric(cost.get("rolling_median_range"))
        entry_price = pathmod.numeric(cost.get("entry_price_input_only"))
        descriptor = pathmod.path_extremes(row["side"], entry_price, unit, path)
        if fill_dt is None:
            entry_recovered_status = "RECOVERED_FILL_TIME_MISSING_FAIL_CLOSED"
        elif fill_bar_index is None:
            entry_recovered_status = "RECOVERED_FILL_BAR_M15_SOURCE_MISSING_FAIL_CLOSED"
        elif not path:
            entry_recovered_status = "RECOVERED_FILL_PATH_EMPTY_FAIL_CLOSED"
        else:
            entry_recovered_status = recovered_path_status(row, None)
        entry_path_row = {
            "recovered_entry_path_id": f"OHLC-GTOS-RECOVERED-UNFILLED-ENTRY-{seq:05d}",
            "entry_variant_id": row["entry_variant_id"],
            "event_id": row["event_id"],
            "route_candidate_id": row["route_candidate_id"],
            "symbol": symbol,
            "side": row["side"],
            "entry_variant": row["entry_variant"],
            "entry_price_input_only": entry_price,
            "rolling_median_range": unit,
            "source_time_utc": row["source_time_utc"],
            "recovered_fill_time_utc": fill_time,
            "recovered_fill_source": fill_source,
            "fill_bar_time_utc": iso_utc(fill_bar_time) if fill_bar_time else None,
            "horizon_end_utc": iso_utc(horizon_end),
            "path_bar_count_from_recovered_fill": len(path),
            "entry_recovered_path_status": entry_recovered_status,
            **descriptor,
            "source_manifest_hash": manifest_hash,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_ENTRY_PATH",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        entry_path_rows.append(entry_path_row)
        entry_context_by_id[row["entry_variant_id"]] = {
            "entry": row,
            "cost": cost,
            "path": path,
            "unit": unit,
            "entry_price": entry_price,
            "fill_source": fill_source,
            "fill_time": fill_time,
            "fill_bar_time": iso_utc(fill_bar_time) if fill_bar_time else None,
        }

    signature_path_rows: list[dict[str, Any]] = []
    touch_counter: Counter[str] = Counter()
    recovered_status_counter: Counter[str] = Counter()
    fill_source_counter: Counter[str] = Counter()
    route_touch_counter: Counter[tuple[str, str]] = Counter()
    for seq, row in enumerate(recovered_signature_rows, 1):
        ctx = entry_context_by_id[row["entry_variant_id"]]
        entry_price = ctx["entry_price"]
        unit = ctx["unit"]
        path = ctx["path"]
        target_price = None
        stop_price = None
        target_offset = None
        stop_offset = None
        first_touch_offset = None
        if entry_price is None or unit is None or unit <= 0 or not path:
            first_status = "RECOVERED_PATH_TARGET_STOP_UNAVAILABLE_FAIL_CLOSED"
        else:
            sign = pathmod.side_sign(row["side"])
            target_price = entry_price + sign * float(row["target_multiple"]) * unit
            stop_price = entry_price - sign * float(row["stop_multiple"]) * unit
            first_status, target_offset, stop_offset, first_touch_offset = touch_status_with_fill_bar(
                row["side"],
                target_price,
                stop_price,
                path,
            )
            if first_touch_offset == 0:
                first_status = f"FILL_BAR_{first_status}_ORDER_UNRESOLVED"
        recovered_status = recovered_path_status(ctx["entry"], first_touch_offset)
        touch_counter[first_status] += 1
        recovered_status_counter[recovered_status] += 1
        fill_source_counter[ctx["fill_source"]] += 1
        route_touch_counter[(row["route_candidate_id"], first_status)] += 1
        signature_path_rows.append(
            {
                "recovered_signature_path_id": f"OHLC-GTOS-RECOVERED-UNFILLED-SIG-{seq:05d}",
                "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
                "entry_variant_id": row["entry_variant_id"],
                "event_id": row["event_id"],
                "route_candidate_id": row["route_candidate_id"],
                "symbol": row["symbol"],
                "side": row["side"],
                "entry_variant": row["entry_variant"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "target_multiple": row["target_multiple"],
                "stop_multiple": row["stop_multiple"],
                "entry_price_input_only": entry_price,
                "target_price": round(target_price, 6) if target_price is not None else None,
                "stop_price": round(stop_price, 6) if stop_price is not None else None,
                "recovered_fill_time_utc": ctx["fill_time"],
                "recovered_fill_source": ctx["fill_source"],
                "fill_bar_time_utc": ctx["fill_bar_time"],
                "recovered_first_touch_status": first_status,
                "target_touch_offset_from_fill_bar": target_offset,
                "stop_touch_offset_from_fill_bar": stop_offset,
                "first_touch_offset_from_fill_bar": first_touch_offset,
                "recovered_path_status": recovered_status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    bucket_rows: list[dict[str, Any]] = []

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("recovered_first_touch_status", touch_counter)
    add_bucket("recovered_path_status", recovered_status_counter)
    add_bucket("recovered_fill_source", fill_source_counter)
    add_bucket("route_candidate_id__recovered_first_touch_status", route_touch_counter)
    add_bucket("entry_window_recovered_status", Counter(row["unfilled_probe_status"] for row in recovered_entry_rows))

    question_rows = [
        {
            "question_id": "OHLC-GTOS-RECOVERED-UNFILLED-PATH-QUESTION-001",
            "question": "Which recovered exact-tick fills have source-safe post-fill target/stop paths versus fill-bar order ambiguity?",
            "row_count": fill_source_counter.get("EXACT_TICK_FILL_SIDE_TOUCH", 0),
            "next_same_resource_action": "split exact tick recovered rows by fill-bar ambiguity and join to execution-friction branch design",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-UNFILLED-PATH-QUESTION-002",
            "question": "Which M1 recovered rows are only bid-bar proxies and must remain fill-side-unresolved stress controls?",
            "row_count": fill_source_counter.get("M1_BID_BAR_TOUCH_PROXY_FILL_SIDE_UNRESOLVED", 0),
            "next_same_resource_action": "join M1 proxy rows to bid/ask acquisition/stress requirements rather than treating them as exact fills",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-RECOVERED-UNFILLED-PATH-QUESTION-003",
            "question": "Which recovered target/stop paths need lower-timeframe ordering because the first touch occurs in the fill M15 bar?",
            "row_count": sum(count for status, count in touch_counter.items() if str(status).startswith("FILL_BAR_")),
            "next_same_resource_action": "route fill-bar target/stop rows to M1/tick ordering reconstruction or conservative stress pairs",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "entry_path_rows": len(entry_path_rows),
        "question_rows": len(question_rows),
        "recovered_entry_input_rows": len(recovered_entry_rows),
        "recovered_signature_input_rows": len(recovered_signature_rows),
        "signature_path_rows": len(signature_path_rows),
        "source_manifest_rows": len(manifest_rows),
        "unfilled_entry_probe_input_rows": len(entry_rows),
        "unfilled_signature_probe_input_rows": len(signature_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_recovered_unfilled_path_control_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_PATH_CONTROL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This recovered-unfilled path-control packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "recovered_first_touch_status_counts": dict(sorted(touch_counter.items())),
        "recovered_path_status_counts": dict(sorted(recovered_status_counter.items())),
        "recovered_fill_source_counts": dict(sorted(fill_source_counter.items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "upstream_unfilled_probe_counts": probe_result.get("counts", {}),
        "next_same_resource_work": [
            "join recovered exact/proxy rows to no-fill geometry and exact-spread controls",
            "route fill-bar order-ambiguous recovered rows to M1/tick ordering stress",
            "split tick-confirmed no-fill families into execution-friction avoid/fillability branches",
        ],
    }

    write_jsonl(ENTRY_PATH_PATH, entry_path_rows)
    write_jsonl(SIGNATURE_PATH_CONTROL_PATH, signature_path_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Recovered-Unfilled Path Controls",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet recomputes M15 target/stop paths for recovered unfilled entry probes while separating exact tick fills from M1 bid-bar proxy recoveries.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Recovered Path Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(recovered_status_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Join recovered exact/proxy rows to no-fill geometry and exact-spread controls.",
                "- Route fill-bar order-ambiguous recovered rows to M1/tick ordering stress.",
                "- Split tick-confirmed no-fill families into execution-friction avoid/fillability branches.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
