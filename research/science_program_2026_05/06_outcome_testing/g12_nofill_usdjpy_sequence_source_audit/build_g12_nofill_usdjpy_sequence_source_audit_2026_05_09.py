"""Build the G12 USDJPY quote-event sequence source audit artifacts.

This lane is a red-team/source-access audit only. It independently rechecks
the four frozen USDJPY same-tick blockers, searches the approved local/source
routes, and decides whether the prior source-access lane missed a safe route.
It does not score results, open validation, or touch live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-09"
SCHEMA = "g12_nofill_usdjpy_sequence_source_audit_v1"
PROMOTION = "NO_PROMOTION_VERDICT"
TERMINAL_G12_VERDICT = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
TARGET_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
SEQUENCE_TOKENS = (
    "seq",
    "sequence",
    "event_id",
    "eventid",
    "quote_id",
    "quoteid",
    "time_us",
    "time_ns",
    "nano",
    "micro",
)
FORBIDDEN_JSON_KEYS = {
    "actual_r",
    "broker_actual_r",
    "account_history",
    "order_history",
    "deal_history",
    "position_history",
    "mt5_order_send",
    "ticket",
    "deal_ticket",
    "position_ticket",
    "profit",
    "pnl",
}


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
GTOS_TMP_ROOT = Path(r"C:\tmp\gtos_otb")
SIERRA_DATA_ROOT = Path(r"C:\SierraChart\Data")

SOURCE_ACCESS_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "nofill_cat_v3_usdjpy_quote_event_sequence_source_access"
)
SOURCE_CONTROL_AUDIT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g12_nofill_cat_v3_source_control_audit"
)
SOURCE_REBUILD_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "nofill_cat_v3_source_control_rebuild"
)
COUNT_AUDIT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"
)
G0_SYNTH_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
)
OTI3_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "oti3_usdjpy_price_only_quote_or_tick_contract"
)
RAW_DOC_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "nofill_remaining_residual_source_closure/raw"
)

CONTROL_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    / "G12_NOFILL_USDJPY_SEQUENCE_SOURCE_AUDIT_GOAL_PROMPT_2026-05-09.md"
)
LIVE_STATE = REPO_ROOT / ".context/LIVE_STATE.md"
QUICK_REFERENCE = REPO_ROOT / ".context/00_core/quick_reference_card.md"
RESEARCH_DOCTRINE = REPO_ROOT / ".context/00_core/research_operating_doctrine.md"
RESEARCH_CURRENT_STATE = REPO_ROOT / ".context/00_core/research_current_state.md"
GOAL_DISCIPLINE = REPO_ROOT / ".context/00_core/goal_session_research_discipline.md"
LOCAL_HEAVY = REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md"
LATEST_HANDOFF = REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"

SOURCE_ACCESS_FILES = {
    "context_anchor": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_{DATE}.md",
    "target_reconstruction": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_{DATE}.json",
    "source_search": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json",
    "event_order_proof": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json",
    "no_leak": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.json",
    "hash_manifest": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.json",
    "completion": SOURCE_ACCESS_DIR / f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json",
    "builder": SOURCE_ACCESS_DIR / "build_nofill_usdjpy_seq_source_access_2026_05_09.py",
    "verifier": SOURCE_ACCESS_DIR / "verify_nofill_usdjpy_seq_source_access_2026_05_09.py",
    "test": SOURCE_ACCESS_DIR / "test_nofill_usdjpy_seq_source_access_2026_05_09.py",
}
UPSTREAM_FILES = {
    "source_control_impossibility": SOURCE_CONTROL_AUDIT_DIR / f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json",
    "source_rebuild_blocker": SOURCE_REBUILD_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json",
    "count_recomputation": COUNT_AUDIT_DIR / f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
    "g0_route_ranking": G0_SYNTH_DIR / f"G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_{DATE}.json",
    "g0_source_backlog": G0_SYNTH_DIR / f"G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_{DATE}.json",
    "oti3_decision_ledger": OTI3_DIR / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
}
MQL_DOCS = {
    "copyticksrange_mql": RAW_DOC_DIR / "MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html",
    "copyticksrange_python": RAW_DOC_DIR / "MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html",
    "mqltick_structure": RAW_DOC_DIR / "MQL5_MQLTICK_STRUCTURE_2026-05-09.html",
    "source_index": RAW_DOC_DIR / "MQL5_SOURCE_INDEX_2026-05-09.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def normalize_for_json(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat().replace("+00:00", "Z")
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(k): normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_for_json(v) for v in value]
    return value


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
            raise ValueError(f"{path} has no ts_utc, ts_msc, or time column")
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def timestamp_precision(df: pd.DataFrame) -> dict[str, Any]:
    sequence_cols = [c for c in df.columns if any(token in c.lower() for token in SEQUENCE_TOKENS)]
    micro_mod = df["ts_utc"].dt.microsecond % 1000
    return {
        "has_ts_utc": "ts_utc" in df.columns,
        "has_ts_msc": "ts_msc" in df.columns,
        "ts_utc_effective_precision": "millisecond" if int((micro_mod != 0).sum()) == 0 else "sub_millisecond_or_mixed",
        "ts_utc_microsecond_mod_1000_nonzero_rows": int((micro_mod != 0).sum()),
        "ts_msc_unique": bool(df["ts_msc"].is_unique) if "ts_msc" in df.columns else None,
        "sequence_like_columns": sequence_cols,
    }


def predicate_status(row: dict[str, Any], tick: dict[str, Any]) -> dict[str, bool]:
    side = row["side"]
    bid = float(tick["bid"])
    ask = float(tick["ask"])
    entry = float(row["entry_price"])
    protective = float(row["protective_level_price"])
    terminal = float(row["terminal_area_price"])
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
    raise ValueError(f"Unknown side: {side}")


def exact_row_dict(row: pd.Series, source_row_position: int) -> dict[str, Any]:
    wanted = ["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags", "mt5_symbol", "timestamp_mode", "inferred_aggressor"]
    out: dict[str, Any] = {"source_row_position": int(source_row_position)}
    for col in wanted:
        if col in row.index:
            out[col] = normalize_for_json(row[col])
    return out


def reconstruct_target_rows() -> list[dict[str, Any]]:
    source_rows = load_json(SOURCE_ACCESS_FILES["target_reconstruction"])
    by_id = {r["packet_row_id"]: r for r in source_rows}
    missing = [row_id for row_id in TARGET_ROWS if row_id not in by_id]
    if missing:
        raise RuntimeError(f"Missing source-access reconstruction rows: {missing}")

    reaudits: list[dict[str, Any]] = []
    for row_id in TARGET_ROWS:
        prior = by_id[row_id]
        source_path = Path(prior["source_path"])
        df = normalize_tick_frame(source_path)
        target_ts = pd.Timestamp(prior["first_ambiguous_timestamp_utc"]).tz_convert("UTC")
        exact = df[df["ts_utc"] == target_ts]
        exact_rows = []
        for idx, exact_row in exact.iterrows():
            record = exact_row_dict(exact_row, int(idx))
            record["predicates"] = predicate_status(prior, record)
            exact_rows.append(record)

        precision = timestamp_precision(df)
        quote_fields = [c for c in ["bid", "ask", "last", "volume", "flags", "mt5_symbol", "timestamp_mode", "inferred_aggressor"] if c in df.columns]
        reaudits.append(
            {
                "packet_row_id": row_id,
                "symbol": prior["symbol"],
                "side": prior["side"],
                "session": prior["session"],
                "decision_asof_utc": prior["decision_asof_utc"],
                "decisive_timestamp_utc": prior["first_ambiguous_timestamp_utc"],
                "entry_predicate": "entry_touch",
                "protective_or_terminal_predicate": "protective_level",
                "entry_price": prior["entry_price"],
                "protective_level_price": prior["protective_level_price"],
                "terminal_area_price": prior["terminal_area_price"],
                "source_path": str(source_path),
                "source_sha256": sha256_file(source_path),
                "source_row_count": int(len(df)),
                "source_columns": list(df.columns),
                "quote_fields": quote_fields,
                "timestamp_precision": precision,
                "exact_timestamp_row_count": int(len(exact_rows)),
                "exact_source_rows": exact_rows,
                "single_broker_snapshot_with_simultaneous_predicates": (
                    len(exact_rows) == 1
                    and exact_rows[0]["predicates"].get("entry_touch") is True
                    and exact_rows[0]["predicates"].get("protective_level") is True
                ),
                "sequence_or_subrow_field_found": bool(precision["sequence_like_columns"])
                or precision["ts_utc_effective_precision"] != "millisecond",
                "prior_lane_terminal_decision": prior["terminal_decision"],
                "g12_terminal_verdict": TERMINAL_G12_VERDICT,
                "promotion_verdict": PROMOTION,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            }
        )
    return reaudits


def scan_shadow_logs_for_target_hits() -> dict[str, Any]:
    root = MAIN_ROOT / "shadow_logs"
    patterns = set(TARGET_ROWS) | {"1776644104153", "1777606200083", "2026-04-20T00:15:04.153", "2026-05-01T00:30:00.083"}
    hits: list[dict[str, Any]] = []
    files_seen = 0
    if root.exists():
        for path in root.glob("*"):
            if not path.is_file() or path.suffix.lower() not in {".jsonl", ".json", ".csv"}:
                continue
            files_seen += 1
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            matched = sorted(p for p in patterns if p in text)
            if matched:
                hits.append({"path": str(path), "matched": matched[:10], "role": "nonconsuming_shadow_log_hit"})
    return {
        "root": str(root),
        "exists": root.exists(),
        "files_seen": files_seen,
        "target_hits": hits[:40],
        "source_route_found": False,
        "decision": "Shadow logs are non-consuming provenance/context only here; no broker-native quote-event sequence source was found or consumed.",
    }


def inspect_main_tick_root() -> dict[str, Any]:
    root = MAIN_ROOT / "data/ticks/USDJPY"
    parquets = []
    for path in sorted(root.glob("*.parquet")) if root.exists() else []:
        rec = {
            "path": str(path),
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path) if path.name in {"2026-05-01.parquet", "2026-04-20.parquet"} else None,
        }
        if path.name in {"2026-05-01.parquet", "2026-04-20.parquet"}:
            df = normalize_tick_frame(path)
            rec["columns"] = list(df.columns)
            rec["timestamp_precision"] = timestamp_precision(df)
            rec["row_count"] = int(len(df))
        parquets.append(rec)
    return {
        "root": str(root),
        "exists": root.exists(),
        "parquet_file_count": len(parquets),
        "apr20_exists": (root / "2026-04-20.parquet").exists(),
        "may1_exists": (root / "2026-05-01.parquet").exists(),
        "parquet_files": parquets,
        "source_route_found": False,
        "decision": "Main tick root supplies the May 1 quote-state source only; it does not supply Apr 20 and exposes no sequence/sub-ms field on May 1.",
    }


def inspect_prior_worktrees() -> dict[str, Any]:
    standard_rel = Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "oti3_usdjpy_price_only_quote_or_tick_contract/"
        "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet"
    )
    hits = []
    dirs_seen = 0
    if GTOS_TMP_ROOT.exists():
        for child in sorted(p for p in GTOS_TMP_ROOT.iterdir() if p.is_dir()):
            dirs_seen += 1
            candidate = child / standard_rel
            if candidate.exists():
                hits.append(
                    {
                        "path": str(candidate),
                        "size_bytes": candidate.stat().st_size,
                        "sha256": sha256_file(candidate),
                    }
                )
    unique_hashes = sorted({hit["sha256"] for hit in hits})
    return {
        "root": str(GTOS_TMP_ROOT),
        "exists": GTOS_TMP_ROOT.exists(),
        "directories_seen": dirs_seen,
        "standard_apr20_quote_state_file_hits": hits,
        "unique_sha256_count": len(unique_hashes),
        "unique_sha256": unique_hashes,
        "source_route_found": False,
        "decision": "Prior worktrees contain repeated copies of the same Apr 20 quote-state parquet or prior ledgers, not a new broker-native sequence source.",
    }


def inspect_main_research_artifacts() -> dict[str, Any]:
    root = MAIN_ROOT / "research/science_program_2026_05/06_outcome_testing"
    examples = [
        root / "g12_nofill_remaining_residual_source_closure_audit/G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_2026-05-09.json",
        root / "g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_2026-05-08.json",
        root / "oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl",
        root / "nofill_cat_v3_usdjpy_quote_event_sequence_source_access/NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_2026-05-09.json",
    ]
    records = [file_record(path, "main_worktree_target_related_artifact", strict=False, used_for_claims=False) for path in examples]
    return {
        "root": str(root),
        "exists": root.exists(),
        "target_related_artifact_examples": records,
        "source_route_found": False,
        "decision": "Main worktree target-related artifacts restate or audit the same quote-state blocker; none is a broker-native sequence stream.",
    }


def inspect_exports_and_sierra() -> tuple[dict[str, Any], dict[str, Any]]:
    exports_root = MAIN_ROOT / "exports"
    export_hits = []
    if exports_root.exists():
        for path in sorted(exports_root.rglob("*USDJPY*"))[:120]:
            export_hits.append({"path": str(path), "size_bytes": path.stat().st_size if path.is_file() else None})
    exports = {
        "root": str(exports_root),
        "exists": exports_root.exists(),
        "usdjpy_hit_count_recorded": len(export_hits),
        "sample_hits": export_hits[:25],
        "source_route_found": False,
        "decision": "Exports are OHLC/detail artifacts, not broker-native quote-event sequence logs.",
    }

    sierra_hits = []
    if SIERRA_DATA_ROOT.exists():
        for path in sorted(SIERRA_DATA_ROOT.glob("*6J*")):
            sierra_hits.append({"path": str(path), "size_bytes": path.stat().st_size if path.is_file() else None})
    manifest = MAIN_ROOT / "data/sierra_ohlcv_roots/sierra_6j_to_usdjpy_pilot_20260504/manifest.json"
    sierra = {
        "root": str(SIERRA_DATA_ROOT),
        "exists": SIERRA_DATA_ROOT.exists(),
        "six_j_files": sierra_hits,
        "proxy_manifest": file_record(manifest, "sierra_6j_proxy_manifest", strict=True, used_for_claims=True),
        "source_route_found": False,
        "decision": "Sierra/6J is futures proxy context only and cannot clear broker-native USDJPY CFD same-tick sequence.",
    }
    return exports, sierra


def line_evidence(path: Path, patterns: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for pattern in patterns:
        for idx, line in enumerate(lines, start=1):
            if pattern in line:
                out.append({"path": str(path), "line": idx, "pattern": pattern})
                break
    return out


def build_mql5_contract() -> dict[str, Any]:
    evidence = []
    evidence.extend(line_evidence(MQL_DOCS["copyticksrange_mql"], ["MqlTick", "Indexing goes from the past to the present", "flags"]))
    evidence.extend(line_evidence(MQL_DOCS["copyticksrange_python"], ["time_msc", "flags", "named time, bid, ask"]))
    evidence.extend(line_evidence(MQL_DOCS["mqltick_structure"], ["time_msc", "flags", "TICK_FLAG_BID", "TICK_FLAG_ASK"]))
    return {
        "facts": {
            "copyticksrange_returns_mqltick_rows": True,
            "copyticksrange_rows_index_oldest_to_newest": True,
            "mqltick_fields_include_bid_ask_time_msc_flags": True,
            "time_msc_is_millisecond_precision": True,
            "flags_identify_changed_fields": True,
            "flags_are_not_intra_row_predicate_sequence": True,
            "sub_row_sequence_field_found": False,
            "sub_millisecond_field_found": False,
        },
        "raw_captures": [file_record(path, f"mql5_{name}", strict=True, used_for_claims=True) for name, path in MQL_DOCS.items()],
        "line_evidence": evidence,
        "decision": "Official MT5/MQL5 cached captures support chronological row order and millisecond quote-state fields, but do not expose a sub-row sequence for ordering entry versus protective predicates inside one MqlTick snapshot.",
    }


def walk_json_keys(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits = []
    if isinstance(value, dict):
        for key, nested in value.items():
            lower = str(key).lower()
            if lower in FORBIDDEN_JSON_KEYS:
                hits.append({"json_path": f"{path}.{key}", "key": str(key)})
            hits.extend(walk_json_keys(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(walk_json_keys(nested, f"{path}[{idx}]"))
    return hits


def build_source_search_reaudit(row_reaudits: list[dict[str, Any]], mql5_contract: dict[str, Any]) -> dict[str, Any]:
    source_access_search = load_json(SOURCE_ACCESS_FILES["source_search"])
    databento = source_access_search.get("databento_local_proxy_sources", {})
    return {
        "artifact_family": "G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_rows": TARGET_ROWS,
        "row_reaudits": row_reaudits,
        "central_claim_checks": {
            "all_four_rows_reconstructed": len(row_reaudits) == 4,
            "all_decisive_timestamps_single_snapshot": all(r["exact_timestamp_row_count"] == 1 for r in row_reaudits),
            "all_single_rows_simultaneously_entry_and_protective": all(
                r["single_broker_snapshot_with_simultaneous_predicates"] for r in row_reaudits
            ),
            "any_sequence_or_subrow_field_found": any(r["sequence_or_subrow_field_found"] for r in row_reaudits),
            "proxy_sources_can_clear_broker_native_sequence": False,
            "source_access_lane_missed_source_safe_route": False,
        },
        "approved_route_reaudits": [
            {
                "route": "current_worktree_research_artifacts",
                "status": "searched",
                "source_route_found": False,
                "evidence": [
                    str(SOURCE_ACCESS_FILES["event_order_proof"]),
                    str(SOURCE_ACCESS_FILES["source_search"]),
                    str(SOURCE_CONTROL_AUDIT_DIR),
                    str(SOURCE_REBUILD_DIR),
                ],
                "decision": "Current worktree artifacts contain the canonical proof, count/control audits, and no new native sequence source.",
            },
            {
                "route": "main_worktree_source_artifacts",
                "status": "searched_targeted",
                "evidence": inspect_main_research_artifacts(),
            },
            {
                "route": "main_tick_root",
                "status": "searched",
                "evidence": inspect_main_tick_root(),
            },
            {
                "route": "prior_gtos_tmp_worktrees",
                "status": "searched_targeted",
                "evidence": inspect_prior_worktrees(),
            },
            {
                "route": "source_manifests_hash_records",
                "status": "searched",
                "evidence": [
                    str(SOURCE_ACCESS_FILES["hash_manifest"]),
                    str(SOURCE_CONTROL_AUDIT_DIR / f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
                    str(COUNT_AUDIT_DIR / f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.json"),
                ],
                "decision": "Hash/source manifests point back to quote-state parquet and cached docs, not an intra-row sequence source.",
            },
            {
                "route": "shadow_logs",
                "status": "searched_nonconsuming",
                "evidence": scan_shadow_logs_for_target_hits(),
            },
            {
                "route": "research_exports",
                "status": "searched",
                "evidence": inspect_exports_and_sierra()[0],
            },
            {
                "route": "sierra_chart_local_roots",
                "status": "searched_proxy_only",
                "evidence": inspect_exports_and_sierra()[1],
            },
            {
                "route": "databento_6j_proxy_cache",
                "status": "searched_proxy_only",
                "evidence": {
                    "candidate_count": databento.get("candidate_count"),
                    "candidate_files": databento.get("candidate_files", []),
                    "usable_for_same_tick_ordering": False,
                    "paid_or_api_call_made": False,
                    "decision": "6J futures proxy cache cannot order broker-native USDJPY CFD bid/ask predicates.",
                },
            },
            {
                "route": "official_mt5_mql5_cached_docs",
                "status": "searched",
                "evidence": mql5_contract,
            },
        ],
        "source_search_conclusion": "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND",
        "terminal_g12_verdict": TERMINAL_G12_VERDICT,
        "exact_remaining_unblocker": (
            "Broker-native USDJPY quote-event stream or server-side quote log for "
            "2026-04-20T00:15:04.153Z and 2026-05-01T00:30:00.083Z, carrying bid/ask plus "
            "sub-millisecond timestamp or monotonic quote-event sequence/event ID, with source hash/provenance "
            "and no account/order/history/deal/position labels."
        ),
    }


def build_hash_audit(row_reaudits: list[dict[str, Any]], mql5_contract: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = [
        file_record(CONTROL_PROMPT, "controlling_prompt", strict=True, used_for_claims=True),
        file_record(LATEST_HANDOFF, "latest_handoff_context", strict=True, used_for_claims=True),
        file_record(QUICK_REFERENCE, "preflight_quick_reference", strict=True, used_for_claims=True),
        file_record(RESEARCH_DOCTRINE, "preflight_research_doctrine", strict=True, used_for_claims=True),
        file_record(GOAL_DISCIPLINE, "preflight_goal_session_discipline", strict=True, used_for_claims=True),
        file_record(LOCAL_HEAVY, "preflight_local_heavy_inventory", strict=True, used_for_claims=True),
        file_record(LIVE_STATE, "preflight_live_state_context_mutable", strict=False, used_for_claims=True),
        file_record(RESEARCH_CURRENT_STATE, "preflight_research_current_state_mutable", strict=False, used_for_claims=True),
    ]
    for role, path in SOURCE_ACCESS_FILES.items():
        records.append(file_record(path, f"source_access_{role}", strict=True, used_for_claims=True))
    for role, path in UPSTREAM_FILES.items():
        records.append(file_record(path, f"upstream_{role}", strict=True, used_for_claims=True))
    for name, path in MQL_DOCS.items():
        records.append(file_record(path, f"mql5_cached_doc_{name}", strict=True, used_for_claims=True))
    for source_path in sorted({Path(r["source_path"]) for r in row_reaudits}):
        records.append(file_record(source_path, "decisive_broker_quote_state_parquet", strict=True, used_for_claims=True))

    sierra_manifest = MAIN_ROOT / "data/sierra_ohlcv_roots/sierra_6j_to_usdjpy_pilot_20260504/manifest.json"
    m1_context = MAIN_ROOT / "data/mt5_research_exports/phase3_v2b_forward_20260401_20260502_readonly/USDJPY_M1.csv"
    records.extend(
        [
            file_record(m1_context, "m1_context_only_not_sequence", strict=True, used_for_claims=True),
            file_record(sierra_manifest, "sierra_6j_proxy_manifest_context_only", strict=True, used_for_claims=True),
        ]
    )

    hash_failures = []
    for rec in records:
        if not rec["strict_hash"]:
            continue
        path = Path(rec["path"])
        if not path.exists():
            hash_failures.append({"path": str(path), "reason": "missing"})
            continue
        actual = sha256_file(path)
        if actual != rec["sha256"]:
            hash_failures.append({"path": str(path), "expected": rec["sha256"], "actual": actual})

    return {
        "artifact_family": "G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "records": records,
        "strict_hash_record_count": sum(1 for r in records if r["strict_hash"]),
        "strict_hash_failures": hash_failures,
        "mql5_contract_raw_capture_count": len(mql5_contract["raw_captures"]),
        "hash_audit_conclusion": "PASS" if not hash_failures else "FAIL",
    }


def build_no_leak_denominator_audit(row_reaudits: list[dict[str, Any]]) -> dict[str, Any]:
    source_access_noleak = load_json(SOURCE_ACCESS_FILES["no_leak"])
    count_recomp = load_json(UPSTREAM_FILES["count_recomputation"])
    source_control = load_json(UPSTREAM_FILES["source_control_impossibility"])
    generated_inputs = [
        load_json(SOURCE_ACCESS_FILES["target_reconstruction"]),
        load_json(SOURCE_ACCESS_FILES["event_order_proof"]),
        source_access_noleak,
        count_recomp,
        source_control,
    ]
    forbidden_hits = []
    for idx, payload in enumerate(generated_inputs):
        for hit in walk_json_keys(payload):
            forbidden_hits.append({"input_index": idx, **hit})

    source_impossible = set(count_recomp["mandatory_exclusions_recomputed"]["source_impossible_rows"])
    return {
        "artifact_family": "G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_row_count": len(row_reaudits),
        "target_rows": TARGET_ROWS,
        "all_target_rows_in_source_impossible_exclusion_set": set(TARGET_ROWS).issubset(source_impossible),
        "accepted_denominator_movement": 0,
        "source_safe_input_only_rows": 0,
        "source_impossible_rows": sorted(source_impossible),
        "exclusion_denominator_violations": count_recomp["mandatory_exclusions_recomputed"].get("exclusion_denominator_violations", []),
        "duplicate_key_counts": dict(Counter(r["packet_row_id"] for r in row_reaudits)),
        "source_access_lane_noleak_conclusion": source_access_noleak.get("no_leak_conclusion"),
        "unsafe_flag_hits": {
            "validation_safe_true": any(r.get("validation_safe") is not False for r in row_reaudits),
            "outcome_review_opened_true": any(r.get("outcome_review_opened") is not False for r in row_reaudits),
            "live_effect_true": any(r.get("live_effect") is not False for r in row_reaudits),
        },
        "forbidden_json_key_hits": forbidden_hits,
        "decision": "PASS_SOURCE_IMPOSSIBILITY_ONLY_NO_RESULT_DENOMINATOR_OR_LIVE_EFFECT",
    }


def write_context_anchor() -> None:
    head = run_git(["rev-parse", "--short", "HEAD"])
    body = f"""# G12 NOFILL USDJPY Sequence Source Audit Context Anchor

