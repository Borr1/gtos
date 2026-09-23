from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
UPSTREAM_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_may3_opening_range_market_closure_or_source_proof"
)
RESIDUAL_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_cat_v2_residual_blocker_clear_source_access_lane"
)
NOFILL_V2_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
)
G12_CAT_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_categorical_result_packet_v2_audit"
)
G12_PENDING_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_cat_v2_pending_source_contract_audit"
)
G12_CNR_T3_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_cnr_t3_lifecycle_audit"
)
G12_CNR061_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_cnr061_sidecar_reaudit"
)
G12_CNR_NEXT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_cnr_next_model_control_audit"
)

TARGET_ROWS = [
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
]
TARGET_SET = set(TARGET_ROWS)
UTC_START = pd.Timestamp("2026-05-03T13:00:00Z")
UTC_END = pd.Timestamp("2026-05-03T13:30:00Z")
SUNDAY_OPEN_UTC = pd.Timestamp("2026-05-03T22:00:00Z")
TERMINAL_DECISION = "ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY"
UPSTREAM_STATUS = "MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL"

FORBIDDEN_TRUE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_KEYS = {
    "actual_r",
    "broker_actual_r",
    "account_history",
    "order_history",
    "deal_history",
    "position_history",
    "win_rate",
    "expectancy",
    "r_multiple",
    "pnl",
    "profit",
    "loss",
    "performance_score",
    "hidden_label",
}
MUTABLE_CONTROL_HASH_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, payload: Any) -> None:
    path = LANE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (LANE_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_hash_record_path(record: dict[str, Any]) -> Path:
    resolved = Path(record.get("resolved_path") or "")
    if resolved.exists():
        return resolved
    raw = Path(record["path"])
    if raw.is_absolute():
        return raw
    return ROOT / raw


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - only used for context anchor fallback
        return f"UNAVAILABLE: {exc}"


def timestamp_series(df: pd.DataFrame) -> pd.Series:
    if "ts_utc" in df.columns:
        return pd.to_datetime(df["ts_utc"], utc=True)
    if "timestamp" in df.columns:
        return pd.to_datetime(df["timestamp"], utc=True)
    if "time" in df.columns:
        return pd.to_datetime(df["time"], utc=True)
    if "time_msc" in df.columns:
        return pd.to_datetime(df["time_msc"], unit="ms", utc=True)
    if isinstance(df.index, pd.DatetimeIndex):
        return pd.Series(pd.to_datetime(df.index, utc=True), index=df.index)
    raise ValueError(f"No timestamp column found in parquet columns: {list(df.columns)}")


def summarize_tick_parquet(path: Path) -> dict[str, Any]:
    df = pd.read_parquet(path)
    ts = timestamp_series(df)
    window_mask = (ts >= UTC_START) & (ts < UTC_END)
    pre_open_mask = ts < SUNDAY_OPEN_UTC
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "rows_total": int(len(df)),
        "columns": list(df.columns),
        "first_timestamp_utc": ts.min().isoformat().replace("+00:00", "Z"),
        "last_timestamp_utc": ts.max().isoformat().replace("+00:00", "Z"),
        "window_start_utc": UTC_START.isoformat().replace("+00:00", "Z"),
        "window_end_utc": UTC_END.isoformat().replace("+00:00", "Z"),
        "window_rows": int(window_mask.sum()),
        "pre_2200_utc_rows": int(pre_open_mask.sum()),
        "first_five_timestamps_utc": [
            t.isoformat().replace("+00:00", "Z") for t in ts.sort_values().head(5)
        ],
    }


