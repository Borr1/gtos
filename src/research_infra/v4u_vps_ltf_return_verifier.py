"""Verify returned VPS/Windows MT5 LTF exports against V4U requirements."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.research_infra.v4u_ordered_path_hydration import (
    VALID_MT5_EXPORT_SOURCE_LABEL,
    VALID_MT5_TICK_EXPORT_SOURCE_LABEL,
    IndexedSourceFile,
    index_source_roots,
    parse_utc,
)


SCHEMA_VERSION = "v4u_vps_ltf_return_verifier_v1"
ROW_SCHEMA_VERSION = "v4u_vps_ltf_return_verifier_row_v1"
REQUIREMENT_ID_RE = re.compile(r"(v4u_ltf_[A-Za-z0-9]+)")


def verify_ltf_returns(
    *,
    requirements_jsonl: Path,
    source_roots: Iterable[Path],
    run_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    requirements = list(_iter_jsonl(requirements_jsonl))
    requirement_by_id = {str(row.get("requirement_id") or ""): row for row in requirements}
    source_index = index_source_roots(tuple(source_roots))
    sources_by_requirement: dict[str, list[IndexedSourceFile]] = defaultdict(list)
    extra_sources: list[IndexedSourceFile] = []
    for source in source_index.inventory_rows:
        req_id = source.handoff_requirement_id or _requirement_id_from_path(source.path)
        if req_id and req_id in requirement_by_id:
            sources_by_requirement[req_id].append(source)
        elif req_id:
            extra_sources.append(source)

    rows = [
        _verify_requirement(
            requirement=requirement,
            sources=sources_by_requirement.get(str(requirement.get("requirement_id") or ""), []),
        )
        for requirement in requirements
    ]
    status_counts = Counter(row["return_status"] for row in rows)
    accepted_rows = sum(1 for row in rows if row["accepted_source_count"] > 0)
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id or "v4u_vps_ltf_return_verifier",
        "requirements_jsonl": str(requirements_jsonl),
        "source_roots": [str(root) for root in source_roots],
        "requirements_total": len(requirements),
        "requirements_with_accepted_source": accepted_rows,
        "requirements_missing_all_returned_sources": status_counts.get(
            "missing_returned_exports",
            0,
        ),
        "requirements_with_rejected_sources_only": status_counts.get(
            "rejected_returned_sources_only",
            0,
        ),
        "return_status_counts": dict(sorted(status_counts.items())),
        "accepted_m1_source_count": sum(row["accepted_m1_source_count"] for row in rows),
        "accepted_tick_source_count": sum(row["accepted_tick_source_count"] for row in rows),
        "rejected_returned_source_count": sum(row["rejected_source_count"] for row in rows),
        "extra_returned_source_count": len(extra_sources),
        "source_index_summary": source_index.summary,
        "source_boundary": {
            "ordered_path_truth_only": True,
            "asof_decision_packet_truth_satisfied": False,
            "broker_ticket_order_deal_account_history_truth_satisfied": False,
            "proxy_or_m15_may_satisfy_ordered_path_truth": False,
            "redacted_account_native_truth_claim": False,
        },
        "next_step": (
            "rerun scripts/build_v4u_ordered_path_hydration_oracle.py only after "
            "requirements_with_accepted_source is greater than zero"
        ),
    }
    return report, rows


def _verify_requirement(
    *,
    requirement: Mapping[str, Any],
    sources: list[IndexedSourceFile],
) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for source in sorted(sources, key=lambda item: item.path):
        payload = _source_payload(source=source, requirement=requirement)
        if source.eligible_for_ordered_path_truth and payload["request_window_status"] == "request_window_matches":
            accepted.append(payload)
        else:
            rejected.append(payload)
    accepted_m1 = [
        source for source in accepted if source["source_label"] == VALID_MT5_EXPORT_SOURCE_LABEL
    ]
    accepted_tick = [
        source for source in accepted if source["source_label"] == VALID_MT5_TICK_EXPORT_SOURCE_LABEL
    ]
    if accepted_m1 and accepted_tick:
        status = "accepted_m1_and_tick"
    elif accepted_tick:
        status = "accepted_tick_only"
    elif accepted_m1:
        status = "accepted_m1_only"
    elif rejected:
        status = "rejected_returned_sources_only"
    else:
        status = "missing_returned_exports"
    return {
        "schema_version": ROW_SCHEMA_VERSION,
        "requirement_id": requirement.get("requirement_id"),
        "symbol": requirement.get("symbol"),
        "mt5_symbol": requirement.get("mt5_symbol"),
        "date": requirement.get("date"),
        "session": requirement.get("session"),
        "request_start_utc": requirement.get("request_start_utc"),
        "request_end_utc": requirement.get("request_end_utc"),
        "candidate_rows": requirement.get("candidate_rows"),
        "return_status": status,
        "accepted_source_count": len(accepted),
        "accepted_m1_source_count": len(accepted_m1),
        "accepted_tick_source_count": len(accepted_tick),
        "rejected_source_count": len(rejected),
        "accepted_sources": accepted,
        "rejected_sources": rejected,
        "can_rerun_ordered_path_oracle_for_requirement": bool(accepted),
        "allowed_use": "post_decision_ordered_path_replay_only",
        "not_asof_decision_packet_truth": True,
        "not_broker_order_lifecycle_truth": True,
    }


def _source_payload(
    *,
    source: IndexedSourceFile,
    requirement: Mapping[str, Any],
) -> dict[str, Any]:
    manifest, file_entry = _manifest_and_file_entry(source)
    request_window_status = _request_window_status(requirement, file_entry)
    return {
        "path": source.path,
        "source_kind": source.source_kind,
        "source_label": source.source_label,
        "eligible_for_ordered_path_truth": source.eligible_for_ordered_path_truth,
        "source_provenance_status": source.source_provenance_status,
        "source_broker": source.source_broker,
        "source_role": source.source_role,
        "source_truth_scope": source.source_truth_scope,
        "not_redacted_account_native": source.not_redacted_account_native,
        "replaces_missing_frozen_path_source": source.replaces_missing_frozen_path_source,
        "source_server": source.source_server,
        "source_account_login": source.source_account_login,
        "handoff_requirement_id": source.handoff_requirement_id,
        "source_manifest_path": source.source_manifest_path,
        "source_manifest_sha256": source.source_manifest_sha256,
        "sha256": source.sha256,
        "row_count": source.row_count,
        "first_time_utc": source.first_time_utc,
        "last_time_utc": source.last_time_utc,
        "manifest_schema_version": manifest.get("schema_version") if manifest else None,
        "manifest_file_row_count": (file_entry or {}).get("row_count"),
        "manifest_file_sha256": (file_entry or {}).get("sha256"),
        "manifest_request_start_utc": (file_entry or {}).get("request_start_utc"),
        "manifest_request_end_utc": (file_entry or {}).get("request_end_utc"),
        "request_window_status": request_window_status,
    }


def _manifest_and_file_entry(source: IndexedSourceFile) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    if not source.source_manifest_path:
        return {}, None
    path = Path(source.source_manifest_path)
    if not path.exists():
        return {}, None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}, None
    if not isinstance(manifest, dict):
        return {}, None
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        return manifest, None
    source_path = Path(source.path)
    for key, value in files.items():
        if not isinstance(value, Mapping):
            continue
        entry_path = value.get("path")
        if entry_path and Path(str(entry_path)) == source_path:
            return manifest, value
        if entry_path and Path(str(entry_path)).name == source_path.name:
            return manifest, value
        if str(key).upper() == source_path.stem.upper():
            return manifest, value
    return manifest, None


def _request_window_status(
    requirement: Mapping[str, Any],
    file_entry: Mapping[str, Any] | None,
) -> str:
    if not file_entry:
        return "missing_manifest_file_entry"
    expected_start = parse_utc(requirement.get("request_start_utc"))
    expected_end = parse_utc(requirement.get("request_end_utc"))
    got_start = parse_utc(file_entry.get("request_start_utc"))
    got_end = parse_utc(file_entry.get("request_end_utc"))
    if expected_start is None or expected_end is None:
        return "requirement_window_missing"
    if got_start is None or got_end is None:
        return "manifest_request_window_missing"
    if got_start != expected_start:
        return "manifest_request_start_mismatch"
    if got_end != expected_end:
        return "manifest_request_end_mismatch"
    timeframe = str(file_entry.get("timeframe") or "").upper()
    first = parse_utc(file_entry.get("first") or file_entry.get("first_time_utc"))
    last = parse_utc(file_entry.get("last") or file_entry.get("last_time_utc"))
    if timeframe == "M1" and first and last:
        if first > expected_start:
            return "m1_first_bar_after_request_start"
        if last < expected_end - timedelta(minutes=1):
            return "m1_last_bar_before_request_end"
    return "request_window_matches"


def _requirement_id_from_path(path: str) -> str | None:
    match = REQUIREMENT_ID_RE.search(path)
    return match.group(1) if match else None


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                yield row


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
