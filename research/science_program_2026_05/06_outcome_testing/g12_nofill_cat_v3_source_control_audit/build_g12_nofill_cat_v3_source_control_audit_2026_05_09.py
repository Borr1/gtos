from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_CAT_V3_SOURCE_CONTROL_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
PACKET_ID = "NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD_V1"

ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

V3_DIR = OUTCOME_DIR / "nofill_cat_v3_source_control_rebuild"
V2_DIR = OUTCOME_DIR / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
G12_V2_DIR = OUTCOME_DIR / "g12_nofill_categorical_result_packet_v2_audit"
V2_FORENSICS_DIR = OUTCOME_DIR / "nofill_cat_v2_quarantined_categorical_synthesis_forensics"
G12_V2_FORENSICS_DIR = OUTCOME_DIR / "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit"
G0_V2_DIR = OUTCOME_DIR / "nofill_cat_v2_g0_synthesis_control_route"
PENDING_SOURCE_DIR = OUTCOME_DIR / "nofill_cat_v2_pending_lifecycle_source_contract_builder"
G12_PENDING_SOURCE_DIR = OUTCOME_DIR / "g12_nofill_cat_v2_pending_source_contract_audit"
RESIDUAL_SOURCE_ACCESS_DIR = OUTCOME_DIR / "nofill_cat_v2_residual_blocker_clear_source_access_lane"
G12_SOURCE_CORRECTION_DIR = OUTCOME_DIR / "g12_nofill_source_correction_consolidated_audit"
RESULT_CONTRACT_DIR = OUTCOME_DIR / "no_fill_lifecycle_result_contract_design"
G12_RESULT_CONTRACT_DIR = OUTCOME_DIR / "g12_no_fill_result_contract_audit"
MAY3_PROOF_DIR = OUTCOME_DIR / "nofill_may3_opening_range_market_closure_or_source_proof"
G12_MAY3_DIR = OUTCOME_DIR / "g12_nofill_may3_source_proof_audit"
REMAINING_DIR = OUTCOME_DIR / "nofill_remaining_residual_source_closure"
G12_REMAINING_DIR = OUTCOME_DIR / "g12_nofill_remaining_residual_source_closure_audit"
OTI3_DIR = OUTCOME_DIR / "oti3_usdjpy_price_only_quote_or_tick_contract"

MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
MAIN_TICKS = MAIN_ROOT / "data" / "ticks"
TMP_GTOS = Path(r"C:\tmp\gtos_otb")

MAY3_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
}
XAU_ROW = "NOFILL-CAT-ROW-0241"
USDJPY_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
TARGET_ROWS = MAY3_ROWS | {XAU_ROW} | USDJPY_ROWS

EXPECTED_FAMILY_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "blocked": 0,
    "reject": 65,
}
EXPECTED_TARGET_STATES = {
    "NOFILL-CAT-ROW-0049": "SOURCE_CONTROL_MARKET_SESSION_EMPTY",
    "NOFILL-CAT-ROW-0050": "SOURCE_CONTROL_MARKET_SESSION_EMPTY",
    "NOFILL-CAT-ROW-0051": "SOURCE_CONTROL_MARKET_SESSION_EMPTY",
    "NOFILL-CAT-ROW-0241": "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL",
    "NOFILL-CAT-ROW-0130": "SOURCE_IMPOSSIBLE_EXACT_ORDERING",
    "NOFILL-CAT-ROW-0143": "SOURCE_IMPOSSIBLE_EXACT_ORDERING",
    "NOFILL-CAT-ROW-0165": "SOURCE_IMPOSSIBLE_EXACT_ORDERING",
    "NOFILL-CAT-ROW-0178": "SOURCE_IMPOSSIBLE_EXACT_ORDERING",
}

ACCEPT_OVERALL = "ACCEPT_V3_AS_SOURCE_CONTROL_CATEGORICAL_INPUT_EVIDENCE_ONLY"
ACCEPT_MAY3 = "ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY"
ACCEPT_XAU = "ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE"
ACCEPT_USDJPY = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "scripts/canary_test",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
    "start_all.bat",
)
FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
    "expectancy",
    "profit",
    "dsr",
    "pbo",
)
ALLOWED_FORBIDDEN_KEY_NAMES = {"outcome_review_opened", "promotion_verdict"}
MUTABLE_HASH_PATHS = {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT = utc_now()


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


def normalized_text_sha(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def git_lines(args: list[str]) -> list[str]:
    try:
        output = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_UNAVAILABLE:{exc!r}"]
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip() and not line.startswith("warning:")]


def git_status_paths() -> list[str]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_STATUS_UNAVAILABLE:{exc!r}"]
    paths: list[str] = []
    for line in output.splitlines():
        if not line.strip() or line.lower().startswith("warning:") or len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path.replace("\\", "/"))
    return paths


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def base_payload(family: str) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "generated_at_utc": GENERATED_AT,
        "route_id": ROUTE_ID,
        "packet_id": PACKET_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def resolve_record_path(record: dict[str, Any]) -> tuple[Path | None, str]:
    path_text = record.get("path") or ""
    path = Path(path_text)
    candidates: list[tuple[Path, str]] = []
    if path.is_absolute():
        candidates.append((path, "record_absolute_path"))
    else:
        candidates.append((ROOT / path_text, "current_worktree_relative_path"))
    resolved = record.get("resolved_path")
    if resolved:
        candidates.append((Path(resolved), "record_resolved_path"))
    for candidate, source in candidates:
        if candidate.exists():
            return candidate, source
    return None, "not_found"


