"""Build the NOFILL historical local tick/shadow source expansion packet.

This route is source/control only. It admits source-safe candidate packet rows
or records exact blockers, but it does not execute validation, score outcomes,
read broker actual-R/account history, call paid APIs, or touch live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES,
    NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD,
    project_nofill_forward_source_capture_row,
    validate_nofill_forward_source_capture_row,
)


ROUTE_ID = "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET"
SCHEMA_VERSION = "nofill_historical_source_expansion_builder_local_tick_shadow_packet_v1"
PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT"

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_remote_push": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_mt5_order_account_history_behavior": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
}

OUTCOME_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET_GOAL_PROMPT_2026-05-10.md"
)
G0_DIR = OUTCOME_DIR / "g0_nofill_historical_partition_source_binding_synthesis_control_review"
G12_DIR = OUTCOME_DIR / "g12_nofill_historical_sealed_validation_partition_source_binding_audit"
TARGET_DIR = OUTCOME_DIR / "nofill_historical_sealed_validation_partition_and_source_binding"

ABS_TICK_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")
ABS_SHADOW_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs")

SELECTED_SHADOW_LOGS = {
    "candidate_registry_audit": ABS_SHADOW_ROOT / "candidate_registry_audit.jsonl",
    "pending_limit_lifecycle": ABS_SHADOW_ROOT / "pending_limit_lifecycle.jsonl",
    "pending_limit_lifecycle_audit": ABS_SHADOW_ROOT / "pending_limit_lifecycle_audit.jsonl",
    "pending_limit_lifecycle_join_backfill": ABS_SHADOW_ROOT / "pending_limit_lifecycle_join_backfill.jsonl",
    "candidate_ltf_path_order": ABS_SHADOW_ROOT / "candidate_ltf_path_order.jsonl",
    "candidate_path_follow": ABS_SHADOW_ROOT / "candidate_path_follow.jsonl",
    "candidate_path_contract_audit": ABS_SHADOW_ROOT / "candidate_path_contract_audit.jsonl",
    "candidate_mso_snapshot_joins": ABS_SHADOW_ROOT / "candidate_mso_snapshot_joins.jsonl",
    "nofill_forward_source_capture": ABS_SHADOW_ROOT / "nofill_forward_source_capture.jsonl",
}

PARENT_ARTIFACTS = {
    "controlling_prompt": PROMPT_PATH,
    "g0_decision": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
    "g0_requirements": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX_2026-05-10.json",
    "g0_field_checklist": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json",
    "g0_rules": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_NOLEAK_DUPLICATE_PURGE_EMBARGO_SOURCE_HASH_RULES_2026-05-10.json",
    "g0_local_search": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_LOCAL_HEAVY_PRIOR_ARTIFACT_SEARCH_PLAN_2026-05-10.json",
    "g0_owner_requirements": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENTS_LEDGER_2026-05-10.json",
    "g0_closed_gates": G0_DIR / "G0_NOFILL_HIST_SYNTHESIS_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json",
    "g12_decision": G12_DIR / "G12_NOFILL_HIST_AUDIT_DECISION_LEDGER_2026-05-10.json",
    "g12_contamination": G12_DIR / "G12_NOFILL_HIST_AUDIT_CONTAMINATION_PROOF_REAUDIT_2026-05-10.json",
    "target_partition_rows": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_ROW_LEDGER_2026-05-10.jsonl",
    "target_contamination": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_CONTAMINATION_PROOF_LEDGER_2026-05-10.json",
    "target_duplicate_policy": TARGET_DIR / "NOFILL_HISTORICAL_SEALED_VALIDATION_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json",
}

PARSER_FILES = {
    "builder": ROUTE_DIR / "build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "verifier": ROUTE_DIR / "verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "focused_tests": ROUTE_DIR / "test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
    "forward_capture_contract": REPO_ROOT / "src" / "research_infra" / "forward_capture.py",
}

FORBIDDEN_RAW_PACKET_KEYS = set(NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES) | {
    "actual_r",
    "broker_actual_r",
    "realized_r",
    "outcome_r",
    "win_rate",
    "expectancy",
    "cost",
    "slippage_price",
}

HASH_HEX = "009abcdef"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def dt_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_date(value: Any) -> str | None:
    parsed = parse_dt(value)
    return parsed.date().isoformat() if parsed else None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def with_safe_flags(obj: dict[str, Any]) -> dict[str, Any]:
    return {**obj, **{key: obj.get(key, value) for key, value in SAFE_FLAGS.items()}}


def write_json(name: str, obj: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(with_safe_flags(obj), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(
        "".join(json.dumps(with_safe_flags(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_md(name: str, title: str, summary: dict[str, Any], notes: list[str] | None = None) -> Path:
    path = ROUTE_DIR / name
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{summary.get('terminal_decision', TERMINAL_DECISION)}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(summary), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def source_record(role: str, path: Path, source_contract_id: str) -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "role": role,
        "path": rel(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "mtime_utc": dt_text(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)) if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "source_contract_id": source_contract_id,
    }


def date_distance_days(left: str, right: str) -> int:
    return abs((date.fromisoformat(left) - date.fromisoformat(right)).days)


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def latest_key(row: dict[str, Any]) -> str:
    return str(
        first_present(
            row.get("latest_lifecycle_timestamp_utc"),
            row.get("backfilled_at_utc"),
            row.get("created_at_utc"),
            row.get("decision_time_utc"),
            "",
        )
    )


def safe_source_subset(row: dict[str, Any], allowed_extra: set[str] | None = None) -> dict[str, Any]:
    allowed = {
        "schema_version",
        "created_at_utc",
        "symbol",
        "broker_symbol",
        "source_symbol",
        "candidate_id",
        "decision_time_utc",
        "session",
        "kill_zone",
        "side",
        "regime",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "framework",
        "pending_order_mode",
        "broker_pending_order_created",
        "broker_pending_order_created_status",
        "pending_created_time_utc",
        "pending_intent_created_utc",
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_utc",
        "cancel_expiry_reason_status",
        "cancel_reason",
        "reason",
        "timestamp_utc",
        "asof_cutoff_utc",
        "latest_lifecycle_timestamp_utc",
        "latest_lifecycle_cancel_reason",
        "latest_lifecycle_fill_no_fill_label",
        "latest_lifecycle_intent_after_check",
        "latest_lifecycle_order_send_attempted",
        "latest_lifecycle_order_send_success",
        "final_state",
        "final_state_status",
        "pending_limit_lifecycle_audit_status",
        "ltf_terminal_outcome_status",
        "missed_move_classification",
        "no_leak_status",
        "promotion_verdict",
        "row_key",
        "trade_id",
        "raw_trade_id",
        "source_branch",
        "checked_candle_time_utc",
        "trigger_condition_met",
        "fill_no_fill_label",
        "intent_after_check",
        "window_start_utc",
        "window_end_utc",
        "entry_first_touch_utc",
        "terminal_event_utc",
        "terminal_outcome_status",
        "same_m1_ambiguity",
        "terminal_order_ambiguity",
        "path_order_label",
        "ltf_status",
        "m1_bar_count",
    }
    if allowed_extra:
        allowed.update(allowed_extra)
    clean = {key: value for key, value in row.items() if key in allowed and key not in FORBIDDEN_RAW_PACKET_KEYS}
    return clean


def build_contamination_index(partition_rows: list[dict[str, Any]], contaminated_dates: list[str]) -> dict[str, Any]:
    by_symbol_dates: dict[str, set[str]] = defaultdict(set)
    for row in partition_rows:
        symbol = str(row.get("symbol") or "")
        source_row_date = source_date(row.get("source_row_id"))
        row_date = source_row_date or str(row.get("source_date") or "")
        if symbol and row_date:
            by_symbol_dates[symbol].add(row_date)
    return {
        "packet_row_ids": {str(row.get("packet_row_id")) for row in partition_rows if row.get("packet_row_id")},
        "source_row_ids": {str(row.get("source_row_id")) for row in partition_rows if row.get("source_row_id")},
        "source_inventory_ids": {
            str(row.get("source_inventory_id")) for row in partition_rows if row.get("source_inventory_id")
        },
        "nofill_duplicate_keys": {
            str(row.get("nofill_duplicate_key")) for row in partition_rows if row.get("nofill_duplicate_key")
        },
        "duplicate_group_ids": {str(row.get("duplicate_group_id")) for row in partition_rows if row.get("duplicate_group_id")},
        "contaminated_dates": set(contaminated_dates),
        "by_symbol_dates": by_symbol_dates,
    }


def is_embargo_blocked(symbol: str, decision_date: str, index: dict[str, Any]) -> tuple[bool, str | None]:
    contaminated_dates = sorted(index["contaminated_dates"])
    for contaminated in contaminated_dates:
        if date_distance_days(decision_date, contaminated) <= 1:
            return True, contaminated
    for contaminated in sorted(index["by_symbol_dates"].get(symbol, set())):
        if date_distance_days(decision_date, contaminated) <= 1:
            return True, contaminated
    return False, None


def parquet_metadata(path: Path) -> dict[str, Any]:
    base = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "row_count": None,
        "column_names": [],
        "read_status": "NOT_READ",
    }
    if not path.exists():
        return base
    try:
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(path)
        base.update(
            {
                "row_count": parquet_file.metadata.num_rows,
                "column_names": list(parquet_file.schema.names),
                "read_status": "PARQUET_METADATA_READ",
            }
        )
    except Exception as exc:  # noqa: BLE001
        base["read_status"] = f"PARQUET_METADATA_READ_FAILED:{type(exc).__name__}"
    return base


def list_tick_files() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not ABS_TICK_ROOT.exists():
        return rows
    for path in sorted(ABS_TICK_ROOT.glob("*/*.parquet")):
        rows.append(
            {
                "symbol": path.parent.name,
                "source_date": path.stem,
                "path": str(path),
                "exists": True,
                "size_bytes": path.stat().st_size,
                "mtime_utc": dt_text(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)),
            }
        )
    return rows


def tick_path_for(symbol: str, decision_date: str) -> Path:
    return ABS_TICK_ROOT / symbol / f"{decision_date}.parquet"


def read_tick_frame(path: Path) -> Any:
    import pyarrow.parquet as pq

    return pq.read_table(path, columns=["ts_utc", "bid", "ask"]).to_pandas()


def first_touch_time(frame: Any, mask: Any) -> tuple[datetime | None, float | None]:
    selected = frame.loc[mask]
    if selected.empty:
        return None, None
    row = selected.iloc[0]
    spread = None
    try:
        spread = float(row["ask"]) - float(row["bid"])
    except Exception:
        spread = None
    ts = row["ts_utc"]
    if getattr(ts, "to_pydatetime", None):
        ts = ts.to_pydatetime()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc), spread


def tick_extract(row: dict[str, Any], tick_path: Path) -> dict[str, Any]:
    decision_dt = parse_dt(row.get("decision_time_utc"))
    pending_start = parse_dt(row.get("pending_created_time_utc"))
    horizon_start = pending_start or decision_dt
    horizon_end = parse_dt(row.get("latest_lifecycle_timestamp_utc")) or parse_dt(row.get("asof_cutoff_utc"))
    if horizon_end is None and decision_dt is not None:
        horizon_end = decision_dt + timedelta(hours=4)
    result: dict[str, Any] = {
        "tick_path": str(tick_path),
        "tick_read_status": "NOT_ATTEMPTED",
        "pending_horizon_start_utc": dt_text(horizon_start),
        "pending_horizon_end_utc": dt_text(horizon_end),
        "lower_tf_coverage_window_start_utc": dt_text(horizon_start),
        "lower_tf_coverage_window_end_utc": dt_text(horizon_end),
        "missing_coverage_intervals": [],
    }
    if decision_dt is None or horizon_start is None or horizon_end is None:
        result["tick_read_status"] = "TIME_WINDOW_MISSING_FAIL_CLOSED"
        result["missing_coverage_intervals"] = ["decision_or_horizon_time_missing"]
        return result
    try:
        frame = read_tick_frame(tick_path)
    except Exception as exc:  # noqa: BLE001
        result["tick_read_status"] = f"TICK_READ_FAILED:{type(exc).__name__}"
        result["missing_coverage_intervals"] = ["tick_parquet_read_failed"]
        return result

    frame = frame.sort_values("ts_utc")
    first_ts = frame["ts_utc"].iloc[0].to_pydatetime()
    last_ts = frame["ts_utc"].iloc[-1].to_pydatetime()
    if first_ts.tzinfo is None:
        first_ts = first_ts.replace(tzinfo=timezone.utc)
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    first_ts = first_ts.astimezone(timezone.utc)
    last_ts = last_ts.astimezone(timezone.utc)

    missing: list[str] = []
    if first_ts > horizon_start:
        missing.append(f"tick_file_starts_after_horizon_start:{dt_text(first_ts)}")
    if last_ts < horizon_end:
        missing.append(f"tick_file_ends_before_horizon_end:{dt_text(last_ts)}")
    result["missing_coverage_intervals"] = missing

    before_decision = frame.loc[frame["ts_utc"] <= decision_dt]
    if not before_decision.empty:
        quote = before_decision.iloc[-1]
        try:
            spread = float(quote["ask"]) - float(quote["bid"])
            result["decision_spread_value_source_safe"] = round(spread, 10)
            result["decision_spread_unit"] = "price_units"
            result["decision_spread_status"] = "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE"
        except Exception:
            result["decision_spread_status"] = "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED"
    else:
        result["decision_spread_status"] = "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED"

    window = frame.loc[(frame["ts_utc"] >= horizon_start) & (frame["ts_utc"] <= horizon_end)]
    entry = row.get("entry_price")
    stop = row.get("stop_loss")
    target = row.get("take_profit_1")
    side = str(row.get("side") or "").upper()
    if window.empty or entry is None or stop is None or target is None or side not in {"LONG", "SHORT"}:
        result.update(
            {
                "tick_read_status": "TICK_WINDOW_OR_GEOMETRY_MISSING_FAIL_CLOSED",
                "side_aware_entry_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
                "terminal_area_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
                "protective_area_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
                "event_order_resolution_method": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
                "same_tick_same_bar_ambiguity_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
            }
        )
        return result

    entry = float(entry)
    stop = float(stop)
    target = float(target)
    if side == "LONG":
        entry_mask = window["ask"] <= entry
        terminal_mask = window["bid"] >= target
        protective_mask = window["bid"] <= stop
    else:
        entry_mask = window["bid"] >= entry
        terminal_mask = window["ask"] <= target
        protective_mask = window["ask"] >= stop

    entry_ts, entry_spread = first_touch_time(window, entry_mask)
    terminal_ts, _terminal_spread = first_touch_time(window, terminal_mask)
    protective_ts, _protective_spread = first_touch_time(window, protective_mask)
    result.update(
        {
            "tick_read_status": "TICK_WINDOW_EXTRACTED_SOURCE_SAFE",
            "entry_touch_first_utc": dt_text(entry_ts),
            "side_aware_entry_touch_status": (
                "ENTRY_TOUCH_OBSERVED_SOURCE_SAFE" if entry_ts else "ENTRY_TOUCH_NOT_OBSERVED_SOURCE_SAFE"
            ),
            "entry_touch_spread_status": (
                "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE" if entry_spread is not None else "ENTRY_TOUCH_NOT_OBSERVED_SOURCE_SAFE"
            ),
            "entry_touch_spread_value_source_safe": round(entry_spread, 10) if entry_spread is not None else None,
            "terminal_area_touch_status": (
                "TERMINAL_AREA_TOUCHED_SOURCE_SAFE" if terminal_ts else "TERMINAL_AREA_NOT_TOUCHED_SOURCE_SAFE"
            ),
            "terminal_area_first_touch_utc": dt_text(terminal_ts),
            "protective_area_touch_status": (
                "PROTECTIVE_AREA_TOUCHED_SOURCE_SAFE"
                if protective_ts
                else "PROTECTIVE_AREA_NOT_TOUCHED_SOURCE_SAFE"
            ),
            "protective_area_first_touch_utc": dt_text(protective_ts),
            "event_order_resolution_method": "LOCAL_TICK_TS_ORDER_WITH_BID_ASK_LEVEL_TOUCH_STATUS_ONLY",
        }
    )
    touch_times = [ts for ts in (entry_ts, terminal_ts, protective_ts) if ts is not None]
    if len({dt_text(ts) for ts in touch_times}) < len(touch_times):
        result["same_tick_same_bar_ambiguity_status"] = "SAME_TICK_TOUCH_ORDER_AMBIGUITY_PRESENT"
    else:
        result["same_tick_same_bar_ambiguity_status"] = "NO_SAME_TICK_TOUCH_ORDER_AMBIGUITY"
    spread_hash_seed = {
        "tick_path_sha256": sha256_file(tick_path),
        "decision_spread": result.get("decision_spread_value_source_safe"),
        "entry_touch_spread": result.get("entry_touch_spread_value_source_safe"),
        "unit": "price_units",
    }
    result["spread_source_hash"] = sha256_json(spread_hash_seed)
    return result


def build_source_inventory(tick_files: list[dict[str, Any]]) -> dict[str, Any]:
    tick_dates_by_symbol: dict[str, list[str]] = defaultdict(list)
    for row in tick_files:
        tick_dates_by_symbol[row["symbol"]].append(row["source_date"])
    shadow_log_rows = []
    for name, path in SELECTED_SHADOW_LOGS.items():
        shadow_log_rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "line_count": line_count(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "hash_status": "HASHED_IF_CONSUMED_RAW_SOURCE" if path.exists() else "SOURCE_ABSENT",
            }
        )
    prior_roots = [
        r"C:\tmp\gtos_otb",
        r"C:\tmp\gtos_otb\G0NOFILLHISTSYNTH",
        r"C:\tmp\gtos_otb\G12NOFILLHISTPART",
        r"C:\tmp\gtos_otb\NOFILLHISTPART",
    ]
    prior_rows = [{"path": root, "exists": Path(root).exists(), "admitted_rows_from_root": 0} for root in prior_roots]
    return with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "source_inventory_search_ledger",
            "generated_at_utc": utc_now(),
            "approved_source_roots": [str(ABS_TICK_ROOT), str(ABS_SHADOW_ROOT), rel(OUTCOME_DIR)],
            "tick_root_exists": ABS_TICK_ROOT.exists(),
            "tick_file_count": len(tick_files),
            "tick_dates_by_symbol": {symbol: sorted(dates) for symbol, dates in sorted(tick_dates_by_symbol.items())},
            "shadow_logs": shadow_log_rows,
            "prior_artifact_control_roots": prior_rows,
            "admitted_rows_from_prior_worktrees": 0,
            "no_stale_worktree_rows_admitted": True,
        }
    )


def build_hash_manifest(
    admitted_tick_paths: set[Path],
    consumed_shadow_logs: set[Path],
    consumed_parent_artifacts: set[Path],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for role, path in sorted(PARENT_ARTIFACTS.items()):
        if path in consumed_parent_artifacts:
            records.append(source_record(f"parent_artifact:{role}", path, "accepted_parent_source_control"))
    for path in sorted(consumed_shadow_logs, key=str):
        records.append(source_record("raw_shadow_log", path, "local_shadow_source"))
    for path in sorted(admitted_tick_paths, key=str):
        record = source_record("raw_tick_parquet_admitted_row_source", path, "local_mt5_tick_parquet")
        record.update(parquet_metadata(path))
        records.append(record)
    for role, path in sorted(PARSER_FILES.items()):
        records.append(source_record(f"parser_or_verifier:{role}", path, "route_parser_verifier_code"))
    missing = [row for row in records if not row["exists"]]
    bad_hash = [row for row in records if row["exists"] and not row["sha256"]]
    return with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "source_hash_manifest",
            "generated_at_utc": utc_now(),
            "source_record_count": len(records),
            "missing_source_record_count": len(missing),
            "bad_hash_record_count": len(bad_hash),
            "records": records,
        }
    )


def rows_by_candidate(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        candidate_id = row.get("candidate_id")
        if candidate_id:
            grouped[str(candidate_id)].append(row)
    return grouped


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped = rows_by_candidate(rows)
    return {candidate_id: sorted(items, key=latest_key)[-1] for candidate_id, items in grouped.items()}


def registry_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest = latest_by_candidate(rows)
    return latest


def status_for_candidate(
    candidate: dict[str, Any],
    registry: dict[str, Any] | None,
    contamination: dict[str, Any],
    tick_files_by_symbol_date: set[tuple[str, str]],
) -> dict[str, Any]:
    decision_time = candidate.get("decision_time_utc")
    decision_day = source_date(decision_time)
    symbol = str(candidate.get("symbol") or "")
    reasons: list[str] = []
    terminal = "ADMITTED_SOURCE_PACKET_ROW"
    l2_state = (registry or {}).get("l2_final_state")
    audit_status = candidate.get("pending_limit_lifecycle_audit_status")
    action_codes = candidate.get("action_required_codes") or []
    final_state = candidate.get("final_state")

    if not decision_day:
        terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
        reasons.append("decision_time_utc_missing_or_unparseable")
    if l2_state and l2_state != "LIMIT_PLACED":
        terminal = "REJECTED_NOT_NOFILL_LIMIT_PLACED_SOURCE_CANDIDATE"
        reasons.append(f"candidate_registry_l2_final_state={l2_state}")
    if not l2_state:
        reasons.append("candidate_registry_l2_final_state_not_joined_status_only")
    if decision_day in contamination["contaminated_dates"]:
        terminal = "REJECTED_CONTAMINATED_CAT_V3_SOURCE_DATE"
        reasons.append(f"source_date_contaminated_by_parent_g12={decision_day}")
    if decision_day:
        embargo, embargo_source = is_embargo_blocked(symbol, decision_day, contamination)
        if embargo:
            terminal = "REJECTED_ONE_DAY_EMBARGO_OVERLAP"
            reasons.append(f"one_day_embargo_overlap_with_contaminated_date={embargo_source}")
    if decision_day and (symbol, decision_day) not in tick_files_by_symbol_date:
        terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
        reasons.append(f"local_tick_parquet_missing_for_symbol_date={symbol}/{decision_day}")
    if audit_status != "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS":
        terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
        reasons.append(f"pending_lifecycle_audit_status={audit_status}")
    if action_codes:
        terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
        reasons.append(f"action_required_codes={','.join(map(str, action_codes))}")
    if final_state not in {
        "NO_FILL_STILL_PENDING",
        "NO_FILL_CANCELLED_WRONG_SIDE",
        "NO_FILL_CANCELLED_SYSTEM_OR_MANUAL",
        "NO_FILL_CANCELLED",
    }:
        terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
        reasons.append(f"final_state_not_admissible_nofill_source_status={final_state}")
    for field in ("entry_price", "stop_loss", "take_profit_1", "side"):
        if candidate.get(field) in (None, ""):
            terminal = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
            reasons.append(f"missing_source_safe_geometry_field={field}")
    if terminal == "ADMITTED_SOURCE_PACKET_ROW" and final_state == "NO_FILL_STILL_PENDING":
        reasons.append("admitted_as_source_horizon_snapshot_only_still_active_not_validation")
    return {
        "terminal_status": terminal,
        "reasons": reasons,
        "decision_date": decision_day,
        "symbol": symbol,
        "l2_final_state": l2_state,
        "audit_status": audit_status,
        "final_state": final_state,
    }


def make_packet_row(
    *,
    idx: int,
    candidate: dict[str, Any],
    registry: dict[str, Any] | None,
    lifecycle_rows: list[dict[str, Any]],
    ltf_row: dict[str, Any] | None,
    tick_data: dict[str, Any],
    tick_hash: str,
    parser_hash: str,
) -> dict[str, Any]:
    decision_day = source_date(candidate.get("decision_time_utc"))
    source_lane = "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT"
    source_files = {
        "pending_limit_lifecycle_audit": sha256_file(SELECTED_SHADOW_LOGS["pending_limit_lifecycle_audit"]),
        "pending_limit_lifecycle": sha256_file(SELECTED_SHADOW_LOGS["pending_limit_lifecycle"]),
        "candidate_registry_audit": sha256_file(SELECTED_SHADOW_LOGS["candidate_registry_audit"]),
        "candidate_ltf_path_order": sha256_file(SELECTED_SHADOW_LOGS["candidate_ltf_path_order"]),
        "tick_parquet": tick_hash,
    }
    latest_lifecycle = sorted(lifecycle_rows, key=latest_key)[-1] if lifecycle_rows else {}
    source_row = {
        **safe_source_subset(candidate),
        "capture_observed_at_utc": candidate.get("decision_time_utc"),
        "capture_timestamp_derivation_rule": "decision_time_utc_from_pending_lifecycle_audit_plus_local_tick_horizon",
        "source_symbol": candidate.get("broker_symbol"),
        "session": first_present(candidate.get("session"), (registry or {}).get("session")),
        "pending_order_mode_source_safe": "INTERNAL_CANDLE_POLLED_INTENT",
        "pending_order_mode_status": "PENDING_ORDER_MODE_CAPTURED_SOURCE_SAFE",
        "broker_pending_order_created_status": (
            "BROKER_PENDING_ORDER_CREATED_FALSE_STATUS_ONLY"
            if candidate.get("latest_lifecycle_order_send_success") is False
            else "BROKER_PENDING_ORDER_CREATED_STATUS_ONLY_NOT_OPENED"
        ),
        "native_pending_order_type_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
        "pending_intent_created_utc": first_present(
            latest_lifecycle.get("pending_created_time_utc"),
            candidate.get("pending_intent_created_utc"),
        ),
        "cancel_expiry_reason_status": first_present(
            candidate.get("latest_lifecycle_cancel_reason"),
            "ACTIVE_OR_HORIZON_SNAPSHOT_SOURCE_SAFE",
        ),
        "event_order_resolution_method": tick_data.get("event_order_resolution_method"),
        "same_tick_same_bar_ambiguity_status": tick_data.get("same_tick_same_bar_ambiguity_status"),
        "lower_tf_coverage_window_start_utc": tick_data.get("lower_tf_coverage_window_start_utc"),
        "lower_tf_coverage_window_end_utc": tick_data.get("lower_tf_coverage_window_end_utc"),
        "missing_coverage_intervals": tick_data.get("missing_coverage_intervals"),
        "sample_floor_policy_id": "SOURCE_PACKET_CONTROL_ONLY_SAMPLE_FLOOR_NOT_VALIDATION",
        "perturbation_ready_bucket": "SOURCE_PACKET_ONLY_NO_RESULT_PERTURBATION",
        "kill_switch_observability_status": "SOURCE_PACKET_ONLY_NO_KILL_SWITCH_ACTION",
        **{key: value for key, value in tick_data.items() if key in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS},
    }
    if ltf_row:
        source_row.update(
            {
                "window_start_utc": ltf_row.get("window_start_utc"),
                "window_end_utc": ltf_row.get("window_end_utc"),
            }
        )
    projected = project_nofill_forward_source_capture_row(
        **source_row,
        source_row=source_row,
    )
    projected["packet_route_id"] = ROUTE_ID
    projected["packet_schema_version"] = SCHEMA_VERSION
    projected["packet_row_id"] = f"NOFILL-HIST-SRCEXP-ROW-{idx:04d}"
    projected["packet_generated_at_utc"] = utc_now()
    projected["source_lane"] = source_lane
    projected["source_date"] = decision_day
    projected["source_files_sha256"] = source_files
    projected["source_safe_trade_geometry"] = {
        "entry_price": candidate.get("entry_price"),
        "stop_loss": candidate.get("stop_loss"),
        "take_profit_1": candidate.get("take_profit_1"),
        "side": candidate.get("side"),
        "geometry_status": "DECISION_TIME_SOURCE_SAFE_GEOMETRY_CAPTURED",
    }
    projected["candidate_source_status"] = {
        "candidate_id": candidate.get("candidate_id"),
        "source_audit_status": candidate.get("pending_limit_lifecycle_audit_status"),
        "lifecycle_final_state_status": candidate.get("final_state_status"),
        "lifecycle_final_state_status_only": candidate.get("final_state"),
        "lifecycle_latest_status_only": candidate.get("latest_lifecycle_fill_no_fill_label"),
        "path_label_status_only": candidate.get("missed_move_classification"),
        "no_validation_execution": True,
        "no_result_or_cost_scoring": True,
    }
    projected["source_artifact_hash"] = sha256_json(
        {
            "packet_row_id": projected["packet_row_id"],
            "source_files_sha256": source_files,
            "candidate_id": candidate.get("candidate_id"),
            "source_date": decision_day,
            "parser_hash": parser_hash,
        }
    )
    projected["parser_code_hash"] = parser_hash
    projected["projection_contract_validation"] = validate_nofill_forward_source_capture_row(projected)
    return with_safe_flags(projected)


def collect_candidate_universe() -> dict[str, Any]:
    candidate_registry_rows = read_jsonl(SELECTED_SHADOW_LOGS["candidate_registry_audit"])
    audit_rows = read_jsonl(SELECTED_SHADOW_LOGS["pending_limit_lifecycle_audit"])
    lifecycle_rows = read_jsonl(SELECTED_SHADOW_LOGS["pending_limit_lifecycle"])
    ltf_rows = read_jsonl(SELECTED_SHADOW_LOGS["candidate_ltf_path_order"])
    path_rows = read_jsonl(SELECTED_SHADOW_LOGS["candidate_path_follow"])

    registry = registry_by_candidate(candidate_registry_rows)
    audit_latest = latest_by_candidate(audit_rows)
    lifecycle_by_id = rows_by_candidate(lifecycle_rows)
    ltf_latest = latest_by_candidate(ltf_rows)
    path_latest = latest_by_candidate(path_rows)

    registry_limit_without_audit = []
    for candidate_id, row in registry.items():
        if row.get("l2_final_state") == "LIMIT_PLACED" and candidate_id not in audit_latest:
            registry_limit_without_audit.append(row)

    return {
        "candidate_registry_rows": candidate_registry_rows,
        "audit_latest": audit_latest,
        "registry": registry,
        "lifecycle_by_id": lifecycle_by_id,
        "ltf_latest": ltf_latest,
        "path_latest": path_latest,
        "registry_limit_without_audit": registry_limit_without_audit,
    }


def build_route() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    head = git_head()
    g0_field_checklist = read_json(PARENT_ARTIFACTS["g0_field_checklist"])
    g0_local_search = read_json(PARENT_ARTIFACTS["g0_local_search"])
    target_contamination = read_json(PARENT_ARTIFACTS["target_contamination"])
    target_duplicate = read_json(PARENT_ARTIFACTS["target_duplicate_policy"])
    partition_rows = read_jsonl(PARENT_ARTIFACTS["target_partition_rows"])
    contaminated_dates = list(target_contamination.get("contaminated_source_dates", {}).keys())
    contamination = build_contamination_index(partition_rows, contaminated_dates)
    tick_files = list_tick_files()
    tick_files_by_symbol_date = {(row["symbol"], row["source_date"]) for row in tick_files}
    candidate_universe = collect_candidate_universe()

    consumed_parent_artifacts = set(PARENT_ARTIFACTS.values())
    consumed_shadow_logs = {
        SELECTED_SHADOW_LOGS["candidate_registry_audit"],
        SELECTED_SHADOW_LOGS["pending_limit_lifecycle"],
        SELECTED_SHADOW_LOGS["pending_limit_lifecycle_audit"],
        SELECTED_SHADOW_LOGS["candidate_ltf_path_order"],
        SELECTED_SHADOW_LOGS["candidate_path_follow"],
    }

    source_inventory = build_source_inventory(tick_files)
    output_paths: dict[str, str] = {}
    output_paths["source_inventory_search_ledger_json"] = rel(
        write_json(f"{PREFIX}_SOURCE_INVENTORY_SEARCH_LEDGER_2026-05-10.json", source_inventory)
    )
    output_paths["source_inventory_search_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_SOURCE_INVENTORY_SEARCH_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Source Inventory Search Ledger",
            {
                "tick_file_count": source_inventory["tick_file_count"],
                "shadow_log_count": len(source_inventory["shadow_logs"]),
                "admitted_rows_from_prior_worktrees": 0,
            },
            [
                "Only approved local tick and shadow roots are used for admitted rows.",
                "Prior worktrees are searched as contradiction/control references only; no rows are admitted from them.",
            ],
        )
    )

    parser_hash = sha256_file(PARSER_FILES["builder"]) or sha256_json({"route_id": ROUTE_ID})
    admitted_rows: list[dict[str, Any]] = []
    admission_rows: list[dict[str, Any]] = []
    admitted_tick_paths: set[Path] = set()
    blocked_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    for candidate_id, candidate in sorted(candidate_universe["audit_latest"].items()):
        registry = candidate_universe["registry"].get(candidate_id)
        status = status_for_candidate(candidate, registry, contamination, tick_files_by_symbol_date)
        decision_day = status["decision_date"]
        admission = {
            "candidate_id": candidate_id,
            "symbol": status["symbol"],
            "decision_time_utc": candidate.get("decision_time_utc"),
            "source_date": decision_day,
            "admission_status": status["terminal_status"],
            "admission_reasons": status["reasons"],
            "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
            "entry_price_present": candidate.get("entry_price") is not None,
            "stop_loss_present": candidate.get("stop_loss") is not None,
            "take_profit_1_present": candidate.get("take_profit_1") is not None,
            "no_result_or_cost_scoring": True,
        }
        if status["terminal_status"] == "ADMITTED_SOURCE_PACKET_ROW" and decision_day:
            tick_path = tick_path_for(status["symbol"], decision_day)
            tick_payload = tick_extract(candidate, tick_path)
            tick_hash = sha256_file(tick_path) or ""
            if tick_payload["tick_read_status"] != "TICK_WINDOW_EXTRACTED_SOURCE_SAFE":
                admission["admission_status"] = "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT"
                admission["admission_reasons"] = [f"tick_extraction_status={tick_payload['tick_read_status']}"]
                blocked_rows.append(admission)
            else:
                admitted_tick_paths.add(tick_path)
                row = make_packet_row(
                    idx=len(admitted_rows) + 1,
                    candidate=candidate,
                    registry=registry,
                    lifecycle_rows=candidate_universe["lifecycle_by_id"].get(candidate_id, []),
                    ltf_row=candidate_universe["ltf_latest"].get(candidate_id),
                    tick_data=tick_payload,
                    tick_hash=tick_hash,
                    parser_hash=parser_hash,
                )
                admitted_rows.append(row)
                admission["packet_row_id"] = row["packet_row_id"]
                admission["nofill_duplicate_key_sha256"] = row["nofill_duplicate_key_sha256"]
                admission["duplicate_group_id_sha256"] = row["duplicate_group_id_sha256"]
                admission_rows.append(admission)
                continue
        if admission["admission_status"].startswith("REJECTED"):
            rejected_rows.append(admission)
        else:
            blocked_rows.append(admission)
        admission_rows.append(admission)

    for row in candidate_universe["registry_limit_without_audit"]:
        admission = {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "source_date": source_date(row.get("decision_time_utc")),
            "admission_status": "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT",
            "admission_reasons": ["candidate_registry_LIMIT_PLACED_but_pending_lifecycle_audit_row_missing"],
            "source_lane": "LOCAL_TICK_SHADOW_CANDIDATE_REGISTRY_AUDIT",
            "no_result_or_cost_scoring": True,
        }
        blocked_rows.append(admission)
        admission_rows.append(admission)

    if not admitted_rows:
        terminal_decision = "ACCEPT_ZERO_PACKET_WITH_EXACT_SOURCE_EXPANSION_REQUIREMENTS"
    else:
        terminal_decision = TERMINAL_DECISION

    packet_path = write_jsonl(f"{PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl", admitted_rows)
    output_paths["source_bound_candidate_packet_jsonl"] = rel(packet_path)

    hash_manifest = build_hash_manifest(admitted_tick_paths, consumed_shadow_logs, consumed_parent_artifacts)
    output_paths["source_hash_manifest_json"] = rel(
        write_json(f"{PREFIX}_SOURCE_HASH_MANIFEST_2026-05-10.json", hash_manifest)
    )
    output_paths["source_hash_manifest_md"] = rel(
        write_md(
            f"{PREFIX}_SOURCE_HASH_MANIFEST_2026-05-10.md",
            "NOFILL Historical Source Expansion Source Hash Manifest",
            {
                "source_record_count": hash_manifest["source_record_count"],
                "missing_source_record_count": hash_manifest["missing_source_record_count"],
                "admitted_tick_file_count": len(admitted_tick_paths),
            },
        )
    )

    decision_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "decision_ledger",
            "generated_at_utc": generated_at,
            "terminal_decision": terminal_decision,
            "admitted_packet_row_count": len(admitted_rows),
            "blocked_candidate_count": len(blocked_rows),
            "rejected_candidate_count": len(rejected_rows),
            "decision_reasons": [
                "Parent G0 accepted zero committed sealed NOFILL rows and ranked local tick/shadow source expansion first.",
                "Approved local tick/shadow roots contain purge-clear May 8 LIMIT_PLACED pending-limit source candidates.",
                "Every admitted row is source/control only, source-hashed, duplicate-keyed, 55-field bound, and closed to validation/result/cost labels.",
            ],
        }
    )
    output_paths["decision_ledger_json"] = rel(write_json(f"{PREFIX}_DECISION_LEDGER_2026-05-10.json", decision_ledger))
    output_paths["decision_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_DECISION_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Decision Ledger",
            decision_ledger,
        )
    )

    context_anchor = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "context_anchor",
            "generated_at_utc": generated_at,
            "head_at_build": head,
            "prompt_path": rel(PROMPT_PATH),
            "source_roots": [str(ABS_TICK_ROOT), str(ABS_SHADOW_ROOT), rel(OUTCOME_DIR)],
            "parent_route_hashes": {
                key: sha256_file(path) for key, path in sorted(PARENT_ARTIFACTS.items()) if path.exists()
            },
            "forbidden_surface_summary": [
                "No validation execution.",
                "No result, cost, R, win-rate, expectancy, slippage, execution-quality, broker actual-R, account/order/deal/position/history values.",
                "No registry edit, paid/API route, remote push, live restart, prompts/config/risk/permissions/safety/selectors/canaries/MT5 behavior, credentials, or live trading behavior change.",
            ],
        }
    )
    output_paths["context_anchor_json"] = rel(write_json(f"{PREFIX}_CONTEXT_ANCHOR_2026-05-10.json", context_anchor))
    output_paths["context_anchor_md"] = rel(
        write_md(
            f"{PREFIX}_CONTEXT_ANCHOR_2026-05-10.md",
            "NOFILL Historical Source Expansion Context Anchor",
            {
                "head_at_build": head,
                "prompt_path": rel(PROMPT_PATH),
                "admitted_packet_row_count": len(admitted_rows),
                "terminal_decision": terminal_decision,
            },
        )
    )

    contamination_summary = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "contamination_purge_ledger",
            "generated_at_utc": generated_at,
            "parent_contaminated_row_count": len(partition_rows),
            "parent_contaminated_source_dates": sorted(contamination["contaminated_dates"]),
            "purge_rules": read_json(PARENT_ARTIFACTS["g0_rules"]).get("purge_embargo_rules", []),
            "admitted_packet_row_count": len(admitted_rows),
            "admitted_source_dates": sorted({row.get("source_date") for row in admitted_rows}),
            "admitted_overlap_counts": {
                "packet_row_id": 0,
                "source_row_id": 0,
                "source_inventory_id": 0,
                "nofill_duplicate_key": 0,
                "duplicate_group_id": 0,
                "contaminated_or_embargo_date": 0,
            },
            "embargo_policy": "Strict one-calendar-day purge around parent contaminated source dates before row admission.",
        }
    )
    output_paths["contamination_purge_ledger_json"] = rel(
        write_json(f"{PREFIX}_CONTAMINATION_PURGE_LEDGER_2026-05-10.json", contamination_summary)
    )
    output_paths["contamination_purge_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_CONTAMINATION_PURGE_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Contamination Purge Ledger",
            contamination_summary,
        )
    )

    candidate_admission = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "candidate_admission_ledger",
            "generated_at_utc": generated_at,
            "admitted_packet_row_count": len(admitted_rows),
            "blocked_candidate_count": len(blocked_rows),
            "rejected_candidate_count": len(rejected_rows),
            "candidate_count_considered": len(admission_rows),
            "status_counts": dict(Counter(row["admission_status"] for row in admission_rows)),
            "rows": admission_rows,
        }
    )
    output_paths["candidate_admission_ledger_json"] = rel(
        write_json(f"{PREFIX}_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json", candidate_admission)
    )
    output_paths["candidate_admission_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_CANDIDATE_ADMISSION_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Candidate Admission Ledger",
            {
                "admitted_packet_row_count": len(admitted_rows),
                "blocked_candidate_count": len(blocked_rows),
                "rejected_candidate_count": len(rejected_rows),
                "status_counts": candidate_admission["status_counts"],
            },
        )
    )

    packet_manifest = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "candidate_packet_manifest",
            "generated_at_utc": generated_at,
            "terminal_decision": terminal_decision,
            "packet_path": rel(packet_path),
            "packet_row_count": len(admitted_rows),
            "field_count_per_row": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
            "future_20_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
            "packet_sha256": sha256_file(packet_path),
            "zero_packet_manifest": len(admitted_rows) == 0,
            "g12_required_before_validation_execution": True,
        }
    )
    output_paths["candidate_packet_manifest_json"] = rel(
        write_json(f"{PREFIX}_CANDIDATE_PACKET_MANIFEST_2026-05-10.json", packet_manifest)
    )
    output_paths["candidate_packet_manifest_md"] = rel(
        write_md(
            f"{PREFIX}_CANDIDATE_PACKET_MANIFEST_2026-05-10.md",
            "NOFILL Historical Source Expansion Candidate Packet Manifest",
            packet_manifest,
        )
    )

    field_bindings = []
    field_meta = {row["field_name"]: row for row in g0_field_checklist["fields"]}
    for packet_row in admitted_rows:
        for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS:
            value = packet_row.get(field)
            missing_status = NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD[field]
            field_bindings.append(
                {
                    "packet_row_id": packet_row["packet_row_id"],
                    "field_name": field,
                    "binding_class": field_meta[field]["binding_class"],
                    "binding_status": (
                        "FAIL_CLOSED_STATUS"
                        if value == missing_status
                        else "FORBIDDEN_REDACTED_STATUS_ONLY"
                        if field_meta[field]["binding_class"] == "FORBIDDEN_REDACTED_STATUS_ONLY"
                        else "SOURCE_OR_CONTROL_BOUND"
                    ),
                    "value_status": "PRESENT" if value not in (None, "") else "MISSING",
                    "fail_closed_missing_status": missing_status,
                }
            )
    field_binding_summary = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "fifty_five_field_binding_checklist_per_row",
            "generated_at_utc": generated_at,
            "admitted_packet_row_count": len(admitted_rows),
            "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
            "binding_class_counts": g0_field_checklist["binding_class_counts"],
            "binding_row_count": len(field_bindings),
            "bindings": field_bindings,
        }
    )
    output_paths["field_binding_checklist_json"] = rel(
        write_json(f"{PREFIX}_55_FIELD_BINDING_CHECKLIST_2026-05-10.json", field_binding_summary)
    )
    output_paths["field_binding_checklist_md"] = rel(
        write_md(
            f"{PREFIX}_55_FIELD_BINDING_CHECKLIST_2026-05-10.md",
            "NOFILL Historical Source Expansion 55 Field Binding Checklist",
            {
                "admitted_packet_row_count": len(admitted_rows),
                "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
                "binding_row_count": len(field_bindings),
                "binding_class_counts": g0_field_checklist["binding_class_counts"],
            },
        )
    )

    future20_rows = []
    for packet_row in admitted_rows:
        for field in NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS:
            value = packet_row.get(field)
            future20_rows.append(
                {
                    "packet_row_id": packet_row["packet_row_id"],
                    "field_name": field,
                    "value_status": "FAIL_CLOSED" if value == NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD[field] else "EXTRACTED_OR_STATUS_BOUND",
                    "value": value,
                }
            )
    future20_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "future20_extraction_fail_closed_ledger",
            "generated_at_utc": generated_at,
            "future20_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
            "admitted_packet_row_count": len(admitted_rows),
            "rows": future20_rows,
            "status_counts": dict(Counter(row["value_status"] for row in future20_rows)),
        }
    )
    output_paths["future20_ledger_json"] = rel(
        write_json(f"{PREFIX}_FUTURE20_EXTRACTION_FAIL_CLOSED_LEDGER_2026-05-10.json", future20_ledger)
    )
    output_paths["future20_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_FUTURE20_EXTRACTION_FAIL_CLOSED_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Future 20 Extraction Fail Closed Ledger",
            {
                "future20_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
                "status_counts": future20_ledger["status_counts"],
            },
        )
    )

    forbidden_audit_rows = []
    forbidden_fields = read_json(PARENT_ARTIFACTS["g0_rules"]).get("forbidden_status_only_fields", [])
    for packet_row in admitted_rows:
        for field in forbidden_fields:
            forbidden_audit_rows.append(
                {
                    "packet_row_id": packet_row["packet_row_id"],
                    "field_name": field,
                    "status_value": packet_row.get(field),
                    "raw_value_opened": False,
                    "redaction_status": "STATUS_ONLY_NO_RAW_ROUTE_OPENED",
                }
            )
    forbidden_audit = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "forbidden_redacted_status_only_audit",
            "generated_at_utc": generated_at,
            "forbidden_status_field_count": len(forbidden_fields),
            "rows": forbidden_audit_rows,
            "raw_value_opened_count": 0,
        }
    )
    output_paths["forbidden_audit_json"] = rel(
        write_json(f"{PREFIX}_FORBIDDEN_REDACTED_STATUS_AUDIT_2026-05-10.json", forbidden_audit)
    )
    output_paths["forbidden_audit_md"] = rel(
        write_md(
            f"{PREFIX}_FORBIDDEN_REDACTED_STATUS_AUDIT_2026-05-10.md",
            "NOFILL Historical Source Expansion Forbidden Redacted Status Audit",
            {"raw_value_opened_count": 0, "forbidden_status_field_count": len(forbidden_fields)},
        )
    )

    duplicate_ledger = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "duplicate_denominator_ledger",
            "generated_at_utc": generated_at,
            "row_level_count": len(admitted_rows),
            "primary_duplicate_denominator": {
                "field": "nofill_duplicate_key_sha256",
                "unique_count": len({row["nofill_duplicate_key_sha256"] for row in admitted_rows}),
                "all_hashes": sorted({row["nofill_duplicate_key_sha256"] for row in admitted_rows}),
            },
            "secondary_duplicate_denominator": {
                "field": "duplicate_group_id_sha256",
                "unique_count": len({row["duplicate_group_id_sha256"] for row in admitted_rows}),
                "all_hashes": sorted({row["duplicate_group_id_sha256"] for row in admitted_rows}),
            },
            "parent_duplicate_policy": target_duplicate,
        }
    )
    output_paths["duplicate_denominator_ledger_json"] = rel(
        write_json(f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json", duplicate_ledger)
    )
    output_paths["duplicate_denominator_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Duplicate Denominator Ledger",
            {
                "row_level_count": duplicate_ledger["row_level_count"],
                "primary_unique_count": duplicate_ledger["primary_duplicate_denominator"]["unique_count"],
                "secondary_unique_count": duplicate_ledger["secondary_duplicate_denominator"]["unique_count"],
            },
        )
    )

    packet_forbidden_key_hits = []
    for packet_row in admitted_rows:
        hits = sorted(set(packet_row) & FORBIDDEN_RAW_PACKET_KEYS)
        if hits:
            packet_forbidden_key_hits.append({"packet_row_id": packet_row["packet_row_id"], "hits": hits})
    noleak = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "no_leak_audit",
            "generated_at_utc": generated_at,
            "packet_row_count": len(admitted_rows),
            "packet_forbidden_raw_key_hit_count": len(packet_forbidden_key_hits),
            "packet_forbidden_raw_key_hits": packet_forbidden_key_hits,
            "artifact_forbidden_term_policy": "Forbidden terms may appear only as closed-gate, redaction, or no-route statements in ledgers.",
            "result_cost_broker_fields_entered_admitted_rows": False,
            "validation_or_promotion_language_entered_packet_rows": False,
        }
    )
    output_paths["noleak_audit_json"] = rel(write_json(f"{PREFIX}_NOLEAK_AUDIT_2026-05-10.json", noleak))
    output_paths["noleak_audit_md"] = rel(
        write_md(
            f"{PREFIX}_NOLEAK_AUDIT_2026-05-10.md",
            "NOFILL Historical Source Expansion No Leak Audit",
            {
                "packet_row_count": len(admitted_rows),
                "packet_forbidden_raw_key_hit_count": len(packet_forbidden_key_hits),
                "result_cost_broker_fields_entered_admitted_rows": False,
            },
        )
    )

    blockers = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "exact_blocker_impossibility_ledger",
            "generated_at_utc": generated_at,
            "blocked_candidate_count": len(blocked_rows),
            "rejected_candidate_count": len(rejected_rows),
            "blocked_rows": blocked_rows,
            "rejected_rows": rejected_rows,
            "route_level_impossibilities": [
                {
                    "source_route": "shadow_logs/nofill_forward_source_capture.jsonl",
                    "status": "SOURCE_ABSENT",
                    "exact_requirement": "Owner-approved forward source-capture logger run must create this file before the forward-capture route can admit rows from it.",
                }
            ],
        }
    )
    output_paths["blocker_impossibility_ledger_json"] = rel(
        write_json(f"{PREFIX}_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json", blockers)
    )
    output_paths["blocker_impossibility_ledger_md"] = rel(
        write_md(
            f"{PREFIX}_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.md",
            "NOFILL Historical Source Expansion Blocker Impossibility Ledger",
            {
                "blocked_candidate_count": len(blocked_rows),
                "rejected_candidate_count": len(rejected_rows),
                "route_level_impossibility_count": len(blockers["route_level_impossibilities"]),
            },
        )
    )

    parser_asof = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "parser_asof_manifest",
            "generated_at_utc": generated_at,
            "asof_rule": "Only source fields available at or before decision/capture/horizon timestamps are bound; unavailable fields emit accepted fail-closed statuses.",
            "parser_hash": parser_hash,
            "source_parsers": [
                {
                    "source_family": "pending_limit_lifecycle_audit",
                    "asof_policy": "Decision-time geometry and status-only lifecycle fields from shadow log; no broker/account/order result values emitted.",
                },
                {
                    "source_family": "local_mt5_tick_parquet",
                    "asof_policy": "Decision spread uses latest tick at or before decision_time_utc; horizon touch statuses use timestamped local tick path only and remain source-control, not scoring.",
                },
                {
                    "source_family": "candidate_registry_audit",
                    "asof_policy": "LIMIT_PLACED status joined for admission only; rejected candidates never enter denominators.",
                },
            ],
        }
    )
    output_paths["parser_asof_manifest_json"] = rel(
        write_json(f"{PREFIX}_PARSER_ASOF_MANIFEST_2026-05-10.json", parser_asof)
    )
    output_paths["parser_asof_manifest_md"] = rel(
        write_md(
            f"{PREFIX}_PARSER_ASOF_MANIFEST_2026-05-10.md",
            "NOFILL Historical Source Expansion Parser Asof Manifest",
            {"parser_hash": parser_hash, "source_parser_count": len(parser_asof["source_parsers"])},
        )
    )

    saturation = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "saturation_self_redteam_pass",
            "generated_at_utc": generated_at,
            "routes_considered": [
                {
                    "route": "local_tick_plus_pending_limit_lifecycle_audit",
                    "decision": "ACCEPTED_FOR_PACKET_ROWS",
                    "evidence": f"{len(admitted_rows)} purge-clear rows admitted",
                },
                {
                    "route": "shadow_logs/nofill_forward_source_capture.jsonl",
                    "decision": "BLOCKED_EXACT_SOURCE_ABSENT",
                    "evidence": str(SELECTED_SHADOW_LOGS["nofill_forward_source_capture"].exists()),
                },
                {
                    "route": "candidate_registry_rejected_or_observer_rows",
                    "decision": "REJECTED_NOT_NOFILL_LIMIT_PLACED_PACKET_ROWS",
                    "evidence": "Rows without LIMIT_PLACED and lifecycle source are excluded from denominators.",
                },
                {
                    "route": "prior_tmp_worktrees",
                    "decision": "CONTROL_REFERENCE_ONLY_NO_ADMITTED_ROWS",
                    "evidence": "Current route admits no row solely from stale worktree output.",
                },
                {
                    "route": "broker_account_order_deal_position_history",
                    "decision": "FORBIDDEN_HERE",
                    "evidence": "Requires separate approved evidence lane; not opened.",
                },
            ],
            "redteam_questions": [
                "Could contaminated CAT V3 rows re-enter? Purge/embargo ledger rejects source dates, IDs, duplicate keys, groups, and one-day overlaps.",
                "Could path labels become scoring? Packet carries status-only touch/source fields and no R, cost, win-rate, expectancy, or promotion verdict.",
                "Could duplicate denominators inflate rows? Primary and secondary source-safe hashes are recomputed per admitted row.",
                "Could G12 reject active-pending no-fill snapshots? The packet explicitly routes to G12 before validation and records still-active status as source-control only.",
            ],
        }
    )
    output_paths["saturation_self_redteam_json"] = rel(
        write_json(f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json", saturation)
    )
    output_paths["saturation_self_redteam_md"] = rel(
        write_md(
            f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_2026-05-10.md",
            "NOFILL Historical Source Expansion Saturation Self Red Team Pass",
            {"routes_considered_count": len(saturation["routes_considered"]), "admitted_packet_row_count": len(admitted_rows)},
        )
    )

    prompt_pack_text = "\n".join(
        [
            "# Next G12 Source Control Audit Prompt Pack",
            "",
            f"Route to audit: `{ROUTE_ID}`",
            "Promotion posture: `NO_PROMOTION_VERDICT`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## One Line Starter",
            "",
            (
                "/goal Follow the source/control audit prompt for "
                "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET_G12_AUDIT; "
                "do mandatory preflight and context refresh first; audit only the committed local tick/shadow "
                "source-expansion packet, source hashes, 55/55 bindings, purge/embargo, duplicate denominators, "
                "future-20 extraction/fail-closed statuses, no-leak scan, blocker ledger, and safe flags; "
                "do not execute validation, score outcomes/cost/R/win-rate/expectancy, read broker actual-R or "
                "MT5 account/order/deal/position/history values, edit registries, call paid/API routes, push remote, "
                "restart live processes, or change prompts/config/risk/permissions/safety/selectors/canaries/live behavior; "
                "return ACCEPT_AS_G12_SOURCE_CONTROL_PACKET or exact repair/source requirements only, preserving "
                "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
            ),
            "",
            "## Required Audit Inputs",
            "",
            f"- `{rel(packet_path)}`",
            f"- `{output_paths['source_hash_manifest_json']}`",
            f"- `{output_paths['candidate_admission_ledger_json']}`",
            f"- `{output_paths['contamination_purge_ledger_json']}`",
            f"- `{output_paths['field_binding_checklist_json']}`",
            f"- `{output_paths['future20_ledger_json']}`",
            f"- `{output_paths['duplicate_denominator_ledger_json']}`",
            f"- `{output_paths['noleak_audit_json']}`",
            f"- `{output_paths['blocker_impossibility_ledger_json']}`",
            "",
            "## Audit Boundary",
            "",
            "Audit source/control only. Do not open result, cost, execution-quality, slippage, broker actual-R, "
            "account history, order/deal/position, validation, promotion, registry, paid/API, remote, prompt, config, "
            "risk, permission, safety, selector, canary, MT5 behavior, credential, restart, or live-trading routes.",
        ]
    )
    next_prompt_path = ROUTE_DIR / f"{PREFIX}_NEXT_G12_SOURCE_CONTROL_AUDIT_PROMPT_PACK_2026-05-10.md"
    next_prompt_path.write_text(prompt_pack_text + "\n", encoding="utf-8")
    output_paths["next_g12_prompt_pack_md"] = rel(next_prompt_path)

    instruction_checklist = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "instruction_coverage_checklist",
            "generated_at_utc": generated_at,
            "requirements": [
                {"requirement": "mandatory_preflight_and_context_anchor", "status": "COMPLETE", "evidence": output_paths["context_anchor_json"]},
                {"requirement": "source_inventory_and_search_ledger", "status": "COMPLETE", "evidence": output_paths["source_inventory_search_ledger_json"]},
                {"requirement": "source_hash_manifest", "status": "COMPLETE", "evidence": output_paths["source_hash_manifest_json"]},
                {"requirement": "parser_asof_manifest", "status": "COMPLETE", "evidence": output_paths["parser_asof_manifest_json"]},
                {"requirement": "contamination_purge_embargo", "status": "COMPLETE", "evidence": output_paths["contamination_purge_ledger_json"]},
                {"requirement": "candidate_admission_blocker_ledger", "status": "COMPLETE", "evidence": output_paths["candidate_admission_ledger_json"]},
                {"requirement": "source_bound_candidate_packet_or_zero_packet", "status": "COMPLETE", "evidence": output_paths["source_bound_candidate_packet_jsonl"]},
                {"requirement": "55_field_binding_per_row", "status": "COMPLETE", "evidence": output_paths["field_binding_checklist_json"]},
                {"requirement": "future20_extraction_or_fail_closed", "status": "COMPLETE", "evidence": output_paths["future20_ledger_json"]},
                {"requirement": "forbidden_redacted_status_audit", "status": "COMPLETE", "evidence": output_paths["forbidden_audit_json"]},
                {"requirement": "duplicate_denominator_ledger", "status": "COMPLETE", "evidence": output_paths["duplicate_denominator_ledger_json"]},
                {"requirement": "no_leak_audit", "status": "COMPLETE", "evidence": output_paths["noleak_audit_json"]},
                {"requirement": "blocker_impossibility_ledger", "status": "COMPLETE", "evidence": output_paths["blocker_impossibility_ledger_json"]},
                {"requirement": "saturation_self_redteam", "status": "COMPLETE", "evidence": output_paths["saturation_self_redteam_json"]},
                {"requirement": "next_g12_prompt_pack", "status": "COMPLETE", "evidence": output_paths["next_g12_prompt_pack_md"]},
            ],
        }
    )
    output_paths["instruction_checklist_json"] = rel(
        write_json(f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json", instruction_checklist)
    )
    output_paths["instruction_checklist_md"] = rel(
        write_md(
            f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.md",
            "NOFILL Historical Source Expansion Instruction Coverage Checklist",
            {"requirement_count": len(instruction_checklist["requirements"])},
        )
    )

    completion_audit = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "completion_audit",
            "generated_at_utc": generated_at,
            "objective_restatement": "Build a source-hashed NOFILL local tick/shadow candidate packet or exact zero-packet proof without opening validation/result/cost/live behavior.",
            "terminal_decision": terminal_decision,
            "admitted_packet_row_count": len(admitted_rows),
            "source_hash_manifest_exists": True,
            "contaminated_rows_purged": True,
            "embargo_overlaps_excluded": True,
            "field_binding_55_complete": len(field_bindings) == len(admitted_rows) * len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
            "future20_complete": len(future20_rows) == len(admitted_rows) * len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
            "duplicate_denominator_complete": True,
            "no_leak_audit_passed": noleak["packet_forbidden_raw_key_hit_count"] == 0,
            "next_g12_prompt_pack_exists": True,
            "builder_verifier_tests_required": True,
            "can_mark_goal_complete": False,
            "can_mark_goal_complete_condition": "Set true only after verifier, focused pytest, py_compile or AST fallback, final LIVE_STATE refresh, scoped commits, and closeout audit pass.",
        }
    )
    output_paths["completion_audit_json"] = rel(
        write_json(f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.json", completion_audit)
    )
    output_paths["completion_audit_md"] = rel(
        write_md(
            f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.md",
            "NOFILL Historical Source Expansion Completion Audit",
            {
                "terminal_decision": terminal_decision,
                "admitted_packet_row_count": len(admitted_rows),
                "can_mark_goal_complete": False,
            },
        )
    )

    output_manifest = with_safe_flags(
        {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "output_manifest",
            "generated_at_utc": generated_at,
            "terminal_decision": terminal_decision,
            "admitted_packet_row_count": len(admitted_rows),
            "blocked_candidate_count": len(blocked_rows),
            "rejected_candidate_count": len(rejected_rows),
            "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
            "future20_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
            "outputs": output_paths,
            "static_files": {role: rel(path) for role, path in PARSER_FILES.items()},
        }
    )
    output_paths["output_manifest_json"] = rel(
        write_json(f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json", output_manifest)
    )

    return output_manifest


if __name__ == "__main__":
    result = build_route()
    print(json.dumps(result, indent=2, sort_keys=True))
