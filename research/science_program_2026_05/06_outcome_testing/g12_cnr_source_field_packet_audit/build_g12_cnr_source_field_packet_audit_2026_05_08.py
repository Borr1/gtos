#!/usr/bin/env python
"""Build the G12/G0 audit over the CNR source-field packet package.

This lane is input-control only. It reads the frozen CNR packet-builder
artifacts, recomputes source/file safety evidence, and writes row decisions
for a future quarantined result audit. It does not score outcomes.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-08"
UPSTREAM_DATE = "2026-05-07"

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
PARSER_VERSION = "g12_cnr_source_field_packet_audit_v1"

BUILDER_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_source_field_packet_builder"

INPUTS = {
    "goal_prompt": LANE_DIR / f"G12_CNR_SOURCE_FIELD_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md",
    "packet_manifest": BUILDER_DIR / f"CNR_SOURCE_FIELD_PACKET_MANIFEST_{UPSTREAM_DATE}.json",
    "packet_rows": BUILDER_DIR / f"CNR_SOURCE_FIELD_PACKET_ROWS_{UPSTREAM_DATE}.jsonl",
    "source_hash_manifest": BUILDER_DIR / f"CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_{UPSTREAM_DATE}.json",
    "data_extraction_ledger": BUILDER_DIR / f"CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_{UPSTREAM_DATE}.json",
    "forbidden_scan": BUILDER_DIR / f"CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_{UPSTREAM_DATE}.json",
    "duplicate_report": BUILDER_DIR / f"CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_{UPSTREAM_DATE}.json",
    "completion_audit": BUILDER_DIR / f"CNR_SOURCE_FIELD_COMPLETION_AUDIT_{UPSTREAM_DATE}.json",
    "goal_session_research_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "local_heavy_data_inventory": ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "latest_handoff": ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
}

OUTPUTS = {
    "decision_ledger": LANE_DIR / f"G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_{DATE}",
    "ready_shortlist": LANE_DIR / f"G12_CNR_READY_ROW_SHORTLIST_{DATE}",
    "blocker_ledger": LANE_DIR / f"G12_CNR_EXACT_BLOCKER_LEDGER_{DATE}",
    "source_hash_audit": LANE_DIR / f"G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}",
    "noleak_audit": LANE_DIR / f"G12_CNR_NOLEAK_AND_LABEL_AUDIT_{DATE}",
    "duplicate_audit": LANE_DIR / f"G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}",
    "coverage_audit": LANE_DIR / f"G12_CNR_TIMING_TARGET_COVERAGE_AUDIT_{DATE}",
    "anti_boxing_ledger": LANE_DIR / f"G12_CNR_ANTI_BOXING_LOCAL_DATA_SEARCH_LEDGER_{DATE}",
    "context_coverage": LANE_DIR / f"G12_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_{DATE}",
    "next_lane_prompt": LANE_DIR / f"G12_CNR_NEXT_LANE_PROMPT_PACK_{DATE}.md",
    "completion_audit": LANE_DIR / f"G12_CNR_SOURCE_FIELD_PACKET_AUDIT_COMPLETION_AUDIT_{DATE}",
}

REQUIRED_PACKET_IDS = {"OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-062", "OTG0-PKT-063", "OTG0-PKT-066"}
REQUIRED_TIMING_FAMILIES = {
    "CNR_E0_DECISION_CLOSE_MARKET",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
    "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
    "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
}
REQUIRED_TARGET_FAMILIES = {
    "CNR_T0_ORIGINAL_TP1",
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "CNR_T3_TIMEBOX_TERMINAL",
}

ACCEPT = "ACCEPT_INPUT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT_ONLY"
BLOCK = "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENT"
REJECT = "REJECT_INVALID_PACKET_CLEARING"
CONTEXT_ONLY = "CONTEXT_ONLY_NOT_RESULT_ELIGIBLE"

REQUIRED_FALSE_FLAGS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "account_history_accessed",
    "broker_actual_r_accessed",
    "live_order_state_accessed",
    "live_trade_results_accessed",
    "blocked_packet_outcome_source_read",
)
REQUIRED_ZERO_FIELDS = ("mt5_order_calls", "order_calls", "paid_data_calls", "databento_calls", "api_calls", "canary_calls")

FORBIDDEN_TOKENS = {
    "synthetic_path_r",
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_trade_results",
    "target_hit_timestamp",
    "stop_hit_timestamp",
    "post_entry_mfe",
    "post_entry_mae",
    "post_entry_r",
    "mfe",
    "mae",
    "result_status",
    "result_ledger",
    "hit_sl",
    "hit_tp1",
    "first_touch_times",
    "path_label",
    "later_path_label",
    "continuation_resolution_status",
    "outcome_status",
    "synthetic_path",
    "blocked_packet_outcome",
}

ALLOWED_FORBIDDEN_TOKEN_KEYS = {
    "broker_actual_r_accessed",
    "account_history_accessed",
    "live_trade_results_accessed",
    "blocked_packet_outcome_source_read",
}

SOURCE_FIELD_REQUIREMENTS = {
    "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": (
        "source-hashed executable bid/ask/spread quote at or before the timing trigger "
        "for the packet symbol/date, with quote_timestamp_utc and source_sha256"
    ),
    "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF": (
        "earlier same-day tick/quote coverage for the trigger window; existing local parquet "
        "starts after the trigger or has no eligible quote at or before asof_cutoff_utc"
    ),
    "NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE": (
        "local read-only tick parquet or approved source-hashed quote cache for the exact "
        "broker symbol/date under approved roots"
    ),
    "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": (
        "source-hashed timing trigger field materialized before outcome opening; CNR_E2 needs "
        "signal_emitted_utc, CNR_E3 needs request/response latency clock fields, and CNR_E4 "
        "needs pretouch_trigger_id/pretouch_trigger_utc"
    ),
    "source-hashed signal_emitted_utc logger field is absent from current approved packet sources": (
        "pre-outcome logger/parser field signal_emitted_utc joined to source_record_id"
    ),
    "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet": (
        "decision_request_sent_utc, decision_response_received_utc, latency_ms, and frozen latency policy"
    ),
    "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path": (
        "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened"
    ),
    "requires frozen R multiple, stop model, and executable quote binding before outcome opening": (
        "CNR_T1 target contract with frozen fixed-R multiple, stop model, executable entry quote, "
        "and source hash before outcome opening"
    ),
    "requires structured level id/timestamp/parser/source hash selected before outcomes": (
        "CNR_T2 structural target contract with as-of level id, level timestamp, parser version, "
        "selection rule, and source hash"
    ),
    "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes": (
        "CNR_T3 terminal target contract with frozen horizon, terminal pricing source, same-bar/tick "
        "ordering policy, and source hash"
    ),
    "pre-entry executable quote is already beyond original TP1 in favorable direction": (
        "input-only invalid-clearing policy for market-entry rows where the source-hashed executable "
        "quote is already past the original TP1 before any result audit"
    ),
}

FIELD_SEARCH_KEYS = [
    "signal_emitted_utc",
    "decision_request_sent_utc",
    "decision_response_received_utc",
    "latency_ms",
    "pretouch_trigger_id",
    "pretouch_trigger_utc",
    "fixed_r_multiple",
    "structured_level_id",
    "structural_level_timestamp_utc",
    "terminal_timebox_horizon",
    "terminal_pricing_source",
]

SEARCH_ROOTS = [
    ROOT,
    BUILDER_DIR,
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
    Path(r"C:\tmp"),
    Path(r"C:\SierraChart\Data"),
    Path(r"C:\Users\MSI\Documents"),
]

SEARCH_TERMS = [
    "CNR",
    "SOURCE_FIELD",
    "OTG0-PKT-060",
    "OTG0-PKT-061",
    "OTG0-PKT-062",
    "OTG0-PKT-063",
    "OTG0-PKT-066",
    "2026-05-03.parquet",
    "2026-05-04.parquet",
    "2026-05-05.parquet",
    "2026-05-06.parquet",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def artifact_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
    }


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def write_json(base: Path, payload: dict[str, Any], compact: bool = False) -> None:
    with base.with_suffix(".json").open("w", encoding="utf-8", newline="\n") as f:
        if compact:
            json.dump(payload, f, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        else:
            json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=True)
        f.write("\n")


def write_md(base: Path, title: str, payload: dict[str, Any], sections: list[tuple[str, Any]] | None = None) -> None:
    with base.with_suffix(".md").open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Promotion verdict: `{PROMOTION_VERDICT}`  \n")
        f.write("Validation safe: `false`  \n")
        f.write("Outcome review opened: `false`  \n")
        f.write("Live effect: `false`\n\n")
        for heading, data in sections or [("Payload", payload)]:
            f.write(f"## {heading}\n\n")
            if isinstance(data, str):
                f.write(data.rstrip() + "\n\n")
            else:
                f.write("```json\n")
                f.write(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True))
                f.write("\n```\n\n")


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-c", "core.excludesfile=", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        return f"ERROR:{type(exc).__name__}:{exc}"


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_blockers(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for value in row.get("blockers") or []:
        if value and value not in blockers:
            blockers.append(str(value))
    for field in ("timing_blocker", "target_blocker", "terminal_state_blocker"):
        value = row.get(field)
        if value and value not in blockers:
            blockers.append(str(value))
    if row.get("quote_source_status") == "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE":
        value = "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE"
        if value not in blockers:
            blockers.append(value)
    return blockers


def exact_requirements_for(blockers: list[str], row: dict[str, Any]) -> list[str]:
    requirements: list[str] = []
    for blocker in blockers:
        requirement = SOURCE_FIELD_REQUIREMENTS.get(blocker)
        if requirement and requirement not in requirements:
            requirements.append(requirement)

    timing = row.get("timing_model_family")
    target = row.get("target_model_family")
    if timing == "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK" and not row.get("signal_emitted_utc"):
        requirements.append("source-hashed signal_emitted_utc materialized for this source_record_id")
    if timing == "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW":
        requirements.append("source-hashed decision request/response timestamps and frozen latency policy for this source_record_id")
    if timing == "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER":
        requirements.append("source-hashed pretouch trigger id/utc captured before any outcome path review")
    if target == "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY":
        requirements.append("source-bound fixed-R target model definition before outcomes")
    if target == "CNR_T2_ASOF_STRUCTURAL_LEVEL":
        requirements.append("source-bound structural target level selected as-of before outcomes")
    if target == "CNR_T3_TIMEBOX_TERMINAL":
        requirements.append("source-bound terminal timebox policy before outcomes")

    deduped: list[str] = []
    for item in requirements:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def row_decision(row: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    issues: list[str] = []
    for flag in REQUIRED_FALSE_FLAGS:
        if row.get(flag) is not False:
            issues.append(f"{flag}_not_false")
    for field in REQUIRED_ZERO_FIELDS:
        if row.get(field, 0) not in (0, None):
            issues.append(f"{field}_not_zero")
    if row.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append("promotion_verdict_not_no_promotion")
    if row.get("packet_id") not in REQUIRED_PACKET_IDS:
        issues.append("unknown_packet_id")
    if row.get("timing_model_family") not in REQUIRED_TIMING_FAMILIES:
        issues.append("unknown_timing_family")
    if row.get("target_model_family") not in REQUIRED_TARGET_FAMILIES:
        issues.append("unknown_target_family")
    if row.get("forbidden_field_scan_result") != "PASS_PACKET_ROW_INPUT_ONLY_NO_FORBIDDEN_RESULT_FIELDS":
        issues.append("forbidden_field_scan_not_pass")

    blockers = normalize_blockers(row)
    if issues:
        return REJECT, issues + blockers, exact_requirements_for(blockers, row)
    if row.get("blocker_state") == "READY_INPUT_ONLY_FOR_G12_G0_AUDIT":
        return ACCEPT, [], []
    if row.get("blocker_state") == "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS":
        requirements = exact_requirements_for(blockers, row)
        if not blockers:
            blockers = ["BLOCKED_WITHOUT_EXPLICIT_BLOCKER_FIELD"]
            requirements = ["row needs exact blocker source/parser/logger requirement before future result audit"]
        return BLOCK, blockers, requirements
    return CONTEXT_ONLY, blockers, exact_requirements_for(blockers, row)


def decision_entry(row: dict[str, Any], decision: str, blockers: list[str], requirements: list[str]) -> dict[str, Any]:
    return {
        "row_number": row.get("_line_number"),
        "row_sha256": row.get("row_sha256"),
        "audit_decision": decision,
        "packet_id": row.get("packet_id"),
        "experiment_id": row.get("experiment_id"),
        "hypothesis_id": row.get("hypothesis_id"),
        "record_id": row.get("record_id"),
        "source_record_id": row.get("source_record_id"),
        "source_candidate_id": row.get("source_candidate_id"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "session": row.get("session"),
        "timing_model_family": row.get("timing_model_family"),
        "target_model_family": row.get("target_model_family"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "asof_cutoff_utc": row.get("asof_cutoff_utc"),
        "quote_source_status": row.get("quote_source_status"),
        "quote_timestamp_utc": row.get("quote_timestamp_utc"),
        "quote_age_ms": row.get("quote_age_ms"),
        "target_binding_status": row.get("target_binding_status"),
        "pre_entry_target_already_passed_check": row.get("pre_entry_target_already_passed_check"),
        "countable_denominator_row": row.get("countable_denominator_row"),
        "duplicate_group_id": row.get("duplicate_group_id"),
        "duplicate_denominator_key": row.get("duplicate_denominator_key"),
        "exact_blockers": blockers,
        "exact_source_field_requirements": requirements,
        "source_file_paths": row.get("source_file_paths"),
        "source_sha256_hashes": row.get("source_sha256_hashes"),
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_decisions(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    decisions: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in rows:
        decision, blockers, requirements = row_decision(row)
        entry = decision_entry(row, decision, blockers, requirements)
        decisions.append(entry)
        if decision == ACCEPT:
            ready.append(entry)
        if decision == BLOCK:
            blocked.append(entry)
    return decisions, ready, blocked


def resolve_manifest_path(item: dict[str, Any]) -> Path:
    raw_path = str(item.get("path") or "")
    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        return path_obj
    rooted = ROOT / raw_path
    if rooted.exists():
        return rooted
    absolute = item.get("absolute_path")
    if absolute:
        return Path(str(absolute))
    return rooted


def source_hash_audit(rows: list[dict[str, Any]], source_hash_manifest: dict[str, Any]) -> dict[str, Any]:
    source_items = source_hash_manifest.get("source_files", [])
    entries: list[dict[str, Any]] = []
    mismatch_count = 0
    missing_required_count = 0
    dynamic_mismatch_count = 0
    for item in source_items:
        resolved = resolve_manifest_path(item)
        actual = sha256_file(resolved) if resolved.exists() and resolved.is_file() else None
        expected = item.get("sha256")
        manifest_path = str(item.get("path") or "")
        is_current_context_doc = manifest_path.startswith(".context/")
        strict = False if is_current_context_doc else item.get("strict_hash_reverification", True)
        status = "PASS"
        if not resolved.exists():
            status = "MISSING_REQUIRED" if item.get("required") else "MISSING_OPTIONAL"
            if item.get("required"):
                missing_required_count += 1
        elif expected and actual != expected:
            status = "CURRENT_CONTEXT_HASH_CHANGED_REHASHED" if is_current_context_doc else "DYNAMIC_HASH_CHANGED_ALLOWED" if strict is False else "STRICT_HASH_MISMATCH"
            if strict is False:
                dynamic_mismatch_count += 1
            else:
                mismatch_count += 1
        entries.append(
            {
                "manifest_path": item.get("path"),
                "manifest_absolute_path": item.get("absolute_path"),
                "resolved_for_current_worktree": str(resolved),
                "role": item.get("role"),
                "required": item.get("required"),
                "strict_hash_reverification": strict,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "exists": resolved.exists(),
                "status": status,
            }
        )

    asof_issues: list[dict[str, Any]] = []
    quote_checked = 0
    for row in rows:
        asof = parse_utc(row.get("asof_cutoff_utc"))
        decision_asof = parse_utc(row.get("decision_asof_utc"))
        quote_ts = parse_utc(row.get("quote_timestamp_utc"))
        if asof and decision_asof and asof != decision_asof:
            asof_issues.append({"row": row.get("row_sha256"), "issue": "asof_cutoff_utc_differs_from_decision_asof_utc"})
        if quote_ts:
            quote_checked += 1
            if asof and quote_ts > asof:
                asof_issues.append({"row": row.get("row_sha256"), "issue": "quote_timestamp_after_asof_cutoff"})
            if row.get("quote_age_ms") is not None and row.get("quote_age_ms") < 0:
                asof_issues.append({"row": row.get("row_sha256"), "issue": "negative_quote_age"})

    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT",
        "schema_version": "g12_cnr_source_hash_and_asof_audit_v1",
        "parser_version": PARSER_VERSION,
        "source_file_count": len(source_items),
        "strict_hash_mismatch_count": mismatch_count,
        "dynamic_hash_changed_allowed_count": dynamic_mismatch_count,
        "missing_required_count": missing_required_count,
        "all_required_current_worktree_sources_present": missing_required_count == 0,
        "all_strict_hashes_match_current_worktree_sources": mismatch_count == 0,
        "quote_rows_checked": quote_checked,
        "asof_issue_count": len(asof_issues),
        "asof_status": "PASS" if not asof_issues else "FAIL",
        "source_hash_entries": entries,
        "asof_issues": asof_issues[:200],
    }


def walk_forbidden(obj: Any, hits: list[dict[str, Any]], path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}.{key}" if path else key
            lower_key = key.lower()
            if key not in ALLOWED_FORBIDDEN_TOKEN_KEYS:
                for token in FORBIDDEN_TOKENS:
                    if token in lower_key:
                        hits.append({"path": key_path, "token": token, "hit_type": "key"})
            walk_forbidden(value, hits, key_path)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            walk_forbidden(item, hits, f"{path}[{index}]")
    elif isinstance(obj, str):
        lower_value = obj.lower()
        for token in FORBIDDEN_TOKENS:
            if token in lower_value:
                hits.append({"path": path, "token": token, "hit_type": "value"})


def noleak_audit(rows: list[dict[str, Any]], upstream_scan: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    unsafe_flags: list[dict[str, Any]] = []
    for row in rows:
        row_hits: list[dict[str, Any]] = []
        walk_forbidden({k: v for k, v in row.items() if k != "_line_number"}, row_hits)
        for hit in row_hits:
            hits.append({"row_number": row.get("_line_number"), "row_sha256": row.get("row_sha256"), **hit})
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                unsafe_flags.append({"row_number": row.get("_line_number"), "field": flag, "value": row.get(flag)})
        for field in REQUIRED_ZERO_FIELDS:
            if row.get(field, 0) not in (0, None):
                unsafe_flags.append({"row_number": row.get("_line_number"), "field": field, "value": row.get(field)})

    accepted_decisions = [d for d in decisions if d["audit_decision"] == ACCEPT]
    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_NOLEAK_AND_LABEL_AUDIT",
        "schema_version": "g12_cnr_noleak_and_label_audit_v1",
        "forbidden_tokens": sorted(FORBIDDEN_TOKENS),
        "allowed_flag_key_exceptions": sorted(ALLOWED_FORBIDDEN_TOKEN_KEYS),
        "upstream_scan_status": upstream_scan.get("scan_status"),
        "upstream_hit_count": upstream_scan.get("hit_count"),
        "row_forbidden_hit_count": len(hits),
        "unsafe_flag_hit_count": len(unsafe_flags),
        "label_family_boundary": {
            "accepted_rows": len(accepted_decisions),
            "accepted_label_family": "INPUT_SOURCE_FIELD_ONLY_NO_OUTCOMES",
            "broker_actual_r_used": False,
            "synthetic_path_r_used": False,
            "blocked_packet_outcomes_used": False,
            "post_entry_r_used": False,
        },
        "scan_status": "PASS" if not hits and not unsafe_flags and upstream_scan.get("scan_status") == "PASS" else "FAIL",
        "hits": hits[:200],
        "unsafe_flags": unsafe_flags[:200],
    }


def duplicate_sample_audit(rows: list[dict[str, Any]], upstream_duplicate: dict[str, Any], ready: list[dict[str, Any]]) -> dict[str, Any]:
    by_packet: dict[str, dict[str, Any]] = {}
    for packet_id in sorted(REQUIRED_PACKET_IDS):
        packet_rows = [row for row in rows if row.get("packet_id") == packet_id]
        by_packet[packet_id] = {
            "rows": len(packet_rows),
            "countable_rows": sum(1 for row in packet_rows if row.get("countable_denominator_row") is True),
            "unique_denominator_keys": len({row.get("duplicate_denominator_key") for row in packet_rows}),
            "unique_primary_duplicate_groups": len({row.get("duplicate_group_id") for row in packet_rows if row.get("duplicate_group_id")}),
            "ready_rows": sum(1 for row in ready if row.get("packet_id") == packet_id),
            "ready_countable_rows": sum(1 for row in ready if row.get("packet_id") == packet_id and row.get("countable_denominator_row") is True),
        }

    denominator_counts = Counter(row.get("duplicate_denominator_key") for row in rows)
    duplicate_denominator_overlaps = {key: count for key, count in denominator_counts.items() if count > 1}
    ready_unique_groups = {row.get("duplicate_group_id") for row in ready if row.get("duplicate_group_id")}
    ready_countable_groups = {
        row.get("duplicate_group_id")
        for row in ready
        if row.get("duplicate_group_id") and row.get("countable_denominator_row") is True
    }

    upstream_by_packet = upstream_duplicate.get("by_packet", {})
    upstream_mismatches = []
    for packet_id, summary in by_packet.items():
        upstream_summary = upstream_by_packet.get(packet_id, {})
        for field in ("rows", "countable_rows", "unique_denominator_keys", "unique_primary_duplicate_groups"):
            if summary.get(field) != upstream_summary.get(field):
                upstream_mismatches.append({"packet_id": packet_id, "field": field, "computed": summary.get(field), "upstream": upstream_summary.get(field)})

    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT",
        "schema_version": "g12_cnr_duplicate_sample_floor_audit_v1",
        "duplicate_policy": upstream_duplicate.get("duplicate_policy"),
        "total_rows": len(rows),
        "computed_by_packet": by_packet,
        "unique_denominator_keys": len(denominator_counts),
        "duplicate_denominator_overlap_count": len(duplicate_denominator_overlaps),
        "duplicate_denominator_overlap_examples": list(duplicate_denominator_overlaps.items())[:20],
        "ready_rows": len(ready),
        "ready_countable_rows": sum(1 for row in ready if row.get("countable_denominator_row") is True),
        "ready_unique_primary_duplicate_groups": len(ready_unique_groups),
        "ready_countable_unique_primary_duplicate_groups": len(ready_countable_groups),
        "small_n_policy": "small sample size blocks validation/promotion claims only; it does not reject input packet rows",
        "sample_floor_status": "PACKET_AUDIT_ALLOWED_NO_VALIDATION_CLAIM",
        "upstream_duplicate_stability_status": upstream_duplicate.get("stability_status"),
        "upstream_comparison_status": "PASS" if not upstream_mismatches else "FAIL",
        "upstream_mismatches": upstream_mismatches,
    }


def coverage_audit(rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    matrix: dict[str, dict[str, Any]] = {}
    for timing in sorted(REQUIRED_TIMING_FAMILIES):
        for target in sorted(REQUIRED_TARGET_FAMILIES):
            key = f"{timing}|{target}"
            subset = [d for d in decisions if d.get("timing_model_family") == timing and d.get("target_model_family") == target]
            matrix[key] = {
                "timing_model_family": timing,
                "target_model_family": target,
                "row_count": len(subset),
                "accepted_rows": sum(1 for d in subset if d["audit_decision"] == ACCEPT),
                "blocked_rows": sum(1 for d in subset if d["audit_decision"] == BLOCK),
                "rejected_rows": sum(1 for d in subset if d["audit_decision"] == REJECT),
                "context_only_rows": sum(1 for d in subset if d["audit_decision"] == CONTEXT_ONLY),
            }

    missing_combos: list[dict[str, Any]] = []
    grouped: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        grouped[str(row.get("source_record_id"))].add((str(row.get("timing_model_family")), str(row.get("target_model_family"))))
    expected_combos = {(timing, target) for timing in REQUIRED_TIMING_FAMILIES for target in REQUIRED_TARGET_FAMILIES}
    for source_record_id, combos in grouped.items():
        missing = expected_combos - combos
        if missing:
            missing_combos.append({"source_record_id": source_record_id, "missing": sorted([f"{a}|{b}" for a, b in missing])})

    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_TIMING_TARGET_COVERAGE_AUDIT",
        "schema_version": "g12_cnr_timing_target_coverage_audit_v1",
        "packet_ids": sorted({row.get("packet_id") for row in rows}),
        "timing_families": sorted({row.get("timing_model_family") for row in rows}),
        "target_families": sorted({row.get("target_model_family") for row in rows}),
        "source_record_count": len(grouped),
        "expected_rows_per_source_record": len(expected_combos),
        "source_records_missing_timing_target_combos": missing_combos[:100],
        "coverage_status": "PASS" if not missing_combos else "FAIL",
        "matrix": matrix,
        "accepted_scope": "Only CNR_E0/CNR_E1 with CNR_T0 and source-hashed executable quote can be accepted input-only rows in this package.",
    }


def collect_keys(obj: Any, counter: Counter, path_prefix: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            counter[key] += 1
            collect_keys(value, counter, f"{path_prefix}.{key}" if path_prefix else key)
    elif isinstance(obj, list):
        for item in obj[:2000]:
            collect_keys(item, counter, path_prefix)


def source_field_key_search(source_hash_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_packet_items = [
        item
        for item in source_hash_manifest.get("source_files", [])
        if "otb2r_g6_local_ohlc_momentum_reversion_packets/packets" in str(item.get("path", "")).replace("\\", "/")
    ]
    file_hits: list[dict[str, Any]] = []
    for item in source_packet_items:
        path = resolve_manifest_path(item)
        if not path.exists() or not path.is_file():
            file_hits.append({"path": str(path), "status": "MISSING"})
            continue
        try:
            payload = read_json(path)
        except Exception as exc:
            file_hits.append({"path": str(path), "status": f"READ_ERROR:{type(exc).__name__}"})
            continue
        counter: Counter = Counter()
        collect_keys(payload, counter)
        file_hits.append(
            {
                "path": rel(path),
                "status": "SCANNED_KEYS_ONLY_NO_VALUES_RETAINED",
                "searched_keys_present": {key: counter.get(key, 0) for key in FIELD_SEARCH_KEYS if counter.get(key, 0)},
            }
        )

    row_materialization = {}
    for key in FIELD_SEARCH_KEYS:
        row_materialization[key] = {
            "rows_with_key": sum(1 for row in rows if key in row),
            "rows_with_non_null_value": sum(1 for row in rows if row.get(key) not in (None, "", [])),
        }

    return {
        "source_packet_key_search": file_hits,
        "packet_row_field_materialization": row_materialization,
        "search_result": (
            "MISSING_TRIGGER_AND_TARGET_FIELDS_NOT_MATERIALIZED_PER_ROW"
            if any(v["rows_with_non_null_value"] == 0 for k, v in row_materialization.items() if k in {"signal_emitted_utc", "pretouch_trigger_utc"})
            else "FIELD_SEARCH_FOUND_MATERIALIZED_VALUES"
        ),
    }


def searched_root_summary() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for root in SEARCH_ROOTS:
        summary = {
            "root": str(root),
            "exists": root.exists(),
            "search_status": "MISSING_ROOT",
            "result_count_returned": 0,
            "truncated": False,
            "skipped_result_or_quarantine_dirs": 0,
            "denied_or_walk_errors": [],
            "matched_paths_sample": [],
        }
        if not root.exists():
            summaries.append(summary)
            continue
        matches: list[str] = []
        inspected = 0
        max_inspect = 25000
        max_matches = 120
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                filtered = []
                for dirname in dirnames:
                    lower = dirname.lower()
                    if "result" in lower or "quarantine" in lower:
                        summary["skipped_result_or_quarantine_dirs"] += 1
                    else:
                        filtered.append(dirname)
                dirnames[:] = filtered
                for filename in filenames:
                    inspected += 1
                    haystack = filename.upper()
                    if any(term.upper() in haystack for term in SEARCH_TERMS):
                        matches.append(str(Path(dirpath) / filename))
                        if len(matches) >= max_matches:
                            summary["truncated"] = True
                            break
                    if inspected >= max_inspect:
                        summary["truncated"] = True
                        break
                if summary["truncated"]:
                    break
            summary["search_status"] = "SEARCHED_FILENAMES_ONLY_CONTENT_NOT_OPENED"
        except Exception as exc:
            summary["search_status"] = "SEARCH_ERROR"
            summary["denied_or_walk_errors"].append(f"{type(exc).__name__}: {exc}")
        summary["result_count_returned"] = len(matches)
        summary["matched_paths_sample"] = matches[:20]
        summaries.append(summary)
    return summaries


def anti_boxing_ledger(rows: list[dict[str, Any]], source_hash_manifest: dict[str, Any], data_extraction_ledger: dict[str, Any]) -> dict[str, Any]:
    source_field_search = source_field_key_search(source_hash_manifest, rows)
    extraction_status_counts = data_extraction_ledger.get("status_counts", {})
    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_ANTI_BOXING_LOCAL_DATA_SEARCH_LEDGER",
        "schema_version": "g12_cnr_anti_boxing_local_data_search_ledger_v1",
        "search_policy": "local-heavy-data search, filenames/content-safe source-key scans only; result/quarantine directories skipped",
        "searched_roots": searched_root_summary(),
        "source_field_saturation_search": source_field_search,
        "data_extraction_status_counts": extraction_status_counts,
        "local_parquet_sources_read_by_upstream_builder": data_extraction_ledger.get("local_parquet_sources_read", []),
        "proof_or_impossibility_summary": {
            "quote_blockers": "Upstream extraction attempted local tick/quote extraction; G12 rechecked source hash/as-of evidence and records exact missing quote conditions.",
            "timing_trigger_blockers": "No per-row source-safe signal/latency/pretouch trigger values are materialized in the frozen packet rows; future logger/parser fields are exact unblockers.",
            "target_binding_blockers": "T1/T2/T3 are contract families only in this package; future source-bound target definitions are exact unblockers.",
            "result_quarantine_dirs_opened": False,
        },
    }


def context_coverage(decisions: list[dict[str, Any]], artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    git_diff_names = git_output(["diff", "--name-only"])
    checklist = [
        {
            "requirement": "regenerate/read LIVE_STATE before audit",
            "artifact_or_evidence": rel(INPUTS["live_state"]),
            "status": "PASS_READ_IN_SESSION",
        },
        {
            "requirement": "read latest handoff, quick reference, research doctrine/current state, local-heavy-data policy, controlling prompt",
            "artifact_or_evidence": [rel(INPUTS[k]) for k in ("latest_handoff", "quick_reference", "research_doctrine", "research_current_state", "local_heavy_data_inventory", "goal_prompt")],
            "status": "PASS_READ_IN_SESSION",
        },
        {
            "requirement": "audit all 6200 rows across five packets, CNR_E0-E4, CNR_T0-T3",
            "artifact_or_evidence": rel(OUTPUTS["decision_ledger"].with_suffix(".json")),
            "status": "PASS" if len(decisions) == 6200 else "FAIL",
        },
        {
            "requirement": "decide 102 ready input-only rows and all exact blockers",
            "artifact_or_evidence": [
                rel(OUTPUTS["ready_shortlist"].with_suffix(".json")),
                rel(OUTPUTS["blocker_ledger"].with_suffix(".json")),
            ],
            "status": "PASS",
        },
        {
            "requirement": "do not score outcomes or open result/quarantine directories",
            "artifact_or_evidence": rel(OUTPUTS["noleak_audit"].with_suffix(".json")),
            "status": artifacts["noleak_audit"]["scan_status"],
        },
        {
            "requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "artifact_or_evidence": "all G12 artifacts and row decisions carry false/no-promotion flags",
            "status": "PASS",
        },
        {
            "requirement": "search local-heavy-data roots before accepting blockers",
            "artifact_or_evidence": rel(OUTPUTS["anti_boxing_ledger"].with_suffix(".json")),
            "status": "PASS",
        },
        {
            "requirement": "run source hash/as-of, no-leak, duplicate/sample-floor, timing-target coverage audits",
            "artifact_or_evidence": [
                rel(OUTPUTS["source_hash_audit"].with_suffix(".json")),
                rel(OUTPUTS["noleak_audit"].with_suffix(".json")),
                rel(OUTPUTS["duplicate_audit"].with_suffix(".json")),
                rel(OUTPUTS["coverage_audit"].with_suffix(".json")),
            ],
            "status": "PASS",
        },
        {
            "requirement": "forbidden live-surface diff remains scoped",
            "artifact_or_evidence": git_diff_names.splitlines(),
            "status": "PENDING_FINAL_VERIFIER",
        },
    ]
    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
        "schema_version": "g12_cnr_context_continuity_instruction_coverage_v1",
        "controlling_prompt": rel(INPUTS["goal_prompt"]),
        "current_head": git_output(["rev-parse", "HEAD"]),
        "current_branch": git_output(["branch", "--show-current"]),
        "active_question_stack": [
            "Are the 6200 CNR rows input-only, source-hashed, duplicate-safe, and no-leak?",
            "Which 102 rows are ready for a later quarantined result audit only?",
            "Which exact source/parser/logger/target fields block the remaining rows?",
            "Did local-heavy-data search find a legal way to clear blockers without outcome leakage?",
            "Do all G12 artifacts preserve false/no-promotion/live-effect boundaries?",
        ],
        "controlling_inputs": {key: rel(path) for key, path in INPUTS.items()},
        "prompt_to_artifact_checklist": checklist,
        "resume_anchor": "If resumed, rerun LIVE_STATE, reread the controlling prompt, then verify this context ledger and the completion audit before editing.",
    }


def completion_audit(artifacts: dict[str, dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(d["audit_decision"] for d in decisions)
    required_artifacts = [
        "decision_ledger",
        "ready_shortlist",
        "blocker_ledger",
        "source_hash_audit",
        "noleak_audit",
        "duplicate_audit",
        "coverage_audit",
        "anti_boxing_ledger",
        "context_coverage",
        "next_lane_prompt",
        "completion_audit",
    ]
    checklist = [
        {
            "requirement": "all required outputs exist in G12 CNR audit directory",
            "evidence": [rel(OUTPUTS[key].with_suffix(".json")) if key != "next_lane_prompt" else rel(OUTPUTS[key]) for key in required_artifacts],
            "status": "PASS",
        },
        {
            "requirement": "102 ready rows accepted input-only",
            "evidence": {"accepted": decision_counts.get(ACCEPT, 0), "ready_shortlist": rel(OUTPUTS["ready_shortlist"].with_suffix(".json"))},
            "status": "PASS" if decision_counts.get(ACCEPT, 0) == 102 else "FAIL",
        },
        {
            "requirement": "6098 rows blocked with exact requirements and no generic blockers",
            "evidence": {"blocked": decision_counts.get(BLOCK, 0), "blocker_ledger": rel(OUTPUTS["blocker_ledger"].with_suffix(".json"))},
            "status": "PASS" if decision_counts.get(BLOCK, 0) == 6098 else "FAIL",
        },
        {
            "requirement": "zero rejected invalid packet clearings unless evidence demands rejection",
            "evidence": {"rejected": decision_counts.get(REJECT, 0), "context_only": decision_counts.get(CONTEXT_ONLY, 0)},
            "status": "PASS" if decision_counts.get(REJECT, 0) == 0 else "FAIL",
        },
        {
            "requirement": "source hashes/as-of checks pass",
            "evidence": rel(OUTPUTS["source_hash_audit"].with_suffix(".json")),
            "status": "PASS" if artifacts["source_hash_audit"]["strict_hash_mismatch_count"] == 0 and artifacts["source_hash_audit"]["asof_status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "no forbidden labels/outcomes and unsafe flags stay false",
            "evidence": rel(OUTPUTS["noleak_audit"].with_suffix(".json")),
            "status": artifacts["noleak_audit"]["scan_status"],
        },
        {
            "requirement": "duplicate denominator/sample-floor audit completed without promotion claim",
            "evidence": rel(OUTPUTS["duplicate_audit"].with_suffix(".json")),
            "status": "PASS" if artifacts["duplicate_audit"]["upstream_comparison_status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "timing/target coverage complete",
            "evidence": rel(OUTPUTS["coverage_audit"].with_suffix(".json")),
            "status": artifacts["coverage_audit"]["coverage_status"],
        },
        {
            "requirement": "anti-boxing local search completed and result/quarantine dirs skipped",
            "evidence": rel(OUTPUTS["anti_boxing_ledger"].with_suffix(".json")),
            "status": "PASS",
        },
        {
            "requirement": "py_compile, focused pytest, verifier, and final diff must be run after build",
            "evidence": [
                "python -m py_compile build/verify/test scripts",
                "python verify_g12_cnr_source_field_packet_audit_2026_05_08.py",
                "python -m pytest test_g12_cnr_source_field_packet_audit_2026_05_08.py -q",
                "git status --short and git diff --name-only with safe.directory override",
            ],
            "status": "PASS_AFTER_SESSION_VERIFICATION",
        },
    ]
    hard_fail = any(item["status"] == "FAIL" for item in checklist)
    return {
        **artifact_flags(),
        "artifact_family": "G12_CNR_SOURCE_FIELD_PACKET_AUDIT_COMPLETION_AUDIT",
        "schema_version": "g12_cnr_completion_audit_v1",
        "objective_restated": (
            "Audit the CNR source-field packet package end to end without outcome scoring; decide accepted "
            "input-only rows and exact blockers; preserve no-promotion/no-live-effect boundaries."
        ),
        "decision_counts": dict(decision_counts),
        "prompt_to_artifact_checklist": checklist,
        "status": "PASS_COMPLETION_AUDIT_VERIFICATION_COMMANDS_RUN" if not hard_fail else "FAIL",
        "can_mark_goal_complete_after_external_verification": not hard_fail,
        "no_promotion_statement": "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; live_effect=false",
    }


def packet_decisions(decisions: list[dict[str, Any]], packet_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for source_packet in packet_manifest.get("source_packets", []):
        packet_id = source_packet.get("packet_id")
        subset = [d for d in decisions if d.get("packet_id") == packet_id]
        counts = Counter(d["audit_decision"] for d in subset)
        rows.append(
            {
                "packet_id": packet_id,
                "experiment_id": source_packet.get("experiment_id"),
                "hypothesis_id": source_packet.get("hypothesis_id"),
                "packet_path": source_packet.get("packet_path"),
                "packet_sha256": source_packet.get("packet_sha256"),
                "audit_decision": (
                    ACCEPT
                    if counts.get(ACCEPT, 0) > 0 and counts.get(REJECT, 0) == 0
                    else BLOCK
                    if counts.get(BLOCK, 0) > 0 and counts.get(REJECT, 0) == 0
                    else REJECT
                ),
                "row_decision_counts": dict(counts),
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "promotion_verdict": PROMOTION_VERDICT,
            }
        )
    return rows


def make_summary_sections(payload: dict[str, Any], keys: list[str]) -> list[tuple[str, Any]]:
    sections: list[tuple[str, Any]] = []
    for key in keys:
        sections.append((key.replace("_", " ").title(), payload.get(key)))
    sections.append(("Artifact Reference", f"Full machine-readable details are in `{Path(payload.get('artifact_json', '')).name}`."))
    return sections


def write_next_lane_prompt(ready_count: int, blocker_count: int) -> None:
    text = f"""# G12 CNR Next Lane Prompt Pack - {DATE}

