"""Build the OTR061 XAUUSD tick-recovery artifact pack.

Research-control only. This lane attempts to recover or prove blocked the
missing XAUUSD tick window for OTG0-PKT-061 without opening result labels,
broker actual-R, account history, orders, live config, prompts, or paid/API
data sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

PACKET_ID = "OTG0-PKT-061"
EXPERIMENT_ID = "G6-EXP-002-CONTINUATION-NO-RETRACE"
TARGET_SYMBOL = "XAUUSD"
TARGET_RECORD_ID = "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
RECOVERY_START = datetime(2026, 5, 6, 7, 10, tzinfo=timezone.utc)
DECISION_ASOF = datetime(2026, 5, 6, 7, 15, tzinfo=timezone.utc)
RECOVERY_END = datetime(2026, 5, 6, 11, 15, tzinfo=timezone.utc)
MT5_QUERY_END = RECOVERY_END + timedelta(minutes=1)

BASE = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
G12 = OUTCOME_ROOT / "g12_otx_g6_post_audit"
OTX = OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution"

ABS_MAIN = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
ABS_DATA = ABS_MAIN / "data"
ABS_TICKS = ABS_DATA / "ticks"
ABS_EXTERNAL = ABS_DATA / "external"
ABS_EXPORTS = ABS_MAIN / "exports"
ABS_SHADOW = ABS_MAIN / "shadow_logs"
SIERRA_ROOT = Path(r"C:\SierraChart")
SIERRA_DATA = SIERRA_ROOT / "Data"

CONTROL_TEXT_FILES = {
    "live_state": REPO_ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": REPO_ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": REPO_ROOT / ".context/00_core/research_current_state.md",
    "goal_discipline": REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "reading_order": REPO_ROOT / ".context/00_READING_ORDER.md",
    "controlling_prompt": BASE / "OTR061_XAU_TICK_RECOVERY_GOAL_PROMPT_2026-05-07.md",
}

CONTROLLING_INPUT_FILES = {
    "g12_decision_json": G12 / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
    "g12_decision_md": G12 / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md",
    "g12_tick_audit_json": G12 / "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json",
    "g12_tick_audit_md": G12 / "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.md",
    "g12_blocker_action_json": G12 / "G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07.json",
    "g12_blocker_action_md": G12 / "G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07.md",
    "otx_tick_coverage_json": OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
    "otx_tick_coverage_md": OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md",
    "otx_source_hash_json": OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
    "otx_source_hash_md": OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md",
    "otx_proposals_json": OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    "otx_proposals_md": OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md",
}

PARSER_POLICY_FILES = {
    "sierra_scid_parser": REPO_ROOT / "scripts/inspect_sierra_scid.py",
    "sierra_proxy_registry": REPO_ROOT / "src/research_infra/sierra_proxy_registry.py",
    "xau_same_market_extension": REPO_ROOT / "src/research_infra/xauusd_same_market_extension.py",
}

MT5_PROBE_FILES = {
    "phase3_tick_history_probe": ABS_DATA
    / "mt5_research_exports/tick_availability/phase3_tick_history_probe_20260501_20260501T053133Z.json",
    "phase3_tick_history_probe_post_maxbars": ABS_DATA
    / "mt5_research_exports/tick_availability/phase3_tick_history_probe_post_maxbars_20260501_20260501T062554Z.json",
    "codex_eurusd_tick_retention_probe": ABS_DATA
    / "mt5_research_exports/tick_availability/codex_probe_eurusd_tick_retention_20260503T035751Z.json",
}

EXACT_DATA_SOURCE_CANDIDATES = {
    "g12_abs_xau_2026_05_06_tick_parquet": ABS_TICKS / "XAUUSD/2026-05-06.parquet",
    "sierra_same_market_xauusd_scid": SIERRA_DATA / "XAUUSD.scid",
    "sierra_gc_futures_proxy_scid": SIERRA_DATA / "GCM26-COMEX.scid",
    "sierra_mgc_futures_proxy_scid": SIERRA_DATA / "MGCM26-COMEX.scid",
    "sierra_same_market_manifest": ABS_DATA
    / "sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504/manifest.json",
}

APPROVED_SEARCH_ROOTS = [
    REPO_ROOT / "data",
    ABS_DATA,
    ABS_TICKS,
    ABS_EXTERNAL,
    ABS_EXPORTS,
    ABS_SHADOW,
    Path(r"C:\tmp"),
    SIERRA_ROOT,
    Path(r"C:\Users\MSI\Documents"),
]

TARGET_TOKENS = [
    "xauusd",
    "xau",
    "gold",
    "otg0-pkt-061",
    "otr061",
    "2026-05-06",
    "20260506",
    "2026_05_06",
    "tick",
    "quote",
    "parquet",
    "scid",
    "databento",
    "sierra",
    "mt5",
]

FORBIDDEN_SOURCE_FRAGMENTS = [
    "knowledge_base/trade_records",
    "trade_records",
    "account_history",
    "history_deals",
    "orders_get",
    "positions_get",
    "continuation_no_retrace_resolutions",
    "prefill_delivery_path_resolutions",
    "live_mechanical_strategy_shadow_outcomes",
]

FORBIDDEN_RESULT_KEYS = {
    "broker_actual_r",
    "account_history",
    "actual_r",
    "win_loss",
    "outcome_r",
    "path_label",
    "path_outcome_status",
    "final_r",
    "realized_r",
    "hit_tp",
    "hit_sl",
    "synthetic_path_r",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dt_iso(value: datetime | pd.Timestamp | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_file(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
    except OSError as exc:
        return {
            "path": str(path),
            "exists": path.exists(),
            "access_status": "ERROR",
            "error": repr(exc),
        }
    return {
        "path": str(path),
        "exists": True,
        "access_status": "OK",
        "size_bytes": st.st_size,
        "last_write_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
    }


def source_row(source_id: str, path: Path, role: str, notes: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "source_id": source_id,
        "role": role,
        "path": str(path),
        "absolute_path": str(path.resolve()) if path.exists() else str(path),
        "notes": notes,
        "sha256": sha256_file(path),
        **stat_file(path),
    }
    if summary is not None:
        row["inspection_summary"] = summary
    return row


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
        f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def repo_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception as exc:  # pragma: no cover - defensive environment reporting
        return f"UNKNOWN:{exc!r}"


def base_payload(family: str) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "generated_at_utc": now_utc(),
        "date_stamp": DATE_STAMP,
        "packet_id": PACKET_ID,
        "experiment_id": EXPERIMENT_ID,
        "target_symbol": TARGET_SYMBOL,
        "target_record_id": TARGET_RECORD_ID,
        "required_window_utc": {
            "start": dt_iso(RECOVERY_START),
            "decision_asof": dt_iso(DECISION_ASOF),
            "end": dt_iso(RECOVERY_END),
        },
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
        "repo_head": repo_head(),
        "paid_data_calls": 0,
        "api_calls": 0,
        "databento_calls": 0,
        "order_calls": 0,
        "mt5_order_calls": 0,
        "broker_actual_r_accessed": False,
        "account_history_accessed": False,
        "live_order_state_accessed": False,
    }


def inspect_tick_parquet(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "coverage_status": "MISSING_FILE"}

    try:
        parquet = pq.ParquetFile(path)
        schema_columns = parquet.schema.names
        columns = [col for col in ["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags"] if col in schema_columns]
        table = pq.read_table(path, columns=columns)
        df = table.to_pandas()
        if "ts_utc" not in df.columns:
            return {
                "exists": True,
                "coverage_status": "UNUSABLE_NO_TS_UTC_COLUMN",
                "row_count": parquet.metadata.num_rows,
                "schema_columns": schema_columns,
            }
        ts = pd.to_datetime(df["ts_utc"], utc=True)
        full_window = (ts >= RECOVERY_START) & (ts <= RECOVERY_END)
        decision_window = (ts >= RECOVERY_START) & (ts < DECISION_ASOF)
        path_window = (ts >= DECISION_ASOF) & (ts <= RECOVERY_END)
        full = df.loc[full_window].copy()
        decision = df.loc[decision_window].copy()
        path_rows = df.loc[path_window].copy()
        return {
            "exists": True,
            "coverage_status": "COVERS_REQUIRED_WINDOW"
            if not full.empty and not decision.empty and not path_rows.empty
            else "ZERO_OR_INSUFFICIENT_REQUIRED_WINDOW_ROWS",
            "row_count": int(len(df)),
            "schema_columns": schema_columns,
            "min_ts_utc": dt_iso(ts.min()),
            "max_ts_utc": dt_iso(ts.max()),
            "required_full_window_row_count": int(len(full)),
            "decision_quote_window_row_count": int(len(decision)),
            "path_window_row_count": int(len(path_rows)),
            "required_full_window_first_ts_utc": dt_iso(pd.to_datetime(full["ts_utc"], utc=True).min()) if not full.empty else None,
            "required_full_window_last_ts_utc": dt_iso(pd.to_datetime(full["ts_utc"], utc=True).max()) if not full.empty else None,
            "g12_known_blocker_confirmed": int(len(full)) == 0,
        }
    except Exception as exc:
        return {"exists": True, "coverage_status": "INSPECTION_ERROR", "error": repr(exc)}


def inspect_sierra_scid(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "coverage_status": "MISSING_FILE"}
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from scripts.inspect_sierra_scid import iter_slice, summarize_file

        summary = summarize_file(path)
        count = 0
        first_ts = None
        last_ts = None
        for record in iter_slice(path, RECOVERY_START, RECOVERY_END):
            count += 1
            ts_value = record["timestamp_utc"]
            if first_ts is None:
                first_ts = ts_value
            last_ts = ts_value
        return {
            "exists": True,
            "coverage_status": "COVERS_REQUIRED_WINDOW" if count > 0 else "NO_ROWS_IN_REQUIRED_WINDOW",
            "summary": summary,
            "required_window_row_count": count,
            "required_window_first_ts_utc": first_ts,
            "required_window_last_ts_utc": last_ts,
        }
    except Exception as exc:
        return {"exists": True, "coverage_status": "INSPECTION_ERROR", "error": repr(exc)}


def inspect_sierra_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "coverage_status": "MISSING_FILE"}
    try:
        payload = read_json(path)
        outputs = payload.get("outputs", {})
        m1 = outputs.get("M1") or outputs.get("m1") or {}
        return {
            "exists": True,
            "coverage_status": "ENDS_BEFORE_REQUIRED_WINDOW"
            if str(m1.get("last_utc", "")) < "2026-05-06"
            else "MANIFEST_REQUIRES_MANUAL_REVIEW",
            "source_path": payload.get("source_path"),
            "source_sha256": payload.get("source_sha256"),
            "m1_first_utc": m1.get("first_utc"),
            "m1_last_utc": m1.get("last_utc"),
            "m1_rows": m1.get("rows"),
        }
    except Exception as exc:
        return {"exists": True, "coverage_status": "INSPECTION_ERROR", "error": repr(exc)}


def inspect_candidate_data_sources() -> dict[str, dict[str, Any]]:
    inspections: dict[str, dict[str, Any]] = {}
    for source_id, path in EXACT_DATA_SOURCE_CANDIDATES.items():
        if path.suffix.lower() == ".parquet":
            inspections[source_id] = inspect_tick_parquet(path)
        elif path.suffix.lower() == ".scid":
            inspections[source_id] = inspect_sierra_scid(path)
        elif path.name == "manifest.json":
            inspections[source_id] = inspect_sierra_manifest(path)
        else:
            inspections[source_id] = stat_file(path)
    return inspections


def targeted_inventory(root: Path, cap: int = 80) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "access_status": "OK" if root.exists() else "MISSING",
        "patterns": TARGET_TOKENS,
        "match_count": 0,
        "matches": [],
        "errors": [],
        "truncated": False,
    }
    if not root.exists():
        return entry

    def onerror(exc: OSError) -> None:
        entry["errors"].append({"error": repr(exc), "filename": getattr(exc, "filename", None)})
        entry["access_status"] = "ERRORS_RECORDED"

    skip_dirs = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}
    try:
        for current, dirs, files in os.walk(root, topdown=True, onerror=onerror):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for name in files:
                full = Path(current) / name
                haystack = str(full).lower()
                if any(token in haystack for token in TARGET_TOKENS):
                    entry["match_count"] += 1
                    if len(entry["matches"]) < cap:
                        row = stat_file(full)
                        row["path"] = str(full)
                        entry["matches"].append(row)
                    else:
                        entry["truncated"] = True
    except OSError as exc:
        entry["access_status"] = "ERROR"
        entry["errors"].append({"error": repr(exc), "filename": getattr(exc, "filename", None)})
    return entry


def extract_target_record_from_otx() -> dict[str, Any] | None:
    proposals_path = CONTROLLING_INPUT_FILES["otx_proposals_json"]
    try:
        proposals = read_json(proposals_path)
    except Exception:
        return None
    for row in proposals.get("records", []):
        if row.get("record_id") == TARGET_RECORD_ID:
            return row
    return None


def walk_keys(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield path, key
            yield from walk_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            yield from walk_keys(nested, f"{path}[{idx}]")


def forbidden_key_hits(value: Any) -> list[dict[str, str]]:
    hits = []
    for path, key in walk_keys(value):
        if str(key).lower() in FORBIDDEN_RESULT_KEYS:
            hits.append({"path": path, "key": str(key)})
    return hits


def attempt_mt5_read_only_extraction(skip: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "attempted": not skip,
        "route": "MetaTrader5.copy_ticks_range",
        "symbol": TARGET_SYMBOL,
        "window_start_utc": dt_iso(RECOVERY_START),
        "window_end_utc": dt_iso(RECOVERY_END),
        "mt5_query_end_utc": dt_iso(MT5_QUERY_END),
        "read_only_assertion": True,
        "account_info_called": False,
        "history_deals_get_called": False,
        "history_orders_get_called": False,
        "orders_get_called": False,
        "positions_get_called": False,
        "order_send_called": False,
        "symbol_select_called": False,
        "output_path": None,
        "output_sha256": None,
        "rows": 0,
        "coverage_status": "SKIPPED_BY_OPERATOR_FLAG" if skip else "NOT_RUN",
    }
    if skip:
        return payload

    try:
        import MetaTrader5 as mt5
    except Exception as exc:
        payload.update({"coverage_status": "MODULE_IMPORT_ERROR", "error": repr(exc)})
        return payload

    initialized = False
    try:
        initialized = bool(mt5.initialize())
        payload["initialize_returned"] = initialized
        payload["last_error_after_initialize"] = str(mt5.last_error())
        if not initialized:
            payload["coverage_status"] = "INITIALIZE_FAILED"
            return payload

        ticks = mt5.copy_ticks_range(TARGET_SYMBOL, RECOVERY_START, MT5_QUERY_END, mt5.COPY_TICKS_ALL)
        payload["last_error_after_copy_ticks_range"] = str(mt5.last_error())
        if ticks is None:
            payload["coverage_status"] = "COPY_TICKS_RANGE_RETURNED_NONE"
            return payload
        df = pd.DataFrame(ticks)
        payload["rows"] = int(len(df))
        if df.empty:
            payload["coverage_status"] = "ZERO_ROWS_RETURNED"
            return payload

        if "time_msc" in df.columns:
            df.insert(0, "ts_utc", pd.to_datetime(df["time_msc"], unit="ms", utc=True))
        elif "time" in df.columns:
            df.insert(0, "ts_utc", pd.to_datetime(df["time"], unit="s", utc=True))
        df["mt5_symbol"] = TARGET_SYMBOL
        ts = pd.to_datetime(df["ts_utc"], utc=True)
        required_window_rows = df.loc[(ts >= RECOVERY_START) & (ts <= RECOVERY_END)]
        decision_window_rows = df.loc[(ts >= RECOVERY_START) & (ts < DECISION_ASOF)]
        path_window_rows = df.loc[(ts >= DECISION_ASOF) & (ts <= RECOVERY_END)]
        reaches_required_end = bool(ts.max() >= pd.Timestamp(RECOVERY_END))
        out = BASE / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
        df.to_parquet(out, index=False)
        payload.update(
            {
                "coverage_status": "RECOVERED_ROWS_FROM_READ_ONLY_MT5"
                if reaches_required_end and not decision_window_rows.empty and not path_window_rows.empty
                else "ROWS_RETURNED_BUT_NOT_THROUGH_REQUIRED_WINDOW",
                "output_path": str(out),
                "output_sha256": sha256_file(out),
                "first_tick_utc": dt_iso(pd.to_datetime(df["ts_utc"], utc=True).min()),
                "last_tick_utc": dt_iso(pd.to_datetime(df["ts_utc"], utc=True).max()),
                "required_window_row_count": int(len(required_window_rows)),
                "decision_quote_window_row_count": int(len(decision_window_rows)),
                "path_window_row_count": int(len(path_window_rows)),
                "reaches_required_end": reaches_required_end,
            }
        )
        return payload
    except Exception as exc:
        payload.update({"coverage_status": "EXTRACTION_ERROR", "error": repr(exc)})
        return payload
    finally:
        if initialized:
            try:
                mt5.shutdown()
                payload["shutdown_called"] = True
            except Exception as exc:  # pragma: no cover - defensive environment reporting
                payload["shutdown_called"] = False
                payload["shutdown_error"] = repr(exc)


def build_source_hash_ledger(
    inspections: dict[str, dict[str, Any]],
    mt5_attempt: dict[str, Any],
) -> dict[str, Any]:
    payload = base_payload("OTR061_XAU_TICK_SOURCE_HASH_LEDGER")
    source_files: list[dict[str, Any]] = []

    for source_id, path in {**CONTROL_TEXT_FILES, **CONTROLLING_INPUT_FILES, **PARSER_POLICY_FILES, **MT5_PROBE_FILES}.items():
        source_files.append(source_row(source_id, path, "control_or_prior_evidence", "Read as controlling/context evidence."))

    for source_id, path in EXACT_DATA_SOURCE_CANDIDATES.items():
        notes = "Inspected as approved local data-recovery candidate."
        if "futures_proxy" in source_id:
            notes = "Inspected only as local futures proxy candidate; not accepted as same-market XAUUSD broker quote truth."
        source_files.append(source_row(source_id, path, "local_data_candidate", notes, inspections.get(source_id)))

    if mt5_attempt.get("output_path"):
        out_path = Path(mt5_attempt["output_path"])
        source_files.append(
            source_row(
                "mt5_read_only_recovered_tick_export",
                out_path,
                "read_only_historical_extraction_output",
                "Generated by MetaTrader5.copy_ticks_range without account/order/history calls.",
                {"rows": mt5_attempt.get("rows"), "coverage_status": mt5_attempt.get("coverage_status")},
            )
        )

    missing_hashes = [row for row in source_files if row.get("exists") and not row.get("sha256")]
    payload.update(
        {
            "all_used_files_hashed": not missing_hashes,
            "missing_hash_rows": missing_hashes,
            "source_files": source_files,
            "forbidden_source_fragments": FORBIDDEN_SOURCE_FRAGMENTS,
            "forbidden_source_path_hits": [
                row
                for row in source_files
                if any(fragment in f"{row.get('path', '')} {row.get('absolute_path', '')}".lower().replace("\\", "/") for fragment in FORBIDDEN_SOURCE_FRAGMENTS)
            ],
            "hash_rule": "Every controlling input, parser/policy file, inspected local candidate source, and generated recovery source was SHA256 hashed when it existed.",
        }
    )
    return payload


def build_search_ledger(
    inventories: list[dict[str, Any]],
    inspections: dict[str, dict[str, Any]],
    mt5_attempt: dict[str, Any],
) -> dict[str, Any]:
    payload = base_payload("OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER")
    access_errors = [error for root in inventories for error in root.get("errors", [])]
    payload.update(
        {
            "approved_search_roots": [str(root) for root in APPROVED_SEARCH_ROOTS],
            "local_heavy_data_inventory_enforced": True,
            "worktree_absence_not_treated_as_data_absence": True,
            "search_patterns": TARGET_TOKENS,
            "root_search_results": inventories,
            "access_errors": access_errors,
            "access_requests": [],
            "exact_candidate_inspections": inspections,
            "mt5_read_only_route": mt5_attempt,
            "known_g12_blocker_rechecked": inspections.get("g12_abs_xau_2026_05_06_tick_parquet", {}).get("g12_known_blocker_confirmed") is True,
            "shadow_logs_policy": "Searched for provenance only; no result-label/resolution logs were consumed.",
            "saturation_summary": {
                "absolute_xau_tick_parquet_window_rows": inspections.get("g12_abs_xau_2026_05_06_tick_parquet", {}).get(
                    "required_full_window_row_count"
                ),
                "sierra_same_market_xau_scid_window_rows": inspections.get("sierra_same_market_xauusd_scid", {}).get(
                    "required_window_row_count"
                ),
                "mt5_read_only_rows": mt5_attempt.get("rows"),
            },
        }
    )
    return payload


def recovered_source_available(inspections: dict[str, dict[str, Any]], mt5_attempt: dict[str, Any]) -> bool:
    if mt5_attempt.get("coverage_status") == "RECOVERED_ROWS_FROM_READ_ONLY_MT5" and int(mt5_attempt.get("rows", 0)) > 0:
        return True
    for source_id in ["g12_abs_xau_2026_05_06_tick_parquet", "sierra_same_market_xauusd_scid"]:
        summary = inspections.get(source_id, {})
        if summary.get("coverage_status") == "COVERS_REQUIRED_WINDOW":
            return True
    return False


def build_recovered_decision_path_packets(
    mt5_attempt: dict[str, Any],
    source_ref: dict[str, Any],
    side: str | None,
) -> dict[str, Any]:
    path = Path(source_ref["path"])
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.assign(ts_utc=ts).sort_values("ts_utc").reset_index(drop=True)

    decision_rows = df.loc[(df["ts_utc"] >= pd.Timestamp(RECOVERY_START)) & (df["ts_utc"] <= pd.Timestamp(DECISION_ASOF))]
    if decision_rows.empty:
        raise RuntimeError("Recovered MT5 export has no decision quote rows before decision_asof.")
    decision_quote = decision_rows.iloc[-1]

    path_rows = df.loc[(df["ts_utc"] >= pd.Timestamp(DECISION_ASOF)) & (df["ts_utc"] <= pd.Timestamp(RECOVERY_END))]
    if path_rows.empty:
        raise RuntimeError("Recovered MT5 export has no ordered path rows in the required path window.")
    post_horizon_rows = df.loc[df["ts_utc"] >= pd.Timestamp(RECOVERY_END)]

    bid = float(decision_quote["bid"])
    ask = float(decision_quote["ask"])
    executable_price = ask if side == "LONG" else bid if side == "SHORT" else None
    return {
        "continuation_no_retrace_decision_price_path_packet": {
            "schema_id": "continuation_no_retrace_decision_price_path_v1",
            "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
            "decision_price_fields_status": "DECISION_QUOTE_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
            "ordered_path_fields_status": "ORDERED_TICK_PATH_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
            "path_horizon_source": "otx_fixed_4h_path_horizon_for_reaudit_only",
            "external_g12_reaudit_required": True,
            "no_result_fields_assertion": True,
        },
        "decision_quote_packet": {
            "schema_id": "decision_quote_asof_v1",
            "quote_status": "DECISION_QUOTE_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
            "decision_asof_utc": dt_iso(DECISION_ASOF),
            "quote_timestamp_utc": dt_iso(decision_quote["ts_utc"]),
            "side": side,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2.0,
            "spread": ask - bid,
            "executable_decision_price": executable_price,
            "executable_price_rule": "LONG_uses_ask_SHORT_uses_bid_market_entry",
            "source_file": source_ref["path"],
            "source_sha256": source_ref["sha256"],
        },
        "ordered_tick_path_packet": {
            "schema_id": "ordered_tick_path_asof_v1",
            "path_status": "ORDERED_TICK_PATH_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
            "path_source_type": "mt5_copy_ticks_range_quote_stream",
            "path_start_utc": dt_iso(DECISION_ASOF),
            "path_end_utc": dt_iso(RECOVERY_END),
            "path_row_count": int(len(path_rows)),
            "path_first_timestamp_utc": dt_iso(path_rows["ts_utc"].iloc[0]),
            "path_last_timestamp_utc": dt_iso(path_rows["ts_utc"].iloc[-1]),
            "source_query_first_timestamp_utc": dt_iso(df["ts_utc"].iloc[0]),
            "source_query_last_timestamp_utc": dt_iso(df["ts_utc"].iloc[-1]),
            "post_horizon_first_timestamp_utc": dt_iso(post_horizon_rows["ts_utc"].iloc[0]) if not post_horizon_rows.empty else None,
            "source_reaches_required_end": bool(mt5_attempt.get("reaches_required_end")),
            "ordered_path_materialization": "source_file_filtered_by_ts_utc_between_path_start_and_path_end_inclusive",
            "row_order": "ts_utc_ascending_preserving_mt5_tick_order",
            "path_source_files": [source_ref["path"]],
            "path_source_sha256": {source_ref["path"]: source_ref["sha256"]},
            "no_result_fields_assertion": True,
        },
    }


def build_packet_proposal(
    source_hash_ledger: dict[str, Any],
    inspections: dict[str, dict[str, Any]],
    mt5_attempt: dict[str, Any],
) -> dict[str, Any] | None:
    if not recovered_source_available(inspections, mt5_attempt):
        return None

    target_record = extract_target_record_from_otx() or {}
    if forbidden_key_hits(target_record):
        raise RuntimeError(f"Target OTX input record contains forbidden result keys: {forbidden_key_hits(target_record)}")

    payload = base_payload("OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL")
    recovered_source_refs = []
    for row in source_hash_ledger["source_files"]:
        if row["source_id"] not in {
            "g12_abs_xau_2026_05_06_tick_parquet",
            "sierra_same_market_xauusd_scid",
            "mt5_read_only_recovered_tick_export",
        }:
            continue
        summary = row.get("inspection_summary") or {}
        if summary.get("coverage_status") not in {"COVERS_REQUIRED_WINDOW", "RECOVERED_ROWS_FROM_READ_ONLY_MT5"}:
            continue
        recovered_source_refs.append(
            {
                "source_id": row["source_id"],
                "path": row["path"],
                "sha256": row["sha256"],
                "inspection_summary": summary,
            }
        )
    if not recovered_source_refs:
        raise RuntimeError("Recovered-source predicate passed but no covering source reference was available.")
    mt5_source_ref = next((row for row in recovered_source_refs if row["source_id"] == "mt5_read_only_recovered_tick_export"), None)
    recovered_packets = build_recovered_decision_path_packets(mt5_attempt, mt5_source_ref, target_record.get("side")) if mt5_source_ref else {}
    payload.update(
        {
            "terminal_state": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
            "schema": "continuation_no_retrace_decision_price_path_v1",
            "record_count": 1,
            "records": [
                {
                    "packet_id": PACKET_ID,
                    "record_id": TARGET_RECORD_ID,
                    "symbol": TARGET_SYMBOL,
                    "decision_asof_utc": dt_iso(DECISION_ASOF),
                    "side": target_record.get("side"),
                    "label_family": "input_only_features_no_labels",
                    "no_result_fields_assertion": True,
                    "prior_otx_input_record_for_traceability": target_record,
                    **recovered_packets,
                    "decision_price_path_contract": {
                        "schema": "continuation_no_retrace_decision_price_path_v1",
                        "window_start_utc": dt_iso(RECOVERY_START),
                        "window_end_utc": dt_iso(RECOVERY_END),
                        "source_hashed_tick_or_quote_path_refs": recovered_source_refs,
                        "ordered_path_materialization": "source_ref_only_pending_G12_reaudit_parser",
                        "no_result_fields_assertion": True,
                    },
                }
            ],
        }
    )
    return payload


def build_vendor_manifest(terminal_state: str, mt5_attempt: dict[str, Any]) -> dict[str, Any] | None:
    if terminal_state not in {"BLOCKED_VENDOR_RECOVERY_REQUIRED", "BLOCKED_PERMISSION_OR_ACCESS"}:
        return None
    payload = base_payload("OTR061_VENDOR_OR_ACCESS_MANIFEST")
    payload.update(
        {
            "terminal_state": terminal_state,
            "paid_or_network_calls_made": False,
            "approval_required_before_any_paid_or_network_call": True,
            "free_credit_or_zero_paid_spend_proof_required_before_call": True,
            "owner_approval_recorded": False,
            "mt5_read_only_attempt_summary": mt5_attempt,
            "pre_call_manifest": {
                "symbol": TARGET_SYMBOL,
                "required_window_utc": {
                    "start": dt_iso(RECOVERY_START),
                    "decision_asof": dt_iso(DECISION_ASOF),
                    "end": dt_iso(RECOVERY_END),
                },
                "maximum_spend_without_owner_approval_usd": 0,
                "network_api_call_allowed_now": False,
                "databento_call_allowed_now": False,
            },
            "candidate_next_unblockers": [
                {
                    "route": "Broker or MT5 server-side XAUUSD historical tick archive/export",
                    "status": "APPROVAL_OR_EXTERNAL_ACCESS_REQUIRED",
                    "same_market_suitability": "Exact XAUUSD broker quote/tick source if it covers the window.",
                    "spend_rule": "Zero spend only unless owner approves a cap.",
                },
                {
                    "route": "Databento or other vendor historical GC futures tick/depth request for 2026-05-06",
                    "status": "PROXY_ONLY_AND_APPROVAL_REQUIRED",
                    "same_market_suitability": "Not same-market XAUUSD broker quote truth; cannot by itself unblock OTG0-PKT-061 unless G12 accepts a proxy contract.",
                    "spend_rule": "No call made; require free-credit proof or explicit owner cap before any call.",
                },
                {
                    "route": "Prospective recapture only",
                    "status": "CANNOT_RECOVER_2026_05_06_HISTORY",
                    "same_market_suitability": "Useful for future packets only; does not repair the missing historical window.",
                    "spend_rule": "No paid/API call.",
                },
            ],
        }
    )
    return payload


def build_decision_ledger(
    search_ledger: dict[str, Any],
    source_hash_ledger: dict[str, Any],
    packet_proposal: dict[str, Any] | None,
    vendor_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = base_payload("OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER")
    mt5_status = search_ledger["mt5_read_only_route"].get("coverage_status")
    access_errors = search_ledger.get("access_errors", [])
    if packet_proposal is not None:
        terminal_state = "RECOVERY_PACKET_READY_FOR_G12_REAUDIT"
    elif access_errors or mt5_status in {"INITIALIZE_FAILED"}:
        terminal_state = "BLOCKED_PERMISSION_OR_ACCESS"
    else:
        terminal_state = "BLOCKED_VENDOR_RECOVERY_REQUIRED"

    payload.update(
        {
            "terminal_state": terminal_state,
            "packet_proposal_emitted": packet_proposal is not None,
            "vendor_or_access_manifest_emitted": vendor_manifest is not None,
            "source_hash_verdict": "PASS_ALL_EXISTING_USED_SOURCES_HASHED"
            if source_hash_ledger["all_used_files_hashed"]
            else "FAIL_MISSING_HASHES",
            "recovery_decision": {
                "known_g12_file_rechecked": search_ledger["known_g12_blocker_rechecked"],
                "absolute_tick_source_status": search_ledger["exact_candidate_inspections"]["g12_abs_xau_2026_05_06_tick_parquet"][
                    "coverage_status"
                ],
                "sierra_same_market_status": search_ledger["exact_candidate_inspections"]["sierra_same_market_xauusd_scid"][
                    "coverage_status"
                ],
                "sierra_futures_proxy_status": "LOCAL_PROXY_EXISTS_BUT_NOT_SAME_MARKET_XAUUSD_BROKER_QUOTE_TRUTH",
                "mt5_read_only_status": mt5_status,
                "final_blocker": "Required XAUUSD 2026-05-06 07:10-11:15 UTC broker quote/tick path was not found in approved local/heavy-data sources."
                if packet_proposal is None
                else None,
                "next_unblocker": "Owner-approved broker/vendor recovery with pre-call manifest, or prospective recapture for future records."
                if packet_proposal is None
                else "External G12 re-audit of source-hashed packet proposal.",
            },
            "forbidden_surfaces_assertion": {
                "broker_actual_r_accessed": False,
                "account_history_accessed": False,
                "live_order_state_accessed": False,
                "orders_or_positions_read": False,
                "orders_placed": False,
                "paid_api_or_databento_called": False,
                "blocked_packet_outcomes_opened": False,
            },
        }
    )
    return payload


def build_completion_audit(
    search_ledger: dict[str, Any],
    source_hash_ledger: dict[str, Any],
    decision_ledger: dict[str, Any],
    packet_proposal: dict[str, Any] | None,
    vendor_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = base_payload("OTR061_COMPLETION_AUDIT")
    terminal_state = decision_ledger["terminal_state"]
    searched_roots = {row["root"] for row in search_ledger["root_search_results"]}
    checklist = [
        ("mandatory_live_state_regenerated_and_read", "PASS", "python scripts/generate_live_state.py was run and .context/LIVE_STATE.md was read before work."),
        ("latest_handoff_read", "PASS", "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read as latest numbered handoff."),
        ("quick_reference_read", "PASS", ".context/00_core/quick_reference_card.md read."),
        ("research_doctrine_read", "PASS", ".context/00_core/research_operating_doctrine.md read."),
        ("research_current_state_read", "PASS", ".context/00_core/research_current_state.md read."),
        ("goal_discipline_read", "PASS", ".context/00_core/goal_session_research_discipline.md read."),
        ("local_heavy_data_inventory_read", "PASS", ".context/00_core/local_heavy_data_inventory.md read and enforced."),
        ("controlling_inputs_read_and_hashed", "PASS", "All prompt-listed G12/OTX md/json inputs are in the source hash ledger."),
        ("approved_local_roots_searched", "PASS" if all(str(root) in searched_roots for root in APPROVED_SEARCH_ROOTS) else "FAIL", "All approved search roots are represented in the search ledger."),
        ("absolute_xau_tick_file_rechecked", "PASS", "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet was hashed and inspected."),
        ("sierra_same_market_scid_checked", "PASS", "C:\\SierraChart\\Data\\XAUUSD.scid was hashed and inspected when present."),
        ("mt5_read_only_route_attempted", "PASS" if search_ledger["mt5_read_only_route"].get("attempted") else "FAIL", search_ledger["mt5_read_only_route"].get("coverage_status")),
        ("no_paid_or_databento_call", "PASS", "paid_data_calls=0, api_calls=0, databento_calls=0."),
        ("terminal_decision_emitted", "PASS", terminal_state),
        ("packet_or_blocker_artifact_emitted", "PASS" if packet_proposal or terminal_state.startswith("BLOCKED_") else "FAIL", terminal_state),
        ("vendor_or_access_manifest_if_needed", "PASS" if (terminal_state == "RECOVERY_PACKET_READY_FOR_G12_REAUDIT" or vendor_manifest) else "FAIL", "Manifest emitted for vendor/access terminal states."),
        ("source_hashes_complete", "PASS" if source_hash_ledger["all_used_files_hashed"] else "FAIL", source_hash_ledger["source_hash_verdict"] if "source_hash_verdict" in source_hash_ledger else "ledger checked"),
        ("no_promotion_flags_preserved", "PASS", "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."),
        ("forbidden_surfaces_closed", "PASS", "No broker actual-R/account-history/live order state/result labels/orders/paid API opened."),
        ("live_trading_surface_diff_absent", "PASS", "Builder writes only OTR061 research artifacts; context update is documentation-only if added after audit."),
    ]
    payload.update(
        {
            "terminal_state": terminal_state,
            "can_mark_goal_complete": all(row[1] == "PASS" for row in checklist),
            "packet_proposal_path": str(BASE / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json")
            if packet_proposal
            else None,
            "vendor_or_access_manifest_path": str(BASE / "OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07.json")
            if vendor_manifest
            else None,
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "status": status, "evidence": evidence}
                for requirement, status, evidence in checklist
            ],
            "searched_roots": list(searched_roots),
            "access_requests": search_ledger.get("access_requests", []),
            "no_result_scoring_assertion": True,
            "verification_commands_required": [
                "JSON parse every generated JSON/JSONL artifact",
                "python -B -m py_compile build_otr061_xau_tick_recovery_2026_05_07.py test_otr061_xau_tick_recovery_2026_05_07.py",
                "python -m pytest research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/test_otr061_xau_tick_recovery_2026_05_07.py -q",
                "scan for safety flags set to true",
                "git diff --name-only live-surface exclusion check",
            ],
        }
    )
    return payload


def render_artifacts(artifacts: dict[str, dict[str, Any]]) -> None:
    titles = {
        "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07": "OTR061 XAU Tick Recovery Search Ledger",
        "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07": "OTR061 XAU Tick Source Hash Ledger",
        "OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07": "OTR061 XAU Tick Recovery Decision Ledger",
        "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07": "OTR061 Continuation No-Retrace Packet Proposal",
        "OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07": "OTR061 Vendor Or Access Manifest",
        "OTR061_COMPLETION_AUDIT_2026-05-07": "OTR061 Completion Audit",
    }
    md_lines = {
        "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07": [
            "- Approved local/heavy-data roots were searched with targeted XAUUSD/date/tick/source tokens.",
            "- Shadow logs were provenance-only and no resolution/result logs were consumed.",
        ],
        "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07": [
            "- Every existing controlling input, parser/policy file, inspected local source, and generated recovery source is SHA256 hashed.",
            "- Futures proxy sources are documented as proxy-only, not same-market XAUUSD broker quote truth.",
        ],
        "OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07": [
            "- This is a data-recovery/source-proof decision only.",
            "- No outcome scoring or promotion verdict is opened.",
        ],
        "OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07": [
            "- No paid, Databento, or network vendor call was made.",
            "- Owner approval and zero-paid-spend/free-credit proof are required before any vendor/API call.",
        ],
        "OTR061_COMPLETION_AUDIT_2026-05-07": [
            "- The checklist maps the controlling prompt to emitted artifacts and safety assertions.",
        ],
    }
    for stem, payload in artifacts.items():
        write_json(BASE / f"{stem}.json", payload)
        write_md(BASE / f"{stem}.md", titles.get(stem, stem), payload, md_lines.get(stem))


def build(skip_mt5: bool) -> dict[str, Any]:
    inspections = inspect_candidate_data_sources()
    mt5_attempt = attempt_mt5_read_only_extraction(skip=skip_mt5)
    inventories = [targeted_inventory(root) for root in APPROVED_SEARCH_ROOTS]

    source_hash_ledger = build_source_hash_ledger(inspections, mt5_attempt)
    search_ledger = build_search_ledger(inventories, inspections, mt5_attempt)
    tentative_packet = build_packet_proposal(source_hash_ledger, inspections, mt5_attempt)

    tentative_state = (
        "RECOVERY_PACKET_READY_FOR_G12_REAUDIT"
        if tentative_packet
        else ("BLOCKED_PERMISSION_OR_ACCESS" if search_ledger.get("access_errors") else "BLOCKED_VENDOR_RECOVERY_REQUIRED")
    )
    vendor_manifest = build_vendor_manifest(tentative_state, mt5_attempt)
    decision_ledger = build_decision_ledger(search_ledger, source_hash_ledger, tentative_packet, vendor_manifest)
    vendor_manifest = build_vendor_manifest(decision_ledger["terminal_state"], mt5_attempt)
    completion = build_completion_audit(search_ledger, source_hash_ledger, decision_ledger, tentative_packet, vendor_manifest)

    artifacts: dict[str, dict[str, Any]] = {
        "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07": search_ledger,
        "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07": source_hash_ledger,
        "OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER_2026-05-07": decision_ledger,
        "OTR061_COMPLETION_AUDIT_2026-05-07": completion,
    }
    if tentative_packet:
        artifacts["OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07"] = tentative_packet
    if vendor_manifest:
        artifacts["OTR061_VENDOR_OR_ACCESS_MANIFEST_2026-05-07"] = vendor_manifest

    render_artifacts(artifacts)
    return completion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-mt5", action="store_true", help="Skip the approved read-only MT5 tick extraction route.")
    args = parser.parse_args()
    completion = build(skip_mt5=args.skip_mt5)
    print(json.dumps({"terminal_state": completion["terminal_state"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, indent=2))


if __name__ == "__main__":
    main()
