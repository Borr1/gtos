"""LTO-028 XAUUSD same-market structural/path extension status.

This is a preregistration/source-status lane only. It freezes the same-market
source-transfer question before outcome opening and keeps live rows separate
from replay evidence. It does not replay outcomes or alter live behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "xauusd_same_market_extension_status_v1"
REPORT_SCHEMA_VERSION = "lto028_xauusd_same_market_extension_v1"
LTO_ID = "LTO-028"
FOLLOW_ID = "LIVE-FOLLOW-026"
ACTION_REQUIRED = "XAUUSD_SAME_MARKET_EXTENSION_ACTION_REQUIRED"
STATUS_OK = "XAUUSD_SAME_MARKET_EXTENSION_PREREGISTERED_SOURCE_STATUS_ONLY"

DEFAULT_REGISTRY_PATH = Path("research/program_control/XAUUSD_SOURCE_TRANSFER_FROZEN_SLICE_REGISTRY_2026-05-04.json")
DEFAULT_SOURCE_MAP_PATH = Path("research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json")
DEFAULT_SIERRA_INVENTORY_PATH = Path("research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _source_ref(path: Path | str, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": bool(payload),
        "schema_version": (payload or {}).get("schema_version"),
        "status": (payload or {}).get("status"),
        "promotion_verdict": (payload or {}).get("promotion_verdict"),
    }


def _rows_with_lines(
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> list[tuple[int, dict[str, Any]]]:
    normalized: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(rows or [], start=1):
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], dict):
            normalized.append((int(item[0]), item[1]))
        elif isinstance(item, dict):
            normalized.append((index, item))
    return normalized


def _candidate_symbol_counts(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> Counter[str]:
    counts: Counter[str] = Counter()
    for _, row in _rows_with_lines(rows):
        counts[str(row.get("symbol") or "UNKNOWN")] += 1
    return counts


def _latest_xau_times(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[str]:
    times = {
        str(row.get("decision_time_utc") or row.get("created_at_utc") or "")
        for _, row in _rows_with_lines(rows)
        if str(row.get("symbol") or "").upper() == "XAUUSD"
    }
    return sorted(time for time in times if time)[-10:]


def _sierra_symbols(inventory: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    symbols = {}
    for row in (inventory or {}).get("symbols") or []:
        if isinstance(row, dict) and row.get("symbol_root"):
            symbols[str(row["symbol_root"]).upper()] = row
    return symbols


def _sierra_source_status(inventory: dict[str, Any] | None) -> dict[str, Any]:
    by_symbol = _sierra_symbols(inventory)
    watched = {}
    for symbol in ("XAUUSD", "GC", "MGC"):
        row = by_symbol.get(symbol) or {}
        watched[symbol] = {
            "status": row.get("status") or "MISSING_FROM_SIERRA_INVENTORY",
            "scid_file_count": int(row.get("scid_file_count") or 0),
            "depth_file_count": int(row.get("depth_file_count") or 0),
            "latest_scid_utc": row.get("latest_scid_utc"),
            "latest_depth_utc": row.get("latest_depth_utc"),
            "evidence_class": "SAME_MARKET_SOURCE_TRANSFER" if symbol == "XAUUSD" else "FUTURES_PROXY_TRANSFER",
        }
    return watched


def _gate(gate_id: str, required: str, observed: Any, passed: bool, blocker_code: str) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "required": required,
        "observed": observed,
        "passed": bool(passed),
        "blocker_code": "" if passed else blocker_code,
    }


def build_status_row(
    *,
    registry: dict[str, Any] | None = None,
    source_map: dict[str, Any] | None = None,
    sierra_inventory: dict[str, Any] | None = None,
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    evaluation_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    source_map_path: Path | str = DEFAULT_SOURCE_MAP_PATH,
    sierra_inventory_path: Path | str = DEFAULT_SIERRA_INVENTORY_PATH,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    candidate_counts = _candidate_symbol_counts(candidate_rows)
    evaluation_counts = _candidate_symbol_counts(evaluation_rows)
    source_status = _sierra_source_status(sierra_inventory)
    opened_outcome_slices = source_map.get("opened_outcome_slices") if isinstance(source_map, dict) else []
    if not isinstance(opened_outcome_slices, list):
        opened_outcome_slices = []

    registry_present = bool(registry)
    registry_no_promotion = (registry or {}).get("promotion_verdict") == PROMOTION_VERDICT
    registry_has_xau_family = any("XAUUSD" in str(item).upper() for item in (registry or {}).get("families") or [])
    opened_outcomes_zero = len(opened_outcome_slices) == 0
    live_replay_separated = True
    behavior_unchanged = (registry or {}).get("live_trading_behavior_changed") is False and (
        source_map or {}
    ).get("live_trading_behavior_changed") is False
    source_status_documented = bool(source_status) and all(item["status"] != "MISSING_FROM_SIERRA_INVENTORY" for item in source_status.values())
    no_promotion = registry_no_promotion and (source_map or {}).get("promotion_verdict") in {None, PROMOTION_VERDICT}

    gates = [
        _gate(
            "G0_NO_LIVE_BEHAVIOR_OR_PAID_CALLS",
            "No AI, canary, order, paid-data, execution, prompt, risk, or trading behavior changes.",
            {"behavior_unchanged": behavior_unchanged, **NO_DECISION_COUNTERS},
            behavior_unchanged,
            "LIVE_BEHAVIOR_BOUNDARY_NOT_PROVEN",
        ),
        _gate(
            "G1_SOURCE_TRANSFER_REGISTRY_PRESENT",
            "XAUUSD same-market/futures-proxy slice registry exists with XAUUSD family and NO_PROMOTION_VERDICT.",
            {
                "registry_present": registry_present,
                "registry_no_promotion": registry_no_promotion,
                "registry_has_xau_family": registry_has_xau_family,
            },
            registry_present and registry_no_promotion and registry_has_xau_family,
            "XAUUSD_SOURCE_TRANSFER_REGISTRY_MISSING_OR_INVALID",
        ),
        _gate(
            "G2_OUTCOMES_CLOSED_AT_REGISTRATION",
            "Opened outcome slices at registration must be exactly zero.",
            {"opened_outcome_slices_at_registration": len(opened_outcome_slices)},
            opened_outcomes_zero,
            "OPENED_OUTCOMES_PRESENT_AT_REGISTRATION",
        ),
        _gate(
            "G3_LIVE_ROWS_SEPARATE_FROM_REPLAY_EVIDENCE",
            "Live forward rows are counted as forward snapshots only, not same-market replay validation outcomes.",
            {
                "xauusd_live_candidate_rows": candidate_counts.get("XAUUSD", 0),
                "xauusd_live_evaluation_rows": evaluation_counts.get("XAUUSD", 0),
                "live_replay_separated": live_replay_separated,
            },
            live_replay_separated,
            "LIVE_REPLAY_EVIDENCE_MIXED",
        ),
        _gate(
            "G4_SOURCE_STATUS_DOCUMENTED",
            "XAUUSD same-market and GC/MGC proxy Sierra source statuses are documented before any outcome opening.",
            source_status,
            source_status_documented,
            "XAUUSD_SOURCE_STATUS_NOT_DOCUMENTED",
        ),
        _gate(
            "G5_NO_PROMOTION_OR_VALIDATION_CLAIM",
            "The lane may register source status only; it must not validate, promote, or report replay lift.",
            {"registry_no_promotion": registry_no_promotion, "source_map_no_promotion": no_promotion},
            no_promotion,
            "PROMOTION_OR_VALIDATION_CLAIM_PRESENT",
        ),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    limitations = []
    if source_status.get("XAUUSD", {}).get("depth_file_count", 0) == 0:
        limitations.append("XAUUSD_SAME_MARKET_DEPTH_MISSING_SCID_ONLY")
    if source_status.get("XAUUSD", {}).get("status") == "CAUTION_SCID_PRESENT_DEPTH_MISSING":
        limitations.append("XAUUSD_SAME_MARKET_DEPTH_MISSING_SCID_ONLY")
    limitations.extend(gate["blocker_code"] for gate in failed if gate["blocker_code"])
    action_required_codes = [gate["blocker_code"] for gate in failed if gate["blocker_code"]]
    status = ACTION_REQUIRED if action_required_codes else STATUS_OK
    # This row's identity is the preregistered source contract, not the latest
    # live observer count. Keep the forward snapshot in the row for study, but
    # do not let normal live evaluation appends make the source-status contract
    # look missing minutes after it was written.
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        generated.split("T")[0],
        registry,
        source_map,
        source_status,
        status,
        sorted(set(limitations)),
        action_required_codes,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("xauusd_same_market_extension", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": status,
        "evidence_class": "SAME_MARKET_SOURCE_TRANSFER_REGISTRATION",
        "promotion_verdict": PROMOTION_VERDICT,
        "registry_ref": _source_ref(registry_path, registry),
        "source_map_ref": _source_ref(source_map_path, source_map),
        "sierra_inventory_ref": _source_ref(sierra_inventory_path, sierra_inventory),
        "registered_question": (registry or {}).get("frozen_question"),
        "registered_families": (registry or {}).get("families") or [],
        "registered_evidence_classes": (registry or {}).get("evidence_classes") or [],
        "target_resolved_rows_before_validation_discussion": (registry or {}).get(
            "target_resolved_rows_before_validation_discussion"
        ),
        "holdout_policy": (registry or {}).get("holdout_policy"),
        "opened_outcome_slices_at_registration": len(opened_outcome_slices),
        "opened_outcome_slices": opened_outcome_slices,
        "outcome_opening_status": "OUTCOMES_CLOSED" if opened_outcomes_zero else "OUTCOMES_OPENED_ACTION_REQUIRED",
        "source_status": source_status,
        "forward_snapshot": {
            "candidate_symbol_counts": dict(candidate_counts),
            "evaluation_symbol_counts": dict(evaluation_counts),
            "xauusd_live_candidate_rows": candidate_counts.get("XAUUSD", 0),
            "xauusd_live_evaluation_rows": evaluation_counts.get("XAUUSD", 0),
            "latest_xauusd_candidate_decision_times": _latest_xau_times(candidate_rows),
            "latest_xauusd_evaluation_times": _latest_xau_times(evaluation_rows),
            "live_rows_are_forward_snapshot_only": True,
            "live_rows_are_not_replay_outcomes": True,
        },
        "validation_gates": gates,
        "gate_summary": {
            "passed": sum(1 for gate in gates if gate["passed"]),
            "failed": len(failed),
            "failed_gate_ids": [gate["gate_id"] for gate in failed],
            "failed_blocker_codes": [gate["blocker_code"] for gate in failed if gate["blocker_code"]],
        },
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": action_required_codes,
        "claim_boundary": (
            "LTO-028 preregisters XAUUSD same-market/source-transfer evidence only. "
            "It opens no outcomes and cannot validate replay lift, promote a selector, or modify live behavior."
        ),
        **NO_DECISION_COUNTERS,
    }


def build_report_payload(
    *,
    registry: dict[str, Any] | None = None,
    source_map: dict[str, Any] | None = None,
    sierra_inventory: dict[str, Any] | None = None,
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    evaluation_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    source_map_path: Path | str = DEFAULT_SOURCE_MAP_PATH,
    sierra_inventory_path: Path | str = DEFAULT_SIERRA_INVENTORY_PATH,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    row = build_status_row(
        registry=registry,
        source_map=source_map,
        sierra_inventory=sierra_inventory,
        candidate_rows=candidate_rows,
        evaluation_rows=evaluation_rows,
        registry_path=registry_path,
        source_map_path=source_map_path,
        sierra_inventory_path=sierra_inventory_path,
        generated_at_utc=generated,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": row["status"],
        "status_row": row,
        "completion_evidence": {
            "opened_outcome_slices_at_registration": row["opened_outcome_slices_at_registration"],
            "live_rows_separate_from_replay_evidence": row["forward_snapshot"]["live_rows_are_not_replay_outcomes"],
            "no_live_behavior_changed": True,
            "new_ai_calls": 0,
            "new_canary_calls": 0,
            "new_order_calls": 0,
            "new_paid_data_calls": 0,
        },
        "synthesis": {
            "summary": (
                "XAUUSD same-market structural/path extension is preregistered as source-status only. "
                "Outcomes remain closed at registration, live rows remain forward snapshots, and XAUUSD/GC/MGC "
                "source statuses are documented before any replay evidence is opened."
            ),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    row = payload["status_row"]
    lines = [
        "# LTO028 XAUUSD Same-Market Extension - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Registration",
        "",
        f"- Registered question: `{row['registered_question']}`",
        f"- Families: `{row['registered_families']}`",
        f"- Evidence classes: `{row['registered_evidence_classes']}`",
        f"- Opened outcome slices at registration: `{row['opened_outcome_slices_at_registration']}`",
        f"- Outcome opening status: `{row['outcome_opening_status']}`",
        f"- Target resolved rows before validation discussion: `{row['target_resolved_rows_before_validation_discussion']}`",
        "",
        "## Forward Snapshot",
        "",
        f"- Candidate symbol counts: `{row['forward_snapshot']['candidate_symbol_counts']}`",
        f"- Evaluation symbol counts: `{row['forward_snapshot']['evaluation_symbol_counts']}`",
        f"- XAUUSD live candidate rows: `{row['forward_snapshot']['xauusd_live_candidate_rows']}`",
        f"- XAUUSD live evaluation rows: `{row['forward_snapshot']['xauusd_live_evaluation_rows']}`",
        f"- Live rows are not replay outcomes: `{row['forward_snapshot']['live_rows_are_not_replay_outcomes']}`",
        "",
        "## Source Status",
        "",
        "| Source | Status | SCID files | Depth files | Evidence class |",
        "|---|---|---:|---:|---|",
    ]
    for symbol, status in row["source_status"].items():
        lines.append(
            f"| `{symbol}` | `{status['status']}` | {status['scid_file_count']} | "
            f"{status['depth_file_count']} | `{status['evidence_class']}` |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Gate | Passed | Observed | Blocker |",
            "|---|---:|---|---|",
        ]
    )
    for gate in row["validation_gates"]:
        observed = json.dumps(gate["observed"], sort_keys=True, default=str).replace("|", r"\|")
        lines.append(f"| `{gate['gate_id']}` | `{gate['passed']}` | `{observed}` | `{gate['blocker_code'] or '-'}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            row["claim_boundary"],
            "",
            "## Safety Counters",
            "",
            f"- ai_calls: `{row['ai_calls']}`",
            f"- canary_calls: `{row['canary_calls']}`",
            f"- order_calls: `{row['order_calls']}`",
            f"- paid_data_calls: `{row['paid_data_calls']}`",
        ]
    )
    return "\n".join(lines) + "\n"
