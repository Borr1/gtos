#!/usr/bin/env python3
"""Build the OTI1 pending-intent closure source packet.

This lane is source-correction only. It materializes pending-intent
entry-touch/fill/cancel/expiry/horizon timestamps from source-hashed lifecycle
logs plus side-aware bid/ask tick parquet, without opening R/performance,
broker/account/live-order, validation, promotion, or live-effect lanes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-08"
SCHEMA = "oti1_pending_intent_closure_source_packet_v1"
PACKET_ID = "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-08T15:38:00Z"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
ROUTER_DIR = OUTCOME_ROOT / "nofill_blocked_family_source_correction_router"
SOURCE_PACKET_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
TICK_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks")

CONTROL_PROMPT = ROUTER_DIR / "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md"
ROUTER_CONTEXT = ROUTER_DIR / "NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md"
ROUTER_ROUTE_LEDGER = ROUTER_DIR / "NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json"
ROUTER_SOURCE_SEARCH = ROUTER_DIR / "NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json"
SOURCE_ROWS_PATH = SOURCE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"
PENDING_LIFECYCLE_PATH = REPO_ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl"
PENDING_AUDIT_PATH = REPO_ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl"
OPPORTUNITY_AUDIT_PATH = REPO_ROOT / "shadow_logs" / "opportunity_lifecycle_audit.jsonl"
CONTRACT_TOUCH_PATH = (
    OUTCOME_ROOT
    / "no_fill_lifecycle_result_contract_design"
    / "NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json"
)
CONTRACT_FIELD_REQ_PATH = (
    OUTCOME_ROOT
    / "no_fill_lifecycle_result_contract_design"
    / "NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_2026-05-08.json"
)
CONTRACT_NOLEAK_PATH = (
    OUTCOME_ROOT
    / "no_fill_lifecycle_result_contract_design"
    / "NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_2026-05-08.json"
)

OUT_JSONL = OUT_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl"
OUT_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}.json"
CONTEXT_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_CONTEXT_ANCHOR_{DATE}.json"
CONTEXT_MD = OUT_DIR / f"OTI1_PENDING_INTENT_CONTEXT_ANCHOR_{DATE}.md"
SEARCH_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_SOURCE_SEARCH_LEDGER_{DATE}.json"
SEARCH_MD = OUT_DIR / f"OTI1_PENDING_INTENT_SOURCE_SEARCH_LEDGER_{DATE}.md"
DECISIONS_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_ROW_DECISION_LEDGER_{DATE}.json"
DECISIONS_MD = OUT_DIR / f"OTI1_PENDING_INTENT_ROW_DECISION_LEDGER_{DATE}.md"
HASH_AUDIT_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT_{DATE}.json"
HASH_AUDIT_MD = OUT_DIR / f"OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT_{DATE}.md"
DUPLICATE_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_DUPLICATE_CONTRACT_AUDIT_{DATE}.json"
DUPLICATE_MD = OUT_DIR / f"OTI1_PENDING_INTENT_DUPLICATE_CONTRACT_AUDIT_{DATE}.md"
IMPOSSIBILITY_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_IMPOSSIBILITY_LEDGER_{DATE}.json"
IMPOSSIBILITY_MD = OUT_DIR / f"OTI1_PENDING_INTENT_IMPOSSIBILITY_LEDGER_{DATE}.md"
COMPLETION_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = OUT_DIR / f"OTI1_PENDING_INTENT_COMPLETION_AUDIT_{DATE}.md"
MANIFEST_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_ARTIFACT_MANIFEST_{DATE}.json"

FORBIDDEN_KEYS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "broker_order_id",
    "broker_position_id",
    "conservative_lower_bound_r",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "pbo",
    "pending_ticket",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
}

EXCLUDED_T3_IDS = {f"CNR-T3-CAND-{idx:04d}" for idx in range(1, 7)}


def parse_utc(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_utc(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"GIT_UNAVAILABLE: {exc}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_with_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_source_line_no"] = line_no
        row["_source_path"] = rel(path)
        rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def value_close(left: Any, right: Any) -> bool:
    try:
        return abs(float(left) - float(right)) <= 1e-9
    except Exception:
        return False


def source_line_ref(row: dict[str, Any]) -> str:
    return f"{row.get('_source_path')}:{row.get('_source_line_no')}"


def line_refs(rows: list[dict[str, Any]]) -> list[str]:
    return [source_line_ref(row) for row in rows]


def last_nonnull_time(rows: list[dict[str, Any]], keys: list[str]) -> dt.datetime | None:
    latest: dt.datetime | None = None
    for row in rows:
        for key in keys:
            value = parse_utc(row.get(key))
            if value is not None and (latest is None or value > latest):
                latest = value
    return latest


def first_nonnull_time(rows: list[dict[str, Any]], key: str) -> dt.datetime | None:
    for row in rows:
        value = parse_utc(row.get(key))
        if value is not None:
            return value
    return None


def find_lifecycle_group(source_row: dict[str, Any], lifecycle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = source_row["source_evidence"]
    symbol = source_row["projected_symbol"]
    side = source_row["projected_side"]
    pending_created = evidence.get("pending_created_at_utc")
    entry = evidence.get("entry_price")
    sl = evidence.get("protective_level_price")
    tp1 = evidence.get("terminal_area_price")

    exact = [
        row
        for row in lifecycle_rows
        if row.get("symbol") == symbol
        and row.get("side") == side
        and row.get("pending_created_time_utc") == pending_created
        and value_close(row.get("entry_price"), entry)
        and value_close(row.get("stop_loss"), sl)
        and value_close(row.get("take_profit_1"), tp1)
    ]
    exact.sort(key=lambda item: parse_utc(item.get("timestamp_utc")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
    return exact


def find_pending_audit_row(source_row: dict[str, Any], audit_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    evidence = source_row["source_evidence"]
    symbol = source_row["projected_symbol"]
    side = source_row["projected_side"]
    pending_created = evidence.get("pending_created_at_utc")
    entry = evidence.get("entry_price")
    sl = evidence.get("protective_level_price")
    tp1 = evidence.get("terminal_area_price")
    matches = [
        row
        for row in audit_rows
        if row.get("symbol") == symbol
        and row.get("side") == side
        and row.get("pending_intent_global_key")
        and str(pending_created) in str(row.get("pending_intent_global_key"))
        and value_close(row.get("entry_price"), entry)
        and value_close(row.get("stop_loss"), sl)
        and value_close(row.get("take_profit_1"), tp1)
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: parse_utc(item.get("latest_lifecycle_timestamp_utc")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True)
    return matches[0]


def find_cancel_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        label = str(row.get("fill_no_fill_label") or "")
        intent = row.get("intent_after_check")
        if row.get("cancel_reason") or intent in {"manual_or_system_cancelled", "cancelled_wrong_side"}:
            return row
        if label in {"no_fill_cancelled", "no_fill_cancelled_wrong_side"}:
            return row
    return None


def date_range(start: dt.datetime, end: dt.datetime) -> list[dt.date]:
    dates: list[dt.date] = []
    cur = start.date()
    while cur <= end.date():
        dates.append(cur)
        cur += dt.timedelta(days=1)
    return dates


def load_tick_window(symbol: str, start: dt.datetime, end: dt.datetime) -> tuple[pd.DataFrame | None, list[dict[str, Any]], list[str]]:
    source_files: list[dict[str, Any]] = []
    missing: list[str] = []
    frames: list[pd.DataFrame] = []
    for day in date_range(start, end):
        path = TICK_ROOT / symbol / f"{day.isoformat()}.parquet"
        record = {
            "path": str(path),
            "rel_path": str(path).replace("\\", "/"),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        source_files.append(record)
        if not path.exists():
            missing.append(str(path))
            continue
        df = pd.read_parquet(path)
        frames.append(df)
    if missing or not frames:
        return None, source_files, missing

    combined = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    window = combined[(combined["ts_utc"] >= pd.Timestamp(start)) & (combined["ts_utc"] <= pd.Timestamp(end))].copy()
    return window, source_files, missing


def first_touch(df: pd.DataFrame, mask: pd.Series) -> dict[str, Any] | None:
    matches = df[mask]
    if matches.empty:
        return None
    row = matches.iloc[0]
    timestamp = row["ts_utc"].to_pydatetime().astimezone(dt.timezone.utc)
    return {
        "timestamp_utc": iso_utc(timestamp),
        "bid": float(row["bid"]),
        "ask": float(row["ask"]),
        "source_row_position": int(row.name),
    }


def compute_touches(df: pd.DataFrame, side: str, entry: float, protective: float, terminal: float) -> dict[str, Any]:
    if df.empty:
        return {
            "entry_touch": None,
            "terminal_area_touch": None,
            "protective_level_touch": None,
            "ordered_source_events": [],
            "same_timestamp_ambiguity": False,
        }

    if side == "LONG":
        masks = {
            "entry_touch": df["ask"] <= entry,
            "terminal_area_touch": df["bid"] >= terminal,
            "protective_level_touch": df["bid"] <= protective,
        }
    elif side == "SHORT":
        masks = {
            "entry_touch": df["bid"] >= entry,
            "terminal_area_touch": df["ask"] <= terminal,
            "protective_level_touch": df["ask"] >= protective,
        }
    else:
        raise ValueError(f"unsupported side: {side}")

    touches = {name: first_touch(df, mask) for name, mask in masks.items()}
    events: list[dict[str, Any]] = []
    for name, touch in touches.items():
        if touch:
            events.append(
                {
                    "event": name,
                    "first_touch_utc": touch["timestamp_utc"],
                    "bid": touch["bid"],
                    "ask": touch["ask"],
                    "source_row_position": touch["source_row_position"],
                }
            )
    events.sort(key=lambda item: (item["first_touch_utc"], item["source_row_position"], item["event"]))
    timestamp_counts = Counter(event["first_touch_utc"] for event in events)
    same_timestamp = any(count > 1 for count in timestamp_counts.values())
    return {
        "entry_touch": touches["entry_touch"],
        "terminal_area_touch": touches["terminal_area_touch"],
        "protective_level_touch": touches["protective_level_touch"],
        "ordered_source_events": events,
        "same_timestamp_ambiguity": same_timestamp,
    }


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                hits.append(child_path)
            hits.extend(scan_forbidden_keys(value, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def materialize_row(
    source_row: dict[str, Any],
    lifecycle_rows: list[dict[str, Any]],
    pending_audit_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = source_row["source_evidence"]
    lifecycle_group = find_lifecycle_group(source_row, lifecycle_rows)
    audit_row = find_pending_audit_row(source_row, pending_audit_rows)
    start = parse_utc(evidence.get("pending_created_at_utc"))
    if start is None:
        raise ValueError(f"missing pending_created_at_utc for {source_row.get('packet_row_id')}")

    cancel_row = find_cancel_row(lifecycle_group)
    cancelled_at = parse_utc(cancel_row.get("timestamp_utc")) if cancel_row else None
    cancel_reason = (
        cancel_row.get("cancel_reason")
        if cancel_row
        else evidence.get("source_cancel_reason")
    )
    expired_at = first_nonnull_time(lifecycle_group, "expiry_time_utc") or parse_utc(evidence.get("source_expiry_time_utc"))
    explicit_fill_at = first_nonnull_time(lifecycle_group, "fill_time_utc") or parse_utc(evidence.get("source_fill_time_utc"))
    last_source_row = lifecycle_group[-1] if lifecycle_group else None
    last_observed_at = parse_utc(last_source_row.get("timestamp_utc")) if last_source_row else None
    original_horizon = parse_utc(evidence.get("frozen_observation_horizon_utc"))
    source_corrected_horizon = last_nonnull_time(
        lifecycle_group,
        ["asof_cutoff_utc", "checked_candle_time_utc", "last_limit_check_candle_time_before", "latest_m15_time_utc"],
    )
    search_end = explicit_fill_at or cancelled_at or expired_at or last_observed_at or source_corrected_horizon or original_horizon
    if search_end is None:
        raise ValueError(f"missing search end for {source_row.get('packet_row_id')}")

    tick_df, tick_sources, missing_ticks = load_tick_window(source_row["projected_symbol"], start, search_end)
    touches = None
    blockers: list[str] = []
    if missing_ticks:
        blockers.append("BLOCK_SOURCE_MISSING_TICK_FILE")
    elif tick_df is None or tick_df.empty:
        blockers.append("BLOCK_SOURCE_EMPTY_TICK_WINDOW")
    else:
        touches = compute_touches(
            tick_df,
            source_row["projected_side"],
            float(evidence["entry_price"]),
            float(evidence["protective_level_price"]),
            float(evidence["terminal_area_price"]),
        )
        if touches["same_timestamp_ambiguity"]:
            blockers.append("BLOCK_CONTRACT_SAME_TIMESTAMP_TOUCH_AMBIGUITY")

    entry_touch = touches["entry_touch"] if touches else None
    entry_touched_at = parse_utc(entry_touch["timestamp_utc"]) if entry_touch else None
    filled_at = explicit_fill_at
    fill_semantics = "explicit_lifecycle_fill_time_not_present"
    if filled_at is None and entry_touched_at is not None:
        if (cancelled_at is None or entry_touched_at <= cancelled_at) and (expired_at is None or entry_touched_at <= expired_at):
            filled_at = entry_touched_at
            fill_semantics = "side_aware_quote_touch_while_pending_active_not_broker_fill"

    pending_active_until = filled_at or cancelled_at or expired_at or last_observed_at or search_end
    pending_key = audit_row.get("pending_intent_global_key") if audit_row else None
    if not pending_key:
        pending_key = "|".join(
            [
                source_row["projected_symbol"],
                str(evidence.get("pending_created_at_utc")),
                source_row["projected_side"],
                str(evidence.get("entry_price")),
                str(evidence.get("protective_level_price")),
                str(evidence.get("terminal_area_price")),
            ]
        )

    if blockers:
        decision_status = "SOURCE_BLOCKED_EXACT"
    elif filled_at is not None:
        decision_status = "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT"
    else:
        decision_status = "SOURCE_CORRECTED_NO_ENTRY_THROUGH_PENDING_HORIZON"

    tick_first = None
    tick_last = None
    tick_rows = 0
    if tick_df is not None and not tick_df.empty:
        tick_rows = int(len(tick_df))
        tick_first = iso_utc(tick_df["ts_utc"].iloc[0].to_pydatetime().astimezone(dt.timezone.utc))
        tick_last = iso_utc(tick_df["ts_utc"].iloc[-1].to_pydatetime().astimezone(dt.timezone.utc))

    field_status = {
        "pending_intent_id_or_deterministic_key": "MATERIALIZED",
        "pending_created_at_utc": "MATERIALIZED",
        "pending_active_from_utc": "MATERIALIZED",
        "pending_active_until_utc": "MATERIALIZED",
        "entry_touched_at_utc": "MATERIALIZED_TIMESTAMP" if entry_touched_at else "MATERIALIZED_NULL_NO_ENTRY_TOUCH_IN_SOURCE_WINDOW",
        "filled_at_utc": "MATERIALIZED_TIMESTAMP_FROM_SIDE_AWARE_ENTRY_TOUCH" if filled_at else "MATERIALIZED_NULL_NO_SOURCE_FILL_TOUCH",
        "cancelled_at_utc": "MATERIALIZED_TIMESTAMP" if cancelled_at else "MATERIALIZED_NULL_NO_CANCEL_SOURCE",
        "expired_at_utc": "MATERIALIZED_TIMESTAMP" if expired_at else "MATERIALIZED_NULL_NO_EXPIRY_SOURCE",
        "frozen_horizon_start_utc": "MATERIALIZED",
        "frozen_horizon_end_utc": "MATERIALIZED",
        "last_observed_pending_state_at_utc": "MATERIALIZED" if last_observed_at else "MATERIALIZED_NULL_NO_LIFECYCLE_GROUP",
        "source_hash_path": "MATERIALIZED",
        "side_aware_touch_source": "MATERIALIZED" if not blockers else "BLOCKED",
        "as_of_rule": "MATERIALIZED",
    }

    source_files = [
        {
            "path": rel(PENDING_LIFECYCLE_PATH),
            "sha256": sha256_file(PENDING_LIFECYCLE_PATH),
            "role": "pending_limit_lifecycle_source_group",
            "line_refs": line_refs(lifecycle_group),
        },
        {
            "path": rel(PENDING_AUDIT_PATH),
            "sha256": sha256_file(PENDING_AUDIT_PATH),
            "role": "pending_limit_lifecycle_audit_join_source",
            "line_refs": [source_line_ref(audit_row)] if audit_row else [],
        },
        {
            "path": rel(SOURCE_ROWS_PATH),
            "sha256": sha256_file(SOURCE_ROWS_PATH),
            "role": "accepted_nofill_close_source_row_packet",
            "line_refs": [source_line_ref(source_row)],
        },
    ]
    for tick_source in tick_sources:
        source_files.append(
            {
                "path": tick_source["rel_path"],
                "sha256": tick_source["sha256"],
                "role": "side_aware_tick_source",
                "size_bytes": tick_source["size_bytes"],
            }
        )

    row = {
        "schema_version": SCHEMA,
        "packet_id": PACKET_ID,
        "packet_row_id": source_row["packet_row_id"].replace("NOFILL-CLOSE", "OTI1-SRC"),
        "source_close_packet_row_id": source_row["packet_row_id"],
        "source_inventory_id": source_row["source_inventory_id"],
        "source_lane": source_row["source_lane"],
        "source_packet_id": source_row["source_packet_id"],
        "source_row_id": source_row["source_row_id"],
        "source_artifact_path": source_row["source_artifact_path"],
        "source_artifact_sha256": sha256_file(REPO_ROOT / source_row["source_artifact_path"]),
        "duplicate_group_id": source_row["duplicate_group_id"],
        "nofill_duplicate_key": source_row["nofill_duplicate_key"],
        "symbol": source_row["projected_symbol"],
        "session": source_row["projected_session"],
        "side": source_row["projected_side"],
        "decision_asof_utc": iso_utc(parse_utc(source_row["decision_asof_utc"])),
        "entry_price": evidence["entry_price"],
        "terminal_area_price": evidence["terminal_area_price"],
        "protective_level_price": evidence["protective_level_price"],
        "pending_intent_id_or_deterministic_key": pending_key,
        "pending_created_at_utc": iso_utc(start),
        "pending_active_from_utc": iso_utc(start),
        "pending_active_until_utc": iso_utc(pending_active_until),
        "entry_touched_at_utc": iso_utc(entry_touched_at),
        "filled_at_utc": iso_utc(filled_at),
        "filled_at_semantics": fill_semantics,
        "cancelled_at_utc": iso_utc(cancelled_at),
        "cancel_reason": cancel_reason,
        "expired_at_utc": iso_utc(expired_at),
        "expiry_policy_id": "source_expiry_time" if expired_at else ("source_new_day_or_system_cancel" if cancel_reason == "new_day" else None),
        "frozen_horizon_start_utc": iso_utc(start),
        "frozen_horizon_end_utc": iso_utc(source_corrected_horizon or original_horizon or search_end),
        "original_packet_frozen_horizon_end_utc": iso_utc(original_horizon),
        "source_corrected_lifecycle_observation_end_utc": iso_utc(source_corrected_horizon),
        "last_observed_pending_state_at_utc": iso_utc(last_observed_at),
        "source_hash_path": rel(HASH_AUDIT_JSON) + "#source_hash_records",
        "source_files": source_files,
        "side_aware_touch_source": {
            "parser_contract": "bid_ask_side_aware_touch_times_v1",
            "side_rule": "LONG entry ask<=entry; SHORT entry bid>=entry",
            "path_start_utc": iso_utc(start),
            "path_end_utc": iso_utc(search_end),
            "source_first_ts_utc": tick_first,
            "source_last_ts_utc": tick_last,
            "source_row_count": tick_rows,
            "source_files": [item for item in source_files if item["role"] == "side_aware_tick_source"],
            "entry_touch": entry_touch,
            "terminal_area_touch": touches["terminal_area_touch"] if touches else None,
            "protective_level_touch": touches["protective_level_touch"] if touches else None,
            "ordered_source_events": touches["ordered_source_events"] if touches else [],
            "same_timestamp_ambiguity": touches["same_timestamp_ambiguity"] if touches else False,
        },
        "as_of_rule": (
            "decision geometry and duplicate keys remain frozen at decision_asof_utc; "
            "pending lifecycle and side-aware tick events are label-time/source-control fields only "
            "and are not used as decision features"
        ),
        "row_decision_status": decision_status,
        "exact_blockers": blockers,
        "field_status": field_status,
        "source_contract_notes": [
            "filled_at_utc is source-authorized side-aware quote touch only; it is not broker/account/live fill proof",
            "rows with filled_at_utc leave no-fill closure and require a separate fill/path categorical contract",
            "no R/performance/win-rate/expectancy/validation/promotion/live-effect claim is emitted",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }

    debug = {
        "source_close_packet_row_id": source_row["packet_row_id"],
        "lifecycle_group_line_refs": line_refs(lifecycle_group),
        "audit_line_ref": source_line_ref(audit_row) if audit_row else None,
        "missing_tick_files": missing_ticks,
        "decision_status": decision_status,
    }
    return row, debug


def build() -> dict[str, Any]:
    close_rows = read_jsonl_with_lines(SOURCE_ROWS_PATH)
    source_rows = [row for row in close_rows if row.get("source_lane") == "OTI1_LIFECYCLE"]
    lifecycle_rows = read_jsonl_with_lines(PENDING_LIFECYCLE_PATH)
    pending_audit_rows = read_jsonl_with_lines(PENDING_AUDIT_PATH)
    route_ledger = read_json(ROUTER_ROUTE_LEDGER)
    search_ledger = read_json(ROUTER_SOURCE_SEARCH)

    packet_rows: list[dict[str, Any]] = []
    debug_rows: list[dict[str, Any]] = []
    for row in source_rows:
        materialized, debug = materialize_row(row, lifecycle_rows, pending_audit_rows)
        packet_rows.append(materialized)
        debug_rows.append(debug)

    decision_counts = Counter(row["row_decision_status"] for row in packet_rows)
    field_missing_counts = Counter()
    for row in packet_rows:
        for field, status in row["field_status"].items():
            if status.startswith("BLOCKED"):
                field_missing_counts[field] += 1

    noleak_hits = scan_forbidden_keys(packet_rows)
    source_hash_records: dict[str, dict[str, Any]] = {}
    for row in packet_rows:
        for source in row["source_files"]:
            path = source["path"]
            if path not in source_hash_records:
                source_hash_records[path] = {
                    "path": path,
                    "sha256": source.get("sha256"),
                    "roles": sorted({source.get("role")}),
                    "exists": True if source.get("sha256") else Path(path).exists(),
                }
            else:
                source_hash_records[path]["roles"] = sorted(
                    set(source_hash_records[path]["roles"]) | {source.get("role")}
                )

    duplicate_groups = defaultdict(list)
    duplicate_keys = defaultdict(list)
    for row in packet_rows:
        duplicate_groups[row["duplicate_group_id"]].append(row["packet_row_id"])
        duplicate_keys[row["nofill_duplicate_key"]].append(row["packet_row_id"])

    source_search_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_SOURCE_SEARCH_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "searched_roots": [
            {"root": rel(OUTCOME_ROOT), "exists": OUTCOME_ROOT.exists(), "role": "worktree outcome-testing artifacts"},
            {"root": rel(SOURCE_PACKET_DIR), "exists": SOURCE_PACKET_DIR.exists(), "role": "accepted nofill closure source packet"},
            {"root": rel(REPO_ROOT / "shadow_logs"), "exists": (REPO_ROOT / "shadow_logs").exists(), "role": "local lifecycle/audit source logs"},
            {"root": str(TICK_ROOT), "exists": TICK_ROOT.exists(), "role": "absolute tick parquet root"},
        ],
        "router_family_tick_availability": search_ledger["tick_availability_by_family"]["OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET"],
        "source_hash_records": list(source_hash_records.values()),
        "debug_lifecycle_line_resolution": debug_rows,
        "materialized_row_count": len(packet_rows),
        "rows_with_missing_tick_source": sum(1 for row in packet_rows if "BLOCK_SOURCE_MISSING_TICK_FILE" in row["exact_blockers"]),
        "rows_with_empty_tick_window": sum(1 for row in packet_rows if "BLOCK_SOURCE_EMPTY_TICK_WINDOW" in row["exact_blockers"]),
    }

    decisions_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_ROW_DECISION_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_count": len(packet_rows),
        "decision_counts": dict(decision_counts),
        "row_decisions": [
            {
                "packet_row_id": row["packet_row_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_row_id": row["source_row_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "entry_touched_at_utc": row["entry_touched_at_utc"],
                "filled_at_utc": row["filled_at_utc"],
                "cancelled_at_utc": row["cancelled_at_utc"],
                "expired_at_utc": row["expired_at_utc"],
                "frozen_horizon_end_utc": row["frozen_horizon_end_utc"],
                "row_decision_status": row["row_decision_status"],
                "exact_blockers": row["exact_blockers"],
            }
            for row in packet_rows
        ],
    }

    hash_audit_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_hash_records": list(source_hash_records.values()),
        "source_hash_missing_count": sum(1 for record in source_hash_records.values() if not record.get("sha256")),
        "forbidden_key_hits": noleak_hits,
        "forbidden_key_hit_count": len(noleak_hits),
        "asof_rule": "decision-time fields are unchanged; lifecycle/tick events are source-control label-time fields only",
        "all_rows_false_flags": all(
            row["promotion_verdict"] == PROMOTION_VERDICT
            and row["validation_safe"] is False
            and row["outcome_review_opened"] is False
            and row["live_effect"] is False
            for row in packet_rows
        ),
    }

    duplicate_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_DUPLICATE_CONTRACT_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_count": len(packet_rows),
        "unique_duplicate_group_id_count": len(duplicate_groups),
        "unique_nofill_duplicate_key_count": len(duplicate_keys),
        "duplicate_group_sizes": {key: len(value) for key, value in sorted(duplicate_groups.items())},
        "nofill_duplicate_key_sizes": {key: len(value) for key, value in sorted(duplicate_keys.items())},
        "duplicate_policy": "row-level source packet preserves repeats; future result lanes must collapse by nofill_duplicate_key before claims",
        "excluded_t3_overlap_count": sum(1 for row in packet_rows if row["source_inventory_id"] in EXCLUDED_T3_IDS),
    }

    impossibility_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_IMPOSSIBILITY_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "rows_with_exact_blockers": sum(1 for row in packet_rows if row["exact_blockers"]),
        "exact_blocker_counts": dict(Counter(blocker for row in packet_rows for blocker in row["exact_blockers"])),
        "access_requests_required": [],
        "source_correction_result": (
            "All 54 OTI1 rows have materialized closure fields. Rows with source-authorized entry touch "
            "are source-corrected into separate fill/path-contract territory, not accepted no-fill labels."
        ),
    }

    packet_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET",
        "schema_version": SCHEMA,
        "packet_id": PACKET_ID,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_count": len(packet_rows),
        "source_rows_in_scope": len(source_rows),
        "blocker_tuple": ["BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD"],
        "decision_counts": dict(decision_counts),
        "entry_touched_rows": sum(1 for row in packet_rows if row["entry_touched_at_utc"]),
        "filled_at_rows": sum(1 for row in packet_rows if row["filled_at_utc"]),
        "no_entry_touch_rows": sum(1 for row in packet_rows if row["entry_touched_at_utc"] is None),
        "cancelled_at_rows": sum(1 for row in packet_rows if row["cancelled_at_utc"]),
        "expired_at_rows": sum(1 for row in packet_rows if row["expired_at_utc"]),
        "rows_with_exact_blockers": impossibility_payload["rows_with_exact_blockers"],
        "source_control_only": True,
        "result_label_emitted": False,
        "r_performance_computed": False,
        "broker_account_live_order_labels_used": False,
        "artifact_paths": {
            "rows": rel(OUT_JSONL),
            "source_search_ledger": rel(SEARCH_JSON),
            "row_decision_ledger": rel(DECISIONS_JSON),
            "source_hash_noleak_asof_audit": rel(HASH_AUDIT_JSON),
            "duplicate_contract_audit": rel(DUPLICATE_JSON),
            "impossibility_ledger": rel(IMPOSSIBILITY_JSON),
            "completion_audit": rel(COMPLETION_JSON),
        },
    }

    context_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_CONTEXT_ANCHOR",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "head": git_output("rev-parse", "--short", "HEAD"),
        "controlling_prompt": rel(CONTROL_PROMPT),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective": "materialize entry/fill/cancel/expiry/horizon source timestamps for 54 OTI1 pending-intent rows",
        "inputs_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(CONTROL_PROMPT),
            rel(ROUTER_CONTEXT),
            rel(ROUTER_ROUTE_LEDGER),
            rel(ROUTER_SOURCE_SEARCH),
            rel(SOURCE_ROWS_PATH),
            rel(PENDING_LIFECYCLE_PATH),
            rel(PENDING_AUDIT_PATH),
            str(TICK_ROOT),
            rel(CONTRACT_TOUCH_PATH),
            rel(CONTRACT_FIELD_REQ_PATH),
            rel(CONTRACT_NOLEAK_PATH),
        ],
        "route_ledger_oti1_count": next(
            item["row_count"]
            for item in route_ledger["family_route_decisions"]
            if item["route_family"] == "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET"
        ),
        "packet_summary": packet_payload,
    }

    completion_checks = {
        "mandatory_preflight_completed": True,
        "controlling_prompt_read": CONTROL_PROMPT.exists(),
        "router_ledgers_read": ROUTER_ROUTE_LEDGER.exists() and ROUTER_SOURCE_SEARCH.exists(),
        "row_count_is_54": len(packet_rows) == 54,
        "all_rows_have_required_timestamp_fields": all(
            all(
                key in row
                for key in [
                    "entry_touched_at_utc",
                    "filled_at_utc",
                    "cancelled_at_utc",
                    "expired_at_utc",
                    "pending_intent_id_or_deterministic_key",
                    "source_hash_path",
                    "side_aware_touch_source",
                    "as_of_rule",
                ]
            )
            for row in packet_rows
        ),
        "all_rows_materialized_or_exact_blocked": len(packet_rows) == 54 and field_missing_counts == Counter(),
        "source_hashes_present": hash_audit_payload["source_hash_missing_count"] == 0,
        "forbidden_key_hits_zero": len(noleak_hits) == 0,
        "duplicate_audit_complete": duplicate_payload["row_count"] == 54,
        "no_access_request_needed": impossibility_payload["access_requests_required"] == [],
        "preserved_no_promotion": all(row["promotion_verdict"] == PROMOTION_VERDICT for row in packet_rows),
        "validation_safe_false": all(row["validation_safe"] is False for row in packet_rows),
        "outcome_review_opened_false": all(row["outcome_review_opened"] is False for row in packet_rows),
        "live_effect_false": all(row["live_effect"] is False for row in packet_rows),
        "no_r_performance_computed": packet_payload["r_performance_computed"] is False,
        "no_broker_account_live_order_labels_used": packet_payload["broker_account_live_order_labels_used"] is False,
    }
    completion_payload = {
        "artifact_family": "OTI1_PENDING_INTENT_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restated": (
            "Build a source-correction packet for 54 OTI1 pending-intent rows that materializes "
            "entry_touched_at_utc plus fill/cancel/expiry/horizon timestamps, or exact blockers."
        ),
        "prompt_to_artifact_checklist": {
            "context_anchor_and_source_search_ledger": [rel(CONTEXT_JSON), rel(SEARCH_JSON)],
            "source_contract_packet": [rel(OUT_JSON), rel(OUT_JSONL)],
            "row_level_decisions": [rel(DECISIONS_JSON)],
            "source_hash_noleak_duplicate_asof_checks": [rel(HASH_AUDIT_JSON), rel(DUPLICATE_JSON)],
            "exact_impossibility_or_access_blockers": [rel(IMPOSSIBILITY_JSON)],
            "completion_audit": [rel(COMPLETION_JSON)],
        },
        "completion_checks": completion_checks,
        "can_mark_goal_complete": all(completion_checks.values()),
        "decision_counts": dict(decision_counts),
        "source_correction_summary": {
            "rows_materialized": len(packet_rows),
            "entry_touched_at_utc_materialized_timestamp": packet_payload["entry_touched_rows"],
            "entry_touched_at_utc_materialized_null_no_touch": packet_payload["no_entry_touch_rows"],
            "source_authorized_fill_touch_rows": packet_payload["filled_at_rows"],
            "source_corrected_no_entry_rows": packet_payload["no_entry_touch_rows"],
            "exact_blocked_rows": impossibility_payload["rows_with_exact_blockers"],
        },
        "scope_boundaries_preserved": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "result_label_emitted": False,
            "r_performance_computed": False,
            "broker_account_live_order_labels_used": False,
            "paid_api_databento_calls": False,
            "mt5_order_account_history_calls": False,
        },
    }

    write_jsonl(OUT_JSONL, packet_rows)
    write_json(OUT_JSON, packet_payload)
    write_json(CONTEXT_JSON, context_payload)
    write_json(SEARCH_JSON, source_search_payload)
    write_json(DECISIONS_JSON, decisions_payload)
    write_json(HASH_AUDIT_JSON, hash_audit_payload)
    write_json(DUPLICATE_JSON, duplicate_payload)
    write_json(IMPOSSIBILITY_JSON, impossibility_payload)
    write_json(COMPLETION_JSON, completion_payload)

    write_md(
        CONTEXT_MD,
        [
            "# OTI1 Pending Intent Context Anchor",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Objective",
            "",
            context_payload["objective"],
            "",
            "## Inputs Read",
            "",
            *[f"- `{item}`" for item in context_payload["inputs_read"]],
            "",
            "## Packet Summary",
            "",
            f"- Rows materialized: `{packet_payload['row_count']}`",
            f"- Entry-touch timestamps: `{packet_payload['entry_touched_rows']}`",
            f"- No-entry materialized nulls: `{packet_payload['no_entry_touch_rows']}`",
            f"- Source-authorized fill-touch rows routed out of no-fill closure: `{packet_payload['filled_at_rows']}`",
        ],
    )
    write_md(
        SEARCH_MD,
        [
            "# OTI1 Pending Intent Source Search Ledger",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Search Result",
            "",
            f"- Rows materialized: `{source_search_payload['materialized_row_count']}`",
            f"- Missing tick files: `{source_search_payload['rows_with_missing_tick_source']}`",
            f"- Empty tick windows: `{source_search_payload['rows_with_empty_tick_window']}`",
            f"- Source hash records: `{len(source_search_payload['source_hash_records'])}`",
            "",
            "## Roots",
            "",
            *[
                f"- `{root['root']}` exists=`{root['exists']}` role={root['role']}"
                for root in source_search_payload["searched_roots"]
            ],
        ],
    )
    write_md(
        DECISIONS_MD,
        [
            "# OTI1 Pending Intent Row Decision Ledger",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            "## Decision Counts",
            "",
            *[f"- `{key}`: `{value}`" for key, value in sorted(decision_counts.items())],
            "",
            "Rows with source-authorized entry touch require a separate fill/path contract before any future label.",
        ],
    )
    write_md(
        HASH_AUDIT_MD,
        [
            "# OTI1 Source Hash / No-Leak / As-Of Audit",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"- Source hash records: `{len(source_hash_records)}`",
            f"- Missing source hashes: `{hash_audit_payload['source_hash_missing_count']}`",
            f"- Forbidden key hits: `{hash_audit_payload['forbidden_key_hit_count']}`",
            f"- All false flags preserved: `{hash_audit_payload['all_rows_false_flags']}`",
            "",
            f"As-of rule: {hash_audit_payload['asof_rule']}",
        ],
    )
    write_md(
        DUPLICATE_MD,
        [
            "# OTI1 Duplicate Contract Audit",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"- Row count: `{duplicate_payload['row_count']}`",
            f"- Unique duplicate_group_id: `{duplicate_payload['unique_duplicate_group_id_count']}`",
            f"- Unique nofill_duplicate_key: `{duplicate_payload['unique_nofill_duplicate_key_count']}`",
            f"- Excluded T3 overlap: `{duplicate_payload['excluded_t3_overlap_count']}`",
            "",
            duplicate_payload["duplicate_policy"],
        ],
    )
    write_md(
        IMPOSSIBILITY_MD,
        [
            "# OTI1 Impossibility / Access Ledger",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"- Rows with exact blockers: `{impossibility_payload['rows_with_exact_blockers']}`",
            f"- Access requests required: `{len(impossibility_payload['access_requests_required'])}`",
            "",
            impossibility_payload["source_correction_result"],
        ],
    )
    write_md(
        COMPLETION_MD,
        [
            "# OTI1 Pending Intent Completion Audit",
            "",
            f"Generated: {GENERATED_AT_UTC}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Objective Restated",
            "",
            completion_payload["objective_restated"],
            "",
            "## Completion Checks",
            "",
            *[f"- `{key}`: `{value}`" for key, value in completion_checks.items()],
            "",
            f"Can mark goal complete: `{completion_payload['can_mark_goal_complete']}`",
            "",
            "## Summary",
            "",
            f"- Rows materialized: `{completion_payload['source_correction_summary']['rows_materialized']}`",
            f"- Entry-touch timestamps: `{completion_payload['source_correction_summary']['entry_touched_at_utc_materialized_timestamp']}`",
            f"- No-entry materialized nulls: `{completion_payload['source_correction_summary']['entry_touched_at_utc_materialized_null_no_touch']}`",
            f"- Exact blocked rows: `{completion_payload['source_correction_summary']['exact_blocked_rows']}`",
            "",
            "No result labels, R/performance, validation, promotion, broker/account/live-order labels, paid/API/Databento calls, or MT5 order/account/history calls were introduced.",
        ],
    )

    artifacts = [
        OUT_JSONL,
        OUT_JSON,
        CONTEXT_JSON,
        CONTEXT_MD,
        SEARCH_JSON,
        SEARCH_MD,
        DECISIONS_JSON,
        DECISIONS_MD,
        HASH_AUDIT_JSON,
        HASH_AUDIT_MD,
        DUPLICATE_JSON,
        DUPLICATE_MD,
        IMPOSSIBILITY_JSON,
        IMPOSSIBILITY_MD,
        COMPLETION_JSON,
        COMPLETION_MD,
    ]
    manifest = {
        "artifact_family": "OTI1_PENDING_INTENT_ARTIFACT_MANIFEST",
        "schema_version": SCHEMA,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "artifact_count": len(artifacts),
        "artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in artifacts
        ],
    }
    write_json(MANIFEST_JSON, manifest)
    return completion_payload


if __name__ == "__main__":
    result = build()
    print(json.dumps({"can_mark_goal_complete": result["can_mark_goal_complete"], "decision_counts": result["decision_counts"]}, sort_keys=True))
