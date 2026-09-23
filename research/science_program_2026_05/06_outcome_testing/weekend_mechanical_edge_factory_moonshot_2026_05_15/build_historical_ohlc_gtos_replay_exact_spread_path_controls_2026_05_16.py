#!/usr/bin/env python3
"""Recompute path controls for gradient rows with exact MT5 spread evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(ROUTE_DIR))

import build_historical_ohlc_gtos_replay_path_control_packet_2026_05_16 as pathmod  # noqa: E402


FAMILY_SPREAD_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_RESULT_2026-05-16.json"
GRADIENT_EXACT_SPREAD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_GRADIENT_EXACT_SPREAD_LEDGER_2026-05-16.jsonl"
SPREAD_STRESS_BOUND_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPREAD_STRESS_BOUND_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_RESULT_2026-05-16.json"
EXACT_PATH_CONTROL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_LEDGER_2026-05-16.jsonl"
EXACT_DESCRIPTOR_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
UNAVAILABLE_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS exact-spread path-control packet only. Rows recompute "
    "M15 path descriptors for gradient-sensitive signatures where exact MT5 "
    "reference spread exists and preserve unavailable rows as stress-only "
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


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        FAMILY_SPREAD_RESULT_PATH,
        GRADIENT_EXACT_SPREAD_PATH,
        SPREAD_STRESS_BOUND_PATH,
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


def rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def descriptor_delta_status(exact: str, low: str, high: str) -> str:
    if exact == low and exact == high:
        return "EXACT_MATCHES_LOW_AND_HIGH_PROXY_DESCRIPTOR"
    if exact == low:
        return "EXACT_MATCHES_LOW_PROXY_DESCRIPTOR"
    if exact == high:
        return "EXACT_MATCHES_HIGH_STATIC_PROXY_DESCRIPTOR"
    return "EXACT_DIFFERS_FROM_LOW_AND_HIGH_PROXY_DESCRIPTOR"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_exact_spread_path_control_packet",
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
        "route": "historical_ohlc_gtos_replay_exact_spread_path_control_packet",
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
    family_result = read_json(FAMILY_SPREAD_RESULT_PATH)
    gradient_rows = [row for row in read_jsonl(GRADIENT_EXACT_SPREAD_PATH) if not row.get("_parse_error")]
    stress_rows = [row for row in read_jsonl(SPREAD_STRESS_BOUND_PATH) if not row.get("_parse_error")]
    cost_status_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    zero_cost_by_entry = {
        row["entry_variant_id"]: row
        for row in cost_status_rows
        if row.get("cost_model") == "ZERO_COST_CONTROL"
    }

    exact_input_rows = [
        row
        for row in gradient_rows
        if row.get("exact_spread_source_status") == "EXACT_MT5_TICK_SPREAD_AT_REFERENCE_AVAILABLE"
        and isinstance(row.get("first_spread_value"), (int, float))
    ]
    unavailable_rows = [
        row
        for row in gradient_rows
        if row.get("exact_spread_source_status") != "EXACT_MT5_TICK_SPREAD_AT_REFERENCE_AVAILABLE"
    ]
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    index_by_symbol_time: dict[str, dict[str, int]] = {}
    for symbol in sorted({row["symbol"] for row in exact_input_rows}):
        bars, by_time = pathmod.load_m15_bars(symbol)
        bars_by_symbol[symbol] = bars
        index_by_symbol_time[symbol] = by_time

    exact_path_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    unavailable_stress_rows: list[dict[str, Any]] = []
    exact_status_counter: Counter[str] = Counter()
    delta_status_counter: Counter[str] = Counter()
    spread_bucket_counter: Counter[str] = Counter()
    route_delta_counter: Counter[tuple[str, str]] = Counter()
    entry_delta_counter: Counter[tuple[str, str]] = Counter()

    for seq, row in enumerate(exact_input_rows, 1):
        zero = zero_cost_by_entry.get(row["entry_variant_id"], {})
        symbol = row["symbol"]
        source_time = zero.get("source_time_utc")
        horizon_bars = int(zero.get("horizon_bars") or 0)
        bar_index = index_by_symbol_time.get(symbol, {}).get(source_time)
        future = pathmod.future_window(bars_by_symbol.get(symbol, []), bar_index, horizon_bars)
        fill_offset = zero.get("fill_offset_bars")
        if fill_offset is not None:
            fill_offset = int(fill_offset)
        path = pathmod.path_after_fill(future, fill_offset)
        entry_price = pathmod.numeric(zero.get("entry_price_input_only"))
        exact_spread = float(row["first_spread_value"])
        exact_spread_distance = pathmod.spread_price_distance(exact_spread)
        effective_entry = pathmod.effective_entry(entry_price, exact_spread_distance, row["side"])
        unit = pathmod.numeric(zero.get("rolling_median_range"))
        target_price = None
        stop_price = None
        target_offset = None
        stop_offset = None
        first_touch_offset = None
        if (
            bar_index is None
            or fill_offset is None
            or effective_entry is None
            or unit is None
            or unit <= 0
            or not path
        ):
            exact_status = "EXACT_SPREAD_PATH_RECOMPUTE_UNAVAILABLE_FAIL_CLOSED"
            descriptor = pathmod.path_extremes(row["side"], effective_entry, unit, path)
        else:
            sign = pathmod.side_sign(row["side"])
            target_price = effective_entry + sign * float(row["target_multiple"]) * unit
            stop_price = effective_entry - sign * float(row["stop_multiple"]) * unit
            exact_status, target_offset, stop_offset, first_touch_offset = pathmod.touch_status(
                row["side"],
                target_price,
                stop_price,
                path,
            )
            descriptor = pathmod.path_extremes(row["side"], effective_entry, unit, path)
        exact_status_counter[exact_status] += 1
        spread_bucket_counter[row["exact_spread_proxy_bucket"]] += 1
        low_status = row.get("median_descriptor_status") or row.get("low_spread_descriptor_status")
        high_status = row.get("static_descriptor_status") or row.get("high_spread_descriptor_status")
        delta_status = descriptor_delta_status(exact_status, str(low_status), str(high_status))
        delta_status_counter[delta_status] += 1
        route_delta_counter[(row["route_candidate_id"], delta_status)] += 1
        entry_delta_counter[(row["entry_variant"], delta_status)] += 1

        exact_path_rows.append(
            {
                "exact_path_control_id": f"OHLC-GTOS-EXACT-SPREAD-PATH-{seq:05d}",
                "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
                "route_candidate_id": row["route_candidate_id"],
                "event_id": row["event_id"],
                "entry_variant_id": row["entry_variant_id"],
                "entry_variant": row["entry_variant"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "symbol": symbol,
                "side": row["side"],
                "source_time_utc": source_time,
                "reference_time_utc": row.get("reference_time_utc"),
                "exact_spread_value": exact_spread,
                "exact_spread_price_distance": rounded(exact_spread_distance),
                "entry_price_input_only": rounded(entry_price),
                "exact_effective_entry_price": rounded(effective_entry),
                "rolling_median_range": rounded(unit),
                "target_multiple": row["target_multiple"],
                "stop_multiple": row["stop_multiple"],
                "target_price": rounded(target_price),
                "stop_price": rounded(stop_price),
                "fill_offset_bars": fill_offset,
                "path_bar_count": len(path),
                "exact_first_touch_status": exact_status,
                "target_touch_offset_bars": target_offset,
                "stop_touch_offset_bars": stop_offset,
                "first_touch_offset_bars": first_touch_offset,
                **descriptor,
                "exact_spread_proxy_bucket": row["exact_spread_proxy_bucket"],
                "low_spread_descriptor_status": low_status,
                "high_spread_descriptor_status": high_status,
                "descriptor_delta_status": delta_status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        delta_rows.append(
            {
                "exact_descriptor_delta_id": f"OHLC-GTOS-EXACT-SPREAD-DELTA-{seq:05d}",
                "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
                "route_candidate_id": row["route_candidate_id"],
                "event_id": row["event_id"],
                "entry_variant_id": row["entry_variant_id"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "symbol": symbol,
                "entry_variant": row["entry_variant"],
                "target_multiple": row["target_multiple"],
                "stop_multiple": row["stop_multiple"],
                "exact_spread_value": exact_spread,
                "tested_low_spread_proxy_value": row.get("median_spread_proxy_value"),
                "tested_high_spread_proxy_value": row.get("static_spread_proxy_value"),
                "low_spread_descriptor_status": low_status,
                "high_spread_descriptor_status": high_status,
                "exact_first_touch_status": exact_status,
                "descriptor_delta_status": delta_status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    stress_by_id = {row["cost_sensitivity_signature_id"]: row for row in stress_rows}
    for seq, row in enumerate(unavailable_rows, 1):
        stress = stress_by_id.get(row["cost_sensitivity_signature_id"], {})
        unavailable_stress_rows.append(
            {
                "unavailable_stress_id": f"OHLC-GTOS-EXACT-SPREAD-UNAVAILABLE-{seq:05d}",
                "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
                "route_candidate_id": row["route_candidate_id"],
                "event_id": row["event_id"],
                "entry_variant_id": row["entry_variant_id"],
                "entry_variant": row["entry_variant"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "symbol": row["symbol"],
                "side": row["side"],
                "target_multiple": row["target_multiple"],
                "stop_multiple": row["stop_multiple"],
                "exact_spread_source_status": row["exact_spread_source_status"],
                "exact_spread_proxy_bucket": row["exact_spread_proxy_bucket"],
                "low_spread_descriptor_status": stress.get("low_spread_descriptor_status"),
                "high_spread_descriptor_status": stress.get("high_spread_descriptor_status"),
                "stress_bound_status": stress.get("stress_bound_status"),
                "next_same_resource_action": "use low/high proxy descriptor stress pair and/or broader MT5 tick-history acquisition attempt; do not wait for future data",
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS",
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
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("exact_first_touch_status", exact_status_counter)
    add_bucket("descriptor_delta_status", delta_status_counter)
    add_bucket("exact_spread_proxy_bucket_exact_rows", spread_bucket_counter)
    add_bucket("route_candidate_id__descriptor_delta_status", route_delta_counter)
    add_bucket("entry_variant__descriptor_delta_status", entry_delta_counter)
    add_bucket("unavailable_source_status", Counter(row["exact_spread_source_status"] for row in unavailable_stress_rows))

    question_rows = [
        {
            "question_id": "OHLC-GTOS-EXACT-SPREAD-PATH-QUESTION-001",
            "question": "Which exact-spread rows resolve back to the low-spread descriptor versus the static or supra-static descriptor?",
            "row_count": len(exact_path_rows),
            "next_same_resource_action": "join exact descriptor deltas to route/entry/target-stop families and isolate stress-sensitive execution-friction branches",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-EXACT-SPREAD-PATH-QUESTION-002",
            "question": "Which unavailable exact-spread rows are still answerable from proxy/stress pairs or broader tick-history acquisition?",
            "row_count": len(unavailable_stress_rows),
            "next_same_resource_action": "split unavailable rows by stress-pair descriptor direction and route to MT5/broker-history/proxy acquisition without future-data waiting",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-EXACT-SPREAD-PATH-QUESTION-003",
            "question": "Do exact rows above the static proxy create new path descriptors beyond the tested static conservative fallback?",
            "row_count": delta_status_counter.get("EXACT_DIFFERS_FROM_LOW_AND_HIGH_PROXY_DESCRIPTOR", 0),
            "next_same_resource_action": "materialize supra-static stress branch rows where exact spread changes descriptor beyond both tested proxies",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "exact_descriptor_delta_rows": len(delta_rows),
        "exact_gradient_input_rows": len(exact_input_rows),
        "exact_path_control_rows": len(exact_path_rows),
        "gradient_input_rows": len(gradient_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "spread_stress_input_rows": len(stress_rows),
        "unavailable_gradient_rows": len(unavailable_rows),
        "unavailable_stress_rows": len(unavailable_stress_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_exact_spread_path_control_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_PATH_CONTROL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This exact-spread path-control packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "exact_first_touch_status_counts": dict(sorted(exact_status_counter.items())),
        "descriptor_delta_status_counts": dict(sorted(delta_status_counter.items())),
        "exact_spread_proxy_bucket_exact_row_counts": dict(sorted(spread_bucket_counter.items())),
        "unavailable_source_status_counts": dict(
            sorted(Counter(row["exact_spread_source_status"] for row in unavailable_stress_rows).items())
        ),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "upstream_family_spread_counts": family_result.get("counts", {}),
        "next_same_resource_work": [
            "split exact descriptor deltas by route/entry/target-stop and execution-friction branch role",
            "probe unfilled retest-limit families with MT5 tick/M1 touch reconstruction",
            "join exact-spread path controls to same-M15 ambiguity and no-fill geometry controls",
        ],
    }

    write_jsonl(EXACT_PATH_CONTROL_PATH, exact_path_rows)
    write_jsonl(EXACT_DESCRIPTOR_DELTA_PATH, delta_rows)
    write_jsonl(UNAVAILABLE_STRESS_PATH, unavailable_stress_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Exact-Spread Path-Control Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet recomputes M15 path controls for gradient-sensitive signatures where exact MT5 reference spread exists, and preserves unavailable exact-spread rows as stress-only controls.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Descriptor Delta Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(delta_status_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Split exact descriptor deltas by route/entry/target-stop and execution-friction role.",
                "- Probe unfilled retest-limit families with MT5 tick/M1 touch reconstruction.",
                "- Join exact-spread path controls to same-M15 ambiguity and no-fill geometry controls.",
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
