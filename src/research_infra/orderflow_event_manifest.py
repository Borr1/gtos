"""Build Databento orderflow harvest manifests from GTOS shadow rows.

Research-only helpers. They read candidate/structure shadow logs and produce
timestamped event windows for futures data pulls. No live trading code imports
this module.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


FUTURES_PROXY_MAP: dict[str, tuple[str, ...]] = {
    "XAUUSD": ("GC.v.0",),
    "XAGUSD": ("SI.v.0",),
    "NAS100": ("NQ.v.0",),
    "US30": ("YM.v.0", "ES.v.0"),
    "US30_cash": ("YM.v.0", "ES.v.0"),
    "GBPUSD": ("6B.v.0",),
}


def parse_utc(value: str) -> datetime:
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def floor_to_m15(value: datetime) -> datetime:
    value = value.astimezone(timezone.utc)
    minute = (value.minute // 15) * 15
    return value.replace(minute=minute, second=0, microsecond=0)


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def event_tags(row: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    decision = row.get("decision")
    if decision == "CANDIDATE":
        tags.append("candidate")
    if row.get("m15_choch_detected"):
        tags.append("m15_choch")
    c_gate = row.get("c_gate_result") or {}
    if c_gate.get("c2_m15_choch_detected"):
        tags.append("c_gate_m15_choch")
    if row.get("h4_aligned"):
        tags.append("h4_aligned")
    if (row.get("mso_h1_unmitigated_ob_count") or 0) > 0:
        tags.append("h1_ob_available")
    if (row.get("mso_h1_fvg_count") or 0) > 0:
        tags.append("h1_fvg_available")
    if (row.get("mso_m15_fvg_count") or 0) > 0:
        tags.append("m15_fvg_available")
    if (row.get("mso_detected_sweeps_count") or 0) > 0:
        tags.append("liquidity_sweeps_detected")

    same_side = row.get("mso_nearest_same_side_pool_distance_atr")
    opposite_side = row.get("mso_nearest_opposite_side_pool_distance_atr")
    for name, value in (("same_side_pool", same_side), ("opposite_side_pool", opposite_side)):
        if isinstance(value, (int, float)) and value <= 0.5:
            tags.append(f"near_{name}")

    zone = row.get("mso_pd_current_zone")
    if zone:
        tags.append(f"pd_{zone}")
    framework = row.get("framework")
    if framework and framework != "none":
        tags.append(f"framework_{framework}")
    return sorted(set(tags))


def event_class(row: dict[str, Any]) -> str:
    tags = set(event_tags(row))
    if "candidate" in tags:
        return "candidate"
    if "m15_choch" in tags or "c_gate_m15_choch" in tags:
        return "m15_choch_context"
    return "structural_context"


def include_event(row: dict[str, Any], *, candidates_only: bool) -> bool:
    symbol = str(row.get("symbol") or "")
    if symbol not in FUTURES_PROXY_MAP:
        return False
    if candidates_only:
        return row.get("decision") == "CANDIDATE"
    tags = set(event_tags(row))
    return bool(
        tags
        & {
            "candidate",
            "m15_choch",
            "c_gate_m15_choch",
            "h1_ob_available",
            "h1_fvg_available",
            "m15_fvg_available",
            "liquidity_sweeps_detected",
        }
    )


def build_events(
    rows: Iterable[dict[str, Any]],
    *,
    source_path: Path | str,
    pre_minutes: int,
    post_minutes: int,
    candidates_only: bool = False,
    available_end_utc: str | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    available_end = parse_utc(available_end_utc) if available_end_utc else None
    for idx, row in enumerate(rows, start=1):
        if not include_event(row, candidates_only=candidates_only):
            continue
        timestamp_raw = row.get("timestamp_utc")
        if not timestamp_raw:
            continue
        ts = parse_utc(str(timestamp_raw))
        candle_close = floor_to_m15(ts)
        start = candle_close - timedelta(minutes=pre_minutes)
        end = candle_close + timedelta(minutes=post_minutes)
        truncated = False
        if available_end is not None:
            if candle_close >= available_end:
                continue
            if end > available_end:
                end = available_end
                truncated = True
        symbol = str(row["symbol"])
        trade_params = row.get("trade_parameters") or {}
        event_id = (
            f"{symbol}_{candle_close.strftime('%Y%m%dT%H%M')}_"
            f"{event_class(row)}_{idx}"
        )
        events.append(
            {
                "event_id": event_id,
                "source_log": str(source_path),
                "source_row_number": idx,
                "symbol": symbol,
                "databento_symbols": list(FUTURES_PROXY_MAP[symbol]),
                "timestamp_utc": iso_utc(ts),
                "canonical_m15_close_utc": iso_utc(candle_close),
                "window_start_utc": iso_utc(start),
                "window_end_utc": iso_utc(end),
                "window_truncated_at_available_end": truncated,
                "event_class": event_class(row),
                "decision": row.get("decision"),
                "framework": row.get("framework"),
                "setup_grade": row.get("setup_grade"),
                "direction": trade_params.get("direction"),
                "kill_zone": row.get("kill_zone"),
                "session_tag": row.get("session_tag"),
                "daily_bias_direction": row.get("daily_bias_direction"),
                "h4_aligned": row.get("h4_aligned"),
                "m15_choch_detected": row.get("m15_choch_detected"),
                "h1_unmitigated_ob_count": row.get("mso_h1_unmitigated_ob_count"),
                "h1_fvg_count": row.get("mso_h1_fvg_count"),
                "m15_fvg_count": row.get("mso_m15_fvg_count"),
                "detected_sweeps_count": row.get("mso_detected_sweeps_count"),
                "nearest_same_side_pool_distance_atr": row.get("mso_nearest_same_side_pool_distance_atr"),
                "nearest_opposite_side_pool_distance_atr": row.get("mso_nearest_opposite_side_pool_distance_atr"),
                "pd_current_zone": row.get("mso_pd_current_zone"),
                "tags": event_tags(row),
            }
        )
    return events


def merge_fetch_groups(events: list[dict[str, Any]], *, merge_gap_minutes: int) -> list[dict[str, Any]]:
    raw_groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for event in events:
        key = tuple(event["databento_symbols"])
        raw_groups.setdefault(key, []).append(event)

    merged: list[dict[str, Any]] = []
    merge_gap = timedelta(minutes=merge_gap_minutes)
    for symbols, symbol_events in sorted(raw_groups.items()):
        sorted_events = sorted(symbol_events, key=lambda item: item["window_start_utc"])
        current: dict[str, Any] | None = None
        for event in sorted_events:
            start = parse_utc(event["window_start_utc"])
            end = parse_utc(event["window_end_utc"])
            if current is None:
                current = {
                    "databento_symbols": list(symbols),
                    "start_utc": iso_utc(start),
                    "end_utc": iso_utc(end),
                    "event_ids": [event["event_id"]],
                    "gtos_symbols": [event["symbol"]],
                    "event_classes": [event["event_class"]],
                }
                continue
            current_end = parse_utc(current["end_utc"])
            if start <= current_end + merge_gap:
                if end > current_end:
                    current["end_utc"] = iso_utc(end)
                current["event_ids"].append(event["event_id"])
                current["gtos_symbols"].append(event["symbol"])
                current["event_classes"].append(event["event_class"])
                continue
            merged.append(current)
            current = {
                "databento_symbols": list(symbols),
                "start_utc": iso_utc(start),
                "end_utc": iso_utc(end),
                "event_ids": [event["event_id"]],
                "gtos_symbols": [event["symbol"]],
                "event_classes": [event["event_class"]],
            }
        if current is not None:
            merged.append(current)

    for idx, group in enumerate(merged, start=1):
        group["group_id"] = f"ofwin_{idx:04d}"
        group["event_count"] = len(group["event_ids"])
        group["gtos_symbols"] = sorted(set(group["gtos_symbols"]))
        group["event_classes"] = sorted(Counter(group["event_classes"]).items())
        group["fetch_command"] = (
            "python scripts/fetch_databento_futures.py fetch "
            "--schema trades "
            f"--symbols {','.join(group['databento_symbols'])} "
            f"--start {group['start_utc']} "
            f"--end {group['end_utc']} "
            "--max-cost-usd 0.25"
        )
    return merged


def build_payload(
    rows: list[dict[str, Any]],
    *,
    source_path: Path | str,
    pre_minutes: int,
    post_minutes: int,
    merge_gap_minutes: int,
    candidates_only: bool = False,
    available_end_utc: str | None = None,
) -> dict[str, Any]:
    events = build_events(
        rows,
        source_path=source_path,
        pre_minutes=pre_minutes,
        post_minutes=post_minutes,
        candidates_only=candidates_only,
        available_end_utc=available_end_utc,
    )
    groups = merge_fetch_groups(events, merge_gap_minutes=merge_gap_minutes)
    symbol_counts = Counter(event["symbol"] for event in events)
    class_counts = Counter(event["event_class"] for event in events)
    truncated_count = sum(1 for event in events if event.get("window_truncated_at_available_end"))
    return {
        "schema_version": "orderflow_event_manifest_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "source_path": str(source_path),
            "rows_loaded": len(rows),
            "pre_minutes": pre_minutes,
            "post_minutes": post_minutes,
            "merge_gap_minutes": merge_gap_minutes,
            "candidates_only": candidates_only,
            "available_end_utc": available_end_utc,
            "supported_symbol_map": {key: list(value) for key, value in FUTURES_PROXY_MAP.items()},
        },
        "events": events,
        "fetch_groups": groups,
        "synthesis": {
            "summary": (
                "This manifest converts supported GTOS structure/candidate rows into "
                "Databento futures harvest windows. It is a data acquisition plan, "
                "not an alpha or promotion claim."
            ),
            "event_count": len(events),
            "fetch_group_count": len(groups),
            "truncated_event_windows": truncated_count,
            "symbol_counts": dict(sorted(symbol_counts.items())),
            "event_class_counts": dict(sorted(class_counts.items())),
            "ambiguities": [
                "canonical_m15_close_utc is inferred by flooring live wall-clock evaluation timestamps to the prior M15 boundary.",
                "The manifest only covers GTOS symbols with validated CME proxy mappings so far: XAUUSD, XAGUSD, NAS100, US30_cash/US30, and GBPUSD.",
                "Fetch commands use trades schema first; depth schemas require a separate cost and value gate.",
                "Event inclusion is limited to fields already present in candidate_features_log.jsonl.",
                "Rows at or after available_end_utc are excluded when an availability cap is supplied; windows crossing the cap are truncated.",
            ],
            "open_questions": [
                "Do trades-level features around these windows separate candidates from structural no-trade context?",
                "Which event classes justify mbp-1/mbp-10 depth after trades features are measured?",
                "Do inferred M15 candle timestamps match future shadow-only canonical candle-close logging?",
            ],
            "next_steps": [
                "Fetch trades schema for the merged candidate/context groups under explicit cost caps.",
                "Extract CVD, delta acceleration, POC/HVN/LVN, volume imbalance, and absorption proxies per event.",
                "Join features back to synthetic/actual outcomes before any strategy hypothesis is registered.",
            ],
        },
    }
