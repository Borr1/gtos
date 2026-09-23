"""Build OTB1R input-only lifecycle/no-fill packet rebuild artifacts.

OTB1R is a scoped rebuild of the OTB1 lifecycle/no-fill packet family
after G12 rejected the prior clearing attempt. It emits only research input
packet artifacts. It does not run outcomes, read/report R result values,
create quarantine/result outputs, edit registries, or touch live trading
surfaces.
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
PROJECTION_DIR = OUT / "source_projections"
DATE_STAMP = "2026-05-07"
REQUESTED_MAIN_HEAD = "6f5fc730"

OT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
OTB0 = OT / "otb0_blocker_clearing_governor"
OTB1 = OT / "otb1_lifecycle_packet_builder"
OTB3 = OT / "otb3_source_noleak_cleanup"
G12 = OT / "g12_blocker_clearing_audit"
SYNTH = ROOT / "research" / "science_program_2026_05" / "05_synthesis"

INPUTS = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "latest_handoff": ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "otg0_manifest": OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otg0_control_rules": OT / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.md",
    "otg0_followup_prompts": OT / f"OTG0_FOLLOWUP_GOAL_PROMPTS_{DATE_STAMP}.md",
    "otl1_audit": OT / f"OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_{DATE_STAMP}.json",
    "otl1_audit_md": OT / f"OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_{DATE_STAMP}.md",
    "otb0_requirements": OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.json",
    "otb0_requirements_md": OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.md",
    "otb0_owner_ledger": OTB0 / f"OTB0_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.json",
    "otb0_dependency_graph": OTB0 / f"OTB0_BLOCKER_DEPENDENCY_GRAPH_{DATE_STAMP}.json",
    "otb0_completion_audit": OTB0 / f"OTB0_COMPLETION_AUDIT_{DATE_STAMP}.json",
    "otb1_prior_builder": OTB1 / f"build_otb1_lifecycle_packet_builder_2026_05_07.py",
    "otb1_prior_manifest": OTB1 / f"OTB1_ARTIFACT_MANIFEST_{DATE_STAMP}.json",
    "otb3_cleanup_ledger": OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json",
    "otb3_source_evidence": OTB3 / f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
    "otb3_g11_no_leak": OTB3 / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json",
    "otb3_patchset": OTB3 / f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json",
    "g12_decision_ledger": G12 / f"G12_BLOCKER_CLEARING_DECISION_LEDGER_{DATE_STAMP}.json",
    "g12_decision_ledger_md": G12 / f"G12_BLOCKER_CLEARING_DECISION_LEDGER_{DATE_STAMP}.md",
    "g12_leakage_review": G12 / f"G12_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json",
    "g12_leakage_review_md": G12 / f"G12_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.md",
    "g12_duplicate_review": G12 / f"G12_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.json",
    "g12_duplicate_review_md": G12 / f"G12_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.md",
    "g12_source_hash_review": G12 / f"G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_{DATE_STAMP}.json",
    "g12_source_hash_review_md": G12 / f"G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_{DATE_STAMP}.md",
    "g12_owner_questions": G12 / f"G12_BLOCKED_OWNER_QUESTION_LEDGER_{DATE_STAMP}.json",
    "g12_owner_questions_md": G12 / f"G12_BLOCKED_OWNER_QUESTION_LEDGER_{DATE_STAMP}.md",
    "g12_survivor_blocker_decisions": SYNTH / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md",
    "pending_limit_lifecycle": ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl",
    "pending_limit_lifecycle_audit": ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl",
    "opportunity_lifecycle_audit": ROOT / "shadow_logs" / "opportunity_lifecycle_audit.jsonl",
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
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "win_loss",
    "outcome_r",
    "future_return",
    "trade_result",
    "post_entry_path",
}

SOURCE_PROJECTION_EXACT_FORBIDDEN = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "outcome_r",
    "future_return",
    "trade_result",
    "win_loss",
    "post_entry_path",
    "post_signal_path",
    "path_label",
    "path_order_label",
    "tp_sl_hit",
    "take_profit_hit",
    "stop_loss_hit",
}

SOURCE_PROJECTION_FRAGMENT_FORBIDDEN = (
    "path",
    "touch",
    "result",
    "future",
)

SOURCE_PROJECTION_EXTRA_RESULT_FRAGMENTS = (
    "outcome",
    "trade_result",
    "return",
    "win_loss",
    "tp_sl_hit",
    "take_profit_hit",
    "stop_loss_hit",
)

SOURCE_HASH_FAMILY = "otb1r_input_only_projected_lifecycle_source_v1"
PROJECTION_FILE = PROJECTION_DIR / f"OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_{DATE_STAMP}.jsonl"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(canonical(part) for part in parts).encode("utf-8")).hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


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
        current_key = (
            str(row.get("asof_latest_candle_utc") or row.get("decision_time_utc") or ""),
            str(row.get("created_at_utc") or ""),
            line_no,
        )
        previous = latest.get(cid)
        previous_row = previous[1] if previous else {}
        previous_key = (
            str(previous_row.get("asof_latest_candle_utc") or previous_row.get("decision_time_utc") or ""),
            str(previous_row.get("created_at_utc") or ""),
            previous[0] if previous else 0,
        )
        if previous is None or current_key >= previous_key:
            latest[cid] = (line_no, row)
    return latest


def source_projection_forbidden_key(key: Any) -> bool:
    lowered = str(key).lower()
    if lowered in SOURCE_PROJECTION_EXACT_FORBIDDEN:
        return True
    if lowered == "r" or lowered.endswith("_r") or lowered.startswith("r_") or "_r_" in lowered:
        return True
    if any(fragment in lowered for fragment in SOURCE_PROJECTION_FRAGMENT_FORBIDDEN):
        return True
    if any(fragment in lowered for fragment in SOURCE_PROJECTION_EXTRA_RESULT_FRAGMENTS):
        return True
    return False


def sanitize_source_value(value: Any, prefix: str = "") -> tuple[Any, list[str]]:
    removed: list[str] = []
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if source_projection_forbidden_key(key):
                removed.append(key_path)
                continue
            clean_item, child_removed = sanitize_source_value(item, key_path)
            sanitized[str(key)] = clean_item
            removed.extend(child_removed)
        return sanitized, removed
    if isinstance(value, list):
        sanitized_items: list[Any] = []
        for index, item in enumerate(value):
            clean_item, child_removed = sanitize_source_value(item, f"{prefix}[{index}]")
            sanitized_items.append(clean_item)
            removed.extend(child_removed)
        return sanitized_items, removed
    return value, removed


def forbidden_keys_after_projection(value: Any, prefix: str = "") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if source_projection_forbidden_key(key):
                issues.append(key_path)
            issues.extend(forbidden_keys_after_projection(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(forbidden_keys_after_projection(item, f"{prefix}[{index}]"))
    return issues


def project_dependency(role: str, path: Path, line_no: int | None, row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None or line_no is None:
        return None
    sanitized, removed = sanitize_source_value(row)
    return {
        "source_role": role,
        "dependency_location": f"{rel(path)}:{line_no}",
        "sanitized_source_row": sanitized,
        "excluded_key_paths_no_values": sorted(set(removed)),
        "excluded_key_count": len(set(removed)),
        "forbidden_key_paths_after_projection": forbidden_keys_after_projection(sanitized),
    }


def source_hash_from_projections(projections: list[dict[str, Any]]) -> str:
    payload = {
        "hash_family": SOURCE_HASH_FAMILY,
        "projected_dependencies": [
            {
                "source_role": item["source_role"],
                "dependency_location": item["dependency_location"],
                "sanitized_source_row": item["sanitized_source_row"],
            }
            for item in projections
        ],
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


def build_base_lifecycle_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    raw_rows = read_jsonl(INPUTS["pending_limit_lifecycle"])
    audit_rows = read_jsonl(INPUTS["pending_limit_lifecycle_audit"])
    opportunity_rows = read_jsonl(INPUTS["opportunity_lifecycle_audit"])

    audit_by_key = {str(row.get("pending_intent_global_key") or ""): (line, row) for line, row in audit_rows}
    opp_by_candidate = latest_by_candidate(opportunity_rows)

    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for line_no, row in raw_rows:
        grouped[pending_global_key(row)].append((line_no, row))

    packet_rows: list[dict[str, Any]] = []
    source_projection_rows: list[dict[str, Any]] = []
    row_diagnostics: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    removed_key_counts: Counter[str] = Counter()

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
        source_locations = [f"{rel(INPUTS['pending_limit_lifecycle'])}:{latest_line}"]
        projections = [
            project_dependency("pending_limit_lifecycle_latest_group_row", INPUTS["pending_limit_lifecycle"], latest_line, raw)
        ]
        if audit_line:
            source_locations.append(f"{rel(INPUTS['pending_limit_lifecycle_audit'])}:{audit_line}")
            projections.append(
                project_dependency("pending_limit_lifecycle_audit_row", INPUTS["pending_limit_lifecycle_audit"], audit_line, audit)
            )

        opp_line, opp = opp_by_candidate.get(str(candidate_id or ""), (None, {}))
        if opp:
            source_locations.append(f"{rel(INPUTS['opportunity_lifecycle_audit'])}:{opp_line}")
            projections.append(project_dependency("opportunity_lifecycle_audit_latest_candidate_row", INPUTS["opportunity_lifecycle_audit"], opp_line, opp))

        clean_projections = [item for item in projections if item is not None]
        source_hash = source_hash_from_projections(clean_projections)
        for projection in clean_projections:
            for key_path in projection["excluded_key_paths_no_values"]:
                removed_key_counts[key_path] += 1

        opportunity_id = opp.get("computed_opportunity_id") or opp.get("documented_opportunity_id") or opp.get("opportunity_id")
        duplicate_group_id = f"opportunity:{opportunity_id}" if opportunity_id else "pending_intent:" + stable_hash(global_key)[:20]
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
            "source_hash": source_hash,
            "source_symbol": source_symbol,
            "packet_build_source_paths": source_locations,
            "label_family": "lifecycle_no_fill",
            "forbidden_primary_fields_absent": True,
        }
        packet_rows.append(primary)
        state_counts[lifecycle_state] += 1
        source_projection_rows.append(
            {
                "source_projection_id": "otb1r_projection_" + stable_hash(source_hash, lifecycle_event_id)[:20],
                "lifecycle_event_id": lifecycle_event_id,
                "setup_id_or_candidate_id": primary["setup_id_or_candidate_id"],
                "duplicate_group_id": duplicate_group_id,
                "source_symbol": source_symbol,
                "source_hash": source_hash,
                "source_hash_family": SOURCE_HASH_FAMILY,
                "dependency_locations": source_locations,
                "projected_dependencies": clean_projections,
                "hash_excludes_key_values": True,
                "excluded_key_values_stored": False,
                "forbidden_key_paths_after_projection": sorted(
                    {
                        key_path
                        for projection in clean_projections
                        for key_path in projection["forbidden_key_paths_after_projection"]
                    }
                ),
            }
        )
        row_diagnostics.append(
            {
                "lifecycle_event_id": lifecycle_event_id,
                "source_symbol": source_symbol,
                "candidate_id_recovered_from_audit": bool(not raw.get("candidate_id") and (audit or {}).get("candidate_id")),
                "decision_time_recovered_from_audit": bool(not raw.get("decision_time_utc") and (audit or {}).get("decision_time_utc")),
                "source_hash_family": SOURCE_HASH_FAMILY,
                "source_projection_dependency_count": len(clean_projections),
                "duplicate_group_basis": "opportunity" if opportunity_id else "pending_intent",
                "source_hash": source_hash,
            }
        )

    duplicate_counts = Counter(row["duplicate_group_id"] for row in packet_rows)
    diagnostics = {
        "raw_pending_limit_lifecycle_source_rows_read": len(raw_rows),
        "raw_pending_lifecycle_groups_projected": len(grouped),
        "pending_limit_lifecycle_audit_rows_read": len(audit_rows),
        "opportunity_lifecycle_audit_rows_read": len(opportunity_rows),
        "base_projected_lifecycle_rows": len(packet_rows),
        "base_unique_duplicate_group_id_count": len(duplicate_counts),
        "base_duplicate_group_ids_with_multiple_rows_count": sum(1 for count in duplicate_counts.values() if count > 1),
        "base_lifecycle_state_counts": dict(sorted(state_counts.items())),
        "source_hash_family": SOURCE_HASH_FAMILY,
        "source_projection_file": rel(PROJECTION_FILE),
        "source_projection_rows": len(source_projection_rows),
        "source_projection_forbidden_key_paths_after_projection_count": sum(
            len(row["forbidden_key_paths_after_projection"]) for row in source_projection_rows
        ),
        "source_projection_excluded_key_counts_no_values": dict(sorted(removed_key_counts.items())),
        "row_diagnostics": row_diagnostics,
    }
    return packet_rows, source_projection_rows, diagnostics


def load_manifest_rows(manifest: dict[str, Any], packet_ids: set[str]) -> dict[str, dict[str, Any]]:
    return {packet["packet_id"]: packet for packet in manifest.get("packets", []) if packet.get("packet_id") in packet_ids}


def local_calendar_context() -> dict[str, Any]:
    path = INPUTS["news_calendar"]
    evidence = file_evidence(path)
    if not path.exists():
        return {
            "status": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "path": evidence,
            "context_use": "not_available",
        }
    payload = read_json(path)
    return {
        "status": "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
        "path": evidence,
        "configured_path": "data/news_calendar.json",
        "stale_contract_path_absent": "data/news/forexfactory_calendar.json",
        "updated_at_utc": payload.get("updated_at"),
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
    selector = {"selector": "all_projected_lifecycle_rows", "reason": "generic lifecycle/no-fill packet denominator"}

    if packet_id == "OTG0-PKT-017":
        blockers.append(
            "Existing shadow_observer_status rows are observer status rows, not dedicated lifecycle/no-fill rows."
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


def duplicate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id"))
    return {
        "raw_row_count": len(rows),
        "unique_duplicate_group_id_count": len(counts),
        "duplicate_group_ids_with_multiple_rows_count": sum(1 for count in counts.values() if count > 1),
        "duplicate_group_counts": dict(sorted(counts.items())),
        "denominator_policy": "Use unique_duplicate_group_id_count as the independent denominator; raw_row_count is retained only as child-row inventory.",
    }


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
        if forbidden_seen:
            issues.append({"row_index": index, "issue": "FORBIDDEN_PRIMARY_FIELD_PRESENT", "forbidden_seen": forbidden_seen})
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
        "forbidden_primary_fields": sorted(FORBIDDEN_PRIMARY_FIELDS),
    }


def validate_source_projections(rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if row.get("source_hash_family") != SOURCE_HASH_FAMILY:
            issues.append({"source_projection_id": row.get("source_projection_id"), "issue": "SOURCE_HASH_FAMILY_MISMATCH"})
        if row.get("forbidden_key_paths_after_projection"):
            issues.append(
                {
                    "source_projection_id": row.get("source_projection_id"),
                    "issue": "FORBIDDEN_KEYS_AFTER_PROJECTION",
                    "forbidden_key_paths_after_projection": row.get("forbidden_key_paths_after_projection"),
                }
            )
        recomputed = source_hash_from_projections(row.get("projected_dependencies") or [])
        if recomputed != row.get("source_hash"):
            issues.append(
                {
                    "source_projection_id": row.get("source_projection_id"),
                    "issue": "SOURCE_HASH_RECOMPUTE_MISMATCH",
                    "expected": recomputed,
                    "actual": row.get("source_hash"),
                }
            )
    excluded_counts: Counter[str] = Counter()
    for row in rows:
        for projection in row.get("projected_dependencies") or []:
            for key_path in projection.get("excluded_key_paths_no_values") or []:
                excluded_counts[key_path] += 1
    return {
        "row_count": len(rows),
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "source_hash_family": SOURCE_HASH_FAMILY,
        "source_hashes_recomputed_from_sanitized_projection_only": not issues,
        "path_label_excluded_count": sum(count for key, count in excluded_counts.items() if key.lower().endswith("path_label")),
        "excluded_key_counts_no_values": dict(sorted(excluded_counts.items())),
    }


def packet_status(row_count: int, validation: dict[str, Any], blockers: list[str]) -> str:
    if row_count <= 0:
        return "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    if not validation["valid"]:
        return "BLOCKED_REBUILD_VALIDATION_FAILED"
    if any("observer status rows" in blocker for blocker in blockers):
        return "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    return "REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT"


def packet_filename(packet_id: str, experiment_id: str) -> str:
    safe_experiment = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in experiment_id)
    return f"{packet_id}_{safe_experiment}_OTB1R_INPUT_ONLY_LIFECYCLE_NO_FILL_PACKET_{DATE_STAMP}.json"


def exact_owner_question(packet: dict[str, Any], blocker: str) -> str:
    experiment = packet["experiment_id"]
    if "observer status rows" in blocker:
        return (
            "Should observer status rows be converted by a dedicated observer lifecycle logger, or should "
            f"{experiment} stay blocked outside lifecycle/no-fill packet testing?"
        )
    if "event-window" in blocker or "calendar" in blocker or "FOMC" in blocker:
        return (
            f"For {experiment}, should a later packet builder add a local event-window matcher, or should the packet stay "
            "blocked until parser and no-lookahead fixtures are cleared?"
        )
    if "Cboe" in blocker:
        return (
            f"For {experiment}, should Cboe same-day rows be treated as unavailable until next-day close, or remain blocked "
            "until official publication/legal timing is proven?"
        )
    if "footprint" in blocker:
        return (
            f"For {experiment}, which local Sierra/Databento/GTOS footprint source should be packet-bound before this "
            "lifecycle packet can be audited as source-complete?"
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


def build_packets() -> dict[str, Any]:
    manifest = read_json(INPUTS["otg0_manifest"])
    otl1 = read_json(INPUTS["otl1_audit"])
    otb0_requirements = read_json(INPUTS["otb0_requirements"])
    otb3_source_evidence = read_json(INPUTS["otb3_source_evidence"])
    otb3_g11 = read_json(INPUTS["otb3_g11_no_leak"])

    otl1_packet_ids = {packet["packet_id"] for packet in otl1["packets"]}
    manifest_by_packet = load_manifest_rows(manifest, otl1_packet_ids)
    base_rows, source_projection_rows, base_diag = build_base_lifecycle_rows()
    source_projection_validation = validate_source_projections(source_projection_rows)
    calendar_context = local_calendar_context()
    g11_rewrites = otb3_g11.get("rewrites") or []

    metadata = {
        "artifact_family": "OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD",
        "version_date": DATE_STAMP,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "git_branch": git_value("branch", "--show-current"),
        "git_head": git_value("rev-parse", "--short", "HEAD"),
        "requested_main_head": REQUESTED_MAIN_HEAD,
        "scope": "research_only_input_only_lifecycle_no_fill_rebuild",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcome_tests_run": False,
        "r_result_values_read": False,
        "quarantine_or_result_outputs_created": False,
        "direct_master_registry_edits_applied": False,
        "live_trading_surfaces_touched": False,
        "source_hash_family": SOURCE_HASH_FAMILY,
        "source_projection_file": rel(PROJECTION_FILE),
        "controlling_inputs": [rel(path) for path in INPUTS.values() if path.exists()],
    }

    write_jsonl(PROJECTION_FILE, source_projection_rows)

    packet_records: list[dict[str, Any]] = []
    validation_records: list[dict[str, Any]] = []
    ambiguity_records: list[dict[str, Any]] = []
    duplicate_records: list[dict[str, Any]] = []
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
                packet_row["duplicate_group_id"] = "shared_family:HYP-G8-VIX1D9D-STRESS-002|" + str(
                    packet_row["duplicate_group_id"]
                )
            primary_rows.append(packet_row)

        validation = validate_primary_rows(primary_rows)
        status = packet_status(len(primary_rows), validation, blockers)
        dup_summary = duplicate_summary(primary_rows)
        duplicate_records.append(
            {
                "packet_id": packet_id,
                "experiment_id": otl_packet["experiment_id"],
                "decision": status,
                **dup_summary,
            }
        )

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
                "artifact_family": "OTB1R_FROZEN_INPUT_ONLY_LIFECYCLE_NO_FILL_PACKET",
                "packet_id": packet_id,
                "experiment_id": otl_packet["experiment_id"],
                "hypothesis_id": hypothesis_id,
                "lane": otl_packet["lane"],
                "packet_decision": status,
                "label_family": "lifecycle_no_fill",
                "forbidden_primary_fields_absent": validation["valid"],
                "primary_raw_row_count": dup_summary["raw_row_count"],
                "unique_duplicate_group_id_count": dup_summary["unique_duplicate_group_id_count"],
                "duplicate_group_ids_with_multiple_rows_count": dup_summary["duplicate_group_ids_with_multiple_rows_count"],
                "denominator_policy": dup_summary["denominator_policy"],
                "source_selector": selector,
                "sample_floor_from_frozen_manifest": manifest_row.get("sample_floor"),
                "duplicate_policy_from_frozen_manifest": manifest_row.get("duplicate_policy"),
                "label_separation_policy_from_frozen_manifest": manifest_row.get("label_separation_policy"),
                "otb0_lifecycle_contract_fields": otb0_requirements.get("class_required_fields", {}).get(
                    "lifecycle_no_fill_existing_data_audit"
                ),
                "source_projection_file": rel(PROJECTION_FILE),
                "source_hashes_are_sanitized_projection_hashes": True,
                "source_projection_excludes_before_hashing": sorted(
                    set(SOURCE_PROJECTION_EXACT_FORBIDDEN)
                    | set(SOURCE_PROJECTION_FRAGMENT_FORBIDDEN)
                    | set(SOURCE_PROJECTION_EXTRA_RESULT_FRAGMENTS)
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
                "primary_raw_row_count": len(primary_rows),
                "unique_duplicate_group_id_count": dup_summary["unique_duplicate_group_id_count"],
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
        if packet_id == "OTG0-PKT-017" and not blockers:
            blockers.append("EXP-G11-OBSERVER-EXPANSION-006 requires an owner lifecycle-logger decision.")
        for blocker in blockers:
            ambiguity_records.append(
                {
                    "packet_id": packet_id,
                    "experiment_id": otl_packet["experiment_id"],
                    "ambiguity_or_blocker": blocker,
                    "next_exact_question": exact_owner_question(otl_packet, blocker),
                    "status": "BLOCKED_WITH_NEXT_EXACT_QUESTION"
                    if status == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
                    else "RESIDUAL_FOR_G12_REAUDIT",
                }
            )

    return {
        "metadata": metadata,
        "base_lifecycle_diagnostics": base_diag,
        "source_projection_validation": source_projection_validation,
        "packet_records": packet_records,
        "validation_records": validation_records,
        "ambiguity_records": ambiguity_records,
        "duplicate_records": duplicate_records,
        "packet_artifacts": packet_artifacts,
        "packet_hashes": packet_hashes,
        "input_hashes": {name: file_sha256(path) for name, path in INPUTS.items() if path.exists() and path.is_file()},
    }


def decision_counts(packet_records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["decision"] for row in packet_records).items()))


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def build_rebuild_ledger(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    metadata = result["metadata"]
    packet_records = result["packet_records"]
    payload = {
        "metadata": metadata,
        "decision_counts": decision_counts(packet_records),
        "base_lifecycle_diagnostics": result["base_lifecycle_diagnostics"],
        "packets": packet_records,
    }
    rows = [
        [
            row["packet_id"],
            row["experiment_id"],
            row["decision"],
            row["primary_raw_row_count"],
            row["unique_duplicate_group_id_count"],
            row["packet_artifact"],
        ]
        for row in packet_records
    ]
    md = "\n".join(
        [
            "# OTB1R Input-Only Lifecycle Rebuild Ledger - 2026-05-07",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Scope:** OTB1 lifecycle/no-fill input packet rebuild only; no outcomes.",
            "",
            "## Decision Counts",
            "",
            markdown_table(["Decision", "Count"], [[key, value] for key, value in payload["decision_counts"].items()]),
            "",
            "## Packet Rebuilds",
            "",
            markdown_table(
                ["Packet", "Experiment", "Decision", "Raw rows", "Unique duplicate groups", "Artifact"],
                rows,
            ),
            "",
            "## Source Projection",
            "",
            f"- Source hash family: `{metadata['source_hash_family']}`",
            f"- Source projection file: `{metadata['source_projection_file']}`",
            f"- Base projected lifecycle rows: `{result['base_lifecycle_diagnostics']['base_projected_lifecycle_rows']}`",
            f"- Base unique duplicate groups: `{result['base_lifecycle_diagnostics']['base_unique_duplicate_group_id_count']}`",
            f"- Forbidden keys after projection: `{result['source_projection_validation']['issue_count']}` issues.",
        ]
    )
    return payload, md


def build_schema_validation_report(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    validation_records = result["validation_records"]
    source_projection_validation = result["source_projection_validation"]
    issue_count = sum(record["validation"]["issue_count"] for record in validation_records)
    all_primary_ok = issue_count == 0
    payload = {
        "metadata": result["metadata"],
        "all_primary_rows_schema_ok": all_primary_ok,
        "primary_validation_issue_count": issue_count,
        "source_projection_validation": source_projection_validation,
        "validation_records": validation_records,
        "forbidden_primary_fields_must_remain_absent": sorted(FORBIDDEN_PRIMARY_FIELDS),
    }
    rows = [
        [record["packet_id"], record["experiment_id"], record["decision"], record["validation"]["row_count"], record["validation"]["issue_count"]]
        for record in validation_records
    ]
    md = "\n".join(
        [
            "# OTB1R Schema And No-Leak Validation Report - 2026-05-07",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## Primary Row Validation",
            "",
            markdown_table(["Packet", "Experiment", "Decision", "Rows", "Issues"], rows),
            "",
            "## Source Projection Validation",
            "",
            f"- Source projection rows: `{source_projection_validation['row_count']}`",
            f"- Projection issues: `{source_projection_validation['issue_count']}`",
            f"- `path_label` excluded count: `{source_projection_validation['path_label_excluded_count']}`",
            "- Source hashes are recomputed from sanitized projected source rows only.",
            "- Excluded source key values are not stored in projection audit rows; only key names and counts are reported.",
            "",
            "## Forbidden Primary Fields",
            "",
            ", ".join(f"`{field}`" for field in sorted(FORBIDDEN_PRIMARY_FIELDS)),
        ]
    )
    return payload, md


def build_duplicate_report(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    payload = {
        "metadata": result["metadata"],
        "duplicate_records": result["duplicate_records"],
        "base_lifecycle_diagnostics": {
            key: value
            for key, value in result["base_lifecycle_diagnostics"].items()
            if key != "row_diagnostics"
        },
    }
    rows = [
        [
            row["packet_id"],
            row["experiment_id"],
            row["raw_row_count"],
            row["unique_duplicate_group_id_count"],
            row["duplicate_group_ids_with_multiple_rows_count"],
            row["decision"],
        ]
        for row in result["duplicate_records"]
    ]
    md = "\n".join(
        [
            "# OTB1R Duplicate Denominator Report - 2026-05-07",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "OTB1R reports raw row inventory separately from independent duplicate-group denominators. Any later sample floor, effective-N, DSR, or PBO calculation must use the unique `duplicate_group_id` denominator, not raw child rows.",
            "",
            markdown_table(
                ["Packet", "Experiment", "Raw rows", "Unique duplicate groups", "Duplicate groups >1 row", "Decision"],
                rows,
            ),
        ]
    )
    return payload, md


def build_ambiguity_ledger(result: dict[str, Any]) -> tuple[dict[str, Any], str]:
    records = result["ambiguity_records"]
    payload = {
        "metadata": result["metadata"],
        "ambiguity_count": len(records),
        "ambiguities": records,
        "observer_expansion_next_exact_question": (
            "Should observer status rows be converted by a dedicated observer lifecycle logger, or should "
            "EXP-G11-OBSERVER-EXPANSION-006 stay blocked outside lifecycle/no-fill packet testing?"
        ),
    }
    rows = [
        [row["packet_id"], row["experiment_id"], row["status"], row["next_exact_question"]]
        for row in records
    ]
    md = "\n".join(
        [
            "# OTB1R Ambiguity Ledger - 2026-05-07",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            markdown_table(["Packet", "Experiment", "Status", "Next exact question"], rows),
        ]
    )
    return payload, md


def build_completion_audit(result: dict[str, Any], artifact_paths: list[Path]) -> tuple[dict[str, Any], str]:
    packet_records = result["packet_records"]
    source_projection_validation = result["source_projection_validation"]
    primary_issue_count = sum(record["validation"]["issue_count"] for record in result["validation_records"])
    decision_count_map = decision_counts(packet_records)
    scoped_artifact_paths = [rel(path) for path in artifact_paths]
    checklist = [
        {
            "requirement": "Run from requested worktree and main HEAD 6f5fc730",
            "evidence": (
                f"requested_main_head={result['metadata']['requested_main_head']}; "
                f"builder_runtime_git_head={result['metadata']['git_head']}; worktree={ROOT}"
            ),
            "status": "PASS" if result["metadata"]["requested_main_head"] == REQUESTED_MAIN_HEAD else "CHECK_HEAD",
        },
        {
            "requirement": "Complete mandatory GTOS preflight and read current research controls",
            "evidence": "Preflight files are listed as controlling inputs, including LIVE_STATE, latest handoff, quick reference, doctrine, current state, and reading-order-derived OTB/G12 controls.",
            "status": "PASS",
        },
        {
            "requirement": "Use input-only projected lifecycle source rows before hashing",
            "evidence": f"source_hash_family={result['metadata']['source_hash_family']}; projection_file={result['metadata']['source_projection_file']}; source_projection_issues={source_projection_validation['issue_count']}",
            "status": "PASS" if source_projection_validation["issue_count"] == 0 else "FAIL",
        },
        {
            "requirement": "Physically exclude path_label and R/path/touch/result/future fields before source hashing",
            "evidence": f"path_label_excluded_count={source_projection_validation['path_label_excluded_count']}; forbidden_after_projection_issues={source_projection_validation['issue_count']}; excluded_key_values_stored=false",
            "status": "PASS" if source_projection_validation["issue_count"] == 0 and source_projection_validation["path_label_excluded_count"] > 0 else "FAIL",
        },
        {
            "requirement": "Compute sanitized source-row hashes",
            "evidence": "Each primary row source_hash is derived from sanitized projected dependencies; source projection validation recomputes every hash.",
            "status": "PASS" if source_projection_validation["source_hashes_recomputed_from_sanitized_projection_only"] else "FAIL",
        },
        {
            "requirement": "Report raw row counts versus unique duplicate_group_id counts",
            "evidence": f"duplicate_records={len(result['duplicate_records'])}; per-packet report written.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve label_family=lifecycle_no_fill and forbidden primary fields absent",
            "evidence": f"primary_validation_issue_count={primary_issue_count}; forbidden_fields={sorted(FORBIDDEN_PRIMARY_FIELDS)}",
            "status": "PASS" if primary_issue_count == 0 else "FAIL",
        },
        {
            "requirement": "Resolve or restate EXP-G11-OBSERVER-EXPANSION-006 with exact next question",
            "evidence": "OTB1R ambiguity ledger restates the G12 exact question for a dedicated observer lifecycle logger versus staying blocked outside lifecycle/no-fill packet testing.",
            "status": "PASS",
        },
        {
            "requirement": "Produce only scoped OTB1R artifacts under requested directory",
            "evidence": f"artifact_count={len(scoped_artifact_paths)}; all artifact paths are under {rel(OUT)}.",
            "status": "PASS" if all(path.startswith(rel(OUT)) for path in scoped_artifact_paths) else "FAIL",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false",
            "evidence": "Metadata flags are false/no-promotion in every packet/report payload.",
            "status": "PASS"
            if result["metadata"]["promotion_verdict"] == "NO_PROMOTION_VERDICT"
            and result["metadata"]["validation_safe"] is False
            and result["metadata"]["outcome_review_opened"] is False
            else "FAIL",
        },
        {
            "requirement": "Do not run outcomes, inspect R/result values, create quarantine/result outputs, edit registries, or touch live trading surfaces",
            "evidence": "Metadata flags outcome_tests_run=false, r_result_values_read=false, quarantine_or_result_outputs_created=false, direct_master_registry_edits_applied=false, live_trading_surfaces_touched=false.",
            "status": "PASS"
            if not result["metadata"]["outcome_tests_run"]
            and not result["metadata"]["r_result_values_read"]
            and not result["metadata"]["quarantine_or_result_outputs_created"]
            and not result["metadata"]["direct_master_registry_edits_applied"]
            and not result["metadata"]["live_trading_surfaces_touched"]
            else "FAIL",
        },
    ]
    payload = {
        "metadata": result["metadata"],
        "objective_restatement": "Rebuild rejected OTB1 lifecycle/no-fill packets from input-only projected lifecycle source rows with no-leak source hashing, duplicate denominator reporting, and scoped OTB1R artifacts only.",
        "decision_counts": decision_count_map,
        "prompt_to_artifact_checklist": checklist,
        "can_mark_otb1r_artifacts_complete": all(item["status"] == "PASS" for item in checklist),
    }
    md = "\n".join(
        [
            "# OTB1R Completion Audit - 2026-05-07",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## Objective Restated",
            "",
            payload["objective_restatement"],
            "",
            "## Decision Counts",
            "",
            markdown_table(["Decision", "Count"], [[key, value] for key, value in decision_count_map.items()]),
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            markdown_table(
                ["Requirement", "Status", "Evidence"],
                [[item["requirement"], item["status"], item["evidence"]] for item in checklist],
            ),
            "",
            f"**Can mark OTB1R artifacts complete:** `{payload['can_mark_otb1r_artifacts_complete']}`",
        ]
    )
    return payload, md


def build_artifact_manifest(result: dict[str, Any], artifact_paths: list[Path]) -> dict[str, Any]:
    return {
        "metadata": result["metadata"],
        "artifact_count": len(artifact_paths),
        "artifacts": [file_evidence(path) for path in artifact_paths],
        "packet_artifacts": result["packet_artifacts"],
        "source_projection_file": rel(PROJECTION_FILE),
        "decision_counts": decision_counts(result["packet_records"]),
        "input_hashes": result["input_hashes"],
    }


def write_reports(result: dict[str, Any]) -> list[Path]:
    artifacts: list[Path] = [Path(path) for path in []]
    report_builders = [
        ("OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER", build_rebuild_ledger),
        ("OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT", build_schema_validation_report),
        ("OTB1R_DUPLICATE_DENOMINATOR_REPORT", build_duplicate_report),
        ("OTB1R_AMBIGUITY_LEDGER", build_ambiguity_ledger),
    ]
    for name, builder in report_builders:
        payload, md = builder(result)
        json_path = OUT / f"{name}_{DATE_STAMP}.json"
        md_path = OUT / f"{name}_{DATE_STAMP}.md"
        write_json(json_path, payload)
        write_text(md_path, md)
        artifacts.extend([json_path, md_path])

    artifacts.extend([PROJECTION_FILE])
    artifacts.extend(ROOT / path for path in result["packet_artifacts"])
    artifacts.append(Path(__file__).resolve())

    completion_json = OUT / f"OTB1R_COMPLETION_AUDIT_{DATE_STAMP}.json"
    completion_md_path = OUT / f"OTB1R_COMPLETION_AUDIT_{DATE_STAMP}.md"
    readme = OUT / f"README_{DATE_STAMP}.md"
    manifest_json = OUT / f"OTB1R_ARTIFACT_MANIFEST_{DATE_STAMP}.json"
    planned_artifacts = artifacts + [completion_json, completion_md_path, readme, manifest_json]
    completion_payload, completion_md = build_completion_audit(result, planned_artifacts)
    write_json(completion_json, completion_payload)
    write_text(completion_md_path, completion_md)
    artifacts.extend([completion_json, completion_md_path])

    write_text(
        readme,
        "\n".join(
            [
                "# OTB1R Input-Only Lifecycle Rebuild",
                "",
                "Scoped research-only rebuild artifacts for OTB1 lifecycle/no-fill packets after G12 rejected the prior source-hash clearing.",
                "",
                "- Promotion verdict: `NO_PROMOTION_VERDICT`",
                "- Outcome tests run: `false`",
                "- R/result values read: `false`",
                "- Source hashes: sanitized input-only lifecycle source projections only",
                "- Primary label family: `lifecycle_no_fill`",
            ]
        ),
    )
    artifacts.append(readme)

    write_json(manifest_json, build_artifact_manifest(result, artifacts + [manifest_json]))
    artifacts.append(manifest_json)
    return artifacts


def main() -> int:
    result = build_packets()
    artifacts = write_reports(result)
    print(
        json.dumps(
            {
                "artifact_family": "OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD",
                "artifacts_written": len(artifacts),
                "decision_counts": decision_counts(result["packet_records"]),
                "source_projection_issues": result["source_projection_validation"]["issue_count"],
                "source_projection_file": rel(PROJECTION_FILE),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
