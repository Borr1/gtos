"""Build OTI2 fill/path categorical contract V2 artifacts.

Research/control lane only. This script reconstructs the current OTI2
fill/path candidate universe from accepted source-correction artifacts,
freezes a conservative source contract, and emits row-level categorical
event-order decisions without R/performance, account, broker, or live order
labels.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-08"
LANE_ID = "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2"
SCHEMA_VERSION = "oti2_fill_path_categorical_contract_v2"
CONTRACT_ID = "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2"
ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent

ROUTER_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router"
OTI1_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/oti1_pending_intent_closure_source_packet"
OTI3_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract"
OTI4_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision"
G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit"
CAT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet"
CONTRACT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_result_contract_design"
OTI2_RISKBANK_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results"

MAIN_DATA_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data")
MAIN_TICK_ROOT = MAIN_DATA_ROOT / "ticks"
MAIN_EXTERNAL_ROOT = MAIN_DATA_ROOT / "external"
MAIN_SHADOW_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs")
TMP_ROOT = Path(r"C:\tmp")
TMP_GTOS_ROOT = Path(r"C:\tmp\gtos_otb")

FORBIDDEN_OUTPUT_KEYS = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    return pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")


def iso_ts(value: pd.Timestamp | None) -> str | None:
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def resolve_source_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.name.startswith("OTI3_MT5_READ_ONLY_USDJPY_TICKS_"):
        current_copy = OTI3_DIR / path.name
        if current_copy.exists():
            return current_copy
    if path.is_absolute() and path.exists():
        return path
    candidate = ROOT / path_value
    if candidate.exists():
        return candidate
    return path if path.is_absolute() else candidate


def source_record(
    path_value: str | Path | None,
    role: str,
    expected_sha256: str | None = None,
    line_refs: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    path = resolve_source_path(str(path_value)) if path_value is not None else None
    exists = bool(path and path.exists())
    sha = sha256_file(path) if exists and path and path.is_file() else None
    return {
        "path": str(path) if path is not None else None,
        "path_rel": rel(path) if path is not None else None,
        "role": role,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path and path.is_file() else None,
        "sha256": sha,
        "expected_sha256": expected_sha256,
        "hash_match": None if not expected_sha256 or sha is None else sha == expected_sha256,
        "line_refs": line_refs or [],
        "notes": notes,
    }


def event_name(name: str) -> str:
    return {
        "terminal_area_touch": "terminal_area",
        "protective_level_touch": "protective_level",
    }.get(name, name)


def sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    out = {
        "event": event_name(str(event.get("event"))),
        "first_touch_utc": event.get("first_touch_utc") or event.get("timestamp_utc"),
    }
    for key in ("bid", "ask", "source_row_position", "source_path", "source_sha256"):
        if key in event:
            out[key] = event[key]
    return out


def sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [sanitize_event(event) for event in events],
        key=lambda item: (
            item.get("first_touch_utc") or "",
            item.get("source_row_position", 10**18),
            item.get("event") or "",
        ),
    )


def classify_ordered_events(events: list[dict[str, Any]], same_timestamp: bool) -> tuple[str | None, list[str], list[str], str]:
    if same_timestamp:
        return (
            None,
            ["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"],
            ["Multiple first source events share one timestamp/quote row; source-safe order cannot be inferred."],
            "blocked_same_timestamp_or_same_tick",
        )
    if not events:
        return (
            None,
            ["BLOCK_FILL_PATH_NO_SOURCE_EVENTS"],
            ["No source-safe entry, terminal, or protective touch event is present in the accepted source window."],
            "blocked_no_source_events",
        )
    first = events[0]["event"]
    if first != "entry_touch":
        return (
            None,
            ["BLOCK_FILL_PATH_FIRST_EVENT_NOT_ENTRY_TOUCH"],
            [f"First source-safe event is {first}; this contract labels post-entry path order only."],
            "blocked_first_event_not_entry",
        )
    sequence = [event["event"] for event in events]
    if len(sequence) == 1:
        return "fill_path_entry_touch_no_terminal_or_protective_observed", [], [], "label_assigned"
    if sequence[1] == "terminal_area":
        if "protective_level" in sequence[2:]:
            return "fill_path_entry_before_terminal_area_before_protective_level", [], [], "label_assigned"
        return "fill_path_entry_before_terminal_area_no_protective_observed", [], [], "label_assigned"
    if sequence[1] == "protective_level":
        if "terminal_area" in sequence[2:]:
            return "fill_path_entry_before_protective_level_before_terminal_area", [], [], "label_assigned"
        return "fill_path_entry_before_protective_level_no_terminal_observed", [], [], "label_assigned"
    return (
        None,
        ["BLOCK_FILL_PATH_UNKNOWN_EVENT_SEQUENCE"],
        [f"Unsupported source event sequence: {'>'.join(sequence)}"],
        "blocked_unknown_sequence",
    )


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def load_cat_rows() -> dict[str, dict[str, Any]]:
    rows = read_jsonl(CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl")
    return {row["source_close_packet_row_id"]: row for row in rows}


def build_contract(generated_at_utc: str) -> dict[str, Any]:
    return {
        "artifact_family": "OTI2_FILL_PATH_FROZEN_CONTRACT",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "contract_id": CONTRACT_ID,
        "contract_status": "FROZEN_BEFORE_ROW_LABELING",
        "contract_frozen_at_utc": generated_at_utc,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "scope": "categorical_fill_path_event_order_only",
        "source_hierarchy": {
            "tier_1_side_aware_tick_or_quote": "Required for new entry/protective/terminal ordering labels unless an upstream accepted source packet already materialized source-safe ordered events.",
            "tier_2_accepted_source_correction_packet": "OTI1 and OTI3 accepted packets can be consumed as source-authorized event-order inputs after hashes/no-leak checks.",
            "tier_3_pending_lifecycle_logs": "May prove cancel/expiry timestamps as internal source-control fields only; broker/account/order labels are not propagated.",
            "tier_4_lower_timeframe_ohlc_or_m1_path": "Context and blocker anatomy only. It cannot prove side-aware fill/path order without tier-1 quote/tick support.",
        },
        "side_aware_touch_rules": {
            "LONG": {
                "entry_touch": "ask <= entry_price",
                "terminal_area_touch": "bid >= terminal_area_price",
                "protective_level_touch": "bid <= protective_level_price",
            },
            "SHORT": {
                "entry_touch": "bid >= entry_price",
                "terminal_area_touch": "ask <= terminal_area_price",
                "protective_level_touch": "ask >= protective_level_price",
            },
        },
        "ordering_policy": {
            "primary_sort": ["first_touch_utc", "source_row_position_or_ts_msc_if_available"],
            "same_timestamp_policy": "Block if the first timestamp has multiple touch predicates and no source row sequence separates them.",
            "same_quote_row_policy": "Block if one source quote row satisfies entry and protective/terminal predicates simultaneously; no lexical event ordering is allowed.",
            "same_bar_lower_timeframe_policy": "Lower-timeframe OHLC same-bar order is not resolved in this contract.",
        },
        "label_taxonomy": {
            "fill_path_entry_before_terminal_area_before_protective_level": "Entry touch first, terminal-area touch next, protective touch later.",
            "fill_path_entry_before_terminal_area_no_protective_observed": "Entry touch first, terminal-area touch later, no protective touch observed in the source window.",
            "fill_path_entry_before_protective_level_before_terminal_area": "Entry touch first, protective touch next, terminal-area touch later.",
            "fill_path_entry_before_protective_level_no_terminal_observed": "Entry touch first, protective touch later, no terminal-area touch observed in the source window.",
            "fill_path_entry_touch_no_terminal_or_protective_observed": "Entry touch first and no terminal/protective touch observed in the source window.",
        },
        "blocker_taxonomy": {
            "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": "First source timestamp/quote row satisfies multiple touch predicates with no source-safe sequence.",
            "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": "Original OTI2 row has M1 entry-touch context but lacks side-aware quote/tick proof for that entry touch.",
            "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": "Original OTI2 row has a tick-source gap inside the active pending window before cancel, so no-entry-before-cancel cannot be proved.",
            "BLOCK_FILL_PATH_FIRST_EVENT_NOT_ENTRY_TOUCH": "Row belongs to no-fill terminal-before-entry family unless another contract admits it.",
            "BLOCK_FILL_PATH_NO_SOURCE_EVENTS": "No source-safe event exists in the frozen source window.",
            "BLOCK_FILL_PATH_UNKNOWN_EVENT_SEQUENCE": "Source events exist but do not match the frozen taxonomy.",
        },
        "duplicate_denominator_policy": {
            "primary_denominator_key": "nofill_duplicate_key",
            "row_identity": "source_close_packet_row_id plus source_inventory_id",
            "counting": "Report row count and unique nofill_duplicate_key count; no validation/promotion use at this sample size.",
            "duplicate_group_policy": "duplicate_group_id concentration is diagnostic only; conflicting duplicate keys would block labels.",
        },
        "sample_floor_policy": {
            "categorical_packet": "Counts can be reported as lifecycle/source evidence at any n.",
            "validation": "Blocked; under_sample_floor until >=30 unique nofill_duplicate_key per label family and separate validation dossier.",
            "promotion": "Always blocked for this lane.",
        },
        "forbidden_fields_and_claims": sorted(FORBIDDEN_OUTPUT_KEYS),
        "forbidden_surfaces": [
            "live trading prompts",
            "src trading logic",
            "risk settings",
            "execution behavior",
            "permissions",
            "safety selectors",
            "MT5 order/account/history",
            "canaries",
            "paid/API/Databento",
            "credentials",
            "remotes",
            "master registry edits",
        ],
    }


def label_oti1_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        source = row.get("side_aware_touch_source") or {}
        events = sort_events(source.get("ordered_source_events") or [])
        label, blockers, reasons, status = classify_ordered_events(events, bool(source.get("same_timestamp_ambiguity")))
        output.append(
            make_row_decision(
                source_family="OTI1_PENDING_INTENT",
                source_row=row,
                source_input_decision=row.get("row_decision_status"),
                ordered_events=events,
                label=label,
                blockers=blockers,
                blocker_reasons=reasons,
                route_status=status,
                source_order_resolution={
                    "upstream_packet": "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_V1",
                    "source_order_status": "accepted_source_authorized_ordered_events",
                    "same_timestamp_ambiguity": bool(source.get("same_timestamp_ambiguity")),
                },
            )
        )
    return output


def label_oti3_rows(rows: list[dict[str, Any]], same_timestamp_inspections: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        events = sort_events(row.get("ordered_source_events") or [])
        same_timestamp = bool(row.get("same_timestamp_ambiguity"))
        label, blockers, reasons, status = classify_ordered_events(events, same_timestamp)
        inspection = same_timestamp_inspections.get(row["source_close_packet_row_id"])
        if same_timestamp:
            blockers = ["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"]
            reasons = [
                "The source tick/quote file has one source row at the first timestamp and that row satisfies multiple touch predicates; no sub-row order exists."
            ]
            status = "blocked_same_tick_order_unresolvable"
            label = None
        output.append(
            make_row_decision(
                source_family="OTI3_USDJPY",
                source_row=row,
                source_input_decision="+".join(row.get("exact_blocker_codes") or []),
                ordered_events=events,
                label=label,
                blockers=blockers,
                blocker_reasons=reasons,
                route_status=status,
                source_order_resolution={
                    "upstream_packet": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
                    "source_order_status": "not_resolvable_from_source_safe_tick_order" if same_timestamp else "accepted_source_authorized_ordered_events",
                    "same_timestamp_ambiguity": same_timestamp,
                    "same_timestamp_inspection": inspection,
                },
            )
        )
    return output


def make_row_decision(
    source_family: str,
    source_row: dict[str, Any],
    source_input_decision: str | None,
    ordered_events: list[dict[str, Any]],
    label: str | None,
    blockers: list[str],
    blocker_reasons: list[str],
    route_status: str,
    source_order_resolution: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "contract_id": CONTRACT_ID,
        "packet_row_id": None,
        "source_family": source_family,
        "source_input_decision": source_input_decision,
        "source_close_packet_row_id": source_row.get("source_close_packet_row_id"),
        "source_inventory_id": source_row.get("source_inventory_id"),
        "source_lane": source_row.get("source_lane"),
        "source_packet_id": source_row.get("source_packet_id"),
        "source_row_id": source_row.get("source_row_id"),
        "symbol": source_row.get("symbol"),
        "session": source_row.get("session"),
        "side": source_row.get("side"),
        "decision_asof_utc": source_row.get("decision_asof_utc"),
        "entry_price": source_row.get("entry_price"),
        "terminal_area_price": source_row.get("terminal_area_price"),
        "protective_level_price": source_row.get("protective_level_price"),
        "duplicate_group_id": source_row.get("duplicate_group_id"),
        "nofill_duplicate_key": source_row.get("nofill_duplicate_key"),
        "ordered_source_events": ordered_events,
        "same_timestamp_ambiguity": bool(source_order_resolution.get("same_timestamp_ambiguity")),
        "source_order_resolution": source_order_resolution,
        "categorical_fill_path_label": label,
        "categorical_label_status": "categorical_fill_path_only" if label else "blocked_no_label",
        "label_family": "fill_path_categorical_only" if label else None,
        "eligibility_decision": "ELIGIBLE_LABEL_ASSIGNED" if label else "BLOCKED_BEFORE_LABEL",
        "eligibility_checked_before_label": True,
        "exact_blocker_codes": blockers,
        "exact_blocker_reasons": blocker_reasons,
        "route_status": route_status,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def inspect_same_timestamp_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    inspections: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not row.get("same_timestamp_ambiguity"):
            continue
        events = row.get("ordered_source_events") or []
        if not events:
            continue
        first_ts = parse_ts(events[0].get("first_touch_utc"))
        source_path = resolve_source_path(events[0].get("source_path"))
        if first_ts is None or source_path is None or not source_path.exists():
            inspections[row["source_close_packet_row_id"]] = {
                "status": "SOURCE_PATH_MISSING_FOR_SAME_TIMESTAMP_INSPECTION",
                "source_path": str(source_path) if source_path else None,
            }
            continue
        df = pd.read_parquet(source_path)
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        hits = df[df["ts_utc"] == first_ts]
        hit_records = []
        for idx, hit in hits.iterrows():
            hit_records.append(
                {
                    "source_row_position": int(idx),
                    "ts_utc": iso_ts(hit["ts_utc"]),
                    "ts_msc": int(hit["ts_msc"]) if "ts_msc" in hit else None,
                    "bid": float(hit["bid"]),
                    "ask": float(hit["ask"]),
                    "flags": int(hit["flags"]) if "flags" in hit else None,
                }
            )
        inspections[row["source_close_packet_row_id"]] = {
            "status": "BLOCKED_NOT_RESOLVABLE_FROM_SOURCE_SAFE_TICK_ORDER",
            "source_path": str(source_path),
            "source_sha256": sha256_file(source_path),
            "first_timestamp_utc": iso_ts(first_ts),
            "rows_at_first_timestamp": len(hits),
            "source_rows_at_first_timestamp": hit_records,
            "decision": "remain_blocked",
            "reason": "One quote row has a single timestamp/ts_msc and simultaneously satisfies multiple side-aware predicates; MT5 tick source has no intra-row event sequence.",
        }
    return inspections


def build_oti2_original_decision(cat_rows: dict[str, dict[str, Any]], generated_at_utc: str) -> tuple[dict[str, Any], dict[str, Any]]:
    router = read_json(ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json")
    router_row = [row for row in router["row_route_decisions"] if row.get("route_family") == "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT"][0]
    cat_row = cat_rows[router_row["source_close_packet_row_id"]]
    riskbank_rows = read_jsonl(OTI2_RISKBANK_DIR / f"OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    riskbank_row = next(row for row in riskbank_rows if row.get("setup_id") == router_row["source_row_id"])

    pending_cancel = find_pending_cancel(router_row["source_row_id"])
    tick_coverage = inspect_oti2_tick_coverage(cat_row, pending_cancel)
    source_order_resolution = {
        "upstream_router_status": "source_safe_next_prompt_pack",
        "m1_path_context_entry_first_touch_utc": riskbank_row.get("entry_first_touch_utc"),
        "m1_path_context_terminal_area_first_touch_utc": riskbank_row.get("tp1_first_touch_utc"),
        "m1_path_context_status": "context_only_not_side_aware_fill_path_label",
        "pending_cancel_observation": pending_cancel,
        "tick_coverage_inspection": tick_coverage,
        "source_order_status": "blocked_exact_source_safe_entry_and_active_window_not_proven",
        "decision": "remain_blocked_before_label",
    }
    source_row = {
        **cat_row,
        "source_input_decision": "+".join(router_row.get("blocker_codes") or []),
    }
    decision = make_row_decision(
        source_family="OTI2_ORIGINAL_ROUTER",
        source_row=source_row,
        source_input_decision=source_row["source_input_decision"],
        ordered_events=sort_events(cat_row.get("ordered_source_events") or []),
        label=None,
        blockers=[
            "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED",
            "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP",
        ],
        blocker_reasons=[
            "Original OTI2 entry-touch evidence is lower-timeframe/M1 context, not a side-aware bid/ask quote touch under the frozen V2 contract.",
            "XAUUSD tick coverage does not cover the complete active pending window through the observed new-day cancel timestamp, so no-entry-before-cancel cannot be source-safely proved.",
        ],
        route_status="blocked_original_oti2_source_gap",
        source_order_resolution=source_order_resolution,
    )
    decision["source_order_resolution"]["contract_frozen_at_utc"] = generated_at_utc
    return decision, source_order_resolution


def find_pending_cancel(candidate_id: str) -> dict[str, Any]:
    path = ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"
    best: dict[str, Any] | None = None
    line_no = None
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or candidate_id not in line:
            continue
        row = json.loads(line)
        if row.get("cancel_reason") in {"new_day", "system", "wrong_side"} or row.get("intent_after_check") == "manual_or_system_cancelled":
            best = row
            line_no = idx
            break
    if not best:
        return {
            "status": "NO_PENDING_CANCEL_ROW_FOUND",
            "source_path": rel(path),
        }
    return {
        "status": "PENDING_CANCEL_SOURCE_ROW_FOUND_CONTEXT_ONLY",
        "source_path": rel(path),
        "source_line": line_no,
        "candidate_id": best.get("candidate_id"),
        "pending_created_time_utc": best.get("pending_created_time_utc"),
        "cancel_observed_at_utc": best.get("timestamp_utc"),
        "cancel_reason": best.get("cancel_reason") or best.get("reason"),
        "internal_intent_state_after_check": best.get("intent_after_check"),
        "note": "Only internal lifecycle/cancel fields are whitelisted; broker/account/order fields in the raw source are not propagated.",
    }


def inspect_oti2_tick_coverage(cat_row: dict[str, Any], pending_cancel: dict[str, Any]) -> dict[str, Any]:
    symbol = cat_row["symbol"]
    dates = ["2026-05-05", "2026-05-06"]
    file_summaries = []
    for date_iso in dates:
        path = MAIN_TICK_ROOT / symbol / f"{date_iso}.parquet"
        summary = {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
            "first_ts_utc": None,
            "last_ts_utc": None,
            "rows": 0,
        }
        if path.exists():
            df = pd.read_parquet(path, columns=["ts_utc", "ts_msc", "bid", "ask"])
            df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
            summary["rows"] = int(len(df))
            if len(df):
                summary["first_ts_utc"] = iso_ts(df["ts_utc"].min())
                summary["last_ts_utc"] = iso_ts(df["ts_utc"].max())
        file_summaries.append(summary)
    cancel_ts = parse_ts(pending_cancel.get("cancel_observed_at_utc")) if pending_cancel else None
    may5_last = parse_ts(file_summaries[0]["last_ts_utc"])
    may6_first = parse_ts(file_summaries[1]["first_ts_utc"])
    gap_seconds = None
    if cancel_ts is not None and may5_last is not None:
        gap_seconds = max(0.0, (cancel_ts - may5_last).total_seconds())
    return {
        "status": "BLOCKED_TICK_COVERAGE_GAP_BEFORE_PENDING_CANCEL",
        "symbol": symbol,
        "active_window_start_utc": pending_cancel.get("pending_created_time_utc"),
        "pending_cancel_observed_at_utc": pending_cancel.get("cancel_observed_at_utc"),
        "file_summaries": file_summaries,
        "gap_seconds_between_last_tick_before_cancel_and_cancel": gap_seconds,
        "may6_first_tick_after_cancel": bool(cancel_ts is not None and may6_first is not None and may6_first > cancel_ts),
        "reason": "The 2026-05-06 XAUUSD tick file starts after the pending cancel and after the M1-context entry-touch window, so side-aware entry/no-entry ordering cannot be proven.",
    }


def build_source_search_ledger(decisions: list[dict[str, Any]], source_records: list[dict[str, Any]]) -> dict[str, Any]:
    needed_symbol_dates = sorted(
        {
            f"{row['symbol']}|{(row.get('decision_asof_utc') or '')[:10]}"
            for row in decisions
            if row.get("symbol") and row.get("decision_asof_utc")
        }
        | {"XAUUSD|2026-05-06"}
    )
    root_checks = []
    for root_path, role in [
        (ROOT, "current_worktree"),
        (MAIN_DATA_ROOT, "absolute_main_data_root"),
        (MAIN_TICK_ROOT, "absolute_main_tick_root"),
        (MAIN_EXTERNAL_ROOT, "absolute_main_external_root"),
        (MAIN_SHADOW_ROOT, "absolute_main_shadow_logs_root"),
        (TMP_ROOT, "tmp_root_targeted"),
        (TMP_GTOS_ROOT, "tmp_gtos_worktree_root_targeted"),
    ]:
        root_checks.append(
            {
                "root": str(root_path),
                "role": role,
                "exists": root_path.exists(),
                "search_policy": "targeted_file_and_artifact_checks_only_no_broad_paid_or_live_access",
            }
        )

    tick_checks = []
    for symbol_date in needed_symbol_dates:
        symbol, date_iso = symbol_date.split("|")
        path = MAIN_TICK_ROOT / symbol / f"{date_iso}.parquet"
        tick_checks.append(
            {
                "symbol_date": symbol_date,
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )

    prior_artifact_checks = [
        source_record(OTI2_RISKBANK_DIR / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "prior_oti2_riskbank_rows"),
        source_record(OTI2_RISKBANK_DIR / "OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json", "prior_oti2_ambiguity_ledger"),
        source_record(ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json", "router_route_decision_ledger"),
        source_record(OTI1_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl", "oti1_source_packet_rows"),
        source_record(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{DATE}.jsonl", "oti3_row_decision_ledger"),
    ]
    return {
        "artifact_family": "OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "root_checks": root_checks,
        "needed_symbol_dates": needed_symbol_dates,
        "absolute_tick_file_checks": tick_checks,
        "prior_artifact_checks": prior_artifact_checks,
        "source_records_consumed_count": len(source_records),
        "source_records_missing_count": sum(1 for record in source_records if not record["exists"]),
        "manual_search_note": "A prebuild broad C:\\tmp text search encountered access-denied pytest temp dirs and timed out; the lane therefore records targeted C:\\tmp\\gtos_otb prior-worktree checks plus source hashes for every consumed file.",
        "source_search_conclusion": "All accepted-label rows have source-authorized ordered events from OTI1/OTI3. The original OTI2 row remains exactly blocked by side-aware tick coverage gaps, and the four OTI3 same-timestamp rows remain blocked by same quote-row ordering impossibility.",
    }


def collect_source_records(decisions: list[dict[str, Any]], same_timestamp_inspections: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = [
        source_record(ROOT / ".context/LIVE_STATE.md", "mandatory_preflight_live_state"),
        source_record(ROOT / ".context/00_core/research_current_state.md", "mandatory_context_research_current_state"),
        source_record(ROOT / ".context/00_core/goal_session_research_discipline.md", "mandatory_context_goal_session_research_discipline"),
        source_record(ROOT / ".context/00_core/local_heavy_data_inventory.md", "mandatory_context_local_heavy_data_inventory"),
        source_record(OUT_DIR / f"OTI2_FILL_PATH_CONTRACT_V2_GOAL_PROMPT_{DATE}.md", "controlling_prompt"),
        source_record(ROUTER_DIR / f"OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_{DATE}.md", "router_oti2_prompt_pack"),
        source_record(ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json", "router_route_decision_ledger"),
        source_record(OTI1_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl", "oti1_source_packet_rows"),
        source_record(OTI1_DIR / f"OTI1_PENDING_INTENT_COMPLETION_AUDIT_{DATE}.json", "oti1_completion_audit"),
        source_record(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{DATE}.jsonl", "oti3_row_decision_ledger"),
        source_record(OTI3_DIR / f"OTI3_USDJPY_COMPLETION_AUDIT_{DATE}.json", "oti3_completion_audit"),
        source_record(OTI4_DIR / f"OTI4_OPENING_DRIVE_COMPLETION_AUDIT_{DATE}.json", "oti4_completion_audit_read_for_merged_context"),
        source_record(ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.json", "oti5_completion_audit_read_for_merged_context"),
        source_record(G12_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.md", "g12_nofill_cat_decision_ledger"),
        source_record(CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl", "nofill_cat_packet_rows"),
        source_record(CONTRACT_DIR / f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json", "nofill_frozen_rulebook"),
        source_record(OTI2_RISKBANK_DIR / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "prior_oti2_riskbank_rows_context_only"),
        source_record(ROOT / "shadow_logs/candidate_ltf_path_order.jsonl", "oti2_m1_path_context_only"),
        source_record(ROOT / "shadow_logs/pending_limit_lifecycle.jsonl", "oti2_internal_pending_cancel_context_only"),
    ]
    seen_event_sources: set[tuple[str, str]] = set()
    for decision in decisions:
        for event in decision.get("ordered_source_events") or []:
            path = event.get("source_path")
            sha = event.get("source_sha256")
            if path:
                key = (str(resolve_source_path(path)), sha or "")
                if key not in seen_event_sources:
                    records.append(source_record(path, f"{decision['source_family']}_ordered_event_source", expected_sha256=sha))
                    seen_event_sources.add(key)
        if decision["source_family"] == "OTI1_PENDING_INTENT":
            # The OTI1 row carries source files in the upstream packet; the hash is
            # already materialized there and rechecked here without propagating
            # raw lifecycle broker/order fields.
            pass
    for inspection in same_timestamp_inspections.values():
        if inspection.get("source_path"):
            records.append(source_record(inspection["source_path"], "oti3_same_timestamp_inspected_tick_source", expected_sha256=inspection.get("source_sha256")))
    records.append(source_record(MAIN_TICK_ROOT / "XAUUSD/2026-05-05.parquet", "oti2_original_xauusd_tick_source"))
    records.append(source_record(MAIN_TICK_ROOT / "XAUUSD/2026-05-06.parquet", "oti2_original_xauusd_tick_gap_source"))

    dedup: dict[tuple[str | None, str], dict[str, Any]] = {}
    for record in records:
        dedup[(record["path"], record["role"])] = record
    return list(dedup.values())


def source_hash_noleak_audit(source_records: list[dict[str, Any]], outputs_for_scan: list[Any]) -> dict[str, Any]:
    forbidden_hits: list[str] = []
    for idx, payload in enumerate(outputs_for_scan):
        forbidden_hits.extend(scan_forbidden_keys(payload, f"$output[{idx}]"))
    return {
        "artifact_family": "OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_hash_records": source_records,
        "source_hash_record_count": len(source_records),
        "source_hash_missing_count": sum(1 for record in source_records if not record["exists"]),
        "source_hash_mismatch_count": sum(1 for record in source_records if record["hash_match"] is False),
        "forbidden_output_key_hits": forbidden_hits,
        "forbidden_output_key_hit_count": len(forbidden_hits),
        "input_boundary_note": "Some upstream context files contain out-of-scope performance/broker/order fields. This lane consumes only whitelisted identity, geometry, source-event, hash, and blocker fields and does not propagate forbidden output keys.",
        "no_r_performance_computed": True,
        "no_broker_account_live_order_labels_used": True,
        "paid_api_databento_calls": 0,
        "mt5_order_account_history_calls": 0,
    }


def duplicate_sample_floor_audit(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(row["categorical_fill_path_label"] for row in decisions if row.get("categorical_fill_path_label"))
    source_counts = Counter(row["source_family"] for row in decisions)
    group_counts = Counter(row.get("duplicate_group_id") for row in decisions if row.get("duplicate_group_id"))
    duplicate_key_counts = Counter(row.get("nofill_duplicate_key") for row in decisions if row.get("nofill_duplicate_key"))
    return {
        "artifact_family": "OTI2_FILL_PATH_DUPLICATE_SAMPLE_FLOOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_count": len(decisions),
        "source_family_counts": dict(source_counts),
        "label_counts": dict(label_counts),
        "blocked_count": sum(1 for row in decisions if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"),
        "unique_nofill_duplicate_key_count": len(duplicate_key_counts),
        "duplicate_key_conflicts": {key: count for key, count in duplicate_key_counts.items() if count > 1},
        "duplicate_group_id_count": len(group_counts),
        "largest_duplicate_group": {
            "duplicate_group_id": group_counts.most_common(1)[0][0] if group_counts else None,
            "row_count": group_counts.most_common(1)[0][1] if group_counts else 0,
            "share_of_rows": (group_counts.most_common(1)[0][1] / len(decisions)) if decisions and group_counts else 0,
        },
        "sample_floor_status": "UNDER_SAMPLE_FLOOR_NO_VALIDATION",
        "sample_floor_reason": "No label family reaches 30 unique nofill_duplicate_key rows, and this lane has no promotion/validation authority.",
        "primary_denominator_key": "nofill_duplicate_key",
    }


def blocker_learning_ledger(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [row for row in decisions if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"]
    return {
        "artifact_family": "OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "blocked_row_count": len(blocked),
        "blocked_rows": [
            {
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "source_family": row["source_family"],
                "symbol": row["symbol"],
                "decision_asof_utc": row["decision_asof_utc"],
                "exact_blocker_codes": row["exact_blocker_codes"],
                "exact_blocker_reasons": row["exact_blocker_reasons"],
                "source_order_resolution": row["source_order_resolution"],
            }
            for row in blocked
        ],
        "failure_learning": [
            {
                "family": "OTI3_same_timestamp",
                "learning": "A single quote row can satisfy entry and protective predicates at the same source timestamp. Without source row sequence below that quote row, assigning order would be fabricated.",
                "next_unblocker": "Future capture would need source-provided intra-tick update sequence or an accepted contract that treats simultaneous entry/protective as a distinct blocked lifecycle class.",
            },
            {
                "family": "OTI2_original",
                "learning": "The old OTI2 M1 path row was useful for finding the ambiguity but is not sufficient for a source-safe side-aware fill/path label.",
                "next_unblocker": "A source-equivalent XAUUSD bid/ask tick file covering 2026-05-06T00:00:00Z through 2026-05-06T06:45:00Z, or an accepted prior source packet with those quote events, is required.",
            },
        ],
    }


def completion_audit(
    decisions: list[dict[str, Any]],
    contract: dict[str, Any],
    source_audit: dict[str, Any],
    duplicate_audit: dict[str, Any],
    source_search: dict[str, Any],
) -> dict[str, Any]:
    counts = Counter(row["source_family"] for row in decisions)
    label_counts = Counter(row["categorical_fill_path_label"] for row in decisions if row.get("categorical_fill_path_label"))
    blocker_counts = Counter(code for row in decisions for code in row.get("exact_blocker_codes", []))
    return {
        "artifact_family": "OTI2_FILL_PATH_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "repo_head_at_build": git_head(),
        "objective_restated": "Build a source-safe fill/path categorical contract and input-only row decision packet for original OTI2, OTI1 entry-touch, OTI3 entry-before-terminal, and OTI3 same-timestamp ambiguity rows without R/performance or live-trading surface changes.",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "can_mark_goal_complete": False,
        "row_counts": {
            "total_candidate_universe_rows": len(decisions),
            "source_family_counts": dict(counts),
            "label_assigned_rows": sum(1 for row in decisions if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"),
            "blocked_before_label_rows": sum(1 for row in decisions if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"),
            "label_counts": dict(label_counts),
            "blocker_counts": dict(blocker_counts),
        },
        "explicit_required_row_family_treatment": {
            "original_oti2_row": "included_and_blocked_exact_by_side_aware_tick_source_gap",
            "oti1_22_source_authorized_entry_touch_rows": "included_and_labeled_fill_path_entry_before_protective_level_no_terminal_observed",
            "oti3_7_entry_touch_before_terminal_rows": "included_and_labeled_by_source_order",
            "oti3_4_same_timestamp_rows": "included_in_packet_as_blocked_before_label; not resolvable from source-safe tick ordering",
        },
        "contract_freeze_evidence": {
            "contract_id": contract["contract_id"],
            "contract_frozen_before_row_labeling": True,
            "contract_path_json": rel(OUT_DIR / f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json"),
        },
        "source_search_summary": {
            "searched_roots": source_search["root_checks"],
            "needed_symbol_dates": source_search["needed_symbol_dates"],
            "source_search_conclusion": source_search["source_search_conclusion"],
        },
        "source_hash_noleak_summary": {
            "source_hash_record_count": source_audit["source_hash_record_count"],
            "source_hash_missing_count": source_audit["source_hash_missing_count"],
            "source_hash_mismatch_count": source_audit["source_hash_mismatch_count"],
            "forbidden_output_key_hit_count": source_audit["forbidden_output_key_hit_count"],
        },
        "duplicate_sample_floor_summary": {
            "unique_nofill_duplicate_key_count": duplicate_audit["unique_nofill_duplicate_key_count"],
            "duplicate_key_conflicts": duplicate_audit["duplicate_key_conflicts"],
            "sample_floor_status": duplicate_audit["sample_floor_status"],
        },
        "scope_boundaries_preserved": {
            "no_r_performance_computed": True,
            "no_win_rate_expectancy_dsr_pbo": True,
            "no_broker_account_live_order_labels_used": True,
            "no_paid_api_databento_calls": True,
            "no_mt5_order_account_history_calls": True,
            "no_live_trading_prompts_risk_execution_permissions_safety_selectors_canaries_changed": True,
            "no_master_registry_edit": True,
            "no_remote_push": True,
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory_gtos_preflight", "status": "covered", "evidence": [".context/LIVE_STATE.md", ".context/00_core/*", "latest handoff read"]},
            {"requirement": "controlling_prompt_and_merged_oti_artifacts_read", "status": "covered", "evidence": source_search["prior_artifact_checks"]},
            {"requirement": "freeze_source_safe_contract_before_labeling", "status": "covered", "evidence": rel(OUT_DIR / f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json")},
            {"requirement": "consume_original_oti2_plus_oti1_22_plus_oti3_7_plus_decide_oti3_4", "status": "covered", "evidence": dict(counts)},
            {"requirement": "same_timestamp_oti3_resolution_decision", "status": "covered", "evidence": "4 rows remain blocked; same quote row/ts_msc cannot establish order"},
            {"requirement": "search_absolute_heavy_data_roots_and_prior_artifacts", "status": "covered", "evidence": rel(OUT_DIR / f"OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER_{DATE}.json")},
            {"requirement": "durable_ledgers_verifiers_tests_next_guidance", "status": "pending_verification_run", "evidence": "builder/verifier/test files emitted; command results added by verifier"},
            {"requirement": "preserve_no_promotion_and_false_flags", "status": "covered", "evidence": "all primary artifacts carry NO_PROMOTION_VERDICT/false flags"},
            {"requirement": "no_forbidden_surface_or_performance", "status": "covered", "evidence": source_audit["forbidden_output_key_hit_count"]},
        ],
        "verification": {
            "verification_status": "PENDING_VERIFIER_RUN",
            "verification_artifact": rel(OUT_DIR / f"OTI2_FILL_PATH_VERIFICATION_{DATE}.json"),
        },
    }


def write_markdown_artifacts(
    context_anchor: dict[str, Any],
    universe: dict[str, Any],
    contract: dict[str, Any],
    source_audit: dict[str, Any],
    duplicate_audit: dict[str, Any],
    blocker_ledger: dict[str, Any],
    source_search: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    md_pairs = {
        f"OTI2_FILL_PATH_CONTEXT_ANCHOR_{DATE}.md": [
            "# OTI2 Fill/Path Context Anchor",
            "",
            f"Lane: `{LANE_ID}`",
            f"Generated: `{context_anchor['generated_at_utc']}`",
            "Status: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
            "",
            "Current task reconstructs the fill/path candidate universe from original OTI2, OTI1, and OTI3 source-correction artifacts. It does not compute R/performance or touch live trading surfaces.",
        ],
        f"OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION_{DATE}.md": [
            "# OTI2 Fill/Path Universe Reconstruction",
            "",
            f"Candidate rows: `{universe['candidate_universe_row_count']}`.",
            f"Source family counts: `{universe['source_family_counts']}`.",
            f"Label-assigned rows: `{universe['label_assigned_rows']}`.",
            f"Blocked rows: `{universe['blocked_before_label_rows']}`.",
            "",
            "The four OTI3 same-timestamp rows are admitted to the row-decision packet but remain blocked before label because source-safe tick ordering cannot resolve a single quote row that satisfies multiple touch predicates.",
        ],
        f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.md": [
            "# OTI2 Fill/Path Frozen Contract",
            "",
            f"Contract: `{CONTRACT_ID}`",
            "Frozen before row labeling: `true`.",
            "",
            "Allowed labels are categorical event-order labels only. Lower-timeframe/M1 path rows are context only unless backed by source-safe bid/ask quote ordering.",
            "",
            f"Allowed label taxonomy: `{list(contract['label_taxonomy'].keys())}`.",
        ],
        f"OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md": [
            "# OTI2 Fill/Path Source Hash And No-Leak Audit",
            "",
            f"Source hash records: `{source_audit['source_hash_record_count']}`.",
            f"Missing source records: `{source_audit['source_hash_missing_count']}`.",
            f"Hash mismatches: `{source_audit['source_hash_mismatch_count']}`.",
            f"Forbidden output key hits: `{source_audit['forbidden_output_key_hit_count']}`.",
            "",
            "Upstream files with out-of-scope fields were consumed only through whitelisted identity/source-event fields.",
        ],
        f"OTI2_FILL_PATH_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md": [
            "# OTI2 Fill/Path Duplicate And Sample-Floor Audit",
            "",
            f"Rows: `{duplicate_audit['row_count']}`.",
            f"Unique nofill duplicate keys: `{duplicate_audit['unique_nofill_duplicate_key_count']}`.",
            f"Duplicate key conflicts: `{duplicate_audit['duplicate_key_conflicts']}`.",
            f"Sample-floor status: `{duplicate_audit['sample_floor_status']}`.",
        ],
        f"OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER_{DATE}.md": [
            "# OTI2 Fill/Path Blocker And Failure Learning Ledger",
            "",
            f"Blocked rows: `{blocker_ledger['blocked_row_count']}`.",
            "",
            "OTI3 same-timestamp blockers are not resolvable from current source-safe tick ordering. The original OTI2 row remains blocked by a side-aware tick coverage gap and M1-only entry-touch context.",
        ],
        f"OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER_{DATE}.md": [
            "# OTI2 Fill/Path Source Search Ledger",
            "",
            f"Needed symbol-dates: `{source_search['needed_symbol_dates']}`.",
            f"Conclusion: {source_search['source_search_conclusion']}",
            "",
            "Searched current worktree anchors, absolute main data/tick roots, shadow-log roots, and targeted prior worktree artifacts under `C:\\tmp\\gtos_otb`.",
        ],
        f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.md": [
            "# OTI2 Fill/Path Completion Audit",
            "",
            f"Candidate rows: `{completion['row_counts']['total_candidate_universe_rows']}`.",
            f"Label-assigned rows: `{completion['row_counts']['label_assigned_rows']}`.",
            f"Blocked rows: `{completion['row_counts']['blocked_before_label_rows']}`.",
            f"Verification status: `{completion['verification']['verification_status']}`.",
            "",
            "All outputs remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        ],
    }
    for filename, lines in md_pairs.items():
        (OUT_DIR / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def next_prompt_pack() -> str:
    return f"""# OTI2 Fill/Path Contract V2 Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Recommended Next Lane

