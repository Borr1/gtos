#!/usr/bin/env python3
"""Build NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1 artifacts.

This correction lane is source/control only. It audits the corrected upstream
NOFILL close packet after row 0127 is source-closed from OTR061 local tick
evidence. It does not compute R/performance, inspect broker/account/live/order
state, or change live trading behavior.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import py_compile
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-08"
SCHEMA = "nofill_lifecycle_closure_source_correction_v1"
CORRECTION_ID = "NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1"
PACKET_ID = "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OTR061_FILE = "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
OTR061_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
UPSTREAM_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
G12_DIR = OUTCOME_ROOT / "g12_no_fill_closure_audit"
OTR061_DIR = OUTCOME_ROOT / "otr061_xau_tick_recovery"
PROMPT_PATH = OUT_DIR / "NOFILL_CLOSURE_SOURCE_CORRECTION_GOAL_PROMPT_2026-05-08.md"

FORBIDDEN_PACKET_KEYS = {
    "actual_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "synthetic_r",
    "descriptive_synthetic_path_r",
    "descriptive_gross_synthetic_path_r",
    "conservative_lower_bound_r",
    "reward_r_to_tp1",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "broker_fill_state",
    "mt5_order_ticket",
    "pending_ticket",
    "trade_state_ticket",
    "hidden_label",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    body = [f"# {title}", ""]
    body.extend(lines)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def parse_utc(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_precise(value: Any) -> str | None:
    parsed = parse_utc(value)
    if parsed is None:
        return None
    return parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")


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


def scan_forbidden(obj: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in FORBIDDEN_PACKET_KEYS:
                hits.append({"path": f"{path}.{key}", "reason": "forbidden_key"})
            hits.extend(scan_forbidden(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden(value, f"{path}[{idx}]"))
    return hits


def load_inputs() -> dict[str, Any]:
    return {
        "packet": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json"),
        "rows": load_jsonl(UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"),
        "blocker": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json"),
        "source_search": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json"),
        "noleak": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "duplicate": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "forensics": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json"),
        "completion": load_json(UPSTREAM_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json"),
        "g12_decision": load_json(G12_DIR / "G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json"),
        "g12_closure": load_json(G12_DIR / "G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json"),
        "g12_blocker": load_json(G12_DIR / "G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json"),
        "g12_hash_noleak": load_json(G12_DIR / "G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json"),
        "g12_duplicate": load_json(G12_DIR / "G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json"),
        "g12_completion": load_json(G12_DIR / "G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json"),
        "otr061_hash": load_json(OTR061_DIR / "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json"),
        "otr061_search": load_json(OTR061_DIR / "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json"),
        "otr061_completion": load_json(OTR061_DIR / "OTR061_COMPLETION_AUDIT_2026-05-07.json"),
    }


def row_0127_resolution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = next(item for item in rows if item["packet_row_id"] == "NOFILL-CLOSE-ROW-0127")
    projection = row["source_evidence"]["tick_terminal_sequence_projection"]
    selected = projection.get("selected_supplemental_source_files") or []
    selected_path = Path(selected[0]) if selected else OTR061_DIR / OTR061_FILE
    df = pd.read_parquet(selected_path, columns=["ts_utc", "bid", "ask"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    start = pd.Timestamp(projection["path_start_utc"])
    end = pd.Timestamp(projection["path_end_utc"])
    window = df[(df["ts_utc"] >= start) & (df["ts_utc"] <= end)].sort_values("ts_utc")
    side = row["projected_side"]
    entry = row["source_evidence"].get("entry_price")
    terminal = row["source_evidence"].get("terminal_area_price")
    protective = row["source_evidence"].get("protective_level_price")
    entry_touch = first_touch(window, side, entry, "entry")
    terminal_touch = first_touch(window, side, terminal, "terminal")
    protective_touch = first_touch(window, side, protective, "protective")
    ordered = sorted(
        [
            {"event": name, "first_touch_utc": touch}
            for name, touch in [
                ("entry", entry_touch),
                ("terminal_area", terminal_touch),
                ("protective_level", protective_touch),
            ]
            if touch
        ],
        key=lambda item: item["first_touch_utc"],
    )
    return {
        "packet_row_id": row["packet_row_id"],
        "source_inventory_id": row["source_inventory_id"],
        "source_row_id": row["source_row_id"],
        "closure_status": row["closure_status"],
        "closure_label": row["closure_label"],
        "source_path": str(selected_path),
        "source_rel_path": rel(selected_path),
        "source_sha256": sha256_file(selected_path),
        "source_expected_sha256": OTR061_SHA256,
        "source_rows_total": int(len(df)),
        "source_first_ts_utc": df["ts_utc"].min().isoformat().replace("+00:00", "Z"),
        "source_last_ts_utc": df["ts_utc"].max().isoformat().replace("+00:00", "Z"),
        "requested_window_start_utc": projection["path_start_utc"],
        "requested_window_end_utc": projection["path_end_utc"],
        "rows_inside_requested_window": int(len(window)),
        "window_first_ts_utc": None if window.empty else window["ts_utc"].iloc[0].isoformat().replace("+00:00", "Z"),
        "window_last_ts_utc": None if window.empty else window["ts_utc"].iloc[-1].isoformat().replace("+00:00", "Z"),
        "entry_price": entry,
        "terminal_area_price": terminal,
        "protective_level_price": protective,
        "entry_touch_time_utc": entry_touch,
        "terminal_area_touch_time_utc": terminal_touch,
        "protective_level_touch_time_utc": protective_touch,
        "ordered_source_events": ordered,
        "first_source_event": ordered[0]["event"] if ordered else None,
        "source_closes_row": bool(row["closure_status"] == "source_closed" and ordered and ordered[0]["event"] == "terminal_area"),
        "no_r_performance_or_live_fields_used": True,
    }


def source_hash_checks(source_search: dict[str, Any]) -> dict[str, Any]:
    checks = []
    for item in source_search.get("consumed_source_files", []):
        path = Path(item.get("path", ""))
        expected = item.get("expected_sha256") or item.get("sha256")
        observed = sha256_file(path)
        role = item.get("role")
        strict = role != "controlling_or_upstream_input"
        checks.append({
            "path": str(path),
            "role": role,
            "exists": path.exists(),
            "expected_sha256": expected,
            "observed_sha256": observed,
            "matches": bool(expected and observed and expected == observed),
            "strict_source_hash_required": strict,
        })
    strict_mismatches = [
        item for item in checks
        if item["strict_source_hash_required"] and item["exists"] and item["expected_sha256"] and item["observed_sha256"] != item["expected_sha256"]
    ]
    strict_missing = [
        item for item in checks
        if item["strict_source_hash_required"] and item["expected_sha256"] and not item["exists"]
    ]
    return {
        "checked_count": len(checks),
        "strict_source_mismatch_count": len(strict_mismatches),
        "strict_source_missing_count": len(strict_missing),
        "checks": checks,
        "strict_mismatches": strict_mismatches,
        "strict_missing": strict_missing,
    }


def write_context_anchor(inputs: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    anchor = {
        "artifact_family": "NOFILL_CORR_CONTEXT_ANCHOR",
        "schema_version": SCHEMA,
        "correction_id": CORRECTION_ID,
        "generated_at_utc": utc_now(),
        "git_head": git_output("rev-parse", "HEAD"),
        "git_status_short": git_output("status", "--short"),
        "controlling_prompt_path": rel(PROMPT_PATH),
        "preflight_completed": True,
        "preflight_inputs_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_READING_ORDER.md",
            rel(PROMPT_PATH),
        ],
        "context_staleness_note": "LIVE_STATE reported UNKNOWN_LATEST_RESEARCH_COMMIT; direct G12, upstream packet, OTR061, builder, verifier, test, and context artifacts were read before correction.",
        "active_question_stack": [
            "Can NOFILL-CLOSE-ROW-0127 be source-closed from existing OTR061 local tick evidence?",
            "Did the upstream packet move from 297/1 to 298/0 without result leakage?",
            "Is the old read-only extraction request inactive or superseded?",
            "Do builder/verifier/tests search prior tick-recovery lanes and absolute heavy-data roots before missing-tick blockers?",
            "Do duplicate/sample-floor and promotion/live-effect boundaries remain false?",
        ],
        "searched_root_ledger": {
            "from_upstream_packet_source_search_roots": inputs["source_search"].get("searched_roots", []),
            "from_row_0127_supplemental_search": (
                next(row for row in inputs["rows"] if row["packet_row_id"] == "NOFILL-CLOSE-ROW-0127")
                ["source_evidence"]["tick_terminal_sequence_projection"]["supplemental_tick_source_search"]
            ),
        },
        "route_decision_ledger": [
            {
                "decision": "SOURCE_ONLY_CORRECTION_NOT_RESULT_LANE",
                "reason": "The lane corrects packet source closure and does not compute R/performance or inspect broker/account/live/order/hidden labels.",
            },
            {
                "decision": "PATCH_GENERATOR_NOT_STATIC_ONLY",
                "reason": "The upstream builder now searches OTR061/prior recovery lanes before emitting missing-tick blockers.",
            },
            {
                "decision": "SUPERSEDE_STALE_EXTRACTION_MANIFEST",
                "reason": "Row 0127 is source-closed from OTR061, so the old read-only request is retained only as inactive historical state.",
            },
        ],
        "row_0127_resolution_summary": resolution,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json", anchor)
    write_md(
        OUT_DIR / "NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.md",
        "NOFILL Correction Context Anchor - 2026-05-08",
        [
            f"Correction ID: `{CORRECTION_ID}`",
            f"Git HEAD: `{anchor['git_head']}`",
            f"Controlling prompt: `{anchor['controlling_prompt_path']}`",
            "",
            "## Active Questions",
            *[f"- {item}" for item in anchor["active_question_stack"]],
            "",
            "## Boundary",
            "- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        ],
    )
    return anchor


def write_source_resolution(inputs: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    packet_counts = inputs["packet"]["closure_status_counts"]
    g12_counts = inputs["g12_decision"]["g12_audited_counts_after_local_source_search"]
    ledger = {
        "artifact_family": "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "upstream_packet_id": PACKET_ID,
        "upstream_packet_counts_after_correction": {
            "packet_rows": inputs["packet"]["packet_row_count"],
            "source_closed": packet_counts.get("source_closed", 0),
            "source_blocked_exact": packet_counts.get("source_blocked_exact", 0),
        },
        "g12_corrected_counts": g12_counts,
        "row_0127_resolution": resolution,
        "stale_blocker_resolution": {
            "BLOCKED_NO_TICKS_IN_WINDOW_active_rows_after_correction": [
                row["packet_row_id"] for row in inputs["rows"]
                if any("BLOCKED_NO_TICKS_IN_WINDOW" in blocker for blocker in row.get("exact_blockers", []))
            ],
            "active_read_only_extraction_requests": inputs["blocker"].get("read_only_extraction_requests", []),
            "superseded_read_only_extraction_requests": inputs["blocker"].get("superseded_read_only_extraction_requests", []),
        },
        "source_only_non_claims": [
            "No R/performance/win-rate/expectancy/DSR/PBO was computed.",
            "No broker/account/live/order/hidden label was inspected.",
            "No blocked CNR061 row was scored.",
            "No validation, promotion, or live-effect lane was opened.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json", ledger)
    write_md(
        OUT_DIR / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.md",
        "NOFILL Correction Source Resolution Ledger - 2026-05-08",
        [
            f"Packet rows: `{ledger['upstream_packet_counts_after_correction']['packet_rows']}`",
            f"Source closed: `{ledger['upstream_packet_counts_after_correction']['source_closed']}`",
            f"Source blocked exact: `{ledger['upstream_packet_counts_after_correction']['source_blocked_exact']}`",
            f"Row 0127 source: `{resolution['source_rel_path']}`",
            f"Row 0127 SHA256: `{resolution['source_sha256']}`",
            f"Terminal first touch: `{resolution['terminal_area_touch_time_utc']}`",
            f"Active read-only extraction requests: `{len(ledger['stale_blocker_resolution']['active_read_only_extraction_requests'])}`",
        ],
    )
    return ledger


def write_patch_ledger() -> dict[str, Any]:
    changed = []
    for line in git_output("status", "--short").splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("warning:"):
            continue
        if len(line) >= 4:
            changed.append(line[3:].replace("\\", "/"))
    upstream_changed = [path for path in changed if path.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/")]
    correction_changed = [path for path in changed if path.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/")]
    ledger = {
        "artifact_family": "NOFILL_CORR_PATCH_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "changed_paths_observed": changed,
        "scoped_upstream_corrections": upstream_changed,
        "correction_lane_outputs": correction_changed,
        "patch_summary": [
            "Upstream tick source search now checks OTR061/prior tick-recovery lanes and absolute local roots before missing-tick blockers.",
            "NOFILL-CLOSE-ROW-0127 is source_closed from OTR061 source-hashed XAUUSD ticks.",
            "Packet status counts are 298 source_closed and 0 source_blocked_exact.",
            "Old read-only extraction manifest is inactive/superseded, not an active request.",
            "Verifier/tests enforce row 0127 OTR061 source closure and zero active blockers.",
        ],
        "forbidden_surface_statement": "No src, prompts, config, canary, execution, risk, permissions, safety, selector, MT5 order/account, paid/API/Databento, credential, remote, or order-behavior files are part of this correction.",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_PATCH_LEDGER_2026-05-08.json", ledger)
    write_md(
        OUT_DIR / "NOFILL_CORR_PATCH_LEDGER_2026-05-08.md",
        "NOFILL Correction Patch Ledger - 2026-05-08",
        ["## Patch Summary", *[f"- {item}" for item in ledger["patch_summary"]], "", "## Scoped Paths", *[f"- `{path}`" for path in upstream_changed + correction_changed]],
    )
    return ledger


def write_hash_noleak(inputs: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    hash_checks = source_hash_checks(inputs["source_search"])
    forbidden_hits = scan_forbidden(inputs["rows"])
    flag_violations = [
        row["packet_row_id"] for row in inputs["rows"]
        if row.get("promotion_verdict") != PROMOTION_VERDICT
        or row.get("validation_safe") is not False
        or row.get("outcome_review_opened") is not False
        or row.get("live_effect") is not False
    ]
    otr061_hash_matches = resolution["source_sha256"] == OTR061_SHA256
    audit = {
        "artifact_family": "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "otr061_source_hash": {
            "path": resolution["source_path"],
            "expected_sha256": OTR061_SHA256,
            "observed_sha256": resolution["source_sha256"],
            "matches": otr061_hash_matches,
        },
        "corrected_packet_source_hash_checks": hash_checks,
        "forbidden_packet_hits": forbidden_hits,
        "forbidden_packet_hits_count": len(forbidden_hits),
        "flag_violations": flag_violations,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_account_calls": 0,
        "mt5_order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "status": "PASS" if otr061_hash_matches and hash_checks["strict_source_mismatch_count"] == 0 and hash_checks["strict_source_missing_count"] == 0 and not forbidden_hits and not flag_violations else "FAIL",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json", audit)
    write_md(
        OUT_DIR / "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md",
        "NOFILL Correction Source Hash And No-Leak Audit - 2026-05-08",
        [
            f"Status: `{audit['status']}`",
            f"OTR061 hash matches: `{otr061_hash_matches}`",
            f"Strict source mismatches: `{hash_checks['strict_source_mismatch_count']}`",
            f"Strict source missing: `{hash_checks['strict_source_missing_count']}`",
            f"Forbidden packet hits: `{len(forbidden_hits)}`",
        ],
    )
    return audit


def write_duplicate_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["rows"]
    duplicate = inputs["duplicate"]
    audit = {
        "artifact_family": "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "packet_rows": len(rows),
        "source_inventory_id_unique": len({row["source_inventory_id"] for row in rows}),
        "nofill_duplicate_key_unique": duplicate.get("nofill_duplicate_key_unique"),
        "duplicate_group_id_unique": duplicate.get("duplicate_group_id_unique"),
        "closure_label_counts": dict(sorted(Counter(row["closure_label"] for row in rows).items())),
        "closure_status_counts": dict(sorted(Counter(row["closure_status"] for row in rows).items())),
        "validation_sample_floor_status": duplicate.get("validation_sample_floor_status"),
        "sample_floor_reason": duplicate.get("sample_floor_reason"),
        "status": "PASS" if duplicate.get("validation_sample_floor_status") == "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION" and len(rows) == 298 else "FAIL",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", audit)
    write_md(
        OUT_DIR / "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
        "NOFILL Correction Duplicate Sample-Floor Audit - 2026-05-08",
        [
            f"Rows: `{audit['packet_rows']}`",
            f"Unique source inventory IDs: `{audit['source_inventory_id_unique']}`",
            f"Validation sample floor: `{audit['validation_sample_floor_status']}`",
            f"Status: `{audit['status']}`",
        ],
    )
    return audit


def write_forensics(inputs: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    forensics = {
        "artifact_family": "NOFILL_CORR_FORENSICS_AND_LEARNING",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "source_closure_learning": [
            "The upstream missing-tick blocker was source-boxed to the packet-cited daily tick file; prior OTR061 recovery already contained the decisive XAUUSD source window.",
            "For terminal-first source closure, full 07:15-17:15 coverage is not required after a source-hashed terminal-area first touch is observed at 07:15:00.634000Z.",
            "Future missing-tick blockers must record prior recovery lane and absolute heavy-data searches before emitting extraction manifests.",
        ],
        "failure_anatomy": {
            "upstream_failure": "BLOCKED_NO_TICKS_IN_WINDOW was exact only inside the original source search box; local-heavy-data search found the source.",
            "corrected_state": "NOFILL-CLOSE-ROW-0127 is source_closed and remains terminal_sequence_tick_source_projected_no_score.",
            "remaining_non_result_limit": "Opening-drive prereg field blockers remain as source/control notes; they are not R/performance labels.",
        },
        "row_0127_resolution": resolution,
        "non_claims": [
            "No R/performance was scored.",
            "No broker/account/live/order/hidden labels were inspected.",
            "No validation, promotion, outcome review, or live effect was opened.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json", forensics)
    write_md(
        OUT_DIR / "NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md",
        "NOFILL Correction Forensics And Learning - 2026-05-08",
        ["## Learning", *[f"- {item}" for item in forensics["source_closure_learning"]], "", "## Non-Claims", *[f"- {item}" for item in forensics["non_claims"]]],
    )
    return forensics


def write_g12_reaudit_prompt(resolution: dict[str, Any]) -> None:
    text = f"""# NOFILL Correction G12 Reaudit Prompt Pack - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Recommended G12 Goal