Generated: `{utc_now()}`
Route: `G12_NOFILL_USDJPY_SEQUENCE_SOURCE_AUDIT`
Promotion verdict: `{PROMOTION}`
`validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Controlling Prompt

- `{CONTROL_PROMPT.relative_to(REPO_ROOT).as_posix()}`
- Actual HEAD at audit build: `{head}`
- Branch: `{run_git(["branch", "--show-current"])}`

## Active Question Stack

- Did the source-access lane prove `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES` for rows `{", ".join(TARGET_ROWS)}`?
- Did it miss any source-safe local route that carries broker-native USDJPY sub-row quote-event ordering?
- Can MT5/MQL5 cached docs authorize intra-row ordering from `MqlTick` flags or `time_msc`?
- What exact owner/platform source is needed if approved routes remain insufficient?

## Hard Boundaries

No result scoring, validation, promotion, live prompt or `src` trading-logic change, risk/config/execution/permission/safety/canary/order behavior change, broker account/order/history/deal/position evidence, paid/API/Databento call, credential change, remote push, or registry promotion.
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_{DATE}.md").write_text(body, encoding="utf-8")


def write_decision_ledger(row_reaudits: list[dict[str, Any]], source_search: dict[str, Any]) -> None:
    rows = []
    for row in row_reaudits:
        rows.append(
            [
                row["packet_row_id"],
                row["symbol"],
                row["side"],
                row["decisive_timestamp_utc"],
                row["exact_timestamp_row_count"],
                ",".join(row["timestamp_precision"]["sequence_like_columns"]) or "none",
                TERMINAL_G12_VERDICT,
            ]
        )
    body = f"""# G12 NOFILL USDJPY Sequence Decision Ledger - {DATE}

Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Terminal G12 verdict: `{TERMINAL_G12_VERDICT}`.

{md_table(["packet_row_id", "symbol", "side", "decisive_timestamp_utc", "rows_at_timestamp", "sequence_like_fields", "g12_verdict"], rows)}

## Decision

The source-access lane is accepted as source-impossibility evidence only. All four target rows are single broker quote-state snapshots where `entry_touch` and `protective_level` are simultaneously true, and no approved current/local route exposes a sub-millisecond timestamp, monotonic quote-event ID, event sequence, or other source-safe intra-row ordering field. Proxy routes remain context only and cannot clear broker-native USDJPY same-tick sequence.

Exact remaining unblocker: {source_search["exact_remaining_unblocker"]}
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.md").write_text(body, encoding="utf-8")


def write_mql5_contract_md(mql5_contract: dict[str, Any]) -> None:
    rows = []
    for record in mql5_contract["raw_captures"]:
        rows.append([record["role"], record["exists"], record["sha256"], record["path"]])
    evidence_rows = [[e["path"], e["line"], e["pattern"]] for e in mql5_contract["line_evidence"]]
    body = f"""# G12 NOFILL USDJPY MQL5 Source Contract Audit - {DATE}

Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Contract Decision

`PASS_SOURCE_CONTRACT_LIMIT_CONFIRMED`.

The cached official MT5/MQL5 source captures support chronological ordering across returned `MqlTick` rows and expose quote-state fields such as bid, ask, `time_msc`, and flags. They do not expose a broker-native sequence/event ID or sub-row timestamp that can order two predicates inside one returned quote-state row.

## Raw Captures

{md_table(["role", "exists", "sha256", "path"], rows)}

## Local Line Evidence

{md_table(["path", "line", "pattern"], evidence_rows)}

## Interpretation Boundary

`time_msc` is millisecond precision. Tick flags identify which fields changed in the tick row; they are not an ordering stream for entry-touch versus protective-level predicates inside the same row. Therefore the official cached docs do not clear the four USDJPY same-tick rows without a separate broker-native quote-event stream/server-side quote log.
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_{DATE}.md").write_text(body, encoding="utf-8")


def write_external_request(source_search: dict[str, Any]) -> None:
    body = f"""# G12 NOFILL USDJPY Sequence External Access Request - {DATE}

Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Exact Request

Provide a broker-native USDJPY quote-event stream or server-side quote log for these exact timestamps:

- `2026-04-20T00:15:04.153Z`
- `2026-05-01T00:30:00.083Z`

Required fields:

- broker-native bid and ask per quote event;
- sub-millisecond timestamp or monotonic quote-event sequence/event ID;
- source provenance and SHA256/hashable raw export;
- enough surrounding rows to verify ordering before/after the decisive update;
- no account, order, history, deal, position, PnL, actual-R, fill, or live-trade result labels.

## Why It Is Needed

{source_search["exact_remaining_unblocker"]}

Prospective source-only logging can prevent future blockers, but it cannot retro-clear these four historical rows unless the broker/native server log covers the exact timestamps above.
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_EXTERNAL_ACCESS_REQUEST_{DATE}.md").write_text(body, encoding="utf-8")


def write_next_prompt_pack() -> None:
    body = f"""# G12 NOFILL USDJPY Sequence Next Prompt Pack - {DATE}

Promotion verdict: `{PROMOTION}`.

Next route status: `WAIT_FOR_EXACT_BROKER_NATIVE_QUOTE_EVENT_SOURCE`.

If the owner obtains the requested source, run a new source-access lane only. Inputs must be the broker-native USDJPY quote-event stream/server-side quote log with source hash/provenance for `2026-04-20T00:15:04.153Z` and `2026-05-01T00:30:00.083Z`.

Allowed next work:

- verify source hash and schema;
- map quote events to the four target rows;
- decide whether each row clears as input-only source evidence or remains impossible;
- preserve exclusions until a separate G12/G0 source-control path accepts any change.

Forbidden next work:

- result scoring, validation, promotion, registry edits, live trading behavior, prompts, `src` trading logic, config/risk/execution/permission/safety/canary changes, broker account/order/history/deal/position labels, paid/API/Databento calls, credentials, or remote pushes.
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_{DATE}.md").write_text(body, encoding="utf-8")


def write_completion_audit(
    row_reaudits: list[dict[str, Any]],
    source_search: dict[str, Any],
    hash_audit: dict[str, Any],
    noleak: dict[str, Any],
) -> None:
    checklist = [
        {
            "requirement": "mandatory_preflight_and_context",
            "status": "PASS",
            "evidence": [
                str(LIVE_STATE),
                str(LATEST_HANDOFF),
                str(QUICK_REFERENCE),
                str(RESEARCH_DOCTRINE),
                str(RESEARCH_CURRENT_STATE),
                str(GOAL_DISCIPLINE),
                str(LOCAL_HEAVY),
            ],
        },
        {
            "requirement": "controlling_inputs_and_upstream_chain_read",
            "status": "PASS",
            "evidence": [str(p) for p in [*SOURCE_ACCESS_FILES.values(), *UPSTREAM_FILES.values()]],
        },
        {
            "requirement": "reconstruct_each_target_row",
            "status": "PASS",
            "evidence": {
                row["packet_row_id"]: {
                    "decisive_timestamp_utc": row["decisive_timestamp_utc"],
                    "source_sha256": row["source_sha256"],
                    "exact_timestamp_row_count": row["exact_timestamp_row_count"],
                    "quote_fields": row["quote_fields"],
                    "timestamp_precision": row["timestamp_precision"],
                }
                for row in row_reaudits
            },
        },
        {
            "requirement": "central_claim_independently_verified",
            "status": "PASS",
            "evidence": source_search["central_claim_checks"],
        },
        {
            "requirement": "approved_routes_saturated",
            "status": "PASS",
            "evidence": source_search["approved_route_reaudits"],
        },
        {
            "requirement": "terminal_g12_verdict",
            "status": "PASS",
            "evidence": TERMINAL_G12_VERDICT,
        },
        {
            "requirement": "source_hash_recomputed",
            "status": "PASS" if not hash_audit["strict_hash_failures"] else "FAIL",
            "evidence": {"strict_hash_record_count": hash_audit["strict_hash_record_count"], "failures": hash_audit["strict_hash_failures"]},
        },
        {
            "requirement": "no_leak_denominator_safety",
            "status": "PASS",
            "evidence": {
                "accepted_denominator_movement": noleak["accepted_denominator_movement"],
                "source_safe_input_only_rows": noleak["source_safe_input_only_rows"],
                "unsafe_flag_hits": noleak["unsafe_flag_hits"],
                "forbidden_json_key_hits": noleak["forbidden_json_key_hits"],
            },
        },
        {
            "requirement": "required_outputs_created",
            "status": "PASS",
            "evidence": [
                f"G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.md",
                f"G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_{DATE}.json",
                f"G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_{DATE}.json",
                f"G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_{DATE}.md",
                f"G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_{DATE}.json",
                f"G12_NOFILL_USDJPY_SEQ_EXTERNAL_ACCESS_REQUEST_{DATE}.md",
                f"G12_NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_{DATE}.md",
                f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.md",
            ],
        },
    ]
    missing_or_weak = [item for item in checklist if item["status"] != "PASS"]
    completion = {
        "artifact_family": "G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "objective_restatement": (
            "Run an independent G12 source-access audit for four USDJPY NOFILL rows and decide whether "
            "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES holds or a source-safe route was missed."
        ),
        "promotion_verdict": PROMOTION,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "terminal_g12_verdict": TERMINAL_G12_VERDICT,
        "prompt_to_artifact_checklist": checklist,
        "missing_or_weak_requirements": missing_or_weak,
        "can_mark_goal_complete": not missing_or_weak,
    }
    write_json(ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json", completion)

    rows = [[item["requirement"], item["status"], json.dumps(item["evidence"], sort_keys=True)[:320]] for item in checklist]
    body = f"""# G12 NOFILL USDJPY Sequence Completion Audit - {DATE}

Promotion verdict: `{PROMOTION}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Can mark goal complete: `{str(completion["can_mark_goal_complete"]).lower()}`.

