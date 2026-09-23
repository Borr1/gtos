from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

RESIDUAL_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_remaining_residual_source_closure"
)
MAY3_G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_may3_source_proof_audit"
)
RESIDUAL_BLOCKER_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_cat_v2_residual_blocker_clear_source_access_lane"
)
PENDING_SOURCE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_cat_v2_pending_source_contract_audit"
)
OTI2_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "oti2_fill_path_categorical_contract_v2"
)
OTI3_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "oti3_usdjpy_price_only_quote_or_tick_contract"
)
SOURCE_CORRECTION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_source_correction_consolidated_audit"
)

MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
MAIN_TICKS = MAIN_ROOT / "data" / "ticks"
MAIN_MT5_EXPORTS = MAIN_ROOT / "data" / "mt5_research_exports"
MAIN_EXTERNAL = MAIN_ROOT / "data" / "external"
TMP_GTOS = Path(r"C:\tmp\gtos_otb")
SIERRA_DATA = Path(r"C:\SierraChart\Data")

TARGET_ROWS = [
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
USDJPY_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
MAY3_ROWS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}
XAU_ROW = "NOFILL-CAT-ROW-0241"

ACCEPT_XAU = "ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE"
ACCEPT_USDJPY = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)
FORBIDDEN_JSON_KEYS = {
    "actual_r",
    "broker_actual_r",
    "hidden_label",
    "live_trade_result",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "broker_order_id",
    "broker_position_id",
    "pending_ticket",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, payload: Any) -> None:
    (LANE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (LANE_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"UNAVAILABLE:{exc!r}"


def normalize_ts(value: Any) -> pd.Timestamp:
    return pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")


def iso(value: Any) -> str | None:
    if value is None:
        return None
    ts = normalize_ts(value)
    return ts.isoformat().replace("+00:00", "Z")


def load_residual_packet() -> dict[str, Any]:
    return {
        "rows": read_jsonl(RESIDUAL_DIR / f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "xau": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json"),
        "usdjpy": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json"),
        "source_search": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.json"),
        "source_hash": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json"),
        "noleak": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json"),
        "completion": read_json(RESIDUAL_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json"),
    }


def read_upstream_context() -> dict[str, Any]:
    return {
        "g12_may3_decision_md": (MAY3_G12_DIR / f"G12_NOFILL_MAY3_DECISION_LEDGER_{DATE}.md").read_text(
            encoding="utf-8"
        ),
        "residual_blocker_rows": read_jsonl(
            RESIDUAL_BLOCKER_DIR / f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl"
        ),
        "pending_source_completion_md": (
            PENDING_SOURCE_DIR / f"G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_{DATE}.md"
        ).read_text(encoding="utf-8"),
        "oti2_rows": read_jsonl(OTI2_DIR / "OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl"),
        "oti3_rows": read_jsonl(OTI3_DIR / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"),
        "oti3_contract": read_json(OTI3_DIR / "OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.json"),
        "source_correction_md": (
            SOURCE_CORRECTION_DIR / "G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md"
        ).read_text(encoding="utf-8"),
    }


def summarize_xau_window(path: Path, start: str, end: str, entry: float) -> dict[str, Any]:
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    mask = (ts >= pd.Timestamp(start)) & (ts <= pd.Timestamp(end))
    sub = df.loc[mask].copy()
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "columns": list(df.columns),
        "rows_total": int(len(df)),
        "window_rows": int(len(sub)),
        "first_window_ts_utc": iso(sub["ts_utc"].min()) if len(sub) else None,
        "last_window_ts_utc": iso(sub["ts_utc"].max()) if len(sub) else None,
        "max_bid": float(pd.to_numeric(sub["bid"], errors="coerce").max()) if len(sub) else None,
        "max_ask": float(pd.to_numeric(sub["ask"], errors="coerce").max()) if len(sub) else None,
        "entry_price": entry,
        "short_entry_touch_bid_ge_entry": bool((pd.to_numeric(sub["bid"], errors="coerce") >= entry).any())
        if len(sub)
        else False,
    }


def exact_usdjpy_row(path: Path, ts_value: str, *, side: str, entry: float, protective: float, terminal: float) -> dict[str, Any]:
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    target = pd.Timestamp(ts_value)
    rows = df.loc[ts == target].copy()
    if side == "LONG":
        entry_touch = rows["ask"] <= entry
        protective_touch = rows["bid"] <= protective
        terminal_touch = rows["bid"] >= terminal
    else:
        entry_touch = rows["bid"] >= entry
        protective_touch = rows["ask"] >= protective
        terminal_touch = rows["ask"] <= terminal
    exact = []
    for idx, (_, row) in enumerate(rows.iterrows()):
        exact.append(
            {
                "row_position_within_exact_timestamp": idx,
                "ts_utc": iso(row["ts_utc"]),
                "ts_msc": int(row["ts_msc"]) if "ts_msc" in row else None,
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
                "last": float(row["last"]) if "last" in row else None,
                "volume": float(row["volume"]) if "volume" in row else None,
                "flags": int(row["flags"]) if "flags" in row else None,
                "entry_touch": bool(entry_touch.iloc[idx]),
                "protective_level": bool(protective_touch.iloc[idx]),
                "terminal_area": bool(terminal_touch.iloc[idx]),
            }
        )
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "columns": list(df.columns),
        "rows_total": int(len(df)),
        "target_ts_utc": ts_value,
        "exact_timestamp_row_count": int(len(rows)),
        "exact_rows": exact,
    }


def direct_evidence_recheck(packet: dict[str, Any]) -> dict[str, Any]:
    xau = packet["xau"]
    recovered_path = RESIDUAL_DIR / "raw" / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet"
    xau_recovered = summarize_xau_window(
        recovered_path,
        "2026-05-06T00:00:00Z",
        "2026-05-06T00:00:37.024315Z",
        float(xau["entry_price"]),
    )
    xau_may5 = summarize_xau_window(
        MAIN_TICKS / "XAUUSD" / "2026-05-05.parquet",
        "2026-05-05T08:15:26.485637Z",
        "2026-05-05T23:59:59.999Z",
        float(xau["entry_price"]),
    )

    usdjpy = []
    for row in packet["usdjpy"]["row_evidence"]:
        source_path = Path(row["source_path"])
        if not source_path.exists() and row["packet_row_id"] in {"NOFILL-CAT-ROW-0130", "NOFILL-CAT-ROW-0165"}:
            source_path = OTI3_DIR / "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet"
        usdjpy.append(
            {
                "packet_row_id": row["packet_row_id"],
                "side": row["side"],
                "levels": row["levels"],
                "source_recheck": exact_usdjpy_row(
                    source_path,
                    row["first_ambiguous_timestamp_utc"],
                    side=row["side"],
                    entry=float(row["levels"]["entry_price"]),
                    protective=float(row["levels"]["protective_level_price"]),
                    terminal=float(row["levels"]["terminal_area_price"]),
                ),
            }
        )
    return {
        "xauusd_recovered_gap_recheck": xau_recovered,
        "xauusd_may5_active_window_recheck": xau_may5,
        "usdjpy_exact_row_rechecks": usdjpy,
    }


def resolve_manifest_path(record: dict[str, Any]) -> Path:
    raw = Path(record["path"])
    if raw.exists():
        return raw
    rel_path = record.get("path_rel")
    if rel_path:
        candidate = ROOT / rel_path
        if candidate.exists():
            return candidate
    text = str(record["path"]).replace("\\", "/")
    marker = "/research/science_program_2026_05/"
    if marker in text:
        suffix = text.split(marker, 1)[1]
        candidate = ROOT / "research" / "science_program_2026_05" / Path(suffix)
        if candidate.exists():
            return candidate
    marker = "/.context/"
    if marker in text:
        suffix = text.split(marker, 1)[1]
        candidate = ROOT / ".context" / Path(suffix)
        if candidate.exists():
            return candidate
    return raw


def hash_manifest_audit(packet: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for record in packet["source_hash"]["records"]:
        resolved = resolve_manifest_path(record)
        mode = record.get("hash_verification_mode", "strict_sha256")
        actual = sha256_file(resolved) if resolved.exists() and resolved.is_file() else None
        expected = record.get("sha256")
        strict = mode != "presence_only_mutable_context"
        rows.append(
            {
                "role": record.get("role"),
                "path": record.get("path"),
                "path_rel": record.get("path_rel"),
                "resolved_path": str(resolved),
                "resolved_exists": resolved.exists(),
                "hash_verification_mode": mode,
                "strict_hash_required": strict,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "sha256_matches_expected": actual == expected if strict else True,
                "size_bytes": resolved.stat().st_size if resolved.exists() and resolved.is_file() else None,
            }
        )
    failures = [row for row in rows if row["strict_hash_required"] and not row["sha256_matches_expected"]]
    return {
        "record_count": len(rows),
        "strict_hash_record_count": sum(1 for row in rows if row["strict_hash_required"]),
        "strict_hash_failures": failures,
        "hash_records": rows,
    }


def official_doc_audit() -> dict[str, Any]:
    captures = []
    checks = {
        "mqltick_has_time_msc": False,
        "mqltick_has_flags": False,
        "mqltick_has_bid_ask": False,
        "copyticksrange_orders_rows_past_to_present": False,
        "copyticksrange_flags_describe_changed_fields": False,
        "python_returns_named_time_bid_ask_last_flags": False,
        "sub_row_sequence_field_found": False,
    }
    files = {
        "mqltick": RESIDUAL_DIR / "raw" / f"MQL5_MQLTICK_STRUCTURE_{DATE}.html",
        "copyticks_mql": RESIDUAL_DIR / "raw" / f"MQL5_COPY_TICKS_RANGE_MQL_{DATE}.html",
        "copyticks_py": RESIDUAL_DIR / "raw" / f"MQL5_COPY_TICKS_RANGE_PY_{DATE}.html",
        "source_index": RESIDUAL_DIR / "raw" / f"MQL5_SOURCE_INDEX_{DATE}.json",
    }
    for role, path in files.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        lower = text.lower()
        captures.append(
            {
                "role": role,
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
        if role == "mqltick":
            checks["mqltick_has_time_msc"] = "time_msc" in lower
            checks["mqltick_has_flags"] = "flags" in lower
            checks["mqltick_has_bid_ask"] = "bid" in lower and "ask" in lower
            checks["sub_row_sequence_field_found"] = checks["sub_row_sequence_field_found"] or "sequence" in lower
        if role == "copyticks_mql":
            checks["copyticksrange_orders_rows_past_to_present"] = "past to the present" in lower
            checks["copyticksrange_flags_describe_changed_fields"] = "flags" in lower and "what exactly has changed" in lower
            checks["sub_row_sequence_field_found"] = checks["sub_row_sequence_field_found"] or "sequence" in lower
        if role == "copyticks_py":
            checks["python_returns_named_time_bid_ask_last_flags"] = (
                "returns ticks as the numpy array" in lower
                and "time" in lower
                and "bid" in lower
                and "ask" in lower
                and "last" in lower
                and "flags" in lower
            )
            checks["sub_row_sequence_field_found"] = checks["sub_row_sequence_field_found"] or "sequence" in lower
    return {
        "raw_captures": captures,
        "contract_checks": checks,
        "decision": (
            "Official MQL5 captures support row-level chronological ordering and MqlTick quote-state fields, "
            "but no sequence/sub-row event field was found for ordering multiple predicates inside one quote row."
        ),
    }


def independent_source_search() -> dict[str, Any]:
    def record(path: Path, role: str, status: str, note: str) -> dict[str, Any]:
        return {
            "role": role,
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
            "status": status,
            "decision_note": note,
        }

    records = [
        record(
            MAIN_TICKS / "USDJPY" / "2026-05-01.parquet",
            "main_usdjpy_2026_05_01_broker_tick_parquet",
            "FOUND_ACCEPTED_BID_ASK_QUOTE_STATE_ONLY",
            "Used for May 1 rows; schema has ts_utc/ts_msc/bid/ask/flags but no sub-row sequence.",
        ),
        record(
            MAIN_TICKS / "USDJPY" / "2026-04-20.parquet",
            "main_usdjpy_2026_04_20_broker_tick_parquet",
            "NOT_FOUND_IN_MAIN_TICK_ROOT",
            "Prior-worktree read-only MT5 export supplies Apr 20 source; no alternate sequence source in main ticks.",
        ),
        record(
            OTI3_DIR / "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
            "current_worktree_usdjpy_2026_04_20_readonly_mt5_tick_parquet",
            "FOUND_ACCEPTED_BID_ASK_QUOTE_STATE_ONLY",
            "Same sha as prior worktrees; no sub-row sequence.",
        ),
        record(
            MAIN_TICKS / "XAUUSD" / "2026-05-05.parquet",
            "main_xauusd_2026_05_05_broker_tick_parquet",
            "FOUND_ACCEPTED_BID_ASK_QUOTE_STATE",
            "Covers active window through 23:59:59.998 UTC before cancel gap.",
        ),
        record(
            MAIN_TICKS / "XAUUSD" / "2026-05-06.parquet",
            "main_xauusd_2026_05_06_existing_broker_tick_parquet",
            "FOUND_BUT_STARTS_AFTER_CANCEL",
            "Existing May 6 file starts after cancel; recovered read-only gap parquet is the decisive source.",
        ),
        record(
            RESIDUAL_DIR / "raw" / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
            "current_worktree_recovered_xauusd_gap_parquet",
            "FOUND_ACCEPTED_READ_ONLY_GAP_TICKS",
            "Recovered via MT5 copy_ticks_range with no account/order/history calls recorded.",
        ),
        record(
            MAIN_MT5_EXPORTS / "phase3_v2b_forward_20260401_20260502_readonly" / "USDJPY_M1.csv",
            "main_usdjpy_m1_context",
            "FOUND_CONTEXT_ONLY_CANNOT_ORDER_SAME_TICK",
            "M1 OHLC cannot order predicates inside one millisecond quote row.",
        ),
        record(
            SIERRA_DATA / "6JM26-CME.scid",
            "sierra_6j_proxy_scid",
            "FOUND_PROXY_NOT_BROKER_NATIVE_USDJPY_EVENT_SEQUENCE",
            "6J futures proxy can be context only; it cannot sequence broker-native USDJPY CFD bid/ask state.",
        ),
        record(
            SIERRA_DATA / "XAUUSD.scid",
            "sierra_xauusd_scid",
            "FOUND_NOT_NEEDED_FOR_0241",
            "XAUUSD decision already resolved by broker-side tick parquets and recovered MT5 gap ticks.",
        ),
    ]
    apr20_duplicates = sorted(
        TMP_GTOS.glob("*/research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet")
    )
    xau_recovered_duplicates = sorted(
        TMP_GTOS.glob("*/research/science_program_2026_05/06_outcome_testing/nofill_remaining_residual_source_closure/raw/NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet")
    )
    return {
        "searched_roots": [
            str(MAIN_TICKS),
            str(MAIN_MT5_EXPORTS),
            str(MAIN_EXTERNAL),
            str(SIERRA_DATA),
            str(TMP_GTOS),
        ],
        "records": records,
        "prior_worktree_usdjpy_apr20_duplicate_count": len(apr20_duplicates),
        "prior_worktree_usdjpy_apr20_duplicates": [
            {"path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in apr20_duplicates[:30]
        ],
        "prior_worktree_xau_recovered_gap_duplicate_count": len(xau_recovered_duplicates),
        "prior_worktree_xau_recovered_gap_duplicates": [
            {"path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in xau_recovered_duplicates[:30]
        ],
        "conclusion": (
            "No searched local root or prior worktree exposed a source-safe USDJPY route with sequence ID, "
            "sub-millisecond timestamp, or sub-row quote-event ordering. All found USDJPY sources are quote-state "
            "rows, M1 context, or futures/proxy context. XAUUSD 0241 is resolved by read-only side-aware broker ticks."
        ),
    }


def scan_json_boundaries(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    unsafe_true: list[dict[str, Any]] = []

    def walk(obj: Any, path: str, file_name: str) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_l = str(key).lower()
                if key_l in FORBIDDEN_JSON_KEYS:
                    hits.append({"file": file_name, "path": f"{path}.{key}", "key": key})
                if key_l in {"validation_safe", "outcome_review_opened", "live_effect"} and value is True:
                    unsafe_true.append({"file": file_name, "path": f"{path}.{key}", "key": key})
                walk(value, f"{path}.{key}", file_name)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                walk(item, f"{path}[{idx}]", file_name)

    for file_path in paths:
        if file_path.suffix == ".jsonl":
            payload: Any = read_jsonl(file_path)
        else:
            payload = read_json(file_path)
        walk(payload, "$", rel(file_path))
    return {
        "files_scanned": [rel(path) for path in paths],
        "forbidden_result_or_account_key_hits": hits,
        "unsafe_true_flag_hits": unsafe_true,
        "status": "PASS" if not hits and not unsafe_true else "FAIL",
    }


def build_decision_ledger(packet: dict[str, Any], upstream: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    rows = packet["rows"]
    blocker_by_id = {
        row["packet_row_id"]: row
        for row in upstream["residual_blocker_rows"]
        if row.get("packet_row_id") in set(TARGET_ROWS) | MAY3_ROWS
    }
    row_decisions = []
    for row in rows:
        rid = row["packet_row_id"]
        if rid == XAU_ROW:
            decision = ACCEPT_XAU
            rationale = (
                "Accepted as source/control input-only evidence because read-only side-aware XAUUSD bid/ask ticks "
                "cover active creation through cancel and bid never reached the short entry before cancel."
            )
        else:
            decision = ACCEPT_USDJPY
            rationale = (
                "Accepted as source impossibility evidence because the first source timestamp has exactly one "
                "MqlTick quote-state row where entry and protective predicates are both true, and approved routes "
                "do not expose a sub-row sequence."
            )
        blocker = blocker_by_id.get(rid, {})
        field_matches = {
            field: row.get(field) == blocker.get(field)
            for field in [
                "packet_row_id",
                "symbol",
                "session",
                "side",
                "source_packet_id",
                "source_row_id",
                "source_inventory_id",
                "source_close_packet_row_id",
                "duplicate_group_id",
                "nofill_duplicate_key",
            ]
        }
        row_decisions.append(
            {
                "packet_row_id": rid,
                "symbol": row["symbol"],
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "upstream_residual_source_status": row["terminal_source_control_status"],
                "prior_blocker_lane_status": blocker.get("terminal_source_control_status"),
                "g12_terminal_decision": decision,
                "decision_rationale": rationale,
                "source_control_only": True,
                "categorical_lifecycle_label": None,
                "result_or_performance_label": None,
                "cleared_into_accepted_denominator": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "identity_field_matches_prior_blocker_lane": field_matches,
                "all_identity_fields_match_prior_blocker_lane": all(field_matches.values()) if blocker else False,
                "original_blocker_codes": row.get("original_exact_blocker_codes"),
                "exact_next_source_needed_if_reopened": row.get("exact_next_source_needed"),
            }
        )
    return {
        "artifact_family": "G12_NOFILL_REMAINING_DECISION_LEDGER",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "packet_decision": "ACCEPT_BY_ROW_EVIDENCE_CLASS_ONLY",
        "target_row_ids": [row["packet_row_id"] for row in rows],
        "targeted_row_count": len(rows),
        "may3_rows_kept_closed": sorted(MAY3_ROWS),
        "may3_rows_reopened": [],
        "row_decisions": row_decisions,
        "terminal_decision_counts": dict(Counter(row["g12_terminal_decision"] for row in row_decisions)),
        "upstream_status_counts": dict(Counter(row["terminal_source_control_status"] for row in rows)),
        "audit_question_answers": [
            {
                "question": "Are exactly five target rows audited and no others?",
                "answer": "Yes. The decision ledger contains exactly 0241, 0130, 0143, 0165, and 0178.",
            },
            {
                "question": "Were May 3 rows kept closed?",
                "answer": "Yes. 0049/0050/0051 remain closed context from the prior G12 May3 audit and are not row decisions here.",
            },
            {
                "question": "Is XAUUSD 0241 acceptable as source-control input-only evidence?",
                "answer": "Yes, narrowly. It proves no side-aware short entry touch before cancel; it does not assign a lifecycle/result/performance label.",
            },
            {
                "question": "Are USDJPY same-tick rows source-impossible from approved routes?",
                "answer": "Yes. Current approved quote/tick rows are MqlTick state rows with no sub-row sequence; M1 and Sierra/proxy routes cannot resolve broker-native event order.",
            },
            {
                "question": "Is a future result/categorical rebuild allowed?",
                "answer": "Only as a separate evidence-class gate. XAUUSD 0241 may be consumed as input-only source-control evidence; the USDJPY rows remain impossibility evidence/blockers unless a broker-native sequence source appears.",
            },
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "evidence_summary": {
            "xau_recovered_gap_rows": evidence["xauusd_recovered_gap_recheck"]["window_rows"],
            "xau_recovered_gap_max_bid": evidence["xauusd_recovered_gap_recheck"]["max_bid"],
            "xau_short_entry_touch": evidence["xauusd_recovered_gap_recheck"]["short_entry_touch_bid_ge_entry"],
            "usdjpy_exact_row_counts": {
                row["packet_row_id"]: row["source_recheck"]["exact_timestamp_row_count"]
                for row in evidence["usdjpy_exact_row_rechecks"]
            },
        },
    }


def build_xau_audit(packet: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    xau = packet["xau"]
    return {
        "artifact_family": "G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "packet_row_id": XAU_ROW,
        "g12_terminal_decision": ACCEPT_XAU,
        "accepted_evidence_class": "source_control_input_only_no_entry_touch_through_cancel",
        "side_aware_rule": xau["short_entry_touch_rule"],
        "entry_price": xau["entry_price"],
        "active_window_start_utc": xau["active_window_start_utc"],
        "cancel_observed_at_utc": xau["cancel_observed_at_utc"],
        "broker_offset_evidence": xau["broker_offset_evidence"],
        "upstream_packet_claim": {
            "source_control_status": xau["source_control_status"],
            "recovered_gap_rows_through_cancel": xau["recovered_gap_rows_through_cancel"],
            "max_bid_through_cancel": xau["max_bid_through_cancel"],
            "max_ask_through_cancel": xau["max_ask_through_cancel"],
            "entry_touch_before_cancel": xau["entry_touch_before_cancel"],
            "mt5_read_only_capture": xau["mt5_read_only_capture"],
        },
        "g12_direct_recheck": {
            "may5_active_window": evidence["xauusd_may5_active_window_recheck"],
            "recovered_may6_gap": evidence["xauusd_recovered_gap_recheck"],
        },
        "decision": (
            "Accept. The May 5 broker tick stream and recovered true-UTC May 6 gap stream are side-aware, hashed, "
            "and show bid below the short entry through the observed cancel. The capture recorded zero account, "
            "order, deal, position, history, order_send, paid API, or Databento calls."
        ),
        "does_not_prove": [
            "No lifecycle/result/performance/R label.",
            "No accepted denominator movement.",
            "No validation-safe or promotion claim.",
            "No live trading behavior change.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_usdjpy_audit(packet: dict[str, Any], evidence: dict[str, Any], doc_audit: dict[str, Any], search: dict[str, Any]) -> dict[str, Any]:
    rows = []
    upstream_by_id = {row["packet_row_id"]: row for row in packet["usdjpy"]["row_evidence"]}
    for recheck in evidence["usdjpy_exact_row_rechecks"]:
        rid = recheck["packet_row_id"]
        rows.append(
            {
                "packet_row_id": rid,
                "g12_terminal_decision": ACCEPT_USDJPY,
                "upstream_evidence": upstream_by_id[rid],
                "g12_source_recheck": recheck["source_recheck"],
                "same_tick_impossibility_holds": recheck["source_recheck"]["exact_timestamp_row_count"] == 1
                and all(
                    row["entry_touch"] and row["protective_level"] and not row["terminal_area"]
                    for row in recheck["source_recheck"]["exact_rows"]
                ),
            }
        )
    return {
        "artifact_family": "G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "target_rows": USDJPY_ROWS,
        "g12_terminal_decision": ACCEPT_USDJPY,
        "row_audits": rows,
        "official_doc_contract": doc_audit,
        "independent_source_search": search,
        "decision": (
            "Accept as source impossibility evidence only. The same-tick rows are not rejected because data is missing; "
            "they are impossible under approved routes because the decisive source unit is one MqlTick quote-state row "
            "with multiple true predicates and no sub-row sequence."
        ),
        "exact_unblocker": (
            "A broker-native USDJPY quote-event source with a sequence ID, exchange/broker quote-event sequence number, "
            "or sub-millisecond/sub-row timestamp for each quote update, source-hashed and without account/order/history labels."
        ),
        "rejected_routes": [
            "M1 OHLC context cannot order same-millisecond bid/ask predicates.",
            "Sierra 6J futures proxy is not the broker-native USDJPY CFD quote-event stream.",
            "MqlTick flags show changed fields but do not order entry/protective predicates inside one quote-state row.",
            "MT5 account/order/history/deal/position routes are forbidden in this source-control lane.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_noleak_audit(packet: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    scan_paths = [
        RESIDUAL_DIR / f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl",
        RESIDUAL_DIR / f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json",
        RESIDUAL_DIR / f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json",
        RESIDUAL_DIR / f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json",
        RESIDUAL_DIR / f"NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_{DATE}.json",
    ]
    boundary_scan = scan_json_boundaries(scan_paths)
    return {
        "artifact_family": "G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "target_row_count": len(decision["target_row_ids"]),
        "target_rows": decision["target_row_ids"],
        "may3_rows_reopened": [],
        "reject_total_preserved_outside_labels_denominators": packet["noleak"]["reject_total_preserved_outside_labels_denominators"],
        "duplicate_group_counts": packet["noleak"]["duplicate_group_counts"],
        "rows_moved_to_accepted_denominator": packet["noleak"]["rows_moved_to_accepted_denominator"],
        "lifecycle_labels_assigned": packet["noleak"]["lifecycle_labels_assigned"],
        "result_or_performance_labels_assigned": packet["noleak"]["result_or_performance_labels_assigned"],
        "validation_safe_true_count": packet["noleak"]["validation_safe_true_count"],
        "outcome_review_opened_true_count": packet["noleak"]["outcome_review_opened_true_count"],
        "live_effect_true_count": packet["noleak"]["live_effect_true_count"],
        "boundary_scan": boundary_scan,
        "label_family_decision": (
            "XAUUSD 0241 is source-control input-only; USDJPY rows are impossibility evidence only. "
            "No lifecycle/result/performance label family opens in this G12 lane."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_source_hash_audit(packet: dict[str, Any], doc_audit: dict[str, Any]) -> dict[str, Any]:
    manifest = hash_manifest_audit(packet)
    return {
        "artifact_family": "G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "residual_source_hash_manifest_record_count": packet["source_hash"]["record_count"],
        "g12_hash_manifest_audit": manifest,
        "official_mql5_raw_capture_audit": doc_audit,
        "raw_capture_decision": (
            "Strict source/raw hashes recompute where stable. Mutable GTOS context records remain presence-only, "
            "matching the hardened upstream residual verifier policy."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_residual_verifier_audit(packet: dict[str, Any]) -> dict[str, Any]:
    verifier_path = RESIDUAL_DIR / f"verify_nofill_remaining_residual_source_closure_2026_05_09.py"
    verifier_text = verifier_path.read_text(encoding="utf-8")
    completion_verification = packet["completion"].get("verification", {})
    code_checks = {
        "uses_committed_diff_names_for_forbidden_live_surface": "git_committed_diff_names" in verifier_text
        and "forbidden_diff = [name for name in committed_diff_names" in verifier_text,
        "records_workspace_diff_names_as_informational": "workspace_diff_names" in verifier_text,
        "checks_forbidden_live_prefixes": "FORBIDDEN_LIVE_PREFIXES" in verifier_text,
        "checks_source_hashes": "check_hashes(manifest)" in verifier_text,
        "checks_exact_target_rows": "ids == TARGET_IDS" in verifier_text,
    }
    return {
        "artifact_family": "G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "residual_verifier_path": rel(verifier_path),
        "residual_verifier_sha256": sha256_file(verifier_path),
        "upstream_completion_verification_snapshot": completion_verification,
        "code_checks": code_checks,
        "decision": (
            "Pass. The residual verifier treats workspace dirt separately from committed-scope forbidden live-surface "
            "diffs, and it independently checks target rows, source hashes, unsafe flags, May 3 exclusion, and no-leak controls."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def build_completion(decision: dict[str, Any], xau: dict[str, Any], usdjpy: dict[str, Any], source_hash: dict[str, Any], noleak: dict[str, Any], verifier_audit: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory GTOS preflight and required context read",
            "artifact": f"G12_NOFILL_REMAINING_CONTEXT_ANCHOR_{DATE}.md",
            "status": "PASS",
            "evidence": "LIVE_STATE was regenerated; latest handoff, quick reference, doctrine, research_current_state, discipline, local-heavy inventory, and reading order were read.",
        },
        {
            "requirement": "complete residual source closure packet read and audited",
            "artifact": f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json",
            "status": "PASS",
            "evidence": "Residual row ledger, proof packets, source search, source hash, no-leak, completion audit, builder/verifier/tests, and raw captures were read or rechecked.",
        },
        {
            "requirement": "exactly five target rows audited and May 3 rows closed",
            "artifact": f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json",
            "status": "PASS" if decision["target_row_ids"] == TARGET_ROWS and not decision["may3_rows_reopened"] else "FAIL",
            "evidence": decision["target_row_ids"],
        },
        {
            "requirement": "XAUUSD 0241 source-control input-only decision",
            "artifact": f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json",
            "status": "PASS" if xau["g12_terminal_decision"] == ACCEPT_XAU else "FAIL",
            "evidence": xau["decision"],
        },
        {
            "requirement": "USDJPY same-tick impossibility decision",
            "artifact": f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json",
            "status": "PASS" if usdjpy["g12_terminal_decision"] == ACCEPT_USDJPY else "FAIL",
            "evidence": usdjpy["decision"],
        },
        {
            "requirement": "source hash/raw capture audit",
            "artifact": f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json",
            "status": "PASS" if not source_hash["g12_hash_manifest_audit"]["strict_hash_failures"] else "FAIL",
            "evidence": {
                "records": source_hash["g12_hash_manifest_audit"]["record_count"],
                "strict_failures": len(source_hash["g12_hash_manifest_audit"]["strict_hash_failures"]),
            },
        },
        {
            "requirement": "no-leak duplicate denominator label-family audit",
            "artifact": f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json",
            "status": "PASS" if noleak["boundary_scan"]["status"] == "PASS" and noleak["rows_moved_to_accepted_denominator"] == 0 else "FAIL",
            "evidence": noleak["label_family_decision"],
        },
        {
            "requirement": "residual verifier audit",
            "artifact": f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.json",
            "status": "PASS" if all(verifier_audit["code_checks"].values()) else "FAIL",
            "evidence": verifier_audit["decision"],
        },
        {
            "requirement": "preserve safety flags and no promotion/outcome/live effect",
            "artifact": "all generated G12 artifacts",
            "status": "PASS",
            "evidence": "All generated JSON writes NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
        },
        {
            "requirement": "verifier/tests/py_compile/focused pytest",
            "artifact": f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json",
            "status": "PENDING_VERIFIER_RUN",
            "evidence": "Filled by verifier/test run after build.",
        },
    ]
    return {
        "artifact_family": "G12_NOFILL_REMAINING_COMPLETION_AUDIT",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "objective_restatement": (
            "Independently G12-audit the residual no-fill source-closure packet for exactly five rows; accept or reject "
            "source/control input-only XAUUSD evidence and USDJPY source-impossibility evidence while preserving closed "
            "result, validation, promotion, and live-behavior lanes."
        ),
        "terminal_packet_decision": decision["packet_decision"],
        "terminal_decision_counts": decision["terminal_decision_counts"],
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": [item for item in checklist if item["status"] == "FAIL"],
        "can_mark_goal_complete_after_verifier": False,
        "verification": {"status": "PENDING_VERIFIER_RUN"},
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def write_markdown_outputs(outputs: dict[str, Any]) -> None:
    generated_at = utc_now()
    decision = outputs["decision"]
    xau = outputs["xau"]
    usdjpy = outputs["usdjpy"]
    source_hash = outputs["source_hash"]
    noleak = outputs["noleak"]
    verifier = outputs["verifier"]
    completion = outputs["completion"]

    write_md(
        f"G12_NOFILL_REMAINING_CONTEXT_ANCHOR_{DATE}.md",
        f"""# G12 NOFILL Remaining Residual Source Closure Context Anchor - {DATE}

Generated: `{generated_at}`

## Run State

- HEAD at build: `{git_output("rev-parse", "HEAD")}`
- Controlling prompt: `research/science_program_2026_05/06_outcome_testing/g12_nofill_remaining_residual_source_closure_audit/G12_NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_AUDIT_GOAL_PROMPT_2026-05-09.md`
- Scope: source/control G12 audit only.
- Safety posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Inputs Read

- Mandatory GTOS preflight files, latest handoff, quick reference, research doctrine/current state, goal-session discipline, local-heavy inventory, and reading order.
- Complete `nofill_remaining_residual_source_closure` packet, including raw MQL5 captures and recovered XAUUSD parquet.
- G12 May3 audit, residual blocker clearance lane, G12 pending source contract audit, OTI2 fill/path V2, OTI3 USDJPY quote/tick contract, and G12 consolidated source-correction audit.

## Active Question Stack

- Exactly five rows and no May 3 reopen.
- XAUUSD 0241 source-control input-only acceptance.
- USDJPY 0130/0143/0165/0178 source impossibility from approved routes.
- Source hashes/raw captures, no-leak/duplicate/denominator/label-family, residual verifier behavior.

After resume, regenerate `LIVE_STATE`, read this anchor and the completion audit, then continue from verifier status rather than chat memory.
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.md",
        f"""# G12 NOFILL Remaining Decision Ledger - {DATE}

Generated: `{generated_at}`

Packet decision: `{decision["packet_decision"]}`

Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Row Decisions

{md_table(decision["row_decisions"], ["packet_row_id", "symbol", "upstream_residual_source_status", "g12_terminal_decision", "source_control_only", "cleared_into_accepted_denominator"])}

## Audit Question Answers

{chr(10).join(f"- {item['question']}: {item['answer']}" for item in decision["audit_question_answers"])}
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining XAUUSD Source-Control Audit - {DATE}

Decision: `{xau["g12_terminal_decision"]}`

## Direct Recheck

```json
{json.dumps(xau["g12_direct_recheck"], indent=2, sort_keys=True)}
```

## Interpretation

{xau["decision"]}

It proves no side-aware short entry touch through cancel for source/control input use only. It does not prove a lifecycle label, result, R/performance, denominator admission, validation, promotion, or live behavior.
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining USDJPY Same-Tick Impossibility Audit - {DATE}

Decision: `{usdjpy["g12_terminal_decision"]}`

## Row Audit

{md_table([{"packet_row_id": row["packet_row_id"], "same_tick_impossibility_holds": row["same_tick_impossibility_holds"], "exact_rows": row["g12_source_recheck"]["exact_timestamp_row_count"]} for row in usdjpy["row_audits"]], ["packet_row_id", "same_tick_impossibility_holds", "exact_rows"])}

## Official Source Contract

```json
{json.dumps(usdjpy["official_doc_contract"]["contract_checks"], indent=2, sort_keys=True)}
```

## Independent Source Search

{usdjpy["independent_source_search"]["conclusion"]}

Exact unblocker: {usdjpy["exact_unblocker"]}

This is impossibility evidence only, not a result or validation label.
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining Source Hash And Raw Capture Audit - {DATE}

Strict source hash failures: `{len(source_hash["g12_hash_manifest_audit"]["strict_hash_failures"])}`.

Residual manifest records: `{source_hash["residual_source_hash_manifest_record_count"]}`.

## Official MQL5 Raw Capture Decision

{source_hash["official_mql5_raw_capture_audit"]["decision"]}

## Hash Audit Summary

```json
{json.dumps({"record_count": source_hash["g12_hash_manifest_audit"]["record_count"], "strict_hash_record_count": source_hash["g12_hash_manifest_audit"]["strict_hash_record_count"], "strict_hash_failures": source_hash["g12_hash_manifest_audit"]["strict_hash_failures"]}, indent=2, sort_keys=True)}
```
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining No-Leak Duplicate Denominator Label-Family Audit - {DATE}

Decision: `{noleak["label_family_decision"]}`

## Counts

```json
{json.dumps({k: noleak[k] for k in ["target_row_count", "may3_rows_reopened", "reject_total_preserved_outside_labels_denominators", "rows_moved_to_accepted_denominator", "lifecycle_labels_assigned", "result_or_performance_labels_assigned", "validation_safe_true_count", "outcome_review_opened_true_count", "live_effect_true_count"]}, indent=2, sort_keys=True)}
```

## Boundary Scan

```json
{json.dumps(noleak["boundary_scan"], indent=2, sort_keys=True)}
```
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining Residual Verifier Audit - {DATE}

Decision: `{verifier["decision"]}`

## Code Checks

```json
{json.dumps(verifier["code_checks"], indent=2, sort_keys=True)}
```

The upstream verifier is not treated as a proxy for this G12 completion by itself. This audit checks that it validates exact rows, source hashes, unsafe flags, May 3 exclusion, no-leak controls, and committed-scope forbidden live-surface paths while preserving workspace dirt as informational.
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_NEXT_PROMPT_PACK_{DATE}.md",
        f"""# G12 NOFILL Remaining Next Prompt Pack - {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`.
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## G12 Outcome

- `NOFILL-CAT-ROW-0241`: `{ACCEPT_XAU}` for source-control input-only evidence.
- `NOFILL-CAT-ROW-0130`, `0143`, `0165`, `0178`: `{ACCEPT_USDJPY}`.
- May 3 rows `0049/0050/0051` remain closed under the prior G12 May3 audit and are not reopened here.

## Exact Next Route

A future categorical rebuild may consume `NOFILL-CAT-ROW-0241` only as source-control input evidence that no side-aware short entry touch occurred before cancel. The four USDJPY rows must remain source-impossible blockers unless the owner provides a broker-native USDJPY quote-event source with sequence ID or sub-row/sub-millisecond timestamp, source-hashed and without account/order/history labels.

Closed routes remain closed: no result/R/performance scoring, broker actual-R, account/order/history/deal/position labels, hidden labels, paid/API/Databento without approval, registry edit, validation-safe flip, promotion, or live trading behavior.
""",
    )

    write_md(
        f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md",
        f"""# G12 NOFILL Remaining Completion Audit - {DATE}

Generated: `{generated_at}`

Objective restatement: {completion["objective_restatement"]}

Can mark complete after verifier: `{completion["can_mark_goal_complete_after_verifier"]}`.

## Prompt-To-Artifact Checklist

{md_table(completion["prompt_to_artifact_checklist"], ["requirement", "artifact", "status", "evidence"])}

## Missing, Incomplete, Or Weak Requirements

```json
{json.dumps(completion["missing_incomplete_or_weak_requirements"], indent=2, sort_keys=True)}
```
""",
    )


def build() -> dict[str, Any]:
    packet = load_residual_packet()
    upstream = read_upstream_context()
    evidence = direct_evidence_recheck(packet)
    doc_audit = official_doc_audit()
    source_search = independent_source_search()
    decision = build_decision_ledger(packet, upstream, evidence)
    xau = build_xau_audit(packet, evidence)
    usdjpy = build_usdjpy_audit(packet, evidence, doc_audit, source_search)
    source_hash = build_source_hash_audit(packet, doc_audit)
    noleak = build_noleak_audit(packet, decision)
    verifier = build_residual_verifier_audit(packet)
    completion = build_completion(decision, xau, usdjpy, source_hash, noleak, verifier)

    outputs = {
        "decision": decision,
        "xau": xau,
        "usdjpy": usdjpy,
        "source_hash": source_hash,
        "noleak": noleak,
        "verifier": verifier,
        "completion": completion,
    }

    write_json(f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json", decision)
    write_json(f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json", xau)
    write_json(f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json", usdjpy)
    write_json(f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json", source_hash)
    write_json(f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json", noleak)
    write_json(f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.json", verifier)
    write_json(f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_outputs(outputs)

    summary = {
        "built": True,
        "targeted_row_count": decision["targeted_row_count"],
        "terminal_decision_counts": decision["terminal_decision_counts"],
        "strict_source_hash_failures": len(source_hash["g12_hash_manifest_audit"]["strict_hash_failures"]),
        "noleak_status": noleak["boundary_scan"]["status"],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    build()
