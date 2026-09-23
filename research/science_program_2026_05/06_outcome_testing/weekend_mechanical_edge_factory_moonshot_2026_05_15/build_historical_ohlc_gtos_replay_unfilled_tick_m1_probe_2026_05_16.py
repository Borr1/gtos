#!/usr/bin/env python3
"""Probe cost-invariant unfilled replay entries with MT5 ticks and M1 bars."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

EXACT_PATH_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_RESULT_2026-05-16.json"
UNFILLED_SPLIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_UNFILLED_LEDGER_2026-05-16.jsonl"
UNFILLED_RECON_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_UNFILLED_RECON_ROUTE_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_RESULT_2026-05-16.json"
ENTRY_WINDOW_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ENTRY_WINDOW_PROBE_LEDGER_2026-05-16.jsonl"
SIGNATURE_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_SIGNATURE_PROBE_LEDGER_2026-05-16.jsonl"
ROUTE_FAMILY_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ROUTE_FAMILY_PROBE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS unfilled tick/M1 probe packet only. Rows attempt "
    "read-only MT5 tick and M1 reconstruction for cost-invariant unfilled "
    "retest-limit entries and join the result to all unfilled signatures; no "
    "validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or "
    "live behavior change is claimed."
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


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        EXACT_PATH_RESULT_PATH,
        UNFILLED_SPLIT_PATH,
        UNFILLED_RECON_ROUTE_PATH,
        COST_STATUS_PATH,
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


def spread_value_from_bid_ask(bid: float, ask: float) -> float | None:
    if bid <= 0 or ask <= 0 or ask < bid:
        return None
    return round((ask - bid) * 100.0, 6)


def side_fill_touch(side: str, bid: float, ask: float, entry: float) -> bool:
    if str(side).upper() == "SHORT":
        return bid >= entry
    return ask <= entry


def side_bid_bar_touch(side: str, high: float, low: float, entry: float) -> bool:
    if str(side).upper() == "SHORT":
        return high >= entry
    return low <= entry


def classify_probe(tick_status: str, tick_fill_touch: bool, m1_status: str, m1_bid_touch: bool) -> str:
    if tick_status == "EXACT_MT5_TICKS_AVAILABLE":
        return "TICK_FILL_SIDE_TOUCH_RECOVERED" if tick_fill_touch else "TICK_CONFIRMS_NO_FILL_SIDE_TOUCH"
    if m1_status == "MT5_M1_BARS_AVAILABLE":
        return "M1_BID_BAR_TOUCH_PROXY_RECOVERED_FILL_SIDE_UNRESOLVED" if m1_bid_touch else "M1_CONFIRMS_NO_BID_BAR_TOUCH"
    return "NO_MT5_TICK_OR_M1_HISTORY_STRESS_ONLY"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_unfilled_tick_m1_probe_packet",
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
        "route": "historical_ohlc_gtos_replay_unfilled_tick_m1_probe_packet",
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
    exact_path_result = read_json(EXACT_PATH_RESULT_PATH)
    unfilled_rows = [row for row in read_jsonl(UNFILLED_SPLIT_PATH) if not row.get("_parse_error")]
    recon_rows = [row for row in read_jsonl(UNFILLED_RECON_ROUTE_PATH) if not row.get("_parse_error")]
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    cost_by_entry = {
        row["entry_variant_id"]: row
        for row in cost_rows
        if row.get("cost_model") == "ZERO_COST_CONTROL"
    }
    entry_ids = sorted({row["entry_variant_id"] for row in unfilled_rows})

    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local terminal package
        mt5 = None
        mt5_init_ok = False
        mt5_init_error = f"{type(exc).__name__}: {exc}"
        terminal_summary = {"mt5_module_available": False, "mt5_initialize": False, "mt5_error": mt5_init_error}
    else:
        mt5_init_ok = bool(mt5.initialize())
        mt5_init_error = mt5.last_error()
        terminal_info = mt5.terminal_info() if mt5_init_ok else None
        terminal_summary = {
            "mt5_module_available": True,
            "mt5_initialize": mt5_init_ok,
            "mt5_last_error": mt5_init_error,
            "terminal_name": getattr(terminal_info, "name", None) if terminal_info is not None else None,
            "terminal_company": getattr(terminal_info, "company", None) if terminal_info is not None else None,
            "read_only_market_data_probe": True,
        }

    entry_probe_rows: list[dict[str, Any]] = []
    probe_by_entry: dict[str, dict[str, Any]] = {}
    symbol_select_cache: dict[str, tuple[bool, Any]] = {}
    try:
        for seq, entry_id in enumerate(entry_ids, 1):
            cost = cost_by_entry.get(entry_id, {})
            symbol = str(cost.get("symbol"))
            side = str(cost.get("side"))
            source_time = parse_utc(str(cost.get("source_time_utc")))
            horizon_bars = int(cost.get("horizon_bars") or 0)
            entry_price = float(cost.get("entry_price_input_only"))
            window_start = source_time + timedelta(minutes=15)
            window_end = source_time + timedelta(minutes=15 * (horizon_bars + 1))
            base = {
                "unfilled_entry_probe_id": f"OHLC-GTOS-UNFILLED-PROBE-{seq:05d}",
                "entry_variant_id": entry_id,
                "event_id": cost.get("event_id"),
                "route_candidate_id": cost.get("route_candidate_id"),
                "symbol": symbol,
                "side": side,
                "entry_variant": cost.get("entry_variant"),
                "entry_price_input_only": entry_price,
                "source_time_utc": iso_utc(source_time),
                "probe_window_start_utc": iso_utc(window_start),
                "probe_window_end_utc": iso_utc(window_end),
                "horizon_bars": horizon_bars,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ENTRY_WINDOW_PROBE",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            tick_status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
            m1_status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
            tick_count = 0
            m1_count = 0
            tick_fill_touch = False
            tick_bid_touch = False
            tick_mid_touch = False
            first_tick_fill_touch_utc = None
            first_tick_bid_touch_utc = None
            first_tick_mid_touch_utc = None
            first_tick_spread_value = None
            m1_bid_touch = False
            first_m1_touch_utc = None
            if mt5 is not None and mt5_init_ok:
                if symbol not in symbol_select_cache:
                    symbol_select_cache[symbol] = (bool(mt5.symbol_select(symbol, True)), mt5.last_error())
                selected, select_error = symbol_select_cache[symbol]
                if not selected:
                    tick_status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
                    m1_status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
                    base["mt5_symbol_select_error"] = str(select_error)
                else:
                    ticks = mt5.copy_ticks_range(symbol, window_start, window_end, mt5.COPY_TICKS_ALL)
                    if ticks is None:
                        tick_status = "MT5_COPY_TICKS_RETURNED_NONE_FAIL_CLOSED"
                        base["mt5_tick_error"] = str(mt5.last_error())
                    else:
                        tick_count = len(ticks)
                        tick_status = "MT5_NO_TICKS_IN_PROBE_WINDOW_FAIL_CLOSED" if tick_count == 0 else "EXACT_MT5_TICKS_AVAILABLE"
                        for tick in ticks:
                            tick_ms = int(tick["time_msc"])
                            tick_dt = datetime.fromtimestamp(tick_ms / 1000.0, tz=timezone.utc)
                            bid = float(tick["bid"])
                            ask = float(tick["ask"])
                            if first_tick_spread_value is None:
                                first_tick_spread_value = spread_value_from_bid_ask(bid, ask)
                            if side_fill_touch(side, bid, ask, entry_price) and not tick_fill_touch:
                                tick_fill_touch = True
                                first_tick_fill_touch_utc = iso_utc(tick_dt)
                            if side_bid_bar_touch(side, bid, bid, entry_price) and not tick_bid_touch:
                                tick_bid_touch = True
                                first_tick_bid_touch_utc = iso_utc(tick_dt)
                            mid = (bid + ask) / 2.0 if ask >= bid > 0 else None
                            if mid is not None:
                                mid_touch = mid >= entry_price if side.upper() == "SHORT" else mid <= entry_price
                                if mid_touch and not tick_mid_touch:
                                    tick_mid_touch = True
                                    first_tick_mid_touch_utc = iso_utc(tick_dt)
                    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, window_start, window_end)
                    if rates is None:
                        m1_status = "MT5_COPY_RATES_M1_RETURNED_NONE_FAIL_CLOSED"
                        base["mt5_m1_error"] = str(mt5.last_error())
                    else:
                        m1_count = len(rates)
                        m1_status = "MT5_NO_M1_BARS_IN_PROBE_WINDOW_FAIL_CLOSED" if m1_count == 0 else "MT5_M1_BARS_AVAILABLE"
                        for rate in rates:
                            high = float(rate["high"])
                            low = float(rate["low"])
                            if side_bid_bar_touch(side, high, low, entry_price):
                                m1_bid_touch = True
                                first_m1_touch_utc = iso_utc(datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc))
                                break
            probe_status = classify_probe(tick_status, tick_fill_touch, m1_status, m1_bid_touch)
            probe_row = {
                **base,
                "tick_source_status": tick_status,
                "ticks_returned": tick_count,
                "tick_fill_side_touch": tick_fill_touch,
                "tick_bid_side_touch": tick_bid_touch,
                "tick_mid_touch": tick_mid_touch,
                "first_tick_fill_touch_utc": first_tick_fill_touch_utc,
                "first_tick_bid_touch_utc": first_tick_bid_touch_utc,
                "first_tick_mid_touch_utc": first_tick_mid_touch_utc,
                "first_tick_spread_value": first_tick_spread_value,
                "m1_source_status": m1_status,
                "m1_bars_returned": m1_count,
                "m1_bid_bar_touch": m1_bid_touch,
                "first_m1_touch_utc": first_m1_touch_utc,
                "unfilled_probe_status": probe_status,
            }
            entry_probe_rows.append(probe_row)
            probe_by_entry[entry_id] = probe_row
    finally:
        if mt5 is not None and mt5_init_ok:
            mt5.shutdown()

    signature_probe_rows: list[dict[str, Any]] = []
    for row in unfilled_rows:
        probe = probe_by_entry[row["entry_variant_id"]]
        signature_probe_rows.append(
            {
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
                "tick_source_status": probe["tick_source_status"],
                "m1_source_status": probe["m1_source_status"],
                "unfilled_probe_status": probe["unfilled_probe_status"],
                "tick_fill_side_touch": probe["tick_fill_side_touch"],
                "m1_bid_bar_touch": probe["m1_bid_bar_touch"],
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_SIGNATURE_PROBE",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    family_counter: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    family_example: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in signature_probe_rows:
        key = (row["route_candidate_id"], row["symbol"], row["side"], row["entry_variant"])
        family_counter[key][row["unfilled_probe_status"]] += 1
        family_example.setdefault(key, row)
    route_family_rows: list[dict[str, Any]] = []
    for seq, (key, counter) in enumerate(sorted(family_counter.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        route_family_rows.append(
            {
                "unfilled_route_family_probe_id": f"OHLC-GTOS-UNFILLED-FAMILY-{seq:04d}",
                "route_candidate_id": key[0],
                "symbol": key[1],
                "side": key[2],
                "entry_variant": key[3],
                "signature_rows": sum(counter.values()),
                "probe_status_counts": dict(sorted(counter.items())),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ROUTE_FAMILY_PROBE",
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
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("entry_window_probe_status", Counter(row["unfilled_probe_status"] for row in entry_probe_rows))
    add_bucket("signature_probe_status", Counter(row["unfilled_probe_status"] for row in signature_probe_rows))
    add_bucket("tick_source_status", Counter(row["tick_source_status"] for row in entry_probe_rows))
    add_bucket("m1_source_status", Counter(row["m1_source_status"] for row in entry_probe_rows))
    add_bucket("symbol__entry_window_probe_status", Counter((row["symbol"], row["unfilled_probe_status"]) for row in entry_probe_rows))
    add_bucket("entry_variant__entry_window_probe_status", Counter((row["entry_variant"], row["unfilled_probe_status"]) for row in entry_probe_rows))
    add_bucket("route__signature_probe_status", Counter((row["route_candidate_id"], row["unfilled_probe_status"]) for row in signature_probe_rows))

    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNFILLED-TICK-M1-QUESTION-001",
            "question": "Which cost-invariant unfilled entries are confirmed unfilled by exact tick fill-side evidence?",
            "row_count": sum(1 for row in entry_probe_rows if row["unfilled_probe_status"] == "TICK_CONFIRMS_NO_FILL_SIDE_TOUCH"),
            "next_same_resource_action": "join tick-confirmed no-fill rows to no-fill geometry controls and execution-friction avoid/fillability branches",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-UNFILLED-TICK-M1-QUESTION-002",
            "question": "Which entries recover a fill touch under exact tick or M1 bid-bar proxy despite M15 no-fill status?",
            "row_count": sum(1 for row in entry_probe_rows if "RECOVERED" in row["unfilled_probe_status"]),
            "next_same_resource_action": "split recovered rows by tick-exact versus M1-proxy and recompute target/stop path only where source-safe",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-UNFILLED-TICK-M1-QUESTION-003",
            "question": "Which unavailable tick/M1 windows need broader MT5 history extraction or OHLC stress proxy?",
            "row_count": sum(1 for row in entry_probe_rows if row["unfilled_probe_status"] == "NO_MT5_TICK_OR_M1_HISTORY_STRESS_ONLY"),
            "next_same_resource_action": "split unavailable windows by date/symbol and route to broader MT5 history, local source search, or explicit stress-only controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "entry_window_probe_rows": len(entry_probe_rows),
        "question_rows": len(question_rows),
        "recon_route_input_rows": len(recon_rows),
        "route_family_probe_rows": len(route_family_rows),
        "signature_probe_rows": len(signature_probe_rows),
        "source_manifest_rows": len(manifest_rows),
        "unfilled_signature_input_rows": len(unfilled_rows),
        "unique_entry_variant_input_rows": len(entry_ids),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_unfilled_tick_m1_probe_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This unfilled tick/M1 probe packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "entry_window_probe_status_counts": dict(sorted(Counter(row["unfilled_probe_status"] for row in entry_probe_rows).items())),
        "signature_probe_status_counts": dict(sorted(Counter(row["unfilled_probe_status"] for row in signature_probe_rows).items())),
        "tick_source_status_counts": dict(sorted(Counter(row["tick_source_status"] for row in entry_probe_rows).items())),
        "m1_source_status_counts": dict(sorted(Counter(row["m1_source_status"] for row in entry_probe_rows).items())),
        "terminal_summary": terminal_summary,
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "upstream_exact_path_counts": exact_path_result.get("counts", {}),
        "next_same_resource_work": [
            "recompute target/stop paths for any tick/M1 recovered fill rows with source-safe ordering",
            "join tick-confirmed no-fill rows to no-fill geometry and exact-spread controls",
            "split unavailable windows by date/symbol and run broader MT5/local-source acquisition or stress proxy",
        ],
    }

    write_jsonl(ENTRY_WINDOW_PROBE_PATH, entry_probe_rows)
    write_jsonl(SIGNATURE_PROBE_PATH, signature_probe_rows)
    write_jsonl(ROUTE_FAMILY_PROBE_PATH, route_family_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Unfilled Tick/M1 Probe",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet probes every unique cost-invariant unfilled retest-limit entry window with read-only MT5 ticks and M1 bars, then joins probe labels to all unfilled signatures.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Entry Probe Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(Counter(row["unfilled_probe_status"] for row in entry_probe_rows).items())),
                "",
                "## Immediate Work",
                "",
                "- Recompute target/stop paths for any recovered fill rows with source-safe ordering.",
                "- Join tick-confirmed no-fill rows to no-fill geometry and exact-spread controls.",
                "- Split unavailable windows by date/symbol and run broader MT5/local-source acquisition or stress proxy.",
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