Audit `NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1` and the corrected upstream `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1` as source/control evidence only.

Verify that the upstream packet now reports `298` total rows, `298 source_closed`, and `0 source_blocked_exact`; that `NOFILL-CLOSE-ROW-0127` is source-closed from `{resolution['source_rel_path']}` with SHA256 `{resolution['source_sha256']}`; and that the first side-aware source event is terminal-area touch at `{resolution['terminal_area_touch_time_utc']}`.

## Required Reaudit Checks

- Recompute the OTR061 parquet SHA256 and source coverage (`{resolution['source_first_ts_utc']}` through `{resolution['source_last_ts_utc']}`).
- Confirm the stale `BLOCKED_NO_TICKS_IN_WINDOW` blocker and active read-only request are gone or superseded.
- Confirm source-search logic searches prior tick-recovery lanes and absolute local heavy-data roots before missing-tick blockers.
- Confirm six T3 rows and 94 G12-blocked CNR061 rows remain excluded.
- Confirm duplicate/sample-floor controls keep validation blocked.
- Confirm no R/performance, broker/account/live/order/hidden labels, blocked CNR061 scoring, paid/API/Databento calls, MT5 account/order calls, or live trading surface changes.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Non-Claims

This correction proves source closure and first-touch source ordering for row `0127` only. It does not prove R/performance, validation, promotion, live effects, T1/T2/E2/E3/E4, or any broker/account/live outcome.
"""
    (OUT_DIR / "NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md").write_text(text, encoding="utf-8")


def write_completion(
    source_resolution: dict[str, Any],
    hash_noleak: dict[str, Any],
    duplicate: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {"requirement": "Mandatory GTOS preflight", "status": "PASS", "evidence": "LIVE_STATE regenerated and core docs/direct artifacts read before correction."},
        {"requirement": "G12 audit, upstream packet, OTR061 artifacts, builders, verifiers, tests, context docs read", "status": "PASS", "evidence": "Context anchor and source resolution ledger enumerate controlling inputs and direct artifacts."},
        {"requirement": "Row 0127 source-closed from OTR061", "status": "PASS" if source_resolution["row_0127_resolution"]["source_closes_row"] else "FAIL", "evidence": source_resolution["row_0127_resolution"]["source_rel_path"]},
        {"requirement": "Packet counts 298 source_closed / 0 source_blocked_exact", "status": "PASS" if source_resolution["upstream_packet_counts_after_correction"]["source_closed"] == 298 and source_resolution["upstream_packet_counts_after_correction"]["source_blocked_exact"] == 0 else "FAIL", "evidence": json.dumps(source_resolution["upstream_packet_counts_after_correction"], sort_keys=True)},
        {"requirement": "Stale blocker/extraction request resolved", "status": "PASS" if not source_resolution["stale_blocker_resolution"]["BLOCKED_NO_TICKS_IN_WINDOW_active_rows_after_correction"] and not source_resolution["stale_blocker_resolution"]["active_read_only_extraction_requests"] else "FAIL", "evidence": "active BLOCKED_NO_TICKS rows and active requests are empty; superseded manifest recorded."},
        {"requirement": "Source hashes and no-leak", "status": hash_noleak["status"], "evidence": f"OTR061 hash matches={hash_noleak['otr061_source_hash']['matches']} forbidden_hits={hash_noleak['forbidden_packet_hits_count']}"},
        {"requirement": "Duplicate/sample-floor validation remains blocked", "status": duplicate["status"], "evidence": duplicate["validation_sample_floor_status"]},
        {"requirement": "G12 reaudit guidance", "status": "PASS", "evidence": "NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md"},
        {"requirement": "Verifier/tests", "status": "PENDING_VERIFIER_RUN", "evidence": "Correction verifier will update this audit."},
    ]
    completion = {
        "artifact_family": "NOFILL_CORR_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "objective_restatement": "Correct the upstream NOFILL close packet so NOFILL-CLOSE-ROW-0127 is source-closed from existing OTR061 XAUUSD tick evidence, packet counts become 298/0, stale blocker state is superseded, and source/no-leak/duplicate/verifier/G12 reaudit artifacts pass.",
        "prompt_to_artifact_checklist": checklist,
        "completion_status": "BUILT_PENDING_VERIFIER",
        "can_mark_goal_complete": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json", completion)
    write_completion_md(completion)
    return completion


def write_completion_md(completion: dict[str, Any]) -> None:
    lines = [
        f"Completion status: `{completion['completion_status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    lines += [f"- `{item['status']}` {item['requirement']}: {item['evidence']}" for item in completion["prompt_to_artifact_checklist"]]
    if completion.get("verification_results"):
        lines += ["", "## Verification Results"]
        for name, result in completion["verification_results"].get("results", {}).items():
            status = result.get("status") if isinstance(result, dict) else result
            lines.append(f"- `{status}` {name}")
    write_md(OUT_DIR / "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md", "NOFILL Correction Completion Audit - 2026-05-08", lines)


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    resolution = row_0127_resolution(inputs["rows"])
    anchor = write_context_anchor(inputs, resolution)
    source_resolution = write_source_resolution(inputs, resolution)
    hash_noleak = write_hash_noleak(inputs, resolution)
    duplicate = write_duplicate_audit(inputs)
    forensics = write_forensics(inputs, resolution)
    write_g12_reaudit_prompt(resolution)
    completion = write_completion(source_resolution, hash_noleak, duplicate)
    patch = write_patch_ledger()
    return {
        "status": "BUILT",
        "anchor": anchor["artifact_family"],
        "patch_changed_paths": len(patch["changed_paths_observed"]),
        "packet_counts": source_resolution["upstream_packet_counts_after_correction"],
        "row_0127_source_closes": resolution["source_closes_row"],
        "hash_noleak_status": hash_noleak["status"],
        "duplicate_status": duplicate["status"],
        "completion_status": completion["completion_status"],
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