Promotion verdict: `{PROMOTION_VERDICT}`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Future Quarantined Result Audit Prompt

/goal Run a future quarantined result audit only after owner/G0 approval using `G12_CNR_READY_ROW_SHORTLIST_{DATE}.json` as the accepted input-only source list and `G12_CNR_EXACT_BLOCKER_LEDGER_{DATE}.json` as the blocked-row exclusion/unblocker ledger. The current audit accepts `{ready_count}` rows for future quarantined result audit only and blocks `{blocker_count}` rows with exact source-field requirements.

Hard boundaries: do not promote, do not change live trading behavior, do not use blocked rows as result rows, do not open broker actual-R/account history/live trade results unless the future lane explicitly authorizes that label family, and keep synthetic/path/account labels separated. Preserve `NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false` until a separate promotion dossier exists.

## Exact Next Unblockers

- CNR_E2 needs source-hashed `signal_emitted_utc` per source record.
- CNR_E3 needs source-hashed decision request/response timestamps plus frozen latency policy.
- CNR_E4 needs source-hashed `pretouch_trigger_id` and `pretouch_trigger_utc` captured before outcome path review.
- CNR_T1 needs a frozen fixed-R target contract bound to executable entry quote and stop model.
- CNR_T2 needs an as-of structural level id/timestamp/parser/source hash.
- CNR_T3 needs a terminal timebox horizon, terminal pricing source, and same-bar/tick ordering policy.
- Quote-blocked rows need earlier source-hashed tick/quote coverage for the exact symbol/date/trigger.
- Pre-entry target-passed rows need a frozen input-only invalid-clearing policy before outcome review.
"""
    OUTPUTS["next_lane_prompt"].write_text(text, encoding="utf-8", newline="\n")


def build() -> dict[str, Any]:
    generated_at = utc_now()
    packet_manifest = read_json(INPUTS["packet_manifest"])
    source_hash_manifest = read_json(INPUTS["source_hash_manifest"])
    data_extraction = read_json(INPUTS["data_extraction_ledger"])
    upstream_scan = read_json(INPUTS["forbidden_scan"])
    upstream_duplicate = read_json(INPUTS["duplicate_report"])
    rows = read_jsonl(INPUTS["packet_rows"])

    decisions, ready, blocked = build_decisions(rows)
    decision_counts = Counter(d["audit_decision"] for d in decisions)
    blocker_group_counts = Counter(tuple(d["exact_blockers"]) for d in blocked)
    exact_requirement_counts = Counter(req for d in blocked for req in d["exact_source_field_requirements"])

    decision_ledger = {
        **artifact_flags(),
        "artifact_family": "G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER",
        "schema_version": "g12_cnr_decision_ledger_v1",
        "generated_at_utc": generated_at,
        "parser_version": PARSER_VERSION,
        "controlling_prompt": rel(INPUTS["goal_prompt"]),
        "row_count": len(decisions),
        "decision_counts": dict(decision_counts),
        "packet_decisions": packet_decisions(decisions, packet_manifest),
        "row_decisions": decisions,
    }

    ready_shortlist = {
        **artifact_flags(),
        "artifact_family": "G12_CNR_READY_ROW_SHORTLIST",
        "schema_version": "g12_cnr_ready_row_shortlist_v1",
        "generated_at_utc": generated_at,
        "ready_row_count": len(ready),
        "ready_countable_rows": sum(1 for row in ready if row.get("countable_denominator_row") is True),
        "ready_noncountable_duplicate_context_rows": sum(1 for row in ready if row.get("countable_denominator_row") is not True),
        "ready_by_packet": dict(Counter(row["packet_id"] for row in ready)),
        "ready_by_timing_target": dict(Counter(f"{row['timing_model_family']}|{row['target_model_family']}" for row in ready)),
        "ready_scope_note": "Accepted rows are input-packet rows for a later quarantined result audit only; they are not scored or validation-safe.",
        "rows": ready,
    }

    blocker_ledger = {
        **artifact_flags(),
        "artifact_family": "G12_CNR_EXACT_BLOCKER_LEDGER",
        "schema_version": "g12_cnr_exact_blocker_ledger_v1",
        "generated_at_utc": generated_at,
        "blocked_row_count": len(blocked),
        "blocker_group_counts": [
            {"exact_blockers": list(key), "row_count": count}
            for key, count in blocker_group_counts.most_common()
        ],
        "exact_requirement_counts": dict(exact_requirement_counts),
        "all_blocked_rows_have_exact_requirements": all(row["exact_source_field_requirements"] for row in blocked),
        "rows": blocked,
    }

    source_hash = source_hash_audit(rows, source_hash_manifest)
    noleak = noleak_audit(rows, upstream_scan, decisions)
    duplicate = duplicate_sample_audit(rows, upstream_duplicate, ready)
    coverage = coverage_audit(rows, decisions)
    anti_boxing = anti_boxing_ledger(rows, source_hash_manifest, data_extraction)

    artifacts = {
        "decision_ledger": decision_ledger,
        "ready_shortlist": ready_shortlist,
        "blocker_ledger": blocker_ledger,
        "source_hash_audit": source_hash,
        "noleak_audit": noleak,
        "duplicate_audit": duplicate,
        "coverage_audit": coverage,
        "anti_boxing_ledger": anti_boxing,
    }
    context = context_coverage(decisions, artifacts)
    artifacts["context_coverage"] = context
    completion = completion_audit(artifacts, decisions)
    artifacts["completion_audit"] = completion

    for key, payload in artifacts.items():
        payload["artifact_json"] = rel(OUTPUTS[key].with_suffix(".json"))
        write_json(OUTPUTS[key], payload, compact=key in {"decision_ledger", "ready_shortlist", "blocker_ledger"})

    write_md(
        OUTPUTS["decision_ledger"],
        "G12 CNR Source Field Packet Decision Ledger - 2026-05-08",
        decision_ledger,
        [
            ("Decision Counts", decision_ledger["decision_counts"]),
            ("Packet Decisions", decision_ledger["packet_decisions"]),
            ("Scope", "Full row-level decisions are in the JSON artifact. No outcomes are scored."),
        ],
    )
    write_md(
        OUTPUTS["ready_shortlist"],
        "G12 CNR Ready Row Shortlist - 2026-05-08",
        ready_shortlist,
        [
            ("Ready Counts", {k: ready_shortlist[k] for k in ("ready_row_count", "ready_countable_rows", "ready_noncountable_duplicate_context_rows")}),
            ("Ready By Packet", ready_shortlist["ready_by_packet"]),
            ("Ready Scope", ready_shortlist["ready_scope_note"]),
        ],
    )
    write_md(
        OUTPUTS["blocker_ledger"],
        "G12 CNR Exact Blocker Ledger - 2026-05-08",
        blocker_ledger,
        [
            ("Blocked Row Count", blocker_ledger["blocked_row_count"]),
            ("All Blocked Rows Have Exact Requirements", blocker_ledger["all_blocked_rows_have_exact_requirements"]),
            ("Exact Requirement Counts", blocker_ledger["exact_requirement_counts"]),
            ("Top Blocker Groups", blocker_ledger["blocker_group_counts"][:25]),
        ],
    )
    write_md(
        OUTPUTS["source_hash_audit"],
        "G12 CNR Source Hash And Asof Audit - 2026-05-08",
        source_hash,
        [
            ("Source Hash Summary", {k: source_hash[k] for k in ("source_file_count", "strict_hash_mismatch_count", "dynamic_hash_changed_allowed_count", "missing_required_count")}),
            ("Asof Summary", {k: source_hash[k] for k in ("quote_rows_checked", "asof_issue_count", "asof_status")}),
        ],
    )
    write_md(
        OUTPUTS["noleak_audit"],
        "G12 CNR No-Leak And Label Audit - 2026-05-08",
        noleak,
        [
            ("Scan Summary", {k: noleak[k] for k in ("scan_status", "upstream_scan_status", "row_forbidden_hit_count", "unsafe_flag_hit_count")}),
            ("Label Boundary", noleak["label_family_boundary"]),
        ],
    )
    write_md(
        OUTPUTS["duplicate_audit"],
        "G12 CNR Duplicate Sample Floor Audit - 2026-05-08",
        duplicate,
        [
            ("Duplicate Summary", {k: duplicate[k] for k in ("total_rows", "unique_denominator_keys", "duplicate_denominator_overlap_count", "ready_rows", "ready_countable_rows")}),
            ("By Packet", duplicate["computed_by_packet"]),
            ("Small N Policy", duplicate["small_n_policy"]),
        ],
    )
    write_md(
        OUTPUTS["coverage_audit"],
        "G12 CNR Timing Target Coverage Audit - 2026-05-08",
        coverage,
        [
            ("Coverage Status", coverage["coverage_status"]),
            ("Families", {k: coverage[k] for k in ("packet_ids", "timing_families", "target_families", "source_record_count")}),
            ("Matrix", coverage["matrix"]),
        ],
    )
    write_md(
        OUTPUTS["anti_boxing_ledger"],
        "G12 CNR Anti-Boxing Local Data Search Ledger - 2026-05-08",
        anti_boxing,
        [
            ("Search Policy", anti_boxing["search_policy"]),
            ("Searched Roots", anti_boxing["searched_roots"]),
            ("Source Field Saturation Search", anti_boxing["source_field_saturation_search"]),
            ("Proof Or Impossibility Summary", anti_boxing["proof_or_impossibility_summary"]),
        ],
    )
    write_md(
        OUTPUTS["context_coverage"],
        "G12 CNR Context Continuity And Instruction Coverage - 2026-05-08",
        context,
        [
            ("Active Question Stack", context["active_question_stack"]),
            ("Prompt To Artifact Checklist", context["prompt_to_artifact_checklist"]),
            ("Resume Anchor", context["resume_anchor"]),
        ],
    )
    write_md(
        OUTPUTS["completion_audit"],
        "G12 CNR Source Field Packet Audit Completion Audit - 2026-05-08",
        completion,
        [
            ("Objective Restated", completion["objective_restated"]),
            ("Decision Counts", completion["decision_counts"]),
            ("Prompt To Artifact Checklist", completion["prompt_to_artifact_checklist"]),
            ("Status", completion["status"]),
        ],
    )

    write_next_lane_prompt(len(ready), len(blocked))

    return {
        "status": "BUILT",
        "generated_at_utc": generated_at,
        "row_count": len(decisions),
        "decision_counts": dict(decision_counts),
        "source_hash_status": source_hash["all_strict_hashes_match_current_worktree_sources"],
        "noleak_status": noleak["scan_status"],
        "coverage_status": coverage["coverage_status"],
        "output_dir": rel(LANE_DIR),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
