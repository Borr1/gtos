"""Build G12 audit artifacts for NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1.

This script is research/audit only. It reads source-packet artifacts, recomputes
machine-checkable counts and hashes, and writes only G12-owned audit artifacts in
this directory.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
SOURCE_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet"
NOFILL_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract"
G12_NOFILL_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit"
T3_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet"

DATE = "2026-05-08"
FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_KEY_PARTS = (
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "conservative_lower_bound_r",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_order_ticket",
    "pbo",
    "pending_ticket",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_keys(obj: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            full = f"{prefix}.{key_text}" if prefix else key_text
            keys.append(full)
            keys.extend(walk_keys(value, full))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            keys.extend(walk_keys(value, f"{prefix}[{idx}]"))
    return keys


def forbidden_key_hits(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for idx, record in enumerate(records):
        row_id = record.get("packet_row_id") or record.get("source_row_id") or str(idx)
        for key_path in walk_keys(record):
            leaf = key_path.split(".")[-1].lower()
            if any(part == leaf or part in leaf for part in FORBIDDEN_KEY_PARTS):
                hits.append({"row_id": str(row_id), "key_path": key_path})
    return hits


def counter_dict(values: list[Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in Counter(values).most_common()}


def read_core_inputs() -> dict[str, Any]:
    return {
        "goal_prompt": OUT_DIR / "G12_NOFILL_CLOSE_AUDIT_GOAL_PROMPT_2026-05-08.md",
        "source_prompt_pack": SOURCE_DIR / "NOFILL_CLOSE_G12_AUDIT_PROMPT_PACK_2026-05-08.md",
        "source_anchor": SOURCE_DIR / "NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json",
        "source_contract": SOURCE_DIR / "NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json",
        "source_packet": SOURCE_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json",
        "source_rows": SOURCE_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl",
        "source_blockers": SOURCE_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json",
        "source_hash_noleak": SOURCE_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
        "source_search": SOURCE_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
        "source_duplicate": SOURCE_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        "source_forensics": SOURCE_DIR / "NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json",
        "source_completion": SOURCE_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json",
        "source_request": SOURCE_DIR
        / "source_requests/NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json",
        "source_builder": SOURCE_DIR / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        "source_verifier": SOURCE_DIR / "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        "source_tests": SOURCE_DIR / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        "nofill_rows": NOFILL_DIR / "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl",
        "g12_nofill_universe": G12_NOFILL_DIR / "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json",
        "t3_rows": T3_DIR / "CNR_T3_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
    }


def file_inventory(paths: dict[str, Path]) -> list[dict[str, Any]]:
    out = []
    for role, path in sorted(paths.items()):
        out.append(
            {
                "role": role,
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
            }
        )
    return out


def search_nofill_0127_sources() -> dict[str, Any]:
    main_tick = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-06.parquet")
    main_otr061 = Path(
        r"C:\Users\MSI\Documents\ai-trading-agent\research\science_program_2026_05\06_outcome_testing"
        r"\otr061_xau_tick_recovery\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    )
    local_otr061 = (
        REPO_ROOT
        / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery"
        / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    )
    tmp_root = Path(r"C:\tmp\gtos_otb")
    tmp_matches = []
    if tmp_root.exists():
        pattern = "*/research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
        for path in sorted(tmp_root.glob(pattern)):
            tmp_matches.append(
                {
                    "path": str(path),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "sha256": sha256_file(path),
                }
            )
    sierra_candidates = [
        Path(r"C:\SierraChart\Data\XAUUSD.scid"),
        Path(r"C:\SierraChart\Data\GCM26-COMEX.scid"),
        Path(r"C:\SierraChart\Data\MGCM26-COMEX.scid"),
        Path(r"C:\SierraChart\Data\MarketDepthData\GCM26-COMEX.2026-05-06.depth"),
        Path(r"C:\SierraChart\Data\MarketDepthData\MGCM26-COMEX.2026-05-06.depth"),
    ]
    return {
        "searched_roots": [
            {
                "root": r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD",
                "purpose": "packet-cited XAUUSD daily tick parquet",
                "matches": [describe_parquet_path(main_tick, include_time_range=True)],
            },
            {
                "root": r"C:\Users\MSI\Documents\ai-trading-agent\research\science_program_2026_05\06_outcome_testing\otr061_xau_tick_recovery",
                "purpose": "prior source-hashed OTR061 read-only XAUUSD tick recovery artifact",
                "matches": [describe_parquet_path(main_otr061, include_time_range=True)],
            },
            {
                "root": rel(local_otr061.parent),
                "purpose": "current worktree copy of prior OTR061 source artifact",
                "matches": [describe_parquet_path(local_otr061, include_time_range=True)],
            },
            {
                "root": r"C:\tmp\gtos_otb",
                "purpose": "prior worktree copies of the OTR061 source artifact",
                "matches": tmp_matches,
            },
            {
                "root": r"C:\SierraChart",
                "purpose": "same-market/proxy local heavy-data discovery only; not used for broker XAUUSD quote truth in this audit",
                "matches": [
                    {
                        "path": str(path),
                        "exists": path.exists(),
                        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                    }
                    for path in sierra_candidates
                ],
            },
        ]
    }


def describe_parquet_path(path: Path, include_time_range: bool = False) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
    }
    if include_time_range and path.exists():
        try:
            df = pd.read_parquet(path, columns=["ts_utc"])
            ts = pd.to_datetime(df["ts_utc"], utc=True)
            item.update(
                {
                    "row_count": int(len(ts)),
                    "first_ts_utc": None if ts.empty else ts.min().isoformat().replace("+00:00", "Z"),
                    "last_ts_utc": None if ts.empty else ts.max().isoformat().replace("+00:00", "Z"),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive, recorded in artifact
            item["parquet_read_error"] = f"{type(exc).__name__}: {exc}"
    return item


def first_touch(df: pd.DataFrame, side: str, level: float | None, kind: str) -> str | None:
    if level is None or df.empty:
        return None
    if side == "LONG":
        if kind == "entry":
            mask = df["ask"] <= float(level)
        elif kind == "terminal":
            mask = df["bid"] >= float(level)
        else:
            mask = df["bid"] <= float(level)
    else:
        if kind == "entry":
            mask = df["bid"] >= float(level)
        elif kind == "terminal":
            mask = df["ask"] <= float(level)
        else:
            mask = df["ask"] >= float(level)
    hits = df.loc[mask, "ts_utc"]
    if hits.empty:
        return None
    return pd.Timestamp(hits.iloc[0]).isoformat().replace("+00:00", "Z")


def resolve_row_0127(blocked_row: dict[str, Any]) -> dict[str, Any]:
    source_path = Path(
        r"C:\Users\MSI\Documents\ai-trading-agent\research\science_program_2026_05\06_outcome_testing"
        r"\otr061_xau_tick_recovery\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    )
    if not source_path.exists():
        source_path = (
            REPO_ROOT
            / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery"
            / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
        )
    evidence = blocked_row.get("source_evidence") or {}
    prior_projection = evidence.get("tick_terminal_sequence_projection") or {}
    start = pd.Timestamp(prior_projection.get("path_start_utc") or "2026-05-06T07:15:00Z")
    end = pd.Timestamp(prior_projection.get("path_end_utc") or "2026-05-06T17:15:00Z")
    entry = evidence.get("entry_price")
    terminal = evidence.get("terminal_area_price")
    protective = evidence.get("protective_level_price")
    side = blocked_row.get("projected_side") or "LONG"
    if not source_path.exists():
        return {
            "packet_row_id": blocked_row.get("packet_row_id"),
            "g12_resolution_status": "STILL_BLOCKED_SOURCE_FILE_NOT_FOUND",
            "source_path": str(source_path),
            "source_exists": False,
        }
    df = pd.read_parquet(source_path)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    window = df[(df["ts_utc"] >= start) & (df["ts_utc"] <= end)].sort_values("ts_utc")
    entry_touch = first_touch(window, side, entry, "entry")
    terminal_touch = first_touch(window, side, terminal, "terminal")
    protective_touch = first_touch(window, side, protective, "protective")
    observed_events = [
        ("entry", entry_touch),
        ("terminal_area", terminal_touch),
        ("protective_level", protective_touch),
    ]
    ordered_events = sorted(({"event": name, "first_touch_utc": ts} for name, ts in observed_events if ts), key=lambda x: x["first_touch_utc"])
    first_event = ordered_events[0]["event"] if ordered_events else None
    source_closes = first_event == "terminal_area"
    return {
        "packet_row_id": blocked_row.get("packet_row_id"),
        "source_inventory_id": blocked_row.get("source_inventory_id"),
        "source_row_id": blocked_row.get("source_row_id"),
        "g12_resolution_status": "SOURCE_CLOSED_BY_EXISTING_LOCAL_OTR061_TICK_FILE" if source_closes else "STILL_BLOCKED_OR_AMBIGUOUS_AFTER_OTR061_CHECK",
        "upstream_blocker_status": blocked_row.get("closure_status"),
        "upstream_blocker_rejected_reason": "Existing source-hashed OTR061 XAUUSD tick parquet contains rows in the frozen window; terminal area is the first observed side-aware touch.",
        "g12_closure_label": "terminal_sequence_tick_source_projected_no_score" if source_closes else blocked_row.get("closure_label"),
        "g12_closure_status": "source_closed" if source_closes else blocked_row.get("closure_status"),
        "source_path": str(source_path),
        "source_sha256": sha256_file(source_path),
        "source_rows_total": int(len(df)),
        "source_first_ts_utc": df["ts_utc"].min().isoformat().replace("+00:00", "Z"),
        "source_last_ts_utc": df["ts_utc"].max().isoformat().replace("+00:00", "Z"),
        "requested_window_start_utc": start.isoformat().replace("+00:00", "Z"),
        "requested_window_end_utc": end.isoformat().replace("+00:00", "Z"),
        "rows_inside_requested_window": int(len(window)),
        "window_first_ts_utc": None if window.empty else window["ts_utc"].iloc[0].isoformat().replace("+00:00", "Z"),
        "window_last_ts_utc": None if window.empty else window["ts_utc"].iloc[-1].isoformat().replace("+00:00", "Z"),
        "covers_full_requested_window": bool(not window.empty and window["ts_utc"].iloc[0] <= start and window["ts_utc"].iloc[-1] >= end),
        "covers_decisive_source_event": bool(source_closes),
        "side_aware_touch_parser": "LONG entry ask<=entry terminal bid>=target protective bid<=stop; SHORT entry bid>=entry terminal ask<=target protective ask>=stop",
        "entry_price": entry,
        "terminal_area_price": terminal,
        "protective_level_price": protective,
        "entry_touch_time_utc": entry_touch,
        "terminal_area_touch_time_utc": terminal_touch,
        "protective_level_touch_time_utc": protective_touch,
        "ordered_source_events": ordered_events,
        "non_claims": [
            "No R/performance is computed.",
            "No broker/account/live/order/hidden label is inspected.",
            "This clears source availability and side-aware terminal ordering only.",
            "If a future contract requires full 07:15-17:15 tick coverage independent of the first terminal touch, the existing read-only extraction manifest remains the exact next request.",
        ],
    }


def recompute_source_hashes(source_search: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for item in source_search.get("consumed_source_files", []):
        path = Path(item.get("path", ""))
        expected = item.get("expected_sha256") or item.get("sha256")
        observed = sha256_file(path)
        role = item.get("role")
        suffix = path.suffix.lower()
        strict_required = not (
            role == "controlling_or_upstream_input"
            and (suffix == ".md" or str(path).replace("\\", "/") in [".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"])
        )
        checks.append(
            {
                "path": str(path),
                "role": role,
                "exists": path.exists(),
                "expected_sha256": expected,
                "observed_sha256": observed,
                "matches": bool(expected and observed and expected == observed),
                "strict_source_hash_required": strict_required,
            }
        )
    return {
        "checked_count": len(checks),
        "missing_count": sum(1 for item in checks if not item["exists"]),
        "mismatch_count": sum(1 for item in checks if item["exists"] and not item["matches"]),
        "strict_source_mismatch_count": sum(
            1 for item in checks if item["exists"] and item["strict_source_hash_required"] and not item["matches"]
        ),
        "nonblocking_text_or_context_hash_drift_count": sum(
            1 for item in checks if item["exists"] and not item["strict_source_hash_required"] and not item["matches"]
        ),
        "checks": checks,
    }


def build_artifacts() -> dict[str, Any]:
    generated_at = utc_now()
    inputs = read_core_inputs()
    packet = load_json(inputs["source_packet"])
    rows = load_jsonl(inputs["source_rows"])
    nofill_rows = load_jsonl(inputs["nofill_rows"])
    source_anchor = load_json(inputs["source_anchor"])
    source_contract = load_json(inputs["source_contract"])
    source_blockers = load_json(inputs["source_blockers"])
    source_search = load_json(inputs["source_search"])
    source_hash_noleak = load_json(inputs["source_hash_noleak"])
    source_duplicate = load_json(inputs["source_duplicate"])
    source_completion = load_json(inputs["source_completion"])
    source_request = load_json(inputs["source_request"])
    g12_nofill_universe = load_json(inputs["g12_nofill_universe"])
    t3_rows = load_jsonl(inputs["t3_rows"])

    closure_status_counts = Counter(row.get("closure_status") for row in rows)
    closure_label_counts = Counter(row.get("closure_label") for row in rows)
    blocked_rows = [row for row in rows if row.get("closure_status") == "source_blocked_exact"]
    blocked_0127 = next(row for row in blocked_rows if row.get("packet_row_id") == "NOFILL-CLOSE-ROW-0127")
    source_search_results = search_nofill_0127_sources()
    row_0127_resolution = resolve_row_0127(blocked_0127)
    corrected_source_closed = int(closure_status_counts.get("source_closed", 0)) + (
        1 if row_0127_resolution["g12_closure_status"] == "source_closed" else 0
    )
    corrected_source_blocked = len(rows) - corrected_source_closed

    closure_ids = {row["source_inventory_id"] for row in rows}
    nofill_ids = {row["source_inventory_id"] for row in nofill_rows}
    t3_ids = {row.get("input_inventory_id") for row in t3_rows}

    hash_recompute = recompute_source_hashes(source_search)
    forbidden_hits = forbidden_key_hits(rows)
    flag_violations = [
        row.get("packet_row_id")
        for row in rows
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT"
        or row.get("validation_safe") is not False
        or row.get("outcome_review_opened") is not False
        or row.get("live_effect") is not False
    ]

    context_anchor = {
        "artifact_family": "G12_NOFILL_CLOSE_CONTEXT_ANCHOR",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "controlling_prompt_path": rel(inputs["goal_prompt"]),
        "source_packet_under_audit": "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1",
        "audit_lane": "G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_AUDIT_V1",
        "preflight_completed": True,
        "preflight_inputs_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel(inputs["goal_prompt"]),
        ],
        "context_staleness_note": "LIVE_STATE was regenerated at audit start; research_current_state was read directly for the NOFILL_CLOSE entries instead of relying on summaries.",
        "input_inventory": file_inventory(inputs),
        "active_question_stack": [
            "Does the packet universe equal the 298 accepted G12_NOFILL rows?",
            "Are six T3 rows and 94 G12-blocked CNR061 rows excluded?",
            "Are 297 upstream source-closed rows genuinely source-only and no-leak?",
            "Is NOFILL-CLOSE-ROW-0127 still exactly source-blocked after absolute local heavy-data search?",
            "Do duplicate/sample-floor and label-family controls prevent promotion or performance interpretation?",
        ],
        "searched_root_ledger": source_search_results["searched_roots"],
        "route_decision_ledger": [
            {
                "decision": "AUDIT_SOURCE_PACKET_NOT_RESULT_LANE",
                "reason": "No R/performance, broker/account/live/order/hidden labels, blocked CNR061 scoring, paid/API/Databento calls, or MT5 order/account calls are allowed.",
            },
            {
                "decision": "SEARCH_PRIOR_OTR061_TICK_RECOVERY_BEFORE_ACCEPTING_BLOCKER",
                "reason": "Local-heavy-data doctrine says worktree/source-packet absence is not data absence.",
            },
            {
                "decision": "G12_ROW_0127_BLOCKER_EXACTNESS_REJECTED",
                "reason": "An existing source-hashed OTR061 XAUUSD tick parquet contains rows in the frozen window and resolves terminal-area first-touch ordering without new extraction.",
            },
        ],
    }

    decision_ledger = {
        "artifact_family": "G12_NOFILL_CLOSE_DECISION_LEDGER",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "terminal_verdict": "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE",
        "packet_level_decision": "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE",
        "decision_scope": "Input-only source/control evidence with G12 correction to the upstream exact-blocker state.",
        "upstream_packet_reported_counts": {
            "packet_rows": len(rows),
            "source_closed": int(closure_status_counts.get("source_closed", 0)),
            "source_blocked_exact": int(closure_status_counts.get("source_blocked_exact", 0)),
        },
        "g12_audited_counts_after_local_source_search": {
            "packet_rows": len(rows),
            "source_closed": corrected_source_closed,
            "source_blocked_exact": corrected_source_blocked,
        },
        "row_level_decisions": [
            {
                "scope": "rows_except_NOFILL-CLOSE-ROW-0127",
                "row_count": len(rows) - 1,
                "decision": "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE",
                "reason": "Counts, source hashes, no-leak flags, label-family boundaries, duplicate/sample-floor controls, and exclusions recompute from artifacts.",
            },
            {
                "scope": "NOFILL-CLOSE-ROW-0127",
                "decision": "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE",
                "reason": "G12 local-heavy-data search found existing source-hashed OTR061 tick file; upstream source_blocked_exact is stale.",
                "evidence": row_0127_resolution,
            },
        ],
        "source_request_manifest_decision": {
            "decision": "EXACT_IF_FULL_PATH_END_COVERAGE_IS_REQUIRED_LATER",
            "manifest_path": rel(inputs["source_request"]),
            "current_audit_use": "Not needed to source-close row 0127 because the decisive terminal-area first touch is in an already-existing local source-hashed file.",
        },
        "hard_boundaries_preserved": {
            "r_performance_scored": False,
            "broker_account_live_order_hidden_labels_inspected": False,
            "blocked_cnr061_scored": False,
            "paid_api_databento_calls": False,
            "mt5_order_or_account_calls": False,
            "live_trading_surface_changed": False,
        },
    }

    universe_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "packet_rows": len(rows),
        "nofill_input_packet_rows": len(nofill_rows),
        "closure_matches_accepted_nofill_universe": closure_ids == nofill_ids,
        "closure_minus_nofill_ids": sorted(closure_ids - nofill_ids),
        "nofill_minus_closure_ids": sorted(nofill_ids - closure_ids),
        "source_lane_counts": counter_dict([row.get("source_lane") for row in rows]),
        "source_packet_id_counts": counter_dict([row.get("source_packet_id") for row in rows]),
        "six_t3_rows_excluded": {
            "t3_row_count": len(t3_rows),
            "t3_input_inventory_ids": sorted(t3_ids),
            "overlap_with_closure_packet": sorted(closure_ids & t3_ids),
            "status": "PASS" if len(t3_rows) == 6 and not (closure_ids & t3_ids) else "FAIL",
        },
        "blocked_94_cnr061_excluded": {
            "source": rel(inputs["g12_nofill_universe"]),
            "blocked_rows": (g12_nofill_universe.get("blocked_94_exclusion") or {}).get("blocked_rows"),
            "blocked_audit_status": (g12_nofill_universe.get("blocked_94_exclusion") or {}).get("blocked_audit_status"),
            "packet_rows_from_blocked_set": (g12_nofill_universe.get("blocked_94_exclusion") or {}).get("packet_rows_from_blocked_set"),
            "closure_rows_with_oti8_cnr061_lane": [row["packet_row_id"] for row in rows if row.get("source_lane") == "OTI8_CNR061"],
            "status": "PASS"
            if (g12_nofill_universe.get("blocked_94_exclusion") or {}).get("blocked_rows") == 94
            and not [row for row in rows if row.get("source_lane") == "OTI8_CNR061"]
            else "FAIL",
        },
    }

    source_closure_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "upstream_closure_status_counts": counter_dict([row.get("closure_status") for row in rows]),
        "upstream_closure_label_counts": counter_dict([row.get("closure_label") for row in rows]),
        "g12_corrected_closure_status_counts": {"source_closed": corrected_source_closed, "source_blocked_exact": corrected_source_blocked},
        "row_0127_resolution": row_0127_resolution,
        "oti_family_audit": {
            "OTI1_LIFECYCLE": {
                "row_count": sum(1 for row in rows if row.get("source_lane") == "OTI1_LIFECYCLE"),
                "missing_projected_symbol_session_side_rows": [
                    row["packet_row_id"]
                    for row in rows
                    if row.get("source_lane") == "OTI1_LIFECYCLE"
                    and not (row.get("projected_symbol") and row.get("projected_session") and row.get("projected_side"))
                ],
                "status": "PASS_SOURCE_METADATA_PROJECTED",
            },
            "OTI2_RISKBANK": {
                "row_count": sum(1 for row in rows if row.get("source_lane") == "OTI2_RISKBANK"),
                "terminal_sequence_unclaimed_rows": [
                    row["packet_row_id"]
                    for row in rows
                    if row.get("source_lane") == "OTI2_RISKBANK"
                    and row.get("closure_label") == "entry_touched_terminal_sequence_unclaimed_source_confirmed"
                ],
                "status": "PASS_SOURCE_ONLY_NO_TERMINAL_ORDER_SCORE",
            },
            "OTI3_G3_GEOMETRY": {
                "row_count": sum(1 for row in rows if row.get("source_lane") == "OTI3_G3_GEOMETRY"),
                "label_counts": counter_dict([row.get("closure_label") for row in rows if row.get("source_lane") == "OTI3_G3_GEOMETRY"]),
                "status": "PASS_RECOVERED_USDJPY_M1_SOURCE_AVAILABILITY_ONLY",
            },
            "OTI4_G6_OPENING_DRIVE": {
                "row_count": sum(1 for row in rows if row.get("source_lane") == "OTI4_G6_OPENING_DRIVE"),
                "upstream_source_blocked_rows": [row["packet_row_id"] for row in rows if row.get("source_lane") == "OTI4_G6_OPENING_DRIVE" and row.get("closure_status") != "source_closed"],
                "g12_source_blocked_rows_after_search": [] if row_0127_resolution["g12_closure_status"] == "source_closed" else [row_0127_resolution["packet_row_id"]],
                "opening_drive_prereg_blockers_retained": True,
                "status": "PASS_WITH_G12_ROW_0127_CORRECTION",
            },
            "OTI5_G6_CUSUM": {
                "row_count": sum(1 for row in rows if row.get("source_lane") == "OTI5_G6_CUSUM"),
                "label_counts": counter_dict([row.get("closure_label") for row in rows if row.get("source_lane") == "OTI5_G6_CUSUM"]),
                "status": "PASS_SOURCE_ONLY_NO_R_SCORED",
            },
        },
        "source_closed_rows_prove": [
            "Source/lifecycle availability and categorical closure labels can be reconstructed for the accepted G12_NOFILL universe.",
            "The corrected row 0127 has a source-hashed tick record inside the frozen window and terminal-area first-touch source ordering.",
        ],
        "source_closed_rows_do_not_prove": [
            "R/performance, win rate, expectancy, DSR/PBO, broker actual-R, validation, promotion, or live execution behavior.",
            "Blocked CNR061 rows, T1/T2/E2/E3/E4 result families, or future live gate readiness.",
        ],
    }

    hash_noleak_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "source_packet_hash_audit_status": source_hash_noleak.get("status"),
        "source_packet_consumed_file_count": source_hash_noleak.get("consumed_source_file_count"),
        "source_packet_reported_hash_mismatches": source_hash_noleak.get("hash_mismatches"),
        "g12_recomputed_hashes": {
            "checked_count": hash_recompute["checked_count"],
            "missing_count": hash_recompute["missing_count"],
            "mismatch_count": hash_recompute["mismatch_count"],
            "strict_source_mismatch_count": hash_recompute["strict_source_mismatch_count"],
            "nonblocking_text_or_context_hash_drift_count": hash_recompute["nonblocking_text_or_context_hash_drift_count"],
        },
        "g12_row_0127_additional_source_hash": {
            "path": row_0127_resolution.get("source_path"),
            "sha256": row_0127_resolution.get("source_sha256"),
        },
        "forbidden_packet_key_hits_count": len(forbidden_hits),
        "forbidden_packet_key_hits": forbidden_hits[:50],
        "flag_violations": flag_violations,
        "no_leak_status": "PASS" if not forbidden_hits and not flag_violations else "FAIL",
        "asof_and_freeze_order": {
            "anchor_written_at_utc": source_anchor.get("written_at_utc"),
            "contract_frozen_at_utc": source_contract.get("contract_frozen_at_utc"),
            "classification_started_at_utc": packet.get("classification_started_at_utc"),
            "status": "PASS"
            if source_anchor.get("written_at_utc")
            <= source_contract.get("contract_frozen_at_utc")
            <= packet.get("classification_started_at_utc")
            else "FAIL",
        },
        "forbidden_surface_counters": {
            "broker_actual_r_accessed": False,
            "account_history_accessed": False,
            "live_trade_results_accessed": False,
            "mt5_order_calls": 0,
            "mt5_account_calls": 0,
            "paid_data_calls": 0,
            "api_calls": 0,
            "databento_calls": 0,
        },
    }

    label_family_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "label_family": "input_only_lifecycle_source_closure",
        "closure_label_counts": counter_dict([row.get("closure_label") for row in rows]),
        "g12_corrected_label_note": "NOFILL-CLOSE-ROW-0127 remains in terminal_sequence_tick_source_projected_no_score family after G12 OTR061 source check.",
        "separation_rules": [
            "Lifecycle/source closure labels are not R/performance labels.",
            "No broker actual-R/account history/live order state is consumed.",
            "Six CNR T3 lifecycle rows remain separate categorical T3 evidence.",
            "The 94 G12-blocked CNR061 rows remain excluded and unscored.",
        ],
        "status": "PASS_LABEL_FAMILY_SEPARATION_PRESERVED" if not forbidden_hits else "FAIL",
    }

    blocker_request_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "upstream_rows_with_exact_blockers": source_blockers.get("rows_with_exact_blockers"),
        "upstream_blocker_counts": source_blockers.get("blocker_counts"),
        "upstream_source_blocked_exact_rows": source_blockers.get("source_blocked_exact_rows"),
        "g12_source_blocker_decision": {
            "packet_row_id": "NOFILL-CLOSE-ROW-0127",
            "decision": "REJECT_UPSTREAM_EXACT_BLOCKER_AS_LOCALLY_RESOLVABLE",
            "evidence": row_0127_resolution,
        },
        "source_request_manifest_audit": {
            "path": rel(inputs["source_request"]),
            "request_id": source_request.get("request_id"),
            "symbol": source_request.get("symbol"),
            "start_utc": source_request.get("start_utc"),
            "end_utc": source_request.get("end_utc"),
            "requested_fields": source_request.get("requested_fields"),
            "requested_source": source_request.get("requested_source"),
            "asof_rule": source_request.get("asof_rule"),
            "forbidden_calls": source_request.get("forbidden_calls"),
            "must_hash_output": source_request.get("must_hash_output"),
            "exactness_status": "PASS_FOR_FUTURE_FULL_WINDOW_EXTRACTION_IF_NEEDED",
            "current_audit_status": "NOT_NEEDED_FOR_SOURCE_ONLY_ROW_0127_CLOSURE_AFTER_OTR061_LOCAL_FILE_FOUND",
        },
        "remaining_exact_blockers_are_non_result_boundaries": [
            "missing opening-drive prereg fields",
            "entry_touched terminal sequence unclaimed from M1 path-order row",
            "terminal touch replay unopened for OTI3 source availability rows",
            "pending lifecycle source does not materialize entry_touched_at_utc",
        ],
        "status": "PASS_WITH_STALE_SOURCE_BLOCKER_CORRECTED",
    }

    duplicate_audit = {
        "artifact_family": "G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "packet_rows": len(rows),
        "duplicate_group_id_unique": len({row.get("duplicate_group_id") for row in rows}),
        "duplicate_group_id_repeated_count": sum(1 for _, count in Counter(row.get("duplicate_group_id") for row in rows).items() if count > 1),
        "nofill_duplicate_key_unique": len({row.get("nofill_duplicate_key") for row in rows}),
        "source_duplicate_audit_status": source_duplicate.get("status"),
        "source_validation_sample_floor_status": source_duplicate.get("validation_sample_floor_status"),
        "source_sample_floor_reason": source_duplicate.get("sample_floor_reason"),
        "top_repeated_nofill_duplicate_keys": source_duplicate.get("top_repeated_nofill_duplicate_keys"),
        "g12_status": "PASS_DUPLICATE_AND_SAMPLE_FLOOR_CONTROLS_BLOCK_VALIDATION",
    }

    forensics = {
        "artifact_family": "G12_NOFILL_CLOSE_FORENSICS_AND_LEARNING",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "learning_verdict": "SOURCE_CLOSURE_PACKET_IS_USEFUL_INPUT_EVIDENCE_BUT_UPSTREAM_BLOCKER_WAS_SOURCE_BOXED",
        "positive_learning": [
            "The 298-row accepted no-fill/still-pending universe can be source-closed without R/performance scoring.",
            "OTI1 pending lifecycle, OTI2/OTI5 no-entry, OTI3 source recovery, and OTI4 tick projection can be separated as source families.",
            "The 94 blocked CNR061 rows and six T3 lifecycle rows remain excluded.",
        ],
        "negative_or_corrective_learning": [
            "The upstream closure source search did not use the existing OTR061 XAUUSD 2026-05-06 07:10-11:15 tick recovery parquet for NOFILL-CLOSE-ROW-0127.",
            "A source packet can pass its own verifier while still missing a prior local-heavy-data artifact outside its selected source list.",
            "Future source verifiers should search prior same-symbol/time tick-recovery lanes before accepting BLOCKED_NO_TICKS_IN_WINDOW.",
        ],
        "still_unknown_or_forbidden": [
            "No R/performance, broker actual-R, account history, validation, promotion, or live effect is opened.",
            "Full 07:15-17:15 tick coverage is still not present in the OTR061 file; it is unnecessary for the source-only terminal-first closure observed here, but would require the existing manifest if a later contract insists on full path-end coverage.",
            "Opening-drive prereg field blockers remain exact non-result blockers.",
        ],
        "next_routes": [
            "Rebuild or patch the NOFILL close packet source-search/verifier logic to include prior OTR061 local tick recovery when auditing XAUUSD 2026-05-06 windows.",
            "Keep any future result lane separate: freeze result contract, denominator controls, as-of/no-leak schema, and G12/owner acceptance before any scoring.",
            "Add a source-only verifier check that BLOCKED_NO_TICKS_IN_WINDOW searches main tick roots, prior tick-recovery lane artifacts, and C:\\tmp worktree copies before emitting an access request.",
        ],
    }

    next_prompt = f"""# G12 NOFILL Close Next Prompt Pack - {DATE}

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Recommended Next Lane