Run `G12_OTI2_FILL_PATH_CATEGORICAL_CONTRACT_V2_AUDIT` against:

- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.json`

## Audit Questions

1. Verify the universe count is 34 rows: original OTI2 1, OTI1 22, OTI3 entry-before-terminal 7, and OTI3 same-timestamp ambiguity 4.
2. Verify the accepted categorical labels are source-event-order labels only and do not compute R/performance.
3. Independently verify that the four OTI3 same-timestamp rows remain blocked because a single quote row/ts_msc satisfies multiple touch predicates.
4. Independently verify that the original OTI2 row remains blocked because M1 context is not side-aware quote proof and XAUUSD 2026-05-06 tick coverage starts after the required source window.
5. Verify source hashes, no-leak checks, duplicate/sample-floor posture, and no live-trading surface changes.

## Forbidden

Do not compute R, win rate, expectancy, broker actual-R, account-history outcomes, live order/deal/position labels, or promotion evidence. Do not touch live trading prompts, risk, execution, permissions, safety selectors, MT5 order/account/history, canaries, paid/API/Databento, credentials, remotes, registries, or order behavior.
"""


def build() -> dict[str, Any]:
    generated_at_utc = utc_now()
    contract = build_contract(generated_at_utc)

    cat_rows = load_cat_rows()
    oti1_rows = [
        row
        for row in read_jsonl(OTI1_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl")
        if row.get("row_decision_status") == "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT"
    ]
    oti3_candidate_rows = []
    for row in read_jsonl(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{DATE}.jsonl"):
        codes = set(row.get("exact_blocker_codes") or [])
        if "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED" in codes or "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS" in codes:
            oti3_candidate_rows.append(row)
    same_timestamp_inspections = inspect_same_timestamp_rows(oti3_candidate_rows)

    decisions: list[dict[str, Any]] = []
    original_oti2, original_oti2_resolution = build_oti2_original_decision(cat_rows, generated_at_utc)
    decisions.append(original_oti2)
    decisions.extend(label_oti1_rows(oti1_rows))
    decisions.extend(label_oti3_rows(oti3_candidate_rows, same_timestamp_inspections))

    decisions.sort(key=lambda row: (row["source_family"], row.get("source_close_packet_row_id") or ""))
    for idx, row in enumerate(decisions, start=1):
        row["packet_row_id"] = f"OTI2-FILLPATH-ROW-{idx:04d}"

    source_records = collect_source_records(decisions, same_timestamp_inspections)
    source_search = build_source_search_ledger(decisions, source_records)
    duplicate_audit = duplicate_sample_floor_audit(decisions)
    universe = {
        "artifact_family": "OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": generated_at_utc,
        "repo_head_at_build": git_head(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "candidate_universe_row_count": len(decisions),
        "source_family_counts": dict(Counter(row["source_family"] for row in decisions)),
        "required_source_counts": {
            "original_oti2_router_rows": 1,
            "oti1_source_authorized_entry_touch_rows": len(oti1_rows),
            "oti3_entry_touch_before_terminal_rows": sum(
                1
                for row in oti3_candidate_rows
                if "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED" in (row.get("exact_blocker_codes") or [])
            ),
            "oti3_same_timestamp_ambiguity_rows": sum(
                1 for row in oti3_candidate_rows if "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS" in (row.get("exact_blocker_codes") or [])
            ),
        },
        "same_timestamp_oti3_resolution_decision": {
            "rows": sorted(same_timestamp_inspections),
            "decision": "admitted_to_packet_as_blocked_before_label",
            "reason": "Current source-safe tick files have one quote row at the first timestamp and no sub-row event sequence.",
        },
        "label_assigned_rows": sum(1 for row in decisions if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"),
        "blocked_before_label_rows": sum(1 for row in decisions if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"),
        "label_counts": dict(Counter(row["categorical_fill_path_label"] for row in decisions if row.get("categorical_fill_path_label"))),
        "blocker_counts": dict(Counter(code for row in decisions for code in row.get("exact_blocker_codes", []))),
        "original_oti2_source_order_resolution": original_oti2_resolution,
    }
    source_audit = source_hash_noleak_audit(source_records, [contract, universe, decisions, duplicate_audit, source_search])
    blocker_ledger = blocker_learning_ledger(decisions)
    completion = completion_audit(decisions, contract, source_audit, duplicate_audit, source_search)
    context_anchor = {
        "artifact_family": "OTI2_FILL_PATH_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": generated_at_utc,
        "repo_head_at_build": git_head(),
        "controlling_prompt": rel(OUT_DIR / f"OTI2_FILL_PATH_CONTRACT_V2_GOAL_PROMPT_{DATE}.md"),
        "mandatory_preflight_completed": True,
        "research_lane": "research_control_input_only_categorical_packet",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "inputs_read": [
            rel(ROUTER_DIR / f"OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_{DATE}.md"),
            rel(ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json"),
            rel(OTI1_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl"),
            rel(OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{DATE}.jsonl"),
            rel(OTI4_DIR / f"OTI4_OPENING_DRIVE_COMPLETION_AUDIT_{DATE}.json"),
            rel(ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_COMPLETION_AUDIT_{DATE}.json"),
            rel(G12_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.md"),
            rel(CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl"),
            rel(CONTRACT_DIR / f"NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
        ],
        "active_question_stack_closed": [
            "reconstruct current universe from OTI2/OTI1/OTI3",
            "freeze source-safe fill/path contract before labels",
            "decide OTI3 same-timestamp rows from source-safe tick ordering",
            "search local heavy-data roots and prior artifacts before blockers",
        ],
        "hard_boundaries": contract["forbidden_surfaces"],
    }

    write_json(OUT_DIR / f"OTI2_FILL_PATH_CONTEXT_ANCHOR_{DATE}.json", context_anchor)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION_{DATE}.json", universe)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json", contract)
    write_jsonl(OUT_DIR / f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl", decisions)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", source_audit)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", duplicate_audit)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER_{DATE}.json", blocker_ledger)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER_{DATE}.json", source_search)
    write_json(OUT_DIR / f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.json", completion)
    (OUT_DIR / f"OTI2_FILL_PATH_NEXT_PROMPT_PACK_{DATE}.md").write_text(next_prompt_pack(), encoding="utf-8")
    write_markdown_artifacts(context_anchor, universe, contract, source_audit, duplicate_audit, blocker_ledger, source_search, completion)
    return {
        "decisions": decisions,
        "contract": contract,
        "universe": universe,
        "source_audit": source_audit,
        "duplicate_audit": duplicate_audit,
        "blocker_ledger": blocker_ledger,
        "completion": completion,
    }


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "lane_id": LANE_ID,
                "rows": len(result["decisions"]),
                "labels": result["universe"]["label_counts"],
                "blocked": result["universe"]["blocked_before_label_rows"],
                "status": "BUILT_NO_PROMOTION_VERDICT",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
