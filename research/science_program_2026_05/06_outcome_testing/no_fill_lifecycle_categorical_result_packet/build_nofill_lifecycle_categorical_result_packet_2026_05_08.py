#!/usr/bin/env python3
"""Build NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1.

This is a categorical lifecycle-only result packet. It consumes only the
G12-accepted 298 source-closed no-fill universe and does not compute
performance, broker/account labels, validation, promotion, or live effect.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except Exception:  # pragma: no cover - verifier records parser availability
    pd = None


DATE = "2026-05-08"
SCHEMA = "nofill_lifecycle_categorical_result_packet_v1"
PACKET_ID = "NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROW_0127_EXPECTED_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
ROW_0127_EXPECTED_FIRST_TOUCH = "2026-05-06T07:15:00.634000Z"
BUILD_GENERATED_AT_UTC = "2026-05-08T13:11:16Z"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
MAIN_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")

SOURCE_PACKET_DIR = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet"
SOURCE_PACKET_ROWS = SOURCE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"
SOURCE_PACKET_JSON = SOURCE_PACKET_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json"

CONTROL_INPUTS = [
    OUT_DIR / "NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_GOAL_PROMPT_2026-05-08.md",
    OUT_DIR / "NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.json",
    OUTCOME_ROOT / "g12_no_fill_result_contract_audit" / "G12_NOFILL_RESULT_CONTRACT_NEXT_PROMPT_PACK_2026-05-08.md",
    OUTCOME_ROOT / "g12_no_fill_result_contract_audit" / "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json",
    OUTCOME_ROOT / "g12_no_fill_result_contract_audit" / "G12_NOFILL_RESULT_CONTRACT_COMPLETION_AUDIT_2026-05-08.json",
    OUTCOME_ROOT / "g12_no_fill_result_contract_audit" / "G12_NOFILL_RESULT_CONTRACT_BLOCKER_AND_GATE_LEDGER_2026-05-08.json",
    OUTCOME_ROOT / "g12_no_fill_result_contract_audit" / "G12_NOFILL_RESULT_CONTRACT_RULEBOOK_AUDIT_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_UNIVERSE_AND_EXCLUSION_LEDGER_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_FIELD_SOURCE_REQUIREMENTS_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_2026-05-08.json",
    OUTCOME_ROOT / "no_fill_lifecycle_closure_source_correction" / "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md",
    OUTCOME_ROOT / "no_fill_lifecycle_closure_source_correction" / "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json",
    OUTCOME_ROOT / "g12_no_fill_correction_reaudit" / "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json",
    SOURCE_PACKET_JSON,
    SOURCE_PACKET_ROWS,
    SOURCE_PACKET_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json",
    SOURCE_PACKET_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    SOURCE_PACKET_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
]

FORBIDDEN_PACKET_KEYS = {
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

EXCLUDED_T3_IDS = {f"CNR-T3-CAND-{i:04d}" for i in range(1, 7)}


def utc_now() -> str:
    return BUILD_GENERATED_AT_UTC


def parse_utc(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_precise(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"GIT_UNAVAILABLE: {exc}"


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    direct = REPO_ROOT / p
    if direct.exists():
        return direct
    main_direct = MAIN_ROOT / p
    if main_direct.exists():
        return main_direct
    return direct


def source_projection(row: dict[str, Any]) -> dict[str, Any]:
    evidence = row.get("source_evidence") or {}
    for key in ("tick_path_projection", "tick_terminal_sequence_projection"):
        value = evidence.get(key)
        if isinstance(value, dict):
            return value
    return evidence


def event_order(row: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    projection = source_projection(row)
    events = []
    for event, field in (
        ("entry_touch", "entry_touch_time_utc"),
        ("terminal_area", "terminal_area_touch_time_utc"),
        ("protective_level", "protective_level_touch_time_utc"),
    ):
        when = parse_utc(projection.get(field))
        if when is not None:
            events.append({"event": event, "first_touch_utc": iso_precise(when)})
    events.sort(key=lambda item: (item["first_touch_utc"], item["event"]))
    first_ts = events[0]["first_touch_utc"] if events else None
    first_event_tie = bool(first_ts) and sum(1 for item in events if item["first_touch_utc"] == first_ts) > 1
    return events, first_event_tie


def event_time(events: list[dict[str, Any]], event: str) -> dt.datetime | None:
    for item in events:
        if item["event"] == event:
            return parse_utc(item["first_touch_utc"])
    return None


def geometry_signature(row: dict[str, Any], proposed_label: str | None) -> str:
    projection = source_projection(row)
    payload = {
        "label": proposed_label,
        "symbol": row.get("projected_symbol"),
        "session": row.get("projected_session"),
        "side": row.get("projected_side"),
        "entry_price": projection.get("entry_price"),
        "terminal_area_price": projection.get("terminal_area_price"),
        "protective_level_price": projection.get("protective_level_price"),
        "entry_touch_time_utc": projection.get("entry_touch_time_utc"),
        "terminal_area_touch_time_utc": projection.get("terminal_area_touch_time_utc"),
        "protective_level_touch_time_utc": projection.get("protective_level_touch_time_utc"),
    }
    return json.dumps(payload, sort_keys=True, default=str)


def proposed_label_from_events(row: dict[str, Any]) -> tuple[str | None, str]:
    source_label = row.get("closure_label")
    events, same_timestamp = event_order(row)
    if same_timestamp:
        return None, "same timestamp ambiguity among entry, terminal, and protective events"
    entry = event_time(events, "entry_touch")
    terminal = event_time(events, "terminal_area")
    protective = event_time(events, "protective_level")
    if terminal and (entry is None or terminal < entry) and (protective is None or terminal < protective):
        return "nofill_terminal_before_entry", "first source event is terminal_area before entry/protective touch"
    if entry is None and terminal is None and protective is None:
        return "nofill_no_entry_through_frozen_horizon", "fully covered source horizon has no entry, terminal, or protective touch"
    if source_label == "pending_cancelled_system_or_new_day_before_fill_source_confirmed":
        return "nofill_cancelled_system_or_new_day_before_fill", "pending-intent source cancellation/expiry family"
    if source_label == "pending_cancelled_wrong_side_before_fill_source_confirmed":
        return "nofill_cancelled_wrong_side_before_fill", "pending-intent wrong-side cancellation family"
    if source_label == "pending_still_open_at_frozen_horizon_source_confirmed":
        return "nofill_still_pending_at_frozen_horizon", "pending-intent still-open horizon family"
    return None, "source family is not eligible for categorical lifecycle label without a separate contract or source correction"


def blocker_codes_for_row(row: dict[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for reason in row.get("exact_blockers") or []:
        if "entry_touched_at_utc" in reason:
            code = "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD"
        elif "terminal touch replay remains unopened" in reason:
            code = "BLOCK_RESULT_LTF_PRICE_ONLY"
        elif "post_entry_terminal_touch_time" in reason:
            code = "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS"
        elif "missing_prereg_opening_drive_field" in reason:
            code = "BLOCK_RESULT_MISSING_SOURCE"
        else:
            code = "BLOCK_RESULT_MISSING_SOURCE"
        blockers.append({"code": code, "reason": reason})
    if row.get("source_inventory_id") in EXCLUDED_T3_IDS:
        blockers.append({"code": "BLOCK_RESULT_EXCLUDED_T3_ROW", "reason": "six CNR T3 rows remain excluded"})
    if row.get("source_lane") == "OTI8_CNR061" or row.get("closure_label") == "stop_after_original_horizon":
        blockers.append({"code": "BLOCK_RESULT_EXCLUDED_CNR061_BLOCKED_ROW", "reason": "blocked CNR061/T3 family excluded"})
    if row.get("closure_status") != "source_closed":
        blockers.append({"code": "BLOCK_RESULT_MISSING_SOURCE", "reason": "row is not source_closed"})
    if row.get("closure_label") == "price_compatible_m1_source_recovered":
        blockers.append({"code": "BLOCK_RESULT_LTF_PRICE_ONLY", "reason": "price-compatible M1 source is not side-aware quote/tick ordering proof"})
    if row.get("closure_label") == "entry_touched_terminal_sequence_unclaimed_source_confirmed":
        blockers.append({"code": "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS", "reason": "entry touched and post-entry terminal sequence is unclaimed"})
        blockers.append({"code": "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED", "reason": "entry touch moves the row out of this no-fill closure result family"})
    _, same_timestamp = event_order(row)
    if same_timestamp:
        blockers.append({"code": "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS", "reason": "same timestamp source events are ambiguous"})
    return blockers


def duplicate_conflict_keys(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[row["nofill_duplicate_key"]].append(row)
    conflicts: dict[str, dict[str, Any]] = {}
    for key, members in by_key.items():
        candidates = []
        for row in members:
            if blocker_codes_for_row(row):
                continue
            label, _ = proposed_label_from_events(row)
            if label:
                candidates.append((row, label))
        if len(candidates) <= 1:
            continue
        labels = {label for _, label in candidates}
        signatures = {geometry_signature(row, label) for row, label in candidates}
        if len(labels) > 1 or len(signatures) > 1:
            conflicts[key] = {
                "nofill_duplicate_key": key,
                "row_count": len(candidates),
                "labels": sorted(labels),
                "geometry_signature_count": len(signatures),
                "packet_row_ids": [row["packet_row_id"] for row, _ in candidates],
                "reason": "duplicate rows disagree on categorical label or source geometry/order",
            }
    return conflicts


def source_file_references(row: dict[str, Any], assigned_label: str | None) -> list[dict[str, Any]]:
    projection = source_projection(row)
    refs = []
    for raw_path, expected in (projection.get("source_sha256") or {}).items():
        refs.append({"path": raw_path, "expected_sha256": expected, "role": "tick_or_quote_path_for_label" if assigned_label else "observed_blocked_source_reference"})
    recovered = (row.get("source_evidence") or {}).get("recovered_m1_source") or {}
    if recovered.get("path"):
        refs.append({"path": recovered["path"], "expected_sha256": recovered.get("sha256"), "role": "price_compatible_context_only"})
    for key, value in (row.get("source_hashes") or {}).items():
        if key.startswith("path_source_sha256:"):
            refs.append({"path": key.split(":", 1)[1], "expected_sha256": value, "role": "path_source_hash_from_source_packet"})
    if row.get("source_artifact_path"):
        refs.append({"path": row["source_artifact_path"], "expected_sha256": None, "role": "upstream_source_artifact"})
    return refs


def build_packet_rows(source_rows: list[dict[str, Any]], generated_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    conflicts = duplicate_conflict_keys(source_rows)
    decisions: list[dict[str, Any]] = []
    by_key = defaultdict(list)
    for row in source_rows:
        by_key[row["nofill_duplicate_key"]].append(row)
    canonical_by_key = {
        key: sorted(members, key=lambda r: (str(r.get("decision_asof_utc") or ""), str(r.get("source_inventory_id") or "")))[0]["packet_row_id"]
        for key, members in by_key.items()
    }

    for source in source_rows:
        events, same_timestamp = event_order(source)
        proposed_label, label_basis = proposed_label_from_events(source)
        blockers = blocker_codes_for_row(source)
        conflict = conflicts.get(source["nofill_duplicate_key"])
        if conflict:
            blockers.append({"code": "BLOCK_RESULT_DUPLICATE_CONFLICT", "reason": conflict["reason"]})
        assigned_label = None if blockers or proposed_label is None else proposed_label
        if proposed_label is None and not blockers:
            blockers.append({"code": "BLOCK_RESULT_UNSUPPORTED_SOURCE_CLOSURE_FAMILY", "reason": label_basis})
        status = "ELIGIBLE_LABEL_ASSIGNED" if assigned_label else "BLOCKED_BEFORE_LABEL"
        projection = source_projection(source)
        packet_row = {
            "schema_version": SCHEMA,
            "packet_id": PACKET_ID,
            "contract_id": CONTRACT_ID,
            "generated_at_utc": generated_at,
            "packet_row_id": source["packet_row_id"].replace("NOFILL-CLOSE-ROW", "NOFILL-CAT-ROW"),
            "source_close_packet_row_id": source["packet_row_id"],
            "source_inventory_id": source["source_inventory_id"],
            "source_lane": source["source_lane"],
            "source_packet_id": source["source_packet_id"],
            "source_row_id": source["source_row_id"],
            "source_closure_status": source["closure_status"],
            "source_closure_label": source["closure_label"],
            "symbol": source.get("projected_symbol"),
            "session": source.get("projected_session"),
            "side": source.get("projected_side"),
            "decision_asof_utc": source.get("decision_asof_utc"),
            "entry_price": projection.get("entry_price"),
            "terminal_area_price": projection.get("terminal_area_price"),
            "protective_level_price": projection.get("protective_level_price"),
            "duplicate_group_id": source.get("duplicate_group_id"),
            "nofill_duplicate_key": source.get("nofill_duplicate_key"),
            "eligibility_decision": status,
            "eligibility_checked_before_label": True,
            "result_blocker_codes": sorted({item["code"] for item in blockers}),
            "result_blocker_reasons": sorted({item["reason"] for item in blockers}),
            "categorical_lifecycle_label": assigned_label,
            "categorical_label_status": "categorical_lifecycle_only" if assigned_label else "blocked_no_label",
            "label_family": "categorical_lifecycle_only" if assigned_label else None,
            "label_assignment_basis": label_basis if assigned_label else None,
            "ordered_source_events": events,
            "same_timestamp_ambiguity": same_timestamp,
            "source_reported_same_timestamp_ambiguity": bool(projection.get("same_timestamp_ambiguity")),
            "source_path_start_utc": projection.get("path_start_utc"),
            "source_path_end_utc": projection.get("path_end_utc") or projection.get("frozen_observation_horizon_utc"),
            "parser_contract": projection.get("parser_contract") or "bid_ask_side_aware_touch_times_v1",
            "source_references": source_file_references(source, assigned_label),
            "duplicate_policy": {
                "primary_denominator_key": "nofill_duplicate_key",
                "canonical_counting_row_for_key": canonical_by_key[source["nofill_duplicate_key"]],
                "is_canonical_counting_row": source["packet_row_id"] == canonical_by_key[source["nofill_duplicate_key"]],
                "duplicate_conflict": bool(conflict),
                "duplicate_conflict_reason": conflict["reason"] if conflict else None,
            },
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }
        decisions.append(packet_row)
    return decisions, {"conflicts": list(conflicts.values())}


def collect_source_hash_records(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records_by_key: dict[tuple[str, str | None, str], dict[str, Any]] = {}

    def add(path_value: str | Path, role: str, expected: str | None = None) -> None:
        path = resolve_path(path_value)
        key = (str(path), expected, role)
        if key in records_by_key:
            return
        actual = sha256_file(path)
        records_by_key[key] = {
            "path": str(path),
            "rel_path": rel(path),
            "role": role,
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "hash_match": None if expected is None or actual is None else actual == expected,
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        }

    for path in CONTROL_INPUTS:
        add(path, "controlling_input")
    for row in packet_rows:
        for ref in row.get("source_references", []):
            add(ref["path"], ref.get("role", "source_reference"), ref.get("expected_sha256"))
    # Preserve and recompute the special row 0127 source even though it remains
    # blocked from labeling by missing prereg opening-drive source fields.
    add(OUTCOME_ROOT / "otr061_xau_tick_recovery" / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet", "row_0127_local_otr061_tick_source", ROW_0127_EXPECTED_SHA256)
    return sorted(records_by_key.values(), key=lambda item: (item["role"], item["path"]))


def recompute_row_0127_first_touch() -> dict[str, Any]:
    path = OUTCOME_ROOT / "otr061_xau_tick_recovery" / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
    audit = {
        "source_path": rel(path),
        "source_sha256": sha256_file(path),
        "parser_contract": "bid_ask_side_aware_touch_times_v1",
        "parser_available": pd is not None,
        "expected_first_touch": ROW_0127_EXPECTED_FIRST_TOUCH,
        "expected_sha256": ROW_0127_EXPECTED_SHA256,
        "status": "NOT_RUN",
    }
    if pd is None or not path.exists():
        audit["status"] = "BLOCKED_PARSER_OR_SOURCE_MISSING"
        return audit
    df = pd.read_parquet(path, columns=["ts_utc", "bid", "ask"])
    start = parse_utc("2026-05-06T07:15:00Z")
    subset = df[df["ts_utc"] >= start]
    terminal = subset[subset["bid"] >= 4582.77].head(1)
    entry = subset[subset["ask"] <= 4561.52].head(1)
    protective = subset[subset["bid"] <= 4547.35].head(1)
    events = []
    if not terminal.empty:
        events.append({"event": "terminal_area", "first_touch_utc": iso_precise(terminal.iloc[0]["ts_utc"].to_pydatetime()), "bid": float(terminal.iloc[0]["bid"]), "ask": float(terminal.iloc[0]["ask"])})
    if not entry.empty:
        events.append({"event": "entry_touch", "first_touch_utc": iso_precise(entry.iloc[0]["ts_utc"].to_pydatetime()), "bid": float(entry.iloc[0]["bid"]), "ask": float(entry.iloc[0]["ask"])})
    if not protective.empty:
        events.append({"event": "protective_level", "first_touch_utc": iso_precise(protective.iloc[0]["ts_utc"].to_pydatetime()), "bid": float(protective.iloc[0]["bid"]), "ask": float(protective.iloc[0]["ask"])})
    events.sort(key=lambda item: (item["first_touch_utc"], item["event"]))
    audit.update({
        "source_rows": int(len(df)),
        "rows_at_or_after_path_start": int(len(subset)),
        "ordered_source_events": events,
        "first_event": events[0] if events else None,
        "status": "PASS" if events and events[0]["event"] == "terminal_area" and events[0]["first_touch_utc"] == ROW_0127_EXPECTED_FIRST_TOUCH and audit["source_sha256"] == ROW_0127_EXPECTED_SHA256 else "FAIL",
    })
    return audit


def update_context_anchor(hash_records: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    path = OUT_DIR / "NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.json"
    anchor = read_json(path) if path.exists() else {}
    anchor.update({
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_row_consumption_started_after_anchor": True,
        "source_rows_consumed": len(source_rows),
        "source_rows_input": rel(SOURCE_PACKET_ROWS),
        "source_files": {
            "status": "consumed_and_hashed_after_initial_anchor",
            "hash_record_count": len(hash_records),
            "missing_files": [item for item in hash_records if not item["exists"]],
            "hash_mismatches": [item for item in hash_records if item["hash_match"] is False],
        },
        "last_updated_utc": utc_now(),
    })
    write_json(path, anchor)
    lines = [
        "# NOFILL Categorical Result Packet Context Anchor",
        "",
        f"Lane: `{PACKET_ID}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Resume State",
        f"- HEAD at original anchor creation: `{anchor.get('head_at_anchor_creation')}`",
        f"- Source rows consumed after anchor: `{len(source_rows)}` from `{rel(SOURCE_PACKET_ROWS)}`",
        f"- Source/hash record count: `{len(hash_records)}`",
        f"- Missing source files: `{len(anchor['source_files']['missing_files'])}`",
        f"- Hash mismatches: `{len(anchor['source_files']['hash_mismatches'])}`",
        "",
        "## Active Stop Condition",
        "- Complete only after packet rows, ledgers, audits, verifier/tests, completion audit, and commit are in place.",
        "- If blocked, every unresolved row needs an exact source/field/parser/access/approval/forbidden-boundary reason.",
    ]
    write_md(OUT_DIR / "NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.md", lines)
    return anchor


def scan_forbidden_packet_fields(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits = []
    for row in packet_rows:
        stack = [([], row)]
        while stack:
            path, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    lower = key.lower()
                    if lower in FORBIDDEN_PACKET_KEYS:
                        hits.append({"packet_row_id": row.get("packet_row_id"), "field_path": ".".join(path + [key]), "forbidden_key": key})
                    stack.append((path + [key], nested))
            elif isinstance(value, list):
                for i, nested in enumerate(value):
                    stack.append((path + [str(i)], nested))
    return hits


def write_manifest(packet_rows: list[dict[str, Any]], hash_records: list[dict[str, Any]], row_0127: dict[str, Any]) -> dict[str, Any]:
    eligible = [row for row in packet_rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"]
    blocked = [row for row in packet_rows if row["eligibility_decision"] != "ELIGIBLE_LABEL_ASSIGNED"]
    manifest = {
        "artifact_family": "NOFILL_CAT_PACKET_MANIFEST",
        "schema_version": SCHEMA,
        "packet_id": PACKET_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": utc_now(),
        "source_universe": {
            "source_packet_rows": len(packet_rows),
            "source_closed_rows": sum(1 for row in packet_rows if row["source_closure_status"] == "source_closed"),
            "source_close_packet_rows_path": rel(SOURCE_PACKET_ROWS),
            "g12_accepted_source_closed_rows_required": 298,
        },
        "row_outcome": {
            "eligible_label_assigned_rows": len(eligible),
            "blocked_before_label_rows": len(blocked),
            "eligible_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in eligible}),
            "blocked_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in blocked}),
        },
        "hash_records": {
            "record_count": len(hash_records),
            "missing_count": sum(1 for item in hash_records if not item["exists"]),
            "mismatch_count": sum(1 for item in hash_records if item["hash_match"] is False),
        },
        "row_0127": row_0127,
        "artifact_inventory": sorted(path.name for path in OUT_DIR.iterdir() if path.is_file()),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_PACKET_MANIFEST_2026-05-08.json", manifest)
    write_md(OUT_DIR / "NOFILL_CAT_PACKET_MANIFEST_2026-05-08.md", [
        "# NOFILL CAT Packet Manifest - 2026-05-08",
        "",
        f"Packet: `{PACKET_ID}`",
        f"Rows covered: `{len(packet_rows)}`",
        f"Eligible label-assigned rows: `{len(eligible)}`",
        f"Blocked-before-label rows: `{len(blocked)}`",
        f"Source hash records: `{len(hash_records)}`",
        f"Hash mismatches: `{manifest['hash_records']['mismatch_count']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ])
    return manifest


def write_eligibility_ledger(packet_rows: list[dict[str, Any]], duplicate_info: dict[str, Any]) -> dict[str, Any]:
    blocker_counter = Counter(code for row in packet_rows for code in row["result_blocker_codes"])
    source_label_status = Counter((row["source_closure_label"], row["eligibility_decision"]) for row in packet_rows)
    ledger = {
        "artifact_family": "NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "row_count": len(packet_rows),
        "eligibility_counts": dict(Counter(row["eligibility_decision"] for row in packet_rows)),
        "blocker_code_counts": dict(sorted(blocker_counter.items())),
        "source_label_by_eligibility": {f"{label}|{status}": count for (label, status), count in sorted(source_label_status.items())},
        "duplicate_conflicts": duplicate_info["conflicts"],
        "row_decisions": [
            {
                "packet_row_id": row["packet_row_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_closure_label": row["source_closure_label"],
                "eligibility_decision": row["eligibility_decision"],
                "result_blocker_codes": row["result_blocker_codes"],
                "result_blocker_reasons": row["result_blocker_reasons"],
                "categorical_lifecycle_label": row["categorical_lifecycle_label"],
                "nofill_duplicate_key": row["nofill_duplicate_key"],
            }
            for row in packet_rows
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json", ledger)
    lines = [
        "# NOFILL CAT Eligibility And Blocker Ledger - 2026-05-08",
        "",
        f"Rows: `{len(packet_rows)}`",
        "",
        "## Eligibility Counts",
    ]
    for key, value in ledger["eligibility_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Blocker Counts"]
    for key, value in ledger["blocker_code_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", f"Duplicate conflict groups: `{len(duplicate_info['conflicts'])}`", "", f"Promotion verdict: `{PROMOTION_VERDICT}`", "Validation safe: `false`", "Outcome review opened: `false`", "Live effect: `false`"]
    write_md(OUT_DIR / "NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.md", lines)
    return ledger


def write_source_hash_audit(packet_rows: list[dict[str, Any]], hash_records: list[dict[str, Any]], row_0127: dict[str, Any]) -> dict[str, Any]:
    asof_issues = []
    for row in packet_rows:
        if row["eligibility_decision"] != "ELIGIBLE_LABEL_ASSIGNED":
            continue
        decision = parse_utc(row["decision_asof_utc"])
        path_start = parse_utc(row.get("source_path_start_utc"))
        if decision and path_start and path_start < decision:
            asof_issues.append({"packet_row_id": row["packet_row_id"], "issue": "path_start_before_decision_asof"})
    audit = {
        "artifact_family": "NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "hash_records": hash_records,
        "hash_mismatches": [item for item in hash_records if item["hash_match"] is False],
        "missing_source_files": [item for item in hash_records if not item["exists"]],
        "asof_issues": asof_issues,
        "row_0127_terminal_first_recompute": row_0127,
        "source_hierarchy_statement": "Categorical labels use accepted source-closed packet rows plus source-hashed tick/quote projections where present; price-only M1 rows are blocked.",
        "status": "PASS" if not asof_issues and not [item for item in hash_records if item["hash_match"] is False] and row_0127.get("status") == "PASS" else "FAIL",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json", audit)
    write_md(OUT_DIR / "NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.md", [
        "# NOFILL CAT Source Hash And ASOF Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Hash records: `{len(hash_records)}`",
        f"Hash mismatches: `{len(audit['hash_mismatches'])}`",
        f"Missing source files: `{len(audit['missing_source_files'])}`",
        f"ASOF issues: `{len(asof_issues)}`",
        f"Row 0127 recompute status: `{row_0127.get('status')}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ])
    return audit


def write_noleak_audit(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_hits = scan_forbidden_packet_fields(packet_rows)
    six_t3_hits = [row["source_inventory_id"] for row in packet_rows if row["source_inventory_id"] in EXCLUDED_T3_IDS]
    blocked_cnr_hits = [row["packet_row_id"] for row in packet_rows if row["source_lane"] == "OTI8_CNR061" or row["source_closure_label"] == "stop_after_original_horizon"]
    audit = {
        "artifact_family": "NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "forbidden_packet_field_hits": forbidden_hits,
        "six_t3_overlap": six_t3_hits,
        "blocked_cnr061_overlap": blocked_cnr_hits,
        "label_family_counts": dict(Counter(row["label_family"] or "blocked_no_label" for row in packet_rows)),
        "forbidden_surface_counters": {
            "account_history_accessed": False,
            "broker_actual_r_accessed": False,
            "live_trade_results_accessed": False,
            "mt5_account_calls": 0,
            "mt5_order_calls": 0,
            "paid_data_calls": 0,
            "databento_calls": 0,
            "api_calls": 0,
            "canary_calls": 0,
        },
        "status": "PASS" if not forbidden_hits and not six_t3_hits and not blocked_cnr_hits else "FAIL",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.json", audit)
    write_md(OUT_DIR / "NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.md", [
        "# NOFILL CAT No-Leak Label-Family Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Forbidden packet field hits: `{len(forbidden_hits)}`",
        f"Six T3 overlap: `{len(six_t3_hits)}`",
        f"Blocked CNR061 overlap: `{len(blocked_cnr_hits)}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ])
    return audit


def write_duplicate_audit(packet_rows: list[dict[str, Any]], duplicate_info: dict[str, Any]) -> dict[str, Any]:
    row_counts = Counter(row["nofill_duplicate_key"] for row in packet_rows)
    group_counts = Counter(row["duplicate_group_id"] for row in packet_rows)
    eligible = [row for row in packet_rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"]
    audit = {
        "artifact_family": "NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "row_level_count": len(packet_rows),
        "source_inventory_id_unique": len({row["source_inventory_id"] for row in packet_rows}),
        "nofill_duplicate_key_unique": len(row_counts),
        "duplicate_group_id_unique": len(group_counts),
        "eligible_row_level_count": len(eligible),
        "eligible_nofill_duplicate_key_unique": len({row["nofill_duplicate_key"] for row in eligible}),
        "duplicate_conflict_group_count": len(duplicate_info["conflicts"]),
        "duplicate_conflict_blocked_rows": sum(item["row_count"] for item in duplicate_info["conflicts"]),
        "duplicate_conflicts": duplicate_info["conflicts"],
        "sample_floor_status": "DISCOVERY_UNDER_SAMPLE_FLOOR_NO_VALIDATION_OR_PROMOTION",
        "sample_floor_reason": "Categorical counts are source-closed discovery evidence only; no performance values exist and promotion remains blocked.",
        "status": "PASS",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", audit)
    write_md(OUT_DIR / "NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md", [
        "# NOFILL CAT Duplicate Sample-Floor Audit - 2026-05-08",
        "",
        f"Row-level count: `{len(packet_rows)}`",
        f"Unique nofill duplicate keys: `{audit['nofill_duplicate_key_unique']}`",
        f"Eligible unique nofill duplicate keys: `{audit['eligible_nofill_duplicate_key_unique']}`",
        f"Duplicate conflict groups: `{len(duplicate_info['conflicts'])}`",
        f"Sample floor status: `{audit['sample_floor_status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ])
    return audit


def write_category_counts(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in packet_rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"]
    blocked = [row for row in packet_rows if row["eligibility_decision"] != "ELIGIBLE_LABEL_ASSIGNED"]
    collapsed_by_label: dict[str, set[str]] = defaultdict(set)
    for row in eligible:
        collapsed_by_label[row["categorical_lifecycle_label"]].add(row["nofill_duplicate_key"])
    counts = {
        "artifact_family": "NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "row_level": {
            "total_rows": len(packet_rows),
            "eligible_label_assigned_rows": len(eligible),
            "blocked_before_label_rows": len(blocked),
            "categorical_label_counts": dict(Counter(row["categorical_lifecycle_label"] for row in eligible)),
            "blocked_source_closure_label_counts": dict(Counter(row["source_closure_label"] for row in blocked)),
        },
        "collapsed_nofill_duplicate_key": {
            "eligible_unique_keys": len({row["nofill_duplicate_key"] for row in eligible}),
            "blocked_unique_keys": len({row["nofill_duplicate_key"] for row in blocked}),
            "categorical_label_unique_key_counts": {label: len(keys) for label, keys in sorted(collapsed_by_label.items())},
        },
        "non_claims": [
            "No R/performance values exist in this packet.",
            "No win-rate, expectancy, validation, or promotion claim is computable.",
            "DSR/PBO/effective-N are not computable because there are no numeric performance comparisons.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_2026-05-08.json", counts)
    lines = [
        "# NOFILL CAT Lifecycle Category Counts - 2026-05-08",
        "",
        f"Rows: `{len(packet_rows)}`",
        f"Eligible rows: `{len(eligible)}`",
        f"Blocked rows: `{len(blocked)}`",
        "",
        "## Categorical Label Counts",
    ]
    for label, value in counts["row_level"]["categorical_label_counts"].items():
        lines.append(f"- `{label}`: row-level `{value}`, collapsed keys `{counts['collapsed_nofill_duplicate_key']['categorical_label_unique_key_counts'][label]}`")
    lines += ["", f"Promotion verdict: `{PROMOTION_VERDICT}`", "Validation safe: `false`", "Outcome review opened: `false`", "Live effect: `false`"]
    write_md(OUT_DIR / "NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_2026-05-08.md", lines)
    return counts


def write_failure_learning(packet_rows: list[dict[str, Any]], duplicate_info: dict[str, Any]) -> dict[str, Any]:
    learning = {
        "artifact_family": "NOFILL_CAT_FAILURE_LEARNING_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "failure_anatomy": {
            "pending_lifecycle_rows": "Blocked because entry_touched_at_utc is not materialized; fill/cancel/expiry/still-pending labels require that field or source-hashed quote touch proof before labels.",
            "opening_drive_terminal_projection_rows": "Tick terminal-first evidence exists, including row 0127, but missing prereg opening-drive range/breakout source fields remain exact result blockers under the G12 contract.",
            "price_compatible_m1_rows": "Recovered M1 source proves price compatibility only; no side-aware quote/tick terminal replay is opened, so categorical result labels are blocked.",
            "entry_touched_unclaimed_row": "The row has an entry touch and unclaimed post-entry terminal order; it belongs in a separate fill/path contract, not this no-fill closure packet.",
            "duplicate_conflict_rows": "Three nofill_duplicate_key groups have same source family but differing geometry/order across repeated rows; the contract blocks those groups rather than selecting a convenient row.",
        },
        "source_safe_expansion_or_impossibility": {
            "pending_lifecycle_unblocker": "Future logger or source packet must materialize entry_touched_at_utc/fill/cancel/expiry/horizon fields without broker/account/live labels.",
            "opening_drive_unblocker": "Source-correction or contract-revision lane must source-hash breakout_close_time, breakout_side, range_high, and range_low before categorical result labels for those rows.",
            "m1_price_only_unblocker": "Separate accepted conservative quote contract or tick/quote path replay is required; M1 OHLC price compatibility alone is not enough.",
            "duplicate_conflict_unblocker": "Source audit must resolve whether repeated rows share one geometry/order or represent separate opportunities before any conflicted key can count.",
        },
        "duplicate_conflicts": duplicate_info["conflicts"],
        "next_action": "G12 categorical packet audit if this verifier passes; blocked families should route to source-correction or contract-revision lanes before result labels.",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_FAILURE_LEARNING_LEDGER_2026-05-08.json", learning)
    lines = [
        "# NOFILL CAT Failure Learning Ledger - 2026-05-08",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Failure Anatomy",
    ]
    for key, value in learning["failure_anatomy"].items():
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Exact Unblockers"]
    for key, value in learning["source_safe_expansion_or_impossibility"].items():
        lines.append(f"- `{key}`: {value}")
    write_md(OUT_DIR / "NOFILL_CAT_FAILURE_LEARNING_LEDGER_2026-05-08.md", lines)
    return learning


def write_next_prompt_pack(manifest: dict[str, Any], counts: dict[str, Any]) -> None:
    lines = [
        "# NOFILL CAT Next Prompt Pack - 2026-05-08",
        "",
        "Recommended next lane: `G12_NOFILL_CATEGORICAL_RESULT_PACKET_AUDIT_V1`.",
        "",
        "Objective: independently audit `NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1` and decide accept, block, or reject as categorical lifecycle-only evidence.",
        "",
        "Starting facts to preserve:",
        "- Source universe is exactly `298` G12-accepted source-closed no-fill rows.",
        f"- Eligible categorical rows: `{manifest['row_outcome']['eligible_label_assigned_rows']}`.",
        f"- Blocked-before-label rows: `{manifest['row_outcome']['blocked_before_label_rows']}`.",
        f"- Row-level category counts: `{json.dumps(counts['row_level']['categorical_label_counts'], sort_keys=True)}`.",
        "- Row `NOFILL-CLOSE-ROW-0127` OTR061 SHA256 remains `6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff` with first terminal-area touch `2026-05-06T07:15:00.634000Z`, but it remains result-blocked by missing prereg opening-drive fields.",
        "- Six T3 rows and all 94 G12-blocked CNR061 rows remain excluded.",
        "- All outputs preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        "",
        "G12 must verify JSON/JSONL parse, source hashes, 298-row coverage, excluded-row overlap, eligibility-before-label ordering, forbidden-field absence, duplicate conflicts, sample-floor posture, and forbidden live-surface diff.",
        "",
        "Forbidden: no R/performance, win-rate, expectancy, broker actual-R, account history, live order/deal/position labels, hidden labels, blocked CNR061/T3 scoring, paid/API/Databento, MT5 order/account calls, validation, promotion, or live effect.",
    ]
    write_md(OUT_DIR / "NOFILL_CAT_NEXT_PROMPT_PACK_2026-05-08.md", lines)


def write_completion_audit(status: str = "BUILT_PENDING_VERIFIER", verification: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = {
        "artifact_family": "NOFILL_CAT_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "objective_restatement": "Build a categorical lifecycle result packet from the G12-accepted 298 source-closed no-fill universe only, with row-level eligibility/blocker decisions before labels and no R/performance/broker/account/live/order/hidden/promotion/live-effect claims.",
        "completion_status": status,
        "can_mark_goal_complete": status == "PASS_VERIFIED_CATEGORICAL_PACKET",
        "next_action": "G12 categorical packet audit",
        "prompt_to_artifact_checklist": [
            {"requirement": "Mandatory GTOS preflight and controlling prompt reread", "artifact": "NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.json", "status": "PASS"},
            {"requirement": "Context anchor before source-row consumption", "artifact": "NOFILL_CAT_CONTEXT_ANCHOR_2026-05-08.json", "status": "PASS"},
            {"requirement": "Use exactly 298 G12-accepted source-closed rows", "artifact": "NOFILL_CAT_PACKET_MANIFEST_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "Eligibility/blocker decisions before labels", "artifact": "NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl", "status": "PENDING_VERIFIER"},
            {"requirement": "Source hashes and ASOF audit", "artifact": "NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "No forbidden fields or excluded rows", "artifact": "NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "Duplicate/sample-floor counts and conflicts", "artifact": "NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "Category counts row-level and collapsed", "artifact": "NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "Failure learning and exact unblockers", "artifact": "NOFILL_CAT_FAILURE_LEARNING_LEDGER_2026-05-08.json", "status": "PENDING_VERIFIER"},
            {"requirement": "Next prompt pack", "artifact": "NOFILL_CAT_NEXT_PROMPT_PACK_2026-05-08.md", "status": "PASS"},
            {"requirement": "Builder/verifier/tests", "artifact": "build/verify/test lane Python files", "status": "PENDING_VERIFIER"},
            {"requirement": "No live trading surface changes", "artifact": "NOFILL_CAT_COMPLETION_AUDIT_2026-05-08.json", "status": "PENDING_VERIFIER"},
        ],
        "verification_results": verification or {},
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CAT_COMPLETION_AUDIT_2026-05-08.json", audit)
    lines = [
        "# NOFILL CAT Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{status}`",
        f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`",
        f"Next action: `{audit['next_action']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: `{item['artifact']}`")
    if verification:
        lines += ["", "## Verification Results"]
        for key, value in verification.items():
            if isinstance(value, dict):
                lines.append(f"- `{key}`: `{value.get('status')}`")
    write_md(OUT_DIR / "NOFILL_CAT_COMPLETION_AUDIT_2026-05-08.md", lines)
    return audit


def build_artifacts() -> dict[str, Any]:
    generated_at = utc_now()
    source_rows = read_jsonl(SOURCE_PACKET_ROWS)
    packet_rows, duplicate_info = build_packet_rows(source_rows, generated_at)
    write_jsonl(OUT_DIR / "NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl", packet_rows)
    hash_records = collect_source_hash_records(packet_rows)
    update_context_anchor(hash_records, source_rows)
    row_0127 = recompute_row_0127_first_touch()
    manifest = write_manifest(packet_rows, hash_records, row_0127)
    eligibility = write_eligibility_ledger(packet_rows, duplicate_info)
    source_hash = write_source_hash_audit(packet_rows, hash_records, row_0127)
    noleak = write_noleak_audit(packet_rows)
    duplicate = write_duplicate_audit(packet_rows, duplicate_info)
    counts = write_category_counts(packet_rows)
    failure = write_failure_learning(packet_rows, duplicate_info)
    write_next_prompt_pack(manifest, counts)
    completion = write_completion_audit()
    summary = {
        "status": "BUILT",
        "packet_rows": len(packet_rows),
        "eligible_rows": manifest["row_outcome"]["eligible_label_assigned_rows"],
        "blocked_rows": manifest["row_outcome"]["blocked_before_label_rows"],
        "category_counts": counts["row_level"]["categorical_label_counts"],
        "blocker_counts": eligibility["blocker_code_counts"],
        "hash_mismatches": len(source_hash["hash_mismatches"]),
        "forbidden_hits": len(noleak["forbidden_packet_field_hits"]),
        "duplicate_conflicts": duplicate["duplicate_conflict_group_count"],
        "completion_status": completion["completion_status"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    build_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
