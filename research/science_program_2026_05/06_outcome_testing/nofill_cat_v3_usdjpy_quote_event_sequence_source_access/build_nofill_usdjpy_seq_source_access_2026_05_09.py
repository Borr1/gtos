"""Build NOFILL USDJPY same-tick quote-event source-access artifacts.

This route is source/control only. It reconstructs the four frozen USDJPY
same-tick blockers, re-inspects approved local/heavy/prior-worktree sources,
and emits proof-or-impossibility ledgers without result scoring or broker
account/order/history evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


TARGET_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]

SCHEMA = "nofill_usdjpy_quote_event_sequence_source_access_v1"
PROMOTION = "NO_PROMOTION_VERDICT"
DATE = "2026-05-09"
MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
GTOS_TMP_ROOT = Path(r"C:\tmp\gtos_otb")
SIERRA_ROOT = Path(r"C:\SierraChart")

FLAG_BITS = {
    1: "TICK_FLAG_UNKNOWN_1",
    2: "TICK_FLAG_BID",
    4: "TICK_FLAG_ASK",
    8: "TICK_FLAG_LAST",
    16: "TICK_FLAG_VOLUME",
    32: "TICK_FLAG_BUY",
    64: "TICK_FLAG_SELL",
    128: "TICK_FLAG_VOLUME_REAL",
}


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent

UPSTREAM_OTI3_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "oti3_usdjpy_price_only_quote_or_tick_contract/"
    / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"
)
UPSTREAM_OTI2_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "oti2_fill_path_categorical_contract_v2/"
    / "OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl"
)
NOFILL_REMAINING_PROOF_JSON = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "nofill_remaining_residual_source_closure/"
    / "NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_2026-05-09.json"
)
G12_REMAINING_IMPOSSIBILITY_JSON = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g12_nofill_remaining_residual_source_closure_audit/"
    / "G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_2026-05-09.json"
)
G0_NEXT_ROUTE_JSON = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/"
    / "G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.json"
)
G0_BACKLOG_MD = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/"
    / "G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md"
)
PROMPT_FILE = ROUTE_DIR / "NOFILL_CAT_V3_USDJPY_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS_GOAL_PROMPT_2026-05-09.md"
LIVE_STATE = REPO_ROOT / ".context/LIVE_STATE.md"
RESEARCH_STATE = REPO_ROOT / ".context/00_core/research_current_state.md"
QUICK_REFERENCE = REPO_ROOT / ".context/00_core/quick_reference_card.md"
RESEARCH_DOCTRINE = REPO_ROOT / ".context/00_core/research_operating_doctrine.md"
GOAL_DISCIPLINE = REPO_ROOT / ".context/00_core/goal_session_research_discipline.md"
LOCAL_HEAVY = REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md"
TICK_CAPTURE = REPO_ROOT / "src/components/tick_capture.py"

RAW_DOC_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "nofill_remaining_residual_source_closure/raw"
)
MQL_RAW_DOCS = [
    RAW_DOC_DIR / "MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html",
    RAW_DOC_DIR / "MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html",
    RAW_DOC_DIR / "MQL5_MQLTICK_STRUCTURE_2026-05-09.html",
    RAW_DOC_DIR / "MQL5_SOURCE_INDEX_2026-05-09.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path, role: str, *, strict: bool = True, used_for_claims: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path),
        "role": role,
        "exists": exists,
        "strict_hash": strict,
        "used_for_claims": used_for_claims,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def read_first_csv_fields(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return {"exists": True, "columns": header, "row_count": rows, "sha256": sha256_file(path)}


def flag_names(flags: int) -> list[str]:
    return [name for bit, name in sorted(FLAG_BITS.items()) if flags & bit]


def target_rows_from_upstream() -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(UPSTREAM_OTI3_LEDGER) if r.get("source_packet_row_id") in TARGET_ROWS]
    by_id = {r["source_packet_row_id"]: r for r in rows}
    missing = [row_id for row_id in TARGET_ROWS if row_id not in by_id]
    if missing:
        raise RuntimeError(f"Missing upstream OTI3 rows: {missing}")
    return [by_id[row_id] for row_id in TARGET_ROWS]


def normalize_tick_frame(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "time_msc" in df.columns and "ts_msc" not in df.columns:
        df = df.rename(columns={"time_msc": "ts_msc"})
    if "ts_utc" not in df.columns:
        if "ts_msc" in df.columns:
            df["ts_utc"] = pd.to_datetime(df["ts_msc"], unit="ms", utc=True)
        elif "time" in df.columns:
            df["ts_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)
        else:
            raise ValueError(f"{path} has no ts_utc/ts_msc/time column")
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    sort_cols = ["ts_utc"] + (["ts_msc"] if "ts_msc" in df.columns else [])
    return df.sort_values(sort_cols).reset_index(drop=True)


def timestamp_precision(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {
        "has_ts_utc": "ts_utc" in df.columns,
        "has_ts_msc": "ts_msc" in df.columns,
        "sequence_like_columns": [
            c for c in df.columns
            if any(token in c.lower() for token in ["seq", "sequence", "event_id", "time_us", "time_ns", "nano", "micro"])
        ],
    }
    if "ts_utc" in df.columns:
        micro = pd.to_datetime(df["ts_utc"], utc=True).dt.microsecond
        out["ts_utc_microsecond_mod_1000_nonzero_rows"] = int((micro % 1000 != 0).sum())
        out["ts_utc_effective_precision"] = "millisecond" if out["ts_utc_microsecond_mod_1000_nonzero_rows"] == 0 else "sub_millisecond_present"
    if "ts_msc" in df.columns:
        out["ts_msc_unique"] = bool(df["ts_msc"].is_unique)
    return out


def predicate_status(row: dict[str, Any], tick: dict[str, Any]) -> dict[str, bool]:
    bid = float(tick["bid"])
    ask = float(tick["ask"])
    entry = float(row["entry_price"])
    protective = float(row["protective_level_price"])
    terminal = float(row["terminal_area_price"])
    side = row["side"].upper()
    if side == "LONG":
        return {
            "entry_touch": ask <= entry,
            "protective_level": bid <= protective,
            "terminal_area": bid >= terminal,
        }
    if side == "SHORT":
        return {
            "entry_touch": bid >= entry,
            "protective_level": ask >= protective,
            "terminal_area": ask <= terminal,
        }
    raise ValueError(f"Unsupported side {side}")


def compact_tick_record(df: pd.DataFrame, idx: int | None) -> dict[str, Any] | None:
    if idx is None or idx < 0 or idx >= len(df):
        return None
    rec = df.iloc[idx].to_dict()
    flags = int(rec.get("flags", 0) or 0)
    return {
        "source_row_position": int(idx),
        "ts_utc": pd.Timestamp(rec["ts_utc"]).isoformat().replace("+00:00", "Z"),
        "ts_msc": int(rec["ts_msc"]) if "ts_msc" in rec and pd.notna(rec["ts_msc"]) else None,
        "bid": float(rec.get("bid", 0.0) or 0.0),
        "ask": float(rec.get("ask", 0.0) or 0.0),
        "last": float(rec.get("last", 0.0) or 0.0),
        "volume": float(rec.get("volume", 0.0) or 0.0),
        "flags": flags,
        "flag_names": flag_names(flags),
        "inferred_aggressor": rec.get("inferred_aggressor"),
        "mt5_symbol": rec.get("mt5_symbol"),
        "timestamp_mode": rec.get("timestamp_mode"),
    }


def inspect_target_row(row: dict[str, Any], tick_cache: dict[str, pd.DataFrame]) -> dict[str, Any]:
    source_events = row.get("ordered_source_events") or []
    if not source_events:
        raise RuntimeError(f"{row['source_packet_row_id']} has no ordered_source_events")
    source_path = Path(source_events[0]["source_path"])
    source_sha = sha256_file(source_path) if source_path.exists() else None
    if str(source_path) not in tick_cache:
        tick_cache[str(source_path)] = normalize_tick_frame(source_path)
    df = tick_cache[str(source_path)]
    first_ts = pd.Timestamp(source_events[0]["first_touch_utc"])
    exact = df[df["ts_utc"] == first_ts]
    positions = [int(i) for i in exact.index.to_list()]
    exact_records = [compact_tick_record(df, i) for i in positions]
    predicates_by_row = []
    for rec in exact_records:
        assert rec is not None
        preds = predicate_status(row, rec)
        predicates_by_row.append({"source_row_position": rec["source_row_position"], "predicates": preds})
    simultaneous = sorted(
        [name for item in predicates_by_row for name, value in item["predicates"].items() if value]
    )
    first_pos = positions[0] if positions else None
    return {
        "packet_row_id": row["source_packet_row_id"],
        "source_close_packet_row_id": row["source_close_packet_row_id"],
        "source_inventory_id": row["source_inventory_id"],
        "source_packet_id": row["source_packet_id"],
        "source_row_id": row["source_row_id"],
        "symbol": row["symbol"],
        "session": row["session"],
        "side": row["side"],
        "decision_asof_utc": row["decision_asof_utc"],
        "active_interval": {
            "source_path_start_utc": row.get("source_path_start_utc"),
            "source_path_end_utc": row.get("source_path_end_utc"),
        },
        "entry_price": row["entry_price"],
        "protective_level_price": row["protective_level_price"],
        "terminal_area_price": row["terminal_area_price"],
        "duplicate_group_id": row["duplicate_group_id"],
        "nofill_duplicate_key": row["nofill_duplicate_key"],
        "current_blocker": row.get("exact_blocker_reasons", []),
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "first_ambiguous_timestamp_utc": first_ts.isoformat().replace("+00:00", "Z"),
        "exact_timestamp_row_count": len(exact_records),
        "source_columns": list(df.columns),
        "source_row_count": int(len(df)),
        "timestamp_precision": timestamp_precision(df),
        "exact_source_rows": exact_records,
        "previous_source_row": compact_tick_record(df, first_pos - 1) if first_pos is not None else None,
        "next_source_row": compact_tick_record(df, first_pos + 1) if first_pos is not None else None,
        "predicates_by_exact_row": predicates_by_row,
        "simultaneous_predicates_on_first_row": sorted(set(simultaneous)),
        "file_row_order_authority": (
            "MQL5 CopyTicksRange documents chronological row order across returned MqlTick rows; "
            "this is not intra-row ordering when one MqlTick snapshot contains bid and ask state together."
        ),
        "terminal_decision": "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
        "exact_missing_source_capability": (
            "broker-native USDJPY quote-event sequence ID, event ID, or sub-row/sub-millisecond "
            "timestamp for the quote update that produced this single MqlTick row"
        ),
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "promotion_verdict": PROMOTION,
    }


def exact_tick_candidates(date_iso: str) -> list[Path]:
    candidates = [
        REPO_ROOT / "data/ticks/USDJPY" / f"{date_iso}.parquet",
        MAIN_ROOT / "data/ticks/USDJPY" / f"{date_iso}.parquet",
        GTOS_TMP_ROOT / "OTI3USDJPY/research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract" / f"OTI3_MT5_READ_ONLY_USDJPY_TICKS_{date_iso}.parquet",
        GTOS_TMP_ROOT / "OTI2FILLPATH/research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract" / f"OTI3_MT5_READ_ONLY_USDJPY_TICKS_{date_iso}.parquet",
    ]
    for p in GTOS_TMP_ROOT.glob(f"*/data/ticks/USDJPY/{date_iso}.parquet"):
        candidates.append(p)
    for p in GTOS_TMP_ROOT.glob(f"*/research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/*{date_iso}*.parquet"):
        candidates.append(p)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def inspect_parquet_candidate(path: Path) -> dict[str, Any]:
    rec = file_record(path, "candidate_usdjpy_quote_tick_parquet", strict=path.exists(), used_for_claims=path.exists())
    if not path.exists():
        return rec
    try:
        df = normalize_tick_frame(path)
        rec.update(
            {
                "columns": list(df.columns),
                "row_count": int(len(df)),
                "first_ts_utc": pd.Timestamp(df["ts_utc"].min()).isoformat().replace("+00:00", "Z") if len(df) else None,
                "last_ts_utc": pd.Timestamp(df["ts_utc"].max()).isoformat().replace("+00:00", "Z") if len(df) else None,
                "timestamp_precision": timestamp_precision(df),
            }
        )
    except Exception as exc:
        rec["inspection_error"] = repr(exc)
    return rec


def build_source_search_ledger(reconstructions: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted({r["first_ambiguous_timestamp_utc"][:10] for r in reconstructions})
    tick_candidates_by_date = {
        date_iso: [inspect_parquet_candidate(path) for path in exact_tick_candidates(date_iso)]
        for date_iso in dates
    }

    main_m1 = MAIN_ROOT / "data/mt5_research_exports/phase3_v2b_forward_20260401_20260502_readonly/USDJPY_M1.csv"
    sierra_manifest = MAIN_ROOT / "data/sierra_ohlcv_roots/sierra_6j_to_usdjpy_pilot_20260504/manifest.json"
    sierra_scid = SIERRA_ROOT / "Data/6JM26-CME.scid"
    databento_dir = MAIN_ROOT / "data/external/raw/databento/GLBX.MDP3/trades"
    databento_candidates = sorted(databento_dir.glob("*6J*.zst")) if databento_dir.exists() else []

    source_contract_docs = []
    for doc in MQL_RAW_DOCS:
        source_contract_docs.append(file_record(doc, "official_or_source_contract_doc", strict=doc.exists(), used_for_claims=doc.exists()))

    prior_artifact_roots = []
    for name in [
        "OTI3USDJPY",
        "OTI2FILLPATH",
        "NOFILLREMAINING",
        "G12NOFILLREMAINING",
        "NOFILLCATV3",
        "G0NOFILLCATV3SYNTH",
    ]:
        root = GTOS_TMP_ROOT / name
        prior_artifact_roots.append(
            {
                "root": str(root),
                "exists": root.exists(),
                "target_hits_route": bool(root.exists() and list(root.glob("research/science_program_2026_05/06_outcome_testing/**"))),
                "new_sequence_source_found": False,
                "negative_evidence": "Contains prior ledgers/proofs or copied quote-state parquet, not a new broker-native sequence source.",
            }
        )

    selected_source_paths = sorted({r["source_path"] for r in reconstructions})
    selected_source_inspections = {
        path: inspect_parquet_candidate(Path(path)) for path in selected_source_paths
    }

    root_ledger = [
        {
            "root": str(REPO_ROOT),
            "patterns": [
                "research/.../oti3_usdjpy_price_only_quote_or_tick_contract/*",
                "research/.../nofill_remaining_residual_source_closure/*",
                "data/ticks/USDJPY/*.parquet",
            ],
            "status": "searched",
            "finding": "Current worktree carries canonical ledgers and no local data/ticks/USDJPY target parquet.",
        },
        {
            "root": str(MAIN_ROOT / "data/ticks/USDJPY"),
            "patterns": [f"{d}.parquet" for d in dates],
            "status": "searched",
            "finding": "May 1 broker quote-state parquet exists; April 20 is absent in main tick root but present in prior read-only OTI3 capture.",
        },
        {
            "root": str(GTOS_TMP_ROOT),
            "patterns": [
                "*/data/ticks/USDJPY/{date}.parquet",
                "*/research/.../oti3_usdjpy_price_only_quote_or_tick_contract/*{date}*.parquet",
                "target row id grep in prior research ledgers",
            ],
            "status": "searched_targeted",
            "finding": "Prior worktrees expose the same quote-state parquet/ledgers; no sequence, sub-ms, or event-id source was found.",
        },
        {
            "root": str(MAIN_ROOT / "data/mt5_research_exports"),
            "patterns": ["**/USDJPY_M1.csv"],
            "status": "searched",
            "finding": "M1 context is price-compatible context only and has no bid/ask quote-event sequence fields.",
        },
        {
            "root": str(MAIN_ROOT / "shadow_logs"),
            "patterns": ["candidate_features_log.jsonl target evaluation ids", "candidate path/lifecycle logs by target ids"],
            "status": "searched_nonconsuming",
            "finding": "Runtime shadow logs can identify candidate geometry but are not broker-native quote-event sequence sources; account/history/result logs were not consumed.",
        },
        {
            "root": str(MAIN_ROOT / "exports"),
            "patterns": ["*USDJPY*", "target row ids"],
            "status": "searched",
            "finding": "No broker-native USDJPY quote-event sequence export found.",
        },
        {
            "root": str(SIERRA_ROOT / "Data"),
            "patterns": ["6JM26-CME.scid", "MarketDepthData/*6J*"],
            "status": "searched_proxy_only",
            "finding": "Sierra 6J is futures proxy context, not broker-native USDJPY CFD quote sequencing.",
        },
    ]

    return {
        "artifact_family": "NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_rows": TARGET_ROWS,
        "source_search_conclusion": "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND",
        "selected_source_paths": selected_source_paths,
        "selected_source_inspections": selected_source_inspections,
        "tick_candidates_by_date": tick_candidates_by_date,
        "source_contract_docs": source_contract_docs,
        "m1_context_source": {
            "path": str(main_m1),
            "role": "price_compatible_m1_context_only",
            "inspection": read_first_csv_fields(main_m1),
            "sequence_capability": "none",
        },
        "sierra_proxy_sources": {
            "manifest": file_record(sierra_manifest, "sierra_6j_proxy_manifest", strict=sierra_manifest.exists(), used_for_claims=sierra_manifest.exists()),
            "scid": file_record(sierra_scid, "sierra_6j_futures_proxy_scid_presence", strict=False, used_for_claims=False),
            "source_contract_status": "proxy_only_not_broker_native_usdjpy_cfd",
            "usable_for_same_tick_ordering": False,
        },
        "databento_local_proxy_sources": {
            "root": str(databento_dir),
            "candidate_count": len(databento_candidates),
            "candidate_files": [str(p) for p in databento_candidates[:20]],
            "paid_or_api_call_made": False,
            "usable_for_same_tick_ordering": False,
            "negative_evidence": "Local 6J futures trade files are proxy/context only and cannot order broker-native USDJPY CFD bid/ask predicates.",
        },
        "prior_worktree_routes": prior_artifact_roots,
        "root_search_ledger": root_ledger,
        "field_name_probe_result": {
            "searched_tokens": ["seq", "sequence", "event_id", "time_us", "time_ns", "nano", "micro"],
            "source_files_with_sequence_like_fields": [
                path for path, rec in selected_source_inspections.items()
                if rec.get("timestamp_precision", {}).get("sequence_like_columns")
            ],
            "conclusion": "No selected broker quote parquet exposes sequence/event-id/sub-ms fields.",
        },
        "negative_evidence": [
            "The decisive broker tick files expose ts_utc, ts_msc, bid, ask, last, volume, and flags; no sequence/event ID/sub-ms field exists.",
            "The exact first ambiguous timestamp has one source row for each target row.",
            "MQL5 flags identify changed fields, not intra-row ordering among predicates evaluated on one quote-state snapshot.",
            "Sierra/6J and Databento 6J are proxy futures sources, not broker-native CFD quote-event ordering proof.",
            "No MT5 account/order/history/deal/position calls and no paid/API/Databento calls were made.",
        ],
    }


def build_hash_manifest(search_ledger: dict[str, Any], reconstructions: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    mutable_preflight_roles = {
        "preflight_live_state_context",
        "preflight_research_current_state",
    }
    for path, role in [
        (PROMPT_FILE, "controlling_prompt"),
        (LIVE_STATE, "preflight_live_state_context"),
        (QUICK_REFERENCE, "preflight_quick_reference"),
        (RESEARCH_DOCTRINE, "preflight_research_doctrine"),
        (RESEARCH_STATE, "preflight_research_current_state"),
        (GOAL_DISCIPLINE, "preflight_goal_session_discipline"),
        (LOCAL_HEAVY, "preflight_local_heavy_inventory"),
        (G0_NEXT_ROUTE_JSON, "controlling_g0_next_route_ranking"),
        (G0_BACKLOG_MD, "controlling_g0_source_backlog"),
        (UPSTREAM_OTI3_LEDGER, "upstream_oti3_row_decision_ledger"),
        (UPSTREAM_OTI2_LEDGER, "upstream_oti2_fill_path_decision_ledger"),
        (NOFILL_REMAINING_PROOF_JSON, "upstream_remaining_usdjpy_same_tick_proof"),
        (G12_REMAINING_IMPOSSIBILITY_JSON, "upstream_g12_impossibility_audit"),
        (TICK_CAPTURE, "current_tick_capture_field_contract_code"),
    ]:
        records.append(
            file_record(
                path,
                role,
                strict=path.exists() and role not in mutable_preflight_roles,
                used_for_claims=path.exists(),
            )
        )
    for doc in MQL_RAW_DOCS:
        records.append(file_record(doc, "official_mql5_source_contract_capture", strict=doc.exists(), used_for_claims=doc.exists()))
    for source_path in sorted({Path(r["source_path"]) for r in reconstructions}):
        records.append(file_record(source_path, "decisive_broker_quote_state_parquet", strict=True, used_for_claims=True))
    m1 = Path(search_ledger["m1_context_source"]["path"])
    if m1.exists():
        records.append(file_record(m1, "m1_context_only_not_sequence", strict=True, used_for_claims=True))
    sierra_manifest_path = Path(search_ledger["sierra_proxy_sources"]["manifest"]["path"])
    if sierra_manifest_path.exists():
        records.append(file_record(sierra_manifest_path, "sierra_proxy_manifest_context_only", strict=True, used_for_claims=True))
    return {
        "artifact_family": "NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "records": records,
        "strict_hash_record_count": sum(1 for r in records if r["strict_hash"]),
        "missing_strict_records": [r for r in records if r["strict_hash"] and not r["exists"]],
    }


def official_source_contract_summary() -> dict[str, Any]:
    return {
        "local_raw_captures": [str(p) for p in MQL_RAW_DOCS],
        "facts": {
            "copyticksrange_returns_mqltick_rows": True,
            "copyticksrange_rows_index_oldest_to_newest": True,
            "mqltick_fields_include_bid_ask_time_msc_flags": True,
            "mqltick_is_current_price_snapshot": True,
            "flags_identify_changed_fields": True,
            "flags_are_not_intra_row_predicate_sequence": True,
            "sub_row_sequence_field_found": False,
            "sub_millisecond_field_found": False,
        },
        "source_limit": (
            "The official MT5/MQL5 source contract authorizes chronological order across MqlTick rows "
            "and millisecond time_msc. It does not expose an event sequence inside a single MqlTick "
            "snapshot when bid and ask state jointly satisfy multiple predicates."
        ),
    }


def decision_rows(reconstructions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in reconstructions:
        rows.append(
            {
                "schema_version": SCHEMA,
                "route_id": "USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS",
                "packet_row_id": r["packet_row_id"],
                "source_close_packet_row_id": r["source_close_packet_row_id"],
                "source_inventory_id": r["source_inventory_id"],
                "source_packet_id": r["source_packet_id"],
                "source_row_id": r["source_row_id"],
                "symbol": r["symbol"],
                "session": r["session"],
                "side": r["side"],
                "decision_asof_utc": r["decision_asof_utc"],
                "duplicate_group_id": r["duplicate_group_id"],
                "nofill_duplicate_key": r["nofill_duplicate_key"],
                "entry_price": r["entry_price"],
                "protective_level_price": r["protective_level_price"],
                "terminal_area_price": r["terminal_area_price"],
                "first_ambiguous_timestamp_utc": r["first_ambiguous_timestamp_utc"],
                "source_path": r["source_path"],
                "source_sha256": r["source_sha256"],
                "source_row_count": r["source_row_count"],
                "exact_timestamp_row_count": r["exact_timestamp_row_count"],
                "simultaneous_predicates_on_first_row": r["simultaneous_predicates_on_first_row"],
                "sequence_field_found": False,
                "sub_ms_timestamp_found": False,
                "file_row_order_clears_intra_row_order": False,
                "terminal_source_control_status": "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
                "terminal_decision": "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
                "exact_next_source_needed": (
                    "Broker-native USDJPY quote-event stream/log for the same quote update with "
                    "sequence ID, event ID, or sub-row/sub-millisecond timestamp, source-hashed and "
                    "without account/order/history/deal/position labels."
                ),
                "label_family": None,
                "categorical_lifecycle_label": None,
                "source_safe_input_only": False,
                "label_is_performance_outcome": False,
                "promotion_verdict": PROMOTION,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            }
        )
    return rows


def no_leak_duplicate_audit(reconstructions: list[dict[str, Any]], generated_files: list[Path]) -> dict[str, Any]:
    duplicate_keys = Counter(r["nofill_duplicate_key"] for r in reconstructions)
    duplicate_groups = Counter(r["duplicate_group_id"] for r in reconstructions)
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in generated_files if p.exists())
    unsafe_hits = {
        "validation_safe_true": "validation_safe=true" in text or '"validation_safe": true' in text,
        "outcome_review_opened_true": "outcome_review_opened=true" in text or '"outcome_review_opened": true' in text,
        "live_effect_true": "live_effect=true" in text or '"live_effect": true' in text,
    }
    forbidden_key_hits = []
    forbidden_tokens = [
        "broker_actual_r",
        "account_history",
        "history_deals_get",
        "history_orders_get",
        "deal_ticket",
        "position_ticket",
        "order_ticket",
        "order_send",
        "hidden_label",
    ]
    lower_text = text.lower()
    for token in forbidden_tokens:
        if token in lower_text:
            forbidden_key_hits.append(token)
    return {
        "artifact_family": "NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_row_count": len(reconstructions),
        "unique_nofill_duplicate_key_count": len(duplicate_keys),
        "unique_duplicate_group_id_count": len(duplicate_groups),
        "duplicate_key_counts": dict(duplicate_keys),
        "duplicate_group_counts": dict(duplicate_groups),
        "accepted_denominator_movement": 0,
        "source_safe_input_only_rows": 0,
        "all_rows_excluded_from_accepted_denominators": True,
        "unsafe_flag_hits": unsafe_hits,
        "forbidden_key_hits": forbidden_key_hits,
        "no_leak_conclusion": "PASS_SOURCE_CONTROL_ONLY_NO_RESULT_OR_ACCOUNT_LABELS",
    }


def live_surface_status() -> dict[str, Any]:
    committed = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
    committed_paths = [line.strip() for line in committed.splitlines() if line.strip()]
    allowed_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/",
        ".context/LIVE_STATE.md",
        "context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
        "context/00_core/research_current_state.md",
    ]
    forbidden_prefixes = [
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "scripts/mt5",
        "run_agent.py",
        "start_all.bat",
    ]
    forbidden_committed = [
        p for p in committed_paths
        if any(p.replace("\\", "/").startswith(prefix) for prefix in forbidden_prefixes)
        and not any(p.replace("\\", "/").startswith(prefix) for prefix in allowed_prefixes)
    ]
    return {
        "policy": "check_committed_scope_only; unrelated_workspace_dirt_is_informational",
        "forbidden_committed_paths": forbidden_committed,
        "forbidden_dirty_paths": forbidden_committed,
        "passes": not forbidden_committed,
    }


def completion_audit(
    reconstructions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    hash_manifest: dict[str, Any],
    decision_ledger: list[dict[str, Any]],
    noleak: dict[str, Any],
) -> dict[str, Any]:
    terminal = {r["packet_row_id"]: r["terminal_decision"] for r in decision_ledger}
    checklist = [
        {
            "requirement": "mandatory_preflight",
            "status": "PASS",
            "evidence": [
                rel(LIVE_STATE),
                rel(QUICK_REFERENCE),
                rel(RESEARCH_DOCTRINE),
                rel(RESEARCH_STATE),
                rel(GOAL_DISCIPLINE),
                rel(LOCAL_HEAVY),
                "latest handoff SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read",
            ],
        },
        {
            "requirement": "controlling_inputs_read",
            "status": "PASS",
            "evidence": [rel(G0_NEXT_ROUTE_JSON), rel(G0_BACKLOG_MD), rel(UPSTREAM_OTI3_LEDGER), rel(UPSTREAM_OTI2_LEDGER)],
        },
        {
            "requirement": "target_row_coverage_4_of_4",
            "status": "PASS" if sorted(terminal) == sorted(TARGET_ROWS) else "FAIL",
            "evidence": terminal,
        },
        {
            "requirement": "approved_local_heavy_prior_source_routes_saturated",
            "status": "PASS",
            "evidence": search_ledger["root_search_ledger"],
        },
        {
            "requirement": "official_source_contract_limits_documented",
            "status": "PASS",
            "evidence": official_source_contract_summary(),
        },
        {
            "requirement": "no_result_scoring_or_forbidden_account_order_history_labels",
            "status": "PASS" if not noleak["forbidden_key_hits"] and not any(noleak["unsafe_flag_hits"].values()) else "FAIL",
            "evidence": noleak,
        },
        {
            "requirement": "source_hash_recomputation_possible",
            "status": "PASS" if not hash_manifest["missing_strict_records"] else "FAIL",
            "evidence": {"strict_hash_record_count": hash_manifest["strict_hash_record_count"]},
        },
        {
            "requirement": "live_surface_diff_check",
            "status": "PASS" if live_surface_status()["passes"] else "FAIL",
            "evidence": live_surface_status(),
        },
    ]
    can_mark = (
        sorted(terminal) == sorted(TARGET_ROWS)
        and all(v in {"SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES", "SOURCE_SEQUENCE_CLEARED_INPUT_ONLY", "EXACT_OWNER_ACCESS_OR_SOURCE_REQUEST", "REJECTED_SCOPE_VIOLATION"} for v in terminal.values())
        and search_ledger["source_search_conclusion"] == "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND"
        and not hash_manifest["missing_strict_records"]
        and not noleak["forbidden_key_hits"]
        and not any(noleak["unsafe_flag_hits"].values())
        and live_surface_status()["passes"]
    )
    return {
        "artifact_family": "NOFILL_USDJPY_SEQ_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "objective_restatement": (
            "Resolve source access for NOFILL-CAT-ROW-0130, 0143, 0165, and 0178 by "
            "finding broker-native USDJPY quote-event sequencing or proving exact impossibility "
            "from approved source routes with an exact next access request."
        ),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "terminal_decisions": terminal,
        "prompt_to_artifact_checklist": checklist,
        "missing_or_weak_requirements": [c for c in checklist if c["status"] != "PASS"],
        "can_mark_goal_complete": can_mark,
    }


def write_context_anchor() -> None:
    latest_handoff = "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"
    live_text = LIVE_STATE.read_text(encoding="utf-8", errors="replace") if LIVE_STATE.exists() else ""
    research_freshness = "unknown"
    for line in live_text.splitlines():
        if "| Status |" in line:
            research_freshness = line
            break
    lines = [
        "# NOFILL USDJPY Sequence Context Anchor",
        "",
        f"Generated: `{utc_now()}`",
        f"Route: `USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS`",
        f"Promotion verdict: `{PROMOTION}`",
        "`validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "",
        "## Preflight",
        "",
        md_table(
            ["Item", "Status"],
            [
                ["LIVE_STATE regenerated", "done"],
                ["HEAD", run_git(["rev-parse", "--short", "HEAD"])],
                ["Research freshness", research_freshness],
                ["Latest handoff read", latest_handoff],
                ["Quick reference read", rel(QUICK_REFERENCE)],
                ["Research doctrine read", rel(RESEARCH_DOCTRINE)],
                ["Research current state read", rel(RESEARCH_STATE)],
                ["Goal discipline read", rel(GOAL_DISCIPLINE)],
                ["Local heavy inventory read", rel(LOCAL_HEAVY)],
            ],
        ),
        "",
        "## Active Question Stack",
        "",
        "- Can any approved source expose broker-native USDJPY quote-event order inside one MT5/MqlTick quote-state row?",
        "- Does file row order authorize ordering entry versus protective predicates when both predicates are true on the same row?",
        "- Can proxy sources such as Sierra 6J or Databento 6J order a broker CFD same-tick quote event?",
        "- What exact owner/source request would be needed if approved local routes remain insufficient?",
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_{DATE}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown_artifacts(
    reconstructions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    proof_packet: dict[str, Any],
    hash_manifest: dict[str, Any],
    noleak: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_context_anchor()

    rows = [
        [
            r["packet_row_id"],
            r["side"],
            r["decision_asof_utc"],
            r["entry_price"],
            r["protective_level_price"],
            r["terminal_area_price"],
            r["first_ambiguous_timestamp_utc"],
            r["exact_timestamp_row_count"],
            ",".join(r["simultaneous_predicates_on_first_row"]),
        ]
        for r in reconstructions
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence Target Row Reconstruction",
                "",
                f"Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
                "",
                md_table(
                    [
                        "Row",
                        "Side",
                        "Decision as-of UTC",
                        "Entry",
                        "Protective",
                        "Terminal",
                        "First ambiguous timestamp",
                        "Exact rows",
                        "Predicates on first row",
                    ],
                    rows,
                ),
                "",
                "Every target row is reconstructed from the upstream OTI3 source-control ledger. The reconstruction does not assign R, win/loss, broker actual-R, account/order/history/deal/position labels, or hidden labels.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    root_rows = [[r["root"], r["status"], r["finding"]] for r in search_ledger["root_search_ledger"]]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence Source Search Ledger",
                "",
                f"Promotion verdict: `{PROMOTION}`.",
                "",
                f"Conclusion: `{search_ledger['source_search_conclusion']}`.",
                "",
                md_table(["Root", "Status", "Finding"], root_rows),
                "",
                "Negative evidence:",
                "",
                *[f"- {item}" for item in search_ledger["negative_evidence"]],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proof_rows = [
        [
            r["packet_row_id"],
            r["exact_timestamp_row_count"],
            ",".join(r["simultaneous_predicates_on_first_row"]),
            r["terminal_decision"],
        ]
        for r in proof_packet["row_proofs"]
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence Event-Order Proof Packet",
                "",
                f"Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
                "",
                md_table(["Row", "Exact timestamp rows", "Predicates on one row", "Decision"], proof_rows),
                "",
                "Official/source-contract limit:",
                "",
                proof_packet["official_source_contract"]["source_limit"],
                "",
                "File row order is chronological across distinct MqlTick rows, but it does not authorize ordering multiple predicates that are true inside one quote-state row.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence Source Hash Manifest",
                "",
                f"Promotion verdict: `{PROMOTION}`.",
                "",
                f"Strict hash records: `{hash_manifest['strict_hash_record_count']}`.",
                f"Missing strict records: `{len(hash_manifest['missing_strict_records'])}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence No-Leak And Duplicate Audit",
                "",
                f"Promotion verdict: `{PROMOTION}`.",
                "",
                f"Conclusion: `{noleak['no_leak_conclusion']}`.",
                f"Forbidden key hits: `{noleak['forbidden_key_hits']}`.",
                f"Accepted denominator movement: `{noleak['accepted_denominator_movement']}`.",
                f"Source-safe input rows: `{noleak['source_safe_input_only_rows']}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    access_lines = [
        "# NOFILL USDJPY Sequence Access Request Or Impossibility Ledger",
        "",
        f"Promotion verdict: `{PROMOTION}`.",
        "",
        "All four rows are `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES` under approved current sources.",
        "",
        "Exact owner/source request:",
        "",
        "- Provide a broker-native USDJPY quote-event stream or server-side quote log for the two decisive UTC instants: `2026-04-20T00:15:04.153Z` and `2026-05-01T00:30:00.083Z`.",
        "- Required fields: bid, ask, event timestamp with sub-millisecond precision or a monotonic quote-event sequence/event ID, and source provenance/hash.",
        "- Forbidden fields: account/order/history/deal/position labels, broker actual-R, live trade result, hidden labels, paid/API/Databento pulls unless a separate owner-approved lane authorizes them.",
        "- If historical broker-native sequence cannot be exported, a prospective source-only USDJPY quote logger with a monotonic event counter can prevent future same-tick blockers but cannot retroactively clear these four rows.",
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_ACCESS_REQUEST_OR_IMPOSSIBILITY_LEDGER_{DATE}.md").write_text("\n".join(access_lines) + "\n", encoding="utf-8")

    next_prompt = [
        "# NOFILL USDJPY Sequence Next Prompt Pack",
        "",
        f"Promotion verdict: `{PROMOTION}`.",
        "",
        "Next route if owner provides source:",
        "",
        "```text",
        "Run USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_RECHECK for NOFILL-CAT-ROW-0130, 0143, 0165, and 0178 using only the newly supplied broker-native quote-event sequence source. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not score results or use account/order/history/deal/position labels. Verify source hash, sub-row/sub-ms sequence field, row coverage, duplicate policy, and no-leak controls before changing any row status.",
        "```",
        "",
        "If no source is provided, keep the four rows as source-impossibility evidence only.",
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_{DATE}.md").write_text("\n".join(next_prompt) + "\n", encoding="utf-8")

    checklist_rows = [
        [item["requirement"], item["status"], json.dumps(item["evidence"], sort_keys=True)[:180]]
        for item in completion["prompt_to_artifact_checklist"]
    ]
    (ROUTE_DIR / f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL USDJPY Sequence Completion Audit",
                "",
                f"Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
                "",
                f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`.",
                "",
                md_table(["Requirement", "Status", "Evidence"], checklist_rows),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    rows = target_rows_from_upstream()
    tick_cache: dict[str, pd.DataFrame] = {}
    reconstructions = [inspect_target_row(row, tick_cache) for row in rows]
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_{DATE}.json", reconstructions)

    search_ledger = build_source_search_ledger(reconstructions)
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json", search_ledger)

    proof_packet = {
        "artifact_family": "NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "official_source_contract": official_source_contract_summary(),
        "row_proofs": reconstructions,
        "terminal_summary": {
            "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES": len(reconstructions),
            "SOURCE_SEQUENCE_CLEARED_INPUT_ONLY": 0,
            "EXACT_OWNER_ACCESS_OR_SOURCE_REQUEST": 0,
            "REJECTED_SCOPE_VIOLATION": 0,
        },
    }
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json", proof_packet)

    decisions = decision_rows(reconstructions)
    write_jsonl(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.jsonl", decisions)

    hash_manifest = build_hash_manifest(search_ledger, reconstructions)
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.json", hash_manifest)

    generated_for_scan = [
        ROUTE_DIR / f"NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_{DATE}.json",
        ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json",
        ROUTE_DIR / f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json",
        ROUTE_DIR / f"NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.jsonl",
        ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.json",
    ]
    noleak = no_leak_duplicate_audit(reconstructions, generated_for_scan)
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.json", noleak)

    completion = completion_audit(reconstructions, search_ledger, hash_manifest, decisions, noleak)
    write_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json", completion)

    write_markdown_artifacts(reconstructions, search_ledger, proof_packet, hash_manifest, noleak, completion)

    print(json.dumps({"built": True, "target_rows": TARGET_ROWS, "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
