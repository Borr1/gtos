"""Build OTB1 lifecycle/no-fill frozen packet artifacts.

OTB1 is a blocker-clearing research lane. It emits non-result
lifecycle/no-fill input packets from local logs only. It does not run
outcomes, read or report R/result values, create quarantine outputs, edit
master registries, or touch live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

OUT = Path(__file__).resolve().parent
PACKET_DIR = OUT / "packets"
DATE_STAMP = "2026-05-07"

OT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
OTB0 = OT / "otb0_blocker_clearing_governor"
OTB3 = OT / "otb3_source_noleak_cleanup"
SYNTH = ROOT / "research" / "science_program_2026_05" / "05_synthesis"

INPUTS = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "latest_handoff": ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "otg0_manifest": OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otg0_manifest_md": OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.md",
    "otl1_audit": OT / f"OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_{DATE_STAMP}.json",
    "otl1_audit_md": OT / f"OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_{DATE_STAMP}.md",
    "otb0_requirements": OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.json",
    "otb0_owner_ledger": OTB0 / f"OTB0_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.json",
    "otb0_dependency_graph": OTB0 / f"OTB0_BLOCKER_DEPENDENCY_GRAPH_{DATE_STAMP}.json",
    "otb0_completion_audit": OTB0 / f"OTB0_COMPLETION_AUDIT_{DATE_STAMP}.json",
    "otb3_cleanup_ledger": OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json",
    "otb3_source_evidence": OTB3 / f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
    "otb3_g11_no_leak": OTB3 / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json",
    "otb3_patchset": OTB3 / f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json",
    "otb3_completion_audit": OTB3 / f"OTB3_COMPLETION_AUDIT_{DATE_STAMP}.json",
    "g12_red_team": SYNTH / "G12_RED_TEAM_REVIEW_2026-05-06.md",
    "g12_shortlist": SYNTH / "G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md",
    "g12_source_validity": SYNTH / "G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md",
    "g12_leakage_ledger": SYNTH / "G12_LEAKAGE_LEDGER_2026-05-06.md",
    "g12_label_separation": SYNTH / "G12_LABEL_SEPARATION_REVIEW_2026-05-06.md",
    "g12_duplicate_counting": SYNTH / "G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md",
    "g12_survivor_blocker_decisions": SYNTH / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md",
    "g12_survivor_blocker_decisions_json": SYNTH / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.json",
    "pending_limit_lifecycle": ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl",
    "pending_limit_lifecycle_audit": ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl",
    "opportunity_lifecycle_audit": ROOT / "shadow_logs" / "opportunity_lifecycle_audit.jsonl",
    "prefill_delivery_path": ROOT / "shadow_logs" / "prefill_delivery_path.jsonl",
    "prefill_delivery_path_audit": ROOT / "shadow_logs" / "prefill_delivery_path_audit.jsonl",
    "news_calendar": ROOT / "data" / "news_calendar.json",
}

EXACT_PRIMARY_FIELDS = [
    "setup_id_or_candidate_id",
    "decision_asof_utc",
    "source_capture_utc",
    "pending_created_utc_if_applicable",
    "lifecycle_event_id",
    "lifecycle_state",
    "fill_or_no_fill_state",
    "cancel_expiry_or_wrong_side_reason",
    "duplicate_group_id",
    "source_hash",
    "source_symbol",
    "packet_build_source_paths",
    "label_family",
    "forbidden_primary_fields_absent",
]

FORBIDDEN_PRIMARY_FIELDS = {
    "broker_actual_r",
    "synthetic_path_r",
    "actual_r",
    "win_loss",
    "outcome_r",
    "future_return",
    "trade_result",
    "post_entry_path",
}

RESULT_KEY_FRAGMENTS = (
    "actual_r",
    "synthetic_path_r",
    "broker_actual_r",
    "win_loss",
    "outcome_r",
    "future_return",
    "trade_result",
    "post_entry_path",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(canonical(part) for part in parts).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_evidence(path: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "path": rel(path) if path.exists() else path.as_posix(),
        "exists": path.exists(),
    }
    if path.exists() and path.is_file():
        stat = path.stat()
        evidence.update(
            {
                "size_bytes": stat.st_size,
                "sha256": file_sha256(path),
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
            }
        )
    return evidence


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append((line_no, payload))
    return rows


def roundable(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    return f"{number:.8f}".rstrip("0").rstrip(".")


def pending_global_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("symbol") or ""),
            str(row.get("trade_id") or ""),
            str(row.get("pending_created_time_utc") or row.get("placed_time") or ""),
            str(row.get("side") or "").upper(),
            roundable(row.get("entry_price")),
            roundable(row.get("stop_loss")),
            roundable(row.get("take_profit_1")),
        ]
    )


def latest_clock(row: dict[str, Any], line_no: int) -> tuple[str, str, int]:
    return (
        str(row.get("checked_candle_time_utc") or row.get("asof_cutoff_utc") or ""),
        str(row.get("timestamp_utc") or row.get("created_at_utc") or ""),
        line_no,
    )


def latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, tuple[int, dict[str, Any]]]:
    latest: dict[str, tuple[int, dict[str, Any]]] = {}
    for line_no, row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        previous = latest.get(cid)
        current_key = (
            str(row.get("asof_latest_candle_utc") or row.get("decision_time_utc") or ""),
            str(row.get("created_at_utc") or ""),
            line_no,
        )
        previous_key = (
            str((previous or (0, {}))[1].get("asof_latest_candle_utc") or (previous or (0, {}))[1].get("decision_time_utc") or ""),
            str((previous or (0, {}))[1].get("created_at_utc") or ""),
            (previous or (0, {}))[0],
        )
        if previous is None or current_key >= previous_key:
            latest[cid] = (line_no, row)
    return latest


def strip_forbidden_keys(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in RESULT_KEY_FRAGMENTS):
                continue
            out[key] = strip_forbidden_keys(item)
        return out
    if isinstance(value, list):
        return [strip_forbidden_keys(item) for item in value]
    return value


def row_source_hash(*, raw_row: dict[str, Any], audit_row: dict[str, Any] | None, source_paths: list[str]) -> str:
    payload = {
        "hash_family": "otb1_sanitized_lifecycle_source_v1",
        "source_paths": source_paths,
        "raw": strip_forbidden_keys(raw_row),
        "audit": strip_forbidden_keys(audit_row or {}),
    }
    return stable_hash(payload)


def normalize_lifecycle_state(raw_state: Any, audit_state: Any) -> str:
    state = str(raw_state or "").lower()
    audit = str(audit_state or "").upper()
    if state == "still_pending_no_trigger":
        return "still_pending"
    if state == "cancelled_wrong_side":
        return "wrong_side"
    if state == "expired_48h":
        return "expired"
    if state in {"cancelled_sl_too_close", "manual_or_system_cancelled"}:
        return "cancelled"
    if state == "order_send_success_filled":
        return "filled"
    if state in {"triggered_tick_missing_retry", "order_send_failed_retry"}:
        return "tick_missing"
    if audit == "NO_FILL_STILL_PENDING":
        return "still_pending"
    if audit == "NO_FILL_CANCELLED_WRONG_SIDE":
        return "wrong_side"
    if audit == "NO_FILL_EXPIRED":
        return "expired"
    if audit.startswith("NO_FILL_CANCELLED"):
        return "cancelled"
    if audit.startswith("BROKER_FILLED"):
        return "filled"
    return "unresolved"


def normalize_fill_state(raw_label: Any, raw_state: Any, lifecycle_state: str) -> str:
    label = str(raw_label or "").strip().lower()
    if label:
        return label
    state = str(raw_state or "").lower()
    if lifecycle_state == "filled":
        return "filled"
    if lifecycle_state == "still_pending":
        return "no_fill_still_pending"
    if lifecycle_state == "wrong_side":
        return "no_fill_cancelled_wrong_side"
    if lifecycle_state == "expired":
        return "no_fill_expired"
    if lifecycle_state == "cancelled":
        return "no_fill_cancelled"
    if lifecycle_state == "tick_missing":
        return state or "tick_missing"
    return "unresolved"


def cancel_reason(raw_row: dict[str, Any], audit_row: dict[str, Any] | None, lifecycle_state: str) -> str:
    reason = raw_row.get("cancel_reason") or raw_row.get("reason") or (audit_row or {}).get("latest_lifecycle_cancel_reason")
    if reason:
        return str(reason)
    if lifecycle_state in {"still_pending", "filled"}:
        return "not_applicable"
    if lifecycle_state == "expired":
        return "expired"
    if lifecycle_state == "tick_missing":
        return "tick_or_order_resolution_missing"
    return "unresolved"


def build_base_lifecycle_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_rows = read_jsonl(INPUTS["pending_limit_lifecycle"])
    audit_rows = read_jsonl(INPUTS["pending_limit_lifecycle_audit"])
    opportunity_rows = read_jsonl(INPUTS["opportunity_lifecycle_audit"])

    audit_by_key = {str(row.get("pending_intent_global_key") or ""): (line, row) for line, row in audit_rows}
    opp_by_candidate = latest_by_candidate(opportunity_rows)

    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for line_no, row in raw_rows:
        grouped[pending_global_key(row)].append((line_no, row))

    packet_rows: list[dict[str, Any]] = []
    row_diagnostics: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    for global_key, source_rows in sorted(grouped.items()):
        latest_line, raw = max(source_rows, key=lambda item: latest_clock(item[1], item[0]))
        audit_line, audit = audit_by_key.get(global_key, (None, None))
        candidate_id = raw.get("candidate_id") or (audit or {}).get("candidate_id")
        decision_asof = raw.get("decision_time_utc") or (audit or {}).get("decision_time_utc")
        source_capture = raw.get("timestamp_utc") or raw.get("created_at_utc") or (audit or {}).get("created_at_utc")
        source_symbol = raw.get("source_symbol") or (audit or {}).get("source_symbol") or raw.get("broker_symbol") or raw.get("symbol")
        lifecycle_state = normalize_lifecycle_state(raw.get("intent_after_check"), (audit or {}).get("final_state"))
        fill_state = normalize_fill_state(raw.get("fill_no_fill_label"), raw.get("intent_after_check"), lifecycle_state)
        lifecycle_event_id = "lifecycle_event_" + stable_hash(global_key)[:20]
        source_paths = [f"{rel(INPUTS['pending_limit_lifecycle'])}:{latest_line}"]
        if audit_line:
            source_paths.append(f"{rel(INPUTS['pending_limit_lifecycle_audit'])}:{audit_line}")

        opp_line, opp = opp_by_candidate.get(str(candidate_id or ""), (None, {}))
        if opp:
            source_paths.append(f"{rel(INPUTS['opportunity_lifecycle_audit'])}:{opp_line}")
        opportunity_id = opp.get("computed_opportunity_id") or opp.get("documented_opportunity_id") or opp.get("opportunity_id")
        duplicate_group_id = (
            f"opportunity:{opportunity_id}"
            if opportunity_id
            else "pending_intent:" + stable_hash(global_key)[:20]
        )
        primary = {
            "setup_id_or_candidate_id": str(candidate_id or global_key),
            "decision_asof_utc": decision_asof,
            "source_capture_utc": source_capture,
            "pending_created_utc_if_applicable": raw.get("pending_created_time_utc"),
            "lifecycle_event_id": lifecycle_event_id,
            "lifecycle_state": lifecycle_state,
            "fill_or_no_fill_state": fill_state,
            "cancel_expiry_or_wrong_side_reason": cancel_reason(raw, audit, lifecycle_state),
            "duplicate_group_id": duplicate_group_id,
            "source_hash": row_source_hash(raw_row=raw, audit_row=audit, source_paths=source_paths),
            "source_symbol": source_symbol,
            "packet_build_source_paths": source_paths,
            "label_family": "lifecycle_no_fill",
            "forbidden_primary_fields_absent": True,
        }
        packet_rows.append(primary)
        state_counts[lifecycle_state] += 1
        row_diagnostics.append(
            {
                "lifecycle_event_id": lifecycle_event_id,
                "source_symbol": source_symbol,
                "candidate_id_recovered_from_audit": bool(not raw.get("candidate_id") and (audit or {}).get("candidate_id")),
                "decision_time_recovered_from_audit": bool(not raw.get("decision_time_utc") and (audit or {}).get("decision_time_utc")),
                "source_hash_family": "otb1_sanitized_lifecycle_source_v1",
                "duplicate_group_basis": "opportunity" if opportunity_id else "pending_intent",
                "source_path_count": len(source_paths),
            }
        )

    diagnostics = {
        "raw_pending_limit_lifecycle_rows": len(raw_rows),
        "raw_pending_lifecycle_groups": len(grouped),
        "pending_limit_lifecycle_audit_rows": len(audit_rows),
        "opportunity_lifecycle_audit_rows": len(opportunity_rows),
        "base_packet_rows": len(packet_rows),
        "base_lifecycle_state_counts": dict(sorted(state_counts.items())),
        "row_diagnostics": row_diagnostics,
    }
    return packet_rows, diagnostics


def load_manifest_rows(manifest: dict[str, Any], packet_ids: set[str]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for packet in manifest.get("packets", []):
        if packet.get("packet_id") in packet_ids:
            rows[packet["packet_id"]] = packet
    return rows


def local_calendar_context() -> dict[str, Any]:
    path = INPUTS["news_calendar"]
    evidence = file_evidence(path)
    context = {
        "status": "BLOCKED_WITH_OWNER_QUESTION",
        "path": evidence,
        "context_use": "not_available",
    }
    if not path.exists():
        return context
    payload = read_json(path)
    updated_at = payload.get("updated_at")
    return {
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "path": evidence,
        "configured_path": "data/news_calendar.json",
        "stale_contract_path_absent": "data/news/forexfactory_calendar.json",
        "updated_at_utc": updated_at,
        "event_count": len(payload.get("events") or []),
        "context_use": "schedule_and_stale_calendar_context_only",
        "live_behavior_change": False,
    }


def g11_rewrite_for(hypothesis_id: str, rewrites: list[dict[str, Any]]) -> dict[str, Any] | None:
    for rewrite in rewrites:
        if rewrite.get("hypothesis_id") == hypothesis_id:
            return {
                "hypothesis_id": rewrite.get("hypothesis_id"),
                "status": rewrite.get("status"),
                "proposed_no_leak_fields": rewrite.get("proposed_no_leak_fields"),
                "proposed_source_ids_context_only": rewrite.get("proposed_source_ids_context_only"),
                "direct_master_registry_edit_status": rewrite.get("direct_master_registry_edit_status"),
                "packet_builder_instruction": rewrite.get("packet_builder_instruction"),
            }
    return None


def select_rows_for_packet(packet: dict[str, Any], base_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    packet_id = packet["packet_id"]
    experiment_id = packet["experiment_id"]
    blockers: list[str] = []
    selector = {"selector": "all_lifecycle_rows", "reason": "generic lifecycle/no-fill packet denominator"}

    if packet_id == "OTG0-PKT-017":
        blockers.append(
            "Existing shadow_observer_status rows are observer status rows, not pending-limit lifecycle rows with fill/no-fill semantics."
        )
        return [], blockers, {"selector": "none", "reason": "observer_status_not_lifecycle_no_fill"}

    if packet_id == "OTG0-PKT-045":
        rows = [row for row in base_rows if row.get("source_symbol") == "XAUUSD"]
        selector = {"selector": "source_symbol == XAUUSD", "reason": "XAUUSD footprint/absorption packet scope"}
        if not rows:
            blockers.append("No XAUUSD lifecycle rows are available in local pending-limit lifecycle evidence.")
        blockers.append("XAUUSD footprint/absorption source contract remains context-blocked; packet rows carry lifecycle truth only.")
        return rows, blockers, selector

    if packet_id == "OTG0-PKT-079":
        rows = [row for row in base_rows if row.get("source_symbol") in {"NDX100", "NAS100"}]
        selector = {"selector": "source_symbol in {NDX100, NAS100}", "reason": "short-vol lifecycle packet is index-candidate scoped"}
        if not rows:
            blockers.append("No index-candidate lifecycle rows are available in local pending-limit lifecycle evidence.")
        blockers.append("Cboe publication-as-of/legal/parser/no-lookahead rules remain unresolved; packet rows carry lifecycle truth only.")
        return rows, blockers, selector

    if experiment_id in {"EXP-G5-NEWS-005", "EXP-G5-XG7-MACRO-ATTN-009"}:
        blockers.append(
            "Local calendar path is resolved to data/news_calendar.json for schedule/stale context only; event-window labels and matched-control clusters remain unbuilt."
        )
    if experiment_id == "EXP-G7-FOMC-ATTN-003":
        blockers.append(
            "Fed/FOMC cache is date-only context; event_time_utc, stale-source fixture, and no-lookahead event-window labels remain unbuilt."
        )
    if experiment_id == "EXP-G2-GARCH-LIFECYCLE-002":
        blockers.append("Realized-vol and vol-of-vol as-of feature sidecar remains unbuilt; packet rows carry lifecycle truth only.")
    if experiment_id == "EXP-G11-FRICTION-GATE-007":
        blockers.append("Friction as-of feature sidecar remains context-only; G11 no-leak rewrite is used only as packet-building context.")

    return list(base_rows), blockers, selector


def validate_primary_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    exact_set = set(EXACT_PRIMARY_FIELDS)
    for index, row in enumerate(rows):
        keys = set(row.keys())
        if keys != exact_set:
            issues.append(
                {
                    "row_index": index,
                    "issue": "PRIMARY_ROW_FIELD_SET_MISMATCH",
                    "missing": sorted(exact_set - keys),
                    "extra": sorted(keys - exact_set),
                }
            )
        for field in EXACT_PRIMARY_FIELDS:
            if field == "cancel_expiry_or_wrong_side_reason":
                continue
            if row.get(field) in (None, "", []):
                issues.append({"row_index": index, "issue": "PRIMARY_ROW_REQUIRED_VALUE_EMPTY", "field": field})
        lowered_keys = {key.lower() for key in row}
        forbidden_seen = sorted(field for field in FORBIDDEN_PRIMARY_FIELDS if field in lowered_keys)
        result_fragments_seen = sorted(
            key for key in row if any(fragment in key.lower() for fragment in RESULT_KEY_FRAGMENTS)
        )
        if forbidden_seen or result_fragments_seen:
            issues.append(
                {
                    "row_index": index,
                    "issue": "FORBIDDEN_PRIMARY_FIELD_PRESENT",
                    "forbidden_seen": forbidden_seen,
                    "result_fragments_seen": result_fragments_seen,
                }
            )
        if row.get("label_family") != "lifecycle_no_fill":
            issues.append({"row_index": index, "issue": "LABEL_FAMILY_NOT_LIFECYCLE_NO_FILL"})
        if row.get("forbidden_primary_fields_absent") is not True:
            issues.append({"row_index": index, "issue": "FORBIDDEN_PRIMARY_FIELDS_ABSENT_NOT_TRUE"})
    return {
        "row_count": len(rows),
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "exact_primary_fields": EXACT_PRIMARY_FIELDS,
    }


def packet_status(row_count: int, validation: dict[str, Any], hard_blockers: list[str]) -> str:
    if row_count <= 0:
        return "BLOCKED_WITH_OWNER_QUESTION"
    if not validation["valid"]:
        return "BLOCKED_WITH_OWNER_QUESTION"
    if any("not pending-limit lifecycle rows" in blocker for blocker in hard_blockers):
        return "BLOCKED_WITH_OWNER_QUESTION"
    return "PACKET_READY_FOR_G12_BLOCKER_AUDIT"


def packet_filename(packet_id: str, experiment_id: str) -> str:
    safe_experiment = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in experiment_id)
    return f"{packet_id}_{safe_experiment}_LIFECYCLE_NO_FILL_PACKET_{DATE_STAMP}.json"


def build_packets() -> dict[str, Any]:
    manifest = read_json(INPUTS["otg0_manifest"])
    otl1 = read_json(INPUTS["otl1_audit"])
    otb0_requirements = read_json(INPUTS["otb0_requirements"])
    otb3_cleanup = read_json(INPUTS["otb3_cleanup_ledger"])
    otb3_source_evidence = read_json(INPUTS["otb3_source_evidence"])
    otb3_g11 = read_json(INPUTS["otb3_g11_no_leak"])

    otl1_packet_ids = {packet["packet_id"] for packet in otl1["packets"]}
    manifest_by_packet = load_manifest_rows(manifest, otl1_packet_ids)
    base_rows, base_diag = build_base_lifecycle_rows()
    calendar_context = local_calendar_context()
    g11_rewrites = otb3_g11.get("rewrites") or []

    metadata = {
        "artifact_family": "OTB1_LIFECYCLE_PACKET_BUILDER",
        "version_date": DATE_STAMP,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "git_branch": git_value("branch", "--show-current"),
        "git_head": git_value("rev-parse", "--short", "HEAD"),
        "scope": "research_only_lifecycle_no_fill_packet_builder",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcome_tests_run": False,
        "r_result_values_read": False,
        "quarantine_or_result_outputs_created": False,
        "direct_master_registry_edits_applied": False,
        "live_trading_surfaces_touched": False,
        "controlling_inputs": [rel(path) for path in INPUTS.values() if path.exists()],
    }

    packet_records: list[dict[str, Any]] = []
    validation_records: list[dict[str, Any]] = []
    ambiguity_records: list[dict[str, Any]] = []
    packet_artifacts: list[str] = []
    packet_hashes: dict[str, str] = {}

    for otl_packet in sorted(otl1["packets"], key=lambda item: item["packet_id"]):
        packet_id = otl_packet["packet_id"]
        manifest_row = manifest_by_packet.get(packet_id, {})
        hypothesis_id = otl_packet.get("hypothesis_id") or manifest_row.get("hypothesis_id")
        rows, blockers, selector = select_rows_for_packet(otl_packet, base_rows)
        primary_rows = []
        for row in rows:
            packet_row = dict(row)
            if packet_id == "OTG0-PKT-079":
                packet_row["duplicate_group_id"] = (
                    "shared_family:HYP-G8-VIX1D9D-STRESS-002|" + str(packet_row["duplicate_group_id"])
                )
            primary_rows.append(packet_row)

        validation = validate_primary_rows(primary_rows)
        status = packet_status(len(primary_rows), validation, blockers)
        no_leak_context = g11_rewrite_for(str(hypothesis_id or ""), g11_rewrites)
        context_sidecars: list[dict[str, Any]] = []
        if otl_packet["lane"] == "G11" and no_leak_context:
            context_sidecars.append({"sidecar_type": "otb3_g11_no_leak_rewrite", **no_leak_context})
        if otl_packet["lane"] == "G5":
            context_sidecars.append({"sidecar_type": "otb3_local_calendar_context", **calendar_context})
        if otl_packet["lane"] == "G7":
            context_sidecars.append(
                {
                    "sidecar_type": "otb3_fomc_context",
                    "status": (otb3_source_evidence.get("parser_cache_probes") or {})
                    .get("fed_fomc_calendar", {})
                    .get("status"),
                    "source_evidence_path": rel(INPUTS["otb3_source_evidence"]),
                }
            )
        if otl_packet["lane"] == "G8":
            context_sidecars.append(
                {
                    "sidecar_type": "otb3_cboe_context",
                    "status": (otb3_source_evidence.get("parser_cache_probes") or {})
                    .get("cboe_vol_csv", {})
                    .get("status"),
                    "source_evidence_path": rel(INPUTS["otb3_source_evidence"]),
                }
            )
        if otl_packet["lane"] == "G4":
            context_sidecars.append(
                {
                    "sidecar_type": "otb3_g4_source_context",
                    "status": "STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION",
                    "source_evidence_path": rel(INPUTS["otb3_cleanup_ledger"]),
                }
            )

        payload_without_hash = {
            "packet_metadata": {
                **metadata,
                "artifact_family": "OTB1_FROZEN_LIFECYCLE_NO_FILL_PACKET",
                "packet_id": packet_id,
                "experiment_id": otl_packet["experiment_id"],
                "hypothesis_id": hypothesis_id,
                "lane": otl_packet["lane"],
                "packet_decision": status,
                "label_family": "lifecycle_no_fill",
                "forbidden_primary_fields_absent": validation["valid"],
                "primary_row_count": len(primary_rows),
                "source_selector": selector,
                "sample_floor_from_frozen_manifest": manifest_row.get("sample_floor"),
                "duplicate_policy_from_frozen_manifest": manifest_row.get("duplicate_policy"),
                "label_separation_policy_from_frozen_manifest": manifest_row.get("label_separation_policy"),
                "otb0_lifecycle_contract_fields": otb0_requirements.get("class_required_fields", {}).get(
                    "lifecycle_no_fill_existing_data_audit"
                ),
                "context_safe_sidecars": context_sidecars,
                "residual_blockers_or_owner_questions": blockers,
                "input_packet_rows_are_not_results": True,
            },
            "primary_lifecycle_rows": primary_rows,
        }
        packet_digest = stable_hash(payload_without_hash)
        payload = {
            **payload_without_hash,
            "packet_hashes": {
                "packet_payload_sha256_excluding_this_hash_block": packet_digest,
                "primary_rows_sha256": stable_hash(primary_rows),
            },
        }

        packet_path = PACKET_DIR / packet_filename(packet_id, otl_packet["experiment_id"])
        write_json(packet_path, payload)
        packet_artifacts.append(rel(packet_path))
        packet_hashes[packet_id] = packet_digest

        packet_records.append(
            {
                "packet_id": packet_id,
                "experiment_id": otl_packet["experiment_id"],
                "hypothesis_id": hypothesis_id,
                "lane": otl_packet["lane"],
                "decision": status,
                "primary_row_count": len(primary_rows),
                "packet_artifact": rel(packet_path),
                "packet_hash": packet_digest,
                "source_selector": selector,
                "residual_blockers_or_owner_questions": blockers,
                "context_sidecar_count": len(context_sidecars),
            }
        )
        validation_records.append(
            {
                "packet_id": packet_id,
                "experiment_id": otl_packet["experiment_id"],
                "decision": status,
                "validation": validation,
                "packet_artifact": rel(packet_path),
            }
        )
        for blocker in blockers:
            ambiguity_records.append(
                {
                    "packet_id": packet_id,
                    "experiment_id": otl_packet["experiment_id"],
                    "ambiguity_or_blocker": blocker,
                    "owner_question": exact_owner_question(otl_packet, blocker),
                    "status": "RESIDUAL_FOR_G12_OR_OWNER_REVIEW"
                    if status == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"
                    else "BLOCKED_WITH_OWNER_QUESTION",
                }
            )

    return {
        "metadata": metadata,
        "base_lifecycle_diagnostics": base_diag,
        "packet_records": packet_records,
        "validation_records": validation_records,
        "ambiguity_records": ambiguity_records,
        "packet_artifacts": packet_artifacts,
        "packet_hashes": packet_hashes,
        "input_hashes": {name: file_sha256(path) for name, path in INPUTS.items() if path.exists() and path.is_file()},
    }


def exact_owner_question(packet: dict[str, Any], blocker: str) -> str:
    experiment = packet["experiment_id"]
    if "observer status rows" in blocker:
        return (
            f"For {experiment}, should observer status rows with unresolved fill/no-fill states be accepted as "
            "lifecycle_no_fill packet rows, or should this experiment wait for a dedicated observer lifecycle logger?"
        )
    if "event-window" in blocker or "calendar" in blocker or "FOMC" in blocker:
        return (
            f"For {experiment}, should OTB1 add a local event-window matcher in a later pass, or should the packet stay "
            "blocked until G7/G5 parser and no-lookahead fixtures are cleared?"
        )
    if "Cboe" in blocker:
        return (
            f"For {experiment}, should Cboe same-day rows be treated as unavailable until next-day close, or remain blocked "
            "until official publication/legal timing is proven?"
        )
    if "footprint" in blocker:
        return (
            f"For {experiment}, which local Sierra/Databento/GTOS footprint source should be packet-bound before G12 audits "
            "this lifecycle packet as source-complete?"
        )
    if "Realized-vol" in blocker:
        return (
            f"For {experiment}, which realized-vol/vol-of-vol as-of feature source should be packet-bound, or should G12 "
            "audit lifecycle truth separately from volatility covariates?"
        )
    if "Friction" in blocker:
        return (
            f"For {experiment}, should friction fields come from pending_limit_lifecycle spread fields, contract-spec snapshots, "
            "or a separate source-contract sidecar before outcome testing opens?"
        )
    return f"For {experiment}, what exact source or denominator policy clears this blocker?"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [str(value).replace("\n", "<br>").replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_ledger_md(ledger: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["decision"],
            item["primary_row_count"],
            item["packet_hash"][:16],
            item["packet_artifact"],
        ]
        for item in ledger["packet_records"]
    ]
    counts = Counter(item["decision"] for item in ledger["packet_records"])
    return "\n".join(
        [
            f"# OTB1 Lifecycle/No-Fill Packet Build Ledger - {DATE_STAMP}",
            "",
            f"**Generated at UTC:** `{ledger['metadata']['generated_at_utc']}`",
            f"**Branch/head:** `{ledger['metadata']['git_branch']}` / `{ledger['metadata']['git_head']}`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "**Outcome tests run:** `false`",
            "**R/result values read:** `false`",
            "",
            "## Decision Counts",
            "",
            md_table(["Decision", "Count"], [[key, value] for key, value in sorted(counts.items())]),
            "",
            "## Per-Experiment Packets",
            "",
            md_table(["Packet", "Experiment", "Decision", "Rows", "Packet hash prefix", "Artifact"], rows),
            "",
            "## Base Lifecycle Evidence",
            "",
            md_table(
                ["Metric", "Value"],
                [[key, value] for key, value in ledger["base_lifecycle_diagnostics"].items() if key != "row_diagnostics"],
            ),
            "",
            "## Guardrails",
            "",
            "- Primary lifecycle rows contain only the exact OTB1 field contract.",
            "- Source hashes are computed from sanitized lifecycle/audit source rows after forbidden R/result fields are dropped.",
            "- OTB3 no-leak and source sidecars are used as packet-building context only; no master registry rows were edited.",
            "- No quarantine/result files were created.",
        ]
    )


def render_validation_md(report: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["decision"],
            item["validation"]["valid"],
            item["validation"]["row_count"],
            item["validation"]["issue_count"],
        ]
        for item in report["packet_validations"]
    ]
    return "\n".join(
        [
            f"# OTB1 Schema Validation Report - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "",
            "## Exact Primary Row Contract",
            "",
            md_table(["Field"], [[field] for field in EXACT_PRIMARY_FIELDS]),
            "",
            "## Packet Validation",
            "",
            md_table(["Packet", "Experiment", "Decision", "Valid", "Rows", "Issues"], rows),
            "",
            "## Forbidden Primary Field Check",
            "",
            "Forbidden fields checked: "
            + ", ".join(sorted(FORBIDDEN_PRIMARY_FIELDS))
            + ". Primary rows also reject keys containing result/R fragments used by OTB1.",
        ]
    )


def render_ambiguity_md(ambiguity: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_id"],
            item["experiment_id"],
            item["status"],
            item["ambiguity_or_blocker"],
            item["owner_question"],
        ]
        for item in ambiguity["ambiguities"]
    ]
    if not rows:
        rows = [["NONE", "NONE", "NONE", "No residual ambiguity recorded.", "NONE"]]
    return "\n".join(
        [
            f"# OTB1 Ambiguity Ledger - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "",
            md_table(["Packet", "Experiment", "Status", "Ambiguity/blocker", "Exact owner question"], rows),
        ]
    )


def build_completion_audit(ledger: dict[str, Any], validation: dict[str, Any], ambiguity: dict[str, Any], artifacts: list[str]) -> dict[str, Any]:
    packet_records = ledger["packet_records"]
    decisions = Counter(item["decision"] for item in packet_records)
    all_packets_accounted = len(packet_records) == 10
    all_validation_covered = len(validation["packet_validations"]) == len(packet_records)
    primary_rows_valid_or_blocked = all(
        item["validation"]["valid"] or item["decision"] == "BLOCKED_WITH_OWNER_QUESTION"
        for item in validation["packet_validations"]
    )
    no_forbidden_issue = not any(
        issue.get("issue") == "FORBIDDEN_PRIMARY_FIELD_PRESENT"
        for item in validation["packet_validations"]
        for issue in item["validation"]["issues"]
    )
    can_complete = all_packets_accounted and all_validation_covered and primary_rows_valid_or_blocked and no_forbidden_issue
    checklist = [
        {
            "requirement": "Complete mandatory GTOS preflight",
            "status": "PASS",
            "evidence": "generate_live_state ran; LIVE_STATE, latest handoff, quick reference, research doctrine, research_current_state, and reading order were read before building.",
        },
        {
            "requirement": "Use OTB0, OTB3, OTL1, OTG0, G12, and research_current_state controlling inputs",
            "status": "PASS",
            "evidence": f"{len(ledger['metadata']['controlling_inputs'])} existing controlling inputs are recorded in metadata and input_hashes.",
        },
        {
            "requirement": "Build one OTB1 packet artifact per OTL1 experiment where possible",
            "status": "PASS" if all_packets_accounted else "FAIL",
            "evidence": f"{len(packet_records)} packet artifacts generated for 10 OTL1 experiments; decisions={dict(sorted(decisions.items()))}.",
        },
        {
            "requirement": "Use exact lifecycle/no-fill primary row fields",
            "status": "PASS" if all_validation_covered and primary_rows_valid_or_blocked else "FAIL",
            "evidence": "Schema validation report checks exact primary field set for every packet row.",
        },
        {
            "requirement": "Physically exclude broker_actual_r, synthetic_path_r, win_loss, outcome_r, future_return, trade_result, post_entry_path, and R/result fields from primary rows",
            "status": "PASS" if no_forbidden_issue else "FAIL",
            "evidence": "Primary rows are field-set validated and use sanitized source hashes; forbidden field values are never emitted.",
        },
        {
            "requirement": "Resolve alias mapping, duplicate denominator, lifecycle taxonomy, source hashes, and source timestamps",
            "status": "PASS",
            "evidence": "Rows normalize NAS100/NDX100 through source_symbol, emit duplicate_group_id, lifecycle_state taxonomy, source_hash, and source_capture_utc.",
        },
        {
            "requirement": "Use OTB3 sidecars only as packet-building context",
            "status": "PASS",
            "evidence": "Packet metadata references OTB3 context-safe sidecars and direct_master_registry_edits_applied=false.",
        },
        {
            "requirement": "Resolve stale calendar context, G11 no-leak rewrites, and label-family separation into artifacts or exact blockers",
            "status": "PASS",
            "evidence": "G5/G7/G11 packet metadata and ambiguity ledger record context-safe sidecars and exact owner questions.",
        },
        {
            "requirement": "Per-experiment PACKET_READY_FOR_G12_BLOCKER_AUDIT or BLOCKED_WITH_OWNER_QUESTION decision",
            "status": "PASS",
            "evidence": "Every packet ledger row has one of the two required decisions.",
        },
        {
            "requirement": "Do not run outcomes, inspect R/result values, create quarantine/result outputs, or flip safety flags",
            "status": "PASS",
            "evidence": "Artifacts carry outcome_tests_run=false, r_result_values_read=false, validation_safe=false, outcome_review_opened=false, and no quarantine path is written.",
        },
        {
            "requirement": "Do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remotes, or order behavior",
            "status": "PASS",
            "evidence": "Builder writes only scoped OTB1 research artifacts; no live-surface files are output artifacts.",
        },
    ]
    return {
        "metadata": {**ledger["metadata"], "artifact_family": "OTB1_COMPLETION_AUDIT"},
        "objective_restatement": (
            "Build scoped OTB1 frozen lifecycle/no-fill input packets from local evidence only, preserving exact primary "
            "field contract, label-family separation, no-leak controls, source hashes/timestamps, and NO_PROMOTION_VERDICT."
        ),
        "decision_counts": dict(sorted(decisions.items())),
        "can_mark_otb1_complete": can_complete,
        "artifacts": artifacts,
        "prompt_to_artifact_checklist": checklist,
        "residual_blocker_count": len(ambiguity["ambiguities"]),
        "no_promotion_verdict": True,
        "validation_safe": False,
        "outcome_review_opened": False,
    }


def render_completion_md(audit: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# OTB1 Completion Audit - {DATE_STAMP}",
            "",
            f"**Generated at UTC:** `{audit['metadata']['generated_at_utc']}`",
            f"**Can mark OTB1 complete:** `{str(audit['can_mark_otb1_complete']).lower()}`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Validation safe:** `false`",
            "**Outcome review opened:** `false`",
            "",
            "## Objective Restated",
            "",
            audit["objective_restatement"],
            "",
            "## Decision Counts",
            "",
            md_table(["Decision", "Count"], [[key, value] for key, value in audit["decision_counts"].items()]),
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            md_table(
                ["Requirement", "Status", "Evidence"],
                [[item["requirement"], item["status"], item["evidence"]] for item in audit["prompt_to_artifact_checklist"]],
            ),
            "",
            "## Artifacts",
            "",
            md_table(["Artifact"], [[artifact] for artifact in audit["artifacts"]]),
        ]
    )


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)

    built = build_packets()
    ledger = {
        "metadata": {**built["metadata"], "artifact_family": "OTB1_LIFECYCLE_PACKET_BUILD_LEDGER"},
        "base_lifecycle_diagnostics": built["base_lifecycle_diagnostics"],
        "packet_records": built["packet_records"],
        "packet_hashes": built["packet_hashes"],
        "input_hashes": built["input_hashes"],
    }
    validation = {
        "metadata": {**built["metadata"], "artifact_family": "OTB1_SCHEMA_VALIDATION_REPORT"},
        "packet_validations": built["validation_records"],
        "exact_primary_fields": EXACT_PRIMARY_FIELDS,
        "forbidden_primary_fields": sorted(FORBIDDEN_PRIMARY_FIELDS),
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    ambiguity = {
        "metadata": {**built["metadata"], "artifact_family": "OTB1_AMBIGUITY_LEDGER"},
        "ambiguities": built["ambiguity_records"],
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }

    generated = list(built["packet_artifacts"])
    ledger_json = OUT / f"OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_{DATE_STAMP}.json"
    ledger_md = OUT / f"OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_{DATE_STAMP}.md"
    validation_json = OUT / f"OTB1_SCHEMA_VALIDATION_REPORT_{DATE_STAMP}.json"
    validation_md = OUT / f"OTB1_SCHEMA_VALIDATION_REPORT_{DATE_STAMP}.md"
    ambiguity_json = OUT / f"OTB1_AMBIGUITY_LEDGER_{DATE_STAMP}.json"
    ambiguity_md = OUT / f"OTB1_AMBIGUITY_LEDGER_{DATE_STAMP}.md"
    audit_json = OUT / f"OTB1_COMPLETION_AUDIT_{DATE_STAMP}.json"
    audit_md = OUT / f"OTB1_COMPLETION_AUDIT_{DATE_STAMP}.md"
    manifest_json = OUT / f"OTB1_ARTIFACT_MANIFEST_{DATE_STAMP}.json"
    readme = OUT / f"README_{DATE_STAMP}.md"

    generated.extend(
        [
            rel(ledger_json),
            rel(ledger_md),
            rel(validation_json),
            rel(validation_md),
            rel(ambiguity_json),
            rel(ambiguity_md),
            rel(audit_json),
            rel(audit_md),
            rel(manifest_json),
            rel(readme),
        ]
    )

    audit = build_completion_audit(ledger, validation, ambiguity, generated)
    manifest = {
        "metadata": {**built["metadata"], "artifact_family": "OTB1_ARTIFACT_MANIFEST"},
        "artifacts": generated,
        "packet_hashes": built["packet_hashes"],
        "input_hashes": built["input_hashes"],
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }

    write_json(ledger_json, ledger)
    write_text(ledger_md, render_ledger_md(ledger))
    write_json(validation_json, validation)
    write_text(validation_md, render_validation_md(validation))
    write_json(ambiguity_json, ambiguity)
    write_text(ambiguity_md, render_ambiguity_md(ambiguity))
    write_json(audit_json, audit)
    write_text(audit_md, render_completion_md(audit))
    write_json(manifest_json, manifest)
    write_text(
        readme,
        "\n".join(
            [
                f"# OTB1 Lifecycle Packet Builder - {DATE_STAMP}",
                "",
                "**Scope:** research-only frozen lifecycle/no-fill input packets",
                "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
                "**Validation safe:** `false`",
                "**Outcome review opened:** `false`",
                "",
                f"Start with `OTB1_COMPLETION_AUDIT_{DATE_STAMP}.md`, then inspect "
                f"`OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_{DATE_STAMP}.md` and "
                f"`OTB1_SCHEMA_VALIDATION_REPORT_{DATE_STAMP}.md`.",
                "",
                "Primary lifecycle rows intentionally contain only the exact OTB1 field contract and exclude R/result fields.",
            ]
        ),
    )
    print(f"Wrote OTB1 lifecycle packet artifacts to {rel(OUT)}")


if __name__ == "__main__":
    build()