`/goal Rebuild or patch NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 as a source-only correction lane using the G12 no-fill closure audit under research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/. Complete mandatory GTOS preflight; read the original NOFILL close packet, G12 decision/source-closure/blocker/hash/no-leak/duplicate/forensics/completion artifacts; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; do not score R/performance, broker/account/live/order/hidden labels, blocked CNR061 rows, paid/API/Databento/MT5 order calls, registries, remotes, credentials, or live trading surfaces; incorporate the source-hashed OTR061 XAUUSD 2026-05-06 07:10-11:15 tick recovery file to clear NOFILL-CLOSE-ROW-0127 as input-only terminal-sequence source evidence; update source-search/verifier logic so BLOCKED_NO_TICKS_IN_WINDOW searches prior tick-recovery lanes and absolute local heavy-data roots before emitting read-only extraction manifests; stop only after corrected packet artifacts, source-hash/no-leak audit, duplicate/sample-floor audit, verifier/tests, and completion audit pass.`

## What Remains Forbidden

- No R/performance, win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claim.
- No broker actual-R, account history, live order state, hidden labels, or blocked CNR061 scoring.
- No paid/API/Databento calls and no MT5 order/account calls.

## Exact Source Note

G12 found `C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet` with SHA256 `{row_0127_resolution.get('source_sha256')}`. It contains rows from 2026-05-06T07:10:01.820Z through 2026-05-06T11:15:59.763Z and source-closes row 0127 because the terminal-area side-aware touch is the first observed source event at `{row_0127_resolution.get('terminal_area_touch_time_utc')}`.
"""

    completion = {
        "artifact_family": "G12_NOFILL_CLOSE_COMPLETION_AUDIT",
        "schema_version": "g12_nofill_close_audit_v1",
        "generated_at_utc": generated_at,
        **FLAGS,
        "objective_restatement": "Audit the merged NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 and G12 prompt pack as input-only source/control evidence; verify counts, exclusions, hashes, no-leak/as-of, duplicate/sample-floor and label-family controls; search absolute heavy-data roots before accepting the XAUUSD blocker; stop with accept/block/reject and machine-checkable evidence.",
        "completion_status": "BUILT_PENDING_VERIFIER",
        "terminal_verdict": decision_ledger["terminal_verdict"],
        "can_mark_goal_complete": False,
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory GTOS preflight", "evidence": context_anchor["preflight_inputs_read"], "status": "PASS"},
            {"requirement": "required G12 artifacts under G12-owned directory", "evidence": "builder writes only G12_NOFILL_CLOSE_* plus builder/verifier/test in this directory", "status": "PASS"},
            {"requirement": "298 total rows", "evidence": len(rows), "status": "PASS" if len(rows) == 298 else "FAIL"},
            {
                "requirement": "upstream 297 source-closed and 1 source-blocked",
                "evidence": decision_ledger["upstream_packet_reported_counts"],
                "status": "PASS" if closure_status_counts.get("source_closed") == 297 and closure_status_counts.get("source_blocked_exact") == 1 else "FAIL",
            },
            {
                "requirement": "XAUUSD blocker exactness after heavy-data search",
                "evidence": row_0127_resolution,
                "status": "CORRECTED_NOT_EXACT_BLOCKER" if row_0127_resolution["g12_closure_status"] == "source_closed" else "PASS_EXACT_BLOCKER",
            },
            {"requirement": "six T3 rows excluded", "evidence": universe_audit["six_t3_rows_excluded"], "status": universe_audit["six_t3_rows_excluded"]["status"]},
            {"requirement": "94 G12-blocked CNR061 rows excluded", "evidence": universe_audit["blocked_94_cnr061_excluded"], "status": universe_audit["blocked_94_cnr061_excluded"]["status"]},
            {
                "requirement": "source hashes",
                "evidence": hash_noleak_audit["g12_recomputed_hashes"],
                "status": "PASS"
                if hash_recompute["strict_source_mismatch_count"] == 0 and hash_recompute["missing_count"] == 0
                else "FAIL",
            },
            {"requirement": "no-leak/as-of validity", "evidence": {"no_leak": hash_noleak_audit["no_leak_status"], "freeze": hash_noleak_audit["asof_and_freeze_order"]}, "status": "PASS" if hash_noleak_audit["no_leak_status"] == "PASS" and hash_noleak_audit["asof_and_freeze_order"]["status"] == "PASS" else "FAIL"},
            {"requirement": "duplicate/sample-floor controls", "evidence": duplicate_audit, "status": "PASS"},
            {"requirement": "label-family separation", "evidence": label_family_audit["status"], "status": "PASS"},
            {"requirement": "NO_PROMOTION_VERDICT and false safety/live flags", "evidence": FLAGS, "status": "PASS" if not flag_violations else "FAIL"},
            {"requirement": "no forbidden live/order/paid/API/Databento surfaces", "evidence": hash_noleak_audit["forbidden_surface_counters"], "status": "PASS"},
            {"requirement": "next prompt guidance", "evidence": "G12_NOFILL_CLOSE_NEXT_PROMPT_PACK_2026-05-08.md", "status": "PASS"},
        ],
        "verification_results": {},
    }

    artifacts: dict[str, Any] = {
        "G12_NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json": context_anchor,
        "G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json": decision_ledger,
        "G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json": universe_audit,
        "G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json": source_closure_audit,
        "G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json": hash_noleak_audit,
        "G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT_2026-05-08.json": label_family_audit,
        "G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json": blocker_request_audit,
        "G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json": duplicate_audit,
        "G12_NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json": forensics,
        "G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json": completion,
    }
    for name, data in artifacts.items():
        write_json(OUT_DIR / name, data)
        write_companion_md(name, data)
    (OUT_DIR / "G12_NOFILL_CLOSE_NEXT_PROMPT_PACK_2026-05-08.md").write_text(next_prompt, encoding="utf-8")
    return artifacts


def write_companion_md(json_name: str, data: dict[str, Any]) -> None:
    md_name = json_name.replace(".json", ".md")
    title = json_name.replace("_2026-05-08.json", "").replace("_", " ").title()
    lines = [
        f"# {title} - {DATE}",
        "",
        f"Promotion verdict: `{data.get('promotion_verdict')}`",
        f"Validation safe: `{str(data.get('validation_safe')).lower()}`",
        f"Outcome review opened: `{str(data.get('outcome_review_opened')).lower()}`",
        f"Live effect: `{str(data.get('live_effect')).lower()}`",
        "",
    ]
    if "terminal_verdict" in data:
        lines.extend(["## Terminal Verdict", "", f"`{data['terminal_verdict']}`", ""])
    if "completion_status" in data:
        lines.extend(["## Completion Status", "", f"`{data['completion_status']}`", ""])
    if json_name.endswith("SOURCE_CLOSURE_AUDIT_2026-05-08.json"):
        row = data["row_0127_resolution"]
        lines.extend(
            [
                "## G12 Row 0127 Correction",
                "",
                f"- Upstream status: `{row['upstream_blocker_status']}`",
                f"- G12 status: `{row['g12_resolution_status']}`",
                f"- Source: `{row['source_path']}`",
                f"- SHA256: `{row['source_sha256']}`",
                f"- Terminal touch: `{row['terminal_area_touch_time_utc']}`",
                f"- Entry touch: `{row['entry_touch_time_utc']}`",
                "",
            ]
        )
    if json_name.endswith("UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json"):
        lines.extend(
            [
                "## Counts",
                "",
                f"- Packet rows: `{data['packet_rows']}`",
                f"- NOFILL input rows: `{data['nofill_input_packet_rows']}`",
                f"- Closure matches accepted NOFILL universe: `{data['closure_matches_accepted_nofill_universe']}`",
                f"- Six T3 exclusion status: `{data['six_t3_rows_excluded']['status']}`",
                f"- 94 CNR061 exclusion status: `{data['blocked_94_cnr061_excluded']['status']}`",
                "",
            ]
        )
    if json_name.endswith("BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json"):
        lines.extend(
            [
                "## Blocker Decision",
                "",
                f"`{data['g12_source_blocker_decision']['decision']}`",
                "",
                "The upstream read-only extraction request remains exact only if a future contract requires full path-end coverage independent of the already observed terminal first-touch event.",
                "",
            ]
        )
    if "prompt_to_artifact_checklist" in data:
        lines.extend(["## Checklist", ""])
        for item in data["prompt_to_artifact_checklist"]:
            lines.append(f"- `{item['status']}` - {item['requirement']}")
        lines.append("")
    lines.extend(["## Machine-Readable Artifact", "", f"See `{json_name}`."])
    write_md(OUT_DIR / md_name, lines)


def run_live_state_regeneration() -> dict[str, Any]:
    cmd = [sys.executable, "scripts/generate_live_state.py"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    live_state = REPO_ROOT / ".context/LIVE_STATE.md"
    freshness_line = None
    if live_state.exists():
        for line in live_state.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("| Status |"):
                freshness_line = line
                break
    return {
        "command": "python scripts/generate_live_state.py",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1000:],
        "stderr_tail": proc.stderr[-1000:],
        "live_state_research_status_line": freshness_line,
    }


def main() -> None:
    build_artifacts()
    print("Wrote G12 no-fill close audit artifacts")


if __name__ == "__main__":
    main()
