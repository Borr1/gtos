"""Verify the CNR061 geometry+horizon sidecar artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from build_cnr061_geometry_horizon_sidecar_2026_05_08 import (
    OUTPUTS,
    PACKET_ID,
    file_sha256,
    hash_path_text,
    sidecar_forbidden_hits,
    stable_hash,
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify() -> dict[str, Any]:
    packet = read_json(OUTPUTS["packet_json"])
    packet_rows = read_jsonl(OUTPUTS["packet_jsonl"])
    join_map = read_json(OUTPUTS["join_map_json"])
    search_ledger = read_json(OUTPUTS["search_json"])
    noleak = read_json(OUTPUTS["noleak_json"])
    proposal = read_json(OUTPUTS["proposal_json"])
    blockers = read_json(OUTPUTS["blockers_json"])
    completion = read_json(OUTPUTS["completion_json"])

    issues: list[dict[str, Any]] = []

    if packet.get("packet_id") != PACKET_ID:
        issues.append({"check": "packet_id", "observed": packet.get("packet_id")})
    if packet.get("rows") != packet_rows:
        issues.append({"check": "json_jsonl_row_match", "observed": "packet rows differ from jsonl"})
    if packet.get("record_count") != len(packet_rows):
        issues.append({"check": "packet_record_count", "observed": packet.get("record_count"), "expected": len(packet_rows)})
    if len(packet_rows) != 8:
        issues.append({"check": "sidecar_row_count", "observed": len(packet_rows), "expected": 8})
    if packet.get("sidecar_rows_sha256") != stable_hash(packet_rows):
        issues.append({"check": "sidecar_rows_sha256", "observed": packet.get("sidecar_rows_sha256"), "expected": stable_hash(packet_rows)})

    for artifact_name, artifact in (
        ("packet", packet),
        ("join_map", join_map),
        ("search_ledger", search_ledger),
        ("noleak", noleak),
        ("proposal", proposal),
        ("blockers", blockers),
        ("completion", completion),
    ):
        if artifact.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append({"check": f"{artifact_name}.promotion_verdict", "observed": artifact.get("promotion_verdict")})
        if artifact.get("validation_safe") is not False:
            issues.append({"check": f"{artifact_name}.validation_safe", "observed": artifact.get("validation_safe")})
        if artifact.get("outcome_review_opened") is not False:
            issues.append({"check": f"{artifact_name}.outcome_review_opened", "observed": artifact.get("outcome_review_opened")})
        if artifact.get("live_effect") is not False:
            issues.append({"check": f"{artifact_name}.live_effect", "observed": artifact.get("live_effect")})

    for idx, row in enumerate(packet_rows):
        if row.get("packet_id") != PACKET_ID:
            issues.append({"check": "row.packet_id", "row": idx, "observed": row.get("packet_id")})
        if row.get("validation_safe") is not False:
            issues.append({"check": "row.validation_safe", "row": idx, "observed": row.get("validation_safe")})
        if row.get("live_effect") is not False:
            issues.append({"check": "row.live_effect", "row": idx, "observed": row.get("live_effect")})
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append({"check": "row.promotion_verdict", "row": idx, "observed": row.get("promotion_verdict")})
        for required in ("entry_sl_tp_or_level_packet", "executable_quote_packet", "ordered_path_packet", "source_evidence"):
            if required not in row:
                issues.append({"check": "row.required_field", "row": idx, "missing": required})
        geometry = row.get("entry_sl_tp_or_level_packet") or {}
        quote = row.get("executable_quote_packet") or {}
        path = row.get("ordered_path_packet") or {}
        if not all(geometry.get(k) is not None for k in ("entry_price", "stop_loss", "take_profit_1")):
            issues.append({"check": "row.geometry_values", "row": idx, "record_id": row.get("record_id")})
        if quote.get("quote_source_status") != "QUOTE_EXTRACTED_SOURCE_HASHED":
            issues.append({"check": "row.quote_status", "row": idx, "observed": quote.get("quote_source_status")})
        if path.get("path_status") != "ORDERED_TICK_PATH_AVAILABLE":
            issues.append({"check": "row.path_status", "row": idx, "observed": path.get("path_status")})
        hits = sidecar_forbidden_hits(row)
        if hits:
            issues.append({"check": "row.forbidden_key_hits", "row": idx, "hits": hits})
        row_hash = row.get("sidecar_row_sha256")
        row_copy = dict(row)
        row_copy.pop("sidecar_row_sha256", None)
        row_copy["no_leak_scan_status"] = "PENDING_VERIFIER"
        expected_hash = stable_hash(row_copy)
        if row_hash != expected_hash:
            issues.append({"check": "row.sidecar_row_sha256", "row": idx, "observed": row_hash, "expected": expected_hash})

    source_counts = join_map.get("source_counts") or {}
    expected_counts = {
        "cnr_source_field_pkt061_rows_all_timing_targets": 1020,
        "cnr_source_field_pkt061_e0e1_t0_rows": 102,
        "g12_ready_pkt061_rows": 8,
        "cnr_geometry_matrix_pkt061_rows": 8,
        "otx_pkt061_proposal_rows": 51,
        "otx_pkt061_rows_with_decision_quote": 50,
        "otx_pkt061_rows_with_ordered_path": 50,
        "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": 0,
        "otr061_recovered_rows": 1,
        "sidecar_ready_rows": 8,
    }
    for key, expected in expected_counts.items():
        if source_counts.get(key) != expected:
            issues.append({"check": f"join_map.source_counts.{key}", "observed": source_counts.get(key), "expected": expected})

    if noleak.get("forbidden_sidecar_key_status") != "PASS":
        issues.append({"check": "noleak.forbidden_sidecar_key_status", "observed": noleak.get("forbidden_sidecar_key_status")})
    duplicate_denominator_key_counts = noleak.get("duplicate_denominator_key_counts") or {}
    if sum(duplicate_denominator_key_counts.values()) != len(packet_rows):
        issues.append({
            "check": "noleak.duplicate_denominator_key_count_sum",
            "observed": sum(duplicate_denominator_key_counts.values()),
            "expected": len(packet_rows),
        })
    if proposal.get("ready_sidecar_row_count") != len(packet_rows):
        issues.append({"check": "proposal.ready_sidecar_row_count", "observed": proposal.get("ready_sidecar_row_count"), "expected": len(packet_rows)})
    if blockers.get("blocker_summary", {}).get("blocked_e0e1_t0_rows") != 94:
        issues.append({"check": "blockers.blocked_e0e1_t0_rows", "observed": blockers.get("blocker_summary", {}).get("blocked_e0e1_t0_rows"), "expected": 94})

    hash_failures = []
    for source in search_ledger.get("source_files", []):
        declared = source.get("declared_path") or source.get("path") or source.get("absolute_path")
        if not declared:
            continue
        if source.get("resolved_path"):
            observed = hash_path_text(str(source.get("declared_path"))).get("sha256")
            expected = source.get("sha256")
        else:
            path = Path(str(source.get("absolute_path") or declared))
            observed = file_sha256(path)
            expected = source.get("sha256")
        if expected and observed and expected != observed:
            hash_failures.append({"source": declared, "observed": observed, "expected": expected})
    if hash_failures:
        issues.append({"check": "source_hash_recompute", "failures": hash_failures})

    status = "PASS" if not issues else "FAIL"
    report = {
        "artifact_family": "CNR061_GEOMETRY_HORIZON_SIDECAR_VERIFICATION",
        "status": status,
        "issues": issues,
        "checked_artifacts": {name: str(path) for name, path in OUTPUTS.items()},
        "packet_rows": len(packet_rows),
        "blocked_rows": blockers.get("blocker_summary", {}).get("blocked_e0e1_t0_rows"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    return report


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