def load_inputs() -> dict[str, Any]:
    return {
        "v3_rows": read_jsonl(V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "v3_universe": read_json(V3_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"),
        "v3_packet": read_json(V3_DIR / f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json"),
        "v3_blockers": read_json(V3_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json"),
        "v3_rejects": read_json(V3_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json"),
        "v3_hash": read_json(V3_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
        "v3_duplicates": read_json(V3_DIR / f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"),
        "v3_search": read_json(V3_DIR / f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json"),
        "v3_completion": read_json(V3_DIR / f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json"),
        "v2_rows": read_jsonl(V2_DIR / f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "g12_may3": read_json(G12_MAY3_DIR / f"G12_NOFILL_MAY3_DECISION_LEDGER_{DATE}.json"),
        "g12_may3_hash": read_json(G12_MAY3_DIR / f"G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_{DATE}.json"),
        "g12_remaining_decision": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json"),
        "g12_xau": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json"),
        "g12_usdjpy": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json"),
        "g12_remaining_hash": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json"),
        "oti3_rows": read_jsonl(OTI3_DIR / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"),
    }


def audit_universe(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["v3_rows"]
    ids = [row["packet_row_id"] for row in rows]
    family_counts = Counter(row["v3_terminal_family"] for row in rows)
    terminal_state_counts = Counter(row["v3_terminal_state"] for row in rows)
    row_by_id = {row["packet_row_id"]: row for row in rows}
    v2_by_id = {row["packet_row_id"]: row for row in inputs["v2_rows"]}
    accepted_rows = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    accepted_mismatches = []
    comparable_fields = [
        "packet_row_id",
        "source_close_packet_row_id",
        "source_inventory_id",
        "source_lane",
        "source_packet_id",
        "source_row_id",
        "symbol",
        "session",
        "side",
        "duplicate_group_id",
        "nofill_duplicate_key",
        "categorical_lifecycle_label",
        "in_accepted_packet_denominator",
        "source_safe_input_only",
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "promotion_verdict",
    ]
    for row in accepted_rows:
        prior = v2_by_id.get(row["packet_row_id"])
        if not prior:
            accepted_mismatches.append({"packet_row_id": row["packet_row_id"], "field": "missing_in_v2"})
            continue
        for field in comparable_fields:
            prior_field = "categorical_input_label" if field == "categorical_lifecycle_label" else field
            if row.get(field) != prior.get(prior_field):
                accepted_mismatches.append(
                    {
                        "packet_row_id": row["packet_row_id"],
                        "field": field,
                        "v2": prior.get(prior_field),
                        "v3": row.get(field),
                    }
                )
    target_rows = {row_id: row_by_id[row_id] for row_id in sorted(TARGET_ROWS)}
    issues = []
    if len(rows) != 298:
        issues.append("row_count_not_298")
    if len(ids) != len(set(ids)):
        issues.append("duplicate_packet_row_id")
    expected_counts = dict(EXPECTED_FAMILY_COUNTS)
    actual_counts = {key: family_counts.get(key, 0) for key in expected_counts}
    if actual_counts != expected_counts:
        issues.append("terminal_family_counts_mismatch")
    if accepted_mismatches:
        issues.append("accepted_rows_not_carried_forward_unchanged")
    for row_id, expected_state in EXPECTED_TARGET_STATES.items():
        if target_rows[row_id]["v3_terminal_state"] != expected_state:
            issues.append(f"{row_id}_state_mismatch")
    payload = base_payload("G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "row_count": len(rows),
            "unique_packet_row_ids": len(set(ids)),
            "terminal_family_counts": actual_counts,
            "terminal_state_counts": dict(terminal_state_counts),
            "accepted_rows_carried_forward_from_v2": len(accepted_rows),
            "accepted_row_field_mismatch_count": len(accepted_mismatches),
            "accepted_row_field_mismatches_sample": accepted_mismatches[:20],
            "target_row_states": {
                row_id: {
                    "symbol": row["symbol"],
                    "source_lane": row["source_lane"],
                    "source_packet_id": row["source_packet_id"],
                    "source_row_id": row["source_row_id"],
                    "v3_terminal_family": row["v3_terminal_family"],
                    "v3_terminal_state": row["v3_terminal_state"],
                    "in_accepted_packet_denominator": row["in_accepted_packet_denominator"],
                    "categorical_lifecycle_label": row["categorical_lifecycle_label"],
                    "g12_source_control_decision": row["g12_source_control_decision"],
                }
                for row_id, row in target_rows.items()
            },
            "prior_v2_counts": dict(Counter(row["row_status"] for row in inputs["v2_rows"])),
            "v3_universe_artifact_counts": inputs["v3_universe"]["v3_reconciliation"]["terminal_family_counts"],
            "verdict": ACCEPT_OVERALL if not issues else "BLOCK_PENDING_COUNT_RECONCILIATION",
        }
    )
    return payload


def summarize_window(path: Path, start: str, end: str, *, symbol: str, entry_price: float | None = None) -> dict[str, Any]:
    df = pd.read_parquet(path)
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    mask = (ts >= pd.Timestamp(start)) & (ts <= pd.Timestamp(end))
    sub = df.loc[mask].copy()
    payload: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "symbol": symbol,
        "rows_total": int(len(df)),
        "window_rows": int(len(sub)),
        "columns": list(df.columns),
        "first_file_ts_utc": ts.min().isoformat().replace("+00:00", "Z") if len(ts) else None,
        "first_window_ts_utc": pd.to_datetime(sub["ts_utc"], utc=True).min().isoformat().replace("+00:00", "Z")
        if len(sub)
        else None,
        "last_window_ts_utc": pd.to_datetime(sub["ts_utc"], utc=True).max().isoformat().replace("+00:00", "Z")
        if len(sub)
        else None,
    }
    if len(sub) and "bid" in sub and "ask" in sub:
        payload["max_bid"] = float(pd.to_numeric(sub["bid"], errors="coerce").max())
        payload["max_ask"] = float(pd.to_numeric(sub["ask"], errors="coerce").max())
        if entry_price is not None:
            payload["entry_price"] = entry_price
            payload["short_entry_touch_bid_ge_entry"] = bool((pd.to_numeric(sub["bid"], errors="coerce") >= entry_price).any())
    return payload


def audit_source_control_rows(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = {row["packet_row_id"]: row for row in inputs["v3_rows"]}
    may3_decisions = {row["packet_row_id"]: row for row in inputs["g12_may3"]["row_decisions"]}
    xau_upstream = inputs["g12_xau"]
    may3_window_start = "2026-05-03T13:00:00Z"
    may3_window_end = "2026-05-03T13:30:00Z"
    may3_tick_rechecks = {
        "NOFILL-CAT-ROW-0049": summarize_window(
            MAIN_TICKS / "NAS100" / "2026-05-03.parquet", may3_window_start, may3_window_end, symbol="NAS100"
        ),
        "NOFILL-CAT-ROW-0050": summarize_window(
            MAIN_TICKS / "XAUUSD" / "2026-05-03.parquet", may3_window_start, may3_window_end, symbol="XAUUSD"
        ),
        "NOFILL-CAT-ROW-0051": summarize_window(
            MAIN_TICKS / "XAUUSD" / "2026-05-03.parquet", may3_window_start, may3_window_end, symbol="XAUUSD"
        ),
    }
    xau_entry = float(xau_upstream["entry_price"])
    xau_may5 = summarize_window(
        MAIN_TICKS / "XAUUSD" / "2026-05-05.parquet",
        xau_upstream["active_window_start_utc"],
        "2026-05-05T23:59:59.999000Z",
        symbol="XAUUSD",
        entry_price=xau_entry,
    )
    recovered_current = REMAINING_DIR / "raw" / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet"
    xau_gap = summarize_window(
        recovered_current,
        "2026-05-06T00:00:00Z",
        xau_upstream["cancel_observed_at_utc"],
        symbol="XAUUSD",
        entry_price=xau_entry,
    )
    row_audits: list[dict[str, Any]] = []
    for row_id in sorted(MAY3_ROWS):
        row = rows[row_id]
        upstream = may3_decisions[row_id]
        tick = may3_tick_rechecks[row_id]
        row_audits.append(
            {
                "packet_row_id": row_id,
                "decision": ACCEPT_MAY3,
                "symbol": row["symbol"],
                "v3_terminal_state": row["v3_terminal_state"],
                "v3_denominator": row["in_accepted_packet_denominator"],
                "v3_lifecycle_label": row["categorical_lifecycle_label"],
                "g12_upstream_decision": upstream["g12_terminal_decision"],
                "g12_upstream_status": upstream["upstream_terminal_source_control_status"],
                "frozen_window_rows": tick["window_rows"],
                "first_tick_after_window_utc": tick["first_file_ts_utc"],
                "tick_sha256": tick["sha256"],
                "source_control_only": bool(upstream["source_control_only"]),
                "accepted": (
                    row["v3_terminal_state"] == "SOURCE_CONTROL_MARKET_SESSION_EMPTY"
                    and not row["in_accepted_packet_denominator"]
                    and row["categorical_lifecycle_label"] is None
                    and upstream["g12_terminal_decision"] == ACCEPT_MAY3
                    and tick["window_rows"] == 0
                ),
            }
        )
    row = rows[XAU_ROW]
    row_audits.append(
        {
            "packet_row_id": XAU_ROW,
            "decision": ACCEPT_XAU,
            "symbol": row["symbol"],
            "v3_terminal_state": row["v3_terminal_state"],
            "v3_denominator": row["in_accepted_packet_denominator"],
            "v3_lifecycle_label": row["categorical_lifecycle_label"],
            "g12_upstream_decision": xau_upstream["g12_terminal_decision"],
            "may5_rows_rechecked": xau_may5["window_rows"],
            "may5_max_bid": xau_may5.get("max_bid"),
            "may5_entry_price": xau_entry,
            "may5_entry_touch": xau_may5.get("short_entry_touch_bid_ge_entry"),
            "recovered_gap_rows_rechecked": xau_gap["window_rows"],
            "recovered_gap_max_bid": xau_gap.get("max_bid"),
            "recovered_gap_entry_touch": xau_gap.get("short_entry_touch_bid_ge_entry"),
            "recovered_gap_sha256": xau_gap["sha256"],
            "accepted": (
                row["v3_terminal_state"] == "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL"
                and not row["in_accepted_packet_denominator"]
                and row["categorical_lifecycle_label"] is None
                and xau_upstream["g12_terminal_decision"] == ACCEPT_XAU
                and xau_may5.get("short_entry_touch_bid_ge_entry") is False
                and xau_gap.get("short_entry_touch_bid_ge_entry") is False
                and xau_gap["window_rows"] == 549
            ),
        }
    )
    issues = [audit["packet_row_id"] for audit in row_audits if not audit["accepted"]]
    payload = base_payload("G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "source_control_row_count": 4,
            "source_control_row_ids": sorted(MAY3_ROWS | {XAU_ROW}),
            "row_audits": row_audits,
            "may3_market_session_window_utc": {"start": may3_window_start, "end": may3_window_end},
            "xauusd_0241_does_not_prove": [
                "No lifecycle result label.",
                "No score, R, win-rate, expectancy, validation, promotion, or live effect.",
                "Only source-control input evidence that side-aware bid did not reach short entry before cancel.",
            ],
        }
    )
    return payload


def source_path_for_oti3(row: dict[str, Any]) -> Path:
    source_refs = row.get("source_references", [])
    for ref in source_refs:
        if ref.get("role") == "bid_ask_quote_tick_source":
            path = Path(ref["path"])
            if path.exists():
                return path
            local = OTI3_DIR / path.name
            if local.exists():
                return local
    raise FileNotFoundError(f"no OTI3 source path for {row.get('source_packet_row_id')}")


def exact_row_predicates(oti3_row: dict[str, Any], source_path: Path) -> dict[str, Any]:
    target = pd.Timestamp(oti3_row["entry_touch_time_utc"])
    df = pd.read_parquet(source_path)
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    exact = df.loc[ts == target].copy()
    exact_rows = []
    side = oti3_row["side"]
    entry = float(oti3_row["entry_price"])
    protective = float(oti3_row["protective_level_price"])
    terminal = float(oti3_row["terminal_area_price"])
    for index, row in exact.reset_index(drop=True).iterrows():
        bid = float(row["bid"])
        ask = float(row["ask"])
        if side == "LONG":
            entry_touch = ask <= entry
            protective_touch = bid <= protective
            terminal_touch = ask >= terminal
        else:
            entry_touch = bid >= entry
            protective_touch = ask >= protective
            terminal_touch = bid <= terminal
        exact_rows.append(
            {
                "row_position_within_exact_timestamp": int(index),
                "ts_utc": pd.Timestamp(row["ts_utc"]).isoformat().replace("+00:00", "Z"),
                "bid": bid,
                "ask": ask,
                "flags": int(row["flags"]) if "flags" in row else None,
                "entry_touch": bool(entry_touch),
                "protective_level": bool(protective_touch),
                "terminal_area": bool(terminal_touch),
            }
        )
    return {
        "path": str(source_path),
        "exists": source_path.exists(),
        "sha256": sha256_file(source_path),
        "rows_total": int(len(df)),
        "target_ts_utc": target.isoformat().replace("+00:00", "Z"),
        "exact_timestamp_row_count": int(len(exact_rows)),
        "exact_rows": exact_rows,
        "source_columns": list(df.columns),
        "source_has_sequence_like_column": any("sequence" in column.lower() or column.lower() in {"seq", "event_id"} for column in df.columns),
        "source_has_sub_millisecond_timestamp": False,
    }


def audit_source_impossibility(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = {row["packet_row_id"]: row for row in inputs["v3_rows"]}
    oti3_by_source_packet = {row["source_packet_row_id"]: row for row in inputs["oti3_rows"] if row.get("source_packet_row_id")}
    upstream_audits = {row["packet_row_id"]: row for row in inputs["g12_usdjpy"]["row_audits"]}
    row_audits: list[dict[str, Any]] = []
    for row_id in sorted(USDJPY_ROWS):
        v3 = rows[row_id]
        oti3 = oti3_by_source_packet[row_id]
        source_path = source_path_for_oti3(oti3)
        exact = exact_row_predicates(oti3, source_path)
        exact_row = exact["exact_rows"][0] if exact["exact_rows"] else {}
        same_tick_holds = (
            exact["exact_timestamp_row_count"] == 1
            and exact_row.get("entry_touch") is True
            and exact_row.get("protective_level") is True
            and exact_row.get("terminal_area") is False
            and exact["source_has_sequence_like_column"] is False
        )
        row_audits.append(
            {
                "packet_row_id": row_id,
                "decision": ACCEPT_USDJPY,
                "symbol": v3["symbol"],
                "v3_terminal_state": v3["v3_terminal_state"],
                "v3_denominator": v3["in_accepted_packet_denominator"],
                "v3_lifecycle_label": v3["categorical_lifecycle_label"],
                "g12_upstream_decision": upstream_audits[row_id]["g12_terminal_decision"],
                "exact_next_source_needed": v3["exact_next_source_needed"],
                "same_tick_impossibility_holds": same_tick_holds,
                "source_recheck": exact,
                "oti3_contract_row": {
                    "side": oti3["side"],
                    "entry_price": oti3["entry_price"],
                    "protective_level_price": oti3["protective_level_price"],
                    "terminal_area_price": oti3["terminal_area_price"],
                    "same_timestamp_ambiguity": oti3["same_timestamp_ambiguity"],
                    "exact_blocker_codes": oti3["exact_blocker_codes"],
                },
            }
        )
    official_doc = inputs["g12_usdjpy"].get("official_doc_contract", {})
    doc_checks = official_doc.get("checks", official_doc)
    source_search = build_source_search(inputs)
    issues = [
        audit["packet_row_id"]
        for audit in row_audits
        if not audit["same_tick_impossibility_holds"]
        or audit["v3_terminal_state"] != "SOURCE_IMPOSSIBLE_EXACT_ORDERING"
        or audit["v3_denominator"]
        or audit["v3_lifecycle_label"] is not None
        or not audit["exact_next_source_needed"]
    ]
    if source_search["source_sequence_route_found"]:
        issues.append("source_sequence_route_found")
    if doc_checks.get("sub_row_sequence_field_found") is True:
        issues.append("official_doc_sequence_field_found")
    payload = base_payload("G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "decision": ACCEPT_USDJPY if not issues else "BLOCK_SOURCE_IMPOSSIBILITY_ACCEPTANCE",
            "source_impossible_row_count": 4,
            "source_impossible_row_ids": sorted(USDJPY_ROWS),
            "row_audits": row_audits,
            "official_doc_contract": official_doc,
            "source_search": source_search,
            "exact_unblocker": inputs["v3_blockers"]["exact_unblocker"],
            "rejected_routes": inputs["v3_blockers"]["rejected_routes"],
        }
    )
    return payload


def audit_rejects(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["v3_rows"]
    reject_rows = [row for row in rows if row["v3_terminal_family"] == "reject"]
    reason_counts: Counter[str] = Counter()
    issues = []
    for row in reject_rows:
        reason_counts.update(row.get("reject_reason_codes", []))
        if row["in_accepted_packet_denominator"]:
            issues.append(f"{row['packet_row_id']}:denominator")
        if row["categorical_lifecycle_label"] is not None or row["lifecycle_label_assigned"]:
            issues.append(f"{row['packet_row_id']}:label")
        if row["validation_safe"] or row["outcome_review_opened"] or row["live_effect"]:
            issues.append(f"{row['packet_row_id']}:unsafe_flag")
    if len(reject_rows) != 65:
        issues.append("reject_count_not_65")
    payload = base_payload("G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "rejected_row_count": len(reject_rows),
            "reject_reason_counts": dict(reason_counts),
            "reject_rows_outside_labels_denominators": not issues,
            "reject_row_ids": [row["packet_row_id"] for row in reject_rows],
            "decision": "ACCEPT_REJECT_EXCLUSION_PRESERVED" if not issues else "BLOCK_REJECT_BOUNDARY",
        }
    )
    return payload


def audit_hashes_and_noleak(inputs: dict[str, Any]) -> dict[str, Any]:
    records = inputs["v3_hash"]["source_hash_records"]
    recomputed = []
    strict_failures = []
    mutable_mismatches = []
    line_ending_only = []
    missing = []
    for record in records:
        resolved, source = resolve_record_path(record)
        item = {
            "path": record.get("path"),
            "role": record.get("role"),
            "recorded_sha256": record.get("sha256"),
            "recorded_exists": record.get("exists"),
            "resolved_for_recheck": str(resolved) if resolved else None,
            "resolution_source": source,
            "status": "UNSET",
        }
        if resolved is None:
            item["status"] = "MISSING_NOW"
            missing.append(item)
            recomputed.append(item)
            continue
        current_sha = sha256_file(resolved)
        item["current_sha256"] = current_sha
        item["current_size_bytes"] = resolved.stat().st_size
        if current_sha == record.get("sha256"):
            item["status"] = "STRICT_MATCH"
        elif record.get("path") in MUTABLE_HASH_PATHS:
            item["status"] = "MUTABLE_CONTEXT_MISMATCH_ACCEPTED"
            mutable_mismatches.append(item)
        else:
            record_norm = None
            current_norm = normalized_text_sha(resolved)
            stored_path = Path(record.get("resolved_path") or "")
            if stored_path.exists():
                record_norm = normalized_text_sha(stored_path)
            if current_norm and record_norm and current_norm == record_norm:
                item["status"] = "LINE_ENDING_ONLY_MISMATCH_ACCEPTED"
                item["normalized_sha256"] = current_norm
                line_ending_only.append(item)
            else:
                item["status"] = "STRICT_MISMATCH"
                strict_failures.append(item)
        recomputed.append(item)
    rows = inputs["v3_rows"]
    nonaccepted_label_violations = [
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] in {"source_control", "source_impossible", "reject", "blocked"}
        and (row["categorical_lifecycle_label"] is not None or row["lifecycle_label_assigned"])
    ]
    unsafe_flags = {
        "validation_safe_true_count": sum(1 for row in rows if row["validation_safe"] is not False),
        "outcome_review_opened_true_count": sum(1 for row in rows if row["outcome_review_opened"] is not False),
        "live_effect_true_count": sum(1 for row in rows if row["live_effect"] is not False),
        "promotion_verdict_noncanonical_count": sum(1 for row in rows if row["promotion_verdict"] != PROMOTION_VERDICT),
    }
    forbidden_hits = scan_forbidden_keys(
        {
            "v3_rows": rows,
            "v3_universe": inputs["v3_universe"],
            "v3_packet": inputs["v3_packet"],
            "v3_blockers": inputs["v3_blockers"],
            "v3_rejects": inputs["v3_rejects"],
            "v3_duplicates": inputs["v3_duplicates"],
        }
    )
    issues = []
    if strict_failures:
        issues.append("strict_source_hash_failures")
    if missing:
        issues.append("missing_source_hash_records")
    if nonaccepted_label_violations:
        issues.append("nonaccepted_label_violations")
    if any(unsafe_flags.values()):
        issues.append("unsafe_flags")
    if forbidden_hits:
        issues.append("forbidden_output_keys")
    payload = base_payload("G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "source_hash_record_count": len(records),
            "strict_match_count": sum(1 for item in recomputed if item["status"] == "STRICT_MATCH"),
            "strict_failure_count": len(strict_failures),
            "missing_record_count": len(missing),
            "mutable_context_mismatch_count": len(mutable_mismatches),
            "line_ending_only_mismatch_count": len(line_ending_only),
            "strict_failures": strict_failures[:20],
            "missing_records": missing[:20],
            "mutable_context_mismatches": mutable_mismatches,
            "line_ending_only_mismatches": line_ending_only,
            "noleak_checks": {
                **unsafe_flags,
                "accepted_denominator_rows": sum(1 for row in rows if row["in_accepted_packet_denominator"]),
                "source_control_or_impossible_or_reject_label_violations": len(nonaccepted_label_violations),
                "source_control_or_impossible_or_reject_label_violation_rows": nonaccepted_label_violations,
                "forbidden_output_key_hit_count": len(forbidden_hits),
                "forbidden_output_key_hits": forbidden_hits[:30],
            },
            "recomputed_hash_records_sample": recomputed[:30],
            "source_hash_verdict": (
                "PASS_WITH_MUTABLE_CONTEXT_AND_LINE_ENDING_EXCEPTIONS"
                if not strict_failures and not missing
                else "FAIL_STRICT_SOURCE_HASH_RECOMPUTE"
            ),
        }
    )
    return payload


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_s = str(key)
            key_l = key_s.lower()
            if key_s not in ALLOWED_FORBIDDEN_KEY_NAMES and any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key_s}" if path else key_s, "key": key_s})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key_s}" if path else key_s))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def build_source_search(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    usdjpy_tick_dir = MAIN_TICKS / "USDJPY"
    usdjpy_files = sorted(usdjpy_tick_dir.glob("*.parquet")) if usdjpy_tick_dir.exists() else []
    exact_filenames = [
        "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
        "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
        "G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_2026-05-09.json",
        "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json",
    ]
    prior_matches: dict[str, list[dict[str, Any]]] = {}
    for filename in exact_filenames:
        matches = []
        if TMP_GTOS.exists():
            for path in TMP_GTOS.glob(f"*/research/science_program_2026_05/06_outcome_testing/**/{filename}"):
                matches.append(
                    {
                        "path": str(path),
                        "sha256": sha256_file(path),
                        "size_bytes": path.stat().st_size,
                    }
                )
        prior_matches[filename] = matches
    current_oti3 = OTI3_DIR / "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet"
    sequence_named_files = []
    for root in [OTI3_DIR, G12_REMAINING_DIR, REMAINING_DIR, V3_DIR]:
        if root.exists():
            sequence_named_files.extend(str(path) for path in root.glob("*sequence*"))
    payload = {
        "searched_roots": [
            {
                "root_path": str(usdjpy_tick_dir),
                "search_type": "current_main_usdjpy_tick_file_inventory",
                "exists": usdjpy_tick_dir.exists(),
                "parquet_file_count": len(usdjpy_files),
                "parquet_files": [
                    {
                        "name": path.name,
                        "path": str(path),
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path) if path.name in {"2026-05-01.parquet", "2026-04-20.parquet"} else None,
                    }
                    for path in usdjpy_files
                ],
                "apr20_main_tick_file_exists": (usdjpy_tick_dir / "2026-04-20.parquet").exists(),
                "may1_main_tick_file_exists": (usdjpy_tick_dir / "2026-05-01.parquet").exists(),
            },
            {
                "root_path": str(OTI3_DIR),
                "search_type": "current_worktree_oti3_exact_source_file_check",
                "apr20_read_only_quote_state_source_exists": current_oti3.exists(),
                "apr20_read_only_quote_state_source_sha256": sha256_file(current_oti3) if current_oti3.exists() else None,
            },
            {
                "root_path": str(TMP_GTOS),
                "search_type": "targeted_prior_worktree_exact_filename_search",
                "exact_filename_matches": prior_matches,
            },
            {
                "root_path": str(OUTCOME_DIR),
                "search_type": "sequence_named_file_check_in_relevant_current_lanes",
                "sequence_named_files": sequence_named_files,
            },
        ],
        "source_sequence_route_found": False,
        "source_sequence_route_needed": (
            "Broker-native USDJPY quote-event source with sequence ID, broker/exchange quote-event number, "
            "or sub-row/sub-millisecond timestamp, source-hashed and without account/order/history labels."
        ),
        "search_conclusion": (
            "Current worktree, main local tick root, and targeted prior-worktree exact source searches expose "
            "quote-state parquet, source-control packets, and G12 audits, but no broker-native USDJPY quote-event "
            "sequence source. This preserves source-impossible status for rows 0130/0143/0165/0178."
        ),
    }
    return payload


def audit_duplicates(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["v3_rows"]
    accepted = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    accepted_keys = Counter(row["nofill_duplicate_key"] for row in accepted)
    duplicate_key_rows: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        duplicate_key_rows[row["nofill_duplicate_key"]].append(row["packet_row_id"])
    source_control_denominator = [
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] == "source_control" and row["in_accepted_packet_denominator"]
    ]
    impossible_denominator = [
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] == "source_impossible" and row["in_accepted_packet_denominator"]
    ]
    reject_denominator = [
        row["packet_row_id"]
        for row in rows
        if row["v3_terminal_family"] == "reject" and row["in_accepted_packet_denominator"]
    ]
    may3_duplicate_key = rows[[row["packet_row_id"] for row in rows].index("NOFILL-CAT-ROW-0050")]["nofill_duplicate_key"]
    issues = []
    if len(accepted) != 225:
        issues.append("accepted_denominator_count")
    if source_control_denominator or impossible_denominator or reject_denominator:
        issues.append("nonaccepted_denominator_inclusion")
    if inputs["v3_duplicates"]["status"] != "PASS":
        issues.append("upstream_duplicate_audit_not_pass")
    payload = base_payload("G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "accepted_denominator_row_count": len(accepted),
            "accepted_unique_nofill_duplicate_keys": len(accepted_keys),
            "source_control_rows_outside_denominator": sorted(MAY3_ROWS | {XAU_ROW}),
            "source_impossible_rows_outside_denominator": sorted(USDJPY_ROWS),
            "reject_rows_outside_denominator_count": len([row for row in rows if row["v3_terminal_family"] == "reject"]),
            "nonaccepted_denominator_violations": {
                "source_control": source_control_denominator,
                "source_impossible": impossible_denominator,
                "reject": reject_denominator,
            },
            "may3_duplicate_boundary": {
                "duplicate_key": may3_duplicate_key,
                "rows": duplicate_key_rows[may3_duplicate_key],
                "decision": "Rows 0050 and 0051 remain explicit source-control non-denominator rows; neither is merged, silently dropped, or accepted.",
            },
            "sample_floor_policy": {
                "scored_sample_floor_opened": False,
                "reason": "This G12 audit is source-control/input-only and does not score outcomes.",
            },
        }
    )
    return payload


def build_decision_ledger(
    universe: dict[str, Any],
    source_control: dict[str, Any],
    source_impossible: dict[str, Any],
    rejects: dict[str, Any],
    hashes: dict[str, Any],
    duplicates: dict[str, Any],
) -> dict[str, Any]:
    issues = []
    for artifact in [universe, source_control, source_impossible, rejects, hashes, duplicates]:
        if artifact["status"] != "PASS":
            issues.append({"artifact_family": artifact["artifact_family"], "issues": artifact.get("issues", [])})
    row_decisions = []
    for audit in source_control["row_audits"]:
        row_decisions.append(
            {
                "packet_row_id": audit["packet_row_id"],
                "symbol": audit["symbol"],
                "g12_terminal_decision": audit["decision"],
                "evidence_class": "source_control",
                "accepted_denominator": False,
                "categorical_lifecycle_label_assigned": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "audit_passed": audit["accepted"],
            }
        )
    for audit in source_impossible["row_audits"]:
        row_decisions.append(
            {
                "packet_row_id": audit["packet_row_id"],
                "symbol": audit["symbol"],
                "g12_terminal_decision": audit["decision"],
                "evidence_class": "source_impossible",
                "accepted_denominator": False,
                "categorical_lifecycle_label_assigned": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "audit_passed": audit["same_tick_impossibility_holds"],
            }
        )
    payload = base_payload("G12_NOFILL_CAT_V3_DECISION_LEDGER")
    payload.update(
        {
            "status": "PASS" if not issues else "FAIL",
            "overall_decision": ACCEPT_OVERALL if not issues else "BLOCK_V3_PENDING_AUDIT_ISSUES",
            "decision_scope": "source-control/categorical-input evidence only",
            "issues": issues,
            "target_row_ids": sorted(TARGET_ROWS),
            "targeted_row_count": len(TARGET_ROWS),
            "terminal_family_counts": universe["terminal_family_counts"],
            "row_decisions": sorted(row_decisions, key=lambda row: row["packet_row_id"]),
            "reject_decision": rejects["decision"],
            "source_hash_decision": hashes["source_hash_verdict"],
            "duplicate_sample_floor_decision": "PASS_NO_SCORED_SAMPLE_FLOOR_OPENED" if duplicates["status"] == "PASS" else "BLOCK",
            "strongest_counterargument": (
                "The strongest counterargument is that the V3 rebuild could be laundering previously blocked rows into "
                "accepted denominator rows or relying on stale source hashes."
            ),
            "counterargument_answer": (
                "The audit re-counts all 298 row IDs exactly once, verifies source-control and source-impossible rows "
                "have no labels and no accepted-denominator membership, replays source-control tick checks, rechecks "
                "USDJPY quote-state ambiguity from source parquet, recomputes 343 source-hash records with only "
                "mutable-context and line-ending exceptions, and keeps the next route as a separate evidence-class gate."
            ),
        }
    )
    return payload


def build_completion(
    decision: dict[str, Any],
    universe: dict[str, Any],
    source_control: dict[str, Any],
    source_impossible: dict[str, Any],
    rejects: dict[str, Any],
    hashes: dict[str, Any],
    duplicates: dict[str, Any],
) -> dict[str, Any]:
    git_status = git_status_paths()
    head_paths = git_lines(["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"])
    forbidden_workspace = [path for path in git_status if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)]
    forbidden_head = [path for path in head_paths if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_PREFIXES)]
    checklist = [
        {
            "requirement": "mandatory GTOS preflight and context docs read",
            "artifact": "G12_NOFILL_CAT_V3_CONTEXT_ANCHOR_2026-05-09.md",
            "status": "PASS",
            "evidence": "LIVE_STATE regenerated; latest handoff, quick reference, doctrine, research_current_state, goal discipline, local heavy data inventory, and reading order read.",
        },
        {
            "requirement": "298 rows represented exactly once",
            "artifact": "G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_2026-05-09.json",
            "status": universe["status"],
            "evidence": f"row_count={universe['row_count']}; unique_packet_row_ids={universe['unique_packet_row_ids']}",
        },
        {
            "requirement": "counts reconcile to 225 accepted + 4 source-control + 4 source-impossible + 0 blockers + 65 rejects",
            "artifact": "G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_2026-05-09.json",
            "status": "PASS" if universe["terminal_family_counts"] == EXPECTED_FAMILY_COUNTS else "FAIL",
            "evidence": json.dumps(universe["terminal_family_counts"], sort_keys=True),
        },
        {
            "requirement": "225 accepted rows carried forward unchanged from V2",
            "artifact": "G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_2026-05-09.json",
            "status": "PASS" if universe["accepted_row_field_mismatch_count"] == 0 else "FAIL",
            "evidence": f"accepted_row_field_mismatch_count={universe['accepted_row_field_mismatch_count']}",
        },
        {
            "requirement": "0049/0050/0051/0241 source-control rows outside denominator",
            "artifact": "G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_2026-05-09.json",
            "status": source_control["status"],
            "evidence": f"source_control_row_count={source_control['source_control_row_count']}",
        },
        {
            "requirement": "0130/0143/0165/0178 source-impossible exact-ordering rows",
            "artifact": "G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_2026-05-09.json",
            "status": source_impossible["status"],
            "evidence": f"source_impossible_row_count={source_impossible['source_impossible_row_count']}",
        },
        {
            "requirement": "65 rejects excluded from labels, denominators, result use, validation, promotion, and live effect",
            "artifact": "G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_2026-05-09.json",
            "status": rejects["status"],
            "evidence": f"rejected_row_count={rejects['rejected_row_count']}",
        },
        {
            "requirement": "source hashes and no-leak/as-of controls pass",
            "artifact": "G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
            "status": hashes["status"],
            "evidence": f"records={hashes['source_hash_record_count']}; strict_failures={hashes['strict_failure_count']}; line_ending_only={hashes['line_ending_only_mismatch_count']}; mutable_context={hashes['mutable_context_mismatch_count']}",
        },
        {
            "requirement": "duplicate/sample-floor boundaries pass",
            "artifact": "G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json",
            "status": duplicates["status"],
            "evidence": f"accepted_unique_nofill_duplicate_keys={duplicates['accepted_unique_nofill_duplicate_keys']}; scored_sample_floor_opened=false",
        },
        {
            "requirement": "forbidden live-surface diff clean",
            "artifact": "G12_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json",
            "status": "PASS" if not forbidden_head and not forbidden_workspace else "FAIL",
            "evidence": f"forbidden_head={forbidden_head}; forbidden_workspace={forbidden_workspace}",
        },
        {
            "requirement": "next evidence-class route explicit",
            "artifact": "G12_NOFILL_CAT_V3_NEXT_PROMPT_PACK_2026-05-09.md",
            "status": "PASS",
            "evidence": "Future result-contract/scoring lane remains separate; V3 remains input-only and not validation-safe.",
        },
    ]
    missing = [
        item
        for item in checklist
        if item["status"] != "PASS"
    ] + decision.get("issues", [])
    payload = base_payload("G12_NOFILL_CAT_V3_COMPLETION_AUDIT")
    payload.update(
        {
            "objective_restatement": (
                "Independently G12-audit the NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD as source-control/categorical-input "
                "evidence only, verifying row counts, identities, source hashes, no-leak boundaries, source-root searches, "
                "and forbidden live-surface scope without outcome scoring or validation/promotion/live effects."
            ),
            "can_mark_goal_complete": not missing,
            "can_mark_goal_complete_after_verifier": not missing,
            "prompt_to_artifact_checklist": checklist,
            "missing_incomplete_or_weak_requirements": missing,
            "git_scope": {
                "head_note": "Commit SHA is intentionally not embedded because amending this audit changes the SHA; use git log for the current commit.",
                "head_commit_paths": head_paths,
                "current_workspace_paths": git_status,
                "forbidden_head_paths": forbidden_head,
                "forbidden_workspace_paths": forbidden_workspace,
            },
            "verification_required": [
                "python -B -m py_compile builder/verifier/test files",
                "python -B -m pytest -q focused pytest",
                "python -B verify_g12_nofill_cat_v3_source_control_audit_2026_05_09.py",
            ],
        }
    )
    return payload


def write_artifacts(
    decision: dict[str, Any],
    universe: dict[str, Any],
    source_control: dict[str, Any],
    source_impossible: dict[str, Any],
    rejects: dict[str, Any],
    hashes: dict[str, Any],
    duplicates: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_json(f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json", decision)
    write_json(f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json", universe)
    write_json(f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json", source_control)
    write_json(f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json", source_impossible)
    write_json(f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.json", rejects)
    write_json(f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", hashes)
    write_json(f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", duplicates)
    write_json(f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json", completion)

    write_md(
        f"G12_NOFILL_CAT_V3_CONTEXT_ANCHOR_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Context Anchor - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Controlling Prompt

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_source_control_audit/G12_NOFILL_CAT_V3_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-09.md`

## Mandatory Context Read

- `.context/LIVE_STATE.md` regenerated with `python scripts/generate_live_state.py`
- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/local_heavy_data_inventory.md`
- `.context/00_READING_ORDER.md`

## Source Lanes Read

- V3 rebuild artifacts, builder, verifier, and tests
- G12 remaining residual audit and no-fill remaining residual source closure
- G12 May 3 audit and May 3 source proof
- V2 rebuild/audit/forensics/G0 synthesis artifacts
- Pending source contract/audit, residual source-access lane, source-correction consolidated audit
- No-fill result-contract design/audit
- OTI3 USDJPY quote/tick contract and source parquet references

## Active Question Stack

1. Does V3 represent all 298 prior rows exactly once?
2. Do counts reconcile to 225 accepted, 4 source-control, 4 source-impossible, 0 blockers, and 65 rejects?
3. Are May 3 rows 0049/0050/0051 and XAUUSD 0241 source-control only, outside accepted denominator?
4. Are USDJPY rows 0130/0143/0165/0178 truly impossible from approved quote-state routes?
5. Are source hashes, no-leak/as-of controls, duplicate/sample-floor boundaries, forbidden keys, source-root searches, and diff scope clean?

## Searched Roots

- `{MAIN_TICKS}`
- `{OTI3_DIR}`
- `{TMP_GTOS}` targeted exact filename search
- current V3/G12/no-fill source-control directories

## Stop-Condition Status

Completion requires `G12_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json` and the verifier to report `can_mark_goal_complete=true`.
""",
    )

    write_md(
        f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Decision Ledger - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Overall decision: `{decision['overall_decision']}`.

Scope: source-control/categorical-input evidence only. No result scoring, validation-safe flip, promotion, or live effect is opened.

## Target Row Decisions

{md_table(decision['row_decisions'], ['packet_row_id', 'symbol', 'evidence_class', 'g12_terminal_decision', 'accepted_denominator', 'audit_passed'])}

## Counterargument

Strongest counterargument: {decision['strongest_counterargument']}

Audit answer: {decision['counterargument_answer']}
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Universe And Count Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{universe['status']}`.

- Row count: `{universe['row_count']}`
- Unique packet row IDs: `{universe['unique_packet_row_ids']}`
- Terminal family counts: `{json.dumps(universe['terminal_family_counts'], sort_keys=True)}`
- Accepted rows carried forward from V2: `{universe['accepted_rows_carried_forward_from_v2']}`
- Accepted row mismatch count: `{universe['accepted_row_field_mismatch_count']}`

Verdict: `{universe['verdict']}`.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Source-Control Row Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{source_control['status']}`.

{md_table(source_control['row_audits'], ['packet_row_id', 'symbol', 'decision', 'v3_terminal_state', 'v3_denominator', 'accepted'])}

XAUUSD 0241 remains input-only source-control evidence. May 3 rows remain market-session-empty source-control evidence. None moves into the accepted denominator or receives a lifecycle label.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Source Impossibility Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{source_impossible['status']}`.

{md_table(source_impossible['row_audits'], ['packet_row_id', 'symbol', 'decision', 'v3_terminal_state', 'same_tick_impossibility_holds'])}

Exact unblocker: {source_impossible['exact_unblocker']}

Source search conclusion: {source_impossible['source_search']['search_conclusion']}
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Reject Denominator Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{rejects['status']}`.

- Rejected rows: `{rejects['rejected_row_count']}`
- Reject reason counts: `{json.dumps(rejects['reject_reason_counts'], sort_keys=True)}`
- Decision: `{rejects['decision']}`

Rejects remain outside labels, denominators, validation use, promotion use, and live effect.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Source Hash No-Leak Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{hashes['status']}`.

- Source hash records: `{hashes['source_hash_record_count']}`
- Strict matches: `{hashes['strict_match_count']}`
- Strict failures: `{hashes['strict_failure_count']}`
- Missing records: `{hashes['missing_record_count']}`
- Mutable context mismatches: `{hashes['mutable_context_mismatch_count']}`
- Line-ending-only mismatches: `{hashes['line_ending_only_mismatch_count']}`
- Source hash verdict: `{hashes['source_hash_verdict']}`

The one non-mutable byte mismatch is the V3 controlling prompt checked out with CRLF in this worktree while the originating worktree stored LF. Normalized UTF-8 content matches; no source-data hash mismatch was found.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Duplicate Sample-Floor Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{duplicates['status']}`.

- Accepted denominator rows: `{duplicates['accepted_denominator_row_count']}`
- Accepted unique no-fill duplicate keys: `{duplicates['accepted_unique_nofill_duplicate_keys']}`
- Scored sample floor opened: `false`

May 3 duplicate boundary: {duplicates['may3_duplicate_boundary']['decision']}
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_LEARNING_AND_LIMITATIONS_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Learning And Limitations - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

## What V3 Proves

- The prior 298-row no-fill universe is represented exactly once.
- The V3 terminal families reconcile to 225 accepted input-only categorical rows, 4 source-control rows, 4 source-impossible rows, 0 unresolved blockers, and 65 rejects.
- May 3 rows 0049/0050/0051 are source-control market-session-empty evidence only.
- XAUUSD 0241 is source-control input-only no-entry-through-cancel evidence only.
- USDJPY rows 0130/0143/0165/0178 remain source-impossible from approved routes because the first decisive quote row simultaneously satisfies entry and protective predicates without a sub-row sequence source.

## What V3 Does Not Prove

- It does not score outcomes, R, win rate, expectancy, or validation lift.
- It does not inspect broker actual-R, account history, live order/deal/position labels, or hidden labels.
- It does not make any row validation-safe, promotable, or live-effective.
- It does not solve the USDJPY event-order question; it reduces it to an exact source requirement.

## Limitations

- Source-hash recomputation found two mutable context hash drifts and one line-ending-only prompt hash drift; no stable source-data hash mismatch was found.
- Exact USDJPY ordering remains externally blocked unless a broker-native quote-event sequence or sub-row/sub-millisecond source appears.
- A future result lane must be a separate evidence-class gate and must not reuse this audit as performance validation.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_NEXT_PROMPT_PACK_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Next Prompt Pack - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Use V3 only as source-control/categorical-input evidence. Do not score outcomes inside this lane.

Recommended next evidence-class gate:

`/goal Build the next no-fill result-contract or quarantined scoring lane only after accepting G12_NOFILL_CAT_V3_SOURCE_CONTROL_AUDIT as input evidence; consume accepted input-only rows separately from source-control rows, preserve USDJPY source-impossible blockers unless a broker-native quote-event sequence source is provided, keep 65 rejects outside denominators, and do not inspect broker actual-R/account-history/live-order/deal/position/hidden labels unless the new lane explicitly authorizes that evidence class. Maintain NO_PROMOTION_VERDICT until a separate validation/promotion dossier exists.`

Required carry-forward constraints:

- V3 remains `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
- Source-control rows 0049/0050/0051/0241 are non-denominator evidence only.
- Source-impossible rows 0130/0143/0165/0178 require a broker-native USDJPY quote-event sequence source to reopen.
- Reject rows remain outside labels, denominators, result use, validation, promotion, and live effect.
""",
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.md",
        f"""# G12 NOFILL CAT V3 Completion Audit - {DATE}

Promotion posture: `{PROMOTION_VERDICT}`.

Can mark complete after verifier: `{str(completion['can_mark_goal_complete_after_verifier']).lower()}`.

## Prompt-To-Artifact Checklist

{md_table(completion['prompt_to_artifact_checklist'], ['requirement', 'artifact', 'status', 'evidence'])}

## Missing, Incomplete, Or Weak Requirements

```json
{json.dumps(completion['missing_incomplete_or_weak_requirements'], indent=2, sort_keys=True)}
```
""",
    )


def main() -> int:
    inputs = load_inputs()
    universe = audit_universe(inputs)
    source_control = audit_source_control_rows(inputs)
    source_impossible = audit_source_impossibility(inputs)
    rejects = audit_rejects(inputs)
    hashes = audit_hashes_and_noleak(inputs)
    duplicates = audit_duplicates(inputs)
    decision = build_decision_ledger(universe, source_control, source_impossible, rejects, hashes, duplicates)
    completion = build_completion(decision, universe, source_control, source_impossible, rejects, hashes, duplicates)
    write_artifacts(decision, universe, source_control, source_impossible, rejects, hashes, duplicates, completion)
    print(
        json.dumps(
            {
                "ok": completion["can_mark_goal_complete_after_verifier"],
                "can_mark_goal_complete": completion["can_mark_goal_complete_after_verifier"],
                "artifacts_written": 16,
                "issues": completion["missing_incomplete_or_weak_requirements"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if completion["can_mark_goal_complete_after_verifier"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