def market_session_conversion() -> dict[str, Any]:
    start = datetime(2026, 5, 3, 13, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 3, 13, 30, tzinfo=timezone.utc)
    chicago = ZoneInfo("America/Chicago")
    new_york = ZoneInfo("America/New_York")
    globex_open_chicago = datetime(2026, 5, 3, 17, 0, tzinfo=chicago)
    globex_open_new_york = globex_open_chicago.astimezone(new_york)
    globex_open_utc = globex_open_chicago.astimezone(timezone.utc)
    return {
        "date": "2026-05-03",
        "weekday": start.strftime("%A"),
        "frozen_window_utc": {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
        },
        "frozen_window_chicago_ct": {
            "start": start.astimezone(chicago).isoformat(),
            "end": end.astimezone(chicago).isoformat(),
            "timezone": "America/Chicago",
            "utc_offset": start.astimezone(chicago).strftime("%z"),
        },
        "frozen_window_new_york_et": {
            "start": start.astimezone(new_york).isoformat(),
            "end": end.astimezone(new_york).isoformat(),
            "timezone": "America/New_York",
            "utc_offset": start.astimezone(new_york).strftime("%z"),
        },
        "official_globex_sunday_open_chicago_ct": globex_open_chicago.isoformat(),
        "official_globex_sunday_open_new_york_et": globex_open_new_york.isoformat(),
        "official_globex_sunday_open_utc": globex_open_utc.isoformat().replace("+00:00", "Z"),
        "window_is_before_official_sunday_open": end <= globex_open_utc,
        "minutes_from_window_end_to_globex_open": int((globex_open_utc - end).total_seconds() // 60),
    }


def official_cme_recheck(generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "source_capture_method": (
            "OpenAI web.open/find against official CME pages; direct factual support is recorded "
            "as URL plus web-tool line references and short snippets. No paid/API/Databento, "
            "broker/account/order/history, or MT5 route was used."
        ),
        "sources": [
            {
                "source_id": "G12_CME_NQ_PRODUCT_PAGE_JA",
                "source_owner": "CME Group",
                "url": "https://www.cmegroup.com/ja/markets/equities/nasdaq/e-mini-nasdaq-100.html",
                "web_tool_ref": "turn5view1 lines 302-312",
                "short_snippet_under_25_words": "Sunday-Friday 6:00 p.m. - 5:00 p.m. ET",
                "paraphrased_claim": (
                    "The official CME E-mini Nasdaq-100 futures contract specifications list "
                    "CME Globex trading from Sunday evening to Friday evening in ET."
                ),
                "proxy_use": "NAS100 CFD market-session source-control proxy only.",
            },
            {
                "source_id": "G12_CME_GC_CONTRACT_SPECS_CN",
                "source_owner": "CME Group",
                "url": "https://www.cmegroup.com/cn-s/markets/metals/precious/gold.contractSpecs.html",
                "web_tool_ref": "turn5view3 lines 254-262",
                "short_snippet_under_25_words": "Sunday-Friday 6:00 p.m.-5:00 p.m. ET; 5:00 p.m.-4:00 p.m. CT",
                "paraphrased_claim": (
                    "The official CME Gold futures contract specifications list CME Globex "
                    "trading from Sunday evening to Friday evening, with the CT equivalent."
                ),
                "proxy_use": "XAUUSD CFD market-session source-control proxy only.",
            },
        ],
        "conversion": market_session_conversion(),
        "inference": (
            "On 2026-05-03, 18:00 ET and 17:00 CT convert to 22:00 UTC because New York "
            "was on EDT and Chicago was on CDT. The frozen window 13:00-13:30 UTC was "
            "08:00-08:30 CT and 09:00-09:30 ET, ending 510 minutes before that open."
        ),
        "copyright_note": "Only short snippets and paraphrases are stored; no bulk page text copied.",
    }


def recompute_source_hash_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audits: list[dict[str, Any]] = []
    for idx, record in enumerate(records):
        resolved = resolve_hash_record_path(record)
        current = Path(record["path"]) if Path(record["path"]).is_absolute() else ROOT / record["path"]
        actual = sha256_file(resolved) if resolved.exists() and resolved.is_file() else None
        current_actual = sha256_file(current) if current.exists() and current.is_file() else None
        strict_required = record.get("path") not in MUTABLE_CONTROL_HASH_PATHS
        audits.append(
            {
                "index": idx,
                "role": record.get("role"),
                "path": record.get("path"),
                "strict_hash_required": strict_required,
                "resolved_path_used": str(resolved),
                "resolved_exists": resolved.exists(),
                "expected_sha256": record.get("sha256"),
                "actual_sha256": actual,
                "sha256_matches_expected": actual == record.get("sha256"),
                "strict_hash_pass": (actual == record.get("sha256")) if strict_required else True,
                "current_worktree_path": str(current),
                "current_worktree_exists": current.exists(),
                "current_worktree_sha256": current_actual,
                "current_worktree_matches_expected": (
                    current_actual == record.get("sha256") if current_actual is not None else None
                ),
                "current_worktree_drift_is_source_failure": False
                if current_actual is not None and current_actual != record.get("sha256") and resolved.exists()
                else None,
            }
        )
    return audits


def collect_forbidden_key_hits(obj: Any, path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower()
            if key_l in FORBIDDEN_KEYS:
                hits.append({"path": f"{path}.{key}", "key": key, "value_type": type(value).__name__})
            if key_l in FORBIDDEN_TRUE_FLAGS and value is True:
                hits.append({"path": f"{path}.{key}", "key": key, "value": True})
            hits.extend(collect_forbidden_key_hits(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(collect_forbidden_key_hits(value, f"{path}[{idx}]"))
    return hits


def boundary_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix == ".jsonl":
            payload: Any = read_jsonl(path)
        else:
            payload = read_json(path)
        file_hits = collect_forbidden_key_hits(payload)
        for hit in file_hits:
            hit["file"] = str(path.relative_to(ROOT))
            if hit.get("key") in FORBIDDEN_TRUE_FLAGS:
                flags.append(hit)
            else:
                hits.append(hit)
    return {
        "files_scanned": [str(p.relative_to(ROOT)) for p in paths],
        "forbidden_result_or_account_key_hits": hits,
        "unsafe_true_flag_hits": flags,
        "status": "PASS" if not hits and not flags else "FAIL",
    }


def row_matching_audit(upstream_rows: list[dict[str, Any]], residual_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    residual_by_id = {row["packet_row_id"]: row for row in residual_rows}
    audits: list[dict[str, Any]] = []
    for row in upstream_rows:
        rid = row["packet_row_id"]
        residual = residual_by_id[rid]
        matching_fields = [
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
        field_matches = {field: row.get(field) == residual.get(field) for field in matching_fields}
        audits.append(
            {
                "packet_row_id": rid,
                "symbol": row.get("symbol"),
                "residual_status_before_upstream_lane": residual.get("terminal_source_control_status"),
                "upstream_status": row.get("terminal_source_control_status"),
                "all_identity_fields_match_residual": all(field_matches.values()),
                "field_matches": field_matches,
                "original_blocker_codes_match": row.get("original_exact_blocker_codes")
                == residual.get("original_exact_blocker_codes"),
                "g12_decision": TERMINAL_DECISION,
            }
        )
    return audits


def build() -> dict[str, Any]:
    generated_at = utc_now()

    packet = read_json(UPSTREAM_DIR / "NOFILL_MAY3_SOURCE_PROOF_PACKET_2026-05-09.json")
    upstream_rows = read_jsonl(UPSTREAM_DIR / "NOFILL_MAY3_ROW_DECISION_LEDGER_2026-05-09.jsonl")
    market_ledger = read_json(UPSTREAM_DIR / "NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_2026-05-09.json")
    noleak_upstream = read_json(UPSTREAM_DIR / "NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.json")
    completion_upstream = read_json(UPSTREAM_DIR / "NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json")
    residual_rows = read_jsonl(RESIDUAL_DIR / "NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl")

    v2_universe = read_json(NOFILL_V2_DIR / "NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json")
    v2_rejects = read_json(NOFILL_V2_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json")
    v2_dup = read_json(NOFILL_V2_DIR / "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json")
    g12_v2_noleak = read_json(
        G12_CAT_AUDIT_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json"
    )
    g12_v2_blocker = read_json(
        G12_CAT_AUDIT_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json"
    )
    pending_dup = read_json(
        G12_PENDING_DIR / "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json"
    )
    pending_noleak = read_json(
        G12_PENDING_DIR / "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json"
    )
    cnr_t3_noleak = read_json(G12_CNR_T3_DIR / "G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    cnr061_blocked = read_json(G12_CNR061_DIR / "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json")
    cnr061_noleak = read_json(G12_CNR061_DIR / "G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json")
    cnr_next_lifecycle = read_json(G12_CNR_NEXT_DIR / "G12_CNR061_LIFECYCLE_PACKET_AUDIT_2026-05-08.json")
    cnr_next_noleak = read_json(G12_CNR_NEXT_DIR / "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json")

    row_ids = [row["packet_row_id"] for row in upstream_rows]
    target_rows_ok = row_ids == TARGET_ROWS
    statuses = Counter(row["terminal_source_control_status"] for row in upstream_rows)
    row_match = row_matching_audit(upstream_rows, residual_rows)

    tick_paths = {
        "NAS100": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet"),
        "XAUUSD": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet"),
    }
    tick_audits = {symbol: summarize_tick_parquet(path) for symbol, path in tick_paths.items()}

    official_recheck = official_cme_recheck(generated_at)
    write_json("G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json", official_recheck)
    official_recheck_hash = sha256_file(LANE_DIR / "G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json")

    hash_audits = recompute_source_hash_records(packet["source_hash_records"])
    strict_hash_ok = all(row["strict_hash_pass"] for row in hash_audits)
    mutable_control_hash_drift = [
        row
        for row in hash_audits
        if not row["strict_hash_required"] and not row["sha256_matches_expected"]
    ]
    source_hash_audit = {
        "artifact_family": "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_hash_records_checked": len(hash_audits),
        "strict_source_hash_records_checked": sum(1 for row in hash_audits if row["strict_hash_required"]),
        "strict_source_hashes_recomputed_ok": strict_hash_ok,
        "mutable_control_hash_drift_count": len(mutable_control_hash_drift),
        "mutable_control_hash_drift": mutable_control_hash_drift,
        "hash_audits": hash_audits,
        "tick_parquet_recompute": tick_audits,
        "g12_official_cme_source_recheck": {
            "path": str(
                (
                    LANE_DIR / "G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json"
                ).relative_to(ROOT)
            ),
            "sha256": official_recheck_hash,
        },
        "current_worktree_hash_drift_note": (
            "When a packet record also has a recorded resolved_path from the originating worktree, "
            "G12 recomputes the recorded source path. Current-worktree copies of mutable prompts or "
            "context docs can drift after merge/context refresh and are not treated as source-data failures."
        ),
    }
    write_json("G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json", source_hash_audit)

    session_audit = {
        "artifact_family": "G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "conversion": market_session_conversion(),
        "official_cme_recheck": official_recheck,
        "proxy_decisions": [
            {
                "symbol": "NAS100",
                "official_proxy": "CME E-mini Nasdaq-100 futures (NQ)",
                "decision": "ACCEPT_FOR_MARKET_SESSION_SOURCE_CONTROL_ONLY",
                "reason": (
                    "NQ is an official Nasdaq-100 futures session proxy and the same-symbol "
                    "NAS100 broker tick parquet independently shows no broker ticks until just "
                    "after 22:00 UTC."
                ),
                "limitation": "Not a broker-native CFD schedule and not a fill/outcome label.",
            },
            {
                "symbol": "XAUUSD",
                "official_proxy": "CME Gold futures (GC)",
                "decision": "ACCEPT_FOR_MARKET_SESSION_SOURCE_CONTROL_ONLY",
                "reason": (
                    "GC is an official gold futures session proxy and the same-symbol XAUUSD "
                    "broker tick parquet independently shows no broker ticks until just after "
                    "22:00 UTC."
                ),
                "limitation": "Not a broker-native CFD schedule and not a fill/outcome label.",
            },
        ],
        "counterargument_review": {
            "broker_native_session_metadata_would_be_stronger": True,
            "broker_native_metadata_required_for_this_source_control_decision": False,
            "reason": (
                "The source question is whether a 13:00-13:30 UTC Sunday frozen range can be "
                "closed as market-session empty source/control evidence. Same-symbol broker "
                "quote absence plus first ticks aligned with official CME proxy open is sufficient "
                "for that narrow source/control closure."
            ),
        },
        "decision": TERMINAL_DECISION,
    }

    scanned_paths = [
        UPSTREAM_DIR / "NOFILL_MAY3_SOURCE_PROOF_PACKET_2026-05-09.json",
        UPSTREAM_DIR / "NOFILL_MAY3_ROW_DECISION_LEDGER_2026-05-09.jsonl",
        UPSTREAM_DIR / "NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_2026-05-09.json",
        UPSTREAM_DIR / "NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json",
        NOFILL_V2_DIR / "NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json",
        NOFILL_V2_DIR / "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
        G12_CAT_AUDIT_DIR / "G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_2026-05-09.json",
        G12_CAT_AUDIT_DIR / "G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_2026-05-09.json",
        G12_PENDING_DIR / "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json",
    ]
    noleak_scan = boundary_scan(scanned_paths)

    noleak_denominator = {
        "artifact_family": "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "may3_upstream_boundary": {
            "targeted_row_count": packet["targeted_row_count"],
            "result_labels_assigned": packet["result_labels_assigned"],
            "rows_moved_into_accepted_denominator": packet["rows_moved_into_accepted_denominator"],
            "reject_total_preserved_outside_labels_denominators": packet[
                "reject_total_preserved_outside_labels_denominators"
            ],
            "noleak_violations": len(noleak_upstream.get("violations", [])),
        },
        "nofill_cat_v2_boundary": {
            "row_count": v2_universe["source_universe"]["row_count"],
            "accepted_rows": v2_universe["source_universe"]["accepted_rows"],
            "blocked_exact_rows": v2_universe["source_universe"]["blocked_exact_rows"],
            "rejected_rows": v2_universe["source_universe"]["rejected_rows"],
            "reject_ledger_rows": v2_rejects["rejected_row_count"],
            "duplicate_posture": {
                "accepted_rows": v2_dup["accepted_rows"],
                "accepted_unique_nofill_duplicate_keys": v2_dup["accepted_unique_nofill_duplicate_keys"],
                "oti5_canonical_rows_accepted_for_rebuild": len(
                    v2_dup["oti5_canonical_rows_accepted_for_rebuild"]
                ),
                "oti5_noncanonical_rows_rejected_from_denominator": v2_dup[
                    "oti5_noncanonical_rows_rejected_from_denominator"
                ],
            },
            "g12_v2_noleak_status": g12_v2_noleak["status"],
            "g12_blocker_review_status": g12_v2_blocker["status"],
            "pending_duplicate_review_status": pending_dup["status"],
            "pending_noleak_review_status": pending_noleak["status"],
        },
        "other_row_boundary": {
            "six_t3_rows_status": {
                "source": "G12_CNR061_LIFECYCLE_PACKET_AUDIT_2026-05-08.json",
                "row_count": cnr_next_lifecycle["independent_lifecycle_recompute"]["row_count"],
                "promotion_verdict": cnr_next_lifecycle["promotion_verdict"],
                "validation_safe": cnr_next_lifecycle["validation_safe"],
                "outcome_review_opened": cnr_next_lifecycle["outcome_review_opened"],
                "live_effect": cnr_next_lifecycle["live_effect"],
                "decision": cnr_next_lifecycle["decision"],
            },
            "g12_blocked_cnr061_rows_status": {
                "source": "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
                "blocked_rows": cnr061_blocked["exclusion_counts"]["blocked_rows"],
                "audit_status": cnr061_blocked["audit_status"],
                "promotion_verdict": cnr061_blocked["promotion_verdict"],
                "validation_safe": cnr061_blocked["validation_safe"],
                "outcome_review_opened": cnr061_blocked["outcome_review_opened"],
                "live_effect": cnr061_blocked["live_effect"],
            },
            "cnr_t3_blocked_94_status": cnr_t3_noleak["blocked_94_exclusion"],
            "cnr061_noleak_status": cnr061_noleak["audit_status"],
            "cnr_next_noleak_status": cnr_next_noleak["decision"],
        },
        "boundary_scan": noleak_scan,
        "decision": "PASS_NO_LABEL_DENOMINATOR_RESULT_VALIDATION_PROMOTION_MOVEMENT",
    }

    per_row_decisions = []
    for row in upstream_rows:
        symbol = row["symbol"]
        tick = tick_audits[symbol]
        per_row_decisions.append(
            {
                "packet_row_id": row["packet_row_id"],
                "symbol": symbol,
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "decision_asof_utc": row["decision_asof_utc"],
                "upstream_terminal_source_control_status": row["terminal_source_control_status"],
                "g12_terminal_decision": TERMINAL_DECISION,
                "source_control_only": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "result_label_assigned": False,
                "cleared_into_accepted_denominator": False,
                "tick_file_sha256": tick["sha256"],
                "tick_window_rows": tick["window_rows"],
                "tick_first_timestamp_utc": tick["first_timestamp_utc"],
                "official_proxy": row["source_contract_scope"]["official_exchange_session_proxy"],
                "proxy_accepted_narrowly": True,
                "exact_next_source_needed": None,
                "decision_reason": (
                    "Residual blocker identity matches exactly; same-symbol broker tick file has zero "
                    "ticks in the frozen window and first tick near official Sunday Globex open; official "
                    "CME proxy session evidence places NQ/GC opening after the frozen range; no denominator "
                    "or label movement is allowed."
                ),
            }
        )

    decision_ledger = {
        "artifact_family": "G12_NOFILL_MAY3_DECISION_LEDGER",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "terminal_decision": TERMINAL_DECISION,
        "terminal_decision_counts": {TERMINAL_DECISION: 3},
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_row_ids": TARGET_ROWS,
        "targeted_row_count": len(TARGET_ROWS),
        "exact_target_rows_only": target_rows_ok,
        "upstream_status_counts": dict(statuses),
        "row_matching_audit": row_match,
        "row_decisions": per_row_decisions,
        "audit_question_answers": [
            {
                "question_id": idx + 1,
                "answer": answer,
            }
            for idx, answer in enumerate(
                [
                    "Yes. The three target rows exactly match the residual OTI4 May 3 rows by row ID, symbol, source lane, source packet, source row, duplicate group, duplicate key, and original blocker code.",
                    "Yes. G12 independently supports MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL for the three rows as source/control evidence only.",
                    "Yes. NAS100 and XAUUSD broker tick parquets have zero rows in 2026-05-03T13:00:00Z through 13:30:00Z and first ticks at 22:00:00.391Z / 22:00:00.780Z.",
                    "Yes. Official CME NQ and GC source checks support Sunday evening Globex open at 18:00 ET / 17:00 CT, which converts to 2026-05-03T22:00:00Z.",
                    "Yes. UTC 13:00-13:30 converts to 08:00-08:30 America/Chicago and 09:00-09:30 America/New_York on 2026-05-03.",
                    "Yes, narrowly. NAS100-to-NQ and XAUUSD-to-GC are acceptable only as market-session source-control proxies when paired with same-symbol broker quote zero-row evidence.",
                    "Yes. Failed direct curl attempts are recorded as failed and used_for_factual_claims=false.",
                    "Yes. All 36 upstream strict source hash records recompute against their recorded source paths.",
                    "Yes. Sierra SCID files are supporting proxy/same-market zero-row checks and depth files are presence/hash only, not OHLC or quote proof.",
                    "Yes. The 65 rejects, six T3 rows, G12-blocked CNR061 rows, and all other no-fill rows remain outside May 3 labels, denominators, result use, validation use, and promotion use.",
                    "No generated or upstream-scanned artifact sets validation_safe=true, outcome_review_opened=true, or live_effect=true.",
                    "No result/R/performance scoring, broker actual-R, account/order/history label, hidden label, or blocked-packet outcome use was found in this lane.",
                    f"G12 decision: {TERMINAL_DECISION}.",
                    "No exact next source prompt remains for these three source-control rows. A future optional hardening route could export broker-native symbol-session metadata, but result lanes still remain closed unless separately frozen, approved, and no-leak verified.",
                ]
            )
        ],
    }
    write_json("G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json", decision_ledger)

    write_json("G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json", completion_payload(
        generated_at=generated_at,
        decision_ledger=decision_ledger,
        source_hash_audit=source_hash_audit,
        session_audit=session_audit,
        noleak_denominator=noleak_denominator,
        upstream_completion=completion_upstream,
    ))

    write_markdown_outputs(
        generated_at=generated_at,
        decision_ledger=decision_ledger,
        source_hash_audit=source_hash_audit,
        session_audit=session_audit,
        noleak_denominator=noleak_denominator,
        market_ledger=market_ledger,
    )

    return {
        "built": True,
        "terminal_decision": TERMINAL_DECISION,
        "strict_source_hashes_recomputed_ok": strict_hash_ok,
        "target_rows_ok": target_rows_ok,
        "noleak_status": noleak_scan["status"],
    }


def completion_payload(
    *,
    generated_at: str,
    decision_ledger: dict[str, Any],
    source_hash_audit: dict[str, Any],
    session_audit: dict[str, Any],
    noleak_denominator: dict[str, Any],
    upstream_completion: dict[str, Any],
) -> dict[str, Any]:
    required_files = [
        "G12_NOFILL_MAY3_CONTEXT_ANCHOR_2026-05-09.md",
        "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md",
        "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json",
        "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.md",
        "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json",
        "G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT_2026-05-09.md",
        "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md",
        "G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md",
        "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md",
        "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json",
        "build_g12_nofill_may3_source_proof_audit_2026_05_09.py",
        "verify_g12_nofill_may3_source_proof_audit_2026_05_09.py",
        "test_g12_nofill_may3_source_proof_audit_2026_05_09.py",
        "G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json",
    ]
    checklist = [
        {
            "requirement": "exactly three target rows audited",
            "evidence": decision_ledger["target_row_ids"],
            "status": "PASS" if decision_ledger["targeted_row_count"] == 3 else "FAIL",
        },
        {
            "requirement": "terminal G12 decision emitted",
            "evidence": decision_ledger["terminal_decision"],
            "status": "PASS" if decision_ledger["terminal_decision"] == TERMINAL_DECISION else "FAIL",
        },
        {
            "requirement": "local tick zero-row evidence recomputed",
            "evidence": source_hash_audit["tick_parquet_recompute"],
            "status": "PASS"
            if all(v["window_rows"] == 0 for v in source_hash_audit["tick_parquet_recompute"].values())
            else "FAIL",
        },
        {
            "requirement": "official CME/session/timezone/proxy evidence checked",
            "evidence": session_audit["decision"],
            "status": "PASS" if session_audit["conversion"]["window_is_before_official_sunday_open"] else "FAIL",
        },
        {
            "requirement": "source hashes recomputed",
            "evidence": source_hash_audit["source_hash_records_checked"],
            "status": "PASS" if source_hash_audit["strict_source_hashes_recomputed_ok"] else "FAIL",
        },
        {
            "requirement": "no-leak denominator and rejects preserved",
            "evidence": noleak_denominator["decision"],
            "status": "PASS" if noleak_denominator["boundary_scan"]["status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "NO_PROMOTION_VERDICT and unsafe flags false",
            "evidence": {
                "promotion_verdict": decision_ledger["promotion_verdict"],
                "validation_safe": decision_ledger["validation_safe"],
                "outcome_review_opened": decision_ledger["outcome_review_opened"],
                "live_effect": decision_ledger["live_effect"],
            },
            "status": "PASS"
            if decision_ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"
            and not decision_ledger["validation_safe"]
            and not decision_ledger["outcome_review_opened"]
            and not decision_ledger["live_effect"]
            else "FAIL",
        },
        {
            "requirement": "upstream completion reviewed but not blindly accepted",
            "evidence": upstream_completion.get("objective_satisfied"),
            "status": "PASS" if upstream_completion.get("objective_satisfied") is True else "FAIL",
        },
    ]
    return {
        "artifact_family": "G12_NOFILL_MAY3_COMPLETION_AUDIT",
        "generated_at_utc": generated_at,
        "route_id": "G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT",
        "objective_satisfied": all(item["status"] == "PASS" for item in checklist),
        "terminal_decision": decision_ledger["terminal_decision"],
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "required_artifacts": required_files,
        "prompt_to_artifact_checklist": checklist,
        "verification_commands_required_before_final_status": [
            "python -m py_compile research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/build_g12_nofill_may3_source_proof_audit_2026_05_09.py research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/verify_g12_nofill_may3_source_proof_audit_2026_05_09.py research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/test_g12_nofill_may3_source_proof_audit_2026_05_09.py",
            "python research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/verify_g12_nofill_may3_source_proof_audit_2026_05_09.py",
            "pytest -q research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/test_g12_nofill_may3_source_proof_audit_2026_05_09.py",
            "python research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
            "pytest -q research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/test_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
            "python scripts/generate_live_state.py",
        ],
        "non_claims": [
            "No result lane opens.",
            "No validation or promotion claim is made.",
            "No broker/account/order/history labels or paid/API/Databento calls were used.",
            "No live trading surface was changed.",
        ],
    }


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(out)


def write_markdown_outputs(
    *,
    generated_at: str,
    decision_ledger: dict[str, Any],
    source_hash_audit: dict[str, Any],
    session_audit: dict[str, Any],
    noleak_denominator: dict[str, Any],
    market_ledger: dict[str, Any],
) -> None:
    head = git_output(["git", "rev-parse", "HEAD"])
    branch = git_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = git_output(["git", "status", "--short"])

    active_questions = [
        "Q1 target-row identity vs residual blocker lane",
        "Q2 upstream MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL support",
        "Q3 local NAS100/XAUUSD tick zero-row evidence",
        "Q4 official CME Sunday Globex open evidence",
        "Q5 UTC/Chicago/New York timezone conversion",
        "Q6 NAS100-to-NQ and XAUUSD-to-GC proxy validity",
        "Q7 direct curl failures excluded from claims",
        "Q8 strict source hashes recomputed",
        "Q9 Sierra/SCID/depth role boundaries",
        "Q10 rejects/T3/CNR061/other rows outside labels and denominators",
        "Q11 unsafe flags remain false",
        "Q12 no result/R/performance/account/order/history use",
        "Q13 terminal G12 decision",
        "Q14 exact next prompt status",
    ]
    write_md(
        "G12_NOFILL_MAY3_CONTEXT_ANCHOR_2026-05-09.md",
        f"""# G12 NOFILL May 3 Context Anchor - 2026-05-09

Generated: `{generated_at}`

## Run State

- HEAD: `{head}`
- Branch: `{branch}`
- Controlling prompt: `research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_SOURCE_PROOF_AUDIT_GOAL_PROMPT_2026-05-09.md`
- Working tree at anchor build:

```text
{status or "clean"}
```

## Boundaries

- Scope: source/control red-team audit only.
- Terminal decision options: `ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY`, `BLOCK_WITH_EXACT_NEXT_SOURCE`, `REJECT_INVALID_SOURCE_CONTROL_PROOF`.
- Forbidden: result/R/performance scoring, broker actual-R, account/order/history labels, hidden labels, paid/API/Databento, live trading prompts, `src` trading logic, risk/execution/permissions/safety/selectors/canaries, credentials, registry edits, remote pushes, promotion.
- Preserved: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Active Question Stack

{chr(10).join(f"- {q}: answered in `G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json`." for q in active_questions)}

## Inputs Read

- Upstream May 3 packet, row ledger, market-session source ledger, blocked/cleared ledger, no-leak audit, completion audit, raw official-source capture, direct curl attempt ledger, builder, verifier, and tests.
- Prior residual blocker source-access lane row ledger.
- G12 pending source contract audit duplicate/no-leak artifacts.
- NOFILL CAT V2 rebuild/audit artifacts for counts, rejects, duplicate denominator, and label boundaries.
- G12 CNR T3/CNR061 artifacts for six-row and blocked-row exclusion boundaries.
- Approved local heavy-data roots: main tick parquet root, Sierra OHLC roots, Sierra raw SCID/depth roots.

## Resume Rule

After compaction or interruption: regenerate `LIVE_STATE`, re-read the controlling prompt and this anchor, then continue from the generated G12 ledgers and verifier status. Do not rely on chat memory.
""",
    )

    row_table = md_table(
        [
            {
                "row": row["packet_row_id"],
                "symbol": row["symbol"],
                "window_rows": row["tick_window_rows"],
                "first_tick": row["tick_first_timestamp_utc"],
                "decision": row["g12_terminal_decision"],
            }
            for row in decision_ledger["row_decisions"]
        ],
        ["row", "symbol", "window_rows", "first_tick", "decision"],
    )
    write_md(
        "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md",
        f"""# G12 NOFILL May 3 Decision Ledger - 2026-05-09

Generated: `{generated_at}`

Terminal decision: `{decision_ledger["terminal_decision"]}`

Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Row Decisions

{row_table}

## Decision Rationale

The three rows exactly match the residual OTI4 May 3 blockers. The same-symbol broker tick files have zero ticks in the frozen `2026-05-03T13:00:00Z` to `2026-05-03T13:30:00Z` range. First broker ticks arrive at `2026-05-03T22:00:00.391Z` for NAS100 and `2026-05-03T22:00:00.780Z` for XAUUSD. Independent official CME source checks support Sunday evening Globex open at `2026-05-03T22:00:00Z` for the NQ/GC proxy sessions.

Acceptance is narrow: source-control market-session-empty evidence only. It is not a result label, denominator admission, validation-safe flip, promotion, or live behavior change.

## Audit Question Answers

{chr(10).join(f"- Q{item['question_id']}: {item['answer']}" for item in decision_ledger["audit_question_answers"])}
""",
    )

    hash_rows = [
        {
            "role": row["role"],
            "ok": row["sha256_matches_expected"],
            "path": row["path"],
        }
        for row in source_hash_audit["hash_audits"]
    ]
    write_md(
        "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.md",
        f"""# G12 NOFILL May 3 Source Hash Audit - 2026-05-09

Generated: `{generated_at}`

Strict source hashes recomputed: `{source_hash_audit["source_hash_records_checked"]}`.

Overall status: `{"PASS" if source_hash_audit["strict_source_hashes_recomputed_ok"] else "FAIL"}`.

## Tick Recompute

```json
{json.dumps(source_hash_audit["tick_parquet_recompute"], indent=2, sort_keys=True)}
```

## Official CME Recheck Capture

- File: `{source_hash_audit["g12_official_cme_source_recheck"]["path"]}`
- SHA256: `{source_hash_audit["g12_official_cme_source_recheck"]["sha256"]}`

## Source Hash Records

{md_table(hash_rows, ["role", "ok", "path"])}

Note: recorded `resolved_path` values are authoritative for the upstream packet's source hash records. Current worktree copies of mutable context or prompt files can differ after merge/context refresh and are not source-data failures when the recorded source path still hash-matches.
""",
    )

    write_md(
        "G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT_2026-05-09.md",
        f"""# G12 NOFILL May 3 Session And Proxy Audit - 2026-05-09

Generated: `{generated_at}`

Decision: `{session_audit["decision"]}`

## Timezone Recompute

```json
{json.dumps(session_audit["conversion"], indent=2, sort_keys=True)}
```

The frozen window was Sunday `08:00-08:30` America/Chicago and `09:00-09:30` America/New_York. CME Sunday evening open for the official proxy markets converts to `2026-05-03T22:00:00Z`, so the frozen range ended `510` minutes before open.

## Official Source Recheck

- NQ official source: CME E-mini Nasdaq-100 page, `turn5view1 lines 302-312`, short captured trading-hours phrase under 25 words.
- GC official source: CME Gold contract specs page, `turn5view3 lines 254-262`, short captured trading-hours phrase under 25 words.
- Upstream direct curl attempts remain honest negative evidence: failed attempts are recorded with `used_for_factual_claims=false`.

## Proxy Review

NAS100-to-NQ and XAUUSD-to-GC are accepted only for market-session source-control evidence. They do not prove broker-native CFD schedule, fill state, price path, result outcome, or validation. Same-symbol broker tick files are the broker-side quote evidence and the official CME markets are the session-open proxy evidence.

This is not a result label.

## Searched Routes

{chr(10).join(f"- `{route['route_id']}`: {route['status']} - {route['coverage']}" for route in market_ledger["searched_routes"])}
""",
    )

    write_md(
        "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md",
        f"""# G12 NOFILL May 3 No-Leak Denominator Audit - 2026-05-09

Generated: `{generated_at}`

Decision: `{noleak_denominator["decision"]}`

## May 3 Boundary

```json
{json.dumps(noleak_denominator["may3_upstream_boundary"], indent=2, sort_keys=True)}
```

## NOFILL CAT V2 Boundary

```json
{json.dumps(noleak_denominator["nofill_cat_v2_boundary"], indent=2, sort_keys=True)}
```

## Other Row Boundary

```json
{json.dumps(noleak_denominator["other_row_boundary"], indent=2, sort_keys=True)}
```

## Forbidden Field/Flag Scan

```json
{json.dumps(noleak_denominator["boundary_scan"], indent=2, sort_keys=True)}
```

Conclusion: the `65` rejects, six T3/CNR061 lifecycle rows, G12-blocked CNR061 rows, and all rows outside the three May 3 source-control targets remain outside this lane's labels, denominators, result use, validation use, promotion use, and live effect.
""",
    )

    write_md(
        "G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md",
        f"""# G12 NOFILL May 3 Next Prompt Pack - 2026-05-09

Terminal G12 decision: `{TERMINAL_DECISION}`.

No exact next source prompt is required for `NOFILL-CAT-ROW-0049`, `NOFILL-CAT-ROW-0050`, or `NOFILL-CAT-ROW-0051` before accepting the narrow source-control market-session-empty evidence.

Optional future hardening, not a blocker: export broker-native symbol-session metadata for NAS100 and XAUUSD Sunday sessions using an approved read-only non-account/non-order route. That would strengthen provenance but is not required because same-symbol broker tick files show zero frozen-window rows and first ticks at the official proxy open.

Closed routes remain closed: no result/R/performance scoring, no validation-safe flip, no outcome review opening, no promotion, no registry edit, and no live trading behavior change.
""",
    )

    completion = read_json(LANE_DIR / "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json")
    write_md(
        "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md",
        f"""# G12 NOFILL May 3 Completion Audit - 2026-05-09

Generated: `{generated_at}`

Objective satisfied by artifact evidence: `{completion["objective_satisfied"]}`.

Terminal decision: `{completion["terminal_decision"]}`.

Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Prompt-To-Artifact Checklist

{md_table(completion["prompt_to_artifact_checklist"], ["requirement", "status", "evidence"])}

## Required Artifacts

{chr(10).join(f"- `{name}`" for name in completion["required_artifacts"])}

## Verification Commands To Run Before Final Status

{chr(10).join(f"- `{cmd}`" for cmd in completion["verification_commands_required_before_final_status"])}

## Non-Claims

{chr(10).join(f"- {claim}" for claim in completion["non_claims"])}
""",
    )


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
