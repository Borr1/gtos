"""Recompute entry-redesign buckets with spread-aware local tick replay.

This builder is read-only. It consumes current shadow candidate/path rows plus
local tick parquet, then materializes fixed offset challenger outcomes for the
current entry-redesign buckets without appending to shadow logs or changing live
behavior.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    entry_retest_redesign_context,
    path_outcome_status,
    read_jsonl,
)


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
SHIFT_LEVELS = (0.25, 0.50, 1.00)
ENTRY_REDESIGN_BUCKETS = {
    "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE",
    "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE",
}
INPUTS = {
    "strategy_follow_candidates": Path("shadow_logs/strategy_follow_candidates.jsonl"),
    "candidate_path_follow": Path("shadow_logs/candidate_path_follow.jsonl"),
    "candidate_ltf_path_order": Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    "missed_opportunity_shadow": Path("shadow_logs/missed_opportunity_shadow.jsonl"),
}
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: float | None, digits: int = 8) -> float | None:
    return None if value is None else round(float(value), digits)


def iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or parse_utc(row.get("backfilled_at_utc"))
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc")) or parse_utc(
            out.get(cid, {}).get("backfilled_at_utc")
        )
        current_created = current_created or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = previous_created or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[cid] = row
    return out


class TickCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.frames: dict[Path, Any] = {}
        self.artifacts: dict[str, dict[str, Any]] = {}

    def _load_file(self, path: Path) -> pd.DataFrame | None:
        key = str(path)
        if path not in self.frames:
            item: dict[str, Any] = {
                "path": key,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
            if not path.exists():
                item["status"] = "MISSING"
                self.frames[path] = None
            else:
                try:
                    frame = pd.read_parquet(path)
                except Exception as exc:  # noqa: BLE001 - artifact records exact parser error
                    item["status"] = "PARQUET_READ_ERROR"
                    item["error_type"] = type(exc).__name__
                    item["error"] = str(exc)
                    self.frames[path] = None
                else:
                    item["status"] = "READABLE_PARQUET"
                    item["row_count"] = int(len(frame))
                    self.frames[path] = frame
            self.artifacts[key] = item
        frame = self.frames[path]
        return frame if isinstance(frame, pd.DataFrame) else None

    def window(self, symbol: str, start: datetime, end: datetime) -> tuple[pd.DataFrame | None, dict[str, Any]]:
        symbol_dir = self.root / symbol
        day = start.date()
        end_day = end.date()
        paths: list[Path] = []
        while day <= end_day:
            path = symbol_dir / f"{day.isoformat()}.parquet"
            if path.exists():
                paths.append(path)
            day += timedelta(days=1)

        frames: list[pd.DataFrame] = []
        read_errors: list[str] = []
        for path in paths:
            frame = self._load_file(path)
            if frame is None:
                read_errors.append(str(path))
            else:
                frames.append(frame)

        meta = {
            "symbol_tick_dir": str(symbol_dir),
            "source_files": [str(path) for path in paths],
            "read_error_files": read_errors,
            "source_file_count": len(paths),
        }
        if read_errors:
            meta["tick_source_status"] = "TICK_SOURCE_INCOMPLETE_BAD_PARQUET"
            return None, meta
        if not frames:
            meta["tick_source_status"] = "TICK_SOURCE_MISSING"
            return None, meta
        frame = pd.concat(frames, ignore_index=True).sort_values("ts_utc") if len(frames) > 1 else frames[0]
        window = frame[(frame.ts_utc >= pd.Timestamp(start)) & (frame.ts_utc <= pd.Timestamp(end))]
        if window.empty:
            meta["tick_source_status"] = "TICK_SOURCE_WINDOW_EMPTY"
            return None, meta
        meta["tick_source_status"] = "TICK_REPLAY_SOURCE_COMPLETE"
        meta["tick_count"] = int(len(window))
        return window, meta


def trade_geometry(candidate: dict[str, Any], path: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters") or path.get("trade_parameters") or {}
    side = str(candidate.get("side") or path.get("side") or params.get("direction") or "").upper()
    entry = safe_float(params.get("entry_price"))
    stop = safe_float(params.get("stop_loss"))
    target = safe_float(params.get("take_profit_1"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    return {
        "side": side,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": target,
        "base_r_price": risk if risk and risk > 0 else None,
    }


def min_required_shift_r(window: pd.DataFrame, geometry: dict[str, Any]) -> dict[str, Any]:
    entry = geometry["entry_price"]
    risk = geometry["base_r_price"]
    side = geometry["side"]
    if entry is None or risk is None:
        return {"minimum_spread_aware_shift_r": None, "minimum_fill_price": None, "minimum_fill_tick_utc": None}
    if side == "LONG":
        idx = window.ask.idxmin()
        row = window.loc[idx]
        shift = max(0.0, (float(row.ask) - entry) / risk)
        return {
            "minimum_spread_aware_shift_r": round_or_none(shift),
            "minimum_fill_price": round_or_none(float(row.ask)),
            "minimum_fill_tick_utc": iso_or_none(row.ts_utc),
            "minimum_fill_bid": round_or_none(float(row.bid)),
            "minimum_fill_ask": round_or_none(float(row.ask)),
        }
    if side == "SHORT":
        idx = window.bid.idxmax()
        row = window.loc[idx]
        shift = max(0.0, (entry - float(row.bid)) / risk)
        return {
            "minimum_spread_aware_shift_r": round_or_none(shift),
            "minimum_fill_price": round_or_none(float(row.bid)),
            "minimum_fill_tick_utc": iso_or_none(row.ts_utc),
            "minimum_fill_bid": round_or_none(float(row.bid)),
            "minimum_fill_ask": round_or_none(float(row.ask)),
        }
    return {"minimum_spread_aware_shift_r": None, "minimum_fill_price": None, "minimum_fill_tick_utc": None}


def score_shift(window: pd.DataFrame | None, geometry: dict[str, Any], shift_r: float) -> dict[str, Any]:
    entry = geometry["entry_price"]
    stop = geometry["stop_loss"]
    target = geometry["take_profit_1"]
    base_r = geometry["base_r_price"]
    side = geometry["side"]
    if window is None:
        return {"shift_r": shift_r, "outcome_status": "TICK_SOURCE_MISSING_OR_BAD", "proxy_r": None}
    if entry is None or stop is None or target is None or base_r is None:
        return {"shift_r": shift_r, "outcome_status": "TRADE_GEOMETRY_MISSING", "proxy_r": None}

    shifted_entry = entry + shift_r * base_r if side == "LONG" else entry - shift_r * base_r
    if side == "LONG" and shifted_entry >= target:
        return {
            "shift_r": shift_r,
            "shifted_entry_price": round_or_none(shifted_entry),
            "outcome_status": "INVALID_SHIFT_CROSSES_TARGET",
            "proxy_r": None,
        }
    if side == "SHORT" and shifted_entry <= target:
        return {
            "shift_r": shift_r,
            "shifted_entry_price": round_or_none(shifted_entry),
            "outcome_status": "INVALID_SHIFT_CROSSES_TARGET",
            "proxy_r": None,
        }

    if side == "LONG":
        fill_rows = window[window.ask <= shifted_entry].head(1)
    elif side == "SHORT":
        fill_rows = window[window.bid >= shifted_entry].head(1)
    else:
        return {"shift_r": shift_r, "outcome_status": "SIDE_UNKNOWN", "proxy_r": None}

    target_r = (target - shifted_entry) / (shifted_entry - stop) if side == "LONG" else (shifted_entry - target) / (stop - shifted_entry)
    out = {
        "shift_r": shift_r,
        "shifted_entry_price": round_or_none(shifted_entry),
        "shifted_risk_price": round_or_none(abs(shifted_entry - stop)),
        "shifted_target_r": round_or_none(target_r),
    }
    if fill_rows.empty:
        return {
            **out,
            "outcome_status": "NO_FILL_AT_SHIFT",
            "fill_first_touch_utc": None,
            "terminal_event_utc": None,
            "proxy_r": 0.0,
            "proxy_r_delta_vs_original_no_fill": 0.0,
        }

    fill_time = fill_rows.ts_utc.iloc[0]
    after_fill = window[window.ts_utc >= fill_time]
    if side == "LONG":
        target_rows = after_fill[after_fill.bid >= target].head(1)
        stop_rows = after_fill[after_fill.bid <= stop].head(1)
    else:
        target_rows = after_fill[after_fill.ask <= target].head(1)
        stop_rows = after_fill[after_fill.ask >= stop].head(1)

    target_time = None if target_rows.empty else target_rows.ts_utc.iloc[0]
    stop_time = None if stop_rows.empty else stop_rows.ts_utc.iloc[0]
    if target_time is not None and (stop_time is None or target_time <= stop_time):
        proxy_r = round_or_none(target_r)
        return {
            **out,
            "outcome_status": "TP1_AFTER_SHIFT_FILL",
            "fill_first_touch_utc": iso_or_none(fill_time),
            "terminal_event_utc": iso_or_none(target_time),
            "proxy_r": proxy_r,
            "proxy_r_delta_vs_original_no_fill": proxy_r,
        }
    if stop_time is not None:
        return {
            **out,
            "outcome_status": "SL_AFTER_SHIFT_FILL",
            "fill_first_touch_utc": iso_or_none(fill_time),
            "terminal_event_utc": iso_or_none(stop_time),
            "proxy_r": -1.0,
            "proxy_r_delta_vs_original_no_fill": -1.0,
        }
    return {
        **out,
        "outcome_status": "FILLED_UNRESOLVED_BY_ASOF",
        "fill_first_touch_utc": iso_or_none(fill_time),
        "terminal_event_utc": None,
        "proxy_r": None,
        "proxy_r_delta_vs_original_no_fill": None,
    }


def branch_decision(bucket: str, tick_status: str, shift_outcomes: dict[str, dict[str, Any]]) -> str:
    if bucket == "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW":
        return "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_ENTRY_REDESIGN_DENOMINATOR"
    if tick_status != "TICK_REPLAY_SOURCE_COMPLETE":
        return "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER"
    shift_025 = shift_outcomes.get("0.25", {})
    shift_050 = shift_outcomes.get("0.5", {})
    if bucket == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE":
        if shift_025.get("outcome_status") == "TP1_AFTER_SHIFT_FILL":
            return "IMPLEMENT_025R_ENTRY_OFFSET_SCORER_DEFAULT_OFF"
        if shift_050.get("outcome_status") == "TP1_AFTER_SHIFT_FILL":
            return "KILL_025R_OFFSET_AS_FILL_PROXY_REDESIGN_TO_SPREAD_AWARE_050R_CHALLENGER"
        return "REDESIGN_NEAR_MISS_ENTRY_OFFSET_REQUIRES_SPREAD_AWARE_THRESHOLD"
    if bucket == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE":
        if shift_025.get("outcome_status") == "TP1_AFTER_SHIFT_FILL":
            return "IMPLEMENT_FAR_MISS_025R_OFFSET_SCORER_DEFAULT_OFF"
        if shift_050.get("outcome_status") == "TP1_AFTER_SHIFT_FILL":
            return "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL"
        return "KILL_025R_FAR_MISS_OFFSET_REDESIGN_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    return "ENTRY_REDESIGN_DISTANCE_REPAIR_REQUIRED"


def build_rows() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    candidates = latest_by_candidate(read_jsonl(INPUTS["strategy_follow_candidates"]))
    paths = latest_by_candidate(read_jsonl(INPUTS["candidate_path_follow"]))
    ltf_rows = latest_by_candidate(read_jsonl(INPUTS["candidate_ltf_path_order"]))
    missed_rows = latest_by_candidate(read_jsonl(INPUTS["missed_opportunity_shadow"]))
    tick_cache = TickCache(Path("data/ticks"))
    generated = utc_now()
    rows: list[dict[str, Any]] = []

    for cid in sorted(set(candidates) & set(paths)):
        candidate = candidates[cid]
        path = paths[cid]
        ltf = ltf_rows.get(cid, {})
        missed = missed_rows.get(cid, {})
        redesign = entry_retest_redesign_context(candidate, path)
        bucket = redesign["entry_retest_redesign_bucket"]
        geometry = trade_geometry(candidate, path)
        start = parse_utc(candidate.get("decision_time_utc") or path.get("decision_time_utc"))
        end = parse_utc(path.get("asof_latest_candle_utc"))
        tick_window = None
        tick_meta = {"tick_source_status": "NOT_REQUIRED_FOR_NON_REDESIGN_ROW"}
        minimum_shift = {
            "minimum_spread_aware_shift_r": None,
            "minimum_fill_price": None,
            "minimum_fill_tick_utc": None,
        }
        if bucket in ENTRY_REDESIGN_BUCKETS and start is not None and end is not None:
            tick_window, tick_meta = tick_cache.window(str(candidate.get("symbol") or path.get("symbol")), start, end)
            if tick_meta.get("tick_source_status") == "TICK_REPLAY_SOURCE_COMPLETE" and tick_window is not None:
                minimum_shift = min_required_shift_r(tick_window, geometry)
        elif bucket in ENTRY_REDESIGN_BUCKETS:
            tick_meta = {"tick_source_status": "TICK_SOURCE_WINDOW_TIME_MISSING"}

        shift_outcomes = {
            f"{shift:g}": score_shift(tick_window, geometry, shift) for shift in SHIFT_LEVELS
        } if bucket in ENTRY_REDESIGN_BUCKETS else {}
        decision = branch_decision(str(bucket), str(tick_meta.get("tick_source_status")), shift_outcomes)
        nearest_r = safe_float(redesign.get("nearest_distance_to_entry_r"))
        min_shift = safe_float(minimum_shift.get("minimum_spread_aware_shift_r"))

        rows.append(
            {
                "row_id": f"MAIN-ORCH24-ENTRY-REDESIGN-TICK-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "candidate_id": cid,
                "symbol": candidate.get("symbol") or path.get("symbol"),
                "broker_symbol": candidate.get("broker_symbol") or path.get("broker_symbol"),
                "side": geometry["side"],
                "framework": candidate.get("framework") or path.get("framework"),
                "decision_time_utc": candidate.get("decision_time_utc") or path.get("decision_time_utc"),
                "asof_latest_candle_utc": path.get("asof_latest_candle_utc"),
                "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log")
                or path.get("final_outcome_at_candidate_log"),
                "path_outcome_status": path_outcome_status(path),
                "path_label": path.get("path_label"),
                "ltf_terminal_outcome_status": ltf.get("terminal_outcome_status"),
                "ltf_path_order_label": ltf.get("path_order_label"),
                "missed_opportunity_shadow_status": missed.get("near_miss_classification"),
                "opportunity_counting_hint": missed.get("manual_backfill_status"),
                "entry_retest_redesign_bucket": bucket,
                "entry_retest_redesign_bucket_basis": redesign.get("entry_retest_redesign_bucket_basis"),
                "entry_retest_redesign_fill_claim_status": redesign.get("entry_retest_redesign_fill_claim_status"),
                "entry_retest_redesign_tick_replay_requirement": redesign.get(
                    "entry_retest_redesign_tick_replay_requirement"
                ),
                "entry_touch_distance_status": redesign.get("entry_touch_distance_status"),
                "m15_nearest_distance_to_entry_r": round_or_none(nearest_r),
                "m15_nearest_distance_to_entry_price": round_or_none(safe_float(path.get("nearest_distance_to_entry"))),
                "minimum_spread_aware_shift_r": round_or_none(min_shift),
                "spread_aware_shift_delta_vs_m15_range_r": round_or_none(min_shift - nearest_r)
                if min_shift is not None and nearest_r is not None
                else None,
                "minimum_spread_aware_fill_price": minimum_shift.get("minimum_fill_price"),
                "minimum_spread_aware_fill_tick_utc": minimum_shift.get("minimum_fill_tick_utc"),
                "trade_geometry": geometry,
                "tick_source_status": tick_meta.get("tick_source_status"),
                "tick_source_files": tick_meta.get("source_files", []),
                "tick_source_read_error_files": tick_meta.get("read_error_files", []),
                "tick_count": tick_meta.get("tick_count"),
                "offset_shift_outcomes": shift_outcomes,
                "implementation_decision": decision,
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )
    return rows, tick_cache.artifacts


def numeric_values(rows: list[dict[str, Any]], shift_key: str) -> list[float]:
    out: list[float] = []
    for row in rows:
        value = ((row.get("offset_shift_outcomes") or {}).get(shift_key) or {}).get("proxy_r")
        parsed = safe_float(value)
        if parsed is not None:
            out.append(parsed)
    return out


def summarize(rows: list[dict[str, Any]], tick_artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_bucket[str(row.get("entry_retest_redesign_bucket") or "")].append(row)

    shift_summary: dict[str, Any] = {}
    for bucket, bucket_rows in sorted(by_bucket.items()):
        if bucket not in ENTRY_REDESIGN_BUCKETS:
            continue
        shift_summary[bucket] = {}
        for shift in SHIFT_LEVELS:
            key = f"{shift:g}"
            values = numeric_values(bucket_rows, key)
            statuses = Counter(
                str(((row.get("offset_shift_outcomes") or {}).get(key) or {}).get("outcome_status"))
                for row in bucket_rows
            )
            shift_summary[bucket][key] = {
                "rows": len(bucket_rows),
                "numeric_proxy_rows": len(values),
                "proxy_r_sum": round_or_none(sum(values)),
                "proxy_r_mean": round_or_none(sum(values) / len(values)) if values else None,
                "proxy_r_delta_vs_original_no_fill_sum": round_or_none(sum(values)),
                "outcome_status_counts": dict(statuses),
            }

    affected = [row for row in rows if row.get("entry_retest_redesign_bucket") in ENTRY_REDESIGN_BUCKETS]
    source_counts = Counter(str(row.get("tick_source_status")) for row in affected)
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE",
        "claim_boundary": (
            "Spread-aware local tick replay for current entry-redesign buckets only. Exact broker/account R is "
            "not opened; proxy R is mechanical tick-path target/stop ordering for fixed shifted-entry challengers."
        ),
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "affected_entry_redesign_rows": len(affected),
        "exact_r_rows": 0,
        "entry_retest_redesign_bucket_counts": dict(
            Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)
        ),
        "tick_source_status_counts_for_affected_rows": dict(source_counts),
        "implementation_decision_counts": dict(Counter(str(row.get("implementation_decision")) for row in rows)),
        "shift_summary_by_bucket": shift_summary,
        "tick_artifact_status_counts": dict(
            Counter(str(item.get("status")) for item in tick_artifacts.values())
        ),
        "tick_artifact_count": len(tick_artifacts),
        "safe_flags": SAFE_FLAGS,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def build_manifest(tick_artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in INPUTS.values()
            if path.exists()
        },
        "tick_artifacts": tick_artifacts,
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows, tick_artifacts = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows, tick_artifacts))
    write_json(OUTPUT_MANIFEST, build_manifest(tick_artifacts))
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