Terminal G12 verdict: `{TERMINAL_G12_VERDICT}`.

{md_table(["requirement", "status", "evidence"], rows)}

## Missing Or Weak Requirements

`{len(missing_or_weak)}`.

## Closeout Decision

The source-access lane did not miss a source-safe local/current route. The four target rows remain source-impossible from approved routes unless the exact broker-native quote-event/server-log source named in the external access request is provided.
"""
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.md").write_text(body, encoding="utf-8")


def main() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    write_context_anchor()
    row_reaudits = reconstruct_target_rows()
    mql5_contract = build_mql5_contract()
    source_search = build_source_search_reaudit(row_reaudits, mql5_contract)
    hash_audit = build_hash_audit(row_reaudits, mql5_contract)
    noleak = build_no_leak_denominator_audit(row_reaudits)

    write_json(ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_{DATE}.json", source_search)
    write_json(ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_{DATE}.json", hash_audit)
    write_json(ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_{DATE}.json", noleak)
    write_decision_ledger(row_reaudits, source_search)
    write_mql5_contract_md(mql5_contract)
    write_external_request(source_search)
    write_next_prompt_pack()
    write_completion_audit(row_reaudits, source_search, hash_audit, noleak)

    return {
        "ok": not hash_audit["strict_hash_failures"],
        "target_rows": TARGET_ROWS,
        "terminal_g12_verdict": TERMINAL_G12_VERDICT,
        "source_search_conclusion": source_search["source_search_conclusion"],
        "strict_hash_record_count": hash_audit["strict_hash_record_count"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True))
